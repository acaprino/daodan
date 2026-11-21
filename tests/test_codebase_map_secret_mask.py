"""The secrets of a text are masked by Secretlint, or no text passes (`secret_mask`).

    python -B -m pytest -q -p no:cacheprovider tests/test_codebase_map_secret_mask.py
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "daodan/core"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import container  # noqa: E402
import engine_tools  # noqa: E402
import fake_secretlint  # noqa: E402
import secret_mask  # noqa: E402

KEY = "-----BEGIN FAKE-----\nMIIB0gIBAAJBAKj3\n-----END FAKE-----"


@pytest.fixture
def fake(tmp_path, monkeypatch):
    program = fake_secretlint.install(tmp_path / "tool")
    monkeypatch.setattr(secret_mask, "executable", lambda: program)
    return program


def test_a_secret_is_masked_and_counted_and_the_lines_stay(fake):
    text = f"# café \U0001F600\nKEY = '''{KEY}'''\nprint(KEY)\n"
    checked = secret_mask.masked(text, "src/signing.py")
    assert checked["found"] == 1 and checked["kinds"] == ["@secretlint/secretlint-rule-fake"]
    assert "MIIB" not in checked["text"] and checked["text"].count("\n") == text.count("\n")
    assert checked["text"].splitlines()[0] == "# café \U0001F600"  # UTF-16 ranges, the emoji is two units
    assert checked["text"].splitlines()[1] == "KEY = '''" + "*" * 20
    assert checked["text"].endswith("'''\nprint(KEY)\n")
    assert fake_secretlint.calls(fake)[0]["stdin"] == text


def test_a_text_without_secrets_passes_as_it_is_and_a_blank_one_starts_nothing(fake):
    assert secret_mask.masked("﻿x = 1\n", "a.py") == {"text": "﻿x = 1\n", "found": 0, "kinds": []}
    assert fake_secretlint.calls(fake)[0]["stdin"] == "x = 1\n"  # the BOM stays here, the ranges stay right
    assert secret_mask.masked(" \n", "b.py")["found"] == 0 and len(fake_secretlint.calls(fake)) == 1


@pytest.mark.parametrize("mode, cause", [("fail", "exit status 2; Error: the fake failed"),
                                         ("garbage", "Secretlint failed on a.py"),
                                         ("sleep", "did not answer within")])
def test_a_failure_is_a_gap_and_no_text(fake, monkeypatch, mode, cause):
    monkeypatch.setenv("FAKE_SECRETLINT", mode)
    monkeypatch.setattr(secret_mask, "TIMEOUT", 0.5 if mode == "sleep" else secret_mask.TIMEOUT)
    with pytest.raises(container.Gap, match=cause):
        secret_mask.masked(KEY, "a.py")


def test_without_the_executable_no_text_passes(monkeypatch):
    def unavailable():
        raise container.Gap("Secretlint 14.0.1 could not be downloaded and verified: offline", "check")
    monkeypatch.setattr(secret_mask, "executable", unavailable)
    with pytest.raises(container.Gap, match="offline"):
        secret_mask.masked(KEY, "a.py")


def _scanner(monkeypatch, ranges):
    """Answer the local CLI's JSON protocol with synthetic UTF-16 ranges. No executable or connection."""
    calls = []
    monkeypatch.setattr(secret_mask, "executable", lambda: Path(sys.executable))

    def run(command, **options):
        text = options["input"].decode()
        calls.append(text)
        messages = [{"range": span, "ruleId": "fixture"} for span in ranges(text)]
        result = json.dumps([{"messages": messages}]).encode()
        return subprocess.CompletedProcess(command, int(bool(messages)), result, b"")

    monkeypatch.setattr(secret_mask.subprocess, "run", run)
    return calls


