"""The commands the user and the assistant state for a folder of the project: what runs its tests, starts or builds it.

They live in `commands.json` in the per-user shared folder (`egress.shared_cache_dir`), never in the project, as the
answers of `egress` do: `{<project>: [entry]}`, the project named as `egress.project_of` names it, the file written
whole under `egress.locked`. An entry is `{kind, root, argv, by, grade}`, with `port`, `surface` (one of
`registry_build.SURFACES`) and, for `tests`, the `runner` where given: `kind` one of `KINDS`, `root` the folder from the
project's root (`.` the root), `argv` the command's words. `by` says who stated it, `user` (grade `confermato`) or
`assistant` (`proposto`); an entry the user confirmed keeps `proposed_by`. One entry per kind, folder and, for
`tests`, runner: a new one takes its place, but the assistant never takes the place of the user's.

`merged` puts them before the pre-map's entries of the same kind, which `dynamic.declared` and `dynamic.app.plan` rank
by `dynamic.PRECEDENCE` (user, assistant, CI). A command runs only in the container, as every other does, and the hosts
it reaches are approved only in the app (`egress`). The app sets, confirms and removes (`/api/app/command`, `user`);
MCP only proposes (`codebase_map_set_command`, always `assistant`).
"""
from __future__ import annotations

import json
import posixpath
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import egress  # noqa: E402

FILE = "commands.json"
KINDS = ("tests", "starts", "builds")
GRADES = {"user": "confermato", "assistant": "proposto"}


def _root(project: str, root) -> str:
    """`root` as the folder from the project's root, refused when it is no relative path inside the project."""
    if not isinstance(root, str) or not root.strip() or Path(root).is_absolute() or root.startswith(("/", "\\")):
        raise ValueError(f"root must be a folder of the project, relative to its root: {root!r}")
    rel = posixpath.normpath(root.replace("\\", "/"))
    base = Path(project).resolve()
    if rel == ".." or rel.startswith("../") or not (base / rel).resolve().is_relative_to(base):
        raise ValueError(f"root is outside the project: {root!r}")
    return rel


def _runner(argv: list[str]) -> str:
    """The test runner a command starts: the longest an observer declares that its words begin with (the CI's rule,
    `premap.renovate._runners`), else its first word."""
    from premap import renovate
    return next((name for name in renovate._runners() if argv[:len(name.split())] == name.split()), argv[0])


def entry(project: str, given: dict, by: str) -> dict:
    """The entry `given` as it is kept, checked: a ValueError names what is wrong."""
    if by not in GRADES:
        raise ValueError(f"by must be one of {', '.join(GRADES)}: {by!r}")
    if not isinstance(given, dict):
        raise ValueError("a command is an object")
    kind, argv = given.get("kind"), given.get("argv")
    if kind not in KINDS:
        raise ValueError(f"kind must be one of {', '.join(KINDS)}: {kind!r}")
    if not isinstance(argv, list) or not argv or not all(isinstance(word, str) and word for word in argv):
        raise ValueError("argv must be a nonempty list of nonempty strings")
    from registry_build import SURFACES
    port, surface = given.get("port"), given.get("surface")
    if port is not None and (type(port) is not int or not 0 < port < 65536):
        raise ValueError(f"port must be a number from 1 to 65535: {port!r}")
    if surface is not None and surface not in SURFACES:
        raise ValueError(f"surface must be one of {', '.join(SURFACES)}: {surface!r}")
    kept = {"kind": kind, "root": _root(project, given.get("root", ".")), "argv": list(argv), "by": by,
            "grade": GRADES[by]}
    if kind == "tests":
        kept["runner"] = given["runner"] if isinstance(given.get("runner"), str) and given["runner"] else _runner(argv)
    return {**kept, **({"port": port} if port is not None else {}), **({"surface": surface} if surface else {})}


def _key(entry: dict) -> tuple:
    return entry["kind"], entry["root"], entry.get("runner")


