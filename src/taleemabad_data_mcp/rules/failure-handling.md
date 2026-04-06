# Failure Handling

- Never return partial or wrong data silently — every failure tells user what happened + what to try
- Max 2 retries with exponential backoff (1s, 4s) — then stop and report
- Circuit breaker: 3 failures in 5 min → open for 2 min → probe → recover or reset
- Max 3 clarification rounds → escalate: "Can't resolve. Here's what I understood. Routing to data team."
- Dead letter queue for unresolvable requests — never retry automatically, include in weekly digest
- BigQuery down → serve last-known value with "stale / unavailable" warning
- Ambiguous metric → list all matches, force user to choose — never pick one
- Design rationale: docs/VISION.md Section 12
