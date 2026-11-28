"""What the app's page draws, composed from a run: the pre-map's inventory and the graph's groups.

Composition only: the stack, the modules and the envelope are the service's; the files and their languages are the
run's snapshot headers. Nothing of the project runs. The graph groups files by module when the run has two or more,
otherwise by the directory that holds them (its `grouping`), and counts the relations between groups; an external node
holds no file and is drawn beside the groups at either grouping (a service, say); frameworks, libraries and tools are
nodes under «Tecnologie», which opens into them, and each group keeps those its files declare (`projects`). These are the natures `codice` and `fisico`
(`node_model.NATURES`; the only ones the app builds): a group opens in place into its directories
and files, a directory in turn, a file into its outermost symbols and a symbol into those its lines hold (`view`); a
file's symbols and their calls are also the inspector's, open or not (`symbols`).
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import PurePosixPath

import node_model
from premap.suffix_table import NAMES
from service_registry import marked, package_key
from snapshot_store import open_snapshot, resolve_run_snapshot
from system_levels import NATURES, _contract, natures_asked
from technologies import module_declaration

STRUCTURE = ("file", "directory", "symbol")
EVIDENCE = 20  # sites kept per relation, as the envelope keeps
BUILT = ("codice", "fisico")  # the natures the app builds: files and groups, external nodes
MODES = ("highlight", "hide")  # what the filter by nature does to the other nodes: dims them, or hides them
GRADES = ("uncertain", "sampled", "observed", "inferred", "confirmed")  # a relation's statuses, weakest first
BLOCK = 300  # the children a view shows of an open group at once, the view of the spec's measure


def headers(run_dir) -> dict:
    """The snapshot's file headers of the run in `run_dir`, by path."""
    state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
    with open_snapshot(resolve_run_snapshot(run_dir, state)) as store:
        return dict(store.iter_file_headers_only())


def _inside(path: str, root: str) -> bool:
    return root in ("", ".") or path == root or path.startswith(root.rstrip("/") + "/")


def _dependencies(module: dict) -> list[dict]:
    """Keep a declaration beside its resolved direct version when the package identity gives a unique pairing."""
    rows = [{"name": item["name"], "scope": item["ecosystem"], "state": "declared",
             "source": item["path"] + (f":{item['line']}" if item.get("line") else ""),
             **({"version": item["version"]} if item.get("version") else {})}
            for item in module.get("libraries", [])]
    resolved = module.get("resolved_libraries") or []
    if not resolved:
        return rows

    def key(ecosystem, name):
        return ecosystem, package_key(ecosystem, name)

    declarations = {key(row["scope"], row["name"]): row for row in rows}
    direct = Counter(key(item["ecosystem"], item["name"]) for item in resolved if item["direct"])
    for item in resolved:
        identity = key(item["ecosystem"], item["name"])
        declared = declarations.get(identity)
        if declared is not None and item["direct"] and direct[identity] == 1:
            row = declared
            row.update(state="declared_resolved", resolution_source=item["path"])
        else:
            row = {"name": item["name"], "scope": item["ecosystem"], "source": item["path"], "state": "resolved"}
            rows.append(row)
        row.update(resolved_version=item["version"], direct=item["direct"])
    return rows


