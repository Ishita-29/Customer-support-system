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