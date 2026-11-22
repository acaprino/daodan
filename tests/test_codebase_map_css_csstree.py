"""The facts `css_csstree.js` hands `css.tree_records` (the ESLint fork of CSSTree over plain CSS), against records
written by hand from what each CSS form means. The trees are the neutral ones the script documents (`{t, line, ...}`).
The tests of the first part run no engine. The ones marked `ON_MODAL`, the last part, start the pinned Node and the pinned
engine (`css.node_runner` installs them) over small texts and read the script's own trees: they skip anywhere but on
Modal. The engine's recorded runs over the fixtures are replayed by `test_codebase_map_css_graph.py`;
`benchmarks/css-parser/` has the A/B on a corpus.

    python -B -m pytest -q -p no:cacheprovider tests/test_codebase_map_css_csstree.py
    python tests/modal_pytest.py tests/test_codebase_map_css_csstree.py -q          # with the engine
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "daodan/core"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
from indexers import css, css_csstree  # noqa: E402

REL = "src/a.css"


def decl(prop, value="x", line=1, **facts):
    return {"t": "decl", "line": line, "end": line, "prop": prop, "value": value, "important": False, "facts": facts}


def rule(sel, kids=(), line=1, names=(), custom=(), lost=()):
    return {"t": "rule", "line": line, "end": line, "sel": [sel], "names": [list(n) for n in names],
            "custom": list(custom), "kids": list(kids), **({"lost": list(lost)} if lost else {})}


def at(kind, params="", kids=None, line=1, text=None, **facts):
    return {"t": "at", "line": line, "end": line, "name": kind, "params": params, "facts": facts, "kids": kids,
            **({"text": text} if text else {})}


def records(tree, rel=REL, **options):
    return css.tree_records(rel, tree, "css", **options)


def of(out, kind):
    return [r for r in out if r["t"] == kind]


def refs(out, kind):
    return sorted((r["name"], r["site"], r["from"]) for r in of(out, "ref") if r["kind"] == kind)


def nodes(out):
    return {r["id"]: r for r in of(out, "node")}


# --- selectors: the names come from the parsed selector, with the mode that reaches them

def test_a_rule_names_its_classes_and_ids_with_the_mode_of_each():
    tree = [rule(".a :global(.b) #c", names=[("class", "a", "local"), ("class", "b", "global"), ("id", "c", "local")])]
    node = of(records(tree, module="src/a.module.css"), "node")[0]
    assert node["id"] == f"{REL}:1 .a :global(.b) #c"
    assert node["names"] == [["class", "a", "src/a.module.css"], ["class", "b", None], ["id", "c", "src/a.module.css"]]


def test_deep_names_of_a_scoped_block_belong_to_the_component_below():
    tree = [rule(".a .b", names=[("class", "a", "local"), ("class", "b", "deep")])]
    node = of(records(tree, module="scoped:src/C.vue"), "node")[0]
    assert node["names"] == [["class", "a", "scoped:src/C.vue"], ["class", "b", "deep:src/C.vue"]]


def test_a_nested_rule_names_its_parents_and_reads_as_a_css_nesting_does():
    tree = [rule(".a, .b", names=[("class", "a", "local"), ("class", "b", "local")], kids=[
        rule("&:hover", line=2, names=[]), rule(".c &", line=3, names=[("class", "c", "local")])])]
    found = nodes(records(tree))
    assert sorted(found) == [f"{REL}:1 .a, .b", f"{REL}:2 :is(.a, .b):hover", f"{REL}:3 .c :is(.a, .b)"]
    assert found[f"{REL}:2 :is(.a, .b):hover"]["names"] == [["class", "a", None], ["class", "b", None]]
    assert found[f"{REL}:3 .c :is(.a, .b)"]["names"] == [["class", "a", None], ["class", "b", None], ["class", "c", None]]


def test_a_rule_inside_an_at_rule_is_labelled_with_it_and_a_scope_adds_its_names():
    tree = [at("scope", "(.shell) to (.limit)", line=1, names=[["class", "shell", "local"], ["class", "limit", "local"]],
               kids=[rule("img", line=2, names=[])]),
            at("media", "(min-width: 1px)", kids=[rule(".m", line=3, names=[("class", "m", "local")])], line=3)]
    found = nodes(records(tree))
    assert found[f"{REL}:2 @scope (.shell) to (.limit) {{ img }}"]["names"] == [["class", "limit", None],
                                                                                 ["class", "shell", None]]
    assert f"{REL}:3 @media (min-width: 1px) {{ .m }}" in found


def test_a_custom_selector_in_a_rule_is_a_reference_to_the_one_the_sheet_defines():
    tree = [at("custom-selector", ":--heading h1, h2", line=1, word=":--heading"),
            rule(":--heading", line=2, custom=[":--heading"])]
    out = records(tree)
    assert nodes(out)[f"{REL}:1 @custom-selector :--heading"]["names"] == [["custom-selector", ":--heading"]]
    assert refs(out, "custom-selector") == [(":--heading", f"{REL}:2", f"{REL}:2 :--heading")]


# --- values: the references a declaration makes, from the tree and the lexer

def test_a_var_reference_keeps_its_fallback_and_its_own_line():
    tree = [rule(".a", names=[("class", "a", "local")], kids=[
        decl("color", "VAR(--accent, calc(1px + 2px))", line=2, vars=[{"name": "--accent", "fallback": "calc(1px + 2px)",
                                                                          "dl": 0}]),
        decl("margin", "0 var(--a)\n var(--b)", line=3, vars=[{"name": "--a", "fallback": None, "dl": 0},
                                                              {"name": "--b", "fallback": None, "dl": 1}])])]
    found = of(records(tree, offset=10), "ref")
    assert [(r["name"], r["site"], r["fallback"]) for r in found] == [
        ("--accent", f"{REL}:12", "calc(1px + 2px)"), ("--a", f"{REL}:13", None), ("--b", f"{REL}:14", None)]


def test_a_custom_property_declaration_is_a_node():
    out = records([rule(".a", kids=[decl("--gap", "4px", line=2)])])
    assert nodes(out)[f"{REL}:2 --gap"]["names"] == [["custom-property", "--gap"]]


def test_names_the_lexer_finds_in_animation_font_and_container_are_references():
    tree = [rule(".a", kids=[decl("animation", "spin 1s, \"pulse\" 2s", line=2, kf=["spin", "pulse"]),
                             decl("font", "12px \"Brand Sans\", serif", line=3, ff=["Brand Sans"]),
                             decl("container", "side / inline-size", line=4, ct=["side"])])]
    out = records(tree)
    assert refs(out, "keyframes") == [("pulse", f"{REL}:2", f"{REL}:1 .a"), ("spin", f"{REL}:2", f"{REL}:1 .a")]
    assert [(r["name"], r["symbol"]) for r in of(out, "ref") if r["kind"] == "font-face"] == [("brand sans", "Brand Sans")]
    assert f"{REL}:4 container side" in nodes(out)


def test_a_family_in_a_font_face_is_not_a_reference():
    tree = [at("font-face", kids=[decl("font-family", "Brand Sans", line=2, ff=["Brand Sans"], fam="Brand Sans")],
               family="Brand Sans", line=1)]
    out = records(tree)
    assert nodes(out)[f"{REL}:1 @font-face Brand Sans"]["names"] == [["font-face", "brand sans"]]
    assert refs(out, "font-face") == []


def test_a_value_the_lexer_does_not_match_is_a_hole_not_a_guess_from_its_words():
    tree = [rule(".a", kids=[decl("font-family", "var(--f), \"Open Sans\"", line=2,
                                  vars=[{"name": "--f", "fallback": None, "dl": 0}],
                                  unmatched="Matching for a tree with var() is not supported"),
                             decl("animation", "var(--a) spin", line=3, unmatched="Mismatch")])]
    out = records(tree)
    assert refs(out, "font-face") == [] and refs(out, "keyframes") == []
    assert [(h["file"], h["line"], h["kind"], h["cls"], h["name"]) for h in of(out, "hole")] == [
        (REL, 2, "font-face", "value-not-matched", "font-family: Matching for a tree with var() is not supported"),
        (REL, 3, "keyframes", "value-not-matched", "animation: Mismatch")]
    assert refs(out, "custom-property") == [("--f", f"{REL}:2", f"{REL}:1 .a")]  # the tree still gives the var()


def test_composes_and_the_words_of_a_module_value_come_from_the_tree():
    tree = [rule(".a", kids=[decl("composes", "b c from \"./x.module.css\"", line=2,
                                  composes={"names": ["b", "c"], "from": "./x.module.css"}),
                             decl("composes", "d from global", line=3, composes={"names": ["d"], "from": "global"}),
                             decl("composes", "e", line=4, composes={"names": ["e"], "from": None}),
                             decl("border", "1px solid brand", line=5, words=["solid", "brand"])])]
    out = records(tree, module="src/a.module.css")
    found = sorted((r["name"], r["site"], r["origin"]) for r in of(out, "ref") if r["kind"] == "composes")
    assert found == [("b", f"{REL}:2", "./x.module.css"), ("c", f"{REL}:2", "./x.module.css"),
                     ("d", f"{REL}:3", "global"), ("e", f"{REL}:4", None)]
    words = [r for r in of(out, "ref") if r["kind"] == "css-value"]
    assert sorted(r["name"] for r in words) == ["brand", "solid"] and all(r["optional"] for r in words)


def test_a_value_names_no_module_word_outside_a_module():
    out = records([rule(".a", kids=[decl("border", "1px solid brand", line=2, words=["solid", "brand"])])])
    assert [r for r in of(out, "ref") if r["kind"] == "css-value"] == []


# --- at-rules

def test_an_import_names_every_url_and_the_layer_it_declares():
    tree = [at("import", "url(\"./a.css\") layer(base.x) supports(selector(:has(a))) screen", line=1,
               urls=["./a.css"], layer="base.x"),
            at("import", "\"b.css\" layer", line=2, urls=["b.css"], layer=""),
            at("import", "url(c.css)", line=3, urls=["c.css"])]
    out = records(tree)
    assert refs(out, "import") == [("./a.css", f"{REL}:1", REL), ("b.css", f"{REL}:2", REL), ("c.css", f"{REL}:3", REL)]
    assert [(n["id"]) for n in of(out, "node")] == [f"{REL}:1 @layer base.x"]  # a bare `layer` is anonymous: no name


def test_layers_are_declared_where_they_first_appear_and_a_nested_one_is_dotted():
    tree = [at("layer", "reset, base", line=1, names=["reset", "base"]),
            at("layer", "base", line=2, names=["base"], kids=[
                at("layer", "inner", line=3, names=["inner"], kids=[rule(".x", line=4, names=[("class", "x", "local")])])])]
    out = records(tree)
    assert sorted(n["id"] for n in of(out, "node") if n["kind"] == "layer") == [
        f"{REL}:1 @layer base", f"{REL}:1 @layer reset", f"{REL}:3 @layer base.inner"]
    assert refs(out, "layer") == [("base", f"{REL}:2", REL)]
    assert [r["to"] for r in of(out, "ref") if r["kind"] == "layer"] == [f"{REL}:1 @layer base"]


def test_a_container_query_names_the_container_it_asks():
    tree = [at("container", "side (min-width: 400px)", line=1, names=["side"],
               kids=[rule(".a", line=2, names=[("class", "a", "local")])]),
            at("container", "(min-width: 1px)", line=3, names=[], kids=[])]
    out = records(tree)
    assert refs(out, "container") == [("side", f"{REL}:1", REL)]
    assert f"{REL}:2 @container side (min-width: 400px) {{ .a }}" in nodes(out)


def test_a_media_query_names_the_custom_media_it_uses_and_a_statement_defines_one():
    tree = [at("custom-media", "--narrow (max-width: 30em)", line=1, word="--narrow"),
            at("media", "(--narrow) and (min-width: 1px)", line=2, custom=["--narrow"], kids=[])]
    out = records(tree)
    assert nodes(out)[f"{REL}:1 @custom-media --narrow"]["names"] == [["custom-media", "--narrow"]]
    assert refs(out, "custom-media") == [("--narrow", f"{REL}:2", REL)]


def test_the_at_rules_tailwind_reads_name_their_node_or_their_reference():
    tree = [at("utility", "tab-*", line=1, word="tab-*", kids=[decl("tab-size", "x", line=2)]),
            at("utility", "card", line=3, word="card", kids=[]),
            at("custom-variant", "dark (&:where(.dark, .dark *))", line=4, word="dark"),
            at("variant", "dark", line=5, word="dark", kids=[]),
            at("apply", "font-bold hover:underline", line=6, tokens="font-bold hover:underline"),
            at("source", "inline(\"underline\")", line=7, inline="underline", path=None),
            at("source", "not \"../x\"", line=8, inline=None, path="../x"),
            at("plugin", "\"@tailwindcss/typography\"", line=9, path="@tailwindcss/typography"),
            at("config", "\"./tailwind.config.js\"", line=10, path="./tailwind.config.js"),
            at("tailwind", "base", line=11)]
    out = records(tree)
    found = {n["id"]: n for n in of(out, "node")}
    assert found[f"{REL}:1 @utility tab-*"]["names"] == [["utility-pattern", "tab-"]]
    assert found[f"{REL}:3 @utility card"]["names"] == [["utility", "card"]]
    assert found[f"{REL}:4 @custom-variant dark"]["names"] == [["variant", "dark"]]
    assert [(r["name"], r["symbol"], r["optional"]) for r in of(out, "ref") if r["kind"] == "variant"] == [
        ("dark", "dark", True)]
    assert [(c["chain"], c["alts"]) for c in of(out, "classes")] == [
        (["@apply"], [[{"s": "font-bold hover:underline"}]]), (["@source inline"], [[{"s": "underline"}]])]
    assert sorted((r["kind"], r["name"]) for r in of(out, "ref") if r["kind"] in ("source", "plugin", "config")) == [
        ("config", "./tailwind.config.js"), ("plugin", "@tailwindcss/typography"), ("source", "../x")]
    assert refs(out, "import") == [("tailwindcss", f"{REL}:11", REL)]


def test_a_css_modules_value_defines_a_name_or_imports_it():
    tree = [at("value", "primary: #BF4040", line=1, define="primary"),
            at("value", "a, b as c from \"./x.module.css\"", line=2, **{"from": "./x.module.css"},
               items=[{"name": "a", "local": "a"}, {"name": "b", "local": "c"}])]
    out = records(tree, module="src/a.module.css")
    assert nodes(out)[f"{REL}:1 @value primary"]["names"] == [["css-value", "primary", "src/a.module.css"]]
    assert sorted((r["name"], r["local"], r["origin"]) for r in of(out, "ref") if r["kind"] == "css-value") == [
        ("a", "a", "./x.module.css"), ("b", "c", "./x.module.css")]
    assert [r for r in records(tree) if r["t"] in ("node", "ref")] == []  # outside a module a `@value` is nothing


def test_keyframes_font_face_and_property_make_the_nodes_their_names_reach():
    tree = [at("keyframes", "\"spin\"", line=1, name="spin", kids=[rule("from", line=2, names=[])]),
            at("property", "--angle", line=3, kids=[decl("syntax", "\"<angle>\"", line=4)])]
    found = nodes(records(tree))
    assert found[f"{REL}:1 @keyframes spin"]["names"] == [["keyframes", "spin"]]
    assert f"{REL}:2 from" not in found  # a keyframe selector is no rule
    assert found[f"{REL}:3 @property --angle"]["names"] == [["custom-property", "--angle"]]


# --- what the parser keeps as Raw is a hole with its file and line, never read again by a rule on its shape

def raw_decl(prop, value, line=1):
    return {"t": "decl", "line": line, "end": line, "prop": prop, "value": value, "important": False, "raw": True,
            "facts": {}}


def test_raw_statements_rules_and_declarations_are_holes_with_their_lines():
    tree = [{"t": "hole", "line": 1, "end": 1, "kind": "statement", "name": "$gap: 4px"},
            rule(".a", line=2, names=[("class", "a", "local")], kids=[raw_decl("margin", "$gap", line=3)]),
            {"t": "hole", "line": 4, "end": 4, "kind": "rule", "name": "&:has(.x", "kids": []}]
    out = records(tree, offset=5)
    assert [(h["file"], h["line"], h["kind"], h["cls"], h["name"]) for h in of(out, "hole")] == [
        (REL, 6, "statement", "unparsed", "$gap: 4px"), (REL, 8, "declaration", "unparsed", "margin: $gap"),
        (REL, 9, "rule", "unparsed", "&:has(.x")]
    assert f"{REL}:7 .a" in nodes(out)  # what the parser did read is still there


def test_a_rule_whose_prelude_is_raw_has_its_block_read_all_the_same():
    """Else a `--y` it declares would be reported undeclared where it is used."""
    tree = [{"t": "hole", "line": 1, "end": 3, "kind": "rule", "name": "b[", "kids": [
        decl("--y", "1", line=2), decl("color", "var(--z)", line=3, vars=[{"name": "--z", "fallback": None, "dl": 0}])]}]
    out = records(tree)
    assert [(h["line"], h["kind"], h["cls"]) for h in of(out, "hole")] == [(1, "rule", "unparsed")]
    assert f"{REL}:2 --y" in nodes(out) and refs(out, "custom-property") == [("--z", f"{REL}:3", REL)]


def test_a_custom_property_whose_value_is_raw_is_declared_and_a_hole():
    out = records([rule(".a", names=[("class", "a", "local")], kids=[raw_decl("--w", "$white", line=2)])])
    assert nodes(out)[f"{REL}:2 --w"]["names"] == [["custom-property", "--w"]]
    assert [(h["line"], h["kind"], h["name"]) for h in of(out, "hole")] == [(2, "declaration", "--w: $white")]


def test_a_selector_argument_no_selector_reads_is_a_hole():
    tree = [rule(":global(.a", line=1, names=[], lost=[".a"]),
            at("scope", "(:is(", line=2, names=[], lost=["(("], kids=[])]
    out = records(tree)
    assert [(h["line"], h["kind"], h["cls"], h["name"]) for h in of(out, "hole")] == [
        (1, "selector", "unparsed", ".a"), (2, "selector", "unparsed", "((")]


def test_a_tree_the_walk_cannot_take_is_a_file_missing_with_the_reason_and_the_other_files_are_read():
    deep = leaf = rule(".a", names=[("class", "a", "local")])
    for _ in range(600):
        deep = rule(".b", kids=[deep], names=[("class", "b", "local")])

    def runner(script, payload):
        trees = {"deep.css": [deep], "ok.css": [leaf]}
        return {"version": "4.1.3", "seconds": 0, "sheets": {item["key"]: {"tree": trees[item["key"]]}
                                                              for item in payload["items"]}}, {}
    found = css.engine_sheets(runner, css_csstree, "css", Path("."), ["deep.css", "ok.css"], words=True)
    assert list(found["missing"]) == ["deep.css"] and found["missing"]["deep.css"].startswith("not parsed: ")
    assert [r["file"] for r in found["records"] if r["t"] == "file"] == ["ok.css"]


def test_an_at_rule_whose_prelude_is_no_tree_is_a_hole_and_its_block_is_still_read():
    tree = [at("container", "(((", line=1, unreadable=True, kids=[rule(".a", line=2, names=[("class", "a", "local")])]),
            at("import", "url(", line=3, unreadable=True)]
    out = records(tree)
    assert [(h["line"], h["kind"], h["cls"]) for h in of(out, "hole")] == [(1, "statement", "unparsed"),
                                                                         (3, "statement", "unparsed")]
    assert f"{REL}:2 @container ((( {{ .a }}" in nodes(out)


def test_a_custom_property_with_an_empty_value_is_declared():
    """`--bs-btn-font-family:;` is valid (CSS Variables): Bootstrap declares half its component variables so."""
    out = records([rule(".btn", names=[("class", "btn", "local")], kids=[decl("--bs-btn-font-family", "", line=2)])])
    assert nodes(out)[f"{REL}:2 --bs-btn-font-family"]["names"] == [["custom-property", "--bs-btn-font-family"]]
    assert of(out, "hole") == []


def test_an_at_rule_labels_what_is_inside_it_as_the_source_spells_it():
    tree = [at("media", "(min-width: 1px)", line=1, text="@media(min-width: 1px)",
               kids=[rule(".m", line=2, names=[("class", "m", "local")])])]
    assert list(nodes(records(tree))) == [f"{REL}:2 @media(min-width: 1px) {{ .m }}"]


def test_a_tailwind_directive_anywhere_in_a_sheet_makes_its_layers_tailwinds():
    """Tailwind's own `index.css` ends with `@layer utilities { @tailwind utilities; }`."""
    tree = [at("layer", "base", line=1, names=["base"], kids=[]),
            at("layer", "utilities", line=2, names=["utilities"], kids=[at("tailwind", "utilities", line=3)])]
    out = records(tree)
    assert [(r["name"], r.get("package")) for r in of(out, "ref") if r["kind"] == "layer"] == [
        ("base", "tailwindcss"), ("utilities", "tailwindcss")]


