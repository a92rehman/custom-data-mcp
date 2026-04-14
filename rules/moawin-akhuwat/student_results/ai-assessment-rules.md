# Student Results — AI Assessment Query Rules — Moawin / Akhuwat

## When These Rules Apply

User asks about:
- Student AI reading assessments in Moawin or Akhuwat
- Student reading fluency (WCPM), accuracy, or comprehension scores
- Assessment outcomes or student reading levels
- Student performance trends by grade or subject
- On-track rate or benchmark comparison

## Mandatory Clarifications

### Metric
Ask: "Which metric? WCPM, accuracy, comprehension, or all?"
- WCPM = Words Correct Per Minute (fluency metric)
- `accuracy_percentage` = reading accuracy (0-100%)
- `comprehension_score` = understanding level

### Aggregation Level
Ask: "Per student, per teacher, per school, or overall?"

### Grade Level
Ask: "Which grade level, or all?"
- `grade_level` (INT) available for filtering

### Time Period
Ask: "Which time period?"
- `created_at` (TIMESTAMP) is primary timestamp

### Region
Ask: "Moawin or Akhuwat?"
- Filter via teacher's `organization_id`

## Key Tables

| Table | Role | Database | Rows | Status |
|-------|------|----------|------|--------|
| `zavia1.public.reading_assessments` | Student reading assessment records | Zavia (PostgreSQL) | 277 (baseline) | **CANONICAL** |
| `zavia1.public.users` | Assessment administrator (teacher/coach) | Zavia | 5,319 | For join |
| `neondb.public.users` | Teacher enrichment (organization_id, status) | Schoolpilot | 1,296+ | For regional filter |

**Note:** These tables are small and unpartitioned. Full scans acceptable at this scale.

## Key Columns — zavia1.public.reading_assessments

### Identity & Status
- `id` — primary key (STRING), use `COUNT(DISTINCT id)` for assessment count
- `user_id` — FK to `zavia1.public.users.id` (teacher/administrator)
- `student_identifier`, `student_number` — student identity within session (no FK — STRING)
- `status` — assessment status: `completed`, `passage_generated`, `fluency_completed`, `comprehension_completed`, `failed`, `abandoned`, `comprehension_in_progress`

### Reading Metrics (Core)
- `wcpm` — Words Correct Per Minute (FLOAT, primary fluency metric)
- `accuracy_percentage` — reading accuracy (FLOAT, 0-100)
- `words_read`, `words_correct` — raw counts (FLOAT)
- `total_words_in_passage` — passage length (FLOAT)
- `time_elapsed_seconds` — reading duration (FLOAT)
- `on_track` — BOOLEAN, whether student meets grade benchmark
- `grade_benchmark_min`, `grade_benchmark_max` — grade-level WCPM benchmarks (FLOAT)
- `percentile_rank` — position relative to peers (STRING — may need parsing)

### Comprehension
- `comprehension_score` — numeric comprehension result (FLOAT)
- `comprehension_questions` — JSON STRING, questions asked
- `comprehension_answers` — JSON STRING, student answers
- `comprehension_analysis` — JSON STRING, AI analysis of answers
- `comprehension_requested` — BOOLEAN, whether comprehension was part of assessment

### Pronunciation & Prosody
- `pronunciation_accuracy` — numeric score (FLOAT)
- `pronunciation_data` — JSON STRING, detailed pronunciation analysis
- `prosody_analysis` — JSON STRING, speech rhythm/intonation analysis
- `errors` — JSON STRING, reading errors (list of error instances)
- `self_corrections_count` — INT, student self-corrections

### Assessment Context
- `grade_level` — INT, student grade (e.g., 1, 2, 3, 4, 5, 6)
- `language` — assessment language (STRING, e.g., "Urdu", "English", "Pashto")
- `passage_type` — type of reading passage (STRING, e.g., "narrative", "informational")
- `passage_text` — the actual passage (STRING)
- `assessment_mode` — how administered (STRING, e.g., "individual", "group")
- `starting_level`, `final_level` — adaptive leveling (STRING)
- `level_attempts` — JSON STRING, attempts per level

### Temporal
- `created_at` — TIMESTAMP, when assessment was created/started
- `updated_at` — TIMESTAMP, last modification

## Join Pattern (Regional Filter)

```sql
SELECT ra.*, zu.user_id, zu.testing_account, nu.organization_id, nu.status, nt.school_assignment
FROM zavia1.public.reading_assessments ra
JOIN zavia1.public.users zu ON ra.user_id = zu.id
LEFT JOIN neondb.public.users nu ON zu.phone_number = nu.phone_number
LEFT JOIN neondb.public.teachers nt ON nu.id = nt.user_id
WHERE nu.organization_id IN (<moawin_org_id>, <akhuwat_org_id>)
  AND zu.testing_account = false
  AND nu.testing_account = false
  AND nu.status = 'active'
  AND ra.status = 'completed'  -- FOR KPI REPORTING (omit for diagnostics)
```

