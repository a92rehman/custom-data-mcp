# Semantic Layer Tools and Metric Definition Patterns: Deep Research Report

**Date:** 2026-04-04
**Purpose:** Inform the design of a Data Governance MCP server that enforces governed data access through pre-approved metric definitions stored as YAML.

---

## Table of Contents

1. [Semantic Layer Tools: How They Define Metrics](#1-semantic-layer-tools-how-they-define-metrics)
2. [YAML Schema Patterns for Metric Definitions](#2-yaml-schema-patterns-for-metric-definitions)
3. [Bronze/Silver/Gold Medallion Architecture](#3-bronzesilvergold-medallion-architecture)
4. [Rule-as-Code / Policy-as-Code for Data](#4-rule-as-code--policy-as-code-for-data)
5. [Metric Lineage Patterns](#5-metric-lineage-patterns)
6. [Architectural Recommendations for the MCP Server](#6-architectural-recommendations-for-the-mcp-server)
7. [Sources](#7-sources)

---

## 1. Semantic Layer Tools: How They Define Metrics

### 1.1 dbt Metrics Layer / MetricFlow

dbt's semantic layer is built on MetricFlow. It uses a two-tier YAML structure: **semantic models** define the raw building blocks (entities, dimensions, measures), and **metrics** compose those building blocks into business-facing KPIs.

**Core Architecture:**
- **Semantic Models** = the data source definition (maps to a dbt model/table)
- **Entities** = join keys / traversal paths between semantic models
- **Dimensions** = slice/dice/group-by columns (categorical or time)
- **Measures** = aggregatable columns with a defined aggregation function
- **Metrics** = business-facing calculations composed from measures and other metrics

**Metric Types in MetricFlow:**

| Type | Description | Key Parameters |
|------|-------------|----------------|
| **Simple** | Direct reference to a single measure | `measure` |
| **Ratio** | Division of two metrics | `numerator`, `denominator` |
| **Cumulative** | Running aggregate over time window | `measure`, `window`, `grain_to_date` |
| **Derived** | Expression combining other metrics | `expr`, `metrics` (with aliases, offsets) |
| **Conversion** | Funnel/conversion calculations | `base_metric`, `conversion_metric`, `entity`, `window` |

**Complete Semantic Model YAML:**

```yaml
semantic_models:
  - name: orders
    defaults:
      agg_time_dimension: ordered_at
    description: |
      Order fact table. This table is at the order grain with one row per order.
    model: ref('stg_orders')
    entities:
      - name: order_id
        type: primary
      - name: location
        type: foreign
        expr: location_id
      - name: customer
        type: foreign
        expr: customer_id
    dimensions:
      - name: ordered_at
        expr: date_trunc('day', ordered_at)
        type: time
        type_params:
          time_granularity: day
      - name: is_large_order
        type: categorical
        expr: case when order_total > 50 then true else false end
    measures:
      - name: order_total
        description: The total revenue for each order.
        agg: sum
      - name: order_count
        description: The count of individual orders.
        expr: 1
        agg: sum
      - name: tax_paid
        description: The total tax paid on each order.
        agg: sum
```

**Metric Definition Examples:**

```yaml
metrics:
  # Simple metric -- wraps a single measure
  - name: customers
    description: Count of customers
    type: simple
    label: Count of customers
    type_params:
      measure: customers

  # Ratio metric -- numerator / denominator
  - name: food_revenue_pct
    description: The % of order revenue from food.
    label: Food Revenue %
    type: ratio
    type_params:
      numerator: food_revenue
      denominator: revenue

  # Cumulative metric -- running total with window
  - name: cumulative_revenue
    description: The cumulative revenue for all orders.
    label: Cumulative Revenue (All Time)
    type: cumulative
    type_params:
      measure: revenue

  # Derived metric -- expression over other metrics with time offsets
  - name: revenue_growth_mom
    description: Percentage growth of revenue compared to 1 month ago.
    type: derived
    label: Revenue Growth % M/M
    type_params:
      expr: (current_revenue - revenue_prev_month) * 100 / revenue_prev_month
      metrics:
        - name: revenue
          alias: current_revenue
        - name: revenue
          offset_window: 1 month
          alias: revenue_prev_month
```

**Key Fields in dbt Metric Definitions:**
- `name` -- unique identifier
- `description` -- human-readable explanation
- `type` -- simple, ratio, cumulative, derived, conversion
- `label` -- display name for BI tools
- `type_params` -- type-specific configuration
- `filter` -- Jinja-based filter expressions using `{{ Dimension(...) }}`, `{{ TimeDimension(...) }}`, `{{ Entity(...) }}`

### 1.2 Cube.js Semantic Layer

Cube uses a different conceptual model: **Cubes** (data entities) and **Views** (consumer-facing facades).

**Core Concepts:**
- **Cubes** = business entities (orders, users, products) containing measures, dimensions, joins
- **Views** = read-only facades that compose cubes into consumer-ready data products
- **Measures** = aggregated values (sum, count, avg, min, max, count_distinct, etc.)
- **Dimensions** = descriptive attributes for grouping/filtering
- **Joins** = relationships between cubes (one_to_one, one_to_many, many_to_one)
- **Pre-aggregations** = materialized cache layers for performance

**Cube Definition (YAML):**

```yaml
cubes:
  - name: orders
    sql_table: public.orders

    measures:
      - name: count
        type: count
      - name: total_amount
        sql: amount
        type: sum
      - name: average_order_value
        sql: amount
        type: avg

    dimensions:
      - name: id
        sql: id
        type: number
        primary_key: true
      - name: status
        sql: status
        type: string
      - name: created_at
        sql: created_at
        type: time

    joins:
      - name: users
        relationship: many_to_one
        sql: "{CUBE}.user_id = {users.id}"

    pre_aggregations:
      - name: main
        measures:
          - count
          - total_amount
        dimensions:
          - status
        time_dimension: created_at
        granularity: day
```

**View Definition (Metrics-First Approach):**

```yaml
views:
  - name: average_order_value
    cubes:
      - join_path: orders
        includes:
          - average_order_value   # the measure
          - status                # dimension for grouping
          - created_at            # time dimension
      - join_path: orders.users
        prefix: true
        includes:
          - city
          - age
          - gender
```

**Key Distinction:** Cube recommends two design approaches:
1. **Entity-first** -- views built around a business entity with multiple measures and dimensions
2. **Metrics-first** -- one view per metric, containing that metric's measure plus all relevant dimensions

The metrics-first approach is closer to what a governed MCP server would use, where each metric is a self-contained, pre-approved data product.

### 1.3 Looker LookML

LookML uses its own DSL (not YAML) structured around **Models**, **Explores**, **Views**, **Dimensions**, and **Measures**.

```lookml
view: orders {
  sql_table_name: public.orders ;;

  dimension: order_id {
    primary_key: yes
    type: number
    sql: ${TABLE}.id ;;
  }

  dimension: status {
    type: string
    sql: ${TABLE}.status ;;
  }

  dimension_group: created {
    type: time
    timeframes: [date, week, month, quarter, year]
    sql: ${TABLE}.created_at ;;
  }

  measure: total_sales {
    type: sum
    sql: ${TABLE}.sales_amount ;;
    value_format_name: usd
  }

  measure: order_count {
    type: count
    sql: ${TABLE}.id ;;
  }

  measure: avg_order {
    type: average
    sql: ${sales_price} ;;
    value_format_name: usd
  }

  measure: profit_margin {
    type: number
    sql: ${total_profit} / NULLIF(${total_sales}, 0) ;;
    value_format_name: percent_2
  }
}
```

**Key Characteristics:**
- Dimensions and measures live within views (not separate metric files)
- Calculated metrics reference other measures using `${measure_name}` syntax
- `dimension_group` with `type: time` auto-generates multiple time grain fields
- Strong typing with format specifications (`value_format_name`)

### 1.4 AtScale

AtScale presents a GUI-driven semantic layer using **virtual OLAP cubes**. Key concepts:
- Metrics are defined as measures within virtual cubes
- Supports semi-additive measures (First Non-Empty, Last Non-Empty)
- KPIs, measures, and calculated fields are defined once and reused across tools
- Compatible with Excel, Power BI, and Tableau via MDX/DAX
- Not YAML-based -- uses a visual Design Center

### 1.5 Comparison Summary

| Feature | dbt/MetricFlow | Cube.js | LookML | AtScale |
|---------|----------------|---------|--------|---------|
| **Config Format** | YAML | YAML or JS | LookML DSL | GUI |
| **Metric Composition** | Metrics reference measures; derived metrics reference metrics | Views compose cubes | Measures reference other measures | Virtual cube builder |
| **Time Grains** | `type_params.time_granularity` | `granularity` on time dimensions | `dimension_group` timeframes | GUI setting |
| **Filters** | Jinja templates | SQL expressions | sql parameter | GUI filters |
| **Dependencies** | Derived metrics with `metrics` list | Views with `join_path` | `${measure}` references | Cube relationships |
| **Version Control** | Git-native YAML | Git-native YAML/JS | Git-native LookML | Proprietary |
| **Best For** | Data teams using dbt | API-first analytics | Google Cloud/Looker shops | Enterprise BI |

---

## 2. YAML Schema Patterns for Metric Definitions

### 2.1 Universal Fields Across All Tools

Every semantic layer tool includes these core fields in metric definitions:

```yaml
# Universal metric definition schema
metric:
  name: string            # Unique identifier (snake_case)
  label: string           # Human-readable display name
  description: string     # Business context and meaning
  type: string            # Metric type (simple, derived, ratio, etc.)
  owner: string           # Team or person responsible
  tags: list[string]      # Categorization labels

  # Source definition
  source:
    model: string         # Source table or model reference
    schema: string        # Database schema
    database: string      # Database/catalog

  # Calculation
  calculation:
    aggregation: string   # sum, count, avg, min, max, count_distinct
    expression: string    # SQL expression or formula
    filters: list         # Pre-applied filters

  # Dimensions (group-by fields)
  dimensions: list
    - name: string
      type: string        # categorical, time, boolean
      expression: string  # SQL or column reference

  # Time configuration
  time:
    primary_time_dimension: string
    granularities: list   # day, week, month, quarter, year
    window: string        # For cumulative metrics
```

### 2.2 Handling Metric Dependencies

Tools use different patterns for metrics built from other metrics:

**Pattern A: dbt Derived Metrics (Expression + Metric References)**
```yaml
metrics:
  - name: profit_margin
    type: derived
    type_params:
      expr: (revenue - costs) / revenue
      metrics:
        - name: total_revenue
          alias: revenue
        - name: total_costs
          alias: costs
```

**Pattern B: Cube.js View Composition**
```yaml
views:
  - name: profit_analysis
    cubes:
      - join_path: revenue_cube
        includes: [total_revenue]
      - join_path: cost_cube
        includes: [total_costs]
```

**Pattern C: LookML Cross-Measure References**
```lookml
measure: profit_margin {
  type: number
  sql: (${total_revenue} - ${total_costs}) / NULLIF(${total_revenue}, 0) ;;
}
```

### 2.3 Handling Metric Versioning

No tool has native metric versioning built into its schema. The standard industry patterns are:

1. **Git-based versioning** -- metric YAML files live in version control; changes are tracked through commits and pull requests
2. **Naming conventions** -- `revenue_v2`, `revenue_2024` for breaking changes
3. **Deprecation flags** -- custom metadata fields:

```yaml
metrics:
  - name: total_revenue
    meta:
      version: "2.1"
      deprecated: false
      deprecated_by: null        # replacement metric name
      effective_date: "2025-01-01"
      sunset_date: null
      change_log:
        - date: "2025-01-01"
          change: "Added tax exclusion filter"
          author: "data-team"
          pr: "#234"
```

### 2.4 Proposed Governed Metric Schema for MCP Server

Based on patterns across all tools, here is a recommended schema that combines the best elements:

```yaml
# ============================================================
# Governed Metric Definition Schema v1.0
# For use with Data Governance MCP Server
# ============================================================

metric:
  # --- Identity ---
  name: monthly_active_students
  label: "Monthly Active Students"
  description: |
    Count of unique students who completed at least one lesson
    in the given calendar month.
  version: "1.0"
  status: approved          # draft | in_review | approved | deprecated
  owner: analytics-team
  tags: [engagement, students, kpi]

  # --- Data Tier ---
  tier: gold                # bronze | silver | gold
  access_level: public      # public | internal | restricted | confidential

  # --- Source ---
  source:
    model: ref('fct_lesson_completions')
    database: analytics
    schema: gold
    primary_entity: student_id
    primary_time_dimension: completed_at

  # --- Calculation ---
  type: simple              # simple | ratio | cumulative | derived
  calculation:
    aggregation: count_distinct
    expression: student_id
    filters:
      - dimension: lesson_status
        operator: equals
        value: "completed"

  # --- Dimensions (approved slice-and-dice fields) ---
  dimensions:
    - name: grade_level
      type: categorical
      column: grade
      allowed_values: ["K", "1", "2", "3", "4", "5"]
    - name: subject
      type: categorical
      column: subject_name
    - name: school_district
      type: categorical
      column: district_id
    - name: completed_at
      type: time
      column: completed_at
      granularities: [day, week, month, quarter, year]

  # --- Time Behavior ---
  time:
    default_granularity: month
    supported_granularities: [day, week, month, quarter, year]
    window: null              # for cumulative: "30 days", "1 year"
    grain_to_date: null       # for cumulative: "month", "year"

  # --- Dependencies (for derived/ratio metrics) ---
  depends_on: []
  # Example for derived metric:
  # depends_on:
  #   - metric: total_revenue
  #     alias: revenue
  #   - metric: total_students
  #     alias: students

  # --- Lineage ---
  lineage:
    upstream_tables:
      - database: raw
        schema: bronze
        table: lesson_events
      - database: analytics
        schema: silver
        table: stg_lesson_completions
    transformation_steps:
      - "Bronze: Raw lesson events ingested from API"
      - "Silver: Deduplication, null handling, status validation"
      - "Gold: Aggregation by student per month"

  # --- Governance ---
  governance:
    approved_by: data-governance-board
    approved_date: "2025-06-15"
    review_cycle: quarterly
    last_reviewed: "2025-06-15"
    next_review: "2025-09-15"
    change_log:
      - date: "2025-06-15"
        change: "Initial metric definition approved"
        author: "jane.doe"
        pr: "governance-repo#42"

  # --- Validation Rules ---
  validation:
    expected_range:
      min: 0
      max: 1000000
    not_null: true
    freshness:
      warn_after: "24 hours"
      error_after: "48 hours"
```

---

## 3. Bronze/Silver/Gold Medallion Architecture

### 3.1 Databricks Definition

The medallion architecture (also called multi-hop architecture) organizes data into three layers that denote progressively higher data quality:

| Aspect | Bronze (Raw) | Silver (Validated) | Gold (Enriched) |
|--------|-------------|-------------------|-----------------|
| **Purpose** | Ingest and preserve raw data | Clean, validate, deduplicate | Business-ready aggregates |
| **Data Shape** | Source-system format, often strings/VARIANT | Typed, normalized, joined | Star schema, aggregated |
| **Users** | Data engineers, compliance/audit | Data engineers, analysts, data scientists | Business analysts, executives, BI tools |
| **Operations** | Append-only ingestion | Schema enforcement, null handling, deduplication, type casting, joins | Dimensional modeling, aggregation, KPI calculation |
| **Quality Checks** | Minimal (preserve fidelity) | Extensive (constraints, expectations) | Business rule validation |
| **Update Pattern** | Append/overwrite partitions | Incremental merge (CDC) | Materialized views, scheduled refresh |
| **Example Tables** | `lesson_events_raw`, `api_responses` | `stg_lesson_completions`, `stg_students` | `fct_monthly_active_students`, `dim_schools` |

### 3.2 Tier Access Rules

Databricks recommends enforcing tier access through Unity Catalog with separate service principals per layer:

```
Bronze Identity  -->  Can READ source systems, WRITE to bronze schema
                      CANNOT access silver or gold

Silver Identity  -->  Can READ bronze, WRITE to silver schema
                      CANNOT access gold

Gold Identity    -->  Can READ silver, WRITE to gold schema
                      Gold tables exposed to BI/API consumers
```

**Key Governance Principles:**
1. **Least privilege per pipeline stage** -- each Lakeflow job runs under its own service principal with only the permissions needed for its layer
2. **Blast radius containment** -- if bronze code is compromised, it cannot read or corrupt silver/gold
3. **Unity Catalog for metadata** -- centralized access control, audit logging, lineage tracking
4. **Schema isolation** -- `ops.bronze`, `ops.silver`, `ops.gold` or separate catalogs

### 3.3 Data Flow Between Tiers

```
Source Systems (APIs, Kafka, S3, databases)
       |
       v
  +---------+    Append raw data, preserve fidelity
  | BRONZE  |    Schema: strings/VARIANT, metadata columns
  +---------+    Access: data engineers only
       |
       v  (streaming or triggered incremental reads)
  +---------+    Validate, deduplicate, type-cast, join
  | SILVER  |    Schema: enforced types, normalized
  +---------+    Access: engineers + analysts + data scientists
       |
       v  (scheduled batch or materialized views)
  +---------+    Aggregate, model dimensions, calculate KPIs
  |  GOLD   |    Schema: star schema, pre-aggregated
  +---------+    Access: business users, BI tools, APIs, MCP server
```

### 3.4 Governance Rules by Tier

**Bronze Governance:**
- Immutable audit trail -- never delete or modify raw records
- Retain all historical data for reprocessing
- Add metadata columns: `_ingested_at`, `_source_file`, `_batch_id`
- PII tagging at ingestion time (but no masking yet)

**Silver Governance:**
- Data quality expectations enforced (Great Expectations, dbt tests)
- PII masking/tokenization applied
- Referential integrity checks
- Schema evolution handled gracefully
- Quarantine tables for records that fail validation

**Gold Governance:**
- Business metric definitions enforced (the MCP server's domain)
- Row-level and column-level security for sensitive dimensions
- SLA monitoring on freshness
- Approved dimensions and filters only (no ad-hoc raw column access)
- Metric definitions version-controlled and reviewed

---

## 4. Rule-as-Code / Policy-as-Code for Data

### 4.1 Version-Controlling Business Metric Definitions

The industry standard is to treat metric definitions as code:

```
metrics-repo/
  |-- metrics/
  |   |-- engagement/
  |   |   |-- monthly_active_students.yml
  |   |   |-- lesson_completion_rate.yml
  |   |   |-- average_session_duration.yml
  |   |-- revenue/
  |   |   |-- monthly_recurring_revenue.yml
  |   |   |-- average_revenue_per_user.yml
  |   |-- quality/
  |       |-- content_accuracy_score.yml
  |-- policies/
  |   |-- tier_access_policy.yml
  |   |-- pii_masking_policy.yml
  |   |-- freshness_sla_policy.yml
  |-- schemas/
  |   |-- metric_schema_v1.json      # JSON Schema for validation
  |-- tests/
  |   |-- test_metric_validity.py
  |   |-- test_policy_compliance.py
  |-- .github/
      |-- CODEOWNERS                  # Require data governance board approval
      |-- workflows/
          |-- validate_metrics.yml    # CI: validate YAML against schema
          |-- deploy_metrics.yml      # CD: push approved metrics to MCP server
```

### 4.2 GitOps Patterns for Metric Definitions

**Pull Request Workflow:**

```
Developer creates/modifies metric YAML
       |
       v
  Open Pull Request
       |
       v
  CI Pipeline runs:
    1. YAML schema validation (jsonschema or cerberus)
    2. SQL expression syntax check
    3. Dimension reference validation (do referenced columns exist?)
    4. Lineage graph update check
    5. Impact analysis (what dashboards use this metric?)
       |
       v
  Required Reviewers (from CODEOWNERS):
    - Data governance board member
    - Domain data owner
    - Data engineering lead
       |
       v
  Merge to main
       |
       v
  CD Pipeline:
    1. Push metric definitions to MCP server config
    2. Update metric catalog/registry
    3. Notify downstream consumers of changes
    4. Update lineage graph
```

### 4.3 YAML-Based Policy Engine Example

**Tier Access Policy:**

```yaml
# policies/tier_access_policy.yml
policy:
  name: tier_access_control
  version: "1.0"
  description: |
    Controls which roles can access which data tiers
    and what operations they can perform.

  rules:
    - name: bronze_access
      tier: bronze
      allowed_roles:
        - data_engineer
        - data_ops
        - compliance_auditor
      allowed_operations:
        - read
        - write
        - schema_evolve
      deny_roles:
        - business_analyst
        - executive
      conditions:
        - require_vpn: true
        - audit_logging: mandatory

    - name: silver_access
      tier: silver
      allowed_roles:
        - data_engineer
        - data_analyst
        - data_scientist
      allowed_operations:
        - read
      write_roles:
        - data_engineer
      conditions:
        - pii_masked: true
        - data_quality_passed: true

    - name: gold_access
      tier: gold
      allowed_roles:
        - data_analyst
        - business_analyst
        - executive
        - mcp_server
      allowed_operations:
        - read
      conditions:
        - approved_metrics_only: true
        - no_raw_column_access: true
        - freshness_sla_met: true
```

**PII Masking Policy:**

```yaml
# policies/pii_masking_policy.yml
policy:
  name: pii_masking
  version: "1.0"

  classifications:
    - name: student_pii
      fields:
        - pattern: "*student_name*"
          action: hash_sha256
        - pattern: "*email*"
          action: mask_email        # j***@example.com
        - pattern: "*phone*"
          action: redact
        - pattern: "*date_of_birth*"
          action: generalize_year   # 2015-03-21 -> 2015

  tier_rules:
    bronze:
      pii_handling: tag_only        # Tag PII columns, don't mask
    silver:
      pii_handling: mask            # Apply masking rules above
    gold:
      pii_handling: remove_or_aggregate  # No PII in gold, only aggregates
```

### 4.4 Open Policy Agent (OPA) for Data Access

OPA provides a general-purpose policy engine. For data governance, Rego policies evaluate structured input (JSON/YAML) to produce allow/deny decisions:

```rego
package data.governance

default allow = false

# Allow gold-tier metric access for approved roles
allow {
    input.tier == "gold"
    input.metric.status == "approved"
    input.user.role == data.allowed_roles[input.tier][_]
}

# Deny access to deprecated metrics
deny[msg] {
    input.metric.status == "deprecated"
    msg := sprintf("Metric '%s' is deprecated. Use '%s' instead.",
                   [input.metric.name, input.metric.governance.deprecated_by])
}

# Enforce dimension restrictions
allow_dimension[dim] {
    dim := input.requested_dimensions[_]
    dim == input.metric.dimensions[_].name
}

deny_dimension[msg] {
    dim := input.requested_dimensions[_]
    not dim == input.metric.dimensions[_].name
    msg := sprintf("Dimension '%s' is not approved for metric '%s'",
                   [dim, input.metric.name])
}
```

---

## 5. Metric Lineage Patterns

### 5.1 Lineage Representation

Lineage is universally represented as a **Directed Acyclic Graph (DAG)**:

- **Nodes** = data entities (source tables, staging models, metrics)
- **Edges** = transformations / data flow between nodes
- **Direction** = upstream (sources) to downstream (consumers)

**Two granularity levels:**
- **Table-level lineage** -- which tables feed which tables (coarse, useful for impact analysis)
- **Column-level lineage** -- which columns flow to which columns (fine-grained, needed for PII tracking and compliance)

### 5.2 Lineage YAML Representation for MCP Server

```yaml
# lineage/monthly_active_students.yml
lineage:
  metric: monthly_active_students

  graph:
    # Source layer (external)
    - node: source.taleemabad_api.lesson_events
      type: source
      tier: external
      columns: [student_id, lesson_id, event_type, event_timestamp]

    # Bronze layer
    - node: bronze.lesson_events_raw
      type: table
      tier: bronze
      upstream:
        - source.taleemabad_api.lesson_events
      transformation: "Raw ingestion, append-only, no cleaning"
      columns: [student_id, lesson_id, event_type, event_timestamp, _ingested_at]

    # Silver layer
    - node: silver.stg_lesson_completions
      type: table
      tier: silver
      upstream:
        - bronze.lesson_events_raw
      transformation: |
        Filter event_type = 'lesson_completed',
        deduplicate on (student_id, lesson_id, date),
        validate student_id NOT NULL,
        cast event_timestamp to DATE
      columns: [student_id, lesson_id, completed_date, grade, subject_name]
      quality_tests:
        - not_null: [student_id, lesson_id, completed_date]
        - unique: [student_id, lesson_id, completed_date]
        - accepted_values:
            column: grade
            values: ["K", "1", "2", "3", "4", "5"]

    # Gold layer (the metric itself)
    - node: gold.fct_monthly_active_students
      type: metric_table
      tier: gold
      upstream:
        - silver.stg_lesson_completions
      transformation: |
        COUNT(DISTINCT student_id)
        WHERE completed_date within calendar month
        GROUP BY month, grade, subject, district
      metric_ref: monthly_active_students
```

### 5.3 Impact Analysis Using Lineage

When a metric or source changes, lineage enables:

1. **Upstream impact** (root cause): "Why did this metric change?" -- trace back through silver and bronze to source
2. **Downstream impact** (blast radius): "What breaks if I change this table?" -- trace forward to all dependent metrics, dashboards, reports

```yaml
# Impact analysis output example
impact_analysis:
  changed_object: silver.stg_lesson_completions
  change_type: column_removed
  column: district_id

  affected_downstream:
    - type: metric
      name: monthly_active_students
      impact: "Dimension 'school_district' will break"
      severity: high

    - type: dashboard
      name: executive_engagement_report
      impact: "District filter will fail"
      severity: high

    - type: metric
      name: lesson_completion_rate
      impact: "No impact (does not use district_id)"
      severity: none
```

### 5.4 Tools for Lineage

| Tool | Lineage Type | Approach |
|------|-------------|----------|
| **dbt** | Table + column level | Parsed from `ref()` and SQL in YAML |
| **DataHub** | Table + column level | Metadata ingestion from multiple sources |
| **Atlan** | Table + column level | Active metadata, automated discovery |
| **OpenLineage** | Table + column level | Open standard, event-based lineage collection |
| **Marquez** | Table + column level | Open-source lineage server (OpenLineage reference impl) |
| **Unity Catalog** | Table + column level | Built into Databricks, automatic for Spark jobs |

For an MCP server, the recommended approach is to **embed lineage metadata directly in the metric YAML** (as shown above) for self-contained governance, while optionally integrating with OpenLineage for automated collection.

---

## 6. Architectural Recommendations for the MCP Server

### 6.1 Core Design Principles

1. **Metrics-as-Code** -- every metric is a version-controlled YAML file with a strict schema
2. **Pre-approved only** -- the MCP server can ONLY serve queries for metrics with `status: approved`
3. **Dimension lockdown** -- queries can only group/filter by dimensions explicitly listed in the metric definition
4. **Tier enforcement** -- the MCP server only reads from gold-tier tables; bronze/silver are invisible
5. **Lineage embedded** -- each metric carries its own lineage for transparency
6. **Policy-as-Code** -- access rules, PII handling, and freshness SLAs are YAML-defined and version-controlled

### 6.2 Recommended MCP Server Architecture

```
+------------------+
|  Claude / LLM    |
|  (MCP Client)    |
+--------+---------+
         |  MCP Protocol
         v
+--------+---------+
|  Data Governance  |
|  MCP Server       |
|                   |
|  +-------------+  |
|  | Metric      |  |    <-- Loads from metrics/*.yml
|  | Registry    |  |
|  +-------------+  |
|  | Policy      |  |    <-- Loads from policies/*.yml
|  | Engine      |  |
|  +-------------+  |
|  | Query       |  |    <-- Generates SQL from metric definitions
|  | Builder     |  |
|  +-------------+  |
|  | Lineage     |  |    <-- Resolves upstream/downstream
|  | Resolver    |  |
|  +------+------+  |
+---------|----------+
          |  SQL queries (read-only)
          v
+------------------+
|  Gold Layer DB   |
|  (Warehouse)     |
+------------------+
```

### 6.3 MCP Tool Definitions

The MCP server should expose these tools:

```yaml
tools:
  - name: query_metric
    description: "Query an approved metric with optional dimension breakdowns and filters"
    parameters:
      metric_name: string       # Must match an approved metric
      dimensions: list[string]  # Must be from metric's allowed dimensions
      filters: list[object]     # Must reference allowed dimensions
      time_grain: string        # Must be in metric's supported_granularities
      time_range: object        # start_date, end_date

  - name: list_metrics
    description: "List all approved metrics, optionally filtered by tag or domain"
    parameters:
      tags: list[string]
      domain: string
      status: string            # default: "approved"

  - name: describe_metric
    description: "Get full definition of a metric including lineage"
    parameters:
      metric_name: string

  - name: get_lineage
    description: "Trace a metric's upstream sources and downstream dependents"
    parameters:
      metric_name: string
      direction: string         # upstream | downstream | both

  - name: impact_analysis
    description: "Assess impact of a proposed change on dependent metrics"
    parameters:
      object_name: string       # table or metric name
      change_type: string       # column_removed | column_renamed | table_dropped
```

### 6.4 Query Flow

```
1. LLM asks: "What was the monthly active students count by grade for Q1 2025?"

2. MCP Server:
   a. Parse request -> metric: monthly_active_students,
                       dimensions: [grade_level],
                       time_grain: month,
                       time_range: 2025-01-01 to 2025-03-31

   b. Validate:
      - Is "monthly_active_students" approved? YES
      - Is "grade_level" in allowed dimensions? YES
      - Is "month" in supported granularities? YES
      - Does requester have gold tier access? YES

   c. Build SQL from metric definition:
      SELECT
        DATE_TRUNC('month', completed_at) AS month,
        grade AS grade_level,
        COUNT(DISTINCT student_id) AS monthly_active_students
      FROM gold.fct_lesson_completions
      WHERE lesson_status = 'completed'
        AND completed_at BETWEEN '2025-01-01' AND '2025-03-31'
      GROUP BY 1, 2
      ORDER BY 1, 2

   d. Execute against gold-tier database (read-only connection)

   e. Return results + metadata (metric description, lineage summary, freshness)
```

### 6.5 Validation Schema (JSON Schema for Metric YAML)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["metric"],
  "properties": {
    "metric": {
      "type": "object",
      "required": ["name", "label", "description", "version", "status",
                    "owner", "tier", "source", "type", "calculation",
                    "dimensions", "governance"],
      "properties": {
        "name": {
          "type": "string",
          "pattern": "^[a-z][a-z0-9_]*$"
        },
        "status": {
          "type": "string",
          "enum": ["draft", "in_review", "approved", "deprecated"]
        },
        "tier": {
          "type": "string",
          "enum": ["bronze", "silver", "gold"]
        },
        "type": {
          "type": "string",
          "enum": ["simple", "ratio", "cumulative", "derived"]
        },
        "calculation": {
          "type": "object",
          "required": ["aggregation", "expression"],
          "properties": {
            "aggregation": {
              "type": "string",
              "enum": ["sum", "count", "count_distinct", "avg",
                       "min", "max", "median", "percentile"]
            }
          }
        }
      }
    }
  }
}
```

---

## 7. Sources

### Semantic Layer Documentation
- [1] dbt Labs. "About MetricFlow." dbt Developer Hub. https://docs.getdbt.com/docs/build/about-metricflow
- [2] dbt Labs. "Creating Metrics." dbt Developer Hub. https://docs.getdbt.com/docs/build/metrics-overview
- [3] dbt Labs. "Semantic Models." dbt Developer Hub. https://docs.getdbt.com/docs/build/semantic-models
- [4] dbt Labs. "Building Semantic Models (Best Practices)." dbt Developer Hub. https://docs.getdbt.com/best-practices/how-we-build-our-metrics/semantic-layer-3-build-semantic-models
- [5] dbt Labs. "Derived Metrics." dbt Developer Hub. https://docs.getdbt.com/docs/build/derived
- [6] dbt Labs. "Cumulative Metrics." dbt Developer Hub. https://docs.getdbt.com/docs/build/cumulative
- [7] Cube Dev. "Data Modeling Concepts." Cube Documentation. https://cube.dev/docs/product/data-modeling/concepts
- [8] Cube Dev. "Designing Metrics." Cube Documentation. https://cube.dev/docs/product/data-modeling/recipes/designing-metrics
- [9] Cube Dev. "Measures Reference." Cube Documentation. https://cube.dev/docs/product/data-modeling/reference/measures
- [10] Google Cloud. "LookML Terms and Concepts." Looker Documentation. https://cloud.google.com/looker/docs/lookml-terms-and-concepts
- [11] Google Cloud. "Measure Types." Looker Documentation. https://docs.cloud.google.com/looker/docs/reference/param-measure-types
- [12] AtScale. "What is a Semantic Layer?" AtScale Glossary. https://www.atscale.com/glossary/semantic-layer/

### Medallion Architecture
- [13] Microsoft. "What is the Medallion Lakehouse Architecture?" Azure Databricks Documentation. https://learn.microsoft.com/en-us/azure/databricks/lakehouse/medallion
- [14] Databricks. "What is Medallion Architecture?" Databricks Blog. https://www.databricks.com/blog/what-is-medallion-architecture
- [15] Microsoft. "Secure Medallion Architecture Pattern on Azure Databricks." Microsoft Tech Community. https://techcommunity.microsoft.com/blog/analyticsonazure/secure-medallion-architecture-pattern-on-azure-databricks-part-i/4459268

### Policy-as-Code and Governance
- [16] Open Policy Agent. "Documentation." https://www.openpolicyagent.org/docs/latest/
- [17] Spacelift. "Top 12 Policy as Code (PaC) Tools in 2026." https://spacelift.io/blog/policy-as-code-tools
- [18] Platform Engineering. "Policy as Code: The Platform Engineer's Guide." https://platformengineering.org/blog/policy-as-code
- [19] CNCF. "GitOps Policy-as-Code: Securing Kubernetes with Argo CD and Kyverno." https://www.cncf.io/blog/2026/04/02/gitops-policy-as-code-securing-kubernetes-with-argo-cd-and-kyverno/

### Lineage and Impact Analysis
- [20] DataHub. "Data Lineage: What It Is and Why It Matters." https://datahub.com/blog/data-lineage-what-it-is-and-why-it-matters/
- [21] Monte Carlo. "The Ultimate Guide to Data Lineage." https://www.montecarlodata.com/blog-data-lineage/
- [22] Metaplane. "The Ultimate Guide to Data Lineage in dbt." https://www.metaplane.dev/blog/ultimate-guide-to-data-lineage-in-dbt
- [23] dbt Labs. "Getting Started with Data Lineage." https://www.getdbt.com/blog/getting-started-with-data-lineage
- [24] Neo4j. "What Is Data Lineage? Tracking Data Through Enterprise Systems." https://neo4j.com/blog/graph-database/what-is-data-lineage/

### Data Quality
- [25] Great Expectations. "Checkpoint Reference." https://docs.greatexpectations.io/docs/0.18/reference/learn/terms/checkpoint/
