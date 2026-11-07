"""Persistent conservative semantic bindings; only one file payload is decoded at once."""
from __future__ import annotations

from collections.abc import Mapping
from contextlib import contextmanager
from datetime import datetime, timezone
import ast
import hashlib
import itertools
import json
from pathlib import Path
import re
import sqlite3
import tempfile
import textwrap

import snapshot
from snapshot_store import SnapshotStore, SnapshotWriter, _pack, _unpack, _settings, logical_digest
from tree_scope import Perimeter
import card_store
import resolution
import semantic_index

RESOLVER_VERSION = 3
# The resolution policy and its reason vocabulary live in resolution.py, shared with
# semantic_index so the two owners of the source graph cannot disagree. Re-exported
# here because consumers and tests read both names from this module.
TARGET_KINDS = resolution.TARGET_KINDS
MRO_LIMIT = resolution.MRO_LIMIT
MAX_META_CHANGESETS = 16
MAX_META_HISTORY_BYTES = 4 * 1024 * 1024
# The algorithm behind interface_hash. A digest carries it as a `v<N>:` prefix,
# and an unprefixed digest is version 1 (parameter names only), so a digest
# computed by another algorithm is told apart instead of read as an edit.
INTERFACE_DIGEST_VERSION = 2


def digest_version(digest: object) -> int:
    """The algorithm version of a `v<N>:`-prefixed digest; 1 when unprefixed."""
    if isinstance(digest, str):
        head, separator, _ = digest.partition(":")
        if separator and head[:1] == "v" and head[1:].isdigit():
            return int(head[1:])
    return 1


