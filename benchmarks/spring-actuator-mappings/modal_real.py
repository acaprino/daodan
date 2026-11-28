"""The launcher of this folder on real public Spring Boot applications, on Modal.

    PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal modal run benchmarks/spring-actuator-mappings/modal_real.py
    VARIANTS=petclinic,ruoyi ...   (a choice of `APPS`)

Each application is fetched at a pinned commit (`https://codeload.github.com/<repo>/tar.gz/<sha>`) while the image is built, with
the network open, and so are Maven's dependencies, with Daodan's own restore line (`preparation.RESTORES["maven"]["line"]`, in a
repository of the application's own) and the Noir that `entry_points/noir.py` pins (sha256 checked). Nothing of the applications is
kept in the repository: the answers are. Then, with the network blocked and in a copy of the project: Noir over the sources, `mvn -o
-DskipTests package`, each repackaged jar (the ones whose manifest has `Start-Class`) unpacked, the launcher on each (Actuator's
`mappings` first, the handler methods when the bean is absent, then the variants that try to reach the mappings without the services
the application needs), `javap -l -p -s` over the handler classes (those of the module and those of the reactor's other
modules that its jar carries), and the files the run left in the copy. `cold` is the same restore and build with the network open,
from an empty repository: time, memory, and whether the project builds at all. `real_summary.py` reads the answers with the
sources (fetched on the host as text, never run) and writes `results/real/<name>-summary.json`.
"""
import json
import os
import pathlib
import sys

import modal

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import harness  # noqa: E402

LOCAL = modal.is_local()
OUT = HERE / "results" / "real"
# name -> (repository, commit, licence): the commit pins what runs; the licence is GitHub's SPDX id, checked against the LICENSE file
APPS = {
    "petclinic": ("spring-projects/spring-petclinic", "500158f732419217507c7656904b8e6aa1bcc0d6", "Apache-2.0"),
    "ruoyi": ("yangzongzhuan/RuoYi", "d6708994364bfbb472c96380d6129e24303b3228", "MIT"),
    "microservices": ("spring-petclinic/spring-petclinic-microservices", "935ba9320a6514a6c31ff1316c29281b2191dcd3", "Apache-2.0"),
}
NOIR = ("https://github.com/owasp-noir/noir/releases/download/v1.5.0/noir-v1.5.0-linux-x86_64",  # entry_points/noir.py DOWNLOAD
        "4e176c92ee16f60fafd3be7ea6f605d82d3f27c39704a3f875cbed5bd050dc70")
GO_OFFLINE = "mvn -B -q org.apache.maven.plugins:maven-dependency-plugin:3.8.1:go-offline"  # preparation.RESTORES["maven"]["line"]
BASE = ["server.port=-1", "management.server.port=-1", "management.endpoints.web.exposure.include=mappings", "spring.main.banner-mode=off"]
LEGACY = ["management.endpoint.mappings.enabled=true"]  # Spring Boot up to 3.3
MODERN = ["management.endpoints.access.max-permitted=unrestricted", "management.endpoint.mappings.access=unrestricted",
          "management.endpoint.mappings.enabled="]  # 3.4 and later; the empty value clears the project's own `enabled`
LAZY = ["spring.main.lazy-initialization=true"]
# Spring's own property, with the names of the auto-configurations of the stores the failing project uses (Spring Boot 3 and 4 packages)
EXCLUDE = ["spring.autoconfigure.exclude=" + ",".join((
    "org.springframework.boot.autoconfigure.jdbc.DataSourceAutoConfiguration", "org.springframework.boot.jdbc.autoconfigure.DataSourceAutoConfiguration",
    "org.mybatis.spring.boot.autoconfigure.MybatisAutoConfiguration", "com.github.pagehelper.autoconfigure.PageHelperAutoConfiguration",
    "org.springframework.boot.autoconfigure.quartz.QuartzAutoConfiguration", "org.springframework.boot.quartz.autoconfigure.QuartzAutoConfiguration",
    "org.springframework.boot.autoconfigure.data.redis.RedisAutoConfiguration", "org.springframework.boot.data.redis.autoconfigure.DataRedisAutoConfiguration"))]

