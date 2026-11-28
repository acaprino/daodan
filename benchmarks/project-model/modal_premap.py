"""The pre-map on Modal, in a Linux container: snapshot, sources, model commands and score, nothing on this PC.

The container holds the plugin's scripts and the pinned tools the pre-map's model sources name: Go 1.27.3,
Rust 1.99.1 (rustup's proxies with `RUSTUP_TOOLCHAIN` set by the command), uv 0.11.28, Node 24.22.3 with
Renovate 44.239.1 and TypeScript 6.0.3 (go-enry left the pre-map in T1.9: `_languages` finds no `daodan-enry`
answer). A case is written to `/work/<case>`, snapshotted, and `premap.write` runs with a runner that
executes each command in its `cwd` there (network on: the preparation and the run are not split here).

`--store` keeps, for each case of `tests/fixtures/premap/projects.json`, every model command with its answer in
`tests/fixtures/premap/outputs/<case>.json`: the readers' tests replay them. `--score` scores corpus fixtures
(`fixtures/<name>`) against their `expected.json`, beside `modules.py` read the way `tools/daodan_modules.py`
reads it, and writes the scores to `--out`. The code hash of this driver and of `premap/` is printed on both
sides; they must match.

    python -m modal run benchmarks/project-model/modal_premap.py --store go_nested,rust_buildrs,uv_workspace
    python -m modal run benchmarks/project-model/modal_premap.py --score js,py,jvm,sys,mix,real --out OUT.json
    python -m modal run benchmarks/project-model/modal_premap.py --score ... --out OUT.json --runs results/premap-runs

`--runs` also keeps, per fixture, every model command with its answer (`results/premap-runs/<fixture>.json.gz`):
`tools/premap_replay.py` replays them on this PC, so a change to a reader is scored without a new run.

`--network` runs the pre-map of one real repository with Renovate's commands given the network and refused it (a
Sandbox with `block_network`, as in the pipeline), with and without the stack's `--tools`, and Renovate alone on two
small projects, one whose config extends a preset of GitHub's (`renovate_network`):

    python -m modal run benchmarks/project-model/modal_premap.py --network real-bank-of-anthos --tools maven,python --out OUT.json

A family's fixtures share one container; each real repository (its clone from the archive `modal_native.py
prepare` keeps on the volume `daodan-flow-results`) has a container of its own.
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
REMOTE_SCRIPTS = "/daodan/map/core"  # container paths: POSIX strings, whatever runs the client
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
             f"PATH=/opt/node-{NODE}-linux-x64/bin:$PATH npm install -g --ignore-scripts renovate@44.239.1 typescript@6.0.3")
         .pip_install("uv==0.11.28", "tree-sitter==0.26.0", "tree-sitter-language-pack==1.13.5", "sqlglot>=30", "PyYAML>=6",
                      "pip-requirements-parser==32.0.1")
         .env({"PATH": f"/root/.cargo/bin:/usr/local/go/bin:/opt/node-{NODE}-linux-x64/bin:/usr/local/bin:/usr/bin:/bin"}))
if LOCAL:
    image = (image.add_local_dir(REPO / "daodan/core", REMOTE_SCRIPTS,
                                 ignore=["**/__pycache__/**"])
             .add_local_dir(REPO / "daodan/data", "/daodan/map/data")  # `container` reads package-managers.json
             .add_local_dir(HERE / "fixtures", f"{REMOTE_PM}/fixtures")
             .add_local_file(HERE / "score.py", f"{REMOTE_PM}/score.py")
             .add_local_file(HERE / "tools/daodan_modules.py", f"{REMOTE_PM}/tools/daodan_modules.py")
             .add_local_file(HERE / "tools/native_common.py", f"{REMOTE_PM}/tools/native_common.py")
             .add_local_file(REPO / "tests/fixtures/premap/projects.json", f"{REMOTE_PM}/projects.json"))
app = modal.App("daodan-premap", image=image)
volume = modal.Volume.from_name("daodan-flow-results")


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


def _versions() -> dict:
    return {argv[0]: subprocess.run(argv, capture_output=True, text=True,
                                    env={**os.environ, "RUSTUP_TOOLCHAIN": "1.99.1"}).stdout.strip()
            for argv in (["go", "version"], ["cargo", "--version"], ["uv", "--version"], ["renovate", "--version"])}


def _real(name: str) -> Path:
    """A real repository's clone at its pinned commit, from the archive `modal_native.py prepare` stored; without an
    archive, cloned here at that commit (shallow), as `modal_stack.py` does."""
    import tarfile
    project, part = Path("/work") / name, Path("/work/real-part") / name
    shutil.rmtree(project, ignore_errors=True)
    shutil.rmtree(part, ignore_errors=True)
    archive = Path("/results/project-model/native-real") / f"{name}.tar.gz"
    if not archive.is_file():
        source = json.loads((Path(REMOTE_PM) / "fixtures" / name / "source.json").read_text(encoding="utf-8"))
        project.mkdir(parents=True)
        for argv in (["git", "init", "-q"], ["git", "remote", "add", "origin", source["repo"]],
                     ["git", "fetch", "-q", "--depth", "1", "origin", source["commit"]],
                     ["git", "checkout", "-q", "FETCH_HEAD"]):
            done = subprocess.run(argv, cwd=project, capture_output=True, text=True, timeout=900,
                                  env={**os.environ, "GIT_TERMINAL_PROMPT": "0"})
            if done.returncode:
                raise RuntimeError(f"{' '.join(argv[:3])}: {done.stderr.strip()[-300:]}")
        return project
    part.mkdir(parents=True)
    with tarfile.open(archive) as tar:
        tar.extractall(part, filter="tar")
    (part / name).rename(project)
    return project


@app.function(cpu=1.0, memory=2048, timeout=900)
def store_outputs(names: list) -> dict:
    sys.path[:0] = [REMOTE_SCRIPTS, REMOTE_PM, f"{REMOTE_PM}/tools"]
    import premap
    import snapshot
    out = {"code": code_hash(Path(__file__), Path(REMOTE_SCRIPTS) / "premap"), "versions": _versions(), "store": {}}
    projects = json.loads((Path(REMOTE_PM) / "projects.json").read_text(encoding="utf-8"))
    for name in names:
        project, manifest = _case(name, projects[name])
        os.environ["PREMAP_ROOT"] = str(project)
        snapshot.read_project(project, manifest)
        log: list = []
        premap.write(manifest, runner=_runner(log))
        out["store"][name] = log
    return out


@app.function(cpu=1.0, memory=3072, timeout=2400, volumes={"/results": volume})
def score_fixtures(names: list) -> dict:
    sys.path[:0] = [REMOTE_SCRIPTS, REMOTE_PM, f"{REMOTE_PM}/tools"]
    import daodan_modules
    import modules
    import premap
    import score as scorer
    import snapshot
    out = {"code": code_hash(Path(__file__), Path(REMOTE_SCRIPTS) / "premap"), "versions": _versions(), "score": {}}
    for name in names:
        fixture = Path(REMOTE_PM) / "fixtures" / name
        expected = json.loads((fixture / "expected.json").read_text(encoding="utf-8"))
        started = time.monotonic()
        try:
            if (fixture / "source.json").is_file():
                project = _real(name)
                manifest = Path("/work") / f"{name}.out" / "manifest.sqlite"
                shutil.rmtree(manifest.parent, ignore_errors=True)
            else:
                project, manifest = _case(name, None)
            os.environ["PREMAP_ROOT"] = str(project)
            snapshot.read_project(project, manifest)
            graph = modules.load_graph(Path(modules.ensure_graph(manifest)["graph"]))
            middle = time.monotonic()
            log = []
            record = premap.write(manifest, runner=_runner(log))
            languages = _languages(manifest, log)
        except Exception as error:  # noqa: BLE001 - a fixture's failure is its result
            out["score"][name] = {"error": f"{type(error).__name__}: {error}"}
            continue
        out["score"][name] = {"base": scorer.score(expected, daodan_modules.convert(graph)),
                              "premap": scorer.score(expected, record), "sources": record["sources"],
                              "gaps": record["gaps"], "output": record,
                              "languages_per_file": languages, "runs": log,
                              "seconds": {"snapshot_and_graph": round(middle - started, 2),
                                          "premap": round(time.monotonic() - middle, 2)}}
    return out


# `--network`: two small projects of the same Python, one whose Renovate config extends a preset of GitHub's
PRESET = "github>GoogleCloudPlatform/kubernetes-engine-samples//.github/renovate-configs/dee-platform-ops.json5"
SYNTHETIC = {"pyproject.toml": '[project]\nname = "syn"\nversion = "0"\nrequires-python = ">=3.12"\n',
             ".python-version": "3.12\n", "main.py": "print(1)\n"}


def _boxed(box, log: list, env: dict | None = None):
    """`_runner` in `box`, a Sandbox of this image with the network blocked, as the pipeline's execution runs a command."""
    def run(commands):
        answers = []
        for command in commands:
            root = os.environ["PREMAP_ROOT"]
            process = box.exec("sh", "-c", 'cd "$0" && exec "$@"', f"{root}/{command['cwd']}", *command["argv"],
                               env={**command["env"], **(env or {})}, timeout=600)
            out, err = process.stdout.read(), process.stderr.read()
            answer = {"returncode": process.wait(), "stdout": out, "stderr": err, "root": root}
            log.append({"command": command, "result": answer})
            answers.append(answer)
        return answers
    return run


