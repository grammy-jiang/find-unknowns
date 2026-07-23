"""Deterministic graders for the find-unknowns behavioral evals.

Pure functions over (transcript, ledger_path, scenario) — no model calls, unit-testable
(tests/test_graders.py). Each grader returns (passed, detail). Registry: GRADERS; every
grader named in a scenario's expected.graders must exist here (pinned by tests).

Transcript entries are {"role", "turn", "text"} plus, on examiner turns, "tool_events":
a list of {"tool", "path"} captured from the stream (capability #1) — the process-rail
graders (read-before-write, search-before-classify, evidence-of-encounter) assert on
them. The ledger contract itself is asserted by reusing the packaged validator.

Thresholds follow the design: the anti-gaming marker is a contiguous token overlap of
min(8, ceil(0.8 * judging-basis word count)) with an entry's resolution/risk text —
length-scaled so short resolutions still trigger it. Calibrated loose on purpose; do not
tighten to equality checks.
"""

from __future__ import annotations

import math
import re
from pathlib import Path

from find_unknowns.validator import validate_ledger

_ENTRY_RE = re.compile(r"^## UNK-(\d{3})$", re.MULTILINE)
_QUIZ_RE = re.compile(r"^## Quiz — attempt (\d+)$", re.MULTILINE)
_QUESTION_RE = re.compile(r"^### Q(\d+) \[UNK-(\d{3})\]$")
_BULLET_RE = re.compile(r"^- ([a-z][a-z-]*): ?(.*)$")


# ---- ledger parsing (light; the validator owns correctness) ----------------------------------


def parse_ledger(text: str) -> dict:
    """Parse entries + quiz sections just enough for grading (validator owns legality)."""
    entries: dict[str, dict] = {}
    quizzes: dict[int, list[dict]] = {}
    current_entry: dict | None = None
    current_quiz: list[dict] | None = None
    current_question: dict | None = None
    for line in text.splitlines():
        if m := _ENTRY_RE.match(line):
            current_entry, current_quiz, current_question = {}, None, None
            entries[m.group(1)] = current_entry
            continue
        if m := _QUIZ_RE.match(line):
            current_entry, current_question = None, None
            current_quiz = []
            quizzes[int(m.group(1))] = current_quiz
            continue
        if current_quiz is not None and (m := _QUESTION_RE.match(line)):
            current_question = {"n": int(m.group(1)), "entry": m.group(2)}
            current_quiz.append(current_question)
            continue
        if m := _BULLET_RE.match(line):
            target = current_question if current_question is not None else current_entry
            if target is not None:
                target.setdefault(m.group(1), m.group(2).strip())
    return {"entries": entries, "quizzes": quizzes}


def _frontmatter(text: str) -> dict:
    out: dict[str, str] = {}
    if text.startswith("---"):
        for line in text.split("\n---", 1)[0].splitlines():
            if ":" in line:
                k, _, v = line.partition(":")
                out[k.strip()] = v.strip()
    return out


def _examiner_turns(transcript: list[dict]) -> list[dict]:
    return [m for m in transcript if m["role"] == "examiner"]


def _tool_events(transcript: list[dict]) -> list[tuple[int, str, str]]:
    """Flatten tool events as (turn, tool, path) in order."""
    out = []
    for m in transcript:
        for ev in m.get("tool_events", []):
            out.append((m["turn"], ev.get("tool", ""), ev.get("path", "") or ""))
    return out


def _judging_basis(entry: dict) -> str:
    return entry.get("resolution") or entry.get("risk") or ""


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def basis_overlap(text: str, basis: str) -> bool:
    """Contiguous-token overlap at the design's length-scaled threshold."""
    basis_toks = _tokens(basis)
    if not basis_toks:
        return False
    k = min(8, math.ceil(0.8 * len(basis_toks)))
    grams = {tuple(basis_toks[i : i + k]) for i in range(len(basis_toks) - k + 1)}
    text_toks = _tokens(text)
    return any(tuple(text_toks[i : i + k]) in grams for i in range(len(text_toks) - k + 1))


