"""The snapshot in two writes, the inventory and the reading (spec 8.6 and 8.11, steps 1-2).

`read_project` stages the inventory and reads it: the reading takes the files and their language from the inventory and
keeps its rows. Proof 1 of 8.10 compared that with the single pass (`build_manifest`), removed on 24 November 2026; what is
compared now is the reading with `read_project` and with the JSON snapshot, and the inventory's order with the walk's.
"""
from __future__ import annotations

import hashlib
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


class SnapshotSplitTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="map-split-")
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name).resolve()

    def tree(self, fixture: Path) -> Path:
        root = self.base / fixture.parent.name / fixture.name
        shutil.copytree(fixture, root)
        return root

    def test_inventory_then_reading_is_what_read_project_writes_in_both_formats_and_keeps_the_walk(self):
        """On the graph fixtures: the inventory lists the files in the walk's order, and its reading, `read_project` (the
        two writes in one call) and the JSON snapshot have the same keys and the same logical digest."""
        import file_inventory
        for fixture in GRAPHS:
            with self.subTest(fixture=f"{fixture.parent.name}/{fixture.name}"):
                root = self.tree(fixture)
                inventory, split, together, as_json = (root.parent / f"{root.name}.{name}" for name in
                                                       ("inventory.sqlite", "split.sqlite", "together.sqlite", "json"))
                file_inventory.write(root, inventory)
                with snapshot_store.open_snapshot(inventory) as store:
                    self.assertEqual(store.file_count, 0, "the inventory holds no reading")
                    rows = dict(store.iter_inventory())
                top = snapshot.repo_root(root).resolve()
                self.assertEqual(list(rows), [snapshot.relative_to_root(path, top) for path in snapshot.iter_files(root)])
                snapshot.write_reading(inventory, split)
                snapshot.read_project(root, together)
                snapshot.read_project(root, as_json, format="json")
                seen = {}
                for name, path in (("split", split), ("together", together), ("json", as_json)):
                    with snapshot_store.open_snapshot(path) as store:
                        keys = _keys(store)
                        seen[name] = (set(keys), snapshot_store.logical_digest(store, keys=keys))
                        if name == "split":
                            entries = dict(store.iter_files())
                            self.assertEqual(dict(store.iter_inventory()), rows, "the store keeps the inventory it read")
                self.assertEqual(seen["together"], seen["split"])
                self.assertEqual(seen["json"], seen["split"])
                self.assertEqual(sorted(entries), sorted(rows), "every file of the inventory")
                for path, row in rows.items():  # the reading measures the bytes again: the inventory's numbers hold
                    self.assertEqual({key: row[key] for key in ("size", "mtime", "raw_hash")},
                                     {key: entries[path][key] for key in ("size", "mtime", "raw_hash")}, path)

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

    def test_the_header_counts_the_files_no_reader_reads_by_linguists_name_and_type(self):
        """`.rb` is not in the inventory and none of its bytes is read; `.php` is, with no language of Daodan's. Both
        are counted from their names alone: a suffix several languages list stays under the suffix, a name Linguist
        does not give is `Unknown`, and a file Daodan reads is not counted."""
        import file_inventory
        root = self.base / "tree"
        root.mkdir()
        for name in ("app.rb", "lib.rb", "index.php", "main.py", "data.xyzzy", "Dockerfile", "docs/guide.txt"):
            (root / name).parent.mkdir(exist_ok=True)
            (root / name).write_text("x = 1\n", encoding="utf-8")
        inventory = self.base / "inventory.sqlite"
        header = file_inventory.write(root, inventory)
        self.assertEqual(header["excluded"], [{"path": "docs/", "why": "documentation"}])  # Linguist's `^[Dd]ocs?/`
        with snapshot_store.open_snapshot(inventory) as store:
            rows = dict(store.iter_inventory())
        self.assertNotIn("app.rb", rows)
        self.assertEqual(header["metrics"]["files_read"], len(rows))  # `.rb` and `.xyzzy` are not among the reads
        self.assertEqual(header["unread"]["Ruby"], {"type": "programming", "files": 2})
        self.assertEqual(header["unread"][".php"], {"type": "programming", "files": 1, "candidates": ["Hack", "PHP"]})
        self.assertEqual(header["unread"]["Unknown"], {"type": "Unknown", "files": 1})
        self.assertNotIn("Python", header["unread"])
        split = self.base / "manifest.sqlite"
        snapshot.write_reading(inventory, split)
        with snapshot_store.open_snapshot(split) as store:
            self.assertEqual(store.get("unread"), header["unread"], "the snapshot keeps what the inventory counted")
            self.assertEqual(store.get("excluded"), header["excluded"], "and what it left out")

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


    def test_a_previous_store_is_reused_only_where_the_file_and_its_language_still_hold(self):
        """Between the two writes one file is edited, one removed, one grows past the size limit: none of them keeps
        its previous entry, even on the bulk copy from a SQLite snapshot. A header from the inventory with another
        language than the previous entry's is read again in the inventory's language."""
        import file_inventory
        root = self.base / "tree"
        root.mkdir()
        for name, text in (("a.py", "A = 1\n"), ("b.py", "B = 1\n"), ("c.py", "C = 1\n"), ("d.py", "D = 1\n"),
                           ("shape.h", "int area(int side);\n")):
            (root / name).write_text(text, encoding="utf-8")
        previous_path, inventory, out = (self.base / f"{name}.sqlite" for name in ("previous", "inventory", "out"))
        snapshot.read_project(root, previous_path)
        detect = file_inventory.detect_language
        with mock.patch.object(file_inventory, "detect_language",
                               side_effect=lambda path, text: "cpp" if path.suffix == ".h" else detect(path, text)):
            file_inventory.write(root, inventory)
        (root / "b.py").write_text("B = 22\n\ndef later():\n    return B\n", encoding="utf-8")
        (root / "c.py").unlink()
        (root / "d.py").write_text("D = 1\n" + "# padding\n" * 50, encoding="utf-8")
        with mock.patch.object(file_inventory, "MAX_FILE_BYTES", 200), \
                snapshot_store.open_snapshot(previous_path) as previous:
            kept = previous.get_file("a.py")
            snapshot.write_reading(inventory, out, previous=previous)
        with snapshot_store.open_snapshot(out) as store:
            files, rows = dict(store.iter_files()), dict(store.iter_inventory())
        self.assertEqual(sorted(files), ["a.py", "b.py", "shape.h"])
        self.assertEqual(sorted(rows), sorted(files))
        self.assertEqual(files["a.py"], kept)
        self.assertEqual(files["b.py"]["raw_hash"], hashlib.sha256((root / "b.py").read_bytes()).hexdigest())
        self.assertIn("later", files["b.py"]["symbols"])
        self.assertEqual(files["shape.h"]["language"], "cpp", "the inventory's language, not the previous entry's")
        for path, entry in files.items():
            self.assertEqual({key: rows[path][key] for key in ("size", "mtime", "raw_hash", "language")},
                             {key: entry[key] for key in ("size", "mtime", "raw_hash", "language")}, path)

    def test_json_and_sqlite_give_the_same_store_and_supplied_content_is_read(self):
        root = self.base / "tree"
        root.mkdir()
        (root / "one.py").write_text("def one():\n    return 1\n", encoding="utf-8")
        (root / "two.py").write_text("def two():\n    return 2\n", encoding="utf-8")
        supplied = {str(root / "two.py"): ("def edited():\n    return 22\n", None)}
        digests = {}
        for format in ("sqlite", "json"):
            with self.subTest(format=format):
                out = self.base / f"manifest.{format}"
                snapshot.read_project(root, out, format=format, parse_results=supplied)
                with snapshot_store.open_snapshot(out) as store:
                    digests[format] = snapshot_store.logical_digest(store, keys=_keys(store))
                    self.assertIn("edited", store.get_file("two.py")["symbols"])
        self.assertEqual(digests["json"], digests["sqlite"])

    def test_a_refused_write_creates_nothing(self):
        out = self.base / "absent" / "deeper" / "manifest.sqlite"
        with self.assertRaisesRegex(ValueError, "does not exist"):
            snapshot.read_project(self.base / "missing", out)
        self.assertFalse((self.base / "absent").exists())

    def test_the_reading_refuses_a_store_that_is_not_an_inventory(self):
        root = self.base / "tree"
        root.mkdir()
        (root / "one.py").write_text("VALUE = 1\n", encoding="utf-8")
        read = self.base / "read.sqlite"
        snapshot.read_project(root, read)
        with self.assertRaisesRegex(ValueError, "inventory"):
            snapshot.write_reading(read, self.base / "again.sqlite")
        self.assertFalse((self.base / "again.sqlite").exists())

    def test_the_reading_is_written_by_read_project_alone(self):
        """One path reads the files (the owner's decision of 24 November 2026): no module of the product calls
        `write_reading` but `snapshot.py`, whose `read_project` stages the inventory and reads it, and none defines, calls
        or exports `build_manifest` (nor the old name of `read_project`), the single pass that read them a second way. The names are found in each module's
        syntax tree (`ast`, Python's own parser)."""
        import ast
        product = SCRIPTS.parent
        found = []
        for path in sorted(product.rglob("*.py")):
            names = {"build_manifest", "write_" + "snapshot"} | (set() if path == Path(snapshot.__file__).resolve() else {"write_reading"})
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                name = (node.name if isinstance(node, (ast.FunctionDef, ast.alias)) else node.attr
                        if isinstance(node, ast.Attribute) else node.id if isinstance(node, ast.Name)
                        else node.value if isinstance(node, ast.Constant) else None)
                if name in names:
                    found.append(f"{path.relative_to(product).as_posix()}:{node.lineno} {name}")
        self.assertEqual(found, [])


if __name__ == "__main__":
    unittest.main()
