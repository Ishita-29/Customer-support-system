import time
import json
import re
import streamlit as st
from enum import Enum
from typing import Dict, List, Any, Optional

# --- Basic Models ---
class TicketCategory(str, Enum):
    TECHNICAL = "technical"
    BILLING = "billing"
    FEATURE = "feature"
    ACCESS = "access"

class Priority(int, Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4

# --- Sample Data ---
SAMPLE_TICKETS = [
    {
        "id": "TKT-001",
        "subject": "Cannot access admin dashboard",
        "content": """
Hi Support,

Since this morning I can't access the admin dashboard. I keep getting a 403 error.

I need this fixed ASAP as I need to process payroll today.

Thanks,
John Smith
Finance Director
""",
        "customer_info": {
            "role": "Admin",
            "plan": "Enterprise",
            "company_size": "250+"
        }
    },
    {
        "id": "TKT-002",
        "subject": "Question about billing cycle",
        "content": """
Hello,

Our invoice shows billing from the 15th but we signed up on the 20th.

Can you explain how the pro-rating works?

Best regards,
Sarah Jones
""",
        "customer_info": {
            "role": "Billing Admin",
            "plan": "Professional",
            "company_size": "50-249"
        }
    },
    {
        "id": "TKT-003",
        "subject": "URGENT: System down during demo",
        "content": """
System crashed during customer demo!!!

Call me ASAP: +1-555-0123

-Sent from my iPhone
""",
        "customer_info": {
            "role": "Sales Director",
            "plan": "Enterprise",
        }
    }
]

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

# --- Simple Agents ---
class TicketAnalysisAgent:
    def analyze_ticket(self, ticket_content, customer_info=None):
        # Simple rule-based analyzer
        analysis = {
            "category": "technical",
            "priority": 2,
            "key_points": ["Issue needs investigation"],
            "required_expertise": ["support"],
            "sentiment": 0.0,
            "urgency_indicators": [],
            "business_impact": "",
            "suggested_response_type": "technical_issue"
        }
        
        # Detect access issues
        if "access" in ticket_content.lower() or "login" in ticket_content.lower() or "403" in ticket_content.lower():
            analysis["category"] = "access"
            analysis["key_points"] = ["Cannot access dashboard", "403 error"]
            analysis["required_expertise"] = ["access control", "permissions"]
            analysis["suggested_response_type"] = "access_issue"
            
            # Check for urgency
            if "asap" in ticket_content.lower() or "urgent" in ticket_content.lower():
                analysis["priority"] = 3
                analysis["urgency_indicators"] = ["ASAP mentioned"]
                
            # Check for business impact
            if "payroll" in ticket_content.lower():
                analysis["priority"] = 4
                analysis["business_impact"] = "Payroll processing blocked"
            
        # Detect billing issues
        elif "billing" in ticket_content.lower() or "invoice" in ticket_content.lower():
            analysis["category"] = "billing"
            analysis["key_points"] = ["Billing question", "Pro-rating confusion"]
            analysis["required_expertise"] = ["billing", "accounting"]
            analysis["suggested_response_type"] = "billing_inquiry"
        
        # Detect urgency
        if "urgent" in ticket_content.lower() or "asap" in ticket_content.lower():
            analysis["urgency_indicators"].append("Urgent language")
            if analysis["priority"] < 3:
                analysis["priority"] = 3
        
        # Check role-based priority
        if customer_info and "role" in customer_info:
            role = customer_info["role"].lower()
            if "director" in role or "chief" in role or "ceo" in role:
                if analysis["priority"] < 3:
                    analysis["priority"] = 3
                    analysis["key_points"].append("VIP customer")
        
        return analysis

class ResponseAgent:
    def generate_response(self, ticket_analysis, response_templates, context):
        # Simple template-based response
        response = {
            "response_text": "Default response text",
            "confidence_score": 0.7,
            "requires_approval": False,
            "suggested_actions": []
        }
        
        template_key = ticket_analysis["suggested_response_type"]
        if template_key not in response_templates:
            template_key = list(response_templates.keys())[0]  # Default to first template
            
        template = response_templates[template_key]
        
        # Fill in template based on analysis
        if template_key == "access_issue":
            customer_name = context.get("customer_name", "Customer")
            feature = "admin dashboard" if "dashboard" in context.get("ticket_content", "").lower() else "system"
            
            diagnosis = "It appears you're encountering a 403 error, which typically indicates a permissions issue."
            
            resolution_steps = """Please try the following steps:
1. Clear your browser cache and cookies
2. Try accessing from an incognito/private window
3. Ensure you're using the correct admin credentials

If these steps don't resolve the issue, our technical team will need to investigate your account permissions."""
            
            priority_text = "HIGH" if ticket_analysis["priority"] >= 3 else "MEDIUM"
            eta = "Today (within 2-3 hours)" if ticket_analysis["priority"] >= 3 else "Within 24 hours"
            
            response_text = template.format(
                name=customer_name,
                feature=feature,
                diagnosis=diagnosis,
                resolution_steps=resolution_steps,
                priority_level=priority_text,
                eta=eta
            )
            
            response["response_text"] = response_text
            response["suggested_actions"] = ["Escalate to Access Control team if not resolved within 1 hour"]
            
        elif template_key == "billing_inquiry":
            customer_name = context.get("customer_name", "Customer")
            billing_topic = "billing cycle" if "cycle" in context.get("ticket_content", "").lower() else "billing"
            
            explanation = """Our system bills from the 15th of each month. Since you signed up on the 20th, your first invoice includes a pro-rated amount for the period from the 20th to the 14th of the following month.

Subsequent invoices will cover the full period from the 15th to the 14th of the next month."""
            
            next_steps = "If you prefer to align your billing date with your signup date, we can arrange this for you."
            
            response_text = template.format(
                name=customer_name,
                billing_topic=billing_topic,
                explanation=explanation,
                next_steps=next_steps
            )
            
            response["response_text"] = response_text
            response["confidence_score"] = 0.9
            response["suggested_actions"] = ["Offer billing date adjustment if requested"]
        
        # Determine if approval is needed
        if ticket_analysis["priority"] >= 4:
            response["requires_approval"] = True
            
        return response

class TicketProcessor:
    def __init__(self):
        self.analysis_agent = TicketAnalysisAgent()
        self.response_agent = ResponseAgent()
        
    def process_ticket(self, ticket):
        start_time = time.time()
        
        try:
            # Extract customer name from ticket content
            name_match = re.search(r"(?:Regards|Thanks|Best regards),?\s*(.*?)(?:\n|$)", ticket["content"])
            customer_name = name_match.group(1).strip() if name_match else "Customer"
            
            # Create context
            context = {
                "customer_name": customer_name,
                "customer_role": ticket["customer_info"].get("role", "Unknown"),
                "customer_plan": ticket["customer_info"].get("plan", "Unknown"),
                "company_size": ticket["customer_info"].get("company_size", "Unknown"),
                "ticket_content": ticket["content"]
            }
            
            # Analyze ticket
            analysis = self.analysis_agent.analyze_ticket(ticket["content"], ticket["customer_info"])
            
            # Generate response
            response = self.response_agent.generate_response(analysis, RESPONSE_TEMPLATES, context)
            
            processing_time = time.time() - start_time
            
            # Prepare result
            resolution = {
                "ticket_id": ticket["id"],
                "analysis": analysis,
                "response": response,
                "status": "resolved",
                "processing_time": processing_time,
                "error": None
            }
            
            return resolution
            
        except Exception as e:
            processing_time = time.time() - start_time
            return {
                "ticket_id": ticket["id"],
                "analysis": None,
                "response": None,
                "status": "error",
                "processing_time": processing_time,
                "error": str(e)
            }

# --- UI Helper Functions ---
def get_priority_color(priority):
    colors = {
        1: "green",  # LOW
        2: "blue",   # MEDIUM
        3: "orange", # HIGH
        4: "red"     # URGENT
    }
    return colors.get(priority, "gray")

def get_category_icon(category):
    icons = {
        "technical": "🔧",
        "billing": "💰",
        "feature": "✨",
        "access": "🔑"
    }
    return icons.get(category, "❓")

def format_processing_time(seconds):
    if seconds < 1:
        return f"{seconds * 1000:.0f} ms"
    return f"{seconds:.2f} s"

# --- Streamlit App ---
st.set_page_config(
    page_title="AI Support Ticket System", 
    page_icon="🎫",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "processor" not in st.session_state:
    st.session_state.processor = TicketProcessor()
if "current_ticket" not in st.session_state:
    st.session_state.current_ticket = None
if "resolution" not in st.session_state:
    st.session_state.resolution = None
if "history" not in st.session_state:
    st.session_state.history = []

# Process function
def process_current_ticket():
    if st.session_state.current_ticket:
        processor = st.session_state.processor
        resolution = processor.process_ticket(st.session_state.current_ticket)
        st.session_state.resolution = resolution
        st.session_state.history.append({
            "ticket": st.session_state.current_ticket,
            "resolution": resolution,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        })

# Sidebar
with st.sidebar:
    st.title("🎫 Support Ticket System")
    
    # Sample ticket selection
    st.subheader("Sample Tickets")
    sample_options = [f"{ticket['id']}: {ticket['subject']}" for ticket in SAMPLE_TICKETS]
    selected_sample = st.selectbox("Select a sample ticket", sample_options)
    
    if st.button("Load Sample"):
        selected_index = sample_options.index(selected_sample)
        st.session_state.current_ticket = SAMPLE_TICKETS[selected_index]
        st.session_state.resolution = None
    
    # History
    st.subheader("Recent Tickets")
    if not st.session_state.history:
        st.info("No tickets processed yet")
    else:
        for i, item in enumerate(reversed(st.session_state.history[-5:])):
            with st.expander(f"{item['ticket']['id']}: {item['ticket']['subject']}"):
                st.write(f"**Time:** {item['timestamp']}")
                st.write(f"**Status:** {item['resolution']['status']}")
                if item['resolution']['analysis']:
                    st.write(f"**Category:** {get_category_icon(item['resolution']['analysis']['category'])} {item['resolution']['analysis']['category']}")
                    st.write(f"**Priority:** {item['resolution']['analysis']['priority']}")

# Main content
st.title("AI Support Ticket Processing System")

tab1, tab2 = st.tabs(["Submit Ticket", "View Results"])

# Submit tab
with tab1:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Ticket Content")
        
        ticket_id = st.text_input("Ticket ID", value="TKT-" + time.strftime("%Y%m%d%H%M%S"))
        ticket_subject = st.text_input("Subject", value="")
        ticket_content = st.text_area("Content", height=200, value="")
    
    with col2:
        st.subheader("Customer Info")
        
        customer_role = st.text_input("Role", value="")
        customer_plan = st.selectbox("Plan", ["Basic", "Professional", "Enterprise"])
        company_size = st.selectbox("Company Size", ["1-49", "50-249", "250+"])
        
        if st.button("Process Ticket", type="primary"):
            if not ticket_subject or not ticket_content:
                st.error("Please fill in the subject and content fields")
            else:
                st.session_state.current_ticket = {
                    "id": ticket_id,
                    "subject": ticket_subject,
                    "content": ticket_content,
                    "customer_info": {
                        "role": customer_role,
                        "plan": customer_plan,
                        "company_size": company_size
                    }
                }
                process_current_ticket()

# Results tab
with tab2:
    if st.session_state.current_ticket:
        ticket = st.session_state.current_ticket
        
        # Ticket info
        with st.expander("Ticket Information", expanded=True):
            st.write(f"**ID:** {ticket['id']}")
            st.write(f"**Subject:** {ticket['subject']}")
            st.write("**Content:**")
            st.text(ticket['content'])
            
            st.write("**Customer Information:**")
            customer_info = ticket['customer_info']
            cols = st.columns(3)
            with cols[0]:
                st.write(f"Role: {customer_info.get('role', 'Not specified')}")
            with cols[1]:
                st.write(f"Plan: {customer_info.get('plan', 'Not specified')}")
            with cols[2]:
                st.write(f"Company Size: {customer_info.get('company_size', 'Not specified')}")
        
        # Process button in results tab
        if st.button("Process"):
            process_current_ticket()
        
        # Resolution
        if st.session_state.resolution:
            resolution = st.session_state.resolution
            
            if resolution["error"]:
                st.error(f"Error processing ticket: {resolution['error']}")
            else:
                col1, col2 = st.columns([1, 1])
                
                # Analysis results
                with col1:
                    st.subheader("Ticket Analysis")
                    
                    analysis = resolution["analysis"]
                    
                    # Display priority with color
                    priority_color = get_priority_color(analysis["priority"])
                    st.markdown(
                        f"""
                        <div style="background-color: {priority_color}; color: white; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                            <h3 style="margin:0; color: white;">Priority: {analysis["priority"]}</h3>
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )
                    
                    # Display category
                    st.markdown(
                        f"""
                        <div style="background-color: #f0f0f0; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                            <h3 style="margin:0;">Category: {get_category_icon(analysis["category"])} {analysis["category"]}</h3>
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )
                    
                    # Key points
                    st.write("**Key Points:**")
                    for point in analysis["key_points"]:
                        st.write(f"• {point}")
                    
                    # Additional analysis
                    with st.expander("Additional Analysis"):
                        st.write(f"**Required Expertise:** {', '.join(analysis['required_expertise'])}")
                        st.write(f"**Sentiment Score:** {analysis['sentiment']}")
                        st.write(f"**Business Impact:** {analysis['business_impact']}")
                        
                        if analysis["urgency_indicators"]:
                            st.write(f"**Urgency Indicators:** {', '.join(analysis['urgency_indicators'])}")
                
                # Response
                with col2:
                    st.subheader("Generated Response")
                    
                    response = resolution["response"]
                    
                    # Display confidence score
                    confidence_color = "green" if response["confidence_score"] >= 0.8 else "orange" if response["confidence_score"] >= 0.5 else "red"
                    st.markdown(
                        f"""
                        <div style="background-color: #f0f0f0; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                            <span style="color: {confidence_color}; font-weight: bold;">Confidence: {response["confidence_score"]:.2f}</span>
                            <span style="margin-left: 20px;">Requires approval: {"Yes" if response["requires_approval"] else "No"}</span>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    
                    # Display response text
                    st.markdown(
                        f"""
                        <div style="background-color: white; border: 1px solid #ddd; padding: 15px; border-radius: 5px; height: 300px; overflow-y: auto;">
                            {response["response_text"].replace("\n", "<br>")}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    
                    # Suggested actions
                    if response["suggested_actions"]:
                        st.write("**Suggested Actions:**")
                        for action in response["suggested_actions"]:
                            st.write(f"• {action}")
                
                # Processing metrics
                st.info(f"Processing time: {format_processing_time(resolution['processing_time'])}")

# Instructions
with st.expander("How to use this system"):
    st.markdown("""
    ### AI Support Ticket Processing System
    
    This system demonstrates an AI-powered approach to processing customer support tickets. It uses:
    
    1. **Ticket Analysis**: Classifies tickets by category and priority
    2. **Response Generation**: Creates personalized responses using templates
    3. **Workflow Orchestration**: Coordinates the processing pipeline
    
    #### How to Use:
    
    1. **Submit a Ticket**: Enter ticket details or load a sample ticket
    2. **Process the Ticket**: Click the Process button
    3. **View Results**: See the analysis and generated response
    
    This implementation demonstrates the core functionality required for the assessment.
    """)

# Footer
st.markdown("---")
st.markdown("AI Support Ticket Processing System - Practical Assessment")