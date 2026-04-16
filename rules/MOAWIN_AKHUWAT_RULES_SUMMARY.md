# Moawin / Akhuwat Governance Rules — Implementation Summary

**Date:** April 11, 2026
**Status:** COMPLETE — Moawin/Akhuwat region rules created with global rule enhancements

---

## Global Rules Enhanced (All Regions)

### 1. `data-governance.md` — Added Two New Sections

#### Test User Exclusion (All Regions)
- **Schoolpilot (`Muawin_Akhuwat_db` for Moawin/Akhuwat, `neondb` for Rawalpindi):** Filter `users.testing_account = false` OR use name-based patterns
- **Zavia (`Zavia_db` for Moawin/Akhuwat, `zavia1` for Rawalpindi):** Filter `users.testing_account = false` OR name-based exclusions
- **When applying:** All user counts, coaching counts, assessment counts must exclude test accounts
- **Purpose:** Prevent test/pilot data from polluting production KPI reports
- **Applies to:** ICT/Islamabad, Rawalpindi, Moawin/Akhuwat

#### Database Priority Rules
- **User/Teacher data:** Schoolpilot (`Muawin_Akhuwat_db.users` + `Muawin_Akhuwat_db.teachers`) CANONICAL; Zavia secondary
- **Lesson plans, coaching, assessments:** Zavia (`Zavia_db.*`) CANONICAL; Schoolpilot supporting
- **Teacher enrichment:** Always LEFT JOIN Schoolpilot users + teachers on `teachers.user_id = users.id`
- **Cross-database joins:** Use phone_number or stable identifiers; prefer primary keys within same database
- **Applies to:** Rawalpindi, Moawin/Akhuwat (uses both databases)

### 2. `bigquery.md` — Added Moawin/Akhuwat BigQuery Datasets

New section: **Moawin / Akhuwat — BigQuery Datasets (migrated from PostgreSQL)**

| Dataset | Role | Source | Status |
|---------|------|--------|--------|
| `Muawin_Akhuwat_db` (Schoolpilot) | User/teacher data, student assessments | Migrated from `neondb` (PostgreSQL) | CANONICAL |
| `Zavia_db` (Zavia) | AI coaching/LP/assessments | Migrated from `zavia1` (PostgreSQL) | CANONICAL |

**Rules:**
- Reference tables as `Muawin_Akhuwat_db.users`, `Zavia_db.lesson_plans` (no `public.` schema)
- Small unpartitioned tables acceptable for full scans (< 10,000 rows)
- No hardcoded credentials in queries

---

## Index Updated (`index.md`)

### Region Section Revised

**From:** "Moawin → read `moawin/` (not yet available)"
**To:** "Moawin or Akhuwat → read `moawin-akhuwat/` (use `organization_id` to split within region)"

### New Moawin/Akhuwat Section Added

```
## Region: Moawin / Akhuwat (`moawin-akhuwat/`)
Datasets: `Muawin_Akhuwat_db` (Schoolpilot) + `Zavia_db` (Zavia) — BigQuery | Regional split: `organization_id`

### moawin-akhuwat/dimensions/users/
- user-query-rules.md — Schoolpilot canonical + enrichment, org_id filter, test exclusion

### moawin-akhuwat/lesson_plans/
- lp-query-rules.md — Zavia lesson_plans, test exclusion

### moawin-akhuwat/coaching/
- ai-coaching-rules.md — Zavia coaching_sessions, test exclusion, fidelity scoring

### moawin-akhuwat/student_results/
- ai-assessment-rules.md — Zavia reading_assessments
- school-assessment-rules.md — Schoolpilot student_scores + assessments
- coach-spotcheck-rules.md — COMING SOON (Apr 13)
```

### Cross-Region KPI Table Updated

Added Moawin/Akhuwat column:

| KPI | ICT | RWP | Moawin/Akhuwat | Comparable |
|-----|-----|-----|-----------------|-----------|
| User data | user_school_profiles | TaleemHub_DB.users | **Muawin_Akhuwat_db.users + teachers** | ✓ Count, cohort |
| Lesson plans | analytics_events | RUMI_DB.lesson_plans | **Zavia_db.lesson_plans** | ✓ Volume |
| Coaching - AI | observation stack (auto) | coaching_sessions | **coaching_sessions** | ✓ Count + rate |
| AI Coaching - Lesson Fidelity | coaching_observationquestion | analysis_data | **analysis_data** | Fidelity score (if comparable) |
| Student results - AI | not active | reading_assessments | **reading_assessments** | Not comparable yet |
| Student results - Human | ODK ASER | TaleemHub ASER | **student_scores + assessments** | ✓ Volume |

