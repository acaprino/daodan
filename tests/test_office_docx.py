"""Word native structure checks and independent preservation failure modes."""

import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "plugins/office/skills/docx/scripts/docx_inspect.py"
SPEC = importlib.util.spec_from_file_location("office_docx_inspect", SCRIPT)
docx = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(docx)
WORD_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PACKAGE_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
TYPE_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
MAIN_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"


def relationships(items):
    return '<Relationships xmlns="' + PACKAGE_REL_NS + '">' + "".join(
        '<Relationship Id="' + rel_id + '" Type="' + REL_NS + "/" + kind + '" Target="' + target + '"'
        + (' TargetMode="' + mode + '"' if mode else "") + "/>"
        for rel_id, kind, target, mode in items
    ) + "</Relationships>"


def story(kind, body):
    return '<w:' + kind + ' xmlns:w="' + WORD_NS + '" xmlns:r="' + REL_NS + '">' + body + "</w:" + kind + ">"


def paragraph(text="Report", bold=False):
    return "<w:p><w:r>" + ("<w:rPr><w:b/></w:rPr>" if bold else "") + "<w:t>" + text + "</w:t></w:r></w:p>"


def package_parts(body=None, related=True):
    if body is None:
        body = paragraph() + '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1440"/></w:sectPr>'
    parts = {"word/document.xml": story("document", "<w:body>" + body + "</w:body>")}
    if related:
        parts["_rels/.rels"] = relationships([("rId1", "officeDocument", "word/document.xml", None)])
    return parts


def add_content_types(parts, main_type=MAIN_TYPE):
    declarations = '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    declarations += '<Default Extension="xml" ContentType="application/xml"/><Default Extension="bin" ContentType="application/octet-stream"/>'
    declarations += '<Default Extension="png" ContentType="image/png"/>'
    declarations += '<Override PartName="/word/document.xml" ContentType="' + main_type + '"/>'
    return {"[Content_Types].xml": '<Types xmlns="' + TYPE_NS + '">' + declarations + "</Types>", **parts}


class WordInspectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)

    def write(self, parts=None, filename="document.docx", main_type=MAIN_TYPE, content_types=True):
        destination = self.directory / filename
        if parts is None:
            parts = package_parts()
        if content_types:
            parts = add_content_types(parts, main_type)
        with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
            for name, data in parts.items():
                archive.writestr(name, data)
        return destination

    def inspect(self, parts=None, **kwargs):
        return docx.inspect_document(self.write(parts, **kwargs))

    def compare(self, before, after):
        return docx.compare_documents(self.write(before, "before.docx"), self.write(after, "after.docx"))

    def test_native_text_runs_and_page_layout(self):
        result = self.inspect()
        self.assertTrue(result["valid"], result["errors"])
        self.assertEqual(MAIN_TYPE, result["main_content_type"])
        self.assertEqual("Report", result["stories"][0]["paragraphs"][0]["text"])
        props = result["stories"][0]["sections"][0]["properties"]
        self.assertEqual("11906", props[0]["attributes"]["{" + WORD_NS + "}w"])
        self.assertIn("no pages were rendered", result["layout_verification"])

    def test_formula_like_text_is_literal_and_never_a_word_field(self):
        result = self.inspect(package_parts(paragraph("=SUM(A1:A9)")))
        self.assertTrue(result["valid"], result["errors"])
        self.assertEqual("=SUM(A1:A9)", result["stories"][0]["paragraphs"][0]["text"])
        self.assertEqual([], result["stories"][0]["fields"])

    def test_lost_header_footer_and_notes_are_native_story_deltas(self):
        before = package_parts()
        before["word/_rels/document.xml.rels"] = relationships([
            ("header", "header", "header1.xml", None), ("footer", "footer", "footer1.xml", None),
            ("notes", "footnotes", "footnotes.xml", None), ("end", "endnotes", "endnotes.xml", None),
        ])
        before.update({"word/header1.xml": story("hdr", paragraph("Confidential")), "word/footer1.xml": story("ftr", paragraph("Page 1")),
                       "word/footnotes.xml": story("footnotes", '<w:footnote w:id="1">' + paragraph("Source") + '</w:footnote>'),
                       "word/endnotes.xml": story("endnotes", '<w:endnote w:id="1">' + paragraph("End source") + '</w:endnote>')})
        result = self.compare(before, package_parts())
        self.assertTrue(result["valid"], result["after"]["errors"])
        self.assertEqual(["word/endnotes.xml", "word/footer1.xml", "word/footnotes.xml", "word/header1.xml"], result["removed_story_parts"])
        self.assertTrue(any(item["before"] == "Confidential" and item["after"] is None for item in result["text_changes"]))
        self.assertEqual(["word/endnotes.xml", "word/footnotes.xml"], result["before"]["preservation_sensitive"]["footnotes_or_endnotes"])

    def test_content_controls_and_internal_hyperlinks_require_preservation_before_editing(self):
        body = '<w:sdt><w:sdtPr><w:tag w:val="binding"/></w:sdtPr><w:sdtContent>' + paragraph("Value") + '</w:sdtContent></w:sdt>'
        body += '<w:p><w:hyperlink w:anchor="section"><w:r><w:t>Jump</w:t></w:r></w:hyperlink></w:p>'
        result = self.compare(package_parts(body), package_parts(paragraph("Value") + paragraph("Jump")))
        self.assertEqual([], result["text_changes"])
        for feature in ("content_controls", "hyperlinks"):
            self.assertEqual(["word/document.xml"], result["before"]["preservation_sensitive"][feature])
            self.assertEqual(["word/document.xml"], result[feature + "_changed_parts"])

    def test_table_flattening_is_detected_even_when_paragraph_text_survives(self):
        body = paragraph("Same")
        result = self.compare(package_parts("<w:tbl><w:tr><w:tc>" + body + "</w:tc></w:tr></w:tbl>"), package_parts(body))
        self.assertTrue(result["valid"])
        self.assertEqual([], result["text_changes"])
        self.assertEqual(["word/document.xml"], result["tables_changed_parts"])

    def test_run_formatting_loss_is_detected_with_unchanged_text(self):
        result = self.compare(package_parts(paragraph("Same", bold=True)), package_parts(paragraph("Same")))
        self.assertEqual([], result["text_changes"])
        self.assertEqual(1, len(result["formatting_changes"]))
        self.assertEqual(1, len(result["native_paragraph_changes"]))

    def test_mixed_runs_are_not_equated_with_one_flat_run(self):
        mixed = '<w:p><w:r><w:rPr><w:b/></w:rPr><w:t>Head</w:t></w:r><w:r><w:t>tail</w:t></w:r></w:p>'
        result = self.compare(package_parts(mixed), package_parts(paragraph("Headtail")))
        self.assertEqual([], result["text_changes"])
        self.assertEqual(1, len(result["formatting_changes"]))

    def test_tracked_change_acceptance_is_an_explicit_delta(self):
        revised = '<w:p><w:ins w:id="7" w:author="Editor"><w:r><w:t>Same</w:t></w:r></w:ins></w:p>'
        result = self.compare(package_parts(revised), package_parts(paragraph("Same")))
        self.assertEqual([], result["text_changes"])
        self.assertEqual(["word/document.xml"], result["revisions_changed_parts"])
        self.assertIn("revisions", result["before"]["preservation_sensitive"])

    def test_stored_field_result_does_not_prove_updated_field_or_preserved_instruction(self):
        field = '<w:p><w:fldSimple w:instr="PAGE"><w:r><w:t>0</w:t></w:r></w:fldSimple></w:p>'
        result = self.compare(package_parts(field), package_parts(paragraph("0")))
        self.assertEqual([], result["text_changes"])
        self.assertEqual(["word/document.xml"], result["fields_changed_parts"])
        self.assertIn("not updated", result["before"]["field_verification"])
        self.assertEqual("PAGE", result["before"]["stories"][0]["fields"][0]["attributes"]["{" + WORD_NS + "}instr"])

    def test_complex_field_instructions_and_deleted_text_are_inventoried(self):
        body = '<w:p><w:r><w:fldChar w:fldCharType="begin"/><w:instrText> TOC \\o "1-3" </w:instrText><w:fldChar w:fldCharType="end"/></w:r><w:del w:id="2"><w:r><w:delText>removed</w:delText></w:r></w:del></w:p>'
        result = self.inspect(package_parts(body))
        fields = result["stories"][0]["fields"]
        self.assertEqual(3, len(fields))
        self.assertEqual(' TOC \\o "1-3" ', fields[1]["instruction_text"])
        self.assertEqual("removed", result["stories"][0]["paragraphs"][0]["text"])

    def test_comments_and_math_preservation_are_explicit(self):
        math_ns = "http://schemas.openxmlformats.org/officeDocument/2006/math"
        body = '<w:p><w:commentRangeStart w:id="1"/><m:oMath xmlns:m="' + math_ns + '"><m:r><m:t>x+1</m:t></m:r></m:oMath></w:p>'
        before = package_parts(body)
        before["word/comments.xml"] = story("comments", '<w:comment w:id="1" w:author="Editor">' + paragraph("Check") + '</w:comment>')
        before["word/_rels/document.xml.rels"] = relationships([("c", "comments", "comments.xml", None)])
        result = self.compare(before, package_parts("<w:p/>"))
        self.assertIn("word/document.xml", result["math_changed_parts"])
        self.assertIn("word/comments.xml", result["comments_changed_parts"])
        self.assertIn("math", result["before"]["preservation_sensitive"])

    def test_styles_and_objects_are_not_lost_silently(self):
        before = package_parts()
        before["word/styles.xml"] = story("styles", '<w:style w:styleId="Title" w:type="paragraph"><w:name w:val="Title"/></w:style>')
        before["word/_rels/document.xml.rels"] = relationships([("i", "image", "media/image.png", None), ("o", "oleObject", "embeddings/object.bin", None)])
        before["word/media/image.png"], before["word/embeddings/object.bin"] = b"image data", b"object data"
        result = self.compare(before, package_parts())
        self.assertTrue(result["styles_changed"])
        self.assertTrue(result["objects_changed"])
        self.assertIn("word/media/image.png", result["removed_parts"])
        self.assertIn("embedded_objects", result["before"]["preservation_sensitive"])

    def test_external_targets_macros_and_metadata_are_inventoried_without_execution(self):
        parts = package_parts()
        parts["word/_rels/document.xml.rels"] = relationships([("url", "hyperlink", "https://example.invalid/", "External")])
        parts.update({"word/vbaProject.bin": b"macro", "docProps/core.xml": '<coreProperties/>', "word/vendor.bin": b"unknown"})
        result = self.inspect(parts, main_type="application/vnd.ms-word.document.macroEnabled.main+xml")
        self.assertTrue(result["valid"], result["errors"])
        self.assertIn("macros", result["preservation_sensitive"])
        self.assertIn("document_metadata", result["preservation_sensitive"])
        self.assertIn("word/vendor.bin", result["preservation_sensitive"]["unknown_parts"])
        self.assertEqual("https://example.invalid/", result["external_relationships"][0]["target"])

    def test_changed_image_payload_is_detected_with_identical_relationships(self):
        before = package_parts()
        before["word/_rels/document.xml.rels"] = relationships([("i", "image", "media/image.png", None)])
        before["word/media/image.png"] = b"original image"
        result = self.compare(before, {**before, "word/media/image.png": b"replacement image"})
        self.assertTrue(result["objects_changed"])
        self.assertEqual(["word/media/image.png"], result["object_part_changes"])

    def test_alt_chunk_is_sensitive_even_if_its_filename_is_generic(self):
        parts = package_parts('<w:altChunk r:id="chunk"/>')
        parts["word/_rels/document.xml.rels"] = relationships([("chunk", "aFChunk", "chunk1.xml", None)])
        parts["word/chunk1.xml"] = '<html/>'
        result = self.inspect(parts)
        self.assertTrue(result["valid"], result["errors"])
        self.assertIn("word/document.xml", result["preservation_sensitive"]["imported_content"])

    def test_empty_story_or_zero_deltas_is_not_semantic_or_layout_proof(self):
        result = self.compare(package_parts(""), package_parts(""))
        self.assertTrue(result["valid"])
        self.assertEqual([], result["text_changes"])
        self.assertEqual([], result["changed_parts"])
        self.assertIn("do not establish semantic preservation or layout fidelity", result["notice"])

    def test_strict_namespace_and_relations_are_supported(self):
        parts = {name: text.replace(WORD_NS, "http://purl.oclc.org/ooxml/wordprocessingml/main").replace(REL_NS, "http://purl.oclc.org/ooxml/officeDocument/relationships") for name, text in package_parts().items()}
        result = self.inspect(parts)
        self.assertTrue(result["valid"], result["errors"])
        self.assertEqual("Report", result["stories"][0]["paragraphs"][0]["text"])

    def test_missing_or_wrong_main_relationship_is_invalid(self):
        for parts in (package_parts(related=False), {**package_parts(), "_rels/.rels": relationships([("rId1", "notOffice", "word/document.xml", None)])}):
            with self.subTest(parts=parts):
                result = self.inspect(parts)
                self.assertFalse(result["valid"])
                self.assertTrue(any("officeDocument relationship" in error for error in result["errors"]))

    def test_spreadsheet_or_wrong_word_namespace_and_main_type_are_invalid(self):
        parts = package_parts()
        for invalid_root in ('<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"/>', story("document", "<w:body/>").replace(WORD_NS, "urn:unrecognized-word")):
            with self.subTest(root=invalid_root):
                result = self.inspect({**parts, "word/document.xml": invalid_root})
                self.assertFalse(result["valid"])
                self.assertTrue(any("Word document root" in error for error in result["errors"]))
        result = self.inspect(main_type="application/xml")
        self.assertFalse(result["valid"])
        self.assertTrue(any("main content type" in error for error in result["errors"]))

    def test_missing_header_reference_and_wrong_header_namespace_are_invalid(self):
        body = '<w:sectPr><w:headerReference w:type="default" r:id="missing"/></w:sectPr>'
        result = self.inspect(package_parts(body))
        self.assertFalse(result["valid"])
        self.assertTrue(any("Word reference relationship" in error for error in result["errors"]))
        parts = package_parts()
        parts["word/_rels/document.xml.rels"] = relationships([("h", "header", "header1.xml", None)])
        parts["word/header1.xml"] = '<hdr xmlns="urn:unknown"/>'
        result = self.inspect(parts)
        self.assertFalse(result["valid"])
        self.assertTrue(any("story relationship" in error for error in result["errors"]))

    def test_missing_targets_invalid_xml_and_dtd_are_explicit_failures(self):
        cases = []
        parts = package_parts()
        parts["word/_rels/document.xml.rels"] = relationships([("h", "header", "missing.xml", None)])
        cases.append((parts, "Missing relationship target"))
        cases.append(({**package_parts(), "word/styles.xml": "<broken>"}, "Invalid XML"))
        cases.append(({**package_parts(), "word/styles.xml": '<!DOCTYPE x [<!ENTITY y "expanded">]><x>&y;</x>'}, "DTD or entity"))
        for parts, message in cases:
            with self.subTest(message=message):
                result = self.inspect(parts)
                self.assertFalse(result["valid"])
                self.assertTrue(any(message in error for error in result["errors"]))

    def test_deep_xml_and_bounded_package_reading_do_not_escape_json_error_contract(self):
        destination = self.write(package_parts('<w:p>' + '<w:r>' * 1500 + '<w:t>Deep</w:t>' + '</w:r>' * 1500 + '</w:p>'))
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            status = docx.main(["inspect", str(destination)])
        self.assertEqual(1, status)
        self.assertFalse(json.loads(stream.getvalue())["valid"])
        destination = self.write()
        with patch.object(docx.package, "MAX_PART_BYTES", 8):
            result = docx.inspect_document(destination)
        self.assertFalse(result["valid"])
        self.assertIn("byte limit", result["errors"][0])

    def test_cli_handles_malformed_encoding_non_zip_and_invalid_comparison(self):
        before = self.write(filename="before.docx")
        bad = self.write({**package_parts(), "word/styles.xml": b'<?xml version="1.0" encoding="no-such-encoding"?><styles/>'}, filename="bad.docx")
        for args in (["inspect", str(bad)], ["compare", str(before), str(bad)]):
            stream = io.StringIO()
            with contextlib.redirect_stdout(stream):
                status = docx.main(args)
            self.assertEqual(1, status)
            self.assertFalse(json.loads(stream.getvalue())["valid"])
        bad.write_bytes(b"not a ZIP")
        self.assertFalse(docx.inspect_document(bad)["valid"])

    def test_missing_content_types_traversal_and_missing_body_are_invalid(self):
        self.assertFalse(self.inspect(content_types=False)["valid"])
        self.assertFalse(self.inspect({"../outside.xml": "<x/>"})["valid"])
        self.assertFalse((self.directory.parent / "outside.xml").exists())
        result = self.inspect({**package_parts(), "word/document.xml": story("document", "")})
        self.assertFalse(result["valid"])
        self.assertTrue(any("body" in error for error in result["errors"]))

    def test_inspection_comparison_do_not_mutate_and_deltas_are_not_automatic_failure(self):
        before = self.write(package_parts(paragraph("Same", bold=True)), "before.docx")
        after = self.write(package_parts(paragraph("Same")), "after.docx")
        original = before.read_bytes(), after.read_bytes()
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            status = docx.main(["compare", str(before), str(after)])
        self.assertEqual(0, status)
        self.assertTrue(json.loads(stream.getvalue())["formatting_changes"])
        self.assertEqual(original, (before.read_bytes(), after.read_bytes()))


if __name__ == "__main__":
    unittest.main()
