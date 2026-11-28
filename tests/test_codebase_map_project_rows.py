"""The rows of a project file revision from the map's envelope and from the snapshot's inventory
(`docs/specs/architettura.md`, «File di progetto»), and how a node is recognised at the next analysis.

    modal run tests/modal_pytest.py --args "tests/test_codebase_map_project_rows.py tests/test_codebase_map_project_file.py -q"
"""
from __future__ import annotations

import hashlib
import random
import struct
import sys
from contextlib import closing
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "daodan/core"
sys.path.insert(0, str(SCRIPTS))
import node_model
import project_file
import project_rows

A = hashlib.sha256(b"def run():\n    return helper()\n").hexdigest()
B = hashlib.sha256(b"def helper():\n    return 1\n").hexdigest()


def _entity(ref, kind, name, **fields):
    entity = {"ref": ref, "type": kind, "name": name, "technical": ref.split(":", 1)[1], "description": "",
              "evidence": [], "gaps": [], **fields}
    entity["species"] = node_model.species_of(entity)
    entity.setdefault("concrete", node_model.concrete(entity["species"]))
    return entity


def envelope():
    """`src/a.py` and `src/b.py` in `src`, `a.py` in two modules, a service and a framework, and a flow of two steps
    from `run` through `helper` to the service."""
    entities = [
        _entity("directory:src", "directory", "src", path="src", location="internal"),
        _entity("file:src/a.py", "file", "a.py", path="src/a.py", location="internal"),
        _entity("file:src/b.py", "file", "b.py", path="src/b.py", location="internal"),
        _entity("module:core", "module", "core", location="internal", status="confirmed", languages=["Python"],
                description="Il nucleo", evidence=[{"path": "codebase-modules.json", "line": 2}]),
        _entity("component:web", "component", "web", location="internal", status="inferred"),
        _entity("symbol:src/a.py::run", "symbol", "run", path="src/a.py", location="internal"),
        _entity("symbol:src/b.py::helper", "symbol", "helper", path="src/b.py", location="internal"),
        _entity("external:stripe", "external", "Stripe", location="external", node_type="servizio o API",
                status="inferred", mark="stripe", provenance="registry"),
        _entity("technology:flask", "technology", "Flask", location="external", node_type="altro", status="inferred"),
        _entity("group:technologies", "group", "Tecnologie", location="internal"),
    ]
    relations = [
        {"ref": "contains:directory:src->file:src/a.py", "kind": "contains", "source": "directory:src",
         "target": "file:src/a.py", "status": "confirmed", "evidence": []},
        {"ref": "contains:directory:src->file:src/b.py", "kind": "contains", "source": "directory:src",
         "target": "file:src/b.py", "status": "confirmed", "evidence": []},
        {"ref": "calls:file:src/a.py->file:src/b.py", "kind": "calls", "source": "file:src/a.py",
         "target": "file:src/b.py", "status": "confirmed", "counts": {"calls": 1},
         "evidence": [{"path": "src/a.py", "line": 2}]},
    ]
    memberships = [
        {"member": "file:src/a.py", "group": "directory:src", "view": "physical"},
        {"member": "file:src/b.py", "group": "directory:src", "view": "physical"},
        {"member": "file:src/a.py", "group": "module:core", "view": "logical"},
        {"member": "file:src/a.py", "group": "component:web", "view": "logical"},
        {"member": "technology:flask", "group": "group:technologies", "view": "logical"},
    ]
    flows = [{"ref": "flow:abc", "entry": "symbol:src/a.py::run", "entry_kind": "rotta", "site": "src/a.py:1",
              "label": "GET /run", "complete": True, "nodes": ["external:stripe", "symbol:src/a.py::run", "symbol:src/b.py::helper"],
              "steps": [{"source": "symbol:src/a.py::run", "target": "symbol:src/b.py::helper", "type": "chiama",
                         "origin": "statico", "site": "src/a.py:2"},
                        {"source": "symbol:src/b.py::helper", "target": "external:stripe", "type": "usa",
                         "origin": "statico", "site": "src/b.py:2"}],
              "gaps": []}]
    gaps = [{"refs": ["component:web"], "reason": "external module without resolved evidence"}]
    return {"schema": "daodan/visual@1", "meta": {}, "entities": entities, "relations": relations,
            "memberships": memberships, "gaps": gaps, "flows": flows, "technologies": []}


