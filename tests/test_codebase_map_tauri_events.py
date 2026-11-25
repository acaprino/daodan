"""The events between a Tauri shell and its page: an `emit` on one side and a `listen` on the other, joined by the event's name
(plan task 11b; spec of the project's interfaces, 4.3).

A name is a key, not a resolution: an event has no declaration, so the pair is a link with both positions, the emitter's call
(`site`) and the listener's (`target_site`), `resolver` `tauri-event` and the name as `event`. What proves the call is Tauri's:
on the page the import of `listen`, `once`, `emit` or `emitTo` from `@tauri-apps/api/event`; in Rust the import of the trait that
has the method, `tauri::Emitter` or `tauri::Listener` (the signatures are those of `@tauri-apps/api@2`'s `event.d.ts` and of
`tauri` 2.12.7's traits). A method of that name on any other value proves nothing and is no link. The trees are read engine-less.

    python -B -m pytest -q -p no:cacheprovider tests/test_codebase_map_tauri_events.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_codebase_map_entries import flows, snapshot_of  # noqa: E402

PAGE = ('import {listen} from "@tauri-apps/api/event";\n'
        'export function start() { return listen("progress", onProgress); }\n'
        'function onProgress(event: unknown) { return event; }\n')
SHELL = ('use tauri::Emitter;\n'
         'fn report(app: tauri::AppHandle) { app.emit("progress", 1).unwrap(); }\n'
         'fn main() { tauri::Builder::default().run(tauri::generate_context!()); }\n')


def events(manifest) -> tuple[list[dict], list[dict]]:
    links = flows.cached_links(manifest, [])
    return [e for e in links["edges"] if e.get("resolver") == "tauri-event"], \
        [g for g in links["gaps"] if g["reason"].startswith("Tauri event")]


def test_an_emit_in_rust_and_a_listen_in_the_page_on_the_same_name_are_one_link_with_both_positions(tmp_path):
    manifest = snapshot_of(tmp_path, {"src/view.ts": PAGE, "src-tauri/src/main.rs": SHELL})
    [link], gaps = events(manifest)
    assert (link["from"], link["to"], link["event"]) == ("src-tauri/src/main.rs::report", "src/view.ts::onProgress", "progress")
    assert (link["site"], link["target_site"], link["type"], link["origin"]) == (
        "src-tauri/src/main.rs:2", "src/view.ts:2", "chiama", "dedotto")
    assert gaps == []


def test_the_page_emits_and_rust_listens_and_a_closure_ends_at_the_function_that_holds_the_listen(tmp_path):
    page = 'import {emit} from "@tauri-apps/api/event";\nexport function ping() { return emit("ping", 1); }\n'
    shell = ('use tauri::Listener;\n'
             'fn setup(app: &tauri::App) { app.listen("ping", |_event| {}); }\n'
             'fn main() { tauri::Builder::default().run(tauri::generate_context!()); }\n')
    manifest = snapshot_of(tmp_path, {"src/view.ts": page, "src-tauri/src/main.rs": shell})
    [link], _gaps = events(manifest)
    assert (link["from"], link["to"], link["event"]) == ("src/view.ts::ping", "src-tauri/src/main.rs::setup", "ping")
    assert (link["site"], link["target_site"]) == ("src/view.ts:2", "src-tauri/src/main.rs:2")


def test_two_different_names_do_not_link(tmp_path):
    manifest = snapshot_of(tmp_path, {"src/view.ts": PAGE.replace('"progress"', '"done"'), "src-tauri/src/main.rs": SHELL})
    assert events(manifest) == ([], [])


def test_one_emit_with_two_listeners_is_a_link_to_each(tmp_path):
    page = PAGE + ('export function again() { return listen("progress", (event) => event); }\n')
    manifest = snapshot_of(tmp_path, {"src/view.ts": page, "src-tauri/src/main.rs": SHELL})
    links, _gaps = events(manifest)
    assert sorted(link["target_site"] for link in links) == ["src/view.ts:2", "src/view.ts:4"]
    assert {link["from"] for link in links} == {"src-tauri/src/main.rs::report"}


def test_a_name_that_is_not_a_literal_is_a_gap_with_its_point_and_never_a_link(tmp_path):
    page = 'import {listen} from "@tauri-apps/api/event";\nexport function start(name: string) { return listen(name, () => {}); }\n'
    shell = SHELL.replace('"progress"', "NAME")
    manifest = snapshot_of(tmp_path, {"src/view.ts": page, "src-tauri/src/main.rs": shell})
    links, gaps = events(manifest)
    assert links == [] and sorted(gap["site"] for gap in gaps) == ["src-tauri/src/main.rs:2", "src/view.ts:2"]
    assert all("not a string literal" in gap["reason"] for gap in gaps)


def test_an_emit_or_a_listen_that_tauri_does_not_own_proves_nothing(tmp_path):
    """The same names on an event emitter of Node, a bus of the project and a Rust method with no Tauri trait in scope."""
    page = ('import {EventEmitter} from "events";\nimport {listen} from "./local";\n'
            'const bus = new EventEmitter();\n'
            'export function start() { bus.emit("progress", 1); return listen("progress", () => {}); }\n')
    shell = ('struct Bus;\nimpl Bus { fn emit(&self, name: &str, value: i32) {} }\n'
             'fn report(bus: Bus) { bus.emit("progress", 1); }\n')
    manifest = snapshot_of(tmp_path, {"src/view.ts": page, "src/local.ts": "export function listen(name: string, handler: () => void) {}\n",
                                      "src-tauri/src/main.rs": shell})
    assert events(manifest) == ([], [])


def test_an_event_between_two_files_of_the_page_is_not_a_link_of_this_kind(tmp_path):
    """Only a pair across the shell and the page is read: both ends in TypeScript are the page talking to itself."""
    emitter = 'import {emit} from "@tauri-apps/api/event";' + chr(10) + 'export function go() { return emit("progress", 1); }' + chr(10)
    manifest = snapshot_of(tmp_path, {"src/view.ts": PAGE, "src/b.ts": emitter})
    assert events(manifest) == ([], [])
