"""Source: how a Node package says it starts and builds, read from its `package.json`, never run.

`starts` entries `{root, mode, runner, argv, surface, declared_in, port, needs_build}` for the `dev` and `start`
scripts, `builds` entries `{root, runner, argv, declared_in}` for `build`; `argv` is the command, `<runner> run
<script>`, the one the package declares (spec of the project's interfaces, section 5), and `surface` is `web`: a script
opens an HTTP address (`dynamic.app`). The runner is the one of the nearest lockfile, the folder's or above it
(`pnpm-lock.yaml`, `yarn.lock`, `bun.lock`, `bun.lockb`), else the one the nearest `packageManager` names (the field
corepack reads; the restore reads it too, `preparation.node_restores`), else npm.

Each script is read from its syntax tree (`premap/shell.py`, tree-sitter bash: no official tool reads an npm script,
and a regular expression is not for a language with a grammar). `port` is a decimal literal: `--port N`,
`--port=N`, `-p N` or `PORT=N`, never a default. `needs_build` is true for the closed table of production servers that read compiled
output (`next start`, `nuxt start`, `vite preview`, `astro preview`) and for `node` run on a file the snapshot does
not hold (built output is no part of the checkout); a build the package does not declare is a
`build_command_missing` gap. A script that only runs a test runner or a checker, or names a CLI that wants a
subcommand and has none (`tauri`), is no start: a `no_start_command` gap says which.

shortcut: only `node`'s file is checked, its first argument that is no flag; a script that runs another one (`npm run serve`) is not followed, and a wrapper (`cross-env NODE_ENV=x
next start`) hides the table's command and its port, and `cross-env X=1 jest --watch` counts as a start (the
exploration's failure gaps carry the log); the executor ignores the module's `toolchains`. Upgrade when a project needs it.
"""
from __future__ import annotations

import json
import posixpath
from pathlib import Path, PurePosixPath

from premap import shell

NAME, VERSION, RANK = "npm-start", "daodan/premap/v2", "reader"
MODES = ("dev", "start")
LOCKFILES = (("pnpm-lock.yaml", "pnpm"), ("yarn.lock", "yarn"), ("bun.lock", "bun"), ("bun.lockb", "bun"),
             ("package-lock.json", "npm"), ("npm-shrinkwrap.json", "npm"))
SURFACE = "web"  # a package script opens an HTTP address: the `web` surface (`dynamic.app.WEB`)
BUILT_FIRST = {("next", "start"), ("nuxt", "start"), ("vite", "preview"), ("astro", "preview")}
NOT_STARTS = {"jest", "vitest", "mocha", "ava", "tap", "cypress",  # test runners
              "tsc", "vue-tsc", "svelte-check", "eslint", "stylelint", "prettier"}  # checkers
NEEDS_SUBCOMMAND = {"tauri", "wails"}


def _commands(script: str) -> list[tuple[dict, str, list[str]]] | None:
    """The commands of a script (`shell.commands`): `(assignments, name, arguments)`, the program's name without its
    folder; None where the bash grammar is not available."""
    found = shell.commands(script)
    return None if found is None else [(assigned, PurePosixPath(words[0]).name, words[1:]) for assigned, words in found]


def _subcommand(arguments: list[str]) -> str | None:
    return next((text for text in arguments if not text.startswith("-")), None)


def _is_start(name: str, arguments: list[str]) -> bool:
    return not (name in NOT_STARTS or _subcommand(arguments) == "test" or (name == "node" and "--test" in arguments)
                or (name in NEEDS_SUBCOMMAND and not arguments))


def _unbuilt(commands, root: str, context) -> bool:
    """Whether `node` runs a file of the module that the snapshot does not hold (a literal path, no variable)."""
    for _, name, arguments in commands:
        target = _subcommand(arguments) if name == "node" else None
        if target and not any(mark in target for mark in "$*?"):
            path = posixpath.normpath(posixpath.join(root, target))
            if path not in context.inventory.headers and path not in context.inventory.directories:
                return True
    return False


