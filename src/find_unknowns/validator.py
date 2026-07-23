"""Validate an unknowns ledger produced by the find-unknowns skill.

Structural: YAML frontmatter validated against the packaged
``unknowns-ledger-v1.schema.json``. Body rules the schema cannot express (from
``references/ledger-contract.md``, the prose source of truth):

- entries are ``## UNK-NNN`` sections of ``- key: value`` bullets, ids unique and
  ascending, at least one entry; any other ``##`` header except ``## Quiz — attempt N``
  is policed (near-miss variants called out);
- per-status field rules (``resolution`` on resolved/deviated, ``risk`` on
  accepted-risk, ``technique`` presence rules, ``quadrant: assumption`` on deviated);
- ``supersedes`` references must name an existing entry;
- quiz sections: contiguous attempt numbers capped at 3, ``### Qn [UNK-NNN]`` questions
  referencing real entries, ``verdict`` enum, ``- warning:`` as the one section-level
  bullet; ``quiz_attempts`` equals the number of fully-scored sections;
- cross-field corollaries of the pass rule (``quiz_passed: true`` implications);
- the filename slug (``<feature-slug>-YYYYMMDD[-b].md``) must agree with ``feature``.

Hardening copied from the socratic-method blueprint validator: bounded read, no-alias
YAML loader, Recursion/MemoryError guards, and a never-raise contract.

API: ``validate_ledger(path) -> list[str]`` (empty list = valid).
CLI: ``find-unknowns validate <ledger.md>``.
"""

from __future__ import annotations

import datetime
import json
import re
from importlib.resources import files
from pathlib import Path

import jsonschema
import yaml

QUADRANTS = ("known-unknown", "unknown-known", "assumption")
IMPACTS = ("architecture", "local", "cosmetic")
ENTRY_STATUSES = ("open", "investigating", "resolved", "deviated", "accepted-risk", "abandoned")
TECHNIQUES = ("interview", "reference-hunt", "brainstorm-prototype")
VERDICTS = ("correct", "missed", "passed-after-reveal")
ENTRY_KEYS = frozenset(
    {
        "quadrant",
        "impact",
        "status",
        "technique",
        "statement",
        "resolution",
        "risk",
        "supersedes",
        "note",
    }
)
QUESTION_KEYS = frozenset({"answer", "verdict"})
MAX_ATTEMPTS = 3

_ENTRY_HEADER_RE = re.compile(r"^## UNK-(\d{3})$")
_QUIZ_HEADER_RE = re.compile(r"^## Quiz — attempt (\d+)$")
_QUESTION_RE = re.compile(r"^### Q(\d+) \[UNK-(\d{3})\]$")
_BULLET_RE = re.compile(r"^- ([a-z][a-z-]*): ?(.*)$")
_SUPERSEDES_RE = re.compile(r"^UNK-\d{3}$")
_FILENAME_RE = re.compile(r"^(?P<slug>[a-z0-9][a-z0-9-]*)-(?P<date>\d{8})(?:-[b-z])?\.md$")

# A real ledger is a few KB. Cap the read (blueprint pattern) so a pathological input
# cannot exhaust memory in the CLI or the eval harness.
_MAX_LEDGER_BYTES = 1 << 20  # 1 MiB


def load_schema() -> dict:
    """Load the packaged unknowns-ledger-v1 JSON schema."""
    raw = (
        files("find_unknowns")
        .joinpath("assets/unknowns-ledger-v1.schema.json")
        .read_text(encoding="utf-8")
    )
    return json.loads(raw)


def split_frontmatter(text: str) -> tuple[str | None, str]:
    """Return (frontmatter_yaml, body), or (None, text) when no frontmatter block."""
    if not text.startswith("---"):
        return None, text
    parts = text.split("\n---", 1)
    if len(parts) < 2:
        return None, text
    return parts[0].removeprefix("---").strip("\n"), parts[1]


class _NoAliasSafeLoader(yaml.SafeLoader):
    """SafeLoader that refuses YAML anchors/aliases (alias-bomb defense; see blueprint)."""

    def compose_node(self, parent, index):
        if self.check_event(yaml.events.AliasEvent):
            event = self.get_event()
            raise yaml.constructor.ConstructorError(
                None,
                None,
                "YAML aliases/anchors are not allowed in an unknowns ledger",
                event.start_mark,
            )
        return super().compose_node(parent, index)


