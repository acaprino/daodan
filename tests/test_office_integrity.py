"""Static integrity rules, their report contract and the verify/fix entries on every host.

Packages are synthetic and minimal. These tests establish rule behaviour and
shipped instructions, not rendering, recalculation or installed-host execution.
"""

import contextlib
import importlib.util
import io
import json
import os
import re
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
for import_root in (REPO_ROOT, REPO_ROOT / "tests"):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

import test_office_deckcraft as deck_fixtures  # noqa: E402
import test_office_docx as word_fixtures  # noqa: E402
import test_office_xlsx as sheet_fixtures  # noqa: E402
from scripts.daodan.adapter import HOSTS, load_adapter  # noqa: E402
from scripts.daodan.load import load_plugin  # noqa: E402
from scripts.daodan.render import render_plugin  # noqa: E402
from host_binding_assertions import loaded_instruction_text  # noqa: E402
import office_entries  # noqa: E402

OFFICE = REPO_ROOT / "plugins/office"
SCRIPT = OFFICE / "skills/integrity/scripts/office_verify.py"
RULES = OFFICE / "skills/integrity/references/rules.md"
SPEC = importlib.util.spec_from_file_location("office_verify_under_test", SCRIPT)
verifier = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verifier)

WP = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
P, A = deck_fixtures.P, deck_fixtures.A
ENTRY_PATHS = {
    "claude": "commands/{name}.md",
    "copilot": "prompts/{name}.prompt.md",
    "codex": "skills/{name}-workflow/SKILL.md",
    "pi": "prompts/daodan-{name}.md",
    "opencode": "commands/{name}.md",
}


def rules_of(report):
    return {item["rule"] for item in report["findings"]}


def picture(name="Picture 1", descr=None, decorative=False):
    extension = ('<a:extLst xmlns:a="' + A + '"><a:ext uri="{C183D7F6-B498-43B3-948B-1728B52AA6E4}">'
                 '<adec:decorative xmlns:adec="http://schemas.microsoft.com/office/drawing/2017/decorative" val="1"/>'
                 "</a:ext></a:extLst>") if decorative else ""
    description = ' descr="' + descr + '"' if descr else ""
    return ('<w:p><w:r><w:drawing><wp:inline xmlns:wp="' + WP + '"><wp:docPr id="1" name="' + name + '"'
            + description + ">" + extension + "</wp:docPr></wp:inline></w:drawing></w:r></w:p>")


def styled(text, style):
    return '<w:p><w:pPr><w:pStyle w:val="' + style + '"/></w:pPr><w:r><w:t>' + text + "</w:t></w:r></w:p>"


STYLES = ('<w:styles xmlns:w="' + word_fixtures.WORD_NS + '">' + "".join(
    '<w:style w:type="paragraph" w:styleId="Heading' + str(level) + '"><w:name w:val="heading '
    + str(level) + '"/></w:style>' for level in (1, 2, 3)) + "</w:styles>")


def title(text="Agenda"):
    return ('<p:sp><p:nvSpPr><p:cNvPr id="2" name="Title 1"/><p:cNvSpPr/><p:nvPr><p:ph type="title"/></p:nvPr>'
            '</p:nvSpPr><p:txBody><a:p><a:r><a:t>' + text + '</a:t></a:r></a:p></p:txBody></p:sp>')


def slide_picture(descr=None):
    description = ' descr="' + descr + '"' if descr else ""
    return ('<p:pic><p:nvPicPr><p:cNvPr id="3" name="Picture 2"' + description + '/><p:cNvPicPr/><p:nvPr/>'
            '</p:nvPicPr><p:blipFill/><p:spPr/></p:pic>')


def positioned(x, width):
    return ('<p:sp><p:nvSpPr><p:cNvPr id="5" name="Box 4"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr><p:spPr><a:xfrm>'
            '<a:off x="' + str(x) + '" y="0"/><a:ext cx="' + str(width) + '" cy="100"/></a:xfrm></p:spPr>'
            '<p:txBody><a:p><a:r><a:t>Note</a:t></a:r></a:p></p:txBody></p:sp>')


