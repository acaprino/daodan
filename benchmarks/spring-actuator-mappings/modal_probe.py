"""Spring Boot's Actuator `mappings` on Modal, in a container with the network blocked.

    PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal modal run benchmarks/spring-actuator-mappings/modal_probe.py
    VARIANTS=actuator-boot3,javap ... (a choice of `PROBES`, `PIPELINES` and `EXTRA`)

The image is built with the network open (the one moment it is, as a project's preparation is): each fixture's
`mvn package` (its dependencies and plugins land in `~/.m2`) and the jar unpacked, as the JDK's `jar` does;
`/fix/goffline*` hold only Daodan's own restore (`preparation.RESTORES["maven"]["line"]`, the pinned
`maven-dependency-plugin:3.8.1:go-offline`) in a repository of their own (`/m2-goffline*`), to tell whether that
restore is enough to build offline. Each probe then runs with the network blocked, in a copy: the project's code
(`Launcher.java` loads it) runs only in the container. Every answer (`argv`, `returncode`, `seconds`, peak memory,
the sockets that listened during the run and the process that owned each, the java processes left, the file the
launcher wrote) goes to `results/<probe>.json`.
"""
import json
import os
import pathlib
import sys

import modal

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import harness  # noqa: E402

_run = harness.run
LOCAL = modal.is_local()
FIXTURE = HERE / "fixture"
OUT = HERE / "results"
# fixture name -> (pom folder, overlay folder or None): the overlay's files are copied over the fixture's project
POMS = {"boot3": ("boot3", None), "boot27": ("boot27", None), "plain": ("plain", None),
        "props": ("boot3", "props"), "closed": ("boot3", "closed"), "access": ("boot3", "access"), "jpa": ("boot3", "jpa"),
        "props27": ("boot27", "props"), "closed27": ("boot27", "closed"), "legacyoff": ("boot3", "legacyoff"), "accessoff": ("boot3", "accessoff")}
# the restore Daodan runs (`preparation.RESTORES["maven"]["line"]`), pointed at a repository of its own
GO_OFFLINE = "mvn -B -q org.apache.maven.plugins:maven-dependency-plugin:3.8.1:go-offline"
GOFFLINE = {"goffline": "boot3", "goffline27": "boot27"}  # restored project -> its pom

image = modal.Image.from_registry("maven:3.9-eclipse-temurin-17", add_python="3.12")
if LOCAL:
    image = image.add_local_dir(FIXTURE, "/src", copy=True)

    def _build(name: str, pom: str, overlay: str | None) -> str:
        merged = f" && cp -r /src/overlays/{overlay}/. /fix/{name}/" if overlay else ""
        return (f"mkdir -p /fix/{name} && cp -r /src/src /fix/{name}/src && cp /src/poms/{pom}/pom.xml /fix/{name}/pom.xml{merged}"
                f" && cd /fix/{name} && mvn -B -q -DskipTests package"
                f" && mkdir target/unpacked && cd target/unpacked && jar xf ../demo-0.0.1.jar")

    image = image.run_commands(*(_build(name, pom, overlay) for name, (pom, overlay) in POMS.items()))
    image = image.run_commands(*(
        f"mkdir -p /fix/{name} && cp -r /src/src /fix/{name}/src && cp /src/poms/{pom}/pom.xml /fix/{name}/pom.xml"
        f" && cd /fix/{name} && {GO_OFFLINE} -Dmaven.repo.local=/m2-{name}" for name, pom in GOFFLINE.items()))
    image = image.add_local_file(HERE / "Launcher.java", "/launcher/Launcher.java").add_local_file(HERE / "harness.py", "/root/harness.py")
app = modal.App("spring-actuator-mappings", image=image)

