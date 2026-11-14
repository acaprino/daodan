"""Python, a second source: Jedi in batch beside the whole-project index, site by site (README of this folder).

Wiring only: the Jedi adapter (`adapters/python_jedi.py`), the stored index, snapshot and checkout of
`lang_python.py` (volume `daodan-flow-results`, `inference-audit/graph-python/<case>/`) and `scip_graph.py`.
One container: the project's declared dependencies in a venv (the build of `adapters/python.py` `index`), Jedi
over every name of every file in its own process, then each snapshot call and read compared with what the index
graph answers at the same position. No model, no change to the stored graph.

    modal deploy benchmarks/inference-audit/strong_python.py
    python benchmarks/inference-audit/strong_python.py spawn --cases semver
    python benchmarks/inference-audit/strong_python.py fetch --cases semver
    python benchmarks/inference-audit/strong_python.py report --cases semver

Writes `results/strong-python-<case>.json` (rows per snapshot reference, counts, the hand check, the run) and
`results/strong-python-<case>-jedi.json` (the adapter's output). `report` prints the tables of the README from them.
"""
from __future__ import annotations

import collections
import json
import re
import sys
from pathlib import Path

import modal

HERE = Path(__file__).resolve().parent
LOCAL = modal.is_local()
PLUGIN = HERE.parents[1] / "plugins/codebase-map/skills/map" if LOCAL else Path("/daodan/map")
SCRIPTS = str(PLUGIN / "scripts")
RESULTS = HERE / "results"
TAG = "inference-audit"
STORE = f"{TAG}/graph-python"  # per case: engine.json, the index file, run.json, work.tar.gz (lang_python.py)
OUT = f"{TAG}/strong-python"
LANGUAGE = "python"
sys.path.insert(0, str(HERE) if LOCAL else "/audit")
sys.path.insert(0, SCRIPTS)
import plugin_scripts  # noqa: E402
import code_graph as scip_graph  # noqa: E402
from indexers import python as adapter  # noqa: E402

CASES = {"semver": {"target": "."}}


def _image():
    return (
        modal.Image.debian_slim(python_version="3.13")
        .apt_install("git", "ca-certificates")
        .pip_install("uv", "tree-sitter==0.26.0", "tree-sitter-language-pack==1.13.5", "sqlglot>=30", "jedi>=0.19")
        .add_local_dir(PLUGIN, "/daodan/map", ignore=["**/__pycache__/**", "**/tests/**"])
        .add_local_file(HERE / "plugin_scripts.py" if LOCAL else Path("/audit/plugin_scripts.py"),
                        "/audit/plugin_scripts.py")
        .add_local_dir(HERE / "adapters" if LOCAL else Path("/audit/adapters"), "/audit/adapters",
                       ignore=["**/__pycache__/**"])
    )


app = modal.App("daodan-strong-python", image=_image())
volume = modal.Volume.from_name("daodan-flow-results", create_if_missing=True)


# The 19 calls the index leaves without a project function that should have one (README, Python): file, line, name.
MISSES = [("tests/test_pysemver-cli.py", 41, "createparser")] +          [("tests/test_pysemver-cli.py", n, "main") for n in (109, 116, 124, 129, 133, 156)] +          [("tests/test_pysemver-cli.py", 104, "func"), ("src/semver/_deprecated.py", 81, "func"),
          ("src/semver/version.py", 68, "operator"), ("tests/test_deprecated_functions.py", 63, "func"),
          ("src/semver/cli.py", 152, "args.func"), ("src/semver/cli.py", 46, "func"), ("src/semver/version.py", 556, ""),
          ("src/semver/version.py", 65, "cls"), ("src/semver/version.py", 65, "cls"), ("src/semver/version.py", 807, ""),
          ("tests/test_semver.py", 30, "version.to_dict"), ("tests/test_semver.py", 36, "version.to_tuple")]


