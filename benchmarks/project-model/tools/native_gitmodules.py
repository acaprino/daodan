"""Git submodules: what `git config -f .gitmodules --list` declares (it reads the file and needs no repository),
whether each folder is present, and, inside a Git checkout, the commit its gitlink pins (`git ls-files --stage`,
mode 160000). A submodule is an excluded folder and a dependency named by its URL as written.
"""
from __future__ import annotations

from pathlib import Path

import native_common as common

VERSION = "git of the image (Debian 12: 2.39; Ubuntu 24.04: 2.43)"
VERSION_COMMAND = ["git", "--version"]
TRIGGERS = (".gitmodules",)
COMMAND = "git config -f .gitmodules --list; git ls-files --stage -- <path>"


def run(fixture_dir, work_dir) -> dict:
    root = Path(fixture_dir)
    if not (root / ".gitmodules").is_file():
        return {}
    done = common.run(["git", "config", "-f", ".gitmodules", "--list"], root, name="git config -f .gitmodules --list")
    if done.returncode != 0:
        common.NOTES.update(errors=[common.error_of(done)], raw={})
        return {}
    modules: dict[str, dict] = {}
    for line in done.stdout.splitlines():
        key, _, value = line.partition("=")
        if not key.startswith("submodule.") or "." not in key[len("submodule."):]:
            continue
        name, _, field = key[len("submodule."):].rpartition(".")
        modules.setdefault(name, {})[field] = value
    inside = common.run(["git", "rev-parse", "--show-toplevel"], root, name="git rev-parse --show-toplevel")
    checkout = inside.returncode == 0 and Path(inside.stdout.strip()).resolve() == root.resolve()
    excluded, dependencies, raw = [], [], {"present": {}, "checkout": checkout}
    for name, fields in modules.items():
        path = fields.get("path") or name
        folder = root / path
        raw["present"][path] = folder.is_dir() and any(folder.iterdir())
        excluded.append({"path": path.rstrip("/") + "/", "why": "submodule"})
        item = {"name": fields.get("url"), "declared": fields.get("branch"), "declared_in": f".gitmodules#submodule.{path}"}
        if checkout:
            staged = common.run(["git", "ls-files", "--stage", "--", path], root, name="git ls-files --stage")
            parts = staged.stdout.split()
            item["resolved"] = parts[1] if len(parts) >= 2 and parts[0] == "160000" else None
        dependencies.append(item)
    common.NOTES.update(errors=[], raw=raw)
    return {"excluded": excluded, "dependencies": dependencies}
