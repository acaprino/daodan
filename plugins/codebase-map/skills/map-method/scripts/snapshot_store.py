"""Versioned snapshot storage; binary readers do not materialize the inventory."""
from __future__ import annotations

from collections.abc import Mapping
import hashlib
import itertools
import json
from pathlib import Path
import sqlite3
from typing import Iterable, Iterator
import zlib

from json_snapshot import JsonSnapshot, MAX_RECORD_BYTES, DECODER

APPLICATION_ID = 0x444D4150
STORAGE_VERSION = 1
FORMATS = frozenset({"sqlite", "json"})
FACT_KINDS = ("scopes", "declarations", "imports", "exports", "references")
INDEX_KINDS = frozenset({"coverage", "module_targets", "resolved_references", "graph_metrics"})
SQLITE_HEADER = b"SQLite format 3\x00"


def validate_format(format: str) -> str:
    if not isinstance(format, str) or format not in FORMATS:
        raise ValueError("snapshot format must be sqlite or json")
    return format


def _encoded(value) -> bytes:
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _pack(value) -> bytes:
    data = _encoded(value)
    if len(data) > MAX_RECORD_BYTES:
        raise ValueError("snapshot record exceeds storage limit")
    compressed = zlib.compress(data, 3)
    return b"z" + compressed if len(compressed) < len(data) else b"j" + data


def _unpack(data):
    if not isinstance(data, bytes) or not data:
        raise ValueError("invalid snapshot record codec")
    if data[:1] == b"z":
        inflater = zlib.decompressobj()
        try:
            payload = inflater.decompress(data[1:], MAX_RECORD_BYTES + 1)
        except zlib.error as error:
            raise ValueError("invalid compressed snapshot record") from error
        if len(payload) > MAX_RECORD_BYTES or not inflater.eof or inflater.unused_data:
            raise ValueError("invalid or oversized compressed snapshot record")
    elif data[:1] == b"j":
        payload = data[1:]
    else:
        raise ValueError("unsupported snapshot record codec")
    if len(payload) > MAX_RECORD_BYTES:
        raise ValueError("snapshot record exceeds storage limit")
    try:
        return DECODER.decode(payload.decode("utf-8"))
    except (ValueError, RecursionError) as error:
        raise ValueError("invalid snapshot record JSON") from error


def _settings(connection, *, readonly=False):
    connection.execute("PRAGMA trusted_schema=OFF")
    connection.execute("PRAGMA cache_size=-8192")
    connection.execute("PRAGMA mmap_size=0")
    connection.execute("PRAGMA temp_store=FILE")
    if hasattr(connection, "setlimit"):
        connection.setlimit(sqlite3.SQLITE_LIMIT_LENGTH, MAX_RECORD_BYTES + 1)
    if readonly:
        connection.execute("PRAGMA query_only=ON")


def _pack_bytes(data: bytes) -> bytes:
    if len(data) > MAX_RECORD_BYTES:
        raise ValueError("snapshot record exceeds storage limit")
    compressed = zlib.compress(data, 3)
    return b"z" + compressed if len(compressed) < len(data) else b"j" + data


def _unpack_bytes(data: bytes) -> bytes:
    if not isinstance(data, bytes) or not data:
        raise ValueError("invalid snapshot record codec")
    if data[:1] == b"z":
        inflater = zlib.decompressobj()
        try:
            payload = inflater.decompress(data[1:], MAX_RECORD_BYTES + 1)
        except zlib.error as error:
            raise ValueError("invalid compressed snapshot record") from error
        if len(payload) > MAX_RECORD_BYTES or not inflater.eof or inflater.unused_data:
            raise ValueError("invalid or oversized compressed snapshot record")
        return payload
    if data[:1] == b"j":
        payload = data[1:]
        if len(payload) > MAX_RECORD_BYTES:
            raise ValueError("snapshot record exceeds storage limit")
        return payload
    raise ValueError("unsupported snapshot record codec")


_TAMPER_TRIGGERS = (
    "trg_files_tamper_i",
    "trg_files_tamper_u",
    "trg_files_tamper_d",
    "trg_symbols_tamper_i",
    "trg_symbols_tamper_u",
    "trg_symbols_tamper_d",
    "trg_facts_tamper_i",
    "trg_facts_tamper_u",
    "trg_facts_tamper_d",
)


