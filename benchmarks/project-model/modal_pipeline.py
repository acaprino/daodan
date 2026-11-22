"""The whole pipeline on Modal: snapshot, scan (the pre-map with its build tools), analyzers and union.

Nothing runs on this PC. A Modal function holds the plugin's scripts, with the data they read beside them, and
runs `pipeline.run` on each case; where the pipeline asks for a container (`container.run_in_container`), the
function starts a Modal Sandbox from the same image, pinned by the same digest:

- the copy of the project and its inputs travel on the volume `daodan-flow-results` and are unpacked at `/`;
- with a preparation, a first sandbox runs it with the network open (Modal's allowlist is by address, not by
  host: the registries-only proxy of Daodan's container is not reproduced here), its filesystem is snapshotted
  and a second sandbox starts from the snapshot with the network blocked for the execution;
- without one, a single sandbox with the network blocked;
- a run whose execution starts Valgrind (the native observers) takes VM Sandboxes (`vm`): Valgrind grows a
  program's stack only on Linux's SEGV_MAPERR, and gVisor reports SEGV_ACCERR;
- with services (`container.beside`), both are VM Sandboxes, where Docker runs
  (modal.com/docs/guide/docker-in-sandboxes; a gVisor sandbox has no Docker and mounts nothing, and a Sidecar is
  reached by name on a bridge that `block_network` does not allow): the first, with the network, starts Docker's static binaries (`DOCKER`, from the volume),
  pulls each image and pins it by its digest (`container.pin`); the second, network blocked, starts Docker again
  and each service with `--network host`, the sandbox's own namespace, awaited before the tests
  (`container.start_services`): they reach it at localhost, and nothing outside;
- the declared outputs come back, a tar each made by the image's own tar (BusyBox's has no -r and one -C), into
  the run's folder, as `container.fetch` leaves them.

A family's fixtures run in groups of `--chunk` (4), each group in a function call of its own; each real repository (its clone from the archive `modal_native.py
prepare` keeps on the volume) has its own. Per case the result holds the pre-map's score against
`expected.json`, each source's state, the gaps, each step's result, the dynamic step's gaps, the events by kind and the seconds.
Beside the cases, `code` names the Daodan code the round ran (`code`): the checkout's commit, the tree of the copy
it uploaded and the paths where the two differ.

    python -m modal run benchmarks/project-model/modal_pipeline.py --cases js-npm-single,sys-meson --out OUT.json
    python -m modal run benchmarks/project-model/modal_pipeline.py --cases js,py,jvm,sys,mix,real --out OUT.json
    DAODAN_FOLDER=<folder> python -m modal run benchmarks/project-model/modal_pipeline.py --folder-out DIR

The last form runs the pipeline on a folder of this PC and brings its snapshot, pre-map, edge store and events
back into DIR; `--folder-stop analyze` ends it after that step, without the tests of the dynamic step.
"""
from __future__ import annotations

import collections
import hashlib
import io
import json
import os
import posixpath
import shlex
import shutil
import subprocess
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
REMOTE_SCRIPTS = "/daodan/map/core"  # container paths: POSIX strings, whatever runs the client
REMOTE_PM = "/pm"
REMOTE_FOLDER = "/folder"
SCRATCH = "project-model/pipeline-scratch"  # on the volume: each run's copy, removed when the run ends
FAMILIES = ("js", "py", "jvm", "sys", "mix")
PACKED = "/tmp/daodan-outputs.tar"
SANDBOX_CPU = 2.0  # cores a build or an indexer is given: the default share would throttle Gradle and CMake
DOCKER = ("https://download.docker.com/linux/static/stable/x86_64/docker-29.10.0.tgz",
          "7c1ebadc65c716cdc6d35fc78759ed0e4317debf43c21dd12f066f2006999def")  # the services' engine in a sandbox
ENGINE = "/daodan/engine"  # where its binaries lie in a sandbox
VM = {"vm_runtime": True}  # the `experimental_options` of a VM Sandbox (client 1.5: no `runtime` argument yet)

