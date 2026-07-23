---
schema: unknowns-ledger-v1
feature: notifications
created: 2026-07-22
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
- statement: Delivery channel for v1?
- resolution: Platform events API, chosen for zero polling.

## UNK-002
- quadrant: assumption
- impact: architecture
- status: deviated
- statement: UNK-001's resolution (deliver via Platform events API) assumed an existing codebase/repo where that API's integration point is reachable.
- resolution: The working directory contains no application source at all (no repo, language, or framework) — only notes/unknowns and the find-unknowns skill. Conservative option taken: pause before scaffolding or writing any implementation code and ask the user to point to the target repo/stack, rather than guessing an architecture that isn't recorded anywhere in the ledger.

## UNK-003
- quadrant: assumption
- impact: architecture
- status: deviated
- statement: UNK-001 resolved delivery via the Platform events API on the assumption it would remain available, avoiding polling entirely.
- resolution: The Platform events API was removed from the platform (per user, removed the week of 2026-07-16, ahead of this 2026-07-23 build). Conservative option taken: replace the event listener with an HTTP-polling workaround that preserves as much of UNK-001's original intent as possible — an adaptive/backoff poll schedule plus a client-side rate limiter, instead of naive fixed-interval polling, to keep load on the platform close to the original zero-polling spirit.