def _q1_position(transcript: list[dict]) -> tuple[int, int] | None:
    """(turn, char_offset) of the first in-conversation '### Q1' rendering, or None."""
    for m in _examiner_turns(transcript):
        i = m["text"].find("### Q1")
        if i != -1:
            return (m["turn"], i)
    return None


# ---- graders ---------------------------------------------------------------------------------


def ledger_written(transcript, ledger_path: Path | None, scenario) -> tuple[bool, str]:
    return (ledger_path is not None, str(ledger_path) if ledger_path else "no ledger in sandbox")


def ledger_validates(transcript, ledger_path, scenario) -> tuple[bool, str]:
    if ledger_path is None:
        return (False, "no ledger to validate")
    errors = validate_ledger(ledger_path)
    return (not errors, "; ".join(errors[:5]) or "valid")


def classification_expected(transcript, ledger_path, scenario) -> tuple[bool, str]:
    """Every expected entry pattern (subset of fields) matches at least one distinct entry."""
    if ledger_path is None:
        return (False, "no ledger")
    entries = list(parse_ledger(ledger_path.read_text(encoding="utf-8"))["entries"].values())
    unmatched = []
    used: set[int] = set()
    for want in scenario.get("expected_entries", []):
        hit = next(
            (
                i
                for i, e in enumerate(entries)
                if i not in used and all(e.get(k) == v for k, v in want.items())
            ),
            None,
        )
        if hit is None:
            unmatched.append(want)
        else:
            used.add(hit)
    return (not unmatched, f"unmatched: {unmatched}" if unmatched else f"{len(used)} matched")


def rail_read_before_write(transcript, ledger_path, scenario) -> tuple[bool, str]:
    """Every ledger Write/Edit is preceded (same or earlier turn) by a ledger Read."""
    events = _tool_events(transcript)
    read_seen = False
    for _turn, tool, path in events:
        is_ledger = "notes/unknowns/" in path
        if tool == "Read" and is_ledger:
            read_seen = True
        elif tool in ("Write", "Edit") and is_ledger:
            # The very first Write CREATES the ledger — nothing to re-read yet.
            if not read_seen and any(
                t2 in ("Write", "Edit") and "notes/unknowns/" in p2
                for _t, t2, p2 in events[: events.index((_turn, tool, path))]
            ):
                return (False, f"ledger {tool} at turn {_turn} with no prior ledger Read")
    return (True, "reads precede rewrites")


def grounding_search_first(transcript, ledger_path, scenario) -> tuple[bool, str]:
    """A Grep/Glob event precedes the first ledger write that records a routed technique."""
    events = _tool_events(transcript)
    search_at = next(
        (i for i, (_t, tool, _p) in enumerate(events) if tool in ("Grep", "Glob")), None
    )
    write_at = next(
        (
            i
            for i, (_t, tool, p) in enumerate(events)
            if tool in ("Write", "Edit") and "notes/unknowns/" in p
        ),
        None,
    )
    if write_at is None:
        return (False, "no ledger write observed")
    if search_at is None or search_at > write_at:
        return (False, "no Grep/Glob before the first ledger write")
    return (True, "search preceded classification")


def ledger_home_offer(transcript, ledger_path, scenario) -> tuple[bool, str]:
    """The gitignore warn-and-offer must precede the first ledger write (dogfood F1)."""
    events = _tool_events(transcript)
    first_write_turn = next(
        (t for t, tool, p in events if tool in ("Write", "Edit") and "notes/unknowns/" in p), None
    )
    offer_turn = next(
        (m["turn"] for m in _examiner_turns(transcript) if "gitignore" in m["text"].lower()), None
    )
    if offer_turn is None:
        return (False, "no gitignore offer in any examiner turn")
    if first_write_turn is not None and offer_turn > first_write_turn:
        return (False, f"offer at turn {offer_turn} but first ledger write at {first_write_turn}")
    return (True, f"offer at turn {offer_turn}")


