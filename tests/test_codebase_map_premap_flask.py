"""The routes of a Flask application, `premap/flask_app.py`: the rows and the gaps `read` makes from what Daodan's script
(`premap/flask_routes.py`, run in the container by the project's own Python) prints.

WRITTEN WITHOUT A CONTAINER TO TRY IT IN; NOT RUN. No answer here was recorded from a real run: the script's output is built
inline by `printed`, in the layout the script's source says it prints ("expected shape, read from Flask 3.1.3's source, not
recorded"); the file names and qualified names are the ones the fixture (`benchmarks/flask-routes/fixture/`) has, and what Flask
and the interpreter would really print for them is what `benchmarks/flask-routes/modal_probe.py` measures. The test of a recorded
answer is `xfail(strict=True)` until the probe has written one: when it has, the test must pass and the mark must go.
Two things are assumed, not measured, and are told where they are used: that the snapshot's record of a decorated function sits
on its `def` or on its decorator, and that the snapshot names a method `Class.method` as Python's `__qualname__` does.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from test_codebase_map_premap_container_runner import container, container_runner, manifest_of, premap, recorder
from unittest.mock import patch

from premap import flask_app  # not in `premap.SOURCES` yet: the source waits for the probe's measure

BENCHMARK = Path(__file__).resolve().parents[1] / "benchmarks/flask-routes"
FIXTURE = BENCHMARK / "fixture"
RECORDED = Path(__file__).parent / "fixtures/premap/flask/answers.json"
SOURCE = "flask@daodan/premap/v1"


def project(**changes) -> dict[str, str]:
    files = {path.relative_to(FIXTURE).as_posix(): path.read_text(encoding="utf-8")
             for path in FIXTURE.rglob("*") if path.is_file() and path.name not in ("uv.lock",) and "__pycache__" not in path.parts}
    files["requirements.txt"] = "flask==3.1.3\n"  # the pre-map's own packages (`requirements`) say the folder is Flask's
    files.update(changes)
    return {rel: text for rel, text in files.items() if text is not None}


def view(qualname, file, kind="function"):
    return {"kind": kind, "module": file.removesuffix(".py").replace("/", "."), "qualname": qualname, "file": file}


def rule(path, methods, handler, endpoint="x", host=None):
    return {"rule": path, "methods": methods, "endpoint": endpoint, "host": host, "handler": handler}


def printed(routes, **fields):
    """What the script prints on its last line: expected shape, read from the script's source, not recorded."""
    return {"returncode": 0, "stdout": "log of the project's module\n" + json.dumps({"called": True, "routes": routes}), "stderr": "",
            "root": "/work", **fields}


FIXTURE_ROUTES = [
    rule("/", ["GET"], view("index", "wsgi.py")),
    rule("/items", ["POST"], view("create_item", "wsgi.py")),
    rule("/admin/users/<int:user_id>", ["GET", "POST"], view("user", "app/blueprint.py")),
    rule("/admin/stats", ["GET"], view("stats", "app/blueprint.py")),
    rule("/page", ["GET"], view("Pages.show", "wsgi.py")),
    rule("/lambda", ["GET"], view("<lambda>", "wsgi.py")),
    # Flask's own `static` rule: its function is in the package of the environment, outside the project
    rule("/static/<path:filename>", ["GET"], view("App.send_static_file", "../../venvs/lib/python3.12/site-packages/flask/app.py")),
]


def read(tmp_path, files, answers=None):
    _, manifest = manifest_of(tmp_path, files)
    asked = []

    def run(commands):
        asked.extend(commands)
        return answers or [printed(FIXTURE_ROUTES)]
    record = premap.write(manifest, sources=(premap.requirements, flask_app), runner=run)
    return record, [g for g in record["gaps"] if g.get("source") == SOURCE], asked


def lines_of(files, file, needle):
    """The lines of `file` that hold `needle` (the `def` line): a decorated function's record is on it or on the decorator above."""
    return next(n for n, line in enumerate(files[file].split("\n"), 1) if needle in line)


def rows(record):
    return [r for r in record.get("framework_entries", []) if r["reader"] == "flask"]


