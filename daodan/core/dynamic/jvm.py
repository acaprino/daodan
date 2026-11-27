"""The JVM observer: the tests of a Gradle or Maven build of Java and Kotlin under an exact recorder, a Java agent.

The recorder. The rule: every call, with its caller, its callee and the call site's line, in the test JVMs that
Gradle's Test task and Surefire fork, on Kotlin's bytecode too. Compared from their own documentation and source
(November 2026), no existing recorder meets it:

- java-callgraph's javacg-dynamic (BSD-2-Clause): Javassist probes at method entry and exit, method pairs printed
  at JVM exit; no call-site line, "will not work reliably (or at all) for multithreaded programs", and no release
  (0.1-SNAPSHOT, built from source).
- BTrace (Apache-2.0): `Kind.CALL` gives the probed method and the name the call instruction declares; no line,
  and not the method that ran (no dispatch, lambda or reflection target).
- Byteman (LGPL-2.1): a rule names its class or interface and, `AT INVOKE`, the called method; no pattern for
  every class, and the declared callee only.
- ByteBuddy (Apache-2.0) is a library to write an agent with; the agents built on it (OpenTelemetry's, Elastic's,
  Glowroot) record chosen library methods as spans, not every call.
- JFR: `jdk.ExecutionSample` samples, so it loses short calls (a declared second source at most, provenance
  `sampled`); `jdk.MethodTrace` (JDK 25, JEP 520) records each call of the methods its filter names, by method
  or class, with the stack, but only in a test JVM of JDK 25 or later, and the JEP sets no overhead bound for it.

So the recorder is Daodan's own, `jvm_record/`: `Agent.java` rewrites every class loaded from the project's copy
as it loads (`java.lang.instrument`, part of the JDK) and `Recorder.java` is what the rewritten code calls. It
rewrites with ASM (`ASM`, BSD-3-Clause, one jar from Maven Central pinned by sha256): the JDK's own class-file
API exists only from JDK 24 and the image holds JDK 17. The sources are compiled in the container's preparation
by the image's JDK (`agent_commands`, class files of Java `RELEASE`, so a test JVM from 8 on loads them), so no
binary of Daodan's is carried; Daodan carries the sources and the jar (`observe`).

The agent is attached without changing the project: every JVM reads JAVA_TOOL_OPTIONS when it starts, Gradle's
Test task forks its test JVMs with the build's environment ("Defaults to the environment of this process"), and
Surefire with Maven's ("inherited from the Maven process to the forked Surefire processes"; with `forkCount` 0
the tests run in Maven's own JVM, which reads it too). So the agent also starts in the build's own JVMs (Gradle,
the Kotlin daemon, Maven), where it rewrites only classes loaded from the copy: build logic of the project that
runs there (buildSrc, an annotation processor of its own) is observed as well. A build that clears its test JVMs'
environment (Gradle's `environment`, Surefire's `excludedEnvironmentVariables`) runs them without the agent: the
`not_observed` gap.

`plan` reads the pre-map: each outermost Gradle or Maven build (`indexers/jvm.py` `build_tools`) that holds a test
file (one that imports JUnit, TestNG, kotlin.test, Kotest or Spock) runs its build's own tests: Maven's `test`
phase, Surefire's where the packaging binds it; under Gradle, in each project, its `test` task, else (Kotlin
Multiplatform, which has none) each task of type Test it has (`jvmTest`), as Gradle names them once it has
configured the build. A folder Gradle and Maven both build runs the same tests under each: Maven's run only when
Gradle's did not. `observe` is one container run per build, `indexers/jvm.py` `run`: its image, build tools and
restore, on the JDK `jvm.build_jdk` names. The preparation, with the registries: the agent is built, the tests are
compiled and their
classpath resolved. Under Gradle that is `jvm_record/tests.gradle`, an init script that writes the paths of the
Test tasks to run: their runtime-only dependencies (a JUnit engine, a JDBC driver) are not on the compile
classpath, and offline Gradle downloads nothing. Under Maven, `test-compile` resolves the test scope, and
Surefire resolves its test provider, which it does only when it starts the tests (`dependency:go-offline` does
not fetch it): it is given a `java` that exits at once (`NO_JVM`), so no test runs there unless the build sets
`forkCount` 0. A build that does not compile is `failed`, with its output tail. The execution, with no network:
the tests, offline, under the agent, stopped after `LIMIT` seconds; each fact is on disk as soon as it is seen.
Back come the recorder's files (one per JVM), the build's log and its JUnit XML reports' counts.

What a site is: a call instruction (`invokevirtual`, `invokespecial`, `invokestatic`, `invokeinterface`) with
the line its class file gives it and the method it names. The JVM has no column: `place` puts a site on the call
of the snapshot's parse of its file that has its line and name (a constructor's is its class's, a Kotlin getter's
or setter's its property's, Kotlin's `name$default` is `name`), as `code_graph.Snapshot.callee` places a
reference. Two calls of the same name on one line are ambiguous: the site is not placed and the `sites_ambiguous`
gap says how many. A call the source
does not write (a constructor's `super()`, string concatenation, boxing, an operator) has no call there and is
counted, never placed. A callee is the declaration of the snapshot's parse whose name it has and which holds its
first line; a lambda or a getter without one is a project callable the snapshot does not declare. A call that
entered none of the project's methods is an external end named by the class it declares; on a project type it
ran in code from outside the copy (a mock, a proxy, an inherited library method) and is no destination (`mock`).
"""
from __future__ import annotations

