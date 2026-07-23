"""Autonomous behavioral eval runner for the find-unknowns skill.

Ported from the socratic-method blueprint harness, plus the four capabilities the design
names (docs/design.md, eval plan):

1. **Tool-event capture** — stream-json parsing keeps per-turn tool_use events (tool +
   path), so process-rail graders (read-before-write, search-before-classify,
   evidence-of-encounter) have something to assert on.
2. **Per-scenario workdir fixtures** — ``workdir_fixtures: {relpath: content}`` seeds the
   sandbox (plans, contradicting stubs, pre-existing ledgers, malformed plants);
   ``omit_assets: [rel]`` installs a deliberately partial skill (degradation cell).
3. **Memory-load verification** — ``memory_load_probe: true`` runs a one-shot probe that
   must echo the seeded ledger path before the real invocation; an unverified plant cell
   is a HARNESS defect (reported like a leak), never a skill failure.
4. **Per-cell tool grant + egress damping** — ``allowed_tools`` overrides the examiner
   grant (default mirrors SKILL.md's surface plus Skill); a grant containing Bash gets
   proxy env vars pointed at an unroutable address (best-effort egress damping, honestly
   NOT a firewall — the environment's own sandbox is the real boundary).

Roles stay separated: examiner (generator), simulator (environment), graders
(computational sensors), judge (inferential sensor). The examiner never grades itself.

Usage (repo root):  python evals/run_eval.py --dry-run | --cell C1 [--cell ...] | (full)
Cost warning: a full matrix spawns dozens of headless claude calls. Never wire into CI.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

EVAL_DIR = Path(__file__).resolve().parent
REPO_ROOT = EVAL_DIR.parent
SKILL_DIR = REPO_ROOT / "src" / "find_unknowns" / "assets"
sys.path.insert(0, str(EVAL_DIR))
sys.path.insert(0, str(REPO_ROOT / "src"))

from graders import run_graders  # noqa: E402

EXAMINER_TIMEOUT = 900
SIM_TIMEOUT = 300
JUDGE_TIMEOUT = 600
DEFAULT_ALLOWED_TOOLS = "Skill,Read,Grep,Glob,Write,Edit"

_LEAK_STOPWORDS = frozenset(
    {
        "find",
        "unknowns",
        "unknown",
        "ledger",
        "feature",
        "skill",
        "this",
        "that",
        "with",
        "from",
        "your",
        "what",
        "want",
        "have",
        "into",
        "about",
        "plan",
        "would",
        "should",
        "them",
        "then",
        "than",
    }
)

SIM_PROMPT_TMPL = """{persona}

Conversation so far (you are the "user"; the "examiner" is the agent):

{dialogue}

The examiner's latest message is the last one above. Reply as the user, in character,
per your briefing. Output ONLY the user's reply text — no quotes, no role labels,
no commentary."""

JUDGE_PROMPT_TMPL = """{rubric}

## Scenario expectation

{judge_focus}

## Transcript

{dialogue}

## Ledger written by the examiner (empty if none)