def _header_sig(header_blob: bytes, semantic_header_blob: bytes | None) -> bytes:
    digest = hashlib.sha256()
    digest.update(b"H:")
    digest.update(header_blob)
    if semantic_header_blob is not None:
        digest.update(b"S:")
        digest.update(semantic_header_blob)
    return digest.digest()


def _plain(path: Path):
    import stat
    for item in (path, *path.parents):
        try:
            value = item.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(value.st_mode) or getattr(value, "st_file_attributes", 0) & 0x400:
            raise ValueError("linked snapshot path is forbidden")


class SnapshotStore:
    def __init__(self, path, format, *, connection=None, json_reader=None, metadata=None, borrowed=False):
        self.path = Path(path)
        self.format = format
        self.connection = connection
        self._json = json_reader
        self.metadata = metadata if metadata is not None else json_reader.metadata
        self.closed = False
        self._borrowed = borrowed

    def _open(self):
        if self.closed:
            raise ValueError("snapshot is closed")

    def get(self, key, default=None):
        self._open()
        if key == "files":
            raise ValueError("use explicit snapshot file access")
        return self.metadata.get(key, default)

    def __getitem__(self, key):
        self._open()
        return self.metadata[key]

    def iter_paths(self):
        self._open()
        if self._json:
            yield from sorted(self._json.offsets)
        else:
            for (path,) in self.connection.execute("SELECT path FROM files ORDER BY path"):
                yield path

    def has_file(self, path):
        self._open()
        if self._json:
            return path in self._json.offsets
        return self.connection.execute("SELECT 1 FROM files WHERE path=?", (path,)).fetchone() is not None

    @property
    def file_count(self):
        self._open()
        return len(self._json.offsets) if self._json else self.connection.execute("SELECT count(*) FROM files").fetchone()[0]

    def get_file(self, path: str, *, semantic: bool = True) -> dict | None:
        self._open()
        if self._json:
            return self._json.get_file(path, semantic=semantic)
        row = self.connection.execute("SELECT header,semantic_header FROM files WHERE path=?", (path,)).fetchone()
        if row is None:
            return None
        value = _unpack(row[0])
        if not isinstance(value, dict):
            raise ValueError("invalid snapshot file header")
        value["symbols"] = {name: _unpack(payload) for name, payload in self.connection.execute(
            "SELECT name,payload FROM symbols WHERE file=? ORDER BY ordinal", (path,))}
        if semantic and row[1] is not None:
            stored = _unpack(row[1])
            if (not isinstance(stored, dict) or not isinstance(stored.get("header"), dict)
                    or not isinstance(stored.get("lists"), list)
                    or any(not isinstance(kind, str) or kind not in FACT_KINDS for kind in stored["lists"])
                    or len(set(stored["lists"])) != len(stored["lists"])):
                raise ValueError("invalid snapshot semantic header")
            payload = stored["header"]
            for kind in stored["lists"]:
                payload[kind] = list(self.iter_records(kind, path=path))
            value["semantic"] = payload
        if not semantic:
            value.pop("semantic", None)
        return value

    def iter_files(self, *, semantic: bool = True) -> Iterator[tuple[str, dict]]:
        self._open()
        if self._json:
            yield from self._json.iter_files(semantic=semantic)
            return
        for (path,) in self.connection.execute("SELECT path FROM files ORDER BY path"):
            yield path, self.get_file(path, semantic=semantic)

    def get_file_header(self, path: str) -> dict | None:
        self._open()
        if self._json:
            return self._json.get_file(path, semantic=False)
        row = self.connection.execute("SELECT header FROM files WHERE path=?", (path,)).fetchone()
        if row is None:
            return None
        value = _unpack(row[0])
        if not isinstance(value, dict):
            raise ValueError("invalid snapshot file header")
        return value

    def iter_file_headers_only(self) -> Iterator[tuple[str, dict]]:
        self._open()
        if self._json:
            yield from self._json.iter_files(semantic=False)
            return
        for path, raw_header in self.connection.execute("SELECT path, header FROM files ORDER BY path"):
            value = _unpack(raw_header)
            if not isinstance(value, dict):
                raise ValueError("invalid snapshot file header")
            yield path, value

    def _has_json_cache(self) -> bool:
        self._open()
        if self._json or self.connection is None:
            return False
        has_table = (
            self.connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='file_json_cache'"
            ).fetchone()
            is not None
        )
        if not has_table:
            return False
        trig_count = self.connection.execute(
            "SELECT count(*) FROM sqlite_master WHERE type='trigger' AND name LIKE 'trg_%_tamper_%'"
        ).fetchone()[0]
        return trig_count == len(_TAMPER_TRIGGERS)

    def verified_reusable_headers(self) -> dict[str, dict] | None:
        """Return headers for SQLite rows whose trigger-guarded file_json_cache is intact."""
        self._open()
        if not self._has_json_cache():
            return None
        conn = self.connection
        verified = {}
        for path, header_blob, sem_blob, expected_sig in conn.execute(
            """
            SELECT f.path, f.header, f.semantic_header, c.row_sig
            FROM files f
            LEFT JOIN file_json_cache c ON c.path = f.path
            ORDER BY f.path
            """
        ):
            if expected_sig is None or _header_sig(header_blob, sem_blob) != expected_sig:
                return None
            header = _unpack(header_blob)
            if not isinstance(header, dict):
                return None
            verified[path] = header
        return verified

    def iter_symbols(self, *, path: str | None = None, pattern: str | None = None) -> Iterator[dict]:
        self._open()
        folded = pattern.casefold() if pattern else None
        if self._json:
            for rel, entry in self.iter_files(semantic=False):
                if path is not None and path != rel:
                    continue
                for name, payload in entry.get("symbols", {}).items():
                    if folded is None or folded in rel.casefold() or folded in name.casefold():
                        yield {"path": rel, "name": name, **payload}
            return
        sql = "SELECT file,name,payload FROM symbols"
        parameters = ()
        if path is not None:
            sql += " WHERE file=?"
            parameters = (path,)
        for rel, name, payload in self.connection.execute(sql + " ORDER BY file,name", parameters):
            if folded is None or folded in rel.casefold() or folded in name.casefold():
                yield {"path": rel, "name": name, **_unpack(payload)}

    def iter_records(self, kind: str, *, path: str):
        self._open()
        if kind not in FACT_KINDS:
            raise ValueError("unknown semantic record kind")
        if self._json:
            entry = self.get_file(path)
            yield from (entry or {}).get("semantic", {}).get(kind, [])
            return
        for (payload,) in self.connection.execute(
                "SELECT payload FROM facts WHERE file=? AND kind=? ORDER BY ordinal", (path, kind)):
            yield _unpack(payload)

    def close(self):
        if not self.closed:
            if self._json:
                self._json.close()
            if self.connection is not None and not self._borrowed:
                self.connection.close()
            self.closed = True

    def __enter__(self):
        self._open()
        return self

    def __exit__(self, *args):
        self.close()


