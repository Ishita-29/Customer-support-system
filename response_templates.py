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