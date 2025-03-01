import time
import re
import traceback
import json
from typing import Dict, Any, Optional
import asyncio

from agents.ticket_analysis_agent import TicketAnalysisAgent
from agents.response_agent import ResponseAgent

class SupportTicket:
    def __init__(self, id: str, subject: str, content: str, customer_info: Dict[str, Any] = None):
        self.id = id
        self.subject = subject
        self.content = content
        self.customer_info = customer_info or {}
    
    def to_dict(self):
        return {
            "id": self.id,
            "subject": self.subject,
            "content": self.content,
            "customer_info": self.customer_info
        }

class TicketResolution:
    def __init__(self, ticket_id, analysis=None, response=None, status="pending", 
                 processing_time=0.0, error=None):
        self.ticket_id = ticket_id
        self.analysis = analysis
        self.response = response
        self.status = status
        self.processing_time = processing_time
        self.error = error
    
    def to_dict(self):
        return {
            "ticket_id": self.ticket_id,
            "analysis": self.analysis.to_dict() if self.analysis else None,
            "response": self.response.to_dict() if self.response else None,
            "status": self.status,
            "processing_time": self.processing_time,
            "error": self.error
        }

class TicketProcessor:
    def __init__(self, response_templates, llm=None):
        """
        Initialize the ticket processor with analysis and response agents.
        
        Args:
            response_templates: Dictionary of response templates
            llm: Optional language model to use (default: None)
        """
        self.analysis_agent = TicketAnalysisAgent(llm=llm)
        self.response_agent = ResponseAgent(llm=llm)
        self.response_templates = response_templates
    
    async def process_ticket(self, ticket: SupportTicket) -> TicketResolution:
        """
        Process a support ticket through the full workflow.
        
        Args:
            ticket: SupportTicket object to process
            
        Returns:
            TicketResolution with analysis and response
        """
        start_time = time.time()
        resolution = TicketResolution(ticket_id=ticket.id)
        
        try:
            # Step 1: Extract customer name and build context
            context = self._build_context(ticket)
            
            # Step 2: Analyze the ticket
            analysis = await self.analyze_ticket(ticket, context)
            resolution.analysis = analysis
            
            # Step A: Check for errors from analysis
            if analysis is None:
                resolution.status = "error"
                resolution.error = "Analysis failed"
                return resolution
            
            # Step 3: Generate a response
            response = await self.generate_response(analysis, context)
            resolution.response = response
            
            # Step B: Check for errors from response generation
            if response is None:
                resolution.status = "error"
                resolution.error = "Response generation failed"
                return resolution
            
            # Step 4: Set status and finish
            resolution.status = "resolved"
            
        except Exception as e:
            # Catch any exceptions and record the error
            resolution.status = "error"
            resolution.error = f"Error: {str(e)}\n{traceback.format_exc()}"
        
        finally:
            # Always record processing time
            resolution.processing_time = time.time() - start_time
        
        return resolution
    
    def _build_context(self, ticket: SupportTicket) -> Dict[str, Any]:
        """
        Build context dictionary from ticket information.
        
        Args:
            ticket: SupportTicket object
            
        Returns:
            Context dictionary with extracted information
        """
        # Extract customer name from the ticket content
        name_match = re.search(r"(?:Regards|Thanks|Best regards|Sincerely),?\s*(.*?)(?:\n|$)", ticket.content)
        customer_name = name_match.group(1).strip() if name_match else "Customer"
        
        # Build context dictionary
        context = {
            "ticket_id": ticket.id,
            "ticket_subject": ticket.subject,
            "customer_name": customer_name,
            "customer_role": ticket.customer_info.get("role", "Unknown"),
            "customer_plan": ticket.customer_info.get("plan", "Unknown"),
            "company_size": ticket.customer_info.get("company_size", "Unknown")
        }
        
        return context
    
    async def analyze_ticket(self, ticket: SupportTicket, context: Dict[str, Any]):
        """
        Analyze a support ticket.
        
        Args:
            ticket: SupportTicket to analyze
            context: Context dictionary
            
        Returns:
            TicketAnalysis object or None if analysis fails
        """
        try:
            # Add debugging
            print(f"Analyzing ticket: {ticket.id}")
            
            # Run analysis
            analysis = await self.analysis_agent.analyze_ticket(
                ticket_content=ticket.content,
                customer_info=ticket.customer_info
            )
            
            # Log the result
            print(f"Analysis complete for {ticket.id}: {analysis.category.value}, Priority: {analysis.priority.value}")
            
            return analysis
            
        except Exception as e:
            print(f"Error in ticket analysis: {str(e)}")
            traceback.print_exc()
            return None
    
    async def generate_response(self, analysis, context: Dict[str, Any]):
        """
        Generate a response based on ticket analysis.
        
        Args:
            analysis: TicketAnalysis object
            context: Context dictionary
            
        Returns:
            ResponseSuggestion object or None if generation fails
        """
        try:
            # Add debugging
            print(f"Generating response for category: {analysis.category.value}")
            
            # Generate response
            response = await self.response_agent.generate_response(
                ticket_analysis=analysis,
                response_templates=self.response_templates,
                context=context
            )
            
            # Log the result
            print(f"Response generation complete, confidence: {response.confidence_score:.2f}")
            
            return response
            
        except Exception as e:
            print(f"Error in response generation: {str(e)}")
            traceback.print_exc()
            return None

# For testing
if __name__ == "__main__":
    import sys
    import os
    
    # Response templates for testing
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
        # Create a processor
        processor = TicketProcessor(RESPONSE_TEMPLATES)
        
        # Create a test ticket
        ticket = SupportTicket(
            id="TKT-001",
            subject="Cannot access admin dashboard",
            content="""
Hi Support,

Since this morning I can't access the admin dashboard. I keep getting a 403 error.

I need this fixed ASAP as I need to process payroll today.

Thanks,
John Smith
Finance Director
""",
            customer_info={
                "role": "Finance Director",
                "plan": "Enterprise",
                "company_size": "250+"
            }
        )
        
        # Process the ticket
        resolution = await processor.process_ticket(ticket)
        
        # Print results
        print(f"\nTicket: {ticket.id}")
        print(f"Status: {resolution.status}")
        print(f"Processing time: {resolution.processing_time:.2f} seconds")
        
        if resolution.error:
            print(f"Error: {resolution.error}")
        else:
            print(f"\nCategory: {resolution.analysis.category.value}")
            print(f"Priority: {resolution.analysis.priority.value}")
            print(f"\nResponse:\n{resolution.response.response_text}")
            print(f"\nSuggested actions:")
            for action in resolution.response.suggested_actions:
                print(f"- {action}")
    
    # Run the test
    asyncio.run(test())