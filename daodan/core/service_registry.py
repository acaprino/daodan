#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# ///
"""Technologies, frameworks, tools and external services of a snapshot, recognized from Step 1 facts and the registry.

Consumes the pre-map's `packages`, `services`, `docker_builds` and `excluded` without re-parsing manifests,
requirements files, Dockerfiles or Compose files; falls back to `premap.module_graph.package_facts` only when a caller
passes a partial `facts` stub in tests. Every sign respects `excluded`.

A checker reads one kind of the registry's signs and names no technology: `checker(entries, project)` answers
`{"signs": [(entry id, value, path, line)], "gaps": [...]}`. `run` runs `CHECKERS` in order; each sign found carries
its checker (`sign`) and the checker's strength: `declared`, a package, image, file or explicit source reference, or
`mentioned`, a token in a line of text. A checker that fails is a gap with its cause, and the others still run.
An exact host in a source literal or configuration value is a mention.
"""
from __future__ import annotations

from collections.abc import Callable
import json
import re
import sys
from pathlib import Path, PurePosixPath
from typing import NamedTuple

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import flows  # noqa: E402
import premap  # noqa: E402
from registry_hosts import check_hosts  # noqa: E402
from stack_source import check_sources  # noqa: E402
from premap.module_graph import declared_image, package_facts  # noqa: E402
from mark_svg import MAX_MARK, clean_svg, safe_member  # noqa: E402
from module_inventory import _Inventory  # noqa: E402
from snapshot_store import open_snapshot  # noqa: E402

REGISTRY = SCRIPT_DIR.parent / "data" / "service-registry.json"
OWN = ('"daodan/service-registry/', '"daodan/registry-additions/')


def load(path: Path | None = None) -> dict:
    return json.loads(Path(path or REGISTRY).read_text(encoding="utf-8"))


def mark_file(entry: dict, data: Path | None = None) -> Path | None:
    """The SVG a page shows for an entry's mark, or None: the file shipped in `marks/`, or the one the owner's package
    holds (`mark_source`), taken out on first use into the folder of the shared download, clean (`clean_svg`).

    The package comes through `preparation.fetched`, which checks its sha256; only the member named is read, never
    extracted. Any failure (no network, a package that changed, a member that is missing, too large or not safe) is
    None: the graph then draws the generic icon of the entry's type."""
    data = data or REGISTRY.parent
    if entry.get("mark"):
        path = data / entry["mark"]
        return path if path.is_file() else None
    source = entry.get("mark_source")
    try:
        import hashlib
        import zipfile
        from urllib.parse import urlparse
        import preparation
        member = source["member"]
        if not safe_member(member):
            return None
        package = preparation.fetched(source["url"], source["sha256"], PurePosixPath(urlparse(source["url"]).path).name)
        out = package.parent / "marks" / re.sub(r"[^\w.-]+", "_", member)
        if out.is_file() and clean_svg(out.read_bytes()) == out.read_text(encoding="utf-8"):
            return out
        if hashlib.sha256(package.read_bytes()).hexdigest() != source["sha256"]:
            return None
        with zipfile.ZipFile(package) as archive, archive.open(member) as file:
            svg = clean_svg(file.read(MAX_MARK + 1))
        out.parent.mkdir(exist_ok=True)
        out.write_text(svg, encoding="utf-8", newline="\n")
        return out
    except Exception:  # noqa: BLE001 - whatever the download, the archive or the file does, the answer is no mark
        return None


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


def service_site(service: dict) -> tuple[str | None, int | None]:
    """The source file even for a Compose invocation identified by its numbered step inside a shell script."""
    location = service["declared_in"].removesuffix(f".services.{service.get('name')}")
    return _split_declared_in(service.get("source_path") or location)


