"""What the host starts runs nothing of the analyzed project (AGENTS.md): no program found in the project's folder,
no module imported from it.

    python -B -m pytest -q -p no:cacheprovider tests/test_codebase_map_host_programs.py
"""
from __future__ import annotations

import os
import stat
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "plugins/codebase-map/skills/map/scripts"))

import code_graph  # noqa: E402
import container  # noqa: E402
import engine_pass  # noqa: E402
import tree_scope  # noqa: E402
import usage_finder  # noqa: E402


def _planted(folder: Path, name: str) -> Path:
    """A program named `name` in `folder`, as Windows would start it (`.bat` there)."""
    path = folder / (f"{name}.bat" if os.name == "nt" else name)
    path.write_text("echo planted\n", encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IEXEC)
    return path


def test_a_program_is_found_on_absolute_path_entries_only(tmp_path, monkeypatch):
    """Windows, and `shutil.which` there, look in the working directory first, and an analysis runs with the
    analyzed project as its working directory: its own `docker.bat`, `podman.bat`, `npm.bat` or `wsl.exe` would run.
    `tree_scope.program` reads only absolute PATH entries, as `git_executable` does."""
    project, tools = tmp_path / "project", tmp_path / "tools"
    project.mkdir()
    tools.mkdir()
    for name in ("docker", "podman", "npm", "wsl"):
        _planted(project, name)
    monkeypatch.chdir(project)
    monkeypatch.setenv("PATH", os.pathsep.join([".", "project", ""]))
    assert [tree_scope.program(name) for name in ("docker", "podman", "npm", "wsl")] == [None] * 4
    assert container.wsl_executable() in (None, str(Path(os.environ.get("SystemRoot", r"C:\Windows"))
                                                    / "System32" / "wsl.exe"))
    monkeypatch.delenv("DAODAN_CONTAINER", raising=False)
    with pytest.raises(container.Gap):
        container.user_engine()  # no docker, no podman: the project's are never started
    tool = _planted(tools, "npm")
    monkeypatch.setenv("PATH", os.pathsep.join([".", str(tools)]))
    assert tree_scope.program("npm") == str(tool)


def test_the_comment_rewriter_runs_no_formatter_on_the_host(tmp_path, monkeypatch):
    """prettier loads `prettier.config.js` and its plugins, ruff and black read the project's pyproject: a formatter
    over the project's file runs the project's configuration. The rewrite leaves formatting undone and says why
    (D-256); no program starts, though one of each name is on PATH."""
    import subprocess
    import comment_rewriter
    marker, project, tools = tmp_path / "ran", tmp_path / "project", tmp_path / "tools"
    project.mkdir()
    tools.mkdir()
    (project / "prettier.config.js").write_text(f"require('fs').writeFileSync({str(marker)!r}, 'config');\n"
                                                "module.exports = {};\n", encoding="utf-8")
    (project / "app.js").write_text("// increment i\ni++;\n", encoding="utf-8")
    for name in ("prettier", "biome", "ruff", "black", "rustfmt", "gofmt"):
        path = tools / (f"{name}.bat" if os.name == "nt" else name)
        path.write_text(f"echo {name} > {marker}\n", encoding="utf-8")
        path.chmod(path.stat().st_mode | stat.S_IEXEC)
    monkeypatch.setenv("PATH", os.pathsep.join([str(tools), os.environ.get("PATH", "")]))
    started = []
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: started.append(args) or pytest.fail("a process"))
    _rewritten, changes = comment_rewriter.rewrite_file(project / "app.js", dry_run=False)
    assert not marker.exists() and started == []
    assert changes[-1] == comment_rewriter.FORMAT_UNDONE


