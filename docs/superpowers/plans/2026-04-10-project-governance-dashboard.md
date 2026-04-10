# Project Governance Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Project Status section to the Overview page and a new Governance tab showing table-level rule coverage across all Taleemabad projects.

**Architecture:** A `projects.yaml` registry lists all projects. A `governance_mapper.py` module parses rule `.md` files to extract table references. The Overview page shows a compact project table. A new Governance page shows per-table governance status with filters.

**Tech Stack:** Python 3.11, Streamlit, Plotly, PyYAML, BigQuery `__TABLES__` metadata, regex for rule parsing.

**Spec:** `docs/superpowers/specs/2026-04-10-project-governance-dashboard-design.md`

---

## File Structure

| File | Action | Responsibility |
|------|--------|---------------|
| `src/taleemabad_data_mcp/projects.yaml` | Create | Project registry — single source of truth for all projects |
| `src/taleemabad_data_mcp/engine/governance_mapper.py` | Create | Parse rule files → extract table references → return mapping |
| `src/taleemabad_data_mcp/dashboard/data/projects.py` | Create | Load projects.yaml + query BigQuery `__TABLES__` for stats |
| `src/taleemabad_data_mcp/dashboard/pages/0_Overview.py` | Modify | Add Project Status section between KPI row and Activity Trend |
| `src/taleemabad_data_mcp/dashboard/pages/6_Governance.py` | Create | New tab: table-level governance detail with filters |
| `src/taleemabad_data_mcp/dashboard/app.py` | Modify | Register new Governance page in navigation |
| `tests/test_governance_mapper.py` | Create | Tests for rule parsing logic |
| `pyproject.toml` | Modify | Add `pyyaml` dependency |

---

### Task 1: Add PyYAML dependency

**Files:**
- Modify: `pyproject.toml:10-17`

- [ ] **Step 1: Add pyyaml to dependencies**

In `pyproject.toml`, add `"pyyaml>=6.0"` to the `dependencies` list:

```toml
dependencies = [
    "mcp[cli]>=1.6.0",
    "google-cloud-bigquery>=3.25.0",
    "pydantic>=2.0",
    "pydantic-settings>=2.0",
    "structlog>=24.0",
    "click>=8.0",
    "pyyaml>=6.0",
]
```

- [ ] **Step 2: Sync deps**

Run: `uv sync`

- [ ] **Step 3: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "chore: add pyyaml dependency for project registry"
```

---

### Task 2: Create projects.yaml

**Files:**
- Create: `src/taleemabad_data_mcp/projects.yaml`

- [ ] **Step 1: Create the registry file**

```yaml
# Project Registry — single source of truth for all Taleemabad projects.
# Adding a new project: add an entry here. No code changes needed.
# Status values: active | inactive | system

projects:
  - name: "ICT/Islamabad"
    dataset: "tbproddb"
    status: "active"
    region: "ict-islamabad"
    description: "ICT school program — teachers, lesson plans, coaching, training"

  - name: "TaleemHub (RWP)"
    dataset: "TaleemHub_DB"
    status: "active"
    region: "rawalpindi"
    description: "Rawalpindi teacher platform — roster, mentoring visits, ASER"

  - name: "Rumi AI (RWP)"
    dataset: "RUMI_DB"
    status: "active"
    region: "rawalpindi"
    description: "AI coaching, lesson plans, reading assessments for RWP"

  - name: "Muawin/Akhuwat"
    dataset: "Muawin_Akhuwat_db"
    status: "active"
    region: "muawin-akhuwat"
    description: "Muawin + Akhuwat school program — teachers, attendance, student scores"

  - name: "Zaviya"
    dataset: null
    status: "active"
    region: "zaviya"
    description: "Zaviya program — not yet migrated to BigQuery"

  - name: "MCP Audit"
    dataset: "mcp_audit"
    status: "system"
    region: null
    description: "Internal audit logging for MCP queries and feedback"

  - name: "Rawalpindi Prod"
    dataset: "rwp_proddb"
    status: "inactive"
    region: null
    description: "RWP production database mirror — use TaleemHub_DB + RUMI_DB instead"

  - name: "Balochistan"
    dataset: "bl_proddb"
    status: "inactive"
    region: null
    description: "Balochistan program — data exists but stale (last updated Sep 2025)"

  - name: "ODK Surveys"
    dataset: "odk"
    status: "inactive"
    region: null
    description: "Field survey data from ODK — ASER, TEACH, baseline/endline"
