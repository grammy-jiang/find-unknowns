"""Installer behavior — ported expectations from the blueprint architecture.

Every test uses an isolated tmp root+home; none touches the real filesystem outside
tmp_path. The "never write through a pre-existing symlink" pin matters most: writing
through a link would edit the packaged asset itself.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from find_unknowns.installer import (
    MANAGED_FILES,
    OUTCOMES,
    detect_platforms,
    install,
    install_state,
    packaged_content,
    skill_dir,
    status,
    uninstall,
)
from find_unknowns.installer import (
    PLATFORMS as P,
)


@pytest.fixture()
def root(tmp_path: Path) -> Path:
    (tmp_path / "root").mkdir()
    return tmp_path / "root"


@pytest.fixture()
def home(tmp_path: Path) -> Path:
    (tmp_path / "home").mkdir()
    return tmp_path / "home"


def test_install_symlinks_by_default_and_verifies(root, home):
    a = install("claude", "project", root, home)
    assert a.outcome == "installed"
    assert "symlinked" in a.detail and "verified" in a.detail
    target = skill_dir(P["claude"], "project", root, home)
    assert install_state(target) == "up-to-date"
    assert (target / "SKILL.md").is_symlink()


def test_install_copy_mode_writes_real_files(root, home):
    a = install("claude", "project", root, home, copy=True)
    assert a.outcome == "installed"
    target = skill_dir(P["claude"], "project", root, home)
    for rel in MANAGED_FILES:
        assert (target / rel).is_file()
        assert not (target / rel).is_symlink()
        assert (target / rel).read_bytes() == packaged_content(rel)


def test_install_is_idempotent(root, home):
    install("claude", "project", root, home)
    a = install("claude", "project", root, home)
    assert a.outcome == "up-to-date"


def test_local_edit_blocks_without_force_then_force_overwrites(root, home):
    install("claude", "project", root, home, copy=True)
    target = skill_dir(P["claude"], "project", root, home)
    (target / "SKILL.md").write_text("locally modified\n", encoding="utf-8")
    a = install("claude", "project", root, home, copy=True)
    assert a.outcome == "blocked"
    assert "SKILL.md" in a.detail
    a = install("claude", "project", root, home, copy=True, force=True)
    assert a.outcome == "installed"
    assert (target / "SKILL.md").read_bytes() == packaged_content("SKILL.md")


def test_install_never_writes_through_preexisting_symlink(root, home, tmp_path):
    # A stale symlink at a managed path must be unlinked, not written through —
    # writing through it would modify whatever the link points at.
    decoy = tmp_path / "decoy.md"
    decoy.write_text("decoy content\n", encoding="utf-8")
    target = skill_dir(P["claude"], "project", root, home)
    (target / "SKILL.md").parent.mkdir(parents=True)
    (target / "SKILL.md").symlink_to(decoy)
    a = install("claude", "project", root, home, copy=True, force=True)
    assert a.outcome == "installed"
    assert decoy.read_text(encoding="utf-8") == "decoy content\n"
    assert not (target / "SKILL.md").is_symlink()


def test_dry_run_writes_nothing(root, home):
    a = install("claude", "project", root, home, dry_run=True)
    assert a.outcome == "would-install"
    target = skill_dir(P["claude"], "project", root, home)
    assert install_state(target) == "not-installed"


def test_uninstall_removes_files_and_empty_dirs(root, home):
    install("claude", "project", root, home)
    a = uninstall("claude", "project", root, home)
    assert a.outcome == "removed"
    target = skill_dir(P["claude"], "project", root, home)
    assert not target.exists()
    assert uninstall("claude", "project", root, home).outcome == "not-installed"


def test_uninstall_sweeps_dangling_symlinks(root, home, tmp_path):
    ghost = tmp_path / "ghost.md"
    ghost.write_text("x\n", encoding="utf-8")
    target = skill_dir(P["claude"], "project", root, home)
    (target / "SKILL.md").parent.mkdir(parents=True)
    (target / "SKILL.md").symlink_to(ghost)
    ghost.unlink()  # now dangling; install_state reads it as missing
    a = uninstall("claude", "project", root, home)
    assert a.outcome == "removed"
    assert not (target / "SKILL.md").is_symlink()


def test_copilot_project_skipped_when_claude_covers_it(root, home):
    install("claude", "project", root, home)
    a = install("copilot", "project", root, home)
    assert a.outcome == "skipped"
    assert ".claude/skills" in a.detail


def test_copilot_has_no_user_scope(root, home):
    with pytest.raises(ValueError, match="no documented user-scope"):
        install("copilot", "user", root, home)


def test_unknown_platform_raises_value_error(root, home):
    with pytest.raises(ValueError, match="unknown platform"):
        install("cursor", "project", root, home)


def test_status_covers_every_platform_scope(root, home):
    actions = status(root, home)
    seen = {(a.platform, a.scope) for a in actions}
    expected = {
        (key, scope)
        for key, platform in P.items()
        for scope in ("project", "user")
        if not (scope == "user" and platform.user_dir is None)
    }
    assert seen == expected
    assert all(a.outcome in OUTCOMES for a in actions)


def test_detect_platforms_reports_evidence_or_none(home):
    evidence = detect_platforms(home, path_env="")  # empty PATH: no CLIs found
    assert set(evidence) == set(P)
    assert all(v is None for v in evidence.values())
    (home / ".claude").mkdir()
    evidence = detect_platforms(home, path_env="")
    assert evidence["claude"] and ".claude" in evidence["claude"]