@pytest.mark.skipif(sys.platform == "win32", reason="the memory probe wraps a run on POSIX only")
def test_the_memory_probe_imports_nothing_from_the_folder_it_runs_in(tmp_path):
    """`code_graph.measured` wraps an indexer in this Python with `-c`, started in the project's folder or its mirror:
    with `-c` Python puts that folder first on `sys.path`, so a project's `subprocess.py` or `resource.py` would
    run on the host. The probe runs isolated (`-I`)."""
    marker, folder = tmp_path / "ran", tmp_path / "project"
    folder.mkdir()
    for name in ("subprocess", "resource", "sys"):
        (folder / f"{name}.py").write_text(f"open({str(marker)!r}, 'a').write({name!r})\nraise SystemExit(3)\n",
                                           encoding="utf-8")
    run = code_graph.measured([sys.executable, "-I", "-c", "pass"], str(folder), None, 60)
    assert not marker.exists() and run["returncode"] == 0 and run["peak_mb"] is not None


# ------------------------------------------------------------------ a program named without its folder

# The stand-in programs are files that say they started: a file is a program by its mode only where modes count.
marked = pytest.mark.skipif(os.name == "nt", reason="the stand-in programs are shell scripts")


def _marked(folder: Path, name: str, mark: Path, code: int = 0) -> Path:
    """A program named `name` in `folder` that says in `mark` that it started and with what, then ends with `code`."""
    path = folder / name
    path.write_text(f'#!/bin/sh\necho "$0 $*" >> "{mark}"\nexit {code}\n', encoding="utf-8")
    path.chmod(0o755)
    return path


@pytest.fixture
def searched(tmp_path, monkeypatch):
    """A project that is the working directory and is searched for a program's name before the PATH's own folder:
    what Windows does with every name written without a folder, and any system whose PATH holds a relative entry.
    `(project, tools, what the project's programs said, what the PATH's said)`."""
    project, tools = tmp_path / "project", tmp_path / "tools"
    project.mkdir()
    tools.mkdir()
    monkeypatch.chdir(project)
    monkeypatch.setenv("PATH", os.pathsep.join([".", str(tools)]))
    return project, tools, tmp_path / "the-project-s-ran", tmp_path / "the-path-s-ran"


@marked
def test_a_pass_is_ended_by_the_taskkill_of_the_path_never_by_the_project_s(searched, monkeypatch):
    project, tools, ran, own = searched
    for name in ("taskkill", "taskkill.exe"):
        _marked(project, name, ran)
    _marked(tools, "taskkill.exe", own)
    with monkeypatch.context() as windows:
        windows.setattr(os, "name", "nt")  # the branch of Windows, on the programs above
        engine_pass._terminate_tree(4242)
        (tools / "taskkill.exe").unlink()
        with pytest.raises(OSError, match="taskkill"):  # no name without a folder is tried instead
            engine_pass._terminate_tree(4242)
    assert not ran.exists(), ran.read_text(encoding="utf-8")
    assert own.read_text(encoding="utf-8").split() == [str(tools / "taskkill.exe"), "/PID", "4242", "/T", "/F"]


@marked
def test_without_wsl_nothing_named_wsl_is_started(searched):
    project, _tools, ran, _own = searched
    _marked(project, "wsl.exe", ran)
    assert container.wsl_executable() is None
    for start in (lambda: container.wsl("--status"), container.distro_argv):
        with pytest.raises(container.Gap) as gap:
            start()
        assert gap.value.cause == "WSL is not installed"
    assert not ran.exists(), ran.read_text(encoding="utf-8")


@marked
def test_usages_are_searched_by_a_tool_of_the_path_or_by_python_never_by_the_project_s(searched):
    """A project's own `rg` or `grep` would also choose the answer: here each says there is no match."""
    project, tools, ran, own = searched
    (project / "a.py").write_text("class Engine:\n    pass\n\n\nEngine()\n", encoding="utf-8")
    for name in ("rg", "grep"):
        _marked(project, name, ran, code=1)
    found = usage_finder.find_usages_with_grep("Engine", [project])
    assert {usage.line_number for usage in found} == {1, 5}  # no tool on the PATH: Python's own search
    _marked(tools, "rg", own, code=1)
    assert usage_finder.find_usages_with_grep("Engine", [project]) == []  # the PATH's tool answers
    assert own.read_text(encoding="utf-8").startswith(f"{tools / 'rg'} -n --with-filename -F -e Engine -- ")
    assert not ran.exists(), ran.read_text(encoding="utf-8")
