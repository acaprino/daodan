"""Construct-level isolation tool: the diagnostic companion to eval_grammars.py.

The gate asserts invariants. This script produces the observations behind them,
one construct at a time, because every wrong conclusion reached while building
the gate came from parsing several constructs in one document and attributing
the resulting error to the wrong one.

Rule this tool exists to enforce: never attribute a parse error to a construct
without parsing that construct alone.

Sections:
  N  negative controls. Invalid Oracle that MUST fail, so a correct rejection
     is never again mistaken for a grammar gap.
  A  call inventory on the package body, for hand-checking recall and precision
     against corpus.EXPECTED_CALLS_IN_PACKAGE_BODY.
  B  the dollar-quote ladder: which single addition to a PL/pgSQL body flips the
     generic SQL grammar from clean to ERROR, and where the error lands.
  C  Oracle construct matrix, both grammars side by side.
  D  conditional-compilation forms, which contradict the grammar's own README.

Usage:
    python isolate_constructs.py            # all sections
    python isolate_constructs.py --section B C
    python isolate_constructs.py --json out.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from corpus import EXPECTED_CALLS_IN_PACKAGE_BODY, FILES  # noqa: E402

# --------------------------------------------------------------------- engines

class Engines:
    def __init__(self) -> None:
        self.plsql = None
        self.sql = None
        self.reasons: dict[str, str] = {}
        try:
            import tree_sitter_plsql  # noqa: PLC0415
            from tree_sitter import Language, Parser  # noqa: PLC0415
            self.plsql = Parser(Language(tree_sitter_plsql.language()))
        except Exception as error:  # noqa: BLE001
            self.reasons["njank-plsql"] = f"{type(error).__name__}: {error}"
        try:
            import tree_sitter_sql  # noqa: PLC0415
            from tree_sitter import Language, Parser  # noqa: PLC0415
            self.sql = Parser(Language(tree_sitter_sql.language()))
        except Exception as error:  # noqa: BLE001
            self.reasons["derekstride-sql"] = f"{type(error).__name__}: {error}"

    def get(self, name: str):
        return self.plsql if name == "njank-plsql" else self.sql

    def available(self) -> list[str]:
        return [n for n in ("njank-plsql", "derekstride-sql") if self.get(n)]


def text_of(node, raw: bytes) -> str:
    return raw[node.start_byte:node.end_byte].decode("utf-8", "replace")


def probe(eng: Engines, engine_name: str, label: str, source: str) -> dict:
    parser = eng.get(engine_name)
    if parser is None:
        return {"label": label, "engine": engine_name, "verdict": "SKIP",
                "detail": eng.reasons.get(engine_name, "absent")}
    raw = source.encode("utf-8")
    tree = parser.parse(raw)
    spans, stack = [], [tree.root_node]
    while stack and len(spans) < 5:
        node = stack.pop()
        if node.type == "ERROR" or node.is_missing:
            spans.append(f"{node.start_point[0]+1}:{node.start_point[1]} {text_of(node, raw)[:44]!r}")
            continue
        stack.extend(node.children)
    return {"label": label, "engine": engine_name,
            "verdict": "ERROR" if tree.root_node.has_error else "clean",
            "spans": sorted(spans)}


def show(rows: list[dict]) -> None:
    for row in rows:
        extra = f"  {row['spans']}" if row.get("spans") else (
            f"  ({row['detail']})" if row.get("detail") else "")
        print(f"  {row['verdict']:5} {row['engine']:16} {row['label'][:58]:58}{extra}")


# ------------------------------------------------------- N: negative controls

NEGATIVE_CONTROLS = {
    "N1 PROCEDURE ... DETERMINISTIC (invalid Oracle)":
        "CREATE OR REPLACE PACKAGE p AS\n PROCEDURE q(x IN DATE) DETERMINISTIC;\nEND p;\n/\n",
    "N1b FUNCTION ... RETURN NUMBER DETERMINISTIC (valid)":
        "CREATE OR REPLACE PACKAGE p AS\n FUNCTION q(x IN DATE) RETURN NUMBER DETERMINISTIC;\nEND p;\n/\n",
    "N2 FUNCTION with no RETURN clause (invalid Oracle)":
        "CREATE OR REPLACE FUNCTION f(x NUMBER) IS BEGIN RETURN x; END;\n/\n",
    "N3 unbalanced BEGIN/END (invalid)":
        "CREATE OR REPLACE PROCEDURE p IS BEGIN NULL;\n/\n",
}


def section_n(eng: Engines) -> list[dict]:
    """Invalid Oracle must be rejected. A grammar that accepts these is worse."""
    rows = []
    for label, source in NEGATIVE_CONTROLS.items():
        for engine_name in eng.available():
            rows.append(probe(eng, engine_name, label, source))
    print("\n=== N. negative controls: invalid Oracle must be REJECTED")
    print("    (N1 was misread as a grammar gap once; it is the test that was wrong)")
    show(rows)
    return rows


# --------------------------------------------------------- A: call inventory

def section_a(eng: Engines) -> list[dict]:
    """Hand-checkable recall and precision on the package body."""
    rows = []
    if not eng.plsql:
        print(f"\n=== A. SKIP: {eng.reasons.get('njank-plsql')}")
        return rows
    raw = FILES["02_pkg_body.pkb"].encode("utf-8")
    tree = eng.plsql.parse(raw)
    print("\n=== A. call inventory on 02_pkg_body.pkb (njank-plsql)")
    for node_type in ("ref_call", "aggregate_function_call",
                      "raise_application_error_statement", "execute_immediate"):
        stack, found = [tree.root_node], []
        while stack:
            node = stack.pop()
            if node.type == node_type:
                found.append((node.start_point[0] + 1,
                              " ".join(text_of(node, raw).split())[:76]))
            stack.extend(node.children)
        print(f"\n  {node_type} ({len(found)}):")
        for line, text in sorted(found):
            print(f"    L{line:<4} {text}")
        rows.append({"node_type": node_type, "count": len(found),
                     "items": [t for _, t in sorted(found)]})

    calls = {" ".join(text_of(n, raw).split()) for n in _collect(tree.root_node, {"ref_call"}, raw)}
    joined = "\n".join(calls)
    missing = [c for c in EXPECTED_CALLS_IN_PACKAGE_BODY if c not in joined]
    print(f"\n  hand-counted ground truth: {len(EXPECTED_CALLS_IN_PACKAGE_BODY)} calls")
    print(f"  recovered as dotted ref_call : {len(EXPECTED_CALLS_IN_PACKAGE_BODY) - len(missing)}")
    print(f"  missing                      : {missing or 'none'}")
    print(f"  false positives (subscripts) : "
          f"{sorted(c for c in calls if c.startswith('l_ids'))}")
    rows.append({"missing": missing, "false_positives": sorted(c for c in calls if c.startswith("l_ids"))})
    return rows


def _collect(root, wanted: set[str], raw: bytes) -> list:
    out, stack = [], [root]
    while stack:
        node = stack.pop()
        if node.type in wanted:
            out.append(node)
        stack.extend(node.children)
    return out


# ------------------------------------------------- B: the dollar-quote ladder

LADDER = [
    ("B0 trivial body, AS $$ before LANGUAGE",
     "CREATE FUNCTION f() RETURNS INT AS $$ BEGIN RETURN 1; END; $$ LANGUAGE plpgsql;\n"),
    ("B1 trivial body, LANGUAGE before AS $$",
     "CREATE FUNCTION f() RETURNS INT LANGUAGE plpgsql AS $$ BEGIN RETURN 1; END; $$;\n"),
    ("B2 + DECLARE section",
     "CREATE FUNCTION f() RETURNS INT LANGUAGE plpgsql AS $$\nDECLARE\n x INT;\nBEGIN\n x := 1;\n RETURN x;\nEND;\n$$;\n"),
    ("B3 + %ROWTYPE",
     "CREATE FUNCTION f() RETURNS INT LANGUAGE plpgsql AS $$\nDECLARE\n r orders%ROWTYPE;\nBEGIN\n RETURN 1;\nEND;\n$$;\n"),
    ("B4 + IF/THEN",
     "CREATE FUNCTION f() RETURNS INT LANGUAGE plpgsql AS $$\nBEGIN\n IF 1 = 1 THEN\n RETURN 1;\n END IF;\n RETURN 0;\nEND;\n$$;\n"),
    ("B5 + EXCEPTION WHEN",
     "CREATE FUNCTION f() RETURNS INT LANGUAGE plpgsql AS $$\nBEGIN\n RETURN 1;\nEXCEPTION\n WHEN no_data_found THEN\n RETURN 0;\nEND;\n$$;\n"),
    ("B6 + RAISE EXCEPTION ... USING ERRCODE",
     "CREATE FUNCTION f() RETURNS INT LANGUAGE plpgsql AS $$\nBEGIN\n RAISE EXCEPTION 'x %', 1 USING ERRCODE = '22023';\n RETURN 0;\nEND;\n$$;\n"),
    ("B7 + PERFORM routine_call()",
     "CREATE FUNCTION f() RETURNS INT LANGUAGE plpgsql AS $$\nBEGIN\n PERFORM audit_write('CALC', 1);\n RETURN 0;\nEND;\n$$;\n"),
    ("B8 anonymous DO block",
     "DO $$ BEGIN PERFORM 1; END $$;\n"),
    ("B9 tagged dollar quote $tag$...$tag$",
     "SELECT $tag$body$tag$ AS lit;\n"),
    ("B10 dollar quote in a SELECT list",
     "SELECT $$CREATE VIEW fake AS SELECT 1$$;\n"),
]


def section_b(eng: Engines) -> list[dict]:
    """Where the error lands is the finding: inside the quotes means the body is
    being parsed as SQL, not treated as an opaque literal."""
    rows = []
    print("\n=== B. dollar-quote ladder (error INSIDE the body = body parsed as SQL)")
    for label, source in LADDER:
        for engine_name in eng.available():
            row = probe(eng, engine_name, label, source)
            rows.append(row)
    show(rows)
    return rows


# --------------------------------------------- C: Oracle construct matrix

MATRIX = {
    "C01 package spec with %TYPE, cursor, exception, pragma":
        FILES["01_pkg_spec.pks"],
    "C02 package body, nested subprograms, bulk collect, forall":
        FILES["02_pkg_body.pkb"],
    "C03 object type + type body, OVERRIDING/MAP/CONSTRUCTOR/SELF":
        FILES["03_object_type.sql"],
    "C04 non-reserved keywords as identifiers":
        FILES["04_keyword_traps.sql"],
    "C05 MERGE / CONNECT BY / SEARCH-CYCLE / JSON_TABLE / q'[...]'":
        FILES["05_oracle_sql.sql"],
    "C06 trigger with :NEW/:OLD, REFERENCING, WHEN":
        FILES["06_trigger.sql"],
    "C07 Oracle-wrapped body (declared gap)":
        FILES["07_wrapped_body.sql"],
    "C08 escaped quotes in quoted identifiers":
        FILES["10_quoted_identifiers.sql"],
    "C09 LISTAGG without DISTINCT":
        "SELECT LISTAGG(status, ',') WITHIN GROUP (ORDER BY status) FROM orders;\n",
    "C10 LISTAGG(DISTINCT ...) (declared gap)":
        "SELECT LISTAGG(DISTINCT status, ',') WITHIN GROUP (ORDER BY status) FROM orders;\n",
    "C11 @dblink in FROM (declared gap)": "SELECT * FROM t@link;\n",
    "C12 @dblink in a call (declared gap)": "SELECT pkg.fn@link(1) FROM dual;\n",
    "C13 KEEP (DENSE_RANK ...) OVER (...)":
        "SELECT AVG(salary) KEEP (DENSE_RANK FIRST ORDER BY hire_date) OVER (PARTITION BY dept) FROM e;\n",
    "C14 KEEP without OVER":
        "SELECT MAX(salary) KEEP (DENSE_RANK LAST ORDER BY hire_date) FROM employees;\n",
    "C15 PIPELINED in the signature":
        "CREATE OR REPLACE FUNCTION f PIPELINED RETURN t_tab AS\nBEGIN RETURN;\nEND;\n/\n",
    "C16 PIPE ROW inside a normal function":
        "CREATE OR REPLACE FUNCTION f RETURN NUMBER AS\nBEGIN\n PIPE ROW(1);\n RETURN 1;\nEND;\n/\n",
    "C17 WITH FUNCTION (12c inline)":
        "WITH FUNCTION g(x NUMBER) RETURN NUMBER IS BEGIN RETURN x*2; END;\nSELECT g(id) FROM t;\n/\n",
    "C18 RESULT_CACHE RELIES_ON":
        "CREATE OR REPLACE FUNCTION f(x NUMBER) RETURN NUMBER RESULT_CACHE RELIES_ON (orders) AS\nBEGIN RETURN x;\nEND;\n/\n",
    "C19 CASE + %NOTFOUND + GOTO with label":
        "CREATE OR REPLACE PROCEDURE p AS\n c SYS_REFCURSOR; n NUMBER;\nBEGIN\n OPEN c FOR SELECT 1 FROM dual;\n FETCH c INTO n;\n IF c%NOTFOUND THEN GOTO done; END IF;\n CASE WHEN n = 1 THEN NULL; ELSE NULL; END CASE;\n <<done>> NULL;\nEND;\n/\n",
    "C20 PRAGMA RESTRICT_REFERENCES":
        "CREATE OR REPLACE PACKAGE p AS\n FUNCTION f RETURN NUMBER;\n PRAGMA RESTRICT_REFERENCES(f, WNDS, RNDS);\nEND p;\n/\n",
    "C21 MERGE with DELETE WHERE":
        "MERGE INTO t USING s ON (t.id = s.id)\n WHEN MATCHED THEN UPDATE SET t.v = s.v DELETE WHERE t.v IS NULL\n WHEN NOT MATCHED THEN INSERT (id, v) VALUES (s.id, s.v);\n",
    "C22 outer join (+) with several predicates":
        "SELECT a.x, b.y FROM a, b WHERE a.id = b.id(+) AND b.dt(+) > SYSDATE;\n",
    "C23 SELF member dispatch":
        "CREATE OR REPLACE TYPE BODY t AS\n MEMBER FUNCTION f RETURN VARCHAR2 IS\n BEGIN\n RETURN SELF.g();\n END;\n MEMBER FUNCTION g RETURN VARCHAR2 IS\n BEGIN\n RETURN 'x';\n END;\nEND;\n/\n",
}


def section_c(eng: Engines) -> list[dict]:
    rows = []
    print("\n=== C. Oracle construct matrix")
    tally = {n: {"clean": 0, "ERROR": 0} for n in eng.available()}
    for label, source in MATRIX.items():
        for engine_name in eng.available():
            row = probe(eng, engine_name, label, source)
            rows.append(row)
            if row["verdict"] in ("clean", "ERROR"):
                tally[engine_name][row["verdict"]] += 1
    show(rows)
    print("\n  tally:")
    for engine_name, counts in tally.items():
        total = counts["clean"] + counts["ERROR"]
        print(f"    {engine_name:16} clean {counts['clean']:2} / {total}")
    rows.append({"tally": tally})
    return rows


# ------------------------------------------- D: conditional compilation

COND_COMP = {
    "D1 $IF $$DBG $THEN ... $END (README claims $$inquiry support)":
        "CREATE OR REPLACE PACKAGE p AS\n $IF $$DBG $THEN\n PROCEDURE dbg;\n $END\nEND p;\n/\n",
    "D2 $IF ... $THEN ... $ELSE ... $END":
        "CREATE OR REPLACE PACKAGE p AS\n $IF $$DBG $THEN\n PROCEDURE dbg;\n $ELSE\n PROCEDURE rel;\n $END\nEND p;\n/\n",
    "D3 $IF TRUE $THEN ... $END (literal condition)":
        "CREATE OR REPLACE PACKAGE p AS\n $IF TRUE $THEN\n PROCEDURE dbg;\n $END\nEND p;\n/\n",
    "D4 $IF inside a package body":
        "CREATE OR REPLACE PACKAGE BODY p AS\n PROCEDURE q IS\n BEGIN\n $IF $$DBG $THEN NULL; $END\n END;\nEND p;\n/\n",
    "D5 $ERROR directive":
        "CREATE OR REPLACE PACKAGE p AS\n $IF $$DBG $THEN\n $ERROR 'dbg not allowed' $END\n $END\nEND p;\n/\n",
}


def section_d(eng: Engines) -> list[dict]:
    rows = []
    print("\n=== D. conditional compilation (README claims $IF/$END and $$inquiry)")
    for label, source in COND_COMP.items():
        if eng.plsql:
            rows.append(probe(eng, "njank-plsql", label, source))
        else:
            print(f"  SKIP {label} ({eng.reasons.get('njank-plsql')})")
    show(rows)
    return rows


SECTIONS = {"N": section_n, "A": section_a, "B": section_b, "C": section_c, "D": section_d}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--section", nargs="*", default=sorted(SECTIONS), choices=sorted(SECTIONS))
    ap.add_argument("--json", type=Path, default=None)
    args = ap.parse_args()

    eng = Engines()
    print(f"engines available: {eng.available() or 'none'}")
    for name, reason in eng.reasons.items():
        print(f"  {name} absent: {reason}")

    collected: dict[str, list] = {}
    for key in args.section:
        collected[key] = SECTIONS[key](eng)

    if args.json:
        args.json.write_text(json.dumps(collected, indent=2, ensure_ascii=False, default=str),
                             encoding="utf-8")
        print(f"\nwrote {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