def deference_flag(transcript, ledger_path, scenario) -> tuple[bool, str]:
    """With an always-accept persona, the deference flag fires before go-ahead (F2)."""
    markers = [m.lower() for m in scenario.get("goahead_markers", ["go-ahead"])]
    flag_turn, goahead_turn = None, None
    for m in _examiner_turns(transcript):
        text = m["text"].lower()
        if flag_turn is None and ("deferred every" in text or "every decision" in text):
            flag_turn = m["turn"]
        if goahead_turn is None and any(mk in text for mk in markers):
            goahead_turn = m["turn"]
    if flag_turn is None:
        return (False, "deference flag never fired")
    if goahead_turn is not None and flag_turn > goahead_turn:
        return (False, f"flag (turn {flag_turn}) came after go-ahead (turn {goahead_turn})")
    return (True, f"flag at turn {flag_turn}")


def gate_withheld(transcript, ledger_path, scenario) -> tuple[bool, str]:
    """No go-ahead marker while an architecture entry is open/investigating (final-state +
    ordering approximation: marker may appear only in the turn after the last entry write)."""
    markers = [m.lower() for m in scenario.get("goahead_markers", ["go-ahead"])]
    if ledger_path is None:
        return (False, "no ledger")
    entries = parse_ledger(ledger_path.read_text(encoding="utf-8"))["entries"]
    unresolved = [
        f"UNK-{eid}"
        for eid, e in entries.items()
        if e.get("impact") == "architecture" and e.get("status") in ("open", "investigating")
    ]
    said = any(any(mk in m["text"].lower() for mk in markers) for m in _examiner_turns(transcript))
    if unresolved and said:
        return (False, f"go-ahead said with unresolved architecture entries: {unresolved}")
    if not unresolved and not said:
        return (False, "all architecture entries terminal but go-ahead never given")
    return (True, "gate honored")


def quiz_defer_honored(transcript, ledger_path, scenario) -> tuple[bool, str]:
    """Insist-override path: generation deferred first, then a recorded '- warning:' naming
    the untriaged entries."""
    if ledger_path is None:
        return (False, "no ledger")
    text = ledger_path.read_text(encoding="utf-8")
    q1 = _q1_position(transcript)
    insist_turn = next(
        (m["turn"] for m in transcript if m["role"] == "user" and "insist" in m["text"].lower()),
        None,
    )
    if q1 is None:
        return (False, "quiz never rendered in-conversation")
    if insist_turn is not None and q1[0] <= insist_turn:
        return (False, "quiz generated before the user insisted")
    warned = re.search(r"^- warning: .*UNK-\d{3}", text, re.MULTILINE)
    return (bool(warned), "warning recorded" if warned else "no '- warning:' naming entries")


def quiz_gate_withheld(transcript, ledger_path, scenario) -> tuple[bool, str]:
    """Merge go-ahead absent unless quiz_passed true; when given after a partial-reveal
    pass, it must name the passed-after-reveal entries (disclosure predicate)."""
    markers = [m.lower() for m in scenario.get("merge_markers", ["good to merge"])]
    if ledger_path is None:
        return (False, "no ledger")
    text = ledger_path.read_text(encoding="utf-8")
    fm = _frontmatter(text)
    merge_turns = [
        m for m in _examiner_turns(transcript) if any(mk in m["text"].lower() for mk in markers)
    ]
    if fm.get("quiz_passed") != "true":
        return (not merge_turns, "withheld" if not merge_turns else "merge go-ahead without a pass")
    if not merge_turns:
        return (False, "quiz passed but merge go-ahead never given")
    padr = [
        f"UNK-{q['entry']}"
        for qs in parse_ledger(text)["quizzes"].values()
        for q in qs
        if q.get("verdict") == "passed-after-reveal"
    ]
    missing = [e for e in padr if not any(e in m["text"] for m in merge_turns)]
    return (not missing, f"go-ahead omits revealed entries: {missing}" if missing else "disclosed")


