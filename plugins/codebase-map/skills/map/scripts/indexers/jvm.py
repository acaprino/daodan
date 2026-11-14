"""scip-java for Java and Kotlin: the image, the two phases and the container run both languages share.

scip-java reads what the build compiles: it runs Maven or Gradle with its compiler plugins, and a build runs
the project's build scripts and plugins. So the build happens only in a container (`container.run_in_container`,
spec `docs/specs/2026-11-12-passo-dinamico.md`, sections 2-4), never on the host: without a container the
language is `unavailable`, with the gap's cause and remedy.

- Image: `IMAGE`, Temurin's JDK 17 on Ubuntu, pinned by digest; the engine pulls it on first use and keeps it.
  It holds no other JDK: a build whose toolchain or compiler release asks for a newer one is `unavailable` with
  that cause (`newer_jdk`), until an image for that JDK exists.
- What the image lacks, Daodan downloads on the host into the shared directory, verified, and the copy carries
  into the container (`tools`): scip-java's classpath at `VERSION`, each jar pinned by sha256, and the build tool
  the project asks for. The wrapper's `distributionUrl` names it (`gradle/wrapper/gradle-wrapper.properties`,
  `.mvn/wrapper/maven-wrapper.properties`), checked with its `distributionSha256Sum`, else with the checksum
  the distribution site publishes; without a wrapper, `GRADLE` or `MAVEN`. A wrapper that names another site is
  `unavailable`, and nothing is fetched from it. In the container the wrapper only calls that tool, so no build
  downloads a distribution.
- Preparation, on a network that reaches only `registries()` through the operation's proxy: the build and
  `scip-java index`. The build downloads the project's dependencies and its Gradle plugins; its scripts run
  there and stay in the container (spec, section 4).
- Execution, with no network, from the image the preparation leaves: what reads the build's output, and
  every output copied under `OUT`, which comes back into `<work_dir>/container/out`.

A phase is one bash script (`script`). Each step prints `DAODAN_STEP` lines into the phase log, read back by
`steps` as the runs of the contract, with the container's memory peak (cgroup `memory.peak`).
"""
from __future__ import annotations

import collections
import hashlib
import re
import shutil
from pathlib import Path

import code_graph

