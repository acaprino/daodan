"""scip-java for Java: how the indexer runs. What its index leaves to the reader is the plugin's
`indexers/java.py`.

`index` compiles a copy of the checkout with scip-java (Maven and the SemanticDB javac plugin): unchanged
first, then with the plain javac when the unchanged build gives no index. The default aggregation writes each
`is_implementation` twice, from child to parent and from parent to child with the same flags, so the shared
traversal would take a method's parent and siblings for its implementations; the same build is aggregated once
more with `--no-emit-inverse-relationships`, and that index, whose occurrences are checked equal, is the one
read. `class_file_declaration` reads the overload an external `name(+n)` names from the class-file member
order: the hand check uses it, the graph does not.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import plugin_scripts  # noqa: E402,F401  (puts the plugin's scripts on the path)
import code_graph  # noqa: E402

VERSION = "0.13.2"  # org.scip-code:scip-java on Maven Central, released 2026-10-22
LAUNCHER = "/opt/scip-java/scip-java"
APT = ("default-jdk-headless", "maven")
METHOD = re.compile(r"^((?:[\w$]+/)*)((?:[\w$]+#)+)`?([\w$<>]+)`?\(([^)]*)\)\.$")


def install_commands() -> list[str]:
    """scip-java assembled by coursier, at the coursier pin of the map's engines."""
    import resolve_edges
    coursier = resolve_edges.COURSIER
    return [f"curl -fsSL {coursier['url']} -o /opt/coursier.jar",
            f"echo '{coursier['sha256']}  /opt/coursier.jar' | sha256sum -c -",
            "mkdir -p /opt/scip-java",
            f"java -jar /opt/coursier.jar bootstrap --assembly -o {LAUNCHER} org.scip-code:scip-java:{VERSION} "
            "--main org.scip_code.scip_java.ScipJava"]


def _install() -> None:
    if Path(LAUNCHER).is_file():
        return
    for command in ["apt-get update", f"apt-get install -y {' '.join(APT)}", *install_commands()]:
        subprocess.run(command, shell=True, check=True)


def _plain_javac(pom: Path) -> list[str]:
    """The compiler plugin without Error Prone, whose pinned 2.3.1 runs only on Java 8 and 9: what was removed."""
    text = pom.read_text(encoding="utf-8")
    start = text.index("<artifactId>maven-compiler-plugin</artifactId>")
    end = text.index("</plugin>", start)
    block, removed = text[start:end], []
    for pattern in (r"\s*<compilerId>[^<]*</compilerId>", r"\s*<forceJavacCompilerUse>[^<]*</forceJavacCompilerUse>",
                    r"\s*<dependencies>.*?</dependencies>"):
        removed += [m.group(0).strip() for m in re.finditer(pattern, block, flags=re.S)]
        block = re.sub(pattern, "", block, flags=re.S)
    pom.write_text(text[:start] + block + text[end:], encoding="utf-8")
    return removed


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


