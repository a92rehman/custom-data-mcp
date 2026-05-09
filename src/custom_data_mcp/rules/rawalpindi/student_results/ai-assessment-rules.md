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
