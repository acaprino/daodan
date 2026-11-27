"""The pipeline's `stack` step on Modal: snapshot, pre-map and `technologies.ensure`, scored on the corpus. The step is
the product's: the recogniser is stack-analyser (`stack_recognition.run`), and nothing else recognizes.

Nothing runs on this PC, and the project's code runs nowhere: the container writes the snapshot, then, as the pipeline
does, the stack step's record (`stack_recognition.ensure`, whose build tools choose the pre-map's sources), the pre-map
with the answers `modal_premap.py --runs` recorded for its model commands (`results/premap-runs`, replayed as
`tools/premap_replay.py` replays them: no tool runs), and `technologies.ensure(manifest)` derives the record
`technologies.json`: the full scan, whose seconds are `seconds.stack` (the pre-map's replay among them). A fixture without a recording has its model
commands `not_run` (`model: none`), and the pre-map's facts that come from them (services of a CI job, `excluded`) are
missing; a command the recording lacks is counted (`model: partial`). Then the fast scan: the pre-map again without its
model commands, and `technologies.derive` on it, timed (`fast_seconds`; the pre-map and the stack step's record, already
there, are not in it). A fixture whose run of the tool failed is an `error`, not a result that found nothing. The result
also has `declarations`, the number the step sent to the tool in the full scan (0: the step sends none), and `perimeter`,
the entries of `skipDirs` and `ignore` it sent (`tools/fork_stack.py`).


The tool is the image's Node (`indexers.runtime.NODE_VERSION`, the one the product starts) on the image's release (the
pin of `daodan/core/stack_analyser.py`, fetched as `tests/modal_pytest.py` fetches it; `test_fork_stack.py` compares them):
the container replaces `stack_analyser.node` and `stack_analyser.cli` by those two paths, so the install itself (the
download in the product's tool folder) is not measured here; it is the proof `tests/test_codebase_map_host_programs.py`
runs. Before its first fixture a batch runs the tool once on an empty folder, outside every timing, for Node's cold start; if
it cannot start, every fixture of the batch has that error. A process started during the two scans is recorded
(`spawned`); a fixture's result is `executed_project_code: no` when each is the perimeter's git with hooks and monitors off
(GIT) or the image's Node on the release's `cli.mjs` (`fork_stack.executed`), else `unknown`. The container holds the
plugin's scripts with the data they read beside their folder (`service_registry.REGISTRY`), `score.py` and this driver, at the
paths of the repository under `/repo`; the code hash of those files is printed on both sides and must match. A fixture with `source.json` is
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
sys.path.insert(0, str(HERE / "tools"))  # `fork_stack`: beside this file, on this PC and at /repo in the container
LOCAL = modal.is_local()
REPO = HERE.parents[1] if LOCAL else Path("/repo")
FIXTURES = Path(os.environ.get("DAODAN_FIXTURES") or HERE / "fixtures")
APP, STORE, REAL_STORE = "daodan-pm-stack", "project-model/stack", "project-model/native-real"
FAMILIES = ("js", "py", "jvm", "sys", "mix", "real")
SCRIPTS, DATA = "daodan/core", "daodan/data"
# what the container holds, each at its repository path under /repo; the data sit beside the scripts
UPLOADED = ((REPO / SCRIPTS, SCRIPTS), (REPO / DATA, DATA),
            (HERE / "score.py", "benchmarks/project-model/score.py"),
            (HERE / "tools/premap_replay.py", "benchmarks/project-model/tools/premap_replay.py"),
            (HERE / "tools/daodan_modules.py", "benchmarks/project-model/tools/daodan_modules.py"),
            (HERE / "tools/native_common.py", "benchmarks/project-model/tools/native_common.py"),
            (HERE / "tools/fork_stack.py", "benchmarks/project-model/tools/fork_stack.py"),
            (HERE / "results/premap-runs", "benchmarks/project-model/results/premap-runs"),
            (HERE / "modal_stack.py", "benchmarks/project-model/modal_stack.py"))
SKIPPED = ("expected.json", "source.json")
GIT = "/usr/bin/git -c core.fsmonitor=false -c core.hooksPath=/dev/null "  # the perimeter: hooks and monitors off
BATCH = {"hand": 20, "real": 4}  # fixtures per container: a family's hand-written ones, real repositories
TIMEOUT = 3000  # seconds a container may spend over its batch: two scans by the release per fixture
FIXTURE_TIMEOUT = 1800  # seconds one fixture may take (the registry's one pass held its largest at 360 in 900)
# The Node the product starts (`NODE_VERSION` of `daodan/core/indexers/runtime.py`; sha256 from the release's
# SHASUMS256.txt), fetched and checked as `tests/modal_pytest.py` fetches its own; and the release of
# `daodan/core/stack_analyser.py` as that launcher pins it, in /opt/stack-analyser. The launcher is not a module the
# container can import, so its pin and commands are repeated: `test_fork_stack.py` reads them from its syntax tree.
NODE_VERSION = "v22.23.4"
NODE = ("https://nodejs.org/dist/v22.23.4/node-v22.23.4-linux-x64.tar.gz",
        "b8492284c76a54baf58d61668dd0e41ee0fc98adabf9503d30f05d08f55b4406")
FETCH_NODE = ("python -c \"import hashlib, urllib.request; data = urllib.request.urlopen('%s').read(); "
              "assert hashlib.sha256(data).hexdigest() == '%s'; open('/tmp/node.tar.gz', 'wb').write(data)\"" % NODE)
STACK_ANALYSER = ("https://github.com/acaprino/stack-analyser-daodan/releases/download/v1.27.6-daodan.6/"
                  "stack-analyser-daodan-1.27.6-daodan.6.tgz",
                  "d9f9b2f0200b5f4ed2479fa1583a9ff308d96ca7bf5accde9df5827ed772a209", "/opt/stack-analyser")
FETCH_STACK_ANALYSER = ("python -c \"import hashlib, urllib.request; data = urllib.request.urlopen('%s').read(); "
                        "assert hashlib.sha256(data).hexdigest() == '%s'; open('%s/release.tgz', 'wb').write(data)\""
                        % STACK_ANALYSER)
NODE_BIN = "/opt/node-v22.23.4-linux-x64/bin/node"  # where the tarball above unpacks, in /opt
CLI = "/opt/stack-analyser/package/dist/cli.mjs"  # `stack_analyser.PROGRAM` of the unpacked release

image = (modal.Image.debian_slim(python_version="3.12").apt_install("git", "ca-certificates")
         .pip_install("tree-sitter==0.26.0", "tree-sitter-language-pack==1.13.5", "sqlglot>=30", "PyYAML>=6")
         .run_commands(FETCH_NODE, "tar -xzf /tmp/node.tar.gz -C /opt && rm /tmp/node.tar.gz",
                       f"mkdir -p {STACK_ANALYSER[2]}", FETCH_STACK_ANALYSER,
                       f"tar -xzf {STACK_ANALYSER[2]}/release.tgz -C {STACK_ANALYSER[2]}"))
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
    import score

    units = [{k: u[k] for k in ("id", "name", "kind", "paths", "technologies", "technology_evidence") if k in u}
             for u in record["units"]]
    entries = []
    for entry in record["technologies"]:
        signs = entry["signs"]  # the registry deduplicates and sorts by checker, path, line and value
        sample = signs[:8]
        sampled_paths = {s["path"] for s in sample if score.declared_stack_sign(s)}
        for sign in signs[8:]:
            if score.declared_stack_sign(sign) and sign["path"] not in sampled_paths:
                sample.append(sign)
                sampled_paths.add(sign["path"])
        entries.append({**{k: entry[k] for k in ("id", "name", "kind", "type", "category") if k in entry},
                        "signs": sample, "signs_total": len(signs)})
    return {"technologies": entries, "units": units,
            **({"configured_services": record["configured_services"]} if "configured_services" in record else {})}


def _recording(name: str) -> dict | None:
    import gzip
    file = Path("/repo/benchmarks/project-model/results/premap-runs") / f"{name}.json.gz"
    return json.loads(gzip.decompress(file.read_bytes()).decode("utf-8")) if file.is_file() else None


def _image_tool() -> None:
    """The tool is the image's Node on the image's release, not an install of Daodan's own."""
    import stack_analyser
    stack_analyser.node = lambda _project: Path(NODE_BIN)
    stack_analyser.cli = lambda: Path(CLI)


