"""Binary snapshots preserve facts without retaining the whole inventory."""
from __future__ import annotations

from contextlib import closing
import hashlib
import importlib
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1] / "plugins/codebase-map/skills/map-method/scripts"
sys.path.insert(0, str(SCRIPTS))
import snapshot


class SnapshotStorageTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="map-storage-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        (self.root / "one.py").write_text("VALUE = 7\n\ndef answer():\n    return VALUE\n", encoding="utf-8")

    def api(self):
        self.assertTrue(hasattr(snapshot, "write_snapshot"), "snapshot requires the streaming write_snapshot API")
        return importlib.import_module("snapshot_store")

    def out(self, name="manifest.sqlite"):
        return self.root / ".codebase-map" / name

    def test_default_is_sqlite(self):
        storage = self.api()
        with mock.patch.object(snapshot, "build_manifest", side_effect=AssertionError("whole manifest built")):
            result = snapshot.write_snapshot(self.root, self.out())
        self.assertEqual(self.out().read_bytes()[:16], b"SQLite format 3\x00")
        self.assertEqual(result["metrics"]["parsed_files"], 1)
        with storage.open_snapshot(self.out(), expected_format="sqlite") as store:
            self.assertEqual(store.format, "sqlite")
            self.assertEqual(store.file_count, 1)
            self.assertEqual(store.get_file("one.py")["language"], "python")
            self.assertIsNone(store.get_file("missing.py"))
        with self.assertRaisesRegex(ValueError, "closed"):
            store.get_file("one.py")

    def test_progress_reports_observed_work_and_additional_metadata_is_bound(self):
        storage = self.api()
        events = []
        snapshot.write_snapshot(self.root, self.out(), extra_metadata={"host": {"checkout": "one", "generation": 1}},
                                progress=lambda phase, count: events.append((phase, count)))
        self.assertIn(("reading", 1), events)
        self.assertIn(("parsing", 1), events)
        self.assertEqual(events[-1], ("validating", 1))
        with storage.open_snapshot(self.out()) as store:
            self.assertEqual(store.metadata["host"], {"checkout": "one", "generation": 1})
        before = self.out().read_bytes()
        with self.assertRaisesRegex(ValueError, "metadata"):
            snapshot.write_snapshot(self.root, self.out(), extra_metadata={"root": "foreign"})
        def cancel(phase, count):
            if phase == "reading":
                raise ValueError("cancelled")
        with self.assertRaisesRegex(ValueError, "cancelled"):
            snapshot.write_snapshot(self.root, self.out(), progress=cancel)
        self.assertEqual(self.out().read_bytes(), before)
        self.assertEqual(list(self.out().parent.iterdir()), [self.out()])

    def test_explicit_json_roundtrip_and_reuse(self):
        storage = self.api()
        snapshot.write_snapshot(self.root, self.out("first.json"), format="json")
        self.assertEqual(json.loads(self.out("first.json").read_text())["schema"], snapshot.SCHEMA)
        with storage.open_snapshot(self.out("first.json")) as previous:
            self.assertEqual(previous.format, "json")
            original = previous.get_file("one.py")
            with mock.patch.object(snapshot, "file_entry", side_effect=AssertionError("unchanged file parsed")):
                result = snapshot.write_snapshot(self.root, self.out(), previous=previous)
            self.assertEqual(result["metrics"]["cache_hits"], 1)
        with storage.open_snapshot(self.out()) as current:
            self.assertEqual(current.get_file("one.py"), original)

    def test_unicode_and_fact_order_roundtrip(self):
        storage = self.api()
        (self.root / "caf\u00e9.py").write_text("def caf\u00e9():\n    return '\u4e2d\U0001f600'\n", encoding="utf-8")
        expected = snapshot.build_manifest(self.root)["files"]
        for format in ("sqlite", "json"):
            out = self.out("facts." + format)
            snapshot.write_snapshot(self.root, out, format=format)
            with storage.open_snapshot(out) as store:
                self.assertEqual(dict(store.iter_files()), expected)
                self.assertEqual(sorted(store.iter_symbols(path="caf\u00e9.py"), key=lambda row: row["name"])[0]["name"], "caf\u00e9")

    def test_unrecognized_header_and_schema_refused(self):
        storage = self.api()
        self.out().parent.mkdir()
        self.out().write_bytes(b"not a snapshot")
        with self.assertRaises(ValueError):
            storage.open_snapshot(self.out())
        self.out().unlink()
        with closing(sqlite3.connect(self.out())) as database:
            database.execute("PRAGMA user_version=1")
            database.execute("CREATE TABLE unrelated(value)")
        with self.assertRaisesRegex(ValueError, "application|snapshot"):
            storage.open_snapshot(self.out())
        self.out().unlink()
        snapshot.write_snapshot(self.root, self.out())
        with closing(sqlite3.connect(self.out())) as database:
            database.execute("PRAGMA user_version=99")
        with self.assertRaisesRegex(ValueError, "version"):
            storage.open_snapshot(self.out())

    def test_writer_releases_prior_entries(self):
        self.api()
        for number in range(18):
            (self.root / f"entry{number}.py").write_text(f"VALUE = {number}\n")
        original = snapshot.file_entry
        alive, peak = 0, 0
        class Observed(dict):
            def __init__(self, value):
                nonlocal alive, peak
                super().__init__(value)
                alive += 1
                peak = max(peak, alive)
            def __del__(self):
                nonlocal alive
                alive -= 1
        def entry(*args, **kwargs):
            return Observed(original(*args, **kwargs))
        with mock.patch.object(snapshot, "file_entry", side_effect=entry):
            result = snapshot.write_snapshot(self.root, self.out())
        self.assertEqual(result["metrics"]["files_read"], 19)
        self.assertLessEqual(peak, 2, "writer retained previous parsed entries")

    def test_failed_write_preserves_current_and_cleans_temporary(self):
        self.api()
        snapshot.write_snapshot(self.root, self.out())
        before = self.out().read_bytes()
        with mock.patch.object(snapshot, "file_entry", side_effect=RuntimeError("cancelled")):
            with self.assertRaisesRegex(RuntimeError, "cancelled"):
                snapshot.write_snapshot(self.root, self.out())
        self.assertEqual(self.out().read_bytes(), before)
        self.assertEqual([path.name for path in self.out().parent.iterdir()], ["manifest.sqlite"])

    def test_logical_and_artifact_digests_are_distinct_and_streamed(self):
        storage = self.api()
        snapshot.write_snapshot(self.root, self.out())
        with storage.open_snapshot(self.out()) as store:
            logical = {**store.metadata, "files": dict(store.iter_files())}
            for ascii in (True, False):
                expected = hashlib.sha256(json.dumps(logical, sort_keys=True, ensure_ascii=ascii,
                                                    separators=(",", ":")).encode()).hexdigest()
                self.assertEqual(storage.logical_digest(store, ensure_ascii=ascii), expected)
            self.assertEqual(storage.artifact_digest(self.out()), hashlib.sha256(self.out().read_bytes()).hexdigest())
            with mock.patch.object(Path, "read_text", side_effect=AssertionError("whole file text read")):
                self.assertEqual(store.get_file("one.py")["language"], "python")

    def test_unknown_semantic_fields_are_preserved(self):
        storage = self.api()
        original = snapshot.file_entry
        def extra(*args, **kwargs):
            value = original(*args, **kwargs)
            value["semantic"]["_stored_lists"] = ["retained"]
            value["semantic"]["future"] = {"flag": False, "notes": ["one", "two"]}
            return value
        with mock.patch.object(snapshot, "file_entry", side_effect=extra):
            snapshot.write_snapshot(self.root, self.out())
        with storage.open_snapshot(self.out()) as store:
            self.assertEqual(store.get_file("one.py")["semantic"]["_stored_lists"], ["retained"])
            self.assertEqual(store.get_file("one.py")["semantic"]["future"]["flag"], False)

    def test_corrupt_compressed_record_is_refused(self):
        storage = self.api()
        snapshot.write_snapshot(self.root, self.out())
        with closing(sqlite3.connect(self.out())) as database:
            database.execute("UPDATE files SET header=?", (b"znot-valid-zlib",))
            database.commit()
        with storage.open_snapshot(self.out()) as store:
            with self.assertRaises(ValueError):
                store.get_file("one.py")

    def test_corrupt_record_shapes_raise_storage_errors(self):
        storage = self.api()
        from snapshot_store import _pack
        snapshot.write_snapshot(self.root, self.out())
        for column, value in (("header", []), ("semantic_header", {"header": [], "lists": ["references"]}),
                              ("semantic_header", {"header": {}, "lists": ["unknown"]})):
            with self.subTest(column=column, value=value):
                with closing(sqlite3.connect(self.out())) as database:
                    database.execute(f"UPDATE files SET {column}=? WHERE path='one.py'", (_pack(value),))
                    database.commit()
                with storage.open_snapshot(self.out()) as store:
                    with self.assertRaises(ValueError):
                        store.get_file("one.py")
                snapshot.write_snapshot(self.root, self.out())

    def test_replacing_reused_path_closes_its_reader_before_publication(self):
        storage = self.api()
        snapshot.write_snapshot(self.root, self.out())
        with storage.open_snapshot(self.out()) as previous:
            result = snapshot.write_snapshot(self.root, self.out(), previous=previous)
            self.assertTrue(previous.closed)
            self.assertEqual(result["metrics"]["cache_hits"], 1)
        with storage.open_snapshot(self.out()) as current:
            self.assertEqual(current.file_count, 1)

    def test_nonstring_format_is_refused(self):
        self.api()
        with self.assertRaises(ValueError):
            snapshot.write_snapshot(self.root, self.out(), format=[])

    def test_json_stream_handles_utf8_chunks_and_rejects_duplicates(self):
        storage = self.api()
        import json_snapshot
        (self.root / "caf\u00e9.py").write_text("def caf\u00e9():\n    return '\u4e2d\U0001f600'\n", encoding="utf-8")
        value = snapshot.build_manifest(self.root)
        self.out().parent.mkdir()
        self.out("unicode.json").write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
        with mock.patch.object(json_snapshot, "CHUNK_BYTES", 13):
            with storage.open_snapshot(self.out("unicode.json")) as store:
                self.assertEqual(dict(store.iter_files()), value["files"])
        duplicate = '{"schema":1,"root":".","target":".","files":{"a":{},"a":{}}}'
        self.out("duplicate.json").write_text(duplicate, encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "duplicate"):
            storage.open_snapshot(self.out("duplicate.json"))

    def test_json_numbers_across_every_decimal_and_exponent_chunk_boundary(self):
        storage = self.api()
        import json_snapshot
        prefix = b'{"files":{},"schema":1,"root":".","target":".","score":'
        self.out().parent.mkdir()
        path = self.out("numbers.json")
        for token in (b"1e3", b"1.25", b"-12.5e-2", b"123E+4"):
            for split in range(1, len(token)):
                with self.subTest(token=token, split=split):
                    payload = prefix + b" " * (json_snapshot.CHUNK_BYTES - len(prefix) - split) + token + b"}"
                    path.write_bytes(payload)
                    with storage.open_snapshot(path, expected_format="json") as store:
                        self.assertEqual(store.metadata["score"], json.loads(payload)["score"])

    def test_nonfinite_overflow_is_rejected_in_json_and_sqlite_records(self):
        storage = self.api()
        self.out().parent.mkdir()
        for number in (b"1e400", b"-1e400", b"NaN", b"Infinity", b"-Infinity"):
            with self.subTest(number=number):
                path = self.out("invalid.json")
                path.write_bytes(b'{"files":{},"schema":1,"root":".","target":".","score":' + number + b'}')
                with self.assertRaisesRegex(ValueError, "non-finite"):
                    storage.open_snapshot(path, expected_format="json")
                with self.assertRaises(ValueError):
                    storage._unpack(b"j" + number)

    def test_format_mismatch_and_invalid_format_do_not_write(self):
        storage = self.api()
        snapshot.write_snapshot(self.root, self.out())
        with self.assertRaisesRegex(ValueError, "format"):
            storage.open_snapshot(self.out(), expected_format="json")
        with self.assertRaisesRegex(ValueError, "format"):
            snapshot.write_snapshot(self.root, self.out("invalid"), format="pickle")
        self.assertFalse(self.out("invalid").exists())


if __name__ == "__main__":
    unittest.main()
