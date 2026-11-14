"""Dynamic step on Modal, Python: python-semver's pytest suite under dynamic_record.py, joined to the index graph.

    modal deploy benchmarks/call-provenance/modal_dynamic_python.py
    python benchmarks/call-provenance/modal_dynamic_python.py spawn --tag <name>
    python benchmarks/call-provenance/modal_dynamic_python.py fetch --tag <name>
    python benchmarks/call-provenance/modal_dynamic_python.py report

Preparation is the image, network open: the checkout that benchmarks/inference-audit/lang_python.py stored on the
volume daodan-flow-results (inference-audit/graph-python/semver/work.tar.gz, the pinned commit without .git) and a
venv with the dependencies the project declares, constrained to the versions of the index run (engine.json).
The run is a function with block_network=True: the Modal container is the isolation. It runs the suite as the
project configures it (`.pytest.ini`, coverage included) once to warm the caches, then alternately without and
with the recorder, also with --no-cov. The first recorder run is joined, reference by reference, to the snapshot's
references and the index graph's answers stored on the volume (inference-audit/strong-python/semver.json: one row
per reference of the snapshot in graph-python/semver, with the index's ends and Jedi's targets), and its holes are
checked against the stored graph (inference-audit/graph-python-semver.json). Everything lands on the volume under
dynamic/python-<tag>/; `fetch` copies the join to results/dynamic-python-semver.json.
"""
from __future__ import annotations

import collections
import json
import re
import sys
import time
from pathlib import Path

import modal

HERE = Path(__file__).resolve().parent
LOCAL = modal.is_local()
RESULTS = HERE / "results"
STORE = "inference-audit/graph-python/semver"
ROWS = "inference-audit/strong-python/semver.json"
GRAPH = "inference-audit/graph-python-semver.json"
WORK = Path("/work/src")

# The 16 calls no static source gives a project target (benchmarks/inference-audit/README.md, Python):
# file, line, name token ("" for a computed callee), nth occurrence on the line.
MISSES = [("tests/test_pysemver-cli.py", 41, "createparser", 0)] + \
    [("tests/test_pysemver-cli.py", n, "main", 0) for n in (109, 116, 124, 129, 133, 156)] + \
    [("tests/test_pysemver-cli.py", 104, "func", 0), ("src/semver/_deprecated.py", 81, "func", 0),
     ("src/semver/version.py", 68, "operator", 0), ("tests/test_deprecated_functions.py", 63, "func", 0),
     ("src/semver/cli.py", 152, "func", 0), ("src/semver/version.py", 556, "", 0),
     ("src/semver/version.py", 807, "", 0), ("tests/test_semver.py", 30, "to_dict", 0),
     ("tests/test_semver.py", 36, "to_tuple", 0)]

D, C, V = "src/semver/_deprecated.py", "src/semver/cli.py", "src/semver/version.py"
WRAPPER = f"{D}::deprecated.<locals>.wrapper@49"
CLI = {"cmd_bump": 21, "cmd_check": 49, "cmd_compare": 62, "cmd_nextver": 74, "createparser": 86, "process": 139,
       "main": 155}
OLD = {"compare": 91, "parse": 117, "parse_version_info": 146, "match": 174, "max_ver": 202, "min_ver": 221,
       "format_version": 240, "bump_major": 262, "bump_minor": 280, "bump_patch": 298, "bump_prerelease": 316,
       "bump_build": 335, "finalize_version": 354, "replace": 376}
BUMPS = {"bump_major": 333, "bump_minor": 347, "bump_patch": 361, "bump_prerelease": 375, "bump_build": 426}
COMPARISONS = {"__eq__": 593, "__ne__": 597, "__lt__": 601, "__le__": 605, "__gt__": 609, "__ge__": 613}


def cli(*names):
    return {f"{C}::{name}@{CLI[name]}" for name in names}


