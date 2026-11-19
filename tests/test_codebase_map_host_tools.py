"""The platform Daodan downloads its tools for is read from the process: no question to the system, so no process
is started even when Windows does not answer."""
from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "daodan/core"
sys.path.insert(0, str(SCRIPTS))

import resolve_edges as rx  # noqa: E402


@pytest.fixture
def silent_windows(monkeypatch):
    """`platform` with an empty cache and a WMI that does not answer, as with the commit exhausted: it would run
    `ver` through the shell. Every process started is recorded and refused."""
    import platform
    import subprocess
    started = []

    def refuse(*args, **kwargs):
        started.append(args[0] if args else kwargs.get("args"))
        raise AssertionError("a process was started")

    monkeypatch.setattr(platform, "_uname_cache", None)
    monkeypatch.setattr(platform, "_wmi_query", lambda *args: (_ for _ in ()).throw(OSError("WMI did not answer")),
                        raising=False)
    monkeypatch.setattr(subprocess, "Popen", refuse)
    return started


@pytest.mark.parametrize("system, machine, key", [
    ("win32", "AMD64", "win-x64"), ("win32", "ARM64", "win-arm64"), ("linux", "x86_64", "linux-x64"),
    ("linux", "aarch64", "linux-arm64"), ("darwin", "arm64", "osx-arm64")])
def test_the_platform_key_comes_from_the_process_and_starts_no_process(silent_windows, monkeypatch, system,
                                                                         machine, key):
    monkeypatch.setattr(rx.sys, "platform", system)
    monkeypatch.setenv("PROCESSOR_ARCHITECTURE", machine)
    monkeypatch.setattr(rx.os, "uname", lambda: types.SimpleNamespace(machine=machine), raising=False)
    assert rx._platform() == key
    assert silent_windows == []
