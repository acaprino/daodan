"""The Python analyzer's runs when a project sits inside a checkout that holds more Python code."""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "daodan/core"))

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


def test_a_type_after_the_first_of_a_python_3_14_except_clause_carries_why_the_index_names_nothing(tmp_path):
    """real-app-full-stack-fastapi, backend/app/api/deps.py:36: `except InvalidTokenError, ValidationError:` (PEP
    758, Python 3.14), which the snapshot reads with the Python the project states; scip-python's parser predates
    3.14 and gives the types after the first no occurrence. A parenthesized clause is any Python's."""
    source = ("try:\n    pass\nexcept InvalidTokenError, ValidationError:\n    pass\n"
              "try:\n    pass\nexcept (KeyError, ValueError):\n    pass\n")
    index = run(tmp_path, {"app.py": source}, [document("app.py", [occurrence(3, 7, 24, APP + "`app`/InvalidTokenError#")])])
    assert python.unanswered(index)(("app.py", 3, 26)) == python.NEWER_SYNTAX
    assert python.unanswered(index)(("app.py", 7, 18)) is None


def test_the_checker_pass_reads_the_hover_at_each_member_s_name():
    assert python_unbound.members("import x\nx.y.z(1)\nf(a).b\n") == [(2, 2), (2, 4), (3, 5)]
    assert python_unbound.kind("```python\n(function) bump: Any\n```") == ("Any", "")
    assert python_unbound.kind("```python\n(variable) response: Unknown\n```") == ("Unknown", "")
    assert python_unbound.kind("```python\n(method) def assert_called_once() -> None\n```\n---\nassert...") == (
        "bound", "method assert_called_once")
    assert python_unbound.kind("```python\n(function) def exit(\n    status: int = None,\n    /\n) -> NoReturn\n```") \
        == ("bound", "function exit")
    assert python_unbound.kind("") is None and python_unbound.kind("class list(): ...") is None


def test_a_name_an_annotation_reads_before_its_definition_is_the_module_s_one_definition(tmp_path):
    """real-app-full-stack-fastapi: `items: list[Item]` in `User`, `Item` defined below it. Python 3.14 evaluates an
    annotation when it is read (PEP 649), and scip-python 0.6.8, whose Pyright predates 3.14, gives `Item` a local
    it defines nowhere: the name is the module's one top-level definition of it. A name outside an annotation is
    evaluated where it is written and keeps no hop."""
    user, item = APP + "`app.models`/User#", APP + "`app.models`/Item#"
    text = "class User:\n    items: list[Item] = []\nalias = Item\n\n\nclass Item:\n    pass\n"
    index = run(tmp_path, {"app/models.py": text}, [document("app/models.py", [
        occurrence(1, 6, 10, user, True), occurrence(2, 4, 9, user + "items.", True),
        occurrence(2, 11, 15, STDLIB + "builtins/list#"), occurrence(2, 16, 20, "local 1"),
        occurrence(3, 0, 5, APP + "`app.models`/alias.", True), occurrence(3, 8, 12, "local 2"),
        occurrence(6, 6, 10, item, True)])])
    hops = python.hops(index)
    assert hops["app/models.py#local 1"] == [(item, "deferred-annotation")]
    assert "app/models.py#local 2" not in hops
    assert [cls for cls, _detail, _chain in ends(index, "app/models.py#local 1", hops)] == ["project-value"]


def test_each_run_takes_the_python_its_folder_states_first_as_uv_reads_it():
    """real-app-full-stack-fastapi: the workspace's `.python-version` states 3.14 before its member's requires-python;
    without it, the member's requires-python. The image a Dockerfile names is not what uv reads."""
    record = {"units": [{"kind": "python-project", "root": "backend", "manifest": "backend/pyproject.toml",
                         "sources": [], "name": "app"}],
              "workspace": [{"tool": "uv", "root": "."}],
              "toolchains": [{"tool": "python", "version": "3.14", "declared_in": "backend/Dockerfile"},
                             {"tool": "python", "version": ">=3.14,<4.0", "declared_in": "backend/pyproject.toml"},
                             {"tool": "python", "version": "3.14", "declared_in": ".python-version"}]}
    [unit] = python.structure(record)["units"]
    assert unit["root"] == "" and unit["python"] == {"version": "3.14", "declared_in": ".python-version"}
    record["toolchains"].pop()
    [unit] = python.structure(record)["units"]
    assert unit["python"] == {"version": ">=3.14,<4.0", "declared_in": "backend/pyproject.toml"}
    record["toolchains"] = []
    assert "python" not in python.structure(record)["units"][0]


