"""The candidates for the `.h` rule as it was before 25 November: each differs from the frozen patterns in the one edit it names, answers as the
rule before does wherever that edit does not reach, and where the edit does reach (the cases written out here) it answers as the
compiler reads the text. Standard library only."""
import ast
import random
import re
import subprocess
import time
from pathlib import Path

import pytest

import header_patterns as patterns
import header_routes as routes

OLD_CLASS = r"\bclass\s+\w+[^;(){}]*\{"
NEW_CLASS = r"\bclass\s+\w++(?:(?!\bclass\s+\w)[^;(){}])*+\{"
ORDINARY = ("int a;\n", "namespace a { int x; }\n", "@interface X\n@end\n", "/* c */ class A { int f; };\n", "// class A {\n",
            "char *s = \"/* not a comment\"; template <class T> struct S { T x; };\n", "using namespace std;\n",
            "#include <vector>\n", "#ifdef __cplusplus\nextern \"C\" {\n#endif\nint f(void);\n", "struct namespace_t { int a; };\n",
            "class A : public B, public C { int f; };\n", "enum class E { a };\n", "")


# ---- each candidate is today's pattern with its one edit ------------------------------------------------------

def test_fix_is_todays_comment_pattern_with_the_end_of_the_text_as_a_way_to_end():
    assert patterns.NOISE_FIX != patterns.BEFORE_NOISE
    assert patterns.NOISE_FIX.replace(r"(?:\*/|\Z)", r"\*/") == patterns.BEFORE_NOISE


def test_fixq_is_fix_with_a_quote_that_no_backslash_precedes_and_a_string_with_no_way_back():
    assert patterns.NOISE_FIXQ.count(r"(?<!\\)") == 2 and patterns.NOISE_FIXQ.count(")*+") == 2
    assert patterns.NOISE_FIXQ.replace(r"(?<!\\)", "").replace(")*+", ")*") == patterns.NOISE_FIX


def test_fixqc_is_todays_cpp_pattern_with_the_class_stopped_at_the_next_class():
    assert patterns.CPP_FIXQC != patterns.BEFORE_CPP
    assert patterns.BEFORE_CPP.count(OLD_CLASS) == 1 and patterns.CPP_FIXQC.count(NEW_CLASS) == 1
    assert patterns.CPP_FIXQC.replace(NEW_CLASS, OLD_CLASS) == patterns.BEFORE_CPP


def test_the_variants_are_these_patterns_and_nothing_else():
    assert {name: (n.pattern, c.pattern) for name, (n, c) in patterns.VARIANTS.items()} == {
        "fix": (patterns.NOISE_FIX, patterns.BEFORE_CPP), "fixq": (patterns.NOISE_FIXQ, patterns.BEFORE_CPP),
        "fixqc": (patterns.NOISE_FIXQ, patterns.CPP_FIXQC)}


# ---- the answers --------------------------------------------------------------------------------------------

@pytest.mark.parametrize("variant", sorted(patterns.VARIANTS))
def test_every_variant_answers_as_today_on_ordinary_text(variant):
    for text in ORDINARY:
        assert patterns.answer(text, variant) == patterns.answer(text), text


def test_the_class_candidate_loses_nothing_a_long_list_of_bases_is_still_cpp():
    bases = ", ".join(f"public ns::VeryLongInterfaceName{n}<int>" for n in range(14))
    text = f"class A : {bases} {{ int f; }};\n"
    assert len(text.split("{")[0]) > 450 and patterns.answer(text) == "cpp" and patterns.answer(text, "fixqc") == "cpp"
    bounded = re.compile(patterns.BEFORE_CPP.replace("[^;(){}]*", "[^;(){}]{0,400}"), re.MULTILINE)  # the cap the candidate replaced
    assert bounded.pattern != patterns.BEFORE_CPP and not bounded.search(text)


def test_the_class_candidate_gives_todays_answer_on_random_texts_of_its_tokens():
    tokens = ["class", " ", "a", "B", "{", "}", ";", "(", ")", ":", "public", "\n", "template", "<", ">", "enum", "struct", "x::y"]
    rng = random.Random(7)
    today, candidate = re.compile(patterns.BEFORE_CPP, re.MULTILINE), re.compile(patterns.CPP_FIXQC, re.MULTILINE)
    for _ in range(20000):
        text = "".join(rng.choice(tokens) for _ in range(rng.randint(1, 14)))
        assert bool(today.search(text)) == bool(candidate.search(text)), text


