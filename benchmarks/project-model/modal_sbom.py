"""SBOM group: Syft, Trivy, osv-scanner, cdxgen and ScanCode read the corpus of `fixtures/`, on Modal.

Every tool runs as a non-root user on a fresh copy of each fixture, with a clean environment, a fresh HOME and
logging shims on PATH in place of the build tools (so a tool that looks one up finds it and the log says so). Per
fixture: a traced run (strace on execve and connect, network on), a timed run (network on: seconds, peak memory of
the process tree) and an offline run (a container with the network blocked; its records come back as the call's
result and `fetch` stores them). Unless `--no-defaults`, a traced run also goes once with each tool's defaults on
a few fixtures. The fixture is hashed before and after every run. `fetch` scores with `score.py` into
`results/<tool>.json`. Deploy from a still copy of the fixtures, since the corpus agents keep writing:

    cp -r benchmarks/project-model/fixtures <stage>/ && PM_FIXTURES=<stage>/fixtures modal deploy benchmarks/project-model/modal_sbom.py
    python benchmarks/project-model/modal_sbom.py spawn [--tools syft,trivy] [--fixtures js-bun,...] [--no-defaults]
    python benchmarks/project-model/modal_sbom.py fetch [--tools ...]
    python benchmarks/project-model/modal_sbom.py reparse [--tools ...]   after an adapter change, no tool runs
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

import modal

HERE = Path(__file__).resolve().parent
LOCAL = modal.is_local()
ROOT = HERE if LOCAL else Path("/pm")
TOOLS = ("syft", "trivy", "osv_scanner", "cdxgen", "scancode")
ADDED = ("component_detection", "deptry", "dependency_cruiser", "uv_script")
# The hash every record of the first full run carries, over the five adapters and _sbom.py as they were then.
# syft, trivy, osv_scanner and scancode are unchanged since, so their stored records stay valid under it.
FIRST_RUN = "01963090825fe103bf04ca41e8b42e0e0cb0c303ea3b938d698d414ec8a6af42"
UNCHANGED_SINCE_FIRST_RUN = ("syft", "trivy", "osv_scanner", "scancode")
STORE = "project-model/sbom"
SHIMS = ("mvn", "mvnw", "gradle", "gradlew", "sbt", "ant", "java", "javac", "kotlinc", "npm", "npx", "node", "yarn",
         "pnpm", "bun", "deno", "go", "cargo", "rustc", "pip", "pip3", "python", "python3", "uv", "poetry", "pdm",
         "pipenv", "hatch", "conda", "dotnet", "nuget", "composer", "php", "bundle", "ruby", "gem", "mix", "elixir",
         "swift", "dart", "flutter", "cmake", "make", "conan", "vcpkg", "bazel", "git")
GH = "https://github.com"
INSTALL = [
    f"curl -sSfLO {GH}/anchore/syft/releases/download/v1.57.1/syft_1.57.1_linux_amd64.tar.gz"
    f" && curl -sSfLO {GH}/anchore/syft/releases/download/v1.57.1/syft_1.57.1_checksums.txt"
    " && sha256sum -c --ignore-missing syft_1.57.1_checksums.txt"
    " && tar -xzf syft_1.57.1_linux_amd64.tar.gz -C /usr/local/bin syft && rm syft_*",
    f"curl -sSfLO {GH}/aquasecurity/trivy/releases/download/v0.76.2/trivy_0.76.2_Linux-64bit.tar.gz"
    f" && curl -sSfLO {GH}/aquasecurity/trivy/releases/download/v0.76.2/trivy_0.76.2_checksums.txt"
    " && sha256sum -c --ignore-missing trivy_0.76.2_checksums.txt"
    " && tar -xzf trivy_0.76.2_Linux-64bit.tar.gz -C /usr/local/bin trivy && rm trivy_*",
    f"curl -sSfLO {GH}/google/osv-scanner/releases/download/v2.7.1/osv-scanner_linux_amd64"
    f" && curl -sSfLO {GH}/google/osv-scanner/releases/download/v2.7.1/osv-scanner_SHA256SUMS"
    " && sha256sum -c --ignore-missing osv-scanner_SHA256SUMS"
    " && install -m 755 osv-scanner_linux_amd64 /usr/local/bin/osv-scanner && rm osv-scanner_*",
    f"curl -sSfLO {GH}/CycloneDX/cdxgen/releases/download/v13.7.0/cdxgen-linux-amd64-slim"
    f" && curl -sSfLO {GH}/CycloneDX/cdxgen/releases/download/v13.7.0/cdxgen-linux-amd64-slim.sha256"
    " && sha256sum cdxgen-linux-amd64-slim && cat cdxgen-linux-amd64-slim.sha256"
    " && test \"$(sha256sum cdxgen-linux-amd64-slim | cut -c1-64)\" = \"$(cut -c1-64 cdxgen-linux-amd64-slim.sha256)\""
    " && install -m 755 cdxgen-linux-amd64-slim /usr/local/bin/cdxgen && rm cdxgen-*",
]


ADDED_INSTALL = [
    "apt-get update -q && apt-get install -y -q --no-install-recommends libicu72 xz-utils && rm -rf /var/lib/apt/lists/*",
    f"curl -sSfLo /usr/local/bin/component-detection {GH}/microsoft/component-detection/releases/download/v9.1.0/"
    "component-detection-linux-x64 && chmod 755 /usr/local/bin/component-detection"
    " && sha256sum /usr/local/bin/component-detection",  # the release publishes no checksum file: printed only
    "curl -sSfLO https://nodejs.org/dist/v22.23.4/node-v22.23.4-linux-x64.tar.xz"
    " && curl -sSfLO https://nodejs.org/dist/v22.23.4/SHASUMS256.txt"
    " && sha256sum -c --ignore-missing SHASUMS256.txt && mkdir -p /opt/node"
    " && tar -xJf node-v22.23.4-linux-x64.tar.xz -C /opt/node --strip-components 1 && rm node-v22.23.4* SHASUMS256.txt",
    "PATH=/opt/node/bin:$PATH /opt/node/bin/npm install -g --ignore-scripts dependency-cruiser@18.7.2",
    "pip install uv==0.13.8",
    "python -m venv /opt/deptry && /opt/deptry/bin/pip install -q deptry==0.25.1",  # its own environment only
]


def _shims() -> None:
    """A logging stand-in for every build tool, so a tool that looks one up on PATH finds it and runs it."""
    folder = Path("/shims")
    folder.mkdir(exist_ok=True)
    body = "\n".join(('#!/bin/sh', 'echo "$(basename "$0") $*" >> "${SHIM_LOG:-/dev/null}"',
                      'echo "shim: $(basename "$0") not run" >&2', 'exit 1', ''))
    for name in SHIMS:
        (folder / name).write_text(body, encoding="utf-8")
        (folder / name).chmod(0o755)


def _real() -> list:
    """A real-project fixture holds only source.json: its checkout at the pinned commit goes into the image, so the
    offline container has it too. Files only, no .git."""
    commands = []
    for source in sorted(Path(os.environ.get("PM_FIXTURES") or ROOT / "fixtures").glob("*/source.json")):
        data = json.loads(source.read_text(encoding="utf-8"))
        target = f"/pm/real/{source.parent.name}"
        commands.append(f"mkdir -p {target} && cd {target} && git init -q && git remote add origin {data['repo']}"
                        f" && git fetch -q --depth 1 origin {data['commit']} && git checkout -q FETCH_HEAD && rm -rf .git")
    return commands


def _image():
    return (
        modal.Image.debian_slim(python_version="3.12")
        .apt_install("ca-certificates", "curl", "strace", "procps", "git")
        .run_commands("useradd -m -u 1000 scan")  # cdxgen refuses secure mode as root; every tool runs as this user
        .run_commands(*INSTALL)
        .run_function(_shims)
        .run_commands("pip install scancode-toolkit==32.5.0 -c https://raw.githubusercontent.com/aboutcode-org/"
                      "scancode-toolkit/v32.5.0/requirements.txt")  # the release pins pluggy and plugincode
        .run_commands("scancode-reindex-licenses")  # the license index once, in the image, not in every run
        .run_commands(*(_real() or ["true"]))  # a new real fixture rebuilds from here
        .run_commands(*ADDED_INSTALL)
        .add_local_dir(ROOT / "tools", "/pm/tools", ignore=["**/__pycache__/**"])
        .add_local_dir(os.environ.get("PM_FIXTURES") or ROOT / "fixtures", "/pm/fixtures")  # a still copy
        .add_local_file(ROOT / "modal_sbom.py", "/pm/modal_sbom.py")
    )


app = modal.App("daodan-pm-sbom", image=_image())
VOLUME = "daodan-flow-results"
OFFLINE = "daodan-pm-sbom-offline"  # Modal Dict that carries the offline records out of the blocked containers
volume = modal.Volume.from_name(VOLUME, create_if_missing=True)


def code_sha256(tool: str) -> str:
    """The hash of one adapter and _sbom.py, printed by every container and kept in every record."""
    digest = hashlib.sha256()
    for path in (ROOT / "tools" / "_sbom.py", ROOT / "tools" / f"{tool}.py"):
        digest.update(path.name.encode() + b"\0" + path.read_bytes().replace(b"\r\n", b"\n"))
    return digest.hexdigest()


def _valid_codes(tool: str) -> set:
    return {code_sha256(tool)} | ({FIRST_RUN} if tool in UNCHANGED_SINCE_FIRST_RUN else set())


# Commands with each tool's defaults, traced on a few fixtures only, to say what the tool does when nobody
# switches anything off. `<p>` is the fixture, `<o>` the output file.
DEFAULTS = {
    "syft": ["syft", "scan", "dir:<p>", "-o", "syft-json=<o>"],
    "trivy": ["trivy", "fs", "--format", "json", "--list-all-pkgs", "-o", "<o>", "<p>"],
    "osv_scanner": ["osv-scanner", "scan", "source", "-r", "--format", "json", "--all-packages", "<p>"],
    "cdxgen": ["cdxgen", "-o", "<o>", "<p>"],
    "scancode": ["scancode", "--package", "--json", "<o>", "<p>"],
    "component_detection": ["component-detection", "scan", "--SourceDirectory", "<p>", "--ManifestFile", "<o>"],
}
# Third-party imports read in the files of the fixtures that declare little or nothing: the truth of the honesty
# score. undeclared: imported and declared nowhere; declared: imported and declared in the file itself (PEP 723)
# or in a manifest; not_dependencies: standard library, built-in or local modules.
HONESTY = {
    "py-undeclared-scripts": {"undeclared": ["yaml", "numpy", "sklearn", "PIL", "cv2"], "declared": [],
                              "not_dependencies": ["os", "json", "helpers"]},
    "js-node-scripts": {"undeclared": ["ms"], "declared": [], "not_dependencies": ["node:fs", "./lib.js"]},
    "js-static-html": {"undeclared": ["vue"], "declared": [], "not_dependencies": []},  # vue: an import map only
    "py-pep723-scripts": {"undeclared": [], "declared": ["requests", "rich", "pandas"],
                          "not_dependencies": ["json", "sys"]},
    "py-notebooks": {"undeclared": ["seaborn"], "declared": ["pandas"], "not_dependencies": ["nbproj"]},
}
PY_CANARY = ('__import__("os").environ.get("CANARY_FILE") and open(__import__("os").environ["CANARY_FILE"], "a")'
             '.write({path!r} + "\\n")  # canary of the sbom benchmark')
JS_CANARY = ('try {{ globalThis.process.getBuiltinModule("fs").appendFileSync(globalThis.process.env.CANARY_FILE, '
             '{path!r} + "\\n"); }} catch (e) {{}} // canary of the sbom benchmark')
DEFAULT_FIXTURES = ("js-npm-workspaces", "py-poetry-groups", "sys-go-single", "sys-rust-single", "jvm-maven-wrapper",
                    "jvm-gradle-locking")
BUILD_TOOLS = set(SHIMS) - {"git"}
WORK = Path("/work")
COMMIT_EVERY = 10
# Facts about a tool's coverage of the corpus that its results file must say itself.
NOTES = {"scancode": "Not measured on the eight real repositories added last: real-app-hoppscotch, "
                     "real-app-jhipster-sample, real-app-kotlinconf, real-app-memos, real-svc-eshop, real-svc-otel-demo, "
                     "real-svc-petclinic-microservices, real-svc-robot-shop (skipped for the budget). Its 114 fixtures "
                     "include real-app-full-stack-fastapi and real-svc-voting-app."}
BATCH = 8  # fixtures per offline call: fewer container starts, a result still small
MEMORY = {"scancode": 3072, "cdxgen": 1536, "component_detection": 1536}  # MB per container; the others peak near 250 MB


def _adapter(tool: str):
    import importlib
    sys.path.insert(0, str(ROOT / "tools"))
    return importlib.import_module(tool)


def _hashes(folder: Path) -> dict:
    out = {}
    for path in sorted(folder.rglob("*")):
        if path.is_file() and not path.is_symlink():
            out[path.relative_to(folder).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return out


def _fresh(fixture: str, run_dir: Path) -> Path:
    """A clean copy of the fixture and an empty work folder with HOME and TMPDIR, all owned by the scan user."""
    import shutil
    shutil.rmtree(run_dir, ignore_errors=True)
    project = run_dir / fixture
    real = Path("/pm/real") / fixture
    shutil.copytree(real if real.is_dir() else ROOT / "fixtures" / fixture, project, symlinks=True)
    for sub in ("home", "tmp", "out"):
        (run_dir / sub).mkdir(parents=True)
    import subprocess
    subprocess.run(["chown", "-R", "scan:scan", str(run_dir)], check=True)
    return project


def _tree(root_pid: int) -> tuple[int, dict]:
    """RSS in KB of root_pid and its descendants, and their {pid: command line}."""
    import os
    parent, rss, cmd = {}, {}, {}
    for entry in os.listdir("/proc"):
        if not entry.isdigit():
            continue
        try:
            stat = Path(f"/proc/{entry}/stat").read_text()
            parent[int(entry)] = int(stat[stat.rindex(")") + 2:].split()[1])
            status = Path(f"/proc/{entry}/status").read_text()
            rss[int(entry)] = next((int(line.split()[1]) for line in status.splitlines() if line.startswith("VmRSS:")), 0)
            cmd[int(entry)] = Path(f"/proc/{entry}/cmdline").read_bytes().replace(b"\0", b" ").decode(errors="replace")[:200]
        except (OSError, ValueError, IndexError):
            continue
    members, frontier = {root_pid}, [root_pid]
    while frontier:
        pid = frontier.pop()
        for child, dad in parent.items():
            if dad == pid and child not in members:
                members.add(child)
                frontier.append(child)
    return sum(rss.get(p, 0) for p in members), {p: cmd.get(p, "") for p in members if p != root_pid}


def measure(argv: list, env: dict, run_dir: Path, stdout_to: Path | None, trace: bool, timeout: int = 900,
            cwd: Path | None = None) -> dict:
    """Run argv as the scan user with a clean environment; seconds, peak memory of the process tree, the processes
    seen by sampling, and with `trace` the execve and connect calls strace saw."""
    import os
    import pwd
    import subprocess
    import threading
    import time
    user = pwd.getpwnam("scan")
    clean = {"PATH": "/shims:/usr/local/bin:/usr/bin:/bin", "HOME": str(run_dir / "home"), "TMPDIR": str(run_dir / "tmp"),
             "LANG": "C.UTF-8", "SHIM_LOG": str(run_dir / "shims.log"), "USER": "scan",
             "CANARY_FILE": str(run_dir / "canary.log")}
    clean.update(env)
    trace_file = run_dir / "trace.txt"
    if trace:
        argv = ["strace", "-f", "-qq", "-e", "trace=execve,execveat,connect", "-e", "signal=none", "-s", "300",
                "-o", str(trace_file), "--", *argv]
    out = open(stdout_to, "w", encoding="utf-8") if stdout_to else subprocess.DEVNULL
    err_path = run_dir / "stderr.txt"
    err = open(err_path, "w", encoding="utf-8")
    started = time.time()
    proc = subprocess.Popen([str(a) for a in argv], cwd=str(cwd or run_dir / "out"), env=clean, stdout=out, stderr=err,
                            user=user.pw_uid, group=user.pw_gid, extra_groups=[])
    peak, seen, stop = [0], {}, threading.Event()

    def sample():
        while not stop.is_set():
            total, members = _tree(proc.pid)
            peak[0] = max(peak[0], total)
            seen.update(members)
            stop.wait(0.05)

    sampler = threading.Thread(target=sample, daemon=True)
    sampler.start()
    timed_out = False
    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        proc.kill()
        proc.wait()
    seconds = round(time.time() - started, 2)
    stop.set()
    sampler.join()
    for handle in (out, err):
        if handle is not subprocess.DEVNULL:
            handle.close()
    record = {"rc": proc.returncode, "seconds": seconds, "peak_mb": round(peak[0] / 1024, 1), "timed_out": timed_out,
              "stderr": err_path.read_text(encoding="utf-8", errors="replace")[-1500:],
              "sampled": sorted({c.split(" ")[0] for c in seen.values() if c})}
    shims = run_dir / "shims.log"
    record["shims"] = shims.read_text(encoding="utf-8", errors="replace").splitlines()[:40] if shims.is_file() else []
    if trace:
        record.update(_strace(trace_file.read_text(encoding="utf-8", errors="replace")))
    return record


def _strace(text: str) -> dict:
    """Programs started (execve that returned 0, past the first) and non-loopback connect calls."""
    import re
    execs, attempts, endpoints = [], 0, {}
    first = True
    for line in text.splitlines():
        m = re.search(r'execve(?:at)?\((?:\d+, )?"([^"]+)", \[([^\]]*)\].*= (0|-1 \w+)', line)
        if m:
            if m.group(3) == "0":
                if first:
                    first = False
                    continue
                args = re.findall(r'"((?:[^"\\]|\\.)*)"', m.group(2))[1:4]
                execs.append(" ".join([m.group(1), *args])[:200])
            continue
        m = re.search(r"connect\(\d+, \{sa_family=AF_INET6?, sin6?_port=htons\((\d+)\).*?"
                      r"(?:inet_addr\(\"([\d.]+)\"\)|inet_pton\(AF_INET6, \"([0-9a-f:.]+)\")", line)
        if m:
            host = m.group(2) or m.group(3)
            if host.startswith("127.") or host in ("::1", "::ffff:127.0.0.1"):
                continue
            attempts += 1
            endpoints[f"{host}:{m.group(1)}"] = endpoints.get(f"{host}:{m.group(1)}", 0) + 1
    return {"execs": sorted(set(execs)), "network_attempts": attempts, "endpoints": endpoints}


def _names(endpoints: dict) -> dict:
    """Reverse names of the endpoints a traced run connected to, best effort."""
    import socket
    socket.setdefaulttimeout(3)
    names = {}
    for endpoint in endpoints:
        host = endpoint.rsplit(":", 1)[0]
        try:
            names[endpoint] = socket.gethostbyaddr(host)[0]
        except OSError:
            names[endpoint] = None
    return names


def _one(tool: str, fixture: str, mode: str) -> dict:
    """One fixture, one tool, one mode: `traced` (strace, network on), `timed` or `offline` (no strace)."""
    import shutil
    import subprocess
    adapter = _adapter(tool)
    run_dir = WORK / tool / mode / fixture
    project = _fresh(fixture, run_dir)
    planted = _plant(project) if getattr(adapter, "CANARY", False) else []
    before = _hashes(project)
    argv, env, out = adapter.command(project, run_dir / "out")
    subprocess.run(["chown", "-R", "scan:scan", str(run_dir)], check=True)  # folders command() made as root
    record = measure(argv, env, run_dir, out if getattr(adapter, "STDOUT", False) else None, trace=mode == "traced",
                     cwd=project if getattr(adapter, "CWD", None) == "project" else None)
    record["code"] = code_sha256(tool)
    if planted:
        log = run_dir / "canary.log"
        record["canary"] = {"planted": len(planted),
                            "fired": sorted(set(log.read_text(encoding="utf-8").split())) if log.is_file() else []}
    if getattr(adapter, "STDOUT", False) and record["rc"] == 128 and not out.read_text(encoding="utf-8").strip():
        out.write_text("{}", encoding="utf-8")
    after = _hashes(project)
    record["wrote_in_fixture"] = {"added": sorted(set(after) - set(before)), "removed": sorted(set(before) - set(after)),
                                  "changed": sorted(k for k in set(before) & set(after) if before[k] != after[k])}
    record["executed_project_code"] = _project_code(record, project, mode)
    try:
        ok = record["rc"] in getattr(adapter, "OK", (0,)) and out.is_file()
        record["output"] = adapter.parse(out, project) if ok else None
        record["error"] = None if ok else f"rc={record['rc']}"
        record["raw_bytes"] = out.stat().st_size if out.is_file() else 0
        if ok and hasattr(adapter, "honesty"):
            record["honesty"] = adapter.honesty(out, project)
    except Exception as exc:  # a parse failure is a result too
        record["output"], record["error"] = None, f"{type(exc).__name__}: {exc}"
    if mode != "traced" and out.is_file():
        import base64
        import gzip
        record["raw_gz"] = base64.b64encode(gzip.compress(out.read_bytes())).decode("ascii")  # for `reparse`
    shutil.rmtree(run_dir, ignore_errors=True)
    return record


def _plant(project: Path) -> list:
    """A canary statement in every Python, JavaScript and notebook file of the COPY: run or imported, it appends the
    file's path to $CANARY_FILE. It adds no import statement, so it changes no import a tool reads."""
    planted = []
    for path in sorted(project.rglob("*")):
        if not path.is_file() or path.is_symlink():
            continue
        rel = path.relative_to(project).as_posix()
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        first = text.split("\n", 1)[0]
        if path.suffix == ".ipynb":
            nb = json.loads(text)
            nb.setdefault("cells", []).insert(0, {"cell_type": "code", "execution_count": None, "metadata": {},
                                                  "outputs": [], "source": [PY_CANARY.format(path=rel)]})
            path.write_text(json.dumps(nb, indent=1), encoding="utf-8")
        elif path.suffix in (".py", ".js", ".mjs", ".cjs") or (not path.suffix and first.startswith("#!")
                                                              and ("python" in first or "node" in first)):
            line = (PY_CANARY if path.suffix == ".py" or "python" in first else JS_CANARY).format(path=rel)
            lines = text.split("\n")
            at = 1 if first.startswith("#!") else 0
            if len(lines) > at and "coding" in lines[at][:40] and lines[at].startswith("#"):
                at += 1  # keep an encoding cookie in the first two lines
            if "# /// script" in lines and "# ///" in lines[lines.index("# /// script"):]:
                at = lines.index("# ///", lines.index("# /// script")) + 1  # after a PEP 723 block, left intact
            lines.insert(at, line)
            path.write_text("\n".join(lines), encoding="utf-8")
        else:
            continue
        planted.append(rel)
    return planted


