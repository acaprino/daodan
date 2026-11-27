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
    ("\n\n  class A {\n public:\n int x;\n};\n", "cpp"), ("\n \n\ttemplate <class T> T f(T v);\n", "cpp"),
    ("\n\n   namespace {\n int x;\n}\n", "cpp"), ("int a;\n\n\n  struct B : A {\n};\n", "cpp"),
    ("\n\n  @interface A : B\n@end\n", None), ("\n\n @class X;\n", None), ("\n\n int f(void);\n", "c"),
    ("int a;\n", "c")])
def test_an_indented_mark_after_blank_lines_still_counts(text, language):
    assert detect_language(Path("a.h"), text) == language


# Marks that never close, and braces that never end: the text a grammar is slowest on (quadratic in its length), with
# the C++ the answer is made of in front or not.
BAD = {"open comments": "/* " * 16_000, "classes": "class a " * 12_000, "escaped quotes": '"' + r'\"' * 20_000,
       "escaped apostrophes": "'" + r"\'" * 20_000, "nested braces": "{" * SIZE, "open string": '"' + "x " * SIZE,
       "open comment lines": "int a;\n/* x\n" * 8_000}


@pytest.mark.parametrize("text", BAD.values(), ids=BAD)
@pytest.mark.parametrize("front", ["", "namespace a { int x; }\n"], ids=["alone", "after C++"])
def test_a_header_whose_marks_never_close_is_decided_at_once(front, text):
    started = time.perf_counter()
    detect_language(Path("a.h"), front + text)
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


# A rule reads at most `detect.MAX_CHARS` of a text, and costs in line with what it reads: four times the text, at most eight
# times the time (a quadratic rule would take sixteen). Below 50 ms the ratio is noise, so the text grows until it clears it.
import languages.detect as detection  # noqa: E402

RULE_IDS = ("ts.xml-document", "sql.oracle-words", "sql.anchored-type", "h.syntax-tree")
UNITS = ("%", "a%", " \n", "create or replace ")


def rule_of(rule_id):
    return next(rule for group in detection.RULES.values() for rule in group if rule.id == rule_id)


def best(rule, text):
    times = []
    for _ in range(3):
        started = time.perf_counter()
        rule.decide(text)
        times.append(time.perf_counter() - started)
    return min(times)


@pytest.mark.parametrize("unit", UNITS, ids=["percent", "name-percent", "blank-lines", "create-or-replace"])
@pytest.mark.parametrize("rule_id", RULE_IDS)
def test_a_rule_costs_in_line_with_the_text_it_reads(rule_id, unit):
    rule = rule_of(rule_id)
    rule.decide("int a;\n")  # the first parse of a grammar pays for its set-up
    size = 1_000
    while 4 * size * len(unit) * 2 <= detection.MAX_CHARS and best(rule, unit * size) < 0.05:
        size *= 2
    small, large = best(rule, unit * size), best(rule, unit * size * 4)
    assert large < 2
    if small < 0.05:
        pytest.skip(f"{rule_id} stays under 50 ms on {unit!r} up to the bound: no ratio to check")
    assert large / small < 8


@pytest.mark.parametrize("rule_id", RULE_IDS)
def test_a_word_after_the_bound_is_not_seen_by_the_rule(rule_id):
    rule = rule_of(rule_id)
    sample = rule.yes[0][0]
    path = Path("a" + rule.extensions[0])
    assert detection.detect(path, sample).decided_by == rule.id
    assert detection.detect(path, " " * detection.MAX_CHARS + sample).decided_by == detection.EXTENSION
