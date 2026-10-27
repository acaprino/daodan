"""CLI behavior of the real-content comparison and explicit design selection.

These filesystem integration tests inspect semantic sample markers and applied
CSS data, not a particular HTML layout. Browser rendering remains a separate gate.
"""

import copy
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib

from test_office_records import valid_design, records


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "plugins/office/skills/design/scripts/design_compare.py"


def valid_comparison(formats=("docx", "pptx")):
    """Two authored proposals on identical source-backed Office requirements."""
    first = valid_design(formats)
    del first["selection"]
    second = copy.deepcopy(first)
    second["direction"] = {"name": "Technical clarity", "idea": "Separate evidence through strong type",
                           "principles": ["Use direct labels", "Give evidence enough space"]}
    second["typography"]["heading"] = {"family": "Atkinson Hyperlegible", "fallbacks": ["Arial", "sans-serif"],
                                          "weight": 800}
    second["typography"]["body"]["family"] = "Georgia"
    second["palette"].update(background="#FAF7F0", surface="#EAE4D8", ink="#242622", accent="#166534")
    second["spacing"]["unit"] = 12
    second["components"]["callout"] = "panel"
    second["data"]["table"] = "striped"
    return {
        "schema": "office/design-candidates/v1", "project_id": first["project_id"],
        "formats": list(formats),
        "sample": {
            "title": "Office content and composition",
            "lead": "One editorial record supplies independent native formats.",
            "body": "Office assigns the shared editorial method responsibility for claims, sources, "
                    "logical sequence and approved transformations. Visual design supplies a coherent "
                    "identity while DOCX and PPTX retain their own composition methods. Documents use "
                    "sections, paragraphs and continuous reading; presentations use slides, objects and "
                    "a speaking sequence. A comparison preview shows the intended visual decisions on "
                    "the same real material. Native editability, saved-file rendering and source fidelity "
                    "require their own evidence and independent review.",
            "source_note": "Office evolution relation, sections 4, 7, 8 and 9.",
            "table": {"headers": ["Responsibility", "DOCX", "PPTX"],
                      "rows": [["Content", "Shared editorial record", "Shared editorial record"],
                               ["Composition", "Sections and paragraphs", "Slides and objects"]]},
        },
        "candidates": [{"id": "editorial", "design": first}, {"id": "technical", "design": second}],
    }


def png_bytes(width=1, height=1):
    """A complete RGB PNG, including a valid large image for the pixel boundary."""
    def chunk(kind, payload):
        return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload))
    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    compressor = zlib.compressobj()
    row = b"\x00" + b"\x1d\x4e\xd8" * width
    compressed = b"".join(compressor.compress(row) for _ in range(height)) + compressor.flush()
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", compressed) + chunk(b"IEND", b"")


def jpeg_bytes():
    """A complete 1x1 grayscale baseline JPEG, without an imaging dependency."""
    def segment(marker, payload):
        return b"\xff" + bytes([marker]) + struct.pack(">H", len(payload) + 2) + payload
    one_code = b"\x01" + b"\x00" * 15
    return (b"\xff\xd8" + segment(0xDB, b"\x00" + b"\x01" * 64)
            + segment(0xC0, b"\x08\x00\x01\x00\x01\x01\x01\x11\x00")
            + segment(0xC4, b"\x00" + one_code + b"\x00")
            + segment(0xC4, b"\x10" + one_code + b"\x00")
            + segment(0xDA, b"\x01\x01\x00\x00\x3f\x00") + b"\x3f\xff\xd9")


class Element:
    def __init__(self, tag, attributes):
        self.tag, self.attributes, self.children = tag, dict(attributes), []

    def text(self):
        return "".join(item if isinstance(item, str) else item.text() for item in self.children)


