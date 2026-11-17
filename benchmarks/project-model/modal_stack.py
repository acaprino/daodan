"""The pipeline's `stack` step on Modal: snapshot, pre-map and `technologies.ensure`, scored on the corpus.

Nothing runs on this PC, and the project's code runs nowhere: the container writes the snapshot, writes the
pre-map with the answers `modal_premap.py --runs` recorded for its model commands (`results/premap-runs`, replayed
as `tools/premap_replay.py` replays them: no tool runs), then `technologies.ensure(manifest)` derives the record
`technologies.json`. A fixture without a recording has its model commands `not_run` (`model: none`), and the
pre-map's facts that come from them (services of a CI job, `excluded`) are missing; a command the recording lacks
is counted (`model: partial`). A process started during `ensure` is recorded (`spawned`); a fixture's result is
`executed_project_code: no` when each is the perimeter's git with hooks and monitors off (GIT), else `unknown`. The container holds the plugin's scripts with the data they
read beside their folder (`service_registry.REGISTRY`), `score.py` and this driver, at the paths of the repository
under `/repo`; the code hash of those files is printed on both sides and must match. A fixture with `source.json` is
a real repository: its clone from the archive `modal_native.py prepare` keeps on the volume, else a shallow clone at
the pinned commit. `expected.json` and `source.json` never enter the project the step reads.

The container stores per fixture the record (`project-model/stack/<fixture>.json`); `fetch` converts and scores it
here (`score.score_technologies`), so a change to the adapter or the aliases costs no run, and writes
`results/daodan_stack.json`. The fixtures are baked into the image: deploy again after the corpus changed.

    modal deploy benchmarks/project-model/modal_stack.py
    python benchmarks/project-model/modal_stack.py spawn [--fixtures a,b | --families js,py,jvm,sys,mix,real]
    python benchmarks/project-model/modal_stack.py fetch [--fixtures a,b | --families ...]

`DAODAN_FIXTURES` names another fixtures folder (the live checkout's, while a copy of the repository is edited).
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
import time
from pathlib import Path

import modal

HERE = Path(__file__).resolve().parent
LOCAL = modal.is_local()
REPO = HERE.parents[1] if LOCAL else Path("/repo")
FIXTURES = Path(os.environ.get("DAODAN_FIXTURES") or HERE / "fixtures")
APP, STORE, REAL_STORE = "daodan-pm-stack", "project-model/stack", "project-model/native-real"
FAMILIES = ("js", "py", "jvm", "sys", "mix", "real")
SCRIPTS, DATA = "plugins/codebase-map/skills/map/scripts", "plugins/codebase-map/skills/map/data"
# what the container holds, each at its repository path under /repo; the data sit beside the scripts
UPLOADED = ((REPO / SCRIPTS, SCRIPTS), (REPO / DATA, DATA),
            (HERE / "score.py", "benchmarks/project-model/score.py"),
            (HERE / "tools/premap_replay.py", "benchmarks/project-model/tools/premap_replay.py"),
            (HERE / "tools/daodan_modules.py", "benchmarks/project-model/tools/daodan_modules.py"),
            (HERE / "tools/native_common.py", "benchmarks/project-model/tools/native_common.py"),
            (HERE / "results/premap-runs", "benchmarks/project-model/results/premap-runs"),
            (HERE / "modal_stack.py", "benchmarks/project-model/modal_stack.py"))
SKIPPED = ("expected.json", "source.json")
GIT = "/usr/bin/git -c core.fsmonitor=false -c core.hooksPath=/dev/null "  # the perimeter: hooks and monitors off
BATCH = {"hand": 20, "real": 4}  # fixtures per container: a family's hand-written ones, real repositories
TIMEOUT = 1500  # seconds a container may spend over its batch

image = (modal.Image.debian_slim(python_version="3.12").apt_install("git", "ca-certificates")
         .pip_install("tree-sitter==0.26.0", "tree-sitter-language-pack==1.13.5", "sqlglot>=30"))
if LOCAL:
    for _local, _repo in UPLOADED:
        image = (image.add_local_dir(_local, f"/repo/{_repo}", ignore=["**/__pycache__/**"]) if _local.is_dir()
                 else image.add_local_file(_local, f"/repo/{_repo}"))
    image = image.add_local_dir(FIXTURES, "/repo/benchmarks/project-model/fixtures")
app = modal.App(APP, image=image)
volume = modal.Volume.from_name("daodan-flow-results", create_if_missing=True)


def code_files(base: Path) -> dict[str, str]:
    """The files of UPLOADED by their repository paths, each with the hash of its content (line endings as git keeps them)."""
    out = {}
    for _, repo in UPLOADED:
        root = Path(base) / repo
        for file in sorted([root] if root.is_file() else root.rglob("*")):
            if file.is_file() and "__pycache__" not in file.parts:
                out[file.relative_to(base).as_posix()] = hashlib.sha256(file.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    return out


def code_hash(base: Path) -> str:
    return hashlib.sha256(json.dumps(code_files(base), sort_keys=True).encode()).hexdigest()[:16]


def batches(names: list[str], hand: int = BATCH["hand"], real: int = BATCH["real"]) -> list[list[str]]:
    """The fixtures in containers: a family's together up to `hand`, the `real-*` ones up to `real`."""
    out: dict[str, list[str]] = {}
    for name in sorted(names):
        out.setdefault(name.split("-", 1)[0], []).append(name)
    return [group[i:i + size] for family, group in out.items() for size in [real if family == "real" else hand]
            for i in range(0, len(group), size)]


