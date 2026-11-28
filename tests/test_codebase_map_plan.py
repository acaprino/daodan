"""The plan (spec 8.4, 8.10 proofs 3 and 4, 8.11 step 4): the choice of adapters in one function, executed by the steps.

    python -B -m pytest -q -p no:cacheprovider tests/test_codebase_map_plan.py
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path
from unittest import mock

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "daodan/core"
sys.path.insert(0, str(SCRIPTS))

import dynamic  # noqa: E402
import engine_pass  # noqa: E402
import pipeline  # noqa: E402
import resolve_edges  # noqa: E402
import snapshot  # noqa: E402
from dynamic import go as dynamic_go, python as dynamic_python  # noqa: E402
from languages import _treesitter  # noqa: E402
from pipeline import events  # noqa: E402
from snapshot_store import open_snapshot  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures"
GRAPHS = sorted(path for base in ("code-graph", "css-graph") for path in (FIXTURES / base).iterdir() if path.is_dir())
GO = "package billing\n\nfunc Pay(amount int) int {\n\treturn amount\n}\n"
PY = "def pay(amount):\n    return amount\n"


def _planning():
    from pipeline import plan
    return plan


def _project(root: Path, files: dict[str, str]) -> Path:
    root.mkdir(parents=True)
    for rel, text in files.items():
        (root / rel).write_text(text, encoding="utf-8", newline="")
    return root


def _without(*ids: str):
    """`pipeline.plan.plan` as it is, minus the nodes `ids`: a plan that leaves an adapter out."""
    real = _planning().plan

    def plan(rows):
        planned = real(rows)
        return {**planned, "nodes": [node for node in planned["nodes"] if node["id"] not in ids]}
    return plan


def _parse_without(*ids: str):
    """`pipeline.plan.parse_nodes`, which the reading takes its nodes from, minus the nodes `ids`."""
    real = _planning().parse_nodes
    return lambda rows: [node for node in real(rows) if node["id"] not in ids]


# ---------------------------------------------------------------------------------------------------------------
# The function


def test_the_plan_names_each_adapter_on_what_it_runs_on_and_what_it_needs():
    planning = _planning()
    rows = [("a.py", {"language": "python"}), ("b.py", {"language": "python"}), ("c.go", {"language": "go"}),
            ("README", {"language": None}), ("q.sql", {"language": "sql"})]
    planned = planning.plan(rows)
    nodes = {node["id"]: node for node in planned["nodes"]}
    assert {"read_code:python", "read_code:go", "read_code:file-level", "read_code:sql", "link_calls:scip-python", "link_calls:scip-go",
            "run_and_observe:dynamic-record-python", "run_and_observe:dynamic-record-go"} == set(nodes)
    assert nodes["read_code:python"]["on"] == {"languages": ["python"], "files": 2} and not nodes["read_code:python"]["needs"]
    assert nodes["read_code:file-level"]["on"] == {"languages": [], "files": 1}
    resolve = nodes["link_calls:scip-go"]
    assert (resolve["step"], resolve["adapter"], resolve["container"], resolve["needs"]) == (
        "link_calls", "scip-go", True, ["read_code:go"])
    assert resolve["on"] == {"languages": ["go"], "files": 1, "unit_kinds": ["go-module"]} and resolve["version"]
    observe = nodes["run_and_observe:dynamic-record-go"]
    assert (observe["needs"], observe["on"]["languages"], observe["container"]) == (["link_calls:scip-go"], ["go"], True)
    assert "version" not in nodes["read_code:go"]  # only an adapter that declares one has it
    assert [planning.node_of(row) for _path, row in rows] == [
        "read_code:python", "read_code:python", "read_code:go", "read_code:file-level", "read_code:sql"]
    assert {(gap["kind"], gap["language"], gap["files"]) for gap in planned["gaps"]} == {("no-analyzer", "sql", 1)}


def test_a_language_with_an_analyzer_and_no_observer_is_a_gap_and_a_resolver_is_the_first_to_list_it():
    planning = _planning()
    planned = planning.plan([("a.rs", {"language": "rust"}), ("b.c", {"language": "c"}), ("b.h", {"language": "c"})])
    gaps = {(gap["kind"], gap["language"]): gap for gap in planned["gaps"]}
    assert ("no-observer", "rust") not in gaps and ("no-observer", "c") not in gaps  # both have an observer
    planned = planning.plan([("a.css", {"language": "css"}), ("a.rb", {"language": "ruby"})])
    assert [(gap["kind"], gap["language"]) for gap in planned["gaps"] if gap["kind"] == "no-observer"] == [
        ("no-observer", "stylesheet")]
    assert "link_calls:stylesheet" in {node["id"] for node in planned["nodes"]}  # a graph of other languages' files
    nodes = [node for node in planned["nodes"] if node["step"] == "link_calls"]
    languages = [language for node in nodes for language in node["on"]["languages"]]
    assert len(languages) == len(set(languages))  # a language has one resolver


def test_a_node_whose_need_failed_is_blocked_per_language_and_says_which_need():
    planning = _planning()
    planned = planning.plan([("a.c", {"language": "c"}), ("a.cpp", {"language": "cpp"})])
    clang = next(node for node in planned["nodes"] if node["id"] == "link_calls:scip-clang")
    assert planning.blocked(clang, {}) == {}
    assert planning.blocked(clang, {"read_code:c": "no c file was parsed"}) == {"c": ("read_code:c", "no c file was parsed")}
    watcher = next(node for node in planned["nodes"] if node["step"] == "run_and_observe" and "cpp" in node["on"]["languages"])
    failed = {"link_calls:scip-clang": {"cpp": "no graph of cpp"}}
    assert planning.blocked(watcher, failed) == {"cpp": ("link_calls:scip-clang", "no graph of cpp")}


def test_a_row_may_stand_for_a_group_of_files_and_the_parse_part_needs_no_adapter_registry():
    planning = _planning()
    single = [(f"f{n}", {"language": "python", "status": "ast"}) for n in range(3)] + [
        ("x", {"language": "go", "status": "excluded"}), ("y", {"language": None, "status": "lexical"})]
    grouped = [("", {"language": "python", "status": "ast", "files": 3}),
               ("", {"language": "go", "status": "excluded", "files": 1}),
               ("", {"language": None, "status": "lexical", "files": 1})]
    assert planning.plan(grouped) == planning.plan(single)
    ids = {node["id"] for node in planning.plan(single)["nodes"]}
    assert "read_code:go" not in ids and not {"link_calls:scip-go", "run_and_observe:dynamic-record-go"} & ids  # all excluded
    assert planning.parse_nodes(single) == [node for node in planning.plan(single)["nodes"] if node["step"] == "read_code"]


def test_the_stylesheet_graph_is_built_from_its_own_parsers_so_no_parse_node_blocks_it():
    planning = _planning()
    nodes = {node["id"]: node for node in planning.plan([("a.css", {"language": "css"}),
                                                         ("b.vue", {"language": "vue"})])["nodes"]}
    sheet = nodes["link_calls:stylesheet"]
    assert sheet["needs"] == [] and nodes["link_calls:scip-typescript"]["needs"] == ["read_code:vue"]
    assert planning.blocked(sheet, {"read_code:stylesheet": "x", "read_code:css": "x", "read_code:vue": "x"}) == {}
    assert planning.blocked(nodes["link_calls:scip-typescript"], {"read_code:vue": "x"}) == {"vue": ("read_code:vue", "x")}


# ---------------------------------------------------------------------------------------------------------------
# Proof 3: the plan covers everything, and nothing runs outside it


@pytest.mark.parametrize("fixture", GRAPHS, ids=lambda path: f"{path.parent.name}/{path.name}")
def test_every_file_of_the_inventory_is_in_a_parse_node(tmp_path, fixture):
    planning = _planning()
    root, manifest = tmp_path / "project", tmp_path / "out" / "manifest.sqlite"
    shutil.copytree(fixture, root)
    snapshot.read_project(root, manifest)
    with open_snapshot(manifest) as store:
        rows = list(store.iter_inventory())
        entries = {path: entry for path, entry in store.iter_files(semantic=False)}
    planned = planning.plan(rows)
    parse = {node["id"]: node for node in planned["nodes"] if node["step"] == "read_code"}
    assert rows and sum(node["on"]["files"] for node in parse.values()) == len(rows)
    assert {path for path, _row in rows} == set(entries)
    assert all(planning.node_of(row) in parse for _path, row in rows)
    assert all(planning.node_of(entry) in parse for entry in entries.values())  # the snapshot's own entries


def test_no_parser_runs_outside_the_plan(tmp_path):
    root = _project(tmp_path / "project", {"billing.go": GO, "pay.py": PY})
    parsed = []
    real = snapshot.get_adapter
    with mock.patch.object(_planning(), "parse_nodes", _parse_without("read_code:go")), \
            mock.patch.object(snapshot, "get_adapter", side_effect=lambda name: parsed.append(name) or real(name)):
        snapshot.read_project(root, tmp_path / "out" / "manifest.sqlite")
    assert "python" in parsed and "go" not in parsed  # the spy sees the adapter that is in the plan


def test_a_file_in_no_parse_node_keeps_its_row_and_says_why(tmp_path):
    root = _project(tmp_path / "project", {"billing.go": GO, "pay.py": PY})
    manifest = tmp_path / "out" / "manifest.sqlite"
    with mock.patch.object(_planning(), "parse_nodes", _parse_without("read_code:go")):
        written = snapshot.read_project(root, manifest)
    with open_snapshot(manifest) as store:
        assert [path for path, _row in store.iter_inventory()] == ["billing.go", "pay.py"]
        entry = store.get_file("billing.go")
        assert (store.file_count, written["file_count"]) == (2, 2)
    assert entry["status"] == "file-level" and entry["symbols"] == {}
    assert entry["parser_notes"] == ["no parse node in the plan"]
    assert entry["language"] == "go"  # the inventory's fact: not read, still a Go file


def test_no_resolver_runs_outside_the_plan(tmp_path):
    root = _project(tmp_path / "project", {"billing.go": GO, "pay.py": PY})
    manifest, launched = tmp_path / "out" / "manifest.sqlite", []
    snapshot.read_project(root, manifest)

    def launch(spec, wanted, path):
        launched.append(spec.name)
        return None, None, None, {"available": True, "engine": spec.name,
                                  "languages": {language: {"state": "fresh"} for language in wanted}}

    with mock.patch.object(_planning(), "plan", _without("link_calls:scip-go")), \
            mock.patch.object(engine_pass, "_launch", side_effect=launch), \
            mock.patch.object(engine_pass, "free_memory", return_value=64 * 2**30):
        report = engine_pass.run_pass(manifest, tmp_path / "out" / "report.json")
    assert launched == ["scip-python"] and "go" not in report["languages"]


@pytest.mark.parametrize("dropped, seen", [("run_and_observe:dynamic-record-go", "python"),
                                           ("run_and_observe:dynamic-record-python", "go")])
def test_no_observer_runs_outside_the_plan(tmp_path, dropped, seen):
    root = _project(tmp_path / "project", {"billing.go": GO, "pay.py": PY})
    manifest, asked = tmp_path / "out" / "manifest.sqlite", []
    snapshot.read_project(root, manifest)
    graphs = {"manifest_digest": "d", "parser_fingerprint": "p", "resolver_version": 1,
              "languages": {language: {"state": "fresh", "engine": "x", "coverage": {}}
                            for language in ("go", "python")}}
    with mock.patch.object(_planning(), "plan", _without(dropped)), \
            mock.patch.object(resolve_edges, "read_edge_store", return_value=([], graphs, None)), \
            mock.patch.object(dynamic_go, "plan", side_effect=lambda *a: asked.append("go") or {"runs": [], "gaps": []}), \
            mock.patch.object(dynamic_python, "plan",
                              side_effect=lambda *a: asked.append("python") or {"runs": [], "gaps": []}):
        dynamic.run(manifest, events.Bus())
    assert asked == [seen]


# ---------------------------------------------------------------------------------------------------------------
# Proof 4: a failed need stops only what needs it


@pytest.fixture
def no_go_grammar():
    _treesitter.get_parser.cache_clear()
    with mock.patch.object(_treesitter, "place_grammars", lambda *args: "download failed: no network"), \
            mock.patch.object(_treesitter, "_GRAMMAR_MODULES", {}):
        _treesitter.get_parser.cache_clear()
        yield
    _treesitter.get_parser.cache_clear()


def _chain(tmp_path):
    """parse, resolve and observe of a Go and a Python file, end to end: the stage stub reports its languages
    fresh, and the store's graphs are the languages it reported, so a stopped resolver leaves its observer no graph."""
    root = _project(tmp_path / "project", {"billing.go": GO, "pay.py": PY})
    manifest = tmp_path / "out" / "manifest.sqlite"
    snapshot.read_project(root, manifest)
    launched, asked, seen, fresh = [], [], [], {}

    def launch(spec, wanted, path):
        launched.append(spec.name)
        fresh.update({language: {"state": "fresh", "engine": spec.name, "coverage": {}} for language in wanted})
        return None, None, None, {"available": True, "engine": spec.name,
                                  "languages": {language: {"state": "fresh"} for language in wanted}}

    def graphs(*args):
        return [], {"manifest_digest": "d", "parser_fingerprint": "p", "resolver_version": 1,
                    "languages": dict(fresh)}, None

    with mock.patch.object(engine_pass, "_launch", side_effect=launch), \
            mock.patch.object(engine_pass, "free_memory", return_value=64 * 2**30), \
            mock.patch.object(resolve_edges, "read_edge_store", side_effect=graphs), \
            mock.patch.object(dynamic_go, "plan", side_effect=lambda *a: asked.append("go") or {"runs": [], "gaps": []}), \
            mock.patch.object(dynamic_python, "plan",
                              side_effect=lambda *a: asked.append("python") or {"runs": [], "gaps": []}):
        results = pipeline.run(manifest, listeners=[seen.append], start="link_calls", stop="run_and_observe")
    return results, launched, asked, seen


