"""An event and its handler retain their identity even where evidence of later calls ends."""
from test_codebase_map_entries import entries, flows, snapshot_of


def test_inline_invokes_and_same_line_components_keep_their_own_handlers(tmp_path):
    manifest = snapshot_of(tmp_path, {
        "view.tsx": '''import {invoke} from "@tauri-apps/api/core";
function save(){} function cancel(){}
export function Pay(){return <button onClick={save}>Pay</button>} export function Cancel(){return <button onClick={cancel}>Cancel</button>}
export function Native(){return <button onClick={()=>invoke("pay")}>Native</button>}
export function Checkout(){return <button onClick={()=>{window.location.href="/payment"}}>Checkout</button>}
''',
        "src-tauri/src/main.rs": '''#[tauri::command]
fn pay(){}
fn main(){launch()}
fn launch(){tauri::Builder::default().setup(|_| Ok(())).invoke_handler(tauri::generate_handler![pay]).run(tauri::generate_context!());}
''',
    })
    links = flows.cached_links(manifest, [])
    handlers = {e["label"]: (e["from"], e["to"]) for e in links["edges"] if e["type"] == "attiva"}
    assert handlers["Pay"] == ("view.tsx::Pay", "view.tsx::save")
    assert handlers["Cancel"] == ("view.tsx::Cancel", "view.tsx::cancel")
    assert handlers["Native"][1].startswith("view.tsx::function@4:")
    assert handlers["Checkout"][1].startswith("view.tsx::function@5:")
    assert [(e["from"], e["to"]) for e in links["edges"] if e.get("resolver") == "tauri-invoke"] == [
        (handlers["Native"][1], "src-tauri/src/main.rs::pay")]
    assert not any(e["from"] == handlers["Checkout"][1] and e["type"] == "chiama" for e in links["edges"])


def test_test_only_and_mock_registrations_do_not_activate_a_rust_command(tmp_path):
    manifest = snapshot_of(tmp_path, {
        "view.ts": 'import {invoke} from "@tauri-apps/api/core";\nexport function save(){invoke("pay")}\n',
        "src-tauri/src/main.rs": '''#[tauri::command]
fn pay(){}
struct Mock;
impl Mock { fn invoke_handler<T>(self, x:T){} }
#[cfg(test)]
mod tests {
    fn test_only(){tauri::Builder::default().invoke_handler(tauri::generate_handler![pay]).run(tauri::generate_context!());}
}
fn never_called(){tauri::Builder::default().invoke_handler(tauri::generate_handler![pay]).run(tauri::generate_context!());}
fn main(){
    Mock.invoke_handler(tauri::generate_handler![pay]);
    tauri::Builder::default().invoke_handler(tauri::generate_handler![pay]);
}
''',
    })
    links = flows.cached_links(manifest, [])
    assert not any(e["to"].endswith("::pay") for e in links["edges"])
    assert any("no unique registered destination" in g["reason"] for g in links["gaps"])


def test_instance_reassignments_change_the_qt_label_and_do_not_prove_a_shadowed_tk_method(tmp_path):
    manifest = snapshot_of(tmp_path, {"ui.py": '''import tkinter as tk
from PySide6.QtWidgets import QPushButton
def other(): pass
class Win:
    def save(self): pass
    def wire(self):
        self.button = QPushButton("Cancel")
        self.button.clicked.connect(self.save)
        self.button = QPushButton("Pay")
        self.button.clicked.connect(self.save)
        self.save = other
        tk.Button(text="Submit", command=self.save)
        self.save = dynamic(other)
        tk.Button(text="Dynamic", command=self.save)
'''})
    rows = entries.cached_syntax(manifest)
    assert {(r["label"], r["site"]) for r in rows if r.get("event") == "clicked"} == {
        ("Cancel", "ui.py:8"), ("Pay", "ui.py:10")}
    [submit] = [r for r in rows if r.get("label") == "Submit"]
    assert submit["symbol"] == "ui.py::other"
    [dynamic] = [r for r in rows if r.get("label") == "Dynamic"]
    assert "assigns save at run time" in dynamic["gap"]
    rule = {"reader": "argomento", "shape": submit["shape"], "link": "ingresso", "source": "modello", "entry": entries.ENTRY_KINDS[0]}
    assert [(r["label"], r["symbol"]) for r in flows.cached_links(manifest, [rule])["entries"]] == [("Submit", "ui.py::other")]


