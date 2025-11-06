from typing import List, Dict, Optional
import importlib
import mock_data
from json_db import json_db


class RAGService:
    def __init__(self):
        self.hackathons = mock_data.MOCK_HACKATHONS
        self.prize_recommendations = mock_data.PRIZE_RECOMMENDATIONS
        self.timeline_recommendations = mock_data.TIMELINE_RECOMMENDATIONS
        self.approved_embeddings: List[Dict] = []
        self._load_approved_embeddings()
    
    def _load_approved_embeddings(self):
        try:
            self.approved_embeddings = json_db.get_approved_embeddings()
        except Exception as e:
            print(f"[RAG] Error loading approved embeddings: {e}")
            self.approved_embeddings = []
    
    def train(self):
        try:
            importlib.reload(mock_data)
            self.hackathons = mock_data.MOCK_HACKATHONS
            self.prize_recommendations = mock_data.PRIZE_RECOMMENDATIONS
            self.timeline_recommendations = mock_data.TIMELINE_RECOMMENDATIONS
            self._load_approved_embeddings()
            print(f"[Training] Reloaded mock data - {len(self.hackathons)} hackathons available")
            print(f"[Training] Loaded {len(self.approved_embeddings)} approved embeddings")
            return True
        except Exception as e:
            print(f"[Training] Error reloading data: {e}")
            return False
    
    def _extract_keywords(self, query: str) -> List[str]:
        query_lower = query.lower()
        keywords = []
        
        themes = ["ai", "artificial intelligence", "climate", "healthcare", "fintech", 
                  "education", "edtech", "sustainability", "medical", "financial"]
        for theme in themes:
            if theme in query_lower:
                keywords.append(theme)
        
        if any(word in query_lower for word in ["prize", "prizes", "reward", "money", "cash", "$"]):
            keywords.append("prize")
        
        if any(word in query_lower for word in ["challenge", "challenges", "track", "category"]):
            keywords.append("challenge")
        
        if any(word in query_lower for word in ["judge", "judges", "mentor", "evaluator"]):
            keywords.append("judge")
        
        if any(word in query_lower for word in ["timeline", "duration", "days", "time", "schedule"]):
            keywords.append("timeline")
        
        return keywords
    
    def search_hackathons(self, query: str, limit: int = 3) -> List[Dict]:
        keywords = self._extract_keywords(query)
        query_lower = query.lower()
        scored_hackathons = []
        
        for hackathon in self.hackathons:
            score = 0
            
            if any(keyword in hackathon["theme"].lower() for keyword in keywords):
                score += 3
            
            if any(keyword in hackathon["title"].lower() for keyword in keywords):
                score += 2
            if any(keyword in hackathon["description"].lower() for keyword in keywords):
                score += 1
            
            if "prize" in keywords and any(word in query_lower for word in ["prize", "prizes"]):
                score += 1
            if "challenge" in keywords and any(word in query_lower for word in ["challenge", "challenges"]):
                score += 1
            
            if score > 0:
                scored_hackathons.append((score, hackathon))
        
        scored_hackathons.sort(key=lambda x: x[0], reverse=True)
        return [hackathon for _, hackathon in scored_hackathons[:limit]]
    
    def get_prize_recommendation(self, total_prize: float, theme: Optional[str] = None) -> Dict:
        if theme:
            theme_lower = theme.lower()
            for embedding in self.approved_embeddings:
                emb_theme = embedding.get("metadata", {}).get("theme", "").lower()
                if emb_theme and (emb_theme in theme_lower or theme_lower in emb_theme):
                    ratios = embedding.get("metadata", {}).get("prize_allocation_ratios")
                    if ratios:
                        return {
                            "category": "learned",
                            "first": total_prize * ratios["first"],
                            "second": total_prize * ratios["second"],
                            "third": total_prize * ratios["third"],
                            "ratios": ratios,
                            "source": "learned",
                            "theme": embedding.get("metadata", {}).get("theme")
                        }
        
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
            "ratios": ratios,
            "source": "default"
        }
    
    def get_timeline_recommendation(self, hackathon_type: str = "standard") -> Dict:
        return self.timeline_recommendations.get(
            hackathon_type, 
            self.timeline_recommendations["standard"]
        )
    
    def get_similar_challenges(self, theme: str, limit: int = 4) -> List[str]:
        similar_hackathons = self.search_hackathons(theme, limit=2)
        challenges = []
        for hackathon in similar_hackathons:
            challenges.extend(hackathon.get("challenges", []))
        return challenges[:limit]
    
    def get_similar_judges(self, theme: str, limit: int = 4) -> List[str]:
        similar_hackathons = self.search_hackathons(theme, limit=2)
        judges = []
        for hackathon in similar_hackathons:
            judges.extend(hackathon.get("judges", []))
        return judges[:limit]


rag_service = RAGService()
