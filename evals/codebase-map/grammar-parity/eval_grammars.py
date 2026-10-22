"""Grammar-parity gate: named invariants over Oracle PL/SQL and PostgreSQL parsing.

This is a mechanical gate, not an agent-scored case. It exists because the
Oracle PL/SQL engine the resolver layer depends on is a third-party grammar
that publishes no tests of its own, sits close to a self-declared state budget
whose overflow misparses silently, and reaches us only as an optional probed
dependency. Without this file nothing would notice a version of that grammar
starting to parse real code incorrectly.

Several cases below are INVERTED PINS: they assert that a known gap still
fails. They fail loudly the day the gap is fixed, on purpose, so that a fix is
re-measured and the claim updated instead of quietly drifting. Do not "fix" an
inverted pin by weakening or deleting it; update the expectation and record the
re-measurement in RESULTS.md.

Engines are probed, never assumed. When the optional Oracle grammar is absent
its cases report SKIP with the install command, following the precedent of
tests/test_xray_scripts.py, which runs the tree-sitter path wherever it is
installed. A SKIP is not a pass and is counted separately in the summary.

Usage:
    python eval_grammars.py                 # probe, run what can run
    python eval_grammars.py --json out.json # also write machine-readable results
    python eval_grammars.py --with-build    # additionally check the abi3 wheel recipe
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from corpus import (  # noqa: E402
    EXPECTED_CALLS_IN_PACKAGE_BODY,
    EXPECTED_FALSE_CALLS_IN_PACKAGE_BODY,
    FILES,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_SCRIPTS = REPO_ROOT / "plugins" / "codebase-map" / "skills" / "map-method" / "scripts"

PLSQL_INSTALL = (
    "pip install git+https://github.com/njank/tree-sitter-plsql "
    "(needs a C compiler: MSVC Build Tools on Windows, build-essential on Debian/Ubuntu)"
)

PASS, FAIL, SKIP = "pass", "fail", "skip"


@dataclass
class Result:
    case_id: str
    requirement: str
    verdict: str
    detail: str
    evidence: list = field(default_factory=list)


# ---------------------------------------------------------------- engine probe

class Engines:
    def __init__(self) -> None:
        self.plsql = None
        self.sql = None
        self.plsql_reason = ""
        self.sql_reason = ""
        self.versions: dict[str, str] = {}
        try:
            import tree_sitter_plsql  # noqa: PLC0415
            from tree_sitter import Language, Parser  # noqa: PLC0415
            self.plsql = Parser(Language(tree_sitter_plsql.language()))
            self.versions["tree_sitter_plsql"] = getattr(tree_sitter_plsql, "__version__", "unknown")
        except Exception as error:  # noqa: BLE001
            self.plsql_reason = f"{type(error).__name__}: {error}"
        try:
            import tree_sitter_sql  # noqa: PLC0415
            from tree_sitter import Language, Parser  # noqa: PLC0415
            self.sql = Parser(Language(tree_sitter_sql.language()))
            self.versions["tree_sitter_sql"] = getattr(tree_sitter_sql, "__version__", "unknown")
        except Exception as error:  # noqa: BLE001
            self.sql_reason = f"{type(error).__name__}: {error}"
        try:
            import tree_sitter  # noqa: PLC0415
            self.versions["tree_sitter"] = getattr(tree_sitter, "__version__", "unknown")
        except Exception:  # noqa: BLE001
            pass

    def available(self) -> list[str]:
        return [n for n, p in (("njank-plsql", self.plsql), ("derekstride-sql", self.sql)) if p]


def parse(parser, source: str):
    raw = source.encode("utf-8")
    return parser.parse(raw), raw


def text_of(node, raw: bytes) -> str:
    return raw[node.start_byte:node.end_byte].decode("utf-8", "replace")


def has_error(tree) -> bool:
    return tree.root_node.has_error


def error_spans(tree, raw: bytes, limit: int = 6) -> list[str]:
    out, stack = [], [tree.root_node]
    while stack and len(out) < limit:
        node = stack.pop()
        if node.type == "ERROR" or node.is_missing:
            out.append(f"{node.start_point[0]+1}:{node.start_point[1]} {text_of(node, raw)[:44]!r}")
            continue
        stack.extend(node.children)
    return sorted(out)


def collect_types(root) -> set[str]:
    types, stack = set(), [root]
    while stack:
        node = stack.pop()
        if node.is_named:
            types.add(node.type)
        stack.extend(node.children)
    return types


def collect_nodes(root, wanted: set[str]) -> list:
    out, stack = [], [root]
    while stack:
        node = stack.pop()
        if node.type in wanted:
            out.append(node)
        stack.extend(node.children)
    return out


def ref_call_texts(parser, source: str) -> list[str]:
    tree, raw = parse(parser, source)
    return sorted({" ".join(text_of(n, raw).split()) for n in collect_nodes(tree.root_node, {"ref_call"})})


def adapters():
    """The repository's own regex adapters, imported from the plugin scripts."""
    sys.path.insert(0, str(PLUGIN_SCRIPTS))
    from languages import plsql as plsql_adapter  # noqa: PLC0415
    from languages import sql as sql_adapter  # noqa: PLC0415
    return {"regex-sql": sql_adapter.adapter, "regex-plsql": plsql_adapter.adapter}