def test_a_parser_that_is_missing_stops_the_resolver_and_the_observer_of_its_language_only(tmp_path, no_go_grammar):
    results, launched, asked, seen = _chain(tmp_path)
    assert launched == ["scip-python"]  # scip-go does not start, with its parser missing
    languages = results["link_calls"]["languages"]
    assert languages["go"]["state"] == "unavailable" and languages["go"]["need"] == "read_code:go"
    assert "none of the 1 go files was parsed" in languages["go"]["reason"] and languages["python"]["state"] == "fresh"
    unavailable = [event for event in seen if event["kind"] == "analyzer.unavailable"]
    assert [(event["analyzer"], event["data"]["need"]) for event in unavailable] == [("scip-go", "read_code:go")]
    assert asked == ["python"]  # the go observer does not plan its runs
    observed = results["run_and_observe"]["languages"]
    assert (observed["go"]["state"], observed["go"]["need"]) == ("no-static-graph", "link_calls:scip-go")
    assert observed["python"]["state"] == "not-run"


def test_with_its_parser_the_same_chain_reaches_the_observer_of_each_language(tmp_path):
    results, launched, asked, _seen = _chain(tmp_path)
    assert sorted(launched) == ["scip-go", "scip-python"] and sorted(asked) == ["go", "python"]
    assert {language: outcome["state"] for language, outcome in results["run_and_observe"]["languages"].items()} == {
        "go": "not-run", "python": "not-run"}