```

- [ ] **Step 2: Commit**

```bash
git add src/taleemabad_data_mcp/projects.yaml
git commit -m "feat: add project registry (projects.yaml)"
```

---

### Task 3: Create governance_mapper.py

**Files:**
- Create: `src/taleemabad_data_mcp/engine/governance_mapper.py`
- Create: `tests/test_governance_mapper.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_governance_mapper.py`:

```python
"""Tests for governance_mapper — extracts table references from rule files."""

from taleemabad_data_mcp.engine.governance_mapper import (
    extract_tables_from_text,
    get_governance_map,
)


def test_extract_dataset_dot_table():
    text = "| `tbproddb.coaching_observation` | Core record |"
    result = extract_tables_from_text(text)
    assert ("tbproddb", "coaching_observation") in result


def test_extract_multiple_tables():
    text = """
    | `tbproddb.users_user` | Base user table |
    | `tbproddb.users_teacherprofile` | Teacher profile |
    | `RUMI_DB.lesson_plans` | AI lesson plans |
    """
    result = extract_tables_from_text(text)
    assert ("tbproddb", "users_user") in result
    assert ("tbproddb", "users_teacherprofile") in result
    assert ("RUMI_DB", "lesson_plans") in result


def test_extract_from_sql():
    text = """
    FROM tbproddb.coaching_observation co
    JOIN tbproddb.coaching_teachervisit tv ON co.id = tv.observation_id
    """
    result = extract_tables_from_text(text)
    assert ("tbproddb", "coaching_observation") in result
    assert ("tbproddb", "coaching_teachervisit") in result


def test_extract_odk_tables():
    text = "| `odk.NIETE_-_ICT_-_IMPACT_ICT-ENDLINE-ASER_1-3_Test` | Grades 1-3 |"
    result = extract_tables_from_text(text)
    assert ("odk", "NIETE_-_ICT_-_IMPACT_ICT-ENDLINE-ASER_1-3_Test") in result


def test_extract_taleemhub_tables():
    text = "FROM TaleemHub_DB.mentoring_visits mv"
    result = extract_tables_from_text(text)
    assert ("TaleemHub_DB", "mentoring_visits") in result


def test_no_false_positives():
    text = "Use `is_active = 'true'` filter. The `source` column matters."
    result = extract_tables_from_text(text)
    # These are column names, not tables — should not match
    assert len(result) == 0


def test_get_governance_map_returns_dict():
    gmap = get_governance_map()
    assert isinstance(gmap, dict)
    # Should find at least coaching_observation from the observation rules
    key = ("tbproddb", "coaching_observation")
    assert key in gmap
    assert "rule_file" in gmap[key]
    assert "domain" in gmap[key]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_governance_mapper.py -v`
Expected: FAIL with ImportError

- [ ] **Step 3: Write the implementation**

Create `src/taleemabad_data_mcp/engine/governance_mapper.py`:

```python
"""Parse governance rule files to extract table references.

Scans all .md files under rules/ and extracts dataset.table references,
producing a mapping used by the dashboard to show governance coverage.
"""

from __future__ import annotations

import re
from pathlib import Path

# Datasets we recognize in table references
KNOWN_DATASETS = {
    "tbproddb", "RUMI_DB", "TaleemHub_DB", "odk",
    "Muawin_Akhuwat_db", "mcp_audit", "rwp_proddb", "bl_proddb",
}

# Pattern: dataset.table_name (with optional backticks, in markdown tables or SQL)
# Handles: `tbproddb.table_name`, FROM tbproddb.table_name, tbproddb.table_name
_TABLE_RE = re.compile(
    r"(?:`|\b)("
    + "|".join(re.escape(d) for d in KNOWN_DATASETS)
    + r")\.([A-Za-z_][A-Za-z0-9_\-]+)`?"
)

