#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# ///
"""System brief: what the analysis steps already produced, composed without a model for who proposes the map.

Modules and directories with their file counts, entry points, stores and routes, the
external services recognized and by which source, the files that configure running
and release and what they declare, links counted by origin, and one candidate group
per resource two or more entry points touch. Groups overlap and never merge, so no
threshold is needed; an entry point that shares nothing is listed alone.
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict, deque
from pathlib import Path, PurePosixPath

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import flows  # noqa: E402
import modules  # noqa: E402
import service_registry  # noqa: E402
import stack_analyser  # noqa: E402
import system_map  # noqa: E402
from snapshot_store import open_snapshot  # noqa: E402

SCHEMA = "daodan/system-brief/v1"
CAP = 24_000        # characters, a parameter of the benchmark
HOLDERS = 8         # past this many, a group's entry points are summed up by directory
HOSTING = {"vercel.json", "netlify.toml", "fly.toml", "render.yaml", "app.yaml", "app.json", "firebase.json",
           "railway.json", "railway.toml", "serverless.yml", "serverless.yaml", "wrangler.toml", "catalog-info.yaml"}
CI = {".gitlab-ci.yml", "azure-pipelines.yml", "azure-pipelines.yaml", "bitbucket-pipelines.yml", ".travis.yml",
      "cloudbuild.yaml", "cloudbuild.yml", "appveyor.yml", "buildspec.yml", "Jenkinsfile"}
_KEY = re.compile(r"^(\s*)([\w.-]+):\s*(.*?)\s*$")


def _compose(name: str) -> bool:
    return name.startswith(("docker-compose", "compose")) and name.endswith((".yml", ".yaml"))


def _runtime(rel: str, lines: list[str]) -> bool:
    name = PurePosixPath(rel).name
    if name == "Dockerfile" or name.endswith(".Dockerfile") or _compose(name) or name.endswith(".tf"):
        return True
    if name in HOSTING or name in CI or rel.startswith(".github/workflows/"):
        return True
    return name.endswith((".yml", ".yaml")) and any(line.startswith("apiVersion:") for line in lines) \
        and any(line.startswith("kind:") for line in lines)


def _declared(rel: str, lines: list[str]) -> list[dict]:
    """What a runtime file declares, read without tools: compose services, base images, Backstage entities."""
    name, out = PurePosixPath(rel).name, []
    if name == "Dockerfile" or name.endswith(".Dockerfile"):
        stages = set()
        for number, line in enumerate(lines, 1):
            match = re.match(r"^\s*FROM\s+(?:--\S+\s+)*(\S+)(?:\s+AS\s+(\S+))?", line, re.I)
            if match and match.group(1).lower() not in stages:
                out.append({"kind": "base image", "name": service_registry._image(match.group(1)), "file": rel,
                            "line": number})
            if match and match.group(2):
                stages.add(match.group(2).lower())
    elif _compose(name):
        inside, indent, current = False, None, None
        for number, line in enumerate(lines, 1):
            match = _KEY.match(line)
            if not match or line.lstrip().startswith("#"):
                continue
            depth, key, value = len(match.group(1)), match.group(2), match.group(3)
            if depth == 0:
                inside = key == "services"
                continue
            if inside and (indent is None or depth == indent):
                indent = depth
                current = {"kind": "service", "name": key, "image": None, "file": rel, "line": number}
                out.append(current)
            elif inside and current and key == "image":
                current["image"] = service_registry._image(value.strip("'\""))
    elif name == "catalog-info.yaml":
        kind = None
        for number, line in enumerate(lines, 1):
            if line.startswith("---"):
                kind = None
            elif line.startswith("kind:"):
                kind = line.split(":", 1)[1].strip()
            elif kind and re.match(r"^\s{2}name:", line):
                out.append({"kind": kind, "name": line.split(":", 1)[1].strip(), "file": rel, "line": number})
                kind = None
    return out


def _groups(links: dict) -> tuple[list[dict], list[str]]:
    """One group per resource touched by two or more entry points, and the entry points that share nothing."""
    calls = defaultdict(set)
    for edge in links["edges"]:
        if edge["type"] in ("chiama", "attiva"):
            calls[edge["from"]].add(edge["to"])
    entries = sorted({e["symbol"] for e in links["entries"]})
    touched = {}
    for entry in entries:
        reached, queue = {entry}, deque([entry])
        while queue:
            for target in calls.get(queue.popleft(), ()):
                if target not in reached:
                    reached.add(target)
                    queue.append(target)
        resources = set()
        for edge in links["edges"]:
            if edge["from"] in reached and edge["to"].startswith(("store:", "module:")):
                resources.add(edge["to"])
            if edge["to"] in reached and edge["from"].startswith("store:"):
                resources.add(edge["from"])
            if edge["from"] in reached and edge.get("route"):
                resources.add("route:" + " ".join(edge["route"]))
        touched[entry] = resources
    holders = defaultdict(list)
    for entry, resources in touched.items():
        for resource in resources:
            holders[resource].append(entry)
    groups = [{"resource": r, "entries": sorted(e),
               "by_directory": dict(sorted(Counter(PurePosixPath(s.split("::")[0]).parent.as_posix() for s in e).items()))}
              for r, e in holders.items() if len(e) >= 2]
    groups.sort(key=lambda g: (-len(g["entries"]), g["resource"]))
    shared = {g["resource"] for g in groups}
    return groups, [e for e in entries if not touched[e] & shared]


def _externals(manifest: Path, graph: dict, files: list[str], root: Path, registry: dict,
               recognized: list[dict]) -> tuple[list[dict], dict]:
    by_id = {e["id"]: e for e in registry["entries"]}
    out = {}
    for found in recognized:
        out[found["id"]] = {"id": found["id"], "name": found["name"], "kind": found["kind"], "type": found["type"],
                            "from": ["registry"], "paths": sorted({s["path"] for s in found["signs"] if s["path"]})}
    from embedding_worker import shared_cache_dir
    stack = stack_analyser.run(root, shared_cache_dir() / "stack-analyser", set(files))
    for found in stack.get("found", []):
        entry = out.get(found["tech"])
        if entry is None:
            known = by_id.get(found["tech"], {})
            entry = out[found["tech"]] = {"id": found["tech"], "name": known.get("name", found["tech"]),
                                          "kind": known.get("kind"), "type": known.get("type", "altro"),
                                          "from": [], "paths": []}
        entry["from"] = sorted(set(entry["from"]) | {"stack-analyser"})
        entry["paths"] = sorted(set(entry["paths"]) | set(found["paths"]))
    for module in graph["modules"]:
        if module.get("location") == "external":
            ident = modules.slug(module["name"])
            out.setdefault(ident, {"id": ident, "name": module["name"], "kind": None, "type": "altro", "from": [],
                                   "paths": sorted({str(e.get("path") if isinstance(e, dict) else e).split("#")[0]
                                                    for e in module.get("evidence", [])})})
            out[ident]["from"] = sorted(set(out[ident]["from"]) | {"modules"})
    status = {k: v for k, v in stack.items() if k != "found"}
    return sorted(out.values(), key=lambda e: system_map.key(e["name"])), status


def _text(value: dict, cap: int, holders: int) -> tuple[str, int]:
    steps = ", ".join(f"{k} {'yes' if v else 'no'}" for k, v in value["steps"].items())
    head = [f"# System brief\nSteps: {steps}",
            "Modules: " + "; ".join(f"{m['name']} ({m['kind']}, {m['files']} files)" for m in value["modules"]),
            "Directories: " + "; ".join(f"{d} {n}" for d, n in value["directories"].items()),
            f"Entry points: {value['entries']}; store keys: {value['stores']}; routes: {value['routes']['offered']} "
            f"offered, {value['routes']['called']} called, {value['routes']['linked']} linked; "
            "links: " + ", ".join(f"{k} {n}" for k, n in value["links"].items()),
            "Externals: " + "; ".join(f"{e['name']} [{e['type']}] from {', '.join(e['from'])}: "
                                      f"{', '.join(e['paths'][:3])}" for e in value["externals"]),
            "Other dependencies: " + "; ".join(f"{u} {n}" for u, n in value["other_dependencies"].items()),
            "Runtime files: " + ", ".join(value["runtime_files"]),
            "Declared: " + "; ".join(f"{d['kind']} {d['name']}" + (f" ({d['image']})" if d.get("image") else "")
                                     + f" in {d['file']}" for d in value["declared"]),
            "Alone: " + ", ".join(value["alone"]),
            "Confirmed: " + ", ".join(value["confirmed"]),
            "Cards: " + ", ".join(value["cards"]),
            "Groups (resource, entry points that touch it):"]
    text = "\n".join(line for line in head if not line.endswith(": "))  # an empty section costs tokens
    lines = []
    for group in value["groups"]:
        entries = group["entries"]
        listed = ", ".join(entries) if len(entries) <= holders else \
            "by directory " + ", ".join(f"{d} {n}" for d, n in group["by_directory"].items())
        lines.append(f"- {group['resource']} ({len(entries)}): {listed}")
    kept = len(lines)
    while kept and len(text) + sum(len(line) + 1 for line in lines[:kept]) + _tail(value, kept) > cap:
        kept -= 1
    rest = value["groups"][kept:]
    body = lines[:kept]
    if rest:
        body.append(f"- {len(rest)} more groups, fewest entry points: "
                    + ", ".join(f"{g['resource']} ({len(g['entries'])})" for g in rest))
    out = "\n".join([text, *body])
    return (out if len(out) <= cap else out[: cap - 1] + "…"), len(rest)


def _tail(value: dict, kept: int) -> int:
    rest = value["groups"][kept:]
    return 0 if not rest else 40 + sum(len(g["resource"]) + 8 for g in rest)


def brief(manifest: Path, rules: list[dict], *, cap: int = CAP, holders: int = HOLDERS) -> dict:
    """The system brief of a snapshot under its link rules."""
    manifest = Path(manifest).resolve()
    links = flows.cached_links(manifest, rules)
    graph = modules.load_graph(Path(modules.ensure_graph(manifest)["graph"]))
    with open_snapshot(manifest) as store:
        root = Path(store["root"]) / (store.get("target") or ".")
        files = sorted(dict(store.iter_file_headers_only()))
        source = flows.Source(store)
        texts = {rel: source.lines(rel) or [] for rel in files}
    registry = service_registry.load()
    recognized = service_registry.recognize(manifest, registry)
    externals, stack = _externals(manifest, graph, files, root, registry, recognized)
    known = {s["value"] for e in recognized for s in e["signs"] if s["sign"] == "package"}
    other = {}
    for module in graph["modules"]:
        if module["provenance"] == "build":
            left = [d for d in module["dependencies"] if d not in known]
            if left:
                other[module["name"]] = len(left)
    runtime = [rel for rel in files if _runtime(rel, texts[rel])]
    system = system_map.load(manifest, rules)
    groups, alone = _groups(links)
    cards_file = manifest.with_name("flow-cards.json")
    try:
        cards = sorted({c.get("name", "") for c in json.loads(cards_file.read_text(encoding="utf-8")).get("cards", {}).values()} - {""})
    except (OSError, ValueError, AttributeError):
        cards = []
    value = {"schema": SCHEMA,
             "steps": {"statico": True, "inferenza": bool(rules), "dinamico": False, "semantico": system is not None},
             "modules": [{"name": m["name"], "kind": m["kind"], "provenance": m["provenance"], "files": len(m.get("files", []))}
                         for m in graph["modules"]],
             "directories": dict(sorted(Counter(f.split("/", 1)[0] if "/" in f else "." for f in files).items())),
             "entries": len({e["symbol"] for e in links["entries"]}), "stores": len(links["stores"]),
             "routes": links["routes"], "links": dict(sorted(Counter(e["origin"] for e in links["edges"]).items())),
             "externals": externals, "stack_analyser": stack, "other_dependencies": other, "runtime_files": runtime,
             "declared": [d for rel in runtime for d in _declared(rel, texts[rel])],
             "groups": groups, "alone": alone,
             "confirmed": [n["name"] for n in (system or {}).get("nodes", []) if n["status"] == "confirmed"],
             "cards": cards}
    value["text"], value["truncated"] = _text(value, cap, holders)
    return value
