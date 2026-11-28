"""The tree-sitter grammars: a pinned pack, its bundle fetched by Daodan into its own cache, a missing grammar
declared as a gap in the snapshot.

The pack (tree-sitter-language-pack) loads a grammar from the directory it is configured with, extracting it
from the platform's bundle when the manifest sits beside it, and never verifies a bundle already in place: the
sha256 Daodan pins is the only guard. These tests use small fake bundles with patched pins, except the last,
which reads the real bundle when the user's own pack cache holds it.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from unittest import mock

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "daodan" / "core"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import snapshot  # noqa: E402
from languages import _treesitter  # noqa: E402
from snapshot_store import open_snapshot  # noqa: E402
from read_manifest import read_manifest  # noqa: E402

PLATFORMS = {"linux-aarch64", "linux-x86_64", "macos-arm64", "macos-x86_64", "windows-aarch64", "windows-x86_64"}


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _tree(directory: Path) -> dict:
    """Every file under `directory` with its bytes and mtime: what must not change on the user's side."""
    return {p.relative_to(directory).as_posix(): (p.read_bytes(), p.stat().st_mtime_ns)
            for p in sorted(directory.rglob("*")) if p.is_file()}


@pytest.fixture
def fake_release(tmp_path, monkeypatch):
    """Pins of a fake release: a manifest and one bundle for the platform `test-x86_64`."""
    manifest, bundle = b'{"version": "fake"}', b"fake bundle bytes"
    monkeypatch.setattr(_treesitter, "PACK_MANIFEST", (_sha(manifest), len(manifest)))
    monkeypatch.setattr(_treesitter, "PACK_BUNDLES", {"test-x86_64": (_sha(bundle), len(bundle))})
    user = tmp_path / "user-pack" / "v1.13.5"
    return {"manifest": manifest, "bundle": bundle, "user": user, "home": tmp_path / "daodan" / "v1.13.5",
            "bundle_name": f"test-x86_64-{_sha(bundle)}.tar.zst"}


def _user_cache(release, manifest=None, bundle=None):
    user = release["user"]
    (user / "bundles").mkdir(parents=True)
    (user / "libs").mkdir()
    (user / "manifest.json").write_bytes(release["manifest"] if manifest is None else manifest)
    (user / "bundles" / release["bundle_name"]).write_bytes(release["bundle"] if bundle is None else bundle)
    return _tree(user)


def _no_network(url, target, *, sha256=None):
    raise AssertionError(f"no download expected: {url}")


# ---------------------------------------------------------------------------------------------------------------
# The pins


def test_the_requirements_pin_the_versions_the_loader_reads_with():
    lines = set((SCRIPTS / "requirements.txt").read_text(encoding="utf-8").split("\n"))
    assert _treesitter.PACK_VERSION == "1.13.5"
    assert {"tree-sitter==0.26.0", f"tree-sitter-language-pack=={_treesitter.PACK_VERSION}"} <= lines


def test_the_mcp_server_installs_the_pinned_versions():
    """The MCP server installs its own dependencies from its PEP 723 header: the same pins."""
    header = (SCRIPTS / "mcp_server.py").read_text(encoding="utf-8").splitlines()[2]
    assert '"tree-sitter==0.26.0"' in header and f'"tree-sitter-language-pack=={_treesitter.PACK_VERSION}"' in header


def test_the_table_pins_the_six_platforms_of_the_release():
    assert set(_treesitter.PACK_BUNDLES) == PLATFORMS
    for platform, (digest, size) in _treesitter.PACK_BUNDLES.items():
        assert re.fullmatch(r"[0-9a-f]{64}", digest) and size > 0, platform
        assert _treesitter.bundle_url(platform) == (
            f"https://github.com/xberg-io/tree-sitter-language-pack/releases/download/v1.13.5/parsers-{platform}.tar.zst")
    assert _treesitter.manifest_url() == \
        "https://github.com/xberg-io/tree-sitter-language-pack/releases/download/v1.13.5/parsers.json"


