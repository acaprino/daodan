"""Source: uv's model of a Python project from its `uv.lock`, never locking again (`--frozen`), offline.

`commands` describes, for Daodan's container, in each folder holding a `uv.lock` beside a `pyproject.toml`:
`uv export --frozen --all-packages --no-hashes --format pylock.toml` (the local packages with their
directories: units and workspace members) and `uv tree --frozen --depth 1` (each member's direct dependencies,
the version the lock fixes and the group or extra). `UV_OFFLINE` and no interpreter download: uv reads the lock
and writes nothing in the project. Registries are the indexes the exported lock names.
"""
from __future__ import annotations

import posixpath
from pathlib import PurePosixPath
import re
import tomllib
from urllib.parse import urlsplit

NAME, VERSION, RANK = "uv", "0.11.28", "model"  # pinned by the pre-map; the container brings this release
ENV = {"UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never", "UV_NO_PROGRESS": "1"}
EXPORT = ["uv", "export", "--frozen", "--all-packages", "--no-hashes", "--format", "pylock.toml"]
TREE = ["uv", "tree", "--frozen", "--depth", "1"]
LINE = re.compile(r"^(?P<prefix>[\s│├└─]*)(?P<name>[A-Za-z0-9][A-Za-z0-9._-]*)(?:\[[^\]]*\])? v(?P<version>\S+)"
                  r"(?P<rest>.*)$")


def _tree(text: str) -> dict[str, list[dict]]:
    """`{root package: [direct dependency]}` from `uv tree --depth 1`."""
    out, current = {}, None
    for line in text.splitlines():
        match = LINE.match(line)
        if not match:
            continue
        if not match.group("prefix"):
            current = match.group("name")
            out.setdefault(current, [])
            continue
        if current is None:
            continue
        rest, scope = match.group("rest"), "runtime"
        group = re.search(r"\(group: ([^)]+)\)", rest)
        if group:
            scope = "test" if group.group(1).strip() == "test" else "dev"
        if re.search(r"\(extra: ([^)]+)\)", rest):
            scope = "optional"
        out[current].append({"name": match.group("name"), "version": match.group("version"), "scope": scope})
    return out


def commands(context):
    folders = sorted({PurePosixPath(rel).parent.as_posix() if "/" in rel else "." for rel in context.inventory.files
                      if PurePosixPath(rel).name == "pyproject.toml"}, key=lambda f: (f.count("/"), f))
    folders = [f for f in folders if (context.root / f / "uv.lock").is_file()]
    return [{"tool": "uv", "argv": argv, "cwd": folder, "env": ENV, "network": "none"}
            for folder in folders for argv in (EXPORT, TREE)] or None


def read(context, commands, results):
    answers = {(c["cwd"], c["argv"][1]): r for c, r in zip(commands, results)}
    gaps, units, workspaces, dependencies, covered = [], [], [], [], set()
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
        registries = sorted({f"{u.scheme}://{u.netloc}" for p in lock.get("packages") or [] if isinstance(p.get("index"), str)
                             for u in [urlsplit(p["index"])] if u.scheme in ("http", "https")})
        tree = answers[(folder, "tree")]
        trees = _tree(tree["stdout"]) if tree["returncode"] == 0 else {}
        for name in sorted(set(local) | set(trees)):
            unit_root = local.get(name, folder)
            covered.add(unit_root)
            manifest = "pyproject.toml" if unit_root == "." else f"{unit_root}/pyproject.toml"
            inner = {d["name"] for d in trees.get(name, []) if d["name"] in local or d["name"] in trees}
            dependencies += [{"unit": name, "name": d["name"], "resolved": d["version"], "scope": d["scope"],
                              "declared_in": manifest} for d in trees.get(name, []) if d["name"] not in inner]
            unit = {"name": name, "kind": "python-project", "root": unit_root, "manifest": manifest,
                    "registries": registries}
            if tree["returncode"] == 0:  # the edges between units come from `uv tree` alone
                unit["depends_on"] = sorted(inner)
            units.append(unit)
        members = sorted(v for v in local.values() if v != folder)
        if members:
            workspaces.append({"tool": "uv", "root": folder, "members": members})
    return {"facts": {"units": units, "workspace": workspaces, "dependencies": dependencies}, "gaps": gaps}