PORT = ["server.port=-1"]
JPA = ["spring.datasource.url=jdbc:postgresql://db.invalid:5432/app", "spring.datasource.username=u", "spring.datasource.password=p"]
BASE = [*PORT, "management.endpoints.web.exposure.include=mappings", "spring.main.banner-mode=off"]
COMMON = [*BASE, "management.server.port=-1"]
LEGACY = ["management.endpoint.mappings.enabled=true"]  # Spring Boot 2.2 to 3.3 (deprecated from 3.4)
MODERN = ["management.endpoints.access.max-permitted=unrestricted", "management.endpoint.mappings.access=unrestricted"]  # 3.4 and later
FULL = [*COMMON, *LEGACY, *MODERN]
PROBES = {  # probe -> (fixture, mode, stop, how, properties, seconds the launcher has)
    "actuator-boot3": ("boot3", "actuator", "started", "args", BASE, 120),
    "actuator-boot3-returned": ("boot3", "actuator", "returned", "args", BASE, 120),
    "actuator-boot27": ("boot27", "actuator", "started", "args", BASE, 120),
    "no-actuator": ("plain", "actuator", "started", "args", BASE, 120),  # no bean of the endpoint: what does the launcher say
    "handler-methods-boot3": ("boot3", "handler-methods", "started", "args", BASE, 120),
    "handler-methods-boot27": ("boot27", "handler-methods", "started", "args", BASE, 120),
    "handler-methods-plain": ("plain", "handler-methods", "started", "args", BASE, 120),  # spring-webmvc alone, no Actuator
    "port-control": ("boot3", "actuator", "started", "args", ["server.port=0", *BASE[1:]], 120),  # a connector on a random port
    # the project's own application.properties sets server.port=8080, management.server.port=9001 and an exposure of `health`
    "props-defaults": ("props", "actuator", "started", "defaults", BASE, 60),  # setDefaultProperties: the lowest precedence
    "props-args": ("props", "actuator", "started", "args", BASE, 60),
    "props-args-management-off": ("props", "actuator", "started", "args", [*BASE, "management.server.port=-1"], 60),
    # the project's own application.properties turns every endpoint off by default
    "closed-args": ("closed", "actuator", "started", "args", BASE, 60),
    "closed-args-enabled": ("closed", "actuator", "started", "args", [*BASE, "management.endpoint.mappings.enabled=true"], 60),
    # the project's own application.properties caps every endpoint's access at none (Spring Boot 3.4 and later)
    "access-args": ("access", "actuator", "started", "args", BASE, 60),
    "access-args-unrestricted": ("access", "actuator", "started", "args", [*BASE, "management.endpoints.access.max-permitted=unrestricted",
                                                                          "management.endpoint.mappings.access=unrestricted"], 60),
    "loopback": ("boot3", "actuator", "started", "args", [*BASE, "server.address=127.0.0.1"], 120),
    # the JVM stays alive (a runner that never returns, the launcher stops after run()): is anything served on the socket?
    "poke-minus1": ("boot3", "actuator", "returned", "args", [*BASE, "probe.block=true"], 8),  # a run whose name starts with `poke-` is poked
    "poke-port0": ("boot3", "actuator", "returned", "args", ["server.port=0", *BASE[1:], "probe.block=true"], 8),
    # the whole set at once, over a project that sets nothing, one that moves the ports, one that turns the endpoints off
    "full-boot3": ("boot3", "actuator", "started", "args", FULL, 60),
    "full-boot27": ("boot27", "actuator", "started", "args", FULL, 60),
    "full-props": ("props", "actuator", "started", "args", FULL, 60),
    "full-props27": ("props27", "actuator", "started", "args", FULL, 60),
    "full-closed": ("closed", "actuator", "started", "args", FULL, 60),
    "full-closed27": ("closed27", "actuator", "started", "args", FULL, 60),
    "full-access": ("access", "actuator", "started", "args", FULL, 60),
    # one set at a time: Spring Boot 3.4 and later reject `enabled` and `access` of one endpoint set together
    "modern-boot3": ("boot3", "actuator", "started", "args", [*COMMON, *MODERN], 60),
    "modern-props": ("props", "actuator", "started", "args", [*COMMON, *MODERN], 60),
    "modern-access": ("access", "actuator", "started", "args", [*COMMON, *MODERN], 60),
    "legacy-boot27": ("boot27", "actuator", "started", "args", [*COMMON, *LEGACY], 60),
    "legacy-props27": ("props27", "actuator", "started", "args", [*COMMON, *LEGACY], 60),
    "legacy-closed27": ("closed27", "actuator", "started", "args", [*COMMON, *LEGACY], 60),
    # a project that sets the endpoint's own `enabled` (or `access`) and the launcher the other one
    "legacy-legacyoff": ("legacyoff", "actuator", "started", "args", [*COMMON, *LEGACY], 60),
    "modern-legacyoff": ("legacyoff", "actuator", "started", "args", [*COMMON, *MODERN], 60),
    "modern-accessoff": ("accessoff", "actuator", "started", "args", [*COMMON, *MODERN], 60),
    "legacy-accessoff": ("accessoff", "actuator", "started", "args", [*COMMON, *LEGACY], 60),
    # the other family's property given an empty value, to clear the project's: does Spring Boot still call it set
    "blank-legacyoff": ("legacyoff", "actuator", "started", "args", [*COMMON, *MODERN, "management.endpoint.mappings.enabled="], 60),
    "blank-accessoff": ("accessoff", "actuator", "started", "args", [*COMMON, *LEGACY, "management.endpoint.mappings.access="], 60),
    "legacy-access": ("access", "actuator", "started", "args", [*COMMON, *LEGACY], 60),  # does `enabled` alone beat max-permitted=none
    "modern-closed": ("closed", "actuator", "started", "args", [*COMMON, *MODERN], 60),  # does `access` alone beat enabled-by-default=false
    "needs-database": ("boot3", "actuator", "started", "args", [*BASE, "probe.db=true"], 120),
    "needs-database-lazy": ("boot3", "actuator", "started", "args", [*BASE, "probe.db=true", "spring.main.lazy-initialization=true"], 120),
    # a project with Spring Data JPA and a PostgreSQL driver, the database named in the properties and not there
    "jpa-eager": ("jpa", "actuator", "started", "args", [*BASE, *JPA], 120),
    "jpa-lazy": ("jpa", "actuator", "started", "args", [*BASE, *JPA, "spring.main.lazy-initialization=true"], 120),
    "jpa-no-open-in-view": ("jpa", "actuator", "started", "args", [*BASE, *JPA, "spring.jpa.open-in-view=false"], 120),
    "jpa-lazy-no-open-in-view": ("jpa", "actuator", "started", "args",
                                 [*BASE, *JPA, "spring.main.lazy-initialization=true", "spring.jpa.open-in-view=false"], 120),
    # the context taken at ApplicationPreparedEvent, up to `refreshForAotProcessing`, and only the handler mapping created
    "aot-boot3": ("boot3", "handler-methods", "aot", "args", BASE, 60),
    "aot-boot27": ("boot27", "handler-methods", "aot", "args", BASE, 60),  # Spring Framework 5.3 has no such method
    "aot-needs-database": ("boot3", "handler-methods", "aot", "args", [*BASE, "probe.db=true"], 60),
    "aot-jpa": ("jpa", "handler-methods", "aot", "args", [*BASE, *JPA], 60),
    "aot-jpa-no-open-in-view": ("jpa", "handler-methods", "aot", "args", [*BASE, *JPA, "spring.jpa.open-in-view=false"], 60),
    "aot-never-builds": ("boot3", "handler-methods", "aot", "args", [*BASE, "probe.refresh=true"], 30),
    "never-ends-started": ("boot3", "actuator", "started", "args", [*BASE, "probe.block=true"], 20),  # a runner: not reached
    "never-ends-returned": ("boot3", "actuator", "returned", "args", [*BASE, "probe.block=true"], 20),  # run() never returns
    "never-builds": ("boot3", "actuator", "started", "args", [*BASE, "probe.refresh=true"], 20),  # the context never finishes
    "never-closes": ("boot3", "actuator", "started", "args", [*BASE, "probe.hang=true"], 15),  # the shutdown hook hangs
}
PIPELINES = ("pipeline-m2", "pipeline-m2-keep-target", "pipeline-goffline", "pipeline-goffline27", "pipeline-compile")
EXTRA = ("javap", "repeat-boot3", "repeat-boot3-quiet", "memory-256", "memory-128", "poke-repeat", "clean-package-m2", "clean-package-goffline")


