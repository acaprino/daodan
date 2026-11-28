"""The project file `.daodan` (`docs/specs/architettura.md`, «File di progetto»): a SQLite database of schema 2, its
DDL in `project_schema.sql`, the one place it lives. This module creates, opens and recognises the file, writes its
revisions and reads its state; it has no interface.

Standard library `sqlite3` only: the format's version is `PRAGMA user_version`, its identity `PRAGMA application_id`,
and the expected schema is compared by SQLite itself with a database created in memory from the same DDL (no parser
of the DDL).

A row is one object's version as the writer takes it and `state` gives it back: `id` (the stable `object_id`),
`kind` (`node`, `edge`, `flow`, `variant`, `step`, `gap`, `record`), `provenance`, `fields` (the columns of the
kind's table, with `attributes` and `payload` as JSON values), `evidence` (`{kind, locator, start_line, end_line,
symbol, blob_ref}`), and for a variant its `endpoints` (`{role, node_id, description}`), for a step its `edges`
(object ids, in order) and `transitions` (`{to_step_id, condition}`).
"""
from __future__ import annotations

import functools
import json
import os
import sqlite3
import uuid
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from snapshot_store import _plain

__all__ = ["APPLICATION_ID", "FORMAT_VERSION", "MIGRATIONS", "ProjectError", "commit", "create", "head",
           "open_project", "state"]

SCHEMA_FILE = Path(__file__).with_name("project_schema.sql")
APPLICATION_ID = 0x44414F44  # "DAOD"
FORMAT_VERSION = 2
SQLITE_MINIMUM = (3, 38)  # JSON functions and STRICT tables
MIGRATIONS: dict = {}  # an older user_version -> its migration (T2.E.8)
BUSY_TIMEOUT_S = 10

TABLES = {"node": "nodes", "edge": "edges", "flow": "flows", "variant": "variants", "step": "steps", "gap": "gaps",
          "record": "technical_records"}
COLUMNS = {"node": ("parent_id", "name", "species", "position", "status", "abstraction", "catalog_id", "attributes"),
           "edge": ("source_id", "target_id", "kind", "grade", "profile", "attributes"),
           "flow": ("name", "feature_id", "attributes"),
           "variant": ("flow_id", "name", "profile", "condition"),
           "step": ("variant_id", "display_order", "label"),
           "gap": ("subject_id", "description", "cause", "remedy"),
           "record": ("kind", "payload")}
REFERENCES = {"node": ("parent_id",), "edge": ("source_id", "target_id"), "flow": ("feature_id",),
              "variant": ("flow_id",), "step": ("variant_id",), "gap": ("subject_id",), "record": ()}
JSON_COLUMNS = {"attributes": "attributes_json", "payload": "payload_json"}
EVIDENCE = ("kind", "locator", "start_line", "end_line", "symbol", "blob_ref")
SOURCE = ("repository_uri", "git_commit", "git_committed_at", "tree_sha256", "inventory_policy")
REVISION_KINDS = ("analysis", "manual", "resolution", "import")


class ProjectError(ValueError):
    """A project file that cannot be used, or a revision that cannot be written, with the cause."""


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


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


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


# ---------------------------------------------------------------------------------------------------------------
# Writing


