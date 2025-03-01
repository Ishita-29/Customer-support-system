import streamlit as st
import asyncio
import time
import json
import re
from typing import Dict, List, Any

# Import our agent classes
from agents.ticket_analysis_agent import TicketAnalysisAgent, TicketAnalysis, TicketCategory, Priority
from agents.response_agent import ResponseAgent, ResponseSuggestion
from agents.ticket_processor import TicketProcessor, SupportTicket, TicketResolution

# Sample tickets for testing
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
    },
    {
        "id": "TKT-004",
        "subject": "It's not working",
        "content": "Nothing works. Please help.",
        "customer_info": {
            "role": "User",
            "plan": "Basic",
        }
    },
    {
        "id": "TKT-005",
        "subject": "Feature request: Export to CSV",
        "content": """
Hello Support,

We'd like to request a feature to export our analytics data to CSV format.
Currently, we're manually copying data which is time-consuming.

Is this on your roadmap? If not, could it be considered for a future release?

Regards,
Lisa Chen
Product Manager
""",
        "customer_info": {
            "role": "Manager",
            "plan": "Professional",
            "company_size": "50-249"
        }
    }
]

# Response templates
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
""",
    "feature_request": """
Hello {name},

Thank you for suggesting the addition of {feature_name}.

{feedback}

{timeline}

We appreciate your input in making our product better.

Best regards,
Baguette Product Team
""",
    "technical_issue": """
Hello {name},

I'm sorry you're experiencing an issue with {issue_description}.

{troubleshooting}

{solution}

Priority Status: {priority_level}

If you need further assistance, please don't hesitate to reach out.

Best regards,
Baguette Technical Support
""",
    "ambiguous_request": """
Hello {name},

Thank you for contacting Baguette Support.

To better assist you with your request, I would appreciate if you could provide some additional details:

{questions}

Once I have this information, I'll be able to help you more effectively.

