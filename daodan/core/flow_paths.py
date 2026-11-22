"""Numbered event paths derived from classified entries and the snapshot's flow links.

The graph supplies the handler, direction, sites and effect. A naming decision
can cite those steps; a correction needs an actual link at the cited endpoint.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import stat
from collections import defaultdict, deque
from contextlib import closing
from functools import cache
from graphlib import TopologicalSorter
from pathlib import Path

import confinement
from edge_view import uncertainty as _uncertain
import flows
import semantic_store
import snapshot
import system_brief
import system_map
from snapshot_store import open_snapshot


PENDING = "flow-decision-pending.json"


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


@cache
def _reader_id():
    digest = hashlib.sha256()
    for path in (Path(__file__), Path(system_map.__file__)):
        digest.update(path.name.encode() + b"\0" + path.read_bytes().replace(b"\r\n", b"\n"))
    return digest.hexdigest()


def entry_id(entry):
    """The binding site stays identifiable across proof, label and classification revisions."""
    fields = ("site", "column", "symbol", "reader", "shape", "event", "declared_in", "path", "method")
    if not (entry.get("event") or entry.get("shape")):
        fields += ("kind",)  # Legacy manual rules can distinguish two bindings only by their declared kind.
    return _digest({k: entry[k] for k in fields if k in entry})


def _inventory(links, graph):
    cards = {}
    for index, entry in enumerate(links["entries"]):
        labels = graph.activated[entry["symbol"], entry["site"]]
        label = entry.get("label") or (next(iter(labels)) if len(labels) == 1 else None)
        ident = graph.card_id(entry, label)
        cards[ident] = {"row": index, "card_id": ident, "handler": entry["symbol"], "event": entry.get("event") or entry.get("shape") or entry["kind"],
                        **{k: entry[k] for k in ("kind", "site", "column", "declared_in", "handler_source", "handler_confidence", "reader") if k in entry},
                        **({"label": label} if label else {})}
    return cards


def _artifact(manifest, name, *, sqlite=False):
    path = Path(manifest).absolute().with_name(name)
    confinement.reject_link_chain(path)
    paths = [path]
    if sqlite:
        paths.extend(path.with_name(name + suffix) for suffix in ("-journal", "-wal", "-shm"))
    for file in paths:
        info = confinement.reject_link(file)
        if info is not None and (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1):
            raise ValueError(f"not a regular artifact without aliases: {file}")
    return path


def _saved(manifest, key, build):
    """Remember the inventory and only the cards actually opened, across processes."""
    path = _artifact(manifest, "trace-cards.sqlite", sqlite=True)
    with closing(sqlite3.connect(path, timeout=10)) as db, db:
        db.execute("CREATE TABLE IF NOT EXISTS cards (id TEXT PRIMARY KEY, value TEXT NOT NULL)")
        row = db.execute("SELECT value FROM cards WHERE id=?", (key,)).fetchone()
        if row:
            return json.loads(row[0])
        result = build()
        db.execute("INSERT OR IGNORE INTO cards VALUES (?,?)", (key, json.dumps(result)))
        return result


def _deck(manifest, rules):
    confinement.reject_link_chain(Path(manifest).absolute())
    _artifact(manifest, "flow-links.json")
    _artifact(manifest, system_map.FILE)
    key, links = flows.cached_links(manifest, rules, with_key=True)
    # Without a verified filesystem identity compute directly from the current
    # evidence. Do not publish derived facts for these inputs.
    revision = _reader_id() + ":" + key if key else None
    def inventory():
        return _inventory(links, _graph(links, revision))
    cards = _saved(manifest, revision, inventory) if revision else inventory()
    return links, cards, revision


def _detail(manifest, links, card, revision):
    def build():
        return _steps(_graph(links, revision), card)
    return _saved(manifest, revision + ":" + card["card_id"], build) if revision else build()


def _effect(edge):
    # Using a dependency from this file, or reading a shared key, does not prove
    # a state change, an emitted event, a shown value or a device command.
    return edge["type"] == "scrive" and edge["to"].startswith("store:")


class _PathGraph:
    """Index the snapshot once. A component's revision depends only on its downstream evidence."""

    def __init__(self, links):
        self.activated = defaultdict(set)
        self.outgoing = defaultdict(list)
        self.gaps = defaultdict(list)
        self.local = defaultdict(list)
        calls = defaultdict(set)
        entries = links["entries"]
        nodes = {entry["symbol"] for entry in entries}
        effects = set()
        for edge in links["edges"]:
            src, dst = edge["from"], edge["to"]
            self.outgoing[src].append(edge)
            if edge["type"] == "attiva" and edge.get("label"):
                self.activated[dst, edge["site"]].add(edge["label"])
            if not _uncertain(edge) and edge["type"] in ("chiama", "scrive"):
                calls[src].add(dst)
                nodes.update((src, dst))
                if _effect(edge):
                    effects.add(dst)
        for gap in links["gaps"]:
            if gap.get("symbol"):
                self.gaps[gap["symbol"]].append(gap)
            else:
                self.local[system_map._site_file(gap.get("site", ""))].append(gap)
        for index in (self.gaps, self.local):
            for rows in index.values():
                rows.sort(key=_digest)

        components = semantic_store._scc_components(nodes, calls)
        self.owner = {node: i for i, group in enumerate(components) for node in group["symbols"]}
        downstream = [set() for group in components]
        for src, destinations in calls.items():
            i = self.owner[src]
            downstream[i].update(self.owner[dst] for dst in destinations if self.owner[dst] != i)
        order = tuple(TopologicalSorter(dict(enumerate(downstream))).static_order())
        masks = [0] * len(components)
        for i, entry in enumerate(entries):
            masks[self.owner[entry["symbol"]]] |= 1 << i
        for i in reversed(order):
            for child in downstream[i]:
                masks[child] |= masks[i]
        self.shared = {node: count for node, i in self.owner.items()
                       if (count := masks[i].bit_count()) > 1 and count * 2 > len(entries)}
        self.proven = {self.owner[node] for node in effects}
        for i in order:
            if self.proven.intersection(downstream[i]):
                self.proven.add(i)
        self.revisions = {}
        for i in order:
            facts = []
            for node in components[i]["symbols"]:
                edges = self.outgoing[node]
                edges.sort(key=lambda e: (self.owner.get(e["to"]) not in self.proven,
                                          e["to"] in self.shared, e["site"], e["to"], _digest(e)))
                facts.append([node, edges, self.gaps[node], self.local[node.partition("::")[0]]])
            self.revisions[i] = _digest([facts, sorted(self.revisions[child] for child in downstream[i])])

    def card_id(self, entry, label):
        return "v2-" + _digest([entry, label, self.revisions[self.owner[entry["symbol"]]]])


