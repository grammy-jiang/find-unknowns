---
schema: unknowns-ledger-v1
feature: api-client-rate-limiting
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
- statement: What language/runtime and HTTP stack will the API client be built on — nothing in the repo indicates this yet.
- resolution: Go, built directly on the standard library net/http client; no third-party HTTP library, to avoid fighting someone else's abstractions.

## UNK-002
- quadrant: known-unknown
- impact: architecture
- status: resolved
- technique: interview
- statement: Does "rate limiting" mean the client proactively throttles its own outbound calls to stay under a budget, handles the server telling it to back off (429/Retry-After), or both.
- resolution: Both. Proactive per-endpoint budget throttling on the outbound side, plus correct 429/Retry-After handling on the inbound side; user explicitly wants both so one failure mode doesn't get missed.

## UNK-003
- quadrant: known-unknown
- impact: architecture
- status: resolved
- technique: interview
- statement: Which external API(s) this client talks to, and whether their actual published rate limits (numbers, burst vs sustained, per-endpoint vs global) are known.
- resolution: No specific target API. This is a generic HTTP client; per-endpoint budgets are caller-configured at construction/call time, not hardcoded against any provider's published limits.

## UNK-004
- quadrant: known-unknown
- impact: architecture
- status: resolved
- technique: interview
- statement: What unit counts as an "endpoint" for per-endpoint limits — literal URL, or a route template/pattern (matters for parameterized paths like /users/{id} and for unbounded bucket-key growth).
- resolution: Caller-supplied bucket key string (e.g. "GET /users/{id}"), passed in explicitly per call. The limiter never infers templates from literal request URLs; no unbounded map growth risk since keys come from a caller-controlled, presumably-bounded set.

## UNK-005
- quadrant: assumption
- impact: architecture
- status: resolved
- technique: interview
- statement: The client will run single-threaded/single-process, so the limiter's state does not need to be thread-safe or shared across processes.
- resolution: Assumption rejected. User confirmed single-threaded use was never actually verified; decided to build for concurrent use from the start (mutex or atomics guarding the limiter's counters) rather than bet on an unconfirmed constraint, especially given Go's goroutine-heavy idioms. Cross-process/distributed sharing (e.g. Redis-backed) is out of scope unless UNK-003 surfaces a multi-process deployment need.

## UNK-006
- quadrant: known-unknown
- impact: architecture
- status: resolved
- technique: brainstorm-prototype
- statement: What should happen when a call would exceed the limit — block and wait, reject immediately with an error, or queue with a timeout. Nobody has decided this yet.
- resolution: Option D — expose both Allow(key) bool (non-blocking) and Wait(ctx, key) error (blocking, context-aware) on the same limiter, sharing one internal token-accounting core. Caller picks per call site; no internal queue (fairness/starvation risk rejected along with option C).

## UNK-007
- quadrant: known-unknown
- impact: architecture
- status: resolved
- technique: interview
- statement: How callers set a per-endpoint budget — static config supplied once at construction, or a Configure/SetLimit call usable anytime — and what Allow/Wait do for a key that was never configured.
- resolution: Configure(key, Rate) error, callable anytime, guarded by the same mutex as the counters. Allow/Wait return ErrNotConfigured for an unconfigured key rather than defaulting to unlimited.

## UNK-008
- quadrant: known-unknown
- impact: architecture
- status: resolved
- technique: interview
- statement: Whether 429/Retry-After handling is automatic (the client retries once internally) or purely observed and reported back to the caller as a typed error carrying the delay.
- resolution: Observed and reported, not auto-retried. Do(ctx, req, key) parses Retry-After on a 429 into *RateLimitedError{RetryAfter time.Duration} and returns it; caller decides whether to retry.

## UNK-009
- quadrant: known-unknown
- impact: architecture
- status: resolved
- supersedes: UNK-006
- statement: UNK-006's recorded signature "Allow(key) bool" is incomplete now that UNK-007 requires Allow to report ErrNotConfigured for an unconfigured key, which a bare bool cannot carry.
- resolution: Allow's actual signature is Allow(key string) (bool, error); Wait's signature (ctx, key) error needed no change. Implemented as such in ratelimit/limiter.go.

## UNK-010
- quadrant: assumption
- impact: local
- status: deviated
- statement: The plan assumed I would verify the implementation by running go build, go vet, and go test -race in this session before handing it off.
- resolution: Bash invocations of the go toolchain (go build/vet/test) were blocked by the session's permission system on every attempt, while non-go commands succeeded. Conservative option taken: the code is handed off explicitly marked as unverified rather than claimed as tested; asked the user to run go build ./..., go vet ./..., and go test -race ./... themselves, or grant approval so this can be run in-session.
