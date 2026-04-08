# Human Coaching Query Rules — Rawalpindi

## When These Rules Apply

User asks about:
- Human coaching/mentoring visits in Rawalpindi
- Observation feedback (strengths, areas for improvement, action items)
- Teacher coverage by mentors/observers
- Coaching session counts or trends
- Voice note transcriptions from visits

## Mandatory Clarifications

### Query Type
Ask: "Session count, or detailed coaching results (feedback text)?"

### Time Period
Ask: "Which time period?"
- `visit_date` is the date column for aggregation

### Aggregation Level
Ask: "Per school, per observer, per teacher, or overall?"

## Key Tables

| Table | Role | Rows | Dataset |
|-------|------|------|---------|
| `TaleemHub_DB.mentoring_visits` | Human coaching visit records | 95 | TaleemHub_DB |
| `TaleemHub_DB.users` | Observer/mentor identity | 1,296 | TaleemHub_DB |

**Explicitly NOT:** `TaleemHub_DB.monitoring_visits` — this is a separate table for infrastructure/compliance monitoring, NOT coaching.

**Note:** These tables are small and unpartitioned. Full scans are acceptable at this scale.

## Key Columns — TaleemHub_DB.mentoring_visits

### Identity & Context
- `id` — primary key (STRING), use `COUNT(DISTINCT id)` for visit count
- `user_id` — FK to `TaleemHub_DB.users.id` (the observer/mentor who conducted the visit)
- `observer_name`, `observer_designation` — observer identity and role
- `teacher_name` — observed teacher (STRING, no FK — see Teacher Matching Note)
- `teacher_cnic` — observed teacher CNIC (STRING, no FK — preferred for matching)
- `school_id`, `school_name` — school where visit occurred
- `visit_date` — date of visit (STRING, use for time-based aggregation)
- `arrival_time`, `departure_time` — visit duration
- `class_observed`, `grade_observed`, `subject` — classroom context
- `markaz`, `tehsil` — geographic hierarchy
- `rubric_type` — may indicate structured rubric (future use)
- `role_id` — observer role (FLOAT)

### Coaching Results (all inline, unstructured narrative)
- `general_feedback` — free text overall feedback
- `strengths_observed` — what went well
- `areas_for_improvement` — what needs work
- `action_items` — next steps for the teacher
- `evidence` — supporting evidence/notes
- `voice_note_transcription` — transcribed voice notes from the visit
- `voice_note_url` — URL to audio evidence
- `tm_notes` — team manager notes

### Geo-verification
- `captured_latitude`, `captured_longitude` — GPS coordinates of visit
- `captured_location_source` — how location was captured

### Status
- `status` — all current records are `submitted` (95/95)
- Default filter: `status = 'submitted'`

## Teacher Matching Note

`teacher_name` and `teacher_cnic` are string fields with **no foreign key** to the users table. For reliable teacher-level aggregation:
- **Prefer `teacher_cnic`** over `teacher_name` (names have spelling variations, CNIC is more stable)
- CNIC format may vary (with/without dashes) — normalize before matching
- If CNIC matching proves unreliable, flag as a data quality gap

## Key Difference from ICT

- ICT has **structured scoring** — `coaching_observationanswer` with yes/partial/no answers, numeric scores, FICO sections B/C/D
- RWP is **unstructured narrative** — free text feedback fields, no numeric scores, no sections
- Cross-region coaching comparison: **session count** and **coverage %** (teachers observed / total teachers) only. Score-based comparison is NOT valid.

## Required Filters

- `status = 'submitted'` — valid visits only (currently all records)
- `visit_date` — for time range filtering

## Aggregation Patterns

| User asks about | GROUP BY | Aggregate |
|-----------------|----------|-----------|
| Total visits | — | `COUNT(DISTINCT mv.id)` |
| Visits per school | `mv.school_id`, `mv.school_name` | `COUNT(DISTINCT mv.id)` |
| Visits per observer | `mv.user_id`, `mv.observer_name` | `COUNT(DISTINCT mv.id)` |
| Visits per teacher | `mv.teacher_cnic` | `COUNT(DISTINCT mv.id)` |
| Teacher coverage | — | `COUNT(DISTINCT mv.teacher_cnic)` / total active teachers |
| Visits per tehsil/markaz | `mv.tehsil`, `mv.markaz` | `COUNT(DISTINCT mv.id)` |
| Weekly trend | `DATE(mv.visit_date)` grouped by week | `COUNT(DISTINCT mv.id)` |
| Monthly trend | `DATE(mv.visit_date)` grouped by month | `COUNT(DISTINCT mv.id)` |

## Data Conventions

- Timezone: `Asia/Karachi` for all date conversions
- `visit_date` is stored as STRING — cast to DATE for aggregation: `PARSE_DATE('%Y-%m-%d', mv.visit_date)`
- One visit = one classroom observation session
