#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# ///
"""External services and projects of a snapshot, recognized from the registry without a model.

Signs: the dependencies of each build unit, in the registry ecosystem of the unit;
the packages of `requirements*.txt`; the images of Dockerfiles and compose files;
the names of configuration variables and the hosts written in the files; the file
names the registry knows. A dependency that names a build unit of the project is
the project's own, never external.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path, PurePosixPath

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import flows  # noqa: E402
import modules  # noqa: E402
from snapshot_store import open_snapshot  # noqa: E402

REGISTRY = SCRIPT_DIR.parent / "data" / "service-registry.json"
# Build unit ecosystems of the module graph, as registry ecosystems.
ECOSYSTEMS = {"npm": "npm", "pnpm": "npm", "lerna": "npm", "nx": "npm", "deno": "npm", "python": "pypi",
              "cargo": "crates", "go": "go", "composer": "composer", "bundler": "rubygems", "rubygems": "rubygems",
              "terraform": "terraform"}
_REQUIREMENT = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)(?:\[[^\]]*\])?\s*(?:[<>=!~;@#]|$)")
_FROM = re.compile(r"^\s*FROM\s+(?:--\S+\s+)*([^\s]+)", re.I)
_IMAGE = re.compile(r"^\s*image:\s*['\"]?([^\s'\"#]+)")


def load(path: Path | None = None) -> dict:
    return json.loads(Path(path or REGISTRY).read_text(encoding="utf-8"))


def _image(reference: str) -> str:
    """An image reference without registry host, tag or digest: `docker.io/library/postgres:16` is `postgres`."""
    name = reference.split("@", 1)[0]
    if ":" in name.rsplit("/", 1)[-1]:
        name = name.rsplit(":", 1)[0]
    parts = name.split("/")
    if len(parts) > 1 and ("." in parts[0] or ":" in parts[0] or parts[0] == "localhost"):
        parts = parts[1:]
    if parts[:1] == ["library"]:
        parts = parts[1:]
    return "/".join(parts).lower()


def _package_signs(manifest: Path, lines_of) -> list[tuple[str, str, str, int | None]]:
    """(ecosystem, package, path, line) of every declared dependency the project does not hold itself."""
    graph = modules.load_graph(Path(modules.ensure_graph(manifest)["graph"]))
    units = [m for m in graph["modules"] if m["provenance"] == "build"]
    own = {(ECOSYSTEMS.get(e), name) for m in units for e in m.get("ecosystems", []) for name in [m["name"], *m["aliases"]]}
    out = []
    for unit in units:
        for ecosystem in {ECOSYSTEMS[e] for e in unit.get("ecosystems", []) if e in ECOSYSTEMS}:
            for name in unit["dependencies"]:
                if (ecosystem, name) in own:
                    continue
                path, line = next(((p, n) for p in unit["manifests"] for n, text in enumerate(lines_of(p) or [], 1)
                                   if re.search(rf"""(^|[\s"'/]){re.escape(name)}($|[\s"'=<>~^@:,\[])""", text)),
                                  (unit["manifests"][0] if unit["manifests"] else None, None))
                out.append((ecosystem, name, path, line))
    return out


def _text_signs(files: list[str], lines_of) -> list[tuple[str, str, str, int]]:
    """(ecosystem, package, path, line) read from requirements files, Dockerfiles and compose files."""
    out = []
    for rel in files:
        name = PurePosixPath(rel).name
        requirements = name.startswith("requirements") and name.endswith(".txt")
        dockerfile = name == "Dockerfile" or name.endswith(".Dockerfile")
        compose = name.startswith(("docker-compose", "compose")) and name.endswith((".yml", ".yaml"))
        if not (requirements or dockerfile or compose):
            continue
        for number, line in enumerate(lines_of(rel) or [], 1):
            if requirements and (match := _REQUIREMENT.match(line)) and not line.lstrip().startswith("-"):
                out.append(("pypi", match.group(1).lower().replace("_", "-"), rel, number))
            elif dockerfile and (match := _FROM.match(line)):
                out.append(("docker", _image(match.group(1)), rel, number))
            elif compose and (match := _IMAGE.match(line)):
                out.append(("docker", _image(match.group(1)), rel, number))
    return out


def recognize(manifest: Path, registry: dict | None = None) -> list[dict]:
    """Registry entries the snapshot shows signs of, each sign with its path and line."""
    manifest = Path(manifest)
    entries = (registry or load())["entries"]
    with open_snapshot(manifest) as store:
        files = sorted(dict(store.iter_file_headers_only()))
        source = flows.Source(store)
        packages = _package_signs(manifest, source.lines) + _text_signs(files, source.lines)
        texts = {rel: source.lines(rel) or [] for rel in files}
    by_package, patterns, prefixes, hosts, names = {}, [], {}, {}, {}
    for entry in entries:
        signs = entry.get("signs") or {}
        for ecosystem, values in (signs.get("packages") or {}).items():
            for value in values:
                by_package.setdefault((ecosystem, value.lower()), []).append(entry["id"])
        for ecosystem, values in (signs.get("patterns") or {}).items():
            for value in values:
                try:
                    patterns.append((ecosystem, re.compile(value), entry["id"]))
                except re.error:
                    continue
        for value in signs.get("env") or []:
            prefixes.setdefault(value, []).append(entry["id"])
        for value in signs.get("hosts") or []:
            hosts.setdefault(value, []).append(entry["id"])
        for value in signs.get("files") or []:
            names.setdefault(value, []).append(entry["id"])
    found: dict[str, list[dict]] = {}

    def add(ids, sign, value, path, line):
        for ident in ids:
            found.setdefault(ident, []).append({"sign": sign, "value": value, "path": path, "line": line})

    for ecosystem, name, path, line in packages:
        ids = list(by_package.get((ecosystem, name.lower()), []))
        if ecosystem == "go":  # a module path names its packages and major versions below it
            ids += [i for (e, value), owners in by_package.items() if e == "go" and name.startswith(value + "/")
                    for i in owners]
        ids += [i for e, pattern, i in patterns if e == ecosystem and pattern.search(name)]
        add(dict.fromkeys(ids), "package", name, path, line)
    for rel in files:
        add(names.get(PurePosixPath(rel).name, []), "file", PurePosixPath(rel).name, rel, None)
    words = re.compile(r"\b(" + "|".join(sorted(map(re.escape, prefixes), key=len, reverse=True)) + r")[A-Z0-9_]*\b") \
        if prefixes else None
    places = re.compile("|".join(sorted(map(re.escape, hosts), key=len, reverse=True))) if hosts else None
    for rel, lines in texts.items():
        for number, line in enumerate(lines, 1):
            for match in words.finditer(line) if words else ():
                add(prefixes[match.group(1)], "env", match.group(0), rel, number)
            for match in places.finditer(line) if places else ():
                add(hosts[match.group(0)], "host", match.group(0), rel, number)
    by_id = {e["id"]: e for e in entries}
    out = []
    for ident in sorted(found):
        entry = by_id[ident]
        signs = {(s["sign"], s["value"], s["path"], s["line"]): s for s in found[ident]}
        out.append({**{k: entry.get(k) for k in ("id", "name", "kind", "type", "site", "icon")}, "source": "registry",
                    "signs": sorted(signs.values(), key=lambda s: (s["sign"], s["path"] or "", s["line"] or 0, s["value"]))})
    return out
