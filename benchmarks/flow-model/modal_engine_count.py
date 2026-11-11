"""Phase 2 step 1 on Modal: resolved `chiama` links over resolvable, per case, with the product engines.

One container per case. Each builds the snapshot of the case target at its declared
commit, runs the engine pass in the foreground and returns the coverage summary.
Nothing heavy runs on the local machine: it only uploads the plugin scripts and the
private case archive, then writes the summaries.

    modal run benchmarks/flow-model/modal_engine_count.py --phazly-tar PATH [--cases polar,tududi,phazly]
"""
from __future__ import annotations

import json
from pathlib import Path

import modal

HERE = Path(__file__).resolve().parent
# Paths of the checkout exist only on the local side; the container reads /daodan/scripts.
SCRIPTS = HERE.parents[1] / "plugins/codebase-map/skills/map/scripts" if modal.is_local() else Path("/daodan/scripts")
RESULTS = HERE / "results"

CASES = {
    "polar": {"repo": "https://github.com/polarsource/polar.git",
              "commit": "ee8e1c01492eeeb6bd773d35a51a01ed53e613dc", "target": "server"},
    "tududi": {"repo": "https://github.com/chrisvel/tududi.git",
               "commit": "71da9d7b34dfd1600657e9c5ddf40420206fd263", "target": "."},
    "phazly": {"tar": "phazly.tar", "target": "."},
    # Diagnostics: phazly's interface alone, polar with the project's own environment.
    "phazly-react": {"tar": "phazly.tar", "target": "react-app"},
    "polar-venv": {"repo": "https://github.com/polarsource/polar.git",
                   "commit": "ee8e1c01492eeeb6bd773d35a51a01ed53e613dc", "target": "server",
                   "setup": "cd server && uv sync --frozen --no-install-project --no-dev"},
}

image = (
    modal.Image.debian_slim(python_version="3.13")
    .apt_install("git", "curl", "ca-certificates", "nodejs", "npm")
    .pip_install("uv", "tree-sitter==0.26.0", "tree-sitter-language-pack==1.13.5", "sqlglot>=30")
    .add_local_dir(SCRIPTS, "/daodan/scripts", ignore=["**/__pycache__/**", "**/tests/**"])
)
app = modal.App("daodan-flow-engine-count", image=image)
# Each result is also kept here, so a detached run survives the local client: `modal volume get`.
volume = modal.Volume.from_name("daodan-flow-results", create_if_missing=True)


def _run(command: list[str], cwd: str | None = None) -> str:
    import subprocess
    done = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
    if done.returncode not in (0, 1):
        raise RuntimeError(f"{' '.join(command)} -> {done.returncode}\n{done.stderr[-4000:]}")
    return done.stdout


@app.function(cpu=4, memory=16384, timeout=3 * 3600, volumes={"/results": volume})
def count(name: str, case: dict, archive: bytes | None, tag: str = "") -> dict:
    import io
    import sys
    import tarfile
    import time

    work = Path("/work") / name
    source = work / "src"
    source.mkdir(parents=True)
    if archive is not None:
        with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
            tar.extractall(source, filter="data")
        _run(["git", "init", "-q"], str(source))
        _run(["git", "add", "-A"], str(source))
        _run(["git", "-c", "user.name=bench", "-c", "user.email=bench@local", "commit", "-qm", "case"], str(source))
    else:
        _run(["git", "init", "-q"], str(source))
        _run(["git", "remote", "add", "origin", case["repo"]], str(source))
        _run(["git", "fetch", "-q", "--depth", "1", "origin", case["commit"]], str(source))
        _run(["git", "checkout", "-q", "FETCH_HEAD"], str(source))
    setup = None
    if case.get("setup"):
        import subprocess
        done = subprocess.run(["sh", "-c", case["setup"]], cwd=source, capture_output=True, text=True)
        setup = {"returncode": done.returncode, "tail": (done.stdout + done.stderr)[-1500:]}
    manifest = work / "snapshot/manifest.sqlite"
    started = time.time()
    _run([sys.executable, "/daodan/scripts/snapshot.py", "write", str(source / case["target"]),
          "--out", str(manifest), "--no-engine"])
    snapshot_seconds = round(time.time() - started, 1)
    started = time.time()
    _run([sys.executable, "/daodan/scripts/resolve_edges.py", str(manifest), "--pass",
          "--report-out", str(work / "engine-report.json")])
    pass_seconds = round(time.time() - started, 1)
    sys.path.insert(0, "/daodan/scripts")
    import edge_view
    view = edge_view.load_edge_view(manifest)
    report = json.loads((work / "engine-report.json").read_text(encoding="utf-8"))
    result = {"case": name, "snapshot_seconds": snapshot_seconds, "pass_seconds": pass_seconds, "setup": setup,
            "resolution": view["coverage"].get("resolution"), "gaps": view["gaps"][:20],
            "languages": report.get("languages"), "unresolved": _unresolved(manifest),
            "pass_log": _tail(manifest.with_name("engine-pass.log"))}
    if tag:
        out = Path("/results") / tag / f"engine-count-{name}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        volume.commit()
    return result


