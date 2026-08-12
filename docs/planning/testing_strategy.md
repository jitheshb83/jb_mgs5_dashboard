# Testing Strategy

## Principle

Every feature ships with tests that prove it works, written against the contracts in
`docs/architecture/api_contract.md` and `docs/architecture/data_model.md` — not against
whatever the implementation happens to do. Tests should fail if the contract is violated,
even if the code "runs."

## Backend (pytest)

**Unit tests** (`backend/tests/unit/`):
- Rate-limit gate logic: given a `last_fetched_at`, correctly decides live vs. cached
  (boundary cases: exactly 30 min, 29 min, 31 min).
- SOH cycle detection: given a sequence of snapshots, correctly identifies full-charge
  cycles and excludes partial charges (see `soh_methodology.md` for the rules to test against).
- Settings validation: rejects invalid values (e.g. schedule interval < min refresh gap).

**Integration tests** (`backend/tests/integration/`):
- Full `/api/refresh` → SQLite round-trip, using a **mocked** `saic_ismart_client_ng` response
  (never call the real SAIC API in automated tests — it's rate-limited and tied to a real vehicle).
- `/api/history` query param filtering (date range, limit).
- `/api/soh` returns empty array before 2+ cycles exist, populated array after.

**Mocking the SAIC API:** capture 1-2 real (anonymized) response payloads once during manual
development and store as fixtures in `backend/tests/fixtures/`. Strip any credentials, VIN, or
location data from fixtures before committing.

## Frontend (Vitest + React Testing Library)

- Dashboard renders correctly given a mock Snapshot object (including all-null fields — must
  not crash, must show placeholders).
- Refresh button disables while a request is in flight, re-enables after.
- Settings form validates before submitting (interval >= min gap).
- Trend chart renders with 0, 1, and many history points without crashing.

## What NOT to test in v1

- Real network calls to SAIC (mocked only, per above).
- Visual/pixel-perfect UI regression testing — out of scope for a personal single-user tool.
- Load/performance testing — single user, local, not a concern at this scale.

## Definition of done for any feature

1. Implementation matches `api_contract.md` / `data_model.md` exactly, or those docs were
   updated first and the user was told.
2. Tests written and passing.
3. No unrelated files changed (see root `CLAUDE.md` — surgical changes only).
