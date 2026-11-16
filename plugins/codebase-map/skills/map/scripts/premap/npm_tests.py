"""Source: how a Node package says its tests run, read from its `package.json`, never run.

The `test` script, the one `npm test` runs, and the runner it names: Jest (`jest`, `react-scripts test`), Vitest,
Mocha, Node's own (`node --test`), Bun's (`bun test`), Turborepo (`turbo run test`: the packages' own `test`
scripts, run by turbo); a script that names none of them is npm's to run (`npm`: the runner is whatever it
starts). A script of the package it runs (`npm run test:unit`, `yarn test:unit`, `pnpm test:unit`) is read
through. npm's placeholder (`echo "Error: no test specified" && exit 1`) declares nothing.

Each is a `tests` entry `{root, runner, declared_in, args}`, `args` empty: the command is `npm run` of the script
`declared_in` names, `npm test` for `test`. A package without the script states nothing: the dynamic step's gap,
never a guessed command.

A runner the package's other scripts start in a folder (a `cd` before it) where `test` starts none, as the
frontend's Jest at the root beside a `test` that runs the backend's (`cd backend && jest`), is declared by those
scripts: one entry, the script with the fewest arguments after the runner's name (those it passes to a script it
runs included) that does not watch (`ENDLESS`). Where every one watches, they are a `tests_not_declared` gap
`{path, runner, scripts}`, and none runs. Arguments are not compared otherwise (`jest --selectProjects e2e` beside
a `test` that runs `jest` adds nothing), and a CI workflow is not read.
"""
from __future__ import annotations

import json
from pathlib import PurePosixPath
import posixpath
import re

NAME, VERSION, RANK = "npm-tests", "daodan/premap/v5", "reader"  # v3: Turborepo; v4, v5: the other scripts
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
ENDLESS = {runner: re.compile(f"(?:{pattern})|--inspect-(?:brk|wait)(?![\\w-])") for runner, pattern in {
    # a runner's watch mode, from its documentation, or Node waiting for a debugger: a run that never ends
    "jest": r"--watch(?:All)?(?:=true)?(?=\s|$)|(?<![\w.@-])react-scripts\s+test(?!.*--watchAll=false)",
    "vitest": r"(?<![\w.@-])vitest(?![\w.-])(?!.*(?<![\w-])(?:run|--run)(?![\w-]))",  # no `run`: it watches
    "mocha": r"(?<![\w-])(?:--watch|-w)(?![\w-])",
    "node:test": r"--watch(?:-path)?(?![\w-])",
    "bun": r"--watch(?![\w-])",
    "turbo": r"(?<![\w.@-])turbo\s+watch(?![\w-])"}.items()}


def _starts(script: str, scripts: dict, folder: str = ".", depth: int = 0) -> list[tuple[str, str, str, int]]:
    """The runners the script starts, in order: `(folder, runner, command, arguments)`, the folder from the
    package's through each `cd`, the command that starts it and the number of arguments after its name. Through the
    package's scripts it runs, read while it is in the package's folder, with the arguments it passes them."""
    found = []
    for command in COMMANDS.split(script):
        cd = CD.match(command)
        if cd:
            folder = posixpath.normpath(posixpath.join(folder, cd.group(1)))
            continue
        hits = [(match.start(), [(folder, name, command.strip(), len(command[match.end():].split()))])
                for name, pattern in RUNNERS for match in [pattern.search(command)] if match]
        for match in THROUGH.finditer(command) if depth < 3 and folder == "." else ():
            inner = scripts.get(match.group(1)) if match.group(1) != "test" else None
            if isinstance(inner, str):
                passed = [word for word in command[match.end():].split() if word != "--"]
                hits.append((match.start(), [(where, runner, " ".join([text, *passed]), count + len(passed))
                                             for where, runner, text, count in _starts(inner, scripts, folder,
                                                                                       depth + 1)]))
        found += [item for _, items in sorted(hits, key=lambda hit: hit[0]) for item in items]
    return found


def _others(rel: str, root: str, scripts: dict, test: str | None) -> tuple[list[dict], list[dict]]:
    """The `tests` entries and the `tests_not_declared` gaps of a package's other scripts: see the module's
    docstring."""
    declared = [(where, runner) for name in (("pretest", "test", "posttest") if test else ())
                if isinstance(scripts.get(name), str) for where, runner, _, _ in _starts(scripts[name], scripts)]
    named: dict[tuple[str, str], dict[str, tuple[str, int]]] = {}
    for name, script in sorted(scripts.items()):
        if name not in ("pretest", "test", "posttest") and isinstance(script, str):
            for where, runner, command, count in _starts(script, scripts):
                if (where, runner) not in declared:
                    named.setdefault((where, runner), {}).setdefault(name, (command, count))
    started = ", ".join(f"{runner} in {posixpath.normpath(posixpath.join(root, where))}"
                        for where, runner in dict.fromkeys(declared))
    why = (f"its `test` script does not (it starts {started})" if started else
           "its `test` script names no runner" if test else "the package declares no `test` script")
    tests, gaps = [], []
    for (where, runner), found in sorted(named.items()):
        plain = sorted((count, name) for name, (command, count) in found.items() if not ENDLESS[runner].search(command))
        if plain:
            tests.append({"root": root, "runner": runner, "declared_in": f"{rel}#scripts.{plain[0][1]}", "args": []})
            continue
        where, names = posixpath.normpath(posixpath.join(root, where)), sorted(found)
        shown = ", ".join(names[:6]) + (f" and {len(names) - 6} more" if len(names) > 6 else "")
        gaps.append({"kind": "tests_not_declared", "path": rel, "runner": runner, "scripts": names,
                     "detail": f"{rel}: {shown} start{'s' if len(names) == 1 else ''} {runner} in {where} only in a "
                               f"watch mode or waiting for a debugger, a run that never ends, and {why}: the tests "
                               f"{runner} finds in {where} do not run"})
    return tests, gaps


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
            tests.append({"root": root, "runner": (_starts(script, scripts) or [(".", "npm", "", 0)])[0][1],
                          "declared_in": f"{rel}#scripts.test", "args": []})
        others, unrun = _others(rel, root, scripts, script)
        tests, gaps = [*tests, *others], [*gaps, *unrun]
    if not tests and not gaps:
        return None
    return {"facts": {"tests": sorted(tests, key=lambda test: test["root"])} if tests else {}, "gaps": gaps}
