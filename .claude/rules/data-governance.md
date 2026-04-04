# Data Governance

## Metric Access
- All analytical queries MUST resolve to a pre-approved metric definition before execution — never generate ad-hoc SQL
- The metric definitions will be stored as version-controlled YAML files (not yet built — see docs/VISION.md Section 4 for the planned lifecycle: draft → review → approved → certified → deprecated)
- Never allow direct access to raw or intermediate data tables through the MCP
- No matching metric → show closest matches, log the gap — never fall back to raw SQL

## Conversation
- Never assume when ambiguous — clarify first, max 3 rounds, then escalate to data team

## Audit
- Every interaction creates an immutable audit log entry

## Data Classification
- `public`: aggregate KPIs safe for external/donor reports
- `internal`: all team-level and individual-level data — accessible to all internal Taleemabad teams
- `external_guarded`: data leaving the organization — requires explicit confirmation + audit logging
- Individual teacher FICO scores and student outcomes are `internal`, not restricted
