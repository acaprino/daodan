#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# ///
"""Build the registry of external services and projects from public catalogs. A development tool.

Sources, at fixed versions: the rules of stack-analyser (MIT), evaluated in Node with
`register` replaced by a collector; the marks of Simple Icons (CC0), joined by name and written, clean, as one SVG
per entry in `data/marks/ID.svg` (the entry's `mark`), and the official marks of the services Simple Icons lacks
(`add-mark`: the owner's file, its URL, the day and its terms, or with `--own` a drawing of Daodan's, kept in the
additions and in REGISTRY-NOTICES.md);
the entries of the CNCF Landscape (CC BY 4.0) with name, category and site; and
`registry-additions.json`, what the catalogs lack and the machine verified.

    python registry_build.py build --out FILE [--cache DIR]
    python registry_build.py check FILE        # also the marks beside FILE: each file named, clean, none left over
    python registry_build.py marks [--registry FILE] [--additions FILE] [--cache DIR]
    python registry_build.py add-mark ID SVG (--url URL [--terms URL] | --own)
    python registry_build.py add-package-mark ID ZIP --url URL --member PATH --terms URL
    python registry_build.py derive [--registry FILE] [--additions FILE]
    python registry_build.py verify-additions [--additions FILE]
    python registry_build.py model-input [--icons] > PROMPT; claude -p ... < PROMPT > ANSWER
    python registry_build.py accept ANSWER

`derive` looks for the packages a catalog lists only for npm on PyPI, crates.io and
the Go proxy, under the same name or the name without a scope, prefix or suffix, and
keeps one only when its repository has the owner of the npm package's repository.
What is left a cheap model proposes in one run; `accept` keeps a proposal only when
the same owner check holds, the package exists and the site answers.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import io
import json
import os
import re
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import flows  # noqa: E402
from mark_svg import clean_svg, safe_member  # noqa: E402

SCHEMA = "daodan/service-registry/v1"
ADDITIONS_SCHEMA = "daodan/registry-additions/v1"
DATA = SCRIPT_DIR.parent / "data"
SOURCES = ("stack-analyser", "simple-icons", "cncf-landscape", "additions")
KINDS = ("service", "project")
CATEGORIES = ("framework", "library", "tool", "service")
SIGNS = ("packages", "patterns", "env", "hosts", "files")
MIN_ENTRIES = 1000
MARKS = "marks"  # the folder of the marks, beside the registry: one SVG per entry, named by the entry's id
MARK_PATH = re.compile(rf"{MARKS}/[a-z0-9][a-z0-9._-]*\.svg")
STACK_ANALYSER = ("@specfy/stack-analyser", "1.27.6")
SIMPLE_ICONS = ("simple-icons", "16.37.0")
CNCF_COMMIT = "75b47639d132b3a7afa31ecc84a90f61b8072dd6"
AGENT = "daodan-registry-build"
# stack-analyser dependency types, as registry ecosystems.
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
_PREFIXES = ("node-", "js-")
_SUFFIXES = ("-node", "-js", ".js", "js", "-sdk", "-client", "-api")


# ---------------------------------------------------------------- check

def check(value: object, data: Path | None = None) -> list[str]:
    """What breaks the registry's rules, one line each; empty when it holds.

    With `data`, the folder that holds the registry, the marks it names must be there, clean, and no other."""
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
        signs = entry.get("signs")
        if signs is not None and (not isinstance(signs, dict) or set(signs) != set(SIGNS)
                                  or not any(signs.values())):
            problems.append(f"{ident}: signs are null or have at least one of {', '.join(SIGNS)}")
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


# ---------------------------------------------------------------- names and owners

def candidates(package: str) -> list[str]:
    """Names an npm package may have in another ecosystem: as is, without its scope, prefix or suffix."""
    if package.startswith("@") and "/" in package:
        scope, name = package[1:].split("/", 1)
        return list(dict.fromkeys([f"{scope}-{name}", scope]))
    out = [package]
    for prefix in _PREFIXES:
        if package.startswith(prefix):
            out.append(package[len(prefix):])
    for suffix in _SUFFIXES:
        if package.endswith(suffix) and len(package) > len(suffix):
            out.append(package[: -len(suffix)])
    return list(dict.fromkeys(name.rstrip("-.") for name in out if name.rstrip("-.")))


def owner(url: object) -> str | None:
    """`host/owner` of a repository URL on a code host, lower case; None for anything else."""
    if not isinstance(url, str):
        return None
    text = url.strip().removeprefix("git+")
    text = re.sub(r"^git@([^:]+):", r"https://\1/", text)
    text = re.sub(r"^(github|gitlab|bitbucket):", lambda m: f"https://{m.group(1)}.{'org' if m.group(1) == 'bitbucket' else 'com'}/", text)
    if re.fullmatch(r"[\w.-]+/[\w.-]+", text):
        text = "https://github.com/" + text
    match = re.match(r"^[a-z+]+://(?:[^@/]+@)?(github\.com|gitlab\.com|bitbucket\.org)/([^/#?]+)/[^/#?]+", text, re.I)
    return f"{match.group(1).lower()}/{match.group(2).lower()}" if match else None


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


def _json(url: str):
    data = _get(url)
    try:
        return json.loads(data) if data else None
    except ValueError:
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

_COLLECT = r"""
const fs = require('fs'), path = require('path');
const root = process.argv[2], rules = [];
const plain = v => v instanceof RegExp ? {regex: v.source} : v;
function walk(dir) {
  for (const name of fs.readdirSync(dir).sort()) {
    const file = path.join(dir, name);
    if (fs.statSync(file).isDirectory()) { walk(file); continue; }
    if (!name.endsWith('.js')) continue;
    let text = fs.readFileSync(file, 'utf8');
    if (!/^register\(/m.test(text)) continue;
    // Every other import is a detection function the registry does not need: a no-op stands in.
    const names = [];
    for (const line of text.match(/^import .*$/gm) || []) {
      const named = line.match(/\{([^}]*)\}/), single = line.match(/^import (?:\* as )?([A-Za-z_$][\w$]*)/);
      if (named) names.push(...named[1].split(',').map(n => n.trim().split(/\s+as\s+/).pop()).filter(Boolean));
      else if (single) names.push(single[1]);
      text = text.replace(line, '');
    }
    text = text.replace(/^export (default )?/gm, '');
    const others = [...new Set(names)].filter(n => n !== 'register');
    new Function(...others, 'register', text)(...others.map(() => () => undefined), rule => rules.push(rule));
  }
}
walk(path.join(root, 'dist', 'rules'));
process.stdout.write(JSON.stringify(rules, (k, v) => plain(v)));
"""


def stack_analyser_rules(cache: Path) -> list[dict]:
    root = _tarball(*STACK_ANALYSER, cache)
    with tempfile.TemporaryDirectory() as work:
        script = Path(work) / "collect.cjs"
        script.write_text(_COLLECT, encoding="utf-8")
        done = subprocess.run(["node", str(script), str(root)], capture_output=True, text=True, timeout=120, cwd=work)
    if done.returncode != 0:
        raise RuntimeError(f"stack-analyser rules: {done.stderr.strip()[:500]}")
    return json.loads(done.stdout)


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

def _empty_signs() -> dict:
    return {name: ({} if name in ("packages", "patterns") else []) for name in SIGNS}


def _add_signs(signs: dict, more: dict) -> None:
    for name, value in more.items():
        if name in ("packages", "patterns"):
            for ecosystem, names in value.items():
                signs[name][ecosystem] = sorted(set(signs[name].get(ecosystem, [])) | set(names))
        else:
            signs[name] = sorted(set(signs[name]) | set(value))


def _drop_signs(signs: dict, wrong: dict) -> None:
    for name, value in wrong.items():
        if name in ("packages", "patterns"):
            for ecosystem, names in value.items():
                kept = [n for n in signs[name].get(ecosystem, []) if n not in names]
                if kept:
                    signs[name][ecosystem] = kept
                else:
                    signs[name].pop(ecosystem, None)
        else:
            signs[name] = [n for n in signs[name] if n not in value]


def _from_rule(rule: dict) -> dict:
    signs = _empty_signs()
    for dependency in rule.get("dependencies", []):
        ecosystem = ECOSYSTEMS.get(dependency["type"], dependency["type"])
        name = dependency["name"]
        if isinstance(name, dict):
            signs["patterns"].setdefault(ecosystem, []).append(name["regex"])
        else:
            signs["packages"].setdefault(ecosystem, []).append(name)
    signs["env"] = list(rule.get("dotenv", []))
    signs["files"] = [f for f in rule.get("files", []) if isinstance(f, str)]
    _add_signs(signs, {})
    kind = "service" if rule["type"] in SERVICES or rule["type"] in SERVICE_TYPES else "project"
    node_type = SERVICE_TYPES.get(rule["type"], "servizio o API" if kind == "service" else "altro")
    return {"id": rule["tech"], "name": rule["name"], "kind": kind, "type": node_type, "site": None, "mark": None,
            "signs": signs, "from": ["stack-analyser"]}


def apply_additions(entries: dict[str, dict], records: list[dict]) -> None:
    """Merge curated/verified `additions` records into `entries` in place; a record's `wrong_signs` take away the
    signs a catalog gives the entry wrongly."""
    for record in records:
        entry = entries.get(record["id"])
        if entry is None:
            entry = entries[record["id"]] = {"id": record["id"], "name": record["name"], "kind": record["kind"],
                                             "type": record["type"], "site": None, "mark": None,
                                             "signs": _empty_signs(), "from": []}
        elif entry["signs"] is None:
            entry["signs"] = _empty_signs()
        for name in ("name", "kind", "type", "site", "category", "mark", "mark_source"):
            if record.get(name):
                entry[name] = record[name]
        if record.get("mark"):
            entry.pop("mark_source", None)  # a file and a package are two cases: the record's file stays
        _add_signs(entry["signs"], record.get("signs", {}))
        _drop_signs(entry["signs"], record.get("wrong_signs", {}))
        entry["from"] = sorted(set(entry["from"]) | {"additions"})
        if not any(entry["signs"].values()):
            entry["signs"] = None


def build(cache: Path, additions: Path, data: Path) -> dict:
    entries, by_name = {}, {}
    for rule in stack_analyser_rules(cache):
        entry = _from_rule(rule)
        entries[entry["id"]] = entry
        by_name.setdefault(_norm(entry["name"]), entry["id"])
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
                          "site": item.get("homepage_url"), "mark": None, "signs": _empty_signs(),
                          "from": ["cncf-landscape"]}
        by_name[_norm(item["name"])] = ident
    apply_additions(entries, json.loads(additions.read_text(encoding="utf-8"))["entries"] if additions.is_file() else [])
    root = _tarball(*SIMPLE_ICONS, cache)
    records = json.loads(additions.read_text(encoding="utf-8"))["entries"] if additions.is_file() else []
    refused = apply_marks(entries, simple_icons(cache), lambda slug: (root / "icons" / f"{slug}.svg").read_bytes(), data,
                          {r["id"]: r for r in records if r.get("mark") or r.get("mark_source")})
    if refused:
        print("\n".join(refused), file=sys.stderr)
    for entry in entries.values():
        if not any(entry["signs"].values()):
            entry["signs"] = None
    return {"schema": SCHEMA, "versions": {"stack-analyser": STACK_ANALYSER[1], "simple-icons": SIMPLE_ICONS[1],
                                           "cncf-landscape": CNCF_COMMIT},
            "entries": [entries[i] for i in sorted(entries)]}


# ---------------------------------------------------------------- derive and verify

def _npm_owner(package: str) -> str | None:
    data = _json(f"https://registry.npmjs.org/{urllib.parse.quote(package, safe='@')}/latest")
    repository = (data or {}).get("repository")
    return owner(repository.get("url") if isinstance(repository, dict) else repository)


def _pypi_owners(name: str) -> set[str] | None:
    data = _json(f"https://pypi.org/pypi/{urllib.parse.quote(name)}/json")
    if data is None:
        return None
    info = data.get("info") or {}
    urls = [info.get("home_page"), info.get("project_url"), *(info.get("project_urls") or {}).values()]
    return {o for o in map(owner, urls) if o}


_crates_clock = [0.0]


def _crates_owners(name: str) -> set[str] | None:
    wait = 1.0 - (time.monotonic() - _crates_clock[0])  # crates.io asks for one request a second
    if wait > 0:
        time.sleep(wait)
    _crates_clock[0] = time.monotonic()
    data = _json(f"https://crates.io/api/v1/crates/{urllib.parse.quote(name)}")
    if data is None:
        return None
    crate = data.get("crate") or {}
    return {o for o in map(owner, [crate.get("repository"), crate.get("homepage")]) if o}


def real_go_mod(text: bytes) -> bool:
    """A go.mod the module wrote: the proxy makes up a bare `module` line for any repository."""
    return any(line.startswith(b"go ") for line in text.splitlines())


def _go_module(module: str) -> bool:
    escaped = re.sub(r"[A-Z]", lambda m: "!" + m.group(0).lower(), module)
    latest = _json(f"https://proxy.golang.org/{escaped}/@latest")
    version = (latest or {}).get("Version")
    mod = _get(f"https://proxy.golang.org/{escaped}/@v/{version}.mod") if version else None
    return bool(mod) and real_go_mod(mod)


def own_npm(packages: dict) -> list[str]:
    """An entry's npm packages without type stubs and OpenTelemetry instrumentations, which belong to those projects."""
    return [p for p in packages.get("npm", []) if not p.startswith(("@types/", "@opentelemetry/"))]


