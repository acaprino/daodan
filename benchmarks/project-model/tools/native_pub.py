"""Dart pub: per pubspec.yaml, `dart pub deps --json` (the resolved graph: root, direct, dev, with versions; it
needs a resolution) and, when that refuses, `dart pub get --dry-run` (resolves, writes nothing, prints the
packages it would add). A Flutter package needs the Flutter SDK, which is not installed here.
"""
from __future__ import annotations

import re
from pathlib import Path

import native_common as common

VERSION = "Dart SDK 3.5.4"
VERSION_COMMAND = ["dart", "--version"]
TRIGGERS = ("pubspec.yaml",)
COMMAND = "dart pub deps --json; dart pub get --dry-run"
KIND = {"direct": "runtime", "dev": "dev"}


def run(fixture_dir, work_dir) -> dict:
    root = Path(fixture_dir)
    units, dependencies, errors = [], [], []
    for manifest in common.find(root, {"pubspec.yaml"}):
        here, directory = root / common.parent(manifest), common.parent(manifest)
        done = common.run(["dart", "pub", "deps", "--json"], here, name="dart pub deps --json")
        data = common.json_or_none(done.stdout)
        if done.returncode == 0 and isinstance(data, dict):
            packages = {p["name"]: p for p in data.get("packages") or []}
            name = data.get("root")
            local = {p["name"] for p in packages.values() if p.get("source") in ("root", "path")}
            depends = [d for d in (packages.get(name) or {}).get("dependencies") or [] if d in local]
            units.append({"name": name, "kind": "pub-package", "root": directory, "manifest": manifest,
                          "depends_on": sorted(depends)})
            for p in packages.values():
                if p.get("kind") in KIND and p["name"] not in local:
                    dependencies.append({"unit": name, "name": p["name"], "resolved": p.get("version"),
                                         "scope": KIND[p["kind"]], "declared_in": manifest})
            continue
        errors.append(f"{manifest}: dart pub deps: {common.error_of(done)}")
        dry = common.run(["dart", "pub", "get", "--dry-run"], here, name="dart pub get --dry-run")
        if dry.returncode != 0:
            errors.append(f"{manifest}: dart pub get --dry-run: {common.error_of(dry)}")
            continue
        for line in dry.stdout.splitlines():
            match = re.match(r"^\+ (\S+) (\S+)", line)
            if match:
                dependencies.append({"name": match.group(1), "resolved": match.group(2), "declared_in": manifest})
    common.NOTES.update(errors=errors, raw={})
    return {"units": units, "dependencies": dependencies}
