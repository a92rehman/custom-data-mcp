# AI Coaching Query Rules — Rawalpindi

## When These Rules Apply

User asks about:
- AI coaching sessions in Rawalpindi
- Audio coaching analysis or transcripts
- Coaching quality metrics (processing time, satisfaction)
- AI coaching costs or token usage
- Teacher satisfaction with AI coaching
- Coaching pipeline status or errors

## Mandatory Clarifications

### Query Type
Ask: "Session count, coaching results (analysis/transcripts), or quality metrics?"

### Session Filter
Ask: "All sessions or completed only?"
- Default KPI reporting: `status = 'completed'` only
- Include all statuses only if user explicitly asks for pipeline diagnostics

### Time Period
Ask: "Which time period?"
- `created_at` (TIMESTAMP) is the primary timestamp

## Key Tables

| Table | Role | Rows | Dataset |
|-------|------|------|---------|
| `RUMI_DB.coaching_sessions` | AI coaching session records | 170 | RUMI_DB |
| `RUMI_DB.coaching_quality_metrics` | Quality and performance metrics | 125 | RUMI_DB |
| `RUMI_DB.users` | User bridge | 5,319 | RUMI_DB |
| `TaleemHub_DB.users` | RWP cohort filter | 1,296 | TaleemHub_DB |

**Note:** These tables are small and unpartitioned. Full scans are acceptable at this scale.

## Join Path

```sql
-- Session data with RWP cohort filter
SELECT ...
FROM RUMI_DB.coaching_sessions cs
JOIN RUMI_DB.users ru ON cs.user_id = ru.id
JOIN TaleemHub_DB.users th ON ru.phone_number = th.phone_number
WHERE ru.is_test_user IS NOT TRUE
  AND th.status = 'active'

-- With quality metrics
LEFT JOIN RUMI_DB.coaching_quality_metrics cqm ON cqm.coaching_session_id = cs.id
```

## Status Values

| Status | Count | Meaning | Include in KPI? |
|--------|-------|---------|-----------------|
| `completed` | 124 | Successfully processed | YES (default) |
| `failed` | 29 | Processing failed | Only for diagnostics |
| `test_cleanup` | 7 | Test data cleanup | NEVER |
| `cancelled` | 4 | User cancelled | Only if asked |
| `initiated` | 3 | Started, not completed | Only for diagnostics |
| `awaiting_photo` | 2 | Waiting for photo upload | Only for diagnostics |
| `awaiting_lesson_plan` | 1 | Waiting for LP upload | Only for diagnostics |

Default KPI filter: `cs.status = 'completed'`
Exclude always: `cs.status != 'test_cleanup'`

## Key Columns — coaching_sessions

### Identity & Status
- `id` — primary key (STRING)
- `user_id` — FK to `RUMI_DB.users.id`
- `status` — session status (see Status Values above)
- `last_successful_step`, `failed_step`, `error_message`, `can_resume` — pipeline diagnostics

### Pipeline Timestamps
- `created_at` → `confirmed_at` → `transcription_started_at` → `transcription_completed_at` → `analysis_started_at` → `analysis_completed_at` → `completed_at`
- All TIMESTAMP type

### Coaching Content
- `transcript_text` — full lesson transcript (STRING, can be large)
- `analysis_data` — AI analysis output (JSON STRING — parse with `JSON_VALUE()` for structured queries)
- `lesson_plan_text`, `lesson_plan_excerpt` — LP being coached against
- `report_pdf_url` — generated PDF coaching report
- `voice_debrief_url`, `voice_debrief_duration_seconds` — AI voice debrief for teacher
- `prioritized_action` — key action item from AI analysis
- `agency_response` — teacher's reflection/response
- `classroom_photos`, `photo_analysis` — visual evidence (JSON STRING)

### Audio
- `audio_url`, `audio_duration_seconds`, `audio_format`, `audio_size_bytes`
- `transcript_language` — detected language

### Cost
- `transcription_cost`, `analysis_cost`, `total_cost` — per-session cost (FLOAT)
- `gpt5_input_tokens`, `gpt5_output_tokens`, `gpt5_cached_tokens` — token usage (FLOAT)

## Key Columns — coaching_quality_metrics

- `coaching_session_id` — FK to `coaching_sessions.id`
- `diarization_confidence` — audio quality score (FLOAT)
- `processing_time_seconds`, `transcription_time_seconds`, `analysis_time_seconds` — performance (INTEGER/INTEGER/INTEGER)
- `user_satisfaction_rating` — teacher rating (STRING — cast to FLOAT64 for aggregation)
- `user_feedback` — free text teacher feedback
- `session_cost` — cost from quality perspective (FLOAT)
- `had_errors` — BOOLEAN, whether errors occurred
- `retry_count` — INTEGER, number of retries

## Key Difference from ICT

- ICT AI coaching uses the **same observation stack** with `coaching_observationquestion.source = 'automated'`, scored via FICO B/C/D sections
- RWP AI coaching is a **completely separate audio-based system** — records classroom audio, transcribes, runs AI analysis, generates reports
- Cross-region AI coaching comparison: **session count** and **completion rate** only. Score/quality comparison is NOT valid.

## Counting Rules

- Session count = `COUNT(DISTINCT cs.id)` with appropriate status filter
- Completion rate = `COUNTIF(cs.status = 'completed') / COUNTIF(cs.status != 'test_cleanup')`
- Teachers with AI coaching = `COUNT(DISTINCT cs.user_id)`

## Aggregation Patterns

| User asks about | GROUP BY | Aggregate |
|-----------------|----------|-----------|
| Total sessions | — | `COUNT(DISTINCT cs.id)` |
| Sessions per teacher | `cs.user_id` | `COUNT(DISTINCT cs.id)` |
| Completion rate | — | `COUNTIF(status='completed') / COUNTIF(status!='test_cleanup')` |
| Avg processing time | — | `AVG(cqm.processing_time_seconds)` |
| Avg satisfaction | — | `AVG(CAST(cqm.user_satisfaction_rating AS FLOAT64))` |
| Total cost | — | `SUM(cs.total_cost)` |
| Avg cost per session | — | `AVG(cs.total_cost)` |
| Sessions by week | `DATE_TRUNC(cs.created_at, WEEK(SATURDAY))` | `COUNT(DISTINCT cs.id)` |
| Sessions by month | `DATE_TRUNC(cs.created_at, MONTH)` | `COUNT(DISTINCT cs.id)` |
| Error rate | — | `COUNTIF(cqm.had_errors) / COUNT(*)` |
| By status (diagnostics) | `cs.status` | `COUNT(DISTINCT cs.id)` |

## Data Conventions

- Timezone: `Asia/Karachi` for all date/timestamp conversions
- `analysis_data` is a JSON string — use `JSON_VALUE(cs.analysis_data, '$.key')` for structured access
- `user_satisfaction_rating` is stored as STRING — cast to FLOAT64 for numeric aggregation
- Weeks run Saturday to Friday (consistent with ICT convention)
