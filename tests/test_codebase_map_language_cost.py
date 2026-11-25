"""The language of a file is decided on the host from a text nobody chose: no text makes the choice slow."""
import sys
import time
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "daodan/core"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
from languages import detect_language  # noqa: E402

SIZE = 50_000


@pytest.mark.parametrize("text", ["\n" * SIZE, " \n" * (SIZE // 2), "\t\n" * (SIZE // 2)], ids=["blank", "spaces", "tabs"])
@pytest.mark.parametrize("suffix", [".h", ".ts", ".sql"])
def test_a_file_of_blank_lines_is_decided_at_once(suffix, text):
    started = time.perf_counter()
    detect_language(Path("a" + suffix), text)
    assert time.perf_counter() - started < 2


@pytest.mark.parametrize("text,language", [
    ("\n\n  public:\n int x;\n", "cpp"), ("\n \n\t#include <vector>\n", "cpp"), ("\n\n   namespace {\n", "cpp"),
    ("\n\n  @interface A : B\n@end\n", None), ("\n\n @class X;\n", None), ("\n\n int f(void);\n", "c"),
    ("int a;\n\n\n private :\n", "cpp"), ("int a;\n", "c")])
def test_an_indented_mark_after_blank_lines_still_counts(text, language):
    assert detect_language(Path("a.h"), text) == language


@pytest.mark.parametrize("text", ["/* " * 16_000, "class a " * 12_000, '"' + r'\"' * 20_000, "'" + r"\'" * 20_000],
                         ids=["open comments", "classes", "escaped quotes", "escaped apostrophes"])
def test_a_header_whose_marks_never_close_is_decided_at_once(text):
    started = time.perf_counter()
    detect_language(Path("a.h"), text)
    assert time.perf_counter() - started < 2


BASES = ", ".join(f"public ns::VeryLongInterfaceName<int{number}>" for number in range(14))


@pytest.mark.parametrize("text,language", [
    ("class Node : " + BASES + " {\n};\n", "cpp"),
    ("class a;\nclass Node {\n int x;\n};\n", "cpp"),
    ("class a;\nstruct b;\n", "c"),
    ("int f(void); /* class Node {", "c"),
    ('const char *s = "class Node {";\n', "c"),
    (r'const char *s = "a\"b class Node {";' + "\n", "c"),
    (r"char c = '\'';" + "\nclass Node {\n};\n", "cpp"),
    (r'const char *s = "\\";' + "\nclass Node {\n};\n", "cpp")],
    ids=["bases", "declared before", "only declared", "open comment", "string", "escaped quote", "apostrophe", "backslash"])
def test_a_class_counts_where_it_is_code(text, language):
    assert detect_language(Path("a.h"), text) == language
