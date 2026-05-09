# Student Results — School Assessments Query Rules — Moawin / Akhuwat

## When These Rules Apply

User asks about:
- School-administered student assessment marks in Moawin or Akhuwat
- Student academic performance (human-entered scores)
- Assessment scores by subject, grade, or teacher
- Student pass rates
- PEFSIS student demographics linked to scores

## Mandatory Clarifications

### Assessment Type
Ask: "Which assessment? (name, academic_year, or assessment_type)"
- `assessment_type` and `status` (draft/active/completed) on `assessments` table

### Subject
Ask: "Which subject, or all?"
- Subjects defined in `assessment_subjects` per assessment

### Grade Level
Ask: "Which grade level, or all?"
- Grade is on `assessment_subjects.grade` and `pefsis_students.grade`

### Time Period
Ask: "Which assessment period or date range?"
- `assessment_date` and `assessment_date_to` on `assessments`

### Region
Ask: "Moawin or Akhuwat?"
- Filter via `assessments.organization_id`

## Key Tables

| Table | Role | Dataset | Status |
|-------|------|---------|--------|
| `Muawin_Akhuwat_db.student_scores` | Individual student marks per subject | Schoolpilot (BigQuery) | **CANONICAL** |
| `Muawin_Akhuwat_db.assessments` | Assessment definitions (name, type, dates, passing %) | Schoolpilot | **Required** |
| `Muawin_Akhuwat_db.assessment_subjects` | Subjects within an assessment (name, total_marks, grade) | Schoolpilot | **Required** |
| `Muawin_Akhuwat_db.pefsis_students` | Student identity (name, school, grade, demographics) | Schoolpilot | ~16,800 rows |
| `Muawin_Akhuwat_db.schools` | School context (name, EMIS) | Schoolpilot | For school rollups |
| `Muawin_Akhuwat_db.users` | Score entry user (entered_by) | Schoolpilot | For audit |

## Key Columns — Muawin_Akhuwat_db.student_scores

- `assessment_id` — FK to `assessments.id`
- `student_id` — FK to `pefsis_students.id` (NOT a generic student table)
- `subject_id` — FK to `assessment_subjects.id`
- `marks_obtained` — student's raw score (NUMERIC)
- `is_absent` — BOOLEAN, whether student was absent
- `percentage` — computed percentage (FLOAT)
- `grade` — letter grade (STRING)
- `is_passed` — BOOLEAN, whether student passed
- `entered_by` — FK to `users.id` (who entered the score)

**NOTE:** Score column is `marks_obtained` (NOT `score`). Pass status is `is_passed` (BOOLEAN, pre-computed).

## Key Columns — Muawin_Akhuwat_db.assessments

- `id` — primary key (VARCHAR UUID)
- `organization_id` — FK to `organizations.id` (region filter)
- `name` — assessment name (STRING)
- `assessment_type` — type (STRING)
- `academic_year` — year (STRING)
- `assessment_date`, `assessment_date_to` — date range
- `passing_percentage` — threshold for passing (FLOAT, e.g., 33.0)
- `status` — `draft`, `active`, `completed`
- `created_by` — FK to `users.id`

## Key Columns — Muawin_Akhuwat_db.assessment_subjects

- `assessment_id` — FK to `assessments.id`
- `subject_name` — subject (STRING, e.g., "Math", "English", "Urdu")
- `total_marks` — maximum marks for this subject (INTEGER)
- `grade` — which grade this subject applies to (STRING)
- `display_order` — ordering (INTEGER)

## Key Columns — Muawin_Akhuwat_db.pefsis_students

- `id` — primary key (VARCHAR UUID)
- `pefsis_student_id` — unique external ID (INTEGER, from PEFSIS portal)
- `emis` — school EMIS code
- `school_id` — FK to `schools.id`
- `organization_id` — FK to `organizations.id`
- `name_with_father` — student + father name (STRING)
- `registration_no`, `b_form` — identity documents
- `class`, `grade` — student class/grade (STRING)
- `date_of_birth` — **stored as TEXT, not date** — cast for age calculations
- `gender` — STRING
- `father_name`, `father_cnic`, `mother_cnic` — family
- `approval_status` — `pending`, `approved`, `rejected`
- `is_orphan`, `is_osc` (out-of-school child), `is_bricklin` — flags (BOOLEAN)
- `sync_status`, `synced_at` — PEFSIS sync tracking
- `created_at`, `updated_at`

