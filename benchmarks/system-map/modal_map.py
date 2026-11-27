"""System map benchmark on Modal: the system brief without a model (measure 6), the links of a case,
and the runs of the system-mapper agent (measures 1 to 5).

One container per job, Daodan and its plugin from this checkout. A case without a public repository comes
from an archive (`git archive`, tracked files only); polar and tududi are cloned at the commit of their
flow benchmark. A run prepares a Codebase Map run before any session. With `--rules session` the
engine pass runs, a `claude -p` session given the app's `LINKS` task writes the link rules, and the
links follow from them; the first repetition keeps rules and links on the volume (`rules.json`,
`links.json`) and starts the other repetitions on them, so a case, scope and model has one rules
session. With a rules file the links come computed before and replace the cache; with
`--rules none` the agent finds no rules. The engine pass is the pipeline's, with its containers on Modal
Sandboxes (`modal_pipeline.engine_on_modal`, handed to the pass's child process by a `sitecustomize`): the
code of the analyzed project never runs in the job's own container. Then a fresh `claude -p` session is the agent. The
event streams, the recorded map, the snapshot's files and the cost go to the volume
`daodan-flow-results`, under TAG/LABEL; `modal volume get daodan-flow-results TAG/LABEL
benchmarks/system-map/results/system/TAG` brings a run here. Nothing heavy runs on the local machine.

    modal run benchmarks/system-map/modal_map.py::brief [--tar PATH --links-file PATH] [--cases ...]
    modal run --detach benchmarks/system-map/modal_map.py::links --case tududi --out PATH
    modal run benchmarks/system-map/modal_map.py::entries --tars CASE=PATH[,CASE=PATH] [--tag entries]
    modal run benchmarks/system-map/modal_map.py::possible --snapshot VOLUME-DIR --source VOLUME-DIR --rules PATH
           --expected PATH --out PATH [--generators ritorno,incerto]
    modal run benchmarks/system-map/modal_map.py::engine_proof_run [--tag TAG] [--out PATH]
    python benchmarks/system-map/modal_map.py whole --tag TAG --cases CASE[,CASE] --tar CASE=PATH ...
           [--models qwen,haiku,opus] [--reps 2] [--budget USD]
    modal deploy benchmarks/system-map/modal_map.py
    python benchmarks/system-map/modal_map.py spawn --tag TAG --cases CASE[,CASE] --tar CASE=PATH ...
           [--rules session|none|PATH] [--links CASE=PATH ...] [--scopes system] [--models opus] [--reps 2]
           [--budget USD]
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import modal

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1] if modal.is_local() else Path("/daodan")  # the checkout, and where the image holds it
SCRIPTS = "/daodan/daodan/core"
ENGINE_FOLDER = "/daodan/benchmarks/project-model"  # where `modal_pipeline.py` lies in the image
PROOF = "js-npm-single"  # the fixture of `engine_proof`: one test that calls lodash, `src/index.js`
RESULTS = HERE / "results"
CAPS = (12_000, 24_000, 48_000, 0)  # 0: no cap, the whole brief
HOLDERS = (5, 8, 12)
RUN_ID = "sysmap"
AREA = "pagamenti e abbonamenti"
MODELS = {"haiku": "claude-haiku-5-5", "sonnet": "claude-sonnet-5-5", "opus": "claude-opus-5-5", "qwen": "janura-qwen"}
# Served by the owner's LiteLLM gateway, the comparison beside Claude: its address and key are the Modal secret
# GATEWAY_SECRET (GATEWAY_URL, GATEWAY_KEY), never a file of the repository.
GATEWAY = {"qwen"}
GATEWAY_EFFORT = "medium"  # the gateway's model refuses the effort Claude Code sends by default (`high`)
BUDGET_USD = 3  # per session: a session past it stops, and its summary says so
SESSION_SECONDS = 3600
ENGINE_SECONDS = 2 * 3600  # the pass of the largest case: 51 minutes alone, over an hour under load (23 November 2026)
RULES = ("session", "none")  # the rules a run writes itself, or leaves to the agent; anything else is a rules file

CASES = {
    "polar": {"repo": "https://github.com/polarsource/polar.git",
              "commit": "ee8e1c01492eeeb6bd773d35a51a01ed53e613dc", "target": "server"},
    "tududi": {"repo": "https://github.com/chrisvel/tududi.git",
               "commit": "71da9d7b34dfd1600657e9c5ddf40420206fd263", "target": ".",
               "rules": "benchmarks/tududi-flow/rules.json"},
    # the sample of T0.B.4, from `code_archive.py` on the commit of its `source.json`
    "bank-of-anthos": {"tar": True, "target": "."},
}

SKIP = ["**/__pycache__/**", "**/node_modules/**", "**/tests/**"]
# DAODAN_CODE names the `daodan` folder to run when not the checkout's: an engine index is read only by the code that
# made it (`engine_pass.adapter_fingerprint`), so a measure on a kept run uses the copy that run was made with.
CODE = Path(os.environ.get("DAODAN_CODE") or ROOT / "daodan")
# The package is installed because the plugin's `.mcp.json` starts `daodan mcp`; its dependencies come first,
# from pyproject.toml, so that a change of the code does not reinstall them.
image = (
    modal.Image.debian_slim(python_version="3.13")
    .apt_install("git", "curl", "ca-certificates", "nodejs", "npm")
    .run_commands("npm install -g @anthropic-ai/claude-code", "useradd -m runner")
    .pip_install("uv")
    .pip_install_from_pyproject(str(ROOT / "pyproject.toml"))
    .add_local_file(ROOT / "pyproject.toml", "/daodan/pyproject.toml", copy=True)
    .add_local_file(ROOT / "README.md", "/daodan/README.md", copy=True)
    .add_local_dir(CODE, "/daodan/daodan", copy=True, ignore=SKIP)
    .run_commands("pip install --no-deps -e /daodan")
    .add_local_dir(ROOT / "plugins/codebase-map", "/daodan/plugins/codebase-map", ignore=[*SKIP, "**/viewer/**"])
    .add_local_file(ROOT / "benchmarks/system-map/possible.py", "/daodan/benchmarks/system-map/possible.py")
    # the engine of the pipeline's containers: Modal Sandboxes, as `modal_pipeline.engine_on_modal` gives it
    .add_local_file(ROOT / "benchmarks/project-model/modal_pipeline.py", f"{ENGINE_FOLDER}/modal_pipeline.py")
    .add_local_dir(ROOT / "benchmarks/project-model/fixtures" / PROOF, f"{ENGINE_FOLDER}/fixtures/{PROOF}")
)
app = modal.App("daodan-system-map", image=image)
# The account the agent runs bill: its OAuth token (`claude setup-token`) as CLAUDE_CODE_OAUTH_TOKEN.
CLAUDE_SECRET = "claude-code-alt"
GATEWAY_SECRET = "daodan-gateway"
volume = modal.Volume.from_name("daodan-flow-results", create_if_missing=True)


def _run(command: list[str], cwd: str | None = None, ok: tuple = (0,), timeout: int | None = None) -> str:
    import subprocess
    done = subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    if done.returncode not in ok:
        raise RuntimeError(f"{' '.join(command)} -> {done.returncode}\n{done.stderr[-4000:]}")
    return done.stdout


def _source(source: Path, case: dict, archive: bytes | None) -> Path:
    import io
    import tarfile
    source.mkdir(parents=True)
    if archive is not None:
        with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
            tar.extractall(source, filter="data")
        for command in (["git", "init", "-q"], ["git", "add", "-A"],
                        ["git", "-c", "user.name=bench", "-c", "user.email=bench@local", "commit", "-qm", "case"]):
            _run(command, str(source))
    else:
        _run(["git", "init", "-q"], str(source))
        _run(["git", "remote", "add", "origin", case["repo"]], str(source))
        _run(["git", "fetch", "-q", "--depth", "1", "origin", case["commit"]], str(source))
        _run(["git", "checkout", "-q", "FETCH_HEAD"], str(source))
    return source / case["target"]


def _save(tag: str, name: str, value) -> None:
    out = Path("/results") / tag / name
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(value if isinstance(value, str) else json.dumps(value, indent=1, ensure_ascii=False) + "\n",
                   encoding="utf-8")


@app.function(cpu=4, memory=16384, timeout=2 * 3600, volumes={"/results": volume})
def brief_case(name: str, case: dict, archive: bytes | None, rules: str, links: bytes | None, tag: str) -> dict:
    import time

    work = Path("/work") / name
    target = _source(work / "src", case, archive)
    manifest = work / "snapshot/manifest.sqlite"
    started = time.time()
    _run([sys.executable, f"{SCRIPTS}/snapshot.py", "write", str(target), "--out", str(manifest),
          "--no-engine", "--no-index"])
    sys.path.insert(0, SCRIPTS)
    import flows
    import system_brief
    if links is not None:  # computed before with the engine pass: the brief reads them as they are
        given = json.loads(links)
        flows.cached_links = lambda _manifest, _rules: given
    (work / "rules.json").write_text(rules, encoding="utf-8")
    value = system_brief.brief(manifest, flows.load_rules(work / "rules.json") if rules else [])
    sizes = {f"{cap}/{holders}": dict(zip(("chars", "truncated"),
                                          (lambda t: (len(t[0]), t[1]))(system_brief._text(value, cap or 10**9, holders))))
             for cap in CAPS for holders in HOLDERS}
    result = {"case": name, "seconds": round(time.time() - started, 1),
              "externals": [{k: e[k] for k in ("id", "name", "from", "paths")} for e in value["externals"]],
              "entries": value["entries"], "stores": value["stores"],
              "groups": len(value["groups"]), "alone": len(value["alone"]), "sizes": sizes}
    _save(tag, f"brief-{name}.json", result)
    volume.commit()
    return result


@app.function(cpu=4, memory=16384, timeout=2 * 3600, volumes={"/results": volume})
def links_case(name: str, case: dict, rules: str, tag: str) -> dict:
    """The links of a cloned case under its rules, after the engine pass."""
    work = Path("/work") / name
    target = _source(work / "src", case, None)
    manifest = work / "snapshot/manifest.sqlite"
    _run([sys.executable, f"{SCRIPTS}/snapshot.py", "write", str(target), "--out", str(manifest),
          "--no-engine", "--no-index"])
    _run([sys.executable, f"{SCRIPTS}/resolve_edges.py", str(manifest), "--pass",
          "--report-out", str(work / "engine-report.json")], ok=(0, 1))
    sys.path.insert(0, SCRIPTS)
    import flows
    links = flows.link_facts(manifest, flows.validate_rules(json.loads(rules)["rules"]))
    _save(tag, f"links-{name}.json", json.dumps(links, sort_keys=True))
    volume.commit()
    return links


@app.function(cpu=4, memory=65536, timeout=2 * 3600, volumes={"/results": volume})
def possible_case(snapshot: str, source: str, rules: str, expected: str, generators: list[str]) -> dict:
    """`possible.py` with no model on a run the whole pipeline made (`modal_pipeline.py --folder-out`), whose files
    are in the folder `snapshot` of the volume and whose project is in the folder `source`, laid where the snapshot
    says its root is (the links read the arguments of a call from the files): the links under `rules`, then the
    measure against `expected`. The
    reference comes with the call and the answer goes back to the caller: neither is kept on the volume."""
    import shutil
    work = Path("/work/possible")
    shutil.copytree(Path("/results") / snapshot, work)  # the links' cache is written beside the manifest
    manifest = work / "manifest.sqlite"
    sys.path[:0] = [SCRIPTS, "/daodan/benchmarks/system-map"]
    import flows
    import possible
    from snapshot_store import open_snapshot
    with open_snapshot(manifest) as store:
        shutil.copytree(Path("/results") / source, store["root"])
    import technologies
    technologies.ensure(manifest)  # the stack step's record, which the links read: the run's files may lack it
    links = flows.link_facts(manifest, flows.validate_rules(json.loads(rules)["rules"]))
    kinds, types = {}, {}
    for entry in links["entries"]:
        kinds[entry["kind"]] = kinds.get(entry["kind"], 0) + 1
    for edge in links["edges"]:
        types[edge["type"]] = types.get(edge["type"], 0) + 1
    import modules
    reasons = {}
    for gap in links["gaps"]:
        reasons[gap["reason"]] = reasons.get(gap["reason"], 0) + 1
    graph = modules.ensure_graph(manifest)
    import edge_view
    view = edge_view.load_edge_view(manifest)  # whether the links read the engine's store or fell back
    import entries
    syntax, forwarded, with_gap = entries.cached_syntax(manifest), {}, {}
    for row in syntax:  # what the syntax readers found and what became of it
        if row.get("forwarded"):
            forwarded[row["shape"]] = forwarded.get(row["shape"], 0) + 1
        if row.get("gap"):
            key = row["gap"].split(":")[0][:90]
            with_gap[key] = with_gap.get(key, 0) + 1
    return {"links": {"edges": types, "entries": kinds, "gaps": len(links["gaps"]), "routes": links["routes"],
                      "external": len(links["external"]), "source_gaps": links["source_gaps"],
                      "gap_reasons": sorted(reasons.items(), key=lambda item: -item[1])[:60],
                      "graph": {key: graph.get(key) for key in ("state", "reason", "modules")},
                      "engine": {"coverage": view["coverage"].get("status"), "profile": view["profile"],
                                 "languages": {name: entry.get("state") for name, entry in
                                               (view["coverage"].get("languages") or {}).items()},
                                 "gaps": view["gaps"][:20], "references": len(view["references"])},
                      "syntax": {"candidates": len(syntax), "forwarded": sum(forwarded.values()),
                                 "forwarded_shapes": sorted(forwarded.items(), key=lambda item: -item[1])[:40],
                                 "gaps": sorted(with_gap.items(), key=lambda item: -item[1])[:25]}},
            "measure": possible.measure(manifest, links, json.loads(expected), tuple(generators))}


@app.function(cpu=4, memory=16384, timeout=2 * 3600, volumes={"/results": volume})
def entries_case(name: str, case: dict, archive: bytes | None, tag: str) -> dict:
    """The entry candidates of a case without rules, after the engine pass, with the calls of its links and the
    snapshot's files: what `entries.py measure` reads (plan, Task C4.1)."""
    work = Path("/work") / name
    target = _source(work / "src", case, archive)
    manifest = work / "snapshot/manifest.sqlite"
    _run([sys.executable, f"{SCRIPTS}/snapshot.py", "write", str(target), "--out", str(manifest),
          "--no-engine", "--no-index"])
    _run([sys.executable, f"{SCRIPTS}/resolve_edges.py", str(manifest), "--pass",
          "--report-out", str(work / "engine-report.json")], ok=(0, 1), timeout=ENGINE_SECONDS)
    sys.path.insert(0, SCRIPTS)
    import entries
    import flows
    import system_map
    links = flows.link_facts(manifest, [])
    found = {"case": name, "candidates": entries.candidates(links, manifest),
             "calls": sorted({(e["from"], e["to"]) for e in links["edges"] if e["type"] in entries.CALLS})}
    files = "".join(f"{path}\n" for path in sorted(system_map._headers(manifest)))
    _save(tag, f"{name}/candidates.json", found)
    _save(tag, f"{name}/files.txt", files)
    volume.commit()
    return {"case": name, "candidates": found, "files": files}


