"""Spring Boot's Actuator `mappings` on Modal, in a container with the network blocked. NOT RUN YET (24 November 2026: no Modal credentials in
the session that wrote it).

    PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal python -m modal run benchmarks/spring-actuator-mappings/modal_probe.py
    VARIANTS=actuator-boot3,no-actuator ... (a choice of `PROBES`)

The image is built with the network open (the one moment it is): each fixture's `mvn package` (its dependencies and plugins land in
`~/.m2`) and the jar unpacked, as the JDK's `jar` does; `/fix/goffline` has only `dependency:go-offline` in its own repository
(`/m2-goffline`), to tell whether Daodan's restore (`preparation.RESTORES["maven"]`) is enough to build offline. Each probe then runs with
the network blocked, in a copy: the project's code (`Launcher.java` loads it) runs only in the container. Every answer (`argv`,
`returncode`, `seconds`, peak memory, the ports that listened during the run, the processes left, the file the launcher wrote) goes to
`results/<probe>.json`.
"""
import json
import os
import pathlib

import modal

HERE = pathlib.Path(__file__).resolve().parent
LOCAL = modal.is_local()
FIXTURE = HERE / "fixture"
OUT = HERE / "results"
POMS = ("boot3", "boot27", "plain")  # Boot 3.5.0 with Actuator, Boot 2.7.18 with Actuator, Boot 3.5.0 without
LIBS = "BOOT-INF/classes:BOOT-INF/lib/*"

image = modal.Image.from_registry("maven:3.9-eclipse-temurin-17", add_python="3.12")
if LOCAL:
    image = image.add_local_dir(FIXTURE, "/src", copy=True)
    image = image.run_commands(*(
        f"mkdir -p /fix/{name} && cp -r /src/src /fix/{name}/src && cp /src/poms/{name}/pom.xml /fix/{name}/pom.xml"
        f" && cd /fix/{name} && mvn -B -q -DskipTests package 2>&1 | tail -5"
        f" && mkdir target/unpacked && cd target/unpacked && jar xf ../demo-0.0.1.jar" for name in POMS))
    image = image.run_commands(
        "mkdir -p /fix/goffline && cp -r /src/src /fix/goffline/src && cp /src/poms/boot3/pom.xml /fix/goffline/pom.xml"
        " && cd /fix/goffline && mvn -B -q -Dmaven.repo.local=/m2-goffline dependency:go-offline 2>&1 | tail -5")
    image = image.add_local_file(HERE / "Launcher.java", "/launcher/Launcher.java")
app = modal.App("spring-actuator-mappings", image=image)

PROBES = {  # probe -> (fixture, mode, extra properties, seconds the launcher has)
    "actuator-boot3": ("boot3", "actuator", [], 120),
    "actuator-boot27": ("boot27", "actuator", [], 120),
    "no-actuator": ("plain", "actuator", [], 120),  # no bean of the endpoint: what does the launcher say
    "handler-methods-boot3": ("boot3", "handler-methods", [], 120),
    "handler-methods-plain": ("plain", "handler-methods", [], 120),  # spring-webmvc alone, no Actuator
    "port-control": ("boot3", "actuator", ["server.port=0"], 120),  # a connector on a random port: the watcher must see it
    "needs-database": ("boot3", "actuator", ["probe.db=true"], 120),
    "needs-database-lazy": ("boot3", "actuator", ["probe.db=true", "spring.main.lazy-initialization=true"], 120),
    "never-ends": ("boot3", "actuator", ["probe.block=true"], 20),  # the limit ends it: exit 124 or 137, nothing left
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


def _run(argv: list[str], cwd: str, env: dict | None = None, out_file: str | None = None) -> dict:
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
    with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
        watcher.start()
        process = subprocess.Popen(argv, cwd=cwd, stdout=stdout, stderr=stderr, env={**os.environ, "NO_COLOR": "1", **(env or {})})
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
            "processes_left": [l.strip() for l in left.splitlines() if "java" in l or "mvn" in l],
            "stdout": out[-3000:], "stderr": err[-3000:], "written": written[:200000] if written else None,
            "written_bytes": len(written) if written else 0}


