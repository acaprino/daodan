#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# ///
"""The registry of technologies, frameworks, tools and external services, and what the stack step reads of Step 1's facts.

`load` the registry and `mark_file` the SVG of an entry, `entry_category` its category; `step1_packages` the declared
packages and images of the pre-map's `packages`, `services` and `docker_builds` (or `premap.module_graph.package_facts`
only when a caller passes a partial `facts` stub in tests), `package_key` the identity a package is compared by. What a
project shows of the registry's technologies is recognized by `stack_recognition`.
"""
from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
import json
import re
import sys
import threading
from pathlib import Path, PurePosixPath
from typing import NamedTuple

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import premap  # noqa: E402
from premap.module_graph import declared_image, package_facts  # noqa: E402
from mark_svg import MAX_MARK, clean_svg, safe_member  # noqa: E402
from module_inventory import _Inventory  # noqa: E402

REGISTRY = SCRIPT_DIR.parent / "data" / "service-registry.json"


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


def marked() -> set[str]:
    """The ids of the entries with a mark (`mark_file`): what a page may ask the image of."""
    return {entry["id"] for entry in load()["entries"] if entry.get("mark") or entry.get("mark_source")}


class Marks:
    """The marks of the registry's entries, for the servers of the pages. An id is only looked up among the entries,
    so none is a path; without a registry no id is known."""

    def __init__(self):
        self.entries = {entry["id"]: entry for entry in load()["entries"]} if REGISTRY.is_file() else {}
        self._fetched, self._fetch = {}, ThreadPoolExecutor(max_workers=1)  # the packages' marks, one at a time
        self._lock = threading.Lock()

    def file(self, ident: str | None) -> Path | None:
        """The mark of the entry `ident` (`mark_file`), or None: the page draws the icon of the node's type. A mark
        taken out of its owner's package on first use is fetched off the request: until it is there, and after it
        failed, the answer is None, so that no page or graph waits on a download."""
        entry = self.entries.get(ident)
        if entry is None:
            return None
        if entry.get("mark") or not entry.get("mark_source"):
            return mark_file(entry)
        with self._lock:
            if ident not in self._fetched:
                self._fetched[ident] = self._fetch.submit(mark_file, entry)
            fetched = self._fetched[ident]
        return fetched.result() if fetched.done() else None

    def close(self) -> None:
        self._fetch.shutdown(wait=False, cancel_futures=True)


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
    the package fact's (as its manifest writes it), None for none and for an image. A package a central file
    declares is also at each file that uses it (`used_in`), with the central version: the module's link to it."""
    raw = facts.get("packages")
    if raw is None and "sources" not in facts:
        raw = package_facts(manifest)
    out: list[tuple[str, str, str | None, int | None, str | None]] = []
    for item in raw or ():
        for place in [item.get("declared_in"), *(item.get("used_in") or ())]:
            path, line = _split_declared_in(place)
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


def _lines(inventory: _Inventory, rel: str) -> list[str]:
    """A file's lines; none from a file changed since the inventory or that cannot be read."""
    try:
        return inventory.text(rel).split("\n")
    except ValueError:
        return []
