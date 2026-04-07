# Rawalpindi Region Rules — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create governed query rules for the Rawalpindi region across 6 KPIs + 1 user dimension, mirrored in both `.claude/rules/` and `src/taleemabad_data_mcp/rules/`.

**Architecture:** Markdown rule files in `rawalpindi/` subdirectories, following the same pattern as existing `ict-islamabad/` rules. Each file defines one KPI domain with tables, filters, joins, aggregation patterns, and mandatory clarifications. The `index.md` is updated to route Rawalpindi questions to these rule files.

**Tech Stack:** Markdown rule files, BigQuery SQL patterns, no code changes.

**Spec:** `docs/superpowers/specs/2026-04-07-rawalpindi-rules-design.md`

---

## Discovered Status Values (from live BigQuery queries)

These MUST be used in the rule files:

**TaleemHub_DB.users.status:** `active` (1171), `pending` (124), `approved` (1)
**TaleemHub_DB.users.role:** `TEACHER` (1002), `HEAD_TEACHER` (255), `AEO` (23), `TRAINING_MANAGER` (8), `SUPER_ADMIN` (4), `DDEO` (2), `DEO` (2)
**TaleemHub_DB.mentoring_visits.status:** `submitted` (95) — all visits are submitted
**RUMI_DB.coaching_sessions.status:** `completed` (124), `failed` (29), `test_cleanup` (7), `cancelled` (4), `initiated` (3), `awaiting_photo` (2), `awaiting_lesson_plan` (1)
**RUMI_DB.reading_assessments.status:** `completed` (142), `passage_generated` (63), `fluency_completed` (40), `failed` (19), `comprehension_completed` (11), `abandoned` (1), `comprehension_in_progress` (1)

---

## File Map

### Files to Create (each in TWO locations)
| File | Location 1 (dev) | Location 2 (dist) |
|------|------------------|--------------------|
| User dimension rules | `.claude/rules/rawalpindi/dimensions/users/user-query-rules.md` | `src/taleemabad_data_mcp/rules/rawalpindi/dimensions/users/user-query-rules.md` |
| Lesson plan rules | `.claude/rules/rawalpindi/lesson_plans/lp-query-rules.md` | `src/taleemabad_data_mcp/rules/rawalpindi/lesson_plans/lp-query-rules.md` |
| Human coaching rules | `.claude/rules/rawalpindi/coaching/human-coaching-rules.md` | `src/taleemabad_data_mcp/rules/rawalpindi/coaching/human-coaching-rules.md` |
| AI coaching rules | `.claude/rules/rawalpindi/coaching/ai-coaching-rules.md` | `src/taleemabad_data_mcp/rules/rawalpindi/coaching/ai-coaching-rules.md` |
| AI student results | `.claude/rules/rawalpindi/student_results/ai-assessment-rules.md` | `src/taleemabad_data_mcp/rules/rawalpindi/student_results/ai-assessment-rules.md` |
| Human student results | `.claude/rules/rawalpindi/student_results/human-assessment-rules.md` | `src/taleemabad_data_mcp/rules/rawalpindi/student_results/human-assessment-rules.md` |

### Files to Modify (TWO locations each)
| File | Location 1 (dev) | Location 2 (dist) |
|------|------------------|--------------------|
| Rules index | `.claude/rules/index.md` | `src/taleemabad_data_mcp/rules/index.md` |

---

### Task 1: Create directory structure

**Files:**
- Create directories in both `.claude/rules/rawalpindi/` and `src/taleemabad_data_mcp/rules/rawalpindi/`

- [ ] **Step 1: Create all directories**

```bash
mkdir -p ".claude/rules/rawalpindi/dimensions/users"
mkdir -p ".claude/rules/rawalpindi/lesson_plans"
mkdir -p ".claude/rules/rawalpindi/coaching"
mkdir -p ".claude/rules/rawalpindi/student_results"
mkdir -p "src/taleemabad_data_mcp/rules/rawalpindi/dimensions/users"
mkdir -p "src/taleemabad_data_mcp/rules/rawalpindi/lesson_plans"
mkdir -p "src/taleemabad_data_mcp/rules/rawalpindi/coaching"
mkdir -p "src/taleemabad_data_mcp/rules/rawalpindi/student_results"
```

- [ ] **Step 2: Verify directories exist**

```bash
find .claude/rules/rawalpindi -type d
find src/taleemabad_data_mcp/rules/rawalpindi -type d
```

---

### Task 2: Write User Dimension Rules

**Files:**
- Create: `.claude/rules/rawalpindi/dimensions/users/user-query-rules.md`
- Create: `src/taleemabad_data_mcp/rules/rawalpindi/dimensions/users/user-query-rules.md`

- [ ] **Step 1: Write the rule file**

Write the following content to `.claude/rules/rawalpindi/dimensions/users/user-query-rules.md`:

```markdown
# User Query Rules — Rawalpindi

## When These Rules Apply

User asks about:
- Rawalpindi teacher profiles, registration, or institutional attributes
- User counts, cohort size, school assignments
- Rumi-TaleemHub user matching
- Teacher roster for Rawalpindi

## Mandatory Clarifications

### Role
Ask: "Which role? TEACHER, HEAD_TEACHER, or all?"
- Known roles: `TEACHER` (1002), `HEAD_TEACHER` (255), `AEO` (23), `TRAINING_MANAGER` (8), `SUPER_ADMIN` (4), `DDEO` (2), `DEO` (2)
- For teacher KPIs, default to `role = 'TEACHER'` unless user specifies otherwise

### Geographic Scope
Ask: "All Rawalpindi, or specific tehsil/markaz?"
- Geographic hierarchy: `district_id` → `tehsil_id`/`tehsil_name` → `markaz_id`/`markaz_name`

## Key Tables

| Table | Role | Rows | Dataset |
|-------|------|------|---------|
| `TaleemHub_DB.users` | Canonical teacher roster | 1,296 | TaleemHub_DB |
| `RUMI_DB.users` | Join helper for Rumi data (AI LP, coaching, assessments) | 5,319 | RUMI_DB |

**Note:** These tables are small and unpartitioned. Full scans are acceptable at this scale. Revisit if tables grow beyond 10,000 rows.

## Key Columns — TaleemHub_DB.users

- `id` — primary key (STRING)
- `name`, `phone_number`, `cnic` — identity
- `role` — user type: TEACHER, HEAD_TEACHER, AEO, TRAINING_MANAGER, SUPER_ADMIN, DDEO, DEO
- `status` — `active` (1171), `pending` (124), `approved` (1)
- `school_id`, `school_name` — school assignment
- `district_id`, `tehsil_id`, `tehsil_name`, `markaz_id`, `markaz_name` — geographic hierarchy
- `role_id` — numeric role identifier (FLOAT)
- `gender` — teacher gender
- `created_at`, `date_of_joining` — temporal
- `whatsapp_number` — may differ from phone_number

## Key Columns — RUMI_DB.users

- `id` — primary key (STRING, Rumi user ID)
- `phone_number` — join key to TaleemHub
- `is_test_user` — BOOLEAN, must exclude `true`
- `region`, `organization` — Rumi-side context (can filter RWP when querying Rumi directly)
- `registration_completed` — BOOLEAN, whether fully onboarded
- `name`, `first_name`, `last_name` — identity
- `school_name`, `subjects_taught`, `grades_taught` — teaching context
- `emis_code` — school EMIS if available

## Join Logic (TaleemHub → Rumi)

Use this join whenever a query needs Rumi data (lesson plans, AI coaching, reading assessments) for the RWP cohort:

```sql
TaleemHub_DB.users th
LEFT JOIN RUMI_DB.users ru ON th.phone_number = ru.phone_number
  AND ru.is_test_user IS NOT TRUE
```

Use `LEFT JOIN` to keep all TaleemHub teachers; `INNER JOIN` only when Rumi data is required.

## Required Filters

- `th.status = 'active'` — active users only (default). Include `pending`/`approved` only if user explicitly asks.
- `ru.is_test_user IS NOT TRUE` — exclude Rumi test accounts when joining
- `th.role` — filter by role for teacher-specific queries

## Region Filter Strategy

`TaleemHub_DB.users` currently contains only Rawalpindi users. If TaleemHub expands to other regions:
- Add `th.district_id` filter for Rawalpindi-specific queries
- `RUMI_DB.users` has `region` and `organization` columns — use these when querying Rumi directly without TaleemHub join

## Aggregation Patterns

| User asks about | GROUP BY | Aggregate |
|-----------------|----------|-----------|
| Total teachers | — | `COUNT(DISTINCT th.id)` |
| Teachers per school | `th.school_id`, `th.school_name` | `COUNT(DISTINCT th.id)` |
| Teachers per tehsil/markaz | `th.tehsil_name`, `th.markaz_name` | `COUNT(DISTINCT th.id)` |
| Teachers with Rumi match | — | `COUNT(DISTINCT th.id) WHERE ru.id IS NOT NULL` (use LEFT JOIN) |
| Teachers by role | `th.role` | `COUNT(DISTINCT th.id)` |
| Teachers by status | `th.status` | `COUNT(DISTINCT th.id)` |

## Data Conventions

- Timezone: `Asia/Karachi` for all date conversions
- `phone_number` is the universal join key between TaleemHub and Rumi
- A teacher appears once in TaleemHub (one row per user)
- A teacher may or may not exist in Rumi — not all teachers use the AI tools
```

- [ ] **Step 2: Copy to distribution location**

```bash
cp .claude/rules/rawalpindi/dimensions/users/user-query-rules.md src/taleemabad_data_mcp/rules/rawalpindi/dimensions/users/user-query-rules.md
```

- [ ] **Step 3: Commit**

```bash
git add .claude/rules/rawalpindi/dimensions/users/user-query-rules.md src/taleemabad_data_mcp/rules/rawalpindi/dimensions/users/user-query-rules.md
git commit -m "rules: add Rawalpindi user dimension query rules"
```

---

### Task 3: Write Lesson Plan Rules

**Files:**
- Create: `.claude/rules/rawalpindi/lesson_plans/lp-query-rules.md`
- Create: `src/taleemabad_data_mcp/rules/rawalpindi/lesson_plans/lp-query-rules.md`

- [ ] **Step 1: Write the rule file**

Write the following content to `.claude/rules/rawalpindi/lesson_plans/lp-query-rules.md`:

