"""Progressive, input-bound code scope selection. No inference, writes or run closure.

Preparation registers requirements and canonical impact obligations before applying
discovery caps. Advancement checkpoints a deterministic frontier; source availability
and process validation remain separate facts. See references/scope.md for the API.
"""
from __future__ import annotations

import copy
from contextlib import ExitStack, closing
import hashlib
import json
import math
from pathlib import Path
import time

import edge_view
import migrate_root
import resolve_edges
import retrieval
import semantic_store as semantics
import snapshot
import source_reader
from snapshot_store import artifact_digest, logical_digest, open_snapshot

SCHEMA = "daodan/scope-plan/v1"
POLICY = "scope-v1"
_SECTIONS = ("analysis", "edit_candidates", "potential_impact", "validation_obligations",
             "deferred", "unresolved", "outside_boundary")
_CAPS = {"candidates": "max_candidates", "edges": "max_edges", "rounds": "max_rounds",
         "seconds": "max_seconds", "input_tokens": "max_input_tokens",
         "output_tokens": "max_output_tokens"}


def _relative(path):
    return source_reader._relative(path, allow_root=True)


def _inside(path, boundaries):
    return any(b == "." or path == b or path.startswith(b + "/") for b in boundaries)


def _boundaries(values):
    if not isinstance(values, list):
        raise ValueError("boundary must be a list of relative paths")
    return sorted(set(_relative(v) for v in values))


def _authority(request, authority):
    if not isinstance(authority, dict) or not Path(authority.get("root", "")).is_absolute():
        raise ValueError("independent authority requires an absolute project root")
    root = Path(authority["root"])
    migrate_root._reject_link_chain(root)
    root = root.resolve(strict=True)
    result = {"root": str(root)}
    source = root
    if 'source_root' in authority:
        if not isinstance(authority['source_root'], (str, Path)):
            raise ValueError('independent source root must name a directory')
        source = Path(authority['source_root'])
        if not source.is_absolute():
            raise ValueError('independent source root must be absolute')
        migrate_root._reject_link_chain(source)
        source = source.resolve(strict=True)
        if not source.is_dir() or not (source.is_relative_to(root) or root.is_relative_to(source)):
            raise ValueError('source coordinate root must be related to the artifact project')
        result['source_root'] = str(source)
    for name in ("read_boundary", "write_boundary"):
        allowed = _boundaries(authority.get(name))
        for boundary in allowed:
            _path(source / boundary, root)
        requested = _boundaries(request.get(name))
        if any(not _inside(b, allowed) for b in requested):
            raise ValueError(f"request exceeds independent {name} boundary")
        result[name] = requested
    if any(not _inside(b, result["read_boundary"]) for b in result["write_boundary"]):
        raise ValueError("write boundary must be inside the read boundary")
    return result


def _validate_request(request):
    required = {"schema", "task_id", "intent", "query", "read_boundary", "write_boundary",
                "anchors", "base", "candidate", "diff", "proposed_edits",
                "mandatory_requirements", "required_gates", "budget", "policy_version"}
    if not isinstance(request, dict) or not required <= request.keys():
        raise ValueError("incomplete context request")
    if request["schema"] != "daodan/context-request/v1" or request["policy_version"] != POLICY:
        raise ValueError("unsupported scope request or policy version")
    if request["intent"] not in {"analysis", "docs", "bug", "change", "test", "finish"}:
        raise ValueError("unsupported scope intent")
    if not isinstance(request["task_id"], str) or not request["task_id"]:
        raise ValueError("task_id must be nonempty text")
    if not isinstance(request["query"], str) or len(request["query"]) > 16384:
        raise ValueError("invalid scope query")
    for key in ("anchors", "diff", "proposed_edits", "mandatory_requirements", "required_gates"):
        if not isinstance(request[key], list) or any(not isinstance(v, dict) for v in request[key]):
            raise ValueError(f"{key} must be a list of records")
    budget = request["budget"]
    if not isinstance(budget, dict) or not set(_CAPS.values()) <= budget.keys():
        raise ValueError("scope budget requires independent cumulative caps")
    for cap in _CAPS.values():
        value = budget[cap]
        if (type(value) not in (int, float) or not math.isfinite(value) or value < 0
                or (cap != "max_seconds" and type(value) is not int)):
            raise ValueError(f"invalid scope budget {cap}")
    for key in ("mandatory_requirements", "required_gates"):
        seen = set()
        for row in request[key]:
            if not isinstance(row.get("id"), str) or not row["id"] or row["id"] in seen:
                raise ValueError(f"{key} requires unique nonempty IDs")
            seen.add(row["id"])
            if key == "mandatory_requirements":
                support = row.get("support", [])
                if not isinstance(support, list) or any(not isinstance(s, dict) for s in support):
                    raise ValueError("requirement support must be a list of predicates")


