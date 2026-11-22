"""The language readers read source from its syntax tree and from nothing else.

The lines of code come from the comment nodes of the tree, the imports of a classified file from its parse, and a
grammar that does not load makes the reader say so: no symbol is read by expression in its place.
"""
import sys
from pathlib import Path
from unittest import mock

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "daodan/core"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import analyze_file  # noqa: E402
import classifier  # noqa: E402
from languages import _treesitter, get_adapter  # noqa: E402

# A comment opener and closer inside a string literal are code, and the line of a comment is not.
STRINGS = 'const open = "/*";\nlet a = 1;\nconst close = "*/";\n'
CODE_LINES = [
    ("javascript", "a.js", STRINGS, 3),
    ("typescript", "a.ts", STRINGS, 3),
    ("java", "A.java", 'class A {\n  String o = "/*";\n  int a = 1;\n  String c = "*/";\n}\n', 5),
    ("go", "a.go", 'package p\n\nfunc f() {\n\ta := "/*"\n\tb := 1\n\tc := "*/"\n}\n', 6),
    ("rust", "a.rs", 'fn a() {}\n/*\nuse std::fs;\n*/\nconst S: &str = "/*";\nconst T: &str = "*/";\n', 3),
    ("kotlin", "A.kt", 'fun a() {}\n/* x\n y */\nval s = "/*"\nval t = "*/" // z\n', 3),
    ("csharp", "A.cs", 'class A {}\n/* x\n y */\nstring s = "/*";\nstring t = "*/"; // z\n', 3),
    ("c", "a.c", 'int a;\n/* x\n y */\nchar *s = "/*";\nchar *t = "*/"; // z\n', 3),
    ("cpp", "a.cpp", 'int a;\n/* x\n y */\nchar *s = "/*";\nchar *t = "*/"; // z\n', 3),
    ("sql", "a.sql", "SELECT '/*' AS a;\nSELECT 1;\nSELECT '*/' AS b;\n", 3),
    ("kotlin", "A.kt", 'val s = """\nline one\n  // not a comment\n\n/* nor this */\nend"""\nval t = 1\n', 6),
    ("rust", "a.rs", 'const S: &str = r#"\nraw // text\n"#;\nconst T: u8 = 1;\n', 4),
    ("csharp", "A.cs", 'class A { string s = """\n    raw // text\n    """; }\n', 3),
    ("go", "a.go", 'package p\nvar s = `\nraw // text\n\nmore\n`\n', 5),
    ("java", "A.java", 'class A { String s = """\n  text // no\n  """; }\n', 3),
    ("cpp", "a.cpp", 'auto s = R"(\nraw // x\n)";\nint y;\n', 4),
    ("sql", "a.sql", "CREATE FUNCTION f() RETURNS int AS $$\nBEGIN\n  -- c\n  RETURN 1;\nEND;\n$$ LANGUAGE plpgsql;\n", 5),
    ("plsql", "a.pks", "BEGIN\n  x := '/*';\n  -- c\n  y := 1;\n  z := '*/';\nEND;\n", 5),
]


@pytest.mark.parametrize("language, name, source, expected", CODE_LINES, ids=[row[0] for row in CODE_LINES])
def test_lines_of_code_are_the_lines_with_a_token_outside_the_comments(language, name, source, expected):
    assert get_adapter(language).strip_comments_and_blanks(source) == expected


@pytest.mark.parametrize("source, expected", [
    ("// only a comment\n", 0),
    ("\n\n   \n", 0),
    ("a(); // trailing\n", 1),
    ("/* one\n two\n three */\n", 0),
    ("/* one\n two */ b();\n", 1),
    ("a(); /* x */ b();\n", 1),
    ("const t = `a\n\nb`;\n", 2),
    ("const t = `// not a comment`;\n", 1),
])
def test_lines_of_code_whatever_the_lines_hold(source, expected):
    assert get_adapter("javascript").strip_comments_and_blanks(source) == expected


def test_a_nested_sql_block_comment_is_read_as_the_grammar_reads_it():
    """The pinned SQL grammar does not nest block comments (PostgreSQL does): `/* a /* b */` is one comment and
    ` c */` is code, so this input counts 2 where an engine that nests would count 1."""
    assert get_adapter("sql").strip_comments_and_blanks("/* a /* b */ c */\nSELECT 1;\n") == 2