def premap(stack: dict, modules: dict, files: dict) -> dict:
    """Files, languages, technologies and the units of the stack with their declared and resolved libraries. A technology
    whose registry entry has a logo carries the entry's id in `mark`, as in the envelope; the others have none."""
    if "modules" not in stack:  # the snapshot's gate answered in place of the stack
        raise ValueError(stack.get("reason") or "the stack of the run is not available")
    described = {module["id"]: module for module in modules.get("modules", [])}
    known, logos = {item["id"]: item for item in stack["technologies"]}, marked()
    units, technologies = [], []
    service_roots = {}
    for module in stack["modules"]:
        paths = module.get("paths") or ["."]
        root = paths[0]
        for service in module.get("configured_services", []):
            service_roots.setdefault((service["name"], service["declared_in"]), set()).add(root)
        declared = [tool["declared_in"] for tool in module.get("toolchains", [])]
        units.append({
            "id": module["id"], "name": module["name"], "root": root, "kind": module.get("kind"),
            "status": described.get(module["id"], {}).get("status"),
            "description": described.get(module["id"], {}).get("description") or "",
            "manifest": next(iter(declared + [item["path"] for item in module.get("libraries", [])]), None),
            "dependencies": _dependencies(module)})
        library_sources = {item["id"]: item for item in module.get("libraries", []) if item.get("id")}
        for ident in module.get("technologies", []):
            found = known.get(ident)
            if found is None:
                continue
            sign = module.get("technology_evidence", {}).get(ident)
            if sign is None:  # older records did not retain the module's declaring site
                signs = (s for s in found.get("signs", []) if module_declaration(s))
                sign = library_sources.get(ident) or next((s for s in signs if any(_inside(s["path"], path) for path in paths)), {})
            technologies.append({"name": found["name"], "category": found.get("category") or "tecnologia",
                                 "source": (sign.get("path") or "") + (f":{sign['line']}" if sign.get("line") else ""),
                                 "unit": root, "state": "recognized", **({"mark": ident} if ident in logos else {})})
        technologies.extend({"name": tool["tool"], "category": "toolchain", "version": tool.get("version") or "",
                             "source": tool["declared_in"], "unit": root, "state": "declared"}
                            for tool in module.get("toolchains", []))
    for service in stack.get("configured_services", []):
        for root in sorted(service_roots.get((service["name"], service["declared_in"]), {""})):
            technologies.append({"name": service["name"], "category": "servizio configurato",
                                 "source": service["declared_in"], "unit": root, "state": "configured",
                                 **({"image": service["image"]} if service.get("image") else {})})
    for unit in units:
        parents = [other for other in units if other is not unit and other["root"] != unit["root"]
                   and _inside(unit["root"], other["root"])]
        unit["parent"] = max(parents, key=lambda other: len(other["root"]))["id"] if parents else None
    languages = Counter(header["language"] for header in files.values() if header.get("language"))
    return {"files": sorted(files), "units": units, "technologies": technologies,
            "languages": [{"name": NAMES.get(name, name.capitalize()), "files": count}
                          for name, count in sorted(languages.items(), key=lambda item: (-item[1], item[0]))]}


def graph(envelope: dict) -> dict:
    """The envelope's files grouped into nodes, and the relations between groups with their counts and sites."""
    grouping, entities, files, nodes, owner = _top(envelope)
    return {"grouping": grouping, "nodes": sorted(nodes.values(), key=lambda node: node["name"]),
            "edges": _edges(envelope["relations"], nodes, owner), "files": len(files),
            "symbols": sum(item["type"] == "symbol" for item in entities.values()),
            "unassigned": _unassigned(entities, files, owner), "gaps": envelope.get("gaps", []),
            "meta": envelope.get("meta", {})}


def levels(names: list | None) -> tuple:
    """The natures a request names (`system_levels.natures_asked`, which still takes the old names), in their order,
    both of BUILT when it names none: another one of the list is not built in the app yet, and is refused rather than
    served as the code's; `fisico` (the external nodes and their uses) is built only beside `codice`, which gives it
    the groups that use them."""
    if names is None:
        return BUILT
    if not isinstance(names, list) or not names or not all(isinstance(name, str) for name in names):
        raise ValueError("levels is a JSON list of levels")
    asked = natures_asked(names)
    for name in asked:
        if name not in BUILT:
            raise ValueError(f"the level {name!r} is not built in the app yet: it builds {' and '.join(BUILT)}")
    if "codice" not in asked:
        raise ValueError("the level 'fisico' is built in the app only beside 'codice'")
    return tuple(name for name in NATURES if name in asked)