def _path(value, root):
    if not isinstance(value, (str, Path)):
        raise ValueError("scope input paths must be absolute paths")
    path = Path(value)
    if not path.is_absolute():
        raise ValueError("scope input paths must be absolute")
    migrate_root._reject_link_chain(path)
    path = path.resolve()
    if not path.is_relative_to(root):
        raise ValueError("scope artifact is outside the authorized project")
    return path


def _stamp(path):
    migrate_root._reject_link_chain(path)
    if path.exists() and not path.is_file():
        raise ValueError("scope input is not a regular file")
    # A live SQLite writer cannot hide behind an unchanged main database file.
    sidecars = {}
    for suffix in ("-wal", "-journal"):
        p = Path(str(path) + suffix)
        migrate_root._reject_link_chain(p)
        if p.exists():
            if not p.is_file():
                raise ValueError("scope SQLite sidecar is not a regular file")
            sidecars[suffix] = artifact_digest(p)
    return {"path": str(path), "sha256": artifact_digest(path) if path.is_file() else None,
            "sidecars": sidecars}


def _verify_source(store, boundaries):
    root, target, perimeter = source_reader._binding(store)
    actual = {p.relative_to(root).as_posix() for p in snapshot.iter_files(target, perimeter)
              if _inside(p.relative_to(root).as_posix(), boundaries)}
    expected = {p for p in store.iter_paths() if _inside(p, boundaries)}
    if actual != expected:
        raise ValueError("stale source inventory; refresh the snapshot")
    if actual:
        source_reader.read_packet(store, [{"path": rel, "full_file": True} for rel in sorted(actual)])


def _stable(stores, bindings, paths, stamps, boundaries):
    for name, store in stores.items():
        if _stamp(store.path) != {k: bindings[name][k] for k in ("path", "sha256", "sidecars")}:
            raise ValueError("stale snapshot changed during scope selection")
    for name, stamp in stamps.items():
        if stamp != _stamp(Path(paths[name])):
            raise ValueError("stale index changed during scope selection")
    _verify_source(stores["candidate"], boundaries)


def _inputs(request, authority, indexes, stack):
    _validate_request(request)
    bound = _authority(request, authority)
    root = Path(bound["root"])
    stores, bindings = {}, {}
    for name in ("base", "candidate"):
        descriptor = request[name]
        if descriptor is None and name == "base":
            bindings[name] = None
            continue
        if not isinstance(descriptor, dict) or set(descriptor) != {"manifest"}:
            raise ValueError(f"{name} must name a manifest")
        path = _path(descriptor["manifest"], root)
        store = stack.enter_context(open_snapshot(path))
        if store.format != "sqlite" or Path(store.get("root")).resolve() != Path(bound.get('source_root', root)):
            raise ValueError("scope requires a project-bound SQLite snapshot")
        _path(Path(store.get('root')) / _relative(store.get('target')), root)
        stores[name] = store
        bindings[name] = {**_stamp(path), "logical_digest": logical_digest(store),
                          **snapshot._snapshot_info(store)}
    if not isinstance(indexes, dict) or set(indexes) - {"engine", "base_engine", "retrieval", "cards", "embedding_result"}:
        raise ValueError("invalid scope indexes")
    paths = dict(indexes)
    for key, name in (("engine", "candidate"), ("base_engine", "base")):
        if name in stores:
            paths.setdefault(key, str(resolve_edges.default_edge_store(stores[name].path)))
    stamps = {key: _stamp(_path(path, root)) for key, path in sorted(paths.items())}
    _verify_source(stores["candidate"], bound["read_boundary"])
    binding = {"request": request, "authority": bound, "snapshots": bindings,
               "indices": stamps, "planner_policy": POLICY,
               "parser": snapshot.parser_fingerprint(), "resolver": semantics.RESOLVER_VERSION}
    return stores, bindings, bound, paths, stamps, retrieval._digest(binding)