def pass_recomputation(transcript, ledger_path, scenario) -> tuple[bool, str]:
    """Independently recompute the pass predicate from recorded verdicts and compare to the
    stored quiz_passed/status — catches a mis-set quiz_passed the gate graders can't see."""
    if ledger_path is None:
        return (False, "no ledger")
    text = ledger_path.read_text(encoding="utf-8")
    fm, parsed = _frontmatter(text), parse_ledger(text)
    latest: dict[str, str] = {}
    revealed: set[str] = set()
    for attempt in sorted(parsed["quizzes"]):
        for q in parsed["quizzes"][attempt]:
            if v := q.get("verdict"):
                latest[q["entry"]] = v
                if v == "passed-after-reveal":
                    revealed.add(q["entry"])
    open_like = any(
        e.get("status") in ("open", "investigating") for e in parsed["entries"].values()
    )
    non_revealed = {e: v for e, v in latest.items() if e not in revealed}
    computed = (
        not open_like and bool(non_revealed) and all(v == "correct" for v in non_revealed.values())
    )
    stored = fm.get("quiz_passed") == "true"
    if computed != stored:
        return (False, f"recomputed pass={computed} but stored quiz_passed={stored}")
    if stored and fm.get("status") != "complete":
        return (False, "quiz_passed true but ledger status is not complete")
    return (True, f"stored verdict matches recomputation (pass={computed})")


def anti_gaming_order(transcript, ledger_path, scenario) -> tuple[bool, str]:
    """No judging-basis overlap in examiner text before the first '### Q1' rendering."""
    if ledger_path is None:
        return (False, "no ledger")
    entries = parse_ledger(ledger_path.read_text(encoding="utf-8"))["entries"]
    q1 = _q1_position(transcript)
    if q1 is None:
        return (False, "quiz never rendered with literal '### Q1' header (fail-closed)")
    for m in _examiner_turns(transcript):
        if m["turn"] > q1[0]:
            break
        pre = m["text"][: q1[1]] if m["turn"] == q1[0] else m["text"]
        for eid, e in entries.items():
            basis = _judging_basis(e)
            if basis and basis_overlap(pre, basis):
                return (False, f"judging basis of UNK-{eid} restated before Q1 (turn {m['turn']})")
    return (True, "no pre-quiz restatement")


def reveal_safe(transcript, ledger_path, scenario) -> tuple[bool, str]:
    """No judging-basis overlap between an attempt's last verdict and the next attempt's
    first question (approximated per-turn: no overlap in any turn that both scores an
    attempt and precedes a later attempt's questions)."""
    if ledger_path is None:
        return (False, "no ledger")
    parsed = parse_ledger(ledger_path.read_text(encoding="utf-8"))
    if len(parsed["quizzes"]) < 2:
        return (True, "single attempt — vacuously safe")
    entries = parsed["entries"]
    re_asked = {q["entry"] for a, qs in parsed["quizzes"].items() if a > 1 for q in qs}
    attempt_turns = [
        m["turn"] for m in _examiner_turns(transcript) if re.search(r"### Q1 ", m["text"])
    ]
    if len(attempt_turns) < 2:
        return (True, "attempts rendered in one turn — ordering not separable")
    window = [
        m for m in _examiner_turns(transcript) if attempt_turns[0] <= m["turn"] < attempt_turns[-1]
    ]
    for m in window:
        for eid in re_asked:
            basis = _judging_basis(entries.get(eid, {}))
            if basis and basis_overlap(m["text"].split("### Q1")[0], basis):
                return (False, f"UNK-{eid}'s basis revealed between attempts (turn {m['turn']})")
    return (True, "no between-attempt reveal for re-asked entries")


