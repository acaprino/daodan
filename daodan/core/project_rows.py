"""The rows of a project file revision from the map's envelope (`daodan/visual@1`) and from the snapshot's
inventory (`docs/specs/architettura.md`, «File di progetto»). No access to the project file: `project_file` writes
what this module gives.

A row here is a `project_file` row that names itself and the objects it points at by their identity key (`key`, the
envelope's `ref` and the keys derived from it) instead of an object id; `assign` gives the ids.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from pathlib import Path

from project_file import REFERENCES

__all__ = ["POLICY", "PRODUCER", "assign", "from_envelope", "inventory", "source", "tree_sha256"]

PRODUCER = "daodan/visual@1"
POLICY = "daodan/inventory@1"
TECHNOLOGIES = "group:technologies"  # visual.TECHNOLOGIES, not imported: visual reads snapshots and registries
STATUS = {None: "confermato", "confirmed": "confermato", "inferred": "dedotto", "incomplete": "incompleto"}
POSITION = {None: "interno", "internal": "interno", "external": "esterno"}
DESCRIPTIVE = ("description", "languages", "technologies")
FLOW_FIELDS = ("entry_kind", "site", "column", "event", "shape", "complete")
STEP_FIELDS = ("site", "route", "origin", "resolver", "conflict")


def _site(site: str) -> dict:
    """`{kind, locator, start_line}` of a site `path:line` (an identifier, no grammar: split at its last colon, as
    `visual._site`)."""
    path, _, line = site.rpartition(":")
    return {"kind": "source", "locator": path, "start_line": int(line)} if line.isdigit() and int(line) >= 1 \
        else {"kind": "source", "locator": site}


def _evidence(items) -> list[dict]:
    """Source evidence of the analysis from the envelope's `{path, line}`."""
    return [{"kind": "source", "locator": item["path"],
             **({"start_line": item["line"]} if isinstance(item.get("line"), int) and item["line"] >= 1 else {})}
            for item in items if item.get("path")]


def _identity(key: str) -> dict:
    return {"producer": PRODUCER, "key": key}


def from_envelope(envelope: dict, hashes: dict[str, str] | None = None) -> list[dict]:
    """The rows of one revision from an envelope built with `symbols=False`: a node per entity, an edge per
    relation, per logical membership (`member`) and per step of a flow, a flow with one variant without profile per
    envelope flow, and a gap per entity a gap of the envelope names. `hashes` (path -> SHA-256 of the inventory)
    puts each file's digest in its identity, which recognises it after a rename."""
    hashes = hashes or {}
    entities = {item["ref"]: item for item in envelope["entities"]}
    rows: list[dict] = []
    # The parent is the physical membership: the folder that holds an entity, or the group «Tecnologie»; every other
    # membership (a logical module, a build unit) is a `member` edge from the member to its group.
    parents: dict[str, str] = {}
    members = []
    for item in envelope["memberships"]:
        member, group = item["member"], item["group"]
        if member not in parents and (group == TECHNOLOGIES or (item["view"] == "physical" and group.startswith("directory:"))):
            parents[member] = group
        else:
            members.append((member, group))
    for ref, entity in entities.items():
        identity = _identity(ref)
        if entity["type"] == "file":
            identity["path"] = entity["path"]
            if entity["path"] in hashes:
                identity["sha256"] = hashes[entity["path"]]
        status = entity.get("status")
        if status not in STATUS:
            raise ValueError(f"{ref}: stato sconosciuto {status!r}")
        catalog = entity.get("mark") or (ref.split(":", 1)[1] if entity["type"] in ("external", "technology") else None)
        rows.append({"key": ref, "kind": "node", "provenance": "analysis", "evidence": _evidence(entity.get("evidence", ())),
                     "fields": {"parent_id": parents.get(ref), "name": entity["name"], "species": entity["species"],
                                "position": POSITION[entity.get("location")], "status": STATUS[status],
                                "abstraction": "concreto" if entity.get("concrete", True) else "astratto",
                                "catalog_id": catalog,
                                "attributes": {"identity": identity,
                                               **{key: entity[key] for key in DESCRIPTIVE if entity.get(key) not in (None, "", [])}}}})
    for relation in envelope["relations"]:
        if relation["kind"] == "contains" and parents.get(relation["target"]) == relation["source"]:
            continue  # the parent says it
        attributes = {"identity": _identity(relation["ref"]),
                      **{key: relation[key] for key in ("counts", "link_type", "key", "conflict") if key in relation}}
        rows.append({"key": relation["ref"], "kind": "edge", "provenance": "analysis",
                     "evidence": _evidence(relation.get("evidence", ())),
                     "fields": {"source_id": relation["source"], "target_id": relation["target"], "kind": relation["kind"],
                                "grade": relation.get("status") or "confirmed", "profile": None, "attributes": attributes}})
    for member, group in members:
        key = f"member:{member}->{group}"
        rows.append({"key": key, "kind": "edge", "provenance": "analysis",
                     "fields": {"source_id": member, "target_id": group, "kind": "member", "grade": "confirmed",
                                "profile": None, "attributes": {"identity": _identity(key)}}})
    step_edges: set[str] = set()
    for flow in envelope["flows"]:
        ref = flow["ref"]
        variant = f"{ref}#variant"
        rows.append({"key": ref, "kind": "flow", "provenance": "analysis",
                     "fields": {"name": flow.get("label") or entities[flow["entry"]]["name"], "feature_id": None,
                                "attributes": {"identity": _identity(ref),
                                               **{key: flow[key] for key in FLOW_FIELDS if key in flow}}}})
        rows.append({"key": variant, "kind": "variant", "provenance": "analysis",
                     "fields": {"flow_id": ref, "name": "predefinita", "profile": None, "condition": None},
                     "endpoints": [{"role": "entry", "node_id": flow["entry"]}]})
        for order, step in enumerate(flow["steps"]):
            edge = f"step:{step['type']}:{step['source']}->{step['target']}@{step.get('site')}"
            if edge not in step_edges:  # two steps may walk the same edge
                step_edges.add(edge)
                rows.append({"key": edge, "kind": "edge", "provenance": "analysis",
                             "evidence": [_site(step["site"])] if step.get("site") else [],
                             "fields": {"source_id": step["source"], "target_id": step["target"], "kind": step["type"],
                                        "grade": step.get("confidence") or "confirmed", "profile": None,
                                        "attributes": {"identity": _identity(edge),
                                                       **{key: step[key] for key in STEP_FIELDS if key in step}}}})
            following = order + 1 < len(flow["steps"])
            rows.append({"key": f"{ref}#step:{order}", "kind": "step", "provenance": "analysis",
                         "fields": {"variant_id": variant, "display_order": order, "label": step["type"]},
                         "edges": [edge], "transitions": [{"to_step_id": f"{ref}#step:{order + 1}"}] if following else []})
        for number, gap in enumerate(flow.get("gaps", ())):
            reason = gap["reason"]
            rows.append({"key": f"{ref}#gap:{number}", "kind": "gap", "provenance": "analysis",
                         "evidence": [_site(gap["site"])] if gap.get("site") else [],
                         "fields": {"subject_id": ref, "description": reason, "cause": reason, "remedy": None}})
    number = 0
    for gap in envelope["gaps"]:
        for subject in gap.get("refs") or [None]:
            known = subject in entities
            description = gap["reason"] if known or subject is None else f"{gap['reason']} ({subject})"
            rows.append({"key": f"gap:{number}", "kind": "gap", "provenance": "analysis",
                         "fields": {"subject_id": subject if known else None, "description": description,
                                    "cause": gap["reason"], "remedy": None}})
            number += 1
    return rows