def _port(commands) -> int | None:
    for assigned, _, arguments in commands:
        if assigned.get("PORT", "").isdigit():
            return int(assigned["PORT"])
        for index, text in enumerate(arguments):
            if text.startswith("--port=") and text[7:].isdigit():
                return int(text[7:])
            if text in ("--port", "-p") and index + 1 < len(arguments) and arguments[index + 1].isdigit():
                return int(arguments[index + 1])
    return None


def _runner(root: str, context, named: dict[str, str]) -> str:
    """The lockfile's executor, else the manager `named` (folder -> the one its `packageManager` names) gives, in the
    folder or the nearest above it; the snapshot holds no `yarn.lock` or `bun.lockb`, so each is looked for on disk, in
    a folder the snapshot holds (`origins.disk_text`)."""
    folder = root
    while True:
        for lockfile, runner in LOCKFILES:
            rel = lockfile if folder == "." else f"{folder}/{lockfile}"
            if rel in context.inventory.headers or (folder in context.inventory.directories
                                                    and (Path(context.root) / rel).is_file()):
                return runner
        if folder in named:
            return named[folder]
        if folder == ".":
            return "npm"
        folder = PurePosixPath(folder).parent.as_posix()


def _manifests(context) -> dict[str, dict]:
    """Each readable `package.json` of the snapshot by its folder (`.` the root), in the order of their paths."""
    found = {}
    for rel in sorted(context.inventory.files):
        if PurePosixPath(rel).name != "package.json":
            continue
        try:
            manifest = json.loads(context.inventory.text(rel))
        except ValueError:
            continue  # an unreadable manifest is the module graph's gap
        if isinstance(manifest, dict):
            found[PurePosixPath(rel).parent.as_posix() if "/" in rel else "."] = manifest
    return found


def run(context):
    starts, builds, gaps = [], [], []
    manifests = _manifests(context)
    named = {folder: name for folder, manifest in manifests.items()  # `<name>@<version>`, as corepack writes it
             for name in [str(manifest.get("packageManager") or "").split("@")[0].strip()] if name}
    for root, manifest in manifests.items():
        rel = "package.json" if root == "." else f"{root}/package.json"
        scripts = manifest.get("scripts")
        if not isinstance(scripts, dict):
            continue
        runner = _runner(root, context, named)
        if isinstance(scripts.get("build"), str):
            builds.append({"root": root, "runner": runner, "argv": [runner, "run", "build"],
                           "declared_in": f"{rel}#scripts.build"})
        for mode in MODES:
            script = scripts.get(mode)
            if not isinstance(script, str) or not script.strip():
                continue
            commands = _commands(script)
            if commands is None:
                gaps.append({"kind": "shell_grammar_unavailable", "path": rel,
                             "detail": f"{rel}: the bash grammar is not available: the `{mode}` script is not read"})
                continue
            if not any(_is_start(name, arguments) for _, name, arguments in commands):
                gaps.append({"kind": "no_start_command", "path": rel, "script": mode,
                             "detail": f"{rel}: the `{mode}` script runs only a test runner, a checker or a CLI "
                                       "without its subcommand: it starts nothing"})
                continue
            starts.append({"root": root, "mode": mode, "runner": runner, "argv": [runner, "run", mode],
                           "surface": SURFACE, "declared_in": f"{rel}#scripts.{mode}", "port": _port(commands),
                           "needs_build": _unbuilt(commands, root, context) or any(
                               (name, _subcommand(arguments)) in BUILT_FIRST for _, name, arguments in commands)})
    for entry in starts:
        if entry["needs_build"] and not any(build["root"] == entry["root"] for build in builds):
            path = entry["declared_in"].split("#")[0]
            gaps.append({"kind": "build_command_missing", "path": path,
                         "detail": f"{entry['declared_in']} starts a server that reads compiled output and the "
                                   "package declares no `build` script"})
    if not starts and not builds and not gaps:
        return None
    facts = {key: sorted(value, key=lambda item: (item["root"], item["declared_in"]))
             for key, value in (("starts", starts), ("builds", builds)) if value}
    return {"facts": facts, "gaps": gaps}
