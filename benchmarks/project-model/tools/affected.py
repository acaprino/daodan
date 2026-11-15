"""`affected` (Rani367/affected): the project graph it builds to tell which packages a change touches.

`affected detect` prints the ecosystem it chose and every package with its name and folder; `affected graph --dot`
prints the edges between those packages (an edge `"a" -> "b"` is "a depends on b"; a package without edges is not
in the graph). The two are joined here. Both read the manifests of the project root and pick the first of 13
resolvers that matches (Cargo and Go ask `cargo metadata` and `go mod graph`). `list --json` only names the
packages a git diff touches and counts the total, so it is not used. The tool states no workspace, no manifest
path, no dependency and no version, so those facets are left out.
"""
from __future__ import annotations

import posixpath
import re

import native_common as common

VERSION = "1.0.0"
VERSION_COMMAND = ["affected", "--version"]
COMMAND = "affected --no-color --root <fixture> detect; affected --no-color --root <fixture> graph --dot"
KIND = {"cargo": "cargo-crate", "npm": "npm-package", "yarn": "npm-package", "bun": "npm-package", "go": "go-module",
        "python": "python-project", "maven": "maven-module", "gradle": "gradle-project", "dotnet": "dotnet-project",
        "swift": "swift-package", "dart": "pub-package", "elixir": "mix-project", "sbt": "sbt-project"}
NOTHING = "No supported project type"  # "found" from detect.rs, "detected" from resolvers/mod.rs


def _norm(path: str) -> str:
    return posixpath.normpath(path.replace("\\", "/")) if path else "."


def parse_detect(text: str) -> dict:
    """`{"ecosystem", "detected": [...], "packages": [(name, root)]}` from the text of `affected detect`."""
    ecosystem, detected, packages, listing = None, [], [], False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("Ecosystem:"):
            ecosystem = stripped.split(":", 1)[1].strip()
        elif stripped.startswith("Detected:"):
            detected = [e.strip() for e in stripped.split(":", 1)[1].split(",") if e.strip()]
        elif stripped.startswith("Packages"):
            listing = True
        elif listing and stripped.startswith("●"):
            parts = stripped[1:].strip().split()
            if len(parts) == 1:  # the project root prints an empty folder
                packages.append((parts[0], "."))
            elif parts:
                packages.append((" ".join(parts[:-1]), _norm(parts[-1])))
    return {"ecosystem": ecosystem, "detected": detected, "packages": packages}


def parse_dot(text: str) -> list[tuple[str, str]]:
    return re.findall(r'^\s*"(.*)"\s*->\s*"(.*)";\s*$', text, re.M)


def convert(detected: dict, edges: list[tuple[str, str]]) -> dict:
    kind = KIND.get(detected["ecosystem"] or "")
    units = [{"name": name, "kind": kind, "root": root, "depends_on": []} for name, root in detected["packages"]]
    by_name = {u["name"]: u for u in units}
    by_root = {u["root"]: u for u in units}
    unmatched = []
    for source, target in edges:  # an id is the package name or, for Go, Maven, .NET and Elixir, its folder
        a = by_name.get(source) or by_root.get(_norm(source))
        b = by_name.get(target) or by_root.get(_norm(target))
        if a is None or b is None:
            unmatched.append((source, target))
        elif b["name"] not in a["depends_on"]:
            a["depends_on"].append(b["name"])
    for unit in units:
        unit["depends_on"].sort()
    common.NOTES["raw"] = {"ecosystem": detected["ecosystem"], "detected": detected["detected"], "packages": len(units),
                           "edges": len(edges), "unmatched_edges": unmatched[:10]}
    return {"units": units}


def run(fixture_dir, work_dir) -> dict:
    base = ["affected", "--no-color", "--root", str(fixture_dir)]
    found = common.run(base + ["detect"], fixture_dir, name="affected detect")
    if found.returncode != 0:
        common.NOTES["raw"] = {"rc": found.returncode, "stderr": found.stderr.strip()[-500:]}
        if NOTHING in found.stderr:  # the tool's answer: no project it knows
            return {"units": []}
        raise RuntimeError(common.error_of(found))
    detected = parse_detect(found.stdout)
    graph = common.run(base + ["graph", "--dot"], fixture_dir, name="affected graph --dot")
    if graph.returncode != 0:
        raise RuntimeError("graph --dot " + common.error_of(graph))
    return convert(detected, parse_dot(graph.stdout))