def assign(rows: list[dict], ids: dict[str, str]) -> list[dict]:
    """The rows with their object `id` and object ids in place of the keys they point at: the id `ids` gives a key,
    else a new UUID. A key no row has and `ids` does not give is an error."""
    ids = dict(ids)
    for row in rows:
        ids.setdefault(row["key"], str(uuid.uuid4()))

    def ref(key):
        if key is None:
            return None
        if key not in ids:
            raise ValueError(f"riferimento a un oggetto sconosciuto: {key}")
        return ids[key]

    out = []
    for row in rows:
        new = {**row, "id": ids[row["key"]],
               "fields": {**row["fields"], **{name: ref(row["fields"].get(name)) for name in REFERENCES[row["kind"]]}}}
        if "endpoints" in row:
            new["endpoints"] = [{**item, "node_id": ref(item["node_id"])} for item in row["endpoints"]]
        if "edges" in row:
            new["edges"] = [ref(item) for item in row["edges"]]
        if "transitions" in row:
            new["transitions"] = [{**item, "to_step_id": ref(item["to_step_id"])} for item in row["transitions"]]
        out.append(new)
    return out


def tree_sha256(hashes: dict[str, str]) -> str:
    """The perimeter's digest of «Identità e storia»: in binary order of the UTF-8 relative paths, for each file the
    path's length in bytes (unsigned 64-bit big endian), the path and the binary SHA-256 of its bytes; the lowercase
    hexadecimal SHA-256 of the whole."""
    digest = hashlib.sha256()
    for encoded, path in sorted((path.encode("utf-8"), path) for path in hashes):
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
        digest.update(bytes.fromhex(hashes[path]))
    return digest.hexdigest()


def _listed(manifest: Path) -> tuple[dict[str, str], object]:
    from snapshot_store import open_snapshot
    with open_snapshot(Path(manifest)) as store:
        return {path: row["raw_hash"] for path, row in store.iter_listed()}, store.get("scope")


def inventory(manifest: Path) -> dict[str, str]:
    """Path -> SHA-256 of the bytes read, for every file the snapshot's inventory lists."""
    return _listed(manifest)[0]


def source(manifest: Path, commit: str | None = None, committed_at: str | None = None,
           repository_uri: str | None = None) -> dict:
    """The `source_snapshots` row of the snapshot at `manifest`: the commit and its date when the checkout has them,
    and always the perimeter's digest with the inventory policy and the header's `scope`."""
    hashes, scope = _listed(manifest)
    return {"repository_uri": repository_uri, "git_commit": commit, "git_committed_at": committed_at if commit else None,
            "tree_sha256": tree_sha256(hashes),
            "inventory_policy": json.dumps({"policy": POLICY, "scope": scope}, sort_keys=True)}
