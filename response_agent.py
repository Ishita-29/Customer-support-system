import re
from typing import Dict, List, Any, Optional
import json

class ResponseSuggestion:
    def __init__(self, response_text, confidence_score=0.0, requires_approval=False, 
                 suggested_actions=None):
        self.response_text = response_text
        self.confidence_score = confidence_score
        self.requires_approval = requires_approval
        self.suggested_actions = suggested_actions or []
    
    def to_dict(self):
        return {
            "response_text": self.response_text,
            "confidence_score": self.confidence_score,
            "requires_approval": self.requires_approval,
            "suggested_actions": self.suggested_actions
        }

class ResponseAgent:
    def __init__(self, llm=None):
        self.llm = llm
    
    async def generate_response(self, ticket_analysis, response_templates, context):
        """
        Generate a response to a ticket based on its analysis and available templates.
        
        Args:
            ticket_analysis: TicketAnalysis object with ticket classification
            response_templates: Dictionary of response templates
            context: Additional context information
            
        Returns:
            ResponseSuggestion object with the generated response
        """
        # Determine which template to use
        template_key = ticket_analysis.suggested_response_type
        
        # Fallback to a default template if the suggested one isn't available
        if template_key not in response_templates:
            if ticket_analysis.category.value in response_templates:
                template_key = ticket_analysis.category.value
            else:
                template_key = list(response_templates.keys())[0]
        
        template = response_templates[template_key]
        
        # Start building response variables
        response_vars = {}
        confidence_score = 0.8  # Default confidence
        requires_approval = False
        suggested_actions = []
        
        # Extract customer name
        customer_name = context.get("customer_name", "Customer")
        response_vars["name"] = customer_name
        
        # Fill in template variables based on ticket category and context
        if ticket_analysis.category.value == "access":
            response_vars.update(self._generate_access_response_vars(ticket_analysis, context))
            suggested_actions = [
                "Verify user permissions in the admin system",
                "Check for recent security updates that might affect access"
            ]
            
            # Add escalation if urgent
            if ticket_analysis.priority.value >= 3:
                suggested_actions.append("Escalate to access control team if not resolved within 1 hour")
            
        elif ticket_analysis.category.value == "billing":
            response_vars.update(self._generate_billing_response_vars(ticket_analysis, context))
            suggested_actions = [
                "Verify billing records",
                "Consider offering billing adjustments if appropriate"
            ]
            
        elif ticket_analysis.category.value == "feature":
            response_vars.update(self._generate_feature_response_vars(ticket_analysis, context))
            suggested_actions = [
                "Log feature request in product backlog",
                "Check with product team about similar planned features"
            ]
            
        else:  # technical
            response_vars.update(self._generate_technical_response_vars(ticket_analysis, context))
            suggested_actions = [
                "Document the issue in internal knowledge base",
                "Check for similar recent technical issues"
            ]
            
            # Add escalation if urgent
            if ticket_analysis.priority.value >= 3:
                suggested_actions.append("Escalate to technical specialists if not resolved within 2 hours")
        
        # Check if approval should be required
        if ticket_analysis.priority.value == 4:  # URGENT
            requires_approval = True
            suggested_actions.append("Supervisory review required due to priority")
        
        # Adjust confidence based on ambiguity and sentiment
        if len(ticket_analysis.key_points) <= 1:
            confidence_score -= 0.2  # Less confident with vague tickets
        
        if ticket_analysis.sentiment < -0.5:
            confidence_score -= 0.1  # Less confident with very negative sentiment
            suggested_actions.append("Follow up personally due to customer sentiment")
        
        # Generate the response text by filling in the template
        response_text = self._fill_template(template, response_vars)
        
        # Create and return the response suggestion
        return ResponseSuggestion(
            response_text=response_text,
            confidence_score=max(0.1, min(confidence_score, 1.0)),  # Clamp between 0.1 and 1.0
            requires_approval=requires_approval,
            suggested_actions=suggested_actions
        )
    
    def _generate_access_response_vars(self, ticket_analysis, context):
        vars = {}
        
        # Determine the feature they're trying to access
        if any("dashboard" in point.lower() for point in ticket_analysis.key_points):
            vars["feature"] = "admin dashboard"
        elif any("login" in point.lower() for point in ticket_analysis.key_points):
            vars["feature"] = "login system"
        else:
            vars["feature"] = "system"
        
        # Generate diagnostic information
        if any("403" in point for point in ticket_analysis.key_points):
            vars["diagnosis"] = "It appears you're encountering a 403 error, which typically indicates a permissions issue. This could be due to recent security updates or account changes."
        else:
            vars["diagnosis"] = "Based on your description, it appears to be an access control issue that might be related to your account permissions."
        
        # Resolution steps
        vars["resolution_steps"] = """Please try the following steps:
1. Clear your browser cache and cookies
2. Try accessing from an incognito/private window
3. Ensure you're using the correct admin credentials

If these steps don't resolve the issue, our technical team will need to investigate your account permissions."""
        
        # Priority level and ETA
        if ticket_analysis.priority.value >= 3:
            vars["priority_level"] = "HIGH"
            vars["eta"] = "Today (within 2-3 hours)"
        else:
            vars["priority_level"] = "MEDIUM"
            vars["eta"] = "Within 24 hours"
        
        return vars
    
    def _generate_billing_response_vars(self, ticket_analysis, context):
        vars = {}
        
        # Determine the billing topic
        if any("cycle" in point.lower() for point in ticket_analysis.key_points):
            vars["billing_topic"] = "billing cycle"
        elif any("invoice" in point.lower() for point in ticket_analysis.key_points):
            vars["billing_topic"] = "invoice"
        elif any("payment" in point.lower() for point in ticket_analysis.key_points):
            vars["billing_topic"] = "payment"
        else:
            vars["billing_topic"] = "billing inquiry"
        
        # Explanation based on billing topic
        if vars["billing_topic"] == "billing cycle":
            vars["explanation"] = """Our system bills from the 15th of each month. When you sign up on a date other than the 15th, we pro-rate your first invoice for the partial period.

For example, if you signed up on the 20th, your first invoice includes a pro-rated amount for the period from the 20th to the 14th of the following month. Subsequent invoices will cover the full period from the 15th to the 14th of the next month."""
        else:
            vars["explanation"] = """Our billing system processes payments on a monthly basis, with the billing cycle starting on the 15th of each month. Your plan charges are calculated based on your subscription level and any additional usage fees that may apply."""
        
        # Next steps
        vars["next_steps"] = """If you would like to:
1. Receive a detailed breakdown of your charges, we can provide that by email
2. Change your billing date to align with your signup date, we can arrange this for you
3. Discuss other billing options, please let us know your preferences"""
        
        return vars
    
    def _generate_feature_response_vars(self, ticket_analysis, context):
        vars = {}
        
        # Extract the requested feature
        feature_points = [point for point in ticket_analysis.key_points if "feature" in point.lower() or "request" in point.lower()]
        if feature_points:
            vars["feature_name"] = feature_points[0].replace("Feature request: ", "").replace("Addition request: ", "")
        else:
            vars["feature_name"] = "the requested functionality"
        
        # Feedback on the request
        vars["feedback"] = f"""Thank you for your suggestion about {vars["feature_name"]}. We appreciate customer feedback as it helps us improve our product.

We regularly review feature requests and prioritize them based on customer demand, alignment with our roadmap, and technical feasibility."""
        
        # Timeline information
        vars["timeline"] = """While I can't provide a specific timeline for implementation at this moment, I've logged your request in our product management system. Our product team will review it during our next planning cycle.

We'll be sure to notify you if this feature is added in a future update."""
        
        return vars
    
    def _generate_technical_response_vars(self, ticket_analysis, context):
        vars = {}
        
        # Determine the issue description
        if any("error" in point.lower() for point in ticket_analysis.key_points):
            vars["issue_description"] = "the error you encountered"
        elif any("crash" in point.lower() for point in ticket_analysis.key_points):
            vars["issue_description"] = "the system crash"
        elif any("slow" in point.lower() for point in ticket_analysis.key_points):
            vars["issue_description"] = "the performance issue"
        else:
            vars["issue_description"] = "the technical issue you reported"
        
        # Troubleshooting steps
        vars["troubleshooting"] = """To help us resolve this issue efficiently, could you please provide the following information if you haven't already:

1. The exact error message you're seeing (or a screenshot)
2. Which browser and operating system you're using
3. The steps you were taking when the issue occurred
4. Whether this is a new issue or has happened before"""
        
        # Solution approach
        vars["solution"] = """Once we have this information, our technical team will investigate the issue. In the meantime, you might try:

1. Clearing your browser cache and cookies
2. Trying a different browser
3. Restarting your device

These simple steps sometimes resolve technical issues without further intervention."""
        
        # Priority level
        if ticket_analysis.priority.value >= 3:
            vars["priority_level"] = "HIGH"
        else:
            vars["priority_level"] = "STANDARD"
        
        return vars
    
    def _fill_template(self, template, variables):
        """Fill in a template with the provided variables."""
        filled_template = template
        
        # For each variable in the template
        for placeholder in re.findall(r'\{([^}]+)\}', template):
            if placeholder in variables:
                filled_template = filled_template.replace(
                    '{' + placeholder + '}', 
                    variables[placeholder]
                )
            else:
                # If we don't have a value, replace with a generic placeholder
                filled_template = filled_template.replace(
                    '{' + placeholder + '}', 
                    f"[{placeholder}]"
                )
        
        return filled_template

