# AI Coaching Query Rules — Moawin / Akhuwat

## When These Rules Apply

User asks about:
- AI coaching sessions in Moawin or Akhuwat
- Coaching session counts, trends, or completion rates
- Coaching results: analysis outputs, transcripts, or quality metrics
- Lesson plan fidelity scores from coaching
- Teacher satisfaction or coaching quality metrics
- Coaching pipeline status or errors

## Mandatory Clarifications

### Query Type
Ask: "Session count, coaching results (analysis/transcripts), quality metrics, or lesson fidelity?"

### Session Filter
Ask: "All sessions or completed only?"
- Default for KPI reporting: `status = 'completed'` only

### Time Period
Ask: "Which time period?"

### Region
Ask: "Moawin or Akhuwat?"

## Key Tables

| Table | Role | Dataset | Rows | Status |
|-------|------|---------|------|--------|
| `Zavia_db.coaching_sessions` | AI coaching session records | Zavia (BigQuery) | 170 | **CANONICAL** |
| `Zavia_db.coaching_quality_metrics` | Quality and performance metrics | Zavia | 125 | For enrichment |
| `Zavia_db.audio_sessions` | Raw audio uploads (pre-processing) | Zavia | Variable | Supporting |
| `Zavia_db.users` | Session creator identity | Zavia | 5,319 | For join |
| `Muawin_Akhuwat_db.teachers` | Teacher enrichment (school, org) | Schoolpilot | Variable | For regional filter |

## Key Columns — Zavia_db.coaching_sessions

### Identity & Status
- `id` — primary key (UUID)
- `user_id` — FK to `Zavia_db.users.id`
- `session_id` — FK to `Zavia_db.chat_sessions.id`
- `status` — `completed`, `failed`, `in_progress`, `initiated`, `cancelled`, `test_cleanup`, `awaiting_photo`, `awaiting_lesson_plan`
- `last_successful_step`, `failed_step`, `error_message`, `can_resume` — pipeline diagnostics

### Audio & Transcript
- `audio_url`, `audio_duration_seconds`, `audio_format`, `audio_size_bytes`, `audio_id`
- `transcript_text`, `transcript_language`
- `diarization_data` (JSONB → STRING), `diarization_confidence`

### Lesson Plan Context
- `lesson_plan_url`, `lesson_plan_text`, `lesson_plan_structured` (JSONB → STRING)
- `lesson_plan_format`, `has_lesson_plan`, `lesson_plan_word_count`, `lesson_plan_extraction_status`

### Analysis & Reports
- `analysis_data` (JSONB → STRING) — contains `fidelity_analysis.score` (0-100) when `has_lesson_plan = true`
- `conversation_state` (JSONB → STRING), `silence_markers` (JSONB → STRING), `tokens_raw` (JSONB → STRING)
- `report_pdf_url`, `report_generated_at`, `report_gamma_url`
- `voice_debrief_url`, `voice_debrief_duration_seconds`

### Cost & Tokens
- `transcription_cost`, `analysis_cost`, `total_cost` (FLOAT)
- `gpt5_input_tokens`, `gpt5_output_tokens`, `gpt5_cached_tokens` (FLOAT)

### Timestamps
- `created_at`, `confirmed_at`, `transcription_started_at`, `transcription_completed_at`
- `analysis_started_at`, `analysis_completed_at`, `completed_at`, `updated_at`, `reminder_sent_at`

## Key Columns — Zavia_db.coaching_quality_metrics

- `coaching_session_id` — FK to `coaching_sessions.id`
- `diarization_confidence` (FLOAT, 0-1)
- `processing_time_seconds`, `transcription_time_seconds`, `analysis_time_seconds`, `report_generation_time_seconds` (INT)
- `user_satisfaction_rating` (STRING — cast to FLOAT for aggregation)
- `user_feedback` — free text
- `worker_id` — processing worker ID
- `retry_count` (INT), `had_errors` (BOOLEAN)
- `session_cost` (FLOAT)
- `created_at`

## Join Pattern (Regional Filter)

