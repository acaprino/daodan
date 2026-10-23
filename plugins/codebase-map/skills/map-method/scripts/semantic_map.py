"""Render canonical cards and verified static relations without model calls."""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
from pathlib import Path
import re
import tempfile

import card_store
import migrate_root
import semantic_store
import snapshot
import source_reader
from snapshot_store import artifact_digest, logical_digest, open_snapshot, _unpack
from store_consumers import consumer_reader

SCHEMA = "daodan/semantic-map/v1"
RENDERER_VERSION = 1
SEMANTIC_FIELDS = ("purpose", *card_store.CARD_LIST_KEYS)
FRESHNESS = ("fresh", "stale_body", "stale_interface", "stale_callee", "unread", "orphan")


def _json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def _text(value):
    text = html.escape(str(value), quote=True).replace("\n", " ").replace("\r", " ")
    return re.sub(r"([\\`*_{}\[\]()#!|~])", r"\\\1", text)


def _anchor(identity):
    return "entity-" + hashlib.sha256(identity.encode("utf-8")).hexdigest()


def _code(value):
    text = str(value).replace("\n", " ").replace("\r", " ")
    fence = "`" * (1 + max((len(run) for run in re.findall(r"`+", text)), default=0))
    return f"{fence} {text} {fence}"


def _link(label, path, line=None):
    url = Path(path).as_uri() + (f"#L{line}" if line is not None else "")
    return f"[{_text(label)}](<{url}>)"


def _plain(path):
    migrate_root._reject_link_chain(path)
    if path.exists() and (not path.is_file() or path.stat().st_nlink != 1):
        raise ValueError(f"artifact must be a regular file without aliases: {path}")


def _digest(path):
    _plain(path)
    return artifact_digest(path) if path.exists() else None


def _destination(manifest, out):
    manifest = Path(manifest).absolute()
    _plain(manifest)
    root = card_store.default_cards_path(manifest).parent
    output = Path(out).absolute() if out is not None else root / "semantic-map.md"
    if (".." in output.parts or output.parent.resolve() != root
            or not re.fullmatch(r"semantic-map(?:-[a-z0-9][a-z0-9-]{0,63})?\.md", output.name)):
        raise ValueError("map output must be semantic-map[-slug].md in the canonical analysis root")
    _plain(output)
    _plain(output.with_suffix(".json"))
    return manifest, output


def _inventory(store):
    root, target, perimeter = source_reader._binding(store)
    current = {path.relative_to(root).as_posix() for path in snapshot.iter_files(target, perimeter)
               if path.stat().st_size <= snapshot.MAX_FILE_BYTES}
    if current != set(store.iter_paths()):
        raise ValueError("source inventory changed; refresh the snapshot before rendering")
    return current


def _select(paths, inventory, card_rows):
    if paths is None:
        return None, sorted(inventory)
    if not isinstance(paths, list) or not paths:
        raise ValueError("paths must be a nonempty list, or omitted for the whole target")
    requested = sorted({source_reader._relative(path) for path in paths})
    known = inventory | {row[1] for row in card_rows}
    for area in requested:
        if not any(path == area or path.startswith(area + "/") for path in known):
            raise ValueError(f"area is absent from the snapshot and canonical cards: {area}")
    return requested, sorted(path for path in inventory if _selected(path, requested))


def _selected(path, requested):
    return requested is None or any(path == area or path.startswith(area + "/") for area in requested)


def _card_provenance(row):
    if row is None:
        return None
    return dict(zip(("body_hash", "interface_hash", "effects_hash", "callee_digest", "updated_at"), row[3:]))


def _require_verified_entities(store, db):
    for (file,) in db.execute("SELECT file FROM q_cover WHERE verified<>1 ORDER BY file"):
        # A rebuilt consumer index can omit symbols; consult the bound inventory.
        if store.get_file(file, semantic=False).get("symbols"):
            raise ValueError(f"cannot verify inventoried symbols in {file}; refresh the snapshot")