def view(envelope: dict, groups: tuple = (), shown: tuple = BUILT, symbols_of=None, natures: list | None = None,
         mode: str = "highlight") -> dict:
    """The graph at the levels `shown` (`levels`) with `groups` open in place: the first grouping's nodes, each open
    group replaced by what it holds (a module or a directory its directories and files, `_contents`; a file its
    outermost symbols, read for that file only by `symbols_of(path)`, and a symbol those its lines hold, `_nested`),
    each node with its `level` and the open `group` that holds it, a first-level group, and its frame when open, with
    its stack (`_stack`); without `fisico` no external node nor its arrows. The edges are the envelope's
    relations lifted to the node that shows each end now (`_edges`), and an open file's calls between its symbols
    (`_calls`) in place of its file-to-file
    calls; a relation with no finer end (a module's own, a file's import) stays on its open group, which `open` lists
    with its parent so that it is drawn around what it holds. So a summary arrow becomes the arrows that make it up,
    with their counts, status and evidence, and the gaps stay. An asked id the graph does not show, or that holds
    nothing to open (an external node, a symbol holding no other), is refused, ending with the id.

    `natures` (`system_levels.natures_asked`) filters the same view, computed with the opening and never opening a
    group (`_filter`): `mode` `highlight` keeps every node and dims the others, `hide` keeps only those of the
    natures and contracts the arrows through the hidden ones; a nature no node has is `absent`."""
    if mode not in MODES:
        raise ValueError(f"mode is one of {', '.join(MODES)}")
    asked = None if natures is None else natures_asked(natures)
    grouping, entities, files, nodes, owner, holder, opened, read = _open(envelope, groups, symbols_of)
    unassigned = _unassigned(entities, files, owner)
    nodes = {ref: {**item, "level": "fisico" if item["location"] == "external" and item["kind"] != "technology" else "codice",
                   "group": holder[ref]} for ref, item in nodes.items()}
    nodes = {ref: item for ref, item in nodes.items() if item["level"] in shown}
    ends = {**nodes, **{group["id"]: group for group in opened}}
    files_read = {f"file:{path}" for path in read}  # their calls between files are read again by symbol
    relations = [item for item in envelope["relations"] if not (item["kind"] == "calls" and "origin" not in item and (
        item["source"] in files_read or item["target"] in files_read))] + _calls(read)
    edges = _edges(relations, ends, owner)
    gaps = [*envelope.get("gaps", []), *(gap for found in read.values() for gap in found["gaps"])]
    filtered = {}
    if asked is not None:
        nodes, edges, absent, lost = _filter(nodes, edges, {group["id"] for group in opened}, entities, asked, mode)
        gaps += lost
        filtered = {"natures": asked, "mode": mode, "absent": absent}
    return {"levels": list(shown), **filtered, "grouping": grouping, "open": opened,
            "nodes": sorted(nodes.values(), key=lambda item: item["name"]),
            "edges": edges, "files": len(files), "unassigned": unassigned, "gaps": gaps,
            "meta": envelope.get("meta", {})}


def _natures(node: dict, entities: dict) -> list[str]:
    """A node's natures (`node_model.natures`): «Tecnologie» and a block of a large group (`more`) have those of
    what they hold (`_held`)."""
    if node["kind"] in ("group", "more"):
        return node_model.natures("gruppo", contained=_held(node, entities))
    return node_model.natures(node_model.species_of({"type": node["kind"], "node_type": node.get("node_type")}),
                              node["location"])


def _held(node: dict, entities: dict) -> list[list[str]]:
    """The natures of each thing a closed node holds that the graph knows without reading: its files, unless it is
    one, and its members (a symbol's outline is read only when its file opens)."""
    files = [] if node["kind"] == "file" else node["files"]
    members = [_natures(_node(entities[ref], entities[ref]["name"]), entities) if ref in entities else ["codice"]
               for ref in node.get("members", ())]
    return [["codice"]] * len(files) + members


def _filter(nodes: dict, edges: list, frames: set, entities: dict, asked: list, mode: str) -> tuple:
    """The view filtered by the natures `asked`, never opening a group: a node is admitted when it has one of them,
    and a closed node holding admitted ones says how many (`lit`). `highlight` keeps every node and dims (`dim`)
    those neither admitted nor lit; `hide` keeps only admitted or lit ones and draws an arrow between two of them
    (or an open group's frame) through hidden nodes as `system_levels._contract` does (`through`, and the arrows it
    passes in `steps`, with their sites), its grade the weakest (`GRADES`), a spent path budget a gap. The natures
    no node has nor holds are `absent`."""
    own = {ref: set(_natures(item, entities)) for ref, item in nodes.items()}
    held = {ref: _held(item, entities) for ref, item in nodes.items()}
    lit = {ref: sum(bool(set(found) & set(asked)) for found in held[ref]) for ref in nodes}
    absent = [nature for nature in asked
              if not any(nature in own[ref] or any(nature in found for found in held[ref]) for ref in nodes)]
    admitted = {ref for ref in nodes if own[ref] & set(asked) or lit[ref]}
    shown = {ref: {**item, **({"lit": lit[ref]} if lit[ref] else {}), **({} if ref in admitted else {"dim": True})}
             for ref, item in nodes.items() if mode == "highlight" or ref in admitted}
    if mode == "highlight":
        return shown, edges, absent, []
    visible = admitted | frames
    kept = [edge for edge in edges if edge["source"] in visible and edge["target"] in visible]
    by_id = {edge["id"]: edge for edge in edges}
    steps = [{"from": edge["source"], "to": edge["target"], "data": "", "asserts": [], "via": [], "through": [],
              "status": edge["status"] + (" conflict" if edge.get("conflict") else ""), "proof": [{"edge": edge["id"]}]}
             for edge in edges if edge["source"] not in visible or edge["target"] not in visible]
    arrows, gaps = _contract(visible, steps, set(), GRADES)
    for arrow in arrows:
        parts = [by_id[item["edge"]] for item in arrow["proof"]]
        status, _, conflict = arrow["status"].partition(" ")
        counts = Counter()
        for part in parts:
            counts.update(part["counts"])
        kept.append({"id": f"{arrow['from']}->{arrow['to']} via" + ("" if arrow["status"] == "confirmed" else f" {arrow['status']}"),
                     "source": arrow["from"], "target": arrow["to"], "counts": dict(counts), "status": status,
                     "evidence": [site for part in parts for site in part["evidence"]][:EVIDENCE],
                     "relations": list(dict.fromkeys(ref for part in parts for ref in part["relations"])),
                     "through": arrow["through"], "steps": parts, **({"conflict": True} if conflict else {})})
    lost = [{"refs": [end for end in (gap["from"], gap["to"]) if end], "reason": gap["reason"]} for gap in gaps]
    return shown, sorted(kept, key=lambda edge: edge["id"]), absent, lost


