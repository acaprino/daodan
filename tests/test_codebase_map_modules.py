"""Manifest readers and module contracts, independent of the benchmark corpus."""
from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "daodan/core"
sys.path.insert(0, str(SCRIPTS))

import modules  # noqa: E402
import snapshot  # noqa: E402
from snapshot_store import open_snapshot  # noqa: E402

FIXTURES = Path(__file__).with_name("fixtures") / "modules"
READERS = json.loads((FIXTURES / "readers.json").read_text(encoding="utf-8"))
REGRESSIONS = json.loads((FIXTURES / "regressions.json").read_text(encoding="utf-8"))


def build(tmp_path, files, *, ledger=()):
    project = tmp_path / "proj"
    for name, text in files.items():
        path = project / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    manifest = tmp_path / "out" / "manifest.sqlite"
    snapshot.read_project(project, manifest)
    with open_snapshot(manifest) as store:
        graph = modules.derive(store, ledger=list(ledger))
    return project, manifest, graph


def relations(graph, kind):
    names = {m["id"]: m["name"] for m in graph["modules"]}
    return sorted([names[e["source"]], names[e["target"]]] for e in graph["edges"] if e["kind"] == kind)


def assert_case(graph, case):
    actual = [[m["name"], m["kind"], m["members"][0]["path"], m["external"]]
              for m in graph["modules"] if m["provenance"] == "build"]
    assert sorted(actual) == sorted(case["units"])
    assert relations(graph, "declares") == sorted(case["declares"])
    assert relations(graph, "contains") == sorted(case["contains"])


def test_every_registered_reader_has_a_case():
    readers = {*modules.READERS.values(), *modules.SUFFIX_READERS.values()}
    assert {reader.__name__ for _, reader in readers} == set(READERS)


@pytest.mark.parametrize("reader", sorted(READERS))
def test_reader_manifest_units_dependencies_and_workspace(tmp_path, reader):
    case = READERS[reader]
    _, _, graph = build(tmp_path, case["files"])
    assert_case(graph, case)
    assert all(m["status"] == "confirmed" for m in graph["modules"])
    assert graph["gaps"] == []


@pytest.mark.parametrize("cause", sorted(REGRESSIONS))
def test_regression(tmp_path, cause):
    case = REGRESSIONS[cause]
    _, _, graph = build(tmp_path, case["files"])
    assert_case(graph, case)


def test_contract_record_and_evidence_are_bound_to_snapshot(tmp_path):
    _, manifest, graph = build(tmp_path, READERS["_package_json"]["files"])
    assert graph["schema"] == modules.SCHEMA
    assert graph["binding"]["manifest"] == str(manifest.resolve())
    assert len(graph["binding"]["logical_digest"]) == 64
    required = {"id", "name", "kind", "provenance", "status", "members", "manifests", "evidence",
                "files", "paths", "external", "coverage", "gaps", "conflicts"}
    ids = {m["id"] for m in graph["modules"]}
    assert len(ids) == len(graph["modules"])
    with open_snapshot(manifest) as store:
        inventory = set(store.iter_paths())
        assert modules.derive(store, ledger=[]) == graph
    for record in graph["modules"]:
        assert required <= record.keys()
        assert record["provenance"] == "build"
        assert set(record["manifests"]) <= inventory
        assert set(record["files"]) <= inventory
        assert all(e["path"] in inventory for e in record["evidence"])
        assert record["coverage"]["files"] == len(record["files"])
    for edge in graph["edges"]:
        assert {edge["source"], edge["target"]} <= ids
        assert edge["evidence"]
        assert all(e["path"] in inventory for e in edge["evidence"])


def test_contract_provenances_stay_distinct(tmp_path):
    declared = {"name": "Declared", "kind": "component", "members": ["README.md"], "evidence": ["README.md"]}
    proposed = {**declared, "name": "Proposed"}
    _, manifest, graph = build(tmp_path, {
        "package.json": '{"name":"Build"}', "README.md": "# Design\n",
        "codebase-modules.json": json.dumps({"schema": modules.DECLARED_SCHEMA, "modules": [declared]}),
    }, ledger=modules.validate_modules([proposed], source="test"))
    assert {m["name"]: (m["provenance"], m["status"]) for m in graph["modules"]} == {
        "Build": ("build", "confirmed"), "Declared": ("declared", "confirmed"), "Proposed": ("proposed", "inferred")}
    with open_snapshot(manifest) as store:
        assert modules.derive(store, ledger=modules.validate_modules([proposed], source="test")) == graph


def test_contract_directory_and_source_do_not_declare_module(tmp_path):
    """No folder becomes a module by its name or its README: code outside every build unit is the one implicit
    `source-tree` at the root (pipeline spec of 15 November 2026, section 1, «Scansione»)."""
    _, _, graph = build(tmp_path, {"feature/logic.py": "def run():\n    return 1\n", "README.md": "# A component\n"})
    [tree] = graph["modules"]
    assert (tree["provenance"], tree["kind"], tree["nature"], tree["named"]) == ("virtual", "source-tree", "virtual", False)
    assert [m["path"] for m in tree["members"]] == ["."]
    assert graph["edges"] == []


