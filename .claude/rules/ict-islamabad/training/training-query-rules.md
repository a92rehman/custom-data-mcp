---
paths:
  - "src/**/*.py"
  - "tests/**/*.py"
---

# Teacher Training Query Rules

## When These Rules Apply

User asks about:
- Training level completion or progress
- How many teachers passed Level 1, Level 2, etc.
- Pass rates by level
- When a teacher passed a training level
- How many attempts a teacher took to pass
- Training progression across levels

## Mandatory Clarifications

### Which Level
Ask: "Which training level? A specific level, or all levels?"
- Levels come from `teacher_training_level` table
- `level_order` column defines the sequence — always sort by `level_order`

### Status Filter
Ask if relevant: "Passed teachers only, or include in-progress and pending?"
- Status values: `COMPLETED`, `IN_PROGRESS`, `PENDING`, or NULL (not yet started)
- NULL means the teacher hasn't reached that level at all

## Pass Threshold

**Score >= 80** to pass any level. This is uniform across all levels.

## Data Structure

The base query produces one row per **teacher x training level** (cross join of all teachers with all levels). This means:
- Every teacher has a row for every level, even if they haven't started
- `status IS NULL` = teacher has not passed that level
- Use this to calculate both pass rates AND non-completion rates

## Two Data Sources

Pass status comes from two sources, merged via COALESCE (q1 preferred, q2 fallback):

### q1 — Analytics Events
- Event: `'trainingExamLevelPassed'` from `analytics_analyticsevent`
- Level: `JSON_VALUE(properties, '$.ep_level_name')` — lowercased and trimmed
- Join to levels on: `LOWER(TRIM(training_level)) = level_name`
- Low-volume event — unpartitioned table acceptable here but be cost-aware on large date ranges

### q2 — Assessment Results
- Table: `teacher_training_assessment` (derived table)
- Join to `user_school_profiles` on `profile_id` to get `user_id`
- Level: `grand_quiz_id` links to `teacher_training_level.id`
- Filter: `grand_quiz_id IS NOT NULL AND score >= 80`
- Status hardcoded to `'COMPLETED'` when score >= 80

### Merge: `COALESCE(q1.value, q2.value)` — q1 preferred, q2 fills gaps

## Key Tables

| Table | Role |
|-------|------|
| `tbproddb.teacher_training_level` | Level definitions — name, order |
| `tbproddb.teacher_training_assessment` | Assessment results — score, grand_quiz_id, profile_id |
| `tbproddb.analytics_analyticsevent` | Event source for `trainingExamLevelPassed` |
| `tbproddb.user_school_profiles` | Teacher dimension — cross join with levels to build the full matrix |

## Aggregation Patterns

| User asks about | How to query |
|-----------------|-------------|
| Teachers who passed a specific level | `WHERE training_level = '...' AND status = 'COMPLETED'` |
| Pass count per level | `GROUP BY training_level`, `COUNT(DISTINCT user_id) WHERE status = 'COMPLETED'` |
| Highest level passed per teacher | `GROUP BY user_id`, `MAX(level_order) WHERE status = 'COMPLETED'` |
| Teachers who haven't passed any level | `WHERE status IS NULL`, `GROUP BY user_id HAVING COUNT(*) = total_levels` |
| Average attempts to pass | `AVG(max_attempt_no) WHERE status = 'COMPLETED'` |
| Pass rate per level | `COUNT(COMPLETED) / COUNT(all teachers)` per level |

## Important Notes

- Always `ORDER BY level_order` when displaying level progression — never alphabetical
- The cross join ensures denominator is always total teachers, not just those who attempted
- `max_attempt_no` counts attempts — useful for identifying difficult levels
- `passed_date` is the date of successful completion