```markdown
# Lesson Plan Query Rules — Rawalpindi

## When These Rules Apply

User asks about:
- AI lesson plan generation in Rawalpindi
- LP counts, volume, or trends
- LP breakdown by grade or subject
- Teacher LP activity or engagement

## Mandatory Clarifications

### Time Period
Ask: "Which time period? Specific date range, or all-time?"
- `created_at` (DATETIME) is the timestamp column

### Breakdown
Ask if relevant: "Breakdown by grade/subject, or total count?"
- `grade` and `subject` columns available for segmentation

## Key Tables

| Table | Role | Rows | Dataset |
|-------|------|------|---------|
| `RUMI_DB.lesson_plans` | AI-generated lesson plan records | 4,759 | RUMI_DB |
| `RUMI_DB.users` | User bridge (LP creator → phone_number) | 5,319 | RUMI_DB |
| `TaleemHub_DB.users` | RWP cohort filter | 1,296 | TaleemHub_DB |

**Note:** These tables are small and unpartitioned. Full scans are acceptable at this scale.

## Key Columns — RUMI_DB.lesson_plans

- `id` — primary key (STRING), use `COUNT(DISTINCT id)` for LP count
- `user_id` — FK to `RUMI_DB.users.id`
- `topic` — lesson topic
- `grade` — grade level (STRING)
- `subject` — subject name (STRING)
- `type` — LP type categorization
- `source` — generation source
- `lp_variant` — LP variant for A/B testing
- `ab_group` — A/B test group assignment
- `created_at` (DATETIME) — when the LP was generated

## Join Path (RWP Cohort Filter)

Every LP query for Rawalpindi MUST filter to the RWP teacher cohort:

```sql
SELECT ...
FROM RUMI_DB.lesson_plans lp
JOIN RUMI_DB.users ru ON lp.user_id = ru.id
JOIN TaleemHub_DB.users th ON ru.phone_number = th.phone_number
WHERE ru.is_test_user IS NOT TRUE
  AND th.status = 'active'
```

## Counting Rules

- LP count = `COUNT(DISTINCT lp.id)` — never count raw rows
- Unique teachers with LPs = `COUNT(DISTINCT lp.user_id)`
- Never assume one LP per teacher — teachers can generate multiple LPs

## Key Difference from ICT

- ICT counts LP **starts and completions** from `events_partitioned`, computes `lp_ratio` (completion rate) against timetable schedule
- RWP counts **generated records** — one row in `RUMI_DB.lesson_plans` = one AI-generated LP delivered to a teacher
- RWP has no timetable data → no completion rate, no On-Schedule/Off-Schedule concept
- **Cross-region LP comparison is volume only** (total LPs generated)

## Reporting Grain

Daily / Weekly / Monthly, with optional grade/subject breakdown

## Aggregation Patterns

| User asks about | GROUP BY | Aggregate |
|-----------------|----------|-----------|
| Total LPs generated | — | `COUNT(DISTINCT lp.id)` |
| LPs per teacher | `lp.user_id` | `COUNT(DISTINCT lp.id)` |
| LPs per school | `th.school_id`, `th.school_name` | `COUNT(DISTINCT lp.id)` |
| LPs by grade | `lp.grade` | `COUNT(DISTINCT lp.id)` |
| LPs by subject | `lp.subject` | `COUNT(DISTINCT lp.id)` |
| LPs by grade + subject | `lp.grade`, `lp.subject` | `COUNT(DISTINCT lp.id)` |
| Daily trend | `DATE(lp.created_at)` | `COUNT(DISTINCT lp.id)` |
| Weekly trend | `DATE_TRUNC(lp.created_at, WEEK(SATURDAY))` | `COUNT(DISTINCT lp.id)` |
| Monthly trend | `DATE_TRUNC(lp.created_at, MONTH)` | `COUNT(DISTINCT lp.id)` |
| Active LP teachers | — | `COUNT(DISTINCT lp.user_id)` |

## Data Conventions

- Timezone: `Asia/Karachi` for all date conversions
- Weeks run Saturday to Friday (consistent with ICT convention)
```

- [ ] **Step 2: Copy to distribution location**

```bash
cp .claude/rules/rawalpindi/lesson_plans/lp-query-rules.md src/taleemabad_data_mcp/rules/rawalpindi/lesson_plans/lp-query-rules.md
```

- [ ] **Step 3: Commit**

```bash
git add .claude/rules/rawalpindi/lesson_plans/ src/taleemabad_data_mcp/rules/rawalpindi/lesson_plans/
git commit -m "rules: add Rawalpindi lesson plan query rules"
```

---

### Task 4: Write Human Coaching Rules

**Files:**
- Create: `.claude/rules/rawalpindi/coaching/human-coaching-rules.md`
- Create: `src/taleemabad_data_mcp/rules/rawalpindi/coaching/human-coaching-rules.md`

- [ ] **Step 1: Write the rule file**

Write the following content to `.claude/rules/rawalpindi/coaching/human-coaching-rules.md`:

```markdown
# Human Coaching Query Rules — Rawalpindi

## When These Rules Apply

User asks about:
- Human coaching/mentoring visits in Rawalpindi
- Observation feedback (strengths, areas for improvement, action items)
- Teacher coverage by mentors/observers
- Coaching session counts or trends
- Voice note transcriptions from visits

## Mandatory Clarifications

### Query Type
Ask: "Session count, or detailed coaching results (feedback text)?"

### Time Period
Ask: "Which time period?"
- `visit_date` is the date column for aggregation

### Aggregation Level
Ask: "Per school, per observer, per teacher, or overall?"

## Key Tables

| Table | Role | Rows | Dataset |
|-------|------|------|---------|
| `TaleemHub_DB.mentoring_visits` | Human coaching visit records | 95 | TaleemHub_DB |
| `TaleemHub_DB.users` | Observer/mentor identity | 1,296 | TaleemHub_DB |

**Explicitly NOT:** `TaleemHub_DB.monitoring_visits` — this is a separate table for infrastructure/compliance monitoring, NOT coaching.

**Note:** These tables are small and unpartitioned. Full scans are acceptable at this scale.

## Key Columns — TaleemHub_DB.mentoring_visits

### Identity & Context
- `id` — primary key (STRING), use `COUNT(DISTINCT id)` for visit count
- `user_id` — FK to `TaleemHub_DB.users.id` (the observer/mentor who conducted the visit)
- `observer_name`, `observer_designation` — observer identity and role
- `teacher_name` — observed teacher (STRING, no FK — see Teacher Matching Note)
- `teacher_cnic` — observed teacher CNIC (STRING, no FK — preferred for matching)
- `school_id`, `school_name` — school where visit occurred
- `visit_date` — date of visit (STRING, use for time-based aggregation)
- `arrival_time`, `departure_time` — visit duration
- `class_observed`, `grade_observed`, `subject` — classroom context
- `markaz`, `tehsil` — geographic hierarchy
- `rubric_type` — may indicate structured rubric (future use)
- `role_id` — observer role (FLOAT)

### Coaching Results (all inline, unstructured narrative)
- `general_feedback` — free text overall feedback
- `strengths_observed` — what went well
- `areas_for_improvement` — what needs work
- `action_items` — next steps for the teacher
- `evidence` — supporting evidence/notes
- `voice_note_transcription` — transcribed voice notes from the visit
- `voice_note_url` — URL to audio evidence
- `tm_notes` — team manager notes

### Geo-verification
- `captured_latitude`, `captured_longitude` — GPS coordinates of visit
- `captured_location_source` — how location was captured

### Status
- `status` — all current records are `submitted` (95/95)
- Default filter: `status = 'submitted'`

## Teacher Matching Note

`teacher_name` and `teacher_cnic` are string fields with **no foreign key** to the users table. For reliable teacher-level aggregation:
- **Prefer `teacher_cnic`** over `teacher_name` (names have spelling variations, CNIC is more stable)
- CNIC format may vary (with/without dashes) — normalize before matching
- If CNIC matching proves unreliable, flag as a data quality gap

## Key Difference from ICT

- ICT has **structured scoring** — `coaching_observationanswer` with yes/partial/no answers, numeric scores, FICO sections B/C/D
- RWP is **unstructured narrative** — free text feedback fields, no numeric scores, no sections
- Cross-region coaching comparison: **session count** and **coverage %** (teachers observed / total teachers) only. Score-based comparison is NOT valid.

## Required Filters

- `status = 'submitted'` — valid visits only (currently all records)
- `visit_date` — for time range filtering

## Aggregation Patterns

| User asks about | GROUP BY | Aggregate |
|-----------------|----------|-----------|
| Total visits | — | `COUNT(DISTINCT mv.id)` |
| Visits per school | `mv.school_id`, `mv.school_name` | `COUNT(DISTINCT mv.id)` |
| Visits per observer | `mv.user_id`, `mv.observer_name` | `COUNT(DISTINCT mv.id)` |
| Visits per teacher | `mv.teacher_cnic` | `COUNT(DISTINCT mv.id)` |
| Teacher coverage | — | `COUNT(DISTINCT mv.teacher_cnic)` / total active teachers |
| Visits per tehsil/markaz | `mv.tehsil`, `mv.markaz` | `COUNT(DISTINCT mv.id)` |
| Weekly trend | `DATE(mv.visit_date)` grouped by week | `COUNT(DISTINCT mv.id)` |
| Monthly trend | `DATE(mv.visit_date)` grouped by month | `COUNT(DISTINCT mv.id)` |

## Data Conventions

- Timezone: `Asia/Karachi` for all date conversions
- `visit_date` is stored as STRING — cast to DATE for aggregation: `PARSE_DATE('%Y-%m-%d', mv.visit_date)`
- One visit = one classroom observation session
```

- [ ] **Step 2: Copy to distribution location**

```bash
cp .claude/rules/rawalpindi/coaching/human-coaching-rules.md src/taleemabad_data_mcp/rules/rawalpindi/coaching/human-coaching-rules.md
```

- [ ] **Step 3: Commit**

```bash
git add .claude/rules/rawalpindi/coaching/human-coaching-rules.md src/taleemabad_data_mcp/rules/rawalpindi/coaching/human-coaching-rules.md
git commit -m "rules: add Rawalpindi human coaching query rules"
```

---

### Task 5: Write AI Coaching Rules

**Files:**
- Create: `.claude/rules/rawalpindi/coaching/ai-coaching-rules.md`
- Create: `src/taleemabad_data_mcp/rules/rawalpindi/coaching/ai-coaching-rules.md`

- [ ] **Step 1: Write the rule file**

Write the following content to `.claude/rules/rawalpindi/coaching/ai-coaching-rules.md`:

```markdown
# AI Coaching Query Rules — Rawalpindi

## When These Rules Apply

User asks about:
- AI coaching sessions in Rawalpindi
- Audio coaching analysis or transcripts
- Coaching quality metrics (processing time, satisfaction)
- AI coaching costs or token usage
- Teacher satisfaction with AI coaching
- Coaching pipeline status or errors

## Mandatory Clarifications

### Query Type
Ask: "Session count, coaching results (analysis/transcripts), or quality metrics?"

### Session Filter
Ask: "All sessions or completed only?"
- Default KPI reporting: `status = 'completed'` only
- Include all statuses only if user explicitly asks for pipeline diagnostics

### Time Period
Ask: "Which time period?"
- `created_at` (TIMESTAMP) is the primary timestamp

## Key Tables

| Table | Role | Rows | Dataset |
|-------|------|------|---------|
| `RUMI_DB.coaching_sessions` | AI coaching session records | 170 | RUMI_DB |
| `RUMI_DB.coaching_quality_metrics` | Quality and performance metrics | 125 | RUMI_DB |
| `RUMI_DB.users` | User bridge | 5,319 | RUMI_DB |
| `TaleemHub_DB.users` | RWP cohort filter | 1,296 | TaleemHub_DB |

**Note:** These tables are small and unpartitioned. Full scans are acceptable at this scale.

## Join Path

```sql
-- Session data with RWP cohort filter
SELECT ...
FROM RUMI_DB.coaching_sessions cs
JOIN RUMI_DB.users ru ON cs.user_id = ru.id
JOIN TaleemHub_DB.users th ON ru.phone_number = th.phone_number
WHERE ru.is_test_user IS NOT TRUE
  AND th.status = 'active'