def _span(text, start, end):
    return [len(text[:edge].encode("utf-16-le")) // 2 for edge in (start, end)]


def test_tool_result_uses_key_context_once_and_redacts_equal_values(monkeypatch):
    demo = "demo \U0001F600 value"

    def ranges(text):
        pair = '"fixture_key": "' + demo + '"'
        start = text.index(pair) + len('"fixture_key": "')
        return [_span(text, start, start + len(demo))]

    calls = _scanner(monkeypatch, ranges)
    packet = {"rows": [demo, {"fixture_key": demo, 'other"key': 'a\\b "c"'}], "counts": {2: 3}, "ready": True}
    stars = "*" * (len(demo) + 1)
    assert secret_mask.tool_result(packet) == {
        "rows": [stars, {"fixture_key": stars, 'other"key': 'a\\b "c"'}],
        "counts": {"2": 3}, "ready": True, "masked_secrets": 1}
    assert len(calls) == 1 and packet["rows"][0] == demo


def test_tool_result_scans_numbered_source_and_adjacent_strings_as_actual_lines(monkeypatch):
    marker = "start of demo\nsynthetic contents\nend of demo"

    def ranges(text):
        assert text.count("\n" + marker + "\n") == 2
        first = text.index(marker)
        last = text.rindex(marker)
        return [_span(text, index, index + len(marker)) for index in (first, last)]

    calls = _scanner(monkeypatch, ranges)
    lines = ["safe \U0001F600", *marker.split("\n"), "13: part of the source", ""]
    def numbered(rows):
        return "".join(f"{number}: {row}\n" for number, row in enumerate(rows, 8))

    block = {"start": 8, "end": 13, "source": numbered(lines)}
    packet = {"files": [{"blocks": [block]}], "rows": marker.split("\n")}
    stars = ["*" * len(line) for line in marker.split("\n")]
    masked_block = {**block, "source": numbered([lines[0], *stars, *lines[-2:]])}
    assert secret_mask.tool_result(packet) == {
        "files": [{"blocks": [masked_block]}], "rows": stars, "masked_secrets": 2}
    assert len(calls) == 1


@pytest.mark.parametrize("match", ["fixture_key", "1245", '": '])
def test_tool_result_withholds_when_masking_would_change_a_key_number_or_separator(monkeypatch, match):
    def ranges(text):
        index = text.index(match)
        return [_span(text, index, index + len(match))]
    calls = _scanner(monkeypatch, ranges)
    assert secret_mask.tool_result({"fixture_key": 1245, "note": "fixture"}) == {
        "status": "withheld", "error": secret_mask.UNAVAILABLE}
    assert len(calls) == 1


@pytest.mark.parametrize("bad_range", ["past-end", "half-surrogate", [0, 0], [False, 2], [2, 1]])
def test_tool_result_withholds_for_invalid_scanner_ranges(monkeypatch, bad_range):
    def ranges(text):
        if bad_range == "past-end":
            return [[0, len(text) + 100]]
        if bad_range == "half-surrogate":
            start, end = _span(text, text.index("\U0001F600"), text.index("\U0001F600") + 1)
            return [[start + 1, end]]
        return [bad_range]
    calls = _scanner(monkeypatch, ranges)
    assert secret_mask.tool_result({"note": "fixture \U0001F600"}) == {
        "status": "withheld", "error": secret_mask.UNAVAILABLE}
    assert len(calls) == 1


def test_tool_result_withholds_on_unverifiable_source_numbers_or_offline_scanner(monkeypatch):
    def offline():
        raise OSError("synthetic private diagnostic")
    monkeypatch.setattr(secret_mask, "executable", offline)
    withheld = {"status": "withheld", "error": secret_mask.UNAVAILABLE}
    assert secret_mask.tool_result({"value": "demo"}) == withheld
    calls = _scanner(monkeypatch, lambda text: [])
    assert secret_mask.tool_result({"start": 2, "end": 3, "source": "2: demo\n4: fixture\n"}) == withheld
    assert secret_mask.tool_result({"1": "first", 1: "second"}) == withheld
    assert calls == []


@pytest.mark.parametrize("status, report", [(0, []), (0, {}), (1, [{"messages": []}])])
def test_tool_result_withholds_when_the_scanner_omits_its_report(monkeypatch, status, report):
    monkeypatch.setattr(secret_mask, "executable", lambda: Path(sys.executable))
    monkeypatch.setattr(secret_mask.subprocess, "run", lambda *args, **options:
                        subprocess.CompletedProcess(args, status, json.dumps(report).encode(), b"fixture diagnostic"))
    assert secret_mask.tool_result({"note": "fixture"}) == {"status": "withheld", "error": secret_mask.UNAVAILABLE}


def test_the_executable_is_the_pinned_one_in_daodan_s_tool_folder(tmp_path, monkeypatch):
    """Downloaded on the first call only, by the release's sha256; a file that differs is never started."""
    content = b"the release's executable"
    platform = engine_tools._platform()
    monkeypatch.setattr(secret_mask, "ASSETS", {platform: ("x", hashlib.sha256(content).hexdigest())})
    monkeypatch.setattr(engine_tools, "shared_engine_dir", lambda name: tmp_path / "engines" / name)
    fetched = []

    def download(url, target, sha256=None):
        fetched.append((url, target, sha256))
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        return target
    monkeypatch.setattr(engine_tools, "download", download)
    secret_mask.executable.cache_clear()
    try:
        binary = secret_mask.executable()
        assert binary == tmp_path / "engines/secretlint/14.0.1" / engine_tools.executable_name("secretlint")
        assert fetched == [("https://github.com/secretlint/secretlint/releases/download/v14.0.1/secretlint-14.0.1-x",
                            binary, hashlib.sha256(content).hexdigest())]
        secret_mask.executable.cache_clear()
        assert secret_mask.executable() == binary and len(fetched) == 1  # kept, checked again, not fetched
        binary.write_bytes(b"something else")
        secret_mask.executable.cache_clear()
        with pytest.raises(container.Gap, match="sha256 differs"):
            secret_mask.executable()
        binary.unlink()
        monkeypatch.setattr(engine_tools, "download", lambda *a, **k: (_ for _ in ()).throw(OSError("offline")))
        with pytest.raises(container.Gap, match="could not be downloaded and verified: offline"):
            secret_mask.executable()
    finally:
        secret_mask.executable.cache_clear()


def test_the_release_digests_are_written_for_every_platform_it_publishes():
    assert sorted(secret_mask.ASSETS) == ["linux-arm64", "linux-x64", "osx-arm64", "osx-x64", "win-x64"]
    assert all(len(digest) == 64 for _asset, digest in secret_mask.ASSETS.values())
    assert secret_mask.CONFIG.is_file()
