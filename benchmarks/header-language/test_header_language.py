"""The pure part of the header-language benchmark: the corpus rules, the routes' decisions over features, the
statistics and the bad texts. Nothing here parses with tree-sitter (`test_header_probe.py` does)."""
import pytest

import header_corpus as corpus
import header_routes as routes


# ---- corpus -------------------------------------------------------------------------------------------------

def make(**kw):
    base = dict(name="p", url="https://example.invalid/p.tar.gz", pin="v1", license="MIT", permissive=True, label="c",
                include=("",), exclude=(), overrides=(), cap=None)
    base.update(kw)
    return corpus.Project(**base)


def test_strip_root_drops_the_archive_folder():
    assert corpus.strip_root("zlib-51b7f2/zlib.h") == "zlib.h"
    assert corpus.strip_root("zlib-51b7f2/") == ""
    assert corpus.strip_root("x") == ""


def test_accepts_only_dot_h_under_include_and_not_excluded():
    p = make(include=("include/", "src/"), exclude=("src/vendor/",))
    assert p.accepts("include/a.h") and p.accepts("src/b/c.h")
    assert not p.accepts("include/a.hpp") and not p.accepts("include/A.H") and not p.accepts("include/a.c")
    assert not p.accepts("src/vendor/x.h") and not p.accepts("docs/x.h")


def test_label_of_takes_the_longest_override_prefix():
    p = make(label="cpp", overrides=(("include/", "c"), ("include/cc/", "cpp")))
    assert p.label_of("src/a.h") == "cpp"
    assert p.label_of("include/c.h") == "c"
    assert p.label_of("include/cc/x.h") == "cpp"


def test_select_keeps_the_first_path_of_identical_contents():
    p = make()
    got = corpus.select(p, {"b/x.h": "h1", "a/x.h": "h1", "c.h": "h2"})
    assert got == ["a/x.h", "c.h"]


def test_select_cap_is_deterministic_sorted_and_seeded():
    p = make(cap=3)
    files = {f"d/f{i}.h": f"h{i}" for i in range(20)}
    one = corpus.select(p, files)
    assert one == corpus.select(p, dict(reversed(list(files.items()))))
    assert len(one) == 3 and one == sorted(one)
    assert one != corpus.select(p, files, seed="other")


def test_select_ignores_what_the_project_does_not_accept():
    p = make(include=("include/",))
    assert corpus.select(p, {"include/a.h": "1", "src/b.h": "2", "include/c.hpp": "3"}) == ["include/a.h"]


def test_fingerprint_is_order_independent_and_content_sensitive():
    a = corpus.fingerprint({"x.h": "1", "y.h": "2"})
    assert a == corpus.fingerprint({"y.h": "2", "x.h": "1"})
    assert a != corpus.fingerprint({"x.h": "1", "y.h": "3"})


def test_projects_are_well_formed():
    names = [p.name for p in corpus.PROJECTS]
    assert len(names) == len(set(names))
    for p in corpus.PROJECTS:
        assert p.label in ("c", "cpp", "objc"), p.name
        assert p.url.startswith("https://") and p.pin and p.license, p.name
        assert all(label in ("c", "cpp", "objc") for _, label in p.overrides), p.name
        assert p.include and all(isinstance(i, str) for i in p.include), p.name
    assert {p.label for p in corpus.PROJECTS} == {"c", "cpp", "objc"}
    assert any(not p.permissive for p in corpus.PROJECTS)  # linux, named as the one exception


# ---- routes: decisions over features -----------------------------------------------------------------------

def feats(c_err=0, cpp_err=0, objc_err=0, cpp_kinds=None, objc_kinds=None, c_b=0, cpp_b=0, objc_b=0, missing=(0, 0, 0), r0="c"):
    return {
        "size": 100, "r0": r0,
        "c": {"ms": 1.0, "err": c_err, "missing": missing[0], "err_bytes": c_b},
        "cpp": {"ms": 1.0, "err": cpp_err, "missing": missing[1], "err_bytes": cpp_b, "kinds": cpp_kinds or {}},
        "objc": {"ms": 1.0, "err": objc_err, "missing": missing[2], "err_bytes": objc_b, "kinds": objc_kinds or {}},
    }


