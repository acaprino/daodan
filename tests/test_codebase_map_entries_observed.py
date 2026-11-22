"""The entries the browser found: a control the exploration pressed, that did something, and that no static candidate
stands for (plan task 11.4).

    python -B -m pytest -q -p no:cacheprovider tests/test_codebase_map_entries_observed.py
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

SCRIPTS = Path(__file__).resolve().parents[1] / "daodan/core"
sys.path.insert(0, str(SCRIPTS))

import observed_entries  # noqa: E402

FILES = {"src/App.tsx", "src/lib/actions.ts"}


def call(name: str, source: str | None, line: int | None = 1) -> dict:
    return {"url": "/src/x.ts", "source": source, "line": line, "name": name, "count": 1}


def control(name: str, *, role="button", state="pressed", calls=(), requests=(), **more) -> dict:
    return {"role": role, "name": name, "url": None, "occurrence": 0, "state": state, "calls": list(calls),
            "requests": list(requests), **more}


def pages(*controls: dict, url="http://localhost:5173/") -> list[dict]:
    return [{"declared_in": "package.json#scripts.dev", "pages": [{"url": url, "controls": list(controls)}]}]


SAVE = control("Save", calls=[call("save", "/work/app/src/lib/actions.ts", 5), call("validate", "src/lib/actions.ts", 1),
                              call("tick", "node_modules/x/y.js", 3)],
               requests=[{"method": "POST", "url": "http://localhost:5173/api/save"}])


def test_a_pressed_control_that_ran_project_code_and_no_static_candidate_has_is_an_entry():
    [row] = observed_entries.candidates(pages(SAVE), [], FILES)
    assert (row["reader"], row["shape"], row["status"]) == ("observed", "control", "candidate")
    assert (row["label"], row["event"], row["role"], row["site"]) == ("Save", "click", "button", "/")
    assert row["observed_calls"] == ["src/lib/actions.ts:1 validate", "src/lib/actions.ts:5 save"]
    assert row["requests"] == ["POST /api/save"]
    assert "not isolated" in row["gap"] and "handler" not in row  # the call tree is not recorded: no handler is named


def test_a_static_candidate_of_the_same_name_and_event_keeps_the_control_its_own():
    static = [{"reader": "attributo", "shape": "onClick", "site": "src/App.tsx:16", "label": " save ", "event": "click"}]
    assert observed_entries.candidates(pages(SAVE), static, FILES) == []
    other = [{"reader": "attributo", "shape": "onClick", "site": "src/App.tsx:16", "label": "Save", "event": "change"}]
    assert len(observed_entries.candidates(pages(SAVE), other, FILES)) == 1


def test_a_control_that_did_nothing_or_was_not_pressed_is_no_entry():
    quiet = control("Details", role="link")
    skipped = [control("Name", role="textbox", state="skipped", reason="needs_value"),
               control("Out", role="link", state="skipped", reason="leaves_the_app"),
               control("Broken", state="failed", reason="not_found_again")]
    library = control("Menu", calls=[call("toggle", "node_modules/ui/menu.js", 9), call("x", None, None)])
    assert observed_entries.candidates(pages(quiet, *skipped, library), [], FILES) == []


def test_a_request_alone_is_an_effect():
    [row] = observed_entries.candidates(pages(control("Refresh", requests=[{"method": "GET", "url": "/api/items"}])), [], FILES)
    assert row["requests"] == ["GET /api/items"] and row["observed_calls"] == []


def test_each_control_of_a_page_is_its_own_row_with_its_page():
    two = control("Delete", calls=[call("remove", "src/App.tsx", 7)])
    again = {**two, "occurrence": 1}
    found = observed_entries.candidates(pages(two, again, url="http://localhost:5173/details?id=3"), [], FILES)
    assert [(row["site"], row["occurrence"]) for row in found] == [("/details?id=3", 0), ("/details?id=3", 1)]


def test_the_rows_are_read_from_the_file_beside_the_manifest_and_none_without_it(tmp_path):
    manifest = tmp_path / "manifest.sqlite"
    assert observed_entries.rows(manifest, [], FILES) == []
    observed_entries.write(manifest, pages(SAVE))
    assert json.loads((tmp_path / observed_entries.FILE).read_text(encoding="utf-8"))["apps"][0]["pages"]
    assert [row["label"] for row in observed_entries.rows(manifest, [], FILES)] == ["Save"]


def test_the_public_candidates_carry_the_observed_rows_beside_the_static_ones(tmp_path):
    import entries
    import snapshot
    project = tmp_path / "proj"
    (project / "src/lib").mkdir(parents=True)
    (project / "src/lib/actions.ts").write_text("export function save(n: number) { return n + 1; }\n", encoding="utf-8")
    manifest = tmp_path / "out" / "manifest.sqlite"
    snapshot.write_snapshot(project, manifest)
    assert [row for row in entries.cached_syntax(manifest) if row["reader"] == "observed"] == []
    observed_entries.write(manifest, pages(SAVE))
    [row] = [row for row in entries.cached_syntax(manifest) if row["reader"] == "observed"]
    assert row["label"] == "Save"
    assert row["observed_calls"] == ["src/lib/actions.ts:1 validate", "src/lib/actions.ts:5 save"]


def test_a_source_the_dev_server_names_from_the_apps_root_is_found_under_the_apps_folder():
    """Vite serves `/src/lib/actions.ts` for `web/src/lib/actions.ts`: the app's folder, from its declared script."""
    apps = [{"declared_in": "web/package.json#scripts.dev",
             "pages": [{"url": "http://localhost:5173/", "controls": [
                 control("Save", calls=[call("save", "/src/lib/actions.ts", 5), call("other", "/src/lib/missing.ts", 2)])]}]}]
    [row] = observed_entries.candidates(apps, [], {"web/src/lib/actions.ts", "api/src/lib/actions.ts"})
    assert row["observed_calls"] == ["web/src/lib/actions.ts:5 save"]


