# Blindspot pass — surfacing unknown-unknowns

A populating technique: it fills the ledger at the start of the pre phase. It is never a
route for an existing entry — by definition, once an unknown is written down it is no
longer an unknown-unknown, so each surfaced item is immediately classified as a
`known-unknown` or an `assumption` and handled by the routing table from there.

When it earns its cost: the user is working in an unfamiliar part of the codebase, an
unfamiliar domain, or a task type they have not done before — the situations where they
do not yet know what questions to ask, what good looks like, or which potholes others
have already hit.

## How to run it

1. Ground in the intake: what the user said about their experience with the problem and
   the codebase decides where blindspots are likely.
2. Sweep systematically — search the codebase (Grep/Glob) and use domain knowledge; do
   not just introspect. Productive sweep lanes:
   - **History and conventions:** what has this codebase already decided about problems
     like this one (patterns, utilities, prior implementations, migration leftovers)?
   - **Domain concepts the user has not named:** terms of art in this problem space the
     intake never mentioned — if the user doesn't know the word, they can't ask the
     question.
   - **Hidden constraints:** performance envelopes, auth/permission boundaries, platform
     quirks, deployment realities that the naive design would trip on.
   - **Quality bar:** what does "good" look like here, and would the user recognize it?
     If not, that itself is an entry.
   - **Failure memory:** what commonly goes wrong with this kind of change?
3. For each candidate blindspot, state it to the user in one sentence and classify it:
   something they realize they need to find out → `known-unknown`; something they were
   taking for granted → `assumption`; a "recognize it when I see it" criterion →
   `unknown-known`.
4. Do not pad the ledger. A sweep lane that turns up nothing real gets no entry; five
   sharp entries beat fifteen vague ones.

## What to write back into the ledger

One entry per surfaced item, via the copy template in references/ledger-contract.md:
`quadrant` as classified, `impact` judged honestly (`architecture` if the answer could
change the design), `status: open`, `statement` in the user's language. Then return to
SKILL.md's routing table.
