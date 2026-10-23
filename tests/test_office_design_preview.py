"""Contract tests for the presentation design preview generator.

The preview is a review artifact: these tests verify plan validation, library
reading, wireframe geometry and honest scope labelling. They do not prove
browser rendering or PowerPoint fidelity.
"""

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = next(
    parent for parent in Path(__file__).resolve().parents
    if (parent / "scripts/daodan").is_dir()
)
PRESENTATION = REPO_ROOT / "plugins/office/skills/presentation-design"
SCRIPT = PRESENTATION / "scripts/design_preview.py"
LAYOUT_PATTERNS = PRESENTATION / "references/layout-patterns.md"
VISUAL_DIRECTIONS = PRESENTATION / "references/visual-directions.md"
DIRECTIONS_WITH_PALETTE = 16
PATTERNS_IN_LIBRARY = 18


def _load_module():
    spec = importlib.util.spec_from_file_location("design_preview", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _plan(**overrides):
    plan = {
        "deck_title": "Test deck",
        "direction": {"library": "A"},
        "slides": [
            {"pattern": "cover", "title": "Cover title", "subtitle": "Sub", "meta": "Meta"},
            {"pattern": "executive summary", "headline": "One decision per slide",
             "content": {"cards": ["A", "B", "C"]}, "source_note": "Source"},
        ],
    }
    plan.update(overrides)
    return plan


class LibraryParsingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.preview = _load_module()

    def test_every_documented_direction_is_read_with_four_colours(self):
        directions = self.preview.parse_directions(VISUAL_DIRECTIONS)
        self.assertEqual(len(directions), DIRECTIONS_WITH_PALETTE)
        for label, entry in directions.items():
            with self.subTest(direction=label):
                self.assertTrue(entry["name"])
                self.assertTrue(entry["typography"])
                if label == "H":
                    continue
                for key in ("background", "ink", "surface", "accent"):
                    self.assertRegex(entry[key], r"^#[0-9A-Fa-f]{6}$")

    def test_brand_direction_requires_an_explicit_palette_to_render(self):
        direction, problems = self.preview.resolve_direction({"library": "H"}, self.preview.parse_directions(VISUAL_DIRECTIONS))
        self.assertTrue(any("missing background" in item for item in problems))
        palette = {"background": "#000000", "ink": "#FFFFFF", "surface": "#111111", "accent": "#00AAFF"}
        direction, problems = self.preview.resolve_direction({"library": "H", "palette": palette}, self.preview.parse_directions(VISUAL_DIRECTIONS))
        self.assertEqual(problems, [])
        self.assertEqual(direction["background"], "#000000")

    def test_every_documented_pattern_is_read_with_capacity_and_geometry(self):
        patterns = self.preview.parse_patterns(LAYOUT_PATTERNS)
        self.assertEqual(len(patterns), PATTERNS_IN_LIBRARY)
        for key, entry in patterns.items():
            with self.subTest(pattern=key):
                self.assertIn(key, self.preview.PATTERN_GEOMETRY,
                              f"Pattern {key} has no wireframe geometry")
                self.assertTrue(entry["name"])
                self.assertTrue(entry["job"])
                self.assertTrue(entry["details"])
                self.assertTrue(entry["slots"])
                capacity = self.preview.resolve_pattern(key, patterns)["capacity"]
                self.assertGreaterEqual(capacity, 0)
                self.assertLessEqual(capacity, 6, "Wireframe capacity must respect the density cap")
                if capacity == 0:
                    self.assertIn(key, {"cover", "section divider", "chart and insight",
                                        "case study", "quote and testimonial"},
                                  "Only single-instance patterns may have no repeatable slots")

    def test_wireframe_geometry_stays_inside_the_canvas_and_clear_of_other_boxes(self):
        for key, (meta, boxes) in self.preview.PATTERN_GEOMETRY.items():
            with self.subTest(pattern=key):
                self.assertGreaterEqual(len(boxes), 3)
                for label, (x, y, w, h) in boxes.items():
                    with self.subTest(box=label):
                        self.assertGreaterEqual(x, 0)
                        self.assertGreaterEqual(y, 0)
                        self.assertLessEqual(x + w, 1000)
                        self.assertLessEqual(y + h, 562.5)
                if meta["kind"] in ("cover", "divider"):
                    continue
                # The rendered headline band occupies the top of the frame.
                self.assertGreaterEqual(
                    min(y for _, y, _, _ in boxes.values()), 135,
                    f"Pattern {key} draws a box inside the headline band",
                )
                for (label, (x, y, w, h)) in boxes.items():
                    for (other, (ox, oy, ow, oh)) in boxes.items():
                        if label >= other:
                            continue
                        overlap_x = min(x + w, ox + ow) - max(x, ox)
                        overlap_y = min(y + h, oy + oh) - max(y, oy)
                        self.assertFalse(
                            overlap_x > 0 and overlap_y > 0,
                            f"Pattern {key}: boxes '{label}' and '{other}' overlap",
                        )


class PlanValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.preview = _load_module()
        cls.library = cls.preview.load_library()

    def build(self, plan):
        return self.preview.build_document(plan, self.library)

    def test_valid_plan_renders_frames_for_every_slide(self):
        document, problems = self.build(_plan())
        self.assertEqual(problems, [])
        self.assertIn("<!DOCTYPE html>", document)
        self.assertIn('id="slide-1"', document)
        self.assertIn('id="slide-2"', document)
        self.assertIn("One decision per slide", document)
        self.assertIn("Slide sequence", document)
        self.assertIn("preview only", document)

    def test_unknown_pattern_and_unknown_direction_are_reported_not_rendered(self):
        document, problems = self.build(_plan(slides=[{"pattern": "hologram", "headline": "x"}]))
        self.assertEqual(document, "")
        self.assertTrue(any("unknown pattern 'hologram'" in item for item in problems))
        document, problems = self.build(_plan(direction={"library": "Z"}))
        self.assertEqual(document, "")
        self.assertTrue(any("unknown library direction: Z" in item for item in problems))

    def test_palette_must_be_complete_and_hex(self):
        document, problems = self.build(_plan(direction={"palette": {"background": "white"}}))
        self.assertEqual(document, "")
        self.assertTrue(any("palette.background" in item for item in problems))
        self.assertTrue(any("missing ink" in item for item in problems))

    def test_density_and_capacity_problems_are_reported_with_slide_numbers(self):
        slides = [
            {"pattern": "executive summary", "headline": "Too many cards",
             "content": {"cards": ["A", "B", "C", "D", "E"]}},
            {"pattern": "data table", "headline": "Too small",
             "content": {"rows": ["A"]}, "density": 9},
        ]
        document, problems = self.build(_plan(slides=slides))
        self.assertEqual(document, "")
        self.assertTrue(any(item.startswith("slide 1: 5 items exceed") for item in problems))
        self.assertTrue(any("below the 13 pt floor" in item for item in problems))

    def test_capacity_matches_the_wireframe_and_a_within_capacity_plan_renders(self):
        entry = self.preview.resolve_pattern("executive summary", self.library[0])
        self.assertEqual(entry["capacity"], 3)
        document, problems = self.build(_plan(slides=[
            {"pattern": "executive summary", "headline": "Four cards do not fit",
             "content": {"cards": ["A", "B", "C", "D"]}},
        ]))
        self.assertEqual(document, "")
        self.assertTrue(any("4 items exceed the pattern's 3" in item for item in problems))
        document, problems = self.build(_plan(slides=[
            {"pattern": "executive summary", "headline": "Three cards fit",
             "content": {"cards": ["A", "B", "C"]}},
            {"pattern": "data table", "headline": "Five rows fit",
             "content": {"rows": list("ABCDE")}},
        ]))
        self.assertEqual(problems, [])
        self.assertIn("Five rows fit", document)

    def test_missing_headline_and_overlong_text_are_plan_problems(self):
        slides = [
            {"pattern": "executive summary"},
            {"pattern": "cover", "title": "T" * 100},
            {"pattern": "data table", "headline": "H" * 120},
        ]
        document, problems = self.build(_plan(slides=slides))
        self.assertEqual(document, "")
        self.assertTrue(any("no action headline" in item for item in problems))
        self.assertTrue(any("title is 100 characters" in item for item in problems))
        self.assertTrue(any("headline is 120 characters" in item for item in problems))

    def test_cover_and_divider_do_not_require_an_action_headline(self):
        slides = [
            {"pattern": "cover", "title": "Cover"},
            {"pattern": "section divider", "title": "Appendix"},
        ]
        document, problems = self.build(_plan(slides=slides))
        self.assertEqual(problems, [])
        self.assertIn('id="slide-2"', document)

    def test_empty_and_oversized_slide_lists_are_refused(self):
        document, problems = self.build(_plan(slides=[]))
        self.assertEqual(document, "")
        self.assertIn("plan has no slides", problems)
        slide = {"pattern": "executive summary", "headline": "x", "content": {"cards": ["A"]}}
        document, problems = self.build(_plan(slides=[slide] * (self.preview.MAX_SLIDES + 1)))
        self.assertEqual(document, "")
        self.assertTrue(any("exceed the 60-slide preview bound" in item for item in problems))

    def test_injected_plan_text_cannot_break_the_document(self):
        slides = [{"pattern": "cover", "title": "</title><script>alert(1)</script>"}]
        document, problems = self.build(_plan(slides=slides))
        self.assertEqual(problems, [])
        self.assertNotIn("<script>", document)
        self.assertIn("&lt;script&gt;", document)


class CommandLineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)

    def run_script(self, *arguments):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *arguments],
            capture_output=True, text=True, timeout=60,
        )

    def test_missing_plan_argument_is_an_invocation_error(self):
        result = self.run_script()
        self.assertEqual(result.returncode, 2)
        self.assertIn("missing --plan", result.stderr)
        self.assertIn("nothing was read or written", result.stderr)

    def test_invalid_json_writes_nothing_and_reports_position(self):
        plan = self.directory / "broken.json"
        plan.write_text("{ not json", encoding="utf-8")
        out = self.directory / "preview.html"
        result = self.run_script("--plan", str(plan), "--out", str(out))
        self.assertEqual(result.returncode, 1)
        self.assertIn("not valid JSON", result.stderr)
        self.assertFalse(out.exists())

    def test_plan_problems_write_nothing(self):
        plan = self.directory / "plan.json"
        plan.write_text(json.dumps(_plan(slides=[{"pattern": "nope", "headline": "x"}])), encoding="utf-8")
        out = self.directory / "preview.html"
        result = self.run_script("--plan", str(plan), "--out", str(out))
        self.assertEqual(result.returncode, 1)
        self.assertIn("unknown pattern", result.stderr)
        self.assertFalse(out.exists())

    def test_missing_output_directory_writes_nothing(self):
        plan = self.directory / "plan.json"
        plan.write_text(json.dumps(_plan()), encoding="utf-8")
        out = self.directory / "missing" / "preview.html"
        result = self.run_script("--plan", str(plan), "--out", str(out))
        self.assertEqual(result.returncode, 2)
        self.assertIn("output directory does not exist", result.stderr)
        self.assertFalse(out.exists())

    def test_render_writes_html_and_reports_the_review_scope(self):
        plan = self.directory / "plan.json"
        plan.write_text(json.dumps(_plan()), encoding="utf-8")
        out = self.directory / "preview.html"
        result = self.run_script("--plan", str(plan), "--out", str(out))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("preview only", result.stdout)
        document = out.read_text(encoding="utf-8")
        self.assertIn("<!DOCTYPE html>", document)
        self.assertIn("One decision per slide", document)

    def test_view_summary_reports_capacity_and_writes_nothing(self):
        plan = self.directory / "plan.json"
        plan.write_text(json.dumps(_plan()), encoding="utf-8")
        before = set(self.directory.iterdir())
        result = self.run_script("--plan", str(plan), "--view")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("executive summary: One decision per slide | 3/3 Executive summary capacity", result.stdout)
        self.assertEqual(set(self.directory.iterdir()), before)


if __name__ == "__main__":
    unittest.main()
