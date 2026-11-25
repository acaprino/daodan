"""scip-java for Java: how it runs, and what its index leaves to the reader.

`index` runs scip-java's Maven or Gradle build in a container (`indexers.jvm`), on the JDK the build states
(`jvm.build_jdk`). scip-java's compiler plugin runs on javac 17 or newer only (its documentation's Java versions:
8 and 11 were dropped in 0.13.0), so a build that states an older one says so (`jdk_unsupported`): Maven's is
indexed on the image's JDK, Gradle's compiles on that toolchain, where the plugin does not load (Gradle itself runs
on the image's). In the preparation, the build as declared, then, when it gives no index, a declared second
attempt, which the result says (`build_edited`). Under Maven, with the plain javac (the root pom's compiler
plugin without its `compilerId`, `forceJavacCompilerUse` and `dependencies`: Error Prone 2.3.1 runs only on
Java 8 and 9) and each pom's level under 8 raised to 8, the oldest the image's javac compiles. Under Gradle,
when a script states a Java under 17, with `jvm.RAISE_LEVELS`. The
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
NAME, LANGUAGES, UNIT_KINDS, NEEDS_CONTAINER = "scip-java", ("java",), jvm.BUILD_KINDS, True
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
if scip_index && [ -s "$OUT/index.scip" ]; then kotlin_too; exit; fi
if ! maven; then
  [ -n "${DAODAN_RAISE:-}" ] || exit 1
  raise_levels
else
cat > /tmp/PlainJavac.java <<'JAVA'
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.stream.Stream;

public class PlainJavac {
    static String quoted(String item) {
        return '"' + item.replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", "\\n").replace("\r", "\\r")
            .replace("\t", "\\t") + '"';
    }

    public static void main(String[] args) throws Exception {
        List<String> removed = removed(Path.of("pom.xml"));
        List<String> raised = new ArrayList<>();
        Pattern level = Pattern.compile(
            "<((?:maven\\.compiler\\.)?(?:source|target|release)|java\\.version)>\\s*(?:1\\.[0-7]|[1-7])\\s*</\\1>");
        List<Path> poms;
        try (Stream<Path> files = Files.walk(Path.of(""))) {
            poms = files.filter(file -> file.endsWith("pom.xml") && !file.toString().contains("target/"))
                .sorted().toList();
        }
        for (Path pom : poms) {
            String before = Files.readString(pom);
            Matcher matcher = level.matcher(before);
            StringBuilder after = new StringBuilder();
            while (matcher.find()) {
                raised.add(pom + ": " + matcher.group().replaceAll("\\s+", "") + " -> 8");
                matcher.appendReplacement(after, "<$1>8</$1>");
            }
            if (after.length() > 0) {
                Files.writeString(pom, matcher.appendTail(after).toString());
            }
        }
        if (removed.isEmpty() && raised.isEmpty()) {
            System.out.println("nothing to edit: no compiler plugin setting to remove, no level under 8");
            System.exit(1);
        }
        if (!removed.isEmpty()) {
            List<String> items = new ArrayList<>();
            for (String item : removed) {
                items.add(quoted(item));
            }
            System.out.println("DAODAN_PATCHED [" + String.join(", ", items) + "]");
        }
        for (String item : raised) {
            System.out.println("DAODAN_RAISED " + quoted(item));
        }
    }

    /** What the root pom's compiler plugin loses: the settings that take the compilation from the JDK's javac. */
    static List<String> removed(Path pom) throws Exception {
        String text = Files.readString(pom);
        List<String> removed = new ArrayList<>();
        int start = text.indexOf("<artifactId>maven-compiler-plugin</artifactId>");
        int end = start < 0 ? -1 : text.indexOf("</plugin>", start);
        if (end < 0) {
            return removed;
        }
        String block = text.substring(start, end);
        for (String pattern : new String[] {"\\s*<compilerId>[^<]*</compilerId>",
                "\\s*<forceJavacCompilerUse>[^<]*</forceJavacCompilerUse>", "\\s*<dependencies>.*?</dependencies>"}) {
            Matcher matcher = Pattern.compile(pattern, Pattern.DOTALL).matcher(block);
            while (matcher.find()) {
                removed.add(matcher.group().strip());
            }
            block = matcher.replaceAll("");
        }
        if (!removed.isEmpty()) {
            Files.writeString(pom, text.substring(0, start) + block + text.substring(end));
        }
        return removed;
    }
}
JAVA
step plain-javac java /tmp/PlainJavac.java || exit 1
fi
rm -f "$OUT/index.scip"
scip_index && [ -s "$OUT/index.scip" ] && kotlin_too
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
    modules with their source folders, the kinds of the JVM builds Daodan does not run, what maven-compiler-plugin
    leaves out of each source folder (`excluded`: {folder: [pom, patterns]}), and the Maven modules only a file
    states, which Maven's reactor does not hold (`outside`: [root, pom])."""
    maven = [unit for unit in record.get("units", []) if unit["kind"] == "maven-module"]
    excluded = {folder: [unit["manifest"], patterns] for unit in maven
                for folder, patterns in (unit.get("compile_excludes") or {}).items()}
    modeled = [any(str(source).startswith("maven@") for source in unit.get("sources") or ()) for unit in maven]
    outside = [[unit["root"], unit["manifest"]] for unit, held in zip(maven, modeled) if not held] if any(modeled) \
        else []  # a module only a file names: Maven's reactor does not hold it
    return {"roots": jvm.build_roots(record), "tools": jvm.build_tools(record), "toolchains": jvm.toolchains(record),
            "modules": jvm.modules(record), "other_builds": jvm.other_builds(record),
            **({"excluded": excluded} if excluded else {}), **({"outside": outside} if outside else {})}


