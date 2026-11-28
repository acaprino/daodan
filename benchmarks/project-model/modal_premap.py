"""The pre-map on Modal: snapshot, sources, model commands and score, nothing on this PC.

`--score` and `--store` run the pre-map as the product runs it (`T1.F.4`): in a VM Sandbox with Docker's daemon (as
`modal_engine.py`), `engine_premap_driver.py` gives every model command to the product's own launcher,
`container_runner.runner(manifest)`, so the firewall, the phases and the requests are the product's (`T1.F.3`): every
run behind Daodan's proxy, the canonical registries and the approved hosts open, any other host a request. Nobody
answers during a run, as in MCP and on the command line: the request is refused at once and kept in the fixture's result
(`egress`). The answers are per fixture in `egress-answers.json` (`{fixture: [host]}`), given as «Sempre» for the
fixture's project before it runs. A sandbox has `--hours` (4); `--parallel` (24) run at once.

`--store` keeps, for each case of `tests/fixtures/premap/projects.json`, every model command with its answer in
`tests/fixtures/premap/outputs/<case>.json`: the readers' tests replay them. `--score` scores corpus fixtures
(`fixtures/<name>`) against their `expected.json`, beside `modules.py` read the way `tools/daodan_modules.py`
reads it, and writes the scores to `--out`, with each fixture's unanswered requests (`egress.requests`). The code hash of
the drivers, of `premap/` and of the modules that run its commands is printed on both sides; they must match.

    python -m modal run benchmarks/project-model/modal_premap.py --store go_nested,rust_buildrs,uv_workspace
    python -m modal run benchmarks/project-model/modal_premap.py --score js,py,jvm,sys,mix,real --out OUT.json
    python -m modal run benchmarks/project-model/modal_premap.py --score ... --out OUT.json --runs results/premap-runs

`--runs` also keeps, per fixture, every model command with its answer (`results/premap-runs/<fixture>.json.gz`):
`tools/premap_replay.py` replays them on this PC, so a change to a reader is scored without a new run.

`--network` and `--presets` are the measures of 28 November 2026 (README, «Renovate con la rete e senza») and keep their
own container, with the pinned tools on it: Go 1.27.3, Rust 1.99.1, uv 0.11.28, Node 24.22.3 with Renovate 44.239.1 and
TypeScript 6.0.3. `--network` runs the pre-map of one real repository with Renovate's commands given the whole network
(`_runner`, the arm the reference had before `T1.F.4`) and refused it (a Sandbox with `block_network`), with and without
the stack's `--tools`, and Renovate alone on small projects, one whose config extends a preset of GitHub's
(`renovate_network`):

    python -m modal run benchmarks/project-model/modal_premap.py --network real-bank-of-anthos --tools maven,python --out OUT.json

`--presets` counts the fixtures whose Renovate config extends a preset outside Renovate (`renovate_presets`): the config
file Renovate itself would take and the source of each preset, from the installed Renovate's own code (`PRESETS`):

    python -m modal run benchmarks/project-model/modal_premap.py --presets --out OUT.json

A family's fixtures share one container; each real repository (its clone from the archive `modal_native.py
prepare` keeps on the volume `daodan-flow-results`) has a container of its own.
"""
from __future__ import annotations

import concurrent.futures
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
DOCKER = "https://download.docker.com/linux/static/stable/x86_64/docker-29.10.0.tgz"  # `modal_engine.py`
REMOTE_SCRIPTS = "/daodan/map/core"  # container paths: POSIX strings, whatever runs the client
REMOTE_PM = "/pm"
DRIVER = "engine_premap_driver.py"
PIP = ("tree-sitter==0.26.0", "tree-sitter-language-pack==1.13.5", "sqlglot>=30", "PyYAML>=6",
       "pip-requirements-parser==32.0.1")

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
         .pip_install("uv==0.11.28", *PIP)
         .env({"PATH": f"/root/.cargo/bin:/usr/local/go/bin:/opt/node-{NODE}-linux-x64/bin:/usr/local/bin:/usr/bin:/bin"}))
