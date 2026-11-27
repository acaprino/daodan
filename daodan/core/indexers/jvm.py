"""scip-java for Java and Kotlin: the image, the two phases and the container run both languages share.

scip-java reads what the build compiles: it runs Maven or Gradle with its compiler plugins, and a build runs
the project's build scripts and plugins. So the build happens only in a container (`container.run_in_container`,
spec `docs/specs/2026-11-12-passo-dinamico.md`, sections 2-4), never on the host: without a container the
language is `unavailable`, with the gap's cause and remedy.

- Image: `IMAGE`, the base every language shares (`preparation.IMAGE`), pinned by digest; the engine pulls it on
  first use and keeps it. Temurin's JDK 17 (`preparation.TEMURIN`) comes as an input like the build tools and is
  unpacked into the state volume, linked where the scripts look for it (`preparation.UNPACK_JDK`), before
  anything runs Java. Another JDK a build asks for, the preparation installs; one it cannot is `unavailable`
  with that cause (`judged`).
- What the image lacks, Daodan downloads on the host into the shared directory, verified, and the copy carries
  into the container (`tools`): scip-java's classpath at `VERSION`, each jar pinned by sha256, and the build tool
  the project asks for. The wrapper's `distributionUrl` names it (`gradle/wrapper/gradle-wrapper.properties`,
  `.mvn/wrapper/maven-wrapper.properties`), checked with its `distributionSha256Sum`, else with the checksum
  the distribution site publishes; without a wrapper, `GRADLE` or `MAVEN`. A wrapper that names another site is
  `unavailable`, and nothing is fetched from it. In the container the wrapper only calls that tool, so no build
  downloads a distribution.
- Preparation, on a network that reaches only `registries` through the operation's proxy: the steps of
  `preparation` (its proxy for the JVM, a JDK the pre-map states above the image's installed by mise, the Android
  SDK packages it states installed by Google's sdkmanager after its licences are accepted as a CI accepts them,
  `ANDROID_HOME` in both phases, the restore of the dependencies with Gradle's or Maven's own command), then the
  build and `scip-java index`. The build
  downloads the project's dependencies and its Gradle plugins; its scripts run there and stay in the container
  (spec, section 4). What a step could not do (`preparation.missing`, `preparation.restore_gaps`) is a gap of
  the contract, and the build goes on.
- Execution, with no network, from the same image: what reads the build's output, and every output copied
  under `OUT`, which comes back into `<work_dir>/container/out`. What the preparation keeps for it lies in the
  operation's volumes (`container.STATE`): scip-java and the build tools, `HOME` with the dependency caches
  (the JVM and Gradle are pointed there too), and the index under `KEPT`, copied into `OUT` first.

A phase is one bash script (`script`). Each step prints `DAODAN_STEP` lines into the phase log, read back by
`steps` as the runs of the contract, with the container's memory peak (cgroup `memory.peak`).
"""
from __future__ import annotations

import collections
import hashlib
import re
import shutil
from pathlib import Path
from typing import Callable

import code_graph
import preparation

VERSION = "0.14.2"  # org.scip-code:scip-java, released 2026-11-12
IMAGE = preparation.IMAGE
JDK = 17  # `preparation.TEMURIN`
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
# The only hosts a JVM build reaches: the build runs project code, and a registry that accepts publishing
# (npm, RubyGems, PyPI, crates.io, NuGet, Go) would let it publish the source. Maven Central under its two
# names, Google's Maven under its two and JCenter take no upload (Central publishes through central.sonatype.com
# and the OSSRH hosts, never listed; JCenter is read-only since 2021). For Gradle also the Plugin Portal and its
# artifact host: the Portal does take plugin uploads, with the publisher's key, and Gradle resolves its plugins
# there; no other way exists to build a Gradle project that applies one.
READ_ONLY = ("repo1.maven.org", "repo.maven.apache.org", "dl.google.com", "maven.google.com", "jcenter.bintray.com")
PLUGIN_PORTAL = ("plugins.gradle.org", "plugins-artifacts.gradle.org")
LIB, TOOLS, KEPT, OUT = "/daodan/state/scip-java/lib", "/daodan/state/tools", "/daodan/state/out", "/daodan/out"
ENV = {"TERM": "dumb"}
PIDS = 4096  # threads count: Gradle, the Kotlin daemon and scip-java each start a hundred or more

# scip-java's index of the build, which the analyzers' scripts run (`scip_index`). A Gradle build runs scip-java's
# own tasks (its command when none is given) with Daodan's init script, in the phase's temporary folder:
# - `SCIP_GRADLE` leaves in each project's `scipCompileAll` only the tasks the project has. scip-java 0.14.2's Gradle
#   plugin names compileKotlinJvm and compileTestKotlinJvm in every Kotlin Multiplatform project, with or without a
#   jvm() target (ScipGradlePlugin.java, `triggers`), and Gradle stops on a name the project lacks: kotlinconf's
#   app/adminApp, JavaScript only, "Task with name 'compileKotlinJvm' not found in project ':app:adminApp'".
# - `ANDROID_GRADLE`, with the SDK the preparation installed (ANDROID_HOME), also runs each project's debug variant
#   compiles, main and unit tests: the plugin puts no Android task in `scipCompileAll` (scip-java issue 177, closed
#   as not planned), though it adds its javac plugin to every JavaCompile task of an Android project and dumps the
#   configuration of every KotlinCompile task.
SCIP_GRADLE = r'''gradle.projectsEvaluated {
    gradle.rootProject.allprojects { project ->
        def all = project.tasks.findByName('scipCompileAll')
        if (all != null) {
            all.setDependsOn(all.dependsOn.flatten().findAll {
                !(it instanceof CharSequence) || project.tasks.findByPath(it.toString()) != null
            })
        }
    }
}
'''
ANDROID_GRADLE = r'''allprojects { project ->
    project.tasks.register('daodanAndroidCompile') { task ->
        task.dependsOn(project.tasks.matching { it.name ==~ /compile\w*Debug(UnitTest)?Sources/ })
    }
}
'''
SCIP_INDEX = r'''scip_index() {
  if [ "${DAODAN_TOOL:-gradle}" = gradle ] && { [ -f build.gradle ] || [ -f build.gradle.kts ] \
      || [ -f settings.gradle ] || [ -f settings.gradle.kts ]; }; then
    local init="${TMPDIR:-/tmp}/daodan-scip.gradle"
    set -- clean scipPrintDependencies scipCompileAll
    cat > "$init" <<'GRADLE'
@SCIP_GRADLE@GRADLE
    if [ -n "${ANDROID_HOME:-}" ]; then
      cat >> "$init" <<'GRADLE'
@ANDROID_GRADLE@GRADLE
      set -- "$@" daodanAndroidCompile
    fi
    step index "$SCIP_JAVA" index --output "$OUT/index.scip" ${DAODAN_TOOL:+--build-tool=$DAODAN_TOOL} \
      -- "$@" --init-script "$init"
  else
    step index "$SCIP_JAVA" index --output "$OUT/index.scip" ${DAODAN_TOOL:+--build-tool=$DAODAN_TOOL}
  fi
}
'''.replace("@SCIP_GRADLE@", SCIP_GRADLE).replace("@ANDROID_GRADLE@", ANDROID_GRADLE)

