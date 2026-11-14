"""Composer: the root package as `composer show --self --format=json` reports it (requirements as written,
autoload) and the locked packages as `composer show --locked --direct --format=json` reports them.
Neither installs or runs scripts; without composer.lock the second refuses.
"""
from __future__ import annotations

from pathlib import Path

import native_common as common

VERSION = "Composer 2 (Ubuntu 24.04), PHP 8.3"
VERSION_COMMAND = ["composer", "--version"]
TRIGGERS = ("composer.json",)
COMMAND = "composer show --self --format=json; composer show --locked --direct --format=json"
ENV = {"COMPOSER_ALLOW_SUPERUSER": "1", "COMPOSER_NO_INTERACTION": "1"}


def run(fixture_dir, work_dir) -> dict:
    root = Path(fixture_dir)
    units, toolchains, dependencies, errors, raw = [], [], [], [], {}
    for manifest in common.find(root, {"composer.json"}):
        here = root / common.parent(manifest)
        me = common.run(["composer", "show", "--self", "--format=json"], here, name="composer show --self", env=ENV)
        data = common.json_or_none(me.stdout)
        if me.returncode != 0 or not isinstance(data, dict):
            errors.append(f"{manifest}: composer show --self: {common.error_of(me)}")
            continue
        name = data.get("name")
        raw.setdefault("show --self keys", {})[manifest] = sorted(data)
        locked = common.run(["composer", "show", "--locked", "--direct", "--format=json"], here,
                            name="composer show --locked", env=ENV)
        lock = common.json_or_none(locked.stdout)
        versions = {p["name"]: p.get("version") for p in lock.get("locked", [])} if isinstance(lock, dict) else None
        if locked.returncode != 0:
            errors.append(f"{manifest}: composer show --locked: {common.error_of(locked)}")
        unit = {"name": name, "kind": "composer-package", "root": common.parent(manifest), "manifest": manifest}
        autoload = (data.get("autoload") or {}).get("psr-4")
        if autoload:
            unit["config"] = {"paths": {k: v if isinstance(v, list) else [v] for k, v in autoload.items()}}
        units.append(unit)
        keys = {"runtime": ("requires", "require"), "dev": ("devRequires", "devrequires", "requires (dev)", "require-dev")}
        for scope, names in keys.items():
            links = next((data[k] for k in names if isinstance(data.get(k), dict)), {})
            for dep, constraint in links.items():
                if dep == "php":
                    toolchains.append({"tool": "php", "version": constraint, "declared_in": manifest})
                if dep == "php" or dep.startswith(("ext-", "lib-")):
                    continue
                item = {"unit": name, "name": dep, "declared": constraint, "scope": scope, "declared_in": manifest}
                if versions is not None:
                    item["resolved"] = versions.get(dep)
                dependencies.append(item)
    common.NOTES.update(errors=errors, raw=raw)
    return {"units": units, "toolchains": toolchains, "dependencies": dependencies}