image = modal.Image.from_registry("maven:3.9-eclipse-temurin-17", add_python="3.12")
if LOCAL:
    image = image.run_commands(
        f"curl -fsSL -o /usr/local/bin/noir {NOIR[0]} && echo '{NOIR[1]}  /usr/local/bin/noir' | sha256sum -c - && chmod +x /usr/local/bin/noir")
    for name, (repository, commit, _) in APPS.items():
        image = image.run_commands(f"mkdir -p /apps/{name} /state && curl -fsSL https://codeload.github.com/{repository}/tar.gz/{commit}"
                                   f" | tar xz -C /apps/{name} --strip-components=1")
    for name in APPS:  # the restore may fail: its code and log are kept, and the image is built anyway
        image = image.run_commands(f"cd /apps/{name} && ({GO_OFFLINE} -Dmaven.repo.local=/m2/{name} > /state/{name}.restore.log 2>&1;"
                                   f" echo $? > /state/{name}.restore.rc); true")
    for name in APPS:  # the other restore: the build itself, with the network open (what `dynamic/jvm.py`'s preparation does)
        image = image.run_commands(f"mkdir -p /built && cp -r /apps/{name} /built/{name} && cd /built/{name} && (mvn -B -q -DskipTests"
                                   f" -Dmaven.repo.local=/m2b/{name} package > /state/{name}.built.log 2>&1; echo $? > /state/{name}.built.rc); true")
    image = image.run_commands("apt-get update -qq && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq --no-install-recommends mariadb-server > /dev/null && rm -rf /var/lib/apt/lists/*")  # RuoYi's stand-in service
    image = image.add_local_dir(HERE / "fixture" / "src", "/fixture-src", copy=True)  # the fixture of the other probe, for Noir
    image = image.add_local_file(HERE / "Launcher.java", "/launcher/Launcher.java").add_local_file(HERE / "harness.py", "/root/harness.py")
app = modal.App("spring-real-applications", image=image)


def _listing(root: str) -> dict[str, int]:
    found = {}
    for folder, _, files in os.walk(root):
        for file in files:
            path = os.path.join(folder, file)
            try:
                found[os.path.relpath(path, root)] = os.path.getsize(path)
            except OSError:
                pass
    return found


def _properties(version: str, extra: list[str] = ()) -> list[str]:
    major, minor = (int(part) for part in version.split(".")[:2])
    chosen = {}  # a later value of a key replaces the earlier: Spring Boot would join two `--key=` arguments
    for item in [*BASE, *(MODERN if (major, minor) >= (3, 4) else LEGACY), *extra]:
        key, _, value = item.partition("=")
        chosen[key] = value
    return [f"{key}={value}" for key, value in chosen.items()]


def _start_class_jars(project: str) -> tuple[list[dict], list[str]]:
    """The repackaged jars of the build (a manifest with `Start-Class`) and the names of every jar the reactor made."""
    import zipfile

    jars, names = [], []
    for folder, _, files in os.walk(project):
        if os.path.basename(folder) != "target":
            continue
        for file in files:
            if file.endswith(".jar") and not file.endswith("-sources.jar"):
                path = os.path.join(folder, file)
                names.append(file)
                try:
                    manifest = zipfile.ZipFile(path).read("META-INF/MANIFEST.MF").decode("utf-8", "replace")
                except (OSError, KeyError, zipfile.BadZipFile):
                    continue
                unfolded = manifest.replace(chr(13) + chr(10), chr(10)).replace(chr(10) + " ", "")  # a manifest line wraps at 72 bytes, the next starts with a space
                attributes = dict(line.split(": ", 1) for line in unfolded.splitlines() if ": " in line)
                if "Start-Class" in attributes:
                    module = os.path.relpath(os.path.dirname(folder), project)
                    jars.append({"jar": path, "module": "" if module == "." else module, "start_class": attributes["Start-Class"],
                                 "boot_version": attributes.get("Spring-Boot-Version", ""), "jdk": attributes.get("Build-Jdk-Spec", "")})
    return sorted(jars, key=lambda item: item["jar"]), names