def _by_key(rows):
    return {row["key"]: row for row in rows}


def test_every_entity_is_a_node_of_an_admitted_species():
    rows = _by_key(project_rows.from_envelope(envelope(), {"src/a.py": A, "src/b.py": B}))
    nodes = {key: row for key, row in rows.items() if row["kind"] == "node"}
    assert sorted(nodes) == sorted(item["ref"] for item in envelope()["entities"])
    assert all(row["fields"]["species"] in node_model.SPECIES for row in nodes.values())
    file = nodes["file:src/a.py"]["fields"]
    assert file["attributes"]["identity"] == {"producer": "daodan/visual@1", "key": "file:src/a.py",
                                             "path": "src/a.py", "sha256": A}
    assert (file["position"], file["status"], file["abstraction"]) == ("interno", "confermato", "concreto")
    stripe = nodes["external:stripe"]["fields"]
    assert (stripe["position"], stripe["status"], stripe["catalog_id"]) == ("esterno", "dedotto", "stripe")
    core = nodes["module:core"]
    assert core["fields"]["attributes"]["description"] == "Il nucleo" and core["fields"]["attributes"]["languages"] == ["Python"]
    assert core["evidence"] == [{"kind": "source", "locator": "codebase-modules.json", "start_line": 2}]
    assert nodes["group:technologies"]["fields"]["abstraction"] == "astratto"
    assert nodes["technology:flask"]["fields"]["parent_id"] == "group:technologies"


def test_a_file_in_two_modules_has_one_parent_and_two_member_edges():
    given = envelope()
    given["memberships"] += [{"member": "file:src/a.py", "group": "module:core", "view": "physical"},  # twice
                             {"member": "file:src/a.py", "group": "directory:src", "view": "logical"}]  # the parent
    rows = project_rows.from_envelope(given)
    by_key = _by_key(rows)
    assert by_key["file:src/a.py"]["fields"]["parent_id"] == "directory:src"
    members = sorted(row["fields"]["target_id"] for row in rows
                     if row["kind"] == "edge" and row["fields"]["kind"] == "member" and row["fields"]["source_id"] == "file:src/a.py")
    assert members == ["component:web", "module:core"]
    assert not [row for row in rows if row["kind"] == "edge" and row["fields"]["kind"] == "contains"]  # the parent says it
    calls = by_key["calls:file:src/a.py->file:src/b.py"]
    assert calls["fields"]["grade"] == "confirmed" and calls["fields"]["attributes"]["counts"] == {"calls": 1}


def test_a_flow_of_two_steps_has_two_edges_two_steps_and_one_transition():
    rows = project_rows.from_envelope(envelope())
    flow = [row for row in rows if row["kind"] == "flow"]
    assert [row["fields"]["name"] for row in flow] == ["GET /run"]
    (variant,) = [row for row in rows if row["kind"] == "variant"]
    assert variant["fields"]["profile"] is None and variant["endpoints"] == [{"role": "entry", "node_id": "symbol:src/a.py::run"}]
    steps = sorted((row for row in rows if row["kind"] == "step"), key=lambda row: row["fields"]["display_order"])
    edges = [row for row in rows if row["kind"] == "edge" and row["key"].startswith("step:")]
    assert len(steps) == 2 and len(edges) == 2
    assert [step["edges"][0] for step in steps] == [edge["key"] for edge in edges]
    assert sum(len(step["transitions"]) for step in steps) == 1 and steps[0]["transitions"] == [{"to_step_id": steps[1]["key"]}]
    assert edges[0]["fields"]["attributes"]["site"] == "src/a.py:2"
    assert edges[0]["evidence"] == [{"kind": "source", "locator": "src/a.py", "start_line": 2}]


