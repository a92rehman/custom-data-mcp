# Data Governance

## Metric Access
- All analytical queries MUST follow the governed query definitions in `.claude/rules/` subfolders — never generate ad-hoc SQL
- Read the relevant domain rules (e.g., `dimensions/teachers/teacher-data.md`) to find the correct query
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
