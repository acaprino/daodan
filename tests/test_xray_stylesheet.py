"""The stylesheet adapter and the cascade scanner.

A stylesheet decides whether a screen renders, scrolls and can be completed.
Until codebase-xray 4.1.0 the X-ray did not record one at all, and until 4.2.0
it recorded one only as a hash. The
motivating case is a Phazly incident of 2026-09-14: the rule
`.dark #root > div:first-child { position: relative; }` reached the consent
modal, the first child of the React root, and replaced its `position: fixed`,
so on mobile in dark theme the modal could not scroll and nobody could enter
the app. Every build and lint check accepted both rules.

Two properties are pinned here. The adapter turns every rule into a symbol
with an exact span, so an incremental run marks stale the claims about the
rule that changed and the symbols enclosing it, never those about its siblings. The scanner finds that exact signature mechanically: a
rule that reaches the root's untargeted children and sets a layout property,
next to the class rules it can silently override.

Most cases after the first set come from two adversarial reviews, one case per
confirmed defect. The one that mattered most: on the real Phazly tree the
scanner found the dark-theme rule and missed the modal, because the modal's
`position: fixed` was written `@apply fixed`, and in that tree
90% of the applied rules used `@apply`.
"""

import json
import shutil
import subprocess
import sys
import tempfile
import textwrap
import time
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "plugins/codebase-xray/skills/xray-method/scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from languages import SUPPORTED_EXTENSIONS, get_adapter  # noqa: E402

THEME_CSS = textwrap.dedent(
    """\
    /* Ambient glow for the dark theme. */
    .dark-ambient-glow {
      position: relative;
    }

    .dark #root > div:first-child {
      position: relative;
    }
    """
)

MODAL_CSS = textwrap.dedent(
    """\
    .terms-acceptance-modal {
      position: fixed;
      inset: 0;
      display: flex;
      flex-direction: column;
    }

    .terms-acceptance-modal__body {
      overflow-y: auto;
    }
    """
)


def write(directory: Path, rel: str, content: str) -> Path:
    path = directory / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def parse(content: str, name: str = "sheet.scss"):
    return get_adapter("css").parse(content, name)


def symbols(result):
    return [(c.name, c.kind, c.line_number, c.end_line) for c in result.classes]


def names(result):
    return [c.name for c in result.classes]


def styled(content: str, name: str):
    from languages.stylesheet import dialect_for, iter_styled_blocks, parse_sheet

    return [
        (node.selectors, [(d.property, d.value) for d in node.declarations])
        for node in iter_styled_blocks(parse_sheet(content, dialect_for(name)))
    ]


def scratch(test: unittest.TestCase, prefix: str) -> Path:
    tmp = Path(tempfile.mkdtemp(prefix=prefix))
    test.addCleanup(shutil.rmtree, tmp, True)
    return tmp


def xray(*args):
    """Invoke snapshot.py as the workflows do; return (code, combined output)."""
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / "snapshot.py"), *[str(a) for a in args]],
        capture_output=True,
        text=True,
    )
    return proc.returncode, proc.stdout + proc.stderr


class StylesheetRegistryTests(unittest.TestCase):
    def test_stylesheet_extensions_map_to_the_css_adapter(self):
        for suffix in (".css", ".scss", ".less"):
            self.assertEqual(SUPPORTED_EXTENSIONS.get(suffix), "css")
        # Indented Sass has no braces to tokenize: it stays a file-level entry.
        self.assertNotIn(".sass", SUPPORTED_EXTENSIONS)

    def test_parse_file_dispatches_a_stylesheet(self):
        from ast_parser import parse_file

        result = parse_file(write(scratch(self, "xray-css-"), "theme.css", THEME_CSS))
        self.assertEqual(result.language, "css")
        self.assertTrue(result.notes[0].startswith("parser=stylesheet"), result.notes)


