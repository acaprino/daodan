#!/usr/bin/env python3
"""Parse files with the RUNNING interpreter's stdlib ast and emit canonical facts.

This worker is launched once per CPython version under test (3.11 to 3.14), so
the same bytes are parsed by every interpreter a host might use to run the
Codebase Map. It is stdlib only and written without any syntax newer than 3.11,
because the oldest interpreter under test has to be able to run it.

The facts emitted are deliberately parser-neutral, so the other workers can emit
the same shape and the outputs can be compared line by line:

    q  qualified name: the chain of enclosing class/def names, joined by "."
    k  kind: "class", "def", "async def" or "type" (PEP 695 alias)
    l  line of the def/class/async/type keyword (decorators excluded)
    e  last line of the definition
    c  column of that keyword, in UTF-8 bytes
    d  number of decorators
    b  1 when the definition sits inside a compound statement (if/try/with/
       for/while/match) relative to its nearest module/class/def container
    a  kinds of the enclosing definitions, outermost first ("c" class, "d" def)

When the file is rejected, `salvage` records the stdlib-only recovery policy
measured beside tree-sitter's: keep every complete top-level statement before
the first syntax error, by re-parsing the longest prefix that ends on a
top-level statement boundary. Whatever it returns is the CPython grammar's own
reading of unchanged lines.

Walkers are iterative: a deep expression in third-party code must not crash the
measuring process.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import io
import json
import sys
import time
import tokenize
from pathlib import Path

TYPE_ALIAS = getattr(ast, "TypeAlias", None)
DEF_TYPES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
SALVAGE_ATTEMPTS = 200


def definitions(tree: ast.AST) -> list:
    out = []
    stack = [(child, [], [], False) for child in reversed(list(ast.iter_child_nodes(tree)))]
    while stack:
        node, chain, kinds, in_block = stack.pop()
        if isinstance(node, DEF_TYPES):
            if isinstance(node, ast.ClassDef):
                kind, tag = "class", "c"
            elif isinstance(node, ast.AsyncFunctionDef):
                kind, tag = "async def", "d"
            else:
                kind, tag = "def", "d"
            names = chain + [node.name]
            out.append({"q": ".".join(names), "k": kind, "l": node.lineno, "e": node.end_lineno,
                        "c": node.col_offset, "d": len(node.decorator_list), "b": int(in_block),
                        "a": ".".join(kinds)})
            children = [(c, names, kinds + [tag], False) for c in ast.iter_child_nodes(node)]
        elif TYPE_ALIAS is not None and isinstance(node, TYPE_ALIAS):
            name = node.name.id if isinstance(node.name, ast.Name) else "?"
            out.append({"q": ".".join(chain + [name]), "k": "type", "l": node.lineno,
                        "e": node.end_lineno, "c": node.col_offset, "d": 0, "b": int(in_block),
                        "a": ".".join(kinds)})
            children = []
        elif isinstance(node, ast.stmt):
            # A statement that is not a definition holds definitions only when it
            # is compound (if/try/with/for/while/match).
            children = [(c, chain, kinds, True) for c in ast.iter_child_nodes(node)]
        else:
            children = [(c, chain, kinds, in_block) for c in ast.iter_child_nodes(node)]
        stack.extend(reversed(children))
    return out


def imports(tree: ast.AST) -> list:
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                out.append(["import", alias.name, alias.asname or "", node.lineno])
        elif isinstance(node, ast.ImportFrom):
            module = "." * (node.level or 0) + (node.module or "")
            for alias in node.names:
                out.append(["from", module, alias.name, alias.asname or "", node.lineno])
    return out


def decode(data: bytes) -> str:
    encoding, _ = tokenize.detect_encoding(io.BytesIO(data).readline)
    return data.decode(encoding, errors="replace")


def salvage(data: bytes, error_line) -> dict:
    """Longest prefix ending on a top-level statement boundary that still parses."""
    try:
        lines = decode(data).splitlines(keepends=True)
    except (SyntaxError, LookupError, UnicodeDecodeError) as error:
        return {"cut": None, "attempts": 0, "defs": [], "note": f"undecodable: {error}"[:120]}
    limit = len(lines) if not error_line else min(len(lines), max(error_line - 1, 0))
    attempts = 0
    for cut in range(limit, -1, -1):
        if cut and cut < len(lines):
            first_excluded = lines[cut]
            if not first_excluded[:1].strip() or first_excluded.startswith("#"):
                continue
        attempts += 1
        if attempts > SALVAGE_ATTEMPTS:
            return {"cut": None, "attempts": attempts - 1, "defs": [], "note": "attempt limit"}
        try:
            tree = ast.parse("".join(lines[:cut]))
        except (SyntaxError, ValueError, RecursionError, MemoryError):
            continue
        return {"cut": cut, "attempts": attempts, "defs": definitions(tree)}
    return {"cut": 0, "attempts": attempts, "defs": []}


def parse_one(data: bytes) -> dict:
    started = time.perf_counter()
    try:
        tree = ast.parse(data)
    except (SyntaxError, ValueError, RecursionError, MemoryError, OverflowError) as error:
        elapsed = time.perf_counter() - started
        line = getattr(error, "lineno", None)
        record = {"ok": False, "t": elapsed,
                  "err": {"type": type(error).__name__,
                          "msg": (getattr(error, "msg", None) or str(error))[:160], "line": line}}
        if isinstance(error, SyntaxError):
            record["salvage"] = salvage(data, line)
        return record
    elapsed = time.perf_counter() - started
    return {"ok": True, "t": elapsed, "defs": definitions(tree), "imps": imports(tree)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--list", type=Path)
    ap.add_argument("--features", action="store_true")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    with args.out.open("w", encoding="utf-8") as sink:
        sink.write(json.dumps({"meta": True, "engine": "ast",
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
                record = {"ok": False, "t": 0.0,
                          "err": {"type": "OSError", "msg": str(error)[:160], "line": None}}
            else:
                record = parse_one(data)
                record["h"] = hashlib.sha256(data).hexdigest()[:16]
            record["f"] = path
            sink.write(json.dumps(record) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