def _interface_digest(contract: dict) -> str:
    canonical = json.dumps(contract, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return f"v{INTERFACE_DIGEST_VERSION}:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


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
        record = self.scope_record(rel, identity)
        if record is None:
            raise ValueError("semantic scope is missing")
        return record

    def scope_record(self, rel, scope_id):
        """One scope's payload, or None: the shared policy tolerates an absent scope."""
        row = self.db.execute("SELECT payload FROM sem_scopes WHERE file=? AND id=?", (rel, scope_id)).fetchone()
        return _unpack(row[0]) if row else None

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

    def language(self, rel):
        row = self.db.execute("SELECT language FROM sem_coverage WHERE file=?", (rel,)).fetchone()
        return row[0] if row else None

    def bindings_named(self, rel, scope_id, name):
        """Every binding is relevant: a non-callable member blocks a base member."""
        return [self.binding(row) for row in self.bindings(rel, scope_id, name)]

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
                  "resolver": resolution.LEXICAL_RESOLVER,
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
                found = (resolution.instance_method(self, rel, item, parts)
                         if len(parts) == 2 else None)
                if found is None:
                    record["reason"] = "unknown-receiver"
                else:
                    record.update(target_id=found[0], resolution="resolved", reason=found[1])
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
        elif imported["mode"] == "named" and len(parts) == 2 and self.language(rel) == "python":
            # Checked before the single-target rule: a Python relative import keys
            # the module as written, so one file's several `from . import x`
            # statements share the key "." and only the imported name picks the file.
            identity, reason = resolution.module_attribute(self, rel, imported, parts[1])
            record["imported_name"] = parts[1]
            record.update(target_id=identity, reason=reason)
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
    target_key,
) -> list[tuple]:
    """Meta-symbol rows of one file.

    `target_key` maps a reference target to a key that survives an edit elsewhere.
    The ids in sem_references are positional (`function@4:0`), so hashing them
    would change the effects of an untouched caller whenever a callee below an
    edit moved down a line.

    The interface digest covers the symbol's kind, name, export, the parameter
    names its semantic declarations bind and the adapter's signature records
    (parameter kinds, annotations, defaults, return, async, generator,
    decorators; bases and attributes of a class), and a class's members. A
    symbol with neither declarations nor an exhaustive signature falls back to
    its body: any edit may then have changed its contract.
    """
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
        signatures = sym.get("signatures") or []
        sym_info[name] = {
            "sym": sym,
            "start": start,
            "end": end,
            "matched_decls": set(matched_decls),
            "own": {"params": param_names, "signatures": signatures},
            "exhaustive": bool(signatures) and all(
                isinstance(item, dict) and item.get("fields") for item in signatures),
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
        contract = {"kind": kind, "name": name, "exported": is_exp}
        if kind == "class":
            prefix = name + "."
            # Direct members only. A definition nested inside a method is its own
            # symbol now, and it is not part of the class contract: including it
            # would make a private helper's signature change propagate to every
            # caller of the class.
            contract.update(info["own"], members={
                m_name[len(prefix):]: m_info["own"]
                for m_name, m_info in sym_info.items()
                if m_name.startswith(prefix) and "." not in m_name[len(prefix):]
            })
        elif matched_decls or info["exhaustive"]:
            contract.update(info["own"])
        else:
            contract["body"] = body_hash
        interface_hash = _interface_digest(contract)

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
                effects.add((r_kind, target_key(target_id), last_name or "", resolution))
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

    stable: dict[str, str] = {}

    def target_key(target_id):
        if not target_id:
            return ""
        if target_id not in stable:
            row = db.execute("SELECT file,name,payload FROM sem_declarations WHERE id=?", (target_id,)).fetchone()
            stable[target_id] = (f"{row[0]}::{_unpack(row[2]).get('qualified_name') or row[1]}"
                                 if row else target_id)
        return stable[target_id]

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
            target_key,
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


def _record_meta_changeset(
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
            _record_meta_changeset(db, store, prev_attached)

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


def install_edge_view(db, store, *, engine_store=None, limit=100):
    """Materialize effective references on the reader connection, never the snapshot.

    Card digests continue to query sem_references. Consumer queries explicitly
    use effective_references, so merely installing an engine cannot age cards.
    """
    from edge_view import load_edge_view
    view = load_edge_view(store, engine_store=engine_store)
    db.execute("CREATE TEMP TABLE effective_references AS SELECT * FROM sem_references")
    db.execute("CREATE INDEX temp.effective_target ON effective_references(target_id)")
    db.execute("CREATE UNIQUE INDEX temp.effective_id ON effective_references(id)")
    coverage = "q_cover" if db.execute(
        "SELECT 1 FROM sqlite_temp_master WHERE name='q_cover'").fetchone() else "sem_coverage"
    allowed = {r[0] for r in db.execute(f"SELECT file FROM {coverage} WHERE verified=1")}
    targets = {r[0] for r in db.execute("SELECT id,file FROM sem_declarations") if r[1] in allowed}
    for ref in view["references"]:
        if ref["file"] not in allowed or (ref["target_id"] and ref["target_id"] not in targets):
            continue
        db.execute("UPDATE effective_references SET target_id=?,resolution=?,payload=? WHERE id=?",
                   (ref["target_id"], ref["resolution"], _pack(ref), ref["id"]))
    summary = {key: view[key] for key in ("schema", "version", "profile", "coverage", "gaps")}
    summary["profile"] = {key: value for key, value in view["profile"].items() if key != "engine_report"}
    for key in ("candidates", "conflicts"):
        summary[key] = {"items": view[key][:limit], "total": len(view[key]),
                        "truncated": max(0, len(view[key]) - limit)}
    db.execute("CREATE TEMP TABLE effective_metadata(payload BLOB)")
    db.execute("INSERT INTO effective_metadata VALUES(?)", (_pack(summary),))
    return summary


def query_graph(store, paths=None, hops=2, limit=100, *, engine_store=None):
    from store_graph import query_graph as query
    return query(store, paths, hops, limit, engine_store=engine_store)


def query_references(store, declaration_id, *, engine_store=None):
    from store_consumers import consumer_reader
    with consumer_reader(store, engine_store=engine_store) as db:
        for (payload,) in db.execute("SELECT payload FROM effective_references WHERE target_id=? ORDER BY file,l0,c0,l1,c1,id", (declaration_id,)):
            yield _unpack(payload)


CARD_FRESHNESS = ("fresh", "stale_body", "stale_interface", "stale_callee", "orphan")
MAX_CARD_BATCH = 500


class _Cards:
    """The cards of one root, judged against the snapshot being read.

    A card keeps the digests of the symbol it was written against. Here they are
    compared with this snapshot's symbols, so one card can be fresh in a snapshot
    and stale in the next without anything having to carry it forward.
    """

    def __init__(self, db, cards_path, root):
        self.path, self.root = cards_path, root
        rows = card_store.digests(cards_path, root) if cards_path is not None else []
        self.rows = {row[0]: row for row in rows}
        self.states = self._judge(db) if self.rows else {}
        self._payloads: dict[str, dict] = {}

    def _judge(self, db):
        symbols = {row[0]: row for row in db.execute(
            "SELECT id,body_hash,interface_hash,effects_hash FROM meta_symbols") if row[0] in self.rows}
        states, pending = {}, {}
        for symbol_id, (_id, file, _name, body, interface, effects, _callee, _at) in self.rows.items():
            current = symbols.get(symbol_id)
            if current is None:
                states[symbol_id] = ("orphan", "symbol-removed")
            elif digest_version(interface) != digest_version(current[2]):
                # Written against another interface algorithm: the two digests do
                # not compare, so the card is re-read rather than called changed.
                states[symbol_id] = ("stale_interface", "digest-version-changed")
            elif interface != current[2]:
                states[symbol_id] = ("stale_interface", "symbol-interface-changed")
            elif effects != current[3]:
                states[symbol_id] = ("stale_body", "symbol-effects-changed")
            elif body != current[1]:
                states[symbol_id] = ("stale_body", "symbol-body-changed")
            else:
                pending[symbol_id] = file
        if pending:
            callee = _callee_interface_digests(db, set(pending.values()))
            for symbol_id in pending:
                same = callee.get(symbol_id, "") == self.rows[symbol_id][6]
                states[symbol_id] = ("fresh", None) if same else ("stale_callee", "callee-interface-changed")
        return states

    def counts(self) -> dict[str, int]:
        found: dict[str, int] = {}
        for freshness, _reason in self.states.values():
            found[freshness] = found.get(freshness, 0) + 1
        return found

    def prefetch(self, symbol_ids):
        wanted = [i for i in symbol_ids if i in self.states and i not in self._payloads]
        if wanted:
            self._payloads.update(card_store.read_cards(self.path, self.root, wanted))

    def get(self, symbol_id):
        """Freshness, reason, timestamp and stored fields of a card, or None."""
        if symbol_id not in self.states:
            return None
        self.prefetch([symbol_id])
        freshness, reason = self.states[symbol_id]
        return {**self._payloads.get(symbol_id, {}), "freshness": freshness,
                "stale_reason": reason, "freshness_basis": "lexical"}


def upsert_meta_cards(store: SnapshotStore, cards_path: Path | str, cards: list[dict]) -> dict:
    """Write cards to the project's card store, bound to the digests of `store`.

    The snapshot is only read: a run's snapshot is immutable evidence, so the cards
    live in their own file and are judged against whichever snapshot is queried.
    A card names its symbol by `symbol_id`, or by `file` and `symbol`. A symbol the
    snapshot does not hold is reported in `missing_symbols` and not written.
    """
    if store.format != "sqlite":
        raise ValueError("Meta-Code requires a SQLite snapshot")
    if not isinstance(cards, list) or not 1 <= len(cards) <= MAX_CARD_BATCH:
        raise ValueError(f"cards must be a list of 1 to {MAX_CARD_BATCH} cards")
    prepared: list[tuple[str, dict]] = []
    for item in cards:
        payload = card_store.validate_card(item)
        symbol_id = item.get("symbol_id")
        if symbol_id is None:
            file, symbol = item.get("file"), item.get("symbol")
            if not isinstance(file, str) or not isinstance(symbol, str) or not file or not symbol:
                raise ValueError("a card needs symbol_id, or both file and symbol")
            symbol_id = f"{file}::{symbol}"
        if not isinstance(symbol_id, str) or not symbol_id or len(symbol_id) > 1000:
            raise ValueError("symbol_id must be text of at most 1000 characters")
        prepared.append((symbol_id, payload))

    root = store.metadata.get("root")
    rows: list[dict] = []
    missing: list[str] = []
    found: dict[str, tuple] = {}
    with semantic_reader(store) as db:
        for symbol_id, _payload in prepared:
            row = db.execute(
                "SELECT id,file,name,kind,body_hash,interface_hash,effects_hash FROM meta_symbols WHERE id=?",
                (symbol_id,)).fetchone()
            if row is None:
                missing.append(symbol_id)
            else:
                found[symbol_id] = row
        callee = _callee_interface_digests(db, {row[1] for row in found.values()}) if found else {}
    for symbol_id, payload in prepared:
        row = found.get(symbol_id)
        if row is not None:
            rows.append({"symbol_id": symbol_id, "file": row[1], "symbol": row[2], "kind": row[3],
                         "body_hash": row[4], "interface_hash": row[5], "effects_hash": row[6],
                         "callee_digest": callee.get(symbol_id, ""), "payload": payload})
    if rows:
        card_store.write_cards(cards_path, root, rows)
    return {"upserted": len(rows), "missing_symbols": missing, "store": str(cards_path)}


def query_meta_code(
    store: SnapshotStore,
    *,
    cards_path: Path | str | None = None,
    paths: list[str] | None = None,
    symbol: str | None = None,
    freshness: str | None = None,
    include_history: bool = True,
    limit: int = 100,
) -> dict:
    """Query the Meta-Code index, its cards with their freshness, and the bounded changeset history.

    `freshness` filters to one of `fresh`, `stale_body`, `stale_interface`,
    `stale_callee`, `uncovered` (a symbol with no card) or `orphan` (a card whose
    symbol the snapshot no longer holds, listed under `orphans`).
    """
    if store.format != "sqlite":
        raise ValueError("Meta-Code requires a SQLite snapshot")
    if freshness is not None and freshness not in (*CARD_FRESHNESS, "uncovered"):
        raise ValueError("freshness must be one of: " + ", ".join((*CARD_FRESHNESS, "uncovered")))
    with semantic_reader(store) as db:
        has_meta = db.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='meta_symbols'"
        ).fetchone() is not None
        if not has_meta:
            return {
                "summary": {"total_symbols": 0, "cards": {}, "changesets": 0, "history_bytes": 0},
                "symbols": [],
                "orphans": [],
                "changesets": [],
            }
        cards = _Cards(db, cards_path, store.metadata.get("root"))
        total_symbols = db.execute("SELECT COUNT(*) FROM meta_symbols").fetchone()[0]
        card_counts = cards.counts()
        card_counts["uncovered"] = total_symbols - sum(
            count for name, count in card_counts.items() if name != "orphan")
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
        where_sql = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        limit = max(1, int(limit))
        selected = []
        if freshness != "orphan":
            for row in db.execute(f"{_SYMBOL_SELECT} {where_sql} ORDER BY m.file, m.start, m.name", params):
                state = cards.states.get(row[0], ("uncovered", None))[0]
                if freshness is None or state == freshness:
                    selected.append(row)
                    if len(selected) == limit:
                        break
        cards.prefetch([row[0] for row in selected])
        symbols_out = []
        for sym_id, file, name, kind, start, end, b_hash, i_hash, e_hash, exported, spec in selected:
            card = cards.get(sym_id)
            symbols_out.append({
                "symbol_id": sym_id,
                "file": file,
                "name": name,
                "kind": kind,
                "start": start,
                "end": end,
                "body_hash": b_hash,
                "interface_hash": i_hash,
                "effects_hash": e_hash,
                "signatures": _signatures(spec),
                "exported": bool(exported),
                "freshness": card["freshness"] if card else "uncovered",
                "stale_reason": card["stale_reason"] if card else None,
                "card": ({k: v for k, v in card.items() if k not in ("freshness", "stale_reason", "updated_at")}
                         if card else None),
                "card_updated_at": card.get("updated_at") if card else None,
            })
        orphans = []
        if freshness == "orphan":
            for symbol_id, file, name, *_digests, updated_at in cards.rows.values():
                if cards.states[symbol_id][0] == "orphan" and (not paths or file in paths):
                    orphans.append({"symbol_id": symbol_id, "file": file, "symbol": name, "card_updated_at": updated_at})
            orphans = orphans[:limit]

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
            "orphans": orphans,
            "changesets": changesets_out,
        }