def test_the_plan_of_the_stored_rows_is_the_plan_the_pass_runs(tmp_path):
    """One row source (`plan.stored`): the plan has the pass's gaps, the astro code no analyzer serves too."""
    root = _project(tmp_path / "project", {
        "a.sql": "select 1;\n", "pay.py": PY, "page.html": '<p class="x">x</p>\n',
        "Page.astro": '---\nimport { f } from "./f";\nf();\n---\n<p class="x">x</p>\n<style>\n.x { color: red }\n</style>\n'})
    manifest = tmp_path / "out" / "manifest.sqlite"
    snapshot.read_project(root, manifest)
    with open_snapshot(manifest) as store:
        said = _planning().plan(_planning().stored(store))
        planned = engine_pass.snapshot_plan(store.connection)
        assert engine_pass.no_analyzer(store.connection) == {gap["language"]: gap["files"] for gap in planned["gaps"]
                                                            if gap["kind"] == "no-analyzer"} == {"astro": 1, "sql": 1}
    assert said == planned


# ---------------------------------------------------------------------------------------------------------------
# The one plan (`plan.current`): the steps, the policy, the actions and the gaps, from their owners


@pytest.fixture
def shared(tmp_path, monkeypatch):
    import egress
    monkeypatch.setenv("DAODAN_SHARED_DIR", str(tmp_path / "shared"))
    egress.PENDING.clear()
    yield tmp_path / "shared"
    egress.PENDING.clear()


