# MySchool Query Rules

## When These Rules Apply

User asks about:
- MySchool platform data (school management system)
- School profiles, staff, students, attendance, timetables, results
- Infrastructure assessments, assets, buildings, utilities
- Academic years, terms, grades, subjects, grading thresholds
- Exam results, academic performance, pass/fail rates
- Maintenance, bills, financial details
- User interaction events or notifications

## Dataset

**`MySchool_db`** in BigQuery (project: `niete-bq-prod`)
- Source: Django PostgreSQL app (`my-school-db`)
- 59 migrated tables, integer PKs (Django auto-increment)
- All timestamps are `timestamptz` → serialized to ISO strings in BQ
- JSONB columns serialized to STRING — use `JSON_VALUE()` in BQ

## Mandatory Clarifications

### Query Domain
Ask: "Which area? Schools, staff, students, attendance, results, infrastructure, or analytics?"

### Time Period
Ask if relevant: "Which time period or academic year?"
- `academic_years` table defines years; `terms` defines terms within years

## Key Tables by Domain

### Core School

| Table | Role | Rows | Key Columns |
|-------|------|------|-------------|
| `MySchool_db.school_school` | Core school entity | 1 | `id`, `school_name`, `emis_code`, `school_type`, `school_level`, `gender`, `district`, `tehsil`, `total_students`, `boys_enrollment`, `girls_enrollment`, `total_teaching_staff`, `total_non_teaching_staff`, `is_active` |
| `MySchool_db.school_schoolclass` | Class sections (Grade + Section) | 11 | `id`, `emis_code`, `grade`, `section`, `shift` |
| `MySchool_db.school_schoolremark` | School remarks/observations | 1 | `id`, `school_id`, `remark_title`, `remark_description`, `priority`, `immediate_action_required`, `images` (JSON) |

### Staff (3,613 rows)

| Table | Role | Rows | Key Columns |
|-------|------|------|-------------|
| `MySchool_db.school_staff` | All staff (teaching + non-teaching) | 3,613 | `id`, `name`, `subject`, `email`, `phone`, `status`, `joining_date`, `qualification`, `experience`, `category`, `designation`, `gender`, `grade`, `cnic`, `is_active`, `emis_code` |
| `MySchool_db.school_staffdetail` | Aggregate staffing stats | 0 | `school_id`, `sanctioned_teaching_posts`, `filled_teaching_posts`, `vacant_teaching_posts`, etc. |

**Staff key columns:**
- `category` — teaching vs non-teaching
- `designation` — job title (e.g., SST, PST, Head Teacher)
- `status` — active/inactive
- `is_temporary_duty_in/out` — transfer status
- `is_deputation` — deputation flag

### Students (30 rows — early stage)

| Table | Role | Rows | Key Columns |
|-------|------|------|-------------|
| `MySchool_db.school_student` | Student master records | 30 | `id`, `name`, `emis_code`, `grade`, `section`, `roll_number`, `admission_number`, `admission_date`, `date_of_birth`, `gender`, `disability_status`, `is_active`, `parent_name`, `father_name`, `school_id` |
| `MySchool_db.school_studentenrollment` | Session enrollment per student | 30 | `student_id`, `academic_session`, `grade`, `section`, `outcome`, `exit_date` |
| `MySchool_db.enrollments` | Academic year enrollment with result | 0 | `student_id`, `grade_id`, `academic_year_id`, `roll_number`, `status`, `final_percentage`, `final_grade_letter`, `passed` |

### Academic Structure

| Table | Role | Rows |
|-------|------|------|
| `MySchool_db.academic_years` | Year definitions | 1 |
| `MySchool_db.terms` | Terms within year | 3 |
| `MySchool_db.grades` | Grade/class levels | 13 |
| `MySchool_db.subjects` | Subject catalogue | 14 |
| `MySchool_db.grade_thresholds` | Grading scale (% → letter) | 7 |
| `MySchool_db.pass_config` | Pass/fail configuration | 1 |
| `MySchool_db.grade_subjects` | Subject-grade mapping with marks | 0 |

