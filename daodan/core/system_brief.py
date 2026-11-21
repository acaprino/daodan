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

import entries  # noqa: E402
import flows  # noqa: E402
import modules  # noqa: E402
import pipeline  # noqa: E402
import service_registry  # noqa: E402
import technologies  # noqa: E402
import system_map  # noqa: E402
from premap.compose import is_compose_file  # noqa: E402
from snapshot_store import open_snapshot  # noqa: E402

SCHEMA = "daodan/system-brief/v1"
LIMIT = 31_800      # characters of an answer as JSON: on phazly a brief answer of 31.8 KB passed the host's
                    # tool-output limit, on tududi one of 51.9 KB did not; the brief gets what the rest leaves
HOLDERS = 8         # past this many, a group's entry points are summed up by directory
HOSTING = {"vercel.json", "netlify.toml", "fly.toml", "render.yaml", "app.yaml", "app.json", "firebase.json",
           "railway.json", "railway.toml", "serverless.yml", "serverless.yaml", "wrangler.toml", "catalog-info.yaml"}
CI = {".gitlab-ci.yml", "azure-pipelines.yml", "azure-pipelines.yaml", "bitbucket-pipelines.yml", ".travis.yml",
      "cloudbuild.yaml", "cloudbuild.yml", "appveyor.yml", "buildspec.yml", "Jenkinsfile"}

def _runtime(rel: str, lines: list[str]) -> bool:
    name = PurePosixPath(rel).name
    if name == "Dockerfile" or name.endswith(".Dockerfile") or is_compose_file(name) or name.endswith(".tf"):
        return True
    if name in HOSTING or name in CI or rel.startswith(".github/workflows/"):
        return True
    return name.endswith((".yml", ".yaml")) and any(line.startswith("apiVersion:") for line in lines) \
        and any(line.startswith("kind:") for line in lines)


def _declared(rel: str, lines: list[str]) -> list[dict]:
    """What a runtime file declares besides the service declarations already delivered by the stack."""
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


def _externals(graph: dict, record: dict) -> list[dict]:
    """The stack step's technologies and the external modules of the graph, by id."""
    out = {found["id"]: {"id": found["id"], "name": found["name"], "kind": found["kind"],
                         "type": found["type"] or "altro", "from": ["registry"],
                         "paths": sorted({s["path"] for s in found["signs"] if s["strength"] == "declared" and s["path"]})}
           for found in record["technologies"]}
    for module in graph["modules"]:
        if module.get("location") == "external":
            ident = modules.slug(module["name"])
            out.setdefault(ident, {"id": ident, "name": module["name"], "kind": None, "type": "altro", "from": [],
                                   "paths": sorted({str(e.get("path") if isinstance(e, dict) else e).split("#")[0]
                                                    for e in module.get("evidence", [])})})
            out[ident]["from"] = sorted(set(out[ident]["from"]) | {"modules"})
    return sorted(out.values(), key=lambda e: system_map.key(e["name"]))


# Headed sections, not tags: one line per label, the same convention as the map format that follows the brief.
HEADER = "\n".join((
    "# System brief",
    "What the machine found in this snapshot with its analysis steps, without a model.",
    "Sections, in this order: Steps that ran; Counts; Modules (M) and top Directories (D) with their files; "
    "Externals (X), services of others, with `id` when the service registry has it; Other dependencies (O), per "
    "module the ones the registry does not know; Runtime files (R) for running and release, and what they Declare (S); "
    "names the project Confirmed (N); flow Cards (C); AST entry candidates (A); Entry points (E) with kind and "
    "`file:line`, alone when they reach no resource another reaches; Groups (G), a resource two or more entry points "
    "reach, with them. AST candidates are unclassified evidence, separate from entry points and coverage. "
    "Read all candidates with entry_offset=0 and continue at next_offset.",
    "For each proposed flow, name its entry nodes in entries and its effect nodes in effects. "
    "The map checks directed paths between them across the named participants.",
    "One item per line, numbered in its section; a number stays the same for the same snapshot. "
    "A line `- N more` sums up the rest of a section.",
    "What is not here the machine did not find: `entry points 0` means the machine found none, not that the system "
    "has none; a step marked no did not run. An empty section is left out."))


