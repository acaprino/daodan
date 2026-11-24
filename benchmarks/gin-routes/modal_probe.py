"""Gin's `Routes()` and debug hooks on Modal, in a container with the network blocked. Written on 23 November 2026, run on 24 November
2026 (`results/`); the answer comes back in compressed pieces (a call with the network blocked cannot return more than about 8 KB).

    PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal python -m modal run benchmarks/gin-routes/modal_probe.py
    VARIANTS=hook-names,app-panic ... (a choice of `PROBES`)

The image is built with the network open (the one moment it is): the fixture's `go mod tidy` (makes `go.sum`), `go mod download` and one
`go build`, so the module and build caches are in the image. Each probe then runs with the network blocked, in a copy of the fixture:
`go build -overlay` adds one file of `hooks/` to the build of the copy (the tree gets no new file: the probe lists what is left in it),
then the binary runs under `timeout`. The project's code runs only in the container. Every answer (`argv`, `returncode`, `seconds`, peak
memory, the ports that listened during the run, the processes left, the file the hook wrote, the files left in the copy) goes to
`results/<probe>.json`; the probes that collect handler names are followed by the toolchain's own `go tool nm` and `go tool addr2line`
on the binary, to see whether a name gives a file and a line.
"""
import json
import os
import pathlib

import modal

HERE = pathlib.Path(__file__).resolve().parent
LOCAL = modal.is_local()
FIXTURE = HERE / "fixture"
HOOKS = HERE / "hooks"
OUT = HERE / "results"

GO_ENV = {"GOMODCACHE": "/gomod", "GOCACHE": "/gocache", "GOTOOLCHAIN": "local", "GOFLAGS": "-buildvcs=false"}
image = modal.Image.from_registry("golang:1.25-bookworm", add_python="3.12").env(GO_ENV)
if LOCAL:
    image = image.add_local_dir(FIXTURE, "/fix", copy=True)
    image = image.run_commands("cd /fix && go mod tidy && go mod download && go build -o /dev/null .",
                               "cd /fix && go list -m github.com/gin-gonic/gin")
    image = image.add_local_dir(HOOKS, "/probe", copy=True)
app = modal.App("gin-routes", image=image)

# probe -> (overlay file or None, environment, seconds the binary has, whether the names are resolved to file and line)
PROBES = {
    # the official hooks, Gin's debug mode (its default), stopped at the line every Run* prints before it binds
    "hook-names": ("hook_names.go", {"GIN_MODE": "debug", "DAODAN_STOP": "1"}, 20, True),
    "hook-no-stop": ("hook_names.go", {"GIN_MODE": "debug"}, 20, False),  # Run binds: the port watcher must see it
    "hook-release-env": ("hook_names.go", {"GIN_MODE": "release", "DAODAN_STOP": "1"}, 20, False),  # IsDebugging() false: silent
    "hook-release-code": ("hook_names.go", {"FIXTURE_RELEASE": "1", "DAODAN_STOP": "1"}, 20, False),  # gin.SetMode in main(): silent
    # the debug text on standard output, no file added to the build
    "debug-stdout": (None, {"GIN_MODE": "debug"}, 20, False),
    # `Routes()` with HandlerFunc, file and line, through the project's own `setupRouter()` (a convention of the fixture only)
    "routes-in-init": ("routes_in_init.go", {"DAODAN_ROUTES": "1"}, 20, False),
    # the application does not load
    "app-panic": ("hook_names.go", {"FIXTURE_FAIL": "panic", "DAODAN_STOP": "1"}, 20, False),
    "app-db": ("hook_names.go", {"FIXTURE_FAIL": "db", "DAODAN_STOP": "1"}, 20, False),
    "app-block": ("hook_names.go", {"FIXTURE_FAIL": "block", "DAODAN_STOP": "1"}, 20, False),  # limit ends it: exit 124 or 137
    "app-panic-routes-in-init": ("routes_in_init.go", {"FIXTURE_FAIL": "panic", "DAODAN_ROUTES": "1"}, 20, False),
}