class Document(HTMLParser):
    """Inspect rendered data through semantic attributes, independent of tags."""
    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}

    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.root = Element("document", [])
        self.stack, self.elements = [self.root], []
        self.feed(html)

    def handle_starttag(self, tag, attributes):
        node = Element(tag, attributes)
        self.stack[-1].children.append(node)
        self.elements.append(node)
        if tag not in self.VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attributes):
        self.handle_starttag(tag, attributes)
        if tag not in self.VOID:
            self.stack.pop()

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                break

    def handle_data(self, value):
        self.stack[-1].children.append(value)

    def frames(self):
        return [node for node in self.elements if "data-format" in node.attributes]

    def css(self):
        return "\n".join(node.text() if node.tag == "style" else node.attributes.get("style", "")
                         for node in self.elements if node.tag == "style" or "style" in node.attributes)

    def interface_text(self):
        def visit(node):
            if node.tag in {"style", "script"} or "data-format" in node.attributes:
                return ""
            return " ".join(item if isinstance(item, str) else visit(item) for item in node.children)
        return visit(self.root)

    def style_signature(self):
        css = self.css()
        bindings = [(node.tag, node.attributes.get("style", ""),
                     tuple(name for name in node.attributes.get("class", "").split()
                           if re.search(r"\." + re.escape(name) + r"(?:[^\w-]|$)", css)))
                    for node in self.elements]
        return css, bindings


class DesignComparisonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not SCRIPT.is_file():
            raise FileNotFoundError(f"Required comparison CLI is not implemented: {SCRIPT}")

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="office-comparison-")
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.inputs = self.directory / "inputs"
        self.inputs.mkdir()
        self.input = self.inputs / "candidates.json"

    def run_cli(self, document, *arguments, output="COMPARE.html"):
        self.input.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")
        destination = self.directory / output
        result = subprocess.run([sys.executable, "-B", str(SCRIPT), str(self.input), *map(str, arguments),
                                 "--out", str(destination)], cwd=ROOT, capture_output=True, text=True,
                                encoding="utf-8", errors="replace", timeout=30)
        return result, destination

    def preview(self, document, output="COMPARE.html"):
        result, destination = self.run_cli(document, output=output)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(destination.is_file())
        return Document(destination.read_text(encoding="utf-8"))

    def assert_rejected(self, document, *arguments):
        result, destination = self.run_cli(document, *arguments)
        self.assertNotEqual(result.returncode, 0, "Invalid input was accepted")
        self.assertFalse(destination.exists(), "Rejected input published an output")
        self.assertEqual(json.loads(self.input.read_text(encoding="utf-8")), document)

    def assert_css_value(self, document, property_name, expected):
        declarations = re.findall(r"([\w-]+)\s*:\s*([^;{}]+)", document.css())
        direct = any(key == property_name and expected.casefold() in value.casefold()
                     for key, value in declarations)
        variables = [key for key, value in declarations if key.startswith("--")
                     and expected.casefold() in value.casefold()]
        indirect = any(key == property_name and any(re.search(r"var\(\s*" + re.escape(variable) + r"[\s,)]", value)
                                                   for variable in variables)
                       for key, value in declarations)
        self.assertTrue(direct or indirect, f"{expected!r} is not applied through CSS {property_name}")

    def test_every_requested_frame_uses_the_same_complete_real_content(self):
        document = valid_comparison()

        rendered = self.preview(document)

        frames = rendered.frames()
        self.assertEqual({(node.attributes.get("data-candidate-id"), node.attributes["data-format"])
                          for node in frames}, {("editorial", "docx"), ("editorial", "pptx"),
                                                ("technical", "docx"), ("technical", "pptx")})
        self.assertEqual(len(frames), 4)
        sample = document["sample"]
        expected = [sample[name] for name in ("title", "lead", "body", "source_note")]
        expected += sample["table"]["headers"]
        expected += [cell for row in sample["table"]["rows"] for cell in row]
        for frame in frames:
            for text in expected:
                self.assertIn(text, frame.text())

    def test_single_format_comparisons_have_no_implicit_other_format_frame(self):
        for formats in (("docx",), ("pptx",)):
            with self.subTest(formats=formats):
                rendered = self.preview(valid_comparison(formats), output=formats[0] + ".html")

                self.assertEqual(len(rendered.frames()), 2)
                self.assertEqual({node.attributes["data-format"] for node in rendered.frames()}, set(formats))

    def test_actual_candidate_fonts_weights_and_colours_are_used_in_css(self):
        document = valid_comparison()

        rendered = self.preview(document)

        for candidate in document["candidates"]:
            design = candidate["design"]
            for role in ("heading", "body", "caption"):
                self.assert_css_value(rendered, "font-family", design["typography"][role]["family"])
                self.assert_css_value(rendered, "font-weight", str(design["typography"][role]["weight"]))
            self.assert_css_value(rendered, "color", design["palette"]["ink"])
            declarations = rendered.css().lower()
            self.assertIn(design["palette"]["background"].lower(), declarations)
            self.assertIn(design["palette"]["accent"].lower(), declarations)

    def test_spacing_callout_and_table_decisions_change_applied_styles(self):
        original = valid_comparison(("docx",))
        before = self.preview(original).style_signature()
        for owner in ("spacing", "callout", "table"):
            with self.subTest(owner=owner):
                changed = copy.deepcopy(original)
                design = changed["candidates"][0]["design"]
                if owner == "spacing":
                    design["spacing"]["unit"] = 17
                elif owner == "callout":
                    design["components"]["callout"] = "panel"
                else:
                    design["data"]["table"] = "striped"

                after = self.preview(changed, output=owner + ".html").style_signature()

                self.assertNotEqual(after, before, f"The {owner} decision changed labels only")

    def test_preview_escapes_sample_direction_and_source_text(self):
        document = valid_comparison(("docx",))
        hostile = '<img src=x onerror="alert(1)"><script>alert(2)</script>&'
        for field in ("title", "lead", "body", "source_note"):
            document["sample"][field] = hostile
        document["sample"]["table"]["rows"][0][0] = hostile
        document["candidates"][0]["design"]["direction"]["idea"] = hostile

        rendered = self.preview(document)

        self.assertIn(hostile, rendered.root.text())
        self.assertFalse(any("onerror" in node.attributes for node in rendered.elements))
        self.assertFalse(any(node.tag == "img" for node in rendered.elements))
        self.assertFalse(any(node.tag == "script" and "alert(" in node.text() for node in rendered.elements))

    def test_unsafe_font_colour_and_style_values_fail_without_output(self):
        for target in ("font", "colour", "style"):
            with self.subTest(target=target):
                document = valid_comparison()
                design = document["candidates"][0]["design"]
                if target == "font":
                    design["typography"]["heading"]["family"] = "Arial;display:none"
                elif target == "colour":
                    design["palette"]["accent"] = "url(https://invalid.test/x)"
                else:
                    design["components"]["callout"] = "panel;position:fixed"

                self.assert_rejected(document)

    def test_preview_is_self_contained_keyboard_accessible_and_explicitly_limited(self):
        rendered = self.preview(valid_comparison())
        text = " ".join(rendered.interface_text().lower().split())

        self.assertIn("preview", text)
        self.assertRegex(text, r"native|saved.office|office.file")
        self.assertRegex(text, r"not.{0,100}(fidelity|render|verify|proof|prove)|"
                              r"(native|saved|office).{0,100}(require|independent|separate)")
        controls = [node for node in rendered.elements if node.tag in {"button", "a", "input", "select"}
                    or node.attributes.get("tabindex") == "0"]
        self.assertTrue(controls, "Comparison navigation needs keyboard-reachable controls")
        for node in rendered.elements:
            if node.tag in {"script", "link", "img", "iframe"}:
                for field in ("src", "href"):
                    value = node.attributes.get(field, "")
                    self.assertFalse(value.startswith(("http:", "https:", "//")))
        self.assertNotRegex(rendered.css(), r"(?i)@import|url\(\s*['\"]?https?:")
        self.assertFalse((self.directory / "DESIGN.md").exists())
        self.assertEqual({path.relative_to(self.directory).as_posix() for path in self.directory.rglob("*")
                          if path.is_file()}, {"inputs/candidates.json", "COMPARE.html"})
        self.assertTrue(all("selection" not in item["design"] for item in json.loads(self.input.read_text())[
            "candidates"]), "Preview must not save an implicit decision into its input")

    def test_missing_or_incomplete_representative_sample_fails_without_invented_content(self):
        for field in ("sample", "title", "lead", "body", "source_note", "table"):
            with self.subTest(field=field):
                document = valid_comparison()
                if field == "sample":
                    del document[field]
                else:
                    del document["sample"][field]

                self.assert_rejected(document)
        for table in ({"headers": [], "rows": []}, {"headers": ["A", "B"], "rows": [["only one"]]}):
            with self.subTest(table=table):
                document = valid_comparison()
                document["sample"]["table"] = table

                self.assert_rejected(document)

    def test_schema_candidate_count_ids_and_design_records_are_validated(self):
        for mutation in ("schema", "one", "four", "duplicate", "missing_design", "invalid_design"):
            with self.subTest(mutation=mutation):
                document = valid_comparison()
                if mutation == "schema":
                    document["schema"] = "other"
                elif mutation == "one":
                    document["candidates"].pop()
                elif mutation == "four":
                    for identity in ("third", "fourth"):
                        candidate = copy.deepcopy(document["candidates"][0])
                        candidate["id"] = identity
                        document["candidates"].append(candidate)
                elif mutation == "duplicate":
                    document["candidates"][1]["id"] = "editorial"
                elif mutation == "missing_design":
                    del document["candidates"][0]["design"]
                else:
                    del document["candidates"][0]["design"]["typography"]["caption"]

                self.assert_rejected(document)

    def test_every_candidate_matches_the_shared_project_and_requested_formats(self):
        for mutation in ("project", "formats"):
            with self.subTest(mutation=mutation):
                document = valid_comparison(("docx",))
                design = document["candidates"][0]["design"]
                if mutation == "project":
                    design["project_id"] = design["content"]["project_id"] = "other-project"
                else:
                    document["candidates"][0]["design"] = valid_design(("pptx",))
                    del document["candidates"][0]["design"]["selection"]

                self.assert_rejected(document)

    def test_explicit_user_and_autonomous_selection_write_the_exact_validated_design(self):
        for authority in ("user", "autonomous"):
            with self.subTest(authority=authority):
                document = valid_comparison()
                source = "User chose technical in answer Q2" if authority == "user" else "Approved engineering autonomy"

                result, output = self.run_cli(document, "--select", "technical", "--authority", authority,
                                              "--source", source, output=authority + "-DESIGN.md")

                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                selected = records.load_record(output)
                expected = copy.deepcopy(document["candidates"][1]["design"])
                expected["selection"] = {"candidate_id": "technical", "authority": authority, "source": source}
                self.assertEqual(selected, expected)
                self.assertEqual(records.validate_design(selected), [])
                self.assertFalse((self.directory / "COMPARE.html").exists())

    def test_selection_rejects_unknown_candidate_authority_or_missing_decision_source(self):
        arguments = (("--select", "UNKNOWN", "--authority", "user", "--source", "Q2"),
                     ("--select", "technical", "--authority", "browser", "--source", "Q2"),
                     ("--select", "technical", "--authority", "user"),
                     ("--select", "technical", "--authority", "user", "--source", ""),
                     ("--select", "technical", "--source", "Q2"))
        for arguments_for_case in arguments:
            with self.subTest(arguments=arguments_for_case):
                self.assert_rejected(valid_comparison(), *arguments_for_case)

    def test_selection_validates_the_candidate_and_image_before_publishing(self):
        for target in ("design", "image"):
            with self.subTest(target=target):
                document = valid_comparison()
                if target == "design":
                    document["candidates"][1]["design"]["palette"]["ink"] = "invalid"
                else:
                    document["sample"]["image"] = {"path": "missing.png", "alt": "Project logo"}

                self.assert_rejected(document, "--select", "technical", "--authority", "user", "--source", "Q2")

    def combined_document(self):
        document = valid_comparison()
        child = copy.deepcopy(document["candidates"][0])
        child.update(id="combined", parent_ids=["editorial", "technical"])
        child["design"]["revision"] = 2
        child["design"]["direction"]["name"] = "Authored combination"
        child["design"]["typography"] = copy.deepcopy(document["candidates"][1]["design"]["typography"])
        document["candidates"].append(child)
        return document

    def test_authored_combination_with_explicit_parents_and_new_revision_is_repreviewable(self):
        document = self.combined_document()

        rendered = self.preview(document)

        self.assertEqual(len(rendered.frames()), 6)
        self.assertEqual({node.attributes.get("data-candidate-id") for node in rendered.frames()},
                         {"editorial", "technical", "combined"})
        self.assertIn("Authored combination", rendered.root.text())

    def test_combination_rejects_unknown_duplicate_self_parent_and_stale_revision(self):
        for mutation in ("unknown", "duplicate", "self", "stale"):
            with self.subTest(mutation=mutation):
                document = self.combined_document()
                child = document["candidates"][2]
                if mutation == "unknown":
                    child["parent_ids"] = ["editorial", "UNKNOWN"]
                elif mutation == "duplicate":
                    child["parent_ids"] = ["editorial", "editorial"]
                elif mutation == "self":
                    child["parent_ids"] = ["editorial", "combined"]
                else:
                    child["design"]["revision"] = 1

                self.assert_rejected(document)

    def test_selection_of_an_authored_combination_preserves_exact_content_and_identity(self):
        document = self.combined_document()
        self.preview(document)

        result, output = self.run_cli(document, "--select", "combined", "--authority", "user",
                                      "--source", "Approved authored combination Q3", output="DESIGN.md")

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        selected = records.load_record(output)
        expected = copy.deepcopy(document["candidates"][2]["design"])
        expected["selection"] = {"candidate_id": "combined", "authority": "user",
                                 "source": "Approved authored combination Q3",
                                 "parent_ids": ["editorial", "technical"]}
        self.assertEqual(selected, expected)
        self.assertEqual(json.loads(self.input.read_text())["candidates"][2]["parent_ids"], ["editorial", "technical"])

    def test_valid_local_png_and_jpeg_are_embedded_without_external_dependencies(self):
        for suffix, payload, mime in (("png", png_bytes(), "image/png"), ("jpg", jpeg_bytes(), "image/jpeg")):
            with self.subTest(suffix=suffix):
                image = self.inputs / ("logo." + suffix)
                image.write_bytes(payload)
                document = valid_comparison(("docx",))
                document["sample"]["image"] = {"path": image.name, "alt": "Daodan project logo"}

                rendered = self.preview(document, output=suffix + ".html")

                images = [node for node in rendered.elements if node.tag == "img"]
                self.assertEqual(len(images), 2)
                for node in images:
                    self.assertTrue(node.attributes.get("src", "").startswith("data:" + mime + ";base64,"))
                    self.assertEqual(node.attributes.get("alt"), "Daodan project logo")
                self.assertEqual(image.read_bytes(), payload)

    def test_images_reject_remote_absolute_traversal_missing_and_wrong_format_inputs(self):
        outside = self.directory / "outside.png"
        outside.write_bytes(png_bytes())
        bad = self.inputs / "bad.png"
        bad.write_bytes(b"not an image")
        for path in ("https://invalid.test/logo.png", "//invalid.test/logo.png", str(outside),
                     "../outside.png", "missing.png", "bad.png"):
            with self.subTest(path=path):
                document = valid_comparison()
                document["sample"]["image"] = {"path": path, "alt": "Project logo"}

                self.assert_rejected(document)
        self.assertEqual(outside.read_bytes(), png_bytes())

    def test_images_require_alt_text_and_reject_disguised_non_png_jpeg_data(self):
        for suffix, payload in (("svg", b'<svg xmlns="http://www.w3.org/2000/svg"/>'),
                                ("gif", b"GIF89a\x01\x00\x01\x00"),
                                ("png", b"<script>alert(1)</script>")):
            with self.subTest(suffix=suffix):
                image = self.inputs / ("unsupported." + suffix)
                image.write_bytes(payload)
                document = valid_comparison()
                document["sample"]["image"] = {"path": image.name, "alt": "Project logo"}

                self.assert_rejected(document)
        (self.inputs / "logo.png").write_bytes(png_bytes())
        document = valid_comparison()
        document["sample"]["image"] = {"path": "logo.png", "alt": ""}

        self.assert_rejected(document)

    def test_image_byte_and_pixel_bounds_fail_without_output(self):
        for name, payload in (("bytes.png", png_bytes() + b"\x00" * (4 * 1024 * 1024)),
                              ("pixels.png", png_bytes(5000, 5000))):
            with self.subTest(name=name):
                (self.inputs / name).write_bytes(payload)
                document = valid_comparison()
                document["sample"]["image"] = {"path": name, "alt": "Project logo"}

                self.assert_rejected(document)

    def test_directory_links_cannot_escape_the_input_directory(self):
        outside = self.directory / "outside-assets"
        outside.mkdir()
        (outside / "logo.png").write_bytes(png_bytes())
        alias = self.inputs / "linked-assets"
        try:
            alias.symlink_to(outside, target_is_directory=True)
        except OSError:
            if os.name != "nt":
                raise
            result = subprocess.run(["cmd", "/c", "mklink", "/J", str(alias), str(outside)],
                                    capture_output=True, text=True, timeout=15,
                                    creationflags=subprocess.CREATE_NO_WINDOW)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.addCleanup(lambda: (os.unlink if alias.is_symlink() else os.rmdir)(alias) if alias.exists() else None)
        document = valid_comparison()
        document["sample"]["image"] = {"path": "linked-assets/logo.png", "alt": "Project logo"}

        self.assert_rejected(document)
        self.assertEqual((outside / "logo.png").read_bytes(), png_bytes())

    def test_preview_and_selection_refuse_existing_outputs_without_replacement(self):
        for mode in ("preview", "selection"):
            with self.subTest(mode=mode):
                output = self.directory / (mode + (".html" if mode == "preview" else ".md"))
                output.write_bytes(b"Approved previous artifact\r\n")
                arguments = () if mode == "preview" else ("--select", "technical", "--authority", "user", "--source", "Q2")

                result, destination = self.run_cli(valid_comparison(), *arguments, output=output.name)

                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(destination.read_bytes(), b"Approved previous artifact\r\n")

    def test_preview_and_selection_preserve_same_path_and_hard_link_input_aliases(self):
        for mode in ("preview", "selection"):
            for alias_kind in ("same", "hardlink"):
                with self.subTest(mode=mode, alias=alias_kind):
                    document = valid_comparison()
                    self.input.write_text(json.dumps(document), encoding="utf-8")
                    output = self.input if alias_kind == "same" else self.inputs / (
                        mode + ("-alias.html" if mode == "preview" else "-alias.md"))
                    if alias_kind == "hardlink":
                        output.hardlink_to(self.input)
                    before = self.input.read_bytes()
                    arguments = () if mode == "preview" else ("--select", "technical", "--authority", "user", "--source", "Q2")
                    result = subprocess.run([sys.executable, "-B", str(SCRIPT), str(self.input), *arguments,
                                             "--out", str(output)], capture_output=True, text=True, timeout=30)

                    self.assertNotEqual(result.returncode, 0)
                    self.assertEqual(self.input.read_bytes(), before)
                    self.assertEqual(output.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
