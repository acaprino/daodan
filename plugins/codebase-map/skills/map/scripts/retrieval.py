"""Snapshot-bound, incremental local code retrieval. No model or network calls."""
from __future__ import annotations

from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import tempfile
import time

import confinement
import snapshot
import source_reader
from snapshot_store import open_snapshot, logical_digest, artifact_digest

SCHEMA = "daodan/retrieval-index/v1"
DOCUMENT_VERSION = 1
TOKENIZER_VERSION = "subtokens-unicode-v1"
RANKING_VERSION = "exact-fts5-bm25-v1"


def subtokens(text):
    tokens = []
    for word in re.findall(r"[^\W_]+", text, re.UNICODE):
        word = re.sub(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])", " ", word)
        tokens.extend(part.lower() for part in word.split())
    return tokens


def _json(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _digest(value):
    return hashlib.sha256(_json(value).encode()).hexdigest()


def _read(path):
    return sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)


def _require_fts5(db):
    try:
        db.execute("CREATE VIRTUAL TABLE temp.fts_probe USING fts5(value)")
        db.execute("DROP TABLE temp.fts_probe")
    except sqlite3.OperationalError as error:
        if "no such module" in str(error).lower():
            raise ValueError("SQLite FTS5 unavailable; use a Python runtime with FTS5") from error
        raise


def _binding(store):
    return {"manifest": str(store.path.resolve()), "manifest_digest": logical_digest(store),
            "root": store.get("root"), "target": store.get("target"), "scope": store.get("scope"),
            "parser_fingerprint": store.get("parser_fingerprint"), "schema": SCHEMA,
            "document_version": DOCUMENT_VERSION, "tokenizer": TOKENIZER_VERSION,
            "ranking": RANKING_VERSION, "sqlite_version": sqlite3.sqlite_version}


def _verify_tree(store):
    root, target, perimeter = source_reader._binding(store)
    actual = {p.relative_to(root).as_posix() for p in snapshot.iter_files(target, perimeter)}
    if actual != set(store.iter_paths()):
        raise ValueError("source inventory changed; refresh the snapshot before retrieval")
    # Verify every dependency in one reader pass, including empty files and
    # files without symbols. Per-file packets would rebuild the Git perimeter
    # for every source and make each search pay that process cost repeatedly.
    source_reader.read_packet(store, [{"path": rel, "full_file": True} for rel in sorted(actual)])


def _documents(store):
    entries = list(store.iter_files(semantic=False))
    packet = source_reader.read_packet(
        store, [{"path": rel, "full_file": True} for rel, _entry in entries])
    sources = {file["path"]: file["blocks"][0]["source"] for file in packet["files"]}
    for rel, entry in entries:
        numbered = sources[rel]
        lines = [line.split(": ", 1)[1] for line in numbered.removesuffix("\n").split("\n")]
        symbols = dict(entry.get("symbols") or {})
        covered = set()
        for spec in symbols.values():
            start, end = spec.get("start"), spec.get("end")
            if type(start) is not int or type(end) is not int or not 1 <= start <= end <= len(lines):
                raise ValueError(f"invalid symbol span: {rel}; refresh the snapshot")
            covered.update(range(start, end + 1))
        symbols.setdefault("@file", {
            "kind": "file", "start": 1, "end": entry["lines"], "span_precision": "file",
            "hash": entry.get("hash"), "signatures": [],
        })
        for name, spec in sorted(symbols.items()):
            record = snapshot._entity_record(store, rel, entry, name, spec)
            start, end = spec.get("start"), spec.get("end")
            if type(start) is not int or type(end) is not int or not 1 <= start <= end <= len(lines):
                raise ValueError(f"invalid symbol span: {rel}::{name}; refresh the snapshot")
            # Keep imports, configuration and other non-symbol text searchable
            # without duplicating symbol bodies in the file context document.
            body = "\n".join(line for number, line in enumerate(lines[start - 1:end], start)
                             if name != "@file" or number not in covered)
            signature = _json(record["signatures"])
            document = {"record": record, "name": name, "path": rel, "signature": signature,
                        "body": body, "parser": entry.get("parser_profile"),
                        "version": DOCUMENT_VERSION, "tokenizer": TOKENIZER_VERSION}
            yield record["entity_id"], document, _digest(document)


