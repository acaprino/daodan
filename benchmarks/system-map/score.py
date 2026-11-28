#!/usr/bin/env python3
"""Score a system map against a reference made by hand, and a recognition of externals against a list.

    python score.py map MAP.json EXPECTED.json
    python score.py externals BRIEF.json EXPECTED.json [registry|stack-analyser|both]
    python score.py stable MAP1.json MAP2.json
    python score.py system MAP.json EXPECTED-system.json FILES.txt
    python score.py whole TAG
    python score.py runs FROM-SCRATCH UNCHANGED ONE-MODULE

MAP.json is what `system_map.load` returns, optionally with `refused_arrows` from the
record reports. A reference node with code is found when a proposed node shares at least
half of the union of their files and store keys (Jaccard index). A node without code is
found when a proposed node in the same position cites one of its evidence files; an
unseen node cites none, so a proposed unseen node of the same type finds it.
A reference flow is found when one proposed flow holds two thirds of its nodes, as
matched. Names never count: the project confirms names, the score only shapes.

`system` compares the whole system against a reference of `expected/*-system.json` on the
snapshot's files (FILES.txt, one path per line, the same for both sides), one node to one:
an external is found by the same `registry` id, one without it (an actor, a device) and an
unseen node by position and type, counted apart. On the services of others found, `services`
counts the same `family`, a closed value, and only whether `role` and `mode` are there. `reach` counts the parts of depth 0 and 1 a
map points into without carrying them: a node that names one file of a part, a service of
others by its name.

`whole` reads what the one job of `modal_map.py whole` leaves under TAG (`results/system/TAG`, brought from the
volume) and gives the table of the plan of the unified analysis, section 4: per case, one row per model, scope
and rules. Each run is a folder `TAG/LABEL/` with `summary.json`, and, where the run got that far, `map.json`,
`files.txt` and `engine-report.json`; what is per case lies in `TAG/cases/CASE/`: `archive.json` (the
counts `code_archive.py` writes beside the archive), `candidates.json` and `files.txt` (the entry candidates and
the snapshot's files after the engine pass, measured here against `expected/CASE-system.json` with
`entries.py measure`, so a private reference never goes to Modal), `engine.json`, and `paths.json` and `search.json`
(the verify of the path cards, `embed_probe.py rank`). A
column whose file is not there, or whose reference is not, says `non misurato` and why; it is never a zero.
`runs` puts three runs of one project side by side (spec of the pipeline, 7.4; task 2b of the plan): from scratch,
unchanged, and after a change to one module. Each folder holds what the run left: `pipeline-events.jsonl`, the
`container-runs.jsonl` records anywhere under it, and `links.json` (`found` and `of`: the expected links the run
found, from `possible.py`). Per run: seconds from the first event to the last, restores (the `node-restore` and
`prepare` phases), analyzer starts, app starts, and the links. CPU, peak memory and temporary space are in no event:
`non misurato`. A run that costs less than the first and finds fewer links is marked, never counted as a gain.

The layout of those files is provisional until `modal_map.py whole` writes it. The other states: `ingresso omesso` (the archive left files out: what the program needs to start may be
missing), `passo fallito` (the engine pass timed out or failed, the numbers after it are of what ran) and
`zero trovati` (measured, and found none).
"""
from __future__ import annotations

import json
import os
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path


def _files(node: dict) -> set[str]:
    return (set(node.get("files") or []) | {e.split("#")[0].split(":")[0] for e in node.get("evidence") or []}
            | {m for m in node.get("members") or [] if m.startswith("store:")})


def _jaccard(a: set[str], b: set[str]) -> float:
    return len(a & b) / len(a | b) if a | b else 0.0


def _likeness(proposed: dict, reference: dict) -> float:
    """How well a proposed node stands for a reference node; 0 when it does not."""
    position = reference.get("position", "internal")
    if position == "internal":
        share = _jaccard(_files(proposed), _files(reference))
        return share if share >= 0.5 else 0.0
    if proposed.get("position", "internal") != position:
        return 0.0
    if not (wanted := _files(reference)):
        return 1.0 if proposed.get("type") == reference.get("type") else 0.0
    return len(wanted & _files(proposed)) / len(wanted)