def step1_packages(manifest: Path, facts: dict) -> list[tuple[str, str, str | None, int | None, str | None]]:
    """(ecosystem, name, path, line, version) from Step 1's `packages`, `services` and `docker_builds`; `version`,
    the package fact's (as its manifest writes it), None for none and for an image."""
    raw = facts.get("packages")
    if raw is None and "sources" not in facts:
        raw = package_facts(manifest)
    out: list[tuple[str, str, str | None, int | None, str | None]] = []
    for item in raw or ():
        path, line = _split_declared_in(item.get("declared_in"))
        out.append((item["ecosystem"], item["name"], path, line, item.get("version")))
    seen = {("docker", declared_image(name), path) for eco, name, path, *_ in out if eco == "docker"}
    for service in facts.get("services") or ():
        if service.get("image"):
            path, _ = service_site(service)
            img = declared_image(service["image"])
            if img and ("docker", img, path) not in seen:
                seen.add(("docker", img, path))
                out.append(("docker", img, path, None, None))
    for build in facts.get("docker_builds") or ():
        dockerfile = build.get("dockerfile")
        for stage in build.get("stages") or ():
            base = stage.get("base")
            if dockerfile and base and base != "scratch":
                img = declared_image(base)
                if img and ("docker", img, dockerfile) not in seen:
                    seen.add(("docker", img, dockerfile))
                    out.append(("docker", img, dockerfile, stage.get("line"), None))
    return out


def entry_category(entry: dict) -> str:
    """The entry's `category`; without one, a service when its kind is, else a framework."""
    return entry.get("category") or ("service" if entry.get("kind") == "service" else "framework")


class Project(NamedTuple):
    """What a checker reads, without what the pre-map excludes: the declared packages and images
    (`step1_packages`), the files, and a file's lines."""
    packages: list[tuple[str, str, str | None, int | None, str | None]]
    files: list[str]
    lines: Callable[[str], list[str]]


def package_key(ecosystem: str, name: str) -> str:
    """Compare PyPI distribution names by PEP 503 and Docker images by repository identity."""
    if ecosystem == "docker":
        return declared_image(name)
    return premap.normalize_pypi_name(name) if ecosystem == "pypi" else name.lower()


def check_packages(entries: list[dict], project: Project) -> dict:
    """A declared package or image, by its name in its ecosystem, a Maven artifact without its group, a Go package
    under a module or an entry's pattern. One no entry knows, named like an entry with no sign in its ecosystem, is a
    gap: the registry lacks that sign."""
    by_package, patterns, named = {}, [], {}
    for entry in entries:
        signs = entry.get("signs") or {}
        for ecosystem, values in (signs.get("packages") or {}).items():
            for value in values:
                by_package.setdefault((ecosystem, package_key(ecosystem, value)), []).append(entry["id"])
        for ecosystem, values in (signs.get("patterns") or {}).items():
            for value in values:
                try:
                    # A bare Docker selector names a Hub repository or publisher; explicit prefix rules stay anchored.
                    if ecosystem == "docker" and not value.startswith("^"):
                        end = "$" if "/" in value else "(?:/|$)"
                        value = f"^(?:{value}){end}"
                    patterns.append((ecosystem, re.compile(value, re.I), entry["id"]))
                except re.error:
                    continue
        for key in (entry["id"], entry.get("name") or ""):
            named.setdefault(key.casefold(), entry)
    found, gaps, seen = [], [], set()
    for ecosystem, name, path, line, *_ in project.packages:  # a version is no sign
        low = package_key(ecosystem, name)
        ids = list(by_package.get((ecosystem, low), []))
        if ecosystem == "maven" and ":" in low:
            ids += by_package.get((ecosystem, low.split(":", 1)[1]), [])
        if ecosystem == "go":
            ids += [i for (e, value), owners in by_package.items() if e == "go" and low.startswith(value + "/")
                    for i in owners]
        ids += [i for e, pattern, i in patterns if e == ecosystem and pattern.search(low if e == "docker" else name)]
        found += [(ident, name, path, line) for ident in dict.fromkeys(ids)]
        entry = None if ids else named.get(name.casefold()) or named.get(re.split(r"[:/]", name.casefold())[-1])
        signs = (entry or {}).get("signs") or {}
        if entry and (entry["id"], ecosystem) not in seen and not any(
                ecosystem in (signs.get(kind) or {}) for kind in ("packages", "patterns")):
            seen.add((entry["id"], ecosystem))
            gaps.append({"kind": "no_ecosystem_sign", "entry": entry["id"], "ecosystem": ecosystem, "value": name,
                         "path": path, "line": line})
    return {"signs": found, "gaps": gaps}


def check_files(entries: list[dict], project: Project) -> dict:
    """A file of the project, by its name."""
    names = {}
    for entry in entries:
        for value in (entry.get("signs") or {}).get("files") or []:
            names.setdefault(value, []).append(entry["id"])
    found = []
    for rel in project.files:
        name = PurePosixPath(rel).name
        found += [(ident, name, rel, None) for ident in names.get(name, [])]
    return {"signs": found, "gaps": []}


