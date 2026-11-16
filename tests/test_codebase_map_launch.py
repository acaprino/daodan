"""The command lines the host starts for the plugin (`.mcp.json`, `hooks/hooks.json`, `plugin.toml`). The host
starts them in the analyzed project's folder, and uv runs the interpreter of a `.venv` it finds from its working
directory up, whatever `--no-config --no-project` say: so each line takes uv out of the project first
(`--directory`), and the server is told its project (AGENTS.md: nothing of the project runs on the host).

    python -B -m pytest -q -p no:cacheprovider tests/test_codebase_map_launch.py
"""
from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
import tomllib
from pathlib import Path

import pytest

PLUGIN = Path(__file__).resolve().parents[1] / "plugins/codebase-map"
# What stands in for the server: it says how it was started.
SCRIPT = ('# /// script\n# requires-python = ">=3.12"\n# dependencies = []\n# ///\n'
          'import json, os, sys\nprint(json.dumps({"argv": sys.argv[1:], "cwd": os.getcwd()}))\n')


def launches() -> dict[str, list[str]]:
    """Each command line a host starts for the plugin, as its words."""
    server = json.loads((PLUGIN / ".mcp.json").read_text(encoding="utf-8"))["mcpServers"]["codebase-map"]
    hooks = json.loads((PLUGIN / "hooks/hooks.json").read_text(encoding="utf-8"))["hooks"]
    found = {"server": [server["command"], *server["args"]]}
    for event, groups in hooks.items():
        for group in groups:
            for number, hook in enumerate(group["hooks"]):
                found[f"hook {event} {number}"] = shlex.split(hook["command"])
    return found


def test_the_manifest_declares_the_server_as_the_host_starts_it():
    declared = tomllib.loads((PLUGIN / "plugin.toml").read_text(encoding="utf-8"))["mcp"]["servers"]
    assert [[server["command"], *server["args"]] for server in declared] == [launches()["server"]]


@pytest.mark.parametrize("name", sorted(launches()))
@pytest.mark.skipif(os.name == "nt" or not shutil.which("uv"),
                    reason="uv itself runs the line, where a file is a program")
def test_uv_started_in_a_project_runs_nothing_of_it(tmp_path, name):
    """A project whose `.venv` holds programs named as an interpreter's, whose version files name another, and
    whose uv settings no uv can read. The line, started in the project's folder as the host starts it and with
    nothing in uv's cache (a first start: uv looks for an interpreter only until the script has an environment
    there), runs its script on uv's own Python, outside the project; none of the project's programs leaves a
    mark. The server
    gets the project's folder as the host gives it (`${CLAUDE_PROJECT_DIR}`: the folder it would have started
    in); the hook reads it from its input."""
    project, plugin, mark = tmp_path / "project", tmp_path / "plugin", tmp_path / "mark"
    python = project / "its-python"
    (project / ".venv/bin").mkdir(parents=True)
    for program in (python, project / ".venv/bin/python", project / ".venv/bin/python3"):
        program.write_text(f'#!/bin/sh\necho "$0 $*" >> "{mark}"\nexit 1\n', encoding="utf-8")
        program.chmod(0o755)
    (project / ".venv/pyvenv.cfg").write_text(f"home = {project}\n", encoding="utf-8")
    for version_file in (".python-version", ".python-versions"):
        (project / version_file).write_text(f"{python}\n", encoding="utf-8")
    for settings in ("uv.toml", "pyproject.toml"):
        (project / settings).write_text("no uv reads [this\n", encoding="utf-8")
    script = plugin / "skills/map/scripts/mcp_server.py"
    script.parent.mkdir(parents=True)
    script.write_text(SCRIPT, encoding="utf-8")
    given = {"${CLAUDE_PLUGIN_ROOT}": str(plugin), "${CLAUDE_PROJECT_DIR}": str(project)}  # as the host fills them
    words = launches()[name]
    for variable, value in given.items():
        words = [word.replace(variable, value) for word in words]
    assert words[0] == "uv" and str(script) in words and not any("${" in word for word in words)
    def first(command: list[str], cache: str) -> subprocess.CompletedProcess:
        env = {**os.environ, "UV_CACHE_DIR": str(tmp_path / cache), "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}
        return subprocess.run(command, cwd=project, env=env, capture_output=True, text=True, timeout=300)

    done = first(words, "cache")
    assert not mark.exists(), mark.read_text(encoding="utf-8")
    assert done.returncode == 0, done.stderr
    started = json.loads(done.stdout)
    assert Path(started["cwd"]) == plugin
    assert started["argv"] == (["--project", str(project)] if name == "server" else ["--hook"])
    # The same line started where the host starts it, without the option that takes uv out: uv runs the project's.
    at = words.index("--directory")
    inside = first([*words[:at], *words[at + 2:]], "another cache")
    assert mark.exists(), (inside.stdout, inside.stderr)
