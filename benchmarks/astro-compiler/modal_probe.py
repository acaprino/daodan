"""The parser of an Astro project's compiler on Modal, in a container with the network blocked.

    PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal python -m modal run benchmarks/astro-compiler/modal_probe.py --mode lock
    PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal python -m modal run benchmarks/astro-compiler/modal_probe.py

Astro 5, 6 and 7 do not share a compiler (`@astrojs/compiler` 2.x, `@astrojs/compiler` 4.x, `@astrojs/compiler-rs`), so each has its own
`versions/<name>/package.json`, pinned to one Astro, and the same project files (`fixture/`) are put on each.

`--mode lock` writes each version's `package-lock.json` (the one moment it is made: `npm install --package-lock-only
--ignore-scripts`, run with the network open in a Modal function, never on this PC). `--mode probes` (the default) builds one image
for each version with its packages restored from its lockfile (`npm ci`, while the image is built: the one moment the network is
open), then runs each script of `probe/` (env `PROBES="01_parse.mjs,02_positions.mjs"` picks some, `VERSIONS="astro5"` picks some)
in the project's folder with the network blocked; each script's output is written to `results/<version>/`. The project's code
(`astro.config.mjs`, `node_modules`) runs only in the container.

`--mode source` runs what `daodan/core/premap/astro.py` runs in Daodan's container: the command it gives for the fixture (a function
with the network open, where Daodan's grammar bundle comes from), then the script of that command (`daodan/core/premap/astro_templates.mjs`)
by each version's Node and packages, with the network blocked: in a copy of the project with its packages, in a copy with Windows line
ends, and in a copy without its packages. The answers, as the container runner returns them (`returncode`, `stdout`, `stderr`), are
written to `tests/fixtures/premap/astro/<version>.json`, which `tests/test_codebase_map_premap_astro.py` reads, with the sha256 of the
script that produced them and the `VERSION` of the source (`script.json`): if the script changes, the answers are recorded again and
the `VERSION` is raised. `astro5-node20` is Astro 5 on Node 20, the oldest Node the script has to run on.
"""
import os
import pathlib

import modal

HERE = pathlib.Path(__file__).resolve().parent
LOCAL = modal.is_local()  # in a container this file lies at /root: nothing below that reads the checkout runs there
REPO = HERE.parents[1] if LOCAL else HERE
FIX = HERE / "fixture"
OUT = HERE / "results"
VERSIONS = ("astro5", "astro6", "astro7")


RECORDED = REPO / "tests/fixtures/premap/astro"


def _image(name: str, node: str = "24", lock: str | None = None) -> modal.Image:
    """The image of a version: its packages restored from its lockfile (`lock` names the folder of `versions/` when it is not `name`:
    the Node 20 image is Astro 5's lockfile on an older Node, which Astro 5 supports and the script has to run on)."""
    image = modal.Image.from_registry(f"node:{node}-bookworm", add_python="3.12")
    if not LOCAL:
        return image
    version = HERE / "versions" / (lock or name)
    if not (version / "package-lock.json").is_file():
        return image.add_local_file(version / "package.json", f"/lockwork/{name}/package.json", copy=True)
    return (
        image.add_local_file(version / "package.json", f"/fix/{name}/package.json", copy=True)
        .add_local_file(version / "package-lock.json", f"/fix/{name}/package-lock.json", copy=True)
        # The network is open only while the image is built: restore from the lockfile here.
        .run_commands(f"cd /fix/{name} && node --version && npm ci --no-audit --no-fund 2>&1 | tail -20")
        .add_local_file(FIX / "astro.config.mjs", f"/fix/{name}/astro.config.mjs")
        .add_local_file(FIX / "tsconfig.json", f"/fix/{name}/tsconfig.json")
        .add_local_dir(FIX / "src", f"/fix/{name}/src")
        .add_local_dir(HERE / "probe", f"/fix/{name}/probe")
        .add_local_file(REPO / "daodan/core/premap/astro_templates.mjs", "/tools/astro_templates.mjs")
    )


NODE20 = "astro5-node20"
IMAGES = {**{name: _image(name) for name in VERSIONS}, NODE20: _image(NODE20, node="20", lock="astro5")}
app = modal.App("astro-compiler", image=IMAGES[VERSIONS[0]])
RUN = dict(cpu=2, memory=4096, timeout=1800, block_network=True)


