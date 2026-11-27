"""Build tools: what the fork names against what the pre-map's sources find, on the corpus, on Modal (T1.B.1).

For each fixture with `expected.json` of `benchmarks/project-model/fixtures/`, the container does what `modal_stack.py`
does before the `stack` step (its image, its project copy or clone, its replay): the snapshot, then the pre-map written
with the answers `modal_premap.py --runs` recorded for its model commands (`results/premap-runs`, replayed: no command of
the project runs; a fixture without a recording has its model commands `not_run`). Then `stack_recognition.run` twice
on the same snapshot and perimeter: `with` takes the pre-map's facts as they are (the declarations of today), `without`
takes them without `packages`, `services` and `docker_builds` (`DECLARED`, what `stack_recognition.declarations` reads):
the fork as `recognize_stack` would run it before `find_modules` (decision 2 of T1.B). The tool is the image's Node on the
image's release (`modal_stack._image_tool`), and every process started is recorded and judged (`fork_stack.executed`).

The container stores per fixture the unit kinds and workspace tools of the pre-map and, for each variant, the entries
found with the sources and the first signs (`project-model/build-tools/<fixture>.json`); `fetch` reads them, scores them
with the pure functions below (`TOOLS`, `rows`, `lost`, `summary`, tested in `test_build_tools.py`) and writes
`results/build_tools.json`. A change to the table costs no run.

    modal deploy benchmarks/stack-build-tools/modal_build_tools.py
    python benchmarks/stack-build-tools/modal_build_tools.py spawn [--fixtures a,b | --families js,py,...]
    python benchmarks/stack-build-tools/modal_build_tools.py fetch [--fixtures a,b | --families ...]
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

import modal

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1] if modal.is_local() else Path("/repo")  # Modal starts this file as /root/modal_build_tools.py
sys.path.insert(0, str(REPO / "benchmarks/project-model"))
import modal_stack as stack  # noqa: E402  (image, project copy, replay, bounded run)

APP, STORE = "daodan-stack-build-tools", "project-model/build-tools"
OWN = "benchmarks/stack-build-tools/modal_build_tools.py"
DECLARED = ("packages", "services", "docker_builds")  # the pre-map facets `stack_recognition.declarations` sends
HOSTS = "registry_hosts"  # the sign source that is not the fork: a host mention
SIGNS = 5  # signs kept per entry, the fork's own first
# The table of the step: a build tool of `find_modules` -> (registry ids the fork names for it, pre-map unit kinds,
# pre-map workspace tools, pre-map sources that state a unit without a kind of their own). The registry has no entry
# for CMake, Meson, Bazel, Make, autotools, sbt, .NET SDK and Mix: their first field is empty, and what the fork names
# where they are found is in `summary`'s `beside`.
TOOLS = {
    "cargo": (("cargo",), ("cargo-crate",), ("cargo",), ()),
    "gradle": (("gradle",), ("gradle-project",), ("gradle",), ()),
    "maven": (("maven",), ("maven-module",), ("maven",), ()),
    "npm": (("npm", "pnpm", "yarn"), ("npm-package",), ("npm", "pnpm"), ()),
    "tsc": (("typescript",), (), (), ("tsc",)),
    "python": (("uv", "pip", "poetry"), ("python-project",), ("uv",), ()),
    "go": (("golang",), ("go-module",), ("go",), ()),
    "cmake": ((), ("cmake-target",), ("cmake",), ()),
    "meson": ((), ("meson-target",), ("meson",), ()),
    "bazel": ((), ("bazel-module", "bazel-target"), ("bazel",), ()),
    "make": ((), ("make-target",), ("make",), ()),
    "autotools": ((), ("autotools-project",), (), ()),
    "sbt": ((), ("sbt-project",), ("sbt",), ()),
    "dotnet": ((), ("dotnet-project", "msbuild-project"), ("dotnet",), ()),
    "mix": ((), ("mix-project",), ("mix",), ()),
    "nx": (("nxjs",), ("nx-project",), (), ()),
}

app = modal.App(APP, image=stack.image.add_local_file(HERE / "modal_build_tools.py", f"/repo/{OWN}")
                if modal.is_local() else stack.image)


# --- pure: what a stored record says --------------------------------------------------------------------------------

def fork_named(entries: dict) -> set[str]:
    """The ids of `entries` (`{id: {"sources": [...], ...}}`) with a sign the fork made, not only a host mention."""
    return {ident for ident, entry in entries.items() if set(entry["sources"]) - {HOSTS}}


def rows(record: dict) -> dict[str, dict[str, bool]]:
    """Per build tool of `TOOLS`: named by the fork without declarations, with them, found by the pre-map's sources."""
    without, with_ = fork_named(record["without"]), fork_named(record["with"])
    kinds, tools, sources = set(record["units"]), set(record["workspace"]), set(record["unit_sources"])
    return {tool: {"fork": bool(without & set(ids)), "fork_with": bool(with_ & set(ids)),
                   "sources": bool(kinds & set(unit) or tools & set(space) or sources & set(stated))}
            for tool, (ids, unit, space, stated) in TOOLS.items()}


