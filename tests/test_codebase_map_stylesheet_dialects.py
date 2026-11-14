"""Every stylesheet file and style block in the snapshot with its rules, or listed with the reason it is not read.

Expectations are written by hand from the sources below, before the reader existed.
"""

import sys
import textwrap
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "plugins/codebase-map/skills/map/scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from languages import SUPPORTED_EXTENSIONS, get_adapter  # noqa: E402
from languages.stylesheet import dialect_for, iter_styled_blocks, parse_sheet  # noqa: E402

# Indented Sass: the same facts as the SCSS below, line for line.
SASS = textwrap.dedent(
    """\
    // tokens come first
    @use "tokens" as t
    $gap: 4px !default
    =pad($x)
      padding: $x
    .card,
    .card-alt
      color: red
      margin: t.$gap
      +pad(2px)
      &__title
        color: blue
      @media (min-width: 600px)
        display: grid
    /* a loud comment
       that runs on
    .after-comment
      a: b
    %ph
      font:
        family: serif
    .ext
      @extend %ph
      width: calc(100% - #{$gap}) // trailing
      background: url(//cdn.example/x.png)
    """
)
SCSS = textwrap.dedent(
    """\
    // tokens come first
    @use "tokens" as t;
    $gap: 4px !default;
    @mixin pad($x) {
      padding: $x; }
    .card,
    .card-alt {
      color: red;
      margin: t.$gap;
      @include pad(2px);
      &__title {
        color: blue; }
      @media (min-width: 600px) {
        display: grid; } }
    /* a loud comment
       that runs on */
    .after-comment {
      a: b; }
    %ph {
      font: {
        family: serif; } }
    .ext {
      @extend %ph;
      width: calc(100% - #{$gap}); // trailing
      background: url(//cdn.example/x.png); }
    """
)


def symbols(result):
    return [(c.name, c.kind, c.line_number, c.end_line) for c in result.classes]


def styled(content: str, name: str):
    return [(node.selectors, node.line, node.end_line, [(d.property, d.value, d.line) for d in node.declarations])
            for node in iter_styled_blocks(parse_sheet(content, dialect_for(name)))]


class IndentedSassTests(unittest.TestCase):
    def test_sass_maps_to_the_stylesheet_adapter(self):
        self.assertEqual(SUPPORTED_EXTENSIONS.get(".sass"), "css")
        self.assertEqual(dialect_for("a/_x.sass"), "sass")

    def test_the_symbols_are_those_of_the_same_sheet_in_scss(self):
        sass = get_adapter("css").parse(SASS, "theme.sass")
        self.assertEqual(sass.notes, ["parser=stylesheet (sass)"])
        self.assertEqual(symbols(sass), [
            ("$gap", "variable", 3, 3),
            (".card, .card-alt", "rule", 6, 14),
            (".card__title, .card-alt__title", "rule", 11, 12),
            (".after-comment", "rule", 17, 18),
            ("%ph", "rule", 19, 21),
            (".ext", "rule", 22, 25),
        ])
        self.assertEqual([(f.name, f.line_number, f.end_line, [p.name for p in f.parameters]) for f in sass.functions],
                         [("pad", 4, 5, ["$x"])])
        self.assertEqual([(i.module, i.is_internal) for i in sass.imports], [("./tokens", True)])
        self.assertEqual(sass.exported_symbols, ["card", "card-alt", "card__title", "card-alt__title",
                                                 "after-comment", "ext"])
        scss = get_adapter("css").parse(SCSS, "theme.scss")
        self.assertEqual(symbols(sass), symbols(scss))
        self.assertEqual(sass.constants, scss.constants)

    def test_declarations_land_on_their_lines(self):
        self.assertEqual(styled(SASS, "theme.sass"), [
            ([".card", ".card-alt"], 6, 14, [("color", "red", 8), ("margin", "t.$gap", 9)]),
            ([".card__title", ".card-alt__title"], 11, 12, [("color", "blue", 12)]),
            ([".card", ".card-alt"], 13, 14, [("display", "grid", 14)]),
            ([".after-comment"], 17, 18, [("a", "b", 18)]),
            (["%ph"], 19, 21, [("font-family", "serif", 21)]),
            ([".ext"], 22, 25, [("width", "calc(100% - #{$gap})", 24),
                                ("background", "url(//cdn.example/x.png)", 25)]),
        ])
        self.assertEqual(styled(SASS, "theme.sass"), styled(SCSS, "theme.scss"))

    def test_comments_keep_their_lines(self):
        comments = get_adapter("css").extract_comments(SASS, "theme.sass")
        self.assertEqual([(c.line_number, c.is_block) for c in comments], [(1, False), (15, True), (24, False)])