# Domain inference from file path
_DOMAIN_MAP = {
    "teachers": "teachers",
    "dimensions": "teachers",
    "lesson_plans": "lesson_plans",
    "coaching_observations": "coaching",
    "coaching_ai": "coaching_ai",
    "coaching": "coaching",
    "training": "training",
    "student_results": "student_results",
}


def _rules_dir() -> Path:
    """Return the rules directory bundled in this package."""
    return Path(__file__).parent.parent / "rules"


def _infer_domain(rule_path: Path) -> str:
    """Infer the governance domain from the rule file's directory path."""
    parts = rule_path.parts
    for part in parts:
        if part in _DOMAIN_MAP:
            return _DOMAIN_MAP[part]
    return "general"


def extract_tables_from_text(text: str) -> set[tuple[str, str]]:
    """Extract (dataset, table) tuples from markdown/SQL text.

    Returns a set of (dataset, table_name) tuples.
    """
    return {(m.group(1), m.group(2)) for m in _TABLE_RE.finditer(text)}


def get_governance_map() -> dict[tuple[str, str], dict]:
    """Scan all rule files and return a mapping of governed tables.

    Returns:
        Dict keyed by (dataset, table_name) with values:
        {
            "rule_file": "ict-islamabad/coaching_observations/observation-query-rules.md",
            "domain": "coaching",
            "region": "ict-islamabad",
        }
    """
    rules_dir = _rules_dir()
    if not rules_dir.exists():
        return {}

    result: dict[tuple[str, str], dict] = {}

    for md_file in rules_dir.rglob("*.md"):
        text = md_file.read_text(encoding="utf-8", errors="ignore")
        tables = extract_tables_from_text(text)

        if not tables:
            continue

        rel_path = md_file.relative_to(rules_dir)
        domain = _infer_domain(md_file)

        # Infer region from path (first directory component if it's a region dir)
        parts = rel_path.parts
        region = parts[0] if len(parts) > 1 and parts[0] not in (
            "bigquery.md", "caching.md", "index.md",
        ) else "general"

        for dataset, table in tables:
            key = (dataset, table)
            # First rule file wins (more specific rules are deeper in tree)
            if key not in result:
                result[key] = {
                    "rule_file": str(rel_path),
                    "domain": domain,
                    "region": region,
                }

    return result
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/test_governance_mapper.py -v`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add src/taleemabad_data_mcp/engine/governance_mapper.py tests/test_governance_mapper.py
git commit -m "feat: governance mapper — parse rule files for table references"
```

---

### Task 4: Create projects data module

**Files:**
- Create: `src/taleemabad_data_mcp/dashboard/data/projects.py`

- [ ] **Step 1: Create the data module**

