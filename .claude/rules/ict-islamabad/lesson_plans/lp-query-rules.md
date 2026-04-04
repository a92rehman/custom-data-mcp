---
paths:
  - "src/**/*.py"
  - "tests/**/*.py"
---

# Lesson Plan Query Rules

## What LP Queries Produce

One row per **teacher x week x grade x subject** containing:
- Scheduled classes (`max_classes`)
- LPs started and completed, split by type (Core / User Generated)
- `lp_ratio` — completion rate capped at 1.0
- `lp_status_category` — On-Schedule / Moderate / Off-Schedule

## LP Status Categories

| Category | Condition | Meaning |
|----------|-----------|---------|
| On-Schedule | `lp_ratio >= 0.60` | Teacher completed LPs for 60%+ of scheduled classes |
| Moderate | `lp_ratio >= 0.40` | Completed 40–59% |
| Off-Schedule | `lp_ratio < 0.40` | Completed fewer than 40% |

Formula: `lp_ratio = LEAST((userGen_lp_completed + core_lp_completed) / max_classes, 1)`

## Mandatory Clarifications

### Session
Always ask: "Which academic session?"
- Session 2024-25: `session_id = 1`
- Session 2025-26: `session_id = 2`, starts 2025-04-19
- Never hardcode session dates — parameterize based on session_id
- Filter: `WHERE session_id = <session_id>` and `week_start >= DATE('<session_start>')`

### LP Type
Ask if relevant: "Core lesson plans, User Generated, or both?"
- Core = curriculum-aligned LPs from the platform
- User Generated = teacher-created via `userGenLessonPlanGenerate` event
- Default: both combined (most common ask)

### Aggregation Level
Ask: "Per teacher, per school, per week, or overall?"
- Raw data is per teacher x week x grade x subject
- Aggregate up based on user's need

## LP Types — How They Differ

### Core Lesson Plans
- Events: `lessonLessonStarted` (start) / `lessonLessonCompleted` (complete)
- LP ID: `JSON_VALUE(properties, '$.ep_lp_id')`
- Grade/subject: via `ep_gradesubject_id` → `slo_gradesubject` → `slo_grade` + `slo_subject`
- Start and complete matched on: `user_id + lp_id + grade_subject`

### User Generated Lesson Plans
- Events: `userGenLessonPlanGenerate` (start) / `userGenLessonPlanComplete` (complete)
- LP ID: `JSON_VALUE(properties, '$.ep_lesson_plan_id')`
- Grade/subject: directly from `ep_grade` and `ep_subject` properties
- Extra fields: `class_strength`, `page_start`, `page_end`
- Complete matched on: `user_id + lp_id + complete_date >= start_date`

## Key Tables

| Table | Role |
|-------|------|
| `tbproddb.events_partitioned` | **USE THIS** — partitioned daily on `created`, filter required. 7.5 GB |
| `tbproddb.analytics_analyticsevent` | **AVOID** — unpartitioned, 68.6 GB, full scan every query. Only use if `events_partitioned` is missing data |
| `tbproddb.lp_info_all_types` | Pre-computed: one row per teacher x LP x date x type (Core + User Generated) |
| `tbproddb.schools_schoolclasstimetable` | Weekly schedule — `daysOfWeek` string where digits 1-5 = weekdays |
| `tbproddb.schools_schoolclasssubject` | Teacher-to-class-subject assignments |
| `tbproddb.schools_schoolclass` | Class metadata (section, shift, session) |
| `tbproddb.slo_gradesubject` → `slo_grade` + `slo_subject` | Grade and subject lookup |
| `tbproddb.user_school_profiles` | Teacher dimension — final filter for valid teachers |
| `tbproddb.FDE_Schools` | ICT/Islamabad school reference |

## Counting Rules

- LP started: `COUNT(DISTINCT lp_s_id)` — unique LPs started
- LP completed: `COUNT(DISTINCT lp_c_id)` — unique LPs completed
- Never count raw event rows — always count distinct LP IDs
- A teacher appears once per grade-subject per week — use `COUNT(DISTINCT user_id)` when counting unique teachers

## max_classes Calculation

Counts teaching days per week from timetable `daysOfWeek` string:
- Digits 1-5 represent Sunday through Thursday
- Sum the days present in the string = scheduled classes per week
- Use `MAX()` in GROUP BY to take the most scheduled version

## Calendar Rules

- Weeks run **Saturday to Friday** (`EXTRACT(WEEK(SATURDAY) FROM date)`)
- Date spine generated from session start to `CURRENT_DATE()`
- Exclude weeks before teacher's `activated_on` date
- Only include timetable entries that existed by that week (`created <= week_end`)

## Subject Normalization

- `'maths'` → `'Math'`
- `'science'` → `'Sci'`
- All others: use `short_code` as-is

## Aggregation Patterns

| User asks about | GROUP BY | Aggregate |
|-----------------|----------|-----------|
| Weekly LP rate across all teachers | `week_number` | `AVG(lp_ratio)` |
| Per-teacher overall rate | `user_id` | `AVG(lp_ratio)` |
| Per-school weekly rate | `EMIS` | `AVG(lp_ratio)` |
| Status distribution | `lp_status_category` | `COUNT(DISTINCT user_id)` |