# For testing
if __name__ == "__main__":
    import asyncio
    from ticket_analysis_agent import TicketAnalysis, TicketCategory, Priority
    
    RESPONSE_TEMPLATES = {
        "access_issue": """
Hello {name},

I understand you're having trouble accessing the {feature}. Let me help you resolve this.

{diagnosis}

{resolution_steps}

Priority Status: {priority_level}

Estimated Resolution: {eta}

Please let me know if you need any clarification.

Best regards,
Baguette Support
""",
        "billing_inquiry": """
Hi {name},

Thank you for your inquiry about {billing_topic}.

{explanation}

{next_steps}

If you have any questions, don't hesitate to ask.

Best regards,
Baguette Billing Team
"""
    }
    
    async def test():
        agent = ResponseAgent()
        
        # Create a test analysis
        analysis = TicketAnalysis(
            category=TicketCategory.ACCESS,
            priority=Priority.URGENT,
            key_points=["Cannot access admin dashboard", "Getting 403 error"],
            required_expertise=["access control", "admin permissions"],
            sentiment=-0.5,
            urgency_indicators=["ASAP"],
            business_impact="Blocking payroll processing",
            suggested_response_type="access_issue"
        )
        
        # Create context
        context = {
            "customer_name": "John Smith",
            "customer_role": "Finance Director",
            "customer_plan": "Enterprise",
            "company_size": "250+"
        }
        
        # Generate response
        response = await agent.generate_response(analysis, RESPONSE_TEMPLATES, context)
        print(json.dumps(response.to_dict(), indent=2))
    
    asyncio.run(test())