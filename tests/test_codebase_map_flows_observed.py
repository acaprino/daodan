"""A control the browser pressed is an entry of the links when its handler is a function of the snapshot (plan task 11.4).

The links are `flows.cached_links`; the controls come from the file `observed-controls.json` beside the manifest
(`observed_entries`), which the exploration writes. A handler the browser isolated is found in the snapshot as the
Noir reader's endpoints are: by its name and the lines of its declaration, and only when exactly one function fits.

    python -B -m pytest -q -p no:cacheprovider tests/test_codebase_map_flows_observed.py
"""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "daodan/core"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import observed_entries  # noqa: E402
from test_codebase_map_entries import flows, snapshot_of  # noqa: E402

LIB = "export function save(n: number) {\n  return n + 1;\n}\n"
ALONE = {"src/lib.ts": LIB}


def pressed(name: str, handler: dict | None, **more) -> dict:
    """A control that ran `save` (so it is an entry) and whose handler the browser named as `handler`."""
    return {"role": "button", "name": name, "url": None, "occurrence": 0, "state": "pressed", "requests": [],
            "calls": [{"url": "/src/lib.ts", "source": "src/lib.ts", "line": 1, "name": "save", "count": 1}],
            **({"handler": handler} if handler else {}), **more}


def keep(manifest: Path, *controls: dict) -> None:
    observed_entries.write(manifest, [{"declared_in": "package.json#scripts.dev",
                                       "pages": [{"url": "http://localhost:5173/", "controls": list(controls)}]}])


def named(name: str, line: int = 2) -> dict:
    return {"name": name, "url": "/assets/index.js", "source": "/src/lib.ts", "line": line}


def started(file: str, line: int, at: int, column: int, name: str = "onClick") -> dict:
    """What the browser gives for a handler: the place it paused at (`line`) and where the function starts (`at`, `column`)."""
    return {"name": name, "url": "/assets/index.js", "source": f"/{file}", "line": line, "start": {"line": at, "column": column}}


def test_a_control_whose_handler_the_browser_isolated_starts_a_flow_at_that_handler(tmp_path):
    manifest = snapshot_of(tmp_path, ALONE)
    assert flows.cached_links(manifest, [])["entries"] == []
    keep(manifest, pressed("Save", named("save")))
    [entry] = flows.cached_links(manifest, [])["entries"]  # the file appearing recomputes the links
    assert (entry["symbol"], entry["site"], entry["kind"]) == ("src/lib.ts::save", "src/lib.ts:1", observed_entries.KIND)
    assert (entry["reader"], entry["label"], entry["handler_confidence"]) == ("observed", "Save", "observed")
    (tmp_path / "snapshot" / observed_entries.FILE).unlink()
    assert flows.cached_links(manifest, [])["entries"] == []  # and so does its going


def test_a_handler_no_function_of_the_snapshot_holds_is_no_entry_and_a_gap(tmp_path):
    manifest = snapshot_of(tmp_path, ALONE)
    keep(manifest, pressed("Elsewhere", named("save", line=40)), pressed("Unisolated", None),
         pressed("Another file", {"name": "save", "url": "/assets/index.js", "source": "/src/none.ts", "line": 2}))
    links = flows.cached_links(manifest, [])
    assert links["entries"] == []  # they stay candidates, with the gap that says why
    assert [gap["site"] for gap in links["gaps"]] == ["src/lib.ts:40"]  # none for the other two: no place in the snapshot
    assert all("observed" in gap["reason"] for gap in links["gaps"])


WIRED = ("export function wire(el: HTMLElement) {\n  el.addEventListener(\"click\", () => {\n    save(1);\n  });\n}\n")


def test_an_inline_arrow_is_its_own_node_and_the_function_that_holds_it_activates_it(tmp_path):
    manifest = snapshot_of(tmp_path, {"src/lib.ts": LIB, "src/wire.ts": 'import {save} from "./lib";\n' + WIRED})
    keep(manifest, pressed("Wired", {"name": "onClick", "url": "/assets/index.js", "source": "/src/wire.ts", "line": 4}))
    links = flows.cached_links(manifest, [])
    [entry] = links["entries"]
    assert entry["symbol"].startswith("src/wire.ts::function@3:") and entry["site"] == "src/wire.ts:3"
    assert [(edge["from"], edge["to"], edge["label"]) for edge in links["edges"] if edge["type"] == "attiva"] == [
        ("src/wire.ts::wire", entry["symbol"], "Wired")]


def test_two_controls_of_one_handler_are_one_entry(tmp_path):
    manifest = snapshot_of(tmp_path, ALONE)
    keep(manifest, pressed("Save", named("save")), pressed("Save again", named("save")))
    assert [entry["symbol"] for entry in flows.cached_links(manifest, [])["entries"]] == ["src/lib.ts::save"]