def test_contract_unknown_member_is_an_explicit_gap(tmp_path):
    proposal = {"name": "Unknown", "kind": "component", "members": ["missing.py"], "evidence": ["README.md"]}
    _, _, graph = build(tmp_path, {"README.md": "# Project\n"},
                        ledger=modules.validate_modules([proposal], source="test"))
    record, = graph["modules"]
    assert record["provenance"] == "proposed" and record["status"] == "incomplete"
    assert record["members"][0]["resolved"] is False
    assert record["gaps"] == [{"kind": "member_missing", "detail": "missing.py: absent from the tree"}]


@pytest.mark.parametrize("name,text", [("package.json", "{"), ("pyproject.toml", "[project"), ("pom.xml", "<project>")])
def test_contract_unreadable_manifest_is_a_gap(tmp_path, name, text):
    _, _, graph = build(tmp_path, {name: text})
    assert graph["modules"] == []
    gap, = graph["gaps"]
    assert gap["kind"] == "manifest_unreadable" and gap["path"] == name and gap["detail"]


def test_contract_missing_workspace_path_is_a_gap(tmp_path):
    _, _, graph = build(tmp_path, {"package.json": '{"name":"hub","workspaces":["absent"]}'})
    assert [m["name"] for m in graph["modules"]] == ["hub"]
    assert graph["gaps"] == [{"kind": "member_missing", "path": "package.json",
                               "detail": "workspace member absent: absent from the tree"}]


def test_contract_stale_manifest_is_rejected(tmp_path):
    project, manifest, _ = build(tmp_path, {"package.json": '{"name":"before"}'})
    (project / "package.json").write_text('{"name":"after"}', encoding="utf-8")
    with open_snapshot(manifest) as store, pytest.raises(modules.StaleSource, match="source changed"):
        modules.derive(store, ledger=[])


def test_contract_setup_py_is_read_without_execution(tmp_path):
    project, _, graph = build(tmp_path, {"setup.py": "from pathlib import Path\n"
        "Path(__file__).with_name('executed.txt').write_text('executed')\n"
        "from setuptools import setup\nsetup(name='static-name')\n"})
    assert [m["name"] for m in graph["modules"]] == ["static-name"]
    assert not (project / "executed.txt").exists()


def test_contract_a_unit_says_whether_a_file_names_it(tmp_path):
    _, _, graph = build(tmp_path, {"Gemfile": 'gem "rails"\n', "web/package.json": '{"name":"web"}'})
    assert {m["name"]: m["named"] for m in graph["modules"]} == {"proj": False, "web": True}


def test_gradle_include_is_not_include_group(tmp_path):
    _, _, graph = build(tmp_path, {
        "settings.gradle.kts": 'pluginManagement { repositories { google { content { includeGroup("com.android") } } } }\n'
                               'include(":lib")\n',
        "lib/build.gradle.kts": ""})
    assert relations(graph, "contains") == [["proj", "lib"]]
    assert graph["gaps"] == []


def test_regression_ambiguous_dependency_is_a_gap(tmp_path):
    _, _, graph = build(tmp_path, {"package.json": '{"name":"app","dependencies":{"core":"1"}}',
        "left/package.json": '{"name":"core"}', "right/package.json": '{"name":"core"}'})
    app = next(m for m in graph["modules"] if m["name"] == "app")
    assert relations(graph, "declares") == []
    assert any(g["kind"] == "dependency_ambiguous" and "core" in g["detail"] for g in app["gaps"])


def test_path_dependency_without_a_unit_stays_a_declared_dependency(tmp_path):
    _, _, graph = build(tmp_path, {
        "pyproject.toml": '[project]\nname="app"\ndependencies=["proto-py","httpx"]\n'
                          '[tool.uv.sources]\nproto-py = { path = "libs/proto-py" }\n'})
    app, = graph["modules"]
    assert app["external"] == ["httpx", "proto-py"]
    assert app["gaps"] == [{"kind": "dependency_unresolved",
                            "detail": "proto-py -> libs/proto-py: no build unit there"}]


def test_only_the_perimeter_leaves_a_manifest_unread(tmp_path):
    """`tree_scope.DEPENDENCY_DIRS` keeps `node_modules/` out of the snapshot; a folder with the word in its name is
    the project's own, and its manifest is read."""
    _, _, graph = build(tmp_path, {"tools/node_modules-audit/project.json": '{"name":"audit"}',
                                   "node_modules/dep/project.json": '{"name":"dep"}'})
    assert [(m["name"], m["kind"]) for m in graph["modules"] if m["provenance"] == "build"] == [("audit", "nx-project")]


