"""Fail if the harness-independent protocol layer leaks harness, vendor, or
transport vocabulary. Stdlib only, runnable from the repo root."""
import re
import sys
from pathlib import Path

# The four protocol documents (PROTOCOL.md, finding-lifecycle.md, packet-anatomy.md,
# round-prompts.md) ship under the skill, because a kernel-root directory reaches no
# host package.
PROTOCOL_DIR = Path("plugins/peer-review/skills/cross-model-peer-review/references")

# Case-insensitive: vendors, models, transports. Case-sensitive: tool names that
# are ordinary words in lowercase. "Read" is deliberately absent: too ambiguous
# for a mechanical check, covered by review instead.
INSENSITIVE = [
    r"\bclaude\b", r"\banthropic\b", r"\bopenai\b", r"\bgpt-?[0-9o]*\b",
    r"\bgemini\b", r"\bcopilot\b", r"\bcodex\b", r"\bmcp\b",
    r"\bchat/completions\b", r"CLAUDE_PLUGIN_ROOT",
]
SENSITIVE = [r"\bBash\b", r"\bGrep\b", r"\bGlob\b", r"\bWebFetch\b", r"\bWebSearch\b"]

def main() -> int:
    files = sorted(PROTOCOL_DIR.glob("*.md"))
    if not files:
        # Zero files scanned is not a clean result: a moved directory would
        # otherwise pass this check vacuously, which is how it went stale once.
        print(f"no protocol documents found under {PROTOCOL_DIR}: nothing was checked")
        return 1
    failures = []
    for path in files:
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for pattern in INSENSITIVE:
                if re.search(pattern, line, re.IGNORECASE):
                    failures.append(f"{path}:{number}: {pattern}: {line.strip()}")
            for pattern in SENSITIVE:
                if re.search(pattern, line):
                    failures.append(f"{path}:{number}: {pattern}: {line.strip()}")
    if failures:
        print("ontology leak in the protocol layer:")
        print("\n".join(failures))
        return 1
    print(f"protocol layer clean ({len(files)} files)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
