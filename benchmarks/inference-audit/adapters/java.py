"""scip-java for Java on Modal: the plugin's `indexers.java` steps, run by `jvm_here` in the function's own
container, where no container engine runs. How the index is built and what it leaves to the reader is the
plugin's `indexers/java.py`. `class_file_declaration` reads the overload an external `name(+n)` names from the
class-file member order (`javap.json`): the hand check uses it, the graph does not.
"""
from __future__ import annotations

import json
import re
import sys
from functools import lru_cache
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import plugin_scripts  # noqa: E402,F401  (puts the plugin's scripts on the path)
from adapters import jvm_here  # noqa: E402
from indexers import java as plugin  # noqa: E402
from indexers import jvm  # noqa: E402

VERSION = jvm.VERSION
METHOD = re.compile(r"^((?:[\w$]+/)*)((?:[\w$]+#)+)`?([\w$<>]+)`?\(([^)]*)\)\.$")


def index(project_dir: Path, work_dir: Path, files: list[str] | None = None,
          external_classes: dict | None = None) -> dict:
    """The plugin's contract for the checkout, built here; `refused` lists the hosts the registry proxy refused.

    `external_classes` maps a classpath (`""` for the JDK, else a jar under the local Maven repository) to the
    class names whose member order `javap.json` records beside the project's own classes.
    """
    result, runs, out = jvm_here.run(project_dir, work_dir, plugin.PREPARE, plugin.execute(external_classes))
    return {**plugin.finish(Path(project_dir), Path(work_dir), result, runs, out), "refused": result["refused"]}


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