def test_a_tsx_file_counts_its_jsx_text_as_code():
    source = "const a = (\n  <div>\n    // jsx text\n  </div>\n);\n"
    assert get_adapter("typescript").strip_comments_and_blanks(source, "a.tsx") == 5


def test_a_grammar_that_does_not_load_gives_no_line_count():
    from languages import reading
    with mock.patch.object(_treesitter, "get_parser", return_value=None):
        assert reading.code_lines("let a = 1;\n", "javascript") is None
        assert get_adapter("javascript").strip_comments_and_blanks("let a = 1;\n") is None


# A comment and a string that mention an import are not imports.
IMPORTS = [
    ("javascript", "a.js", 'import a from "a";\n// import b from "b"\nconst s = "import c from \'c\'";\n'),
    ("csharp", "A.cs", "using System;\nclass A { void M(string input) { using var reader = input; } }\n"),
    ("python", "a.py", '"""\nimport x\nimport y\n"""\nimport os\n'),
    ("java", "A.java", "import java.util.List;\n/*\nimport java.io.File;\n*/\nclass A {}\n"),
    ("rust", "a.rs", "use std::io;\n/*\nuse std::fs;\n*/\nfn a() {}\n"),
    ("go", "a.go", 'package p\n\nimport (\n\t"fmt"\n\t/*\n\t"os"\n\t*/\n)\n\nvar tpl = `\nimport "net/http"\n`\n'),
    ("kotlin", "A.kt", "import a.b\n/*\nimport c.d\n*/\nfun f() {}\n"),
    ("c", "a.c", "#include <a.h>\n/*\n#include <b.h>\n*/\nint x;\n"),
]


@pytest.mark.parametrize("language, name, source", IMPORTS, ids=[row[0] for row in IMPORTS])
def test_the_dependencies_of_a_classified_file_are_the_imports_of_its_parse(language, name, source):
    parse = get_adapter(language).parse(source, name)

    result = classifier.classify_from_content(source, name, parse_result=parse)

    assert len(parse.imports) == 1
    assert result.num_dependencies == 1


@pytest.mark.parametrize("language", ["python", "java", "javascript", "typescript", "kotlin", "csharp", "rust", "go",
                                      "c", "cpp", "sql", "plsql", "css", "markup", "vue", "svelte", "astro"])
def test_no_reader_counts_imports_from_the_text(language):
    assert not hasattr(get_adapter(language), "count_imports")


# The product reads the script and the style blocks of a component or a page, and no tree of the whole file.
COMPONENTS = [
    ("a.vue", "<template><div/></template>\n<script>\nimport a from 'a'\n</script>\n"),
    ("a.svelte", "<script>\nimport a from 'a'\n</script>\n<p>x</p>\n"),
    ("a.astro", "---\nimport a from 'a'\n---\n<div/>\n"),
    ("a.html", "<style>a { color: red; }</style>\n<p>x</p>\n"),
]


@pytest.mark.parametrize("name, source", COMPONENTS, ids=[row[0] for row in COMPONENTS])
def test_a_component_or_a_page_is_classified_with_an_unknown_line_count(name, source):
    from languages import detect_language
    parse = get_adapter(detect_language(Path(name), source)).parse(source, name)

    result = classifier.classify_from_content(source, name, parse_result=parse)

    assert result.lines_of_code is None
    assert result.num_dependencies == len(parse.imports)
    assert "lines of code unknown" in result.reasoning.lower()
    assert result.classification is not classifier.Classification.UTILITY


def test_a_file_with_no_parse_has_an_unknown_dependency_count():
    source = "import a from 'a';\nimport b from 'b';\n"

    result = classifier.classify_from_content(source, "a.js")

    assert result.num_dependencies is None
    assert "dependencies unknown" in result.reasoning.lower()


def test_the_classifier_reads_a_file_it_is_given_without_a_parse(tmp_path):
    target = tmp_path / "a.js"
    target.write_text("import a from 'a';\n", encoding="utf-8")

    result = classifier.classify_file(target)

    assert result.num_dependencies is None
    assert result.lines_of_code == 1


def test_a_grammar_that_does_not_load_leaves_the_lines_unknown_and_says_so():
    with mock.patch.object(_treesitter, "get_parser", return_value=None):
        result = classifier.classify_from_content("let a = 1;\n", "a.js")

    assert result.lines_of_code is None
    assert "lines of code unknown" in result.reasoning.lower()


