"""A Python file Daodan's interpreter rejects is read by the Python its project states (languages/python_newer.py):
uv provides it, it parses the source and runs none of the project, and the snapshot says which interpreter parsed
it; without one the file stays a parse error that names the Python stated.

    python tests/modal_pytest.py tests/test_codebase_map_python_newer.py -q
"""
from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "daodan/core"))

import engine_tools  # noqa: E402
import snapshot  # noqa: E402
from languages import python_newer  # noqa: E402
from snapshot_store import open_snapshot  # noqa: E402

# PEP 758 (3.14): `except` names its types without parentheses, as fastapi's backend/app/api/deps.py does.
NEWER = pytest.mark.skipif(sys.version_info >= (3, 14), reason="the fixture's syntax is not newer than this Python")
DEPS = ("def check(value):\n    try:\n        return int(value)\n    except ValueError, TypeError:\n"
        "        return helper(value)\n\n\ndef helper(value):\n    return value\n")


def _written(root: Path, files: dict) -> Path:
    for rel, text in files.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(text, encoding="utf-8")
    return root


def test_the_python_a_folder_states_is_its_nearest_version_file_else_its_nearest_requires_python(tmp_path):
    """As uv reads it (`dynamic.python.stated_python`): a version file at or above the folder before any
    requires-python, the first version it lists; up to the snapshot's root."""
    _written(tmp_path, {".python-version": "# pinned\n3.14\n", "lib/.python-versions": "3.13\n3.14\n",
                        "svc/pyproject.toml": '[project]\nname = "svc"\nrequires-python = ">=3.15"\n',
                        "lib/pyproject.toml": '[project]\nname = "lib"\nrequires-python = ">=3.10"\n'})
    assert python_newer.stated(tmp_path, "svc/app") == {"version": "3.14", "declared_in": ".python-version"}
    assert python_newer.stated(tmp_path, "lib") == {"version": "3.13", "declared_in": "lib/.python-versions"}
    (tmp_path / ".python-version").unlink()
    assert python_newer.stated(tmp_path, "svc/app") == {"version": ">=3.15", "declared_in": "svc/pyproject.toml"}
    assert python_newer.stated(tmp_path, "tools") is None


def test_only_a_python_newer_than_daodan_s_reads_again_what_daodan_s_rejects():
    """An older grammar accepts nothing a newer one rejects: a statement Daodan's interpreter meets, or one older
    than it, keeps Daodan's reading."""
    own, later = f"3.{sys.version_info.minor}", f"3.{sys.version_info.minor + 1}"
    assert python_newer.newer(later) and python_newer.newer(f">={later}") and python_newer.newer(f"~={later}.1")
    assert not python_newer.newer(own) and not python_newer.newer(">=3.10") and not python_newer.newer("3.11")
    assert not python_newer.newer("pypy@3.10")


def test_a_tree_rebuilt_from_its_dump_is_the_same_tree_and_a_node_daodan_does_not_know_is_walked():
    """The stated interpreter writes its tree (`dump`), Daodan's `ast` rebuilds it (`tree`): every node, field,
    position and constant. A node type Daodan's `ast` lacks (3.14's `TemplateStr`) keeps its base class and its
    fields: the names in it are read."""
    source = ('import os\n@dec(1)\nclass A(B):\n    x: int = 0b1\n'
              '    def f(self, *a, k=..., **kw) -> "A":\n        return f"{a!r:>{k}}" + b"\\x00" + 1j\n')
    tree = ast.parse(source)
    rebuilt = python_newer.tree(json.loads(json.dumps(python_newer.dump(tree))))
    assert ast.dump(rebuilt, include_attributes=True) == ast.dump(tree, include_attributes=True)
    at = {"lineno": 1, "col_offset": 3, "end_lineno": 1, "end_col_offset": 4}
    name = {"_": "Name", "^": "expr", "id": "x", "ctx": {"_": "Load", "^": "expr_context"}, **at}
    template = {"_": "TemplateStr", "^": "expr", "values": [
        {"_": "Interpolation", "^": "expr", "value": name, "str": "x", "conversion": -1, "format_spec": None, **at}],
        **at}
    node = python_newer.tree({"_": "Expr", "^": "stmt", "value": template, **at})
    assert isinstance(node.value, ast.expr) and type(node.value).__name__ == "TemplateStr"
    assert [item.id for item in ast.walk(node) if isinstance(item, ast.Name)] == ["x"]


@NEWER
def test_without_an_interpreter_for_the_python_its_project_states_a_file_stays_a_parse_error_naming_it(
        tmp_path, monkeypatch):
    project = _written(tmp_path / "project", {".python-version": "3.14\n", "app/deps.py": DEPS})

    def refused(root, names, python=None):
        raise subprocess.SubprocessError("uv could not provide Python 3.14: error: No download found for request")

    monkeypatch.setattr(engine_tools, "python_environment", refused)
    store = tmp_path / "snapshot.sqlite"
    snapshot.read_project(project, store)
    with open_snapshot(store) as opened:
        header = opened.get_file("app/deps.py")
    assert header["status"] == "parse-error"
    [note] = [note for note in header["parser_notes"] if note.startswith("syntax error:")]
    assert "the project states Python 3.14 (.python-version)" in note and "No download found" in note, note


@NEWER
def test_a_file_is_parsed_by_the_python_its_project_states_and_none_of_the_project_runs(tmp_path):
    """AGENTS.md: parsing is not running. uv provides the Python the project states (on Modal, real uv), which
    parses the file isolated and without `site`, reading the source on its standard input in a folder outside the
    project: the file's own code, a build backend and modules named as the standard library's in the project
    each leave a mark when run, and none appears. The file's definitions and calls are read."""
    marks = tmp_path / "marks"
    marks.mkdir()

    def marking(what: str) -> str:
        return f"open({str(marks / what)!r}, 'w').close()\n"

    project = _written(tmp_path / "project", {
        ".python-version": "3.14\n", "app/deps.py": marking("deps") + DEPS,
        "pyproject.toml": '[project]\nname = "app"\nrequires-python = ">=3.14"\n[build-system]\nrequires = []\n'
                          'build-backend = "backend"\nbackend-path = ["."]\n',
        **{rel: marking(rel.replace("/", "-")) for rel in ("backend.py", "ast.py", "json.py", "platform.py",
                                                            "warnings.py", "sitecustomize.py", "app/json.py")}})
    store = tmp_path / "snapshot.sqlite"
    snapshot.read_project(project, store)
    with open_snapshot(store) as opened:
        header = opened.get_file("app/deps.py")
        calls = [row[0] for row in opened.connection.execute(
            "SELECT last_name FROM sem_references WHERE file = ? AND kind = 'call'", ("app/deps.py",))]
    assert header["status"] == "parsed", header["parser_notes"]
    assert [note for note in header["parser_notes"] if note.startswith("parsed by Python 3.14")], header["parser_notes"]
    assert {"check", "helper"} <= set(header["symbols"]) and {"int", "helper"} <= set(calls), (header, calls)
    assert sorted(path.name for path in marks.iterdir()) == []
    # The control: run, the file does leave its mark.
    environment = engine_tools.python_environment(project, [], "3.14")
    subprocess.run([str(environment / "bin/python"), str(project / "app/deps.py")], check=True)
    assert sorted(path.name for path in marks.iterdir()) == ["deps"]