class StylesheetAdapterTests(unittest.TestCase):
    def test_each_top_level_rule_is_a_symbol_with_an_exact_span(self):
        self.assertEqual(symbols(parse(THEME_CSS, "theme.css")), [
            (".dark-ambient-glow", "rule", 2, 4),
            (".dark #root > div:first-child", "rule", 6, 8),
        ])

    def test_an_at_rule_encloses_its_rules_under_qualified_names(self):
        source = textwrap.dedent(
            """\
            @media (max-width: 600px) {
              .a { color: red; }
              .b,
              .c { color: blue; }
            }
            """
        )
        self.assertEqual(symbols(parse(source, "m.css")), [
            ("@media (max-width: 600px)", "at-rule", 1, 5),
            ("@media (max-width: 600px) { .a }", "rule", 2, 2),
            ("@media (max-width: 600px) { .b, .c }", "rule", 3, 4),
        ])

    def test_nesting_is_flattened_into_the_selector_it_applies_as(self):
        source = textwrap.dedent(
            """\
            .card {
              color: red;
              &:hover { color: blue; }
              .title, &__body { margin: 0; }
              > .icon { width: 1px; }
              @media (min-width: 10px) {
                .x { top: 0; }
              }
            }
            .a, .b {
              .c { color: red; }
            }
            """
        )
        rule_names = [name for name, kind, _, _ in symbols(parse(source)) if kind == "rule"]
        self.assertEqual(rule_names, [
            ".card",
            ".card:hover",
            ".card .title, .card__body",
            ".card > .icon",
            "@media (min-width: 10px) { .card .x }",
            ".a, .b",
            ".a .c, .b .c",
        ])

    def test_native_css_nesting_substitutes_the_parent_list_once(self):
        # CSS Nesting gives `&` the meaning of :is(<parent list>); Sass substitutes each parent.
        source = ".a, .b {\n  & + & { position: relative; }\n}\n"
        self.assertEqual(names(parse(source, "n.css")), [".a, .b", ":is(.a, .b) + :is(.a, .b)"])
        self.assertEqual(names(parse(source, "n.scss")), [".a, .b", ".a + .a, .b + .b"])

    def test_strings_comments_urls_and_interpolation_do_not_break_blocks(self):
        source = textwrap.dedent(
            """\
            .a::before { content: "}{;"; }
            /* .ghost { color: red; } */
            // .ghost2 { color: red; }
            .b { background: url(data:image/png;base64,AAA//BBB); }
            .c-#{$name} { color: red; }
            .d { color: red }
            """
        )
        self.assertEqual(symbols(parse(source)), [
            (".a::before", "rule", 1, 1),
            (".b", "rule", 4, 4),
            (".c-#{$name}", "rule", 5, 5),
            (".d", "rule", 6, 6),
        ])

    def test_a_comment_inside_parentheses_does_not_swallow_the_rest_of_the_file(self):
        rule = ".dark #root > div:first-child {\n  position: relative;\n}\n"
        for comment in ("// above toasts (see _toast.scss", "// above toasts /* legacy"):
            with self.subTest(comment=comment):
                source = f"$z: (\n  modal: 100, {comment}\n  toast: 50,\n);\n" + rule
                self.assertEqual(symbols(parse(source, "theme.scss")), [
                    ("$z", "variable", 1, 4),
                    (".dark #root > div:first-child", "rule", 5, 7),
                ])
        source = ".a { background: image-set(url(//cdn.example.com/a.png) 1x); }\n.b { color: red; }\n"
        self.assertEqual(names(parse(source, "u.scss")), [".a", ".b"])

    def test_a_byte_order_mark_is_not_part_of_the_first_statement(self):
        result = parse('\ufeff@use "variables";\n.page { margin: 0; }\n', "main.scss")
        self.assertEqual([(i.module, i.is_internal) for i in result.imports], [("./variables", True)])
        media = parse("\ufeff@media (max-width: 600px) {\n  #app > div { overflow: hidden; }\n}\n", "bp.css")
        self.assertEqual(symbols(media), [
            ("@media (max-width: 600px)", "at-rule", 1, 3),
            ("@media (max-width: 600px) { #app > div }", "rule", 2, 2),
        ])

    def test_html_comment_delimiters_are_discarded(self):
        self.assertEqual(names(parse("<!--\n.a { x: y; }\n-->\n.b { x: y; }\n", "c.css")), [".a", ".b"])

    def test_a_repeated_selector_keeps_one_symbol_per_occurrence(self):
        source = ".dup {\n  color: red;\n}\n.middle {\n  color: green;\n}\n.dup {\n  margin: 0;\n}\n"
        self.assertEqual(symbols(parse(source, "a.css")), [
            (".dup", "rule", 1, 3),
            (".middle", "rule", 4, 6),
            (".dup (2)", "rule", 7, 9),
        ])

    def test_definitions_and_keyframes_are_not_applied_rules(self):
        source = textwrap.dedent(
            """\
            @mixin center($w) {
              .inner { margin: auto; }
            }
            @function double($n) { @return $n * 2; }
            @keyframes spin {
              from { transform: rotate(0); }
              to { transform: rotate(360deg); }
            }
            .e { @include center(1px); }
            """
        )
        result = parse(source)
        self.assertEqual(
            [(f.name, f.line_number, f.end_line) for f in result.functions],
            [("center", 1, 3), ("double", 4, 4)],
        )
        self.assertEqual([p.name for p in result.functions[0].parameters], ["$w"])
        self.assertEqual(symbols(result), [
            ("@keyframes spin", "at-rule", 5, 8),
            (".e", "rule", 9, 9),
        ])

    def test_imports_custom_properties_variables_and_class_names(self):
        source = textwrap.dedent(
            """\
            @use "sass:math";
            @use "variables" as v;
            @import url("./reset.css") screen;
            @import 'https://fonts.example.com/inter.css';
            $gap: 4px;
            :root { --brand: #fff; }
            .btn-primary, #app .x { color: var(--brand); }
            """
        )
        result = parse(source)
        self.assertEqual([(i.module, i.is_internal) for i in result.imports], [
            ("sass:math", False),
            ("./variables", True),
            ("./reset.css", True),
            ("https://fonts.example.com/inter.css", False),
        ])
        self.assertEqual(result.constants, ["$gap", "--brand"])
        self.assertEqual(result.exported_symbols, ["btn-primary", "app", "x"])
        self.assertEqual(get_adapter("css").count_imports(source), 4)
        # A top-level variable is a symbol, so editing its value is a change.
        self.assertIn(("$gap", "variable", 5, 5), symbols(result))

    def test_every_class_and_id_of_a_compound_is_exported(self):
        source = textwrap.dedent(
            """\
            .btn.active { color: red; }
            div.foo { x: y; }
            a#main { x: y; }
            .card { &.is-open { x: y; } }
            html.dark #root > div { x: y; }
            """
        )
        self.assertEqual(
            parse(source, "s.scss").exported_symbols,
            ["btn", "active", "foo", "main", "card", "is-open", "dark", "root"],
        )

    def test_escaped_class_names_are_exported_decoded(self):
        source = "\n".join([
            r".md\:hover\:bg-red-500:hover { x: y; }",
            r".-mt-\[3px\] { x: y; }",
            r".\32xl\:p-4 { x: y; }",
            r".\!mt-0 { x: y; }",
            r".\[mask-type\:luminance\] { x: y; }",
        ]) + "\n"
        self.assertEqual(
            parse(source, "t.css").exported_symbols,
            ["md:hover:bg-red-500", "-mt-[3px]", "2xl:p-4", "!mt-0", "[mask-type:luminance]"],
        )

    def test_interpolated_names_and_guards_export_nothing_invented(self):
        scss = "@each $k in a, b {\n  .icon-#{$k} { x: y; }\n}\n@for $i from 1 through 3 { .m-#{$i} { x: y; } }\n"
        self.assertEqual(parse(scss, "s.scss").exported_symbols, [])
        less = ".col-@{i} { x: y; }\n.guard when (@mode = #fff) { x: y; }\n"
        result = parse(less, "s.less")
        self.assertEqual(result.exported_symbols, ["guard"])
        self.assertEqual(names(result), [".col-@{i}", ".guard"])

    def test_an_ampersand_inside_a_string_is_text(self):
        source = '.a {\n  [title="R&D"] { x: y; }\n  &[data-x="&"] { x: y; }\n}\n'
        self.assertEqual(names(parse(source, "s.scss")), [".a", '.a [title="R&D"]', '.a[data-x="&"]'])

    def test_interpolated_parent_and_at_root_queries_resolve_as_sass_does(self):
        self.assertEqual(names(parse(".card {\n  #{&}__elem { x: y; }\n}\n", "s.scss")), [".card", ".card .card__elem"])
        source = ".a {\n  @media (x) {\n    @at-root (without: media) {\n      .b { top: 0; }\n    }\n  }\n}\n"
        self.assertEqual(names(parse(source, "s.scss")), [".a", ".a .b"])

    def test_sass_nested_properties_become_declarations_of_the_rule(self):
        source = ".info {\n  margin: auto {\n    bottom: 10px;\n  }\n}\n.panel {\n  overflow: {\n    y: auto;\n  }\n}\n"
        self.assertEqual(names(parse(source, "s.scss")), [".info", ".panel"])
        self.assertEqual(styled(source, "s.scss"), [
            ([".info"], [("margin", "auto"), ("margin-bottom", "10px")]),
            ([".panel"], [("overflow-y", "auto")]),
        ])

    def test_less_variables_mixins_and_imports(self):
        source = textwrap.dedent(
            """\
            @import (reference) "base.less";
            @primary: #333;
            .bordered(@width) { border: @width solid @primary; }
            .box { .bordered(2px); }
            """
        )
        result = parse(source, "theme.less")
        self.assertEqual([(i.module, i.is_internal) for i in result.imports], [("./base.less", True)])
        self.assertEqual(result.constants, ["@primary"])
        self.assertEqual([f.name for f in result.functions], [".bordered"])
        self.assertEqual(symbols(result), [
            ("@primary", "variable", 2, 2),
            (".box", "rule", 4, 4),
        ])

    def test_a_guarded_less_mixin_keeps_its_parameters_apart_from_the_guard(self):
        result = parse(".m(@a) when (iscolor(@a)) { color: @a; }\n", "s.less")
        self.assertEqual([(f.name, [p.name for p in f.parameters]) for f in result.functions], [(".m", ["@a"])])

    def test_less_detached_rulesets_are_variables_that_style_nothing_where_defined(self):
        source = "@detached: {\n  background: red;\n  .inner { position: fixed; }\n};\n.top {\n  @detached();\n}\n"
        result = parse(source, "s.less")
        self.assertEqual(symbols(result), [("@detached", "variable", 1, 4), (".top", "rule", 5, 7)])
        self.assertEqual(result.constants, ["@detached"])
        self.assertEqual(styled(source, "s.less"), [([".top"], [])])
        self.assertEqual(styled(".top {\n  @r: { position: fixed; };\n  @r();\n}\n", "s.less"), [([".top"], [])])

    def test_a_custom_property_may_hold_a_block(self):
        result = parse(":root {\n  --x: {a: b};\n  --y: ;\n  --z:{};\n}\n", "s.css")
        self.assertEqual(result.constants, ["--x", "--y", "--z"])
        self.assertEqual(symbols(result), [(":root", "rule", 1, 5)])

    def test_layers_register_their_parents_and_anonymous_layers_stay_distinct(self):
        from languages.stylesheet import parse_sheet

        source = "@layer a.b, c;\n@layer c { .x { top: 0; } }\n@layer a { .y { top: 0; } }\n"
        self.assertEqual(parse_sheet(source, "css").layers, ["a", "a.b", "c"])
        minified = "@layer{#root>div{position:relative}}@layer{.modal{position:fixed}}"
        self.assertEqual(len(parse_sheet(minified, "css").layers), 2)

    def test_tailwind_is_detected_and_its_import_is_a_package(self):
        from languages.stylesheet import parse_sheet

        v4 = parse_sheet('@import "tailwindcss";\n@import "./theme.css";\n', "css")
        self.assertEqual(v4.tailwind, "v4")
        self.assertEqual([(i.module, i.is_internal) for i in v4.imports], [("tailwindcss", False), ("./theme.css", True)])
        self.assertEqual(parse_sheet("@tailwind base;\n@tailwind utilities;\n", "css").tailwind, "v3")
        self.assertIsNone(parse_sheet(".a { color: red; }\n", "css").tailwind)

    def test_at_root_still_resolves_the_parent_reference(self):
        source = ".card {\n  @at-root {\n    &__title { position: fixed; }\n  }\n  @at-root #{&}__body { top: 0; }\n  @at-root &__foot { top: 0; }\n  @at-root .plain { top: 0; }\n}\n"
        result = parse(source, "s.scss")
        self.assertEqual(names(result), [".card", ".card__title", ".card__body", ".card__foot", ".plain"])
        self.assertEqual(result.exported_symbols, ["card", "card__title", "card__body", "card__foot", "plain"])

    def test_at_root_queries_decide_the_layer_too(self):
        from languages.stylesheet import iter_styled_blocks, parse_sheet

        source = "@layer base {\n  .x {\n    @at-root (without: all) {\n      .a { top: 0; }\n    }\n    @at-root {\n      .b { top: 0; }\n    }\n  }\n}\n"
        layers = {tuple(node.selectors): node.layer for node in iter_styled_blocks(parse_sheet(source, "scss"))}
        self.assertEqual((layers[(".a",)], layers[(".b",)], layers[(".x",)]), (None, "base", "base"))

    def test_bracketed_lists_and_custom_properties_keep_their_comments_straight(self):
        rule = ".dark #root > div:first-child {\n  position: relative;\n}\n"
        self.assertEqual(names(parse("$bp: [sm, // phones (portrait\n md];\n" + rule, "t.scss")), ["$bp", ".dark #root > div:first-child"])
        one_line = ":root { --cdn: //cdn.example.com; } .dark #root > div { position: relative; }\n"
        self.assertEqual(names(parse(one_line, "t.scss")), [":root", ".dark #root > div"])
        self.assertEqual(parse(":root {\n  --cdn: //cdn.example.com;\n  --brand: red;\n}\n", "t.scss").constants, ["--cdn", "--brand"])

    def test_a_custom_property_block_may_follow_other_tokens_and_hold_comments(self):
        first = parse(":root {\n  --x: foo { a: b };\n}\n.b { top: 0 }\n", "a.css")
        self.assertEqual((first.constants, names(first)), (["--x"], [":root", ".b"]))
        second = parse(":root {\n  --x: { /* } */ a: b };\n  --y: 1;\n}\n.b { top: 0 }\n", "a.css")
        self.assertEqual((second.constants, symbols(second)), (["--x", "--y"], [(":root", "rule", 1, 4), (".b", "rule", 5, 5)]))

    def test_plain_css_drops_declarations_and_media_blocks_containing_double_slash(self):
        from languages.stylesheet import iter_styled_blocks, parse_sheet

        source = "#root > div {\n  position: relative // was fixed\n}\n@media // x (min-width: 1px) {\n  #root > nav { overflow: hidden; }\n}\n.ok { background: url(//cdn/a.png); }\n"
        self.assertEqual(
            [(node.selectors, [(d.property, d.value) for d in node.declarations]) for node in iter_styled_blocks(parse_sheet(source, "css"))],
            [(["#root > div"], []), ([".ok"], [("background", "url(//cdn/a.png)")])],
        )

    def test_a_suffix_never_collides_with_a_real_name(self):
        source = "@include columns {\n  .x { top: 0 }\n}\n@include columns {\n  .y { top: 0 }\n}\n.z { top: 0 }\n@include columns (2) {\n  .w { top: 0 }\n}\n"
        top = [name for name, kind, _, _ in symbols(parse(source, "g.scss")) if kind == "at-rule"]
        self.assertEqual(top, ["@include columns", "@include columns (3)", "@include columns (2)"])

    def test_class_names_may_start_with_two_hyphens_or_a_non_ascii_letter(self):
        source = ".--modifier { top: 0 }\n.card { &.--active { top: 0 } }\n.caf\u00e9 { top: 0 }\n.\u65e5\u672c { top: 0 }\n"
        self.assertEqual(parse(source, "e.scss").exported_symbols, ["--modifier", "card", "--active", "caf\u00e9", "\u65e5\u672c"])
        self.assertEqual(parse(".\\D800 x { top: 0 }\n", "e.css").exported_symbols, ["\ufffdx"])

    def test_import_layers_declare_their_order(self):
        from languages.stylesheet import parse_sheet

        sheet = parse_sheet('@import "reset.css" layer(base);\n@import url(theme.css) layer;\n@layer components { .a { top: 0 } }\n@layer base { .b { top: 0 } }\n', "css")
        self.assertEqual(sheet.layers, ["base", "(anonymous layer 1)", "components"])
        self.assertFalse(sheet.imports_before_layers)

    def test_counting_and_comments_follow_the_dialect_of_the_path(self):
        adapter = get_adapter("css")
        source = ".a { color: red; }\n// .legacy { position: fixed; }\n.b { top: 0; }\n"
        self.assertEqual((adapter.extract_comments(source, "a.css"), adapter.strip_comments_and_blanks(source, "a.css")), ([], 3))
        self.assertEqual((len(adapter.extract_comments(source, "a.scss")), adapter.strip_comments_and_blanks(source, "a.scss")), (1, 2))

    def test_comments_and_code_lines(self):
        adapter = get_adapter("css")
        comments = adapter.extract_comments(THEME_CSS + ".x { color: red; } // trailing\n", "theme.scss")
        self.assertEqual(
            [(c.line_number, c.text, c.is_block, c.is_inline) for c in comments],
            [(1, "Ambient glow for the dark theme.", True, False), (9, "trailing", False, True)],
        )
        self.assertEqual(adapter.strip_comments_and_blanks(THEME_CSS), 6)