EDIT_IMPACT_SCHEMA = "daodan/edit-impact/v2"
MAX_IMPACT_TARGETS = 25
DEFAULT_IMPACT_BUDGET_CHARS = 120_000
MAX_IMPACT_BUDGET_CHARS = 4_000_000
# A name no scope binds is a builtin or an undeclared global: counted, not listed.
_NOT_A_BLIND_SPOT = frozenset({"unbound-name"})
# A Meta-Code row with its manifest symbol entry, where the signature records live.
_SYMBOL_SELECT = ("SELECT m.id,m.file,m.name,m.kind,m.start,m.end,m.body_hash,m.interface_hash,"
                  "m.effects_hash,m.exported,s.payload FROM meta_symbols m "
                  "LEFT JOIN symbols s ON s.file=m.file AND s.name=m.name")


def _signatures(spec_blob):
    """The signature records of a packed manifest symbol entry, or None."""
    return _unpack(spec_blob).get("signatures") if spec_blob is not None else None


class _ImpactIndex:
    """Per-file lookups over the Meta-Code index, read once per file."""

    def __init__(self, db):
        self.db = db
        self._symbols: dict[str, list] = {}
        self._declarations: dict[str, list] = {}

    def symbols(self, file):
        if file not in self._symbols:
            self._symbols[file] = self.db.execute(
                f"{_SYMBOL_SELECT} WHERE m.file=? ORDER BY m.start,m.end", (file,)
            ).fetchall()
        return self._symbols[file]

    def declarations(self, file):
        if file not in self._declarations:
            rows = self.db.execute(
                "SELECT id,name,l0,payload FROM sem_declarations WHERE file=? AND kind IN ('function','class')",
                (file,),
            ).fetchall()
            self._declarations[file] = [
                (ident, _unpack(payload).get("qualified_name") or name, name, line)
                for ident, name, line, payload in rows
            ]
        return self._declarations[file]

    def declaration_ids(self, symbol):
        """Declarations a manifest symbol stands for, by qualified name, then by position."""
        _, file, name, _kind, start, end = symbol[:6]
        short = name.split(".")[-1]
        found = [ident for ident, qualified, _n, _l in self.declarations(file) if qualified == name]
        return found or [ident for ident, _q, n, line in self.declarations(file)
                         if n == short and start <= line <= end]

    def enclosing(self, file, line):
        inside = [s for s in self.symbols(file) if s[4] <= line <= s[5]]
        return min(inside, key=lambda s: s[5] - s[4]) if inside else None

    def symbol_for_declaration(self, ident):
        row = self.db.execute(
            "SELECT file,name,l0,payload FROM sem_declarations WHERE id=?", (ident,)
        ).fetchone()
        if row is None:
            return None
        file, name, line, payload = row
        qualified = _unpack(payload).get("qualified_name") or name
        for symbol in self.symbols(file):
            if symbol[2] == qualified:
                return symbol
        return self.enclosing(file, line)


def _symbol_fields(row):
    sym_id, file, name, kind, start, end, body, interface, effects, _exported, spec = row
    return {"symbol_id": sym_id, "file": file, "name": name, "kind": kind, "start": start,
            "end": end, "body_hash": body, "interface_hash": interface, "effects_hash": effects,
            "signatures": _signatures(spec)}


def _site(file, kind, start_line, start_col, end_line, end_col):
    return {"file": file, "kind": kind, "start_line": start_line, "start_column": start_col,
            "end_line": end_line, "end_column": end_col}


def _add_reference(found, row, kind, site):
    item = found.setdefault(row[0], [row, 0, {}])
    item[1] += 1
    edge = item[2].setdefault(kind, {"kind": kind, "count": 0, "sites": []})
    edge["count"] += 1
    if site not in edge["sites"]:
        edge["sites"].append(site)


def _neighbors(cards, found, limit):
    """Rank neighbours by how often they are referenced; cap, and report the total."""
    ranked = sorted(found.values(), key=lambda item: (-item[1], item[0][0]))
    cards.prefetch([symbol[0] for symbol, _count, *_rest in ranked[:limit]])
    listed = []
    for item in ranked[:limit]:
        symbol, count = item[0], item[1]
        entry = _symbol_fields(symbol)
        entry["references"] = count
        entry["edges"] = [item[2][kind] for kind in sorted(item[2])] if len(item) > 2 else []
        entry["card"] = cards.get(symbol[0])
        listed.append(entry)
    return {"total": len(ranked), "listed": listed}