# C.UTF-8 is built into glibc; the slim image holds no other locale.
HEAD = r'''set -u
export LANG=C.UTF-8 LC_ALL=C.UTF-8
WORK=${DAODAN_WORK:-/work}${DAODAN_ROOT:+/$DAODAN_ROOT}
OUT=${DAODAN_OUT:-$PHASE_OUT}
SCIP_JAVA=/app/scip-java/bin/scip-java
mkdir -p "$OUT" /app/scip-java/bin "$HOME"
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
JDK=17
for java in /daodan/state/tools/mise/installs/java/*/bin/java; do  # the JDK the preparation installed to run on
  [ -x "$java" ] && "$java" -version 2>&1 | grep -q "version \"\(1\.\)\?$DAODAN_JDK[.\"]" \
    && JAVA_HOME=${java%/bin/java} && JDK=$DAODAN_JDK
done
export JAVA_HOME
export PATH="$JAVA_HOME/bin:$PATH"
# The Android SDK the preparation installed (`preparation.android`), for the Android plugin in either phase.
[ -d /daodan/state/tools/android/cmdline-tools ] && export ANDROID_HOME=/daodan/state/tools/android
if ! "$JAVA_HOME/bin/java" -version 2>&1 | grep -q "version \"\(1\.\)\?$JDK[.\"]"; then  # JDK 8 is 1.8.0_N
  step jdk sh -c "echo 'no JDK $JDK at $JAVA_HOME'; exit 70"
  exit 70
fi
# The options scip-java's own image gives its JVM, for the compiler classes it reads.
JAVA_OPTS=--add-exports=jdk.compiler/com.sun.tools.javac.api=ALL-UNNAMED
for package in code model tree util; do
  JAVA_OPTS="$JAVA_OPTS --add-exports=jdk.compiler/com.sun.tools.javac.$package=ALL-UNNAMED"
done
export JAVA_OPTS
printf '#!/bin/sh\nexec java $JAVA_OPTS -classpath "%s/*" org.scip_code.scip_java.ScipJava "$@"\n' \
  /daodan/state/scip-java/lib > "$SCIP_JAVA"
chmod +x "$SCIP_JAVA"
# The JVM reads user.home from the account, not HOME: Maven's repository and Gradle's home follow HOME.
JAVA_TOOL_OPTIONS="-XX:MaxRAMPercentage=80.0 -XX:+UseContainerSupport -Duser.home=$HOME"
export GRADLE_USER_HOME="$HOME/.gradle"
# A Gradle build finds its toolchains among the image's JDK and those the preparation installed, and downloads
# none: Gradle's `org.gradle.java.installations` properties, in its user home, which every build of a run reads.
paths=/opt/java/openjdk
for java in /daodan/state/tools/mise/installs/java/*/bin/java; do
  [ -x "$java" ] && paths="$paths,${java%/bin/java}"
done
mkdir -p "$GRADLE_USER_HOME" && printf 'org.gradle.java.installations.%s\n' "paths=$paths" auto-download=false \
  > "$GRADLE_USER_HOME/gradle.properties"
'''