class TailwindApplyTests(unittest.TestCase):
    """`@apply` inlines a utility's declarations into the rule, at the rule's specificity."""

    def declarations(self, source):
        from languages.stylesheet import iter_styled_blocks, parse_sheet

        return [
            (d.property, d.value, d.important, d.line, d.condition)
            for node in iter_styled_blocks(parse_sheet(source, "css"))
            for d in node.declarations
        ]

    def test_layout_utilities_become_declarations(self):
        source = ".m {\n  @apply fixed inset-0 z-50 bg-background flex flex-col overflow-y-auto h-[100dvh] !overflow-hidden;\n}\n"
        self.assertEqual(self.declarations(source), [
            ("position", "fixed", False, 2, ""),
            ("inset", "0", False, 2, ""),
            ("display", "flex", False, 2, ""),
            ("overflow-y", "auto", False, 2, ""),
            ("height", "100dvh", False, 2, ""),
            ("overflow", "hidden", True, 2, ""),
        ])

    def test_variants_trailing_important_transforms_and_filters(self):
        source = ".x {\n  @apply dark:relative md:hidden fixed! -translate-x-1/2 transform-none backdrop-blur-sm;\n}\n"
        self.assertEqual(self.declarations(source), [
            ("position", "relative", False, 2, "dark"),
            ("display", "none", False, 2, "md"),
            ("position", "fixed", True, 2, ""),
            ("transform", "-translate-x-1/2", False, 2, ""),
            ("transform", "none", False, 2, ""),
            ("backdrop-filter", "backdrop-blur-sm", False, 2, ""),
        ])

    def test_utilities_that_set_nothing_the_scan_reads_are_not_invented(self):
        source = ".x {\n  @apply translate-none rotate-none scale-none perspective-origin-center inset-shadow-sm inset-ring-2 h-(--modal-h) will-change-[transform] contain-[paint];\n}\n"
        self.assertEqual(self.declarations(source), [
            ("translate", "none", False, 2, ""),
            ("rotate", "none", False, 2, ""),
            ("scale", "none", False, 2, ""),
            ("height", "var(--modal-h)", False, 2, ""),
            ("will-change", "transform", False, 2, ""),
            ("contain", "paint", False, 2, ""),
        ])

    def test_the_declaration_names_the_utility_it_came_from(self):
        from languages.stylesheet import iter_styled_blocks, parse_sheet

        node = next(iter_styled_blocks(parse_sheet(".m { @apply fixed; }\n", "css")))
        self.assertEqual(node.declarations[0].origin, "@apply fixed")


class StylesheetSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.src = scratch(self, "xray-css-snapshot-") / "src"
        write(self.src, "styles/theme.css", THEME_CSS)
        write(self.src, "styles/_variables.scss", "$gap: 4px;\n")
        write(self.src, "styles/main.scss", '@use "variables";\n.page { margin: $gap; }\n')
        write(self.src, "styles/dup.css", ".dup {\n  color: red;\n}\n.middle {\n  color: green;\n}\n.dup {\n  margin: 0;\n}\n")
        import snapshot

        self.snapshot = snapshot
        self.manifest = snapshot.build_manifest(self.src)

    def key(self, suffix):
        return next(k for k in self.manifest["files"] if k.endswith(suffix))

    def changes(self):
        files = self.snapshot.compare_files(self.manifest, self.src)
        found = self.snapshot.compare_symbols(self.manifest, files)
        index = self.snapshot.build_import_index(self.manifest, files, found)
        return found, self.snapshot.blast_radius(index, files, found)

    def test_every_rule_is_a_manifest_symbol(self):
        entry = self.manifest["files"][self.key("styles/theme.css")]
        self.assertEqual(entry["language"], "css")
        rule = entry["symbols"][".dark #root > div:first-child"]
        self.assertEqual((rule["kind"], rule["start"], rule["end"]), ("rule", 6, 8))

    def test_editing_one_rule_changes_only_that_rule(self):
        (self.src / "styles/theme.css").write_text(
            THEME_CSS.replace(
                ".dark #root > div:first-child {\n  position: relative;",
                ".dark #root > div:first-child {\n  position: static;",
            ),
            encoding="utf-8",
        )
        found, _ = self.changes()
        self.assertEqual([item["symbol"] for item in found["changed"]], [".dark #root > div:first-child"])

    def test_editing_a_rule_between_two_repeats_changes_only_that_rule(self):
        path = self.src / "styles/dup.css"
        path.write_text(path.read_text(encoding="utf-8").replace("green", "lime"), encoding="utf-8")
        found, _ = self.changes()
        self.assertEqual([item["symbol"] for item in found["changed"]], [".middle"])

    def test_a_sass_partial_puts_its_importer_in_the_radius(self):
        (self.src / "styles/_variables.scss").write_text("$gap: 8px;\n", encoding="utf-8")
        _, importers = self.changes()
        self.assertTrue(
            any(entry["file"].endswith("styles/main.scss") for entry in importers), importers
        )

    def test_a_multi_line_variable_spans_to_its_semicolon(self):
        (self.src / "styles/_variables.scss").write_text("$gap: (\n  sm: 4px,\n  md: 8px,\n);\n", encoding="utf-8")
        self.manifest = self.snapshot.build_manifest(self.src)
        entry = self.manifest["files"][self.key("styles/_variables.scss")]
        self.assertEqual((entry["symbols"]["$gap"]["start"], entry["symbols"]["$gap"]["end"]), (1, 4))
        (self.src / "styles/_variables.scss").write_text("$gap: (\n  sm: 4px,\n  md: 12px,\n);\n", encoding="utf-8")
        found, importers = self.changes()
        self.assertEqual([item["symbol"] for item in found["changed"]], ["$gap"])
        self.assertTrue(any(entry["file"].endswith("styles/main.scss") for entry in importers), importers)

    def test_a_minified_stylesheet_is_a_file_level_entry(self):
        rules = "".join(f".c{i}{{color:#{i:06x};margin:{i % 9}px}}" for i in range(1500))
        write(self.src, "public/app.min.css", rules)
        manifest = self.snapshot.build_manifest(self.src)
        entry = next(v for k, v in manifest["files"].items() if k.endswith("public/app.min.css"))
        self.assertEqual((entry["language"], entry["symbols"]), ("css", {}))

    def test_a_stylesheet_import_prefers_its_own_partial_and_its_dialect(self):
        known = self.snapshot._by_basename([
            "styles/index.scss", "styles/_tokens.scss", "themes/kit/styles/tokens.scss",
            "styles/main.scss", "styles/x.css", "styles/_x.scss",
            "less/site.less", "less/vars.less", "less/vars.scss",
            "plain/site.css", "plain/theme.css", "plain/theme.scss",
        ])
        resolve = self.snapshot.resolve_module
        self.assertEqual(resolve("./tokens", "styles/index.scss", known), "styles/_tokens.scss")
        self.assertEqual(resolve("./x", "styles/main.scss", known), "styles/_x.scss")
        self.assertEqual(resolve("./vars", "less/site.less", known), "less/vars.less")
        self.assertEqual(resolve("./theme", "plain/site.css", known), "plain/theme.css")

    def test_stylesheet_resolution_is_only_for_stylesheet_importers(self):
        known = self.snapshot._by_basename([
            "src/App.tsx", "src/theme/index.ts", "src/theme.css", "src/_variables.scss",
            "app/__init__.py", "app/static/app.css", "tests/test_app.py",
            "styles/main.scss", "styles/_variables.scss",
        ])
        resolve = self.snapshot.resolve_module
        self.assertEqual(resolve("./theme", "src/App.tsx", known), "src/theme/index.ts")
        self.assertIsNone(resolve("./variables", "src/App.tsx", known))
        self.assertEqual(resolve("app", "tests/test_app.py", known), "app/__init__.py")
        self.assertEqual(resolve("./variables", "styles/main.scss", known), "styles/_variables.scss")


