"""The `stack` step by the registry and by stack-analyser, project by project, on Modal: what the release loses, gains
and costs against the recogniser `technologies.derive` calls today, and the fast scan.

Nothing runs on this PC, and the project's code runs nowhere. Per fixture the container does what `modal_stack.py`
does (the snapshot, the pre-map with the answers `modal_premap.py --runs` recorded: the full scan), then:

- `technologies.derive` three times on those facts: the first, with the registry and not timed, makes the module graph
  the other two find; then with `service_registry.run` (`before`) and with `fork_stack.recognize` (`after`: the facts go
  to the release as declarations, its evidence comes back as the registry's entries), each timed;
- the pre-map again without its model commands (the fast scan) and each recogniser alone on it, timed, compared by the
  ids each declares (`fast.lost`: what the registry declares and the release does not);
- every process started meanwhile (`spawned`): `executed_project_code` is `no` when each is the perimeter's git
  (`modal_stack.GIT`) or the image's Node on the release's `cli.mjs`, else `unknown`.

Before its first fixture a batch runs the tool once on an empty folder, outside every timing, for Node's cold start; if
it cannot start, every fixture of the batch has that error. The pure parts (`measure`, `compare`, `executed`,
`fixture_result`, `summary`, `start`) are `tools/fork_stack.py`'s and are tested on this PC (`test_fork_stack.py`). The
image is `modal_stack.py`'s with the release (the pin and the commands of `tests/modal_pytest.py`; the test compares
them) and the Node the product starts (`indexers.runtime.NODE_VERSION`, not the test image's: the seconds are measured on
it; the test compares the version). The container replaces `stack_analyser.node` and `stack_analyser.cli` by those two
paths and never imports `indexers.runtime`. The container holds `modal_stack.py` too (its helpers are imported, not
copied) and the code hash of the files of `UPLOADED` is printed on both sides.

The container stores per fixture `project-model/stack-fork/<fixture>.json`; `fetch` compares and scores it here
(`score.score_technologies`) and writes `results/daodan_stack_fork.json`: per fixture the comparison (`lost`, `gained`,
`new`, `gone`, `not_in_registry`), the fast scan, the four seconds, `executed_project_code`, the two scores and the fork's
gaps of each scan (`fork_gaps`: their count by kind and the cause of a run of the tool that failed; `fork_failed` when
one did, and then the fixture is out of the totals' losses and fork seconds); at the head, the versions of Node and of
the release, and `totals`. The fixtures are baked into the image: deploy again after the corpus changed.

    modal deploy benchmarks/project-model/modal_stack_fork.py
    python benchmarks/project-model/modal_stack_fork.py spawn [--fixtures a,b | --families js,py,jvm,sys,mix,real]
    python benchmarks/project-model/modal_stack_fork.py fetch [--fixtures a,b | --families ...]
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import time
from pathlib import Path
from unittest import mock

import modal

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), "/repo/benchmarks/project-model"]  # the shared driver: beside this file on this PC, at /repo in the container
import modal_stack  # noqa: E402  (its helpers; it makes an app of its own, which this file does not use)

LOCAL, REPO, FIXTURES, GIT = modal_stack.LOCAL, modal_stack.REPO, modal_stack.FIXTURES, modal_stack.GIT
APP, STORE = "daodan-pm-stack-fork", "project-model/stack-fork"
TIMEOUT = 3000  # seconds a container may spend over its batch: three registry passes and two releases per fixture
FIXTURE_TIMEOUT = 1800  # seconds one fixture may take (`modal_stack`'s 900 held its largest, at 360, for one pass)
# The Node the product starts (`NODE_VERSION` of `daodan/core/indexers/runtime.py`; sha256 from the release's
# SHASUMS256.txt), fetched and checked as `tests/modal_pytest.py` fetches its own; and the release of
# `daodan/core/stack_analyser.py` as that launcher pins it, in /opt/stack-analyser. The launcher is not a module the
# container can import, so its pin and commands are repeated: `test_fork_stack.py` reads them from its syntax tree.
NODE_VERSION = "v22.23.4"
NODE = ("https://nodejs.org/dist/v22.23.4/node-v22.23.4-linux-x64.tar.gz",
        "b8492284c76a54baf58d61668dd0e41ee0fc98adabf9503d30f05d08f55b4406")
FETCH_NODE = ("python -c \"import hashlib, urllib.request; data = urllib.request.urlopen('%s').read(); "
              "assert hashlib.sha256(data).hexdigest() == '%s'; open('/tmp/node.tar.gz', 'wb').write(data)\"" % NODE)
STACK_ANALYSER = ("https://github.com/acaprino/stack-analyser-daodan/releases/download/v1.27.6-daodan.3/"
                  "stack-analyser-daodan-1.27.6-daodan.3.tgz",
                  "dbd26252845ccfabcc95ff45dee15118eb611adc2222f2c0a3f46ad6933fc322", "/opt/stack-analyser")
FETCH_STACK_ANALYSER = ("python -c \"import hashlib, urllib.request; data = urllib.request.urlopen('%s').read(); "
                        "assert hashlib.sha256(data).hexdigest() == '%s'; open('%s/release.tgz', 'wb').write(data)\""
                        % STACK_ANALYSER)
NODE_BIN = "/opt/node-v22.23.4-linux-x64/bin/node"  # where the tarball above unpacks, in /opt
CLI = "/opt/stack-analyser/package/dist/cli.mjs"  # `stack_analyser.PROGRAM` of the unpacked release
# what the container holds: `modal_stack`'s, the adapter and this driver, each at its repository path under /repo
UPLOADED = (*modal_stack.UPLOADED,
            (HERE / "tools/fork_stack.py", "benchmarks/project-model/tools/fork_stack.py"),
            (HERE / "modal_stack_fork.py", "benchmarks/project-model/modal_stack_fork.py"))

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
    """`modal_stack.code_files` over this driver's `UPLOADED`."""
    with mock.patch.object(modal_stack, "UPLOADED", UPLOADED):
        return modal_stack.code_files(base)