def _tail(path: Path, lines: int = 60) -> list[str]:
    try:
        return path.read_text(encoding="utf-8", errors="replace").splitlines()[-lines:]
    except OSError:
        return []


def _unresolved(manifest: Path) -> dict:
    """Per language, the most frequent engine verdicts and callee names that did not become an edge."""
    import collections
    import sqlite3
    import resolve_edges
    answers = resolve_edges.default_answers_path(manifest)
    if not answers.is_file():
        return {"error": f"no answer cache at {answers}"}
    snap = sqlite3.connect(manifest)
    names = {ref: (name, language) for ref, name, language in snap.execute(
        "SELECT r.id, r.last_name, c.language FROM sem_references r JOIN sem_coverage c ON c.file = r.file "
        "WHERE r.kind = 'call'")}
    verdicts, callees = collections.defaultdict(collections.Counter), collections.defaultdict(collections.Counter)
    for ref, verdict in sqlite3.connect(answers).execute("SELECT reference_id, verdict FROM answers"):
        name, language = names.get(ref, (None, "unknown"))
        verdicts[language][verdict] += 1
        if not str(verdict).startswith("edge"):
            callees[language][f"{name} [{verdict}]"] += 1
    return {language: {"verdicts": dict(verdicts[language].most_common()),
                       "top_unresolved": callees[language].most_common(25)} for language in verdicts}


@app.function(cpu=4, memory=16384, timeout=3600, volumes={"/results": volume})
def flow_links(name: str, case: dict, archive: bytes, rules: str, tag: str = "") -> dict:
    """The links `flows.py` deduces on a case from its rules, on a snapshot without the engine pass."""
    import io
    import sys
    import tarfile

    work = Path("/work") / name
    source = work / "src"
    source.mkdir(parents=True)
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        tar.extractall(source, filter="data")
    _run(["git", "init", "-q"], str(source))
    _run(["git", "add", "-A"], str(source))
    _run(["git", "-c", "user.name=bench", "-c", "user.email=bench@local", "commit", "-qm", "case"], str(source))
    manifest = work / "snapshot/manifest.sqlite"
    _run([sys.executable, "/daodan/scripts/snapshot.py", "write", str(source / case["target"]),
          "--out", str(manifest), "--no-engine", "--no-index"])
    (work / "rules.json").write_text(rules, encoding="utf-8")
    sys.path.insert(0, "/daodan/scripts")
    import flows
    links = flows.link_facts(manifest, flows.load_rules(work / "rules.json"))
    links["sizes"] = flows.file_sizes(manifest)
    if tag:
        out = Path("/results") / tag / f"flow-links-{name}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(links, sort_keys=True), encoding="utf-8")
        volume.commit()
    return links


@app.local_entrypoint()
def flows(phazly_tar: str, rules: str, out: str, case: str = "phazly", tag: str = ""):
    result = flow_links.remote(case, CASES[case], Path(phazly_tar).read_bytes(), Path(rules).read_text(encoding="utf-8"), tag)
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(json.dumps(result, sort_keys=True), encoding="utf-8")
    print(case, len(result["edges"]), "edges", len(result["stores"]), "stores", len(result["entries"]), "entries",
          len(result["gaps"]), "gaps", result["routes"])


@app.local_entrypoint()
def main(phazly_tar: str = "", cases: str = "polar,tududi,phazly", results_dir: str = "", tag: str = ""):
    chosen = [name.strip() for name in cases.split(",") if name.strip()]
    archive = Path(phazly_tar).read_bytes() if any("tar" in CASES[name] for name in chosen) else None
    calls = [(name, CASES[name], archive if "tar" in CASES[name] else None, tag) for name in chosen]
    destination = Path(results_dir) if results_dir else RESULTS
    destination.mkdir(parents=True, exist_ok=True)
    for result in count.starmap(calls, return_exceptions=True):
        if isinstance(result, Exception):
            print("FAILED", repr(result)[:2000])
            continue
        out = destination / f"engine-count-{result['case']}.json"
        out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(result["case"], json.dumps(result["resolution"], sort_keys=True)[:600])
