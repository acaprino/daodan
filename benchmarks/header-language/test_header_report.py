"""The scoring of the measured records: answers, costs, the pools to annotate by hand, the estimate of what the
unannotated part of a pool hides, and the lines that show an error."""
import math

import pytest

import header_report as report


def rec(path, decl="cpp", p="proj", r0="cpp", ms=(1.0, 2.0, 3.0), kinds=None, objc_kinds=None, errs=(0, 0, 0), size=100, sym=None):
    return {"p": p, "path": path, "decl": decl, "size": size, "r0": r0, "r0ms": 0.5, "sha": "x", "sym": sym or {"c": 0, "cpp": 0},
            "f": {"size": size,
                  "c": {"ms": ms[0], "q_ms": 0.1, "err": errs[0], "missing": 0, "err_bytes": 0, "err_line": 7 if errs[0] else 0},
                  "cpp": {"ms": ms[1], "q_ms": 0.2, "err": errs[1], "missing": 0, "err_bytes": 0, "err_line": 0, "kinds": kinds or {}},
                  "objc": {"ms": ms[2], "q_ms": 0.3, "err": errs[2], "missing": 0, "err_bytes": 0, "err_line": 0,
                           "kinds": objc_kinds or {}}}}


# ---- answers and costs --------------------------------------------------------------------------------------

def test_answer_is_the_detector_for_r0_and_the_route_decision_for_the_others():
    r = rec("a.h", r0="objc", kinds={"namespace_definition": [1, 1, 3]})
    assert report.answer(r, "R0") == "objc" and report.answer(r, "R1d") == "cpp"


def test_cost_is_the_sum_of_the_parses_a_route_needs():
    r = rec("a.h")
    assert report.cost_ms(r, "R0") == 0.5
    assert report.cost_ms(r, "R1d") == pytest.approx(2.2)
    assert report.cost_ms(r, "R1do") == pytest.approx(2.2 + 3.3)
    assert report.cost_ms(r, "R2") == pytest.approx(1.1 + 2.2)
    assert report.cost_ms(r, "R3") == pytest.approx(1.1 + 2.2 + 3.3)


# ---- the estimate -------------------------------------------------------------------------------------------

def recs(n, prefix="a", **kw):
    return [rec(f"{prefix}{i}", **kw) for i in range(n)]


def test_estimate_scales_the_annotated_share_to_the_stratum():
    rows = recs(10)
    strata = {"s": [report.key(r) for r in rows]}
    labels = {"proj/a0": "cpp", "proj/a1": "cpp", "proj/a2": "either", "proj/a3": "either", "proj/a4": "either"}
    wrong = {"proj/a0", "proj/a1", "proj/a2", "proj/a7"}
    est, se = report.estimate(rows, strata, labels, lambda truth, r: truth == "cpp" and report.key(r) in wrong)
    assert est == pytest.approx(4.0) and se == pytest.approx(math.sqrt(3.0))


def test_estimate_takes_a_number_as_well_as_a_bool_and_a_difference_has_its_own_error():
    rows = recs(10)
    labels = {f"proj/a{i}": "cpp" for i in range(5)}
    strata = {"s": [report.key(r) for r in rows]}
    gain = {"proj/a0": 1, "proj/a1": 1, "proj/a2": -1}  # +1 where one route misses and the other does not, -1 the other way
    est, se = report.estimate(rows, strata, labels, lambda truth, r: gain.get(report.key(r), 0))
    assert est == pytest.approx(2.0)  # (1 + 1 - 1) / 5 of 10
    assert se == pytest.approx(math.sqrt(100 * 0.5 * 0.7 / 5))  # the sample variance of 1, 1, -1, 0, 0 is 0.7
    assert report.estimate(rows, strata, labels, lambda truth, r: 0) == (0.0, 0.0)


def test_estimate_of_a_fully_annotated_stratum_is_exact():
    rows = recs(3)
    labels = {"proj/a0": "cpp", "proj/a1": "either", "proj/a2": "cpp"}
    est, se = report.estimate(rows, {"s": list(labels)}, labels, lambda truth, r: truth == "cpp" and report.key(r) != "proj/a2")
    assert est == 1.0 and se == 0.0


