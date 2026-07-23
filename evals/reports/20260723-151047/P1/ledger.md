---
schema: unknowns-ledger-v1
feature: billing
created: 2026-07-22
updated: 2026-07-23
status: active
quiz_passed: false
quiz_attempts: 0
---
## UNK-001
- quadrant: assumption
- impact: local
- status: resolved
- technique: interview
- statement: Proration rounding follows the invoice currency's minor unit.
- resolution: False — always round to 2 decimals regardless of currency; defer to Stripe for anything more nuanced. Decided via interview 2026-07-23.
