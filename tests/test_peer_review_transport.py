"""Peer-review payload reading and confinement, isolated from MCP/profile setup."""

import ast
import hashlib
import os
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
SERVER = REPO_ROOT / "plugins/peer-review/skills/cross-model-peer-review/scripts/server.py"


def payload_reader():
    """Execute the actual reading function and its function dependencies only."""
    tree = ast.parse(SERVER.read_text(encoding="utf-8"), filename=str(SERVER))
    functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    required, pending = set(), ["_load_payload"]
    while pending:
        name = pending.pop()
        if name in required:
            continue
        required.add(name)
        pending.extend(node.func.id for node in ast.walk(functions[name])
                       if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                       and node.func.id in functions and node.func.id not in required)
    selected = ast.Module(body=[ast.ImportFrom(module="__future__",
                          names=[ast.alias(name="annotations")], level=0),
                          *(functions[name] for name in functions if name in required)], type_ignores=[])
    ast.fix_missing_locations(selected)
    namespace = {"Path": Path, "hashlib": hashlib, "os": os, "stat": stat}
    exec(compile(selected, str(SERVER), "exec"), namespace)
    return namespace["_load_payload"]


class PeerReviewPayloadTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="daodan-peer-payload-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.read_payload = payload_reader()

    def fixture(self, name):
        cwd = self.base / name
        root = cwd / ".peer-review"
        root.mkdir(parents=True)
        return cwd, root

    def assert_rejected_before_read(self, cwd, candidate):
        attempted = []
        original = Path.read_bytes

        def observe_read(path):
            attempted.append(str(path))
            return original(path)

        with patch.object(Path, "cwd", return_value=cwd), \
                patch.object(Path, "read_bytes", observe_read):
            payload, error = self.read_payload(str(candidate))

        self.assertEqual(attempted, [], "Rejected content reached the byte-read boundary")
        self.assertIsNone(payload)
        self.assertIsInstance(error, str)
        self.assertTrue(error)

    def make_directory_link(self, link, target, kind):
        self.assertTrue(link.absolute().is_relative_to(self.base.absolute()))
        self.assertTrue(target.absolute().is_relative_to(self.base.absolute()))
        if kind == "junction":
            created = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)],
                                     capture_output=True, text=True, timeout=10, check=False)
            self.assertEqual(created.returncode, 0, created.stderr)
            self.assertTrue(link.lstat().st_file_attributes & 0x400)
            self.addCleanup(link.rmdir)
        else:
            link.symlink_to(target, target_is_directory=True)
            self.addCleanup(link.unlink)
        self.assertEqual(link.resolve(), target.resolve())

    def test_normal_request_preserves_exact_crlf_bytes_and_digest(self):
        cwd, root = self.fixture("normal")
        request = root / "run/request.txt"
        request.parent.mkdir()
        raw = b"exact outgoing packet\r\nsecond line\r\n"
        request.write_bytes(raw)

        with patch.object(Path, "cwd", return_value=cwd):
            payload, error = self.read_payload(str(request))

        self.assertIsNone(error)
        self.assertEqual(payload, {"text": "exact outgoing packet\r\nsecond line\r\n",
                                  "sha256": hashlib.sha256(raw).hexdigest(),
                                  "bytes": len(raw), "path": str(request.resolve())})

    def test_outside_run_root_is_rejected_before_read(self):
        cwd, root = self.fixture("outside")
        outside = cwd / "owned-outside.txt"
        outside.write_bytes(b"benign owned external content")

        self.assert_rejected_before_read(cwd, outside)

    def test_linked_run_root_is_rejected_before_read(self):
        kinds = ("symlink", "junction") if os.name == "nt" else ("symlink",)
        for kind in kinds:
            with self.subTest(kind=kind):
                cwd, root = self.fixture("root-" + kind)
                target = self.base / ("external-root-" + kind)
                target.mkdir()
                (target / "request.txt").write_bytes(b"benign owned redirected packet")
                root.rmdir()
                self.make_directory_link(root, target, kind)

                self.assert_rejected_before_read(cwd, root / "request.txt")

    def test_linked_child_directory_is_rejected_before_read_even_inside_run_root(self):
        kinds = ("symlink", "junction") if os.name == "nt" else ("symlink",)
        for kind in kinds:
            with self.subTest(kind=kind):
                cwd, root = self.fixture("child-" + kind)
                target = root / "owned-target"
                target.mkdir()
                (target / "request.txt").write_bytes(b"benign owned child packet")
                child = root / "run"
                self.make_directory_link(child, target, kind)

                self.assert_rejected_before_read(cwd, child / "request.txt")

    def test_linked_request_file_is_rejected_before_read_even_inside_run_root(self):
        cwd, root = self.fixture("file-link")
        target = root / "owned-target.txt"
        target.write_bytes(b"benign owned aliased packet")
        request = root / "request.txt"
        request.symlink_to(target)
        self.addCleanup(request.unlink)

        self.assert_rejected_before_read(cwd, request)

    def test_hardlinked_request_is_rejected_before_read(self):
        cwd, root = self.fixture("hardlink")
        target = cwd / "owned-outside.txt"
        target.write_bytes(b"benign owned hardlink packet")
        request = root / "request.txt"
        os.link(target, request)
        self.assertGreater(request.stat().st_nlink, 1)

        self.assert_rejected_before_read(cwd, request)

    def test_invalid_utf8_and_empty_requests_report_errors(self):
        cwd, root = self.fixture("invalid-content")
        for name, raw, message in (("invalid.txt", b"\xff\xfe", "UTF-8"),
                                   ("empty.txt", b" \r\n\t", "empty")):
            with self.subTest(name=name):
                request = root / name
                request.write_bytes(raw)

                with patch.object(Path, "cwd", return_value=cwd):
                    payload, error = self.read_payload(str(request))

                self.assertIsNone(payload)
                self.assertIn(message, error)

    def test_missing_request_is_rejected_without_read(self):
        cwd, root = self.fixture("missing")

        self.assert_rejected_before_read(cwd, root / "run/request.txt")


if __name__ == "__main__":
    unittest.main()
