"""Shared fixture paths (blueprint pattern: defined once, imported everywhere)."""

from pathlib import Path

_FIXTURES = Path(__file__).resolve().parents[1] / "evals" / "fixtures"
GOLDEN = _FIXTURES / "c3-hearst-is-a-20260723.md"
INPROGRESS = _FIXTURES / "schema-validator-20260723.md"