# ------------------------------------------------------------------------ cases

def g1_call_nodes(eng: Engines) -> Result:
    """MUST: a package body yields structured, dotted call nodes with real recall."""
    if not eng.plsql:
        return Result("G1", "MUST", SKIP, f"oracle grammar absent: {eng.plsql_reason}")
    calls = ref_call_texts(eng.plsql, FILES["02_pkg_body.pkb"])
    joined = "\n".join(calls)
    missing = [c for c in EXPECTED_CALLS_IN_PACKAGE_BODY if c.split(".")[-1] not in joined
               and c not in joined]
    if missing:
        return Result("G1", "MUST", FAIL, f"expected calls not found: {missing}", calls)
    if len(calls) < len(EXPECTED_CALLS_IN_PACKAGE_BODY):
        return Result("G1", "MUST", FAIL,
                      f"only {len(calls)} ref_call nodes, expected >= {len(EXPECTED_CALLS_IN_PACKAGE_BODY)}",
                      calls)
    dotted = [c for c in calls if "." in c.split("(")[0]]
    return Result("G1", "MUST", PASS,
                  f"{len(calls)} ref_call nodes, {len(dotted)} dotted cross-unit calls, "
                  f"all {len(EXPECTED_CALLS_IN_PACKAGE_BODY)} hand-counted calls present", calls)


def g2_keyword_identifiers(eng: Engines) -> Result:
    """MUST: non-reserved Oracle keywords inside identifiers are not split."""
    if not eng.plsql:
        return Result("G2", "MUST", SKIP, f"oracle grammar absent: {eng.plsql_reason}")
    tree, raw = parse(eng.plsql, FILES["04_keyword_traps.sql"])
    if has_error(tree):
        return Result("G2", "MUST", FAIL, f"error nodes: {error_spans(tree, raw)}")
    return Result("G2", "MUST", PASS,
                  "LoopContacts / outer / level_id / newPeriod / ordernr / \"comment\" parse clean")


def g3_quoted_identifier_escape(eng: Engines) -> Result:
    """MUST: doubled quotes inside a quoted identifier parse clean."""
    if not eng.plsql:
        return Result("G3", "MUST", SKIP, f"oracle grammar absent: {eng.plsql_reason}")
    tree, raw = parse(eng.plsql, FILES["10_quoted_identifiers.sql"])
    if has_error(tree):
        return Result("G3", "MUST", FAIL, f"error nodes: {error_spans(tree, raw)}")
    return Result("G3", "MUST", PASS, '"sales data"."order""items" and t."a""b" parse clean')