class StylesheetIncrementalRunTests(unittest.TestCase):
    """The diff, carry and check subcommands, run as the workflow runs them."""

    def setUp(self):
        tmp = scratch(self, "xray-css-run-")
        self.tree, self.parent, self.run = tmp / "tree", tmp / "parent", tmp / "run"
        (self.parent / "snapshot").mkdir(parents=True)
        write(self.parent, "state.json", '{"status": "complete"}')

    def snapshot_parent(self):
        code, out = xray("write", self.tree, "--out", self.parent / "snapshot" / "manifest.json")
        self.assertEqual(code, 0, out)

    def test_the_publication_gate_accepts_a_quoted_stylesheet_citation(self):
        write(self.tree, "theme.css", ".a {\n  color: red;\n}\n")
        self.snapshot_parent()
        write(self.tree, "theme.css", ".a {\n  color: red;\n}\n.center {\n  margin: 0;\n}\n@media (max-width: 600px) {\n  .card { margin: 0; }\n}\n")
        self.assertEqual(xray("diff", self.parent, self.tree, "--out", self.run)[0], 0)
        self.assertEqual(xray("carry", self.parent, self.run)[0], 0)
        code, out = xray("check", self.run)
        self.assertNotEqual(code, 0, out)
        write(self.run, "01-structure.md", (
            "# Structure\n\n"
            "- `theme.css::.center` centers content at theme.css:4.\n"
            "- `theme.css::@media (max-width: 600px)` holds `theme.css::@media (max-width: 600px) { .card }` at theme.css:7.\n"
        ))
        code, out = xray("check", self.run)
        self.assertEqual(code, 0, out)

    def test_a_quoted_citation_of_a_changed_rule_is_marked_stale(self):
        write(self.tree, "theme.css", ".dark #root > div:first-child {\n  position: relative;\n}\n.modal {\n  position: fixed;\n}\n")
        write(self.tree, "util.py", "def helper():\n    return 1\n")
        write(self.parent, "03-flows.md", (
            "# Flows\n\n"
            "- Root override: `theme.css::.dark #root > div:first-child`.\n"
            "- The modal is fixed: `theme.css::.modal`.\n"
            "- Helper: `util.py::helper`.\n"
        ))
        self.snapshot_parent()
        write(self.tree, "theme.css", ".dark #root > div:first-child {\n  position: static;\n}\n.modal {\n  position: absolute;\n}\n")
        self.assertEqual(xray("diff", self.parent, self.tree, "--out", self.run)[0], 0)
        claims = json.loads((self.run / "changes.json").read_text(encoding="utf-8"))["claims"]
        self.assertEqual({(c["line"], c["reason"]) for c in claims}, {(3, "symbol-changed"), (4, "symbol-changed")})

    def test_a_quoted_selector_is_not_also_cited_by_its_leading_word(self):
        import snapshot

        self.assertEqual(
            snapshot.cited_symbols("See `theme.css::body > div` and `svc.py::Service.run`."),
            [("svc.py", "Service.run"), ("theme.css", "body > div")],
        )
        write(self.tree, "theme.css", "body > div {\n  position: relative;\n}\n")
        self.snapshot_parent()
        write(self.tree, "theme.css", "body > div {\n  position: relative;\n}\nbody {\n  overflow: hidden;\n}\n")
        self.assertEqual(xray("diff", self.parent, self.tree, "--out", self.run)[0], 0)
        self.assertEqual(xray("carry", self.parent, self.run)[0], 0)
        write(self.run, "02-interfaces.md", "# Interfaces\n\n- `theme.css::body > div` at theme.css:1.\n")
        code, out = xray("check", self.run)
        self.assertNotEqual(code, 0, out)
        self.assertIn("theme.css::body", out)

    def test_a_symbol_citation_into_a_file_level_stylesheet_falls_back_to_the_file(self):
        rules = "".join(f".m{i}{{color:red}}" for i in range(2000))
        write(self.tree, "public/app.min.css", rules)
        write(self.parent, "01-structure.md", "# S\n\n- Symbol only: `app.min.css::.m5` in `public/app.min.css`.\n")
        self.snapshot_parent()
        write(self.tree, "public/app.min.css", rules.replace(".m5{color:red}", ".m5{position:fixed}"))
        self.assertEqual(xray("diff", self.parent, self.tree, "--out", self.run)[0], 0)
        claims = json.loads((self.run / "changes.json").read_text(encoding="utf-8"))["claims"]
        self.assertEqual([(c["line"], c["reason"]) for c in claims], [(3, "file-modified")])

    def test_a_pipe_in_a_symbol_does_not_break_the_changes_table(self):
        write(self.tree, "a.css", 'svg|rect, [lang|="en"] {\n  fill: red;\n}\n')
        self.snapshot_parent()
        write(self.tree, "a.css", 'svg|rect, [lang|="en"] {\n  fill: blue;\n}\n')
        self.assertEqual(xray("diff", self.parent, self.tree, "--out", self.run)[0], 0)
        table = (self.run / "changes.md").read_text(encoding="utf-8")
        self.assertIn(r"svg\|rect", table)
        self.assertNotIn("`svg|rect", table)


class SpecificityTests(unittest.TestCase):
    def test_selectors_score_as_the_cascade_scores_them(self):
        import cascade_scan

        cases = {
            "*": (0, 0, 0),
            "div": (0, 0, 1),
            ".a": (0, 1, 0),
            "#a": (1, 0, 0),
            ".dark #root > div:first-child": (1, 2, 1),
            "a:hover::before": (0, 1, 2),
            "a:before": (0, 0, 2),
            ":where(#a) .b": (0, 1, 0),
            ":is(#a, .b) c": (1, 0, 1),
            ":not(.a, #b)": (1, 0, 0),
            "li:nth-child(2n+1 of .x)": (0, 2, 1),
            '[type="text"]': (0, 1, 0),
            "html body": (0, 0, 2),
            ":root": (0, 1, 0),
            r"#\31 23": (1, 0, 0),
            r".\32 xl\:fixed": (0, 1, 0),
        }
        for selector, expected in cases.items():
            with self.subTest(selector=selector):
                self.assertEqual(cascade_scan.specificity(selector), expected)

    def test_a_hex_escape_consumes_its_terminating_space(self):
        import cascade_scan

        self.assertEqual(cascade_scan.compounds(r"#\31 23"), [("", r"#\31 23")])


class ReachTests(unittest.TestCase):
    def reach(self, selector):
        import cascade_scan

        return cascade_scan.reach(selector)

    def test_the_relation_to_the_root_is_named(self):
        cases = {
            "#root > div": ("descendant", "children"),
            "#root > div > div": ("descendant", "descendants"),
            "#root div": ("descendant", "descendants"),
            "#root + div": ("sibling", "siblings"),
            "body": ("root", "self"),
            "*": ("universal", "all"),
        }
        for selector, expected in cases.items():
            with self.subTest(selector=selector):
                found = self.reach(selector)
                self.assertEqual((found["reach"], found["relation"]), expected)

    def test_an_anchor_wrapped_in_is_or_where_still_anchors(self):
        self.assertEqual(self.reach(":is(html, body)")["reach"], "root")
        found = self.reach(":where(#root) > div:first-child")
        self.assertEqual((found["reach"], found["anchor"]), ("descendant", ":where(#root)"))