def _records(store):
    records = {}
    for rel, entry in store.iter_files(semantic=False):
        symbols = dict(entry.get("symbols") or {})
        symbols.setdefault("@file", {"kind": "file", "start": 1, "end": entry["lines"],
                                     "hash": entry.get("hash"), "span_precision": "file"})
        for name, spec in sorted(symbols.items()):
            record = snapshot._entity_record(store, rel, entry, name, spec)
            records[record["entity_id"]] = record
    return records


def _add(plan, section, entity, reason, provenance, **fields):
    row = next((r for r in plan[section] if r.get("entity_id") == entity
                and r.get("kind") == fields.get("kind")), None)
    if row is None:
        row = {"entity_id": entity, "reason": [], "provenance": [], "status": "candidate", **fields}
        if section == "validation_obligations":
            row["id"] = retrieval._digest([fields.get("kind"), entity])
        plan[section].append(row)
    if reason not in row["reason"]:
        row["reason"].append(reason)
    if provenance not in row["provenance"]:
        row["provenance"].append(provenance)
    return row


def _gap(plan, kind, reason, **details):
    value = {"kind": kind, "reason": reason, **details}
    value["id"] = retrieval._digest(value)
    if value not in plan["unresolved"]:
        plan["unresolved"].append(value)


def _candidate(plan, entity, reason, provenance, *, priority=4, rank=0):
    record = plan["entities"].get(entity)
    if record is None:
        _gap(plan, "missing_entity", "entity absent from the candidate", entity_id=entity)
        return False
    path = record["anchor"]["file"]
    if not _inside(path, plan["boundaries"]["read_boundary"]):
        _add(plan, "outside_boundary", entity, "outside read boundary", provenance, boundary="read")
        _add(plan, "validation_obligations", entity, reason, provenance, kind="boundary", status="open")
        return False
    priority = min([priority, rank], plan["priorities"].get(entity, [priority, rank]))
    plan["priorities"][entity] = priority
    row = _add(plan, "analysis", entity, reason, provenance, anchor=record["anchor"], required_detail="source")
    row["priority"] = priority
    if entity not in plan["visited"] and entity not in plan["frontier"]:
        if plan["active"] is None or plan["active"]["entity_id"] != entity:
            plan["frontier"].append(entity)
    plan["frontier"].sort(key=lambda identity: (plan["priorities"][identity], identity))
    return True


def _anchors(plan, store, anchors, reason):
    for anchor in anchors:
        try:
            found, ambiguous = retrieval._anchor_records(store, plan["entities"], anchor)
        except ValueError as error:
            _gap(plan, "anchor", str(error), anchor=anchor)
            continue
        if ambiguous:
            _gap(plan, "ambiguous_anchor", "anchor requires localization", anchor=anchor)
        for record in found:
            accepted = _candidate(plan, record["entity_id"], reason, {"kind": "anchor", "anchor": anchor},
                                  priority=0 if reason == "explicit requirement target" else 1)
            if accepted and not ambiguous:
                plan["localized"] = True


