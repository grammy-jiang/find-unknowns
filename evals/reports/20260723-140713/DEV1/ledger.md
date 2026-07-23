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
- quadrant: known-unknown
- impact: architecture
- status: resolved
- technique: brainstorm-prototype
- statement: Delivery channel for v1, now that the platform events API has been removed?
- resolution: Adaptive/backoff polling — poll aggressively after detected activity, back off toward a capped interval when quiet. Chosen over fixed-interval polling (worse freshness/cost balance), conditional polling and webhooks (both depend on unconfirmed platform capabilities post-removal).
- supersedes: UNK-001

## UNK-003
- quadrant: known-unknown
- impact: architecture
- status: resolved
- technique: interview
- statement: Language/runtime/framework for the from-scratch notifications repo?
- resolution: Go, standard library only — no external dependencies for v1. User had no strong preference beyond minimal-dependency; picked for the single-binary deploy story and goroutines/channels mapping naturally onto per-resource adaptive-backoff polling plus fan-out (UNK-002).

## UNK-004
- quadrant: known-unknown
- impact: architecture
- status: resolved
- technique: interview
- statement: Outbound notification delivery mechanism — how does a detected change actually reach a user (email, push, in-app feed, webhook/Slack, SMS)?
- resolution: In-app feed only for v1, single non-pluggable channel — a persisted, per-user notification store the poller writes to and a client reads from. No sink abstraction/interface layer yet; explicitly deferred until a second channel is actually needed.

## UNK-005
- quadrant: assumption
- impact: local
- status: resolved
- technique: brainstorm-prototype
- statement: In-process, in-memory storage (no durability across restarts) is sufficient for the v1 in-app feed.
- resolution: Confirmed by building it: a mutex-guarded map keyed by user ID is enough to satisfy UNK-004's scope (single channel, read via a small HTTP endpoint). Explicitly not durable — a restart drops the feed. Revisit if persistence across restarts becomes a real requirement; cheap to swap behind the existing Feed type's methods later.