def flow(envelope: dict, ref: str, groups: tuple = (), symbols_of=None) -> dict:
    """The envelope's flow `ref` step by step with `groups` open in place (`_open`, as `view` opens them).

    Each step, in the order the flow was followed (`n`), goes from `source` to `target` as the graph shows its ends
    now (a symbol's file, a file's closed group; the same node at both ends is a step inside it), names the step that
    reached its source (`parent`, none from the entry), and keeps the arc it was (`relation`: ends, type, origin,
    site) and its site (`proof`). A step has a condition or a profile only where a source gives one; none of the
    flow's steps has a source for them yet (the profiles of Compose are of services, which no step names), so the
    keys are absent. Each closed node the flow crosses (`groups`) lists where it enters (`entries`) and leaves
    (`exits`): the step and its end inside. A closed group summarises its arrows, and reads as a path from what
    enters it to what it reaches: `to_prove` lists each such path (a step of the flow into the group, then an arc of
    the envelope's flows out of it) where no arc inside the group joins the end entered to the end that leaves, the
    rule of `system_levels._close`; with one such arc the flow follows it and the path is its steps."""
    from visual import _site
    found = next((item for item in envelope.get("flows", []) if item["ref"] == ref), None)
    if found is None:
        raise ValueError(f"the run has no flow {json.dumps(ref, ensure_ascii=False)}")
    _, _, _, nodes, owner, _, _, _ = _open(envelope, groups, symbols_of)

    def seen(end: str) -> str:
        if end in owner or not end.startswith("symbol:"):
            return owner.get(end, end)
        file = "file:" + end[len("symbol:"):].split("::", 1)[0]
        return owner.get(file, file)

    steps, reached, crossed = [], {}, {}
    for n, step in enumerate(found["steps"], 1):
        source, target = seen(step["source"]), seen(step["target"])
        steps.append({"n": n, "parent": reached.get(step["source"]), "source": source, "target": target,
                      "relation": step, "proof": [_site(step["site"])]})
        reached.setdefault(step["target"], n)
        if source != target:
            for end, side, held in ((target, "entries", step["target"]), (source, "exits", step["source"])):
                if end in nodes and end != held:
                    crossed.setdefault(end, {"id": end, "name": nodes[end]["name"], "entries": [], "exits": []})[side].append(
                        {"step": n, "end": held})
    pool = list({(item["source"], item["target"], item["type"], item["site"]): item
                 for other in envelope.get("flows", []) for item in other["steps"]}.values())
    to_prove = []
    for group in sorted(crossed):
        inner = {end for item in pool for end in (item["source"], item["target"]) if seen(end) == group}
        inside = defaultdict(set)
        for item in pool:
            if item["source"] in inner and item["target"] in inner:
                inside[item["source"]].add(item["target"])

        paths: dict[tuple, dict] = {}
        for entry in crossed[group]["entries"]:
            first = steps[entry["step"] - 1]
            for item in pool:
                if item["source"] in inner and seen(item["target"]) != group:
                    path = paths.setdefault((first["source"], seen(item["target"])), {"enters": set(), "leaves": set(), "joined": False})
                    path["enters"].add(entry["end"])
                    path["leaves"].add(item["source"])
                    path["joined"] = path["joined"] or _joined(inside, entry["end"], item["source"])
        to_prove += [{"group": group, "from": start, "to": stop, "enters": sorted(path["enters"]),
                      "leaves": sorted(path["leaves"]),
                      "reason": f"no arc inside {group} joins what enters it to what leaves it"}
                     for (start, stop), path in sorted(paths.items()) if not path["joined"]]
    return {"flow": ref, "entry": seen(found["entry"]), "complete": found["complete"], "steps": steps,
            "groups": [crossed[group] for group in sorted(crossed)], "to_prove": to_prove, "gaps": found["gaps"]}