def _states(planned: dict, of: str = "steps") -> dict:
    return {entry["id"]: entry["state"] for entry in planned[of]}


def test_the_plan_of_no_snapshot_has_the_eight_steps_to_do_the_policy_and_the_download_gap(tmp_path, shared):
    import container
    planning = _planning()
    planned = planning.current(tmp_path / "out" / "manifest.sqlite")
    assert [step["id"] for step in planned["steps"]] == list(pipeline.IDS)
    assert set(_states(planned).values()) == {"pending"}
    assert {step["id"]: (step["executes"], step["stops"]) for step in planned["steps"]} == {
        "list_files": ("no", True), "read_code": ("no", True), "recognize_stack": ("no", False),
        "find_modules": ("container", True), "find_entry_points": ("container", False), "link_calls": ("container", True),
        "run_and_observe": ("container", False), "assemble_graph": ("no", True)}
    assert [(action["id"], action["kind"], action["state"]) for action in planned["actions"]] == [
        ("recognize_stack", "recognize", "pending"), ("find_modules", "model", "pending"),
        ("find_entry_points", "entries", "pending"), ("assemble_graph", "assemble", "pending")]
    assert planned["gaps"] == [planning.DOWNLOADS]
    network = planned["policy"]["network"]
    assert network == {"canonical": list(container.REGISTRIES), "approved": [], "blocked": [], "other": "ask",
                       "answered_in": "app"}
    assert planned["policy"]["container"]["engine"] == "off" and planned["policy"]["container"]["remedy"]