VERSION = "0.14.2"  # org.scip-code:scip-java, released 2026-11-12
IMAGE = "eclipse-temurin:17-jdk-noble@sha256:1bedb04434bd275ef072355e9caec2a22be5240fbe82ad51a59323f2bbcab4a6"
JDK = 17
# The classpath coursier 2.1.24 resolves for org.scip-code:scip-java:0.14.2 (14 November 2026), from Maven Central.
CLASSPATH = (
    ("org.scip-code:scip-java:0.14.2", "77c9d643438dab356b0e760f8f427ea29d092a81cfc55591719a66772c19909a"),
    ("org.scip-code:scip-aggregator:0.14.2", "0e49cf8ffa802879176097d1c5fcd9513a66a42c0985c4ff631fd596b6d38ece"),
    ("org.scip-code:scip-kotlin-analysis:0.14.2", "f85fda876b4cabba91a6b602f15af56e0312ccf8f44fa5f3e18a9b8f993d3849"),
    ("com.github.ajalt.clikt:clikt-jvm:5.1.0", "75c330967db15a5c591fba69fc3b18ffb68271d54f90f21c1c9c52e86faeb9d6"),
    ("org.jetbrains.kotlin:kotlin-stdlib:2.4.21", "bd8250210584cb659847dce9cda660f8e9906e5def7fbebcea93dc6dcb6a88a3"),
    ("org.jetbrains.kotlinx:kotlinx-serialization-json-jvm:1.13.0",
     "389b0dd9b4b952db889c160a2478b1cbe54680804f5315756108389dbe9df251"),
    ("org.scip-code:scip-java-bindings:0.10.0", "fd3c27dabf59eab60be774ba228d38d94e01379c0790a8a66916d9ca5e8568d8"),
    ("org.scip-code:scip-shared:0.14.2", "8c58e069af784b178347849f9b0e127781d9070210201ac6617947ace4f895be"),
    ("org.scip-code:scip-kotlin-bindings:0.10.0", "cc65444c07dc9f7a1c1ad55313975cd6141ba76e9d956f1c26c4b96ef94acab1"),
    ("org.jetbrains.kotlin:kotlin-compiler:2.4.0", "66e73eacd619c9beb7c22042117af36b443529c4d80237ee82cc4b2acb6f3d0b"),
    ("com.github.ben-manes.caffeine:caffeine:3.3.1",
     "1f916d052a3f8c0c10951f343f043f176ff2d3c2f9e380e15f0be673c5e67c48"),
    ("org.jetbrains.kotlinx:kotlinx-collections-immutable-jvm:0.5.2",
     "6d7f84d544644fa857bba83292820cdb1e0dae408fa41d2dced903d290286463"),
    ("com.github.ajalt.clikt:clikt-core-jvm:5.1.0", "7f78049fa8159bac05ce09ddef4313248d4cad0014a744214c1150d14e3661e7"),
    ("com.github.ajalt.mordant:mordant-jvm:3.0.2", "9ed3b976fcccc78da746d49866fa8ebb8f10530a93c544ea0420259a607dd95e"),
    ("org.jetbrains:annotations:13.0", "ace2a10dc8e2d5fd34925ecac03e4988b2c0f851650c94b8cef49ba1bd111478"),
    ("org.jetbrains.kotlinx:kotlinx-serialization-core-jvm:1.13.0",
     "db2eb98f585a408970ce726af9dfbaccbdfe5df498ccd9dba9918d208974302d"),
    ("com.google.protobuf:protobuf-java:4.34.2", "780e269712d59ae34b87b702ce26aede7982804299dd56a65aa84bda6c145268"),
    ("com.google.protobuf:protobuf-kotlin:4.34.2", "6ceb1f0f7071682a424cf72983bb08b72b775eec3ff4afbc87a48c0060baf6e8"),
    ("org.jspecify:jspecify:1.0.1", "070d75f261fe4c5b8202508366715f7f2d4660f88c8ef7e6d3575e48c9683b66"),
    ("com.google.errorprone:error_prone_annotations:2.50.0",
     "4667724877f1d37a689202da191e23efa7657c62eef93ccdac406eccfe5cdd0a"),
    ("com.github.ajalt.mordant:mordant-core-jvm:3.0.2",
     "651c3bd74ff4e98db4d58e3dcf4b14e8099ee0d220e672f571f8cfeee4493905"),
    ("com.github.ajalt.mordant:mordant-jvm-jna-jvm:3.0.2",
     "41063442c8891b2774536a9b87a5062a7fd20e6f1949974c6da72f49472d6f4d"),
    ("com.github.ajalt.mordant:mordant-jvm-ffm-jvm:3.0.2",
     "10224784125c9f1782c1d4f1d38f3d54236fcc55c030a2ad00cbe4306e162ba4"),
    ("com.github.ajalt.mordant:mordant-jvm-graal-ffi-jvm:3.0.2",
     "6dd4bebc164aeacddacc8f98e8f871e00fd21ce7bc2eb0d18230ea83bddfc86a"),
    ("com.github.ajalt.colormath:colormath-jvm:3.6.0",
     "59f741adfe62053066782d8b1a45afd06685a4bc64b33277e54876b993ed885c"),
    ("net.java.dev.jna:jna:5.14.0", "34ed1e1f27fa896bca50dbc4e99cf3732967cec387a7a0d5e3486c09673fe8c6"),
)
# The build tool of a project without a wrapper: the versions scip-java's release image ships.
GRADLE = ("9.9.1", "d8a18a7a841dd5df825d35a685fad6f2d7f12ac0c280e57b67c27b4a520ba228")
MAVEN = ("3.10.0", "1f6d9909266510f039f59aa0e13dcd2c66da85f043e56276e41f2918f8bddaff")
# The official distribution sites, the only ones a wrapper may name.
GRADLE_SITE = "https://services.gradle.org/distributions/"
MAVEN_SITE = "https://repo.maven.apache.org/maven2/org/apache/maven/apache-maven/"
DISTRIBUTION = {
    "gradle": re.compile(r"https://services\.gradle\.org/distributions/gradle-[\w.\-]+-(?:bin|all)\.zip"),
    "maven": re.compile(r"https://(?:repo\.maven\.apache\.org|repo1\.maven\.org)/maven2/org/apache/maven/"
                        r"apache-maven/([\w.\-]+)/apache-maven-\1-bin\.zip"),
}
# Repositories some builds declare beyond the operation's default registries: JCenter (read-only) and Google's
# Maven under both its names.
REGISTRIES_ADDED = ("jcenter.bintray.com", "dl.google.com", "maven.google.com")
LIB, TOOLS, OUT = "/app/scip-java/lib", "/daodan/tools", "/daodan/out"
ENV = {"HOME": "/root", "TERM": "dumb"}
PIDS = 4096  # threads count: Gradle, the Kotlin daemon and scip-java each start a hundred or more

