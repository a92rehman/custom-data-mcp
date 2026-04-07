# Rawalpindi Region Rules — Design Spec

**Date:** 2026-04-07
**Status:** Approved (post-review fixes applied)
**Scope:** Write governed query rules for Rawalpindi region covering 6 KPIs + 1 dimension, update index.md with cross-region comparison guide

## Context

Taleemabad operates across 5+ regions with different tools. ICT/Islamabad rules exist (4 domains, single `tbproddb` dataset). Rawalpindi uses a fundamentally different stack: `RUMI_DB` (AI teaching companion) + `TaleemHub_DB` (school management/coaching platform), joined via `phone_number`.

The CEO's reconciled KPI document defines 8 comparable KPIs across regions. Each region implements these against different tables, but business definitions stay the same.

## Theory of Change Alignment

- **Teach Well** (lesson plans + teacher support) → LP generation KPI + coaching KPIs
- **Improve** (observations + coaching feedback) → coaching results + student results KPIs
- **Sensors** (observation + assessment streams) → student results KPIs
- Cross-region comparability enables 70/20/10 focus and truth-over-noise discipline

## Approach: KPI-Aligned Structure (Approach B)

```
rawalpindi/
  dimensions/users/user-query-rules.md
  lesson_plans/lp-query-rules.md
  coaching/human-coaching-rules.md
  coaching/ai-coaching-rules.md
  student_results/ai-assessment-rules.md
  student_results/human-assessment-rules.md    # DRAFT
```

Each rule file maps to exactly one KPI from the CEO doc. Auditable 1:1.

## Design Assumptions

1. `TaleemHub_DB.users` is the canonical Rawalpindi teacher roster (1,296 rows)
2. `RUMI_DB.users` (5,319 rows) is a superset; RWP teachers are a subset identified by existence in TaleemHub
3. `phone_number` is the universal join key between TaleemHub and Rumi
4. `mentoring_visits` and `monitoring_visits` are separate tables (A = coaching, B = infra/compliance)
5. Student results - human assessment has a count conflict (93 vs 264) pending Ahwaz verification
6. Teacher training is NOT in scope for RWP — CEO doc does not include training KPIs for this region

## Conventions

- **Timezone:** `Asia/Karachi` for all date conversions (same as ICT)
- **Partition policy:** All RWP tables are small (<5,000 rows, <60 MB). They are unpartitioned — logged as partition debt per bigquery.md rules. Full scans are acceptable at this scale but should be revisited if tables grow beyond 10,000 rows.
- **Directory name:** `rawalpindi/` (not `punjab-rwp/` — scope is Rawalpindi district specifically, not all of Punjab)
- **Rules sync:** Rule files must be created in both `.claude/rules/rawalpindi/` and `src/taleemabad_data_mcp/rules/rawalpindi/` for distribution via the `setup` CLI command.

## Region Filter Strategy

`TaleemHub_DB.users` currently contains only Rawalpindi users. However, if TaleemHub expands to other regions in the future, an explicit filter will be needed. Recommended approach:
- **Now:** Treat `TaleemHub_DB.users` as RWP-only (confirmed by team)
- **Future-proofing:** If a `district_id` or `region` column reliably identifies Rawalpindi, add it as a required filter. Monitor for multi-region expansion.
- **RUMI_DB.users:** Has `region` and `organization` columns — use these to filter RWP users when querying Rumi directly (without TaleemHub join)

---

## Section 1: User Dimension Rules

**File:** `rawalpindi/dimensions/users/user-query-rules.md`

### When These Rules Apply
User asks about: Rawalpindi teacher profiles, user counts, school assignments, cohort size, teacher roster, Rumi-TaleemHub user matching.

### Tables
| Table | Role | Rows |
|-------|------|------|
| `TaleemHub_DB.users` | Canonical teacher roster | 1,296 |
| `RUMI_DB.users` | Join helper for Rumi data | 5,319 |

### Key Columns — TaleemHub_DB.users
- `id` — primary key
- `name`, `phone_number`, `cnic` — identity
- `role` — user type (teacher/mentor/admin)
- `status` — active filter
- `school_id`, `school_name` — school assignment
- `district_id`, `tehsil_id`, `tehsil_name`, `markaz_id`, `markaz_name` — geographic hierarchy
- `role_id` — numeric role identifier
- `created_at`, `date_of_joining` — temporal