class SnapshotWriter:
    """Write a single staging generation; the caller owns its publication."""

    def __init__(self, path: Path, format: str = "sqlite"):
        self.path = Path(path)
        self.format = validate_format(format)
        _plain(self.path)
        self.closed = False
        self._json_started = False
        self._metadata = {}
        self.connection = None
        self._handle = None
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists():
            raise ValueError("snapshot staging already exists")
        if format == "json":
            self._handle = self.path.open("xb")
            self._handle.write(b'{"files":{')
        else:
            self.connection = sqlite3.connect(self.path)
            _settings(self.connection)
            self.connection.executescript("""
                PRAGMA journal_mode=DELETE;
                PRAGMA application_id=1145913680;
                PRAGMA user_version=1;
                CREATE TABLE metadata(key TEXT PRIMARY KEY,value BLOB NOT NULL);
                CREATE TABLE files(path TEXT PRIMARY KEY,header BLOB NOT NULL,semantic_header BLOB);
                CREATE TABLE symbols(file TEXT NOT NULL,name TEXT NOT NULL,ordinal INTEGER NOT NULL,payload BLOB NOT NULL,
                    PRIMARY KEY(file,name));
                CREATE INDEX symbols_file_order ON symbols(file,ordinal);
                CREATE TABLE facts(file TEXT NOT NULL,kind TEXT NOT NULL,ordinal INTEGER NOT NULL,payload BLOB NOT NULL,
                    PRIMARY KEY(file,kind,ordinal));
                CREATE TABLE index_records(kind TEXT NOT NULL,ordinal INTEGER NOT NULL,payload BLOB NOT NULL,
                    PRIMARY KEY(kind,ordinal));
                CREATE TABLE file_json_cache(
                    path TEXT PRIMARY KEY,
                    row_sig BLOB NOT NULL,
                    is_ascii INTEGER NOT NULL,
                    payload_utf8 BLOB NOT NULL,
                    payload_ascii BLOB
                );
                CREATE TRIGGER trg_files_tamper_i AFTER INSERT ON files BEGIN
                    DELETE FROM file_json_cache WHERE path = NEW.path;
                END;
                CREATE TRIGGER trg_files_tamper_u AFTER UPDATE ON files BEGIN
                    DELETE FROM file_json_cache WHERE path = OLD.path OR path = NEW.path;
                END;
                CREATE TRIGGER trg_files_tamper_d AFTER DELETE ON files BEGIN
                    DELETE FROM file_json_cache WHERE path = OLD.path;
                END;
                CREATE TRIGGER trg_symbols_tamper_i AFTER INSERT ON symbols BEGIN
                    DELETE FROM file_json_cache WHERE path = NEW.file;
                END;
                CREATE TRIGGER trg_symbols_tamper_u AFTER UPDATE ON symbols BEGIN
                    DELETE FROM file_json_cache WHERE path = OLD.file OR path = NEW.file;
                END;
                CREATE TRIGGER trg_symbols_tamper_d AFTER DELETE ON symbols BEGIN
                    DELETE FROM file_json_cache WHERE path = OLD.file;
                END;
                CREATE TRIGGER trg_facts_tamper_i AFTER INSERT ON facts BEGIN
                    DELETE FROM file_json_cache WHERE path = NEW.file;
                END;
                CREATE TRIGGER trg_facts_tamper_u AFTER UPDATE ON facts BEGIN
                    DELETE FROM file_json_cache WHERE path = OLD.file OR path = NEW.file;
                END;
                CREATE TRIGGER trg_facts_tamper_d AFTER DELETE ON facts BEGIN
                    DELETE FROM file_json_cache WHERE path = OLD.file;
                END;
            """)

    def _open(self):
        if self.closed:
            raise ValueError("snapshot writer is closed")

    def put_file(self, path: str, entry: dict) -> None:
        self._open()
        from snapshot import validate_reuse_manifest
        validate_reuse_manifest({"schema": 1, "root": ".", "target": ".", "files": {path: entry}})
        if not isinstance(path, str) or not path or path.startswith(("/", "\\")) or ".." in Path(path).parts:
            raise ValueError("invalid snapshot inventory path")
        if self.format == "json":
            if self._json_started:
                self._handle.write(b",")
            self._handle.write(_encoded(path) + b":" + _encoded(entry))
            self._json_started = True
            return
        header = {key: value for key, value in entry.items() if key != "symbols"}
        semantic = header.get("semantic")
        semantic_header = None
        if isinstance(semantic, dict):
            header.pop("semantic")
            stored = [kind for kind in FACT_KINDS if isinstance(semantic.get(kind), list)]
            semantic_header = _pack({"header": {key: value for key, value in semantic.items() if key not in stored},
                                     "lists": stored})
        header_blob = _pack(header)
        sym_rows = [
            (name, number, _pack(payload))
            for number, (name, payload) in enumerate(entry["symbols"].items())
        ]
        fact_rows = []
        if semantic_header is not None:
            for kind in sorted(stored):
                for number, payload in enumerate(semantic[kind]):
                    fact_rows.append((kind, number, _pack(payload)))
        self.connection.execute("INSERT INTO files VALUES(?,?,?)", (path, header_blob, semantic_header))
        self.connection.executemany(
            "INSERT INTO symbols VALUES(?,?,?,?)",
            ((path, name, number, payload) for name, number, payload in sym_rows),
        )
        if fact_rows:
            self.connection.executemany(
                "INSERT INTO facts VALUES(?,?,?,?)",
                ((path, kind, number, payload) for kind, number, payload in fact_rows),
            )
        row_sig = _header_sig(header_blob, semantic_header)
        utf8_bytes = json.dumps(
            entry, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False
        ).encode("utf-8")
        is_ascii = 1 if utf8_bytes.isascii() else 0
        ascii_blob = (
            None
            if is_ascii
            else _pack_bytes(
                json.dumps(
                    entry, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False
                ).encode("utf-8")
            )
        )
        self.connection.execute(
            "INSERT OR REPLACE INTO file_json_cache VALUES(?,?,?,?,?)",
            (path, row_sig, is_ascii, _pack_bytes(utf8_bytes), ascii_blob),
        )

    def copy_file(self, previous: SnapshotStore, path: str) -> None:
        self.put_file(path, previous.get_file(path))

    def bulk_copy_from_sqlite(
        self,
        previous: SnapshotStore,
        exact_paths: Iterable[str],
        touched_headers: dict[str, dict] | None = None,
    ) -> None:
        self._open()
        if self.format != "sqlite" or previous.format != "sqlite":
            raise ValueError("bulk SQLite copy requires sqlite format")
        exact_list = sorted(set(exact_paths))
        touched = dict(touched_headers or {})
        if not exact_list and not touched:
            return
        conn = self.connection
        conn.commit()
        attached = False
        try:
            conn.execute("ATTACH DATABASE ? AS prev_snap", (str(previous.path.resolve()),))
            attached = True
            conn.execute("CREATE TEMP TABLE _reused_paths(path TEXT PRIMARY KEY, exact INTEGER NOT NULL)")
            if exact_list:
                conn.executemany("INSERT INTO _reused_paths VALUES(?,1)", ((p,) for p in exact_list))
            if touched:
                conn.executemany("INSERT INTO _reused_paths VALUES(?,0)", ((p,) for p in sorted(touched)))
            conn.execute("""
                INSERT INTO main.files(path, header, semantic_header)
                SELECT f.path, f.header, f.semantic_header
                FROM prev_snap.files f
                JOIN _reused_paths r ON f.path = r.path
                WHERE r.exact = 1
            """)
            if touched:
                for rel, new_header in sorted(touched.items()):
                    row = conn.execute(
                        "SELECT semantic_header FROM prev_snap.files WHERE path=?", (rel,)
                    ).fetchone()
                    sem_blob = row[0] if row is not None else None
                    conn.execute(
                        "INSERT INTO main.files(path, header, semantic_header) VALUES(?,?,?)",
                        (rel, _pack(new_header), sem_blob),
                    )
            conn.execute("""
                INSERT INTO main.symbols(file, name, ordinal, payload)
                SELECT s.file, s.name, s.ordinal, s.payload
                FROM prev_snap.symbols s
                JOIN _reused_paths r ON s.file = r.path
            """)
            conn.execute("""
                INSERT INTO main.facts(file, kind, ordinal, payload)
                SELECT fa.file, fa.kind, fa.ordinal, fa.payload
                FROM prev_snap.facts fa
                JOIN _reused_paths r ON fa.file = r.path
            """)
            conn.execute("""
                INSERT INTO main.file_json_cache(path, row_sig, is_ascii, payload_utf8, payload_ascii)
                SELECT c.path, c.row_sig, c.is_ascii, c.payload_utf8, c.payload_ascii
                FROM prev_snap.file_json_cache c
                JOIN _reused_paths r ON c.path = r.path
                WHERE r.exact = 1
            """)
            if touched:
                reader = self.reader()
                for rel in sorted(touched):
                    entry = reader.get_file(rel)
                    h_row = conn.execute(
                        "SELECT header, semantic_header FROM main.files WHERE path=?", (rel,)
                    ).fetchone()
                    row_sig = _header_sig(h_row[0], h_row[1])
                    utf8_bytes = json.dumps(
                        entry, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False
                    ).encode("utf-8")
                    is_ascii = 1 if utf8_bytes.isascii() else 0
                    ascii_blob = (
                        None
                        if is_ascii
                        else _pack_bytes(
                            json.dumps(
                                entry, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False
                            ).encode("utf-8")
                        )
                    )
                    conn.execute(
                        "INSERT OR REPLACE INTO main.file_json_cache VALUES(?,?,?,?,?)",
                        (rel, row_sig, is_ascii, _pack_bytes(utf8_bytes), ascii_blob),
                    )
            conn.execute("DROP TABLE _reused_paths")
            conn.commit()
        finally:
            if attached:
                try:
                    conn.commit()
                except sqlite3.Error:
                    pass
                conn.execute("DETACH DATABASE prev_snap")

    def put_index_records(self, kind: str, records: Iterable[dict]) -> None:
        self._open()
        if self.format != "sqlite" or kind not in INDEX_KINDS:
            raise ValueError("unsupported index record kind or format")
        self.connection.execute("DELETE FROM index_records WHERE kind=?", (kind,))
        self.connection.executemany("INSERT INTO index_records VALUES(?,?,?)",
            ((kind, number, _pack(value)) for number, value in enumerate(records)))

    def reader(self) -> SnapshotStore:
        self._open()
        if self.connection is None:
            raise ValueError("JSON staging cannot be read before completion")
        return SnapshotStore(self.path, "sqlite", connection=self.connection,
                             metadata=self._metadata, borrowed=True)

    def finish(self, metadata: dict) -> None:
        self._open()
        self._metadata.update(metadata)
        if metadata.get("schema") != 1 or not isinstance(metadata.get("root"), str) or not isinstance(metadata.get("target"), str):
            raise ValueError("invalid snapshot header metadata")
        if self.format == "json":
            self._handle.write(b"}")
            for key in sorted(metadata):
                self._handle.write(b"," + _encoded(key) + b":" + _encoded(metadata[key]))
            self._handle.write(b"}\n")
            self._handle.flush()
        else:
            self.connection.executemany("INSERT INTO metadata VALUES(?,?)",
                                        ((key, _pack(value)) for key, value in metadata.items()))
            self.connection.commit()
            if self.connection.execute("PRAGMA quick_check").fetchone()[0] != "ok":
                raise ValueError("snapshot integrity validation failed")
        self.close()

    def close(self):
        if not self.closed:
            if self._handle:
                self._handle.close()
            if self.connection:
                self.connection.close()
            self.closed = True

    def __enter__(self):
        self._open()
        return self

    def __exit__(self, *args):
        self.close()


