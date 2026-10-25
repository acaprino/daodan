"""Native spreadsheet package checks, preservation deltas and formula cache limits."""

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
SCRIPT = REPO_ROOT / "plugins/office/skills/xlsx/scripts/xlsx_inspect.py"
SPEC = importlib.util.spec_from_file_location("office_xlsx_inspect", SCRIPT)
xlsx = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(xlsx)

SHEET_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
DOCUMENT_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PACKAGE_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
TYPE_NS = "http://schemas.openxmlformats.org/package/2006/content-types"


def relationships(items):
    body = "".join(
        '<Relationship Id="' + rel_id + '" Type="' + DOCUMENT_REL_NS + "/" + kind
        + '" Target="' + target + '"' + (' TargetMode="' + mode + '"' if mode else "") + "/>"
        for rel_id, kind, target, mode in items
    )
    return '<Relationships xmlns="' + PACKAGE_REL_NS + '">' + body + "</Relationships>"


def sheet(cells=None, extra=""):
    if cells is None:
        cells = '<c r="A1"><v>2</v></c><c r="B1"><f>A1*2</f><v>4</v></c>'
    return (
        '<worksheet xmlns="' + SHEET_NS + '"><dimension ref="A1:B1"/>'
        '<sheetData><row r="1">' + cells + "</row></sheetData>" + extra + "</worksheet>"
    )


def package_parts(cells=None, chart=False):
    parts = {
        "_rels/.rels": relationships([("rId1", "officeDocument", "xl/workbook.xml", None)]),
        "xl/workbook.xml": (
            '<workbook xmlns="' + SHEET_NS + '" xmlns:r="' + DOCUMENT_REL_NS + '">'
            '<sheets><sheet name="Model" sheetId="1" r:id="rId1"/></sheets>'
            '<definedNames><definedName name="Input">Model!$A$1</definedName></definedNames>'
            '<calcPr calcId="12345" fullCalcOnLoad="1"/></workbook>'
        ),
        "xl/_rels/workbook.xml.rels": relationships([("rId1", "worksheet", "worksheets/sheet1.xml", None)]),
        "xl/worksheets/sheet1.xml": sheet(cells),
        "xl/styles.xml": '<styleSheet xmlns="' + SHEET_NS + '"><cellXfs count="1"><xf/></cellXfs></styleSheet>',
    }
    if chart:
        parts["xl/charts/chart1.xml"] = (
            '<c:chartSpace xmlns:c="http://schemas.openxmlformats.org/drawingml/2006/chart">'
            "<c:chart/></c:chartSpace>"
        )
        parts["xl/worksheets/_rels/sheet1.xml.rels"] = relationships([
            ("rIdChart", "chart", "../charts/chart1.xml", None),
        ])
    return parts


def add_content_types(parts):
    declarations = (
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Default Extension="bin" ContentType="application/octet-stream"/>'
        '<Default Extension="vml" ContentType="application/vnd.openxmlformats-officedocument.vmlDrawing"/>'
    )
    return {"[Content_Types].xml": '<Types xmlns="' + TYPE_NS + '">' + declarations + "</Types>", **parts}


class WorkbookInspectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)

    def write(self, parts=None, filename="workbook.xlsx", content_types=True):
        destination = self.directory / filename
        if parts is None:
            parts = package_parts()
        if content_types:
            parts = add_content_types(parts)
        with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
            for name, data in parts.items():
                archive.writestr(name, data)
        return destination

    def inspect(self, parts=None):
        return xlsx.inspect_workbook(self.write(parts))

    def test_native_formulas_and_names_are_inspected_without_evaluation(self):
        result = self.inspect()
        self.assertTrue(result["valid"], result["errors"])
        self.assertEqual(1, result["formula_count"])
        self.assertEqual("A1*2", result["sheets"][0]["formulas"]["B1"]["text"])
        self.assertEqual("4", result["sheets"][0]["formulas"]["B1"]["cache"]["value"])
        self.assertEqual("Model!$A$1", result["defined_names"][0]["text"])
        self.assertEqual("1", result["calculation_properties"]["fullCalcOnLoad"])
        self.assertIn("unverified", result["cache_verification"])

    def test_zero_missing_and_empty_formula_caches_are_distinct(self):
        result = self.inspect(package_parts(
            '<c r="A1"><f>1-1</f><v>0</v></c>'
            '<c r="B1"><f>SUM(A1)</f></c>'
            '<c r="C1"><f>SUM(A1)</f><v/></c>'
        ))
        self.assertTrue(result["valid"], result["errors"])
        formulas = result["sheets"][0]["formulas"]
        self.assertEqual({"present": True, "value": "0", "type": "n"}, formulas["A1"]["cache"])
        self.assertEqual({"present": False, "value": None, "type": "n"}, formulas["B1"]["cache"])
        self.assertEqual({"present": True, "value": None, "type": "n"}, formulas["C1"]["cache"])
        self.assertEqual(1, result["sheets"][0]["formula_cache_missing_count"])
        self.assertEqual(1, result["sheets"][0]["formula_cache_empty_count"])

    def test_shared_formula_follower_and_array_attributes_are_preserved(self):
        result = self.inspect(package_parts(
            '<c r="A1"><f t="shared" si="0" ref="A1:A2">B1*2</f><v>4</v></c>'
            '<c r="A2"><f t="shared" si="0"/><v>6</v></c>'
            '<c r="C1"><f t="array" ref="C1:C2">A1:A2*2</f><v>8</v></c>'
        ))
        self.assertTrue(result["valid"], result["errors"])
        self.assertEqual("", result["sheets"][0]["formulas"]["A2"]["text"])
        self.assertEqual({"si": "0", "t": "shared"}, result["sheets"][0]["formulas"]["A2"]["attributes"])
        self.assertEqual("C1:C2", result["sheets"][0]["formulas"]["C1"]["attributes"]["ref"])

    def test_cached_errors_include_formula_and_literal_error_cells(self):
        result = self.inspect(package_parts(
            '<c r="A1" t="e"><f>1/0</f><v>#DIV/0!</v></c>'
            '<c r="B1" t="e"><v>#N/A</v></c>'
        ))
        self.assertEqual(2, result["cached_error_count"])
        self.assertEqual([
            {"cell": "A1", "value": "#DIV/0!", "formula": True},
            {"cell": "B1", "value": "#N/A", "formula": False},
        ], result["sheets"][0]["cached_errors"])

    def test_missing_relationship_target_fails_validation(self):
        parts = package_parts()
        del parts["xl/worksheets/sheet1.xml"]
        result = self.inspect(parts)
        self.assertFalse(result["valid"])
        self.assertTrue(any("Missing relationship target" in error for error in result["errors"]))

    def test_orphan_relationship_source_fails_validation(self):
        parts = package_parts()
        parts["xl/worksheets/_rels/deleted.xml.rels"] = relationships([])
        result = self.inspect(parts)
        self.assertFalse(result["valid"])
        self.assertTrue(any("Missing relationship source" in error for error in result["errors"]))

    def test_invalid_xml_fails_in_an_auxiliary_part(self):
        parts = package_parts()
        parts["xl/styles.xml"] = "<styleSheet><broken>"
        result = self.inspect(parts)
        self.assertFalse(result["valid"])
        self.assertTrue(any("Invalid XML in xl/styles.xml" in error for error in result["errors"]))

    def test_unsupported_xml_encoding_returns_invalid_json_for_inspect_and_compare(self):
        before = self.write(package_parts(), "before.xlsx")
        for encoding in ("not-a-real-encoding", "UTF-32"):
            with self.subTest(encoding=encoding):
                parts = package_parts()
                parts["xl/styles.xml"] = ('<?xml version="1.0" encoding="' + encoding + '"?><styleSheet/>').encode("ascii")
                after = self.write(parts, "after.xlsx")
                for args in (["inspect", str(after)], ["compare", str(before), str(after)]):
                    stream = io.StringIO()
                    with contextlib.redirect_stdout(stream):
                        status = xlsx.main(args)
                    result = json.loads(stream.getvalue())
                    self.assertEqual(1, status)
                    self.assertFalse(result["valid"])
                    inspection = result if args[0] == "inspect" else result["after"]
                    self.assertTrue(any("Invalid XML in xl/styles.xml" in error for error in inspection["errors"]))

    def test_dtd_entity_is_rejected_before_parsing(self):
        parts = package_parts()
        parts["xl/styles.xml"] = '<!DOCTYPE x [<!ENTITY y "expanded">]><x>&y;</x>'
        result = self.inspect(parts)
        self.assertFalse(result["valid"])
        self.assertTrue(any("DTD or entity" in error for error in result["errors"]))

    def test_utf16_dtd_entity_is_also_rejected(self):
        parts = package_parts()
        parts["xl/styles.xml"] = '<!DOCTYPE x [<!ENTITY y "expanded">]><x>&y;</x>'.encode("utf-16")
        result = self.inspect(parts)
        self.assertFalse(result["valid"])
        self.assertTrue(any("DTD or entity" in error for error in result["errors"]))

    def test_internal_relationship_escape_is_rejected(self):
        parts = package_parts()
        parts["xl/_rels/workbook.xml.rels"] = relationships([
            ("rId1", "worksheet", "../../outside.xml", None),
        ])
        result = self.inspect(parts)
        self.assertFalse(result["valid"])
        self.assertTrue(any("escapes the package" in error for error in result["errors"]))

    def test_percent_encoded_relationship_escape_is_rejected(self):
        parts = package_parts()
        parts["xl/_rels/workbook.xml.rels"] = relationships([
            ("rId1", "worksheet", "%2e%2e/%2e%2e/outside.xml", None),
        ])
        result = self.inspect(parts)
        self.assertFalse(result["valid"])
        self.assertTrue(any("escapes the package" in error for error in result["errors"]))

    def test_external_relationships_are_not_read_or_treated_as_missing(self):
        parts = package_parts()
        parts["xl/worksheets/_rels/sheet1.xml.rels"] = relationships([
            ("rIdUrl", "hyperlink", "https://example.invalid/report", "External"),
        ])
        result = self.inspect(parts)
        self.assertTrue(result["valid"], result["errors"])
        self.assertEqual("https://example.invalid/report", result["external_relationships"][0]["target"])
        self.assertTrue(any("without contacting" in warning for warning in result["warnings"]))

    def test_sensitive_features_and_unknown_parts_require_preservation(self):
        parts = package_parts()
        parts.update({
            "xl/vbaProject.bin": b"macro payload",
            "xl/pivotTables/pivotTable1.xml": "<pivotTableDefinition/>",
            "xl/pivotCache/pivotCacheDefinition1.xml": "<pivotCacheDefinition/>",
            "xl/slicers/slicer1.xml": "<slicers/>",
            "xl/externalLinks/externalLink1.xml": "<externalLink/>",
            "vendor/custom.bin": b"preserve me",
        })
        parts["xl/worksheets/sheet1.xml"] = sheet(extra="<extLst><ext uri=\"vendor\"/></extLst>")
        result = self.inspect(parts)
        self.assertTrue(result["valid"], result["errors"])
        sensitivity = result["preservation_sensitive"]
        for category in ("macros", "pivots", "slicers_or_timelines", "external_links", "extension_metadata"):
            self.assertIn(category, sensitivity)
        self.assertIn("vendor/custom.bin", sensitivity["unknown_parts"])

    def test_native_tables_and_charts_are_inventoried(self):
        parts = package_parts(chart=True)
        parts["xl/tables/table1.xml"] = (
            '<table xmlns="' + SHEET_NS + '" name="Sales" displayName="Sales" ref="A1:B3">'
            '<tableColumns count="2"><tableColumn id="1" name="Item"/><tableColumn id="2" name="Amount"/>'
            "</tableColumns></table>"
        )
        result = self.inspect(parts)
        self.assertTrue(result["valid"], result["errors"])
        self.assertEqual(["xl/charts/chart1.xml"], result["chart_parts"])
        self.assertEqual("A1:B3", result["tables"][0]["ref"])
        self.assertEqual(["Item", "Amount"], result["tables"][0]["columns"])

    def test_compare_preserved_formula_and_lost_chart_are_separate_observations(self):
        before = self.write(package_parts(chart=True), "before.xlsx")
        after = self.write(package_parts(), "after.xlsx")
        result = xlsx.compare_workbooks(before, after)
        self.assertTrue(result["valid"])
        self.assertEqual([], result["formula_changes"])
        self.assertEqual(["xl/charts/chart1.xml"], result["removed_chart_parts"])
        self.assertIn("xl/charts/chart1.xml", result["removed_parts"])
        self.assertIn("not automatically a defect", result["notice"])

    def test_compare_formula_removal_is_visible_even_with_same_numeric_cache(self):
        before = self.write(package_parts(), "before.xlsx")
        after = self.write(package_parts('<c r="A1"><v>2</v></c><c r="B1"><v>4</v></c>'), "after.xlsx")
        result = xlsx.compare_workbooks(before, after)
        self.assertEqual(1, len(result["formula_changes"]))
        self.assertEqual("B1", result["formula_changes"][0]["cell"])
        self.assertIsNone(result["formula_changes"][0]["after"])

    def test_compare_cache_change_does_not_claim_recalculation(self):
        before = self.write(package_parts(), "before.xlsx")
        after = self.write(package_parts('<c r="A1"><v>2</v></c><c r="B1"><f>A1*2</f><v>999</v></c>'), "after.xlsx")
        result = xlsx.compare_workbooks(before, after)
        self.assertEqual([], result["formula_changes"])
        self.assertEqual(1, len(result["cache_changes"]))
        self.assertIn("do not prove recalculation", result["cache_verification"])

    def test_compare_tracks_shared_formula_attribute_changes(self):
        before = self.write(package_parts('<c r="A1"><f t="shared" si="0"/><v>0</v></c>'), "before.xlsx")
        after = self.write(package_parts('<c r="A1"><f t="shared" si="1"/><v>0</v></c>'), "after.xlsx")
        result = xlsx.compare_workbooks(before, after)
        self.assertEqual(1, len(result["formula_changes"]))
        self.assertEqual([], result["cache_changes"])

    def test_sheet_rename_is_explicit_and_left_for_authorized_change_review(self):
        before = self.write(package_parts(), "before.xlsx")
        after_parts = package_parts()
        after_parts["xl/workbook.xml"] = after_parts["xl/workbook.xml"].replace('name="Model"', 'name="Forecast"')
        after = self.write(after_parts, "after.xlsx")
        result = xlsx.compare_workbooks(before, after)
        self.assertTrue(result["valid"])
        self.assertEqual(["Model"], result["removed_sheets"])
        self.assertEqual(["Forecast"], result["added_sheets"])

    def test_strict_ooxml_spreadsheet_and_document_relationship_namespace(self):
        parts = package_parts()
        for name, text in list(parts.items()):
            parts[name] = text.replace(SHEET_NS, "http://purl.oclc.org/ooxml/spreadsheetml/main").replace(
                DOCUMENT_REL_NS, "http://purl.oclc.org/ooxml/officeDocument/relationships"
            )
        result = self.inspect(parts)
        self.assertTrue(result["valid"], result["errors"])
        self.assertEqual(1, result["formula_count"])

    def test_duplicate_and_out_of_range_cells_fail(self):
        result = self.inspect(package_parts('<c r="A1"/><c r="A1"/><c r="XFE1"/><c r="A1048577"/>'))
        self.assertFalse(result["valid"])
        self.assertEqual(3, sum("cell reference" in error for error in result["errors"]))

    def test_duplicate_zip_parts_fail_without_extracting(self):
        destination = self.directory / "duplicate.xlsx"
        with zipfile.ZipFile(destination, "w") as archive:
            archive.writestr("duplicate.bin", b"first")
            with self.assertWarns(UserWarning):
                archive.writestr("duplicate.bin", b"second")
        result = xlsx.inspect_workbook(destination)
        self.assertFalse(result["valid"])
        self.assertIn("Duplicate package part", result["errors"][0])

    def test_zip_path_traversal_fails_without_creating_a_file(self):
        result = self.inspect({"../outside.xml": "<x/>"})
        self.assertFalse(result["valid"])
        self.assertIn("Invalid package path", result["errors"][0])
        self.assertFalse((self.directory.parent / "outside.xml").exists())

    def test_byte_and_cell_bounds_fail_with_explicit_incomplete_inspection(self):
        destination = self.write()
        with patch.object(xlsx, "MAX_PART_BYTES", 32):
            result = xlsx.inspect_workbook(destination)
        self.assertFalse(result["valid"])
        self.assertIn("byte limit", result["errors"][0])
        with patch.object(xlsx, "MAX_CELLS", 1):
            result = xlsx.inspect_workbook(destination)
        self.assertFalse(result["valid"])
        self.assertTrue(any("cell limit" in error for error in result["errors"]))

    def test_missing_content_types_and_non_zip_files_fail(self):
        result = xlsx.inspect_workbook(self.write(content_types=False))
        self.assertFalse(result["valid"])
        self.assertTrue(any("[Content_Types]" in error for error in result["errors"]))
        destination = self.directory / "not.xlsx"
        destination.write_bytes(b"not a ZIP")
        result = xlsx.inspect_workbook(destination)
        self.assertFalse(result["valid"])
        self.assertIn("Cannot read spreadsheet package", result["errors"][0])

    def test_inspect_and_compare_do_not_mutate_source_files(self):
        before = self.write(package_parts(), "before.xlsx")
        after = self.write(package_parts(chart=True), "after.xlsx")
        before_bytes, after_bytes = before.read_bytes(), after.read_bytes()
        xlsx.inspect_workbook(before)
        xlsx.compare_workbooks(before, after)
        self.assertEqual(before_bytes, before.read_bytes())
        self.assertEqual(after_bytes, after.read_bytes())

    def test_cli_deltas_are_not_automatic_failure_and_invalid_files_are(self):
        before = self.write(package_parts(chart=True), "before.xlsx")
        after = self.write(package_parts(), "after.xlsx")
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            status = xlsx.main(["compare", str(before), str(after)])
        self.assertEqual(0, status)
        self.assertIn("xl/charts/chart1.xml", json.loads(stream.getvalue())["removed_parts"])
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            status = xlsx.main(["inspect", str(self.directory / "missing.xlsx")])
        self.assertEqual(1, status)
        self.assertFalse(json.loads(stream.getvalue())["valid"])


if __name__ == "__main__":
    unittest.main()