```python
"""Data queries for project registry and governance coverage."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st
import yaml

from taleemabad_data_mcp.dashboard.data.client import get_bq_client, get_config
from taleemabad_data_mcp.engine.governance_mapper import get_governance_map


def _projects_yaml_path() -> Path:
    """Return path to projects.yaml."""
    return Path(__file__).parent.parent.parent / "projects.yaml"


@st.cache_data(ttl=3600)
def load_projects() -> list[dict]:
    """Load project registry from projects.yaml."""
    path = _projects_yaml_path()
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("projects", [])


@st.cache_data(ttl=3600)
def get_dataset_stats(datasets: list[str]) -> dict[str, dict]:
    """Query BigQuery __TABLES__ for table count and row count per dataset.

    Returns: {dataset: {"table_count": N, "total_rows": N}}
    """
    client = get_bq_client()
    cfg = get_config()
    result = {}

    for ds in datasets:
        try:
            sql = f"""
                SELECT
                    COUNT(*) as table_count,
                    SUM(row_count) as total_rows
                FROM `{cfg['project']}.{ds}.__TABLES__`
            """
            df = client.query(sql).to_dataframe()
            if not df.empty:
                result[ds] = {
                    "table_count": int(df.iloc[0]["table_count"]),
                    "total_rows": int(df.iloc[0]["total_rows"] or 0),
                }
        except Exception:
            result[ds] = {"table_count": 0, "total_rows": 0}

    return result


@st.cache_data(ttl=3600)
def get_all_tables(datasets: list[str]) -> pd.DataFrame:
    """Get all tables across given datasets with row count and last modified.

    Returns DataFrame with columns: dataset, table_name, row_count, last_modified
    """
    client = get_bq_client()
    cfg = get_config()
    frames = []

    for ds in datasets:
        try:
            sql = f"""
                SELECT
                    '{ds}' as dataset,
                    table_id as table_name,
                    row_count,
                    TIMESTAMP_MILLIS(last_modified_time) as last_modified
                FROM `{cfg['project']}.{ds}.__TABLES__`
                ORDER BY table_id
            """
            df = client.query(sql).to_dataframe()
            if not df.empty:
                frames.append(df)
        except Exception:
            pass

    if frames:
        return pd.concat(frames, ignore_index=True)
    return pd.DataFrame(columns=["dataset", "table_name", "row_count", "last_modified"])


@st.cache_data(ttl=3600)
def get_governance_coverage() -> dict[tuple[str, str], dict]:
    """Get the governance map (cached for dashboard)."""
    return get_governance_map()


def count_rule_files(region: str | None) -> int:
    """Count .md rule files for a given region."""
    if not region:
        return 0
    rules_dir = Path(__file__).parent.parent.parent / "rules" / region
    if not rules_dir.exists():
        return 0
    return len(list(rules_dir.rglob("*.md")))


def format_rows(n: int) -> str:
    """Format row count: 1234 -> 1.2K, 1234567 -> 1.2M."""
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)
```

- [ ] **Step 2: Commit**

```bash
git add src/taleemabad_data_mcp/dashboard/data/projects.py
git commit -m "feat: project data module — registry loader + BQ stats queries"
```

---

### Task 5: Add Project Status to Overview page

**Files:**
- Modify: `src/taleemabad_data_mcp/dashboard/pages/0_Overview.py`

- [ ] **Step 1: Add imports at top of file** (after existing imports, around line 22)

Add after the existing import block:

```python
from taleemabad_data_mcp.dashboard.data.projects import (
    load_projects,
    get_dataset_stats,
    get_governance_coverage,
    count_rule_files,
    format_rows,
)
```

- [ ] **Step 2: Add Project Status section** (insert after the KPI cards section, before `# ROW 2: Activity trend`)

Insert before line `# ======================================================================` / `# ROW 2`:

```python
# ======================================================================
# ROW 1.5: Project Status
# ======================================================================
st.markdown("")
st.markdown('<div class="section-header">Project Status</div>', unsafe_allow_html=True)

projects = load_projects()
datasets_to_query = [p["dataset"] for p in projects if p.get("dataset")]
ds_stats = get_dataset_stats(datasets_to_query)
gov_map = get_governance_coverage()

# Count governed tables per dataset
gov_by_dataset: dict[str, int] = {}
for (ds, _tbl), _info in gov_map.items():
    gov_by_dataset[ds] = gov_by_dataset.get(ds, 0) + 1

STATUS_BADGE = {
    "active": '<span style="color:#22C55E;font-weight:600;">Active</span>',
    "inactive": '<span style="color:#94A3B8;">Inactive</span>',
    "system": '<span style="color:#3B82F6;">System</span>',
}

rows_html = ""
active_count = sum(1 for p in projects if p["status"] == "active")
inactive_count = sum(1 for p in projects if p["status"] == "inactive")

for p in projects:
    ds = p.get("dataset")
    stats = ds_stats.get(ds, {}) if ds else {}
    tbl_count = stats.get("table_count", 0)
    total_rows = stats.get("total_rows", 0)
    rules = count_rule_files(p.get("region"))
    governed = gov_by_dataset.get(ds, 0) if ds else 0

    if p["status"] == "active" and not ds:
        coverage = '<span style="color:#EF4444;font-weight:600;">Not migrated</span>'
    elif p["status"] == "inactive":
        coverage = '<span style="color:#94A3B8;">—</span>'
    elif p["status"] == "system":
        coverage = '<span style="color:#3B82F6;">System</span>'
    elif tbl_count > 0 and governed > 0:
        pct = governed / tbl_count * 100
        bar_w = min(pct * 2, 100)
        coverage = (
            f'<div style="display:flex;align-items:center;gap:6px;">'
            f'<div style="flex:1;background:#E2E8F0;border-radius:4px;height:8px;">'
            f'<div style="width:{bar_w}%;background:#22C55E;border-radius:4px;height:8px;"></div>'
            f'</div><span style="font-size:0.8rem;">{governed}/{tbl_count}</span></div>'
        )
    elif p["status"] == "active" and governed == 0:
        coverage = '<span style="color:#EAB308;font-weight:600;">No rules</span>'
    else:
        coverage = "—"

    badge = STATUS_BADGE.get(p["status"], p["status"])
    ds_display = ds or "—"
    tbl_display = str(tbl_count) if ds else "—"
    rows_display = format_rows(total_rows) if ds and total_rows else "—"

    rows_html += (
        f"<tr>"
        f'<td style="font-weight:500;">{p["name"]}</td>'
        f"<td><code>{ds_display}</code></td>"
        f"<td>{badge}</td>"
        f"<td>{tbl_display}</td>"
        f"<td>{rows_display}</td>"
        f"<td>{coverage}</td>"
        f"</tr>"
    )

st.markdown(
    f'<div style="display:flex;gap:12px;margin-bottom:8px;">'
    f'<span style="color:#22C55E;font-weight:600;">{active_count} active</span>'
    f'<span style="color:#94A3B8;">{inactive_count} inactive</span>'
    f'</div>'
    f'<table style="width:100%;border-collapse:collapse;font-size:0.85rem;">'
    f'<thead><tr style="border-bottom:2px solid #E2E8F0;text-align:left;">'
    f'<th style="padding:6px 8px;">Project</th>'
    f'<th style="padding:6px 8px;">Dataset</th>'
    f'<th style="padding:6px 8px;">Status</th>'
    f'<th style="padding:6px 8px;">Tables</th>'
    f'<th style="padding:6px 8px;">Rows</th>'
    f'<th style="padding:6px 8px;min-width:120px;">Coverage</th>'
    f'</tr></thead><tbody>'
    f'{rows_html}'
    f'</tbody></table>',
    unsafe_allow_html=True,
)

st.markdown("")
```

- [ ] **Step 3: Add governance action items** (insert in the action items section, around line 524-570, after the existing action checks)

Add before `# All clear`:

```python
# Check for active projects with no governance rules
for p in projects:
    if p["status"] == "active" and p.get("dataset"):
        ds = p["dataset"]
        governed = gov_by_dataset.get(ds, 0)
        if governed == 0:
            tbl_count = ds_stats.get(ds, {}).get("table_count", 0)
            actions.append({
                "icon": "&#128220;",  # document
                "color": COLORS["warning"],
                "title": f'{p["name"]} has no governance rules',
                "detail": f"<strong>{tbl_count} tables</strong> in {ds} but none are governed. "
                          "Add rule files to enable governed queries for this project.",
                "priority": "medium",
            })
    if p["status"] == "active" and not p.get("dataset"):
        actions.append({
            "icon": "&#128293;",  # fire
            "color": COLORS["accent"],
            "title": f'{p["name"]} not migrated to BigQuery',
            "detail": "This project has no dataset yet. Migrate data to BigQuery to enable querying.",
            "priority": "low",
        })
```

- [ ] **Step 4: Test manually**

Run: `uv run python -m taleemabad_data_mcp dashboard`
Check: Overview page shows Project Status table between KPIs and Activity Trend.

- [ ] **Step 5: Commit**

```bash
git add src/taleemabad_data_mcp/dashboard/pages/0_Overview.py
git commit -m "feat: add Project Status section to Overview dashboard page"
```

---

### Task 6: Create Governance tab