def _direct_edges(db, index, symbol):
    """Resolved callers and callees of one symbol, with exact reference sites."""
    sym_id, file, _name, _kind, start, end = symbol[:6]

    def inside_target(other):
        return other[1] == file and start <= other[4] and other[5] <= end

    callers: dict = {}
    declaration_ids = index.declaration_ids(symbol)
    if declaration_ids:
        marks = ",".join("?" for _ in declaration_ids)
        for ref_file, kind, l0, c0, l1, c1, payload in db.execute(
            f"SELECT file,kind,l0,c0,l1,c1,payload FROM effective_references WHERE resolution='resolved' AND target_id IN ({marks})",
            declaration_ids,
        ):
            caller = index.enclosing(ref_file, l0)
            if caller is None or caller[0] == sym_id or inside_target(caller):
                continue
            _add_reference(callers, caller, kind, _evidence_site(ref_file, kind, l0, c0, l1, c1, payload))

    callees: dict = {}
    for target_id, kind, l0, c0, l1, c1, payload in db.execute(
        "SELECT target_id,kind,l0,c0,l1,c1,payload FROM effective_references WHERE file=? AND resolution='resolved' "
        "AND target_id IS NOT NULL AND l0 BETWEEN ? AND ?", (file, start, end),
    ):
        callee = index.symbol_for_declaration(target_id)
        if callee is None or callee[0] == sym_id or inside_target(callee):
            continue
        _add_reference(callees, callee, kind, _evidence_site(file, kind, l0, c0, l1, c1, payload))
    return callers, callees


def _evidence_site(file, kind, l0, c0, l1, c1, payload):
    ref = _unpack(payload)
    return {**_site(file, kind, l0, c0, l1, c1),
            **{key: ref[key] for key in ("resolver", "provenance", "target_kind") if key in ref}}


def _is_test_path(path: str) -> bool:
    parts = path.replace("\\", "/").split("/")
    name = parts[-1].lower()
    return (
        any(part.lower() in {"test", "tests", "testing"} for part in parts[:-1])
        or name.startswith("test_")
        or name.endswith(("_test.py", "_test.go", "_test.rs", "test.java", "tests.java"))
        or ".test." in name
        or ".spec." in name
    )


def _second_hop(db, index, target, callers, callees, limit, peer_ids=()):
    excluded = {target[0], *peer_ids} | set(callers) | set(callees)
    found: dict = {}
    for direction, neighbours in (("caller", callers), ("callee", callees)):
        for neighbour in neighbours.values():
            row = neighbour[0]
            next_callers, next_callees = _direct_edges(db, index, row)
            for next_direction, group in (("caller", next_callers), ("callee", next_callees)):
                for item in group.values():
                    candidate = item[0]
                    if candidate[0] in excluded:
                        continue
                    entry = found.setdefault(candidate[0], {
                        "row": candidate, "references": 0, "via": [], "edge_kinds": {},
                    })
                    entry["references"] += item[1]
                    via = {"symbol_id": row[0], "from_target": direction, "direction": next_direction}
                    if via not in entry["via"]:
                        entry["via"].append(via)
                    for kind, edge in item[2].items():
                        entry["edge_kinds"][kind] = entry["edge_kinds"].get(kind, 0) + edge["count"]
    ranked = sorted(found.values(), key=lambda item: (-item["references"], item["row"][0]))
    listed = []
    for item in ranked[:limit]:
        entry = _symbol_fields(item["row"])
        entry.update(references=item["references"], via=item["via"], edge_kinds=item["edge_kinds"])
        listed.append(entry)
    return {"total": len(ranked), "listed": listed,
            "omitted_by_cap": max(0, len(ranked) - len(listed)), "omitted_by_budget": 0}


def _impact_of(db, index, cards, symbol, limit, history, hops=1, peer_ids=()):
    sym_id, file, _name, _kind, start, end = symbol[:6]
    callers, callees = _direct_edges(db, index, symbol)

    blind: dict = {}
    unbound = 0
    for (payload,) in db.execute(
        "SELECT payload FROM effective_references WHERE file=? AND resolution!='resolved' "
        "AND known_unrelated=0 AND l0 BETWEEN ? AND ?", (file, start, end),
    ):
        reference = _unpack(payload)
        reason = reference.get("reason") or "unresolved"
        if reason in _NOT_A_BLIND_SPOT:
            unbound += 1
            continue
        name = ".".join(reference.get("parts") or []) or reference.get("kind") or "reference"
        blind[(name, reason)] = blind.get((name, reason), 0) + 1
    blind_spots = [{"name": name, "reason": reason, "count": count}
                   for (name, reason), count in sorted(blind.items(), key=lambda item: (-item[1], item[0]))]

    recent = [{"changeset": seq, "created_at": created, "change_kind": kind}
              for seq, created, kind in db.execute(
                  "SELECT d.seq,c.created_at,d.change_kind FROM meta_changeset_deltas d "
                  "JOIN meta_changesets c ON c.seq=d.seq WHERE d.symbol_id=? ORDER BY d.seq DESC LIMIT ?",
                  (sym_id, history))]

    caller_packet = _neighbors(cards, callers, limit)
    callee_packet = _neighbors(cards, callees, limit)
    blind_packet = {"total": len(blind_spots), "listed": blind_spots[:limit], "unbound_names": unbound}
    related_tests = []
    for item in callers.values():
        row = item[0]
        if _is_test_path(row[1]):
            entry = _symbol_fields(row)
            entry["references"] = item[1]
            related_tests.append(entry)
    related_tests.sort(key=lambda item: (-item["references"], item["symbol_id"]))
    obligations = []
    if caller_packet["total"]:
        obligations.append({"kind": "inspect-callers", "count": caller_packet["total"]})
    if callee_packet["total"]:
        obligations.append({"kind": "inspect-callees", "count": callee_packet["total"]})
    if blind_packet["total"]:
        obligations.append({"kind": "resolve-blind-spots", "count": blind_packet["total"]})
    if related_tests:
        obligations.append({"kind": "run-related-tests", "count": len(related_tests)})
    omitted = (caller_packet["total"] - len(caller_packet["listed"])
               + callee_packet["total"] - len(callee_packet["listed"]))
    if omitted:
        obligations.append({"kind": "inspect-omitted-neighbours", "count": omitted})

    result = {
        **_symbol_fields(symbol),
        "card": cards.get(sym_id),
        "callers": caller_packet,
        "callees": callee_packet,
        "blind_spots": blind_packet,
        "l4": {
            "related_tests": related_tests[:limit],
            "related_tests_total": len(related_tests),
            "obligations": obligations,
            "do_not_touch": {
                "status": "unavailable",
                "reason": "requires a base/candidate fingerprint delta; use stale-callers",
                "symbols": [],
            },
        },
        "recent_changes": recent,
    }
    if hops == 2:
        result["second_hop"] = _second_hop(db, index, symbol, callers, callees, limit, peer_ids)
    return result


