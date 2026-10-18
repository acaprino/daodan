"""Persistent conservative semantic bindings; only one file payload is decoded at once."""
from __future__ import annotations

from collections.abc import Mapping
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import itertools
import json
from pathlib import Path
import sqlite3
import tempfile

import snapshot
from snapshot_store import SnapshotStore, SnapshotWriter, _pack, _unpack, _settings, logical_digest
from tree_scope import Perimeter
import semantic_index

RESOLVER_VERSION = 1
TARGET_KINDS = frozenset({"function", "class"})
MAX_META_CHANGESETS = 16
MAX_META_HISTORY_BYTES = 4 * 1024 * 1024


class ConfigObservations(Mapping):
    """Expose only verified inventoried bytes to the existing module-config parser."""

    def __init__(self, store, *, perimeter: Perimeter | None = None):
        self.store = store
        self.root = Path(store["root"])
        self.target = self.root / store["target"]
        self.perimeter = perimeter if perimeter is not None else Perimeter(self.target)

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
        CREATE TABLE meta_symbols(
            id TEXT PRIMARY KEY,
            file TEXT NOT NULL,
            name TEXT NOT NULL,
            kind TEXT NOT NULL,
            start INTEGER NOT NULL,
            end INTEGER NOT NULL,
            body_hash TEXT NOT NULL,
            interface_hash TEXT NOT NULL,
            effects_hash TEXT NOT NULL,
            exported INTEGER NOT NULL
        );
        CREATE INDEX meta_symbols_file ON meta_symbols(file, name);
        CREATE TABLE meta_changesets(
            seq INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            git_head TEXT,
            git_dirty INTEGER NOT NULL,
            files_changed INTEGER NOT NULL,
            symbols_added INTEGER NOT NULL,
            symbols_removed INTEGER NOT NULL,
            interfaces_changed INTEGER NOT NULL,
            effects_changed INTEGER NOT NULL,
            bodies_only_changed INTEGER NOT NULL,
            byte_size INTEGER NOT NULL
        );
        CREATE TABLE meta_changeset_deltas(
            seq INTEGER NOT NULL,
            symbol_id TEXT NOT NULL,
            file TEXT NOT NULL,
            name TEXT NOT NULL,
            change_kind TEXT NOT NULL,
            old_body_hash TEXT,
            new_body_hash TEXT,
            old_interface_hash TEXT,
            new_interface_hash TEXT,
            old_effects_hash TEXT,
            new_effects_hash TEXT,
            old_span TEXT,
            new_span TEXT,
            PRIMARY KEY(seq, symbol_id)
        );
        CREATE INDEX meta_changeset_deltas_symbol ON meta_changeset_deltas(symbol_id, seq);
        CREATE TABLE meta_cards(
            symbol_id TEXT PRIMARY KEY,
            file TEXT NOT NULL,
            symbol TEXT NOT NULL,
            kind TEXT NOT NULL,
            body_hash TEXT NOT NULL,
            interface_hash TEXT NOT NULL,
            effects_hash TEXT NOT NULL,
            callee_interface_digest TEXT NOT NULL,
            freshness TEXT NOT NULL,
            stale_reason TEXT,
            updated_at TEXT NOT NULL,
            payload BLOB NOT NULL
        );
        CREATE INDEX meta_cards_file ON meta_cards(file, freshness);
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


def _can_reuse_previous_semantics(previous: SnapshotStore | None, reused_files: set[str] | None) -> bool:
    if (
        previous is None
        or not reused_files
        or getattr(previous, "format", None) != "sqlite"
        or getattr(previous, "connection", None) is None
    ):
        return False
    try:
        prev_db = previous.connection
        ver_row = prev_db.execute("SELECT payload FROM sem_meta WHERE key='resolver_version'").fetchone()
        dig_row = prev_db.execute("SELECT payload FROM sem_meta WHERE key='manifest_digest'").fetchone()
        if ver_row is None or dig_row is None:
            return False
        if _unpack(ver_row[0]) != RESOLVER_VERSION:
            return False
        if _unpack(dig_row[0]) != logical_digest(previous, ensure_ascii=False):
            return False
        return True
    except Exception:
        return False


