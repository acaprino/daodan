"""Bundler: `bundle lock --print`. Bundler evaluates the Gemfile, resolves against the lockfile or the index and
prints the lockfile it would write, writing nothing. DEPENDENCIES are the direct gems with their constraints,
the GEM specs their resolved versions, RUBY VERSION the interpreter it records.
"""
from __future__ import annotations

import re
from pathlib import Path

import native_common as common

VERSION = "Bundler of Ruby 3.3.6"
VERSION_COMMAND = ["bundle", "--version"]
TRIGGERS = ("Gemfile",)
COMMAND = "bundle lock --print"


def run(fixture_dir, work_dir) -> dict:
    root = Path(fixture_dir)
    units, toolchains, dependencies, errors = [], [], [], []
    for manifest in common.find(root, {"Gemfile"}):
        here = root / common.parent(manifest)
        done = common.run(["bundle", "lock", "--print"], here, name=COMMAND)
        if done.returncode != 0:
            errors.append(f"{manifest}: {common.error_of(done)}")
            continue
        gemspec = sorted(p.name for p in here.glob("*.gemspec"))
        units.append({"kind": "gem" if gemspec else "bundler-project", "root": common.parent(manifest),
                      "manifest": common.join(common.parent(manifest), gemspec[0]) if gemspec else manifest})
        section, specs, direct = None, {}, []
        for line in done.stdout.splitlines():
            if line and not line.startswith(" "):
                section = line.strip()
                continue
            spec = re.match(r"^    (\S+) \(([^)]+)\)$", line)
            if section in ("GEM", "PATH", "GIT") and spec:
                specs[spec.group(1)] = spec.group(2)
            dep = re.match(r"^  (\S+?)(!)?(?: \(([^)]+)\))?$", line)
            if section == "DEPENDENCIES" and dep:
                direct.append((dep.group(1), dep.group(3)))
            if section == "RUBY VERSION" and line.strip():
                toolchains.append({"tool": "ruby", "version": line.strip().replace("ruby ", ""), "declared_in": manifest})
        for gem, constraint in direct:
            dependencies.append({"name": gem, "declared": constraint, "resolved": specs.get(gem), "declared_in": manifest})
    common.NOTES.update(errors=errors, raw={})
    return {"units": units, "toolchains": toolchains, "dependencies": dependencies}