def g4_declarations_typed(eng: Engines) -> Result:
    """MUST: each Oracle object kind gets its own named node, not a generic statement."""
    if not eng.plsql:
        return Result("G4", "MUST", SKIP, f"oracle grammar absent: {eng.plsql_reason}")
    expected = {
        "01_pkg_spec.pks": "create_package",
        "02_pkg_body.pkb": "create_package_body",
        "03_object_type.sql": "create_type_body",
        "06_trigger.sql": "create_trigger",
    }
    found, missing = {}, []
    for fname, node_type in expected.items():
        tree, _ = parse(eng.plsql, FILES[fname])
        types = collect_types(tree.root_node)
        found[fname] = node_type in types
        if node_type not in types:
            missing.append(f"{fname}: expected {node_type}")
    tree, _ = parse(eng.plsql, FILES["03_object_type.sql"])
    if "create_type" not in collect_types(tree.root_node):
        missing.append("03_object_type.sql: expected create_type")
    if missing:
        return Result("G4", "MUST", FAIL, "; ".join(missing), [found])
    return Result("G4", "MUST", PASS,
                  "create_package / create_package_body / create_type / create_type_body / "
                  "create_trigger all present", [found])


DECLARED_GAP_CASES = {
    "LISTAGG(DISTINCT ...)": "SELECT LISTAGG(DISTINCT s, ',') WITHIN GROUP (ORDER BY s) FROM t;\n",
    "@dblink in FROM": "SELECT * FROM t@link;\n",
    "@dblink in a call": "SELECT pkg.fn@link(1) FROM dual;\n",
    "Oracle-wrapped body": FILES["07_wrapped_body.sql"],
}

UNDECLARED_GAP_CASES = {
    "KEEP (DENSE_RANK ...) OVER (...)":
        "SELECT AVG(salary) KEEP (DENSE_RANK FIRST ORDER BY hire_date) "
        "OVER (PARTITION BY dept) FROM e;\n",
    "PIPELINED in a function signature":
        "CREATE OR REPLACE FUNCTION f PIPELINED RETURN t_tab AS\nBEGIN RETURN;\nEND;\n/\n",
    "WITH FUNCTION (12c inline)":
        "WITH FUNCTION g(x NUMBER) RETURN NUMBER IS BEGIN RETURN x*2; END;\nSELECT g(id) FROM t;\n/\n",
    "$IF with a $$inquiry directive":
        "CREATE OR REPLACE PACKAGE p AS\n $IF $$DBG $THEN\n PROCEDURE dbg;\n $END\nEND p;\n/\n",
}


def _inverted_pin(case_id: str, label: str, cases: dict[str, str], eng: Engines) -> Result:
    if not eng.plsql:
        return Result(case_id, "MUST", SKIP, f"oracle grammar absent: {eng.plsql_reason}")
    still_failing, now_clean = [], []
    for name, source in cases.items():
        tree, raw = parse(eng.plsql, source)
        (still_failing if has_error(tree) else now_clean).append(
            name if has_error(tree) else f"{name} -> CLEAN {error_spans(tree, raw) or ''}")
    if now_clean:
        return Result(case_id, "MUST", FAIL,
                      f"{label}: these gaps no longer fail, re-measure and update RESULTS.md: "
                      f"{now_clean}", [still_failing])
    return Result(case_id, "MUST", PASS,
                  f"{label}: all {len(still_failing)} pinned gaps still fail as documented",
                  [still_failing])


def g5_declared_gaps(eng: Engines) -> Result:
    """MUST (inverted pin): the gaps the grammar's own README declares are still open."""
    return _inverted_pin("G5", "declared gaps", DECLARED_GAP_CASES, eng)


