"""
Search tool using Tavily API for AI-optimized web search.

Includes query deduplication and result ranking.
"""

from typing import List, Dict, Any, Optional
from tavily import TavilyClient
from tenacity import retry, stop_after_attempt, wait_exponential
import logging

from src.config import Config

logger = logging.getLogger(__name__)


class SearchTool:
    """Web search tool with deduplication and ranking."""
    
    def __init__(self, config: Config):
        """
        Initialize search tool.
        
        Args:
            config: Application configuration
        """
        self.config = config
        self.client = TavilyClient(api_key=config.tavily_api_key)
        self.query_history: List[str] = []  # Track executed queries
        self.results_cache: Dict[str, List[Dict]] = {}  # Cache results
    
    def _normalize_query(self, query: str) -> str:
        """Normalize query for deduplication."""
        return query.lower().strip()
    
    def is_duplicate_query(self, query: str) -> bool:
        """
        Check if query is a duplicate of previous search.
        
        Args:
            query: Search query
            
        Returns:
            True if query is duplicate
        """
        normalized = self._normalize_query(query)
        return normalized in [self._normalize_query(q) for q in self.query_history]
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    def search(
        self,
        query: str,
        max_results: int = 5,
        include_raw_content: bool = True,
        force: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Execute web search with retry logic.
        
        Args:
            query: Search query
            max_results: Maximum number of results
            include_raw_content: Whether to include full page content
            force: Force search even if duplicate
            
        Returns:
            List of search results with URLs and content
        """
        # Check for duplicates
        if not force and self.is_duplicate_query(query):
            logger.warning(f"Skipping duplicate query: {query}")
            normalized = self._normalize_query(query)
            # Return cached results if available
            for cached_query, results in self.results_cache.items():
                if self._normalize_query(cached_query) == normalized:
                    return results
            return []
        
        logger.info(f"Executing search: {query}")
        
        try:
            # Use Tavily's search API
            response = self.client.search(
                query=query,
                max_results=max_results,
                search_depth="advanced",  # Deep search for comprehensive results
                include_raw_content=include_raw_content,
                include_answer=True  # Get AI-generated answer
            )
            
            results = []
            
            # Add AI answer if available
            if response.get('answer'):
                results.append({
                    'type': 'answer',
                    'content': response['answer'],
                    'query': query
                })
            
            # Process search results
            for item in response.get('results', []):
                result = {
                    'type': 'search_result',
                    'url': item.get('url'),
                    'title': item.get('title'),
                    'content': item.get('content', ''),  # Summary
                    'raw_content': item.get('raw_content', ''),  # Full content
                    'score': item.get('score', 0.5),
                    'query': query
                }
                results.append(result)
            
            # Cache results
            self.query_history.append(query)
            self.results_cache[query] = results
            
            logger.info(f"Found {len(results)} results for: {query}")
            return results
            
        except Exception as e:
            logger.error(f"Search failed for query '{query}': {e}")
            raise
    
    def batch_search(
        self,
        queries: List[str],
        max_results_per_query: int = 5
    ) -> Dict[str, List[Dict]]:
        """
        Execute multiple searches efficiently.
        
        Args:
            queries: List of search queries
            max_results_per_query: Max results per query
            
        Returns:
            Dictionary mapping queries to results
        """
        results_map = {}
        
        for query in queries:
            if not self.is_duplicate_query(query):
                try:
                    results = self.search(
                        query,
                        max_results=max_results_per_query
                    )
                    results_map[query] = results
                except Exception as e:
                    logger.error(f"Failed to search '{query}': {e}")
                    results_map[query] = []
            else:
                logger.info(f"Skipping duplicate: {query}")
        
        return results_map
    
    def get_query_history(self) -> List[str]:
        """Get list of all executed queries."""
        return self.query_history.copy()
    
    def clear_history(self):
        """Clear query history and cache."""
        self.query_history.clear()
        self.results_cache.clear()