def test_layers_a_sheet_that_imports_tailwind_gets_from_it_are_its_not_declarations():
    tree = [at("import", '"tailwindcss"', line=1, urls=["tailwindcss"]),
            at("layer", "base", line=2, names=["base"], kids=[rule(".a", line=3, names=[("class", "a", "local")])]),
            at("layer", "mine", line=4, names=["mine"], kids=[])]
    out = records(tree)
    assert [(r["name"], r.get("package")) for r in of(out, "ref") if r["kind"] == "layer"] == [("base", "tailwindcss")]
    assert [n["id"] for n in of(out, "node") if n["kind"] == "layer"] == [f"{REL}:4 @layer mine"]


def test_a_nested_selector_list_is_an_is_for_a_sheet_and_expanded_for_a_scripts_css():
    """The node ids a script's CSS had (read as scss) stay: the caller names the mode."""
    tree = [rule("h1, h2", names=[("class", "x", "local")], kids=[rule("a", line=2)])]
    assert list(nodes(css.tree_records(REL, tree, "css"))) == [f"{REL}:1 h1, h2", f"{REL}:2 :is(h1, h2) a"]
    assert list(nodes(css.tree_records(REL, tree, "scss"))) == [f"{REL}:1 h1, h2", f"{REL}:2 h1 a, h2 a"]