-- With quality metrics
LEFT JOIN RUMI_DB.coaching_quality_metrics cqm ON cqm.coaching_session_id = cs.id
```

## Status Values

| Status | Count | Meaning | Include in KPI? |
|--------|-------|---------|-----------------|
| `completed` | 124 | Successfully processed | YES (default) |
| `failed` | 29 | Processing failed | Only for diagnostics |
| `test_cleanup` | 7 | Test data cleanup | NEVER |
| `cancelled` | 4 | User cancelled | Only if asked |
| `initiated` | 3 | Started, not completed | Only for diagnostics |
| `awaiting_photo` | 2 | Waiting for photo upload | Only for diagnostics |
| `awaiting_lesson_plan` | 1 | Waiting for LP upload | Only for diagnostics |

Default KPI filter: `cs.status = 'completed'`
Exclude always: `cs.status != 'test_cleanup'`

## Key Columns — coaching_sessions

### Identity & Status
- `id` — primary key (STRING)
- `user_id` — FK to `RUMI_DB.users.id`
- `status` — session status (see Status Values above)
- `last_successful_step`, `failed_step`, `error_message`, `can_resume` — pipeline diagnostics

### Pipeline Timestamps
- `created_at` → `confirmed_at` → `transcription_started_at` → `transcription_completed_at` → `analysis_started_at` → `analysis_completed_at` → `completed_at`
- All TIMESTAMP type

### Coaching Content
- `transcript_text` — full lesson transcript (STRING, can be large)
- `analysis_data` — AI analysis output (JSON STRING — parse with `JSON_VALUE()` for structured queries)
- `lesson_plan_text`, `lesson_plan_excerpt` — LP being coached against
- `report_pdf_url` — generated PDF coaching report
- `voice_debrief_url`, `voice_debrief_duration_seconds` — AI voice debrief for teacher
- `prioritized_action` — key action item from AI analysis
- `agency_response` — teacher's reflection/response
- `classroom_photos`, `photo_analysis` — visual evidence (JSON STRING)

### Audio
- `audio_url`, `audio_duration_seconds`, `audio_format`, `audio_size_bytes`
- `transcript_language` — detected language

### Cost
- `transcription_cost`, `analysis_cost`, `total_cost` — per-session cost (FLOAT)
- `gpt5_input_tokens`, `gpt5_output_tokens`, `gpt5_cached_tokens` — token usage (FLOAT)

## Key Columns — coaching_quality_metrics

- `coaching_session_id` — FK to `coaching_sessions.id`
- `diarization_confidence` — audio quality score (FLOAT)
- `processing_time_seconds`, `transcription_time_seconds`, `analysis_time_seconds` — performance (INTEGER/INTEGER/INTEGER)
- `user_satisfaction_rating` — teacher rating (STRING — cast to FLOAT64 for aggregation)
- `user_feedback` — free text teacher feedback
- `session_cost` — cost from quality perspective (FLOAT)
- `had_errors` — BOOLEAN, whether errors occurred
- `retry_count` — INTEGER, number of retries

## Key Difference from ICT

- ICT AI coaching uses the **same observation stack** with `coaching_observationquestion.source = 'automated'`, scored via FICO B/C/D sections
- RWP AI coaching is a **completely separate audio-based system** — records classroom audio, transcribes, runs AI analysis, generates reports
- Cross-region AI coaching comparison: **session count** and **completion rate** only. Score/quality comparison is NOT valid.

## Counting Rules

- Session count = `COUNT(DISTINCT cs.id)` with appropriate status filter
- Completion rate = `COUNTIF(cs.status = 'completed') / COUNTIF(cs.status != 'test_cleanup')`
- Teachers with AI coaching = `COUNT(DISTINCT cs.user_id)`

## Aggregation Patterns

| User asks about | GROUP BY | Aggregate |
|-----------------|----------|-----------|
| Total sessions | — | `COUNT(DISTINCT cs.id)` |
| Sessions per teacher | `cs.user_id` | `COUNT(DISTINCT cs.id)` |
| Completion rate | — | `COUNTIF(status='completed') / COUNTIF(status!='test_cleanup')` |
| Avg processing time | — | `AVG(cqm.processing_time_seconds)` |
| Avg satisfaction | — | `AVG(CAST(cqm.user_satisfaction_rating AS FLOAT64))` |
| Total cost | — | `SUM(cs.total_cost)` |
| Avg cost per session | — | `AVG(cs.total_cost)` |
| Sessions by week | `DATE_TRUNC(cs.created_at, WEEK(SATURDAY))` | `COUNT(DISTINCT cs.id)` |
| Sessions by month | `DATE_TRUNC(cs.created_at, MONTH)` | `COUNT(DISTINCT cs.id)` |
| Error rate | — | `COUNTIF(cqm.had_errors) / COUNT(*)` |
| By status (diagnostics) | `cs.status` | `COUNT(DISTINCT cs.id)` |

## Data Conventions

- Timezone: `Asia/Karachi` for all date/timestamp conversions
- `analysis_data` is a JSON string — use `JSON_VALUE(cs.analysis_data, '$.key')` for structured access
- `user_satisfaction_rating` is stored as STRING — cast to FLOAT64 for numeric aggregation
- Weeks run Saturday to Friday (consistent with ICT convention)
```

- [ ] **Step 2: Copy to distribution location**

```bash
cp .claude/rules/rawalpindi/coaching/ai-coaching-rules.md src/taleemabad_data_mcp/rules/rawalpindi/coaching/ai-coaching-rules.md
```

- [ ] **Step 3: Commit**

```bash
git add .claude/rules/rawalpindi/coaching/ai-coaching-rules.md src/taleemabad_data_mcp/rules/rawalpindi/coaching/ai-coaching-rules.md
git commit -m "rules: add Rawalpindi AI coaching query rules"
```

