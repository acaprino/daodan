"""What a tool on the PATH may download into the user's home when Daodan runs it: never a toolchain a project's
file names. Each fake on the PATH records what it was asked, with the variables that switch its downloads off,
and does what the real tool would do."""
from __future__ import annotations

import json
import os
import stat
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "plugins/codebase-map/skills/map/scripts"
sys.path.insert(0, str(SCRIPTS))

import resolve_edges as rx  # noqa: E402
from indexers import rust  # noqa: E402

# rustup's proxy: a toolchain file in the folder or a parent names the toolchain; one not installed is installed
# unless RUSTUP_AUTO_INSTALL is 0, and then the proxy stops with rustup's error.
RUSTUP = r'''
import json, os, sys
from pathlib import Path
tool, args = sys.argv[1], sys.argv[2:]
here = Path.cwd()
pin = next((folder / name for folder in (here, *here.parents) for name in ("rust-toolchain.toml", "rust-toolchain")
            if (folder / name).is_file()), None)
record = {"tool": tool, "args": args, "cwd": str(here), "auto_install": os.environ.get("RUSTUP_AUTO_INSTALL")}
if pin is not None:
    if os.environ.get("RUSTUP_AUTO_INSTALL") == "0":
        record["refused"] = str(pin)
    else:
        record["installed"] = str(pin)
with open(os.environ["FAKE_LOG"], "a", encoding="utf-8") as log:
    log.write(json.dumps(record) + "\n")
if "refused" in record:
    print("error: toolchain '1.79.0-x86_64-unknown-linux-gnu' is not installed", file=sys.stderr)
    sys.exit(1)
if args[:2] == ["--print", "sysroot"]:
    print(os.environ["FAKE_SYSROOT"])
'''

# uv: records each call; `venv` makes the environment's folder.
UV = r'''
import json, os, sys
from pathlib import Path
args = sys.argv[2:]
keys = ("UV_PYTHON_DOWNLOADS", "UV_NO_CONFIG", "UV_CACHE_DIR")
with open(os.environ["FAKE_LOG"], "a", encoding="utf-8") as log:
    log.write(json.dumps({"tool": "uv", "args": args, "cwd": os.getcwd(),
                          **{key: os.environ.get(key) for key in keys}}) + "\n")
if args[:1] == ["venv"]:
    Path(args[1]).mkdir(parents=True, exist_ok=True)
'''


def _fake(folder: Path, name: str, body: str) -> None:
    script = folder / f"fake_{name}.py"
    script.write_text(body, encoding="utf-8")
    if os.name == "nt":
        (folder / f"{name}.cmd").write_text(f'@"{sys.executable}" -I "{script}" {name} %*\r\n', encoding="utf-8")
    else:
        launcher = folder / name
        launcher.write_text(f'#!/bin/sh\nexec "{sys.executable}" -I "{script}" {name} "$@"\n', encoding="utf-8")
        launcher.chmod(launcher.stat().st_mode | stat.S_IEXEC)


def _log(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()] if path.is_file() else []


@pytest.fixture
def host(tmp_path, monkeypatch):
    """Fakes first on the PATH, the shared folder in `tmp_path`, plenty of memory and disk, and no download."""
    tools = tmp_path / "bin"
    tools.mkdir()
    for name in ("rustc", "cargo", "rustup"):
        _fake(tools, name, RUSTUP)
    _fake(tools, "uv", UV)
    sysroot = tmp_path / "sysroot"
    (sysroot / "lib/rustlib/src/rust/library").mkdir(parents=True)
    log = tmp_path / "asked.jsonl"
    monkeypatch.setenv("PATH", f"{tools}{os.pathsep}{os.environ.get('PATH', '')}")
    monkeypatch.setenv("FAKE_LOG", str(log))
    monkeypatch.setenv("FAKE_SYSROOT", str(sysroot))
    monkeypatch.delenv("RUSTUP_AUTO_INSTALL", raising=False)
    monkeypatch.setattr(rx, "shared_cache_dir", lambda: tmp_path / "cache")
    monkeypatch.setattr(rx, "free_memory", lambda: 64 * 2**30)

    def no_download(url, *args, **kwargs):
        raise AssertionError(f"nothing is downloaded: {url}")

    monkeypatch.setattr(rx, "download", no_download)
    monkeypatch.setattr(rx, "open_url", no_download)
    return {"root": tmp_path, "log": log}


def _pinned(root: Path) -> Path:
    project = root / "project"
    (project / "src").mkdir(parents=True)
    (project / "Cargo.toml").write_text('[package]\nname = "pinned"\nversion = "0.1.0"\n', encoding="utf-8")
    (project / "src/lib.rs").write_text("pub fn f() {}\n", encoding="utf-8")
    (project / "rust-toolchain.toml").write_text('[toolchain]\nchannel = "1.79.0"\n', encoding="utf-8")
    return project


def test_the_rust_toolchain_on_the_path_is_asked_with_rustup_auto_install_off(host, monkeypatch):
    # Started from a pinned project's folder, as a server started there is.
    monkeypatch.chdir(_pinned(host["root"]))
    rx.rust_toolchain()
    asked = _log(host["log"])
    assert asked and all(call["auto_install"] == "0" for call in asked), asked
    assert not [call for call in asked if "installed" in call]


def test_a_project_pinning_a_toolchain_rustup_does_not_have_is_unavailable_and_nothing_is_installed(host, monkeypatch):
    project = _pinned(host["root"])
    monkeypatch.chdir(project)
    result = rust.index(project, host["root"] / "work")
    asked = _log(host["log"])
    assert not [call for call in asked if "installed" in call], asked
    assert result["state"] == "unavailable", result
    assert "rust-toolchain.toml" in result["reason"] and "1.79.0" not in result["install"]
    assert "rustup toolchain install" in result["install"]


def test_rust_analyzer_s_own_cargo_calls_have_rustup_auto_install_off(host):
    engine = rx.RustEngine(_pinned(host["root"]))
    engine.toolchain, engine.target_dir = host["root"] / "toolchain", host["root"] / "target"
    _launch, overrides = engine.command(host["root"] / "home")
    assert overrides["RUSTUP_AUTO_INSTALL"] == "0"


def test_the_project_environment_asks_uv_for_no_python_download_no_project_config_and_the_shared_cache(host,
                                                                                                         monkeypatch):
    project = host["root"] / "py"
    project.mkdir()
    (project / "requirements.txt").write_text("attrs\n", encoding="utf-8")
    # A uv setting in the project would choose a Python to download; a server started there reads it.
    (project / "uv.toml").write_text('python-preference = "only-managed"\n', encoding="utf-8")
    monkeypatch.chdir(project)
    rx.python_environment(project, ["requirements.txt"])
    asked = _log(host["log"])
    assert asked, "uv was not asked"
    cache = str(host["root"] / "cache")
    for call in asked:
        assert (call["UV_PYTHON_DOWNLOADS"], call["UV_NO_CONFIG"]) == ("never", "1"), call
        assert call["UV_CACHE_DIR"] and call["UV_CACHE_DIR"].startswith(cache), call
    venv = next(call["args"] for call in asked if call["args"][:1] == ["venv"])
    assert venv[venv.index("--python") + 1] == sys.executable
