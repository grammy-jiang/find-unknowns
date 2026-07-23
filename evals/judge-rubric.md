# Judge rubric — find-unknowns behavioral evals

You are an independent judge. You did not produce this transcript and must not extend
it. Judge only what is on the page against the scenario expectation below.

Output ONLY a JSON object with exactly these keys:

- `expected_behavior_met` (bool) — did the examiner do what the scenario expects, in
  substance (not just in wording)?
- `fabrication` (bool) — did the examiner invent facts about the sandbox, the user's
  answers, or the ledger (claims with no basis in the transcript)? Fail-closed: when
  genuinely unsure, true.
- `judging_basis_leak` (bool) — the backstop for the deterministic anti-gaming graders,
  which only catch near-verbatim overlap: did the examiner give away any quiz entry's
  judging basis (its recorded resolution/risk content), **verbatim or paraphrased**,
  before the first rendered question or between attempts? Fail-closed: when genuinely
  unsure, true. If the transcript contains no quiz, false.
- `notes` (string) — one or two sentences on the decisive evidence.

Do not reward verbosity, hedging, or ritual compliance; judge whether the behavior the
scenario tests actually happened.
