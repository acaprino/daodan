"""Frameworks and services group: Specfy stack-analyser, @vercel/fs-detectors, @netlify/build-info, alizer and
Railpack `info` read the corpus of `fixtures/` on Modal, against two read-only baselines (Daodan's service registry
and Daodan's stack-analyser wrapper).

Per tool and fixture the container copies the fixture without `expected.json` and `source.json`, makes it a git
repository (as Daodan's snapshot expects) and runs the adapter in a fresh child process three times: traced (strace
on execve and connect, plus a Node hook that logs every project file compiled as a module), timed (`/usr/bin/time`:
seconds and peak memory of the whole process tree) and offline (`unshare -rn`: no network). It records what was
executed, what tried the network, what the offline run changes and what was written inside the fixture. `tududi`
(repository and commit of `modal_audit.py`) runs the same way once per tool, unscored. The volume keeps one JSON per
tool and fixture; `fetch` scores them with `score.py` into `results/<tool>.json`.

    modal deploy benchmarks/project-model/modal_frameworks.py
    python benchmarks/project-model/modal_frameworks.py smoke --tools alizer --fixtures js-nextjs   # answer on screen
    python benchmarks/project-model/modal_frameworks.py spawn [--tools a,b] [--fixtures x,y] [--no-tududi]
    python benchmarks/project-model/modal_frameworks.py fetch [--tools a,b]
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _child(tool: str, fixture: str, work: str, destination: str) -> None:
    """One adapter run in its own process; the answer or the error goes to `destination`."""
    sys.path.insert(0, str(HERE / "tools") if (HERE / "tools").is_dir() else "/pm/tools")
    import importlib
    try:
        output = importlib.import_module(tool).run(fixture, work)
        Path(destination).write_text(json.dumps({"output": output}), encoding="utf-8")
    except Exception as error:  # the error text is the finding
        Path(destination).write_text(json.dumps({"error": f"{type(error).__name__}: {error}"[:1500]}), encoding="utf-8")


if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "child":
    _child(*sys.argv[2:6])
    sys.exit(0)

import modal  # noqa: E402

LOCAL = modal.is_local()
ROOT = HERE if LOCAL else Path("/pm")
PLUGIN = HERE.parents[1] / "plugins/codebase-map/skills/map" if LOCAL else Path("/daodan/map")
TOOLS = ("specfy_stack_analyser", "vercel_fs_detectors", "netlify_build_info", "alizer", "railpack_info",
         "daodan_registry", "daodan_stack_analyser")
STORE = "project-model/frameworks"
RUN_TIMEOUT = 240  # seconds for one execution of one adapter on one fixture (the call may raise it); the function is capped below
COMMIT_EVERY = 5  # a volume commit costs about 12 s
APP = "daodan-pm-frameworks"
GH = "https://github.com"
# tududi as in CASES of benchmarks/inference-audit/modal_audit.py
TUDUDI = {"repo": "https://github.com/chrisvel/tududi.git", "commit": "71da9d7b34dfd1600657e9c5ddf40420206fd263"}
INSTALL = [
    "mkdir -p /opt/tools /opt/cache/stack-analyser-1.27.6 && cd /opt/tools && npm init -y >/dev/null"
    " && npm install --ignore-scripts --no-audit --no-fund @specfy/stack-analyser@1.27.6 @vercel/fs-detectors@7.12.1"
    " @vercel/frameworks@3.35.0 @netlify/build-info@11.3.1"
    " && ln -s /opt/tools/node_modules /opt/cache/stack-analyser-1.27.6/node_modules",
    f"cd /opt && curl -sSfL -o alizer {GH}/devfile/alizer/releases/download/v1.10.0/alizer-v1.10.0-linux-amd64"
    f" && curl -sSfL -o alizer.sha256 {GH}/devfile/alizer/releases/download/v1.10.0/alizer-v1.10.0-linux-amd64.sha256"
    " && echo \"$(cut -c1-64 alizer.sha256)  alizer\" | sha256sum -c - && chmod +x alizer",
    f"cd /opt && curl -sSfLO {GH}/railwayapp/railpack/releases/download/v0.43.0/railpack-v0.43.0-x86_64-unknown-linux-musl.tar.gz"
    f" && curl -sSfLO {GH}/railwayapp/railpack/releases/download/v0.43.0/checksums.txt"
    " && sha256sum -c --ignore-missing checksums.txt && tar -xzf railpack-v0.43.0-x86_64-unknown-linux-musl.tar.gz"
    " && rm railpack-v0.43.0-x86_64-unknown-linux-musl.tar.gz checksums.txt && ls -la /opt/railpack",
]
HOOK = r"""
const Module = require('module'); const fs = require('fs');
const root = process.env.PM_FIXTURE_ROOT, log = process.env.PM_HOOK_LOG;
const compile = Module.prototype._compile;
Module.prototype._compile = function (content, filename) {
  if (root && log && filename.startsWith(root)) fs.appendFileSync(log, 'compile ' + filename + '\n');
  return compile.call(this, content, filename);
};
"""


def _image():
    return (
        modal.Image.from_registry("node:22-bookworm-slim", add_python="3.12")
        .apt_install("git", "curl", "ca-certificates", "strace", "util-linux", "time")
        .pip_install("tree-sitter==0.26.0", "tree-sitter-language-pack==1.13.5", "sqlglot>=30")
        .run_commands(*INSTALL)
        .add_local_dir(PLUGIN, "/daodan/map", ignore=["**/__pycache__/**", "**/tests/**"])
        .add_local_dir(ROOT / "tools", "/pm/tools", ignore=["**/__pycache__/**"])
        .add_local_dir(ROOT / "fixtures", "/pm/fixtures")
        .add_local_file(ROOT / "modal_frameworks.py", "/pm/modal_frameworks.py")
    )


app = modal.App(APP, image=_image())
volume = modal.Volume.from_name("daodan-flow-results", create_if_missing=True)


def code_sha256() -> str:
    """One hash over the adapters, compared with the local one before trusting a run."""
    digest = hashlib.sha256()
    for path in sorted((ROOT / "tools").glob("*.py")):
        if path.stem in TOOLS or path.stem == "_fw":
            digest.update(path.name.encode() + b"\0" + path.read_bytes().replace(b"\r\n", b"\n"))
    return digest.hexdigest()


def _run(command, cwd=None, timeout=900):
    import subprocess
    done = subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    if done.returncode:
        raise RuntimeError(f"{' '.join(map(str, command[:5]))} -> {done.returncode}\n{done.stderr[-1500:]}")
    return done


def _fixture_source(name: str, destination: Path) -> None:
    """The fixture's project files at `destination`, as a git repository; the answer files stay out."""
    import shutil
    source = ROOT / "fixtures" / name
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor = source / "source.json"
    if descriptor.is_file():
        info = json.loads(descriptor.read_text(encoding="utf-8"))
        _clone(info.get("repo") or info.get("repository") or info.get("url"),
               info.get("commit") or info.get("rev") or info.get("sha"), destination)
    else:
        shutil.copytree(source, destination, ignore=shutil.ignore_patterns("expected.json", "source.json"))
    if not (destination / ".git").exists():
        _run(["git", "init", "-q"], destination)
        _run(["git", "add", "-A"], destination)
        _run(["git", "-c", "user.name=bench", "-c", "user.email=bench@local", "commit", "-qm", "fixture"], destination)


