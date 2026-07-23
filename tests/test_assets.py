"""Invariants of the shipped skill assets.

These pin the policies docs/design.md declares: manual-invocation-only encoded in two
places, the SKILL.md size ceiling, and the MANAGED_FILES tuple staying in lockstep with
the assets directory in both directions.
"""

from __future__ import annotations

import re
from pathlib import Path

from find_unknowns.installer import MANAGED_FILES, packaged_content

ASSETS = Path(__file__).resolve().parents[1] / "src" / "find_unknowns" / "assets"


def _skill_md() -> str:
    return (ASSETS / "SKILL.md").read_text(encoding="utf-8")


def test_skill_frontmatter_disables_model_invocation():
    frontmatter = _skill_md().split("---")[1]
    assert "disable-model-invocation: true" in frontmatter


def test_skill_frontmatter_allowed_tools_exact():
    frontmatter = _skill_md().split("---")[1]
    match = re.search(r"^allowed-tools: (.+)$", frontmatter, flags=re.MULTILINE)
    assert match, "allowed-tools line missing from SKILL.md frontmatter"
    tools = [t.strip() for t in match.group(1).split(",")]
    # The exact grant docs/design.md drafted — Bash is deliberately absent.
    assert tools == ["AskUserQuestion", "Read", "Grep", "Glob", "Write", "Edit"]


def test_codex_sidecar_disables_implicit_invocation():
    sidecar = (ASSETS / "agents" / "openai.yaml").read_text(encoding="utf-8")
    assert "allow_implicit_invocation: false" in sidecar


def test_codex_sidecar_is_a_managed_file():
    assert "agents/openai.yaml" in MANAGED_FILES


def test_skill_md_within_size_ceiling():
    # docs/design.md pins the router at <=500 lines and ~<=5k tokens (approximated
    # here as words * 1.35 — calibrated loose on purpose; do not tighten to equality).
    text = _skill_md()
    lines = text.count("\n") + 1
    approx_tokens = int(len(text.split()) * 1.35)
    assert lines <= 500, f"SKILL.md is {lines} lines (ceiling 500)"
    assert approx_tokens <= 5000, f"SKILL.md is ~{approx_tokens} tokens (ceiling 5000)"


def test_managed_files_all_exist_in_assets():
    for rel in MANAGED_FILES:
        assert (ASSETS / rel).is_file(), f"managed file missing from assets: {rel}"
        assert packaged_content(rel), f"managed file empty: {rel}"


def test_all_asset_files_are_managed():
    on_disk = {
        str(p.relative_to(ASSETS)).replace("\\", "/") for p in ASSETS.rglob("*") if p.is_file()
    }
    assert on_disk == set(MANAGED_FILES), (
        "assets/ and MANAGED_FILES disagree — the tuple is hand-enumerated; "
        f"unmanaged on disk: {sorted(on_disk - set(MANAGED_FILES))}; "
        f"managed but missing: {sorted(set(MANAGED_FILES) - on_disk)}"
    )


def test_skill_reference_links_resolve():
    # Every "— see references/<file>.md" pointer in SKILL.md must name a shipped file
    # (the design's link pattern is normative: an unreferenced bundled file never loads).
    for name in re.findall(r"see references/([\w-]+\.md)", _skill_md()):
        assert (ASSETS / "references" / name).is_file(), f"SKILL.md links missing reference: {name}"