def _copy(fixture: str, name: str, drop: str | None = None) -> str:
    import shutil

    shutil.copytree(f"/fix/{fixture}", f"/work/{name}", symlinks=True)
    if drop:
        shutil.rmtree(f"/work/{name}/{drop}", ignore_errors=True)
    return f"/work/{name}"


def _main_class(project: str) -> str:
    for line in open(f"{project}/target/unpacked/META-INF/MANIFEST.MF"):
        if line.startswith("Start-Class:"):
            return line.split(":", 1)[1].strip()
    raise ValueError("no Start-Class in the manifest")


def _launch(project: str, name: str, mode: str, stop: str, how: str, properties: list[str], seconds: int, classpath: str,
            main: str, heap: str = "-Xmx1g", watch_sockets: bool = True) -> dict:
    result = f"/work/{name}.json"
    return _run(["timeout", "--kill-after=10", str(seconds), "java", heap, "-cp", classpath, "/launcher/Launcher.java",
                 main, result, mode, stop, how, *properties], project, out_file=result, poke=name.startswith("poke-"), watch_sockets=watch_sockets)


def _unpacked(project: str) -> str:
    return f"{project}/target/unpacked/BOOT-INF/classes:{project}/target/unpacked/BOOT-INF/lib/*"


def _steps(project: str, name: str, repository: str | None) -> list[dict]:
    """The pipeline offline: the build, the jar unpacked, the launcher on the unpacked jar (`Start-Class`)."""
    flags = [f"-Dmaven.repo.local={repository}"] if repository else []
    steps = [_run(["mvn", "-o", "-B", "-q", "-DskipTests", *flags, "package"], project)]
    if steps[0]["returncode"] == 0:
        os.makedirs(f"{project}/target/unpacked", exist_ok=True)
        steps.append(_run(["jar", "xf", "../demo-0.0.1.jar"], f"{project}/target/unpacked"))
        steps.append(_launch(project, name, "actuator", "started", "args", BASE, 120, _unpacked(project), _main_class(project)))
    return steps


