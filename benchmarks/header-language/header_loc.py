"""The lines of code each way of choosing a `.h` language would put in the product, counted from the benchmark code that
is tested (`header_probe`, `header_routes`) and from the rule of today (`daodan/core/languages/__init__.py`). Standard
library only.

    python benchmarks/header-language/header_loc.py [--out results/loc.json]

A line counts when it holds code: not blank, not a comment, not a docstring. The benchmark functions carry a few lines
the product would not (the timing of a parse); they are counted whole, so each figure is a ceiling for its piece.
"""
from __future__ import annotations

import argparse
import ast
import io
import json
import tokenize
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
TODAY = REPO / "daodan" / "core" / "languages" / "__init__.py"
SKIP = {tokenize.COMMENT, tokenize.NL, tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT, tokenize.ENDMARKER, tokenize.ENCODING}


def code_lines(source: str) -> set[int]:
    """The 1-based numbers of the lines of `source` that hold code."""
    lines = set()
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type not in SKIP:
            lines.update(range(token.start[0], token.end[0] + 1))
    for node in ast.walk(ast.parse(source)):  # a docstring is a string statement that opens a body
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.ClassDef)) and node.body:
            first = node.body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
                lines.difference_update(range(first.lineno, first.end_lineno + 1))
    return lines


def span(source: str, name: str) -> tuple[int, int]:
    """The first and last line of a top-level definition or assignment, or of `Class.method`."""
    scope, _, member = name.partition(".")
    for node in ast.parse(source).body:
        targets = [t.id for t in node.targets if isinstance(t, ast.Name)] if isinstance(node, ast.Assign) else \
            [node.target.id] if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) else \
            [node.name] if isinstance(node, (ast.FunctionDef, ast.ClassDef)) else []
        if scope in targets:
            if not member:
                return node.lineno, node.end_lineno
            for inner in node.body:
                if isinstance(inner, ast.FunctionDef) and inner.name == member:
                    return inner.lineno, inner.end_lineno
    raise KeyError(name)


def count(path: Path, names: list[str] | None = None, ranges: list[tuple[int, int]] | None = None) -> int:
    """Lines of code in the named definitions of a file, or in explicit (first, last) line ranges."""
    source = path.read_text(encoding="utf-8")
    wanted = ranges if ranges is not None else [span(source, name) for name in names or []]
    holding = code_lines(source)
    return sum(1 for n in holding if any(first <= n <= last for first, last in wanted))


# What each route needs of the benchmark code, by file. A route's pieces are the node lists it reads, the queries it
# compiles, the guard of `#ifdef __cplusplus`, the decision, and, for the routes on a grammar, the check before the parse.
PROBE, ROUTES = HERE / "header_probe.py", HERE / "header_routes.py"
CHECK = ["open_comment_start", "_skip_quoted", "safe_prefix"]  # the linear look for a `/*` left open, then a cut before it
PIECES = {
    "R1": {PROBE: ["_CPP_SYNTHETIC", "_named", "_guard_spans", "_inside", "Probe._part"],
           ROUTES: ["SYNTHETIC_CPP", "CPP_DECL", "CPP_EXT", "_found", "_r1"]},
    "R1_objc": {PROBE: ["_OBJC_SYNTHETIC"], ROUTES: ["OBJC_DECL", "OBJC_EXT"]},  # added to R1 by the `o` variants
    "R2": {PROBE: ["_COMMON", "Probe._part"], ROUTES: ["_score", "_r2"]},
    "R3": {ROUTES: ["_r3"]},  # on top of R1 and R2
    "guard": {PROBE: ["_guard_spans", "_inside"]},  # what a route with no guard (`R1d`, `R1e`) does without
    "x": {ROUTES: ["_x"]},  # today's Objective-C rule in front
    "check": {ROUTES: CHECK},
}


def today_ranges(source: str) -> tuple[list[tuple[int, int]], tuple[int, int], list[tuple[int, int]]]:
    """The lines of today's `.h` rule: its three constants, and the `if suffix == ".h"` block of `detect_language`; the
    lines of the whole detection part, from the top of the file to the end of `detect_language`; and the lines of the
    Objective-C half of the rule (the noise constant, the Objective-C constant, the block's `if`, its `code =` line and the
    `if` that answers Objective-C). A product that moves the rule changes none of these silently: this raises."""
    constants = {name: span(source, name) for name in ("_C_NOISE_RE", "_CPP_HEADER_RE", "_OBJC_HEADER_RE")}
    first, last = span(source, "detect_language")
    blocks = [node for node in ast.walk(ast.parse(source))
              if isinstance(node, ast.If) and first <= node.lineno <= last and '".h"' in ast.get_source_segment(source, node.test)]
    if len(blocks) != 1:
        raise ValueError(f"expected one `.h` block in detect_language, found {len(blocks)}: the rule moved, so does this count")
    block = blocks[0]
    code, objc_if = (block.body + [None, None])[:2]
    if not (isinstance(code, ast.Assign) and isinstance(objc_if, ast.If) and "_OBJC_HEADER_RE" in ast.get_source_segment(source, objc_if.test)):
        raise ValueError("the `.h` block no longer starts with `code = ...` and the Objective-C `if`")
    objc = [constants["_C_NOISE_RE"], constants["_OBJC_HEADER_RE"], (block.lineno, block.lineno), (code.lineno, code.end_lineno),
            (objc_if.lineno, objc_if.end_lineno)]
    return [*constants.values(), (block.lineno, block.end_lineno)], (1, last), objc


def measure() -> dict:
    source = TODAY.read_text(encoding="utf-8")
    today_h, detection, today_objc = today_ranges(source)
    out = {"today": {"h_rule": count(TODAY, ranges=today_h), "h_rule_ranges": today_h, "objc_rule": count(TODAY, ranges=today_objc),
                     "detection": count(TODAY, ranges=[detection]), "detection_range": detection}}
    for name, files in PIECES.items():
        out[name] = {path.name: {item: count(path, [item]) for item in items} for path, items in files.items()}
        out[name]["total"] = sum(count(path, items) for path, items in files.items())
    # `_part` serves R1 and R2 both: a route that needs both counts it once
    part = count(PROBE, ["Probe._part"])
    out["totals"] = {"R0": out["today"]["h_rule"], "R1": out["R1"]["total"], "R2": out["R2"]["total"],
                     "R1+objc": out["R1"]["total"] + out["R1_objc"]["total"],
                     "R2+objc": out["R2"]["total"],  # a third grammar adds a parse, no code
                     "R3": out["R1"]["total"] + out["R2"]["total"] - part + out["R3"]["total"],
                     "check": out["check"]["total"],
                     # with today's Objective-C rule in front: the tree route, without a guard where it has none, the `x` and the rule
                     "R1x": out["R1"]["total"] - out["guard"]["total"] + out["x"]["total"] + out["today"]["objc_rule"],
                     "R3x": out["R1"]["total"] + out["R2"]["total"] - part + out["R3"]["total"] + out["x"]["total"] + out["today"]["objc_rule"]}
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(HERE / "results" / "loc.json"))
    args = parser.parse_args()
    result = measure()
    Path(args.out).write_text(json.dumps(result, indent=1), encoding="utf-8")
    print(f"wrote {args.out}: {result['totals']}")


if __name__ == "__main__":
    main()