def test_the_plan_says_the_steps_and_actions_of_the_last_analysis(tmp_path, shared):
    """The steps to `find_entry_points` are done, the store is read, the nodes wait for the steps after; an approved host
    is in the policy, and an analysis started again leaves the steps after it to do."""
    import egress
    planning = _planning()
    root = _project(tmp_path / "project", {"billing.go": GO, "pay.py": PY})
    manifest = tmp_path / "out" / "manifest.sqlite"
    snapshot.read_project(root, manifest)
    pipeline.run(manifest, stop="find_entry_points", fast_scan=True)
    state, _ = egress.answer(egress.load(), egress.new_session(), "git.example.com", egress.project_of(manifest), "always")
    egress.save(state)
    planned = planning.current(manifest)
    assert _states(planned) == {"list_files": "done", "read_code": "done", "recognize_stack": "done",
                                "find_modules": "done", "find_entry_points": "done", "link_calls": "pending",
                                "run_and_observe": "pending", "assemble_graph": "pending"}
    actions = {action["id"]: action for action in planned["actions"]}
    assert {action["kind"] for action in planned["actions"]} <= set(planning.ACTIONS)
    assert all(set(action) >= {"id", "step", "kind", "target", "project_code", "container", "state"}
               for action in planned["actions"])
    assert (actions["read_code:go"]["state"], actions["read_code:go"]["container"]) == ("done", False)
    assert actions["link_calls:scip-go"]["state"] == "pending" and actions["link_calls:scip-go"]["target"]["languages"] == ["go"]
    assert all(not action["project_code"] or action["container"] for action in planned["actions"])
    assert "find_modules" not in actions and "recognize_stack" not in actions  # their fresh records stand for the steps
    assert actions["recognize_stack:stack-analyser"]["state"] in ("done", "failed")
    assert planned["policy"]["network"]["approved"] == ["git.example.com"]
    with open_snapshot(manifest) as store:
        assert [gap for gap in planned["gaps"] if gap is not planning.DOWNLOADS] == planning.plan(planning.stored(store))["gaps"]
    bus = events.Bus(manifest.with_name(events.JOURNAL))
    bus.emit("step.started", "recognize_stack", step="recognize_stack")
    assert _states(planning.current(manifest))["find_modules"] == "pending"  # of the analysis before


def test_a_step_carries_its_times_from_the_journal_a_running_one_only_its_start(tmp_path, shared):
    """A step done has `started_at` and `ended_at` from its events, one running only `started_at`, one to do neither;
    `list_files` and `read_code` have no events, so no times."""
    planning = _planning()
    root = _project(tmp_path / "project", {"billing.go": GO, "pay.py": PY})
    manifest = tmp_path / "out" / "manifest.sqlite"
    snapshot.read_project(root, manifest)
    pipeline.run(manifest, stop="find_entry_points", fast_scan=True)
    recorded = events.read(manifest.with_name(events.JOURNAL))[0]
    steps = {step["id"]: step for step in planning.current(manifest)["steps"]}
    done = steps["find_modules"]
    assert done["state"] in ("done", "skipped") and done["started_at"] <= done["ended_at"]
    assert done["started_at"] == next(event["at"] for event in reversed(recorded) if event.get("step") == "find_modules"
                                      and event["kind"] in ("step.started", "step.skipped"))
    assert not {"started_at", "ended_at"} & (set(steps["list_files"]) | set(steps["link_calls"]))
    bus = events.Bus(manifest.with_name(events.JOURNAL))
    bus.emit("step.started", "recognize_stack", step="recognize_stack")
    steps = {step["id"]: step for step in planning.current(manifest)["steps"]}
    assert steps["recognize_stack"]["state"] == "running" and steps["recognize_stack"]["started_at"]
    assert "ended_at" not in steps["recognize_stack"]
    assert not {"started_at", "ended_at"} & set(steps["find_modules"])  # of the analysis before


def test_an_action_is_not_possible_with_the_cause_and_remedy_of_its_need_and_a_fresh_one_is_skipped(tmp_path, shared,
                                                                                                    no_go_grammar):
    planning = _planning()
    _results, _launched, _asked, _seen = _chain(tmp_path)
    planned = planning.current(tmp_path / "out" / "manifest.sqlite")
    actions = {action["id"]: action for action in planned["actions"]}
    assert actions["read_code:go"]["state"] == "failed" and "none of the 1 go files" in actions["read_code:go"]["cause"]
    go = actions["link_calls:scip-go"]
    assert go["state"] == "not_possible" and "none of the 1 go files" in go["cause"] and go["remedy"]
    assert actions["link_calls:scip-python"]["state"] == "done"
    assert _states(planned)["link_calls"] == "done" and _states(planned)["recognize_stack"] == "pending"
    bus = events.Bus((tmp_path / "out" / "manifest.sqlite").with_name(events.JOURNAL))
    bus.emit("step.started", "link_calls", step="link_calls")
    bus.emit("analyzer.finished", "scip-python: already fresh", step="link_calls", analyzer="scip-python", fresh=True)
    planned = planning.current(tmp_path / "out" / "manifest.sqlite")
    assert _states(planned, "actions")["link_calls:scip-python"] == "skipped"
    assert _states(planned)["link_calls"] == "running"
    assert _states(planned, "actions")["link_calls:scip-go"] == "not_possible"  # its parser is still missing