import collections
import json
import posixpath
import re
import shlex
from pathlib import Path

import dynamic
import preparation
from indexers import jvm

# The observer this module is (`dynamic.observers`): its entry, its recorder's version, the languages it observes.
NAME, VERSION, LANGUAGES = "dynamic-record-jvm", "1", ("java", "kotlin")
ASM = ("org.ow2.asm:asm:9.11.1", "ae4e6e10d59d0a1500317764b21881ad883f8550e33c66e6142f7032c6fb566c")
RECORD = Path(__file__).resolve().parent / "jvm_record"
AGENT = f"{preparation.IN}/dynamic-jvm"  # the agent's sources and ASM, and the jars built from them, in the container
RELEASE = 8  # the agent's class files, for test JVMs from 8 on; its JDK 9 and 10 parts are of their JDK
IMAGE_JDK = f"{preparation.JDK_HOME}/bin/"  # Temurin's JDK (`UNPACK_JDK`), which builds the agent whatever JDK runs the build
SYNTHETIC, BRIDGE = 0x1000, 0x40
GRADLE_TEST = ["gradle", "--no-daemon", "--offline", "--continue", "--console=plain"]  # + the preparation's tasks
MAVEN_TEST = ["mvn", "-B", "-o", "-fae", "-Dmaven.test.failure.ignore=true", "test"]
TASKS = "$OUT/test-tasks.txt"  # the Test tasks the preparation's Gradle names, one path per line
COMPILE = {"gradle": f'env DAODAN_TESTS="{TASKS}" gradle --no-daemon --console=plain --init-script '
                     f"{AGENT}/tests.gradle daodanTests",
           "maven": "mvn -B test-compile"}
NO_JVM = "/tmp/daodan-no-jvm"
TESTS = re.compile(r"^\s*import\s+(?:static\s+)?(?:org\.junit|junit\.framework|org\.testng|kotlin\.test|io\.kotest"
                   r"|org\.spockframework|spock\.lang)\b", re.M)
SOURCES = (".java", ".kt")
MEMORY = 4 * 2**30
LIMIT = 3600  # the seconds one build's tests may take
JDK_PACKAGES = ("java.", "javax.", "jdk.", "sun.", "com.sun.")
PACKAGE = re.compile(r"^\s*package\s+([\w.]+)", re.M)
SUITE = re.compile(r'\b(tests|failures|errors|skipped)="(\d+)"')
EXAMPLES = 20
NO_CALL = "no call of that name on its line"


def agent_commands(source: str, into: str, separator: str = ":", bin: str = "") -> list[list[str]]:
    """The commands that build the agent from the sources in `source` into `into`, where `asm.jar` already is, with
    the JDK in `bin`: `record.jar` for the bootstrap class path, `agent.jar` with the manifest that names both. Of
    Java `RELEASE`, but `Walker` (StackWalker's frame descriptors, JDK 10) and `Modular` (modules, JDK 9), which
    the agent loads only on their JDK."""
    def javac(release: int, *args: str) -> list[str]:
        return [f"{bin}javac", "--release", str(release), "-nowarn", *args]

    record, agent, asm = f"{into}/record", f"{into}/agent", f"{into}/asm.jar"
    return [javac(RELEASE, "-d", record, f"{source}/Recorder.java"),
            javac(10, "-classpath", record, "-d", record, f"{source}/Walker.java"),
            [f"{bin}jar", "--create", "--file", f"{into}/record.jar", "-C", record, "."],
            javac(RELEASE, "-classpath", f"{asm}{separator}{record}", "-d", agent, f"{source}/Agent.java"),
            javac(9, "-classpath", separator.join((asm, record, agent)), "-d", agent, f"{source}/Modular.java"),
            [f"{bin}jar", "--create", "--file", f"{into}/agent.jar", "--manifest", f"{source}/MANIFEST.MF",
             "-C", agent, "."]]