def test_a_tree_as_deep_as_the_engine_allows_is_walked_and_not_missing():
    """`css_csstree.js` stops at 100 nested blocks (MAX_DEPTH): the walk in Python takes that, and the file is read."""
    deep = rule(".a", names=[("class", "a", "local")])
    for _ in range(100):
        deep = rule(".b", kids=[deep], names=[("class", "b", "local")])

    def runner(script, payload):
        return {"version": "4.1.3", "seconds": 0, "sheets": {item["key"]: {"tree": [deep]} for item in payload["items"]}}, {}
    found = css.engine_sheets(runner, css_csstree, "css", Path("."), ["deep.css"], words=True)
    assert found["missing"] == {} and [r["file"] for r in found["records"] if r["t"] == "file"] == ["deep.css"]


# --- the style attribute: a list of declarations, read as the declarations of the element

def test_a_style_attribute_is_declarations_without_a_rule():
    tree = [decl("font-family", "'Brand Sans', var(--f)", line=1, ff=["Brand Sans"], vars=[{"name": "--f", "fallback": None,
                                                                                         "dl": 0}]),
            decl("animation", "pulse 2s", line=1, kf=["pulse"])]
    out = records(tree, rel="src/index.html", offset=6)
    assert [r["kind"] for r in of(out, "node")] == []
    assert sorted((r["kind"], r["name"], r["site"], r["from"]) for r in of(out, "ref")) == [
        ("custom-property", "--f", "src/index.html:7", "src/index.html"),
        ("font-face", "brand sans", "src/index.html:7", "src/index.html"),
        ("keyframes", "pulse", "src/index.html:7", "src/index.html")]