def g6_undeclared_gaps(eng: Engines) -> Result:
    """MUST (inverted pin): gaps found by measurement that the README does not declare."""
    return _inverted_pin("G6", "undeclared gaps", UNDECLARED_GAP_CASES, eng)


def g7_subscript_false_call(eng: Engines) -> Result:
    """MUST (inverted pin): a collection subscript is emitted as ref_call.

    A consumer must therefore separate subscripts from calls, or it will invent
    edges. Pinning the false positive keeps that obligation visible.
    """
    if not eng.plsql:
        return Result("G7", "MUST", SKIP, f"oracle grammar absent: {eng.plsql_reason}")
    calls = ref_call_texts(eng.plsql, FILES["02_pkg_body.pkb"])
    present = [c for c in calls if any(f in c for f in EXPECTED_FALSE_CALLS_IN_PACKAGE_BODY)]
    if not present:
        return Result("G7", "MUST", FAIL,
                      "collection subscript is no longer emitted as ref_call; if the grammar now "
                      "distinguishes subscripts, re-measure precision and update RESULTS.md", calls)
    return Result("G7", "MUST", PASS,
                  f"subscript still surfaces as a call ({present}); consumers must filter it", calls)


PLPGSQL_CONTROL = (
    "trivial body only",
    "CREATE FUNCTION f() RETURNS INT AS $$ BEGIN RETURN 1; END; $$ LANGUAGE plpgsql;\n",
)

# Realistic bodies. Every one of these is what a production PL/pgSQL function
# actually contains, and every one of them breaks the generic SQL grammar.
PLPGSQL_REAL_BODIES = {
    "+ DECLARE section": "CREATE FUNCTION f() RETURNS INT LANGUAGE plpgsql AS $$\nDECLARE\n x INT;\nBEGIN\n x := 1;\n RETURN x;\nEND;\n$$;\n",
    "+ %ROWTYPE": "CREATE FUNCTION f() RETURNS INT LANGUAGE plpgsql AS $$\nDECLARE\n r orders%ROWTYPE;\nBEGIN\n RETURN 1;\nEND;\n$$;\n",
    "+ IF/THEN": "CREATE FUNCTION f() RETURNS INT LANGUAGE plpgsql AS $$\nBEGIN\n IF 1 = 1 THEN\n RETURN 1;\n END IF;\n RETURN 0;\nEND;\n$$;\n",
    "+ EXCEPTION WHEN": "CREATE FUNCTION f() RETURNS INT LANGUAGE plpgsql AS $$\nBEGIN\n RETURN 1;\nEXCEPTION\n WHEN no_data_found THEN\n RETURN 0;\nEND;\n$$;\n",
    "+ RAISE EXCEPTION ... USING": "CREATE FUNCTION f() RETURNS INT LANGUAGE plpgsql AS $$\nBEGIN\n RAISE EXCEPTION 'x %', 1 USING ERRCODE = '22023';\n RETURN 0;\nEND;\n$$;\n",
    "+ PERFORM call": "CREATE FUNCTION f() RETURNS INT LANGUAGE plpgsql AS $$\nBEGIN\n PERFORM audit_write('CALC', 1);\n RETURN 0;\nEND;\n$$;\n",
    "anonymous DO block": "DO $$ BEGIN PERFORM 1; END $$;\n",
    "CREATE PROCEDURE plpgsql": "CREATE PROCEDURE p() LANGUAGE plpgsql AS $$\nBEGIN\n NULL;\nEND;\n$$;\n",
}