def external(callee: dict) -> dict:
    """The package of a callee outside the project: the class's package, of the JDK or of a library; the run does
    not see the library's coordinates."""
    module = callee.get("module") or ""
    return {"manager": "jdk" if module.startswith(JDK_PACKAGES) else "maven",
            "package": module.rpartition(".")[0] or module, "version": None}


def plan(record: dict, files: list[str], read) -> dict:
    """`{runs, gaps, sources, toolchains}` from the pre-map `record` and the snapshot's `files`: a run is `{root,
    tool, argv}`, a build without a test file a `no_tests` gap; `sources` are the Java and Kotlin files `place`
    reads and `toolchains` the JDKs the pre-map states."""
    common = {"sources": sorted(rel for rel in files if rel.endswith(SOURCES)), "toolchains": jvm.toolchains(record)}
    builds = jvm.build_tools(record)
    if not builds:
        others = ", ".join(sorted({kind.split("-")[0] for kind in jvm.other_builds(record)}))
        detail = (f"built with {others}: Daodan runs the tests of Gradle and Maven builds only" if others else
                  "the pre-map names no Gradle or Maven build: no `test` to run")
        return {"runs": [], "gaps": [{"kind": "no_tests", "detail": detail}], **common}
    runs, gaps = [], []
    for root, tools in sorted(builds.items()):
        for tool in tools:
            if any(jvm.inside(rel, root) and rel.endswith((*SOURCES, ".groovy")) and TESTS.search(read(rel) or "")
                   for rel in files):
                runs.append({"root": root, "tool": tool, "argv": GRADLE_TEST if tool == "gradle" else MAVEN_TEST})
            else:
                gaps.append({"kind": "no_tests", "path": root, "detail": f"the {tool} build in {root or '.'} holds no "
                             "test file (none imports JUnit, TestNG, kotlin.test, Kotest or Spock): no test runs"})
    return {"runs": runs, "gaps": gaps, **common}


def scripts(run: dict) -> tuple[str, str]:
    """The preparation's body and the execution's, each after `indexers/jvm.py`'s head (`jvm.script`)."""
    build = " && ".join(shlex.join(command) for command in agent_commands(AGENT, AGENT, bin=IMAGE_JDK))
    # The build compiles as declared; a Gradle one that fails and states a level under 8, which the image's JDK
    # does not compile, compiles once more with the levels raised (`jvm.RAISE_LEVELS`), a declared second attempt.
    compile = f"step compile {COMPILE[run['tool']]}"
    again = (f' || {{ code=$?; [ -n "${{DAODAN_RAISE:-}}" ] || exit $code; raise_levels; {compile}; }}'
             if run["tool"] == "gradle" else "")
    prepare = [f"step agent sh -c {shlex.quote(build)} || exit 70", f"{{ {compile}{again}; }} || exit $?"]
    if run["tool"] == "maven":
        prepare += [f"mkdir -p {NO_JVM}/bin && printf '#!/bin/sh\\nexit 0\\n' > {NO_JVM}/bin/java"
                    f" && chmod +x {NO_JVM}/bin/java", f'cp "$JAVA_HOME/release" {NO_JVM}/ 2>/dev/null',
                    f"step providers mvn -B -fae test -Dmaven.test.failure.ignore=true -DforkCount=1"
                    f" -Djvm={NO_JVM}/bin/java"]
    tests = f"timeout -k 30 {LIMIT} {shlex.join(run['argv'])}"
    tests = [f"{tests} > $OUT/tests.log 2>&1", "echo $? > $OUT/tests.code"] if run["tool"] == "maven" else [
        f'if [ -s "{TASKS}" ]; then', f'  {tests} $(sort -u "{TASKS}") > $OUT/tests.log 2>&1',
        "  echo $? > $OUT/tests.code", "else",
        "  echo 'the build has no Test task' > $OUT/tests.log && echo 0 > $OUT/tests.code", "fi"]
    execute = ["for tool in /daodan/state/tools/*/*/bin/gradle /daodan/state/tools/*/*/bin/mvn; do",
               '  [ -f "$tool" ] && PATH="${tool%/*}:$PATH"', "done", "export PATH",
               f'JAVA_TOOL_OPTIONS="$JAVA_TOOL_OPTIONS -javaagent:{AGENT}/agent.jar=out=$OUT/calls,root=$WORK"',
               "export JAVA_TOOL_OPTIONS", "touch $OUT/tests.start", *tests,
               "find \"$WORK\" -name 'TEST-*.xml' -newer $OUT/tests.start"
               " -exec grep -h -m1 -o '<testsuite [^>]*>' {} + > $OUT/suites.txt"]
    return "\n".join([*prepare, "exit 0"]) + "\n", "\n".join([*execute, "exit 0"]) + "\n"


