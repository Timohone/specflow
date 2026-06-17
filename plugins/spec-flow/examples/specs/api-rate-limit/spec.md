# Spec: API rate limiting

> Status: in progress · Slug: `api-rate-limit` · Created: 2026-06-17

## Problem
The public REST API has no rate limiting, so a single client can exhaust
database connections and degrade service for everyone. We need per-client
limits before onboarding the next batch of integration partners.

## Goals
- Protect the API from accidental and abusive request floods.
- Give clients clear, standard feedback when they are limited.
- Make limits configurable without a redeploy.

## Non-goals
- Per-endpoint custom limits (one global limit per client is enough for v1).
- Distributed rate limiting across regions (single-region for now).
- Billing or quota plans.

## Requirements
1. Each API client is limited to N requests per rolling 60-second window.
2. The limit N is read from configuration at startup.
3. Exceeding the limit returns HTTP 429 with a `Retry-After` header.
4. Responses include `X-RateLimit-Limit` and `X-RateLimit-Remaining` headers.
5. Unauthenticated requests are limited by client IP.

## Acceptance criteria
- [x] A client exceeding N requests in 60s receives HTTP 429.
- [x] 429 responses include a `Retry-After` header in seconds.
- [ ] Successful responses include `X-RateLimit-Limit` and `X-RateLimit-Remaining`.
- [ ] The limit N is configurable via env var `RATE_LIMIT_PER_MIN` (default 100).
- [ ] Unauthenticated requests are bucketed by IP, authenticated by client id.

## Open questions
- Should health-check endpoints be exempt? (assumed yes for v1)