# `--score` and `--store`: Docker's daemon and the product's code, no tool of the pre-map (the product's runs fetch them)
engine_image = (modal.Image.debian_slim(python_version="3.13")  # as `benchmarks/egress/modal_probe.py`
                .apt_install("ca-certificates", "curl", "iptables", "xz-utils", "procps", "git")
                .pip_install(*PIP, "protobuf==7.36.2", "jsonpointer==3.0.0")  # `project_file`, where «Sempre» is kept
                .run_commands(f"curl -fsSL {DOCKER} -o /tmp/d.tgz && mkdir -p /opt/docker && "
                              "tar -xzf /tmp/d.tgz -C /opt/docker --strip-components=1"))


def _with_code(base, copy: bool):
    """`base` with the product's code, the fixtures, the scorer and the driver at their container paths."""
    return (base.add_local_dir(REPO / "daodan/core", REMOTE_SCRIPTS, copy=copy, ignore=["**/__pycache__/**"])
            .add_local_dir(REPO / "daodan/data", "/daodan/map/data", copy=copy)  # `container` reads package-managers.json
            .add_local_dir(HERE / "fixtures", f"{REMOTE_PM}/fixtures", copy=copy)
            .add_local_file(HERE / "score.py", f"{REMOTE_PM}/score.py", copy=copy)
            .add_local_file(HERE / "tools/daodan_modules.py", f"{REMOTE_PM}/tools/daodan_modules.py", copy=copy)
            .add_local_file(HERE / "tools/native_common.py", f"{REMOTE_PM}/tools/native_common.py", copy=copy)
            .add_local_file(REPO / "tests/fixtures/premap/projects.json", f"{REMOTE_PM}/projects.json", copy=copy)
            .add_local_file(HERE / DRIVER, f"{REMOTE_PM}/{DRIVER}", copy=copy))


if LOCAL:
    image = _with_code(image, False)
    engine_image = (_with_code(engine_image, True)  # a Sandbox's image: copied in
                    .add_local_file(HERE / "modal_premap.py", f"{REMOTE_PM}/modal_premap.py", copy=True)
                    .add_local_file(HERE / "egress-answers.json", f"{REMOTE_PM}/egress-answers.json", copy=True))

app = modal.App("daodan-premap", image=image)
volume = modal.Volume.from_name("daodan-flow-results")


def _driver():
    """`engine_premap_driver`, beside this file here and at `REMOTE_PM` in the containers."""
    folder = str(HERE if LOCAL else Path(REMOTE_PM))
    if folder not in sys.path:
        sys.path.insert(0, folder)
    import engine_premap_driver
    return engine_premap_driver


def _code() -> str:
    """The code's hash on this side (`engine_premap_driver.code_hash`)."""
    folder = HERE if LOCAL else Path(REMOTE_PM)
    return _driver().code_hash([Path(__file__), folder / DRIVER], REPO / "daodan/core" if LOCAL else Path(REMOTE_SCRIPTS))


def _real(name: str) -> Path:
    """A real repository's clone at `/work/<name>` (`engine_premap_driver.lay_out`)."""
    return _driver().lay_out(name, Path("/work") / name)


def _case(name: str, files: dict | None) -> tuple[Path, Path]:
    """The case at `/work/<name>`, its manifest beside it."""
    out = Path("/work") / f"{name}.out"
    shutil.rmtree(out, ignore_errors=True)
    return _driver().lay_out(name, Path("/work") / name, files), out / "manifest.sqlite"