### Key Columns — RUMI_DB.users
- `id` — primary key (Rumi user ID)
- `phone_number` — join key to TaleemHub
- `is_test_user` — must exclude `true`
- `region`, `organization` — Rumi-side context
- `registration_completed` — whether fully onboarded

### Join Logic
```sql
TaleemHub_DB.users th
JOIN RUMI_DB.users ru ON th.phone_number = ru.phone_number
WHERE ru.is_test_user IS NOT TRUE
```

### Required Filters
- Filter by `role` for teacher-only queries
- Filter by `status` for active users
- Exclude `RUMI_DB.users.is_test_user = true` when joining

### Mandatory Clarifications
- "Which role? Teachers only, mentors, or all?"
- "All Rawalpindi, or specific tehsil/markaz?"

### Verification Query
Count teachers in TaleemHub with vs without Rumi match (phone_number) to confirm roster completeness assumption.

---

### Aggregation Patterns

| User asks about | GROUP BY | Aggregate |
|-----------------|----------|-----------|
| Total teachers | — | `COUNT(DISTINCT th.id)` |
| Teachers per school | `school_id`, `school_name` | `COUNT(DISTINCT th.id)` |
| Teachers per tehsil/markaz | `tehsil_name`, `markaz_name` | `COUNT(DISTINCT th.id)` |
| Teachers with Rumi match | — | `COUNT(DISTINCT th.id) WHERE ru.id IS NOT NULL` |
| Teachers by role | `role` | `COUNT(DISTINCT th.id)` |

---

## Section 2: Lesson Plan Rules

**File:** `rawalpindi/lesson_plans/lp-query-rules.md`

### When These Rules Apply
User asks about: AI lesson plan generation in Rawalpindi, LP counts, LP volume by grade/subject, teacher LP activity.

### Tables
| Table | Role | Rows |
|-------|------|------|
| `RUMI_DB.lesson_plans` | AI-generated lesson plans | 4,759 |
| `RUMI_DB.users` | User bridge | 5,319 |
| `TaleemHub_DB.users` | RWP cohort filter | 1,296 |

### Key Columns — RUMI_DB.lesson_plans
- `id` — primary key, use `COUNT(DISTINCT id)` for LP count
- `user_id` — FK to `RUMI_DB.users.id`
- `topic`, `grade`, `subject` — LP content metadata
- `type`, `source`, `lp_variant` — LP categorization
- `ab_group` — A/B test segmentation
- `created_at` (DATETIME) — timestamp for aggregation

### Join Path (RWP cohort filter)
```sql
RUMI_DB.lesson_plans lp
JOIN RUMI_DB.users ru ON lp.user_id = ru.id
JOIN TaleemHub_DB.users th ON ru.phone_number = th.phone_number
WHERE ru.is_test_user IS NOT TRUE
```

### Counting Rules
- LP count = `COUNT(DISTINCT lp.id)` — never count raw rows
- Unique teachers = `COUNT(DISTINCT lp.user_id)`

### Key Difference from ICT
- ICT counts LP **starts and completions** from events, computes `lp_ratio` (completion rate) against timetable
- RWP counts **generated records** — one row = one AI-generated LP delivered
- No timetable data → no completion rate or On-Schedule/Off-Schedule concept
- Cross-region LP comparison is **volume only**

### Reporting Grain
Daily / Weekly / Monthly, with optional grade/subject breakdown

### Aggregation Patterns

| User asks about | GROUP BY | Aggregate |
|-----------------|----------|-----------|
| Total LPs generated | — | `COUNT(DISTINCT lp.id)` |
| LPs per teacher | `lp.user_id` | `COUNT(DISTINCT lp.id)` |
| LPs per school | `th.school_id`, `th.school_name` | `COUNT(DISTINCT lp.id)` |
| LPs by grade/subject | `lp.grade`, `lp.subject` | `COUNT(DISTINCT lp.id)` |
| Daily/weekly/monthly trend | `DATE(lp.created_at)` or week/month | `COUNT(DISTINCT lp.id)` |
| Active LP teachers | — | `COUNT(DISTINCT lp.user_id)` |

### Mandatory Clarifications
- "Which time period?"
- "Breakdown by grade/subject, or total count?"

