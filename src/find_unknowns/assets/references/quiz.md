# The quiz — post-phase mechanics

This file is the authoritative source for all quiz mechanics: the two gates, the
confirmation pass, generation, the anti-gaming ordering, retakes, and the pass
computation. SKILL.md carries only the gate conditions; if any summary elsewhere drifts
from this file, this file governs.

Honesty scope, told to the user up front: the quiz verifies understanding of the
ledger's **recorded decisions** — not of the shipped diff (diff-aware questions are
future work). It is a self-check instrument, not enforcement; a user answering in bad
faith defeats it, and that is an accepted property, not a bug.

## Gate (a): generation

Quiz generation is **deferred while any `open` or `investigating` entry exists** — ask
the user to triage each to `resolved`, `accepted-risk`, or `abandoned` first. The user
may insist; then generate anyway, but record a warning in the quiz section naming the
untriaged entries, and repeat it in conversation. **Recorded-warning format (pinned):**
every warning — insist-override, attempts-exhausted, fully-revealed — is a
`- warning: <text>` bullet directly under the `## Quiz — attempt N` header; it is the
only legal section-level bullet (question text and other prose are free).

## Pre-quiz confirmation pass

Before generating questions, re-check each quizzable entry's judging basis
(`resolution:` or `risk:`) against current file state where that is possible with
Read/Grep. Any entry that cannot be confirmed is flagged in conversation **by entry id
plus a generic staleness caveat only** — for example: "UNK-003's recorded resolution
could not be confirmed against current file state; it will be quizzed as a recorded
decision." **The flag must never restate or paraphrase the resolution/risk text** — the
anti-gaming ordering below applies to this pass exactly as it applies to everything else
before Q1.

## Generation

- Sources: `resolved`, `deviated`, and `accepted-risk` entries. Excluded: `abandoned`
  entries and any entry that has been superseded.
- Ask at least one question per `deviated` entry — deviations are where understanding
  most often lags.
- Append to the ledger as a `## Quiz — attempt N` section. Each question is a
  `### Qn [UNK-NNN]` subsection carrying, once answered:
  - `- answer:` the user's answer, summarized faithfully
  - `- verdict: correct | missed | passed-after-reveal`
- **Render each question to the user in conversation with its literal
  `### Qn [UNK-NNN]` header** — the header is the anchor future graders parse; prose-only
  questions are a contract violation.

## Anti-gaming ordering

Questions are generated and answered **before** the agent restates any judging-basis
text in conversation. Do not summarize resolutions, walk through decisions, or "recap
the feature" between invoking the quiz and scoring the final answer of an attempt.

## Grading

Judge the user's answer against the entry's recorded judging basis. Calibration
examples:

- **correct** — Q: "What token-refresh strategy did we settle on, and why?" A: "Sliding
  refresh — it fit the session model we already had." The answer names the decision and
  its ground; wording need not match the ledger.
- **missed** — same question, A: "We refresh tokens when they expire." The answer
  describes generic behavior, not the recorded decision.
- **borderline → judged missed** — A: "Some kind of refresh thing? You handled it."
  Deference is not understanding; when genuinely unsure whether the user understood,
  score `missed` — a false `missed` costs a retake, a false `correct` defeats the
  instrument.

## Retake flow (reveal-safe)

1. A missed attempt triggers a **retake first**: re-ask only the previously-missed
  entries with **variant questions** (not repeats), with **no explanations in between**.
2. Only after the retake is scored does the agent explain the remaining misses.
3. Any entry re-asked **after** its answer was revealed scores `passed-after-reveal`.
4. **Cap: 3 attempts per ledger — a hard ceiling.** No `## Quiz — attempt 4` section is
   ever written, and no further quiz section after a fully-revealed closure either.
   Scoring consumes an attempt; generation alone does not increment `quiz_attempts`.

**Self-study is legitimate — offer it on a missed attempt.** "Reveal" means the AGENT
restating judging-basis content in-conversation; the user reading the ledger file itself
is the flight recorder working as intended, not gaming. On a miss, explicitly offer:
"read the ledger (its resolutions are the record), then take a variant retake" — that
path can still reach a clean pass. Warn before teaching instead: once every entry's
answer has been revealed in-conversation, NO pass path remains in this ledger (a
deliberate property; a post-reveal re-verification mechanism is documented future work,
not a silent gap).

## Pass computation — the single authoritative rule

`quiz_passed: true` requires ALL of:

1. zero `open`/`investigating` entries remain;
2. at least one non-revealed question exists;
3. every non-revealed question's **latest recorded verdict** is `correct` (an early miss
   cured by a passing retake does not block).

**Closure precedence:** when attempt 3 concludes, evaluate the pass rule once more;
attempts-exhausted closure applies only if that evaluation is false.

**Failure closures** (both: ledger `status: complete`, `quiz_passed: false`, a recorded
warning in the quiz section):
- *attempts-exhausted* — the cap was reached without a pass;
- *fully-revealed* — zero non-revealed quizzable questions remain (possible under the
  cap).

**Partial reveals are tolerated by design, never silently:** a pass with
`passed-after-reveal` entries is legal, but the pass record in the ledger AND the
in-conversation merge go-ahead MUST name the revealed entries — "passed; UNK-003 was
answered after reveal" — so the caveat travels with the verdict.

**On pass:** set `quiz_passed: true`, ledger `status: complete`, increment
`quiz_attempts`, clean the plant (see references/plant.md).

## Gate (b): merge go-ahead

The merge go-ahead statement is withheld until `quiz_passed: true`. It never blocks the
user — they can merge whenever they want — but the skill does not say "good to merge"
before a pass, and when it does, it names any `passed-after-reveal` entries.

## Retake eligibility on a complete ledger (owned here)

- `quiz_passed: true` AND `quiz_attempts < 3` → offer a voluntary re-verification
  retake: recorded, attempts increment, and an earned pass is **never demoted** by a
  later failed retake — verdicts are recorded, history stands.
- At the cap (including a pass earned on attempt 3), or closed with
  `quiz_passed: false` by either failure closure → decline; the recorded result stands;
  point to the recorded warning.
