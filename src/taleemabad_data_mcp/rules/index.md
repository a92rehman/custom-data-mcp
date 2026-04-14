# Rules Index

This file is auto-loaded every session. Read the relevant section based on the user's question.

## How This Works
- **Governance logic lives here** in `.claude/rules/` — not in Python code
- **MCP server is a thin execution layer** — use `execute_query`, `list_datasets`, `get_table_schema` tools
- **Rules are organized by region** — always determine the region first, then read that region's rules

## Step 1: Determine Region
Always clarify which region before reading domain rules:
- `organization_id = 1` → **ICT/Islamabad** → read `ict-islamabad/`
- Rawalpindi → read `rawalpindi/`
- Moawin or Akhuwat → read `moawin-akhuwat/` (use `organization_id` to split within region)

If the region's rules don't exist yet, tell the user: "Rules for [region] haven't been added yet."

## General Rules (all regions, always active)
- `data-governance.md` — metric access, audit, classification
- `bigquery.md` — partition-first policy, cost control, event table rules
- `caching.md` — freshness, invalidation, loop prevention
- `failure-handling.md` — retries, circuit breaker, dead letter queue
- `observability.md` — 3-layer telemetry, audit log, structured logging
- `versioning.md` — **ALWAYS bump version before push**, patch vs minor rules

## Region: ICT/Islamabad (`ict-islamabad/`)
Dataset: `tbproddb` | organization_id: 1 | School reference: `FDE_Schools`

### ict-islamabad/dimensions/teachers/
When: teacher profiles, user counts, school assignments
- `teacher-query-rules.md` — level (PRIMARY/MIDDLE/SECONDARY), required filters, key tables

### ict-islamabad/lesson_plans/
When: LP usage, completion rates, On-Schedule/Off-Schedule, Core vs User Generated
- `lp-query-rules.md` — LP types, status categories, counting rules, aggregation
- `lp-product-analytics.md` — 40 LP events catalog, engagement/funnel/retention metrics, video/download/translation/offline analytics, UGLP funnel, error rates

### ict-islamabad/coaching_observations/
When: FICO scores, Section B/C/D, observer activity, feedback, AI vs human bifurcation
- `observation-query-rules.md` — sections, score mapping, observer types, FICO clean tables, aggregation
- `observation-product-analytics.md` — 24 events: scheduling, observation execution, feedback (AI vs manual), digital coach recording funnel

### ict-islamabad/coaching_ai/
When: Digital Coach (AI) observations, automated observation questions, request tracker pipeline
- `ai-coaching-rules.md` — source='automated' bifurcation, same FICO scoring, digital_coach_requesttracker (verification only)

### ict-islamabad/student_results/
When: AI student assessments, ASER enumerator assessments, student learning outcomes
- `ai-assessment-rules.md` — CONFLICT/possibly inactive, student_learning_studentassessmentresult (133 rows)
- `aser-enumerator-rules.md` — ODK endline ASER (grades 1-3 + 4-5), 52 ODK tables available
- `student-product-analytics.md` — 18 events: student list management, results viewing, FLN tracking, report cards

### ict-islamabad/training/
When: teacher training levels, pass rates, completion status
- `training-query-rules.md` — pass threshold (>=80), two data sources, level ordering
- `training-product-analytics.md` — 93 events across 3 features (training courses, exam generator, exam checker), video/quiz funnels, level progression, reliability metrics

### ict-islamabad/platform/
When: app-level engagement, signup/onboarding, navigation, data sync, push notifications, community, errors
- `app-product-analytics.md` — 47 events: signup funnel, dashboard navigation, data sync health, push notifications, community engagement, error rates

## Region: Rawalpindi (`rawalpindi/`)
Datasets: `RUMI_DB` + `TaleemHub_DB` | Join key: `phone_number` | Cohort: `TaleemHub_DB.users`

### rawalpindi/dimensions/users/
When: teacher profiles, user counts, school assignments, cohort size
- `user-query-rules.md` — TaleemHub canonical roster, Rumi join via phone_number, role/status filters

