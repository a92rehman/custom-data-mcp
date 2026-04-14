# Data Governance

## Metric Access
- All analytical queries MUST follow the governed query definitions in `.claude/rules/` subfolders — never generate ad-hoc SQL
- Read the relevant domain rules (e.g., `ict-islamabad/dimensions/teachers/teacher-query-rules.md`) to find the correct query
- Never allow direct access to raw tables that aren't covered by a rule definition
- No matching rule → tell the user no governed query exists for this request, log the gap

## Conversation
- Never assume when ambiguous — clarify first, max 3 rounds, then escalate to data team
- See `.claude/rules/index.md` for which domain rules to read based on the question

## Audit
- Every interaction creates an immutable audit log entry via the MCP audit_logger

## Data Classification
- `public`: aggregate KPIs safe for external/donor reports
- `internal`: all team-level and individual-level data — accessible to all internal Taleemabad teams
- `external_guarded`: data leaving the organization — requires explicit confirmation + audit logging
- Individual teacher FICO scores and student outcomes are `internal`, not restricted

## Test User Exclusion (All Regions)
- **Schoolpilot (neondb):** Filter `users.testing_account = false` OR use name-based patterns to exclude internal test accounts
- **Zavia (zavia1):** Filter `users.testing_account = false` OR name-based exclusions where applicable
- **Purpose:** Prevent test/pilot data from polluting production KPI reports
- **When applying:** All user counts, coaching counts, assessment counts must exclude test accounts
- Never include test data in dashboards or external reports without explicit flagging

## Database Priority Rules
- **User/Teacher data:** Schoolpilot (`neondb.public.users` + `neondb.public.teachers`) is canonical; Zavia is secondary/verification only
- **Lesson plans, coaching, assessments:** Zavia (`zavia1.public.*`) is canonical; Schoolpilot provides supporting context
- **Teacher enrichment:** Always LEFT JOIN Schoolpilot users with teachers table on `teachers.user_id = users.id` for institutional attributes (EMIS, qualifications, designation, etc.)
- **Cross-database joins:** Use phone_number or other stable identifiers where available; prefer primary keys within same database
- Never use secondary database as source of truth for teacher counts or institutional attributes
