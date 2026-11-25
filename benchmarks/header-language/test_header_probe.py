"""The probe: the three grammars' parses of a header, as the features the routes decide on. These run Daodan's own
loader (`languages._treesitter.get_parser`) and the pack's Objective-C grammar, so they need the grammars of the pinned
tree-sitter-language-pack in place, as Daodan's own tests do."""
from pathlib import Path

import pytest

import header_patterns as patterns
import header_patterns as patterns
import header_probe
import header_routes as routes

CORE = Path(__file__).resolve().parents[2] / "daodan" / "core"


@pytest.fixture(scope="module")
def probe():
    return header_probe.Probe(str(CORE))


def kinds_of(probe, grammar):
    language = probe.parsers[grammar][1]
    return {language.node_kind_for_id(i) for i in range(language.node_kind_count)
            if language.node_kind_is_named(i) and language.node_kind_is_visible(i)}


def test_the_cpp_only_kinds_are_exactly_the_nodes_cpp_has_and_c_has_not(probe):
    assert routes.CPP_ONLY_NAMED == kinds_of(probe, "cpp") - kinds_of(probe, "c")


def test_every_objc_kind_of_a_tier_is_a_node_of_the_objc_grammar_and_not_of_c(probe):
    named = kinds_of(probe, "objc") - kinds_of(probe, "c")
    assert routes.OBJC_DECL <= named
    assert routes.OBJC_EXT - {"import_directive"} <= named


def test_a_class_with_a_body_is_cpp_by_declaration_nodes(probe):
    f = probe.features(b"class A { public: int f(); };\n")
    assert f["cpp"]["kinds"]["class_with_body"][:2] == [1, 1] and f["cpp"]["kinds"]["access_specifier"][:2] == [1, 1]
    assert routes.decide("R1d", f) == "cpp" and routes.decide("R1dg", f) == "cpp"


def test_the_c_grammar_reads_a_small_class_without_an_error_so_error_counts_alone_tie(probe):
    f = probe.features(b"class A { public: int f(); };\n")
    assert f["c"]["err"] == 0 and f["cpp"]["err"] == 0
    assert routes.decide("R2", f) == "c"  # the tie goes to C: the error counts cannot see this class


def test_a_namespace_a_template_a_struct_with_a_method_and_an_enum_class(probe):
    for src, kind in ((b"namespace a { int x; }\n", "namespace_definition"),
                      (b"template <class T> struct S { T x; };\n", "template_declaration"),
                      (b"struct S { void f(); };\n", "struct_fn_decl"),
                      (b"struct S { int g() { return 1; } };\n", "struct_fn_def"),
                      (b"enum class E { x };\n", "enum_class"),
                      (b"using namespace std;\n", "using_declaration"),
                      (b"using T = int;\n", "alias_declaration"),
                      (b"struct B : A { };\n", "base_class_clause")):
        f = probe.features(src)
        assert f["cpp"]["kinds"].get(kind, [0, 0])[0] >= 1, (src, f["cpp"]["kinds"])
        assert routes.decide("R1d", f) == "cpp", src


def test_a_plain_c_header_has_no_cpp_node_and_a_function_pointer_field_is_no_method(probe):
    src = (b"#ifndef X_H\n#define X_H\nstruct S { int a; int (*cb)(int); };\ntypedef struct S S;\n"
           b"int f(const S *s, int n);\nstatic inline int g(int a) { return a + 1; }\n#endif\n")
    f = probe.features(src)
    assert f["cpp"]["kinds"] == {} and f["c"]["err"] == 0 and f["cpp"]["err"] == 0
    assert routes.decide("R1a", f) == "c"


def test_nodes_inside_a_cplusplus_block_count_in_the_total_and_not_outside(probe):
    f = probe.features(b"#ifdef __cplusplus\nnamespace a { int x; }\n#endif\nint y;\n")
    assert f["cpp"]["kinds"]["namespace_definition"][:2] == [1, 0]
    assert routes.decide("R1d", f) == "cpp" and routes.decide("R1dg", f) == "c"
    g = probe.features(b"#ifndef FOO_H\n#define FOO_H\nnamespace a { int x; }\n#endif\n")  # an include guard is no guard
    assert g["cpp"]["kinds"]["namespace_definition"][:2] == [1, 1]


def test_an_extern_c_block_is_not_cpp(probe):
    f = probe.features(b'#ifdef __cplusplus\nextern "C" {\n#endif\nint f(int a);\n#ifdef __cplusplus\n}\n#endif\n')
    assert routes.decide("R1a", f) == "c"


