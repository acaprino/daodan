"""Versioned snapshot storage; binary readers do not materialize the inventory."""
from __future__ import annotations

from collections.abc import Mapping
import hashlib
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
        self.connection.execute("INSERT INTO files VALUES(?,?,?)", (path, _pack(header), semantic_header))
        self.connection.executemany("INSERT INTO symbols VALUES(?,?,?,?)",
            ((path, name, number, _pack(payload)) for number, (name, payload) in enumerate(entry["symbols"].items())))
        if semantic_header is not None:
            for kind in stored:
                self.connection.executemany("INSERT INTO facts VALUES(?,?,?,?)",
                    ((path, kind, number, _pack(payload)) for number, payload in enumerate(semantic[kind])))

    def copy_file(self, previous: SnapshotStore, path: str) -> None:
        self.put_file(path, previous.get_file(path))

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
            for ordinal, (path, entry) in enumerate(store.iter_files()):
                if ordinal:
                    yield b","
                yield json.dumps(path, ensure_ascii=ensure_ascii).encode("utf-8") + b":"
                yield json.dumps(entry, sort_keys=True, ensure_ascii=ensure_ascii,
                                 separators=(",", ":"), allow_nan=False).encode("utf-8")
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