def _sections(value: dict) -> list[tuple[str, list[str]]]:
    """The sections before the entry points, each a label and its lines."""
    routes = value["routes"]
    candidates = value.get("entry_candidates", [])
    return [
        ("Steps", [", ".join(f"{k} {'yes' if v else 'no'}" for k, v in value["steps"].items())]),
        ("Counts", [f"entry points {value['entries']}", f"AST candidates {len(candidates)}", f"store keys {value['stores']}",
                    f"routes {routes['offered']} offered, {routes['called']} called, {routes['linked']} linked",
                    *(["links " + ", ".join(f"{k} {n}" for k, n in value["links"].items())] if value["links"] else [])]),
        ("Modules", [f"M{i} {m['name']} ({m['kind']}, {m['files']} files)" for i, m in enumerate(value["modules"], 1)]),
        ("Directories", [f"D{i} {d} ({n} files)" for i, (d, n) in enumerate(value["directories"].items(), 1)]),
        ("Externals", [f"X{i} {e['name']}{' id ' + e['id'] if 'registry' in e['from'] else ''} [{e['type']}] "
                       f"from {', '.join(e['from'])}: {', '.join(e['paths'][:3])}"
                       for i, e in enumerate(value["externals"], 1)]),
        ("Other dependencies", [f"O{i} {u} {n}" for i, (u, n) in enumerate(value["other_dependencies"].items(), 1)]),
        ("Runtime files", [f"R{i} {rel}" for i, rel in enumerate(value["runtime_files"], 1)]),
        ("Declared", [f"S{i} {d['kind']} {d['name']}" + (f" ({d['image']})" if d.get("image") else "")
                      + f" in {d['file']}:{d['line']}" for i, d in enumerate(value["declared"], 1)]),
        ("Confirmed", [f"N{i} {name}" for i, name in enumerate(value["confirmed"], 1)]),
        ("Cards", [f"C{i} {name}" for i, name in enumerate(value["cards"], 1)]),
        ("AST entry candidates", [f"A{i} [candidate] {row['reader']} {row['shape']} at {row['site']}: {row['symbol']}"
                                  for i, row in enumerate(candidates[:HOLDERS], 1)]
         + ([f"- {len(candidates) - HOLDERS} more; read entry_offset={HOLDERS}"]
            if len(candidates) > HOLDERS else []))]


def _join(sections: list[tuple[str, list[str]]]) -> str:
    return "\n".join([HEADER, *(f"## {label}\n" + "\n".join(lines) for label, lines in sections if lines)])


def _by_directory(symbols) -> str:
    counts = Counter(PurePosixPath(s.split("::")[0]).parent.as_posix() for s in symbols)
    return ", ".join(f"{d} {n}" for d, n in sorted(counts.items()))


def _text(value: dict, cap: int, holders: int) -> tuple[str, int]:
    """The brief packed for a model; past `cap` the groups with fewest entry points are summed up, and with them
    the entry points no remaining line names."""
    number = {e["symbol"]: i for i, e in enumerate(value["entry_points"], 1)}
    alone = set(value["alone"])
    named = [sorted(number[s] for s in g["entries"]) if len(g["entries"]) <= holders else []
             for g in value["groups"]]
    lines = [f"G{i} {g['resource']} ({len(g['entries'])}): "
             + (", ".join(f"E{n}" for n in refs) if refs else "by directory " + _by_directory(g["entries"]))
             for i, (g, refs) in enumerate(zip(value["groups"], named), 1)]
    head = _sections(value)

    def compose(kept: int) -> str:
        shown = {number[s] for s in alone} | {n for refs in named[:kept] for n in refs}
        entries = [f"E{n} {e['symbol']} [{', '.join(e['kinds'])}] at {e['site']}"
                   + (", alone" if e["symbol"] in alone else "")
                   for n, e in enumerate(value["entry_points"], 1) if n in shown]
        hidden = [e["symbol"] for n, e in enumerate(value["entry_points"], 1) if n not in shown]
        if hidden:
            entries.append(f"- {len(hidden)} more entry points, by directory: {_by_directory(hidden)}")
        groups = lines[:kept]
        if kept < len(lines):
            groups.append(f"- {len(lines) - kept} more groups, fewest entry points: "
                          + ", ".join(f"G{i} {g['resource']} ({len(g['entries'])})"
                                      for i, g in enumerate(value["groups"][kept:], kept + 1)))
        return _join([*head, ("Entry points", entries), ("Groups", groups)])

    low, high = 0, len(lines)  # the most groups that fit, by bisection: the text grows with the groups kept
    while low < high:
        middle = (low + high + 1) // 2
        low, high = (middle, high) if len(compose(middle)) <= cap else (low, middle - 1)
    kept, out = low, compose(low)
    return (out if len(out) <= cap else out[: cap - 1] + "…"), len(lines) - kept