def _routes(written: str | None) -> list[dict]:
    """What a launcher answer says of each route, trimmed: Actuator's rows (servlet or reactive) or the handler methods."""
    if not written or written.startswith('{"error"'):
        return []
    data = json.loads(written)
    rows = []
    if isinstance(data, list):
        for item in data:
            rows.append({"methods": item["methods"], "patterns": item["patterns"], "class": item["declaringClass"].replace("$", "."),
                         "name": item["name"], "descriptor": item["descriptor"]})
        return rows
    for context in data.get("contexts", {}).values():
        for kind in ("dispatcherServlets", "dispatcherHandlers"):
            for rows_of in (context["mappings"].get(kind) or {}).values():
                for entry in rows_of:
                    details = entry.get("details") or {}
                    handler, conditions = details.get("handlerMethod"), details.get("requestMappingConditions")
                    if handler and conditions:
                        rows.append({"methods": conditions["methods"], "patterns": conditions["patterns"], "class": handler["className"],
                                     "name": handler["name"], "descriptor": handler["descriptor"]})
                    else:
                        function = details.get("handlerFunction") or {}
                        rows.append({"predicate": entry["predicate"], "handler": entry["handler"][:100], "function": function.get("className")})
    return rows


def _class_index(unpacked: str, module_jars: list[str]) -> dict[str, tuple[str, str]]:
    """Canonical class name -> (binary name, where it lies: a folder or a jar), for the module's own classes and those of the
    jars the reactor made that the module carries."""
    import zipfile

    index = {}
    classes = os.path.join(unpacked, "BOOT-INF", "classes")
    for folder, _, files in os.walk(classes):
        for file in files:
            if file.endswith(".class"):
                binary = os.path.relpath(os.path.join(folder, file), classes)[:-6].replace(os.sep, ".")
                index[binary.replace("$", ".")] = (binary, classes)
    lib = os.path.join(unpacked, "BOOT-INF", "lib")
    for jar in sorted(os.listdir(lib)) if os.path.isdir(lib) else []:
        if jar in module_jars:
            for entry in zipfile.ZipFile(os.path.join(lib, jar)).namelist():
                if entry.endswith(".class") and not entry.startswith("META-INF/"):
                    binary = entry[:-6].replace("/", ".")
                    index.setdefault(binary.replace("$", "."), (binary, os.path.join(lib, jar)))
    return index


def _launch(project: str, unpacked: str, item: dict, label: str, mode: str, stop: str, extra: list[str], seconds: int) -> dict:
    result = f"/work/{label}-{abs(hash(item['jar'])) % 10**8}.json"
    classpath = f"{unpacked}/BOOT-INF/classes:{unpacked}/BOOT-INF/lib/*"
    answer = harness.run(["timeout", "--kill-after=10", str(seconds), "java", "-Xmx1g", "-cp", classpath, "/launcher/Launcher.java",
                          item["start_class"], result, mode, stop, "args", *_properties(item["boot_version"] or "3.5", extra)],
                         project, out_file=result, keep=6000)
    answer["label"], answer["routes"] = label, _routes(answer.get("written"))
    answer["error"] = answer["written"][:1500] if (answer.get("written") or "").startswith('{"error"') else None
    answer["written"] = None  # the trimmed routes are the record
    return answer


