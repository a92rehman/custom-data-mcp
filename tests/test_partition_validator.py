"""Tests for partition filter validation."""

from taleemabad_data_mcp.engine.partition_validator import PartitionValidator


def test_accepts_query_with_partition_filter():
    validator = PartitionValidator()
    result = validator.validate(
        partition_column="event_date",
        filters={"event_date_from": "2026-01-01", "event_date_to": "2026-03-31"},
    )
    assert result.valid is True


def test_rejects_query_without_partition_filter():
    validator = PartitionValidator()
    result = validator.validate(
        partition_column="event_date",
        filters={"school_id": "school_123"},
    )
    assert result.valid is False
    assert "date range" in result.error.lower()


def test_accepts_when_no_partition_column():
    validator = PartitionValidator()
    result = validator.validate(partition_column=None, filters={})
    assert result.valid is False
    assert "partition debt" in result.error.lower()
