# Teacher ACR & Promotion Policy Rules — ICT/Islamabad

## When These Rules Apply

User asks about:
- Teacher ACR (Annual Confidential Report) scores or KPIs
- Teacher promotion eligibility or promotion policy metrics
- FICO observation indicators mapped to ACR KPIs
- Teacher performance scores (Planning, Subject Knowledge, Classroom Management, etc.)
- Teacher overall percentage or total score out of 60
- Teacher demographic/service data linked to performance (qualifications, pay scale, designation)

## Mandatory Clarifications

### Metric
Ask: "Which ACR KPI? Planning & Preparation, Subject Knowledge, Classroom Management, Communication Skills, Professional Development, Use of Technology, or overall?"

### Aggregation Level
Ask: "Per teacher, per school, per sector, or overall?"

### Time Period
Ask if relevant: "Which observation date range?"
- `Observation_date` is STRING — may need parsing

### Teacher Level
Ask if relevant: "Which teacher level? PRIMARY, MIDDLE, SECONDARY, or all?"
- `levels` column (STRING, JSON array format)

## Key Tables

| Table | Role | Rows | Dataset | Status |
|-------|------|------|---------|--------|
| `tbproddb.fico_kpis` | FICO observation indicators mapped to ACR KPIs | 5,180 | tbproddb | **CANONICAL** |
| `tbproddb.student_results_data` | Student academic results linked to teachers | 539 | tbproddb | **EARLY STAGE** — feature under development |

## Key Columns — tbproddb.fico_kpis

### Teacher Identity
- `user_id` — INTEGER, teacher user ID (join to `users_user` if needed)
- `teacher_name` — STRING
- `cnic` — STRING (national ID)
- `contact_number` — STRING
- `gender` — STRING
- `date_of_birth` — STRING (cast for age calculations)

### School Context
- `EMIS` — INTEGER, school EMIS code (join to `FDE_Schools` for school details)
- `School` — STRING, school name
- `Sector` — STRING, school sector

### Observation Context
- `Observation_date` — STRING, date of classroom observation (cast to DATE for filtering)
- `grade` — STRING, grade observed
- `subject` — STRING, subject observed

### Teacher Service Profile
- `levels` — STRING (JSON array, e.g., `["PRIMARY"]`)
- `joining_date` — STRING (cast for tenure calculations)
- `last_promotion_date` — STRING
- `professional_trainings` — STRING
- `qualifications` — STRING (e.g., "B.Ed", "M.Ed")
- `service_designation` — STRING (e.g., "PST", "SST", "Head Teacher")
- `basic_pay_scale` — STRING (e.g., "BPS-14", "BPS-16")

### ACR KPI Scores (FLOAT, each 0-10)
- `Planning_and_Preparation` — lesson planning quality (max 10)
- `Subject_Knowledge` — content mastery (max 10)
- `Classroom_Management` — discipline and environment (max 10)
- `Communication_Skills` — teaching communication (max 10)
- `Professional_Development` — growth and learning (max 10)
- `Use_of_Technology` — technology integration (max 10)
- `total_score_out_of_60` — sum of 6 KPIs (max 60)
- `overall_percentage` — `total_score_out_of_60 / 60 * 100` (FLOAT, 0-100)

## Key Columns — tbproddb.student_results_data

> **STATUS: EARLY STAGE** — 539 rows, feature under development. Use for exploratory analysis only.

- `teacher_id` — INTEGER, FK to teacher (join to `fico_kpis.user_id` for ACR+results link)
- `student_id` — STRING
- `student_name` — STRING
- `gender` — INTEGER (encoded — verify mapping: 0=?, 1=?)
- `grade` — INTEGER
- `subject` — STRING
- `session_year` — STRING (academic year)
- `term` — STRING (exam term)
- `marks` — FLOAT, student marks obtained
- `total_marks` — INTEGER, maximum marks
- `percentage` — FLOAT, computed percentage
- `student_grades` — STRING, letter grade
- `result` — STRING, pass/fail outcome
- `exam_date` — DATE
- `created_at` — TIMESTAMP

## ACR KPI Framework

The 6 ACR KPIs are derived from FICO classroom observation indicators:

| KPI | Max Score | What It Measures |
|-----|-----------|------------------|
| Planning & Preparation | 10 | Lesson plan quality and preparation |
| Subject Knowledge | 10 | Content mastery and accuracy |
| Classroom Management | 10 | Discipline, environment, time management |
| Communication Skills | 10 | Teaching clarity, questioning, student engagement |
| Professional Development | 10 | Growth mindset, training participation |
| Use of Technology | 10 | Integration of tech in teaching |
| **Total** | **60** | Sum of all 6 KPIs |

`overall_percentage = total_score_out_of_60 / 60 * 100`

## Join Patterns

