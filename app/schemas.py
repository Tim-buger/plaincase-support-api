from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field


class TicketCategory(StrEnum):
    billing = "billing"
    technical = "technical"
    account = "account"
    feature_request = "feature_request"
    other = "other"


class TicketPriority(StrEnum):
    low = "low"
    medium = "medium"
    high = "high"
    urgent = "urgent"


class TicketSentiment(StrEnum):
    positive = "positive"
    neutral = "neutral"
    frustrated = "frustrated"


class SupportTicket(BaseModel):
    category: TicketCategory = Field(description="Primary issue category")
    priority: TicketPriority = Field(description="Operational response priority")
    summary: str = Field(min_length=3, max_length=240)
    next_action: str = Field(min_length=3, max_length=240)
    sentiment: TicketSentiment
    requires_human: bool
    tags: list[str] = Field(default_factory=list, max_length=5)


class ExtractionRequest(BaseModel):
    text: str = Field(min_length=10, max_length=5000)
    provider: Literal["mock", "openai"] | None = None


class RunMetadata(BaseModel):
    request_id: str
    provider: str
    model: str
    attempts: int
    latency_ms: int
    cached: bool
    validated: bool = True
    created_at: datetime


class ExtractionResponse(BaseModel):
    data: SupportTicket
    meta: RunMetadata


class AuditRecord(BaseModel):
    request_id: str
    provider: str
    status: str
    latency_ms: int
    attempts: int
    created_at: datetime

