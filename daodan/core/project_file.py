"""The project file `.daodan` (`docs/specs/architettura.md`, «File di progetto»): a SQLite database of schema 2, its
DDL in `project_schema.sql`, the one place it lives. This module creates, opens and recognises the file; it has no
interface.

Standard library `sqlite3` only: the format's version is `PRAGMA user_version`, its identity `PRAGMA application_id`,
and the expected schema is compared by SQLite itself with a database created in memory from the same DDL (no parser
of the DDL).
"""
from __future__ import annotations

import functools
from contextlib import closing
import sqlite3
from pathlib import Path

from snapshot_store import _plain

__all__ = ["APPLICATION_ID", "FORMAT_VERSION", "MIGRATIONS", "ProjectError", "create", "open_project"]

SCHEMA_FILE = Path(__file__).with_name("project_schema.sql")
APPLICATION_ID = 0x44414F44  # "DAOD"
FORMAT_VERSION = 2
SQLITE_MINIMUM = (3, 38)  # JSON functions and STRICT tables
MIGRATIONS: dict = {}  # an older user_version -> its migration (T2.E.8)
BUSY_TIMEOUT_S = 10


class ProjectError(ValueError):
    """A project file that cannot be used, with the cause."""


@functools.cache
def ddl() -> str:
    return SCHEMA_FILE.read_text(encoding="utf-8")


@functools.cache
def untrusted_schema_allowed() -> bool:
    """Whether this SQLite marks its JSON functions innocuous, so that the DDL's CHECKs still run with
    `trusted_schema=OFF` (older builds refuse them with «unsafe use of json_type()»)."""
    with closing(sqlite3.connect(":memory:")) as memory:
        memory.execute("CREATE TABLE probe (value TEXT CHECK (json_valid(value)))")
        memory.execute("PRAGMA trusted_schema=OFF")
        try:
            memory.execute("INSERT INTO probe VALUES ('{}')")
        except sqlite3.DatabaseError:
            return False
        return True


@functools.cache
def _expected_schema() -> frozenset:
    with closing(sqlite3.connect(":memory:")) as memory:
        memory.executescript(ddl())
        return frozenset(memory.execute("SELECT type, name, tbl_name, sql FROM sqlite_schema"))


def _initialize(path: Path) -> None:
    """A new file at `path` with the DDL, in rollback-journal mode: one file to pass on, with no `-wal` beside it."""
    path = Path(path)
    _plain(path)
    if path.exists():
        raise ProjectError(f"il file esiste già: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    fresh = sqlite3.connect(path)
    try:
        fresh.execute("PRAGMA journal_mode=DELETE")
        fresh.executescript(ddl())
    finally:
        fresh.close()


def create(path: Path | str) -> None:
    """An empty project file of schema 2 at `path`, which must not exist."""
    _initialize(Path(path))


def open_project(path: Path | str, write: bool = False) -> sqlite3.Connection:
    """A connection to the project file at `path`, read-only unless `write`, with foreign keys on and untrusted
    schema off (both hold per connection, not in the file), after checking SQLite, identity, version and schema.
    The schema is read before `trusted_schema` is turned off: reading it runs nothing, and a file whose schema is the
    DDL's has no trigger or view; where this SQLite would refuse the DDL's own JSON CHECKs without trust
    (`untrusted_schema_allowed`), that equality is the guard. The caller closes it."""
    path = Path(path)
    _plain(path)
    if not path.is_file():
        raise ProjectError(f"nessun file di progetto: {path}")
    if sqlite3.sqlite_version_info < SQLITE_MINIMUM:
        raise ProjectError(f"il file di progetto chiede SQLite {'.'.join(map(str, SQLITE_MINIMUM))} o successivo, "
                           f"questo Python ha {sqlite3.sqlite_version}")
    uri = path.resolve().as_uri() + ("?mode=rw" if write else "?mode=ro")
    try:
        db = sqlite3.connect(uri, uri=True, timeout=BUSY_TIMEOUT_S, isolation_level=None)
    except sqlite3.Error as error:
        raise ProjectError(f"non si apre {path}: {error}") from error
    try:
        db.execute("PRAGMA foreign_keys=ON")
        try:
            identity = db.execute("PRAGMA application_id").fetchone()[0]
            version = db.execute("PRAGMA user_version").fetchone()[0]
        except sqlite3.DatabaseError as error:
            raise ProjectError(f"non è un file di progetto di Daodan: {path} ({error})") from error
        if identity != APPLICATION_ID:
            raise ProjectError(f"non è un file di progetto di Daodan: {path} (application_id {identity:#x})")
        if version != FORMAT_VERSION:
            if version in MIGRATIONS:
                raise ProjectError(f"serve la migrazione da v{version}: {path}")
            raise ProjectError(f"questo file chiede la versione {version} del formato di Daodan, "
                               f"questa legge la {FORMAT_VERSION}: {path}")
        found = frozenset(db.execute("SELECT type, name, tbl_name, sql FROM sqlite_schema"))
        expected = _expected_schema()
        if found != expected:
            extra = sorted(f"{kind} {name}" for kind, name, _, _ in found - expected)
            missing = sorted(f"{kind} {name}" for kind, name, _, _ in expected - found)
            raise ProjectError(f"lo schema non è quello della versione {FORMAT_VERSION}: {path} "
                               f"(in più: {', '.join(extra) or 'niente'}; diverso o mancante: {', '.join(missing) or 'niente'})")
        if untrusted_schema_allowed():
            db.execute("PRAGMA trusted_schema=OFF")
    except BaseException:
        db.close()
        raise
    return db