def test_a_request_of_gradle_waits_for_its_model_action_alone_and_a_no_makes_it_not_possible(tmp_path, shared):
    """The sources of the pre-map are actions of `find_modules`, with the tools and the network their commands name: a
    request `egress.pending` holds for gradle (the tool `egress.asking` named, as `container_runner` asks) puts its action
    alone in `awaiting_approval`, with the hosts only; the user's "no" makes it `not_possible` with `host_denied`."""
    import container
    import egress
    import premap
    from premap import go as premap_go, gradle as premap_gradle
    planning = _planning()
    root = _project(tmp_path / "project", {"settings.gradle": "rootProject.name = 'shop'\n", "build.gradle": "\n",
                                           "go.mod": "module example.com/billing\n\ngo 1.22\n", "billing.go": GO})
    manifest = tmp_path / "out" / "manifest.sqlite"
    snapshot.read_project(root, manifest)
    project = egress.project_of(manifest)

    def runner(commands):  # as `container_runner` asks: gradle's host nobody decided stops it, the others find no engine
        with egress.asking(commands[0]["tool"]):
            if commands[0]["tool"] == "gradle":
                _waiting, said = egress.preflight(project, ("repo.example.com",))
                raise container.Gap(said[0]["detail"], "answer in the app, then analyze again", said)
        raise container.Gap("no container engine answers", "start Docker or Podman")

    looked = lambda rows, *args, **kwargs: [{**row, "address": None, "network": False} for row in rows]  # noqa: E731
    with mock.patch.object(egress, "resolve", side_effect=looked):
        premap.write(manifest, runner=runner)  # every source: the record is fresh for the plan
    gradle, go = premap.label(premap_gradle), premap.label(premap_go)
    actions = {action["id"]: action for action in planning.current(manifest)["actions"]}
    waiting = actions[f"find_modules:{gradle}"]
    assert (waiting["state"], waiting["hosts"], waiting["tools"], waiting["network"]) == (
        "awaiting_approval", ["repo.example.com"], ["gradle"], ["registries"])
    assert set(waiting) == {"id", "step", "kind", "target", "project_code", "container", "state", "hosts", "tools", "network"}
    assert waiting["kind"] == "model" and waiting["project_code"] and waiting["container"]
    assert [action["id"] for action in actions.values() if action["state"] == "awaiting_approval"] == [f"find_modules:{gradle}"]
    assert (actions[f"find_modules:{go}"]["state"], actions[f"find_modules:{go}"]["gap"]) == ("not_possible", "model_not_run")
    assert "find_modules" not in actions  # the record's sources stand for the step
    egress.reply(project, ["repo.example.com"], "no")
    refused = {action["id"]: action for action in planning.current(manifest)["actions"]}[f"find_modules:{gradle}"]
    assert (refused["state"], refused["gap"], refused["hosts"]) == ("not_possible", "host_denied", ["repo.example.com"])
    assert refused["cause"] and refused["remedy"]


def test_a_request_of_the_exploration_waits_for_its_explore_action_alone(tmp_path, shared):
    """The exploration's run asks under its own name (`dynamic.APP`, as an observer's under its own, `egress.asking`): a
    host the proxy refused it and nobody answered puts the `explore` action of the app in `awaiting_approval`, with the
    hosts, and no other action; the answer takes it out."""
    import egress
    import premap
    from dynamic import app
    planning = _planning()
    root = _project(tmp_path / "project", {"package.json": '{"scripts": {"start": "node server.js"}}\n',
                                           "server.js": "require('http').createServer().listen(3000);\n"})
    manifest = tmp_path / "out" / "manifest.sqlite"
    snapshot.read_project(root, manifest)
    premap.write(manifest)  # no runner: the readers' facts, the `starts` among them; no command runs
    project = egress.project_of(manifest)

    def observe(folder, planned, out_dir, engine=None):  # the run's end, as `container.run_in_container` collects it
        asked, _ = egress.collect(egress.name(folder), [{"host": "storage.googleapis.com", "port": "443"}])
        return {"state": "ran", "apps": [{"state": "ready"}], "gaps": egress.approval_gap(asked, "ran")}
    looked = lambda rows, *args, **kwargs: [{**row, "address": None, "network": False} for row in rows]  # noqa: E731
    with mock.patch.object(app, "observe", observe), mock.patch.object(egress, "resolve", side_effect=looked), \
            mock.patch.object(resolve_edges, "read_edge_store", return_value=([], {"languages": {}}, None)):
        dynamic.run(manifest, events.Bus())  # no static graph: no observer runs, the app is explored
    assert [group["tool"] for group in egress.groups([project])] == [dynamic.APP]
    actions = {action["id"]: action for action in planning.current(manifest)["actions"]}
    waiting = actions[f"run_and_observe:{dynamic.APP}:."]
    assert (waiting["state"], waiting["hosts"], waiting["target"]["root"]) == (
        "awaiting_approval", ["storage.googleapis.com"], ".")
    assert [key for key, action in actions.items() if action["state"] == "awaiting_approval"] == [waiting["id"]]
    egress.reply(project, ["storage.googleapis.com"], "once")
    answered = {action["id"]: action for action in planning.current(manifest)["actions"]}[waiting["id"]]
    assert answered["state"] != "awaiting_approval" and "hosts" not in answered


