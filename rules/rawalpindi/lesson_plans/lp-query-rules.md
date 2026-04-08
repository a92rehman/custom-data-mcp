# Lesson Plan Query Rules — Rawalpindi

## When These Rules Apply

User asks about:
- AI lesson plan generation in Rawalpindi
- LP counts, volume, or trends
- LP breakdown by grade or subject
- Teacher LP activity or engagement

## Mandatory Clarifications

### Time Period
Ask: "Which time period? Specific date range, or all-time?"
- `created_at` (DATETIME) is the timestamp column

### Breakdown
Ask if relevant: "Breakdown by grade/subject, or total count?"
- `grade` and `subject` columns available for segmentation

## Key Tables

| Table | Role | Rows | Dataset |
|-------|------|------|---------|
| `RUMI_DB.lesson_plans` | AI-generated lesson plan records | 4,759 | RUMI_DB |
| `RUMI_DB.users` | User bridge (LP creator → phone_number) | 5,319 | RUMI_DB |
| `TaleemHub_DB.users` | RWP cohort filter | 1,296 | TaleemHub_DB |

**Note:** These tables are small and unpartitioned. Full scans are acceptable at this scale.

## Key Columns — RUMI_DB.lesson_plans

- `id` — primary key (STRING), use `COUNT(DISTINCT id)` for LP count
- `user_id` — FK to `RUMI_DB.users.id`
- `topic` — lesson topic
- `grade` — grade level (STRING)
- `subject` — subject name (STRING)
- `type` — LP type categorization
- `source` — generation source
- `lp_variant` — LP variant for A/B testing
- `ab_group` — A/B test group assignment
- `created_at` (DATETIME) — when the LP was generated

## Join Path (RWP Cohort Filter)

Every LP query for Rawalpindi MUST filter to the RWP teacher cohort:

```sql
SELECT ...
FROM RUMI_DB.lesson_plans lp
JOIN RUMI_DB.users ru ON lp.user_id = ru.id
JOIN TaleemHub_DB.users th ON ru.phone_number = th.phone_number
WHERE ru.is_test_user IS NOT TRUE
  AND th.status = 'active'
```

## Counting Rules

- LP count = `COUNT(DISTINCT lp.id)` — never count raw rows
- Unique teachers with LPs = `COUNT(DISTINCT lp.user_id)`
- Never assume one LP per teacher — teachers can generate multiple LPs

## Key Difference from ICT

- ICT counts LP **starts and completions** from `events_partitioned`, computes `lp_ratio` (completion rate) against timetable schedule
- RWP counts **generated records** — one row in `RUMI_DB.lesson_plans` = one AI-generated LP delivered to a teacher
- RWP has no timetable data → no completion rate, no On-Schedule/Off-Schedule concept
- **Cross-region LP comparison is volume only** (total LPs generated)

## Reporting Grain

Daily / Weekly / Monthly, with optional grade/subject breakdown

## Aggregation Patterns

| User asks about | GROUP BY | Aggregate |
|-----------------|----------|-----------|
| Total LPs generated | — | `COUNT(DISTINCT lp.id)` |
| LPs per teacher | `lp.user_id` | `COUNT(DISTINCT lp.id)` |
| LPs per school | `th.school_id`, `th.school_name` | `COUNT(DISTINCT lp.id)` |
| LPs by grade | `lp.grade` | `COUNT(DISTINCT lp.id)` |
| LPs by subject | `lp.subject` | `COUNT(DISTINCT lp.id)` |
| LPs by grade + subject | `lp.grade`, `lp.subject` | `COUNT(DISTINCT lp.id)` |
| Daily trend | `DATE(lp.created_at)` | `COUNT(DISTINCT lp.id)` |
| Weekly trend | `DATE_TRUNC(lp.created_at, WEEK(SATURDAY))` | `COUNT(DISTINCT lp.id)` |
| Monthly trend | `DATE_TRUNC(lp.created_at, MONTH)` | `COUNT(DISTINCT lp.id)` |
| Active LP teachers | — | `COUNT(DISTINCT lp.user_id)` |

## Data Conventions

- Timezone: `Asia/Karachi` for all date conversions
- Weeks run Saturday to Friday (consistent with ICT convention)
