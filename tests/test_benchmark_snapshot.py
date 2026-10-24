"""Pin benchmark provenance, per-board freshness, and effort-series identities.

All upstream replies are local fixtures. Network access is never needed to exercise
the mirror's empty-latest failure or preserve rank-only observations.
"""
from __future__ import annotations

import contextlib
import hashlib
import io
import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

SCRIPTS = (Path(__file__).resolve().parents[1] / "plugins" / "model-routing"
           / "skills" / "model-routing" / "scripts")
sys.path.insert(0, str(SCRIPTS))

import benchmark_snapshot as benchmark  # noqa: E402

SHA = "a" * 40
REPO = "fixture/arena-mirror"


class _Clock(datetime):
    @classmethod
    def now(cls, tz=None):
        return cls(2026, 10, 22, 12, tzinfo=timezone.utc)


def _board(rows, updated="Oct 7, 2026", **meta):
    return {"meta": {"last_updated": updated, "model_count": len(rows),
                     "source_url": "https://arena.ai/leaderboard", **meta},
            "models": rows}


def _row(name, *, rank=1, score=1700, vendor="Fixture lab", **extra):
    row = {"model": name, "rank": rank, "vendor": vendor, "license": "proprietary"}
    if score is not None:
        row.update(score=score, ci=10, votes=3000)
    row.update(extra)
    return row


class SnapshotCase(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix="benchmark-snapshot-")
        self.addCleanup(directory.cleanup)
        self.tmp = Path(directory.name)

    def capture(self, boards=None, *, extra=(), latest="2026-10-07", indices=None):
        boards = boards or {"code": _board([_row("orbit-high")])}
        indices = indices or {"2026-10-07": {"leaderboards": {c: {} for c in boards}}}
        calls = []
        raw_boards = {}
        for category, payload in boards.items():
            if not isinstance(payload, str):
                raw_boards[category] = json.dumps(payload, ensure_ascii=False).encode("utf-8")

        def reply(url, timeout, max_bytes):
            calls.append(url)
            if url == f"https://api.github.com/repos/{REPO}/commits/main":
                payload = {"sha": SHA, "commit": {"author": {"date": "2026-10-21T00:00:00Z"},
                                                    "message": "Pinned fixture\nMore detail"}}
            elif url == f"https://api.github.com/repos/{REPO}/contents/data?ref={SHA}":
                payload = [{"name": d, "type": "dir"} for d in sorted(indices)]
            elif url == benchmark.raw_url(REPO, SHA, "data", "latest.json"):
                payload = {"date": latest}
            else:
                for day, index in indices.items():
                    if url == benchmark.raw_url(REPO, SHA, "data", day, "_index.json"):
                        return index, json.dumps(index).encode(), None
                for category, payload in boards.items():
                    if url == benchmark.raw_url(REPO, SHA, "data", "2026-10-07", f"{category}.json"):
                        if isinstance(payload, str):
                            return None, None, payload
                        return payload, raw_boards[category], None
                raise AssertionError(f"unexpected upstream request: {url}")
            return payload, json.dumps(payload).encode(), None

        stdout = io.StringIO()
        with (mock.patch.object(benchmark, "_get_json", side_effect=reply),
              mock.patch.object(benchmark, "datetime", _Clock),
              contextlib.redirect_stdout(stdout)):
            code = benchmark.main(["--out-dir", str(self.tmp), "--fetch", "--repo", REPO,
                                   "--categories", ",".join(boards), *extra])
        summary = json.loads(stdout.getvalue())
        path = self.tmp / "arena-2026-10-07.json"
        doc = json.loads(path.read_bytes()) if path.exists() else None
        return code, summary, doc, calls, raw_boards


class TestNetworkBoundary(unittest.TestCase):
    def test_non_https_and_hosts_outside_the_allowlist_never_make_a_request(self):
        urls = ["http://api.github.com/repos/a/b", "https://example.com/data.json",
                "https://api.github.com.evil.example/data.json"]
        with mock.patch.object(benchmark.OPENER, "open") as opener:
            for url in urls:
                with self.subTest(url=url):
                    payload, raw, error = benchmark._get_json(url, 5, 100)
                    self.assertIsNone(payload)
                    self.assertIsNone(raw)
                    self.assertTrue(error)
        opener.assert_not_called()

    def test_oversized_bytes_and_invalid_json_are_discarded(self):
        for raw, message in ((b"x" * 11, "exceeds --max-bytes"),
                             (b"not JSON", "not UTF-8 JSON"),
                             (b"\xff", "not UTF-8 JSON")):
            with self.subTest(raw=raw), mock.patch.object(benchmark.OPENER, "open") as opener:
                opener.return_value.__enter__.return_value.read.return_value = raw
                payload, saved, error = benchmark._get_json("https://api.github.com/data", 5, 10)
            self.assertIsNone(payload)
            self.assertIsNone(saved)
            self.assertIn(message, error)

    def test_capture_requires_opt_in_before_resolving_any_source(self):
        stdout = io.StringIO()
        with (mock.patch.object(benchmark, "resolve_commit") as resolve,
              contextlib.redirect_stdout(stdout)):
            code = benchmark.main(["--out-dir", "unused"])
        self.assertEqual(code, 1)
        self.assertIn("opt-in", json.loads(stdout.getvalue())["reason"])
        resolve.assert_not_called()