def _parse_again(tool: str, fixture: str, mode: str, record: dict) -> dict:
    """The adapter's answer again from the stored raw output, at the same paths the run used: no tool runs."""
    import base64
    import gzip
    import shutil
    adapter = _adapter(tool)
    run_dir = WORK / tool / mode / fixture
    project = _fresh(fixture, run_dir)
    _argv, _env, out = adapter.command(project, run_dir / "out")
    out.write_bytes(gzip.decompress(base64.b64decode(record["raw_gz"])))
    try:
        ok = record["rc"] in getattr(adapter, "OK", (0,))
        record["output"] = adapter.parse(out, project) if ok else None
        record["error"] = None if ok else f"rc={record['rc']}"
    except Exception as exc:
        record["output"], record["error"] = None, f"{type(exc).__name__}: {exc}"
    shutil.rmtree(run_dir, ignore_errors=True)
    return record


@app.function(cpu=1, memory=2048, timeout=3600, volumes={"/results": volume})
def reparse(tool: str, fixtures: list | None = None) -> dict:
    """After an adapter change: every stored online and offline record of `tool` parsed again from its raw output."""
    print("code", code_sha256(tool), flush=True)
    done = {}
    for mode, run_mode in (("online", "timed"), ("offline", "offline")):
        folder = Path("/results") / STORE / tool / mode
        for path in sorted(folder.glob("*.json")) if folder.is_dir() else []:
            if fixtures and path.stem not in fixtures:
                continue
            record = json.loads(path.read_text(encoding="utf-8"))
            if not record.get("raw_gz"):
                continue
            record = _parse_again(tool, path.stem, run_mode, record)
            path.write_text(json.dumps(record, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
            done[f"{mode}/{path.stem}"] = record["error"]
    volume.commit()
    return done


def _project_code(record: dict, project: Path, mode: str) -> str:
    """yes: a file of the fixture was executed; unknown: a build tool was started (a shim stood in, so what it
    would have run is not known); no: neither. Only a traced run can say no."""
    inside = [e for e in record.get("execs", []) if e.split(" ")[0].startswith(str(project))]
    if inside:
        return "yes"
    tools = [line.split(" ")[0] for line in record.get("shims", [])]
    if any(t in BUILD_TOOLS for t in tools):
        return "unknown"
    return "no" if mode == "traced" else "unknown"


def _corpus(chosen: list | None) -> list:
    names = sorted(p.name for p in (ROOT / "fixtures").iterdir() if p.is_dir() and not p.name.startswith(("_", ".")))
    return [n for n in names if not chosen or n in chosen]


def _store(tool: str, mode: str, fixture: str, record: dict) -> None:
    target = Path("/results") / STORE / tool / mode / f"{fixture}.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(record, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


@app.function(cpu=1, memory=3072, timeout=10800, volumes={"/results": volume})
def run_online(tool: str, fixtures: list | None = None, defaults: bool = True) -> dict:
    print("code", code_sha256(tool), flush=True)
    names = _corpus(fixtures)
    for n, fixture in enumerate(names):
        traced = _one(tool, fixture, "traced")
        traced["endpoint_names"] = _names(traced.get("endpoints", {}))
        timed = _one(tool, fixture, "timed")
        timed["traced"] = {k: traced.get(k) for k in ("execs", "network_attempts", "endpoints", "endpoint_names",
                                                       "shims", "sampled", "executed_project_code", "wrote_in_fixture",
                                                       "seconds", "error", "canary", "honesty")}
        timed["traced_same_output"] = traced.get("output") == timed.get("output")
        timed["executed_project_code"] = traced["executed_project_code"]
        _store(tool, "online", fixture, timed)
        if n % COMMIT_EVERY == COMMIT_EVERY - 1 or n == len(names) - 1:
            volume.commit()  # about 12 s each: every few fixtures, not after each
        print(fixture, timed["error"], timed["seconds"], traced.get("network_attempts"), flush=True)
    if defaults:
        for fixture in [f for f in DEFAULT_FIXTURES if f in _corpus(None)]:
            run_dir = WORK / tool / "default" / fixture
            project = _fresh(fixture, run_dir)
            argv = [a.replace("<p>", str(project)).replace("<o>", str(run_dir / "out" / "default.json"))
                    for a in DEFAULTS[tool]]
            record = measure(argv, {}, run_dir, run_dir / "out" / "stdout.txt", trace=True, timeout=600)
            record["endpoint_names"] = _names(record.get("endpoints", {}))
            record["executed_project_code"] = _project_code(record, project, "traced")
            record["command"] = " ".join(DEFAULTS[tool])
            _store(tool, "default", fixture, record)
            print("default", fixture, record["rc"], record.get("network_attempts"), record["shims"][:3], flush=True)
        volume.commit()
    return {"tool": tool, "fixtures": len(names)}


@app.function(cpu=1, memory=3072, timeout=3600, block_network=True, max_containers=5)
def run_offline(tool: str, fixtures: list) -> dict:
    """The same timed run for a few fixtures in a container without network. A blocked container can write
    neither the volume nor blob storage, where Modal puts a spawned call's result above about 8 KiB, so each record
    goes to the Modal Dict `OFFLINE` (served by Modal's own API, which stays reachable) and `fetch` stores it on the
    volume. A record keeps the answer's digest and keys, not the answer."""
    code = code_sha256(tool)
    print("code", code, flush=True)
    box = modal.Dict.from_name(OFFLINE, create_if_missing=True)
    for fixture in fixtures:
        record = _one(tool, fixture, "offline")
        record.pop("raw_gz", None)
        record["stderr"] = record.get("stderr", "")[-600:]
        output = record.pop("output", None)
        record["output_digest"] = _digest(output)
        record["output_keys"] = sorted(map(str, _names_of(output)))[:300] if output is not None else None
        record["code"] = code
        box[f"{tool}/{fixture}"] = json.dumps(record)
    return {"stored": len(fixtures), "code": code}


def _digest(output) -> str | None:
    """One hash for an answer, so a small offline record can say whether it equals the online one."""
    if output is None:
        return None
    return hashlib.sha256(json.dumps(output, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


@app.function(cpu=2, memory=4096, timeout=1800, volumes={"/results": volume})
def probe(commands: list[str]) -> str:
    """Exploration only: each shell command's whole output into probe/<n>.txt; /work/out is tarred to probe/out.tgz."""
    import shutil
    import subprocess
    import tarfile
    folder = Path("/results") / STORE / "probe"
    shutil.rmtree(folder, ignore_errors=True)
    folder.mkdir(parents=True)
    Path("/work/out").mkdir(parents=True, exist_ok=True)
    for n, command in enumerate(commands):
        done = subprocess.run(["bash", "-c", command], capture_output=True, text=True, timeout=900, cwd="/work")
        text = "\n".join((f"$ {command}", f"[{done.returncode}]", done.stdout, "--- stderr", done.stderr))
        (folder / f"{n:02d}.txt").write_text(text, encoding="utf-8")
    with tarfile.open(folder / "out.tgz", "w:gz") as tar:
        tar.add("/work/out", arcname="out")
    volume.commit()
    return str(len(commands))


def _read(path: str):
    try:
        return json.loads(b"".join(volume.read_file(path)).decode("utf-8"))
    except Exception:  # missing file
        return None


def _put(path: str, data) -> None:
    import tempfile
    with tempfile.TemporaryDirectory() as folder:
        local = Path(folder) / "f.json"
        local.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        with volume.batch_upload(force=True) as batch:
            batch.put_file(str(local), path)


def _calls() -> dict:
    return _read(f"{STORE}/calls.json") or {}


_CACHE = {}


def _records(tool: str, mode: str) -> dict:
    """The stored records of one tool and mode, downloaded once per fetch with the CLI (one parallel transfer)."""
    import shutil
    import subprocess
    import tempfile
    if tool not in _CACHE:
        folder = Path(tempfile.mkdtemp(prefix="sbom-"))
        done = subprocess.run(["modal", "volume", "get", "--force", VOLUME, f"{STORE}/{tool}", str(folder)],
                              capture_output=True, text=True)
        _CACHE[tool] = folder / tool
        if done.returncode != 0 and not _CACHE[tool].is_dir():
            print(tool, "volume get:", done.stderr[-300:])
    base = _CACHE[tool] / mode
    out = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in sorted(base.glob("*.json"))} if base.is_dir() else {}
    return out


def _offline(tool: str, call_ids: dict | None) -> dict:
    """The offline records: stored ones from the volume, the rest from the finished calls, stored in one batch."""
    import concurrent.futures
    import tempfile
    codes = _valid_codes(tool)
    stored = {f: r for f, r in _records(tool, "offline").items() if r.get("code") in codes}
    batches = (call_ids or {}).get("batches") if isinstance(call_ids, dict) else None
    todo = [(names, c) for names, c in (batches or []) if not all(n in stored for n in names)]

    def get(item):
        names, call_id = item
        try:
            return names, modal.FunctionCall.from_id(call_id).get(timeout=0), None
        except Exception as exc:  # still running or failed
            return names, None, exc

    fresh, waiting = {}, 0
    with concurrent.futures.ThreadPoolExecutor(16) as pool:
        for names, result, exc in pool.map(get, todo):
            if result is not None:
                if "gz" in result:  # a batch of an earlier driver, compressed in the result
                    import base64
                    import gzip
                    result = json.loads(gzip.decompress(base64.b64decode(result["gz"])))
                elif "stored" in result:
                    box = modal.Dict.from_name(OFFLINE, create_if_missing=True)
                    result = {n: json.loads(box[f"{tool}/{n}"]) for n in names if f"{tool}/{n}" in box}
                fresh.update({f: r for f, r in result.items() if r.get("code") in codes})
            else:
                waiting += len(names)
                if not isinstance(exc, TimeoutError):
                    print(tool, names[0], "... offline failed:", type(exc).__name__, str(exc)[:200])
    if fresh:
        with tempfile.TemporaryDirectory() as folder:
            with volume.batch_upload(force=True) as batch:
                for fixture, record in fresh.items():
                    local = Path(folder) / f"{fixture}.json"
                    local.write_text(json.dumps(record, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
                    batch.put_file(str(local), f"{STORE}/{tool}/offline/{fixture}.json")
        stored.update(fresh)
    if waiting:
        print(tool, waiting, "offline records not ready or failed")
    return stored


def _names_of(output: dict | None) -> set:
    return {(d.get("name"), d.get("resolved"), d.get("declared")) for d in (output or {}).get("dependencies", [])}


def _honesty(name: str, rec: dict) -> dict:
    """The honesty score of one record against HONESTY: imports reported as undeclared (good), imports reported
    as undeclared that are declared, built in or local (wrong), package names that appear in no file of the fixture
    (invented: the tool did not read them anywhere), and the canary files that ran."""
    truth = HONESTY[name]
    h = rec.get("honesty") or {}
    reported = set(h.get("undeclared") or [])
    undeclared, declared, other = set(truth["undeclared"]), set(truth["declared"]), set(truth["not_dependencies"])
    text = " ".join(p.read_text(encoding="utf-8", errors="replace").lower()
                    for p in (HERE / "fixtures" / name).rglob("*") if p.is_file() and p.name != "expected.json")
    names = set(h.get("packages") or []) | {d.get("name") for d in ((rec.get("output") or {}).get("dependencies") or [])}
    return {"undeclared_reported": sorted(reported & undeclared), "undeclared_missed": sorted(undeclared - reported),
            "wrongly_undeclared": sorted(reported & (declared | other)),
            "unexpected": sorted(reported - undeclared - declared - other),
            "invented_names": sorted(n for n in names if n and n.lower() not in text),
            "canary_planted": (rec.get("canary") or {}).get("planted"),
            "canary_fired": (rec.get("canary") or {}).get("fired"), "findings": (h.get("findings") or [])[:20]}


def fetch(tools: list) -> None:
    """Score every stored record with score.py and write results/<tool>.json, small: no raw output."""
    sys.path.insert(0, str(HERE))
    import score as scorer
    calls = _calls()
    for tool in tools:
        adapter = _adapter(tool)
        online, offline = _records(tool, "online"), _offline(tool, (calls.get(tool) or {}).get("offline"))
        fixtures = {}
        for name, rec in sorted(online.items()):
            expected_path = HERE / "fixtures" / name / "expected.json"
            expected = json.loads(expected_path.read_text(encoding="utf-8")) if expected_path.is_file() else None
            off = offline.get(name)
            traced = rec.get("traced") or {}
            off_digest = None if off is None else off.get("output_digest", _digest(off.get("output")))
            entry = {"output": rec.get("output"), "raw": f"{rec.get('raw_bytes', 0)} bytes",
                     "seconds": rec.get("seconds"), "peak_mb": rec.get("peak_mb"),
                     "network_attempts": traced.get("network_attempts"),
                     "network_endpoints": {k: (traced.get("endpoint_names") or {}).get(k)
                                           for k in traced.get("endpoints") or {}},
                     "offline_second_run": None if off is None else off_digest == _digest(rec.get("output")),
                     "executed_project_code": rec.get("executed_project_code"),
                     "started": traced.get("execs"), "build_tools_called": traced.get("shims"),
                     "wrote_in_fixture": {k: sorted(set(v) | set((traced.get("wrote_in_fixture") or {}).get(k, [])))
                                          for k, v in (rec.get("wrote_in_fixture") or {}).items() if
                                          v or (traced.get("wrote_in_fixture") or {}).get(k)},
                     "traced_same_output": rec.get("traced_same_output"),
                     "error": rec.get("error"), "stderr_tail": None if not rec.get("error") else rec.get("stderr")}
            if off is not None and off_digest != _digest(rec.get("output")):
                keys = set(off.get("output_keys") or map(str, _names_of(off.get("output"))))
                mine = set(map(str, _names_of(rec.get("output"))))
                entry["offline_diff"] = {"lost": sorted(mine - keys)[:30], "gained": sorted(keys - mine)[:30],
                                         "error": off.get("error"), "stderr_tail": off.get("stderr", "")[-400:]}
                if not (mine ^ keys) and len(keys) < 300 and not off.get("error"):
                    entry["offline_second_run"] = "same packages"  # order or a field outside the keys differs
            if expected is not None and isinstance(rec.get("output"), dict):
                entry["score"] = scorer.score(expected, rec["output"])
            if name in HONESTY and (rec.get("honesty") is not None or rec.get("canary")):
                entry["honesty"] = _honesty(name, rec)
                entry["honesty"]["traced_canary_fired"] = (traced.get("canary") or {}).get("fired")
                entry["honesty"]["offline_canary_fired"] = ((off or {}).get("canary") or {}).get("fired")
            fixtures[name] = entry
        defaults = {name: {k: rec.get(k) for k in ("command", "rc", "seconds", "network_attempts", "endpoint_names",
                                                    "execs", "shims", "executed_project_code")}
                    for name, rec in sorted(_records(tool, "default").items())}
        doc = {"tool": tool.replace("_", "-"), "version": adapter.VERSION, "group": "sbom", "command": adapter.COMMAND,
               "fixtures": fixtures, "defaults": defaults}
        if tool in NOTES:
            doc["notes"] = NOTES[tool]
        target = HERE / "results" / f"{tool}.json"
        target.parent.mkdir(exist_ok=True)
        target.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
        print(tool, len(fixtures), "fixtures,", sum(1 for f in fixtures.values() if f["error"]), "errors ->", target)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("probe", "probe-fetch", "spawn", "fetch", "reparse"))
    parser.add_argument("--tools", default=",".join(TOOLS + ADDED))
    parser.add_argument("--fixtures", default="")
    parser.add_argument("--file", help="with probe: a file holding one shell command per line")
    parser.add_argument("--no-defaults", action="store_true", help="with spawn: skip the traced runs with defaults")
    parser.add_argument("--offline-only", action="store_true", help="with spawn: only the offline runs")
    args = parser.parse_args()
    if args.command == "probe":
        lines = [line for line in Path(args.file).read_text(encoding="utf-8").splitlines() if line.strip()]
        print(modal.Function.from_name("daodan-pm-sbom", "probe").spawn(lines).object_id)
    elif args.command == "probe-fetch":
        import io
        import tarfile
        folder = Path(args.file)
        folder.mkdir(parents=True, exist_ok=True)
        for entry in volume.listdir(f"{STORE}/probe"):
            data = b"".join(volume.read_file(entry.path))
            if entry.path.endswith(".tgz"):
                with tarfile.open(fileobj=io.BytesIO(data)) as tar:
                    tar.extractall(folder, filter="data")
            else:
                (folder / Path(entry.path).name).write_bytes(data)
        print(folder)
    elif args.command == "spawn":
        print("local code", {t: code_sha256(t)[:12] for t in args.tools.split(",")})
        chosen = [f for f in args.fixtures.split(",") if f] or None
        calls = _calls()
        online = modal.Function.from_name("daodan-pm-sbom", "run_online")
        offline = modal.Function.from_name("daodan-pm-sbom", "run_offline")
        staged = Path(os.environ.get("PM_FIXTURES") or HERE / "fixtures")  # the copy the deployed app mounts
        names = [n for n in sorted(p.name for p in staged.iterdir() if p.is_dir() and not p.name.startswith(("_", ".")))
                 if not chosen or n in chosen]
        for tool in args.tools.split(","):
            entry = calls.setdefault(tool, {})
            size = {"memory": MEMORY.get(tool, 1024)}  # billed on the request: small for the Go binaries
            if not args.offline_only:
                entry["online"] = online.with_options(**size).spawn(tool, chosen, not args.no_defaults).object_id
            groups = [names[i:i + BATCH] for i in range(0, len(names), BATCH)]
            entry["offline"] = {"batches": [[g, offline.with_options(**size).spawn(tool, g).object_id] for g in groups]}
            print(tool, "online", entry.get("online"), "offline calls", len(groups))
        _put(f"{STORE}/calls.json", calls)
    elif args.command == "fetch":
        fetch(args.tools.split(","))
    elif args.command == "reparse":
        function = modal.Function.from_name("daodan-pm-sbom", "reparse")
        chosen = [f for f in args.fixtures.split(",") if f] or None
        for tool, call in [(t, function.spawn(t, chosen)) for t in args.tools.split(",")]:
            result = call.get()
            print(tool, len(result), "records,", sum(1 for e in result.values() if e), "errors")
