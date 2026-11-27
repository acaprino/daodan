"""A `.h` header is read as Objective-C, C++ or C from its syntax tree (`languages/detect/rules/header.py`, route R3dx of
`benchmarks/header-language`): the Objective-C rule first, then a declaration only C++ has, then the grammar that errs less."""
import sys
import time
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "daodan/core"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
from languages import _treesitter, detect_language  # noqa: E402
from languages.detect.rules import header  # noqa: E402
import languages.detect as languages_detect  # noqa: E402
from source_files import MAX_PARSE_BYTES  # noqa: E402


def read(text):
    return detect_language(Path("a.h"), text)


def declared(text):
    return header._cpp_declared(_treesitter.get_parser("cpp")[0].parse(text.encode()).root_node)


# What C cannot declare, one construct each: the query finds it, whatever the error counts say.
CPP_ONLY = {
    "namespace": "namespace geo {\nint f();\n}\n",
    "nested namespace": "namespace a::b {\nint f();\n}\n",
    "namespace alias": "namespace fs = std::filesystem;\n",
    "template": "template <typename T> T twice(T v);\n",
    "template instance": "template class Box<int>;\n",
    "using namespace": "using namespace std;\n",
    "type alias": "using Id = int;\n",
    "class": "class Node {\n int x;\n};\n",
    "access label": "class Node {\n public:\n  int x;\n};\n",
    "base class": "struct B : A {\n int x;\n};\n",
    "friend": "struct A {\n friend struct B;\n int x;\n};\n",
    "enum class": "enum class E { a, b };\n",
    "concept": "template <typename T> concept Small = sizeof(T) < 8;\n",
    "method": "struct S {\n void f();\n};\n",
    "method with a body": "struct S {\n int g() { return 1; }\n};\n",
}


@pytest.mark.parametrize("text", CPP_ONLY.values(), ids=CPP_ONLY)
def test_each_declaration_c_lacks_is_found_and_makes_the_header_cpp(text):
    assert declared(text)
    assert read(text) == "cpp"


# Headers the regular expressions of before read as C and a C++ reader loses symbols of: structs with members C
# has not, and not one `namespace`, `class` or `template`. Written by hand in the shape of three of the corpus.
STRUCT_ONLY = {
    "base, initializers": ("struct PosEntry : public Position {\n  uint32_t offset;\n"
                           "  PosEntry(const Position &p, uint32_t o) : Position(p.file, p.pos), offset(o) {}\n"
                           "  PosEntry() { Reset(); }\n  void Reset() { Position::Reset(); offset = 0; }\n};\n"),
    "defaulted, deleted, destructor": ("struct Guard {\n  Guard() = default;\n  Guard(const Guard &) = delete;\n"
                                       "  Guard &operator=(const Guard &) = delete;\n  ~Guard() { release(); }\n  void release();\n};\n"),
    "qualified base, throw": ("struct Handler : winrt::implements<Handler, IValue> {\n"
                              "  int Get() const { if (!ready) throw hresult_error(); return value; }\n"
                              "  bool ready = false;\n  int value = 0;\n};\n"),
}


@pytest.mark.parametrize("text", STRUCT_ONLY.values(), ids=STRUCT_ONLY)
def test_a_struct_with_members_c_lacks_is_cpp_though_no_keyword_says_so(text):
    assert read(text) == "cpp"


C_ONLY = {
    "function pointer field": "struct S { int a; int (*cb)(int); };\ntypedef struct S S;\nint f(const S *s, int n);\n",
    "forward declarations": "class a;\nstruct b;\n",
    "a comment's words": "/* a class of errors */\n// namespace x { template <class T>\nstruct node { int x; };\n",
    "a string's words": 'const char *s = "namespace x { class A {";\n',
    "extern C guard": '#ifdef __cplusplus\nextern "C" {\n#endif\nint f(void);\n#ifdef __cplusplus\n}\n#endif\n',
    "empty": "",
    # C that a C++ grammar reads with an error (`virtual`, `operator` are C names): the grammar that errs less
    "C++ keywords as names": "struct S { int operator; };\nvoid f(int *restrict p) { int virtual = 1; }\n",
}


