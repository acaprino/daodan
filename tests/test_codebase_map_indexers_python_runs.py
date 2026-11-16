"""The Python analyzer's runs when a project sits inside a checkout that holds more Python code."""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "plugins/codebase-map/skills/map/scripts"))

from indexers import python  # noqa: E402


def test_a_project_folded_into_the_checkout_run_keeps_its_folder_as_the_root_of_its_imports(tmp_path):
    """The files of a Python project import each other from its folder; the code outside it sees the declared
    source roots only: a module found by name in a project's folder from outside would be a guess."""
    (tmp_path / "pkg" / "src").mkdir(parents=True)
    target = tmp_path / "pyrightconfig.json.out"
    config = python._pyright_config(tmp_path, target, ["pkg/src"], ["pkg", "tools/lint"])
    assert config == json.loads(target.read_text(encoding="utf-8")) == {"executionEnvironments": [
        {"root": "pkg/src"}, {"root": "pkg", "extraPaths": ["pkg/src"]}, {"root": "tools/lint", "extraPaths": ["pkg/src"]},
        {"root": ".", "extraPaths": ["pkg/src"]}]}


# What scip-python names wrongly or leaves unnamed, read by the adapter (`classify`, `hops`, `unanswered`) from the
# index and what its run left beside it: the environment, the Pyright configuration, the checker's pass.

import code_graph  # noqa: E402
from indexers import python_unbound  # noqa: E402
from test_codebase_map_code_graph import Snapshot, document, occurrence  # noqa: E402

APP, STDLIB = "scip-python python app _ ", "scip-python python python-stdlib 3.11 "


def run(tmp_path, files: dict, documents, packages=(), config=None, unbound=()) -> code_graph.Index:
    """An index as a run leaves it, `scip-python-0.scip`, its sources in `files`, with beside it the environment
    it was told, the Pyright configuration it read and the checker's lines."""
    for rel, text in files.items():
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text(text, encoding="utf-8")
    (tmp_path / "scip-python-0.scip").write_bytes(b"".join(documents))
    (tmp_path / "scip-python-environment-0.json").write_text(json.dumps(list(packages)), encoding="utf-8")
    if config:
        (tmp_path / "pyrightconfig-0.json").write_text(json.dumps(config), encoding="utf-8")
    (tmp_path / "scip-python-0.unbound.jsonl").write_text("".join(json.dumps(row) + "\n" for row in unbound),
                                                          encoding="utf-8")
    index = code_graph.Index(tmp_path)
    index.load(tmp_path / "scip-python-0.scip")
    return index


def ends(index, key, hops=None):
    traversal = code_graph.Traversal(index, Snapshot({}), hops or {}, classify=python.classify(index),
                                     unanswered=python.unanswered(index))
    return [(end.cls, end.detail, end.chain) for end in traversal.ends(key)]


def test_a_name_a_distribution_re_exports_is_that_distributions_and_a_module_attribute_the_interpreters(tmp_path):
    """real-app-full-stack-fastapi: `sa.UUID` (`import sqlalchemy as sa`), `typer.Typer`, `pytest.fail` reach a
    name the package's `__init__` re-exports; scip-python 0.6.8 names it by the module that declares it and labels it
    with the project's package, which defines it nowhere (`undefined-project-symbol`). That module is a file of an
    installed distribution, the one the run's environment lists: the symbol is that distribution's. `__name__`,
    `__file__`, `__package__`, `__doc__` get the module's namespace alone: attributes the interpreter sets on every
    module. A name of the project's own modules stays undefined."""
    uuid, own, typed = APP + "`sqlalchemy.sql.sqltypes`/UUID#", APP + "`app.gone`/f().", APP + "`app.main`/"
    index = run(tmp_path, {"app/main.py": "import sqlalchemy as sa\nsa.UUID\n__name__\n"}, [document("app/main.py", [
        occurrence(1, 0, 6, APP + "`app.main`/__init__:", True), occurrence(2, 3, 7, uuid), occurrence(3, 0, 8, typed),
        occurrence(3, 0, 1, own), occurrence(1, 7, 17, STDLIB + "builtins/str#")])],
        packages=[{"name": "SQLAlchemy", "version": "2.0.51", "files": ["sqlalchemy/__init__.py",
                                                                         "sqlalchemy/sql/sqltypes.py"]}])
    assert ends(index, uuid) == [("external", "python SQLAlchemy@2.0.51", ())]
    assert ends(index, typed) == [("external", "python python-stdlib@3.11", ())]
    assert ends(index, own) == [("dead-end", "undefined-project-symbol", ())]


def test_a_module_imported_through_a_source_root_is_the_one_defined_under_it(tmp_path):
    """mix-real-python-semver: its package lies in `src`, which the run tells Pyright as a root; scip-python names
    the module by its path where it is defined (`src.semver`) and by its import where it is imported (`semver`)."""
    defined, imported = APP + "`src.semver`/__init__:", APP + "semver/__init__:"
    index = run(tmp_path, {"src/semver/__init__.py": "", "tests/conftest.py": "import semver\n"}, [
        document("src/semver/__init__.py", [occurrence(1, 0, 0, defined, True)]),
        document("tests/conftest.py", [occurrence(1, 7, 13, imported)])],
        config={"executionEnvironments": [{"root": "src"}, {"root": ".", "extraPaths": ["src"]}]})
    hops = python.hops(index)
    assert hops[imported] == [(defined, "source-root")]
    assert [cls for cls, _detail, chain in ends(index, imported, hops)] == ["project-value"]


def test_a_member_the_index_names_nowhere_carries_what_the_checker_says_of_it(tmp_path):
    """Where scip-python has no occurrence at a member (`no-occurrence`) or gives it a local it defines nowhere
    (`dangling-local`), the checker's pass says why: a member it types Any or Unknown, which only execution knows,
    or one it binds, which the index leaves unnamed."""
    local = "app.py#local 3"
    index = run(tmp_path, {"app.py": "r.json()\nsys.exit(0)\n"}, [document("app.py", [occurrence(2, 4, 8, "local 3")])],
                unbound=[["app.py", 1, 2, "Unknown", ""], ["app.py", 2, 4, "bound", "function exit"]])
    assert python.unanswered(index)(("app.py", 1, 2)) == python.UNBOUND_CAUSES["Unknown"]
    assert python.unanswered(index)(("app.py", 1, 0)) is None
    [(cls, detail, _chain)] = ends(index, local)
    assert cls == "dead-end" and detail == "the checker binds the function exit and scip-python names nothing there"


def test_the_checker_pass_reads_the_hover_at_each_member_s_name():
    assert python_unbound.members("import x\nx.y.z(1)\nf(a).b\n") == [(2, 2), (2, 4), (3, 5)]
    assert python_unbound.kind("```python\n(function) bump: Any\n```") == ("Any", "")
    assert python_unbound.kind("```python\n(variable) response: Unknown\n```") == ("Unknown", "")
    assert python_unbound.kind("```python\n(method) def assert_called_once() -> None\n```\n---\nassert...") == (
        "bound", "method assert_called_once")
    assert python_unbound.kind("```python\n(function) def exit(\n    status: int = None,\n    /\n) -> NoReturn\n```") \
        == ("bound", "function exit")
    assert python_unbound.kind("") is None and python_unbound.kind("class list(): ...") is None
