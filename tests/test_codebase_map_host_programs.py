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
import tree_scope  # noqa: E402


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
        container.find_engine(own=False)  # no docker, no podman: the project's are never started
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
