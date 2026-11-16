"""A file with a syntax error is read around it: its facts outside the parser's ERROR nodes are kept, and the
lines of each are a declared gap. tinyxml2's xmltest.cpp lost 3,498 references to one `#if` inside a call's
arguments, which tree-sitter cannot read.

    python -B -m pytest -q -p no:cacheprovider tests/test_codebase_map_snapshot_partial.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "plugins/codebase-map/skills/map/scripts"))

import code_graph  # noqa: E402
import snapshot  # noqa: E402

XMLTEST = """#include <cstdio>
int helper(int v) { return v; }
int main() {
    int a = helper(1);
    printf( "Error opening test file.\\n"
            "Is your working directory right?\\n"
    #if defined( _MSC_VER )
            "In Visual Studio set the working directory\\n"
    #endif
          );
    int b = helper(2);
    return a + b;
}
"""
# Per language: a file, the line of a call before its syntax error, the error's line, a call after it.
BROKEN = {
    "cpp": ("main.cpp", XMLTEST, 4, 5, 11),  # tree-sitter reads the `#if` and fails on the call around it
    "c": ("main.c", XMLTEST.replace("<cstdio>", "<stdio.h>"), 4, 5, 11),
    "javascript": ("a.js", "function ok() { return 1; }\nconst a = ok();\nconst broken = (1 + );\nconst b = ok();\n",
                   2, 3, 4),
    "typescript": ("a.ts", "function ok(): number { return 1; }\nconst a = ok();\nconst broken: number = (1 + );\n"
                           "const b = ok();\n", 2, 3, 4),
    "go": ("main.go", "package main\n\nfunc ok() int { return 1 }\n\nfunc main() {\n\ta := ok()\n\tb := (1 + )\n"
                      "\tc := ok()\n\t_ = a + b + c\n}\n", 6, 7, 8),
    "rust": ("main.rs", "fn ok() -> i32 { 1 }\nfn main() {\n    let a = ok();\n    let b = (1 + );\n"
                        "    let c = ok();\n}\n",
             3, 4, 5),
    "java": ("A.java", "class A {\n    int ok() { return 1; }\n    void run() {\n        int a = ok();\n"
                       "        int b = (1 + );\n        int c = ok();\n    }\n}\n", 4, 5, 6),
    "csharp": ("A.cs", "class A {\n    int Ok() { return 1; }\n    void Run() {\n        int a = Ok();\n"
                       "        int b = (1 + );\n        int c = Ok();\n    }\n}\n", 4, 5, 6),
    "kotlin": ("A.kt", "fun ok(): Int = 1\nfun run() {\n    val a = ok()\n    val b = (1 + )\n    val c = ok()\n}\n",
               3, 4, 5),
}


def _called(payload: dict, line: int) -> bool:
    return any(ref["kind"] == "call" and ref["span"][0] == line and ref["parts"][-1:] in (["ok"], ["Ok"], ["helper"])
               for ref in payload["references"])


@pytest.mark.parametrize("language", sorted(BROKEN))
def test_a_file_with_a_syntax_error_keeps_its_facts_around_the_error(tmp_path, language):
    """The reader keeps the facts outside each ERROR node (the walkers skip them, a reference one overlaps is
    dropped) and names the lines of each in `unread`; the file is still a parse error."""
    name, source, before, error, after = BROKEN[language]
    path = tmp_path / name
    path.write_text(source, encoding="utf-8")
    entry = snapshot.file_entry(path)
    assert entry["status"] == "parse-error" and any(note.startswith("syntax error:") for note in entry["parser_notes"])
    payload = entry.get("semantic")
    assert payload is not None, entry["parser_notes"]
    assert any(l0 <= error <= l1 for l0, l1 in payload["unread"]), payload["unread"]
    assert _called(payload, before), payload["references"]
    if not any(l0 <= after <= l1 for l0, l1 in payload["unread"]):
        assert _called(payload, after), (payload["unread"], payload["references"])


def test_the_snapshot_and_the_graph_read_the_file_around_its_error_and_declare_the_rest(tmp_path):
    """The store keeps a partial file's facts (`partial`, with the lines it could not read); the graph measures
    the sites outside them and lists the file among those it could not read whole, with those lines and the
    references the index holds in them."""
    project = tmp_path / "proj"
    project.mkdir()
    (project / "main.cpp").write_text(XMLTEST, encoding="utf-8")
    manifest = tmp_path / "manifest.sqlite"
    snapshot.write_snapshot(project, manifest)
    with code_graph.Snapshot(manifest) as snap:
        status, = snap.connection.execute("SELECT status FROM sem_coverage WHERE file = 'main.cpp'").fetchone()
        assert status == "partial"
        calls = {(rel, span[0], ".".join(parts)) for _id, rel, kind, _r, _t, span, parts, _x in snap.references("cpp")
                 if kind == "call"}
        assert {("main.cpp", 4, "helper"), ("main.cpp", 11, "helper")} <= calls
        index = code_graph.Index(snap.root)
        index.documents = {"main.cpp": [code_graph.Occurrence(4, 12, 4, 18, "helper", False, None),
                                        code_graph.Occurrence(5, 4, 5, 10, "printf", False, None)]}
        [unread] = code_graph.unread(index, snap, "cpp")
    assert unread["path"] == "main.cpp" and unread["references"] == 1 and unread["reason"].startswith("syntax error")
    assert any(l0 <= 5 <= l1 for l0, l1 in unread["lines"]) and not any(l0 <= 4 <= l1 for l0, l1 in unread["lines"])