# The JVM ignores HTTPS_PROXY: the preparation's proxy for Java tools (`preparation.JAVA_PROXY`). The build
# tools Daodan brought are unpacked and put first on the PATH, and a wrapper only calls them.
PREPARE = preparation.JAVA_PROXY + "\n" + r'''export JAVA_TOOL_OPTIONS
for zip in /daodan/state/tools/*.zip; do
  [ -f "$zip" ] || continue
  mkdir -p "${zip%.zip}" && (cd "${zip%.zip}" && jar xf "$zip") && rm -f "$zip" || exit 70
done
for tool in /daodan/state/tools/*/*/bin/gradle /daodan/state/tools/*/*/bin/mvn; do
  [ -f "$tool" ] || continue
  chmod +x "${tool%/*}"/*
  PATH="${tool%/*}:$PATH"
  wrapper=gradlew
  [ "${tool##*/}" = mvn ] && wrapper=mvnw
  # scip-java finds a Gradle build by settings.gradle, gradlew, build.gradle or build.gradle.kts, never by
  # settings.gradle.kts alone (a composite build's root): there it finds the wrapper.
  if [ -e "$wrapper" ] || { [ "$wrapper" = gradlew ] && [ -f settings.gradle.kts ]; }; then
    printf '#!/bin/sh\nexec %s "$@"\n' "$tool" > "$wrapper"
    chmod +x "$wrapper"
  fi
done
export PATH
'''
# Under Maven scip-java indexes Java only (its getting-started table: Maven, Kotlin no). After its build, the
# Kotlin Analysis API indexer it ships reads each module's Kotlin files, as scip-java does after a Gradle build:
# the files in the source folders Maven's own model gives the module (the pre-map's, `DAODAN_MODULES`: a line per
# module, its folder, a tab, its source folders joined by `:`), with the module's classpath (Maven's own
# `dependency:build-classpath` and the reactor's compiled classes), into the build's targetroot. Each module's
# files are written as a compile task (`kotlin.tasks`) under `$1`; the caller aggregates the targetroot again.
# It returns 1, and runs nothing, when no module has a Kotlin file.
MAVEN_KOTLIN = r'''maven_kotlin() {
  local configs=$1 targetroot="$WORK/target/scip-targetroot" tab compiled module roots name list classpath
  tab=$(printf '\t')
  mkdir -p "$configs"
  printf '%s\n' "${DAODAN_MODULES:-}" | while IFS="$tab" read -r module roots; do
    name=$(printf %s "$module" | tr -c 'A-Za-z0-9.\n' _)
    printf '%s\n' "$roots" | tr : '\n' | while read -r root; do
      [ -n "$root" ] && [ -d "$WORK/$root" ] && find "$WORK/$root" -type f -name '*.kt'
    done | sort -u > "$configs/maven-$name.list"
    [ -s "$configs/maven-$name.list" ] || rm -f "$configs/maven-$name.list"
  done
  ls "$configs"/*.list >/dev/null 2>&1 || return 1
  mkdir -p "$targetroot"
  step classpath mvn -q --batch-mode dependency:build-classpath -Dmdep.outputFile=target/daodan-classpath.txt \
    -Dmdep.includeScope=test
  compiled=$(find "$WORK" -type d \( -path '*/target/classes' -o -path '*/target/test-classes' \) | sort | paste -sd: -)
  printf '%s\n' "${DAODAN_MODULES:-}" | while IFS="$tab" read -r module roots; do
    name=$(printf %s "$module" | tr -c 'A-Za-z0-9.\n' _)
    list="$configs/maven-$name.list"
    [ -f "$list" ] || continue
    classpath=$compiled
    [ -f "$WORK/$module/target/daodan-classpath.txt" ] && classpath="$classpath:$(cat "$WORK/$module/target/daodan-classpath.txt")"
    { echo "sourceroot $WORK"; printf '%s\n' "$classpath" | tr : '\n' | sed '/^$/d;s/^/classpath /'
      sed 's/^/source /' "$list"; } > "$configs/maven-$name.txt"
    step kotlin xargs -d '\n' -a "$list" java $JAVA_OPTS -classpath "/daodan/state/scip-java/lib/*" \
      org.scip_code.scip_java.kotlin_analysis.MainKt --sourceroot "$WORK" --targetroot "$targetroot" \
      --classpath "$classpath" < /dev/null
    rm -f "$list"
  done
  return 0
}
'''
PREPARE += MAVEN_KOTLIN + SCIP_INDEX
# A Gradle build whose scripts state a Java the JDK it runs on does not compile, or scip-java's compiler plugin does
# not load on (`raise_line`): `raise_levels` writes an init script, which every later Gradle of the run reads. It
# raises to 8 the source and target of a JavaCompile task that states less; with DAODAN_RAISE=all, the analyzers',
# it also replaces a toolchain under the JDK the build runs on by that JDK, compiling for the level the toolchain
# was (8 at least; with Kotlin for the JDK's, as Kotlin compiles for its toolchain and refuses a Java task that
# targets another). Each change is printed as `DAODAN_RAISED "..."`, which `steps` reads.
RAISE_LEVELS = r'''raise_levels() {
  mkdir -p "$GRADLE_USER_HOME/init.d" && cat > "$GRADLE_USER_HOME/init.d/daodan-levels.gradle" <<'GRADLE'
allprojects { project ->
    project.afterEvaluate {
        def java = project.extensions.findByType(JavaPluginExtension)
        if (java == null) return
        def runsOn = JavaVersion.current().majorVersion as int
        def name = project.path == ':' ? 'the root project' : "project ${project.path}"
        def said = { String what ->
            println 'DAODAN_RAISED ' + groovy.json.JsonOutput.toJson("${name}: ${what}".toString())
        }
        def asked = java.toolchain.languageVersion.orNull?.asInt()
        def replaced = System.getenv('DAODAN_RAISE') == 'all' && asked != null && asked < runsOn
        if (replaced) {
            java.toolchain.languageVersion.set(JavaLanguageVersion.of(runsOn))
            said("Java toolchain ${asked} -> ${runsOn}")
        }
        def level = replaced && project.extensions.findByName('kotlin') == null ? Math.max(asked, 8) : null
        def low = false
        project.tasks.withType(JavaCompile).configureEach { task ->
            if (task.options.release.isPresent()) return
            if (level != null) {
                task.sourceCompatibility = level.toString()
                task.targetCompatibility = level.toString()
                return
            }
            def before = [task.sourceCompatibility, task.targetCompatibility]
            if (JavaVersion.toVersion(before[0]) < JavaVersion.VERSION_1_8) task.sourceCompatibility = '8'
            if (JavaVersion.toVersion(before[1]) < JavaVersion.VERSION_1_8) task.targetCompatibility = '8'
            if (before != [task.sourceCompatibility, task.targetCompatibility] && !low) {
                low = true
                said("source ${before[0]} and target ${before[1]} -> 8")
            }
        }
    }
}
GRADLE
}
'''
PREPARE += RAISE_LEVELS
# A build that needs a newer JDK says so: Gradle's toolchain request (`{languageVersion=21, vendor=JetBrains, ...}`,
# the vendor read after the words, not part of them), javac's release, a class file version (61 is Java 17's).
# Regular expressions: the lines of a build's log have no grammar.
NEWER = (re.compile(r"languageVersion=(\d+)(?=(?:, vendor=(?P<vendor>[^,}]+))?)"),
         re.compile(r"release version (\d+) not supported"), re.compile(r"invalid (?:target|source) release:? (\d+)"))
CLASS_FILE = re.compile(r"class file (?:has wrong )?version (\d+)\.0")


