"""
Anonymization Service
Generates anonymized suggestions from proprietary data
"""

from typing import List, Dict, Optional
import json
import os


class AnonymizationService:
    """Service for generating anonymized suggestions from proprietary data"""
    
    def __init__(self):
        self.data_dir = os.path.join(os.path.dirname(__file__), "data")
        self.prize_recommendations = self._load_prize_recommendations()
    
    def _load_prize_recommendations(self) -> List[Dict]:
        """Load prize recommendations from JSON file"""
        try:
            file_path = os.path.join(self.data_dir, "prize_recommendations.json")
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    return data.get("recommendations", [])
        except Exception as e:
            print(f"Error loading prize recommendations: {e}")
        return []
    
    def get_anonymized_prize_suggestion(self, prize_amount: float, theme: Optional[str] = None) -> Optional[Dict]:
        """
        Get anonymized prize suggestion based on amount and theme
        
        Args:
            prize_amount: Total prize pool amount
            theme: Optional theme filter
            
        Returns:
            Anonymized suggestion dictionary or None
        """
        # Find matching recommendations
        matching_recs = []
        
        for rec in self.prize_recommendations:
            # Check prize pool range
            range_str = rec.get("prize_pool_range", "")
            if "-" in range_str:
                min_val, max_val = map(int, range_str.split("-"))
                if min_val <= prize_amount <= max_val:
                    # Check theme match if provided
                    if theme is None or rec.get("theme") == theme:
                        matching_recs.append(rec)
        
        if not matching_recs:
            # Fallback: use ratio-based calculation
            return self._generate_ratio_based_suggestion(prize_amount)
        
        # Use the first matching recommendation
        best_match = matching_recs[0]
        
        # Anonymize the suggestion
        return {
            "suggestion": {
                "first": best_match["allocations"]["first"],
                "second": best_match["allocations"]["second"],
                "third": best_match["allocations"]["third"],
                "total": prize_amount
            },
            "anonymized_source": best_match.get("anonymized_source", "Past similar hackathon"),
            "metadata": {
                "based_on": "Proprietary data from similar hackathons",
                "theme": best_match.get("theme"),
                "confidence": "high"
            }
        }
    
    def _generate_ratio_based_suggestion(self, prize_amount: float) -> Dict:
        """Generate suggestion using ratio-based approach"""
        if prize_amount < 15000:
            category = "small"
            ratios = {"first": 0.60, "second": 0.30, "third": 0.10}
        elif prize_amount < 30000:
            category = "medium"
            ratios = {"first": 0.50, "second": 0.30, "third": 0.20}
        else:
            category = "large"
            ratios = {"first": 0.45, "second": 0.35, "third": 0.20}
        
        return {
            "suggestion": {
                "first": prize_amount * ratios["first"],
                "second": prize_amount * ratios["second"],
                "third": prize_amount * ratios["third"],
                "total": prize_amount
            },
            "anonymized_source": "Standard allocation model",
            "metadata": {
                "based_on": "Industry-standard ratios",
                "category": category,
                "confidence": "medium"
            }
        }
    
    def anonymize_hackathon_data(self, hackathon_data: Dict) -> Dict:
        """
        Anonymize hackathon data for suggestions
        
        Args:
            hackathon_data: Raw hackathon data
            
        Returns:
            Anonymized version
        """
        anonymized = {
            "theme": hackathon_data.get("theme", "Unknown"),
            "prizes": {
                "total": hackathon_data.get("prizes", {}).get("total", "N/A"),
                "breakdown": "Available"
            },
            "duration_days": hackathon_data.get("duration_days", "N/A"),
            "participants": "Similar scale"
        }
        
        # Remove identifying information
        if "title" in hackathon_data:
            anonymized["anonymized_title"] = f"{hackathon_data['theme']} Hackathon"
        
        return anonymized


# Global anonymization service instance
anonymization_service = AnonymizationService()
