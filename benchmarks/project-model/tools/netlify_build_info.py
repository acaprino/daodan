"""@netlify/build-info 11.3.1: package manager, JS workspaces, frameworks, build settings, from `build-info <dir>`.

The command prints one JSON per project directory. It is run at the root, then once for every workspace package it
names (`<package dir> --rootDir <root>`, the way the package expects a monorepo to be read). Normalisation: the
unit of a framework is the package name the tool gives (`jsWorkspaces.packages[].name`; the root package name is
read from the fixture's package.json); the evidence is that package's package.json when the tool names the matching
package; the workspace tool is the package manager the tool reports; the workspace members and the units are the
packages of `jsWorkspaces` (the root is not listed by the tool). Build settings and runtimes go to `detail`.
"""
from __future__ import annotations

import json
from pathlib import Path

import _fw

VERSION = "11.3.1"
BIN = _fw.NODE_MODULES / "@netlify" / "build-info" / "bin.js"


def _info(directory: Path, root: Path, work: Path) -> dict:
    argv = ["node", BIN, directory] + (["--rootDir", root] if directory != root else [])
    code, out, err = _fw.execute(argv, work)
    if code != 0:
        raise RuntimeError(f"build-info exited {code}: {(err or out)[-400:]}")
    return json.loads(out)


def run(fixture_dir, work_dir) -> dict:
    root, work = Path(fixture_dir).resolve(), Path(work_dir)
    work.mkdir(parents=True, exist_ok=True)
    top = _info(root, root, work)
    packages = (top.get("jsWorkspaces") or {}).get("packages", [])
    projects = [(".", top)] + [(_fw.posix(p["path"]), _info(root / p["path"], root, work)) for p in packages]
    names = {_fw.posix(p["path"]): p["name"] for p in packages}
    names["."] = _fw.package_name(root, ".")
    frameworks, detail = [], {"settings": {}, "packageManager": (top.get("packageManager") or {}).get("name"),
                              "buildSystems": [b["id"] for b in top.get("buildSystems", [])],
                              "runtimes": [r["id"] for r in top.get("langRuntimes", [])]}
    for directory, info in projects:
        unit = names.get(directory)
        for framework in info.get("frameworks", []):
            matched = bool(framework.get("package"))
            frameworks.append({"name": framework["name"], **({"unit": unit} if unit else {}),
                               **({"evidence": _fw.posix(f"{directory}/package.json")} if matched else {})})
        if info.get("settings"):
            detail["settings"][directory] = info["settings"]
    out = {"frameworks": frameworks, "services": [], "detail": detail}
    workspaces = top.get("jsWorkspaces")
    if workspaces:
        out["workspace"] = {"tool": detail["packageManager"], "root": ".", "members": [_fw.posix(p["path"]) for p in packages]}
        out["units"] = [{"name": p["name"], "kind": "npm-package", "root": _fw.posix(p["path"]),
                         "manifest": _fw.posix(f"{p['path']}/package.json")} for p in packages]
    else:
        out["workspace"] = None
    return out
