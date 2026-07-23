"""Unit tests for the pure eval graders (no model calls).

Thresholds are calibrated, not arbitrary — these tests pin behavior, they do not tighten
it to equality checks (blueprint discipline).
"""

from __future__ import annotations

from pathlib import Path

import graders as G
import yaml
from conftest import GOLDEN

EVAL_DIR = Path(__file__).resolve().parents[1] / "evals"


def _ex(turn: int, text: str, events: list | None = None) -> dict:
    return {"role": "examiner", "turn": turn, "text": text, "tool_events": events or []}


def test_every_scenario_grader_exists():
    # A scenario naming a nonexistent grader must be caught here, not mid-run.
    for f in sorted((EVAL_DIR / "scenarios").glob("*.yaml")):
        s = yaml.safe_load(f.read_text(encoding="utf-8"))
        for name in s["expected"]["graders"]:
            assert name in G.GRADERS, f"{f.name} names unknown grader {name}"


def test_basis_overlap_is_length_scaled():
    short = "Sliding refresh; decided in interview."
    assert G.basis_overlap(f"the answer was: {short}", short)  # short basis still triggers
    assert not G.basis_overlap("a completely unrelated sentence about weather", short)


def test_pass_recomputation_on_golden_and_mutation(tmp_path):
    ok, detail = G.pass_recomputation([], GOLDEN, {})
    assert ok, detail
    mutated = tmp_path / GOLDEN.name
    mutated.write_text(
        GOLDEN.read_text(encoding="utf-8").replace("- verdict: correct", "- verdict: missed", 1),
        encoding="utf-8",
    )
    ok, detail = G.pass_recomputation([], mutated, {})
    assert not ok and "recomputed pass=False" in detail


def test_anti_gaming_fails_closed_without_q1():
    ok, detail = G.anti_gaming_order(
        [_ex(1, "let me quiz you informally: what was decided?")], GOLDEN, {}
    )
    assert not ok and "fail-closed" in detail


def test_anti_gaming_catches_pre_q1_restatement():
    leak = "Hash of the normalized cart contents, so identical carts share an entry."
    transcript = [
        _ex(1, f"reminder before we start: {leak}"),
        _ex(2, "### Q1 [UNK-001]\nWhat was decided?"),
    ]
    ok, _ = G.anti_gaming_order(transcript, GOLDEN, {})
    # GOLDEN's UNK-001 basis differs; craft against golden's actual basis instead:
    basis = "Interview verdict, wire the existing seed function into the pipeline"
    transcript = [_ex(1, f"recall: {basis} as deterministic input"), _ex(2, "### Q1 [UNK-001]\nQ?")]
    ok, detail = G.anti_gaming_order(transcript, GOLDEN, {})
    assert not ok and "UNK-001" in detail


def test_variant_retake_flags_near_repeat(tmp_path):
    text = GOLDEN.read_text(encoding="utf-8").replace(
        "Name the step that accepts or rejects seeded edges, and the evidence it exists.",
        "What decides the fate of the seeded candidate edges downstream?",
    )
    p = tmp_path / GOLDEN.name
    p.write_text(text, encoding="utf-8")
    ok, detail = G.variant_retake([], p, {})
    assert not ok and "near-repeat" in detail
    assert G.variant_retake([], GOLDEN, {})[0]


def test_rail_read_before_write_orders_events():
    events_bad = [
        {"tool": "Write", "path": "notes/unknowns/x-20260723.md"},
        {"tool": "Edit", "path": "notes/unknowns/x-20260723.md"},
    ]
    ok, _ = G.rail_read_before_write([_ex(1, "", events_bad)], None, {})
    assert not ok  # a rewrite with no prior Read
    events_ok = [
        {"tool": "Write", "path": "notes/unknowns/x-20260723.md"},
        {"tool": "Read", "path": "notes/unknowns/x-20260723.md"},
        {"tool": "Edit", "path": "notes/unknowns/x-20260723.md"},
    ]
    assert G.rail_read_before_write([_ex(1, "", events_ok)], None, {})[0]


def test_quiz_gate_disclosure_names_revealed_entries(tmp_path):
    text = GOLDEN.read_text(encoding="utf-8").replace(
        "## Quiz — attempt 2\n### Q1 [UNK-002]\nName the step that accepts or rejects seeded edges, and the evidence it exists.\n- answer: The LLM-confirm step; the step-7 doc shows it ran on a real package and produced the confirmed graph.\n- verdict: correct",
        "## Quiz — attempt 2\n### Q1 [UNK-002]\nVariant question about the confirm step.\n- answer: As you explained, the LLM-confirm step.\n- verdict: passed-after-reveal",
    )
    p = tmp_path / GOLDEN.name
    p.write_text(text, encoding="utf-8")
    scenario = {"merge_markers": ["good to merge"]}
    ok, detail = G.quiz_gate_withheld([_ex(9, "All correct — good to merge.")], p, scenario)
    assert not ok and "UNK-002" in detail  # pass without naming the revealed entry
    ok, _ = G.quiz_gate_withheld(
        [_ex(9, "good to merge — note UNK-002 was answered after reveal")], p, scenario
    )
    assert ok


def test_ledger_home_offer_must_precede_first_write():
    events = [{"tool": "Write", "path": "notes/unknowns/x-20260723.md"}]
    late = [
        _ex(1, "writing the ledger now", events),
        _ex(2, "by the way, add notes/ to .gitignore?"),
    ]
    ok, _ = G.ledger_home_offer(late, None, {})
    assert not ok
    early = [_ex(1, "first: notes/ is not in .gitignore — add it?"), _ex(2, "ok, writing", events)]
    assert G.ledger_home_offer(early, None, {})[0]
