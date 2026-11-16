"""A Python file Daodan's interpreter rejects, read by the Python its project states.

The standard library's grammar is the running interpreter's (`python.py`): a file in syntax newer than it (3.14's
`except A, B:`, PEP 758) does not parse. Where its folder states a newer Python (`stated`, as uv reads it: the
nearest version file, else the nearest requires-python; `newer`), the interpreter uv provides for that statement
(`engine_tools.python_environment`, an environment without packages) parses it: started isolated and without
`site` (`-I -S`) in a folder outside the project, this module, run as a script, reads the sources on its standard
input and writes each one's tree (`dump`), which Daodan's `ast` rebuilds (`tree`). No source is imported or run. A
node type Daodan's `ast` does not know (3.14's `TemplateStr`) keeps its base class and its fields, which are walked.
`reread` names the interpreter that parsed a file, or says why none did: no interpreter for the statement, or that
interpreter rejects the file too.

    python -I -S python_newer.py < [{"rel": ..., "text": ...}, ...] > {"python": its version}, a line per source
"""
from __future__ import annotations

import ast
import json
import os
import sys
from pathlib import Path

_KINDS: dict = {}  # the node types Daodan's `ast` lacks, by name and base


def dump(node):
    """A tree as JSON: a node is `{"_": its type, "^": its base, field or position: value}`; a constant JSON holds
    no form of (bytes, complex, `...`) is `{"=": its literal}`."""
    if isinstance(node, ast.AST):
        out = {"_": type(node).__name__, "^": type(node).__mro__[1].__name__}
        for name in (*node._fields, *node._attributes):
            if hasattr(node, name):
                out[name] = dump(getattr(node, name))
        return out
    if isinstance(node, list):
        return [dump(item) for item in node]
    if node is ...:
        return {"=": "..."}
    return {"=": repr(node)} if isinstance(node, (bytes, complex)) else node


def tree(data):
    """The tree `dump` wrote, in Daodan's `ast`."""
    if isinstance(data, list):
        return [tree(item) for item in data]
    if not isinstance(data, dict):
        return data
    if "=" in data:
        return ast.literal_eval(data["="])
    kind = getattr(ast, data["_"], None)
    if not (isinstance(kind, type) and issubclass(kind, ast.AST)):
        if (data["_"], data["^"]) not in _KINDS:
            base = getattr(ast, data["^"], None)
            base = base if isinstance(base, type) and issubclass(base, ast.AST) else ast.AST
            fields = tuple(name for name in data if name not in ("_", "^", *base._attributes))
            _KINDS[(data["_"], data["^"])] = type(data["_"], (base,), {"_fields": fields})
        kind = _KINDS[(data["_"], data["^"])]
    node = kind.__new__(kind)
    for name in (*kind._fields, *kind._attributes):
        if name in data:
            setattr(node, name, tree(data[name]))
        elif name in kind._fields:  # a field the newer grammar dropped: empty, as Daodan's `ast` would leave it
            listed = str(getattr(kind, "_field_types", {}).get(name, "")).startswith("list")
            setattr(node, name, [] if listed else None)
    return node


