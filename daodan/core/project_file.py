"""The project file `.daodan` (`docs/specs/architettura.md`, «File di progetto»): a SQLite database of format version 1, its
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

from jsonpointer import JsonPointer, JsonPointerException, resolve_pointer, set_pointer  # RFC 6901: not in the stdlib
from snapshot_store import _plain

__all__ = ["ABSENT", "APPLICATION_ID", "FORMAT_VERSION", "ProjectError", "analyse", "applied", "changes",
           "commit", "confirm", "conflicts", "copy", "create", "edit", "find", "head", "history", "incoming", "key_of",
           "open_project", "pair", "read", "release", "resolve", "source_of", "state"]

SCHEMA_FILE = Path(__file__).with_name("project_schema.sql")
APPLICATION_ID = 0x44414F44  # "DAOD"
FORMAT_VERSION = 1  # the one version until the first release: the schema changes in place, no migration
SQLITE_MINIMUM = (3, 38)  # JSON functions and STRICT tables
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


def create(path: Path | str, *, name: str | None = None, source: dict | None = None, analysis: dict | None = None,
           rows: list[dict] = (), author: str = "daodan") -> None:
    """A project file of this version at `path`, which must not exist. With `source` and `analysis` it holds the
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
           opened: list[dict] = (), closed: list[str] = (), edits: list[dict] = (), conflicts: list[dict] = (),
           resolved: list[int] = ()) -> int:
    """Write one revision after `expected_head`, all or nothing, and return its number. In one `BEGIN IMMEDIATE`
    transaction: the head is compared with `expected_head`, the revision is inserted on the analysis it names
    (`analysis_id`; a new one from `source` and `analysis`; else the head's, as a manual edit inherits it), the open
    versions of `closed` (object ids) end, the `opened` rows begin, the `edits` (`{object_id, field_path, action,
    base_rev, base, value}`) and the `conflicts` (`{edit_id, incoming, provenance, evidence}`, their provenance
    `incoming`'s with the analysis) are recorded, the `resolved` conflicts get this revision, the resulting
    state is checked (`check`) and the head moves. Any error rolls everything back."""
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
        try:
            for item in edits:
                db.execute("INSERT INTO manual_edits (rev, base_rev, object_id, field_path, action, base_json, value_json)"
                           " VALUES (?, ?, ?, ?, ?, ?, ?)", (rev, item["base_rev"], item["object_id"], item["field_path"],
                                                             item["action"], json.dumps(item["base"]), json.dumps(item["value"])))
            for item in conflicts:
                provenance = {"analysis": analysis_id, **item["provenance"]}
                conflict = db.execute("INSERT INTO conflicts (detected_rev, edit_id, incoming_json, incoming_provenance)"
                                      " VALUES (?, ?, ?, ?)", (rev, item["edit_id"], json.dumps(item["incoming"]),
                                                               json.dumps(provenance, sort_keys=True))).lastrowid
                for evidence in item.get("evidence", ()):
                    db.execute("INSERT INTO conflict_evidence VALUES (?, ?)", (conflict, _evidence(db, analysis_id, evidence)))
        except sqlite3.IntegrityError as error:
            raise ProjectError(f"modifica o conflitto non validi: {error}") from error
        for conflict in resolved:
            if db.execute("UPDATE conflicts SET resolved_rev = ? WHERE conflict_id = ? AND resolved_rev IS NULL",
                          (rev, conflict)).rowcount != 1:
                raise ProjectError(f"nessun conflitto aperto {conflict}")
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


def _evidence(db: sqlite3.Connection, analysis_id: int, item: dict) -> int:
    return db.execute(f"INSERT INTO evidence (analysis_id, {', '.join(EVIDENCE)}) VALUES (?{', ?' * len(EVIDENCE)})",
                      [analysis_id] + [item.get(column) for column in EVIDENCE]).lastrowid


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
            db.execute("INSERT INTO version_evidence VALUES (?, ?)", (version, _evidence(db, analysis_id, item)))
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


