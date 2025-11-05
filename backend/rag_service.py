"""
Simple RAG Service for SpotBot MVP
Retrieves relevant hackathon data based on user queries
"""

from typing import List, Dict, Optional
import importlib
import mock_data


class RAGService:
    """Retrieval-Augmented Generation service for proprietary hackathon data"""
    
    def __init__(self):
        self.hackathons = mock_data.MOCK_HACKATHONS
        self.prize_recommendations = mock_data.PRIZE_RECOMMENDATIONS
        self.timeline_recommendations = mock_data.TIMELINE_RECOMMENDATIONS
    
    def train(self):
        """
        Train/reload the bot with latest mock data
        This reloads the mock_data module to pick up any changes
        """
        try:
            # Reload the mock_data module to get latest data
            importlib.reload(mock_data)
            
            # Update internal data structures
            self.hackathons = mock_data.MOCK_HACKATHONS
            self.prize_recommendations = mock_data.PRIZE_RECOMMENDATIONS
            self.timeline_recommendations = mock_data.TIMELINE_RECOMMENDATIONS
            
            print(f"[Training] Reloaded mock data - {len(self.hackathons)} hackathons available")
            return True
        except Exception as e:
            print(f"[Training] Error reloading data: {e}")
            return False
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Extract keywords from user query for matching"""
        query_lower = query.lower()
        keywords = []
        
        # Theme keywords
        themes = ["ai", "artificial intelligence", "climate", "healthcare", "fintech", 
                  "education", "edtech", "sustainability", "medical", "financial"]
        for theme in themes:
            if theme in query_lower:
                keywords.append(theme)
        
        # Prize keywords
        if any(word in query_lower for word in ["prize", "prizes", "reward", "money", "cash", "$"]):
            keywords.append("prize")
        
        # Challenge keywords
        if any(word in query_lower for word in ["challenge", "challenges", "track", "category"]):
            keywords.append("challenge")
        
        # Judge keywords
        if any(word in query_lower for word in ["judge", "judges", "mentor", "evaluator"]):
            keywords.append("judge")
        
        # Timeline keywords
        if any(word in query_lower for word in ["timeline", "duration", "days", "time", "schedule"]):
            keywords.append("timeline")
        
        return keywords
    
    def search_hackathons(self, query: str, limit: int = 3) -> List[Dict]:
        """Search for relevant hackathons based on query"""
        keywords = self._extract_keywords(query)
        query_lower = query.lower()
        
        scored_hackathons = []
        
        for hackathon in self.hackathons:
            score = 0
            
            # Check theme match
            if any(keyword in hackathon["theme"].lower() for keyword in keywords):
                score += 3
            
            # Check title/description match
            if any(keyword in hackathon["title"].lower() for keyword in keywords):
                score += 2
            if any(keyword in hackathon["description"].lower() for keyword in keywords):
                score += 1
            
            # Direct keyword matches
            if "prize" in keywords:
                if any(word in query_lower for word in ["prize", "prizes"]):
                    score += 1
            if "challenge" in keywords:
                if any(word in query_lower for word in ["challenge", "challenges"]):
                    score += 1
            
            if score > 0:
                scored_hackathons.append((score, hackathon))
        
        # Sort by score and return top results
        scored_hackathons.sort(key=lambda x: x[0], reverse=True)
        return [hackathon for _, hackathon in scored_hackathons[:limit]]
    
    def get_prize_recommendation(self, total_prize: float) -> Dict:
        """Get prize allocation recommendation based on total prize pool"""
        if total_prize < 15000:
            category = "small"
        elif total_prize < 30000:
            category = "medium"
        else:
            category = "large"
        
        ratios = self.prize_recommendations[category]
        return {
            "category": category,
            "first": total_prize * ratios["first"],
            "second": total_prize * ratios["second"],
            "third": total_prize * ratios["third"],
            "ratios": ratios
        }
    
    def get_timeline_recommendation(self, hackathon_type: str = "standard") -> Dict:
        """Get timeline recommendation"""
        return self.timeline_recommendations.get(
            hackathon_type, 
            self.timeline_recommendations["standard"]
        )
    
    def get_similar_challenges(self, theme: str, limit: int = 4) -> List[str]:
        """Get challenge examples for a given theme"""
        similar_hackathons = self.search_hackathons(theme, limit=2)
        challenges = []
        for hackathon in similar_hackathons:
            challenges.extend(hackathon.get("challenges", []))
        return challenges[:limit]
    
    def get_similar_judges(self, theme: str, limit: int = 4) -> List[str]:
        """Get judge examples for a given theme"""
        similar_hackathons = self.search_hackathons(theme, limit=2)
        judges = []
        for hackathon in similar_hackathons:
            judges.extend(hackathon.get("judges", []))
        return judges[:limit]


# Global RAG service instance
rag_service = RAGService()
