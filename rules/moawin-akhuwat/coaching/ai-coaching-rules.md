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
- Include all statuses (failed, in-progress, etc.) only for pipeline diagnostics

### Time Period
Ask: "Which time period?"
- `created_at` (TIMESTAMP) is the primary timestamp

### Region
Ask: "Moawin or Akhuwat?"
- Filter via teacher's `organization_id` through LEFT JOIN to `neondb.public.users`

## Key Tables

| Table | Role | Database | Rows | Status |
|-------|------|----------|------|--------|
| `zavia1.public.coaching_sessions` | AI coaching session records | Zavia (PostgreSQL) | 170 | **CANONICAL** |
| `zavia1.public.coaching_quality_metrics` | Quality and performance metrics | Zavia | 125 | For enrichment |
| `zavia1.public.users` | Session creator identity (user_id) | Zavia | 5,319 | For join |
| `neondb.public.users` | Teacher enrichment (organization_id, status) | Schoolpilot | 1,296+ | For regional filter |

**Note:** These tables are small and unpartitioned. Full scans acceptable at this scale.

## Key Columns — zavia1.public.coaching_sessions

### Identity & Status
- `id` — primary key (STRING), use `COUNT(DISTINCT id)` for session count
- `user_id` — FK to `zavia1.public.users.id` (teacher being coached)
- `status` — session status: `completed`, `failed`, `in_progress`, `initiated`, `cancelled`, `test_cleanup`, `awaiting_photo`, `awaiting_lesson_plan`
- `last_successful_step`, `failed_step`, `error_message`, `can_resume` — pipeline diagnostics

### Pipeline Timestamps
- `created_at` — session start (primary timestamp for filtering/grouping)
- `confirmed_at`, `transcription_started_at`, `transcription_completed_at`, `analysis_started_at`, `analysis_completed_at`, `completed_at` — milestone timestamps
- All TIMESTAMP type

### Coaching Content
- `transcript_text` — full lesson transcript (STRING, can be large)
- `analysis_data` — AI analysis output (JSON STRING — parse with JSON functions for structured access)
  - **Key field:** `fidelity_analysis.score` (0-100) — lesson plan fidelity rating when `has_lesson_plan = true`
- `lesson_plan_text`, `lesson_plan_excerpt` — LP being coached against
- `report_pdf_url` — generated PDF coaching report
- `voice_debrief_url`, `voice_debrief_duration_seconds` — AI voice debrief for teacher
- `prioritized_action` — key action item from AI analysis
- `agency_response` — teacher's reflection/response
- `classroom_photos`, `photo_analysis` — visual evidence (JSON STRING)

### Audio & Transcription
- `audio_url`, `audio_duration_seconds`, `audio_format`, `audio_size_bytes` — recorded lesson audio
- `transcript_language` — detected language

### Cost & Usage
- `transcription_cost`, `analysis_cost`, `total_cost` — per-session cost (FLOAT)
- `gpt5_input_tokens`, `gpt5_output_tokens`, `gpt5_cached_tokens` — token usage (FLOAT)

## Key Columns — zavia1.public.coaching_quality_metrics

- `coaching_session_id` — FK to `coaching_sessions.id`
- `diarization_confidence` — audio quality score (FLOAT, 0-1)
- `processing_time_seconds`, `transcription_time_seconds`, `analysis_time_seconds` — performance metrics (INT)
- `user_satisfaction_rating` — teacher rating (STRING — cast to FLOAT for aggregation, scale TBD)
- `user_feedback` — free text teacher feedback
- `session_cost` — cost perspective metric (FLOAT)
- `had_errors` — BOOLEAN, whether errors occurred
- `retry_count` — INT, number of retries

## Join Pattern (Regional Filter)

```sql
SELECT cs.*, cqm.*, zu.user_id, zu.testing_account, nu.organization_id, nu.status
FROM zavia1.public.coaching_sessions cs
JOIN zavia1.public.users zu ON cs.user_id = zu.id
LEFT JOIN neondb.public.users nu ON zu.phone_number = nu.phone_number
LEFT JOIN zavia1.public.coaching_quality_metrics cqm ON cqm.coaching_session_id = cs.id
WHERE nu.organization_id IN (<moawin_org_id>, <akhuwat_org_id>)
  AND zu.testing_account = false
  AND nu.testing_account = false
  AND nu.status = 'active'
  AND cs.status = 'completed'  -- FOR KPI REPORTING (omit for diagnostics)
```

## Status Values

| Status | Meaning | Include in KPI? |
|--------|---------|-----------------|
| `completed` | Successfully processed | YES (default) |
| `failed` | Processing failed | Only for diagnostics |
| `test_cleanup` | Test data cleanup | **NEVER** |
| `cancelled` | User cancelled | Only if asked |
| `initiated` | Started, not completed | Only for diagnostics |
| `in_progress` | Actively processing | Only for diagnostics |
| `awaiting_photo` | Waiting for photo upload | Only for diagnostics |
| `awaiting_lesson_plan` | Waiting for LP upload | Only for diagnostics |