def test_the_command_line_prints_the_plan_the_app_and_mcp_show(tmp_path, shared, capsys):
    """`daodan snapshot plan MANIFEST` prints `plan.current` as JSON: one plan for app, MCP and command line."""
    import json
    planning = _planning()
    root = _project(tmp_path / "project", {"billing.go": GO, "pay.py": PY})
    manifest = tmp_path / "out" / "manifest.sqlite"
    snapshot.read_project(root, manifest)
    pipeline.run(manifest, stop="find_entry_points", fast_scan=True)
    capsys.readouterr()
    assert snapshot.main(["plan", str(manifest)]) == 0
    assert json.loads(capsys.readouterr().out) == planning.current(manifest)


def test_the_plan_of_the_viewer_s_tests_has_the_server_s_ids_states_kinds_and_keys(tmp_path, shared):
    """`viewer/test/plan.json`, the plan the app's tests read, stays in the server's form: the eight ids in order, the
    states, kinds and keys of `plan.STATES`, `ACTION_STATES`, `ACTIONS` and `_action`, and the policy's keys."""
    import json
    planning = _planning()
    fixture = json.loads((Path(__file__).resolve().parents[1] / "viewer/test/plan.json").read_text(encoding="utf-8"))
    real = planning.current(tmp_path / "out" / "manifest.sqlite")
    assert set(fixture) == set(real)
    assert [step["id"] for step in fixture["steps"]] == list(pipeline.IDS)
    assert {step["state"] for step in fixture["steps"]} <= set(planning.STATES)
    assert all({"id", "state", "executes", "stops"} <= set(step) <= {"id", "state", "executes", "stops", "cause", "remedy",
                                                                     "started_at", "ended_at"} for step in fixture["steps"])
    base = set(planning._action("x", "x", "read", {}, False, False, {"state": "pending"}))
    assert all(base <= set(action) <= base | {"tools", "network", "hosts", "gap", "cause", "remedy", "by", "grade"}
               for action in fixture["actions"])
    assert {action["state"] for action in fixture["actions"]} <= set(planning.ACTION_STATES)
    assert {action["kind"] for action in fixture["actions"]} <= set(planning.ACTIONS)
    assert all(action["step"] == planning.KINDS[action["kind"]][0] for action in fixture["actions"])
    assert set(fixture["policy"]["network"]) == set(real["policy"]["network"])
    assert {"kind", "detail"} <= set(fixture["gaps"][-1]) and fixture["gaps"][-1] == planning.DOWNLOADS