---

## Section 3: Human Coaching Rules

**File:** `rawalpindi/coaching/human-coaching-rules.md`

### When These Rules Apply
User asks about: Rawalpindi human coaching/mentoring visits, observation feedback, teacher coverage by mentors, coaching results text.

### Tables
| Table | Role | Rows |
|-------|------|------|
| `TaleemHub_DB.mentoring_visits` | Human coaching visits | 95 |
| `TaleemHub_DB.users` | Observer/mentor identity | 1,296 |

**Explicitly NOT:** `TaleemHub_DB.monitoring_visits` (separate table, infra/compliance only)

### Key Columns — TaleemHub_DB.mentoring_visits
- `id` — primary key, `COUNT(DISTINCT id)` for session count
- `user_id` — FK to `TaleemHub_DB.users.id` (the observer/mentor)
- `observer_name`, `observer_designation` — observer identity
- `teacher_name`, `teacher_cnic` — observed teacher (string match, no FK)
- `school_id`, `school_name` — school context
- `visit_date` — date for time-based aggregation
- `arrival_time`, `departure_time` — visit duration
- `class_observed`, `grade_observed`, `subject` — classroom context
- `markaz`, `tehsil` — geographic hierarchy
- `status` — visit status (clarify valid values)
- `rubric_type` — may indicate future structured rubrics

### Coaching Results Fields (all inline, unstructured narrative)
- `general_feedback` — free text overall feedback
- `strengths_observed` — what went well
- `areas_for_improvement` — what needs work
- `action_items` — next steps for teacher
- `evidence` — supporting evidence/notes
- `voice_note_transcription` — transcribed voice notes
- `voice_note_url` — audio evidence
- `tm_notes` — team manager notes

### Geo-verification
- `captured_latitude`, `captured_longitude`, `captured_location_source` — visit location proof

### Key Difference from ICT
- ICT has **structured scoring** — questions with yes/partial/no, numeric scores, FICO sections B/C/D
- RWP is **unstructured narrative** — free text feedback, no numeric scores, no sections
- Cross-region coaching comparison: **volume** (session count) and **coverage** (% teachers observed) only. NOT score-based.

### Required Filters
- `status` — filter for valid/submitted visits (exact valid values TBD during implementation — query `SELECT DISTINCT status FROM TaleemHub_DB.mentoring_visits` to enumerate)
- `visit_date` for time range

### Teacher Matching Note
`teacher_name` and `teacher_cnic` are string fields with no FK to the users table. CNIC format may vary (with/without dashes). For reliable teacher-level aggregation, prefer `teacher_cnic` over `teacher_name` (names have spelling variations). If CNIC matching proves unreliable, flag as a data quality gap.

### Aggregation Patterns

| User asks about | GROUP BY | Aggregate |
|-----------------|----------|-----------|
| Total visits | — | `COUNT(DISTINCT id)` |
| Visits per school | `school_id`, `school_name` | `COUNT(DISTINCT id)` |
| Visits per observer | `user_id`, `observer_name` | `COUNT(DISTINCT id)` |
| Visits per teacher | `teacher_cnic` | `COUNT(DISTINCT id)` |
| Teacher coverage | — | `COUNT(DISTINCT teacher_cnic) / total_teachers` |
| Visits per tehsil/markaz | `tehsil`, `markaz` | `COUNT(DISTINCT id)` |
| Weekly/monthly trend | `DATE(visit_date)` or week/month | `COUNT(DISTINCT id)` |

### Mandatory Clarifications
- "Session count, or detailed coaching results?"
- "Which time period?"
- "Per school, per observer, per teacher, or overall?"

---

## Section 4: AI Coaching Rules

**File:** `rawalpindi/coaching/ai-coaching-rules.md`

### When These Rules Apply
User asks about: Rawalpindi AI coaching sessions, audio coaching analysis, coaching quality metrics, AI coaching costs, teacher satisfaction with AI coaching.

### Tables
| Table | Role | Rows |
|-------|------|------|
| `RUMI_DB.coaching_sessions` | AI coaching session records | 170 |
| `RUMI_DB.coaching_quality_metrics` | Quality/performance metrics | 125 |
| `RUMI_DB.users` | User bridge | 5,319 |
| `TaleemHub_DB.users` | RWP cohort filter | 1,296 |

