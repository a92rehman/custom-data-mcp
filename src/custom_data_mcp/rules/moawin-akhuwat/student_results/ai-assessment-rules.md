# Student Results — AI Assessment Query Rules — Moawin / Akhuwat

## When These Rules Apply

User asks about:
- Student AI reading assessments in Moawin or Akhuwat
- Student reading fluency (WCPM), accuracy, or comprehension scores
- Assessment outcomes, student reading levels, or on-track rates
- Pronunciation analysis or prosody scores
- Auto-levelling progression

## Mandatory Clarifications

### Metric
Ask: "Which metric? WCPM, accuracy, comprehension, fluency_score, pronunciation, or all?"

### Aggregation Level
Ask: "Per student, per teacher, per school, or overall?"

### Grade Level
Ask: "Which grade level, or all?"

### Time Period
Ask: "Which time period?"

### Region
Ask: "Moawin or Akhuwat?"

## Key Tables

| Table | Role | Dataset | Rows | Status |
|-------|------|---------|------|--------|
| `Zavia_db.reading_assessments` | Student reading assessment records (89 columns) | Zavia (BigQuery) | 277+ | **CANONICAL** |
| `Zavia_db.wcpm_percentiles` | WCPM benchmarks by grade/season | Zavia | Static | Reference |
| `Zavia_db.lcpm_benchmarks` | Letters correct per minute benchmarks | Zavia | Static | Reference |
| `Zavia_db.users` | Assessment administrator (teacher) | Zavia | 5,319 | For join |
| `Muawin_Akhuwat_db.teachers` | Teacher enrichment (school, org) | Schoolpilot | Variable | For regional filter |

## Key Columns — Zavia_db.reading_assessments

### Identity
- `id` (UUID), `user_id → users.id`, `session_id`
- `student_name`, `student_identifier`, `student_number`, `student_grade`, `grade_level` (INT), `language`

### Passage
- `passage_text`, `passage_title`, `passage_word_count`, `passage_type`, `passage_image_url`, `passage_generated_at`

### Audio
- `audio_url`, `audio_duration_seconds`, `audio_format`, `audio_size_bytes`, `audio_uploaded_at`

### Scoring (Core)
- `wcpm` — Words Correct Per Minute (FLOAT)
- `accuracy_percentage` — reading accuracy 0-100 (FLOAT)
- `fluency_score` — overall fluency (FLOAT)
- `comprehension_score` — understanding (FLOAT)
- `total_words_in_passage`, `words_read`, `words_correct` (FLOAT)
- `time_elapsed_seconds`, `self_corrections_count`

### Benchmarks
- `grade_benchmark_min`, `grade_benchmark_max` (FLOAT)
- `percentile_rank` (STRING — cast for numeric use)
- `on_track` (BOOLEAN)

### Pronunciation & Prosody
- `pronunciation_accuracy` (FLOAT)
- `pronunciation_data` (JSONB → STRING)
- `prosody_analysis` (JSONB → STRING)
- `audio_quality_score` (FLOAT)
- `errors_data`, `errors` (JSONB → STRING)

### Comprehension Detail
- `comprehension_requested` (BOOLEAN)
- `comprehension_questions`, `comprehension_answers`, `comprehension_analysis` (JSONB → STRING)

### Auto-Levelling
- `starting_level`, `final_level` (STRING)
- `level_attempts`, `auto_level_history` (JSONB → STRING)
- `current_level_attempt`, `max_attempts_per_level`

### Status & Mode
- `status` — `completed`, `passage_generated`, `fluency_completed`, `comprehension_completed`, `failed`, `abandoned`, `comprehension_in_progress`
- `assessment_mode`, `is_second_language`, `concurrent_session_count`

### Cost
- `analysis_cost`, `transcription_cost`, `report_cost`, `pronunciation_cost`, `voice_feedback_cost`, `total_cost` (FLOAT)
- `gpt4_input_tokens`, `gpt4_output_tokens`, `azure_api_calls`, `soniox_duration_seconds`

### Timestamps
- `created_at`, `updated_at`

## Join Pattern (Regional Filter)

```sql
SELECT ra.*, zu.name AS teacher_name, zu.phone_number,
       t.school_id, t.designation, s.name AS school_name
FROM Zavia_db.reading_assessments ra
JOIN Zavia_db.users zu ON ra.user_id = zu.id
LEFT JOIN Muawin_Akhuwat_db.teachers t ON t.zavia_user_id = zu.id
LEFT JOIN Muawin_Akhuwat_db.schools s ON t.school_id = s.id
WHERE t.organization_id IN (<moawin_org_id>, <akhuwat_org_id>)
  AND zu.is_test_user = false
  AND t.status = 'ACTIVE'
  AND ra.status = 'completed'  -- FOR KPI REPORTING
```

## Status Values

| Status | Count | Meaning | Include in KPI? |
|--------|-------|---------|-----------------|
| `completed` | ~142 | Fully processed | YES (default) |
| `passage_generated` | ~63 | Passage created, not started | NO |
| `fluency_completed` | ~40 | Fluency done, comprehension pending | Only if asked |
| `failed` | ~19 | Processing failed | Only for diagnostics |
| `comprehension_completed` | ~11 | Comprehension done | Only if asked |
| `abandoned` | ~1 | Abandoned | NO |

## Aggregation Patterns

| User asks about | GROUP BY | Aggregate |
|-----------------|----------|-----------|
| Total assessments (completed) | — | `COUNT(DISTINCT ra.id)` |
| Students assessed | — | `COUNT(DISTINCT ra.student_identifier)` |
| Avg WCPM | — | `AVG(ra.wcpm)` |
| Avg WCPM by grade | `ra.grade_level` | `AVG(ra.wcpm)` |
| Avg accuracy | — | `AVG(ra.accuracy_percentage)` |
| Avg comprehension | — | `AVG(ra.comprehension_score)` |
| On-track rate | — | `COUNTIF(ra.on_track) / COUNT(*)` |
| By grade | `ra.grade_level` | `AVG(ra.wcpm)`, `AVG(ra.accuracy_percentage)` |
| By teacher | `ra.user_id` | `COUNT(DISTINCT ra.id)`, `AVG(ra.wcpm)` |
| By school | `s.name`, `s.emis` | `AVG(ra.wcpm)`, `COUNT(DISTINCT ra.id)` |
| By language | `ra.language` | `AVG(ra.wcpm)` |
| Weekly trend | `DATE_TRUNC(ra.created_at, WEEK(SATURDAY))` | `COUNT(DISTINCT ra.id)`, `AVG(ra.wcpm)` |
| Monthly trend | `DATE_TRUNC(ra.created_at, MONTH)` | `COUNT(DISTINCT ra.id)` |

## Data Conventions

- Timezone: `Asia/Karachi`
- Weeks: Saturday to Friday
- JSONB fields → use `JSON_VALUE()` in BigQuery
- `percentile_rank` is STRING — cast as needed
- `wcpm_percentiles` and `lcpm_benchmarks` are static reference tables (full_replace, no watermark)

## Important Notes

- Join to Schoolpilot via `teachers.zavia_user_id` (NOT phone_number on users table)
- Zavia test filter: `is_test_user = false` (NOT `testing_account`)
- `student_identifier` has no FK — students not linked to Schoolpilot pefsis_students
- 89 columns total — only query what you need

## Data Status
- Status: SCHEMA VERIFIED
- Last verified: April 2026