def _with_mariadb(project: str, unpacked: str, item: dict) -> list[dict]:
    """RuoYi wants MySQL at `localhost:3306` (a Druid pool built as its bean is): MariaDB, installed while the image was built, started
    here with no grant tables, its two SQL files loaded, the JDBC URL given without SSL. The ground truth for the routes of a project
    that does not load without its service."""
    import socket
    import subprocess
    import time

    os.makedirs("/run/mysqld", exist_ok=True)
    subprocess.run(["chown", "mysql:mysql", "/run/mysqld"])
    if not os.path.isdir("/var/lib/mysql/mysql"):
        subprocess.run(["mysql_install_db", "--user=mysql", "--datadir=/var/lib/mysql"], capture_output=True)
    server = subprocess.Popen(["mysqld_safe", "--user=mysql", "--skip-grant-tables", "--bind-address=127.0.0.1"],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    up = False
    for _ in range(120):
        try:
            socket.create_connection(("127.0.0.1", 3306), timeout=1).close()
            up = True
            break
        except OSError:
            time.sleep(0.5)
    setup = []
    if up:
        sql = os.path.join(project, "sql")
        setup.append(harness.run(["mysql", "-uroot", "-e", "CREATE DATABASE ry CHARACTER SET utf8mb4"], project, keep=500))
        for file in sorted(os.listdir(sql)):
            if file.endswith(".sql"):
                setup.append(harness.run(["sh", "-c", f"mysql -uroot ry < {os.path.join(sql, file)}"], project, keep=1500))
    url = ["spring.datasource.druid.master.url=jdbc:mysql://127.0.0.1:3306/ry?useUnicode=true&characterEncoding=utf8&useSSL=false&allowPublicKeyRetrieval=true"]
    runs = [{"label": "mariadb-setup", "returncode": 0 if up and all(step["returncode"] == 0 for step in setup) else 1, "seconds": 0, "peak_memory_mb": 0,
             "listeners": [], "routes": [], "error": None if up else "mariadb did not come up", "setup": [{k: step[k] for k in ("argv", "returncode", "seconds", "stderr")} for step in setup]}]
    if up:
        runs.append(_launch(project, unpacked, item, "service-actuator", "actuator", "started", url, 120))
        runs.append(_launch(project, unpacked, item, "service-aot", "handler-methods", "aot", url, 120))
        runs.append(_launch(project, unpacked, item, "service-handler-methods", "handler-methods", "started", url, 120))
    subprocess.run(["mysqladmin", "-uroot", "shutdown"], capture_output=True)
    server.terminate()
    return runs


@app.function(cpu=2, memory=4096, timeout=3000, block_network=True)
def real(name: str) -> dict:
    import shutil
    import subprocess
    import traceback

    out = {"kind": "real", "name": name, "repository": APPS[name][0], "commit": APPS[name][1], "licence": APPS[name][2]}
    try:
        out["restore_rc"] = open(f"/state/{name}.restore.rc").read().strip()
        out["restore_log_tail"] = open(f"/state/{name}.restore.log", errors="replace").read()[-3000:]
        out["m2_kb"] = subprocess.run(["du", "-sk", f"/m2/{name}"], capture_output=True, text=True).stdout.split()[0]
        out["built_rc"] = open(f"/state/{name}.built.rc").read().strip()
        out["built_log_tail"] = open(f"/state/{name}.built.log", errors="replace").read()[-2000:]
        out["m2b_kb"] = subprocess.run(["du", "-sk", f"/m2b/{name}"], capture_output=True, text=True).stdout.split()[0]
        out["noir_ldd_missing"] = [l for l in subprocess.run(["ldd", "/usr/local/bin/noir"], capture_output=True, text=True).stdout.splitlines() if "not found" in l]
        project = f"/work/{name}"
        shutil.copytree(f"/apps/{name}", project, symlinks=True)
        before = _listing(project)
        out["source_files"] = {"java": sum(1 for path in before if path.endswith(".java")), "all": len(before)}
        noir = harness.run(["noir", "scan", project, "-f", "json", "--no-log"], project, keep=60_000_000)
        out["noir"] = {key: noir[key] for key in ("returncode", "seconds", "peak_memory_mb", "stderr")}
        try:
            report = json.loads(noir["stdout"])
            out["noir"]["endpoints"] = [{"method": e.get("method"), "url": e.get("url"), "protocol": e.get("protocol"), "kind": e.get("kind"),
                                         "handler": e.get("handler"), "code_paths": (e.get("details") or {}).get("code_paths"),
                                         "params": len(e.get("params") or ())} for e in report.get("endpoints", ())]
            out["noir"]["errors"] = len(report.get("errors") or ())
        except ValueError:
            out["noir"]["unreadable"] = noir["stdout"][:500]
        out["build"] = harness.run(["mvn", "-o", "-B", "-q", "-DskipTests", f"-Dmaven.repo.local=/m2/{name}", "package"], project, keep=4000)
        missing = {}  # what the restore's repository has of each artifact the build could not find
        for line in out["build"]["stdout"].splitlines():
            if line.startswith("[ERROR] dependency: "):
                group, artifact, _, version = line.split()[2].split(":")[:4]
                folder = os.path.join("/m2", name, *group.split("."), artifact)
                missing[f"{group}:{artifact}:{version}"] = sorted(os.listdir(folder)) if os.path.isdir(folder) else None
        out["build"]["missing_have"] = missing
        # the project the launcher runs on: the one the build with the network made (the preparation's `target/`), built again offline
        built = f"/work/{name}-built"
        shutil.copytree(f"/built/{name}", built, symlinks=True)
        before_built = _listing(built)
        out["prep_left_behind"] = {"new_outside_target": sorted(path for path in before_built if path not in before and "target" not in path.split(os.sep))[:60],
                                   "new_outside_target_count": sum(1 for path in before_built if path not in before and "target" not in path.split(os.sep))}
        out["build_again"] = harness.run(["mvn", "-o", "-B", "-q", "-DskipTests", f"-Dmaven.repo.local=/m2b/{name}", "package"], built, keep=4000)
        project, before = built, before_built
        out["modules"] = []
        if out["built_rc"] == "0":
            jars, names = _start_class_jars(project)
            out["jars_made"] = len(names)
            for item in jars:
                module = {"module": item["module"], "start_class": item["start_class"], "boot_version": item["boot_version"], "jdk": item["jdk"]}
                unpacked = os.path.join(os.path.dirname(item["jar"]), "unpacked")
                os.makedirs(unpacked, exist_ok=True)
                module["unpack"] = harness.run(["jar", "xf", item["jar"]], unpacked, keep=500)
                module["runs"] = runs = []
                runs.append(_launch(project, unpacked, item, "actuator", "actuator", "started", [], 120))
                first, port = runs[0], []
                if "port out of range" in (first["error"] or ""):  # Netty (WebFlux) takes no port -1: a real one, on the loopback
                    port = ["server.port=0", "server.address=127.0.0.1"]
                    runs.append(_launch(project, unpacked, item, "actuator-port0", "actuator", "started", port, 120))
                    first = runs[-1]
                if first["returncode"] == 2:
                    runs.append(_launch(project, unpacked, item, "handler-methods", "handler-methods", "started", port, 120))
                runs.append(_launch(project, unpacked, item, "aot", "handler-methods", "aot", port, 120))
                if first["returncode"] == 1:  # it does not load: what could reach the mappings without the services
                    runs.append(_launch(project, unpacked, item, "lazy", "actuator", "started", [*port, *LAZY], 120))
                    runs.append(_launch(project, unpacked, item, "lazy-handler-methods", "handler-methods", "started", [*port, *LAZY], 120))
                    runs.append(_launch(project, unpacked, item, "exclude", "actuator", "started", [*port, *EXCLUDE], 120))
                    runs.append(_launch(project, unpacked, item, "exclude-lazy-aot", "handler-methods", "aot", [*port, *EXCLUDE, *LAZY], 120))
                    if name == "ruoyi":  # the service it needs, on this machine: what the routes are when the application does load
                        runs.extend(_with_mariadb(project, unpacked, item))
                best = next((run for run in runs if run["routes"]), None)
                # Spring Boot's own AOT processor (what `spring-boot:process-aot` runs): does its output hold the routes
                output = f"/work/aot-{abs(hash(item['jar'])) % 10**8}"
                module["aot_processor"] = aot = harness.run(
                    ["timeout", "--kill-after=10", "120", "java", "-Xmx1g", "-cp", f"{unpacked}/BOOT-INF/classes:{unpacked}/BOOT-INF/lib/*",
                     "org.springframework.boot.SpringApplicationAotProcessor", item["start_class"], f"{output}/src", f"{output}/res", f"{output}/cls", "g", "a",
                     *_properties(item["boot_version"] or "3.5")], project, keep=3000)
                generated = [os.path.join(folder, file) for folder, _, files in os.walk(output) for file in files]
                text = "".join(open(path, errors="replace").read() for path in generated if path.endswith((".java", ".json")))
                patterns = sorted({pattern for run in runs for row in run["routes"] for pattern in row.get("patterns", ())})
                aot["generated_files"], aot["routes_named"] = len(generated), {"of": len(patterns), "found": sum(chr(34) + pattern + chr(34) in text for pattern in patterns)}
                if best:
                    wanted = {row["class"] for row in best["routes"] if "class" in row}
                    index = _class_index(unpacked, names)
                    found = {canonical: index[canonical] for canonical in wanted if canonical in index}
                    module["handler_classes"] = {"named": len(wanted), "in_project": len(found)}
                    if found:
                        places = sorted({where for _, where in found.values()})
                        module["javap"] = harness.run(["javap", "-l", "-p", "-s", "-cp", ":".join(places), *sorted(binary for binary, _ in found.values())],
                                                      project, keep=20_000_000)
                        module["javap_text"] = module["javap"].pop("stdout")
                out["modules"].append(module)
        after = _listing(project)
        out["left_behind"] = {
            "new_outside_target": sorted(path for path in after if path not in before and "target" not in path.split(os.sep))[:60],
            "new_outside_target_count": sum(1 for path in after if path not in before and "target" not in path.split(os.sep)),
            "changed_outside_target": sorted(path for path in after if path in before and after[path] != before[path] and "target" not in path.split(os.sep))[:30],
            "files_in_target": sum(1 for path in after if path not in before and "target" in path.split(os.sep)),
        }
    except Exception:
        out["harness_error"] = traceback.format_exc()[-3000:]
    return out


@app.function(cpu=2, memory=4096, timeout=3000)
def cold(name: str) -> dict:
    """With the network open, as the preparation has it: the restore and the build from an empty repository."""
    import shutil
    import traceback

    out = {"kind": "cold", "name": name}
    try:
        project, repository = f"/work/{name}", f"/tmp/m2-cold-{name}"
        shutil.copytree(f"/apps/{name}", project, symlinks=True)
        out["restore"] = harness.run([*GO_OFFLINE.split(), f"-Dmaven.repo.local={repository}"], project, keep=4000)
        out["package"] = harness.run(["mvn", "-B", "-q", "-DskipTests", f"-Dmaven.repo.local={repository}", "package"], project, keep=4000)
        shutil.rmtree(project)  # the build alone, from an empty repository: what a preparation that builds costs
        shutil.copytree(f"/apps/{name}", project, symlinks=True)
        out["build_alone"] = harness.run(["mvn", "-B", "-q", "-DskipTests", f"-Dmaven.repo.local=/tmp/m2-alone-{name}", "package"], project, keep=4000)
    except Exception:
        out["harness_error"] = traceback.format_exc()[-3000:]
    return out


@app.function(cpu=2, memory=4096, timeout=3000)
def restore_variants(name: str) -> dict:
    """Why the restore does not make an offline build: other ways to restore (each from an empty repository, with the network), then
    `mvn -o package` over the same repository. The plugin pinned as `preparation.RESTORES["maven"]` pins it, the plugin unpinned (the
    version Maven resolves), and `dependency:resolve` with `dependency:resolve-plugins`."""
    import shutil
    import traceback

    out = {"kind": "restore-variants", "name": name, "variants": {}}
    variants = {"pinned-go-offline": [GO_OFFLINE.split()], "unpinned-go-offline": [["mvn", "-B", "-q", "dependency:go-offline"]],
                "resolve": [["mvn", "-B", "-q", "dependency:resolve", "dependency:resolve-plugins"]]}
    for label, commands in variants.items():
        try:
            project, repository = f"/work/{name}-{label}", f"/tmp/m2-{label}-{name}"
            shutil.copytree(f"/apps/{name}", project, symlinks=True)
            restore = [harness.run([*command, f"-Dmaven.repo.local={repository}"], project, keep=1500) for command in commands]
            offline = harness.run(["mvn", "-o", "-B", "-q", "-DskipTests", f"-Dmaven.repo.local={repository}", "package"], project, keep=60000)
            out["variants"][label] = {"restore": [{k: step[k] for k in ("returncode", "seconds", "peak_memory_mb")} for step in restore],
                                      "offline_package": {k: offline[k] for k in ("returncode", "seconds", "peak_memory_mb")},
                                      "missing": sum(1 for line in offline["stdout"].splitlines() if line.startswith("[ERROR] dependency: "))}
        except Exception:
            out["variants"][label] = {"harness_error": traceback.format_exc()[-1500:]}
    return out


@app.function(cpu=2, memory=4096, timeout=600, block_network=True)
def noir_fixture() -> dict:
    """Noir over the fixture's sources, whose routes `modal_probe.py` has from Spring: what it says of an alias, an inherited and an
    interface-declared handler, overloads, a nested class, a route under a profile that is not active, a router function."""
    run = harness.run(["noir", "scan", "/fixture-src", "-f", "json", "--no-log"], "/fixture-src", keep=5_000_000)
    report = json.loads(run["stdout"])
    return {"kind": "noir-fixture", "returncode": run["returncode"], "seconds": run["seconds"], "peak_memory_mb": run["peak_memory_mb"],
            "endpoints": [{"method": e.get("method"), "url": e.get("url"), "handler": e.get("handler"), "code_paths": (e.get("details") or {}).get("code_paths")}
                          for e in report.get("endpoints", ())]}


@app.local_entrypoint()
def main():
    OUT.mkdir(parents=True, exist_ok=True)
    if os.environ.get("VARIANTS") == "restore":
        for answer in restore_variants.map(["petclinic", "microservices"]):
            (OUT / f"{answer['name']}-restore.json").write_bytes((json.dumps(answer, indent=1, ensure_ascii=False, sort_keys=True) + chr(10)).encode("utf-8"))
            print(f"=== {answer['name']} restore variants:")
            for label, result in answer["variants"].items():
                print("  ", label, result)
        return
    if os.environ.get("VARIANTS") == "fixture":
        answer = noir_fixture.remote()
        (OUT / "fixture-noir.json").write_bytes((json.dumps(answer, indent=1, ensure_ascii=False, sort_keys=True) + chr(10)).encode("utf-8"))
        print(f"=== fixture noir: rc {answer['returncode']} {answer['seconds']} s, {len(answer['endpoints'])} endpoints")
        return
    names = (os.environ.get("VARIANTS") or ",".join(APPS)).split(",")
    for answer in [*real.map(names), *cold.map(names)]:
        name = answer["name"]
        kind = answer["kind"]
        for module in answer.get("modules", ()):
            text = module.pop("javap_text", None)
            if text is not None:  # only the methods the routes name
                keep = {(row["name"], row["descriptor"]) for run in module["runs"] for row in run["routes"] if "name" in row}
                (OUT / f"{name}-javap-{module['module'].replace('/', '_') or 'root'}.txt").write_bytes(harness.trim_javap(text, keep).encode("utf-8"))
        harness.slim(answer)
        (OUT / f"{name}-{kind}.json").write_bytes((json.dumps(answer, indent=1, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8"))
        print(f"=== {name} {kind}: {'HARNESS ERROR ' + answer['harness_error'][-300:] if 'harness_error' in answer else ''}")
        if kind == "real":
            print(f"  built rc {answer.get('built_rc')}, build again rc {answer.get('build_again', {}).get('returncode')}")
            print(f"  restore rc {answer.get('restore_rc')}, noir {answer.get('noir', {}).get('returncode')} with "
                  f"{len(answer.get('noir', {}).get('endpoints', ()))} endpoints, build rc {answer.get('build', {}).get('returncode')} in "
                  f"{answer.get('build', {}).get('seconds')} s")
            for module in answer.get("modules", ()):
                for run in module["runs"]:
                    print(f"  {module['module'] or '.'} {run['label']}: exit {run['returncode']} {run['seconds']} s {run['peak_memory_mb']} MB, "
                          f"{len(run['routes'])} rows, listeners {[(l['port'], l.get('gone_s')) for l in run['listeners']]} {run['error'] and run['error'][:160]}")
        else:
            print(f"  restore rc {answer.get('restore', {}).get('returncode')} in {answer.get('restore', {}).get('seconds')} s; "
                  f"package rc {answer.get('package', {}).get('returncode')} in {answer.get('package', {}).get('seconds')} s; "
                  f"build alone rc {answer.get('build_alone', {}).get('returncode')} in {answer.get('build_alone', {}).get('seconds')} s")