def _boxed_job(job: dict, hours: float) -> tuple[dict, dict]:
    """`engine_premap_driver.py` over `job` in a VM Sandbox with Docker's daemon (as `modal_engine.py`), the clones'
    volume mounted: `({code, versions}, {name: result})`. Each fixture's result is read as soon as the driver has
    written it, so a sandbox past its `hours`, or lost, costs only the fixtures not done; each of those says why."""
    seconds, start, done, said, box = int(hours * 3600), {}, {}, "", None
    try:
        box = modal.Sandbox.create(image=engine_image, app=modal.App.lookup("daodan-premap-engine", create_if_missing=True),
                                   cpu=4, memory=16384, timeout=seconds, runtime="vm", volumes={"/results": volume})
        box.exec("sh", "-c", "PATH=/opt/docker:$PATH nohup dockerd > /tmp/dockerd.log 2>&1 &")
        for _ in range(90):
            if box.exec("/opt/docker/docker", "info", timeout=30).wait() == 0:
                break
            time.sleep(1)
        process = box.exec("python", "-u", f"{REMOTE_PM}/{DRIVER}", json.dumps(job), timeout=max(seconds - 300, 600))
        tail = ""
        for chunk in process.stdout:  # the stream comes in chunks, not lines (`modal_engine.py`)
            *lines, tail = (tail + chunk).split("\n")
            for line in lines:
                print(f"[{job['names'][0]}] {line.rstrip()[:300]}", flush=True)
                if line.startswith("START "):
                    start = json.loads(line[len("START "):])
                elif line.startswith("DONE "):
                    name = line.split()[1]
                    done[name] = json.loads(box.exec("cat", f"/runs/out/{name}.json", timeout=600).stdout.read())
        said = f"the driver ended {process.wait()}: {process.stderr.read()[-1500:]}"
    except Exception as error:  # noqa: BLE001 - past its time or lost: what was read stands
        said = f"{type(error).__name__}: {error}"
    finally:
        if box is not None:
            box.terminate()
    print(f"[{job['names'][0]}] {said}", flush=True)
    return start, {name: done.get(name) or {"error": f"no answer: {said}"} for name in job["names"]}


def _boxed_jobs(jobs: list[dict], hours: float, parallel: int) -> list[tuple[dict, dict]]:
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, min(parallel, len(jobs)))) as pool:
        return list(pool.map(lambda job: _boxed_job(job, hours), jobs))


def _runner(log: list):
    """Every command on this function's container, with its whole network: `renovate_network`'s open arm."""
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


def _versions() -> dict:
    return {argv[0]: subprocess.run(argv, capture_output=True, text=True,
                                    env={**os.environ, "RUSTUP_TOOLCHAIN": "1.99.1"}).stdout.strip()
            for argv in (["go", "version"], ["cargo", "--version"], ["uv", "--version"], ["renovate", "--version"])}


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
    out = {"code": _code(), "versions": _versions(), "arms": {}}
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


# `--presets`: the config of each folder as Renovate 44.239.1 finds and reads it, with its own modules: the first of
# `getConfigFileNames()` that is there (`package.json` only with a `renovate` key, a string being one preset, as
# `detectConfigFile` and `detectRepoFileConfig` take it, lib/workers/repository/init/merge.ts), read by `parseFileConfig`
# (JSON5 for `.json5`, JSONC for the rest), and each preset its `extends` names given its `presetSource` by `parsePreset`.
# Only the config's own `extends` are read: the presets they extend in turn are on the network.
PRESETS = """const [dist, ...folders] = process.argv.slice(2);
const fs = await import('node:fs');
const { getConfigFileNames } = await import(`${dist}/config/app-strings.js`);
const { parseFileConfig } = await import(`${dist}/config/parse.js`);
const { parsePreset } = await import(`${dist}/config/presets/parse.js`);
const out = {};
for (const folder of folders) {
  let found = null;
  for (const name of getConfigFileNames()) {
    const file = `${folder}/${name}`;
    if (!fs.existsSync(file) || !fs.statSync(file).isFile()) continue;
    const raw = fs.readFileSync(file, 'utf8');
    if (name === 'package.json') {
      let pJson;
      try { pJson = JSON.parse(raw); } catch { continue; }
      if (!pJson.renovate) continue;
      found = { file: name, config: typeof pJson.renovate === 'string' ? { extends: [pJson.renovate] } : pJson.renovate };
    } else {
      const parsed = parseFileConfig(name, raw.length ? raw : '{}');
      found = parsed.success ? { file: name, config: parsed.parsedContents } : { file: name, error: parsed.validationError };
    }
    break;
  }
  if (found && found.config) {
    const named = found.config.extends;
    found.presets = (Array.isArray(named) ? named : named ? [named] : []).map((preset) => {
      try { return { preset, source: parsePreset(preset).presetSource }; } catch (error) { return { preset, error: error.message }; }
    });
    delete found.config;
  }
  out[folder] = found;
}
process.stdout.write(JSON.stringify(out));
"""
INSIDE = ("internal", "relative")  # `parsePreset`'s sources Renovate resolves without a request: its own presets, the config's files


