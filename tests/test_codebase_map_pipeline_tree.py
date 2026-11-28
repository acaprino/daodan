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


def test_the_numbered_steps_of_the_plan_carry_the_pipeline_s_ids_in_order_and_one_out_of_order_or_missing_is_named():
    import pipeline
    plan = [step for step in pipeline_tree.tree(pipeline_tree.declared())["steps"]["plan"] if "id" in step]
    assert [step["id"] for step in plan] == list(pipeline.IDS)
    assert [step["key"] for step in plan] == [f"p{number}" for number in range(1, 9)]
    ids = pipeline.IDS
    swapped = (*ids[:3], ids[4], ids[3], *ids[5:])
    assert any(line.startswith("plan: the numbered steps carry") for line in pipeline_tree.check(ids=swapped))
    assert any(line.startswith("plan: the numbered steps carry") for line in pipeline_tree.check(ids=(*ids, "publish")))
    assert not any(line.startswith("plan:") for line in pipeline_tree.check())