def test_a_handler_the_static_reader_already_starts_from_is_not_an_entry_twice(tmp_path):
    manifest = snapshot_of(tmp_path, {
        "src/lib.ts": LIB,
        "src/View.tsx": 'import {save} from "./lib";\nexport function View() { return <button onClick={save}>Pay</button>; }\n'})
    before = flows.cached_links(manifest, [])
    assert [entry["symbol"] for entry in before["entries"]] == ["src/lib.ts::save"]  # the static reader starts there
    keep(manifest, pressed("Paga", named("save")))
    assert flows.cached_links(manifest, [])["entries"] == before["entries"]


NEST = ('export function wire(el: HTMLElement, set: (f: (o: boolean) => boolean) => void) {' + "\n"
        '  el.addEventListener("click", () => {' + "\n"
        '    set(o => !o);' + "\n"
        '  });' + "\n"
        '}' + "\n")
FLAT = ('export function wire(el: HTMLElement, set: (f: (o: boolean) => boolean) => void) {' + "\n"
        '  el.addEventListener("click", () => set(o => !o));' + "\n"
        '}' + "\n")


def test_the_handler_is_the_function_that_starts_where_the_browser_says_not_a_callback_its_first_statement_holds(tmp_path):
    """The pause is at the handler's first statement, which here is the line of a callback that starts on it."""
    manifest = snapshot_of(tmp_path, {"src/lib.ts": LIB, "src/wire.ts": NEST})
    keep(manifest, pressed("Toggle", started("src/wire.ts", line=3, at=2, column=31)))
    [entry] = flows.cached_links(manifest, [])["entries"]
    assert entry["symbol"].startswith("src/wire.ts::function@2:") and entry["site"] == "src/wire.ts:2"


def test_two_functions_on_the_line_the_handler_starts_at_are_told_apart_by_the_column(tmp_path):
    manifest = snapshot_of(tmp_path, {"src/lib.ts": LIB, "src/wire.ts": FLAT})
    keep(manifest, pressed("Toggle", started("src/wire.ts", line=2, at=2, column=31)),
         pressed("Inner", started("src/wire.ts", line=2, at=2, column=41)))
    links = flows.cached_links(manifest, [])
    assert sorted(entry["symbol"].partition("@")[2] for entry in links["entries"]) == ["2:31", "2:41"]


def test_a_control_the_browser_pressed_is_a_card_with_its_label_event_and_handler(tmp_path):
    """The cards of the paths (`flow_paths`) are the entries of the links: an observed one carries the control's name."""
    import flow_paths
    manifest = snapshot_of(tmp_path, ALONE)
    keep(manifest, pressed("Save", named("save")))
    _links, cards, _revision = flow_paths._deck(manifest, [])
    [card] = [card for card in cards.values() if card.get("reader") == "observed"]
    assert (card["label"], card["event"], card["handler"], card["kind"]) == (
        "Save", "click", "src/lib.ts::save", observed_entries.KIND)
    assert card["handler_confidence"] == "observed" and card["site"] == "src/lib.ts:1"
    [step] = flow_paths._steps(flow_paths._graph(_links, None), card)[:1]
    assert step["from"] == "src/lib.ts::save"  # the path starts at the handler the browser named


def test_a_handler_the_static_reader_could_not_name_is_an_entry_though_it_has_a_candidate_of_the_same_name(tmp_path):
    """The static candidate (`Save`, click) is there with a prop for a handler: no entry. The browser ran `save`: that is one."""
    manifest = snapshot_of(tmp_path, {
        "src/lib.ts": LIB,
        "src/View.tsx": "export function View(props: {onSave: () => void}) { return <button onClick={props.onSave}>Save</button>; }\n"})
    assert flows.cached_links(manifest, [])["entries"] == []
    keep(manifest, pressed("Save", named("save")))
    [entry] = flows.cached_links(manifest, [])["entries"]
    assert (entry["symbol"], entry["reader"], entry["label"]) == ("src/lib.ts::save", "observed", "Save")


def test_a_static_candidate_of_the_same_name_does_not_hide_a_handler_the_browser_ran_that_the_candidate_does_not_start_from(tmp_path):
    """On phazly the static reader gave `Dismiss` the member of a context's interface (`clearError`), a declaration with no body; the
    browser ran the arrow that implements it. The two are told apart by the function, not by the name of the control: here the
    static entry is the arrow of `Save` and the browser says `save`, the function it calls."""
    view = 'import {save} from "./lib";\nexport function View() { return <button onClick={() => save(1)}>Save</button>; }\n'
    manifest = snapshot_of(tmp_path, {"src/lib.ts": LIB, "src/View.tsx": view})
    [static] = flows.cached_links(manifest, [])["entries"]
    assert static["label"] == "Save" and static["symbol"].startswith("src/View.tsx::function@")
    keep(manifest, pressed("Save", named("save")))
    entries = flows.cached_links(manifest, [])["entries"]
    assert sorted(entry["symbol"] for entry in entries) == sorted([static["symbol"], "src/lib.ts::save"])