def parse_frontmatter_yaml(raw_fm: str) -> dict | None:
    """Parse frontmatter YAML to a mapping (dates normalized to ISO strings), or None."""
    fm = yaml.load(raw_fm, Loader=_NoAliasSafeLoader)  # SafeLoader subclass
    if not isinstance(fm, dict):
        return None
    for key in ("created", "updated"):
        if isinstance(fm.get(key), datetime.date):
            fm[key] = fm[key].isoformat()
    return fm


def _split_sections(body: str) -> tuple[list[str], list[tuple[str, list[str]]]]:
    """Split the body at ``## `` headers → (findings-for-illegal-headers, sections).

    Each section is ``(header_line, lines)``. Near-miss headers are policed here: the
    highest-risk mistakes are a malformed entry id and a plain hyphen where the quiz
    header's em-dash belongs.
    """
    findings: list[str] = []
    sections: list[tuple[str, list[str]]] = []
    current: tuple[str, list[str]] | None = None
    for line in body.splitlines():
        if line.startswith("## ") and not line.startswith("###"):
            if _ENTRY_HEADER_RE.match(line) or _QUIZ_HEADER_RE.match(line):
                current = (line, [])
                sections.append(current)
                continue
            current = None  # content under an illegal header is not attributed anywhere
            if line[3:].lower().startswith("unk"):
                findings.append(
                    f"body: near-miss entry header '{line}' — entry headers must match "
                    "'## UNK-' + exactly three digits (e.g. '## UNK-001')"
                )
            elif line[3:].lower().startswith("quiz"):
                findings.append(
                    f"body: near-miss quiz header '{line}' — quiz headers must match "
                    "'## Quiz — attempt N' (em-dash, not a plain hyphen)"
                )
            else:
                findings.append(
                    f"body: illegal section header '{line}' — only '## UNK-NNN' and "
                    "'## Quiz — attempt N' sections are allowed"
                )
        elif current is not None:
            current[1].append(line)
    return findings, sections


def _parse_bullets(
    lines: list[str], where: str, allowed: frozenset[str], errors: list[str]
) -> dict:
    """Parse ``- key: value`` bullets; police unknown keys, duplicates, and stray prose."""
    out: dict[str, str] = {}
    for line in lines:
        if not line.strip():
            continue
        m = _BULLET_RE.match(line)
        if not m:
            errors.append(
                f"{where}: non-bullet content {line.strip()!r} — entries are bullet "
                "key-value lists of bare values only"
            )
            continue
        key, value = m.group(1), m.group(2).strip()
        if key not in allowed:
            errors.append(f"{where}: unknown key '{key}' (allowed: {', '.join(sorted(allowed))})")
            continue
        if key in out:
            errors.append(f"{where}: duplicate key '{key}'")
            continue
        out[key] = value
    return out


def _check_entry(entry_id: str, fields: dict, errors: list[str]) -> None:
    where = f"entry UNK-{entry_id}"
    for key, allowed in (("quadrant", QUADRANTS), ("impact", IMPACTS), ("status", ENTRY_STATUSES)):
        value = fields.get(key)
        if value is None:
            errors.append(f"{where}: missing required field '{key}'")
        elif value not in allowed:
            errors.append(f"{where}: {key} '{value}' is not one of: {', '.join(allowed)}")
    if not fields.get("statement"):
        errors.append(f"{where}: missing required field 'statement'")

    status = fields.get("status")
    technique = fields.get("technique")
    if status in ("resolved", "deviated") and not fields.get("resolution"):
        errors.append(
            f"{where}: status '{status}' requires a 'resolution' (its quiz-judging basis)"
        )
    if status == "accepted-risk" and not fields.get("risk"):
        errors.append(
            f"{where}: status 'accepted-risk' requires a 'risk' rationale (its quiz-judging basis)"
        )
    if status in ("accepted-risk", "deviated") and technique is not None:
        errors.append(f"{where}: 'technique' must be absent on status '{status}'")
    if status in ("investigating", "resolved") and technique is None and "supersedes" not in fields:
        errors.append(
            f"{where}: status '{status}' requires a 'technique' (routed entries carry their "
            "route; a superseding correction is the one exemption)"
        )
    if technique is not None and technique not in TECHNIQUES:
        errors.append(f"{where}: technique '{technique}' is not one of: {', '.join(TECHNIQUES)}")
    if status == "deviated" and fields.get("quadrant") not in (None, "assumption"):
        errors.append(
            f"{where}: quadrant must be 'assumption' on a deviated entry (a deviation is a "
            "broken implicit assumption)"
        )
    supersedes = fields.get("supersedes")
    if supersedes is not None and not _SUPERSEDES_RE.match(supersedes):
        errors.append(f"{where}: supersedes '{supersedes}' must match 'UNK-NNN'")


