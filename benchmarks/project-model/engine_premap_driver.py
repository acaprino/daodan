"""Runs INSIDE the VM Sandbox of `modal_premap.py --score` and `--store`, where a real Docker daemon answers: the pre-map of
each fixture with the product's own launcher, `container_runner.runner(manifest)`, called as the pipeline's step calls it
(`pipeline._runner`: the commands and the toolchains), within one analysis (`node_preparation.analysis`,
`egress.analysis`, as `pipeline.run`). Every model command runs in Daodan's container behind its proxy, the preparation
and the execution alike (`T1.F.3`): the canonical registries and the approved hosts open, any other host a request.

Nobody answers here, as in MCP and on the command line (no `egress.ANSWERS`): the proxy refuses a host outside the list at
once and the request stays (`egress.pending`); each fixture's result keeps them (`egress.groups`). The answers are per
fixture in `egress-answers.json` (`{fixture: [host]}`), given as «Sempre» for the fixture's project before it runs
(`egress.respond`): the fixture is laid out as a checkout of the app (`/work/<fixture>/c/source`), so the answer is kept in
its project file (`egress.project_file_of`).

argv[1] is `{"mode": "score" | "store", "names": [...]}`. A line `START {code, versions}` comes first; each fixture's
answer is written to `/runs/out/<name>.json`, then a line `DONE <name>`: `modal_premap.py` reads it at once, so a sandbox
that ends past its time loses only the fixtures after it. `lay_out` and `code_hash` serve `modal_premap.py`'s other
functions too; nothing runs on import.
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
import traceback
from pathlib import Path

CORE, PM = Path("/daodan/map/core"), Path("/pm")  # container paths, the same in both images of `modal_premap.py`
ARCHIVES = Path("/results/project-model/native-real")  # the real repositories' clones `modal_native.py prepare` keeps
OUT = Path("/runs/out")
CODE = ("container.py", "container_runner.py", "egress.py", "preparation.py", "node_preparation.py")  # what runs them


def code_hash(drivers: list[Path], core: Path) -> str:
    """The hash of the drivers, of `premap/` and of the modules that run its commands: the same on both sides."""
    digest = hashlib.sha256()
    for file in [*drivers, *sorted((core / "premap").glob("*.py")), *(core / name for name in CODE)]:
        digest.update(file.name.encode() + b"\0" + file.read_bytes().replace(b"\r\n", b"\n"))
    return digest.hexdigest()[:16]


def lay_out(name: str, project: Path, files: dict | None = None) -> Path:
    """The fixture `name` at `project`: the `files` of a case of `projects.json`; a hand-written fixture copied whole,
    `expected.json` too, with no Git, as the reference always laid it out; a real one (`source.json`) its clone at the
    pinned commit, from the archive on the volume, else cloned here (shallow), as `modal_stack.py` does."""
    shutil.rmtree(project, ignore_errors=True)
    project.parent.mkdir(parents=True, exist_ok=True)
    fixture = PM / "fixtures" / name
    if files is not None:
        for rel, text in files.items():
            (project / rel).parent.mkdir(parents=True, exist_ok=True)
            (project / rel).write_text(text, encoding="utf-8", newline="\n")
        return project
    if not (fixture / "source.json").is_file():
        shutil.copytree(fixture, project)
        return project
    archive = ARCHIVES / f"{name}.tar.gz"
    if archive.is_file():
        part = project.parent / f".part-{name}"
        shutil.rmtree(part, ignore_errors=True)
        with tarfile.open(archive) as tar:
            tar.extractall(part, filter="tar")
        (part / name).rename(project)
        shutil.rmtree(part)
        return project
    source = json.loads((fixture / "source.json").read_text(encoding="utf-8"))
    project.mkdir()
    for argv in (["git", "init", "-q"], ["git", "remote", "add", "origin", source["repo"]],
                 ["git", "fetch", "-q", "--depth", "1", "origin", source["commit"]], ["git", "checkout", "-q", "FETCH_HEAD"]):
        done = subprocess.run(argv, cwd=project, capture_output=True, text=True, timeout=900,
                              env={**os.environ, "GIT_TERMINAL_PROMPT": "0"})
        if done.returncode:
            raise RuntimeError(f"{' '.join(argv[:3])}: {done.stderr.strip()[-300:]}")
    return project


def logged(run, log: list):
    """The product's runner, each command it answered kept with its answer: what `tools/premap_replay.py` and the
    readers' tests replay. A source the runner does not start (`container.Gap`: a host of its tool nobody answered,
    `egress.preflight`) keeps none."""
    def by_tool(commands: list[dict], toolchains: list[dict] = ()) -> list[dict]:
        answers = run(commands, toolchains)
        log.extend({"command": command, "result": answer} for command, answer in zip(commands, answers))
        return answers
    by_tool.uses_default_container = run.uses_default_container
    return by_tool


def one(name: str, files: dict | None, answered: list[str]) -> dict:
    """The pre-map of one fixture through the product's runner; with `files` (`--store`) only its commands' answers."""
    import container_runner
    import egress
    import node_preparation
    import premap
    import snapshot
    folder = Path("/work") / name
    project = lay_out(name, folder / "c" / "source", files)  # a checkout of the app: «Sempre» lands in its project file
    manifest = folder / "out" / "manifest.sqlite"
    shutil.rmtree(manifest.parent, ignore_errors=True)
    (folder / "project.daodan").unlink(missing_ok=True)
    started = time.monotonic()
    snapshot.read_project(project, manifest)
    graph = None
    if files is None:
        import modules
        graph = modules.load_graph(Path(modules.ensure_graph(manifest)["graph"]))
    middle = time.monotonic()
    named = egress.project_of(manifest)
    for host in answered:
        egress.respond(host, named, "always")
    log: list = []
    with node_preparation.analysis(), egress.analysis(named):
        record = premap.write(manifest, runner=logged(container_runner.runner(manifest), log))
    said = {"answered": answered, "requests": egress.groups([named])}
    if files is not None:
        return {"runs": log, "egress": said}
    import daodan_modules
    import score as scorer
    expected = json.loads((PM / "fixtures" / name / "expected.json").read_text(encoding="utf-8"))
    return {"base": scorer.score(expected, daodan_modules.convert(graph)), "premap": scorer.score(expected, record),
            "sources": record["sources"], "gaps": record["gaps"], "output": record, "egress": said, "runs": log,
            "seconds": {"snapshot_and_graph": round(middle - started, 2), "premap": round(time.monotonic() - middle, 2)}}


def main() -> None:
    job = json.loads(sys.argv[1])
    sys.path[:0] = [str(CORE), str(PM), str(PM / "tools")]
    os.environ["PATH"] = "/opt/docker:" + os.environ["PATH"]
    os.environ["DAODAN_SHARED_DIR"] = "/runs/shared"  # egress' requests and answers, the tools' downloads
    os.environ.pop("DAODAN_CONTAINER", None)
    import container
    import container_runner
    import egress
    os.environ.pop(egress.ANSWERS, None)  # nobody answers: refused at once, the request stays
    docker = subprocess.run(["docker", "version", "--format", "{{.Server.Version}}"], capture_output=True, text=True)
    versions = {"engine": container.find_engine().name, "docker": docker.stdout.strip(), "image": container_runner.IMAGE}
    print("START", json.dumps({"code": code_hash([PM / "modal_premap.py", Path(__file__)], CORE), "versions": versions}),
          flush=True)
    answers = json.loads((PM / "egress-answers.json").read_text(encoding="utf-8"))
    cases = json.loads((PM / "projects.json").read_text(encoding="utf-8")) if job["mode"] == "store" else {}
    OUT.mkdir(parents=True, exist_ok=True)
    for name in job["names"]:
        began = time.monotonic()
        try:
            result = one(name, cases[name] if job["mode"] == "store" else None, list(answers.get(name, [])))
        except Exception as error:  # noqa: BLE001 - a fixture's failure is its result
            result = {"error": f"{type(error).__name__}: {error}", "trace": traceback.format_exc()[-1500:]}
        (OUT / f"{name}.json").write_text(json.dumps(result, default=str), encoding="utf-8")
        print("DONE", name, round(time.monotonic() - began, 1), flush=True)


if __name__ == "__main__":
    main()