def open_snapshot(path: Path, *, expected_format: str | None = None) -> SnapshotStore:
    path = Path(path)
    _plain(path)
    if expected_format is not None:
        validate_format(expected_format)
    with path.open("rb") as handle:
        header = handle.read(16)
    format = "sqlite" if header == SQLITE_HEADER else "json"
    if expected_format is not None and format != expected_format:
        raise ValueError("snapshot format does not match required format")
    if format == "json":
        try:
            return SnapshotStore(path, format, json_reader=JsonSnapshot(path))
        except (OSError, ValueError, RecursionError) as error:
            raise ValueError(f"invalid JSON snapshot: {error}") from error
    connection = None
    try:
        connection = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
        _settings(connection, readonly=True)
        if connection.execute("PRAGMA application_id").fetchone()[0] != APPLICATION_ID:
            raise ValueError("unrecognized snapshot application")
        if connection.execute("PRAGMA user_version").fetchone()[0] != STORAGE_VERSION:
            raise ValueError("unsupported snapshot storage version")
        metadata = {key: _unpack(value) for key, value in connection.execute("SELECT key,value FROM metadata")}
        if metadata.get("schema") != 1 or not isinstance(metadata.get("root"), str) or not isinstance(metadata.get("target"), str):
            raise ValueError("invalid snapshot header metadata")
        return SnapshotStore(path, format, connection=connection, metadata=metadata)
    except (sqlite3.Error, ValueError) as error:
        if connection is not None:
            connection.close()
        raise ValueError(f"invalid SQLite snapshot: {error}") from error