def _wheel(path: Path, files: dict) -> None:
    """A wheel holding `files`, with the metadata and RECORD an installer reads."""
    import base64
    import hashlib
    import zipfile
    name, version = path.name.split("-")[:2]
    info = f"{name}-{version}.dist-info"
    files = {**files, f"{info}/METADATA": f"Metadata-Version: 2.1\nName: {name}\nVersion: {version}\n",
             f"{info}/WHEEL": "Wheel-Version: 1.0\nGenerator: test\nRoot-Is-Purelib: true\nTag: py3-none-any\n"}
    record = [f"{rel},sha256={base64.urlsafe_b64encode(hashlib.sha256(text.encode()).digest()).rstrip(b'=').decode()},"
              f"{len(text.encode())}" for rel, text in files.items()]
    with zipfile.ZipFile(path, "w") as archive:
        for rel, text in {**files, f"{info}/RECORD": "\n".join([*record, f"{info}/RECORD,,"]) + "\n"}.items():
            archive.writestr(rel, text)


@pytest.mark.skipif(not os.environ.get("MODAL_TASK_ID"), reason="a real proof on Modal (tests/modal_pytest.py)")
def test_the_analyzer_on_the_host_reads_the_project_and_its_environment_and_runs_none_of_them(tmp_path, monkeypatch):
    """AGENTS.md: the project's code runs only in the container. On the host uv builds the environment from wheels
    and starts its interpreter at each install, scip-python's and the checker's Pyright start it to ask its paths,
    the checker parses with it: a project whose files, and whose environment (a wheel's `.pth` import line and
    `sitecustomize`, a package with only a source distribution), each leave a mark when run is read, its package
    resolved, and no mark appears; the package without a wheel is a gap naming it. uv reads no configuration file,
    the project's or the user's (both unreadable here). Real uv, Node, scip-python and Pyright (on Modal)."""
    import subprocess
    import tarfile
    marks = tmp_path / "marks"
    marks.mkdir()

    def marking(what: str) -> str:
        return f"open({str(marks / what)!r}, 'w').close()\n"

    wheels = tmp_path / "wheels"
    wheels.mkdir()
    _wheel(wheels / "daodanmark-1.0-py3-none-any.whl", {
        "daodanmark/__init__.py": "VALUE = 1\n", "daodanmark_hook.py": marking("pth"),
        "daodanmark.pth": "import daodanmark_hook\n", "sitecustomize.py": marking("sitecustomize")})
    source = tmp_path / "daodansdist-1.0"  # a source distribution alone: building it runs its setup.py
    source.mkdir()
    (source / "PKG-INFO").write_text("Metadata-Version: 2.1\nName: daodansdist\nVersion: 1.0\n", encoding="utf-8")
    (source / "setup.py").write_text(marking("sdist-setup.py") + "from setuptools import setup\nsetup()\n",
                                     encoding="utf-8")
    with tarfile.open(wheels / "daodansdist-1.0.tar.gz", "w:gz") as archive:
        archive.add(source, arcname=source.name)
    unreadable = "this = is not [ toml\n"
    (tmp_path / "config/uv").mkdir(parents=True)
    (tmp_path / "config/uv/uv.toml").write_text(unreadable, encoding="utf-8")  # the user's
    project = tmp_path / "project"
    project.mkdir()
    (project / "uv.toml").write_text(unreadable, encoding="utf-8")
    for name in ("setup.py", "conftest.py", "json.py", "sitecustomize.py", "backend.py"):
        (project / name).write_text(marking(name), encoding="utf-8")
    (project / "pyproject.toml").write_text(
        '[build-system]\nrequires = []\nbuild-backend = "backend"\nbackend-path = ["."]\n', encoding="utf-8")
    # The others have no wheel: installed one at a time, uv starts the interpreter again after the first.
    (project / "requirements.txt").write_text("daodanmark\ndaodansdist\nzz-daodan-without-wheel\n", encoding="utf-8")
    (project / "app.py").write_text("import json\nimport daodanmark\nprint(daodanmark.VALUE, json.dumps(1))\n",
                                    encoding="utf-8")
    for name, value in (("UV_FIND_LINKS", str(wheels)), ("UV_NO_INDEX", "1"), ("UV_NO_CACHE", "1"),
                        ("XDG_CONFIG_HOME", str(tmp_path / "config"))):
        monkeypatch.setenv(name, value)
    result = python.index(project, tmp_path / "work",
                          units=[{"root": "", "manifests": ["pyproject.toml", "requirements.txt"]}])
    [run] = result["runs"]
    assert run["index"] and run["packages"] == {"daodanmark": "1.0"}, result
    failed = {gap["package"]: gap["detail"] for gap in result.get("gaps", ()) if gap.get("package")}
    assert set(failed) == {"daodansdist", "zz-daodan-without-wheel"} and "wheel" in failed["daodansdist"], result
    index = code_graph.Index(project)
    index.load(Path(run["index"]))
    assert any(" daodanmark 1.0 " in o.key for o in index.documents["app.py"])  # read from the environment
    assert ["app.py", 3, 17, "bound"] in [row[:4] for row in python._beside(Path(run["index"]), "unbound")]
    assert sorted(path.name for path in marks.iterdir()) == []
    # The control: run as code, a marking file does leave its mark.
    environment = Path(run["environment"])
    subprocess.run([str(environment / "bin/python"), "-c", "import daodanmark_hook"], check=True)
    subprocess.run([str(environment / "bin/python"), str(project / "setup.py")], check=True)
    subprocess.run([str(environment / "bin/python"), "-c", f"exec(open({str(source / 'setup.py')!r}).readline())"],
                   check=True)
    assert sorted(path.name for path in marks.iterdir()) == ["pth", "sdist-setup.py", "setup.py"]


