# Project Governance Dashboard Design

## Problem

There are 17 datasets in BigQuery across 9+ projects. Only 3 projects (ICT, TaleemHub, Rumi) have governance rules. Nobody can answer:
- "What percentage of our data is governed?"
- "Which tables can I query through governance?"
- "Which projects are active vs inactive?"
- "What gaps need rules?"

## Solution

Two things:
1. **Project Registry** — a config file listing all projects, their datasets, and status
2. **Two Dashboard Tabs** — Project Overview + Table-Level Governance

## Project Registry

A YAML file at `src/taleemabad_data_mcp/projects.yaml`:

```yaml
projects:
  - name: "ICT/Islamabad"
    dataset: "tbproddb"
    status: "active"        # active | inactive | system
    region: "ict-islamabad"  # maps to rules/<region>/
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

**Adding a new project:** Add an entry to this YAML file. No code changes needed.

## Tab 1: Project Overview

Shows all projects in a single table with live BigQuery stats.

### Data Sources
- **Static:** `projects.yaml` for name, status, region, description
- **Live from BigQuery:** table count, row count (from `__TABLES__` metadata)
- **Static:** rule file count (parsed from `rules/<region>/` directory)

### Columns

| Column | Source | Description |
|--------|--------|-------------|
| Project | projects.yaml | Project name |
| Dataset | projects.yaml | BigQuery dataset name, or "Not migrated" |
| Status | projects.yaml | Active (green) / Inactive (grey) / System (blue) |
| Tables | BigQuery `__TABLES__` | Number of tables in the dataset |
| Rows | BigQuery `__TABLES__` | Total row count across all tables |
| Rule Files | Filesystem scan | Count of `.md` files in `rules/<region>/` |
| Governed Tables | Rule parser | Count of distinct tables referenced in rule files |
| Coverage | Computed | `governed_tables / total_tables` as percentage |

### Visual
- Color-coded status badges
- Coverage shown as progress bar (e.g., 12/473 = 2.5%)
- Active projects with 0% coverage highlighted in yellow
- Zaviya row shows "Not migrated" with distinct styling

### Refresh
- BigQuery stats cached for 1 hour (dashboard already has caching)
- Rule counts computed at dashboard startup (static files, fast)

## Tab 2: Table-Level Governance

For **active projects only**, shows every table and whether it's referenced in a governance rule.

### How Tables Are Mapped to Rules

Parse each rule `.md` file and extract table references using patterns:
- `` `dataset.table_name` `` (backtick-wrapped BigQuery references)
- `FROM dataset.table_name` / `JOIN dataset.table_name`
- Table names in markdown tables (the "Key Tables" sections in rule files)

This produces a mapping: `{table_name: [rule_file, domain]}`.

### Implementation

A Python module `src/taleemabad_data_mcp/engine/governance_mapper.py` that:
1. Reads all rule files from `src/taleemabad_data_mcp/rules/`
2. Extracts table references via regex
3. Returns a dict: `{dataset.table: {rule_file, domain, region}}`

### Columns

| Column | Source | Description |
|--------|--------|-------------|
| Dataset | BigQuery | Dataset name |
| Table | BigQuery `__TABLES__` | Table name |
| Rows | BigQuery `__TABLES__` | Row count |
| Last Modified | BigQuery `__TABLES__` | Timestamp |
| Governed | governance_mapper | Yes (green) / No (red) |
| Rule File | governance_mapper | Which `.md` file references this table |
| Domain | governance_mapper | teachers, coaching, training, lesson_plans, etc. |

### Filters
- Filter by project/dataset (dropdown)
- Filter by governed status (All / Governed only / Ungoverned only)
- Sort by any column

### Visual
- Governed tables: green checkmark
- Ungoverned tables: red X
- Summary bar at top: "42 of 473 tables governed (8.9%)" with progress bar

## What This Does NOT Include

- Rule creation workflow (manual — edit `.md` files)
- Automated rule suggestions
- Table freshness monitoring (already exists in the Freshness dashboard page)
- Query-level governance validation (future — would need server-side enforcement)

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `src/taleemabad_data_mcp/projects.yaml` | Create | Project registry |
| `src/taleemabad_data_mcp/engine/governance_mapper.py` | Create | Parse rules → table mapping |
| `src/taleemabad_data_mcp/dashboard/pages/7_Projects.py` | Create | Tab 1: Project Overview |
| `src/taleemabad_data_mcp/dashboard/pages/8_Governance.py` | Create | Tab 2: Table-Level Governance |
| `src/taleemabad_data_mcp/dashboard/data/projects.py` | Create | BigQuery queries for project stats |

## Adding a New Project (User Process)

1. Edit `src/taleemabad_data_mcp/projects.yaml` — add the entry
2. If the project has data in BigQuery, add the dataset to `BIGQUERY_DATASETS` env var
3. If you want governance rules, create `rules/<region>/` and add rule files
4. Run `python -m taleemabad_data_mcp bump` and push
5. Dashboard picks it up automatically on next load
