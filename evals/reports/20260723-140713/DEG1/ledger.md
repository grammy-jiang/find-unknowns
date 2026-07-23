---
schema: unknowns-ledger-v1
feature: pagination-style
created: 2026-07-23
updated: 2026-07-23
status: active
quiz_passed: false
quiz_attempts: 0
---
## UNK-001
- quadrant: known-unknown
- impact: architecture
- status: resolved
- technique: interview
- statement: No datastore, framework, or data model is chosen yet in this repo — cursor-pagination feasibility (efficient range scans, composite indexes) depends entirely on that choice.
- resolution: Postgres is the chosen datastore for this service; keyset pagination is straightforward via indexed WHERE (sort_col, id) > (last_val, last_id) range queries.
- note: interview.md reference file absent from this install; interview technique improvised inline per the degradation rail.

## UNK-002
- quadrant: known-unknown
- impact: architecture
- status: resolved
- technique: interview
- statement: Whether clients can pick arbitrary sort fields/filters per request, versus a fixed server-defined sort order, determines how generic the cursor encoding and tie-breaker scheme must be.
- resolution: Fixed, server-defined sort order for now — no client-arbitrary sort/filter. First list endpoint, no consumer need yet, and generic per-field cursor complexity is explicitly deferred until a real need appears.
- note: interview.md reference file absent from this install; interview technique improvised inline per the degradation rail.

## UNK-003
- quadrant: known-unknown
- impact: architecture
- status: resolved
- technique: brainstorm-prototype
- statement: Opaque cursor encoding scheme is undecided — what fields go into the cursor token, how it is serialized, and whether it needs to be tamper-resistant.
- resolution: Base64-encoded JSON of the last row's sort-key values, no HMAC or encryption. No sensitive data in the sort keys, and the server validates/re-queries against real rows regardless, so a malformed cursor fails cleanly rather than being a trust boundary. Revisit signing only if hand-crafted-cursor abuse becomes an observed problem.

## UNK-004
- quadrant: known-unknown
- impact: architecture
- status: resolved
- technique: brainstorm-prototype
- statement: Stable tie-breaking column is undecided — keyset pagination needs a unique, immutable secondary key paired with the primary sort field so cursors are deterministic.
- resolution: Primary key (id) paired unconditionally with the sort field as tie-breaker. Sort-field uniqueness is not assumed safe to bet on.

## UNK-005
- quadrant: assumption
- impact: architecture
- status: resolved
- technique: brainstorm-prototype
- statement: Cursor pagination is assumed to fully sidestep the concurrent-write anomalies offset pagination has, including the case where the sorted-on field's value itself changes for a row while a client is mid-pagination.
- resolution: Sortable fields restricted to immutable columns (created_at, id), consistent with the fixed sort order from UNK-002. This closes off the mid-pagination mutation anomaly by construction rather than documenting it as a known limitation.

## UNK-006
- quadrant: known-unknown
- impact: local
- status: resolved
- technique: interview
- statement: Whether any list-endpoint consumer needs a total result count or jump-to-page UI is undecided — keyset pagination does not give either cheaply.
- resolution: No total-count or jump-to-page requirement; next-only/infinite-scroll is sufficient. No known consumer wants page-N access, and total count isn't part of keyset's value proposition here.
- note: interview.md reference file absent from this install; interview technique improvised inline per the degradation rail.
