# The unknowns ledger — full contract (`unknowns-ledger-v1`)

This file is the authoritative source for the ledger format. It is enforced twice: in
the live path by discipline (the Read-back self-check below), and statically by the
packaged `unknowns-ledger-v1.schema.json` + `validator.py` (`find-unknowns validate
<ledger.md>` — run in CI/evals, never in-session), which must match this file exactly
(lockstep-edit rule).

## Location, naming, discovery

- One ledger per feature: `notes/unknowns/<feature-slug>-YYYYMMDD.md`. Ledgers are
  private working notes; committing one is a deliberate per-user choice — so `notes/`
  must be gitignored, and **the skill establishes that convention rather than assuming
  it**: before a project's first ledger write, Read the repo's `.gitignore` for a
  `notes/` line (limitation: nested `.gitignore`s and global excludes are invisible to
  this check — say so if it matters) and, if absent, warn and offer to add it.
- The filename's feature slug MUST equal the frontmatter `feature` value.
- Same-day recreate collision: refuse to overwrite; suffix the date segment —
  `<feature-slug>-YYYYMMDD-b.md`, then `-c`, and so on. When comparing filename to
  `feature`, strip the optional `-[b-z]` suffix first.
- Discovery: match the conversation's feature against ledgers' `feature` slugs — active
  ledgers normally; active then complete when dispatching `quiz`. **Silent resume only on
  a normalization-exact slug match** (normalize case, hyphens/underscores, whitespace —
  nothing fuzzier is ever "close enough"). Anything else: list candidates, ask the user.
  Never silently create a new ledger while an active one exists; never silently pick
  among multiple matching complete ledgers under `quiz`.

## Write discipline (the live path)

1. **Before computing a next entry id: re-read the ledger file.** In-context memory of a
   file is not the file.
2. **After every write: re-read what you wrote** and check it against this contract —
   header shape, bare values, required fields for the entry's status, ascending unique
   ids, frontmatter `updated` refreshed.
3. A failed check is **stop-and-repair**: fix the ledger before doing anything else, and
   tell the user what was repaired.

The packaged validator (later milestone) runs in CI/pre-commit/evals only — it is never
executed in-session; the Read-back above is the in-session discipline.

## Frontmatter

```yaml
---
schema: unknowns-ledger-v1
feature: auth-provider-oauth      # must equal the filename slug
created: 2026-07-23
updated: 2026-07-23               # refreshed by the skill on every write
status: active                    # active | complete | abandoned
quiz_passed: false
quiz_attempts: 0
---
```

## Entries

- Entries are body sections whose header matches exactly `^## UNK-\d{3}$` (three digits,
  ascending, unique).
- The only other legal `##` header is `^## Quiz — attempt \d+$` (em-dash, not hyphen).
  Anything else — including near-misses like `## UNK-01` or `## Quiz - attempt 1` — is a
  contract violation to repair on sight.
- Each entry is a bullet list of `- key: value` lines with **bare values only** — no
  inline `#` comments (the parser will not strip them; a comment becomes part of the
  value).

### Field rules

| Field | Rule |
|---|---|
| `quadrant` | required; `known-unknown \| unknown-known \| assumption`; MUST be `assumption` on `deviated` entries |
| `impact` | required; `architecture \| local \| cosmetic` |
| `status` | required; `open \| investigating \| resolved \| deviated \| accepted-risk \| abandoned` |
| `technique` | `interview \| reference-hunt \| brainstorm-prototype`; MUST be absent on `accepted-risk` and `deviated`; MAY be absent on `abandoned`, not-yet-routed `open` entries, and superseding corrections (a correction is not routed) |
| `statement` | required; the unknown/assumption in one sentence |
| `resolution` | required on `resolved` and `deviated` (their quiz-judging basis) |
| `risk` | required on `accepted-risk` (its quiz-judging basis) |
| `supersedes` | optional; `UNK-NNN`; marks this entry as replacing a terminal one |
| `note` | optional freeform bullet, legal on any status (the degradation rail writes it) |

### State machine — all four entry paths

- (a) **routed:** `open` → (routing sets `investigating`) → `resolved` / `accepted-risk`
  / `abandoned`. Transitioning to `accepted-risk` removes the `technique` field — the
  `risk:` rationale records how acceptance was reached.
- (b) **cost-check bypass:** `open` → `accepted-risk` directly (never `investigating`,
  never any `technique`).
- (c) **deviation:** entries are created directly as `deviated` by the deviation rail —
  never routed.
- (d) **early abandonment:** `open` → `abandoned` directly (never routed, no
  `technique`).

### Correction protocol (active ledgers only)

A correction records that an entry was **wrong when written**. If the record was right
and reality moved later (an API removed, a constraint surfaced), that is a deviation —
`status: deviated`, even when the user announces the change — not a correction; see
references/deviation-log.md, "Deviation vs correction".

Terminal entries (`resolved` / `deviated` / `accepted-risk` / `abandoned`) are never
edited in place. To reverse one, append a new entry carrying `supersedes: UNK-NNN`,
shaped as the copy-template pattern populated with the fields its own target status
requires (`resolution` or `risk`), and superseded entries are excluded from quiz
generation. `complete` and `abandoned` **ledgers** are frozen for entry corrections
(quiz sections and frontmatter sit outside that freeze — a voluntary retake touches no
`## UNK-` entry); corrections to a closed feature's decisions belong in the next
feature's ledger.

### Cross-field corollaries (for the future validator)

These follow from the quiz flow in references/quiz.md — restated for static checking:
`quiz_passed: true` ⇒ `quiz_attempts ≥ 1` ∧ at least one `## Quiz — attempt N` section ∧
ledger `status: complete` ∧ zero `open`/`investigating` entries.

**Attempt counting is pinned:** `quiz_attempts` counts SCORED attempts — scoring an
attempt increments it; generating questions alone does not. (A generated-but-unscored
`## Quiz — attempt N` section with `quiz_attempts` one lower is therefore a legal
in-progress state, not a violation.)

## Worked examples

**Reference only — annotated. NEVER copy this form; the comments would corrupt real
values:**

```markdown
## UNK-001
- quadrant: known-unknown    # known-unknown | unknown-known | assumption
- impact: architecture       # architecture | local | cosmetic
- status: resolved           # open | investigating | resolved | deviated | accepted-risk | abandoned
- technique: interview       # interview | reference-hunt | brainstorm-prototype (conditional)
- statement: Which token-refresh strategy fits our session model?
- resolution: Sliding refresh; decided in interview 2026-07-23.
```

**Copy template — the literal shape for real entries (bare values only):**

```markdown
## UNK-002
- quadrant: assumption
- impact: local
- status: open
- statement: Token clock-skew is negligible across our deployment targets.
```

A superseding entry follows the copy-template pattern — bare values, no comments —
populated with the field its own target status requires (`resolution` or `risk`), plus
one `- supersedes: UNK-NNN` bullet.