def registries(project_dir: Path) -> tuple[str, ...]:
    """The hosts the build of `project_dir` may reach: `READ_ONLY`, and `PLUGIN_PORTAL` when Gradle builds it."""
    gradle = any(tool == "gradle" for tool, *_ in wanted(project_dir))
    return READ_ONLY + (PLUGIN_PORTAL if gradle else ())


def script(phase: str, body: str, *, setup: str = "", jdk: int = JDK, root: str = "") -> str:
    """The bash script of one phase: `setup` (the preparation's toolchains, before the head picks the JDK, `jdk`
    when one was installed), the shared head, which works in the build's folder `root` of the copy, the
    preparation's network setup, then `body`."""
    first = (f"# daodan {phase}\nPHASE_OUT={KEPT if phase == 'prepare' else OUT}\nDAODAN_JDK={jdk}\n"
             + (f"DAODAN_ROOT={root}\n" if root else ""))
    if phase == "prepare":
        return f"{first}{preparation.UNPACK_JDK}{setup}{HEAD}{PREPARE}{body}"
    carry = f'if [ -z "${{DAODAN_OUT:-}}" ] && [ -d {KEPT} ]; then cp -a {KEPT}/. "$OUT"/ || exit 70; fi\n'
    return f"{first}{preparation.UNPACK_JDK}{HEAD}{carry}export JAVA_TOOL_OPTIONS\n{body}"


def toolchains(record: dict) -> list[dict]:
    """The JDKs and the Android SDK packages the pre-map states (`toolchains`, tool `java` and those of
    `preparation.ANDROID`): what the stage hands `run`."""
    return [item for item in record.get("toolchains", []) if item.get("tool") in ("java", *preparation.ANDROID)]


_major = preparation.jdk_major  # the one parser of a JDK version, shared with the pre-map's runner


def daemon_jdk(item: dict) -> bool:
    """Whether a stated toolchain is the JDK a Gradle build's daemon file names (`premap.jvm_files.DAEMON`)."""
    from premap import jvm_files
    return item.get("declared_in", "").split("#")[0].endswith(jvm_files.DAEMON)


def for_tool(stated, tool: str | None) -> list[dict]:
    """The toolchains `stated` that state for a build by `tool` (None: the tool scip-java finds): the JDK of a daemon
    file is Gradle's alone."""
    return [item for item in stated or () if tool in (None, "gradle") or not daemon_jdk(item)]


def wanted_jdk(stated) -> dict | None:
    """The newest JDK `stated` above the image's, or at its major of another vendor than its (Temurin): a release or
    toolchain the image's JDK compiles needs nothing, one above it is installed by the preparation at the version
    stated, with the vendor's (`jetbrains-21`). Of two at one major, the one that names a vendor. Where a Gradle
    build's daemon file names a JDK, that one: the daemon runs on it, whatever toolchains the scripts name, which the
    preparation installs beside it."""
    java = [item for item in stated or () if item.get("tool") == "java"]
    java = [item for item in java if daemon_jdk(item)] or java
    other = lambda item: preparation.vendor_key(item.get("vendor")) != preparation.vendor_key(None)  # noqa: E731
    above = [item for item in java if (
        (_major(item.get("version")) or 0) > JDK or _major(item.get("version")) == JDK and other(item))]
    return max(above, key=lambda item: (_major(item["version"]), other(item))) if above else None


def inside(rel: str, folder: str) -> bool:
    """Whether the checkout path `rel` is in the build folder `folder` ('' or '.' for the project's root)."""
    return not folder or folder == "." or rel == folder or rel.startswith(folder.rstrip("/") + "/")


def applying(stated, root: str) -> list[dict]:
    """The toolchains of `stated` that state for the build in `root`: those of its own files and of a file in a
    folder above it (a `.tool-versions` at the checkout's root), never another build's."""
    out = []
    for item in stated or ():
        file = item.get("declared_in", "").split("#")[0]
        if inside(file, root) or inside(root, file.rpartition("/")[0]):
            out.append(item)
    return out


# What a build stops without that the project keeps out of version control: (its words, the file, the plugin that
# reads it, what the file is). Daodan makes none: the build's index is a gap that names them.
INPUTS = ((re.compile(r"File google-services\.json is missing"), "google-services.json",
           "the Google Services Gradle plugin (com.google.gms.google-services)",
           "the Firebase project's configuration, which a developer downloads from the Firebase console"),)


def missing_inputs(runs: list[dict], root: str) -> list[dict]:
    """A `build_input_missing` gap for each input of `INPUTS` a step of `runs` stopped without."""
    said = "\n".join(run.get("stderr_tail") or "" for run in runs)
    return [{"kind": "build_input_missing", "path": root or ".", "file": file,
             "detail": f"the build stopped without {file}, which {plugin} reads: {what}, kept out of the "
                       "repository; Daodan makes none, so the build gives nothing"}
            for words, file, plugin, what in INPUTS if words.search(said)]


# What a plugin a build script applies generates the build's code from: (the plugin's id, the folder it reads by
# default, the plugin, the files' suffix). A checkout without those files lacks the classes they give.
GENERATES = (("com.google.protobuf", "src/main/proto", "the protobuf Gradle plugin (com.google.protobuf)", ".proto"),)
UNRESOLVED = re.compile(r"Unresolved reference|cannot find symbol|package \S+ does not exist")  # kotlinc's, javac's