# Expected at run time, written from the source before any recorder output existed: (file, line, token, nth,
# kind, callees, the functions those callees wrap or None, extra callees allowed by file prefix).
HAND = [
    ("tests/test_pysemver-cli.py", 41, "createparser", 0, "call", {WRAPPER}, cli("createparser"), None),
    *[("tests/test_pysemver-cli.py", n, "main", 0, "call", {WRAPPER}, cli("main"), None)
      for n in (109, 116, 124, 129, 133, 156)],
    ("tests/test_pysemver-cli.py", 104, "func", 0, "call", {WRAPPER},
     cli("cmd_bump", "cmd_compare", "cmd_check", "cmd_nextver"), None),
    (D, 81, "func", 0, "call", cli(*CLI) | {f"{D}::{name}@{line}" for name, line in OLD.items()}, None,
     "tests/test_deprecated_functions.py::"),
    (V, 68, "operator", 0, "call", {f"{V}::Version.{name}@{line}" for name, line in COMPARISONS.items()}, None, None),
    ("tests/test_deprecated_functions.py", 63, "func", 0, "call", {WRAPPER},
     cli(*CLI) | {f"{D}::{name}@{line}" for name, line in OLD.items() if name != "compare"}, None),
    (C, 152, "func", 0, "call", cli("cmd_bump", "cmd_check", "cmd_compare") | {WRAPPER}, None, None),
    (V, 556, "", 0, "call", {f"{V}::Version.{name}@{BUMPS[name]}" for name in ("bump_major", "bump_minor",
                                                                              "bump_patch")}, None, None),
    (V, 807, "", 0, "call", {f"{V}::Version@78"}, None, None),
    ("tests/test_semver.py", 30, "to_dict", 0, "call", {f"{V}::Version.to_dict@272"}, None, None),
    ("tests/test_semver.py", 36, "to_tuple", 0, "call", {f"{V}::Version.to_tuple@257"}, None, None),
    # Four more: getattr on a bound method, type(self) inside a wrapper, a property on a fixture, a C function.
    (C, 46, "func", 0, "call", {f"{V}::Version.{name}@{line}" for name, line in BUMPS.items()}, None, None),
    (V, 65, "cls", 0, "call", {f"{V}::Version@78"}, None, None),
    ("tests/test_semver.py", 43, "major", 0, "read", {f"{V}::Version.major@213"}, None, None),
    ("tests/test_compare_invalid_operands.py", 52, "lt", 0, "call", {"runtime:_operator.lt"}, None, None),
]


def prepare():
    """Image step, network open: the stored checkout and the venv of the declared dependencies."""
    import subprocess
    import tarfile
    store = Path("/results") / STORE
    with tarfile.open(store / "work.tar.gz") as tar:
        members = [m for m in tar.getmembers() if m.name == "src" or m.name.startswith("src/")]
        tar.extractall("/work", members=members, filter="tar")
    engine = json.loads((store / "engine.json").read_text(encoding="utf-8"))
    pins = Path("/work/constraints.txt")
    pins.write_text("".join(f"{name}=={version}\n" for name, version in engine["environment"].items()))
    subprocess.run(["uv", "venv", "--python", sys.executable, "/venv"], check=True, capture_output=True)
    started = time.time()
    install = ["uv", "pip", "install", "--python", "/venv/bin/python", "--compile-bytecode"]
    done = subprocess.run([*install, "-c", str(pins), *engine["requirements"]], capture_output=True, text=True)
    attempts = [{"constrained": True, "returncode": done.returncode, "stderr_tail": done.stderr[-800:]}]
    if done.returncode:
        done = subprocess.run([*install, *engine["requirements"]], capture_output=True, text=True)
        attempts.append({"constrained": False, "returncode": done.returncode, "stderr_tail": done.stderr[-800:]})
    listed = subprocess.run(["uv", "pip", "list", "--python", "/venv/bin/python", "--format", "json"],
                            capture_output=True, text=True)
    installed = {row["name"]: row["version"] for row in json.loads(listed.stdout or "[]")}
    before = engine["environment"]
    Path("/work/prepare.json").write_text(json.dumps({
        "seconds": round(time.time() - started, 1), "attempts": attempts, "packages": len(installed),
        "python": sys.version.split()[0], "requirements": engine["requirements"],
        "only_now": sorted(set(installed) - set(before)),
        "other_version": {k: [before[k], v] for k, v in installed.items() if k in before and before[k] != v}},
        indent=1))


volume = modal.Volume.from_name("daodan-flow-results", create_if_missing=True)
image = (
    modal.Image.debian_slim(python_version="3.13")
    .pip_install("uv==0.9.5")
    .run_function(prepare, volumes={"/results": volume})
    .add_local_file(HERE / "dynamic_record.py" if LOCAL else Path("/tool/dynamic_record.py"),
                    "/tool/dynamic_record.py")
)
app = modal.App("daodan-dynamic-python", image=image)