def _arrows(proposed: dict) -> dict:
    states = [a.get("status") for f in proposed["flows"] for a in f.get("arrows", [])]  # a reference used as a proposal has none
    refused = proposed.get("refused_arrows", states.count("refused"))
    total = states.count("proved") + states.count("declared") + refused
    return {"proved": states.count("proved"), "declared": states.count("declared"), "refused": refused,
            "refused_share": round(refused / total, 3) if total else 0.0}


def score_map(proposed: dict, expected: dict) -> dict:
    match = {}
    for node in expected["nodes"]:
        best = max(proposed["nodes"], key=lambda n: _likeness(n, node), default=None)
        if best is not None and _likeness(best, node) > 0:
            match[node["name"]] = best["name"]
    flows_found = []
    for flow in expected["flows"]:
        wanted = [match.get(n) for n in flow["nodes"]]
        if any(sum(1 for n in wanted if n and n in f["nodes"]) * 3 >= len(flow["nodes"]) * 2 for f in proposed["flows"]):
            flows_found.append(flow["name"])
    return {"nodes": {"found": len(match), "of": len(expected["nodes"]),
                      "missing": [n["name"] for n in expected["nodes"] if n["name"] not in match]},
            "flows": {"found": len(flows_found), "of": len(expected["flows"]),
                      "missing": [f["name"] for f in expected["flows"] if f["name"] not in flows_found]},
            "arrows": _arrows(proposed), "coverage": proposed.get("coverage", {})}


# ---------------------------------------------------------------- the whole system against its reference

def _key(name) -> str:
    plain = unicodedata.normalize("NFKD", str(name or "").strip())
    return "".join(c for c in plain if not unicodedata.combining(c)).casefold()


def _share(part: int, whole: int) -> float:
    return round(part / whole, 3) if whole else 0.0


def _count(found: int, of: int) -> dict:
    return {"found": found, "of": of}


def _units(expected: dict, files: list[str]):
    """What a node stands for, cut as the reference cuts it: a folder is its files in the snapshot, a symbol stays
    a symbol only where the reference puts symbols of its file in two nodes, a store key drops the store's name when
    its last part is unique in the reference; a file out of the snapshot (a generated one) counts for nothing."""
    snapshot, folders = set(files), defaultdict(set)
    for path in files:
        parts = path.split("/")
        for k in range(len(parts)):
            folders["/".join(parts[:k])].add(path)
    holders = defaultdict(set)
    for node in expected["nodes"]:
        for member in node.get("members") or []:
            if "::" in member:
                holders[member.partition("::")[0]].add(_key(node["name"]))
    split = {path for path, nodes in holders.items() if len(nodes) > 1}
    lasts = Counter(m.rsplit("/", 1)[-1] for m in {m for n in expected["nodes"] for m in n.get("members") or []
                                                   if m.startswith("store:")})

    def one(member: str) -> set[str]:
        if member.startswith("store:"):
            last = member.rsplit("/", 1)[-1]
            return {"store:" + last if lasts[last] == 1 else member}
        path, _, symbol = member.partition("::")
        path = path.strip().removeprefix("./").strip("/")
        if path in snapshot:
            return {f"{path}::{symbol}" if symbol and path in split else path}
        return set(folders.get("" if path == "." else path, ()))

    def units(node: dict) -> set[str]:
        members = node.get("members") or []
        if node.get("files"):  # a loaded node: its folders are expanded already, its symbols are files
            named = {m.partition("::")[0] for m in members if "::" in m}
            members = ([f for f in node["files"] if not (f in split and f in named)]
                       + [m for m in members if "::" in m or m.startswith("store:")])
        return {u for m in members if not m.startswith("module:") for u in one(m)}

    return units, folders


def _alike(proposed: dict, reference: dict, have: set[str], want: set[str]) -> float:
    """`_likeness` over the units; an external with a registry id is found by the same id, and only by it."""
    if reference.get("registry") or proposed.get("registry"):
        return 1.0 if proposed.get("registry") == reference.get("registry") else 0.0
    if reference.get("position", "internal") == "internal" and not 0.5 <= len(have) / max(len(want), 1) <= 2:
        return 0.0  # the Jaccard index cannot reach one half
    return _likeness({"files": have, "position": proposed.get("position", "internal"), "type": proposed.get("type")},
                     {"files": want, "position": reference.get("position", "internal"), "type": reference.get("type")})