def _said(record: dict, log: list, debug: bool, raw: bool = False) -> dict:
    """What an arm of `renovate_network` keeps: the toolchains, Renovate's state and gaps, and its extraction's answer
    (`raw`: the answer itself, as a test replays it)."""
    done = next((r["result"] for r in log if r["command"]["argv"][:1] == ["renovate"]), None) or {}
    try:
        report = json.loads(done.get("stdout") or "null")
    except ValueError:
        report = None
    local = ((report or {}).get("repositories") or {}).get("local") or {}
    lines, seen = [], set()
    for line in (done.get("stderr") or "").splitlines():
        try:
            item = json.loads(line)
        except ValueError:
            item = {"level": None, "msg": line[:300]}
        said = f"{item.get('level')} {item.get('msg')}" + (f": {item['err'].get('message')}" if isinstance(
            item.get("err"), dict) else "")
        if said not in seen and len(lines) < 400:
            seen.add(said)
            lines.append(said[:400])
    return {"toolchains": sorted(f"{t['tool']}@{t['declared_in']}" for t in record.get("toolchains", [])),
            "packages": len(record.get("packages", [])),
            "renovate_packages": sum(any(s.startswith("renovate@") for s in p["sources"])
                                     for p in record.get("packages", [])),
            "renovate": [s for s in record["sources"] if s["source"].startswith("renovate@")],
            "renovate_gaps": [{k: str(g.get(k))[:300] for k in ("kind", "path", "detail")} for g in record["gaps"]
                              if str(g.get("source", "")).startswith("renovate@") and g["kind"] != "file_withheld"],
            "extract": {"returncode": done.get("returncode"), "report_keys": sorted(report or {}),
                        "problems": (report or {}).get("problems"), "local_keys": sorted(local),
                        "local_problems": local.get("problems"),
                        "managers": {m: len(files) for m, files in (local.get("packageFiles") or {}).items()},
                        "stderr" if debug else "stderr_tail": lines if debug else (done.get("stderr") or "")[-1500:]},
            **({"answer": done} if raw else {})}