class TestSnapshotResolution(SnapshotCase):
    def test_a_mirror_without_snapshot_directories_reports_failure_before_board_resolution(self):
        stdout = io.StringIO()
        with (mock.patch.object(benchmark, "resolve_commit",
                                return_value=(SHA, {"sha": SHA}, None)),
              mock.patch.object(benchmark, "list_snapshot_dates", return_value=([], None)),
              mock.patch.object(benchmark, "resolve_snapshot") as resolve,
              contextlib.redirect_stdout(stdout)):
            code = benchmark.main(["--out-dir", str(self.tmp), "--fetch"])
        self.assertEqual(code, 1)
        self.assertIn("no snapshot", json.loads(stdout.getvalue())["reason"])
        resolve.assert_not_called()
        self.assertEqual(list(self.tmp.iterdir()), [])

    def test_empty_latest_walks_back_and_every_capture_url_uses_the_pinned_commit(self):
        code, summary, doc, calls, _ = self.capture(
            latest="2026-10-09", indices={
                "2026-10-07": {"leaderboards": {"code": {}}},
                "2026-10-08": {"leaderboards": {}, "errors": []},
                "2026-10-09": {"leaderboards": {}, "errors": []},
            })
        self.assertEqual(code, 0, summary)
        self.assertEqual(doc["source"]["snapshot_date"], "2026-10-07")
        self.assertEqual(doc["source"]["commit"]["sha"], SHA)
        self.assertTrue(any("walked back" in n for n in doc["notes"]))
        capture_urls = [u for u in calls if "raw.githubusercontent.com" in u]
        self.assertTrue(capture_urls)
        self.assertTrue(all(f"/{SHA}/" in u for u in capture_urls))

    def test_an_explicit_unknown_date_fails_without_reading_a_board(self):
        code, summary, doc, calls, _ = self.capture(extra=("--date", "2026-01-01"))
        self.assertEqual(code, 1)
        self.assertIn("not among", summary["reason"])
        self.assertIsNone(doc)
        self.assertFalse(any("raw.githubusercontent.com" in u for u in calls))

    def test_no_nonempty_snapshot_is_a_failed_capture_not_an_empty_artifact(self):
        code, summary, doc, _, _ = self.capture(
            indices={"2026-10-07": {"leaderboards": {}, "errors": []}})
        self.assertEqual(code, 1)
        self.assertIn("no snapshot", summary["reason"])
        self.assertIsNone(doc)