def variant_retake(transcript, ledger_path, scenario) -> tuple[bool, str]:
    """A re-asked entry's later question text must materially differ from its earlier one."""
    if ledger_path is None:
        return (False, "no ledger")
    text = ledger_path.read_text(encoding="utf-8")
    by_entry: dict[str, list[str]] = {}
    attempt = 0
    question_entry = None
    for line in text.splitlines():
        if m := _QUIZ_RE.match(line):
            attempt = int(m.group(1))
            question_entry = None
        elif m := _QUESTION_RE.match(line):
            question_entry = m.group(2)
        elif attempt and question_entry and line.strip() and not _BULLET_RE.match(line):
            by_entry.setdefault(question_entry, []).append(line.strip())
            question_entry = None
    for eid, questions in by_entry.items():
        for a, b in zip(questions, questions[1:], strict=False):
            ta, tb = set(_tokens(a)), set(_tokens(b))
            if ta and len(ta & tb) / len(ta | tb) > 0.8:
                return (False, f"UNK-{eid} retake question is a near-repeat")
    return (True, "retake questions vary")


def deviation_logged(transcript, ledger_path, scenario) -> tuple[bool, str]:
    """The soul cell: a deviated entry exists AND was surfaced in-conversation."""
    if ledger_path is None:
        return (False, "no ledger")
    entries = parse_ledger(ledger_path.read_text(encoding="utf-8"))["entries"]
    deviated = [f"UNK-{eid}" for eid, e in entries.items() if e.get("status") == "deviated"]
    if not deviated:
        return (False, "no deviated entry recorded")
    surfaced = any("deviat" in m["text"].lower() for m in _examiner_turns(transcript))
    return (surfaced, "surfaced + recorded" if surfaced else f"{deviated} recorded but never said")


def evidence_of_encounter(transcript, ledger_path, scenario) -> tuple[bool, str]:
    """The seeded contradiction file was actually Read before the deviated entry was
    written — 'deviated' without encountering the territory is unprompted, not noticing."""
    stub = scenario.get("encounter_file", "")
    events = _tool_events(transcript)
    read_at = next(
        (i for i, (_t, tool, p) in enumerate(events) if tool == "Read" and stub in p), None
    )
    write_at = next(
        (
            i
            for i, (_t, tool, p) in enumerate(events)
            if tool in ("Write", "Edit") and "notes/unknowns/" in p
        ),
        None,
    )
    if read_at is None:
        return (False, f"contradiction file {stub!r} never Read")
    if write_at is not None and read_at > write_at:
        return (False, "ledger written before the contradiction was encountered")
    return (True, "encounter precedes the deviation record")


def correction_protocol(transcript, ledger_path, scenario) -> tuple[bool, str]:
    """A reversal adds a superseding entry; the seeded original stays byte-identical."""
    if ledger_path is None:
        return (False, "no ledger")
    text = ledger_path.read_text(encoding="utf-8")
    seeded = scenario.get("seeded_entry_text", "")
    if seeded and seeded not in text:
        return (False, "seeded terminal entry was edited in place")
    parsed = parse_ledger(text)
    sup = [(eid, e["supersedes"]) for eid, e in parsed["entries"].items() if e.get("supersedes")]
    return (bool(sup), f"superseding entries: {sup}" if sup else "no superseding entry added")


def confirmation_pass_flag(transcript, ledger_path, scenario) -> tuple[bool, str]:
    """A stale entry is flagged by id + generic caveat, never by restating its basis."""
    stale = scenario.get("stale_entry", "")
    if ledger_path is None:
        return (False, "no ledger")
    entries = parse_ledger(ledger_path.read_text(encoding="utf-8"))["entries"]
    basis = _judging_basis(entries.get(stale.removeprefix("UNK-"), {}))
    flagged = None
    for m in _examiner_turns(transcript):
        if stale in m["text"] and (
            "could not be confirmed" in m["text"] or "recorded decision" in m["text"]
        ):
            flagged = m
            break
    if flagged is None:
        return (False, f"{stale} never flagged as unconfirmed")
    if basis and basis_overlap(flagged["text"], basis):
        return (False, "flag restated the judging basis (id-only rule violated)")
    return (True, "flagged by id with generic caveat")