def _compute_file_meta_symbols(
    rel: str,
    sym_rows: list[tuple[str, bytes]],
    decl_rows: list[tuple],
    scope_rows: list[tuple],
    export_rows: list[tuple],
    ref_rows: list[tuple],
) -> list[tuple]:
    if not sym_rows:
        return []
    unpacked_syms = [(name, _unpack(blob)) for name, blob in sym_rows]
    caller_to_scopes: dict[str, list[str]] = {}
    for s_id, _parent, s_blob in scope_rows:
        s_obj = _unpack(s_blob)
        caller_src = s_obj.get("caller")
        if caller_src:
            caller_to_scopes.setdefault(f"{rel}::{caller_src}", []).append(s_id)
    scope_params: dict[str, list[tuple[int, int, str]]] = {}
    decls_parsed: list[tuple[str, str, str, int, int, dict]] = []
    decl_line: dict[str, int] = {}
    for d_id, _src_id, scope, d_name, d_kind, l0, c0, l1, _c1, d_blob in decl_rows:
        decl_line[d_id] = l0 or 0
        if d_kind == "parameter":
            scope_params.setdefault(scope, []).append((l0 or 0, c0 or 0, d_name))
        else:
            decls_parsed.append((d_id, d_name, d_kind, l0 or 0, l1 or 0, _unpack(d_blob)))
    for params in scope_params.values():
        params.sort()
    exported_names: set[str] = set()
    for exp_name, exp_blob in export_rows:
        exp_obj = _unpack(exp_blob)
        exported_names.add(exp_name)
        if exp_obj.get("local"):
            exported_names.add(exp_obj["local"])

    sym_info: dict[str, dict] = {}
    spans = [(name, int(sym["start"]), int(sym["end"])) for name, sym in unpacked_syms]
    for name, sym in unpacked_syms:
        start, end = int(sym["start"]), int(sym["end"])
        short_name = name.split(".")[-1]
        matched_decls: list[str] = []
        param_names: list[str] = []
        for d_id, d_name, _d_kind, l0, _l1, d_obj in decls_parsed:
            q_name = d_obj.get("qualified_name")
            if q_name == name or (q_name is None and d_name == short_name and l0 == start):
                matched_decls.append(d_id)
                for sc_id in caller_to_scopes.get(d_id, ()):
                    for _pl0, _pc0, p_name in scope_params.get(sc_id, ()):
                        param_names.append(p_name)
        is_exp = 1 if (name in exported_names or name.split(".")[0] in exported_names) else 0
        sym_info[name] = {
            "sym": sym,
            "start": start,
            "end": end,
            "matched_decls": set(matched_decls),
            "params_str": ",".join(param_names),
            "is_exp": is_exp,
        }

    out_rows: list[tuple] = []
    for name, info in sym_info.items():
        sym = info["sym"]
        kind = sym["kind"]
        start, end = info["start"], info["end"]
        body_hash = sym["hash"]
        is_exp = info["is_exp"]
        matched_decls = info["matched_decls"]
        params_str = info["params_str"]
        if kind == "class":
            prefix = name + "."
            members = sorted(
                f"{m_name[len(prefix):]}({m_info['params_str']})"
                for m_name, m_info in sym_info.items()
                if m_name.startswith(prefix)
            )
            interface_sig = f"{kind}|{name}|exp={is_exp}|params={params_str}|members={';'.join(members)}"
        elif matched_decls:
            interface_sig = f"{kind}|{name}|exp={is_exp}|params={params_str}|members="
        else:
            interface_sig = f"{kind}|{name}|exp={is_exp}|body={body_hash}"
        interface_hash = hashlib.sha256(interface_sig.encode("utf-8")).hexdigest()[:16]

        child_spans = [
            (c_start, c_end)
            for c_name, c_start, c_end in spans
            if c_name != name and start <= c_start and c_end <= end and (c_start > start or c_end < end)
        ]
        effects: set[tuple[str, str, str, str]] = set()
        for caller, r_kind, target_id, resolution, rl0, _rl1, known_unrel, last_name in ref_rows:
            if known_unrel:
                continue
            in_decl = bool(caller and caller in matched_decls)
            in_span = False
            if not in_decl and rl0 is not None and start <= rl0 <= end:
                in_span = not any(cs <= rl0 <= ce for cs, ce in child_spans)
            if in_decl or in_span:
                if target_id and target_id in decl_line and start <= decl_line[target_id] <= end:
                    continue
                effects.add((r_kind, target_id or "", last_name or "", resolution))
        effects_sig = ";".join(f"{rk}:{tid}:{ln}:{res}" for rk, tid, ln, res in sorted(effects))
        effects_hash = hashlib.sha256(effects_sig.encode("utf-8")).hexdigest()[:16]
        out_rows.append((
            f"{rel}::{name}", rel, name, kind, start, end,
            body_hash, interface_hash, effects_hash, is_exp,
        ))
    return out_rows