def _comparison(plan, stores, paths):
    if "base" not in stores:
        _gap(plan, "no_base", "No cross-revision impact claim is available")
        return
    comparison = semantics.build_stale_callers(stores["base"], stores["candidate"],
        limit=semantics.MAX_STALE_CALLERS, base_engine_store=paths.get("base_engine"),
        candidate_engine_store=paths.get("engine"))
    plan["comparison"] = comparison
    for changed in comparison["changed"]:
        accepted = _candidate(plan, changed["symbol_id"], "snapshot diff", changed, priority=1)
        if accepted and plan["intent"] in {"change", "finish"}:
            plan["localized"] = True
    for name in ("edit_impact", "validation_impact", "do_not_touch"):
        group = comparison[name]
        for row in group["listed"]:
            identity = row["symbol_id"]
            _add(plan, "potential_impact", identity, name, row)
            if name != "do_not_touch":
                _add(plan, "validation_obligations", identity, name, row, kind="impact", status="open")
            _candidate(plan, identity, name, row, priority=2)
        if group["truncated"]:
            # The producer cap is independent of the discovery budget. Never
            # present its bounded result as an exhaustive list of obligations.
            _gap(plan, "impact_overflow", "canonical impact list is truncated", group=name,
                 omitted=group["truncated"], total=group["total"])
    if any(comparison[name]["truncated"] for name in ("edit_impact", "validation_impact", "do_not_touch")):
        # The canonical SCC inventory is not capped. Keep its entire tail as
        # conservative inspection obligations, without reconstructing or guessing
        # the producer's missing per-caller classification.
        classified = {r["symbol_id"] for name in ("edit_impact", "validation_impact", "do_not_touch")
                      for r in comparison[name]["listed"]}
        classified.update(r["symbol_id"] for r in comparison["changed"])
        for component in comparison["components"]:
            for identity in component["symbols"]:
                if identity not in classified:
                    provenance = {"kind": "canonical_impact_component", "component": component,
                                  "classification": "unavailable beyond producer cap"}
                    _add(plan, "potential_impact", identity, "unclassified impact tail", provenance)
                    _add(plan, "validation_obligations", identity, "inspect unclassified impact tail", provenance,
                         kind="impact", status="open")
                    _candidate(plan, identity, "unclassified impact tail", provenance, priority=2)
    for kind in ("lexical_callee_drift", "engine_callee_drift"):
        drift = comparison[kind]
        for row in drift["items"]:
            identity = row.get("symbol_id") or row.get("caller")
            if identity in plan["entities"]:
                _candidate(plan, identity, kind, row, priority=2)
                _add(plan, "validation_obligations", identity, kind, row, kind="binding", status="open")
        if drift["truncated"]:
            _gap(plan, "impact_overflow", "binding drift is truncated", group=kind, omitted=drift["truncated"])
    if comparison["incompatible"]:
        _gap(plan, "incompatible_digests", "cross-revision digest versions differ",
             items=comparison["incompatible"])
    if stores["base"].get("parser_fingerprint") != stores["candidate"].get("parser_fingerprint"):
        _gap(plan, "incompatible_parser", "base and candidate parser profiles differ")


def _has_source(plan, entity):
    record = plan["entities"].get(entity)
    if record is None:
        return False
    anchor = record["anchor"]
    return set(range(anchor["start_line"], anchor["end_line"] + 1)) <= set(
        plan["provided_source"].get(anchor["file"], []))


def _source_support(plan):
    for row in plan["validation_obligations"]:
        if row.get("kind") != "requirement":
            continue
        predicates = row.get("support", [])
        supported = bool(predicates)
        for predicate in predicates:
            if predicate.get("predicate") != "current_source" or not _has_source(plan, predicate.get("entity_id")):
                supported = False
        row["support_status"] = "source_provided" if supported else "missing"
    for row in plan["analysis"]:
        if _has_source(plan, row["entity_id"]):
            row["status"] = "source_provided"