def _graph(store, db, selected):
    index = semantic_store._ImpactIndex(db)
    coverage = {file: {**_unpack(payload), "verified": bool(verified)}
                for file, verified, payload in db.execute("SELECT file,verified,payload FROM q_cover ORDER BY file")}
    calls = []
    for file, line, target, payload in db.execute(
            "SELECT file,l0,target_id,payload FROM effective_references WHERE kind='call' ORDER BY file,l0,c0,l1,c1,id"):
        caller = index.enclosing(file, line)
        callee = index.symbol_for_declaration(target) if target else None
        if file not in selected and (callee is None or callee[1] not in selected):
            continue
        ref = _unpack(payload)
        verified = coverage[file]["verified"] and (callee is None or coverage[callee[1]]["verified"])
        calls.append({**ref, "caller_entity_id": caller[0] if caller else None,
                      "target_entity_id": callee[0] if callee and verified and ref.get("resolution") == "resolved" else None,
                      "verified": verified})
    return {"calls": calls, "metadata": _unpack(db.execute("SELECT payload FROM effective_metadata").fetchone()[0]),
            "metadata_scope": "snapshot",
            "files": {path: coverage[path] for path in sorted(selected)}}


def _reports(manifest, output):
    # Existing phase reports are references, never a second source of card text.
    directories = {output.parent}
    run = manifest.parent.parent
    if manifest.parent.name == "snapshot" and run.parent.name == "runs" and (run / "state.json").is_file():
        directories.add(run)
    found = []
    for directory in sorted(directories):
        for path in sorted(directory.glob("[0-9][0-9]-*.md")):
            _plain(path)
            found.append(str(path))
    return sorted(set(found))


def _render(report):
    counts = report["coverage"]
    root = Path(report["snapshot"]["root"])
    lines = ["# Semantic code map", "", "Generated from canonical cards and verified static evidence.", "",
             f"Inventory files: {counts['inventory_files']}; selected files: {counts['selected_files']}; symbols: {counts['symbols']}.",
             "Application runtime coverage: none. Card freshness basis: lexical.",
             "Renderer LLM calls: 0. Card-generation LLM token cost: unknown (not recorded by the card store).", "",
             "Cards: " + "; ".join(f"{state}: {counts['cards'][state]}" for state in FRESHNESS) + ".", "",
             "## Areas and files", ""]
    entities = report["entities"]
    selected_ids = {entity["entity_id"] for entity in entities}
    for path in report["query"]["selected_files"]:
        file_anchor = _anchor("file:" + path)
        lines.append(f"- [{_text(path)}](#{file_anchor}) (area: {_text(Path(path).parent.as_posix())})")
    for path in report["query"]["selected_files"]:
        lines.extend(["", f'<a id="{_anchor("file:" + path)}"></a>', f"## {_text(path)}", "",
                      _link("Source", root / path), "",
                      "Static coverage: " + _text(report["graph"]["files"][path].get("status", "unavailable")) + "."])
        items = [entity for entity in entities if entity["anchor"]["file"] == path]
        if not items:
            lines.extend(["", "No inventoried symbols. Semantic coverage of this file is unavailable."])
        for entity in items:
            identity = entity["entity_id"]
            lines.extend(["", f'<a id="{_anchor(identity)}"></a>', f"### {_code(identity)}", "",
                          _link("Source", root / path, entity["anchor"]["start_line"]),
                          "", "Card: " + entity["freshness"] + "."])
            if entity["stale_reason"]:
                lines.append("Reason: " + _text(entity["stale_reason"]) + ".")
            card = entity["card"]
            if card is None:
                lines.append("Semantic fields unavailable; requires source reading: " + ", ".join(SEMANTIC_FIELDS) + ".")
                continue
            for field in SEMANTIC_FIELDS:
                label = field.replace("_", " ").capitalize()
                if card is None or field not in card or (field == "purpose" and not card[field].strip()):
                    value = "unavailable; requires source reading"
                elif isinstance(card[field], list):
                    value = "; ".join(_text(item) for item in card[field]) if card[field] else "none recorded by the card"
                else:
                    value = _text(card[field])
                lines.append(f"- {label}: {value}")
            for field in ("confidence", "notes"):
                if card and field in card:
                    lines.append(f"- {field.capitalize()}: {_text(card[field])}")
    lines.extend(["", "## Static calls", "", "Unresolved calls and candidates do not establish confirmed targets.", ""])
    for call in report["graph"]["calls"]:
        caller, target = call["caller_entity_id"], call["target_entity_id"]

        def relation(identity, fallback):
            if identity in selected_ids:
                return f"[{_text(identity)}](#{_anchor(identity)})"
            return _text(identity or fallback) + (" (outside selected area)" if identity else "")

        lines.append(f"- {relation(caller, call.get('file', 'unknown caller'))} -> "
                     f"{relation(target, 'unresolved')} ({_text(call.get('resolver', 'lexical'))}; "
                     f"{_text(call.get('reason', call.get('resolution', 'unavailable')))}")
    metadata = report["graph"]["metadata"]
    lines.extend(["", "Snapshot-wide engine coverage: " + _text(metadata["coverage"].get("status", "unavailable")) + ".",
                  "Conflicts: " + str(metadata["conflicts"]["total"]) + "; candidates: " + str(metadata["candidates"]["total"]) + "."])
    for gap in metadata["gaps"]:
        lines.append("- Graph gap: " + _text(gap))
    lines.extend(["", "## Orphan cards", ""])
    for orphan in report["orphans"]:
        lines.append("- " + _text(orphan["entity_id"]) + ": orphan; no current source anchor.")
    lines.extend(["", "## Reading needed", "",
                  "Use map-method's existing deepen method for the listed entities in the selected area. "
                  "Reuse complete fresh cards; fill partial cards through source reading. This renderer dispatches no analyst.", ""])
    for request in report["reading_requests"]:
        lines.append("- " + _text(request["entity_id"]) + ": " + request["freshness"] + "; missing: "
                     + ", ".join(request["missing_fields"]))
    lines.extend(["", "## Provenance", "", _link("Machine-readable provenance", Path(report["provenance"])), "",
                  "Snapshot logical digest: " + report["snapshot"]["logical_digest"],
                  "Cards digest: " + (report["cards"]["artifact_digest"] or "missing store"), ""])
    lines.extend(_link(Path(path).name, Path(path)) for path in report["phase_reports"])
    return "\n".join(lines) + "\n"


