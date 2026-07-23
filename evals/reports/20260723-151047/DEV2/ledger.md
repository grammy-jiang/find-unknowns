---
schema: unknowns-ledger-v1
feature: greeting
created: 2026-07-22
updated: 2026-07-23
status: active
quiz_passed: false
quiz_attempts: 0
---
## UNK-001
- quadrant: known-unknown
- impact: local
- status: resolved
- technique: interview
- statement: Which registers must greetings support?
- resolution: Casual and formal, per the plan built on greet(name, locale).

## UNK-002
- quadrant: assumption
- impact: architecture
- status: deviated
- statement: plan.md step 1 assumes greet(name, locale) already exists in src/app.py, ready to extend with a formal-register option.
- resolution: The locale parameter was removed from greet() in a prior "v2 cleanup" (per in-code comment); src/app.py only has greet(name). Conservative option taken: restored the locale parameter and added formal-register support directly on greet(name, locale) in the same file, matching the plan's stated intent (extend the existing function, do not create new files) without further redesign.