@app.function(cpu=1.0, memory=2048, timeout=1800, volumes={"/results": volume})
def renovate_presets(names: list) -> dict:
    """The Renovate config of each fixture of `names` and the presets it extends (`PRESETS`): a real repository's clone
    (`_real`), a hand-written fixture as it is."""
    sys.path[:0] = [REMOTE_SCRIPTS, REMOTE_PM, f"{REMOTE_PM}/tools"]
    dist = subprocess.run(["npm", "root", "-g"], capture_output=True, text=True, check=True).stdout.strip() + "/renovate/dist"
    script = Path("/tmp/daodan-presets.mjs")
    script.write_text(PRESETS, encoding="utf-8")
    folders = {}
    for name in names:
        fixture = Path(REMOTE_PM) / "fixtures" / name
        folders[name] = str(_real(name) if (fixture / "source.json").is_file() else fixture)
    done = subprocess.run(["node", str(script), dist, *folders.values()], capture_output=True, text=True, timeout=600,
                          env={**os.environ, "LOG_LEVEL": "fatal"})
    if done.returncode:
        raise RuntimeError(f"the presets' reader failed: {done.stderr.strip()[-600:]}")
    read = json.loads(done.stdout)
    return {"code": _code(), "renovate": _versions()["renovate"],
            "fixtures": {name: read[folder] for name, folder in folders.items()}}


def _answers(fixtures: list[str]) -> dict:
    """`egress-answers.json`, `{fixture: [host]}`, refused here before any sandbox when it is not that shape."""
    answers = json.loads((HERE / "egress-answers.json").read_text(encoding="utf-8"))
    if not isinstance(answers, dict) or any(name not in fixtures or not isinstance(hosts, list)
                                            or not all(isinstance(host, str) and host for host in hosts)
                                            for name, hosts in answers.items()):
        raise SystemExit("egress-answers.json: an object {fixture: [host]}, each fixture one of fixtures/ or projects.json")
    return answers