def _copy(fixture: str, name: str) -> str:
    import shutil

    shutil.copytree(f"/fix/{fixture}", f"/work/{name}", symlinks=True)
    return f"/work/{name}"


def _main_class(project: str) -> str:
    for line in open(f"{project}/target/unpacked/META-INF/MANIFEST.MF"):
        if line.startswith("Start-Class:"):
            return line.split(":", 1)[1].strip()
    raise ValueError("no Start-Class in the manifest")


@app.function(cpu=2, memory=4096, timeout=1800, block_network=True)
def probe(names: list[str]) -> dict:
    import subprocess

    def version(*argv):
        return subprocess.run(argv, capture_output=True, text=True).stderr.strip().splitlines()[:1] or \
            subprocess.run(argv, capture_output=True, text=True).stdout.strip().splitlines()[:1]

    out = {"_env": {"java": version("java", "-version"), "mvn": version("mvn", "-version")}}
    for name in names:
        if name in PROBES:
            fixture, mode, properties, seconds = PROBES[name]
            project = _copy(fixture, name)
            result = f"/work/{name}.json"
            out[name] = [_run(["timeout", "--kill-after=10", str(seconds), "java", "-Xmx1g",
                               "-cp", f"{project}/target/unpacked/BOOT-INF/classes:{project}/target/unpacked/BOOT-INF/lib/*",
                               "/launcher/Launcher.java", _main_class(project), result, mode, *properties], project, out_file=result)]
        elif name == "javap":  # the JDK's own tool: the file and the lines of a class that Actuator does not give
            project = _copy("boot3", name)
            out[name] = [_run(["javap", "-l", "-p", "-cp", f"{project}/target/unpacked/BOOT-INF/classes",
                               "demo.ItemController", "demo.PageController", "demo.PageController$Ping"], project)]
        elif name == "offline-package":  # the packages of the image build, no restore of its own
            project = _copy("boot3", name)
            out[name] = [_run(["mvn", "-o", "-B", "-q", "-DskipTests", "clean", "package"], project)]
        elif name == "goffline-package":  # only Daodan's restore (`dependency:go-offline`): does the build still work offline
            project = _copy("goffline", name)
            out[name] = [_run(["mvn", "-o", "-B", "-q", "-DskipTests", "-Dmaven.repo.local=/m2-goffline", "package"], project)]
    return out


@app.function(cpu=2, memory=4096, timeout=1800)
def cold_build() -> dict:
    """With the network open, as the preparation has it: `mvn package` from an empty repository, time and memory."""
    project = _copy("boot3", "cold")
    return {"cold-build": [_run(["mvn", "-B", "-q", "-DskipTests", "-Dmaven.repo.local=/tmp/m2-cold", "clean", "package"], project)]}


@app.local_entrypoint()
def main():
    wanted = (os.environ.get("VARIANTS") or ",".join([*PROBES, "javap", "offline-package", "goffline-package"])).split(",")
    OUT.mkdir(exist_ok=True)
    answers = {**probe.remote(wanted), **cold_build.remote()}
    for name, items in answers.items():
        (OUT / f"{'00_env' if name == '_env' else name}.json").write_bytes(
            (json.dumps(items, indent=1, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8"))
        if name == "_env":
            print(json.dumps(items))
            continue
        for answer in items:
            print(f"=== {name}: exit {answer['returncode']} in {answer['seconds']} s, {answer['peak_memory_mb']} MB, "
                  f"ports {answer['ports_listening']}, left {answer['processes_left']}, wrote {answer['written_bytes']} bytes")
            if answer["returncode"] != 0:
                print("--- stderr:", answer["stderr"].strip()[-400:])
