"""Source: npm's own model of the packages, `npm query ":root, .workspace"`, run in Daodan's container.

`commands` describes, in each folder holding a `package.json`, the query from the lockfile
(`--package-lock-only`) and without it (npm then reads the manifests, since nothing is installed); neither
installs, runs a script or reaches a registry. `read` keeps the lockfile's answer, else the other, and gives
the units (the root and the workspaces npm resolves), from the lockfile only the workspace with its members
and the edges between units, also to a package a `file:` dependency links to a folder of the project
(`npm query ":link"`; without a lockfile npm links nothing: a `model_partial` gap), and each unit's
`config.entry_files`: the files its `main`, `module`, `browser`, `bin` and `exports` name, relative to the
project's root, as written (a build output the snapshot does not hold stays as declared).
"""
from __future__ import annotations

import json
import posixpath
from pathlib import PurePosixPath

NAME, VERSION, RANK = "npm", "bundled with Node", "model"  # the version that answers (`npm --version`) labels the facts
QUERY = ["npm", "query", ":root, .workspace"]
# The packages a `file:` dependency links to a folder of the project: outside any workspace npm lists them
# only here, and an edge to one is an edge between units.
LINKS = ["npm", "query", ":link", "--package-lock-only"]


def _parent(rel: str) -> str:
    return PurePosixPath(rel).parent.as_posix() if "/" in rel else "."


def _join(folder: str, name: str) -> str:
    value = posixpath.normpath(name if folder == "." else f"{folder}/{name}")
    return "." if value in ("", ".") else value


def commands(context):
    folders = sorted({_parent(rel) for rel in context.inventory.files if PurePosixPath(rel).name == "package.json"},
                     key=lambda f: (f.count("/"), f))
    if not folders:
        return None
    env = {"npm_config_update_notifier": "false"}
    return [{"tool": "npm", "argv": ["npm", "--version"], "cwd": ".", "env": env, "network": "none"}] + [
        {"tool": "npm", "argv": argv, "cwd": folder, "env": env, "network": "none"}
        for folder in folders for argv in (QUERY + ["--package-lock-only"], QUERY, LINKS)]


def _strings(value) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [s for inner in value.values() for s in _strings(inner)]
    if isinstance(value, list):
        return [s for inner in value for s in _strings(inner)]
    return []


def _entries(node: dict, root: str) -> list[str]:
    declared = [*_strings(node.get("main")), *_strings(node.get("module")), *_strings(node.get("bin")),
                *_strings(node.get("exports"))]
    if isinstance(node.get("browser"), str):
        declared.append(node["browser"])
    return sorted({_join(root, path) for path in declared if not path.startswith(("http:", "https:"))})


def _nodes(result) -> list | None:
    """npm's answer, or None when the command gave none."""
    try:
        nodes = json.loads(result["stdout"]) if result and result["returncode"] == 0 else None
    except ValueError:
        return None
    return nodes if isinstance(nodes, list) else None


def _local(nodes: list) -> list[dict]:
    """The nodes that are folders of the project, not installed packages."""
    return [n for n in nodes if isinstance(n, dict) and "node_modules/" not in f"/{n.get('location', '')}/"]


def read(context, commands, results):
    answers: dict[str, dict] = {}
    version = results[0]["stdout"].strip() if results[0]["returncode"] == 0 else None
    for command, result in zip(commands[1:], results[1:]):
        locked = "--package-lock-only" in command["argv"]
        mode = "links" if command["argv"] == LINKS else "lock" if locked else "tree"
        answers.setdefault(command["cwd"], {})[mode] = result
    gaps, units, workspaces, covered = [], [], [], set()
    for folder in sorted(answers, key=lambda f: (f.count("/"), f)):
        if folder in covered:
            continue
        nodes, mode = None, None
        for mode in ("lock", "tree"):
            result = answers[folder].get(mode)
            if result and result["returncode"] == 0:
                try:
                    nodes = json.loads(result["stdout"])
                    break
                except ValueError:
                    pass
        if not isinstance(nodes, list):
            stderr = "; ".join((answers[folder][m]["stderr"] or "").strip()[-200:] for m in ("lock", "tree"))
            gaps.append({"kind": "model_failed", "path": folder, "detail": f"npm query: {stderr}"})
            continue
        base = result.get("root")

        def place(node: dict) -> str:
            """The node's folder: npm answers for the whole workspace even from a member's folder."""
            if base and isinstance(node.get("path"), str):
                value = posixpath.relpath(node["path"], base)
                return "." if value in ("", ".") else value
            return _join(folder, node.get("location") or ".")

        # Without the lockfile nothing is installed: npm then links no workspace, so it states no member and no
        # edge between units (silence there would read as "none"). The same holds for the edges when the links
        # did not answer.
        locked = mode == "lock"
        local = _local(nodes)
        linked = _nodes(answers[folder].get("links")) if locked else None
        names = {n.get("name") for n in local + _local(linked or []) if n.get("name")}
        for node in local:
            root = place(node)
            if root in covered:
                continue
            covered.add(root)
            unit = {"name": node.get("name"), "kind": "npm-package", "root": root,
                    "manifest": _join(root, "package.json")}
            if linked is not None:
                unit["depends_on"] = sorted({dep for section in ("dependencies", "devDependencies",
                                                                 "optionalDependencies", "peerDependencies")
                                             for dep in (node.get(section) or {}) if dep in names})
            entries = _entries(node, root)
            if entries:
                unit["config"] = {"entry_files": entries}
            units.append(unit)
        if locked and linked is None:
            gaps.append({"kind": "model_partial", "path": folder,
                         "detail": "npm query :link did not answer: no edge between units stated"})
        root_node = next((n for n in local if not n.get("location")), None)
        if root_node is None or not root_node.get("workspaces"):
            continue
        top = place(root_node)
        if not locked:
            gaps.append({"kind": "model_partial", "path": top,
                         "detail": "npm query answered without the lockfile: no workspace member before an install"})
        elif not any(w["root"] == top for w in workspaces):
            workspaces.append({"tool": "npm", "root": top,
                               "members": sorted(place(n) for n in local if n.get("location"))})
    return {"version": version, "facts": {"units": units, "workspace": workspaces}, "gaps": gaps}
