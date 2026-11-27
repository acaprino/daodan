"""The logic of the benchmark on samples written by hand: pure functions, no grammar, no network, no Daodan."""
import json
from pathlib import Path

import pytest

import sql_corpus as corpus
import sql_grammar as g

HERE = Path(__file__).resolve().parent


class Node:
    """The part of a tree-sitter node the walk reads."""

    def __init__(self, type, text=b"", start=(0, 0), end=(0, 0), children=(), fields=None, missing=False, span=(0, 0)):
        self.type, self.text, self.start_point, self.end_point = type, text, start, end
        self.children, self._fields, self.is_missing = list(children), fields or {}, missing
        self.start_byte, self.end_byte = span

    def child_by_field_name(self, name):
        return self._fields.get(name)


def reference(name, schema=None):
    fields = {"name": Node("identifier", name.encode())}
    if schema:
        fields["schema"] = Node("identifier", schema.encode())
    return Node("object_reference", children=list(fields.values()), fields=fields)


def test_a_name_is_lowercase_dotted_and_unquoted():
    assert g.norm_name(['"Sales"', '`Region.Totals`']) == "sales.region.totals"
    assert g.norm_name(["", " T "]) == "t"


def test_tree_objects_reads_node_types_with_lines_and_a_name_from_its_fields():
    table = Node("create_table", start=(0, 0), end=(3, 1), children=[reference("t", "s")])
    table._fields["name"] = table.children[0]
    view = Node("create_materialized_view", start=(4, 0), end=(5, 0), children=[reference("v")])
    comment = Node("comment", start=(7, 0), end=(7, 9))
    root = Node("program", children=[Node("statement", children=[table]), view, comment])
    assert g.tree_objects(root) == [g.Obj("table", "s.t", 1, 4), g.Obj("view", "v", 5, 5)]


def test_an_index_is_named_by_its_own_identifier_not_by_the_table_it_is_on():
    index = Node("create_index", start=(5, 0), end=(5, 40),
                 children=[Node("identifier", b"ix_t"), reference("t")])
    assert g.tree_objects(Node("program", children=[index])) == [g.Obj("index", "ix_t", 6, 6)]


def test_a_create_inside_an_error_node_still_counts_and_a_node_without_a_name_does_not():
    named = Node("create_procedure", start=(2, 0), end=(2, 30), children=[reference("p")])
    anonymous = Node("create_trigger", start=(9, 0), end=(9, 5))
    root = Node("program", children=[Node("ERROR", children=[named, anonymous])])
    assert g.tree_objects(root) == [g.Obj("procedure", "p", 3, 3)]


def test_a_node_that_stops_at_the_start_of_a_line_ends_on_the_line_before():
    node = Node("create_table", start=(1, 0), end=(4, 0), children=[reference("t")])
    assert g.tree_objects(Node("program", children=[node]))[0].end == 4


def test_tree_errors_counts_nodes_and_the_bytes_of_the_outermost_error_only():
    inner = Node("ERROR", span=(10, 20))
    outer = Node("ERROR", span=(5, 40), children=[inner])
    gap = Node("identifier", missing=True)
    root = Node("program", children=[outer, gap, Node("ERROR", span=(50, 60))])
    assert g.tree_errors(root) == {"error": 3, "missing": 1, "error_bytes": 45}


def test_from_regex_says_procedure_where_the_regex_reader_marks_it():
    found = g.from_regex([("T", "table", 1)], [("P", "procedure", 4), ("F", None, 2)])
    assert found == [g.Obj("table", "t", 1), g.Obj("function", "f", 2), g.Obj("procedure", "p", 4)]


def test_compare_counts_found_missing_extra_and_the_lines():
    ref = [g.Obj("table", "a", 1, 3), g.Obj("view", "v", 5, 6), g.Obj("function", "f", 8, 9, True)]
    read = [g.Obj("table", "a", 2, 3), g.Obj("view", "v", 5, None), g.Obj("index", "i", 10, 10)]
    out = g.compare(ref, read)
    assert out["total"] == {"found": 2, "missing": 1, "extra": 1, "start_diff": 1, "end_diff": 0, "end_unknown": 1}
    assert out["kinds"]["function"]["missing"] == 1 and out["kinds"]["index"]["extra"] == 1
    assert out["by_level"] == {"top": {"found": 2, "missing": 0}, "inner": {"found": 0, "missing": 1}}
    assert "line table a: 1 vs 2" in out["notes"] and "extra index i line 10" in out["notes"]