def smap(text: str | None) -> list[tuple[int, int, int, int, str, str]]:
    """The first stratum of a class's SourceDebugExtension (JSR-45): `(first output line, input lines, output
    lines per input line, first input line, source file, class path)` per entry. Kotlin writes one for a class
    that holds inlined bodies: their lines lie past the file's end and map back to where the body is written."""
    files, entries, section, pending, last = {}, [], None, None, None
    for line in (text or "").splitlines():
        if line.startswith("*"):
            if line[:2] in ("*S", "*E") and entries:
                break
            section = line[:2]
        elif section == "*F":
            if pending is not None:
                files[pending[0]], pending = (pending[1], line), None
            elif line.startswith("+ "):
                pending = line[2:].split(" ", 1)
            else:
                number, name = line.split(" ", 1)
                files[number] = (name, name)
        elif section == "*L":
            given, _, output = line.partition(":")
            given, _, repeat = given.partition(",")
            start, _, file = given.partition("#")
            first, _, step = output.partition(",")
            last = file or last
            if last in files:
                entries.append((int(first), int(repeat or 1), int(step or 1), int(start), *files[last]))
    return entries


def _where(row: dict):
    """`line -> (package, source file, line)` for the lines of one class of the recorder's file."""
    entries, package = smap(row.get("smap")), row["class"].rpartition("/")[0]

    def where(line: int) -> tuple[str, str, int]:
        for first, repeat, step, start, source, path in entries:
            if first <= line < first + repeat * step:
                return path.rpartition("/")[0], source, start + (line - first) // step
        return package, row["source"], line

    return where


def read(folder: Path) -> dict:
    """What the recorder's files in `folder` say, one file per JVM: `sites`, each call site that ran, with the
    class and method holding it, the `package`, `source` file and `line` it is written at (through the class's
    `smap`), the `owner`, `name` and `desc` it names, the project methods it reached (`callees`, each with its
    class, name, descriptor, source place and whether it is a `lambda` body) and whether it also ran `outside`
    the project's classes; `classes`, the classes rewritten; `skipped`, the classes the agent could not rewrite,
    with the reason; `jvms`, the files read.

    A synthetic method is the compiler's, not the source's: a site that reaches one (a bridge, Kotlin's
    `name$default`, an accessor) gets what that method's own call of the same name reached. A lambda's body is
    synthetic too and is a callee itself.
    """
    merged, skipped, classes, jvms = {}, {}, set(), 0
    for path in sorted(Path(folder).glob("*.jsonl")):
        methods, inside, places, calls, outside = {}, collections.defaultdict(list), {}, \
            collections.defaultdict(set), set()
        jvms += 1
        for text in path.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                row = json.loads(text)
            except ValueError:
                continue  # the line a JVM was writing when it was killed
            if "class" in row:
                where = _where(row)
                classes.add(row["class"])
                for identity, name, desc, access, line in row["methods"]:
                    package, source, mapped = where(line)
                    body = bool(access & SYNTHETIC) and "lambda$" in name
                    methods[identity] = {
                        "class": row["class"], "name": name, "desc": desc, "package": package, "source": source,
                        "line": mapped, "from": row["from"], "lambda": body,
                        "forwards": bool(access & (SYNTHETIC | BRIDGE)) and not body}
                for identity, method, line, owner, name, desc in row["sites"]:
                    places[identity] = (method, where(line), owner, name, desc)
                    inside[method].append(identity)
            elif "call" in row:
                calls[row["call"][0]].add(row["call"][1])
            elif "outside" in row:
                outside.add(row["outside"])
            elif "skipped" in row:
                skipped[row["skipped"]] = row["why"]

        def ends(site: int, seen: frozenset) -> tuple[list[int], bool]:
            found, out = [], site in outside
            for method in sorted(calls.get(site, ())):
                if not methods[method]["forwards"] or method in seen:
                    found.append(method)
                    continue
                for inner in _forwarded(methods[method]["name"], [(i, places[i][3]) for i in inside[method]]):
                    more, left = ends(inner, seen | {method})
                    found, out = found + more, out or left
            return found, out

        for site, (method, (package, source, line), owner, name, desc) in places.items():
            if site not in calls and site not in outside:
                continue
            found, out = ends(site, frozenset())
            holder = methods[method]
            key = (holder["class"], holder["name"], holder["desc"], package, source, line, owner, name, desc)
            entry = merged.setdefault(key, {
                "class": holder["class"], "method": holder["name"], "package": package, "source": source,
                "line": line, "from": holder["from"], "owner": owner, "name": name, "desc": desc, "outside": False,
                "callees": {}})
            entry["outside"] = entry["outside"] or out
            for callee in found:
                kept = {field: value for field, value in methods[callee].items() if field != "forwards"}
                entry["callees"][(kept["class"], kept["name"], kept["desc"])] = kept
    sites = [{**entry, "callees": [entry["callees"][key] for key in sorted(entry["callees"])]}
             for _key, entry in sorted(merged.items())]
    return {"sites": sites, "classes": sorted(classes),
            "skipped": [{"class": name, "why": why} for name, why in sorted(skipped.items())], "jvms": jvms}