def _check_quiz_section(
    attempt: int, lines: list[str], entry_ids: set[str], errors: list[str]
) -> bool:
    """Validate one quiz section; return True when it is fully scored."""
    where = f"quiz attempt {attempt}"
    questions: list[tuple[int, dict]] = []
    current_q: list[str] | None = None
    section_level: list[str] = []
    q_headers: list[tuple[int, str]] = []
    for line in lines:
        m = _QUESTION_RE.match(line)
        if m:
            q_headers.append((int(m.group(1)), m.group(2)))
            current_q = []
            questions.append((int(m.group(1)), {"_lines": current_q}))  # type: ignore[dict-item]
            continue
        if line.startswith("### "):
            errors.append(
                f"{where}: illegal question header {line.strip()!r} — questions must match "
                "'### Qn [UNK-NNN]'"
            )
            current_q = None
            continue
        (current_q if current_q is not None else section_level).append(line)

    for _, qid in q_headers:
        if qid not in entry_ids:
            errors.append(f"{where}: question cites UNK-{qid}, which does not exist in this ledger")
    q_numbers = [n for n, _ in q_headers]
    if q_numbers != sorted(set(q_numbers)) or (q_numbers and q_numbers[0] != 1):
        errors.append(f"{where}: question numbers must ascend from Q1 without duplicates")
    if not q_headers:
        errors.append(f"{where}: quiz section has no questions")

    # Section-level content: free prose is allowed (question text lives here too), but the
    # only legal section-level BULLET is the recorded warning.
    section_bullets = _parse_bullets(
        [ln for ln in section_level if _BULLET_RE.match(ln)], where, frozenset({"warning"}), errors
    )
    del section_bullets

    scored = 0
    for number, q in questions:
        q_lines = q["_lines"]
        bullets = _parse_bullets(
            [ln for ln in q_lines if _BULLET_RE.match(ln)],
            f"{where} Q{number}",
            QUESTION_KEYS,
            errors,
        )
        verdict = bullets.get("verdict")
        if verdict is not None and verdict not in VERDICTS:
            errors.append(
                f"{where} Q{number}: verdict '{verdict}' is not one of: {', '.join(VERDICTS)}"
            )
        if verdict is not None:
            scored += 1
    fully_scored = bool(q_headers) and scored == len(q_headers)
    if 0 < scored < len(q_headers):
        errors.append(
            f"{where}: partially scored ({scored} of {len(q_headers)} questions carry a "
            "verdict) — score a whole attempt or none of it"
        )
    return fully_scored