SCRIPTS, DATA = "daodan/core", "daodan/data"
REMOTE_DATA = "/daodan/map/data"  # the scripts read it beside their folder (`service_registry.REGISTRY`)
# what a round uploads, each with its path in the repository: DAODAN_SCRIPTS names the tool's scripts to run when
# not the checkout's (a committed copy while files are edited), with the data beside them; the driver itself goes
# with its function
_scripts = Path(os.environ.get("DAODAN_SCRIPTS") or REPO / SCRIPTS)
UPLOADED = ((_scripts, SCRIPTS), (_scripts.parent / "data", DATA),
            (HERE / "fixtures", "benchmarks/project-model/fixtures"),
            (HERE / "score.py", "benchmarks/project-model/score.py"),
            (HERE / "modal_pipeline.py", "benchmarks/project-model/modal_pipeline.py"))

image = (modal.Image.debian_slim(python_version="3.13")
         .apt_install("git", "ca-certificates", "xz-utils")
         .pip_install("uv", "tree-sitter==0.26.0", "tree-sitter-language-pack==1.13.5", "sqlglot>=30", "PyYAML>=6"))
if LOCAL:
    image = (image.add_local_dir(UPLOADED[0][0], REMOTE_SCRIPTS, ignore=["**/__pycache__/**"])
             .add_local_dir(UPLOADED[1][0], REMOTE_DATA)
             .add_local_dir(UPLOADED[2][0], f"{REMOTE_PM}/fixtures")
             .add_local_file(UPLOADED[3][0], f"{REMOTE_PM}/score.py"))
    if os.environ.get("DAODAN_FOLDER"):  # a folder of this PC as one more case (`--folder-out`)
        image = image.add_local_dir(os.environ["DAODAN_FOLDER"], REMOTE_FOLDER,
                                    ignore=["**/__pycache__/**", "**/node_modules/**", "**/.git/**"])
app = modal.App("daodan-pipeline", image=image)
volume = modal.Volume.from_name("daodan-flow-results")


def code(repo: Path, parts) -> dict:
    """The Daodan code a round runs: the checkout's `commit`, the `tree` git makes of the copy it uploads (`parts`,
    each a local file or folder and its path in the repository: what git tracks or would, with the checkout's line
    endings, `__pycache__` aside, wherever the copy lies) and the paths where that copy `differs` from the commit."""
    def git(*args, index: str = "index", cwd: Path = repo) -> str:
        return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True,
                              env={**os.environ, "GIT_INDEX_FILE": str(Path(temp) / index)}).stdout.strip()

    skip = ":(exclude,glob)**/__pycache__/**"
    with tempfile.TemporaryDirectory() as temp:
        commit, store = git("rev-parse", "HEAD"), git("rev-parse", "--absolute-git-dir")
        for local, rel in parts:
            if Path(local).resolve() == (repo / rel).resolve():
                git("add", "-A", "--", rel, skip)
            else:  # elsewhere: its own tree, read under its path
                git(f"--git-dir={store}", f"--work-tree={local}", "-c",
                    f"core.attributesFile={repo / '.gitattributes'}", "add", "-A", "--", ".", skip, index="own",
                    cwd=Path(local))
                git("read-tree", f"--prefix={rel}/", git("write-tree", index="own"))
        tree = git("write-tree")
        differs = git("diff-index", "--cached", "--name-only", commit, "--", *(rel for _, rel in parts))
    return {"commit": commit, "tree": tree, "differs": differs.splitlines()}


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


def _bundle() -> str:
    """Docker's static binaries on the volume, downloaded once and checked by their sha256: the path a sandbox
    reads them at."""
    import urllib.request
    path = Path("/results/project-model") / Path(DOCKER[0]).name
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != DOCKER[1]:
        path.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(DOCKER[0], timeout=600) as answer:
            data = answer.read()
        if hashlib.sha256(data).hexdigest() != DOCKER[1]:
            raise RuntimeError(f"{DOCKER[0]} has not the sha256 {DOCKER[1]}")
        path.write_bytes(data)
        volume.commit()
    return str(path)


