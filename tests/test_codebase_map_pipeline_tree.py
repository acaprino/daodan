"""The tree of the pipeline says what the code declares: every source of the pre-map, analyzer, observer and rule has its row,
every file a row names is there, and the page's data is what the script writes."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "daodan/core"))
import pipeline_tree


def test_the_tree_and_the_code_agree_and_the_page_has_the_data_the_script_writes():
    assert pipeline_tree.check() == []


def test_a_source_the_tree_has_no_row_for_and_a_row_whose_source_is_gone_are_named():
    decl = pipeline_tree.declared()
    added = {**decl, "sources": [*decl["sources"], "zig"]}
    assert "zig: a source of the pre-map with no row here" in pipeline_tree.check(added)
    gone = {**decl, "sources": [name for name in decl["sources"] if name != "noir"]}
    assert "noir: a row for a source the pre-map no longer has" in pipeline_tree.check(gone)


def test_an_analyzer_or_a_rule_with_no_words_is_named():
    decl = pipeline_tree.declared()
    new = {**decl, "analyzers": [*decl["analyzers"], {"module": "css", "name": "scip-zig", "languages": ["c"], "container": True}]}
    assert "scip-zig: no words say what it is for" in pipeline_tree.check(new)
    ruled = {**decl, "rules": [*decl["rules"], "md.front-matter"]}
    assert "md.front-matter: a rule of the language with no row here" in pipeline_tree.check(ruled)


def test_data_that_is_behind_the_code_is_named():
    decl = pipeline_tree.declared()
    behind = {**decl, "versions": {**decl["versions"], "noir": "9.9.9"}}
    assert "data.ts: not what `pipeline_tree.py build` writes" in pipeline_tree.check(behind)
    assert pipeline_tree.check(behind, written=pipeline_tree.text(pipeline_tree.tree(behind))) == []
