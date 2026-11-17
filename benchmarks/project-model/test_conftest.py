"""pytest over this folder collects Daodan's tests only: the tests inside the fixtures are data of the fixtures.

On Modal: python tests/modal_pytest.py benchmarks/project-model/test_conftest.py -q
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def test_the_folder_collects_without_errors_and_without_the_tests_of_the_fixtures():
    assert (HERE / "fixtures" / "py-uv-src-layout" / "tests" / "test_main.py").is_file()  # a test that fails to import
    done = subprocess.run([sys.executable, "-B", "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider",
                           str(HERE)], cwd=HERE, capture_output=True, text=True, timeout=300)
    assert done.returncode == 0, done.stdout + done.stderr
    assert not [line for line in done.stdout.splitlines() if line.startswith("fixtures/")], done.stdout