{ledger}
"""


def _now_stamp() -> str:
    return _dt.datetime.now().strftime("%Y%m%d-%H%M%S")


def load_scenarios(cells: list[str] | None) -> list[dict]:
    scenarios = []
    for f in sorted((EVAL_DIR / "scenarios").glob("*.yaml")):
        s = yaml.safe_load(f.read_text(encoding="utf-8"))
        s["_file"] = f.name
        if cells is None or s["cell"] in cells:
            scenarios.append(s)
    return scenarios


def _run(cmd: list[str], *, cwd: Path, timeout: int, extra_env: dict | None = None) -> str:
    # subprocess(cwd=...) does NOT update $PWD — a stale PWD is how a blueprint examiner
    # once wrote outside its sandbox.
    env = {**os.environ, "PWD": str(cwd), "OLDPWD": str(cwd), **(extra_env or {})}
    proc = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, timeout=timeout)
    if proc.returncode != 0:
        raise RuntimeError(
            f"command failed (rc={proc.returncode}): {' '.join(cmd[:4])}...\n"
            f"stderr tail: {proc.stderr[-800:]}"
        )
    return proc.stdout


def _event_path(inp: dict) -> str:
    for key in ("file_path", "path", "notebook_path", "pattern", "command"):
        if isinstance(inp.get(key), str):
            return inp[key]
    return ""


def _parse_stream_json(stdout: str) -> tuple[str | None, str, bool, list[dict]]:
    """(session_id, final_result_text, is_error, tool_events) — capability #1: unlike the
    blueprint, per-turn tool_use events are captured, not discarded."""
    session_id, result_text, is_error = None, "", False
    tool_events: list[dict] = []
    for line in stdout.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            evt = json.loads(line)
        except json.JSONDecodeError:
            continue
        if evt.get("type") == "system" and evt.get("subtype") == "init":
            session_id = evt.get("session_id") or session_id
        elif evt.get("type") == "assistant":
            for block in (evt.get("message") or {}).get("content") or []:
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    tool_events.append(
                        {
                            "tool": block.get("name", ""),
                            "path": _event_path(block.get("input") or {}),
                        }
                    )
        elif evt.get("type") == "result":
            result_text = evt.get("result") or result_text
            session_id = evt.get("session_id") or session_id
            is_error = bool(evt.get("is_error")) or str(evt.get("subtype") or "").startswith(
                "error"
            )
    return session_id, result_text, is_error, tool_events


def _sandbox_env(allowed_tools: str) -> dict:
    """Capability #4's damping half: a Bash-widened examiner gets its egress pointed at an
    unroutable proxy. Best-effort, honestly not a firewall; the env's sandbox is the real
    boundary, and the report records the widened grant as a measured change."""
    if "Bash" not in allowed_tools:
        return {}
    dead = "http://127.0.0.1:9"
    return {
        "HTTP_PROXY": dead,
        "HTTPS_PROXY": dead,
        "http_proxy": dead,
        "https_proxy": dead,
        "NO_PROXY": "",
        "no_proxy": "",
    }


def examiner_call(
    workdir: Path, model: str, prompt: str, session_id: str | None, allowed_tools: str
) -> tuple[str | None, str, bool, list[dict]]:
    cmd = ["claude", "-p"]
    if session_id:
        cmd += ["--resume", session_id]
    cmd += [
        "--model",
        model,
        "--allowedTools",
        allowed_tools,
        "--output-format",
        "stream-json",
        "--verbose",
        prompt,
    ]
    return _parse_stream_json(
        _run(cmd, cwd=workdir, timeout=EXAMINER_TIMEOUT, extra_env=_sandbox_env(allowed_tools))
    )


def one_shot(model: str, prompt: str, cwd: Path, timeout: int) -> str:
    cmd = ["claude", "-p", "--model", model, prompt]
    return _run(cmd, cwd=cwd, timeout=timeout).strip()


def _dialogue_text(transcript: list[dict]) -> str:
    return "\n\n".join(f"[{m['role']} — turn {m['turn']}]\n{m['text']}" for m in transcript)


def _find_ledger(workdir: Path) -> Path | None:
    d = workdir / "notes" / "unknowns"
    ledgers = sorted(d.glob("*.md")) if d.is_dir() else []
    return ledgers[-1] if ledgers else None


def _find_leaked_ledger(run_started: float, scenario: dict) -> Path | None:
    """A ledger written OUTSIDE the sandbox (repo-root notes/) is a harness leak — report
    it as such, never as 'no ledger written'. Token-correlated to this cell so a real
    concurrent ledger in the maintainer's notes/ is not mis-attributed."""
    leak_dir = REPO_ROOT / "notes" / "unknowns"
    if not leak_dir.is_dir():
        return None

    def _fresh(p: Path) -> bool:
        try:
            return p.stat().st_mtime >= run_started
        except OSError:
            return False

    fresh = [p for p in leak_dir.glob("*.md") if _fresh(p)]
    if not fresh:
        return None
    idea_part = scenario.get("invocation", "").split(" --", 1)[0]
    tokens = {
        t.lower()
        for t in re.findall(r"[A-Za-z]{4,}", idea_part)
        if t.lower() not in _LEAK_STOPWORDS
    }

    def related(p: Path) -> bool:
        try:
            text = p.read_text(encoding="utf-8").lower()
        except (OSError, UnicodeDecodeError):
            return False
        return any(t in text for t in tokens) if tokens else True

    related_files = [p for p in fresh if related(p)]
    if not related_files:
        return None
    return sorted(related_files, key=lambda p: p.stat().st_mtime)[-1]


def _dialogue_ended(examiner_text: str, scenario: dict) -> bool:
    markers = scenario.get("end_markers") or []
    return any(mk.lower() in examiner_text.lower() for mk in markers)


def _extract_judge_json(raw: str) -> dict | None:
    stripped = re.sub(r"^\s*```(?:json)?\s*|\s*```\s*$", "", raw.strip(), flags=re.MULTILINE)
    candidates = [stripped]
    i, j = raw.find("{"), raw.rfind("}")
    if i != -1 and j > i:
        candidates.append(raw[i : j + 1])
    for candidate in candidates:
        try:
            obj = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict) and "expected_behavior_met" in obj:
            return obj
    return None


