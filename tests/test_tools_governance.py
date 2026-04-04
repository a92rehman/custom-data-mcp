"""Tests for governance MCP tools."""

import pytest

from taleemabad_data_mcp.server import mcp


@pytest.mark.asyncio
async def test_list_metrics():
    result = await mcp.call_tool("list_metrics", {})
    assert result is not None


@pytest.mark.asyncio
async def test_describe_metric():
    result = await mcp.call_tool("describe_metric", {"metric_name": "lp_adoption_rate_weekly"})
    assert "lp_adoption_rate_weekly" in str(result)


@pytest.mark.asyncio
async def test_describe_unknown_metric():
    result = await mcp.call_tool("describe_metric", {"metric_name": "nonexistent"})
    assert "not found" in str(result).lower() or "no metric" in str(result).lower()


@pytest.mark.asyncio
async def test_get_metric_lineage():
    result = await mcp.call_tool("get_metric_lineage", {"metric_name": "lp_adoption_rate_weekly"})
    assert "silver" in str(result).lower() or "fact_lesson_plan_usage" in str(result)