def _forwarded(name: str, sites: list[tuple[int, str]]) -> list[int]:
    """The sites of a synthetic method that are the call it stands for: the ones naming the method it is named
    after (`name$default` and a bridge call `name`), else its only site (an accessor, `access$000`)."""
    same = [site for site, called in sites if called == name.removesuffix("$default")]
    return same or ([sites[0][0]] if len(sites) == 1 else [])


def _simple(name: str) -> str:
    """A class's name as its source writes it: `fx/Outer$Inner` is `Inner`."""
    return name.rpartition("/")[2].rpartition("$")[2]


def _properties(name: str) -> tuple[str, ...]:
    """The Kotlin property an accessor's name stands for: `getPercent` and `setPercent` for `percent` (or `URL`
    for `getURL`), `isOpen` for itself."""
    match = re.fullmatch(r"(get|set|is)([A-Z]\w*)", name)
    if not match:
        return ()
    rest = match.group(2)
    return (name,) if match.group(1) == "is" else (rest[0].lower() + rest[1:], rest)


def place(observed: dict, root: str, sources: list[str], text) -> tuple[list[dict], dict]:
    """The contract's sites from what the recorder saw (`read`) in the build at `root` ('' the project's), over the
    snapshot's Java and Kotlin `sources` (`text(rel)` their text), and what the placing says of itself: the sites
    `recorded`, `placed`, `ambiguous` (count and examples) and `unplaced` by cause (see the module docstring)."""
    import languages
    from edge_grading import callee_column
    files = [rel for rel in sources if jvm.inside(rel, root)]
    parsed, packages = {}, {}
    project = set(observed.get("classes") or ())

    def parse(rel: str) -> tuple[list[str], dict]:
        """The file's lines and its semantic facts, by the parser the snapshot's are from."""
        if rel not in parsed:
            content = text(rel) or ""
            try:
                result = languages.get_adapter("java" if rel.endswith(".java") else "kotlin").parse(content, rel)
                semantic = result.semantic if isinstance(result.semantic, dict) else {}
            except (ValueError, RecursionError):
                semantic = {}
            parsed[rel] = (content.split("\n"), semantic)
        return parsed[rel]

    def where(package: str, source: str, origin: str) -> str | None:
        """The file of the snapshot a class's `source` file is: the one of that name that declares its package,
        in the module the class was loaded from when two do."""
        named = []
        for rel in files:
            if posixpath.basename(rel) == source:
                if rel not in packages:
                    found = PACKAGE.search(text(rel) or "")
                    packages[rel] = found.group(1) if found else ""
                if packages[rel] == package.replace("/", "."):
                    named.append(rel)
        if len(named) > 1:
            parts = origin.split("/")
            module = "/".join(parts[:next((at for at, part in enumerate(parts) if part in ("target", "build")),
                                          len(parts))])
            named = [rel for rel in named if jvm.inside(rel, posixpath.join(root, module) if module else root)] or named
        return named[0] if len(named) == 1 else None

    def callee(entry: dict) -> dict:
        kind = "constructor" if entry["name"] == "<init>" else "lambda" if entry["lambda"] else "method"
        name = _simple(entry["class"]) if kind == "constructor" else entry["name"]
        rel, line, column = where(entry["package"], entry["source"], entry["from"]), entry["line"], None
        if rel is not None:
            wanted = "(lambda)" if kind == "lambda" else name
            spans = [tuple(item["span"]) for item in parse(rel)[1].get("declarations", ())
                     if item["kind"] in ("function", "method", "class") and item["name"] == wanted
                     and item["span"][0] <= line <= item["span"][2]]
            inner = [span for span in spans if not any(other != span and span[:2] <= other[:2] and other[2:] <= span[2:]
                                                      for other in spans)]
            if len(inner) == 1:
                line, column = inner[0][0], inner[0][1]
        file = rel or posixpath.join(root, entry["from"], entry["class"] + ".class")
        return {"kind": "project", "file": file, "line": max(line - 1, 0), "column": column, "name": name, "type": kind}

    found, ambiguous, unplaced = collections.defaultdict(dict), [], collections.Counter()
    for site in observed["sites"]:
        rel = where(site["package"], site["source"], site["from"])
        if rel is None:
            unplaced["no source file in the snapshot"] += 1
            continue
        if not site["line"]:
            unplaced["no line in the class file"] += 1
            continue
        lines, semantic = parse(rel)
        called = site["name"].removesuffix("$default")  # Kotlin's call of `name` that leaves arguments to defaults
        names = {_simple(site["owner"])} if called == "<init>" else {called}
        reads = set(_properties(called)) if rel.endswith(".kt") else set()
        at = set()
        for reference in semantic.get("references", ()):
            parts, span = reference.get("parts") or [], reference["span"]
            if parts and span[2] == site["line"] and span[2] <= len(lines) and (
                    parts[-1] in names if reference["kind"] == "call" else parts[-1] in reads):
                column = callee_column(lines[span[2] - 1], list(span), parts[-1])
                if column is not None:
                    at.add((column, parts[-1]))
        if len(at) != 1:
            if at:
                ambiguous.append(f"{rel}:{site['line']} {site['name']}")
            else:
                unplaced[NO_CALL] += 1
            continue
        [(column, name)] = at
        callees = found[(rel, site["line"] - 1, column, name)]
        for item in site["callees"]:
            item = callee(item)
            callees[json.dumps(item, sort_keys=True)] = item
        if site["outside"]:
            item = {"kind": "external", "module": site["owner"].replace("/", "."), "name": called,
                    **({"mock": True} if site["owner"] in project else {})}
            callees[json.dumps(item, sort_keys=True)] = item
    sites = [{"file": rel, "line": line, "column": column, "name": name, "role": "call",
              "callees": list(callees.values())} for (rel, line, column, name), callees in sorted(found.items())]
    return sites, {"recorded": len(observed["sites"]), "placed": len(observed["sites"]) - len(ambiguous)
                   - sum(unplaced.values()), "ambiguous": {"count": len(ambiguous),
                                                           "examples": sorted(set(ambiguous))[:EXAMPLES]},
                   "unplaced": dict(sorted(unplaced.items()))}


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""