def _destination(manifest, index_path):
    manifest, index_path = Path(manifest).absolute(), Path(index_path).absolute()
    confinement.reject_link_chain(manifest)
    confinement.reject_link_chain(index_path)
    if (index_path.parent.resolve() != manifest.parent.resolve()
            or index_path.resolve() == manifest.resolve() or index_path.suffix != ".sqlite"):
        raise ValueError("retrieval index must be a separate SQLite file beside its manifest")
    return manifest, index_path


def refresh_index(manifest: Path, index_path: Path) -> dict:
    manifest, index_path = _destination(manifest, index_path)
    lock = index_path.with_name(index_path.name + ".lock")
    descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(descriptor)
    temporary = None
    try:
        with open_snapshot(manifest) as store:
            binding = _binding(store)
            _verify_tree(store)
            manifest_bytes = artifact_digest(manifest)
            index_before = artifact_digest(index_path) if index_path.exists() else None
            docs = dict((identity, (doc, digest)) for identity, doc, digest in _documents(store))
            descriptor, name = tempfile.mkstemp(prefix=".retrieval-", suffix=".sqlite", dir=index_path.parent)
            os.close(descriptor)
            temporary = Path(name)
            with closing(sqlite3.connect(temporary)) as db:
                _require_fts5(db)
                previous = {}
                mode = "rebuild"
                if index_before:
                    with closing(_read(index_path)) as old:
                        metadata = json.loads(old.execute("SELECT value FROM metadata").fetchone()[0])
                        compatible = all(metadata["binding"].get(k) == binding.get(k) for k in
                                         ("schema", "document_version", "tokenizer", "ranking", "root", "target", "parser_fingerprint"))
                        if compatible:
                            old.backup(db)
                            previous = dict(db.execute("SELECT entity_id,digest FROM documents"))
                            mode = "incremental"
                if mode == "rebuild":
                    db.execute("CREATE TABLE metadata(value TEXT NOT NULL)")
                    db.execute("CREATE TABLE documents(entity_id TEXT PRIMARY KEY,digest TEXT NOT NULL,record TEXT NOT NULL)")
                    db.execute("CREATE VIRTUAL TABLE search_text USING fts5(entity_id UNINDEXED,name,path,signature,body)")
                removed = set(previous) - set(docs)
                changed = {key for key in docs if previous.get(key) != docs[key][1]}
                for key in sorted(removed | changed):
                    db.execute("DELETE FROM search_text WHERE entity_id=?", (key,))
                    db.execute("DELETE FROM documents WHERE entity_id=?", (key,))
                for key in sorted(changed):
                    document, digest = docs[key]
                    db.execute("INSERT INTO documents VALUES(?,?,?)", (key, digest, _json(document["record"])))
                    db.execute("INSERT INTO search_text VALUES(?,?,?,?,?)", (key, *(
                        " ".join(subtokens(document[field])) for field in ("name", "path", "signature", "body"))))
                metadata = {"binding": binding, "document_digest": _digest(sorted((k, d[1]) for k, d in docs.items())),
                            "documents": len(docs), "dependencies": "snapshot inventory and verified source; no environment, graph or card inputs"}
                db.execute("DELETE FROM metadata")
                db.execute("INSERT INTO metadata VALUES(?)", (_json(metadata),))
                db.commit()
                if db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                    raise ValueError("retrieval index integrity check failed")
            _verify_tree(store)
            if artifact_digest(manifest) != manifest_bytes:
                raise ValueError("snapshot changed during indexing; retry with a stable snapshot")
            if (artifact_digest(index_path) if index_path.exists() else None) != index_before:
                raise ValueError("retrieval index changed during refresh; previous generation retained")
            confinement.reject_link_chain(index_path)
            os.replace(temporary, index_path)
            return {"schema": SCHEMA, "binding": binding, "mode": mode, "documents": len(docs),
                    "inserted": len(set(docs) - set(previous)), "updated": len(changed & set(previous)),
                    "removed": len(removed), "reused": len(docs) - len(changed),
                    "document_digest": metadata["document_digest"], "artifact_digest": artifact_digest(index_path)}
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
        lock.unlink()