def test_a_handler_the_browser_isolated_is_named_and_the_row_no_longer_says_it_is_not():
    """The pause of Chrome's own breakpoint on `click` (`explore.cjs`): the first project function the event reaches."""
    handled = control("Save", calls=[call("save", "/src/lib/actions.ts", 5)],
                      handler={"name": "onClick", "url": "/src/App.tsx", "source": "/src/App.tsx", "line": 6})
    apps = [{"declared_in": "web/package.json#scripts.dev",
             "pages": [{"url": "http://localhost:5173/", "controls": [handled]}]}]
    [row] = observed_entries.candidates(apps, [], {"web/src/App.tsx", "web/src/lib/actions.ts"})
    assert row["handler"] == "web/src/App.tsx:6 onClick" and row["handler_confidence"] == "observed"
    assert "gap" not in row and row["observed_calls"] == ["web/src/lib/actions.ts:5 save"]


def test_a_handler_outside_the_project_leaves_the_row_without_one():
    """A pause in a dependency's file names no function of the project: the handler is still not isolated."""
    odd = control("Save", calls=[call("save", "src/lib/actions.ts", 5)],
                  handler={"name": "dispatch", "url": "/lib/vendor.js", "source": None, "line": 80})
    [row] = observed_entries.candidates(pages(odd), [], FILES)
    assert "handler" not in row and "not isolated" in row["gap"]


def test_a_control_a_press_revealed_is_an_entry_that_says_what_opened_it():
    opener = control("Menu", requests=[], calls=[], revealed=[
        control("Settings", calls=[call("settings", "src/lib/actions.ts", 5)], opened_by=["Menu"])])
    [row] = observed_entries.candidates(pages(opener), [], FILES)
    assert (row["label"], row["opened_by"]) == ("Settings", ["Menu"]) and row["observed_calls"] == ["src/lib/actions.ts:5 settings"]
    assert "opened_by" not in observed_entries.candidates(pages(SAVE), [], FILES)[0]
