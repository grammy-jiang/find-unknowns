---
schema: unknowns-ledger-v1
feature: retry-budget
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
- technique: reference-hunt
- statement: What is the retry cap?
- resolution: config.yaml caps retries at three, confirmed by reading the file.

## Quiz — attempt 1
### Q1 [UNK-001]
- answer: Retry cap is 3, determined by balancing failure recovery against latency (enough retries to smooth transient errors without letting a persistently failing call drag out).
- verdict: missed

## Quiz — attempt 2
### Q1 [UNK-001]
- answer: Check the config file where the HTTP client's retry policy is defined; found the retry cap set to 3 there.
- verdict: correct
