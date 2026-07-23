# find-unknowns

A lifecycle **unknowns-ledger** skill for coding agents (Claude Code, OpenAI Codex,
GitHub Copilot). The gap between your prompt (the map) and the real codebase (the
territory) is made of unknowns — and they surface before, during, and after
implementation, not just at planning time. `/find-unknowns` keeps one ledger per
feature that every phase reads and writes:

- **Before:** a *blindspot pass* surfaces your unknown-unknowns; every entry is
  classified (`known-unknown` / `unknown-known` / `assumption`) and routed to the
  technique that resolves that kind of unknown — interview, reference hunt, or
  brainstorm/prototype. An advisory gate holds the go-ahead until
  architecture-impacting entries are resolved or explicitly risk-accepted.
- **During:** a *deviation rail* makes the agent surface plan deviations in
  conversation AND record them in the ledger — instead of silently pivoting. With your
  consent, a "plant" in `CLAUDE.local.md` keeps the rail binding in future sessions
  (Claude Code only).
- **After:** a *quiz* generated from the ledger checks that you actually understand the
  recorded decisions — resolutions, deviations, accepted risks — before you merge.

## Install

```bash
pipx install find-unknowns     # recommended (or: uv tool install find-unknowns / pip install find-unknowns)
find-unknowns setup            # auto-detects your agents; installs the skill for each
```

`setup` symlinks the packaged skill into each platform's skill directory (`--copy` for
real copies; `--scope user` for your home instead of the current project). `status`
shows what is installed where; `remove` reverts everything `setup` did. Upgrades:
`pipx upgrade find-unknowns` — symlinked installs pick the new version up immediately.

The skill is **manual-invocation-only**: it runs when you invoke `/find-unknowns`
(Claude Code / Copilot) or `$find-unknowns` (Codex), never proactively.

## Platform scope (v1)

| Platform | Pre (ledger + routing) | During (deviation rail persists) | Post (quiz) |
|---|---|---|---|
| Claude Code | yes | yes — via the consented `CLAUDE.local.md` plant | yes |
| OpenAI Codex | yes | invoked sessions only (no plant) | yes |
| GitHub Copilot | yes | invoked sessions only (no plant) | yes |

Honest notes, deliberately stated:

- The plant is written only with your explicit in-session consent, only to the
  uncommitted `CLAUDE.local.md` (never a shared file — teammates who didn't opt in are
  never bound), and only after checking it is gitignored.
- The skill's `allowed-tools` grant governs its own invocations only; ledger writes made
  by a later, un-invoked session under the plant run under that session's ordinary
  permissions — a boundary no skill can extend or restrict.
- The quiz verifies understanding of the ledger's *recorded decisions*, not the shipped
  diff, and it is a self-check instrument, not enforcement — answering in bad faith
  defeats it.
- The deviation rail's plant-persistence behavior is not yet covered by the behavioral
  eval matrix at this version; that coverage gates v1.0 (see `docs/design.md`).

## Development

```bash
uv sync            # installs dev group (pytest, pre-commit)
uv run pytest -q   # what CI runs
uvx pre-commit run --all-files --show-diff-on-failure
uv build           # what the release build job runs
```

The canonical skill source is `src/find_unknowns/assets/` — never edit an installed
copy (the default install is a symlink to the packaged asset). The full design record,
including the 8-round review trail that shaped it, lives in `docs/design.md`.

## Credits

The technique catalog is distilled (paraphrased, never quoted) from Thariq [@trq212],
"A Field Guide to Fable: Finding Your Unknowns", 2026-07-04,
https://x.com/trq212/article/2073100352921215386.

## License

MIT
