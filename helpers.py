import re
import time
from typing import Dict, List, Any, Optional


def extract_customer_name(text: str) -> str:
    """
    Extract customer name from ticket content.
    
    Args:
        text: The ticket content
        
    Returns:
        Extracted customer name or "Customer" if not found
    """
    # Try different patterns to extract name
    patterns = [
        r"(?:Regards|Thanks|Best regards|Sincerely|Cheers),?\s*(.*?)(?:\n|$)",  # Closing signature
        r"From:\s*(.*?)(?:\n|$)",  # From field
        r"^(?:Hi|Hello|Dear).*?(?:,|\.)\s*(.*?)(?:\n|$)",  # Opening address
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            name = match.group(1).strip()
            # Remove titles and clean up
            name = re.sub(r"^(Mr\.|Mrs\.|Ms\.|Dr\.|Prof\.)\s+", "", name)
            return name
    
    return "Customer"


def extract_subject_from_content(text: str) -> str:
    """
    Extract subject line from ticket content if present.
    
    Args:
        text: The ticket content
        
    Returns:
        Extracted subject or empty string
    """
    subject_match = re.search(r"Subject:\s*(.*?)(?:\n|$)", text)
    if subject_match:
        return subject_match.group(1).strip()
    
    # Try to extract first line as subject
    lines = text.strip().split('\n')
    if lines and len(lines[0]) < 100:  # Reasonable subject length
        return lines[0]
    
    return ""


def identify_urgency_indicators(text: str) -> List[str]:
    """
    Identify words and phrases that indicate urgency in the text.
    
    Args:
        text: The text to analyze
        
    Returns:
        List of urgency indicators found
    """
    indicators = []
    urgency_words = [
        "urgent", "asap", "emergency", "immediately", "critical",
        "as soon as possible", "quickly", "right away", "urgent",
        "highest priority", "deadline", "sos", "time sensitive"
    ]
    
    lower_text = text.lower()
    
    # Check for each urgency word/phrase
    for word in urgency_words:
        if word in lower_text:
            indicators.append(word)
    
    # Check for time expressions with tight deadlines
    time_patterns = [
        r"by (?:today|tomorrow|this afternoon)",
        r"within \d+ (?:hour|minute|day)",
        r"need.*by.*\d{1,2}(?::\d{2})?\s*(?:am|pm|AM|PM)"
    ]
    
    for pattern in time_patterns:
        matches = re.findall(pattern, lower_text)
        indicators.extend(matches)
    
    # Check for exclamation marks (multiple indicates urgency)
    if "!!!" in text or "!!" in text:
        indicators.append("multiple exclamation marks")
    
    return indicators


def estimate_business_impact(text: str, customer_role: Optional[str] = None) -> str:
    """
    Estimate the business impact described in the ticket.
    
    Args:
        text: The ticket content
        customer_role: Optional customer role for context
        
    Returns:
        Description of business impact or empty string
    """
    impact = ""
    
    # High-impact keywords
    high_impact_patterns = [
        r"(?:affecting|impacting).*(?:revenue|sales|customers|clients|users)",
        r"(?:down|unavailable|not working).*(?:production|live|customer-facing)",
        r"(?:unable to|can't|cannot).*(?:process|complete|finish).*(?:payroll|payment|transaction|order)",
        r"(?:blocking|preventing).*(?:work|progress|delivery|deployment)",
        r"(?:lost|losing).*(?:money|revenue|sales|customers)"
    ]
    
    # Medium-impact keywords
    medium_impact_patterns = [
        r"(?:delaying|slowing).*(?:work|progress|process)",
        r"(?:workaround|alternative).*(?:available|possible|exists)",
        r"(?:internal|team).*(?:affected|impacted)",
        r"(?:inconvenient|difficult|challenging)"
    ]
    
    # Check for high-impact matches
    for pattern in high_impact_patterns:
        match = re.search(pattern, text.lower())
        if match:
            impact = f"High impact: {match.group(0)}"
            break
    
    # If no high impact, check medium impact
    if not impact:
        for pattern in medium_impact_patterns:
            match = re.search(pattern, text.lower())
            if match:
                impact = f"Medium impact: {match.group(0)}"
                break
    
    # Consider customer role in impact assessment
    if customer_role and not impact:
        high_impact_roles = ["ceo", "cfo", "cto", "director", "vp", "vice president", "head of", "chief"]
        if any(role.lower() in customer_role.lower() for role in high_impact_roles):
            impact = f"Potential high impact based on customer role: {customer_role}"
    
    return impact


def format_response(template: str, variables: Dict[str, str]) -> str:
    """
    Format a response template with variables.
    
    Args:
        template: Response template with placeholders
        variables: Dictionary of variables to fill in
        
    Returns:
        Formatted response with placeholders filled in
    """
    # Get all placeholders from the template
    placeholders = re.findall(r"\{([^}]+)\}", template)
    
    # Create a formatted template with default values for missing variables
    formatted_template = template
    for placeholder in placeholders:
        if placeholder not in variables:
            variables[placeholder] = f"[{placeholder}]"
    
    # Fill in the template
    return template.format(**variables)