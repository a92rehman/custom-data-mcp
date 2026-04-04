# Caching

## Principle

Transparency and freshness over speed. Users always know how fresh their data is.

## Rules

- Every cached response shows: `"LP adoption: 71.3% (computed 45 min ago, source refreshed 2 hrs ago)"`
- Users can force-refresh to bypass cache
- If cache age exceeds the metric's `freshness_sla_hours` → auto-invalidate, never serve stale silently
- Only cache standard Gold metric requests with common parameters — never ad-hoc/filtered/drill-down queries

## Cache Warming

Critical metrics are pre-computed on schedule, not cached on first request:


| Metrics              | Warm Frequency | Trigger                |
| -------------------- | -------------- | ---------------------- |
| Theory of Change (5) | Every 24 hours | After BigQuery refresh |
| FICO Observation (6) | Every 24 hours | After BigQuery refresh |
| Technical (12)       | Every 3 hour   | After health refresh   |
| All others           | On-demand      | First request          |


## Invalidation

- Source table DML → invalidate all dependent caches
- Metric YAML change → invalidate that metric's cache
- Max TTL of `CACHE_TTL_SECONDS` regardless of SLA
- Manual invalidation endpoint for data team

## When BigQuery Is Down + Cache Is Stale

Return stale value with explicit warning: "Warning: data is [N hours] past SLA. BigQuery unavailable." See [failure-handling.md](failure-handling.md).