**Default KPI filter:** `cs.status = 'completed'`
**Always exclude:** `cs.status != 'test_cleanup'`

## Filtering Rules

- Exclude test users: `zu.testing_account = false` AND `nu.testing_account = false`
- Exclude inactive users: `nu.status = 'active'`
- Include date filter on `cs.created_at >= DATE('...')` per global bigquery rules
- For lesson fidelity queries: add `cs.analysis_data::json->>'has_lesson_plan' = 'true'` (PostgreSQL JSON syntax — verify exact syntax with data team)

## Counting Rules

- Session count = `COUNT(DISTINCT cs.id)` with appropriate status filter
- Completion rate = `COUNTIF(cs.status = 'completed') / COUNTIF(cs.status != 'test_cleanup')`
- Teachers with AI coaching = `COUNT(DISTINCT cs.user_id)`
- Sessions with lesson fidelity score = `COUNT(DISTINCT cs.id) WHERE analysis_data contains fidelity_analysis.score`

## Aggregation Patterns

| User asks about | GROUP BY | Aggregate |
|-----------------|----------|-----------|
| Total sessions (completed) | — | `COUNT(DISTINCT cs.id) WHERE status='completed'` |
| Sessions by region | `nu.organization_id` | `COUNT(DISTINCT cs.id)` |
| Sessions per teacher | `cs.user_id` | `COUNT(DISTINCT cs.id)` |
| Completion rate (overall) | — | `COUNTIF(status='completed') / COUNTIF(status!='test_cleanup')` |
| Avg processing time | — | `AVG(cqm.processing_time_seconds)` |
| Avg satisfaction rating | — | `AVG(CAST(cqm.user_satisfaction_rating AS FLOAT))` |
| Total cost | — | `SUM(cs.total_cost)` |
| Avg cost per session | — | `AVG(cs.total_cost)` |
| Avg lesson fidelity score | — | `AVG(CAST(analysis_data::json->>'fidelity_analysis.score' AS FLOAT))` (PostgreSQL; adjust syntax per dialect) |
| Sessions by week | `DATE_TRUNC(cs.created_at, WEEK(SATURDAY))` or `DATE_TRUNC(cs.created_at, 7 DAY)` (PostgreSQL) | `COUNT(DISTINCT cs.id)` |
| Sessions by month | `DATE_TRUNC(cs.created_at, MONTH)` | `COUNT(DISTINCT cs.id)` |
| Error rate (diagnostics) | — | `COUNTIF(cqm.had_errors) / COUNT(*)` |
| By status (diagnostics) | `cs.status` | `COUNT(DISTINCT cs.id)` |

## Data Conventions

- Timezone: `Asia/Karachi` for all date/timestamp conversions
- Weeks run Saturday to Friday (consistent with Taleemabad convention)
- `analysis_data` is a JSON string — use appropriate PostgreSQL JSON functions for structured access (JSON_VALUE, JSON_QUERY, or `::json` casting)
- `user_satisfaction_rating` is stored as STRING — cast to FLOAT for numeric aggregation
- Lesson fidelity score (0-100) only present when `has_lesson_plan = true`

## Key Difference from ICT/RWP

- **ICT AI coaching:** Same observation stack as human coaching, scored via FICO B/C/D sections, `source='automated'` bifurcation
- **RWP AI coaching:** Separate audio-based system with transcription + analysis pipeline, quality metrics, no FICO framework
- **Moawin/Akhuwat AI coaching:** Audio-based system similar to RWP (same Zavia infrastructure), includes lesson fidelity scoring (0-100) when LP context available
- **Cross-region AI coaching comparison:** Session count + completion rate only. Fidelity scores not comparable due to different scoring frameworks (FICO vs fidelity_analysis).

## Important Notes

- Always exclude test users via `testing_account = false` on BOTH Zavia and Schoolpilot (global rule)
- Phone_number is the join key; verify it's populated and not null before joining
- `analysis_data` is JSON — verify exact structure with data team for correct path to `fidelity_analysis.score`
- If coaching_sessions table grows significantly, coordinate with data team on partitioning strategy
- organization_id values must be verified with data team before hardcoding
- Lesson fidelity score availability and scale (0-100? other?) should be confirmed with data team

## Data Status
- Status: TRANSCRIPT MATCH (per Moawin/Akhuwat reconciliation notes)
- Lesson fidelity: analysis_data contains `fidelity_analysis.score` (1-100), only when `has_lesson_plan = true`
- Last verified: April 2026
- Related global rules: Test user exclusion (data-governance.md), Database priority (data-governance.md)
