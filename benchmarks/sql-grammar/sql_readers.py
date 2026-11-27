"""The three readers the benchmark compares, each handing back (objects, milliseconds, failure): Daodan's regex adapters
as they are, the walk of the `sql` grammar's tree (`sql_grammar.tree_objects`), and sqlglot's expressions. Daodan's
`daodan/core` must be on `sys.path` (the Modal functions put it there); every import of a library is lazy.
"""
from __future__ import annotations

import time

import sql_grammar as g

GLOT_KINDS = {"TABLE": "table", "VIEW": "view", "INDEX": "index", "SEQUENCE": "sequence", "TYPE": "type",
              "SCHEMA": "schema", "TRIGGER": "trigger", "FUNCTION": "function", "PROCEDURE": "procedure"}


def language_of(path: str, text: str) -> str | None:
    """The product's own answer: `sql`, `plsql`, or None for a file it does not read."""
    from pathlib import Path

    from languages import detect_language
    return detect_language(Path(path), text)


def regex(language: str, text: str, path: str):
    """What `get_adapter(language).parse` finds, as objects: classes and functions, a first line and no last line."""
    from languages import get_adapter
    start = time.perf_counter()
    result = get_adapter(language).parse(text, path)
    ms = (time.perf_counter() - start) * 1000
    objects = g.from_regex([(c.name, c.kind, c.line_number) for c in result.classes],
                           [(f.name, f.visibility, f.line_number) for f in result.functions])
    return objects, ms, None


def tree_parser():
    """The pack's `sql` grammar, through Daodan's loader (the pinned release, verified by sha256), and whether the
    pack has `plsql`: (parser, plsql answer)."""
    import tree_sitter_language_pack as pack
    from languages import _treesitter
    pair = _treesitter.get_parser("sql")
    if pair is None:
        raise RuntimeError(f"no sql grammar: {_treesitter.load_failure('sql')}")
    try:
        pack.get_parser("plsql")
        plsql = "yes"
    except Exception as error:  # noqa: BLE001 - the pack's own answer is the finding
        plsql = f"{type(error).__name__}: {error}"
    return pair[0], plsql


def tree(parser, data: bytes):
    """The objects of the tree, its error counts and the milliseconds of the parse alone."""
    start = time.perf_counter()
    parsed = parser.parse(data)
    ms = (time.perf_counter() - start) * 1000
    root = parsed.root_node
    return g.tree_objects(root), g.tree_errors(root), ms


def _glot_name(target):
    from sqlglot import exp
    while isinstance(target, (exp.Schema, exp.UserDefinedFunction)) and target.this is not None:
        target = target.this
    if isinstance(target, exp.Table):
        parts = [target.catalog, target.db, target.name]
    else:
        parts = [getattr(target, "name", "") or ""]
    line = None
    for identifier in target.find_all(exp.Identifier):
        line = identifier.meta.get("line")
        break
    return g.norm_name(parts), line


def glot(text: str, dialect: str | None):
    """sqlglot's Create expressions as objects (the first line is the name's: sqlglot keeps the line of identifiers, not of
    statements), and how many statements it left as a bare Command. A file it cannot parse is the failure."""
    import logging

    import sqlglot
    from sqlglot import exp
    logging.getLogger("sqlglot").setLevel(logging.ERROR)  # it warns for every statement it falls back on
    start = time.perf_counter()
    try:
        trees = sqlglot.parse(text, read=dialect)
    except Exception as error:  # noqa: BLE001 - a whole file lost is what the product's `_try_sqlglot_tables` meets too
        return [], (time.perf_counter() - start) * 1000, {"failure": type(error).__name__, "commands": 0}
    ms = (time.perf_counter() - start) * 1000
    objects, commands = [], 0
    for expression in trees:
        if isinstance(expression, exp.Command):
            commands += 1
        elif isinstance(expression, exp.Create):
            kind = GLOT_KINDS.get(str(expression.args.get("kind") or "").upper())
            name, line = _glot_name(expression.this)
            if kind and name:
                objects.append(g.Obj(kind, name, line or 0))
    return sorted(objects, key=lambda o: (o.line, o.kind, o.name)), ms, {"failure": None, "commands": commands}