def _assign(pairs: list[tuple[float, int, int]]) -> dict[int, int]:
    """One to one, from the highest likeness: first index to second."""
    match, taken = {}, set()
    for _, first, second in sorted(pairs, key=lambda p: (-p[0], p[1], p[2])):
        if first not in match and second not in taken:
            match[first] = second
            taken.add(second)
    return match


def _node_match(proposed: list[dict], expected: list[dict], units) -> dict[int, int]:
    have, want = [units(n) for n in proposed], [units(n) for n in expected]
    sharing = defaultdict(set)
    for j, found in enumerate(have):
        for unit in found:
            sharing[unit].add(j)
    pairs = []
    for i, node in enumerate(expected):
        if node.get("position", "internal") == "internal":
            candidates = {j for u in want[i] for j in sharing[u]}
        else:
            candidates = range(len(proposed))
        pairs += [(like, i, j) for j in candidates if (like := _alike(proposed[j], node, have[j], want[i])) > 0]
    return _assign(pairs)


def _tree(nodes: list[dict]) -> tuple[list[int], list[int | None], list[int]]:
    """Per node: its depth along `inside`, its parent and its ancestor of depth 1 (itself above that)."""
    index = {_key(n["name"]): i for i, n in enumerate(nodes)}
    depths, parents, lifts = [], [], []
    for i, node in enumerate(nodes):
        chain = [i]
        while (up := index.get(_key(nodes[chain[-1]].get("inside")))) is not None and len(chain) <= 20:
            chain.append(up)
        depths.append(len(chain) - 1)
        parents.append(chain[1] if len(chain) > 1 else None)
        lifts.append(chain[-2] if len(chain) > 1 else i)
    return depths, parents, lifts


def _single_folder(found: set[str], folders: dict) -> bool:
    if not found or any("::" in u or u.startswith("store:") for u in found):
        return False
    common = os.path.commonprefix([u.split("/")[:-1] for u in found])
    return found == folders.get("/".join(common))


def _flow_paths(flow, entries, effects):
    """Nodes on a standing directed route from a matched entry to a matched effect, and its two ends."""
    members = {_key(name) for name in flow["nodes"]}
    forward, backward = defaultdict(set), defaultdict(set)
    for arrow in flow.get("arrows", ()):
        source, target = _key(arrow.get("from")), _key(arrow.get("to"))
        if (arrow.get("status") in ("proved", "declared") and arrow.get("fresh") is not False
                and source in members and target in members):
            forward[source].add(target)
            backward[target].add(source)

    def reachable(starts, graph):
        # Follow at least one arrow. Listing the same isolated node at both ends proves no path.
        pending = [node for start in starts for node in graph[start]]
        seen = set()
        while pending:
            node = pending.pop()
            if node not in seen:
                seen.add(node)
                pending.extend(graph[node] - seen)
        return seen

    downstream, upstream = reachable(entries, forward), reachable(effects, backward)
    starts, finishes = entries & upstream, effects & downstream
    return downstream & upstream | starts | finishes, starts, finishes


