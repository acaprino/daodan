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
