from typing import List, Dict, Optional
from rag_service import rag_service
from agent_kit import agent_kit
from anonymization_service import anonymization_service
from llm_service import llm_service
import re
from datetime import datetime


class ChatService:
    def __init__(self):
        self.conversation_history: Dict[str, List[Dict]] = {}
        self.hackathon_drafts: Dict[str, Dict] = {}
    
    def _extract_number(self, text: str) -> Optional[float]:
        amounts = re.findall(r'\$?(\d+(?:,\d{3})*(?:\.\d{2})?)', text.replace(',', ''))
        if amounts:
            try:
                return float(amounts[0])
            except:
                pass
        return None
    
    def _extract_hackathon_info(self, query: str, user_id: str) -> Dict:
        query_lower = query.lower()
        
        if user_id not in self.hackathon_drafts:
            self.hackathon_drafts[user_id] = {
                "title": "",
                "theme": "",
                "description": "",
                "prizes": {},
                "challenges": [],
                "judges": [],
                "duration_days": 48,
                "participants": 0
            }
        
        draft = self.hackathon_drafts[user_id]
        updated = False
        
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
                draft["theme"] = theme_map.get(theme, theme.title())
                updated = True
                break
        
        if any(word in query_lower for word in ["title", "called", "name it", "name is"]):
            title_patterns = [
                r"(?:title|called|name it|name is)[:\s]+(.+?)(?:\.|$)",
                r"i want (?:to|a) (?:create|make|organize) (?:a|an) (.+?)(?: hackathon|$)",
            ]
            for pattern in title_patterns:
                match = re.search(pattern, query, re.IGNORECASE)
                if match:
                    draft["title"] = match.group(1).strip()
                    updated = True
                    break
        
        if len(query) > 20 and not any(word in query_lower for word in ["prize", "challenge", "judge", "timeline", "theme", "title"]):
            if not draft["description"]:
                draft["description"] = query
                updated = True
        
        prize_amount = self._extract_number(query)
        if prize_amount:
            theme = draft.get("theme")
            recommendation = rag_service.get_prize_recommendation(prize_amount, theme)
            draft["prizes"] = {
                "total": f"${prize_amount:,.0f}",
                "first": f"${recommendation['first']:,.0f}",
                "second": f"${recommendation['second']:,.0f}",
                "third": f"${recommendation['third']:,.0f}"
            }
            updated = True
        
        if any(word in query_lower for word in ["timeline", "duration", "days", "how long"]):
            hack_type = "standard"
            if "sprint" in query_lower or "24" in query_lower:
                hack_type = "sprint"
            elif "extended" in query_lower or "72" in query_lower:
                hack_type = "extended"
            elif "deep" in query_lower or "week" in query_lower:
                hack_type = "deep_dive"
            
            recommendation = rag_service.get_timeline_recommendation(hack_type)
            draft["duration_days"] = recommendation["days"]
            updated = True
        
        return draft, updated
    
    def _generate_response(self, query: str, user_id: str, context: Dict = None) -> tuple:
        query_lower = query.lower().strip()
        response_parts = []
        hackathon_data = None
        draft = self.hackathon_drafts.get(user_id, {})
        
        is_config_command = (
            query_lower in ["prize pool", "prize", "prizes", "prize allocation"] or
            query_lower.startswith("prize pool") or
            query_lower.startswith("prize allocation")
        )
        
        if is_config_command:
            prize_amount = self._extract_number(query)
            
            if draft.get("theme"):
                theme = draft["theme"]
                current_prizes = draft.get("prizes", {})
                
                if prize_amount:
                    query_params = agent_kit.extract_query_params(query)
                    query_params["theme"] = theme
                    query_params["prize_amount"] = prize_amount
                    
                    anonymized_suggestion = anonymization_service.get_anonymized_prize_suggestion(
                        prize_amount, theme
                    )
                    
                    if anonymized_suggestion:
                        formatted_response = llm_service.format_prize_response(
                            anonymized_suggestion, query_params
                        )
                        response_parts.append(formatted_response)
                        draft["prizes"] = {
                            "total": f"${prize_amount:,.0f}",
                            "first": f"${anonymized_suggestion['suggestion']['first']:,.0f}",
                            "second": f"${anonymized_suggestion['suggestion']['second']:,.0f}",
                            "third": f"${anonymized_suggestion['suggestion']['third']:,.0f}"
                        }
                    else:
                        recommendation = rag_service.get_prize_recommendation(prize_amount, theme)
                        source_msg = f" (learned from {recommendation.get('theme', 'similar')} hackathons)" if recommendation.get('source') == 'learned' else ""
                        response_parts.append(
                            f"Based on similar hackathons{source_msg} with a ${prize_amount:,.0f} prize pool, "
                            f"I recommend:\n"
                            f"• 1st Place: ${recommendation['first']:,.0f} ({recommendation['ratios']['first']*100:.0f}%)\n"
                            f"• 2nd Place: ${recommendation['second']:,.0f} ({recommendation['ratios']['second']*100:.0f}%)\n"
                            f"• 3rd Place: ${recommendation['third']:,.0f} ({recommendation['ratios']['third']*100:.0f}%)"
                        )
                        draft["prizes"] = {
                            "total": f"${prize_amount:,.0f}",
                            "first": f"${recommendation['first']:,.0f}",
                            "second": f"${recommendation['second']:,.0f}",
                            "third": f"${recommendation['third']:,.0f}"
                        }
                    self.hackathon_drafts[user_id] = draft
                elif current_prizes.get("total"):
                    response_parts.append(f"Current prize pool for your {theme} hackathon:")
                    response_parts.append(f"**Total:** {current_prizes.get('total', 'Not set')}")
                    if current_prizes.get("first"):
                        response_parts.append(f"• 1st Place: {current_prizes.get('first')}")
                        response_parts.append(f"• 2nd Place: {current_prizes.get('second')}")
                        response_parts.append(f"• 3rd Place: {current_prizes.get('third')}")
                    response_parts.append("\nWould you like to change this? Just tell me the new total amount!")
                else:
                    response_parts.append(f"Great! Let's configure the prize pool for your {theme} hackathon.")
                    response_parts.append("\nWhat's your total prize pool amount? (e.g., $25,000)")
                    response_parts.append("\nOr I can suggest an allocation based on similar hackathons. Just tell me the total amount!")
            else:
                if prize_amount:
                    response_parts.append(f"Great! I see you want a ${prize_amount:,.0f} prize pool.")
                    response_parts.append("\nWhat theme is your hackathon? (e.g., AI, Healthcare, Climate)")
                    response_parts.append("Then I can suggest the best allocation based on similar hackathons.")
                else:
                    response_parts.append("I'd love to help you set up the prize pool!")
                    response_parts.append("\nFirst, let's start with your hackathon theme. What area are you interested in? (e.g., AI, Healthcare, Climate)")
                    response_parts.append("Then we can configure the prize allocation.")
            return "\n".join(response_parts), hackathon_data
        
        is_challenges_command = (
            query_lower in ["challenges", "challenge", "tracks", "track", "categories", "category"] or
            query_lower.startswith("challenge")
        )
        
        if is_challenges_command:
            if draft.get("theme"):
                theme = draft["theme"]
                challenges = rag_service.get_similar_challenges(theme, limit=4)
                response_parts.append(f"Here are some popular challenges for {theme} hackathons:")
                for i, challenge in enumerate(challenges, 1):
                    response_parts.append(f"{i}. {challenge}")
                response_parts.append(f"\nWould you like to use these, or tell me about specific challenges you have in mind?")
                draft["challenges"] = challenges
                self.hackathon_drafts[user_id] = draft
            else:
                response_parts.append("I can help you set up challenges for your hackathon!")
                response_parts.append("\nFirst, what theme is your hackathon? (e.g., AI, Healthcare, Climate)")
                response_parts.append("Then I can suggest relevant challenges based on similar successful hackathons.")
            return "\n".join(response_parts), hackathon_data
        
        is_judges_command = (
            query_lower in ["judges", "judge", "mentors", "mentor", "evaluators", "evaluator"] or
            query_lower.startswith("judge")
        )
        
        if is_judges_command:
            if draft.get("theme"):
                theme = draft["theme"]
                judges = rag_service.get_similar_judges(theme, limit=4)
                response_parts.append(f"Here are some ideal judges for {theme} hackathons:")
                for judge in judges:
                    response_parts.append(f"• {judge}")
                response_parts.append(f"\nWould you like to use these suggestions, or tell me about specific judges you have in mind?")
                draft["judges"] = judges
                self.hackathon_drafts[user_id] = draft
            else:
                response_parts.append("I can help you find judges for your hackathon!")
                response_parts.append("\nFirst, what theme is your hackathon? (e.g., AI, Healthcare, Climate)")
                response_parts.append("Then I can suggest relevant judges based on similar successful hackathons.")
            return "\n".join(response_parts), hackathon_data
        
        is_timeline_command = (
            query_lower in ["timeline", "duration", "schedule", "how long", "days"] or
            query_lower.startswith("timeline") or
            query_lower.startswith("duration") or
            query_lower.startswith("schedule")
        )
        
        if is_timeline_command:
            if draft.get("theme"):
                theme = draft["theme"]
                current_duration = draft.get("duration_days", 48)
                response_parts.append(f"Current timeline for your {theme} hackathon:")
                response_parts.append(f"**Duration:** {current_duration} days")
                response_parts.append(f"\nWhat duration would you like?")
                response_parts.append("• 24 hours (Sprint)")
                response_parts.append("• 48 hours (Standard)")
                response_parts.append("• 72 hours (Extended)")
                response_parts.append("• 120+ days (Deep dive)")
                response_parts.append("\nOr just tell me how many days you want!")
            else:
                response_parts.append("I can help you set the timeline for your hackathon!")
                response_parts.append("\nFirst, what theme is your hackathon? (e.g., AI, Healthcare, Climate)")
                response_parts.append("Then I can suggest an appropriate duration based on similar hackathons.")
            return "\n".join(response_parts), hackathon_data
        
        if any(phrase in query_lower for phrase in ["create", "make", "build", "set up", "organize", "ready to create", "generate"]):
            draft, updated = self._extract_hackathon_info(query, user_id)
            
            if draft.get("theme"):
                if not draft["title"]:
                    draft["title"] = f"{draft['theme']} Hackathon 2025"
                
                if not draft["description"]:
                    similar = rag_service.search_hackathons(draft["theme"], limit=1)
                    draft["description"] = similar[0].get("description", f"Build innovative solutions for {draft['theme']}") if similar else f"Build innovative solutions for {draft['theme']}"
                
                if not draft["challenges"]:
                    draft["challenges"] = rag_service.get_similar_challenges(draft["theme"], limit=4)
                
                if not draft["prizes"]:
                    draft["prizes"] = {
                        "total": "$20,000",
                        "first": "$12,000",
                        "second": "$6,000",
                        "third": "$2,000"
                    }
                
                if not draft["judges"]:
                    draft["judges"] = rag_service.get_similar_judges(draft["theme"], limit=4)
                
                hackathon_data = draft.copy()
                response_parts.append("Great! I've prepared your hackathon configuration. Here's what I've set up:\n")
                response_parts.append(f"**Title:** {draft['title']}")
                response_parts.append(f"**Theme:** {draft['theme']}")
                response_parts.append(f"**Description:** {draft['description']}")
                response_parts.append(f"**Duration:** {draft['duration_days']} days")
                response_parts.append(f"**Prize Pool:** {draft['prizes'].get('total', 'TBD')}")
                response_parts.append(f"\n**Challenges:**")
                for challenge in draft['challenges']:
                    response_parts.append(f"• {challenge}")
                response_parts.append(f"\n**Suggested Judges:**")
                for judge in draft['judges'][:3]:
                    response_parts.append(f"• {judge}")
                response_parts.append("\nYou can click the 'Create' button to finalize your hackathon, or tell me if you'd like to change anything!")
            else:
                response_parts.append("I'd love to help you create a hackathon! Let's start with the basics:")
                response_parts.append("• What theme or focus area are you interested in? (e.g., AI, Healthcare, Climate, FinTech)")
                response_parts.append("• What's the prize pool amount? (optional)")
                response_parts.append("• How long should the hackathon be? (e.g., 24 hours, 48 hours, 72 hours)")
        
        elif any(word in query_lower for word in ["prize", "prizes", "reward", "money", "allocation"]):
            if agent_kit.is_proprietary_query(query):
                query_params = agent_kit.extract_query_params(query)
                prize_amount = query_params.get("prize_amount") or self._extract_number(query)
                
                if prize_amount:
                    theme = query_params.get("theme") or draft.get("theme")
                    anonymized_suggestion = anonymization_service.get_anonymized_prize_suggestion(prize_amount, theme)
                    
                    if anonymized_suggestion:
                        formatted_response = llm_service.format_prize_response(anonymized_suggestion, query_params)
                        response_parts.append(formatted_response)
                    else:
                        recommendation = rag_service.get_prize_recommendation(prize_amount, theme)
                        source_msg = f" (learned from {recommendation.get('theme', 'similar')} hackathons)" if recommendation.get('source') == 'learned' else ""
                        response_parts.append(
                            f"Based on similar hackathons{source_msg} with a ${prize_amount:,.0f} prize pool, "
                            f"I recommend:\n"
                            f"• 1st Place: ${recommendation['first']:,.0f} ({recommendation['ratios']['first']*100:.0f}%)\n"
                            f"• 2nd Place: ${recommendation['second']:,.0f} ({recommendation['ratios']['second']*100:.0f}%)\n"
                            f"• 3rd Place: ${recommendation['third']:,.0f} ({recommendation['ratios']['third']*100:.0f}%)"
                        )
                    
                    draft, _ = self._extract_hackathon_info(query, user_id)
                else:
                    similar = rag_service.search_hackathons(query, limit=2)
                    if similar:
                        response_parts.append("Here are prize examples from similar hackathons:")
                        for hack in similar[:2]:
                            prizes = hack.get("prizes", {})
                            response_parts.append(
                                f"• {hack['title']}: {prizes.get('total', 'N/A')} total "
                                f"({prizes.get('first', 'N/A')} / {prizes.get('second', 'N/A')} / {prizes.get('third', 'N/A')})"
                            )
            else:
                prize_amount = self._extract_number(query)
                if prize_amount:
                    theme = draft.get("theme")
                    recommendation = rag_service.get_prize_recommendation(prize_amount, theme)
                    source_msg = f" (learned from {recommendation.get('theme', 'similar')} hackathons)" if recommendation.get('source') == 'learned' else ""
                    response_parts.append(
                        f"For a ${prize_amount:,.0f} prize pool{source_msg}, I recommend:\n"
                        f"• 1st Place: ${recommendation['first']:,.0f}\n"
                        f"• 2nd Place: ${recommendation['second']:,.0f}\n"
                        f"• 3rd Place: ${recommendation['third']:,.0f}"
                    )
        
        elif any(word in query_lower for word in ["challenge", "challenges", "track", "category", "categories"]):
            theme = None
            for hack in rag_service.hackathons:
                if hack["theme"].lower() in query_lower:
                    theme = hack["theme"]
                    break
            
            if theme:
                challenges = rag_service.get_similar_challenges(theme)
                response_parts.append(f"For {theme} hackathons, popular challenges include:")
                for i, challenge in enumerate(challenges, 1):
                    response_parts.append(f"{i}. {challenge}")
                draft, _ = self._extract_hackathon_info(query, user_id)
                draft["challenges"] = challenges
            else:
                similar = rag_service.search_hackathons(query, limit=2)
                if similar:
                    response_parts.append("Here are challenge examples from similar hackathons:")
                    for hack in similar[:2]:
                        response_parts.append(f"\n{hack['title']} ({hack['theme']}):")
                        for challenge in hack.get("challenges", [])[:3]:
                            response_parts.append(f"• {challenge}")
        
        elif any(word in query_lower for word in ["theme", "title", "idea", "topic", "what kind", "want to", "interested in"]):
            draft, updated = self._extract_hackathon_info(query, user_id)
            similar = rag_service.search_hackathons(query, limit=3)
            
            if similar:
                response_parts.append("Here are some successful hackathon themes to inspire you:")
                for hack in similar:
                    response_parts.append(
                        f"\n• {hack['title']}\n"
                        f"  Theme: {hack['theme']}\n"
                        f"  Description: {hack['description']}"
                    )
                
                if updated and draft.get("theme"):
                    response_parts.append(f"\nI've noted your interest in {draft['theme']} hackathons!")
                    response_parts.append("What else would you like to configure? You can tell me about:")
                    response_parts.append("• Prize pool amount")
                    response_parts.append("• Duration/timeline")
                    response_parts.append("• Specific challenges")
                    response_parts.append("• Or just say 'create' when you're ready!")
            else:
                response_parts.append("That sounds interesting! To help you create the perfect hackathon, I'd like to know:")
                response_parts.append("• What theme or focus area? (e.g., AI, Healthcare, Climate)")
                response_parts.append("• What's your prize pool? (optional)")
                response_parts.append("• How many days? (e.g., 24, 48, 72)")
        
        else:
            draft, _ = self._extract_hackathon_info(query, user_id)
            
            if draft.get("theme"):
                response_parts.append(f"Great! I see you're working on a {draft['theme']} hackathon.")
                response_parts.append("\nWhat would you like to configure next?")
                response_parts.append("• Prize pool")
                response_parts.append("• Challenges")
                response_parts.append("• Judges")
                response_parts.append("• Timeline")
                response_parts.append("\nOr say 'create' when you're ready to finalize!")
            else:
                response_parts.append(
                    "I'm Spot, your AI-powered hackathon assistant! I'm here to help you create your custom hackathon and landing page.\n\n"
                    "Let's start by telling me about your hackathon idea:\n"
                    "• What theme or focus area are you interested in?\n"
                    "• What's the prize pool? (optional)\n"
                    "• How long should it be?\n\n"
                    "Or you can ask me about specific aspects like prizes, challenges, judges, or timelines!"
                )
        
        return "\n".join(response_parts) if response_parts else "I'm here to help! Can you tell me more about what you're planning?", hackathon_data
    
    def process_message(self, user_id: str, message: str) -> Dict:
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = []
        
        self.conversation_history[user_id].append({
            "role": "user",
            "content": message
        })
        
        response, hackathon_data = self._generate_response(message, user_id)
        
        self.conversation_history[user_id].append({
            "role": "assistant",
            "content": response
        })
        
        result = {
            "response": response,
            "history": self.conversation_history[user_id]
        }
        
        if hackathon_data:
            result["hackathon_data"] = hackathon_data
        
        return result
    
    def get_conversation_history(self, user_id: str) -> List[Dict]:
        return self.conversation_history.get(user_id, [])
    
    def clear_conversation(self, user_id: str):
        if user_id in self.conversation_history:
            del self.conversation_history[user_id]
        if user_id in self.hackathon_drafts:
            del self.hackathon_drafts[user_id]
    
    def get_hackathon_draft(self, user_id: str) -> Optional[Dict]:
        return self.hackathon_drafts.get(user_id)
    
    def create_hackathon(self, user_id: str, hackathon_data: Dict) -> Dict:
        hackathon_id = len(self.hackathon_drafts) + 1
        
        hackathon = {
            "id": hackathon_id,
            "title": hackathon_data.get("title", "Untitled Hackathon"),
            "theme": hackathon_data.get("theme", ""),
            "description": hackathon_data.get("description", ""),
            "prizes": hackathon_data.get("prizes", {}),
            "challenges": hackathon_data.get("challenges", []),
            "judges": hackathon_data.get("judges", []),
            "duration_days": hackathon_data.get("duration_days", 48),
            "participants": hackathon_data.get("participants", 0),
            "created_at": datetime.now().isoformat(),
            "status": "draft"
        }
        
        return hackathon


chat_service = ChatService()