def _block(group: str, block: int, children: dict, rest: dict) -> dict:
    """The `children` of `group` a view shows at once: all of them up to BLOCK, else the first BLOCK by name and a
    node `more:<group>#<block>` «altri N» holding the others (their files, and the members of those without files),
    which `rest` keeps until it opens. No child is lost: the blocks add up to the children."""
    if len(children) <= BLOCK:
        return children
    order = sorted(children, key=lambda ref: (children[ref]["name"], ref))
    shown, left = {ref: children[ref] for ref in order[:BLOCK]}, {ref: children[ref] for ref in order[BLOCK:]}
    ref = f"more:{group}#{block}"
    rest[ref] = (group, block, left)
    members = [member for child, item in left.items() if not item["files"]
               for member in (child, *item.get("members", ()))]
    shown[ref] = {**_node({"ref": ref, "type": "more"}, f"altri {len(left)}", "confirmed"),
                  "files": [path for item in left.values() for path in item["files"]],
                  **({"members": members} if members else {})}
    return shown


def _joined(inside: dict, start: str, stop: str) -> bool:
    """Whether the arcs `inside` (end to the ends it reaches) lead from `start` to `stop`."""
    todo, met = [start], {start}
    while todo:
        end = todo.pop()
        if end == stop:
            return True
        todo += [item for item in inside[end] if item not in met]
        met.update(inside[end])
    return False


def _open(envelope: dict, groups, symbols_of) -> tuple:
    """The first grouping's nodes with `groups` open in place (`view`): grouping, entities, files, the nodes in view,
    the node that shows each end (`owner`), the open group holding each node (`holder`), the open groups in the
    order they opened, and the files read by `symbols_of`. A group holding more than BLOCK opens on a block of them
    and a node «altri N» (`_block`), which opens on the next block in its place; its children are the group's. An
    asked id the graph does not show, or that holds nothing to open, is refused, ending with the id."""
    grouping, entities, files, nodes, owner = _top(envelope)
    holder, top, opened, read, under, rest = dict.fromkeys(nodes), {ref: ref for ref in nodes}, [], {}, {}, {}
    pending = sorted(set(groups))
    while pending:
        ref = next((item for item in pending if item in nodes), pending[0])
        node = nodes.pop(ref, None)
        if node is None or not (node["files"] or node.get("members")):
            raise ValueError(f"the graph shows no group to open: {json.dumps(ref, ensure_ascii=False)}")
        pending.remove(ref)
        if node["kind"] == "more":
            group, block, children = rest.pop(ref)
            children, parent = _block(group, block + 1, children, rest), holder[ref]
        else:
            if node["kind"] == "file":
                path = node["files"][0]
                read[path] = symbols_of(path)
                under.update(_nested(ref, read[path], entities))
            if node["kind"] in ("file", "symbol"):
                children = under.get(ref, {})
            elif node["kind"] == "group":  # «Tecnologie»: the technologies it holds
                children = {member: _node(entities[member], entities[member]["name"]) for member in node["members"]}
            else:
                children = _contents(top[ref], node["files"], entities)
            children, parent = _block(ref, 1, children, rest), ref
            opened.append({"id": ref, "name": node["name"], "kind": node["kind"], "parent": holder[ref],  # a module its stack
                           **{key: node[key] for key in ("projects", "other_dependencies") if key in node}})
        for child, item in children.items():
            nodes[child], holder[child], top[child] = item, parent, top[ref]
            owner.update((f"file:{path}", child) for path in item["files"])
            owner.update((member, child) for member in (child, *item.get("members", ())))
    return grouping, entities, files, nodes, owner, holder, opened, read