### Join
- `coaching_quality_metrics.coaching_session_id` → `coaching_sessions.id`
- `coaching_sessions.user_id` → `RUMI_DB.users.id` → `phone_number` → TaleemHub cohort

### Key Columns — coaching_sessions
**Identity & status:**
- `id` — primary key
- `user_id` — FK to RUMI_DB.users
- `status` — session status (completed/failed/in_progress/pending)
- `last_successful_step`, `failed_step`, `error_message`, `can_resume` — pipeline diagnostics

**Pipeline timestamps:**
- `created_at` → `confirmed_at` → `transcription_started_at` → `transcription_completed_at` → `analysis_started_at` → `analysis_completed_at` → `completed_at`

**Coaching content:**
- `transcript_text` — full lesson transcript
- `analysis_data` — AI analysis (JSON string)
- `lesson_plan_text`, `lesson_plan_excerpt` — LP being coached against
- `report_pdf_url` — generated coaching report
- `voice_debrief_url`, `voice_debrief_duration_seconds` — AI voice debrief
- `prioritized_action` — key action item from analysis
- `agency_response` — teacher's reflection
- `classroom_photos`, `photo_analysis` — visual evidence

**Cost:**
- `transcription_cost`, `analysis_cost`, `total_cost`
- `gpt5_input_tokens`, `gpt5_output_tokens`, `gpt5_cached_tokens`

### Key Columns — coaching_quality_metrics
- `coaching_session_id` — FK to coaching_sessions
- `diarization_confidence` — audio quality
- `processing_time_seconds`, `transcription_time_seconds`, `analysis_time_seconds`
- `user_satisfaction_rating`, `user_feedback`
- `session_cost`, `had_errors`, `retry_count`

### Counting Rules
- Session count = `COUNT(DISTINCT cs.id)` where `status = 'completed'` (default)
- Completion rate = `COUNT(completed) / COUNT(total)`

### Key Difference from ICT
- ICT AI coaching = same observation stack with `source='automated'`, scored via FICO B/C/D
- RWP AI coaching = separate audio-based system with transcription + AI analysis pipeline
- Cross-region: **volume** (session count) + **completion rate** only

### Status Values
- `status` on `coaching_sessions` — exact values TBD during implementation. Query `SELECT DISTINCT status FROM RUMI_DB.coaching_sessions` to enumerate. Expected: `completed`, `failed`, `in_progress`, `pending`.
- Default KPI reporting: `status = 'completed'` only

### Aggregation Patterns

| User asks about | GROUP BY | Aggregate |
|-----------------|----------|-----------|
| Total sessions | — | `COUNT(DISTINCT cs.id)` |
| Sessions per teacher | `cs.user_id` | `COUNT(DISTINCT cs.id)` |
| Completion rate | — | `COUNT(completed) / COUNT(total)` |
| Avg processing time | — | `AVG(cqm.processing_time_seconds)` |
| Avg satisfaction | — | `AVG(CAST(cqm.user_satisfaction_rating AS FLOAT64))` |
| Cost per session | — | `AVG(cs.total_cost)` |
| Sessions by week/month | `DATE(cs.created_at)` or week/month | `COUNT(DISTINCT cs.id)` |
| Error rate | — | `COUNT(had_errors=TRUE) / COUNT(total)` |

### Mandatory Clarifications
- "Session count, results, or quality metrics?"
- "All sessions or completed only?"
- "Which time period?"

---

## Section 5: Student Results — AI Assessment Rules

**File:** `rawalpindi/student_results/ai-assessment-rules.md`

### When These Rules Apply
User asks about: Rawalpindi student reading assessments, WCPM scores, reading fluency, comprehension results, student reading levels, AI-based student evaluation.

### Tables
| Table | Role | Rows |
|-------|------|------|
| `RUMI_DB.reading_assessments` | Student reading assessments | 277 |
| `RUMI_DB.users` | User bridge (teacher who administered) | 5,319 |
| `TaleemHub_DB.users` | RWP cohort filter | 1,296 |

### Join Path
- `reading_assessments.user_id` → `RUMI_DB.users.id` → `phone_number` → TaleemHub cohort

