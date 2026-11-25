#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# ///
"""Build the registry of external services and projects from public catalogs. A development tool.

Sources, at fixed versions: the catalogue of rules of the stack-analyser release Daodan runs (`stack_analyser.catalogue`:
id, name, type and hosts of each rule; MIT, a fork of specfy/stack-analyser), which makes the register of names and
leaves the recognizing to the release; the marks of Simple Icons (CC0), joined by name and written, clean, as one SVG
per entry in `data/marks/ID.svg` (the entry's `mark`), and the official marks of the services Simple Icons lacks
(`add-mark`: the owner's file, its URL, the day and its terms, or with `--own` a drawing of Daodan's, kept in the
additions and in REGISTRY-NOTICES.md);
the entries of the CNCF Landscape (CC BY 4.0) with name, category and site; and
`registry-additions.json`, what the catalogs lack: a name, a site, a category, a mark, the name of the CNCF item that is the
entry when the two write it otherwise (`cncf`). An entry has no signs: what a
project shows is the release's, and the additions may not hold any.

    python registry_build.py build --out FILE [--cache DIR]
    python registry_build.py check FILE        # also the marks beside FILE: each file named, clean, none left over
    python registry_build.py marks [--registry FILE] [--additions FILE] [--cache DIR]
    python registry_build.py add-mark ID SVG (--url URL [--terms URL] | --own)
    python registry_build.py add-package-mark ID ZIP --url URL --member PATH --terms URL
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys
import tarfile
import time
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import flows  # noqa: E402
import stack_analyser  # noqa: E402
from container import Gap  # noqa: E402
from mark_svg import clean_svg, safe_member  # noqa: E402

SCHEMA = "daodan/service-registry/v1"
ADDITIONS_SCHEMA = "daodan/registry-additions/v1"
DATA = SCRIPT_DIR.parent / "data"
SOURCES = ("stack-analyser", "simple-icons", "cncf-landscape", "additions")
KINDS = ("service", "project")
CATEGORIES = ("framework", "library", "tool", "service")
SUPPORT = ("full", "partial", "none")  # an entry's `support`, written by `support`
# An entry Daodan reads beyond recognizing it, and the module of the reader, from `core/`: the framework's own tool
# for its routes or the events of its templates (`premap.FRAMEWORK_SOURCES`, `premap.TEMPLATE_SOURCES`), its compiler
# for the styles of its components, the project's Tailwind for its utilities.
READERS = {"angular": "premap/angular.py", "astro": "premap/astro.py", "nextjs": "premap/nextjs.py",
           "nuxtjs": "premap/nuxt.py", "reactrouterdom": "premap/react_router.py", "remixrun": "premap/react_router.py",
           "sveltejs": "indexers/css_svelte.py", "sveltekit": "premap/sveltekit.py",
           "tailwind": "indexers/css_tailwind.py", "vue": "indexers/css_vue.py"}
MIN_ENTRIES = 1000
MARKS = "marks"  # the folder of the marks, beside the registry: one SVG per entry, named by the entry's id
MARK_PATH = re.compile(rf"{MARKS}/[a-z0-9][a-z0-9._-]*\.svg")
SIMPLE_ICONS = ("simple-icons", "16.37.0")
CNCF_COMMIT = "75b47639d132b3a7afa31ecc84a90f61b8072dd6"
AGENT = "daodan-registry-build"
# stack-analyser dependency types, as ecosystems (`stack_recognition` reads them the other way round).
ECOSYSTEMS = {"npm": "npm", "python": "pypi", "rust": "crates", "golang": "go", "ruby": "rubygems", "php": "composer",
              "docker": "docker", "githubAction": "github-actions", "terraform": "terraform",
              "terraform.resource": "terraform-resource", "deno": "deno"}
# stack-analyser technology types, as node types; the ones not here are projects of type `altro`.
SERVICE_TYPES = {"db": "database", "storage": "database", "queue": "coda", "messaging": "coda",
                 "auth": "autenticazione", "payment": "gateway"}
SERVICES = {"ai", "analytics", "api", "app", "automation", "ci", "cloud", "cms", "collaboration", "communication",
            "crm", "etl", "hosting", "maps", "monitoring", "network", "notification", "saas", "security"}
CNCF_TYPES = {"Database": "database", "Vector Database": "database", "Cloud Native Storage": "database",
              "Streaming & Messaging": "coda", "API Gateway": "gateway", "Gateway": "gateway",
              "Key Management": "autenticazione"}
CNCF_HOSTED = {"Certified Kubernetes - Hosted", "PaaS/Container Service", "Hosted Platform", "Hosted Platforms"}
CNCF_SKIPPED = {"CNCF Members", "Special"}  # companies and certified vendors, not services or projects


# ---------------------------------------------------------------- support

def support(entry: dict) -> str:
    """How far Daodan supports an entry: `none` when the fork has no rule for it (`from`), so no project shows it;
    `partial` when the fork recognizes it and Daodan reads nothing more of it; `full` when a reader of `READERS`
    does."""
    if "stack-analyser" not in entry["from"]:
        return "none"
    return "full" if entry["id"] in READERS else "partial"


# ---------------------------------------------------------------- check

def check(value: object, data: Path | None = None, additions: list[dict] | None = None) -> list[str]:
    """What breaks the registry's rules, one line each; empty when it holds.

    With `data`, the folder that holds the registry, the marks it names must be there, clean, and no other. With
    `additions`, their records: none may hold signs, which are the release's."""
    if not isinstance(value, dict) or value.get("schema") != SCHEMA or not isinstance(value.get("entries"), list):
        return [f"the registry is {SCHEMA} with a list of entries"]
    problems, seen = [], set()
    if len(value["entries"]) < MIN_ENTRIES:
        problems.append(f"{len(value['entries'])} entries, at least {MIN_ENTRIES} wanted")
    for entry in value["entries"]:
        ident = entry.get("id")
        if ident in seen:
            problems.append(f"{ident}: the id repeats")
        seen.add(ident)
        if not isinstance(entry.get("name"), str) or not entry["name"].strip():
            problems.append(f"{ident}: no name")
        if entry.get("kind") not in KINDS:
            problems.append(f"{ident}: kind is one of {', '.join(KINDS)}")
        if entry.get("category") is not None and entry.get("category") not in CATEGORIES:
            problems.append(f"{ident}: category is one of {', '.join(CATEGORIES)}")
        if entry.get("type") not in flows.NODE_TYPES:
            problems.append(f"{ident}: type is one of {', '.join(flows.NODE_TYPES)}")
        if "signs" in entry:
            problems.append(f"{ident}: no signs, the rules are the fork's")
        if "support" in entry and entry.get("from") and entry["support"] != support(entry):
            problems.append(f"{ident}: support is {support(entry)}, what its rule and READERS give")
        hosts = entry.get("hosts")
        if "hosts" in entry and not (isinstance(hosts, list) and hosts and all(isinstance(h, str) and h for h in hosts)):
            problems.append(f"{ident}: hosts are a list of at least one host")
        if not entry.get("from") or not set(entry["from"]) <= set(SOURCES):
            problems.append(f"{ident}: from names one or more of {', '.join(SOURCES)}")
        mark, package = entry.get("mark"), entry.get("mark_source")
        if mark is not None and not (isinstance(mark, str) and MARK_PATH.fullmatch(mark)):
            problems.append(f"{ident}: mark is null or a file like {MARKS}/NAME.svg")
        elif mark and data is not None:
            problems += _mark_problems(ident, mark, data)
        if mark and package:
            problems.append(f"{ident}: mark and mark_source are two cases, an entry has one")
        if package is not None and not _package_ok(package):
            problems.append(f"{ident}: mark_source is {', '.join(PACKAGE_KEYS)}: https URLs, the sha256 and a safe member")
    problems += [f"additions: {record.get('id')} has {field}, the rules are the fork's"
                 for record in additions or () for field in ("signs", "wrong_signs") if field in record]
    if data is not None:
        named = {e.get("mark") for e in value["entries"]}
        problems += [f"{MARKS}/{f.name}: no entry names this file" for f in sorted((data / MARKS).glob("*"))
                     if f"{MARKS}/{f.name}" not in named]
    return problems


