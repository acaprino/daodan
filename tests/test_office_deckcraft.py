"""DeckCraft argument transport and independent PPTX preservation checks.

Run directly from this draft path or copy into tests/ unchanged.
"""

import contextlib
import importlib.util
import io
import json
import os
import subprocess
import tempfile
import unittest
import warnings
import zipfile
from pathlib import Path
from unittest import mock


ROOT = next(parent for parent in Path(__file__).resolve().parents
            if (parent / "plugins/office/skills").is_dir())
SCRIPTS = ROOT / "plugins/office/skills/deckcraft/scripts"


def load(name):
    spec = importlib.util.spec_from_file_location("office_test_" + name, SCRIPTS / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


bridge = load("deckcraft_bridge")
pptx = load("pptx_inspect")
P = "http://schemas.openxmlformats.org/presentationml/2006/main"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PR = "http://schemas.openxmlformats.org/package/2006/relationships"
CT = "http://schemas.openxmlformats.org/package/2006/content-types"
MAIN_TYPE = "application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"


def rels(items):
    return '<Relationships xmlns="' + PR + '">' + "".join(
        '<Relationship Id="' + key + '" Type="' + R + '/' + kind + '" Target="' + target + '"'
        + (' TargetMode="' + mode + '"' if mode else '') + '/>'
        for key, kind, target, mode in items) + '</Relationships>'


def slide(text="Native title", extra="", hidden=False):
    return ('<p:sld xmlns:p="' + P + '" xmlns:a="' + A + '" xmlns:r="' + R + '"'
            + (' show="0"' if hidden else '') + '><p:cSld><p:spTree><p:sp><p:txBody>'
            '<a:p><a:r><a:t>' + text + '</a:t></a:r></a:p></p:txBody></p:sp>'
            + extra + '</p:spTree></p:cSld></p:sld>')


def parts(order=("slide1.xml", "slide2.xml")):
    """Order is deliberately independent from ZIP or filename sorting."""
    return {
        "_rels/.rels": rels([("doc", "officeDocument", "ppt/presentation.xml", None)]),
        "ppt/presentation.xml": '<p:presentation xmlns:p="' + P + '" xmlns:r="' + R + '"><p:sldIdLst>'
        + ''.join('<p:sldId id="' + str(256 + index) + '" r:id="s' + str(index) + '"/>'
                  for index in range(len(order)))
        + '</p:sldIdLst><p:sldSz cx="12192000" cy="6858000"/></p:presentation>',
        "ppt/_rels/presentation.xml.rels": rels([
            ("s" + str(index), "slide", "slides/" + name, None) for index, name in enumerate(order)]),
        **{"ppt/slides/" + name: slide("Title " + name) for name in order},
    }


def typed(package, main_type=MAIN_TYPE):
    defaults = {'rels': 'application/vnd.openxmlformats-package.relationships+xml',
                'xml': 'application/xml', 'png': 'image/png', 'bin': 'application/octet-stream'}
    overrides = {"ppt/presentation.xml": main_type}
    for name in package:
        if name.startswith("ppt/slides/") and name.endswith(".xml"):
            overrides[name] = "application/vnd.openxmlformats-officedocument.presentationml.slide+xml"
        elif name.startswith("ppt/notesSlides/") and name.endswith(".xml"):
            overrides[name] = "application/vnd.openxmlformats-officedocument.presentationml.notesSlide+xml"
    declarations = ''.join('<Default Extension="' + ext + '" ContentType="' + mime + '"/>'
                           for ext, mime in defaults.items())
    declarations += ''.join('<Override PartName="/' + name + '" ContentType="' + mime + '"/>'
                            for name, mime in overrides.items())
    return {"[Content_Types].xml": '<Types xmlns="' + CT + '">' + declarations + '</Types>', **package}


class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="deckcraft transport ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.binary = self.root / "deckcraft-cli.exe"
        self.binary.touch()
        self.source = self.root / "source deck.pptx"
        self.source.write_bytes(b"original presentation bytes")
        self.output = self.root / "candidate deck.pptx"
        self.plan = self.root / "commands.json"
        self.command_plan([{"command": "text.set", "params": {"id": "title", "text": "Revenue"}}])

    def command_plan(self, commands):
        self.plan.write_text(json.dumps(commands, ensure_ascii=False), encoding="utf-8")
        return self.plan

    def test_selected_executable_probe_has_no_shell_and_reports_version(self):
        with mock.patch.object(bridge.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, "deckcraft-cli 0.10.0\n", "")) as run:
            actual = bridge.discover(environ={"DECKCRAFT_CLI": str(self.binary)})
        self.assertEqual("0.10.0", actual["version"])
        self.assertTrue(actual["matches_reference"])
        self.assertEqual([str(self.binary), "--version"], run.call_args.args[0])
        self.assertNotIn("shell", run.call_args.kwargs)

    def test_missing_runtime_does_not_start_process(self):
        with mock.patch.object(bridge.subprocess, "run") as run:
            with self.assertRaisesRegex(bridge.BridgeError, "missing"):
                bridge.discover(self.root / "missing.exe")
        run.assert_not_called()

    def test_invalid_runtime_response_and_probe_timeout_are_reported(self):
        for completed in [subprocess.CompletedProcess([], 0, "another tool 0.10.0", ""),
                          subprocess.CompletedProcess([], 3, "deckcraft-cli 0.10.0", "failure")]:
            with self.subTest(completed=completed):
                with mock.patch.object(bridge.subprocess, "run", return_value=completed):
                    with self.assertRaises(bridge.BridgeError):
                        bridge.discover(self.binary)
        with mock.patch.object(bridge.subprocess, "run", side_effect=subprocess.TimeoutExpired("probe", 30)):
            with self.assertRaisesRegex(bridge.BridgeError, "Cannot probe"):
                bridge.discover(self.binary)

    def test_unrecognized_version_is_visible_without_claiming_reference_match(self):
        with mock.patch.object(bridge.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, "deckcraft-cli 0.11.0", "")):
            result = bridge.discover(self.binary)
        self.assertFalse(result["matches_reference"])

    def test_apply_passes_unicode_and_shell_characters_as_one_json_argument(self):
        message = 'Caffè "growth" $(literal); & remains text'
        self.command_plan([{"command": "text.set", "params": {"id": "title", "text": message}}])

        def execute(binary, argv):
            self.assertEqual(["run", "--print", "--in", str(self.source)], argv[:4])
            self.assertEqual("text.set", argv[5].split("=", 1)[0])
            self.assertEqual(message, json.loads(argv[5].split("=", 1)[1])["text"])
            self.assertEqual(["--save", str(self.output)], argv[-2:])
            self.output.write_bytes(b"candidate")
            return 0

        before = self.source.read_bytes()
        with mock.patch.object(bridge, "invoke", side_effect=execute):
            self.assertEqual(0, bridge.apply_plan(self.binary, self.plan, self.output, self.source))
        self.assertEqual(before, self.source.read_bytes())

    def test_source_and_output_alias_is_rejected_before_execution(self):
        with mock.patch.object(bridge, "invoke") as run:
            with self.assertRaisesRegex(bridge.BridgeError, "different files"):
                bridge.apply_plan(self.binary, self.plan, self.source.parent / "." / self.source.name, self.source)
        run.assert_not_called()
        self.assertEqual(b"original presentation bytes", self.source.read_bytes())

    def test_hard_link_output_alias_is_rejected_before_execution(self):
        try:
            os.link(self.source, self.output)
        except OSError as error:
            self.skipTest(f"Hard links unavailable: {error}")
        with mock.patch.object(bridge, "invoke") as run:
            with self.assertRaisesRegex(bridge.BridgeError, "different files"):
                bridge.apply_plan(self.binary, self.plan, self.output, self.source)
        run.assert_not_called()

    def test_existing_output_is_preserved_without_execution(self):
        self.output.write_bytes(b"earlier candidate")
        with mock.patch.object(bridge, "invoke") as run:
            with self.assertRaisesRegex(bridge.BridgeError, "already exists"):
                bridge.apply_plan(self.binary, self.plan, self.output, self.source)
        run.assert_not_called()
        self.assertEqual(b"earlier candidate", self.output.read_bytes())

    def test_invalid_input_output_extension_and_missing_parent_are_rejected(self):
        cases = [(self.root / "absent.pptx", self.output),
                 (self.source, self.output.with_suffix(".pdf")),
                 (self.source, self.root / "missing" / "new.pptx")]
        for source, output in cases:
            with self.subTest(output=output):
                with mock.patch.object(bridge, "invoke") as run:
                    with self.assertRaises(bridge.BridgeError):
                        bridge.apply_plan(self.binary, self.plan, output, source)
                run.assert_not_called()

    def test_failed_engine_exit_is_not_relabelled_success(self):
        with mock.patch.object(bridge, "invoke", return_value=17):
            self.assertEqual(17, bridge.apply_plan(self.binary, self.plan, self.output, self.source))
        self.assertFalse(self.output.exists())
        self.assertEqual(b"original presentation bytes", self.source.read_bytes())

    def test_failed_engine_partial_output_is_retained_as_evidence(self):
        def fail(binary, arguments):
            self.output.write_bytes(b"partial candidate")
            return 9
        with mock.patch.object(bridge, "invoke", side_effect=fail):
            self.assertEqual(9, bridge.apply_plan(self.binary, self.plan, self.output, self.source))
        self.assertEqual(b"partial candidate", self.output.read_bytes())

    def test_success_without_output_is_failure(self):
        with mock.patch.object(bridge, "invoke", return_value=0):
            with self.assertRaisesRegex(bridge.BridgeError, "without the requested output"):
                bridge.apply_plan(self.binary, self.plan, self.output, self.source)

    def test_plan_rejects_file_side_effects_and_app_commands(self):
        for command in ("file.save", "file.open", "file.export", "app.quit", "file.new"):
            with self.subTest(command=command):
                self.command_plan([{"command": command, "params": {}}])
                with self.assertRaisesRegex(bridge.BridgeError, "File operations"):
                    bridge.load_commands(self.plan, editing=True)

    def test_new_document_command_is_allowed_only_at_beginning_of_creation(self):
        create = {"command": "file.new", "params": {"blank": True}}
        edit = {"command": "slide.new", "params": {}}
        self.command_plan([create, edit])
        self.assertEqual([create, edit], bridge.load_commands(self.plan))
        self.command_plan([edit, create])
        with self.assertRaises(bridge.BridgeError):
            bridge.load_commands(self.plan)

    def test_plan_has_bounded_size_and_exact_schema(self):
        for data in ([], {}, [{"command": "text.set", "params": []}],
                     [{"command": "text.set", "params": {}, "extra": True}],
                     [{"command": "x;touch", "params": {}}]):
            with self.subTest(data=data):
                self.command_plan(data)
                with self.assertRaises(bridge.BridgeError):
                    bridge.load_commands(self.plan)
        self.plan.write_bytes(b" " * (bridge.MAX_PLAN_BYTES + 1))
        with self.assertRaisesRegex(bridge.BridgeError, "1 MiB"):
            bridge.load_commands(self.plan)

    def test_invoke_preserves_argument_boundaries_and_exit_code(self):
        arguments = ["render", "deck with spaces.pptx", "$(literal)"]
        with mock.patch.object(bridge.subprocess, "run", return_value=subprocess.CompletedProcess([], 23)) as run:
            self.assertEqual(23, bridge.invoke(self.binary, arguments))
        run.assert_called_once_with([str(self.binary), *arguments])

    def test_cli_passthrough_owns_leading_options_for_both_global_option_forms(self):
        runtime = {"binary": str(self.binary)}
        for prefix in ([], ["--binary", str(self.binary)], ["--binary=" + str(self.binary)]):
            for trailing in (["--help"], ["--version"], ["--", "--help"]):
                with self.subTest(prefix=prefix, trailing=trailing):
                    with mock.patch.object(bridge, "discover", return_value=runtime):
                        with mock.patch.object(bridge, "invoke", return_value=0) as run:
                            self.assertEqual(0, bridge.main([*prefix, "cli", *trailing]))
                    run.assert_called_once_with(str(self.binary), trailing[-1:])


class PresentationInspectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="pptx preservation ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def write(self, content=None, name="deck.pptx", main_type=MAIN_TYPE, content_types=True):
        destination = self.root / name
        content = parts() if content is None else content
        if content_types:
            content = typed(content, main_type)
        with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
            for part, payload in content.items():
                archive.writestr(part, payload)
        return destination

    def inspect(self, content=None, **options):
        return pptx.inspect_presentation(self.write(content, **options))

    def compare(self, before, after):
        return pptx.compare_presentations(self.write(before, "before.pptx"), self.write(after, "after.pptx"))

    def test_order_follows_presentation_relationships_and_native_text(self):
        result = self.inspect(parts(("slide20.xml", "slide3.xml")))
        self.assertTrue(result["valid"], result["errors"])
        self.assertEqual(["ppt/slides/slide20.xml", "ppt/slides/slide3.xml"], [slide["part"] for slide in result["slides"]])
        self.assertEqual(["Title slide20.xml"], result["slides"][0]["text"])
        self.assertEqual(1, result["slides"][0]["objects"]["sp"])
        self.assertEqual("12192000", result["canvas"]["cx"])
        self.assertIn("no rendering", result["visual_review"])

    def test_strict_namespaces_are_supported(self):
        content = {name: value.replace(P, "http://purl.oclc.org/ooxml/presentationml/main")
                   .replace(A, "http://purl.oclc.org/ooxml/drawingml/main")
                   .replace(R, "http://purl.oclc.org/ooxml/officeDocument/relationships")
                   for name, value in parts().items()}
        result = self.inspect(content)
        self.assertTrue(result["valid"], result["errors"])
        self.assertEqual(["Title slide1.xml"], result["slides"][0]["text"])

    def test_native_text_and_object_loss_cannot_hide_behind_visual_similarity(self):
        before = parts(("slide1.xml",))
        after = {**before, "ppt/slides/slide1.xml": slide("", '<p:pic/>')}
        result = self.compare(before, after)
        self.assertTrue(result["valid"])
        self.assertEqual(["text", "objects"], result["slide_changes"][0]["changed_fields"])

    def test_notes_hidden_state_and_slide_removal_are_reported(self):
        before = parts()
        before["ppt/slides/slide1.xml"] = slide("Title slide1.xml", hidden=True)
        before["ppt/slides/_rels/slide1.xml.rels"] = rels([("notes", "notesSlide", "../notesSlides/notes1.xml", None)])
        before["ppt/notesSlides/notes1.xml"] = '<p:notes xmlns:p="' + P + '" xmlns:a="' + A + '"><a:t>Speaker note</a:t></p:notes>'
        result = self.compare(before, parts(("slide1.xml",)))
        self.assertTrue(result["valid"], result["before"]["errors"])
        self.assertEqual([["Speaker note"]], result["before"]["slides"][0]["notes"])
        self.assertIn("notes", result["slide_changes"][0]["changed_fields"])
        self.assertIn("hidden", result["slide_changes"][0]["changed_fields"])
        self.assertEqual({}, result["slide_changes"][1]["after"])
        self.assertEqual([1, 0], result["feature_counts_changed"]["notes"])

    def test_changed_image_payload_is_reported_with_unchanged_text(self):
        before = parts(("slide1.xml",))
        before["ppt/slides/_rels/slide1.xml.rels"] = rels([("img", "image", "../media/image1.png", None)])
        before["ppt/media/image1.png"] = b"original image bytes"
        result = self.compare(before, {**before, "ppt/media/image1.png": b"replacement image bytes"})
        self.assertEqual([], result["slide_changes"])
        self.assertEqual(["ppt/media/image1.png"], result["changed_parts"])
        self.assertEqual(1, len(result["removed_payload_hashes"]))

    def test_identical_payload_renaming_does_not_report_binary_loss(self):
        before = {**parts(), "ppt/media/image1.png": b"same image"}
        after = {**parts(), "ppt/media/renamed.png": b"same image"}
        result = self.compare(before, after)
        self.assertEqual([], result["removed_payload_hashes"])
        self.assertEqual(["ppt/media/image1.png"], result["removed_parts"])

    def test_loss_of_one_of_two_identical_payloads_is_reported(self):
        before = {**parts(), "ppt/media/image1.png": b"same", "ppt/media/image2.png": b"same"}
        result = self.compare(before, {**parts(), "ppt/media/image1.png": b"same"})
        self.assertEqual(1, len(result["removed_payload_hashes"]))

    def test_external_relationship_changes_are_reported_without_following_links(self):
        before = {**parts(), "ppt/slides/_rels/slide1.xml.rels": rels([("web", "hyperlink", "https://example.invalid/", "External")])}
        result = self.compare(before, parts())
        self.assertTrue(result["valid"])
        self.assertTrue(result["external_relationships_changed"])
        self.assertEqual("https://example.invalid/", result["before"]["external_relationships"][0]["target"])

    def test_raw_parts_reveal_format_loss_even_when_text_and_counts_match(self):
        before = parts()
        before["ppt/slides/slide1.xml"] = slide("Same").replace('<a:r>', '<a:r><a:rPr b="1"/>')
        result = self.compare(before, {**before, "ppt/slides/slide1.xml": slide("Same")})
        self.assertEqual([], result["slide_changes"])
        self.assertEqual(["ppt/slides/slide1.xml"], result["changed_parts"])

    def test_identical_inventory_is_not_a_fidelity_verdict_and_reads_are_immutable(self):
        source = self.write()
        original = source.read_bytes()
        result = pptx.compare_presentations(source, source)
        self.assertTrue(result["valid"])
        self.assertEqual([], result["changed_parts"])
        self.assertIn("do not prove semantic or visual fidelity", result["notice"])
        self.assertEqual(original, source.read_bytes())

    def test_wrong_main_relationship_namespace_and_main_type_are_invalid(self):
        content = parts()
        invalid = [
            {**content, "_rels/.rels": rels([("doc", "notDocument", "ppt/presentation.xml", None)])},
            {**content, "ppt/presentation.xml": content["ppt/presentation.xml"].replace(P, "urn:wrong")},
        ]
        for candidate in invalid:
            with self.subTest(candidate=candidate):
                self.assertFalse(self.inspect(candidate)["valid"])
        self.assertFalse(self.inspect(main_type="application/vnd.ms-powerpoint.presentation.macroEnabled.main+xml")["valid"])

    def test_missing_slide_relation_and_dangling_embedded_image_are_invalid(self):
        content = parts()
        del content["ppt/slides/slide1.xml"]
        result = self.inspect(content)
        self.assertFalse(result["valid"])
        content = parts()
        content["ppt/slides/slide1.xml"] = slide(extra='<p:pic><a:blip r:embed="missing"/></p:pic>')
        result = self.inspect(content)
        self.assertFalse(result["valid"])
        self.assertTrue(any("Missing referenced relationship" in error for error in result["errors"]))

    def test_duplicate_slide_identity_and_missing_content_types_are_invalid(self):
        content = parts()
        content["ppt/presentation.xml"] = content["ppt/presentation.xml"].replace('id="257"', 'id="256"')
        self.assertFalse(self.inspect(content)["valid"])
        self.assertFalse(self.inspect(content_types=False)["valid"])

    def test_untyped_part_returns_invalid_result_instead_of_traceback(self):
        result = self.inspect({**parts(), "ppt/unknown.no_content_type": b"unknown payload"})
        self.assertFalse(result["valid"])
        self.assertTrue(any("Missing content type" in error for error in result["errors"]))

    def test_path_traversal_and_escaping_relationship_are_rejected(self):
        content = {**parts(), "../outside.xml": "<x/>"}
        result = self.inspect(content)
        self.assertFalse(result["valid"])
        self.assertTrue(any("Invalid package path" in error for error in result["errors"]))
        content = {**parts(), "ppt/slides/_rels/slide1.xml.rels": rels([("bad", "image", "../../../outside.png", None)])}
        result = self.inspect(content)
        self.assertFalse(result["valid"])
        self.assertTrue(any("escapes the package" in error for error in result["errors"]))

    def test_dtd_declarations_are_rejected_in_utf8_and_utf16(self):
        unsafe = '<!DOCTYPE x [<!ENTITY value "expanded">]><x>&value;</x>'
        for payload in (unsafe.encode("utf-8"), unsafe.encode("utf-16")):
            with self.subTest(payload=payload[:8]):
                result = self.inspect({**parts(), "ppt/extra.xml": payload})
                self.assertFalse(result["valid"])
                self.assertTrue(any("DTD or entity" in error for error in result["errors"]))

    def test_duplicate_zip_parts_and_byte_limits_are_rejected(self):
        source = self.write()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            with zipfile.ZipFile(source, "a") as archive:
                archive.writestr("ppt/presentation.xml", "<changed/>")
        result = pptx.inspect_presentation(source)
        self.assertFalse(result["valid"])
        self.assertTrue(any("Duplicate package part" in error for error in result["errors"]))
        source = self.write(name="bounded.pptx")
        with mock.patch.object(pptx.package, "MAX_PART_BYTES", 8):
            result = pptx.inspect_presentation(source)
        self.assertFalse(result["valid"])
        self.assertTrue(any("byte limit" in error for error in result["errors"]))

    def test_invalid_package_cli_returns_nonzero_with_structured_evidence(self):
        source = self.root / "broken.pptx"
        source.write_bytes(b"not a ZIP")
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            code = pptx.main(["inspect", str(source)])
        self.assertEqual(1, code)
        self.assertFalse(json.loads(stream.getvalue())["valid"])


if __name__ == "__main__":
    unittest.main()