def ungenerated(folder: Path, checkout: Path, runs: list[dict]) -> str:
    """Why a build that stopped on names it does not find lacks them, when a plugin of `GENERATES` its scripts
    apply makes them from files the build folder has none of: the plugin, the folder, and the line of the folder's
    Dockerfile that copies them there; '' otherwise. Its files are read, never run."""
    if not any(UNRESOLVED.search(run.get("stderr_tail") or "") for run in runs):
        return ""
    scripts = "".join(path.read_text(encoding="utf-8", errors="replace")
                      for path in folder.glob("build.gradle*") if path.is_file())
    for plugin, sources, name, suffix in GENERATES:
        if plugin not in scripts or next(folder.rglob(f"*{suffix}"), None):
            continue
        why = f"the build applies {name}, which generates the classes its code uses from the {suffix} files of {sources}"
        copied = next((f"{path.relative_to(checkout).as_posix()}:{line} copies them there ({words})"
                       for path, line, words in _copies(folder)
                       if words.split()[-1].removeprefix("./").strip("/") == sources), "")
        return why + (f", and the checkout has none: {copied}; Daodan does not build that image for Java and Kotlin"
                      if copied else ", and the checkout has none")
    return ""


def _copies(folder: Path):
    """Each COPY and ADD of the folder's Dockerfiles: the file, the line it starts on, its words."""
    for path in sorted(folder.glob("*Dockerfile*")):
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines() if path.is_file() else []
        number = 0
        while number < len(lines):
            start, words = number, lines[number].strip()
            while words.endswith("\\") and number + 1 < len(lines):
                number += 1
                words = words[:-1].rstrip() + " " + lines[number].strip()
            number += 1
            if words.split()[:1] and words.split()[0].upper() in ("COPY", "ADD"):
                yield path, start + 1, " ".join(words.split())


def build_jdk(run: dict, stated) -> dict | None:
    """The JDK a build `{root, tool}` states, None for the image's: one `stated` above the image's (`wanted_jdk`);
    for Maven, which compiles with the JDK that runs it, else the JDK of the newest level the build's poms declare
    (`source`, `target`, `java.version`; Temurin's oldest, 8, for one below, which `stated` keeps) when it is
    below the image's: a
    compiler plugin of the pom's time may not read a newer JDK's classes (Error Prone's own javac 9). Not for a pom
    that declares a `release`, which javac 9 or later compiles for it; not for Gradle, which runs on the image's
    JDK and finds the toolchain its scripts ask for."""
    stated = [item for item in applying(for_tool(stated, run["tool"]), run["root"]) if item.get("tool") == "java"]
    above = wanted_jdk(stated)
    if above or run["tool"] != "maven":
        return above
    poms = [item for item in stated if item.get("declared_in", "").split("#")[0].rsplit("/", 1)[-1] == "pom.xml"
            and inside(item["declared_in"].split("#")[0], run["root"])]
    if not poms or any(item["declared_in"].endswith("release") for item in poms):
        return None
    newest = max(poms, key=lambda item: _major(item["version"]) or 0)
    level = _major(newest["version"]) or JDK
    return {**newest, "version": str(max(level, 8)), "stated": newest["version"]} if level < JDK else None


def raise_line(toolchains, root: str, under: int, what: str) -> str:
    """Before a preparation's body: `DAODAN_RAISE=what`, exported, when a Gradle script of the build in `root`
    states a Java under `under`; else nothing."""
    low = any(item.get("tool") == "java" and ".gradle" in item.get("declared_in", "")
              and inside(item["declared_in"].split("#")[0], root) and (_major(item.get("version")) or under) < under
              for item in toolchains or ())
    return f"export DAODAN_RAISE={what}\n" if low else ""


def edited(runs: list[dict], root: str, declared: str = "gave no index",
           this: str = "this index is a second build's") -> list[dict]:
    """A result of a build the preparation edited: the `build_edited` gap, with what was removed from the root pom
    (`plain-javac`), each level or toolchain raised (`RAISE_LEVELS`, the pom's levels), and the errors of the build
    as declared when it ran, which `declared`; `this` names what the edited build gave."""
    removed = next((run["patched_pom_removed"] for run in runs if run.get("patched_pom_removed")), None)
    raised = list(dict.fromkeys(item for run in runs for item in run.get("build_raised", ())))
    if not removed and not raised:
        return []
    first = next((run for run in runs if run.get("returncode")), {})
    lines = (first.get("stderr_tail") or "").splitlines()
    # Maven marks its errors; Gradle says what went wrong under that heading, else its last words.
    start = next((at for at, line in enumerate(lines) if "ERROR" in line or "What went wrong" in line), None)
    last = [line.strip() for line in lines if line.strip()][-3:]
    said = (" / ".join(line.strip() for line in lines[start:start + 6] if line.strip()) if start is not None
            else " / ".join(last) or f"exit code {first.get('returncode')}") if first else ""
    how = ["of the root pom without its compiler plugin's "
           f"{'; '.join(' '.join(item.split()) for item in removed)[:600]}, compiled by the JDK's own javac"
           ] if removed else []
    if raised:
        how.append(f"with {'; '.join(raised)[:600]}")
    return [{"kind": "build_edited", "path": root or ".", "detail":
             f"the build as declared {declared}{f' ({said[:600]})' if said else ''}: {this}, " + ", and ".join(how)}]


def restore_lines(project_dir: Path) -> str:
    """The preparation's restore of Gradle's and Maven's dependencies, per build folder (`preparation.restores`)."""
    marks = {mark for manager in ("gradle", "maven") for mark in preparation.RESTORES[manager]["marks"]}
    skipped = {"build", "target", "node_modules"}
    files = [path.relative_to(project_dir).as_posix() for path in Path(project_dir).rglob("*")
             if path.name in marks and path.is_file()
             and not any(part.startswith(".") or part in skipped for part in path.relative_to(project_dir).parts[:-1])]
    return "".join(preparation.restore(manager, folders) + "\n"
                   for manager, folders in preparation.restores(files).items() if manager in ("gradle", "maven"))


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


def maven_jars(folder: str, pinned) -> dict[str, Path]:
    """The container path under `folder` and the host file of each `(coordinate, sha256)` of Maven Central,
    downloaded once into the shared directory and verified (`fetched`)."""
    from resolve_edges import MAVEN_CENTRAL, maven_central_dir
    jars = {}
    for coordinate, digest in pinned:
        group, artifact, version = coordinate.split(":")
        relative = f"{group.replace('.', '/')}/{artifact}/{version}/{artifact}-{version}.jar"
        jars[f"{folder}/{artifact}-{version}.jar"] = fetched(f"{MAVEN_CENTRAL}/{relative}",
                                                             maven_central_dir() / relative, digest)
    return jars