def _anchor_records(store, records, anchor):
    if not isinstance(anchor, dict) or set(anchor) - {"entity_id", "path", "symbol", "line", "start", "end"}:
        raise ValueError("invalid retrieval anchor")
    path, symbol, identity = anchor.get("path"), anchor.get("symbol"), anchor.get("entity_id")
    if not anchor or any(v is not None and (not isinstance(v, str) or not v) for v in (path, symbol, identity)):
        raise ValueError("anchor needs a nonempty path, symbol or entity_id")
    selected = list(records.values())
    if path is not None:
        source_reader._relative(path)
        if not store.has_file(path):
            raise ValueError("anchor path is not inventoried")
        selected = [r for r in selected if r["anchor"]["file"] == path]
    if identity is not None:
        if identity not in records:
            raise ValueError("anchor entity_id is not inventoried")
        selected = [r for r in selected if r["entity_id"] == identity]
    if symbol is not None:
        selected = [r for r in selected if r["entity_id"].split("::", 1)[1] == symbol]
    if any(k in anchor for k in ("line", "start", "end")):
        if path is None:
            raise ValueError("line anchors require a path")
        start = anchor.get("line", anchor.get("start"))
        end = anchor.get("end", start)
        if type(start) is not int or type(end) is not int or not 1 <= start <= end <= store.get_file(path)["lines"]:
            raise ValueError("anchor line range is outside the file")
        selected = [r for r in selected if r["anchor"]["start_line"] <= end and r["anchor"]["end_line"] >= start]
        if "line" in anchor and selected:
            width = min(r["anchor"]["end_line"] - r["anchor"]["start_line"] for r in selected)
            selected = [r for r in selected if r["anchor"]["end_line"] - r["anchor"]["start_line"] == width]
    ambiguous = path is None and identity is None and len(selected) > 1
    return sorted(selected, key=lambda r: r["entity_id"]), ambiguous


INDEX_STATES = ("fresh", "missing", "stale", "corrupt", "failed")
_BINDING_KEYS = ("schema", "document_version", "tokenizer", "ranking", "root", "target", "scope",
                 "parser_fingerprint", "manifest", "manifest_digest", "sqlite_version")


def index_name(manifest: Path) -> Path:
    """The lexical index of a manifest: `retrieval.sqlite` beside it."""
    return Path(manifest).with_name("retrieval.sqlite")


def index_state(manifest: Path, index_path: Path | None = None) -> dict:
    """Report the index without touching it: fresh, missing, stale or corrupt.

    `fresh` means the stored binding equals the manifest's current binding, so
    `search` would accept it. `stale` names the binding keys that differ.
    `corrupt` covers a file that is not a readable index of this schema.
    Invalid paths raise, as `refresh_index` does.
    """
    manifest, index_path = _destination(manifest, index_path or index_name(manifest))
    if not manifest.is_file():
        raise ValueError(f"manifest does not exist: {manifest}")
    report = {"index": str(index_path), "manifest": str(manifest)}
    lock = index_path.with_name(index_path.name + ".lock")
    if lock.exists():
        report["lock"] = str(lock)
        report["lock_age_s"] = round(max(0.0, time.time() - lock.stat().st_mtime), 1)
    if not index_path.exists():
        return {**report, "state": "missing", "reason": "no retrieval index beside the manifest"}
    try:
        with closing(_read(index_path)) as db:
            metadata = json.loads(db.execute("SELECT value FROM metadata").fetchone()[0])
            stored = metadata["binding"]
            documents = metadata["documents"]
            if not isinstance(stored, dict):
                raise KeyError("binding")
    except sqlite3.OperationalError as error:
        # The file exists but cannot be opened or queried: a sharing violation, a
        # missing table. Not a verdict on its content, so nothing is deleted.
        return {**report, "state": "failed", "reason": f"cannot read the retrieval index: {error}"}
    except (sqlite3.DatabaseError, TypeError, KeyError, ValueError, json.JSONDecodeError) as error:
        return {**report, "state": "corrupt", "reason": f"not a readable retrieval index: {error}"}
    with open_snapshot(manifest) as store:
        current = _binding(store)
    differing = [key for key in _BINDING_KEYS if stored.get(key) != current.get(key)]
    if differing or stored != current:
        return {**report, "state": "stale", "documents": documents,
                "reason": "binding differs: " + ", ".join(differing or sorted(set(stored) ^ set(current)))}
    return {**report, "state": "fresh", "documents": documents, "binding": current}


