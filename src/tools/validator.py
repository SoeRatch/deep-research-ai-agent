"""
Fact validation tool for cross-referencing and confidence scoring.

Implements source quality assessment and multi-source validation.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from collections import Counter
import logging

logger = logging.getLogger(__name__)


class FactValidator:
    """Validates facts across multiple sources and assigns confidence scores."""
    
    def __init__(self):
        """Initialize validator."""
        self.validated_facts: List[Dict] = []
        
        # Source reliability tiers (domain-based)
        self.high_quality_sources = [
            'wikipedia.org', 'reuters.com', 'bloomberg.com',
            'wsj.com', 'nytimes.com', 'bbc.com', 'forbes.com',
            '.gov', '.edu'
        ]
        
        self.medium_quality_sources = [
            'techcrunch.com', 'theverge.com', 'wired.com',
            'fortune.com', 'businessinsider.com', 'cnbc.com'
        ]
    
    def assess_source_quality(self, url: str) -> str:
        """
        Assess source quality based on domain.
        
        Args:
            url: Source URL
            
        Returns:
            Quality level: 'high', 'medium', or 'low'
        """
        url_lower = url.lower()
        
        for domain in self.high_quality_sources:
            if domain in url_lower:
                return 'high'
        
        for domain in self.medium_quality_sources:
            if domain in url_lower:
                return 'medium'
        
        return 'low'
    
    def calculate_base_confidence(
        self,
        source_count: int,
        source_quality: str
    ) -> float:
        """
        Calculate base confidence score.
        
        Args:
            source_count: Number of sources supporting the fact
            source_quality: Quality of primary source
            
        Returns:
            Confidence score (0.0 to 1.0)
        """
        # Base score from source count
        if source_count >= 3:
            count_score = 0.9
        elif source_count == 2:
            count_score = 0.7
        else:
            count_score = 0.5
        
        # Quality multiplier
        quality_weights = {
            'high': 1.0,
            'medium': 0.9,
            'low': 0.7
        }
        quality_weight = quality_weights.get(source_quality, 0.7)
        
        return min(1.0, count_score * quality_weight)
    
    def cross_reference_fact(
        self,
        fact: Dict[str, Any],
        sources: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Cross-reference a fact across multiple sources.
        
        Args:
            fact: Fact dictionary with 'claim' and initial 'confidence'
            sources: List of source dictionaries with 'url' and 'content'
            
        Returns:
            Enhanced fact with updated confidence and validation metadata
        """
        claim = fact.get('claim', '').lower()
        
        # Count sources that mention this fact
        supporting_sources = []
        for source in sources:
            content = source.get('content', '').lower()
            # Simple keyword matching (could be enhanced with semantic similarity)
            claim_keywords = set(claim.split())
            content_keywords = set(content.split())
            overlap = len(claim_keywords & content_keywords) / len(claim_keywords) if claim_keywords else 0
            
            if overlap > 0.4:  # 40% keyword overlap threshold
                supporting_sources.append(source['url'])
        
        # Assess source quality
        if supporting_sources:
            source_qualities = [self.assess_source_quality(url) for url in supporting_sources]
            quality_counts = Counter(source_qualities)
            # Use highest quality available
            if quality_counts['high'] > 0:
                primary_quality = 'high'
            elif quality_counts['medium'] > 0:
                primary_quality = 'medium'
            else:
                primary_quality = 'low'
        else:
            primary_quality = 'low'
        
        # Calculate confidence
        confidence = self.calculate_base_confidence(
            len(supporting_sources),
            primary_quality
        )
        
        # Update fact
        validated_fact = fact.copy()
        validated_fact.update({
            'confidence': confidence,
            'source_count': len(supporting_sources),
            'supporting_sources': supporting_sources[:5],  # Keep top 5
            'source_quality': primary_quality,
            'validated_at': datetime.now().isoformat()
        })
        
        self.validated_facts.append(validated_fact)
        
        logger.info(
            f"Validated fact with {len(supporting_sources)} sources, "
            f"confidence: {confidence:.2f}"
        )
        
        return validated_fact
    
    def batch_validate(
        self,
        facts: List[Dict],
        all_sources: List[Dict]
    ) -> List[Dict]:
        """
        Validate multiple facts against all sources.
        
        Args:
            facts: List of fact dictionaries
            all_sources: List of all source dictionaries
            
        Returns:
            List of validated facts
        """
        validated = []
        for fact in facts:
            validated_fact = self.cross_reference_fact(fact, all_sources)
            validated.append(validated_fact)
        
        return validated
    
    def filter_by_confidence(
        self,
        facts: List[Dict],
        min_confidence: float = 0.5
    ) -> List[Dict]:
        """
        Filter facts by minimum confidence threshold.
        
        Args:
            facts: List of facts
            min_confidence: Minimum confidence threshold
            
        Returns:
            Filtered list of high-confidence facts
        """
        return [f for f in facts if f.get('confidence', 0) >= min_confidence]
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics of validation process.
        
        Returns:
            Dictionary with validation statistics
        """
        if not self.validated_facts:
            return {
                'total_facts': 0,
                'avg_confidence': 0.0,
                'high_confidence_count': 0,
                'low_confidence_count': 0
            }
        
        confidences = [f['confidence'] for f in self.validated_facts]
        
        return {
            'total_facts': len(self.validated_facts),
            'avg_confidence': sum(confidences) / len(confidences),
            'high_confidence_count': sum(1 for c in confidences if c >= 0.7),
            'medium_confidence_count': sum(1 for c in confidences if 0.5 <= c < 0.7),
            'low_confidence_count': sum(1 for c in confidences if c < 0.5),
            'avg_sources_per_fact': sum(f['source_count'] for f in self.validated_facts) / len(self.validated_facts)
        }