EMPTY_PLACEHOLDER = ('<p:sp><p:nvSpPr><p:cNvPr id="4" name="Content 3"/><p:cNvSpPr/><p:nvPr><p:ph idx="1"/>'
                     '</p:nvPr></p:nvSpPr><p:txBody><a:p/></p:txBody></p:sp>')


def grid(rows):
    """A worksheet from {row: cells xml}."""
    body = "".join('<row r="' + str(number) + '">' + cells + "</row>" for number, cells in sorted(rows.items()))
    return '<worksheet xmlns="' + sheet_fixtures.SHEET_NS + '"><sheetData>' + body + "</sheetData></worksheet>"


def formula(ref, text, value="0", attributes=""):
    return '<c r="' + ref + '"><f' + attributes + ">" + text + "</f><v>" + value + "</v></c>"


class IntegrityRuleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)

    def write(self, parts, filename):
        destination = self.directory / filename
        with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
            for name, data in parts.items():
                archive.writestr(name, data)
        return destination

    def word(self, body, extra=None):
        parts = word_fixtures.package_parts(body + '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/></w:sectPr>')
        parts.update(extra or {})
        return verifier.verify(self.write(word_fixtures.add_content_types(parts), "document.docx"))

    def deck(self, *bodies, hidden=False):
        content = deck_fixtures.parts(tuple("slide" + str(n) + ".xml" for n in range(1, len(bodies) + 1)))
        for number, body in enumerate(bodies, 1):
            content["ppt/slides/slide" + str(number) + ".xml"] = deck_fixtures.slide("", body, hidden=hidden)
        return verifier.verify(self.write(deck_fixtures.typed(content), "deck.pptx"))

    def book(self, rows=None, calculated=True, names=None, workbook_rels=None):
        parts = sheet_fixtures.package_parts()
        if rows is not None:
            parts["xl/worksheets/sheet1.xml"] = grid(rows)
        if calculated:
            parts["xl/workbook.xml"] = parts["xl/workbook.xml"].replace(' fullCalcOnLoad="1"', "")
        if names is not None:
            parts["xl/workbook.xml"] = parts["xl/workbook.xml"].replace("Model!$A$1", names)
        if workbook_rels:
            parts["xl/_rels/workbook.xml.rels"] = sheet_fixtures.relationships(
                [("rId1", "worksheet", "worksheets/sheet1.xml", None), *workbook_rels])
        return verifier.verify(self.write(sheet_fixtures.add_content_types(parts), "book.xlsx"))

    # Word

    def test_clean_document_passes_and_names_what_it_did_not_check(self):
        report = self.word(word_fixtures.paragraph("Plain text"))
        self.assertEqual("pass", report["verdict"])
        self.assertEqual([], report["findings"])
        self.assertIn("OOXML schema validity", report["not_checked"])
        self.assertRegex(report["notice"], "not evidence of layout")

    def test_image_alt_text_is_required_unless_described_or_decorative(self):
        self.assertIn("docx.alt-text-missing", rules_of(self.word(picture())))
        self.assertNotIn("docx.alt-text-missing", rules_of(self.word(picture(descr="Revenue by quarter"))))
        self.assertNotIn("docx.alt-text-missing", rules_of(self.word(picture(decorative=True))))

    def test_heading_levels_must_not_skip(self):
        extra = {"word/styles.xml": STYLES}
        skipped = self.word(styled("Intro", "Heading1") + styled("Detail", "Heading3"), extra)
        self.assertIn("docx.heading-skip", rules_of(skipped))
        ordered = self.word(styled("Intro", "Heading1") + styled("Detail", "Heading2"), extra)
        self.assertNotIn("docx.heading-skip", rules_of(ordered))
        outline = self.word('<w:p><w:pPr><w:outlineLvl w:val="2"/></w:pPr><w:r><w:t>Deep</w:t></w:r></w:p>')
        self.assertIn("docx.heading-skip", rules_of(outline))

    def test_unresolved_revisions_and_comments_are_reported(self):
        report = self.word('<w:p><w:ins w:id="1" w:author="A"><w:r><w:t>New</w:t></w:r></w:ins></w:p>')
        self.assertIn("docx.tracked-changes", rules_of(report))
        self.assertEqual("warnings", report["verdict"])

    def test_internal_link_needs_its_bookmark(self):
        link = '<w:p><w:hyperlink w:anchor="Results"><w:r><w:t>See results</w:t></w:r></w:hyperlink></w:p>'
        broken = self.word(link)
        self.assertIn("docx.broken-anchor", rules_of(broken))
        self.assertEqual("fail", broken["verdict"])
        target = '<w:p><w:bookmarkStart w:id="0" w:name="Results"/><w:r><w:t>Results</w:t></w:r><w:bookmarkEnd w:id="0"/></w:p>'
        self.assertNotIn("docx.broken-anchor", rules_of(self.word(link + target)))

    def test_empty_body_paragraphs_count_but_empty_table_cells_do_not(self):
        spacing = word_fixtures.paragraph("A") + "<w:p/>" * 3 + word_fixtures.paragraph("B")
        self.assertIn("docx.empty-paragraph-spacing", rules_of(self.word(spacing)))
        cells = "<w:tbl><w:tr>" + "<w:tc><w:p/></w:tc>" * 4 + "</w:tr></w:tbl>"
        self.assertNotIn("docx.empty-paragraph-spacing", rules_of(self.word(cells)))

    # PowerPoint

    def test_titled_slide_without_defects_passes(self):
        self.assertEqual("pass", self.deck(title())["verdict"])

    def test_slide_rules(self):
        report = self.deck(slide_picture() + positioned(11_000_000, 2_000_000) + EMPTY_PLACEHOLDER)
        found = rules_of(report)
        for rule in ("pptx.alt-text-missing", "pptx.off-slide", "pptx.empty-placeholder", "pptx.title-missing"):
            self.assertIn(rule, found)
        fixes = {item["rule"]: item["fix"] for item in report["findings"]}
        self.assertEqual("safe", fixes["pptx.empty-placeholder"])
        self.assertEqual("content", fixes["pptx.alt-text-missing"])

    def test_described_picture_and_inside_object_are_clean(self):
        found = rules_of(self.deck(title() + slide_picture("Team photo") + positioned(1_000_000, 2_000_000)))
        self.assertFalse(found & {"pptx.alt-text-missing", "pptx.off-slide"})

    def test_hidden_slide_is_reported(self):
        self.assertIn("pptx.hidden-slide", rules_of(self.deck(title(), hidden=True)))

    # Excel

    def test_native_chart_sheet_is_verified_without_worksheet_cells(self):
        parts = sheet_fixtures.package_parts()
        parts["xl/_rels/workbook.xml.rels"] = sheet_fixtures.relationships([
            ("rId1", "chartsheet", "chartsheets/sheet1.xml", None)])
        del parts["xl/worksheets/sheet1.xml"]
        parts["xl/chartsheets/sheet1.xml"] = (
            '<chartsheet xmlns="' + sheet_fixtures.SHEET_NS + '"/>')
        path = self.write(sheet_fixtures.add_content_types(parts), "chart-sheet.xlsx")
        report = verifier.verify(path)
        self.assertNotEqual("fail", report["verdict"], report)

    def test_ref_error_text_in_formula_and_name_is_not_a_broken_reference(self):
        report = self.book({1: formula("B1", 'COUNTIF(A1:A10,"#REF!")')},
                           names='"#REF!"')
        self.assertNotIn("xlsx.ref-error-in-formula", rules_of(report))
        self.assertNotIn("xlsx.broken-name", rules_of(report))

    def test_uncalculated_workbook_is_reported_as_safe_to_fix(self):
        report = self.book(calculated=False)
        self.assertIn("xlsx.not-calculated", rules_of(report))
        self.assertEqual({"safe"}, {item["fix"] for item in report["findings"] if item["rule"] == "xlsx.not-calculated"})

    def test_error_results_and_deleted_references_fail(self):
        report = self.book({1: '<c r="A1" t="e"><f>1/0</f><v>#DIV/0!</v></c>' + formula("B1", "#REF!+1")},
                           names="#REF!$A$1")
        self.assertTrue({"xlsx.cached-error", "xlsx.ref-error-in-formula", "xlsx.broken-name"} <= rules_of(report))
        self.assertEqual("fail", report["verdict"])
        literal = self.book({1: '<c r="A1" t="e"><v>#N/A</v></c>'})
        self.assertIn("xlsx.literal-error", rules_of(literal))

    def test_inconsistent_formula_is_found_in_relative_form(self):
        rows = {1: formula("B1", "A1+C1"), 2: formula("B2", "A2+D2"), 3: formula("B3", "A3+C3")}
        report = self.book(rows)
        flagged = [item["location"] for item in report["findings"] if item["rule"] == "xlsx.inconsistent-formula"]
        self.assertEqual(["Model!B2"], flagged)

    def test_shared_and_absolute_formulas_are_consistent(self):
        shared = {1: formula("B1", "A1+$C$1", attributes=' t="shared" ref="B1:B3" si="0"'),
                  2: formula("B2", "", attributes=' t="shared" si="0"'),
                  3: formula("B3", "", attributes=' t="shared" si="0"')}
        self.assertNotIn("xlsx.inconsistent-formula", rules_of(self.book(shared)))
        absolute = {1: formula("B1", "A1*$C$1"), 2: formula("B2", "A2*$C$1"), 3: formula("B3", "A3*$C$1")}
        self.assertNotIn("xlsx.inconsistent-formula", rules_of(self.book(absolute)))

    def test_hardcoded_constants_ignore_arguments_strings_and_references(self):
        report = self.book({1: formula("A1", "B1*1.05")})
        constant = next(item for item in report["findings"] if item["rule"] == "xlsx.hardcoded-constant")
        self.assertIn("1.05", constant["message"])
        for clean in ("ROUND(B1,2)", "B1*1", '"2"&B10', "SUM(B2:B12)", "Sheet2!B1+$C$10", "'Q 2'!B1+1"):
            with self.subTest(formula=clean):
                self.assertNotIn("xlsx.hardcoded-constant", rules_of(self.book({1: formula("A1", clean)})))

    def test_external_dependency_is_reported_but_hyperlinks_are_not(self):
        linked = self.book(workbook_rels=[("rId9", "externalLink", "file:///C:/other.xlsx", "External")])
        self.assertIn("package.external-link", rules_of(linked))
        linked_web = self.book(workbook_rels=[("rId9", "hyperlink", "https://example.invalid", "External")])
        self.assertNotIn("package.external-link", rules_of(linked_web))

    # Report contract

    def test_unreadable_package_fails_with_its_inspector_error(self):
        broken = self.directory / "broken.xlsx"
        broken.write_bytes(b"not a zip")
        report = verifier.verify(broken)
        self.assertFalse(report["package_valid"])
        self.assertIn("package.invalid", rules_of(report))

    def test_findings_beyond_the_cap_are_counted_not_listed(self):
        rows = {n: formula("A" + str(n), "B" + str(n) + "*1.5") for n in range(1, 6)}
        parts = sheet_fixtures.package_parts()
        parts["xl/worksheets/sheet1.xml"] = grid(rows)
        path = self.write(sheet_fixtures.add_content_types(parts), "many.xlsx")
        report = verifier.verify(path, max_per_rule=2)
        self.assertEqual(5, report["rules"]["xlsx.hardcoded-constant"])
        listed = [item for item in report["findings"] if item["rule"] == "xlsx.hardcoded-constant"]
        self.assertEqual(2, len(listed))
        self.assertEqual(3, report["omitted"]["xlsx.hardcoded-constant"])

    def test_cli_exit_codes_and_source_is_never_written(self):
        clean = self.write(word_fixtures.add_content_types(word_fixtures.package_parts()), "clean.docx")
        failing = self.write(sheet_fixtures.add_content_types(
            {**sheet_fixtures.package_parts(), "xl/worksheets/sheet1.xml": grid({1: formula("A1", "#REF!")})}),
            "failing.xlsx")
        before = {path: path.read_bytes() for path in (clean, failing)}
        unsupported = self.directory / "notes.txt"
        unsupported.write_text("x", encoding="utf-8")
        for path, expected in ((clean, 0), (failing, 1), (unsupported, 2), (self.directory / "absent.docx", 2)):
            stream = io.StringIO()
            with self.subTest(path=path.name), contextlib.redirect_stdout(stream):
                status = verifier.main([str(path)])
            self.assertEqual(expected, status)
            self.assertEqual(verifier.SCHEMA, json.loads(stream.getvalue())["schema"])
        for path, data in before.items():
            self.assertEqual(data, path.read_bytes())

    def test_templates_are_verified_as_their_format(self):
        parts = word_fixtures.add_content_types(
            word_fixtures.package_parts(),
            "application/vnd.openxmlformats-officedocument.wordprocessingml.template.main+xml")
        report = verifier.verify(self.write(parts, "base.dotx"), officecli=False)
        self.assertEqual(("docx", "pass"), (report["format"], report["verdict"]), report["findings"])
        deck = deck_fixtures.typed(
            deck_fixtures.parts(("slide1.xml",)),
            "application/vnd.openxmlformats-officedocument.presentationml.template.main+xml")
        report = verifier.verify(self.write(deck, "base.potx"), officecli=False)
        self.assertEqual("pptx", report["format"])
        self.assertTrue(report["package_valid"], report["findings"])

    def test_officecli_runs_only_when_present_and_owns_the_schema_check(self):
        clean = self.write(word_fixtures.add_content_types(word_fixtures.package_parts()), "clean.docx")
        absent = verifier.verify(clean, officecli=str(self.directory / "missing" / "officecli.exe"))
        self.assertIsNone(absent["checkers"]["officecli"])
        self.assertIn(verifier.SCHEMA_CHECK, absent["not_checked"])
        fake = self.directory / ("officecli.cmd" if os.name == "nt" else "officecli")
        script = ("@echo off\r\nif \"%1\"==\"validate\" (echo {\"success\": false, \"warnings\": "
                  "[{\"message\": \"Found 1 validation error(s):\"}, {\"message\": \"[Schema] bad child\"}, "
                  "{\"message\": \"Part: /ppt/presentation.xml\"}]}) else (echo {\"success\": true, \"data\": "
                  "{\"count\": 1, \"issues\": [{\"code\": \"text_overflow\", \"path\": \"/slide[2]/shape[3]\", "
                  "\"message\": \"Text overflows its box\"}]}})\r\n") if os.name == "nt" else (
                  "#!/bin/sh\nif [ \"$1\" = validate ]; then echo '{\"success\": false, \"warnings\": "
                  "[{\"message\": \"Found 1 validation error(s):\"}, {\"message\": \"[Schema] bad child\"}, "
                  "{\"message\": \"Part: /ppt/presentation.xml\"}]}'; else echo '{\"success\": true, \"data\": "
                  "{\"count\": 1, \"issues\": [{\"code\": \"text_overflow\", \"path\": \"/slide[2]/shape[3]\", "
                  "\"message\": \"Text overflows its box\"}]}}'; fi\n")
        fake.write_text(script, encoding="utf-8")
        fake.chmod(0o755)
        report = verifier.verify(clean, officecli=str(fake))
        self.assertEqual(str(fake), report["checkers"]["officecli"])
        self.assertNotIn(verifier.SCHEMA_CHECK, report["not_checked"])
        self.assertEqual("fail", report["verdict"])
        rules = {item["rule"]: item for item in report["findings"]}
        self.assertIn("[Schema] bad child", rules["package.schema"]["message"])
        self.assertEqual(("warning", "/slide[2]/shape[3]", "review"),
                         (rules["officecli.text_overflow"]["severity"], rules["officecli.text_overflow"]["location"],
                          rules["officecli.text_overflow"]["fix"]))
        template = self.write(word_fixtures.add_content_types(
            word_fixtures.package_parts(),
            "application/vnd.openxmlformats-officedocument.wordprocessingml.template.main+xml"), "t.dotx")
        skipped = verifier.verify(template, officecli=str(fake))
        self.assertIn(verifier.SCHEMA_CHECK, skipped["not_checked"], "OfficeCLI reads no templates")
        self.assertFalse([item for item in skipped["findings"] if item["rule"].startswith("package.schema")])

    def test_reference_lists_exactly_the_rules_the_checker_emits(self):
        emitted = set(re.findall(r'finding\("([a-z]+\.[a-z-]+)"', SCRIPT.read_text(encoding="utf-8")))
        documented = set(re.findall(r"^\| `([a-z]+\.[a-z-]+)` \|", RULES.read_text(encoding="utf-8"), re.M))
        self.assertEqual(emitted, documented)
        script = SCRIPT.read_text(encoding="utf-8")
        for rule, fix in re.findall(r"^\| `([a-z]+\.[a-z-]+)` \| \w+ \| (\w+) \|", RULES.read_text(encoding="utf-8"), re.M):
            with self.subTest(rule=rule):
                self.assertRegex(script, r'finding\("' + re.escape(rule) + r'"(?:.|\n)*?"' + fix + r'"\)')


class IntegrityEntryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plugin = load_plugin(OFFICE)
        cls.temporary = tempfile.TemporaryDirectory(dir=str(REPO_ROOT) if os.name == "nt" else None)
        cls.packages = {}
        cls.entries = office_entries.render_entries(cls.temporary.name, ("verify", "fix"))
        for host in HOSTS:
            package = Path(cls.temporary.name) / host / "office"
            render_plugin(cls.plugin, load_adapter(REPO_ROOT / "adapters", host), package,
                          adapters_root=REPO_ROOT / "adapters")
            cls.packages[host] = package

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def test_verify_and_fix_ship_on_every_host_and_load_the_integrity_method(self):
        self.assertIn("integrity", self.plugin.components.skills)
        # The verify and fix entries are `daodan` workflows; office owns the method.
        self.assertTrue(
            {"verify", "fix"} <= set(load_plugin(office_entries.DAODAN).components.workflows)
        )
        self.assertEqual(set(self.plugin.components.workflows), set())
        for host, package in self.packages.items():
            with self.subTest(host=host):
                for relative in ("skills/integrity/SKILL.md", "skills/integrity/scripts/office_verify.py",
                                 "skills/integrity/references/rules.md"):
                    self.assertTrue((package / relative).is_file(), relative)
                verify = " ".join(loaded_instruction_text(
                    self, self.entries[host] / ENTRY_PATHS[host].format(name="verify"), host).split())
                fix = " ".join(loaded_instruction_text(
                    self, self.entries[host] / ENTRY_PATHS[host].format(name="fix"), host).split())
                for text in (verify, fix):
                    self.assertIn("`office:integrity`", text)
                self.assertIn("Never write to it", verify)
                self.assertIn("The source is never modified", fix)
                self.assertIn("no new finding appeared", fix)

    def test_method_keeps_static_limits_and_candidate_only_repairs(self):
        method = " ".join((OFFICE / "skills/integrity/SKILL.md").read_text(encoding="utf-8").split())
        self.assertIn("A `pass` is never a visual or calculation verdict", method)
        self.assertIn("never overwrite the source", method)
        self.assertIn("Never invent facts", method)
        self.assertIn("no new finding may appear", method)


if __name__ == "__main__":
    unittest.main()