def pytest_run(number: int, recorder: bool, cov: bool, work: Path) -> dict:
    """One run of the configured suite in `work`; returns time, peak memory and the junit counts."""
    import os
    import subprocess
    import xml.etree.ElementTree as ElementTree
    out = work / "out"
    junit = out / f"junit-{number}.xml"
    env = {"PATH": "/venv/bin:/usr/local/bin:/usr/bin:/bin", "HOME": "/tmp/home", "LANG": "C.UTF-8"}
    if recorder:
        env.update(PYTHONPATH=str(work / "site"), DYN_ROOT=str(work / "src"),
                   DYN_OUT=str(out / f"observed-{number}-%p.json"))
    command = ["/venv/bin/python", "-m", "pytest", f"--junitxml={junit}"] + ([] if cov else ["--no-cov"])
    started = time.perf_counter()
    with open(out / f"pytest-{number}.log", "w", encoding="utf-8") as log:
        child = subprocess.Popen(command, cwd=work / "src", env=env, stdout=log, stderr=subprocess.STDOUT)
        _pid, status, usage = os.wait4(child.pid, 0)
    seconds = time.perf_counter() - started
    result = {"number": number, "recorder": recorder, "cov": cov, "seconds": round(seconds, 2),
              "returncode": os.waitstatus_to_exitcode(status), "peak_mb": round(usage.ru_maxrss / 1024)}
    if junit.is_file():
        root = ElementTree.parse(junit).getroot()
        suite = root if root.tag == "testsuite" else root.find("testsuite")
        result.update({key: int(suite.get(key, 0)) for key in ("tests", "failures", "errors", "skipped")})
        result["not_passed"] = sorted(f"{case.get('classname')}::{case.get('name')}:{child.tag}"
                                      for case in suite.iter("testcase") for child in case
                                      if child.tag in ("failure", "error", "skipped"))
    result["observed_files"] = sorted(p.name for p in out.glob(f"observed-{number}-*.json"))
    return result


def network_closed() -> dict:
    import socket
    try:
        socket.create_connection(("1.1.1.1", 443), timeout=3).close()
        return {"closed": False}
    except OSError as error:
        return {"closed": True, "error": f"{type(error).__name__}: {error}"}


@app.function(cpu=2, memory=4096, timeout=1800, block_network=True, volumes={"/results": volume})
def run(tag: str, repeats: int = 3) -> dict:
    import shutil
    import statistics
    import subprocess
    work = Path("/tmp/run")
    shutil.rmtree(work, ignore_errors=True)
    shutil.copytree(WORK, work / "src", symlinks=True)
    (work / "out").mkdir(parents=True)
    Path("/tmp/home").mkdir(exist_ok=True)
    subprocess.run([sys.executable, "-I", "/tool/dynamic_record.py", "site", str(work / "site")], check=True)
    plan = [(False, True)] + [(recorder, True) for _ in range(repeats) for recorder in (False, True)] + \
        [(recorder, False) for _ in range(2) for recorder in (False, True)]
    runs = [pytest_run(number, recorder, cov, work) for number, (recorder, cov) in enumerate(plan)]
    timing = {}
    for cov in (True, False):
        for recorder in (False, True):
            chosen = [r["seconds"] for r in runs[1:] if r["recorder"] == recorder and r["cov"] == cov]
            timing[f"{'cov' if cov else 'nocov'}-{'recorder' if recorder else 'plain'}"] = {
                "median": statistics.median(chosen), "all": chosen}
    first = next(r for r in runs if r["recorder"])
    observed = [json.loads((work / "out" / name).read_text(encoding="utf-8")) for name in first["observed_files"]]
    signature = {}
    for r in runs:
        if r["recorder"]:
            sites = set()
            for name in r["observed_files"]:
                for site in json.loads((work / "out" / name).read_text(encoding="utf-8"))["sites"]:
                    sites.add((site["file"], site["line"], site["column"], site["name"], site["role"],
                               json.dumps(site["callees"], sort_keys=True)))
            signature[r["number"]] = sites
    base = signature[first["number"]]
    same = {number: {"only_here": len(s - base), "only_first": len(base - s)} for number, s in signature.items()}
    rows = json.loads((Path("/results") / ROWS).read_text(encoding="utf-8"))["rows"]
    holes = json.loads((Path("/results") / GRAPH).read_text(encoding="utf-8"))["holes"]
    result = join(rows, holes, [site for data in observed for site in data["sites"]], work / "src")
    result.update({"runs": runs, "timing": timing, "same_sites_across_recorder_runs": same,
                   "network": network_closed(), "prepare": json.loads(Path("/work/prepare.json").read_text()),
                   "recorder_stats": [data["stats"] for data in observed]})
    kept = Path("/results/dynamic") / f"python-{tag}"
    kept.mkdir(parents=True, exist_ok=True)
    for item in (work / "out").iterdir():
        shutil.copyfile(item, kept / item.name)
    (kept / "join.json").write_text(json.dumps(result, ensure_ascii=False) + "\n", encoding="utf-8")
    volume.commit()
    return {"tag": tag, "timing": timing, "runs": [{k: r.get(k) for k in ("number", "recorder", "cov", "seconds",
                                                                          "tests", "failures", "errors", "skipped")}
                                                   for r in runs], "summary": result["summary"]}


