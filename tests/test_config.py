"""Tests for configuration loading."""

import pytest

from custom_data_mcp.config import ServerConfig


def test_config_loads_from_env(monkeypatch):
    monkeypatch.setenv("BIGQUERY_PROJECT", "test-project")
    monkeypatch.setenv("BIGQUERY_DATASETS", "reporting,analytics")
    config = ServerConfig()
    assert config.bigquery_project == "test-project"
    assert config.bigquery_datasets == ["reporting", "analytics"]


def test_config_defaults(monkeypatch):
    monkeypatch.setenv("BIGQUERY_PROJECT", "test-project")
    monkeypatch.setenv("BIGQUERY_DATASETS", "reporting")
    config = ServerConfig()
    assert config.bigquery_max_bytes == 1_073_741_824
    assert config.cache_ttl_seconds == 3600
    assert config.log_level == "INFO"


def test_config_requires_project(monkeypatch, tmp_path):
    monkeypatch.delenv("BIGQUERY_PROJECT", raising=False)
    monkeypatch.delenv("BIGQUERY_DATASETS", raising=False)
    monkeypatch.chdir(tmp_path)  # avoid reading project .env
    with pytest.raises(Exception):  # noqa: B017
        ServerConfig()