PACKAGE_KEYS = ("url", "sha256", "member", "terms")  # the official package a mark is downloaded from


def _package_ok(package: object) -> bool:
    return (isinstance(package, dict) and set(package) == set(PACKAGE_KEYS)
            and all(isinstance(package[k], str) and package[k].startswith("https://") for k in ("url", "terms"))
            and isinstance(package["sha256"], str) and re.fullmatch(r"[0-9a-f]{64}", package["sha256"]) is not None
            and safe_member(package["member"]))


def _mark_problems(ident: str, mark: str, data: Path) -> list[str]:
    path = data / mark
    if not path.is_file():
        return [f"{ident}: {mark} is missing"]
    try:
        text = path.read_text(encoding="utf-8")
        if clean_svg(text.encode("utf-8")) == text:
            return []
    except (ValueError, UnicodeDecodeError):
        pass
    return [f"{ident}: {mark} is not what the sanitiser makes of it"]


# ---------------------------------------------------------------- names

def _norm(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(name).casefold())


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(name).casefold()).strip("-")


# ---------------------------------------------------------------- marks

_COMPANY = {"inc", "ltd", "llc", "corp", "corporation", "gmbh", "co", "company", "limited"}


def mark_index(icons: list[dict]) -> dict[str, dict]:
    """Simple Icons by every name the collection gives an icon: title, slug, `aka`, `dup` and `loc`."""
    index = {}
    for icon in icons:
        aliases = icon.get("aliases", {})
        names = [icon["title"], icon["slug"], *aliases.get("aka", []), *(d["title"] for d in aliases.get("dup", [])),
                 *aliases.get("loc", {}).values()]
        for name in names:
            index.setdefault(_norm(name), icon)
    return index