### Database Context Updated

Now documents BigQuery datasets for all regions: ICT (`tbproddb`), Rawalpindi (`RUMI_DB` + `TaleemHub_DB`), and Moawin/Akhuwat (`Muawin_Akhuwat_db` + `Zavia_db`). PostgreSQL (`neondb` + `zavia1`) remains for Rawalpindi only.

---

## Moawin / Akhuwat Rules Created (5 Domain Areas)

### 1. `moawin-akhuwat/dimensions/users/user-query-rules.md`

**Purpose:** Teacher profiles, user counts, school assignments, institutional attributes

**Key Tables:**
- `Muawin_Akhuwat_db.users` — CANONICAL user identity + registration
- `Muawin_Akhuwat_db.teachers` — REQUIRED enrichment (EMIS, school, qualifications, designation, gender, experience, certifications)
- `Zavia_db.users` — Verification only

**Key Rule:** ALWAYS LEFT JOIN users + teachers; users table alone insufficient

**Filters:**
- `organization_id` for region (Moawin vs Akhuwat — values TBD)
- `status = 'active'` (default)
- `testing_account = false` (global test exclusion rule)

**Aggregation:** By school, designation, qualification, gender, experience

**Data Status:** COMMENT + TRANSCRIPT MATCH

---

### 2. `moawin-akhuwat/lesson_plans/lp-query-rules.md`

**Purpose:** AI lesson plan generation counts, volume, trends, grade/subject breakdown

**Key Table:**
- `Zavia_db.lesson_plans` — CANONICAL LP records (4,759 baseline)
- `Zavia_db.lesson_plan_requests` — Supporting flow table

**Key Rule:** Regional filter via LEFT JOIN to `Muawin_Akhuwat_db.users` on phone_number

**Filters:**
- `testing_account = false` on BOTH Zavia and Schoolpilot
- `status = 'active'` on Schoolpilot
- `created_at >= DATE(...)` for time filtering

**Aggregation:** By grade, subject, teacher, school, week, month

**Data Status:** MATCHED

---

### 3. `moawin-akhuwat/coaching/ai-coaching-rules.md`

**Purpose:** AI coaching sessions, quality metrics, analysis outputs, lesson fidelity

**Key Tables:**
- `Zavia_db.coaching_sessions` — CANONICAL session records (170 baseline)
- `Zavia_db.coaching_quality_metrics` — Quality/performance metrics (125 baseline)

**Key Feature:** Lesson fidelity scoring
- Located in `analysis_data` JSON: `fidelity_analysis.score` (0-100)
- Only when `has_lesson_plan = true`

**Filters:**
- `status = 'completed'` for KPI (default)
- Exclude `status = 'test_cleanup'` always
- `testing_account = false` on both datasets
- `status = 'active'` on Schoolpilot

**Aggregation:** By region, teacher, week, month, plus quality metrics (processing time, satisfaction, cost)

**Data Status:** TRANSCRIPT MATCH; fidelity_score confirmed in analysis_data

---

### 4. `moawin-akhuwat/student_results/ai-assessment-rules.md`

**Purpose:** Student AI reading assessments (WCPM, accuracy, comprehension, pronunciation)

**Key Table:**
- `Zavia_db.reading_assessments` — CANONICAL assessment records (277 baseline)

**Key Metrics:**
- WCPM = Words Correct Per Minute (fluency)
- `accuracy_percentage` = reading accuracy (0-100%)
- `comprehension_score` = understanding
- `on_track` = meets grade benchmark

**Filters:**
- `status = 'completed'` for KPI
- `testing_account = false` on both datasets
- `status = 'active'` on Schoolpilot

**Aggregation:** By grade, subject, teacher, school, language, passage type, plus on-track rate

**Data Status:** MATCHED

---

### 5. `moawin-akhuwat/student_results/school-assessment-rules.md`

**Purpose:** Human-entered school assessment marks (academic subjects)

**Key Tables:**
- `Muawin_Akhuwat_db.student_scores` — CANONICAL student marks
- `Muawin_Akhuwat_db.assessments` — Assessment metadata (subject, type, rubric, total_marks, passing_marks)

