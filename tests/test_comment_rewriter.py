"""The comment rewriter reads source from the syntax tree, never with expressions (AGENTS.md).

    python -B -m pytest -q -p no:cacheprovider tests/test_comment_rewriter.py

Whether a comment is commented-out code, which code a trailing comment restates and where a comment starts are
questions for the file's grammar. A comment's own prose (debt, checklist, why words) is read with words, and a
tool directive in a comment (`@ts-expect-error`, `noqa`) is a table: no grammar tells it from prose.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "daodan/core"))

import comment_rewriter  # noqa: E402
from comment_rewriter import CommentClassification, CommentRewriter, CommentType  # noqa: E402
from languages import _treesitter  # noqa: E402


def _write(tmp_path: Path, name: str, text: str) -> Path:
    path = tmp_path / name
    path.write_text(text, encoding="utf-8", newline="")
    return path


def _rewrite(tmp_path: Path, name: str, text: str) -> tuple[str, list[str]]:
    return comment_rewriter.rewrite_file(_write(tmp_path, name, text), dry_run=True)


def _analysis(tmp_path: Path, name: str, text: str):
    return CommentRewriter().analyze_file(_write(tmp_path, name, text))


# ---------------------------------------------------------------- the inputs the review demonstrated


def test_a_compiler_directive_is_not_commented_out_code(tmp_path):
    source = "// @ts-expect-error the library types lack this overload\nconst x: number = lib.call('a');\n"
    rewritten, _ = _rewrite(tmp_path, "a.ts", source)
    assert rewritten == source


def test_a_checklist_comment_is_not_commented_out_code(tmp_path):
    source = "# if you change this, also update docs/api.md\nLIMIT = 10\n"
    rewritten, _ = _rewrite(tmp_path, "b.py", source)
    assert rewritten == source
    [comment] = _analysis(tmp_path, "b.py", source).comments
    assert comment.comment_type is CommentType.CHECKLIST


def test_a_debt_comment_is_not_commented_out_code(tmp_path):
    source = "# TODO(ana): drop after the migration\nOLD = 1\n"
    rewritten, _ = _rewrite(tmp_path, "b.py", source)
    assert rewritten.endswith(source)  # the debt comment stays; a design decision is added above it
    assert rewritten.startswith("# DESIGN DECISION: ")
    [comment] = _analysis(tmp_path, "b.py", source).comments
    assert comment.comment_type is CommentType.DEBT


def test_a_why_comment_that_reads_like_a_call_is_kept(tmp_path):
    source = "# fallback (cold cache) keeps the first answer\nCACHE = {}\n"
    rewritten, _ = _rewrite(tmp_path, "b.py", source)
    assert rewritten == source


def test_a_java_why_comment_that_starts_with_a_keyword_is_kept(tmp_path):
    source = "class A {\n  // new users get a trial because sales asked\n  int t = 14;\n}\n"
    rewritten, _ = _rewrite(tmp_path, "C.java", source)
    assert rewritten == source
    [comment] = _analysis(tmp_path, "C.java", source).comments
    assert comment.comment_type is CommentType.WHY


def test_the_word_for_inside_the_comment_is_not_a_loop_in_the_code(tmp_path):
    source = "users = fetch()  # loop for the retry budget, see issue 12\n"
    rewritten, _ = _rewrite(tmp_path, "b.py", source)
    assert rewritten == source


def test_a_keyword_in_a_string_of_the_line_is_not_a_loop_in_the_code(tmp_path):
    source = 'label = "for each"  # loop\n'
    rewritten, _ = _rewrite(tmp_path, "b.py", source)
    assert rewritten == source


# ---------------------------------------------------------------- a tool directive is never deleted

DIRECTIVES = [
    ("a.ts", "// @ts-expect-error the library types lack this overload\nconst x: number = lib.call('a');\n"),
    ("a.ts", "// @ts-ignore\nconst x: number = lib.call('a');\n"),
    ("a.js", "// eslint-disable-next-line no-console\nconsole.log(x);\n"),
    ("a.js", "console.log(x); // eslint-disable-line no-console\n"),
    ("a.py", "import os  # noqa: F401\n"),
    ("a.py", "x = compute(a)  # type: ignore[attr-defined]\n"),
    ("a.py", "x = 1  # pragma: no cover\n"),
    ("a.py", "import os  # pylint: disable=unused-import\n"),  # parses as an assignment to an annotated name
    ("a.py", "# fmt: off\nx = [1,2]\n"),
    ("A.java", "class A {\n  // NOPMD\n  int t = 14;\n}\n"),
    ("a.rs", "// rustfmt::skip\nlet x = 1;\n"),
    ("a.go", "var x = 1 //nolint:errcheck\n"),
    ("a.ts", "//#region helpers\nconst x = 1;\n//#endregion\n"),
    ("a.sql", "SELECT /*+ INDEX(t i) */ 1 FROM t; --+ hint\n"),
]


@pytest.mark.parametrize("name,source", DIRECTIVES)
def test_a_tool_directive_in_a_comment_is_never_deleted(tmp_path, name, source):
    rewritten, _ = _rewrite(tmp_path, name, source)
    assert rewritten == source


def test_a_tool_directive_is_its_own_type_and_is_kept(tmp_path):
    [comment] = _analysis(tmp_path, "a.ts", "// @ts-ignore\nconst x: number = lib.call('a');\n").comments
    assert (comment.comment_type, comment.classification) == (CommentType.DIRECTIVE, CommentClassification.KEEP)


# ---------------------------------------------------------------- commented-out code, read by the grammar

CODE = [
    ("a.py", "x = 1\n# y = compute(a)\nz = 2\n", "x = 1\nz = 2\n"),
    ("a.py", "# print('debug')\nx = 1\n", "x = 1\n"),
    ("a.py", "# import os\nx = 1\n", "x = 1\n"),
    ("a.py", "# from a import b\nx = 1\n", "x = 1\n"),
    ("a.py", "# if x:\n#     do()\nx = 1\n", "x = 1\n"),
    ("a.py", "# def old_implementation():\n#     return calculate_slow_way()\n\nx = 1\n", "\nx = 1\n"),
    ("a.py", "x = 1  # y = 2\n", "x = 1\n"),
    ("a.py", "# @app.route('/')\n# def index():\n#     return 1\nx = 1\n", "x = 1\n"),
    ("A.java", "class A {\n  // @Override\n  // public void run() {\n  // }\n  int u = 1;\n}\n", "class A {\n  int u = 1;\n}\n"),
    ("a.js", "// const x = lib.call('a');\nlet y = 1;\n", "let y = 1;\n"),
    ("a.js", "// foo(1, 2);\nlet y = 1;\n", "let y = 1;\n"),
    ("a.js", "// import a from 'b';\nlet y = 1;\n", "let y = 1;\n"),
    ("a.js", "// if (x) {\n//   foo();\n// }\nlet y = 1;\n", "let y = 1;\n"),
    ("a.ts", "// const x: number = lib.call('a');\nlet y = 1;\n", "let y = 1;\n"),
    ("a.ts", "// interface Old { a: number }\nlet y = 1;\n", "let y = 1;\n"),
    ("A.java", "class A {\n  // int t = 14;\n  int u = 1;\n}\n", "class A {\n  int u = 1;\n}\n"),
    ("A.java", "class A {\n  // System.out.println(x);\n  int u = 1;\n}\n", "class A {\n  int u = 1;\n}\n"),
    ("A.java", "// import a.b.C;\nclass A {}\n", "class A {}\n"),
    ("A.java", "class A {\n  // if (x) {\n  //   foo();\n  // }\n  int u = 1;\n}\n", "class A {\n  int u = 1;\n}\n"),
    ("a.rs", "// let x = 5;\nfn main() {}\n", "fn main() {}\n"),
    ("a.rs", "// foo(1);\nfn main() {}\n", "fn main() {}\n"),
    ("a.rs", "// use std::fmt;\nfn main() {}\n", "fn main() {}\n"),
    ("a.rs", "// if x {\n//     foo();\n// }\nfn main() {}\n", "fn main() {}\n"),
    ("a.sql", "-- SELECT * FROM t;\nSELECT 1;\n", "SELECT 1;\n"),
    ("a.sql", "-- DELETE FROM t WHERE a = 1;\nSELECT 1;\n", "SELECT 1;\n"),
    ("a.sql", "-- UPDATE t SET a = 1;\nSELECT 1;\n", "SELECT 1;\n"),
    ("a.sql", "-- CREATE TABLE t (a int);\nSELECT 1;\n", "SELECT 1;\n"),
]


@pytest.mark.parametrize("name,source,expected", CODE, ids=[f"{n}-{s.splitlines()[0]}" for n, s, _ in CODE])
def test_commented_out_code_is_deleted(tmp_path, name, source, expected):
    rewritten, _ = _rewrite(tmp_path, name, source)
    assert rewritten == expected


SENTENCES = [
    ("a.py", "# retry\nx = 1\n"),
    ("a.py", "# Note: retry\nx = 1\n"),  # parses as an annotation
    ("a.py", "# yes or no\nx = 1\n"),  # parses as a boolean expression of two names
    ("a.py", "# config.yaml\nx = 1\n"),  # parses as an attribute
    ("a.py", "# a, b\nx = 1\n"),
    ("a.py", "# see the docs for details\nx = 1\n"),
    ("a.py", "# wait for the lock to be released\nx = 1\n"),
    ("a.py", "# the value is cached per request\nx = 1\n"),
    ("a.py", "# -O is handled in flags()\nx = 1\n"),  # a comparison with a call in it is no statement
    ("a.py", "# Scale: 1 / sqrt(sys.float_info.min)\nx = 1\n"),  # an annotation, whatever its annotation holds
    ("a.py", "# 1.0 / (exp(t) + 2.0 + exp(-t))\nx = 1\n"),
    ("a.js", "// retry\nlet y = 1;\n"),
    ("a.js", "// Note: retry\nlet y = 1;\n"),  # parses as a labeled statement
    ("a.js", "// foo in bar\nlet y = 1;\n"),
    ("a.js", "// the cache is cold at startup\nlet y = 1;\n"),
    ("a.js", "// --- reads ---------------------\nlet y = 1;\n"),  # a rule drawn with dashes parses as nested decrements
    ("a.ts", "// Swift `repos[0]`\nlet y = 1;\n"),  # a name and a backtick quotation parse as a tagged template
    ("a.ts", "// `*args` (untyped)\nlet y = 1;\n"),  # a template literal and a parenthesis parse as a call
    ("a.js", "// new feature\nlet y = 1;\n"),  # `new feature` parses as a construction without arguments
    ("A.java", "class A {\n  // the cache is cold at startup\n  int u = 1;\n}\n"),
    ("a.rs", "// SAFETY: the pointer is valid for reads\nfn main() {}\n"),
    ("a.sql", "-- select the best option\nSELECT 1;\n"),
    ("a.sql", "-- note that the index is needed\nSELECT 1;\n"),
]


@pytest.mark.parametrize("name,source", SENTENCES, ids=[f"{n}-{s.splitlines()[0]}" for n, s in SENTENCES])
def test_a_sentence_is_not_commented_out_code(tmp_path, name, source):
    rewritten, _ = _rewrite(tmp_path, name, source)
    assert rewritten == source


@pytest.mark.parametrize("name,source", [
    ("a.py", "# @app.route('/')\nx = 1\n"),  # a decorator alone is no statement
    ("a.py", "# except KeyError:\nx = 1\n"),
    ("a.py", "# else:\nx = 1\n"),
    ("a.js", "// } else {\nlet y = 1;\n"),
    ("A.java", "class A {\n  // @Override\n  int u = 1;\n}\n"),
])
def test_a_fragment_the_grammar_cannot_read_alone_is_kept(tmp_path, name, source):
    rewritten, _ = _rewrite(tmp_path, name, source)
    assert rewritten == source


def test_a_block_of_commented_out_code_goes_whole_and_prose_beside_it_stays(tmp_path):
    source = ("# Compute the total.\n# total = a + b\n# Then report it.\n# report(total)\nx = 1\n")
    rewritten, _ = _rewrite(tmp_path, "a.py", source)
    assert rewritten == "# Compute the total.\n# Then report it.\nx = 1\n"


@pytest.mark.parametrize("name,source,design", [
    ("a.py", "# TODO: re-enable\n# check(x)\nx = 1\n", "# DESIGN DECISION: re-enable\n"),  # an annotation, then a call
    ("a.js", "// TODO: restore\n// foo();\nlet y = 1;\n", "// DESIGN DECISION: restore\n"),  # a label, then a call
    ("a.js", "// FIXME\n// foo();\nlet y = 1;\n", "// DESIGN DECISION: \n"),  # a name, then a call
    ("a.py", "# TODO(ana)\nx = 1\n", "# DESIGN DECISION: (ana)\n"),  # a call by itself
])
def test_a_debt_line_next_to_commented_out_code_is_not_deleted_with_it(tmp_path, name, source, design):
    rewritten, _ = _rewrite(tmp_path, name, source)
    marker = source.splitlines()[0]
    assert rewritten.startswith(design) and f"\n{marker}\n" in rewritten
    assert "check(x)" not in rewritten and "foo();" not in rewritten


@pytest.mark.parametrize("name,source,expected", [
    ("a.py", "# Note: retry\n# check(x)\nx = 1\n", "# Note: retry\nx = 1\n"),  # an annotation, then a call
    ("a.js", "// Note: retry\n// foo();\nlet y = 1;\n", "// Note: retry\nlet y = 1;\n"),  # a label, then a call
    ("a.js", "// retry\n// foo();\nlet y = 1;\n", "// retry\nlet y = 1;\n"),  # a name, then a call
])
def test_only_the_lines_that_hold_a_statement_go_when_prose_parses_beside_them(tmp_path, name, source, expected):
    rewritten, _ = _rewrite(tmp_path, name, source)
    assert rewritten == expected


@pytest.mark.parametrize("name,source", [
    ("a.py", "# cython: language_level=3\nx = 1\n"),
    ("a.py", "# vim: ts=4\nx = 1\n"),
    ("a.py", "# pytype: disable=attribute-error\nx = 1\n"),
    ("a.py", "# mode: strict = 1\nx = 1\n"),
    ("a.py", "# type: int = 5\nx = 1\n"),  # an annotated assignment is read as a note or a tool, never as code
    ("a.js", "// language=SQL\nlet y = 1;\n"),  # a plain assignment: only the directive table tells it
])
def test_a_tool_setting_that_parses_as_an_assignment_is_kept(tmp_path, name, source):
    rewritten, _ = _rewrite(tmp_path, name, source)
    assert rewritten == source


def test_a_bare_comment_line_between_two_lines_of_commented_out_code_goes_with_them(tmp_path):
    rewritten, _ = _rewrite(tmp_path, "a.py", "# x = 1\n#\n# y = 2\nz = 3\n")
    assert rewritten == "z = 3\n"


def test_commented_out_code_is_judged_by_its_own_body_not_by_its_marker(tmp_path):
    source = "x = 1  # y = 2\nz = 3  # note that y is gone\n"
    rewritten, _ = _rewrite(tmp_path, "a.py", source)
    assert rewritten == "x = 1\nz = 3  # note that y is gone\n"


def test_only_line_comments_are_judged_as_code(tmp_path):
    source = "/* foo(1, 2); */\nlet y = 1;\n"
    rewritten, _ = _rewrite(tmp_path, "a.js", source)
    assert rewritten == source


# ---------------------------------------------------------------- a trailing comment that restates its line

TRIVIAL = [
    ("a.py", "i += 1  # increment i\n", "i += 1\n"),
    ("a.py", "i -= 1  # decrement i\n", "i -= 1\n"),
    ("a.py", "def f():\n    return x  # return the value\n", "def f():\n    return x\n"),
    ("a.py", "for a in b:  # loop over b\n    pass\n", "for a in b:\n    pass\n"),
    ("a.py", "while x:  # loop while x\n    pass\n", "while x:\n    pass\n"),
    ("a.py", "import os  # import os\n", "import os\n"),
    ("a.py", "x = 1  # set x\n", "x = 1\n"),
    ("a.py", "foo()  # call foo\n", "foo()\n"),
    ("a.py", "if x:  # if x holds\n    pass\n", "if x:\n    pass\n"),
    ("A.java", "class A {\n  void f() {\n    i++; // increment i\n  }\n}\n", "class A {\n  void f() {\n    i++;\n  }\n}\n"),
    ("A.java", "class A {\n  void f() {\n    i += 1; // increment i\n  }\n}\n", "class A {\n  void f() {\n    i += 1;\n  }\n}\n"),
    ("A.java", "class A {\n  int t = 14; // set t\n}\n", "class A {\n  int t = 14;\n}\n"),
    ("A.java", "class A {\n  Object o = new Object(); // new object\n}\n", "class A {\n  Object o = new Object();\n}\n"),
    ("A.java", "class A {\n  int f() {\n    return 1; // return one\n  }\n}\n", "class A {\n  int f() {\n    return 1;\n  }\n}\n"),
    ("A.java", "class A {\n  void f() {\n    for (int i = 0; i < 3; i++) { // loop\n    }\n  }\n}\n",
     "class A {\n  void f() {\n    for (int i = 0; i < 3; i++) {\n    }\n  }\n}\n"),
    ("a.js", "i++; // increment i\n", "i++;\n"),
    ("a.js", "--i; // decrement i\n", "--i;\n"),
    ("a.js", "function f() {\n  return x; // return x\n}\n", "function f() {\n  return x;\n}\n"),
    ("a.js", "while (x) { // loop\n}\n", "while (x) {\n}\n"),
    ("a.js", "import a from 'b'; // import a\n", "import a from 'b';\n"),
    ("a.js", "const a = require('b'); // import a\n", "const a = require('b');\n"),
    ("a.ts", "i++; // increment i\n", "i++;\n"),
    ("a.rs", "fn f() {\n    i += 1; // increment i\n}\n", "fn f() {\n    i += 1;\n}\n"),
    ("a.rs", "fn f() {\n    for a in b { // loop\n    }\n}\n", "fn f() {\n    for a in b {\n    }\n}\n"),
    ("a.rs", "use std::fmt; // use fmt\n", "use std::fmt;\n"),
    ("a.rs", "fn f() {\n    match x { // match x\n        _ => {}\n    }\n}\n", "fn f() {\n    match x {\n        _ => {}\n    }\n}\n"),
    ("a.sql", "SELECT * FROM t; -- select all\n", "SELECT * FROM t;\n"),
    ("a.sql", "INSERT INTO t VALUES (1); -- insert a row\n", "INSERT INTO t VALUES (1);\n"),
    ("a.sql", "UPDATE t SET a = 1; -- update a\n", "UPDATE t SET a = 1;\n"),
    ("a.sql", "DELETE FROM t; -- delete all\n", "DELETE FROM t;\n"),
]


@pytest.mark.parametrize("name,source,expected", TRIVIAL, ids=[f"{n}-{s.splitlines()[-1]}" for n, s, _ in TRIVIAL])
def test_a_trailing_comment_that_restates_its_line_is_deleted(tmp_path, name, source, expected):
    rewritten, _ = _rewrite(tmp_path, name, source)
    assert rewritten == expected


NOT_RESTATED = [
    ("a.py", "x = 1  # return the cached value\n"),  # says return, the line sets
    ("a.py", "x = 1  # loop\n"),
    ("a.py", "x = 1  # increment the retries by the backoff\n"),
    ("a.py", "x += 5  # decrement\n"),
    ("a.js", "let y = 1; // import\n"),
    ("A.java", "class A {\n  int t = 14; // new\n}\n"),
    ("a.rs", "fn f() {\n    let x = 1; // match\n}\n"),
    ("a.sql", "SELECT 1; -- delete\n"),
]


@pytest.mark.parametrize("name,source", NOT_RESTATED, ids=[f"{n}-{s.splitlines()[-1]}" for n, s in NOT_RESTATED])
def test_a_trailing_comment_the_line_does_not_say_is_kept(tmp_path, name, source):
    rewritten, _ = _rewrite(tmp_path, name, source)
    assert rewritten == source


def test_a_line_in_a_region_the_grammar_could_not_read_is_not_a_restated_line(tmp_path):
    source = "class A\n    i += 1  # increment i\n"  # `+=` is a token inside an ERROR node
    rewritten, _ = _rewrite(tmp_path, "a.py", source)
    assert rewritten == source


def test_a_comment_above_the_line_is_never_trivial(tmp_path):
    source = "# increment i\ni += 1\n"
    rewritten, _ = _rewrite(tmp_path, "a.py", source)
    assert rewritten == source


def test_the_cut_of_an_inline_comment_follows_characters_not_bytes(tmp_path):
    rewritten, _ = _rewrite(tmp_path, "a.py", 's = "é"  # set s\n')
    assert rewritten == 's = "é"\n'


def test_a_jsx_file_is_read_with_the_tsx_grammar(tmp_path):
    source = "export const A = () => <p>see http://x.y</p>; // a link\n"
    comments = _analysis(tmp_path, "a.tsx", source).comments  # in the typescript grammar `//x.y</p>;` is a comment
    assert [c.raw_text for c in comments] == ["// a link"]


# ---------------------------------------------------------------- where a comment starts is read from the tree


def test_a_double_slash_inside_a_regex_literal_is_no_comment(tmp_path):
    source = "for (const m of s.matchAll(/a\\//g)) { // loop\n}\n"
    rewritten, _ = _rewrite(tmp_path, "a.js", source)
    assert rewritten == "for (const m of s.matchAll(/a\\//g)) {\n}\n"


def test_a_hash_inside_a_string_of_a_file_that_does_not_end_is_no_comment(tmp_path):
    source = 's = "# y = 2"\nx = [1,\n'
    rewritten, _ = _rewrite(tmp_path, "a.py", source)
    assert rewritten == source


def test_a_rust_doc_comment_is_never_rewritten(tmp_path):
    source = "/// foo(1);\nfn main() {}\n//! let x = 5;\n"
    rewritten, _ = _rewrite(tmp_path, "a.rs", source)
    assert rewritten == source


def test_a_jsdoc_block_is_kept(tmp_path):
    source = "/** foo(1); */\nfunction f() {}\n"
    rewritten, _ = _rewrite(tmp_path, "a.js", source)
    assert rewritten == source


def test_the_lines_of_a_crlf_file_stay_crlf(tmp_path):
    path = _write(tmp_path, "a.py", "# y = 2\r\nx = 1\r\n")
    comment_rewriter.rewrite_file(path, dry_run=False)
    assert path.read_bytes() == b"x = 1\r\n"


# ---------------------------------------------------------------- a grammar that does not load: no guess


def test_without_the_grammar_the_file_is_left_alone_and_says_so(tmp_path, monkeypatch):
    monkeypatch.setattr(_treesitter, "get_parser", lambda language: None)
    monkeypatch.setattr(_treesitter, "load_failure", lambda language: "ImportError: no grammar")
    source = "# y = compute(a)\nx = 1  # set x\n# TODO: later\n"
    path = _write(tmp_path, "a.py", source)
    rewritten, changes = comment_rewriter.rewrite_file(path, dry_run=False)
    assert rewritten == source and path.read_text(encoding="utf-8") == source
    assert changes == ["Left unchanged: the python grammar is not available (ImportError: no grammar); "
                       "commented-out code and restated lines are read from the syntax tree, never guessed"]
    assert not list(tmp_path.glob("*.tmp"))


def test_without_the_grammar_the_analysis_says_what_it_could_not_read(tmp_path, monkeypatch):
    monkeypatch.setattr(_treesitter, "get_parser", lambda language: None)
    monkeypatch.setattr(_treesitter, "load_failure", lambda language: None)
    analysis = _analysis(tmp_path, "a.py", "# y = compute(a)\nx = 1\n")
    assert analysis.gap == "the python grammar is not available"
    assert CommentType.BACKUP.value not in analysis.by_type
    assert "the python grammar is not available" in CommentRewriter().generate_report(analysis)


def test_a_file_above_the_parsing_size_limit_is_left_alone_and_says_so(tmp_path, monkeypatch):
    monkeypatch.setattr(comment_rewriter, "MAX_PARSE_BYTES", 20)
    source = "# y = compute(a)\nx = 1  # set x\n"
    path = _write(tmp_path, "a.py", source)
    rewritten, changes = comment_rewriter.rewrite_file(path, dry_run=False)
    assert rewritten == source and path.read_text(encoding="utf-8") == source
    assert len(changes) == 1 and changes[0].startswith("Left unchanged: the file exceeds the parsing size limit (20 bytes)")


def test_plsql_has_no_grammar_in_the_pack_so_its_file_is_left_alone(tmp_path):
    source = "CREATE OR REPLACE PACKAGE p AS\n  -- BEGIN\n  PROCEDURE q;\nEND p;\n"
    path = _write(tmp_path, "p.pks", source)
    rewritten, changes = comment_rewriter.rewrite_file(path, dry_run=False)
    assert rewritten == source and path.read_text(encoding="utf-8") == source
    assert len(changes) == 1 and changes[0].startswith("Left unchanged: the plsql grammar is not available")


def test_a_language_the_rewriter_never_read_as_code_still_gets_its_debt_rewrite(tmp_path):
    rewritten, changes = _rewrite(tmp_path, "a.go", "package a\n\n// TODO: later\nvar x = 1\n")
    assert "// DESIGN DECISION: later" in rewritten
    assert not any(change.startswith("Left unchanged") for change in changes)


# ---------------------------------------------------------------- the stylesheets stay analysis-only


def test_a_stylesheet_is_analyzed_and_never_rewritten(tmp_path):
    path = _write(tmp_path, "a.css", "/* a note */\n.a { top: 0; }\n")
    assert len(CommentRewriter().analyze_file(path).comments) == 1
    with pytest.raises(comment_rewriter.CommentRewriterError):
        CommentRewriter().rewrite_file(path)