class SnapshotDialectTests(unittest.TestCase):
    def setUp(self):
        import shutil
        import tempfile

        import snapshot

        self.snapshot = snapshot
        self.root = Path(tempfile.mkdtemp(prefix="dialects-"))
        self.addCleanup(shutil.rmtree, self.root, True)
        files = {
            "styles/_variables.scss": "$gap: 4px;\n",
            "styles/main.sass": '@use "variables"\n.page\n  margin: variables.$gap\n',
            "styles/app.pcss": ".app {\n  & .title { color: red; }\n}\n",
            "styles/legacy.styl": ".old\n  color red\n",
        }
        for rel, text in files.items():
            (self.root / rel).parent.mkdir(parents=True, exist_ok=True)
            (self.root / rel).write_text(text, encoding="utf-8")
        self.files = snapshot.build_manifest(self.root)["files"]

    def entry(self, suffix):
        return next(v for k, v in self.files.items() if k.endswith(suffix))

    def test_indented_sass_is_parsed_and_resolves_its_partial(self):
        entry = self.entry("styles/main.sass")
        self.assertEqual((entry["language"], entry["status"]), ("css", "parsed"))
        self.assertEqual((entry["symbols"][".page"]["start"], entry["symbols"][".page"]["end"]), (2, 3))
        known = self.snapshot._by_basename(["styles/_variables.scss", "styles/main.sass"])
        self.assertEqual(self.snapshot.resolve_module("./variables", "styles/main.sass", known),
                         "styles/_variables.scss")

    def test_a_postcss_sheet_is_css(self):
        entry = self.entry("styles/app.pcss")
        self.assertEqual((entry["language"], entry["status"]), ("css", "parsed"))
        self.assertEqual(sorted(entry["symbols"]), [".app", ".app .title"])

    def test_stylus_is_listed_with_the_reason_it_is_not_read(self):
        entry = self.entry("styles/legacy.styl")
        self.assertEqual((entry["status"], entry["symbols"]), ("file-level", {}))
        self.assertEqual(entry["parser_notes"], ["not read: no Stylus reader in the product"])


VUE = textwrap.dedent(
    """\
    <template>
      <div class="card" :class="{ active: on }"></div>
    </template>

    <script setup lang="ts">
    const on = true
    function submit() {}
    </script>

    <style scoped>
    .card { color: red; }
    .card:hover { color: blue; }
    </style>

    <style lang="scss" module>
    .panel {
      &__title { margin: 0; }
    }
    </style>

    <style lang="stylus">
    .x
      color red
    </style>
    """
)
SVELTE = textwrap.dedent(
    """\
    <script>
      let on = false;
    </script>

    <div class="card" class:on></div>

    <style>
      .card { color: red; }
      :global(.dark) .card { color: white; }
    </style>
    """
)
HTML = textwrap.dedent(
    """\
    <!doctype html>
    <html>
    <head>
    <style>
      .shell { display: grid; }
      @media (max-width: 600px) {
        .shell { display: block; }
      }
    </style>
    </head>
    <body class="shell"><p style="color: red">x</p></body>
    </html>
    """
)
ASTRO = '---\nconst title = "x";\n---\n<h1 class="title">{title}</h1>\n<style>\n  .title { color: red; }\n</style>\n'
EJS = "<style>\n  .nav { color: <%= color %>; }\n</style>\n"