def ensure_index(manifest: Path, index_path: Path | None = None, *, check: bool = False,
                 break_lock: bool = False) -> dict:
    """Repair the index unless `check`: rebuild `missing`, `stale` and `corrupt`.

    Returns the final `state` plus `action` (`none`, `reported`, `rebuilt`,
    `refreshed`), the reason of a non-fresh state and the `refresh_index`
    result when one ran. `failed` carries the message of an unavailable FTS5,
    a held lock or a write error, and leaves the previous generation in place.
    A lock is a bare file without an owner, so a lock left by a crashed build
    is removed only on an explicit `break_lock`, together with the crashed
    build's `.retrieval-*.sqlite` temporaries.
    """
    before = index_state(manifest, index_path)
    if before["state"] == "fresh" and not (break_lock and "lock" in before):
        return {**before, "action": "none"}
    if check:
        return {**before, "action": "reported"}
    manifest, index_path = _destination(manifest, index_path or index_name(manifest))
    lock = index_path.with_name(index_path.name + ".lock")
    if break_lock and lock.exists():
        confinement.reject_link_chain(lock)
        lock.unlink()
        for leftover in index_path.parent.glob(".retrieval-*.sqlite"):
            confinement.reject_link_chain(leftover)
            leftover.unlink()
        before = dict(index_state(manifest, index_path), lock_broken=str(lock))
        if before["state"] == "fresh":
            return {**before, "action": "none"}
    try:
        if before["state"] == "corrupt":
            confinement.reject_link_chain(index_path)
            index_path.unlink()
        elif before["state"] == "failed":
            return {**before, "action": "none"}
        refresh = refresh_index(manifest, index_path)
    except FileExistsError as error:
        return {**before, "state": "failed", "action": "none", "lock": str(lock),
                "reason": f"index lock held: {error.filename or lock}; a crashed build leaves it, break_lock removes it"}
    except (ValueError, OSError, sqlite3.Error) as error:
        return {**before, "state": "failed", "action": "none", "reason": str(error)}
    after = index_state(manifest, index_path)
    action = "rebuilt" if refresh["mode"] == "rebuild" else "refreshed"
    broken = {"lock_broken": before["lock_broken"]} if "lock_broken" in before else {}
    return {**after, **broken, "action": action, "previous": before["state"], "refresh": refresh}


def gap_result(state: dict, limit: int, repair: str) -> dict:
    """The search envelope when the index is not fresh: no results, one gap naming the repair."""
    return {"schema": "daodan/retrieval-result/v1", "document_digest": None, "results": [], "exact": [],
            "exact_total": 0, "exact_truncated": 0, "ambiguous": [], "matched": 0, "returned": 0, "truncated": 0,
            "limit": limit, "ranking_policy": None,
            "capabilities": {"exact": False, "fts5": False, "embedding": "unavailable"},
            "index_state": state["state"], "gaps": [f"retrieval_{state['state']}: {state['reason']}; run {repair}"]}


def public_result(result: dict) -> dict:
    """The search envelope for agents: the ranking metadata and trimmed records, no source text."""
    records = []
    for record in result["results"]:
        anchor = record.get("anchor") or {}
        records.append({"entity_id": record["entity_id"], "kind": (record.get("entity_key") or {}).get("kind"),
                        "path": anchor.get("file"), "start_line": anchor.get("start_line"),
                        "end_line": anchor.get("end_line"), "signatures": record.get("signatures") or [],
                        "provenance": record.get("provenance") or [], "score": record.get("score")})
    keep = ("schema", "document_digest", "exact", "exact_total", "exact_truncated", "ambiguous", "matched",
            "returned", "truncated", "limit", "gaps", "ranking_policy", "capabilities")
    return {**{key: result[key] for key in keep if key in result}, "results": records}


