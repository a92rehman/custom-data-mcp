# Student Results — School Assessments Query Rules — Moawin / Akhuwat

## When These Rules Apply

User asks about:
- School-administered student assessment marks in Moawin or Akhuwat
- Student academic performance (human-entered scores)
- Assessment scores by subject, grade, or teacher
- Class-level or school-level assessment aggregates
- Student results from formal school assessments

## Mandatory Clarifications

### Assessment Type
Ask: "Which assessment type?" (if multiple exist)
- Verify available assessment types in table with data team

### Subject / Skill
Ask: "Which subject or skill area, or all?"
- Filter by assessment subject/type

### Grade Level
Ask: "Which grade level, or all?"

### Time Period
Ask: "Which assessment period or date range?"
- `created_at` is primary timestamp

### Region
Ask: "Moawin or Akhuwat?"
- Filter via teacher/school organization_id

## Key Tables

| Table | Role | Database | Rows | Status |
|-------|------|----------|------|--------|
| `neondb.public.student_scores` | Individual student assessment marks | Schoolpilot (PostgreSQL) | Variable | **CANONICAL** |
| `neondb.public.assessments` | Assessment metadata (name, subject, type, rubric) | Schoolpilot | Variable | Supporting |
| `neondb.public.users` | Teacher/assessor identity | Schoolpilot | 1,296+ | For enrichment |
| `neondb.public.teachers` | Teacher institutional attributes (school, org_id) | Schoolpilot | Variable | For school context |

**Note:** These tables are small and unpartitioned. Full scans acceptable at this scale. Revisit if student_scores grows beyond 100,000 rows.

## Key Columns — neondb.public.student_scores

- `id` — primary key (STRING or INT)
- `student_id` — FK to student record (STRING or INT — structure TBD)
- `assessment_id` — FK to `neondb.public.assessments.id`
- `score` — student's raw score (FLOAT or INT — scale TBD, e.g., 0-100)
- `percentage` — score as percentage if different from raw score (FLOAT, 0-100)
- `grade_label` — letter grade if applicable (STRING, e.g., "A", "B", "C")
- `status` — submission status: `submitted`, `draft`, `reviewed`, etc.
- `created_at`, `updated_at` — timestamps (DATETIME/TIMESTAMP)
- `created_by`, `reviewed_by` — user IDs for audit trail (optional)

## Key Columns — neondb.public.assessments

- `id` — primary key (STRING or INT)
- `name` — assessment name / title
- `subject` — subject area (STRING, e.g., "Math", "English", "Urdu", "Science")
- `type` — assessment type (STRING, e.g., "quiz", "midterm", "final", "unit_test")
- `grade_level` — target grade (INT, e.g., 1-12)
- `total_marks` — full mark value (INT, e.g., 100)
- `passing_marks` — passing threshold (INT, e.g., 40)
- `rubric` — rubric definition or scoring guidelines (TEXT or JSON — structure TBD)
- `created_at`, `updated_at` — temporal
- `created_by` — assessor/teacher who created (FK to users.id)

## Join Pattern (Regional & School Context)

```sql
SELECT ss.*, a.*, u.id as teacher_id, u.name as teacher_name, nu.organization_id, nt.school_assignment, nt.emis_code
FROM neondb.public.student_scores ss
JOIN neondb.public.assessments a ON ss.assessment_id = a.id
LEFT JOIN neondb.public.users u ON a.created_by = u.id
LEFT JOIN neondb.public.teachers nt ON u.id = nt.user_id
LEFT JOIN neondb.public.users nu ON nt.user_id = nu.id
WHERE nu.organization_id IN (<moawin_org_id>, <akhuwat_org_id>)
  AND ss.status IN ('submitted', 'reviewed')  -- KPI reporting filter
```

## Filtering Rules