class TestBoardCapture(SnapshotCase):
    def test_verbatim_rows_and_raw_digest_survive_the_derived_match_index(self):
        rows = [_row("Claude Opus 5.5 (Max)", extra_dimension={"skill": 0.83}),
                _row("claude-opus-5.5-high", rank=2, score=1650)]
        code, summary, doc, _, raw = self.capture({"code": _board(rows)})
        self.assertEqual(code, 0, summary)
        self.assertEqual(doc["boards"]["code"]["rows_verbatim"], rows)
        self.assertEqual(doc["boards"]["code"]["raw_sha256"], hashlib.sha256(raw["code"]).hexdigest())
        body = (self.tmp / "arena-2026-10-07.json").read_bytes()
        self.assertEqual(summary["snapshot_sha256"], hashlib.sha256(body).hexdigest())
        self.assertFalse((self.tmp / "arena-2026-10-07.json.tmp").exists())
        self.assertEqual(doc["match_index_semantics"]["identity"], "name-normalized-unverified")
        self.assertTrue(doc["authority"]["advisory_only"])

    def test_different_efforts_are_a_measured_series_not_an_identity_conflict(self):
        code, summary, doc, _, _ = self.capture({"code": _board([
            _row("claude-sonnet-5.5-xhigh"),
            _row("Claude Sonnet 5.5 (High)", rank=2, score=1643),
        ])})
        self.assertEqual(code, 0, summary)
        entries = doc["match_index"]["claudesonnet55"]
        self.assertEqual({e["effort"] for e in entries}, {"high", "xhigh"})
        self.assertTrue(all(e["observations_in_category"] == 2 for e in entries))
        self.assertTrue(all(not e["identity_conflict"] for e in entries))
        self.assertEqual(summary["identity_conflicts"], 0)
        self.assertEqual(summary["models_with_effort_series"]["claudesonnet55"], ["high", "xhigh"])

    def test_same_effort_collision_is_reported_without_merging_or_dropping_rows(self):
        rows = [_row("orbit-high", vendor="Lab A"),
                _row("Orbit (High)", vendor="Lab B", rank=2, score=1600)]
        code, summary, doc, _, _ = self.capture({"code": _board(rows)})
        self.assertEqual(code, 0, summary)
        self.assertEqual(summary["identity_conflicts"], 1)
        self.assertEqual(summary["conflict_rows"][0]["vendors"], ["Lab A", "Lab B"])
        self.assertEqual(len(doc["match_index"]["orbit"]), 2)
        self.assertTrue(all(e["identity_conflict"] for e in doc["match_index"]["orbit"]))
        self.assertEqual(doc["boards"]["code"]["rows_verbatim"], rows)

    def test_the_same_name_at_the_same_effort_on_two_boards_is_not_a_collision(self):
        code, summary, doc, _, _ = self.capture({
            "code": _board([_row("orbit-high")]),
            "text": _board([_row("Orbit (High)", score=1900)]),
        })
        self.assertEqual(code, 0, summary)
        self.assertEqual(summary["identity_conflicts"], 0)
        self.assertEqual({e["category"] for e in doc["match_index"]["orbit"]}, {"code", "text"})

    def test_rank_only_dimensions_never_become_an_elo_score(self):
        row = _row("orbit (Max)", rank=2, score=None, dimensions={"planning": 0.9})
        code, summary, doc, _, _ = self.capture({"agent": _board([row], dimensions=["planning"])})
        self.assertEqual(code, 0, summary)
        observation = doc["match_index"]["orbit"][0]
        self.assertEqual(observation["rank"], 2)
        self.assertIsNone(observation["score"])
        self.assertIsNone(observation["ci"])
        self.assertEqual(doc["boards"]["agent"]["meta"]["dimensions"], ["planning"])
        self.assertEqual(doc["boards"]["agent"]["rows_verbatim"], [row])

    def test_freshness_is_per_category_and_unknown_dates_stay_unknown(self):
        code, summary, doc, _, _ = self.capture({
            "code": _board([_row("orbit")], updated="Oct 7, 2026"),
            "text": _board([_row("orbit")], updated="Aug 24, 2026"),
            "document": _board([_row("orbit")], updated="not a date"),
        })
        self.assertEqual(code, 0, summary)
        self.assertEqual(doc["boards"]["code"]["staleness_days"], 15)
        self.assertEqual(doc["boards"]["code"]["staleness_status"], "fresh")
        self.assertEqual(doc["boards"]["text"]["staleness_status"], "stale")
        self.assertIsNone(doc["boards"]["document"]["staleness_days"])
        self.assertEqual(doc["boards"]["document"]["staleness_status"], "unknown")

    def test_a_partial_capture_records_gaps_and_an_entirely_empty_capture_fails(self):
        code, summary, doc, _, _ = self.capture({
            "code": _board([_row("orbit")]), "vision": "HTTPError: 404",
            "agent": _board([]),
        })
        self.assertEqual(code, 0, summary)
        self.assertEqual(doc["categories_captured"], ["code"])
        self.assertEqual({g["category"]: g["status"] for g in doc["gaps"]},
                         {"vision": "unreachable", "agent": "empty"})
        (self.tmp / "arena-2026-10-07.json").unlink()
        code, summary, doc, _, _ = self.capture({"agent": _board([])})
        self.assertEqual(code, 1)
        self.assertIn("every requested category", summary["reason"])
        self.assertIsNone(doc)


class TestArenaNames(unittest.TestCase):
    def test_display_punctuation_and_effort_spellings_share_an_identity_key(self):
        for name in ("claude-sonnet-5.5-xhigh", "Claude Sonnet 5_5 (xHigh)",
                     "claude-sonnet-5-5-high"):
            with self.subTest(name=name):
                self.assertEqual(benchmark.norm_key(name), "claudesonnet55")
        self.assertEqual(benchmark.effort_of("Muse Spark 1.3 (xHigh)"), "xhigh")
        self.assertEqual(benchmark.effort_of("claude-sonnet-5-5-high"), "high")
        self.assertIsNone(benchmark.effort_of("kimi-k3"))

    def test_a_version_is_not_an_effort_suffix(self):
        self.assertNotEqual(benchmark.norm_key("orbit-5.5-high"), benchmark.norm_key("orbit-5.6-high"))
        self.assertIsNone(benchmark.parse_board_date("yesterday"))


if __name__ == "__main__":
    unittest.main()