def state(db: sqlite3.Connection, rev: int | None = None, only=None) -> dict[str, dict]:
    """The objects active at `rev` (the head if None), by id, as rows with their `version_id`; with `only`, just
    those object ids."""
    rev = head(db) if rev is None else rev
    rows: dict[str, dict] = {}
    by_version: dict[int, dict] = {}
    for kind, table in TABLES.items():
        columns = [JSON_COLUMNS.get(column, column) for column in COLUMNS[kind]]
        query = (f"SELECT v.object_id, v.version_id, v.provenance, {', '.join('t.' + column for column in columns)}"
                 f" FROM versions AS v JOIN {table} AS t USING (version_id)"
                 f" WHERE v.from_rev <= ? AND (v.until_rev IS NULL OR ? < v.until_rev)")
        chosen = sorted(set(only)) if only is not None else None
        if chosen is not None:
            query += f" AND v.object_id IN ({', '.join('?' * len(chosen))})"
        for object_id, version, provenance, *values in db.execute(query, (rev, rev, *(chosen or ()))):
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


# ---------------------------------------------------------------------------------------------------------------
# A new analysis and the identity proposals


def _content(row: dict) -> str:
    """What a version says, for comparing an incoming row with the active one: provenance, fields and the rows it
    owns, with every optional column filled."""
    return json.dumps({"kind": row["kind"], "provenance": row.get("provenance") or "analysis", "fields": row["fields"],
                       "evidence": sorted(json.dumps({column: item.get(column) for column in EVIDENCE}, sort_keys=True)
                                          for item in row.get("evidence", ())),
                       "endpoints": [{"role": item["role"], "node_id": item["node_id"], "description": item.get("description")}
                                     for item in row.get("endpoints", ())],
                       "edges": list(row.get("edges", ())),
                       "transitions": [{"to_step_id": item["to_step_id"], "condition": item.get("condition")}
                                       for item in row.get("transitions", ())]}, sort_keys=True, default=str)


def _delta(before: dict[str, dict], rows: list[dict]) -> tuple[list[dict], list[str]]:
    """(opened, closed) that take the state `before` to `rows`: a row new or changed opens, an active object changed
    or missing from `rows` closes."""
    incoming = {row["id"]: row for row in rows}
    if len(incoming) != len(rows):
        raise ProjectError("due righe con lo stesso oggetto")
    changed = [row for object_id, row in incoming.items()
               if object_id not in before or _content(before[object_id]) != _content(row)]
    closed = [object_id for object_id in before if object_id not in incoming]
    return changed, closed + [row["id"] for row in changed if row["id"] in before]


def analyse(db: sqlite3.Connection, *, rows: list[dict], hashes: dict[str, str], source: dict, analysis: dict,
            author: str, unread=(), summary: str = "rianalisi") -> int:
    """Record a new analysis of the project as a revision `analysis`: its rows (`project_rows.from_envelope`, by
    key) reconciled with the head (`project_rows.reconcile`), the choices made by hand merged on them with the
    conflicts they raise (`_merge`), and the difference written. The revision number."""
    import project_rows  # it reads this module's rows: imported here, not at the top
    current = head(db)
    before = state(db, current)
    incoming, conflicts = _merge_all(db, current, before, project_rows.reconcile(db, current, rows, hashes, unread))
    opened, closed = _delta(before, incoming)
    return commit(db, expected_head=current, kind="analysis", author=author, summary=summary, source=source,
                  analysis=analysis, opened=opened, closed=closed, conflicts=conflicts)