**Key Metrics:**
- `score` = raw mark (scale TBD)
- `percentage` = normalized to 0-100 (if different)
- `grade_label` = letter grade (if applicable)
- Pass rate = `score >= passing_marks`

**Filters:**
- `status IN ('submitted', 'reviewed')` for KPI (exclude drafts)
- `organization_id` for region

**Aggregation:** By subject, grade, assessment, school, teacher, plus pass rates

**Data Status:** MATCHED

---

### 6. `moawin-akhuwat/student_results/coach-spotcheck-rules.md` (PLACEHOLDER)

**Purpose:** Coach-collected student spot checks (COMING SOON)

**Current Status:** Table deployment TBD; expected April 13, 2026

**Owner:** Mahrah Ashraf

**What We Need:**
1. Table name and database
2. Complete schema (columns, types)
3. Key identifiers (student ID, coach ID, date, type)
4. Score/result format
5. Links to other tables (coaching_sessions? visits?)
6. Regional split variable
7. Filtering rules (test data, status, dates)
8. Aggregation level

**Action:** Placeholder created; to be updated with full spec once table deployed

---

## Key Global Rules to Remember (All Regions)

### Test User Exclusion
```sql
WHERE users.testing_account = false
```
**Applies to:** All user counts, coaching counts, assessment counts
**Purpose:** Prevent test/pilot data from dashboards

### Database Priority
- **Canonical user/teacher data:** `Muawin_Akhuwat_db.users` + `teachers` (Schoolpilot, BigQuery)
- **Canonical coaching/LP/assessments:** `Zavia_db.*` (Zavia, BigQuery)
- **Teacher enrichment:** Always `LEFT JOIN teachers` on `teachers.user_id = users.id`

### Regional Filtering
- Use `organization_id` in `Muawin_Akhuwat_db.users` to split Moawin vs Akhuwat
- Exact org_id values TBD — verify with data team before hardcoding

---

## Missing Global Rules Identified & Added

### 1. ✅ Test User Exclusion Rule
- **Gap:** ICT/RWP rules don't explicitly document test user filtering
- **Added:** Global rule in `data-governance.md`
- **Applies to:** All regions, both Schoolpilot and Zavia

### 2. ✅ Database Priority Rule
- **Gap:** No global guidance on which DB is canonical for each metric type
- **Added:** Global rule in `data-governance.md`
- **Applies to:** Rawalpindi, Moawin/Akhuwat (multi-database regions)

### 3. ✅ Moawin/Akhuwat BigQuery Datasets
- **Gap:** `bigquery.md` only documented ICT BigQuery; Moawin/Akhuwat not covered
- **Added:** New section in `bigquery.md` with BigQuery dataset references (`Muawin_Akhuwat_db` + `Zavia_db`)
- **Applies to:** Moawin/Akhuwat (migrated to BigQuery). Rawalpindi still uses PostgreSQL (`neondb` + `zavia1`)

---

## Verification Checklist

- [x] Global rules updated with test user exclusion
- [x] Global rules updated with database priority
- [x] BigQuery rules updated with Moawin/Akhuwat BigQuery datasets
- [x] Index updated with Moawin/Akhuwat section
- [x] Cross-region KPI table updated with Moawin/Akhuwat sources
- [x] User query rules created (dimensions/users)
- [x] Lesson plan query rules created
- [x] AI coaching query rules created (with lesson fidelity)
- [x] AI assessment (reading) query rules created
- [x] School assessment (human-entered) query rules created
- [x] Coach spot check placeholder created (TBD Apr 13)

---

## Next Steps

1. **Verify organization_id values** for Moawin and Akhuwat with data team (referenced in all region filter rules)
2. **Confirm phone_number join availability** between Zavia users and Schoolpilot users
3. **Validate exact `grade` and `subject` normalization** rules for lesson plans
4. **Await coach spot check table deployment** from Mahrah Ashraf (deadline April 13)
5. **Test queries** against Moawin/Akhuwat production data
6. **Update `coach-spotcheck-rules.md`** once table structure available
7. **Update index.md** to mark coach-spotcheck-rules as ACTIVE (remove "COMING SOON")

---

## References

- **Global rules:** `.claude/rules/data-governance.md`, `bigquery.md`
- **Index:** `.claude/rules/index.md`
- **Moawin/Akhuwat rules:** `.claude/rules/moawin-akhuwat/`
- **Related regions:** `ict-islamabad/`, `rawalpindi/`

---

**Created:** April 11, 2026
**Last Updated:** April 11, 2026