def test_the_rows_make_a_coherent_project(tmp_path):
    rows = project_rows.assign(project_rows.from_envelope(envelope()), {})
    assert len({row["id"] for row in rows}) == len(rows)
    path = tmp_path / "project.daodan"
    project_file.create(path, name="demo", source={"tree_sha256": "0" * 64, "inventory_policy": "{}"},
                        analysis={"daodan_version": "test", "config": {}}, rows=rows)
    with closing(project_file.open_project(path)) as db:
        found = project_file.state(db)
    assert len(found) == len(rows)
    (gap,) = [row for row in found.values() if row["kind"] == "gap"]
    web = next(row["id"] for row in rows if row["key"] == "component:web")
    assert gap["fields"]["subject_id"] == web and gap["fields"]["cause"] == "external module without resolved evidence"


def test_the_tree_digest_is_the_rule_of_the_spec_and_ignores_the_order_of_the_inventory():
    hashes = {"src/b.py": B, "src/a.py": A}
    by_hand = hashlib.sha256()
    for path in ("src/a.py", "src/b.py"):  # binary order of the UTF-8 paths
        by_hand.update(struct.pack(">Q", len(path.encode())) + path.encode() + bytes.fromhex(hashes[path]))
    assert project_rows.tree_sha256(hashes) == by_hand.hexdigest()
    shuffled = list(hashes.items())
    random.Random(1).shuffle(shuffled)
    assert project_rows.tree_sha256(dict(reversed(shuffled))) == project_rows.tree_sha256(dict(shuffled)) == by_hand.hexdigest()
    assert project_rows.tree_sha256({"é": A, "z": B}) != project_rows.tree_sha256({"é": B, "z": A})


# ---------------------------------------------------------------------------------------------------------------
# The same node at the next analysis

PAYMENT = hashlib.sha256(b"def pay():\n    return 1\n").hexdigest()
OTHER = hashlib.sha256(b"x = 1\n").hexdigest()


def _tree(files: dict[str, str], symbols=()) -> tuple[dict, dict]:
    """An envelope of the files `files` (name in `src` -> digest) and of the symbols `symbols` (`name::symbol`), with
    the inventory of the same files."""
    entities = [_entity("directory:src", "directory", "src", path="src", location="internal")]
    memberships = []
    for name in files:
        entities.append(_entity(f"file:src/{name}", "file", name, path=f"src/{name}", location="internal"))
        memberships.append({"member": f"file:src/{name}", "group": "directory:src", "view": "physical"})
    for symbol in symbols:
        name, short = symbol.split("::")
        entities.append(_entity(f"symbol:src/{symbol}", "symbol", short, path=f"src/{name}", location="internal"))
    return ({"schema": "daodan/visual@1", "meta": {}, "entities": entities, "relations": [], "memberships": memberships,
             "gaps": [], "flows": [], "technologies": []},
            {f"src/{name}": digest for name, digest in files.items()})


def _source(hashes):
    return {"tree_sha256": project_rows.tree_sha256(hashes), "inventory_policy": "{}"}


def _start(tmp_path, files, symbols=()):
    found, hashes = _tree(files, symbols)
    path = tmp_path / "project.daodan"
    project_file.create(path, name="demo", source=_source(hashes), analysis={"daodan_version": "test", "config": {}},
                        rows=project_rows.assign(project_rows.from_envelope(found, hashes), {}))
    return path


def _again(db, files, symbols=(), unread=()):
    found, hashes = _tree(files, symbols)
    return project_file.analyse(db, rows=project_rows.from_envelope(found, hashes), hashes=hashes, source=_source(hashes),
                                analysis={"daodan_version": "test", "config": {}}, author="daodan", unread=unread)


def _id(db, key, rev=None):
    (found,) = [row["id"] for row in project_file.state(db, rev).values() if project_rows._key(row) == key]
    return found


def test_a_rename_with_the_same_content_keeps_the_id_and_its_symbols_follow(tmp_path):
    path = _start(tmp_path, {"payment.py": PAYMENT, "other.py": OTHER}, ["payment.py::pay"])
    with closing(project_file.open_project(path, write=True)) as db:
        file, symbol, other = (_id(db, key) for key in ("file:src/payment.py", "symbol:src/payment.py::pay", "file:src/other.py"))
        assert _again(db, {"transfer.py": PAYMENT, "other.py": OTHER}, ["transfer.py::pay"]) == 2
        assert _id(db, "file:src/transfer.py") == file and _id(db, "symbol:src/transfer.py::pay") == symbol
        assert _id(db, "file:src/other.py") == other
        assert project_file.state(db, 1)[file]["fields"]["name"] == "payment.py"
        assert project_file.state(db)[file]["fields"]["name"] == "transfer.py"
        diff = project_file.changes(db, 1, 2)
        assert diff["added"] == [] and diff["removed"] == [] and sorted(diff["changed"]) == sorted([file, symbol])
        assert _again(db, {"transfer.py": PAYMENT, "other.py": OTHER}, ["transfer.py::pay"]) == 3
        assert project_file.changes(db, 2, 3) == {"added": [], "removed": [], "changed": []}


