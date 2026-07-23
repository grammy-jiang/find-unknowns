# Source reference

This skill's technique catalog is distilled from:

> Thariq [@trq212], **"A Field Guide to Fable: Finding Your Unknowns"**, 2026-07-04.
> https://x.com/trq212/article/2073100352921215386

Rights status: **distillation-only** (copyrighted essay, no open license). This package
paraphrases and restructures; it contains no verbatim passages, and this file
deliberately does NOT include the essay's text. A maintainer's personal reading copy
belongs in gitignored `notes/`, not in the repo; if the author grants written
permission, this file may be revised to carry the full text with a license note.

This is a human/legal-facing citation file — the skill does not load it at runtime (the
one named exemption to the reference-link rule).

## Distilled outline of the essay (structure, not text)

- **Frame:** the map (prompt/context) is not the territory (codebase, real constraints);
  the gap between them is made of unknowns, and with strong models the user's ability to
  find and resolve those unknowns becomes the quality bottleneck.
- **Taxonomy:** known knowns (what the prompt says), known unknowns (questions you know
  to ask), unknown knowns (criteria you would recognize but cannot state), unknown
  unknowns (what you have not considered at all).
- **Failure symmetry:** over-specific instructions suppress warranted pivots; vague ones
  invite generic best-practice defaults — both stem from unaccounted-for unknowns.
- **Working stance:** give the model your starting point (experience, where your
  thinking stands) and use it as a thought partner to discover unknowns faster.
- **Pre-implementation techniques:** a blindspot pass (ask directly for your unknown
  unknowns), brainstorms and disposable prototypes (recognition beats articulation, and
  spec changes are cheap before code exists), interviews (one question at a time,
  architecture-changing answers first), references (existing code as the richest
  specification, portable across languages), and implementation plans that lead with the
  decisions most likely to change.
- **During implementation:** keep a running notes file of deviations — take the
  conservative option, log it, keep going.
- **Post-implementation:** package pitch/explainer artifacts for reviewers who start
  with your original unknowns; take a quiz on the change and merge only on a pass.
- **Worked example:** an end-to-end video-editing project in an unfamiliar domain,
  navigated by explainers, prototypes, and asking to be taught the domain's quality
  criteria rather than guessing at them.
- **Closing thesis:** every explainer, brainstorm, interview, prototype, and reference
  is a cheap way to find out what you didn't know before it gets expensive to fix.

Where this skill deliberately goes beyond the essay: the persistent per-feature ledger
that threads all three phases, the quadrant routing table, the deviation rail's plant,
and the quiz's anti-gaming/pass mechanics are this package's own design — grounded in
the essay's catalog but not claimed to be in it.
