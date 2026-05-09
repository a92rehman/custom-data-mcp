# School & Geographic Query Rules — Moawin / Akhuwat

## When These Rules Apply

User asks about:
- School lists, counts, or profiles in Moawin or Akhuwat
- Geographic hierarchy (districts, tehsils, clusters)
- School infrastructure assessments
- Coordinator visit reports or improvement plans
- School EMIS codes

## Mandatory Clarifications

### Region
Ask: "Moawin or Akhuwat?"

### Query Type
Ask: "School list/count, infrastructure profile, visit reports, or improvement plans?"

## Key Tables

| Table | Role | Dataset | Status |
|-------|------|---------|--------|
| `Muawin_Akhuwat_db.schools` | Core school entity | Schoolpilot | **CANONICAL** |
| `Muawin_Akhuwat_db.organizations` | Root tenant (Moawin, Akhuwat) | Schoolpilot | Hierarchy root |
| `Muawin_Akhuwat_db.districts` | District within org | Schoolpilot | Hierarchy |
| `Muawin_Akhuwat_db.tehsils` | Sub-district | Schoolpilot | Hierarchy |
| `Muawin_Akhuwat_db.clusters` | School grouping | Schoolpilot | Hierarchy |
| `Muawin_Akhuwat_db.school_profiles` | Detailed infrastructure assessment | Schoolpilot | One per school |
| `Muawin_Akhuwat_db.school_visit_reports` | Coordinator visit reports | Schoolpilot | Per visit |
| `Muawin_Akhuwat_db.school_improvement_plans` | Improvement plan submissions | Schoolpilot | Per plan |
| `Muawin_Akhuwat_db.school_profile_audits` | Field-level change log for profiles | Schoolpilot | Audit trail |

## Geographic Hierarchy

```
organizations (Moawin / Akhuwat)
  └── districts
        └── tehsils
              └── clusters (optional grouping)
                    └── schools
                          └── teachers, students, attendance
```

### Key Columns

**schools:** `id`, `name`, `emis` (INTEGER), `cluster_id`, `coordinator_id → users.id`, `phase`, `organization_id`, `tehsil_id`

**organizations:** `id`, `name`, `display_name`, `onboarding_completed`, `admissions_locked`

**districts:** `id`, `name`, `organization_id`

**tehsils:** `id`, `name`, `district_id → districts.id`, `organization_id`

**clusters:** `id`, `name`, `organization_id`

**school_profiles** (one per school):
- `school_id`, `level`, `gender`, `school_status`, `head_teacher_name`
- `overall_school_condition`, `immediate_action_required`, `date_of_handover`, `location_address`
- JSONB blobs (→ STRING in BQ): `boundary_wall`, `playground`, `utilities`, `infrastructure`, `assets`, `furniture`, `classrooms`, `toilets`, `disaster_preparedness`
- ~30 boolean safety flags (building cracks, roof leakage, electrical hazard, etc.)
- Array fields: `safety_image_urls`, `general_remarks_image_urls`

**school_visit_reports:** `school_id`, `submitted_by → users.id`, `report_data` (JSONB → STRING), `created_at`

**school_improvement_plans:** `school_id`, `submitted_by → users.id`, `plan_data` (JSONB → STRING), `created_at`

## Join Pattern

```sql
SELECT s.name, s.emis, s.phase,
       o.name AS org_name,
       d.name AS district_name,
       th.name AS tehsil_name,
       cl.name AS cluster_name,
       sp.level, sp.gender, sp.school_status, sp.overall_school_condition
FROM Muawin_Akhuwat_db.schools s
JOIN Muawin_Akhuwat_db.organizations o ON s.organization_id = o.id
LEFT JOIN Muawin_Akhuwat_db.tehsils th ON s.tehsil_id = th.id
LEFT JOIN Muawin_Akhuwat_db.districts d ON th.district_id = d.id
LEFT JOIN Muawin_Akhuwat_db.clusters cl ON s.cluster_id = cl.id
LEFT JOIN Muawin_Akhuwat_db.school_profiles sp ON sp.school_id = s.id
WHERE s.organization_id IN (<moawin_org_id>, <akhuwat_org_id>)
```

## Aggregation Patterns

| User asks about | GROUP BY | Aggregate |
|-----------------|----------|-----------|
| Total schools | — | `COUNT(DISTINCT s.id)` |
| By district | `d.name` | `COUNT(DISTINCT s.id)` |
| By tehsil | `th.name` | `COUNT(DISTINCT s.id)` |
| By cluster | `cl.name` | `COUNT(DISTINCT s.id)` |
| By phase | `s.phase` | `COUNT(DISTINCT s.id)` |
| By condition | `sp.overall_school_condition` | `COUNT(DISTINCT s.id)` |
| Immediate action needed | — | `COUNTIF(sp.immediate_action_required)` |
| Visit reports count | `s.id` | `COUNT(DISTINCT svr.id)` |
| Schools with profiles | — | `COUNTIF(sp.school_id IS NOT NULL)` |

## Data Conventions

- `emis` is INTEGER (government school code)
- `school_profiles` JSONB blobs: use `JSON_VALUE()` for specific fields
- Visit reports and improvement plans store full content in JSONB `report_data`/`plan_data`
- `coordinator_id` on schools links to `users.id` (the school coordinator)

## Important Notes

- `school_profiles` has ~30 boolean safety flags — query specific ones by name
- JSONB infrastructure blobs (`boundary_wall`, `utilities`, etc.) need `JSON_VALUE()` extraction
- `school_profile_audits` tracks field-level changes — use for change history, not current state
- One school_profile per school (1:1 relationship)

## Data Status
- Status: SCHEMA VERIFIED
- Last verified: April 2026
