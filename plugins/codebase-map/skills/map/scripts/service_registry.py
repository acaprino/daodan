#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# ///
"""Technologies, frameworks, tools and external services of a snapshot, recognized from Step 1 facts and the registry.

Consumes the pre-map's `packages`, `services`, `docker_builds` and `excluded` without re-parsing manifests,
requirements files, Dockerfiles or Compose files; falls back to `premap.module_graph.package_facts` only when a caller
passes a partial `facts` stub in tests. Every sign respects `excluded`.
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
import premap  # noqa: E402
from premap.module_graph import normalize_image as _image, package_facts  # noqa: E402
from snapshot_store import open_snapshot  # noqa: E402

REGISTRY = SCRIPT_DIR.parent / "data" / "service-registry.json"
ECOSYSTEMS = {
    "npm": "npm", "pnpm": "npm", "lerna": "npm", "nx": "npm", "angular": "npm", "deno": "npm",
    "python": "pypi", "cargo": "crates", "go": "go", "maven": "maven", "gradle": "maven", "sbt": "maven",
    "dotnet": "nuget", "composer": "composer", "bundler": "rubygems", "rubygems": "rubygems",
    "pub": "pub", "melos": "pub", "swiftpm": "swiftpm", "mix": "hex", "terraform": "terraform",
}
OWN = ('"daodan/service-registry/', '"daodan/registry-additions/')
FRAMEWORK_OVERRIDES = frozenset({"playwright", "cypressci", "cypress", "opentelemetry"})
TOOL_IDS = frozenset({
    "docker", "eslint", "prettier", "renovate", "travisci", "githubpages", "vite", "webpack", "rollup",
    "esbuild", "babel", "biome", "stylelint", "ruff", "mypy", "black", "flake8", "rubocop", "phpstan",
    "checkstyle", "spotbugs", "gradle", "maven", "npm", "pnpm", "yarn", "bun", "nodejs", "python",
    "golang", "rust", "java", "kotlin", "dotnet", "helm", "terraform",
})
AMBIGUOUS_ENV = {
    "ZOOM_": re.compile(r"^ZOOM_(?:API|CLIENT|SECRET|WEBHOOK|ACCOUNT|SDK|OAUTH|JWT)_"),
    "GHOST_": re.compile(r"^GHOST_(?:API|ADMIN|CONTENT|URL|KEY)_"),
}
PACKAGE_EXCLUSIONS = frozenset({
    ("npm", "passport-google-oauth20", "gcp"),
    ("npm", "postman-collection", "postman"),
})


def load(path: Path | None = None) -> dict:
    return json.loads(Path(path or REGISTRY).read_text(encoding="utf-8"))


def _is_excluded(rel: str | None, left_out: tuple[str, ...]) -> bool:
    if not rel:
        return False
    return any(rel == path.rstrip("/") or rel.startswith(path.rstrip("/") + "/") for path in left_out if path)


def _split_declared_in(declared_in: str | None) -> tuple[str | None, int | None]:
    if not declared_in:
        return None, None
    file, sep, frag = str(declared_in).partition("#")
    if sep and frag.startswith("L") and frag[1:].isdigit():
        return file, int(frag[1:])
    return file, None


def step1_packages(manifest: Path, facts: dict) -> list[tuple[str, str, str | None, int | None]]:
    """(ecosystem, name, path, line) from Step 1's `packages`, `services` and `docker_builds`."""
    raw = facts.get("packages")
    if raw is None and "sources" not in facts:
        raw = package_facts(manifest)
    out: list[tuple[str, str, str | None, int | None]] = []
    for item in raw or ():
        path, line = _split_declared_in(item.get("declared_in"))
        out.append((item["ecosystem"], item["name"], path, line))
    seen = {sign[:3] for sign in out}
    for service in facts.get("services") or ():
        if service.get("image"):
            path = str(service["declared_in"]).split("#", 1)[0]
            img = _image(service["image"])
            if ("docker", img, path) not in seen:
                seen.add(("docker", img, path))
                out.append(("docker", img, path, None))
    for build in facts.get("docker_builds") or ():
        dockerfile = build.get("dockerfile")
        for stage in build.get("stages") or ():
            base = stage.get("base")
            if dockerfile and base and base != "scratch":
                img = _image(base)
                if ("docker", img, dockerfile) not in seen:
                    seen.add(("docker", img, dockerfile))
                    out.append(("docker", img, dockerfile, stage.get("line")))
    return out