def g8_plpgsql_no_engine(eng: Engines) -> Result:
    """MUST (inverted pin): no available grammar parses a real PL/pgSQL body.

    This is the declared PostgreSQL gap. The trivial control body is deliberately
    excluded here, because G9 pins the fact that it parses clean; including it
    would make the two cases contradict each other. G8 fails the day any probed
    engine handles a realistic body, which is the signal to adopt that engine.
    """
    if not eng.available():
        return Result("G8", "MUST", SKIP, "no grammar installed at all")
    handled = []
    for name, source in PLPGSQL_REAL_BODIES.items():
        for engine_name in eng.available():
            parser = eng.plsql if engine_name == "njank-plsql" else eng.sql
            tree, _ = parse(parser, source)
            if not has_error(tree):
                handled.append(f"{engine_name} parses {name}")
    if handled:
        return Result("G8", "MUST", FAIL,
                      f"a grammar now handles PL/pgSQL, re-measure and adopt: {handled}")
    return Result("G8", "MUST", PASS,
                  f"no engine parses any of the {len(PLPGSQL_REAL_BODIES)} realistic PL/pgSQL "
                  "bodies; PostgreSQL procedural stays a declared gap")


def g9_dollar_quote_body_dependent(eng: Engines) -> Result:
    """MUST (pin): the generic SQL grammar's dollar-quote handling depends on the body.

    A trivial body parses clean; every realistic PL/pgSQL statement inside the
    same quotes produces an error located INSIDE the body. This pins the finding
    that dollar quoting is not uniformly opaque to that grammar, so a clean
    result on a toy body is not evidence of support.
    """
    if not eng.sql:
        return Result("G9", "MUST", SKIP, f"tree-sitter-sql absent: {eng.sql_reason}")
    trivial = PLPGSQL_CONTROL[1]
    tree, raw = parse(eng.sql, trivial)
    if has_error(tree):
        return Result("G9", "MUST", FAIL,
                      f"the trivial body no longer parses clean: {error_spans(tree, raw)}")
    real = PLPGSQL_REAL_BODIES
    still_clean = []
    for name, source in real.items():
        tree, raw = parse(eng.sql, source)
        if not has_error(tree):
            still_clean.append(name)
    if still_clean:
        return Result("G9", "MUST", FAIL,
                      f"these bodies now parse clean, re-measure: {still_clean}")
    return Result("G9", "MUST", PASS,
                  f"trivial body clean, all {len(real)} realistic bodies ERROR inside the quotes")


def g10_nested_block_comment(eng: Engines) -> Result:
    """MUST (pin): PostgreSQL-legal nested block comments are unhandled by both."""
    source = "/* outer /* nested */ still comment */\nCREATE TABLE t (id INT);\n"
    checked, failing = [], []
    for engine_name in eng.available():
        parser = eng.plsql if engine_name == "njank-plsql" else eng.sql
        tree, _ = parse(parser, source)
        checked.append(engine_name)
        if has_error(tree):
            failing.append(engine_name)
    if not checked:
        return Result("G10", "MUST", SKIP, "no grammar installed")
    if len(failing) != len(checked):
        clean = [c for c in checked if c not in failing]
        return Result("G10", "MUST", FAIL,
                      f"nested block comments now handled by {clean}; re-measure")
    return Result("G10", "MUST", PASS,
                  f"nested block comments still fail under {', '.join(failing)}")


