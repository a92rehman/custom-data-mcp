---
paths:
  - "src/**/*.py"
---

# Teacher Data Definitions

## teacher_profiles (Silver — base table)

One row per teacher profile. A teacher can have multiple profiles if assigned to multiple schools.

**Source tables:** `tbproddb.users_user` → `tbproddb.users_teacherprofile` → `tbproddb.schools_school`

**Query:**
```sql
SELECT
    u.id AS user_id,
    u.username AS contact,
    u.name AS user_name,
    u.is_staff,
    u.is_active,
    DATETIME(TIMESTAMP(u.date_joined), "Asia/Karachi") AS joining_date,
    u.activated_on,
    u.organization_id,
    u.is_testing_account,
    tp.id AS profile_id,
    tp.role_id,
    tp.school_id,
    s.name,
    CAST(s.emis AS INT64) AS emis,
    tp.levels
FROM `niete-bq-prod.tbproddb.users_user` u
INNER JOIN `niete-bq-prod.tbproddb.users_teacherprofile` tp ON u.id = tp.user_id
INNER JOIN `niete-bq-prod.tbproddb.schools_school` s ON tp.school_id = s.id
WHERE
    s.emis IN (SELECT EMIS FROM `niete-bq-prod.tbproddb.FDE_Schools`)
    AND tp.is_active = 'true'
    AND u.is_active = 'true'
    AND u.deleted_at IS NULL
    AND tp.deleted_at IS NULL
    AND u.organization_id = 1
    AND u.is_testing_account = "false"
    AND 'PRIMARY' IN UNNEST(JSON_VALUE_ARRAY(tp.levels))
```

**Business rules:**
- Only FDE schools (via EMIS filter)
- Both user and profile must be active
- Soft-deleted records excluded
- organization_id = 1 = ICT/Islamabad region
- Testing accounts excluded
- This query filters to PRIMARY level — change the level filter for MIDDLE/SECONDARY

---

## user_school_profiles (Gold — deduplicated dimension)

One row per unique teacher. Multiple school assignments pivoted into school_1/2/3 columns.

**Source:** Built on top of `teacher_profiles`

**Query:**
```sql
WITH RankedProfiles AS (
  SELECT
    user_id, contact, user_name, is_staff, is_active,
    joining_date, activated_on, organization_id,
    profile_id, name, emis, levels,
    ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY profile_id) AS profile_rank
  FROM `niete-bq-prod.tbproddb.teacher_profiles`
),
UserAgg AS (
  SELECT
    user_id, contact, user_name, is_staff, is_active,
    joining_date, activated_on, organization_id,
    COUNT(DISTINCT profile_id) AS profiles_count,
    MAX(IF(profile_rank = 1, name, NULL)) AS school_1,
    MAX(IF(profile_rank = 2, name, NULL)) AS school_2,
    MAX(IF(profile_rank = 3, name, NULL)) AS school_3,
    MAX(IF(profile_rank = 1, emis, NULL)) AS emis_1,
    MAX(IF(profile_rank = 2, emis, NULL)) AS emis_2,
    MAX(IF(profile_rank = 3, emis, NULL)) AS emis_3,
    MAX(IF(profile_rank = 1, profile_id, NULL)) AS profile_id,
    MAX(IF(profile_rank = 1, levels, NULL)) AS levels
  FROM RankedProfiles
  GROUP BY user_id, contact, user_name, is_staff, is_active,
           joining_date, activated_on, organization_id
)
SELECT ua.*
FROM UserAgg AS ua
JOIN `niete-bq-prod.tbproddb.FDE_Schools` AS fs ON fs.EMIS = ua.emis_1
```

**Business rules:**
- One row per teacher (deduplicated by user_id)
- profile_rank 1 = primary school, 2/3 = additional
- levels taken from primary profile only
- Primary school must be FDE (join on emis_1)
- Inherits all filters from teacher_profiles
- Contains PRIMARY teachers only — for other levels, use teacher_profiles with different filter

**Output columns:**
- `user_id` — unique teacher ID
- `contact` — username / phone
- `user_name` — full name
- `profiles_count` — number of school assignments
- `school_1/2/3` — school names (primary, secondary, tertiary)
- `emis_1/2/3` — school EMIS codes
- `joining_date` — Asia/Karachi timezone
- `levels` — JSON array from primary profile
