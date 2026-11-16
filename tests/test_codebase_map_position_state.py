"""The position stage of Vue and Svelte: the Node its language server runs on, and the state of a language none
of whose files it reads whole.

Programs and URLs are the fakes of `test_codebase_map_indexers`; the stage is the one of
`test_codebase_map_indexers_reasons`, whose engine never starts a server.
"""
from __future__ import annotations

import sys
import types
from pathlib import Path

import test_codebase_map_indexers as base
import test_codebase_map_indexers_reasons as reasons
import language_servers  # noqa: E402
import resolve_edges as rx  # noqa: E402
from indexers import runtime, vue_svelte  # noqa: E402
from snapshot_store import open_snapshot  # noqa: E402

sandbox = base.sandbox  # the fixture, for this module's tests
PACKAGES = ["typescript@5.5.4", "typescript-language-server@4.3.3"]
SCRIPT = "<script>\nexport const n = 1\n</script>\n"


class Pinned(vue_svelte.TypeScriptEngine):
    """The engine with the pins multilspy gives it: the tests' interpreter has no multilspy."""

    def pinned(self) -> dict:
        return {"version": "4.3.3", "packages": PACKAGES}


def _host(sandbox) -> None:
    """A host with neither node nor npm on its PATH, where multilspy is there (the stage's environment has it)."""
    sandbox["monkeypatch"].setenv("PATH", str(sandbox["root"]))
    for name in ("multilspy", "multilspy.lsp_protocol_handler", "multilspy.lsp_protocol_handler.server"):
        sandbox["monkeypatch"].setitem(sys.modules, name, types.ModuleType(name))


def _node(sandbox) -> Path:
    """Daodan's Node in the shared directory of such a host (`_host`): its directory."""
    base._tools(sandbox["root"], "python")
    _host(sandbox)
    return runtime.node_directory(rx.shared_engine_dir("node") / runtime.NODE_VERSION)


def test_the_language_server_is_installed_and_started_on_daodans_node_never_the_hosts(sandbox):
    directory = _node(sandbox)
    engine = Pinned(base._project(sandbox, "ts"))
    home = engine.home()
    assert engine.prepare(home) == (True, ""), engine.install
    node = str(directory / rx.executable_name("node"))
    [(command, _cwd)] = sandbox["fake"].calls
    assert command[0] == node and Path(command[1]).name == "npm-cli.js"
    assert command[2:4] == ["install", "--prefix"] and "--ignore-scripts" in command and command[-2:] == PACKAGES
    [env] = sandbox["fake"].envs
    assert Path(env["npm_config_cache"]).is_relative_to(sandbox["cache"])
    assert (home / ".installed").is_file()
    launched, _environment = engine.command(home)
    assert launched[0] == node and launched[-1] == "--stdio"


def test_the_projects_packages_are_installed_with_daodans_npm(sandbox):
    directory = _node(sandbox)
    engine = Pinned(base._project(sandbox, "ts"))
    sandbox["monkeypatch"].setattr(language_servers.LspEngine, "probe", lambda self: (True, ""))  # no server starts
    assert engine.probe() == (True, "")
    [(command, _cwd)] = sandbox["fake"].calls  # `engine_tools.npm_modules`: the manifests' install
    assert Path(command[0]).parent == directory and Path(command[0]).stem == "npm" and command[1] == "install"


def test_without_daodans_node_the_engine_says_the_real_cause_and_what_to_do(sandbox):
    _host(sandbox)
    engine = Pinned(base._project(sandbox, "ts"))
    for ready, reason in (engine.probe(), engine.prepare(engine.home())):
        assert not ready and f"Node {runtime.NODE_VERSION} could not be downloaded" in reason
        assert "no network in this test" in reason and "node and npm are needed" not in reason
    assert engine.install.startswith("check the network") and "nodejs.org" in engine.install
    assert sandbox["fake"].calls == []


def test_without_multilspy_nothing_is_downloaded_for_a_server_that_cannot_start(sandbox):
    sandbox["monkeypatch"].setitem(sys.modules, "multilspy", None)
    ready, reason = Pinned(base._project(sandbox, "ts")).probe()
    assert not ready and "multilspy is not installed" in reason
    assert sandbox["web"].asked == [] and sandbox["fake"].calls == []


def test_a_language_server_npm_cannot_install_says_npms_error(sandbox):
    import subprocess
    _node(sandbox)
    engine = Pinned(base._project(sandbox, "ts"))

    def failing(command, *args, **kwargs):
        raise subprocess.CalledProcessError(1, command, "", "npm error code E404\nnpm error 404 no such package\n")

    sandbox["monkeypatch"].setattr(subprocess, "run", failing)
    ready, reason = engine.prepare(engine.home())
    assert not ready and "typescript-language-server 4.3.3 could not be installed (exit code 1)" in reason
    assert "npm error 404 no such package" in reason and "npm registry" in engine.install
    assert not engine.home().exists()


ASKED = "<script>\nexport function go(x) { return x.run() }\n</script>\n"  # a call the engine is given


