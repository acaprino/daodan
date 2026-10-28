"""Office delivery gate: source protection, engine renders, coverage and review binding.

Search-before-write found no suite for completion gating; test_office_deckcraft.py
owns the inspectors and this suite reuses its deck builder. The engine is replaced
by an in-process fake that answers `info` and writes render images, so nothing is
downloaded or launched. Target runtime: under 10 seconds.
"""

import importlib.util
import json
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = next(parent for parent in Path(__file__).resolve().parents
            if (parent / "plugins/office/skills").is_dir())
SKILLS = ROOT / "plugins/office/skills"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gate = load(SKILLS / "intake/scripts/office_gate.py", "office_test_gate")
decks = load(Path(__file__).with_name("test_office_deckcraft.py"), "office_test_gate_decks")


def write_deck(path, *texts):
    with zipfile.ZipFile(path, "w") as archive:
        for name, body in decks.typed(decks.deck(*(decks.shape(text) for text in texts))).items():
            archive.writestr(name, body)
    return path


class FakeEngine:
    """Answers `info` with the page count and writes one image per page on `render`."""

    def __init__(self, pages, images=None, fail_render=False):
        self.pages, self.images, self.fail_render, self.calls = pages, images, fail_render, []

    def __call__(self, command, **_):
        self.calls.append(command)
        if command[1] == "info":
            return subprocess.CompletedProcess(command, 0, json.dumps({"slides": [{}] * self.pages,
                                                                       "pages": self.pages}), "")
        if self.fail_render:
            return subprocess.CompletedProcess(command, 1, "", "renderer crashed")
        if "--all" in command:
            folder = Path(command[-1])
            for number in range(1, (self.images or self.pages) + 1):
                (folder / f"slide-{number:02d}.png").write_bytes(b"png")
        else:
            Path(command[3]).write_bytes(b"png")
        return subprocess.CompletedProcess(command, 0, "", "")


class GateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.dir = Path(self.temp.name)
        self.source = write_deck(self.dir / "deck.pptx", "Kept title", "Second slide")
        self.record = gate.start(self.source)
        self.binary = self.dir / "deckcraft-cli.exe"

    def tearDown(self):
        self.temp.cleanup()

    def check(self, candidate, engine=None, **options):
        return gate.check(self.record, candidate, run=engine or FakeEngine(2),
                          locate=lambda _engine: self.binary, **options)

    def candidate(self, *texts):
        return write_deck(self.dir / "deck-v2.pptx", *(texts or ("Kept title", "Second slide")))

    def review(self, result, verdict="pass", names=None, digest=None):
        names = names if names is not None else sorted(p.name for p in Path(result["renders"]["folder"]).iterdir())
        path = self.dir / "review.md"
        path.write_text(f"Candidate SHA-256 {digest or result['sha256']}\nInspected: {', '.join(names)}\n"
                        f"Verdict: {verdict}\n", encoding="utf-8")
        return path

    def test_start_keeps_a_copy_and_leaves_the_source_untouched(self):
        before = self.source.read_bytes()
        record = json.loads((self.record / "gate.json").read_text(encoding="utf-8"))
        self.assertEqual(record["source"]["sha256"], gate.sha256(self.source))
        self.assertEqual((self.record / "source.pptx").read_bytes(), before)
        self.assertEqual(self.source.read_bytes(), before)
        self.assertEqual(self.record.parent, self.dir / ".daodan" / "office")

    def test_start_refuses_other_formats_and_a_new_file_without_folder(self):
        other = self.dir / "book.xlsx"
        other.write_bytes(b"x")
        with self.assertRaises(gate.GateError):
            gate.start(other)
        with self.assertRaises(gate.GateError):
            gate.start(kind="pptx")

    def test_check_without_record_is_blocked(self):
        result = gate.check(self.dir / "missing", self.candidate(), run=FakeEngine(2),
                            locate=lambda _engine: self.binary)
        self.assertEqual(result["verdict"], "blocked")
        self.assertIn("start", result["next"])

    def test_candidate_written_over_the_source_is_blocked_with_the_restore_path(self):
        write_deck(self.source, "Overwritten")
        for candidate in (self.source, self.candidate()):
            result = self.check(candidate)
            self.assertEqual(result["verdict"], "blocked")
            self.assertIn(str(self.record / "source.pptx"), result["next"])

    def test_missing_engine_blocks_and_names_the_installer(self):
        result = gate.check(self.record, self.candidate(), run=FakeEngine(2), locate=lambda _engine: None)
        self.assertEqual(result["verdict"], "blocked")
        self.assertIn("engine_install.py", result["next"])

    def test_rendered_candidate_without_review_asks_for_the_reviewer(self):
        engine, candidate = FakeEngine(2), self.candidate()
        result = self.check(candidate, engine)
        self.assertEqual(result["verdict"], "review-needed")
        self.assertEqual(result["renders"]["pages"], 2)
        self.assertIn(result["sha256"], result["next"])
        self.assertIn("office:presentation-reviewer", result["next"])
        self.check(candidate, engine)  # Same bytes: rebuilding the ZIP would change its timestamps.
        self.assertEqual(sum(command[1] == "render" for command in engine.calls), 1, "renders are reused")

    def test_lost_source_text_needs_a_fix_unless_the_user_approved_the_cut(self):
        candidate = self.candidate("Kept title", "Replaced slide")
        result = self.check(candidate)
        self.assertEqual(result["verdict"], "needs-fix")
        self.assertIn("Second slide", result["problems"][0])
        cuts = self.dir / "cuts.json"
        cuts.write_text(json.dumps([{"text": "Second slide", "reason": "user approved"}]), encoding="utf-8")
        self.assertEqual(self.check(candidate, cuts=cuts)["verdict"], "review-needed")

    def test_incomplete_render_is_blocked(self):
        self.assertEqual(self.check(self.candidate(), FakeEngine(2, images=1))["verdict"], "blocked")
        self.assertEqual(self.check(self.candidate(), FakeEngine(2, fail_render=True))["verdict"], "blocked")

    def test_review_must_bind_this_candidate_and_every_page(self):
        candidate = self.candidate()
        first = self.check(candidate)
        for review in (self.review(first, digest="0" * 64), self.review(first, names=["slide-01.png"])):
            result = self.check(candidate, review=review)
            self.assertEqual(result["verdict"], "review-needed", result["problems"])
        silent = self.dir / "silent.md"
        silent.write_text(first["sha256"] + " slide-01.png slide-02.png", encoding="utf-8")
        self.assertEqual(self.check(candidate, review=silent)["verdict"], "review-needed")

    def test_review_verdict_decides_the_outcome(self):
        candidate = self.candidate()
        first = self.check(candidate)
        expected = {"pass": "deliverable", "needs-fix": "needs-fix", "blocked": "blocked"}
        for verdict, outcome in expected.items():
            self.assertEqual(self.check(candidate, review=self.review(first, verdict))["verdict"], outcome)

    def test_new_document_renders_each_page_without_coverage(self):
        record = gate.start(directory=self.dir, kind="docx")
        candidate = self.dir / "report.docx"
        with zipfile.ZipFile(candidate, "w") as archive:
            archive.writestr("[Content_Types].xml", "<Types/>")
        engine = FakeEngine(3)
        result = gate.check(record, candidate, run=engine, locate=lambda _engine: self.binary)
        renders = [command for command in engine.calls if command[1] == "render"]
        self.assertEqual([command[-1] for command in renders], ["1", "2", "3"])
        self.assertEqual(sorted(p.name for p in Path(result["renders"]["folder"]).iterdir()),
                         ["page-01.png", "page-02.png", "page-03.png"])
        self.assertNotIn("coverage", result)

    def test_report_tells_an_unfinished_verdict_as_it_is(self):
        text = gate.report(self.check(self.candidate()))
        self.assertTrue(text.startswith("verdict: review-needed"))
        self.assertIn("not finished", text)


class MethodContractTests(unittest.TestCase):
    def test_methods_route_start_and_completion_through_the_gate(self):
        for skill in ("pptx", "docx"):
            text = (SKILLS / skill / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn("office_gate.py\" start", text)
            self.assertIn("office_gate.py\" check", text)
            self.assertIn("`deliverable`", text)
            self.assertIn("package XML by hand", text)
        intake = (SKILLS / "intake/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("editing package XML by", intake)

    def test_reviewers_write_what_the_gate_reads(self):
        for role in ("presentation-reviewer", "document-reviewer"):
            text = (ROOT / "plugins/office/roles" / f"{role}.md").read_text(encoding="utf-8")
            self.assertIn("SHA-256", text)
            self.assertIn("Verdict: pass", text)


if __name__ == "__main__":
    unittest.main()
