"""The whole pipeline on Modal: snapshot, scan (the pre-map with its build tools), analyzers and union.

Nothing runs on this PC. A Modal function holds the plugin's scripts and runs `pipeline.run` on each case; where
the pipeline asks for a container (`container.run_in_container`), the function starts a Modal Sandbox from the
same image, pinned by the same digest:

- the copy of the project and its inputs travel on the volume `daodan-flow-results` and are unpacked at `/`;
- with a preparation, a first sandbox runs it with the network open (Modal's allowlist is by address, not by
  host: the registries-only proxy of Daodan's container is not reproduced here), its filesystem is snapshotted
  and a second sandbox starts from the snapshot with the network blocked for the execution;
- without one, a single sandbox with the network blocked;
- the declared outputs come back as one tar, into the run's folder, as `container.fetch` leaves them.

A family's fixtures run in groups of `--chunk` (4), each group in a function call of its own; each real repository (its clone from the archive `modal_native.py
prepare` keeps on the volume) has its own. Per case the result holds the pre-map's score against
`expected.json`, each source's state, the gaps, each step's result, the events by kind and the seconds.

    python -m modal run benchmarks/project-model/modal_pipeline.py --cases js-npm-single,sys-meson --out OUT.json
    python -m modal run benchmarks/project-model/modal_pipeline.py --cases js,py,jvm,sys,mix,real --out OUT.json
"""
from __future__ import annotations

import collections
import io
import json
import os
import posixpath
import shlex
import shutil
import sys
import tarfile
import tempfile
import time
import uuid
from pathlib import Path

import modal

HERE = Path(__file__).resolve().parent
LOCAL = (HERE / "score.py").is_file()
REPO = HERE.parents[1] if LOCAL else Path("/")
REMOTE_SCRIPTS = "/daodan/map/scripts"  # container paths: POSIX strings, whatever runs the client
REMOTE_PM = "/pm"
SCRATCH = "project-model/pipeline-scratch"  # on the volume: each run's copy, removed when the run ends
FAMILIES = ("js", "py", "jvm", "sys", "mix")
PACKED = "/tmp/daodan-outputs.tar"
SANDBOX_CPU = 2.0  # cores a build or an indexer is given: the default share would throttle Gradle and CMake

image = (modal.Image.debian_slim(python_version="3.13")
         .apt_install("git", "ca-certificates", "xz-utils")
         .pip_install("uv", "tree-sitter==0.26.0", "tree-sitter-language-pack==1.13.5", "sqlglot>=30"))
if LOCAL:
    image = (image.add_local_dir(REPO / "plugins/codebase-map/skills/map/scripts", REMOTE_SCRIPTS,
                                 ignore=["**/__pycache__/**"])
             .add_local_dir(HERE / "fixtures", f"{REMOTE_PM}/fixtures")
             .add_local_file(HERE / "score.py", f"{REMOTE_PM}/score.py"))
app = modal.App("daodan-pipeline", image=image)
volume = modal.Volume.from_name("daodan-flow-results")


def _phase(sandbox, name: str, script: str, env: dict, timeout: float, out_dir: Path) -> dict:
    """One sh script in `sandbox`, its output in `<name>.log`: the record's row."""
    started = time.monotonic()
    row = {"phase": name, "engine": "modal"}
    try:
        process = sandbox.exec("sh", "-c", f"( {script} ) 2>&1", env=env, timeout=int(timeout))
        (out_dir / f"{name}.log").write_text(process.stdout.read(), encoding="utf-8", errors="replace")
        code = process.wait()
        row.update(outcome="timeout" if code == -1 else "exited", exit_code=None if code == -1 else code)
    except Exception as error:  # noqa: BLE001 - the sandbox's failure is the phase's outcome
        row.update(outcome="failed", exit_code=None, cause=f"{type(error).__name__}: {error}")
    row.update(log=str(out_dir / f"{name}.log"), duration_seconds=round(time.monotonic() - started, 3))
    return row


