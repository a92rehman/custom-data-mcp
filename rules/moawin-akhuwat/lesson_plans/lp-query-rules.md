# Lesson Plan Query Rules — Moawin / Akhuwat

## When These Rules Apply

User asks about:
- AI lesson plan generation counts in Moawin or Akhuwat
- LP volume, trends, or breakdown by grade/subject
- Teacher LP activity or engagement
- Lesson plan completion or delivery metrics

## Mandatory Clarifications

### Engagement / Usage / Retention Queries
If the user asks about LP **engagement**, **usage**, or **retention**, always ask:
- "What specific duration? (e.g., last 7 days, last 30 days, this week, this month)"
- Never assume a time window — engagement metrics are meaningless without an explicit period
- Clarify whether they mean: active teachers generating LPs (usage), repeat generation over time (retention), or LP volume trend (engagement)

### Region
Always ask: "Moawin or Akhuwat?"
- Filter by teacher's `organization_id` via LEFT JOIN to `neondb.public.users`
- Verify exact organization_id values with data team

### Time Period
Ask: "Which time period? Date range, this month, all-time?"
- `created_at` (DATETIME/TIMESTAMP) is the primary timestamp

### Breakdown
Ask if relevant: "Total count, or breakdown by grade/subject/teacher?"
- `grade` and `subject` columns available for segmentation

## Key Tables

| Table | Role | Database | Rows | Status |
|-------|------|----------|------|--------|
| `zavia1.public.lesson_plans` | AI-generated LP records | Zavia (PostgreSQL) | ~4,759 (RWP baseline) | **CANONICAL** |
| `zavia1.public.lesson_plan_requests` | LP request/flow tracking (supporting) | Zavia | Variable | Supporting |
| `zavia1.public.users` | LP creator identity (user_id) | Zavia | 5,319 | For join |
| `neondb.public.users` | Teacher enrichment (organization_id, status) | Schoolpilot | 1,296+ (Moawin+Akhuwat) | For regional filter |

**Note:** These tables are small and unpartitioned. Full scans acceptable at this scale. Revisit if lesson_plans table grows beyond 100,000 rows.

## Key Columns — zavia1.public.lesson_plans

- `id` — primary key (STRING), use `COUNT(DISTINCT id)` for LP count
- `user_id` — FK to `zavia1.public.users.id` (LP creator)
- `topic` — lesson topic / title
- `grade` — grade level (STRING, e.g., "Grade 5")
- `subject` — subject name (STRING, e.g., "Math", "English", "Science")
- `type` — LP type categorization (e.g., "AI-generated", "structured", "narrative")
- `source` — generation source (e.g., "AI", "template", "custom")
- `lp_variant` — LP variant for A/B testing (if applicable)
- `ab_group` — A/B test group assignment (if applicable)
- `created_at` — DATETIME/TIMESTAMP when LP was generated
- `updated_at` — last modification timestamp (optional)

## Join Pattern (Regional Filter)

Every LP query for Moawin/Akhuwat MUST filter to the region via teacher organization_id:

```sql
SELECT lp.*, zu.*, nu.organization_id
FROM zavia1.public.lesson_plans lp
JOIN zavia1.public.users zu ON lp.user_id = zu.id
LEFT JOIN neondb.public.users nu ON zu.phone_number = nu.phone_number
WHERE nu.organization_id IN (<moawin_org_id>, <akhuwat_org_id>)
  AND zu.testing_account = false
  AND nu.testing_account = false
  AND nu.status = 'active'
```

**Alternative (if phone_number not available):** Use email or other stable identifier; coordinate with data team on best join key.

## Counting Rules

- LP count = `COUNT(DISTINCT lp.id)` — never count raw rows
- Unique teachers with LPs = `COUNT(DISTINCT lp.user_id)`
- Never assume one LP per teacher — teachers can generate multiple LPs
- Teachers with LPs = `COUNT(DISTINCT lp.user_id WHERE lp.created_at >= DATE('...'))`

## Filtering Rules

- Exclude test users: `zu.testing_account = false` (Zavia) AND `nu.testing_account = false` (Schoolpilot)
- Exclude test/inactive users: `nu.status = 'active'`
- Include date filter on `lp.created_at >= DATE('...')` per global bigquery rules (partition-first)

## Reporting Grain

Daily / Weekly / Monthly, with optional grade/subject breakdown

## Aggregation Patterns

| User asks about | GROUP BY | Aggregate |
|-----------------|----------|-----------|
| Total LPs generated (all-time) | — | `COUNT(DISTINCT lp.id)` |
| Total LPs (by region) | `nu.organization_id` | `COUNT(DISTINCT lp.id)` |
| LPs per teacher | `lp.user_id` | `COUNT(DISTINCT lp.id)` |
| LPs per school | `nt.school_assignment` (via teacher join) | `COUNT(DISTINCT lp.id)` |
| LPs by grade | `lp.grade` | `COUNT(DISTINCT lp.id)` |
| LPs by subject | `lp.subject` | `COUNT(DISTINCT lp.id)` |
| LPs by grade + subject | `lp.grade`, `lp.subject` | `COUNT(DISTINCT lp.id)` |
| Daily trend | `DATE(lp.created_at)` | `COUNT(DISTINCT lp.id)` |
| Weekly trend | `DATE_TRUNC(lp.created_at, WEEK(SATURDAY))` or `DATE_TRUNC(lp.created_at, 7 DAY)` (PostgreSQL dialect) | `COUNT(DISTINCT lp.id)` |
| Monthly trend | `DATE_TRUNC(lp.created_at, MONTH)` | `COUNT(DISTINCT lp.id)` |
| Active LP teachers | — | `COUNT(DISTINCT lp.user_id WHERE lp.created_at >= DATE('...')` |
| Teachers with LPs in period | `DATE_TRUNC(lp.created_at, MONTH)` | `COUNT(DISTINCT lp.user_id)` |

## Data Conventions

- Timezone: `Asia/Karachi` for all date/timestamp conversions
- Weeks run Saturday to Friday (consistent with Taleemabad convention)
- `grade` and `subject` are STRING type — may need normalization (e.g., "Class 5" vs "Grade 5")
- `created_at` is primary timestamp; use for partitioning/filtering

## Key Difference from ICT/RWP

- **ICT:** Counts LP starts + completions from `analytics_events`, computes completion rate vs timetable (On-Schedule/Off-Schedule)
- **RWP:** Counts generated records from `RUMI_DB.lesson_plans`, no completion tracking, no timetable
- **Moawin/Akhuwat:** Counts generated records from `zavia1.lesson_plans`, no completion tracking, no timetable context (similar to RWP)
- **Cross-region LP comparison:** Volume only (total LPs generated). Completion rate incomparable due to different methodologies.

## Important Notes

- Always exclude test users via `testing_account = false` on BOTH Zavia and Schoolpilot (global rule)
- Phone_number or email may be used for join; verify stable identifier exists and is not null/empty
- If lesson_plans table grows significantly, coordinate with data team on partitioning strategy
- Verify exact `grade` and `subject` values in table and normalize for dashboard display as needed
- organization_id values for Moawin and Akhuwat must be verified with data team before hardcoding

## Data Status
- Status: MATCHED (per Moawin/Akhuwat reconciliation notes)
- Last verified: April 2026
- Related global rules: Test user exclusion (data-governance.md), Database priority (data-governance.md)