def answers(url: str) -> bool:
    """A site answers when its server replies with anything but not found or a server error; 403 to robots counts."""
    request = urllib.request.Request(url, headers={"User-Agent": AGENT})
    try:
        with urllib.request.urlopen(request, timeout=30):
            return True
    except urllib.error.HTTPError as error:
        return error.code not in (404, 410) and error.code < 500
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        return False


def catalog_packages(entry: dict, derived: list[dict]) -> dict:
    """An entry's packages without the ones an earlier `derive` added: each run starts from the catalogs."""
    added = {}
    for record in derived:
        if record["id"] == entry["id"]:
            for ecosystem, names in record["signs"]["packages"].items():
                added.setdefault(ecosystem, set()).update(names)
    packages = {e: [n for n in names if n not in added.get(e, set())]
                for e, names in ((entry.get("signs") or {}).get("packages") or {}).items()}
    return {e: names for e, names in packages.items() if names}


def _derive_entry(entry: dict, packages: dict) -> dict | None:
    """Packages of the other ecosystems for an entry known only on npm, by the owner of the repository."""
    npm = own_npm(packages)[:3]
    found, main = {}, None
    for number, package in enumerate(npm):
        home = _npm_owner(package)
        main = home if number == 0 else main
        if home is None or home != main:  # the first package names the owner; another owner is another project
            continue
        names = candidates(package)
        if "pypi" not in packages and "pypi" not in found:
            hit = next((n for n in names if home in (_pypi_owners(n) or set())), None)
            if hit:
                found["pypi"] = [hit]
        if "crates" not in packages and "crates" not in found:
            hit = next((n for n in names if home in (_crates_owners(n) or set())), None)
            if hit:
                found["crates"] = [hit]
        if "go" not in packages and "go" not in found and home.startswith("github.com/"):
            base = names[0].replace("@", "").replace("/", "-")
            hit = next((m for n in dict.fromkeys([base, *names]) for m in
                        (f"{home}/{n}", f"{home}/{n}-go", f"{home}/go-{n}") if _go_module(m)), None)
            if hit:
                found["go"] = [hit]
        if found:
            return {"id": entry["id"], "signs": {"packages": found}, "by": "derive", "owner": home}
    return None