def changes(db: sqlite3.Connection, before: int, after: int) -> dict[str, list[str]]:
    """The diff between two revisions, by object id: `added` (active only at `after`), `removed` (only at `before`)
    and `changed` (active at both, in another version)."""
    active = "SELECT object_id, version_id FROM versions WHERE from_rev <= {0} AND (until_rev IS NULL OR {0} < until_rev)"
    query = (f"WITH a AS ({active.format(':a')}), b AS ({active.format(':b')})"
             " SELECT a.object_id, a.version_id, b.version_id FROM a LEFT JOIN b USING (object_id)"
             " WHERE a.version_id IS NOT b.version_id"
             " UNION ALL SELECT b.object_id, NULL, b.version_id FROM b WHERE b.object_id NOT IN (SELECT object_id FROM a)")
    out = {"added": [], "removed": [], "changed": []}
    for object_id, old, new in db.execute(query, {"a": before, "b": after}):
        out["added" if old is None else "removed" if new is None else "changed"].append(object_id)
    return {key: sorted(value) for key, value in out.items()}


def confirm(db: sqlite3.Connection, match: str, same: str | None, *, author: str) -> int:
    """Settle the `identity_match` proposal `match` in a revision `resolution` by `author`: with `same`, one of its
    candidates, the new node takes that original id back (`_join`); with None they are distinct and the new id
    stays. The proposal and its gap end either way. The revision number."""
    current = head(db)
    now = state(db, current)
    record = now.get(match)
    if record is None or record["kind"] != "record" or record["fields"]["kind"] != "identity_match":
        raise ProjectError(f"nessuna proposta di corrispondenza aperta: {match}")
    proposal = record["fields"]["payload"]
    closed = [match] + [row["id"] for row in now.values() if row["kind"] == "gap" and row["fields"]["subject_id"] == match]
    opened, raised, resolved = [], [], []
    if same is not None:
        if same not in proposal["candidates"]:
            raise ProjectError(f"{same} non è un candidato di {match}")
        opened, raised, resolved = _join(db, current, now, proposal["new"], same, closed)
    summary = f"conferma: {proposal['keys']['new']} è " + (proposal["keys"]["candidates"][proposal["candidates"].index(same)]
                                                          if same is not None else "un oggetto nuovo")
    return commit(db, expected_head=current, kind="resolution", author=author, summary=summary,
                  opened=opened, closed=closed, conflicts=raised, resolved=resolved)


def pair(db: sqlite3.Connection, new: str, same: str, *, author: str) -> int:
    """The person says that the node `new` is the node `same` of an earlier revision, in a revision `resolution` by
    `author`: a file renamed with changes, which no digest pairs (Git's similarity has no part, decision 7 of `T2.E`)
    and whose edited original the analysis left with a conflict `removed`, or one no edit held. `new` takes the id
    `same` back as a confirmed proposal does (`_join`). The revision number."""
    current = head(db)
    now = state(db, current)
    if now.get(new, {}).get("kind") != "node":
        raise ProjectError(f"nessun nodo attivo {new}")
    known = db.execute("SELECT kind FROM objects WHERE object_id = ?", (same,)).fetchone()
    if known != ("node",) or same == new:
        raise ProjectError(f"{same} non è un altro nodo del progetto")
    closed: list[str] = []
    opened, raised, resolved = _join(db, current, now, new, same, closed)
    keys = [key_of(now[new]), key_of(now[same]) if same in now else same]
    return commit(db, expected_head=current, kind="resolution", author=author, summary=f"conferma: {keys[0]} è {keys[1]}",
                  opened=opened, closed=closed, conflicts=raised, resolved=resolved)