def test_candidate_cache_rechecks_an_indexers_version_on_an_unchanged_snapshot(tmp_path, monkeypatch):
    import engine_pass
    import resolve_edges
    from indexers import typescript
    from snapshot_store import open_snapshot

    manifest = snapshot_of(tmp_path, {
        "actions.ts": "export function persist(){}\nexport function useSave(){return {onPress:persist}}\n",
        "view.tsx": '''import {useSave, persist as direct} from './actions';
export function View(){
 const {onPress}=useSave();
 return <div><button onClick={onPress}>A</button><button onClick={direct}>B</button></div>;
}
''',
    })
    official = {"engine": "scip-typescript@" + typescript.VERSION, "indexer": {"version": typescript.VERSION},
                "state": "fresh", "adapter_digest": engine_pass.adapter_fingerprint("typescript")}
    assert engine_pass.from_source("typescript", official)
    with open_snapshot(manifest) as store:
        db = store.connection
        [target] = db.execute("SELECT id FROM sem_declarations WHERE name='persist'").fetchone()
        binding = resolve_edges.store_binding(store, manifest, store.metadata["parser_fingerprint"], {"typescript": official}, {})
        edges = [{"reference_id": ref, "file": "view.tsx", "language": "typescript", "kind": "read", "caller": caller,
                  "l0": 4, "c0": col, "verdict": "project-callable", "target_id": target, "symbol": "persist",
                  "resolver": "scip-typescript", "confidence": "confirmed", "payload": {"chain": ["same-range"]}}
                 for ref, caller, col in db.execute("SELECT id,caller,c0 FROM sem_references WHERE file='view.tsx' AND l0=4 AND kind='read'")]
    resolve_edges.write_edge_store(resolve_edges.default_edge_store(manifest), edges, binding)
    def buttons():
        return [(r["label"], r["handler_source"]) for r in entries.cached_syntax(manifest) if r.get("event") == "click"]
    assert buttons() == [("A", "scip-typescript"), ("B", "scip-typescript")]
    flows.cached_links(manifest, [])
    monkeypatch.setattr(engine_pass, "adapter_fingerprint", lambda _: "updated")
    warm = buttons()
    assert warm == [("B", "builtin-lexical")]
    assert [r["label"] for r in flows.cached_links(manifest, [])["entries"]] == ["B"]
    manifest.with_name("entry-candidates.json").unlink()
    assert buttons() == warm


def test_old_tauri_resolution_requires_new_registration_evidence(tmp_path):
    import sqlite3
    from snapshot_store import _pack, _unpack

    manifest = snapshot_of(tmp_path, {
        "view.ts": 'import {invoke} from "@tauri-apps/api/core"; export function send(){invoke("pay")}',
        "src-tauri/src/main.rs": '''#[tauri::command]
fn pay(){}
fn main(){tauri::Builder::default().invoke_handler(tauri::generate_handler![pay]).run(tauri::generate_context!());}
''',
    })
    assert any(e.get("resolver") == "tauri-invoke" for e in flows.cached_links(manifest, [])["edges"])
    # Before this reader, the structural index could bind the same type of reference on a mock.
    with sqlite3.connect(manifest) as db:
        ref, blob = db.execute("SELECT id,payload FROM sem_references WHERE target_id LIKE '%.rs::%'").fetchone()
        payload = _unpack(blob)
        del payload["tauri_registration_version"]
        db.execute("UPDATE sem_references SET payload=? WHERE id=?", (_pack(payload), ref))
    links = flows.cached_links(manifest, [])
    assert not any(e["to"].endswith("::pay") for e in links["edges"])
    assert any("Tauri" in g["reason"] for g in links["gaps"])


def test_mobile_startup_and_programmatic_web_event_preserve_the_callback_before_invoke(tmp_path):
    manifest = snapshot_of(tmp_path, {
        "view.ts": '''import {invoke} from "@tauri-apps/api/core";
export function wire(){document.addEventListener("click",()=>invoke("pay"))}
export function page(){button("Pay",()=>invoke("pay"))}
''',
        "src-tauri/src/lib.rs": '''#[tauri::command]
fn pay(){}
#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run(){tauri::Builder::default().invoke_handler(tauri::generate_handler![pay]).run(tauri::generate_context!());}
''',
    })
    [candidate] = [c for c in entries.cached_syntax(manifest) if c.get("event") == "click"]
    assert candidate["symbol"].startswith("view.ts::function@2:")
    links = flows.cached_links(manifest, [{"written": "button", "link": "attiva", "handler": "arg1"}])
    [custom] = [edge for edge in links["edges"] if edge["type"] == "attiva" and edge.get("label") == "Pay"]
    assert custom["to"].startswith("view.ts::function@3:")
    assert {(e["from"], e["to"]) for e in links["edges"] if e.get("resolver") == "tauri-invoke"} == {
        (candidate["symbol"], "src-tauri/src/lib.rs::pay"), (custom["to"], "src-tauri/src/lib.rs::pay")}
