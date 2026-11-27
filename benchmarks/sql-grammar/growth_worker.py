"""One growth measurement in a process of its own, so a reader that does not finish is killed by the caller's timeout
and its peak memory is its own: `python growth_worker.py CORE READER KIND N` prints {"ms", "maxrss_kb", "bytes"}.

READER is regex | tree | glot; KIND the text that grows: ddl (one CREATE TABLE per repeat), package (a PL/SQL package
body per repeat), open_comment (`/* ` repeated, never closed), dollar_run (`$a$ ` repeated, never closed). N = 0 is the
baseline: a one-line text, whose peak memory is the interpreter and the grammar.
"""
from __future__ import annotations

import json
import resource
import sys
import time

PACKAGE = """CREATE OR REPLACE PACKAGE BODY pkg_%d AS
  PROCEDURE p(a IN NUMBER) IS
    l_sql VARCHAR2(100);
  BEGIN
    l_sql := q'[SELECT 1 FROM dual]';
    EXECUTE IMMEDIATE l_sql;
  END p;
  FUNCTION f(a NUMBER) RETURN NUMBER IS
  BEGIN
    RETURN a + 1;
  END f;
END pkg_%d;
/
"""


def text_of(kind: str, n: int) -> str:
    if n == 0:
        return "select 1;\n"
    if kind == "ddl":
        return "".join(f"CREATE TABLE t{i} (id INT);\n" for i in range(n))
    if kind == "package":
        return "".join(PACKAGE % (i, i) for i in range(n))
    if kind == "open_comment":
        return "/* " * n
    if kind == "dollar_run":
        return "$a$ " * n
    raise SystemExit(f"unknown kind {kind}")


def main(core: str, reader: str, kind: str, n: int) -> None:
    sys.path.insert(0, core)
    sys.path.insert(0, __file__.rsplit("/", 1)[0])
    import sql_readers as readers
    text = text_of(kind, n)
    if reader == "regex":
        language = "plsql" if kind == "package" else "sql"
        run = lambda: readers.regex(language, text, "x.sql")  # noqa: E731
    elif reader == "tree":
        parser, _ = readers.tree_parser()
        data = text.encode("utf-8")
        run = lambda: readers.tree(parser, data)  # noqa: E731
    else:
        run = lambda: readers.glot(text, None)  # noqa: E731
    start = time.perf_counter()
    run()
    ms = (time.perf_counter() - start) * 1000  # the reader's own parse and extraction
    print(json.dumps({"ms": round(ms, 2), "maxrss_kb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                      "bytes": len(text.encode("utf-8"))}))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]))