def test_the_analysis_reports_an_unknown_count_as_unknown():
    analysis = {
        "file": "a.js", "language": "javascript", "parser_notes": [],
        "classification": {"level": "utility", "lines_of_code": None, "num_dependencies": None,
                           "imported_by_count": 0, "verification_required": False, "reasoning": "r"},
        "structure": {"classes": [], "functions": [], "exported_symbols": [], "constants": []},
        "dependencies": {"internal": [], "external": []}, "external_calls": {},
    }

    assert "LOC: unknown | Dependencies: unknown" in analyze_file.format_as_summary(analysis)
    markdown = analyze_file.format_as_markdown(analysis)
    assert "**Lines of Code:** unknown" in markdown and "**Dependencies:** unknown" in markdown


# What a reader returns when the grammar does not load: no symbol read in its place, and the reason.
UNREAD = [
    ("go", "a.go", "package p\nimport \"fmt\"\nfunc F() { fmt.Println(1) }\ntype T struct{}\nconst K = 1\n"),
    ("java", "A.java", "import java.util.List;\npublic class A { public void m() {} }\n"),
    ("javascript", "a.js", "import a from 'a';\nclass A { m() {} }\nfunction f() { fetch('/x'); }\n"),
    ("typescript", "a.ts", "interface I {}\nenum E { A }\ntype T = string;\nclass A { m() {} }\n"),
    ("kotlin", "A.kt", "import a.b\nclass A { fun m() {} }\n"),
    ("csharp", "A.cs", "using System;\npublic class A { }\n"),
    ("rust", "a.rs", "use std::io;\npub fn f() {}\npub struct S;\n"),
    ("c", "a.c", "#include <a.h>\nint f(void) { return fopen(\"x\", \"r\") != 0; }\n"),
    ("cpp", "a.cpp", "#include <a.h>\nclass A { void m() {} };\n"),
]


def grammar_gone():
    """The grammar of no language loads: for the modules that bind `get_parser` by name too."""
    from languages import cfamily, go, java, javascript, rust, typescript
    patches = [mock.patch.object(_treesitter, "get_parser", return_value=None)]
    patches += [mock.patch.object(module, "get_parser", return_value=None)
                for module in (cfamily, go, java, javascript, rust, typescript)]
    return patches


@pytest.mark.parametrize("language, name, source", UNREAD, ids=[row[0] for row in UNREAD])
def test_a_reader_without_its_grammar_reads_nothing_and_says_so(language, name, source):
    from contextlib import ExitStack
    with ExitStack() as stack:
        for patch in grammar_gone():
            stack.enter_context(patch)
        result = get_adapter(language).parse(source, name)

    assert (result.classes, result.functions, result.imports, result.constants, result.external_calls,
            result.exported_symbols) == ([], [], [], [], [], [])
    assert result.notes[0] == "parser=none"
    assert any(note.startswith("tree-sitter unavailable: ") for note in result.notes)
    assert result.file_path == name and result.language == language


def test_a_grammar_that_raises_on_a_source_is_reported_with_the_error():
    from languages import go
    parser = mock.Mock()
    parser.parse.side_effect = RuntimeError("boom")
    with mock.patch.object(go, "get_parser", return_value=(parser, object())):
        result = get_adapter("go").parse("package p\nfunc F() {}\n", "a.go")

    assert result.functions == [] and result.notes[0] == "parser=none"
    assert "tree-sitter raised: RuntimeError: boom" in result.notes


def test_an_analysis_without_the_grammar_reports_the_unknown_counts(tmp_path):
    target = tmp_path / "a.js"
    target.write_text("import a from 'a';\nfunction f() {}\n", encoding="utf-8")
    from languages import javascript
    with mock.patch.object(_treesitter, "get_parser", return_value=None), \
            mock.patch.object(javascript, "get_parser", return_value=None):
        analysis = analyze_file.analyze_single_file(target, project_root=tmp_path)

    assert analysis["parser_notes"][0] == "parser=none"
    assert (analysis["classification"]["lines_of_code"], analysis["classification"]["num_dependencies"]) == (None, None)
    assert "LOC: unknown | Dependencies: unknown" in analyze_file.format_as_summary(analysis)