def _outcome(run: dict, code: str, log: str, suites: str, ended: str) -> tuple[dict, list[dict]]:
    """One build's entry (`root`, `runner`, how its tests ended as `dynamic.TESTS` says) and its gaps, from the
    tests' exit code, their log and the counts of the JUnit XML reports this run wrote (Gradle's and Surefire's
    are of one format)."""
    counts = collections.Counter()
    for key, value in SUITE.findall(suites):
        counts[key] += int(value)
    entry = {"root": run["root"], "runner": run["tool"], "state": "ran", "tool": run["tool"], "argv": run["argv"],
             "exit_code": int(code) if code.strip().isdigit() else None,
             **{key: counts[key] for key in ("tests", "failures", "errors", "skipped")}}
    command = f"{' '.join(run['argv'])} in {run['root'] or '.'}"
    tail = " | ".join(line.strip() for line in log.strip().splitlines()[-8:])[-600:]
    failed, tests, exit_code = counts["failures"] + counts["errors"], counts["tests"], entry["exit_code"]

    def gap(kind: str, detail: str) -> dict:
        return {"kind": kind, "path": run["root"], "detail": detail}

    gaps, stop = [], dynamic.stopped(exit_code, None, LIMIT)
    if exit_code is None:
        entry["state"] = "not_started"
        gaps.append(gap("tests_not_started", f"{command}: the run ended before the tests' exit ({ended})"))
    elif stop == "timeout":
        entry["state"] = "timeout"
        gaps.append(gap("tests_timeout", f"{command} did not end in {LIMIT} s: what ran until then is observed"))
    elif stop == "killed":  # the container's memory limit, or `timeout`'s KILL of a build that outlived its TERM
        entry["state"] = "killed"
        gaps.append(gap("tests_killed", f"{command} was killed before its end, at the container's memory limit "
                                        f"({MEMORY // 2**30} GB) or {LIMIT} s: what ran until then is observed: "
                                        f"{tail}"))
    elif not tests:
        entry["state"] = "no_tests" if exit_code == 0 else "not_started"
        gaps.append(gap("no_tests", f"{command} ran no test") if exit_code == 0 else
                    gap("tests_not_started", f"{command}: no test started (exit code {exit_code}): {tail}"))
    elif exit_code and not failed:
        gaps.append(gap("tests_not_started", f"{command} stopped (exit code {exit_code}) after {tests} tests: the "
                                             f"tests of some modules may not have started: {tail}"))
    if failed:
        gaps.append(gap("tests_failed", f"{command}: {failed} of {tests} tests failed, and a test that fails may stop "
                                        f"before its calls: {tail}"))
    said = [line.strip() for line in log.splitlines() if "DAODAN_RECORD_ERROR" in line]
    if said:
        gaps.append(gap("recorder_failed", f"{command}: the agent could not record in some JVM: {said[0][:300]}"))
    return entry, gaps


