---
paths:
  - "src/**/*.py"
  - "tests/**/*.py"
---

# Clarification Rules

## Mandatory Questions Before Any Query

### Teacher Level
Always ask: "Which teacher level? PRIMARY, MIDDLE, SECONDARY, or all?"
- `levels` is a JSON array in `users_teacherprofile` — teachers can have one or multiple levels
- The base `teacher_profiles` table filters to PRIMARY only — for other levels, the query must change
- `user_school_profiles` only contains PRIMARY teachers
- Never assume PRIMARY — the user must specify

### Region
Always ask: "Which region? ICT/Islamabad or another?"
- `organization_id` maps to region, not just organization
- `organization_id = 1` = ICT/Islamabad
- Different regions have different org IDs and different school reference tables
- The base queries filter to org 1 + FDE_Schools — for other regions, the query and reference tables change
- Never assume ICT/Islamabad — the user must specify

## When to Ask
- These two questions (level + region) are mandatory for ANY query that involves teachers, schools, or per-teacher metrics
- Ask at the start of the clarification flow, before resolving to a specific metric
- If the user already specified in their question (e.g., "PRIMARY teachers in Islamabad"), don't re-ask