HEAD = r'''set -u
export LANG=en_US.UTF-8 LANGUAGE=en_US:en LC_ALL=en_US.UTF-8
WORK=${DAODAN_WORK:-/work}
OUT=${DAODAN_OUT:-/daodan/out}
SCIP_JAVA=/app/scip-java/bin/scip-java
mkdir -p "$OUT" /app/scip-java/bin
cd "$WORK" || exit 70
step() {
  local name=$1 code
  shift
  echo "DAODAN_STEP begin $name $(date +%s.%N)"
  "$@"
  code=$?
  echo "DAODAN_STEP end $name $code $(date +%s.%N)"
  return $code
}
trap 'echo "DAODAN_PEAK $(cat /sys/fs/cgroup/memory.peak 2>/dev/null || echo -)"' EXIT
export JAVA_HOME=${JAVA_HOME:-/opt/java/openjdk}
export PATH="$JAVA_HOME/bin:$PATH"
if ! "$JAVA_HOME/bin/java" -version 2>&1 | grep -q 'version "17\.'; then
  step jdk sh -c 'echo "no JDK 17 at $JAVA_HOME"; exit 70'
  exit 70
fi
# The options scip-java's own image gives its JVM, for the compiler classes it reads.
JAVA_OPTS=--add-exports=jdk.compiler/com.sun.tools.javac.api=ALL-UNNAMED
for package in code model tree util; do
  JAVA_OPTS="$JAVA_OPTS --add-exports=jdk.compiler/com.sun.tools.javac.$package=ALL-UNNAMED"
done
export JAVA_OPTS
printf '#!/bin/sh\nexec java $JAVA_OPTS -classpath "/app/scip-java/lib/*" org.scip_code.scip_java.ScipJava "$@"\n' \
  > "$SCIP_JAVA"
chmod +x "$SCIP_JAVA"
JAVA_TOOL_OPTIONS="-XX:MaxRAMPercentage=80.0 -XX:+UseContainerSupport"
'''