PROMPT = ("The Codebase Map run `{run}` of this project is bound and {rules}. "
          "Propose the system map {what}. Follow «Sequence» of the map format and answer with the counts.")


def _label(name: str, scope: str, model: str, rules: str, rep: int) -> str:
    return f"{name}-{scope}-{model}-{rules if rules in RULES else 'given'}-{rep}"


def _tool_texts(stream: list[dict]):
    """The text of every tool answer of a session, in order."""
    for event in stream:
        for block in (event.get("message") or {}).get("content") or []:
            if isinstance(block, dict) and block.get("type") == "tool_result":
                content = block.get("content")
                yield "".join(c.get("text", "") for c in content if isinstance(c, dict)) \
                    if isinstance(content, list) else str(content or "")


def _report_refused(stream: list[dict]) -> int | None:
    """Arrows refused in the last answer to a `map` proposal of the session."""
    last = None
    for text in _tool_texts(stream):
        try:
            value = json.loads(text)
        except ValueError:
            continue
        if isinstance(value, dict) and "coverage" in value and "flows" in value:
            last = value
    if last is None:
        return None
    return sum(1 for f in last["flows"] for a in f.get("arrows", []) if a.get("status") == "refused")


def _spent(stream: list[dict]) -> dict:
    """What a session cost and did: from its `result` and `init` events, its tool calls and their answers."""
    import collections
    result = next((e for e in reversed(stream) if e.get("type") == "result"), {})
    init = next((e for e in stream if e.get("type") == "system" and e.get("subtype") == "init"), {})
    tools = collections.Counter(block.get("name") for event in stream if event.get("type") == "assistant"
                                for block in (event.get("message") or {}).get("content") or []
                                if isinstance(block, dict) and block.get("type") == "tool_use")
    # what the tools gave back: size, and whether the host kept it out of the session
    answers = [{"chars": len(text), "kept_out": text.startswith("<persisted-output>")
                or "exceeds maximum allowed tokens" in text, "error": text.startswith("Error")}
               for text in _tool_texts(stream)]
    return {"cost_usd": result.get("total_cost_usd"), "turns": result.get("num_turns"), "usage": result.get("usage"),
            "model_usage": result.get("modelUsage"), "budget_stop": result.get("subtype") == "error_max_budget_usd",
            "subtype": result.get("subtype"), "tools": dict(tools), "answers": answers,
            "init_tools": init.get("tools"), "init_mcp": init.get("mcp_servers"),
            "version": init.get("claude_code_version"), "result": (result.get("result") or "")[-3000:]}