def _listening() -> set[int]:
    ports = set()
    for table in ("/proc/net/tcp", "/proc/net/tcp6"):
        try:
            for line in open(table).read().splitlines()[1:]:
                fields = line.split()
                if fields[3] == "0A":  # LISTEN
                    ports.add(int(fields[1].rsplit(":", 1)[1], 16))
        except OSError:
            pass
    return ports


def _run(argv: list[str], cwd: str, env: dict | None = None, out_file: str | None = None, stdin: str | None = None) -> dict:
    """One command: time, peak memory (the child's, `wait4`), the ports that listened while it ran, what it left running."""
    import subprocess
    import tempfile
    import threading
    import time

    before, seen, done = _listening(), set(), threading.Event()

    def watch():
        while not done.is_set():
            seen.update(_listening())
            time.sleep(0.05)

    watcher = threading.Thread(target=watch, daemon=True)
    started = time.monotonic()
    with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr, tempfile.TemporaryFile() as fed:
        fed.write((stdin or "").encode())
        fed.seek(0)
        watcher.start()
        process = subprocess.Popen(argv, cwd=cwd, stdin=fed, stdout=stdout, stderr=stderr, env={**os.environ, "NO_COLOR": "1", **(env or {})})
        _, status, usage = os.wait4(process.pid, 0)
        seconds = round(time.monotonic() - started, 2)
        done.set()
        watcher.join()
        stdout.seek(0), stderr.seek(0)
        out, err = stdout.read().decode("utf-8", "replace"), stderr.read().decode("utf-8", "replace")
    left = subprocess.run(["ps", "-eo", "pid,args"], capture_output=True, text=True).stdout
    written = pathlib.Path(out_file).read_text(encoding="utf-8") if out_file and os.path.isfile(out_file) else None
    return {"argv": argv, "returncode": os.waitstatus_to_exitcode(status), "seconds": seconds,
            "peak_memory_mb": round(usage.ru_maxrss / 1024), "ports_listening": sorted(seen - before),
            "processes_left": [l.strip() for l in left.splitlines() if "/app" in l or "timeout" in l],
            "stdout": out[-6000:], "stderr": err[-3000:], "written": written[:100000] if written else None,
            "written_bytes": len(written) if written else 0}


def _listing(root: str) -> dict[str, int]:
    found = {}
    for directory, _names, files in os.walk(root):
        for f in files:
            path = os.path.join(directory, f)
            found[os.path.relpath(path, root).replace("\\", "/")] = os.path.getsize(path)
    return found


def _symbols(binary: str, names: list[str], cwd: str) -> list[dict]:
    """The toolchain's `go tool nm` (name -> address) and `go tool addr2line` (address -> file:line) for each handler name; a name
    ending in `-fm` (the wrapper the compiler writes for a method value) is also resolved without it, the method's own symbol."""
    nm = subprocess_text(["go", "tool", "nm", binary], cwd)
    address = {}
    for line in nm.splitlines():
        parts = line.split(None, 2)
        if len(parts) == 3:
            address.setdefault(parts[2].strip(), parts[0])
    rows = []
    for name in dict.fromkeys(names):
        row = {"handler": name}
        for key, symbol in (("", name), ("method_", name.removesuffix("-fm") if name.endswith("-fm") else None)):
            if symbol is None:
                continue
            row[key + "address"] = address.get(symbol)
            if symbol in address:
                row[key + "addr2line"] = subprocess_text(["go", "tool", "addr2line", binary], cwd, "0x" + address[symbol] + "\n").splitlines()
        rows.append(row)
    return rows


def subprocess_text(argv: list[str], cwd: str, stdin: str | None = None) -> str:
    """The whole standard output of one toolchain command (`_run` keeps only its tail)."""
    import subprocess

    return subprocess.run(argv, cwd=cwd, input=stdin, capture_output=True, text=True).stdout


