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

### ict-islamabad/teacher_acr/
When: teacher ACR (Annual Confidential Report) scores, promotion policy, FICO-to-ACR KPI mapping, teacher performance vs student outcomes
- `acr-kpi-rules.md` — `fico_kpis` (5,180 rows, 6 KPIs scored 0-10, total/60), `student_results_data` (539 rows, early stage)

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
Datasets: `Muawin_Akhuwat_db` (Schoolpilot, ~50 tables) + `Zavia_db` (Zavia, ~57 tables) — BigQuery | Regional split: `organization_id`
Join key: `teachers.zavia_user_id = Zavia_db.users.id` | Test exclusion: Schoolpilot `users.is_active = true`, Zavia `users.is_test_user = false`

### moawin-akhuwat/dimensions/users/
When: teacher profiles, user counts, school assignments, qualifications, designations, geographic hierarchy
- `user-query-rules.md` — `teachers` is primary (not `users`), geographic hierarchy (org → district → tehsil → cluster → school), `zavia_user_id` join key

### moawin-akhuwat/lesson_plans/
When: AI lesson plan generation counts, LP volume by grade/subject
- `lp-query-rules.md` — Zavia `lesson_plans` + `lesson_plan_requests` (pipeline)

### moawin-akhuwat/coaching/
When: AI coaching sessions, coaching results, quality metrics, lesson fidelity
- `ai-coaching-rules.md` — Zavia `coaching_sessions` + `coaching_quality_metrics`, fidelity scoring

### moawin-akhuwat/student_results/
When: AI reading assessments, school-administered assessments, coach spot checks
- `ai-assessment-rules.md` — Zavia `reading_assessments` (89 columns: WCPM, fluency, comprehension, pronunciation, auto-levelling)
- `school-assessment-rules.md` — Schoolpilot `student_scores` + `assessments` + `assessment_subjects` + `pefsis_students` (~16,800 students)
- `coach-spotcheck-rules.md` — COMING SOON

### moawin-akhuwat/attendance/
When: teacher attendance, student attendance, enrollment counts
- `teacher-attendance-rules.md` — Schoolpilot `teacher_attendances` (daily per-teacher) + `teacher_leave_requests`
- `student-attendance-rules.md` — Schoolpilot aggregate per school + Zavia individual student-level AI attendance

### moawin-akhuwat/training/
When: teacher training levels, course progress, quiz scores
- `training-rules.md` — Schoolpilot `training_levels` → `courses` → `modules` → `questions`, `teacher_training_progress`, `teacher_quiz_attempts`

### moawin-akhuwat/schools/
When: school profiles, infrastructure, geographic hierarchy, visit reports
- `school-rules.md` — `schools`, `school_profiles` (infrastructure), `school_visit_reports`, `school_improvement_plans`

## MySchool (`myschool/`)
Dataset: `MySchool_db` (59 tables) — Django school management system | Join key: `emis_code`

### myschool/
When: MySchool platform data — staff, students, attendance, infrastructure, results, timetables, analytics
- `myschool-rules.md` — Full schema: `school_staff` (3,613), `notes_userprofile` (3,889), `events_interactionevent` (9,656), infrastructure profiles (21), students (30, early stage), results (0, not yet populated)

## Cross-Region KPI Comparability

Cross-region comparison is limited to **volume and coverage metrics**. Qualitative comparison (scores, outcomes) is NOT valid because regions use fundamentally different tools and scoring frameworks.

| KPI | ICT Source | RWP Source | Moawin/Akhuwat Source | Comparable Metric |
|-----|-----------|-----------|----------------------|-------------------|
| User data | user_school_profiles | TaleemHub_DB.users | Muawin_Akhuwat_db.teachers | Teacher count, cohort size |
| Lesson plans | analytics_events (canonical) | RUMI_DB.lesson_plans | Zavia_db.lesson_plans | Volume only |
| Coaching - Human | coaching_observation (scored) | mentoring_visits (narrative) | N/A | Session count + coverage % |
| Coaching - AI | observation stack (automated) | coaching_sessions | Zavia_db.coaching_sessions | Session count + completion rate |
| Student results - AI | not active | reading_assessments | Zavia_db.reading_assessments | Not comparable yet |
| Student results - Human | ODK ASER | TaleemHub ASER | Muawin_Akhuwat_db.student_scores | Volume only |
| Training | teacher_training_level | Not in scope | Muawin_Akhuwat_db.teacher_training_progress | Module/quiz completion |
| Attendance | Not in scope | Not in scope | Muawin_Akhuwat_db.teacher_attendances | Moawin/Akhuwat only |

## Database Context
- **BigQuery:** Project `niete-bq-prod` — `tbproddb` (466 tables, ICT), `RUMI_DB` (70 tables, RWP AI), `TaleemHub_DB` (60 tables, RWP roster), `Muawin_Akhuwat_db` (~50 tables, Schoolpilot), `Zavia_db` (~57 tables, Zavia AI), `MySchool_db` (59 tables, school management)
- **PostgreSQL (Rawalpindi only):** `neondb` (Schoolpilot) and `zavia1` (Zavia) — still PostgreSQL for RWP
- More datasets will be added after migration from other sources