_last_graph = (None, None)


def _build_graph(links):
    return _PathGraph(links)


def _graph(links, revision):
    # Keep at most one indexed graph in the service. A CLI process builds it at most once per revision.
    global _last_graph
    previous, graph = _last_graph
    if revision and revision == previous:
        return graph
    graph = _build_graph(links)
    if revision:
        _last_graph = revision, graph
    return graph


def _steps(graph, card):
    """Walk only the reachable, indexed edges of this handler in distance order."""
    start = card["handler"]
    seen, seen_files, steps = {start}, set(), []
    queue = deque([(start, None, card["site"])])
    while queue:
        node, parent, at = queue.popleft()
        file = node.partition("::")[0]
        stops = list(graph.gaps[node])
        if file not in seen_files:
            stops.extend(graph.local[file])
            seen_files.add(file)
        edges = graph.outgoing[node]
        if not edges and not stops:
            stops.append({"reason": "no outgoing evidence for this handler", "site": at, "symbol": node})
        for edge in edges:
            target = edge["to"]
            reason = _uncertain(edge)
            if not reason and edge["type"] not in ("chiama", "scrive"):
                reason = "this link does not establish a behavioral effect"
            if not reason and target in seen and graph.owner.get(target) == graph.owner[node]:
                if graph.owner[node] not in graph.proven:
                    reason = "cycle without a proven effect"
            end = "lacuna" if reason else "effetto" if _effect(edge) else None
            step = {**edge, "n": len(steps) + 1, "parent": parent, "end": end,
                    **({"shared_by": graph.shared[target]} if target in graph.shared else {}),
                    **({"reason": reason} if reason else {})}
            steps.append(step)
            if not end and target not in seen:
                seen.add(target)
                queue.append((target, step["n"], edge.get("target_site") or edge["site"]))
        for stop in stops:
            steps.append({"n": len(steps) + 1, "from": node, "to": None, "site": stop["site"], "type": "lacuna",
                          "parent": parent, "end": "lacuna", "reason": stop["reason"],
                          "scope": "symbol" if stop.get("symbol") else "file"})
    return steps