# --- the engine's answer: a text it cannot read is a file missing with the reason, never a partial tree

def test_a_sheet_the_engine_could_not_read_is_missing_with_the_reason():
    def runner(script, payload):
        assert Path(script).name == "css_csstree.js"
        sheets = {item["key"]: ({"error": "RangeError: Maximum call stack size exceeded"} if item["key"] == "deep.css"
                                else {"tree": [rule(".a", names=[("class", "a", "local")])]}) for item in payload["items"]}
        return {"version": "4.1.3", "seconds": 0.1, "sheets": sheets}, {"seconds": 0.1, "peak_mb": 1}
    found = css.engine_sheets(runner, css_csstree, "css", Path("."), ["a.css", "deep.css", "b.scss", "c.pcss"], words=True)
    assert found["missing"] == {"deep.css": "not parsed: RangeError: Maximum call stack size exceeded"}
    assert sorted(r["file"] for r in found["records"] if r["t"] == "file") == ["a.css", "c.pcss"]
    assert found["indexer"]["name"] == "@eslint/css-tree" and found["indexer"]["version"] == "4.1.3"


def test_the_engine_reads_css_files_by_path_and_the_hand_reader_leaves_them():
    seen = []

    def runner(script, payload):
        seen.append(payload["items"])
        return {"version": "4.1.3", "seconds": 0, "sheets": {item["key"]: {"tree": []} for item in payload["items"]}}, {}
    files = ["a.css", "b.pcss", "c.postcss", "d.module.css", "e.scss"]
    css.engine_sheets(runner, css_csstree, "css", Path("."), files, words=True)
    assert seen == [[{"key": "a.css", "path": "a.css", "words": False}, {"key": "b.pcss", "path": "b.pcss", "words": False},
                     {"key": "c.postcss", "path": "c.postcss", "words": False},
                     {"key": "d.module.css", "path": "d.module.css", "words": True}]]


