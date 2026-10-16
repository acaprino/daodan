"""Render Codex repository instructions from their canonical Claude copies."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_SKILLS = (
    "custom-plugin-refresh",
    "downstream-exports",
    "external-repo-intake",
    "upstream-sync",
)
REPLACEMENTS = (
    (".claude/skills/", ".agents/skills/"),
    ("~/.claude/plugins/cache", "~/.codex/plugins/cache"),
    ("CLAUDE.md", "AGENTS.md"),
    ("claude plugin install", "codex plugin add"),
    ("claude plugin marketplace update", "codex plugin marketplace upgrade"),
    ("claude plugin", "codex plugin"),
    ("hosts that are not Claude Code", "hosts that are not Codex"),
)
CLAUDE_DISTRIBUTION_COMMAND = "claude plugin marketplace add "
CLAUDE_DISTRIBUTION_SENTINEL = "__DAODAN_CLAUDE_DISTRIBUTION_COMMAND__"


def adapt_claude_instructions_for_codex(text: str) -> str:
    """Apply the complete, deliberately small Codex instruction adaptation."""
    text = text.replace(
        CLAUDE_DISTRIBUTION_COMMAND,
        CLAUDE_DISTRIBUTION_SENTINEL,
    )
    for source, target in REPLACEMENTS:
        text = text.replace(source, target)
    return text.replace(
        CLAUDE_DISTRIBUTION_SENTINEL,
        CLAUDE_DISTRIBUTION_COMMAND,
    )


def instruction_pairs(root: Path = ROOT) -> tuple[tuple[Path, Path], ...]:
    skills = tuple(
        (
            root / ".claude" / "skills" / name / "SKILL.md",
            root / ".agents" / "skills" / name / "SKILL.md",
        )
        for name in WORKFLOW_SKILLS
    )
    return ((root / "CLAUDE.md", root / "AGENTS.md"), *skills)


def sync(*, check: bool, root: Path = ROOT) -> list[Path]:
    """Write or report Codex instruction files that differ from their source."""
    drift: list[Path] = []
    for source, target in instruction_pairs(root):
        expected = adapt_claude_instructions_for_codex(
            source.read_text(encoding="utf-8")
        )
        actual = target.read_text(encoding="utf-8") if target.is_file() else None
        if actual == expected:
            continue
        drift.append(target)
        if not check:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(expected, encoding="utf-8", newline="\n")
    return drift


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    drift = sync(check=args.check, root=root)
    for path in drift:
        print(path.relative_to(root).as_posix())
    return 1 if args.check and drift else 0


if __name__ == "__main__":
    sys.exit(main())