## Status Values

| Status | Count | Meaning | Include in KPI? |
|--------|-------|---------|-----------------|
| `completed` | 142 (baseline) | Fully processed | YES (default) |
| `passage_generated` | 63 | Passage created, not started | NO |
| `fluency_completed` | 40 | Fluency done, comprehension pending | Only if asked |
| `failed` | 19 | Processing failed | Only for diagnostics |
| `comprehension_completed` | 11 | Comprehension done, not fully completed | Only if asked |
| `abandoned` | 1 | Student/teacher abandoned | NO |
| `comprehension_in_progress` | 1 | Currently running | NO |

**Default KPI filter:** `ra.status = 'completed'`

## Filtering Rules

- Exclude test users: `zu.testing_account = false` AND `nu.testing_account = false`
- Exclude inactive users: `nu.status = 'active'`
- Include date filter on `ra.created_at >= DATE('...')` per global rules
- For KPI reporting: include only `ra.status = 'completed'`

## Counting Rules

- Assessment count = `COUNT(DISTINCT ra.id)`
- Students assessed = `COUNT(DISTINCT ra.student_identifier)` (within teacher scope)
- Teachers who administered = `COUNT(DISTINCT ra.user_id)`

## Aggregation Patterns

| User asks about | GROUP BY | Aggregate |
|-----------------|----------|-----------|
| Total assessments (completed) | — | `COUNT(DISTINCT ra.id) WHERE status='completed'` |
| Assessments by region | `nu.organization_id` | `COUNT(DISTINCT ra.id)` |
| Students assessed | — | `COUNT(DISTINCT ra.student_identifier)` |
| Avg WCPM | — | `AVG(ra.wcpm)` |
| Avg WCPM by grade | `ra.grade_level` | `AVG(ra.wcpm)` |
| Avg accuracy | — | `AVG(ra.accuracy_percentage)` |
| Avg comprehension | — | `AVG(ra.comprehension_score)` |
| On-track rate | — | `COUNTIF(ra.on_track) / COUNT(*)` |
| On-track by grade | `ra.grade_level` | `COUNTIF(ra.on_track) / COUNT(*)` |
| By grade | `ra.grade_level` | `AVG(ra.wcpm)`, `AVG(ra.accuracy_percentage)` |
| By teacher | `ra.user_id` | `COUNT(DISTINCT ra.id)`, `AVG(ra.wcpm)` |
| By school | `nt.school_assignment` | `AVG(ra.wcpm)`, `COUNT(DISTINCT ra.id)` |
| By language | `ra.language` | `AVG(ra.wcpm)`, `COUNT(DISTINCT ra.id)` |
| By passage type | `ra.passage_type` | `AVG(ra.wcpm)`, `COUNT(DISTINCT ra.id)` |
| Weekly trend | `DATE_TRUNC(ra.created_at, WEEK(SATURDAY))` or `DATE_TRUNC(ra.created_at, 7 DAY)` (PostgreSQL) | `COUNT(DISTINCT ra.id)`, `AVG(ra.wcpm)` |
| Monthly trend | `DATE_TRUNC(ra.created_at, MONTH)` | `COUNT(DISTINCT ra.id)`, `AVG(ra.wcpm)` |

## Data Conventions

- Timezone: `Asia/Karachi` for all date/timestamp conversions
- Weeks run Saturday to Friday (consistent with Taleemabad convention)
- JSON fields (`comprehension_questions`, `pronunciation_data`, `errors`, `level_attempts`) — use PostgreSQL JSON functions for structured access
- `percentile_rank` is STRING — cast or parse as needed
- WCPM scale: typically 0-300+ words per minute; verify benchmarks per grade
- Accuracy is percentage (0-100); comprehension scale TBD (verify with data team)

## Key Difference from ICT/RWP

- **ICT:** AI assessments flagged as CONFLICT/possibly inactive; not recommended for production reporting
- **RWP:** Rich reading assessment system with WCPM, accuracy, comprehension, adaptive leveling, pronunciation analysis (277 rows, active)
- **Moawin/Akhuwat:** Same Zavia infrastructure as RWP, same metrics and schema
- **Cross-region student AI results:** RWP and Moawin/Akhuwat comparable (same system). ICT not comparable until confirmed active.

## Important Notes

- Always exclude test users via `testing_account = false` on BOTH Zavia and Schoolpilot (global rule)
- Phone_number is the join key; verify it's populated and not null
- `student_identifier` is STRING with no FK; students not linked to Schoolpilot student table
- If reading_assessments table grows significantly, coordinate with data team on partitioning strategy
- organization_id values must be verified with data team before hardcoding
- Verify exact WCPM benchmarks and comprehension score scale with data team for dashboard display

## Data Status
- Status: MATCHED (per Moawin/Akhuwat reconciliation notes)
- Last verified: April 2026
- Related global rules: Test user exclusion (data-governance.md), Database priority (data-governance.md)