def _seed_workdir(workdir: Path, scenario: dict) -> None:
    """Capability #2: install the skill (unless the cell tests the un-invoked plant path)
    and write per-scenario fixtures."""
    if scenario.get("install_skill", True):
        target = workdir / ".claude" / "skills" / "find-unknowns"
        omit = set(scenario.get("omit_assets", []))
        for rel in ["SKILL.md", "agents/openai.yaml", "unknowns-ledger-v1.schema.json"] + [
            f"references/{p.name}" for p in sorted((SKILL_DIR / "references").glob("*.md"))
        ]:
            if rel in omit:
                continue
            dst = target / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(SKILL_DIR / rel, dst)
    for rel, content in (scenario.get("workdir_fixtures") or {}).items():
        dst = workdir / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(content, encoding="utf-8")


def _verify_memory_load(workdir: Path, scenario: dict, model: str) -> bool:
    """Capability #3: prove the planted CLAUDE.local.md actually loads under headless
    claude -p before trusting the cell — otherwise a plant-only cell can 'pass' while
    testing nothing."""
    probe = one_shot(
        model,
        "What do your project instructions/memory say about unknowns ledgers? "
        "Answer with the exact ledger file path(s) mentioned, or 'none'.",
        cwd=workdir,
        timeout=SIM_TIMEOUT,
    )
    needle = scenario.get("memory_load_needle", "notes/unknowns/")
    return needle in probe