```sql
-- ACR KPIs with school context
SELECT fk.*, fs.school_name AS fde_school_name
FROM tbproddb.fico_kpis fk
LEFT JOIN tbproddb.FDE_Schools fs ON fk.EMIS = fs.EMIS
WHERE fk.Observation_date >= '2024-01-01'  -- adjust date range

-- ACR + Student Results (teacher performance → student outcomes)
SELECT fk.user_id, fk.teacher_name, fk.overall_percentage AS acr_pct,
       AVG(sr.percentage) AS avg_student_pct,
       COUNT(DISTINCT sr.student_id) AS students_count
FROM tbproddb.fico_kpis fk
JOIN tbproddb.student_results_data sr ON fk.user_id = sr.teacher_id
GROUP BY fk.user_id, fk.teacher_name, fk.overall_percentage
```

## Required Filters

- `Observation_date` — always filter by date range (STRING — parse or compare as string if format is consistent)
- `levels` — filter by teacher level if user specifies: `levels LIKE '%PRIMARY%'`
- For ICT only: join to `FDE_Schools` on `EMIS` for official school context

## Aggregation Patterns

| User asks about | GROUP BY | Aggregate |
|-----------------|----------|-----------|
| Average ACR score (overall) | — | `AVG(overall_percentage)` |
| Average per KPI | — | `AVG(Planning_and_Preparation)`, `AVG(Subject_Knowledge)`, etc. |
| Per teacher | `user_id`, `teacher_name` | `AVG(overall_percentage)`, latest observation |
| Per school | `EMIS`, `School` | `AVG(overall_percentage)`, teacher count |
| Per sector | `Sector` | `AVG(overall_percentage)` |
| Per designation | `service_designation` | `AVG(overall_percentage)` |
| Per pay scale | `basic_pay_scale` | `AVG(overall_percentage)` |
| Per qualification | `qualifications` | `AVG(overall_percentage)` |
| Per gender | `gender` | `AVG(overall_percentage)` |
| Per level | `levels` | `AVG(overall_percentage)` |
| KPI distribution | KPI score buckets | `COUNT(DISTINCT user_id)` |
| Trend over time | `Observation_date` (parsed) | `AVG(overall_percentage)` |
| Promotion readiness | `overall_percentage >= <threshold>` | `COUNT(DISTINCT user_id)` |
| ACR vs student outcomes | `user_id` | `AVG(fk.overall_percentage)`, `AVG(sr.percentage)` |

## Student Results Aggregation (Early Stage)

| User asks about | GROUP BY | Aggregate |
|-----------------|----------|-----------|
| Avg student marks per teacher | `sr.teacher_id` | `AVG(sr.percentage)` |
| Pass rate per teacher | `sr.teacher_id` | `COUNTIF(sr.result = 'Pass') / COUNT(*)` |
| By subject | `sr.subject` | `AVG(sr.percentage)` |
| By grade | `sr.grade` | `AVG(sr.percentage)` |
| By term | `sr.term` | `AVG(sr.percentage)` |
| Teacher performance vs student outcomes | `sr.teacher_id` | join ACR score with student avg |

## Data Conventions

- Timezone: `Asia/Karachi`
- `Observation_date`, `joining_date`, `last_promotion_date`, `date_of_birth` are all STRING — cast to DATE for calculations
- KPI scores are FLOAT, each 0-10; total is 0-60; percentage is 0-100
- `levels` is a STRING containing a JSON array — use `LIKE '%PRIMARY%'` for filtering
- `student_results_data.gender` is INTEGER — verify encoding with data team (likely 0=female, 1=male or vice versa)
- 5,180 rows in `fico_kpis` — one row per teacher per observation (a teacher may have multiple observations)
- 539 rows in `student_results_data` — feature under development, expect growth

## Theory of Change Link

This data directly supports the Taleemabad Theory of Change:
- **Classroom Practice** → ACR KPI scores (FICO observation → ACR mapping)
- **Student Outcomes** → `student_results_data` (teacher → student result link)
- Together: enables analysis of whether better classroom practice leads to better student outcomes

## Important Notes

- `fico_kpis` is a **pre-processed/curated table** — the raw FICO data is in the observation stack (see `observation-query-rules.md`)
- For raw FICO section B/C/D scores, use the observation rules. For ACR-mapped KPIs, use this table.
- `student_results_data` is early stage (539 rows) — flag this to users and don't over-interpret
- A teacher can have multiple observations → multiple rows in `fico_kpis`. Average or take latest depending on use case.
- `last_promotion_date` enables promotion eligibility analysis (years since last promotion)

## Data Status
- `fico_kpis`: SCHEMA VERIFIED, 5,180 rows, production-ready
- `student_results_data`: SCHEMA VERIFIED, 539 rows, **feature under development** — data will grow
- Last verified: April 2026
- Region: ICT/Islamabad (tbproddb)