def symbols(envelope: dict, ref: str, symbols_of) -> dict:
    """The inspector's data of the file `ref`, open or not: its symbols with their lines, card freshness and purpose
    (and the type its flows give one), and the calls that start or end at one of them with their sites
    (`_calls`), read for that file only by `symbols_of(path)` (`visual.file_symbols`)."""
    entities = {item["ref"]: item for item in envelope["entities"]}
    if entities.get(ref, {}).get("type") != "file":
        raise ValueError(f"the run has no file {ref!r}")
    found = symbols_of(entities[ref]["path"])
    shown = [{"id": item["ref"], "name": item["name"], "lines": item.get("lines"), "freshness": item.get("freshness"),
              "responsibility": item.get("description") or "", "node_type": entities.get(item["ref"], {}).get("node_type")}
             for item in found["entities"] if item["type"] == "symbol"]
    calls = _calls({entities[ref]["path"]: found})
    return {"file": ref, "symbols": sorted(shown, key=lambda item: ((item["lines"] or [0])[0] or 0, item["name"])),
            "calls": _edges(calls, {end for item in calls for end in (item["source"], item["target"])}, {}),
            "gaps": found["gaps"]}


def _calls(read: dict) -> list:
    """The resolved calls read for some files (`read`, path to `visual.file_symbols`), each once, as relations between
    the innermost symbol whose lines hold each end (the call's site, the callee's first line) or, at a file's top level
    or in a file not read, that file; a call with no symbol at either end is the files' own and left out."""
    spans = {path: [(item["lines"], item["ref"]) for item in found["entities"]
                    if item["type"] == "symbol" and None not in item["lines"]] for path, found in read.items()}
    starts = {key: line for found in read.values() for key, line in found["declarations"].items()}

    def end(path: str, line: int | None) -> str:
        held = [(stop - start, ref) for (start, stop), ref in spans.get(path, []) if line is not None and start <= line <= stop]
        return min(held)[1] if held else f"file:{path}"

    out = []
    calls = {(call["id"], call["target_id"], call.get("confidence"), call.get("resolver")): call
             for found in read.values() for call in found["calls"]}
    for call in calls.values():
        source, target = end(call["file"], call["line"]), end(call["target_id"].split("::")[0], starts.get(call["target_id"]))
        if source != target and (source.startswith("symbol:") or target.startswith("symbol:")):
            status = call.get("confidence") or "confirmed"
            evidence = {"path": call["file"], "line": call["line"]}
            if call.get("conflict") or status in ("observed", "sampled"):
                evidence.update({key: call[key] for key in ("resolver", "conflict") if key in call})
            out.append({"ref": f"calls:{source}->{target}", "kind": "calls", "source": source, "target": target, "status": status,
                        "counts": {"calls": 1}, "evidence": [evidence], **({"conflict": True} if call.get("conflict") else {})})
    return out


def _nested(ref: str, found: dict, entities: dict) -> dict:
    """The symbols of the file `ref` (`visual.file_symbols`) as nodes, under what holds each: the innermost other
    symbol whose lines hold its own (not the same lines), else the file; each with its lines, freshness and every
    symbol it holds (`members`). The lines are the outline's, whatever the language."""
    items = {item["ref"]: item for item in found["entities"] if item["type"] == "symbol"}
    spans = {key: tuple(item["lines"]) for key, item in items.items() if None not in (item.get("lines") or [None])}

    def holds(outer: str, inner: str) -> bool:
        return outer in spans and inner in spans and spans[outer] != spans[inner] \
            and spans[outer][0] <= spans[inner][0] and spans[inner][1] <= spans[outer][1]

    under: dict[str, dict] = {}
    for key, item in items.items():
        held = [other for other in spans if holds(key, other)]
        holders = [other for other in spans if holds(other, key)]
        parent = min(holders, key=lambda other: (spans[other][1] - spans[other][0], other)) if holders else ref
        under.setdefault(parent, {})[key] = {**_node({**entities.get(key, {}), **item}, item["name"]),
                                             "lines": item.get("lines"), "freshness": item.get("freshness"),
                                             **({"members": held} if held else {})}
    return under


def _node(item: dict, name: str, status: str | None = None) -> dict:
    return {"id": item["ref"], "name": name, "kind": item["type"], "location": item.get("location", "internal"),
            "node_type": item.get("node_type"), "mark": item.get("mark"), "status": item.get("status") or status,
            "provenance": item.get("provenance"), "responsibility": item.get("description") or "",
            "evidence": item.get("evidence", []), "files": []}