def _read() -> dict:
    try:
        held = json.loads((egress.shared_cache_dir() / FILE).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return held if isinstance(held, dict) else {}


def listed(project: str) -> list[dict]:
    """The project's commands, as kept; an entry that is not well formed is left out."""
    rows = _read().get(project)
    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, dict) and row.get("kind") in KINDS
            and isinstance(row.get("root"), str) and isinstance(row.get("argv"), list) and row.get("by") in GRADES]


def _change(project: str, change) -> list[dict]:
    """The project's commands after `change(rows) -> rows`, written whole under the lock."""
    with egress.locked():
        held = _read()
        rows = change(listed(project))
        if rows:
            held[project] = rows
        else:
            held.pop(project, None)
        egress._replace(egress.shared_cache_dir() / FILE, held)
    return rows


def set(project: str, given: dict, by: str) -> list[dict]:  # noqa: A001 - the module's verb, `commands.set`
    """Keep the command `given`, stated `by` the user or the assistant, in place of the one of the same kind, folder
    and runner; the assistant's never replaces the user's. The project's commands after it."""
    kept = entry(project, given, by)

    def change(rows: list[dict]) -> list[dict]:
        there = next((row for row in rows if _key(row) == _key(kept)), None)
        if there is not None and there["by"] == "user" and by == "assistant":
            raise ValueError(f"the user set the {kept['kind']} command of {kept['root']}: the assistant does not "
                             "replace it")
        return [*(row for row in rows if _key(row) != _key(kept)), kept]
    return _change(project, change)


def _match(rows: list[dict], kind: str, root: str, runner: str | None) -> dict:
    found = [row for row in rows if row["kind"] == kind and row["root"] == root
             and (runner is None or row.get("runner") == runner)]
    if len(found) != 1:
        raise ValueError(f"no single {kind} command of {root} is kept" + (f" for {runner}" if runner else ""))
    return found[0]


def confirm(project: str, kind: str, root: str, runner: str | None = None) -> list[dict]:
    """The user confirms the assistant's command: it is the user's (`confermato`) and keeps who proposed it."""
    root = _root(project, root)

    def change(rows: list[dict]) -> list[dict]:
        row = _match(rows, kind, root, runner)
        if row["by"] != "assistant":
            raise ValueError(f"the {kind} command of {root} is the user's: there is nothing to confirm")
        return [{**other, "by": "user", "grade": GRADES["user"], "proposed_by": "assistant"} if other is row else other
                for other in rows]
    return _change(project, change)


def remove(project: str, kind: str, root: str, runner: str | None = None) -> list[dict]:
    """The command is no longer kept: the pre-map's, or the tool's convention, run again."""
    root = _root(project, root)

    def change(rows: list[dict]) -> list[dict]:
        row = _match(rows, kind, root, runner)
        return [other for other in rows if other is not row]
    return _change(project, change)


def merged(record: dict, project: str) -> dict:
    """The pre-map `record` with the project's commands before its own entries of the same kind, in the pre-map's form:
    a `starts` or `builds` entry runs its `argv` (`mode` `start` or `build`, `runner` its first word, no build before
    it), and `declared_in` names this file. The record itself is not changed."""
    rows = sorted(listed(project), key=lambda row: list(GRADES).index(row["by"]))
    if not rows:
        return record
    merged = dict(record)
    for kind in KINDS:
        mine = [row for row in rows if row["kind"] == kind]
        if not mine:
            continue
        shaped = [{key: value for key, value in row.items() if key != "kind"} | {"declared_in": FILE} |
                  ({} if kind == "tests" else {"mode": "start" if kind == "starts" else "build",
                                               "runner": row["argv"][0], "port": row.get("port"),
                                               "needs_build": False})
                  for row in mine]
        merged[kind] = [*shaped, *(record.get(kind) or ())]
    return merged
