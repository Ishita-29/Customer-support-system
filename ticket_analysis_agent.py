from enum import Enum
import re
import json
from typing import Dict, List, Any, Optional

class TicketCategory(Enum):
    TECHNICAL = "technical"
    BILLING = "billing"
    FEATURE = "feature"
    ACCESS = "access"

class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4

class TicketAnalysis:
    def __init__(self, category, priority, key_points, required_expertise, 
                 sentiment=0.0, urgency_indicators=None, business_impact="", 
                 suggested_response_type=""):
        self.category = category
        self.priority = priority
        self.key_points = key_points or []
        self.required_expertise = required_expertise or []
        self.sentiment = sentiment
        self.urgency_indicators = urgency_indicators or []
        self.business_impact = business_impact
        self.suggested_response_type = suggested_response_type
    
    def to_dict(self):
        return {
            "category": self.category.value,
            "priority": self.priority.value,
            "key_points": self.key_points,
            "required_expertise": self.required_expertise,
            "sentiment": self.sentiment,
            "urgency_indicators": self.urgency_indicators,
            "business_impact": self.business_impact,
            "suggested_response_type": self.suggested_response_type
        }

class TicketAnalysisAgent:
    def __init__(self, llm=None):
        self.llm = llm
        self.urgency_keywords = [
            "urgent", "asap", "immediately", "emergency", "critical",
            "as soon as possible", "right away", "time sensitive"
        ]
        self.vip_roles = [
            "ceo", "cfo", "cto", "director", "vp", "vice president", 
            "president", "head", "chief", "manager"
        ]
    
    async def analyze_ticket(self, ticket_content: str, customer_info: Optional[Dict[str, Any]] = None) -> TicketAnalysis:
        """
        Analyze ticket content and customer info to categorize and prioritize the ticket.
        
        Args:
            ticket_content: The content of the support ticket
            customer_info: Optional dictionary with customer metadata
            
        Returns:
            TicketAnalysis object with classification and priority
        """
        # Default values
        category = TicketCategory.TECHNICAL
        priority = Priority.MEDIUM
        key_points = []
        required_expertise = ["general support"]
        sentiment = 0.0
        urgency_indicators = []
        business_impact = ""
        
        # Extract subject if present
        subject_match = re.search(r"Subject: (.*?)(?:\n|$)", ticket_content)
        subject = subject_match.group(1) if subject_match else ""
        
        # Apply content-based rules for categorization
        content = ticket_content.lower()
        
        # Categorization logic
        if any(word in content for word in ["access", "login", "permission", "403", "dashboard"]):
            category = TicketCategory.ACCESS
            required_expertise = ["access control", "permissions", "authentication"]
            suggested_response_type = "access_issue"
            
        elif any(word in content for word in ["bill", "invoice", "payment", "charge", "pricing", "cost", "subscription"]):
            category = TicketCategory.BILLING
            required_expertise = ["billing", "accounting", "finance"]
            suggested_response_type = "billing_inquiry"
            
        elif any(word in content for word in ["feature", "enhancement", "improvement", "add", "suggestion", "roadmap"]):
            category = TicketCategory.FEATURE
            required_expertise = ["product management", "development"]
            suggested_response_type = "feature_request"
            
        else:
            category = TicketCategory.TECHNICAL
            required_expertise = ["technical support", "troubleshooting"]
            suggested_response_type = "technical_issue"
        
        # Extract key points
        if category == TicketCategory.ACCESS:
            key_points = self._extract_access_key_points(content)
        elif category == TicketCategory.BILLING:
            key_points = self._extract_billing_key_points(content)
        elif category == TicketCategory.FEATURE:
            key_points = self._extract_feature_key_points(content)
        else:
            key_points = self._extract_technical_key_points(content)
        
        # Prioritization logic
        # Check for urgency indicators
        urgency_indicators = self._extract_urgency_indicators(content)
        if urgency_indicators:
            if priority.value < Priority.HIGH.value:
                priority = Priority.HIGH
        
        # Check for business impact
        business_impact = self._assess_business_impact(content)
        if "payroll" in content or "revenue" in content or "cannot work" in content:
            priority = Priority.URGENT
            business_impact = "Critical business function impacted"
        
        # VIP customer check
        if customer_info and "role" in customer_info:
            customer_role = customer_info["role"].lower()
            if any(role in customer_role for role in self.vip_roles):
                if priority.value < Priority.HIGH.value:
                    priority = Priority.HIGH
        
        # Enterprise plan check
        if customer_info and "plan" in customer_info and customer_info["plan"] == "Enterprise":
            if priority.value < Priority.MEDIUM.value:
                priority = Priority.MEDIUM
        
        # Sentiment analysis (simplified)
        sentiment = self._analyze_sentiment(content)
        
        # Create and return the analysis
        return TicketAnalysis(
            category=category,
            priority=priority,
            key_points=key_points,
            required_expertise=required_expertise,
            sentiment=sentiment,
            urgency_indicators=urgency_indicators,
            business_impact=business_impact,
            suggested_response_type=suggested_response_type
        )
    
    def _extract_access_key_points(self, content):
        points = []
        if "dashboard" in content:
            points.append("Cannot access dashboard")
        if "403" in content:
            points.append("Receiving 403 error")
        if "password" in content:
            points.append("Password issue")
        if "login" in content:
            points.append("Login problem")
        if "permission" in content:
            points.append("Permission problem")
        if len(points) == 0:
            points.append("General access issue")
        return points
    
    def _extract_billing_key_points(self, content):
        points = []
        if "invoice" in content:
            points.append("Invoice question")
        if "payment" in content:
            points.append("Payment issue")
        if "charge" in content:
            points.append("Charge inquiry")
        if "refund" in content:
            points.append("Refund request")
        if "cycle" in content or "pro-rat" in content:
            points.append("Billing cycle question")
        if len(points) == 0:
            points.append("General billing question")
        return points
    
    def _extract_feature_key_points(self, content):
        points = []
        if "request" in content:
            points.append("Feature request")
        if "suggest" in content:
            points.append("Feature suggestion")
        if "add" in content:
            points.append("Addition request")
        if "improve" in content:
            points.append("Improvement suggestion")
        if "roadmap" in content:
            points.append("Roadmap inquiry")
        if len(points) == 0:
            points.append("General feature request")
        return points
    
    def _extract_technical_key_points(self, content):
        points = []
        if "error" in content:
            points.append("Error reported")
        if "crash" in content:
            points.append("System crash")
        if "bug" in content:
            points.append("Bug report")
        if "slow" in content:
            points.append("Performance issue")
        if "not working" in content:
            points.append("Functionality issue")
        if len(points) == 0:
            points.append("Technical issue")
        return points
    
    def _extract_urgency_indicators(self, content):
        indicators = []
        for keyword in self.urgency_keywords:
            if keyword in content:
                indicators.append(keyword)
        
        # Check for exclamation points
        exclamations = content.count("!")
        if exclamations >= 3:
            indicators.append("multiple exclamation marks")
        
        # Check for terms like "today" or "now"
        if "today" in content or "now" in content or "immediately" in content:
            indicators.append("immediate timeframe")
        
        return indicators
    
    def _assess_business_impact(self, content):
        if "revenue" in content or "sales" in content:
            return "Revenue impact"
        if "customer" in content and ("cannot" in content or "unable" in content):
            return "Customer impact"
        if "production" in content:
            return "Production impact"
        if "deadline" in content:
            return "Deadline impact"
        if "payroll" in content:
            return "Payroll processing impact"
        return ""
    
    def _analyze_sentiment(self, content):
        # Very simplified sentiment analysis
        negative_words = ["cannot", "issue", "problem", "error", "fail", "bug", "broken", "urgent", "bad", "wrong"]
        positive_words = ["thank", "please", "appreciate", "good", "great", "working"]
        
        negative_count = sum(1 for word in negative_words if word in content)
        positive_count = sum(1 for word in positive_words if word in content)
        
        # Calculate sentiment on a scale from -1 to 1
        total = negative_count + positive_count
        if total == 0:
            return 0.0
        
        return (positive_count - negative_count) / total

# For testing
if __name__ == "__main__":
    import asyncio
    
    async def test():
        agent = TicketAnalysisAgent()
        
        test_ticket = """
        Subject: Cannot access admin dashboard
        
        Hi Support,
        
        Since this morning I can't access the admin dashboard. I keep getting a 403 error.
        
        I need this fixed ASAP as I need to process payroll today.
        
        Thanks,
        John Smith
        Finance Director
        """
        
        customer_info = {
            "role": "Finance Director",
            "plan": "Enterprise",
            "company_size": "250+"
        }
        
        analysis = await agent.analyze_ticket(test_ticket, customer_info)
        print(json.dumps(analysis.to_dict(), indent=2))
    
    asyncio.run(test())