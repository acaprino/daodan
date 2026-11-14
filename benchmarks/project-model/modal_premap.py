"""The pre-map on Modal, in a Linux container: snapshot, sources, model commands and score, nothing on this PC.

The container holds the plugin's scripts and the pinned tools the pre-map's model sources name: Go 1.27.3,
Rust 1.99.1 (rustup's proxies with `RUSTUP_TOOLCHAIN` set by the command), uv 0.11.28, Node 24.22.3 with
Renovate 44.239.1. A case is written to `/work/<case>`, snapshotted, and `premap.write` runs with a runner that
executes each command in its `cwd` there (network on: the preparation and the run are not split here).

`--store` keeps, for each case of `tests/fixtures/premap/projects.json`, every model command with its answer in
`tests/fixtures/premap/outputs/<case>.json`: the readers' tests replay them. `--score` scores corpus fixtures
(`fixtures/<name>`) against their `expected.json`, beside `modules.py` read the way `tools/daodan_modules.py`
reads it, and writes the scores to `--out`. The code hash of this driver and of `premap/` is printed on both
sides; they must match.

    python -m modal run benchmarks/project-model/modal_premap.py --store go_nested,rust_buildrs,uv_workspace
    python -m modal run benchmarks/project-model/modal_premap.py --score js,py,sys --out OUT.json
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import modal

HERE = Path(__file__).resolve().parent
LOCAL = (HERE / "score.py").is_file()
REPO = HERE.parents[1] if LOCAL else Path("/")
GO = ("go1.27.3.linux-amd64.tar.gz", "65efbc80fdc1fa2cd2631cad5b481777a68e8725f34e89f50fc6ac714e379b40")
NODE = "v24.22.3"  # `premap/renovate.py` NODE
REMOTE_SCRIPTS = "/daodan/map/scripts"  # container paths: POSIX strings, whatever runs the client
REMOTE_PM = "/pm"

image = (modal.Image.debian_slim(python_version="3.12")
         .apt_install("curl", "ca-certificates", "git", "gcc", "libc6-dev", "xz-utils")
         .run_commands(
             f"curl -sSfLo /tmp/go.tgz https://go.dev/dl/{GO[0]} && echo '{GO[1]}  /tmp/go.tgz' | sha256sum -c -"
             " && tar -C /usr/local -xzf /tmp/go.tgz && rm /tmp/go.tgz",
             "curl -sSf https://sh.rustup.rs | sh -s -- -y --profile minimal --default-toolchain 1.99.1",
             f"cd /tmp && curl -sSfLO https://nodejs.org/dist/{NODE}/node-{NODE}-linux-x64.tar.xz"
             f" && curl -sSfL https://nodejs.org/dist/{NODE}/SHASUMS256.txt | grep ' node-{NODE}-linux-x64.tar.xz$'"
             f" | sha256sum -c - && tar -C /opt -xJf node-{NODE}-linux-x64.tar.xz && rm node-{NODE}-linux-x64.tar.xz",
             f"PATH=/opt/node-{NODE}-linux-x64/bin:$PATH npm install -g --ignore-scripts renovate@44.239.1")
         .pip_install("uv==0.11.28", "tree-sitter==0.26.0", "tree-sitter-language-pack==1.13.5", "sqlglot>=30")
         .env({"PATH": f"/root/.cargo/bin:/usr/local/go/bin:/opt/node-{NODE}-linux-x64/bin:/usr/local/bin:/usr/bin:/bin"}))
if LOCAL:
    image = (image.add_local_dir(REPO / "plugins/codebase-map/skills/map/scripts", REMOTE_SCRIPTS,
                                 ignore=["**/__pycache__/**"])
             .add_local_dir(HERE / "fixtures", f"{REMOTE_PM}/fixtures")
             .add_local_file(HERE / "score.py", f"{REMOTE_PM}/score.py")
             .add_local_file(HERE / "tools/daodan_modules.py", f"{REMOTE_PM}/tools/daodan_modules.py")
             .add_local_file(HERE / "tools/native_common.py", f"{REMOTE_PM}/tools/native_common.py")
             .add_local_file(REPO / "tests/fixtures/premap/projects.json", f"{REMOTE_PM}/projects.json"))
app = modal.App("daodan-premap", image=image)


def code_hash(driver: Path, premap_dir: Path) -> str:
    digest = hashlib.sha256()
    for file in [driver, *sorted(premap_dir.glob("*.py"))]:
        digest.update(file.name.encode() + b"\0" + file.read_bytes().replace(b"\r\n", b"\n"))
    return digest.hexdigest()[:16]


def _runner(log: list):
    def run(commands):
        answers = []
        for command in commands:
            root = Path(os.environ["PREMAP_ROOT"])
            try:
                done = subprocess.run(command["argv"], cwd=root / command["cwd"], env={**os.environ, **command["env"]},
                                      capture_output=True, text=True, timeout=600, stdin=subprocess.DEVNULL)
                answer = {"returncode": done.returncode, "stdout": done.stdout, "stderr": done.stderr, "root": str(root)}
            except subprocess.TimeoutExpired:
                answer = {"returncode": -1, "stdout": "", "stderr": "timeout after 600 s", "root": str(root)}
            log.append({"command": command, "result": answer})
            answers.append(answer)
        return answers
    return run


def _case(name: str, files: dict | None) -> tuple[Path, Path]:
    project, out = Path("/work") / name, Path("/work") / f"{name}.out"
    shutil.rmtree(project, ignore_errors=True)
    shutil.rmtree(out, ignore_errors=True)
    if files is None:
        shutil.copytree(Path(REMOTE_PM) / "fixtures" / name, project)
    else:
        for rel, text in files.items():
            (project / rel).parent.mkdir(parents=True, exist_ok=True)
            (project / rel).write_text(text, encoding="utf-8", newline="\n")
    return project, out / "manifest.sqlite"


@app.function(cpu=1.0, memory=2048, timeout=3000)
def remote(store: list, score: list) -> dict:
    sys.path[:0] = [REMOTE_SCRIPTS, REMOTE_PM, f"{REMOTE_PM}/tools"]
    import modules
    import premap
    import snapshot
    out = {"code": code_hash(Path(__file__), Path(REMOTE_SCRIPTS) / "premap"), "versions": {}, "store": {}, "score": {}}
    for argv in (["go", "version"], ["cargo", "--version"], ["uv", "--version"], ["renovate", "--version"]):
        out["versions"][argv[0]] = subprocess.run(argv, capture_output=True, text=True,
                                                  env={**os.environ, "RUSTUP_TOOLCHAIN": "1.99.1"}).stdout.strip()
    projects = json.loads((Path(REMOTE_PM) / "projects.json").read_text(encoding="utf-8"))
    for name in store:
        project, manifest = _case(name, projects[name])
        os.environ["PREMAP_ROOT"] = str(project)
        snapshot.write_snapshot(project, manifest)
        log: list = []
        premap.write(manifest, runner=_runner(log))
        out["store"][name] = log
    if score:
        import daodan_modules
        import score as scorer
    for name in score:
        project, manifest = _case(name, None)
        os.environ["PREMAP_ROOT"] = str(project)
        expected = json.loads((project / "expected.json").read_text(encoding="utf-8"))
        started = time.monotonic()
        try:
            snapshot.write_snapshot(project, manifest)
            graph = modules.load_graph(Path(modules.ensure_graph(manifest)["graph"]))
            middle = time.monotonic()
            record = premap.write(manifest, runner=_runner([]))
        except Exception as error:  # noqa: BLE001 - a fixture's failure is its result
            out["score"][name] = {"error": f"{type(error).__name__}: {error}"}
            continue
        out["score"][name] = {"base": scorer.score(expected, daodan_modules.convert(graph)),
                              "premap": scorer.score(expected, record), "sources": record["sources"],
                              "gaps": record["gaps"], "output": record,
                              "seconds": {"snapshot_and_graph": round(middle - started, 2),
                                          "premap": round(time.monotonic() - middle, 2)}}
    return out


@app.local_entrypoint()
def main(store: str = "", score: str = "", out: str = ""):
    local = code_hash(Path(__file__), REPO / "plugins/codebase-map/skills/map/scripts/premap")
    print("code", local, flush=True)
    families = ("js", "py", "jvm", "sys", "mix")
    names = []
    for spec in [s for s in score.split(",") if s]:
        if spec in families:
            names += sorted(p.name for p in (HERE / "fixtures").iterdir() if p.name.startswith(spec + "-")
                            and (p / "expected.json").is_file() and not (p / "source.json").is_file())
        else:
            names.append(spec)
    answer = remote.remote([s for s in store.split(",") if s], names)
    print("remote code", answer["code"], "same" if answer["code"] == local else "DIFFERENT", answer["versions"], flush=True)
    for name, log in answer["store"].items():
        target = REPO / "tests/fixtures/premap/outputs" / f"{name}.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps({"versions": answer["versions"], "runs": log}, indent=1, ensure_ascii=False) + "\n",
                          encoding="utf-8")
        print("stored", name, len(log), flush=True)
    if names:
        Path(out).write_text(json.dumps(answer["score"], indent=1), encoding="utf-8")
        print("scored", len(answer["score"]), "->", out, flush=True)