def _build_meta_symbols(db: sqlite3.Connection, recompute_files: set[str] | None, prev_attached: bool) -> None:
    has_prev_meta = (
        prev_attached
        and db.execute("SELECT 1 FROM prev_snap.sqlite_master WHERE type='table' AND name='meta_symbols'").fetchone() is not None
    )
    if has_prev_meta and recompute_files is not None:
        db.execute("""
            INSERT INTO main.meta_symbols
            SELECT * FROM prev_snap.meta_symbols
            WHERE file IN (SELECT file FROM _sem_ref_reused)
        """)
        if not recompute_files:
            return
        db.execute("CREATE TEMP TABLE _meta_recompute(file TEXT PRIMARY KEY)")
        db.executemany("INSERT INTO _meta_recompute VALUES(?)", ((f,) for f in recompute_files))
        sym_cur = db.execute("SELECT file, name, payload FROM symbols WHERE file IN (SELECT file FROM _meta_recompute) ORDER BY file, ordinal")
        decl_cur = db.execute("SELECT file, id, source_id, scope, name, kind, l0, c0, l1, c1, payload FROM sem_declarations WHERE file IN (SELECT file FROM _meta_recompute) ORDER BY file, id")
        scope_cur = db.execute("SELECT file, id, parent, payload FROM sem_scopes WHERE file IN (SELECT file FROM _meta_recompute) ORDER BY file, id")
        exp_cur = db.execute("SELECT file, name, payload FROM sem_exports WHERE file IN (SELECT file FROM _meta_recompute) ORDER BY file, name")
        ref_cur = db.execute("SELECT file, caller, kind, target_id, resolution, l0, l1, known_unrelated, last_name FROM sem_references WHERE file IN (SELECT file FROM _meta_recompute) ORDER BY file, id")
        target_files = sorted(recompute_files)
    else:
        sym_cur = db.execute("SELECT file, name, payload FROM symbols ORDER BY file, ordinal")
        decl_cur = db.execute("SELECT file, id, source_id, scope, name, kind, l0, c0, l1, c1, payload FROM sem_declarations ORDER BY file, id")
        scope_cur = db.execute("SELECT file, id, parent, payload FROM sem_scopes ORDER BY file, id")
        exp_cur = db.execute("SELECT file, name, payload FROM sem_exports ORDER BY file, name")
        ref_cur = db.execute("SELECT file, caller, kind, target_id, resolution, l0, l1, known_unrelated, last_name FROM sem_references ORDER BY file, id")
        target_files = [r[0] for r in db.execute("SELECT path FROM files ORDER BY path")]

    def _group_map(cursor):
        return {k: [row[1:] for row in grp] for k, grp in itertools.groupby(cursor, key=lambda r: r[0])}

    sym_by_file = _group_map(sym_cur)
    decl_by_file = _group_map(decl_cur)
    scope_by_file = _group_map(scope_cur)
    exp_by_file = _group_map(exp_cur)
    ref_by_file = _group_map(ref_cur)

    batch: list[tuple] = []
    for rel in target_files:
        s_rows = sym_by_file.get(rel)
        if not s_rows:
            continue
        batch.extend(_compute_file_meta_symbols(
            rel,
            s_rows,
            decl_by_file.get(rel, []),
            scope_by_file.get(rel, []),
            exp_by_file.get(rel, []),
            ref_by_file.get(rel, []),
        ))
    if batch:
        db.executemany("INSERT INTO meta_symbols VALUES(?,?,?,?,?,?,?,?,?,?)", batch)
    db.execute("DROP TABLE IF EXISTS _meta_recompute")


def _callee_interface_digests(db: sqlite3.Connection, files_filter: set[str] | None = None) -> dict[str, str]:
    """Compute a deterministic digest of resolved callee interface hashes per symbol."""
    where_clause = ""
    if files_filter is not None:
        if not files_filter:
            return {}
        db.execute("CREATE TEMP TABLE IF NOT EXISTS _cid_files(file TEXT PRIMARY KEY)")
        db.execute("DELETE FROM _cid_files")
        db.executemany("INSERT INTO _cid_files VALUES(?)", ((f,) for f in files_filter))
        where_clause = "WHERE caller_ms.file IN (SELECT file FROM _cid_files)"
    rows = db.execute(f"""
        SELECT caller_ms.id, callee_ms.id, callee_ms.interface_hash
        FROM meta_symbols caller_ms
        JOIN sem_references r
          ON r.file = caller_ms.file
         AND r.resolution = 'resolved'
         AND r.target_id IS NOT NULL
         AND r.l0 BETWEEN caller_ms.start AND caller_ms.end
        JOIN sem_declarations td ON td.id = r.target_id
        JOIN meta_symbols callee_ms
          ON callee_ms.file = td.file
         AND (callee_ms.name = td.name OR callee_ms.start = td.l0)
        {where_clause}
        GROUP BY caller_ms.id, callee_ms.id
        ORDER BY caller_ms.id, callee_ms.id
    """).fetchall()
    if files_filter is not None:
        db.execute("DROP TABLE IF EXISTS _cid_files")
    result: dict[str, str] = {}
    for caller_id, grp in itertools.groupby(rows, key=lambda r: r[0]):
        sig = ";".join(f"{cid}:{ihash}" for _caller, cid, ihash in grp)
        result[caller_id] = hashlib.sha256(sig.encode("utf-8")).hexdigest()[:16]
    return result