def tools(project_dir: Path) -> dict[str, Path]:
    """The container paths and host files of the JDK, scip-java's classpath and the build tools the project asks for,
    downloaded once into the shared directory; a Gap when a wrapper names another site or a file cannot be
    verified."""
    import container
    from resolve_edges import shared_engine_dir
    jdk = preparation.JDK_IN
    inputs = {jdk: preparation.fetched(*preparation.TEMURIN, jdk.rsplit("/", 1)[1])}  # where the pre-map's is
    inputs.update(maven_jars(LIB, CLASSPATH))
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


def _newer(text: str, used: int = JDK, has=None) -> tuple[int, str, str | None] | None:
    """The newest JDK a failed build's output asks for that the run's was not, with the words that ask for it and
    the vendor they name (None for none): one above `used`, or `used` itself of a vendor other than `has`, the
    vendor of the JDK the run had (None: the image's, Temurin). None when it asks for no such JDK."""
    found = [(int(match.group(1)), match.group(), preparation.asked_vendor(match.groupdict().get("vendor")))
             for pattern in NEWER for match in pattern.finditer(text)]
    found += [(int(match.group(1)) - 44, match.group(), None) for match in CLASS_FILE.finditer(text)]
    found = [item for item in found if item[0] > used or (
        item[0] == used and item[2] and preparation.vendor_key(item[2]) != preparation.vendor_key(has))]
    return max(found, key=lambda item: (item[0], bool(item[2]))) if found else None


def _jdk(major: int, vendor=None) -> str:
    """A JDK as a message names it: `JDK 17`, `JetBrains JDK 17` when its vendor is asked."""
    return f"{preparation.vendor_label(vendor)} JDK {major}" if vendor else f"JDK {major}"


def _tried(tried: dict, left: bool) -> str:
    """What became of the JDK a second run was made for (`tried`, as `preparation.jdk_named` gave it): the build ran on
    it, or `left` it did not install, whatever its major or vendor, and the image's ran."""
    kind = _jdk(_major(tried["version"]), tried.get("vendor"))
    if not left:
        return f"the build ran again on {kind}, which its first error asked for"
    return f"{kind}, which its first error asked for, did not install, so the build ran on the image's JDK {JDK}"


def judged(result: dict, text: str, used: int = JDK, tried: dict | None = None, has=None, left: bool = False) -> dict:
    """A failed preparation that asks for a JDK above the one it ran with (`used`, of the vendor `has`), or for its
    major of another vendor, is a gap. `tried` is the JDK of a second run, the one the first run's error named, and
    `left` whether it did not install: the gap says what became of it."""
    found = _newer(text, used, has) if result["state"] not in ("done", "gap") else None
    if found is None:
        return result
    asked = _jdk(found[0], found[2])
    held = f"Daodan's image holds JDK {JDK} only" if used == JDK else f"the preparation installed JDK {used}"
    remedy = (f"declare {asked} where the pre-map reads it (the build's toolchain or release), so the "
              "preparation installs it")
    if tried:
        held = _tried(tried, left)
        if left:
            remedy = (f"{_jdk(_major(tried['version']), tried.get('vendor'))} could not be installed by the "
                      "preparation: its toolchain gap says why")
    return {**result, "state": "gap", "cause": f"the build asks for {asked}; {held}", "remedy": remedy}


def _errors(line: str) -> str | None:
    # As `code_graph.measured`: an indexer's own errors.
    return line[line.find(" ERROR ") + 7:][:200] if " ERROR " in line else None


def steps(text: str, phase: str) -> list[dict]:
    """The runs a phase log records: one per step, with its exit code, seconds, output tail and `ERROR` lines;
    `peak_mb` is the container's memory peak over the phase. A step cut off (time limit) has no exit code."""
    runs, current, tail, errors, peak, patched = [], None, collections.deque(maxlen=80), [], None, None
    raised = []

    def close(code, ended):
        output = "\n".join(tail)
        run = {"step": current[0], "phase": phase, "returncode": code,
               "seconds": round(ended - current[1], 1) if ended is not None else None, "peak_mb": None,
               "stderr_tail": output[-2500:], "stderr_errors": len(errors),
               "stderr_error_examples": list(dict.fromkeys(errors))[:5]}
        if patched is not None and current[0] == "plain-javac":
            run["patched_pom_removed"] = patched
        if raised:
            run["build_raised"] = list(dict.fromkeys(raised))
        runs.append(run)

    for line in text.splitlines():
        if line.startswith("DAODAN_STEP "):
            words = line.split()
            if words[1] == "begin":
                current, tail, errors, patched = (words[2], float(words[3])), collections.deque(maxlen=80), [], None
                raised = []
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
            if "DAODAN_RAISED " in line:  # Gradle may print it after words of its own
                import json
                raised.append(json.loads(line.split("DAODAN_RAISED ", 1)[1]))
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
    """No index: the cause the run gives, why where `run` knows it (`ungenerated`), with the output tail of its
    last step."""
    last = runs[-1] if runs else {}
    tail = (last.get("stderr_tail") or "").strip()[-800:]
    cause = result.get("cause") or f"exit code {last.get('returncode')}"
    why = f"{result['why']}. The build said: " if result.get("why") else ""
    return {"indexes": [], "runs": runs, "indexer": code_graph.indexer("scip-java", VERSION, runs),
            "state": "failed", "reason": f"scip-java wrote no index ({cause}): {why}{tail}",
            "errors": sum(run.get("stderr_errors") or 0 for run in runs)}


