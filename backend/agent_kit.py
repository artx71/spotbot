"""
AgentKit - Proprietary Query Detection and Routing
Checks if queries require proprietary data access
"""

from typing import Dict, List, Optional
import re


class AgentKit:
    """AgentKit for detecting proprietary queries and routing to appropriate handlers"""
    
    def __init__(self):
        # Proprietary query indicators
        self.proprietary_keywords = [
            "prize", "prizes", "reward", "allocation", "money", "cash",
            "challenge", "challenges", "track", "category",
            "judge", "judges", "mentor", "evaluator",
            "timeline", "duration", "schedule",
            "theme", "hackathon", "similar", "past", "previous", "example"
        ]
        
        # Query patterns that indicate proprietary data need
        self.proprietary_patterns = [
            r"suggest.*prize",
            r"recommend.*prize",
            r"what.*prize",
            r"how.*allocate",
            r"similar.*hackathon",
            r"past.*hackathon",
            r"example.*hackathon",
            r"what.*challenges",
            r"who.*judge",
            r"what.*timeline"
        ]
    
    def is_proprietary_query(self, query: str) -> bool:
        """
        Check if query requires proprietary data access
        
        Args:
            query: User query string
            
        Returns:
            True if query requires proprietary data, False otherwise
        """
        query_lower = query.lower()
        
        # Check for proprietary keywords
        has_keywords = any(keyword in query_lower for keyword in self.proprietary_keywords)
        
        # Check for proprietary patterns
        has_patterns = any(re.search(pattern, query_lower) for pattern in self.proprietary_patterns)
        
        return has_keywords or has_patterns
    
    def get_query_type(self, query: str) -> str:
        """
        Classify query type for routing
        
        Returns:
            Query type: "prize", "challenge", "judge", "timeline", "theme", "general"
        """
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["prize", "prizes", "reward", "money", "allocation", "cash"]):
            return "prize"
        elif any(word in query_lower for word in ["challenge", "challenges", "track", "category"]):
            return "challenge"
        elif any(word in query_lower for word in ["judge", "judges", "mentor", "evaluator"]):
            return "judge"
        elif any(word in query_lower for word in ["timeline", "duration", "days", "schedule", "how long"]):
            return "timeline"
        elif any(word in query_lower for word in ["theme", "title", "idea", "topic", "what kind"]):
            return "theme"
        else:
            return "general"
    
    def extract_query_params(self, query: str) -> Dict:
        """
        Extract parameters from query for RAG retrieval
        
        Returns:
            Dictionary with extracted parameters
        """
        query_lower = query.lower()
        params = {
            "theme": None,
            "prize_amount": None,
            "hackathon_type": None
        }
        
        # Extract theme
        themes = ["ai", "artificial intelligence", "climate", "healthcare", "fintech", 
                  "education", "edtech", "sustainability", "medical", "financial"]
        for theme in themes:
            if theme in query_lower:
                theme_map = {
                    "ai": "Artificial Intelligence",
                    "artificial intelligence": "Artificial Intelligence",
                    "climate": "Climate & Sustainability",
                    "healthcare": "Healthcare & Medical",
                    "medical": "Healthcare & Medical",
                    "fintech": "Financial Technology",
                    "financial": "Financial Technology",
                    "education": "Education Technology",
                    "edtech": "Education Technology",
                    "sustainability": "Climate & Sustainability"
                }
                params["theme"] = theme_map.get(theme, theme.title())
                break
        
        # Extract prize amount
        amounts = re.findall(r'\$?(\d+(?:,\d{3})*(?:\.\d{2})?)', query.replace(',', ''))
        if amounts:
            try:
                params["prize_amount"] = float(amounts[0])
            except:
                pass
        
        # Extract hackathon type
        if "sprint" in query_lower or "24" in query_lower:
            params["hackathon_type"] = "sprint"
        elif "extended" in query_lower or "72" in query_lower:
            params["hackathon_type"] = "extended"
        elif "deep" in query_lower or "week" in query_lower:
            params["hackathon_type"] = "deep_dive"
        else:
            params["hackathon_type"] = "standard"
        
        return params


# Global AgentKit instance
agent_kit = AgentKit()
