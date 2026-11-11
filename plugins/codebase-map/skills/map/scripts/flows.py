#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# ///
"""Flows of a snapshot: links deduced from the project's link rules, then followed.

A model writes the rules once per project (`daodan/flow-rules/v1`); this module only
applies them, so the same snapshot and rules always give the same links. A rule
names a project function by `file::name` and says what one of its calls means:

- `scrive` / `legge`: the call writes or reads a store; `key` says where the
  field, collection or key is: `argN`, `selector` (`s => s.field`), `object`
  (`{field: ...}`).
- `rotta`: the call reaches a route; `route` gives `service`, `method`, `path`,
  each a literal or `argN`.
- `offre`: the call declares a route (`route` as above); with `decorates` the
  route belongs to the decorated function.
- `attiva`: the call binds a user action to the handler in `handler` (`argN`).
- `ingresso`: the call declares an entry point (`entry` names its kind); with
  `decorates` the entry point is the decorated function.

An argument counts only when it is a literal or a constant bound to a literal; a
computed one is a gap, never a guess. A store link needs the same store and key,
a route link the same service, method and path. External modules of the module
graph are nodes too: a symbol in a file an external module cites as evidence
uses that module, a declared link.

    python flows.py links MANIFEST --rules RULES
    python flows.py trace MANIFEST --rules RULES (--from NODE | --to NODE | --through NODE)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict, deque
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import edge_view  # noqa: E402
import semantic_store  # noqa: E402
import snapshot  # noqa: E402
from snapshot_store import _unpack, open_snapshot  # noqa: E402

RULES_SCHEMA = "daodan/flow-rules/v1"
LINKS_SCHEMA = "daodan/flow-links/v1"
FLOW_SCHEMA = "daodan/flow/v1"
LINKS = ("scrive", "legge", "rotta", "offre", "attiva", "ingresso")
MAX_EDGES = 5000
_ARG = re.compile(r"arg(\d+)$")
_IDENT = re.compile(r"[A-Za-z_$][\w$]*$")
_STRING = re.compile(r"""(['"`])((?:\\.|(?!\1).)*)\1$""", re.S)
_SELECTOR = re.compile(r"""^\(?\s*([A-Za-z_$][\w$]*)\s*(?::[^)=]*)?\)?\s*=>\s*\1\s*\.\s*([A-Za-z_$][\w$]*)""")
_LAMBDA = re.compile(r"^lambda\s+([A-Za-z_]\w*)\s*:\s*\1\s*\.\s*([A-Za-z_]\w*)")
_KEY = re.compile(r"""^\s*(?:\.\.\.|\*\*)|^\s*(['"]?)([A-Za-z_$][\w$]*)\1\s*(?::|,|$)""")


# ---------------------------------------------------------------- rules

def load_rules(path: Path) -> list[dict]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("schema") != RULES_SCHEMA or not isinstance(payload.get("rules"), list):
        raise ValueError(f"rules must be {RULES_SCHEMA} with a rules list")
    for index, rule in enumerate(payload["rules"]):
        where = f"rule {index}"
        if not isinstance(rule, dict) or rule.get("link") not in LINKS:
            raise ValueError(f"{where}: link must be one of {', '.join(LINKS)}")
        if not isinstance(rule.get("callee"), str) or "::" not in rule["callee"]:
            raise ValueError(f"{where}: callee must be file::name")
        need = {"scrive": ("store", "key"), "legge": ("store", "key"), "rotta": ("route",),
                "offre": ("route",), "attiva": ("handler",), "ingresso": ("entry",)}[rule["link"]]
        missing = [name for name in need if not rule.get(name)]
        if missing:
            raise ValueError(f"{where}: {rule['link']} needs {', '.join(missing)}")
        if rule["link"] in ("rotta", "offre") and not {"service", "method", "path"} <= set(rule["route"]):
            raise ValueError(f"{where}: route needs service, method and path")
    return payload["rules"]


# ---------------------------------------------------------------- source

class Source:
    """Verified text of the snapshot's files: a file edited since the snapshot is a gap."""

    def __init__(self, store):
        self.store = store
        self.root = Path(store["root"])
        self.cache: dict[str, list[str] | None] = {}

    def lines(self, rel: str) -> list[str] | None:
        if rel not in self.cache:
            entry = self.store.get_file(rel, semantic=False) or {}
            try:
                text = (self.root / rel).read_bytes().decode("utf-8", errors="replace")
                text = text.replace("\r\n", "\n").replace("\r", "\n")
            except OSError:
                text = None
            self.cache[rel] = text.split("\n") if text is not None and snapshot.hash_text(text) == entry.get("hash") else None
        return self.cache[rel]

    def after(self, rel: str, line: int, column: int) -> str | None:
        """Text from a 1-based line and a byte column to the end of the file."""
        lines = self.lines(rel)
        if lines is None or not 1 <= line <= len(lines):
            return None
        head = lines[line - 1].encode("utf-8")[column:].decode("utf-8", errors="replace")
        return "\n".join([head, *lines[line:]])


def call_arguments(text: str) -> list[str] | None:
    """Top-level arguments of the call whose callee ends where `text` starts."""
    start = text.find("(")
    if start < 0 or text[:start].strip():
        return None
    depth, quote, escaped, current, args = 0, None, False, [], []
    for char in text[start + 1:]:
        if quote:
            current.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue
        if char in "'\"`":
            quote = char
        elif char in "([{":
            depth += 1
        elif char in ")]}":
            if depth == 0:
                args.append("".join(current).strip())
                return [arg for arg in args if arg] if args != [""] else []
            depth -= 1
        elif char == "," and depth == 0:
            args.append("".join(current).strip())
            current = []
            continue
        current.append(char)
    return None


def object_keys(text: str) -> list[str] | None:
    text = text.strip()
    if not (text.startswith("{") and text.endswith("}")):
        return None
    parts = call_arguments("(" + text[1:-1] + ")")
    keys = []
    for part in parts or []:
        match = _KEY.match(part)
        if match is None or match.group(2) is None:
            return None
        keys.append(match.group(2))
    return keys


# ---------------------------------------------------------------- snapshot facts

class Facts:
    def __init__(self, store, db):
        self.store, self.db = store, db
        self.source = Source(store)
        self.declarations = {row[0]: {"id": row[0], "file": row[1], "name": row[2], "kind": row[3],
                                      "line": row[4], "column": row[5], "end": row[6], **_unpack(row[7])}
                             for row in db.execute("SELECT id,file,name,kind,l0,c0,l1,payload FROM sem_declarations")}
        self.reads = defaultdict(list)
        for ref_id, file, l0, c0, target in db.execute(
                "SELECT id,file,l0,c0,target_id FROM sem_references WHERE kind='read'"):
            self.reads[(file, l0, c0)].append(target)
        self.imports = defaultdict(set)
        for source, target in db.execute("SELECT source,target FROM sem_edges"):
            self.imports[source].add(target)

    def targets(self, name: str, file: str, line: int, column: int, kinds: tuple) -> list[str]:
        """Declarations an identifier names: its resolved read, else the one module-level
        declaration of that name in the file or in a file it imports."""
        resolved = [t for t in self.reads.get((file, line, column), [])
                    if self.declarations.get(t or "", {}).get("kind") in kinds]
        if resolved:
            return resolved
        found = [d["id"] for d in self.declarations.values()
                 if d["name"] == name and d["kind"] in kinds and d.get("scope") == "module"
                 and (d["file"] == file or d["file"] in self.imports.get(file, ()))]
        return found if len(found) == 1 else []

    def node(self, declaration_id: str | None) -> str | None:
        """The named symbol a declaration belongs to: an anonymous function counts as its owner."""
        declaration = self.declarations.get(declaration_id or "")
        if declaration is None:
            return None
        name = declaration.get("qualified_name") or declaration["name"]
        name = name.split(".(anonymous)")[0]
        return f"{declaration['file']}::{name}" if name and name != "(anonymous)" else None

    def named(self, declaration_id: str | None) -> str | None:
        declaration = self.declarations.get(declaration_id or "")
        if declaration is None:
            return None
        return f"{declaration['file']}::{declaration.get('qualified_name') or declaration['name']}"

    def decorated(self, file: str, line: int) -> str | None:
        """The function a decorator on this line decorates: the first declaration below it."""
        below = sorted((d for d in self.declarations.values()
                        if d["file"] == file and d["kind"] in ("function", "class", "method") and d["line"] > line),
                       key=lambda d: d["line"])
        return self.node(below[0]["id"]) if below else None

    def literal(self, text: str, file: str, line: int, column: int) -> str | None:
        """The value of a literal, or of a constant bound to a literal; None when computed."""
        text = text.strip()
        match = _STRING.match(text)
        if match:
            return None if match.group(1) == "`" and "${" in match.group(2) else match.group(2)
        if not _IDENT.match(text):
            return None
        for target in self.targets(text, file, line, column, ("binding",)):
            binding = self.declarations[target]
            rest = self.source.after(binding["file"], binding["line"], 0)
            found = re.match(r"[^=\n]*\b" + re.escape(binding["name"]) + r"\b[^=\n]*=\s*(['\"`])([^'\"`\n]*)\1", rest or "")
            if found:
                return found.group(2)
        return None

    def handler(self, text: str, file: str, line: int, column: int) -> str | None:
        """The function an action argument names, directly or as the one call of an arrow."""
        text = text.strip()
        if _IDENT.match(text):
            found = self.targets(text, file, line, column, ("function", "method"))
            return self.node(found[0]) if found else None
        arrow = next((d for d in self.declarations.values() if d["file"] == file and d["line"] == line
                      and d["column"] == column and d["name"] == "(anonymous)"), None)
        if arrow is None:
            return None
        calls = [row[0] for row in self.db.execute(
            "SELECT target_id FROM sem_references WHERE kind='call' AND caller=? AND resolution='resolved'",
            (arrow["id"],))]
        return self.node(calls[0]) if len(calls) == 1 else None


def _position(base_line: int, base_column: int, text_before: str, arg_text: str) -> tuple[int, int]:
    """Line and byte column where an argument starts, from the text between the callee end and it."""
    lead = text_before + arg_text[:len(arg_text) - len(arg_text.lstrip())]
    rows = lead.split("\n")
    if len(rows) == 1:
        return base_line, base_column + len(rows[0].encode("utf-8"))
    return base_line + len(rows) - 1, len(rows[-1].encode("utf-8"))


def _arguments_with_positions(text: str, line: int, column: int):
    args = call_arguments(text)
    if args is None:
        return None
    out, cursor = [], text.find("(") + 1
    for arg in args:
        at = text.find(arg, cursor)
        out.append((arg, *_position(line, column, text[:at], "")))
        cursor = at + len(arg)
    return out


def _value(spec, args, facts, file):
    """A rule field: a literal string, or `argN` read from the call."""
    match = _ARG.match(str(spec))
    if match is None:
        return spec
    index = int(match.group(1))
    if args is None or index >= len(args):
        return None
    text, line, column = args[index]
    return facts.literal(text, file, line, column)


# ---------------------------------------------------------------- links

def link_facts(manifest: Path, rules: list[dict]) -> dict:
    """Accesses, deduced links, entry points and gaps of a snapshot under the given rules."""
    by_callee = defaultdict(list)
    for rule in rules:
        by_callee[rule["callee"]].append(rule)
    accesses, entries, actions, routes_offered, route_calls, gaps = [], [], [], [], [], []
    calls = []
    with open_snapshot(manifest) as store, semantic_store.semantic_reader(store) as db:
        facts = Facts(store, db)
        view = edge_view.load_edge_view(store)
        for ref in view["references"]:
            target = facts.named(ref.get("target_id")) if ref["resolution"] == "resolved" else None
            caller = facts.node(ref.get("caller"))
            span = ref.get("span") or [None, None, None, None]
            site = f"{ref['file']}:{span[0]}"
            if target and caller:
                calls.append({"from": caller, "to": facts.node(ref["target_id"]), "site": site})
            matched = by_callee.get(target or "")
            if not matched:
                if ref["resolution"] != "resolved" and any(rule["callee"].rsplit("::", 1)[1].split(".")[-1]
                                                            == ref.get("last_name") for rule in rules):
                    gaps.append({"site": site, "reason": f"call to {ref.get('last_name')} is unresolved"})
                continue
            text = facts.source.after(ref["file"], span[2], span[3])
            args = _arguments_with_positions(text, span[2], span[3]) if text is not None else None
            if args is None:
                gaps.append({"site": site, "reason": "call arguments not readable"})
                continue
            for rule in matched:
                owner = facts.decorated(ref["file"], span[0]) if rule.get("decorates") else caller
                if owner is None:
                    gaps.append({"site": site, "reason": f"{rule['link']} call outside a named symbol"})
                    continue
                link = rule["link"]
                if link in ("scrive", "legge"):
                    keys = _keys(rule["key"], args, facts, ref["file"])
                    if not keys:
                        gaps.append({"site": site, "symbol": owner, "reason": f"{link} {rule['store']}: key not a literal"})
                    for key in keys or []:
                        accesses.append({"symbol": owner, "link": link, "store": rule["store"], "key": key, "site": site})
                elif link in ("rotta", "offre"):
                    identity = tuple(_value(rule["route"][name], args, facts, ref["file"])
                                     for name in ("service", "method", "path"))
                    if None in identity:
                        gaps.append({"site": site, "symbol": owner, "reason": f"{link}: route not a literal"})
                        continue
                    record = {"symbol": owner, "service": identity[0], "method": identity[1].upper(),
                              "path": identity[2], "site": site}
                    (routes_offered if link == "offre" else route_calls).append(record)
                    if link == "offre":
                        entries.append({"symbol": owner, "kind": "rotta", "site": site})
                elif link == "attiva":
                    match = _ARG.match(rule["handler"])
                    index = int(match.group(1)) if match else -1
                    handler = (facts.handler(args[index][0], ref["file"], args[index][1], args[index][2])
                               if 0 <= index < len(args) else None)
                    if handler is None:
                        gaps.append({"site": site, "symbol": owner, "reason": "attiva: handler not a named function"})
                        continue
                    label = _value("arg0", args, facts, ref["file"])
                    actions.append({"symbol": owner, "handler": handler, "label": label, "site": site})
                    entries.append({"symbol": handler, "kind": "azione", "site": site})
                elif link == "ingresso":
                    entries.append({"symbol": owner, "kind": rule["entry"], "site": site})
        external = _external_nodes(store, manifest)
        symbols_by_file = defaultdict(set)
        for declaration in facts.declarations.values():
            if declaration["kind"] in ("function", "method", "class"):
                node = facts.node(declaration["id"])
                if node:
                    symbols_by_file[declaration["file"]].add(node)

    edges = [{"from": c["from"], "to": c["to"], "type": "chiama", "origin": "diretto", "site": c["site"]}
             for c in calls]
    for access in accesses:
        store_node = f"store:{access['store']}/{access['key']}"
        if access["link"] == "scrive":
            edges.append({"from": access["symbol"], "to": store_node, "type": "scrive", "origin": "dedotto", "site": access["site"]})
        else:
            edges.append({"from": store_node, "to": access["symbol"], "type": "legge", "origin": "dedotto", "site": access["site"]})
    handlers = defaultdict(list)
    for offer in routes_offered:
        handlers[(offer["service"], offer["method"], offer["path"])].append(offer)
    for call in route_calls:
        found = handlers.get((call["service"], call["method"], call["path"]), [])
        if len(found) != 1:
            gaps.append({"site": call["site"], "symbol": call["symbol"],
                         "reason": f"route {call['service']} {call['method']} {call['path']}: "
                                   f"{'no handler' if not found else 'several handlers'}"})
            continue
        edges.append({"from": call["symbol"], "to": found[0]["symbol"], "type": "chiama", "origin": "dedotto",
                      "site": call["site"], "route": [call["service"], call["method"], call["path"]]})
    for action in actions:
        edges.append({"from": action["symbol"], "to": action["handler"], "type": "attiva", "origin": "dedotto",
                      "site": action["site"], "label": action["label"]})
    for module in external:
        for file in module["evidence_files"]:
            for symbol in sorted(symbols_by_file.get(file, ())):
                edges.append({"from": symbol, "to": f"module:{module['name']}", "type": "usa", "origin": "dichiarato",
                              "site": file, "status": module["status"]})
    stores = defaultdict(lambda: {"writes": set(), "reads": set()})
    for access in accesses:
        stores[f"{access['store']}/{access['key']}"]["writes" if access["link"] == "scrive" else "reads"].add(access["symbol"])
    unique = {}
    for edge in edges:
        unique.setdefault((edge["from"], edge["to"], edge["type"], edge["site"]), edge)
    return {"schema": LINKS_SCHEMA, "manifest": str(manifest),
            "stores": {name: {"writes": sorted(v["writes"]), "reads": sorted(v["reads"])} for name, v in sorted(stores.items())},
            "entries": sorted({(e["symbol"], e["kind"]): e for e in entries}.values(), key=lambda e: (e["kind"], e["symbol"])),
            "edges": sorted(unique.values(), key=lambda e: (e["from"], e["to"], e["type"], e["site"])),
            "external": [{"name": m["name"], "status": m["status"]} for m in external],
            "gaps": sorted(gaps, key=lambda g: (g["site"], g["reason"]))}


def _keys(spec: str, args, facts, file) -> list[str] | None:
    if not args:
        return None
    text, line, column = args[0]
    if spec == "selector":
        match = _SELECTOR.match(text.strip()) or _LAMBDA.match(text.strip())
        return [match.group(2)] if match else None
    if spec == "object":
        return object_keys(text)
    value = _value(spec, args, facts, file)
    return [value] if value is not None else None


def _external_nodes(store, manifest: Path) -> list[dict]:
    """External modules of the module graph, with the files they cite as evidence."""
    import modules
    try:
        graph = modules.ensure_graph(manifest)
        payload = json.loads(Path(graph["graph"]).read_text(encoding="utf-8"))
    except (OSError, ValueError, KeyError):
        return []
    out = []
    for module in payload.get("modules", []):
        if module.get("location") != "external":
            continue
        files = sorted({str(item.get("path") if isinstance(item, dict) else item).split("#")[0]
                        for item in module.get("evidence", [])})
        out.append({"name": module["name"], "status": module.get("status"), "evidence_files": files})
    return out


# ---------------------------------------------------------------- flows

def trace(links: dict, start: str, direction: str, boundary: list[str] | None = None,
          max_edges: int = MAX_EDGES) -> dict:
    """Follow links from a node, each once, until nothing is left, a boundary or the budget stops it.

    `from` follows what the node causes: calls, activations, writes and the readers of
    what was written. `to` follows where the node's data comes from: the stores it
    reads, their writers and what those call. `through` lists the entry points whose
    `from` flow contains the node.
    """
    if direction == "through":
        flows = [trace(links, entry["symbol"], "from", boundary, max_edges) for entry in links["entries"]]
        hits = [flow for flow in flows if start in flow["nodes"]]
        return {"schema": FLOW_SCHEMA, "start": start, "direction": "through",
                "entries": [flow["start"] for flow in hits], "complete": all(flow["complete"] for flow in hits)}
    outgoing, incoming = defaultdict(list), defaultdict(list)
    for edge in links["edges"]:
        outgoing[edge["from"]].append(edge)
        incoming[edge["to"]].append(edge)

    def steps(node):
        if direction == "from":
            return [(edge, edge["to"]) for edge in outgoing[node] if edge["type"] in ("chiama", "attiva", "scrive", "legge", "usa")]
        out = [(edge, edge["to"]) for edge in outgoing[node] if edge["type"] in ("chiama", "scrive", "usa")]
        out += [(edge, edge["from"]) for edge in incoming[node] if edge["type"] in ("legge", "scrive")]
        return out

    def inside(node):
        if not boundary or "::" not in node:
            return True
        file = node.split("::", 1)[0]
        return any(b == "." or file == b or file.startswith(b.rstrip("/") + "/") for b in boundary)

    seen, followed, outside, queue = {start}, [], [], deque([start])
    stopped = None
    while queue:
        node = queue.popleft()
        for edge, nxt in steps(node):
            if len(followed) >= max_edges:
                stopped = "budget"
                break
            if not inside(nxt):
                outside.append(edge)
                continue
            followed.append(edge)
            if nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
        if stopped:
            break
    gaps = [gap for gap in links["gaps"] if gap.get("symbol") in seen]
    return {"schema": FLOW_SCHEMA, "start": start, "direction": direction,
            "nodes": sorted(seen), "edges": followed, "outside_boundary": outside, "gaps": gaps,
            "stopped": stopped, "complete": not (stopped or outside or gaps),
            "files": sorted({node.split("::", 1)[0] for node in seen if "::" in node})}


# ---------------------------------------------------------------- units

def units(links: dict, sizes: dict[str, int], perimeter: list[str], limit: int) -> dict:
    """The perimeter's files in units of at most `limit` bytes, following the flows.

    Each entry point's flow gives its files in the order the flow meets them. The
    writers and readers of one store key form a block that is never split while it
    fits the limit. A file shared by two flows goes in both units; files no flow
    touches follow by path, as `pack()` does. Every perimeter file is assigned.
    """
    def inside(file):
        return any(p == "." or file == p or file.startswith(p.rstrip("/") + "/") for p in perimeter)

    files_of = lambda symbols: [s.split("::", 1)[0] for s in symbols if "::" in s]  # noqa: E731
    blocks_of: dict[str, list[str]] = {}
    for key, store in links["stores"].items():
        block = list(dict.fromkeys(f for f in files_of(store["writes"] + store["reads"]) if inside(f)))
        for file in block:
            blocks_of.setdefault(file, block)
    out, cuts = [], []
    for entry in links["entries"]:
        flow = trace(links, entry["symbol"], "from")
        blocks, placed = [], set()
        for node in [flow["start"]] + [edge["to"] for edge in flow["edges"]]:
            for file in files_of([node]):
                block = [item for item in blocks_of.get(file, [file]) if inside(item) and item not in placed]
                if block:
                    blocks.append(block)
                    placed.update(block)
        groups = _pack_blocks(blocks, sizes, limit)
        if len(groups) > 1:
            for edge in flow["edges"]:
                ends = files_of([edge["from"], edge["to"]])
                if len(ends) == 2 and not any(set(ends) <= set(g) for g in groups):
                    cuts.append({"entry": entry["symbol"], "edge": [edge["from"], edge["to"]], "type": edge["type"]})
        out.extend({"files": group, "entries": [entry["symbol"]]} for group in groups)
    # A unit whose files another unit already holds adds nothing but its entry point.
    kept = []
    for unit in sorted(out, key=lambda u: -len(u["files"])):
        holder = next((k for k in kept if set(unit["files"]) <= set(k["files"])), None)
        if holder is None:
            kept.append(unit)
        elif unit["entries"][0] not in holder["entries"]:
            holder["entries"].append(unit["entries"][0])
    out = sorted(kept, key=lambda u: out.index(u))
    assigned = {file for unit in out for file in unit["files"]}
    rest = sorted(f for f in sizes if inside(f) and f not in assigned)
    for group in _pack_blocks([[f] for f in rest], sizes, limit):
        out.append({"files": group, "entries": []})
    counts = defaultdict(int)
    for unit in out:
        for file in unit["files"]:
            counts[file] += 1
    distinct = sorted(f for f in sizes if inside(f))
    return {"units": out, "cuts": cuts, "files": len(distinct),
            "assigned": sum(1 for f in distinct if counts[f]), "in_several_units": sum(1 for f in distinct if counts[f] > 1)}


def _pack_blocks(blocks: list[list[str]], sizes: dict[str, int], limit: int) -> list[list[str]]:
    """Blocks in order, a new group when the next block would pass the limit; a block larger
    than the limit is split by file, and a file larger than the limit stands alone."""
    groups, size = [], 0
    for block in blocks:
        weight = sum(sizes.get(f, 0) for f in block)
        if weight > limit:
            for file in block:
                if groups and size + sizes.get(file, 0) <= limit:
                    groups[-1].append(file)
                    size += sizes.get(file, 0)
                else:
                    groups.append([file])
                    size = sizes.get(file, 0)
            continue
        if groups and size + weight <= limit:
            groups[-1].extend(block)
            size += weight
        else:
            groups.append(list(block))
            size = weight
    return groups


def file_sizes(manifest: Path) -> dict[str, int]:
    with open_snapshot(manifest) as store:
        return {rel: int(entry.get("size") or 0) for rel, entry in snapshot.file_headers(store).items()}


# ---------------------------------------------------------------- cli

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("links", "trace", "units"):
        command = sub.add_parser(name)
        command.add_argument("manifest", type=Path)
        command.add_argument("--rules", type=Path, required=True)
    sub.choices["units"].add_argument("--perimeter", action="append", required=True)
    sub.choices["units"].add_argument("--limit", type=int, default=120_000)
    trace_parser = sub.choices["trace"]
    group = trace_parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--from", dest="start_from")
    group.add_argument("--to", dest="start_to")
    group.add_argument("--through", dest="start_through")
    trace_parser.add_argument("--boundary", action="append", default=None)
    args = parser.parse_args(argv)
    links = link_facts(args.manifest.resolve(), load_rules(args.rules))
    if args.command == "links":
        print(json.dumps(links, indent=2, sort_keys=True))
        return 0
    if args.command == "units":
        result = units(links, file_sizes(args.manifest.resolve()), args.perimeter, args.limit)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    start, direction = next((value, name) for value, name in ((args.start_from, "from"), (args.start_to, "to"),
                                                                (args.start_through, "through")) if value)
    print(json.dumps(trace(links, start, direction, args.boundary), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