def index(project_dir: Path, work_dir: Path, files: list[str] | None = None, external_classes: dict | None = None,
          *, roots, tools=None, toolchains=(), modules=(), other_builds=(), engine=None,
          memory: int = MIN_FREE, declared=None, excluded=None, outside=None) -> dict:
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
        # Gradle compiles on the toolchains its scripts ask for (`jvm.run` installs them), whatever JDK runs it.
        compiled = [item for item in toolchains if tool == "gradle" and item.get("tool") == "java"
                    and ".gradle" in item.get("declared_in", "") and jvm.inside(item["declared_in"].split("#")[0], root)
                    and (jvm._major(item.get("version")) or OLDEST_JDK) < OLDEST_JDK]
        prepare = (jvm.modules_line(modules, root) + jvm.tool_line(tool)
                   + jvm.raise_line(toolchains, root, OLDEST_JDK, "all") + PREPARE)
        result, runs, out = jvm.run(folder, work, prepare, execute(external_classes), memory=memory, engine=engine,
                                    toolchains=jvm.for_tool(toolchains, tool), jdk=None if older else jdk,
                                    hosts=(declared or {}).get("hosts", ()), checkout=project_dir)
        part = finish(folder, work, result, runs, out)
        said = [unsupported([item], root, tool) for item in [older] if item]
        # A Gradle build the second attempt indexed says its edit (`build_edited`), not a plugin that did not load.
        said += [unsupported(compiled, root, tool)] if compiled and not part.get("indexes") else []
        said += jvm.edited(runs, root) if part.get("indexes") else []
        return jvm.with_gaps(jvm.with_gaps(part, result), {"gaps": said})

    parts = jvm.builds(project_dir, work_dir, roots, one, tools)
    members = {}
    for _root, part in parts:
        listed = Path(part["indexes"][0][0]).parent / "javap.json" if part.get("indexes") else None
        if listed and listed.is_file():
            members.update(json.loads(listed.read_text(encoding="utf-8")))
    (work_dir / "javap.json").write_text(json.dumps(members), encoding="utf-8")
    result = jvm.combined(parts, other_builds)
    failed = {build["root"]: build["reason"] for build in result.get("builds") or () if build.get("reason")}
    configs = {key: value for key, value in (("excluded", excluded), ("outside", outside), ("failed", failed)) if value}
    return {**result, "configs": configs} if result.get("indexes") else result