def index(project_dir: Path, work_dir: Path, files: list[str] | None = None,
          external_classes: dict | None = None) -> dict:
    """The forward index of the project, its runs and the indexer's time and memory.

    `external_classes` maps a classpath (`""` for the JDK, else a jar under the local Maven repository) to the
    class names whose member order `javap.json` records beside the project's own classes.
    """
    _install()
    work_dir.mkdir(parents=True, exist_ok=True)
    mirror = work_dir / "mirror"
    if not mirror.exists():
        shutil.copytree(project_dir, mirror, symlinks=True, ignore=shutil.ignore_patterns(".git"))
    env = dict(os.environ)
    tools = {"java": subprocess.run(["java", "-version"], capture_output=True, text=True).stderr.strip().splitlines(),
             "maven": subprocess.run(["mvn", "-v"], capture_output=True, text=True).stdout.strip().splitlines()[:3]}
    runs, output = [], work_dir / "index.scip"
    for patched in (False, True):
        removed = _plain_javac(mirror / "pom.xml") if patched else None
        run = {"step": "index", "tools": tools, "patched_pom_removed": removed,
               **code_graph.measured([LAUNCHER, "index", "--output", str(output)], str(mirror), env, 3000)}
        run["index_bytes"] = output.stat().st_size if output.is_file() else 0
        runs.append(run)
        if run["returncode"] == 0 and run["index_bytes"]:
            break
    if not (runs[-1]["returncode"] == 0 and runs[-1]["index_bytes"]):
        return {"indexes": [], "runs": runs, "indexer": code_graph.indexer("scip-java", VERSION, runs)}
    forward = work_dir / "index-forward.scip"
    runs.append({"step": "aggregate without inverse relationships",
                 **code_graph.measured([LAUNCHER, "aggregate", "--no-emit-inverse-relationships", "--output",
                                        str(forward), str(mirror / "target/scip-targetroot")], str(mirror), env, 600)})
    commands = [["javap", "-p", "-v", *names] if not path else
                ["javap", "-p", "-v", "-cp", str(Path.home() / ".m2/repository" / path), *names]
                for path, names in (external_classes or {}).items()]
    commands.append(["javap", "-p", "-v", *sorted(str(p) for p in mirror.glob("target/*classes/**/*.class"))])
    members = {}
    for command in commands:
        members.update(_members(subprocess.run(command, capture_output=True, text=True).stdout))
    (work_dir / "javap.json").write_text(json.dumps(members), encoding="utf-8")
    runs[-1]["same_occurrences"] = same = forward.is_file() and same_occurrences(project_dir, output, forward)
    # Without an equal forward index the default one is read, and its implementations include the inverses.
    return {"indexes": [[str(forward if same else output), ""]], "runs": runs,
            "indexer": code_graph.indexer("scip-java", VERSION, runs)}


def same_occurrences(root: Path, default: Path, forward: Path) -> bool:
    loaded = []
    for path in (default, forward):
        item = code_graph.Index(root)
        item.load(path)
        loaded.append(item.documents)
    return loaded[0] == loaded[1]


@lru_cache(maxsize=4)
def _javap(work_dir: str) -> dict:
    path = Path(work_dir) / "javap.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}


def class_file_declaration(symbol: str, work_dir: Path) -> str | None:
    """The declaration a method symbol `name(+n)` names, read from the class-file member order, not the index."""
    match = METHOD.match(symbol.split(" ", 4)[-1]) if not symbol.startswith("local ") else None
    if not match:
        return None
    packages, types, name, disambiguator = match.groups()
    members = _javap(str(work_dir)).get(packages + types.rstrip("#").replace("#", "$"))
    if members is None:
        return None
    wanted = types.rstrip("#").split("#")[-1] if name == "<init>" else name
    overloads = [m for m in members if m["name"].split(".")[-1].split("$")[-1] == wanted
                 and "ACC_SYNTHETIC" not in m["flags"] and "ACC_BRIDGE" not in m["flags"]]
    number = int(disambiguator[1:]) if disambiguator.startswith("+") else 0
    return overloads[number]["declaration"] if number < len(overloads) else None


def parameters(signature: str | None, name: str) -> str | None:
    """Parameter types of a Java signature or declaration text, generics erased, names dropped."""
    if not signature:
        return None
    at = signature.find(name + "(") if name not in ("<init>",) else -1
    start = signature.index("(", at) if at >= 0 else signature.find("(")
    if start < 0:
        return None
    depth, end = 0, start
    for end in range(start, len(signature)):
        depth += {"(": 1, ")": -1}.get(signature[end], 0)
        if depth == 0:
            break
    inner, items, depth, current = signature[start + 1:end], [], 0, ""
    for char in inner:
        depth += {"<": 1, ">": -1}.get(char, 0)
        if char == "," and depth == 0:
            items.append(current)
            current = ""
        else:
            current += char
    if current.strip():
        items.append(current)
    types = []
    for item in items:
        item = re.sub(r"@[\w.]+(\([^)]*\))?\s*", "", item).replace("final ", "").strip()
        erased, depth = "", 0
        for char in item:
            depth += 1 if char == "<" else 0
            if depth == 0:
                erased += char
            depth -= 1 if char == ">" else 0
        words = erased.split()
        kind = (" ".join(words[:-1]) if len(words) > 1 else erased).replace(" ", "")
        # A nested class is `Outer$Inner` in a class file and `Inner` in a signature written from source.
        simple = (kind[:-3] if kind.endswith("...") else kind).split(".")[-1].split("$")[-1]
        types.append(simple + "..." if kind.endswith("...") else simple)
    return ", ".join(types)