def _slice_names(node, *, definitions: bool) -> set[str]:
    names = set()
    stack = [node]
    while stack:
        current = stack.pop()
        if current is not node and isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            if definitions and isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                names.add(current.name)
            continue
        if isinstance(current, ast.Name):
            if definitions and isinstance(current.ctx, ast.Store):
                names.add(current.id)
            if not definitions and isinstance(current.ctx, ast.Load):
                names.add(current.id)
        elif definitions and isinstance(current, ast.Import):
            names.update(alias.asname or alias.name.split(".")[0] for alias in current.names)
        elif definitions and isinstance(current, ast.ImportFrom):
            names.update(alias.asname or alias.name for alias in current.names if alias.name != "*")
        elif definitions and isinstance(current, ast.ExceptHandler) and current.name:
            names.add(current.name)
        stack.extend(ast.iter_child_nodes(current))
    return names


def _slice_statements(function) -> list[ast.stmt]:
    statements = []

    def visit(items):
        for item in items:
            statements.append(item)
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            for child in ast.iter_child_nodes(item):
                if isinstance(child, ast.stmt):
                    visit([child])

    visit(function.body)
    return statements


def _python_slice(store, row) -> dict:
    """A lazy conservative backward slice of one Python callable.

    Seeds are observable statements. The closure follows definitions of names
    they use and adds the first line of each enclosing control statement. This
    is intraprocedural evidence, not a proof of runtime reachability.
    """
    _sym_id, file, name, kind, start, end, *_rest = row
    if kind not in {"function", "method"}:
        return {"status": "unavailable", "reason": "slice requires a function or method target"}
    entry = store.get_file(file, semantic=False)
    if entry is None or entry.get("language") != "python" or entry.get("status") != "parsed":
        return {"status": "unavailable", "reason": "slice requires a parsed Python target"}
    import source_reader

    try:
        read = source_reader.read_packet(store, [{"path": file, "ranges": [{"start": start, "end": end}]}])
    except ValueError as error:
        return {"status": "unavailable", "reason": str(error)}
    lines = {}
    for item in read["files"]:
        if item["path"] != file:
            continue
        for block in item["blocks"]:
            for raw in block["source"].splitlines():
                match = re.match(r"(\d+): (.*)\Z", raw)
                if match and start <= int(match.group(1)) <= end:
                    lines[int(match.group(1))] = match.group(2)
    if set(lines) != set(range(start, end + 1)):
        return {"status": "unavailable", "reason": "verified source did not cover the whole target span"}
    try:
        tree = ast.parse(textwrap.dedent("\n".join(lines[number] for number in range(start, end + 1))))
    except SyntaxError as error:
        return {"status": "unavailable", "reason": f"Python slice parse failed: {error.msg}"}
    short = name.split(".")[-1]
    function = next((node for node in ast.walk(tree)
                     if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == short), None)
    if function is None:
        return {"status": "unavailable", "reason": "target callable was not found in its verified span"}
    statements = _slice_statements(function)
    by_id = {id(item): item for item in statements}
    uses = {id(item): _slice_names(item, definitions=False) for item in statements}
    defines = {id(item): _slice_names(item, definitions=True) for item in statements}
    included: dict[int, str] = {}

    def include(item, reason):
        if id(item) not in included:
            included[id(item)] = reason
            return True
        return False

    for item in statements:
        if isinstance(item, (ast.Return, ast.Raise, ast.Expr, ast.Assert)):
            include(item, "observable-statement")
    changed = True
    while changed:
        changed = False
        needed = set().union(*(uses[key] for key in included)) if included else set()
        for item in statements:
            if id(item) not in included and defines[id(item)] & needed:
                changed = include(item, "defines-used-name") or changed
    statement_ids = {id(item) for item in statements}
    for item in statements:
        if id(item) in included:
            continue
        descendants = {id(node) for node in ast.walk(item) if isinstance(node, ast.stmt)} & statement_ids
        if descendants & set(included):
            include(item, "control-header")
    selected = []
    for key, reason in included.items():
        item = by_id[key]
        first = start + item.lineno - 1
        last = start + (item.end_lineno or item.lineno) - 1
        if reason == "control-header":
            last = first
        selected.append({"start": first, "end": last, "kind": type(item).__name__, "reason": reason})
    selected.sort(key=lambda item: (item["start"], item["end"], item["kind"]))
    ranges = []
    for item in selected:
        if ranges and item["start"] <= ranges[-1]["end"] + 1:
            ranges[-1]["end"] = max(ranges[-1]["end"], item["end"])
        else:
            ranges.append({"start": item["start"], "end": item["end"]})
    return {
        "status": "available",
        "language": "python",
        "method": "backward-def-use",
        "statements": selected,
        "ranges": ranges,
        "limitations": [
            "intraprocedural and conservative; dynamic dispatch and aliasing are not resolved",
            "control headers are represented by their first line",
        ],
    }


def _packet_bytes(packet: dict) -> int:
    return len(json.dumps(packet, separators=(",", ":")))