def test_the_table_is_the_manifest_of_the_release():
    """The pinned manifest lists every bundle with the sha256 and size of the table."""
    manifest = _treesitter._user_pack_home()
    manifest = manifest / "manifest.json" if manifest else None
    if manifest is None or not manifest.is_file() or _sha(manifest.read_bytes()) != _treesitter.PACK_MANIFEST[0]:
        pytest.skip("the pinned manifest is not in the user's pack cache")
    platforms = json.loads(manifest.read_text(encoding="utf-8"))["platforms"]
    assert {key: (item["sha256"], item["size"]) for key, item in platforms.items()} == _treesitter.PACK_BUNDLES
    assert {item["url"] for item in platforms.values()} == {_treesitter.bundle_url(key) for key in platforms}


# ---------------------------------------------------------------------------------------------------------------
# Placing the release in Daodan's cache


def test_the_release_is_copied_from_the_users_pack_cache_without_the_network(fake_release):
    before = _user_cache(fake_release)
    home = fake_release["home"]
    assert _treesitter.place_grammars(home, "test-x86_64", fake_release["user"], _no_network) is None
    assert (home / "manifest.json").read_bytes() == fake_release["manifest"]
    assert (home / "bundles" / fake_release["bundle_name"]).read_bytes() == fake_release["bundle"]
    assert (home / "libs").is_dir()
    assert _tree(fake_release["user"]) == before, "the user's pack cache is read only"
    assert not [p for p in home.rglob("*.partial")]


def test_a_copy_that_does_not_match_its_pin_is_removed_and_downloaded(fake_release):
    before = _user_cache(fake_release, bundle=b"tampered bundle")
    fetched = []

    def fetch(url, target, *, sha256=None):
        fetched.append(url)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(fake_release["bundle"])
        return target

    home = fake_release["home"]
    assert _treesitter.place_grammars(home, "test-x86_64", fake_release["user"], fetch) is None
    assert fetched == [_treesitter.bundle_url("test-x86_64")]
    assert (home / "bundles" / fake_release["bundle_name"]).read_bytes() == fake_release["bundle"]
    assert _tree(fake_release["user"]) == before


def test_a_failed_download_is_a_gap_and_leaves_nothing_in_daodans_cache(fake_release):
    def fetch(url, target, *, sha256=None):
        raise ValueError(f"checksum mismatch for {url}")

    home = fake_release["home"]
    reason = _treesitter.place_grammars(home, "test-x86_64", None, fetch)
    assert reason == f"download failed: checksum mismatch for {_treesitter.manifest_url()}"
    assert not [p for p in home.rglob("*") if p.is_file()]


def test_a_downloaded_file_that_does_not_match_its_pin_is_a_gap_and_removed(fake_release):
    """`download` checks the sha256 it is given; a fetch that skips it is caught all the same."""
    def fetch(url, target, *, sha256=None):
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"wrong" if url.endswith(".tar.zst") else fake_release["manifest"])
        return target

    home = fake_release["home"]
    reason = _treesitter.place_grammars(home, "test-x86_64", None, fetch)
    assert reason == f"download failed: checksum mismatch for {_treesitter.bundle_url('test-x86_64')}"
    assert not (home / "bundles" / fake_release["bundle_name"]).exists()


def test_a_release_already_in_daodans_cache_is_verified_and_kept(fake_release):
    home = fake_release["home"]
    _user_cache(fake_release)
    assert _treesitter.place_grammars(home, "test-x86_64", fake_release["user"], _no_network) is None
    assert _treesitter.place_grammars(home, "test-x86_64", None, _no_network) is None


def test_a_damaged_file_in_daodans_cache_is_replaced(fake_release):
    home = fake_release["home"]
    _user_cache(fake_release)
    assert _treesitter.place_grammars(home, "test-x86_64", fake_release["user"], _no_network) is None
    (home / "bundles" / fake_release["bundle_name"]).write_bytes(b"damaged")
    assert _treesitter.place_grammars(home, "test-x86_64", fake_release["user"], _no_network) is None
    assert (home / "bundles" / fake_release["bundle_name"]).read_bytes() == fake_release["bundle"]


