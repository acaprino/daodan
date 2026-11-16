"""scip-java for Java: how it runs, and what its index leaves to the reader.

`index` runs scip-java's Maven or Gradle build in a container (`indexers.jvm`), on the JDK the build states
(`jvm.build_jdk`). scip-java's compiler plugin runs on javac 17 or newer only (its documentation's Java versions:
8 and 11 were dropped in 0.13.0), so a build that states an older one is indexed on the image's JDK and says so
(`jdk_unsupported`). In the preparation, the build as declared, then, when it gives no index, a declared second
attempt with the plain javac (the root pom's compiler plugin without its `compilerId`, `forceJavacCompilerUse`
and `dependencies`: Error Prone 2.3.1 runs only on Java 8 and 9), which the result says (`build_edited`). The
default aggregation writes each `is_implementation` twice, from child to parent and from parent to child with
the same flags, so the shared traversal would take a method's parent and siblings for its implementations; the
execution aggregates the same build once more with `--no-emit-inverse-relationships`, and that index, whose
occurrences are checked equal, is the one read. It also writes the `javap -p -v` member order of the project's
classes and of the `external_classes` asked for, kept as `javap.json`.

`hops` is empty: `new X()` already names the constructor, an implicit constructor is defined at its class's
name, Java has no aliases, and implementations come from `is_implementation`. `static` names the calls through
`super`, bound statically, which take no implementation; `same_range` keeps an enum constant from aliasing the
constructor it runs.
"""
from __future__ import annotations

import json
import re
import shlex
from pathlib import Path

import code_graph
from indexers import jvm

# The analyzer this adapter is: the pass's entry, the languages it indexes, the unit kinds of the pre-map it takes
# its structure from, and whether its build runs only in a container (`indexers.analyzers`).
ENTRY, LANGUAGES, UNIT_KINDS, NEEDS_CONTAINER = "scip-java", ("java",), jvm.BUILD_KINDS, True
MIN_FREE = 2 * 2**30  # the container's memory: 1,360 MB for all its processes on javapoet (13 November 2026)
OLDEST_JDK = 17  # the oldest javac scip-java's compiler plugin runs on (0.12.4 still ran on 8 and 11)


def hops(index) -> dict:
    """None: see the module's docstring."""
    return {}


def static(index) -> set[tuple[str, int, int]]:
    """`(rel, line, byte column)` of each method name called through `super` (`super.m()`), bound statically."""
    out = set()
    for rel, occurrences in index.documents.items():
        ordered = sorted(occurrences, key=lambda o: (o.line, o.start))
        for before, after in zip(ordered, ordered[1:]):
            text = index.line(rel, before.line) or ""
            # `super(...)` names a constructor; `super.m` is `super`, a dot, then the method's name.
            if text[before.start:before.end] == "super" and not before.key.endswith(").")                     and (after.line, after.start) == (before.end_line, before.end + 1) and not after.definition:
                out.add((rel, after.line, index.to_bytes(rel, after.line, after.start)))
    return out


def same_range(index) -> dict[tuple[str, str], bool]:
    """Never an alias: at each enum constant's name scip-java writes its definition and a reference to the enum
    constructor it runs; a read of the constant is not a call of the constructor."""
    out = {}
    for rel, occurrences in index.documents.items():
        for occurrence in occurrences:
            if occurrence.definition:
                for other in index.at.get((rel, occurrence.line, occurrence.start), ()):
                    if not other.definition and "`<init>`" in other.key and other.key != occurrence.key                             and (other.end_line, other.end) == (occurrence.end_line, occurrence.end):
                        out[(occurrence.key, other.key)] = False
    return out


# How it runs: `indexers.jvm`, with the steps below.