@pytest.mark.parametrize("text", [
    "#include <foo/*>\nnamespace a { int x; }\n",  # a path that is not a comment
    "int n = a/*p;\nnamespace a { int x; }\n",  # a division by a dereference, written with no space
    "auto s = R\"(a\"b/*c)\";\nnamespace a { int x; }\n",  # a raw string with a quote and a `/*` in it
])
def test_a_slash_star_never_closed_hides_the_rest_of_the_text_so_a_cpp_header_it_precedes_is_read_c(text):
    assert patterns.answer(text) == "cpp"  # today the `/*` is no comment where no `*/` follows
    assert all(patterns.answer(text, v) == "c" for v in patterns.VARIANTS)  # a compiler reads it to the end of the text


def test_a_slash_star_closed_later_is_hidden_as_today_so_the_candidates_change_nothing_there():
    text = "#include <foo/*>\nnamespace a { }\n/* later */\n"
    assert {patterns.answer(text, v) for v in patterns.VARIANTS} == {patterns.answer(text)} == {"c"}


def test_a_quote_after_a_backslash_outside_a_string_starts_no_string_in_fixq():
    text = 'int a; \\"/*" ;\nnamespace a { int x; }\n'  # today `"/*"` is a string; there `\\"` ends nothing and `/*` has no end
    assert patterns.answer(text) == "cpp" and patterns.answer(text, "fix") == "cpp"
    assert patterns.answer(text, "fixq") == patterns.answer(text, "fixqc") == "c"


def test_a_string_with_an_escaped_quote_is_still_one_string():
    text = 'const char *s = "a \\" /* b"; namespace a { int x; }\n'
    assert {patterns.answer(text, v) for v in patterns.VARIANTS} == {patterns.answer(text)} == {"cpp"}


# ---- the cost on the bad texts (the real measure is on Modal: this only keeps a candidate from going back) -----

@pytest.mark.parametrize("kind", routes.BAD_KINDS)
def test_the_last_candidate_reads_every_bad_text_of_32_kb_in_well_under_a_second(kind):
    text = routes.bad_text(kind, 32768)
    start = time.perf_counter()
    patterns.answer(text, "fixqc")
    assert time.perf_counter() - start < 1.0


# ---- the rule before is frozen here: it is the one of the commit the results were measured at -----------------------

BEFORE_COMMIT = "3960973d8afb1c4e49d97d0da9d9e0fc72857c63"
PRODUCT = Path(__file__).resolve().parents[2] / "daodan" / "core" / "languages" / "__init__.py"


def _patterns_of(source: str) -> dict[str, str]:
    """The pattern text of each `NAME = re.compile(...)` of the module, read from its syntax tree."""
    out = {}
    for node in ast.parse(source).body:
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call) and getattr(node.value.func, "attr", "") == "compile":
            out[node.targets[0].id] = ast.literal_eval(node.value.args[0])
    return out


def test_the_frozen_patterns_are_those_of_the_commit_the_results_were_measured_at():
    shown = subprocess.run(["git", "show", f"{BEFORE_COMMIT}:daodan/core/languages/__init__.py"], cwd=PRODUCT.parent,
                           capture_output=True, text=True)
    if shown.returncode:
        pytest.skip(f"commit {BEFORE_COMMIT[:9]} is not in this checkout")
    before = _patterns_of(shown.stdout)
    assert before["_C_NOISE_RE"] == patterns.BEFORE_NOISE and before["_CPP_HEADER_RE"] == patterns.BEFORE_CPP
    assert before["_OBJC_HEADER_RE"] == patterns.BEFORE_OBJC


def test_the_product_has_the_last_candidate_so_its_copy_here_is_the_products():
    product = _patterns_of(PRODUCT.read_text(encoding="utf-8"))
    assert product["_C_NOISE_RE"] == patterns.NOISE_FIXQ and product["_CPP_HEADER_RE"] == patterns.CPP_FIXQC
    assert product["_OBJC_HEADER_RE"] == patterns.BEFORE_OBJC
