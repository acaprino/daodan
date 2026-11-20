"""The reference checker accepts a map whose citations hold and names each one that does not."""
from __future__ import annotations

import copy
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import reference  # noqa: E402
import system_map  # noqa: E402

GOOD = {
    "case": "shop", "nodes": [
        {"name": "Negozio", "type": "altro", "members": ["api"], "what": "Tutto il sistema.",
         "proof": [{"at": "api/app.py:1", "has": "def orders"}]},
        {"name": "API ordini", "type": "servizio o API", "inside": "Negozio", "members": ["api/app.py::orders"],
         "what": "Riceve gli ordini.", "routes": ["POST /orders"], "proof": [{"at": "api/app.py:1", "has": "def orders"}]},
        {"name": "Archivio ordini", "type": "filesystem", "position": "external", "evidence": ["api/app.py:2"],
         "what": "Il file degli ordini.", "proof": [{"at": "api/app.py:2", "has": "orders.json"}]},
    ],
    "flows": [{"name": "Nuovo ordine", "area": "funzioni principali", "types": ["funzionale"],
               "nodes": ["API ordini", "Archivio ordini"],
               "arrows": [{"from": "API ordini", "to": "Archivio ordini", "data": "l'ordine", "kind": "scrive",
                           "cite": "api/app.py:2", "has": "open("}],
               "entries": [{"node": "API ordini", "kind": "rotta", "what": "POST /orders"}],
               "effects": [{"node": "Archivio ordini", "what": "l'ordine salvato"}]}],
    "areas": [{"name": area, "present": area == "funzioni principali"} for area in system_map.AREAS],
    "packages": [{"path": "api", "manifest": "api/pyproject.toml", "kind": "python-package"}], "gaps": [],
}