def _clone(repo: str, commit: str, destination: Path) -> None:
    destination.mkdir(parents=True)
    _run(["git", "init", "-q"], destination)
    _run(["git", "remote", "add", "origin", repo], destination)
    _run(["git", "fetch", "-q", "--depth", "1", "origin", commit], destination)
    _run(["git", "checkout", "-q", "FETCH_HEAD"], destination)


def _listing(root: Path) -> dict:
    out = {}
    for path in root.rglob("*"):
        parts = path.relative_to(root).parts
        if ".git" in parts or not path.is_file():
            continue
        stat = path.stat()
        out[path.relative_to(root).as_posix()] = (stat.st_size, stat.st_mtime_ns)
    return out


def _trace(text: str) -> tuple[list[str], list[str]]:
    """(executed programs, non-loopback connections) from an strace log."""
    import re
    execs, connects = [], []
    for line in text.splitlines():
        if " execve(" in line and line.rstrip().endswith("= 0"):
            match = re.search(r'execve\("([^"]+)", \[(.*?)\]', line)
            if match:
                execs.append(match.group(1))
        elif " connect(" in line:
            match = re.search(r'sa_family=(AF_INET6?),.*?sin6?_port=htons\((\d+)\).*?(?:inet_addr|inet_pton)\([^"]*"([^"]+)"', line)
            if match and not match.group(3).startswith(("127.", "::1")):
                result = line.rsplit("=", 1)[-1].strip()
                connects.append(f"{match.group(3)}:{match.group(2)} {result}")
    return execs, connects