CHUNK = 6000  # bytes: with the network blocked a call cannot return more than about 8 KB, so the answer comes back in pieces


@app.function(cpu=2, memory=4096, timeout=1800, block_network=True)
def probe(names: list[str]):
    import zlib

    payload = zlib.compress(json.dumps(_probe(names)).encode("utf-8"), 9)
    for start in range(0, len(payload), CHUNK):
        yield payload[start:start + CHUNK]


def _probe(names: list[str]) -> dict:
    import shutil
    import subprocess

    def version(*argv):
        return subprocess.run(argv, cwd="/fix", capture_output=True, text=True).stdout.strip().splitlines()[:1]

    out = {"_env": {"go": version("go", "version"), "gin": version("go", "list", "-m", "github.com/gin-gonic/gin")}}
    for name in names:
        overlay, env, seconds, resolve = PROBES[name]
        project = f"/work/{name}"
        shutil.rmtree(project, ignore_errors=True)
        shutil.copytree("/fix", project)
        before = _listing(project)
        build = ["go", "build", "-o", f"/work/{name}.bin"]
        if overlay:  # a file that exists only for the build: the tree is not touched
            config = f"/work/{name}-overlay.json"
            pathlib.Path(config).write_text(json.dumps({"Replace": {f"{project}/zz_daodan.go": f"/probe/{overlay}"}}), encoding="utf-8")
            build += ["-overlay", config]
        built = _run([*build, "."], project, env={"GOPROXY": "off"})
        result = f"/work/{name}.out"
        if built["returncode"] != 0:
            out[name] = [{"build": built}]
            continue
        ran = _run(["timeout", "--kill-after=5", str(seconds), f"/work/{name}.bin"], project,
                   env={"GOPROXY": "off", "DAODAN_OUT": result, **env}, out_file=result)
        after = _listing(project)
        answer = {"build": built, "run": ran, "left_in_the_project": sorted(set(after) - set(before)),
                  "changed_in_the_project": sorted(f for f in set(after) & set(before) if after[f] != before[f])}
        if resolve and ran["written"]:
            handlers = [json.loads(l)["handler"] for l in ran["written"].splitlines() if l.startswith("{") and '"route"' in l]
            answer["symbols"] = _symbols(f"/work/{name}.bin", handlers, project)
        out[name] = [answer]
    return out


@app.function(cpu=2, memory=4096, timeout=1800)
def cold_build() -> dict:
    """With the network open, as the preparation has it: `go mod download` and `go build` from empty caches, time and memory."""
    import shutil

    shutil.copytree("/fix", "/work/cold")
    env = {"GOMODCACHE": "/tmp/gomod-cold", "GOCACHE": "/tmp/gocache-cold"}
    return {"cold-build": [{"download": _run(["go", "mod", "download"], "/work/cold", env=env),
                            "build": _run(["go", "build", "-o", "/work/cold.bin", "."], "/work/cold", env=env)}]}


@app.local_entrypoint()
def main():
    wanted = (os.environ.get("VARIANTS") or ",".join(PROBES)).split(",")
    OUT.mkdir(exist_ok=True)
    import zlib

    answers = {**json.loads(zlib.decompress(b"".join(probe.remote_gen(wanted)))), **cold_build.remote()}
    for name, items in answers.items():
        (OUT / f"{'00_env' if name == '_env' else name}.json").write_bytes(
            (json.dumps(items, indent=1, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8"))
        if name == "_env":
            print(json.dumps(items))
            continue
        for answer in items:
            ran = answer.get("run") or {}
            print(f"=== {name}: build exit {answer.get('build', {}).get('returncode')}, run exit {ran.get('returncode')} in {ran.get('seconds')} s, "
                  f"{ran.get('peak_memory_mb')} MB, ports {ran.get('ports_listening')}, wrote {ran.get('written_bytes')} bytes, "
                  f"left {answer.get('left_in_the_project')}")
