"""Ad hoc palette generation, seed extraction and the comparison page of office:design."""

import importlib.util
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

ROOT = next(parent for parent in Path(__file__).resolve().parents
            if (parent / "plugins").is_dir() and (parent / "scripts").is_dir())
SCRIPTS = ROOT / "plugins/office/skills/design/scripts"


def _load(name):
    spec = importlib.util.spec_from_file_location("office_test_" + name, SCRIPTS / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


palette = _load("palette")
preview = _load("palette_preview")

SEED_SETS = (["#1D4ED8"], ["#1D4ED8", "#E76F51"], ["#15803D"], ["#5D2E46", "#D4A5A5"],
             ["#F4A900"], ["#777777"], ["#E11D48"], ["#000000"], ["#FFFFFF"])


class ColourMathsTests(unittest.TestCase):
    def test_oklch_round_trips_srgb(self):
        for value in ("#1D4ED8", "#E76F51", "#FFFFFF", "#000000", "#777777"):
            rgb = palette.hex_to_rgb(value)
            L, C, H = palette.to_oklch(rgb)
            self.assertEqual(palette.rgb_to_hex(palette.from_oklch(L, C, H)), value)

    def test_contrast_matches_wcag_reference_values(self):
        white, black = palette.hex_to_rgb("#FFFFFF"), palette.hex_to_rgb("#000000")
        self.assertAlmostEqual(palette.contrast(white, black), 21.0, places=1)
        self.assertAlmostEqual(palette.contrast(palette.hex_to_rgb("#767676"), white), 4.54, places=2)

    def test_gamut_mapping_reduces_chroma_instead_of_clipping_hue(self):
        rgb = palette.from_oklch(0.6, 0.4, 150)
        self.assertTrue(all(0.0 <= c <= 1.0 for c in rgb))
        self.assertAlmostEqual(palette.to_oklch(rgb)[2], 150, delta=3)

    def test_invalid_hex_is_rejected(self):
        for value in ("#12", "#GGGGGG", "", "#12345"):
            with self.subTest(value=value), self.assertRaises(palette.PaletteError):
                palette.hex_to_rgb(value)


class CandidateTests(unittest.TestCase):
    def test_every_variant_passes_its_own_checks_for_many_seeds(self):
        for seeds in SEED_SETS:
            for variant, _ in palette.VARIANTS:
                with self.subTest(seeds=seeds, variant=variant):
                    built = palette.build_palette(variant, seeds)
                    check = built["check"]
                    self.assertTrue(check["passes"], check)
                    for role in ("ink", "accent", "muted"):
                        self.assertGreaterEqual(min(check["text"][role].values()), palette.TEXT_CONTRAST)
                    self.assertEqual(len(built["data"]), 4)
                    self.assertEqual(built["data"][0], built["accent"])
                    for value in check["data_on_background"]:
                        self.assertGreaterEqual(value, palette.GRAPHIC_CONTRAST)

    def test_variants_differ_in_the_one_axis_they_name(self):
        built = {variant: palette.build_palette(variant, ["#1D4ED8"]) for variant, _ in palette.VARIANTS}
        self.assertTrue(built["dark"]["dark"])
        self.assertLess(palette.to_oklch(palette.hex_to_rgb(built["dark"]["background"]))[0], 0.3)
        self.assertLess(palette.to_oklch(palette.hex_to_rgb(built["sober"]["accent"]))[1],
                        palette.to_oklch(palette.hex_to_rgb(built["faithful"]["accent"]))[1])
        self.assertLess(palette.to_oklch(palette.hex_to_rgb(built["bold"]["background"]))[0],
                        palette.to_oklch(palette.hex_to_rgb(built["faithful"]["background"]))[0])
        self.assertGreater(palette.to_oklch(palette.hex_to_rgb(built["deep"]["ink"]))[1],
                           palette.to_oklch(palette.hex_to_rgb(built["faithful"]["ink"]))[1])

    def test_the_faithful_variant_keeps_a_legible_seed_as_accent(self):
        built = palette.build_palette("faithful", ["#1D4ED8"])
        self.assertEqual(built["accent"], "#1D4ED8")

    def test_background_surface_and_ink_share_the_seed_hue(self):
        built = palette.build_palette("faithful", ["#E76F51"])
        hues = [palette.to_oklch(palette.hex_to_rgb(built[role]))[2] for role in ("background", "surface", "ink")]
        seed_hue = palette.to_oklch(palette.hex_to_rgb("#E76F51"))[2]
        for hue in hues:
            self.assertLess(palette.hue_diff(hue, seed_hue), 12)

    def test_check_reports_a_failing_hand_edited_palette(self):
        built = palette.build_palette("faithful", ["#1D4ED8"])
        built["accent"] = "#AAAAFF"
        self.assertFalse(palette.check_palette(built)["passes"])

    def test_candidates_cli_limits_seeds_and_variants(self):
        with mock.patch("sys.stdout"):
            self.assertEqual(palette.main(["candidates", "--seed", "#111111", "--seed", "#222222", "--seed", "#333333"]), 1)
        import io, contextlib
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(palette.main(["candidates", "--seed", "#1D4ED8", "--count", "2"]), 0)
        result = json.loads(out.getvalue())
        self.assertEqual([c["variant"] for c in result["candidates"]], ["sober", "faithful"])
        self.assertEqual(result["schema"], palette.SCHEMA)


class SeedSourceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def test_seeds_rank_saturated_frequent_colours_and_drop_neutrals(self):
        seeds = palette.rank_seeds({"#FFFFFF": 0.6, "#1D4ED8": 0.25, "#E76F51": 0.1, "#777777": 0.05}, 4)
        self.assertEqual([s["hex"] for s in seeds], ["#1D4ED8", "#E76F51"])

    def test_only_neutral_sources_still_yield_one_seed_with_a_note(self):
        seeds = palette.rank_seeds({"#FFFFFF": 0.7, "#333333": 0.3}, 4)
        self.assertEqual(len(seeds), 1)
        self.assertIn("note", seeds[0])

    def test_css_colours_are_counted_and_named_tokens_weighted(self):
        project = self.root / "src"
        project.mkdir()
        (project / "theme.css").write_text(
            ":root{--color-primary:#1D4ED8;--accent:#E76F51;--gray:#666}.a{color:#1D4ED8}.b{color:rgb(29,78,216)}",
            encoding="utf-8")
        (self.root / "node_modules").mkdir()
        (self.root / "node_modules" / "x.css").write_text(".x{color:#FF0000}", encoding="utf-8")
        result = palette.seeds_from_css([self.root], 4)
        self.assertEqual(result["named_tokens"], {"color-primary": "#1D4ED8", "accent": "#E76F51"})
        self.assertEqual([s["hex"] for s in result["seeds"]][:2], ["#1D4ED8", "#E76F51"])
        self.assertFalse(any("node_modules" in f for f in result["files_read"]))

    def test_office_file_theme_scheme_and_used_colours_are_read(self):
        deck = self.root / "deck.pptx"
        a = "http://schemas.openxmlformats.org/drawingml/2006/main"
        with zipfile.ZipFile(deck, "w") as archive:
            archive.writestr("ppt/theme/theme1.xml",
                             f'<a:theme xmlns:a="{a}"><a:themeElements><a:clrScheme name="x">'
                             '<a:dk1><a:sysClr val="windowText" lastClr="000000"/></a:dk1>'
                             '<a:lt1><a:srgbClr val="FFFFFF"/></a:lt1>'
                             '<a:accent1><a:srgbClr val="1D4ED8"/></a:accent1>'
                             '<a:accent2><a:srgbClr val="E76F51"/></a:accent2>'
                             '</a:clrScheme></a:themeElements></a:theme>')
            archive.writestr("ppt/slides/slide1.xml", f'<p:sld xmlns:a="{a}"><a:srgbClr val="15803D"/></p:sld>')
        result = palette.seeds_from_file(deck, 4)
        self.assertEqual(result["theme_scheme"]["accent1"], "#1D4ED8")
        self.assertEqual(result["theme_scheme"]["dk1"], "#000000")
        self.assertEqual([s["hex"] for s in result["seeds"]][0], "#1D4ED8")
        self.assertIn("#15803D", [s["hex"] for s in result["seeds"]])

    def test_url_reads_theme_color_and_stylesheets_without_leaving_http(self):
        pages = {
            "https://example.com/": b'<html><head><meta name="theme-color" content="#1D4ED8">'
                                    b'<link rel="stylesheet" href="/s.css"></head></html>',
            "https://example.com/s.css": b".a{color:#E76F51}.b{color:#E76F51}",
        }
        with mock.patch.object(palette, "_get", side_effect=lambda url, limit: pages[url]):
            result = palette.seeds_from_url("https://example.com/", 4)
        self.assertEqual(result["theme_color"], ["#1D4ED8"])
        self.assertEqual(result["stylesheets_read"], ["https://example.com/s.css"])
        self.assertEqual([s["hex"] for s in result["seeds"]], ["#1D4ED8", "#E76F51"])
        with self.assertRaises(palette.PaletteError):
            palette._get("file:///etc/passwd", 10)

    def test_image_seeds_need_pillow_and_read_dominant_colours(self):
        try:
            from PIL import Image
        except ImportError:
            self.skipTest("Pillow not installed")
        image = Image.new("RGBA", (40, 20), (255, 255, 255, 255))
        for x in range(24):
            for y in range(20):
                image.putpixel((x, y), (29, 78, 216, 255))
        for x in range(24, 32):
            for y in range(20):
                image.putpixel((x, y), (231, 111, 81, 255))
        path = self.root / "logo.png"
        image.save(path)
        seeds = palette.seeds_from_image_bytes(path.read_bytes(), 4)
        self.assertEqual([s["hex"] for s in seeds][:2], ["#1D4ED8", "#E76F51"])
        with self.assertRaises(palette.PaletteError):
            palette.seeds_from_image_bytes(b"not an image", 4)


class PreviewTests(unittest.TestCase):
    def test_page_lists_every_candidate_with_number_strip_and_detail(self):
        document = {"seeds": ["#1D4ED8"],
                    "candidates": [palette.build_palette(v, ["#1D4ED8"]) for v, _ in palette.VARIANTS]}
        html = preview.render(document, "Test palettes")
        self.assertEqual(html.count('class="card"'), 5)
        self.assertEqual(html.count('class="candidate"'), 5)
        self.assertEqual(html.count(" hidden"), 4)
        for candidate in document["candidates"]:
            for role in ("background", "ink", "surface", "accent", "muted"):
                self.assertIn(candidate[role], html)
        self.assertIn("answer with the number", html)
        self.assertNotIn("<script src", html)
        self.assertNotIn("http://", html.split("<body>")[1])

    def test_field_labels_pick_the_more_legible_of_ink_and_background(self):
        built = palette.build_palette("dark", ["#1D4ED8"])
        self.assertEqual(preview._text_on(built["background"], built), built["ink"])
        self.assertEqual(preview._text_on(built["ink"], built), built["background"])

    def test_cli_writes_the_page_and_refuses_empty_input(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "c.json").write_text(json.dumps(
                {"candidates": [palette.build_palette("faithful", ["#1D4ED8"])]}), encoding="utf-8")
            with mock.patch("sys.stdout"):
                self.assertEqual(preview.main([str(root / "c.json"), "--out", str(root / "out" / "p.html")]), 0)
                self.assertTrue((root / "out" / "p.html").is_file())
                (root / "e.json").write_text(json.dumps({"candidates": []}), encoding="utf-8")
                self.assertEqual(preview.main([str(root / "e.json"), "--out", str(root / "x.html")]), 1)


class PaletteContractTests(unittest.TestCase):
    """The scripts ship to every host and the method cites them."""

    def test_scripts_and_method_reach_every_host(self):
        exports = ROOT / "exports"
        for host in ("claude", "copilot", "codex", "pi", "opencode"):
            root = exports / host / "plugins/office/skills"
            if not root.is_dir():
                self.skipTest(f"{host} package not built")
            with self.subTest(host=host):
                for name in ("palette.py", "palette_preview.py"):
                    self.assertEqual((root / "design/scripts" / name).read_bytes(),
                                     (SCRIPTS / name).read_bytes())
                skill = (root / "design/SKILL.md").read_text(encoding="utf-8")
                self.assertIn("palette.py\" candidates", skill)
                self.assertIn("ask which number to use", skill)
                intake = (root / "intake/SKILL.md").read_text(encoding="utf-8")
                self.assertIn("colour source", intake)


if __name__ == "__main__":
    unittest.main()
