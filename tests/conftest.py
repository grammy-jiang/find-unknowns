"""Shared fixture paths (blueprint pattern: defined once, imported everywhere).

Also puts evals/ on sys.path so the pure eval graders can be unit-tested.
"""

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_FIXTURES = _REPO / "evals" / "fixtures"
GOLDEN = _FIXTURES / "c3-hearst-is-a-20260723.md"
INPROGRESS = _FIXTURES / "schema-validator-20260723.md"

sys.path.insert(0, str(_REPO / "evals"))