PLACER = r"""
import json, sys, time
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from languages import _treesitter
home, go, pins = Path(sys.argv[2]), Path(sys.argv[3]), json.loads(Path(sys.argv[4]).read_text(encoding="utf-8"))
_treesitter.PACK_MANIFEST = tuple(pins["manifest"])
_treesitter.PACK_BUNDLES = {"test-x86_64": tuple(pins["bundle"])}
data = {_treesitter.manifest_url(): pins["manifest_bytes"].encode(), _treesitter.bundle_url("test-x86_64"): pins["bundle_bytes"].encode()}

def fetch(url, target, *, sha256=None):
    # Written in pieces, as a download is: another process may look at the file in between.
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "wb") as handle:
        for start in range(0, len(data[url]), 4096):
            handle.write(data[url][start:start + 4096])
            handle.flush()
            time.sleep(0.001)
    return target

while not go.exists():
    time.sleep(0.005)
reason = _treesitter.place_grammars(home, "test-x86_64", None, fetch)
bundle = home / "bundles" / f"test-x86_64-{pins['bundle'][0]}.tar.zst"
print(json.dumps([reason, (home / "manifest.json").read_bytes() == data[_treesitter.manifest_url()],
                  bundle.read_bytes() == data[_treesitter.bundle_url("test-x86_64")]]))
"""


