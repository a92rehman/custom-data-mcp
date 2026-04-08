# Observability

- Log 3 layers on every interaction: Request (who/what) → Execution (which metric/SQL/cost) → Response (result/freshness/feedback)
- Audit entries are immutable with SHA-256 hash chain — never update or delete
- Use `structlog` for server logs (stderr) — never `print()`, never stdout with stdio transport
- Use `ctx.info()`/`ctx.warning()`/`ctx.error()` for client-visible messages
- Include correlation IDs (session_id, event_id) in every log line
- Design rationale: docs/VISION.md Section 6