def build_edit_impact(store, targets, *, cards_path=None, neighbors=20, history=5,
                      include_source=True, hops=1, include_neighbor_source=False,
                      include_slices=False, budget_chars=DEFAULT_IMPACT_BUDGET_CHARS,
                      engine_store=None) -> dict:
    """What to know before editing a symbol, in one bounded packet.

    Read-only over the snapshot's Meta-Code index and the card store. Target
    fields and digests are the core. Callers and callees are L1, with signatures,
    cards and exact reference sites. A second hop is L2 and carries signatures
    and structural summaries only. L3 slices are computed only when requested.
    L4 lists related tests and obligations; its DO NOT TOUCH list stays
    unavailable until a base/candidate delta can classify a symbol GREEN.
    Verified target source is L0, and verified one-hop neighbour source is
    included only when requested. Budget omissions are reported, never hidden.
    This is evidence and leads; whether an edit is correct stays with the reader.
    """
    if store.format != "sqlite":
        raise ValueError("edit impact requires a SQLite snapshot")
    if (not isinstance(targets, list) or not targets
            or any(not isinstance(target, str) or not target for target in targets)):
        raise ValueError("targets must be a nonempty list of symbol ids or file paths")
    for name, value in (("neighbors", neighbors), ("history", history)):
        if type(value) is not int or not 1 <= value <= 200:
            raise ValueError(f"{name} must be an integer from 1 to 200")
    if type(hops) is not int or hops not in (1, 2):
        raise ValueError("hops must be 1 or 2")
    for name, value in (("include_source", include_source),
                        ("include_neighbor_source", include_neighbor_source),
                        ("include_slices", include_slices)):
        if type(value) is not bool:
            raise ValueError(f"{name} must be a boolean")
    if type(budget_chars) is not int or not 1_000 <= budget_chars <= MAX_IMPACT_BUDGET_CHARS:
        raise ValueError(f"budget_chars must be an integer from 1000 to {MAX_IMPACT_BUDGET_CHARS}")

    with semantic_reader(store) as db:
        if db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='meta_symbols'").fetchone() is None:
            raise ValueError("snapshot has no Meta-Code index; refresh the snapshot")
        index = _ImpactIndex(db)
        cards = _Cards(db, cards_path, store.metadata.get("root"))
        edge_summary = install_edge_view(db, store, engine_store=engine_store, limit=neighbors)
        resolved: list = []
        unknown: list = []
        for target in targets:
            row = db.execute(f"{_SYMBOL_SELECT} WHERE m.id=?", (target,)).fetchone()
            rows = [row] if row else db.execute(
                f"{_SYMBOL_SELECT} WHERE m.file=? ORDER BY m.start,m.end", (target,)
            ).fetchall()
            if rows:
                resolved.extend(rows)
            else:
                unknown.append(target)
        unique = list({row[0]: row for row in resolved}.values())
        selected = unique[:MAX_IMPACT_TARGETS]
        packet = {
            "schema": EDIT_IMPACT_SCHEMA,
            "edge_view": edge_summary,
            "freshness_basis": "lexical",
            "root": store.metadata.get("root"),
            "target": store.metadata.get("target"),
            "targets": [_impact_of(db, index, cards, row, neighbors, history, hops,
                                   {item[0] for item in selected}) for row in selected],
            "unknown_targets": unknown,
            "truncated_targets": max(0, len(unique) - len(selected)),
            "disclosure": {
                "L0": "source: verified target source, when requested",
                "L1": "targets[].callers and targets[].callees: signatures, cards and reference sites",
                "L2": "targets[].second_hop: signatures and structural summaries, when hops=2",
                "L3": "targets[].slice: lazy Python backward slice, when requested",
                "L4": "targets[].l4: related tests, obligations and DO NOT TOUCH status",
            },
        }

    if include_source and selected:
        import source_reader

        try:
            read = source_reader.read_packet(
                store, [{"path": row[1], "symbols": [row[2]]} for row in selected])
            packet["source"] = {
                "files": [{key: item.get(key) for key in ("path", "status", "notes", "blocks")}
                          for item in read["files"]],
                "metrics": read["metrics"],
            }
        except ValueError as error:
            # Stale or unreadable source is reported, never hidden: the rest of
            # the packet is metadata and stays usable.
            packet["source"] = {"error": str(error)}
    selected_rows = {row[0]: row for row in selected}
    neighbor_source_omitted: list[dict] = []
    if include_neighbor_source and selected:
        import source_reader

        requests: dict[str, list[str]] = {}
        priority: dict[str, int] = {}
        for target in packet["targets"]:
            for group in ("callers", "callees"):
                for item in target[group]["listed"]:
                    requests.setdefault(item["file"], []).append(item["name"])
                    priority[item["file"]] = priority.get(item["file"], 0) + item["references"]
        files = []
        metrics = {"source_bytes_read": 0, "source_lines_emitted": 0, "source_characters_emitted": 0}
        for file in sorted(requests, key=lambda item: (-priority[item], item)):
            names = sorted(set(requests[file]))
            try:
                read = source_reader.read_packet(store, [{"path": file, "symbols": names}])
            except ValueError as error:
                neighbor_source_omitted.append({"file": file, "symbols": names, "reason": str(error)})
                continue
            candidate_files = [{key: item.get(key) for key in ("path", "status", "notes", "blocks")}
                               for item in read["files"]]
            packet["neighbor_source"] = {"files": files + candidate_files,
                                         "metrics": metrics, "omitted": neighbor_source_omitted}
            if _packet_bytes(packet) > budget_chars:
                del packet["neighbor_source"]
                neighbor_source_omitted.append({"file": file, "symbols": names, "reason": "budget"})
                continue
            files.extend(candidate_files)
            for key in metrics:
                metrics[key] += read["metrics"][key]
        packet["neighbor_source"] = {"files": files, "metrics": metrics,
                                     "omitted": neighbor_source_omitted}

    if include_slices and selected:
        for target in packet["targets"]:
            target["slice"] = _python_slice(store, selected_rows[target["symbol_id"]])

    l2_omitted = 0
    while _packet_bytes(packet) > budget_chars:
        removable = [target for target in packet["targets"]
                     if target.get("second_hop", {}).get("listed")]
        if not removable:
            break
        target = removable[-1]
        target["second_hop"]["listed"].pop()
        target["second_hop"]["omitted_by_budget"] += 1
        l2_omitted += 1
    packet["budget"] = {
        "max_chars": budget_chars,
        "final_bytes": _packet_bytes(packet),
        "exceeded": _packet_bytes(packet) > budget_chars,
        "second_hop_omitted": l2_omitted,
        "neighbor_source_omitted": len(neighbor_source_omitted),
    }
    packet["bytes"] = _packet_bytes(packet)
    return packet


STALE_CALLERS_SCHEMA = "daodan/stale-callers/v1"
MAX_STALE_CALLERS = 1_000


def _meta_map(db):
    return {row[0]: row for row in db.execute(_SYMBOL_SELECT)}


def _call_bindings(db, index, table):
    """Match calls by enclosing symbol and ordinal, independently of shifted lines.

    Changed caller bodies have no reliable callsite identity across revisions;
    consumers retain both witnesses instead of interpreting absence as rewiring.
    """
    result, counts = {}, {}
    for file, line, target, payload in db.execute(
        f"SELECT file,l0,target_id,payload FROM {table} WHERE kind='call' ORDER BY file,l0,c0,id"
    ):
        caller = index.enclosing(file, line)
        callee = index.symbol_for_declaration(target) if target else None
        if caller is None:
            continue
        ref = _unpack(payload)
        parts = tuple(ref.get("parts") or [])
        key = (caller[0], parts)
        ordinal = counts.get(key, 0)
        counts[key] = ordinal + 1
        result[(*key, ordinal)] = {
            "caller": caller[0], "caller_body_hash": caller[6],
            "target": callee[0] if callee else None,
            "interface_hash": callee[7] if callee else None,
            "target_kind": ref.get("target_kind", "concrete"),
            "resolver": ref.get("resolver", "builtin-lexical"),
            "site": {"file": file, "span": ref.get("span")},
        }
    return result


def _binding_drift(before, after, new_symbols, *, engine=False):
    items = []
    for key in sorted(set(before) | set(after)):
        old, new = before.get(key), after.get(key)
        if engine and not any(r and r["resolver"] != "builtin-lexical" for r in (old, new)):
            continue
        kind = None
        if old and old["target"] and old["target"] not in new_symbols:
            kind = "removed_target"
        elif old and new and old["caller_body_hash"] == new["caller_body_hash"]:
            if old["target"] and new["target"] and old["target"] != new["target"]:
                kind = ("dispatch_set_changed" if {old["target_kind"], new["target_kind"]}
                        & {"protocol", "interface"} else "rewired_call")
            elif old["target"] and old["target"] == new["target"] and old["interface_hash"] != new["interface_hash"]:
                kind = "callee_interface_changed"
        if kind:
            items.append({"kind": kind, "caller": (new or old)["caller"],
                          "before_target": old["target"] if old else None,
                          "after_target": new["target"] if new else None,
                          "before": old, "after": new,
                          "certainty": "potential" if kind == "dispatch_set_changed" else "confirmed"})
    return items