def fit(value: dict, answer: dict, limit: int = LIMIT, holders: int = HOLDERS) -> dict:
    """`answer` with the brief in what is left of `limit` after its other keys, whatever their length."""
    def sized(cap: int) -> tuple[dict, int]:
        text, truncated = _text(value, cap, holders)
        out = {**answer, "brief": text, "truncated": truncated}
        return out, len(json.dumps(out)) - limit

    cap = limit - len(json.dumps({**answer, "brief": "", "truncated": 0}))
    out, over = sized(max(cap, 1))
    while over > 0 and cap > 1:  # what JSON adds to the text (escapes) is known once the text is
        cap -= over
        out, over = sized(max(cap, 1))
    return out


def candidate_page(rows: list[dict], run_id: str, offset: int, limit: int) -> dict:
    """A stable page of syntax evidence, within the same response budget as the brief."""
    page = []
    answer = {"status": "ok", "run_id": run_id, "offset": offset, "count": len(rows), "candidates": page,
              "next_offset": None}
    room = LIMIT - len(json.dumps(answer)) - 32
    for row in rows[offset:offset + limit]:
        size = len(json.dumps(row)) + 2
        if size > room:
            if not page:
                page.append({**{k: v[:400] for k, v in row.items()}, "truncated": True})
            break
        page.append(row)
        room -= size
    if offset + len(page) < len(rows):
        answer["next_offset"] = offset + len(page)
    return answer


def brief(manifest: Path, rules: list[dict]) -> dict:
    """The system brief of a snapshot under its link rules."""
    manifest = Path(manifest).resolve()
    links = flows.cached_links(manifest, rules)
    graph = modules.load_graph(Path(modules.ensure_graph(manifest)["graph"]))
    with open_snapshot(manifest) as store:
        files = sorted(dict(store.iter_file_headers_only()))
        source = flows.Source(store)
        # Other paths cannot contain a runtime declaration interpreted by this reader.
        texts = {rel: source.lines(rel) or [] for rel in files
                 if _runtime(rel, []) or rel.endswith((".yml", ".yaml"))}
    record = technologies.ensure(manifest)
    externals = _externals(graph, record)
    known = {s["value"] for e in record["technologies"] for s in e["signs"] if s["sign"] == "package"}
    other = {}
    for module in graph["modules"]:
        if module["provenance"] == "build":
            left = [d for d in module["dependencies"] if d not in known]
            if left:
                other[module["name"]] = len(left)
    runtime = [rel for rel, lines in texts.items() if _runtime(rel, lines)]
    declarations = defaultdict(list)
    for item in record["configured_services"]:
        if item.get("line") and is_compose_file(PurePosixPath(item["path"]).name):
            image = item.get("image") or ""
            declarations[item["path"]].append({"kind": "service", "name": item["name"],
                                               "image": service_registry.declared_image(image) or image or None,
                                               "file": item["path"], "line": item["line"]})
    system = system_map.load(manifest, rules)
    groups, alone = _groups(links)
    cards_file = manifest.with_name("flow-cards.json")
    try:
        cards = sorted({c.get("name", "") for c in json.loads(cards_file.read_text(encoding="utf-8")).get("cards", {}).values()} - {""})
    except (OSError, ValueError, AttributeError):
        cards = []
    found = defaultdict(list)
    for entry in links["entries"]:
        found[entry["symbol"]].append(entry)
    dynamic_evidence = any(edge.get("origin") == "osservato" for edge in links["edges"])
    if not dynamic_evidence and manifest.with_name(pipeline.events.JOURNAL).is_file():
        dynamic_evidence = pipeline.runtime(manifest)["state"] == "observed"
    value = {"schema": SCHEMA,
             "steps": {"statico": True, "inferenza": bool(rules),
                       "dinamico": dynamic_evidence,
                       "semantico": system is not None},
             "modules": [{"name": m["name"], "kind": m["kind"], "provenance": m["provenance"], "files": len(m.get("files", []))}
                         for m in graph["modules"]],
             "directories": dict(sorted(Counter(f.split("/", 1)[0] if "/" in f else "." for f in files).items())),
             "entries": len(found), "stores": len(links["stores"]), "entry_candidates": entries.cached_syntax(manifest),
             "entry_points": [{"symbol": s, "kinds": sorted({e["kind"] for e in found[s]}),
                               "site": min(e["site"] for e in found[s])} for s in sorted(found)],
             "routes": links["routes"], "links": dict(sorted(Counter(e["origin"] for e in links["edges"]).items())),
             "externals": externals, "other_dependencies": other, "runtime_files": runtime,
             "declared": [d for rel in runtime for d in (declarations.get(rel) or _declared(rel, texts[rel]))],
             "groups": groups, "alone": alone,
             "confirmed": [n["name"] for n in (system or {}).get("nodes", []) if n["status"] == "confirmed"],
             "cards": cards}
    return value
