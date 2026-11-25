"""Angular's `parseTemplate` on Modal, in a container with the network blocked: the probes, and Daodan's source.

    PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal python -m modal run benchmarks/angular-compiler/modal_probe.py
    PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal python -m modal run benchmarks/angular-compiler/modal_probe.py --mode source
    REPO=<a public repository> COMMIT=<its commit> ... --mode measure

`--mode probes` (the default) runs the scripts of `probe/` (env `PROBES="01_html.mjs,02_inline.mjs"` picks some) in the
fixture's folder, with the project's packages restored from its lockfile while the image is built (the one moment the
network is open) and blocked when the scripts run; each script's output is written to `results/`.

`--mode source` runs what `daodan/core/premap/angular.py` runs in Daodan's container: the commands it gives for the
fixture (a function with the network open, where Daodan's grammar bundle comes from), then each command's script
(`daodan/core/premap/angular_templates.mjs`) with the network blocked, in a copy of the project with its packages and in
variants of it: without its packages (the project declares Angular and the restore did not install it), without
`@angular/compiler-cli`, without `tsconfig.json`, with a solution-style `tsconfig.json` (no file of its own, the project it
references holds them), and with the type-checker given 0.05 seconds. The same commands then run in an image of Angular 20
(packages installed while that image is built, from the registry: no lockfile). The answers, as the container runner returns
them (`returncode`, `stdout`, `stderr`), are written to `tests/fixtures/premap/angular/`, which
`tests/test_codebase_map_premap_angular.py` reads, with the sha256 of the script that produced them (`script.json`): if the
script changes, the answers are recorded again. `crlf.component.ts` is given Windows line ends here and in that test (git
keeps every text file with `\\n`).

`--mode measure` says what the source finds in a public repository at a commit: its components, its templates, the size of
the list the container is given.
"""
import os
import pathlib

import modal

HERE = pathlib.Path(__file__).resolve().parent
LOCAL = modal.is_local()  # in a container this file lies at /root: nothing below that reads the checkout runs there
REPO = HERE.parents[1] if LOCAL else HERE
FIX = HERE / "fixture"
OUT = HERE / "results"
RECORDED = REPO / "tests/fixtures/premap/angular"
ANGULAR20 = ("@angular/common@20 @angular/compiler@20 @angular/core@20 @angular/forms@20 @angular/platform-browser@20 "
             "@angular/router@20 @angular/compiler-cli@20 rxjs@7 tslib@2 typescript@5.9")

image = modal.Image.from_registry("node:24-bookworm", add_python="3.12")
image20 = modal.Image.from_registry("node:24-bookworm", add_python="3.12")
if LOCAL:
    image = (
        image.add_local_file(FIX / "package.json", "/fixture/package.json", copy=True)
        .add_local_file(FIX / "package-lock.json", "/fixture/package-lock.json", copy=True)
        # The network is open only while the image is built: restore from the lockfile here.
        .run_commands("cd /fixture && node --version && npm ci 2>&1 | tail -20")
        .pip_install("tree-sitter==0.26.0", "tree-sitter-language-pack==1.13.5", "sqlglot>=30", "PyYAML>=6")
        .add_local_file(FIX / "tsconfig.json", "/fixture/tsconfig.json")
        .add_local_dir(FIX / "src", "/fixture/src")
        .add_local_dir(HERE / "probe", "/fixture/probe")
        .add_local_file(REPO / "daodan/core/premap/angular_templates.mjs", "/tools/angular_templates.mjs")
        .add_local_dir(REPO / "daodan/core", "/daodan/core", ignore=["**/__pycache__/**"])
        .add_local_dir(REPO / "daodan/data", "/daodan/data")
    )
    image20 = (
        image20.run_commands("mkdir -p /fixture && cd /fixture && npm init -y > /dev/null && "
                             f"npm install --no-audit --no-fund --save-exact {ANGULAR20} 2>&1 | tail -5")
        .add_local_file(FIX / "tsconfig.json", "/fixture/tsconfig.json")
        .add_local_dir(FIX / "src", "/fixture/src")
        .add_local_file(REPO / "daodan/core/premap/angular_templates.mjs", "/tools/angular_templates.mjs")
    )
app = modal.App("angular-compiler", image=image)