# The JVM ignores HTTPS_PROXY: Java tools get the proxy as system properties, Maven also in its settings. The
# build tools Daodan brought are unpacked and put first on the PATH, and a wrapper only calls them.
PREPARE = r'''if [ -n "${HTTPS_PROXY:-}" ]; then
  address=${HTTPS_PROXY#*://}
  address=${address%%/*}
  host=${address%:*}
  port=${address##*:}
  JAVA_TOOL_OPTIONS="$JAVA_TOOL_OPTIONS -Dhttps.proxyHost=$host -Dhttps.proxyPort=$port"
  JAVA_TOOL_OPTIONS="$JAVA_TOOL_OPTIONS -Dhttp.proxyHost=$host -Dhttp.proxyPort=$port"
  mkdir -p "$HOME/.m2"
  printf '%s\n' '<settings><proxies>' \
    "<proxy><id>https</id><protocol>https</protocol><host>$host</host><port>$port</port></proxy>" \
    "<proxy><id>http</id><protocol>http</protocol><host>$host</host><port>$port</port></proxy>" \
    '</proxies></settings>' > "$HOME/.m2/settings.xml"
fi
export JAVA_TOOL_OPTIONS
for zip in /daodan/tools/*.zip; do
  [ -f "$zip" ] || continue
  mkdir -p "${zip%.zip}" && (cd "${zip%.zip}" && jar xf "$zip") && rm -f "$zip" || exit 70
done
for tool in /daodan/tools/*/*/bin/gradle /daodan/tools/*/*/bin/mvn; do
  [ -f "$tool" ] || continue
  chmod +x "${tool%/*}"/*
  PATH="${tool%/*}:$PATH"
  wrapper=gradlew
  [ "${tool##*/}" = mvn ] && wrapper=mvnw
  if [ -e "$wrapper" ]; then
    printf '#!/bin/sh\nexec %s "$@"\n' "$tool" > "$wrapper"
    chmod +x "$wrapper"
  fi
done
export PATH
'''
# A build that needs a newer JDK says so: Gradle's toolchain request, javac's release, a class file version
# (61 is Java 17's).
NEWER = (re.compile(r"languageVersion=(\d+)"), re.compile(r"release version (\d+) not supported"),
         re.compile(r"invalid (?:target|source) release:? (\d+)"))
CLASS_FILE = re.compile(r"class file (?:has wrong )?version (\d+)\.0")


def registries() -> tuple[str, ...]:
    import container
    return tuple(dict.fromkeys((*container.REGISTRIES, *REGISTRIES_ADDED)))


def script(phase: str, body: str) -> str:
    """The bash script of one phase: the shared head, the preparation's network setup, then `body`."""
    return f"# daodan {phase}\n{HEAD}" + (PREPARE if phase == "prepare" else "export JAVA_TOOL_OPTIONS\n") + body


def properties(path: Path) -> dict[str, str]:
    """A Java properties file's `key=value` lines, with the escapes `\\:` and `\\=` read back."""
    out = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        match = re.match(r"\s*([^#!\s=:][^\s=:]*)\s*[=:]\s*(.*?)\s*$", line)
        if match:
            out[match.group(1)] = re.sub(r"\\(.)", r"\1", match.group(2))
    return out


def wanted(project_dir: Path) -> list[tuple[str, str, str | None, str]]:
    """`(tool, url, sha256, where)` of each build tool the project's build asks for, `sha256` None when only the
    distribution site states it."""
    project_dir, out = Path(project_dir), []
    builds = {"gradle": ("settings.gradle", "settings.gradle.kts", "build.gradle", "build.gradle.kts"),
              "maven": ("pom.xml",)}
    wrappers = {"gradle": "gradle/wrapper/gradle-wrapper.properties", "maven": ".mvn/wrapper/maven-wrapper.properties"}
    defaults = {"gradle": (f"{GRADLE_SITE}gradle-{GRADLE[0]}-bin.zip", GRADLE[1]),
                "maven": (f"{MAVEN_SITE}{MAVEN[0]}/apache-maven-{MAVEN[0]}-bin.zip", MAVEN[1])}
    for tool, files in builds.items():
        if not any((project_dir / name).is_file() for name in files):
            continue
        wrapper = project_dir / wrappers[tool]
        values = properties(wrapper) if wrapper.is_file() else {}
        if values.get("distributionUrl"):
            out.append((tool, values["distributionUrl"], values.get("distributionSha256Sum") or None, wrappers[tool]))
        else:
            out.append((tool, *defaults[tool], "Daodan's default"))
    return out


