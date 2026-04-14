# User Query Rules — Moawin / Akhuwat

## When These Rules Apply

User asks about:
- Moawin or Akhuwat teacher profiles, registration, or institutional attributes
- User counts, cohort size, school assignments
- Teacher roster for either region
- Teacher-level demographic or qualification data
- Teacher experience, certifications, or designations

## Mandatory Clarifications

### Region
Always ask: "Moawin or Akhuwat?"
- `organization_id` in `neondb.public.users` determines region (exact values TBD — verify with data team)
- Never assume region

### Filter Scope
Ask if relevant: "All users, active only, or specific role/designation?"
- Default: active users only (`status = 'active'`)
- Include inactive/pending only if explicitly requested

## Key Tables

| Table | Role | Database | Status |
|-------|------|----------|--------|
| `neondb.public.users` | Base user identity and registration | Schoolpilot (PostgreSQL) | **CANONICAL** |
| `neondb.public.teachers` | Teacher institutional attributes (EMIS, school, qualifications, designation, gender, experience, certifications) | Schoolpilot (PostgreSQL) | **REQUIRED ENRICHMENT** |
| `zavia1.public.users` | Secondary user reference (for AI tool usage verification only) | Zavia (PostgreSQL) | Verification only |

**CRITICAL:** `neondb.public.users` alone is insufficient for full teacher profile. Always LEFT JOIN with `neondb.public.teachers` on `teachers.user_id = users.id` to retrieve institutional attributes.

## Key Columns — neondb.public.users

- `id` — primary key (STRING or INT)
- `name`, `email`, `phone_number` — identity
- `organization_id` — region identifier (Moawin vs Akhuwat — exact values TBD)
- `status` — user status: `active`, `pending`, `inactive`, etc.
- `testing_account` — BOOLEAN, true = test/internal user, false = production user
- `created_at`, `updated_at` — temporal
- Other registration/administrative fields

## Key Columns — neondb.public.teachers

- `user_id` — FK to `neondb.public.users.id` (primary join key)
- `emis_code` — school EMIS identifier (INT or STRING — verify type)
- `school_assignment` — assigned school name or ID
- `qualifications` — teacher qualifications (STRING or array — verify structure)
- `designation` — job title/designation (e.g., "Head Teacher", "Class Teacher")
- `gender` — teacher gender
- `experience` — years of teaching experience (INT or STRING)
- `certifications` — relevant professional certifications (STRING or array — verify structure)
- `is_active` — active status (BOOLEAN or STRING)
- `created_at`, `updated_at` — temporal

## Required Filters

- `neondb.public.users.organization_id` — must match specified region (verify exact values for Moawin and Akhuwat with data team)
- `neondb.public.users.status = 'active'` — active users only (default)
- `neondb.public.users.testing_account = false` — exclude test/internal accounts (per global test user exclusion rule)
- `neondb.public.teachers.is_active = 'true'` OR similar — active teacher profiles only

## Join Pattern

```sql
SELECT u.*, t.*
FROM neondb.public.users u
LEFT JOIN neondb.public.teachers t ON t.user_id = u.id
WHERE u.organization_id = <moawin_or_akhuwat_org_id>
  AND u.status = 'active'
  AND u.testing_account = false
  AND t.is_active = 'true'
```

**Important:** Use `LEFT JOIN` to capture users without matching teacher profiles (e.g., admin users). Use `INNER JOIN` only if you need teacher-profile-only counts.

## Aggregation Patterns

| User asks about | GROUP BY | Aggregate |
|-----------------|----------|-----------|
| Total teachers (active, non-test) | — | `COUNT(DISTINCT u.id)` |
| Teachers per school | `t.school_assignment`, `t.emis_code` | `COUNT(DISTINCT u.id)` |
| By designation | `t.designation` | `COUNT(DISTINCT u.id)` |
| By qualification | `t.qualifications` | `COUNT(DISTINCT u.id)` |
| By gender | `t.gender` | `COUNT(DISTINCT u.id)` |
| By experience range | `CASE WHEN t.experience < 3 THEN '0-3y' WHEN t.experience < 10 THEN '3-10y' ...` | `COUNT(DISTINCT u.id)` |
| By experience quartile | QUARTILE_CONT | `COUNT(DISTINCT u.id)` |
| Teachers with certifications | — | `COUNT(DISTINCT u.id) WHERE t.certifications IS NOT NULL` |

## Data Conventions

- Timezone: `Asia/Karachi` for all date conversions
- `organization_id` is the canonical region split variable — verify exact values with data team before hardcoding
- EMIS codes identify schools (may be INT or STRING — verify type and cast as needed)
- Always verify field types for `qualifications`, `experience`, and `certifications` (single-valued STRING vs array/JSON)
- Distinct() on `user_id` prevents double-counting from teacher JOIN (teacher may have multiple rows if design allows)

## Important Notes

- Never use `zavia1.public.users` as canonical source for teacher counts — always use Schoolpilot
- The `teachers` table enrichment is **mandatory** — `users` table alone lacks institutional context
- Test user exclusion via `testing_account = false` is mandatory (global rule)
- If a teacher has multiple school assignments, clarify with data team whether one row per school or aggregated design
- Verify that `designation` and `qualifications` are single-valued (STRING) vs arrays/JSON before aggregating

## Data Status
- Status: COMMENT + TRANSCRIPT MATCH (per Moawin/Akhuwat reconciliation notes)
- organization_id mapping: TBD (verify exact values with data team)
- Last verified: April 2026
- Related global rules: Test user exclusion (data-governance.md), Database priority (data-governance.md)