def _record_meta_changeset_and_carry_cards(
    db: sqlite3.Connection,
    store: SnapshotStore,
    prev_attached: bool,
) -> None:
    if not prev_attached:
        return
    has_prev_meta = (
        db.execute("SELECT 1 FROM prev_snap.sqlite_master WHERE type='table' AND name='meta_symbols'").fetchone() is not None
    )
    if not has_prev_meta:
        return
    if db.execute("SELECT 1 FROM prev_snap.sqlite_master WHERE type='table' AND name='meta_changesets'").fetchone():
        db.execute("INSERT INTO main.meta_changesets SELECT * FROM prev_snap.meta_changesets")
        db.execute("INSERT INTO main.meta_changeset_deltas SELECT * FROM prev_snap.meta_changeset_deltas")

    deltas = db.execute("""
        SELECT
            COALESCE(n.id, o.id) AS symbol_id,
            COALESCE(n.file, o.file) AS file,
            COALESCE(n.name, o.name) AS name,
            CASE
                WHEN o.id IS NULL THEN 'added'
                WHEN n.id IS NULL THEN 'removed'
                WHEN o.interface_hash != n.interface_hash THEN 'interface_changed'
                WHEN o.effects_hash != n.effects_hash THEN 'effects_changed'
                ELSE 'body_only'
            END AS change_kind,
            o.body_hash, n.body_hash,
            o.interface_hash, n.interface_hash,
            o.effects_hash, n.effects_hash,
            CASE WHEN o.id IS NOT NULL THEN o.start || '-' || o.end ELSE NULL END AS old_span,
            CASE WHEN n.id IS NOT NULL THEN n.start || '-' || n.end ELSE NULL END AS new_span
        FROM prev_snap.meta_symbols o
        FULL OUTER JOIN main.meta_symbols n ON o.id = n.id
        WHERE o.id IS NULL OR n.id IS NULL OR o.body_hash != n.body_hash
           OR o.interface_hash != n.interface_hash OR o.effects_hash != n.effects_hash
        ORDER BY file, name
    """).fetchall()

    if deltas:
        files_changed = len({row[1] for row in deltas})
        counts = {"added": 0, "removed": 0, "interface_changed": 0, "effects_changed": 0, "body_only": 0}
        byte_size = 0
        for row in deltas:
            counts[row[3]] += 1
            byte_size += sum(len(str(col)) for col in row if col is not None)
        git_meta = store.metadata.get("git") or {}
        created_at = store.metadata.get("created_at") or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        cur = db.execute("""
            INSERT INTO meta_changesets(
                created_at, git_head, git_dirty, files_changed,
                symbols_added, symbols_removed, interfaces_changed,
                effects_changed, bodies_only_changed, byte_size
            ) VALUES (?,?,?,?,?,?,?,?,?,?)
        """, (
            created_at,
            git_meta.get("head"),
            1 if git_meta.get("dirty") else 0,
            files_changed,
            counts["added"],
            counts["removed"],
            counts["interface_changed"],
            counts["effects_changed"],
            counts["body_only"],
            byte_size,
        ))
        seq = cur.lastrowid
        db.executemany(
            "INSERT INTO meta_changeset_deltas VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
            ((seq, *row) for row in deltas),
        )
        # Enforce bounded ring buffer: max MAX_META_CHANGESETS and MAX_META_HISTORY_BYTES
        seqs = db.execute("SELECT seq, byte_size FROM meta_changesets ORDER BY seq DESC").fetchall()
        keep_seqs: set[int] = set()
        running_bytes = 0
        for idx, (s_id, b_sz) in enumerate(seqs):
            if idx < MAX_META_CHANGESETS and (idx == 0 or running_bytes + b_sz <= MAX_META_HISTORY_BYTES):
                keep_seqs.add(s_id)
                running_bytes += b_sz
        prune_seqs = [s_id for s_id, _ in seqs if s_id not in keep_seqs]
        if prune_seqs:
            placeholders = ",".join("?" for _ in prune_seqs)
            db.execute(f"DELETE FROM meta_changeset_deltas WHERE seq IN ({placeholders})", prune_seqs)
            db.execute(f"DELETE FROM meta_changesets WHERE seq IN ({placeholders})", prune_seqs)

    # Carry forward meta_cards and update freshness surgically
    if db.execute("SELECT 1 FROM prev_snap.sqlite_master WHERE type='table' AND name='meta_cards'").fetchone():
        prev_cards = db.execute("""
            SELECT c.symbol_id, c.file, c.symbol, c.kind,
                   c.body_hash, c.interface_hash, c.effects_hash,
                   c.callee_interface_digest, c.freshness, c.stale_reason,
                   c.updated_at, c.payload,
                   m.body_hash, m.interface_hash, m.effects_hash
            FROM prev_snap.meta_cards c
            LEFT JOIN main.meta_symbols m ON m.id = c.symbol_id
        """).fetchall()
        if prev_cards:
            card_files = {row[1] for row in prev_cards if row[12] is not None}
            callee_digests = _callee_interface_digests(db, card_files)
            carried: list[tuple] = []
            for (
                sym_id, c_file, c_sym, c_kind,
                c_bhash, c_ihash, c_ehash, c_cdigest,
                c_fresh, c_reason, c_updated, c_payload,
                m_bhash, m_ihash, m_ehash,
            ) in prev_cards:
                if m_bhash is None:
                    freshness = "orphan"
                    reason = "symbol-removed"
                elif c_ihash != m_ihash:
                    freshness = "stale_interface"
                    reason = "symbol-interface-changed"
                elif c_ehash != m_ehash:
                    freshness = "stale_body"
                    reason = "symbol-effects-changed"
                elif c_bhash != m_bhash:
                    freshness = "stale_body"
                    reason = "symbol-body-changed"
                else:
                    curr_cdigest = callee_digests.get(sym_id, "")
                    if c_cdigest != curr_cdigest:
                        freshness = "stale_callee"
                        reason = "callee-interface-changed"
                    else:
                        freshness = c_fresh if c_fresh != "orphan" else "fresh"
                        reason = c_reason if freshness != "fresh" else None
                carried.append((
                    sym_id, c_file, c_sym, c_kind,
                    c_bhash, c_ihash, c_ehash, c_cdigest,
                    freshness, reason, c_updated, c_payload,
                ))
            db.executemany("INSERT INTO main.meta_cards VALUES(?,?,?,?,?,?,?,?,?,?,?,?)", carried)