def create(path: Path | str, *, name: str | None = None, source: dict | None = None, analysis: dict | None = None,
           rows: list[dict] = (), author: str = "daodan") -> None:
    """A project file of schema 2 at `path`, which must not exist. With `source` and `analysis` it holds the
    project: snapshot, analysis, revision 1 (`analysis`, by `author`) with `rows`, and the one row of `project`,
    written together in a file beside `path` and moved onto it only once checked; without them, the empty schema.
    `source` has the columns of `source_snapshots`; `analysis` has `daodan_version`, `config` (an object) and
    optionally `started_at`."""
    path = Path(path)
    _plain(path)
    if path.exists():
        raise ProjectError(f"il file esiste già: {path}")
    if source is None and analysis is None:
        _initialize(path)
        return
    if source is None or analysis is None or name is None:
        raise ProjectError("un progetto nasce con nome, sorgenti e analisi")
    staging = path.with_name(f".{path.name}.{uuid.uuid4().hex}.new")
    try:
        _initialize(staging)
        with closing(open_project(staging, write=True)) as db:
            _begin(db)
            try:
                analysis_id = _analysis(db, source, analysis)
                db.execute("INSERT INTO revisions VALUES (1, ?, NULL, ?, 'analysis', ?, ?, ?)",
                           (str(uuid.uuid4()), analysis_id, author, _now(), "prima analisi"))
                db.execute("INSERT INTO project VALUES (1, ?, ?, 1)", (str(uuid.uuid4()), name))
                for row in rows:
                    _open(db, 1, row, analysis_id)
                check(db, 1)
                db.execute("COMMIT")
            except BaseException:
                db.execute("ROLLBACK")
                raise
        os.replace(staging, path)
    finally:
        staging.unlink(missing_ok=True)


def head(db: sqlite3.Connection) -> int:
    found = db.execute("SELECT head_rev FROM project").fetchone()
    if found is None:
        raise ProjectError("il file non ha ancora un progetto")
    return found[0]


