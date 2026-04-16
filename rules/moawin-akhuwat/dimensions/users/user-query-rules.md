# User Query Rules — Moawin / Akhuwat

## When These Rules Apply

User asks about:
- Moawin or Akhuwat teacher profiles, registration, or institutional attributes
- User counts, cohort size, school assignments
- Teacher roster for either region
- Teacher-level demographic or qualification data
- Teacher experience, certifications, or designations
- Geographic hierarchy (districts, tehsils, clusters, schools)

## Mandatory Clarifications

### Region
Always ask: "Moawin or Akhuwat?"
- `organization_id` on both `users` and `teachers` tables determines region
- Never assume region

### Filter Scope
Ask if relevant: "All users, active only, or specific role/designation?"
- Default: active users only (`users.is_active = true` AND `teachers.status = 'ACTIVE'`)
- Include inactive only if explicitly requested

## Key Tables

| Table | Role | Dataset | Status |
|-------|------|---------|--------|
| `Muawin_Akhuwat_db.teachers` | **Primary teacher data** — name, CNIC, school, qualifications, designation, experience | Schoolpilot (BigQuery) | **CANONICAL** |
| `Muawin_Akhuwat_db.users` | Platform account (auth) — minimal: id, org, role, mobile, is_active | Schoolpilot (BigQuery) | Auth/account only |
| `Muawin_Akhuwat_db.schools` | School identity — name, EMIS code, phase, geographic links | Schoolpilot (BigQuery) | For school context |
| `Muawin_Akhuwat_db.roles` | RBAC role definitions — name, level, permissions | Schoolpilot (BigQuery) | For role lookups |
| `Muawin_Akhuwat_db.organizations` | Root tenant — org name, display_name | Schoolpilot (BigQuery) | For org context |
| `Muawin_Akhuwat_db.districts` | Geographic: district within org | Schoolpilot (BigQuery) | Hierarchy |
| `Muawin_Akhuwat_db.tehsils` | Geographic: sub-district | Schoolpilot (BigQuery) | Hierarchy |
| `Muawin_Akhuwat_db.clusters` | Geographic: group of schools | Schoolpilot (BigQuery) | Hierarchy |
| `Zavia_db.users` | Zavia AI platform user — rich profile (name, phone, grades, subjects, region) | Zavia (BigQuery) | For AI tool usage verification |

**CRITICAL:** The Schoolpilot `users` table is a minimal auth table (no name, no email). The `teachers` table has the real teacher data. For teacher queries, always start from `teachers`.

**Join to Zavia:** `teachers.zavia_user_id = Zavia_db.users.id` (direct FK). Fallback: `teachers.mobile_number = Zavia_db.users.phone_number`.

## Geographic Hierarchy

```
organizations → districts → tehsils → clusters → schools → teachers
```

- `organizations.id` → `districts.organization_id`
- `districts.id` → `tehsils.district_id`
- `clusters.organization_id` → org-level grouping
- `schools.tehsil_id` → `tehsils.id`, `schools.cluster_id` → `clusters.id`
- `teachers.school_id` → `schools.id`

## Key Columns — Muawin_Akhuwat_db.users

- `id` — primary key (VARCHAR UUID)
- `organization_id` — FK to `organizations.id` (region identifier)
- `role_id` — FK to `roles.id` (RBAC role)
- `mobile_number` — phone number (STRING)
- `is_active` — BOOLEAN, active filter (NOT a text `status` field)
- `phase` — deployment phase
- `created_at`, `updated_at` — timestamps

**NOTE:** No `name`, `email`, `phone_number`, `status` (text), or `testing_account` columns exist on this table.

## Key Columns — Muawin_Akhuwat_db.teachers

- `id` — primary key (VARCHAR UUID)
- `user_id` — FK to `users.id` (links to platform account)
- `school_id` — FK to `schools.id`
- `organization_id` — FK to `organizations.id`
- `emis` — school EMIS code (inherited from school, INTEGER)
- `teacher_name` — full name (STRING)
- `cnic` — national ID, unique (STRING)
- `qualification` — teacher qualification (STRING, singular — e.g., "B.Ed", "M.Ed")
- `designation` — job title (STRING — e.g., "Head Teacher", "Class Teacher", "SST")
- `gender` — STRING
- `mobile_number` — phone (STRING)
- `joining_date` — DATE type
- `status` — default `'ACTIVE'` (STRING)
- `experience_years` — numeric years of experience (INTEGER)
- `experience_range` — categorical range (STRING — e.g., "5-10 years")
- `subject_expertise` — subject specialization (STRING)
- `grades_handled` — grades taught (STRING)
- `specialization` — area of specialization (STRING)
- `certifications` — professional certifications (STRING)
- `registration_source` — how teacher was registered (STRING)
- `zavia_user_id` — FK to `Zavia_db.users.id` (**primary join key to Zavia**)