def _bounded(row, room):
    """Keep the reference usable if even a single row exceeds its JSON budget."""
    if len(json.dumps(row)) <= room:
        return row
    out = {k: row[k] for k in ("card_id", "n", "parent", "end") if k in row}
    out["truncated"] = True
    for k, value in row.items():
        if k in out:
            continue
        if isinstance(value, str):
            value = value[:100]
        elif isinstance(value, (dict, list)):
            continue
        candidate = {**out, k: value}
        if len(json.dumps(candidate)) <= room:
            out = candidate
    return out


def _visible(card):
    return _bounded({k: v for k, v in card.items() if k != "row"}, 4_000)


def _paged(field, rows, offset, limit, **fields):
    if type(offset) is not int or offset < 0 or type(limit) is not int or limit < 1:
        raise ValueError("offset must be nonnegative and limit positive")
    guide = ("Each numbered step starts at from. Follow parent numbers from the handler. "
             "Only effetto closes a proved path; lacuna gives the last evidence.") if field == "steps" else (
             "Each card identifies a classified event, its binding site and its handler.")
    question = ("Which numbered path reaches an effect, and what data passes on each step?"
                if field == "steps" else "Select a card_id to inspect its numbered steps.")
    out = {"status": "ok", "guide": guide, **fields, "offset": offset, "count": len(rows),
           field: [], "next_offset": None, "question": question}
    # Reserve space for an enclosing run id, masking metadata and the numeric next offset.
    room = system_brief.LIMIT - len(json.dumps(out)) - 1024
    for row in rows[offset:offset + limit]:
        size = len(json.dumps(row)) + 2
        if size > room:
            if out[field]:
                break
            row = _bounded(row, room - 2)
            size = len(json.dumps(row)) + 2
        out[field].append(row)
        room -= size
    if offset + len(out[field]) < len(rows):
        out["next_offset"] = offset + len(out[field])
    return out


def page(manifest: Path, rules: list[dict], offset=0, limit=20, *, card_id=None):
    links, cards, cacheable = _deck(manifest, rules)
    reviewed = _reviews(manifest, links, cards, cacheable)
    if card_id is None:
        return _paged("cards", [{**_visible(row), **({"review": reviewed[i]} if i in reviewed else {})}
                                for i, row in cards.items()], offset, limit)
    if not isinstance(card_id, str) or card_id not in cards:
        raise ValueError("card is unknown or its evidence has changed; list the cards again")
    card = cards[card_id]
    review = reviewed.get(card_id)
    return _paged("steps", _detail(manifest, links, card, cacheable), offset, limit,
                  card=_visible(card), review=_bounded(review, 4_000) if review else None)


def _correct(step, fix, links, manifest):
    """An exact outgoing edge at this symbol and site must support the proposed destination."""
    if not isinstance(fix, dict) or step.get("scope") != "symbol" or step["type"] != "lacuna":
        raise ValueError("only an unresolved link attributed to its caller can be corrected")
    site = fix.get("site")
    if not isinstance(site, str) or site != step["site"]:
        raise ValueError("correction must cite the unresolved site")
    found = [e for e in links["edges"] if e["site"] == site and e["from"] == step["from"]
             and e["to"] == fix.get("to") and not _uncertain(e) and _effect(e)]
    if not found:
        raise ValueError("no snapshot link proves the destination of the correction")
    path, _, line = site.rpartition(":")
    with open_snapshot(manifest) as store:
        lines = flows.Source(store).lines(path) or []
    said = fix.get("text")
    if not isinstance(said, str) or not said.strip() or not line.isdigit() or not 1 <= int(line) <= len(lines) \
            or said not in lines[int(line) - 1]:
        raise ValueError("the cited text is missing from the snapshot line")
    return found[0]