def report(path: Path) -> None:
    """The counts and sites the README quotes, from a fetched result."""
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = data["rows"]
    print("jedi", data["engine"]["version"], data["engine"]["seconds"], "s", data["engine"]["peak_mb"], "MB",
          data["engine"]["names"], "names", data["engine"]["answered"], "answered")
    for title in ("counts", "counts_product_rule"):
        print(title, json.dumps(data[title]))
    print("jedi sites outside the snapshot's references", json.dumps(data["jedi_sites_outside_snapshot"]))
    print("the 19 misses (file:line name: index | jedi project / other targets)")
    taken = set()
    for rel, line, name in MISSES:
        found = [r for r in rows if r["kind"] == "call" and r["name"] == name and r["site"].split(":")[:2] == [rel, str(line)]
                 and r["site"] not in taken] if name else                 [r for r in rows if r["site"] == f"{rel}:{line}"]
        if not found:
            print(f"  {rel}:{line} {name}: no row")
            continue
        row = found[0]
        taken.add(row["site"])
        other = sorted({f"{t[0].split('::')[-1]} ({t[2]})" for t in row["jedi"].get("targets", [])})
        print(f"  {rel}:{line} {name or '(computed callee)'}: {row['scip'].get('value') or row['scip'].get('hole')} | "
              f"{row['jedi'].get('project') or '-'} / {other[:3] or row['jedi'].get('state')}")
    print("hand check")
    for item in data["hand_check"]:
        row = item["row"]
        print(f"  {item['site']}: index {row['scip']['symbols'] or row['scip']['external'] or row['scip']['value'] or row['scip']['hole']} | "
              f"jedi {[t[0].split('::')[-1] for t in item['jedi']['targets']]}" if row else f"  {item['site']}: no row")


def short(key: str) -> str:
    return key.split("`/")[-1] if "`/" in key else key.split(" ", 4)[-1]


def environment(work: Path, engine: dict) -> dict:
    """The venv `adapters/python.py` `index` builds: the declared requirements in one installer call, then one
    per package when that fails. Returns what is installed and how it differs from the index run's."""
    import subprocess
    import sys as _sys
    venv = work / "venv"
    subprocess.run(["uv", "venv", "--seed", "--python", _sys.executable, str(venv)], check=True, capture_output=True)
    python = str(venv / "bin/python")
    wanted, installs = engine["requirements"], []
    done = subprocess.run(["uv", "pip", "install", "--python", python, *wanted], capture_output=True, text=True)
    installs.append({"packages": "all", "returncode": done.returncode, "stderr_tail": done.stderr[-600:]})
    if done.returncode:
        for package in wanted:
            one = subprocess.run(["uv", "pip", "install", "--python", python, package], capture_output=True, text=True)
            installs.append({"packages": package, "returncode": one.returncode})
    listed = subprocess.run([python, "-m", "pip", "list", "--format=json"], capture_output=True, text=True)
    installed = {row["name"]: row["version"] for row in json.loads(listed.stdout or "[]")}
    before = engine.get("environment") or {}
    return {"venv": str(venv), "installs": installs, "packages": len(installed),
            "only_now": sorted(set(installed) - set(before)), "only_before": sorted(set(before) - set(installed)),
            "other_version": {k: [before[k], installed[k]] for k in installed if k in before and before[k] != installed[k]}}


def product_rule(edges: list) -> list:
    """What the product's `JediEngine.definitions` keeps at a name: the `goto` results that replaced a value that
    is neither a function nor a class, else the inferred values."""
    return [e for e in edges if e["product"]] or [e for e in edges if e["via"] == "infer"]


def _verdict(scip: dict, jedi: dict) -> str:
    if scip["project"]:
        if not jedi["targets"]:
            return "jedi-silent"
        if set(jedi["project"]) == set(scip["project"]):
            return "agree"
        if set(jedi["project"]) & set(scip["project"]):
            return "overlap"
        return "disagree-project" if jedi["project"] else "jedi-no-project-target"
    return "index-no-project/jedi-project" if jedi["project"] else ("both-silent" if not jedi["targets"]
                                                                    else "index-no-project/jedi-other")