@app.function(image=IMAGES[VERSIONS[0]], timeout=900)
def lock(name: str, package: str) -> dict:
    """A version's lockfile, made from its package.json with the network open and no script run."""
    import subprocess

    work = pathlib.Path(f"/work/{name}")
    work.mkdir(parents=True, exist_ok=True)
    (work / "package.json").write_text(package, encoding="utf-8")
    r = subprocess.run(["npm", "install", "--package-lock-only", "--ignore-scripts", "--no-audit", "--no-fund"], cwd=work,
                       capture_output=True, text=True, timeout=800)
    lockfile = work / "package-lock.json"
    return {"returncode": r.returncode, "stderr": r.stderr[-2000:], "stdout": r.stdout[-500:],
            "lock": lockfile.read_text(encoding="utf-8") if lockfile.is_file() else None}


def _probes(name: str, scripts: list[str]) -> dict[str, str]:
    import subprocess

    out = {}
    for script in scripts:
        r = subprocess.run(["node", f"/fix/{name}/probe/{script}"], cwd=f"/fix/{name}", capture_output=True, text=True, timeout=900,
                           env={**os.environ, "NO_COLOR": "1", "CI": "1", "ASTRO_TELEMETRY_DISABLED": "1"})
        out[script] = r.stdout + (f"\n--- STDERR ---\n{r.stderr}" if r.stderr else "") + f"\n--- exit {r.returncode}\n"
    return out


@app.function(image=IMAGES["astro5"], **RUN)
def probes_astro5(scripts: list[str]) -> dict[str, str]:
    return _probes("astro5", scripts)


@app.function(image=IMAGES["astro6"], **RUN)
def probes_astro6(scripts: list[str]) -> dict[str, str]:
    return _probes("astro6", scripts)


@app.function(image=IMAGES["astro7"], **RUN)
def probes_astro7(scripts: list[str]) -> dict[str, str]:
    return _probes("astro7", scripts)


RUNNERS = {"astro5": probes_astro5, "astro6": probes_astro6, "astro7": probes_astro7}

# what builds the command the source gives for the fixture: Daodan's code and grammars beside the fixture's files
commands_image = modal.Image.from_registry("node:24-bookworm", add_python="3.12")
if LOCAL:
    commands_image = (
        commands_image.pip_install("tree-sitter==0.26.0", "tree-sitter-language-pack==1.13.5", "sqlglot>=30", "PyYAML>=6")
        .add_local_dir(FIX, "/lockwork", ignore=["**/package-lock.json"])
        .add_local_file(HERE / "versions/astro7/package.json", "/lockwork/package.json")
        .add_local_dir(REPO / "daodan/core", "/daodan/core", ignore=["**/__pycache__/**"])
        .add_local_dir(REPO / "daodan/data", "/daodan/data")
    )


@app.function(image=commands_image, timeout=900)
def commands() -> dict:
    """What the source asks the container to run for the fixture, and the gaps it states before the run."""
    import shutil
    import sys
    from pathlib import Path

    sys.path[:0] = ["/daodan/core"]
    import premap
    import snapshot
    from snapshot_store import open_snapshot

    project, manifest = Path("/work/project"), Path("/work/out/manifest.sqlite")
    shutil.copytree("/lockwork", project)
    snapshot.write_snapshot(project, manifest)
    with open_snapshot(manifest) as store:
        context = premap.Context(manifest, store)
        return {"commands": premap.astro.commands(context), "gaps": premap.astro._plan(context)["gaps"],
                "version": premap.astro.VERSION}