def test_estimate_sums_strata_and_refuses_a_stratum_nobody_annotated():
    rows = recs(6)
    strata = {"s1": ["proj/a0", "proj/a1"], "s2": ["proj/a2", "proj/a3", "proj/a4", "proj/a5"]}
    labels = {"proj/a0": "cpp", "proj/a2": "cpp", "proj/a3": "either"}
    est, _ = report.estimate(rows, strata, labels, lambda truth, r: truth == "cpp")
    assert est == pytest.approx(2 * 1.0 + 4 * 0.5)
    with pytest.raises(ValueError):
        report.estimate(rows, strata, {"proj/a0": "cpp"}, lambda truth, r: True)


def test_estimate_counts_a_header_outside_the_pools_by_its_declared_label():
    rows = [rec("in.h"), rec("out_cpp.h"), rec("out_c.h", decl="c")]
    est, se = report.estimate(rows, {"s": ["proj/in.h"]}, {"proj/in.h": "either"}, lambda truth, r: truth == "cpp")
    assert est == 1.0 and se == 0.0  # in.h is either, out_cpp.h is its declared cpp, out_c.h is c


def test_flat_strata_names_each_pool_and_leaves_the_empty_ones_out():
    pool = {"cpp": {"all": [rec("a.h")], "some": []}, "c": {"all": [], "some": [rec("b.h", decl="c")]}}
    assert report.flat_strata(pool) == {"cpp/all": ["proj/a.h"], "c/some": ["proj/b.h"]}


def test_audit_labels_names_what_no_longer_holds():
    row, strata = rec("a.h"), {"cpp/all": ["proj/a.h"]}
    note = {"label": "either", "declared": "cpp", "stratum": "all", "sha": "x"}
    assert report.audit_labels([row], {"proj/a.h": note}, strata) == []
    assert "content changed" in report.audit_labels([row], {"proj/a.h": {**note, "sha": "y"}}, strata)[0]
    assert "no such header" in report.audit_labels([], {"proj/a.h": note}, strata)[0]
    assert "now in" in report.audit_labels([row], {"proj/a.h": {**note, "stratum": "some"}}, strata)[0]
    assert "now in" in report.audit_labels([row], {"proj/a.h": {**note, "declared": "c"}}, strata)[0]


# ---- the summary ---------------------------------------------------------------------------------------------

def test_summary_reads_the_symbol_loss_by_annotated_and_by_declared_label_and_the_estimates():
    rows = [rec("ok.h", kinds={"namespace_definition": [1, 1, 3]}, sym={"c": 1, "cpp": 5}), rec("lost.h", r0="c", sym={"c": 1, "cpp": 5}),
            rec("same.h", r0="c", sym={"c": 2, "cpp": 2}), rec("c.h", decl="c", r0="c", sym={"c": 3, "cpp": 3})]
    note = {"proj/same.h": {"label": "either", "declared": "cpp", "stratum": "all", "sha": "x"},
            "proj/lost.h": {"label": "cpp", "declared": "cpp", "stratum": "all", "sha": "x"},
            "proj/ok.h": {"label": "cpp", "declared": "cpp", "stratum": "some", "sha": "x"}}
    out = report.summarize({"records": rows}, note)
    r0 = out["routes"]["R0"]
    assert r0["symbol_loss"]["cpp>c"] == {"errors": 1, "with_loss": 1, "lost": 4, "of": 5}
    assert r0["symbol_loss_declared"]["cpp>c"] == {"errors": 2, "with_loss": 1, "lost": 4, "of": 7}  # same.h counts: no label
    assert out["label_problems"] == [] and out["pools"] == {"cpp/all": 2, "cpp/some": 1} and out["annotated"] == out["pools"]
    assert r0["estimate"]["total"]["either"] == [1.0, 0.0] and r0["estimate"]["wrong"]["cpp"] == [1.0, 0.0]
    assert out["indifference"]["cpp"]["either"] == [1.0, 0.0] and out["indifference"]["cpp"]["same_symbols"] == 1
    assert {**out["r0_c_of_cpp"], "annotated": 0} == {"headers": 2, "annotated": 0, "with_loss": 1, "lost": 4, "of": 7,
                                                       "annotated_cpp_lost": 4, "no_cpp_node": 2}  # lost.h is annotated cpp


