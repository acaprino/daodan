"""The installable application: the wheel built from the checkout holds the command and what its tools read
beside them (the scripts that are not Python, the data, the pages), or `uv tool install` gives a `daodan` that
starts and then finds nothing.

    python tests/modal_pytest.py -q tests/test_daodan_package.py
"""
from __future__ import annotations

import shutil
import subprocess
import zipfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
HELD = ("daodan/__main__.py", "daodan/core/mcp_server.py", "daodan/core/app.py", "daodan/core/indexers/css_sass.js",
        "daodan/core/premap/enry_facts.go", "daodan/core/dynamic/jvm_record/Agent.java",
        "daodan/data/service-registry.json", "daodan/assets/app/index.html", "daodan/assets/viewer/index.html",
        "daodan/references/system-map.md", "daodan/core/composition.py", "daodan/review/catalog.toml",
        "daodan/review/roles/premise-auditor.md", "daodan/review/contracts/reviewer-binding.toml",
        "daodan/review/reviewer-common.md")


@pytest.mark.skipif(not shutil.which("uv") or not (REPO / "pyproject.toml").is_file(),
                    reason="uv builds the wheel from the checkout's pyproject.toml")
def test_the_wheel_holds_the_command_and_what_its_tools_read(tmp_path):
    source = tmp_path / "source"  # a copy: the build writes nothing in the checkout
    source.mkdir()
    for name in ("pyproject.toml", "README.md", "LICENSE"):
        shutil.copy(REPO / name, source / name)
    shutil.copytree(REPO / "daodan", source / "daodan", ignore=shutil.ignore_patterns("__pycache__"))
    built = subprocess.run(["uv", "build", "--wheel", "--out-dir", str(tmp_path / "out"), str(source)],
                           capture_output=True, text=True, timeout=600)
    assert built.returncode == 0, built.stderr
    (wheel,) = (tmp_path / "out").glob("daodan-*.whl")
    with zipfile.ZipFile(wheel) as archive:
        names = set(archive.namelist())
        entry = next(name for name in names if name.endswith(".dist-info/entry_points.txt"))
        assert "daodan = daodan.__main__:main" in archive.read(entry).decode("utf-8")
    assert not [name for name in HELD if name not in names]
    assert sum(name.startswith("daodan/data/marks/") for name in names) == len(list((REPO / "daodan/data/marks").iterdir()))