def _chain(links, card, decision, manifest, cacheable):
    if card.get("handler_confidence") == "sampled":
        raise ValueError("the sampled handler is not a proved binding")
    all_steps = _detail(manifest, links, card, cacheable)
    numbers, corrections = decision.get("steps"), decision.get("corrections", [])
    if not isinstance(numbers, list) or not numbers or any(type(n) is not int or not 1 <= n <= len(all_steps) for n in numbers):
        raise ValueError("steps must cite existing numbers of this card")
    if not isinstance(corrections, list):
        raise ValueError("corrections must be a list")
    fixed = {}
    for fix in corrections:
        n = fix.get("step") if isinstance(fix, dict) else None
        if type(n) is not int or n not in numbers or n in fixed:
            raise ValueError("a correction must identify one distinct cited step")
        fixed[n] = _correct(all_steps[n - 1], fix, links, manifest)
    chain, at, visited = [], card["handler"], {card["handler"]}
    for n in numbers:
        step = all_steps[n - 1]
        edge = fixed.get(n) or step
        if step["end"] == "lacuna" and n not in fixed:
            raise ValueError(step["reason"])
        if edge["from"] != at or edge["to"] in visited:
            raise ValueError("steps do not form a directed path from this handler")
        chain.append({k: v for k, v in edge.items() if k not in ("n", "parent", "end", "shared_by")})
        at = edge["to"]
        visited.add(at)
    if not _effect(chain[-1]):
        raise ValueError("the last step does not reach a proved effect")
    return chain


def record(manifest: Path, rules: list[dict], decision: dict, *, rule_update=None):
    """Commit the decision and any accompanying rule change only after both have been checked."""
    update = {}
    result = _decision(manifest, rules, decision, update)
    if not update:
        return result
    if rule_update is not None:
        update["rules"] = rule_update
        # Once this intent exists, replaying it completes the two writes even after a process interruption.
        pending = _artifact(manifest, PENDING)
        snapshot._write_json_atomic(pending, update)
    _apply_decision(manifest, update)
    if rule_update is not None:
        pending.unlink()
    return result


def recover(manifest):
    """Complete an interrupted rule/decision save under the project lock."""
    pending = _artifact(manifest, PENDING)
    if pending.is_file():
        update = json.loads(pending.read_text(encoding="utf-8"))
        if not isinstance(update, dict) or set(update) not in ({"rules", "map"}, {"rules", "review"}):
            raise ValueError("invalid pending flow decision")
        rules = update["rules"]
        if not isinstance(rules, dict) or rules.get("schema") != flows.RULES_SCHEMA or not isinstance(rules.get("rules"), list):
            raise ValueError("invalid rules in pending flow decision")
        flows.validate_rules(rules["rules"], recorded=True)
        if "map" in update and (not isinstance(update["map"], dict) or update["map"].get("schema") != system_map.SCHEMA):
            raise ValueError("invalid map in pending flow decision")
        if "review" in update:
            review = update["review"]
            if (not isinstance(review, dict) or review.get("status") not in ("unresolved", "excluded")
                    or not isinstance(review.get("card_id"), str) or not isinstance(review.get("reason"), str)):
                raise ValueError("invalid review in pending flow decision")
        _apply_decision(manifest, update)
        pending.unlink()


def _apply_decision(manifest, update):
    if "map" in update:
        snapshot._write_json_atomic(_artifact(manifest, system_map.FILE), update["map"])
    else:
        review = update["review"]
        _save_review(manifest, review["card_id"], review["status"], review["reason"])
    if "rules" in update:
        snapshot._write_json_atomic(_artifact(manifest, "flow-rules.json"), update["rules"])


def _decision(manifest, rules, decision, update):
    """Validate a decision against the current cards and stage its authoritative change."""
    try:
        if not isinstance(decision, dict):
            raise ValueError("a trace decision must be an object")
        card_id = decision.get("card_id")
        links, cards, cacheable = _deck(manifest, rules)
        if not isinstance(card_id, str) or card_id not in cards:
            raise ValueError("card is unknown or stale")
        card = cards[card_id]
        if "disposition" in decision:
            if _reviews(manifest, links, cards, cacheable).get(card_id, {}).get("status") == "accepted":
                raise ValueError("an admitted flow already covers this entry")
            disposition, reason = decision["disposition"], decision.get("reason")
            if disposition not in ("excluded", "unresolved") or not isinstance(reason, str) or not 1 <= len(reason.strip()) <= 400:
                raise ValueError("a disposition is excluded or unresolved and requires a short reason")
            update["review"] = {"status": disposition, "card_id": card_id, "reason": reason.strip()}
            return update["review"]
        chain = _chain(links, card, decision, manifest, cacheable)
        data = decision.get("data")
        if not isinstance(data, list) or len(data) != len(chain):
            raise ValueError("give the data passed on each numbered step")
        members = [card["handler"], *(edge["to"] for edge in chain)]
        names = {member: member if len(member) <= 200 else member[:175] + " [" + _digest(member)[:16] + "]"
                 for member in members}
        nodes = list(names.values())
        area, name = decision.get("area"), decision.get("name")
        if not isinstance(area, str) or not isinstance(name, str):
            raise ValueError("name and area must be short texts")
        flow = {"name": name, "area": area, "types": decision.get("types"),
                **{k: decision[k] for k in ("intent", "outcome") if k in decision}, "nodes": nodes, "entries": nodes[:1],
                "effects": nodes[-1:], "arrows": [
                    {"from": names[edge["from"]], "to": names[edge["to"]], "data": label} for edge, label in zip(chain, data)]}
        rows = [{"name": names[member], "members": [member], "type": "entità" if member.startswith("store:") else "funzionalità"}
                for member in members]
        entry = links["entries"][card["row"]]
        report = system_map.record(manifest, rules, {"scope": [area], "nodes": rows, "flows": [flow]},
                                   trace={"card_id": card_id, "entry": entry, "steps": chain},
                                   write_map=lambda payload: update.update(map=payload))
        result = report["flows"][0]
        return {"status": result["status"], "name": result["name"], **{k: result[k] for k in ("id", "reason") if k in result}}
    except ValueError as exc:
        return {"status": "refused", "reason": str(exc)}


