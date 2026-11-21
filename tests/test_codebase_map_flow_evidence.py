"""A rule, a saved map and inverse reachability must all respect the same evidence."""
import json

from test_codebase_map_dynamic import code_graph, dynamic, observer, static_store, write_project

import edge_store
import engine_pass
import flow_paths
import flows
import system_map
import visual

FILES = {
    "controls.py": '@trigger("refresh")\ndef dispatch(fn):\n    fn("orders")\n',
    "handlers.py": "def save(key): pass\ndef cancel(key): pass\n",
}
ENTRY = "controls.py::dispatch"
EFFECT = "store:db/orders"
RULES = [
    {"link": "ingresso", "written": "trigger", "entry": "comando", "decorates": True},
    {"link": "scrive", "callee": "handlers.py::save", "store": "db", "key": "arg0"},
]
AREA = "pagamenti e abbonamenti"


def ordinary_map():
    return {"scope": [AREA], "nodes": [
        {"name": "Invio", "type": "funzionalità", "members": [ENTRY]},
        {"name": "Ordini", "type": "entità", "members": [EFFECT]}],
        "flows": [{"name": "Registrazione degli ordini", "types": ["funzionale"], "area": AREA,
                   "nodes": ["Invio", "Ordini"], "entries": ["Invio"], "effects": ["Ordini"],
                   "arrows": [{"from": "Invio", "to": "Ordini", "data": "ordine"}]}]}


def install_observation(manifest, name, *, sampled=False):
    with code_graph.Snapshot(manifest) as snap:
        out = edge_store.default_edge_store(manifest)
        static, _, _ = edge_store.read_edge_store(out, snap.store)
        decl, line = snap.connection.execute("SELECT id,l0 FROM sem_declarations WHERE name=?", (name,)).fetchone()
        ref, caller, line0, col = snap.connection.execute(
            "SELECT id,caller,l0,c0 FROM sem_references WHERE last_name='fn' AND kind='call'").fetchone()
        if sampled:
            rows = [{"file": "controls.py", "reference_id": ref, "kind": "call", "caller": caller, "l0": line0,
                     "c0": col, "language": "python", "confidence": "sampled", "resolver": "fixture-sampler",
                     "verdict": "project-callable", "target_id": decl, "symbol": name, "payload": {}}]
            facts = {}
        else:
            sites = [{"file": "controls.py", "line": line0 - 1, "column": col, "name": "fn", "role": "call",
                      "callees": [{"kind": "project", "name": name, "file": "handlers.py", "line": line - 1}]}]
            rows, facts = dynamic.join(snap, "python", sites, static, observer)
        code_graph.write_observed(snap, out, "python", rows, {"resolver": "fixture", **facts})
        return facts


def test_sampled_callee_cannot_certify_a_write_or_an_inverse_path(tmp_path):
    _, manifest = write_project(tmp_path, FILES)
    static_store(manifest)
    install_observation(manifest, "save", sampled=True)
    for _ in range(2):  # Reload the published links and trace cache, too.
        links = flows.cached_links(manifest, RULES)
        card, = flow_paths.page(manifest, RULES)["cards"]
        steps = flow_paths.page(manifest, RULES, card_id=card["card_id"])["steps"]
        write, = [s for s in steps if s["to"] == EFFECT]
        assert (write["end"], write["confidence"], write["resolver"]) == ("lacuna", "sampled", "fixture-sampler")
        decision = {"card_id": card["card_id"], "steps": [write["n"]], "data": ["ordine"],
                    "name": "Registrazione degli ordini", "area": AREA, "types": ["funzionale"]}
        assert flow_paths.record(manifest, RULES, decision)["status"] == "refused"
        for target in (EFFECT, "handlers.py::save"):
            result = flows.trace(links, target, "through")
            assert not result["entries"] and not result["complete"]
        direct = flows.trace(links, ENTRY, "from")
        assert EFFECT not in direct["nodes"] and any(g.get("to") == EFFECT for g in direct["gaps"])
    report = system_map.record(manifest, RULES, ordinary_map())["flows"][0]
    assert (report["status"], report["reachability"]) == ("refused", "unproved")
    # A separate rule about the literal call syntax does not require knowing
    # which project function the sampled frame represents.
    independent = [*RULES, {"link": "scrive", "written": "fn", "store": "db", "key": "arg0"}]
    result = system_map.record(manifest, independent, ordinary_map())["flows"][0]
    assert result["reachability"] == "verified"
    assert all("confidence" not in p for p in result["arrows"][0]["proof"])