def validate_ledger(ledger_path: str | Path) -> list[str]:
    """Return list of error strings. Empty list = valid."""
    path = Path(ledger_path)
    errors: list[str] = []

    try:
        with path.open("rb") as fh:
            raw = fh.read(_MAX_LEDGER_BYTES + 1)
        if len(raw) > _MAX_LEDGER_BYTES:
            return [f"Read error: file exceeds {_MAX_LEDGER_BYTES}-byte limit"]
        text = raw.decode("utf-8-sig")
    except (OSError, UnicodeDecodeError) as e:
        return [f"Read error: {e}"]

    raw_fm, body = split_frontmatter(text)
    if raw_fm is None:
        if text.startswith("---"):
            return ["Unterminated YAML frontmatter block (opening --- found, no closing --- found)"]
        return ["No YAML frontmatter block (file must start with ---)"]

    try:
        fm = parse_frontmatter_yaml(raw_fm)
    except yaml.YAMLError as e:
        return [f"Frontmatter YAML parse error: {e}"]
    except RecursionError:
        return ["Frontmatter YAML parse error: structure nested too deeply"]
    except MemoryError:
        return ["Frontmatter YAML parse error: structure expands too large"]
    if fm is None:
        return ["Frontmatter is not a mapping"]

    try:
        schema = load_schema()
    except (OSError, json.JSONDecodeError) as e:
        return [f"Schema load error: {e}"]
    validator = jsonschema.Draft202012Validator(schema)
    try:
        schema_errors = sorted(validator.iter_errors(fm), key=lambda e: list(e.path))
    except (RecursionError, MemoryError):
        return ["frontmatter: structure too complex to validate"]
    errors.extend(
        f"frontmatter{'.' + '.'.join(str(p) for p in err.path) if err.path else ''}: {err.message}"
        for err in schema_errors
    )

    header_findings, sections = _split_sections(body)
    errors.extend(header_findings)

    entries: dict[str, dict] = {}
    entry_order: list[int] = []
    quiz_sections: list[tuple[int, list[str]]] = []
    for header, lines in sections:
        if m := _ENTRY_HEADER_RE.match(header):
            entry_id = m.group(1)
            if entry_id in entries:
                errors.append(f"body: duplicate entry id UNK-{entry_id}")
                continue
            entries[entry_id] = _parse_bullets(lines, f"entry UNK-{entry_id}", ENTRY_KEYS, errors)
            entry_order.append(int(entry_id))
        elif m := _QUIZ_HEADER_RE.match(header):
            quiz_sections.append((int(m.group(1)), lines))

    if not entries:
        errors.append("body: a ledger must contain at least one '## UNK-NNN' entry")
    if entry_order != sorted(entry_order):
        errors.append("body: entry ids must be ascending (re-read the ledger before assigning ids)")

    for entry_id, fields in entries.items():
        _check_entry(entry_id, fields, errors)
        supersedes = fields.get("supersedes")
        if supersedes and _SUPERSEDES_RE.match(supersedes) and supersedes[4:] not in entries:
            errors.append(f"entry UNK-{entry_id}: supersedes {supersedes}, which does not exist")

    attempt_numbers = [n for n, _ in quiz_sections]
    if attempt_numbers != list(range(1, len(attempt_numbers) + 1)):
        errors.append(f"quiz: attempt numbers must be contiguous from 1 (found: {attempt_numbers})")
    if any(n > MAX_ATTEMPTS for n in attempt_numbers):
        errors.append(
            f"quiz: attempt {max(attempt_numbers)} exceeds the {MAX_ATTEMPTS}-attempt cap — "
            "no attempt beyond 3 is ever written"
        )

    entry_ids = set(entries)
    fully_scored = sum(
        1 for n, lines in quiz_sections if _check_quiz_section(n, lines, entry_ids, errors)
    )
    qa = fm.get("quiz_attempts")
    if isinstance(qa, int) and qa != fully_scored:
        errors.append(
            f"quiz_attempts ({qa}) does not match the {fully_scored} fully-scored quiz "
            "section(s) — scoring an attempt increments it; generation alone does not"
        )

    open_like = [
        f"UNK-{eid}" for eid, f in entries.items() if f.get("status") in ("open", "investigating")
    ]
    if fm.get("quiz_passed") is True:
        if fm.get("status") != "complete":
            errors.append("quiz_passed: true requires ledger status 'complete'")
        if isinstance(qa, int) and qa < 1:
            errors.append("quiz_passed: true requires quiz_attempts >= 1")
        if not quiz_sections:
            errors.append("quiz_passed: true requires at least one '## Quiz — attempt N' section")
        if open_like:
            errors.append(
                f"quiz_passed: true requires zero open/investigating entries (found: "
                f"{', '.join(sorted(open_like))})"
            )

    m = _FILENAME_RE.match(path.name)
    if m and isinstance(fm.get("feature"), str) and m.group("slug") != fm["feature"]:
        errors.append(
            f"filename slug '{m.group('slug')}' does not match frontmatter feature "
            f"'{fm['feature']}'"
        )

    return errors