@app.function(cpu=2, memory=4096, timeout=3000, block_network=True)
def probe(names: list[str]) -> dict:
    import subprocess
    import traceback

    def version(*argv):
        run = subprocess.run(argv, capture_output=True, text=True)
        return (run.stderr.strip().splitlines() or run.stdout.strip().splitlines() or [""])[0]

    def size(path):
        return subprocess.run(["du", "-sk", path], capture_output=True, text=True).stdout.split()[0]

    libs = {name: sorted(f for f in os.listdir(f"/fix/{name}/target/unpacked/BOOT-INF/lib") if f.startswith(("spring-boot-", "spring-webmvc-")))
            for name in ("boot3", "boot27")}
    out = {"_env": {"java": version("java", "-version"), "mvn": version("mvn", "-version"), "libs": libs,
                    "m2_kb": size("/root/.m2"), "goffline_kb": size("/m2-goffline"), "goffline27_kb": size("/m2-goffline27")}}
    for name in names:
        try:
            if name in PROBES:
                fixture, mode, stop, how, properties, seconds = PROBES[name]
                project = _copy(fixture, name)
                out[name] = [_launch(project, name, mode, stop, how, properties, seconds, _unpacked(project), _main_class(project))]
            elif name == "repeat-boot3":  # the same run five times: does a socket come and go, and how much does the time vary
                out[name] = []
                for n in range(5):
                    project = _copy("boot3", f"{name}-{n}")
                    out[name].append(_launch(project, f"{name}-{n}", "actuator", "started", "args", BASE, 120, _unpacked(project), _main_class(project)))
            elif name == "repeat-boot3-quiet":  # the same, with no thread polling /proc: the time and the memory alone
                out[name] = []
                for n in range(5):
                    project = _copy("boot3", f"{name}-{n}")
                    out[name].append(_launch(project, f"{name}-{n}", "actuator", "started", "args", BASE, 120, _unpacked(project),
                                             _main_class(project), watch_sockets=False))
            elif name in ("memory-256", "memory-128"):  # the smallest heap that still loads the fixture
                project = _copy("boot3", name)
                out[name] = [_launch(project, name, "actuator", "started", "args", BASE, 120, _unpacked(project), _main_class(project),
                                     heap="-Xmx" + name.split("-")[1] + "m")]
            elif name == "poke-repeat":  # the instant of the connection varies: five runs of the `server.port=-1` one
                out[name] = []
                for n in range(5):
                    project = _copy("boot3", f"poke-repeat-{n}")
                    out[name].append(_launch(project, f"poke-repeat-{n}", "actuator", "returned", "args", [*BASE, "probe.block=true"], 8,
                                             _unpacked(project), _main_class(project)))
            elif name in ("clean-package-m2", "clean-package-goffline"):  # `clean` is a plugin of its own: is it in each repository
                fixture, flags = ("boot3", []) if name.endswith("m2") else ("goffline", ["-Dmaven.repo.local=/m2-goffline"])
                project = _copy(fixture, name)
                out[name] = [_run(["mvn", "-o", "-B", "-q", "-DskipTests", *flags, "clean", "package"], project)]
            elif name == "javap":  # the JDK's own tool: the file and the lines of a class that Actuator does not give
                project = _copy("boot3", name)
                classes = f"{project}/target/unpacked/BOOT-INF/classes"
                names_ = sorted(os.path.relpath(os.path.join(folder, f), classes)[:-6].replace("/", ".")
                                for folder, _, files in os.walk(classes) for f in files if f.endswith(".class"))
                out[name] = [_run(["javap", "-l", "-p", "-s", "-cp", classes, *names_], project, keep=400000)]
            elif name == "pipeline-m2":  # the packages of the image build in the default repository, `target/` removed
                project = _copy("boot3", name, drop="target")
                out[name] = _steps(project, name, None)
            elif name == "pipeline-m2-keep-target":  # the preparation's `target/` is still there when the build runs again
                project = _copy("boot3", name)
                out[name] = _steps(project, name, None)
            elif name in ("pipeline-goffline", "pipeline-goffline27"):  # only Daodan's restore in the repository
                project = _copy(name.replace("pipeline-", ""), name)
                out[name] = _steps(project, name, "/m2-" + name.replace("pipeline-", ""))
            elif name == "pipeline-compile":  # no jar: compile, the classpath from the dependency plugin, the main class given
                project = _copy("goffline", name)
                cp = f"{project}/cp.txt"
                steps = [_run(["mvn", "-o", "-B", "-q", "-DskipTests", "-Dmaven.repo.local=/m2-goffline", "compile",
                               "org.apache.maven.plugins:maven-dependency-plugin:3.8.1:build-classpath", f"-Dmdep.outputFile={cp}"], project)]
                if steps[0]["returncode"] == 0:
                    steps.append(_launch(project, name, "actuator", "started", "args", BASE, 120,
                                         f"{project}/target/classes:{open(cp).read().strip()}", "demo.DemoApplication"))
                out[name] = steps
        except Exception:
            out[name] = [{"harness_error": traceback.format_exc()[-2000:]}]
    return out


