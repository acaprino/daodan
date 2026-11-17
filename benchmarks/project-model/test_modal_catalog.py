"""modal_catalog.py's report: the files it writes on this PC are the ones pipeline_report.py writes.

On Modal: python tests/modal_pytest.py benchmarks/project-model/test_modal_catalog.py -q (Modal's client is there).
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import modal_catalog  # noqa: E402
import pipeline_report  # noqa: E402

ROUND = HERE / "results" / "pipeline" / "2026-11-16-jvm-kotlinconf.json"


def test_the_report_written_here_is_the_one_pipeline_report_writes(tmp_path):
    direct, here, up = tmp_path / "direct", tmp_path / "here", tmp_path / "up"
    for folder in (direct, here):
        folder.mkdir()
        shutil.copy(ROUND, folder / ROUND.name)
    pipeline_report.main([str(direct / ROUND.name)])
    sent, out = modal_catalog.report_args([str(here / ROUND.name)], here)
    shutil.copytree(here, up)  # the folder as it goes up: the container writes in its own copy
    modal_catalog.write_report(modal_catalog.report_here(sent, up), out)
    for suffix in (".report.md", ".report.json"):
        name = ROUND.with_suffix(suffix).name
        assert (here / name).read_bytes() == (direct / name).read_bytes(), name


def test_a_path_outside_the_benchmark_folder_stops_before_modal(tmp_path):
    with pytest.raises(SystemExit, match="outside"):
        modal_catalog.report_args([str(tmp_path / "round.json")], tmp_path / "benchmark")