## Join Pattern

```sql
SELECT ss.marks_obtained, ss.percentage, ss.is_passed, ss.is_absent,
       a.name AS assessment_name, a.assessment_type, a.academic_year,
       asub.subject_name, asub.total_marks, asub.grade,
       ps.name_with_father, ps.gender, ps.class,
       sch.name AS school_name, sch.emis
FROM Muawin_Akhuwat_db.student_scores ss
JOIN Muawin_Akhuwat_db.assessments a ON ss.assessment_id = a.id
JOIN Muawin_Akhuwat_db.assessment_subjects asub ON ss.subject_id = asub.id
JOIN Muawin_Akhuwat_db.pefsis_students ps ON ss.student_id = ps.id
JOIN Muawin_Akhuwat_db.schools sch ON ps.school_id = sch.id
WHERE a.organization_id IN (<moawin_org_id>, <akhuwat_org_id>)
  AND a.status IN ('active', 'completed')
  AND ss.is_absent = false
```

## Filtering Rules

- Region: `a.organization_id` (on assessments table)
- Active assessments: `a.status IN ('active', 'completed')` — exclude drafts for KPI
- Absent students: `ss.is_absent = false` for score aggregation (include for attendance metrics)
- Approved students: `ps.approval_status = 'approved'` (optional, for clean cohort)

## Counting & Aggregation Rules

- Score count = `COUNT(*)` where `is_absent = false` (one per student-subject)
- Students assessed = `COUNT(DISTINCT ss.student_id)`
- Pass rate = `COUNTIF(ss.is_passed) / COUNTIF(NOT ss.is_absent)` (pre-computed boolean)
- Avg marks = `AVG(ss.marks_obtained)` where `is_absent = false`

## Aggregation Patterns

| User asks about | GROUP BY | Aggregate |
|-----------------|----------|-----------|
| Total students scored | — | `COUNT(DISTINCT ss.student_id) WHERE NOT is_absent` |
| Avg marks (overall) | — | `AVG(ss.marks_obtained)` |
| Avg marks by subject | `asub.subject_name` | `AVG(ss.marks_obtained)` |
| Avg marks by grade | `asub.grade` | `AVG(ss.marks_obtained)` |
| Pass rate (overall) | — | `COUNTIF(ss.is_passed) / COUNTIF(NOT ss.is_absent)` |
| Pass rate by subject | `asub.subject_name` | `COUNTIF(ss.is_passed) / COUNT(*)` |
| Pass rate by school | `sch.name`, `sch.emis` | `COUNTIF(ss.is_passed) / COUNT(*)` |
| By assessment | `a.name`, `a.academic_year` | `AVG(ss.marks_obtained)`, pass rate |
| Grade distribution | `ss.grade` (letter) | `COUNT(DISTINCT ss.student_id)` |
| By gender | `ps.gender` | `AVG(ss.marks_obtained)`, pass rate |
| Absent rate | — | `COUNTIF(ss.is_absent) / COUNT(*)` |

## Data Conventions

- Timezone: `Asia/Karachi`
- `pefsis_students.date_of_birth` is TEXT — cast with `SAFE.PARSE_DATE('%Y-%m-%d', ...)` for age
- `passing_percentage` on `assessments` is the threshold; `is_passed` on `student_scores` is pre-computed
- `total_marks` is per-subject on `assessment_subjects`, not on `assessments`

## Key Difference from ICT/RWP/Zavia

- **Zavia AI assessments:** Automated reading fluency (WCPM, comprehension) — different purpose
- **School assessments:** Human teacher-entered academic marks (Math, English, Urdu, Science)
- **PEFSIS students:** Synced from external government portal, ~16,800 rows
- Not directly comparable with AI reading assessments

## Important Notes

- `student_id` FK goes to `pefsis_students` (government-synced student records)
- `marks_obtained` is the score column (NOT `score`)
- `is_passed` is pre-computed BOOLEAN (NOT derived from threshold)
- No direct Zavia join needed — school assessments are purely Schoolpilot data
- `pefsis_students.date_of_birth` and `admission_date` are TEXT, not DATE

## Data Status
- Status: SCHEMA VERIFIED
- Last verified: April 2026