def build_semantic_store(
    store: SnapshotStore,
    *,
    writer: SnapshotWriter,
    previous: SnapshotStore | None = None,
    reused_files: set[str] | None = None,
    perimeter: Perimeter | None = None,
) -> None:
    db = writer.connection
    _schema(db)
    root = Path(store["root"]).resolve()
    target = (root / store["target"]).resolve()
    if perimeter is None:
        perimeter = Perimeter(target)
    fingerprint = snapshot.parser_fingerprint()
    observed = db.execute("SELECT 1 FROM sqlite_master WHERE name='observed_coverage'").fetchone() is not None

    can_reuse = _can_reuse_previous_semantics(previous, reused_files)
    prev_attached = False
    if can_reuse and previous is not None and previous.path is not None:
        db.execute("ATTACH DATABASE ? AS prev_snap", (str(previous.path),))
        prev_attached = True

    try:
        sem_reused_set: set[str] = set()
        curr_all_paths = set(store.iter_paths())
        config_changed = True
        set_of_paths_changed = True
        if prev_attached and reused_files:
            prev_all_paths = {r[0] for r in db.execute("SELECT path FROM prev_snap.files")}
            set_of_paths_changed = prev_all_paths != curr_all_paths
            prev_verified = {r[0] for r in db.execute("SELECT file FROM prev_snap.sem_coverage WHERE verified=1")}
            for rel in reused_files:
                if rel not in prev_verified or snapshot.is_forbidden(Path(rel).name):
                    continue
                resolved = (root / rel).resolve()
                if (resolved.is_relative_to(target) or resolved == target) and perimeter.covers(resolved):
                    sem_reused_set.add(rel)
            config_names = {"tsconfig.json", "jsconfig.json", "package.json"}
            changed_or_removed = (curr_all_paths ^ prev_all_paths) | (curr_all_paths - sem_reused_set)
            config_changed = any(Path(p).name in config_names for p in changed_or_removed)

        if sem_reused_set:
            db.execute("CREATE TEMP TABLE _sem_reused(file TEXT PRIMARY KEY)")
            db.executemany("INSERT INTO _sem_reused VALUES(?)", ((rel,) for rel in sem_reused_set))
            db.execute("INSERT INTO main.sem_coverage SELECT * FROM prev_snap.sem_coverage WHERE file IN (SELECT file FROM _sem_reused)")
            db.execute("INSERT INTO main.sem_scopes SELECT * FROM prev_snap.sem_scopes WHERE file IN (SELECT file FROM _sem_reused)")
            db.execute("INSERT INTO main.sem_declarations SELECT * FROM prev_snap.sem_declarations WHERE file IN (SELECT file FROM _sem_reused)")
            db.execute("INSERT INTO main.sem_bindings SELECT * FROM prev_snap.sem_bindings WHERE file IN (SELECT file FROM _sem_reused)")
            db.execute("INSERT INTO main.sem_exports SELECT * FROM prev_snap.sem_exports WHERE file IN (SELECT file FROM _sem_reused)")

        changed_files = sorted(curr_all_paths - sem_reused_set)
        file_iter = (
            ((rel, store.get_file(rel)) for rel in changed_files)
            if sem_reused_set
            else store.iter_files()
        )
        for rel, entry in file_iter:
            if entry is None:
                continue
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

        if sem_reused_set and not set_of_paths_changed and not config_changed:
            db.execute("INSERT INTO main.sem_modules SELECT * FROM prev_snap.sem_modules WHERE file IN (SELECT file FROM _sem_reused)")
            if changed_files:
                config = snapshot.ts_path_config(target, source_observations=ConfigObservations(store, perimeter=perimeter))
                for rel, modules in snapshot.iter_resolved_imports(
                    store, config, include_self=True, only_importers=set(changed_files), perimeter=perimeter
                ):
                    for module, targets in modules.items():
                        db.executemany("INSERT INTO sem_modules VALUES(?,?,?)", ((rel, module, target) for target in targets))
        else:
            config = snapshot.ts_path_config(target, source_observations=ConfigObservations(store, perimeter=perimeter))
            for rel, modules in snapshot.iter_resolved_imports(store, config, include_self=True, perimeter=perimeter):
                for module, targets in modules.items():
                    db.executemany("INSERT INTO sem_modules VALUES(?,?,?)", ((rel, module, target) for target in targets))

        db.execute("""INSERT OR IGNORE INTO sem_edges SELECT m.file,m.target FROM sem_modules m
                      JOIN sem_coverage a ON a.file=m.file AND a.verified=1
                      JOIN sem_coverage b ON b.file=m.target AND b.verified=1""")

        ref_reused_set: set[str] = set()
        if sem_reused_set:
            if not set_of_paths_changed and not config_changed:
                if not changed_files:
                    ref_reused_set = set(sem_reused_set)
                else:
                    dirty_importers = {
                        r[0] for r in db.execute("""
                            SELECT DISTINCT file FROM main.sem_modules
                            WHERE file IN (SELECT file FROM _sem_reused)
                              AND target NOT IN (SELECT file FROM _sem_reused)
                        """)
                    }
                    ref_reused_set = sem_reused_set - dirty_importers
            else:
                dirty_importers = {
                    r[0] for r in db.execute("""
                        SELECT DISTINCT m.file FROM main.sem_modules m
                        WHERE m.file IN (SELECT file FROM _sem_reused)
                          AND m.target NOT IN (SELECT file FROM _sem_reused)
                        UNION
                        SELECT DISTINCT p.file FROM prev_snap.sem_modules p
                        WHERE p.file IN (SELECT file FROM _sem_reused)
                          AND NOT EXISTS (
                              SELECT 1 FROM main.sem_modules m
                              WHERE m.file = p.file AND m.module = p.module AND m.target = p.target
                          )
                        UNION
                        SELECT DISTINCT m.file FROM main.sem_modules m
                        WHERE m.file IN (SELECT file FROM _sem_reused)
                          AND NOT EXISTS (
                              SELECT 1 FROM prev_snap.sem_modules p
                              WHERE p.file = m.file AND p.module = m.module AND p.target = m.target
                          )
                    """)
                }
                ref_reused_set = sem_reused_set - dirty_importers

        if ref_reused_set:
            db.execute("CREATE TEMP TABLE _sem_ref_reused(file TEXT PRIMARY KEY)")
            db.executemany("INSERT INTO _sem_ref_reused VALUES(?)", ((rel,) for rel in ref_reused_set))
            db.execute("INSERT INTO main.sem_references SELECT * FROM prev_snap.sem_references WHERE file IN (SELECT file FROM _sem_ref_reused)")
            db.execute("""
                INSERT INTO main.sem_reference_candidates
                SELECT * FROM prev_snap.sem_reference_candidates
                WHERE reference IN (SELECT id FROM main.sem_references WHERE file IN (SELECT file FROM _sem_ref_reused))
            """)
            ast_query = "SELECT file FROM sem_coverage WHERE status='ast' AND file NOT IN (SELECT file FROM _sem_ref_reused) ORDER BY file"
        else:
            ast_query = "SELECT file FROM sem_coverage WHERE status='ast' ORDER BY file"

        resolver = _Resolver(db)
        for (rel,) in db.execute(ast_query):
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

        can_copy_metrics = (
            prev_attached
            and not set_of_paths_changed
            and not config_changed
            and not changed_files
            and db.execute("SELECT 1 FROM prev_snap.sqlite_master WHERE type='table' AND name='sem_graph_meta'").fetchone() is not None
        )
        if can_copy_metrics:
            db.executescript("""
                CREATE TABLE sem_rank(node TEXT PRIMARY KEY,score REAL,next REAL,degree INTEGER,visited INTEGER,finished INTEGER);
                CREATE TABLE sem_cycles(component TEXT,ordinal INTEGER,node TEXT,PRIMARY KEY(component,ordinal));
                CREATE TABLE sem_graph_meta(key TEXT PRIMARY KEY,payload BLOB NOT NULL);
                INSERT INTO main.sem_rank SELECT * FROM prev_snap.sem_rank;
                INSERT INTO main.sem_cycles SELECT * FROM prev_snap.sem_cycles;
                INSERT INTO main.sem_graph_meta SELECT * FROM prev_snap.sem_graph_meta;
            """)
        else:
            from store_graph_metrics import build_metrics
            build_metrics(db, prefix="sem", temporary=False,
                          nodes="SELECT file FROM sem_coverage WHERE verified=1",
                          edges="SELECT source,target FROM sem_edges")

        if store.format == "sqlite":
            recompute_meta = (curr_all_paths - ref_reused_set) if ref_reused_set else None
            _build_meta_symbols(db, recompute_meta, prev_attached)
            _record_meta_changeset_and_carry_cards(db, store, prev_attached)

        db.execute("DROP TABLE IF EXISTS _sem_ref_reused")
        db.execute("DROP TABLE IF EXISTS _sem_reused")
    finally:
        if prev_attached:
            db.commit()
            db.execute("DETACH DATABASE prev_snap")

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