def test_components_read_in_part_keep_their_language_fresh_with_a_lower_bound(tmp_path):
    """Every component has a template the engine does not read and a script block whose calls it is given: the
    language is fresh, its coverage a lower bound, each file missing with the template's reason; no gap."""
    report = reasons._stage(tmp_path, {
        "Only.vue": ASKED + "<template>\n  <p>{{ n }}</p>\n</template>\n",
        "Card.svelte": ASKED + "<button on:click={h}>x</button>\n", "List.svelte": SCRIPT + "<ul></ul>\n"})
    assert report["available"], report.get("reason")
    assert "gaps" not in report
    for language, files in (("vue", 1), ("svelte", 2)):
        entry = report["languages"][language]
        assert entry["state"] == "fresh" and "reason" not in entry
        assert entry["coverage"]["state"] == "lower-bound"
        assert (entry["coverage"]["files"]["snapshot"], entry["coverage"]["files"]["indexed"]) == (files, 0)
        assert {item["reason"] for item in entry["coverage"]["files"]["missing"]} == {reasons.TEMPLATE}


def test_a_language_of_whose_files_the_engine_reads_nothing_is_failed_with_the_cause(tmp_path):
    """As the indexer stage does (`engine_pass.index_stage`): nothing read proves nothing of the language. A
    component without a script block gives the engine nothing; one with a script block is read in part."""
    report = reasons._stage(tmp_path, {
        "Bare.vue": SCRIPT, "Only.vue": SCRIPT + "<template>\n  <p>{{ n }}</p>\n</template>\n",
        "Card.svelte": "<button>x</button>\n", "List.svelte": "<ul></ul>\n<style>\nul {}\n</style>\n"})
    assert report["available"], report.get("reason")
    vue, svelte = report["languages"]["vue"], report["languages"]["svelte"]
    assert (vue["state"], vue["coverage"]["files"]["indexed"]) == ("fresh", 1) and "reason" not in vue
    assert (svelte["state"], svelte["coverage"]["files"]["indexed"]) == ("failed", 0)
    assert svelte["reason"] == f"nothing of the 2 svelte files is read: {vue_svelte.NO_SCRIPT} (2)"
    assert {item["reason"] for item in svelte["coverage"]["files"]["missing"]} == {vue_svelte.NO_SCRIPT}
    assert report["gaps"] == [{"kind": "language_not_indexed", "language": "svelte", "detail": svelte["reason"]}]
    with open_snapshot(tmp_path / "manifest.sqlite") as store:
        _edges, binding, refused = rx.read_edge_store(tmp_path / "engine-edges.sqlite", store)
    assert refused is None
    assert {language: entry["state"] for language, entry in binding["languages"].items()} == {
        "vue": "fresh", "svelte": "failed"}


SVELTEKIT = Path(__file__).resolve().parents[1] / "benchmarks/project-model/fixtures/js-sveltekit/src/routes"


def test_components_whose_templates_are_unread_and_whose_calls_none_is_asked_are_failed(tmp_path):
    """js-sveltekit: each component's template is unread and the only calls of their script blocks are runes no
    engine is asked (`$props()`): nothing of any file is read, so the language is failed with the cause."""
    report = reasons._stage(tmp_path, {f"src/routes/{name}": (SVELTEKIT / name).read_text(encoding="utf-8")
                                       for name in ("+layout.svelte", "+page.svelte")})
    assert report["available"], report.get("reason")
    svelte = report["languages"]["svelte"]
    files, excluded = svelte["coverage"]["files"], svelte["excluded_classes"]
    assert (files["snapshot"], files["indexed"], svelte["population"], sum(excluded.values())) == (2, 0, 0, 2)
    assert svelte["state"] == "failed"
    assert svelte["reason"] == (f"nothing of the 2 svelte files is read: {reasons.TEMPLATE} (2); none of their 2 "
                                "calls is asked: " + ", ".join(f"{name} ({count})" for name, count in excluded.items()))
    assert report["gaps"] == [{"kind": "language_not_indexed", "language": "svelte", "detail": svelte["reason"]}]


class Served(reasons.Quiet):
    """The engine as the real one names itself: its entry, then the server and its release."""

    version = "4.3.3"
    identity = vue_svelte.TypeScriptEngine.identity


def test_the_store_entry_names_the_entry_that_serves_the_language_so_the_state_agrees(tmp_path):
    """The pass reads a store entry as fresh only when it names the entry that serves the language now
    (`engine_pass.from_source`): the stage's report and the edge state say the same."""
    import engine_pass
    import snapshot
    assert Served().identity() == "typescript@typescript-language-server@4.3.3"
    root = reasons._project(tmp_path / "proj", {"Only.vue": ASKED + "<template>\n  <p>{{ n }}</p>\n</template>\n"})
    manifest = tmp_path / "manifest.sqlite"
    snapshot.write_snapshot(root, manifest)
    report = rx.resolve_edges(manifest, engine=Served(), limit=None, stride=1, out=tmp_path / "engine-edges.sqlite")
    assert report["languages"]["vue"]["state"] == "fresh"
    assert engine_pass.from_source("vue", report["languages"]["vue"])
    state = rx.edge_state(manifest)["languages"]["vue"]
    assert (state["state"], state["coverage"]) == ("fresh", report["languages"]["vue"]["coverage"])
