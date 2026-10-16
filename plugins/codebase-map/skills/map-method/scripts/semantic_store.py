"""Persistent conservative semantic bindings; only one file payload is decoded at once."""
from __future__ import annotations

from collections.abc import Mapping
from contextlib import contextmanager
import hashlib
from pathlib import Path
import sqlite3
import tempfile

import snapshot
from snapshot_store import SnapshotStore, SnapshotWriter, _pack, _unpack, _settings, logical_digest
from tree_scope import Perimeter
import semantic_index

RESOLVER_VERSION = 1
TARGET_KINDS = frozenset({"function", "class"})


class ConfigObservations(Mapping):
    """Expose only verified inventoried bytes to the existing module-config parser."""

    def __init__(self, store):
        self.store = store
        self.root = Path(store["root"])
        self.target = self.root / store["target"]
        self.perimeter = Perimeter(self.target)

    def __iter__(self):
        for rel in self.store.iter_paths():
            yield (self.root / rel).resolve()

    def __len__(self):
        return self.store.file_count

    def __contains__(self, path):
        try:
            rel = Path(path).relative_to(self.root).as_posix()
        except ValueError:
            return False
        return self.store.has_file(rel)

    def __getitem__(self, path):
        from source_reader import _source_path
        try:
            rel = Path(path).relative_to(self.root).as_posix()
        except ValueError as error:
            raise KeyError(path) from error
        entry = self.store.get_file(rel, semantic=False)
        if entry is None:
            raise KeyError(path)
        try:
            source = _source_path(rel, self.root, self.target, self.perimeter)
            if source.stat().st_size > snapshot.MAX_PARSE_BYTES:
                raise KeyError(path)
            data = source.read_bytes()
        except OSError as error:
            raise KeyError(path) from error
        if hashlib.sha256(data).hexdigest() != entry.get("raw_hash"):
            raise ValueError("configuration source changed; refresh the snapshot")
        return data


def _schema(database):
    database.executescript("""
        CREATE TABLE sem_meta(key TEXT PRIMARY KEY,payload BLOB NOT NULL);
        CREATE TABLE sem_coverage(file TEXT PRIMARY KEY,status TEXT NOT NULL,verified INTEGER NOT NULL,
                                  language TEXT,module_scope TEXT,payload BLOB NOT NULL);
        CREATE TABLE sem_scopes(file TEXT NOT NULL,id TEXT NOT NULL,parent TEXT,payload BLOB NOT NULL,
                                PRIMARY KEY(file,id));
        CREATE TABLE sem_declarations(id TEXT PRIMARY KEY,file TEXT NOT NULL,source_id TEXT NOT NULL,
             scope TEXT NOT NULL,name TEXT NOT NULL,kind TEXT NOT NULL,l0 INTEGER,c0 INTEGER,l1 INTEGER,c1 INTEGER,
             payload BLOB NOT NULL);
        CREATE INDEX sem_declarations_file ON sem_declarations(file,kind);
        CREATE TABLE sem_bindings(file TEXT NOT NULL,scope TEXT NOT NULL,name TEXT NOT NULL,
                                  kind TEXT NOT NULL,identity TEXT,payload BLOB);
        CREATE INDEX sem_bindings_lookup ON sem_bindings(file,scope,name);
        CREATE TABLE sem_exports(file TEXT NOT NULL,name TEXT NOT NULL,payload BLOB NOT NULL);
        CREATE INDEX sem_exports_lookup ON sem_exports(file,name);
        CREATE TABLE sem_modules(file TEXT NOT NULL,module TEXT NOT NULL,target TEXT NOT NULL,
                                 PRIMARY KEY(file,module,target));
        CREATE TABLE sem_edges(source TEXT NOT NULL,target TEXT NOT NULL,PRIMARY KEY(source,target));
        CREATE TABLE sem_references(id TEXT PRIMARY KEY,file TEXT NOT NULL,kind TEXT NOT NULL,
             caller TEXT,target_id TEXT,resolution TEXT NOT NULL,l0 INTEGER,c0 INTEGER,l1 INTEGER,c1 INTEGER,
             known_unrelated INTEGER NOT NULL,last_name TEXT,has_candidates INTEGER NOT NULL,payload BLOB NOT NULL);
        CREATE TABLE sem_reference_candidates(reference TEXT NOT NULL,file TEXT NOT NULL,imported TEXT,
                                              PRIMARY KEY(reference,file,imported));
        CREATE INDEX sem_reference_candidates_lookup ON sem_reference_candidates(file,imported,reference);
        CREATE INDEX sem_references_name ON sem_references(last_name,resolution);
        CREATE INDEX sem_references_caller ON sem_references(caller,kind,resolution);
        CREATE INDEX sem_references_target ON sem_references(target_id,kind,resolution);
        CREATE INDEX sem_references_file ON sem_references(file,kind);
    """)