def code_hash(base: Path) -> str:
    with mock.patch.object(modal_stack, "UPLOADED", UPLOADED):
        return modal_stack.code_hash(base)


def _image_tool() -> None:
    """The tool is the image's Node on the image's release, not an install of Daodan's own."""
    import stack_analyser
    stack_analyser.node = lambda _project: Path(NODE_BIN)
    stack_analyser.cli = lambda: Path(CLI)


def _measure(name: str) -> dict:
    import fork_stack
    import premap
    import premap_replay
    import service_registry
    import snapshot
    from snapshot_store import open_snapshot
    _image_tool()
    project = modal_stack._project(name)
    manifest = Path("/work") / f"{name}.out" / "manifest.sqlite"
    shutil.rmtree(manifest.parent, ignore_errors=True)
    snapshot.write_snapshot(project, manifest)
    recording, missing = modal_stack._recording(name), []
    full = (premap.ensure(manifest) if recording is None
            else premap.write(manifest, runner=premap_replay.replayer(recording, missing)))
    model = "none" if recording is None else "partial" if missing else "recorded"
    spawned, original = [], subprocess.Popen.__init__

    def watch(self, args, *rest, **keywords):
        spawned.append(" ".join(map(str, args if isinstance(args, (list, tuple)) else [args]))[:200])
        original(self, args, *rest, **keywords)

    subprocess.Popen.__init__ = watch
    try:
        with open_snapshot(manifest) as store:
            fast = premap.derive(manifest, store, runner=None)  # the fast scan: no model command
        measured = fork_stack.measure(manifest, service_registry.load(), full, fast)
    finally:
        subprocess.Popen.__init__ = original
    return {"before": modal_stack._trim(measured["before"]),
            "after": {**modal_stack._trim(measured["after"]), "gaps": measured["after"]["gaps"]},
            "fast": measured["fast"], "fast_gaps": measured["fast_gaps"], "seconds": measured["seconds"],
            "spawned": spawned, "model": model, "model_missing": len(missing)}


@app.function(cpu=1.0, memory=4096, timeout=TIMEOUT + FIXTURE_TIMEOUT + 300, volumes={"/results": volume})
def run_batch(names: list[str]) -> dict:
    sys.path[:0] = [f"/repo/{modal_stack.SCRIPTS}", "/repo/benchmarks/project-model", "/repo/benchmarks/project-model/tools"]
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
            record = modal_stack.bounded(FIXTURE_TIMEOUT, _measure, name)
        (folder / f"{name}.json").write_text(json.dumps({"fixture": name, "code": code, **record}, ensure_ascii=False)
                                             + "\n", encoding="utf-8")
        done.append(name)
        print(name, record.get("error") or "ok", record.get("seconds") or {}, flush=True)
    volume.commit()
    return {"code": code, "done": done, "seconds": round(time.monotonic() - began)}


@app.function(timeout=120)
def listing() -> dict[str, str]:
    return code_files(Path("/repo"))


def fetch(names: list[str]) -> None:
    sys.path[:0] = [str(HERE / "tools"), str(HERE)]
    import fork_stack
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
        out[name] = fork_stack.fixture_result(expected, stored, NODE_BIN, CLI, GIT)
    totals = fork_stack.summary(out)
    data = {"tool": "daodan_stack_fork", "version": f"stack-analyser {stack_analyser.VERSION} on Node {NODE_VERSION}, against service_registry.run",
            "group": "stack",
            "command": "technologies.derive(manifest, registry, facts) with service_registry.run and with "
                       "fork_stack.recognize; the fast scan: premap.derive(runner=None) and each recogniser alone",
            "code": {"container": sorted(c for c in codes if c), "local": local}, "totals": totals}
    target = HERE / "results" / "daodan_stack_fork.json"
    target.parent.mkdir(exist_ok=True)
    head = json.dumps(data, ensure_ascii=False)[:-1]
    lines = [f'"{n}":' + json.dumps(r, ensure_ascii=False, separators=(",", ":")) for n, r in sorted(out.items())]
    target.write_text(head + ',\n"fixtures":{\n' + ",\n".join(lines) + "\n}}\n", encoding="utf-8", newline="\n")
    print(len(out), "fixtures ->", target, "| code", "same" if codes == {local} else f"DIFFERENT {sorted(codes)} vs {local}")
    print(json.dumps(totals, ensure_ascii=False))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("spawn", "fetch"))
    parser.add_argument("--fixtures", default="")
    parser.add_argument("--families", default=",".join(modal_stack.FAMILIES))
    arguments = parser.parse_args()
    chosen = modal_stack._chosen(arguments)
    if arguments.command == "fetch":
        fetch(chosen)
    else:
        print("local code", code_hash(REPO), len(chosen), "fixtures")
        remote, local = modal.Function.from_name(APP, "listing").remote(), code_files(REPO)
        if remote != local:  # the deployed copy is not this one: deploy again before trusting a round
            raise SystemExit("deployed code differs: " + ", ".join(sorted(k for k in set(remote) | set(local)
                                                                          if remote.get(k) != local.get(k))[:10]))
        function = modal.Function.from_name(APP, "run_batch")
        for group in modal_stack.batches(chosen):
            print(group[0], "...", len(group), function.spawn(group).object_id)