def _iter_verified_file_json_bytes(store: SnapshotStore, *, ensure_ascii: bool) -> Iterator[tuple[str, bytes]]:
    if not store._has_json_cache():
        for path, entry in store.iter_files():
            yield path, json.dumps(
                entry, sort_keys=True, ensure_ascii=ensure_ascii, separators=(",", ":"), allow_nan=False
            ).encode("utf-8")
        return
    conn = store.connection
    for path, header_blob, sem_blob, expected_sig, is_ascii, payload_utf8, payload_ascii in conn.execute(
        """
        SELECT f.path, f.header, f.semantic_header, c.row_sig, c.is_ascii, c.payload_utf8, c.payload_ascii
        FROM files f
        LEFT JOIN file_json_cache c ON c.path = f.path
        ORDER BY f.path
        """
    ):
        if expected_sig is not None and _header_sig(header_blob, sem_blob) == expected_sig:
            if not ensure_ascii or is_ascii:
                yield path, _unpack_bytes(payload_utf8)
            else:
                yield path, _unpack_bytes(payload_ascii)
            continue
        entry = store.get_file(path)
        yield path, json.dumps(
            entry, sort_keys=True, ensure_ascii=ensure_ascii, separators=(",", ":"), allow_nan=False
        ).encode("utf-8")