def test_an_app_the_person_or_the_assistant_starts_is_an_explore_action_with_who_said_it_and_its_grade(tmp_path, shared,
                                                                                                    monkeypatch):
    """The apps of the fresh pre-map and those a command of the user or the assistant starts (`commands`) are the
    `explore` actions of `run_and_observe`, their target the root with the words, the surface and the place of the start
    that runs there; one whose start is a stated command carries its `by` and `grade`. The assistant's proposal does not
    run (`app.chosen`): its folder shows the project's start, with no `by`."""
    import json
    import commands
    import entry_points
    import premap
    import stack_recognition
    planning = _planning()
    record = tmp_path / "premap.json"
    record.write_text(json.dumps({"sources": [], "starts": [
        {"root": root, "mode": "start", "runner": "npm", "argv": ["npm", "run", "start"], "surface": "web",
         "declared_in": f"{root}/package.json#scripts.start", "port": None, "needs_build": False}
        for root in ("api", "web")]}), encoding="utf-8")
    monkeypatch.setattr(premap, "state", lambda manifest: {"state": "fresh"})
    monkeypatch.setattr(premap, "path", lambda manifest: record)
    monkeypatch.setattr(entry_points, "state", lambda manifest: {"state": "stale"})
    monkeypatch.setattr(stack_recognition, "state", lambda manifest: "stale")
    project = tmp_path / "project"
    (project / "api").mkdir(parents=True)
    (project / "web").mkdir()
    key = str(project.resolve())
    commands.set(key, {"kind": "starts", "root": "api", "argv": ["npm", "run", "serve"]}, "assistant")
    commands.set(key, {"kind": "starts", "root": "web", "argv": ["npm", "run", "dev"]}, "user")
    found = planning._found(tmp_path / "manifest.sqlite", {}, {}, [], lambda tools, hosts=(): None, key)
    assert [(action["id"], action["state"], action.get("by"), action.get("grade")) for action in found["explore"]] == [
        ("run_and_observe:app:api", "pending", None, None),
        ("run_and_observe:app:web", "pending", "user", "confermato")]
    assert [action["target"] for action in found["explore"]] == [
        {"root": "api", "argv": ["npm", "run", "start"], "surface": "web",
         "declared_in": "api/package.json#scripts.start"},
        {"root": "web", "argv": ["npm", "run", "dev"], "surface": "web", "declared_in": commands.FILE}]
    alone = planning._found(tmp_path / "manifest.sqlite", {}, {}, [], lambda tools, hosts=(): None, None)
    assert [(action["target"], "by" in action) for action in alone["explore"]] == [
        ({"root": root, "argv": ["npm", "run", "start"], "surface": "web",
          "declared_in": f"{root}/package.json#scripts.start"}, False) for root in ("api", "web")]


def test_a_folder_on_a_surface_not_run_yet_is_an_explore_action_not_possible_with_its_gap(tmp_path, shared,
                                                                                         monkeypatch):
    """A module whose technology has a surface the exploration does not run yet (its registry entry's), with no start of
    its folder, and a start the user states on such a surface: their `explore` actions are `not_possible` with
    `ui_execution_deferred:<surface>`, whatever the app's events say; the other app keeps its state."""
    import json
    import commands
    import entry_points
    import premap
    import service_registry
    import stack_recognition
    import technologies
    from dynamic import app
    planning = _planning()
    ident, surface = next((entry["id"], entry["surface"]) for entry in service_registry.load()["entries"]
                          if entry.get("surface") and entry["surface"] not in app.ACTIVE)
    manifest = tmp_path / "manifest.sqlite"
    record = tmp_path / "premap.json"
    record.write_text(json.dumps({"sources": [], "starts": [
        {"root": "web", "mode": "start", "runner": "npm", "argv": ["npm", "run", "start"], "surface": "web",
         "declared_in": "web/package.json#scripts.start", "port": None, "needs_build": False}]}), encoding="utf-8")
    technologies.path(manifest).write_text(json.dumps({"schema": technologies.SCHEMA, "technologies": [], "units": [
        {"id": "mobile", "name": "mobile", "paths": ["mobile"], "technologies": [ident],
         "technology_evidence": {ident: {"path": "mobile/manifest.file"}}}]}), encoding="utf-8")
    monkeypatch.setattr(premap, "state", lambda manifest: {"state": "fresh"})
    monkeypatch.setattr(premap, "path", lambda manifest: record)
    monkeypatch.setattr(entry_points, "state", lambda manifest: {"state": "stale"})
    monkeypatch.setattr(stack_recognition, "state", lambda manifest: "stale")
    project = tmp_path / "project"
    (project / "api").mkdir(parents=True)
    key = str(project.resolve())
    commands.set(key, {"kind": "starts", "root": "api", "argv": ["npm", "run", "phone"], "surface": surface}, "user")
    journal = [{"kind": "step.started", "step": "run_and_observe"},
               {"kind": "analyzer.finished", "step": "run_and_observe", "analyzer": "app"}]
    found = planning._found(manifest, {}, {"run_and_observe": 0}, journal, lambda tools, hosts=(): None, key)
    actions = {action["target"]["root"]: action for action in found["explore"]}
    assert {root: (action["state"], action.get("gap")) for root, action in actions.items()} == {
        "api": ("not_possible", f"ui_execution_deferred:{surface}"),
        "mobile": ("not_possible", f"ui_execution_deferred:{surface}"), "web": ("done", None)}
    assert ident in actions["mobile"]["cause"] and "mobile/manifest.file" in actions["mobile"]["cause"]
    assert actions["mobile"]["remedy"] and (actions["api"]["by"], actions["api"]["grade"]) == ("user", "confermato")
    assert actions["mobile"]["target"] == {"root": "mobile"}  # no start declared there: nothing more to say
    assert (actions["api"]["target"]["surface"], actions["web"]["target"]["surface"]) == (surface, "web")
