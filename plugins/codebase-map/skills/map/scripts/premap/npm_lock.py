"""Source: what `package.json` and `package-lock.json` declare about installing, read from the files, never run.

Daodan installs a unit's packages with `npm ci --ignore-scripts`: the install scripts a `package.json` declares
(`preinstall`, `install`, `postinstall`, `prepare`) and those of the dependencies the lockfile marks
`hasInstallScript` are a `not_executed` gap. The registries an install reaches are the origins of the
lockfile's `resolved` URLs, on the unit whose folder holds the lockfile.
"""
from __future__ import annotations

import json
from pathlib import PurePosixPath
from urllib.parse import urlsplit

NAME, VERSION, RANK = "npm-files", "daodan/premap/v1", "reader"
INSTALL_SCRIPTS = ("preinstall", "install", "postinstall", "prepare")


def _json(context, rel: str) -> dict:
    try:
        value = json.loads(context.inventory.text(rel)) if rel in context.inventory.headers else {}
    except ValueError:
        return {}  # an unreadable manifest is the module graph's gap
    return value if isinstance(value, dict) else {}


def run(context):
    manifests = [rel for rel in context.inventory.files if PurePosixPath(rel).name == "package.json"]
    if not manifests:
        return None
    units, gaps = [], []
    for rel in manifests:
        root = PurePosixPath(rel).parent.as_posix() if "/" in rel else "."
        scripts = _json(context, rel).get("scripts")
        own = [f"scripts.{k}" for k in INSTALL_SCRIPTS if isinstance(scripts, dict) and k in scripts]
        lock_rel = "package-lock.json" if root == "." else f"{root}/package-lock.json"
        packages = _json(context, lock_rel).get("packages")
        packages = packages if isinstance(packages, dict) else {}
        theirs = sorted(key.rsplit("node_modules/", 1)[-1] for key, entry in packages.items()
                        if key and isinstance(entry, dict) and entry.get("hasInstallScript"))
        if own or theirs:
            named = ", ".join([*own, *theirs[:10]]) + (f" and {len(theirs) - 10} more" if len(theirs) > 10 else "")
            gaps.append({"kind": "not_executed", "path": rel,
                         "detail": f"install scripts are not run ({named}): what they generate is unknown"})
        origins = sorted({f"{parts.scheme}://{parts.netloc}" for entry in packages.values() if isinstance(entry, dict)
                          and isinstance(entry.get("resolved"), str)
                          for parts in [urlsplit(entry["resolved"])] if parts.scheme in ("http", "https")})
        if origins:
            units.append({"root": root, "kind": "npm-package", "registries": origins})
    return {"facts": {"units": units}, "gaps": gaps}
