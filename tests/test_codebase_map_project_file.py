"""The project file `.daodan` (`docs/specs/architettura.md`, «File di progetto»): a SQLite file of schema 2 that
Daodan recognises by its identity, its version and its schema, and refuses with the cause otherwise.

    modal run tests/modal_pytest.py --args "tests/test_codebase_map_project_file.py -q"
"""
from __future__ import annotations

import sqlite3
import sys
from contextlib import closing
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "daodan/core"
sys.path.insert(0, str(SCRIPTS))
import node_model
import project_file
from project_file import ProjectError


def _raw(path: Path) -> sqlite3.Connection:
    return sqlite3.connect(path, isolation_level=None)


def _base(db: sqlite3.Connection) -> None:
    """A snapshot, an analysis and revision 1, the least a node's version needs."""
    db.execute("INSERT INTO source_snapshots (source_id, git_commit) VALUES (1, ?)", ("a" * 40,))
    db.execute("INSERT INTO analyses VALUES (1, 1, 'test', '{}', '2026-11-28T00:00:00+00:00')")
    db.execute("INSERT INTO revisions VALUES (1, 'r1', NULL, 1, 'analysis', 'test', '2026-11-28T00:00:00+00:00', 'r1')")


def _node(db: sqlite3.Connection, number: int, species: str) -> None:
    db.execute("INSERT INTO objects VALUES (?, 'node')", (f"n{number}",))
    db.execute("INSERT INTO versions VALUES (?, ?, 1, NULL, 'analysis')", (number, f"n{number}"))
    db.execute("INSERT INTO nodes (version_id, name, species, position, status, abstraction) "
               "VALUES (?, ?, ?, 'interno', 'confermato', 'concreto')", (number, f"n{number}", species))


def test_a_new_file_has_the_identity_the_version_and_the_21_tables(tmp_path):
    path = tmp_path / "project.daodan"
    project_file.create(path)
    with closing(project_file.open_project(path)) as db:
        assert db.execute("PRAGMA application_id").fetchone()[0] == 0x44414F44
        assert db.execute("PRAGMA user_version").fetchone()[0] == 2
        assert db.execute("SELECT count(*) FROM sqlite_schema WHERE type = 'table'").fetchone()[0] == 21
        assert db.execute("PRAGMA journal_mode").fetchone()[0] == "delete"
    assert sorted(item.name for item in tmp_path.iterdir()) == ["project.daodan"]
    with pytest.raises(ProjectError, match="esiste già"):
        project_file.create(path)


@pytest.mark.parametrize(("change", "cause"), [
    ("PRAGMA application_id = 1", "non è un file di progetto"),
    ("PRAGMA user_version = 3", "chiede la versione 3"),
    ("CREATE TABLE extra (x INTEGER) STRICT", "in più: table extra"),
    ("DROP INDEX edge_out", "mancante: index edge_out"),
])
def test_another_identity_version_or_schema_is_refused_with_the_cause(tmp_path, change, cause):
    path = tmp_path / "project.daodan"
    project_file.create(path)
    with closing(_raw(path)) as db:
        db.execute(change)
    with pytest.raises(ProjectError, match=cause):
        project_file.open_project(path).close()


def test_a_known_older_version_asks_for_the_migration(tmp_path, monkeypatch):
    path = tmp_path / "project.daodan"
    project_file.create(path)
    with closing(_raw(path)) as db:
        db.execute("PRAGMA user_version = 1")
    monkeypatch.setitem(project_file.MIGRATIONS, 1, lambda path: None)
    with pytest.raises(ProjectError, match="serve la migrazione da v1"):
        project_file.open_project(path).close()


def test_a_file_that_is_no_database_and_a_link_are_refused(tmp_path):
    other = tmp_path / "other.daodan"
    other.write_bytes(b"not a database, only some bytes" * 4)
    with pytest.raises(ProjectError, match="non è un file di progetto"):
        project_file.open_project(other).close()
    path = tmp_path / "project.daodan"
    project_file.create(path)
    link = tmp_path / "link.daodan"
    link.symlink_to(path)
    with pytest.raises(ValueError, match="linked"):
        project_file.open_project(link).close()


def test_every_species_of_the_code_enters_and_an_invented_one_is_refused_by_the_check(tmp_path):
    """The code's list and the DDL's cannot drift apart."""
    path = tmp_path / "project.daodan"
    project_file.create(path)
    with closing(project_file.open_project(path, write=True)) as db:
        _base(db)
        for number, species in enumerate(node_model.SPECIES, 1):
            _node(db, number, species)
        assert db.execute("SELECT count(*) FROM nodes").fetchone()[0] == len(node_model.SPECIES) == 24
        with pytest.raises(sqlite3.IntegrityError, match="CHECK"):
            _node(db, 100, "drago")