def test_summary_without_a_sample_of_every_pool_gives_no_estimate():
    rows = [rec("a.h", r0="c"), rec("b.h", r0="c")]
    out = report.summarize({"records": rows}, {})
    assert out["routes"]["R0"]["estimate"] is None and out["indifference"]["cpp"]["either"] is None


def test_caps_count_the_answer_on_the_prefix_and_the_symbols_it_costs():
    cut = rec("far.h", r0="cpp", sym={"c": 1, "cpp": 9})
    cut["caps"] = {"4096": {"cut": {"R0": "c"}, "safe": {"R0": "c"}}}  # the C++ comes after the 4 KB
    near = rec("near.h", r0="cpp", sym={"c": 1, "cpp": 3})  # within the cap: no entry, its own answer
    caps = report._caps([cut, near], {})
    assert caps["none"]["full"]["R0"]["accuracy"]["cpp"] == [2, 2] and caps["none"]["full"]["R0"]["loss"] == {}
    assert caps["4096"]["cut"]["R0"]["accuracy"]["cpp"] == [1, 2]
    assert caps["4096"]["cut"]["R0"]["loss"]["cpp>c"] == {"errors": 1, "with_loss": 1, "lost": 8, "of": 9}


def test_capcost_charges_a_header_within_the_cap_its_own_cost_and_one_beyond_it_its_prefix():
    small, big = rec("small.h", ms=(1.0, 2.0, 3.0)), rec("big.h", ms=(10.0, 20.0, 30.0))
    rows = [{"p": "proj", "path": "small.h", "caps": {"8192": {"scan_ms": 0.5}}},
            {"p": "proj", "path": "big.h", "caps": {"8192": {"scan_ms": 1.0, "safe": {"c": 0.1, "cpp": 0.2, "objc": 0.3}, "r0_cut": 0.4}}}]
    out = report._capcost([small, big], rows)
    assert out["R0"]["8192"]["max"] == pytest.approx(0.5)  # the plain cut of the big one, the detector alone for the small
    assert out["R1eg"]["8192"]["max"] == pytest.approx(2.2 + 0.5)  # small: cpp parse and query, plus the check
    assert out["R2"]["8192"]["max"] == pytest.approx(1.1 + 2.2 + 0.5)  # small: both parses and the check; big: 0.1 + 0.2 + 1.0 is less


def test_r0check_counts_the_answers_a_candidate_changes_and_its_cost():
    rows = [{"r0": "c", "fix": "c", "fixq": "cpp", "fixqc": "cpp", "ms": [1.0, 2.0, 3.0, 4.0]},
            {"r0": "cpp", "fix": "cpp", "fixq": "cpp", "fixqc": "cpp", "ms": [3.0, 2.0, 1.0, 5.0]}]
    out = report._r0check(rows)
    assert out["headers"] == 2 and out["differ"] == {"fix": 0, "fixq": 1, "fixqc": 1}
    assert out["cost_ms"]["r0"]["max"] == 3.0 and out["cost_ms"]["fixq"]["median"] == 2.0 and out["cost_ms"]["fixqc"]["max"] == 5.0


def test_a_route_that_parsed_the_header_with_the_grammar_it_is_given_does_not_pay_that_parse_twice():
    cpp = rec("a.h", ms=(1.0, 20.0, 3.0), kinds={"namespace_definition": [1, 1, 3]})  # R1d: the cpp parse, and the answer is cpp
    assert report.cost_ms(cpp, "R1d") == pytest.approx(20.2) and report.marginal_ms(cpp, "R1d") == pytest.approx(0.2)
    plain = rec("b.h", ms=(1.0, 20.0, 3.0))  # R1d answers c and parsed only cpp: nothing of it is reused
    assert report.marginal_ms(plain, "R1d") == pytest.approx(20.2)
    assert report.marginal_ms(plain, "R2") == pytest.approx(1.1 + 20.2 - 1.0)  # both parsed, and the C parse (1.0 of its 1.1) is the answer's
    assert report.marginal_ms(plain, "R0") == report.cost_ms(plain, "R0") == 0.5  # today's rule parses nothing