---

### Task 6: Write AI Student Assessment Rules

**Files:**
- Create: `.claude/rules/rawalpindi/student_results/ai-assessment-rules.md`
- Create: `src/taleemabad_data_mcp/rules/rawalpindi/student_results/ai-assessment-rules.md`

- [ ] **Step 1: Write the rule file**

Write the following content to `.claude/rules/rawalpindi/student_results/ai-assessment-rules.md`:

```markdown
# AI Student Assessment Query Rules — Rawalpindi

## When These Rules Apply

User asks about:
- Student reading assessments in Rawalpindi
- WCPM (Words Correct Per Minute) scores
- Reading fluency or accuracy metrics
- Comprehension results
- Student reading levels or benchmarks
- AI-based student evaluation results

## Mandatory Clarifications

### Metric
Ask: "Which metric? WCPM, accuracy, comprehension, or all?"
- WCPM is the primary fluency metric
- `accuracy_percentage` for reading accuracy
- `comprehension_score` for understanding

### Aggregation Level
Ask: "Per student, per teacher, per school, or overall?"

### Grade Level
Ask: "Which grade level, or all?"
- `grade_level` (INTEGER) available for filtering

### Time Period
Ask: "Which time period?"
- `created_at` (TIMESTAMP) is the primary timestamp

## Key Tables

| Table | Role | Rows | Dataset |
|-------|------|------|---------|
| `RUMI_DB.reading_assessments` | Student reading assessment records | 277 | RUMI_DB |
| `RUMI_DB.users` | User bridge (teacher who administered) | 5,319 | RUMI_DB |
| `TaleemHub_DB.users` | RWP cohort filter | 1,296 | TaleemHub_DB |

**Note:** These tables are small and unpartitioned. Full scans are acceptable at this scale.

## Join Path (RWP Cohort Filter)

```sql
SELECT ...
FROM RUMI_DB.reading_assessments ra
JOIN RUMI_DB.users ru ON ra.user_id = ru.id
JOIN TaleemHub_DB.users th ON ru.phone_number = th.phone_number
WHERE ru.is_test_user IS NOT TRUE
  AND th.status = 'active'
  AND ra.status = 'completed'
```

## Status Values

| Status | Count | Meaning | Include in KPI? |
|--------|-------|---------|-----------------|
| `completed` | 142 | Fully processed | YES (default) |
| `passage_generated` | 63 | Passage created, not started | NO |
| `fluency_completed` | 40 | Fluency done, comprehension pending | Only if asked |
| `failed` | 19 | Processing failed | Only for diagnostics |
| `comprehension_completed` | 11 | Comprehension done, not fully completed | Only if asked |
| `abandoned` | 1 | Student/teacher abandoned | NO |
| `comprehension_in_progress` | 1 | Currently running | NO |

Default KPI filter: `ra.status = 'completed'`

## Key Columns — Core Reading Metrics

- `wcpm` — Words Correct Per Minute (FLOAT, primary fluency metric)
- `accuracy_percentage` — reading accuracy (FLOAT, 0-100)
- `words_read`, `words_correct` — raw counts (FLOAT)
- `total_words_in_passage` — passage length (FLOAT)
- `time_elapsed_seconds` — reading duration (FLOAT)
- `on_track` — BOOLEAN, whether student meets grade benchmark
- `grade_benchmark_min`, `grade_benchmark_max` — grade-level WCPM benchmarks (FLOAT)
- `percentile_rank` — position relative to peers (STRING — may need parsing)

## Key Columns — Comprehension

- `comprehension_score` — numeric comprehension result (FLOAT)
- `comprehension_questions` — JSON STRING, questions asked
- `comprehension_answers` — JSON STRING, student answers
- `comprehension_analysis` — JSON STRING, AI analysis of answers
- `comprehension_requested` — BOOLEAN, whether comprehension was part of this assessment

## Key Columns — Pronunciation & Prosody

- `pronunciation_accuracy` — numeric score (FLOAT)
- `pronunciation_data` — JSON STRING, detailed pronunciation analysis
- `prosody_analysis` — JSON STRING, speech rhythm/intonation analysis
- `errors` — JSON STRING, reading errors
- `self_corrections_count` — INTEGER, student self-corrections

## Key Columns — Assessment Context

- `grade_level` — INTEGER, student grade
- `language` — assessment language (STRING)
- `passage_type` — type of reading passage (STRING)
- `passage_text` — the actual passage (STRING)
- `assessment_mode` — how assessment was administered (STRING)
- `starting_level`, `final_level` — adaptive leveling (STRING)
- `level_attempts` — JSON STRING, attempts per level
- `student_identifier`, `student_number` — student identity within session

## Key Difference from ICT

- ICT student results - AI points to `tbproddb.student_learning_studentassessmentresult` but is flagged as **CONFLICT/not active**
- RWP has a **rich, active reading assessment system** with WCPM, accuracy, comprehension, adaptive leveling, pronunciation analysis
- Cross-region student AI results are **not comparable** until ICT activates its system

## Counting Rules

- Assessment count = `COUNT(DISTINCT ra.id)`
- Students assessed = `COUNT(DISTINCT ra.student_identifier)` (within teacher scope)
- Teachers who administered = `COUNT(DISTINCT ra.user_id)`

## Aggregation Patterns

| User asks about | GROUP BY | Aggregate |
|-----------------|----------|-----------|
| Total assessments | — | `COUNT(DISTINCT ra.id)` |
| Students assessed | — | `COUNT(DISTINCT ra.student_identifier)` |
| Avg WCPM | — | `AVG(ra.wcpm)` |
| Avg accuracy | — | `AVG(ra.accuracy_percentage)` |
| Avg comprehension | — | `AVG(ra.comprehension_score)` |
| On-track rate | — | `COUNTIF(ra.on_track) / COUNT(*)` |
| By grade | `ra.grade_level` | `AVG(ra.wcpm)`, `AVG(ra.accuracy_percentage)` |
| By teacher | `ra.user_id` | `COUNT(DISTINCT ra.id)`, `AVG(ra.wcpm)` |
| By school | `th.school_id`, `th.school_name` | `AVG(ra.wcpm)`, `COUNT(DISTINCT ra.id)` |
| By language | `ra.language` | `AVG(ra.wcpm)`, `COUNT(DISTINCT ra.id)` |
| Weekly trend | `DATE_TRUNC(ra.created_at, WEEK(SATURDAY))` | `COUNT(DISTINCT ra.id)`, `AVG(ra.wcpm)` |
| Monthly trend | `DATE_TRUNC(ra.created_at, MONTH)` | `COUNT(DISTINCT ra.id)`, `AVG(ra.wcpm)` |

## Data Conventions

- Timezone: `Asia/Karachi` for all date/timestamp conversions
- JSON fields (`comprehension_questions`, `pronunciation_data`, etc.) — use `JSON_VALUE()` or `JSON_QUERY()` for structured access
- `percentile_rank` is stored as STRING — cast or parse as needed
- Weeks run Saturday to Friday (consistent with ICT convention)
```