def _measure(tool: str, name: str, mode: str, source: Path, work: Path, limit: int = RUN_TIMEOUT) -> dict:
    """One child run of one adapter; `mode` is traced, timed or offline."""
    import shutil
    import subprocess
    import time
    (work).mkdir(parents=True, exist_ok=True)
    answer, trace, clock, hook = work / "answer.json", work / "strace.txt", work / "time.txt", work / "hook.txt"
    before = _listing(source)
    env = {**os.environ, "NODE_OPTIONS": "--require /tmp/pm_hook.js", "PM_FIXTURE_ROOT": str(source.resolve()),
           "PM_HOOK_LOG": str(hook), "HOME": f"/tmp/pm-home-{tool}",
           "PM_PLUGIN_SCRIPTS": "/daodan/map/scripts"}
    child = [sys.executable, "/pm/modal_frameworks.py", "child", tool, str(source), str(work / "w"), str(answer)]
    if mode == "traced":
        argv = ["strace", "-f", "-qq", "-s", "300", "-e", "trace=execve,connect", "-o", str(trace), *child]
    elif mode == "timed":
        argv = ["/usr/bin/time", "-f", "%e %M", "-o", str(clock), *child]
    else:
        argv = ["unshare", "-rn", *child]
    started = time.time()
    process = subprocess.Popen(argv, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=work,
                               start_new_session=True)
    try:
        stdout, stderr = process.communicate(timeout=limit)
        crashed = None if answer.is_file() else f"no answer, exit {process.returncode}: {(stderr or stdout)[-400:]}"
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, 9)
        process.communicate()
        crashed = f"timeout {limit} s"
    result = json.loads(answer.read_text(encoding="utf-8")) if answer.is_file() else {"error": crashed}
    result["wall_seconds"] = round(time.time() - started, 2)
    after = _listing(source)
    result["wrote"] = sorted(p for p in set(before) | set(after) if before.get(p) != after.get(p))[:20]
    if mode == "traced" and trace.is_file():
        result["execs"], result["connects"] = _trace(trace.read_text(encoding="utf-8", errors="replace"))
        result["compiled"] = sorted(set(hook.read_text().split("\n"))) if hook.is_file() else []
    if mode == "timed" and clock.is_file() and len(clock.read_text().split()) >= 2:
        seconds, kb = clock.read_text().split()[-2:]
        result["seconds"], result["peak_mb"] = float(seconds), round(int(kb) / 1024, 1)
    return result


OWN_PROGRAMS = {"python", "python3", "python3.12", "node", "alizer", "railpack", "git", "time", "unshare"}
SHELLS = {"sh", "bash", "dash", "npm", "npx", "yarn", "pnpm", "make", "gradle", "mvn", "pip", "uv", "cargo", "go"}


def _facts(traced: dict, source: Path) -> dict:
    execs = traced.get("execs", [])
    names = [Path(e).name for e in execs]
    inside = [e for e in execs if e.startswith(str(source.resolve()) + "/")]
    helpers = sorted({n for n in names if n not in OWN_PROGRAMS and not n.startswith("python")})
    compiled = [c for c in traced.get("compiled", []) if c]
    if inside or compiled or any(n in SHELLS for n in names):
        code = "yes"
    else:
        code = "no" if execs else "unknown"
    return {"executed_project_code": code, "programs": sorted(set(names)), "helpers": helpers,
            "project_files_compiled_by_node": compiled[:10], "network_attempts": len(traced.get("connects", [])),
            "network_destinations": sorted(set(traced.get("connects", [])))[:8]}


def _canon(value):
    if isinstance(value, dict):
        return {k: _canon(v) for k, v in value.items()}
    if isinstance(value, list):
        return sorted((_canon(v) for v in value), key=lambda v: json.dumps(v, sort_keys=True))
    return value


def _same(first: dict, second: dict) -> tuple[bool, str]:
    def core(r):
        out = r.get("output")
        return _canon({k: v for k, v in out.items() if k != "detail"}) if isinstance(out, dict) else r.get("error")
    a, b = core(first), core(second)
    if a == b:
        return True, "same output"
    if not isinstance(b, dict):
        return False, f"offline run failed: {b}"
    keys = sorted(k for k in set(a or {}) | set(b) if (a or {}).get(k) != b.get(k))
    return False, "differs in " + ", ".join(keys)