def _join(db: sqlite3.Connection, current: int, now: dict[str, dict], provisional: str, same: str,
          closed: list[str]) -> tuple[list[dict], list[dict], list[int]]:
    """(opened, conflicts, resolved) by which the node `provisional` takes the original id `same` back at the head
    `current`, adding to `closed`: the provisional identity ends, every active row that pointed at it points at the
    original, and the choices kept on the original apply to it (a value they disagree with is a conflict). An
    original the analysis had left active for its choices ends too, with its conflicts `removed`, now settled."""
    if provisional not in now:
        raise ProjectError(f"l'identità provvisoria non è più attiva: {provisional}")
    swap = {provisional: same}

    def moved(value):
        return swap.get(value, value)

    resolved = [conflict for conflict, edit, provenance in db.execute(
        "SELECT c.conflict_id, e.object_id, c.incoming_provenance FROM conflicts AS c JOIN manual_edits AS e USING (edit_id)"
        " WHERE c.resolved_rev IS NULL") if edit == same and json.loads(provenance).get("object") == "removed"]
    pending = {edit: value for edit, value in _open_conflicts(db, current).items()}
    for conflict in resolved:
        (edit,) = db.execute("SELECT edit_id FROM conflicts WHERE conflict_id = ?", (conflict,)).fetchone()
        pending.pop(edit, None)
    reopened, raised = _merge({**now[provisional], "id": same, "provenance": "resolution"}, _edits(db, current, {same}), pending)
    opened = [reopened]
    closed.append(provisional)
    if same in now:
        closed.append(same)
    for row in now.values():
        if row["id"] in closed:
            continue
        replaced = {**row, "fields": {**row["fields"], **{name: moved(row["fields"].get(name)) for name in REFERENCES[row["kind"]]}}}
        if "endpoints" in row:
            replaced["endpoints"] = [{**item, "node_id": moved(item["node_id"])} for item in row["endpoints"]]
        if "edges" in row:
            replaced["edges"] = [moved(item) for item in row["edges"]]
        if "transitions" in row:
            replaced["transitions"] = [{**item, "to_step_id": moved(item["to_step_id"])} for item in row["transitions"]]
        if _content(replaced) != _content(row):
            opened.append(replaced)
            closed.append(row["id"])
    return opened, raised, resolved


def keep_needed(before: dict[str, dict], rows: list[dict], kept: list[dict]) -> list[dict]:
    """`rows` with the rows of `kept` (active rows of `before`) and, transitively, the active rows they point at
    that `rows` lacks: a row that stays keeps its parent, its ends, its flow and its steps' edges."""
    out = list(rows)
    present = {row["id"] for row in out}
    kept = list(kept)
    while kept:
        row = kept.pop()
        if row["id"] in present:
            continue
        present.add(row["id"])
        out.append(row)
        pointed = [row["fields"].get(name) for name in REFERENCES[row["kind"]]] + list(row.get("edges", ())) + \
            [item["node_id"] for item in row.get("endpoints", ())] + [item["to_step_id"] for item in row.get("transitions", ())]
        kept += [before[item] for item in pointed if item in before and item not in present]
    return out


# ---------------------------------------------------------------------------------------------------------------
# Manual edits, their merge at the next analysis and the resolution of conflicts («Integrità al salvataggio», 4)

ABSENT = object()  # the value of an edit that removes its field
_ABSENT = {"present": False}
KEEP = ("manual", "incoming", "analysis")


def _present(value) -> dict:
    return {"present": True, "value": value}


def _lookup(document: dict, pointer: str) -> dict:
    """The field at the JSON Pointer `pointer` of `document` as `{"present": …, "value": …}`."""
    if pointer == "":
        return _present(document)
    try:
        return _present(resolve_pointer(document, pointer))
    except JsonPointerException:
        return _ABSENT


def _put(document: dict, pointer: str, value: dict) -> dict:
    """A copy of `document` with the field at `pointer` set to `value` (`{"present": …}`), or removed. A field is
    a whole object or list: a pointer into a list names no element after a reorder, so it is refused."""
    if pointer == "":
        raise ProjectError("l'oggetto intero non si modifica a mano: si modifica un suo campo")
    parts = JsonPointer(pointer).parts
    if len(parts) == 1 and not value["present"]:
        raise ProjectError(f"un campo della tabella non si toglie, si imposta: {pointer}")
    try:
        container = resolve_pointer(document, JsonPointer.from_parts(parts[:-1]).path)
    except JsonPointerException as error:
        raise ProjectError(f"il campo {pointer} non c'è: {error}") from error
    if not isinstance(container, dict):
        raise ProjectError(f"un elenco si modifica intero, non per indice: {pointer}")
    if value["present"]:
        return set_pointer(document, pointer, value["value"], inplace=False)
    copy = json.loads(json.dumps(document))
    resolve_pointer(copy, JsonPointer.from_parts(parts[:-1]).path).pop(parts[-1], None)
    return copy