def _engine_comparison(before, after):
    available = [v["profile"]["engine_available"] for v in (before, after)]
    if not any(available):
        return "unavailable", "neither snapshot has a verified engine pass"
    if not all(available):
        return "incomparable", "only one snapshot has a verified engine pass"
    if before["profile"]["engine"] != after["profile"]["engine"]:
        return "incomparable", "engine versions differ"
    sampled = [v["coverage"]["sampled"] for v in (before, after)]
    if any(sampled):
        keys = ("sampled", "population", "selected", "stride")
        if any(before["coverage"][k] != after["coverage"][k] for k in keys):
            return "incomparable", "sampled coverage differs"
        return "partial", "only positively resolved witnesses are comparable; absence is not evidence"
    return "complete", None


def build_stale_callers(base, candidate, *, limit=100,
                       base_engine_store=None, candidate_engine_store=None) -> dict:
    """Compare two snapshots and classify callers of changed symbols.

    Interface or effects changes put direct candidate callers in
    `edit_impact` (RED: inspect or edit). Body-only changes put transitive
    callers in `validation_impact` (GREEN for editing: rerun tests, do not
    rewrite). Edit propagation stops at a caller whose own interface and
    effects did not change; that caller's callers are GREEN and join
    `do_not_touch`. Callers retain resolved base and candidate references and
    containment, whether or not they have cards. This query is distinct from
    card freshness (`stale_callee`).
    """
    if type(limit) is not int or not 1 <= limit <= MAX_STALE_CALLERS:
        raise ValueError(f"limit must be an integer from 1 to {MAX_STALE_CALLERS}")
    for label, store in (("base", base), ("candidate", candidate)):
        if store.format != "sqlite":
            raise ValueError(f"stale-callers requires a SQLite {label} snapshot")

    with semantic_reader(base) as base_db, semantic_reader(candidate) as candidate_db:
        for db in (base_db, candidate_db):
            if db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='meta_symbols'").fetchone() is None:
                raise ValueError("snapshot has no Meta-Code index; refresh the snapshot")
        old = _meta_map(base_db)
        new = _meta_map(candidate_db)
        index = _ImpactIndex(candidate_db)
        base_index = _ImpactIndex(base_db)
        base_view = install_edge_view(base_db, base, engine_store=base_engine_store, limit=limit)
        candidate_view = install_edge_view(candidate_db, candidate, engine_store=candidate_engine_store, limit=limit)
        engine_status, engine_reason = _engine_comparison(base_view, candidate_view)
        comparable = engine_status in {"complete", "partial"}
        lexical_drift = _binding_drift(_call_bindings(base_db, base_index, "sem_references"),
                                      _call_bindings(candidate_db, index, "sem_references"), new)
        engine_drift = (_binding_drift(_call_bindings(base_db, base_index, "effective_references"),
                                       _call_bindings(candidate_db, index, "effective_references"), new,
                                       engine=True) if comparable else [])

        changed = []
        incompatible = []
        for symbol_id in sorted(set(old) | set(new)):
            before, after = old.get(symbol_id), new.get(symbol_id)
            if before is None:
                kind = "added"
            elif after is None:
                kind = "removed"
            elif digest_version(before[7]) != digest_version(after[7]):
                kind = "digest_version_mismatch"
            elif before[7] != after[7]:
                kind = "interface_changed"
            elif before[8] != after[8]:
                kind = "effects_changed"
            elif before[6] != after[6]:
                kind = "body_only"
            else:
                continue
            row = after or before
            entry = {
                **_symbol_fields(row),
                "change_kind": kind,
                "old": {"body_hash": before[6], "interface_hash": before[7], "effects_hash": before[8]} if before else None,
                "new": {"body_hash": after[6], "interface_hash": after[7], "effects_hash": after[8]} if after else None,
            }
            (incompatible if kind == "digest_version_mismatch" else changed).append(entry)
        changed_by_id = {item["symbol_id"]: item for item in changed}

        # Keep base witnesses as well: removed bindings still impose inspection.
        reverse: dict[str, dict[str, dict]] = {}
        forward: dict[str, set[str]] = {}

        def add_edge(caller, callee, kind, site):
            if caller is None or callee is None or caller[0] == callee[0]:
                if caller is not None and callee is not None and caller[0] == callee[0]:
                    forward.setdefault(caller[0], set()).add(callee[0])
                return
            item = reverse.setdefault(callee[0], {}).setdefault(
                caller[0], {"row": caller, "edges": {}})
            edge = item["edges"].setdefault(kind, {"kind": kind, "count": 0, "sites": []})
            edge["count"] += 1
            if site is not None and site not in edge["sites"]:
                edge["sites"].append(site)
            forward.setdefault(caller[0], set()).add(callee[0])

        # A positive witness remains an inspection obligation even when the
        # two engine profiles cannot support a claim of changed resolution.
        table = "effective_references"
        witnessed = set()
        for db, lookup, revision in ((candidate_db, index, "candidate"), (base_db, base_index, "base")):
            for file, kind, l0, c0, l1, c1, target_id, payload in db.execute(
                f"SELECT file,kind,l0,c0,l1,c1,target_id,payload FROM {table} "
                "WHERE resolution='resolved' AND target_id IS NOT NULL"
            ):
                callee = lookup.symbol_for_declaration(target_id)
                caller = lookup.enclosing(file, l0)
                if caller is None or callee is None or caller[0] not in new:
                    continue
                witness = (caller[0], callee[0], kind, l0, c0, l1, c1)
                if witness in witnessed:
                    continue
                witnessed.add(witness)
                edge_kind = {"call": "CALLS", "read": "READS"}.get(kind, str(kind).upper())
                add_edge(new[caller[0]], new.get(callee[0], callee), edge_kind,
                         {**_evidence_site(file, kind, l0, c0, l1, c1, payload), "snapshot": revision})
        for row in new.values():
            name = row[2]
            if "." not in name:
                continue
            parent = next((item for item in index.symbols(row[1]) if item[2] == name.rsplit(".", 1)[0]), None)
            if parent is not None:
                add_edge(parent, row, "CONTAINS", None)

        def contract_changed(symbol_id):
            item = changed_by_id.get(symbol_id)
            return item is not None and item["change_kind"] in {"interface_changed", "effects_changed", "added"}

        edit: dict[str, dict] = {}
        validation: dict[str, dict] = {}
        green: dict[str, dict] = {}

        def record(store_map, row, status, channel, depth, reason):
            entry = store_map.get(row[0])
            if entry is None:
                entry = {**_symbol_fields(row), "status": status, "channel": channel,
                         "depth": depth, "reasons": []}
                store_map[row[0]] = entry
            entry["depth"] = min(entry["depth"], depth)
            if reason not in entry["reasons"]:
                entry["reasons"].append(reason)

        from collections import deque

        edit_queue = deque()
        for item in changed:
            if item["change_kind"] in {"interface_changed", "effects_changed", "added", "removed"}:
                edit_queue.append((item["symbol_id"], 0))
        seen_edit_sources = set()
        while edit_queue:
            source_id, depth = edit_queue.popleft()
            if source_id in seen_edit_sources:
                continue
            seen_edit_sources.add(source_id)
            for caller_id, item in sorted(reverse.get(source_id, {}).items()):
                row = item["row"]
                removed_source = changed_by_id[source_id]["change_kind"] == "removed"
                if caller_id in changed_by_id and contract_changed(caller_id) and not removed_source:
                    if caller_id != source_id:
                        edit_queue.append((caller_id, depth + 1))
                    continue
                if caller_id in changed_by_id and not removed_source:
                    continue
                record(edit, row, "RED", "edit_impact", depth + 1, {
                    "changed_symbol": source_id,
                    "change_kind": changed_by_id[source_id]["change_kind"],
                    "edges": [item["edges"][kind] for kind in sorted(item["edges"])],
                })
                if contract_changed(caller_id):
                    edit_queue.append((caller_id, depth + 1))
                else:
                    for upper_id, upper in sorted(reverse.get(caller_id, {}).items()):
                        if upper_id in changed_by_id or upper_id in edit:
                            continue
                        record(green, upper["row"], "GREEN", "do_not_touch", depth + 2, {
                            "changed_symbol": source_id,
                            "stopped_at": caller_id,
                            "reason": "intermediate contract unchanged",
                        })

        validation_queue = deque(
            (item["symbol_id"], 0) for item in changed if item["change_kind"] == "body_only")
        seen_validation = set()
        while validation_queue:
            source_id, depth = validation_queue.popleft()
            if source_id in seen_validation:
                continue
            seen_validation.add(source_id)
            for caller_id, item in sorted(reverse.get(source_id, {}).items()):
                if caller_id in changed_by_id:
                    if changed_by_id[caller_id]["change_kind"] == "body_only":
                        validation_queue.append((caller_id, depth + 1))
                    continue
                if caller_id in edit:
                    continue
                record(validation, item["row"], "GREEN", "validation_impact", depth + 1, {
                    "changed_symbol": source_id,
                    "change_kind": "body_only",
                    "edges": [item["edges"][kind] for kind in sorted(item["edges"])],
                })
                validation_queue.append((caller_id, depth + 1))
        for symbol_id in list(green):
            if symbol_id in edit or symbol_id in validation or symbol_id in changed_by_id:
                del green[symbol_id]

        def bounded(store_map):
            ranked = sorted(store_map.values(), key=lambda item: (item["depth"], item["symbol_id"]))
            return {"total": len(ranked), "listed": ranked[:limit],
                    "truncated": max(0, len(ranked) - limit)}

        def drift_packet(items, status, reason=None):
            return {"status": status, "reason": reason, "items": items[:limit],
                    "total": len(items), "truncated": max(0, len(items) - limit)}

        edit_packet = bounded(edit)
        validation_packet = bounded(validation)
        do_not_touch = dict(validation)
        do_not_touch.update({key: value for key, value in green.items() if key not in do_not_touch})
        green_packet = bounded(do_not_touch)

        nodes = ({item["symbol_id"] for item in changed if new.get(item["symbol_id"]) is not None}
                 | set(edit) | set(validation) | set(green))
        components = _scc_components(nodes, forward)
        component_of = {}
        for position, component in enumerate(components):
            for symbol_id in component["symbols"]:
                component_of[symbol_id] = position
        order = _component_order(components, forward, component_of)

        return {
            "schema": STALE_CALLERS_SCHEMA,
            "freshness_basis": "lexical",
            "lexical_callee_drift": drift_packet(lexical_drift, "complete"),
            "engine_callee_drift": drift_packet(engine_drift, engine_status, engine_reason),
            "edge_views": {"base": base_view, "candidate": candidate_view},
            "base": snapshot._snapshot_info(base),
            "candidate": snapshot._snapshot_info(candidate),
            "changed": changed,
            "edit_impact": edit_packet,
            "validation_impact": validation_packet,
            "do_not_touch": green_packet,
            "components": [components[position] for position in order],
            "incompatible": incompatible,
            "unavailable_edge_kinds": ["OVERRIDES", "INHERITS", "IMPORTS"],
            "summary": {
                "changed": len(changed),
                "edit_impact": len(edit),
                "validation_impact": len(validation),
                "do_not_touch": len(do_not_touch),
                "incompatible": len(incompatible),
                "components": len(components),
            },
        }