# Under Maven the modules' Kotlin is indexed too (`jvm.MAVEN_KOTLIN`), so a call from Java to a Kotlin member
# ends where the same index defines it, as it does under Gradle, where scip-java indexes both. scip-java runs
# the build tool it is told (`jvm.tool_line`); a folder Gradle and Maven both build is built by each in turn.
PREPARE = r'''maven() { [ -f pom.xml ] && [ "${DAODAN_TOOL:-maven}" = maven ]; }
kotlin_too() {
  maven && maven_kotlin "$(mktemp -d)" \
    && step aggregate-kotlin "$SCIP_JAVA" aggregate --output "$OUT/index.scip" "$WORK/target/scip-targetroot"
  [ -s "$OUT/index.scip" ]
}
if step index "$SCIP_JAVA" index --output "$OUT/index.scip" ${DAODAN_TOOL:+--build-tool=$DAODAN_TOOL} \
  && [ -s "$OUT/index.scip" ]; then kotlin_too; exit; fi
maven || exit 1
cat > /tmp/PlainJavac.java <<'JAVA'
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class PlainJavac {
    public static void main(String[] args) throws Exception {
        Path pom = Path.of("pom.xml");
        String text = Files.readString(pom);
        int start = text.indexOf("<artifactId>maven-compiler-plugin</artifactId>");
        int end = start < 0 ? -1 : text.indexOf("</plugin>", start);
        if (end < 0) {
            System.out.println("no maven-compiler-plugin in pom.xml");
            System.exit(1);
        }
        String block = text.substring(start, end);
        List<String> removed = new ArrayList<>();
        for (String pattern : new String[] {"\\s*<compilerId>[^<]*</compilerId>",
                "\\s*<forceJavacCompilerUse>[^<]*</forceJavacCompilerUse>", "\\s*<dependencies>.*?</dependencies>"}) {
            Matcher matcher = Pattern.compile(pattern, Pattern.DOTALL).matcher(block);
            while (matcher.find()) {
                removed.add(matcher.group().strip());
            }
            block = matcher.replaceAll("");
        }
        if (removed.isEmpty()) {
            System.out.println("nothing to remove from the compiler plugin");
            System.exit(1);
        }
        Files.writeString(pom, text.substring(0, start) + block + text.substring(end));
        StringBuilder json = new StringBuilder("[");
        for (String item : removed) {
            json.append(json.length() > 1 ? ", \"" : "\"").append(item.replace("\\", "\\\\").replace("\"", "\\\"")
                .replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")).append('"');
        }
        System.out.println("DAODAN_PATCHED " + json.append(']'));
    }
}
JAVA
step plain-javac java /tmp/PlainJavac.java || exit 1
rm -f "$OUT/index.scip"
step index "$SCIP_JAVA" index --output "$OUT/index.scip" ${DAODAN_TOOL:+--build-tool=$DAODAN_TOOL} \
  && [ -s "$OUT/index.scip" ] && kotlin_too
'''
# Maven writes under `target/`, Gradle under `build/`: the build that ran made one of them, in every module.
EXECUTE = r'''TARGETROOT=target/scip-targetroot
[ -d "$TARGETROOT" ] || TARGETROOT=build/scip-targetroot
step aggregate "$SCIP_JAVA" aggregate --no-emit-inverse-relationships --output "$OUT/index-forward.scip" \
  "$TARGETROOT"
mkdir -p "$OUT/javap"
javap_to() { local out=$1; shift; javap -p -v "$@" > "$out"; }
project_classes() {
  find . \( -path '*/target/*classes/*' -o -path '*/build/classes/*' \) -name '*.class' \
    | sort | xargs -r -d '\n' javap -p -v > "$OUT/javap/project.txt"
}
'''


def execute(external_classes: dict | None = None) -> str:
    """The execution's steps: the second aggregation, then `javap` of `external_classes` (a classpath under the
    local Maven repository, `""` for the JDK, to class names) and of the project's classes."""
    lines = [EXECUTE]
    for number, (path, names) in enumerate(sorted((external_classes or {}).items())):
        classpath = f'-cp "$HOME/.m2/repository/"{shlex.quote(path)} ' if path else ""
        lines.append(f'step javap-{number} javap_to "$OUT/javap/{number}.txt" {classpath}'
                     + " ".join(shlex.quote(name) for name in names))
    lines.append("step javap-project project_classes\nexit 0\n")
    return "\n".join(lines)


def structure(record: dict) -> dict:
    """What `index` takes from the pre-map: the folder of each build with its tools, the JDKs it states, Maven's
    modules with their source folders, and the kinds of the JVM builds Daodan does not run."""
    return {"roots": jvm.build_roots(record), "tools": jvm.build_tools(record), "toolchains": jvm.toolchains(record),
            "modules": jvm.modules(record), "other_builds": jvm.other_builds(record)}


def index(project_dir: Path, work_dir: Path, files: list[str] | None = None, external_classes: dict | None = None,
          *, roots, tools=None, toolchains=(), modules=(), other_builds=(), engine=None,
          memory: int = MIN_FREE, declared=None) -> dict:
    """The forward index of each build in `roots` (the pre-map's build folders, built by their `tools`), each in
    a container of its own, with its runs and the indexer's time and memory (`files` is not used: a build compiles
    every module); the member order of all of them in `javap.json`. The preparation also reaches the hosts the
    project declares (`declared`, `preparation.declared`). Without a container, `unavailable`; without an index,
    `failed`."""
    project_dir, work_dir = Path(project_dir).resolve(), Path(work_dir).resolve()
    work_dir.mkdir(parents=True, exist_ok=True)

    def one(folder: Path, work: Path, tool: str | None) -> dict:
        root = jvm.build_root(project_dir, folder)
        jdk = jvm.build_jdk({"root": root, "tool": tool}, toolchains)
        older = jdk if jdk and jvm._major(jdk["version"]) < OLDEST_JDK else None
        prepare = jvm.modules_line(modules, root) + jvm.tool_line(tool) + PREPARE
        result, runs, out = jvm.run(folder, work, prepare, execute(external_classes), memory=memory, engine=engine,
                                    toolchains=toolchains, jdk=None if older else jdk,
                                    hosts=(declared or {}).get("hosts", ()))
        part = finish(folder, work, result, runs, out)
        said = [*([unsupported(older, root)] if older else ()), *(edited(runs, root) if part.get("indexes") else ())]
        return jvm.with_gaps(jvm.with_gaps(part, result), {"gaps": said})

    parts = jvm.builds(project_dir, work_dir, roots, one, tools)
    members = {}
    for _root, part in parts:
        listed = Path(part["indexes"][0][0]).parent / "javap.json" if part.get("indexes") else None
        if listed and listed.is_file():
            members.update(json.loads(listed.read_text(encoding="utf-8")))
    (work_dir / "javap.json").write_text(json.dumps(members), encoding="utf-8")
    return jvm.combined(parts, other_builds)