def test_r1_declaration_nodes_make_cpp_and_a_bare_forward_declaration_only_in_the_extended_tier():
    assert routes.decide("R1d", feats(cpp_kinds={"namespace_definition": [1, 1]})) == "cpp"
    assert routes.decide("R1d", feats(cpp_kinds={"class_specifier": [1, 1]})) == "c"
    assert routes.decide("R1e", feats(cpp_kinds={"class_specifier": [1, 1]})) == "cpp"
    assert routes.decide("R1d", feats()) == "c"


def test_r1_guard_variants_ignore_nodes_under_a_cplusplus_block():
    f = feats(cpp_kinds={"namespace_definition": [2, 0]})
    assert routes.decide("R1d", f) == "cpp"
    assert routes.decide("R1dg", f) == "c"
    assert routes.decide("R1dg", feats(cpp_kinds={"namespace_definition": [2, 1]})) == "cpp"


def test_r1_all_tier_reads_any_cpp_only_node():
    f = feats(cpp_kinds={"lambda_expression": [1, 1]})
    assert routes.decide("R1d", f) == "c" and routes.decide("R1a", f) == "cpp"


def test_r1_objc_variant_looks_at_objc_nodes_first():
    objc = {"class_interface": [1, 1]}
    assert routes.decide("R1do", feats(objc_kinds=objc)) == "objc"
    assert routes.decide("R1d", feats(objc_kinds=objc)) == "c"
    both = feats(cpp_kinds={"namespace_definition": [1, 1]}, objc_kinds=objc)
    assert routes.decide("R1do", both) == "objc"
    assert routes.decide("R1do", feats(cpp_kinds={"namespace_definition": [1, 1]})) == "cpp"


def test_r2_picks_the_grammar_with_fewer_errors_and_c_wins_a_tie():
    assert routes.decide("R2", feats(c_err=3, cpp_err=1)) == "cpp"
    assert routes.decide("R2", feats(c_err=1, cpp_err=1)) == "c"
    assert routes.decide("R2", feats(c_err=1, cpp_err=3)) == "c"
    assert routes.decide("R2", feats(c_err=1, cpp_err=1, missing=(1, 0, 0))) == "cpp"  # missing tokens count


def test_r2_bytes_weighs_the_size_of_the_error_not_its_count():
    f = feats(c_err=1, cpp_err=2, c_b=500, cpp_b=40)
    assert routes.decide("R2", f) == "c" and routes.decide("R2b", f) == "cpp"


def test_r2_three_grammars_tie_order_is_c_then_cpp_then_objc():
    assert routes.decide("R2o", feats(c_err=2, cpp_err=2, objc_err=2)) == "c"
    assert routes.decide("R2o", feats(c_err=2, cpp_err=1, objc_err=1)) == "cpp"
    assert routes.decide("R2o", feats(c_err=2, cpp_err=2, objc_err=0)) == "objc"
    assert routes.decide("R2ob", feats(c_err=1, cpp_err=1, objc_err=1, c_b=9, cpp_b=9, objc_b=3)) == "objc"


def test_r3_strong_cpp_nodes_first_then_the_error_counts():
    strong = feats(c_err=0, cpp_err=5, cpp_kinds={"template_declaration": [1, 1]})
    assert routes.decide("R3", strong) == "cpp"
    assert routes.decide("R3", feats(c_err=3, cpp_err=2, objc_err=0)) == "objc"
    assert routes.decide("R3", feats()) == "c"


def test_every_route_name_decides_and_unknown_names_raise():
    for name in routes.ROUTES:
        assert routes.decide(name, feats()) in ("c", "cpp", "objc")
    with pytest.raises(KeyError):
        routes.decide("R9", feats())


