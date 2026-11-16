"""Source: what `package.json` and the lockfiles declare about installing, read from the files, never run.

Daodan installs a unit's packages with `npm ci --ignore-scripts`: the install scripts a `package.json` declares
(`preinstall`, `install`, `postinstall`, `prepare`) and those of the dependencies the lockfile marks
`hasInstallScript` are a `not_executed` gap. A unit's registries are the origins its install reaches: of the URLs
its lockfile records (`package-lock.json`'s `resolved`, every URL of `pnpm-lock.yaml` and `yarn.lock`), of the
registries `.yarnrc.yml` names, and of the URLs its `package.json` dependencies name, npm's shorthands for a
hosted git repository (`github:`, `owner/repo`, `gitlab:`, `bitbucket:`, `gist:`) included.
"""
from __future__ import annotations

import json
from pathlib import PurePosixPath
import re

from premap.origins import disk_text, found, origin

NAME, VERSION, RANK = "npm-files", "daodan/premap/v1", "reader"
INSTALL_SCRIPTS = ("preinstall", "install", "postinstall", "prepare")
DECLARED = ("dependencies", "devDependencies", "optionalDependencies", "peerDependencies")
HOSTED = {"github": "https://github.com", "gitlab": "https://gitlab.com", "bitbucket": "https://bitbucket.org",
          "gist": "https://gist.github.com"}  # npm's shorthands for a hosted git repository (hosted-git-info)
SHORTHAND = re.compile(r"^(?:(github|gitlab|bitbucket|gist):)?[\w.-]+/[\w.-]+(?:#.*)?$")
LOCAL = (".", "/", "~", "file:", "link:", "workspace:", "npm:", "portal:")  # a folder, an alias: no host
REGISTRY_SERVER = re.compile(r"npmRegistryServer:\s*[\"']?([^\s\"']+)")  # Yarn's, in .yarnrc.yml


def _json(context, rel: str) -> dict:
    try:
        value = json.loads(context.inventory.text(rel)) if rel in context.inventory.headers else {}
    except ValueError:
        return {}  # an unreadable manifest is the module graph's gap
    return value if isinstance(value, dict) else {}


def _spec(value) -> str | None:
    """The origin a dependency's spec names: a URL's, or the host of npm's shorthand for a hosted git repository."""
    if not isinstance(value, str) or value.startswith(LOCAL):
        return None
    shorthand = SHORTHAND.match(value)
    return HOSTED[shorthand.group(1) or "github"] if shorthand else origin(value) if "://" in value else None


def run(context):
    manifests = [rel for rel in context.inventory.files if PurePosixPath(rel).name == "package.json"]
    if not manifests:
        return None
    units, gaps = [], []
    for rel in manifests:
        root = PurePosixPath(rel).parent.as_posix() if "/" in rel else "."
        manifest = _json(context, rel)
        scripts = manifest.get("scripts")
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
        beside = (lambda name: name if root == "." else f"{root}/{name}")  # noqa: E731
        origins = {origin(entry["resolved"]) for entry in packages.values() if isinstance(entry, dict)
                   and isinstance(entry.get("resolved"), str)}
        origins |= {_spec(spec) for field in DECLARED if isinstance(manifest.get(field), dict)
                    for spec in manifest[field].values()}
        pnpm = beside("pnpm-lock.yaml")
        origins |= found(context.inventory.text(pnpm) if pnpm in context.inventory.headers else "")
        origins |= found(disk_text(context, beside("yarn.lock")) or "")
        yarnrc = beside(".yarnrc.yml")
        origins |= {origin(url) for url in REGISTRY_SERVER.findall(
            context.inventory.text(yarnrc) if yarnrc in context.inventory.headers else "")}
        origins.discard(None)
        if origins:
            units.append({"root": root, "kind": "npm-package", "registries": sorted(origins)})
    return {"facts": {"units": units}, "gaps": gaps}
