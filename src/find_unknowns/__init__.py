"""find-unknowns — a lifecycle unknowns-ledger skill for coding agents, with an installer.

The skill (``assets/SKILL.md``) keeps one unknowns ledger per feature: a blindspot pass
populates it before implementation, routed techniques resolve its entries, a deviation
rail appends to it during implementation, and a quiz generated from it closes the loop
before merging. This package ships the skill and a ``setup`` command that installs it
for Claude Code, OpenAI Codex, and GitHub Copilot.
"""

# Keep this line as `__version__ = "X.Y.Z"` (double quotes, single spaces): both
# hatchling's version source and any future tag-release workflow parse this exact shape.
__version__ = "0.1.0"

SKILL_NAME = "find-unknowns"