def _first(path: Path) -> str | None:
    """The first version a version file lists."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError):
        return None
    return next((line.strip() for line in lines if line.strip() and not line.lstrip().startswith("#")), None)


def stated(root: Path, folder: str) -> dict | None:
    """The Python the project states for `folder` (from the snapshot's root) as uv reads it: of the version files at
    or above it and the requires-python of the pyproject files there, the nearest version file, else the nearest
    requires-python (`dynamic.python.stated_python`)."""
    import tomllib
    from pathlib import PurePosixPath
    from dynamic import python as observer  # the rule the analyzers read the pre-map's statements by
    here, items = PurePosixPath(folder or "."), []
    for place in (here, *here.parents):
        prefix = "" if str(place) == "." else f"{place}/"
        for name in observer.VERSION_FILES:
            version = _first(Path(root) / f"{prefix}{name}")
            if version:
                items.append({"version": version, "declared_in": f"{prefix}{name}"})
        try:
            project = tomllib.loads((Path(root) / f"{prefix}pyproject.toml").read_text(encoding="utf-8")).get("project")
        except (OSError, UnicodeError, ValueError):
            project = None
        if isinstance(project, dict) and isinstance(project.get("requires-python"), str):
            items.append({"version": project["requires-python"], "declared_in": f"{prefix}pyproject.toml"})
    return observer.stated_python(items, str(here))


def newer(version: str) -> bool:
    """Whether a stated Python excludes Daodan's interpreter and admits a newer one: only a newer grammar accepts
    what Daodan's rejects."""
    from dynamic import python as observer
    own = sys.version_info[:3]
    later = [(3, minor, patch) for minor in range(own[1] + 1, 40) for patch in (0, 99)] + [(4, 0, 0)]
    return observer.admits(version, own) is False and any(observer.admits(version, other) for other in later)


def _interpreter(root: Path, version: str) -> tuple[Path | None, str | None]:
    """The interpreter uv provides for a stated Python, as `uv sync` would, else why there is none."""
    import contextlib
    import shutil
    import subprocess
    import engine_tools
    if shutil.which("uv") is None:
        return None, "uv is not installed: Daodan asks it for the Python a project states"
    try:
        with contextlib.redirect_stdout(sys.stderr):  # its progress is no server's output
            environment = engine_tools.python_environment(root, [], version)
    except (OSError, subprocess.SubprocessError) as error:
        return None, str(error)[:400]
    if environment is None:
        return None, f"less than {engine_tools.ENVIRONMENT_MIN_FREE // 2**30} GB free in Daodan's shared directory"
    return environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python"), None


def _parsed(python: Path, sources: list[tuple[str, str]]) -> tuple[str, dict, str | None]:
    """This module run by `python` over `sources`: its version, each source's row, and why it failed when it did."""
    import subprocess
    try:
        done = subprocess.run([str(python), "-I", "-S", str(Path(__file__).resolve())], cwd=python.parent,
                              input=json.dumps([{"rel": rel, "text": text} for rel, text in sources]),
                              capture_output=True, text=True, timeout=600)
    except (OSError, subprocess.SubprocessError) as error:
        return "", {}, f"{python} did not run: {error}"
    lines = done.stdout.splitlines()
    try:
        ran, rows = json.loads(lines[0])["python"], [json.loads(line) for line in lines[1:]]
    except (IndexError, KeyError, TypeError, ValueError):
        return "", {}, f"{python} ended with code {done.returncode}: {done.stderr.strip()[-300:]}"
    return ran, {row["rel"]: row for row in rows}, None


def reread(root: Path, sources: list[tuple[str, str]]) -> dict[str, tuple[ast.Module | None, str]]:
    """`{rel: (tree, note)}` of the sources Daodan's interpreter rejected (`(rel, text)`) whose folder states a
    newer Python: the tree its interpreter parsed and the note naming it; without a tree, the note says why. A
    source whose folder states no newer Python is left out."""
    import collections
    import platform
    import posixpath
    groups = collections.defaultdict(list)
    for rel, text in sources:
        found = stated(root, posixpath.dirname(rel))
        if found and newer(str(found["version"])):
            groups[(str(found["version"]), found["declared_in"])].append((rel, text))
    out = {}
    for (version, declared_in), group in groups.items():
        python, cause = _interpreter(root, version)
        ran, rows, failed = _parsed(python, group) if python else ("", {}, None)
        missing = (f"the project states Python {version} ({declared_in}), newer than Daodan's "
                   f"{platform.python_version()}, and no interpreter for it is available: {cause}" if cause else
                   f"the Python uv provides for {version} ({declared_in}) did not parse it: {failed}")
        for rel, _text in group:
            row, note = rows.get(rel) or {}, missing
            if "tree" in row:
                try:
                    out[rel] = (tree(row["tree"]), f"parsed by Python {ran}, the interpreter uv provides for {version}"
                                                   f" ({declared_in})")
                    continue
                except (KeyError, TypeError, ValueError, SyntaxError, RecursionError) as error:
                    note = f"the tree Python {ran} parsed is not read: {type(error).__name__}: {error}"
            elif "error" in row:
                note = f"Python {ran}, the one {declared_in} states ({version}), rejects it too: {row['error']}"
            out[rel] = (None, note)
    return out


def main() -> None:
    """Each source on the standard input parsed, written as its tree (`dump`), after this interpreter's version."""
    import platform
    import warnings
    warnings.simplefilter("ignore")  # a source's SyntaxWarning (an invalid escape) is not this pass's
    print(json.dumps({"python": platform.python_version()}))
    for item in json.loads(sys.stdin.read()):
        try:
            line = json.dumps({"rel": item["rel"], "tree": dump(ast.parse(item["text"]))})
        except SyntaxError as error:
            line = json.dumps({"rel": item["rel"], "error": f"{error.msg} at line {error.lineno}"})
        except (ValueError, RecursionError, MemoryError) as error:
            line = json.dumps({"rel": item["rel"], "error": f"{type(error).__name__}: {error}"})
        print(line)


if __name__ == "__main__":
    main()
