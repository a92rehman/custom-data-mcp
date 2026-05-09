"""Tests for FeedbackEntry model."""

import pytest
from pydantic import ValidationError

from custom_data_mcp.models.feedback import FeedbackEntry


def test_feedback_entry_defaults():
    entry = FeedbackEntry(event_id="abc-123", rating="up")
    assert entry.feedback_id is not None
    assert entry.timestamp is not None
    assert entry.event_id == "abc-123"
    assert entry.rating == "up"
    assert entry.comment is None
    assert entry.user_name == "unknown"


def test_feedback_entry_with_comment():
    entry = FeedbackEntry(
        event_id="abc-123",
        rating="down",
        comment="Wrong number, expected 150",
        user_name="Abdur-Rehman",
    )
    assert entry.rating == "down"
    assert entry.comment == "Wrong number, expected 150"
    assert entry.user_name == "Abdur-Rehman"


def test_feedback_entry_invalid_rating():
    with pytest.raises(ValidationError):
        FeedbackEntry(event_id="abc-123", rating="maybe")


def test_feedback_entry_serialization():
    entry = FeedbackEntry(event_id="abc-123", rating="up")
    data = entry.model_dump()
    assert "feedback_id" in data
    assert "timestamp" in data
    assert data["rating"] == "up"

    json_str = entry.model_dump_json()
    assert "abc-123" in json_str