### Key Columns — Core Reading Metrics
- `wcpm` — Words Correct Per Minute (primary fluency metric)
- `accuracy_percentage` — reading accuracy
- `words_read`, `words_correct`, `total_words_in_passage`
- `time_elapsed_seconds` — reading duration
- `on_track` — boolean benchmark indicator
- `grade_benchmark_min`, `grade_benchmark_max`
- `percentile_rank`

### Comprehension
- `comprehension_score` — numeric
- `comprehension_questions`, `comprehension_answers`, `comprehension_analysis` — JSON strings

### Pronunciation & Prosody
- `pronunciation_accuracy` — numeric
- `pronunciation_data`, `prosody_analysis` — JSON strings
- `errors`, `self_corrections_count`

### Assessment Context
- `grade_level`, `language`, `passage_type`, `passage_text`
- `assessment_mode` — administration mode
- `starting_level`, `final_level`, `level_attempts`, `auto_level_history` — adaptive leveling
- `student_identifier`, `student_number` — student identity within session

### Status & Timestamps
- `status` — filter to completed
- `created_at`, `completed_at`

### Counting Rules
- Assessment count = `COUNT(DISTINCT id)`
- Students assessed = `COUNT(DISTINCT student_identifier)` (within teacher scope)

### Key Difference from ICT
- ICT student results - AI is **CONFLICT/not active**
- RWP has active reading assessment with rich metrics
- Cross-region not comparable until ICT activates

### Reporting Grain
Per assessment + class aggregates (by teacher/school via TaleemHub join)

### Aggregation Patterns

| User asks about | GROUP BY | Aggregate |
|-----------------|----------|-----------|
| Total assessments | — | `COUNT(DISTINCT ra.id)` |
| Students assessed | — | `COUNT(DISTINCT ra.student_identifier)` |
| Avg WCPM | — | `AVG(ra.wcpm)` |
| Avg accuracy | — | `AVG(ra.accuracy_percentage)` |
| On-track rate | — | `COUNT(on_track=TRUE) / COUNT(total)` |
| By grade | `ra.grade_level` | `AVG(ra.wcpm)`, `AVG(ra.accuracy_percentage)` |
| By teacher | `ra.user_id` | `COUNT(DISTINCT ra.id)`, `AVG(ra.wcpm)` |
| By school | `th.school_id`, `th.school_name` | `AVG(ra.wcpm)` |
| Weekly/monthly trend | `DATE(ra.created_at)` or week/month | `COUNT(DISTINCT ra.id)` |

### Mandatory Clarifications
- "Which metric? WCPM, accuracy, comprehension, or all?"
- "Per student, per teacher, per school, or overall?"
- "Which grade level?"
- "Which time period?"

---

## Section 6: Student Results — Human Assessment Rules (DRAFT)

**File:** `rawalpindi/student_results/human-assessment-rules.md`
**Status:** DRAFT — pending Ahwaz verification

### When These Rules Apply
User asks about: Rawalpindi ASER assessment results, human-administered student evaluations, coach-led student assessments, rubric scores.

### Tables
| Table | Role | Rows |
|-------|------|------|
| `TaleemHub_DB.aser_assessment_results` | Rubric item scores | 264 |
| `TaleemHub_DB.aser_assessments` | Assessment sessions | 93 |
| `TaleemHub_DB.aser_student_profiles` | Student identity | 33 |

### Join Path
- `aser_assessment_results.assessment_id` → `aser_assessments.id`
- `aser_assessments.student_profile_id` → `aser_student_profiles.id`
- `aser_assessments.created_by_user_id` → `TaleemHub_DB.users.id` (administering coach)
- `aser_student_profiles.school_id` → school rollups

### Key Columns
**aser_assessment_results:**
- `id`, `assessment_id`, `rubric_item_id`, `status_id`, `created_at`

**aser_assessments:**
- `id`, `student_profile_id`, `subject_id`, `notes`, `created_by_user_id`, `created_at`

**aser_student_profiles:**
- `id`, `student_name`, `school_id`, `grade_level`, `created_at`

### Count Clarification (93 vs 264)
- 93 = unique assessment sessions (one per student per subject)
- 264 = rubric item scores within those sessions (multiple items per assessment)
- These are different grains, not a conflict