## Key Columns — Muawin_Akhuwat_db.schools

- `id` — primary key (VARCHAR UUID)
- `name` — school name (STRING)
- `emis` — government EMIS code (INTEGER)
- `cluster_id` — FK to `clusters.id`
- `coordinator_id` — FK to `users.id` (school coordinator)
- `phase` — deployment phase (STRING)
- `organization_id` — FK to `organizations.id`
- `tehsil_id` — FK to `tehsils.id`

## Required Filters

- `t.organization_id` — must match specified region (Moawin or Akhuwat org ID)
- `u.is_active = true` — active platform account (default)
- `t.status = 'ACTIVE'` — active teacher profile (default)
- When joining Zavia: `zu.is_test_user = false` — exclude Zavia test accounts

## Join Pattern

```sql
-- Teacher roster with school and geographic context
SELECT t.*, u.mobile_number, u.is_active,
       s.name AS school_name, s.emis AS school_emis,
       th.name AS tehsil_name, d.name AS district_name
FROM Muawin_Akhuwat_db.teachers t
JOIN Muawin_Akhuwat_db.users u ON t.user_id = u.id
JOIN Muawin_Akhuwat_db.schools s ON t.school_id = s.id
LEFT JOIN Muawin_Akhuwat_db.tehsils th ON s.tehsil_id = th.id
LEFT JOIN Muawin_Akhuwat_db.districts d ON th.district_id = d.id
WHERE t.organization_id = <moawin_or_akhuwat_org_id>
  AND u.is_active = true
  AND t.status = 'ACTIVE'
```

```sql
-- Teacher with Zavia AI platform link
SELECT t.*, zu.name AS zavia_name, zu.registration_completed, zu.is_test_user
FROM Muawin_Akhuwat_db.teachers t
LEFT JOIN Zavia_db.users zu ON t.zavia_user_id = zu.id
WHERE t.organization_id = <moawin_or_akhuwat_org_id>
  AND t.status = 'ACTIVE'
  AND (zu.is_test_user = false OR zu.is_test_user IS NULL)
```

## Aggregation Patterns

| User asks about | GROUP BY | Aggregate |
|-----------------|----------|-----------|
| Total teachers (active) | — | `COUNT(DISTINCT t.id)` |
| Teachers per school | `s.name`, `s.emis` | `COUNT(DISTINCT t.id)` |
| By designation | `t.designation` | `COUNT(DISTINCT t.id)` |
| By qualification | `t.qualification` | `COUNT(DISTINCT t.id)` |
| By gender | `t.gender` | `COUNT(DISTINCT t.id)` |
| By experience range | `t.experience_range` | `COUNT(DISTINCT t.id)` |
| By experience years | `CASE WHEN t.experience_years < 3 THEN '0-2y' WHEN t.experience_years < 10 THEN '3-9y' ELSE '10+y' END` | `COUNT(DISTINCT t.id)` |
| Teachers with Zavia link | — | `COUNT(DISTINCT t.id) WHERE t.zavia_user_id IS NOT NULL` |
| By tehsil | `th.name` | `COUNT(DISTINCT t.id)` |
| By district | `d.name` | `COUNT(DISTINCT t.id)` |
| Teachers with certifications | — | `COUNT(DISTINCT t.id) WHERE t.certifications IS NOT NULL` |

## Data Conventions

- Timezone: `Asia/Karachi` for all date conversions
- `organization_id` is the canonical region split variable
- EMIS codes on `schools` table are INTEGER type
- `teachers.cnic` is unique — use for deduplication if needed
- `teachers` is the primary dimension table for teacher queries, not `users`
- `users` table only needed for `is_active` filter and `mobile_number`
- `joining_date` is DATE type — no casting needed

## Important Notes

- Never use `Zavia_db.users` as canonical source for teacher counts — always use Schoolpilot `teachers`
- The `users` table is auth-only — it has NO name, email, or phone_number. Use `teachers.teacher_name` and `teachers.mobile_number`
- `teachers.zavia_user_id` is the primary join key to Zavia (not phone_number)
- One teacher has one school assignment (`school_id` FK)
- `roles` table provides role names — join via `users.role_id = roles.id`

## Data Status
- Status: SCHEMA VERIFIED (from actual Schoolpilot schema documentation)
- organization_id mapping: TBD (verify exact values with data team)
- Last verified: April 2026
- Related global rules: Test user exclusion (data-governance.md), Database priority (data-governance.md)