Best regards,
Baguette Support
"""
}

# Helper functions
def get_priority_color(priority_value):
    colors = {
        1: "green",  # LOW
        2: "blue",   # MEDIUM
        3: "orange", # HIGH
        4: "red"     # URGENT
    }
    return colors.get(priority_value, "gray")

def get_category_icon(category_value):
    icons = {
        "technical": "🔧",
        "billing": "💰",
        "feature": "✨",
        "access": "🔑"
    }
    return icons.get(category_value, "❓")

def format_processing_time(seconds):
    if seconds < 1:
        return f"{seconds * 1000:.0f} ms"
    return f"{seconds:.2f} s"

async def process_ticket(ticket):
    processor = st.session_state.processor
    return await processor.process_ticket(ticket)

# Initialize the Streamlit app
st.set_page_config(
    page_title="AI Support Ticket System", 
    page_icon="🎫", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "processor" not in st.session_state:
    st.session_state.processor = TicketProcessor(RESPONSE_TEMPLATES)
if "current_ticket" not in st.session_state:
    st.session_state.current_ticket = None
if "resolution" not in st.session_state:
    st.session_state.resolution = None
if "history" not in st.session_state:
    st.session_state.history = []
if "processing" not in st.session_state:
    st.session_state.processing = False

# Sidebar
with st.sidebar:
    st.title("🎫 Support Ticket System")
    
    # Sample ticket selection
    st.subheader("Sample Tickets")
    sample_options = [f"{ticket['id']}: {ticket['subject']}" for ticket in SAMPLE_TICKETS]
    selected_sample = st.selectbox("Select a sample ticket", sample_options)
    
    if st.button("Load Sample"):
        selected_index = sample_options.index(selected_sample)
        sample = SAMPLE_TICKETS[selected_index]
        
        # Create ticket object
        st.session_state.current_ticket = SupportTicket(
            id=sample["id"],
            subject=sample["subject"],
            content=sample["content"],
            customer_info=sample["customer_info"]
        )
        st.session_state.resolution = None
    
    # Ticket history
    st.subheader("Recent Tickets")
    if not st.session_state.history:
        st.info("No tickets processed yet")
    else:
        for i, item in enumerate(reversed(st.session_state.history[-5:])):
            ticket = item["ticket"]
            resolution = item["resolution"]
            with st.expander(f"{ticket.id}: {ticket.subject}"):
                st.write(f"**Time:** {item['timestamp']}")
                st.write(f"**Status:** {resolution.status}")
                if resolution.analysis:
                    st.write(f"**Category:** {get_category_icon(resolution.analysis.category.value)} {resolution.analysis.category.value}")
                    st.write(f"**Priority:** {resolution.analysis.priority.value}")

# Main content
st.title("AI Support Ticket Processing System")

# Create tabs
tab1, tab2 = st.tabs(["Submit Ticket", "View Results"])

# Submit tab
with tab1:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Ticket Content")
        
        # Input fields for ticket
        ticket_id = st.text_input("Ticket ID", value="TKT-" + time.strftime("%Y%m%d%H%M%S"))
        ticket_subject = st.text_input("Subject", value="")
        ticket_content = st.text_area("Content", height=200, value="")
    
    with col2:
        st.subheader("Customer Info")
        
        # Customer information
        customer_role = st.text_input("Role", value="")
        customer_plan = st.selectbox("Plan", ["Basic", "Professional", "Enterprise"])
        company_size = st.selectbox("Company Size", ["1-49", "50-249", "250+"])
        
        # Submit button
        if st.button("Process Ticket", type="primary", disabled=st.session_state.processing):
            if not ticket_subject or not ticket_content:
                st.error("Please fill in the subject and content fields")
            else:
                # Create ticket object
                ticket = SupportTicket(
                    id=ticket_id,
                    subject=ticket_subject,
                    content=ticket_content,
                    customer_info={
                        "role": customer_role,
                        "plan": customer_plan,
                        "company_size": company_size
                    }
                )
                
                # Set current ticket
                st.session_state.current_ticket = ticket
                st.session_state.processing = True
                
                # Process the ticket (will be shown in results tab)
                st.info("Processing ticket... Please switch to the Results tab.")

# Results tab
with tab2:
    # Check if we need to process a ticket
    if st.session_state.processing and st.session_state.current_ticket:
        with st.spinner("Processing ticket..."):
            # Process the ticket
            ticket = st.session_state.current_ticket
            resolution = asyncio.run(process_ticket(ticket))
            
            # Update state
            st.session_state.resolution = resolution
            st.session_state.processing = False
            
            # Add to history
            st.session_state.history.append({
                "ticket": ticket,
                "resolution": resolution,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            })
            
            # Force rerun to show results
            st.rerun()
    
    # Display current ticket
    if st.session_state.current_ticket:
        ticket = st.session_state.current_ticket
        
        # Ticket information
        with st.expander("Ticket Information", expanded=True):
            st.write(f"**ID:** {ticket.id}")
            st.write(f"**Subject:** {ticket.subject}")
            st.write(f"**Content:**")
            st.text(ticket.content)
            
            # Customer info
            st.write("**Customer Information:**")
            customer_info = ticket.customer_info
            cols = st.columns(3)
            with cols[0]:
                st.write(f"Role: {customer_info.get('role', 'Not specified')}")
            with cols[1]:
                st.write(f"Plan: {customer_info.get('plan', 'Not specified')}")
            with cols[2]:
                st.write(f"Company Size: {customer_info.get('company_size', 'Not specified')}")
    
    # Display resolution
    if st.session_state.resolution:
        resolution = st.session_state.resolution
        
        # Check if error occurred
        if resolution.error:
            st.error(f"Error processing ticket: {resolution.error}")
        else:
            # Layout for results
            col1, col2 = st.columns([1, 1])
            
            # Analysis results
            with col1:
                st.subheader("Ticket Analysis")
                
                analysis = resolution.analysis
                
                # Display priority with color
                priority_color = get_priority_color(analysis.priority.value)
                priority_name = analysis.priority.name if hasattr(analysis.priority, 'name') else f"Level {analysis.priority.value}"
                
                st.markdown(
                    f"""
                    <div style="background-color: {priority_color}; color: white; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                        <h3 style="margin:0; color: white;">Priority: {priority_name}</h3>
                    </div>
                    """, 
                    unsafe_allow_html=True
                )
                
                # Display category
                category_value = analysis.category.value
                st.markdown(
                    f"""
                    <div style="background-color: #f0f0f0; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                        <h3 style="margin:0;">Category: {get_category_icon(category_value)} {category_value}</h3>
                    </div>
                    """, 
                    unsafe_allow_html=True
                )
                
                # Key points
                st.write("**Key Points:**")
                for point in analysis.key_points:
                    st.write(f"• {point}")
                
                # Additional analysis
                with st.expander("Additional Analysis"):
                    st.write(f"**Required Expertise:** {', '.join(analysis.required_expertise)}")
                    st.write(f"**Sentiment Score:** {analysis.sentiment:.2f}")
                    st.write(f"**Business Impact:** {analysis.business_impact}")
                    
                    if analysis.urgency_indicators:
                        st.write(f"**Urgency Indicators:** {', '.join(analysis.urgency_indicators)}")
            
            # Response
            with col2:
                st.subheader("Generated Response")
                
                response = resolution.response
                
                # Display confidence score
                confidence_color = "green" if response.confidence_score >= 0.8 else "orange" if response.confidence_score >= 0.5 else "red"
                st.markdown(
                    f"""
                    <div style="background-color: #f0f0f0; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                        <span style="color: {confidence_color}; font-weight: bold;">Confidence: {response.confidence_score:.2f}</span>
                        <span style="margin-left: 20px;">Requires approval: {"Yes" if response.requires_approval else "No"}</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
                # Display response text
                st.markdown(
                    f"""
                    <div style="background-color: white; border: 1px solid #ddd; padding: 15px; border-radius: 5px; height: 300px; overflow-y: auto;">
                        {response.response_text.replace("\n", "<br>")}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
                # Suggested actions
                if response.suggested_actions:
                    st.write("**Suggested Actions:**")
                    for action in response.suggested_actions:
                        st.write(f"• {action}")
            
            # Processing metrics
            st.info(f"Processing time: {format_processing_time(resolution.processing_time)}")

# Instructions at the bottom
with st.expander("How to use this system"):
    st.markdown("""
    ### AI Support Ticket Processing System
    
    This system demonstrates an AI-powered approach to processing customer support tickets. It uses a series of specialized agents to:
    
    1. **Analyze** incoming support tickets
    2. **Generate** appropriate responses
    3. **Orchestrate** the workflow between different components
    
    #### How to Use:
    
    1. **Submit a Ticket**: Enter ticket details or load a sample ticket
    2. **View Results**: See the analysis and generated response
    3. **Track History**: Recent tickets are saved in the sidebar
    
    #### Technical Implementation:
    
    - Built with agent-based architecture for modularity
    - Uses rule-based analysis for ticket classification
    - Implements template-based response generation
    - Features comprehensive error handling
    """)

# Footer information
st.markdown("---")
st.markdown("AI Support Ticket Processing System - Practical Assessment")

if __name__ == "__main__":
    # This allows running the app with "streamlit run app.py"
    pass