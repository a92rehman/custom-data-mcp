"""Tests for BigQuery cost estimation."""

from unittest.mock import MagicMock

from taleemabad_data_mcp.engine.cost_estimator import CostEstimator


def test_estimate_returns_bytes_and_cost():
    mock_client = MagicMock()
    mock_job = MagicMock()
    mock_job.total_bytes_processed = 500_000_000
    mock_client.query.return_value = mock_job
    estimator = CostEstimator(mock_client, max_bytes=1_073_741_824)
    result = estimator.estimate("SELECT * FROM table WHERE date = '2026-01-01'")
    assert result.bytes_processed == 500_000_000
    assert result.needs_confirmation is False


def test_estimate_flags_over_threshold():
    mock_client = MagicMock()
    mock_job = MagicMock()
    mock_job.total_bytes_processed = 2_000_000_000
    mock_client.query.return_value = mock_job
    estimator = CostEstimator(mock_client, max_bytes=1_073_741_824)
    result = estimator.estimate("SELECT * FROM big_table")
    assert result.needs_confirmation is True


def test_estimate_calculates_usd_cost():
    mock_client = MagicMock()
    mock_job = MagicMock()
    mock_job.total_bytes_processed = 1_099_511_627_776
    mock_client.query.return_value = mock_job
    estimator = CostEstimator(mock_client, max_bytes=2_000_000_000_000)
    result = estimator.estimate("SELECT * FROM table")
    assert abs(result.cost_usd - 6.25) < 0.01