def _flow_scores(proposed: dict, expected: dict, match: dict[int, int], lifts: list[int]) -> dict:
    """Match once by shape alone, then separately by directed entry-to-effect paths on proved or declared arrows."""
    index = {_key(n["name"]): i for i, n in enumerate(expected["nodes"])}
    names = {i: _key(proposed["nodes"][j]["name"]) for i, j in match.items()}
    back = {_key(proposed["nodes"][j]["name"]): i for i, j in match.items()}
    held = [{names[index[_key(n)]] for n in f["nodes"] if index.get(_key(n)) in names} for f in expected["flows"]]
    holds = [{_key(n) for n in f["nodes"]} for f in proposed["flows"]]
    pairs = [(len(h & mine) / len(flow["nodes"]), i, j) for i, (flow, h) in enumerate(zip(expected["flows"], held))
             for j, mine in enumerate(holds)
             if len(h & mine) * 3 >= len(flow["nodes"]) * 2 and len(h & mine) * 2 >= len(mine) > 0]
    shape = _assign(pairs)
    paths, candidates = {}, []
    for _, i, j in pairs:
        flow = expected["flows"][i]
        endpoints = [{names[index[_key(item["node"])]] for item in flow.get(field, ())
                      if index.get(_key(item["node"])) in names} for field in ("entries", "effects")]
        connected, starts, finishes = _flow_paths(proposed["flows"][j], *endpoints)
        matched = len(held[i] & connected)
        if starts and finishes and matched * 3 >= len(flow["nodes"]) * 2:
            candidates.append((matched / len(flow["nodes"]), i, j))
            paths[i, j] = {"entries": starts, "effects": finishes}
    found = _assign(candidates)
    by_type, ends = defaultdict(lambda: [0, 0]), {"entries": [0, 0], "effects": [0, 0]}
    for i, flow in enumerate(expected["flows"]):
        for kind in flow.get("types") or []:
            by_type[kind][0] += i in found and kind in proposed["flows"][found[i]].get("types", ())
            by_type[kind][1] += 1
        for end, count in ends.items():
            for item in flow.get(end) or []:
                at = names.get(index.get(_key(item.get("node"))))
                count[0] += i in found and at in paths[i, found[i]][end]
                count[1] += 1
    raised = [{lifts[back[n]] for n in mine if n in back} for mine in holds]
    best = [max((_jaccard({lifts[index[_key(n)]] for n in f["nodes"] if _key(n) in index}, r) for r in raised),
                default=0.0) for f in expected["flows"]]
    correct_types = sum(len(set(expected["flows"][i].get("types", ())) & set(proposed["flows"][j].get("types", ())))
                        for i, j in found.items())
    proposed_types = sum(len(set(flow.get("types", ()))) for flow in proposed["flows"])
    return {"flows": {"found": len(found), "of": len(expected["flows"]),
                      "missing": [f["name"] for i, f in enumerate(expected["flows"]) if i not in found],
                      "by_type": {k: _count(*v) for k, v in sorted(by_type.items())}},
            "flows_by_nodes": _count(len(shape), len(expected["flows"])),
            "flow_type_precision": {**_count(correct_types, proposed_types), "share": _share(correct_types, proposed_types)},
            "flows_depth_1": {"share": _share(sum(best), len(best)) if best else 0.0, "of": len(best)},
            **{end: _count(*count) for end, count in ends.items()}}


def _reached(mine: list[dict], nodes: list[dict], match: dict[int, int], units, depths: list[int], parents: list,
             counted: list[int]) -> dict:
    """The parts of depth 0 and 1 the map points into without carrying them. A proposed node that stands for no
    reference node points at the deepest internal node holding most of its files (one file of a part reaches the
    part), a node of others at the one with its proper name. Flows are not paired this way: through coarse nodes
    one proposed flow passes for many, and the pairs come out wrong."""
    want = [units(n) for n in nodes]
    inner = [i for i, n in enumerate(nodes) if n.get("position", "internal") == "internal"]
    named = {_key(name): i for i in sorted(set(range(len(nodes))) - set(inner), reverse=True)
             for name in (nodes[i]["name"], nodes[i].get("registry")) if name}
    pointed = set(match)
    for j, node in enumerate(mine):
        if j in match.values():
            continue
        if node.get("position", "internal") != "internal":
            pointed.add(named.get(_key(node["name"])))
            continue
        have = units(node)
        holders = [i for i in inner if len(have & want[i]) * 2 > len(have)]
        if holders:
            pointed.add(max(holders, key=lambda i: (depths[i], -len(want[i]), -i)))
    above = set()
    for i in pointed - {None}:
        while i is not None and i not in above:
            above.add(i)
            i = parents[i]
    top = [i for i in counted if depths[i] <= 1]
    return _count(sum(i in above for i in top), len(top))