def test_the_hand_reader_leaves_the_css_files_and_hands_the_style_texts_of_markup_to_the_engine(tmp_path):
    (tmp_path / "a.css").write_text(".a { color: red }\n", encoding="utf-8")
    (tmp_path / "index.html").write_text('<style>\n.a { color: red }\n</style>\n<p style="color: red; margin: 0">x</p>\n',
                                         encoding="utf-8")
    found = css.parse(tmp_path, ["a.css", "index.html"])
    assert [r for r in found["records"] if r["file"] == "a.css"] == [] and "a.css" not in found["missing"]
    assert [(s["key"], s["rel"], s["offset"], s.get("kind"), s["text"]) for s in found["styles"]] == [
        ("index.html#style0", "index.html", 0, None, "\n.a { color: red }\n"),
        ("index.html#style1", "index.html", 3, "declarations", "color: red; margin: 0")]


# --- the engine itself (`css_csstree.js`, the pinned `@eslint/css-tree` 4.1.3): on Modal, where the pinned Node and
# the engines are installed (tests/modal_pytest.py); the trees are the script's own, read as the graph reads them.

ON_MODAL = pytest.mark.skipif(not os.environ.get("MODAL_TASK_ID"), reason="the engine runs on Modal (tests/modal_pytest.py)")


