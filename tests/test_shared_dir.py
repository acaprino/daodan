"""`DAODAN_SHARED_DIR`: where Daodan keeps what it shares across projects (language engines, npm and uv caches,
models, the container engine's WSL distribution), on the disk its owner chooses. Unset, it is the per-user cache
folder's `Daodan`, as before. Every reader goes through `embedding_worker.shared_cache_dir`.

    python -B -m pytest -q -p no:cacheprovider tests/test_shared_dir.py
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "daodan/core"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import container  # noqa: E402
import embedding_worker  # noqa: E402
import engine_pass  # noqa: E402
import engine_tools  # noqa: E402
import mcp_service  # noqa: E402
from indexers import runtime  # noqa: E402
from languages import _treesitter  # noqa: E402


@pytest.fixture
def named(tmp_path, monkeypatch):
    """The folder `DAODAN_SHARED_DIR` names, which does not exist yet; the per-user default is elsewhere in the
    scratch, so a reader that ignores the setting finds out without touching the real one."""
    folder = tmp_path / "other-disk" / "daodan-shared"
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "default"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "default"))
    monkeypatch.setenv("DAODAN_SHARED_DIR", str(folder))
    return folder


def test_unset_or_empty_the_shared_folder_is_the_per_user_cache_folders_daodan(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    expected = tmp_path / ("Daodan" if os.name == "nt" else "daodan")
    monkeypatch.delenv("DAODAN_SHARED_DIR", raising=False)
    assert embedding_worker.shared_cache_dir() == expected
    monkeypatch.setenv("DAODAN_SHARED_DIR", "")
    assert embedding_worker.shared_cache_dir() == expected


def test_the_named_folder_is_the_shared_folder_itself(named):
    assert embedding_worker.shared_cache_dir() == named
    assert not named.exists()  # the callers create it where they already do


def test_engines_caches_models_and_the_containers_folder_are_in_the_named_folder(named):
    reached = {
        "engines": engine_tools.shared_engine_dir("scip-go"),
        "maven": engine_tools.maven_central_dir(),
        "uv": Path(engine_tools.uv_options()[-1]),
        "npm": Path(engine_tools.node_environment()["npm_config_cache"]),
        "node": Path(engine_tools.node_environment()["NODE_COMPILE_CACHE"]),
        "model": embedding_worker.default_model_dir(),
        "grammars": _treesitter._daodan_home(),
        "volumes": container.volume_registry(),
        "distribution": container.engine_home() / "distro-0123456789ab",
        "pass": engine_pass.running_record(named / "manifest.sqlite"),
        "explorer": mcp_service.requests_record(named / "store"),
    }
    outside = {kind: path for kind, path in reached.items() if named not in path.parents}
    assert outside == {}
    assert container.engine_home() == named / "engines" / "kiri" / container.KIRI_VERSION


@pytest.mark.parametrize("value", ["relative/folder", "folder", ".", "..", "~/daodan"])
def test_a_relative_folder_is_refused_with_the_settings_name(value, monkeypatch):
    monkeypatch.setenv("DAODAN_SHARED_DIR", value)
    with pytest.raises(ValueError, match="DAODAN_SHARED_DIR must be an absolute path"):
        embedding_worker.shared_cache_dir()


def test_a_process_daodan_starts_for_a_node_tool_sees_the_folder(named):
    """`runtime.environment` is what a Node tool of Daodan's is started with; the child reads it as Daodan does."""
    probe = ("import sys; sys.path.insert(0, sys.argv[1]); import embedding_worker; "
             "print(embedding_worker.shared_cache_dir())")
    done = subprocess.run([sys.executable, "-c", probe, str(SCRIPTS)], env=runtime.environment(), cwd=str(SCRIPTS),
                          capture_output=True, text=True, timeout=120)
    assert done.returncode == 0, done.stderr
    assert Path(done.stdout.strip()) == named