def _previous(output, provenance, root):
    previous = {path: path.read_bytes() if path.exists() else None for path in (output, provenance)}
    if any(value is not None for value in previous.values()):
        try:
            report = json.loads(previous[provenance])
            valid = (report["schema"] == SCHEMA and report["output"] == str(output)
                     and report["provenance"] == str(provenance) and report["snapshot"]["root"] == root
                     and report["artifact_digest"] == hashlib.sha256(previous[output]).hexdigest())
        except (ValueError, TypeError, KeyError):
            valid = False
        if not valid:
            raise ValueError("existing map outputs are not an intact renderer-owned pair")
    return previous


def _publish(contents, previous):
    staged, replaced = {}, []

    def stage(path, data):
        descriptor, name = tempfile.mkstemp(prefix=".semantic-map-", dir=path.parent)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
        return Path(name)

    try:
        for path, data in contents.items():
            staged[path] = stage(path, data)
        for path, temporary in staged.items():
            _plain(path)
            if (path.read_bytes() if path.exists() else None) != previous[path]:
                raise ValueError("map output changed while rendering; publication refused")
            os.replace(temporary, path)
            replaced.append(path)
    except BaseException:
        for path in reversed(replaced):
            if previous[path] is None:
                path.unlink()
            else:
                backup = stage(path, previous[path])
                try:
                    os.replace(backup, path)
                finally:
                    backup.unlink(missing_ok=True)
        raise
    finally:
        for temporary in staged.values():
            temporary.unlink(missing_ok=True)