def read(db: sqlite3.Connection, object_id: str, rev: int | None = None) -> dict | None:
    """The object as an edit's JSON Pointer reads it at `rev` (the head if None): the columns of its table, with
    `attributes` (or `payload`) as JSON. None when it is not active."""
    found = state(db, rev, [object_id]).get(object_id)
    return None if found is None else found["fields"]


def _edits(db: sqlite3.Connection, rev: int, object_ids=None) -> list[dict]:
    """The last edit of each field up to `rev`, when it is a `set`: the choices that hold."""
    query = ("SELECT edit_id, rev, object_id, field_path, base_json, value_json FROM manual_edits AS e"
             " WHERE action = 'set' AND rev = (SELECT max(rev) FROM manual_edits"
             " WHERE object_id = e.object_id AND field_path = e.field_path AND rev <= :rev)")
    found = [{"edit_id": edit, "rev": number, "object_id": object_id, "field_path": path,
              "base": json.loads(base), "value": json.loads(value)}
             for edit, number, object_id, path, base, value in db.execute(query + " ORDER BY edit_id", {"rev": rev})]
    return [item for item in found if object_ids is None or item["object_id"] in object_ids]


def _open_conflicts(db: sqlite3.Connection, rev: int) -> dict[int, dict]:
    return {edit: json.loads(incoming) for edit, incoming in db.execute(
        "SELECT edit_id, incoming_json FROM conflicts WHERE detected_rev <= ? AND (resolved_rev IS NULL OR ? < resolved_rev)",
        (rev, rev))}


def incoming(edit: dict, version: dict) -> tuple[dict, dict]:
    """The value an analysis brings for the field of `edit` in `version` (the incoming row) and its provenance: who
    owns a manual edit, in one place («Identità e storia»; [deciso, su delega, provvisorio], `T2.E.7`). The `.daodan`
    is the one place the app writes an edit, and Daodan never writes the project's files: `codebase-modules.json`
    and `codebase-system-map.json` stay inputs of the analysis, so a declared value (provenance `declared`) arrives
    as every other value of the analysis does, and its change under an edit is a conflict, never a silent
    precedence. Another answer of the owner changes this function, its test and the sentence of the spec."""
    fields = version["fields"]
    return _lookup(fields, edit["field_path"]), {
        "origin": version.get("provenance") or "analysis",
        "producer": ((fields.get("attributes") or {}).get("identity") or {}).get("producer")}


def _merge(row: dict, edits: list[dict], pending: dict[int, dict]) -> tuple[dict, list[dict]]:
    """`row` as the analysis brings it with the choices of `edits` on it, and the conflicts it raises: an incoming
    value (`incoming`) equal to the edit's base or to its choice keeps the choice; another one keeps it too and is a
    conflict, unless the same value is already one that is open (`pending`, edit id -> incoming)."""
    fields, conflicts = row["fields"], []
    for item in edits:
        value, provenance = incoming(item, {**row, "fields": fields})
        if value not in (item["base"], item["value"]) and pending.get(item["edit_id"]) != value:
            conflicts.append({"edit_id": item["edit_id"], "incoming": value, "evidence": row.get("evidence", ()),
                              "provenance": provenance})
        fields = _put(fields, item["field_path"], item["value"])
    return ({**row, "fields": fields, "provenance": "manual"} if edits else row), conflicts


