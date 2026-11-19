"""An npm tool Daodan installed is used only when the script it runs is there."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "daodan/core"))

from indexers import runtime  # noqa: E402

PACKAGE = "@sourcegraph/scip-python"


def _fake_npm(calls: list, entry: bool):
    def run(command, **options):
        calls.append(command)
        root = Path(command[command.index("--prefix") + 1]) / "node_modules" / PACKAGE
        root.mkdir(parents=True)
        (root / "package.json").write_text(json.dumps({"bin": {"scip-python": "index.js"}}), encoding="utf-8")
        if entry:
            (root / "index.js").write_text("// entry\n", encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, "", "")
    return run


@pytest.fixture
def shared(tmp_path, monkeypatch):
    monkeypatch.setattr(runtime.rx, "shared_engine_dir", lambda name: tmp_path / "engines" / name)
    monkeypatch.setattr(runtime, "room", lambda: None)
    monkeypatch.setattr(runtime, "_npm_cli", lambda directory: directory / "npm-cli.js")
    monkeypatch.setattr(runtime, "environment", lambda directory: {})
    return tmp_path


def test_an_install_that_lost_its_entry_script_is_installed_again(shared, monkeypatch):
    """The mark says installed, the script the tool runs is gone (a cleaner, a disk fault): it is installed anew,
    not run into `Cannot find module`."""
    home = shared / "engines" / "scip-python" / "0.6.8"
    damaged = home / "node_modules" / PACKAGE
    damaged.mkdir(parents=True)
    (damaged / "package.json").write_text(json.dumps({"bin": {"scip-python": "index.js"}}), encoding="utf-8")
    (home / ".installed").write_text("0.6.8", encoding="utf-8")
    calls: list = []
    monkeypatch.setattr(subprocess, "run", _fake_npm(calls, entry=True))
    script = runtime.npm_package(shared / "project", shared / "node", PACKAGE, "0.6.8")
    assert script == damaged / "index.js" and script.is_file() and len(calls) == 1


def test_a_package_that_installs_without_its_entry_script_is_unavailable_with_the_cause(shared, monkeypatch):
    calls: list = []
    monkeypatch.setattr(subprocess, "run", _fake_npm(calls, entry=False))
    with pytest.raises(runtime.Unavailable) as raised:
        runtime.npm_package(shared / "project", shared / "node", PACKAGE, "0.6.8")
    assert "index.js" in raised.value.reason and len(calls) == 1