def check_env(entries: list[dict], project: Project) -> dict:
    """A token starting with an entry's prefix in a line of text, outside the registry's own files and minified
    lines."""
    prefixes = {}
    for entry in entries:
        for value in (entry.get("signs") or {}).get("env") or []:
            prefixes.setdefault(value, []).append(entry["id"])
    if not prefixes:
        return {"signs": [], "gaps": []}
    words = re.compile(r"\b(" + "|".join(sorted(map(re.escape, prefixes), key=len, reverse=True)) + r")[A-Z0-9_]*\b")
    found = []
    for rel in project.files:
        lines = project.lines(rel)
        if any(mark in line for line in lines[:3] for mark in OWN):
            continue
        for number, line in enumerate(lines, 1):
            if len(line) <= flows.snapshot.MAX_STYLESHEET_LINE:
                found += [(ident, match.group(0), rel, number) for match in words.finditer(line)
                          for ident in prefixes[match.group(1)]]
    return {"signs": found, "gaps": []}


CHECKERS = (("package", "declared", check_packages), ("file", "declared", check_files),
            ("env", "mentioned", check_env), ("host", "mentioned", check_hosts), ("source", "declared", check_sources))


def _lines(inventory: _Inventory, rel: str) -> list[str]:
    """A file's lines; none from a file changed since the inventory or that cannot be read."""
    try:
        return inventory.text(rel).split("\n")
    except ValueError:
        return []


def run(manifest: Path, registry: dict | None = None, facts: dict | None = None) -> dict:
    """`CHECKERS` over the snapshot: the registry entries it shows signs of (`found`), each sign with its path, line
    and strength, each checker's status (`checkers`) and the `gaps`; `facts` is the pre-map."""
    manifest = Path(manifest)
    facts = premap.ensure(manifest) if facts is None else facts
    entries = (registry or load())["entries"]
    left_out = tuple(item["path"] for item in facts.get("excluded") or () if item.get("path"))
    declared = [s for s in step1_packages(manifest, facts) if not _is_excluded(s[2], left_out)]
    found: dict[str, list[dict]] = {}
    checkers, gaps = [], []
    with open_snapshot(manifest) as store:
        # The files the inventory lists, their text checked against its hash: `stack` runs before `parse`.
        inventory = _Inventory(store)
        files = [rel for rel in inventory.files if not _is_excluded(rel, left_out)]
        project = Project(declared, files, lambda rel: _lines(inventory, rel))
        for name, strength, checker in CHECKERS:
            try:
                answer = checker(entries, project)
                signs = [(ident, {"sign": name, "value": value, "path": path, "line": line, "strength": strength})
                         for ident, value, path, line in answer["signs"]]
                more = [{**gap, "checker": name} for gap in answer.get("gaps") or ()]
            except Exception as error:  # a checker's failure is its gap, never the end of the others
                reason = f"{type(error).__name__}: {error}"
                checkers.append({"checker": name, "state": "failed", "reason": reason})
                gaps.append({"kind": "checker_failed", "checker": name, "detail": reason})
                continue
            checkers.append({"checker": name, "state": "ran"})
            gaps += more
            for ident, sign in signs:
                found.setdefault(ident, []).append(sign)
    by_id = {e["id"]: e for e in entries}
    out = []
    for ident in sorted(found):
        entry = by_id[ident]
        category = entry_category(entry)
        kind = "project" if category != "service" else "service"
        signs = {(s["sign"], s["value"], s["path"], s["line"]): s for s in found[ident]}
        out.append({"id": entry.get("id"), "name": entry.get("name"), "kind": kind, "category": category,
                    "type": entry.get("type"), "site": entry.get("site"), "mark": entry.get("mark"),
                    "source": "registry",
                    "signs": sorted(signs.values(), key=lambda s: (s["sign"], s["path"] or "", s["line"] or 0, s["value"]))})
    return {"found": out, "checkers": checkers, "gaps": gaps}


def recognize(manifest: Path, registry: dict | None = None, facts: dict | None = None) -> list[dict]:
    """Registry entries the snapshot shows signs of, each sign with its path and line (`run`'s `found`)."""
    return run(manifest, registry, facts)["found"]
