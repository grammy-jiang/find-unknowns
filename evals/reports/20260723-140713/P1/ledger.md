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
- resolution: No payment-processor decision pins this yet. User chose invoice-currency minor unit (cents for USD, whole units for JPY/KRW, etc.) as the safer default in interview, 2026-07-23; not a firm external constraint, revisit if a processor is selected later.
- note: reference-hunt attempted first (grounding search over proration/currency/billing/invoice terms) found no existing code or docs to verify against; re-routed to interview per reference-hunt.md degradation guidance.
