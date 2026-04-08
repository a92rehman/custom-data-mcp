# Caching

## Transparency
- Every cached response MUST show: computation timestamp + source refresh timestamp
- Users can force-refresh to bypass cache at any time

## What to cache
- Only standard Gold metric requests with common parameters
- Pre-compute (warm) Theory of Change and FICO metrics on schedule — don't wait for first request
- Never cache ad-hoc, filtered, or drill-down queries

## Invalidation
- Invalidate when cache age exceeds metric's `freshness_sla_hours` — never serve stale silently
- Invalidate on: source table DML, metric YAML change, or max TTL exceeded

## Loop Prevention
- If a cached response triggers a follow-up query that returns the same cached data, detect the cycle and force a live BigQuery fetch on the second occurrence
- Never serve the same stale cached result more than once in a single session without warning the user: "You're seeing cached data from [timestamp]. Want me to fetch live?"
- If cache warming fails (BigQuery down, query error), do NOT retry warming in a tight loop — backoff and skip until next scheduled cycle
- If a user force-refreshes and the live query also fails, return the stale cache WITH explicit label: "Live query failed. Showing cached result from [timestamp]. This data may be outdated." — do NOT silently fall back to cache
- If cache + live query both fail, say so clearly — never loop between cache miss → query fail → cache miss
- Cap cache-warming retries at 2 per cycle. If both fail, log the failure and wait for next cycle

## Design rationale
docs/VISION.md Section 11
