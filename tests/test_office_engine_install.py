"""Office engine installer: pinned official releases, approval, integrity and confinement.

Search-before-write found no suite for engine installation; test_office_deckcraft.py
covers the bridge's argument transport and test_office_gridcraft.py the method text.
Archives are built in owned temporary directories and the network is replaced by an
in-memory response, so nothing is downloaded. Target runtime: under 10 seconds.
"""

import contextlib
import hashlib
import importlib.util
import io
import json
import re
import stat
import sys
import tarfile
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

ROOT = next(parent for parent in Path(__file__).resolve().parents
            if (parent / "plugins/office/skills").is_dir())
SKILLS = ROOT / "plugins/office/skills"
KEY = "windows-x64"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


engine = load(SKILLS / "intake/scripts/engine_install.py", "office_test_engine_install")
bridge = load(SKILLS / "deckcraft/scripts/deckcraft_bridge.py", "office_test_engine_bridge")
TOP = "deckcraft-0.10.0-windows-x64-portable"


def zip_bytes(members):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as bundle:
        for name, data in members.items():
            bundle.writestr(name, data)
    return buffer.getvalue()


GOOD = zip_bytes({f"{TOP}/deckcraft-cli.exe": b"cli", f"{TOP}/LICENSE-MIT": b"mit"})


def fetcher(blob, calls=None):
    def fetch(url, destination, size, digest):
        if calls is not None:
            calls.append(url)
        Path(destination).write_bytes(blob)
    return fetch


class EngineInstallTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="daodan engines ")
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name).resolve()
        self.env = {"DAODAN_ENGINE_HOME": str(self.home)}

    def install(self, blob=GOOD, approved=True, calls=None, check=lambda *args: None):
        return engine.install("deckcraft", approved, self.env, KEY, fetcher(blob, calls), check)

    def test_pins_are_well_formed_and_agree_with_their_readers(self):
        for name, spec in engine.ENGINES.items():
            runtime = (SKILLS / name / "references/runtime.md").read_text(encoding="utf-8")
            self.assertIn(f"v{spec['version']}", runtime, name)
            for key, (asset, size, digest) in spec["assets"].items():
                with self.subTest(engine=name, platform=key):
                    self.assertTrue(asset.startswith(name) and spec["version"] in asset)
                    self.assertGreater(size, 0)
                    self.assertRegex(digest, r"^[0-9a-f]{64}$")
                    self.assertEqual(engine.plan(name, self.env, key)["url"],
                                     f"https://github.com/storytold/{name}/releases/download/v{spec['version']}/{asset}")
        self.assertEqual(engine.ENGINES["deckcraft"]["version"], bridge.REFERENCE_VERSION)

    def test_plan_and_unsupported_platforms_touch_no_network(self):
        with mock.patch.object(engine.urllib.request, "urlopen", side_effect=AssertionError("network")):
            self.assertEqual(engine.plan("gridcraft", self.env, KEY)["destination"],
                             str(self.home / "gridcraft" / "0.11.1"))
        with self.assertRaises(engine.InstallError):
            engine.platform_key("freebsd", "x86_64")
        with self.assertRaises(engine.InstallError):
            engine.plan("deckcraft", self.env, "windows-arm64")
        with self.assertRaises(engine.InstallError):
            engine.plan("officecli", self.env, KEY)

    def test_nothing_is_fetched_without_approval(self):
        calls = []
        with self.assertRaisesRegex(engine.InstallError, "approval"):
            self.install(approved=False, calls=calls)
        self.assertEqual((calls, list(self.home.iterdir())), ([], []))

    def test_approved_install_unpacks_proves_and_is_found_without_a_second_fetch(self):
        calls = []
        result = self.install(calls=calls)
        binary = Path(result["binary"])
        self.assertEqual((result["status"], binary.name), ("installed", "deckcraft-cli.exe"))
        self.assertTrue(binary.is_relative_to(self.home / "deckcraft" / "0.10.0"))
        receipt = json.loads((self.home / "deckcraft/0.10.0/.daodan-engine.json").read_text(encoding="utf-8"))
        self.assertEqual((receipt["sha256"], receipt["version"]),
                         (engine.ENGINES["deckcraft"]["assets"][KEY][2], "0.10.0"))
        self.assertEqual(engine.find("deckcraft", self.env), binary)
        again = self.install(approved=False, calls=calls)
        self.assertEqual((again["status"], len(calls)), ("present", 1))
        self.assertEqual([path.name for path in (self.home / "deckcraft").iterdir()], ["0.10.0"])

    def test_failed_proof_leaves_no_install(self):
        def refuse(*args):
            raise engine.InstallError("wrong version")
        with self.assertRaisesRegex(engine.InstallError, "wrong version"):
            self.install(check=refuse)
        self.assertEqual(list((self.home / "deckcraft").iterdir()), [])
        self.assertIsNone(engine.find("deckcraft", self.env))

    def test_download_checks_size_and_digest_before_anything_is_unpacked(self):
        data = b"x" * 10
        digest = hashlib.sha256(data).hexdigest()
        target = self.home / "asset.zip"
        for served, size, sha in ((data, 10, digest), (data, 10, "0" * 64), (data + b"y", 10, digest), (data, 11, digest)):
            with self.subTest(size=size, sha=sha[:4], served=len(served)):
                with mock.patch.object(engine.urllib.request, "urlopen", return_value=io.BytesIO(served)):
                    if served == data and size == 10 and sha == digest:
                        engine.download("https://example.invalid/a", target, size, sha)
                        self.assertEqual(target.read_bytes(), data)
                    else:
                        with self.assertRaises(engine.InstallError):
                            engine.download("https://example.invalid/a", target, size, sha)

    def test_unsafe_archives_are_refused_and_write_nothing_outside(self):
        link = zipfile.ZipInfo(f"{TOP}/link")
        link.external_attr = (stat.S_IFLNK | 0o777) << 16
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as bundle:
            bundle.writestr(f"{TOP}/deckcraft-cli.exe", b"cli")
            bundle.writestr(link, "deckcraft-cli.exe")
        tarball = io.BytesIO()
        with tarfile.open(fileobj=tarball, mode="w:gz") as bundle:
            info = tarfile.TarInfo(f"{TOP}/deckcraft-cli")
            info.type, info.linkname = tarfile.SYMTYPE, "/etc/passwd"
            bundle.addfile(info)
        for label, blob in (("parent", zip_bytes({"../evil.txt": b"x"})),
                            ("absolute", zip_bytes({"/evil.txt": b"x"})),
                            ("drive", zip_bytes({"C:/evil.txt": b"x"})),
                            ("zip symlink", buffer.getvalue()), ("tar symlink", tarball.getvalue()),
                            ("two clis", zip_bytes({"a/deckcraft-cli.exe": b"1", "b/deckcraft-cli.exe": b"2"})),
                            ("no cli", zip_bytes({"a/readme.txt": b"1"})), ("not an archive", b"plain")):
            with self.subTest(label), self.assertRaises(engine.InstallError):
                self.install(blob)
        self.assertFalse((self.home.parent / "evil.txt").exists())
        self.assertFalse((self.home / "evil.txt").exists())
        self.assertEqual(list((self.home / "deckcraft").iterdir()), [])

    def test_version_probe_demands_the_pinned_version(self):
        binary = Path(self.temp.name) / "deckcraft-cli.exe"
        for stdout, code, ok in (("deckcraft-cli 0.10.0\n", 0, True), ("deckcraft-cli 0.9.0\n", 0, False),
                                 ("deckcraft-cli 0.10.0\n", 1, False)):
            run = mock.Mock(stdout=stdout, stderr="", returncode=code)
            with self.subTest(stdout=stdout, code=code), mock.patch.object(engine.subprocess, "run", return_value=run):
                if ok:
                    engine.probe(binary, "deckcraft", "0.10.0")
                else:
                    with self.assertRaises(engine.InstallError):
                        engine.probe(binary, "deckcraft", "0.10.0")

    def test_command_line_refuses_to_install_without_approval(self):
        errors = io.StringIO()
        with mock.patch.dict(engine.os.environ, self.env), \
                mock.patch.object(engine.urllib.request, "urlopen", side_effect=AssertionError("network")), \
                contextlib.redirect_stderr(errors):
            self.assertEqual(engine.main(["install", "deckcraft"]), 1)
            self.assertEqual(engine.main(["find", "deckcraft"]), 1)
        self.assertRegex(errors.getvalue(), r"approval")
        self.assertEqual(list(self.home.iterdir()), [])

    def test_deckcraft_bridge_discovers_the_installed_engine_without_path_or_variable(self):
        self.install()
        probe = mock.Mock(stdout="deckcraft-cli 0.10.0\n", stderr="", returncode=0)
        env = {**self.env, "PATH": ""}
        with mock.patch.object(bridge.subprocess, "run", return_value=probe):
            found = bridge.discover(environ=env)
        self.assertEqual((found["version"], found["matches_reference"]), ("0.10.0", True))
        self.assertTrue(Path(found["binary"]).is_relative_to(self.home))
        with self.assertRaisesRegex(bridge.BridgeError, r"engine_install\.py install deckcraft --approved"):
            bridge.discover(environ={"DAODAN_ENGINE_HOME": str(self.home / "nowhere"), "PATH": ""})


if __name__ == "__main__":
    unittest.main()
