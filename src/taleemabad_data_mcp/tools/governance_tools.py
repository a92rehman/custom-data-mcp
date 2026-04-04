"""Governance tools: list, describe, lineage, report gap."""

import json

from mcp.server.fastmcp import Context

from taleemabad_data_mcp.engine.rule_engine import RuleEngine


def register_governance_tools(mcp, rule_engine: RuleEngine):
    """Register governance tools on the FastMCP server."""

    @mcp.tool()
    async def list_metrics(category: str | None = None, ctx: Context | None = None) -> str:
        """List available Gold metrics, optionally filtered by category.

        Args:
            category: Filter by category (e.g., 'theory_of_change'). Omit to list all.
        """
        metrics = (
            rule_engine.list_by_category(category) if category else rule_engine.list_all()
        )
        result = []
        for m in metrics:
            queryable = "queryable" if m.is_queryable else f"status: {m.status}"
            result.append(f"- {m.display_name} ({m.name}) [{queryable}]: {m.description}")
        if not result:
            if category:
                return f"No metrics found for category '{category}'."
            return "No metrics loaded."
        return "\n".join(result)

    @mcp.tool()
    async def describe_metric(metric_name: str, ctx: Context | None = None) -> str:
        """Get full definition, target, lineage, and freshness info for a metric.

        Args:
            metric_name: The metric name or synonym to look up.
        """
        metric = rule_engine.resolve(metric_name)
        if metric is None:
            return (
                f"No metric found for '{metric_name}'. "
                "Use list_metrics to see available metrics."
            )
        return json.dumps(metric.model_dump(), indent=2, default=str)

    @mcp.tool()
    async def get_metric_lineage(metric_name: str, ctx: Context | None = None) -> str:
        """Trace a metric from Gold back through Silver to Bronze sources.

        Args:
            metric_name: The metric name to trace.
        """
        metric = rule_engine.resolve(metric_name)
        if metric is None:
            return f"No metric found for '{metric_name}'."
        return (
            f"Lineage for {metric.display_name}:\n"
            f"  Gold:   {metric.name}\n"
            f"  Silver: {metric.lineage.silver}\n"
            f"  Bronze: {metric.lineage.bronze}"
        )

    @mcp.tool()
    async def report_gap(description: str, ctx: Context | None = None) -> str:
        """Report a metric that should exist but doesn't.

        Args:
            description: Description of the metric you need.
        """
        if ctx:
            await ctx.info(f"Metric gap reported: {description}")
        return f"Gap reported: '{description}'. This has been logged for the data team to review."