def _source(name: str, asked: list[dict]) -> dict:
    """Each command's script, as the container runs it: Daodan's script by Node, the path of its list where the runner would have
    put it, in the project with its packages, in a copy with Windows line ends, in a copy without its packages and, where the command
    is under `timeout`, with 0.05 seconds."""
    import hashlib
    import shutil
    import subprocess
    from pathlib import Path

    given = Path("/work/in")  # the files the commands carry (`inputs`), where `preparation.IN` is in Daodan's container
    given.mkdir(parents=True, exist_ok=True)
    for command in asked:
        for file, text in command["inputs"].items():
            (given / file).write_text(text, encoding="utf-8")

    def copy(destination: str, modules: bool, crlf: bool = False) -> Path:
        shutil.copytree(f"/fix/{name}", destination, symlinks=True, ignore=shutil.ignore_patterns("probe", *(() if modules else ("node_modules",))))
        if crlf:
            for file in Path(destination).rglob("*.astro"):
                file.write_bytes(file.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
        return Path(destination)

    def run(command: dict, project: Path, seconds: str | None = None) -> dict:
        argv = []
        for word in command["argv"]:
            argv += ["node", "/tools/astro_templates.mjs"] if word == "daodan-astro" else [f"{given}/{Path(word).name}" if word.startswith("/daodan/") else word]
        if seconds and argv[0] == "timeout":
            argv[2] = seconds
        r = subprocess.run(argv, cwd=project / command["cwd"], capture_output=True, text=True, timeout=900, env={**os.environ, "NO_COLOR": "1"})
        return {"returncode": r.returncode, "stdout": r.stdout, "stderr": r.stderr}

    out = {"script_sha256": hashlib.sha256(Path("/tools/astro_templates.mjs").read_bytes().replace(b"\r\n", b"\n")).hexdigest()}
    for key, project in (("installed", copy("/work/installed", True)), ("crlf", copy("/work/crlf", True, crlf=True)),
                         ("not_installed", copy("/work/bare", False))):
        out[key] = [run(command, project) for command in asked]
    if asked[0]["argv"][0] == "timeout":
        out["timeout"] = [run(command, copy("/work/limit", True), "0.05") for command in asked]
    return out


@app.function(image=IMAGES["astro5"], **RUN)
def source_astro5(asked: list[dict]) -> dict:
    return _source("astro5", asked)


@app.function(image=IMAGES["astro6"], **RUN)
def source_astro6(asked: list[dict]) -> dict:
    return _source("astro6", asked)


@app.function(image=IMAGES["astro7"], **RUN)
def source_astro7(asked: list[dict]) -> dict:
    return _source("astro7", asked)


@app.function(image=IMAGES[NODE20], **RUN)
def source_astro5_node20(asked: list[dict]) -> dict:
    return _source(NODE20, asked)


SOURCES = {"astro5": source_astro5, "astro6": source_astro6, "astro7": source_astro7, NODE20: source_astro5_node20}


@app.local_entrypoint()
def main(mode: str = "probes"):
    wanted = (os.environ.get("VERSIONS") or ",".join(VERSIONS)).split(",")
    if mode == "lock":
        for name in wanted:
            answer = lock.remote(name, (HERE / "versions" / name / "package.json").read_text(encoding="utf-8"))
            print(name, "exit", answer["returncode"], answer["stderr"][-300:])
            if answer["lock"]:
                (HERE / "versions" / name / "package-lock.json").write_bytes(answer["lock"].replace("\r\n", "\n").encode("utf-8"))
        return
    if mode == "source":
        import json

        asked = commands.remote()
        print("commands:", len(asked["commands"] or []), "gaps stated before the run:", json.dumps(asked["gaps"]))
        RECORDED.mkdir(parents=True, exist_ok=True)
        hashes = set()
        for name in wanted if os.environ.get("VERSIONS") else (*wanted, NODE20):
            answers = SOURCES[name].remote(asked["commands"])
            hashes.add(answers.pop("script_sha256"))
            (RECORDED / f"{name}.json").write_bytes((json.dumps(answers, indent=1, ensure_ascii=False) + "\n").encode("utf-8"))
            for key, results in answers.items():
                for answer in results:
                    print(f"=== {name} {key}: exit {answer['returncode']}, {len(answer['stdout'])} bytes out\n{answer['stderr'].strip()[:400]}")
        (RECORDED / "script.json").write_bytes((json.dumps({"astro_templates.mjs": hashes.pop(), "version": asked["version"]}, indent=1) + "\n").encode("utf-8"))
        return
    scripts = os.environ.get("PROBES") or ",".join(sorted(p.name for p in (HERE / "probe").glob("[0-9]*.mjs")))
    for name in wanted:
        folder = OUT / name
        folder.mkdir(parents=True, exist_ok=True)
        for script, text in RUNNERS[name].remote(scripts.split(",")).items():
            (folder / (script.removesuffix(".mjs") + ".txt")).write_bytes(text.replace("\r\n", "\n").encode("utf-8"))
            print(f"=== {name} {script}\n{text[:3000]}")
