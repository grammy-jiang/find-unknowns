---
schema: unknowns-ledger-v1
feature: checkout-cache
created: 2026-07-22
updated: 2026-07-23
status: complete
quiz_passed: true
quiz_attempts: 2
---
## UNK-001
- quadrant: known-unknown
- impact: architecture
- status: resolved
- technique: interview
- statement: What should the cache key be?
- resolution: Hash of the normalized cart contents, so identical carts share an entry.
## UNK-002
- quadrant: known-unknown
- impact: architecture
- status: resolved
- technique: brainstorm-prototype
- statement: Which eviction policy?
- resolution: TTL-based eviction; correctness beats hit-rate for checkout data.
## UNK-003
- quadrant: assumption
- impact: local
- status: accepted-risk
- risk: Behavior above ten thousand concurrent carts is untested; monitored by the deviation rail.
- statement: The cache holds at production load.

## Quiz — attempt 1
### Q1 [UNK-001]
What did we decide the cache key should be, and why that choice over alternatives?
- answer: Hash of the cart contents, so identical carts map to the same entry instead of duplicating cache slots.
- verdict: correct
### Q2 [UNK-002]
Which eviction policy did we settle on for the cache, and what consideration drove that choice?
- answer: No idea, probably random eviction.
- verdict: missed
### Q3 [UNK-003]
What risk did we accept about the cache's behavior at production load, and what's monitoring it?
- answer: Behavior above 10k carts under production load is untested; the deviation rail is monitoring it.
- verdict: correct

## Quiz — attempt 2
### Q1 [UNK-002]
When the cache needs to evict entries, what's the deciding factor — age of an entry, or how often it's been hit?
- answer: Age of an entry — TTL-based eviction. Correctness beats hit-rate here, so we chose to expire entries rather than optimize for access frequency.
- verdict: correct