- Exclude draft/incomplete scores: include only `status IN ('submitted', 'reviewed')` for KPI
- Include active assessments: may need to filter on assessment `is_active = true` (verify with data team)
- Region filter: `nu.organization_id` must match specified Moawin or Akhuwat org_id
- Time filter on `ss.created_at >= DATE('...')` per global rules

## Counting & Aggregation Rules

- Score count = `COUNT(DISTINCT ss.id)` (one per student per assessment)
- Students assessed = `COUNT(DISTINCT ss.student_id)` per assessment or period
- Never count raw rows — distinct student/score pairs
- Passing count = `COUNTIF(ss.score >= a.passing_marks)`
- Pass rate = `COUNTIF(ss.score >= a.passing_marks) / COUNT(DISTINCT ss.student_id)`

## Aggregation Patterns

| User asks about | GROUP BY | Aggregate |
|-----------------|----------|-----------|
| Total assessments administered | — | `COUNT(DISTINCT a.id)` |
| Total student scores | — | `COUNT(DISTINCT ss.id)` |
| Avg score (all) | — | `AVG(ss.score)` |
| Avg score by subject | `a.subject` | `AVG(ss.score)` |
| Avg score by grade | `a.grade_level` | `AVG(ss.score)` |
| Avg score by assessment | `a.id`, `a.name` | `AVG(ss.score)` |
| Pass rate (overall) | — | `COUNTIF(ss.score >= a.passing_marks) / COUNT(*)` |
| Pass rate by subject | `a.subject` | `COUNTIF(ss.score >= a.passing_marks) / COUNT(*)` |
| Pass rate by grade | `a.grade_level` | `COUNTIF(ss.score >= a.passing_marks) / COUNT(*)` |
| Pass rate by assessment | `a.id`, `a.name` | `COUNTIF(ss.score >= a.passing_marks) / COUNT(*)` |
| By school | `nt.school_assignment`, `nt.emis_code` | `AVG(ss.score)`, `COUNTIF(ss.score >= a.passing_marks) / COUNT(*)` |
| By teacher | `u.id`, `u.name` | `AVG(ss.score)`, `COUNT(DISTINCT ss.id)` |
| By date/week | `DATE(ss.created_at)` or `DATE_TRUNC(ss.created_at, WEEK)` | `COUNT(DISTINCT ss.id)`, `AVG(ss.score)` |
| Grade distribution (for one assessment) | `ss.grade_label` | `COUNT(DISTINCT ss.student_id)` |

## Data Conventions

- Timezone: `Asia/Karachi` for all date/timestamp conversions
- Score scale: typically 0-100 or 0-total_marks; verify exact range with data team
- Percentage: if different from raw score, use for display; raw score for calculations
- Grade labels: typically A/B/C/D/F or similar; verify exact label values
- Passing marks threshold varies per assessment; use `a.passing_marks` not hardcoded threshold

## Key Difference from ICT/RWP/Zavia

- **Zavia AI assessments:** Automated reading fluency tests (WCPM, comprehension, pronunciation)
- **School assessments (Schoolpilot):** Human teacher-entered marks for academic subjects (Math, English, Urdu, Science)
- **Cross-region:** School assessment schema should be similar across regions (Moawin/Akhuwat use same Schoolpilot database)
- Comparison with Zavia: Different purpose (academic achievement vs reading fluency); not directly comparable

## Important Notes

- Student linking may be complex; verify `student_id` structure and join keys with data team
- Assessment rubric structure (if present) needs clarification before advanced analysis
- Exact score scale and passing marks threshold should be documented
- Status values (`submitted`, `draft`, `reviewed`) need verification — use only confirmed final states for KPI
- organization_id values must be verified with data team
- If student_scores table is used by multiple regions (not just Moawin/Akhuwat), ensure regional filters are always applied

## Data Status
- Status: MATCHED (per Moawin/Akhuwat reconciliation notes)
- School assessment KPI: `neondb.public.student_scores + assessments`
- Last verified: April 2026
- Related global rules: Database priority (data-governance.md), Schoolpilot as canonical user/teacher source
