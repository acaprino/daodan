"""Source: how a Node package says its tests run, read from its `package.json`, never run.

The `test` script, the one `npm test` runs, and the runner it names: Jest (`jest`, `react-scripts test`), Vitest,
Mocha, Node's own (`node --test`); a script that names none of them is npm's to run (`npm`: the runner is
whatever it starts). A script of the package it runs (`npm run test:unit`, `yarn test:unit`, `pnpm test:unit`)
is read through. npm's placeholder (`echo "Error: no test specified" && exit 1`) declares nothing.

Each is a `tests` entry `{root, runner, declared_in, args}`, `args` empty: the command is `npm test`. A package
without the script states nothing: the dynamic step's gap, never a guessed command.
"""
from __future__ import annotations

import json
from pathlib import PurePosixPath
import re

NAME, VERSION, RANK = "npm-tests", "daodan/premap/v1", "reader"
WORD = r"(?<![\w.@-]){}(?![\w.-])"  # a program's name alone or at the end of its path, not a part of another's
RUNNERS = (("jest", re.compile(WORD.format("jest") + "|" + WORD.format(r"react-scripts\s+test"))),
           ("vitest", re.compile(WORD.format("vitest"))),
           ("mocha", re.compile(WORD.format("mocha"))),
           ("node:test", re.compile(WORD.format(r"node\s(?:[^&|;]*\s)?--test"))))
THROUGH = re.compile(r"(?<![\w./@-])(?:npm|pnpm|yarn)\s+(?:run\s+)?([\w:.-]+)")  # a script that runs another


def _runner(script: str, scripts: dict, depth: int = 0) -> str:
    """The runner the script names first, through the package's scripts it runs; `npm` when it names none."""
    found = [(match.start(), name) for name, pattern in RUNNERS for match in [pattern.search(script)] if match]
    for match in THROUGH.finditer(script) if depth < 3 else ():
        inner = scripts.get(match.group(1)) if match.group(1) != "test" else None
        runner = _runner(inner, scripts, depth + 1) if isinstance(inner, str) else "npm"
        if runner != "npm":
            found.append((match.start(), runner))
    return min(found)[1] if found else "npm"


def run(context):
    tests = []
    for rel in context.inventory.files:
        if PurePosixPath(rel).name != "package.json":
            continue
        try:
            scripts = json.loads(context.inventory.text(rel)).get("scripts")
        except (ValueError, AttributeError):
            continue  # an unreadable manifest is the module graph's gap
        script = scripts.get("test") if isinstance(scripts, dict) else None
        if not isinstance(script, str) or not script.strip() or "no test specified" in script:
            continue
        tests.append({"root": PurePosixPath(rel).parent.as_posix() if "/" in rel else ".",
                      "runner": _runner(script, scripts), "declared_in": f"{rel}#scripts.test", "args": []})
    return {"facts": {"tests": sorted(tests, key=lambda test: test["root"])}} if tests else None
