"""The pure part of `modal_scan_cost.py`: the counts per reason of exclusion, the import pairs across the line, the
totals per corpus, the median of the repetitions and the rhythm. Run on this PC (Modal's client and pytest from uv, nothing
is built): uv run --no-project --with modal --with pytest python -m pytest benchmarks/project-model/test_modal_scan_cost.py"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parents[1] / "daodan/core")]

import modal_scan_cost as cost  # noqa: E402

HEADERS = {
    "vendor/jquery.js": {"status": "parsed", "size": 300, "language": "javascript"},
    "vendor/min.js": {"status": "parse-error", "size": 100, "language": "javascript"},
    "vendor/logo.png": {"status": "file-level", "size": 50, "language": None},
    "gen/api.ts": {"status": "parsed", "size": 200, "language": "typescript"},
    "src/app.ts": {"status": "parsed", "size": 400, "language": "typescript"},
}
HELD = {"vendor/jquery.js": "vendored", "vendor/min.js": "vendored", "vendor/logo.png": "binary", "gen/api.ts": "generated"}


def test_each_reason_counts_its_files_bytes_symbols_and_the_ones_a_parser_read():
    found = cost.by_reason(HELD, HEADERS, {"vendor/jquery.js": 40, "vendor/min.js": 2, "gen/api.ts": 7, "src/app.ts": 9})
    assert found["vendored"] == {"files": 2, "parsed": 2, "statuses": {"parsed": 1, "parse-error": 1}, "bytes": 400,
                                 "parsed_bytes": 400, "symbols": 42, "languages": {"javascript": 2}}
    assert found["binary"] == {"files": 1, "parsed": 0, "statuses": {"file-level": 1}, "bytes": 50, "parsed_bytes": 0,
                               "symbols": 0, "languages": {"none": 1}}
    assert set(found) == {"vendored", "binary", "generated"} and found["generated"]["symbols"] == 7


def test_the_folders_that_hold_the_files_a_parser_read_come_per_reason_by_their_first_two_segments():
    held = {**HELD, "vendor/deep/a/x.js": "vendored", "vendor/deep/b/y.js": "vendored"}
    headers = {**HEADERS, "vendor/deep/a/x.js": {"status": "parsed"}, "vendor/deep/b/y.js": {"status": "parsed"}}
    found = cost.top_folders(held, headers, {"vendor/deep/a/x.js": 3, "gen/api.ts": 7}, limit=2)
    assert found["vendored"] == [{"folder": "vendor", "files": 2, "symbols": 0},  # as many files: by name
                                 {"folder": "vendor/deep", "files": 2, "symbols": 3}]
    assert found["generated"] == [{"folder": "gen", "files": 1, "symbols": 7}]
    assert "binary" not in found  # no parser read it


def test_a_file_that_stays_is_in_no_reason():
    assert "src/app.ts" not in str(cost.by_reason({}, HEADERS, {}))
    assert cost.by_reason({}, HEADERS, {}) == {}


def test_an_import_pair_counts_once_however_many_specifiers_reach_the_target():
    resolved = {"src/app.ts": {"./api": ["gen/api.ts"], "./api.ts": ["gen/api.ts"], "./util": ["src/util.ts"]},
                "src/other.ts": {"../gen/api": ["gen/api.ts"]}}
    found = cost.import_pairs(resolved, HELD)
    assert found["to"] == {"generated": {"pairs": 2, "importers": 2}}
    assert found["from"] == {}


def test_a_pair_between_two_excluded_files_crosses_no_line_and_the_other_direction_is_counted_apart():
    resolved = {"gen/api.ts": {"./x": ["src/app.ts"], "../vendor/min": ["vendor/min.js"]},
                "src/app.ts": {"./api": ["gen/api.ts"]}}
    found = cost.import_pairs(resolved, HELD)
    assert found["to"] == {"generated": {"pairs": 1, "importers": 1}}
    assert found["from"] == {"generated": {"pairs": 1}}


def record(corpus, excluded, files=10, parsed=8, known=True, not_recorded=None, **extra):
    return {"corpus": corpus, "known": known, "not_recorded": not_recorded or {}, "files": files, "parsed_files": parsed,
            "excluded": {"files": sum(item["files"] for item in excluded.values()), "by_reason": excluded}, **extra}


def test_the_totals_add_each_corpus_apart_and_leave_a_project_with_unknown_exclusions_out_of_them():
    vendored = {"files": 3, "parsed": 2, "bytes": 30, "parsed_bytes": 20, "symbols": 5, "to_pairs": 1, "to_importers": 1}
    fixtures = {
        "js-a": record("miniature", {"vendored": vendored}),
        "js-b": record("miniature", {"vendored": vendored, "generated": {**vendored, "files": 1}}),
        "real-x": record("real", {"vendored": vendored}, files=100, parsed=80),
        "real-y": record("real", {"vendored": vendored}, known=False, not_recorded={"daodan-enry": 1, "noir": 1}),
        "real-z": record("real", {"vendored": vendored}, not_recorded={"noir": 1}),
        "real-w": {"error": "no archive"},
    }
    found = cost.summarize(fixtures)
    assert found["miniature"]["projects"] == 2 and found["miniature"]["files"] == 20 and found["miniature"]["parsed"] == 16
    assert found["miniature"]["by_reason"]["vendored"]["files"] == 6
    assert found["miniature"]["by_reason"]["vendored"]["projects"] == 2
    assert found["miniature"]["by_reason"]["generated"]["projects"] == 1
    assert found["miniature"]["excluded"] == 7
    assert found["real"]["projects"] == 2 and found["real"]["by_reason"]["vendored"]["to_pairs"] == 2
    assert found["incomplete"] == {"real-y": {"corpus": "real", "not_recorded": {"daodan-enry": 1, "noir": 1}}}
    assert found["not_recorded"] == {"daodan-enry": 1, "noir": 2}  # the commands not recorded, per tool
    assert found["failed"] == {"real-w": "no archive"}


def test_the_median_of_the_repetitions_is_taken_per_measure():
    runs = [{"inventory": 3.0, "reading": 9.0}, {"inventory": 1.0, "reading": 10.0}, {"inventory": 2.0, "reading": 8.0}]
    assert cost.median_runs(runs) == {"inventory": 2.0, "reading": 9.0}


def test_the_old_rule_chooses_the_files_that_import_the_decorator_from_the_core_package():
    headers = {
        "a.ts": {"language": "typescript", "import_bindings": [{"module": "@angular/core", "names": ["Component", "Input"]}]},
        "b.ts": {"language": "typescript", "import_bindings": [{"module": "@angular/core", "names": ["Injectable"]}]},
        "c.ts": {"language": "typescript", "import_bindings": [{"module": "./core", "names": ["Component"]}]},
        "d.js": {"language": "javascript", "import_bindings": [{"module": "@angular/core", "names": ["Component"]}]},
        "e.ts": {"language": "typescript"},
    }
    assert cost.old_component_files(headers, "@angular/core", "Component") == ["a.ts"]


def test_the_rhythm_is_files_and_megabytes_per_second_and_none_without_time():
    assert cost.rate(200, 4 * 2**20, 2.0) == {"files_per_second": 100.0, "mb_per_second": 2.0}
    assert cost.rate(0, 0, 0.0) is None


def test_the_largest_project_is_the_one_with_most_bytes_of_the_language():
    samples = {"a": {"typescript": {"files": 900, "bytes": 10}}, "b": {"typescript": {"files": 5, "bytes": 99}},
               "c": {"typescript": None}}
    assert cost.largest(samples) == "b"
    assert cost.largest({"c": {"typescript": None}}) is None


def test_the_reading_totals_add_the_medians_and_give_the_share_of_the_re_read_bytes():
    def item(inventory, reading, reread):
        median = {"inventory": inventory, "reading": reading, "seal": reading / 2, "pass": 1.0, "reread": reread,
                  "reread_files": 10, "reread_bytes": 1000}
        return {"files": 10, "bytes": 1000, "reading": {"runs": [median], "median": median}}
    fixtures = {"real-a": item(1.0, 3.0, 0.5), "real-b": item(2.0, 6.0, 1.5), "js-c": {"files": 3, "bytes": 9}}
    found = cost.reading_totals(fixtures)
    assert (found["projects"], found["inventory"], found["reading"], found["reread"]) == (2, 3.0, 9.0, 2.0)
    assert found["reread_share"] == round(2.0 / 12.0, 4)
    assert found["repetitions"] == {1: 2}  # how many projects have each number of repetitions
    assert [row["project"] for row in found["slowest"]] == ["real-b", "real-a"]
