# query_analyzer.py - Auto-generated
"""
Query analyzer for processing user queries
"""
import logging
import re
from typing import Dict, Any, Optional, List, Tuple

from config import settings

logger = logging.getLogger(__name__)

class QueryAnalyzer:
    """Analyzes user queries to extract key information"""
    
    def __init__(self):
        """Initialize the query analyzer"""
        # Load country and topic keywords
        self.countries = settings.COUNTRIES
        self.topics = settings.TOPICS
        
        # Prepare regex patterns for country and topic detection
        self.country_patterns = self._prepare_country_patterns()
        self.topic_patterns = self._prepare_topic_patterns()
    
    def analyze_query(self, query: str) -> Dict[str, Any]:
        """
        Analyze a user query to extract country, topic, and other metadata
        
        Args:
            query: User query string
            
        Returns:
            Dictionary with extracted information
        """
        result = {
            "query": query,
            "country": None,
            "topic": None,
            "is_question": self._is_question(query),
            "is_procedural": self._is_procedural_query(query),
            "keywords": self._extract_keywords(query)
        }
        
        # Extract country and topic
        result["country"] = self._extract_country(query)
        result["topic"] = self._extract_topic(query)
        
        logger.info(f"Query analysis: {result}")
        return result
    
    def _prepare_country_patterns(self) -> Dict[str, List[str]]:
        """
        Prepare regex patterns for country detection
        
        Returns:
            Dictionary mapping countries to their patterns
        """
        patterns = {}
        
        # Pattern for Australia
        patterns["Australia"] = [
            r'\baustralia\b', 
            r'\baustralian\b',
            r'\bau\b',
            r'\bsydney\b',
            r'\bmelbourne\b',
            r'\bperth\b',
            r'\bbrisbane\b',
            r'\bcanberra\b'
        ]
        
        # Pattern for Canada
        patterns["Canada"] = [
            r'\bcanada\b',
            r'\bcanadian\b',
            r'\bca\b',
            r'\btoronto\b',
            r'\bmontreal\b',
            r'\bvancouver\b',
            r'\bottawa\b'
        ]
        
        # Pattern for France
        patterns["France"] = [
            r'\bfrance\b',
            r'\bfrench\b',
            r'\bfr\b',
            r'\bparis\b',
            r'\blyon\b',
            r'\bnice\b',
            r'\bmarseille\b'
        ]
        
        return patterns
    
    def _prepare_topic_patterns(self) -> Dict[str, List[str]]:
        """
        Prepare regex patterns for topic detection
        
        Returns:
            Dictionary mapping topics to their patterns
        """
        patterns = {}
        
        # Pattern for visa
        patterns["visa"] = [
            r'\bvisa\b',
            r'\bpassport\b',
            r'\bentry\b',
            r'\bpermit\b',
            r'\bstay\b',
            r'\bworking holiday\b',
            r'\bwork visa\b',
            r'\bstudent visa\b',
            r'\btourist visa\b',
            r'\bvisitor visa\b',
            r'\bwhv\b',
            r'\beia\b'
        ]
        
        # Pattern for insurance
        patterns["insurance"] = [
            r'\binsurance\b',
            r'\bmedical\b',
            r'\bhealth cover\b',
            r'\bhealthcare\b',
            r'\bcoverage\b',
            r'\bhealth insurance\b',
            r'\btravel insurance\b',
            r'\bmedical coverage\b'
        ]
        
        # Pattern for immigration
        patterns["immigration"] = [
            r'\bimmigration\b',
            r'\bimmigrate\b',
            r'\bpermanent residence\b',
            r'\bpr\b',
            r'\bcitizenship\b',
            r'\bnaturalization\b',
            r'\bresidence\b',
            r'\bsettle\b',
            r'\bsettlement\b',
            r'\bmigrate\b'
        ]
        
        return patterns
    
    def _extract_country(self, query: str) -> Optional[str]:
        """
        Extract country from query
        
        Args:
            query: User query
            
        Returns:
            Country name or None
        """
        query_lower = query.lower()
        
        for country, patterns in self.country_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    return country
        
        return None
    
    def _extract_topic(self, query: str) -> Optional[str]:
        """
        Extract topic from query
        
        Args:
            query: User query
            
        Returns:
            Topic name or None
        """
        query_lower = query.lower()
        
        for topic, patterns in self.topic_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    return topic
        
        return None
    
    def _is_question(self, query: str) -> bool:
        """
        Check if query is a question
        
        Args:
            query: User query
            
        Returns:
            True if query is a question
        """
        # Check for question marks
        if "?" in query:
            return True
        
        # Check for question words
        question_words = [
            r'^what', r'^how', r'^where', r'^when', r'^why', r'^who', 
            r'^can i', r'^do i', r'^does', r'^is', r'^are', r'^will'
        ]
        
        query_lower = query.lower()
        for word in question_words:
            if re.search(word, query_lower):
                return True
        
        return False
    
    def _is_procedural_query(self, query: str) -> bool:
        """
        Check if query is about a procedure or process
        
        Args:
            query: User query
            
        Returns:
            True if query is procedural
        """
        procedural_patterns = [
            r'how (to|do)',
            r'process',
            r'procedure',
            r'steps',
            r'requirement',
            r'apply',
            r'application',
            r'submit',
            r'document',
            r'form',
            r'file',
            r'what (do|should) i need'
        ]
        
        query_lower = query.lower()
        for pattern in procedural_patterns:
            if re.search(pattern, query_lower):
                return True
        
        return False
    
    def _extract_keywords(self, query: str) -> List[str]:
        """
        Extract important keywords from query
        
        Args:
            query: User query
            
        Returns:
            List of keywords
        """
        # Remove common stop words
        stop_words = [
            "a", "an", "the", "and", "or", "but", "is", "are", "was", "were",
            "be", "been", "being", "to", "of", "for", "with", "about", "in",
            "on", "at", "by", "this", "that", "these", "those", "it", "its"
        ]
        
        # Tokenize and filter
        words = re.findall(r'\b\w+\b', query.lower())
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        return keywords