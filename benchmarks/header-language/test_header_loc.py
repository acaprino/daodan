"""The count of lines of code behind the comparison of the routes' size."""
import pytest

import header_loc as loc

SAMPLE = '''"""Module doc
over two lines."""
import re  # a comment after code

# a comment line
X = re.compile(
    r"a"
    r"b"
)


def f(a):
    """Doc."""

    return a  # trailing


class C:
    def m(self):
        x = """
text that is data
"""
        return x
'''


def test_code_lines_leaves_out_blank_comment_and_docstring_lines_and_keeps_a_data_string():
    assert sorted(loc.code_lines(SAMPLE)) == [3, 6, 7, 8, 9, 12, 15, 18, 19, 20, 21, 22, 23]


def test_span_of_a_definition_an_assignment_and_a_method():
    assert loc.span(SAMPLE, "X") == (6, 9)
    assert loc.span(SAMPLE, "f") == (12, 15)
    assert loc.span(SAMPLE, "C.m") == (19, 23)
    with pytest.raises(KeyError):
        loc.span(SAMPLE, "nope")


def test_count_by_name_and_by_range(tmp_path):
    path = tmp_path / "m.py"
    path.write_text(SAMPLE, encoding="utf-8")
    assert loc.count(path, ["X"]) == 4 and loc.count(path, ["f"]) == 2
    assert loc.count(path, ranges=[(3, 3), (13, 15)]) == 2


def test_todays_rule_is_found_by_name_in_the_product_file():
    ranges, detection, objc = loc.today_ranges(loc.TODAY.read_text(encoding="utf-8"))
    assert len(ranges) == 4 and detection[0] == 1 and len(objc) == 5
    assert 0 < loc.count(loc.TODAY, ranges=objc) < loc.count(loc.TODAY, ranges=ranges) < loc.count(loc.TODAY, ranges=[detection])


def test_a_rule_that_moves_out_of_detect_language_fails_the_count_instead_of_counting_less():
    moved = "_C_NOISE_RE = 1\n_CPP_HEADER_RE = 2\n_OBJC_HEADER_RE = 3\n\n\ndef detect_language(path, content=None):\n    return None\n"
    with pytest.raises(ValueError, match="rule moved"):
        loc.today_ranges(moved)
    reshaped = moved.replace("    return None", '    if suffix == ".h":\n        return looks_like_cpp(content)\n    return None')
    with pytest.raises(ValueError, match="no longer starts"):
        loc.today_ranges(reshaped)
    with pytest.raises(KeyError):
        loc.today_ranges("def detect_language(path):\n    return None\n")


def test_every_piece_of_a_route_exists_in_the_benchmark_code():
    totals = loc.measure()["totals"]
    assert totals["R0"] < totals["R2"] < totals["R1"] and totals["R3"] > totals["R1"]
    assert totals["R1x"] < totals["R1"] + totals["R0"] and totals["R3x"] > totals["R3"]  # no guard, but today's Objective-C rule
