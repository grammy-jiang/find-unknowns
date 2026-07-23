# Example session — a complete lifecycle, ending in the ledger below

Consult this before a session's first ledger write: it shows the full loop once, and the
embedded ledger at the bottom is a known-valid `unknowns-ledger-v1` document (it is this
package's golden test fixture — `find-unknowns validate` passes it with zero findings).

## How this session ran

**Pre.** Intake: the user was new to both the concept and the code, so the blindspot
pass swept wide. Its headline catch was UNK-001 — the "map" (a status doc) said the
feature didn't exist yet, but the territory (the code) already contained it end-to-end;
the real feature was wiring, not building. Routing then did its work: two entries went
to interviews (the user held the scope decision), one to a reference hunt that confirmed
the downstream consumer existed, and one assumption was cost-checked into
`accepted-risk` with its `risk:` rationale recorded. The pre-phase gate released only
when every architecture-impact entry reached a terminal status; the plant was offered
and declined-or-planted per the user's call.

**During.** Implementation hit one surprise: a control experiment silently didn't run
(an empty input fell back to a default with no warning). The deviation rail fired —
said in conversation, conservative fix taken, recorded as UNK-004 with
`quadrant: assumption` and no `technique`. A later correction widened that record via a
superseding entry (UNK-006) instead of editing UNK-004 in place: terminal entries are
never rewritten, corrections supersede.

**Post.** One entry was abandoned as out of scope (UNK-005 — `open` straight to
`abandoned`, never routed). The quiz was generated from the quizzable entries
(superseded UNK-004 and abandoned UNK-005 excluded); attempt 1 missed one question, so
the retake re-asked only that entry with a variant question — no explanations in
between — and passed. Scoring each attempt incremented `quiz_attempts`; the pass set
`status: complete` and `quiz_passed: true`, and the plant was cleaned.

## The resulting ledger (verbatim golden fixture)

```markdown
---
schema: unknowns-ledger-v1
feature: c3-hearst-is-a
created: 2026-07-23
updated: 2026-07-23
status: complete
quiz_passed: true
quiz_attempts: 2
---
## UNK-001
- quadrant: known-unknown
- impact: architecture
- status: resolved
- technique: interview
- statement: The map disagrees with the territory — the extractor module already exists end-to-end, so the real feature scope needs a decision only the user can make.
- resolution: Interview verdict, wire the existing seed function into the pipeline as deterministic input for the confirm step; source-prose corpus expansion explicitly deferred.

## UNK-002
- quadrant: known-unknown
- impact: architecture
- status: resolved
- technique: reference-hunt
- statement: The docstring hands candidate edges to an LLM-confirm step — does that step actually exist?
- resolution: Confirmed built and battle-tested, the step-7 doc records it producing confirmed clusters and a 24-edge graph on a real package; the seed's downstream consumer is real.

## UNK-003
- quadrant: assumption
- impact: local
- status: accepted-risk
- risk: Production-quality recall depends on the optional nlp extra (spaCy plus WordNet); the flat path is high-precision low-recall, accepted for now and monitored by the deviation rail.
- statement: The flat regex path's recall is sufficient beyond integration verification.

## UNK-004
- quadrant: assumption
- impact: architecture
- status: deviated
- statement: The plan assumed the sources flag exercised source prose on the test package.
- resolution: Reality forced a fix, the package had no source markdown and the function silently fell back to principle statements; conservative option taken, an explicit warning instead of the silent fallback.

## UNK-005
- quadrant: known-unknown
- impact: cosmetic
- status: abandoned
- statement: Benchmark spaCy-path yield against the flat path on factory data.

## UNK-006
- quadrant: assumption
- impact: architecture
- status: resolved
- supersedes: UNK-004
- statement: The deviation entry under-stated the fix's scope.
- resolution: Correction, the warning fix also sorted the sources glob for determinism; supersedes the original deviation record.

## Quiz — attempt 1
### Q1 [UNK-001]
What did the feature's scope turn out to be, and why that instead of the alternatives?
- answer: Wire the existing seed into the flow as deterministic confirm-step input; determinism and provenance beat the bigger corpus rework.
- verdict: correct
### Q2 [UNK-002]
What decides the fate of the seeded candidate edges downstream?
- answer: Some validator script rejects the bad ones.
- verdict: missed
### Q3 [UNK-003]
What risk was accepted about extraction recall, and what monitors it?
- answer: Flat-path recall is accepted as thin without the nlp extra; the deviation rail monitors it.
- verdict: correct

## Quiz — attempt 2
### Q1 [UNK-002]
Name the step that accepts or rejects seeded edges, and the evidence it exists.
- answer: The LLM-confirm step; the step-7 doc shows it ran on a real package and produced the confirmed graph.
- verdict: correct
```