def run(project_dir: Path, work_dir: Path, prepare: str, execute: str, *, memory: int, engine=None,
        toolchains=(), prepare_timeout: float = 1800, timeout: float = 600,
        inputs: dict[str, Path] | Callable[[], dict[str, Path]] | None = None, jdk: dict | None = None, hosts=(),
        checkout: Path | None = None, tried: dict | None = None) -> tuple[dict, list[dict], Path]:
    """Both phases in one container run over a copy of `checkout` (`project_dir`'s when not given: a build reads
    what lies outside its folder as it does in a checkout) and the `tools` it needs, the steps in the build's
    folder `project_dir`; the preparation's steps before `prepare` (the JDK it runs on, `jdk` or the newest of
    `toolchains` above the image's, and each other JDK a Gradle toolchain of `toolchains` asks for, of those that
    state for that folder, `applying`; the restore), reaching beside the registries the `hosts` the project
    declares (`preparation.declared`): the operation's result (`judged`, with the preparation's `gaps` and the
    inputs a build stopped without, `missing_inputs`), the runs of both logs, and the folder the outputs came
    back into. A build whose output asks for a JDK above the one it ran on, or the same one of another vendor
    (Gradle's words, else `_newer`) runs once more on it, installed as the preparation installs the pre-map's
    (`preparation.jdk_named`); that second run, `tried` the JDK it is on, is never followed by a third."""
    import container
    out_dir = Path(work_dir) / "container"
    out = out_dir / Path(OUT).name
    shutil.rmtree(out, ignore_errors=True)
    for phase in ("prepare", "execute"):
        (out_dir / f"{phase}.log").unlink(missing_ok=True)
    checkout = Path(checkout or project_dir)
    root = Path(project_dir).relative_to(checkout).as_posix().removeprefix(".")
    toolchains = applying(toolchains, root)
    jdk = jdk or wanted_jdk(toolchains)
    # Each other JDK a Gradle toolchain asks for is installed beside it, for Gradle to find (`HEAD`).
    others, runs_on = {}, _major(jdk["version"]) if jdk else JDK
    for item in toolchains:
        major = _major(item.get("version")) if item.get("tool") == "java" else None
        # A level under 8 names no JDK to find: none is built, and the image's compiles it raised.
        if major and major >= 8 and ".gradle" in item.get("declared_in", "") and major not in (JDK, runs_on):
            others.setdefault(major, {**item, "version": str(major)})
    parts = [preparation.toolchains([item]) for item in [*([jdk] if jdk else []), *others.values()]]
    chains = {"files": list(dict.fromkeys(file for part in parts for file in part["files"])),
              "lines": [line for part in parts for line in part["lines"]],
              "hosts": tuple(dict.fromkeys(host for part in parts for host in part["hosts"])),
              "gaps": [gap for part in parts for gap in part["gaps"]]}
    sdk = preparation.android(toolchains)
    setup = "".join(f"{line}\n" for line in ([f"mkdir -p {preparation.T}/bin"] if parts else []) + chains["lines"]
                    + sdk["lines"])
    used = _major(jdk["version"]) if jdk else JDK

    inputs_given = inputs

    def inputs(extra=inputs) -> dict:
        given = tools(project_dir)
        given.update({f"{preparation.IN}/{name}": preparation.fetched(url, digest, name)
                      for url, digest, name in chains["files"] + sdk["files"]})
        given.update((extra() if callable(extra) else extra) or {})  # a function: downloaded once an engine answers
        return given

    result = container.run_in_container(
        checkout, ["bash", "-c", script("execute", execute, jdk=used, root=root)], image=IMAGE, out_dir=out_dir,
        prepare=["bash", "-c", script("prepare", restore_lines(project_dir) + prepare, setup=setup, jdk=used,
                                      root=root)],
        outputs=[OUT], env=dict(ENV), timeout=timeout, prepare_timeout=prepare_timeout, memory=memory, pids=PIDS,
        registries=tuple(dict.fromkeys(registries(project_dir) + chains["hosts"] + sdk["hosts"] + tuple(hosts))),
        engine=engine, inputs=inputs)
    runs, prepared = [], ""
    for phase in ("prepare", "execute"):
        log = out_dir / f"{phase}.log"
        if log.is_file():
            text = log.read_text(encoding="utf-8", errors="replace")
            prepared = text if phase == "prepare" else prepared
            runs += steps(text, phase)
    missing = preparation.missing(prepared)
    # The JDK that was to run the build did not install (mise failed, or has none of the vendor): the head took
    # the image's.
    left =bool(jdk) and any(gap["tool"] == "java" and gap["version"] in (jdk["version"], preparation.mise_version(jdk))
                             for gap in [*missing, *chains["gaps"]])
    used = JDK if left else used
    has = None if left or not jdk else jdk.get("vendor")  # the vendor of the JDK the build ran on
    gaps = (chains["gaps"] + sdk["gaps"] + missing + preparation.restore_gaps(prepared)
            + list(result.get("gaps") or ())  # and what the copy left out (`container.copy_perimeter`)
            + missing_inputs(runs, root))
    # A build that needs a newer JVM than it ran on, or the same one of another vendor, runs once more on the JDK it
    # names: Gradle's words first (`gradle.asked_jdk`), else any other error of a failed build (`_newer`). One the
    # first run already tried to install is not run again.
    from premap import gradle
    asked = None
    if tried is None and result.get("state") != "gap":
        asked = gradle.asked_jdk(prepared, toolchains)
        found = _newer(prepared, used, has) if asked is None and result["state"] != "done" else None
        asked = preparation.jdk_named(found[0], found[1], toolchains, vendor=found[2]) if found else asked
    kind = lambda item: (_major(item["version"]) or 0, preparation.vendor_key(item.get("vendor")))  # noqa: E731
    again_on = kind(asked[0]) if asked else None
    if asked and again_on[0] >= used and again_on != (used, preparation.vendor_key(has)) and again_on != (
            kind(jdk) if jdk else None):
        again, more, out = run(project_dir, work_dir, prepare, execute, memory=memory, engine=engine,
                               toolchains=toolchains, prepare_timeout=prepare_timeout, timeout=timeout,
                               inputs=inputs_given, jdk=asked[0], hosts=hosts, checkout=checkout, tried=asked[0])
        said = [{**asked[1], "path": root or "."}] if asked[1] else []
        return {**again, "gaps": [*said, *again.get("gaps", ())]}, runs + more, out
    why = ungenerated(Path(project_dir), checkout, runs)
    ended = judged(result, prepared, used, tried, has, left)
    if tried and ended["state"] not in ("done", "gap"):  # the second run, on the JDK the first error named, failed
        why = _tried(tried, left) + (f"; {why}" if why else "")
    return {**ended, **({"gaps": gaps} if gaps else {}), **({"why": why} if why else {})}, runs, out