class CascadeScanTests(unittest.TestCase):
    def setUp(self):
        self.src = scratch(self, "xray-cascade-") / "src"
        import cascade_scan

        self.cascade = cascade_scan

    def report(self, files, sub=""):
        root = self.src / sub if sub else self.src
        for rel, content in files.items():
            write(root, rel, content)
        return self.cascade.scan(root)

    def conflicts(self, report):
        return {
            candidate["selector"]: [(c["selector"], c["decided_by"]) for c in candidate["conflicts"]]
            for candidate in report["candidates"]
        }

    def test_the_phazly_rule_is_found_with_the_modal_rule_it_overrides(self):
        report = self.report({"styles/theme.css": THEME_CSS, "styles/modal.css": MODAL_CSS})
        self.assertEqual(len(report["candidates"]), 1, report["candidates"])
        found = report["candidates"][0]
        self.assertEqual((found["file"], found["line"]), ("styles/theme.css", 6))
        self.assertEqual(found["selector"], ".dark #root > div:first-child")
        self.assertEqual((found["reach"], found["anchor"]), ("descendant", "#root"))
        self.assertEqual(found["scope"], [".dark"])
        self.assertEqual(found["specificity"], [1, 2, 1])
        self.assertEqual(
            [(d["property"], d["value"], d["line"]) for d in found["declarations"]],
            [("position", "relative", 7)],
        )
        self.assertEqual(
            [
                (c["file"], c["line"], c["selector"], c["property"], c["value"], c["relation"], c["decided_by"])
                for c in found["conflicts"]
            ],
            [("styles/modal.css", 2, ".terms-acceptance-modal", "position", "fixed", "overrides", "specificity")],
        )

    def test_the_real_incident_shape_with_tailwind_apply(self):
        report = self.report({
            "styles/components/dark-ambient-glow.css": ".dark #root > div:first-child {\n  position: relative;\n}\n",
            "styles/legal/terms-acceptance-modal.css": (
                ".terms-acceptance-modal {\n  @apply fixed inset-0 z-50 bg-background flex flex-col;\n}\n"
            ),
        })
        found = report["candidates"][0]
        self.assertEqual(
            [(c["file"], c["line"], c["selector"], c["property"], c["value"], c["decided_by"]) for c in found["conflicts"]],
            [("styles/legal/terms-acceptance-modal.css", 2, ".terms-acceptance-modal", "position", "fixed", "specificity")],
        )

    def test_a_targeted_descendant_is_not_a_candidate(self):
        report = self.report({
            "a.css": "#root > .app-shell { position: relative; }\nbody .modal { overflow: hidden; }\n",
        })
        self.assertEqual(report["candidates"], [])

    def test_candidates_below_the_root_come_before_the_root_itself(self):
        report = self.report({"a.css": "body { overflow: hidden; }\n* { position: relative; }\n"})
        self.assertEqual(
            [(c["selector"], c["reach"]) for c in report["candidates"]],
            [("*", "universal"), ("body", "root")],
        )

    def test_rules_that_set_no_layout_or_are_never_applied_are_not_candidates(self):
        report = self.report({
            "a.scss": textwrap.dedent(
                """\
                #root > div { color: red; }
                body > div { transform: none; }
                @mixin lock { body { overflow: hidden; } }
                @keyframes fade { from { opacity: 0; } }
                """
            ),
        })
        self.assertEqual(report["candidates"], [])

    def test_the_at_rule_context_is_reported(self):
        report = self.report({"a.css": "@media (max-width: 600px) {\n  #app > div { overflow: hidden; }\n}\n"})
        found = report["candidates"][0]
        self.assertEqual((found["line"], found["context"]), (2, ["@media (max-width: 600px)"]))

    def test_a_containing_block_for_fixed_descendants_names_the_fixed_rules(self):
        report = self.report({"a.css": "#app > div { transform: translateZ(0); }\n", "modal.css": MODAL_CSS})
        found = report["candidates"][0]
        self.assertEqual(found["declarations"][0]["group"], "containing-block")
        self.assertEqual(
            [(c["selector"], c["property"], c["value"], c["relation"]) for c in found["conflicts"]],
            [(".terms-acceptance-modal", "position", "fixed", "containing-block")],
        )

    def test_modern_containing_block_triggers_and_their_exceptions(self):
        report = self.report({"a.css": textwrap.dedent(
            """\
            #root > div { translate: 10px 0; }
            body > main { content-visibility: auto; }
            #app > section { will-change: translate; }
            #app > aside { transform-style: preserve-3d; }
            #root > nav { container-type: inline-size; }
            html.dark { filter: invert(1); }
            body.blurred { filter: blur(2px); }
            .modal { position: fixed; }
            """
        )})
        by_selector = {c["selector"]: c for c in report["candidates"]}
        self.assertEqual(
            set(by_selector),
            {"#root > div", "body > main", "#app > section", "#app > aside", "body.blurred"},
        )
        for candidate in by_selector.values():
            self.assertEqual(
                [(c["selector"], c["relation"]) for c in candidate["conflicts"]],
                [(".modal", "containing-block")],
            )

    def test_a_pseudo_element_is_never_overridden_but_is_still_re_anchored(self):
        report = self.report({"a.css": textwrap.dedent(
            """\
            #root > div:first-child { position: relative; }
            .glow::before { content: ''; position: absolute; }
            .tip:after { position: absolute; }
            #app > main { transform: translateZ(0); }
            .float::after { position: fixed; }
            """
        )})
        self.assertEqual(self.conflicts(report), {
            "#root > div:first-child": [],
            "#app > main": [(".float::after", None)],
        })

    def test_selectors_that_cannot_share_an_element_are_not_conflicts(self):
        report = self.report({"a.css": textwrap.dedent(
            """\
            #root { height: 100%; }
            #modal { height: 50%; }
            body > div:first-child { position: relative; }
            section.sheet { position: fixed; }
            div.sheet { position: fixed; }
            body.modal-open { overflow: hidden; }
            .panel__body { overflow-y: auto; }
            """
        )})
        self.assertEqual(self.conflicts(report), {
            "body > div:first-child": [("div.sheet", "specificity")],
            "#root": [],
            "body.modal-open": [],
        })

    def test_cascade_layers_decide_before_specificity(self):
        cases = [
            ("layered-candidate", {"a.css": "@layer base {\n  #root > div:first-child { position: relative; }\n}\n.modal { position: fixed; }\n"}, []),
            ("layered-other", {"a.css": "#root > div:first-child { position: relative; }\n@layer components {\n  #modal#modal { position: fixed; }\n}\n"}, [("#modal#modal", "layer")]),
            ("important-reverses", {"a.css": "@layer base {\n  #root > div { position: relative !important; }\n}\n.modal { position: fixed !important; }\n"}, [(".modal", "layer")]),
            ("declared-order", {"a.css": "@layer base, components;\n@layer components {\n  #root > div { position: relative; }\n}\n@layer base {\n  .modal { position: fixed; }\n}\n"}, [(".modal", "layer")]),
            ("across-files", {"x.css": "@layer components {\n  #root > div { position: relative; }\n}\n", "y.css": "@layer base {\n  .modal { position: fixed; }\n}\n"}, [(".modal", "layer-order-unknown")]),
        ]
        for sub, files, expected in cases:
            with self.subTest(case=sub):
                report = self.report(files, sub)
                self.assertEqual(len(report["candidates"]), 1, report["candidates"])
                self.assertEqual(list(self.conflicts(report).values())[0], expected)

    def test_important_and_source_order_decide_as_the_cascade_does(self):
        report = self.report({
            "a.css": textwrap.dedent(
                """\
                body > div { position: relative; }
                body > span { position: relative !important; }
                body > :first-child { position: absolute; }
                """
            ),
            "b.css": ".m { position: fixed; }\nsection .n { position: sticky; }\n",
        })
        by_selector = {c["selector"]: c for c in report["candidates"]}
        # (0,0,2) loses to (0,1,0) and (0,1,1): it overrides nothing.
        self.assertEqual(by_selector["body > div"]["conflicts"], [])
        # !important wins over any specificity without it.
        self.assertEqual(
            {(c["selector"], c["decided_by"]) for c in by_selector["body > span"]["conflicts"]},
            {(".m", "important"), ("section .n", "important")},
        )
        # (0,1,1) beats (0,1,0) and ties (0,1,1) in another file, where load order decides.
        self.assertEqual(
            {(c["selector"], c["decided_by"]) for c in by_selector["body > :first-child"]["conflicts"]},
            {(".m", "specificity"), ("section .n", "source-order-unknown")},
        )

    def test_source_order_decides_a_tie_only_for_the_later_rule_in_one_file(self):
        report = self.report({"a.css": textwrap.dedent(
            """\
            body > div:first-child { position: relative; }
            section div.first { position: fixed; }
            section div.late { position: sticky; }
            body > div:last-child { position: relative; }
            """
        )})
        self.assertEqual(self.conflicts(report), {
            "body > div:first-child": [],
            "body > div:last-child": [("section div.first", "source-order"), ("section div.late", "source-order")],
        })

    def test_native_css_nesting_is_scored_as_is_and_sass_as_substitution(self):
        source = "body, #app {\n  & > div { position: relative; }\n}\n.portal-modal.open { position: fixed; }\n"
        css = self.report({"a.css": source}, "css")
        self.assertEqual(
            [(c["selector"], c["specificity"], [x["selector"] for x in c["conflicts"]]) for c in css["candidates"]],
            [(":is(body, #app) > div", [1, 0, 1], [".portal-modal.open"])],
        )
        scss = self.report({"a.scss": source}, "scss")
        self.assertEqual(
            [(c["selector"], [x["selector"] for x in c["conflicts"]]) for c in scss["candidates"]],
            [("body > div", []), ("#app > div", [".portal-modal.open"])],
        )

    def test_rules_wrapped_in_is_or_where_are_targeted(self):
        report = self.report({"a.css": "#root > div { position: relative; }\n:is(.modal, .drawer) { position: fixed; }\n:where(.dialog) { position: fixed; }\n"})
        self.assertEqual(self.conflicts(report), {
            "#root > div": [(":is(.modal, .drawer)", "specificity"), (":where(.dialog)", "specificity")],
        })

    def test_only_the_winning_declaration_of_a_property_counts(self):
        report = self.report({"a.css": "#root > div { height: 100vh; height: 100dvh; }\n.sheet { height: 100vh; height: 100dvh; }\n.other { height: 50vh; }\n"})
        found = report["candidates"][0]
        self.assertEqual([(d["property"], d["value"]) for d in found["declarations"]], [("height", "100dvh")])
        self.assertEqual([(c["selector"], c["value"]) for c in found["conflicts"]], [(".other", "50vh")])

    def test_shorthand_and_longhand_values_are_compared_as_longhands(self):
        report = self.report({"a.css": textwrap.dedent(
            """\
            #root > div { overflow: hidden auto; }
            .list { overflow-y: auto; }
            .scroller { overflow-y: scroll; }
            #app > div { inset: 0 auto; }
            .modal { top: 0; }
            .drawer { left: 0; }
            #root > nav { overflow: hidden; overflow-y: hidden; }
            .menu { overflow-y: auto; }
            """
        )})
        by_selector = {c["selector"]: [x["selector"] for x in c["conflicts"]] for c in report["candidates"]}
        self.assertEqual(by_selector, {
            "#root > div": [".scroller"],
            "#app > div": [".drawer"],
            "#root > nav": [".list", ".scroller", ".menu"],
        })

    def test_double_slash_is_a_comment_in_sass_but_not_in_css(self):
        source = "#root > div {\n  // legacy\n  position: relative;\n}\n// note\n.modal { position: fixed; }\n"
        self.assertEqual(self.report({"a.css": source}, "css")["candidates"], [])
        scss = self.report({"a.scss": source}, "scss")
        self.assertEqual(self.conflicts(scss), {"#root > div": [(".modal", "specificity")]})

    def test_screen_level_rules_are_listed_first_and_marked(self):
        # On the real tree the incident rule could beat dozens of rules, nearly all
        # `position: absolute` decorations, and the consent modal sat in the middle.
        widgets = "".join(f".widget-{i} {{\n  @apply absolute;\n}}\n" for i in range(30))
        report = self.report({
            "styles/components/dark-ambient-glow.css": ".dark #root > div:first-child {\n  position: relative;\n}\n",
            "styles/common/widgets.css": widgets,
            "styles/legal/terms-acceptance-modal.css": (
                ".terms-acceptance-modal {\n  @apply fixed inset-0 flex flex-col;\n}\n"
                ".terms-acceptance-modal__body {\n  @apply flex-1 overflow-y-auto;\n}\n"
            ),
            "styles/common/picker.css": ".picker {\n  @apply before:absolute [&::-webkit-calendar-picker-indicator]:absolute;\n}\n",
        })
        found = report["candidates"][0]
        first = found["conflicts"][0]
        self.assertEqual((first["selector"], first["value"], first["screen_level"]), (".terms-acceptance-modal", "fixed", True))
        self.assertEqual(sum(1 for c in found["conflicts"] if c["screen_level"]), 1)
        self.assertEqual(len(found["conflicts"]), 31)
        self.assertNotIn(".picker", {c["selector"] for c in found["conflicts"]})
        markdown = self.cascade.format_markdown(report)
        self.assertLess(markdown.index(".terms-acceptance-modal"), markdown.index(".widget-0"))

    def test_a_root_candidate_says_its_overrides_were_not_compared(self):
        report = self.report({"a.css": "html.dark body { overflow: auto; }\n.modal-open { overflow: hidden; }\n"})
        markdown = self.cascade.format_markdown(report)
        self.assertIn("not compared", markdown)
        self.assertNotIn("No rule that could match the same element", markdown)

    def test_tailwind_declares_its_layer_order_before_the_file_does(self):
        v4 = self.report({"a.css": (
            '@import "tailwindcss";\n@layer utilities {\n  .modal-fixed { position: fixed; }\n}\n'
            "@layer base {\n  body > div { position: relative; }\n}\n"
        )}, "v4")
        self.assertEqual(self.conflicts(v4), {"body > div": []})
        v3 = self.report({"a.css": (
            "@tailwind base;\n@tailwind components;\n@tailwind utilities;\n"
            "body > div { position: relative; }\n@layer components {\n  .modal { position: fixed; }\n}\n"
        )}, "v3")
        self.assertEqual(self.conflicts(v3), {"body > div": []})
        imported = self.report({"a.css": (
            '@import "./layers.css";\n@layer components {\n  #root > div { position: relative; }\n}\n'
            "@layer base {\n  .modal { position: fixed; }\n}\n"
        )}, "imported")
        self.assertEqual(self.conflicts(imported), {"#root > div": [(".modal", "layer-order-unknown")]})

    def test_nested_dotted_and_anonymous_layers_order_as_the_cascade_does(self):
        cases = [
            ("direct-after-sub", {"a.css": "@layer a {\n  @layer b {\n    .modal { position: fixed; }\n  }\n  #root > div { position: relative; }\n}\n"},
             {"#root > div": [(".modal", "layer")]}),
            ("sub-before-direct", {"a.css": "@layer a {\n  .modal { position: fixed; }\n  @layer b {\n    #root > div { position: relative; }\n  }\n}\n"},
             {"#root > div": []}),
            ("dotted-declares-parent", {"a.css": "@layer a.b, c;\n@layer c {\n  .modal { position: fixed; }\n}\n@layer a {\n  #root > div { position: relative; }\n}\n"},
             {"#root > div": []}),
            ("anonymous-same-file", {"a.css": "@layer{#root>div{position:relative}}@layer{.modal{position:fixed}}"},
             {"#root > div": []}),
            ("anonymous-across-files", {"x.css": "@layer {\n  #root > div { position: relative; }\n}\n", "y.css": "@layer {\n  .modal { position: fixed; }\n}\n"},
             {"#root > div": [(".modal", "layer-order-unknown")]}),
        ]
        for sub, files, expected in cases:
            with self.subTest(case=sub):
                self.assertEqual(self.conflicts(self.report(files, sub)), expected)

    def test_pseudo_element_variants_style_nothing_on_either_side(self):
        report = self.report({"a.css": textwrap.dedent(
            """\
            #root > div:first-child { @apply before:absolute before:inset-0; }
            #root > nav { @apply before:rotate-45; }
            #root > main:first-child { position: relative; }
            .a { @apply details-content:absolute; }
            .b { @apply [&:before]:absolute; }
            .c { @apply before:absolute; }
            .modal { position: fixed; }
            """
        )})
        # The plain rule still meets the plain fixed rule; the pseudo-element variants meet nothing.
        self.assertEqual(self.conflicts(report), {"#root > main:first-child": [(".modal", "specificity")]})

    def test_a_shorthand_after_its_longhand_resets_it(self):
        report = self.report({"a.css": textwrap.dedent(
            """\
            #root > div { overflow-y: auto; overflow: hidden; }
            .list { overflow-y: hidden; }
            #root > nav { overflow-y: hidden; }
            .list2 { overflow-y: auto; overflow: hidden; }
            """
        )})
        self.assertEqual(self.conflicts(report), {"#root > div": [], "#root > nav": []})

    def test_functional_values_are_single_components(self):
        report = self.report({"a.css": textwrap.dedent(
            """\
            #app > div { inset: calc(50% - 10px); }
            .modal { top: calc(50% - 10px); }
            #root > div { inset: var(--x, 0px); }
            .sheet { top: var(--x, 0px); }
            """
        )})
        self.assertEqual(self.conflicts(report), {
            "#app > div": [(".sheet", "specificity")],
            "#root > div": [(".modal", "specificity")],
        })

    def test_viewport_heights_inside_calc_are_screen_level(self):
        report = self.report({"a.css": textwrap.dedent(
            """\
            #root > div { height: auto; }
            .page { height: calc(100dvh - 4rem); }
            .tw { @apply h-[calc(100dvh-4rem)]; }
            """
        )})
        found = report["candidates"][0]
        self.assertEqual([(c["selector"], c["screen_level"]) for c in found["conflicts"]], [(".page", True), (".tw", True)])

    def test_offsets_and_minimum_heights_are_candidate_properties(self):
        report = self.report({"a.css": textwrap.dedent(
            """\
            #root > div:first-child { top: 64px; }
            .modal { @apply fixed inset-0; }
            #root > main { min-height: 100vh; }
            .page { @apply min-h-dvh; }
            """
        )})
        self.assertEqual(self.conflicts(report), {
            "#root > div:first-child": [(".modal", "specificity")],
            "#root > main": [(".page", "specificity")],
        })

    def test_screen_level_tailwind_utilities_in_markup_are_conflicts(self):
        report = self.report({
            "src/index.css": '@import "tailwindcss";\n.dark #root > div:first-child {\n  position: relative;\n}\n',
            "src/OnboardingFlow.tsx": (
                "export function OnboardingFlow() {\n"
                '  return <div className="fixed inset-0 h-dvh overflow-hidden">x</div>;\n'
                "}\n"
            ),
            "src/Badge.tsx": 'export const Badge = () => <span className="absolute top-0">b</span>;\n',
            "src/Sheet.tsx": 'export const Sheet = () => <section className="fixed inset-0">s</section>;\n',
        }, "markup")
        found = report["candidates"][0]
        self.assertEqual(
            [
                (c["file"], c["line"], c["selector"], c["value"], c["relation"], c["decided_by"], c["screen_level"])
                for c in found["conflicts"]
            ],
            [("src/OnboardingFlow.tsx", 2, ".fixed", "fixed", "overrides", "layer", True)],
        )
        # Without Tailwind in the stylesheets, a `fixed` class in markup is not a utility the scan can read.
        plain = self.report({
            "src/index.css": ".dark #root > div:first-child {\n  position: relative;\n}\n",
            "src/OnboardingFlow.tsx": '<div className="fixed inset-0">x</div>\n',
        }, "plain")
        self.assertEqual(plain["candidates"][0]["conflicts"], [])

    def test_a_parent_list_with_one_root_anchor_still_reaches(self):
        report = self.report({"a.css": "body, #shell {\n  & > div { position: relative; }\n}\n", "m.css": ".modal.open { position: fixed; }\n"}, "mixed")
        self.assertEqual([c["selector"] for c in report["candidates"]], [":is(body, #shell) > div"])

    def test_an_import_layer_declares_its_place_in_the_order(self):
        report = self.report({"app.css": '@import "reset.css" layer(base);\n@layer components {\n  #root > div { position: relative; }\n}\n@layer base {\n  .modal { position: fixed; }\n}\n'}, "import-layer")
        self.assertEqual(self.conflicts(report), {"#root > div": [(".modal", "layer")]})

    def test_the_cli_prints_markdown_and_json(self):
        write(self.src, "styles/theme.css", THEME_CSS)
        write(self.src, "styles/modal.css", MODAL_CSS)
        script = str(SCRIPTS / "cascade_scan.py")
        markdown = subprocess.run([sys.executable, script, str(self.src)], capture_output=True, text=True)
        self.assertEqual(markdown.returncode, 0, markdown.stderr)
        self.assertIn("styles/theme.css:6", markdown.stdout)
        self.assertIn(".terms-acceptance-modal", markdown.stdout)
        as_json = subprocess.run(
            [sys.executable, script, str(self.src), "--json"], capture_output=True, text=True
        )
        self.assertEqual(as_json.returncode, 0, as_json.stderr)
        data = json.loads(as_json.stdout)
        self.assertEqual(data["candidates"][0]["selector"], ".dark #root > div:first-child")


