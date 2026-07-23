# Interview — when the user holds the answer

The route for `known-unknown` entries whose answer lives in the user's head: preferences,
priorities, context about their team or product, decisions only they can make.

## How to run it

1. **One question at a time.** Batched questions get shallow answers; a single question
   gets a considered one. Use AskUserQuestion where available.
2. **Priority order: answers that would change the architecture first.** Ask yourself
   which open entry, answered differently, forces the largest redesign — that entry's
   question goes first. Cosmetic preferences go last or go unasked.
3. Anchor each question to its ledger entry (name the `UNK-NNN` id) so the user can see
   why it is being asked.
4. Push once past the first answer when it is vague — "whichever is best" is not an
   answer; offer 2–3 concrete options with their trade-offs and ask the user to pick.
5. Stop when the remaining open entries no longer justify the user's attention: when an
   answer would not change what gets built, record the default being assumed as an
   `assumption` entry instead of asking.

## What to write back into the ledger

For each entry asked about: `status: resolved`, `resolution:` recording the decision AND
its ground in one or two sentences ("Sliding refresh; user prioritized session
continuity over strict expiry"). If the user explicitly declines to decide, route the
entry onward (brainstorm-prototype for an open decision) or record `accepted-risk` with
their consent — never leave it silently `investigating`.