def test_the_foreign_keys_hold_on_every_connection_also_read_only(tmp_path):
    path = tmp_path / "project.daodan"
    project_file.create(path)
    with closing(project_file.open_project(path)) as db:
        assert db.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert db.execute("PRAGMA trusted_schema").fetchone()[0] == (0 if project_file.untrusted_schema_allowed() else 1)
        with pytest.raises(sqlite3.OperationalError, match="readonly"):
            db.execute("INSERT INTO objects VALUES ('x', 'node')")
    with closing(project_file.open_project(path, write=True)) as db:
        _base(db)  # the JSON CHECKs of the DDL run on this connection
        with pytest.raises(sqlite3.IntegrityError, match="FOREIGN KEY"):
            db.execute("INSERT INTO versions VALUES (1, 'missing', 1, NULL, 'analysis')")


# ---------------------------------------------------------------------------------------------------------------
# The writer: creation and revisions, with the integrity checks

SOURCE = {"git_commit": "a" * 40, "git_committed_at": "2026-11-28T09:00:00+00:00"}
ANALYSIS = {"daodan_version": "1.4.1", "config": {"run_id": "r1"}}


def _node_row(object_id, name, species, parent=None):
    return {"id": object_id, "kind": "node", "fields": {"parent_id": parent, "name": name, "species": species,
                                                        "position": "interno", "status": "confermato",
                                                        "abstraction": "concreto", "attributes": {}}}


def _rows():
    """A folder, a file in it, two of its symbols, a call between them and a flow of two steps along it."""
    return [_node_row("dir", "src", "cartella"), _node_row("file", "a.py", "file", "dir"),
            _node_row("run", "run", "simbolo", "file"), _node_row("helper", "helper", "simbolo", "file"),
            {"id": "call", "kind": "edge", "fields": {"source_id": "run", "target_id": "helper", "kind": "chiama",
                                                      "grade": "confirmed", "attributes": {"site": "src/a.py:3"}},
             "evidence": [{"kind": "source", "locator": "src/a.py", "start_line": 3}]},
            {"id": "flow", "kind": "flow", "fields": {"name": "Pagamento", "attributes": {}}},
            {"id": "variant", "kind": "variant", "fields": {"flow_id": "flow", "name": "predefinita"},
             "endpoints": [{"role": "entry", "node_id": "run"}]},
            {"id": "s1", "kind": "step", "fields": {"variant_id": "variant", "display_order": 0, "label": "chiama"},
             "edges": ["call"], "transitions": [{"to_step_id": "s2"}]},
            {"id": "s2", "kind": "step", "fields": {"variant_id": "variant", "display_order": 1, "label": "torna"},
             "edges": ["call"]}]


def _project(tmp_path) -> Path:
    path = tmp_path / "project.daodan"
    project_file.create(path, name="demo", source=SOURCE, analysis=ANALYSIS, rows=_rows(), author="ada")
    return path


def _dump(db) -> dict:
    tables = [name for (name,) in db.execute("SELECT name FROM sqlite_schema WHERE type = 'table' ORDER BY name")]
    return {table: sorted(db.execute(f"SELECT * FROM {table}"), key=repr) for table in tables}


def test_a_minimal_project_is_created_and_read_back(tmp_path):
    path = _project(tmp_path)
    assert sorted(item.name for item in tmp_path.iterdir()) == ["project.daodan"]
    with closing(project_file.open_project(path)) as db:
        assert project_file.head(db) == 1
        assert db.execute("SELECT name, head_rev FROM project").fetchone() == ("demo", 1)
        kind, author, parent, created = db.execute("SELECT kind, author, parent_rev, created_at FROM revisions").fetchone()
        assert (kind, author, parent) == ("analysis", "ada", None) and created.endswith("+00:00")
        found = project_file.state(db)
        assert sorted(found) == sorted(row["id"] for row in _rows())
        assert found["file"]["fields"]["parent_id"] == "dir"
        assert found["call"]["evidence"] == [{"kind": "source", "locator": "src/a.py", "start_line": 3, "end_line": None,
                                              "symbol": None, "blob_ref": None}]
        assert found["variant"]["endpoints"] == [{"role": "entry", "node_id": "run", "description": None}]
        assert found["s1"]["edges"] == ["call"] and found["s1"]["transitions"] == [{"to_step_id": "s2", "condition": None}]
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []
    with pytest.raises(ProjectError, match="esiste già"):
        project_file.create(path, name="demo", source=SOURCE, analysis=ANALYSIS, rows=_rows())


