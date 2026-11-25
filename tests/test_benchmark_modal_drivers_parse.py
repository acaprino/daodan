"""The Modal drivers of the benchmarks are valid Python. No suite imports them (they need Modal's client and an account), so a broken
one shows only when a round starts: `modal_map.py` was pushed with its `routes_case` inside the string of `NETWORK_PROBE`."""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DRIVERS = sorted((ROOT / "benchmarks").glob("*/modal_*.py"))


def test_the_benchmarks_have_modal_drivers_to_check():
    assert {path.name for path in DRIVERS} >= {"modal_map.py", "modal_pipeline.py"}


@pytest.mark.parametrize("path", DRIVERS, ids=lambda path: path.relative_to(ROOT).as_posix())
def test_a_modal_driver_of_the_benchmarks_parses(path):
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