def with_gaps(part: dict, result: dict) -> dict:
    """A build's contract with the preparation's gaps of its run beside its own."""
    gaps = [*part.get("gaps", ()), *result.get("gaps", ())]
    return {**part, "gaps": gaps} if gaps else part


BUILDS = ({"gradle-project"}, {"maven-module"})  # a Gradle build and a Maven reactor build the modules inside them
BUILD_KINDS = frozenset().union(*BUILDS)
BUILD_TOOLS = ("gradle", "maven")  # the build tool of each of `BUILDS`, in its order


def build_tools(record: dict) -> dict[str, list[str]]:
    """The folder of each build to run, as the pre-map names it, with the tools that build it: per build tool,
    the outermost unit, '' for the project's root. A module inside one is built by it."""
    import premap
    found = {}
    for kinds, tool in zip(BUILDS, BUILD_TOOLS):
        roots = premap.roots(record, kinds)
        for root in sorted(roots):
            if not any(other != root and (other == "" or root.startswith(f"{other}/")) for other in roots):
                found.setdefault(root, []).append(tool)
    return found


def build_roots(record: dict) -> set[str]:
    """The folders of `build_tools`."""
    return set(build_tools(record))


OTHER_BUILDS = frozenset({"sbt-project", "bazel-target", "bazel-module"})  # JVM builds Daodan does not run


def other_builds(record: dict) -> list[str]:
    """The unit kinds of the pre-map that build JVM code another way: what `combined` names when nothing ran."""
    return sorted({unit["kind"] for unit in record.get("units", [])} & OTHER_BUILDS)


def modules(record: dict) -> list[list]:
    """Each Maven module of the pre-map, '' the project's root, with the source folders Maven's model gives it."""
    return sorted(["" if unit["root"] == "." else unit["root"], list(unit.get("source_roots") or [])]
                  for unit in record.get("units", []) if unit["kind"] == "maven-module")


def modules_line(modules, root: str) -> str:
    """The script line that hands `MAVEN_KOTLIN` the modules of the build in `root` ('' the project's), their
    folders relative to the build's."""
    import posixpath
    import shlex
    inside = [(module, folders) for module, folders in modules
              if not root or module == root or module.startswith(f"{root}/")]
    rows = "\n".join(f"{posixpath.relpath(module or '.', root or '.')}\t"
                     + ":".join(posixpath.relpath(folder, root or ".") for folder in folders)
                     for module, folders in inside)
    return f"DAODAN_MODULES={shlex.quote(rows)}\n"


def build_root(project_dir: Path, folder: Path) -> str:
    """The build folder as the pre-map names it: relative to the checkout, '' for the project's root."""
    root = Path(folder).relative_to(project_dir).as_posix()
    return "" if root == "." else root


def tool_line(tool: str | None) -> str:
    """The script line naming the build tool scip-java runs (`--build-tool`); empty, scip-java finds it."""
    return f"DAODAN_TOOL={tool or ''}\n"


def builds(project_dir: Path, work_dir: Path, roots, one, tools=None) -> list[tuple[str, dict]]:
    """`one(folder, work, tool)` for each build folder, each in a work folder of its own (`build-N`), in order,
    with each tool `tools` (`build_tools`) names for it. Two tools build the same files of a folder, and a second
    index of a file would repeat its occurrences: the next tool builds only when the one before gave no index."""
    out, number = [], 0
    for root in sorted(roots):
        for tool in (tools or {}).get(root) or [None]:
            work = Path(work_dir) / f"build-{number}"
            work.mkdir(parents=True, exist_ok=True)
            number += 1
            part = one(Path(project_dir) / root if root else Path(project_dir), work, tool)
            out.append((root, {**part, **({"tool": tool} if tool else {})}))
            if part.get("indexes"):
                break
    return out


def combined(parts: list[tuple[str, dict]], others=(), **joined) -> dict:
    """One contract from one per build: each index named from the checkout by its build's folder, every run
    with its `build`, each build's state; without any index, the first build's failure (or `unavailable`,
    naming the builds of `others`, the pre-map's kinds Daodan does not run)."""
    if not parts and others:
        tools = ", ".join(sorted({kind.split("-")[0] for kind in others}))
        return unavailable(f"built with {tools}: Daodan builds Java and Kotlin only with Gradle and Maven",
                           "none yet: these files have no graph")
    if not parts:
        return unavailable("no Gradle or Maven build in the pre-map: nothing builds these files",
                           "declare the build of the project (settings.gradle, build.gradle or pom.xml)")
    runs, indexes, states = [], [], []
    gaps = [gap for _root, part in parts for gap in part.get("gaps", ())]
    joined = {**joined, **({"gaps": gaps} if gaps else {})}
    for root, part in parts:
        runs += [{**run, "build": root} for run in part.get("runs", [])]
        indexes += [[path, "/".join(name for name in (root, prefix) if name)] for path, prefix in part["indexes"]]
        states.append({"root": root, **({"tool": part["tool"]} if part.get("tool") else {}),
                       "state": part.get("state", "done"), **({"reason": part["reason"]} if part.get("state") else {})})
    if not indexes:
        first = next((part for _root, part in parts if part.get("state") == "failed"), parts[0][1])
        return {**first, "runs": runs, "builds": states, **({"gaps": gaps} if gaps else {})}
    return {"indexes": indexes, "runs": runs, "indexer": code_graph.indexer("scip-java", VERSION, runs),
            "builds": states, **joined}


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
