"""CLI surface — return codes, target validation, and the outcome-mark contract."""

from __future__ import annotations

from pathlib import Path

import pytest

from find_unknowns.cli import _OUTCOME_MARKS, main
from find_unknowns.installer import OUTCOMES, PLATFORMS, skill_dir


def test_version_flag_exits_zero(capsys):
    with pytest.raises(SystemExit) as e:
        main(["--version"])
    assert e.value.code == 0
    assert "find-unknowns" in capsys.readouterr().out


def test_setup_all_dry_run_and_status_and_remove(tmp_path: Path, capsys):
    root = tmp_path / "proj"
    root.mkdir()
    assert main(["setup", "all", "--dry-run", "--root", str(root)]) == 0
    assert main(["status", "--root", str(root)]) == 0
    assert main(["remove", "all", "--root", str(root)]) == 0  # nothing installed: still 0
    out = capsys.readouterr().out
    assert "would-install" in out
    assert "not-installed" in out


def test_setup_and_remove_round_trip(tmp_path: Path):
    root = tmp_path / "proj"
    root.mkdir()
    assert main(["setup", "claude", "--root", str(root)]) == 0
    target = skill_dir(PLATFORMS["claude"], "project", root, Path.home())
    assert (target / "SKILL.md").exists()
    assert main(["remove", "claude", "--root", str(root)]) == 0
    assert not target.exists()


def test_unknown_target_exits_with_error(tmp_path: Path):
    with pytest.raises(SystemExit):
        main(["setup", "cursor", "--root", str(tmp_path)])


def test_cli_marks_cover_outcomes():
    # Every installer outcome must render with a deliberate mark, never the "?" fallback.
    assert set(_OUTCOME_MARKS) == set(OUTCOMES)
