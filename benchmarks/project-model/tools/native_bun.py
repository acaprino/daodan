"""Bun: `bun pm pkg get` (the manifest as Bun reads it) and `bun pm ls` (direct dependencies
with the versions in bun.lock), where a bun.lock or bun.lockb sits. `bun pm ls` prints text: one
`name@version` per line under the project path.
"""
from __future__ import annotations

import re
from pathlib import Path

import native_common as common

VERSION = "bun 1.4.4"
VERSION_COMMAND = ["bun", "--version"]
TRIGGERS = ("bun.lock", "bun.lockb")
COMMAND = "bun pm pkg get; bun pm ls"


def run(fixture_dir, work_dir) -> dict:
    root = Path(fixture_dir)
    places = sorted({common.parent(p) for p in common.find(root, set(TRIGGERS))})
    units, dependencies, errors = [], [], []
    for directory in places:
        here = root / directory
        pkg = common.run(["bun", "pm", "pkg", "get"], here, name="bun pm pkg get")
        data = common.json_or_none(pkg.stdout)
        name = data.get("name") if isinstance(data, dict) else None
        if pkg.returncode != 0 or not isinstance(data, dict):
            errors.append(f"{directory}: bun pm pkg get: {common.error_of(pkg)}")
        else:
            units.append({"name": name, "kind": "npm-package", "root": common.rel(here, root),
                          "manifest": common.join(common.rel(here, root), "package.json")})
        listing = common.run(["bun", "pm", "ls"], here, name="bun pm ls")
        if listing.returncode != 0:
            errors.append(f"{directory}: bun pm ls: {common.error_of(listing)}")
            continue
        for line in listing.stdout.splitlines():
            match = re.match(r"^[\s│├└─]+(@?[^@\s]+)@(\S+)", line)
            if match:
                item = {"name": match.group(1), "resolved": match.group(2)}
                if name:
                    item["unit"] = name
                    item["declared_in"] = common.join(common.rel(here, root), "package.json")
                dependencies.append(item)
    common.NOTES.update(errors=errors, raw={})
    return {"units": units, "dependencies": dependencies}