- [ ] **Step 2: Copy to distribution location**

```bash
cp .claude/rules/rawalpindi/student_results/ai-assessment-rules.md src/taleemabad_data_mcp/rules/rawalpindi/student_results/ai-assessment-rules.md
```

- [ ] **Step 3: Commit**

```bash
git add .claude/rules/rawalpindi/student_results/ai-assessment-rules.md src/taleemabad_data_mcp/rules/rawalpindi/student_results/ai-assessment-rules.md
git commit -m "rules: add Rawalpindi AI student assessment query rules"
```

---

### Task 7: Write Human Student Assessment Rules (DRAFT)

**Files:**
- Create: `.claude/rules/rawalpindi/student_results/human-assessment-rules.md`
- Create: `src/taleemabad_data_mcp/rules/rawalpindi/student_results/human-assessment-rules.md`

- [ ] **Step 1: Write the rule file**

Write the following content to `.claude/rules/rawalpindi/student_results/human-assessment-rules.md`:

```markdown
# Human Student Assessment (ASER) Query Rules — Rawalpindi

> **STATUS: DRAFT** — Pending Ahwaz verification of rubric_item_id, status_id, and subject_id mappings. Do not use for production reporting until verified.

## When These Rules Apply

User asks about:
- ASER assessment results in Rawalpindi
- Human-administered student evaluations
- Coach-led student assessments
- Rubric item scores or levels

## Mandatory Clarifications

### Grain
Ask: "Assessment count (per student session) or rubric-level results (per item scored)?"
- 93 assessment sessions vs 264 rubric item scores — different grains

### Subject
Ask: "Which subject, or all?"
- `subject_id` available but mapping TBD

### Aggregation Level
Ask: "Per student, per school, per assessor, or overall?"

## Key Tables

| Table | Role | Rows | Dataset |
|-------|------|------|---------|
| `TaleemHub_DB.aser_assessment_results` | Individual rubric item scores | 264 | TaleemHub_DB |
| `TaleemHub_DB.aser_assessments` | Assessment sessions (one per student per subject) | 93 | TaleemHub_DB |
| `TaleemHub_DB.aser_student_profiles` | Student identity and school | 33 | TaleemHub_DB |
| `TaleemHub_DB.users` | Assessor identity | 1,296 | TaleemHub_DB |

**Note:** These tables are small and unpartitioned. Full scans are acceptable at this scale.

## Join Path

```sql
SELECT ...
FROM TaleemHub_DB.aser_assessment_results aar
JOIN TaleemHub_DB.aser_assessments aa ON aar.assessment_id = aa.id
JOIN TaleemHub_DB.aser_student_profiles asp ON aa.student_profile_id = asp.id
LEFT JOIN TaleemHub_DB.users u ON aa.created_by_user_id = u.id
```

## Count Clarification (93 vs 264)

- **93 assessments** = unique assessment sessions (`aser_assessments`), one per student per subject
- **264 results** = rubric item scores (`aser_assessment_results`), multiple rubric items per assessment
- These are different grains, NOT a data conflict
- For session count KPIs: `COUNT(DISTINCT aa.id)`
- For rubric detail: `COUNT(DISTINCT aar.id)`

## Key Columns

### aser_assessment_results
- `id` — primary key (STRING)
- `assessment_id` — FK to `aser_assessments.id`
- `rubric_item_id` — which ASER rubric item (STRING — **mapping TBD, needs verification**)
- `status_id` — score/outcome for this item (STRING — **mapping TBD, needs verification**)
- `created_at` — timestamp (STRING)

### aser_assessments
- `id` — primary key (STRING)
- `student_profile_id` — FK to `aser_student_profiles.id`
- `subject_id` — which subject (STRING — **mapping TBD, needs verification**)
- `notes` — assessor notes (STRING)
- `created_by_user_id` — FK to `TaleemHub_DB.users.id` (the coach/assessor)
- `created_at`, `updated_at` — timestamps (STRING)

### aser_student_profiles
- `id` — primary key (STRING)
- `student_name`, `student_name_normalized` — student identity
- `school_id` — FK for school-level rollups (STRING)
- `grade_level` — student grade (INTEGER)
- `created_at` — timestamp (STRING)

## Verification Needed (before removing DRAFT)

1. **`rubric_item_id` mapping** — What ASER levels do values represent? (e.g., Nothing, Letter, Word, Sentence, Story)
2. **`status_id` mapping** — What scores/outcomes do values mean? (e.g., passed, failed, partial)
3. **`subject_id` mapping** — What subjects exist? (e.g., Urdu reading, Math, English)
4. **Count reconciliation** — Verify 93 assessments / 264 results with Ahwaz

Run these discovery queries:
```sql
SELECT DISTINCT rubric_item_id, COUNT(*) FROM TaleemHub_DB.aser_assessment_results GROUP BY rubric_item_id
SELECT DISTINCT status_id, COUNT(*) FROM TaleemHub_DB.aser_assessment_results GROUP BY status_id
SELECT DISTINCT subject_id, COUNT(*) FROM TaleemHub_DB.aser_assessments GROUP BY subject_id
```

## Key Difference from ICT

- ICT student results - coaches is **DEPRECATED** per CEO doc
- ICT ASER uses **ODK tables** (`odk.NIETE_-_ICT_-_IMPACT_ICT-ENDLINE-ASER_1-3_Test`) — completely different structure
- Cross-region: **volume comparison only** until RWP rubric mapping is confirmed

## Aggregation Patterns

| User asks about | GROUP BY | Aggregate |
|-----------------|----------|-----------|
| Total assessments | — | `COUNT(DISTINCT aa.id)` |
| Students assessed | — | `COUNT(DISTINCT asp.id)` |
| Results per student | `asp.id`, `asp.student_name` | `COUNT(DISTINCT aar.id)` |
| By school | `asp.school_id` | `COUNT(DISTINCT aa.id)` |
| By grade | `asp.grade_level` | `COUNT(DISTINCT aa.id)` |
| By subject | `aa.subject_id` | `COUNT(DISTINCT aa.id)` |
| By assessor | `aa.created_by_user_id` | `COUNT(DISTINCT aa.id)` |

## Data Conventions

- Timezone: `Asia/Karachi` for all date conversions
- All ID columns are STRING type
- Timestamps are stored as STRING — cast with `PARSE_TIMESTAMP` or `PARSE_DATE` as needed
```