def commit(db: sqlite3.Connection, *, expected_head: int, kind: str, author: str, summary: str,
           analysis_id: int | None = None, source: dict | None = None, analysis: dict | None = None,
           opened: list[dict] = (), closed: list[str] = ()) -> int:
    """Write one revision after `expected_head`, all or nothing, and return its number. In one `BEGIN IMMEDIATE`
    transaction: the head is compared with `expected_head`, the revision is inserted on the analysis it names
    (`analysis_id`; a new one from `source` and `analysis`; else the head's, as a manual edit inherits it), the open
    versions of `closed` (object ids) end, the `opened` rows begin, the resulting state is checked (`check`) and
    the head moves. Any error rolls everything back."""
    if kind not in REVISION_KINDS:
        raise ProjectError(f"tipo di revisione sconosciuto: {kind}")
    _begin(db)
    try:
        current = head(db)
        if current != expected_head:
            raise ProjectError(f"la testa è cambiata, rileggi: attesa {expected_head}, trovata {current}")
        if analysis is not None:
            analysis_id = _analysis(db, source, analysis)
        elif analysis_id is None:
            analysis_id = db.execute("SELECT analysis_id FROM revisions WHERE rev = ?", (current,)).fetchone()[0]
        rev = current + 1
        db.execute("INSERT INTO revisions VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                   (rev, str(uuid.uuid4()), current, analysis_id, kind, author, _now(), summary))
        for object_id in closed:
            if db.execute("UPDATE versions SET until_rev = ? WHERE object_id = ? AND until_rev IS NULL",
                          (rev, object_id)).rowcount != 1:
                raise ProjectError(f"nessuna versione aperta da chiudere: {object_id}")
        for row in opened:
            _open(db, rev, row, analysis_id)
        db.execute("UPDATE project SET head_rev = ?", (rev,))
        check(db, rev)
        db.execute("COMMIT")
        return rev
    except BaseException:
        db.execute("ROLLBACK")
        raise


def _begin(db: sqlite3.Connection) -> None:
    """A write transaction whose foreign keys are checked at its end (`check`), so rows may name each other in any
    order; the pragma ends with the transaction."""
    db.execute("BEGIN IMMEDIATE")
    db.execute("PRAGMA defer_foreign_keys=ON")


def _analysis(db: sqlite3.Connection, source: dict, analysis: dict) -> int:
    """The analysis row of `analysis` on the snapshot `source`, which an equal snapshot already written serves."""
    unknown = set(source) - set(SOURCE)
    if unknown:
        raise ProjectError(f"campi sconosciuti delle sorgenti: {sorted(unknown)}")
    values = [source.get(column) for column in SOURCE]
    found = db.execute("SELECT source_id FROM source_snapshots WHERE "
                       + " AND ".join(f"{column} IS ?" for column in SOURCE), values).fetchone()
    try:
        source_id = found[0] if found else db.execute(
            f"INSERT INTO source_snapshots ({', '.join(SOURCE)}) VALUES ({', '.join('?' * len(SOURCE))})", values).lastrowid
        return db.execute("INSERT INTO analyses (source_id, daodan_version, config_json, started_at) VALUES (?, ?, ?, ?)",
                          (source_id, analysis["daodan_version"], json.dumps(analysis.get("config", {}), sort_keys=True),
                           analysis.get("started_at") or _now())).lastrowid
    except sqlite3.IntegrityError as error:
        raise ProjectError(f"sorgenti o analisi non valide: {error}") from error


def _open(db: sqlite3.Connection, rev: int, row: dict, analysis_id: int) -> int:
    """Open a version of `row` at `rev`: its object (new, or of the same kind), the version, the row of its kind's
    table, its evidence and the rows it owns. The version id."""
    kind, object_id = row["kind"], row["id"]
    if kind not in TABLES:
        raise ProjectError(f"tipo di oggetto sconosciuto: {kind}")
    fields = row["fields"]
    unknown = set(fields) - set(COLUMNS[kind])
    if unknown:
        raise ProjectError(f"campi sconosciuti per {kind} {object_id}: {sorted(unknown)}")
    try:
        db.execute("INSERT INTO objects VALUES (?, ?) ON CONFLICT (object_id) DO NOTHING", (object_id, kind))
        stored = db.execute("SELECT kind FROM objects WHERE object_id = ?", (object_id,)).fetchone()[0]
        if stored != kind:
            raise ProjectError(f"l'oggetto {object_id} è un {stored}, non un {kind}")
        version = db.execute("INSERT INTO versions (object_id, from_rev, provenance) VALUES (?, ?, ?)",
                             (object_id, rev, row.get("provenance") or "analysis")).lastrowid
        columns = ["version_id"] + [JSON_COLUMNS.get(column, column) for column in COLUMNS[kind]]
        values = [version] + [json.dumps(fields.get(column, {} if column == "attributes" else None), sort_keys=True)
                              if column in JSON_COLUMNS else fields.get(column) for column in COLUMNS[kind]]
        db.execute(f"INSERT INTO {TABLES[kind]} ({', '.join(columns)}) VALUES ({', '.join('?' * len(columns))})", values)
        for item in row.get("evidence", ()):
            evidence = db.execute(f"INSERT INTO evidence (analysis_id, {', '.join(EVIDENCE)}) VALUES (?{', ?' * len(EVIDENCE)})",
                                  [analysis_id] + [item.get(column) for column in EVIDENCE]).lastrowid
            db.execute("INSERT INTO version_evidence VALUES (?, ?)", (version, evidence))
        roles: dict[str, int] = {}
        for item in row.get("endpoints", ()):
            ordinal = roles[item["role"]] = roles.get(item["role"], -1) + 1
            db.execute("INSERT INTO variant_endpoints VALUES (?, ?, ?, ?, ?)",
                       (version, item["role"], ordinal, item["node_id"], item.get("description")))
        for ordinal, edge in enumerate(row.get("edges", ())):
            db.execute("INSERT INTO step_edges VALUES (?, ?, ?)", (version, ordinal, edge))
        for ordinal, item in enumerate(row.get("transitions", ())):
            db.execute("INSERT INTO step_transitions VALUES (?, ?, ?, ?)",
                       (version, ordinal, item["to_step_id"], item.get("condition")))
    except sqlite3.IntegrityError as error:
        raise ProjectError(f"{kind} {object_id} non valido: {error}") from error
    return version


# ---------------------------------------------------------------------------------------------------------------
# Integrity of a revision («Integrità al salvataggio», points 1-3), as queries on the state it leaves

_ACTIVE = ("WITH active AS (SELECT v.version_id, v.object_id, o.kind FROM versions AS v JOIN objects AS o USING (object_id)"
           " WHERE v.from_rev <= :rev AND (v.until_rev IS NULL OR :rev < v.until_rev)),"
           " live_nodes AS (SELECT object_id FROM active WHERE kind = 'node') ")


def _checks():
    """(cause, query): each query lists the object ids that break the cause at revision `:rev`."""
    yield "la testa non è l'ultima revisione", "SELECT 'project' FROM project WHERE head_rev <> (SELECT max(rev) FROM revisions)"
    yield ("due intervalli di validità dello stesso oggetto si sovrappongono",
           "SELECT a.object_id FROM versions AS a JOIN versions AS b ON a.object_id = b.object_id AND a.version_id < b.version_id"
           " WHERE a.from_rev < coalesce(b.until_rev, 9e18) AND b.from_rev < coalesce(a.until_rev, 9e18)")
    for kind, table in TABLES.items():
        yield (f"una versione di un oggetto {kind} senza la sua riga in {table}",
               f"SELECT v.object_id FROM versions AS v JOIN objects AS o USING (object_id)"
               f" WHERE o.kind = '{kind}' AND v.version_id NOT IN (SELECT version_id FROM {table})")
        yield (f"una riga di {table} per un oggetto che non è {kind}",
               f"SELECT v.object_id FROM {table} AS t JOIN versions AS v USING (version_id) JOIN objects AS o USING (object_id)"
               f" WHERE o.kind <> '{kind}'")
    yield ("il padre non è un nodo attivo",
           _ACTIVE + "SELECT a.object_id FROM active AS a JOIN nodes AS n USING (version_id)"
                     " WHERE n.parent_id IS NOT NULL AND n.parent_id NOT IN live_nodes")
    yield ("la gerarchia dei padri ha un ciclo",
           _ACTIVE + ", tree AS (SELECT a.object_id, n.parent_id FROM active AS a JOIN nodes AS n USING (version_id)),"
                     " up (start, node) AS (SELECT object_id, parent_id FROM tree WHERE parent_id IS NOT NULL"
                     " UNION SELECT up.start, tree.parent_id FROM up JOIN tree ON tree.object_id = up.node"
                     " WHERE tree.parent_id IS NOT NULL)"
                     " SELECT start FROM up WHERE node = start")
    yield ("un estremo dell'arco non è un nodo attivo",
           _ACTIVE + "SELECT a.object_id FROM active AS a JOIN edges AS e USING (version_id)"
                     " WHERE e.source_id NOT IN live_nodes OR e.target_id NOT IN live_nodes")
    yield ("un ingresso o un esito della variante non è un nodo attivo",
           _ACTIVE + "SELECT a.object_id FROM active AS a JOIN variant_endpoints AS p ON p.variant_version = a.version_id"
                     " WHERE p.node_id NOT IN live_nodes")
    yield ("la funzionalità del flusso non è un nodo attivo",
           _ACTIVE + "SELECT a.object_id FROM active AS a JOIN flows AS f USING (version_id)"
                     " WHERE f.feature_id IS NOT NULL AND f.feature_id NOT IN live_nodes")
    yield ("la variante non appartiene a un flusso attivo",
           _ACTIVE + "SELECT a.object_id FROM active AS a JOIN variants AS v USING (version_id)"
                     " WHERE v.flow_id NOT IN (SELECT object_id FROM active WHERE kind = 'flow')")
    yield ("il passo non appartiene a una variante attiva",
           _ACTIVE + "SELECT a.object_id FROM active AS a JOIN steps AS s USING (version_id)"
                     " WHERE s.variant_id NOT IN (SELECT object_id FROM active WHERE kind = 'variant')")
    yield ("un arco del passo non è attivo per il profilo della sua variante",
           _ACTIVE + "SELECT a.object_id FROM active AS a JOIN steps AS s USING (version_id)"
                     " JOIN step_edges AS se ON se.step_version = a.version_id"
                     " JOIN active AS va ON va.object_id = s.variant_id JOIN variants AS v ON v.version_id = va.version_id"
                     " WHERE NOT EXISTS (SELECT 1 FROM active AS ea JOIN edges AS e ON e.version_id = ea.version_id"
                     " WHERE ea.object_id = se.edge_id AND (e.profile IS NULL OR e.profile IS v.profile))")
    yield ("una transizione va a un passo che non è della stessa variante",
           _ACTIVE + "SELECT a.object_id FROM active AS a JOIN steps AS s USING (version_id)"
                     " JOIN step_transitions AS t ON t.from_step_version = a.version_id"
                     " WHERE NOT EXISTS (SELECT 1 FROM active AS ta JOIN steps AS other ON other.version_id = ta.version_id"
                     " WHERE ta.object_id = t.to_step_id AND other.variant_id = s.variant_id)")


def check(db: sqlite3.Connection, rev: int) -> None:
    """ProjectError with every cause the state at `rev` breaks, and the objects that break it; first the foreign
    keys."""
    dangling = sorted({f"{table} {rowid} -> {parent}" for table, rowid, parent, _ in db.execute("PRAGMA foreign_key_check")})
    if dangling:
        raise ProjectError(f"la revisione {rev} cita oggetti che non esistono: {', '.join(dangling[:5])}")
    problems = []
    for cause, query in _checks():
        found = sorted({item for (item,) in db.execute(query, {"rev": rev})})
        if found:
            problems.append(f"{cause}: {', '.join(found[:5])}" + (f" e altri {len(found) - 5}" if len(found) > 5 else ""))
    if problems:
        raise ProjectError(f"la revisione {rev} non è coerente: " + "; ".join(problems))


# ---------------------------------------------------------------------------------------------------------------
# Reading


def state(db: sqlite3.Connection, rev: int | None = None) -> dict[str, dict]:
    """The objects active at `rev` (the head if None), by id, as rows with their `version_id`."""
    rev = head(db) if rev is None else rev
    rows: dict[str, dict] = {}
    by_version: dict[int, dict] = {}
    for kind, table in TABLES.items():
        columns = [JSON_COLUMNS.get(column, column) for column in COLUMNS[kind]]
        query = (f"SELECT v.object_id, v.version_id, v.provenance, {', '.join('t.' + column for column in columns)}"
                 f" FROM versions AS v JOIN {table} AS t USING (version_id)"
                 f" WHERE v.from_rev <= ? AND (v.until_rev IS NULL OR ? < v.until_rev)")
        for object_id, version, provenance, *values in db.execute(query, (rev, rev)):
            fields = {column: json.loads(value) if column in JSON_COLUMNS else value
                      for column, value in zip(COLUMNS[kind], values)}
            row = {"id": object_id, "kind": kind, "provenance": provenance, "version_id": version, "fields": fields,
                   "evidence": []}
            if kind == "variant":
                row["endpoints"] = []
            if kind == "step":
                row["edges"], row["transitions"] = [], []
            rows[object_id] = by_version[version] = row
    versions = sorted(by_version)
    for chunk in (versions[start:start + 500] for start in range(0, len(versions), 500)):
        marks = ", ".join("?" * len(chunk))
        for version, *values in db.execute(
                f"SELECT ve.version_id, {', '.join('e.' + column for column in EVIDENCE)} FROM version_evidence AS ve"
                f" JOIN evidence AS e USING (evidence_id) WHERE ve.version_id IN ({marks}) ORDER BY e.evidence_id", chunk):
            by_version[version]["evidence"].append(dict(zip(EVIDENCE, values)))
        for version, role, node_id, description in db.execute(
                f"SELECT variant_version, role, node_id, description FROM variant_endpoints"
                f" WHERE variant_version IN ({marks}) ORDER BY variant_version, role, ordinal", chunk):
            by_version[version]["endpoints"].append({"role": role, "node_id": node_id, "description": description})
        for version, edge in db.execute(f"SELECT step_version, edge_id FROM step_edges WHERE step_version IN ({marks})"
                                        f" ORDER BY step_version, ordinal", chunk):
            by_version[version]["edges"].append(edge)
        for version, target, condition in db.execute(
                f"SELECT from_step_version, to_step_id, condition FROM step_transitions"
                f" WHERE from_step_version IN ({marks}) ORDER BY from_step_version, ordinal", chunk):
            by_version[version]["transitions"].append({"to_step_id": target, "condition": condition})
    return rows