@pytest.mark.parametrize("text", C_ONLY.values(), ids=C_ONLY)
def test_what_has_no_declaration_of_cpp_is_c(text):
    assert not declared(text)
    assert read(text) == "c"


def test_the_grammar_that_errs_less_decides_when_no_declaration_does_and_a_tie_is_c():
    assert read("std::size_t bound(std::size_t n);\n") == "cpp"  # C++ reads it whole, C does not
    assert read("#include <vector>\nint f(void);\n") == "c"  # neither errs: the suffix's answer, as for any neutral header
    assert read("int a;\n") == "c"


def test_a_cplusplus_block_is_the_c_headers_own_guard_and_an_include_guard_is_none():
    assert read("#ifdef __cplusplus\nnamespace a { int x; }\n#endif\nint y;\n") == "c"
    assert read("#if defined(__cplusplus) && !defined(X)\nnamespace a { int x; }\n#else\nint y;\n#endif\n") == "c"
    assert read("#ifndef FOO_H\n#define FOO_H\nnamespace a { int x; }\n#endif\n") == "cpp"
    assert read("#ifdef __cplusplus\nnamespace a { int x; }\n#endif\nclass B { int y; };\n") == "cpp"


def test_the_rule_of_objective_c_comes_first_and_counts_in_code_only():
    assert read("@interface X : NSObject\n@end\n") is None
    assert read("class A { int x; };\n@interface X\n@end\n") is None
    assert read("// @interface, namespace a::b {\nconst char *s = \"@end\";\n") == "c"


def test_beyond_the_bound_the_header_is_read_by_its_head(monkeypatch):
    monkeypatch.setattr(languages_detect, "MAX_CHARS", 1_000)
    filler = "int a;\n" * 150
    assert read("namespace a { int x; }\n" + filler) == "cpp"
    assert read(filler + "namespace a { int x; }\n") == "c"
    assert read("namespace a { int x; }\n" + "x" * 5_000) == "cpp"  # the line the bound cuts is read as far as it goes


def test_the_bound_is_what_the_snapshot_parses_and_no_more():
    assert languages_detect.MAX_CHARS == MAX_PARSE_BYTES  # above it the snapshot parses no file: no parse here either


def test_a_flat_run_of_errors_is_walked_in_line_with_its_length():
    """A query over a tree whose root has 65,536 children of error takes seconds (it is quadratic); the walk does not."""
    started = time.perf_counter()
    assert read("{" * 65_536) == "c"
    assert time.perf_counter() - started < 1


def test_a_comment_that_never_closes_is_left_out_and_what_precedes_it_counts():
    assert read("namespace a { int x; }\n/* never closed\nclass B {") == "cpp"
    assert read("int f(void);\n/* class Node {\n};\n") == "c"
    assert read("#include <foo/*>\nnamespace a { }\n") == "c"  # the compiler reads the `/*` to the end of the text


def test_line_ends_a_bom_and_a_lone_surrogate_do_not_change_the_reading():
    assert [read(text) for text in ("namespace a {\r\n int x;\r\n}\r\n", "﻿namespace a {\n}\n", "\ud800namespace a { }\n")] == ["cpp"] * 3
    assert read("﻿int a;\r\n") == "c" and read("@interface X\r\n@end\r\n") is None


def test_no_grammar_and_no_text_give_the_suffixs_answer(monkeypatch):
    text = "namespace a { int x; }\n"
    assert read(text) == "cpp" and detect_language(Path("a.h")) == "c"
    monkeypatch.setattr(_treesitter, "get_parser", lambda language: None)
    assert read(text) == "c"
    assert read("@interface X\n@end\n") is None  # the rule of Objective-C needs no grammar
