"""
LLM Service for formatting responses
Uses OpenAI to format human-readable outputs
"""

from typing import Dict, Optional
import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()


class LLMService:
    """Service for formatting responses using LLM"""
    
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            self.client = OpenAI(api_key=api_key)
            self.enabled = True
        else:
            self.client = None
            self.enabled = False
            print("Warning: OPENAI_API_KEY not set. LLM formatting disabled.")
    
    def format_prize_response(self, suggestion: Dict, query_context: Dict) -> str:
        """
        Format prize allocation suggestion into human-readable response
        
        Args:
            suggestion: Anonymized suggestion dictionary
            query_context: Context from query (theme, amount, etc.)
            
        Returns:
            Formatted human-readable response
        """
        if not self.enabled:
            # Fallback formatting without LLM
            return self._fallback_format_prize(suggestion, query_context)
        
        try:
            theme = query_context.get("theme", "similar")
            amount = suggestion["suggestion"]["total"]
            
            prompt = f"""Format this prize allocation suggestion into a friendly, conversational response:

Theme: {theme}
Prize Pool: ${amount:,.0f}
Recommendation: 1st: ${suggestion['suggestion']['first']:,.0f}, 2nd: ${suggestion['suggestion']['second']:,.0f}, 3rd: ${suggestion['suggestion']['third']:,.0f}
Based on: {suggestion.get('anonymized_source', 'Similar hackathons')}

Write a concise, helpful response (2-3 sentences) that:
- Mentions it's based on past similar hackathons
- Provides the allocation breakdown
- Ends with "Want details?" or similar engaging question

Keep it conversational and friendly."""
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Using gpt-4o-mini as GPT-5 is not available
                messages=[
                    {"role": "system", "content": "You are a helpful hackathon planning assistant. Format responses in a friendly, conversational tone."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error in LLM formatting: {e}")
            return self._fallback_format_prize(suggestion, query_context)
    
    def _fallback_format_prize(self, suggestion: Dict, query_context: Dict) -> str:
        """Fallback formatting when LLM is not available"""
        theme = query_context.get("theme", "similar")
        amount = suggestion["suggestion"]["total"]
        first = suggestion["suggestion"]["first"]
        second = suggestion["suggestion"]["second"]
        third = suggestion["suggestion"]["third"]
        
        response = f"Based on past {theme} hackathons, a balanced model could be ${first:,.0f} / ${second:,.0f} / ${third:,.0f}. Want details?"
        
        return response
    
    def format_general_response(self, data: Dict, query_type: str) -> str:
        """
        Format general responses based on query type
        
        Args:
            data: Retrieved data
            query_type: Type of query (challenge, judge, timeline, etc.)
            
        Returns:
            Formatted response
        """
        if not self.enabled:
            return self._fallback_format_general(data, query_type)
        
        try:
            prompt = f"""Format this hackathon planning information into a helpful, conversational response:

Query Type: {query_type}
Data: {str(data)}

Write a concise, friendly response that helps the user understand the information and suggests next steps."""
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful hackathon planning assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error in LLM formatting: {e}")
            return self._fallback_format_general(data, query_type)
    
    def _fallback_format_general(self, data: Dict, query_type: str) -> str:
        """Fallback formatting for general responses"""
        return f"Here's what I found for {query_type} based on similar hackathons. Want more details?"


# Global LLM service instance
llm_service = LLMService()
