"""Inference audit on Modal: for each case and each engine, what is asked, what the engine answers, what
is stored and what reaches the graph (README of this benchmark, P1 to P7). No model.

One container per case: snapshot, the product's engine pass, then `probe.py` in each engine's own stage
environment (the command `resolve_edges.stage_command` builds), then the graph use measured in process.

    modal run --detach benchmarks/inference-audit/modal_audit.py --phazly-tar PATH [--cases ...]
"""
from __future__ import annotations

import json
from pathlib import Path

import modal

HERE = Path(__file__).resolve().parent
# Paths of the checkout exist only on the local side; the container reads /daodan/map and /audit.
ROOT = HERE.parents[1] if modal.is_local() else Path("/")
PLUGIN = ROOT / "plugins/codebase-map/skills/map" if modal.is_local() else Path("/daodan/map")
SCRIPTS = "/daodan/map/scripts"
RESULTS = HERE / "results"
TAG = "inference-audit"

CASES = {
    "phazly": {"tar": True, "target": ".", "rules": "benchmarks/phazly-flow/rules.json"},
    "tududi": {"repo": "https://github.com/chrisvel/tududi.git", "target": ".",
               "commit": "71da9d7b34dfd1600657e9c5ddf40420206fd263", "rules": "benchmarks/tududi-flow/rules.json"},
    "javapoet": {"repo": "https://github.com/square/javapoet.git", "target": ".",
                 "commit": "b9017a9503b76e11b4ad4c1a9f050e2d29112cb0"},
    "klaxon": {"repo": "https://github.com/cbeust/klaxon.git", "target": ".",
               "commit": "1173bdc568a6d339b45cf24a6a9c5c2f6847f42d"},
    "semver": {"repo": "https://github.com/dtolnay/semver.git", "target": ".",
               "commit": "280ebcb6edac3aa4cdc545dbff8a26c5ac4861fe"},
    "chi": {"repo": "https://github.com/go-chi/chi.git", "target": ".",
            "commit": "c64ed7d6635f33a8b2feaff7dcfa55677023ac7d"},
}

image = (
    modal.Image.debian_slim(python_version="3.13")
    .apt_install("git", "curl", "ca-certificates", "nodejs", "npm", "unzip", "xz-utils")
    .pip_install("uv", "tree-sitter==0.26.0", "tree-sitter-language-pack==1.13.5", "sqlglot>=30")
    .add_local_dir(PLUGIN, "/daodan/map", ignore=["**/__pycache__/**", "**/tests/**"])
    .add_local_file(HERE / "probe.py" if modal.is_local() else Path("/audit/probe.py"), "/audit/probe.py")
)
app = modal.App("daodan-inference-audit", image=image)
volume = modal.Volume.from_name("daodan-flow-results", create_if_missing=True)


def _run(command: list[str], cwd: str | None = None, ok: tuple = (0,), timeout: int | None = None, env=None):
    import subprocess
    done = subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=timeout, env=env)
    if done.returncode not in ok:
        raise RuntimeError(f"{' '.join(command[:6])} -> {done.returncode}\n{done.stderr[-4000:]}")
    return done


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


def _graph_use(manifest: Path, rules: list | None) -> dict:
    """P6: what the edge view holds and what of it becomes a link of the flows."""
    import collections
    import sys
    sys.path.insert(0, SCRIPTS)
    import edge_view
    import flows
    import resolution
    import semantic_store
    from snapshot_store import open_snapshot
    view = edge_view.load_edge_view(manifest)
    refs = view["references"]
    resolved = collections.Counter()
    for r in refs:
        source = "lexical" if r.get("resolver") == resolution.LEXICAL_RESOLVER else "engine"
        resolved[f"{source} {r['resolution']} target={r.get('target_kind')}"] += 1
    kept, lost, examples = collections.Counter(), collections.Counter(), collections.defaultdict(list)
    with open_snapshot(manifest) as store, semantic_store.semantic_reader(store) as db:
        facts = flows.Facts(store, db)
        for r in refs:
            if r["resolution"] != "resolved":
                continue
            source = "lexical" if r.get("resolver") == resolution.LEXICAL_RESOLVER else "engine"
            # As flows.link_facts links a call: the callee is a node, the caller a node or its module.
            if facts.node(r.get("target_id")):
                kept[source] += 1
                continue
            reason = "no target node"
            lost[f"{source}: {reason}"] += 1
            if len(examples[reason]) < 4:
                examples[reason].append({"site": f"{r['file']}:{(r.get('span') or [None])[0]}",
                                         "caller": r.get("caller"), "target": r.get("target_id")})
    out = {"coverage": {k: v for k, v in view["coverage"].items() if k != "engine_pass"},
           "references": dict(sorted(resolved.items())), "candidates": len(view["candidates"]),
           "conflicts": len(view["conflicts"]), "conflict_examples": view["conflicts"][:4],
           "call_links_kept": dict(kept), "call_links_lost": dict(lost), "lost_examples": dict(examples)}
    if rules:
        links = flows.link_facts(manifest, rules)
        out["links"] = {"edges": dict(collections.Counter(f"{e['type']} {e.get('origin')}" for e in links["edges"])),
                        "entries": dict(collections.Counter(e["kind"] for e in links["entries"])),
                        "routes": links["routes"],
                        "gaps": dict(collections.Counter(g["reason"].split(":")[0][:60] for g in links["gaps"]))}
    return out


