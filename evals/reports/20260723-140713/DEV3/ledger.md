---
schema: unknowns-ledger-v1
feature: checkout-flow
created: 2026-07-22
updated: 2026-07-22
status: active
quiz_passed: false
quiz_attempts: 0
---
## UNK-001
- quadrant: known-unknown
- impact: local
- status: resolved
- technique: interview
- statement: How do promo codes enter the checkout flow?
- resolution: Via apply_discount(cart, code) per the plan.

## UNK-002
- quadrant: assumption
- impact: architecture
- status: deviated
- statement: apply_discount(cart, code) accepts a discount code argument to apply promo codes.
- resolution: apply_discount only accepts cart; discount codes were removed and discounts are now automatic. Conservatively wired a checkout(cart) entry point that calls apply_discount(cart) with no code argument, instead of adding an unused code parameter to resurrect removed functionality.