def unambiguous(found: list[dict]) -> list[dict]:
    """Derived records without the packages found for more than one entry: an umbrella names none of them."""
    count = {}
    for record in found:
        for ecosystem, names in record["signs"]["packages"].items():
            for name in names:
                count[(ecosystem, name)] = count.get((ecosystem, name), 0) + 1
    out = []
    for record in found:
        packages = {e: [n for n in names if count[(e, n)] == 1] for e, names in record["signs"]["packages"].items()}
        packages = {e: names for e, names in packages.items() if names}
        if packages:
            out.append({**record, "signs": {**record["signs"], "packages": packages}})
    return out


def derive(registry: Path, additions: Path, workers: int = 8) -> dict:
    value = json.loads(registry.read_text(encoding="utf-8"))
    records = json.loads(additions.read_text(encoding="utf-8"))["entries"] if additions.is_file() else []
    kept = [r for r in records if r.get("by") != "derive"]
    last = [r for r in records if r.get("by") == "derive"]
    wanted = [(e, catalog_packages(e, last)) for e in value["entries"]]
    wanted = [(e, packages) for e, packages in wanted if packages.get("npm")]
    with concurrent.futures.ThreadPoolExecutor(workers) as pool:
        derived = unambiguous([r for r in pool.map(lambda pair: _derive_entry(*pair), wanted) if r])
    out = {"schema": ADDITIONS_SCHEMA, "entries": sorted(kept + derived, key=lambda r: (r["id"], r.get("by", "")))}
    additions.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return {"looked": len(wanted), "derived": len(derived)}