def _docker(box):
    """Docker's command line in `box`, answered as `container.cli` answers; `stdin` a file it reads."""
    def run(*args, timeout=300, stdin=None):
        process = box.exec(f"{ENGINE}/docker", *args, timeout=int(timeout), text=False)
        if stdin is not None:
            process.stdin.write(stdin.read())
            process.stdin.write_eof()
            process.stdin.drain()
        out, err = process.stdout.read(), process.stderr.read()
        code = process.wait()
        if code == -1:
            raise subprocess.TimeoutExpired([f"{ENGINE}/docker", *args], timeout)
        return subprocess.CompletedProcess(list(args), code, out, err)
    return run


def _daemon(box, bundle: str | None = None) -> None:
    """Docker's daemon running in `box`, its binaries unpacked from `bundle` first: no bridge and no iptables,
    since a service shares the sandbox's network."""
    if bundle:
        unpacked = box.exec("sh", "-c", f"mkdir -p {ENGINE} && tar -xzf {bundle} -C {ENGINE} --strip-components=1")
        if unpacked.wait() != 0:
            raise RuntimeError(f"Docker's binaries did not unpack: {unpacked.stderr.read().strip()[-300:]}")
    box.exec("sh", "-c", f"PATH={ENGINE}:$PATH exec dockerd --iptables=false --ip6tables=false --bridge=none"
                         " > /tmp/dockerd.log 2>&1")
    for _ in range(120):
        if box.exec(f"{ENGINE}/docker", "info", timeout=30).wait() == 0:
            return
        time.sleep(0.5)
    raise RuntimeError("Docker's daemon did not start in the sandbox: "
                       + box.exec("tail", "-c", "300", "/tmp/dockerd.log").stdout.read().strip())


def _quiet(box) -> None:
    """Docker's daemon stopped before a snapshot, so the images it keeps are whole on disk."""
    box.exec("sh", "-c", "p=$(cat /var/run/docker.pid) && kill $p && while kill -0 $p 2>/dev/null; do sleep 0.2;"
                         " done", timeout=120).wait()


def _hosts(box, pinned) -> None:
    """The names the services are reached by, other than localhost, at 127.0.0.1 in `box`, as the pod's hosts
    name them."""
    for name in sorted({name for s in pinned for name in (s.get("host"), *s.get("aliases", ()))
                        if name not in (None, "localhost")}):
        box.exec("sh", "-c", f"echo 127.0.0.1 {shlex.quote(name)} >> /etc/hosts").wait()


def _dotenv(token: str, files: list, options: dict) -> tuple[dict, set]:
    """`container.dotenv_values` on Modal: `container.RESOLVE` in a Sandbox of Python's with no network, over the
    tracked files of this run's copy on the volume that `reader.list` names (the .env files and the others, where
    their values may stand)."""
    import container
    box = modal.Sandbox.create(image=modal.Image.debian_slim(python_version="3.13"), block_network=True,
                               app=options["app"], volumes=options["volumes"], timeout=600, cpu=0.25, memory=256)
    try:
        scratch = f"/results/{SCRATCH}/{token}"
        process = box.exec("sh", "-c", f"tar -xf {scratch}/copy.tar -C / --verbatim-files-from --null -T "
                           f"{scratch}/reader.list && cd {container.WORKDIR} && DAODAN_PUBLIC="
                           f"{container.PUBLIC_SECONDS} exec python3 -c {shlex.quote(container.RESOLVE)} "
                           + " ".join(map(shlex.quote, files)), timeout=container.PUBLIC_SECONDS + 300)
        said = process.stdout.read()
        return container.dotenv_answer(said, process.wait()), container.published(said)
    finally:
        box.terminate()


def vm(command, services) -> bool:
    """Whether a run takes a VM Sandbox, with a Linux kernel of its own: with services (Docker runs only there), or
    when its execution starts Valgrind (the Rust and the C and C++ observers, `dynamic/callgrind.py`), which grows a
    program's stack only on Linux's SEGV_MAPERR, where gVisor reports SEGV_ACCERR."""
    from dynamic import callgrind
    return bool(services) or callgrind.VALGRIND_BIN in " ".join(command)


