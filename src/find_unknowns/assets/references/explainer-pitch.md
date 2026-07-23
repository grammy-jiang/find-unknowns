# Explainer / pitch — post-phase optional deliverable

A phase-bound technique, not a quadrant route. It neither gates nor is gated by the
quiz: produce it on request, before or alongside the quiz, whenever the work needs
buy-in from people who were not in the room.

Why the ledger makes this cheap: reviewers arrive holding the same unknowns the user
started with, and experienced reviewers specifically look for evidence that the common
failure points were considered. The ledger already records both — what was unknown, what
was decided and on what ground, what deviated mid-flight, and what risk was accepted
with eyes open. An explainer built from it answers the reviewer's questions before they
are asked.

## How to run it

1. Input: the ledger, plus any artifacts the user names (a prototype, a diff, a plan).
2. Shape the story in ledger order, not code order:
   - what we did not know going in (the opening entries, by quadrant);
   - what we decided and why (resolutions, with their grounds — not just the verdicts);
   - what surprised us (deviated entries — deviations are the most credible part of the
     story, include them rather than polishing them away);
   - what we chose not to test and why that is safe enough (accepted-risk entries with
     their `risk:` rationale).
3. Output: ONE standalone document the user can drop into a review thread — it must read
   without the ledger, the conversation, or this skill installed.
4. Lead with whatever makes the result concrete fastest (a demo, a before/after, the
   headline decision); the unknowns story supports the ask, it is not the ask.

## What to write back into the ledger

Nothing. The explainer is derived output; the ledger stays the record. If a reviewer's
question exposes a genuinely new unknown, it enters the NEXT feature's ledger — a
`complete` ledger is frozen for entry corrections.