@pytest.mark.skipif(not os.environ.get("MODAL_TASK_ID"), reason="a real proof on Modal (tests/modal_pytest.py)")
@pytest.mark.parametrize(("config", "site"), [("pyrightconfig.json", True), ("pyrightconfig.json", False),
                                              ("pyproject.toml", True)])
def test_a_venv_the_project_s_pyright_configuration_names_is_read_and_never_started(tmp_path, config, site):
    """AGENTS.md: the project's code runs only in the container. Its Pyright configuration may name a venv in the
    project (`venvPath`, `venv`), whose interpreter is the project's: scip-python and the checker read that venv's
    packages as files, where it holds any, else ask Daodan's interpreter, and never start the venv's. Real Node,
    scip-python and Pyright (on Modal)."""
    import subprocess
    marks, project = tmp_path / "marks", tmp_path / "project"
    marks.mkdir()
    (project / "venv/bin").mkdir(parents=True)
    (project / "venv/pyvenv.cfg").write_text("home = /usr/local/bin\nversion_info = 3.13.3\n", encoding="utf-8")
    for name in ("python", "python3", f"python3.{sys.version_info.minor}"):
        (project / "venv/bin" / name).write_text(f"#!/bin/sh\ntouch {marks / name}\nexec {sys.executable} \"$@\"\n",
                                                 encoding="utf-8")
        (project / "venv/bin" / name).chmod(0o755)
    if site:
        (project / f"venv/lib/python3.{sys.version_info.minor}/site-packages/vpkg").mkdir(parents=True)
        (project / f"venv/lib/python3.{sys.version_info.minor}/site-packages/vpkg/__init__.py").write_text(
            "VALUE = 1\n", encoding="utf-8")
    (project / config).write_text('{"venvPath": ".", "venv": "venv"}' if config == "pyrightconfig.json" else
                                  '[project]\nname = "p"\n[tool.pyright]\nvenvPath = "."\nvenv = "venv"\n',
                                  encoding="utf-8")
    (project / "app.py").write_text("import vpkg\nprint(vpkg.VALUE)\n", encoding="utf-8")
    environment = tmp_path / "environment"
    import engine_tools
    subprocess.run([str(engine_tools.uv_binary()), "venv", "-q", str(environment), "--python", sys.executable],
                   check=True)
    result = python.index(project, tmp_path / "work", environment=environment, units=[{"root": ""}])
    assert len(result["runs"]) == 1, (result.get("reason"), result.get("install"))
    [run] = result["runs"]
    rows = {tuple(row[:3]): row[3] for row in python._beside(Path(run["index"]), "unbound")}
    assert rows[("app.py", 2, 11)] == ("bound" if site else "Unknown"), rows  # the venv's files, else Daodan's
    assert sorted(path.name for path in marks.iterdir()) == []
    # The control: started, the venv's interpreter does leave its mark.
    subprocess.run([str(project / "venv/bin/python"), "-c", "pass"], check=True)
    assert sorted(path.name for path in marks.iterdir()) == ["python"]
