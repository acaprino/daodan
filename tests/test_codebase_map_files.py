"""snapshot.py files lists the snapshot inventory: path, content hash, size and language."""
import hashlib
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "plugins/codebase-map/skills/map/scripts"
sys.path.insert(0, str(SCRIPTS))
import snapshot

FILES = {
    "pkg/a.py": b"def f():\n    return 1\n",
    "web/b.ts": b"export const x = 1;\n",
    "README.md": b"# Fixture\n",
}


class SnapshotFilesTest(unittest.TestCase):
    def test_files_lists_every_snapshot_file(self):
        with tempfile.TemporaryDirectory(prefix="map-files-") as tmp:
            base = Path(tmp).resolve()
            root = base / "tree"
            for rel, data in FILES.items():
                path = root / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
            manifest = base / "manifest.sqlite"
            snapshot.write_snapshot(root, manifest)
            dest = base / "FILES.json"
            out = StringIO()
            with redirect_stdout(out):
                code = snapshot.main(["files", str(manifest), "--out", str(dest)])

            self.assertEqual(code, 0)
            self.assertEqual(json.loads(out.getvalue()), {"files": 3})
            payload = json.loads(dest.read_text(encoding="utf-8"))
            self.assertEqual(payload["schema"], "codebase-map/files/v1")
            self.assertEqual(payload["manifest"], manifest.as_posix())
            self.assertEqual([row["path"] for row in payload["files"]], ["README.md", "pkg/a.py", "web/b.ts"])
            rows = {row["path"]: row for row in payload["files"]}
            for rel, data in FILES.items():
                self.assertEqual(rows[rel]["sha256"], hashlib.sha256(data).hexdigest())
                self.assertEqual(rows[rel]["size"], len(data))
                self.assertIsInstance(rows[rel]["lines"], int)
            self.assertEqual(rows["pkg/a.py"]["language"], "python")
            self.assertEqual(rows["web/b.ts"]["language"], "typescript")


if __name__ == "__main__":
    unittest.main()