def _merge_all(db: sqlite3.Connection, current: int, before: dict[str, dict], incoming: list[dict]) -> tuple[list, list]:
    """The incoming rows with every choice that holds at `current`, and the conflicts; an edited object the analysis
    no longer brings stays, with what it needs, and each of its choices is a conflict with an absent value."""
    edits: dict[str, list] = {}
    for item in _edits(db, current):
        edits.setdefault(item["object_id"], []).append(item)
    pending = _open_conflicts(db, current)
    present = {row["id"] for row in incoming}
    out, conflicts, kept = [], [], []
    for row in incoming:
        merged, raised = _merge(row, edits.get(row["id"], []), pending)
        out.append(merged)
        conflicts += raised
    for object_id, items in edits.items():
        if object_id not in present and object_id in before:
            kept.append(before[object_id])
            conflicts += [{"edit_id": item["edit_id"], "incoming": _ABSENT, "evidence": (),
                           "provenance": {"origin": "analysis", "producer": None, "object": "removed"}}
                          for item in items if pending.get(item["edit_id"]) != _ABSENT]
    return keep_needed(before, out, kept), conflicts


def edit(db: sqlite3.Connection, *, object_id: str, field_path: str, value, author: str, base_rev: int,
         summary: str | None = None) -> int:
    """A revision `manual` by `author` that sets the field at the JSON Pointer `field_path` of the object (as `read`
    gives it) to `value` (`ABSENT` removes it), on the analysis of `base_rev`, which must be the head. The old
    version ends and one with the value and the provenance `manual` begins. The edit's base is the value the
    analysis gave the field: its value at `base_rev`, or, over an earlier choice that still holds, that choice's base
    (the three-way merge compares the analysis with the analysis). The revision number."""
    now = state(db, base_rev, [object_id]).get(object_id)
    if now is None:
        raise ProjectError(f"nessun oggetto attivo {object_id} nella revisione {base_rev}")
    chosen = _ABSENT if value is ABSENT else _present(value)
    fields = _put(now["fields"], field_path, chosen)
    earlier = [item["base"] for item in _edits(db, base_rev, {object_id}) if item["field_path"] == field_path]
    return commit(db, expected_head=base_rev, kind="manual", author=author, summary=summary or f"modifica di {field_path}",
                  opened=[{**now, "fields": fields, "provenance": "manual"}], closed=[object_id],
                  edits=[{"object_id": object_id, "field_path": field_path, "action": "set", "base_rev": base_rev,
                          "base": earlier[0] if earlier else _lookup(now["fields"], field_path), "value": chosen}])


def release(db: sqlite3.Connection, *, object_id: str, field_path: str, author: str, base_rev: int) -> int:
    """A revision `manual` in which the field follows the analysis again: it takes back the last analysis value
    the choice knew (its base)."""
    (choice,) = [item for item in _edits(db, base_rev, {object_id}) if item["field_path"] == field_path] or [None]
    if choice is None:
        raise ProjectError(f"nessuna scelta a mano su {field_path} di {object_id}")
    return _settle(db, base_rev, object_id, field_path, choice["base"], "release", choice["base"], author,
                   f"{field_path} torna all'analisi", kind="manual")


def _settle(db, current, object_id, field_path, value, action, base, author, summary, *, kind, resolved=()) -> int:
    """A revision with the field at `value` and the edit `action` (`set` with that value, or `release`)."""
    now = state(db, current, [object_id]).get(object_id)
    if now is None:
        raise ProjectError(f"nessun oggetto attivo {object_id}")
    others = [item for item in _edits(db, current, {object_id}) if item["field_path"] != field_path]
    record = {"object_id": object_id, "field_path": field_path, "action": action, "base_rev": current, "base": base,
              "value": value if action == "set" else _ABSENT}
    fields = _put(now["fields"], field_path, value)
    provenance = "manual" if others or action == "set" else "analysis"
    return commit(db, expected_head=current, kind=kind, author=author, summary=summary,
                  opened=[{**now, "fields": fields, "provenance": provenance}], closed=[object_id],
                  edits=[record], resolved=resolved)