### rawalpindi/lesson_plans/
When: AI lesson plan generation counts, LP volume by grade/subject
- `lp-query-rules.md` — Rumi lesson_plans, RWP cohort via phone_number bridge

### rawalpindi/coaching/
When: human mentoring visits, AI coaching sessions, coaching results
- `human-coaching-rules.md` — TaleemHub mentoring_visits, narrative feedback, geo-verification
- `ai-coaching-rules.md` — Rumi coaching_sessions + quality_metrics, audio-based AI coaching pipeline

### rawalpindi/student_results/
When: reading assessments (AI), ASER assessments (human)
- `ai-assessment-rules.md` — Rumi reading_assessments (WCPM, accuracy, comprehension)
- `human-assessment-rules.md` — DRAFT — TaleemHub ASER results, pending rubric verification

## Region: Moawin / Akhuwat (`moawin-akhuwat/`)
Databases: `neondb` (Schoolpilot) + `zavia1` (Zavia) | Regional split: `organization_id` | School reference: TBD per region

### moawin-akhuwat/dimensions/users/
When: teacher profiles, user counts, school assignments, institutional attributes
- `user-query-rules.md` — Schoolpilot canonical roster + teachers enrichment, organization_id filter, test user exclusion

### moawin-akhuwat/lesson_plans/
When: AI lesson plan generation counts, LP volume by grade/subject
- `lp-query-rules.md` — Zavia lesson_plans, test user exclusion

### moawin-akhuwat/coaching/
When: AI coaching sessions, coaching results, quality metrics
- `ai-coaching-rules.md` — Zavia coaching_sessions + quality_metrics, test user exclusion, lesson fidelity scoring

### moawin-akhuwat/student_results/
When: AI reading assessments, school-administered assessments, coach spot checks
- `ai-assessment-rules.md` — Zavia reading_assessments
- `school-assessment-rules.md` — Schoolpilot student_scores + assessments (human-entered)
- `coach-spotcheck-rules.md` — COMING SOON — coach-collected spot checks (table deployment TBD, deadline Apr 13)

## Cross-Region KPI Comparability

Cross-region comparison is limited to **volume and coverage metrics**. Qualitative comparison (scores, outcomes) is NOT valid because regions use fundamentally different tools and scoring frameworks.

| KPI | ICT Source | RWP Source | Moawin/Akhuwat Source | Comparable Metric |
|-----|-----------|-----------|----------------------|-------------------|
| User data | user_school_profiles | TaleemHub_DB.users | neondb.users + teachers | Teacher count, cohort size |
| Lesson plans | analytics_events (canonical) | RUMI_DB.lesson_plans | zavia1.lesson_plans | Volume only |
| Coaching - Human | coaching_observation (scored) | mentoring_visits (narrative) | DEPRECATED / TBD | Session count + coverage % |
| Coaching - AI | observation stack (automated) | coaching_sessions | coaching_sessions | Session count + completion rate |
| AI Coaching - Lesson Fidelity | coaching_observationquestion | analysis_data | analysis_data (fidelity_score) | Fidelity score (if comparable) |
| Student results - AI | not active | reading_assessments | reading_assessments | Not comparable yet |
| Student results - Human | ODK ASER | TaleemHub ASER | student_scores + assessments | Volume only |
| Training | teacher_training_level | Not in scope | Not in scope | ICT only |

## Database Context
- **BigQuery:** Project `niete-bq-prod` — ICT/Islamabad dataset `tbproddb` (466 tables), `RUMI_DB` (70 tables), `TaleemHub_DB` (60 tables)
- **PostgreSQL (Schoolpilot):** Database `neondb` — user/teacher rosters, student assessments, institutional attributes
- **PostgreSQL (Zavia):** Database `zavia1` — AI coaching sessions, lesson plans, reading assessments, quality metrics
- More datasets will be added after migration from other sources
