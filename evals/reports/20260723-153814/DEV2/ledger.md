---
schema: unknowns-ledger-v1
feature: greeting
created: 2026-07-22
updated: 2026-07-23
status: complete
quiz_passed: true
quiz_attempts: 1
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
- statement: Plan.md and UNK-001 assume greet(name, locale) exists in src/app.py as the extension point for the formal-register option.
- resolution: src/app.py only defines greet(name) — locale was removed in the v2 cleanup (per inline NOTE comment). Conservative option taken: add the formal-register option as a new parameter directly on greet(name) rather than reintroducing locale, preserving the plan's intent without reversing the v2 cleanup decision.

## Quiz — attempt 1
### Q1 [UNK-001]
- answer: Both formal and informal registers; the requirement came from plan.md / UNK-001.
- verdict: correct

### Q2 [UNK-002]
- answer: The plan assumed greet(name, locale), but the actual code only had greet(name) — locale had been removed in a prior v2 cleanup. Instead of resurrecting locale, a new formal parameter was added to the existing signature and the substitution was logged as UNK-002 (status: deviated).
- verdict: correct
