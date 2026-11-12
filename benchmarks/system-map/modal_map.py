"""System map benchmark on Modal: the system brief without a model (measure 6), the links of a case,
and the runs of the system-mapper agent (measures 1 to 5).

One container per job, plugin scripts of this checkout. Phazly comes from its private archive,
polar and tududi are cloned at the commit of their flow benchmark. A run prepares, before the
session, a Codebase Map run with the case's link rules and the links computed with the engine
pass, then starts a fresh `claude -p` session as the agent; the event stream, the recorded map
and the cost go to the volume `daodan-flow-results`. Nothing heavy runs on the local machine.

    modal run benchmarks/system-map/modal_map.py::brief --phazly-tar PATH --phazly-links PATH [--cases ...]
    modal run --detach benchmarks/system-map/modal_map.py::links --case tududi --out PATH
    modal deploy benchmarks/system-map/modal_map.py
    python benchmarks/system-map/modal_map.py spawn --phazly-tar PATH --phazly-links PATH --tududi-links PATH --tag TAG
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import modal

HERE = Path(__file__).resolve().parent
PLUGIN = HERE.parents[1] / "plugins/codebase-map" if modal.is_local() else Path("/daodan/plugins/codebase-map")
SCRIPTS = "/daodan/plugins/codebase-map/skills/map/scripts"
RESULTS = HERE / "results"
CAPS = (12_000, 24_000, 48_000, 0)  # 0: no cap, the whole brief
HOLDERS = (5, 8, 12)
RUN_ID = "sysmap"
AREA = "pagamenti e abbonamenti"
MODELS = {"haiku": "claude-haiku-5-5", "sonnet": "claude-sonnet-5-5"}
BUDGET_USD = 3  # per run: a session past it stops

CASES = {
    "phazly": {"tar": True, "target": ".", "rules": "benchmarks/phazly-flow/rules.json"},
    "polar": {"repo": "https://github.com/polarsource/polar.git",
              "commit": "ee8e1c01492eeeb6bd773d35a51a01ed53e613dc", "target": "server"},
    "tududi": {"repo": "https://github.com/chrisvel/tududi.git",
               "commit": "71da9d7b34dfd1600657e9c5ddf40420206fd263", "target": ".",
               "rules": "benchmarks/tududi-flow/rules.json"},
}

image = (
    modal.Image.debian_slim(python_version="3.13")
    .apt_install("git", "curl", "ca-certificates", "nodejs", "npm")
    .run_commands("npm install -g @anthropic-ai/claude-code", "useradd -m runner")
    .pip_install("uv", "tree-sitter==0.26.0", "tree-sitter-language-pack==1.13.5", "sqlglot>=30")
    .add_local_dir(PLUGIN, "/daodan/plugins/codebase-map",
                   ignore=["**/__pycache__/**", "**/node_modules/**", "**/tests/**", "**/viewer/**"])
)
app = modal.App("daodan-system-map", image=image)
# The account the agent runs bill: its OAuth token (`claude setup-token`) as CLAUDE_CODE_OAUTH_TOKEN.
CLAUDE_SECRET = "claude-code-alt"
volume = modal.Volume.from_name("daodan-flow-results", create_if_missing=True)


def _run(command: list[str], cwd: str | None = None, ok: tuple = (0,)) -> str:
    import subprocess
    done = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
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
              "stack_analyser": value["stack_analyser"], "entries": value["entries"], "stores": value["stores"],
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


PROMPT = ("The Codebase Map run `{run}` of this project is bound and has its link rules. "
          "Propose the system map {what}. Follow your fixed sequence and answer with the counts.")


def _report_refused(stream: list[dict]) -> int | None:
    """Arrows refused in the last answer to a `map` proposal of the session."""
    last = None
    for event in stream:
        for block in (event.get("message") or {}).get("content") or []:
            if not isinstance(block, dict) or block.get("type") != "tool_result":
                continue
            content = block.get("content")
            text = "".join(c.get("text", "") for c in content if isinstance(c, dict)) if isinstance(content, list) \
                else str(content or "")
            try:
                value = json.loads(text)
            except ValueError:
                continue
            if isinstance(value, dict) and "coverage" in value and "flows" in value:
                last = value
    if last is None:
        return None
    return sum(1 for f in last["flows"] for a in f.get("arrows", []) if a.get("status") == "refused")


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


# One container per run: a reused container would keep the project and the session state of another.
@app.function(cpu=4, memory=16384, timeout=2 * 3600, volumes={"/results": volume}, single_use_containers=True,
              secrets=[modal.Secret.from_name(CLAUDE_SECRET)])
def map_run(name: str, case: dict, archive: bytes | None, rules: str, links: bytes, scope: str, model: str,
            rep: int, tag: str) -> dict:
    import collections
    import os
    import subprocess
    import time

    home = Path("/home/runner")
    project = home / name
    target = _source(project, case, archive)
    rules_file = home / "rules.json"
    rules_file.write_text(rules, encoding="utf-8")
    links_file = home / "links.json"
    links_file.write_bytes(links)
    # The run is prepared before the session: snapshot, rules and the links of the engine pass.
    prepare = (f"import json, sys\nfrom pathlib import Path\nsys.path.insert(0, {SCRIPTS!r})\nimport mcp_service\n"
               f"service = mcp_service.MapService(Path({str(project)!r}))\n"
               f"service.create_run({Path(target).relative_to(project).as_posix() or '.'!r}, {RUN_ID!r}, engine=False)\n"
               f"service.flows({RUN_ID!r}, rules=json.loads(Path({str(rules_file)!r}).read_text())['rules'])\n"
               f"cache = Path({str(project)!r}) / '.daodan/map/runs/{RUN_ID}/snapshot/flow-links.json'\n"
               f"kept = json.loads(cache.read_text())\n"
               f"kept['links'] = json.loads(Path({str(links_file)!r}).read_text())\n"
               f"cache.write_text(json.dumps(kept))\n")
    subprocess.run(["chown", "-R", "runner:runner", str(home)], check=True)
    as_runner = ["runuser", "-u", "runner", "--", "env", f"HOME={home}"]
    # The MCP server's dependencies are installed before the session: a first `uv` install can
    # outlast the first-turn wait, and the session then runs without the server's tools.
    done = subprocess.run([*as_runner, "uv", "run", "--no-config", "--no-project", "--script",
                           f"{SCRIPTS}/mcp_server.py", "--help"], cwd=project, capture_output=True, text=True, timeout=900)
    if done.returncode != 0:
        raise RuntimeError(f"mcp server warm-up -> {done.returncode}\n{done.stderr[-4000:]}")
    # The run is prepared with the server's own dependencies: other parser versions would leave
    # the snapshot stale for the server ("parser fingerprint changed").
    header = Path(f"{SCRIPTS}/mcp_server.py").read_text(encoding="utf-8").split("# ///", 2)[1]
    script = home / "prepare.py"
    script.write_text("# ///" + header + "# ///\n" + prepare, encoding="utf-8")
    subprocess.run(["chown", "runner:runner", str(script)], check=True)
    done = subprocess.run([*as_runner, "uv", "run", "--no-config", "--no-project", "--script", str(script)],
                          cwd=project, capture_output=True, text=True, timeout=1800)
    if done.returncode != 0:
        raise RuntimeError(f"prepare -> {done.returncode}\n{done.stderr[-4000:]}")
    what = f"for the area «{AREA}» only, with scope" if scope == "area" else "for the whole system"
    command = [*as_runner, "claude", "-p", PROMPT.format(run=RUN_ID, what=what), "--agent", "codebase-map:system-mapper",
               "--model", MODELS[model], "--plugin-dir", "/daodan/plugins/codebase-map",
               "--dangerously-skip-permissions", "--max-budget-usd", str(BUDGET_USD),
               "--output-format", "stream-json", "--verbose"]
    stream_file = home / "stream.jsonl"
    started, timed_out = time.time(), False
    with stream_file.open("w", encoding="utf-8") as sink:
        process = subprocess.Popen(command, cwd=project, env={**os.environ, "HOME": str(home), "USER": "runner",
                                                              "MCP_TIMEOUT": "120000",
                                                              "CLAUDE_CODE_MCP_STARTUP_WAIT_MS": "120000"},
                                   stdout=sink, stderr=subprocess.PIPE, text=True)
        try:
            _, error = process.communicate(timeout=2 * 3600 - 900)
        except subprocess.TimeoutExpired:
            process.kill()
            _, error = process.communicate()
            timed_out = True
    seconds = round(time.time() - started)
    stream = []
    for line in stream_file.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            stream.append(json.loads(line))
        except ValueError:
            continue
    result = next((e for e in reversed(stream) if e.get("type") == "result"), {})
    init = next((e for e in stream if e.get("type") == "system" and e.get("subtype") == "init"), {})
    answers = []  # what the tools gave back: size, and whether the host kept it out of the session
    for event in stream:
        for block in (event.get("message") or {}).get("content") or []:
            if isinstance(block, dict) and block.get("type") == "tool_result":
                content = block.get("content")
                text = "".join(c.get("text", "") for c in content if isinstance(c, dict)) \
                    if isinstance(content, list) else str(content or "")
                answers.append({"chars": len(text), "kept_out": text.startswith("<persisted-output>")
                                or "exceeds maximum allowed tokens" in text, "error": text.startswith("Error")})
    tools = collections.Counter(block.get("name") for event in stream if event.get("type") == "assistant"
                                for block in (event.get("message") or {}).get("content") or []
                                if isinstance(block, dict) and block.get("type") == "tool_use")
    sys.path.insert(0, SCRIPTS)
    import flows
    import system_map
    manifest = project / f".daodan/map/runs/{RUN_ID}/snapshot/manifest.sqlite"
    recorded = system_map.load(manifest, flows.load_rules(rules_file)) or {"nodes": [], "flows": []}
    recorded["refused_arrows"] = _report_refused(stream) or 0
    try:
        recorded["levels"] = _levels(recorded, json.loads(links), manifest)
    except Exception as error:  # the measure reports, the run's result stays
        recorded["levels"] = {"error": repr(error)[:2000]}
    label = f"{name}-{scope}-{model}-{rep}"
    summary = {"case": name, "scope": scope, "model": MODELS[model], "rep": rep, "returncode": process.returncode,
               "timed_out": timed_out, "seconds": seconds, "cost_usd": result.get("total_cost_usd"),
               "turns": result.get("num_turns"), "usage": result.get("usage"), "tools": dict(tools),
               "answers": answers, "init_tools": init.get("tools"), "init_mcp": init.get("mcp_servers"), "version": init.get("claude_code_version"),
               "result": (result.get("result") or "")[-3000:], "stderr": (error or "")[-3000:]}
    _save(tag, f"{label}/stream.jsonl", stream_file.read_text(encoding="utf-8", errors="replace"))
    _save(tag, f"{label}/map.json", recorded)
    _save(tag, f"{label}/summary.json", summary)
    volume.commit()
    return summary


@app.local_entrypoint()
def brief(phazly_tar: str = "", phazly_links: str = "", cases: str = "phazly,polar,tududi", tag: str = "system-map"):
    chosen = [c.strip() for c in cases.split(",") if c.strip()]
    root = HERE.parents[1]
    calls = []
    for name in chosen:
        case = CASES[name]
        archive = Path(phazly_tar).read_bytes() if case.get("tar") else None
        links = Path(phazly_links).read_bytes() if case.get("tar") and phazly_links else None
        rules = (root / case["rules"]).read_text(encoding="utf-8") if case.get("rules") else ""
        calls.append((name, case, archive, rules, links, tag))
    RESULTS.mkdir(parents=True, exist_ok=True)
    for result in brief_case.starmap(calls, return_exceptions=True):
        if isinstance(result, Exception):
            print("FAILED", repr(result)[:2000])
            continue
        (RESULTS / f"brief-{result['case']}.json").write_text(json.dumps(result, indent=1, ensure_ascii=False) + "\n",
                                                              encoding="utf-8")
        print(result["case"], len(result["externals"]), "externals", result["stack_analyser"].get("status"),
              result["groups"], "groups", result["sizes"])


@app.local_entrypoint()
def links(case: str, out: str, tag: str = "system-map"):
    value = links_case.remote(case, CASES[case], (HERE.parents[1] / CASES[case]["rules"]).read_text(encoding="utf-8"), tag)
    Path(out).write_text(json.dumps(value, sort_keys=True), encoding="utf-8")
    print(case, len(value["edges"]), "edges", len(value["stores"]), "stores", len(value["entries"]), "entries",
          len(value["gaps"]), "gaps", value["routes"])


def spawn(phazly_tar: str, phazly_links: str, tududi_links: str, tag: str, cases: str, scopes: str, models: str,
          reps: int) -> None:
    function = modal.Function.from_name("daodan-system-map", "map_run")
    root = HERE.parents[1]
    inputs = {"phazly": (Path(phazly_tar).read_bytes(), Path(phazly_links).read_bytes()),
              "tududi": (None, Path(tududi_links).read_bytes() if tududi_links else b"")}
    calls = {}
    for name in cases.split(","):
        archive, links_bytes = inputs[name]
        rules = (root / CASES[name]["rules"]).read_text(encoding="utf-8")
        for scope in scopes.split(","):
            for model in models.split(","):
                for rep in range(1, reps + 1):
                    calls[f"{name}-{scope}-{model}-{rep}"] = function.spawn(
                        name, CASES[name], archive, rules, links_bytes, scope, model, rep, tag).object_id
    print(json.dumps(calls, indent=1))


if __name__ == "__main__":
    if sys.argv[1:2] == ["spawn-links"]:  # python modal_map.py spawn-links CASE TAG: the volume gets links-CASE.json
        function = modal.Function.from_name("daodan-system-map", "links_case")
        name, tag = sys.argv[2], sys.argv[3]
        print(function.spawn(name, CASES[name], (HERE.parents[1] / CASES[name]["rules"]).read_text(encoding="utf-8"),
                             tag).object_id)
    if len(sys.argv) >= 2 and sys.argv[1] == "spawn":
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument("command")
        parser.add_argument("--phazly-tar", required=True)
        parser.add_argument("--phazly-links", required=True)
        parser.add_argument("--tududi-links", default="")
        parser.add_argument("--tag", required=True)
        parser.add_argument("--cases", default="phazly,tududi")
        parser.add_argument("--scopes", default="area,system")
        parser.add_argument("--models", default="haiku,sonnet")
        parser.add_argument("--reps", type=int, default=2)
        args = parser.parse_args()
        spawn(args.phazly_tar, args.phazly_links, args.tududi_links, args.tag, args.cases, args.scopes, args.models,
              args.reps)