@pytest.fixture(scope="module")
def engine(tmp_path_factory):
    """`read({key: text | bytes}, **item)` -> {key: tree | {"error"}}: bytes are a file read by path, text a text."""
    project = tmp_path_factory.mktemp("project")
    runner = css.node_runner(project, tmp_path_factory.mktemp("work"))

    def read(sources, **options):
        items = []
        for key, source in sources.items():
            if isinstance(source, bytes):
                (project / key).write_bytes(source)
                items.append({"key": key, "path": key, **options})
            else:
                items.append({"key": key, "text": source, **options})
        sheets = css_csstree.index(runner, items)["sheets"]
        return {key: sheet.get("tree", sheet) for key, sheet in sheets.items()}
    return read


def only(tree, kind):
    return [n for n in tree if n["t"] == kind]


@ON_MODAL
def test_every_newline_form_gives_the_lines_of_the_snapshots_text(engine):
    """The snapshot reads a file with universal newlines (CRLF and CR are LF) and counts LF only: a form feed is no
    line end for it, and CSSTree counts it as one."""
    source = "a{}\r\nb{}\rc{}\x0cd{}\ne{}\n"
    found = engine({"nl.css": source.encode("utf-8")}) | engine({"nl-text": source})
    assert [[n["line"] for n in only(found[key], "rule")] for key in ("nl.css", "nl-text")] == [[1, 2, 3, 3, 4]] * 2
    assert [n["sel"] for n in only(found["nl.css"], "rule")] == [["a"], ["b"], ["c"], ["d"], ["e"]]


