"""The command lines the host starts for the plugin (`.mcp.json`, `hooks/hooks.json`, `plugin.toml`): the
installed `daodan`. The host starts them in the analyzed project's folder; the command imports its tools from its
own `core/` and nothing from the folder it starts in, and the server is told its project (AGENTS.md: nothing of
the project runs on the host).

    python -B -m pytest -q -p no:cacheprovider tests/test_codebase_map_launch.py
"""
from __future__ import annotations

import importlib
import json
import os
import shlex
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path
from unittest import mock

import pytest

REPO = Path(__file__).resolve().parents[1]
PLUGIN, PACKAGE = REPO / "plugins/codebase-map", REPO / "daodan"
# What stands in for the server: it says how it was started.
SCRIPT = 'import json, os, sys\nprint(json.dumps({"argv": sys.argv[1:], "cwd": os.getcwd()}))\n'
# What an installer writes for `[project.scripts] daodan`: a file outside the project that calls the entry.
COMMAND = 'import sys\nfrom daodan.__main__ import main\nsys.exit(main())\n'
# Files of the project named as Daodan's own and as modules it imports: each leaves a mark when run.
TRAPS = ("daodan/__init__.py", "daodan/__main__.py", "mcp_server.py", "snapshot.py", "sitecustomize.py",
         "usercustomize.py", "json.py", "runpy.py", "core/mcp_server.py")


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
def test_daodan_started_in_a_project_runs_nothing_of_it(tmp_path, name):
    """A project that holds files named as Daodan's own and as the modules it imports, each leaving a mark when
    run. The line, started in the project's folder as the host starts it, runs the server of the installation and
    none of them. The server gets the project's folder as the host gives it (`${CLAUDE_PROJECT_DIR}`); the hook
    reads it from its input."""
    project, site, mark = tmp_path / "project", tmp_path / "site", tmp_path / "mark"
    for trap in TRAPS:
        (project / trap).parent.mkdir(parents=True, exist_ok=True)
        (project / trap).write_text(f"open({str(mark)!r}, 'a').write(__file__)\n", encoding="utf-8")
    (site / "daodan/core").mkdir(parents=True)  # the installation: the entry as it is, a stand-in for the server
    for entry in ("__init__.py", "__main__.py"):
        shutil.copy(PACKAGE / entry, site / "daodan" / entry)
    (site / "daodan/core/mcp_server.py").write_text(SCRIPT, encoding="utf-8")
    command = tmp_path / "bin/daodan"
    command.parent.mkdir()
    command.write_text(COMMAND, encoding="utf-8")
    words = [word.replace("${CLAUDE_PROJECT_DIR}", str(project)) for word in launches()[name]]
    assert words[0] == "daodan" and not any("${" in word for word in words)
    env = {**os.environ, "PYTHONPATH": str(site)}

    done = subprocess.run([sys.executable, str(command), *words[1:]], cwd=project, env=env, capture_output=True,
                          text=True, timeout=300)
    assert not mark.exists(), mark.read_text(encoding="utf-8")
    assert done.returncode == 0, done.stderr
    started = json.loads(done.stdout)
    assert started["argv"] == (["--project", str(project)] if name == "server" else ["--hook"])
    # The traps are live: the same entry asked as a module of the folder it starts in runs the project's.
    subprocess.run([sys.executable, "-m", "daodan", *words[1:]], cwd=project, env=env, capture_output=True, timeout=300)
    assert mark.exists()


def test_the_command_refuses_what_is_not_a_tool_of_the_core(tmp_path):
    for words in (["../../outside"], ["no_such_tool"], [str(tmp_path / "x")], []):
        done = subprocess.run([sys.executable, str(PACKAGE / "__main__.py"), *words], capture_output=True, text=True,
                              timeout=300)
        assert done.returncode == 2 and "daodan app" in done.stderr, (words, done)


@pytest.mark.skipif(sys.version_info < (3, 12), reason="the server requires Python 3.12")
def test_the_server_takes_its_project_from_the_launch_never_from_where_it_starts(tmp_path, monkeypatch, capsys):
    """The server's project is `--project`, else the host's CLAUDE_PROJECT_DIR, and with neither it stops with the
    cause instead of mapping the folder it stands in."""
    monkeypatch.syspath_prepend(str(PACKAGE / "core"))
    for name in ("anyio", "mcp", "mcp.server", "mcp.server.mcpserver", "mcp.server.mcpserver.exceptions", "mcp.types"):
        try:
            importlib.import_module(name)
        except ImportError:  # the SDK is uv's to provide: the entry needs only its names
            monkeypatch.setitem(sys.modules, name, mock.MagicMock())
    held = sys.modules.pop("mcp_server", None)
    try:
        import mcp_server
        bound = []
        monkeypatch.setattr(mcp_server, "create_server",
                            lambda project, store=None: bound.append(Path(project)) or mock.MagicMock())
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path / "host"))
        mcp_server.main(["--project", str(tmp_path / "given")])
        mcp_server.main([])
        assert bound == [tmp_path / "given", tmp_path / "host"]
        monkeypatch.delenv("CLAUDE_PROJECT_DIR")
        with pytest.raises(SystemExit) as stopped:
            mcp_server.main([])
        assert stopped.value.code == 2 and "--project" in capsys.readouterr().err and len(bound) == 2
    finally:
        sys.modules.pop("mcp_server", None)
        if held is not None:
            sys.modules["mcp_server"] = held