def test_an_objc_interface_is_found_by_its_nodes_and_by_the_error_counts(probe):
    f = probe.features(b"@interface Foo : NSObject\n- (void)bar;\n@property int x;\n@end\n")
    assert f["objc"]["kinds"]["class_interface"][0] == 1 and f["objc"]["err"] == 0
    assert f["c"]["err"] > 0 and f["cpp"]["err"] > 0
    assert routes.decide("R1do", f) == "objc" and routes.decide("R2o", f) == "objc" and routes.decide("R3", f) == "objc"
    assert routes.decide("R1d", f) == "c"  # without the Objective-C grammar the nodes cannot name it


def test_the_error_counts_and_the_bytes_of_a_broken_header(probe):
    f = probe.features(b"int f(int a;\nint g(\n")
    assert f["c"]["err"] + f["c"]["missing"] > 0
    assert f["c"]["err_bytes"] >= 0 and f["size"] == 20


def test_an_empty_header_has_nothing(probe):
    f = probe.features(b"")
    assert f["size"] == 0 and f["cpp"]["kinds"] == {} and all(f[g]["err"] == 0 for g in routes.GRAMMARS)
    assert all(routes.decide(name, {**f, "r0": "c"}) == "c" for name in routes.ROUTES)  # the `x` routes read `r0` too


def test_every_part_has_a_parse_time_and_a_query_time(probe):
    f = probe.features(b"int a;\n")
    for g in routes.GRAMMARS:
        assert f[g]["ms"] >= 0 and f[g]["q_ms"] >= 0


def test_route_zero_is_the_products_detector_and_names_objc_when_it_answers_nothing(probe):
    assert probe.r0("int a;\n")[0] == "c"
    assert probe.r0("namespace a { int x; }\n")[0] == "cpp"
    assert probe.r0("@interface X\n@end\n")[0] == "objc"
    assert probe.r0("int a;\n")[1] >= 0


def test_symbols_are_the_functions_the_classes_and_their_methods(probe):
    src = "class A { public: int f() { return 1; } };\nint g() { return 2; }\n"
    assert probe.symbols(src, "cpp") > probe.symbols(src, "c") >= 0
    assert probe.symbols("", "cpp") == 0


def test_each_kind_and_each_error_carries_the_line_of_its_first_node(probe):
    f = probe.features(b"int a;\nnamespace a { int x; }\nnamespace b { }\n")
    assert f["cpp"]["kinds"]["namespace_definition"] == [2, 2, 2]
    g = probe.features(b"int a;\nint f(int a;\n")
    assert g["c"]["err_line"] == 2 and probe.features(b"int a;\n")["c"]["err_line"] == 0


def test_the_copies_of_the_products_patterns_are_the_products_so_a_change_there_fails_here(probe):
    import languages as product  # the product's module, on the path since the probe was built: it has `fixqc` since 25 November
    noise, cpp = patterns.VARIANTS["fixqc"]
    assert product._C_NOISE_RE.pattern == patterns.NOISE_FIXQ and product._C_NOISE_RE.flags == noise.flags
    assert product._CPP_HEADER_RE.pattern == patterns.CPP_FIXQC and product._CPP_HEADER_RE.flags == cpp.flags
    assert product._OBJC_HEADER_RE.pattern == patterns.BEFORE_OBJC and product._OBJC_HEADER_RE.flags == patterns.OBJC.flags


def test_the_product_answers_as_its_copy_here_and_where_it_differs_from_the_rule_before_it_is_the_designed_case(probe):
    for text in ("int a;\n", "namespace a { int x; }\n", "@interface X\n@end\n", "/* c */ class A { int f; };\n", "// class A {\n", "",
                 "#include <foo/*>\nnamespace a { }\n"):
        assert patterns.answer(text, "fixqc") == probe.r0(text)[0], text
    never_closed = "#include <foo/*>\nnamespace a { }\n"
    assert patterns.answer(never_closed) == "cpp" and probe.r0(never_closed)[0] == "c"  # the rule before and the product part here


def test_the_probe_times_a_candidate_and_gives_its_answer(probe):
    for variant in patterns.VARIANTS:
        answer, ms = probe.r0_variant("namespace a { int x; }\n", variant)
        assert answer == "cpp" and ms >= 0
    with pytest.raises(KeyError):
        probe.r0_variant("int a;\n", "fix2")
