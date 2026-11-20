"""A stand-in for the Secretlint executable: it records how it was started and answers as `--format=json` does.

`install(folder)` writes a program in `folder` that runs this file with the record's path; the program appends
`{argv, cwd, env, stdin}` to `folder/calls.jsonl`. Each `-----BEGIN FAKE-----` ... `-----END FAKE-----` of its input
is one secret, its range in UTF-16 code units. `FAKE_SECRETLINT=fail|garbage|sleep` makes it fail with status 2,
print what is not JSON, or sleep.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

BEGIN, END = "-----BEGIN FAKE-----", "-----END FAKE-----"
WATCHED = ("BUN_OPTIONS", "BUN_BE_BUN", "NODE_OPTIONS", "NODE_PATH", "DEBUG")


def install(folder: Path) -> Path:
    """A program in `folder` that is this stand-in."""
    folder.mkdir(parents=True, exist_ok=True)
    record = folder / "calls.jsonl"
    if os.name == "nt":
        program = folder / "secretlint.bat"
        program.write_text(f'@"{sys.executable}" -I "{__file__}" "{record}" %*\n@exit /b %ERRORLEVEL%\n',
                           encoding="utf-8")
    else:
        program = folder / "secretlint"
        program.write_text(f'#!/bin/sh\nexec "{sys.executable}" -I "{__file__}" "{record}" "$@"\n', encoding="utf-8")
        program.chmod(0o755)
    return program


def calls(program: Path) -> list[dict]:
    path = program.parent / "calls.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()] if path.is_file() else []


def _units(text: str) -> int:
    return len(text.encode("utf-16-le", "surrogatepass")) // 2


def main(record: str, argv: list[str]) -> int:
    content = sys.stdin.buffer.read().decode("utf-8")
    with open(record, "a", encoding="utf-8") as handle:
        handle.write(json.dumps({"argv": argv, "cwd": os.getcwd(), "stdin": content,
                                 "env": sorted(name for name in WATCHED if name in os.environ)}) + "\n")
    mode = os.environ.get("FAKE_SECRETLINT")
    if mode == "fail":
        print("Error: the fake failed", file=sys.stderr)
        return 2
    if mode == "garbage":
        print("not json")
        return 0
    if mode == "sleep":
        time.sleep(3)
    messages, start = [], content.find(BEGIN)
    while start >= 0:
        end = content.index(END, start) + len(END)
        messages.append({"ruleId": "@secretlint/secretlint-rule-fake", "messageId": "Fake", "severity": "error",
                         "range": [_units(content[:start]), _units(content[:end])], "message": "[FAKE] ***"})
        start = content.find(BEGIN, end)
    print(json.dumps([{"filePath": "stdin", "sourceContentType": "text", "messages": messages}]))
    return 1 if messages else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2:]))