def observe(project: Path, planned: dict, out_dir: Path, engine=None) -> dict:
    """The planned runs, one container run per build over a copy of its folder, read back from `out_dir`:
    `{state, sites, runs, gaps, facts}`, `state` `ran`, `gap` (no container, or a JDK the image lacks: `cause`,
    `remedy`) or `failed` (the preparation failed: `cause`, `remedy`) when no build's tests ran; a build that did
    not run beside one that did is a run `not_started` with its `tests_not_started` gap. `facts` is what the
    recorder and the placing say of themselves."""
    import container
    from engine_tools import MAVEN_CENTRAL, maven_central_dir
    runs, out_dir = planned["runs"], Path(out_dir)
    if not runs:
        return {"state": "ran", "sites": [], "runs": [], "gaps": [], "facts": {}}  # the plan's gaps say why
    group, artifact, version = ASM[0].split(":")
    relative = f"{group.replace('.', '/')}/{artifact}/{version}/{artifact}-{version}.jar"
    try:
        asm = jvm.fetched(f"{MAVEN_CENTRAL}/{relative}", maven_central_dir() / relative, ASM[1])
    except container.Gap as gap:
        return {"state": "gap", "cause": gap.cause, "remedy": gap.remedy, "sites": [], "runs": [], "gaps": [],
                "facts": {}}
    carried = {f"{AGENT}/asm.jar": asm,
               **{f"{AGENT}/{path.name}": path for path in sorted(RECORD.iterdir()) if path.is_file()}}

    def text(rel: str) -> str:
        return _text(Path(project) / rel)

    def ran(attempt: dict) -> bool:
        return attempt.get("entry", {}).get("state") in dynamic.TESTS[:3]

    attempts = []  # per run started: its root, its entry or why it stopped, its gaps, sites and placing
    for number, run in enumerate(runs):
        if any(item["root"] == run["root"] and ran(item) for item in attempts):
            continue  # the folder's other build ran the same tests
        work = out_dir / f"build-{number}"
        prepare, execute = scripts(run)
        prepare = jvm.raise_line(planned.get("toolchains"), run["root"], 8, "levels") + prepare
        result, steps, back = jvm.run(Path(project) / run["root"] if run["root"] else Path(project), work, prepare,
                                      execute, memory=MEMORY, engine=engine,
                                      toolchains=jvm.for_tool(planned.get("toolchains"), run["tool"]),
                                      timeout=LIMIT + 300, inputs=carried,
                                      jdk=jvm.build_jdk(run, planned.get("toolchains")),
                                      hosts=planned.get("declared", {}).get("hosts", ()), checkout=Path(project))
        attempt = {"root": run["root"], "gaps": [*result.get("gaps", []), *jvm.edited(
            steps, run["root"], "does not compile on the JDK it runs on", "its tests ran on a build")]}
        attempts.append(attempt)
        if result["state"] in ("gap", "failed"):
            failing = next((step for step in steps if step["returncode"]), steps[-1] if steps else {})
            tail = (failing.get("stderr_tail") or "").strip()[-800:]
            cause = result.get("cause") or "the container run failed"
            attempt["stopped"] = {"root": run["root"], "tool": run["tool"], "argv": run["argv"],
                                  "state": result["state"],
                                  "cause": f"{cause}: {tail}" if result["state"] == "failed" and tail else cause,
                                  "remedy": result.get("remedy")
                                  or f"see prepare.log and execute.log in {work / 'container'}"}
            continue
        if run["tool"] == "gradle":  # the Test tasks the preparation named
            run = {**run, "argv": [*run["argv"], *sorted(set(_text(back / "test-tasks.txt").split()))]}
        entry, own = _outcome(run, _text(back / "tests.code"), _text(back / "tests.log"), _text(back / "suites.txt"),
                              result["state"])
        observed = read(back / "calls")
        entry["jvms"] = observed["jvms"]
        attempt["entry"] = entry
        attempt["gaps"] += own
        command = f"{' '.join(run['argv'])} in {run['root'] or '.'}"
        if entry["tests"] and not observed["jvms"]:
            attempt["gaps"].append({"kind": "not_observed", "path": run["root"], "detail": f"{command}: "
                                    f"{entry['tests']} tests ran and no JVM recorded a call: the build starts its "
                                    "test JVMs without JAVA_TOOL_OPTIONS"})
        if observed["skipped"]:
            first = observed["skipped"][0]
            attempt["gaps"].append({"kind": "classes_unrecorded", "path": run["root"], "detail":
                                    f"{len(observed['skipped'])} classes ran as built, unrecorded: the agent could "
                                    f"not rewrite them ({first['class']}: {first['why'][:200]})"})
        attempt["observed"] = observed
        attempt["sites"], attempt["said"] = place(observed, run["root"], planned.get("sources") or [], text)
    # Where a folder's tests ran, the other build's attempt there says nothing of what they call.
    done = {item["root"] for item in attempts if ran(item)}
    attempts = [item for item in attempts if item["root"] not in done or ran(item)]
    sites = [site for item in attempts for site in item.get("sites", ())]
    entries = [item["entry"] for item in attempts if "entry" in item]
    gaps = [gap for item in attempts for gap in item["gaps"]]
    stopped = [item["stopped"] for item in attempts if "stopped" in item]
    facts = {"jvms": 0, "skipped": 0, "recorded": 0, "placed": 0, "ambiguous": {"count": 0, "examples": []},
             "unplaced": collections.Counter()}
    for item in attempts:
        if "said" not in item:
            continue
        observed, said = item["observed"], item["said"]
        facts["jvms"] += observed["jvms"]
        facts["skipped"] += len(observed["skipped"])
        for key in ("recorded", "placed"):
            facts[key] += said[key]
        facts["ambiguous"]["count"] += said["ambiguous"]["count"]
        facts["ambiguous"]["examples"] = (facts["ambiguous"]["examples"] + said["ambiguous"]["examples"])[:EXAMPLES]
        facts["unplaced"].update(said["unplaced"])
    if not entries:
        first = next((item for item in stopped if item["state"] == "gap"), stopped[0])
        return {"state": first["state"], "cause": first["cause"], "remedy": first["remedy"], "sites": [], "runs": [],
                "gaps": gaps, "facts": {}}
    for item in stopped:
        entries.append({"root": item["root"], "runner": item["tool"], "state": "not_started", "tool": item["tool"],
                        "argv": item["argv"]})
        gaps.append({"kind": "tests_not_started", "path": item["root"],
                     "detail": f"the {item['tool']} build in {item['root'] or '.'} did not run its tests: "
                               f"{item['cause']}"})
    if facts["ambiguous"]["count"]:
        gaps.append({"kind": "sites_ambiguous", "detail": f"{facts['ambiguous']['count']} observed call sites share "
                     "their line with another call of the same name, so the reference each answers is unknown and "
                     f"they are not placed: {', '.join(facts['ambiguous']['examples'][:3])}"})
    facts["unplaced"] = dict(sorted(facts["unplaced"].items()))
    completed = {entry["root"]: entry["tool"] for entry in entries
                 if entry["state"] == "ran" and entry.get("exit_code") == 0}
    equivalent = [index for index, run in enumerate(runs) if run["root"] in completed
                  and run["tool"] != completed[run["root"]]]
    return {"state": "ran", "sites": sites, "runs": entries, "gaps": gaps, "facts": facts,
            **({"equivalent_completed": equivalent} if equivalent else {})}
