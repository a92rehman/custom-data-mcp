# Teacher Training Query Rules — Moawin / Akhuwat

## When These Rules Apply

User asks about:
- Teacher training progress in Moawin or Akhuwat
- Training level/course/module completion
- Quiz scores and pass rates
- Video watch percentage
- Training content structure

## Mandatory Clarifications

### Query Type
Ask: "Training progress/completion, quiz performance, or content structure?"

### Level/Course
Ask if relevant: "Specific training level or course, or all?"

### Time Period
Ask: "Which time period?"
- `last_accessed_at` on progress, `completed_at` on quiz attempts

### Region
Ask: "Moawin or Akhuwat?"

## Key Tables

| Table | Role | Dataset | Status |
|-------|------|---------|--------|
| `Muawin_Akhuwat_db.teacher_training_progress` | Per teacher-module progress | Schoolpilot | **CANONICAL** |
| `Muawin_Akhuwat_db.teacher_quiz_attempts` | Individual quiz attempt records | Schoolpilot | Detail |
| `Muawin_Akhuwat_db.training_levels` | Top-level training tiers | Schoolpilot | Content structure |
| `Muawin_Akhuwat_db.training_courses` | Courses within a level | Schoolpilot | Content structure |
| `Muawin_Akhuwat_db.training_modules` | Modules within a course (video + quiz) | Schoolpilot | Content structure |
| `Muawin_Akhuwat_db.training_questions` | Quiz questions within a module | Schoolpilot | Content structure |

## Content Hierarchy

```
training_levels → training_courses → training_modules → training_questions
```

### training_levels
- `id`, `name`, `order` (INT — sort by this), `is_active`, `organization_id`, `created_at`

### training_courses
- `id`, `level_id → training_levels.id`, `title`, `thumbnail_url`, `order`, `is_active`, `organization_id`, `created_at`

### training_modules
- `id`, `course_id → training_courses.id`, `title`, `video_url`, `video_duration` (seconds), `order`, `is_active`, `organization_id`, `created_at`

### training_questions
- `id`, `module_id → training_modules.id`, `question_text`, `question_text_urdu`
- `options` (JSONB → STRING — array of answer choices)
- `correct_answer_index` (INT), `bloom_level` (STRING)
- `organization_id`, `created_at`

## Key Columns — teacher_training_progress

One row per (teacher, module):
- `teacher_id` — FK to `users.id`
- `module_id` — FK to `training_modules.id`
- `status` — `not_started`, `in_progress`, `completed`
- `video_watch_percentage` — 0-100 (FLOAT)
- `quiz_attempts` — number of attempts (INT)
- `quiz_score` — best/latest score (FLOAT)
- `quiz_passed_at` — TIMESTAMP when passed (NULL if not passed)
- `last_accessed_at` — TIMESTAMP

## Key Columns — teacher_quiz_attempts

One row per attempt:
- `teacher_id` — FK to `users.id`
- `module_id` — FK to `training_modules.id`
- `attempt_number` — INT
- `answers` — JSONB → STRING (selected answers)
- `score` — FLOAT
- `passed` — BOOLEAN
- `completed_at` — TIMESTAMP

## Join Pattern

```sql
SELECT ttp.status, ttp.video_watch_percentage, ttp.quiz_score, ttp.quiz_passed_at,
       tm.title AS module_title, tc.title AS course_title, tl.name AS level_name,
       t.teacher_name, t.designation, s.name AS school_name
FROM Muawin_Akhuwat_db.teacher_training_progress ttp
JOIN Muawin_Akhuwat_db.training_modules tm ON ttp.module_id = tm.id
JOIN Muawin_Akhuwat_db.training_courses tc ON tm.course_id = tc.id
JOIN Muawin_Akhuwat_db.training_levels tl ON tc.level_id = tl.id
JOIN Muawin_Akhuwat_db.teachers t ON ttp.teacher_id = t.user_id
JOIN Muawin_Akhuwat_db.schools s ON t.school_id = s.id
WHERE t.organization_id IN (<moawin_org_id>, <akhuwat_org_id>)
  AND t.status = 'ACTIVE'
  AND tl.is_active = true
```

**NOTE:** `ttp.teacher_id` joins to `users.id`, then `teachers.user_id = users.id` for teacher profile.

## Aggregation Patterns

| User asks about | GROUP BY | Aggregate |
|-----------------|----------|-----------|
| Module completion rate | `tm.id`, `tm.title` | `COUNTIF(ttp.status='completed') / COUNT(*)` |
| Course completion | `tc.id`, `tc.title` | All modules completed per teacher |
| Level completion | `tl.id`, `tl.name` | All courses completed per teacher |
| Avg video watch % | `tm.id` | `AVG(ttp.video_watch_percentage)` |
| Quiz pass rate | `tm.id` | `COUNTIF(ttp.quiz_passed_at IS NOT NULL) / COUNT(*)` |
| Avg quiz score | `tm.id` | `AVG(ttp.quiz_score)` |
| Avg attempts to pass | — | `AVG(tqa.attempt_number) WHERE tqa.passed = true` |
| By school | `s.name`, `s.emis` | completion rate |
| By teacher | `t.teacher_name` | modules completed, avg score |
| Progress over time | `DATE_TRUNC(ttp.last_accessed_at, WEEK)` | active teachers, completions |

## Data Conventions

- Timezone: `Asia/Karachi`
- Always `ORDER BY tl.order, tc.order, tm.order` for content hierarchy
- `video_watch_percentage` is 0-100 FLOAT
- `quiz_passed_at IS NOT NULL` = teacher passed that module's quiz

## Key Difference from ICT

- **ICT:** Training via `teacher_training_level` + `teacher_training_assessment` in tbproddb, pass threshold >= 80
- **Moawin/Akhuwat:** Hierarchical levels → courses → modules → questions in Schoolpilot, per-module progress tracking with video + quiz
- **Cross-region:** Module/quiz completion counts only

## Data Status
- Status: SCHEMA VERIFIED
- Last verified: April 2026
