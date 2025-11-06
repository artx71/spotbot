from typing import Dict
import re


class AgentKit:
    def __init__(self):
        self.proprietary_keywords = [
            "prize", "prizes", "reward", "allocation", "money", "cash",
            "challenge", "challenges", "track", "category",
            "judge", "judges", "mentor", "evaluator",
            "timeline", "duration", "schedule",
            "theme", "hackathon", "similar", "past", "previous", "example"
        ]
        
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
        query_lower = query.lower()
        has_keywords = any(keyword in query_lower for keyword in self.proprietary_keywords)
        has_patterns = any(re.search(pattern, query_lower) for pattern in self.proprietary_patterns)
        return has_keywords or has_patterns
    
    def get_query_type(self, query: str) -> str:
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
        return "general"
    
    def extract_query_params(self, query: str) -> Dict:
        query_lower = query.lower()
        params = {
            "theme": None,
            "prize_amount": None,
            "hackathon_type": None
        }
        
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
        
        themes = ["ai", "artificial intelligence", "climate", "healthcare", "fintech", 
                  "education", "edtech", "sustainability", "medical", "financial"]
        for theme in themes:
            if theme in query_lower:
                params["theme"] = theme_map.get(theme, theme.title())
                break
        
        amounts = re.findall(r'\$?(\d+(?:,\d{3})*(?:\.\d{2})?)', query.replace(',', ''))
        if amounts:
            try:
                params["prize_amount"] = float(amounts[0])
            except:
                pass
        
        if "sprint" in query_lower or "24" in query_lower:
            params["hackathon_type"] = "sprint"
        elif "extended" in query_lower or "72" in query_lower:
            params["hackathon_type"] = "extended"
        elif "deep" in query_lower or "week" in query_lower:
            params["hackathon_type"] = "deep_dive"
        else:
            params["hackathon_type"] = "standard"
        
        return params


agent_kit = AgentKit()