def test_a_project_that_breaks_its_integrity_is_never_created(tmp_path):
    path = tmp_path / "project.daodan"
    with pytest.raises(ProjectError, match="padre non è un nodo attivo"):
        project_file.create(path, name="demo", source=SOURCE, analysis=ANALYSIS,
                            rows=[_node_row("file", "a.py", "file", "dir"), _node_row("dir", "src", "cartella", "gone"),
                                  {"id": "gone", "kind": "gap", "fields": {"description": "x", "cause": "x"}}])
    assert list(tmp_path.iterdir()) == []


STEP_S1 = {"id": "s1", "kind": "step", "fields": {"variant_id": "variant", "display_order": 0, "label": "chiama"},
           "edges": ["call"], "transitions": [{"to_step_id": "s3"}]}


@pytest.mark.parametrize(("change", "cause"), [
    ({"closed": ["dir"], "opened": [_node_row("dir", "src", "cartella", "file")]}, "ciclo"),
    ({"closed": ["dir"]}, "padre non è un nodo attivo"),
    ({"opened": [{"id": "lost", "kind": "edge", "fields": {"source_id": "file", "target_id": "gone", "kind": "usa",
                                                           "grade": "confirmed"}}]}, "estremo dell'arco"),
    ({"closed": ["s1"], "opened": [{"id": "variant2", "kind": "variant", "fields": {"flow_id": "flow", "name": "altra"}},
                                   {"id": "s3", "kind": "step", "edges": ["call"],
                                    "fields": {"variant_id": "variant2", "display_order": 0, "label": "x"}}, STEP_S1]},
     "transizione va a un passo che non è della stessa variante"),
])
def test_a_revision_that_breaks_the_integrity_is_refused_and_the_file_stays_as_it_was(tmp_path, change, cause):
    path = _project(tmp_path)
    with closing(project_file.open_project(path, write=True)) as db:
        db.execute("INSERT INTO objects VALUES ('gone', 'node')")  # an object with no active version
        before = _dump(db)
        with pytest.raises(ProjectError, match=cause):
            project_file.commit(db, expected_head=1, kind="manual", author="ada", summary="prova", **change)
        assert _dump(db) == before and project_file.head(db) == 1


def test_a_revision_closes_and_opens_versions_and_moves_the_head(tmp_path):
    path = _project(tmp_path)
    with closing(project_file.open_project(path, write=True)) as db:
        renamed = _node_row("file", "b.py", "file", "dir")
        assert project_file.commit(db, expected_head=1, kind="manual", author="ada", summary="rinomina",
                                   closed=["file"], opened=[renamed]) == 2
        assert project_file.state(db)["file"]["fields"]["name"] == "b.py"
        assert project_file.state(db, 1)["file"]["fields"]["name"] == "a.py"
        assert db.execute("SELECT parent_rev, analysis_id FROM revisions WHERE rev = 2").fetchone() == (1, 1)
        with pytest.raises(ProjectError, match="è un node, non un edge"):
            project_file.commit(db, expected_head=2, kind="manual", author="ada", summary="x", closed=["dir"],
                                opened=[{"id": "dir", "kind": "edge", "fields": {"source_id": "file", "target_id": "run",
                                                                                 "kind": "usa", "grade": "confirmed"}}])
        assert project_file.head(db) == 2


def test_of_two_writers_from_the_same_head_the_second_is_refused(tmp_path):
    path = _project(tmp_path)
    with closing(project_file.open_project(path, write=True)) as first, \
            closing(project_file.open_project(path, write=True)) as second:
        assert project_file.head(first) == project_file.head(second) == 1
        project_file.commit(first, expected_head=1, kind="manual", author="ada", summary="prima",
                            closed=["file"], opened=[_node_row("file", "b.py", "file", "dir")])
        with pytest.raises(ProjectError, match="la testa è cambiata, rileggi"):
            project_file.commit(second, expected_head=1, kind="manual", author="bob", summary="seconda",
                                closed=["file"], opened=[_node_row("file", "c.py", "file", "dir")])
        assert project_file.state(second)["file"]["fields"]["name"] == "b.py"