@ON_MODAL
def test_an_at_rules_text_is_its_own_slice_whatever_comes_before_it(engine):
    """Offsets are UTF-16 units: an astral character before the rule moves them by two, a comment inside the prelude
    is blanked, the `AtrulePrelude`'s own location (one parenthesis short) is not used."""
    source = ('/* 😀😀 */\n@import "a.css" /* x */ layer(x) supports(display: grid);\n'
              '.a { content: "😀😀"; color: red }\n@supports (not (display: inline-grid)) { .😀 { color: red } }\n')
    tree = engine({"u.css": source.encode("utf-8")})["u.css"]
    [imported, rule, supports] = tree
    assert imported["params"] == '"a.css" layer(x) supports(display: grid)'
    assert imported["facts"] == {"urls": ["a.css"], "layer": "x"} and imported["line"] == 2
    assert [d["value"] for d in rule["kids"]] == ['"😀😀"', "red"]
    assert supports["params"] == "(not (display: inline-grid))" and supports["line"] == 4
    assert supports["kids"][0]["names"] == [["class", "😀", "local"]]


@ON_MODAL
def test_a_parse_error_on_a_tree_that_is_right_is_no_hole(engine):
    source = ('@supports (not (display: inline-grid)) { .a { color: red } }\n@import "b.css" supports(selector(:has(a)));\n'
              '@import url(c.css) layer(base.x) supports(display: grid) screen and (min-width: 1px);\n.c { color: red }\n')
    tree = engine({"e.css": source.encode("utf-8")})["e.css"]
    assert [n["t"] for n in tree] == ["at", "at", "at", "rule"]
    assert [n["facts"].get("urls") for n in tree[1:3]] == [["b.css"], ["c.css"]] and tree[2]["facts"]["layer"] == "base.x"


@ON_MODAL
def test_a_sheet_that_cannot_be_read_is_an_error_of_its_own_and_the_others_are_read(engine):
    found = engine({"deep.css": (".a{" * 150 + "}" * 150).encode("utf-8"), "bytes.css": b"a{color:\xff}",
                    "ok.css": b".a{color:red}", "text-deep": ".a{" * 150 + "}" * 150})
    assert found["deep.css"]["error"] == "Error: blocks nested deeper than 100" == found["text-deep"]["error"]
    assert found["bytes.css"]["error"].startswith("TypeError")
    assert [n["sel"] for n in found["ok.css"]] == [[".a"]]


@ON_MODAL
def test_what_the_parser_keeps_as_raw_is_a_hole_and_never_swallows_what_it_still_read(engine):
    """A Raw prelude that is unbalanced runs to the end of the sheet (CSS Syntax): each such form is a sheet of its own."""
    source = (".a, { --y: 1; color: var(--z) }\n.b { c: d;; ; --w: $white; --j: { x: 1 } }\n"
              "@media screen and { .x { y: z } }\n.k { @container (min-width: 1px) { & .b { c: d } } }\n")
    found = engine({"raw.css": source, "unknown.css": "@foo (((a { b: c }\n", "statement.css": ".q:not( { b: c }\n"})
    first, second, media, last = found["raw.css"]
    assert (first["t"], first["kind"], first["name"], [k["prop"] for k in first["kids"]]) == ("hole", "rule", ".a,", ["--y", "color"])
    assert [(k["prop"], k.get("raw")) for k in second["kids"]] == [
        ("c", None), ("--w", True), ("--j", True)]  # a stray `;` is nothing, a Raw value is a declaration and a hole
    assert media["facts"] == {"unreadable": True} and [n["sel"] for n in media["kids"]] == [[".x"]]
    assert [(n["t"], n["sel"]) for n in last["kids"][0]["kids"]] == [("rule", ["& .b"])]  # read again, see below
    assert [(n["t"], n["name"], n["facts"]) for n in found["unknown.css"]] == [("at", "foo", {"unreadable": True})]
    assert [(n["t"], n["kind"]) for n in found["statement.css"]] == [("hole", "statement")]