def test_an_x_route_pays_today_s_rule_and_no_parse_where_that_rule_says_objc():
    objc = rec("c.h", r0="objc", ms=(1.0, 20.0, 3.0))
    assert report.cost_ms(objc, "R1dx") == report.marginal_ms(objc, "R1dx") == 0.5 and report.answer(objc, "R1dx") == "objc"
    other = rec("d.h", ms=(1.0, 20.0, 3.0))
    assert report.cost_ms(other, "R1dx") == pytest.approx(0.5 + 20.2)
    assert report.cost_ms(rec("e.h", ms=(1.0, 20.0, 3.0), kinds={"namespace_definition": [1, 1, 3]}), "R3dx") == pytest.approx(0.5 + 20.2)  # today's rule and the cpp parse, and stops there


def test_a_project_is_labelled_as_the_corpus_says_not_as_its_first_header():
    first_of_llvm = rec("llvm/include/llvm-c/Core.h", decl="c", p="llvm")  # the C API of a C++ project
    out = report.summarize({"records": [first_of_llvm, rec("llvm/include/llvm/IR/Type.h", p="llvm")]}, {})
    assert out["projects"]["llvm"]["label"] == "cpp"
    assert report.summarize({"records": [rec("a.h", p="not-in-the-corpus")]}, {})["projects"]["not-in-the-corpus"]["label"] == "cpp"


# ---- pools and the sample to annotate ----------------------------------------------------------------------

def test_pools_hold_the_declared_headers_some_route_reads_as_another_label_by_how_many_routes():
    ns = {"namespace_definition": [1, 1, 3]}
    recs = [rec("ok.h", kinds=ns), rec("macro.h", r0="c"), rec("some.h", r0="c", kinds=ns),
            rec("c.h", decl="c", r0="c"), rec("cc.h", decl="c", r0="cpp")]
    pools = report.pools(recs, routes_in=("R0", "R1d"))
    assert [r["path"] for r in pools["cpp"]["all"]] == ["macro.h"]
    assert [r["path"] for r in pools["cpp"]["some"]] == ["some.h"]
    assert [r["path"] for r in pools["c"]["some"]] == ["cc.h"] and pools["c"]["all"] == []


def test_the_annotation_sample_is_deterministic_proportional_and_keeps_at_least_two_per_stratum():
    pool = {"all": [f"a{i}" for i in range(100)], "some": [f"s{i}" for i in range(10)]}
    one = report.annotation_sample(pool, total=22, seed="x")
    assert one == report.annotation_sample(pool, total=22, seed="x")
    assert one != report.annotation_sample(pool, total=22, seed="y")
    assert len(one) == 22
    assert sum(k.startswith("s") for k in one) >= 2 and sum(k.startswith("a") for k in one) >= 2
    assert len(report.annotation_sample({"s": ["a", "b"]}, total=10, seed="x")) == 2  # a stratum smaller than the ask


# ---- the line that shows an error --------------------------------------------------------------------------

def test_evidence_line_of_a_cpp_header_read_as_c_is_the_first_cpp_only_node_of_any_tier():
    r = rec("a.h", kinds={"this": [1, 1, 40], "lambda_expression": [1, 1, 12]})
    assert report.evidence_line(r, "R1d", truth="cpp", answer="c") == 12
    assert report.evidence_line(rec("b.h"), "R1d", truth="cpp", answer="c") is None
    assert report.evidence_line(r, "R0", truth="cpp", answer="c") == 12  # the line is the header's own, whoever missed it
    assert report.evidence_line(r, "R0", truth="c", answer="cpp") is None


def test_evidence_line_of_a_c_header_read_as_cpp_is_the_node_that_misled():
    r = rec("a.h", decl="c", kinds={"qualified_identifier": [1, 1, 5], "namespace_definition": [1, 0, 9]})
    assert report.evidence_line(r, "R1e", truth="c", answer="cpp") == 5
    assert report.evidence_line(r, "R1dg", truth="c", answer="c") is None
    assert report.evidence_line(rec("a.h", decl="c", errs=(3, 1, 3)), "R2", truth="c", answer="cpp") == 7  # where C failed