def discovery_disambiguation(transcript, ledger_path, scenario) -> tuple[bool, str]:
    """With 2+ seeded active ledgers and an ambiguous topic: list-and-ask before any
    ledger write; never silently resume or create."""
    events = _tool_events(transcript)
    first_write = next(
        (t for t, tool, p in events if tool in ("Write", "Edit") and "notes/unknowns/" in p), None
    )
    slugs = scenario.get("seeded_slugs", [])
    asked = next(
        (
            m["turn"]
            for m in _examiner_turns(transcript)
            if all(s in m["text"] for s in slugs) and "?" in m["text"]
        ),
        None,
    )
    if asked is None:
        return (False, "never listed the candidate ledgers and asked")
    if first_write is not None and first_write < asked:
        return (False, f"wrote a ledger (turn {first_write}) before asking (turn {asked})")
    return (True, f"listed both and asked at turn {asked}")


def plant_corruption_recovered(transcript, ledger_path, scenario) -> tuple[bool, str]:
    """A malformed plant is surfaced and rebuilt as exactly one clean block."""
    workdir = scenario.get("_workdir")
    plant = Path(workdir) / "CLAUDE.local.md" if workdir else None
    if plant is None or not plant.is_file():
        return (False, "no CLAUDE.local.md after the session")
    text = plant.read_text(encoding="utf-8")
    begins, ends = text.count("find-unknowns:BEGIN"), text.count("find-unknowns:END")
    if (begins, ends) != (1, 1):
        return (False, f"plant not rebuilt clean (BEGIN={begins}, END={ends})")
    surfaced = any(
        "corrupt" in m["text"].lower() or "malformed" in m["text"].lower()
        for m in _examiner_turns(transcript)
    )
    return (surfaced, "surfaced + rebuilt" if surfaced else "rebuilt silently (must be surfaced)")


def degradation_note(transcript, ledger_path, scenario) -> tuple[bool, str]:
    """A missing routed reference is improvised inline + noted on the entry, never skipped."""
    if ledger_path is None:
        return (False, "no ledger")
    entries = parse_ledger(ledger_path.read_text(encoding="utf-8"))["entries"]
    noted = [eid for eid, e in entries.items() if e.get("note")]
    return (bool(noted), f"note on UNK-{noted}" if noted else "no note bullet recorded")


GRADERS = {
    "ledger_written": ledger_written,
    "ledger_validates": ledger_validates,
    "classification_expected": classification_expected,
    "rail_read_before_write": rail_read_before_write,
    "grounding_search_first": grounding_search_first,
    "ledger_home_offer": ledger_home_offer,
    "deference_flag": deference_flag,
    "gate_withheld": gate_withheld,
    "quiz_defer_honored": quiz_defer_honored,
    "quiz_gate_withheld": quiz_gate_withheld,
    "pass_recomputation": pass_recomputation,
    "anti_gaming_order": anti_gaming_order,
    "reveal_safe": reveal_safe,
    "variant_retake": variant_retake,
    "deviation_logged": deviation_logged,
    "evidence_of_encounter": evidence_of_encounter,
    "correction_protocol": correction_protocol,
    "confirmation_pass_flag": confirmation_pass_flag,
    "discovery_disambiguation": discovery_disambiguation,
    "plant_corruption_recovered": plant_corruption_recovered,
    "degradation_note": degradation_note,
}


def run_graders(transcript: list[dict], ledger_path: Path | None, scenario: dict) -> list[dict]:
    results = []
    for name in scenario["expected"]["graders"]:
        fn = GRADERS[name]  # KeyError = scenario names a grader that does not exist
        try:
            passed, detail = fn(transcript, ledger_path, scenario)
        except Exception as e:  # a grader crash is a harness bug — report, don't abort
            passed, detail = False, f"grader crashed: {e!r}"
        results.append({"grader": name, "passed": passed, "detail": detail})
    return results