def g11_regex_classifies_effects_not_edges(eng: Engines) -> Result:
    """MUST: the repository's PL/SQL adapter yields declarations and effect kinds, never caller to callee pairs.

    `external_calls` is an effects taxonomy (database / network / filesystem /
    messaging / ipc) feeding the effect digest, not a call graph. On a package
    body it reports where DML happens and says nothing about which routine calls
    which. This pins that distinction with the hand-counted ground truth from
    corpus.py, so "the adapter already extracts calls" cannot be assumed again.
    """
    try:
        ad = adapters()
    except Exception as error:  # noqa: BLE001
        return Result("G11", "MUST", SKIP, f"plugin adapters not importable: {error}")
    result = ad["regex-plsql"].parse(FILES["02_pkg_body.pkb"], "02_pkg_body.pkb")
    problems = []
    if not result.classes:
        problems.append("no classes extracted")
    if not result.functions:
        problems.append("no functions extracted")
    if result.semantic is not None:
        problems.append("semantic unexpectedly populated")
    label = (result.notes[0] if result.notes else "")
    if label != "parser=regex (plsql)":
        problems.append(f"notes[0] is {label!r}, expected 'parser=regex (plsql)'")

    kinds = {(c.call_type, c.pattern) for c in result.external_calls}
    if kinds and kinds != {("database", "sql-dml")}:
        problems.append(f"external_calls carries non-DML kinds: {sorted(kinds)}")

    # A cross-unit edge is recoverable only if the CALLEE is recoverable. The
    # receiver package of a dotted call can never be a declaration in this file,
    # so its presence anywhere in the result would mean the adapter found the
    # edge. A bare name like `get_order_total` legitimately appears as a
    # declaration and is therefore not evidence of a recovered call.
    receivers = sorted({c.split(".")[0] for c in EXPECTED_CALLS_IN_PACKAGE_BODY if "." in c})
    full_blob = json.dumps({
        "classes": [[c.name, getattr(c, "kind", "")] for c in result.classes],
        "functions": [f.name for f in result.functions],
        "imports": [[i.module, i.names] for i in result.imports],
        "external_calls": [[c.call_type, c.pattern, c.line_number, c.context]
                           for c in result.external_calls],
    }, ensure_ascii=False)
    recovered = [r for r in receivers if r in full_blob]
    if recovered:
        problems.append(f"adapter recovers cross-unit callees: {recovered}")
    # And no undotted call may survive as an edge either: declarations aside,
    # nothing in the effect or import fields may name a called routine.
    edges_blob = json.dumps({
        "imports": [[i.module, i.names] for i in result.imports],
        "external_calls": [c.context for c in result.external_calls],
    }, ensure_ascii=False)
    leaked = [c for c in EXPECTED_CALLS_IN_PACKAGE_BODY
              if c.split(".")[-1] in edges_blob]
    if leaked:
        problems.append(f"adapter leaks call targets into effects/imports: {leaked}")
    if problems:
        return Result("G11", "MUST", FAIL, "; ".join(problems))
    return Result("G11", "MUST", PASS,
                  f"declarations={[c.name for c in result.classes]} + "
                  f"functions={[f.name for f in result.functions]}; "
                  f"external_calls={len(result.external_calls)} entries, all effects-kind "
                  f"{sorted(kinds)}; 0 of {len(receivers)} cross-unit callees and 0 of "
                  f"{len(EXPECTED_CALLS_IN_PACKAGE_BODY)} hand-counted calls recoverable; "
                  "label=" + repr(label))


def g14_regex_dynamic_sql_target_blanked(eng: Engines) -> Result:
    """MUST (pin): a dynamic SQL target is unrecoverable from the regex adapter.

    The EXECUTE IMMEDIATE line is reported as an effect, but the string literal
    holding the actual call is blanked out of the context, so the target routine
    cannot be recovered at all. njank keeps the literal intact, which is what
    makes a second parse of it possible in principle.
    """
    try:
        ad = adapters()
    except Exception as error:  # noqa: BLE001
        return Result("G14", "MUST", SKIP, f"plugin adapters not importable: {error}")
    result = ad["regex-plsql"].parse(FILES["02_pkg_body.pkb"], "02_pkg_body.pkb")
    dyn = [c for c in result.external_calls if "EXECUTE IMMEDIATE" in c.context]
    if not dyn:
        return Result("G14", "MUST", FAIL, "no EXECUTE IMMEDIATE effect reported any more")
    leaked = [c.context for c in dyn if "stats_pkg" in c.context]
    if leaked:
        return Result("G14", "MUST", FAIL,
                      f"the dynamic target is no longer blanked: {leaked}; re-measure")
    return Result("G14", "MUST", PASS,
                  f"EXECUTE IMMEDIATE reported at line {dyn[0].line_number} with the target "
                  f"blanked out: {dyn[0].context!r}")