def test_each_rule_and_method_is_a_row_on_the_function_the_view_is_with_the_rule_as_flask_writes_it(tmp_path):
    files = project()
    record, gaps, asked = read(tmp_path, files)
    bound = {(r["path"], r.get("method")): r for r in rows(record) if not r.get("gap")}
    assert sorted(bound) == [("/", "GET"), ("/admin/stats", "GET"), ("/admin/users/<int:user_id>", "GET"),
                             ("/admin/users/<int:user_id>", "POST"), ("/items", "POST"), ("/page", "GET")]
    for (path, _), row in bound.items():
        file, _, line = row["site"].rpartition(":")
        qualified = row["symbol"].split("::")[1]
        assert row["shape"] == "route" and row["kind"] == "rotta" and row["handler"] == qualified and row["sources"] == [SOURCE]
        assert row["symbol"] == f"{file}::{qualified}"
        name = qualified.split(".")[-1]
        # not measured: the record of a decorated function sits on its `def` or on the decorator above it
        assert int(line) in (lines_of(files, file, f"def {name}("), lines_of(files, file, f"def {name}(") - 1), (path, row["site"])
    assert bound[("/page", "GET")]["handler"] == "Pages.show"  # not measured: a method is `Class.method` in the snapshot
    assert [(c["cwd"], c["network"], c["env"]) for c in asked] == [(".", "none", {})]


def test_a_handler_the_snapshot_has_no_record_of_is_a_row_on_its_file_with_the_cause_and_not_a_guess_by_name(tmp_path):
    record, gaps, _ = read(tmp_path, project())
    [lam] = [r for r in rows(record) if r["path"] == "/lambda"]
    assert lam["site"] == "wsgi.py" and lam["symbol"] == "wsgi.py::<module>" and "<lambda>" in lam["gap"] and "handler" not in lam


def test_a_function_in_a_file_the_snapshot_does_not_hold_is_a_gap_with_the_rule_and_no_row(tmp_path):
    record, gaps, _ = read(tmp_path, project())
    assert [g["kind"] for g in gaps] == ["outside_snapshot"] and "/static/<path:filename>" in gaps[0]["detail"]
    assert not [r for r in rows(record) if r["path"].startswith("/static")]


def test_a_class_based_view_is_a_row_on_its_file_with_the_gap_for_the_method_it_does_not_read(tmp_path):
    answers = [printed([rule("/pages", ["GET", "POST"], view("Pages", "wsgi.py", kind="class"))])]
    record, gaps, _ = read(tmp_path, project(), answers)
    assert sorted((r["method"], "class-based view" in r["gap"]) for r in rows(record)) == [("GET", True), ("POST", True)]
    assert gaps == []


def test_a_rule_that_names_no_method_is_one_row_with_no_method(tmp_path):
    answers = [printed([rule("/", [], view("index", "wsgi.py"))])]
    record, _, _ = read(tmp_path, project(), answers)
    [row] = rows(record)
    assert "method" not in row and row["handler"] == "index"


def test_a_nested_function_is_found_by_the_name_the_snapshot_gives_it_without_the_locals_marker_of_python(tmp_path):
    files = project(**{"wsgi.py": "from flask import Flask\n\n\ndef make():\n    app = Flask(__name__)\n\n    @app.route('/')\n"
                                  "    def inner():\n        return 'x'\n\n    return app\n\n\napp = make()\n"})
    answers = [printed([rule("/", ["GET"], view("make.<locals>.inner", "wsgi.py"))])]
    record, gaps, _ = read(tmp_path, files, answers)
    [row] = rows(record)  # not measured: the snapshot's reader names a nested function `make.inner`
    assert row["handler"] == "make.inner" and not row.get("gap") and gaps == []


# ------------------------------------------------------------------- what fails

@pytest.mark.parametrize("answer, cause", [
    ({"returncode": 3, "stdout": "", "stderr": "NoAppException: Could not locate a Flask application.\n"}, "Could not locate a Flask application"),
    ({"returncode": 3, "stdout": "", "stderr": "ModuleNotFoundError: No module named 'flask_sqlalchemy'\n"}, "flask_sqlalchemy"),
    ({"returncode": 124, "stdout": "", "stderr": ""}, "did not end in 900 seconds"),
    ({"returncode": 137, "stdout": "", "stderr": ""}, "exit 137"),
    ({"returncode": 0, "stdout": "not json\n", "stderr": ""}, "printed no JSON"),
    ({"returncode": 0, "stdout": json.dumps({"called": True, "routes": [{"rule": 1}]}), "stderr": ""}, "printed no JSON"),
])
def test_an_application_that_does_not_load_or_a_script_that_fails_is_the_folder_s_gap_with_the_cause_and_no_row(tmp_path, answer, cause):
    record, gaps, _ = read(tmp_path, project(), [{**answer, "root": "/work"}])
    assert rows(record) == [] and [g["kind"] for g in gaps] == ["model_failed"] and cause in gaps[0]["detail"] and gaps[0]["path"] == "."