def run_cell(scenario: dict, args, report_dir: Path) -> dict:
    cell = scenario["cell"]
    cell_dir = report_dir / cell
    workdir = cell_dir / "workdir"
    workdir.mkdir(parents=True)
    _seed_workdir(workdir, scenario)
    scenario["_workdir"] = str(workdir)  # for graders that inspect non-ledger sandbox state

    allowed_tools = scenario.get("allowed_tools", DEFAULT_ALLOWED_TOOLS)
    transcript: list[dict] = []
    session_id: str | None = None
    prompt = scenario["invocation"].strip()
    quiet_examiner_turns = 0
    run_started = _dt.datetime.now().timestamp()

    memory_load_failed = False
    if scenario.get("memory_load_probe") and not _verify_memory_load(
        workdir, scenario, args.sim_model
    ):
        memory_load_failed = True
        print(f"  [{cell}] HARNESS: CLAUDE.local.md did not reach the model — cell invalid")

    def _persist_transcript() -> None:
        (cell_dir / "transcript.json").write_text(
            json.dumps(transcript, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )

    if not memory_load_failed:
        for turn in range(1, int(scenario.get("max_turns", 16)) + 1):
            session_id, examiner_text, examiner_error, tool_events = examiner_call(
                workdir, args.model, prompt, session_id, allowed_tools
            )
            transcript.append(
                {
                    "role": "examiner",
                    "turn": turn,
                    "text": examiner_text,
                    "tool_events": tool_events,
                }
            )
            _persist_transcript()
            print(f"  [{cell}] examiner turn {turn} ({len(examiner_text)} chars)")

            if examiner_error or (turn > 1 and session_id is None):
                transcript[-1]["session_error"] = True
                print(f"  [{cell}] WARNING: examiner turn {turn} errored/lost session — stopping")
                break

            if _dialogue_ended(examiner_text, scenario):
                break
            if "?" not in re.sub(r"```.*?```", "", examiner_text, flags=re.DOTALL):
                quiet_examiner_turns += 1
                if quiet_examiner_turns >= 2:
                    break
            else:
                quiet_examiner_turns = 0

            sim_prompt = SIM_PROMPT_TMPL.format(
                persona=scenario["persona"].strip(), dialogue=_dialogue_text(transcript)
            )
            user_text = one_shot(args.sim_model, sim_prompt, cwd=cell_dir, timeout=SIM_TIMEOUT)
            transcript.append({"role": "user", "turn": turn, "text": user_text})
            _persist_transcript()
            prompt = user_text

    ledger_path = _find_ledger(workdir)
    harness_leak = False
    if ledger_path is None:
        leaked = _find_leaked_ledger(run_started, scenario)
        if leaked is not None:
            harness_leak = True
            print(f"  [{cell}] HARNESS LEAK: ledger written outside sandbox: {leaked}")
            try:
                ledger_path = Path(shutil.copy2(str(leaked), cell_dir / "ledger-leaked.md"))
            except OSError as e:
                print(f"  [{cell}] leak capture failed ({e}); continuing")
                ledger_path = None
    grader_results = run_graders(transcript, ledger_path, scenario)

    judge_prompt = JUDGE_PROMPT_TMPL.format(
        rubric=(EVAL_DIR / "judge-rubric.md").read_text(encoding="utf-8"),
        judge_focus=scenario["expected"].get("judge_focus", "").strip(),
        dialogue=_dialogue_text(transcript),
        ledger=ledger_path.read_text(encoding="utf-8") if ledger_path else "(no ledger written)",
    )
    judge_raw = one_shot(args.judge_model, judge_prompt, cwd=cell_dir, timeout=JUDGE_TIMEOUT)
    judge = _extract_judge_json(judge_raw)
    if judge is None:
        judge_raw = one_shot(
            args.judge_model,
            judge_prompt + "\n\nOutput ONLY the JSON object — no preamble, no prose, no fences.",
            cwd=cell_dir,
            timeout=JUDGE_TIMEOUT,
        )
        judge = _extract_judge_json(judge_raw)
    if judge is None:
        judge = {"parse_error": True, "raw": judge_raw[-2000:]}

    # judging_basis_leak is the judge backstop for the anti-gaming graders (a paraphrase
    # the literal-overlap marker misses) — fail-closed, like fabrication. A failed memory
    # probe or sandbox leak is a harness defect and also hard-fails the cell.
    passed = (
        all(g["passed"] for g in grader_results)
        and judge.get("expected_behavior_met", False)
        and not judge.get("fabrication", True)
        and not judge.get("judging_basis_leak", True)
        and not harness_leak
        and not memory_load_failed
    )

    _persist_transcript()
    (cell_dir / "graders.json").write_text(
        json.dumps(grader_results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (cell_dir / "judge.json").write_text(
        json.dumps(judge, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    if ledger_path:
        shutil.copy2(ledger_path, cell_dir / "ledger.md")

    return {
        "cell": cell,
        "name": scenario["name"],
        "passed": passed,
        "harness_leak": harness_leak,
        "memory_load_failed": memory_load_failed,
        "judge_basis_leak": judge.get("judging_basis_leak"),
        "graders": {g["grader"]: g["passed"] for g in grader_results},
        "judge_expected_behavior_met": judge.get("expected_behavior_met"),
        "turns": len([m for m in transcript if m["role"] == "examiner"]),
        "ledger": str(ledger_path.name) if ledger_path else None,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cell", action="append", help="run only this cell (repeatable)")
    ap.add_argument("--model", default="sonnet", help="examiner model (default: sonnet)")
    ap.add_argument("--sim-model", default="sonnet", help="user-simulator model")
    ap.add_argument("--judge-model", default="opus", help="judge model (default: opus)")
    ap.add_argument("--dry-run", action="store_true", help="list planned cells, no calls")
    args = ap.parse_args()

    scenarios = load_scenarios(args.cell)
    if not scenarios:
        print(f"No scenarios matched cells={args.cell}")
        return 1

    if args.dry_run:
        for s in scenarios:
            extras = []
            if s.get("workdir_fixtures"):
                extras.append(f"fixtures={len(s['workdir_fixtures'])}")
            if not s.get("install_skill", True):
                extras.append("plant-only")
            if s.get("allowed_tools"):
                extras.append(f"tools={s['allowed_tools']}")
            print(
                f"{s['cell']:6} {s['name']:36} graders={s['expected']['graders']} "
                f"{' '.join(extras)}"
            )
        print(f"\nexaminer={args.model} sim={args.sim_model} judge={args.judge_model}")
        return 0

    report_dir = EVAL_DIR / "reports" / _now_stamp()
    report_dir.mkdir(parents=True)
    results = []
    for s in scenarios:
        print(f"[{s['cell']}] {s['name']} ...")
        try:
            results.append(run_cell(s, args, report_dir))
        except (RuntimeError, subprocess.TimeoutExpired) as e:
            results.append({"cell": s["cell"], "name": s["name"], "passed": False, "error": str(e)})
        print(f"[{s['cell']}] {'PASS' if results[-1].get('passed') else 'FAIL'}")

    summary_lines = [
        "# find-unknowns eval run",
        "",
        f"examiner={args.model} sim={args.sim_model} judge={args.judge_model}",
        "",
        "| cell | name | result | leak | mem | basis-leak? | graders | judge ebm |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in results:
        graders = ", ".join(f"{k}={'P' if v else 'F'}" for k, v in r.get("graders", {}).items())
        leak = "LEAK" if r.get("harness_leak") else ""
        mem = "NOMEM" if r.get("memory_load_failed") else ""
        bleak = "BASIS?" if r.get("judge_basis_leak") else ""
        summary_lines.append(
            f"| {r['cell']} | {r['name']} | {'PASS' if r.get('passed') else 'FAIL'} "
            f"| {leak} | {mem} | {bleak} | {graders or r.get('error', '')} | "
            f"{r.get('judge_expected_behavior_met')} |"
        )
    (report_dir / "summary.md").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")
    (report_dir / "summary.json").write_text(
        json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"\nReports: {report_dir}")
    n_pass = sum(1 for r in results if r.get("passed"))
    print(f"{n_pass}/{len(results)} cells passed")
    return 0 if n_pass == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