@app.local_entrypoint()
def main(store: str = "", score: str = "", out: str = "", runs: str = "", network: str = "", tools: str = "",
         presets: bool = False, hours: float = 4.0, parallel: int = 24):
    local = _code()
    print("code", local, flush=True)
    fixtures = sorted(p.name for p in (HERE / "fixtures").iterdir() if (p / "expected.json").is_file())
    if presets:  # every fixture's Renovate config and the presets it extends (`renovate_presets`)
        real = [n for n in fixtures if (HERE / "fixtures" / n / "source.json").is_file()]
        answers = list(renovate_presets.map([[n for n in fixtures if n not in real], *([n] for n in real)]))
        found = {name: said for answer in answers for name, said in answer["fixtures"].items()}
        remote = {name: [p for p in said.get("presets") or () if p.get("source") not in INSIDE]
                  for name, said in found.items() if said}
        summary = {"fixtures": len(found), "with_config": sum(bool(said) for said in found.values()),
                   "extending_outside": sorted(name for name, named in remote.items() if named),
                   "by_source": {source: sorted({n for n, named in remote.items() for p in named
                                                 if p.get("source", "error") == source})
                                 for source in sorted({p.get("source", "error") for named in remote.values()
                                                       for p in named})}}
        print(json.dumps(summary, indent=1), "remote code", sorted({a["code"] for a in answers}), "local", local, flush=True)
        Path(out).write_text(json.dumps({"summary": summary, "renovate": answers[0]["renovate"], "fixtures": found},
                                        indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        return
    if network:  # one real repository, Renovate with the network open and blocked (`renovate_network`)
        answer = renovate_network.remote(network, [t for t in tools.split(",") if t])
        print("remote code", answer["code"], "same" if answer["code"] == local else "DIFFERENT", flush=True)
        for arm, said in answer["arms"].items():
            print(arm, len(said["toolchains"]), "toolchains", said["packages"], "packages",
                  said["extract"]["returncode"], said["extract"]["managers"], flush=True)
        Path(out).write_text(json.dumps(answer, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        return
    cases = json.loads((REPO / "tests/fixtures/premap/projects.json").read_text(encoding="utf-8"))
    _answers([*fixtures, *cases])
    if store:
        start, done = _boxed_job({"mode": "store", "names": [s for s in store.split(",") if s]}, hours)
        print("remote code", start.get("code"), "same" if start.get("code") == local else "DIFFERENT",
              start.get("versions"), flush=True)
        for name, said in done.items():
            if "error" in said:
                print("not stored", name, said["error"], flush=True)
                continue
            target = REPO / "tests/fixtures/premap/outputs" / f"{name}.json"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps({"versions": start.get("versions"), "runs": said["runs"]}, indent=1,
                                         ensure_ascii=False) + "\n", encoding="utf-8")
            print("stored", name, len(said["runs"]), "requests", said["egress"]["requests"], flush=True)
    if not score:
        return
    batches = []
    for spec in score.split(","):
        if spec in ("js", "py", "jvm", "sys", "mix"):  # a family's hand-written fixtures in one sandbox
            batches.append([n for n in fixtures if n.startswith(spec + "-") and not (HERE / "fixtures" / n / "source.json").is_file()])
        elif spec == "real":  # every real repository in a sandbox of its own
            batches += [[n] for n in fixtures if (HERE / "fixtures" / n / "source.json").is_file()]
        elif spec:
            batches.append([spec])
    results, codes, asked = {}, set(), {}
    for start, done in _boxed_jobs([{"mode": "score", "names": names} for names in batches if names], hours, parallel):
        codes.add(start.get("code"))
        for name, result in done.items():
            log = result.pop("runs", None)
            if runs and log is not None:  # every model command with its answer, to replay the pre-map here
                import gzip
                target = Path(runs) / f"{name}.json.gz"
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(gzip.compress(json.dumps({"versions": start.get("versions"), "runs": log}, indent=1,
                                                            ensure_ascii=False).encode("utf-8") + b"\n", 9, mtime=0))
            for group in (result.get("egress") or {}).get("requests", ()):  # the requests nobody answered
                for request in group["requests"]:
                    asked.setdefault(f"{request['host']}:{request['port']}", set()).add(f"{name} ({group['tool']})")
        results.update(done)
    print("remote code", sorted(map(str, codes)), "same" if codes == {local} else "DIFFERENT", flush=True)
    print("requests without an answer:", json.dumps({host: sorted(seen) for host, seen in sorted(asked.items())},
                                                    indent=1) if asked else "none", flush=True)
    Path(out).write_text(json.dumps(results, indent=1), encoding="utf-8")
    print("scored", len(results), "errors", sum("error" in r for r in results.values()), "->", out, flush=True)
