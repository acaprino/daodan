"""System map benchmark on Modal: the system brief of each case, without a model (measure 6, brief size).

One container per case: it builds the snapshot of the case target, composes the brief with
the plugin scripts of this checkout and returns the externals by source and the brief size
for every value of CAP and HOLDERS. Phazly comes from its private archive with the links
already computed; polar and tududi are cloned at the commit of their flow benchmark and have
no link rules, so they have no groups. Nothing heavy runs on the local machine.

    modal run benchmarks/system-map/modal_map.py::brief --phazly-tar PATH --phazly-links PATH [--cases ...]
"""
from __future__ import annotations

import json
from pathlib import Path

import modal

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parents[1] / "plugins/codebase-map/skills/map" if modal.is_local() else Path("/daodan/map")
RESULTS = HERE / "results"
CAPS = (12_000, 24_000, 48_000, 0)  # 0: no cap, the whole brief
HOLDERS = (5, 8, 12)

CASES = {
    "phazly": {"tar": True, "target": ".", "rules": "benchmarks/phazly-flow/rules.json"},
    "polar": {"repo": "https://github.com/polarsource/polar.git",
              "commit": "ee8e1c01492eeeb6bd773d35a51a01ed53e613dc", "target": "server"},
    "tududi": {"repo": "https://github.com/chrisvel/tududi.git",
               "commit": "71da9d7b34dfd1600657e9c5ddf40420206fd263", "target": "."},
}

image = (
    modal.Image.debian_slim(python_version="3.13")
    .apt_install("git", "curl", "ca-certificates", "nodejs", "npm")
    .pip_install("tree-sitter==0.26.0", "tree-sitter-language-pack==1.13.5", "sqlglot>=30")
    .add_local_dir(SCRIPTS, "/daodan/map", ignore=["**/__pycache__/**", "**/tests/**"])
)
app = modal.App("daodan-system-map", image=image)
volume = modal.Volume.from_name("daodan-flow-results", create_if_missing=True)


def _run(command: list[str], cwd: str | None = None) -> None:
    import subprocess
    done = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
    if done.returncode != 0:
        raise RuntimeError(f"{' '.join(command)} -> {done.returncode}\n{done.stderr[-4000:]}")


def _source(work: Path, case: dict, archive: bytes | None) -> Path:
    import io
    import tarfile
    source = work / "src"
    source.mkdir(parents=True)
    if archive is not None:
        with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
            tar.extractall(source, filter="data")
    else:
        _run(["git", "init", "-q"], str(source))
        _run(["git", "remote", "add", "origin", case["repo"]], str(source))
        _run(["git", "fetch", "-q", "--depth", "1", "origin", case["commit"]], str(source))
        _run(["git", "checkout", "-q", "FETCH_HEAD"], str(source))
    return source / case["target"]


@app.function(cpu=4, memory=16384, timeout=2 * 3600, volumes={"/results": volume})
def brief_case(name: str, case: dict, archive: bytes | None, rules: str, links: bytes | None, tag: str) -> dict:
    import sys
    import time

    work = Path("/work") / name
    target = _source(work, case, archive)
    manifest = work / "snapshot/manifest.sqlite"
    started = time.time()
    _run([sys.executable, "/daodan/map/scripts/snapshot.py", "write", str(target), "--out", str(manifest),
          "--no-engine", "--no-index"])
    sys.path.insert(0, "/daodan/map/scripts")
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
    out = Path("/results") / tag / f"brief-{name}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    volume.commit()
    return result


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
