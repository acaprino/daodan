"""Source: Cargo's package model, `cargo metadata --format-version 1`, in each folder holding a Cargo.toml.

`commands` describes, for Daodan's container, `--locked` (the lockfile as it is, never rewritten; it reaches
the registries) and `--no-deps` (no resolution, offline). `RUSTUP_TOOLCHAIN` pins the toolchain, so a
`rust-toolchain` file of the project never makes rustup install another; no build script runs. `read` keeps the
`--locked` answer, else the `--no-deps` one (a `model_partial` gap: versions unresolved). Units are the
workspace members with their targets, edition, features and build script; dependencies are the members'
registry and git dependencies, resolved from the `resolve` graph; registries are the sources of the packages
the lockfile resolves. Cargo's `req` is the requirement as Cargo reads it (`^1.0` for `1.0`), not as written:
it is not `declared`.
"""
from __future__ import annotations

import json
import posixpath
from pathlib import PurePosixPath
import tomllib

NAME, VERSION, RANK = "cargo", "1.99.1", "model"  # the Rust release Daodan pins (`resolve_edges.RUST_VERSION`)
ENV = {"CARGO_TERM_COLOR": "never", "RUSTUP_TOOLCHAIN": VERSION, "RUSTUP_AUTO_INSTALL": "0"}
SCOPE = {None: "runtime", "dev": "dev", "build": "build"}
MODES = (("--locked", "registries"), ("--no-deps", "none"))


def commands(context):
    folders = sorted({PurePosixPath(rel).parent.as_posix() if "/" in rel else "." for rel in context.inventory.files
                      if PurePosixPath(rel).name == "Cargo.toml"}, key=lambda f: (f.count("/"), f))
    return [{"tool": "cargo", "argv": ["cargo", "metadata", "--format-version", "1", mode], "cwd": folder,
             "env": ENV, "network": network} for folder in folders for mode, network in MODES] or None


def _origin(source: str) -> str:
    """`registry+https://...`, `sparse+https://...`, `git+https://...?rev#sha` as the URL the install reaches."""
    return source.split("+", 1)[-1].split("?", 1)[0].split("#", 1)[0]


def read(context, commands, results):
    by_folder: dict[str, dict] = {}
    for command, result in zip(commands, results):
        by_folder.setdefault(command["cwd"], {})[command["argv"][-1]] = result
    root = next((r["root"] for r in results if r.get("root")), "/")
    gaps, units, workspaces, toolchains, dependencies, seen = [], [], [], [], [], set()

    def rel(path: str) -> str:
        value = posixpath.relpath(path, root)
        return "." if value in ("", ".") else value

    for folder, answers in sorted(by_folder.items(), key=lambda item: (item[0].count("/"), item[0])):
        locked, plain = answers.get("--locked"), answers.get("--no-deps")
        chosen = locked if locked and locked["returncode"] == 0 else plain if plain and plain["returncode"] == 0 else None
        if chosen is None:
            gaps.append({"kind": "model_failed", "path": folder, "detail": "; ".join(
                f"cargo metadata {m}: {(a['stderr'] or '').strip()[-300:]}" for m, a in answers.items())})
            continue
        if chosen is plain and locked is not None:
            gaps.append({"kind": "model_partial", "path": folder,
                         "detail": f"resolved versions unknown: cargo metadata --locked: {(locked['stderr'] or '').strip()[-300:]}"})
        data = json.loads(chosen["stdout"])
        packages = {p["id"]: p for p in data["packages"]}
        members = [packages[i] for i in data["workspace_members"] if i in packages]
        if all(rel(p["manifest_path"]) in seen for p in members):
            continue
        nodes = {n["id"]: n for n in (data.get("resolve") or {}).get("nodes") or []}
        registries = sorted({_origin(p["source"]) for p in data["packages"] if p.get("source") and p["id"] not in
                             data["workspace_members"]}) if data.get("resolve") is not None else None
        ws_manifest = rel(posixpath.join(data["workspace_root"], "Cargo.toml"))
        member_dirs = []
        for package in members:
            manifest = rel(package["manifest_path"])
            unit_root = PurePosixPath(manifest).parent.as_posix() if "/" in manifest else "."
            member_dirs.append(unit_root)
            if manifest in seen:
                continue
            seen.add(manifest)
            targets = [{"kind": t["kind"][0], "name": t["name"], "path": rel(t["src_path"])} for t in package["targets"]]
            config = {"edition": package.get("edition"), "targets": targets}
            build = [t["path"] for t in targets if t["kind"] == "custom-build"]
            if build:
                config["build_script"] = build[0]
            if package.get("features"):
                config["features"] = package["features"]
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
                item = {"unit": package["name"], "name": dep["name"], "declared_in": manifest,
                        "scope": "optional" if dep.get("optional") else SCOPE.get(dep.get("kind"), dep.get("kind"))}
                version = resolved.get((dep.get("rename") or dep["name"]).replace("-", "_"), resolved.get(dep["name"]))
                if version:  # an optional dependency the default features leave out is not in `resolve`
                    item["resolved"] = version
                dependencies.append(item)
            unit = {"name": package["name"], "kind": "cargo-crate", "root": unit_root, "manifest": manifest,
                    "source_roots": sorted({PurePosixPath(t["path"]).parent.as_posix() for t in targets
                                            if t["kind"] != "custom-build"}),
                    "depends_on": sorted(set(depends)), "config": config}
            if registries is not None:
                unit["registries"] = registries
            units.append(unit)
            if package.get("rust_version"):
                written = tomllib.loads(context.inventory.text(manifest)).get("package", {}).get("rust-version") \
                    if manifest in context.inventory.headers else None
                toolchain = {"tool": "rust", "version": package["rust_version"],
                             "declared_in": ws_manifest if isinstance(written, dict) else manifest}
                if toolchain not in toolchains:
                    toolchains.append(toolchain)
        ws_root = rel(data["workspace_root"])
        if (len(member_dirs) > 1 or member_dirs != [ws_root]) and not any(w["root"] == ws_root for w in workspaces):
            workspaces.append({"tool": "cargo", "root": ws_root, "members": member_dirs})
    return {"facts": {"units": units, "workspace": workspaces, "toolchains": toolchains, "dependencies": dependencies},
            "gaps": gaps}
