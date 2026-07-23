---
schema: unknowns-ledger-v1
feature: search-index
created: 2026-07-22
updated: 2026-07-23
status: complete
quiz_passed: false
quiz_attempts: 2
---
## UNK-001
- quadrant: known-unknown
- impact: architecture
- status: resolved
- technique: interview
- statement: Which fields get indexed?
- resolution: Title and tags only; body indexing deferred for cost.
## UNK-002
- quadrant: known-unknown
- impact: local
- status: open
- statement: Does the analyzer handle CJK text?
## Quiz — attempt 1
- warning: generated with UNK-002 still open (untriaged) — user insisted on generation despite the gate
### Q1 [UNK-001]
- answer: Title and body fields are indexed, for highest-signal relevance-ranking terms.
- verdict: missed
## Quiz — attempt 2
- warning: closed fully-revealed — UNK-001 (the only quizzable entry) was explained in-conversation after two misses, at user's request; no pass path remained
### Q1 [UNK-001]
- answer: Deferred field was updated_at (cost reasons); title and body made the cut.
- verdict: missed
