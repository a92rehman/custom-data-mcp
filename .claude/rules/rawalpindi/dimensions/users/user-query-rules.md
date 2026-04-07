# User Query Rules — Rawalpindi

## When These Rules Apply

User asks about:
- Rawalpindi teacher profiles, registration, or institutional attributes
- User counts, cohort size, school assignments
- Rumi-TaleemHub user matching
- Teacher roster for Rawalpindi

## Mandatory Clarifications

### Role
Ask: "Which role? TEACHER, HEAD_TEACHER, or all?"
- Known roles: `TEACHER` (1002), `HEAD_TEACHER` (255), `AEO` (23), `TRAINING_MANAGER` (8), `SUPER_ADMIN` (4), `DDEO` (2), `DEO` (2)
- For teacher KPIs, default to `role = 'TEACHER'` unless user specifies otherwise

### Geographic Scope
Ask: "All Rawalpindi, or specific tehsil/markaz?"
- Geographic hierarchy: `district_id` → `tehsil_id`/`tehsil_name` → `markaz_id`/`markaz_name`

## Key Tables

| Table | Role | Rows | Dataset |
|-------|------|------|---------|
| `TaleemHub_DB.users` | Canonical teacher roster | 1,296 | TaleemHub_DB |
| `RUMI_DB.users` | Join helper for Rumi data (AI LP, coaching, assessments) | 5,319 | RUMI_DB |

**Note:** These tables are small and unpartitioned. Full scans are acceptable at this scale. Revisit if tables grow beyond 10,000 rows.

## Key Columns — TaleemHub_DB.users

- `id` — primary key (STRING)
- `name`, `phone_number`, `cnic` — identity
- `role` — user type: TEACHER, HEAD_TEACHER, AEO, TRAINING_MANAGER, SUPER_ADMIN, DDEO, DEO
- `status` — `active` (1171), `pending` (124), `approved` (1)
- `school_id`, `school_name` — school assignment
- `district_id`, `tehsil_id`, `tehsil_name`, `markaz_id`, `markaz_name` — geographic hierarchy
- `role_id` — numeric role identifier (FLOAT)
- `gender` — teacher gender
- `created_at`, `date_of_joining` — temporal
- `whatsapp_number` — may differ from phone_number

## Key Columns — RUMI_DB.users

- `id` — primary key (STRING, Rumi user ID)
- `phone_number` — join key to TaleemHub
- `is_test_user` — BOOLEAN, must exclude `true`
- `region`, `organization` — Rumi-side context (can filter RWP when querying Rumi directly)
- `registration_completed` — BOOLEAN, whether fully onboarded
- `name`, `first_name`, `last_name` — identity
- `school_name`, `subjects_taught`, `grades_taught` — teaching context
- `emis_code` — school EMIS if available

## Join Logic (TaleemHub → Rumi)

Use this join whenever a query needs Rumi data (lesson plans, AI coaching, reading assessments) for the RWP cohort:

```sql
TaleemHub_DB.users th
LEFT JOIN RUMI_DB.users ru ON th.phone_number = ru.phone_number
  AND ru.is_test_user IS NOT TRUE
```

Use `LEFT JOIN` to keep all TaleemHub teachers; `INNER JOIN` only when Rumi data is required.

## Required Filters

- `th.status = 'active'` — active users only (default). Include `pending`/`approved` only if user explicitly asks.
- `ru.is_test_user IS NOT TRUE` — exclude Rumi test accounts when joining
- `th.role` — filter by role for teacher-specific queries

## Region Filter Strategy

`TaleemHub_DB.users` currently contains only Rawalpindi users. If TaleemHub expands to other regions:
- Add `th.district_id` filter for Rawalpindi-specific queries
- `RUMI_DB.users` has `region` and `organization` columns — use these when querying Rumi directly without TaleemHub join

## Aggregation Patterns

| User asks about | GROUP BY | Aggregate |
|-----------------|----------|-----------|
| Total teachers | — | `COUNT(DISTINCT th.id)` |
| Teachers per school | `th.school_id`, `th.school_name` | `COUNT(DISTINCT th.id)` |
| Teachers per tehsil/markaz | `th.tehsil_name`, `th.markaz_name` | `COUNT(DISTINCT th.id)` |
| Teachers with Rumi match | — | `COUNT(DISTINCT th.id) WHERE ru.id IS NOT NULL` (use LEFT JOIN) |
| Teachers by role | `th.role` | `COUNT(DISTINCT th.id)` |
| Teachers by status | `th.status` | `COUNT(DISTINCT th.id)` |

## Data Conventions

- Timezone: `Asia/Karachi` for all date conversions
- `phone_number` is the universal join key between TaleemHub and Rumi
- A teacher appears once in TaleemHub (one row per user)
- A teacher may or may not exist in Rumi — not all teachers use the AI tools