def test_an_exact_observation_disagreeing_with_scip_rechecks_the_saved_flow(tmp_path):
    _, manifest = write_project(tmp_path, FILES)
    with code_graph.Snapshot(manifest) as snap:
        save, = snap.connection.execute("SELECT id FROM sem_declarations WHERE name='save'").fetchone()
    static_store(manifest, {("controls.py", 3, "fn"): save})
    assert system_map.record(manifest, RULES, ordinary_map())["flows"][0]["reachability"] == "verified"
    assert install_observation(manifest, "cancel")["conflicts"]["count"] == 1
    for _ in range(2):
        loaded = system_map.load(manifest, RULES)["flows"][0]
        assert (loaded["reachability"], loaded["fresh"]) == ("unproved", False)
        edges = flows.cached_links(manifest, RULES)["edges"]
        site = [e for e in edges if e["site"] == "controls.py:3"]
        assert {e["to"] for e in site} == {"handlers.py::save", "handlers.py::cancel", EFFECT}
        assert all(e["conflict"] for e in site)
    assert install_observation(manifest, "save")["agree"] == 1
    assert system_map.load(manifest, RULES)["flows"][0]["reachability"] == "verified"


def test_an_old_callee_based_write_survives_only_exact_evidence(tmp_path):
    _, manifest = write_project(tmp_path, FILES)
    static_store(manifest)
    assert install_observation(manifest, "save")["joined"] == 1
    card, = flow_paths.page(manifest, RULES)["cards"]
    steps = flow_paths.page(manifest, RULES, card_id=card["card_id"])["steps"]
    write, = [s for s in steps if s["to"] == EFFECT]
    result = flow_paths.record(manifest, RULES, {
        "card_id": card["card_id"], "steps": [write["n"]], "data": ["ordine"],
        "name": "Registrazione degli ordini", "area": AREA, "types": ["funzionale"]})
    assert result["status"] == "accepted"
    path = manifest.with_name(system_map.FILE)
    prior = json.loads(path.read_text())
    pin, = prior["flows"][0]["trace"]["steps"]
    assert pin.pop("confidence") == "observed"
    pin.pop("resolver")
    path.write_text(json.dumps(prior))
    loaded, = system_map.load(manifest, RULES)["flows"]
    assert loaded["fresh"] and loaded["arrows"][0]["proof"][0]["confidence"] == "observed"
    install_observation(manifest, "save", sampled=True)
    loaded, = system_map.load(manifest, RULES)["flows"]
    assert not loaded["fresh"] and loaded["reachability"] == "unproved"


def test_live_graph_stamp_tracks_input_files_and_the_indexer_identity(tmp_path, monkeypatch):
    _, manifest = write_project(tmp_path, FILES)
    directory = tmp_path / "run" / "snapshot"
    directory.mkdir(parents=True)
    manifest = manifest.rename(directory / "manifest.sqlite")
    static_store(manifest)
    stamp = visual.inputs_stamp(directory.parent)
    original = engine_pass.adapter_fingerprint
    monkeypatch.setattr(engine_pass, "adapter_fingerprint", lambda name: "changed" if name == "python" else original(name))
    changed = visual.inputs_stamp(directory.parent)
    assert changed != stamp
    from premap import path
    path(manifest).write_text("{}")
    assert visual.inputs_stamp(directory.parent) != changed
