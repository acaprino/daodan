"""Cargo: the package model as `cargo metadata --format-version 1` reports it.

Per Cargo.toml no earlier answer covered (a walk by file name finds them; cargo finds the workspace root
itself): first `--frozen` (lockfile as is, no network), then without flags (may write Cargo.lock and use the
network). The output is the `--frozen` answer when it succeeded, otherwise the plain one; both calls are
measured. Units are the workspace members, dependencies the members' non-path dependencies, resolved
versions from the `resolve` graph.
"""
from __future__ import annotations

from pathlib import Path

import native_common as common

VERSION = "cargo 1.99.1"
VERSION_COMMAND = ["cargo", "--version"]
TRIGGERS = ("Cargo.toml",)
COMMAND = "cargo metadata --format-version 1 --frozen; cargo metadata --format-version 1"
SCOPE = {None: "runtime", "dev": "dev", "build": "build"}


def _metadata(directory: Path):
    frozen = common.run(["cargo", "metadata", "--format-version", "1", "--frozen"], directory,
                        name="cargo metadata --frozen")
    plain = common.run(["cargo", "metadata", "--format-version", "1"], directory, name="cargo metadata")
    for done, mode in ((frozen, "frozen"), (plain, "plain")):
        data = common.json_or_none(done.stdout) if done.returncode == 0 else None
        if data:
            return data, mode, [common.error_of(d) for d in (frozen, plain) if d.returncode != 0]
    return None, None, [common.error_of(frozen), common.error_of(plain)]


def run(fixture_dir, work_dir) -> dict:
    root = Path(fixture_dir)
    manifests = common.find(root, {"Cargo.toml"})
    units, workspaces, toolchains, dependencies, errors, modes = [], [], [], [], [], {}
    covered: set[str] = set()
    for manifest in manifests:
        if manifest in covered:
            continue
        data, mode, failures = _metadata(root / common.parent(manifest))
        errors.extend(f"{manifest}: {f}" for f in failures)
        if not data:
            covered.add(manifest)
            continue
        modes[manifest] = mode
        packages = {p["id"]: p for p in data["packages"]}
        members = [packages[i] for i in data["workspace_members"] if i in packages]
        nodes = {n["id"]: n for n in (data.get("resolve") or {}).get("nodes") or []}
        for package in members:
            manifest_rel = common.rel(package["manifest_path"], root)
            covered.add(manifest_rel)
            unit_root = common.parent(manifest_rel)
            targets = []
            for t in package["targets"]:
                target = {"kind": t["kind"][0], "name": t["name"], "path": common.rel(t["src_path"], root)}
                if t.get("crate_types") and t["crate_types"] != t["kind"]:
                    target["crate_types"] = t["crate_types"]
                targets.append(target)
            config = {"edition": package.get("edition"), "targets": targets}
            if any(t["kind"] == "proc-macro" for t in targets):
                config["proc_macro"] = True
            build = [t["path"] for t in targets if t["kind"] == "custom-build"]
            if build:
                config["build_script"] = common.rel(root / build[0], root / unit_root)
            if package.get("features"):
                config["features"] = package["features"]
                if "default" in package["features"]:
                    config["default_features"] = package["features"]["default"]
            sources = sorted({common.parent(t["path"]) for t in targets if t["kind"] != "custom-build"})
            resolved = {}
            for dep in (nodes.get(package["id"]) or {}).get("deps") or []:
                target = packages.get(dep["pkg"])
                if target:
                    resolved[dep["name"]] = target["version"]
                    resolved.setdefault(target["name"], target["version"])
            depends = []
            for dep in package["dependencies"]:
                if dep.get("path") or dep.get("source") is None:
                    depends.append(dep["name"])
                    continue
                item = {"unit": package["name"], "name": dep["name"], "declared": dep.get("req"),
                        "scope": "optional" if dep.get("optional") else SCOPE.get(dep.get("kind"), dep.get("kind")),
                        "declared_in": manifest_rel}
                if data.get("resolve") is not None:
                    item["resolved"] = resolved.get((dep.get("rename") or dep["name"]).replace("-", "_"),
                                                    resolved.get(dep["name"]))
                dependencies.append(item)
            units.append({"name": package["name"], "kind": "cargo-crate", "root": unit_root, "manifest": manifest_rel,
                          "source_roots": sources, "depends_on": sorted(set(depends)),
                          "config": config})
            if package.get("rust_version"):
                toolchains.append({"tool": "rust", "version": package["rust_version"], "declared_in": manifest_rel})
        ws_root = common.rel(data["workspace_root"], root)
        covered.add(common.join(ws_root, "Cargo.toml"))
        member_dirs = [common.parent(common.rel(p["manifest_path"], root)) for p in members]
        if len(member_dirs) > 1 or member_dirs != [ws_root]:
            workspaces.append({"tool": "cargo", "root": ws_root, "members": member_dirs})
    common.NOTES.update(errors=errors, raw={"mode per manifest": modes})
    return {"units": units, "workspace": workspaces[0] if len(workspaces) == 1 else (workspaces or None),
            "toolchains": toolchains, "dependencies": dependencies}