def score_system(proposed: dict, expected: dict, files: list[str]) -> dict:
    """The whole-system map against its reference (README, «Riferimenti dell'intero sistema»), on the snapshot's
    files. Names, `what`, `proof`, `routes`, `packages`, `gaps`, areas, `cite` and `has` never count."""
    units, folders = _units(expected, files)
    nodes, mine = expected["nodes"], proposed["nodes"]
    match = _node_match(mine, nodes, units)
    depths, parents, lifts = _tree(nodes)
    apart = [i for i, n in enumerate(nodes) if n.get("position", "internal") != "internal" and not n.get("registry")]
    counted = [i for i in range(len(nodes)) if i not in set(apart)]
    by_depth, by_type = defaultdict(lambda: [0, 0]), defaultdict(lambda: [0, 0])
    for i in counted:
        for bucket in (by_depth["0-1" if depths[i] <= 1 else "2" if depths[i] == 2 else "3+"], by_type[nodes[i]["type"]]):
            bucket[0] += i in match
            bucket[1] += 1
    same = sum(mine[j].get("type") == nodes[i].get("type") for i, j in match.items())
    with_parent = [i for i, p in enumerate(parents) if p is not None]
    both = [i for i in with_parent if i in match and parents[i] in match]
    kept = sum(_key(mine[match[i]].get("inside")) == _key(mine[match[parents[i]]]["name"]) for i in both)
    services = [(nodes[i], mine[j]) for i, j in match.items() if nodes[i].get("family")]
    return {"nodes": {"found": sum(i in match for i in counted), "of": len(counted),
                      "by_depth": {k: _count(*by_depth[k]) for k in ("0-1", "2", "3+")},
                      "by_type": {k: _count(*v) for k, v in sorted(by_type.items())},
                      "missing": [nodes[i]["name"] for i in counted if i not in match]},
            "apart": _count(sum(i in match for i in apart), len(apart)),
            "precision": {"found": len(match), "of": len(mine), "share": _share(len(match), len(mine))},
            "single_folder": _share(sum(_single_folder(units(n), folders) for n in mine), len(mine)),
            "type": {"same": same, "of": len(match), "share": _share(same, len(match))},
            "inside": {"kept": kept, "of_found": len(both), "of": len(with_parent), "share": _share(kept, len(both))},
            "services": {"of": len(services), "family": sum(m.get("family") == n["family"] for n, m in services),
                         **{field: sum(bool(m.get(field)) for _, m in services) for field in ("role", "mode")}},
            **_flow_scores(proposed, expected, match, lifts), "arrows": _arrows(proposed),
            "reach": _reached(mine, nodes, match, units, depths, parents, counted)}


def stability(first: dict, second: dict) -> dict:
    """Nodes of two runs that are the same thing, compared as `score_map` compares a reference node."""
    same, taken = 0, set()
    for node in first["nodes"]:
        best = max((n for n in second["nodes"] if n["name"] not in taken), key=lambda n: _likeness(n, node), default=None)
        if best is not None and _likeness(best, node) > 0:
            same += 1
            taken.add(best["name"])
    of = max(len(first["nodes"]), len(second["nodes"]))
    return {"same": same, "of": of, "share": round(same / of, 3) if of else 0.0}


SOURCES = {"registry": {"registry"}, "stack-analyser": {"stack-analyser"}, "both": {"registry", "stack-analyser"}}


def score_externals(recognized: dict, expected: dict, source: str | None = None) -> dict:
    """Recall over the named externals; `also` lists what the project uses unnamed: neither found nor wrong."""
    found = {e["id"] for e in recognized["externals"] if source is None or SOURCES[source] & set(e.get("from", []))}
    wanted, also = set(expected["externals"]), set(expected.get("also", []))
    return {"recall": round(len(found & wanted) / len(wanted), 3) if wanted else 0.0, "found": sorted(found & wanted),
            "missed": sorted(wanted - found), "wrong": sorted(found - wanted - also)}


EXPECTED_FOLDER = Path(__file__).resolve().parent / "expected"
CASE_FILES = {"paths": ("paths.json", "the verify of the path cards"), "search": ("search.json", "embed_probe.py rank")}


def _read(path: Path):
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None


def _measured(value) -> dict:
    return {"state": "misurato", "value": value}


def _unmeasured(cause: str) -> dict:
    return {"state": "non misurato", "cause": cause}