def logical_chunks(store: SnapshotStore, *, ensure_ascii=True, keys=None):
    metadata = store.metadata
    selected = sorted(set(metadata) | {"files"}) if keys is None else sorted(keys)
    yield b"{"
    for number, key in enumerate(selected):
        if number:
            yield b","
        yield json.dumps(key, ensure_ascii=ensure_ascii).encode("utf-8") + b":"
        if key == "files":
            yield b"{"
            for ordinal, (path, entry_bytes) in enumerate(_iter_verified_file_json_bytes(store, ensure_ascii=ensure_ascii)):
                if ordinal:
                    yield b","
                yield json.dumps(path, ensure_ascii=ensure_ascii).encode("utf-8") + b":"
                yield entry_bytes
            yield b"}"
        else:
            yield json.dumps(metadata.get(key), sort_keys=True, ensure_ascii=ensure_ascii,
                             separators=(",", ":"), allow_nan=False).encode("utf-8")
    yield b"}"


def logical_digest(store: SnapshotStore, *, ensure_ascii: bool = True, keys=None) -> str:
    digest = hashlib.sha256()
    for chunk in logical_chunks(store, ensure_ascii=ensure_ascii, keys=keys):
        digest.update(chunk)
    return digest.hexdigest()


def artifact_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for data in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(data)
    return digest.hexdigest()


