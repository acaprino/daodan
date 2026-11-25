"""The writing of the README's tables: the cells, the blocks, and that a block never swallows the text around it."""
import pytest

import header_tables as tables

README = "intro\n<!-- table:a -->\n<!-- /table -->\ntext between\n<!-- table:b -->\nold\nlines\n<!-- /table -->\nend\n"


def test_render_fills_every_block_even_an_empty_one_and_keeps_the_text_between():
    out = tables.render(README, {"a": "A", "b": "B"})
    assert out == "intro\n<!-- table:a -->\nA\n<!-- /table -->\ntext between\n<!-- table:b -->\nB\n<!-- /table -->\nend\n"


def test_render_is_stable_when_run_again():
    once = tables.render(README, {"a": "A\nA2", "b": "B"})
    assert tables.render(once, {"a": "A\nA2", "b": "B"}) == once


def test_render_names_a_block_with_no_table():
    with pytest.raises(KeyError):
        tables.render(README, {"a": "A"})


def test_a_table_is_a_header_a_rule_and_its_rows_and_an_estimate_reads_value_and_error():
    assert tables.table(["x", "y"], [[1, "a"], [2, "b"]]) == "| x | y |\n| --- | --- |\n| 1 | a |\n| 2 | b |"
    assert tables.est([4.54, 3.91]) == "4.5 ± 3.9" and tables.est([4.54, 3.91], 0) == "5 ± 4"