def sandbox_run(project, command, *, image, out_dir, prepare=None, outputs=(), env=None, timeout=600,
                prepare_timeout=1800, memory=2 * 2**30, inputs=None, dotenv_env=(), blind=False, node_restore=None,
                **_):
    """`container.run_in_container` on Modal Sandboxes: the same arguments and result (the module's docstring),
    `container.beside`'s services, variables and steps included. With steps and services, the services start in
    the preparation's sandbox, the steps beside them, and start again from what they kept (the snapshot holds
    Docker's own folders) beside the tests. `node_restore`, the restore an analysis shares between its runs
    (`node_preparation`), runs here in each run's own preparation sandbox, before `prepare`: no volume passes from
    one sandbox to the next, so a round on Modal does not measure the sharing."""
    import container
    out_dir = Path(out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    record = out_dir / container.RECORD_NAME
    result = {"state": "failed", "exit_code": None, "outputs": [], "record": str(record), "engine": "modal"}
    token = uuid.uuid4().hex[:12]
    scratch = Path("/results") / SCRATCH / token
    services, variables, steps, said = container.BESIDE.get() or ((), {}, (), container.Said([], []))
    if steps and not prepare:  # they run at the end of a preparation, which this run has not
        result["ci_steps"] = [{"declared_in": step["declared_in"], **({"name": step["name"]} if step.get("name") else {}),
                               "outcome": "not_run", "exit_code": None, "duration_seconds": 0,
                               "cause": "the run has no preparation, at whose end Daodan runs the CI's steps"}
                              for step in steps]
        said.ci_steps.extend(result["ci_steps"])
    steps = list(steps) if prepare else []
    env = {**variables, **(env or {})}
    env = {"HOME": container.HOME, **env} if prepare else env
    options = {"app": modal.App.lookup("daodan-pipeline-sandboxes", create_if_missing=True),
               "volumes": {"/results": volume},
               "memory": int(memory / 2**20), "cpu": SANDBOX_CPU, "timeout": int(prepare_timeout + timeout + 900),
               **({"experimental_options": VM} if vm(command, services) else {})}
    unpack = f"tar -xf /results/{SCRATCH}/{token}/copy.tar -C / && mkdir -p {container.WORKDIR} && cd {container.WORKDIR}"
    boxes, pinned, served, kept = [], [], [], False  # `kept`: the services started beside the steps
    limits = {"memory": int(memory), "pids": 1024}
    hide = None  # the masks of the tracked .env files' values (`container.masker`)

    def failed(items, error) -> list[dict]:
        cause = f"{type(error).__name__}: {error}"
        return [{"phase": "service", "name": s["name"], "image": s["image"], "outcome": "failed", "cause": cause,
                 **{key: s[key] for key in ("pinned",) if key in s}} for s in items]

    try:
        try:
            given = inputs() if callable(inputs) else inputs
        except container.Gap as gap:
            return {**container.declared(record, image, command, gap), "engine": "modal"}
        bundle = None
        if services:  # on the volume before a sandbox mounts it
            try:
                bundle = _bundle()
            except (OSError, RuntimeError) as error:
                served += failed(services, error)
        scratch.mkdir(parents=True)
        digest = container.copy_perimeter(Path(project), scratch / "copy.tar", given)
        if digest["gaps"]:  # what the copy left out of the project, as `run_in_container` says it
            result["gaps"] = digest["gaps"]
        read = digest.get("dotenv") and not (blind and not services and not dotenv_env)  # as `run_in_container`
        if read:  # what the reader of the .env files reads (`container.dotenv_values`), beside the copy
            (scratch / "reader.list").write_bytes(b"".join(f"work/{rel}".encode() + b"\0"
                                                           for rel in (*digest["dotenv"], *digest["published"])))
        volume.commit()
        values, public = _dotenv(token, digest["dotenv"], options) if read else ({}, set())
        secret = container.secret(values, public)
        hide = container.masker(secret)
        if said_partial := container.partial(secret):  # what the masks leave, said once
            result["gaps"] = [*(result.get("gaps") or ()), *said_partial]
        services = [container.filled(item, values) for item in services]  # the values only here, never on record
        exported = {name: values[file][name] for name, file in dotenv_env if name in values.get(file, {})}
        base = modal.Image.from_registry(image)
        if prepare or bundle or node_restore:
            boxes.append(modal.Sandbox.create(image=base, **options))
            if node_restore:  # as `node_preparation._seed` and `clone`: the tools stay the restore's own
                import preparation
                hidden = container.named() if blind and digest.get("dotenv") else ""
                row = _phase(boxes[-1], "node-restore", f"{unpack} && sh -ec {shlex.quote(hidden + node_restore['script'])}"
                             f" && rm -rf {preparation.T}", preparation.ENV, prepare_timeout, out_dir)
                container.mask_file(row["log"], hide)
                container.append_record(record, {**container.mask_row(row, hide), "image": image})
                if row["outcome"] != "exited" or row["exit_code"] != 0:
                    result["cause"] = row.get("cause") or "Node dependency preparation failed (node-restore.log)"
                    return result
                log = Path(row["log"]).read_text(encoding="utf-8", errors="replace")
                restore_gaps = [*preparation.missing(log), *preparation.restore_gaps(log),
                                *preparation.generation_gaps(log)]
                if restore_gaps:
                    result["gaps"] = [*(result.get("gaps") or ()), *restore_gaps]
                unpack = f"cd {container.WORKDIR}"  # the copy is there, with what the restore added
            if bundle:  # pulled with the network, before anything of the project runs
                try:
                    _daemon(boxes[-1], bundle)
                    for service in services:
                        try:
                            pinned.append({**service, "pinned": container.pin(_docker(boxes[-1]), service["image"],
                                                                              prepare_timeout)})
                        except (RuntimeError, subprocess.TimeoutExpired) as error:
                            served += failed([service], error)
                    if any(s.get("wait") == "ports" for s in pinned):  # the image their ports are asked from
                        container.pin(_docker(boxes[-1]), container.PROXY_IMAGE, prepare_timeout)
                    if steps and pinned:  # the services beside the steps, as they will be beside the tests
                        _hosts(boxes[-1], pinned)
                        early = container.start_services(_docker(boxes[-1]), pinned, "host", limits, token,
                                                         copy=scratch / "copy.tar")
                        for item in early:
                            container.append_record(record, {**container.mask_row(item, hide), "engine": "modal"})
                        unready = {item["name"] for item in early if item["outcome"] != "ready"}
                        served += [item for item in early if item["name"] in unready]
                        pinned, kept = [s for s in pinned if s["name"] not in unready], True
                    else:
                        _quiet(boxes[-1])
                except (RuntimeError, subprocess.TimeoutExpired) as error:
                    told = {item["name"] for item in served}
                    served += failed([s for s in services if s["name"] not in told], error)
                    pinned = []
            if prepare:
                run = ["sh", "-c", container.steps_script(steps, timeout, token), "sh", *prepare] if steps else prepare
                row = _phase(boxes[-1], "prepare", f"{unpack} && mkdir -p \"$HOME\" && exec {shlex.join(run)}",
                             {**env, **exported}, prepare_timeout + (timeout if steps else 0), out_dir)
                container.mask_file(row["log"], hide)
                container.append_record(record, {**container.mask_row(row, hide), "image": image,
                                                 "command": list(prepare), "copy": digest})
                for item in container.stepped(Path(row["log"]).read_text(encoding="utf-8", errors="replace")
                                              if Path(row["log"]).is_file() else "", steps, token, timeout):
                    container.append_record(record, {**container.mask_row(item, hide), "engine": "modal"})
                    result.setdefault("ci_steps", []).append({key: item[key] for key in item if key != "phase"})
                said.ci_steps.extend(result.get("ci_steps", ()))
                if row["outcome"] != "exited" or row["exit_code"] != 0:
                    result["cause"] = row.get("cause") or f"preparation {row['outcome']} with code {row['exit_code']}"
                    return result
                unpack = f"cd {container.WORKDIR}"
            if kept:
                _quiet(boxes[-1])  # the services stop with the daemon, their data in its folders
            base = boxes[-1].snapshot_filesystem()
            boxes.pop().terminate()
        boxes.append(modal.Sandbox.create(image=base, block_network=True, **options))
        if pinned:
            try:
                _daemon(boxes[-1])
                _hosts(boxes[-1], pinned)
                served += container.start_services(_docker(boxes[-1]), pinned, "host", limits, token,
                                                   copy=scratch / "copy.tar", created=kept)
            except (RuntimeError, subprocess.TimeoutExpired) as error:
                served += failed(pinned, error)
        for item in served:
            container.append_record(record, {**container.mask_row(item, hide), "engine": "modal"})
        if services:
            result["services"] = [{key: item[key] for key in ("name", "image", "pinned", "outcome", "cause")
                                   if key in item} for item in served]
            said.services.extend(result["services"])
        row = _phase(boxes[-1], "execute", f"{unpack} && exec {shlex.join(command)}", {**env, **exported}, timeout,
                     out_dir)
        container.mask_file(row["log"], hide)
        container.append_record(record, {**container.mask_row(row, hide), "image": image, "command": list(command),
                                         "copy": digest})
        if outputs and row["outcome"] != "failed":
            for number, path in enumerate(outputs):  # a tar each: the image's own may be BusyBox's (no -r, one -C)
                packed = f"{PACKED}.{number}"
                pack = (f"[ -e {shlex.quote(path)} ] && tar -cf {packed} -C {shlex.quote(posixpath.dirname(path))}"
                        f" {shlex.quote(posixpath.basename(path))}")
                if boxes[-1].exec("sh", "-c", pack).wait() != 0:  # an output the run did not write
                    continue
                with tarfile.open(fileobj=io.BytesIO(boxes[-1].filesystem.read_bytes(packed))) as bundle:
                    members = [m for m in bundle.getmembers() if m.isfile() or m.isdir()]
                    bundle.extractall(out_dir, members=members, filter="data")
                    result["outputs"] += [str(out_dir / m.name) for m in members if m.isfile()]
            # no value of the tracked .env files in what the run keeps (`container.scrubbed`)
            result["outputs"], withheld = container.scrubbed(result["outputs"], hide, secret, out_dir)
            result["gaps"] = [*(result.get("gaps") or ()), *withheld]
        result.update(exit_code=row.get("exit_code"),
                      state={"exited": "done", "timeout": "timeout"}.get(row["outcome"], "failed"))
        if "cause" in row:
            result["cause"] = row["cause"]
        return result
    except Exception as error:  # noqa: BLE001 - as `run_in_container`: a run that cannot happen says why
        result["cause"] = f"{type(error).__name__}: {error}"
        return result
    finally:
        if hide and isinstance(result.get("cause"), str):
            result["cause"] = hide(result["cause"])
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


def _engine():
    """The plugin's `container` with its runs on Modal Sandboxes, in this process and in each stage's."""
    import container
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
    return container


KEPT = ("manifest.sqlite", "engine-edges.sqlite", "engine-report.json", "premap.json", "pipeline-events.jsonl",
        "modules.json", "technologies.json")


@app.function(cpu=(0.5, 8.0), memory=(2048, 16384), timeout=7200, volumes={"/results": volume})
def run_folder(stop: str | None = None) -> dict:
    """The pipeline on the folder of `DAODAN_FOLDER`, through the step `stop` (default: all): the steps' results,
    the events, and the run's files (`KEPT`) as a tar.gz, for whoever reads the graph on the PC."""
    sys.path[:0] = [REMOTE_SCRIPTS]
    import pipeline
    import snapshot
    _engine()
    project, manifest = Path("/cases/folder"), Path("/runs/folder/manifest.sqlite")
    shutil.rmtree(project, ignore_errors=True)
    shutil.rmtree(manifest.parent, ignore_errors=True)
    shutil.copytree(REMOTE_FOLDER, project)
    started, events = time.monotonic(), []
    snapshot.write_snapshot(project, manifest)

    def listen(event):
        if event["kind"] != "progress":
            events.append(f"{time.monotonic() - started:7.1f}s {event['kind']:22} {event.get('step') or '':8} "
                          f"{str(event.get('message') or '')[:160]}")

    steps = pipeline.run(manifest, listeners=[listen], stop=stop)
    packed = io.BytesIO()
    with tarfile.open(fileobj=packed, mode="w:gz") as bundle:
        for name in KEPT:
            if (manifest.parent / name).is_file():
                bundle.add(manifest.parent / name, arcname=name)
    return {"steps": json.loads(json.dumps(steps, default=str)), "events": events, "files": packed.getvalue(),
            "seconds": round(time.monotonic() - started, 1)}


# A request and a limit: the function mostly waits for its sandboxes, and is billed for what it uses above the request.
@app.function(cpu=(0.5, 8.0), memory=(2048, 16384), timeout=7200, volumes={"/results": volume})
def run_cases(names: list) -> dict:
    sys.path[:0] = [REMOTE_SCRIPTS, REMOTE_PM]
    import pipeline
    import premap
    import score as scorer
    import snapshot
    container = _engine()
    out = {}
    for name in names:
        started = time.monotonic()
        try:
            project = _project(name)
            manifest = Path("/runs") / name / "manifest.sqlite"
            shutil.rmtree(manifest.parent, ignore_errors=True)
            snapshot.write_snapshot(project, manifest)
            seen, clock, said = [], {}, []

            def listen(event, seen=seen, clock=clock, said=said, started=started):
                seen.append(event["kind"])
                if event["kind"] == "gap" and event["step"] == "dynamic":  # its gaps: no record keeps them
                    gap = (event.get("data") or {}).get("gap") or {}
                    said.append({key: gap[key] for key in ("kind", "path", "name", "image", "detail") if key in gap})
                if event["kind"].startswith("step."):
                    clock.setdefault(event["step"], []).append(round(time.monotonic() - started, 1))

            steps = pipeline.run(manifest, listeners=[listen])
            record = json.loads(premap.path(manifest).read_text(encoding="utf-8"))
            expected = json.loads((Path(REMOTE_PM) / "fixtures" / name / "expected.json").read_text(encoding="utf-8"))
            runs = [json.loads(line) for file in sorted(manifest.parent.rglob(container.RECORD_NAME))
                    for line in file.read_text(encoding="utf-8").splitlines() if line.strip()]
            out[name] = {"premap": scorer.score(expected, record), "sources": record["sources"],
                         "gaps": record["gaps"], "units": len(record["units"]), "toolchains": record.get("toolchains", []),
                         "steps": json.loads(json.dumps(steps, default=str)), "dynamic_gaps": said,
                         "events": dict(collections.Counter(seen)), "step_seconds": clock,
                         "containers": [{**{key: run.get(key) for key in ("phase", "image", "outcome", "exit_code",
                                                                          "duration_seconds", "cause")},
                                         **{key: run[key] for key in ("name", "declared_in") if key in run}}
                                        for run in runs],
                         "logs": {file.relative_to(manifest.parent).as_posix():
                                  file.read_text(encoding="utf-8", errors="replace")[-3000:]
                                  for pattern in ("engine-pass*.log", "premap-runs/*/prepare.log",
                                                  "premap-runs/*/results/*/stderr",
                                                  "premap-runs/*/results/0/stdout", "dynamic-runs/**/*.log")
                                  for file in sorted(manifest.parent.glob(pattern)) if file.stat().st_size},
                         "seconds": round(time.monotonic() - started, 1)}
        except Exception as error:  # noqa: BLE001 - a case's failure is its result
            import traceback
            out[name] = {"error": f"{type(error).__name__}: {error}", "trace": traceback.format_exc()[-1500:],
                         "seconds": round(time.monotonic() - started, 1)}
    return out


@app.local_entrypoint()
def main(cases: str = "", out: str = "", chunk: int = 4, folder_out: str = "", folder_stop: str = ""):
    if folder_out:  # the folder of DAODAN_FOLDER: its run's files into `folder_out`
        answer = run_folder.remote(folder_stop or None)
        target = Path(folder_out)
        target.mkdir(parents=True, exist_ok=True)
        with tarfile.open(fileobj=io.BytesIO(answer.pop("files"))) as bundle:
            bundle.extractall(target, filter="data")
        (target / "run.json").write_text(json.dumps(answer, indent=1), encoding="utf-8")
        for line in answer["events"]:
            print(line, flush=True)
        print("ran the folder in", answer["seconds"], "s ->", target, flush=True)
        return
    ran = code(REPO, UPLOADED)  # as uploaded when the app started, just before
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
    Path(out).write_text(json.dumps({"code": ran, **results}, indent=1), encoding="utf-8")
    print("ran", len(results), "->", out, flush=True)