def render_map(manifest, *, cards_path=None, paths=None, out=None, engine_store=None) -> dict:
    manifest, output = _destination(manifest, out)
    provenance = output.with_suffix(".json")
    cards = Path(cards_path).absolute() if cards_path is not None else card_store.default_cards_path(manifest)
    engine = Path(engine_store).absolute() if engine_store is not None else manifest.with_name("engine-edges.sqlite")
    inputs = {path: _digest(path) for path in (manifest, cards, engine)}
    if {output.resolve(), provenance.resolve()} & {path.resolve() for path in inputs}:
        raise ValueError("map outputs must be separate from their evidence inputs")
    lock = output.with_suffix(".lock")
    _plain(lock)
    descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(descriptor)
    try:
        with open_snapshot(manifest, expected_format="sqlite") as store:
            inventory = _inventory(store)
            card_rows = card_store.digests(cards, store["root"])
            requested, selected = _select(paths, inventory, card_rows)
            card_by_id = {row[0]: row for row in card_rows}
            previous = _previous(output, provenance, store["root"])
            entries = {path: store.get_file(path, semantic=False) for path in selected}
            count = sum(len(entry.get("symbols") or {}) for entry in entries.values())
            with consumer_reader(store, engine_store=engine) as db:
                _require_verified_entities(store, db)
                graph = _graph(store, db, set(selected))
            queried = semantic_store.query_meta_code(store, cards_path=cards, paths=selected,
                                                    include_history=False, limit=max(1, count)) if selected else {"symbols": []}
            entities = []
            for row in queried["symbols"]:
                entry = entries[row["file"]]
                record = snapshot._entity_record(store, row["file"], entry, row["name"], entry["symbols"][row["name"]])
                fresh = "unread" if row["freshness"] == "uncovered" else row["freshness"]
                card = row["card"] if fresh == "fresh" else None
                missing = [field for field in SEMANTIC_FIELDS if card is None or field not in card
                           or (field == "purpose" and not card[field].strip())]
                entities.append({**record, **{key: row[key] for key in ("body_hash", "interface_hash", "effects_hash")},
                                 "freshness": fresh, "freshness_basis": "lexical", "stale_reason": row["stale_reason"],
                                 "card": card, "card_provenance": _card_provenance(card_by_id.get(row["symbol_id"])),
                                 "missing_fields": missing})
            if len(entities) != count:
                raise ValueError("semantic symbol inventory is incomplete; refresh the snapshot")
            orphan_rows = semantic_store.query_meta_code(store, cards_path=cards, freshness="orphan",
                                                        include_history=False, limit=max(1, len(card_rows)))["orphans"]
            orphans = [{"entity_id": row["symbol_id"], "file": row["file"], "freshness": "orphan",
                        "card_provenance": _card_provenance(card_by_id[row["symbol_id"]])}
                       for row in orphan_rows if _selected(row["file"], requested)]
            counts = {state: sum(entity["freshness"] == state for entity in entities) for state in FRESHNESS}
            counts["orphan"] = len(orphans)
            report = {"schema": SCHEMA, "renderer_version": RENDERER_VERSION,
                      "snapshot": {"manifest": str(manifest), "logical_digest": logical_digest(store),
                                   **{key: store.get(key) for key in ("root", "target", "scope", "git", "created_at", "parser_fingerprint")},
                                   "resolver_version": semantic_store.RESOLVER_VERSION},
                      "cards": {"path": str(cards), "artifact_digest": inputs[cards]},
                      "engine_store": {"path": str(engine), "artifact_digest": inputs[engine]},
                      "query": {"paths": requested, "selected_files": selected},
                      "coverage": {"inventory_files": len(inventory), "selected_files": len(selected), "symbols": count,
                                   "cards": counts, "runtime_files": 0},
                      "entities": entities, "orphans": orphans, "graph": graph,
                      "reading_requests": [{"entity_id": entity["entity_id"], "freshness": entity["freshness"],
                                            "missing_fields": entity["missing_fields"]} for entity in entities
                                           if entity["freshness"] != "fresh" or entity["missing_fields"]],
                      "phase_reports": _reports(manifest, output), "output": str(output), "provenance": str(provenance),
                      "llm_calls": 0, "card_llm_tokens": None}
            markdown = _render(report).encode("utf-8")
            report["artifact_digest"] = hashlib.sha256(markdown).hexdigest()
            _inventory(store)
            with consumer_reader(store, engine_store=engine) as db:
                _require_verified_entities(store, db)
            if any(_digest(path) != digest for path, digest in inputs.items()):
                raise ValueError("snapshot, cards or engine evidence changed during rendering")
            _publish({output: markdown, provenance: _json(report).encode("utf-8")}, previous)
            return report
    finally:
        lock.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--cards-path", type=Path)
    parser.add_argument("--path", action="append", dest="paths")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--engine-store", type=Path)
    args = parser.parse_args()
    try:
        report = render_map(**vars(args))
    except (OSError, ValueError) as error:
        parser.exit(1, f"semantic map: {error}\n")
    print(_json({key: report[key] for key in ("output", "provenance", "coverage", "llm_calls")}))


if __name__ == "__main__":
    main()