# --- join ----------------------------------------------------------------------------------------------------

def name_of(callee: dict) -> str:
    """A callee as the hand check writes it: file::qualname@def line, or kind:module.name."""
    if callee["kind"] == "project":
        return f"{callee['file']}::{callee['name']}@{callee['line'] + 1}"
    return f"{callee['kind']}:{callee['module']}.{callee['name']}"


def target(callee: dict) -> str:
    """A project callee in the notation of the index rows: file::function@line:column or file::class@line:column."""
    return f"{callee['file']}::{'class' if callee['type'] == 'class' else 'function'}@{callee['line'] + 1}:" \
           f"{callee['column']}"


def package(callee: dict) -> str:
    if callee["kind"] == "runtime":
        return "python-stdlib"
    return (callee.get("package") or callee.get("module") or "").lower().replace("_", "-")


def grade(project: set, external: set, callees: list) -> str:
    """The observed callees against one static answer (project targets, external packages)."""
    if callees and all(c.get("mock") for c in callees):
        return "mock"
    callees = [c for c in callees if not c.get("mock")]
    # A wrapper made by a decorator, in the project or not, stands for the project function it wraps.
    wrapped = [c for c in callees if (c.get("wraps") or {}).get("kind") == "project"]
    own = {target(c) for c in callees if c["kind"] == "project"} | {target(c["wraps"]) for c in wrapped}
    outside = {package(c) for c in callees if c["kind"] != "project" and c not in wrapped}
    if project:
        reached = [c for c in callees if (c["kind"] == "project" and target(c) in project)
                   or (c in wrapped and target(c["wraps"]) in project)]
        if not reached:
            return "contradiction"
        return "agree" if len(reached) == len(callees) else "agree-wider"
    if external:
        if own:
            return "contradiction"
        return "agree-external" if outside & external else "external-other-package"
    return "gain-project" if own else "gain-external" if outside else "none"