def _scc_components(nodes, forward):
    """Tarjan SCCs over the candidate graph induced by the impacted nodes."""
    index_counter = [0]
    indices: dict[str, int] = {}
    lowlink: dict[str, int] = {}
    stack: list[str] = []
    on_stack: set[str] = set()
    components = []

    def neighbors(node):
        return sorted(item for item in forward.get(node, ()) if item in nodes)

    for root in sorted(nodes):
        if root in indices:
            continue
        work = [(root, 0)]
        while work:
            node, child_pos = work[-1]
            if child_pos == 0:
                indices[node] = lowlink[node] = index_counter[0]
                index_counter[0] += 1
                stack.append(node)
                on_stack.add(node)
            recurse = False
            children = neighbors(node)
            for position in range(child_pos, len(children)):
                child = children[position]
                if child not in indices:
                    work[-1] = (node, position + 1)
                    work.append((child, 0))
                    recurse = True
                    break
                if child in on_stack:
                    lowlink[node] = min(lowlink[node], indices[child])
            if recurse:
                continue
            if lowlink[node] == indices[node]:
                component = []
                while True:
                    item = stack.pop()
                    on_stack.remove(item)
                    component.append(item)
                    if item == node:
                        break
                component.sort()
                components.append({
                    "symbols": component,
                    "cyclic": len(component) > 1 or component[0] in forward.get(component[0], ()),
                    "atomic": True,
                })
            work.pop()
            if work:
                parent = work[-1][0]
                lowlink[parent] = min(lowlink[parent], lowlink[node])
    components.sort(key=lambda item: item["symbols"])
    return components


def _component_order(components, forward, component_of):
    """Component positions in callees-before-callers order."""
    precedence: dict[int, set[int]] = {position: set() for position in range(len(components))}
    indegree: dict[int, int] = {position: 0 for position in range(len(components))}
    for caller, callees in forward.items():
        if caller not in component_of:
            continue
        for callee in callees:
            if callee not in component_of:
                continue
            before, after = component_of[callee], component_of[caller]
            if before != after and after not in precedence[before]:
                precedence[before].add(after)
                indegree[after] += 1
    ready = sorted((position for position, degree in indegree.items() if degree == 0),
                   key=lambda position: components[position]["symbols"])
    order = []
    while ready:
        position = ready.pop(0)
        order.append(position)
        for nxt in sorted(precedence[position], key=lambda item: components[item]["symbols"]):
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                ready.append(nxt)
        ready.sort(key=lambda item: components[item]["symbols"])
    return order