def resolve(db: sqlite3.Connection, conflict_id: int, keep: str, *, author: str) -> int:
    """Settle the open conflict `conflict_id` in a revision `resolution` by `author`, keeping the choice made by hand
    (`manual`), the incoming value as a choice (`incoming`) or following the analysis again (`analysis`); the edit
    is recorded in that revision and its number written in `resolved_rev`. The revision number."""
    if keep not in KEEP:
        raise ProjectError(f"scelta sconosciuta: {keep} (una di {', '.join(KEEP)})")
    current = head(db)
    found = db.execute("SELECT c.incoming_json, c.resolved_rev, e.object_id, e.field_path, e.value_json, c.incoming_provenance"
                       " FROM conflicts AS c JOIN manual_edits AS e USING (edit_id) WHERE c.conflict_id = ?",
                       (conflict_id,)).fetchone()
    if found is None or found[1] is not None:
        raise ProjectError(f"nessun conflitto aperto {conflict_id}")
    incoming, object_id, field_path, chosen = json.loads(found[0]), found[2], found[3], json.loads(found[4])
    removed = json.loads(found[5]).get("object") == "removed"
    value = chosen if keep == "manual" else incoming
    action = "release" if keep == "analysis" else "set"
    if removed and keep != "manual":  # the analysis took the object away and the person agrees
        return commit(db, expected_head=current, kind="resolution", author=author, summary=f"conflitto {conflict_id}: {keep}",
                      closed=[object_id], resolved=[conflict_id],
                      edits=[{"object_id": object_id, "field_path": field_path, "action": action, "base_rev": current,
                              "base": incoming, "value": _ABSENT if action == "release" else incoming}])
    return _settle(db, current, object_id, field_path, value, action, incoming, author, f"conflitto {conflict_id}: {keep}",
                   kind="resolution", resolved=[conflict_id])


def conflicts(db: sqlite3.Connection, rev: int | None = None) -> list[dict]:
    """The conflicts detected up to `rev` (the head if None), each `open` or not at that revision, with the edit's
    field, base and choice, the incoming value and its provenance."""
    rev = head(db) if rev is None else rev
    rows = db.execute("SELECT c.conflict_id, c.detected_rev, c.resolved_rev, c.incoming_json, c.incoming_provenance,"
                      " e.edit_id, e.object_id, e.field_path, e.base_json, e.value_json"
                      " FROM conflicts AS c JOIN manual_edits AS e USING (edit_id) WHERE c.detected_rev <= ?"
                      " ORDER BY c.conflict_id", (rev,))
    return [{"conflict_id": conflict, "detected_rev": detected, "resolved_rev": resolved if resolved and resolved <= rev else None,
             "open": resolved is None or rev < resolved, "incoming": json.loads(incoming), "provenance": json.loads(provenance),
             "edit_id": edit, "object_id": object_id, "field_path": path, "base": json.loads(base), "value": json.loads(value)}
            for conflict, detected, resolved, incoming, provenance, edit, object_id, path, base, value in rows]


# ---------------------------------------------------------------------------------------------------------------
# What the app reads and does with the file: the choices on the envelope, the history, copies


FIELDS = {"name": "/name", "description": "/attributes/description"}  # what the app lets a person change by hand


def key_of(row: dict) -> str | None:
    """The identity key of a row: the envelope's `ref` of a node or a flow."""
    return ((row["fields"].get("attributes") or {}).get("identity") or {}).get("key")


def find(db: sqlite3.Connection, key: str) -> str:
    """The object id of the node or flow active at the head whose identity key is `key`."""
    found = [row["id"] for row in state(db).values() if row["kind"] in ("node", "flow") and key_of(row) == key]
    if len(found) != 1:
        raise ProjectError(f"nessun nodo o flusso attivo con la chiave {key}")
    return found[0]