def upsert_meta_cards(snapshot_path: Path | str, cards: list[dict]) -> dict:
    """Insert or patch persistent Meta-Code cards bound to current symbol triple-hashes."""
    path = Path(snapshot_path)
    db = sqlite3.connect(path)
    _settings(db)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    upserted = 0
    missing: list[str] = []
    try:
        target_files: set[str] = set()
        resolved_targets: list[tuple[tuple, dict]] = []
        for item in cards:
            sym_id = item.get("symbol_id") or f"{item.get('file', '')}::{item.get('symbol', '')}"
            row = db.execute(
                "SELECT id, file, name, kind, body_hash, interface_hash, effects_hash FROM meta_symbols WHERE id=?",
                (sym_id,),
            ).fetchone()
            if row is None:
                missing.append(sym_id)
                continue
            target_files.add(row[1])
            resolved_targets.append((row, item))
        callee_digests = _callee_interface_digests(db, target_files) if target_files else {}
        with db:
            for (sym_id, file, name, kind, b_hash, i_hash, e_hash), item in resolved_targets:
                payload = {
                    k: item[k]
                    for k in (
                        "purpose",
                        "preconditions",
                        "postconditions",
                        "invariants",
                        "side_effects",
                        "failure_modes",
                        "notes",
                        "confidence",
                    )
                    if k in item
                }
                c_digest = callee_digests.get(sym_id, "")
                db.execute(
                    "INSERT OR REPLACE INTO meta_cards VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        sym_id,
                        file,
                        name,
                        kind,
                        b_hash,
                        i_hash,
                        e_hash,
                        c_digest,
                        "fresh",
                        None,
                        item.get("updated_at") or now,
                        _pack(payload),
                    ),
                )
                upserted += 1
    finally:
        db.close()
    return {"upserted": upserted, "missing_symbols": missing}


