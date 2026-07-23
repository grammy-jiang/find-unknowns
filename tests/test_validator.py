"""Validator mutation tests — each pins the exact error wording (blueprint discipline:
rewording a validator error string is a breaking change and must fail here)."""

from __future__ import annotations

from pathlib import Path

from conftest import GOLDEN, INPROGRESS

from find_unknowns.validator import validate_ledger


def _mutate(tmp_path: Path, transform, name: str = GOLDEN.name, source: Path = GOLDEN) -> list[str]:
    """Write a transformed copy of a fixture (same filename by default) and validate it."""
    out = tmp_path / name
    out.write_text(transform(source.read_text(encoding="utf-8")), encoding="utf-8")
    return validate_ledger(out)


def test_golden_fixture_is_valid():
    assert validate_ledger(GOLDEN) == []


def test_inprogress_fixture_is_valid():
    assert validate_ledger(INPROGRESS) == []


def test_missing_file_reports_read_error(tmp_path):
    assert any("Read error" in e for e in validate_ledger(tmp_path / "nope.md"))


def test_oversize_file_is_capped(tmp_path):
    errors = _mutate(tmp_path, lambda t: t + "x" * (1 << 20))
    assert errors == ["Read error: file exceeds 1048576-byte limit"]


def test_no_frontmatter(tmp_path):
    errors = _mutate(tmp_path, lambda t: t.split("---\n", 2)[2])
    assert "No YAML frontmatter block (file must start with ---)" in errors


def test_yaml_alias_is_refused(tmp_path):
    errors = _mutate(
        tmp_path, lambda t: t.replace("status: complete", "status: &a complete\nnote: *a", 1)
    )
    assert any("aliases/anchors are not allowed" in e for e in errors)


def test_wrong_schema_const(tmp_path):
    errors = _mutate(tmp_path, lambda t: t.replace("unknowns-ledger-v1", "unknowns-ledger-v9", 1))
    assert any("frontmatter.schema" in e for e in errors)


def test_extra_frontmatter_key(tmp_path):
    errors = _mutate(
        tmp_path, lambda t: t.replace("quiz_attempts: 2", "quiz_attempts: 2\nextra: 1", 1)
    )
    assert any("Additional properties are not allowed" in e for e in errors)


def test_filename_feature_mismatch(tmp_path):
    errors = _mutate(tmp_path, lambda t: t, name="other-feature-20260723.md")
    assert any(
        "filename slug 'other-feature' does not match frontmatter feature 'c3-hearst-is-a'" in e
        for e in errors
    )


def test_near_miss_entry_header(tmp_path):
    errors = _mutate(tmp_path, lambda t: t.replace("## UNK-005", "## UNK-05", 1))
    assert any("near-miss entry header" in e and "exactly three digits" in e for e in errors)


def test_near_miss_quiz_header(tmp_path):
    errors = _mutate(tmp_path, lambda t: t.replace("## Quiz — attempt 2", "## Quiz - attempt 2", 1))
    assert any("near-miss quiz header" in e and "em-dash" in e for e in errors)


def test_illegal_section_header(tmp_path):
    errors = _mutate(tmp_path, lambda t: t + "\n## Notes\n")
    assert any("illegal section header" in e for e in errors)


def test_out_of_order_ids(tmp_path):
    errors = _mutate(tmp_path, lambda t: t.replace("## UNK-005", "## UNK-009", 1))
    assert any("entry ids must be ascending" in e for e in errors)


def test_duplicate_entry_id(tmp_path):
    errors = _mutate(tmp_path, lambda t: t.replace("## UNK-005", "## UNK-004", 1))
    assert any("duplicate entry id UNK-004" in e for e in errors)


def test_missing_statement(tmp_path):
    errors = _mutate(
        tmp_path,
        lambda t: t.replace(
            "- statement: Benchmark spaCy-path yield against the flat path on factory data.\n", ""
        ),
    )
    assert any("entry UNK-005: missing required field 'statement'" in e for e in errors)


def test_technique_forbidden_on_deviated(tmp_path):
    errors = _mutate(
        tmp_path,
        lambda t: t.replace(
            "- status: deviated\n", "- status: deviated\n- technique: interview\n", 1
        ),
    )
    assert any("'technique' must be absent on status 'deviated'" in e for e in errors)


def test_technique_required_on_resolved(tmp_path):
    errors = _mutate(tmp_path, lambda t: t.replace("- technique: interview\n", "", 1))
    assert any(
        "status 'resolved' requires a 'technique'" in e and "superseding correction" in e
        for e in errors
    )


def test_superseding_resolved_entry_needs_no_technique():
    # UNK-006 in the golden fixture IS the exemption — resolved, no technique, supersedes.
    assert validate_ledger(GOLDEN) == []


