# Plan: API rate limiting

> Spec: `specs/api-rate-limit/spec.md` · Created: 2026-06-17

## Approach
Use a token-bucket limiter held in an in-process store keyed by client id (or IP
for unauthenticated requests), enforced in a single middleware. Rejected
alternative: a Redis-backed limiter — correct for multi-instance, but a non-goal
for v1 (single region/instance) and adds an external dependency we don't need yet.

## Files to change
| Path | Change | Why |
|------|--------|-----|
| `src/middleware/rate_limit.py` | create | the limiter middleware |
| `src/config.py` | edit | read `RATE_LIMIT_PER_MIN` (default 100) |
| `src/app.py` | edit | register the middleware |
| `tests/test_rate_limit.py` | create | cover the acceptance criteria |

## Steps
- [x] Add `RATE_LIMIT_PER_MIN` to config with default 100.
- [x] Implement token-bucket limiter + middleware returning 429 with `Retry-After`.
- [ ] Add `X-RateLimit-Limit` / `X-RateLimit-Remaining` headers to all responses.
- [ ] Key buckets by client id when authenticated, else by IP.
- [ ] Exempt health-check endpoints.
- [ ] Write tests covering each acceptance criterion.

## Test plan
- 429 after N+1 requests in window → criterion 1.
- assert `Retry-After` present on 429 → criterion 2.
- assert rate-limit headers on a 200 → criterion 3.
- monkeypatch env var, assert effective limit → criterion 4.
- two clients/IPs limited independently → criterion 5.

## Risks & rollback
- Risk: in-process store resets on restart (acceptable for v1). Rollback: feature
  flag `RATE_LIMIT_ENABLED=false` disables the middleware with no redeploy needed.