def simple_icon(entry: dict, index: dict[str, dict]) -> dict | None:
    """The icon that has the entry's name (or its id) up to case, punctuation and a closing company word."""
    words = re.findall(r"[a-z0-9]+", entry["name"].casefold())
    if len(words) > 1 and words[-1] in _COMPANY:
        words = words[:-1]
    return index.get("".join(words)) or index.get(_norm(entry["name"])) or index.get(_norm(entry["id"]))


def apply_marks(entries: dict[str, dict], icons: list[dict], read_svg, data: Path, official: dict[str, dict]) -> list[str]:
    """Give each entry its mark: the Simple Icons one, written clean into `data/marks`, else its official one
    (`official`: id to a record with `mark`, a file kept as it is, or `mark_source`, a package it is downloaded from).
    Files nobody names are removed. Returns what it refused, one line each."""
    index, refused, keep = mark_index(icons), [], set()
    folder = data / MARKS
    folder.mkdir(parents=True, exist_ok=True)
    for ident, entry in entries.items():
        record = official.get(ident) or {}
        sources, mark, package = set(entry["from"]) - {"simple-icons"}, record.get("mark"), record.get("mark_source")
        icon = simple_icon(entry, index)
        if icon:
            try:
                svg = clean_svg(read_svg(icon["slug"]), "#" + icon["hex"])
            except (ValueError, OSError) as error:
                refused.append(f"{ident}: {icon['slug']}: {error}")
            else:
                mark, package = f"{MARKS}/{ident.lower()}.svg", None
                (data / mark).write_text(svg, encoding="utf-8", newline="\n")
                sources.add("simple-icons")
        entry["mark"], entry["from"] = mark, sorted(sources)
        entry.pop("mark_source", None)
        if package and not mark:
            entry["mark_source"] = package
        if mark:
            keep.add(Path(mark).name)
    for stale in folder.glob("*"):
        if stale.name not in keep:
            stale.unlink()
    return refused


# ---------------------------------------------------------------- network

