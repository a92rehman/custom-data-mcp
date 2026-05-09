# Teacher Query Rules

## Mandatory Questions Before Any Teacher Query

### Teacher Level
Always ask: "Which teacher level? PRIMARY, MIDDLE, SECONDARY, or all?"
- `levels` is a JSON array in `users_teacherprofile` — teachers can have one or multiple levels
- Never assume PRIMARY — the user must specify
- Filter syntax: `'PRIMARY' IN UNNEST(JSON_VALUE_ARRAY(tp.levels))`

### Region
Always ask: "Which region? ICT/Islamabad or another?"
- `organization_id` maps to region (1 = ICT/Islamabad)
- Different regions have different org IDs and different school reference tables
- ICT/Islamabad uses `FDE_Schools` as the school reference table — other regions use different tables
- Never assume ICT/Islamabad

### When to Ask
- These two questions are mandatory for ANY query involving teachers, schools, or per-teacher metrics
- Ask at the start, before executing anything
- If the user already specified (e.g., "PRIMARY teachers in Islamabad"), don't re-ask

## Required Filters for Teacher Queries
- `tp.is_active = 'true'` AND `u.is_active = 'true'` — both user and profile must be active
- `u.deleted_at IS NULL` AND `tp.deleted_at IS NULL` — exclude soft-deleted records
- `u.is_testing_account = "false"` — exclude test accounts
- `organization_id` — must match the user's specified region 1 for ICT/Islamabad
- `FDE_Schools` EMIS filter — for ICT/Islamabad; other regions use their own school reference
- Level filter via `JSON_VALUE_ARRAY(tp.levels)` — must match user's specified level

## Key Tables
- `tbproddb.users_user` — base user table (id, username, name, is_active, date_joined, organization_id)
- `tbproddb.users_teacherprofile` — teacher profile (user_id, school_id, role_id, levels, is_active)
- `tbproddb.schools_school` — school details (id, name, emis)
- `tbproddb.FDE_Schools` — reference table for ICT/Islamabad schools (EMIS column)
- `tbproddb.teacher_profiles` — curated join of users + profiles + schools (already filtered for ICT PRIMARY)
- `tbproddb.user_school_profiles` — deduplicated one-row-per-teacher dimension (ICT PRIMARY only)

## Data Conventions
- A teacher can have multiple profiles (one per school assignment)
- `user_school_profiles` is deduplicated — one row per teacher with school_1/2/3 columns
- `user_school_profiles` only contains PRIMARY teachers in ICT — for other levels/regions, query from base tables
- Timezone: `Asia/Karachi` for all date conversions
- EMIS codes identify schools (integer, cast from string)
