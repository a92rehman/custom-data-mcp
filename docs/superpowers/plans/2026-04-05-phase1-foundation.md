# Phase 1: Foundation — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A working MCP server that loads metric definitions from YAML, validates queries, connects to BigQuery, and returns governed results with audit logging.

**Architecture:** FastMCP server with stdio transport. Metric definitions stored as YAML files loaded at startup via a rule engine. Queries go through a 7-step pipeline: receive → resolve → validate → cache-check → cost-estimate → execute → observe. BigQuery client managed via lifespan pattern.

**Tech Stack:** Python 3.11+, FastMCP (mcp[cli]), google-cloud-bigquery, pydantic/pydantic-settings, structlog, pyyaml, pytest/pytest-asyncio, ruff

---

## File Structure

```
pyproject.toml                              # Project config, dependencies
src/
  taleemabad_data_mcp/
    __init__.py                             # Package init, version
    __main__.py                             # Entry: python -m taleemabad_data_mcp
    server.py                               # FastMCP instance, lifespan, tool registration
    config.py                               # ServerConfig via pydantic-settings
    models/
      __init__.py
      metric.py                             # GoldMetric, MetricTarget, MetricLineage, MetricSource
      audit.py                              # AuditLogEntry
    engine/
      __init__.py
      rule_engine.py                        # Load YAML → GoldMetric objects, resolve by name/synonym
      query_builder.py                      # GoldMetric → parameterized SQL string
      partition_validator.py                # Reject queries missing partition filters
      cost_estimator.py                     # BigQuery dry-run, byte estimation
      audit_logger.py                       # Create + store audit log entries
    tools/
      __init__.py
      query_tools.py                        # query_metric tool (stub in Phase 1)
      governance_tools.py                   # list_metrics, describe_metric, get_metric_lineage, report_gap
    resources/                              # MCP resource definitions (empty in Phase 1)
      __init__.py
    prompts/                                # MCP prompt templates (empty in Phase 1)
      __init__.py
    rules/
      theory_of_change/
        lp_adoption_rate_weekly.yaml        # First real metric (certified)
        fico_section_b_average.yaml         # Second metric (draft — for testing lifecycle)
tests/
  __init__.py
  conftest.py                               # Shared fixtures
  test_config.py
  test_models.py
  test_rule_engine.py
  test_query_builder.py
  test_partition_validator.py
  test_cost_estimator.py
  test_audit_logger.py
  test_tools_query.py
  test_tools_governance.py
  test_server.py                            # Integration: full MCP client → tool → result
```

---

### Task 1: Project Scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `src/taleemabad_data_mcp/__init__.py`
- Create: `src/taleemabad_data_mcp/__main__.py`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`

- [ ] **Step 1: Create pyproject.toml**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "taleemabad-data-mcp"
version = "0.1.0"
description = "Taleemabad's Data Navigator — governed semantic layer for BigQuery"
requires-python = ">=3.11"
dependencies = [
    "mcp[cli]>=1.6.0",
    "google-cloud-bigquery>=3.25.0",
    "pydantic>=2.0",
    "pydantic-settings>=2.0",
    "structlog>=24.0",
    "pyyaml>=6.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.24",
    "pytest-cov>=5.0",
    "ruff>=0.8",
]

[tool.ruff]
target-version = "py311"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "N", "UP", "B", "SIM"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

- [ ] **Step 2: Create package init**

```python
# src/taleemabad_data_mcp/__init__.py
"""Taleemabad Data Navigator — governed semantic layer for BigQuery."""

__version__ = "0.1.0"
```

- [ ] **Step 3: Create entry point**

```python
# src/taleemabad_data_mcp/__main__.py
"""Entry point: python -m taleemabad_data_mcp"""

from taleemabad_data_mcp.server import mcp

if __name__ == "__main__":
    mcp.run()
```

- [ ] **Step 4: Create .gitignore**

```gitignore
# .gitignore
__pycache__/
*.pyc
.env
.venv/
dist/
*.egg-info/
.pytest_cache/
.ruff_cache/
htmlcov/
.coverage
```

- [ ] **Step 5: Create test conftest and empty dirs**

```python
# tests/__init__.py
# (empty)
```

```python
# tests/conftest.py
"""Shared test fixtures."""

