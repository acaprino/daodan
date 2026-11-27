"""An npm tool Daodan installed is used only when the script it runs is there."""
from __future__ import annotations

import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile

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


# ------------------------------------------------------------------ the real npm, in a project that sets traps for it

HOOKS = ("preinstall", "install", "postinstall", "prepare")
NODE = shutil.which("node")


def _marking(mark: Path) -> dict:
    """Lifecycle scripts that, run, each leave a file in `mark`."""
    return {hook: f"node -e \"require('fs').writeFileSync({json.dumps(str(mark / hook))}, '')\"" for hook in HOOKS}


def _trapped_project(root: Path, mark: Path) -> Path:
    """A project whose `.npmrc` and `package.json` each leave a mark in `mark` when npm reads or runs them:
    `logs-dir` (npm writes its debug log there on every command), `script-shell` (a shell that marks),
    `ignore-scripts=false`, an unreachable `registry` and the project's own lifecycle scripts."""
    root.mkdir(parents=True)
    mark.mkdir()
    shell = root / "shell.sh"
    shell.write_text(f"#!/bin/sh\ntouch {mark / 'script-shell'}\nexec /bin/sh \"$@\"\n", encoding="utf-8")
    shell.chmod(0o755)
    (root / ".npmrc").write_text(f"logs-dir={mark / 'npmrc-read'}\nscript-shell={shell}\nignore-scripts=false\n"
                                 "registry=http://127.0.0.1:9/\n", encoding="utf-8")
    (root / "package.json").write_text(json.dumps({"name": "trapped", "version": "1.0.0",
                                                   "scripts": _marking(mark)}), encoding="utf-8")
    return root


def _tarball(folder: Path, mark: Path) -> Path:
    """A package, packed as the registry serves one, whose own install scripts leave a mark: npm needs no network."""
    folder.mkdir(parents=True)
    archive = folder / "pinned-1.0.0.tgz"
    files = {"package/package.json": json.dumps({"name": "pinned", "version": "1.0.0", "bin": "index.js",
                                                 "scripts": _marking(mark)}),
             "package/index.js": "// entry\n"}
    with tarfile.open(archive, "w:gz") as packed:
        for name, text in files.items():
            data = text.encode("utf-8")
            info = tarfile.TarInfo(name)
            info.size = len(data)
            packed.addfile(info, io.BytesIO(data))
    return archive


@pytest.mark.skipif(not NODE or os.name == "nt", reason="no real Node on PATH (the image of tests/modal_pytest.py has it)")
def test_the_real_npm_install_reads_and_runs_nothing_of_the_project_it_is_started_in(tmp_path, monkeypatch):
    """`npm_install` started with the project as the working folder (it has no `cwd` of its own, it takes Daodan's):
    `--prefix` makes the prefix npm's project, so the project's `.npmrc` is not read, and with `--ignore-scripts`
    neither the project's lifecycle scripts nor the package's run. The control: the same npm with the same flags but
    no `--prefix`, started in a copy of the trap, reads that `.npmrc` (its `logs-dir` fills), so the mark is one npm
    leaves when it reads the file."""
    directory = Path(NODE).resolve().parent
    if not runtime._npm_cli(directory).is_file():
        pytest.skip(f"no npm beside {directory}")
    monkeypatch.setattr(runtime.rx, "node_environment", lambda: {"npm_config_cache": str(tmp_path / "npm-cache")})
    mark = tmp_path / "mark"
    project = _trapped_project(tmp_path / "project", mark)
    archive = _tarball(tmp_path / "registry", mark)
    prefix = tmp_path / "engines" / "pinned"
    prefix.mkdir(parents=True)
    monkeypatch.chdir(project)

    runtime.npm_install(directory, prefix, [str(archive)])

    assert (prefix / "node_modules" / "pinned" / "index.js").is_file()
    assert sorted(path.name for path in mark.iterdir()) == []
    assert not (project / "node_modules").exists() and not (project / "package-lock.json").exists()

    control_mark = tmp_path / "control-mark"
    control = _trapped_project(tmp_path / "control", control_mark)
    subprocess.run([str(directory / "node"), str(runtime._npm_cli(directory)), "install", "--ignore-scripts",
                    "--no-audit", "--no-fund", "--loglevel=error", str(archive)], cwd=str(control), check=True,
                   env=runtime.environment(directory), stdin=subprocess.DEVNULL, capture_output=True, text=True,
                   timeout=300)
    assert any((control_mark / "npmrc-read").iterdir())
