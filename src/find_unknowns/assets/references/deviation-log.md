# Deviation log — the during-phase rail

Not a mode: a standing rule bound either by this skill being invoked in the session or
by the plant (references/plant.md). Its premise: however good the plan, implementation
meets territory the map missed — an edge case in the code, a constraint nobody surfaced.
When that forces a change of course, the failure mode to prevent is the **silent
pivot**: the agent quietly doing something different from what was agreed, discovered
only much later, if ever.

## The rail

Before ending any significant implementation step, ask: did anything just diverge from
the plan? On any forced deviation, in order:

1. **Say so in the conversation, explicitly.** A ledger write alone is not compliance —
   the user must be able to see the pivot in real time, in the turn where it happens.
2. **Take the conservative option** — the choice that preserves the most of the agreed
   plan's intent and is easiest to revisit. The deviation entry records the fork; it does
   not license a redesign.
3. **Append a `deviated` entry** to the matching ledger (write discipline and template:
   references/ledger-contract.md; a plant-bound session uses the template embedded in the
   planted block):
   - `quadrant: assumption` — a deviation is a broken implicit assumption;
   - `impact:` your honest judgment, **`architecture` when unsure** — self-reported
     severity under momentum skews low, so the default skews high;
   - `status: deviated`; no `technique`;
   - `statement:` what the plan assumed; `resolution:` what reality forced instead, and
     the conservative option taken.
4. **Keep going.** The rail exists so deviations are visible and recorded, not so work
   stops.

When more than one active ledger exists, append to the one whose feature matches the
work at hand; if unclear, ask before appending.

If a previously `accepted-risk` entry's risk is what materialized, still create a new
`deviated` entry (v1 records them as separate entries; a back-reference link is
documented future work) — and say in conversation which accepted risk just came due.

## Deviation vs correction

Route by **when reality diverged from the record**, not by who noticed or how politely:

- The recorded resolution was **right when written, and reality moved later** — an API
  removed, a dependency dropped, a constraint surfaced → `status: deviated`, via the
  rail above. This holds even when the user announces the change and approves the new
  direction in conversation; visibility does not reclassify it.
- The recorded content was **already wrong at write time** — a misheard decision, a
  wrong fact → the correction protocol: a new entry with `supersedes: UNK-NNN`
  (references/ledger-contract.md), not a `deviated` status.

Replacing an invalidated decision with a fresh `resolved` entry hides the fork: the
`deviated` entry is what records that plan and build diverged, and it is what the
post-phase quiz probes hardest.

## What the quiz does with these

Every `deviated` entry gets at least one quiz question (references/quiz.md) — deviations
are where the user's mental model most often lags the recorded reality. Write the
`resolution:` with that in mind: it is the judging basis a future answer is graded
against.
