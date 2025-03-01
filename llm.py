import os
from typing import Dict, Any, Optional, List, Union

from langchain_core.language_models.llms import LLM
from transformers import pipeline

# Simple dummy LLM that doesn't require downloading large models
class DummyLLM(LLM):
    """Dummy LLM for demonstration purposes."""
    
    def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        """Process the prompt and return a response."""
        # Simple rule-based response generation
        response = ""
        
        if "category" in prompt.lower():
            if "access" in prompt.lower() or "dashboard" in prompt.lower() or "403" in prompt.lower():
                response = """
{
  "category": "access",
  "priority": 3,
  "key_points": ["Cannot access admin dashboard", "Getting 403 error", "Needs to process payroll"],
  "required_expertise": ["access control", "permissions", "admin systems"],
  "sentiment": -0.5,
  "urgency_indicators": ["ASAP", "today"],
  "business_impact": "Blocking payroll processing",
  "suggested_response_type": "access_issue"
}
"""
            elif "billing" in prompt.lower() or "invoice" in prompt.lower():
                response = """
{
  "category": "billing",
  "priority": 2,
  "key_points": ["Question about billing cycle", "Pro-rating confusion", "Invoice date discrepancy"],
  "required_expertise": ["billing", "finance", "customer accounts"],
  "sentiment": -0.1,
  "urgency_indicators": [],
  "business_impact": "Minimal, requesting clarification",
  "suggested_response_type": "billing_inquiry"
}
"""
            elif "feature" in prompt.lower() or "request" in prompt.lower():
                response = """
{
  "category": "feature",
  "priority": 1,
  "key_points": ["Requesting CSV export", "Currently manual process", "Time-consuming"],
  "required_expertise": ["product management", "development"],
  "sentiment": 0.2,
  "urgency_indicators": [],
  "business_impact": "Efficiency improvement opportunity",
  "suggested_response_type": "feature_request"
}
"""
            else:
                response = """
{
  "category": "technical",
  "priority": 2,
  "key_points": ["System not working", "Unspecified issue", "Needs troubleshooting"],
  "required_expertise": ["technical support", "troubleshooting"],
  "sentiment": -0.4,
  "urgency_indicators": ["help"],
  "business_impact": "User blocked from normal operation",
  "suggested_response_type": "technical_issue"
}
"""
        elif "response" in prompt.lower():
            if "access" in prompt.lower():
                response = """
{
  "response_text": "Hello John,\\n\\nI understand you're having trouble accessing the admin dashboard. Let me help you resolve this.\\n\\nIt appears you're encountering a 403 error, which typically indicates a permissions issue. This could be due to recent security updates or account changes.\\n\\nPlease try the following steps:\\n1. Clear your browser cache and cookies\\n2. Try accessing from an incognito/private window\\n3. Ensure you're using the correct admin credentials\\n\\nIf these steps don't resolve the issue, our technical team will need to investigate your account permissions.\\n\\nPriority Status: HIGH\\n\\nEstimated Resolution: Today (within 2-3 hours)\\n\\nPlease let me know if you need any clarification.\\n\\nBest regards,\\nBaguette Support",
  "confidence_score": 0.85,
  "requires_approval": false,
  "suggested_actions": ["Escalate to Access Control team if not resolved within 1 hour", "Follow up to confirm payroll processing was completed"]
}
"""
            elif "billing" in prompt.lower():
                response = """
{
  "response_text": "Hi Sarah,\\n\\nThank you for your inquiry about our billing cycle.\\n\\nOur system bills from the 15th of each month. Since you signed up on the 20th, your first invoice includes a pro-rated amount for the period from the 20th to the 14th of the following month.\\n\\nSubsequent invoices will cover the full period from the 15th to the 14th of the next month.\\n\\nIf you prefer to align your billing date with your signup date, we can arrange this for you.\\n\\nIf you have any questions, don't hesitate to ask.\\n\\nBest regards,\\nBaguette Billing Team",
  "confidence_score": 0.92,
  "requires_approval": false,
  "suggested_actions": ["Offer billing date adjustment if requested", "Attach pro-rating calculation example"]
}
"""
            else:
                response = """
{
  "response_text": "Hello Customer,\\n\\nThank you for contacting Baguette Support.\\n\\nI understand you're experiencing an issue with our system. To better assist you, could you please provide some additional details:\\n\\n1. What specific feature or area were you trying to use?\\n2. Are you seeing any error messages?\\n3. When did you first notice this issue?\\n\\nOnce I have this information, I'll be able to help you more effectively.\\n\\nBest regards,\\nBaguette Support",
  "confidence_score": 0.65,
  "requires_approval": true,
  "suggested_actions": ["Flag for follow-up if no response within 24 hours", "Assign to technical specialist once details provided"]
}
"""
        
        return response
    
    @property
    def _identifying_params(self) -> Dict[str, Any]:
        return {"name": "dummy_llm"}
    
    @property
    def _llm_type(self) -> str:
        return "dummy"


def get_default_llm() -> LLM:
    """
    Get the default LLM instance.
    
    Returns:
        LangChain-compatible LLM instance
    """
    return DummyLLM()