def _copy(destination: str) -> str:
    """The fixture without its packages, `crlf.component.ts` with Windows line ends."""
    import shutil
    from pathlib import Path

    shutil.copytree("/fixture", destination, ignore=shutil.ignore_patterns("node_modules", "probe", "package-lock.json"))
    crlf = Path(destination) / "src/app/crlf.component.ts"
    crlf.write_bytes(crlf.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
    return destination


def _run(command: dict, project, given, seconds: str | None = None) -> dict:
    """A command of `angular.py` as the container runs it: Daodan's script by Node, the path of its list of templates where the
    runner would have put it."""
    import os
    import subprocess
    from pathlib import Path

    argv = []
    for word in command["argv"]:
        argv += ["node", "/tools/angular_templates.mjs"] if word == "daodan-angular" else [
            f"{given}/{Path(word).name}" if word.startswith("/daodan/") else word]
    if seconds and argv[0] == "timeout":
        argv[2] = seconds
    r = subprocess.run(argv, cwd=project / command["cwd"], capture_output=True, text=True, timeout=900, env={**os.environ, "NO_COLOR": "1"})
    return {"returncode": r.returncode, "stdout": r.stdout, "stderr": r.stderr}


def _carried(asked: list[dict]):
    from pathlib import Path

    given = Path("/work/in")  # the files the commands carry (`inputs`), where `preparation.IN` is in Daodan's container
    given.mkdir(parents=True, exist_ok=True)
    for command in asked:
        for name, text in command["inputs"].items():
            (given / name).write_text(text, encoding="utf-8")
    return given


@app.function(cpu=2, memory=4096, timeout=1800, block_network=True)
def probes(scripts: list[str]) -> dict[str, str]:
    import json
    import subprocess

    node = subprocess.run(["node", "--version"], capture_output=True, text=True).stdout.strip()
    version = json.load(open("/fixture/node_modules/@angular/compiler/package.json"))["version"]
    out = {"00_env.mjs": f"node {node}, @angular/compiler {version} (the fixture's package-lock.json), network blocked\n"}
    for name in scripts:
        r = subprocess.run(["node", f"/fixture/probe/{name}"], cwd="/fixture", capture_output=True, text=True, timeout=900)
        out[name] = r.stdout + (f"\n--- STDERR ---\n{r.stderr}" if r.stderr else "") + f"\n--- exit {r.returncode}\n"
    return out


@app.function(timeout=900)
def commands() -> dict:
    """What the source asks the container to run for the fixture, and the gaps it states before the run."""
    import sys

    sys.path[:0] = ["/daodan/core"]
    import premap
    import snapshot
    from snapshot_store import open_snapshot
    from pathlib import Path

    project, manifest = Path(_copy("/work/project")), Path("/work/out/manifest.sqlite")
    snapshot.read_project(project, manifest)
    with open_snapshot(manifest) as store:
        context = premap.Context(manifest, store)
        return {"commands": premap.angular.commands(context), "gaps": premap.angular._plan(context)["gaps"]}


@app.function(timeout=1800)
def measure(repo: str, commit: str) -> dict:
    """What the source finds in a public repository at a commit: its components, its templates, the size of the list the
    container is given."""
    import json
    import subprocess
    import sys
    from pathlib import Path

    sys.path[:0] = ["/daodan/core"]
    import premap
    import snapshot
    from snapshot_store import open_snapshot

    project, manifest = Path("/work/repo"), Path("/work/out/manifest.sqlite")
    subprocess.run(["git", "clone", "--quiet", repo, str(project)], check=True)
    subprocess.run(["git", "-C", str(project), "checkout", "--quiet", commit], check=True)
    snapshot.read_project(project, manifest)
    with open_snapshot(manifest) as store:
        context = premap.Context(manifest, store)
        plan = premap.angular._plan(context)
        asked = premap.angular.commands(context) or []
    return {"templates": {f: len(items) for f, items in plan["jobs"].items()},
            "components": sum(len(members) for items in plan["jobs"].values() for _, members in items),
            "list_characters": {f: len(json.dumps([job for job, _ in items], separators=(",", ":"))) for f, items in plan["jobs"].items()},
            "gaps": [(g["kind"], g["path"], g["detail"][:160]) for g in plan["gaps"]], "commands": len(asked)}


@app.function(cpu=2, memory=4096, timeout=1800, block_network=True)
def source(asked: list[dict]) -> dict:
    """Each command's script, as the container runs it, in the project with its packages and in variants of it."""
    import hashlib
    import json
    import shutil
    import time
    from pathlib import Path

    given = _carried(asked)
    modules = Path("/fixture/node_modules")
    installed, bare, nocli, notsconfig, solution = (Path(_copy(f"/work/{name}")) for name in ("installed", "bare", "nocli", "notsconfig", "solution"))
    shutil.copytree(modules, installed / "node_modules", symlinks=True)  # a copy: a link would give the declarations a path outside the project
    (notsconfig / "node_modules").symlink_to(modules)
    (notsconfig / "tsconfig.json").unlink()
    (solution / "node_modules").symlink_to(modules)  # a solution-style tsconfig.json: no file of its own, the project it references has them
    (solution / "tsconfig.app.json").write_text((solution / "tsconfig.json").read_text(encoding="utf-8"), encoding="utf-8")
    (solution / "tsconfig.json").write_text(json.dumps({"files": [], "references": [{"path": "./tsconfig.app.json"}]}), encoding="utf-8")
    (nocli / "node_modules" / "@angular").mkdir(parents=True)
    for entry in modules.iterdir():
        if entry.name != "@angular":
            (nocli / "node_modules" / entry.name).symlink_to(entry)
    for entry in (modules / "@angular").iterdir():
        if entry.name != "compiler-cli":
            (nocli / "node_modules" / "@angular" / entry.name).symlink_to(entry)
    out = {"script_sha256": hashlib.sha256(Path("/tools/angular_templates.mjs").read_bytes().replace(b"\r\n", b"\n")).hexdigest()}
    for name, project, seconds in (("installed", installed, None), ("not_installed", bare, None), ("no_compiler_cli", nocli, None),
                                   ("no_tsconfig", notsconfig, None), ("solution", solution, None), ("timeout", installed, "0.05")):
        started = time.monotonic()
        out[name] = [_run(command, project, given, seconds) for command in asked]
        out[name + "_seconds"] = [round(time.monotonic() - started, 2)]
    shutil.rmtree(given, ignore_errors=True)
    return out


@app.function(image=image20, cpu=2, memory=4096, timeout=1800, block_network=True)
def source20(asked: list[dict]) -> dict:
    """The same commands in an image of Angular 20: whether what the script calls is there before 22."""
    import json
    import shutil
    from pathlib import Path

    given = _carried(asked)
    project = Path(_copy("/work/installed"))
    shutil.copytree("/fixture/node_modules", project / "node_modules", symlinks=True)
    versions = {name: json.loads(Path(f"/fixture/node_modules/{name}/package.json").read_text(encoding="utf-8"))["version"]
                for name in ("@angular/core", "@angular/compiler", "@angular/compiler-cli", "typescript")}
    return {"versions": versions, "answers": [_run(command, project, given) for command in asked]}


@app.local_entrypoint()
def main(mode: str = "probes"):
    import json

    if mode == "measure":
        report = measure.remote(os.environ["REPO"], os.environ["COMMIT"])
        print(json.dumps(report, indent=1))
        name = os.environ["REPO"].rstrip("/").rsplit("/", 1)[-1]
        OUT.mkdir(exist_ok=True)
        (OUT / f"measure-{name}.json").write_bytes((json.dumps(report, indent=1, sort_keys=True) + "\n").encode("utf-8"))
        return
    if mode == "source":
        asked = commands.remote()
        print("commands:", len(asked["commands"] or []), "gaps stated before the run:", json.dumps(asked["gaps"], indent=1))
        answers = source.remote(asked["commands"])
        RECORDED.mkdir(parents=True, exist_ok=True)
        for name, file in (("installed", "fixture.json"), ("not_installed", "not-installed.json"), ("no_compiler_cli", "no-compiler-cli.json"),
                           ("no_tsconfig", "no-tsconfig.json"), ("solution", "solution.json"), ("timeout", "timeout.json")):
            (RECORDED / file).write_bytes((json.dumps(answers[name], indent=1, ensure_ascii=False) + "\n").encode("utf-8"))
            for answer in answers[name]:
                print(f"=== {name}: exit {answer['returncode']}, {len(answer['stdout'])} bytes out, {answers[name + '_seconds']} s (all commands)\n"
                      f"{answer['stderr'].strip()[:600]}")
        (RECORDED / "script.json").write_bytes((json.dumps({"angular_templates.mjs": answers["script_sha256"]}, indent=1) + "\n").encode("utf-8"))
        old = source20.remote(asked["commands"])
        (RECORDED / "fixture-angular20.json").write_bytes((json.dumps(old["answers"], indent=1, ensure_ascii=False) + "\n").encode("utf-8"))
        print("Angular 20 image:", json.dumps(old["versions"]))
        for answer in old["answers"]:
            print(f"=== angular 20: exit {answer['returncode']}, {len(answer['stdout'])} bytes out\n{answer['stderr'].strip()[:800]}")
        return
    scripts = os.environ.get("PROBES") or ",".join(sorted(p.name for p in (HERE / "probe").glob("[0-9]*.mjs")))
    OUT.mkdir(exist_ok=True)
    for name, text in probes.remote(scripts.split(",")).items():
        (OUT / (name.removesuffix(".mjs") + ".txt")).write_text(text, encoding="utf-8")
        print(f"=== {name}\n{text}")
