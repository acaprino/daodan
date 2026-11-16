"""The pipeline's Sandboxes on Modal: the runtime a run takes. Run: python tests/modal_pytest.py
benchmarks/project-model/test_modal_pipeline.py (Modal's client is there)."""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parents[1] / "plugins/codebase-map/skills/map/scripts")]

import modal_pipeline  # noqa: E402
from dynamic import callgrind  # noqa: E402


def test_a_run_that_starts_valgrind_or_services_takes_a_vm_sandbox():
    """gVisor reports SEGV_ACCERR where Linux says SEGV_MAPERR, and Valgrind dies at a program's start there: the
    runs of the native observers, which start it, take a VM Sandbox with its own Linux kernel, as the runs with
    services do (Docker runs only there). Measured on 16 November 2026: Linux 7.3.4, `valgrind true` at 48
    environment sizes, 105 stack extensions on SEGV_MAPERR and none on SEGV_ACCERR, a crate's cargo test traced by
    Callgrind."""
    assert modal_pipeline.vm(["sh", "-c", f"run 0 . {callgrind.VALGRIND_BIN} -q --tool=callgrind true"], ())
    assert modal_pipeline.vm(["sh", "-c", "npm test"], [{"name": "db", "image": "postgres:16"}])
    assert not modal_pipeline.vm(["sh", "-c", "npm test"], ())
