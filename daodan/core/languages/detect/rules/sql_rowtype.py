"""`.sql`: an anchored type, `name%TYPE` or `name%ROWTYPE`, is Oracle's PL/SQL."""
from __future__ import annotations

import re


class SqlRowtype:
    id = "sql.anchored-type"
    extensions = (".sql", ".ddl", ".dml")
    languages = ("PLSQL",)
    why = ("`%TYPE` and `%ROWTYPE` after a name declare a variable of a column's or a row's type, which only PL/SQL "
           "does. A literal comparison cannot ask it: `LIKE '%type%'`, common in queries on pg_catalog, has the same "
           "letters with no name before them.")
    source = "Daodan, `languages.detect_language` as of 2026-11-25."
    yes = (("DECLARE\n  v_total invoice.total%TYPE;\nBEGIN\n  NULL;\nEND;\n", "PLSQL"),
           ("CURSOR c IS SELECT * FROM invoice;\nr c%rowtype;\n", "PLSQL"))
    no = ("SELECT typname FROM pg_type WHERE typname LIKE '%type%';\n", "SELECT 10 % type_id FROM t;\n")

    # A pattern on source text: the file's language is not known yet, so no grammar can be chosen to read it with.
    _ANCHORED = re.compile(r"\w%(?:rowtype|type)\b", re.IGNORECASE)

    def decide(self, text: str) -> str | None:
        return "PLSQL" if self._ANCHORED.search(text) else None