def observed_coverage(entry, data):
    """Validate one extracted payload while its observed source is still in memory."""
    record = {"status": "excluded", "reason": "outside-current-perimeter", "verified_source": False,
              "reference_count": 0, "resolved_count": 0}
    try:
        if len(data) > snapshot.MAX_FILE_BYTES:
            record.update(status="oversized", reason="source-size-limit")
            return record
        data.decode("utf-8")
    except UnicodeError as error:
        record.update(status="unavailable", reason=type(error).__name__)
        return record
    actual = hashlib.sha256(data).hexdigest()
    record["raw_hash"] = actual
    if not isinstance(entry.get("raw_hash"), str):
        record.update(status="unbound-source", reason="manifest-source-hash-missing")
    elif entry["raw_hash"] != actual:
        record.update(status="stale", reason="source-hash-mismatch")
    else:
        record["verified_source"] = True
        payload = entry.get("semantic")
        if payload is None:
            record.update(status="lexical", reason="semantic-backend-unavailable")
        else:
            problem = semantic_index._validate(payload, data)
            if problem:
                record.update(status="malformed", reason=problem)
            elif entry.get("status") != "parsed":
                record.update(status="lexical", reason="source-not-successfully-parsed")
            else:
                record.update(status="ast", reason=None, backend=payload["backend"],
                              reference_count=len(payload["references"]), notes=list(payload.get("notes", [])))
    return record


def _coverage(store, rel, entry, root, target, perimeter, fingerprint, observed=None):
    from source_reader import _relative, _source_path
    _relative(rel)
    path = root / rel
    if not semantic_index._allowed(path.resolve(), rel, root, target, perimeter):
        return {"status": "excluded", "reason": "outside-current-perimeter", "verified_source": False,
                "reference_count": 0, "resolved_count": 0}, None
    _source_path(rel, root, target, perimeter)
    if observed is None:
        try:
            if path.stat().st_size > snapshot.MAX_FILE_BYTES:
                data = b""
                record = {"status": "oversized", "reason": "source-size-limit", "verified_source": False,
                          "reference_count": 0, "resolved_count": 0}
            else:
                record = observed_coverage(entry, path.read_bytes())
        except OSError as error:
            record = {"status": "unavailable", "reason": type(error).__name__, "verified_source": False,
                      "reference_count": 0, "resolved_count": 0}
    else:
        record = observed
    if store.get("parser_fingerprint") != fingerprint and record.get("verified_source"):
        record.update(status="fingerprint-mismatch", reason="helper-fingerprint-mismatch", verified_source=False)
    return record, entry.get("semantic") if record["status"] == "ast" else None