def _actions(plan):
    def offer(kind, entity, gap):
        key = retrieval._digest([plan["input_digest"], kind, entity, "current_source" if kind == "read_source" else gap])
        action = next((a for a in plan["actions"] if a["id"] == key), None)
        if action is None:
            plan["actions"].append({"id": key, "kind": kind, "entity_id": entity, "gap": gap,
                                    "gaps": [gap],
                                    "status": "available", "max_attempts": 1,
                                    "max_cost": {"machine_seconds": plan["budget"]["max_seconds"], "llm_calls": 0},
                                    "cost_measurement": "cooperative time cap; tokens require caller observations"})
        elif gap not in action["gaps"]:
            action["gaps"].append(gap)
            action["gaps"].sort()
    for action in plan["actions"]:
        if action["kind"] == "localize" and plan["localized"]:
            action["status"] = "satisfied"
        if action["kind"] == "read_source" and _has_source(plan, action["entity_id"]):
            action["status"] = "satisfied"
    for row in plan["validation_obligations"]:
        if row.get("kind") == "requirement" and row["support_status"] == "missing":
            for predicate in row.get("support", []):
                entity = predicate.get("entity_id")
                record = plan["entities"].get(entity)
                if (predicate.get("predicate") == "current_source" and record
                        and not _has_source(plan, entity)
                        and _inside(record["anchor"]["file"], plan["boundaries"]["read_boundary"])):
                    offer("read_source", entity, row["id"])
    if not plan["localized"]:
        offer("localize", None, "query")


def _finish(plan):
    _source_support(plan)
    _actions(plan)
    exhausted = [key for key, cap in _CAPS.items() if plan["usage"][key] >= plan["budget"][cap]]
    pending = bool(plan["frontier"] or plan["active"])
    missing = any(r.get("support_status") == "missing" for r in plan["validation_obligations"])
    overflow = any(g["kind"] == "impact_overflow" for g in plan["unresolved"])
    if overflow or exhausted and (pending or missing or not plan["localized"]):
        plan["status"] = "needs_split"
    elif pending:
        plan["status"] = "incomplete"
    elif missing or not plan["localized"]:
        plan["status"] = "needs_localization"
    else:
        plan["status"] = "ready_for_attempt"
    plan["deferred"] = [{"entity_id": e, "reason": "pending frontier", "status": "deferred",
                          "provenance": ["input-bound checkpoint"]} for e in plan["frontier"]]
    if plan["active"]:
        plan["deferred"].append({"entity_id": plan["active"]["entity_id"], "reason": "partially expanded frontier",
                                 "status": "deferred", "provenance": ["input-bound checkpoint"],
                                 "remaining_edges": len(plan["active"]["neighbors"]) - plan["active"]["offset"]})
    plan["coverage"].update(frontier_exhausted=not pending, provisional=True,
                             hard_support_missing=missing, exhausted_budgets=exhausted)
    for section in _SECTIONS:
        plan[section].sort(key=lambda r: (r.get("entity_id") or "", r.get("kind") or "", r.get("id") or ""))
    plan["cursor"] = {"schema": "daodan/scope-cursor/v1", "input_digest": plan["input_digest"],
                      "state_digest": retrieval._digest({k: v for k, v in plan.items() if k != "cursor"})}
    return plan


def _verify_cursor(plan):
    if (not isinstance(plan, dict) or plan.get("schema") != SCHEMA
            or plan.get("cursor", {}).get("state_digest") != retrieval._digest({k: v for k, v in plan.items() if k != "cursor"})):
        raise ValueError("invalid or altered scope cursor")


