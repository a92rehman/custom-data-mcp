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
- **Moawin/Akhuwat Schoolpilot (`Muawin_Akhuwat_db`):** Filter `users.is_active = true` (no `testing_account` field — `users` table is minimal auth)
- **Moawin/Akhuwat Zavia (`Zavia_db`):** Filter `users.is_test_user = false`
- **Rawalpindi Schoolpilot (`neondb`):** Filter `users.testing_account = false`
- **Rawalpindi Zavia (`zavia1`):** Filter `users.testing_account = false`
- **ICT (`tbproddb`):** Filter `u.is_testing_account = "false"`
- **Purpose:** Prevent test/pilot data from polluting production KPI reports
- **When applying:** All user counts, coaching counts, assessment counts must exclude test accounts
- Never include test data in dashboards or external reports without explicit flagging

## Database Priority Rules
- **User/Teacher data:** Schoolpilot `teachers` table is canonical (has teacher_name, CNIC, school, qualification, designation)
  - Moawin/Akhuwat: `Muawin_Akhuwat_db.teachers` (primary) + `Muawin_Akhuwat_db.users` (auth only — minimal: id, org_id, mobile_number, is_active)
  - Rawalpindi: `neondb.public.users` + `neondb.public.teachers` (PostgreSQL)
- **Lesson plans, coaching, assessments:** Zavia is canonical
  - Moawin/Akhuwat: `Zavia_db.*` (BigQuery)
  - Rawalpindi: `zavia1.public.*` (PostgreSQL)
- **Cross-dataset join (Moawin/Akhuwat):** `Muawin_Akhuwat_db.teachers.zavia_user_id = Zavia_db.users.id` (primary). Fallback: `teachers.mobile_number = Zavia_db.users.phone_number`
- **Cross-database join (Rawalpindi):** `phone_number` or other stable identifiers
- Never use Zavia as source of truth for teacher counts or institutional attributes
