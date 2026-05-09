# Student Results — AI Assessment Rules — ICT/Islamabad

> **STATUS: CONFLICT** — CEO doc lists `tbproddb.student_learning_studentassessmentresult` but transcript states "AI student assessments are not active in Islamabad right now." Needs owner confirmation before using in dashboard/production reporting.

## When These Rules Apply

User asks about:
- AI student assessment results in ICT
- Student marks or AI remarks from assessments
- Student learning assessment outcomes

## Key Tables

| Table | Role | Rows | Status |
|-------|------|------|--------|
| `tbproddb.student_learning_studentassessmentresult` | Student AI assessment outcomes | 133 | **CONFLICT — may not be active** |

## Key Columns

- `id` — primary key (INTEGER)
- `created`, `modified` — timestamps (TIMESTAMP)
- `is_active` — active filter (STRING)
- `uuid` — unique identifier (STRING)
- `deleted_at` — soft delete (STRING)
- `obtained_marks` — student's score (FLOAT)
- `ai_remarks` — AI-generated feedback text (STRING)
- `assessment_id` — FK to assessment (INTEGER)
- `student_id` — FK to student (INTEGER)

## Data Summary

- 133 results total
- 65 unique students
- 18 unique assessments
- Small dataset — may be pilot/test data

## Engagement / Usage / Retention Queries
If the user asks about student data **engagement**, **usage**, or **retention**, always ask:
- "What specific duration? (e.g., last 7 days, last 30 days, this week, this month)"
- Never assume a time window

> **Product analytics for student list, results, FLN, report cards:** See `student-product-analytics.md` in this directory.

## Conflict Details

The CEO's KPI document row points to this table, but during the reconciliation meeting the transcript states: "AI student assessments are not active in Islamabad right now." This creates ambiguity:

1. The table exists and has 133 rows — suggesting it was used at some point
2. The team says it's not currently active — suggesting it may be pilot/legacy data
3. **Do not use for production KPI reporting until confirmed by data team**

## Required Filters (when confirmed active)

- `is_active = 'true'`
- `deleted_at IS NULL`
- Join to student dimension for school/grade context

## Key Difference from RWP

- ICT: simple marks + AI remarks (133 rows, possibly inactive)
- RWP: rich reading assessment system with WCPM, accuracy, comprehension, pronunciation (277 rows, active)
- Cross-region: **not comparable** until ICT system is confirmed active

## Verification Queries

```sql
-- Check if data is recent or stale
SELECT MIN(created) as earliest, MAX(created) as latest, COUNT(*) as total
FROM tbproddb.student_learning_studentassessmentresult
WHERE is_active = 'true'

-- Check assessment IDs for context
SELECT DISTINCT assessment_id, COUNT(*) as results
FROM tbproddb.student_learning_studentassessmentresult
GROUP BY assessment_id
ORDER BY results DESC
```