def _top(envelope: dict) -> tuple[str, dict, list, dict, dict]:
    """How the graph groups files when it opens (`modules` or `directories`), the entities (with the directories it
    groups by), the files, the groups as nodes with their files, and the group of each file. A framework, a library or
    a tool is a node under «Tecnologie» (`group:technologies`), a group beside the others that does not choose the
    grouping and opens into them; each group also carries the frameworks and libraries its files declare
    (`projects`), with the declaring sites: the closed form of its arrows to them."""
    entities = {item["ref"]: item for item in envelope["entities"]}
    files = sorted(ref for ref, item in entities.items() if item["type"] == "file")
    # a virtual module is the tree no build names, not a group of its own: its files show by their directories;
    # a store is a member of a node, not a group (the system map's «nodo»), and holds no file
    # a technology is a member of the group «Tecnologie», not a group in itself
    groups = [ref for ref, item in entities.items() if item["type"] not in (*STRUCTURE, "virtual", "store", "technology")]
    # an external node holds no file, nor does «Tecnologie»: neither chooses the grouping, and both are drawn beside
    # the groups at either one
    outside = [ref for ref in groups if entities[ref].get("location") == "external" or entities[ref]["type"] == "group"]
    owner: dict[str, str] = {}
    if len(groups) - len(outside) >= 2:
        grouping = "modules"
        sizes = Counter(item["group"] for item in envelope["memberships"] if item["group"] in groups)
        for item in envelope["memberships"]:  # a file in nested modules belongs to the smallest
            if item["group"] in sizes and item["member"] in entities and entities[item["member"]]["type"] == "file":
                current = owner.get(item["member"])
                if current is None or sizes[item["group"]] < sizes[current]:
                    owner[item["member"]] = item["group"]
    else:
        grouping = "directories"
        for ref in files:
            parent = PurePosixPath(entities[ref]["path"]).parent.as_posix()
            owner[ref] = f"directory:{parent}"
            if owner[ref] not in entities:
                entities[owner[ref]] = {"ref": owner[ref], "type": "directory", "name": parent, "path": parent}
        groups = sorted(set(owner.values())) + outside
    nodes = {ref: _node(entities[ref], entities[ref]["name"] if ref in outside or grouping == "modules" else entities[ref]["path"],
                        "confirmed" if grouping == "directories" else None) for ref in groups}
    for ref in files:
        if ref in owner:
            nodes[owner[ref]]["files"].append(entities[ref]["path"])
    for item in envelope["memberships"]:  # «Tecnologie» holds the technologies, which show by it until it is open
        if item["group"] in nodes and entities.get(item["member"], {}).get("type") == "technology":
            nodes[item["group"]].setdefault("members", []).append(item["member"])
            owner[item["member"]] = item["group"]
    _stack(envelope["technologies"], entities, nodes, owner)
    return grouping, entities, files, nodes, owner


TILES = ("framework", "library")  # the registry's categories a module shows; a service is a node, a tool neither


def _stack(technologies: list, entities: dict, nodes: dict, owner: dict) -> None:
    """Each group's stack, as the stack step has it (the envelope's `technologies`): the frameworks and libraries of
    the registry one of its files declares, by a package's line or by a file's name (`projects`: the registry id,
    which the mark route takes, name, kind `project`, its `category` and the declaring sites), and the count of its
    other declared packages, known to the registry or not, neither a tile nor a service, which has its node
    (`other_dependencies`). One a line only mentions is not listed."""
    projects: dict[str, dict] = {ref: {} for ref, node in nodes.items()
                                 if node["location"] != "external" and node["kind"] != "group"}
    others: dict[str, set] = {ref: set() for ref in projects}
    shown = {item["id"] for item in technologies if item["category"] in (*TILES, "service")}
    for item in technologies:
        for site in item["evidence"] if item["category"] in TILES else ():
            ref = owner.get(f"file:{site['path']}")
            if ref in projects:
                found = projects[ref].setdefault(item["id"], {"id": item["id"], "name": item["name"], "kind": "project",
                                                              "category": item["category"], "mark": item["id"],
                                                              "evidence": []})
                if site not in found["evidence"]:
                    found["evidence"].append(site)
    for entity in entities.values():
        for item in entity.get("libraries") or ():
            ref = owner.get(f"file:{item['path']}")
            if ref in projects and item.get("id") not in shown:
                others[ref].add((item["ecosystem"], item["name"].casefold()))
    for ref, found in projects.items():
        for item in found.values():
            item["evidence"].sort(key=lambda site: (site["path"], site["line"] or 0))
        nodes[ref]["projects"] = sorted(found.values(), key=lambda item: (item["name"].casefold(), item["id"]))
        nodes[ref]["other_dependencies"] = len(others[ref])


