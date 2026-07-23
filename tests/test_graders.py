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
    # Flip the retake's verdict — the file's LAST verdict line — to passed-after-reveal:
    # UNK-002 becomes a revealed entry, and the merge go-ahead must then name it.
    head, sep, _tail = GOLDEN.read_text(encoding="utf-8").rpartition("- verdict: correct")
    assert sep
    p = tmp_path / GOLDEN.name
    p.write_text(head + "- verdict: passed-after-reveal\n", encoding="utf-8")
    scenario = {"merge_markers": ["good to merge"]}
    ok, detail = G.quiz_gate_withheld([_ex(9, "All correct — good to merge.")], p, scenario)
    assert not ok and "UNK-002" in detail  # pass without naming the revealed entry
    ok, _ = G.quiz_gate_withheld(
        [_ex(9, "good to merge — note UNK-002 was answered after reveal")], p, scenario
    )
    assert ok


def test_evidence_of_encounter_accepts_bash_view():
    # A Bash-widened examiner views territory with cat/git, not the Read tool (live DEV2).
    scenario = {"encounter_file": "src/app.py"}
    bash_first = [
        _ex(1, "", [{"tool": "Bash", "path": "test -f x; cat src/app.py"}]),
        _ex(2, "", [{"tool": "Edit", "path": "notes/unknowns/g-20260722.md"}]),
    ]
    assert G.evidence_of_encounter(bash_first, None, scenario)[0]
    never = [_ex(1, "", [{"tool": "Edit", "path": "notes/unknowns/g-20260722.md"}])]
    ok, detail = G.evidence_of_encounter(never, None, scenario)
    assert not ok and "never encountered" in detail
    late = [
        _ex(1, "", [{"tool": "Edit", "path": "notes/unknowns/g-20260722.md"}]),
        _ex(2, "", [{"tool": "Bash", "path": "cat src/app.py"}]),
    ]
    ok, detail = G.evidence_of_encounter(late, None, scenario)
    assert not ok and "before" in detail


def test_plant_corruption_surfacing_accepts_named_defect(tmp_path):
    (tmp_path / "CLAUDE.local.md").write_text(
        "<!-- find-unknowns:BEGIN schema=unknowns-ledger-v1 -->\nbody\n"
        "<!-- find-unknowns:END -->\n",
        encoding="utf-8",
    )
    scenario = {"_workdir": str(tmp_path)}
    silent = [_ex(1, "Rebuilt. CLAUDE.local.md now has one clean block.")]
    ok, detail = G.plant_corruption_recovered(silent, None, scenario)
    assert not ok and "silently" in detail
    named = [_ex(1, "The plant block is orphaned: a BEGIN with no END marker. Rebuilding.")]
    assert G.plant_corruption_recovered(named, None, scenario)[0]
    concrete = [_ex(1, "Found a `BEGIN` marker with a missing `END`; I will not guess.")]
    assert G.plant_corruption_recovered(concrete, None, scenario)[0]


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