@app.function(cpu=2, memory=4096, timeout=1800)
def cold_build() -> dict:
    """With the network open, as the preparation has it: the restore and the build from an empty repository, time and memory."""
    import subprocess

    project = _copy("goffline", "cold")
    repository = "/tmp/m2-cold"
    steps = [_run(GO_OFFLINE.split() + [f"-Dmaven.repo.local={repository}"], project),
             _run(["mvn", "-o", "-B", "-q", "-DskipTests", f"-Dmaven.repo.local={repository}", "package"], project)]
    steps[-1]["m2_kb"] = subprocess.run(["du", "-sk", repository], capture_output=True, text=True).stdout.split()[0]
    return {"cold-build": steps}


@app.local_entrypoint()
def main():
    wanted = (os.environ.get("VARIANTS") or ",".join([*PROBES, *PIPELINES, *EXTRA])).split(",")
    OUT.mkdir(exist_ok=True)
    answers = {**probe.remote(wanted), **({} if os.environ.get("VARIANTS") else cold_build.remote())}
    for name, items in answers.items():
        (OUT / f"{'00_env' if name == '_env' else name}.json").write_bytes(
            (json.dumps(items, indent=1, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8"))
        if name == "_env":
            print(json.dumps(items)[:600])
            continue
        for answer in items:
            if "harness_error" in answer:
                print(f"=== {name}: HARNESS ERROR {answer['harness_error'][-300:]}")
                continue
            print(f"=== {name}: exit {answer['returncode']} in {answer['seconds']} s, {answer['peak_memory_mb']} MB, "
                  f"listeners {[(l['port'], l.get('gone_s'), l.get('poke')) for l in answer['listeners']]}, java left {len(answer['java_left'])}, "
                  f"wrote {answer['written_bytes']} bytes")
            if answer["returncode"] not in (0,):
                print("--- tail:", (answer["stderr"].strip() or answer["stdout"].strip())[-300:])
    if "javap" in answers:
        (OUT / "javap.txt").write_bytes(answers["javap"][0]["stdout"].encode("utf-8"))