def join(rows: list, holes: list, sites: list, source: Path) -> dict:
    lines_of = {}

    def text(rel: str) -> list:
        if rel not in lines_of:
            path = source / rel
            lines_of[rel] = path.read_text(encoding="utf-8").split("\n") if path.is_file() else []
        return lines_of[rel]

    def char_column(rel: str, line: int, column: int) -> int:
        line_text = text(rel)[line] if line < len(text(rel)) else ""
        return len(line_text.encode("utf-8")[:column].decode("utf-8", errors="ignore"))

    at = collections.defaultdict(list)
    computed = collections.defaultdict(list)
    for site in sites:
        at[(site["file"], site["line"] + 1, char_column(site["file"], site["line"], site["column"]))].append(site)
        if site["name"] == "" and site["role"] == "call":
            computed[(site["file"], site["line"] + 1)].append(site)

    def index_side(row):
        scip = row["scip"]
        return set(scip.get("project") or []), {e.split(" ", 1)[-1].split("@")[0] for e in scip.get("external") or []}

    def jedi_side(row):
        """Jedi's project targets and the packages of its external functions and classes; an `instance` answer
        is the type of a value (int, Callable, partial), not a target."""
        jedi = row.get("jedi") or {}
        external = {t[0].split("::")[0] for t in jedi.get("targets") or [] if t[1] is None and t[2] != "instance"}
        return set(jedi.get("project") or []), external

    joined, used = [], set()
    for row in rows:
        parts = row["site"].split(":")
        rel, line = parts[0], int(parts[1])
        if len(parts) == 2:
            found = computed.get((rel, line), [])
        else:
            # Same name token: a computed callee starts where its inner call's name does.
            found = [s for s in at.get((rel, line, int(parts[2])), []) if s["name"] == row["name"].split(".")[-1]
                     and (row["kind"] == "read" or s["role"] == "call")]
        for site in found:
            used.add(id(site))
        callees = [c for site in found for c in site["callees"]]
        unique = {json.dumps(c, sort_keys=True): c for c in callees}
        callees = list(unique.values())
        project, external = index_side(row)
        j_project, j_external = jedi_side(row)
        joined.append({
            "site": row["site"], "name": row["name"], "kind": row["kind"], "hole": row["scip"].get("hole") or "",
            "index": sorted(project) or sorted(external) or row["scip"].get("value") or row["scip"].get("dead") or [],
            "jedi": sorted(j_project), "roles": sorted({s["role"] for s in found}),
            "observed": sorted({name_of(c) for c in callees}),
            "observed_wraps": sorted({name_of(c["wraps"]) for c in callees if c.get("wraps")}),
            "observed_targets": sorted({target(c) for c in callees if c["kind"] == "project"}),
            "index_not_observed": sorted(project - {target(c) for c in callees if c["kind"] == "project"} - {
                target(c["wraps"]) for c in callees if (c.get("wraps") or {}).get("kind") == "project"})
            if found else [],
            "verdict": grade(project, external, callees) if found else "not-executed",
            "verdict_jedi": grade(j_project, j_external, callees) if found else "not-executed",
            "callees": callees})
    by_site = {}
    for entry in joined:
        by_site.setdefault((entry["site"], entry["kind"]), entry)

    def locate(rel, line, token, nth, kind="call"):
        if not token:
            return by_site.get((f"{rel}:{line}", kind))
        line_text = text(rel)[line - 1] if line - 1 < len(text(rel)) else ""
        found = [m.start() for m in re.finditer(rf"(?<![A-Za-z0-9_]){re.escape(token)}(?![A-Za-z0-9_])", line_text)]
        return by_site.get((f"{rel}:{line}:{found[nth]}", kind)) if len(found) > nth else None

    misses = []
    for rel, line, token, nth in MISSES:
        entry = locate(rel, line, token, nth)
        misses.append({"site": f"{rel}:{line} {token or '(computed callee)'}", "row": entry and entry["site"],
                       "observed": entry and entry["observed"], "wraps": entry and entry["observed_wraps"],
                       "verdict": entry and entry["verdict"]})
    hand = []
    for rel, line, token, nth, kind, expected, wraps, extra in HAND:
        entry = locate(rel, line, token, nth, kind)
        seen = set(entry["observed"]) if entry else set()
        seen_wraps = set(entry["observed_wraps"]) if entry else set()
        rest = seen - expected
        exact = bool(seen) and expected <= seen and all(extra and name.startswith(extra) for name in rest) \
            if rest else seen == expected
        if exact and wraps is not None:
            exact = seen_wraps == wraps
        score = "right" if exact else "partial" if seen & expected else "wrong" if seen else "not-observed"
        hand.append({"site": f"{rel}:{line} {token or '(computed callee)'}", "expected": sorted(expected),
                     "expected_wraps": sorted(wraps) if wraps is not None else None, "observed": sorted(seen),
                     "observed_wraps": sorted(seen_wraps), "score": score})

    graph_holes = collections.Counter((h["site"], h["name"]) for h in holes)
    row_holes = collections.Counter((":".join(e["site"].split(":")[:2]), e["name"]) for e in joined if e["hole"])
    calls = [e for e in joined if e["kind"] == "call"]
    def area(site: str) -> str:
        return "tests" if site.startswith("tests/") else "src" if site.startswith("src/") else "docs"

    executed = collections.Counter((area(e["site"]), e["verdict"] != "not-executed") for e in calls)
    unmatched = [s for s in sites if id(s) not in used]
    polymorphic = sorted(({"site": f"{s['file']}:{s['line'] + 1}:{s['column']} {s['name']}", "role": s["role"],
                           "callees": [name_of(c) for c in s["callees"]]}
                          for s in sites if len({name_of(c) for c in s["callees"]}) > 1),
                         key=lambda item: -len(item["callees"]))
    wrapped_many = [{"site": f"{s['file']}:{s['line'] + 1} {s['name']}",
                     "wraps": sorted({name_of(c['wraps']) for c in s['callees'] if c.get('wraps')})}
                    for s in sites if len({name_of(c['wraps']) for c in s['callees'] if c.get('wraps')}) > 1]
    slots = [e for e in joined if e["kind"] == "read" and re.fullmatch(r"\w+\._(major|minor|patch|prerelease|build)",
                                                                      e["name"]) and any("class@78" in t for t in
                                                                                         e["index"])]
    wrong = {
        "slots": {"rows": len(slots), "executed_with_callee": sum(1 for e in slots if e["observed"]),
                  "observed": sorted({o for e in slots for o in e["observed"]})},
        "operator": [{k: e[k] for k in ("site", "name", "kind", "index", "observed", "roles")} for e in joined
                     if e["site"].startswith(("tests/test_compare_invalid_operands.py:52:",
                                              "tests/test_compare_invalid_operands.py:67:"))],
        "pytest_outcomes": [{k: e[k] for k in ("site", "name", "kind", "index", "observed", "verdict")} for e in joined
                            if e["name"] in ("pytest.skip", "pytest.fail")]}
    contradictions = [{k: e[k] for k in ("site", "name", "kind", "index", "jedi", "observed", "observed_wraps",
                                         "observed_targets", "verdict", "verdict_jedi")}
                      for e in joined if "contradiction" in (e["verdict"], e["verdict_jedi"])]
    counts = collections.Counter(f"{e['kind']} {e['verdict']}" for e in joined)
    counts_jedi = collections.Counter(f"{e['kind']} {e['verdict_jedi']}" for e in joined)
    hole_rows = [{k: e[k] for k in ("site", "name", "kind", "hole", "roles", "observed", "verdict")}
                 for e in joined if e["hole"]]
    summary = {
        "references": len(joined), "calls": len(calls),
        "calls_executed": sum(1 for e in calls if e["verdict"] != "not-executed"),
        "calls_executed_by_area": {f"{a} {'executed' if x else 'not'}": n for (a, x), n in sorted(executed.items())},
        "holes": len(hole_rows), "holes_with_observed_callee": sum(1 for e in hole_rows if e["observed"]),
        "holes_match_graph": graph_holes == row_holes,
        "misses_with_observed_callee": sum(1 for m in misses if m["observed"]),
        "contradictions_index": sum(1 for e in joined if e["verdict"] == "contradiction"),
        "contradictions_jedi": sum(1 for e in joined if e["verdict_jedi"] == "contradiction"),
        "agree_with_index_targets_not_observed": sum(1 for e in joined if e["verdict"] in ("agree", "agree-wider")
                                                     and e["index_not_observed"]),
        "polymorphic_sites": len(polymorphic), "sites_wrapping_several": len(wrapped_many),
        "observed_sites": len(sites), "observed_sites_without_reference": len(unmatched),
        "hand": dict(collections.Counter(h["score"] for h in hand))}
    return {"summary": summary, "counts": dict(sorted(counts.items())), "counts_jedi": dict(sorted(counts_jedi.items())),
            "misses": misses, "hand": hand, "holes": hole_rows, "contradictions": contradictions,
            "polymorphic": polymorphic, "wrapping_several": wrapped_many, "wrong_targets": wrong,
            "calls_not_executed": [{k: e[k] for k in ("site", "name", "hole")} for e in calls
                                   if e["verdict"] == "not-executed"],
            "unmatched_by_role": dict(collections.Counter(s["role"] for s in unmatched)),
            "unmatched_calls": [{k: s[k] for k in ("file", "line", "column", "name", "role", "end")} | {
                "callees": [name_of(c) for c in s["callees"]][:3]} for s in unmatched
                if s["role"] not in ("decorator", "WITH_EXIT") and not s["role"].isupper()],
            "unmatched_examples": [{k: s[k] for k in ("file", "line", "column", "name", "role", "end")} | {
                "callees": [name_of(c) for c in s["callees"]][:3]} for s in unmatched[:40]],
            "rows": [e for e in joined if e["verdict"] != "not-executed" or e["hole"]]}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("spawn", "fetch", "report"))
    parser.add_argument("--tag", default="exact-20261114")
    args = parser.parse_args()
    out = RESULTS / "dynamic-python-semver.json"
    if args.command == "spawn":
        print(modal.Function.from_name("daodan-dynamic-python", "run").spawn(args.tag).object_id)
    elif args.command == "fetch":
        data = b"".join(volume.read_file(f"dynamic/python-{args.tag}/join.json"))
        out.write_bytes(data.replace(b"\r\n", b"\n"))
        print(out, len(data))
    else:
        data = json.loads(out.read_text(encoding="utf-8"))
        print(json.dumps({k: data[k] for k in ("summary", "timing", "network")}, indent=1))
        for r in data["runs"]:
            print(r["number"], r["recorder"], r["cov"], r["seconds"], r.get("tests"), r.get("failures"),
                  r.get("errors"), r.get("skipped"), r["peak_mb"])