def _save_review(manifest, card_id, disposition, reason):
    # Explicit decisions survive clearing the derived card cache. Concurrent
    # clients can review different entries without overwriting one another.
    path = _artifact(manifest, "entry-reviews.sqlite", sqlite=True)
    with closing(sqlite3.connect(path, timeout=10)) as db, db:
        db.execute("CREATE TABLE IF NOT EXISTS reviews (id TEXT PRIMARY KEY, disposition TEXT, reason TEXT)")
        db.execute("INSERT OR REPLACE INTO reviews VALUES (?,?,?)", (card_id, disposition, reason))


def rebind(links, cards, saved_flows):
    """A saved flow retains its admitted evidence. Expose the current card id when the binding still exists."""
    by_entry = {_digest(links["entries"][card["row"]]): ident for ident, card in cards.items()}
    for flow in saved_flows:
        field = "trace" if "trace" in flow else "trace_review"
        if pin := flow.get(field):
            current = [{**binding, "card_id": ident} for binding in system_map.trace_bindings(pin)
                       if (ident := by_entry.get(_digest(binding["entry"])))]
            if current:
                flow[field] = {**{k: v for k, v in pin.items() if k != "bindings"}, **current[0],
                               **({"bindings": current[1:]} if len(current) > 1 else {})}
            else:
                flow[field] = {**pin, "card_id": None}


def _legacy_reviews(manifest, links, cards, revision, missing):
    """An older exclusion contains only an opaque id. Recover it only from matching saved evidence."""
    path = _artifact(manifest, "trace-cards.sqlite", sqlite=True)
    if not path.is_file() or not missing:
        return {}
    candidates = defaultdict(list)
    for card in cards.values():
        candidates[card["site"], card["handler"]].append(card)
    matched = {}
    with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)) as db:
        # v1 inventories used a two-digest key. Only read inventory rows sharing an old decision.
        for old_key, raw, ident, detail in db.execute(
                "SELECT c.id, j.value, j.key, d.value FROM cards c, json_each(c.value) j "
                "JOIN cards d ON d.id=j.key WHERE length(c.id)=129 AND substr(c.id,65,1)=':' "
                "AND j.key IN (SELECT value FROM json_each(?))", (json.dumps(list(missing)),)):
            old = json.loads(raw)
            for card in candidates[old["site"], old["handler"]]:
                entry = links["entries"][card["row"]]
                if _digest([old_key, entry]) == ident and json.loads(detail) == _steps(_graph(links, revision), card):
                    matched[ident] = card["card_id"]
    return matched