_EXISTS = {"npm": lambda n: _get(f"https://registry.npmjs.org/{urllib.parse.quote(n, safe='@')}/latest") is not None,
           "pypi": lambda n: _pypi_owners(n) is not None, "crates": lambda n: _crates_owners(n) is not None,
           "go": _go_module}


def verify_additions(additions: Path) -> list[str]:
    """What in the additions does not hold: a package its registry does not have, a site that does not answer."""
    problems = []
    for record in json.loads(additions.read_text(encoding="utf-8"))["entries"]:
        for ecosystem, names in record.get("signs", {}).get("packages", {}).items():
            for name in names:
                if ecosystem in _EXISTS and not _EXISTS[ecosystem](name):
                    problems.append(f"{record['id']}: {ecosystem} has no package {name}")
        if record.get("site") and not answers(record["site"]):
            problems.append(f"{record['id']}: {record['site']} does not answer")
    return problems


# ---------------------------------------------------------------- model proposals

MODEL_PROMPT = """Each line below is an entry of a registry of external services and projects: id, name, kind,
npm packages. For each, give only what you know with confidence: the package of the same product on pypi
and crates, the Go module path, and its official site. Leave out what you are not sure of.
Then add up to 100 widely used services and projects that have no line here and are not only on npm
(frameworks, SDKs, databases, clouds), each with id (lowercase), name, kind (service or project),
type (one of: {types}), site and packages.
Answer with JSON only, no prose: {{"entries": [{{"id": "...", "name": "...", "kind": "...", "type": "...",
"site": "https://...", "packages": {{"pypi": ["..."], "crates": ["..."], "go": ["..."], "npm": ["..."]}}}}]}};
for a line of the list, id and the fields you add are enough.

{lines}
"""


