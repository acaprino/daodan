"""The probe: the three grammars' parses of a header, as the features the routes decide on. These run Daodan's own
loader (`languages._treesitter.get_parser`) and the pack's Objective-C grammar, so they need the grammars of the pinned
tree-sitter-language-pack in place, as Daodan's own tests do."""
from pathlib import Path

import pytest

import header_patterns as patterns
import header_probe
import header_routes as routes

CORE = Path(__file__).resolve().parents[2] / "daodan" / "core"


@pytest.fixture(scope="module")
def probe():
    return header_probe.Probe(str(CORE))


def detect_language(path, text):
    from languages import detect_language as product  # the product's, on the path once the probe is built
    return product(path, text)


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


def test_route_zero_is_the_rule_before_the_tree_and_names_objc_when_it_answers_nothing(probe):
    assert probe.r0("int a;\n")[0] == "c"
    assert probe.r0("namespace a { int x; }\n")[0] == "cpp"
    assert probe.r0("@interface X\n@end\n")[0] == "objc"
    assert probe.r0("#include <vector>\n")[0] == "cpp"  # by the name of the header: what the tree does not know
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


def test_the_product_keeps_two_of_the_frozen_patterns_so_a_change_there_fails_here(probe):
    from languages.detect.rules import header  # the product's module, on the path since the probe was built
    noise, _ = patterns.VARIANTS["fixqc"]
    assert header._C_NOISE_RE.pattern == patterns.NOISE_FIXQ and header._C_NOISE_RE.flags == noise.flags
    assert header._OBJC_HEADER_RE.pattern == patterns.BEFORE_OBJC and header._OBJC_HEADER_RE.flags == patterns.OBJC.flags


PARITY = (
    "int a;\n", "", "namespace a { int x; }\n", "@interface X\n@end\n", "class A { int f; };\n@interface X\n@end\n",
    "struct S { int a; int (*cb)(int); };\n", "struct S { void f(); };\n", "struct B : A { int x; };\n", "enum class E { a };\n",
    "template <typename T> T twice(T v);\n", "using namespace std;\n", "using Id = int;\n", "std::size_t bound(std::size_t n);\n",
    "#include <vector>\nint f(void);\n", "class a;\nstruct b;\n", "struct namespace { int id; };\n", "int f(int a;\nint g(\n",
    "void f(int *restrict p) { int virtual = 1; }\n", "#ifdef __cplusplus\nnamespace a { int x; }\n#endif\nint y;\n",
    "#if defined(__cplusplus)\nclass A { int x; };\n#else\nint y;\n#endif\n", "#ifndef X_H\n#define X_H\nnamespace a { }\n#endif\n",
    "/* class A { int f; }; */\nint a;\n", "// namespace a { }\nint a;\n", 'const char *s = "namespace a { }";\n',
    '#ifdef __cplusplus\nextern "C" {\n#endif\nint f(void);\n#ifdef __cplusplus\n}\n#endif\n',
    "struct Guard {\n  Guard() = default;\n  Guard &operator=(const Guard &) = delete;\n  ~Guard() { release(); }\n};\n",
)


def test_the_product_answers_as_route_r3dx_with_the_rule_before_in_front(probe):
    """Route R3dx is a decision over the features of the parses (`header_routes`): the Objective-C rule of before as the
    records have it (`r0`), then the nodes of its tier outside a `__cplusplus` block, then the fewer errors, C on a tie.
    The product reads the same for a header within its bound and with no comment left open."""
    for text in PARITY:
        wanted = routes.decide("R3dx", {**probe.features(text.encode()), "r0": probe.r0(text)[0]})
        got = detect_language(Path("a.h"), text)
        assert ("objc" if got is None else got) == wanted, text


def test_with_the_bound_off_a_longer_header_reads_as_route_r3dx_too(probe, monkeypatch):
    from languages.detect.rules import header
    text = "int a;\n" * 200 + "namespace a { int x; }\n"
    monkeypatch.setattr(header, "MAX_CHARS", 1_000)
    assert detect_language(Path("a.h"), text) == "c"  # the bound leaves the namespace out: the head is C
    monkeypatch.setattr(header, "MAX_CHARS", len(text))
    assert detect_language(Path("a.h"), text) == routes.decide("R3dx", {**probe.features(text.encode()), "r0": probe.r0(text)[0]}) == "cpp"


def test_the_probe_times_a_candidate_and_gives_its_answer(probe):
    for variant in patterns.VARIANTS:
        answer, ms = probe.r0_variant("namespace a { int x; }\n", variant)
        assert answer == "cpp" and ms >= 0
    with pytest.raises(KeyError):
        probe.r0_variant("int a;\n", "fix2")