@ON_MODAL
def test_what_the_parser_places_wrongly_inside_a_block_is_read_again_as_the_contents_of_a_block(engine):
    """The parser takes `--a: 1; @keyframes k { }` for one rule whose prelude is Raw, and a rule that starts with `&`
    inside an at-rule inside a rule for a Raw statement: inside a block the same parser reads the text again whole, at the
    positions of the source, comments blanked; what it still cannot read is a hole, once."""
    source = ("@theme default {\n  --a: 1;\n  --b: calc(1 / 3); /* c */\n  @keyframes spin { to { x: y } }\n  --y: 2;\n}\n"
              ".k { @container (min-width: 1px) {\n  & .b { c: d }\n  & .e /* c */ { f: g } } }\n"
              ".m { @media x {\n  & .b { c: d }\n  .z[ { y: z } } }\n")
    [theme, k, m] = engine({"re.css": source})["re.css"]
    assert [(n["t"], n.get("prop") or n.get("name"), n["line"]) for n in theme["kids"]] == [
        ("decl", "--a", 2), ("decl", "--b", 3), ("at", "keyframes", 4), ("decl", "--y", 5)]
    assert theme["kids"][2]["kids"][0]["sel"] == ["to"]
    [container] = k["kids"]
    assert [(n["t"], n["sel"], n["line"]) for n in container["kids"]] == [("rule", ["& .b"], 8), ("rule", ["& .e"], 9)]
    [media] = m["kids"]
    assert [(n["t"], n.get("sel") or n.get("kind"), n["line"]) for n in media["kids"]] == [
        ("rule", ["& .b"], 11), ("hole", "statement", 12)]


@ON_MODAL
def test_an_empty_custom_property_is_a_declaration_and_an_at_rule_keeps_its_spelling(engine):
    found = engine({"e.css": ".a { --e:; --f: ; --g: x }\n@media(min-width: 1px){.a{b:c}}\n"})["e.css"]
    [rule, media] = found
    assert [(d["prop"], d["value"], d.get("raw")) for d in rule["kids"]] == [("--e", "", None), ("--f", "", None),
                                                                              ("--g", "x", None)]
    assert (media["text"], media["params"]) == ("@media(min-width: 1px)", "(min-width: 1px)")


@ON_MODAL
def test_a_value_the_lexer_cannot_match_is_a_hole_only_where_a_name_could_hide(engine):
    source = (".a { font-family: var(--f); animation: var(--a) 1s; font: 12px var(--f), serif; "
              "font-family: var(--f, Arial); animation: spin 1s; font: 12px \"Brand Sans\", serif }")
    [rule] = engine({"v.css": source})["v.css"]
    facts = [d["facts"] for d in rule["kids"]]
    assert ["unmatched" in f for f in facts] == [False, False, True, True, False, False]
    assert facts[4]["kf"] == ["spin"] and facts[5]["ff"] == ["Brand Sans"]
    assert facts[0]["vars"] == [{"name": "--f", "fallback": None, "dl": 0}]


@ON_MODAL
def test_the_at_rules_the_grammar_does_not_know_are_read_from_their_exact_text(engine):
    source = ("@custom-media --narrow (max-width: 30em);\n@custom-selector :--heading h1, h2;\n@value primary: #BF4040;\n"
              '@value a, b as c from "./x.module.css";\n@apply p-4 hover:underline !important;\n'
              "@custom-variant dark (&:where(.dark, .dark *));\n")
    tree = engine({"x.module.css": source}, words=True)["x.module.css"]
    assert [n["facts"] for n in tree] == [
        {"word": "--narrow"}, {"word": ":--heading"}, {"define": "primary"},
        {"from": "./x.module.css", "items": [{"name": "a", "local": "a"}, {"name": "b", "local": "c"}]},
        {"tokens": "p-4 hover:underline"}, {"word": "dark"}]
    assert tree[0]["params"] == "--narrow (max-width: 30em)"


@ON_MODAL
def test_a_style_attribute_is_a_list_of_declarations_and_comments_leave_the_selectors(engine):
    found = engine({"attr": "color: red; font-family: 'Brand Sans', var(--f)"}, kind="declarations")
    assert [(d["t"], d["prop"], d["facts"].get("ff")) for d in found["attr"]] == [
        ("decl", "color", None), ("decl", "font-family", None)]  # `var()` in a family list: the lexer matches no syntax
    assert "unmatched" in found["attr"][1]["facts"]
    [rule] = engine({"c.css": ".a /* x */ .b,\n .c { }"})["c.css"]
    assert rule["sel"] == [".a .b, .c"]