def _project(name: str) -> Path:
    """The project the step reads: a copy of the fixture, or the real repository's clone; no answer file in it."""
    fixture = Path("/repo/benchmarks/project-model/fixtures") / name
    project = Path("/work") / name
    shutil.rmtree(project, ignore_errors=True)
    if not (fixture / "source.json").is_file():
        shutil.copytree(fixture, project, ignore=shutil.ignore_patterns(*SKIPPED))
        return project
    archive = Path("/results") / REAL_STORE / f"{name}.tar.gz"
    if archive.is_file():
        part = Path("/work/real-part") / name
        shutil.rmtree(part, ignore_errors=True)
        part.mkdir(parents=True)
        with tarfile.open(archive) as tar:
            tar.extractall(part, filter="tar")
        (part / name).rename(project)
        return project
    source = json.loads((fixture / "source.json").read_text(encoding="utf-8"))
    project.mkdir(parents=True)
    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}
    for argv in (["git", "init", "-q"], ["git", "remote", "add", "origin", source["repo"]],
                 ["git", "fetch", "-q", "--depth", "1", "origin", source["commit"]],
                 ["git", "checkout", "-q", "FETCH_HEAD"]):
        done = subprocess.run(argv, cwd=project, capture_output=True, text=True, timeout=900, env=env)
        if done.returncode:
            raise RuntimeError(f"{' '.join(argv[:3])}: {done.stderr.strip()[-300:]}")
    return project


def _trim(record: dict) -> dict:
    """The record without the repeated signs: what the adapter and the cards read."""
    entries = []
    for entry in record["technologies"]:
        signs = {(s["sign"], s["value"], s["path"], s["line"]) for s in entry["signs"]}
        entries.append({**{k: entry.get(k) for k in ("id", "name", "kind", "type")},
                        "signs": [dict(zip(("sign", "value", "path", "line"), s)) for s in sorted(signs, key=str)[:8]],
                        "signs_total": len(signs)})
    return {"technologies": entries, "units": [{k: u.get(k) for k in ("id", "name", "kind", "paths", "technologies")}
                                               for u in record["units"]]}


def _recording(name: str) -> dict | None:
    import gzip
    file = Path("/repo/benchmarks/project-model/results/premap-runs") / f"{name}.json.gz"
    return json.loads(gzip.decompress(file.read_bytes()).decode("utf-8")) if file.is_file() else None


def _measure(name: str) -> dict:
    import premap
    import premap_replay
    import snapshot
    import technologies
    started = time.monotonic()
    project = _project(name)
    manifest = Path("/work") / f"{name}.out" / "manifest.sqlite"
    shutil.rmtree(manifest.parent, ignore_errors=True)
    snapshot.write_snapshot(project, manifest)
    recording, missing = _recording(name), []
    if recording is not None:
        premap.write(manifest, runner=premap_replay.replayer(recording, missing))
    model = "none" if recording is None else "partial" if missing else "recorded"
    middle = time.monotonic()
    spawned, original = [], subprocess.Popen.__init__

    def watch(self, args, *rest, **keywords):
        spawned.append(" ".join(map(str, args if isinstance(args, (list, tuple)) else [args]))[:200])
        original(self, args, *rest, **keywords)

    subprocess.Popen.__init__ = watch
    try:
        record = technologies.ensure(manifest)
    finally:
        subprocess.Popen.__init__ = original
    states: dict[str, int] = {}
    for source in json.loads(premap.path(manifest).read_text(encoding="utf-8"))["sources"]:
        states[source["state"]] = states.get(source["state"], 0) + 1
    return {**_trim(record), "premap_sources": states, "spawned": spawned, "model": model, "model_missing": len(missing),
            "seconds": {"snapshot": round(middle - started, 2), "stack": round(time.monotonic() - middle, 2)}}