@app.function(cpu=4, memory=16384, timeout=4 * 3600, volumes={"/results": volume})
def audit(name: str, case: dict, archive: bytes | None, rules_text: str) -> dict:
    import os
    import sys
    import time

    started = time.time()
    work = Path("/work") / name
    target = _source(work / "src", case, archive)
    manifest = work / "snapshot/manifest.sqlite"
    _run([sys.executable, f"{SCRIPTS}/snapshot.py", "write", str(target), "--out", str(manifest),
          "--no-engine", "--no-index"])
    snapshot_seconds = round(time.time() - started, 1)
    report_path = work / "engine-report.json"
    done = _run([sys.executable, f"{SCRIPTS}/resolve_edges.py", str(manifest), "--pass",
                 "--report-out", str(report_path)], ok=(0, 1), timeout=3 * 3600)
    result = {"case": name, "snapshot_seconds": snapshot_seconds,
              "pass_seconds": round(time.time() - started - snapshot_seconds, 1),
              "pass_stdout": done.stdout[-3000:], "pass_stderr": done.stderr[-3000:]}
    try:
        result["pass_report"] = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        result["pass_report"] = {"error": repr(error)}

    sys.path.insert(0, SCRIPTS)
    import resolve_edges as rx
    plan, _fresh, _digest = rx.pass_plan(manifest)
    result["engines"] = {}
    for spec, wanted in plan:
        out = work / f"probe-{spec.name}.json"
        command = rx.stage_command(spec, manifest, work / "unused.json", [])
        if command is None:
            result["engines"][spec.name] = {"error": "no stage command"}
            continue
        at = next(i for i in range(len(command) - 1) if command[i] == "python" and command[i + 1] == "-B")
        command = command[:at] + ["python", "-B", "/audit/probe.py", SCRIPTS, str(manifest), spec.name, str(out)]
        begun = time.time()
        try:
            probe = _run(command, cwd=SCRIPTS, ok=(0, 1), timeout=7200, env={**os.environ, **spec.environment})
            value = json.loads(out.read_text(encoding="utf-8")) if out.is_file() else \
                {"error": f"exit {probe.returncode}", "stderr": probe.stderr[-3000:]}
        except Exception as error:
            value = {"error": repr(error)[:3000]}
        value["probe_seconds"] = round(time.time() - begun, 1)
        result["engines"][spec.name] = value
    try:
        rules = json.loads(rules_text)["rules"] if rules_text else None
        result["graph_use"] = _graph_use(manifest, rules)
    except Exception as error:
        result["graph_use"] = {"error": repr(error)[:3000]}
    result["seconds"] = round(time.time() - started, 1)
    destination = Path("/results") / TAG / f"audit-{name}.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    volume.commit()
    return result


@app.local_entrypoint()
def main(phazly_tar: str = "", cases: str = ",".join(CASES)):
    chosen = [c.strip() for c in cases.split(",") if c.strip()]
    calls = []
    for name in chosen:
        case = CASES[name]
        archive = Path(phazly_tar).read_bytes() if case.get("tar") else None
        rules = (ROOT / case["rules"]).read_text(encoding="utf-8") if case.get("rules") else ""
        calls.append((name, case, archive, rules))
    RESULTS.mkdir(parents=True, exist_ok=True)
    for result in audit.starmap(calls, return_exceptions=True):
        if isinstance(result, Exception):
            print("FAILED", repr(result)[:2000])
            continue
        (RESULTS / f"audit-{result['case']}.json").write_text(json.dumps(result, indent=1, ensure_ascii=False) + "\n",
                                                              encoding="utf-8")
        print(result["case"], "engines", sorted(result["engines"]), "seconds", result["seconds"])