def sandbox_run(project, command, *, image, out_dir, prepare=None, outputs=(), env=None, timeout=600,
                prepare_timeout=1800, memory=2 * 2**30, inputs=None, **_):
    """`container.run_in_container` on Modal Sandboxes: the same arguments and result (the module's docstring)."""
    import container
    out_dir = Path(out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    record = out_dir / container.RECORD_NAME
    result = {"state": "failed", "exit_code": None, "outputs": [], "record": str(record), "engine": "modal"}
    token = uuid.uuid4().hex[:12]
    scratch = Path("/results") / SCRATCH / token
    env = {"HOME": container.HOME, **(env or {})} if prepare else dict(env or {})
    options = {"app": modal.App.lookup("daodan-pipeline-sandboxes", create_if_missing=True),
               "volumes": {"/results": volume},
               "memory": int(memory / 2**20), "cpu": SANDBOX_CPU, "timeout": int(prepare_timeout + timeout + 900)}
    unpack = f"tar -xf /results/{SCRATCH}/{token}/copy.tar -C / && mkdir -p {container.WORKDIR} && cd {container.WORKDIR}"
    boxes = []
    try:
        try:
            given = inputs() if callable(inputs) else inputs
        except container.Gap as gap:
            return {**container.declared(record, image, command, gap), "engine": "modal"}
        scratch.mkdir(parents=True)
        digest = container.copy_perimeter(Path(project), scratch / "copy.tar", given)
        volume.commit()
        base = modal.Image.from_registry(image)
        if prepare:
            boxes.append(modal.Sandbox.create(image=base, **options))
            row = _phase(boxes[-1], "prepare", f"{unpack} && mkdir -p \"$HOME\" && exec {shlex.join(prepare)}",
                         env, prepare_timeout, out_dir)
            container.append_record(record, {**row, "image": image, "command": list(prepare), "copy": digest})
            if row["outcome"] != "exited" or row["exit_code"] != 0:
                result["cause"] = row.get("cause") or f"preparation {row['outcome']} with code {row['exit_code']}"
                return result
            base, unpack = boxes[-1].snapshot_filesystem(), f"cd {container.WORKDIR}"
            boxes.pop().terminate()
        boxes.append(modal.Sandbox.create(image=base, block_network=True, **options))
        row = _phase(boxes[-1], "execute", f"{unpack} && exec {shlex.join(command)}", env, timeout, out_dir)
        container.append_record(record, {**row, "image": image, "command": list(command), "copy": digest})
        if outputs and row["outcome"] != "failed":
            pack = " ; ".join(f"[ -e {shlex.quote(path)} ] && tar -rf {PACKED} -C {shlex.quote(posixpath.dirname(path))}"
                              f" {shlex.quote(posixpath.basename(path))}" for path in outputs)
            boxes[-1].exec("sh", "-c", f"rm -f {PACKED} ; {pack} ; [ -e {PACKED} ] || tar -cf {PACKED} -T /dev/null").wait()
            with tarfile.open(fileobj=io.BytesIO(boxes[-1].filesystem.read_bytes(PACKED))) as bundle:
                members = [m for m in bundle.getmembers() if m.isfile() or m.isdir()]
                bundle.extractall(out_dir, members=members, filter="data")
                result["outputs"] = [str(out_dir / m.name) for m in members if m.isfile()]
        result.update(exit_code=row.get("exit_code"),
                      state={"exited": "done", "timeout": "timeout"}.get(row["outcome"], "failed"))
        if "cause" in row:
            result["cause"] = row["cause"]
        return result
    except Exception as error:  # noqa: BLE001 - as `run_in_container`: a run that cannot happen says why
        result["cause"] = f"{type(error).__name__}: {error}"
        return result
    finally:
        for box in boxes:
            try:
                box.terminate()
            except Exception:  # noqa: BLE001, S110 - already gone
                pass
        shutil.rmtree(scratch, ignore_errors=True)
        volume.commit()


def engine_on_modal(container) -> None:
    """`container`, the plugin's module, with its runs on Modal Sandboxes."""
    container.run_in_container = sandbox_run  # `run_commands` and every analyzer call it by this name
    container.find_engine = lambda **_: container.Engine("modal", ())


# An analyzer's stage is a process of its own: this `sitecustomize`, on its path, gives it the same engine.
SITE = """import importlib.machinery, sys


class Finder:
    @staticmethod
    def find_spec(name, path=None, target=None):
        if name != "container":
            return None
        spec = importlib.machinery.PathFinder.find_spec(name, path)
        if spec is not None:
            load = spec.loader.exec_module

            def exec_module(module):
                load(module)
                import modal_pipeline
                modal_pipeline.engine_on_modal(module)

            spec.loader.exec_module = exec_module
        return spec


sys.meta_path.insert(0, Finder)
"""


def _project(name: str) -> Path:
    """The case's project under /cases: a corpus fixture, or a real repository's clone from its archive."""
    fixture, project = Path(REMOTE_PM) / "fixtures" / name, Path("/cases") / name
    shutil.rmtree(project, ignore_errors=True)
    project.parent.mkdir(parents=True, exist_ok=True)
    if (fixture / "source.json").is_file():
        with tempfile.TemporaryDirectory() as part:
            with tarfile.open(Path("/results/project-model/native-real") / f"{name}.tar.gz") as tar:
                tar.extractall(part, filter="tar")
            shutil.move(str(Path(part) / name), str(project))
    else:
        shutil.copytree(fixture, project, ignore=shutil.ignore_patterns("expected.json", "source.json"))
    return project


# A request and a limit: the function mostly waits for its sandboxes, and is billed for what it uses above the request.
@app.function(cpu=(0.5, 8.0), memory=(2048, 16384), timeout=7200, volumes={"/results": volume})
def run_cases(names: list) -> dict:
    sys.path[:0] = [REMOTE_SCRIPTS, REMOTE_PM]
    import container
    import pipeline
    import premap
    import score as scorer
    import snapshot
    engine_on_modal(container)
    site = Path("/site")
    site.mkdir(exist_ok=True)
    (site / "sitecustomize.py").write_text(SITE, encoding="utf-8")
    # uv gives a stage its own environment: Modal's client is installed in it, and this driver reaches it by the path
    os.environ["PYTHONPATH"] = os.pathsep.join([str(site), str(Path(__file__).resolve().parent)])
    import engine_pass
    stage_command = engine_pass.stage_command

    def with_modal(*args, **options):
        argv = stage_command(*args, **options)
        if argv and argv[1:2] == ["run"]:
            argv[2:2] = ["--with", f"modal=={modal.__version__}"]
        return argv

    engine_pass.stage_command = with_modal
    out = {}
    for name in names:
        started = time.monotonic()
        try:
            project = _project(name)
            manifest = Path("/runs") / name / "manifest.sqlite"
            shutil.rmtree(manifest.parent, ignore_errors=True)
            snapshot.write_snapshot(project, manifest)
            seen, clock = [], {}

            def listen(event, seen=seen, clock=clock, started=started):
                seen.append(event["kind"])
                if event["kind"].startswith("step."):
                    clock.setdefault(event["step"], []).append(round(time.monotonic() - started, 1))

            steps = pipeline.run(manifest, listeners=[listen])
            record = json.loads(premap.path(manifest).read_text(encoding="utf-8"))
            expected = json.loads((Path(REMOTE_PM) / "fixtures" / name / "expected.json").read_text(encoding="utf-8"))
            runs = [json.loads(line) for file in sorted(manifest.parent.rglob(container.RECORD_NAME))
                    for line in file.read_text(encoding="utf-8").splitlines() if line.strip()]
            out[name] = {"premap": scorer.score(expected, record), "sources": record["sources"],
                         "gaps": record["gaps"], "units": len(record["units"]), "toolchains": record.get("toolchains", []),
                         "steps": json.loads(json.dumps(steps, default=str)),
                         "events": dict(collections.Counter(seen)), "step_seconds": clock,
                         "containers": [{key: run.get(key) for key in ("phase", "image", "outcome", "exit_code",
                                                                        "duration_seconds", "cause")} for run in runs],
                         "logs": {file.name: file.read_text(encoding="utf-8", errors="replace")[-3000:]
                                  for file in sorted(manifest.parent.glob("engine-pass*.log"))},
                         "seconds": round(time.monotonic() - started, 1)}
        except Exception as error:  # noqa: BLE001 - a case's failure is its result
            import traceback
            out[name] = {"error": f"{type(error).__name__}: {error}", "trace": traceback.format_exc()[-1500:],
                         "seconds": round(time.monotonic() - started, 1)}
    return out


@app.local_entrypoint()
def main(cases: str = "", out: str = "", chunk: int = 4):
    fixtures = sorted(p.name for p in (HERE / "fixtures").iterdir() if (p / "expected.json").is_file())
    real = {n for n in fixtures if (HERE / "fixtures" / n / "source.json").is_file()}
    batches = []
    for spec in filter(None, cases.split(",")):
        if spec in FAMILIES:  # a family in groups of `chunk`, each in a container of its own: billed the same
            family = [n for n in fixtures if n.startswith(spec + "-") and n not in real]
            batches += [family[i:i + chunk] for i in range(0, len(family), chunk)]
        elif spec == "real":
            batches += [[n] for n in sorted(real)]
        else:
            batches.append([spec])
    results = {}
    for answer in run_cases.map(batches, return_exceptions=True):
        if isinstance(answer, Exception):
            print("a container failed:", answer, flush=True)
            continue
        results.update(answer)
        for name, result in answer.items():
            print(name, result.get("error") or {key: result[key] for key in ("units", "seconds")}, flush=True)
    Path(out).write_text(json.dumps(results, indent=1), encoding="utf-8")
    print("ran", len(results), "->", out, flush=True)