def query_meta_code(
    store: SnapshotStore,
    *,
    paths: list[str] | None = None,
    symbol: str | None = None,
    freshness: str | None = None,
    include_history: bool = True,
    limit: int = 100,
) -> dict:
    """Query the triple-hash Meta-Code index, cards, freshness state, and bounded N-changeset history."""
    with semantic_reader(store) as db:
        has_meta = db.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='meta_symbols'"
        ).fetchone() is not None
        if not has_meta:
            return {
                "summary": {"total_symbols": 0, "cards": {}, "changesets": 0, "history_bytes": 0},
                "symbols": [],
                "changesets": [],
            }
        total_symbols = db.execute("SELECT COUNT(*) FROM meta_symbols").fetchone()[0]
        card_counts = dict(
            db.execute("SELECT freshness, COUNT(*) FROM meta_cards GROUP BY freshness").fetchall()
        )
        cs_meta = db.execute(
            "SELECT COUNT(*), COALESCE(SUM(byte_size), 0) FROM meta_changesets"
        ).fetchone()

        clauses: list[str] = []
        params: list[object] = []
        if paths:
            placeholders = ",".join("?" for _ in paths)
            clauses.append(f"m.file IN ({placeholders})")
            params.extend(paths)
        if symbol:
            clauses.append("(m.name = ? OR m.id = ? OR m.name LIKE ?)")
            params.extend([symbol, symbol, f"%.{symbol}"])
        if freshness == "uncovered":
            clauses.append("c.symbol_id IS NULL")
        elif freshness:
            clauses.append("c.freshness = ?")
            params.append(freshness)
        where_sql = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        rows = db.execute(
            f"""
            SELECT m.id, m.file, m.name, m.kind, m.start, m.end,
                   m.body_hash, m.interface_hash, m.effects_hash, m.exported,
                   c.freshness, c.stale_reason, c.updated_at, c.payload
            FROM meta_symbols m
            LEFT JOIN meta_cards c ON c.symbol_id = m.id
            {where_sql}
            ORDER BY m.file, m.start, m.name
            LIMIT ?
            """,
            [*params, max(1, int(limit))],
        ).fetchall()
        symbols_out = []
        for (
            sym_id, file, name, kind, start, end,
            b_hash, i_hash, e_hash, exported,
            c_fresh, c_reason, c_updated, c_payload,
        ) in rows:
            entry = {
                "symbol_id": sym_id,
                "file": file,
                "name": name,
                "kind": kind,
                "start": start,
                "end": end,
                "body_hash": b_hash,
                "interface_hash": i_hash,
                "effects_hash": e_hash,
                "exported": bool(exported),
                "freshness": c_fresh or "uncovered",
                "stale_reason": c_reason,
                "card": _unpack(c_payload) if c_payload is not None else None,
                "card_updated_at": c_updated,
            }
            symbols_out.append(entry)

        changesets_out = []
        if include_history:
            cs_rows = db.execute(
                """
                SELECT seq, created_at, git_head, git_dirty, files_changed,
                       symbols_added, symbols_removed, interfaces_changed,
                       effects_changed, bodies_only_changed, byte_size
                FROM meta_changesets
                ORDER BY seq DESC
                """
            ).fetchall()
            for (
                seq, created_at, git_head, git_dirty, files_changed,
                s_add, s_rem, i_chg, e_chg, b_chg, b_sz,
            ) in cs_rows:
                delta_rows = db.execute(
                    """
                    SELECT symbol_id, file, name, change_kind,
                           old_body_hash, new_body_hash,
                           old_interface_hash, new_interface_hash,
                           old_effects_hash, new_effects_hash,
                           old_span, new_span
                    FROM meta_changeset_deltas
                    WHERE seq = ?
                    ORDER BY file, name
                    """,
                    (seq,),
                ).fetchall()
                changesets_out.append({
                    "seq": seq,
                    "created_at": created_at,
                    "git_head": git_head,
                    "git_dirty": bool(git_dirty),
                    "files_changed": files_changed,
                    "symbols_added": s_add,
                    "symbols_removed": s_rem,
                    "interfaces_changed": i_chg,
                    "effects_changed": e_chg,
                    "bodies_only_changed": b_chg,
                    "byte_size": b_sz,
                    "deltas": [
                        {
                            "symbol_id": d[0],
                            "file": d[1],
                            "name": d[2],
                            "change_kind": d[3],
                            "old_body_hash": d[4],
                            "new_body_hash": d[5],
                            "old_interface_hash": d[6],
                            "new_interface_hash": d[7],
                            "old_effects_hash": d[8],
                            "new_effects_hash": d[9],
                            "old_span": d[10],
                            "new_span": d[11],
                        }
                        for d in delta_rows
                    ],
                })
        return {
            "summary": {
                "total_symbols": total_symbols,
                "cards": card_counts,
                "changesets": cs_meta[0],
                "history_bytes": cs_meta[1],
            },
            "symbols": symbols_out,
            "changesets": changesets_out,
        }
