"""Tests for the YAML rule engine."""

from pathlib import Path

from taleemabad_data_mcp.engine.rule_engine import RuleEngine
from taleemabad_data_mcp.models.metric import MetricStatus

RULES_DIR = Path(__file__).parent.parent / "src" / "taleemabad_data_mcp" / "rules"


def test_load_metrics_from_yaml():
    engine = RuleEngine(RULES_DIR)
    engine.load()
    assert len(engine.metrics) == 2


def test_resolve_by_name():
    engine = RuleEngine(RULES_DIR)
    engine.load()
    metric = engine.resolve("lp_adoption_rate_weekly")
    assert metric is not None
    assert metric.name == "lp_adoption_rate_weekly"
    assert metric.status == MetricStatus.CERTIFIED


def test_resolve_is_case_insensitive():
    engine = RuleEngine(RULES_DIR)
    engine.load()
    metric = engine.resolve("LP_Adoption_Rate_Weekly")
    assert metric is not None
    assert metric.name == "lp_adoption_rate_weekly"


def test_resolve_by_synonym():
    engine = RuleEngine(RULES_DIR)
    engine.load()
    metric = engine.resolve("lesson plan adoption")
    assert metric is not None
    assert metric.name == "lp_adoption_rate_weekly"


def test_resolve_unknown_returns_none():
    engine = RuleEngine(RULES_DIR)
    engine.load()
    metric = engine.resolve("nonexistent_metric")
    assert metric is None


def test_list_by_category():
    engine = RuleEngine(RULES_DIR)
    engine.load()
    metrics = engine.list_by_category("theory_of_change")
    assert len(metrics) == 2
    assert all(m.category == "theory_of_change" for m in metrics)


def test_list_by_nonexistent_category():
    engine = RuleEngine(RULES_DIR)
    engine.load()
    metrics = engine.list_by_category("nonexistent")
    assert metrics == []


def test_list_all():
    engine = RuleEngine(RULES_DIR)
    engine.load()
    all_metrics = engine.list_all()
    assert len(all_metrics) == 2


def test_draft_metric_loaded_but_not_queryable():
    engine = RuleEngine(RULES_DIR)
    engine.load()
    metric = engine.resolve("fico_section_b_average")
    assert metric is not None
    assert metric.status == MetricStatus.DRAFT
    assert metric.is_queryable is False


def test_malformed_yaml_skipped(tmp_path):
    """Bad YAML files are skipped, not crash the server."""
    bad_file = tmp_path / "bad.yaml"
    bad_file.write_text("not: valid: yaml: [")
    good_file = tmp_path / "good.yaml"
    good_file.write_text("""
name: test_metric
display_name: Test
description: A test
category: theory_of_change
tier: gold
status: draft
type: simple
target: ">= 50%"
source_table: some_table
partition_column: event_date
dimensions: []
freshness_sla_hours: 4
sensitivity: internal
owner: test
lineage:
  silver: some_table
  bronze: raw
""")
    engine = RuleEngine(tmp_path)
    engine.load()
    assert len(engine.metrics) == 1
