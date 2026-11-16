"""The Python analyzer's runs when a project sits inside a checkout that holds more Python code."""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "plugins/codebase-map/skills/map/scripts"))

from indexers import python  # noqa: E402


def test_a_project_folded_into_the_checkout_run_keeps_its_folder_as_the_root_of_its_imports(tmp_path):
    """The files of a Python project import each other from its folder; the code outside it sees the declared
    source roots only: a module found by name in a project's folder from outside would be a guess."""
    (tmp_path / "pkg" / "src").mkdir(parents=True)
    target = tmp_path / "pyrightconfig.json.out"
    config = python._pyright_config(tmp_path, target, ["pkg/src"], ["pkg", "tools/lint"])
    assert config == json.loads(target.read_text(encoding="utf-8")) == {"executionEnvironments": [
        {"root": "pkg/src"}, {"root": "pkg", "extraPaths": ["pkg/src"]}, {"root": "tools/lint", "extraPaths": ["pkg/src"]},
        {"root": ".", "extraPaths": ["pkg/src"]}]}