ICONS_PROMPT = """Below are names of brands that have a mark (a logo) and no entry in a registry of external services.
Choose the ones that are external services a software project calls or uses through a package: hosted APIs, SaaS,
databases, clouds, authentication, payments, messaging, monitoring, AI. Leave out companies and products that have
no developer service, end-user apps, and libraries or frameworks that are not a service.
For each one chosen give: id (lowercase), name exactly as listed, kind "service", type (one of: {types}), site
(the official one) and packages: the official SDK or client package on npm, pypi, crates or go (a Go module path),
only the ones you know with confidence; an entry without a package is not wanted.
Answer with JSON only, no prose: {{"entries": [{{"id": "...", "name": "...", "kind": "service", "type": "...",
"site": "https://...", "packages": {{"npm": ["..."], "pypi": ["..."], "crates": ["..."], "go": ["..."]}}}}]}}

{lines}
"""


def model_input(registry: dict, icons: list[dict] | None = None) -> str:
    """The prompt: entries known only on npm and without a site, or, with `icons`, the marks that have no entry."""
    if icons is not None:
        index = mark_index(icons)
        named = {_norm(e["name"]) for e in registry["entries"]} | {_norm(e["id"]) for e in registry["entries"]}
        used = {i["slug"] for e in registry["entries"] if (i := simple_icon(e, index))}
        lines = [i["title"] for i in icons if i["slug"] not in used and _norm(i["title"]) not in named]
        return ICONS_PROMPT.format(types=", ".join(flows.NODE_TYPES), lines="\n".join(lines))
    lines = []
    for entry in registry["entries"]:
        packages = (entry.get("signs") or {}).get("packages") or {}
        npm_only = packages.get("npm") and not {"pypi", "crates", "go"} & set(packages)
        if npm_only or (not entry["site"] and "stack-analyser" in entry["from"]):
            lines.append("\t".join([entry["id"], entry["name"], entry["kind"], ",".join(packages.get("npm", [])[:2])]))
    return MODEL_PROMPT.format(types=", ".join(flows.NODE_TYPES), lines="\n".join(lines))


