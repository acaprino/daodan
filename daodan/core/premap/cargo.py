"""Source: Cargo's package model, `cargo metadata --format-version 1`, in each folder holding a Cargo.toml.

`commands` describes, for Daodan's container, `--locked` (the lockfile as it is, never rewritten; it reaches
the registries) and `--no-deps` (no resolution, offline). `RUSTUP_TOOLCHAIN` pins the toolchain, so a
`rust-toolchain` file of the project never makes rustup install another; no build script runs. `read` keeps the
`--locked` answer, else the `--no-deps` one (a `model_partial` gap: registries unknown). Units are the
workspace members with their targets, edition, features and build script, and the path dependencies between
them as edges; registries are the sources of the packages the lockfile resolves. A resolved workspace
also yields Cargo's package graph, including development, build and target-specific edges.
"""
from __future__ import annotations

import json
import posixpath
from pathlib import PurePosixPath
import tomllib

NAME, VERSION, RANK = "cargo", "1.99.1", "model"  # the Rust release Daodan pins (`resolve_edges.RUST_VERSION`)
ENV = {"CARGO_TERM_COLOR": "never", "RUSTUP_TOOLCHAIN": VERSION, "RUSTUP_AUTO_INSTALL": "0"}
MODES = (("--locked", "registries"), ("--no-deps", "none"))


def commands(context):
    folders = sorted({PurePosixPath(rel).parent.as_posix() if "/" in rel else "." for rel in context.inventory.files
                      if PurePosixPath(rel).name == "Cargo.toml"}, key=lambda f: (f.count("/"), f))
    return [{"tool": "cargo", "argv": ["cargo", "metadata", "--format-version", "1", mode], "cwd": folder,
             "env": ENV, "network": network} for folder in folders for mode, network in MODES] or None


def _origin(source: str) -> str:
    """`registry+https://...`, `sparse+https://...`, `git+https://...?rev#sha` as the URL the install reaches."""
    return source.split("+", 1)[-1].split("?", 1)[0].split("#", 1)[0]


def _package_graph(data, packages, manifest, rel):
    """Project Cargo's resolved edges into graph-local indices. Cargo IDs can contain private URLs and paths."""
    resolved = {n["id"]: n for n in data["resolve"]["nodes"]}
    members = set(data["workspace_members"])
    if not members <= resolved.keys():
        raise ValueError("missing workspace member")
    ordered = sorted(resolved, key=lambda i: (packages[i]["name"], packages[i]["version"], i))
    indices = {package_id: index for index, package_id in enumerate(ordered)}
    nodes = []
    for i in ordered:
        package = packages[i]
        edges = {(indices[dep["pkg"]], kind.get("kind") or "", kind.get("target") or "")
                 for dep in resolved[i]["deps"] for kind in (dep["dep_kinds"] or [{}])}
        node = {"name": package["name"], "version": package["version"],
                "dependencies": [{"to": to, **({"kind": kind} if kind else {}),
                                  **({"target": target} if target else {})} for to, kind, target in sorted(edges)]}
        if i in members:
            member = rel(package["manifest_path"])
            if not member.startswith("../"):
                node["manifest"] = member
        if not package.get("source") and "manifest" not in node:
            node["local"] = True
        nodes.append(node)
    return {"ecosystem": "crates", "path": manifest, "nodes": nodes}


def read(context, commands, results):
    by_folder: dict[str, dict] = {}
    for command, result in zip(commands, results):
        by_folder.setdefault(command["cwd"], {})[command["argv"][-1]] = result
    root = next((r["root"] for r in results if r.get("root")), "/")
    gaps, units, workspaces, toolchains, seen = [], [], [], [], set()
    graphs = {}

    def rel(path: str) -> str:
        value = posixpath.relpath(path, root)
        return "." if value in ("", ".") else value

    for folder, answers in sorted(by_folder.items(), key=lambda item: (len(PurePosixPath(item[0]).parts), item[0])):
        locked, plain = answers.get("--locked"), answers.get("--no-deps")
        chosen = locked if locked and locked["returncode"] == 0 else plain if plain and plain["returncode"] == 0 else None
        if chosen is None:
            gaps.append({"kind": "model_failed", "path": folder, "detail": "; ".join(
                f"cargo metadata {m}: {(a['stderr'] or '').strip()[-300:]}" for m, a in answers.items())})
            continue
        if chosen is plain and locked is not None:
            gaps.append({"kind": "model_partial", "path": folder,
                         "detail": "package resolution and registries unknown: cargo metadata --locked: "
                                   f"{(locked['stderr'] or '').strip()[-300:]}"})
        data = json.loads(chosen["stdout"])
        packages = {p["id"]: p for p in data["packages"]}
        members = [packages[i] for i in data["workspace_members"] if i in packages]
        ws_root = rel(data["workspace_root"])
        ws_manifest = rel(posixpath.join(data["workspace_root"], "Cargo.toml"))
        if data.get("resolve") is not None:
            # A member can supply the resolved answer even when an earlier command saw only --no-deps.
            try:
                graph = _package_graph(data, packages, ws_manifest, rel)
            except (KeyError, TypeError, ValueError):
                gaps.append({"kind": "model_partial", "path": folder,
                             "detail": "cargo metadata returned an incomplete resolved package graph"})
            else:
                previous = graphs.get(ws_manifest)
                if previous is None:
                    if folder != ws_root:
                        graph["resolved_in"] = folder
                    graphs[ws_manifest] = graph
                elif graph["nodes"] != previous["nodes"]:
                    gaps.append({"kind": "model_partial", "path": folder,
                                 "detail": f"cargo metadata resolves a different package graph here; "
                                           f"the reported graph is from {previous.get('resolved_in', ws_root)}"})
        if all(rel(p["manifest_path"]) in seen for p in members):
            continue
        registries = sorted({_origin(p["source"]) for p in data["packages"] if p.get("source") and p["id"] not in
                             data["workspace_members"]}) if data.get("resolve") is not None else None
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
            depends = sorted({dep["name"] for dep in package["dependencies"]
                              if dep.get("path") or dep.get("source") is None})
            unit = {"name": package["name"], "kind": "cargo-crate", "root": unit_root, "manifest": manifest,
                    "source_roots": sorted({PurePosixPath(t["path"]).parent.as_posix() for t in targets
                                            if t["kind"] != "custom-build"}),
                    "depends_on": depends, "config": config}
            if registries is not None:
                unit["registries"] = registries
            units.append(unit)
            declared = (tomllib.loads(context.inventory.text(manifest)).get("package", {})
                        if manifest in context.inventory.headers else {})
            for field, tool, value in (("rust-version", "rust", package.get("rust_version")),
                                       ("edition", "rust-edition", package.get("edition"))):
                written = declared.get(field)
                if value and (written is not None or field == "rust-version"):  # an edition no file writes is 2015
                    toolchain = {"tool": tool, "version": value,
                                 "declared_in": ws_manifest if isinstance(written, dict) else manifest}
                    if toolchain not in toolchains:
                        toolchains.append(toolchain)
        if (len(member_dirs) > 1 or member_dirs != [ws_root]) and not any(w["root"] == ws_root for w in workspaces):
            workspaces.append({"tool": "cargo", "root": ws_root, "members": member_dirs})
    return {"facts": {"units": units, "workspace": workspaces, "toolchains": toolchains,
                      **({"package_graphs": list(graphs.values())} if graphs else {})}, "gaps": gaps}
