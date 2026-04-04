# Data Governance MCP: Taleemabad's Data Navigator

> A conversational semantic layer that ensures every report, dashboard, and analysis uses accurate, consistent, and governed data definitions.

---

## 1. Problem Statement

Taleemabad is an EdTech organization with apps for teacher training and lesson plans, working to improve student learning outcomes. Multiple teams — Product, Partnerships, Pedagogy, Data — all need data to make decisions.

Today, getting the right data is broken:

- **Conflicting numbers.** "What's our LP adoption rate?" returns different answers depending on which dashboard you check. Two board decks show two different numbers for the same metric.
- **Repeated definition questions.** The data team answers "what does X mean?" every week. Is FICO Section B >= 60% per teacher or per school? Does LP adoption count opened or used-in-class?
- **No audit trail.** When a number appears in a donor report, there is no traceable path from the final figure back to the query and definition that produced it.

---

## 2. Solution Overview

A Model Context Protocol server built in Python that acts as the single governed interface between business teams and Taleemabad's BigQuery data warehouse.

Instead of writing SQL or navigating dashboards with inconsistent definitions, users ask natural language questions. The MCP clarifies ambiguity, resolves to pre-approved metric definitions, executes governed queries, and logs everything.

---

## 3. How It Works

Every interaction follows a five-step flow:

**Ask** — "Show me LP adoption this quarter"

**Clarify** — "Which regions? Weekly threshold >= 65% or cumulative? By school or by teacher?"

**Validate** — Maps to approved Gold metric `lp_weekly_adoption_rate`

**Execute** — Runs pre-approved BigQuery query against curated reporting tables

**Observe** — Logs who asked, which rule fired, result shape

---

## 4. Core Principles

1. **Conversation over assumption** — always clarify, never guess
2. **Rules over ad-hoc SQL** — no direct raw table access
3. **Definitions as code** — YAML-defined, version-controlled, review-gated. Lifecycle: `draft → review → approved → certified → deprecated`
4. **Observe everything** — full audit trail of who asked what
5. **Progressive trust** — Bronze → Silver → Gold tier system

---

## 5. Three-Tier Rule Architecture

### Bronze: Raw Ingestion
Raw event tables — app telemetry, observation logs, assessment submissions. Data engineering access only. No MCP access.

### Silver: Curated Reporting Tables
Taleemabad's existing curated tables used by Power BI and other reporting tools. Cleaned, joined, and transformed. Data team maintains these.

### Gold: Approved Metrics & KPIs
Pre-approved metric definitions with certified calculations and target values. Examples:
- LP adoption >= 65%/week
- FICO Section B >= 60%
- Student 3/5+ pass rate at 60%
- Coach uptime >= 99.5%

The MCP reads only from Gold. Bronze and Silver are invisible to consumers.

---

## 6. Observability & Continuous Improvement Engine

### Auto-Tracking
Every interaction logged: who asked, what was clarified, which Gold metric resolved, query execution time, result shape, errors.

### Pattern Detection
- Frequently asked questions that don't map to a Gold metric (signal to create new metrics)
- Common clarification paths (signal to improve metric descriptions)
- Failed/rejected queries (signal for rule gaps)
- Usage heatmaps — which teams query which metrics, peak times

### Self-Improvement Loop
- Suggests new Gold metrics when Silver-tier queries repeat
- Flags stale metrics nobody queries anymore
- Recommends clarification shortcuts when the same disambiguation happens repeatedly
- Generates weekly governance digest for the data team

---

## 7. Metric Lineage & Transparency

When someone asks "How is LP adoption calculated?", the MCP provides a full trace:

Gold metric → Silver curated table → Bronze raw source events

Users can always ask "how is this calculated?" and get the full path.

---

## 8. Data Freshness & SLAs

- Every response includes: "This data is current as of [timestamp]."
- The system knows refresh schedules of curated tables and warns when data is stale.
- Each metric defines a freshness SLA. Stale data triggers warnings.

---

## 9. Data Classification

| Tier | Description | Examples |
|------|-------------|----------|
| **Public** | Aggregate KPIs safe for external/donor reports | School-level LP adoption, programme-wide proficiency |
| **Internal** | All team-level and individual-level data — accessible to all internal teams | Individual teacher FICO scores, student outcomes, regional breakdowns |
| **external_guarded** | Data leaving the organization — extra confirmation + audit logging | Board decks, donor reports, partner data sharing |

Individual teacher FICO scores and student outcomes are Internal, not restricted.

---

## 10. Query Cost Guardrails

BigQuery charges by data scanned. The MCP enforces a **partition-first execution policy**: always route to partitioned tables, reject queries without date filters, and estimate cost before execution. Unpartitioned tables are flagged as "partition debt" for the data team rather than scanned.

Exact thresholds and enforcement rules: `.claude/rules/bigquery.md`

---

## 11. Caching & Performance

The user always knows how fresh their data is, and the system never pretends cached data is live. Every response shows when it was computed and when the source was last refreshed. Users can force-refresh at any time.

The system pre-computes critical metrics on schedule and auto-invalidates stale cache. Ad-hoc queries always go live. The caching design includes explicit loop prevention to ensure users and the system never get stuck serving stale data.

Exact rules and loop prevention logic: `.claude/rules/caching.md`

---

## 12. Failure Modes & Graceful Degradation

The MCP never returns partial or wrong data silently. Every failure tells the user what happened, why, and what to try next.

**Principles:**
- BigQuery down → serve last-known value with clear "unavailable" label, never silently retry in a loop
- Ambiguous metric → list all matches, force user to pick — never guess
- No matching metric → show closest matches, log gap — never fall back to raw SQL
- Partial or stale data → show what's available with explicit warnings — never present incomplete data as complete

**Loop prevention:** retries with backoff, circuit breaker pattern, clarification depth limit, and a dead letter queue for unresolvable requests.

Exact thresholds, retry counts, and circuit breaker parameters: `.claude/rules/failure-handling.md`

---

## 13. Stakeholder Value

| Stakeholder | Pain Today | Value from Data Navigator |
|-------------|-----------|---------------------------|
| **Product & Partnerships** | Different dashboards, different numbers | Self-service certified metrics; consistent numbers |
| **Pedagogy Team** | Definitions vary by analyst | Standardized Theory of Change metrics |
| **Data Team** | 40%+ time on "what does X mean?" | MCP handles definitions; digest surfaces gaps |
| **Leadership/Governance** | No audit trail for external data | Immutable audit log; External-Guarded tier |

---

## 14. Success Criteria

- Zero conflicting metric definitions across dashboards
- 80% reduction in "what does X mean?" queries to data team
- 100% audit coverage on sensitive metrics (student outcomes, FICO scores)

---

## 15. Roadmap

| Phase | Focus |
|-------|-------|
| **Phase 1** | Core MCP + rule engine + BigQuery connector |
| **Phase 2** | Conversational governance + clarification flows |
| **Phase 3** | Observability dashboard + audit trails |
| **Phase 4** | Self-service expansion + feedback loops |

---

## Appendix: Theory of Change Pipeline

```
LP Adoption (>= 65%/week) → Coaching Loop → Classroom Practice (FICO-B >= 60%)
  → Teacher Behavior (FICO-C trend) → Student Outcomes (60% score 3/5+)
```