def _owners(ecosystem: str, name: str) -> set[str] | None:
    if ecosystem == "npm":
        found = _npm_owner(name)
        return {found} if found else (set() if _EXISTS["npm"](name) else None)
    if ecosystem == "pypi":
        return _pypi_owners(name)
    if ecosystem == "crates":
        return _crates_owners(name)
    if ecosystem == "go":
        return {o for o in [owner("https://" + name)] if o} if _go_module(name) else None
    return None


NETWORK = {"owners": _owners, "site": answers}


def accept(proposals: list[dict], entries: dict[str, dict], check: dict = NETWORK) -> tuple[list[dict], list[str]]:
    """Additions from a model's proposals, kept only where the machine verifies them, and why the rest is not.

    A package of a known entry needs the owner of the entry's first npm package, when it has one;
    a new entry needs a name, a kind, a type, packages that exist and have one owner among them, no package that
    another entry has already, and a site that answers.
    """
    by_name = {_norm(e["name"]): i for i, e in entries.items()}
    kept, refused = [], []
    for proposal in proposals:
        ident = proposal.get("id")
        ident = ident if ident in entries else by_name.get(_norm(proposal.get("name", "")), ident)
        entry = entries.get(ident)
        have = ((entry or {}).get("signs") or {}).get("packages") or {}
        first = next(iter(own_npm(have)), None)
        main = check["owners"]("npm", first) if first else None
        packages = {}
        for ecosystem, names in (proposal.get("packages") or {}).items():
            if ecosystem in have:
                refused.append(f"{ident}: already has {ecosystem}")
                continue
            for name in names:
                found = check["owners"](ecosystem, name)
                if entry is None and main is None and found:  # a new entry: its first package names the owner
                    main = found
                if found is None:
                    refused.append(f"{ident}: {ecosystem} has no package {name}")
                elif main and not main & found:
                    refused.append(f"{ident}: {ecosystem} {name} has another owner than npm {first}")
                else:
                    packages.setdefault(ecosystem, []).append(name)
        site = proposal.get("site") if not (entry or {}).get("site") else None
        if site and not check["site"](site):
            refused.append(f"{ident}: {site} does not answer")
            site = None
        taken = [i for i, e in entries.items() if entry is None and any(
            n in (((e.get("signs") or {}).get("packages") or {}).get(eco) or []) for eco, ns in packages.items() for n in ns)]
        if taken:
            refused.append(f"{ident}: has packages that {', '.join(taken)} already has")
            continue
        if entry is None:
            if (not packages or proposal.get("kind") not in KINDS or proposal.get("type") not in flows.NODE_TYPES
                    or not proposal.get("name") or not site):
                refused.append(f"{ident}: a new entry needs a name, kind, type, a site that answers and a package")
                continue
            kept.append({"id": _slug(ident), "name": proposal["name"], "kind": proposal["kind"],
                         "type": proposal["type"], "site": site, "signs": {"packages": packages}, "by": "model"})
        elif packages or site:
            kept.append({"id": ident, **({"site": site} if site else {}), "signs": {"packages": packages}, "by": "model"})
    return kept, refused


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
    problems = check(reg_doc, registry.parent)
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
                      "services with signs and either": sum(1 for e in marked if e["kind"] == "service" and e["signs"])}))
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
    derive_parser = sub.add_parser("derive")
    derive_parser.add_argument("--registry", type=Path, default=DATA / "service-registry.json")
    derive_parser.add_argument("--additions", type=Path, default=DATA / "registry-additions.json")
    input_parser = sub.add_parser("model-input")
    input_parser.add_argument("--registry", type=Path, default=DATA / "service-registry.json")
    input_parser.add_argument("--icons", action="store_true", help="ask for the services of the marks that have no entry")
    input_parser.add_argument("--cache", type=Path, default=Path.home() / ".cache/daodan/registry-build")
    accept_parser = sub.add_parser("accept")
    accept_parser.add_argument("answer", type=Path, help="the model's JSON answer")
    accept_parser.add_argument("--registry", type=Path, default=DATA / "service-registry.json")
    accept_parser.add_argument("--additions", type=Path, default=DATA / "registry-additions.json")
    verify_parser = sub.add_parser("verify-additions")
    verify_parser.add_argument("--additions", type=Path, default=DATA / "registry-additions.json")
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
        value = build(args.cache, args.additions, args.out.parent)
        args.out.write_text(json.dumps(value, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"{len(value['entries'])} entries -> {args.out}")
        return 0
    if args.command == "model-input":
        args.cache.mkdir(parents=True, exist_ok=True)
        print(model_input(json.loads(args.registry.read_text(encoding="utf-8")), simple_icons(args.cache) if args.icons else None))
        return 0
    if args.command == "accept":
        text = args.answer.read_text(encoding="utf-8")
        answer = json.loads(text[text.index("{"): text.rindex("}") + 1])
        entries = {e["id"]: e for e in json.loads(args.registry.read_text(encoding="utf-8"))["entries"]}
        kept, refused = accept(answer["entries"], entries)
        print(json.dumps({"kept": len(kept), "refused": refused}, ensure_ascii=False, indent=1))
        return sync_additions(kept, args.registry, args.additions)  # the registry takes what the additions now hold
    if args.command == "derive":
        print(json.dumps(derive(args.registry, args.additions)))
        return 0
    problems = (check(json.loads(args.file.read_text(encoding="utf-8")), args.file.parent) if args.command == "check"
                else verify_additions(args.additions))
    print("\n".join(problems) or "ok")
    return 1 if problems else 0


if __name__ == "__main__":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    raise SystemExit(main())