def prepare_scope(request: dict, *, authority: dict, indexes: dict | None = None) -> dict:
    """Register obligations and seed a resumable frontier from existing evidence."""
    started = time.monotonic()
    with ExitStack() as stack:
        stores, bindings, bound, paths, stamps, digest = _inputs(request, authority, indexes or {}, stack)
        store = stores["candidate"]
        view = edge_view.load_edge_view(store, engine_store=paths["engine"])
        plan = {"schema": SCHEMA, "task_id": request["task_id"], "input_digest": digest,
                "base": bindings["base"], "candidate": bindings["candidate"], "policy_version": POLICY,
                "resolver_profile": {"profile": view["profile"], "coverage": view["coverage"],
                                     "resolver_version": view["resolver_version"]},
                "indices": stamps, "index_paths": paths, "boundaries": bound, "intent": request["intent"],
                "budget": copy.deepcopy(request["budget"]), "entities": _records(store),
                "usage": {key: 0 for key in _CAPS}, "usage_observations": {}, "provided_source": {},
                "frontier": [], "active": None, "visited": [], "priorities": {}, "actions": [], "localized": False,
                "comparison": None, "coverage": {"static_only": True, "inventory_files": len(list(store.iter_paths())),
                    "engine": view["coverage"], "unavailable_edge_kinds": ["OVERRIDES", "INHERITS", "IMPORTS"],
                    "runtime_exercised": 0}, "stop_calibration": "uncalibrated",
                "task_complete": False, "validation_complete": False, "write_authorized": False,
                **{section: [] for section in _SECTIONS}}
        for key, kind in (("mandatory_requirements", "requirement"), ("required_gates", "gate")):
            plan["validation_obligations"].extend({**copy.deepcopy(row), "kind": kind, "status": "open"}
                                                  for row in request[key])
        for requirement in request["mandatory_requirements"]:
            for predicate in requirement.get("support", []):
                if predicate.get("predicate") == "current_source" and predicate.get("entity_id") in plan["entities"]:
                    _anchors(plan, store, [{"entity_id": predicate["entity_id"]}], "explicit requirement target")
        _comparison(plan, stores, paths)
        _anchors(plan, store, request["anchors"], "exact anchor")
        for diff in request["diff"]:
            anchors = [{"path": diff["path"], **r} for r in diff["ranges"]] if "ranges" in diff else [diff]
            _anchors(plan, store, anchors, "supplied diff")
        for proposed in request["proposed_edits"]:
            _anchors(plan, store, [proposed], "proposed intervention")
            try:
                matches, ambiguous = retrieval._anchor_records(store, plan["entities"], proposed)
            except ValueError:
                continue
            for record in matches:
                entity, path = record["entity_id"], record["anchor"]["file"]
                if not ambiguous and _inside(path, bound["write_boundary"]):
                    _add(plan, "edit_candidates", entity, "explicitly proposed site", proposed)
                else:
                    if not _inside(path, bound["write_boundary"]):
                        _add(plan, "outside_boundary", entity, "outside write boundary", proposed, boundary="write")
                    if ambiguous:
                        _gap(plan, "ambiguous_proposal", "proposal needs an exact intervention site", anchor=proposed)
                    _add(plan, "validation_obligations", entity, "proposal requires owner decision", proposed, kind="boundary", status="open")
        if request["query"]:
            if "retrieval" not in paths:
                _gap(plan, "retrieval_missing", "No explicit text index supplied")
            elif any(not _inside(p, bound["read_boundary"]) for p in store.iter_paths()):
                _gap(plan, "retrieval_boundary", "whole-index verification would read outside the boundary")
            else:
                # Inspect index metadata before its reader can open another
                # manifest or source tree. Post-search validation is too late.
                with closing(retrieval._read(Path(paths["retrieval"]))) as db:
                    metadata = json.loads(db.execute("SELECT value FROM metadata").fetchone()[0])
                if metadata.get("binding") != retrieval._binding(store):
                    raise ValueError("retrieval index belongs to a different candidate")
                dense = json.loads(Path(paths["embedding_result"]).read_text(encoding="utf8")) if "embedding_result" in paths else None
                result = retrieval.search(Path(paths["retrieval"]), request["query"], anchors=[], limit=1000, embedding_result=dense)
                if result["binding"] != retrieval._binding(store):
                    raise ValueError("retrieval index belongs to a different candidate")
                plan["retrieval"] = {k: v for k, v in result.items() if k != "results"}
                for rank, row in enumerate(result["results"]):
                    _candidate(plan, row["entity_id"], "retrieval lead", row, priority=3, rank=rank)
                plan["localized"] |= bool(result["exact"])
                for reason in result["gaps"]:
                    _gap(plan, "retrieval", reason)
                if result["truncated"]:
                    _gap(plan, "retrieval_overflow", "retrieval candidates truncated", omitted=result["truncated"])
        _gap(plan, "static_limits", "unavailable edge kinds and unresolved calls cannot prove independence",
             unavailable_edge_kinds=plan["coverage"]["unavailable_edge_kinds"],
             unresolved_references=sum(r.get("resolution") != "resolved" for r in view["references"]),
             engine_coverage=view["coverage"]["status"])
        if view["conflicts"]:
            _gap(plan, "engine_conflicts", "conflicting targets require inspection", conflicts=view["conflicts"])
        # Stable order is stored on disk; no fixed-hop completeness rule.
        plan["frontier"].sort(key=lambda identity: (plan["priorities"][identity], identity))
        _stable(stores, bindings, paths, stamps, bound["read_boundary"])
        plan["usage"]["seconds"] = time.monotonic() - started
        return _finish(plan)