def _ran(answer: dict, scan: str) -> None:
    """The scan's run of the tool did not fail: a fixture whose run failed is an `error`, not a project that shows nothing."""
    failed = [gap["detail"] for gap in answer["gaps"] if gap["kind"] == "checker_failed" and gap.get("checker") == "stack-analyser"]
    if failed:
        raise RuntimeError(f"stack-analyser failed in the {scan} scan: {failed[0]}"[:600])


def _measure(name: str) -> dict:
    import premap
    import premap_replay
    import service_registry
    import snapshot
    import stack_analyser
    import stack_recognition
    import technologies
    from fork_stack import figures
    _image_tool()

    started = time.monotonic()
    project = _project(name)
    manifest = Path("/work") / f"{name}.out" / "manifest.sqlite"
    shutil.rmtree(manifest.parent, ignore_errors=True)
    snapshot.read_project(project, manifest)
    recording, missing = _recording(name), []
    middle = time.monotonic()
    spawned, original = [], subprocess.Popen.__init__
    passed, run = [], stack_analyser.run

    def watch(self, args, *rest, **keywords):
        spawned.append(" ".join(map(str, args if isinstance(args, (list, tuple)) else [args]))[:200])
        original(self, args, *rest, **keywords)

    subprocess.Popen.__init__ = watch
    stack_analyser.run = lambda root, **keywords: passed.append(keywords) or run(root, **keywords)
    try:
        stack_recognition.ensure(manifest)  # the stack step first: its build tools choose the pre-map's sources
        if recording is not None:
            premap.write(manifest, runner=premap_replay.replayer(recording, missing))
        record = technologies.ensure(manifest)  # the full scan
        states: dict[str, int] = {}
        for source in json.loads(premap.path(manifest).read_text(encoding="utf-8"))["sources"]:
            states[source["state"]] = states.get(source["state"], 0) + 1
        ended = time.monotonic()
        facts = premap.write(manifest, runner=None)  # the fast scan: the pre-map without its model commands, not timed
        began = time.monotonic()
        fast = technologies.derive(manifest, service_registry.load(), facts)  # derives, never a stored record
        fast_seconds = round(time.monotonic() - began, 3)
    finally:
        subprocess.Popen.__init__ = original
        stack_analyser.run = run
    model = "none" if recording is None else "partial" if missing else "recorded"
    _ran(record, "full")
    _ran(fast, "fast")
    return {**_trim(record), "premap_sources": states, "spawned": spawned, "model": model, "model_missing": len(missing),
            "seconds": {"snapshot": round(middle - started, 2), "stack": round(ended - middle, 2)},
            "fast_seconds": fast_seconds, **figures(passed)}


