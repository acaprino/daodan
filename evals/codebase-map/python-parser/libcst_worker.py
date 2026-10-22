#!/usr/bin/env python3
"""Parse files with LibCST and emit the facts ast_worker.py emits.

LibCST is the only strict Python parser besides the stdlib that carries its own
grammar, so what it accepts does not depend on the interpreter running it. It is
measured as the third candidate on the same corpora.

Same output shape as ast_worker.py, with one limit stated rather than faked:
LibCST has no node for the `def` keyword, so `c` (column of the keyword) is
reported as null and is not compared. `l` is the line of the definition's name,
which is the keyword's line for every definition that does not split its header
with a backslash continuation.

Requires libcst.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import libcst as cst
from libcst.metadata import MetadataWrapper, PositionProvider

COMPOUND = (cst.If, cst.Try, cst.With, cst.For, cst.While, cst.Else, cst.Finally,
            cst.ExceptHandler, cst.IndentedBlock)
TRY_STAR = getattr(cst, "TryStar", None)
MATCH = getattr(cst, "Match", None)
TYPE_ALIAS = getattr(cst, "TypeAlias", None)
EXTRA_COMPOUND = tuple(t for t in (TRY_STAR, MATCH, getattr(cst, "MatchCase", None),
                                   getattr(cst, "ExceptStarHandler", None)) if t is not None)
BLOCK_TYPES = (cst.If, cst.Try, cst.With, cst.For, cst.While) + EXTRA_COMPOUND


def dotted(node) -> str:
    if isinstance(node, cst.Name):
        return node.value
    if isinstance(node, cst.Attribute):
        return f"{dotted(node.value)}.{node.attr.value}"
    return "?"


def facts(source: bytes):
    module = cst.parse_module(source)
    wrapper = MetadataWrapper(module, unsafe_skip_copy=True)
    positions = wrapper.resolve(PositionProvider)
    defs, imps = [], []

    def line_of(node):
        return positions[node].start.line

    def end_of(node):
        return positions[node].end.line

    def walk(node, chain, kinds, in_block):
        for child in node.children:
            if isinstance(child, (cst.FunctionDef, cst.ClassDef)):
                if isinstance(child, cst.ClassDef):
                    kind, tag = "class", "c"
                else:
                    kind = "async def" if child.asynchronous is not None else "def"
                    tag = "d"
                names = chain + [child.name.value]
                defs.append({"q": ".".join(names), "k": kind, "l": line_of(child.name),
                             "e": end_of(child), "c": None, "d": len(child.decorators),
                             "b": int(in_block), "a": ".".join(kinds)})
                walk(child, names, kinds + [tag], False)
            elif TYPE_ALIAS is not None and isinstance(child, TYPE_ALIAS):
                defs.append({"q": ".".join(chain + [child.name.value]), "k": "type",
                             "l": line_of(child), "e": end_of(child), "c": None, "d": 0,
                             "b": int(in_block), "a": ".".join(kinds)})
            elif isinstance(child, cst.Import):
                line = line_of(child)
                for alias in child.names:
                    asname = alias.asname.name.value if alias.asname is not None else ""
                    imps.append(["import", dotted(alias.name), asname, line])
            elif isinstance(child, cst.ImportFrom):
                line = line_of(child)
                module_name = dotted(child.module) if child.module is not None else ""
                module_text = "." * len(child.relative) + module_name
                if isinstance(child.names, cst.ImportStar):
                    imps.append(["from", module_text, "*", "", line])
                else:
                    for alias in child.names:
                        asname = alias.asname.name.value if alias.asname is not None else ""
                        imps.append(["from", module_text, dotted(alias.name), asname, line])
            elif isinstance(child, BLOCK_TYPES):
                walk(child, chain, kinds, True)
            else:
                walk(child, chain, kinds, in_block)

    walk(module, [], [], False)
    return defs, imps


def parse_one(data: bytes) -> dict:
    started = time.perf_counter()
    try:
        defs, imps = facts(data)
    except cst.ParserSyntaxError as error:
        return {"ok": False, "t": time.perf_counter() - started, "defs": [], "imps": [],
                "err": {"type": "ParserSyntaxError", "msg": str(error).splitlines()[0][:160],
                        "line": getattr(error, "raw_line", None)}}
    except Exception as error:  # noqa: BLE001
        return {"ok": False, "t": time.perf_counter() - started, "defs": [], "imps": [],
                "err": {"type": type(error).__name__, "msg": str(error)[:160], "line": None}}
    return {"ok": True, "t": time.perf_counter() - started, "defs": defs, "imps": imps}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--list", type=Path)
    ap.add_argument("--features", action="store_true")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    sys.setrecursionlimit(10000)
    try:
        from importlib.metadata import version
        lib_version = version("libcst")
    except Exception:  # noqa: BLE001
        lib_version = "?"

    with args.out.open("w", encoding="utf-8") as sink:
        sink.write(json.dumps({"meta": True, "engine": "libcst", "version": lib_version,
                               "python": sys.version.split()[0]}) + "\n")
        if args.features:
            sys.path.insert(0, str(Path(__file__).resolve().parent))
            from features import FEATURES
            for case in FEATURES:
                record = parse_one(case["source"].encode(case.get("enc", "utf-8")))
                record["f"] = case["id"]
                sink.write(json.dumps(record) + "\n")
            return 0
        for line in args.list.read_text(encoding="utf-8").splitlines():
            path = line.strip()
            if not path:
                continue
            try:
                data = Path(path).read_bytes()
            except OSError as error:
                record = {"ok": False, "t": 0.0, "defs": [], "imps": [],
                          "err": {"type": "OSError", "msg": str(error)[:160], "line": None}}
            else:
                record = parse_one(data)
                record["h"] = hashlib.sha256(data).hexdigest()[:16]
            record["f"] = path
            sink.write(json.dumps(record) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
