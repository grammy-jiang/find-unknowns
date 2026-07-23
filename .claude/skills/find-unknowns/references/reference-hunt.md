# Reference hunt — when the code or world holds the answer

The route for entries whose answer already exists somewhere readable: `known-unknown`
entries answerable from the codebase or documentation (routing row 2), `unknown-known`
entries where an exemplar can stand in for words the user does not have (row 4), and
assumptions testable against existing code or data (assumption procedure step 2).

The principle behind row 4: when someone cannot describe what they want, the richest
specification is an existing artifact that already embodies it. Source code is the best
reference of all — it carries the real structure and behavior, not a screenshot's
impression — and it works even across languages: read the semantics, reimplement them
natively, never port line-by-line.

## How to run it

1. **Bounded search, declared scope.** Say what will be searched (paths, patterns) and
   run Grep/Glob over exactly that. The grounding rule in SKILL.md exists because
   classifying "an exemplar exists" from memory is guessing with confidence.
2. For an **answer hunt** (row 2): find the authoritative site — the actual
   implementation, config, or doc — and read it. Prefer the code over comments about the
   code.
3. For an **exemplar hunt** (row 4): have the user point at the thing they like (a
   module, a library, a component — theirs or vendored), then read how it is actually
   built and extract the properties that make it what it is. Confirm with the user:
   "the parts doing the work are X and Y — is that the part you want?"
4. For an **assumption verification** (step 2): state the assumption as a checkable
   claim, check it against the code/data, and record what was actually found — including
   a partial or negative result.
5. If the bounded search finds nothing, say so and re-route: an unanswered row-2 entry
   usually becomes an interview or brainstorm entry, not a dead end.

## What to write back into the ledger

`status: resolved` with a `resolution:` naming the evidence site ("vendor/rate-limiter's
backoff loop, read 2026-07-23: exponential with jitter, cap 30s — reimplement these
semantics"), or a re-route (update `technique` and keep `investigating`), or — for a
verified/falsified assumption — the finding itself. Never a bare "done".
