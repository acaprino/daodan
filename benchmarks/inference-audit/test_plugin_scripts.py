"""The plugin's scripts as the benchmark finds them, and the digests of the graph code a container runs.

    python -B -m pytest -q -p no:cacheprovider benchmarks/inference-audit/test_plugin_scripts.py
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import plugin_scripts  # noqa: E402


# The map's scripts are found from any depth, or the Modal mount is assumed.

def test_scripts_lookup_from_a_shallow_folder(tmp_path):
    (tmp_path / "plugin_scripts.py").write_bytes((HERE / "plugin_scripts.py").read_bytes())
    code = "import sys; sys.path.insert(0, '.'); import plugin_scripts; print(plugin_scripts.SCRIPTS.as_posix())"
    found = subprocess.run([sys.executable, "-I", "-c", code],
                           cwd=tmp_path, capture_output=True, text=True, timeout=60)
    assert found.returncode == 0, found.stderr
    assert found.stdout.strip() in ("/daodan/map/scripts",
                                    *(str(parent / "plugins/codebase-map/skills/map/scripts").replace("\\", "/")
                                      for parent in tmp_path.parents))


def test_code_digests_name_the_graph_module_each_indexer_and_each_adapter():
    digests = plugin_scripts.code_sha256()
    assert {"code_graph.py", "indexers/go.py", "indexers/kotlin.py", "adapters/clang.py"} \
        <= set(digests)
    assert all(len(value) == 12 for value in digests.values())
