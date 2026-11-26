"""The recorded scanner answer, container boundary and a second read of the same snapshot."""
import hashlib
import json
from unittest.mock import patch

from test_codebase_map_premap_container_runner import container, container_runner, manifest_of, premap, recorder


def test_noir_candidates_reopen_without_running_a_command_or_installing_packages(tmp_path):
    from premap import noir
    import entries
    import flows
    _, manifest = manifest_of(tmp_path, {"api.py": "def submit():\n    pass\n\ndef cancel():\n    pass\n"})
    route = {"protocol": "http", "url": "/submit", "method": "POST",
             "handler": {"path": "/work/api.py", "line": 1, "name": "submit"}}
    outside = {**route, "handler": {**route["handler"], "path": "/work/vendor/other.py"}}
    calls, run = recorder([{"returncode": 0, "stdout": json.dumps({"endpoints": [route, outside]}), "stderr": ""}])
    runner = container_runner.runner(manifest)
    with patch.object(container, "run_commands", run):
        original = premap.ensure(manifest, (noir,), runner)
        with patch.object(premap, "inventory_digest", side_effect=AssertionError("unchanged snapshot reread")):
            assert premap.ensure(manifest, (noir,), runner) == original
            assert len(noir.recorded(manifest)) == 1
    [call] = calls
    setup, scan = call["commands"]
    assert scan["argv"] == ["noir", "scan", "/work", "-f", "json", "--no-log"]
    assert setup["network"] == scan["network"] == "none"
    assert "node_restore" not in call
    assert call["out_dir"] == manifest.parent / "premap-runs/noir"
    [candidate], gaps = noir.evidence(manifest)
    assert (candidate["kind"], candidate["site"], candidate["symbol"], candidate["path"]) == (
        "rotta", "api.py:1", "api.py::submit", "/submit")
    assert any(gap.get("path") == "vendor/other.py" for gap in gaps)
    assert noir.recorded(manifest) == [candidate]
    links = flows.cached_links(manifest, [])
    assert [r["symbol"] for r in links["entries"] if r.get("reader") == "noir"] == ["api.py::submit"]
    assert [c["path"] for c in entries.cached_syntax(manifest) if c["reader"] == "noir"] == ["/submit"]
    # A different snapshot occupying the same location cannot inherit the old route.
    _, replacement = manifest_of(tmp_path / "different", {"api.py": "x = 1\n"})
    premap.path(replacement).write_bytes(premap.path(manifest).read_bytes())
    assert not noir.recorded(replacement)


def test_no_engine_carries_the_reason_and_never_runs_noir_on_the_host(tmp_path):
    from premap import noir
    _, manifest = manifest_of(tmp_path, {"app.py": "pass\n"})
    _, run = recorder(state="gap")
    with patch.object(container, "run_commands", run):
        premap.write(manifest, sources=(noir,), runner=container_runner.runner(manifest))
    candidates, gaps = noir.evidence(manifest)
    assert candidates == [] and gaps[0]["kind"] == "model_not_run"
    assert "no engine" in gaps[0]["detail"] and gaps[0]["remedy"] == "start one"


def test_only_a_repeat_of_the_same_disabled_container_skips_the_premap(tmp_path, monkeypatch):
    import pipeline
    from premap import noir
    _, manifest = manifest_of(tmp_path, {"api.py": "pass\n"})
    sources = (noir,)
    monkeypatch.setenv("DAODAN_CONTAINER", "off")
    premap.ensure(manifest, sources)  # reader-only scan, no container attempt yet
    with patch.object(container, "find_engine", wraps=container.find_engine) as probe:
        attempted = premap.ensure(manifest, sources, pipeline._runner(manifest))
        assert probe.call_count == 1
        assert premap.ensure(manifest, sources, pipeline._runner(manifest)) == attempted
        assert probe.call_count == 1
        with patch.object(container, "run_commands", side_effect=AssertionError("unexpected container request")):
            assert premap.ensure(manifest, sources, container_runner.runner(manifest)) == attempted
        premap.write(manifest, sources, pipeline._runner(manifest))  # explicit refresh
        assert probe.call_count == 2
    with patch.object(container, "find_engine", side_effect=container.Gap("engine offline", "start engine")) as probe:
        monkeypatch.delenv("DAODAN_CONTAINER")
        premap.ensure(manifest, sources, pipeline._runner(manifest))
        assert probe.call_count == 1
        monkeypatch.setenv("DAODAN_CONTAINER", "off")  # previous cause was different
        premap.ensure(manifest, sources, pipeline._runner(manifest))
        assert probe.call_count == 2
    premap.write(manifest, sources, pipeline._runner(manifest))
    calls, run = recorder(state="gap")
    with patch.object(container, "run_commands", run):
        # An explicitly supplied engine does not use the default engine setting.
        premap.ensure(manifest, sources, container_runner.runner(manifest, engine="daodan"))
    assert len(calls) == 1
    premap.write(manifest, sources, pipeline._runner(manifest))
    def custom(commands):
        return [{"root": "/work", "returncode": 0, "stdout": '{"endpoints":[]}', "stderr": ""}]
    assert premap.ensure(manifest, sources, custom)["sources"][0]["state"] == "ran"


def test_a_noir_server_action_is_no_entry_and_no_route_of_the_flows(tmp_path):
    from premap import noir
    import flows
    _, manifest = manifest_of(tmp_path, {"app/api/pay/route.ts": "export async function POST() {}\n",
                                         "app/checkout/actions.ts": '"use server";\n\nexport async function pay() {}\n'})
    def endpoint(url, kind, file, name, line):
        return {"protocol": "http", "url": url, "method": "POST", "kind": kind,
                "handler": {"path": f"/work/{file}", "line": line, "name": name}}
    report = {"endpoints": [endpoint("/api/pay", "", "app/api/pay/route.ts", "POST", 1),
                            endpoint("/pay", "server-action", "app/checkout/actions.ts", "pay", 3)]}
    premap.write(manifest, sources=(noir,), runner=lambda commands: [
        {"root": "/work", "returncode": 0, "stdout": json.dumps(report), "stderr": ""}])
    assert [(r["path"], r["shape"], r["kind"]) for r in noir.recorded(manifest)] == [
        ("/api/pay", "http", "rotta"), ("/pay", "server-action", "nessun ingresso")]
    links = flows.cached_links(manifest, [])
    assert [(e["path"], e["symbol"]) for e in links["entries"]] == [("/api/pay", "app/api/pay/route.ts::POST")]


def test_a_premap_made_with_the_old_noir_marker_is_stale(tmp_path):
    from premap import noir
    _, manifest = manifest_of(tmp_path, {"api.py": "pass\n"})
    record = premap.write(manifest, sources=(noir,), runner=lambda commands: [
        {"root": "/work", "returncode": 0, "stdout": '{"endpoints": []}', "stderr": ""}])
    assert premap.state(manifest, sources=(noir,))["state"] == "fresh"
    binding = record["binding"]  # the digest the pre-map had before the server action was no entry
    old = [binding["inventory_digest"], binding["root"], [f"{noir.NAME}@{noir.VERSION}"], premap.SCHEMA,
           "noir-entry-paths-v2"]
    record["inputs_digest"] = hashlib.sha256(json.dumps(old, sort_keys=True).encode("utf-8")).hexdigest()
    premap.path(manifest).write_text(json.dumps(record), encoding="utf-8")
    assert premap.state(manifest, sources=(noir,))["state"] == "stale"
