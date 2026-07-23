---
schema: unknowns-ledger-v1
feature: session-storage-migration
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
- statement: Whether the app runs (or will run) as a single process or multiple/horizontally-scaled instances — decides whether a shared store is required at all and which store fits.
- resolution: User declined to answer twice, including after being told this was a factual question rather than a preference, and asked to go with the recommendation. Assumed multi-instance-capable deployment as the safer default, since MemoryStore's known failure mode (repo comment, server.js:6-7) is exactly this, and nothing in the repo signals single-process-only.

## UNK-002
- quadrant: known-unknown
- impact: architecture
- status: resolved
- technique: interview
- statement: Which backend to migrate session storage to — no store client, infra config, or env vars for one exist anywhere in the repo.
- resolution: User deferred to recommendation. Chose Redis via connect-redis: de facto standard store for express-session, actively maintained, fits the multi-instance assumption from UNK-001.

## UNK-003
- quadrant: known-unknown
- impact: architecture
- status: accepted-risk
- statement: Whether a Redis or database instance is already provisioned and reachable from this app, or whether new infra must be stood up as part of this migration.
- risk: Cannot verify from the repo (no docker-compose, env example, or infra config) or from the user, who deferred on adjacent questions. Mitigated by making the connection fully configurable via a REDIS_URL env var with no hardcoded host — provisioning itself is an ops prerequisite outside this code change's scope and must be confirmed before deploy.

## UNK-004
- quadrant: assumption
- impact: architecture
- status: accepted-risk
- statement: Assuming sessions surviving process restarts and being shared across instances introduces no new security or product requirement — today every restart silently logs everyone out, and that may or may not be relied upon.
- risk: Confirming this needs a product/security review out of scope for this session. Low risk by default — persisting sessions is standard practice, and MemoryStore's restart-wipe reads as an accident of the default rather than a designed control — but flagged for confirmation before relying on it in a security-sensitive context.

## UNK-005
- quadrant: unknown-known
- impact: local
- status: investigating
- technique: brainstorm-prototype
- statement: Whether the chosen store correctly implements session touch (idle-timeout refresh under resave: false) the way MemoryStore does implicitly — a common source of surprising idle-timeout regressions when swapping session stores.
- note: WebFetch/WebSearch were unavailable this session to verify connect-redis's touch() behavior against its docs. Will verify empirically with an idle-timeout test once the store is wired up during implementation, rather than resolve from memory.
