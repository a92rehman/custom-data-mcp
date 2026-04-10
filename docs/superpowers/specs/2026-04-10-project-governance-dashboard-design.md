# Project Governance Dashboard Design

## Problem

There are 17 datasets in BigQuery across 9+ projects. Only 3 projects (ICT, TaleemHub, Rumi) have governance rules. Nobody can answer:
- "What percentage of our data is governed?"
- "Which tables can I query through governance?"
- "Which projects are active vs inactive?"
- "What gaps need rules?"

## Solution

Three things:
1. **Project Registry** — a YAML config listing all projects and their status
2. **Project Status section on Overview page** — compact table showing all projects at a glance
3. **New "Governance" tab** — detailed table-level view of which tables are governed

## Project Registry

A YAML file at `src/taleemabad_data_mcp/projects.yaml`:

```yaml
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

**Adding a new project:** Add one entry to this YAML file. No code changes needed.

## Overview Page: Project Status Section

Added to the existing `0_Overview.py` between the KPI cards (Row 1) and the Activity Trend (Row 2).

### Layout

A compact table inside a section box (matching the existing design system):

```
┌─────────────────────────────────────────────────────────────────┐
│  Project Status                                    6 active │ 3 inactive  │
├──────────────────┬──────────┬────────┬────────┬──────┬──────────┤
│ Project          │ Dataset  │ Status │ Tables │ Rows │ Coverage │
├──────────────────┼──────────┼────────┼────────┼──────┼──────────┤
│ ICT/Islamabad    │ tbproddb │ 🟢     │ 473    │ 451M │ ████░ 3% │
│ TaleemHub (RWP)  │ TaleemHu │ 🟢     │ 62     │ 69K  │ ██░░ 13% │
│ Rumi AI (RWP)    │ RUMI_DB  │ 🟢     │ 72     │ 154K │ ██░░ 8%  │
│ Muawin/Akhuwat   │ Muawin_A │ 🟡     │ 6      │ 41K  │ ░░░░ 0%  │
│ Zaviya           │ —        │ 🔴     │ —      │ —    │ N/A      │
│ MCP Audit        │ mcp_audi │ 🔵     │ 2      │ 104  │ System   │
│ Rawalpindi Prod  │ rwp_prod │ ⚪     │ 260    │ 550K │ Inactive │
│ Balochistan      │ bl_prodd │ ⚪     │ 222    │ 2.6M │ Inactive │
│ ODK Surveys      │ odk      │ ⚪     │ 52     │ 38K  │ Inactive │
└──────────────────┴──────────┴────────┴────────┴──────┴──────────┘
```

### Status Colors
- 🟢 Active + has rules (governed)
- 🟡 Active + no rules (gap — needs attention)
- 🔴 Active + not migrated (Zaviya)
- 🔵 System
- ⚪ Inactive

### Data Sources
- Static: `projects.yaml` for name, dataset, status, region
- Live BigQuery: `__TABLES__` metadata for table count and row count (cached 1hr)
- Filesystem: count `.md` files in `rules/<region>/` for rule coverage
- Governance mapper: count governed tables per dataset

### Integration with Existing Action Items
Add governance-related action items to the existing Row 5 action items list:
- Active project with 0% coverage → yellow warning: "Muawin/Akhuwat has 6 tables but no governance rules"
- Zaviya not migrated → info: "Zaviya has no BigQuery dataset yet"

## New Tab: Governance (Detailed Table-Level View)

A new page at `src/taleemabad_data_mcp/dashboard/pages/6_Governance.py`.

### How Tables Are Mapped to Rules

A Python module `governance_mapper.py` parses rule files and extracts table references:
- `` `tbproddb.table_name` `` (backtick-wrapped BigQuery references)
- `FROM tbproddb.table_name` / `JOIN tbproddb.table_name`
- Table names in "Key Tables" markdown tables in rule files

Returns: `{dataset.table: {rule_file, domain, region}}`

### Layout

**Top: Summary KPIs**
```
┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ Total Tables │  │  Governed    │  │ Ungoverned   │  │  Coverage    │
│    665       │  │    ~30       │  │    ~635      │  │    4.5%      │
└──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘
```

**Filters**
- Dropdown: filter by project/dataset
- Toggle: All / Governed only / Ungoverned only

**Table**

| Dataset | Table | Rows | Last Modified | Governed | Rule File | Domain |
|---------|-------|------|---------------|----------|-----------|--------|
| tbproddb | coaching_observation | 6,697 | Apr 9 | ✅ | observation-query-rules.md | Coaching |
| tbproddb | users_user | 96,731 | Apr 9 | ✅ | teacher-query-rules.md | Teachers |
| tbproddb | community_post | 5,000 | Apr 8 | ❌ | — | — |
| Muawin_Akhuwat_db | teachers | 866 | Apr 8 | ❌ | — | — |

### Visual
- Governed: green checkmark ✅
- Ungoverned: red X ❌
- Sortable by any column
- Row count formatted (K, M)

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `src/taleemabad_data_mcp/projects.yaml` | Create | Project registry |
| `src/taleemabad_data_mcp/engine/governance_mapper.py` | Create | Parse rules → table mapping |
| `src/taleemabad_data_mcp/dashboard/data/projects.py` | Create | BigQuery queries for project stats |
| `src/taleemabad_data_mcp/dashboard/pages/0_Overview.py` | Modify | Add Project Status section after KPI row |
| `src/taleemabad_data_mcp/dashboard/pages/6_Governance.py` | Create | New tab: table-level governance detail |

## What This Does NOT Include

- Rule creation workflow (manual — edit `.md` files)
- Automated rule suggestions
- Table freshness monitoring (already in Freshness tab)
- Query-level governance validation (future)

## Adding a New Project (User Process)

1. Edit `src/taleemabad_data_mcp/projects.yaml` — add the entry
2. If the project has data in BigQuery, add the dataset to `BIGQUERY_DATASETS` env var
3. If you want governance rules, create `rules/<region>/` and add rule files
4. Run `python -m taleemabad_data_mcp bump` and push
5. Dashboard picks it up on next load