def _get(url: str, timeout: int = 30) -> bytes | None:
    request = urllib.request.Request(url, headers={"User-Agent": AGENT, "Accept": "application/json"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return response.read()
        except urllib.error.HTTPError as error:
            if error.code in (404, 410):
                return None
            if error.code != 429 and error.code < 500:
                return None
        except (urllib.error.URLError, TimeoutError, OSError):
            pass
        time.sleep(2 ** attempt)
    return None


def _tarball(name: str, version: str, cache: Path) -> Path:
    """An npm package's files, unpacked once into the cache; no install scripts run."""
    target = cache / f"{name.replace('/', '__')}-{version}"
    if not (target / "package.json").is_file():
        base = name.rsplit("/", 1)[-1]
        data = _get(f"https://registry.npmjs.org/{name}/-/{base}-{version}.tgz", timeout=120)
        if data is None:
            raise RuntimeError(f"cannot download {name}@{version}")
        target.mkdir(parents=True, exist_ok=True)
        with tarfile.open(fileobj=io.BytesIO(data)) as archive:
            for member in archive.getmembers():
                member.name = member.name.split("/", 1)[1] if "/" in member.name else member.name
            archive.extractall(target, filter="data")
    return target


# ---------------------------------------------------------------- sources

def simple_icons(cache: Path) -> list[dict]:
    root = _tarball(*SIMPLE_ICONS, cache)
    return json.loads((root / "data" / "simple-icons.json").read_text(encoding="utf-8"))


def cncf_items(cache: Path) -> list[dict]:
    """Items of landscape.yml with their category and subcategory; read line by line, its layout is fixed."""
    path = cache / f"cncf-landscape-{CNCF_COMMIT}.yml"
    if not path.is_file():
        data = _get(f"https://raw.githubusercontent.com/cncf/landscape/{CNCF_COMMIT}/landscape.yml", timeout=120)
        if data is None:
            raise RuntimeError("cannot download the CNCF landscape")
        path.write_bytes(data)
    items, marker, category, subcategory, item = [], None, None, None, None
    for line in path.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if text in ("- category:", "- subcategory:", "- item:"):
            marker = text[2:-1]
            if marker == "item":
                item = {"category": category, "subcategory": subcategory}
                items.append(item)
            continue
        match = re.match(r"(name|homepage_url|repo_url):\s*(.*)$", text)
        if not match:
            continue
        value = match.group(2).strip().strip("'\"")
        if marker == "category" and match.group(1) == "name":
            category, marker = value, None
        elif marker == "subcategory" and match.group(1) == "name":
            subcategory, marker = value, None
        elif marker == "item" and item is not None and match.group(1) not in item:
            item[match.group(1)] = value
    return items


# ---------------------------------------------------------------- build

# stack-analyser technology types, as the category of an entry the additions give none: the majority of the
# categories curated for the types, which this table does not replace. A release with a type not here stops the build.
CATEGORY_OF_TYPE = {
    "ai": "service", "analytics": "service", "api": "service", "app": "service", "auth": "service",
    "automation": "service", "ci": "service", "cloud": "service", "cms": "service", "collaboration": "service",
    "communication": "service", "crm": "service", "db": "service", "etl": "service", "hosting": "service",
    "maps": "service", "messaging": "service", "monitoring": "service", "network": "service",
    "notification": "service", "payment": "service", "queue": "service", "saas": "service", "security": "service",
    "storage": "service",
    "builder": "tool", "iac": "tool", "language": "tool", "linter": "tool", "package_manager": "tool",
    "runtime": "tool", "test": "tool",
    "framework": "framework", "ssg": "framework", "ui_framework": "framework",
    "iconset": "library", "orm": "library", "tool": "library", "ui": "library", "validation": "library",
}


def _from_rule(rule: dict) -> dict:
    """The entry of a rule of the catalogue: what it names, no sign. `hosts` only when the rule has some."""
    if rule["type"] not in CATEGORY_OF_TYPE:
        raise ValueError(f"{rule['tech']}: no category for the type {rule['type']}; add it to CATEGORY_OF_TYPE")
    kind = "service" if rule["type"] in SERVICES or rule["type"] in SERVICE_TYPES else "project"
    node_type = SERVICE_TYPES.get(rule["type"], "servizio o API" if kind == "service" else "altro")
    entry = {"id": rule["tech"], "name": rule["name"], "kind": kind, "type": node_type, "site": None, "mark": None,
             "from": ["stack-analyser"], "category": CATEGORY_OF_TYPE[rule["type"]]}
    if rule.get("hosts"):
        entry["hosts"] = list(rule["hosts"])
    return entry


def apply_additions(entries: dict[str, dict], records: list[dict]) -> None:
    """Merge curated `additions` records into `entries` in place. The records that make an entry (they have its
    `name`) come first, whatever their order: another may only add to it."""
    for record in sorted(records, key=lambda record: "name" not in record):
        entry = entries.get(record["id"])
        if entry is None:
            entry = entries[record["id"]] = {"id": record["id"], "name": record["name"], "kind": record["kind"],
                                             "type": record["type"], "site": None, "mark": None, "from": []}
        for name in ("name", "kind", "type", "site", "category", "mark", "mark_source"):
            if record.get(name):
                entry[name] = record[name]
        if record.get("mark"):
            entry.pop("mark_source", None)  # a file and a package are two cases: the record's file stays
        entry["from"] = sorted(set(entry["from"]) | {"additions"})


def build(cache: Path, additions: Path, data: Path) -> dict:
    entries, by_name = {}, {}
    records = json.loads(additions.read_text(encoding="utf-8"))["entries"] if additions.is_file() else []
    for rule in stack_analyser.catalogue():
        entry = _from_rule(rule)
        entries[entry["id"]] = entry
        by_name.setdefault(_norm(entry["name"]), entry["id"])
    # A CNCF item whose name the rule writes otherwise (`Kafka`, `Apache Kafka`) joins the entry whose record names it.
    by_name |= {_norm(r["cncf"]): r["id"] for r in records if r.get("cncf") and r["id"] in entries}
    for item in cncf_items(cache):
        if item["category"] in CNCF_SKIPPED or not item.get("name"):
            continue
        found = by_name.get(_norm(item["name"]))
        if found:
            entry = entries[found]
            entry["site"] = entry["site"] or item.get("homepage_url")
            entry["from"] = sorted(set(entry["from"]) | {"cncf-landscape"})
            continue
        hosted = item["subcategory"] in CNCF_HOSTED
        ident = _slug(item["name"])
        while ident in entries:
            ident += "-cncf"
        entries[ident] = {"id": ident, "name": item["name"], "kind": "service" if hosted else "project",
                          "type": CNCF_TYPES.get(item["subcategory"], "servizio o API" if hosted else "altro"),
                          "site": item.get("homepage_url"), "mark": None, "from": ["cncf-landscape"]}
        by_name[_norm(item["name"])] = ident
    apply_additions(entries, records)
    root = _tarball(*SIMPLE_ICONS, cache)
    refused = apply_marks(entries, simple_icons(cache), lambda slug: (root / "icons" / f"{slug}.svg").read_bytes(), data,
                          {r["id"]: r for r in records if r.get("mark") or r.get("mark_source")})
    if refused:
        print("\n".join(refused), file=sys.stderr)
    for entry in entries.values():
        entry["support"] = support(entry)
    return {"schema": SCHEMA, "versions": {"stack-analyser": stack_analyser.VERSION, "simple-icons": SIMPLE_ICONS[1],
                                           "cncf-landscape": CNCF_COMMIT},
            "entries": [entries[i] for i in sorted(entries)]}


def _write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")


def sync_additions(incoming: list[dict], registry: Path, additions: Path) -> int:
    """Merge records into the additions and into the registry the way `build` does; refuse what breaks `check`."""
    add_doc = json.loads(additions.read_text(encoding="utf-8"))
    by_key = {(e["id"], e.get("by")): e for e in add_doc["entries"]}
    for item in incoming:
        if item.get("mark") or item.get("mark_source"):  # one record gives an entry its mark: the new one
            for key in [k for k, e in by_key.items() if k[0] == item["id"] and (e.get("mark") or e.get("mark_source"))]:
                del by_key[key]
        by_key[(item["id"], item.get("by"))] = item
    add_doc["entries"] = sorted(by_key.values(), key=lambda e: (e["id"], e.get("by") or ""))
    reg_doc = json.loads(registry.read_text(encoding="utf-8"))
    entries = {e["id"]: e for e in reg_doc["entries"]}
    apply_additions(entries, incoming)
    reg_doc["entries"] = [entries[k] for k in sorted(entries)]
    problems = check(reg_doc, registry.parent, add_doc["entries"])
    if problems:
        print("\n".join(problems), file=sys.stderr)
        return 1
    _write(additions, add_doc)
    _write(registry, reg_doc)
    print(f"{len(reg_doc['entries'])} entries -> {registry}")
    return 0


def add_mark(ident: str, source: Path, url: str | None, terms: str | None, registry: Path, additions: Path,
             own: bool = False) -> int:
    """Take an SVG into `marks/` (clean) and record where it came from: the owner's file at `url`, or with `own` a
    drawing of Daodan's, which takes the place of a package's. One that Simple Icons has is refused."""
    entry = next((e for e in json.loads(registry.read_text(encoding="utf-8"))["entries"] if e["id"] == ident), None)
    if entry is None or "simple-icons" in entry["from"]:
        print(f"{ident}: no such entry, or its mark is the one of Simple Icons", file=sys.stderr)
        return 1
    try:
        svg = clean_svg(source.read_bytes())
    except ValueError as error:
        print(f"{ident}: {source.name}: {error}", file=sys.stderr)
        return 1
    mark = f"{MARKS}/{ident.lower()}.svg"
    (registry.parent / MARKS).mkdir(exist_ok=True)
    (registry.parent / mark).write_text(svg, encoding="utf-8", newline="\n")
    today = date.today().isoformat()
    source_record = {"drawn_by": "Daodan", "date": today} if own else {
        "url": url, **({"terms": terms} if terms else {}), "date": today}
    return sync_additions([{"id": ident, "mark": mark, "mark_origin": source_record,
                            "by": "daodan" if own else "official"}], registry, additions)


def add_package_mark(ident: str, url: str, archive: Path, member: str, terms: str, registry: Path, additions: Path) -> int:
    """Record that an entry's mark is `member` of the owner's package at `url`, which `archive` is a copy of: its
    sha256 is taken, and the member must come out of `clean_svg`. Nothing of the package is kept in the repository."""
    import hashlib
    import zipfile
    entry = next((e for e in json.loads(registry.read_text(encoding="utf-8"))["entries"] if e["id"] == ident), None)
    if entry is None or "simple-icons" in entry["from"] or not safe_member(member):
        print(f"{ident}: no such entry, its mark is the one of Simple Icons, or the member is not safe", file=sys.stderr)
        return 1
    try:
        with zipfile.ZipFile(archive) as package:
            clean_svg(package.read(member))
    except (OSError, KeyError, ValueError, zipfile.BadZipFile) as error:
        print(f"{ident}: {member}: {error}", file=sys.stderr)
        return 1
    source = {"url": url, "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(), "member": member, "terms": terms}
    return sync_additions([{"id": ident, "mark_source": source, "by": "official"}], registry, additions)


def set_marks(registry: Path, additions: Path, cache: Path) -> int:
    """Give every entry of the registry its mark (see `apply_marks`) and write the registry and the files."""
    cache.mkdir(parents=True, exist_ok=True)
    reg_doc = json.loads(registry.read_text(encoding="utf-8"))
    entries = {e["id"]: {("mark" if k == "icon" else k): (None if k == "icon" else v) for k, v in e.items()}
               for e in reg_doc["entries"]}
    records = json.loads(additions.read_text(encoding="utf-8"))["entries"] if additions.is_file() else []
    root = _tarball(*SIMPLE_ICONS, cache)
    refused = apply_marks(entries, simple_icons(cache), lambda slug: (root / "icons" / f"{slug}.svg").read_bytes(),
                          registry.parent, {r["id"]: r for r in records if r.get("mark") or r.get("mark_source")})
    reg_doc["entries"] = [entries[k] for k in sorted(entries)]
    problems = check(reg_doc, registry.parent)
    print("\n".join(refused + problems), file=sys.stderr)
    if problems:
        return 1
    _write(registry, reg_doc)
    marked = [e for e in reg_doc["entries"] if e["mark"] or e.get("mark_source")]
    print(json.dumps({"entries with a mark file": sum(1 for e in marked if e["mark"]),
                      "entries with a package": sum(1 for e in marked if e.get("mark_source")),
                      "services with a rule and either": sum(1 for e in marked if e["kind"] == "service" and "stack-analyser" in e["from"])}))
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    sub = parser.add_subparsers(dest="command", required=True)
    build_parser = sub.add_parser("build")
    build_parser.add_argument("--out", type=Path, required=True)
    build_parser.add_argument("--cache", type=Path, default=Path.home() / ".cache/daodan/registry-build")
    build_parser.add_argument("--additions", type=Path, default=DATA / "registry-additions.json")
    check_parser = sub.add_parser("check")
    check_parser.add_argument("file", type=Path)
    check_parser.add_argument("--additions", type=Path, default=DATA / "registry-additions.json")
    package_parser = sub.add_parser("add-package-mark")
    package_parser.add_argument("id")
    package_parser.add_argument("archive", type=Path, help="a copy of the owner's package, downloaded into a folder of its own")
    package_parser.add_argument("--url", required=True, help="where the package is, at a fixed version")
    package_parser.add_argument("--member", required=True, help="the SVG inside the package")
    package_parser.add_argument("--terms", required=True, help="the owner's page of terms for the mark")
    package_parser.add_argument("--registry", type=Path, default=DATA / "service-registry.json")
    package_parser.add_argument("--additions", type=Path, default=DATA / "registry-additions.json")
    marks_parser = sub.add_parser("marks")
    marks_parser.add_argument("--registry", type=Path, default=DATA / "service-registry.json")
    marks_parser.add_argument("--additions", type=Path, default=DATA / "registry-additions.json")
    marks_parser.add_argument("--cache", type=Path, default=Path.home() / ".cache/daodan/registry-build")
    mark_parser = sub.add_parser("add-mark")
    mark_parser.add_argument("id")
    mark_parser.add_argument("file", type=Path, help="the owner's SVG, downloaded into a folder of its own")
    origin = mark_parser.add_mutually_exclusive_group(required=True)
    origin.add_argument("--url", help="where the owner's file came from")
    origin.add_argument("--own", action="store_true", help="the file is a drawing of Daodan's")
    mark_parser.add_argument("--terms", help="the owner's page of terms for the mark, when there is one")
    mark_parser.add_argument("--registry", type=Path, default=DATA / "service-registry.json")
    mark_parser.add_argument("--additions", type=Path, default=DATA / "registry-additions.json")
    sync_parser = sub.add_parser("sync-additions")
    sync_parser.add_argument("source", type=Path)
    sync_parser.add_argument("--registry", type=Path, default=DATA / "service-registry.json")
    sync_parser.add_argument("--additions", type=Path, default=DATA / "registry-additions.json")
    args = parser.parse_args(argv)
    if args.command == "sync-additions":
        return sync_additions(json.loads(args.source.read_text(encoding="utf-8")), args.registry, args.additions)
    if args.command == "add-mark":
        return add_mark(args.id, args.file, args.url, args.terms, args.registry, args.additions, args.own)
    if args.command == "add-package-mark":
        return add_package_mark(args.id, args.url, args.archive, args.member, args.terms, args.registry, args.additions)
    if args.command == "marks":
        return set_marks(args.registry, args.additions, args.cache)
    if args.command == "build":
        args.cache.mkdir(parents=True, exist_ok=True)
        try:
            value = build(args.cache, args.additions, args.out.parent)
        except Gap as gap:
            print(f"{gap}: {gap.remedy}", file=sys.stderr)
            return 1
        args.out.write_text(json.dumps(value, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"{len(value['entries'])} entries -> {args.out}")
        return 0
    additions = json.loads(args.additions.read_text(encoding="utf-8"))["entries"] if args.additions.is_file() else []
    problems = check(json.loads(args.file.read_text(encoding="utf-8")), args.file.parent, additions)
    print("\n".join(problems) or "ok")
    return 1 if problems else 0


if __name__ == "__main__":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    raise SystemExit(main())
