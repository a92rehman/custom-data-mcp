"""Tests for Pydantic models."""

from taleemabad_data_mcp.models.metric import (
    GoldMetric,
    MetricStatus,
    Sensitivity,
)


def test_gold_metric_from_dict():
    data = {
        "name": "lp_adoption_rate_weekly",
        "display_name": "LP Adoption Rate (Weekly)",
        "description": "Percentage of teachers engaging with LPs per week",
        "category": "theory_of_change",
        "tier": "gold",
        "status": "certified",
        "type": "ratio",
        "target": ">= 65%",
        "source_table": "fact_lesson_plan_usage",
        "partition_column": "event_date",
        "dimensions": ["school_id", "region_id"],
        "freshness_sla_hours": 4,
        "sensitivity": "internal",
        "owner": "pedagogy_team",
        "lineage": {
            "silver": "fact_lesson_plan_usage",
            "bronze": "raw_app_events",
        },
    }
    metric = GoldMetric(**data)
    assert metric.name == "lp_adoption_rate_weekly"
    assert metric.status == MetricStatus.CERTIFIED
    assert metric.sensitivity == Sensitivity.INTERNAL
    assert metric.is_queryable is True


def test_draft_metric_is_not_queryable():
    data = {
        "name": "test_metric",
        "display_name": "Test",
        "description": "Test metric",
        "category": "theory_of_change",
        "tier": "gold",
        "status": "draft",
        "type": "simple",
        "target": ">= 50%",
        "source_table": "some_table",
        "partition_column": "event_date",
        "dimensions": [],
        "freshness_sla_hours": 4,
        "sensitivity": "internal",
        "owner": "test_team",
        "lineage": {"silver": "some_table", "bronze": "raw"},
    }
    metric = GoldMetric(**data)
    assert metric.is_queryable is False


def test_metric_status_enum():
    assert MetricStatus.DRAFT == "draft"
    assert MetricStatus.CERTIFIED == "certified"
    assert MetricStatus.DEPRECATED == "deprecated"
