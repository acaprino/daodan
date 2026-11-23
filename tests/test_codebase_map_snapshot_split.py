"""The snapshot in two writes, the inventory and the reading, is the store of the single pass (spec 8.10, proof 1).

docs/specs/2026-11-15-pipeline-di-analisi.md, 8.6 and 8.11 (steps 1-2). The single pass is `snapshot.build_manifest`,
which walks and parses the tree in one go: on the graph fixtures its files and header are the store's, so the two
writes must give the same logical digest, `created_at` aside.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1] / "daodan/core"
sys.path.insert(0, str(SCRIPTS))
import snapshot  # noqa: E402
import snapshot_store  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures"
GRAPHS = sorted(path for base in ("code-graph", "css-graph", "clang-reader")
                for path in (FIXTURES / base).iterdir() if path.is_dir())


def _keys(store) -> list[str]:
    return sorted((set(store.metadata) | {"files"}) - {"created_at"})


def _single_pass_digest(manifest: dict, keys: list[str]) -> str:
    """`logical_digest` of the single pass's manifest over `keys` (the same JSON `logical_chunks` streams)."""
    return hashlib.sha256(json.dumps({key: manifest.get(key) for key in keys}, sort_keys=True, ensure_ascii=True,
                                     separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()


class SnapshotSplitTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="map-split-")
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name).resolve()

    def tree(self, fixture: Path) -> Path:
        root = self.base / fixture.parent.name / fixture.name
        shutil.copytree(fixture, root)
        return root

    def test_inventory_then_reading_is_the_single_pass(self):
        import file_inventory
        for fixture in GRAPHS:
            with self.subTest(fixture=f"{fixture.parent.name}/{fixture.name}"):
                root = self.tree(fixture)
                inventory, out = root.parent / f"{root.name}.inventory.sqlite", root.parent / f"{root.name}.sqlite"
                file_inventory.write(root, inventory)
                single = snapshot.build_manifest(root)
                with snapshot_store.open_snapshot(inventory) as store:
                    self.assertEqual(store.file_count, 0, "the inventory holds no reading")
                    rows = dict(store.iter_inventory())
                self.assertEqual(list(rows), list(single["files"]), "every file of the single pass, in its order")
                for path, row in rows.items():
                    entry = single["files"][path]
                    self.assertEqual({key: row[key] for key in ("size", "mtime", "raw_hash", "language")},
                                     {key: entry[key] for key in ("size", "mtime", "raw_hash", "language")}, path)
                snapshot.write_reading(inventory, out)
                with snapshot_store.open_snapshot(out) as store:
                    keys = _keys(store)
                    self.assertEqual(set(keys), set(single) - {"created_at"})
                    self.assertEqual(snapshot_store.logical_digest(store, keys=keys), _single_pass_digest(single, keys))
                    self.assertEqual(dict(store.iter_inventory()), rows, "the store keeps the inventory it read")
                snapshot.write_snapshot(root, out)  # the two writes behind the one call every caller makes
                with snapshot_store.open_snapshot(out) as store:
                    self.assertEqual(snapshot_store.logical_digest(store, keys=keys), _single_pass_digest(single, keys))

    def test_the_reading_takes_files_and_language_from_the_inventory(self):
        import file_inventory
        root = self.base / "tree"
        root.mkdir()
        (root / "shape.h").write_text("int area(int side);\n", encoding="utf-8")
        (root / "main.py").write_text("def main():\n    return 1\n", encoding="utf-8")
        inventory, out = self.base / "inventory.sqlite", self.base / "manifest.sqlite"
        detect = file_inventory.detect_language
        with mock.patch.object(file_inventory, "detect_language",
                               side_effect=lambda path, text: "cpp" if path.suffix == ".h" else detect(path, text)):
            file_inventory.write(root, inventory)
        with mock.patch.object(snapshot, "iter_files", side_effect=AssertionError("the reading walked the tree")), \
                mock.patch.object(snapshot, "detect_language", side_effect=AssertionError("the reading chose a language")):
            snapshot.write_reading(inventory, out)
        with snapshot_store.open_snapshot(out) as store:
            self.assertEqual(sorted(store.iter_paths()), ["main.py", "shape.h"])
            self.assertEqual(store.get_file("shape.h")["language"], "cpp")
            self.assertEqual(store.get_file("shape.h")["parser_profile"], snapshot.parser_profile(root / "shape.h", "cpp"))
            self.assertEqual(store.get_file("main.py")["language"], "python")

    def test_a_file_changed_between_the_two_writes_is_recorded_as_read(self):
        import file_inventory
        root = self.base / "tree"
        root.mkdir()
        (root / "one.py").write_text("VALUE = 1\n", encoding="utf-8")
        inventory, out = self.base / "inventory.sqlite", self.base / "manifest.sqlite"
        file_inventory.write(root, inventory)
        (root / "one.py").write_text("VALUE = 22\n\ndef later():\n    return VALUE\n", encoding="utf-8")
        snapshot.write_reading(inventory, out)
        with snapshot_store.open_snapshot(out) as store:
            entry = store.get_file("one.py")
            row = dict(store.iter_inventory())["one.py"]
        data = (root / "one.py").read_bytes()
        self.assertEqual(entry["raw_hash"], hashlib.sha256(data).hexdigest())
        self.assertIn("later", entry["symbols"])
        self.assertEqual({key: row[key] for key in ("size", "mtime", "raw_hash", "language")},
                         {key: entry[key] for key in ("size", "mtime", "raw_hash", "language")})


if __name__ == "__main__":
    unittest.main()
