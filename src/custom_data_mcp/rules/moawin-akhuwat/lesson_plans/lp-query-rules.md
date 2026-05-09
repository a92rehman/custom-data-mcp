# Lesson Plan Query Rules — Moawin / Akhuwat

## When These Rules Apply

User asks about:
- AI lesson plan generation counts in Moawin or Akhuwat
- LP volume, trends, or breakdown by grade/subject
- Teacher LP activity or engagement
- Lesson plan request pipeline (status, errors, retries)

## Mandatory Clarifications

### Engagement / Usage / Retention Queries
If the user asks about LP **engagement**, **usage**, or **retention**, always ask:
- "What specific duration? (e.g., last 7 days, last 30 days, this week, this month)"
- Never assume a time window

### Region
Always ask: "Moawin or Akhuwat?"
- Filter by teacher's `organization_id` via join to `Muawin_Akhuwat_db.teachers`

### Time Period
Ask: "Which time period? Date range, this month, all-time?"
- `created_at` (TIMESTAMP) is the primary timestamp

### Breakdown
Ask if relevant: "Total count, or breakdown by grade/subject/teacher?"

## Key Tables

| Table | Role | Dataset | Rows | Status |
|-------|------|---------|------|--------|
| `Zavia_db.lesson_plans` | AI-generated LP output | Zavia (BigQuery) | ~4,759 | **CANONICAL** |
| `Zavia_db.lesson_plan_requests` | LP generation request queue | Zavia | Variable | Supporting (pipeline diagnostics) |
| `Zavia_db.users` | LP creator identity | Zavia | 5,319 | For join |
| `Muawin_Akhuwat_db.teachers` | Teacher enrichment (school, org, name) | Schoolpilot | Variable | For regional filter |

## Key Columns — Zavia_db.lesson_plans

- `id` — primary key (UUID)
- `user_id` — FK to `Zavia_db.users.id`
- `topic` — lesson topic / title (STRING)
- `grade` — grade level (STRING)
- `subject` — subject name (STRING)
- `type` — LP type (STRING)
- `gamma_url` — Gamma presentation URL (STRING)
- `pdf_url` — PDF version URL (STRING)
- `content` — full LP content (JSONB → STRING in BQ, use `JSON_VALUE()`)
- `created_at` — TIMESTAMP

## Key Columns — Zavia_db.lesson_plan_requests

- `id` — primary key (UUID)
- `user_id` — FK to `Zavia_db.users.id`
- `phone_number` — requester phone (STRING)
- `topic`, `full_message`, `language`, `content_type` — request parameters
- `status` — pipeline status (STRING)
- `error_message`, `retry_count` — error tracking
- `created_at`, `processing_started_at`, `completed_at`, `last_retry_at` — timestamps

## Join Pattern (Regional Filter)

```sql
SELECT lp.*, zu.name AS teacher_name, zu.phone_number,
       t.school_id, t.designation, s.name AS school_name
FROM Zavia_db.lesson_plans lp
JOIN Zavia_db.users zu ON lp.user_id = zu.id
LEFT JOIN Muawin_Akhuwat_db.teachers t ON t.zavia_user_id = zu.id
LEFT JOIN Muawin_Akhuwat_db.schools s ON t.school_id = s.id
WHERE t.organization_id IN (<moawin_org_id>, <akhuwat_org_id>)
  AND zu.is_test_user = false
  AND t.status = 'ACTIVE'
```

**Fallback join** (if `zavia_user_id` not populated): `t.mobile_number = zu.phone_number`

## Counting Rules

- LP count = `COUNT(DISTINCT lp.id)` — never count raw rows
- Unique teachers with LPs = `COUNT(DISTINCT lp.user_id)`

## Filtering Rules

- Zavia test exclusion: `zu.is_test_user = false`
- Schoolpilot active filter: `t.status = 'ACTIVE'`
- Date filter: `lp.created_at >= TIMESTAMP('...')`

## Aggregation Patterns

| User asks about | GROUP BY | Aggregate |
|-----------------|----------|-----------|
| Total LPs generated | — | `COUNT(DISTINCT lp.id)` |
| LPs by region | `t.organization_id` | `COUNT(DISTINCT lp.id)` |
| LPs per teacher | `lp.user_id` | `COUNT(DISTINCT lp.id)` |
| LPs per school | `s.name`, `s.emis` | `COUNT(DISTINCT lp.id)` |
| LPs by grade | `lp.grade` | `COUNT(DISTINCT lp.id)` |
| LPs by subject | `lp.subject` | `COUNT(DISTINCT lp.id)` |
| Daily trend | `DATE(lp.created_at)` | `COUNT(DISTINCT lp.id)` |
| Weekly trend | `DATE_TRUNC(lp.created_at, WEEK(SATURDAY))` | `COUNT(DISTINCT lp.id)` |
| Monthly trend | `DATE_TRUNC(lp.created_at, MONTH)` | `COUNT(DISTINCT lp.id)` |
| Request pipeline health | `lpr.status` | `COUNT(DISTINCT lpr.id)` |

## Data Conventions

- Timezone: `Asia/Karachi`
- Weeks: Saturday to Friday
- `content` is JSONB → STRING in BQ — use `JSON_VALUE()` for structured access

## Key Difference from ICT/RWP

- **ICT:** LP starts/completions from `analytics_events`, completion rate vs timetable
- **RWP:** Generated records from `RUMI_DB.lesson_plans`, no completion tracking
- **Moawin/Akhuwat:** Generated records from `Zavia_db.lesson_plans`, similar to RWP
- **Cross-region:** Volume comparison only

## Important Notes

- Join to Schoolpilot via `teachers.zavia_user_id` (NOT phone_number on users table)
- Zavia test filter: `is_test_user = false` (NOT `testing_account`)
- `lesson_plan_requests` is for pipeline diagnostics, not KPI counts

## Data Status
- Status: SCHEMA VERIFIED
- Last verified: April 2026