**Files:**
- Create: `src/taleemabad_data_mcp/dashboard/pages/6_Governance.py`

- [ ] **Step 1: Create the Governance page**

```python
"""Governance — table-level rule coverage across all active projects."""

import sys as _sys
from pathlib import Path as _Path
_src = str(_Path(__file__).parent.parent.parent.parent)
if _src not in _sys.path:
    _sys.path.insert(0, _src)

import pandas as pd
import streamlit as st

from taleemabad_data_mcp.dashboard.data.projects import (
    load_projects,
    get_all_tables,
    get_governance_coverage,
    format_rows,
)

# -- CSS (consistent with Overview) --
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Fira+Sans:wght@300;400;500;600;700&display=swap');
    .stApp { font-family: 'Fira Sans', system-ui, sans-serif; }
    .block-container { padding-top: 1.2rem; }
    .kpi-card {
        background: white; border: 1px solid #E2E8F0; border-radius: 12px;
        padding: 16px 18px; box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        text-align: center; min-height: 80px;
    }
    .kpi-card .kpi-label { font-weight: 500; color: #64748B; font-size: 0.82rem; }
    .kpi-card .kpi-value { font-size: 1.55rem; font-weight: 700; color: #1E293B; margin: 4px 0 0; }
    .section-header {
        font-size: 0.95rem; font-weight: 600; color: #1E293B;
        margin: 0.6rem 0 0.3rem 0; padding-bottom: 0.25rem;
        border-bottom: 2px solid #3B82F6;
    }
</style>
""", unsafe_allow_html=True)

st.markdown(
    '<h2 style="margin-bottom:0;color:#1E293B;">Governance Coverage</h2>'
    '<p style="color:#64748B;margin-top:0;margin-bottom:0.8rem;">'
    "Which tables are governed by query rules — and which are gaps</p>",
    unsafe_allow_html=True,
)

# -- Load data --
projects = load_projects()
active_datasets = [p["dataset"] for p in projects if p.get("dataset") and p["status"] == "active"]
all_tables_df = get_all_tables(active_datasets)
gov_map = get_governance_coverage()

if all_tables_df.empty:
    st.info("No table data available. Check BigQuery connectivity.")
    st.stop()

# -- Add governance info to each table --
all_tables_df["governed"] = all_tables_df.apply(
    lambda r: (r["dataset"], r["table_name"]) in gov_map, axis=1
)
all_tables_df["rule_file"] = all_tables_df.apply(
    lambda r: gov_map.get((r["dataset"], r["table_name"]), {}).get("rule_file", ""),
    axis=1,
)
all_tables_df["domain"] = all_tables_df.apply(
    lambda r: gov_map.get((r["dataset"], r["table_name"]), {}).get("domain", ""),
    axis=1,
)

total = len(all_tables_df)
governed = int(all_tables_df["governed"].sum())
ungoverned = total - governed
coverage_pct = governed / total * 100 if total > 0 else 0

# -- KPI row --
c1, c2, c3, c4 = st.columns(4)
c1.markdown(
    f'<div class="kpi-card"><div class="kpi-label">Total Tables</div>'
    f'<div class="kpi-value">{total:,}</div></div>',
    unsafe_allow_html=True,
)
c2.markdown(
    f'<div class="kpi-card"><div class="kpi-label">Governed</div>'
    f'<div class="kpi-value" style="color:#22C55E;">{governed}</div></div>',
    unsafe_allow_html=True,
)
c3.markdown(
    f'<div class="kpi-card"><div class="kpi-label">Ungoverned</div>'
    f'<div class="kpi-value" style="color:#EF4444;">{ungoverned}</div></div>',
    unsafe_allow_html=True,
)
c4.markdown(
    f'<div class="kpi-card"><div class="kpi-label">Coverage</div>'
    f'<div class="kpi-value">{coverage_pct:.1f}%</div></div>',
    unsafe_allow_html=True,
)

st.markdown("")

# -- Filters --
project_names = {p["dataset"]: p["name"] for p in projects if p.get("dataset")}
fcol1, fcol2 = st.columns(2)
with fcol1:
    selected_ds = st.selectbox(
        "Filter by project",
        ["All"] + active_datasets,
        format_func=lambda x: "All projects" if x == "All" else project_names.get(x, x),
    )
with fcol2:
    gov_filter = st.selectbox("Filter by status", ["All", "Governed only", "Ungoverned only"])

# Apply filters
filtered = all_tables_df.copy()
if selected_ds != "All":
    filtered = filtered[filtered["dataset"] == selected_ds]
if gov_filter == "Governed only":
    filtered = filtered[filtered["governed"]]
elif gov_filter == "Ungoverned only":
    filtered = filtered[~filtered["governed"]]

# -- Summary bar --
f_total = len(filtered)
f_governed = int(filtered["governed"].sum())
st.markdown(
    f'<div style="background:#F1F5F9;border-radius:8px;padding:10px 16px;'
    f'margin-bottom:12px;font-size:0.85rem;">'
    f'Showing <strong>{f_total}</strong> tables'
    f' — <span style="color:#22C55E;font-weight:600;">{f_governed} governed</span>'
    f' / <span style="color:#EF4444;">{f_total - f_governed} ungoverned</span></div>',
    unsafe_allow_html=True,
)

# -- Table --
display = filtered[["dataset", "table_name", "row_count", "governed", "rule_file", "domain"]].copy()
display["row_count"] = display["row_count"].apply(lambda x: format_rows(int(x)) if pd.notna(x) else "—")
display["governed"] = display["governed"].apply(lambda x: "Yes" if x else "No")
display.columns = ["Dataset", "Table", "Rows", "Governed", "Rule File", "Domain"]

st.dataframe(
    display,
    use_container_width=True,
    height=600,
    column_config={
        "Governed": st.column_config.TextColumn(
            width="small",
        ),
        "Rule File": st.column_config.TextColumn(
            width="medium",
        ),
    },
)
```