def project(tmp_path: Path) -> Path:
    (tmp_path / "api").mkdir()
    (tmp_path / "api" / "app.py").write_text('def orders():\n    open("orders.json", "a")\n', encoding="utf-8")
    (tmp_path / "api" / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
    (tmp_path / "secrets.json").write_text("{}", encoding="utf-8")
    return tmp_path


def problems(tmp_path: Path, change) -> list[str]:
    value = copy.deepcopy(GOOD)
    change(value)
    return reference.check(value, project(tmp_path))["problems"]


def test_a_map_whose_citations_hold_has_no_problem(tmp_path):
    report = reference.check(GOOD, project(tmp_path))
    assert report["problems"] == []
    assert report["by_depth"] == {0: 2, 1: 1}


def test_each_wrong_citation_is_named(tmp_path):
    cases = {
        "outside the file": lambda v: v["nodes"][1]["proof"].__setitem__(0, {"at": "api/app.py:9", "has": "def orders"}),
        "is not within": lambda v: v["flows"][0]["arrows"][0].__setitem__("has", "requests.post"),
        "is not in the project": lambda v: v["nodes"][1]["members"].append("api/gone.py"),
        "does not name": lambda v: v["nodes"][1]["members"].append("api/app.py::refunds"),
        "file of secrets": lambda v: v["nodes"][2]["proof"].__setitem__(0, {"at": "secrets.json:1", "has": "{"}),
        "is not a node": lambda v: v["nodes"][1].__setitem__("inside", "Magazzino"),
        "only an internal node has members": lambda v: v["nodes"][2].__setitem__("members", ["api"]),
        "not declared present": lambda v: v["flows"][0].__setitem__("area", "comunicazioni"),
        "an end is not a node of the flow": lambda v: v["flows"][0]["arrows"][0].__setitem__("to", "Negozio"),
    }
    for expected, change in cases.items():
        folder = tmp_path / expected.replace(" ", "-")
        folder.mkdir()
        found = problems(folder, change)
        assert any(expected in problem for problem in found), (expected, found)


PAYMENTS = {"name": "Pagamenti", "type": "gateway", "position": "external", "evidence": ["api/app.py:1"],
            "what": "Incassa gli ordini.", "proof": [{"at": "api/app.py:1", "has": "def orders"}],
            "family": "provider", "role": "processore dei pagamenti", "mode": "chiamate API e avvisi di ritorno"}


def test_an_external_service_says_its_family_role_and_mode(tmp_path):
    value = copy.deepcopy(GOOD)
    value["nodes"].append(copy.deepcopy(PAYMENTS))
    assert reference.check(value, project(tmp_path))["problems"] == []
    cases = {
        "missing family": lambda v: v["nodes"][3].pop("family"),
        "unknown family": lambda v: v["nodes"][3].__setitem__("family", "fornitore"),
        "empty role": lambda v: v["nodes"][3].__setitem__("role", ""),
        "missing mode": lambda v: v["nodes"][3].pop("mode"),
        "fields on an internal node": lambda v: v["nodes"][1].__setitem__("role", "le rotte"),
        "fields on a filesystem": lambda v: v["nodes"][2].__setitem__("family", "provider"),
    }
    for label, change in cases.items():
        folder = tmp_path / label.replace(" ", "-")
        folder.mkdir()
        found = problems(folder, lambda v: (v["nodes"].append(copy.deepcopy(PAYMENTS)), change(v)))
        assert len(found) == 1 and "family, role and mode" in found[0], (label, found)


def test_registry_names_an_entry_of_the_registry_on_an_external_node(tmp_path):
    value = copy.deepcopy(GOOD)
    value["nodes"].append({**value["nodes"][2], "name": "Stripe · pagamenti", "registry": "stripe"})
    value["nodes"].append({**value["nodes"][2], "name": "Futuro", "registry": "not-yet-in-the-registry"})
    report = reference.check(value, project(tmp_path))
    assert report["problems"] == []
    assert report["notes"] == ["node Futuro: registry not-yet-in-the-registry is not in the registry yet"]
    (tmp_path / "internal").mkdir()
    found = problems(tmp_path / "internal", lambda v: v["nodes"][1].__setitem__("registry", "stripe"))
    assert found == ["node API ordini: only an external node has a registry id"]


def test_a_flow_named_by_an_empty_word_and_a_service_not_by_its_registry_name_are_problems(tmp_path):
    found = problems(tmp_path, lambda v: (v["flows"][0].__setitem__("name", "Gestione degli ordini"),
                                          v["nodes"].append({**copy.deepcopy(PAYMENTS), "registry": "stripe"})))
    assert found == [f"flow Gestione degli ordini: {system_map.flow_name_problem('Gestione degli ordini')}",
                     f"node Pagamenti: {system_map.registry_name_problem('Pagamenti', 'stripe')}"]


def test_a_reference_bound_to_a_commit_is_checked_on_that_commit(tmp_path):
    (tmp_path / "shop").mkdir()
    root = project(tmp_path / "shop")
    git = ["git", "-C", str(root), "-c", "user.name=t", "-c", "user.email=t@example.invalid"]
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    subprocess.run([*git, "add", "-A"], check=True)
    subprocess.run([*git, "commit", "-q", "-m", "x"], check=True)
    commit = subprocess.run([*git, "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
    (root / "api" / "app.py").write_text("\n" * 9 + 'def orders():\n    open("orders.json", "a")\n', encoding="utf-8")
    assert reference.check(GOOD, root)["problems"] != []                      # the project went on
    assert reference.check({**GOOD, "commit": commit}, root)["problems"] == []  # the reference stays on its commit
    spanning = reference.Committed(tmp_path, {"shop": commit})                # a case over repositories, each in its folder
    assert (spanning.kind("shop/api"), spanning.kind("shop/api/app.py"), spanning.kind("shop/gone.py")) == ("dir", "file", None)
    assert spanning.text("shop/api/app.py")[0] == "def orders():"


def test_pinning_moves_a_citation_to_where_its_text_went_and_names_the_one_that_is_gone(tmp_path):
    root = project(tmp_path)
    git = ["git", "-C", str(root), "-c", "user.name=t", "-c", "user.email=t@example.invalid"]
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    (root / "api" / "app.py").write_text("\n" * 9 + 'def orders():\n    open("orders.json", "a")\n', encoding="utf-8")
    subprocess.run([*git, "add", "-A"], check=True)
    subprocess.run([*git, "commit", "-q", "-m", "x"], check=True)
    commit = subprocess.run([*git, "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
    value = copy.deepcopy(GOOD)
    value["nodes"][1]["proof"].append({"at": "api/app.py:1", "has": "def refunds"})
    report = reference.pin(value, root, commit)
    assert value["commit"] == commit and report["moved"] == 4
    assert value["nodes"][1]["proof"][0] == {"at": "api/app.py:10", "has": "def orders"}
    assert value["flows"][0]["arrows"][0]["cite"] == "api/app.py:11"
    assert report["problems"] == ["node API ordini: «def refunds» is not within 3 lines of api/app.py:1"]
