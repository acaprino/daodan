"""Optional original-choice fingerprints at the public DESIGN record boundary.

These are historical provenance, not proof of current native render derivation.
The frozen v1 suite remains the owner of the underlying DESIGN requirements.
"""

import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from test_office_records import records, valid_design


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "plugins/office/skills/content/scripts/office_records.py"
TEMP_ROOT = ROOT / "office-verification-tmp/taste-tests"


def valid_preview():
    """Original selection fingerprints, deliberately unrelated to current bytes."""
    return {
        "comparison_sha256": "a" * 64,
        "hash_mode": "canonical-json-v1",
        "sample_sha256": "b" * 64,
        "design_sha256": "c" * 64,
        "frames": {
            "docx": [{"slot_id": "opening", "sha256": "d" * 64},
                     {"slot_id": "reading", "sha256": "e" * 64}],
            "pptx": [{"slot_id": "opening", "sha256": "f" * 64}],
        },
    }


class CreativeDesignRecordTests(unittest.TestCase):
    def setUp(self):
        TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        environment = mock.patch.dict(os.environ, {"TMP": str(TEMP_ROOT), "TEMP": str(TEMP_ROOT)})
        environment.start()
        self.addCleanup(environment.stop)
        temporary = tempfile.TemporaryDirectory(prefix="creative-records-", dir=TEMP_ROOT)
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)

    def selected(self):
        design = valid_design()
        design["selection"]["preview"] = valid_preview()
        return design

    def assert_invalid_preview(self, preview):
        design = valid_design()
        design["selection"]["preview"] = preview
        before = copy.deepcopy(design)

        errors = records.validate_design(design)

        self.assertTrue(errors, "Malformed original-choice fingerprints were accepted")
        self.assertTrue(all(isinstance(error, str) and error for error in errors))
        self.assertEqual(design, before, "Validation changed the caller's design")

    def test_optional_preview_round_trips_exactly_without_inventing_render_authority(self):
        design = self.selected()
        destination = self.directory / "DESIGN.md"
        before = copy.deepcopy(design)

        self.assertEqual(records.validate_design(design), [])
        records.write_record(design, destination)
        loaded = records.load_record(destination)

        self.assertEqual(loaded, before)
        self.assertEqual(design, before)

    def test_legacy_selected_and_unselected_designs_remain_valid(self):
        design = valid_design()

        self.assertEqual(records.validate_design(design), [])
        del design["selection"]

        self.assertEqual(records.validate_design(design, require_selected=False), [])
        self.assertNotIn("selection", design)

    def test_rebinding_keeps_original_hashes_and_original_format_keys(self):
        design = self.selected()
        fingerprints = copy.deepcopy(design["selection"]["preview"])
        design["revision"] = 5
        design["content"]["revision"] = 8
        design["formats"] = ["docx"]
        del design["adaptations"]["pptx"]
        destination = self.directory / "inherited-DESIGN.md"

        self.assertEqual(records.validate_design(design), [])
        records.write_record(design, destination)

        self.assertEqual(records.load_record(destination)["selection"]["preview"], fingerprints)
        self.assertEqual(set(fingerprints["frames"]), {"docx", "pptx"})

    def test_preview_requires_an_object_complete_fields_and_known_hash_mode(self):
        for invalid in (None, [], "proof", False):
            with self.subTest(shape=invalid):
                self.assert_invalid_preview(invalid)
        for field in valid_preview():
            preview = valid_preview()
            del preview[field]
            with self.subTest(missing=field):
                self.assert_invalid_preview(preview)
        for mode in ("file-bytes", "canonical-json-v2", "", None):
            preview = valid_preview()
            preview["hash_mode"] = mode
            with self.subTest(mode=mode):
                self.assert_invalid_preview(preview)

    def test_every_preview_digest_requires_a_sha256_value(self):
        for field in ("comparison_sha256", "sample_sha256", "design_sha256"):
            for invalid in ("", "a" * 63, "g" * 64, 42, None):
                preview = valid_preview()
                preview[field] = invalid
                with self.subTest(field=field, value=invalid):
                    self.assert_invalid_preview(preview)
        preview = valid_preview()
        preview["frames"]["docx"][0]["sha256"] = "not-a-digest"
        self.assert_invalid_preview(preview)

    def test_frames_require_supported_formats_and_populated_unique_slots(self):
        for frames in ({}, [], {"pdf": [{"slot_id": "opening", "sha256": "d" * 64}]},
                       {"docx": []}, {"pptx": "frame"}, {"docx": [None]},
                       {"docx": [{"sha256": "d" * 64}]},
                       {"docx": [{"slot_id": " ", "sha256": "d" * 64}]},
                       {"docx": [{"slot_id": "opening"}]},
                       {"docx": [{"slot_id": "opening", "sha256": "d" * 64}] * 2}):
            preview = valid_preview()
            preview["frames"] = frames
            with self.subTest(frames=frames):
                self.assert_invalid_preview(preview)

    def test_unknown_preview_and_frame_keys_fail_without_restricting_design_extensions(self):
        for location in ("preview", "frame"):
            preview = valid_preview()
            target = preview if location == "preview" else preview["frames"]["docx"][0]
            target["verified_native"] = True
            with self.subTest(location=location):
                self.assert_invalid_preview(preview)
        design = self.selected()
        design["project_annotation"] = {"owner": "Office maintainer"}

        self.assertEqual(records.validate_design(design), [])

    def test_bad_preview_is_rejected_even_when_selected_requirement_is_disabled(self):
        design = self.selected()
        design["selection"]["preview"]["hash_mode"] = "unknown"

        self.assertTrue(records.validate_design(design, require_selected=False))

    def test_invalid_preview_cannot_be_written_through_api_or_cli(self):
        design = self.selected()
        design["selection"]["preview"]["frames"]["pptx"][0]["sha256"] = "stale"
        input_path = self.directory / "input.json"
        input_path.write_text(json.dumps(design), encoding="utf-8")
        destination = self.directory / "rejected-DESIGN.md"
        original = input_path.read_bytes()

        with self.assertRaises(ValueError):
            records.write_record(design, destination)
        result = subprocess.run([sys.executable, "-B", str(SCRIPT), "write", str(input_path),
                                 "--out", str(destination)], cwd=ROOT, capture_output=True,
                                text=True, timeout=30)

        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse(destination.exists())
        self.assertEqual(input_path.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