def compare(work: Path, engine: dict, jedi_output: dict, hand: list, name: str) -> dict:
    source = work / "snapshot-src" / CASES[name]["target"]
    index = scip_graph.Index(source)
    for path, prefix in engine["indexes"]:
        index.load(work / Path(path).name, prefix)
    hops = adapter.hops(index)
    at = collections.defaultdict(list)
    for edge in jedi_output["edges"]:
        rel, line, column = edge["site"].rsplit(":", 2)
        at[(rel, int(line), int(column))].append(edge)
    named = {tuple(item.rsplit(":", 2)) for item in jedi_output["silent"] + jedi_output["failed"]}
    named = {(rel, int(line), int(column)) for rel, line, column in named} | set(at)
    failed = {tuple(item.rsplit(":", 2)) for item in jedi_output["failed"]}
    failed = {(rel, int(line), int(column)) for rel, line, column in failed}
    with scip_graph.Snapshot(work / "snapshot" / "manifest.sqlite") as snapshot:
        traversal = scip_graph.Traversal(index, snapshot, hops)
        sites = adapter.static(index)
        _graph, references = scip_graph.build(index, snapshot, LANGUAGE, hops, engine["indexer"], None, traversal,
                                              static=sites)

        def jedi_side(edges: list) -> dict:
            project, targets, value, external = [], [], [], []
            for edge in edges:
                targets.append([edge["callee"], edge["at"], edge["type"], edge["kind"]])
                if edge["external"]:
                    external.append(edge["external"]["package"])
                    continue
                if edge["type"] in ("function", "class", "property") and edge["at"]:
                    rel, line, column = edge["at"].rsplit(":", 2)
                    text = index.line(rel, int(line)) or ""
                    verdict, target = snapshot.grade(snapshot.rel.get(rel, rel), int(line),
                                                     len(text[:int(column)].encode("utf-8")))
                    if verdict == "callable":
                        project.append(target)
                        continue
                    value.append(f"{edge['type']} {edge['at']} ({verdict})")
                else:
                    value.append(f"{edge['type']} {edge['at']}")
            return {"project": sorted(set(project)), "value": value, "external": sorted(set(external)),
                    "targets": targets}

        rows, used = [], set()
        for identity, rel, kind, _resolution, _lexical, span, parts, _reason in snapshot.references(LANGUAGE):
            reference = references.get(identity)
            checkout = snapshot.checkout.get(rel, rel)
            found = snapshot.callee(rel, span, parts)
            if reference is None or found is None:
                rows.append({"site": f"{checkout}:{span[2]}", "name": ".".join(parts), "kind": kind,
                             "scip": {"project": [], "hole": "no-position"}, "jedi": {"state": "no-position"},
                             "verdict": "no-position"})
                continue
            line, byte = found
            text = index.line(checkout, line) or ""
            column = len(text.encode("utf-8")[:byte].decode("utf-8", errors="ignore"))
            ends = reference["ends"]
            scip = {"project": sorted({end.target for end in ends if end.cls == "project-callable" and end.target}),
                    "symbols": sorted({short(end.key) for end in ends if end.cls == "project-callable"}),
                    "value": sorted({end.detail for end in ends if end.cls == "project-value"}),
                    "external": sorted({end.detail for end in ends if end.cls == "external"}),
                    "dead": sorted({end.detail for end in ends if end.cls == "dead-end"}),
                    "hops": sorted({hop for end in ends for hop in end.chain}), "hole": reference["hole"]}
            key = (checkout, line, column)
            used.add(key)
            jedi = jedi_side(at.get(key, []))
            product = jedi_side(product_rule(at.get(key, [])))
            jedi["state"] = ("answered" if key in at else "failed" if key in failed
                             else "silent" if key in named else "no-name")
            rows.append({"site": f"{checkout}:{line}:{column}", "name": ".".join(parts), "kind": kind,
                         "text": text.strip()[:150], "scip": scip, "jedi": jedi, "verdict": _verdict(scip, jedi),
                         "product": {"project": product["project"], "targets": product["targets"]},
                         "verdict_product": _verdict(scip, product)})
        counts = collections.Counter((row["kind"], row["verdict"]) for row in rows)
        counts_product = collections.Counter((row["kind"], row.get("verdict_product")) for row in rows)
        by_state = collections.Counter((row["kind"], row["jedi"].get("state")) for row in rows)
        extra = [(key, edges) for key, edges in at.items() if key not in used]
        outside = collections.Counter()
        for key, edges in extra:
            side = jedi_side(edges)
            outside["project-callable" if side["project"] else "external" if side["external"] else "value"] += 1
        row_at = {tuple(row["site"].rsplit(":", 2)): row for row in rows if row["verdict"] != "no-position"}
        checked = []
        for rel, line, word, nth, expected in hand:
            text = index.line(rel, line) or ""
            positions = [m.start() for m in re.finditer(rf"(?<![A-Za-z0-9_]){re.escape(word)}(?![A-Za-z0-9_])", text)]
            column = positions[nth] if len(positions) > nth else None
            row = row_at.get((rel, str(line), str(column)))
            checked.append({"site": f"{rel}:{line} {word}", "expected": expected, "row": row,
                            "jedi": jedi_side(at.get((rel, line, column), [])) if column is not None else None})
    return {"rows": rows, "counts": {f"{kind} {verdict}": n for (kind, verdict), n in sorted(counts.items())},
            "counts_product_rule": {f"{kind} {verdict}": n for (kind, verdict), n in sorted(counts_product.items(),
                                                                                           key=str)},
            "jedi_state": {f"{kind} {state}": n for (kind, state), n in sorted(by_state.items(), key=str)},
            "jedi_sites_outside_snapshot": {"sites": len(extra), "by_answer": dict(outside)},
            "hand_check": checked}