def test_an_application_with_no_rule_is_a_gap_and_no_row(tmp_path):
    record, gaps, _ = read(tmp_path, project(), [printed([])])
    assert rows(record) == [] and [g["kind"] for g in gaps] == ["model_partial"]


# ------------------------------------------------------------ what runs, and where

def test_only_a_folder_whose_manifest_declares_flask_runs_the_script_in_the_environment_restored_for_it(tmp_path):
    import preparation
    from snapshot_store import open_snapshot
    files = {"api/requirements.txt": "flask==3.1.3\n", "worker/requirements.txt": "celery==5.4.0\n",
             "docs/requirements/base.txt": "flask\n"}
    _, manifest = manifest_of(tmp_path, files)
    seen = []

    def run(commands):
        seen.extend(commands)
        return [printed([]) for _ in commands]
    premap.write(manifest, sources=(premap.requirements, flask_app), runner=run)
    assert [c["cwd"] for c in seen] == ["api"]  # a file that is not a manifest the restore starts from (`requirements/base.txt`) names no folder
    assert seen[0]["argv"] == ["timeout", "--kill-after=10", "900", f"{preparation.VENVS}/api/bin/python", "-I", f"{preparation.T}/flask_routes.py"]
    assert seen[0]["tool"] == "flask" and seen[0]["network"] == "none"
    _, manifest = manifest_of(tmp_path / "plain", {"requirements.txt": "django==6.1.3\n"})
    record = premap.write(manifest, sources=(premap.requirements, flask_app), runner=lambda commands: 1 / 0)
    assert [s["state"] for s in record["sources"] if s["source"].startswith("flask")] == ["not_needed"]


def test_the_folders_share_the_time_and_none_has_less_than_ten_seconds():
    assert [flask_app.run_seconds(n) for n in (1, 3, 90, 200)] == [900, 300, 10, 10]


def test_the_runner_restores_the_python_environment_of_each_folder_and_the_script_is_unpacked_beside_the_tools(tmp_path):
    import preparation
    spec = container_runner.TOOLS["flask"]
    assert spec["restores"] == "python" and spec["registries"] and spec["memory"] == container_runner.TOOLS["next"]["memory"]
    assert "flask_routes.py" in {name for _, _, name in spec["files"]} and f"{preparation.T}/flask_routes.py" in spec["setup"][0]
    project_dir = tmp_path / "p"
    (project_dir / "api").mkdir(parents=True)
    (project_dir / "api/requirements.txt").write_text("flask==3.1.3\n", encoding="utf-8")
    (project_dir / "docs").mkdir()
    (project_dir / "docs/uv.lock").write_text("", encoding="utf-8")
    (project_dir / "docs/pyproject.toml").write_text("[project]\nname='d'\nversion='1'\n", encoding="utf-8")
    restored = container_runner._python(project_dir)
    assert len(restored["lines"]) == 2 and any("'api'" in line and "uv venv" in line for line in restored["lines"])
    assert any("'docs'" in line and "uv sync" in line for line in restored["lines"])
    assert set(restored["needs"]) == {"uv"}


def test_no_engine_carries_the_reason_as_the_source_s_gap_and_nothing_of_the_project_runs_here(tmp_path):
    _, manifest = manifest_of(tmp_path, project())
    _, run = recorder(state="gap")
    with patch.object(container, "run_commands", run):
        record = premap.write(manifest, sources=(premap.requirements, flask_app), runner=container_runner.runner(manifest))
    [gap] = [g for g in record["gaps"] if g.get("source") == SOURCE]
    assert gap["kind"] == "model_not_run" and "no engine" in gap["detail"] and gap["remedy"] == "start one"
    assert "framework_entries" not in record


# -------------------------------------------------------- the answer the probe will record

@pytest.mark.xfail(strict=True, condition=not RECORDED.is_file(), reason="waits for the answer `benchmarks/flask-routes/modal_probe.py` records on Modal")
def test_the_answer_recorded_on_modal_gives_every_rule_of_the_fixture_a_row_or_a_gap(tmp_path):
    recorded = json.loads(RECORDED.read_text(encoding="utf-8"))
    record, gaps, _ = read(tmp_path, project(), [{**recorded["routes"], "root": "/work"}])
    assert {r["path"] for r in rows(record)} >= {"/", "/items", "/admin/stats", "/admin/users/<int:user_id>", "/page"}