- [ ] **Step 2: Commit**

```bash
git add src/taleemabad_data_mcp/dashboard/pages/6_Governance.py
git commit -m "feat: add Governance dashboard tab — table-level rule coverage"
```

---

### Task 7: Register Governance page in app.py

**Files:**
- Modify: `src/taleemabad_data_mcp/dashboard/app.py:46-53`

- [ ] **Step 1: Add Governance to navigation**

Change the `pg = st.navigation([...])` block to include the new page:

```python
pg = st.navigation([
    st.Page(pages_dir / "0_Overview.py", title="Overview", default=True),
    st.Page(pages_dir / "1_Query_Analytics.py", title="Query Analytics"),
    st.Page(pages_dir / "2_feedback.py", title="Feedback"),
    st.Page(pages_dir / "3_cost.py", title="Cost"),
    st.Page(pages_dir / "4_errors.py", title="Errors"),
    st.Page(pages_dir / "5_freshness.py", title="Freshness"),
    st.Page(pages_dir / "6_Governance.py", title="Governance"),
])
```

- [ ] **Step 2: Commit**

```bash
git add src/taleemabad_data_mcp/dashboard/app.py
git commit -m "feat: register Governance page in dashboard navigation"
```

---

### Task 8: Final integration test and version bump

- [ ] **Step 1: Run all tests**

```bash
uv run pytest -v
```

Expected: all pass.

- [ ] **Step 2: Test dashboard manually**

```bash
uv run python -m taleemabad_data_mcp dashboard
```

Check:
1. Overview page: Project Status table visible with 9 projects, coverage bars
2. Overview page: Action items include governance gaps (Muawin/Akhuwat, Zaviya)
3. Governance tab: KPIs show total/governed/ungoverned/coverage
4. Governance tab: filters work (by project, by governed status)
5. Governance tab: table shows governed=Yes/No with rule file and domain

- [ ] **Step 3: Bump version and push**

```bash
python -m taleemabad_data_mcp bump --minor
git add -A
git commit -m "chore: bump version to v0.12.0"
git tag v0.12.0
git push origin master
git push origin master:main
git push origin v0.12.0
```
