"""V2 native-render gallery contracts through the actual comparison CLI.

Tiny PNG/JPEG containers and opaque retained-source bytes are seam fixtures.
They establish identity, confinement and publication, never native editability,
actual render derivation, artistic quality or a browser's visual result.
"""

import base64
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import zlib

from test_office_design_compare import Document, jpeg_bytes, png_bytes, valid_comparison
from test_office_records import records


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "plugins/office/skills/design/scripts/design_compare.py"
TEMP_ROOT = ROOT / "office-verification-tmp/taste-tests"
SELECT = ("--select", "technical", "--authority", "user", "--source", "Q7: choose technical")
MIB = 1024 * 1024


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical_digest(value):
    """Independent serialization specified by canonical-json-v1, not helper code."""
    return digest(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def refresh_bindings(document):
    """Author fresh fixture proofs after an intentional input change."""
    for candidate in document["candidates"]:
        for output, preview in candidate["previews"].items():
            preview["binding"] = {
                "candidate_id": candidate["id"], "design_revision": candidate["design"]["revision"],
                "design_sha256": canonical_digest(candidate["design"]),
                "content": copy.deepcopy(document["sample"]["content"]),
                "sample_sha256": canonical_digest(document["sample"]), "format": output,
            }
            # The sample binding contains identity/revision, not the editorial ID lists.
            if isinstance(preview["binding"]["content"], dict):
                preview["binding"]["content"] = {
                    key: document["sample"]["content"].get(key) for key in ("project_id", "revision")}


def creative_comparison(directory, formats=("docx", "pptx")):
    """Two complete proposals, two real-content jobs, exact local proof identities."""
    document = valid_comparison(formats)
    document["schema"] = "office/design-candidates/v2"
    document["sample"]["title"] = "Office content and composition: qualità"
    document["sample"]["content"] = {
        "project_id": document["project_id"], "revision": 1,
        "unit_ids": ["U1", "U2"], "claim_ids": ["C1", "C2"],
    }
    document["sample"]["evidence"] = [
        {"id": "EV1", "text": "Independent composition keeps DOCX reading and PPTX speaking distinct.",
         "source_refs": [{"source_id": "SRC1", "locator": "section 2"}]},
    ]
    document["sources"] = [{"id": "SRC1", "sha256": digest(b"Source brief, section 2"),
                            "provenance": "Source-backed Office ownership relation, section 2"}]
    document["representatives"] = {
        output: [{"slot_id": "opening", "roles": ["title", "lead"]},
                 {"slot_id": "reading", "roles": ["body", "source_note", "table", "evidence"]}]
        for output in formats
    }
    for index, candidate in enumerate(document["candidates"]):
        candidate["previews"] = {}
        for output in formats:
            source_name = f"{candidate['id']}-specimen.{output}"
            source_bytes = (f"Seam-only retained {output} source for {candidate['id']}. "
                            "Not an Office validity or editability fixture.\n").encode("utf-8")
            (directory / source_name).write_bytes(source_bytes)
            frames = []
            for slot_index, slot in enumerate(document["representatives"][output]):
                name = f"{candidate['id']}-{output}-{slot['slot_id']}.png"
                raw = png_bytes(3 + index, 2 + slot_index)
                (directory / name).write_bytes(raw)
                frames.append({
                    "slot_id": slot["slot_id"], "path": name, "sha256": digest(raw),
                    "alt": f"{candidate['id']} {output} {slot['slot_id']} seam image",
                    "provenance": {"kind": "native-render", "source": source_name,
                                   "source_sha256": digest(source_bytes), "locator": slot["slot_id"],
                                   "tool": "retained-render-fixture", "tool_version": "fixture-1",
                                   "capture_id": f"{candidate['id']}-{output}-{slot['slot_id']}"},
                })
            candidate["previews"][output] = {
                "binding": {}, "frames": frames,
                "assets": [{"id": "ASSET1", "sha256": digest(b"retained asset lineage"),
                            "provenance": "Supplied project asset, seam lineage only"}],
            }
    refresh_bindings(document)
    return document


def sized_png(size, marker=b"x"):
    """Valid PNG with an inert tEXt chunk, for exact encoded-byte boundaries."""
    raw = png_bytes(3, 2)
    padding = size - len(raw) - 12 - len(b"Fixture\x00")
    if padding < 0:
        raise ValueError("requested PNG is too small")
    payload = b"Fixture\x00" + marker * padding
    chunk = struct.pack(">I", len(payload)) + b"tEXt" + payload
    chunk += struct.pack(">I", zlib.crc32(b"tEXt" + payload))
    return raw[:-12] + chunk + raw[-12:]


class CreativeComparisonTests(unittest.TestCase):
    def setUp(self):
        TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        environment = mock.patch.dict(os.environ, {"TMP": str(TEMP_ROOT), "TEMP": str(TEMP_ROOT)})
        environment.start()
        self.addCleanup(environment.stop)
        temporary = tempfile.TemporaryDirectory(prefix="creative-comparison-", dir=TEMP_ROOT)
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.inputs = self.directory / "inputs"
        self.inputs.mkdir()
        self.input = self.inputs / "candidates.json"
        self.document = creative_comparison(self.inputs)
        self.sequence = 0

    def run_cli(self, document, *arguments, destination=None, audit_images=None):
        self.input.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")
        self.sequence += 1
        destination = destination or self.directory / f"result-{self.sequence}.html"
        command = [sys.executable, "-B", str(SCRIPT), str(self.input), *map(str, arguments),
                   "--out", str(destination)]
        if audit_images is not None:
            # Python's public audit stream observes real opens; no production collaborator is mocked.
            code = ("import collections,json,os,runpy,sys\n"
                    f"tracked = set({[str(path.resolve()) for path in audit_images]!r})\n"
                    "opened = collections.Counter()\n"
                    "def observe(event,args):\n"
                    "    if event == 'open' and isinstance(args[0], (str,bytes)):\n"
                    "        path = os.path.realpath(os.fsdecode(args[0]))\n"
                    "        if path in tracked: opened[path] += 1\n"
                    "sys.addaudithook(observe)\n"
                    "sys.argv = sys.argv[1:]\n"
                    "code = 0\n"
                    "try: runpy.run_path(sys.argv[0], run_name='__main__')\n"
                    "except SystemExit as stopped: code = stopped.code\n"
                    "print('TASTE_IMAGE_OPENS=' + json.dumps(opened, sort_keys=True))\n"
                    "sys.exit(code)\n")
            command = [sys.executable, "-B", "-c", code, *command[2:]]
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True,
                                encoding="utf-8", errors="replace", timeout=45)
        return result, destination

    def preview(self, document):
        result, destination = self.run_cli(document)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(destination.is_file())
        return Document(destination.read_text(encoding="utf-8"))

    def reject(self, document, *arguments):
        result, destination = self.run_cli(document, *arguments)
        self.assertNotEqual(result.returncode, 0, "Invalid v2 input was accepted")
        self.assertFalse(destination.exists(), "Rejected v2 input published an output")
        self.assertEqual(json.loads(self.input.read_text(encoding="utf-8")), document)

    def first_frame(self, document=None):
        return (document or self.document)["candidates"][0]["previews"]["docx"]["frames"][0]

    def sample_image(self, document, name="supplied.png", raw=None):
        raw = png_bytes(5, 2) if raw is None else raw
        (self.inputs / name).write_bytes(raw)
        document["sample"]["image"] = {"path": name, "alt": "Supplied project asset", "sha256": digest(raw)}
        refresh_bindings(document)

    def proof_images(self, rendered):
        return [node for node in rendered.elements if node.tag == "img"]

    def test_gallery_embeds_each_exact_proof_and_one_complete_readable_sample(self):
        rendered = self.preview(self.document)

        expected_images = []
        for candidate in self.document["candidates"]:
            self.assertIn(candidate["design"]["direction"]["idea"], rendered.root.text())
            for preview in candidate["previews"].values():
                for frame in preview["frames"]:
                    raw = (self.inputs / frame["path"]).read_bytes()
                    expected_images.append("data:image/png;base64," + base64.b64encode(raw).decode("ascii"))
                    self.assertIn(frame["provenance"]["capture_id"], rendered.root.text())
        self.assertCountEqual([node.attributes.get("src") for node in self.proof_images(rendered)], expected_images)
        sample = self.document["sample"]
        for text in [sample["lead"], sample["body"], sample["source_note"], sample["evidence"][0]["text"]]:
            self.assertEqual(rendered.root.text().count(text), 1, f"Common real content repeated or omitted: {text}")
        for text in [sample["title"], *sample["table"]["headers"],
                     *[cell for row in sample["table"]["rows"] for cell in row]]:
            self.assertIn(text, rendered.root.text())

    def test_requested_formats_and_flexible_representative_sets_control_the_gallery(self):
        for formats in (("docx",), ("pptx",)):
            for slots in (1, 3):
                with self.subTest(formats=formats, slots=slots):
                    document = creative_comparison(self.inputs, formats)
                    output = formats[0]
                    if slots == 1:
                        document["representatives"][output][0]["roles"] += document["representatives"][output][1]["roles"]
                        del document["representatives"][output][1:]
                        for candidate in document["candidates"]:
                            del candidate["previews"][output]["frames"][1:]
                    else:
                        document["representatives"][output].append({"slot_id": "detail", "roles": ["body"]})
                        for candidate in document["candidates"]:
                            frame = copy.deepcopy(candidate["previews"][output]["frames"][1])
                            frame["slot_id"] = "detail"
                            candidate["previews"][output]["frames"].append(frame)
                    rendered = self.preview(document)
                    self.assertEqual(len(self.proof_images(rendered)), 2 * slots)
                    self.assertEqual({node.attributes["data-format"] for node in rendered.frames()}, set(formats))

    def test_v2_accepts_authored_design_decisions_beyond_v1_css_recipes(self):
        document = copy.deepcopy(self.document)
        design = document["candidates"][0]["design"]
        design["components"].update(title="oversized flush title", callout="evidence lattice",
                                    quote="margin annotation", navigation="chapter folio")
        design["data"].update(table="open ledger", chart="native direct labels", source_notes="running notes")
        design["spacing"]["density"] = "editorial rhythm"
        design["imagery"]["treatment"] = "warm documentary with structural silhouettes"
        design["project_annotation"] = {"reason": "Complete authored native decisions"}
        refresh_bindings(document)

        self.preview(document)

    def test_supplied_png_and_jpeg_bytes_and_hashes_are_part_of_selection(self):
        for name, raw, mime in (("supplied.png", png_bytes(5, 2), "image/png"),
                                ("supplied.jpeg", jpeg_bytes(), "image/jpeg")):
            with self.subTest(name=name):
                document = copy.deepcopy(self.document)
                self.sample_image(document, name, raw)
                rendered = self.preview(document)
                embedded = "data:" + mime + ";base64," + base64.b64encode(raw).decode("ascii")
                self.assertEqual(sum(node.attributes.get("src") == embedded for node in self.proof_images(rendered)), 1)
                result, destination = self.run_cli(document, *SELECT)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                selected = records.load_record(destination)
                self.assertEqual(selected["selection"]["preview"]["sample_sha256"], canonical_digest(document["sample"]))
                if mime == "image/jpeg":
                    frame = self.first_frame(document)
                    frame.update(path=name, sha256=digest(raw))
                    rendered = self.preview(document)
                    self.assertEqual(sum(node.attributes.get("src") == embedded
                                         for node in self.proof_images(rendered)), 2)

    def test_absent_table_and_evidence_need_only_the_matching_nonempty_reasons(self):
        document = copy.deepcopy(self.document)
        document["sample"].update(table=None, evidence=[], not_applicable={
            "table": "The supplied source contains no tabular job.",
            "evidence": "This announcement has no separate evidence job."})
        for slots in document["representatives"].values():
            slots[1]["roles"] = ["body", "source_note"]
        refresh_bindings(document)

        self.preview(document)

        for excuse in ({}, {"table": "No table"}, {"table": " ", "evidence": "None"},
                       {"table": "None", "evidence": "None", "body": "Skip dense content"}):
            changed = copy.deepcopy(document)
            changed["sample"]["not_applicable"] = excuse
            refresh_bindings(changed)
            with self.subTest(excuse=excuse):
                self.reject(changed)
        present = copy.deepcopy(self.document)
        present["sample"]["not_applicable"] = {"table": "Ignore the present table"}
        refresh_bindings(present)
        self.reject(present)

    def test_explicit_user_and_autonomous_selection_save_exact_original_proof_fingerprints(self):
        for authority in ("user", "autonomous"):
            with self.subTest(authority=authority):
                document = copy.deepcopy(self.document)
                source = "Q7 user's exact answer" if authority == "user" else "Existing authorized visual autonomy"
                result, destination = self.run_cli(document, "--select", "technical", "--authority", authority,
                                                   "--source", source)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                candidate = document["candidates"][1]
                expected = copy.deepcopy(candidate["design"])
                expected["selection"] = {"candidate_id": "technical", "authority": authority, "source": source,
                    "preview": {"comparison_sha256": canonical_digest(document), "hash_mode": "canonical-json-v1",
                                "sample_sha256": canonical_digest(document["sample"]),
                                "design_sha256": canonical_digest(candidate["design"]),
                                "frames": {output: [{"slot_id": frame["slot_id"], "sha256": frame["sha256"]}
                                                     for frame in preview["frames"]]
                                           for output, preview in candidate["previews"].items()}}}
                self.assertEqual(records.load_record(destination), expected)
                self.assertEqual(records.validate_design(expected), [])

    def test_preview_is_inert_self_contained_keyboard_accessible_and_truthfully_limited(self):
        rendered = self.preview(self.document)

        self.assertTrue(all("selection" not in candidate["design"] for candidate in self.document["candidates"]))
        self.assertFalse(list(self.directory.glob("*.md")))
        self.assertEqual(json.loads(self.input.read_text(encoding="utf-8")), self.document)
        self.assertFalse(any(node.tag in {"script", "iframe", "object", "embed", "form", "link"}
                             for node in rendered.elements))
        policy = next(node.attributes["content"] for node in rendered.elements
                      if node.tag == "meta" and node.attributes.get("http-equiv", "").lower() == "content-security-policy")
        self.assertIn("default-src 'none'", policy)
        self.assertIn("img-src data:", policy)
        links = [node.attributes["href"] for node in rendered.elements if node.tag == "a"]
        anchors = {node.attributes["id"] for node in rendered.elements if "id" in node.attributes}
        self.assertGreaterEqual(len(links), len(self.document["candidates"]))
        self.assertTrue(all(link.startswith("#") and link[1:] in anchors for link in links))
        self.assertRegex(rendered.css(), r":focus(?:-visible)?")
        self.assertRegex(rendered.root.text().lower(), r"(?:separate|independent|not|doesn.t).{0,150}(?:editability|derivation|quality|fidelity)")

    def test_preview_keeps_intrinsic_image_ratios_and_does_not_restyle_pixels(self):
        rendered = self.preview(self.document)

        for image in self.proof_images(rendered):
            raw = base64.b64decode(image.attributes["src"].split(",", 1)[1], validate=True)
            width, height = struct.unpack_from(">II", raw, 16)
            attributes = image.attributes
            if "width" in attributes and "height" in attributes:
                self.assertAlmostEqual(float(attributes["width"]) / float(attributes["height"]), width / height)
            self.assertNotRegex(attributes.get("style", ""), r"(?i)(filter|clip-path|transform)\s*:")
        self.assertNotRegex(rendered.css(), r"(?i)object-fit\s*:\s*cover|(?:filter|clip-path)\s*:\s*(?!none\b)")

    def test_nested_untrusted_text_is_escaped_and_never_becomes_markup(self):
        document = copy.deepcopy(self.document)
        attack = '<script id="injected">bad()</script><img src=x onerror="bad()">'
        document["sample"]["body"] += attack
        document["sample"]["evidence"][0]["text"] += attack
        document["sources"][0]["provenance"] += attack
        document["candidates"][0]["design"]["direction"]["idea"] += attack
        frame = self.first_frame(document)
        frame["alt"] += attack
        frame["provenance"]["locator"] += attack
        document["candidates"][0]["previews"]["docx"]["assets"][0]["provenance"] += attack
        refresh_bindings(document)

        rendered = self.preview(document)

        self.assertIn(attack, rendered.root.text())
        self.assertFalse(any(node.attributes.get("id") == "injected" or node.tag == "script"
                             or any(key.lower().startswith("on") for key in node.attributes)
                             for node in rendered.elements))
        self.assertTrue(all(node.attributes.get("src", "").startswith("data:image/")
                            for node in self.proof_images(rendered)))

    def test_invalid_fonts_palette_and_design_records_still_fail_v2(self):
        for owner, field, invalid in (("palette", "accent", "red; background:url(https://invalid)"),
                                       ("components", "title", "x;position:fixed")):
            document = copy.deepcopy(self.document)
            document["candidates"][0]["design"][owner][field] = invalid
            refresh_bindings(document)
            with self.subTest(field=field):
                self.reject(document)
        document = copy.deepcopy(self.document)
        document["candidates"][0]["design"]["typography"]["body"]["family"] = 'Arial";url(https://invalid)'
        refresh_bindings(document)
        self.reject(document)

    def test_missing_sample_data_identity_and_referenced_sources_fail_without_invented_content(self):
        for field in ("title", "lead", "body", "source_note", "content", "evidence", "table"):
            document = copy.deepcopy(self.document)
            del document["sample"][field]
            if field == "content":
                for candidate in document["candidates"]:
                    for preview in candidate["previews"].values():
                        preview["binding"]["sample_sha256"] = canonical_digest(document["sample"])
            else:
                refresh_bindings(document)
            with self.subTest(missing=field):
                self.reject(document)
        for field, invalid in (("project_id", "other-project"), ("revision", 0),
                               ("unit_ids", ["U1", "U1"]), ("claim_ids", [""])):
            document = copy.deepcopy(self.document)
            document["sample"]["content"][field] = invalid
            refresh_bindings(document)
            with self.subTest(content=field):
                self.reject(document)
        document = copy.deepcopy(self.document)
        document["sample"]["evidence"][0]["source_refs"][0]["source_id"] = "UNKNOWN"
        refresh_bindings(document)
        self.reject(document)
        for table in ({"headers": [], "rows": [["Unlabeled"]]},
                      {"headers": ["Column"], "rows": [["One", "Extra"]]},
                      {"headers": ["Column"], "rows": [[""]]}):
            document = copy.deepcopy(self.document)
            document["sample"]["table"] = table
            refresh_bindings(document)
            with self.subTest(table=table):
                self.reject(document)

    def test_candidate_count_identity_requested_formats_and_unselected_state_are_enforced(self):
        changes = [lambda d: d["candidates"].pop(),
                   lambda d: d["candidates"].extend(copy.deepcopy(d["candidates"])),
                   lambda d: d["candidates"][1].update(id="editorial"),
                   lambda d: d["candidates"][0]["design"].update(project_id="foreign"),
                   lambda d: d["candidates"][0]["design"].update(formats=["docx"]),
                   lambda d: d["candidates"][0]["design"].update(selection={
                       "candidate_id": "editorial", "authority": "user", "source": "Fake approval"})]
        for index, change in enumerate(changes):
            document = copy.deepcopy(self.document)
            change(document)
            refresh_bindings(document)
            with self.subTest(case=index):
                self.reject(document)

    def test_every_proof_binding_matches_its_actual_candidate_content_sample_and_format(self):
        for field, invalid in (("candidate_id", "technical"), ("design_revision", 2),
                               ("design_sha256", "0" * 64), ("sample_sha256", "0" * 64),
                               ("format", "pptx"), ("content", {"project_id": "foreign", "revision": 1}),
                               ("content", {"project_id": self.document["project_id"], "revision": 2})):
            document = copy.deepcopy(self.document)
            document["candidates"][0]["previews"]["docx"]["binding"][field] = invalid
            with self.subTest(field=field, invalid=invalid):
                self.reject(document)
                self.reject(document, *SELECT)
        for field in ("direction", "content"):
            document = copy.deepcopy(self.document)
            if field == "direction":
                document["candidates"][0]["design"][field]["idea"] = "Changed after render"
            else:
                document["candidates"][0]["design"][field]["revision"] = 2
            self.reject(document)

    def test_every_present_reading_role_needs_a_representative_for_each_format(self):
        for role in ("title", "lead", "body", "source_note", "table", "evidence"):
            document = copy.deepcopy(self.document)
            for slot in document["representatives"]["pptx"]:
                slot["roles"] = [item for item in slot["roles"] if item != role]
            with self.subTest(role=role):
                self.reject(document)
        document = copy.deepcopy(self.document)
        document["representatives"]["docx"][0]["roles"].append("invented-chart")
        self.reject(document)

    def test_missing_reordered_duplicate_or_unrequested_slots_and_formats_fail(self):
        changes = [lambda d: d["representatives"].pop("pptx"),
                   lambda d: d["representatives"].update(pdf=d["representatives"]["docx"]),
                   lambda d: d["representatives"].update(docx=[]),
                   lambda d: d["representatives"]["docx"].extend(d["representatives"]["docx"]),
                   lambda d: d["representatives"]["docx"][1].update(slot_id="opening"),
                   lambda d: d["candidates"][0]["previews"].pop("pptx"),
                   lambda d: d["candidates"][0]["previews"].update(pdf={}),
                   lambda d: d["candidates"][0]["previews"]["docx"]["frames"].pop(),
                   lambda d: d["candidates"][0]["previews"]["docx"]["frames"].reverse(),
                   lambda d: d["candidates"][0]["previews"]["docx"]["frames"][1].update(slot_id="opening")]
        for index, change in enumerate(changes):
            document = copy.deepcopy(self.document)
            change(document)
            with self.subTest(case=index):
                self.reject(document)

    def test_reused_frame_digest_vectors_cannot_pass_as_a_second_candidate(self):
        document = copy.deepcopy(self.document)
        original = document["candidates"][0]["previews"]["docx"]["frames"]
        copied = document["candidates"][1]["previews"]["docx"]["frames"]
        for first, second in zip(original, copied):
            second["path"], second["sha256"] = first["path"], first["sha256"]

        self.reject(document)
        self.reject(document, *SELECT)

    def test_source_asset_and_evidence_lineage_has_real_ids_digests_and_inert_provenance(self):
        changes = [lambda d: d["sources"].append(copy.deepcopy(d["sources"][0])),
                   lambda d: d["sources"][0].update(sha256="bad"),
                   lambda d: d["sources"][0].update(provenance=" "),
                   lambda d: d["sample"]["evidence"][0].update(source_refs=[]),
                   lambda d: d["sample"]["evidence"][0]["source_refs"][0].update(locator=""),
                   lambda d: d["sample"]["evidence"].append(copy.deepcopy(d["sample"]["evidence"][0])),
                   lambda d: d["candidates"][0]["previews"]["docx"]["assets"][0].update(sha256="bad"),
                   lambda d: d["candidates"][0]["previews"]["docx"]["assets"][0].update(provenance={"url": "remote"}),
                   lambda d: d["candidates"][0]["previews"]["docx"]["assets"].append(
                       copy.deepcopy(d["candidates"][0]["previews"]["docx"]["assets"][0]))]
        for index, change in enumerate(changes):
            document = copy.deepcopy(self.document)
            change(document)
            refresh_bindings(document)
            with self.subTest(case=index):
                self.reject(document)
        document = copy.deepcopy(self.document)
        document["candidates"][0]["previews"]["docx"]["assets"] = []
        self.preview(document)
        assets = [{"id": f"A{index}", "sha256": "a" * 64, "provenance": "Retained source"} for index in range(20)]
        document["candidates"][0]["previews"]["docx"]["assets"] = assets
        self.preview(document)
        assets.append({"id": "A20", "sha256": "b" * 64, "provenance": "One beyond the bound"})
        self.reject(document)

    def test_new_wrapper_and_preview_objects_reject_unknown_keys(self):
        def targets(document):
            candidate = document["candidates"][0]
            preview = candidate["previews"]["docx"]
            return [document, document["sample"], document["sample"]["content"], document["sample"]["table"],
                    document["sample"]["evidence"][0], document["sample"]["evidence"][0]["source_refs"][0],
                    document["sources"][0], document["representatives"]["docx"][0], candidate, preview,
                    preview["binding"], preview["binding"]["content"], preview["frames"][0],
                    preview["frames"][0]["provenance"], preview["assets"][0]]
        for index in range(len(targets(self.document))):
            document = copy.deepcopy(self.document)
            targets(document)[index]["verified_quality"] = True
            # Keep other fingerprints current so this is a shape check, not a stale-hash check.
            old_binding = copy.deepcopy(document["candidates"][0]["previews"]["docx"]["binding"])
            refresh_bindings(document)
            if index in (10, 11):
                document["candidates"][0]["previews"]["docx"]["binding"] = old_binding
            with self.subTest(object=index):
                self.reject(document)
        document = copy.deepcopy(self.document)
        self.sample_image(document)
        document["sample"]["image"]["verified"] = True
        refresh_bindings(document)
        self.reject(document)

    def test_replacing_sample_image_frame_or_native_source_bytes_invalidates_both_commands(self):
        for changed in ("sample", "frame", "source"):
            with self.subTest(changed=changed):
                document = creative_comparison(self.inputs)
                self.sample_image(document)
                frame = self.first_frame(document)
                path = (document["sample"]["image"]["path"] if changed == "sample" else
                        frame["path"] if changed == "frame" else frame["provenance"]["source"])
                (self.inputs / path).write_bytes(png_bytes(8, 3) if changed != "source" else b"Changed source bytes")
                self.reject(document)
                self.reject(document, *SELECT)

    def test_malformed_native_provenance_and_wrong_native_format_are_rejected(self):
        for field, invalid in (("kind", "imagegen"), ("source_sha256", "bad"), ("source_sha256", "0" * 64),
                               ("locator", ""), ("tool", ""), ("tool_version", None), ("capture_id", "")):
            document = copy.deepcopy(self.document)
            self.first_frame(document)["provenance"][field] = invalid
            with self.subTest(field=field, invalid=invalid):
                self.reject(document)
        for field in self.first_frame()["provenance"]:
            document = copy.deepcopy(self.document)
            del self.first_frame(document)["provenance"][field]
            with self.subTest(missing=field):
                self.reject(document)
        document = copy.deepcopy(self.document)
        self.first_frame(document)["provenance"]["source"] = "editorial-specimen.pptx"
        self.first_frame(document)["provenance"]["source_sha256"] = digest((self.inputs / "editorial-specimen.pptx").read_bytes())
        self.reject(document)

    def test_image_paths_and_native_source_paths_reject_every_escape_class(self):
        paths = ("https://example.invalid/proof.png", "/absolute/proof.png", "C:\\proof.png", "C:proof.png",
                 "\\\\server\\share\\proof.png", "../outside.png", "..\\outside.png", "proof.png:stream", "missing.png")
        for target in ("sample", "frame", "source"):
            for path in paths:
                document = copy.deepcopy(self.document)
                self.sample_image(document)
                if target == "sample":
                    document["sample"]["image"]["path"] = path
                    refresh_bindings(document)
                elif target == "frame":
                    self.first_frame(document)["path"] = path
                else:
                    self.first_frame(document)["provenance"]["source"] = path.replace(".png", ".docx")
                with self.subTest(target=target, path=path):
                    self.reject(document)

    def test_directory_links_cannot_escape_for_frames_sample_images_or_native_sources(self):
        outside = self.directory / "outside"
        outside.mkdir()
        raw, native = png_bytes(3, 2), b"Outside retained specimen"
        (outside / "proof.png").write_bytes(raw)
        (outside / "specimen.docx").write_bytes(native)
        alias = self.inputs / "linked"
        try:
            alias.symlink_to(outside, target_is_directory=True)
        except OSError:
            if os.name != "nt":
                raise
            result = subprocess.run(["cmd", "/c", "mklink", "/J", str(alias), str(outside)],
                                    capture_output=True, text=True, timeout=15,
                                    creationflags=subprocess.CREATE_NO_WINDOW)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.addCleanup(lambda: os.rmdir(alias) if alias.exists() else None)
        for target in ("sample", "frame", "source"):
            document = copy.deepcopy(self.document)
            if target == "sample":
                document["sample"]["image"] = {"path": "linked/proof.png", "alt": "Outside", "sha256": digest(raw)}
                refresh_bindings(document)
            elif target == "frame":
                self.first_frame(document).update(path="linked/proof.png", sha256=digest(raw))
            else:
                self.first_frame(document)["provenance"].update(source="linked/specimen.docx", source_sha256=digest(native))
            with self.subTest(target=target):
                self.reject(document)
                self.reject(document, *SELECT)
        self.assertEqual((outside / "proof.png").read_bytes(), raw)
        self.assertEqual((outside / "specimen.docx").read_bytes(), native)

    def test_image_containers_alt_text_hashes_and_per_image_bounds_apply_to_proofs(self):
        invalid_images = [b"GIF89a", png_bytes()[:-7], jpeg_bytes()[:-2],
                          png_bytes(5000, 4000), sized_png(4 * MIB + 1)]
        bad_crc = bytearray(png_bytes())
        bad_crc[29] ^= 1
        invalid_images.append(bytes(bad_crc))
        for index, raw in enumerate(invalid_images):
            document = copy.deepcopy(self.document)
            frame = self.first_frame(document)
            (self.inputs / frame["path"]).write_bytes(raw)
            frame["sha256"] = digest(raw)
            with self.subTest(container=index):
                self.reject(document)
        creative_comparison(self.inputs)
        for field, invalid in (("alt", " "), ("sha256", "bad"), ("sha256", "0" * 64)):
            document = copy.deepcopy(self.document)
            self.first_frame(document)[field] = invalid
            with self.subTest(field=field):
                self.reject(document)
        document = copy.deepcopy(self.document)
        self.first_frame(document)["path"] = "proof.svg"
        (self.inputs / "proof.svg").write_bytes(png_bytes())
        self.first_frame(document)["sha256"] = digest(png_bytes())
        self.reject(document)

    def test_sample_image_requires_its_exact_v2_shape_and_current_raw_digest(self):
        for invalid in ({"path": "supplied.png", "alt": "Asset"},
                        {"path": "supplied.png", "alt": "Asset", "sha256": "bad"},
                        {"path": "supplied.png", "alt": "Asset", "sha256": "0" * 64},
                        {"path": "supplied.png", "alt": "", "sha256": digest(png_bytes())}):
            document = copy.deepcopy(self.document)
            (self.inputs / "supplied.png").write_bytes(png_bytes())
            document["sample"]["image"] = invalid
            refresh_bindings(document)
            with self.subTest(image=invalid):
                self.reject(document)
                self.reject(document, *SELECT)

    def test_native_sources_are_bounded_at_64_mib_without_execution_or_unpacking(self):
        document = copy.deepcopy(self.document)
        source = self.inputs / "bounded.docx"
        with source.open("wb") as stream:
            stream.truncate(64 * MIB)
        source_hash = hashlib.sha256()
        with source.open("rb") as stream:
            while chunk := stream.read(MIB):
                source_hash.update(chunk)
        self.first_frame(document)["provenance"].update(source=source.name, source_sha256=source_hash.hexdigest())

        self.preview(document)

        with source.open("ab") as stream:
            stream.write(b"x")
        source_hash.update(b"x")
        self.first_frame(document)["provenance"]["source_sha256"] = source_hash.hexdigest()
        self.reject(document)
        self.reject(document, *SELECT)

    def repeated_large_images(self):
        document = creative_comparison(self.inputs, ("docx",))
        for index, candidate in enumerate(document["candidates"]):
            raw = sized_png(4 * MIB, bytes([97 + index]))
            name = f"repeated-{index}.png"
            (self.inputs / name).write_bytes(raw)
            for frame in candidate["previews"]["docx"]["frames"]:
                frame.update(path=name, sha256=digest(raw))
        return document

    def test_aggregate_limit_accepts_16_mib_and_counts_reused_frame_occurrences_and_sample(self):
        document = self.repeated_large_images()

        rendered = self.preview(document)

        self.assertEqual(len(self.proof_images(rendered)), 4)
        # There are only 8 MiB of distinct files, but 16 MiB of frame embeds.
        self.sample_image(document, raw=png_bytes())
        self.reject(document)
        self.reject(document, *SELECT)

    def test_each_actual_image_is_opened_once_even_when_reused_across_frames_and_sample(self):
        document = copy.deepcopy(self.document)
        tracked = []
        for candidate in document["candidates"]:
            first = candidate["previews"]["docx"]["frames"][0]
            tracked.append(self.inputs / first["path"])
            for preview in candidate["previews"].values():
                for frame in preview["frames"]:
                    frame.update(path=first["path"], sha256=first["sha256"])
        first = self.first_frame(document)
        document["sample"]["image"] = {"path": first["path"], "alt": "Reused supplied asset", "sha256": first["sha256"]}
        refresh_bindings(document)

        result, destination = self.run_cli(document, audit_images=tracked)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        line = next(line for line in result.stdout.splitlines() if line.startswith("TASTE_IMAGE_OPENS="))
        self.assertEqual(json.loads(line.split("=", 1)[1]), {str(path.resolve()): 1 for path in tracked})
        self.assertEqual(len(self.proof_images(Document(destination.read_text(encoding="utf-8")))), 9)

    def test_an_authored_combination_requires_explicit_parents_new_revision_and_fresh_proofs(self):
        document = copy.deepcopy(self.document)
        for output, slots in document["representatives"].items():
            slots.append({"slot_id": "detail", "roles": ["body"]})
            for candidate in document["candidates"]:
                frame = copy.deepcopy(candidate["previews"][output]["frames"][1])
                frame["slot_id"] = "detail"
                candidate["previews"][output]["frames"].append(frame)
        combined = copy.deepcopy(document["candidates"][0])
        combined.update(id="combined", parent_ids=["editorial", "technical"])
        combined["design"]["revision"] = 2
        combined["design"]["direction"]["idea"] = "Authored combination with independently retained specimens"
        for output, preview in combined["previews"].items():
            source_name = f"combined-specimen.{output}"
            source_bytes = f"New combined {output} seam specimen, not native fidelity proof".encode("utf-8")
            (self.inputs / source_name).write_bytes(source_bytes)
            for index, frame in enumerate(preview["frames"]):
                raw = png_bytes(7, 2 + index)
                name = f"combined-{output}-{index}.png"
                (self.inputs / name).write_bytes(raw)
                frame.update(path=name, sha256=digest(raw))
                frame["provenance"].update(source=source_name, source_sha256=digest(source_bytes),
                                           capture_id=f"combined-{output}-{index}")
        document["candidates"].append(combined)
        refresh_bindings(document)

        rendered = self.preview(document)
        self.assertEqual(len(self.proof_images(rendered)), 18)
        result, destination = self.run_cli(document, "--select", "combined", "--authority", "user", "--source", "Q8")

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        selected = records.load_record(destination)
        self.assertEqual(selected["selection"]["parent_ids"], ["editorial", "technical"])
        self.assertEqual(selected["selection"]["candidate_id"], "combined")
        self.assertEqual(selected["revision"], 2)
        for parents in (["editorial", "unknown"], ["editorial", "editorial"], ["editorial", "combined"], []):
            invalid = copy.deepcopy(document)
            invalid["candidates"][2]["parent_ids"] = parents
            with self.subTest(parents=parents):
                self.reject(invalid)
        stale = copy.deepcopy(document)
        stale["candidates"][2]["design"]["revision"] = 1
        refresh_bindings(stale)
        self.reject(stale)

    def test_selection_needs_a_known_candidate_valid_authority_and_nonempty_source(self):
        for arguments in (("--select", "unknown", "--authority", "user", "--source", "Q7"),
                          ("--select", "technical", "--authority", "browser", "--source", "Q7"),
                          ("--select", "technical", "--authority", "user"),
                          ("--select", "technical", "--source", "Q7"),
                          ("--select", "technical", "--authority", "user", "--source", " "),
                          ("--authority", "user", "--source", "Implicit choice")):
            with self.subTest(arguments=arguments):
                self.reject(self.document, *arguments)

    def test_preview_and_selection_preserve_existing_output_and_all_input_aliases(self):
        document = copy.deepcopy(self.document)
        self.sample_image(document)
        for arguments in ((), SELECT):
            destination = self.directory / f"prior-{len(arguments)}.html"
            destination.write_bytes(b"Previously approved artifact\r\n")
            result, _ = self.run_cli(document, *arguments, destination=destination)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(destination.read_bytes(), b"Previously approved artifact\r\n")
            self.input.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")
            frame = self.first_frame(document)
            targets = [self.input, self.inputs / document["sample"]["image"]["path"],
                       self.inputs / frame["path"], self.inputs / frame["provenance"]["source"]]
            for index, target in enumerate(targets):
                for alias_kind in ("same", "hardlink"):
                    with self.subTest(command=arguments, target=index, alias=alias_kind):
                        alias = target if alias_kind == "same" else self.inputs / f"alias-{len(arguments)}-{index}.out"
                        if alias_kind == "hardlink":
                            alias.hardlink_to(target)
                        before = target.read_bytes()
                        result, _ = self.run_cli(document, *arguments, destination=alias)
                        self.assertNotEqual(result.returncode, 0)
                        self.assertEqual(target.read_bytes(), before)
                        self.assertEqual(alias.read_bytes(), before)

    def test_nested_duplicate_json_keys_nonfinite_numbers_and_malformed_json_publish_nothing(self):
        text = json.dumps(self.document)
        duplicate = text.replace('"capture_id":', '"capture_id": "duplicate", "capture_id":', 1)
        nonfinite = text.replace('"design_revision": 1', '"design_revision": NaN', 1)
        for index, raw in enumerate((duplicate, nonfinite, "{broken")):
            with self.subTest(raw=index):
                self.input.write_text(raw, encoding="utf-8")
                destination = self.directory / f"bad-json-{index}.html"
                result = subprocess.run([sys.executable, "-B", str(SCRIPT), str(self.input), "--out", str(destination)],
                                        cwd=ROOT, capture_output=True, text=True, timeout=30)
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(destination.exists())
                self.assertEqual(self.input.read_text(encoding="utf-8"), raw)


if __name__ == "__main__":
    unittest.main()