def resolve_run_snapshot(run_dir: Path, state: dict) -> Path:
    recorded = state.get("snapshot")
    candidates = {"sqlite": run_dir / "snapshot/manifest.sqlite", "json": run_dir / "snapshot/manifest.json"}
    if sum(path.exists() for path in candidates.values()) != 1:
        raise ValueError("run snapshot is missing or ambiguous")
    if recorded is None:
        format = "json"
    elif (isinstance(recorded, dict) and isinstance(recorded.get("format"), str) and recorded.get("format") in FORMATS
          and recorded.get("storage_version") == STORAGE_VERSION
          and recorded.get("path") == f"snapshot/manifest.{recorded['format']}"):
        format = recorded["format"]
    else:
        raise ValueError("invalid run snapshot format binding")
    path = candidates[format]
    _plain(path)
    if not path.is_file():
        raise ValueError("declared run snapshot is missing")
    with open_snapshot(path, expected_format=format):
        pass
    return path


class FileHeaders(Mapping):
    """Legacy structural algorithms get one header at a time, never semantic facts."""

    def __init__(self, store):
        self.store = store

    def __getitem__(self, path):
        value = self.store.get_file(path, semantic=False)
        if value is None:
            raise KeyError(path)
        return value

    def __iter__(self):
        return self.store.iter_paths()

    def __len__(self):
        return self.store.file_count

    def __contains__(self, path):
        return self.store.has_file(path)


def file_headers(manifest):
    return FileHeaders(manifest) if isinstance(manifest, SnapshotStore) else manifest.get("files", {})


def header_metadata(manifest):
    return manifest.metadata if isinstance(manifest, SnapshotStore) else manifest
