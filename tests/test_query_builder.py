"""Tests for SQL query generation from metric definitions."""

import pytest

from taleemabad_data_mcp.engine.query_builder import QueryBuilder
from taleemabad_data_mcp.models.metric import GoldMetric


@pytest.fixture
def sample_metric():
    return GoldMetric(
        name="lp_adoption_rate_weekly",
        display_name="LP Adoption Rate",
        description="Percentage of teachers engaging with LPs",
        category="theory_of_change",
        tier="gold",
        status="certified",
        type="ratio",
        target=">= 65%",
        source_table="fact_lesson_plan_usage",
        partition_column="event_date",
        dimensions=["school_id", "region_id"],
        freshness_sla_hours=4,
        sensitivity="internal",
        owner="pedagogy_team",
        lineage={"silver": "fact_lesson_plan_usage", "bronze": "raw"},
    )


def test_build_basic_query(sample_metric):
    builder = QueryBuilder(project="my-project", dataset="reporting")
    sql, params = builder.build(
        metric=sample_metric,
        filters={"event_date_from": "2026-01-01", "event_date_to": "2026-03-31"},
    )
    assert "my-project.reporting.fact_lesson_plan_usage" in sql
    assert "@date_from" in sql
    assert "@date_to" in sql
    assert len(params) == 2


def test_build_with_dimension_filter(sample_metric):
    builder = QueryBuilder(project="my-project", dataset="reporting")
    sql, params = builder.build(
        metric=sample_metric,
        filters={
            "event_date_from": "2026-01-01",
            "event_date_to": "2026-03-31",
            "school_id": "school_123",
        },
    )
    assert "@dim_school_id" in sql
    assert len(params) == 3


def test_build_rejects_invalid_dimension(sample_metric):
    builder = QueryBuilder(project="my-project", dataset="reporting")
    with pytest.raises(ValueError, match="not a valid dimension"):
        builder.build(
            metric=sample_metric,
            filters={
                "event_date_from": "2026-01-01",
                "event_date_to": "2026-03-31",
                "invalid_column": "value",
            },
        )