def test_colocated_builds_do_not_claim_exclusive_import_ownership(tmp_path):
    files = {"package.json": '{"name":"web"}',
             "pyproject.toml": '[project]\nname="api"\n',
             "main.py": "from lib import run\n",
             "lib/pyproject.toml": '[project]\nname="library"\n',
             "lib/__init__.py": "def run():\n    return 1\n"}
    _, _, graph = build(tmp_path, files)
    assert relations(graph, "imports") == []
    assert any(g["kind"] == "ownership_ambiguous" and g["path"] == "." for g in graph["gaps"])


def test_nx_project_file_beside_package_json_is_one_unit(tmp_path):
    _, _, graph = build(tmp_path, {
        "libs/a/package.json": '{"name":"@acme/a"}', "libs/a/project.json": '{"name":"a"}',
        "libs/a/index.ts": 'import { b } from "../b/index";\nexport const a = b;\n',
        "libs/b/package.json": '{"name":"@acme/b"}', "libs/b/index.ts": "export const b = 1;\n"})
    assert sorted(m["kind"] for m in graph["modules"]) == ["npm-package", "npm-package+nx-project"]
    assert relations(graph, "imports") == [["@acme/a", "@acme/b"]]
    assert graph["gaps"] == []


def test_colocated_builds_remain_available_as_review_scope(tmp_path):
    proposal = {"name": "Feature", "kind": "component", "members": ["README.md"], "evidence": ["README.md"]}
    _, _, graph = build(tmp_path, {"package.json": '{"name":"web"}',
        "pyproject.toml": '[project]\nname="api"\n', "README.md": "# Feature\n"},
        ledger=modules.validate_modules([proposal], source="test"))
    result = modules.query(graph, "Feature", state="fresh")
    assert {r["name"] for r in result["candidates"][0]["read_scope"] if r["relation"] == "owned_by"} == {"api", "web"}


@pytest.mark.parametrize("root_use", [".", "./", None], ids=["dot", "dot-slash", "not-included"])
def test_go_root_workspace_membership_is_explicit(tmp_path, root_use):
    members = f" {root_use}\n ./lib\n" if root_use else " ./lib\n"
    _, _, graph = build(tmp_path, {
        "go.work": f"go 1.22\nuse (\n{members})\n",
        "go.mod": "module example/app\nrequire (\n example/core v1.0.0\n)\n",
        "lib/go.mod": "module example/core\n",
    })
    app = next(m for m in graph["modules"] if m["name"] == "example/app")
    assert relations(graph, "declares") == ([["example/app", "example/core"]] if root_use else [])
    assert app["external"] == ([] if root_use else ["example/core"])
    assert not any(e["source"] == e["target"] for e in graph["edges"])


def test_go_require_block_accepts_tab_whitespace(tmp_path):
    _, _, graph = build(tmp_path, {
        "go.mod": "module example/app\nrequire\t(\n example/core v1.0.0\n)\n",
    })
    app, = graph["modules"]
    assert app["external"] == ["example/core"]


def test_maven_dependency_uses_declared_project_group(tmp_path):
    _, _, graph = build(tmp_path, {
        "pom.xml": "<project><groupId>org.example</groupId><artifactId>app</artifactId>"
                   "<modules><module>core</module></modules><dependencies><dependency>"
                   "<groupId>${project.groupId}</groupId><artifactId>core</artifactId>"
                   "</dependency></dependencies></project>",
        "core/pom.xml": "<project><groupId>org.example</groupId><artifactId>core</artifactId></project>",
    })
    app = next(m for m in graph["modules"] if m["name"] == "app")
    assert relations(graph, "declares") == [["app", "core"]]
    assert app["external"] == []


def test_maven_profiles_are_a_declared_gap(tmp_path):
    _, _, graph = build(tmp_path, REGRESSIONS["maven_inactive_profile"]["files"])
    assert [g for g in graph["gaps"] if g["kind"] == "profiles_not_evaluated"] == [{
        "kind": "profiles_not_evaluated", "path": "pom.xml",
        "detail": "Only unconditional Maven modules and dependencies are read; profiles are not evaluated"}]


def test_package_name_and_directory_alias_are_one_dependency_target(tmp_path):
    _, _, graph = build(tmp_path, {
        "package.json": '{"name":"app","dependencies":{"@acme/data":"workspace:*"},"workspaces":["acme-data"]}',
        "acme-data/package.json": '{"name":"@acme/data"}',
    })
    app = next(m for m in graph["modules"] if m["name"] == "app")
    assert relations(graph, "declares") == [["app", "@acme/data"]]
    assert app["external"] == []
    assert app["gaps"] == []


def test_workspace_registration_cites_its_declaring_manifest(tmp_path):
    _, _, graph = build(tmp_path, {
        "package.json": '{"name":"hub"}',
        "pnpm-workspace.yaml": "packages:\n  - 'libs/*'\n",
        "libs/core/package.json": '{"name":"core"}',
    })
    assert relations(graph, "contains") == [["hub", "core"]]
    registration, = [e for e in graph["edges"] if e["kind"] == "contains"]
    assert registration["evidence"] == [{"path": "pnpm-workspace.yaml", "line": 2}]