def _levels(system: dict, links: dict, manifest: Path) -> dict:
    """Measure 3 on every recorded flow: each level shows only its node types and every cited point exists."""
    import flows
    import system_levels
    from snapshot_store import open_snapshot

    def points(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if key in ("site", "cite") and isinstance(item, str):
                    yield item
                else:
                    yield from points(item)
        elif isinstance(value, list):
            for item in value:
                yield from points(item)

    out = {"views": 0, "out_of_level": [], "missing_points": [], "technical_with_persone": []}
    with open_snapshot(manifest) as store:
        source = flows.Source(store)
        for flow in system["flows"]:
            for level in system_levels.LEVELS:
                view = system_levels.view(system, flow["name"], [level], links)
                out["views"] += 1
                for node in view["nodes"]:
                    home = ["codice"] if node["type"] == "file" else system_levels.levels_of(
                        next(n for n in system["nodes"] if n["name"] == node["name"]))
                    if node["level"] != level or level not in home:
                        out["out_of_level"].append(f"{flow['name']} / {level}: {node['name']}")
                for point in points({"arrows": view["arrows"], "gaps": view["gaps"]}):
                    path, _, line = point.rpartition(":")
                    lines = source.lines(path) if line.isdigit() else None
                    if lines is None or not 1 <= int(line) <= len(lines):
                        out["missing_points"].append(point)
                if level == "persone" and flow.get("types") == ["tecnico"] and view["nodes"]:
                    out["technical_with_persone"].append(flow["name"])
    out["missing_points"] = sorted(set(out["missing_points"]))
    return out


HOME = Path("/home/runner")
AS_RUNNER = ["runuser", "-u", "runner", "--", "env", f"HOME={HOME}"]


def _own() -> None:
    """The runner's home is the runner's again, with what root wrote in it: the sessions run as the runner."""
    import subprocess
    subprocess.run(["chown", "-R", "runner:runner", str(HOME)], check=True)


def _engine_pass(manifest: Path) -> dict:
    """`resolve_edges.py --pass`, the pipeline from the pre-map to the union, with its containers on Modal Sandboxes:
    the child process gets the engine from its `sitecustomize` (`modal_pipeline.engine_environment`), so the pre-map's
    commands, scip-typescript and the dynamic step's tests never run in this function. The report lands in
    `HOME/engine-report.json`. The answer: the pass's `exit` code and `stderr` tail, `timed_out`, and each
    language's state in the report as `languages` (absent when the pass wrote none: it ended before its analyzers).
    The pass runs in a process group of its own: at the limit it gets an interrupt, so that the sandboxes it started
    and its folders on the volume are removed (`sandbox_run`'s `finally`), and a kill 120 seconds later."""
    import signal
    import subprocess
    sys.path.insert(0, ENGINE_FOLDER)
    import modal_pipeline
    report = HOME / "engine-report.json"
    process = subprocess.Popen(
        [sys.executable, f"{SCRIPTS}/resolve_edges.py", str(manifest), "--pass", "--report-out", str(report)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True,
        env={**os.environ, **modal_pipeline.engine_environment()})
    answer = {"timed_out": False}
    try:
        _, error = process.communicate(timeout=ENGINE_SECONDS)
    except subprocess.TimeoutExpired:
        answer["timed_out"] = True
        error = ""
        for sent, wait in ((signal.SIGINT, 120), (signal.SIGKILL, 30)):
            try:
                os.killpg(process.pid, sent)
                _, error = process.communicate(timeout=wait)
                break
            except (subprocess.TimeoutExpired, ProcessLookupError):
                continue
    answer.update(exit=process.returncode, stderr=(error or "")[-2000:])
    if report.is_file():  # rewritten after every stage: what a timed-out pass reached stays
        answer["languages"] = {language: entry.get("state") for language, entry
                               in (json.loads(report.read_text(encoding="utf-8")).get("languages") or {}).items()}
    return answer


def _engine_failure(engine: dict | None) -> str | None:
    """Why the engine pass left nothing to build on, or None: it timed out, ended with a code other than 0 or 1, or
    wrote no report (a crash exits with 1 too). Without a pass (a rules file replaced it) there is nothing to say."""
    if engine is None:
        return None
    if engine["timed_out"]:
        return f"the engine pass timed out after {ENGINE_SECONDS} seconds"
    if engine["exit"] not in (0, 1) or "languages" not in engine:
        return f"the engine pass {'wrote no report' if engine['exit'] in (0, 1) else 'exited with ' + str(engine['exit'])}: {engine['stderr'][-400:]}"
    return None


def _prepare(project: Path, target: Path, rules: str, links: bytes | None, model: str,
             budget: float) -> tuple[Path, dict | None, dict | None]:
    """The Codebase Map run before any session, and the rules session when `rules` is `session`; with the engine
    pass's answer (`_engine_pass`, None when a rules file replaced it).

    A rules file is recorded and its links, computed before with the engine pass, replace the cache. Otherwise the
    engine pass runs here, and the rules session is the app's: the `LINKS` task with the rule format the service
    answers, given to Claude Code on the app's command line, with Daodan's server as the installed command."""
    import engines
    import mcp_service
    service = mcp_service.MapService(project)
    service.create_run(target.relative_to(project).as_posix(), RUN_ID, engine=False)
    manifest = project / f".daodan/map/runs/{RUN_ID}/snapshot/manifest.sqlite"
    if rules not in RULES:
        service.flows(RUN_ID, rules=json.loads(rules)["rules"])
        cache = manifest.with_name("flow-links.json")
        kept = json.loads(cache.read_text(encoding="utf-8"))
        kept["links"] = json.loads(links)
        cache.write_text(json.dumps(kept), encoding="utf-8")
        return manifest, None, None
    engine = _engine_pass(manifest)
    if rules == "none":
        return manifest, None, engine
    import app as daodan_app
    needs = service.flows(RUN_ID)
    if needs.get("status") != "needs_rules":
        raise RuntimeError(f"a new run should need its rules; the service answered {str(needs)[:600]}")
    technologies = needs.get("technologies") or needs.get("technologies_unavailable")
    if "technologies_remaining" in needs:  # as the app fills its task (`App.link`)
        technologies = {"units": needs["technologies"], "remaining": needs["technologies_remaining"],
                        "lookup": needs["technologies_lookup"]}
    prompt = daodan_app.LINKS.format(run=RUN_ID, rounds=daodan_app.ROUNDS, format=needs["format"],
                                     technologies=json.dumps(technologies, ensure_ascii=False),
                                     shapes=json.dumps(needs.get("shapes", {}), ensure_ascii=False))
    folder = HOME / "engine"
    folder.mkdir()
    arguments = engines.ClaudeCode().arguments(
        {"mcp": {"command": "daodan", "args": ["mcp", "--project", str(project)]}}, folder)
    command = [*AS_RUNNER, "claude", *arguments, "--model", MODELS[model], "--max-budget-usd", str(budget)]
    return manifest, {"command": command, "prompt": prompt, "cwd": folder}, engine


def _through(environment: dict, model: str) -> dict:
    """A model of the gateway: Claude Code talks to the gateway with its key, every model name it would use is that
    model, and the Claude account's token stays out of the session. The gateway's address and key, as the secret
    names them, reach no session: a Claude model's session has no use for them."""
    own = {k: v for k, v in environment.items() if k not in ("GATEWAY_URL", "GATEWAY_KEY")}  # never a session's to read
    if model not in GATEWAY:
        return own
    name = MODELS[model]
    kept = {k: v for k, v in own.items() if k not in ("CLAUDE_CODE_OAUTH_TOKEN", "ANTHROPIC_API_KEY")}
    return {**kept, "ANTHROPIC_BASE_URL": environment["GATEWAY_URL"], "ANTHROPIC_AUTH_TOKEN": environment["GATEWAY_KEY"],
            "ANTHROPIC_MODEL": name, "ANTHROPIC_DEFAULT_OPUS_MODEL": name, "ANTHROPIC_DEFAULT_SONNET_MODEL": name,
            "ANTHROPIC_DEFAULT_HAIKU_MODEL": name, "ANTHROPIC_SMALL_FAST_MODEL": name,
            "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1"}


def _session(command: list[str], prompt: str, cwd: Path, stream_file: Path, model: str) -> dict:
    """One `claude -p` session, its prompt on its input: its events as they came, and how it ended."""
    import os
    import subprocess
    import time
    if model in GATEWAY:
        command = [*command, "--effort", GATEWAY_EFFORT]
    environment = _through({**os.environ, "HOME": str(HOME), "USER": "runner", "MCP_TIMEOUT": "120000",
                            "CLAUDE_CODE_MCP_STARTUP_WAIT_MS": "120000"}, model)
    started, timed_out = time.time(), False
    with stream_file.open("w", encoding="utf-8") as sink:
        process = subprocess.Popen(command, cwd=cwd, env=environment, stdin=subprocess.PIPE, stdout=sink,
                                   stderr=subprocess.PIPE, text=True)
        try:
            _, error = process.communicate(prompt, timeout=SESSION_SECONDS)
        except subprocess.TimeoutExpired:
            process.kill()
            _, error = process.communicate()
            timed_out = True
    text = stream_file.read_text(encoding="utf-8", errors="replace")
    stream = []
    for line in text.splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if isinstance(event, dict):
            stream.append(event)
    return {"stream": stream, "text": text, "returncode": process.returncode, "timed_out": timed_out,
            "seconds": round(time.time() - started), "stderr": (error or "")[-3000:]}


def _costs(sessions: dict) -> dict:
    """Each session's end and spending, and the run's: the cost summed, and whether a budget stopped a session."""
    ended = {name: {**{key: session[key] for key in ("returncode", "timed_out", "seconds", "stderr")},
                    **_spent(session["stream"])} for name, session in sessions.items()}
    return {"cost_usd": round(sum(s["cost_usd"] or 0 for s in ended.values()), 6),
            "budget_stop": any(s["budget_stop"] for s in ended.values()), "sessions": ended}


def _record(manifest: Path, stream: list[dict], tag: str, label: str) -> None:
    """The map as `system_map.load` gives it, with measure 3 and the refused arrows, and the snapshot's files."""
    import flows
    import system_map
    recorded_rules = manifest.with_name("flow-rules.json")
    rules = flows.load_rules(recorded_rules) if recorded_rules.is_file() else []
    recorded = system_map.load(manifest, rules) or {"nodes": [], "flows": []}
    recorded["refused_arrows"] = _report_refused(stream) or 0
    try:
        recorded["levels"] = _levels(recorded, flows.cached_links(manifest, rules), manifest)
    except Exception as error:  # the measure reports, the run's result stays
        recorded["levels"] = {"error": repr(error)[:2000]}
    _save(tag, f"{label}/map.json", recorded)
    _save(tag, f"{label}/files.txt", "".join(f"{path}\n" for path in sorted(system_map._headers(manifest))))


def _hand_on(name: str, case: dict, archive: bytes | None, rules: str, links: dict, scope: str, model: str,
             reps: int, tag: str, budget: float, label: str) -> list[str]:
    """The rules a rules session recorded and their links, kept on the volume beside its run and given to the
    case's other repetitions, which run the agent alone on them: one rules session per case, scope and model."""
    text = json.dumps(links)
    _save(tag, f"{label}/rules.json", rules)
    _save(tag, f"{label}/links.json", text)
    volume.commit()
    return [map_run.spawn(name, case, archive, rules, text.encode("utf-8"), scope, model, rep, tag, budget,
                          origin=label).object_id for rep in range(2, reps + 1)]


# One container per run: a reused container would keep the project and the session state of another.
@app.function(cpu=4, memory=16384, timeout=4 * 3600, volumes={"/results": volume}, single_use_containers=True,
              secrets=[modal.Secret.from_name(CLAUDE_SECRET), modal.Secret.from_name(GATEWAY_SECRET)])
def map_run(name: str, case: dict, archive: bytes | None, rules: str, links: bytes | None, scope: str, model: str,
            rep: int, tag: str, budget: float = BUDGET_USD, reps: int = 1, origin: str | None = None) -> dict:
    """One run: the case prepared, its rules session when asked, the agent, and what they recorded and cost.
    `rules` is `session`, `none` or the text of a rules file, whose `links` come computed before. A rules session
    hands its rules to repetitions 2 to `reps`; `origin` is the run whose session wrote the rules given."""
    import time
    mode = "session" if origin else rules if rules in RULES else "given"
    label = _label(name, scope, model, mode, rep)
    project = HOME / name
    target = _source(project, case, archive)
    sys.path.insert(0, SCRIPTS)
    import flows
    started = time.time()
    manifest, writer, engine = _prepare(project, target, rules, links, model, budget)
    summary = {"case": name, "scope": scope, "model": MODELS[model], "rep": rep,
               "rules": mode, "rules_from": origin, "budget_usd": budget,
               "prepared_seconds": round(time.time() - started), "engine": engine}
    if (HOME / "engine-report.json").is_file():  # what each analyzer came to, kept with the run
        _save(tag, f"{label}/engine-report.json", (HOME / "engine-report.json").read_text(encoding="utf-8"))
    if failure := _engine_failure(engine):  # no session is paid for on a pass that left nothing
        summary["stopped"] = failure
        _save(tag, f"{label}/summary.json", summary)
        volume.commit()
        return summary
    _own()
    _run([*AS_RUNNER, "daodan", "mcp", "--help"], cwd=str(project), timeout=300)  # the server the sessions start
    sessions = {}
    if writer is not None:
        sessions["rules"] = _session(writer["command"], writer["prompt"], writer["cwd"], HOME / "rules-stream.jsonl",
                                     model)
        _save(tag, f"{label}/rules-stream.jsonl", sessions["rules"]["text"])
    recorded_rules = manifest.with_name("flow-rules.json")
    if rules == "session" and not recorded_rules.is_file():
        summary["stopped"] = "the rules session recorded no rules"
    else:
        if recorded_rules.is_file():  # computed now, so that the agent's first call does not wait for them
            computed = flows.cached_links(manifest, flows.load_rules(recorded_rules))
            _own()
            if rules == "session":
                summary["spawned"] = _hand_on(name, case, archive, recorded_rules.read_text(encoding="utf-8"),
                                              computed, scope, model, reps, tag, budget, label)
        what = f"for the area «{AREA}» only, with scope" if scope == "area" else "for the whole system"
        has = "has its link rules" if recorded_rules.is_file() else "has no link rules yet"
        command = [*AS_RUNNER, "claude", "-p", "--agent", "codebase-map:system-mapper", "--model", MODELS[model],
                   "--plugin-dir", "/daodan/plugins/codebase-map", "--dangerously-skip-permissions",
                   "--max-budget-usd", str(budget), "--output-format", "stream-json", "--verbose"]
        sessions["mapper"] = _session(command, PROMPT.format(run=RUN_ID, rules=has, what=what), project,
                                      HOME / "stream.jsonl", model)
        _save(tag, f"{label}/stream.jsonl", sessions["mapper"]["text"])
    summary.update(_costs(sessions))
    try:
        _record(manifest, sessions["mapper"]["stream"] if "mapper" in sessions else [], tag, label)
    except Exception as error:  # the streams and the summary stay
        summary["record_error"] = repr(error)[:2000]
    _save(tag, f"{label}/summary.json", summary)
    volume.commit()
    return summary


@app.function(cpu=4, memory=16384, timeout=2 * 3600, volumes={"/results": volume}, single_use_containers=True)
def whole_case(name: str, case: dict, archive: bytes | None, counts: str | None, tag: str) -> dict:
    """What a whole job (`whole`) keeps per case for `score.py whole`, under TAG/cases/CASE/: the counts of the
    archive (`code_archive.py`'s, `archive.json`), the answer of the engine pass (`engine.json`) and, when the pass
    left something to build on, the entry candidates with the snapshot's files (`candidates.json`, `files.txt`).
    The pass's containers are Modal Sandboxes: nothing of the project runs in this function."""
    work = Path("/work") / name
    target = _source(work / "src", case, archive)
    manifest = work / "snapshot/manifest.sqlite"
    _run([sys.executable, f"{SCRIPTS}/snapshot.py", "write", str(target), "--out", str(manifest), "--no-engine",
          "--no-index"])
    engine = _engine_pass(manifest)
    if counts:
        _save(tag, f"cases/{name}/archive.json", counts)
    _save(tag, f"cases/{name}/engine.json", engine)
    failure = _engine_failure(engine)
    if not failure:
        sys.path.insert(0, SCRIPTS)
        import entries
        import flows
        import system_map
        links = flows.link_facts(manifest, [])
        _save(tag, f"cases/{name}/candidates.json",
              {"case": name, "candidates": entries.candidates(links, manifest),
               "calls": sorted({(e["from"], e["to"]) for e in links["edges"] if e["type"] in entries.CALLS})})
        _save(tag, f"cases/{name}/files.txt", "".join(f"{path}\n" for path in sorted(system_map._headers(manifest))))
    volume.commit()
    return {"case": name, "engine": engine, "stopped": failure}


@app.function(cpu=4, memory=16384, timeout=3 * 3600, volumes={"/results": volume}, single_use_containers=True)
def routes_case(name: str, case: dict, archive: bytes | None, rules: str, tag: str) -> dict:
    """The routes of a case at the code of this image, with the rules an earlier rules session wrote (`rules`, the text of
    its `rules.json`): the engine pass with its containers on Modal Sandboxes, then `flows.link_facts`. No model. Saved under
    TAG/routes/NAME.json: the counts `offered`, `called` and `linked` of the brief, the entries by reader, the gaps by
    their words, and the calls no route met."""
    import collections
    work = Path("/work") / name
    target = _source(work / "src", case, archive)
    manifest = work / "snapshot/manifest.sqlite"
    _run([sys.executable, f"{SCRIPTS}/snapshot.py", "write", str(target), "--out", str(manifest), "--no-engine",
          "--no-index"])
    engine = _engine_pass(manifest)
    answer = {"case": name, "engine": engine, "stopped": _engine_failure(engine)}
    if not answer["stopped"]:
        sys.path.insert(0, SCRIPTS)
        import flows
        links = flows.link_facts(manifest, json.loads(rules)["rules"])
        gaps = links.get("gaps") or []
        answer.update(
            routes=links["routes"],
            entries_by_reader=dict(collections.Counter(e.get("reader") for e in links["entries"])),
            gaps_by_words=dict(collections.Counter(
                str(g.get("reason") or g.get("detail") or g.get("kind"))[:90] for g in gaps).most_common(25)),
            calls_no_route=[g for g in gaps if "no handler" in str(g.get("reason") or g.get("detail"))][:60])
        # what the dynamic step said about this project: why the app was or was not started and explored
        import premap
        journal = manifest.with_name("pipeline-events.jsonl")
        answer["dynamic_events"] = [
            {"kind": e["kind"], "analyzer": e.get("analyzer"), "level": e.get("level"), "message": str(e["message"])[:220],
             **{key: str((e.get("data") or {})[key])[:300] for key in ("gap", "cause", "remedy") if (e.get("data") or {}).get(key)}}
            for e in (json.loads(line) for line in journal.read_text(encoding="utf-8").splitlines() if line.strip())
            if e.get("step") == "dynamic"][:80] if journal.is_file() else []
        record = json.loads(premap.path(manifest).read_text(encoding="utf-8"))
        answer["premap_starts"] = json.dumps(record.get("starts"))[:3000]
        controls = manifest.with_name("observed-controls.json")
        answer["observed_controls"] = [{k: (len(v) if isinstance(v, (list, dict)) else v) for k, v in app.items()}
                                       for app in json.loads(controls.read_text(encoding="utf-8")).get("apps", [])][:6] \
            if controls.is_file() else None
        # what Noir's rows that no function holds say, and what the snapshot declares in the files they cite
        import edge_view
        import semantic_store
        from premap import noir
        from snapshot_store import open_snapshot
        with open_snapshot(manifest) as store, semantic_store.semantic_reader(store) as db:
            view = edge_view.load_edge_view(store)
            facts = flows.Facts(store, db, view)
            rows = flows.bind_declared(noir.recorded(manifest), facts, view, json.loads(rules)["rules"])
            failed = [row for row in rows if row.get("gap")]
            answer["noir_gaps"] = [{"site": row["site"], "handler": row.get("handler"), "method": row.get("method"),
                                    "path": row.get("path"), "gap": row["gap"][:240]} for row in failed][:90]
            cited = list(dict.fromkeys(row["site"].rpartition(":")[0] for row in failed))
            answer["gap_files"] = len(cited)
            answer["declarations_in_gap_files"] = {
                file: [{key: d.get(key) for key in ("name", "qualified_name", "kind", "line", "end")}
                       for d in facts.functions.get(file, ())][:30] for file in cited[:8]}
    _save(tag, f"routes/{name}.json", answer)
    volume.commit()
    return answer


NETWORK_PROBE = """import urllib.request
for name, url in (("registry", "https://pypi.org/simple/"), ("outside", "https://example.com/"),
                  ("plain", "http://pypi.org/simple/"), ("address", "https://1.1.1.1/")):
    try:
        urllib.request.urlopen(url, timeout=20).close()
        print(name, "reached")
    except Exception as error:
        print(name, "refused", type(error).__name__)
"""
VOLUME_PROBE = ("ls /results 2>&1; echo '--- found'; find / -name secret.txt 2>/dev/null; echo '--- write'; "
                "touch /mnt/daodan-in/x 2>&1; echo write=$?")


def _proof_archive() -> bytes:
    """The proof's fixture as the archive a case comes as (`_source`): its files, but the reference."""
    import io
    import tarfile
    root = Path(ENGINE_FOLDER) / "fixtures" / PROOF
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w") as tar:
        for path in sorted(root.rglob("*")):
            if path.is_file() and path.name != "expected.json":
                tar.add(path, arcname=path.relative_to(root).as_posix())
    return buffer.getvalue()


def _proof_run(name: str, command: list[str], **options) -> tuple[dict, str]:
    """`container.run_in_container` as the pipeline calls it, on Modal Sandboxes, over a one-file project: its
    result and the text of its `prepare.log` and `execute.log`."""
    import container
    from indexers.python import IMAGE  # an image the rounds on Modal have run through `sandbox_run`
    project, out = Path("/tmp/proof") / name / "project", Path("/tmp/proof") / name / "out"
    project.mkdir(parents=True, exist_ok=True)
    (project / "file.txt").write_text("a file\n", encoding="utf-8")
    result = container.run_in_container(project, command, image=IMAGE, out_dir=out, **options)
    logs = "".join((out / log).read_text(encoding="utf-8", errors="replace") for log in ("prepare.log", "execute.log")
                   if (out / log).is_file())
    return result, logs


@app.function(cpu=4, memory=16384, timeout=2 * 3600, volumes={"/results": volume}, single_use_containers=True)
def engine_proof(tag: str) -> dict:
    """The container in the run of the map, on one fixture and before the five cases (task 1 of the plan of the
    unified analysis). Five checks, each with its evidence:

    1. `engine-report.json` says scip-typescript `fresh` on the fixture (`_prepare`, the pass in a child process);
    2. the dynamic step's observed edge is in the store: the engine reached the child process, and the test ran
       in a sandbox under the recorder;
    3. the preparation refuses a destination outside its registries (a host, a plain-HTTP address, an address) and
       reaches one of them;
    4. a sandbox does not see another case's results on the volume, and cannot write to its own folder;
    5. nothing is left after a run that fails (its folder on the volume, a running sandbox), at its preparation or
       before its sandbox exists. It counts the live sandboxes of the shared app `daodan-pipeline-sandboxes`: no other
       round may run while this one does."""
    import sqlite3
    import time
    sys.path[:0] = [SCRIPTS, ENGINE_FOLDER]
    import modal_pipeline
    import container
    checks = {}
    scratch = Path("/results") / modal_pipeline.SCRATCH
    before = {path.name for path in scratch.iterdir()} if scratch.is_dir() else set()

    project = HOME / PROOF
    target = _source(project, {"target": "."}, _proof_archive())
    manifest, _, engine = _prepare(project, target, "none", None, "haiku", 0)
    report = json.loads((HOME / "engine-report.json").read_text(encoding="utf-8")) \
        if (HOME / "engine-report.json").is_file() else {}
    fresh = (engine.get("languages") or {}).get("javascript") == "fresh" and "scip-typescript" in (report.get("engines") or {})
    checks["scip_typescript_fresh"] = {"pass": fresh, "evidence": {"engine": engine, "engines": sorted(report.get("engines") or {})}}
    store = manifest.with_name("engine-edges.sqlite")
    observed, total = [], None
    if store.is_file():  # the dynamic step saves its rows in the analyzers' store (`code_graph.write_observed`)
        with sqlite3.connect(store) as database:
            observed = database.execute("SELECT file, kind, symbol, target_id FROM edges WHERE confidence = 'observed' "
                                        "AND file LIKE '%src/index.js' LIMIT 5").fetchall()
            total = database.execute("SELECT COUNT(*) FROM edges WHERE confidence = 'observed'").fetchone()[0]
    checks["dynamic_edge_observed"] = {"pass": bool(observed), "evidence": {"in_src_index_js": observed,
                                                                             "observed_in_the_store": total}}
    # only from here on this process runs containers itself, as the pass's child process did until now
    modal_pipeline.engine_on_modal(container)

    result, logs = _proof_run("network", ["true"], prepare=["python", "-c", NETWORK_PROBE])
    said = dict(line.split()[:2] for line in logs.splitlines() if line.split()[:1] in (["registry"], ["outside"],
                                                                                        ["plain"], ["address"]))
    checks["preparation_refuses_outside_registries"] = {
        "pass": said == {"registry": "reached", "outside": "refused", "plain": "refused", "address": "refused"}
        and result["state"] == "done", "evidence": {"said": said, "state": result["state"], "cause": result.get("cause")}}

    canary = Path("/results") / tag / "other-case" / "secret.txt"
    canary.parent.mkdir(parents=True, exist_ok=True)
    canary.write_text("another case's result\n", encoding="utf-8")
    volume.commit()
    result, logs = _proof_run("volume", ["sh", "-c", VOLUME_PROBE])
    after_found = logs.split("--- found")[-1].split("--- write")[0]
    checks["sandbox_does_not_read_other_results"] = {
        "pass": "secret.txt" not in after_found and "No such file" in logs.split("--- found")[0]
        and "write=0" not in logs, "evidence": {"log": logs[-800:], "state": result["state"]}}

    failed, _ = _proof_run("failed-preparation", ["true"], prepare=["sh", "-c", "exit 3"])
    broken = container.run_in_container(Path("/tmp/proof/network/project"), ["true"], image="invalid.invalid/none:none",
                                        out_dir=Path("/tmp/proof/broken/out"))
    volume.reload()
    left = ({path.name for path in scratch.iterdir()} if scratch.is_dir() else set()) - before
    running = None
    try:  # a terminated sandbox leaves the list a moment later
        app_id = modal.App.lookup("daodan-pipeline-sandboxes").app_id
        for _ in range(15):
            running = len(list(modal.Sandbox.list(app_id=app_id)))
            if not running:
                break
            time.sleep(2)
    except Exception as error:  # the proof says what it could not count
        running = f"not counted: {type(error).__name__}: {error}"
    checks["everything_removed_after_an_error"] = {
        "pass": failed["state"] != "done" and broken["state"] != "done" and not left and running == 0,
        "evidence": {"states": [failed["state"], broken["state"]], "left_on_the_volume": sorted(left),
                     "sandboxes_running": running, "causes": [str(failed.get("cause"))[:300], str(broken.get("cause"))[:300]]}}
    _save(tag, "engine-proof.json", checks)
    volume.commit()
    return checks


@app.local_entrypoint()
def engine_proof_run(tag: str = "engine-proof", out: str = ""):
    checks = engine_proof.remote(tag)
    for name, check in checks.items():
        print("PASS" if check["pass"] else "FAIL", name)
    RESULTS.mkdir(parents=True, exist_ok=True)
    Path(out or RESULTS / "engine-proof.json").write_text(json.dumps(checks, indent=1, ensure_ascii=False) + "\n",
                                                          encoding="utf-8")


@app.local_entrypoint()
def brief(tar: str = "", links_file: str = "", cases: str = "polar,tududi", tag: str = "system-map"):
    chosen = [c.strip() for c in cases.split(",") if c.strip()]
    root = HERE.parents[1]
    calls = []
    for name in chosen:
        case = CASES[name]
        archive = Path(tar).read_bytes() if case.get("tar") else None
        links = Path(links_file).read_bytes() if case.get("tar") and links_file else None
        rules = (root / case["rules"]).read_text(encoding="utf-8") if case.get("rules") else ""
        calls.append((name, case, archive, rules, links, tag))
    RESULTS.mkdir(parents=True, exist_ok=True)
    for result in brief_case.starmap(calls, return_exceptions=True):
        if isinstance(result, Exception):
            print("FAILED", repr(result)[:2000])
            continue
        (RESULTS / f"brief-{result['case']}.json").write_text(json.dumps(result, indent=1, ensure_ascii=False) + "\n",
                                                              encoding="utf-8")
        print(result["case"], len(result["externals"]), "externals",
              result["groups"], "groups", result["sizes"])


@app.local_entrypoint()
def links(case: str, out: str, tag: str = "system-map"):
    value = links_case.remote(case, CASES[case], (HERE.parents[1] / CASES[case]["rules"]).read_text(encoding="utf-8"), tag)
    Path(out).write_text(json.dumps(value, sort_keys=True), encoding="utf-8")
    print(case, len(value["edges"]), "edges", len(value["stores"]), "stores", len(value["entries"]), "entries",
          len(value["gaps"]), "gaps", value["routes"])


@app.local_entrypoint()
def possible(snapshot: str, source: str, rules: str, expected: str, out: str, generators: str = "ritorno,incerto"):
    """`modal volume put daodan-flow-results DIR SNAPSHOT` first, with the files `--folder-out` brought into DIR,
    and the same for the project's folder as SOURCE."""
    value = possible_case.remote(snapshot, source, Path(rules).read_text(encoding="utf-8"),
                                 Path(expected).read_text(encoding="utf-8"), [g for g in generators.split(",") if g])
    Path(out).write_text(json.dumps(value, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(value["links"], value["measure"]["possible"], value["measure"]["arrows"],
          value["measure"]["entries_from_others"])


@app.local_entrypoint()
def entries(tars: str, tag: str = "entries"):
    """The candidates and files of each case of `--tars CASE=PATH[,CASE=PATH]`, here in results/system/TAG/CASE/."""
    calls = [(name, CASES[name], Path(path).read_bytes(), tag) for name, path in _pairs(tars.split(","), "tars").items()]
    _bring(entries_case.starmap(calls, return_exceptions=True), tag)


def _bring(results, tag: str) -> None:
    """The candidates and files of each case a job returned, here in results/system/TAG/CASE/."""
    for result in results:
        if isinstance(result, Exception):
            print("FAILED", repr(result)[:2000])
            continue
        out = RESULTS / "system" / tag / result["case"]
        out.mkdir(parents=True, exist_ok=True)
        (out / "candidates.json").write_bytes(json.dumps(result["candidates"], ensure_ascii=False, indent=1).encode())
        (out / "files.txt").write_bytes(result["files"].encode("utf-8"))
        print(result["case"], len(result["candidates"]["candidates"]), "candidates",
              len(result["candidates"]["calls"]), "calls", result["files"].count("\n"), "files")


# OWASP Noir, a ready-made finder of the endpoints an application offers (MIT, static analysis; plan, Task C4.14): tried
# here, in a container, before Daodan writes a reader of routes of its own. The version is pinned.
NOIR = "https://github.com/owasp-noir/noir/releases/download/v1.5.0/noir-v1.5.0-linux-x86_64"
noir_image = (modal.Image.debian_slim(python_version="3.13").apt_install("git", "curl", "ca-certificates")
              .run_commands(f"curl -fsSL -o /usr/local/bin/noir {NOIR}", "chmod +x /usr/local/bin/noir"))


@app.function(image=noir_image, cpu=4, memory=8192, timeout=3600, volumes={"/results": volume})
def noir_case(name: str, case: dict, archive: bytes | None, tag: str) -> dict:
    """What Noir finds in a case: its version, its own help (the flags are read from it, not assumed) and its JSON."""
    import subprocess
    work = Path("/work") / name
    target = _source(work / "src", case, archive)
    out = work / "noir.json"

    def run(*args: str, timeout: int = 1800) -> dict:
        done = subprocess.run(["noir", *args], cwd="/work", capture_output=True, text=True, timeout=timeout)
        return {"returncode": done.returncode, "stdout": done.stdout[-20000:], "stderr": done.stderr[-4000:]}

    found = {"case": name, "version": run("--version", timeout=60), "help": run("scan", "-h", timeout=60),
             "scan": run("scan", str(target), "-f", "json", "-o", str(out), "--no-log")}
    found["json"] = out.read_text(encoding="utf-8", errors="replace") if out.is_file() else None
    _save(tag, f"{name}/noir.json", found)
    volume.commit()
    return found


@app.local_entrypoint()
def noir(tars: str, tag: str = "noir"):
    """Noir's answer for each case of `--tars CASE=PATH[,CASE=PATH]`, here in results/system/TAG/CASE/noir.json."""
    calls = [(name, CASES[name], Path(path).read_bytes(), tag) for name, path in _pairs(tars.split(","), "tars").items()]
    for result in noir_case.starmap(calls, return_exceptions=True):
        if isinstance(result, Exception):
            print("FAILED", repr(result)[:2000])
            continue
        out = RESULTS / "system" / tag / result["case"]
        out.mkdir(parents=True, exist_ok=True)
        (out / "noir.json").write_bytes(json.dumps(result, ensure_ascii=False, indent=1).encode("utf-8"))
        print(result["case"], "scan", result["scan"]["returncode"], "json", len(result["json"] or ""), "characters")


def _pairs(values: list[str], what: str) -> dict[str, str]:
    """`CASE=PATH` options as a mapping; a case this file does not know, or a missing `=`, is refused."""
    out = {}
    for value in values:
        name, sep, path = value.partition("=")
        if not sep or not path or name not in CASES:
            raise SystemExit(f"--{what} {value!r}: give CASE=PATH, with CASE one of {', '.join(CASES)}")
        out[name] = path
    return out


def _inputs(name: str, rules: str | None, tars: dict, links: dict) -> tuple[bytes | None, str, bytes | None]:
    """A case's archive, rules and links, read before anything is started: `rules` is `session`, `none`, a rules
    file, or None for the case's own file; a rules file needs the links computed with the engine pass."""
    case = CASES[name]
    if case.get("tar") and name not in tars:
        raise SystemExit(f"{name} comes from an archive: give --tar {name}=PATH")
    archive = Path(tars[name]).read_bytes() if case.get("tar") else None
    if rules in RULES:
        return archive, rules, None
    if rules is None and "rules" not in case:
        raise SystemExit(f"{name} has no rules file: give --rules session, none or PATH")
    if name not in links:
        raise SystemExit(f"a rules file needs the links of the engine pass: give --links {name}=PATH")
    text = Path(rules or ROOT / case["rules"]).read_text(encoding="utf-8")
    return archive, text, Path(links[name]).read_bytes()


def spawn(args) -> None:
    tars, links = _pairs(args.tar, "tar"), _pairs(args.links, "links")
    prepared = {name: _inputs(name, args.rules, tars, links) for name in args.cases.split(",")}
    function = modal.Function.from_name("daodan-system-map", "map_run")
    calls = {}
    for name, (archive, rules, given) in prepared.items():
        for scope in args.scopes.split(","):
            for model in args.models.split(","):
                first = _label(name, scope, model, rules, 1)
                for rep in range(1, args.reps + 1):  # a rules session's first repetition starts the others
                    calls[_label(name, scope, model, rules, rep)] = f"started by {first}" \
                        if rules == "session" and rep > 1 else function.spawn(
                            name, CASES[name], archive, rules, given, scope, model, rep, args.tag, args.budget,
                            reps=args.reps).object_id
    print(json.dumps(calls, indent=1))


def whole(args) -> None:
    """The one job of the unified analysis, from the archives: a `whole_case` per case and an independent `map_run`
    per case, model and repetition. A repetition is a preparation of its own, with its own rules session (`reps=1`:
    none is handed on), so that `score.py whole` can say how stable the map is. With no model, only the cases run."""
    tars = _pairs(args.tar, "tar")
    cases = modal.Function.from_name("daodan-system-map", "whole_case")
    runs = modal.Function.from_name("daodan-system-map", "map_run")
    calls = {}
    for name in args.cases.split(","):
        archive = _inputs(name, "session", tars, {})[0]
        sidecar = Path(tars[name]).with_suffix(".json") if name in tars else None  # `code_archive.py`'s counts
        counts = sidecar.read_text(encoding="utf-8") if sidecar is not None and sidecar.is_file() else None
        if not args.no_cases:
            calls[f"{name} case"] = cases.spawn(name, CASES[name], archive, counts, args.tag).object_id
        for model in (m for m in args.models.split(",") if m):
            for rep in range(1, args.reps + 1):
                calls[_label(name, "system", model, "session", rep)] = runs.spawn(
                    name, CASES[name], archive, "session", None, "system", model, rep, args.tag, args.budget,
                    reps=1).object_id
    print(json.dumps(calls, indent=1))


def _arguments(argv: list[str] | None = None):
    import argparse
    parser = argparse.ArgumentParser(description="Start runs of the deployed app `daodan-system-map`.")
    commands = parser.add_subparsers(dest="command", required=True)
    one = commands.add_parser("spawn", help="one map_run per case, scope, model and repetition")
    one.add_argument("--tag", required=True, help="the folder of the runs on the volume")
    one.add_argument("--cases", default="tududi", help=f"comma-separated, of {', '.join(CASES)}")
    one.add_argument("--tar", action="append", default=[], metavar="CASE=PATH",
                     help="the archive of a case (`git archive`), repeatable")
    one.add_argument("--rules", default=None, metavar="session|none|PATH",
                     help="session: a Claude Code session writes them, as the app does; none: the agent finds none; "
                          "PATH: a rules file; default: the case's own rules file")
    one.add_argument("--links", action="append", default=[], metavar="CASE=PATH",
                     help="the links computed with the engine pass, for a rules file, repeatable")
    one.add_argument("--scopes", default="area,system")
    one.add_argument("--models", default="haiku,sonnet", help=f"comma-separated, of {', '.join(MODELS)}")
    one.add_argument("--reps", type=int, default=2)
    one.add_argument("--budget", type=float, default=BUDGET_USD, help="USD per session")
    every = commands.add_parser("whole", help="the unified analysis: a job per case, and independent runs of the map")
    every.add_argument("--tag", required=True, help="the folder of the job on the volume")
    every.add_argument("--cases", required=True, help=f"comma-separated, of {', '.join(CASES)}")
    every.add_argument("--tar", action="append", default=[], metavar="CASE=PATH",
                       help="the archive of a case (`code_archive.py`), repeatable; its counts are PATH with .json")
    every.add_argument("--no-cases", action="store_true",
                       help="start only the runs of the map, under a TAG whose cases an earlier job already kept")
    every.add_argument("--models", default="", help=f"comma-separated, of {', '.join(MODELS)}; none: only the cases")
    every.add_argument("--reps", type=int, default=2, help="independent runs per case and model")
    every.add_argument("--budget", type=float, default=BUDGET_USD, help="USD per session")
    by_links = commands.add_parser("spawn-links", help="the links of a cloned case; the volume gets links-CASE.json")
    by_links.add_argument("case", choices=[name for name, case in CASES.items() if "repo" in case and "rules" in case])
    by_links.add_argument("tag")
    args = parser.parse_args(argv)
    if args.command in ("spawn", "whole"):
        unknown = [m for m in args.models.split(",") if m and m not in MODELS] + \
                  [c for c in args.cases.split(",") if c not in CASES]
        if unknown:
            parser.error(f"unknown models or cases: {', '.join(unknown)}")
    return args


if __name__ == "__main__":
    arguments = _arguments()
    if arguments.command == "spawn-links":
        function = modal.Function.from_name("daodan-system-map", "links_case")
        print(function.spawn(arguments.case, CASES[arguments.case],
                             (ROOT / CASES[arguments.case]["rules"]).read_text(encoding="utf-8"),
                             arguments.tag).object_id)
    elif arguments.command == "whole":
        whole(arguments)
    else:
        spawn(arguments)