### Results & Assessments (mostly 0 rows — early stage)

| Table | Role | Rows | Key Columns |
|-------|------|------|-------------|
| `MySchool_db.term_results` | Per-student per-subject term marks | 0 | `enrollment_id`, `subject_id`, `term_id`, `marks_obtained`, `is_absent` |
| `MySchool_db.student_results` | Student results with grade | 0 | `student_id`, `subject_id`, `term_id`, `obtained_marks`, `total_marks`, `grade` |
| `MySchool_db.school_examresult` | Exam results with workflow | 0 | `student_id`, `exam_type`, `term`, `class_grade`, `subject_name`, `total_marks`, `obtained_marks`, `percentage`, `grade`, `result_status`, `workflow_status` |
| `MySchool_db.school_academicperformance` | School-level performance stats | 0 | `school_id`, `pass_percentage_current`, `dropout_rate`, `student_teacher_ratio` |
| `MySchool_db.result_audit_logs` | Mark change audit trail | 0 | `term_result_id`, `old_marks`, `new_marks`, `changed_by_id` |

### Attendance

| Table | Role | Rows | Key Columns |
|-------|------|------|-------------|
| `MySchool_db.attendance_attendancerecord` | Daily student attendance | 0 | `student_id`, `date`, `status`, `leave_type`, `academic_session` |
| `MySchool_db.attendance_staffattendancerecord` | Daily staff attendance | 17 | `staff_id`, `date`, `status`, `leave_type` |

### Infrastructure (detailed facility assessments)

| Table | Role | Rows |
|-------|------|------|
| `MySchool_db.school_infrastructureprofile` | Full infrastructure assessment (12+ JSONB blobs) | 21 |
| `MySchool_db.school_infrastructureimage` | Photos per infrastructure section | 24 |
| `MySchool_db.school_infrastructureitem` | Individual infrastructure items | 1 |
| `MySchool_db.school_assetitem` | Asset inventory | 0 |
| `MySchool_db.school_furnitureitem` | Furniture inventory | 0 |
| `MySchool_db.school_building` | Buildings on campus | 0 |
| `MySchool_db.school_room` | Rooms within buildings | 0 |
| `MySchool_db.school_landareadetail` | Land and boundary wall | 0 |
| `MySchool_db.school_utilitydetail` | Electricity, water, sewerage | 0 |
| `MySchool_db.school_connectivitydetail` | Internet and digital resources | 0 |
| `MySchool_db.school_safetycompliance` | Safety compliance checks | 0 |
| `MySchool_db.school_accessibilityfeature` | Accessibility features | 0 |
| `MySchool_db.school_environmentalfeature` | Environmental features | 0 |
| `MySchool_db.school_disasterpreparedness` | Disaster preparedness | 0 |

### Timetable

| Table | Role | Rows |
|-------|------|------|
| `MySchool_db.school_timetable` | Weekly timetable entries | 78 |
| `MySchool_db.class_assignments` | Teacher-class assignments | 0 |

### Finance

| Table | Role | Rows |
|-------|------|------|
| `MySchool_db.school_financialdetail` | School financial summary | 0 |
| `MySchool_db.school_maintenance` | Maintenance transactions | 3 |
| `MySchool_db.school_bill` | Utility bills | 1 |
| `MySchool_db.school_inspectionhistory` | Inspection records | 0 |

### Users & Analytics

| Table | Role | Rows |
|-------|------|------|
| `MySchool_db.auth_user` | Django user accounts (password excluded) | 3,898 |
| `MySchool_db.notes_userprofile` | Extended user profile with school stats | 3,889 |
| `MySchool_db.events_interactionevent` | User interaction events | 9,656 |
| `MySchool_db.notes_notification` | In-app notifications | 1,708 |
| `MySchool_db.notes_conversation` | AI assistant conversations | 34 |
| `MySchool_db.notes_message` | AI assistant messages | 87 |

## Join Patterns

