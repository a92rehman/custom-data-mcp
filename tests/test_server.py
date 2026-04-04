"""Integration test: full MCP server tool registration."""

import pytest

from taleemabad_data_mcp.server import mcp


@pytest.mark.asyncio
async def test_server_starts_and_lists_tools():
    tools = await mcp.list_tools()
    tool_names = [t.name for t in tools]
    assert "list_metrics" in tool_names
    assert "describe_metric" in tool_names
    assert "get_metric_lineage" in tool_names
    assert "report_gap" in tool_names
