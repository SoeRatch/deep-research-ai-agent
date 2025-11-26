"""
LangGraph node implementations for research agent.

Each node represents a step in the research workflow.
"""

import json
import logging
from typing import Dict, Any, List
from src.models import get_orchestrator, ModelRole
from src.agent.state import ResearchState
from src.config import get_config
from src.prompts import ResearchPrompts
from src.tools.search import SearchTool
from src.tools.scraper import WebScraper
from src.tools.validator import FactValidator
logger = logging.getLogger(__name__)


class ResearchNodes:
    """Collection of node functions for the research graph."""
    
    def __init__(self):
        """Initialize nodes with tools and models."""
        self.config = get_config()
        self.orchestrator = get_orchestrator(self.config)
        self.search_tool = SearchTool(self.config)
        self.scraper = WebScraper(self.config)
        self.validator = FactValidator()
        self.prompts = ResearchPrompts()
    
    def _log_audit(self, state: ResearchState, node_name: str, data: Dict[str, Any]):
        """Add entry to audit trail."""
        entry = {
            'node': node_name,
            'iteration': state['iteration_count'],
            'depth': state['research_depth'],
            'data': data
        }
        return {'audit_trail': [entry]}
    
    def _parse_json_response(self, response: str) -> Dict:
        """Parse JSON from model response, handling markdown code blocks."""
        try:
            # Try direct parse first
            return json.loads(response)
        except json.JSONDecodeError:
            # Try extracting from markdown code block
            if '```json' in response:
                start = response.find('```json') + 7
                end = response.find('```', start)
                json_str = response[start:end].strip()
                return json.loads(json_str)
            elif '```' in response:
                start = response.find('```') + 3
                end = response.find('```', start)
                json_str = response[start:end].strip()
                return json.loads(json_str)
            else:
                logger.error(f"Failed to parse JSON from response: {response[:200]}")
                return {}
    
    async def plan_node(self, state: ResearchState) -> Dict[str, Any]:
        """
        Initial planning node - create research strategy.
        
        Args:
            state: Current research state
            
        Returns:
            State updates
        """
        logger.info(f"Planning research for: {state['entity']}")
        
        # 1. Generate the planning prompt
        prompt = self.prompts.get_planner_prompt(state['entity'])
        
        # 2. Send prompt to LLM
        response = await self.orchestrator.invoke_with_fallback(
            ModelRole.PLANNER,
            [{'role': 'user', 'content': prompt}]
        )
        
        # 3. Parse the JSON response from LLM
        plan = self._parse_json_response(response)
        
        # 4. Use LLM's entity_type detection (might be more accurate than heuristic)
        entity_type = plan.get('entity_type', state.get('entity_type', 'individual'))

        # 5. Update state: entity_type, initial queries, information gaps, increment depth
        updates = {
            'entity_type': entity_type,
            'next_queries': plan.get('initial_queries', []),
            'information_gaps': plan.get('information_gaps', []),
            'research_depth': state['research_depth'] + 1
        }
        
        # 6. Log to audit trail
        updates.update(
            self._log_audit(state, 'plan',{
                'entity_type': entity_type,
                'strategy': plan.get('strategy', ''),
                'initial_queries': plan.get('initial_queries', [])
                }
                )
            )
        
        return updates
    

    async def search_node(self, state: ResearchState) -> Dict[str, Any]:
        """
        Execute search queries and ensure all results have content.
        
        Uses Tavily's raw_content when available, falls back to scraping
        for results without sufficient content. This ensures extract_node
        always has content to process.
        
        Args:
            state: Current research state
            
        Returns:
            State updates
        """
        queries = state['next_queries'][:self.config.max_queries_per_iteration]
        
        logger.info(f"Executing {len(queries)} search queries")
        
        results_map = self.search_tool.batch_search(queries, max_results_per_query=5)
        
        all_results = []
        all_sources = []
        
        for query, results in results_map.items():
            all_results.extend(results)
            for result in results:
                if result.get('url'):
                    all_sources.append(result['url'])
        
        # Enrich results: Scrape URLs that don't have sufficient Tavily content
        urls_needing_scrape = []
        for result in all_results:
            if result.get('type') == 'search_result':
                # Check if Tavily provided sufficient content
                if not result.get('raw_content') or len(result.get('raw_content', '')) < 200:
                    if result.get('url'):
                        urls_needing_scrape.append((result['url'], all_results.index(result)))
        
        # Scrape missing content as fallback
        scraped_count = 0
        if urls_needing_scrape:
            logger.info(f"Scraping {len(urls_needing_scrape)} URLs without sufficient Tavily content")
            urls_to_scrape = [url for url, _ in urls_needing_scrape[:5]]  # Limit to 5
            scraped = self.scraper.batch_scrape(urls_to_scrape)
            
            # Enrich the results with scraped content
            for url, result_index in urls_needing_scrape[:5]:
                if url in scraped and scraped[url]:
                    all_results[result_index]['raw_content'] = scraped[url]['content']
                    all_results[result_index]['content_source'] = 'scraper'
                    scraped_count += 1
                else:
                    all_results[result_index]['content_source'] = 'tavily'
        
        # Mark Tavily results
        # Tags results that already had Tavily content as 'tavily'
        for result in all_results:
            if result.get('type') == 'search_result' and 'content_source' not in result:
                result['content_source'] = 'tavily'
        
        logger.info(f"Search complete: {len(all_results)} results ({len(all_results) - scraped_count} from Tavily, {scraped_count} scraped)")
        
        updates = {
            'queries_executed': queries,        # Track what queries ran
            'search_results': all_results,      # All search results with content
            'sources': all_sources,             # All source URLs
            'next_queries': []                  # Clear queue (important!)
        }
        
        updates.update(self._log_audit(state, 'search', {
            'queries': queries,
            'results_count': len(all_results),
            'tavily_results': len(all_results) - scraped_count,
            'scraped_results': scraped_count
        }))
        
        return updates
    

    async def extract_node(self, state: ResearchState) -> Dict[str, Any]:
        """
        Extract facts AND entities from search results.
        
        Uses parallel processing for 10x speedup on multiple content sources.
        
        Args:
            state: Current research state
            
        Returns:
            State updates
        """
        import asyncio
        
        logger.info("Extracting facts and entities from search results")
        
        # Get recent results and prioritize by relevance score
        recent_results = state['search_results'][-20:]
        
        # Collect and prioritize content sources by relevance score
        content_sources = []
        for result in recent_results:
            if result.get('type') == 'search_result' and result.get('raw_content'):
                content_sources.append({
                    'url': result['url'],
                    'content': result['raw_content'],
                    'source': result.get('content_source', 'tavily'),
                    'score': result.get('score', 0.5),
                    'metadata': {
                        'title': result.get('title', ''),
                        'score': result.get('score', 0.5)
                    }
                })
        
        # Prioritize top 10 by relevance score (cost & speed optimization)
        content_sources.sort(key=lambda x: x['score'], reverse=True)
        content_sources = content_sources[:10]
        
        logger.info(f"Processing {len(content_sources)} content sources in parallel")
        
        # Prepare all extraction tasks for parallel execution
        async def extract_from_source(content_source):
            """Extract facts from a single content source."""
            try:
                prompt = self.prompts.get_fact_extraction_prompt(
                    state['entity'],
                    content_source['content'],
                    content_source['url']
                )
                
                response = await self.orchestrator.invoke_with_fallback(
                    ModelRole.RESEARCHER,
                    [{'role': 'user', 'content': prompt}]
                )
                
                extracted = self._parse_json_response(response)
                facts = extracted.get('facts', [])
                entities = extracted.get('key_entities_mentioned', [])
                
                # Add source metadata to facts
                for fact in facts:
                    fact['source_url'] = content_source['url']
                    fact['content_source'] = content_source['source']
                
                return {'facts': facts, 'entities': entities, 'url': content_source['url']}
                
            except Exception as e:
                logger.error(f"Failed to extract from {content_source.get('url', 'unknown')}: {e}")
                return {'facts': [], 'entities': [], 'url': content_source.get('url', 'unknown')}
        
        # Execute all extractions in parallel (major speedup!)
        extraction_results = await asyncio.gather(
            *[extract_from_source(cs) for cs in content_sources],
            return_exceptions=True
        )
        
        # Collect all facts and entities from parallel results
        all_facts = []
        all_entities_raw = []
        
        for result in extraction_results:
            # Skip failed tasks (exceptions)
            if isinstance(result, Exception):
                logger.error(f"Extraction task failed: {result}")
                continue
            
            all_facts.extend(result['facts'])
            
            # Collect raw entities for deduplication
            for entity in result['entities'] if isinstance(result['entities'], list) else []:
                # Handle both dict and string formats
                if isinstance(entity, str):
                    entity = {'name': entity, 'relationship': 'Mentioned in content'}
                
                # Ensure required fields with defaults
                if isinstance(entity, dict) and 'name' in entity:
                    entity.setdefault('priority', 'medium')
                    entity.setdefault('relationship', 'Unknown')
                    entity['discovered_in_iteration'] = state['iteration_count']
                    all_entities_raw.append(entity)
        
        # Deduplicate entities by name (keep highest priority version)
        seen_entities = {}
        priority_order = {'high': 3, 'medium': 2, 'low': 1}
        
        for entity in all_entities_raw:
            name_key = entity['name'].lower().strip()
            
            if name_key not in seen_entities:
                seen_entities[name_key] = entity
            else:
                # Keep entity with higher priority
                existing_priority = priority_order.get(seen_entities[name_key]['priority'], 0)
                new_priority = priority_order.get(entity['priority'], 0)
                
                if new_priority > existing_priority:
                    seen_entities[name_key] = entity
        
        all_entities = list(seen_entities.values())
        
        logger.info(f"Extracted {len(all_facts)} facts and {len(all_entities)} unique entities (deduplicated from {len(all_entities_raw)})")
        
        updates = {
            'scraped_content': content_sources,
            'facts_discovered': all_facts,
            'entities_to_investigate': all_entities
        }
        
        updates.update(self._log_audit(state, 'extract', {
            'content_sources_processed': len(content_sources),
            'facts_extracted': len(all_facts),
            'entities_discovered': len(all_entities)
        }))
        
        return updates
    

    async def analyze_node(self, state: ResearchState) -> Dict[str, Any]:
        """
        Analyze facts for risks and connections using secondary model.
        
        Args:
            state: Current research state
            
        Returns:
            State updates
        """
        logger.info("Analyzing facts for risks and connections")
        
        # Format facts for analysis
        facts_str = "\n".join([
            f"- [{f.get('category', 'unknown')}] {f.get('claim', '')} (confidence: {f.get('confidence', 0):.2f})"
            for f in state['facts_discovered'][-50:]  # Last 50 facts
        ])
        
        # Risk analysis
        risk_prompt = self.prompts.get_risk_analysis_prompt(state['entity'], facts_str)
        risk_response = await self.orchestrator.invoke_with_fallback(
            ModelRole.ANALYZER,  # Use secondary model
            [{'role': 'user', 'content': risk_prompt}]
        )
        
        risk_analysis = self._parse_json_response(risk_response)
        risks = risk_analysis.get('risks', [])
        
        # Connection mapping
        # Identify all connections mentioned in the facts and structure them as relationships
        # This appears in the report as a visual network map!
        connection_prompt = self.prompts.get_connection_mapping_prompt(state['entity'], facts_str)
        connection_response = await self.orchestrator.invoke_with_fallback(
            ModelRole.ANALYZER,
            [{'role': 'user', 'content': connection_prompt}]
        )
        
        connection_analysis = self._parse_json_response(connection_response)
        connections = connection_analysis.get('connections', [])
        
        updates = {
            'risks_identified': risks,
            'connections': connections
        }
        
        updates.update(self._log_audit(state, 'analyze', {
            'risks_found': len(risks),
            'connections_found': len(connections)
        }))
        
        return updates
    
    async def validate_node(self, state: ResearchState) -> Dict[str, Any]:
        """
        Validate facts across sources and assign confidence.
        
        Args:
            state: Current research state
            
        Returns:
            State updates
        """
        logger.info("Validating facts across sources")
        
        # Prepare sources for validation
        all_sources = []
        for scraped in state['scraped_content']:
            all_sources.append({
                'url': scraped['url'],
                'content': scraped['content']
            })
        
        # Validate all facts
        validated_facts = self.validator.batch_validate(
            state['facts_discovered'],
            all_sources
        )
        
        # Calculate overall confidence
        if validated_facts:
            overall_confidence = sum(f.get('confidence', 0) for f in validated_facts) / len(validated_facts)
        else:
            overall_confidence = 0.0
        
        validation_summary = self.validator.get_validation_summary()
        
        updates = {
            'facts_discovered': validated_facts,  # Replace with validated versions
            'overall_confidence': overall_confidence
        }
        
        updates.update(self._log_audit(state, 'validate', validation_summary))
        
        return updates
    

    async def refine_node(self, state: ResearchState) -> Dict[str, Any]:
        """
        Refine search strategy based on findings.
        
        Args:
            state: Current research state
            
        Returns:
            State updates
        """
        logger.info("Refining search strategy")
        
        # Summarize findings so far
        findings_summary = f"""
        Facts discovered: {len(state['facts_discovered'])}
        Connections mapped: {len(state['connections'])}
        Risks identified: {len(state['risks_identified'])}

        Recent facts:
        {chr(10).join([f"- {f.get('claim', '')}" for f in state['facts_discovered'][-10:]])}
        """
        
        prompt = self.prompts.get_query_refinement_prompt(
            state['entity'],
            findings_summary,
            state['information_gaps'],
            discovered_entities=state['entities_to_investigate'],
            investigated_entities=state['investigated_entities']
        )
        
        response = await self.orchestrator.invoke_with_fallback(
            ModelRole.PLANNER,
            [{'role': 'user', 'content': prompt}]
        )
        
        refinement = self._parse_json_response(response)
        
        new_queries = refinement.get('next_queries', [])
        entities_investigated_this_round = refinement.get('entities_to_investigate_this_round', [])
        
        # Increment iteration counter
        iteration_count = state['iteration_count'] + 1
        
        # Check for uninvestigated HIGH priority entities
        # This ensures we don't stop early if we found important leads (like family/co-founders)
        # even if we are confident about the main facts.
        uninvestigated_high_priority = [
            e for e in state['entities_to_investigate']
            if e.get('priority') == 'high' 
            and e['name'] not in state['investigated_entities']
            and e['name'] not in entities_investigated_this_round
        ]
        
        has_important_leads = len(uninvestigated_high_priority) > 0
        
        if has_important_leads:
            logger.info(f"Continuing research due to {len(uninvestigated_high_priority)} uninvestigated high-priority leads")
        
        # Check if should continue
        should_continue = (
            iteration_count < state['max_depth'] and
            len(new_queries) > 0 and
            (
                state['overall_confidence'] < self.config.confidence_threshold or
                has_important_leads  # Force continue for high-value targets
            )
        )
        
        updates = {
            'next_queries': new_queries,
            'iteration_count': iteration_count,
            'should_continue': should_continue,
            'investigated_entities': entities_investigated_this_round
        }
        
        updates.update(self._log_audit(state, 'refine', {
            'new_queries': new_queries,
            'should_continue': should_continue,
            'iteration': iteration_count
        }))
        
        return updates
    

    async def report_node(self, state: ResearchState) -> Dict[str, Any]:
        """
        Generate final research report.
        
        Args:
            state: Current research state
            
        Returns:
            State updates with final report
        """
        logger.info("Generating final report")
        
        prompt = self.prompts.get_synthesis_prompt(
            state['entity'],
            state['facts_discovered'],
            state['connections'],
            state['risks_identified']
        )
        
        report = await self.orchestrator.invoke_with_fallback(
            ModelRole.SYNTHESIZER,
            [{'role': 'user', 'content': prompt}]
        )
        
        updates = {
            'final_report': report,
            'should_continue': False  # End workflow
        }
        
        updates.update(self._log_audit(state, 'report', {
            'report_length': len(report),
            'total_facts': len(state['facts_discovered']),
            'total_sources': len(set(state['sources']))
        }))
        
        return updates