def applied(envelope: dict, db: sqlite3.Connection) -> dict:
    """A copy of `envelope` with the names and descriptions chosen by hand at the head: an entity or a flow whose
    object holds a choice takes its name and description and says `manual`, and `conflict` too when one of its
    choices has an open conflict. The analysis stays as it is: only what the person chose is carried."""
    rows = state(db)
    opened = {item["object_id"] for item in conflicts(db) if item["open"]}
    chosen = {key_of(row): row for row in rows.values() if row["kind"] in ("node", "flow") and row["provenance"] == "manual"}

    def marked(item: dict, label: str) -> dict:
        row = chosen.get(item["ref"])
        if row is None:
            return item
        description = (row["fields"].get("attributes") or {}).get("description")
        return {**item, label: row["fields"]["name"], "manual": True,
                **({"description": description or ""} if "description" in item or description else {}),
                **({"conflict": True} if row["id"] in opened else {})}
    return {**envelope, "entities": [marked(item, "name") for item in envelope["entities"]],
            "flows": [marked(item, "label") for item in envelope["flows"]]}


def history(db: sqlite3.Connection) -> list[dict]:
    """The revisions in order: number, kind, author, date, summary, the versions opened and closed, and the edits
    (`{object_id, key, field_path, action, base_rev, value}`: who changed what, from which revision)."""
    opened = dict(db.execute("SELECT from_rev, count(*) FROM versions GROUP BY from_rev"))
    closed = dict(db.execute("SELECT until_rev, count(*) FROM versions WHERE until_rev IS NOT NULL GROUP BY until_rev"))
    keys = {object_id: json.loads(attributes).get("identity", {}).get("key") for object_id, attributes in db.execute(
        "SELECT v.object_id, t.attributes_json FROM versions AS v JOIN (SELECT version_id, attributes_json FROM nodes"
        " UNION ALL SELECT version_id, attributes_json FROM flows) AS t USING (version_id)"
        " WHERE v.object_id IN (SELECT object_id FROM manual_edits) ORDER BY v.version_id")}
    edits: dict[int, list] = {}
    for rev, object_id, path, action, base_rev, value in db.execute(
            "SELECT rev, object_id, field_path, action, base_rev, value_json FROM manual_edits ORDER BY edit_id"):
        edits.setdefault(rev, []).append({"object_id": object_id, "key": keys.get(object_id), "field_path": path,
                                          "action": action, "base_rev": base_rev, "value": json.loads(value)})
    return [{"rev": rev, "kind": kind, "author": author, "created_at": created, "summary": summary,
             "opened": opened.get(rev, 0), "closed": closed.get(rev, 0), "edits": edits.get(rev, [])}
            for rev, kind, author, created, summary in db.execute(
                "SELECT rev, kind, author, created_at, summary FROM revisions ORDER BY rev")]


def source_of(db: sqlite3.Connection) -> dict:
    """The sources of the head's analysis, with the columns of `source_snapshots`."""
    found = db.execute(f"SELECT {', '.join('s.' + column for column in SOURCE)} FROM project AS p"
                       " JOIN revisions AS r ON r.rev = p.head_rev JOIN analyses AS a USING (analysis_id)"
                       " JOIN source_snapshots AS s USING (source_id)").fetchone()
    if found is None:
        raise ProjectError("il file non ha ancora un progetto")
    return dict(zip(SOURCE, found))


def copy(source: Path | str, target: Path | str) -> None:
    """A consistent copy of the project file at `source` at `target`, which it replaces: `Connection.backup` into a
    file beside `target`, recognised by `open_project` before it takes `target`'s place."""
    target = Path(target)
    _plain(target)
    staging = target.with_name(f".{target.name}.{uuid.uuid4().hex}.new")
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        with closing(open_project(source)) as db, closing(sqlite3.connect(staging)) as out:
            db.backup(out)
        with closing(open_project(staging)):
            pass
        os.replace(staging, target)
    finally:
        staging.unlink(missing_ok=True)
