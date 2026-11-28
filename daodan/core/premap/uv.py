"""Source: uv's model of a Python project from its `uv.lock`, never locking again (`--frozen`), offline.

`commands` describes, for Daodan's container, in each folder holding a `uv.lock` beside a `pyproject.toml`:
`uv export --frozen --all-packages --no-hashes --format pylock.toml` (the local packages with their
directories: units and workspace members) and `uv tree --frozen --depth 1 --universal` (each member's direct
dependencies: those that are local packages are the edges between units). `UV_OFFLINE` and no interpreter: uv reads
the lock and writes nothing in the project. `--universal` is uv's tree for every Python and platform the lock covers;
without it uv filters the tree by an interpreter of the project's `requires-python` and, finding none, stops ("No
interpreter found for Python >=3.14", Bank of Anthos on Modal, 28 November 2026): the command would need the
project's Python installed only to read its lock. Registries are the origins the exported lock fetches from: each
package's index, its files, its git source or its archive.
"""
from __future__ import annotations

import posixpath
from pathlib import PurePosixPath
import re
import tomllib

from premap.origins import origin

NAME, VERSION, RANK = "uv", "0.11.28", "model"  # pinned by the pre-map; the container brings this release
ENV = {"UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never", "UV_NO_PROGRESS": "1"}
EXPORT = ["uv", "export", "--frozen", "--all-packages", "--no-hashes", "--format", "pylock.toml"]
TREE = ["uv", "tree", "--frozen", "--depth", "1", "--universal"]
LINE = re.compile(r"^(?P<prefix>[\s│├└─]*)(?P<name>[A-Za-z0-9][A-Za-z0-9._-]*)(?:\[[^\]]*\])? v(?P<version>\S+)"
                  r"(?P<rest>.*)$")


VIRTUAL = ""  # in `_tree`, the root of a workspace that is no package: its dependency groups (`zizmor v1 (group: dev)`)


def _tree(text: str) -> dict[str, list[str]]:
    """`{root package: [direct dependency]}` from `uv tree --depth 1`. A root that carries `(group: ...)` is a dependency
    group of a root with no `[project]`, not a package: it and what hangs from it go under `VIRTUAL`."""
    out, current = {}, None
    for line in text.splitlines():
        match = LINE.match(line)
        if not match:
            continue
        if not match.group("prefix"):
            current = VIRTUAL if "(group:" in match.group("rest") else match.group("name")
            out.setdefault(current, [])
            if current == VIRTUAL:
                out[VIRTUAL].append(match.group("name"))
        elif current is not None:
            out[current].append(match.group("name"))
    return out


def commands(context):
    folders = sorted({PurePosixPath(rel).parent.as_posix() if "/" in rel else "." for rel in context.inventory.files
                      if PurePosixPath(rel).name == "pyproject.toml"}, key=lambda f: (f.count("/"), f))
    folders = [f for f in folders if (context.root / f / "uv.lock").is_file()]
    return [{"tool": "uv", "argv": argv, "cwd": folder, "env": ENV, "network": "none"}
            for folder in folders for argv in (EXPORT, TREE)] or None


def read(context, commands, results):
    answers = {(c["cwd"], c["argv"][1]): r for c, r in zip(commands, results)}
    gaps, units, workspaces, covered = [], [], [], set()
    for folder in sorted({c["cwd"] for c in commands}, key=lambda f: (f.count("/"), f)):
        if folder in covered:
            continue
        failed = [f"uv {verb}: {(answers[(folder, verb)]['stderr'] or '').strip()[-300:]}" for verb in ("export", "tree")
                  if answers[(folder, verb)]["returncode"] != 0]
        if failed:
            gaps.append({"kind": "model_failed", "path": folder, "detail": "; ".join(failed)})
        export = answers[(folder, "export")]
        if export["returncode"] != 0:
            continue
        lock = tomllib.loads(export["stdout"])
        local = {p["name"]: posixpath.normpath(posixpath.join(folder, p["directory"]["path"]))
                 for p in lock.get("packages") or [] if isinstance(p.get("directory"), dict)}
        packages = [p for p in lock.get("packages") or [] if isinstance(p, dict)]
        registries = sorted({o for p in packages for url in [p.get("index"), *(
            t.get("url") for t in [p.get("vcs"), p.get("archive"), p.get("sdist"), *(p.get("wheels") or [])]
            if isinstance(t, dict))] if url for o in [origin(url)] if o})
        tree = answers[(folder, "tree")]
        trees = _tree(tree["stdout"]) if tree["returncode"] == 0 else {}
        virtual = trees.pop(VIRTUAL, None)
        for name in sorted(set(local) | set(trees)):
            unit_root = local.get(name, folder)
            covered.add(unit_root)
            manifest = "pyproject.toml" if unit_root == "." else f"{unit_root}/pyproject.toml"
            inner = {d for d in trees.get(name, []) if d in local or d in trees}
            unit = {"name": name, "kind": "python-project", "root": unit_root, "manifest": manifest,
                    "registries": registries}
            if tree["returncode"] == 0:  # the edges between units come from `uv tree` alone
                unit["depends_on"] = sorted(inner)
            units.append(unit)
        if virtual is not None and folder not in local.values():  # the root names no package: one unit, with no name
            covered.add(folder)
            units.append({"kind": "python-project", "root": folder, "registries": registries,
                          "manifest": "pyproject.toml" if folder == "." else f"{folder}/pyproject.toml",
                          "depends_on": sorted({d for d in virtual if d in local or d in trees})})
        members = sorted(v for v in local.values() if v != folder)
        if members:
            workspaces.append({"tool": "uv", "root": folder, "members": members})
    return {"facts": {"units": units, "workspace": workspaces}, "gaps": gaps}