def _lines(path: Path) -> list[str]:
    return [line.strip().replace("\\", "/") for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _entries_measure(candidates: dict, reference: dict, files: list[str]) -> dict:
    """`entries.py measure`, loaded by its path: the core has an `entries` module of its own."""
    import importlib.util
    import types
    spec = importlib.util.spec_from_file_location("system_map_entries", Path(__file__).resolve().parent / "entries.py")
    module = importlib.util.module_from_spec(spec)
    before = list(sys.path)  # the module puts its folder first on the path: not for the modules after it
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path[:] = before
    # its `import score` may have found another `score` module of the process (project-model's has no `_units`)
    module.score = types.SimpleNamespace(_units=_units, _key=_key)
    return module.measure(candidates, reference, files)


def _engine_cell(engine: dict | None) -> dict:
    """The engine pass of a run or of a case job (`modal_map.py::_engine_pass`): its languages, or why it failed."""
    why = (None if engine is None else "the engine pass timed out" if engine.get("timed_out")
           else f"the engine pass exited with {engine.get('exit')}" if engine.get("exit") not in (0, 1)
           else "the engine pass wrote no report" if "languages" not in engine else None)  # a crash exits with 1 too
    return (_unmeasured("no state of the engine pass was kept") if engine is None else
            {"state": "passo fallito", "cause": why + (f": {engine['stderr'][-400:]}" if engine.get("stderr") else "")}
            if why else _measured(engine["languages"]))


def _case_columns(folder: Path, reference_file: Path) -> dict:
    """What is of a case and not of a run: what the archive left out and the secrets masked in it (`archive.json`),
    the entry candidates measured against the reference, the path cards and the search."""
    columns = {}
    archive = _read(folder / "archive.json")  # `code_archive.py`'s counts, per repository
    if archive is None:
        columns["input"] = _unmeasured("archive.json is not there: the job was given no counts of the archive")
        columns["secrets"] = _unmeasured("archive.json is not there: Secretlint's counts of the archive are not either")
    else:
        left = sum(counts["left"] for counts in archive.values())
        withheld = sum(len(counts["withheld"]) for counts in archive.values())
        columns["input"] = ({"state": "ingresso omesso", "left": left, "withheld": withheld} if left or withheld
                            else _measured("nothing left out"))
        columns["secrets"] = _measured({
            "masked_in_the_archive": sum(sum(counts["masked"].values()) for counts in archive.values()),
            "in_the_texts_sent_out": _unmeasured("the job does not collect them (task 8)")})
    candidates, listed = _read(folder / "candidates.json"), folder / "files.txt"
    reference = _read(reference_file)
    columns["entries"] = (_unmeasured("candidates.json is not there: the engine pass left nothing (engine.json says why)")
                          if candidates is None else
                          _unmeasured(f"{reference_file.name} is not there") if reference is None else
                          _unmeasured("files.txt of the case is not there") if not listed.is_file() else
                          _measured(_entries_measure(candidates, reference, _lines(listed))))
    for column, (name, source) in CASE_FILES.items():
        value = _read(folder / name)
        columns[column] = (_unmeasured(f"{name} is not there: {source} did not run in this job") if value is None
                           else _measured(value))
    columns["handlers"] = _unmeasured("there is no small set of controls and handlers confirmed by the owner")
    return columns


def _masked(run: Path) -> dict | None:
    """What the answers of the tools gave a run's model, as the streams of its two sessions keep them: how many
    answers, how many were read as JSON, and the secrets they report masked (`masked_secrets`, which
    `secret_mask.tool_result` puts in every answer). None when the run kept no stream."""
    streams = [run / name for name in ("stream.jsonl", "rules-stream.jsonl") if (run / name).is_file()]
    if not streams:
        return None
    counts = {"answers": 0, "read": 0, "masked_secrets": 0}
    for stream in streams:
        for line in stream.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                event = json.loads(line)
            except ValueError:
                continue
            blocks = ((event.get("message") or {}).get("content") or []) if isinstance(event, dict) else []
            for block in blocks:
                if not (isinstance(block, dict) and block.get("type") == "tool_result"):
                    continue
                content = block.get("content")
                text = ("".join(part.get("text", "") for part in content if isinstance(part, dict))
                        if isinstance(content, list) else str(content or ""))
                counts["answers"] += 1
                try:
                    answer = json.loads(text)
                except ValueError:
                    continue  # an error text, or one the host cut: not counted as read
                if isinstance(answer, dict):
                    counts["read"] += 1
                    counts["masked_secrets"] += int(answer.get("masked_secrets") or 0)
    return counts


def _usage(group: list) -> dict:
    """Tokens, seconds and turns of the sessions of a row's runs, by session (`rules`, `mapper`)."""
    tokens, seconds, turns = Counter(), Counter(), Counter()
    for item, _ in group:
        for name, session in (item.get("sessions") or {}).items():
            seconds[name] += session.get("seconds") or 0
            turns[name] += session.get("turns") or 0
            for key in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens"):
                tokens[key] += (session.get("usage") or {}).get(key) or 0
    return {"tokens": dict(tokens), "seconds": dict(seconds), "turns": dict(turns)}


def _row(group: list, folder: Path, reference_file: Path) -> dict:
    """One row of `whole`: the runs of a case, model, scope and rules, by repetition."""
    group = sorted(group, key=lambda item: item[0].get("rep", 0))
    summary, run = group[0]
    row = {"runs": len(group), **_case_columns(folder, reference_file), "engine": _engine_cell(summary.get("engine"))}
    proposed, files = _read(run / "map.json"), run / "files.txt"
    reference = _read(reference_file)
    if proposed is None:
        row["system"] = _unmeasured(summary.get("stopped") or summary.get("record_error") or "map.json is not there")
    elif reference is None or not files.is_file():
        row["system"] = _unmeasured(f"{reference_file.name} is not there" if reference is None else "files.txt is not there")
    else:
        found = score_system(proposed, reference, _lines(files))
        row["system"] = _measured(found) if found["nodes"]["found"] else {"state": "zero trovati", "value": found}
    # a run given the rules and links of another (`rules_from`) is not an independent one: it measures the mapper only
    maps = [mapped for mapped in (_read(folder_run / "map.json") for item, folder_run in group
                                  if not item.get("rules_from")) if mapped is not None]
    row["stable"] = (_measured(stability(maps[0], maps[1])) if len(maps) > 1
                     else _unmeasured("a second independent run is not there"
                                      + (" (the others were given the first one's rules)"
                                         if any(item.get("rules_from") for item, _ in group) else "")))
    costs = [item.get("cost_usd") for item, _ in group]
    row["cost"] = (_unmeasured("no run recorded its cost") if all(cost is None for cost in costs)
                   else _measured({"cost_usd": round(sum(cost or 0 for cost in costs), 6),
                                   "budget_stop": any(item.get("budget_stop") for item, _ in group),
                                   "prepared_seconds": [item.get("prepared_seconds") for item, _ in group],
                                   "usage": _usage(group)}))
    if row["secrets"]["state"] == "misurato":  # the archive's count is there: add what the models were given
        seen = [counts for counts in (_masked(folder_run) for _, folder_run in group) if counts is not None]
        row["secrets"]["value"]["in_the_texts_sent_out"] = (
            _unmeasured("no run kept a stream.jsonl: the texts the models were given are not there") if not seen
            else _measured({key: sum(counts[key] for counts in seen) for key in ("answers", "read", "masked_secrets")}
                           | {"runs": len(seen)}))
    return row


def whole(tag: Path, expected: Path = EXPECTED_FOLDER) -> dict:
    """`{case: {row: cells}}` from what a whole job left under `tag` (the module's docstring). A case the job ran
    with no model has the row `no model`: its archive, its candidates and its engine pass, no run."""
    runs = defaultdict(list)
    for file in sorted(Path(tag).glob("*/summary.json")):
        summary = json.loads(file.read_text(encoding="utf-8"))
        runs[summary["case"], f"{summary['model']} {summary['scope']} {summary['rules']}"].append((summary, file.parent))
    table = defaultdict(dict)
    for (case, name), group in sorted(runs.items()):
        table[case][name] = _row(group, Path(tag) / "cases" / case, Path(expected) / f"{case}-system.json")
    for folder in sorted(Path(tag, "cases").glob("*")):
        if folder.is_dir() and folder.name not in table:
            table[folder.name]["no model"] = {
                "runs": 0, **_case_columns(folder, Path(expected) / f"{folder.name}-system.json"),
                "engine": _engine_cell(_read(folder / "engine.json"))}
    return dict(table)


def _journal(folder: Path) -> list[dict]:
    """The events of the run in `folder`, each with its step's id, an old journal's too (`pipeline.events.read`)."""
    core = str(Path(__file__).resolve().parents[2] / "daodan" / "core")
    if core not in sys.path:
        sys.path.insert(0, core)
    from pipeline import events
    return events.read(folder / "pipeline-events.jsonl")[0]


def runs(folders: list[Path]) -> dict:
    """The runs of one project side by side, the first one the base (the module's docstring)."""
    from datetime import datetime
    rows = []
    for folder in map(Path, folders):
        events = _journal(folder)
        times = [datetime.strptime(event["at"], "%Y-%m-%dT%H:%M:%S.%fZ") for event in events]
        phases = [json.loads(line).get("phase") for file in sorted(folder.rglob("container-runs.jsonl"))
                  for line in file.read_text(encoding="utf-8").splitlines() if line.strip()]
        started = [event for event in events if event["kind"] == "analyzer.started"]
        links = _read(folder / "links.json")
        rows.append({"run": folder.name,
                     "seconds": _measured(round((max(times) - min(times)).total_seconds(), 1)) if times
                     else _unmeasured("pipeline-events.jsonl is not there or empty"),
                     "restores": _measured(sum(phase in ("node-restore", "prepare") for phase in phases)) if phases
                     else _unmeasured("no container-runs.jsonl under the folder"),
                     "analyzer_starts": _measured(sum(event["step"] == "link_calls" for event in started)) if events
                     else _unmeasured("pipeline-events.jsonl is not there or empty"),
                     "app_starts": _measured(sum(event.get("analyzer") == "app" for event in started)) if events
                     else _unmeasured("pipeline-events.jsonl is not there or empty"),
                     "cpu": _unmeasured("no event of the pipeline carries it"),
                     "peak_memory": _unmeasured("no event of the pipeline carries it"),
                     "temporary_space": _unmeasured("no event of the pipeline carries it"),
                     "links": _measured(links) if links else _unmeasured("links.json is not there: possible.py did not run")})
    base = rows[0] if rows else None
    for row in rows[1:]:
        cheaper = (base["seconds"]["state"] == row["seconds"]["state"] == "misurato"
                   and row["seconds"]["value"] < base["seconds"]["value"])
        fewer = (base["links"]["state"] == row["links"]["state"] == "misurato"
                 and row["links"]["value"]["found"] < base["links"]["value"]["found"])
        if cheaper and fewer:
            row["flag"] = "costs less and finds fewer links: not a gain"
    return {"runs": rows}


def main(argv: list[str]) -> int:
    if argv[:1] == ["whole"] and len(argv) == 2:
        print(json.dumps(whole(Path(argv[1])), ensure_ascii=False, indent=1))
        return 0
    if argv[:1] == ["runs"] and len(argv) == 4:
        print(json.dumps(runs([Path(folder) for folder in argv[1:]]), ensure_ascii=False, indent=1))
        return 0
    if not (argv[:1] in (["map"], ["stable"]) and len(argv) == 3 or argv[:1] == ["externals"] and len(argv) in (3, 4)
            and argv[3:] in ([], *([s] for s in SOURCES)) or argv[:1] == ["system"] and len(argv) == 4):
        print(__doc__)
        return 2
    first, second = (json.loads(Path(p).read_text(encoding="utf-8")) for p in argv[1:3])
    if argv[0] == "system":
        files = [line.strip().replace("\\", "/") for line in Path(argv[3]).read_text(encoding="utf-8").splitlines()]
        result = score_system(first, second, [f for f in files if f])
    elif argv[0] == "externals":
        result = score_externals(first, second, *argv[3:])
    else:
        result = {"map": score_map, "stable": stability}[argv[0]](first, second)
    print(json.dumps(result, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