def bounded(seconds: int, function, *args, **keywords) -> dict:
    """`function(*args, **keywords)` in a process of its own, or `{"error": "no answer in N s; stood at: ..."}` when
    it does not answer in `seconds`: faulthandler writes the stack of the process at four fifths of the time, and
    the top of it goes into the error, the cause of a hang. An exception is the fixture's result, with its type."""
    import faulthandler
    import multiprocessing
    import tempfile

    context = multiprocessing.get_context("fork")
    receiver, sender = context.Pipe(duplex=False)
    with tempfile.TemporaryFile("w+") as stack:
        def work():
            faulthandler.dump_traceback_later(seconds * 0.8, exit=False, file=stack)
            try:
                sender.send(function(*args, **keywords))
            except Exception as error:  # noqa: BLE001 - a fixture's failure is its result
                sender.send({"error": f"{type(error).__name__}: {str(error)[-400:]}"})

        process = context.Process(target=work)
        process.start()
        if receiver.poll(seconds):
            result = receiver.recv()
            process.join()
            return result
        process.kill()
        stack.seek(0)
        top = " ".join(line.strip() for line in stack.read().splitlines()[1:9])
        return {"error": f"no answer in {seconds} s; stood at: {top}"[:900]}


@app.function(cpu=1.0, memory=4096, timeout=TIMEOUT + FIXTURE_TIMEOUT + 300, volumes={"/results": volume})
def run_batch(names: list[str]) -> dict:
    sys.path[:0] = [f"/repo/{SCRIPTS}", "/repo/benchmarks/project-model", "/repo/benchmarks/project-model/tools"]
    import fork_stack
    code = code_hash(Path("/repo"))
    print("code", code, flush=True)
    folder = Path("/results") / STORE
    folder.mkdir(parents=True, exist_ok=True)
    _image_tool()
    cannot = fork_stack.start()  # Node's cold start, here and not in the first fixture's seconds
    if cannot:
        print("stack-analyser cannot start:", cannot, flush=True)
    began, done = time.monotonic(), []
    for name in names:
        if cannot:
            record = {"error": f"stack-analyser cannot start: {cannot}"}
        elif time.monotonic() - began > TIMEOUT:
            record = {"error": f"not run: the batch used its {TIMEOUT} s"}
        else:
            record = bounded(FIXTURE_TIMEOUT, _measure, name)
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
    import fork_stack
    import score
    import stack_analyser
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
                     **({"configured_services": stored["configured_services"]} if "configured_services" in stored else {}),
                     "units": len(stored["units"]), "premap_sources": stored["premap_sources"],
                     "model": stored["model"], "model_missing": stored["model_missing"],
                     "seconds": round(sum(stored["seconds"].values()), 2), "seconds_detail": stored["seconds"],
                     "fast_seconds": stored.get("fast_seconds"), "declarations": stored.get("declarations"),
                     "perimeter": stored.get("perimeter"),
                     "executed_project_code": fork_stack.executed(stored["spawned"], NODE_BIN, CLI, GIT),
                     "spawned": sorted(set(stored["spawned"]))}
    data = {"tool": "daodan_stack",
            "version": f"technologies.py (daodan/technologies/v1) of the checkout, stack-analyser {stack_analyser.VERSION} on Node {NODE_VERSION}",
            "group": "stack", "command": "snapshot.read_project; technologies.ensure(manifest), no runner; premap.write(runner=None); technologies.derive",
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