def _evidence(plan, evidence, store):
    if not isinstance(evidence, dict) or set(evidence) - {"source_packets", "usage", "attempted_actions", "leads", "anchors"}:
        raise ValueError("unsupported scope evidence")
    if any(not isinstance(value, list) for value in evidence.values()):
        raise ValueError("scope evidence fields must be lists")
    for packet in evidence.get("source_packets", []):
        if not isinstance(packet, dict) or packet.get("schema") != source_reader.SCHEMA or not packet.get("files"):
            raise ValueError("invalid source evidence")
        for supplied in packet["files"]:
            path = _relative(supplied["path"])
            if not _inside(path, plan["boundaries"]["read_boundary"]):
                raise ValueError("source evidence is outside the read boundary")
            requests = [{"path": path, "ranges": [{"start": b["start"], "end": b["end"]} for b in supplied["blocks"]]}]
            actual = source_reader.read_packet(store, requests)
            expected = actual["files"][0]
            if any(packet.get(k) != actual.get(k) for k in ("root", "target", "scope", "inventory")):
                raise ValueError("source evidence has a different snapshot binding")
            lines = {}
            for block in expected["blocks"]:
                physical = [line + "\n" for line in block["source"].removesuffix("\n").split("\n")]
                lines.update(zip(range(block["start"], block["end"] + 1), physical))
            if any(b["reason"] == "full-file-fallback" for b in expected["blocks"]):
                covered = {n for b in supplied["blocks"] for n in range(b["start"], b["end"] + 1)}
                if not set(lines) <= covered:
                    raise ValueError("source evidence requires the canonical full-file fallback")
            for block in supplied["blocks"]:
                if (supplied.get("raw_hash") != expected["raw_hash"] or block["source"] != "".join(
                        lines[n] for n in range(block["start"], block["end"] + 1))):
                    raise ValueError("source evidence does not match current source")
            covered = set(plan["provided_source"].get(path, []))
            covered.update(n for b in supplied["blocks"] for n in range(b["start"], b["end"] + 1))
            plan["provided_source"][path] = sorted(covered)
    for observation in evidence.get("usage", []):
        if (not isinstance(observation, dict) or set(observation) != {"id", "input_tokens", "output_tokens", "measurement"}
                or not isinstance(observation["id"], str) or not observation["id"]
                or observation["measurement"] not in {"actual", "estimated"}
                or any(type(observation[k]) is not int or observation[k] < 0 for k in ("input_tokens", "output_tokens"))):
            raise ValueError("invalid usage observation")
        previous = plan["usage_observations"].get(observation["id"])
        if previous is not None and previous != observation:
            raise ValueError("usage observation ID changed")
        if previous is None:
            plan["usage_observations"][observation["id"]] = copy.deepcopy(observation)
            for key in ("input_tokens", "output_tokens"):
                plan["usage"][key] += observation[key]
    for identity in evidence.get("attempted_actions", []):
        action = next((a for a in plan["actions"] if a["id"] == identity), None)
        if action is None:
            raise ValueError("unknown scope action")
        action["status"] = "exhausted"
    # Similarity and cards are discovery leads, never hard source support.
    for lead in evidence.get("leads", []):
        _candidate(plan, lead["entity_id"], "unverified external lead", lead, priority=3, rank=1000)
    _anchors(plan, store, evidence.get("anchors", []), "explicit localization evidence")