@app.function(cpu=1.0, memory=3072, timeout=TIMEOUT + 300, volumes={"/results": volume})
def run_batch(names: list[str]) -> dict:
    sys.path[:0] = [f"/repo/{SCRIPTS}", "/repo/benchmarks/project-model", "/repo/benchmarks/project-model/tools"]
    code = code_hash(Path("/repo"))
    print("code", code, flush=True)
    folder = Path("/results") / STORE
    folder.mkdir(parents=True, exist_ok=True)
    began, done = time.monotonic(), []
    for name in names:
        if time.monotonic() - began > TIMEOUT:
            record = {"error": f"not run: the batch used its {TIMEOUT} s"}
        else:
            try:
                record = _measure(name)
            except Exception as error:  # noqa: BLE001 - a fixture's failure is its result
                record = {"error": f"{type(error).__name__}: {str(error)[-400:]}"}
        (folder / f"{name}.json").write_text(json.dumps({"fixture": name, "code": code, **record}, ensure_ascii=False)
                                             + "\n", encoding="utf-8")
        done.append(name)
        print(name, record.get("error") or "ok", record.get("seconds") or {}, flush=True)
    volume.commit()
    return {"code": code, "done": done, "seconds": round(time.monotonic() - began)}


@app.function(timeout=120)
def listing() -> dict[str, str]:
    return code_files(Path("/repo"))


def _chosen(arguments) -> list[str]:
    if arguments.fixtures:
        return [n for n in arguments.fixtures.split(",") if n]
    families = [f for f in arguments.families.split(",") if f]
    return sorted(p.name for p in FIXTURES.iterdir()
                  if (p / "expected.json").is_file() and p.name.split("-", 1)[0] in families)


def fetch(names: list[str]) -> None:
    sys.path.insert(0, str(HERE))
    import score
    local = code_hash(REPO)
    out, codes = {}, set()
    for name in names:
        try:
            stored = json.loads(b"".join(volume.read_file(f"{STORE}/{name}.json")))
        except Exception as error:  # noqa: BLE001
            out[name] = {"error": f"no stored record: {type(error).__name__}"}
            continue
        codes.add(stored.get("code"))
        if stored.get("error"):
            out[name] = {"error": stored["error"]}
            continue
        expected = json.loads((FIXTURES / name / "expected.json").read_text(encoding="utf-8"))
        out[name] = {"output": score.technologies_faces(stored), "score": score.score_technologies(expected, stored),
                     "technologies": len(stored["technologies"]), "ids": [t["id"] for t in stored["technologies"]],
                     "units": len(stored["units"]), "premap_sources": stored["premap_sources"],
                     "model": stored["model"], "model_missing": stored["model_missing"],
                     "seconds": round(sum(stored["seconds"].values()), 2), "seconds_detail": stored["seconds"],
                     "executed_project_code": "no" if all(c.startswith(GIT) for c in stored["spawned"]) else "unknown",
                     "spawned": sorted(set(stored["spawned"]))}
    data = {"tool": "daodan_stack", "version": "technologies.py (daodan/technologies/v1) of the checkout",
            "group": "stack", "command": "snapshot.write_snapshot; technologies.ensure(manifest), no runner",
            "code": {"container": sorted(c for c in codes if c), "local": local}}
    target = HERE / "results" / "daodan_stack.json"
    target.parent.mkdir(exist_ok=True)
    head = json.dumps(data, ensure_ascii=False)[:-1]
    lines = [f'"{n}":' + json.dumps(r, ensure_ascii=False, separators=(",", ":")) for n, r in sorted(out.items())]
    target.write_text(head + ',\n"fixtures":{\n' + ",\n".join(lines) + "\n}}\n", encoding="utf-8", newline="\n")
    print(len(out), "fixtures ->", target, "| code", "same" if codes == {local} else f"DIFFERENT {sorted(codes)} vs {local}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("spawn", "fetch"))
    parser.add_argument("--fixtures", default="")
    parser.add_argument("--families", default=",".join(FAMILIES))
    arguments = parser.parse_args()
    chosen = _chosen(arguments)
    if arguments.command == "fetch":
        fetch(chosen)
    else:
        print("local code", code_hash(REPO), len(chosen), "fixtures")
        remote, local = modal.Function.from_name(APP, "listing").remote(), code_files(REPO)
        if remote != local:  # the deployed copy is not this one: deploy again before trusting a round
            raise SystemExit("deployed code differs: " + ", ".join(sorted(k for k in set(remote) | set(local)
                                                                          if remote.get(k) != local.get(k))[:10]))
        function = modal.Function.from_name(APP, "run_batch")
        for group in batches(chosen):
            print(group[0], "...", len(group), function.spawn(group).object_id)