### Verification Needed (before removing DRAFT)
- `rubric_item_id` mapping — what ASER levels do values represent?
- `status_id` mapping — what scores/outcomes do values mean?
- `subject_id` mapping — what subjects exist?
- Reconcile count with Ahwaz

### Key Difference from ICT
- ICT student results - coaches is **DEPRECATED**
- ICT ASER uses **ODK tables** (different structure entirely)
- Cross-region: **volume only** until rubric mapping confirmed

### Aggregation Patterns

| User asks about | GROUP BY | Aggregate |
|-----------------|----------|-----------|
| Total assessments | — | `COUNT(DISTINCT aa.id)` |
| Students assessed | — | `COUNT(DISTINCT asp.id)` |
| Results per student | `asp.id`, `asp.student_name` | `COUNT(DISTINCT aar.id)` |
| By school | `asp.school_id` | `COUNT(DISTINCT aa.id)` |
| By grade | `asp.grade_level` | `COUNT(DISTINCT aa.id)` |
| By subject | `aa.subject_id` | `COUNT(DISTINCT aa.id)` |
| By assessor | `aa.created_by_user_id` | `COUNT(DISTINCT aa.id)` |

### Mandatory Clarifications
- "Assessment count or rubric-level results?"
- "Per student, per school, or overall?"
- "Which subject?"

---

## Section 7: Index.md Updates

### New Region Block
Add Rawalpindi under existing ICT block with dataset info, join key, and domain routing.

### Cross-Region KPI Comparability Matrix

| KPI | ICT Source | RWP Source | Comparable Metric |
|-----|-----------|-----------|-------------------|
| User data (dimension) | tbproddb.user_school_profiles | TaleemHub_DB.users | Teacher count, cohort size |
| Lesson plans | events_partitioned (start/complete) | RUMI_DB.lesson_plans (generated) | Volume only — ICT has completion rate, RWP has generation count |
| Coaching - Human | coaching_observation (scored B/C/D) | mentoring_visits (narrative) | Session count + coverage % only |
| Coaching - AI | observation stack source='automated' | RUMI_DB.coaching_sessions | Session count + completion rate only |
| Student results - AI | CONFLICT/not active | reading_assessments (WCPM) | Not comparable yet |
| Student results - Human | DEPRECATED / ODK ASER | TaleemHub ASER | Volume only |
| Training | teacher_training_level + assessment | Not in scope | ICT only — no RWP equivalent |

**Cross-region principle:** Comparison is limited to volume and coverage metrics. Qualitative comparison (scores, outcomes) is NOT valid because regions use fundamentally different tools and scoring frameworks. Rules must make this explicit.

---

## Implementation Notes

### File Creation Order
Each rule file must be created in both locations:
- `.claude/rules/rawalpindi/` (dev copy, auto-loaded by Claude Code)
- `src/taleemabad_data_mcp/rules/rawalpindi/` (distribution copy, installed via `setup` CLI)

Files:
1. `rawalpindi/dimensions/users/user-query-rules.md`
2. `rawalpindi/lesson_plans/lp-query-rules.md`
3. `rawalpindi/coaching/human-coaching-rules.md`
4. `rawalpindi/coaching/ai-coaching-rules.md`
5. `rawalpindi/student_results/ai-assessment-rules.md`
6. `rawalpindi/student_results/human-assessment-rules.md`
7. Update `index.md` (both locations) — change `punjab-rwp/` reference to `rawalpindi/`

### Status Value Discovery
During implementation, run these queries to enumerate actual status values:
- `SELECT DISTINCT status, COUNT(*) FROM TaleemHub_DB.users GROUP BY status`
- `SELECT DISTINCT status, COUNT(*) FROM TaleemHub_DB.mentoring_visits GROUP BY status`
- `SELECT DISTINCT status, COUNT(*) FROM RUMI_DB.coaching_sessions GROUP BY status`
- `SELECT DISTINCT status, COUNT(*) FROM RUMI_DB.reading_assessments GROUP BY status`
- `SELECT DISTINCT role, COUNT(*) FROM TaleemHub_DB.users GROUP BY role`

### What This Does NOT Cover
- Student results - enumerators (TBD, ETA Apr 20)
- Student results - EGRA/EGMA (TBD)
- Moawin/Akhuwat region rules (separate spec needed)
- ICT rule updates for missing KPIs (separate spec needed)
- MCP server code changes (implementation phase)