@app.function(cpu=2, memory=6144, timeout=1800, volumes={"/results": volume})
def strong_case(name: str, hand: list, reuse: bool = False) -> dict:
    """`reuse`: compare again the Jedi output stored by a previous call, without the venv and the Jedi run."""
    import shutil
    import tarfile
    store = Path("/results") / STORE / name
    work = Path("/work") / name
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    with tarfile.open(store / "work.tar.gz") as tar:
        tar.extractall(work, filter="tar")
    for item in store.iterdir():
        if item.is_file() and item.name != "work.tar.gz":
            shutil.copyfile(item, work / item.name)
    print("code", plugin_scripts.code_sha256(), flush=True)
    engine = json.loads((work / "engine.json").read_text(encoding="utf-8"))
    folder = Path("/results") / OUT
    if reuse:
        before = json.loads((folder / f"{name}.json").read_text(encoding="utf-8"))
        jedi_output = json.loads((folder / f"{name}-jedi.json").read_text(encoding="utf-8"))
        built, run = before["environment"], before["run"]
    else:
        built = environment(work, engine)
        project = work / "snapshot-src" / CASES[name]["target"]
        output = work / "jedi.json"
        run = scip_graph.measured([sys.executable, "-I", "/audit/adapters/python_jedi.py", str(project),
                                   str(work / "jedi-work"), built["venv"], str(output)], str(work), None, 1500)
        if run["returncode"] != 0 or not output.is_file():
            return {"case": name, "error": "jedi run", "run": run, "environment": built}
        jedi_output = json.loads(output.read_text(encoding="utf-8"))
    result = compare(work, engine, jedi_output, hand if name == "semver" else [], name)
    result.update({"case": name, "engine": jedi_output["engine"], "run": {k: run[k] for k in ("seconds", "peak_mb")},
                   "environment": built, "code": plugin_scripts.code_sha256()})
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{name}.json").write_text(json.dumps(result, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    (folder / f"{name}-jedi.json").write_text(json.dumps(jedi_output, ensure_ascii=False) + "\n", encoding="utf-8",
                                              newline="\n")
    volume.commit()
    return {"case": name, "rows": len(result["rows"]), "counts": result["counts"], "engine": result["engine"],
            "run": result["run"]}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("spawn", "fetch", "report"))
    parser.add_argument("--cases", default="semver")
    parser.add_argument("--reuse", action="store_true", help="with spawn: compare the stored Jedi output again")
    args = parser.parse_args()
    chosen = [c.strip() for c in args.cases.split(",") if c.strip()]
    if args.command == "spawn":
        from lang_python import HAND
        function = modal.Function.from_name("daodan-strong-python", "strong_case")
        for name in chosen:
            print(name, function.spawn(name, [list(item) for item in HAND], args.reuse).object_id)
    elif args.command == "report":
        for name in chosen:
            report(RESULTS / f"strong-python-{name}.json")
    else:
        for name in chosen:
            for suffix, target in (("", ""), ("-jedi", "-jedi")):
                data = b"".join(volume.read_file(f"{OUT}/{name}{suffix}.json"))
                (RESULTS / f"strong-python-{name}{target}.json").write_bytes(data.replace(b"\r\n", b"\n"))
                print(name + suffix, len(data))
