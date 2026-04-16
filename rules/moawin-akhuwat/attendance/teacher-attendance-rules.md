# Teacher Attendance Query Rules — Moawin / Akhuwat

## When These Rules Apply

User asks about:
- Daily teacher attendance in Moawin or Akhuwat
- Teacher presence/absence rates by school, tehsil, or date
- Teacher leave requests and approval status
- Late arrivals or check-in times

## Mandatory Clarifications

### Query Type
Ask: "Attendance counts/rates, or leave request tracking?"

### Time Period
Ask: "Which date range?"
- `date` (DATE) on `teacher_attendances`

### Region
Ask: "Moawin or Akhuwat?"

### Aggregation
Ask: "By school, by tehsil, by teacher, or overall?"

## Key Tables

| Table | Role | Dataset | Status |
|-------|------|---------|--------|
| `Muawin_Akhuwat_db.teacher_attendances` | Daily per-teacher attendance | Schoolpilot (BigQuery) | **CANONICAL** |
| `Muawin_Akhuwat_db.teacher_leave_requests` | Leave applications with approval workflow | Schoolpilot | Supporting |
| `Muawin_Akhuwat_db.teachers` | Teacher identity | Schoolpilot | For join |
| `Muawin_Akhuwat_db.schools` | School context | Schoolpilot | For school rollups |

## Key Columns — teacher_attendances

- `teacher_id` — FK to `teachers.id`
- `school_id` — FK to `schools.id`
- `date` — DATE, one record per teacher per date
- `status` — `PRESENT`, `ABSENT`, `LATE`, `ON_LEAVE`
- `check_in_time` — TIMESTAMP (for late analysis)
- `submitted_by_id` — FK to `users.id` (who marked)
- `is_locked` — BOOLEAN, whether record is finalized
- `locked_by` — FK to `users.id`

## Key Columns — teacher_leave_requests

- `teacher_id` — FK to `teachers.id`
- `school_id` — FK to `schools.id`
- `created_by_id`, `approver_id` — FK to `users.id`
- `type` — `CASUAL`, `SICK`, etc.
- `start_date`, `end_date` — DATE range
- `status` — `PENDING`, `APPROVED`, `REJECTED`
- `synced_to_attendance` — BOOLEAN, whether reflected in attendance

## Join Pattern

```sql
SELECT ta.date, ta.status, ta.check_in_time,
       t.teacher_name, t.designation, t.gender,
       s.name AS school_name, s.emis,
       th.name AS tehsil_name
FROM Muawin_Akhuwat_db.teacher_attendances ta
JOIN Muawin_Akhuwat_db.teachers t ON ta.teacher_id = t.id
JOIN Muawin_Akhuwat_db.schools s ON ta.school_id = s.id
LEFT JOIN Muawin_Akhuwat_db.tehsils th ON s.tehsil_id = th.id
WHERE t.organization_id IN (<moawin_org_id>, <akhuwat_org_id>)
  AND t.status = 'ACTIVE'
  AND ta.date BETWEEN DATE('...') AND DATE('...')
```

## Aggregation Patterns

| User asks about | GROUP BY | Aggregate |
|-----------------|----------|-----------|
| Daily attendance rate | `ta.date` | `COUNTIF(ta.status = 'PRESENT') / COUNT(*)` |
| By school | `s.name`, `s.emis` | attendance rate |
| By tehsil | `th.name` | attendance rate |
| Teacher-level | `t.id`, `t.teacher_name` | `COUNTIF(PRESENT)`, `COUNTIF(ABSENT)` |
| Late rate | `ta.date` | `COUNTIF(ta.status = 'LATE') / COUNT(*)` |
| Leave type distribution | `tlr.type` | `COUNT(DISTINCT tlr.id)` |
| Leave approval rate | `tlr.status` | `COUNT(*)` |

## Data Conventions

- Timezone: `Asia/Karachi`
- One record per teacher per date
- `is_locked = true` means finalized — prefer locked records for reporting

## Data Status
- Status: SCHEMA VERIFIED
- Last verified: April 2026
