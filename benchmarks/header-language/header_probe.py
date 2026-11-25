"""Parses a header with the C, C++ and Objective-C grammars and returns the features `header_routes` decides on.

Daodan's own loader gives the C and C++ parsers (`languages._treesitter.get_parser`: the pinned pack release, in Daodan's
cache); the Objective-C grammar is the pack's, which the same pack configuration serves (Daodan has no alias for it).
A query that does not compile raises: `languages._treesitter.query_captures` answers `{}` on any failure, which would
make a misspelled node name read as "no C++ anywhere".
"""
from __future__ import annotations

import bisect
import sys
import time

import header_patterns as patterns
import header_routes as routes

_COMMON = "(ERROR) @err\n(MISSING) @missing\n"
_CPP_SYNTHETIC = """
(class_specifier body: (_)) @class_with_body
(struct_specifier body: (field_declaration_list (function_definition))) @struct_fn_def
(struct_specifier body: (field_declaration_list (field_declaration declarator: (function_declarator declarator: (field_identifier))))) @struct_fn_decl
(enum_specifier "class") @enum_class
(preproc_ifdef) @guard
(preproc_if) @guard
"""
_OBJC_SYNTHETIC = '(preproc_include "#import") @import_directive\n'


def _named(kinds) -> str:
    return "".join(f"({kind}) @{kind}\n" for kind in sorted(kinds))


def _ms(start: int, end: int) -> float:
    return (end - start) / 1e6


class Probe:
    """The parsers and the compiled queries of one process; `core_dir` is the folder of Daodan's `languages` package."""

    def __init__(self, core_dir: str):
        if core_dir not in sys.path:
            sys.path.insert(0, core_dir)
        import tree_sitter_language_pack as pack
        from tree_sitter import Query, QueryCursor
        from languages import _treesitter, get_adapter

        self._cursor = QueryCursor
        self._adapter = get_adapter
        self.parsers = {}
        for grammar in ("c", "cpp"):
            pair = _treesitter.get_parser(grammar)
            if pair is None:
                raise RuntimeError(f"no {grammar} grammar: {_treesitter.load_failure(grammar)}")
            self.parsers[grammar] = pair
        objc = pack.get_parser("objc")  # after Daodan's `get_parser`, which configures the pack on its pinned cache
        self.parsers["objc"] = (objc, objc.language)
        text = {"c": _COMMON,
                "cpp": _COMMON + _named(routes.CPP_ONLY_NAMED) + _CPP_SYNTHETIC,
                "objc": _COMMON + _named(routes.OBJC_EXT - {"import_directive"}) + _OBJC_SYNTHETIC}
        self.queries = {g: Query(self.parsers[g][1], text[g]) for g in routes.GRAMMARS}  # raises on a bad pattern

    def _part(self, grammar: str, src: bytes) -> dict:
        parser, _ = self.parsers[grammar]
        t0 = time.perf_counter_ns()
        root = parser.parse(src).root_node
        t1 = time.perf_counter_ns()
        caps = self._cursor(self.queries[grammar]).captures(root)
        errors, missing = caps.get("err", []), caps.get("missing", [])
        part = {"ms": _ms(t0, t1), "err": len(errors), "missing": len(missing),
                "err_bytes": routes.union_length((n.start_byte, n.end_byte) for n in errors),
                "err_line": min((n.start_point[0] + 1 for n in errors + missing), default=0)}
        if grammar != "c":
            guards = _guard_spans(caps.get("guard", [])) if grammar == "cpp" else ([], [])
            part["kinds"] = {kind: [len(nodes), sum(1 for n in nodes if not _inside(guards, n.start_byte)),
                                    min(n.start_point[0] for n in nodes) + 1]
                             for kind, nodes in caps.items() if kind not in ("err", "missing", "guard")}
        part["q_ms"] = _ms(t1, time.perf_counter_ns())
        return part

    def features(self, src: bytes) -> dict:
        return {"size": len(src), **{g: self._part(g, src) for g in routes.GRAMMARS}}

    def r0(self, content: str) -> tuple[str, float]:
        """R0 of the results in `results/`: the rule the product had until route R3dx took its place (`fixqc`, frozen in
        `header_patterns`), as `r0_variant` runs it: its answer (None, which is Objective-C, as "objc") and ms. The product's own
        answer is `languages.detect_language`, which `modal_headers.py --step product` runs."""
        return self.r0_variant(content, "fixqc")

    def r0_variant(self, content: str, variant: str) -> tuple[str, float]:
        """A candidate for the rule before (`header_patterns.VARIANTS`: fix, fixq, fixqc), timed as `r0` is. The patterns are
        written in full there and checked against the product's by the tests, not made from them here."""
        t0 = time.perf_counter_ns()
        answer = patterns.answer(content, variant)
        return answer, _ms(t0, time.perf_counter_ns())

    def symbols(self, content: str, language: str) -> int:
        """How many definitions Daodan's adapter of `language` extracts from the header."""
        result = self._adapter(language).parse(content, "x.h")
        return (len(result.functions) + len(result.nested) + sum(1 + len(c.methods) for c in result.classes))


def _guard_spans(nodes) -> tuple[list[int], list[int]]:
    """The merged (starts, ends) of the `#if` blocks whose own line names `__cplusplus`."""
    spans = []
    for node in nodes:
        head = node.child_by_field_name("name" if node.type == "preproc_ifdef" else "condition")
        if head is not None and b"__cplusplus" in head.text:
            spans.append((node.start_byte, node.end_byte))
    merged: list[list[int]] = []
    for start, end in sorted(spans):
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return [s for s, _ in merged], [e for _, e in merged]


def _inside(guards: tuple[list[int], list[int]], byte: int) -> bool:
    starts, ends = guards
    i = bisect.bisect_right(starts, byte) - 1
    return i >= 0 and byte < ends[i]