```sql
SELECT cs.*, cqm.*, zu.name AS teacher_name, zu.phone_number,
       t.school_id, t.designation, s.name AS school_name
FROM Zavia_db.coaching_sessions cs
JOIN Zavia_db.users zu ON cs.user_id = zu.id
LEFT JOIN Muawin_Akhuwat_db.teachers t ON t.zavia_user_id = zu.id
LEFT JOIN Muawin_Akhuwat_db.schools s ON t.school_id = s.id
LEFT JOIN Zavia_db.coaching_quality_metrics cqm ON cqm.coaching_session_id = cs.id
WHERE t.organization_id IN (<moawin_org_id>, <akhuwat_org_id>)
  AND zu.is_test_user = false
  AND t.status = 'ACTIVE'
  AND cs.status = 'completed'  -- FOR KPI REPORTING
```

## Status Values

| Status | Meaning | Include in KPI? |
|--------|---------|-----------------|
| `completed` | Successfully processed | YES (default) |
| `failed` | Processing failed | Only for diagnostics |
| `test_cleanup` | Test data | **NEVER** |
| `cancelled` | User cancelled | Only if asked |
| `initiated` | Started, not completed | Only for diagnostics |
| `in_progress` | Actively processing | Only for diagnostics |
| `awaiting_photo` | Waiting for photo | Only for diagnostics |
| `awaiting_lesson_plan` | Waiting for LP | Only for diagnostics |

## Filtering Rules

- Zavia test exclusion: `zu.is_test_user = false`
- Schoolpilot active: `t.status = 'ACTIVE'`
- Always exclude: `cs.status != 'test_cleanup'`
- KPI default: `cs.status = 'completed'`
- Lesson fidelity: add `JSON_VALUE(cs.analysis_data, '$.has_lesson_plan') = 'true'`

## Counting Rules

- Session count = `COUNT(DISTINCT cs.id)`
- Completion rate = `COUNTIF(cs.status = 'completed') / COUNTIF(cs.status != 'test_cleanup')`
- Teachers with coaching = `COUNT(DISTINCT cs.user_id)`

## Aggregation Patterns

| User asks about | GROUP BY | Aggregate |
|-----------------|----------|-----------|
| Total sessions (completed) | — | `COUNT(DISTINCT cs.id) WHERE status='completed'` |
| Sessions by region | `t.organization_id` | `COUNT(DISTINCT cs.id)` |
| Sessions per teacher | `cs.user_id` | `COUNT(DISTINCT cs.id)` |
| Completion rate | — | `COUNTIF(status='completed') / COUNTIF(status!='test_cleanup')` |
| Avg processing time | — | `AVG(cqm.processing_time_seconds)` |
| Avg satisfaction | — | `AVG(CAST(cqm.user_satisfaction_rating AS FLOAT64))` |
| Total cost | — | `SUM(cs.total_cost)` |
| Avg lesson fidelity | — | `AVG(CAST(JSON_VALUE(cs.analysis_data, '$.fidelity_analysis.score') AS FLOAT64))` |
| Sessions by week | `DATE_TRUNC(cs.created_at, WEEK(SATURDAY))` | `COUNT(DISTINCT cs.id)` |
| Error rate | — | `COUNTIF(cqm.had_errors) / COUNT(*)` |

## Data Conventions

- Timezone: `Asia/Karachi`
- Weeks: Saturday to Friday
- `analysis_data` is JSONB → STRING — use `JSON_VALUE()` for structured access
- `user_satisfaction_rating` is STRING — cast to FLOAT64 for numeric aggregation
- Lesson fidelity score (0-100) only when `has_lesson_plan = true`

## Key Difference from ICT/RWP

- **ICT:** Same observation stack as human coaching, FICO B/C/D sections
- **RWP:** Separate audio-based system via RUMI_DB (same architecture as Moawin/Akhuwat)
- **Moawin/Akhuwat:** Audio-based via Zavia_db, includes lesson fidelity scoring
- **Cross-region:** Session count + completion rate only

## Important Notes

- Join to Schoolpilot via `teachers.zavia_user_id` (NOT phone_number on users table)
- Zavia test filter: `is_test_user = false` (NOT `testing_account`)
- `analysis_data` JSON path: `$.fidelity_analysis.score` for fidelity

## Data Status
- Status: SCHEMA VERIFIED
- Last verified: April 2026