def test_missing_risk_on_accepted_risk(tmp_path):
    errors = _mutate(
        tmp_path, lambda t: t.replace("- risk: Production-quality", "- note: Production-quality", 1)
    )
    assert any("status 'accepted-risk' requires a 'risk' rationale" in e for e in errors)


def test_quadrant_must_be_assumption_on_deviated(tmp_path):
    errors = _mutate(
        tmp_path,
        lambda t: t.replace(
            "- quadrant: assumption\n- impact: architecture\n- status: deviated",
            "- quadrant: known-unknown\n- impact: architecture\n- status: deviated",
            1,
        ),
    )
    assert any("quadrant must be 'assumption' on a deviated entry" in e for e in errors)


def test_unknown_bullet_key(tmp_path):
    errors = _mutate(
        tmp_path,
        lambda t: t.replace(
            "- statement: The map disagrees", "- remark: x\n- statement: The map disagrees", 1
        ),
    )
    assert any("unknown key 'remark'" in e for e in errors)


def test_dangling_supersedes(tmp_path):
    errors = _mutate(
        tmp_path, lambda t: t.replace("- supersedes: UNK-004", "- supersedes: UNK-099", 1)
    )
    assert any("supersedes UNK-099, which does not exist" in e for e in errors)


def test_question_cites_missing_entry(tmp_path):
    errors = _mutate(tmp_path, lambda t: t.replace("### Q1 [UNK-002]", "### Q1 [UNK-042]", 1))
    assert any("question cites UNK-042, which does not exist" in e for e in errors)


def test_bad_verdict(tmp_path):
    errors = _mutate(tmp_path, lambda t: t.replace("- verdict: missed", "- verdict: nope", 1))
    assert any("verdict 'nope' is not one of" in e for e in errors)


def test_attempt_cap(tmp_path):
    extra = (
        "\n## Quiz — attempt 3\n### Q1 [UNK-001]\n- verdict: correct\n"
        "\n## Quiz — attempt 4\n### Q1 [UNK-001]\n- verdict: correct\n"
    )
    errors = _mutate(tmp_path, lambda t: t + extra)
    assert any("exceeds the 3-attempt cap" in e for e in errors)


def test_noncontiguous_attempts(tmp_path):
    errors = _mutate(tmp_path, lambda t: t.replace("## Quiz — attempt 2", "## Quiz — attempt 3", 1))
    assert any("attempt numbers must be contiguous from 1" in e for e in errors)


def test_partially_scored_attempt(tmp_path):
    errors = _mutate(
        tmp_path,
        lambda t: t.replace(
            "- answer: Some validator script rejects the bad ones.\n- verdict: missed\n", "", 1
        ),
    )
    assert any("partially scored" in e for e in errors)


def test_quiz_attempts_counts_scored_sections(tmp_path):
    errors = _mutate(tmp_path, lambda t: t.replace("quiz_attempts: 2", "quiz_attempts: 1", 1))
    assert any(
        "quiz_attempts (1) does not match the 2 fully-scored quiz section(s)" in e for e in errors
    )


def test_quiz_passed_requires_complete_status(tmp_path):
    errors = _mutate(tmp_path, lambda t: t.replace("status: complete", "status: active", 1))
    assert any("quiz_passed: true requires ledger status 'complete'" in e for e in errors)


def test_quiz_passed_forbids_open_entries(tmp_path, monkeypatch):
    text = INPROGRESS.read_text(encoding="utf-8").replace(
        "status: active\nquiz_passed: false\nquiz_attempts: 0",
        "status: complete\nquiz_passed: true\nquiz_attempts: 1",
    )
    text += "\n## Quiz — attempt 1\n### Q1 [UNK-001]\n- verdict: correct\n"
    out = tmp_path / INPROGRESS.name
    out.write_text(text, encoding="utf-8")
    errors = validate_ledger(out)
    assert any(
        "quiz_passed: true requires zero open/investigating entries" in e
        and "UNK-001" in e
        and "UNK-002" in e
        for e in errors
    )


def test_empty_body(tmp_path):
    errors = _mutate(tmp_path, lambda t: t.split("## UNK-001")[0])
    assert any("must contain at least one '## UNK-NNN' entry" in e for e in errors)


def test_non_bullet_prose_in_entry(tmp_path):
    block = (
        "- quadrant: known-unknown\n- impact: architecture\n"
        "- status: resolved\n- technique: interview"
    )
    errors = _mutate(tmp_path, lambda t: t.replace(block, f"free prose line\n{block}", 1))
    assert any("non-bullet content 'free prose line'" in e for e in errors)