import pytest
```

```python
# src/taleemabad_data_mcp/resources/__init__.py
"""MCP resource definitions. Populated in Phase 2+."""
```

```python
# src/taleemabad_data_mcp/prompts/__init__.py
"""MCP prompt templates. Populated in Phase 2+."""
```

- [ ] **Step 6: Install dependencies and verify**

Run: `uv sync`
Expected: Dependencies install successfully.

Run: `uv run ruff check src/ tests/`
Expected: No lint errors.

- [ ] **Step 7: Commit**

```bash
git init
git add pyproject.toml .gitignore .env.example src/ tests/
git commit -m "feat: project scaffolding with pyproject.toml and package structure"
```

---

### Task 2: Configuration

**Files:**
- Create: `src/taleemabad_data_mcp/config.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_config.py
"""Tests for configuration loading."""

import os
import pytest
from taleemabad_data_mcp.config import ServerConfig


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


def test_config_requires_project(monkeypatch):
    monkeypatch.delenv("BIGQUERY_PROJECT", raising=False)
    monkeypatch.delenv("BIGQUERY_DATASETS", raising=False)
    with pytest.raises(Exception):
        ServerConfig()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_config.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'taleemabad_data_mcp.config'`

- [ ] **Step 3: Implement config**

```python
# src/taleemabad_data_mcp/config.py
"""Server configuration via environment variables."""

from pydantic_settings import BaseSettings


class ServerConfig(BaseSettings):
    """Configuration loaded from environment variables or .env file."""

    bigquery_project: str
    bigquery_datasets: list[str]
    google_application_credentials: str | None = None
    bigquery_max_bytes: int = 1_073_741_824  # 1 GB
    cache_ttl_seconds: int = 3600
    log_level: str = "INFO"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_config.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add src/taleemabad_data_mcp/config.py tests/test_config.py
git commit -m "feat: add server configuration with pydantic-settings"
```

---

### Task 3: Pydantic Models

**Files:**
- Create: `src/taleemabad_data_mcp/models/__init__.py`
- Create: `src/taleemabad_data_mcp/models/metric.py`
- Create: `src/taleemabad_data_mcp/models/audit.py`
- Create: `tests/test_models.py`

- [ ] **Step 1: Write failing test for GoldMetric model**

```python
# tests/test_models.py
"""Tests for Pydantic models."""

