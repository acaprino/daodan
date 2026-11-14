"""scip-java for Kotlin: how this engine builds its index. What its index leaves to the reader is the
plugin's `indexers/kotlin.py`.

`index` runs `scip-java index` (0.14: the Gradle build with scip-java's init script, then its standalone
Kotlin Analysis API indexer over the sources and classpath each KotlinCompile task dumps to
`kotlin-configs/`) on a copy of the checkout. The indexer writes `is_implementation` on the overriding member,
pointing to the member it overrides; the aggregator adds the reverse one on the overridden member
(`is_implementation` and `is_reference`, ScipAggregator.java), which `forward_only` drops so the shared reader
sees one direction.
"""
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import plugin_scripts  # noqa: E402,F401  (puts the plugin's scripts on the path)
import code_graph  # noqa: E402

VERSION = "0.14.2"  # org.scip-code:scip-java on Maven Central, Kotlin through scip-kotlin-analysis 0.14.2
JDK = "https://api.adoptium.net/v3/binary/latest/17/ga/linux/x64/jdk/hotspot/normal/eclipse"
JAVA = "/opt/jdk/bin/java"
CLASSPATH = "/opt/scip-java/classpath.txt"  # strings: the image is defined on any host


def install_commands() -> list[str]:
    """A JDK 17 and scip-java's classpath, fetched by coursier at the pin of the map's engines."""
    import resolve_edges
    coursier = resolve_edges.COURSIER
    return [f"curl -fsSL '{JDK}' -o /tmp/jdk.tgz && mkdir -p /opt/jdk && "
            "tar -xzf /tmp/jdk.tgz -C /opt/jdk --strip-components=1 && rm /tmp/jdk.tgz",
            f"mkdir -p /opt/scip-java && curl -fsSL {coursier['url']} -o /opt/scip-java/coursier.jar",
            f"echo '{coursier['sha256']}  /opt/scip-java/coursier.jar' | sha256sum -c -",
            f"{JAVA} -jar /opt/scip-java/coursier.jar fetch --classpath org.scip-code:scip-java:{VERSION} "
            f"> {CLASSPATH}"]


def index(project_dir: Path, work_dir: Path, files: list[str] | None = None) -> dict:
    """One `scip-java index` run at the checkout's root; the forward-only copy is the index to read."""
    work_dir = Path(work_dir)
    mirror = work_dir / "mirror-scip-java"
    if not mirror.exists():
        shutil.copytree(project_dir, mirror, symlinks=True)
    env = dict(os.environ, JAVA_HOME=str(Path(JAVA).parents[1]), GRADLE_USER_HOME=str(work_dir / "gradle-home"),
               TERM="dumb")
    env["PATH"] = f"{Path(JAVA).parent}{os.pathsep}{env.get('PATH', '')}"
    output = work_dir / "scip-java-0.scip"
    command = [JAVA, "-Xmx4g", "-cp", Path(CLASSPATH).read_text().strip(), "org.scip_code.scip_java.ScipJava", "index",
               "--output", str(output)]
    run = {"prefix": "", **code_graph.measured(command, str(mirror), env, 3600)}
    run["index_bytes"] = output.stat().st_size if output.is_file() else 0
    configs = mirror / "build/scip-targetroot/kotlin-configs"
    if configs.is_dir():
        shutil.copytree(configs, work_dir / "kotlin-configs", dirs_exist_ok=True)
    forward = work_dir / "index-forward.scip"
    run["index"] = str(forward) if output.is_file() else None
    if output.is_file():
        run["reverse_relationships_dropped"] = forward_only(output, forward)
    return {"indexes": [[run["index"], ""]] if run["index"] else [], "runs": [run],
            "indexer": code_graph.indexer("scip-java", VERSION, [run]), "configs": str(work_dir / "kotlin-configs")}


# The aggregator's reverse relationships, dropped from a copy of the index.

def _varint(value: int) -> bytes:
    out = bytearray()
    while True:
        byte, value = value & 0x7F, value >> 7
        out.append(byte | 0x80 if value else byte)
        if not value:
            return bytes(out)


def _spans(data: bytes):
    """`(number, wire, value, start, end)` of each field, `start:end` its raw bytes."""
    at = 0
    while at < len(data):
        start = at
        tag, at = code_graph._varint(data, at)
        number, wire = tag >> 3, tag & 7
        if wire == 0:
            value, at = code_graph._varint(data, at)
        elif wire == 2:
            length, at = code_graph._varint(data, at)
            value, at = data[at:at + length], at + length
        elif wire in (1, 5):
            value, at = data[at:at + (8 if wire == 1 else 4)], at + (8 if wire == 1 else 4)
        else:
            raise ValueError(f"unsupported wire type {wire}")
        yield number, wire, value, start, at


def _rebuilt(data: bytes, keep) -> tuple[bytes, int]:
    """`data` without the fields `keep(number, wire, value)` refuses, and how many it refused."""
    out, dropped = bytearray(), 0
    for number, wire, value, start, end in _spans(data):
        if keep(number, wire, value):
            out += data[start:end]
        else:
            dropped += 1
    return bytes(out), dropped


def _information(data: bytes) -> tuple[bytes, int]:
    def keep(number, wire, value):
        if number != 4 or wire != 2:
            return True
        flags = {field: item for field, kind, item in code_graph._fields(value) if kind == 0}
        return not (flags.get(2) and flags.get(3))  # is_reference and is_implementation: the reverse one
    return _rebuilt(data, keep)


def forward_only(source: Path, out: Path) -> int:
    """Write `source` without the aggregator's reverse relationships; returns how many were dropped."""
    data, total, result = Path(source).read_bytes(), 0, bytearray()
    for number, wire, value, start, end in _spans(data):
        if wire == 2 and number in (2, 3):
            if number == 2:  # Document: its SymbolInformation entries are field 3
                parts, count = bytearray(), 0
                for field, kind, item, begin, stop in _spans(value):
                    if field == 3 and kind == 2:
                        item, dropped = _information(item)
                        count += dropped
                        parts += _varint(field << 3 | 2) + _varint(len(item)) + item
                    else:
                        parts += value[begin:stop]
                value = bytes(parts)
            else:  # external SymbolInformation
                value, count = _information(value)
            total += count
            result += _varint(number << 3 | 2) + _varint(len(value)) + value
        else:
            result += data[start:end]
    Path(out).write_bytes(bytes(result))
    return total
