# The plant — during-phase persistence (Claude Code)

This file is the authoritative source for plant mechanics. The plant is a delimited
managed block written into `CLAUDE.local.md` so the deviation rail binds future sessions
**where this skill is never invoked**. That is its entire point — and it is the one
deliberate, user-consented exception to this skill's manual-only invocation policy.

## Consent and preconditions (in order)

1. Offer the plant at pre-phase go-ahead. **Never write it without an explicit yes in
   this session.**
2. **Verify `CLAUDE.local.md` is git-ignored** before writing: Read the repo's
   `.gitignore` and look for a matching line. Known limitation: nested `.gitignore`s and
   global excludes are not visible to this check — say so if it matters. If no matching
   line exists, warn the user and offer to add one via Edit first; an accidentally
   committed plant would bind collaborators who never consented, which is exactly what
   this design refuses to do.
3. If the user declines the plant: the deviation rail binds only sessions where this
   skill is invoked. Say that plainly, once.

## The managed block

Write exactly one block, shaped like this (ledger list varies):

```text
<!-- find-unknowns:BEGIN schema=unknowns-ledger-v1 -->
Unknowns ledger(s) for in-flight features (managed by find-unknowns; do not hand-edit):
- notes/unknowns/auth-provider-oauth-20260723.md
Before ending any significant implementation step, ask: did anything just diverge from the
plan? On any forced deviation: (1) say so in the conversation explicitly, (2) take the
conservative option, (3) append a `deviated` entry to the matching ledger, (4) keep going.
When more than one ledger is listed, append to the one whose feature matches what you are
currently implementing; if unclear, ask before appending. Before writing: re-read the
ledger file and use the next ascending three-digit id — never compute the id from memory.
After writing: re-read your entry and confirm it matches the shape below (bare values, all
five bullets). Entry format:

## UNK-<next-id>
- quadrant: assumption
- impact: <architecture | local | cosmetic — architecture when unsure>
- status: deviated
- statement: <what the plan assumed>
- resolution: <what reality forced instead, and the conservative option taken>

If a listed ledger path does not exist on this machine, that line is inert.
<!-- find-unknowns:END -->
```

The block deliberately embeds the write discipline and the entry template: a plant-only
session never loads references/ledger-contract.md, so everything it needs must be in the
planted text itself.

## Target

`CLAUDE.local.md` — never the committed `CLAUDE.md`, so the plant cannot bind
collaborators or CI (whose machines lack the gitignored ledger anyway). Note:
`CLAUDE.local.md` is deprecated-but-honored in current Claude Code memory docs; if it
stops loading, the fallback is an import line in a memory file pointing at an
uncommitted planted file (e.g. `@notes/unknowns/plant.md`).

## Hygiene

- The block is **updated in place** — never duplicated — and lists only `active`
  ledgers.
- Quiz-pass and abandon flows rewrite the block; the post flow's last act is plant
  cleanup: remove the block entirely when no active ledgers remain.
- The `BEGIN` marker carries the schema version. On every invocation, compare it to this
  skill's schema version; on mismatch, offer to rewrite the block (stale per-user plants
  after a schema bump are otherwise undetectable).

## Corruption recovery

On any malformed marker state — orphaned `BEGIN`, missing `END`, duplicate pairs (an
interrupted write, a manual edit) — treat the block as corrupted:

1. Do NOT guess which block or fragment to edit.
2. Show the user what was found — name the defect concretely in conversation ("orphaned
   `BEGIN`, no `END` marker", "duplicate blocks") *before* rebuilding, so the user can
   tell what, if anything, was lost.
3. Rebuild one clean block whose ledger list is **re-derived by scanning
   `notes/unknowns/*.md` for `status: active`** — never salvaged from the corrupted
   remnants.

Concurrent sessions writing the plant are unsupported in v1.

## Tool grant and boundary honesty

The plant's own write happens in-invocation under this skill's `allowed-tools`
(Write/Edit; path-scoped to `CLAUDE.local.md` where the runtime supports that). But
`allowed-tools` governs only this skill's own invocations: the planted block's
cross-session ledger writes run under whatever ordinary permissions the later,
un-invoked session already has — a boundary this skill can neither extend nor restrict.
