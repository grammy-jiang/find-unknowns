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
- status: abandoned
- statement: Where the actual session-storage code lives (this repo has no matching code — searched files, git history, and content for redis/cookie/jwt/session_id/express-session/flask-session with zero hits) and what the current and target storage mechanisms are.
- note: Routed to interview; user declined to answer three times ("go with whatever you think," "trust your call"), each time asked directly for a repo/path/service name or confirmation this is greenfield. Abandoned rather than fabricated, since no technique can resolve a fact only the user holds and no risk-acceptance framing applies (nothing downstream can proceed without it).
