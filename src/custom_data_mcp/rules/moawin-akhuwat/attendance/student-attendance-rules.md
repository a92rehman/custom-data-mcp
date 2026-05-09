# Student Attendance Query Rules — Moawin / Akhuwat

## When These Rules Apply

User asks about:
- Student attendance in Moawin or Akhuwat
- School-level aggregate attendance (present/absent counts)
- Individual student attendance via AI-powered voice marking (Zavia)
- Enrollment counts

## Mandatory Clarifications

### Data Source
Ask: "School-level aggregate (Schoolpilot) or individual student-level (Zavia AI attendance)?"
- **Schoolpilot:** daily aggregate per school — total_students, total_present, total_absent
- **Zavia:** per-student records from AI audio attendance marking

### Time Period
Ask: "Which date range?"

### Region
Ask: "Moawin or Akhuwat?"

## Two Attendance Systems

### 1. School-Level Aggregate — Schoolpilot (`Muawin_Akhuwat_db`)

| Table | Role | Status |
|-------|------|--------|
| `Muawin_Akhuwat_db.attendance` | Daily aggregate per school | **CANONICAL for school-level** |
| `Muawin_Akhuwat_db.physical_enrollment_logs` | Manual daily enrollment count | Supporting |

**`attendance` columns:**
- `school_id`, `organization_id`, `date`
- `total_students`, `total_present`, `total_absent` — aggregate counts
- `nadra_pending_in_sis`, `pending_in_sis` — PEFSIS sync status
- `detected_student_count` — AI photo count (INTEGER)
- `pending_review` — needs review flag
- `photo_urls` (ARRAY → STRING), `photo_timestamps` (JSONB → STRING)

**`physical_enrollment_logs` columns:**
- `school_id`, `date`, `enrollment_count`, `region`, `created_by_id`

### 2. Individual Student-Level — Zavia (`Zavia_db`)

| Table | Role | Status |
|-------|------|--------|
| `Zavia_db.attendance_sessions` | Per-class marking session | **CANONICAL for individual** |
| `Zavia_db.attendance_records` | Per-student record within session | Detail |
| `Zavia_db.student_lists` | Class rosters | Supporting |
| `Zavia_db.students` | Individual student profiles | Supporting |

**`attendance_sessions` columns:**
- `id`, `user_id → users.id`, `list_id → student_lists.id`
- `session_date`, `session_type`, `total_students`, `present_count`, `absent_count`
- `audio_url`, `transcript`, `transcript_confidence` — AI audio marking
- `excel_url`, `was_manually_edited`, `marking_method`
- `created_at`

**`attendance_records` columns:**
- `id`, `session_id → attendance_sessions.id`, `student_id → students.id`
- `student_name`, `status`, `notes`, `confidence`, `detected_response`
- `was_manually_changed` — whether AI result was manually overridden
- `created_at`

**`student_lists` columns:**
- `id`, `user_id → users.id`, `class_name`, `section`, `academic_year`
- `student_count`, `is_active`, `attendance_frequency`

**`students` columns:**
- `id`, `list_id → student_lists.id`, `student_name`, `student_name_urdu`
- `father_name`, `father_name_urdu`, `roll_number`, `is_active`

## Join Patterns

```sql
-- School-level aggregate (Schoolpilot)
SELECT att.date, att.total_students, att.total_present, att.total_absent,
       s.name AS school_name, s.emis
FROM Muawin_Akhuwat_db.attendance att
JOIN Muawin_Akhuwat_db.schools s ON att.school_id = s.id
WHERE att.organization_id IN (<moawin_org_id>, <akhuwat_org_id>)

-- Individual student (Zavia)
SELECT ars.session_date, ar.student_name, ar.status, ar.confidence,
       sl.class_name, sl.section, zu.name AS teacher_name
FROM Zavia_db.attendance_records ar
JOIN Zavia_db.attendance_sessions ars ON ar.session_id = ars.id
JOIN Zavia_db.student_lists sl ON ars.list_id = sl.id
JOIN Zavia_db.users zu ON ars.user_id = zu.id
WHERE zu.is_test_user = false
```

## Aggregation Patterns

| User asks about | Source | Aggregate |
|-----------------|--------|-----------|
| School daily attendance rate | Schoolpilot | `total_present / total_students` |
| By school | Schoolpilot | GROUP BY `school_id` |
| Individual student rate | Zavia | `COUNTIF(ar.status = 'present') / COUNT(*)` |
| AI confidence distribution | Zavia | `AVG(ar.confidence)`, distribution buckets |
| Manual override rate | Zavia | `COUNTIF(ar.was_manually_changed) / COUNT(*)` |

## Important Notes

- Two separate systems — do NOT combine counts from Schoolpilot and Zavia
- Schoolpilot attendance is aggregate (no per-student detail)
- Zavia attendance is per-student with AI audio marking confidence
- `marking_method` on `attendance_sessions` indicates how attendance was taken

## Data Status
- Status: SCHEMA VERIFIED
- Last verified: April 2026