class StyleBlockTests(unittest.TestCase):
    def test_vue_style_blocks_are_rules_beside_the_script(self):
        result = get_adapter("vue").parse(VUE, "Button.vue")
        rules = [s for s in symbols(result) if s[1] == "rule"]
        self.assertEqual(rules, [(".card", "rule", 11, 11), (".card:hover", "rule", 12, 12),
                                 (".panel", "rule", 16, 18), (".panel__title", "rule", 17, 17)])
        self.assertIn("submit", [f.name for f in result.functions])
        self.assertIn("style blocks: stylesheet (css, scss)", result.notes)
        self.assertIn("style block at line 21 not read: no Stylus reader in the product", result.notes)

    def test_svelte_style_block(self):
        result = get_adapter("svelte").parse(SVELTE, "Card.svelte")
        self.assertEqual([s for s in symbols(result) if s[1] == "rule"],
                         [(".card", "rule", 8, 8), (":global(.dark) .card", "rule", 9, 9)])

    def test_markup_files_have_the_rules_of_their_style_blocks(self):
        self.assertEqual(SUPPORTED_EXTENSIONS.get(".html"), "markup")
        self.assertEqual(SUPPORTED_EXTENSIONS.get(".ejs"), "markup")
        self.assertEqual(SUPPORTED_EXTENSIONS.get(".astro"), "markup")
        self.assertEqual(symbols(get_adapter("markup").parse(HTML, "index.html")), [
            (".shell", "rule", 5, 5),
            ("@media (max-width: 600px)", "at-rule", 6, 8),
            ("@media (max-width: 600px) { .shell }", "rule", 7, 7),
        ])
        self.assertEqual(symbols(get_adapter("markup").parse(ASTRO, "Title.astro")), [(".title", "rule", 6, 6)])
        self.assertEqual(symbols(get_adapter("markup").parse(EJS, "nav.ejs")), [(".nav", "rule", 2, 2)])
        self.assertEqual(symbols(get_adapter("markup").parse("<p>x</p>\n", "plain.html")), [])

    def test_the_snapshot_records_style_blocks_and_lists_pug(self):
        import shutil
        import tempfile

        import snapshot

        root = Path(tempfile.mkdtemp(prefix="style-blocks-"))
        self.addCleanup(shutil.rmtree, root, True)
        (root / "index.html").write_text(HTML, encoding="utf-8")
        (root / "page.pug").write_text("style.\n  .a { color: red; }\n", encoding="utf-8")
        files = snapshot.build_manifest(root)["files"]
        html = next(v for k, v in files.items() if k.endswith("index.html"))
        self.assertEqual((html["language"], html["status"]), ("markup", "parsed"))
        self.assertEqual((html["symbols"][".shell"]["start"], html["symbols"][".shell"]["end"]), (5, 5))
        pug = next(v for k, v in files.items() if k.endswith("page.pug"))
        self.assertEqual((pug["status"], pug["parser_notes"]), ("file-level", ["not read: no Pug reader in the product"]))
        self.assertEqual(snapshot.cited_symbols("see `index.html::@media (max-width: 600px) { .shell }`"),
                         [("index.html", "@media (max-width: 600px) { .shell }")])


class ModernCssTests(unittest.TestCase):
    def test_every_modern_block_is_a_symbol(self):
        sheet = (REPO_ROOT / "benchmarks/inference-audit/fixtures/css-modern/src/modern.css").read_text(encoding="utf-8")
        self.assertEqual(symbols(get_adapter("css").parse(sheet, "modern.css")), [
            ("@property --angle", "at-rule", 4, 4),
            (".card", "rule", 5, 9),
            (".card .title", "rule", 7, 7),
            (".card:has(.icon)", "rule", 8, 8),
            ("@scope (.panel) to (.panel-body)", "at-rule", 10, 12),
            ("@scope (.panel) to (.panel-body) { .heading }", "rule", 11, 11),
            ("@media (--narrow)", "at-rule", 13, 15),
            ("@media (--narrow) { :is(.card, .tile) > :where(.badge) }", "rule", 14, 14),
            ("@media (--wide)", "at-rule", 16, 16),
            ("@media (--wide) { .x }", "rule", 16, 16),
            ("@supports (display: grid)", "at-rule", 17, 19),
            ("@supports (display: grid) { @container side (min-width: 20em) { .tile } }", "rule", 18, 18),
            (".side", "rule", 20, 20),
            ("@layer components", "at-rule", 21, 21),
            ("@layer components { .btn }", "rule", 21, 21),
        ])


if __name__ == "__main__":
    unittest.main()
