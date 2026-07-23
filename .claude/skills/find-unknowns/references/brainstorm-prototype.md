# Brainstorm & prototype — when the answer must be created or recognized

The route for open decisions nobody holds yet (routing row 3), for "I'll recognize it
when I see it" criteria with no exemplar (row 5), and for assumptions testable only by
building something (assumption procedure spike).

Why this is worth doing before implementation: criteria the user can only recognize, not
articulate, are cheap to discover against a disposable variation and expensive to
discover against a half-built feature — small spec changes can force disproportionate
implementation changes, and reverting built work is harder than discarding a sketch.

## How to run it

1. **Scope the artifact to the question.** The prototype exists to resolve one ledger
   entry — a static mock, a single throwaway file, a hardcoded variation. No backend
   wiring, no state management, nothing the entry does not need.
2. For **recognition entries** (row 5): produce genuinely different variations — a few
   distinct directions, not one direction in three shades — and ask the user to react.
   The reaction IS the data; capture what they responded to, not just which one won.
3. For **open decisions** (row 3): enumerate options wide-to-narrow with honest
   trade-offs, recommend one, and let the user pick or redirect. Range matters —
   cheapest-to-most-ambitious beats three variants of the same idea.
4. For **spikes**: build the smallest thing that makes the assumption's truth observable,
   observe it, record the observation.
5. **Everything built here is disposable by default.** Say so; a prototype promoted into
   production code is a new decision the user makes explicitly.

## What to write back into the ledger

`status: resolved` with a `resolution:` that captures the decision AND the recognized
criteria ("Variant B — user reacted to the two-panel layout and instant preview; density
over whitespace"), or the spike's observation for an assumption. If the user reacts to
none of the variations, record what was learned and re-route — often to an interview
with sharper options.