class StylesheetScaleTests(unittest.TestCase):
    def test_many_custom_properties_and_one_line_comments_parse_in_linear_time(self):
        tokens = ":root{\n" + "".join(f"  --token-{i}: {i}px;\n" for i in range(40000)) + "}\n"
        comments = "".join(f"/*c{i}*/.a{i}{{x:y}}" for i in range(40000))
        for label, source in (("tokens", tokens), ("comments", comments)):
            with self.subTest(case=label):
                start = time.perf_counter()
                parse(source, "t.css")
                self.assertLess(time.perf_counter() - start, 8.0)

    def test_a_long_top_level_selector_list_parses_in_linear_time(self):
        source = ",\n".join(f".icon-{i}" for i in range(8000)) + " { display: inline-block; }\n"
        start = time.perf_counter()
        parse(source, "i.css")
        self.assertLess(time.perf_counter() - start, 5.0)

    def test_deep_nesting_does_not_exhaust_the_stack(self):
        source = "".join(f".l{i} {{\n" for i in range(1200)) + "x: y;\n" + "}\n" * 1200
        self.assertEqual(len(parse(source, "d.scss").classes), 1200)


class NeighbourScriptTests(unittest.TestCase):
    def test_a_hyphenated_class_name_is_a_valid_usage_symbol(self):
        import usage_finder

        self.assertEqual(usage_finder.validate_symbol("dark-ambient-glow"), "dark-ambient-glow")
        with self.assertRaises(ValueError):
            usage_finder.validate_symbol("-rf")

    def test_usages_are_found_in_markup_and_matched_literally(self):
        import usage_finder

        tmp = scratch(self, "xray-css-usage-")
        write(tmp, "Glow.vue", '<template><div class="dark-ambient-glow"></div></template>\n')
        write(tmp, "app.component.html", '<div class="dark-ambient-glow"></div>\n')
        write(tmp, "B.tsx", 'export const B = () => <div className="w-125" />;\n')
        found = {Path(u.file_path).name for u in usage_finder.find_usages_with_grep("dark-ambient-glow", [tmp])}
        self.assertEqual(found, {"Glow.vue", "app.component.html"})
        self.assertEqual(usage_finder.find_usages_with_grep("w-1.5", [tmp]), [])

    def test_a_class_name_usage_search_cannot_refuse_does_not_abort_the_analysis(self):
        from analyze_file import analyze_single_file, format_as_markdown

        tmp = scratch(self, "xray-css-analyze-")
        path = write(tmp, "src/tw.css", ".-mt-4 { margin-top: -1rem; }\n.md\\:flex { display: flex; }\n.card { color: red; }\n")
        result = analyze_single_file(path, find_usages=True, project_root=tmp)
        self.assertIn("error", result["usages"]["-mt-4"])
        self.assertIn("count", result["usages"]["card"])
        self.assertIn("card", format_as_markdown(result))

    def test_a_stylesheet_is_analyzed_but_never_rewritten(self):
        from comment_rewriter import CommentRewriter, CommentRewriterError

        path = write(scratch(self, "xray-css-comments-"), "theme.css", THEME_CSS)
        self.assertEqual(len(CommentRewriter().analyze_file(path).comments), 1)
        with self.assertRaises(CommentRewriterError):
            CommentRewriter().rewrite_file(path, dry_run=True)


    def test_a_stylesheet_verification_marker_is_validated_against_its_rules(self):
        from doc_review import DocReviewer

        tmp = scratch(self, "xray-css-markers-")
        write(tmp, "src/modal.css", ".modal {\n  position: fixed;\n}\n@media (max-width: 600px) {\n  .modal { inset: 0; }\n}\n")
        write(tmp, "docs/modal.md", (
            "Fixed [VERIFIED: modal.css::.modal], narrow [VERIFIED: modal.css::@media (max-width: 600px) { .modal }], "
            "gone [VERIFIED: modal.css::.gone].\n"
        ))
        statuses = [v.status for v in DocReviewer(str(tmp)).validate_markers("docs/")]
        self.assertEqual(statuses, ["valid", "valid", "stale_symbol"])

    def test_a_marker_for_an_attribute_selector_is_read_whole(self):
        from doc_review import DocReviewer

        tmp = scratch(self, "xray-css-attr-markers-")
        write(tmp, "src/form.css", 'input[type="text"] {\n  border: 0;\n}\n[data-theme=dark] .x {\n  top: 0;\n}\n')
        write(tmp, "docs/m.md", '[VERIFIED: form.css::input[type="text"]] and [VALIDATED: form.css::[data-theme=dark] .x]\n')
        self.assertEqual([v.status for v in DocReviewer(str(tmp)).validate_markers("docs/")], ["valid", "valid"])

    def test_comment_analysis_reads_a_css_double_slash_as_code(self):
        from comment_rewriter import CommentRewriter

        path = write(scratch(self, "xray-css-dialect-"), "a.css", ".a { color: red; }\n// .legacy { position: fixed; }\n.b { top: 0; }\n")
        self.assertEqual(len(CommentRewriter().analyze_file(path).comments), 0)


if __name__ == "__main__":
    unittest.main()