```sql
-- Staff with school context
SELECT s.*, sch.school_name, sch.emis_code, sch.district, sch.tehsil
FROM MySchool_db.school_staff s
LEFT JOIN MySchool_db.school_school sch ON s.emis_code = sch.emis_code
WHERE s.is_active = true

-- Students with enrollment
SELECT st.*, se.academic_session, se.grade AS enrolled_grade, se.outcome
FROM MySchool_db.school_student st
LEFT JOIN MySchool_db.school_studentenrollment se ON st.id = se.student_id
WHERE st.is_active = true

-- Staff attendance with staff details
SELECT sar.date, sar.status, sar.leave_type,
       s.name, s.designation, s.category
FROM MySchool_db.attendance_staffattendancerecord sar
JOIN MySchool_db.school_staff s ON sar.staff_id = s.id

-- User profile with auth user
SELECT up.*, au.username, au.email, au.is_active, au.last_login
FROM MySchool_db.notes_userprofile up
JOIN MySchool_db.auth_user au ON up.user_id = au.id
```

## Filtering Rules

- Staff active filter: `school_staff.is_active = true`
- Student active filter: `school_student.is_active = true`
- Soft deletes: `enrollments.deleted_at IS NULL`, `class_assignments.deleted_at IS NULL`, `grade_subjects.deleted_at IS NULL`
- Academic year: join to `academic_years` where `is_current = true` (default)

## Aggregation Patterns

| User asks about | GROUP BY | Aggregate |
|-----------------|----------|-----------|
| Total staff | — | `COUNT(*) WHERE is_active = true` |
| Staff by category | `category` | `COUNT(*)` (teaching vs non-teaching) |
| Staff by designation | `designation` | `COUNT(*)` |
| Staff by gender | `gender` | `COUNT(*)` |
| Staff by qualification | `qualification` | `COUNT(*)` |
| Total students | — | `COUNT(*) WHERE is_active = true` |
| Students by grade | `grade` | `COUNT(*)` |
| Students by gender | `gender` | `COUNT(*)` |
| Staff attendance rate | `date` | `COUNTIF(status='present') / COUNT(*)` |
| Interaction events | `event_type` or `event_name` | `COUNT(*)` |
| Active users | — | `COUNT(DISTINCT user_id)` from events |

## Data Conventions

- Timezone: `Asia/Karachi`
- All PKs are INTEGER (Django auto-increment), not UUID
- JSONB columns → STRING in BQ, use `JSON_VALUE()` for access
- `school_opening_time`/`school_closing_time` → STRING `"HH:MM:SS"`
- Base64 image columns are large text fields — avoid `SELECT *`
- Many tables have 0 rows (early stage) — flag this to users
- `emis_code` is the school identifier, used across staff/student/class tables
- Django table naming: `app_modelname` (e.g., `school_staff`, `attendance_attendancerecord`)

## Data Maturity

| Domain | Rows | Status |
|--------|------|--------|
| Staff | 3,613 | **Production-ready** |
| User profiles | 3,889 | **Production-ready** |
| Interaction events | 9,656 | **Production-ready** |
| Infrastructure profiles | 21 | Active but small |
| Timetable | 78 | Active |
| Students | 30 | **Early stage** |
| Attendance | 17 (staff only) | **Early stage** |
| Results/Assessments | 0 | **Not yet populated** |
| Finance | 4 | **Early stage** |

Flag data maturity to users before running queries on early-stage tables.

## Important Notes

- `auth_user.password` is **excluded** from migration (security)
- `notes_userprofile` is the richest user table — has school stats, head teacher info, report card config
- Infrastructure is highly detailed (12+ JSONB blobs) — query specific sections, not `SELECT *`
- `events_interactionevent` is the primary analytics table (9,656 rows)
- Many tables have `created_at` + `updated_at` as watermarks for incremental sync

## Data Status
- Status: SCHEMA VERIFIED (from MySchool schema documentation)
- Dataset: `MySchool_db` in BigQuery
- Last verified: April 2026