def finish(project_dir: Path, work_dir: Path, result: dict, runs: list[dict], out: Path) -> dict:
    """The contract from what came back into `out`: `index.scip`, `index-forward.scip` and `javap.json`, placed
    in `work_dir`."""
    if result["state"] == "gap":
        return jvm.unavailable(result["cause"], result["remedy"])
    default = jvm.place(out / "index.scip", Path(work_dir) / "index.scip")
    if result["state"] != "done" or default is None or not default.stat().st_size:
        return jvm.failed(result, runs)
    forward = jvm.place(out / "index-forward.scip", Path(work_dir) / "index-forward.scip")
    members = {}
    for listing in sorted((out / "javap").glob("*.txt")):
        members.update(_members(listing.read_text(encoding="utf-8", errors="replace")))
    (Path(work_dir) / "javap.json").write_text(json.dumps(members), encoding="utf-8")
    indexed = [run for run in runs if run["step"] == "index"]
    if indexed:
        indexed[-1]["index_bytes"] = default.stat().st_size
    same = forward is not None and same_occurrences(project_dir, default, forward)
    for run in runs:
        if run["step"] == "aggregate":
            run["same_occurrences"] = same
    # Without an equal forward index the default one is read, and its implementations include the inverses:
    # a call on a method then also reaches its parent and siblings. Said as a gap, never silent.
    gaps = [] if same else [{"kind": "implementations_both_ways", "detail":
                             "the forward aggregate of this build is missing or differs from its index: "
                             "implementations are read both ways, so a call on a method may also name its "
                             "parent and sibling methods"}]
    return {"indexes": [[str(forward if same else default), ""]], "runs": runs,
            "indexer": code_graph.indexer("scip-java", jvm.VERSION, runs), **({"gaps": gaps} if gaps else {})}


def unsupported(jdk: dict, root: str) -> dict:
    """A build that states a JDK older than scip-java's: the `jdk_unsupported` gap of its index."""
    return {"kind": "jdk_unsupported", "path": root or ".", "detail":
            f"the build states Java {jdk['version']} ({jdk['declared_in']}) and scip-java {jvm.VERSION}'s compiler "
            f"plugin runs on javac {OLDEST_JDK} or newer only: it was indexed on the image's JDK {jvm.JDK}, so its "
            f"calls into the JDK name JDK {jvm.JDK}'s classes, not those of Java {jdk['version']}"}


def edited(runs: list[dict], root: str) -> list[dict]:
    """An index of the second build, of the pom `PREPARE` edited (its `plain-javac` step): the `build_edited` gap,
    with what was removed and the errors of the build as declared."""
    removed = next((run["patched_pom_removed"] for run in runs if run.get("patched_pom_removed")), None)
    if not removed:
        return []
    first = next((run for run in runs if run["step"] == "index"), {})
    lines = (first.get("stderr_tail") or "").splitlines()
    start = next((at for at, line in enumerate(lines) if "ERROR" in line), None)
    said = (" / ".join(line.strip() for line in lines[start:start + 6]) if start is not None
            else f"exit code {first.get('returncode')}")
    return [{"kind": "build_edited", "path": root or ".", "detail":
             f"the build as declared gave no index ({said[:600]}): this index is a second build's, of the root pom "
             f"without its compiler plugin's {'; '.join(' '.join(item.split()) for item in removed)[:600]}, "
             "compiled by the JDK's own javac"}]


def same_occurrences(root: Path, default: Path, forward: Path) -> bool:
    loaded = []
    for path in (default, forward):
        item = code_graph.Index(root)
        item.load(path)
        loaded.append(item.documents)
    return loaded[0] == loaded[1]


def _members(text: str) -> dict:
    """Methods of each class of a `javap -p -v` output, in class-file order, with their access flags."""
    out, current, pending = {}, None, None
    for line in text.split("\n"):
        match = re.match(r"\s*this_class: #\d+\s+// (\S+)", line)
        if match:
            current, pending = match.group(1), None
            out[current] = []
            continue
        if current is None:
            continue
        if re.match(r"^  \S", line) and line.rstrip().endswith(";") and "(" in line:
            name = re.search(r"([\w$<>]+)\(", line)
            pending = {"declaration": line.strip(), "name": name.group(1) if name else "", "flags": []}
            out[current].append(pending)
            continue
        match = re.match(r"^    flags: \(0x[0-9a-f]+\)(.*)", line)
        if match and pending is not None:
            pending["flags"] = [flag.strip() for flag in match.group(1).split(",") if flag.strip()]
            pending = None
    return out
