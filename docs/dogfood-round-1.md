# Dogfood round 1 — evidence log

Design step 2: run the packaged skill end-to-end (pre → during → quiz) on one real
subagent-factory feature. Every behavioral failure below must become a rail, scenario,
or grader note — never a prose spot-fix (Constraint 4).

Setup: installed via the real user path — wheel → `uv tool install` → `find-unknowns
setup claude --root /home/user/subagent-factory` → 10 symlinked, read back and verified.

## Findings

### F1 — ledger contract assumes the host project gitignores `notes/`

- **Observed:** subagent-factory has no `notes/` entry in its `.gitignore` (and no
  `notes/` directory). The contract says ledgers are "gitignored by default — private
  working notes," but that is only true in the find-unknowns repo itself; the skill
  never checks or establishes the convention in a host project. First ledger write
  would create an untracked, committable file containing private working notes.
- **Class:** missing rail (the plant already solves this exact problem for
  `CLAUDE.local.md` — check, warn, offer to add the ignore line; the ledger path has no
  equivalent).
- **Durable fix:** pre-phase rail in SKILL.md — before the first ledger write in a
  project, check `.gitignore` for `notes/` (same Read-based check and limitation note
  as the plant's), and offer to add it; plus an eval-cell assertion (fixture without the
  ignore entry → grader checks the offer happens before the write).
- **Interim behavior this round:** surfaced to the user at intake; improvised the
  plant's consent pattern.

### F2 — deference defeats the quiz's precondition (THE finding of the round)

- **Observed:** the user answered every pre-phase decision by picking the recommended
  option, then honestly declared at quiz time: "I can't answer these, I just picked the
  recommended options." Attempt 1 scored 4/4 missed. The instrument WORKED — it caught
  exactly the understanding gap it exists to catch — but the skill let the gap build
  silently through the whole pre phase.
- **Class:** missing rail. The skill's interview/gates happily accept
  recommendation-following all the way to implementation; nothing notices the deference
  pattern or warns that the quiz will be unpassable.
- **Durable fix:** a deference rail in SKILL.md — when the user has accepted
  recommendations for every architecture-impact decision, say so at the pre-phase gate
  ("you have deferred every decision; the quiz will test understanding you haven't
  built — want a 2-minute walkthrough now?"); plus an eval scenario with an
  always-accept persona, grading that the flag fires before go-ahead.

### F3 — no path back to a pass after a full reveal

- **Observed (by construction, from F2):** if the agent now teaches the four answers,
  every entry becomes `passed-after-reveal`-tainted → fully-revealed closure
  (`quiz_passed: false`) is the ONLY reachable terminal state; the hard 3-attempt cap +
  frozen-complete rule leave no legitimate later re-verification. Learning-then-proving
  is impossible within one ledger once everything is revealed.
- **Mitigation that IS in-spec:** the user can self-study the ledger file itself (the
  resolutions are the recorded artifact — reading it is the flight recorder working, not
  gaming; "reveal" is defined as the AGENT restating in-conversation), then take a
  variant retake cleanly. Offered in round 1; the user chose teach-then-close instead,
  so the self-study path remains unexercised.
- **Durable fix:** references/quiz.md should name the self-study path explicitly, and
  the design should decide whether a post-reveal "re-verification ledger" (new attempt
  cycle after demonstrated re-learning) is wanted — currently it is not, silently.

### F4 (minor) — `quiz_attempts` increment timing under-specified

- The contract says attempts increment "on pass" and on retakes, but not whether
  generation or scoring consumes an attempt. Round 1 chose: scoring does. One sentence
  in ledger-contract.md + a validator cross-check would pin it.

### Round-1 note — deviation rail never fired

- Implementation completed with zero forced deviations, so the rail's append path went
  unexercised this round. Not a failure — but it means round 1 provides NO evidence on
  the rail's soul-of-the-product behavior; the fixture-seeded eval cells remain the only
  planned proof. Recorded so the dogfood criterion isn't over-claimed.

## Round-1 outcome (end-to-end: pre -> during -> quiz -> closure)

- **Pre:** intake calibrated (user new to both concept and code); blindspot pass yielded
  6 entries; 3 resolved by reference-hunt in-session, 2 by interview, 1 by prototype.
  The headline territory fact: the "C3 optional" map line was stale — the extractor
  existed end-to-end; the real feature was the unwired seed artifact.
- **During:** feature shipped (subagent-factory `358e5f5`) — seed artifact wiring +
  silent-fallback footgun fix + 3 tests + doc corrections. Zero forced deviations
  (rail unexercised — see note above).
- **Quiz:** attempt 1 scored 4/4 missed on the user's honest declaration of deference
  (F2). User chose teaching over self-study retake; fully-revealed closure recorded:
  ledger `complete`, `quiz_passed: false`, warning naming all four revealed entries.
  Merge go-ahead deliberately NOT issued (advisory; branch merge is the user's call).
- **Design-criterion readout:** the dogfood success criterion ("ledger catches >=1
  unknown that would otherwise surface late") is MET — UNK-001 alone (stale map, wrong
  feature scope) would have cost the whole feature being built wrong. The deviation
  criterion is UNTESTED (no deviation occurred). The quiz criterion produced its most
  valuable possible outcome: a true negative, honestly recorded.
- **Fix queue for the skill (from F1-F4):** notes/-gitignore rail; deference rail +
  always-accept eval persona; self-study path named in quiz.md + post-reveal
  re-verification decision; quiz_attempts timing pinned in ledger-contract.md.