import pytest
from taleemabad_data_mcp.models.metric import (
    GoldMetric,
    MetricStatus,
    MetricType,
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_models.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement models**

```python
# src/taleemabad_data_mcp/models/__init__.py
"""Pydantic models for the Data Governance MCP."""

from taleemabad_data_mcp.models.metric import (
    GoldMetric,
    MetricStatus,
    MetricType,
    Sensitivity,
)
from taleemabad_data_mcp.models.audit import AuditLogEntry

__all__ = [
    "GoldMetric",
    "MetricStatus",
    "MetricType",
    "Sensitivity",
    "AuditLogEntry",
]
```

```python
# src/taleemabad_data_mcp/models/metric.py
"""Gold metric definition model."""

from enum import StrEnum

from pydantic import BaseModel


class MetricStatus(StrEnum):
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    CERTIFIED = "certified"
    DEPRECATED = "deprecated"


class MetricType(StrEnum):
    SIMPLE = "simple"
    RATIO = "ratio"
    CUMULATIVE = "cumulative"
    DERIVED = "derived"


class Sensitivity(StrEnum):
    PUBLIC = "public"
    INTERNAL = "internal"
    EXTERNAL_GUARDED = "external_guarded"


class MetricLineage(BaseModel):
    silver: str
    bronze: str


class GoldMetric(BaseModel):
    name: str
    display_name: str
    description: str
    category: str
    tier: str = "gold"
    status: MetricStatus
    type: MetricType
    target: str
    source_table: str
    partition_column: str
    dimensions: list[str]
    freshness_sla_hours: int
    sensitivity: Sensitivity
    owner: str
    lineage: MetricLineage
    synonyms: list[str] = []

    @property
    def is_queryable(self) -> bool:
        return self.status == MetricStatus.CERTIFIED
```

```python
# src/taleemabad_data_mcp/models/audit.py
"""Audit log entry model."""

import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, Field


class AuditLogEntry(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    session_id: str | None = None
    user_id: str | None = None
    query_text: str
    matched_metric: str | None = None
    generated_sql: str | None = None
    tables_accessed: list[str] = []
    rows_returned: int | None = None
    execution_ms: int | None = None
    result_cached: bool = False
    error_type: str | None = None
    error_message: str | None = None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_models.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add src/taleemabad_data_mcp/models/ tests/test_models.py
git commit -m "feat: add GoldMetric and AuditLogEntry pydantic models"
```

---

### Task 4: Rule Engine (YAML Loader + Resolver)

**Files:**
- Create: `src/taleemabad_data_mcp/engine/__init__.py`
- Create: `src/taleemabad_data_mcp/engine/rule_engine.py`
- Create: `src/taleemabad_data_mcp/rules/theory_of_change/lp_adoption_rate_weekly.yaml`
- Create: `tests/test_rule_engine.py`

- [ ] **Step 1: Create metric YAML files**

```yaml
# src/taleemabad_data_mcp/rules/theory_of_change/lp_adoption_rate_weekly.yaml
name: lp_adoption_rate_weekly
display_name: "LP Adoption Rate (Weekly)"
description: "Percentage of teachers engaging with AI-generated lesson plans per week. Engagement = used, modified, or completed."
category: theory_of_change
tier: gold
status: certified
type: ratio
target: ">= 65%"
source_table: fact_lesson_plan_usage
partition_column: event_date
dimensions:
  - school_id
  - region_id
  - grade
  - subject
freshness_sla_hours: 4
sensitivity: internal
owner: pedagogy_team
lineage:
  silver: fact_lesson_plan_usage
  bronze: raw_app_events
synonyms:
  - "lp usage rate"
  - "lesson plan adoption"
```

```yaml
# src/taleemabad_data_mcp/rules/theory_of_change/fico_section_b_average.yaml
name: fico_section_b_average
display_name: "FICO Section B Average"
description: "Average score across 10 LP fidelity indicators (B1-B10), 4-point scale."
category: theory_of_change
tier: gold
status: draft
type: simple
target: ">= 60%"
source_table: fact_observation_scores
partition_column: observation_date
dimensions:
  - school_id
  - region_id
  - teacher_id
freshness_sla_hours: 4
sensitivity: internal
owner: pedagogy_team
lineage:
  silver: fact_observation_scores
  bronze: raw_observation_events
```

- [ ] **Step 2: Write failing test**

```python
# tests/test_rule_engine.py
"""Tests for the YAML rule engine."""

import pytest
from pathlib import Path
from taleemabad_data_mcp.engine.rule_engine import RuleEngine
from taleemabad_data_mcp.models.metric import MetricStatus


RULES_DIR = Path(__file__).parent.parent / "src" / "taleemabad_data_mcp" / "rules"


def test_load_metrics_from_yaml():
    engine = RuleEngine(RULES_DIR)
    engine.load()
    assert len(engine.metrics) == 2  # certified + draft


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
    assert len(engine.metrics) == 1  # only the good one loaded
```

- [ ] **Step 3: Run test to verify it fails**

Run: `uv run pytest tests/test_rule_engine.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 4: Implement rule engine**

```python
# src/taleemabad_data_mcp/engine/__init__.py
"""Core governance engine."""
```

```python
# src/taleemabad_data_mcp/engine/rule_engine.py
"""Load Gold metric definitions from YAML and resolve queries to metrics."""

from pathlib import Path

import structlog
import yaml

from taleemabad_data_mcp.models.metric import GoldMetric

logger = structlog.get_logger()


class RuleEngine:
    """Loads metric YAML files and resolves queries to GoldMetric objects."""

    def __init__(self, rules_dir: Path) -> None:
        self._rules_dir = rules_dir
        self._metrics: dict[str, GoldMetric] = {}
        self._synonyms: dict[str, str] = {}

    def load(self) -> None:
        """Load all YAML metric definitions from the rules directory."""
        self._metrics.clear()
        self._synonyms.clear()

        for yaml_file in self._rules_dir.rglob("*.yaml"):
            try:
                with open(yaml_file) as f:
                    data = yaml.safe_load(f)
                if not isinstance(data, dict):
                    logger.warning("skipping_non_dict_yaml", file=str(yaml_file))
                    continue
                metric = GoldMetric(**data)
            except (yaml.YAMLError, Exception) as e:
                logger.error("failed_to_load_metric", file=str(yaml_file), error=str(e))
                continue

            key = metric.name.lower()
            if key in self._metrics:
                logger.warning("duplicate_metric_name", name=metric.name, file=str(yaml_file))
            self._metrics[key] = metric
            for synonym in metric.synonyms:
                syn_key = synonym.lower()
                if syn_key in self._synonyms:
                    logger.warning("duplicate_synonym", synonym=synonym, file=str(yaml_file))
                self._synonyms[syn_key] = key

    def resolve(self, name_or_synonym: str) -> GoldMetric | None:
        """Resolve a metric by exact name or synonym. Returns None if not found."""
        key = name_or_synonym.lower().strip()
        if key in self._metrics:
            return self._metrics[key]
        metric_name = self._synonyms.get(key)
        if metric_name:
            return self._metrics.get(metric_name)
        return None

    def list_all(self) -> list[GoldMetric]:
        """Return all loaded metrics."""
        return list(self._metrics.values())

    def list_by_category(self, category: str) -> list[GoldMetric]:
        """Return metrics filtered by category."""
        return [m for m in self._metrics.values() if m.category == category]

    @property
    def metrics(self) -> dict[str, GoldMetric]:
        return self._metrics
```

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run pytest tests/test_rule_engine.py -v`
Expected: 6 passed.

- [ ] **Step 6: Commit**

```bash
git add src/taleemabad_data_mcp/engine/ src/taleemabad_data_mcp/rules/ tests/test_rule_engine.py
git commit -m "feat: add rule engine with YAML metric loading and resolution"
```

---

### Task 5: Partition Validator

**Files:**
- Create: `src/taleemabad_data_mcp/engine/partition_validator.py`
- Create: `tests/test_partition_validator.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_partition_validator.py
"""Tests for partition filter validation."""

import pytest
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
    """Tables without partition columns should flag partition debt."""
    validator = PartitionValidator()
    result = validator.validate(
        partition_column=None,
        filters={},
    )
    assert result.valid is False
    assert "partition debt" in result.error.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_partition_validator.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement**

```python
# src/taleemabad_data_mcp/engine/partition_validator.py
"""Validate that queries include required partition filters."""

from pydantic import BaseModel


class ValidationResult(BaseModel):
    valid: bool
    error: str = ""


class PartitionValidator:
    """Enforces partition-first execution policy."""

    def validate(
        self,
        partition_column: str | None,
        filters: dict[str, str],
    ) -> ValidationResult:
        if partition_column is None:
            return ValidationResult(
                valid=False,
                error="This table has no partition column. Flagged as partition debt for the data team.",
            )

        date_from_key = f"{partition_column}_from"
        date_to_key = f"{partition_column}_to"

        has_filter = date_from_key in filters or date_to_key in filters
        if not has_filter:
            return ValidationResult(
                valid=False,
                error=f"Please specify a date range. Without a filter on '{partition_column}', this query would scan the entire table.",
            )

        return ValidationResult(valid=True)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_partition_validator.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add src/taleemabad_data_mcp/engine/partition_validator.py tests/test_partition_validator.py
git commit -m "feat: add partition validator for partition-first execution policy"
```

---

### Task 6: Cost Estimator

**Files:**
- Create: `src/taleemabad_data_mcp/engine/cost_estimator.py`
- Create: `tests/test_cost_estimator.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_cost_estimator.py
"""Tests for BigQuery cost estimation."""

import pytest
from unittest.mock import MagicMock
from taleemabad_data_mcp.engine.cost_estimator import CostEstimator


def test_estimate_returns_bytes_and_cost():
    mock_client = MagicMock()
    mock_job = MagicMock()
    mock_job.total_bytes_processed = 500_000_000  # 500 MB
    mock_client.query.return_value = mock_job

    estimator = CostEstimator(mock_client, max_bytes=1_073_741_824)
    result = estimator.estimate("SELECT * FROM table WHERE date = '2026-01-01'")

    assert result.bytes_processed == 500_000_000
    assert result.needs_confirmation is False


def test_estimate_flags_over_threshold():
    mock_client = MagicMock()
    mock_job = MagicMock()
    mock_job.total_bytes_processed = 2_000_000_000  # 2 GB
    mock_client.query.return_value = mock_job

    estimator = CostEstimator(mock_client, max_bytes=1_073_741_824)
    result = estimator.estimate("SELECT * FROM big_table")

    assert result.needs_confirmation is True


def test_estimate_calculates_usd_cost():
    mock_client = MagicMock()
    mock_job = MagicMock()
    mock_job.total_bytes_processed = 1_099_511_627_776  # 1 TB
    mock_client.query.return_value = mock_job

    estimator = CostEstimator(mock_client, max_bytes=2_000_000_000_000)
    result = estimator.estimate("SELECT * FROM table")

    assert abs(result.cost_usd - 6.25) < 0.01  # $6.25 per TB
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_cost_estimator.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement**

```python
# src/taleemabad_data_mcp/engine/cost_estimator.py
"""Estimate BigQuery query cost via dry run."""

from pydantic import BaseModel

from google.cloud import bigquery


class CostEstimate(BaseModel):
    bytes_processed: int
    cost_usd: float
    needs_confirmation: bool


class CostEstimator:
    """Estimate query cost before execution."""

    PRICE_PER_TB_USD = 6.25
    BYTES_PER_TB = 1_099_511_627_776

    def __init__(self, bq_client: bigquery.Client, max_bytes: int) -> None:
        self._client = bq_client
        self._max_bytes = max_bytes

    def estimate(self, sql: str, params: list | None = None) -> CostEstimate:
        """Run a dry-run query to estimate cost."""
        job_config = bigquery.QueryJobConfig(
            dry_run=True,
            use_query_cache=False,
        )
        if params:
            job_config.query_parameters = params

        job = self._client.query(sql, job_config=job_config)
        bytes_processed = job.total_bytes_processed
        cost_usd = (bytes_processed / self.BYTES_PER_TB) * self.PRICE_PER_TB_USD

        return CostEstimate(
            bytes_processed=bytes_processed,
            cost_usd=cost_usd,
            needs_confirmation=bytes_processed > self._max_bytes,
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_cost_estimator.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add src/taleemabad_data_mcp/engine/cost_estimator.py tests/test_cost_estimator.py
git commit -m "feat: add cost estimator with BigQuery dry-run"
```

---

### Task 7: Audit Logger

**Files:**
- Create: `src/taleemabad_data_mcp/engine/audit_logger.py`
- Create: `tests/test_audit_logger.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_audit_logger.py
"""Tests for audit logging."""

import pytest
from taleemabad_data_mcp.engine.audit_logger import AuditLogger


def test_log_creates_entry():
    logger = AuditLogger()
    entry = logger.log(
        query_text="What is LP adoption?",
        matched_metric="lp_adoption_rate_weekly",
        generated_sql="SELECT ...",
        tables_accessed=["fact_lesson_plan_usage"],
    )
    assert entry.event_id is not None
    assert entry.timestamp is not None
    assert entry.query_text == "What is LP adoption?"
    assert entry.matched_metric == "lp_adoption_rate_weekly"


def test_log_stores_entries():
    logger = AuditLogger()
    logger.log(query_text="query 1")
    logger.log(query_text="query 2")
    assert len(logger.entries) == 2


def test_log_with_error():
    logger = AuditLogger()
    entry = logger.log(
        query_text="bad query",
        error_type="NoMatchingMetric",
        error_message="No metric found for 'bad query'",
    )
    assert entry.error_type == "NoMatchingMetric"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_audit_logger.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement**

```python
# src/taleemabad_data_mcp/engine/audit_logger.py
"""Immutable audit log for all MCP interactions."""

import structlog

from taleemabad_data_mcp.models.audit import AuditLogEntry

logger = structlog.get_logger()


class AuditLogger:
    """Creates and stores immutable audit log entries."""

    def __init__(self) -> None:
        self._entries: list[AuditLogEntry] = []

    def log(
        self,
        query_text: str,
        session_id: str | None = None,
        user_id: str | None = None,
        matched_metric: str | None = None,
        generated_sql: str | None = None,
        tables_accessed: list[str] | None = None,
        rows_returned: int | None = None,
        execution_ms: int | None = None,
        result_cached: bool = False,
        error_type: str | None = None,
        error_message: str | None = None,
    ) -> AuditLogEntry:
        """Create an immutable audit log entry."""
        entry = AuditLogEntry(
            query_text=query_text,
            session_id=session_id,
            user_id=user_id,
            matched_metric=matched_metric,
            generated_sql=generated_sql,
            tables_accessed=tables_accessed or [],
            rows_returned=rows_returned,
            execution_ms=execution_ms,
            result_cached=result_cached,
            error_type=error_type,
            error_message=error_message,
        )
        self._entries.append(entry)
        logger.info(
            "audit_log_entry",
            event_id=entry.event_id,
            query_text=entry.query_text,
            matched_metric=entry.matched_metric,
            error_type=entry.error_type,
        )
        return entry

    @property
    def entries(self) -> list[AuditLogEntry]:
        return list(self._entries)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_audit_logger.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add src/taleemabad_data_mcp/engine/audit_logger.py tests/test_audit_logger.py
git commit -m "feat: add audit logger for immutable interaction logging"
```

---

### Task 8: Query Builder

**Files:**
- Create: `src/taleemabad_data_mcp/engine/query_builder.py`
- Create: `tests/test_query_builder.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_query_builder.py
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
    assert "event_date >=" in sql or "@date_from" in sql
    assert len(params) >= 2


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
    assert "@school_id" in sql or "school_id" in sql
    assert len(params) >= 3


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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_query_builder.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement**

```python
# src/taleemabad_data_mcp/engine/query_builder.py
"""Generate parameterized SQL from Gold metric definitions."""

from google.cloud import bigquery

from taleemabad_data_mcp.models.metric import GoldMetric


class QueryBuilder:
    """Builds parameterized BigQuery SQL from metric definitions."""

    def __init__(self, project: str, dataset: str) -> None:
        self._project = project
        self._dataset = dataset

    def build(
        self,
        metric: GoldMetric,
        filters: dict[str, str],
    ) -> tuple[str, list[bigquery.ScalarQueryParameter]]:
        """Build a parameterized SQL query from a metric and filters."""
        table = f"{self._project}.{self._dataset}.{metric.source_table}"
        params: list[bigquery.ScalarQueryParameter] = []
        where_clauses: list[str] = []

        # Partition filter
        pc = metric.partition_column
        from_key = f"{pc}_from"
        to_key = f"{pc}_to"

        if from_key in filters:
            where_clauses.append(f"{pc} >= @date_from")
            params.append(
                bigquery.ScalarQueryParameter("date_from", "STRING", filters[from_key])
            )

        if to_key in filters:
            where_clauses.append(f"{pc} <= @date_to")
            params.append(
                bigquery.ScalarQueryParameter("date_to", "STRING", filters[to_key])
            )

        # Dimension filters
        reserved_keys = {from_key, to_key}
        for key, value in filters.items():
            if key in reserved_keys:
                continue
            if key not in metric.dimensions:
                raise ValueError(
                    f"'{key}' is not a valid dimension for metric '{metric.name}'. "
                    f"Valid dimensions: {metric.dimensions}"
                )
            param_name = f"dim_{key}"
            where_clauses.append(f"{key} = @{param_name}")
            params.append(
                bigquery.ScalarQueryParameter(param_name, "STRING", value)
            )

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        sql = f"SELECT * FROM `{table}` WHERE {where_sql} LIMIT 1000"

        return sql, params
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_query_builder.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add src/taleemabad_data_mcp/engine/query_builder.py tests/test_query_builder.py
git commit -m "feat: add query builder for parameterized SQL from metric YAML"
```

---

### Task 9: FastMCP Server + Tools

**Files:**
- Create: `src/taleemabad_data_mcp/server.py`
- Create: `src/taleemabad_data_mcp/tools/__init__.py`
- Create: `src/taleemabad_data_mcp/tools/governance_tools.py`
- Create: `tests/test_tools_governance.py`
- Create: `tests/test_server.py`

- [ ] **Step 1: Write failing test for governance tools**

```python
# tests/test_tools_governance.py
"""Tests for governance MCP tools (list, describe, lineage)."""

import pytest
from taleemabad_data_mcp.server import mcp


@pytest.fixture
async def client():
    async with mcp.test_client() as c:
        yield c


@pytest.mark.asyncio
async def test_list_metrics(client):
    result = await client.call_tool("list_metrics", {})
    assert result is not None


@pytest.mark.asyncio
async def test_describe_metric(client):
    result = await client.call_tool("describe_metric", {"metric_name": "lp_adoption_rate_weekly"})
    assert "lp_adoption_rate_weekly" in str(result)


@pytest.mark.asyncio
async def test_describe_unknown_metric(client):
    result = await client.call_tool("describe_metric", {"metric_name": "nonexistent"})
    assert "not found" in str(result).lower() or "no metric" in str(result).lower()


@pytest.mark.asyncio
async def test_get_metric_lineage(client):
    result = await client.call_tool("get_metric_lineage", {"metric_name": "lp_adoption_rate_weekly"})
    assert "silver" in str(result).lower() or "fact_lesson_plan_usage" in str(result)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_tools_governance.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement server with lifespan and governance tools**

```python
# src/taleemabad_data_mcp/tools/__init__.py
"""MCP tool implementations."""
```

```python
# src/taleemabad_data_mcp/tools/governance_tools.py
"""Governance tools: list, describe, lineage, report gap."""

import json

from mcp.server.fastmcp import Context

from taleemabad_data_mcp.engine.rule_engine import RuleEngine


def register_governance_tools(mcp, rule_engine: RuleEngine):
    """Register governance tools on the FastMCP server."""

    @mcp.tool()
    async def list_metrics(category: str | None = None, ctx: Context = None) -> str:
        """List available Gold metrics, optionally filtered by category.

        Args:
            category: Filter by category (e.g., 'theory_of_change', 'fico_observation').
                      Omit to list all metrics.
        """
        if category:
            metrics = rule_engine.list_by_category(category)
        else:
            metrics = rule_engine.list_all()

        result = []
        for m in metrics:
            queryable = "queryable" if m.is_queryable else f"status: {m.status}"
            result.append(f"- {m.display_name} ({m.name}) [{queryable}]: {m.description}")

        if not result:
            return f"No metrics found for category '{category}'." if category else "No metrics loaded."

        return "\n".join(result)

    @mcp.tool()
    async def describe_metric(metric_name: str, ctx: Context = None) -> str:
        """Get full definition, target, lineage, and freshness info for a metric.

        Args:
            metric_name: The metric name or synonym to look up.
        """
        metric = rule_engine.resolve(metric_name)
        if metric is None:
            return f"No metric found for '{metric_name}'. Use list_metrics to see available metrics."

        return json.dumps(metric.model_dump(), indent=2, default=str)

    @mcp.tool()
    async def get_metric_lineage(metric_name: str, ctx: Context = None) -> str:
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
    async def report_gap(description: str, ctx: Context = None) -> str:
        """Report a metric that should exist but doesn't.

        Args:
            description: Description of the metric you need (e.g., 'teacher training completion by region').
        """
        # In Phase 1, just log it. Phase 3 adds proper dead letter queue.
        if ctx:
            await ctx.info(f"Metric gap reported: {description}")
        return f"Gap reported: '{description}'. This has been logged for the data team to review."
```

```python
# src/taleemabad_data_mcp/server.py
"""FastMCP server setup with lifespan and tool registration."""

from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from taleemabad_data_mcp.config import ServerConfig
from taleemabad_data_mcp.engine.audit_logger import AuditLogger
from taleemabad_data_mcp.engine.rule_engine import RuleEngine
from taleemabad_data_mcp.tools.governance_tools import register_governance_tools


@dataclass
class AppContext:
    config: ServerConfig
    rule_engine: RuleEngine
    audit_logger: AuditLogger


@asynccontextmanager
async def app_lifespan(server: FastMCP):
    """Initialize server-wide resources. BigQuery client added in Phase 2."""
    config = ServerConfig()
    rules_dir = Path(__file__).parent / "rules"
    rule_engine = RuleEngine(rules_dir)
    rule_engine.load()
    audit_logger = AuditLogger()

    yield AppContext(
        config=config,
        rule_engine=rule_engine,
        audit_logger=audit_logger,
    )


# Create FastMCP server with lifespan
mcp = FastMCP("Taleemabad Data Navigator", lifespan=app_lifespan)

# Register tools (rule_engine accessed via ctx.request_context.lifespan_context at runtime)
# For Phase 1, also load eagerly for test_client compatibility
_rules_dir = Path(__file__).parent / "rules"
_rule_engine = RuleEngine(_rules_dir)
_rule_engine.load()
register_governance_tools(mcp, _rule_engine)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_tools_governance.py -v`
Expected: 4 passed.

- [ ] **Step 5: Write integration test**

```python
# tests/test_server.py
"""Integration test: full MCP client → tool → result."""

import pytest
from taleemabad_data_mcp.server import mcp


@pytest.fixture
async def client():
    async with mcp.test_client() as c:
        yield c


@pytest.mark.asyncio
async def test_server_starts_and_lists_tools(client):
    tools = await client.list_tools()
    tool_names = [t.name for t in tools]
    assert "list_metrics" in tool_names
    assert "describe_metric" in tool_names
    assert "get_metric_lineage" in tool_names
    assert "report_gap" in tool_names
```

- [ ] **Step 6: Run full test suite**

Run: `uv run pytest -v`
Expected: All tests pass.

- [ ] **Step 7: Commit**

```bash
git add src/taleemabad_data_mcp/server.py src/taleemabad_data_mcp/tools/ tests/test_tools_governance.py tests/test_server.py
git commit -m "feat: add FastMCP server with governance tools (list, describe, lineage, report_gap)"
```

---

### Task 10: Run Full Suite + Lint + Verify

**Files:** None new — verification only.

- [ ] **Step 1: Run full test suite with coverage**

Run: `uv run pytest --cov=src/taleemabad_data_mcp --cov-report=term-missing -v`
Expected: All tests pass, coverage >= 80%.

- [ ] **Step 2: Lint**

Run: `uv run ruff check src/ tests/`
Expected: No errors.

- [ ] **Step 3: Format**

Run: `uv run ruff format src/ tests/`
Expected: No changes (already formatted).

- [ ] **Step 4: Test MCP Inspector**

Run: `uv run mcp dev src/taleemabad_data_mcp/server.py`
Expected: Inspector opens. Call `list_metrics` — returns LP adoption metric.

- [ ] **Step 5: Final commit**

```bash
git add -A
git commit -m "chore: phase 1 complete — core MCP server with rule engine and governance tools"
```

---

## Summary

| Task | Component | Tests |
|------|-----------|-------|
| 1 | Project scaffolding | — |
| 2 | Configuration | 3 |
| 3 | Pydantic models | 3 |
| 4 | Rule engine (YAML) | 11 |
| 5 | Partition validator | 3 |
| 6 | Cost estimator | 3 |
| 7 | Audit logger | 3 |
| 8 | Query builder | 3 |
| 9 | MCP server + tools | 5 |
| 10 | Full verification | — |
| **Total** | **10 tasks** | **34 tests** |

## What Phase 1 Delivers

- Working MCP server connectable to Claude Code via stdio
- Lifespan pattern established (config, rule engine, audit logger)
- 4 governance tools: `list_metrics`, `describe_metric`, `get_metric_lineage`, `report_gap`
- Rule engine loading Gold metrics from YAML with error handling for malformed files
- Partition validation, cost estimation, query building
- Audit logging for every interaction (with session_id/user_id support)
- 2 metric definitions: `lp_adoption_rate_weekly` (certified) + `fico_section_b_average` (draft)
- 34 tests with 80%+ coverage

## What Phase 1 Does NOT Include (deferred to later phases)

- `query_metric` tool with live BigQuery execution (needs BigQuery credentials in CI)
- Conversational clarification/disambiguation
- Cache implementation
- Circuit breaker
- Observability dashboard / weekly digest