def _unassigned(entities: dict, files: list, owner: dict) -> dict:
    alone = [entities[ref]["path"] for ref in files if ref not in owner]
    return {"count": len(alone), "areas": Counter(PurePosixPath(path).parent.as_posix() for path in alone).most_common(8)}


def _edges(relations: list, nodes: dict, owner: dict) -> list:
    """The relations between `nodes`, each end lifted to the node that shows it now (`owner`: a file's group, a
    symbol's outermost shown holder): one between two files counts once, with the pair as its site; any
    other keeps its counts and sites (a module's, a use, a symbol's call), a deduced link its key too; an uncertain one
    is its own edge. Each edge lists the `ref` of every relation it sums up (`relations`), however many sites it
    keeps: the way back to the original arcs."""
    edges: dict[tuple, dict] = {}
    for relation in relations:
        if relation["kind"] in ("contains", "defines"):
            continue
        source, target = (owner.get(relation[end], relation[end]) for end in ("source", "target"))
        if source not in nodes or target not in nodes or source == target:
            continue
        key = {"key": relation["key"]} if "key" in relation else {}  # a deduced link keeps its count, sites and key
        status = relation["status"]
        # Older envelopes kept the marker only on individual sites.
        conflict = relation.get("conflict") or any(site.get("conflict") for site in relation.get("evidence", []))
        pair = (not key and not conflict and status not in ("observed", "sampled") and
                relation["source"].startswith("file:") and relation["target"].startswith("file:"))
        counts = {relation["kind"]: 1} if pair else relation.get("counts") or {relation["kind"]: 1}
        site = {"path": relation["source"].removeprefix("file:"), "line": None,
                "target": relation["target"].removeprefix("file:")} if pair else None
        separate = status if status in ("uncertain", "observed", "sampled") else ""
        if conflict:
            separate = status + " conflict"
        edge = edges.setdefault((source, target, separate), {
            "id": f"{source}->{target}" + (f" {separate}" if separate else ""), "source": source, "target": target,
            "counts": {}, "status": relation["status"], "evidence": [], "relations": [],
            **({"conflict": True} if conflict else {})})
        if relation.get("ref") and relation["ref"] not in edge["relations"]:
            edge["relations"].append(relation["ref"])
        for kind, count in counts.items():
            edge["counts"][kind] = edge["counts"].get(kind, 0) + count
        sites = relation.get("evidence", []) if site is None else [site]
        edge["evidence"].extend([{"kind": relation["kind"], **item, **key} for item in sites][:EVIDENCE - len(edge["evidence"])])
    return sorted(edges.values(), key=lambda edge: edge["id"])


def _base(files: list) -> str:
    """The deepest directory that holds all `files`; '' is the root of the checkout."""
    common = PurePosixPath(files[0]).parent.parts
    for path in files[1:]:
        parts = PurePosixPath(path).parent.parts
        size = 0
        while size < min(len(common), len(parts)) and common[size] == parts[size]:
            size += 1
        common = common[:size]
    return "/".join(common)


def _contents(top: str, files: list, entities: dict) -> dict:
    """What a node holding `files` opens into: each file in the deepest directory holding them all, and each
    directory below that one, named down to the deepest directory holding its own files. A directory's id carries the
    first group `top` it belongs to, since a directory can hold the files of several modules."""
    base = _base(files)
    held: dict[str, list] = {}
    for path in files:
        head, below, _ = (path[len(base) + 1:] if base else path).partition("/")
        held.setdefault((f"{base}/{head}" if base else head) if below else path, []).append(path)
    children = {}
    for key, paths in held.items():
        if paths == [key]:  # a file: a directory never has the path of one
            children[f"file:{key}"] = {**_node(entities[f"file:{key}"], entities[f"file:{key}"]["name"], "confirmed"),
                                       "files": paths}
        else:
            directory = _base(paths)
            children[f"{top}#{directory}"] = {**_node({"ref": f"{top}#{directory}", "type": "directory"},
                                                      directory[len(base) + 1:] if base else directory, "confirmed"),
                                              "files": paths}
    return children
