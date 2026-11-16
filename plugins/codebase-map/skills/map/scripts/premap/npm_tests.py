"""Source: how a Node package says its tests run, read from its `package.json`, never run.

The `test` script, the one `npm test` runs, and the runner it names: Jest (`jest`, `react-scripts test`), Vitest,
Mocha, Node's own (`node --test`), Bun's (`bun test`), Turborepo (`turbo run test`: the packages' own `test`
scripts, run by turbo); a script that names none of them is npm's to run (`npm`: the runner is whatever it
starts). A script of the package it runs (`npm run test:unit`, `yarn test:unit`, `pnpm test:unit`) is read
through. npm's placeholder (`echo "Error: no test specified" && exit 1`) declares nothing.

Each is a `tests` entry `{root, runner, declared_in, args}`, `args` empty: the command is `npm test`. A package
without the script states nothing: the dynamic step's gap, never a guessed command.

The package's other scripts that start a runner in a folder (a `cd` before it) where the `test` script starts
none, as the frontend's Jest at the root beside a `test` that runs the backend's (`cd backend && jest`), are a
`tests_not_declared` gap `{path, runner, scripts}`: their names alone say they run tests, and they never run.
Arguments are not compared (`jest --selectProjects e2e` beside a `test` that runs `jest` says nothing), and a
CI workflow is not read: a script a workflow runs is named here too.
"""
from __future__ import annotations

import json
from pathlib import PurePosixPath
import posixpath
import re

NAME, VERSION, RANK = "npm-tests", "daodan/premap/v4", "reader"  # v2: Bun; v3: Turborepo; v4: tests_not_declared
WORD = r"(?<![\w.@-]){}(?![\w.-])"  # a program's name alone or at the end of its path, not a part of another's
RUNNERS = (("jest", re.compile(WORD.format("jest") + "|" + WORD.format(r"react-scripts\s+test"))),
           ("vitest", re.compile(WORD.format("vitest"))),
           ("mocha", re.compile(WORD.format("mocha"))),
           ("node:test", re.compile(WORD.format(r"node\s(?:[^&|;]*\s)?--test"))),
           ("bun", re.compile(WORD.format(r"bun\s+test"))),
           ("turbo", re.compile(WORD.format(r"turbo(?:\s+[^\s&|;]+)*?\s+test"))))  # turbo runs a `test` task
THROUGH = re.compile(r"(?<![\w./@-])(?:npm|pnpm|yarn)\s+(?:run\s+)?([\w:.-]+)")  # a script that runs another
COMMANDS = re.compile(r"&&|\|\||[;|]")
CD = re.compile(r"^\s*cd\s+([^\s&|;]+)\s*$")


def _starts(script: str, scripts: dict, folder: str = ".", depth: int = 0) -> list[tuple[str, str]]:
    """The runners the script starts, in order, each with its folder (from the package's, through each `cd`):
    through the package's scripts it runs, read while it is in the package's folder."""
    found = []
    for command in COMMANDS.split(script):
        cd = CD.match(command)
        if cd:
            folder = posixpath.normpath(posixpath.join(folder, cd.group(1)))
            continue
        hits = [(match.start(), [(folder, name)]) for name, pattern in RUNNERS for match in [pattern.search(command)]
                if match]
        for match in THROUGH.finditer(command) if depth < 3 and folder == "." else ():
            inner = scripts.get(match.group(1)) if match.group(1) != "test" else None
            if isinstance(inner, str):
                hits.append((match.start(), _starts(inner, scripts, folder, depth + 1)))
        found += [pair for _, pairs in sorted(hits) for pair in pairs]
    return found


def _unrun(rel: str, root: str, scripts: dict, test: str | None) -> list[dict]:
    """The `tests_not_declared` gaps of a package: see the module's docstring."""
    declared = [pair for name in (("pretest", "test", "posttest") if test else ())
                for pair in _starts(scripts.get(name) if isinstance(scripts.get(name), str) else "", scripts)]
    named: dict[tuple[str, str], list[str]] = {}
    for name, script in sorted(scripts.items()):
        if name not in ("pretest", "test", "posttest") and isinstance(script, str):
            for pair in dict.fromkeys(_starts(script, scripts)):
                if pair not in declared:
                    named.setdefault(pair, []).append(name)
    started = ", ".join(f"{runner} in {posixpath.normpath(posixpath.join(root, where))}"
                        for where, runner in dict.fromkeys(declared))
    why = (f"its `test` script does not (it starts {started})" if started else
           "its `test` script names no runner" if test else "the package declares no `test` script")
    gaps = []
    for (where, runner), names in sorted(named.items()):
        where = posixpath.normpath(posixpath.join(root, where))
        shown = ", ".join(names[:6]) + (f" and {len(names) - 6} more" if len(names) > 6 else "")
        gaps.append({"kind": "tests_not_declared", "path": rel, "runner": runner, "scripts": names,
                     "detail": f"{rel}: {shown} start{'s' if len(names) == 1 else ''} {runner} in {where} and "
                               f"{why}: the dynamic step runs `npm test` alone, so the tests {runner} finds in "
                               f"{where} do not run"})
    return gaps


def run(context):
    tests, gaps = [], []
    for rel in context.inventory.files:
        if PurePosixPath(rel).name != "package.json":
            continue
        try:
            scripts = json.loads(context.inventory.text(rel)).get("scripts")
        except (ValueError, AttributeError):
            continue  # an unreadable manifest is the module graph's gap
        if not isinstance(scripts, dict):
            continue
        root = PurePosixPath(rel).parent.as_posix() if "/" in rel else "."
        script = scripts.get("test")
        if not isinstance(script, str) or not script.strip() or "no test specified" in script:
            script = None
        else:
            tests.append({"root": root, "runner": (_starts(script, scripts) or [(".", "npm")])[0][1],
                          "declared_in": f"{rel}#scripts.test", "args": []})
        gaps += _unrun(rel, root, scripts, script)
    if not tests and not gaps:
        return None
    return {"facts": {"tests": sorted(tests, key=lambda test: test["root"])} if tests else {}, "gaps": gaps}
