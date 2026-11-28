"""The acceptance tests of the project file's format (`docs/specs/architettura.md`, «Prove di accettazione del formato»),
on files on disk and through the app: a small project analysed by Daodan as the app does, its graph recorded in the
repository's `.daodan` at each analysis, and what a person chooses sent to the app's routes.

    modal run tests/modal_pytest.py --args "tests/test_codebase_map_project_acceptance.py -q"
"""
from __future__ import annotations

import getpass
import http.client
import json
import os
import sqlite3
import subprocess
import sys
import threading
from contextlib import closing
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "daodan/core"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import app as launcher  # noqa: E402
import mcp_service  # noqa: E402
import node_model  # noqa: E402
import project_file  # noqa: E402
import repository  # noqa: E402
from project_file import ProjectError  # noqa: E402

CLEAN = {"GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1", "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
         "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
PAYMENT = "def pay(amount):\n    return amount\n"
EARLIER = HERE / "fixtures/project-file/earlier-build.sql"  # an earlier development build's DDL (c7bc75b)


def git(folder: Path, *arguments: str) -> str:
    return subprocess.run(["git", *arguments], cwd=folder, env={**os.environ, **CLEAN}, check=True,
                          capture_output=True, text=True).stdout.strip()


class Project:
    """A project in `src/`, with or without Git, analysed by Daodan at each `analyse` in a run of its own, and the app
    on it: its project file is the one of the repository o/n under the app's work folder."""

    def __init__(self, tmp_path: Path, files: dict[str, str], with_git: bool = True):
        self.root, self.with_git, self.runs = tmp_path / "shop", with_git, 0
        (self.root / "src").mkdir(parents=True)
        self.write(files)
        if with_git:
            git(self.root, "init", "-q", "-b", "main")
        self.app = launcher.App(tmp_path / "work", environment={})
        self.path = self.app.work / "repositories" / "o" / "n" / repository.PROJECT
        self.server = self.app.serve(token="t")
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def write(self, files: dict[str, str | None]) -> None:
        for name, text in files.items():
            target = self.root / "src" / name
            if text is None:
                target.unlink()
            else:
                target.write_text(text, encoding="utf-8")

    def analyse(self) -> int:
        """A new analysis of the tree as it is now, recorded in the project file as the app does at a pass's end."""
        commit = committed = None
        if self.with_git:
            git(self.root, "add", "-A")
            git(self.root, "commit", "-q", "--allow-empty", "-m", f"r{self.runs + 1}")
            commit, committed = git(self.root, "rev-parse", "HEAD"), git(self.root, "show", "-s", "--format=%cI", "HEAD")
        self.runs += 1
        service = mcp_service.MapService(self.root)
        service.create_run(".", f"r{self.runs}", engine=False)
        self.app.service = service
        self.app.context = {"run_id": f"r{self.runs}", "path": str(self.root), "project": str(self.path), "commit": commit,
                            "committed_at": committed,
                            "repository": {"host": "github.com", "owner": "o", "name": "n", "url": "https://github.com/o/n"}}
        self.app._record(self.app.context)
        assert self.app.recorded["state"] == "done", self.app.recorded
        return self.app.recorded["rev"]

    def ask(self, path: str, body=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_address[1], timeout=120)
        headers = {"X-Daodan-Token": "t"}
        if body is not None:
            headers.update({"Content-Type": "application/json", "Origin": f"http://127.0.0.1:{self.server.server_address[1]}"})
        try:
            connection.request("GET" if body is None else "POST", path, None if body is None else json.dumps(body), headers)
            answer = connection.getresponse()
            return answer.status, json.loads(answer.read())
        finally:
            connection.close()

    def done(self, path: str, body=None) -> dict:
        status, found = self.ask(path, body)
        assert status == 200, found
        return found

    def id_of(self, key: str) -> str:
        with closing(project_file.open_project(self.path)) as db:
            return project_file.find(db, key)

    def read(self, key: str) -> dict:
        with closing(project_file.open_project(self.path)) as db:  # opened again: what is read is what the file keeps
            return project_file.read(db, project_file.find(db, key))

    def close(self) -> None:
        self.app.close()
        self.server.shutdown()
        self.server.server_close()


@pytest.fixture
def made(tmp_path, real_stack):
    """A factory of `Project`s, closed at the test's end."""
    made = []

    def make(files: dict[str, str], with_git: bool = True) -> Project:
        made.append(Project(tmp_path / str(len(made)), files, with_git))
        return made[-1]
    yield make
    for item in made:
        item.close()


DESCRIBED = "Paga il conto del cliente"


def described(project: Project, key: str) -> None:
    """A person describes the node `key` by hand, through the app."""
    project.done("/api/app/project/edit", {"ref": key, "field": "description", "value": DESCRIBED})


@pytest.mark.parametrize("with_git", [True, False])
def test_a_rename_after_an_edit_keeps_the_id_and_the_edit_also_reopened(made, with_git):
    project = made({"payment.py": PAYMENT, "other.py": "x = 1\n"}, with_git)
    assert project.analyse() == 1
    original = project.id_of("file:src/payment.py")
    described(project, "file:src/payment.py")
    os.replace(project.root / "src/payment.py", project.root / "src/transfer.py")
    assert project.analyse() == 3
    assert project.id_of("file:src/transfer.py") == original  # one pair, verified by the two inventories
    found = project.read("file:src/transfer.py")
    assert found["name"] == "transfer.py" and found["attributes"]["description"] == DESCRIBED
    assert project.done("/api/app/project/conflicts")["conflicts"] == []
    with closing(project_file.open_project(project.path)) as db:
        source = project_file.source_of(db)
    assert (source["git_commit"] is not None) == with_git and len(source["tree_sha256"]) == 64


def test_a_copy_beside_its_original_gets_a_new_id_and_the_edit_stays_on_the_original(made):
    project = made({"payment.py": PAYMENT})
    project.analyse()
    original = project.id_of("file:src/payment.py")
    described(project, "file:src/payment.py")
    project.write({"copy.py": PAYMENT})
    project.analyse()
    assert project.id_of("file:src/payment.py") == original and project.id_of("file:src/copy.py") != original
    assert project.read("file:src/payment.py")["attributes"]["description"] == DESCRIBED
    assert "description" not in project.read("file:src/copy.py")["attributes"]
    assert project.done("/api/app/project/conflicts")["proposals"] == []


def test_two_equal_candidates_ask_for_a_confirmation_with_its_author_decision_and_history(made):
    project = made({"x.py": PAYMENT, "y.py": PAYMENT})
    project.analyse()
    x, y = project.id_of("file:src/x.py"), project.id_of("file:src/y.py")
    project.write({"x.py": None, "y.py": None, "z.py": PAYMENT})
    project.analyse()
    z = project.id_of("file:src/z.py")
    (proposal,) = project.done("/api/app/project/conflicts")["proposals"]
    assert z not in (x, y) and proposal["new"] == z and sorted(proposal["candidates"]) == sorted([x, y])
    rev = project.done("/api/app/project/confirm", {"match": proposal["match"], "same": x})["rev"]
    assert project.id_of("file:src/z.py") == x and project.done("/api/app/project/conflicts")["proposals"] == []
    last = project.done("/api/app/project/history")["revisions"][-1]
    assert (last["rev"], last["kind"], last["author"]) == (rev, "resolution", getpass.getuser())
    assert last["summary"] == "conferma: file:src/z.py è file:src/x.py"


def test_a_rename_with_changes_asks_for_a_confirmation_and_then_keeps_the_id_with_its_author_and_history(made):
    """No digest pairs a file renamed and changed, and Git's similarity has no part: the edited original stays, with a
    conflict that says the analysis no longer finds it, until the person says which node it is."""
    project = made({"payment.py": PAYMENT})
    project.analyse()
    original = project.id_of("file:src/payment.py")
    described(project, "file:src/payment.py")
    project.write({"payment.py": None, "transfer.py": PAYMENT + "\n\ndef refund(amount):\n    return -amount\n"})
    project.analyse()
    renamed = project.id_of("file:src/transfer.py")
    assert renamed != original and project.read("file:src/payment.py")["attributes"]["description"] == DESCRIBED
    (conflict,) = project.done("/api/app/project/conflicts")["conflicts"]
    assert conflict["open"] and conflict["key"] == "file:src/payment.py" and conflict["provenance"]["object"] == "removed"
    rev = project.done("/api/app/project/confirm", {"new": "file:src/transfer.py", "same": "file:src/payment.py"})["rev"]
    assert project.id_of("file:src/transfer.py") == original
    assert project.read("file:src/transfer.py")["attributes"]["description"] == DESCRIBED
    (settled,) = project.done("/api/app/project/conflicts")["conflicts"]
    assert not settled["open"] and settled["resolved_rev"] == rev
    last = project.done("/api/app/project/history")["revisions"][-1]
    assert (last["kind"], last["author"], last["summary"]) == \
        ("resolution", getpass.getuser(), "conferma: file:src/transfer.py è file:src/payment.py")
    project.analyse()  # the next analysis keeps the pair and the choice
    assert project.id_of("file:src/transfer.py") == original and project.done("/api/app/project/conflicts")["conflicts"] == [settled]


def test_a_file_received_from_someone_brings_its_changes_into_the_history(made, tmp_path):
    project = made({"payment.py": PAYMENT})
    project.analyse()
    copy = tmp_path / "ricevuto.daodan"
    project.done("/api/app/project/save", {"path": str(copy)})
    with closing(project_file.open_project(copy, write=True)) as db:
        project_file.edit(db, object_id=project_file.find(db, "file:src/payment.py"), field_path="/name", value="Pagamenti",
                          author="bob", base_rev=project_file.head(db))
    project.done("/api/app/project/open", {"path": str(copy)})
    (made_by_bob,) = [item for item in project.done("/api/app/project/history")["revisions"] if item["author"] == "bob"]
    assert made_by_bob["edits"][0]["field_path"] == "/name" and project.read("file:src/payment.py")["name"] == "Pagamenti"


# ---------------------------------------------------------------------------------------------------------------
# The format itself, on the file on disk


def _node(object_id: str, species: str, parent: str | None = None) -> dict:
    return {"id": object_id, "kind": "node", "fields": {"parent_id": parent, "name": object_id, "species": species,
                                                        "position": "interno", "status": "confermato",
                                                        "abstraction": "concreto", "attributes": {}}}


SOURCE, ANALYSIS = {"git_commit": "a" * 40}, {"daodan_version": "test", "config": {}}


def test_the_24_species_are_accepted_and_an_invented_one_is_refused_by_the_ddl_and_by_the_opening(tmp_path):
    path = tmp_path / "project.daodan"
    assert len(node_model.SPECIES) == 24
    project_file.create(path, name="specie", source=SOURCE, analysis=ANALYSIS,
                        rows=[_node(f"n{number}", species) for number, species in enumerate(node_model.SPECIES)])
    with closing(project_file.open_project(path, write=True)) as db:
        assert sorted(row["fields"]["species"] for row in project_file.state(db).values()) == sorted(node_model.SPECIES)
        with pytest.raises(ProjectError, match="CHECK"):
            project_file.commit(db, expected_head=1, kind="manual", author="ada", summary="x", opened=[_node("bad", "inventata")])
    # a file of an earlier development build, of the same version, whose nodes take any species is not one this
    # build opens: its schema is not the DDL's
    loose = tmp_path / "loose.daodan"
    with closing(sqlite3.connect(loose, isolation_level=None)) as db:
        db.executescript(EARLIER.read_text(encoding="utf-8"))
    with pytest.raises(ProjectError, match="lo schema non è quello della versione 1"):
        project_file.open_project(loose).close()


def test_a_cycle_between_parents_is_refused_by_the_writer_and_the_file_stays_as_it_was(tmp_path):
    path = tmp_path / "project.daodan"
    project_file.create(path, name="ciclo", source=SOURCE, analysis=ANALYSIS,
                        rows=[_node("a", "cartella"), _node("b", "cartella", "a")])
    kept = path.read_bytes()
    with closing(project_file.open_project(path, write=True)) as db:
        with pytest.raises(ProjectError, match="ciclo"):
            project_file.commit(db, expected_head=1, kind="manual", author="ada", summary="ciclo", closed=["a"],
                                opened=[_node("a", "cartella", "b")])
        assert project_file.head(db) == 1
    assert path.read_bytes() == kept
