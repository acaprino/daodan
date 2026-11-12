#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# ///
"""Build the registry of external services and projects from public catalogs. A development tool.

Sources, at fixed versions: the rules of stack-analyser (MIT), evaluated in Node with
`register` replaced by a collector; the marks of Simple Icons (CC0), joined by name;
the entries of the CNCF Landscape (CC BY 4.0) with name, category and site; and
`registry-additions.json`, what the catalogs lack and the machine verified.

    python registry_build.py build --out FILE [--cache DIR]
    python registry_build.py check FILE
    python registry_build.py derive [--registry FILE] [--additions FILE]
    python registry_build.py verify-additions [--additions FILE]
    python registry_build.py model-input > PROMPT; claude -p ... < PROMPT > ANSWER
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
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import flows  # noqa: E402

SCHEMA = "daodan/service-registry/v1"
ADDITIONS_SCHEMA = "daodan/registry-additions/v1"
DATA = SCRIPT_DIR.parent / "data"
SOURCES = ("stack-analyser", "simple-icons", "cncf-landscape", "additions")
KINDS = ("service", "project")
SIGNS = ("packages", "patterns", "env", "hosts", "files")
MIN_ENTRIES = 1000
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

def check(value: object) -> list[str]:
    """What breaks the registry's rules, one line each; empty when it holds."""
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
        if entry.get("type") not in flows.NODE_TYPES:
            problems.append(f"{ident}: type is one of {', '.join(flows.NODE_TYPES)}")
        signs = entry.get("signs")
        if signs is not None and (not isinstance(signs, dict) or set(signs) != set(SIGNS)
                                  or not any(signs.values())):
            problems.append(f"{ident}: signs are null or have at least one of {', '.join(SIGNS)}")
        if not entry.get("from") or not set(entry["from"]) <= set(SOURCES):
            problems.append(f"{ident}: from names one or more of {', '.join(SOURCES)}")
    return problems


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
    return {"id": rule["tech"], "name": rule["name"], "kind": kind, "type": node_type, "site": None, "icon": None,
            "signs": signs, "from": ["stack-analyser"]}


def build(cache: Path, additions: Path) -> dict:
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
                          "site": item.get("homepage_url"), "icon": None, "signs": _empty_signs(),
                          "from": ["cncf-landscape"]}
        by_name[_norm(item["name"])] = ident
    for record in json.loads(additions.read_text(encoding="utf-8"))["entries"] if additions.is_file() else []:
        entry = entries.get(record["id"])
        if entry is None:
            entry = entries[record["id"]] = {"id": record["id"], "name": record["name"], "kind": record["kind"],
                                             "type": record["type"], "site": None, "icon": None,
                                             "signs": _empty_signs(), "from": []}
        for name in ("name", "kind", "type", "site"):
            entry[name] = record.get(name) or entry[name]
        _add_signs(entry["signs"], record.get("signs", {}))
        entry["from"] = sorted(set(entry["from"]) | {"additions"})
    icons = {}
    for icon in simple_icons(cache):
        for name in [icon["title"], icon["slug"], *icon.get("aliases", {}).get("aka", [])]:
            icons.setdefault(_norm(name), icon["slug"])
    for entry in entries.values():
        entry["icon"] = icons.get(_norm(entry["name"])) or icons.get(_norm(entry["id"]))
        if entry["icon"]:
            entry["from"] = sorted(set(entry["from"]) | {"simple-icons"})
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


def model_input(registry: dict) -> str:
    """The prompt: entries known only on npm, and entries of stack-analyser without a site."""
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
    a new entry needs a name, a kind, a type, packages that exist and a site that answers.
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
    accept_parser = sub.add_parser("accept")
    accept_parser.add_argument("answer", type=Path, help="the model's JSON answer")
    accept_parser.add_argument("--registry", type=Path, default=DATA / "service-registry.json")
    accept_parser.add_argument("--additions", type=Path, default=DATA / "registry-additions.json")
    verify_parser = sub.add_parser("verify-additions")
    verify_parser.add_argument("--additions", type=Path, default=DATA / "registry-additions.json")
    args = parser.parse_args(argv)
    if args.command == "build":
        args.cache.mkdir(parents=True, exist_ok=True)
        value = build(args.cache, args.additions)
        args.out.write_text(json.dumps(value, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"{len(value['entries'])} entries -> {args.out}")
        return 0
    if args.command == "model-input":
        print(model_input(json.loads(args.registry.read_text(encoding="utf-8"))))
        return 0
    if args.command == "accept":
        text = args.answer.read_text(encoding="utf-8")
        answer = json.loads(text[text.index("{"): text.rindex("}") + 1])
        entries = {e["id"]: e for e in json.loads(args.registry.read_text(encoding="utf-8"))["entries"]}
        kept, refused = accept(answer["entries"], entries)
        records = json.loads(args.additions.read_text(encoding="utf-8"))["entries"] if args.additions.is_file() else []
        records = [r for r in records if r.get("by") != "model"] + kept
        args.additions.write_text(json.dumps({"schema": ADDITIONS_SCHEMA, "entries": sorted(
            records, key=lambda r: (r["id"], r.get("by", "")))}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(json.dumps({"kept": len(kept), "refused": refused}, ensure_ascii=False, indent=1))
        return 0
    if args.command == "derive":
        print(json.dumps(derive(args.registry, args.additions)))
        return 0
    problems = (check(json.loads(args.file.read_text(encoding="utf-8"))) if args.command == "check"
                else verify_additions(args.additions))
    print("\n".join(problems) or "ok")
    return 1 if problems else 0


if __name__ == "__main__":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    raise SystemExit(main())