def lost(record: dict) -> list[dict]:
    """The entries the fork names with the declarations and not without them, each with the files of its signs."""
    gone = fork_named(record["with"]) - fork_named(record["without"])
    return [{"id": ident, "files": sorted({sign[1] for sign in record["with"][ident]["signs"] if sign[1]})}
            for ident in sorted(gone)]


def summary(records: dict[str, dict], tool_ids: set[str], categories: dict[str, str]) -> dict:
    """Totals over the fixtures without an error: per build tool, the fixtures where the sources find it, the fork
    names it (without declarations), both, only the sources (`uncovered`), only the fork, with the registry tool ids the
    fork names where only the sources find it (`beside`); per registry tool id, the fixtures that name it in each
    variant; the entries lost without declarations, by category."""
    tools = {tool: {"sources": 0, "fork": 0, "both": 0, "uncovered": 0, "fork_only": 0, "fork_with": 0,
                    "uncovered_fixtures": [], "beside": {}} for tool in TOOLS}
    named, losses, by_category = {}, 0, {}
    for name, record in sorted(records.items()):
        for tool, row in rows(record).items():
            line = tools[tool]
            line["sources"] += row["sources"]
            line["fork"] += row["fork"]
            line["fork_with"] += row["fork_with"]
            line["both"] += row["sources"] and row["fork"]
            line["fork_only"] += row["fork"] and not row["sources"]
            if row["sources"] and not row["fork"]:
                line["uncovered"] += 1
                line["uncovered_fixtures"].append(name)
                for ident in sorted(fork_named(record["without"]) & tool_ids):
                    line["beside"][ident] = line["beside"].get(ident, 0) + 1
        for variant in ("without", "with"):
            for ident in fork_named(record[variant]) & tool_ids:
                named.setdefault(ident, {"without": 0, "with": 0})[variant] += 1
        for item in lost(record):
            losses += 1
            category = categories.get(item["id"], "unknown")
            by_category[category] = by_category.get(category, 0) + 1
    return {"fixtures": len(records), "tools": tools, "tool_ids": dict(sorted(named.items())),
            "lost": {"entries": losses, "fixtures": sum(1 for r in records.values() if lost(r)),
                     "by_category": dict(sorted(by_category.items()))}}


# --- the container --------------------------------------------------------------------------------------------------

def code_files(base: Path) -> dict[str, str]:
    """`modal_stack`'s code files and this driver, each with the hash of its content."""
    return {**stack.code_files(base),
            OWN: hashlib.sha256((Path(base) / OWN).read_bytes().replace(b"\r\n", b"\n")).hexdigest()}


def code_hash(base: Path) -> str:
    return hashlib.sha256(json.dumps(code_files(base), sort_keys=True).encode()).hexdigest()[:16]


def _entries(found: list[dict]) -> dict:
    """The found entries by id: their sign sources and their first signs `[sign, path, line, source]`, the fork's first."""
    out = {}
    for entry in found:
        signs = sorted(entry["signs"], key=lambda s: s["source"] == HOSTS)[:SIGNS]
        out[entry["id"]] = {"sources": sorted({s["source"] for s in entry["signs"]}),
                            "signs": [[s["sign"], s["path"], s["line"], s["source"]] for s in signs]}
    return out


def _measure(name: str) -> dict:
    import premap
    import premap_replay
    import service_registry
    import snapshot
    import stack_recognition
    stack._image_tool()
    started = time.monotonic()
    project = stack._project(name)
    manifest = Path("/work") / f"{name}.out" / "manifest.sqlite"
    shutil.rmtree(manifest.parent, ignore_errors=True)
    snapshot.read_project(project, manifest)
    recording, missing = stack._recording(name), []
    facts = premap.write(manifest, runner=None if recording is None else premap_replay.replayer(recording, missing))
    model = "none" if recording is None else "partial" if missing else "recorded"
    registry, spawned, original = service_registry.load(), [], subprocess.Popen.__init__

    def watch(self, args, *rest, **keywords):
        spawned.append(" ".join(map(str, args if isinstance(args, (list, tuple)) else [args]))[:200])
        original(self, args, *rest, **keywords)

    middle = time.monotonic()
    subprocess.Popen.__init__ = watch
    try:
        with_ = stack_recognition.run(manifest, registry, facts)
        without = stack_recognition.run(manifest, registry, {k: v for k, v in facts.items() if k not in DECLARED})
    finally:
        subprocess.Popen.__init__ = original
    stack._ran(with_, "with")
    stack._ran(without, "without")
    units, spaces = facts.get("units") or [], facts.get("workspace") or []
    return {"model": model, "model_missing": len(missing),
            "units": sorted({u.get("kind") for u in units if u.get("kind")}),
            "workspace": sorted({w.get("tool") for w in spaces if w.get("tool")}),
            "unit_sources": sorted({s.partition("@")[0] for item in units + spaces for s in item.get("sources") or ()}),
            "declarations": len(stack_recognition.declarations(facts)[0]),
            "with": _entries(with_["found"]), "without": _entries(without["found"]), "spawned": spawned,
            "seconds": {"snapshot_premap": round(middle - started, 2), "stack": round(time.monotonic() - middle, 2)}}


