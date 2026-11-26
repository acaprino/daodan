"""A stand-in for `node cli.mjs` of the stack-analyser release: it records how it was started and answers as the
release does.

`install(folder)` writes a program in `folder` that runs this file with the record's path; the program appends
`{argv, cwd, env}` to `folder/calls.jsonl` (`env`: the names of the variables that begin with `NODE_`), copies the
files named after `--declarations` and `--perimeter` to `folder/declarations.json` and `folder/perimeter.json`, writes
`ANSWER` to the file after `--output`, and `CATALOGUE` to the file after `--catalogue`.
`FAKE_STACK_ANALYSER=fail|garbage|sleep` makes it exit with status 1 and a message on stderr, write what is not
JSON, or sleep.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import time
from pathlib import Path

ANSWER = {"name": "main", "path": ["/"], "techs": ["react"], "childs": [],
          "evidence": [{"tech": "react", "kind": "package", "value": "react", "path": "/package.json",
                        "source": "stack-analyser"}]}
CATALOGUE = [{"tech": "react", "name": "React", "type": "framework", "dependencies": [{"type": "npm", "name": "react"}]}]


def install(folder: Path) -> Path:
    """A program in `folder` that is this stand-in."""
    folder.mkdir(parents=True, exist_ok=True)
    record = folder / "calls.jsonl"
    if os.name == "nt":
        program = folder / "node.bat"
        program.write_text(f'@"{sys.executable}" -I "{__file__}" "{record}" %*\n@exit /b %ERRORLEVEL%\n',
                           encoding="utf-8")
    else:
        program = folder / "node"
        program.write_text(f'#!/bin/sh\nexec "{sys.executable}" -I "{__file__}" "{record}" "$@"\n', encoding="utf-8")
        program.chmod(0o755)
    return program


def calls(program: Path) -> list[dict]:
    path = program.parent / "calls.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()] if path.is_file() else []


def _after(argv: list[str], option: str) -> str | None:
    return argv[argv.index(option) + 1] if option in argv else None


def main(record: str, argv: list[str]) -> int:
    with open(record, "a", encoding="utf-8") as handle:
        handle.write(json.dumps({"argv": argv, "cwd": os.getcwd(),
                                 "env": sorted(name for name in os.environ if name.upper().startswith("NODE_"))})
                     + "\n")
    for option, copy in (("--declarations", "declarations.json"), ("--perimeter", "perimeter.json")):
        if _after(argv, option):
            shutil.copyfile(_after(argv, option), Path(record).parent / copy)
    mode = os.environ.get("FAKE_STACK_ANALYSER")
    if mode == "fail":
        print("Error: the fake failed", file=sys.stderr)
        return 1
    if mode == "sleep":
        time.sleep(3)
    answer = CATALOGUE if "--catalogue" in argv else ANSWER
    Path(_after(argv, "--catalogue") or _after(argv, "--output")).write_text(
        "not json" if mode == "garbage" else json.dumps(answer), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2:]))
