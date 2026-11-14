"""Version group: which toolchain and build-tool versions a project asks for, read without running it, on Modal.

Tools: mise, proto, Renovate (local extraction), Railpack, and the native mechanisms (go mod edit and
GOTOOLCHAIN=auto, uv python find and venv, rustup, Corepack, the Gradle and Maven wrapper properties). No model.

    modal deploy benchmarks/project-model/modal_versions.py
    python benchmarks/project-model/modal_versions.py spawn [--tools mise,proto,...] [--only a,b]
    python benchmarks/project-model/modal_versions.py fetch [--tools ...]

Each tool runs in its own container on a fresh copy of every fixture (without `expected.json`) and a fresh HOME,
in variants: `open` (network on, tool defaults), `blocked` (a network namespace with no network) and, for the
tools that install a toolchain, `confined` (every cache inside the work directory) and `confined_offline` (the
same cache, no network). strace records execve, connect and the DNS queries; the bytes downloaded are the eth0
counter; the writes are a `find -newer` over the writable system folders, the HOME summary and a hash of the
project. Besides the corpus each tool reads small projects of its own (`EXTRA`: conflicts, ranges, Java, nothing
declared) and a canary project whose scripts, hooks and templates touch files under /tmp/pmv-canary, to see what
the tool executes. The volume keeps the records; `fetch` scores them with `score.py` into `results/<tool>.json`.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import modal

HERE = Path(__file__).resolve().parent
LOCAL = modal.is_local()
ROOT = HERE if LOCAL else Path("/pm")
APP = "daodan-pm-versions"
STORE = "project-model/versions"
V = {"node": "24.22.3", "renovate": "44.239.1", "corepack": "0.36.0", "mise": "v2026.11.8", "proto": "v0.64.0",
     "railpack": "v0.43.0", "uv": "0.13.8", "go": "1.23.12", "rustup": "1.29.3"}
GH = "https://github.com"
INSTALL = [
    f"curl -fsSL https://nodejs.org/dist/v{V['node']}/node-v{V['node']}-linux-x64.tar.xz"
    " | tar -xJ -C /usr/local --strip-components=1",
    f"npm install -g --no-audit --no-fund renovate@{V['renovate']} corepack@{V['corepack']} --force",
    f"mkdir -p /opt/mise && curl -fsSL {GH}/jdx/mise/releases/download/{V['mise']}/mise-{V['mise']}-linux-x64.tar.gz"
    " | tar -xz -C /opt/mise --strip-components=1 && ln -s /opt/mise/bin/mise /usr/local/bin/mise",
    f"mkdir -p /opt/proto && curl -fsSL {GH}/moonrepo/proto/releases/download/{V['proto']}/"
    "proto_cli-x86_64-unknown-linux-gnu.tar.xz | tar -xJ -C /opt/proto --strip-components=1"
    " && ln -s /opt/proto/proto /usr/local/bin/proto",
    f"curl -fsSL {GH}/railwayapp/railpack/releases/download/{V['railpack']}/"
    f"railpack-{V['railpack']}-x86_64-unknown-linux-musl.tar.gz | tar -xz -C /usr/local/bin railpack",
    f"mkdir -p /opt/gobase && curl -fsSL https://go.dev/dl/go{V['go']}.linux-amd64.tar.gz"
    " | tar -xz -C /opt/gobase --strip-components=1",
    f"curl -fsSL https://static.rust-lang.org/rustup/archive/{V['rustup']}/x86_64-unknown-linux-gnu/rustup-init"
    " -o /usr/local/bin/rustup-init && chmod +x /usr/local/bin/rustup-init"
    " && RUSTUP_HOME=/opt/rustup CARGO_HOME=/opt/cargo rustup-init -y --default-toolchain none --no-modify-path",
]


def _image():
    return (
        modal.Image.debian_slim(python_version="3.13")
        .apt_install("git", "ca-certificates", "curl", "xz-utils", "unzip", "strace", "util-linux", "procps")
        .run_commands(*INSTALL)
        .pip_install(f"uv=={V['uv']}", "psutil")
        .add_local_dir(ROOT / "tools", "/pm/tools", ignore=["**/__pycache__/**"])
        .add_local_dir(ROOT / "fixtures", "/pm/fixtures")
        .add_local_file(ROOT / "score.py", "/pm/score.py")
        .add_local_file(ROOT / "modal_versions.py", "/pm/modal_versions.py")
    )


app = modal.App(APP, image=_image())
volume = modal.Volume.from_name("daodan-flow-results", create_if_missing=True)

INSTALLERS = {"go_auto", "uv_venv", "rustup_auto", "corepack"}
# The tools an ecosystem mechanism can be asked about; the general readers (mise, proto, Renovate, Railpack) are
# scored on every expected toolchain, the mechanisms also on their own ecosystem alone (`score_scope`).
SCOPE = {"go_edit": {"go"}, "go_auto": {"go"}, "uv_find": {"python"}, "uv_venv": {"python"}, "rustup": {"rust"},
         "rustup_auto": {"rust"}, "corepack": {"npm", "pnpm", "yarn", "bun"},
         "wrapper_props": {"gradle", "maven", "maven-wrapper", "gradle-wrapper"}}
TOOLS = ("mise", "proto", "renovate", "railpack", "go_edit", "go_auto", "uv_find", "uv_venv", "rustup",
         "rustup_auto", "corepack", "wrapper_props")
COMMAND = {
    "mise": "MISE_SAFE=1 MISE_OFFLINE=1 mise ls --current --json", "proto": "proto status --json",
    "renovate": "renovate --platform=local --dry-run=extract --report-type=file",
    "railpack": "railpack info --format json .",
    "go_edit": "GOTOOLCHAIN=local go env GOMOD GOWORK; go mod edit -json; go work edit -json",
    "go_auto": "GOTOOLCHAIN=auto go version", "uv_find": "uv python find -v",
    "uv_venv": "uv venv --python-preference only-managed", "rustup": "RUSTUP_AUTO_INSTALL=0 rustup show",
    "rustup_auto": "RUSTUP_AUTO_INSTALL=1 rustup show active-toolchain",
    "corepack": "corepack yarn|pnpm --version with the network off, then corepack <declared> --version",
    "wrapper_props": "properties parser (gradle-wrapper.properties, maven-wrapper.properties)"}
CANARY_DIR = "/tmp/pmv-canary"
PATH = "/opt/gobase/bin:/opt/cargo/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
# Writable folders scanned after a traced run. /usr/local and /opt hold the tools themselves (tens of thousands
# of files): a scan of them took half a minute per run here and no tool is expected to write there.
SCAN = ["/root", "/tmp", "/var/tmp", "/var/cache", "/etc", "/home", "/srv", "/mnt"]
# Blocked-network runs (no strace) beyond the key fixtures: the cases where the network may matter.
BLOCKED = ("x-node-ranges", "x-node-conflict", "x-python-range", "x-java-files", "x-nothing")
# The fixtures that get the traced runs (strace, blocked network, write scan, install variants); the extras
# below always do. The other fixtures run once, untraced, for the score and the time.
KEY = ("js-version-conflict", "py-version-disagree", "sys-go-toolchain", "sys-rust-toolchain-conflict",
       "jvm-maven-wrapper", "js-yarn-berry")

# Projects of our own, for the cases the corpus may not cover. `toolchains` is written by hand from the files.
EXTRA = {
    "x-node-conflict": {
        "files": {".nvmrc": "22.1.0\n", ".node-version": "20.11.1\n", ".tool-versions": "nodejs 18.19.0\n",
                  "package.json": '{"name":"x","engines":{"node":">=18.17 <21"},"volta":{"node":"20.11.1"}}\n'},
        "toolchains": [
            {"tool": "node", "version": "22.1.0", "declared_in": ".nvmrc"},
            {"tool": "node", "version": "20.11.1", "declared_in": ".node-version"},
            {"tool": "node", "version": "18.19.0", "declared_in": ".tool-versions"},
            {"tool": "node", "version": ">=18.17 <21", "declared_in": "package.json"},
            {"tool": "node", "version": "20.11.1", "declared_in": "package.json"}]},
    "x-node-ranges": {
        "files": {".nvmrc": "lts/*\n"},
        "toolchains": [{"tool": "node", "version": "lts/*", "declared_in": ".nvmrc"}]},
    "x-node-major": {
        "files": {".node-version": "20\n"},
        "toolchains": [{"tool": "node", "version": "20", "declared_in": ".node-version"}]},
    "x-node-engines": {
        "files": {"package.json": '{"name":"x","engines":{"node":">=18"}}\n'},
        "toolchains": [{"tool": "node", "version": ">=18", "declared_in": "package.json"}]},
    "x-python-range": {
        "files": {"pyproject.toml": '[project]\nname = "x"\nversion = "0.1.0"\nrequires-python = ">=3.10,<3.13"\n'},
        "toolchains": [{"tool": "python", "version": ">=3.10,<3.13", "declared_in": "pyproject.toml"}]},
    "x-python-pinned-and-range": {
        "files": {".python-version": "3.12\n",
                  "pyproject.toml": '[project]\nname = "x"\nversion = "0.1.0"\nrequires-python = ">=3.13"\n'},
        "toolchains": [{"tool": "python", "version": "3.12", "declared_in": ".python-version"},
                       {"tool": "python", "version": ">=3.13", "declared_in": "pyproject.toml"}]},
    "x-java-files": {
        "files": {".java-version": "11\n", ".sdkmanrc": "java=21.0.2-tem\n", ".tool-versions": "java temurin-17.0.9\n"},
        "toolchains": [{"tool": "java", "version": "11", "declared_in": ".java-version"},
                       {"tool": "java", "version": "21.0.2-tem", "declared_in": ".sdkmanrc"},
                       {"tool": "java", "version": "temurin-17.0.9", "declared_in": ".tool-versions"}]},
    "x-java-build": {
        "files": {"pom.xml": "<project><modelVersion>4.0.0</modelVersion><groupId>g</groupId><artifactId>a</artifactId>"
                             "<version>1</version><properties><java.version>17</java.version></properties></project>\n",
                  "build.gradle": "plugins { id 'java' }\njava { toolchain { languageVersion = JavaLanguageVersion.of(21) } }\n"},
        "toolchains": [{"tool": "java", "version": "17", "declared_in": "pom.xml"},
                       {"tool": "java", "version": "21", "declared_in": "build.gradle"}]},
    "x-go-older": {
        "files": {"go.mod": "module example.com/x\n\ngo 1.20\n", "main.go": "package main\n\nfunc main() {}\n"},
        "toolchains": [{"tool": "go", "version": "1.20", "declared_in": "go.mod"}]},
    "x-subfolders": {
        "files": {"packages/a/.nvmrc": "20.11.0\n", "packages/b/.python-version": "3.12.1\n"},
        "toolchains": [{"tool": "node", "version": "20.11.0", "declared_in": "packages/a/.nvmrc"},
                       {"tool": "python", "version": "3.12.1", "declared_in": "packages/b/.python-version"}]},
    "x-nothing": {"files": {"README.md": "# nothing declared\n"}, "toolchains": []},
}
# Scripts, hooks and templates that run when something evaluates the project; each touches a file in CANARY_DIR.
_T = f"touch {CANARY_DIR}/"
CANARY = {
    "mise.toml": ('[tools]\nnode = "20"\n\n[env]\nFROM_TEMPLATE = "{{exec(command=\'' + _T + 'mise-env-template\')}}"\n'
                  '_.source = "./canary-env.sh"\n\n[hooks]\nenter = "' + _T + 'mise-hook-enter"\n\n'
                  '[tasks.canary]\nrun = "' + _T + 'mise-task"\n'),
    "canary-env.sh": _T + "mise-env-source\n",
    ".tool-versions": "nodejs 20.11.0\n",
    "package.json": ('{"name":"c","packageManager":"yarn@4.5.0","engines":{"node":">=18"},"scripts":{"preinstall":"'
                     + _T + 'npm-preinstall","postinstall":"' + _T + 'npm-postinstall"}}\n'),
    "build.gradle": "new File('" + CANARY_DIR + "/gradle-build').text = 'x'\nplugins { id 'java' }\n",
    "settings.gradle": "new File('" + CANARY_DIR + "/gradle-settings').text = 'x'\nrootProject.name = 'c'\n",
    "gradlew": "#!/bin/sh\n" + _T + "gradlew\n",
    "gradle/wrapper/gradle-wrapper.properties":
        "distributionUrl=https\\://services.gradle.org/distributions/gradle-8.10-bin.zip\n",
    "mvnw": "#!/bin/sh\n" + _T + "mvnw\n",
    ".mvn/extensions.xml": "<extensions/>\n",
    "pom.xml": "<project><modelVersion>4.0.0</modelVersion><groupId>g</groupId><artifactId>c</artifactId>"
               "<version>1</version></project>\n",
    "setup.py": f"open('{CANARY_DIR}/setup-py', 'w').close()\nfrom setuptools import setup\nsetup(name='c')\n",
    "pyproject.toml": '[project]\nname = "c"\nversion = "0"\nrequires-python = ">=3.10"\n[build-system]\n'
                      'requires = []\nbuild-backend = "backend"\nbackend-path = ["."]\n',
    "backend.py": f"open('{CANARY_DIR}/python-backend', 'w').close()\n",
    "go.mod": "module example.com/c\n\ngo 1.23\n",
    "main.go": "package main\n\n//go:generate " + _T + "go-generate\nfunc main() {}\n",
    "rust-toolchain.toml": '[toolchain]\npath = "' + CANARY_DIR + '/fake-toolchain"\n',
    "Cargo.toml": '[package]\nname = "c"\nversion = "0.1.0"\nedition = "2021"\n',
    "build.rs": "fn main() { std::fs::File::create(\"" + CANARY_DIR + "/build-rs\").unwrap(); }\n",
    "src/main.rs": "fn main() {}\n",
    "Makefile": "all:\n\t" + _T + "make\n",
    ".envrc": _T + "envrc\n",
    "renovate.json": '{"extends":["config:recommended"],"postUpgradeTasks":{"commands":["' + _T + 'renovate-task"]}}\n',
}


def code_sha256() -> str:
    """One hash over the adapters, compared with the local one before trusting a run."""
    digest = hashlib.sha256()
    for path in sorted((ROOT / "tools").glob("*.py")):
        if path.stem in TOOLS or path.stem == "_versions":
            digest.update(path.name.encode() + b"\0" + path.read_bytes().replace(b"\r\n", b"\n"))
    return digest.hexdigest()


# ---------------------------------------------------------------- measuring (runs in the container)

def _rx() -> int:
    for line in Path("/proc/net/dev").read_text().splitlines():
        if line.strip().startswith("eth0:"):
            return int(line.split(":", 1)[1].split()[0])
    return 0


def _tree(root: Path) -> dict:
    found = {}
    for path in sorted(root.rglob("*")):
        if path.is_file() and not path.is_symlink():
            found[path.relative_to(root).as_posix()] = hashlib.sha1(path.read_bytes()).hexdigest()
    return found


def _du(path: Path) -> int:
    return sum(p.stat().st_size for p in path.rglob("*") if p.is_file() and not p.is_symlink())


def _dns_names(log: str) -> list:
    import re
    names = []
    for m in re.finditer(r'(?:sendto\(\d+, |iov_base=)"((?:[^"\\]|\\.)*)"', log):
        try:
            raw = bytes(m.group(1), "latin-1").decode("unicode_escape").encode("latin-1")
        except (UnicodeError, ValueError):
            continue
        if len(raw) < 17:
            continue
        i, labels = 12, []
        while i < len(raw) and 0 < raw[i] < 64 and i + raw[i] < len(raw):
            labels.append(raw[i + 1:i + 1 + raw[i]].decode("ascii", "replace"))
            i += raw[i] + 1
        if labels and raw[i:i + 1] == b"\0" and all(re.fullmatch(r"[A-Za-z0-9_-]+", x) for x in labels):
            names.append(".".join(labels))
    return sorted(set(names))


def _strace(log_path: Path, project: Path) -> dict:
    import re
    log = log_path.read_text(errors="replace") if log_path.exists() else ""
    execs, project_exec, project_args = [], [], []
    for m in re.finditer(r'execve\("([^"]+)", \[(.*?)\], .*?\) = 0', log):
        exe, argv = m.group(1), m.group(2)
        execs.append(exe)
        if "/pm/tools/_versions.py" in argv:
            continue  # the adapter's own interpreter
        if exe.startswith(str(project)):
            project_exec.append(exe + " " + argv[:120])  # a file of the project run as a program
        elif str(project) in argv:
            project_args.append(exe.rsplit("/", 1)[-1] + " " + argv[:100])  # a program told to read the project
    connects = []
    pattern = (r'connect\(\d+, \{sa_family=(AF_INET6?), sin6?_port=htons\((\d+)\), '
               r'sin6?_addr=(?:inet_addr|inet_pton)\((?:AF_INET6, )?"([^"]+)"[^}]*\}, \d+\) = (-?\d+[^\n]*)')
    for m in re.finditer(pattern, log):
        fam, port, addr, result = m.groups()
        if addr.startswith("127.") or addr in ("::1", "0.0.0.0"):
            continue
        connects.append(f"{addr}:{port} {result.strip()[:30]}")
    return {"execs": sorted(set(execs)), "project_exec": project_exec[:10], "project_args": project_args[:6], "connects": sorted(set(connects))[:12],
            "connect_count": len(connects), "hosts": _dns_names(log)}


def _writes(stamp: Path, skip: str) -> list:
    import subprocess
    cmd = ["find", *SCAN, "-xdev", "-newer", str(stamp), "-type", "f", "-not", "-path", f"{skip}/*",
           "-not", "-path", "/tmp/pmv-*", "-not", "-path", "/tmp/modal*", "-not", "-path", "/var/lib/dpkg/*"]
    done = subprocess.run(cmd, capture_output=True, text=True)
    return sorted(x for x in done.stdout.splitlines() if x)


def _home_summary(home: Path) -> dict:
    files = [p for p in home.rglob("*") if p.is_file()]
    tops = {}
    for p in files:
        parts = p.relative_to(home).parts
        key = "/".join(parts[:3]) if parts[0] in (".local", ".cache", ".config") else parts[0]
        tops[key] = tops.get(key, 0) + p.stat().st_size
    return {"count": len(files), "bytes": sum(tops.values()),
            "top": dict(sorted(tops.items(), key=lambda kv: -kv[1])[:8])}


def _variant(tool, name, source: Path, base: Path, variant, blocked, confine, extra_env=None, reuse=False,
             canary=False, traced=True) -> dict:
    """One run of the adapter. `traced` adds strace, the network namespace when `blocked`, the project hash and
    the scan of the writable system folders; an untraced run only times the adapter (the scan is slow here)."""
    import shutil
    import subprocess
    import time
    vdir = base / variant
    proj, home, work = vdir / "proj", vdir / "home", vdir / "work"
    if not reuse:
        shutil.rmtree(vdir, ignore_errors=True)
        shutil.copytree(source, proj, symlinks=True, ignore=shutil.ignore_patterns("expected.json", ".git"))
        home.mkdir(parents=True)
        work.mkdir(parents=True)
    out, log, stamp = vdir / "out.json", vdir / "strace.log", vdir / "stamp"
    for f in (out, log):
        f.unlink(missing_ok=True)
    if traced:
        shutil.rmtree(CANARY_DIR, ignore_errors=True)
        Path(CANARY_DIR).mkdir(parents=True)
    if canary:
        fake = Path(CANARY_DIR) / "fake-toolchain" / "bin"
        fake.mkdir(parents=True)
        for exe in ("rustc", "cargo"):
            (fake / exe).write_text(f"#!/bin/sh\ntouch {CANARY_DIR}/fake-{exe}\necho 'rustc 1.0.0'\n")
            (fake / exe).chmod(0o755)
    env = {"PATH": PATH, "HOME": str(home), "LANG": "C.UTF-8", "PYTHONDONTWRITEBYTECODE": "1", "TMPDIR": "/tmp",
           "PMV_CONFINE": "1" if confine else "0", **(extra_env or {})}
    cmd = ["python", "-I", "/pm/tools/_versions.py", tool, str(proj), str(work), str(out)]
    if traced:
        cmd = ["strace", "-f", "-qq", "-e", "trace=execve,connect,sendto,sendmmsg", "-s", "300", "-o", str(log), *cmd]
    if blocked:
        cmd = ["unshare", "-rn", *cmd]
    stamp.write_text("x")
    time.sleep(0.05)
    before = _tree(proj) if traced else {}
    rx0, t0 = _rx(), time.time()
    timeout = 60  # per execution; a tool that needs longer is reported as a timeout
    try:
        done = subprocess.run(cmd, env=env, cwd=str(vdir), capture_output=True, text=True, timeout=timeout)
        crashed = None if out.exists() else (done.stderr or done.stdout)[-300:]
    except subprocess.TimeoutExpired:
        crashed = f"timeout after {timeout}s"
    wall, rx1 = round(time.time() - t0, 1), _rx()
    record = json.loads(out.read_text(encoding="utf-8")) if out.exists() else {"output": None, "error": crashed}
    record.update({"variant": variant, "traced": traced, "wall": wall, "rx_bytes": rx1 - rx0,
                   "home": _home_summary(home),
                   "cache_bytes": _du(work / "cache") if (work / "cache").exists() else 0})
    if traced:
        after = _tree(proj)
        t1 = time.time()
        record.update({
            **_strace(log, proj),
            "proj_created": sorted(set(after) - set(before))[:10],
            "proj_deleted": sorted(set(before) - set(after))[:10],
            "proj_modified": sorted(k for k in before if k in after and before[k] != after[k])[:10],
            "elsewhere": _writes(stamp, str(vdir.parent.parent))[:30],
            "canary": sorted(p.name for p in Path(CANARY_DIR).iterdir() if p.name != "fake-toolchain")})
        record["scan_seconds"] = round(time.time() - t1, 1)
    return record


def _write_extra(name: str, root: Path) -> Path:
    files = CANARY if name == "x-canary" else EXTRA[name]["files"]
    folder = root / name
    for rel_path, body in files.items():
        target = folder / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8")
        if rel_path in ("gradlew", "mvnw", "canary-env.sh"):
            target.chmod(0o755)
    return folder


def _runs(tool, name, source, base, canary, traced, blocked, installs_traced) -> dict:
    runs = {"open": _variant(tool, name, source, base, "open", False, False, canary=canary, traced=traced)}
    if blocked:
        runs["blocked"] = _variant(tool, name, source, base, "blocked", True, False, canary=canary, traced=traced)
    if tool in INSTALLERS and installs_traced:
        runs["confined"] = _variant(tool, name, source, base, "confined", False, True, canary=canary)
        runs["confined_offline"] = _variant(tool, name, source, base, "confined", True, True, reuse=True,
                                            canary=canary)
        runs["confined_offline"]["variant"] = "confined_offline"
    if tool == "mise" and canary:
        runs["unsafe"] = _variant(tool, name, source, base, "unsafe", False, False,
                                  {"PMV_MISE_SAFE": "0", "MISE_TRUSTED_CONFIG_PATHS": "/w"}, canary=True)
    return runs


def _measure_all(tools: list, only: list | None, budget_s: int, label: str) -> dict:
    """One container, every tool: first the key fixtures and our own projects with the facts, then the other
    fixtures once, untraced, each tool on the same fixture before the next fixture. Records are written to the
    volume after every fixture; what the budget leaves out is listed as skipped."""
    import shutil
    import time
    start = time.time()
    print("adapters sha256", code_sha256(), flush=True)
    names = sorted(d.name for d in (ROOT / "fixtures").iterdir()
                   if d.is_dir() and not d.name.startswith("_") and (d / "expected.json").exists()
                   and not (d / "source.json").exists())
    pool = sorted(EXTRA) + ["x-canary"]
    if only:
        names, pool = [n for n in names if n in only], [n for n in pool if n in only]
    order = [n for n in KEY if n in names] + pool + [n for n in names if n not in KEY]
    records = {t: {} for t in tools}
    skipped = {t: [] for t in tools}
    folder = Path("/results") / STORE
    folder.mkdir(parents=True, exist_ok=True)

    def save():
        for t in tools:
            (folder / f"{t}.records.{label}.json").write_text(json.dumps(
                {"tool": t, "adapters": code_sha256(), "skipped": skipped[t], "records": records[t]},
                ensure_ascii=False), encoding="utf-8")
        volume.commit()

    done_count = 0
    for name in order:
        source = ROOT / "fixtures" / name if name in names else _write_extra(name, Path("/w") / "extra")
        extra = name not in names
        traced = name in KEY or name == "x-canary"
        blocked = name in KEY or name in BLOCKED
        for tool in tools:
            if time.time() - start > budget_s:
                skipped[tool].append(name)
                continue
            base = Path("/w") / tool / name
            runs = _runs(tool, name, source, base, name == "x-canary", traced, blocked or traced, traced)
            records[tool][name] = {"extra": extra, "runs": runs}
            shutil.rmtree(base, ignore_errors=True)
            print(tool, name, {k: ((v["error"] or "ok")[:40], v["wall"], v.get("scan_seconds")) for k, v in runs.items()},
                  flush=True)
        done_count += 1
        if done_count % 6 == 0:
            save()  # a commit of the volume takes about ten seconds here: one per six fixtures
    save()
    return {"tools": tools, "fixtures": len(order), "skipped": {t: len(v) for t, v in skipped.items()},
            "seconds": round(time.time() - start)}


def _clone(name: str, root: Path) -> tuple:
    """The pinned commit of a descriptor fixture, shallow when the host allows it. Returns (path, seconds, error)."""
    import shutil
    import subprocess
    import time
    desc = json.loads((ROOT / "fixtures" / name / "source.json").read_text(encoding="utf-8"))
    target = root / name
    shutil.rmtree(target, ignore_errors=True)
    target.mkdir(parents=True)
    t0 = time.time()
    steps = [["git", "init", "-q"], ["git", "remote", "add", "origin", desc["repo"]],
             ["git", "fetch", "-q", "--depth", "1", "origin", desc["commit"]], ["git", "checkout", "-q", "FETCH_HEAD"]]
    for step in steps:
        done = subprocess.run(step, cwd=target, capture_output=True, text=True, timeout=300)
        if done.returncode:
            return target, round(time.time() - t0, 1), f"{' '.join(step[:2])}: {done.stderr.strip()[-200:]}"
    return target, round(time.time() - t0, 1), None


def _measure_real(tools: list, only: list | None, budget_s: int, label: str) -> dict:
    """The descriptor fixtures (`source.json`): clone each pinned commit once, run every tool on a copy, untraced,
    open network, one run each. Records are committed every six repositories."""
    import shutil
    import time
    start = time.time()
    print("adapters sha256", code_sha256(), flush=True)
    names = sorted(d.name for d in (ROOT / "fixtures").iterdir()
                   if d.is_dir() and not d.name.startswith("_") and (d / "expected.json").exists()
                   and (d / "source.json").exists() and (not only or d.name in only))
    records = {t: {} for t in tools}
    skipped = {t: [] for t in tools}
    folder = Path("/results") / STORE
    folder.mkdir(parents=True, exist_ok=True)

    def save():
        for t in tools:
            (folder / f"{t}.records.{label}.json").write_text(json.dumps(
                {"tool": t, "adapters": code_sha256(), "skipped": skipped[t], "records": records[t]},
                ensure_ascii=False), encoding="utf-8")
        volume.commit()

    for number, name in enumerate(names):
        if time.time() - start > budget_s:
            for t in tools:
                skipped[t].append(name)
            continue
        source, clone_s, error = _clone(name, Path("/w") / "clones")
        files = sum(1 for p in source.rglob("*") if p.is_file() and ".git" not in p.parts)
        print(name, "clone", clone_s, "s", files, "files", error or "ok", flush=True)
        for tool in tools:
            if error:
                skipped[tool].append(name)
                continue
            if time.time() - start > budget_s:
                skipped[tool].append(name)
                continue
            base = Path("/w") / tool / name
            try:
                runs = _runs(tool, name, source, base, False, False, False, False)
            except Exception as exc:  # noqa: BLE001 - one repository must not end the pass
                print(" ", tool, "driver failure", f"{type(exc).__name__}: {exc}"[:150], flush=True)
                skipped[tool].append(name)
                continue
            runs["open"]["clone_seconds"], runs["open"]["clone_files"] = clone_s, files
            records[tool][name] = {"extra": False, "runs": runs}
            shutil.rmtree(base, ignore_errors=True)
            print(" ", tool, runs["open"]["wall"], (runs["open"]["error"] or "ok")[:60], flush=True)
        shutil.rmtree(source, ignore_errors=True)
        if number % 6 == 5:
            save()
    save()
    return {"tools": tools, "repos": len(names), "seconds": round(time.time() - start)}


@app.function(cpu=1, memory=3072, timeout=900, volumes={"/results": volume})
def measure_real(tools: list, only: list | None = None, budget_s: int = 840, label: str = "real") -> dict:
    return _measure_real(tools, only, budget_s, label)


@app.function(cpu=1, memory=3072, timeout=900, volumes={"/results": volume})
def measure_all(tools: list, only: list | None = None, budget_s: int = 840, label: str = "a") -> dict:
    return _measure_all(tools, only, budget_s, label)


@app.function(cpu=2, memory=4096, timeout=1800, volumes={"/results": volume})
def probe(commands: list[str], block_network: bool = False, files: dict | None = None) -> str:
    import os
    import subprocess
    os.makedirs("/w/p", exist_ok=True)
    for name, body in (files or {}).items():
        target = Path("/w/p") / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8")
    out = []
    for command in commands:
        if block_network:
            command = "unshare -rn sh -c " + json.dumps(command)
        done = subprocess.run(["bash", "-c", command], capture_output=True, text=True, timeout=900, cwd="/w/p")
        out.append(f"$ {command}\n[{done.returncode}]\n{done.stdout[-8000:]}\n{done.stderr[-3000:]}")
    text = "\n".join(out)
    target = Path("/results") / STORE / "probe.txt"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    volume.commit()
    return text


# ---------------------------------------------------------------- local: spawn and fetch

def _fixture_expected() -> dict:
    out = {}
    for d in sorted((HERE / "fixtures").iterdir()):
        if d.is_dir() and not d.name.startswith("_") and (d / "expected.json").exists():
            out[d.name] = json.loads((d / "expected.json").read_text(encoding="utf-8"))
    return out


RUN_NOTES = ("Modal spend read from `modal billing report`: the first full run (12 containers, stopped after about "
             "40 minutes) and a smoke run cost about 0.25 USD and left no per-fixture records (they were written only "
             "at the end); the second run (three 15 minute containers, a fourth for the rest, a Renovate rerun) "
             "about 0.17 USD against the 0.10 cap, so the total is over the cap. Untraced fixtures ran once, "
             "without strace, blocked network or write scan; the key fixtures and the `x-` projects ran traced. The 18 "
             "descriptor fixtures (`real-*`, `mix-real-*`) were cloned at the pinned commit inside the container and "
             "ran once, untraced, network open (two containers; the first stopped on a dangling symlink in a copy). "
             "Billing read at the end: 0.406 USD for the app, the last hours not fully billed yet.")


def build_results(tool: str, doc: dict) -> dict:
    """Score one tool's records into the shape of SCHEMA.md plus the measured facts."""
    sys.path.insert(0, str(HERE))
    import score
    expected = _fixture_expected()
    fixtures, extras = {}, {}
    for name, rec in doc["records"].items():
        runs = rec["runs"]
        op, bl = runs["open"], runs.get("blocked") or {}
        exp = {"toolchains": EXTRA[name]["toolchains"]} if rec["extra"] and name in EXTRA else expected.get(name)
        out = op.get("output") if isinstance(op.get("output"), dict) else None
        entry = {"output": out, "error": op.get("error"), "seconds": op.get("seconds"), "peak_mb": op.get("peak_mb"),
                 "network_attempts": op.get("connect_count"), "hosts": op.get("hosts"),
                 "executed_project_code": ("yes" if op.get("project_exec") or op.get("canary") else "no")
                 if op.get("traced") else "unknown",
                 "offline_second_run": (bl.get("output") == out and bl.get("error") is None) if bl else None,
                 "blocked": {"error": bl.get("error"), "output": bl.get("output"), "connects": bl.get("connects"),
                             "hosts": bl.get("hosts")}}
        if exp is not None and out is not None:
            full = score.score(exp, out)
            entry["score"] = {k: v for k, v in full.items() if v.get("given")}
            if tool in SCOPE:
                mine = dict(exp, toolchains=[t for t in exp.get("toolchains", []) if t.get("tool") in SCOPE[tool]])
                entry["score_scope"] = {k: v for k, v in score.score(mine, out).items() if k == "toolchains"}
        if out is not None and bl.get("output") is not None and exp is not None:
            full = score.score(exp, bl["output"])
            entry["blocked_score"] = {k: v for k, v in full.items() if v.get("given")}
        for k in ("execs", "project_exec", "project_args", "connects", "rx_bytes", "wall", "home", "elsewhere", "proj_created",
                  "proj_modified", "proj_deleted", "canary", "cache_bytes"):
            entry[k] = op.get(k)
        for variant in ("confined", "confined_offline", "unsafe"):
            if variant in runs:
                r = runs[variant]
                entry[variant] = {k: r.get(k) for k in ("output", "error", "seconds", "rx_bytes", "home", "elsewhere",
                                                        "cache_bytes", "canary", "proj_created", "proj_modified",
                                                        "connect_count", "hosts", "execs")}
        (extras if rec["extra"] else fixtures)[name] = entry
    version = next((r["runs"]["open"].get("version") for r in doc["records"].values() if r["runs"]["open"].get("version")), None)
    return {"tool": tool, "version": version, "group": "versions", "command": COMMAND[tool], "adapters": doc["adapters"],
            "fixtures": fixtures, "extras": extras, "skipped": doc.get("skipped") or []}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("probe", "probe-fetch", "spawn", "fetch"))
    parser.add_argument("--file")
    parser.add_argument("--blocked", action="store_true")
    parser.add_argument("--files", help="with probe: a JSON file {path: text} written into /w/p first")
    parser.add_argument("--tools", default=",".join(TOOLS))
    parser.add_argument("--only", default="", help="with spawn: fixture or extra names, comma separated")
    parser.add_argument("--real", action="store_true", help="with spawn: the descriptor fixtures (source.json)")
    parser.add_argument("--label", default="a", help="with spawn: name of this container's record files")
    parser.add_argument("--budget", type=int, default=840, help="with spawn: seconds before the rest is skipped")
    args = parser.parse_args()
    chosen = [t for t in args.tools.split(",") if t]
    if args.command == "probe":
        lines = [x for x in Path(args.file).read_text(encoding="utf-8").splitlines() if x.strip()]
        print(modal.Function.from_name(APP, "probe").spawn(
            lines, args.blocked, json.loads(Path(args.files).read_text(encoding="utf-8")) if args.files else None
        ).object_id)
    elif args.command == "probe-fetch":
        sys.stdout.buffer.write(b"".join(volume.read_file(f"{STORE}/probe.txt")))
    elif args.command == "spawn":
        print("local adapters sha256", code_sha256())
        only = [x for x in args.only.split(",") if x] or None
        fn = "measure_real" if args.real else "measure_all"
        print(modal.Function.from_name(APP, fn).spawn(chosen, only, args.budget, args.label).object_id)
    else:
        for tool in chosen:
            doc = {"tool": tool, "adapters": None, "skipped": [], "records": {}}
            for entry in volume.listdir(STORE):
                leaf = Path(entry.path).name
                if not (leaf.startswith(tool + ".records.") and leaf.endswith(".json")):
                    continue
                part = json.loads(b"".join(volume.read_file(f"{STORE}/{leaf}")))
                doc["adapters"] = part["adapters"]
                doc["records"].update(part["records"])
                doc["skipped"] += part["skipped"]
            if not doc["records"]:
                print(tool, "no records yet")
                continue
            doc["skipped"] = sorted(set(doc["skipped"]) - set(doc["records"]))
            results = build_results(tool, doc)
            (HERE / "results").mkdir(exist_ok=True)
            results["run_notes"] = RUN_NOTES
            top = json.dumps({k: v for k, v in results.items() if k not in ("fixtures", "extras")}, ensure_ascii=False)
            body = [top[:-1]]
            for key in ("fixtures", "extras"):
                rows = [f"  {json.dumps(n)}: {json.dumps(e, ensure_ascii=False, separators=(',', ':'))}"
                        for n, e in results[key].items()]
                body.append(f', "{key}": {{' + chr(10) + (',' + chr(10)).join(rows) + chr(10) + '}')
            (HERE / "results" / f"{tool}.json").write_text(chr(10).join(body) + '}' + chr(10), encoding="utf-8", newline=chr(10))
            print(tool, len(results["fixtures"]), "fixtures,", len(results["extras"]), "extras; adapters", doc["adapters"])
