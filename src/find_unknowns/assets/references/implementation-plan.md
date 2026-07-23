# Implementation plan — pre-gate supplementary technique

A phase-bound technique, not a quadrant route. It neither gates nor is gated by the
pre-phase gate: skipping it never blocks the go-ahead, and writing one never substitutes
for resolving architecture-impact entries. Reach for it when the feature is large enough
that implementation will make many small decisions the ledger never captured — a plan is
where those get surfaced while they are still cheap to change.

## The ordering principle

Lead with the decisions the user is most likely to want to change: data-model shapes,
type interfaces, anything user-facing, anything a resolved ledger entry only settled at
the level of direction. Bury the mechanical work (renames, plumbing, refactors the
design forces) at the bottom — reviewing it costs attention and rarely changes anything.
A plan ordered mechanically (file by file, step by step) hides the two decisions that
matter under twenty that don't.

## How to run it

1. Draft the plan AFTER routing has resolved or parked every entry — the plan implements
   decisions, it does not make them.
2. Anchor plan items to ledger entries by id where they descend from one ("token refresh
   per UNK-001's resolution"); an implementation step no entry explains is worth a second
   look — it may be a blindspot the pass missed, and can still become a late entry.
3. Ask the user to react to the top of the plan only; say explicitly that the bottom is
   mechanical and reviewing it is optional.
4. Plan disagreements that change a recorded resolution go through the correction
   protocol (a superseding entry — see references/ledger-contract.md), never a silent
   plan edit.

## What to write back into the ledger

Nothing is required. Optionally add a `note:` bullet to entries whose resolution the
plan elaborated ("plan section 2 details the migration order"). If drafting the plan
surfaces a NEW unknown, that is the blindspot pass working late — add the entry through
the normal routing flow.