@app.function(cpu=1.0, memory=4096, timeout=stack.TIMEOUT + stack.FIXTURE_TIMEOUT + 300,
              volumes={"/results": stack.volume})
def run_batch(names: list[str]) -> dict:
    sys.path[:0] = [f"/repo/{stack.SCRIPTS}", "/repo/benchmarks/project-model", "/repo/benchmarks/project-model/tools"]
    import fork_stack
    code = code_hash(Path("/repo"))
    print("code", code, flush=True)
    folder = Path("/results") / STORE
    folder.mkdir(parents=True, exist_ok=True)
    stack._image_tool()
    cannot = fork_stack.start()  # Node's cold start, outside every fixture
    began, done = time.monotonic(), []
    for name in names:
        if cannot:
            record = {"error": f"stack-analyser cannot start: {cannot}"}
        elif time.monotonic() - began > stack.TIMEOUT:
            record = {"error": f"not run: the batch used its {stack.TIMEOUT} s"}
        else:
            record = stack.bounded(stack.FIXTURE_TIMEOUT, _measure, name)
        (folder / f"{name}.json").write_text(json.dumps({"fixture": name, "code": code, **record}, ensure_ascii=False)
                                             + "\n", encoding="utf-8")
        done.append(name)
        print(name, record.get("error") or "ok", record.get("seconds") or {}, flush=True)
    stack.volume.commit()
    return {"code": code, "done": done, "seconds": round(time.monotonic() - began)}


@app.function(timeout=120)
def listing() -> dict[str, str]:
    return code_files(Path("/repo"))


def fetch(names: list[str]) -> None:
    sys.path[:0] = [str(REPO / "benchmarks/project-model/tools"), str(REPO / stack.SCRIPTS)]
    import fork_stack
    import service_registry
    import stack_analyser
    local, records, errors, codes, executed = code_hash(REPO), {}, {}, set(), {}
    for name in names:
        try:
            stored = json.loads(b"".join(stack.volume.read_file(f"{STORE}/{name}.json")))
        except Exception as error:  # noqa: BLE001
            errors[name] = f"no stored record: {type(error).__name__}"
            continue
        codes.add(stored.get("code"))
        if stored.get("error"):
            errors[name] = stored["error"]
            continue
        records[name] = stored
        executed[name] = fork_stack.executed(stored["spawned"], stack.NODE_BIN, stack.CLI, stack.GIT)
    entries = service_registry.load()["entries"]
    categories = {e["id"]: service_registry.entry_category(e) for e in entries}
    tool_ids = {ident for ident, category in categories.items() if category == "tool"}
    fixtures = {name: {"model": r["model"], "declarations": r["declarations"], "executed_project_code": executed[name],
                       "rows": {t: row for t, row in rows(r).items() if any(row.values())}, "lost": lost(r),
                       "tool_ids": {"without": sorted(fork_named(r["without"]) & tool_ids),
                                    "with": sorted(fork_named(r["with"]) & tool_ids)}}
                for name, r in sorted(records.items())}
    data = {"tool": "stack_build_tools", "version": f"stack-analyser {stack_analyser.VERSION} on Node {stack.NODE_VERSION}",
            "command": "snapshot.read_project; premap.write(replayed runs); stack_recognition.run with and without "
                       + ", ".join(DECLARED),
            "code": {"container": sorted(c for c in codes if c), "local": local},
            "executed_project_code": sorted(set(executed.values())),
            "summary": summary(records, tool_ids, categories), "errors": errors}
    target = HERE / "results" / "build_tools.json"
    target.parent.mkdir(exist_ok=True)
    head = json.dumps(data, ensure_ascii=False, indent=1)[:-2]
    lines = [f'"{n}":' + json.dumps(r, ensure_ascii=False, separators=(",", ":")) for n, r in fixtures.items()]
    target.write_text(head + ',\n"fixtures":{\n' + ",\n".join(lines) + "\n}}\n", encoding="utf-8", newline="\n")
    print(len(records), "fixtures,", len(errors), "errors ->", target,
          "| code", "same" if codes == {local} else f"DIFFERENT {sorted(codes)} vs {local}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("spawn", "fetch"))
    parser.add_argument("--fixtures", default="")
    parser.add_argument("--families", default=",".join(stack.FAMILIES))
    arguments = parser.parse_args()
    chosen = stack._chosen(arguments)
    if arguments.command == "fetch":
        fetch(chosen)
    else:
        print("local code", code_hash(REPO), len(chosen), "fixtures")
        remote, here = modal.Function.from_name(APP, "listing").remote(), code_files(REPO)
        if remote != here:  # the deployed copy is not this one: deploy again before trusting a round
            raise SystemExit("deployed code differs: " + ", ".join(sorted(k for k in set(remote) | set(here)
                                                                          if remote.get(k) != here.get(k))[:10]))
        function = modal.Function.from_name(APP, "run_batch")
        for group in stack.batches(chosen):
            print(group[0], "...", len(group), function.spawn(group).object_id)
