from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


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


class SupportTicket(BaseModel):
    id: str
    subject: str
    content: str
    customer_info: Dict[str, Any] = {}


class TicketAnalysis(BaseModel):
    category: TicketCategory
    priority: Priority
    key_points: List[str]
    required_expertise: List[str]
    sentiment: float = Field(default=0.0, description="Customer sentiment score (-1 to 1)")
    urgency_indicators: List[str] = []
    business_impact: str = ""
    suggested_response_type: str


class ResponseSuggestion(BaseModel):
    response_text: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    requires_approval: bool = False
    suggested_actions: List[str] = []


class TicketResolution(BaseModel):
    ticket_id: str
    analysis: TicketAnalysis
    response: ResponseSuggestion
    status: str = "resolved"
    processing_time: float = 0.0
    error: Optional[str] = None