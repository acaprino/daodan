"""The links of phazly and what they close, on Modal, for one tree of Daodan's code: run it for two trees (before and
after a change) on the same recorded input and compare with `check_store_keys.py`.

Shape of `benchmarks/system-map/modal_map.py::possible_case` (same image recipe, same volume, same `possible.measure`),
and it returns what a comparison needs: the links themselves (gzipped), the counts of `summarize.py`, and `possible.measure`
with and without the possible links. The input is a run of the whole pipeline kept on the volume `daodan-flow-results`: its
snapshot folder (`--snapshot`) and the project's source folder (`--source`). The reference (`--expected`, the system map
the owner keeps privately) is read here at run time and is not copied anywhere. The pre-map's recorded record is the
input: a code newer than the one that wrote it calls it stale, and deriving it again takes the container, which drops what
Noir found; `premap.ensure` is held to the record, so two trees are compared on the same one.

    MEASURE_CODE=<folder of the tree to measure> python -m modal run benchmarks/phazly-flow/measure_links.py \\
        --label after --snapshot DIR --source DIR --rules full=benchmarks/phazly-flow/rules.json \\
        --expected REFERENCE.json --out OUT-DIR

`MEASURE_CODE` is the `daodan` folder of the tree (default: this checkout's). Nothing is written to the repository.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import os
import sys
from pathlib import Path

import modal

LOCAL = modal.is_local()
ROOT = Path(__file__).resolve().parents[2] if LOCAL else Path("/daodan")
CODE = Path(os.environ.get("MEASURE_CODE") or ROOT / "daodan") if LOCAL else Path("/daodan/daodan")
SCRIPTS = "/daodan/daodan/core"
SKIP = ["**/__pycache__/**", "**/node_modules/**", "**/tests/**"]

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
    .add_local_file(ROOT / "benchmarks/phazly-flow/summarize.py", "/daodan/benchmarks/phazly-flow/summarize.py")
)
app = modal.App("measure-phazly-links", image=image)
volume = modal.Volume.from_name("daodan-flow-results", create_if_missing=False)


def _count(items):
    out = {}
    for item in items:
        out[item] = out.get(item, 0) + 1
    return out


def _gap_class(reason: str) -> str:
    """The cause of a gap without the place it names: a route's, a declared route's, or the text before its first colon."""
    if reason.startswith("route "):
        return "route: " + ("several handlers" if reason.endswith("several handlers") else "no handler")
    if reason.startswith("declared route "):
        return "declared route: " + reason.partition(": ")[2][:100]
    return reason.split(":")[0][:90]


def _adapters(engine_pass) -> dict:
    out = {}
    for name in ("python", "typescript", "rust"):
        try:
            out[name] = engine_pass.adapter_fingerprint(name)[:12]
        except Exception as error:  # noqa: BLE001 - a name the engine does not know is only not reported
            out[name] = repr(error)[:80]
    return out


@app.function(cpu=4, memory=65536, timeout=3 * 3600, volumes={"/results": volume})
def measure_case(label: str, snapshot: str, source: str, rules: dict, expected: str) -> dict:
    import shutil
    import time
    work = Path("/work/m")
    shutil.copytree(Path("/results") / snapshot, work)  # the links' cache is written beside the manifest
    manifest = work / "manifest.sqlite"
    sys.path[:0] = [SCRIPTS, "/daodan/benchmarks/system-map", "/daodan/benchmarks/phazly-flow"]
    import flows
    import possible
    import summarize
    from snapshot_store import open_snapshot
    with open_snapshot(manifest) as store:
        shutil.copytree(Path("/results") / source, store["root"])  # the links read the arguments of a call from the files
    import premap
    record_file = premap.path(manifest)
    recorded = json.loads(record_file.read_text(encoding="utf-8"))
    sha = lambda: hashlib.sha256(record_file.read_bytes()).hexdigest()[:12]  # noqa: E731
    held = {"state": premap.state(manifest), "sha": sha(), "noir_entries": len(recorded.get("noir_entries", []))}
    premap.ensure = lambda *args, **kwargs: recorded
    import technologies
    technologies.ensure(manifest)
    held["sha_after_ensure"] = sha()
    import edge_view
    import engine_pass
    out = {"label": label,
           "provenance": {"flows_sha256": hashlib.sha256(Path(flows.__file__).read_bytes()).hexdigest()[:16],
                          "adapters": _adapters(engine_pass)},
           "premap": held, "runs": {}}
    expected = json.loads(expected)
    import http_wrappers
    cases = []
    for name, text in rules.items():  # each rules file as it is, then with the `rotta` rules the wrapper proof proposes
        own = flows.validate_rules(json.loads(text)["rules"])
        proposed = http_wrappers.wrappers(manifest, own)
        out.setdefault("wrappers", {})[name] = proposed
        cases += [(name, own), (f"{name}+wrappers", flows.validate_rules(own + [c["rule"] for c in proposed["candidates"]]))]
    for name, own in cases:
        started = time.time()
        links = flows.link_facts(manifest, own)
        seconds = round(time.time() - started)
        view = edge_view.load_edge_view(manifest)
        measured = {}
        for generators in ((), ("ritorno", "incerto")):
            m = possible.measure(manifest, links, expected, generators)
            measured["+".join(generators) or "certo"] = {
                "arrows": m["arrows"], "entries_from_others": m["entries_from_others"], "possible": m["possible"],
                "reader_routes_apart": m["reader_routes_apart"],
                "verified_before": sum(1 for f in m["flows"] if f["reachability"][0] == "verified"),
                "verified_after": sum(1 for f in m["flows"] if f["reachability"][1] == "verified"),
                "flows": [{"name": f["name"], "reach": f["reachability"]} for f in m["flows"]]}
        out["runs"][name] = {
            "seconds": seconds, "routes": links["routes"],
            "edges": _count(f"{e['type']}|{e['origin']}" for e in links["edges"]),
            "gaps_total": len(links["gaps"]),
            "gap_classes": sorted(_count(_gap_class(g["reason"]) for g in links["gaps"]).items(), key=lambda i: -i[1])[:80],
            "engine": {"coverage": view["coverage"].get("status"), "references": len(view["references"]),
                       "profile_engine": view["profile"].get("engine")},
            "non_route_edges_digest": hashlib.sha256(json.dumps(sorted(
                [e["from"], e["to"], e["type"], e["site"], e["origin"]] for e in links["edges"] if not e.get("route"))
            ).encode()).hexdigest()[:16],
            "summary": summarize.summarize(links), "possible": measured,
            "links_gz": gzip.compress(json.dumps(links, sort_keys=True).encode("utf-8"), 6)}
    return out


@app.local_entrypoint()
def main(label: str, snapshot: str, source: str, rules: str, expected: str, out: str):
    """`rules` is `NAME=PATH[,NAME=PATH]`: one run of the links for each rules file."""
    named = {}
    for item in rules.split(","):
        name, _, path = item.partition("=")
        named[name] = Path(path).read_text(encoding="utf-8")
    value = measure_case.remote(label, snapshot, source, named, Path(expected).read_text(encoding="utf-8"))
    target = Path(out)
    target.mkdir(parents=True, exist_ok=True)
    for name, run in value["runs"].items():
        (target / f"{label}-{name}-links.json.gz").write_bytes(run.pop("links_gz"))
    (target / f"{label}.json").write_text(json.dumps(value, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    for name, run in value["runs"].items():
        print(label, name, run["routes"], run["gaps_total"], run["summary"]["flows"],
              {k: v["verified_after"] for k, v in run["possible"].items()})