def test_an_x_route_takes_todays_objc_answer_first_and_never_parses_such_a_header():
    ns = {"namespace_definition": [1, 1]}
    assert routes.decide("R1dx", feats(cpp_kinds=ns, r0="objc")) == "objc" and routes.decide("R1dx", feats(cpp_kinds=ns)) == "cpp"
    assert routes.decide("R1ex", feats(cpp_kinds={"class_specifier": [1, 1]})) == "cpp"
    assert routes.decide("R3dx", feats(c_err=3, cpp_err=2, objc_err=0)) == "cpp"  # no objc grammar: C and C++ only
    assert routes.decide("R3dx", feats(r0="objc", c_err=3)) == "objc"
    assert routes.needs("R1dx", feats(r0="objc")) == () and routes.needs("R1dx", feats()) == ("cpp",)
    with pytest.raises(KeyError):
        routes.decide("R1dx", {k: v for k, v in feats().items() if k != "r0"})


def test_an_x_route_has_no_guard_and_so_reads_a_c_header_with_a_cplusplus_block_as_cpp():
    guarded_only = feats(cpp_kinds={"namespace_definition": [1, 0]})
    assert routes.decide("R1dx", guarded_only) == "cpp" and routes.decide("R1dg", guarded_only) == "c"


def test_r3_parses_the_other_grammars_only_when_the_cpp_parse_has_no_node():
    assert routes.needs("R3d", feats(cpp_kinds={"namespace_definition": [1, 1]})) == ("cpp",)
    assert routes.needs("R3d", feats()) == routes.GRAMMARS and routes.needs("R3dx", feats()) == ("c", "cpp")
    assert routes.needs("R3", feats(cpp_kinds={"class_specifier": [1, 1]})) == ("cpp",)  # the e tier has the bare class
    assert routes.needs("R3d", feats(cpp_kinds={"class_specifier": [1, 1]})) == routes.GRAMMARS
    assert routes.needs("R2", feats()) == ("c", "cpp") and routes.needs("R1eo", feats()) == ("cpp", "objc")


def test_kind_tiers_nest():
    assert routes.CPP_DECL < routes.CPP_EXT < routes.CPP_ALL
    assert "namespace_definition" in routes.CPP_DECL and "qualified_identifier" in routes.CPP_EXT
    assert routes.OBJC_DECL and "class_interface" in routes.OBJC_DECL


# ---- statistics ---------------------------------------------------------------------------------------------

def test_correct_is_exact_but_either_takes_any_answer():
    assert routes.correct("c", "c") and not routes.correct("c", "cpp")
    assert all(routes.correct("either", a) for a in ("c", "cpp", "objc"))


def test_matrix_and_accuracy_by_truth():
    pairs = [("c", "c"), ("c", "cpp"), ("cpp", "cpp"), ("either", "objc"), ("either", "c")]
    m = routes.matrix(pairs)
    assert m["c"] == {"c": 1, "cpp": 1}
    assert routes.accuracy(m) == {"c": (1, 2), "cpp": (1, 1), "either": (2, 2)}


def test_percentile_interpolates_and_handles_edges():
    v = [1, 2, 3, 4, 5]
    assert routes.percentile(v, 50) == 3 and routes.percentile(v, 0) == 1 and routes.percentile(v, 100) == 5
    assert routes.percentile([10], 95) == 10
    assert routes.percentile([0, 10], 95) == pytest.approx(9.5)
    with pytest.raises(ValueError):
        routes.percentile([], 50)


def test_growth_ratios_pair_each_size_with_its_double():
    assert routes.growth({2048: 1.0, 4096: 2.0, 8192: 8.0, 16384: 16.0}) == [(2048, 2.0), (4096, 4.0), (8192, 2.0)]
    assert routes.growth({2048: 1.0, 8192: 4.0}) == []  # not a doubling


def test_union_length_does_not_count_nested_or_overlapping_spans_twice():
    assert routes.union_length([(0, 10), (2, 5), (8, 12), (20, 25)]) == 17
    assert routes.union_length([]) == 0


# ---- bad texts ----------------------------------------------------------------------------------------------