def _neighbors(db, lookup, rows, entity, intent):
    if entity not in rows:
        return []
    incoming, outgoing = semantics._direct_edges(db, lookup, rows[entity])
    directions = [("callee", outgoing)]
    if intent in {"bug", "change", "test", "finish"}:
        directions.insert(0, ("caller", incoming))
    return [{"entity_id": other, "direction": direction,
             "edges": [item[2][key] for key in sorted(item[2])]}
            for direction, group in directions for other, item in sorted(group.items())]


def advance_scope(plan: dict, request: dict, *, authority: dict, indexes: dict | None = None,
                  evidence: dict | None = None, max_steps: int = 100) -> dict:
    """Advance bounded machine discovery, preserving every prior obligation."""
    _verify_cursor(plan)
    if type(max_steps) is not int or max_steps < 0:
        raise ValueError("max_steps must be a nonnegative checkpoint quota")
    started = time.monotonic()
    with ExitStack() as stack:
        stores, bindings, bound, paths, stamps, digest = _inputs(request, authority,
            plan["index_paths"] if indexes is None else indexes, stack)
        if digest != plan["input_digest"]:
            raise ValueError("stale scope cursor: request, authority, snapshot or index changed")
        result = copy.deepcopy(plan)
        store = stores["candidate"]
        _evidence(result, evidence or {}, store)
        db = stack.enter_context(semantics.semantic_reader(store))
        semantics.install_edge_view(db, store, engine_store=paths["engine"])
        lookup, rows = semantics._ImpactIndex(db), semantics._meta_map(db)
        work = result["frontier"] or result["active"]
        if work and result["usage"]["rounds"] < result["budget"]["max_rounds"]:
            result["usage"]["rounds"] += 1
            for _ in range(max_steps):
                usage, budget = result["usage"], result["budget"]
                if (usage["seconds"] + time.monotonic() - started >= budget["max_seconds"]
                        or any(usage[k] >= budget[_CAPS[k]] for k in ("input_tokens", "output_tokens"))):
                    break
                active = result["active"]
                if active is None:
                    if not result["frontier"] or usage["candidates"] >= budget["max_candidates"]:
                        break
                    entity = result["frontier"].pop(0)
                    usage["candidates"] += 1
                    result["visited"].append(entity)
                    neighbors = _neighbors(db, lookup, rows, entity, result["intent"])
                    result["active"] = {"entity_id": entity, "neighbors": neighbors, "offset": 0} if neighbors else None
                    continue
                if usage["edges"] >= budget["max_edges"]:
                    break
                neighbor = active["neighbors"][active["offset"]]
                active["offset"] += 1
                usage["edges"] += 1
                _candidate(result, neighbor["entity_id"], "resolved " + neighbor["direction"],
                           {"from": active["entity_id"], **neighbor})
                if active["offset"] == len(active["neighbors"]):
                    result["active"] = None
        # Optimistic concurrency check: do not seal mixed evidence from a writer
        # that changed an artifact or allowed source during this call.
        _stable(stores, bindings, paths, stamps, bound["read_boundary"])
        result["usage"]["seconds"] += time.monotonic() - started
        return _finish(result)


def persist_scope(plan: dict, output: Path, *, authority: dict) -> dict:
    """Publish a new immutable derived artifact; never replace existing evidence."""
    _verify_cursor(plan)
    bound = _authority(plan["boundaries"], authority)
    if bound != plan["boundaries"]:
        raise ValueError("scope authority binding changed")
    root = Path(bound["root"])
    path = _path(output, root)
    manifest = Path(plan["candidate"]["path"])
    if path.parent != manifest.parent or path.suffix != ".json":
        raise ValueError("scope output must be a new JSON sibling of the manifest")
    import embedding_worker
    embedding_worker._publish_json(path, plan)
    return {"schema": "daodan/scope-artifact/v1", "path": str(path),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "input_digest": plan["input_digest"], "status": plan["status"]}