def _one(tool: str, name: str, source: Path, root: Path, modes=("traced", "timed", "offline"), limit: int = RUN_TIMEOUT) -> dict:
    """The runs of one tool on one prepared source (three by default); the source is rebuilt for each."""
    import shutil
    results = {}
    for mode in modes:
        copy = root / mode / name
        shutil.rmtree(root / mode, ignore_errors=True)
        shutil.copytree(source, copy, symlinks=True)
        results[mode] = _measure(tool, name, mode, copy, root / mode, limit)
    online = results["timed"]
    if modes != ("traced", "timed", "offline"):  # one run only: its facts are those of that run, the others are unmeasured
        record = {"error": online.get("error"), "modes": list(modes), "output": online.get("output"),
                  "seconds": online.get("seconds"), "peak_mb": online.get("peak_mb"),
                  "wrote_inside_fixture": online.get("wrote", [])}
        if record["output"] is None:
            del record["output"]
        return record
    record = {"error": online.get("error") or results["traced"].get("error")}
    if "output" in online:
        record["output"] = online["output"]
    same, note = _same(online, results["offline"])
    record.update(_facts(results["traced"], root / "traced" / name))
    record.update({"seconds": online.get("seconds"), "peak_mb": online.get("peak_mb"), "offline_second_run": same,
                   "offline_note": note, "wrote_inside_fixture": sorted({p for m in results.values() for p in m.get("wrote", [])})[:20]})
    if online.get("error"):
        record["error_offline"] = results["offline"].get("error")
    return record