def test_processes_placing_the_release_at_once_each_find_it_whole(tmp_path):
    """Two analyses on one machine share Daodan's cache: each writes under a name of its own and renames it into
    place, so none reads a file another is writing, and none removes one another has placed."""
    manifest, bundle = "m" * 200_000, "b" * 300_000
    pins = {"manifest": [_sha(manifest.encode()), len(manifest)], "bundle": [_sha(bundle.encode()), len(bundle)],
            "manifest_bytes": manifest, "bundle_bytes": bundle}
    home, go = tmp_path / "daodan" / "v1.13.5", tmp_path / "go"
    script, given = tmp_path / "placer.py", tmp_path / "pins.json"
    script.write_text(PLACER, encoding="utf-8")
    given.write_text(json.dumps(pins), encoding="utf-8")
    placers = [subprocess.Popen([sys.executable, str(script), str(SCRIPTS), str(home), str(go), str(given)],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for _ in range(6)]
    go.write_text("", encoding="utf-8")
    outcomes = [placer.communicate(timeout=120) for placer in placers]
    assert [json.loads(out.strip().splitlines()[-1]) if out.strip() else err for out, err in outcomes] == \
        [[None, True, True]] * len(placers)
    assert sorted(p.relative_to(home).as_posix() for p in home.rglob("*") if p.is_file()) == [
        f"bundles/test-x86_64-{pins['bundle'][0]}.tar.zst", "manifest.json"]


def test_a_platform_without_a_pinned_bundle_is_a_gap(fake_release):
    reason = _treesitter.place_grammars(fake_release["home"], "plan9-mips", None, _no_network)
    assert reason == "no pinned grammar bundle for platform plan9-mips"


# ---------------------------------------------------------------------------------------------------------------
# The loader


@pytest.fixture
def fresh_loader():
    _treesitter.get_parser.cache_clear()
    yield
    _treesitter.get_parser.cache_clear()


def test_a_pack_of_another_version_is_a_gap(fresh_loader):
    pack = mock.Mock(__version__="1.14.0")
    with mock.patch.dict(sys.modules, {"tree_sitter_language_pack": pack}), \
            mock.patch.object(_treesitter, "_GRAMMAR_MODULES", {}):
        assert _treesitter.get_parser("go") is None
        assert _treesitter.load_failure("go") == \
            "tree-sitter-language-pack 1.14.0 is installed, Daodan reads with 1.13.5"
    pack.get_parser.assert_not_called()


def test_the_grammars_are_placed_once_per_process(fresh_loader):
    calls = []

    def place(*args):
        calls.append(args)
        return "download failed: no network"

    with mock.patch.object(_treesitter, "place_grammars", place), \
            mock.patch.object(_treesitter, "_GRAMMAR_MODULES", {}):
        assert _treesitter.get_parser("go") is None and _treesitter.get_parser("java") is None
        assert _treesitter.load_failure("java") == "download failed: no network"
    assert len(calls) == 1


def test_a_test_that_clears_the_loader_leaves_the_next_one_its_grammars(request, tmp_path, monkeypatch):
    """`cache_clear` forgets the placement: the first parse after it places again, under the shared folder and the
    network of the test it runs in. An egress test moves the folder and cuts the network (the 28 November group 14 of
    `--shards 32`: every test after it in the process read `download failed`); the suite places again before each
    test (`conftest.pytest_runtest_setup`), and that test reads."""
    import conftest

    def offline(url, target, *, sha256=None):
        raise OSError("no network in this test")
    _treesitter.get_parser.cache_clear()  # a test that clears the loader
    conftest.pytest_runtest_setup(request.node)  # the next test's setup
    monkeypatch.setenv("DAODAN_SHARED_DIR", str(tmp_path / "shared"))
    monkeypatch.setattr(_treesitter, "_fetch", offline)
    assert _treesitter.get_parser("go") is not None and _treesitter.load_failure("go") is None


# ---------------------------------------------------------------------------------------------------------------
# The snapshot


GO = 'package billing\n\nfunc Pay(amount int) int {\n\treturn amount\n}\n'
PY = "def pay(amount):\n    return amount\n"


@pytest.fixture
def no_grammars(fresh_loader):
    """Daodan cannot place the grammars: no download and no copy."""
    with mock.patch.object(_treesitter, "place_grammars", lambda *args: "download failed: no network"), \
            mock.patch.object(_treesitter, "_GRAMMAR_MODULES", {}):
        _treesitter.get_parser.cache_clear()
        yield
    _treesitter.get_parser.cache_clear()


def test_a_missing_grammar_is_a_declared_gap_in_the_snapshot(tmp_path, no_grammars):
    (tmp_path / "billing.go").write_text(GO, encoding="utf-8", newline="")
    (tmp_path / "pay.py").write_text(PY, encoding="utf-8", newline="")
    manifest = read_manifest(tmp_path)
    assert manifest["metrics"]["grammars_unavailable"] == {"go": "download failed: no network"}
    written = snapshot.read_project(tmp_path, tmp_path / "out" / "manifest.sqlite")
    with open_snapshot(tmp_path / "out" / "manifest.sqlite") as stored:
        assert stored.metadata["metrics"]["grammars_unavailable"] == {"go": "download failed: no network"}
        assert stored.get_file("billing.go")["status"] == "parse-skipped"
    assert written["metrics"]["grammars_unavailable"] == {"go": "download failed: no network"}
    files = manifest["files"]
    entry = files["billing.go"]
    assert entry["status"] == "parse-skipped"
    assert entry["parser_notes"] == ["grammar unavailable: go: download failed: no network"]
    assert entry["symbols"] == {} and entry["imports"] == [] and "semantic" not in entry
    assert entry["parser_profile"] == {"language": "go", "backend": "unavailable", "grammar": "go",
                                       "reason": "download failed: no network"}
    assert files["pay.py"]["status"] == "parsed" and "pay" in files["pay.py"]["symbols"]


def test_with_its_grammar_a_file_is_read_as_before(tmp_path, fresh_loader):
    """No gap, no reason in the profile, no list in the metrics: the snapshot of a machine with the grammars."""
    (tmp_path / "billing.go").write_text(GO, encoding="utf-8", newline="")
    manifest = read_manifest(tmp_path)
    entry = manifest["files"]["billing.go"]
    assert entry["status"] == "parsed" and "Pay" in entry["symbols"]
    assert entry["parser_profile"]["backend"] == "tree-sitter" and "reason" not in entry["parser_profile"]
    assert "grammars_unavailable" not in manifest["metrics"]


def test_the_file_is_read_again_once_its_grammar_is_there(tmp_path, fresh_loader):
    (tmp_path / "billing.go").write_text(GO, encoding="utf-8", newline="")
    (tmp_path / "pay.py").write_text(PY, encoding="utf-8", newline="")
    with mock.patch.object(_treesitter, "place_grammars", lambda *args: "download failed: no network"), \
            mock.patch.object(_treesitter, "_GRAMMAR_MODULES", {}):
        _treesitter.get_parser.cache_clear()
        snapshot.read_project(tmp_path, tmp_path / "first.sqlite")
    _treesitter.get_parser.cache_clear()
    with open_snapshot(tmp_path / "first.sqlite") as previous:
        second = snapshot.read_project(tmp_path, tmp_path / "second.sqlite", previous=previous)
    assert second["metrics"]["cache_hits"] == 1
    with open_snapshot(tmp_path / "second.sqlite") as current:
        entry = current.get_file("billing.go")
    assert entry["status"] == "parsed" and "Pay" in entry["symbols"]


@pytest.mark.parametrize("system, machine, expected", [
    ("win32", "AMD64", "windows-x86_64"), ("win32", "ARM64", "windows-aarch64"), ("linux", "x86_64", "linux-x86_64"),
    ("linux", "aarch64", "linux-aarch64"), ("darwin", "arm64", "macos-arm64"), ("darwin", "x86_64", "macos-x86_64")])
def test_the_platform_names_the_pack_uses(system, machine, expected):
    assert _treesitter.pack_platform(system, machine) == expected


def test_the_windows_architecture_is_the_process_s_not_the_machine_s(monkeypatch):
    """The bundle's libraries load into this process: an x64 Python emulated on ARM64 Windows needs x86_64."""
    monkeypatch.setenv("PROCESSOR_ARCHITECTURE", "AMD64")
    monkeypatch.setenv("PROCESSOR_ARCHITEW6432", "ARM64")
    assert _treesitter.pack_platform("win32") == "windows-x86_64"
    monkeypatch.setenv("PROCESSOR_ARCHITECTURE", "ARM64")
    monkeypatch.delenv("PROCESSOR_ARCHITEW6432")
    assert _treesitter.pack_platform("win32") == "windows-aarch64"


def test_the_platform_starts_no_process_even_when_windows_does_not_answer():
    """`platform.system()` and `platform.machine()` ask Windows through WMI and, when WMI fails (the commit
    exhausted), run `ver` through the shell: the pack's platform asks nothing."""
    import platform

    def refuse(*args, **kwargs):
        raise AssertionError(f"pack_platform started a process: {args[:1]}")

    with mock.patch.object(platform, "_uname_cache", None), \
            mock.patch.object(platform, "_wmi_query", side_effect=OSError("WMI did not answer"), create=True), \
            mock.patch.object(subprocess, "Popen", refuse):
        name = _treesitter.pack_platform()
    assert name in _treesitter.PACK_BUNDLES


# ---------------------------------------------------------------------------------------------------------------
# The real bundle, offline


def test_the_real_bundle_loads_a_grammar_from_daodans_cache_offline(tmp_path):
    """In a separate process, because the pack's configuration is global: the pinned bundle copied from the
    user's pack cache into a Daodan cache under tmp_path, the pack's manifest URL a closed port."""
    user = _treesitter._user_pack_home()
    platform = _treesitter.pack_platform()
    if platform not in _treesitter.PACK_BUNDLES or user is None or not (
            user / "bundles" / f"{platform}-{_treesitter.PACK_BUNDLES[platform][0]}.tar.zst").is_file():
        pytest.skip("the pinned bundle is not in the user's pack cache")
    before = sorted(p.name for p in user.rglob("*"))
    script = f"""
import sys
from pathlib import Path
sys.path.insert(0, {str(SCRIPTS)!r})
from languages import _treesitter
_treesitter._daodan_home = lambda: Path({str(tmp_path / 'daodan')!r})
def no_network(url, target, *, sha256=None):
    raise OSError("no network in this test: " + url)
_treesitter._fetch = no_network
pair = _treesitter.get_parser("c")
assert pair is not None, _treesitter.load_failure("c")
tree = pair[0].parse(b"int f(void) {{ return 1; }}\\n")
print(tree.root_node.type, tree.root_node.has_error)
"""
    env = {**os.environ, "TREE_SITTER_LANGUAGE_PACK_MANIFEST_URL": "http://127.0.0.1:9/closed"}
    done = subprocess.run([sys.executable, "-B", "-c", script], capture_output=True, text=True, env=env, timeout=300)
    assert done.returncode == 0, done.stderr
    assert done.stdout.split() == ["translation_unit", "False"]
    assert (tmp_path / "daodan" / "libs").is_dir()
    assert sorted(p.name for p in user.rglob("*")) == before