- [ ] **Step 2: Copy to distribution location**

```bash
cp .claude/rules/rawalpindi/student_results/human-assessment-rules.md src/taleemabad_data_mcp/rules/rawalpindi/student_results/human-assessment-rules.md
```

- [ ] **Step 3: Commit**

```bash
git add .claude/rules/rawalpindi/student_results/ src/taleemabad_data_mcp/rules/rawalpindi/student_results/
git commit -m "rules: add Rawalpindi student assessment query rules (AI + human DRAFT)"
```

---

### Task 8: Update index.md

**Files:**
- Modify: `.claude/rules/index.md`
- Modify: `src/taleemabad_data_mcp/rules/index.md`

- [ ] **Step 1: Update `.claude/rules/index.md`**

Replace the Punjab/RWP section (lines 44-45):

```
## Region: Punjab/RWP (`punjab-rwp/`)
Not yet available. Will follow same domain structure when added.
```

With:

```markdown
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
```

Also update Step 1 (line 13):

Replace: `- Punjab/RWP → read `punjab-rwp/` (not yet available)`
With: `- Rawalpindi → read `rawalpindi/``

Also add cross-region section before BigQuery Context:

```markdown
## Cross-Region KPI Comparability

Cross-region comparison is limited to **volume and coverage metrics**. Qualitative comparison (scores, outcomes) is NOT valid because regions use fundamentally different tools and scoring frameworks.

| KPI | ICT Source | RWP Source | Comparable Metric |
|-----|-----------|-----------|-------------------|
| User data | user_school_profiles | TaleemHub_DB.users | Teacher count, cohort size |
| Lesson plans | events_partitioned | RUMI_DB.lesson_plans | Volume only |
| Coaching - Human | coaching_observation (scored) | mentoring_visits (narrative) | Session count + coverage % |
| Coaching - AI | observation stack (automated) | coaching_sessions | Session count + completion rate |
| Student results - AI | not active | reading_assessments | Not comparable yet |
| Student results - Human | ODK ASER | TaleemHub ASER | Volume only |
| Training | teacher_training_level | Not in scope | ICT only |
```

- [ ] **Step 2: Copy updated index.md to distribution location**

```bash
cp .claude/rules/index.md src/taleemabad_data_mcp/rules/index.md
```

- [ ] **Step 3: Verify both index files match**

```bash
diff .claude/rules/index.md src/taleemabad_data_mcp/rules/index.md
```

Expected: no differences

- [ ] **Step 4: Commit**

```bash
git add .claude/rules/index.md src/taleemabad_data_mcp/rules/index.md
git commit -m "rules: update index with Rawalpindi region routing and cross-region comparability"
```

---

### Task 9: Final Verification

- [ ] **Step 1: Verify all rule files exist in both locations**

```bash
echo "=== .claude/rules/rawalpindi ===" && find .claude/rules/rawalpindi -name "*.md" | sort
echo "=== src/rules/rawalpindi ===" && find src/taleemabad_data_mcp/rules/rawalpindi -name "*.md" | sort
```

Expected: 6 rule files in each location

- [ ] **Step 2: Verify files are identical between locations**

```bash
diff -r .claude/rules/rawalpindi src/taleemabad_data_mcp/rules/rawalpindi
```

Expected: no differences

- [ ] **Step 3: Verify index.md references match actual files**

```bash
grep -c "rawalpindi" .claude/rules/index.md
```

Expected: multiple matches (region header + each domain subsection)

- [ ] **Step 4: Run git log to verify all commits**

```bash
git log --oneline -10
```

Expected: 7 commits (1 directory setup + 6 rule files/index)