def g12_regex_mangles_quoted_identifier(eng: Engines) -> Result:
    """MUST (pin): the regex adapter returns a mangled name for an escaped identifier.

    The concrete defect that motivated replacing it. Pinned so the replacement
    is provably better rather than assumed to be.
    """
    try:
        ad = adapters()
    except Exception as error:  # noqa: BLE001
        return Result("G12", "MUST", SKIP, f"plugin adapters not importable: {error}")
    result = ad["regex-plsql"].parse(FILES["10_quoted_identifiers.sql"], "10_quoted_identifiers.sql")
    names = [c.name for c in result.classes]
    mangled = [n for n in names if n.count('"') % 2 == 1]
    if not mangled:
        return Result("G12", "MUST", FAIL,
                      f"no mangled name any more ({names}); if the adapter was fixed, "
                      "re-measure and retire this pin")
    return Result("G12", "MUST", PASS,
                  f"mangled names still produced: {mangled} (all classes: {names})")


def g13_abi3_recipe(eng: Engines) -> Result:
    """SHOULD: the recorded abi3 patch yields a version-independent wheel.

    Needs a C compiler and a second interpreter, so it only runs under
    --with-build. See abi3-packaging.md for the recipe this asserts.
    """
    return Result("G13", "SHOULD", SKIP,
                  "compiler-gated; run the recipe in abi3-packaging.md and record the outcome "
                  "in RESULTS.md")


CASES = [
    g1_call_nodes, g2_keyword_identifiers, g3_quoted_identifier_escape,
    g4_declarations_typed, g5_declared_gaps, g6_undeclared_gaps,
    g7_subscript_false_call, g8_plpgsql_no_engine, g9_dollar_quote_body_dependent,
    g10_nested_block_comment, g11_regex_classifies_effects_not_edges,
    g12_regex_mangles_quoted_identifier, g14_regex_dynamic_sql_target_blanked,
    g13_abi3_recipe,
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", type=Path, default=None)
    ap.add_argument("--with-build", action="store_true",
                    help="also report on the compiler-gated abi3 recipe")
    args = ap.parse_args()

    eng = Engines()
    print(f"repo root      : {REPO_ROOT}")
    print(f"plugin scripts : {PLUGIN_SCRIPTS} (exists={PLUGIN_SCRIPTS.is_dir()})")
    print(f"engines        : {eng.versions or 'none'}")
    print(f"available      : {eng.available() or 'none'}")
    if eng.plsql_reason:
        print(f"  oracle grammar NOT available: {eng.plsql_reason}")
        print(f"  install: {PLSQL_INSTALL}")
    if eng.sql_reason:
        print(f"  tree-sitter-sql NOT available: {eng.sql_reason}")
    print()

    results = [case(eng) for case in CASES]
    if not args.with_build:
        results = [r for r in results if r.case_id != "G13"]

    width = max(len(r.case_id) for r in results)
    for r in results:
        print(f"  [{r.verdict.upper():4}] {r.case_id:<{width}} {r.requirement:5} {r.detail}")
        for line in r.evidence[:1]:
            if isinstance(line, list):
                for item in line[:14]:
                    print(f"           {item}")

    counts = {v: sum(1 for r in results if r.verdict == v) for v in (PASS, FAIL, SKIP)}
    must_fail = [r.case_id for r in results if r.verdict == FAIL and r.requirement == "MUST"]
    print()
    print(f"  pass={counts[PASS]} fail={counts[FAIL]} skip={counts[SKIP]}  total={len(results)}")
    if must_fail:
        print(f"  MUST FAILURES: {must_fail}")

    if args.json:
        args.json.write_text(json.dumps({
            "engines": eng.versions, "available": eng.available(),
            "plsql_absent_reason": eng.plsql_reason,
            "results": [r.__dict__ for r in results], "counts": counts,
            "must_failures": must_fail,
        }, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"  wrote {args.json}")

    return 1 if must_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
