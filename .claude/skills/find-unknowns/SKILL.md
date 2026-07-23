---
name: find-unknowns
description: "Track and resolve a feature's unknowns across its whole lifecycle with a per-feature unknowns ledger. Use BEFORE implementing a feature (blindspot pass populates the ledger; entries are routed to resolution techniques), WHEN RESUMING a feature that has an active ledger, and AFTER implementation — run '/find-unknowns quiz' to verify understanding of the recorded decisions before merging. Not for general planning or spec writing, code review, or retrospectives without a ledger."
disable-model-invocation: true
allowed-tools: AskUserQuestion, Read, Grep, Glob, Write, Edit
---

# find-unknowns — a lifecycle unknowns ledger

The gap between what the user asked for (the map) and what the work actually requires
(the territory) is made of unknowns — and they surface before, during, and after
implementation, not just at planning time. This skill keeps one **unknowns ledger per
feature** that every phase reads and writes: a blindspot pass populates it, techniques
resolve its entries, a deviation rail appends to it mid-implementation, and a quiz
generated from it closes the loop before merging.

Credits: the technique catalog is distilled (paraphrased, never quoted) from Thariq
[@trq212], "A Field Guide to Fable: Finding Your Unknowns", 2026-07-04,
https://x.com/trq212/article/2073100352921215386.

## Dispatch — pick the phase first

Evaluate in order:

1. Invoked with the `quiz` argument → **post phase** — see references/quiz.md.
   Discovery widens for `quiz` only: newest *active* matching ledger, else newest
   *complete* matching ledger. Retake eligibility is owned by references/quiz.md; in
   summary: `quiz_passed: true` under the 3-attempt cap → offer a voluntary recorded
   retake; closed with `quiz_passed: false` (attempts-exhausted at the cap, or
   fully-revealed under it) → decline, point to the recorded warning.
   With no ledger of either status → explain that, and offer the pre phase.
2. No discoverable active ledger (none, or only `complete`/`abandoned`) → **pre phase**
   (below). Create a new ledger; on a same-day filename collision, refuse and suffix the
   date segment (`-b`, `-c`, …).
3. An active ledger exists → **during-resume**: review entry statuses, route still-open
   entries (routing table below), log any deviations discussed in this conversation, and
   offer the quiz gate if implementation is done.

**Ledger discovery is conservative by rule, not judgment:** silently resume only on a
normalization-exact `feature`-slug match (case, hyphen/underscore, whitespace — nothing
fuzzier). In every other situation where at least one ledger exists in the discovery set,
list the candidates and ask the user. Never silently create a new ledger while an active
one exists. Staleness is advisory: if the discovered active ledger's `updated` date is 14+
days old with open entries, suggest resolve-or-abandon before proceeding.

## The ledger — conventions that are not optional

Full contract, worked examples, and the copy template: — see references/ledger-contract.md.
The load-bearing rules also live here because every phase depends on them:

- One file per feature at `notes/unknowns/<feature-slug>-YYYYMMDD.md`; filename slug MUST
  equal frontmatter `feature`.
- Entries are `## UNK-NNN` sections (three digits, ascending) of bare-value bullets. No
  inline comments, ever.
- **Before computing a next entry id, re-read the ledger file — never trust in-context
  memory of it. After every write, re-read what you wrote and check it against the
  contract (Read-back self-check); a failed check is stop-and-repair, not a note.**
- Terminal entries are never edited in place; reversals add a `supersedes: UNK-NNN` entry.

## Pre phase

1. **Intake first.** Ask for the user's starting point: their experience with the problem
   and this part of the codebase, what they already know they don't know, and where they
   are in their thinking. This calibrates everything that follows — the same feature needs
   a different diagnostic for a newcomer than for the module's author.
2. Consult references/example-session.md if present (golden walkthrough; not yet authored
   in the walking skeleton).
3. **Blindspot pass** (— see references/blindspot-pass.md) populates the ledger with
   surfaced unknowns, each immediately classified as `known-unknown`, `unknown-known`, or
   `assumption`.
4. **Route each open entry** with the table below; run the routed techniques; record
   resolutions in the ledger.

**Pre-phase gate** (withholds the go-ahead-to-implement statement, never blocks the
user): held while any `impact: architecture` entry is `open` or `investigating` — each
must reach `resolved`, `accepted-risk`, or `abandoned` first. On go-ahead, offer the
plant (below).

## Routing

| # | Quadrant | Selector (decisive) | Technique |
|---|---|---|---|
| 1 | known-unknown | the user holds the answer | interview — see references/interview.md |
| 2 | known-unknown | the codebase/world holds the answer | reference-hunt — see references/reference-hunt.md |
| 3 | known-unknown | nobody holds it yet (open decision) | brainstorm-prototype — see references/brainstorm-prototype.md |
| 4 | unknown-known | an exemplar exists in reachable code/artifacts | reference-hunt |
| 5 | unknown-known | no exemplar — "I'll recognize it when I see it" | brainstorm-prototype (variations to react to) |

**Assumptions route through an ordered procedure — the order is the semantics:**

1. **Cost check first.** If testing the assumption now is too expensive (rule of thumb:
   it would take longer than the feature work it blocks, or needs resources out of reach
   this session), transition the entry to `accepted-risk`: record a `risk:` rationale, no
   technique, monitored by the deviation rail.
2. **Otherwise pick by test method:** testable against existing code/data →
   reference-hunt (verify); testable only by building something → brainstorm-prototype
   (spike).

**Grounding precondition:** before classifying "the codebase holds the answer" (row 2),
"an exemplar exists" (row 4), "testable against existing code" (assumption step 2), or a
cost-check "too expensive" verdict whose cheap alternative would be a search — actually
run a bounded Grep/Glob over the stated scope first. Never classify those selectors from
memory.

Routing an entry sets `status: investigating` until its technique concludes. The
blindspot pass is populating-only — never a route for an existing entry.
`implementation-plan` (pre-gate; supplementary — it neither gates nor is gated) and
`explainer-pitch` (post; optional deliverable) are deferred to a later milestone and not
part of the walking skeleton.

**Degradation rail:** if a routed reference file is absent (partial install), improvise
the technique inline and add a `note:` bullet to the entry saying so — never silently
skip.

## During phase — the deviation rail

During is a rail, not a mode (— see references/deviation-log.md). On any forced deviation
from the plan: **(1) say so in the conversation explicitly** — a file write alone is not
compliance; (2) take the conservative option; (3) append a `deviated` entry
(`quadrant: assumption`; `impact` = `architecture` when unsure — self-reported severity
under momentum skews low, so the default skews high; no `technique`); (4) keep going.

**The plant** makes this rail survive fresh sessions where the skill is never invoked
(— see references/plant.md for all mechanics). At pre-phase go-ahead: ask the user for
consent, verify `CLAUDE.local.md` is git-ignored, then write the managed block. If the
user declines, the rail binds only sessions where this skill is invoked — say so.

## Post phase — the quiz

Run via `/find-unknowns quiz`. Gate conditions (mechanics — see references/quiz.md):

- **Generation gate:** deferred while `open`/`investigating` entries exist — triage them
  first; the user can insist, and generation proceeds under a recorded warning naming the
  untriaged entries.
- **Merge gate:** the merge go-ahead statement is withheld until `quiz_passed: true`; if
  the pass includes `passed-after-reveal` entries, the go-ahead must name them.

Honesty scope, stated to the user when relevant: the quiz verifies understanding of the
ledger's *recorded decisions*, not the shipped diff; it is a self-check instrument, not
enforcement — answering in bad faith defeats it.