def sha256(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def fetched(url: str, target: Path, digest: str | None, *, published: str | None = None,
            sha1_url: str | None = None) -> Path:
    """`url` in the shared directory once, verified with `digest`, else with the sha256 `published` names or the
    sha1 at `sha1_url`; a cached file is checked again when `digest` is known. A Gap when it cannot be."""
    import container
    from resolve_edges import download, open_url
    try:
        if target.is_file():
            if digest is None or sha256(target) == digest:
                return target
            raise ValueError(f"checksum mismatch for {url}")
        if digest is None and published:
            with open_url(published, timeout=60) as response:
                digest = response.read().decode("ascii", "replace").split()[0].lower()
        return download(url, target, sha256=digest, sha1_url=None if digest else sha1_url)
    except (OSError, ValueError, IndexError) as error:
        raise container.Gap(f"{url} could not be downloaded and verified: {error}",
                            "check the connection; with a mismatch, check the wrapper's distributionSha256Sum") \
            from error


def tools(project_dir: Path) -> dict[str, Path]:
    """The container paths and host files of scip-java's classpath and of the build tools the project asks for,
    downloaded once into the shared directory; a Gap when a wrapper names another site or a file cannot be
    verified."""
    import container
    from resolve_edges import MAVEN_CENTRAL, maven_central_dir, shared_engine_dir
    inputs = {}
    for coordinate, digest in CLASSPATH:
        group, artifact, version = coordinate.split(":")
        relative = f"{group.replace('.', '/')}/{artifact}/{version}/{artifact}-{version}.jar"
        inputs[f"{LIB}/{artifact}-{version}.jar"] = fetched(f"{MAVEN_CENTRAL}/{relative}",
                                                            maven_central_dir() / relative, digest)
    for tool, url, digest, where in wanted(project_dir):
        if not DISTRIBUTION[tool].fullmatch(url):
            site = GRADLE_SITE if tool == "gradle" else "Maven Central"
            raise container.Gap(f"the {tool} wrapper ({where}) asks for {url}, which is not {site}; nothing is "
                                f"fetched from it", f"point distributionUrl in {where} at {site}")
        name = url.rsplit("/", 1)[1]
        inputs[f"{TOOLS}/{name}"] = fetched(url, shared_engine_dir(tool) / name, digest,
                                            published=url + ".sha256" if tool == "gradle" else None,
                                            sha1_url=url + ".sha1" if tool == "maven" else None)
    return inputs


def newer_jdk(text: str) -> int | None:
    """The newest JDK above `JDK` a failed build's output asks for, or None."""
    found = [int(value) for pattern in NEWER for value in pattern.findall(text)]
    found += [int(value) - 44 for value in CLASS_FILE.findall(text)]
    found = [value for value in found if value > JDK]
    return max(found) if found else None


def judged(result: dict, text: str) -> dict:
    """A failed preparation that asks for a newer JDK is a gap: the image has JDK 17 only."""
    jdk = newer_jdk(text) if result["state"] not in ("done", "gap") else None
    if jdk is None:
        return result
    return {**result, "state": "gap", "cause": f"the build asks for JDK {jdk}; Daodan's image holds JDK {JDK} only",
            "remedy": f"none yet: no image with JDK {jdk} exists, so this project is not indexed"}


def _errors(line: str) -> str | None:
    # As `code_graph.measured`: an indexer's own errors.
    return line[line.find(" ERROR ") + 7:][:200] if " ERROR " in line else None


def steps(text: str, phase: str) -> list[dict]:
    """The runs a phase log records: one per step, with its exit code, seconds, output tail and `ERROR` lines;
    `peak_mb` is the container's memory peak over the phase. A step cut off (time limit) has no exit code."""
    runs, current, tail, errors, peak, patched = [], None, collections.deque(maxlen=80), [], None, None

    def close(code, ended):
        output = "\n".join(tail)
        run = {"step": current[0], "phase": phase, "returncode": code,
               "seconds": round(ended - current[1], 1) if ended is not None else None, "peak_mb": None,
               "stderr_tail": output[-2500:], "stderr_errors": len(errors),
               "stderr_error_examples": list(dict.fromkeys(errors))[:5]}
        if patched is not None and current[0] == "plain-javac":
            run["patched_pom_removed"] = patched
        runs.append(run)

    for line in text.splitlines():
        if line.startswith("DAODAN_STEP "):
            words = line.split()
            if words[1] == "begin":
                current, tail, errors, patched = (words[2], float(words[3])), collections.deque(maxlen=80), [], None
            elif current is not None:
                close(int(words[3]), float(words[4]))
                current = None
        elif line.startswith("DAODAN_PEAK "):
            value = line.split()[1]
            peak = round(int(value) / 2**20) if value.isdigit() else None
        elif current is not None:
            if line.startswith("DAODAN_PATCHED "):
                import json
                patched = json.loads(line.split(" ", 1)[1])
            tail.append(line)
            found = _errors(line)
            if found:
                errors.append(found)
    if current is not None:
        close(None, None)
    for run in runs:
        run["peak_mb"] = peak
    return runs


def unavailable(cause: str, remedy: str) -> dict:
    """No index can be built here: the contract's `unavailable`, with `reason` and `install`."""
    indexer = {"name": "scip-java", "version": VERSION, "seconds": 0, "peak_mb": None}
    return {"indexes": [], "runs": [], "indexer": indexer, "state": "unavailable", "reason": cause, "install": remedy}


def failed(result: dict, runs: list[dict]) -> dict:
    """No index: the cause the run gives, with the output tail of its last step."""
    last = runs[-1] if runs else {}
    tail = (last.get("stderr_tail") or "").strip()[-800:]
    cause = result.get("cause") or f"exit code {last.get('returncode')}"
    return {"indexes": [], "runs": runs, "indexer": code_graph.indexer("scip-java", VERSION, runs),
            "state": "failed", "reason": f"scip-java wrote no index ({cause}): {tail}",
            "errors": sum(run.get("stderr_errors") or 0 for run in runs)}


def run(project_dir: Path, work_dir: Path, prepare: str, execute: str, *, memory: int, engine=None,
        prepare_timeout: float = 1800, timeout: float = 600) -> tuple[dict, list[dict], Path]:
    """Both phases in one container run over a copy of `project_dir` and the `tools` it needs: the operation's
    result (`judged`), the runs of both logs, and the folder the outputs came back into."""
    import container
    out_dir = Path(work_dir) / "container"
    out = out_dir / Path(OUT).name
    shutil.rmtree(out, ignore_errors=True)
    for phase in ("prepare", "execute"):
        (out_dir / f"{phase}.log").unlink(missing_ok=True)
    result = container.run_in_container(
        project_dir, ["bash", "-c", script("execute", execute)], image=IMAGE, out_dir=out_dir,
        prepare=["bash", "-c", script("prepare", prepare)], outputs=[OUT], env=dict(ENV), timeout=timeout,
        prepare_timeout=prepare_timeout, memory=memory, pids=PIDS, registries=registries(), engine=engine,
        inputs=lambda: tools(project_dir))
    runs, prepared = [], ""
    for phase in ("prepare", "execute"):
        log = out_dir / f"{phase}.log"
        if log.is_file():
            text = log.read_text(encoding="utf-8", errors="replace")
            prepared = text if phase == "prepare" else prepared
            runs += steps(text, phase)
    return judged(result, prepared), runs, out


def place(source: Path, target: Path) -> Path | None:
    """An output moved from the container's folder to where the contract names it; None when it is missing."""
    if not source.exists():
        return None
    if target.is_dir():
        shutil.rmtree(target)
    else:
        target.unlink(missing_ok=True)
    shutil.move(str(source), str(target))
    return target