@pytest.mark.parametrize("kind", routes.BAD_KINDS)
def test_bad_text_has_the_exact_size(kind):
    for size in (2048, 16384, 50000):
        assert len(routes.bad_text(kind, size).encode()) == size


def test_bad_text_shapes():
    assert set(routes.bad_text("blank_lines", 100)) <= {" ", "\n"}
    assert routes.bad_text("open_comment", 100).startswith("/*") and "*/" not in routes.bad_text("open_comment", 100)
    assert routes.bad_text("class_repeat", 100).startswith("class a class a ")
    assert routes.bad_text("open_comment_repeat", 100).startswith("/* /* /* ") and "*/" not in routes.bad_text("open_comment_repeat", 100)
    assert routes.bad_text("open_comment_lines", 100).startswith("int a;\n/* x\n/* x\n")
    assert set(routes.bad_text("nested_brace", 50)) == {"{"}
    assert routes.bad_text("escaped_dq", 100).startswith('"\\"\\"\\"') and routes.bad_text("escaped_dq", 100).count('"') == 50
    assert routes.bad_text("escaped_sq", 100).startswith("'\\'\\'\\'") and routes.bad_text("escaped_sq", 100).count("\\") == 50
    assert routes.bad_text("open_string", 100).startswith('"') and routes.bad_text("open_string", 100).count('"') == 1
    with pytest.raises(KeyError):
        routes.bad_text("nope", 10)


def test_open_comment_start_finds_only_an_unclosed_block_comment():
    f = routes.open_comment_start
    assert f("int a; /* x */ int b;") is None
    assert f("int a; /* never") == 7
    assert f('char *s = "/* not a comment"; int b;') is None
    assert f("// /* in a line comment\nint a;") is None
    assert f("char c = '\"'; /* open") == 14
    assert f('s = "a\\"/*"; int b;') is None
    assert f("/* a */ /* b") == 8


def test_safe_prefix_cuts_at_a_line_and_before_an_open_comment():
    text = "a\nb\nc\n"
    assert routes.safe_prefix(text, 100) == text
    assert routes.safe_prefix("aaa\nbbb\nccc\n", 9) == "aaa\nbbb\n"
    assert routes.safe_prefix("int a;\n/* open\nstill\nmore\n", 20) == "int a;\n"
    assert routes.safe_prefix("x" * 50, 10) == ""  # one line longer than the cap: nothing safe


def test_symbol_loss_counts_what_the_wrong_reading_lost():
    assert routes.symbol_loss({"c": 3, "cpp": 10}, truth="cpp", answer="c") == 7
    assert routes.symbol_loss({"c": 3, "cpp": 10}, truth="c", answer="cpp") == 0
    assert routes.symbol_loss({"c": 12, "cpp": 10}, truth="c", answer="cpp") == 2
    assert routes.symbol_loss({"c": 3, "cpp": 10}, truth="either", answer="c") == 0
    assert routes.symbol_loss({"c": 3, "cpp": 10}, truth="c", answer="c") == 0


def test_a_header_answered_objc_is_not_read_so_all_its_symbols_are_lost():
    assert routes.symbol_loss({"c": 3, "cpp": 10}, truth="cpp", answer="objc") == 10
    assert routes.symbol_loss({"c": 3, "cpp": 10}, truth="c", answer="objc") == 3
    assert routes.symbol_loss({"c": 3, "cpp": 10}, truth="either", answer="objc") == 0
    assert routes.symbol_loss({"c": 3, "cpp": 10}, truth="objc", answer="c") == 0


def test_exponent_is_the_slope_of_time_over_size_and_none_without_two_usable_sizes():
    assert routes.exponent({1000: 1.0, 4000: 4.0, 16000: 16.0}) == pytest.approx(1.0)
    assert routes.exponent({1000: 1.0, 2000: 4.0}) == pytest.approx(2.0)
    assert routes.exponent({1000: 1.0}) is None and routes.exponent({1000: 0.0, 2000: 1.0}) is None