@app.function(cpu=2.0, memory=4096, timeout=2400, volumes={"/results": volume})
def renovate_network(name: str, tools: list) -> dict:
    """The pre-map of the real repository `name` with Renovate's commands run with the network open (`_runner`) and blocked
    (in a Sandbox of this image with `block_network`, as the pipeline's execution runs them), with and without the
    stack's `tools` (`premap._chosen`); then Renovate alone on three small projects: no config, a config that extends
    a preset of GitHub's (`PRESET`), one that disables Renovate: what tells the network from the choice of sources."""
    sys.path[:0] = [REMOTE_SCRIPTS, REMOTE_PM, f"{REMOTE_PM}/tools"]
    import io
    import tarfile
    import premap
    import snapshot
    from premap import renovate
    from snapshot_store import open_snapshot
    out = {"code": code_hash(Path(__file__), Path(REMOTE_SCRIPTS) / "premap"), "versions": _versions(), "arms": {}}
    real = _real(name)
    synthetic = {"syn-plain": SYNTHETIC, "syn-preset": {**SYNTHETIC, "renovate.json": json.dumps({"extends": [PRESET]})},
                 "syn-disabled": {**SYNTHETIC, "renovate.json": json.dumps({"enabled": False})}}
    manifests = {name: Path("/work") / f"{name}.out" / "manifest.sqlite"}
    shutil.rmtree(manifests[name].parent, ignore_errors=True)
    snapshot.read_project(real, manifests[name])
    for case, files in synthetic.items():
        project, manifests[case] = _case(case, files)
        snapshot.read_project(project, manifests[case])
    packed = io.BytesIO()
    with tarfile.open(fileobj=packed, mode="w") as tar:
        for case in manifests:
            tar.add(Path("/work") / case, arcname=f"work/{case}")
    box = modal.Sandbox.create(image=image, block_network=True, cpu=2.0, memory=4096, timeout=2400,
                               app=modal.App.lookup("daodan-premap-sandboxes", create_if_missing=True))
    try:
        unpack = box.exec("tar", "-xf", "-", "-C", "/", text=False)
        unpack.stdin.write(packed.getvalue())
        unpack.stdin.write_eof()
        unpack.stdin.drain()
        if unpack.wait() != 0:
            raise RuntimeError(f"the copy did not unpack in the sandbox: {unpack.stderr.read()[-300:]}")
        arms = [("open", name, False, None, None, False), ("open+stack", name, False, tools, None, False),
                ("blocked+stack", name, True, tools, None, False), ("blocked-debug", name, True, tools, (renovate,), True)]
        arms += [(f"{case}-{way}", case, way == "blocked", None, (renovate,), False)
                 for case in synthetic for way in ("open", "blocked")]
        for arm, case, blocked, chosen, sources, debug in arms:
            os.environ["PREMAP_ROOT"] = str(Path("/work") / case)
            log: list = []
            local = _runner(log)
            boxed = _boxed(box, log, {"LOG_FILE_LEVEL": "debug"} if debug else None)
            run = (lambda commands: (boxed if commands[0]["tool"] == "renovate" else local)(commands)) if blocked \
                else local
            with open_snapshot(manifests[case]) as store:
                record = premap.derive(manifests[case], store, sources=sources, runner=run, tools=chosen)
            out["arms"][arm] = _said(record, log, debug, raw=case.startswith("syn-") and blocked)
            print(arm, len(out["arms"][arm]["toolchains"]), "toolchains", flush=True)
    finally:
        box.terminate()
    return out