def search(index_path: Path, query: str, *, anchors: list[dict], limit: int,
           embedding_result: dict | None = None, verify: bool = True) -> dict:
    """Rank the index for `query`. `verify=False` skips the whole-tree read and keeps the binding check."""
    if not isinstance(query, str) or len(query) > 16_384:
        raise ValueError("query must be text of at most 16384 characters")
    if not isinstance(anchors, list) or len(anchors) > 100:
        raise ValueError("anchors must be a list of at most 100 anchors")
    if type(limit) is not int or not 1 <= limit <= 1000:
        raise ValueError("limit must be an integer from 1 through 1000")
    index_path = Path(index_path)
    confinement.reject_link_chain(index_path)
    with closing(_read(index_path)) as db:
        _require_fts5(db)
        metadata = json.loads(db.execute("SELECT value FROM metadata").fetchone()[0])
        manifest, _ = _destination(metadata["binding"]["manifest"], index_path)
        with open_snapshot(manifest) as store:
            if metadata["binding"] != _binding(store):
                raise ValueError("stale retrieval index or incompatible snapshot; refresh the index")
            if verify:
                _verify_tree(store)
            records = {key: json.loads(value) for key, value in db.execute("SELECT entity_id,record FROM documents")}
            ranked, exact, ambiguous, gaps = {}, [], [], []

            def add(record, origin, priority, score=0.0):
                key = record["entity_id"]
                current = ranked.setdefault(key, {**record, "provenance": [], "priority": priority, "score": score})
                if origin not in current["provenance"]:
                    current["provenance"].append(origin)
                current["priority"] = min(current["priority"], priority)

            requests = [(anchor, "exact") for anchor in anchors]
            for match in re.finditer(r'File "([^"]+)", line (\d+)', query):
                path = Path(match[1])
                if path.is_absolute():
                    try:
                        path = path.relative_to(Path(store["root"]))
                    except ValueError:
                        gaps.append("traceback path outside snapshot root")
                        continue
                requests.append(({"path": path.as_posix(), "line": int(match[2])}, "traceback"))
            if query in records:
                requests.append(({"entity_id": query}, "exact"))
            elif query and re.fullmatch(r"[\w.]+", query):
                requests.append(({"symbol": query}, "exact"))
            for anchor, origin in requests:
                try:
                    matches, is_ambiguous = _anchor_records(store, records, anchor)
                except ValueError as error:
                    if origin != "traceback":
                        raise
                    gaps.append(f"traceback frame {anchor['path']}:{anchor['line']}: {error}")
                    continue
                if is_ambiguous:
                    ambiguous.append({"anchor": anchor, "items": [r["entity_id"] for r in matches[:limit]],
                                      "total": len(matches), "truncated": max(0, len(matches) - limit)})
                for record in matches:
                    add(record, "ambiguous-anchor" if is_ambiguous else origin, 1 if is_ambiguous else 0)
                    if not is_ambiguous and record["entity_id"] not in exact:
                        exact.append(record["entity_id"])
            tokens = list(dict.fromkeys(subtokens(query)))
            if tokens:
                expression = " OR ".join('"' + token.replace('"', '""') + '"' for token in tokens)
                for identity, score in db.execute(
                    "SELECT entity_id,bm25(search_text,0,10,5,3,1) FROM search_text "
                    "WHERE search_text MATCH ? ORDER BY 2,entity_id", (expression,)):
                    add(records[identity], "fts5", 2, score)
            embedding_status = "unavailable"
            ranking_policy = RANKING_VERSION
            if embedding_result is not None:
                # Only consume an explicitly produced, bound result. Importing
                # this standard-library validator never loads an encoder.
                import embedding_worker
                try:
                    dense = embedding_worker.validate_result(embedding_result, metadata, query, records)
                except embedding_worker.StaleEmbedding as error:
                    gaps.append(str(error))
                    embedding_status = "stale"
                else:
                    lexical = sorted((r for r in ranked.values() if "fts5" in r["provenance"]),
                                     key=lambda r: (r["score"], r["entity_id"]))
                    lexical_rank = {row["entity_id"]: rank for rank, row in enumerate(lexical)}
                    dense_rank = {row["entity_id"]: row["rank"] for row in dense}
                    for row in dense:
                        add(records[row["entity_id"]], "embedding", 2)
                    for identity, row in ranked.items():
                        row["score"] = -(0.75 / (60 + dense_rank.get(identity, 1000))
                                         + 0.25 / (60 + lexical_rank.get(identity, 1000)))
                    embedding_status = "available"
                    ranking_policy = "exact-rrf75-25-k60-v1"
            ordered = sorted(ranked.values(), key=lambda r: (r["priority"], r["score"], r["entity_id"]))
            result = [{k: v for k, v in record.items() if k != "priority"} for record in ordered[:limit]]
            return {"schema": "daodan/retrieval-result/v1", "binding": metadata["binding"],
                    "document_digest": metadata["document_digest"], "results": result,
                    "exact": exact[:limit], "exact_total": len(exact), "exact_truncated": max(0, len(exact) - limit),
                    "ambiguous": ambiguous, "matched": len(ordered), "returned": len(result),
                    "truncated": max(0, len(ordered) - limit), "limit": limit, "gaps": gaps,
                    "ranking_policy": ranking_policy,
                    "capabilities": {"exact": True, "fts5": True, "embedding": embedding_status}}