def tasks(configs) -> dict:
    """What `missing` reads of the run: `{"excluded": {folder: [pom, patterns]}, "outside": [[root, pom]],
    "failed": {build root: why it wrote no index}}`, empty without it."""
    return configs if isinstance(configs, dict) else {}


def _matches(pattern: str, path: str) -> bool:
    """Whether `path`, relative to a source folder, matches a pattern of maven-compiler-plugin (Ant's: `**` any
    folders, `*` and `?` within one name; a pattern ending in `/` takes all below it)."""
    pattern = pattern + "**" if pattern.endswith("/") else pattern
    words = []
    for part in re.split(r"(\*\*/?|\*|\?)", pattern):
        words.append({"**/": "(?:.*/)?", "**": ".*", "*": "[^/]*", "?": "[^/]"}.get(part, re.escape(part)))
    return re.fullmatch("".join(words), path) is not None


def missing(index, rels: list[str], configs: dict | None = None) -> dict:
    """Why a Java file has no document. scip-java writes one for every file javac compiles, so no javac task of the
    build compiled it: maven-compiler-plugin leaves it out of the source folder it compiles, its module is in no
    reactor of Maven's default build, the build that holds it wrote no index, or no source set holds it."""
    configs = configs or {}

    def inside(rel: str, root: str) -> bool:
        return root in ("", ".") or rel.startswith(root.rstrip("/") + "/")

    reasons = {}
    for rel in rels:
        for folder, (pom, patterns) in (configs.get("excluded") or {}).items():
            found = next((pattern for pattern in patterns
                          if inside(rel, folder) and _matches(pattern, rel[len(folder) + 1:])), None)
            if found:
                reasons[rel] = (f"the build leaves it out: maven-compiler-plugin excludes `{found}` from {folder} "
                                f"({pom}, as Maven's effective model gives it)")
                break
        if rel in reasons:
            continue
        module = max((item for item in configs.get("outside") or () if inside(rel, item[0])),
                     key=lambda item: len(item[0]), default=None)
        build = max((root for root in configs.get("failed") or {} if inside(rel, root)), key=len, default=None)
        if module:
            reasons[rel] = (f"its module {module[0]} ({module[1]}) is in no reactor of Maven's default build: Maven's "
                            "effective model holds no project of it, so no javac task compiles it")
        elif build is not None:
            reasons[rel] = f"the build of {build or '.'} wrote no index: {configs['failed'][build]}"
        else:
            reasons[rel] = ("no javac task of the build compiles it: scip-java writes a document for every file "
                            "javac compiles")
    return reasons


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


def unsupported(stated: list[dict], root: str, tool: str | None) -> dict:
    """The JDKs a build states older than scip-java's: the `jdk_unsupported` gap. Maven compiles on the JDK that
    runs it, the image's; Gradle on the toolchains, where the plugin does not load."""
    # The level the build states: `jvm.build_jdk` keeps it as `stated` beside the JDK it names.
    versions = " and ".join(str(major) for major in sorted(
        {jvm._major(item.get("stated", item["version"])) or 0 for item in stated}))
    where = ", ".join(item["declared_in"] for item in stated[:3]) + (", ..." if len(stated) > 3 else "")
    then = (f"Gradle compiles it on that JDK, where the plugin, of Java {OLDEST_JDK}'s class files, does not load"
            if tool == "gradle" else f"it was indexed on the image's JDK {jvm.JDK}, so its calls into the JDK name "
            f"JDK {jvm.JDK}'s classes, not those of Java {versions}")
    return {"kind": "jdk_unsupported", "path": root or ".", "detail":
            f"the build states Java {versions} ({where}) and scip-java {jvm.VERSION}'s compiler plugin runs on javac "
            f"{OLDEST_JDK} or newer only: {then}"}


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