def _reviews(manifest, links, cards, revision):
    reviews = {}
    path = _artifact(manifest, "entry-reviews.sqlite", sqlite=True)
    if path.is_file():
        with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)) as db:
            saved_reviews = {i: {"status": status, "reason": reason} for i, status, reason in
                             db.execute("SELECT id, disposition, reason FROM reviews")}
        reviews = {k: v for k, v in saved_reviews.items() if k in cards}
        missing = {k: v for k, v in saved_reviews.items() if not k.startswith("v2-")}
        recovered = _legacy_reviews(manifest, links, cards, revision, missing)
        if recovered:
            with closing(sqlite3.connect(path, timeout=10)) as db, db:
                for old_id, current in recovered.items():
                    db.execute("INSERT OR IGNORE INTO reviews SELECT ?, disposition, reason FROM reviews WHERE id=?",
                               (current, old_id))
                    db.execute("DELETE FROM reviews WHERE id=?", (old_id,))
                    reviews.setdefault(current, missing[old_id])
    saved = _artifact(manifest, system_map.FILE)
    if saved.is_file():
        from store_graph import source_stamp
        stamp = source_stamp(saved)
        def accepted():
            # Recheck the saved map. A historical trace_verified flag is insufficient when rules or proofs changed.
            headers = system_map._headers(manifest)
            state = system_map._state(manifest, headers)
            current = system_map._evaluate(manifest, links, state, headers)
            rebind(links, cards, current["flows"])
            result = {}
            for flow in current["flows"]:
                if flow.get("trace") and flow["fresh"] and flow.get("reachability") == "verified":
                    for binding in system_map.trace_bindings(flow["trace"]):
                        if ident := binding["card_id"]:
                            result[ident] = {"status": "accepted", "flow": flow["id"]}
            return result
        reviews.update(_saved(manifest, revision + ":accepted:" + _digest(stamp), accepted)
                       if revision and stamp[-1] else accepted())
    return reviews


def _write_coverage(links):
    """A write belongs to its writer and site; sharing a store key gives no path between writers."""
    reached = flows.reached_symbols(links["entries"], links["edges"], kinds=("chiama",))
    outgoing, writes, stopped = defaultdict(list), set(), {}
    for edge in links["edges"]:
        if edge["type"] == "chiama":
            if edge["from"] not in reached:
                outgoing[edge["from"]].append(edge)
            elif edge["to"] not in reached and (reason := _uncertain(edge)):
                stopped.setdefault(edge["to"], {"site": edge["site"], "reason": reason})
        elif _effect(edge) and not _uncertain(edge):
            writes.add((edge["from"], edge["site"], edge["to"]))

    # Explain an orphan downstream of an uncertain call, without counting its call chain as proved.
    todo = deque(sorted(stopped))
    while todo:
        caller = todo.popleft()
        for edge in outgoing[caller]:
            target = edge["to"]
            if target not in reached and target not in stopped:
                stopped[target] = stopped[caller]
                todo.append(target)

    orphaned = []
    for writer, site, effect in sorted(writes):
        if writer in reached:
            continue
        barrier = stopped.get(writer)
        orphaned.append({"n": len(orphaned) + 1, "writer": writer, "site": site, "effect": effect,
                         "reason": barrier["reason"] if barrier else "no evidenced call path from a classified entry",
                         **({"stopped_at": barrier["site"]} if barrier else {})})
    return {"writes": len(writes), "reached": len(writes) - len(orphaned), "without_entry": len(orphaned),
            "effects": orphaned}


def _effect_inventory(manifest, links, revision):
    if revision:
        return _saved(manifest, revision + ":effects", lambda: _write_coverage(links))
    return _write_coverage(links)


def orphan_effects(manifest, rules, offset=0, limit=20):
    """Page certain writes for which this snapshot cannot prove a call path from a classified entry."""
    links, _, revision = _deck(manifest, rules)
    coverage = _effect_inventory(manifest, links, revision)
    counts = {k: coverage[k] for k in ("writes", "reached", "without_entry")}
    page = _paged("effects", coverage["effects"], offset, limit, **counts)
    page["guide"] = "Each numbered row is a distinct writer, site and written key with no proved entry path."
    page["question"] = "Which unresolved write site needs more evidence?"
    return page


def next_question(manifest: Path, rules: list[dict]):
    """One fresh context per unreviewed classified control, resumed on the same evidence."""
    links, cards, revision = _deck(manifest, rules)
    coverage = _effect_inventory(manifest, links, revision)
    reviewed = _reviews(manifest, links, cards, revision)
    counts = dict.fromkeys(("accepted", "excluded", "unresolved"), 0)
    for row in reviewed.values():
        counts[row["status"]] += 1
    first = next((card for ident, card in cards.items() if ident not in reviewed), None)
    return {"status": "pending" if first else "complete", "count": len(cards), "remaining": len(cards) - len(reviewed),
            "reviewed": counts, "effect_coverage": {k: coverage[k] for k in ("writes", "reached", "without_entry")},
            "question": _visible(first) if first else None}