class _Resolver:
    def __init__(self, database):
        self.db = database

    def scope(self, rel, identity):
        row = self.db.execute("SELECT payload FROM sem_scopes WHERE file=? AND id=?", (rel, identity)).fetchone()
        if row is None:
            raise ValueError("semantic scope is missing")
        return _unpack(row[0])

    def bindings(self, rel, scope, name):
        return self.db.execute(
            "SELECT kind,identity,payload FROM sem_bindings WHERE file=? AND scope=? AND name=? ORDER BY rowid",
            (rel, scope, name))

    @staticmethod
    def binding(row):
        return (row[0], row[1] if row[0] == "declaration" else _unpack(row[2]))

    def lexical(self, rel, scope_id, name):
        while scope_id is not None:
            scope = self.scope(rel, scope_id)
            if scope.get("unresolved"):
                return None, "scope-unresolved"
            cursor = self.bindings(rel, scope_id, name)
            matches = cursor.fetchmany(2)
            cursor.close()
            if matches:
                return (self.binding(matches[0]), None) if len(matches) == 1 else (None, "ambiguous-binding")
            scope_id = scope.get("parent")
        return None, "unbound-name"

    def targets(self, rel, module):
        return [row[0] for row in self.db.execute(
            "SELECT target FROM sem_modules WHERE file=? AND module=? ORDER BY target", (rel, module))]

    def uncertain_imports(self, rel, scope_id, parts):
        while scope_id is not None:
            scope = self.scope(rel, scope_id)
            cursor = self.bindings(rel, scope_id, parts[0])
            first = cursor.fetchone()
            if first is not None:
                result = []
                row = first
                while row is not None:
                    kind, value = self.binding(row)
                    if kind == "import":
                        result.append({"files": self.targets(rel, value["module"]),
                            "imported": parts[1] if value["mode"] == "namespace" and len(parts) == 2 else value["imported"]})
                    row = cursor.fetchone()
                cursor.close()
                return result
            cursor.close()
            if scope.get("unresolved"):
                break
            scope_id = scope.get("parent")
        return []

    def declaration(self, identity):
        row = self.db.execute("SELECT payload FROM sem_declarations WHERE id=?", (identity,)).fetchone()
        return _unpack(row[0]) if row else None

    def exported_target(self, rel, exported):
        row = self.db.execute("SELECT status,language,module_scope FROM sem_coverage WHERE file=?", (rel,)).fetchone()
        if row is None or row[0] != "ast":
            return None, "import-target-" + (row[0] if row else "unavailable")
        if row[1] == "python":
            local = exported
        else:
            cursor = self.db.execute("SELECT payload FROM sem_exports WHERE file=? AND name=? ORDER BY rowid", (rel, exported))
            matches = cursor.fetchmany(2)
            cursor.close()
            if len(matches) != 1:
                return None, "export-missing-or-ambiguous"
            export = _unpack(matches[0][0])
            if export.get("type_only"):
                return None, "type-only-export"
            if export.get("module"):
                return None, "reexport-unsupported"
            local = export.get("local")
        binding, reason = self.lexical(rel, row[2], local)
        if reason:
            return None, reason
        kind, value = binding
        if kind != "declaration":
            return None, "reexport-unsupported"
        if self.declaration(value)["kind"] not in TARGET_KINDS:
            return None, "unsupported-target-kind"
        return value, None

    def reference(self, rel, number, item):
        record = {**item, "id": f"{rel}::reference#{number}", "file": rel,
                  "caller": f"{rel}::{item['caller']}" if item.get("caller") else None,
                  "target_id": None, "resolution": "unresolved", "reason": item.get("reason"),
                  "known_unrelated": False, "candidate_files": [], "imported_name": None,
                  "candidate_bindings": []}
        if item.get("reason") or not item["parts"]:
            record["reason"] = item.get("reason") or "dynamic-reference"
            return record
        parts = item["parts"]
        binding, reason = self.lexical(rel, item["scope"], parts[0])
        if reason:
            record["reason"] = reason
            record["candidate_bindings"] = self.uncertain_imports(rel, item["scope"], parts)
            return record
        kind, value = binding
        if kind == "declaration":
            if len(parts) != 1:
                record["reason"] = "unknown-receiver"
            elif self.declaration(value)["kind"] in TARGET_KINDS:
                record.update(target_id=value, resolution="resolved", reason="unique-lexical-binding")
            else:
                record.update(reason="non-callable-binding", known_unrelated=True, binding_id=value)
            return record
        imported = value
        targets = self.targets(rel, imported["module"])
        record["candidate_files"] = targets
        record["imported_name"] = imported["imported"]
        if imported.get("unresolved"):
            record["reason"] = imported.get("reason") or "import-binding-unresolved"
        elif imported.get("type_only"):
            record["reason"] = "type-only-import"
        elif len(targets) != 1:
            record["reason"] = "import-target-missing-or-ambiguous"
        elif imported["mode"] == "namespace" and len(parts) == 2:
            record["imported_name"] = parts[1]
            identity, reason = self.exported_target(targets[0], parts[1])
            record.update(target_id=identity, reason=reason or "direct-internal-import")
        elif imported["mode"] in {"named", "default"} and len(parts) == 1 and imported["imported"] != "*":
            name = "default" if imported["mode"] == "default" else imported["imported"]
            identity, reason = self.exported_target(targets[0], name)
            record.update(target_id=identity, reason=reason or "direct-internal-import")
        else:
            record["reason"] = "unknown-receiver-or-import-form"
        if record["target_id"] is not None:
            record["resolution"] = "resolved"
        return record


