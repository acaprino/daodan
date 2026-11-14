"""Bazel (through Bazelisk, which honours .bazelversion): targets as `bazel query` reports them (one
`bazel-target` unit per rule, named by its label, rooted at its package),
external modules as `bazel mod graph` reports them.

At the directory of MODULE.bazel (or WORKSPACE): `bazel mod graph --output=json` (the root module with its
`bazel_dep`s and their resolved versions) and `bazel query //... --output=streamed_jsonproto` (every rule
with its attributes). The server is shut down after each run. Loading packages runs Starlark and may run
repository rules, which can execute programs.
"""
from __future__ import annotations

from pathlib import Path

import native_common as common

VERSION = "Bazelisk 1.26.0, Bazel from .bazelversion (7.4.1 prefetched)"
VERSION_COMMAND = ["env", "USE_BAZEL_VERSION=7.4.1", "bazel", "--version"]
TRIGGERS = ("MODULE.bazel", "WORKSPACE", "WORKSPACE.bazel")
COMMAND = "bazel mod graph --output=json; bazel query //... --output=streamed_jsonproto"
ATTRIBUTES = ("srcs", "hdrs", "deps", "local_defines", "defines", "visibility", "includes", "copts")


def _value(attribute: dict):
    for key in ("stringListValue", "stringValue", "intValue", "booleanValue"):
        if key in attribute:
            return attribute[key]
    return None


def _short(label: str, package: str) -> str:
    prefix = f"//{package}:"
    return label[len(prefix):] if label.startswith(prefix) else label


def run(fixture_dir, work_dir) -> dict:
    root = Path(fixture_dir)
    places = sorted({common.parent(p) for p in common.find(root, set(TRIGGERS))}, key=lambda d: (d.count("/"), d))
    places = [d for d in places if not any(d != q and d.startswith(q + "/") for q in places)][:1]
    units, workspaces, dependencies, errors = [], [], [], []
    for directory in places:
        here = root / directory
        graph = common.run(["bazel", "mod", "graph", "--output=json"], here, name="bazel mod graph")
        data = common.json_or_none(graph.stdout)
        module = None
        if graph.returncode != 0 or not isinstance(data, dict):
            errors.append(f"{directory}: bazel mod graph: {common.error_of(graph)}")
        else:
            module = data.get("name") or data.get("key", "").split("@")[0]
            units.append({"name": module, "kind": "bazel-module", "root": directory,
                          "manifest": common.join(directory, "MODULE.bazel"), "depends_on": [],
                          "config": {"version": data.get("version")}})
            for dep in data.get("dependencies") or []:
                name, _, version = str(dep.get("key") or "").partition("@")
                dependencies.append({"unit": module, "name": dep.get("name") or name,
                                     "resolved": dep.get("version") or version or None,
                                     "scope": "dev" if dep.get("devDependency") else "runtime",
                                     "declared_in": common.join(directory, "MODULE.bazel")})
        query = common.run(["bazel", "query", "//...", "--output=streamed_jsonproto"], here, name="bazel query //...")
        packages: dict[str, dict] = {}
        for target in common.json_stream(query.stdout):
            rule = target.get("rule") if isinstance(target, dict) else None
            if not rule:
                continue
            label = rule["name"]
            package = label[2:].split(":", 1)[0]
            entry = {"rule": rule["ruleClass"], "name": label}
            for attribute in rule.get("attribute") or []:
                if attribute.get("name") in ATTRIBUTES and attribute.get("explicitlySpecified"):
                    value = _value(attribute)
                    if attribute["name"] in ("srcs", "hdrs") and isinstance(value, list):
                        value = [_short(v, package) for v in value]
                    entry[attribute["name"]] = value
            package_root = common.join(directory, package) if package else directory
            build_file = "BUILD.bazel" if (here / package / "BUILD.bazel").is_file() else "BUILD"
            config = {k: v for k, v in entry.items() if k not in ("name", "deps")}
            local = sorted({d for d in entry.get("deps") or [] if d.startswith("//") and d != label})
            if entry.get("deps"):
                config["deps"] = entry["deps"]
            packages[label] = {"name": label, "kind": "bazel-target", "root": package_root,
                               "manifest": common.join(package_root, build_file), "source_roots": [package_root],
                               "depends_on": local, "config": config}
        if query.returncode != 0:
            errors.append(f"{directory}: bazel query: {common.error_of(query)}")
        units.extend(packages.values())
        if packages:
            workspaces.append({"tool": "bazel", "root": directory,
                               "members": sorted({u["root"] for u in packages.values()})})
        common.run(["bazel", "shutdown"], here, name="bazel shutdown")
    common.NOTES.update(errors=errors, raw={})
    return {"units": units, "workspace": workspaces[0] if workspaces else None, "dependencies": dependencies}