def entry_category(entry: dict) -> str:
    if entry.get("id") in FRAMEWORK_OVERRIDES:
        return "framework"
    if entry.get("category"):
        return entry["category"]
    if entry.get("id") in TOOL_IDS:
        return "tool"
    return "service" if entry.get("kind") == "service" else "framework"


def recognize(manifest: Path, registry: dict | None = None, facts: dict | None = None) -> list[dict]:
    """Registry entries the snapshot shows signs of, each sign with its path and line; `facts` is the pre-map."""
    manifest = Path(manifest)
    facts = premap.ensure(manifest) if facts is None else facts
    entries = (registry or load())["entries"]
    left_out = tuple(item["path"] for item in facts.get("excluded") or () if item.get("path"))
    packages = [s for s in step1_packages(manifest, facts) if not _is_excluded(s[2], left_out)]
    with open_snapshot(manifest) as store:
        files = [rel for rel in sorted(dict(store.iter_file_headers_only())) if not _is_excluded(rel, left_out)]
        source = flows.Source(store)
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
                    patterns.append((ecosystem, re.compile(value, re.I), entry["id"]))
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
        low = name.lower()
        ids = list(by_package.get((ecosystem, low), []))
        if ecosystem == "maven" and ":" in low:
            ids += list(by_package.get((ecosystem, low.split(":", 1)[1]), []))
        if ecosystem == "go":
            ids += [i for (e, value), owners in by_package.items() if e == "go" and low.startswith(value + "/")
                    for i in owners]
        ids += [i for e, pattern, i in patterns if e == ecosystem and pattern.search(name)]
        filtered = [i for i in dict.fromkeys(ids) if (ecosystem, low, i) not in PACKAGE_EXCLUSIONS]
        add(filtered, "package", name, path, line)
    for rel in files:
        add(names.get(PurePosixPath(rel).name, []), "file", PurePosixPath(rel).name, rel, None)
    words = re.compile(r"\b(" + "|".join(sorted(map(re.escape, prefixes), key=len, reverse=True)) + r")[A-Z0-9_]*\b") \
        if prefixes else None
    places = re.compile("|".join(sorted(map(re.escape, hosts), key=len, reverse=True))) if hosts else None
    for rel, lines in texts.items():
        if any(mark in line for line in lines[:3] for mark in OWN):
            continue
        for number, line in enumerate(lines, 1):
            if len(line) > flows.snapshot.MAX_STYLESHEET_LINE:
                continue
            for match in words.finditer(line) if words else ():
                prefix, token = match.group(1), match.group(0)
                guard = AMBIGUOUS_ENV.get(prefix)
                if guard is not None and not guard.match(token):
                    continue
                add(prefixes[prefix], "env", token, rel, number)
            for match in places.finditer(line) if places else ():
                add(hosts[match.group(0)], "host", match.group(0), rel, number)
    by_id = {e["id"]: e for e in entries}
    out = []
    for ident in sorted(found):
        entry = by_id[ident]
        category = entry_category(entry)
        kind = "project" if category != "service" else "service"
        signs = {(s["sign"], s["value"], s["path"], s["line"]): s for s in found[ident]}
        out.append({"id": entry.get("id"), "name": entry.get("name"), "kind": kind, "category": category,
                    "type": entry.get("type"), "site": entry.get("site"), "icon": entry.get("icon"),
                    "source": "registry",
                    "signs": sorted(signs.values(), key=lambda s: (s["sign"], s["path"] or "", s["line"] or 0, s["value"]))})
    return out