def test_compare_pairs_the_same_name_in_order_and_reports_a_last_line_that_differs():
    ref = [g.Obj("package", "p", 1, 5), g.Obj("package", "p", 7, 9)]
    read = [g.Obj("package", "p", 1, 5), g.Obj("package", "p", 7, 10)]
    assert g.compare(ref, read)["total"]["end_diff"] == 1
    assert g.compare(ref, read[:1])["total"]["missing"] == 1


def test_merge_adds_tallies_per_kind():
    one = g.compare([g.Obj("table", "a", 1)], [g.Obj("table", "a", 1)])
    two = g.compare([g.Obj("table", "b", 1)], [])
    merged = g.merge([one, two])
    assert merged["kinds"]["table"]["found"] == 1 and merged["kinds"]["table"]["missing"] == 1
    assert merged["total"]["found"] == 1


def test_summarise_groups_measured_files_and_leaves_the_others_out():
    ok = {"p": "x", "lang": "sql", "ts_ms": 2.0, "rx_ms": 1.0, "size": 100, "n_rx": 1, "n_ts": 1,
          "err": {"error": 2, "missing": 0, "error_bytes": 20}, "cmp_ts": g.compare([g.Obj("table", "a", 1)], [g.Obj("table", "a", 1)])}
    out = g.summarise([ok, {"p": "x", "lang": None}], lambda r: r["p"])
    assert out["x"]["files"] == 1 and out["x"]["files_with_error"] == 1 and out["x"]["error_byte_share"] == 0.2
    assert out["x"]["cmp_ts"]["total"]["found"] == 1 and out["x"]["glot_skipped"] == 1


@pytest.mark.parametrize("small, large, factor, verdict", [(100, 400, 4, "linear"), (100, 1600, 4, "superlinear")])
def test_growth_is_judged_by_time_over_size(small, large, factor, verdict):
    assert g.judge(g.growth_ratio(small, large, factor), floor_ok=True) == verdict


def test_a_run_too_fast_to_tell_is_noise_and_a_zero_time_is_infinite():
    assert g.judge(1.0, floor_ok=False) == "noise"
    assert g.growth_ratio(0, 5, 4) == float("inf")


def test_a_project_accepts_its_suffixes_under_its_prefixes_and_builds_the_archive_url():
    project = corpus.Project("p", "o/r", ("v1",), "MIT", ("source/",), None, exclude=("source/old/",))
    assert project.accepts("source/a.PKB") and not project.accepts("source/old/a.sql")
    assert not project.accepts("docs/a.sql") and not project.accepts("source/a.txt")
    assert project.url("v1") == "https://codeload.github.com/o/r/tar.gz/refs/tags/v1"
    assert project.url("heads/master").endswith("refs/heads/master")
    assert corpus.strip_root("r-1/source/a.sql") == "source/a.sql"


def test_select_keeps_one_path_per_content_within_the_size_bound_and_caps_by_the_seed():
    project = corpus.Project("p", "o/r", ("v1",), "MIT", ("",), None, cap=2)
    hashes = {"a.sql": "1", "b.sql": "1", "c.sql": "2", "d.sql": "3", "e.sql": "4", "big.sql": "5"}
    sizes = dict.fromkeys(hashes, 10) | {"big.sql": corpus.MAX_BYTES + 1}
    picked = corpus.select(project, hashes, sizes)
    assert len(picked) == 2 and "b.sql" not in picked and "big.sql" not in picked
    assert picked == corpus.select(project, hashes, sizes)
    assert corpus.fingerprint({"a": "1"}) == corpus.fingerprint({"a": "1"}) != corpus.fingerprint({"a": "2"})


def test_every_project_names_a_ref_and_a_dialect_sqlglot_knows():
    assert all(p.refs and p.dialect in (None, "oracle", "postgres") for p in corpus.PROJECTS)
    assert len({p.name for p in corpus.PROJECTS}) == len(corpus.PROJECTS)


def test_the_gold_of_each_fixture_points_at_its_own_lines():
    gold = json.loads((HERE / "fixtures" / "gold.json").read_text(encoding="utf-8"))
    files = [name for name in gold if name != "_"]
    assert sorted(files) == sorted(p.name for p in (HERE / "fixtures").iterdir() if p.name != "gold.json")
    for name in files:
        lines = (HERE / "fixtures" / name).read_text(encoding="utf-8").splitlines()
        for kind, obj, first, last, inner in gold[name]["objects"]:
            assert first <= last <= len(lines)
            assert obj in lines[first - 1].lower().replace('"', ""), (name, obj)
            assert lines[last - 1].strip() not in ("", "/"), (name, obj)
            assert inner or lines[first - 1].upper().startswith("CREATE"), (name, obj)
