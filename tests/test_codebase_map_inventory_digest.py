"""What `scan` and `recognize` write is bound to the inventory's digest, not the reading's (spec of the pipeline, 8.6 point 2;
8.11 step 5, piece C).

The pre-map, the structure of the module graph and the technologies read no symbol, so a new reading of the same files (another
parser's identity: the logical digest changes) leaves them fresh, and only the module graph's `imports` and `calls`, which read
the symbols, are computed again; a file whose bytes change makes them all stale.
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "daodan/core"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import modules  # noqa: E402
import pipeline  # noqa: E402
import premap  # noqa: E402
import snapshot  # noqa: E402
import technologies  # noqa: E402
from snapshot_store import logical_digest, open_snapshot  # noqa: E402
from test_codebase_map_module_edges_in_connect import FILES  # noqa: E402
from test_codebase_map_premap_container_runner import manifest_of  # noqa: E402


def _scanned(tmp_path):
    root, manifest = manifest_of(tmp_path, FILES)
    pipeline.run(manifest, stop="scan", fast_scan=True)
    modules.ensure_graph(manifest)
    return root, manifest


def _digest(manifest) -> str:
    with open_snapshot(manifest) as store:
        return logical_digest(store)


def test_a_new_reading_of_the_same_files_leaves_the_pre_map_the_modules_and_the_technologies_fresh(tmp_path):
    root, manifest = _scanned(tmp_path)
    before = _digest(manifest)
    with mock.patch.object(snapshot, "parser_fingerprint", return_value="another parser"):
        snapshot.read_project(root, manifest)
    assert _digest(manifest) != before  # the reading changed
    # the modules first: `technologies.state` ensures the module graph itself
    assert modules.graph_state(manifest)["state"] == "fresh"
    assert premap.state(manifest)["state"] == "fresh"
    assert technologies.state(manifest) == "fresh"
    assert modules.ensure_graph(manifest)["action"] == "completed"  # only the edges that read the symbols again


def test_a_changed_file_makes_them_all_stale(tmp_path):
    root, manifest = _scanned(tmp_path)
    (root / "libs/b/index.ts").write_text("export function b() {\n  return 2;\n}\n", encoding="utf-8")
    snapshot.read_project(root, manifest)
    assert modules.graph_state(manifest)["state"] == "stale"
    assert premap.state(manifest)["state"] == "stale"
    assert technologies.state(manifest) == "stale"