@app.function(cpu=1, memory=2048, timeout=5400, volumes={"/results": volume})
def run_tool(tool: str, fixtures: list[str], tududi: bool = True, store: bool = True, timed_only: bool = False,
             limit: int = RUN_TIMEOUT) -> dict:
    import shutil
    import time
    Path("/tmp/pm_hook.js").write_text(HOOK, encoding="utf-8")
    sys.path.insert(0, "/pm/tools")
    adapter = __import__(tool)
    print("code", code_sha256(), flush=True)
    started = time.time()
    for cache in (f"/tmp/pm-home-{tool}", "/tmp/railpack"):  # the first fixture runs cold: downloads show there
        shutil.rmtree(cache, ignore_errors=True)
    Path(f"/tmp/pm-home-{tool}").mkdir(parents=True)
    root = Path("/work") / tool
    shutil.rmtree(root, ignore_errors=True)
    folder = Path("/results") / STORE / tool
    folder.mkdir(parents=True, exist_ok=True)
    answers = {}
    for name in [*fixtures, *(["tududi"] if tududi and "mix-real-tududi" not in fixtures else [])]:
        prepared = root / "prepared" / name
        if name == "tududi":
            _clone(TUDUDI["repo"], TUDUDI["commit"], prepared)
        else:
            _fixture_source(name, prepared)
        record = _one(tool, name, prepared, root / "runs" / name, modes=("timed",) if timed_only else ("traced", "timed", "offline"), limit=limit)
        record.update({"fixture": name, "tool": tool, "version": adapter.VERSION, "code": code_sha256()})
        record["first_run_of_container"] = not answers
        answers[name] = record
        if store:
            (folder / f"{name}.json").write_text(json.dumps(record, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
            if len(answers) % COMMIT_EVERY == 0:
                volume.commit()
        print(name, record.get("error") or "ok", record.get("seconds"), flush=True)
        shutil.rmtree(root / "runs" / name, ignore_errors=True)
        shutil.rmtree(prepared, ignore_errors=True)
    if store:
        volume.commit()
    return {"tool": tool, "fixtures": len(answers), "seconds": round(time.time() - started),
            **({} if store else {"answers": answers})}


def _expected_fixtures() -> list[str]:
    folder = HERE / "fixtures"
    return sorted(d.name for d in folder.iterdir() if d.is_dir() and not d.name.startswith("_") and (d / "expected.json").exists())


COMMANDS = {"specfy_stack_analyser": "stack-analyser <dir> --output=out.json",
            "vercel_fs_detectors": "node vercel_detect.cjs <dir> (getWorkspaces, detectFrameworks, packageManagers, monorepoManagers)",
            "netlify_build_info": "build-info <dir> [--rootDir <root>] at the root and each workspace package",
            "alizer": "alizer analyze <dir>; alizer component <dir> --no-port-detection",
            "railpack_info": "railpack info --format json <dir>",
            "daodan_registry": "snapshot.py write <dir> --no-engine --no-index; service_registry.recognize(manifest)",
            "daodan_stack_analyser": "stack_analyser.run(root, cache, files) over stack-analyser 1.27.6"}


def _local_hash():
    digest = hashlib.sha256()
    for path in sorted((HERE / "tools").glob("*.py")):
        if path.stem in TOOLS or path.stem == "_fw":
            digest.update(path.name.encode() + b"\0" + path.read_bytes().replace(b"\r\n", b"\n"))
    return digest


def fetch(tools: list[str]) -> None:
    sys.path.insert(0, str(HERE))
    import score
    results = HERE / "results"
    results.mkdir(exist_ok=True)
    local = _local_hash()
    for tool in tools:
        fixtures, tududi, version, codes = {}, None, "", {}
        for entry in volume.listdir(f"{STORE}/{tool}"):
            name = Path(entry.path).stem
            record = json.loads(b"".join(volume.read_file(f"{STORE}/{tool}/{name}.json")))
            version = record.get("version", version)
            codes.setdefault(record.pop("code", None), []).append(name)
            for key in ("fixture", "tool", "version"):
                record.pop(key, None)
            if name == "tududi":
                tududi = record
                continue
            exp = HERE / "fixtures" / name / "expected.json"
            if exp.is_file() and isinstance(record.get("output"), dict):
                got = {k: v for k, v in record["output"].items() if k != "detail"}
                full = score.score(json.loads(exp.read_text(encoding="utf-8")), got)
                record["score"] = {f: r for f, r in full.items() if r["given"]}
            if isinstance(record.get("output"), dict):  # the long parts of `detail` stay on the volume
                detail = record["output"].pop("detail", {})
                record["ids"] = detail.get("ids")
                if detail.get("technologies"):  # the tool's own type of each technology it found
                    record["id_types"] = {k: v["type"] for k, v in detail["technologies"].items()}
                if detail.get("entries"):  # the registry's kind of each entry it recognised
                    record["id_kinds"] = {k: v["kind"] for k, v in detail["entries"].items()}
                record["detail"] = {k: v for k, v in detail.items() if k not in ("ids", "technologies", "entries")}
            fixtures[name] = record
        if "mix-real-tududi" in fixtures:  # the same checkout, run by the current code
            tududi = fixtures["mix-real-tududi"]
            codes = {c: [n for n in names if n != "tududi"] for c, names in codes.items()}
            codes = {c: names for c, names in codes.items() if names}
        data = {"tool": tool, "version": version, "group": "frameworks", "command": COMMANDS[tool], "fixtures": fixtures}
        if tududi:
            data["tududi"] = tududi
        data["code"] = {"container": sorted(c for c in codes if c), "local_adapters": local.hexdigest()}
        stale = sorted(n for c, names in codes.items() for n in names if c != max(codes, key=lambda k: len(codes[k])))
        if stale:
            data["mixed_code"] = stale
        head = json.dumps({k: v for k, v in data.items() if k not in ("fixtures", "tududi")}, ensure_ascii=False)[:-1]
        lines = [f'"{n}":' + json.dumps(r, ensure_ascii=False, separators=(",", ":")) for n, r in sorted(fixtures.items())]
        tail = ',\n"tududi":' + json.dumps(data["tududi"], ensure_ascii=False, separators=(",", ":")) if "tududi" in data else ""
        (results / f"{tool}.json").write_text(head + ',\n"fixtures":{\n' + ",\n".join(lines) + "\n}" + tail + "}\n",
                                              encoding="utf-8", newline="\n")
        print(tool, len(fixtures), "fixtures", ("MIXED CODE: " + ",".join(stale)) if stale else "one code " + ",".join(c[:10] for c in codes if c))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("smoke", "spawn", "fetch"))
    parser.add_argument("--tools", default=",".join(TOOLS))
    parser.add_argument("--fixtures", default="")
    parser.add_argument("--no-tududi", action="store_true")
    parser.add_argument("--timed-only", action="store_true", help="one timed run per fixture, no trace and no offline run")
    parser.add_argument("--limit", type=int, default=RUN_TIMEOUT, help="seconds allowed to one execution of one adapter")
    args = parser.parse_args()
    chosen = [t.strip() for t in args.tools.split(",") if t.strip()]
    names = [f.strip() for f in args.fixtures.split(",") if f.strip()] or _expected_fixtures()
    if args.command == "fetch":
        fetch(chosen)
    else:
        print("local code", _local_hash().hexdigest())
        function = modal.Function.from_name(APP, "run_tool")
        if args.command == "smoke":
            for tool in chosen:
                answer = function.remote(tool, names, False, False, args.timed_only, args.limit)
                print(json.dumps(answer, ensure_ascii=False, indent=1))
        else:
            for tool in chosen:
                print(tool, function.spawn(tool, names, not args.no_tududi, True, args.timed_only, args.limit).object_id)
