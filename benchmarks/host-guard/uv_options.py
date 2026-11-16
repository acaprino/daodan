"""What real uv runs of a project it is started in, option by option and start after start. Prints its rows.

    python tests/modal_pytest.py -q -s benchmarks/host-guard/uv_options.py
"""
from __future__ import annotations

import itertools
import json
import os
import subprocess
import sys
from pathlib import Path

SCRIPT = ('# /// script\n# requires-python = ">=3.12"\n# dependencies = []\n# ///\n'
          'import os, sys\nprint("RAN cwd=" + os.getcwd())\n')
PLANTS = ("venv", "version-file-path", "version-file-absent", "settings")  # what the project holds
OPTIONS = {"--no-config --no-project": ["--no-config", "--no-project"],
           "+ --project PLUGIN": ["--no-config", "--no-project", "--project", "PLUGIN"],
           "+ --managed-python": ["--no-config", "--no-project", "--managed-python"],
           "+ --python 3.13": ["--no-config", "--no-project", "--python", "3.13"],
           "+ --python <this interpreter>": ["--no-config", "--no-project", "--python", sys.executable],
           "--directory PLUGIN +": ["--directory", "PLUGIN", "--no-config", "--no-project"]}


def plant(project: Path, what: str, mark: Path) -> None:
    program = f'#!/bin/sh\necho "{what}" >> "{mark}"\nexit 1\n'
    if what == "venv":
        (project / ".venv/bin").mkdir(parents=True)
        for name in ("python", "python3"):
            (project / ".venv/bin" / name).write_text(program, encoding="utf-8")
            (project / ".venv/bin" / name).chmod(0o755)
        (project / ".venv/pyvenv.cfg").write_text(f"home = {project}\n", encoding="utf-8")
    elif what == "version-file-path":
        (project / "its-python").write_text(program, encoding="utf-8")
        (project / "its-python").chmod(0o755)
        (project / ".python-version").write_text(f"{project / 'its-python'}\n", encoding="utf-8")
    elif what == "version-file-absent":
        (project / ".python-version").write_text("3.99\n", encoding="utf-8")
    else:
        for name in ("uv.toml", "pyproject.toml"):
            (project / name).write_text("no uv reads [this\n", encoding="utf-8")


def started(words: list[str], project: Path, cache: Path, mark: Path) -> dict:
    mark.unlink(missing_ok=True)
    env = {**os.environ, "UV_CACHE_DIR": str(cache), "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}
    done = subprocess.run(words, cwd=project, env=env, capture_output=True, text=True, timeout=300)
    return {"exit": done.returncode, "project's program ran": mark.exists(),
            "script's folder is the project": f"RAN cwd={project}\n" in done.stdout}


def test_options(tmp_path):
    """Each option set on a first start (an empty cache), for each thing a project can hold."""
    print("\nPROBE " + subprocess.run(["uv", "--version"], capture_output=True, text=True).stdout.strip())
    for number, (what, (label, options)) in enumerate(itertools.product(PLANTS, OPTIONS.items())):
        base = tmp_path / str(number)
        project, plugin = base / "project", base / "plugin"
        project.mkdir(parents=True)
        plugin.mkdir()
        plant(project, what, base / "mark")
        (plugin / "server.py").write_text(SCRIPT, encoding="utf-8")
        words = [str(plugin) if word == "PLUGIN" else word for word in options]
        before = words[:2] if words[0] == "--directory" else []  # a global option stands before the command
        words = ["uv", *before, "run", *words[len(before):], "--script", str(plugin / "server.py")]
        print("PROBE " + json.dumps({"project holds": what, "options": label,
                                     **started(words, project, base / "cache", base / "mark")}))


def test_starts(tmp_path):
    """The shipped options, start after start with one cache: when uv looks for an interpreter again."""
    project, mark, cache = tmp_path / "project", tmp_path / "mark", tmp_path / "cache"
    project.mkdir()
    plant(project, "venv", mark)

    def start(script: Path) -> str:
        return json.dumps(started(["uv", "run", "--no-config", "--no-project", "--script", str(script)], project,
                                  cache, mark))

    one, two = tmp_path / "plugin/1.0.0/server.py", tmp_path / "plugin/1.0.1/server.py"
    for script in (one, two):
        script.parent.mkdir(parents=True)
        script.write_text(SCRIPT, encoding="utf-8")
    print("\nPROBE first start: " + start(one))
    print("PROBE second start: " + start(one))
    one.write_text(SCRIPT + "# edited\n", encoding="utf-8")
    print("PROBE after the script's text changed: " + start(one))
    print("PROBE the script at a new path: " + start(two))