def _languages(manifest: Path, log: list) -> dict:
    """Per file of the snapshot, its suffix-table language against go-enry's: what replacing the table would change."""
    from premap import suffix_table
    from snapshot_store import open_snapshot
    import modules
    run = next((r["result"] for r in log if r["command"]["tool"] == "daodan-enry"), None)
    if run is None or run["returncode"] != 0:
        return {"error": "daodan-enry did not answer"}
    rows = {row["path"]: row for row in json.loads(run["stdout"])}
    with open_snapshot(manifest) as store:
        headers = modules._Inventory(store).headers
    out = {"same": 0, "changed": {}, "table_only": {}, "enry_only": {}, "left_out_by_enry": {}, "examples": {}}
    for rel, header in sorted(headers.items()):
        table = header.get("language")
        table = suffix_table.NAMES.get(table, table) if table else None
        row = rows.get(rel) or {}
        why = next((w for w in ("vendored", "generated", "documentation", "binary") if row.get(w)), None)
        guess = row.get("language") or None
        if why and table:
            key, bucket = f"{table} ({why})", "left_out_by_enry"
        elif table == guess:
            out["same"] += table is not None
            continue
        elif table and guess:
            key, bucket = f"{table} -> {guess}", "changed"
        elif table:
            key, bucket = table, "table_only"
        else:
            key, bucket = guess, "enry_only"
        out[bucket][key] = out[bucket].get(key, 0) + 1
        out["examples"].setdefault(f"{bucket}: {key}", [])
        if len(out["examples"][f"{bucket}: {key}"]) < 2:
            out["examples"][f"{bucket}: {key}"].append(rel)
    return out