def build_semantic_store(store: SnapshotStore, *, writer: SnapshotWriter) -> None:
    db = writer.connection
    _schema(db)
    root = Path(store["root"]).resolve()
    target = (root / store["target"]).resolve()
    perimeter = Perimeter(target)
    fingerprint = snapshot.parser_fingerprint()
    observed = db.execute("SELECT 1 FROM sqlite_master WHERE name='observed_coverage'").fetchone() is not None
    for rel, entry in store.iter_files():
        row = db.execute("SELECT payload FROM observed_coverage WHERE file=?", (rel,)).fetchone() if observed else None
        record, payload = _coverage(store, rel, entry, root, target, perimeter, fingerprint,
                                    _unpack(row[0]) if row else None)
        module_scope = next((scope["id"] for scope in payload["scopes"] if scope.get("parent") is None), None) if payload else None
        db.execute("INSERT INTO sem_coverage VALUES(?,?,?,?,?,?)",
                   (rel, record["status"], int(record["verified_source"]), entry.get("language"), module_scope, _pack(record)))
        if payload is not None:
            db.executemany("INSERT INTO sem_scopes VALUES(?,?,?,?)",
                          ((rel, item["id"], item.get("parent"), _pack(item)) for item in payload["scopes"]))
            for item in payload["declarations"]:
                identity = f"{rel}::{item['id']}"
                declaration = {**item, "id": identity, "source_id": item["id"], "file": rel}
                db.execute("INSERT INTO sem_declarations VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                    (identity, rel, item["id"], item["scope"], item["name"], item["kind"], *item["span"], _pack(declaration)))
                if item.get("lexical", True):
                    db.execute("INSERT INTO sem_bindings VALUES(?,?,?,?,?,NULL)",
                               (rel, item["scope"], item["name"], "declaration", identity))
            db.executemany("INSERT INTO sem_bindings VALUES(?,?,?,?,NULL,?)",
                          ((rel, item["scope"], item["local"], "import", _pack(item)) for item in payload["imports"]))
            db.executemany("INSERT INTO sem_exports VALUES(?,?,?)",
                          ((rel, item["exported"], _pack(item)) for item in payload["exports"]))
        del entry, payload
    config = snapshot.ts_path_config(target, source_observations=ConfigObservations(store))
    for rel, modules in snapshot.iter_resolved_imports(store, config, include_self=True):
        for module, targets in modules.items():
            db.executemany("INSERT INTO sem_modules VALUES(?,?,?)", ((rel, module, target) for target in targets))
    db.execute("""INSERT OR IGNORE INTO sem_edges SELECT m.file,m.target FROM sem_modules m
                  JOIN sem_coverage a ON a.file=m.file AND a.verified=1
                  JOIN sem_coverage b ON b.file=m.target AND b.verified=1""")
    resolver = _Resolver(db)
    for (rel,) in db.execute("SELECT file FROM sem_coverage WHERE status='ast' ORDER BY file"):
        resolved = 0
        for number, item in enumerate(store.iter_records("references", path=rel)):
            record = resolver.reference(rel, number, item)
            db.execute("INSERT INTO sem_references VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                       (record["id"], rel, record["kind"], record["caller"], record["target_id"],
                        record["resolution"], *record["span"], int(bool(record.get("known_unrelated"))),
                        record["parts"][-1] if record["parts"] else None,
                        int(bool(record.get("candidate_files"))), _pack(record)))
            candidates = ((file, record.get("imported_name")) for file in record.get("candidate_files", []))
            db.executemany("INSERT OR IGNORE INTO sem_reference_candidates VALUES(?,?,?)",
                           ((record["id"], file, imported) for file, imported in candidates))
            for binding in record.get("candidate_bindings", []):
                db.executemany("INSERT OR IGNORE INTO sem_reference_candidates VALUES(?,?,?)",
                               ((record["id"], file, binding["imported"]) for file in binding["files"]))
            resolved += record["resolution"] == "resolved"
        row = db.execute("SELECT payload FROM sem_coverage WHERE file=?", (rel,)).fetchone()
        record = _unpack(row[0])
        record["resolved_count"] = resolved
        db.execute("UPDATE sem_coverage SET payload=? WHERE file=?", (_pack(record), rel))
    if observed:
        db.execute("DROP TABLE observed_coverage")
    from store_graph_metrics import build_metrics
    build_metrics(db, prefix="sem", temporary=False,
                  nodes="SELECT file FROM sem_coverage WHERE verified=1",
                  edges="SELECT source,target FROM sem_edges")
    db.execute("INSERT INTO sem_meta VALUES('resolver_version',?)", (_pack(RESOLVER_VERSION),))
    db.execute("INSERT INTO sem_meta VALUES('manifest_digest',?)", (_pack(logical_digest(store, ensure_ascii=False)),))


@contextmanager
def semantic_reader(store, *, rebuild=False):
    """JSON compatibility derives only an operation-owned index, never a second snapshot."""
    if store.format == "sqlite" and not rebuild:
        row = store.connection.execute("SELECT payload FROM sem_meta WHERE key='resolver_version'").fetchone()
        if row is None or _unpack(row[0]) != RESOLVER_VERSION:
            raise ValueError("semantic resolver changed; refresh the snapshot")
        db = sqlite3.connect(store.path.resolve().as_uri() + "?mode=ro", uri=True)
        _settings(db)
        try:
            yield db
        finally:
            db.close()
    else:
        with tempfile.TemporaryDirectory(prefix="map-semantic-") as temporary:
            path = Path(temporary) / "derived.sqlite"
            with SnapshotWriter(path) as writer:
                build_semantic_store(store, writer=writer)
                writer.finish(store.metadata)
            db = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
            _settings(db)
            try:
                yield db
            finally:
                db.close()


def query_graph(store, paths=None, hops=2, limit=100):
    from store_graph import query_graph as query
    return query(store, paths, hops, limit)


def query_references(store, declaration_id):
    from store_consumers import consumer_reader
    with consumer_reader(store) as db:
        for (payload,) in db.execute("SELECT payload FROM sem_references WHERE target_id=? ORDER BY file,l0,c0,l1,c1,id", (declaration_id,)):
            yield _unpack(payload)
