"""Pins model_capabilities.py: one vocabulary, read the same way from every host shape."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "plugins/model-routing/skills/model-routing/scripts"))

import model_capabilities as mc  # noqa: E402


class TestNormalize(unittest.TestCase):
    def test_an_opencode_config_entry_exposes_every_declared_capability(self):
        view = mc.normalize({"tool_call": True, "reasoning": True, "attachment": True,
                             "temperature": False, "interleaved": {"field": "reasoning_content"},
                             "modalities": {"input": ["text", "image", "video", "pdf"],
                                            "output": ["text"]}})
        self.assertEqual(view["input"], ["text", "image", "video", "pdf"])
        self.assertEqual(view["output"], ["text"])
        self.assertEqual(view["features"], {"tool_call": True, "reasoning": True,
                                            "attachment": True, "structured_output": None,
                                            "temperature": False, "interleaved": True})
        self.assertEqual(view["interleaved_field"], "reasoning_content")

    def test_a_declared_false_stays_false_and_an_absent_value_stays_unknown(self):
        # models.dev marks a model that refuses the parameter with `temperature: false`;
        # reading presence instead of value made it true in the catalog.
        view = mc.normalize({"temperature": False})
        self.assertIs(view["features"]["temperature"], False)
        self.assertIsNone(view["features"]["tool_call"])
        self.assertIsNone(view["input"])
        self.assertIsNone(mc.has(view, "input.video"))

    def test_a_pi_entry_declares_its_input_list(self):
        view = mc.normalize({"reasoning": True, "input": ["text", "image"]})
        self.assertEqual(view["input"], ["text", "image"])
        self.assertIsNone(view["output"])
        self.assertIs(view["features"]["reasoning"], True)

    def test_a_catalog_view_reads_back_unchanged_including_the_older_interleaved_shape(self):
        stored = {"input": ["text"], "output": ["text"],
                  "features": {"tool_call": True, "interleaved": {"field": "reasoning"}},
                  "reasoning_options": [], "effort_levels": []}
        view = mc.normalize(stored)
        self.assertIs(view["features"]["interleaved"], True)
        self.assertEqual(view["interleaved_field"], "reasoning")
        self.assertEqual(mc.normalize(view), view)

    def test_a_host_spelling_of_a_modality_is_read_as_the_vocabulary_name(self):
        view = mc.normalize({"modalities": {"input": ["Text", "file"]}})
        self.assertEqual(view["input"], ["text", "pdf"])


class TestRequirements(unittest.TestCase):
    def test_every_name_of_the_vocabulary_is_answerable(self):
        view = mc.normalize({"tool_call": False, "reasoning": False, "attachment": False,
                             "structured_output": False, "temperature": False,
                             "interleaved": False,
                             "modalities": {"input": ["text"], "output": ["text"]}})
        for requirement in mc.VOCABULARY:
            self.assertIsNotNone(mc.has(view, requirement), requirement)

    def test_output_non_text_is_any_output_besides_text(self):
        self.assertIs(mc.has(mc.normalize({"modalities": {"output": ["text", "audio"]}}),
                             "output.non_text"), True)
        self.assertIs(mc.has(mc.normalize({"modalities": {"output": ["text"]}}),
                             "output.non_text"), False)

    def test_a_name_outside_the_vocabulary_is_reported(self):
        self.assertEqual(mc.unknown_requirements(["input.video", "input.vidoe", "tools"]),
                         ["input.vidoe", "tools"])

    def test_disagreements_list_only_capabilities_both_sources_report(self):
        host = mc.normalize({"tool_call": True, "modalities": {"input": ["text", "image"]}})
        catalog = mc.normalize({"tool_call": True, "temperature": True,
                                "modalities": {"input": ["text", "image", "video"]}})
        self.assertEqual(mc.disagreements(host, catalog),
                         [{"capability": "input.video", "host": False, "catalog": True}])


if __name__ == "__main__":
    unittest.main()
