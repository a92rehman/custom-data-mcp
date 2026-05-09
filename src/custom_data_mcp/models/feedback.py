"""Feedback entry model."""

import uuid
from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field


class FeedbackEntry(BaseModel):
    feedback_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_id: str
    user_name: str = "unknown"
    rating: Literal["up", "down"]
    comment: str | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
