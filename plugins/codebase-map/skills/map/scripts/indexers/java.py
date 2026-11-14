"""scip-java for Java: how it runs, and what its index leaves to the reader.

`index` runs scip-java's Maven or Gradle build in a container (`indexers.jvm`): in the preparation, the build
unchanged, then, when it gives no index, with the plain javac (the root pom's compiler plugin without its
`compilerId`, `forceJavacCompilerUse` and `dependencies`: Error Prone 2.3.1 runs only on Java 8 and 9). The
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

MIN_FREE = 2 * 2**30  # the container's memory: 1,360 MB for all its processes on javapoet (13 November 2026)


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

PREPARE = r'''if step index "$SCIP_JAVA" index --output "$OUT/index.scip" && [ -s "$OUT/index.scip" ]; then exit 0; fi
[ -f pom.xml ] || exit 1
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
step index "$SCIP_JAVA" index --output "$OUT/index.scip" && [ -s "$OUT/index.scip" ]
'''
EXECUTE = r'''step aggregate "$SCIP_JAVA" aggregate --no-emit-inverse-relationships --output "$OUT/index-forward.scip" \
  target/scip-targetroot
mkdir -p "$OUT/javap"
javap_to() { local out=$1; shift; javap -p -v "$@" > "$out"; }
project_classes() {
  for directory in target/*classes; do [ -d "$directory" ] && find "$directory" -name '*.class'; done \
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


def index(project_dir: Path, work_dir: Path, files: list[str] | None = None, external_classes: dict | None = None,
          *, engine=None, memory: int = MIN_FREE) -> dict:
    """The forward index of the whole build, its runs and the indexer's time and memory (`files` is not used:
    the build compiles every module). Without a container, `unavailable`; without an index, `failed`."""
    project_dir, work_dir = Path(project_dir).resolve(), Path(work_dir).resolve()
    work_dir.mkdir(parents=True, exist_ok=True)
    result, runs, out = jvm.run(project_dir, work_dir, PREPARE, execute(external_classes), memory=memory,
                                engine=engine)
    return finish(project_dir, work_dir, result, runs, out)


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
    # Without an equal forward index the default one is read, and its implementations include the inverses.
    return {"indexes": [[str(forward if same else default), ""]], "runs": runs,
            "indexer": code_graph.indexer("scip-java", jvm.VERSION, runs)}


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