def test_a_copy_beside_its_original_gets_a_new_id(tmp_path):
    path = _start(tmp_path, {"payment.py": PAYMENT})
    with closing(project_file.open_project(path, write=True)) as db:
        file = _id(db, "file:src/payment.py")
        _again(db, {"payment.py": PAYMENT, "copy.py": PAYMENT})
        assert _id(db, "file:src/payment.py") == file and _id(db, "file:src/copy.py") != file
        assert not [row for row in project_file.state(db).values() if row["kind"] == "record"]


def test_two_equal_candidates_ask_for_a_confirmation_and_keep_its_author_and_history(tmp_path):
    path = _start(tmp_path, {"x.py": PAYMENT, "y.py": PAYMENT})
    with closing(project_file.open_project(path, write=True)) as db:
        x, y = _id(db, "file:src/x.py"), _id(db, "file:src/y.py")
        _again(db, {"z.py": PAYMENT})
        z = _id(db, "file:src/z.py")
        assert z not in (x, y)
        now = project_file.state(db)
        (record,) = [row for row in now.values() if row["kind"] == "record"]
        assert record["fields"]["kind"] == "identity_match" and record["provenance"] == "identity"
        assert record["fields"]["payload"]["new"] == z and sorted(record["fields"]["payload"]["candidates"]) == sorted([x, y])
        (gap,) = [row for row in now.values() if row["kind"] == "gap"]
        assert gap["fields"]["subject_id"] == record["id"] and gap["fields"]["cause"] == "identity_match"
        assert _again(db, {"z.py": PAYMENT}) == 3  # an open proposal stays open at the next analysis
        assert record["id"] in project_file.state(db)
        assert project_file.confirm(db, record["id"], x, author="ada") == 4
        now = project_file.state(db)
        assert _id(db, "file:src/z.py") == x and z not in now and record["id"] not in now and gap["id"] not in now
        assert db.execute("SELECT kind, author FROM revisions WHERE rev = 4").fetchone() == ("resolution", "ada")
        assert [row for (row,) in db.execute("SELECT from_rev FROM versions WHERE object_id = ? ORDER BY from_rev", (x,))] == [1, 4]
        assert project_file.state(db, 3)[z]["fields"]["name"] == "z.py"  # the earlier revisions keep their ids


def test_distinct_candidates_keep_the_new_id(tmp_path):
    path = _start(tmp_path, {"x.py": PAYMENT, "y.py": PAYMENT})
    with closing(project_file.open_project(path, write=True)) as db:
        _again(db, {"z.py": PAYMENT})
        z = _id(db, "file:src/z.py")
        (record,) = [row["id"] for row in project_file.state(db).values() if row["kind"] == "record"]
        project_file.confirm(db, record, None, author="ada")
        assert _id(db, "file:src/z.py") == z and record not in project_file.state(db)


def test_a_file_a_partial_analysis_did_not_read_stays_open_with_a_gap(tmp_path):
    path = _start(tmp_path, {"a.py": PAYMENT, "b.py": OTHER})
    with closing(project_file.open_project(path, write=True)) as db:
        b = _id(db, "file:src/b.py")
        _again(db, {"a.py": PAYMENT}, unread={"src/b.py"})
        now = project_file.state(db)
        assert b in now
        (gap,) = [row for row in now.values() if row["kind"] == "gap"]
        assert gap["fields"]["subject_id"] == b and "non è stato letto" in gap["fields"]["description"]
        _again(db, {"a.py": PAYMENT})
        assert b not in project_file.state(db)  # read and gone: it ends