@app.local_entrypoint()
def main(store: str = "", score: str = "", out: str = "", runs: str = "", network: str = "", tools: str = ""):
    local = code_hash(Path(__file__), REPO / "daodan/core/premap")
    print("code", local, flush=True)
    if network:  # one real repository, Renovate with the network open and blocked (`renovate_network`)
        answer = renovate_network.remote(network, [t for t in tools.split(",") if t])
        print("remote code", answer["code"], "same" if answer["code"] == local else "DIFFERENT", flush=True)
        for arm, said in answer["arms"].items():
            print(arm, len(said["toolchains"]), "toolchains", said["packages"], "packages",
                  said["extract"]["returncode"], said["extract"]["managers"], flush=True)
        Path(out).write_text(json.dumps(answer, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        return
    if store:
        answer = store_outputs.remote([s for s in store.split(",") if s])
        print("remote code", answer["code"], "same" if answer["code"] == local else "DIFFERENT", answer["versions"],
              flush=True)
        for name, log in answer["store"].items():
            target = REPO / "tests/fixtures/premap/outputs" / f"{name}.json"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps({"versions": answer["versions"], "runs": log}, indent=1, ensure_ascii=False)
                              + "\n", encoding="utf-8")
            print("stored", name, len(log), flush=True)
    if not score:
        return
    fixtures = sorted(p.name for p in (HERE / "fixtures").iterdir() if (p / "expected.json").is_file())
    batches = []
    for spec in score.split(","):
        if spec in ("js", "py", "jvm", "sys", "mix"):  # a family's hand-written fixtures in one container
            batches.append([n for n in fixtures if n.startswith(spec + "-") and not (HERE / "fixtures" / n / "source.json").is_file()])
        elif spec == "real":  # every real repository in a container of its own
            batches += [[n] for n in fixtures if (HERE / "fixtures" / n / "source.json").is_file()]
        elif spec:
            batches.append([spec])
    results, codes = {}, set()
    for answer in score_fixtures.map(batches, return_exceptions=True):
        if isinstance(answer, Exception):
            print("a container failed:", answer, flush=True)
            continue
        codes.add(answer["code"])
        for name, result in answer["score"].items():
            log = result.pop("runs", None)
            if runs and log is not None:  # every model command with its answer, to replay the pre-map here
                import gzip
                target = Path(runs) / f"{name}.json.gz"
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(gzip.compress(json.dumps({"versions": answer["versions"], "runs": log}, indent=1,
                                                            ensure_ascii=False).encode("utf-8") + b"\n", 9, mtime=0))
        results.update(answer["score"])
    print("remote code", sorted(codes), "same" if codes == {local} else "DIFFERENT", flush=True)
    Path(out).write_text(json.dumps(results, indent=1), encoding="utf-8")
    print("scored", len(results), "->", out, flush=True)
