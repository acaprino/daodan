"""Public Office record contracts, with real parser and file-preservation boundaries.

Validation is a unit contract. Parser, serializer and CLI checks exercise owned
filesystem integration; none establishes editorial fidelity or Office rendering.
The fixture vocabulary is the approved step-1 contract, not a copy of a validator.
"""

import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "plugins/office/skills/content/scripts/office_records.py"


def valid_pptx_plan():
    """Existing PPTX slide contract plus the editorial revision it projects."""
    return {
        "deck_title": "Office engineering brief",
        "content_revision": 1,
        "direction": {"library": "A"},
        "slides": [
            {"id": "S1", "pattern": "cover", "title": "Office engineering brief",
             "job": "State the shared editorial requirement", "claims": ["C1"],
             "source_note": "Source brief, section 1"},
            {"id": "S2", "pattern": "executive summary",
             "headline": "Each format keeps its own composition",
             "job": "Explain independent native composition", "claims": ["C2"],
             "content": {"cards": ["DOCX flows", "PPTX uses slides"]},
             "source_note": "Source brief, section 2"},
        ],
    }


def _plan_digest(plan):
    """The public binding hashes canonical UTF-8 JSON, independent of whitespace."""
    payload = json.dumps(plan, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def valid_content(formats=("docx", "pptx")):
    """A source-backed core claim and supporting claim, projected only as asked."""
    record = {
        "schema": "office/content/v1",
        "project_id": "office-engineering-brief",
        "revision": 1,
        "brief": {
            "operation": "create", "intent": "explain", "goal": "Explain Office ownership",
            "audience": "Office maintainers", "market": "developer tools",
            "channel": "independent reading", "formats": list(formats),
            "scope": "Shared editorial work and native composition",
            "depth": "mechanisms and limits", "extent": "two sections or slides",
            "density": "standard", "tone": "technical", "transformation": "rewrite",
        },
        "sources": [{"id": "SRC1", "path": "source-brief.md", "sha256": "a" * 64,
                     "role": "information"}],
        "claims": [
            {"id": "C1", "text": "Office uses one shared editorial record.",
             "priority": "core", "sources": [{"source_id": "SRC1", "locator": "section 1"}],
             "locked": True, "conditions": ["For requested DOCX and PPTX work"], "conflicts": []},
            {"id": "C2", "text": "DOCX and PPTX keep independent composition methods.",
             "priority": "supporting", "sources": [{"source_id": "SRC1", "locator": "section 2"}],
             "locked": False, "conditions": [], "conflicts": []},
        ],
        "units": [
            {"id": "U1", "message": "Share editorial authority",
             "text": "Office uses one shared editorial record.", "claim_ids": ["C1"],
             "relationship": "evidence", "detail": "State the approved invariant verbatim",
             "transformation": "verbatim"},
            {"id": "U2", "message": "Retain independent composition",
             "text": "DOCX and PPTX keep independent composition methods.", "claim_ids": ["C2"],
             "relationship": "comparison", "detail": "Explain the distinct native formats",
             "transformation": "rewrite"},
        ],
        "sequence": ["U1", "U2"],
        "projections": {},
        "transformations": [], "gaps": [], "exclusions": [],
    }
    if "docx" in formats:
        record["projections"]["docx"] = {
            "content_revision": 1, "structure": "technical brief",
            "sections": [{"id": "D1", "title": "Editorial authority", "unit_ids": ["U1"]},
                         {"id": "D2", "title": "Native composition", "unit_ids": ["U2"]}],
        }
    if "pptx" in formats:
        record["projections"]["pptx"] = {
            "content_revision": 1,
            "plan": {"path": "plan.json", "hash_mode": "canonical-json-v1",
                     "sha256": _plan_digest(valid_pptx_plan())},
            "placements": [{"slide_id": "S1", "unit_ids": ["U1"]},
                           {"slide_id": "S2", "unit_ids": ["U2"]}],
        }
    return record


def valid_design(formats=("docx", "pptx")):
    """Complete visual decisions on existing palette roles and safe font data."""
    return {
        "schema": "office/design/v1", "project_id": "office-engineering-brief", "revision": 1,
        "content": {"project_id": "office-engineering-brief", "revision": 1},
        "formats": list(formats),
        "direction": {"name": "Engineering editorial", "idea": "Clear ownership through hierarchy",
                      "principles": ["Lead with the message", "Keep evidence readable"]},
        "palette": {
            "background": "#FFFFFF", "surface": "#F1F5F9", "ink": "#172033",
            "accent": "#1D4ED8", "muted": "#475569",
            "data": ["#1D4ED8", "#166534", "#9A3412", "#6B21A8"],
            "provenance": {"source": "project brief", "method": "authored from the technical subject"},
            "proportions": {"background": 0.65, "surface": 0.20, "ink": 0.10, "accent": 0.05},
        },
        "typography": {
            "heading": {"family": "Source Serif 4", "fallbacks": ["Georgia", "serif"], "weight": 600},
            "body": {"family": "Source Sans 3", "fallbacks": ["Arial", "sans-serif"], "weight": 400},
            "caption": {"family": "Source Sans 3", "fallbacks": ["Arial", "sans-serif"], "weight": 400},
        },
        "spacing": {"unit": 8, "scale": [1, 2, 3, 5], "density": "comfortable"},
        "imagery": {"treatment": "documentary", "source_policy": "Use supplied project assets"},
        "data": {"table": "ruled", "chart": "direct-labels", "source_notes": "required"},
        "components": {"title": "left-aligned", "callout": "rule", "quote": "inset",
                       "navigation": "section-label"},
        "adaptations": {name: {"reading": "continuous" if name == "docx" else "projected",
                               "emphasis": "message before detail"} for name in formats},
        "selection": {"candidate_id": "engineering-A", "authority": "autonomous",
                      "source": "Approved engineering verification autonomy"},
    }


spec = importlib.util.spec_from_file_location("office_records_contract", SCRIPT)
records = importlib.util.module_from_spec(spec)
spec.loader.exec_module(records)


class ContentRecordTests(unittest.TestCase):
    def assert_invalid(self, record, *, plan=None):
        problems = records.validate_content(record, pptx_plan=plan)
        self.assertIsInstance(problems, list)
        self.assertTrue(problems, "The inconsistent editorial record was accepted")
        self.assertTrue(all(isinstance(problem, str) and problem for problem in problems))

    def test_valid_paired_record_accepts_the_existing_pptx_plan(self):
        record, plan = valid_content(), valid_pptx_plan()
        original_record, original_plan = copy.deepcopy(record), copy.deepcopy(plan)

        problems = records.validate_content(record, pptx_plan=plan)

        self.assertEqual(problems, [])
        self.assertEqual(record, original_record)
        self.assertEqual(plan, original_plan)

    def test_docx_only_record_requires_no_deck_or_pptx_projection(self):
        record = valid_content(("docx",))

        problems = records.validate_content(record)

        self.assertEqual(problems, [])
        self.assertEqual(set(record["projections"]), {"docx"})

    def test_pptx_only_record_requires_no_docx_projection(self):
        record = valid_content(("pptx",))

        problems = records.validate_content(record, pptx_plan=valid_pptx_plan())

        self.assertEqual(problems, [])
        self.assertEqual(set(record["projections"]), {"pptx"})

    def test_schema_project_revision_and_editorial_dimensions_are_required(self):
        changes = [("schema", None), ("project_id", ""), ("revision", 0),
                   ("revision", True), ("revision", 1.5)]
        for field, value in changes:
            with self.subTest(field=field, value=value):
                record = valid_content(("docx",))
                record[field] = value

                self.assert_invalid(record)
        for field in valid_content()["brief"]:
            with self.subTest(missing_dimension=field):
                record = valid_content(("docx",))
                del record["brief"][field]

                self.assert_invalid(record)

    def test_stable_source_claim_unit_and_section_ids_are_unique(self):
        for collection in ("sources", "claims", "units"):
            with self.subTest(collection=collection):
                record = valid_content(("docx",))
                record[collection].append(copy.deepcopy(record[collection][0]))

                self.assert_invalid(record)
        record = valid_content(("docx",))
        record["projections"]["docx"]["sections"][1]["id"] = "D1"

        self.assert_invalid(record)

    def test_claim_sources_must_exist_and_carry_a_locator(self):
        for reference in ({"source_id": "UNKNOWN", "locator": "section 1"},
                          {"source_id": "SRC1", "locator": ""}):
            with self.subTest(reference=reference):
                record = valid_content(("docx",))
                record["claims"][0]["sources"] = [reference]

                self.assert_invalid(record)

    def test_source_hashes_must_be_sha256_values(self):
        record = valid_content(("docx",))
        record["sources"][0]["sha256"] = "not a digest"

        self.assert_invalid(record)

    def test_units_sequence_and_docx_sections_reject_unknown_references(self):
        for target in ("claim", "sequence", "section"):
            with self.subTest(target=target):
                record = valid_content(("docx",))
                if target == "claim":
                    record["units"][0]["claim_ids"] = ["UNKNOWN"]
                elif target == "sequence":
                    record["sequence"] = ["UNKNOWN", "U2"]
                else:
                    record["projections"]["docx"]["sections"][0]["unit_ids"] = ["UNKNOWN"]

                self.assert_invalid(record)

    def test_sequence_cannot_duplicate_or_drop_a_unit(self):
        for sequence in (["U1", "U1", "U2"], ["U1"]):
            with self.subTest(sequence=sequence):
                record = valid_content(("docx",))
                record["sequence"] = sequence

                self.assert_invalid(record)

    def test_each_requested_format_must_cover_core_claims(self):
        for output in ("docx", "pptx"):
            with self.subTest(output=output):
                record = valid_content()
                if output == "docx":
                    record["projections"]["docx"]["sections"][0]["unit_ids"] = ["U2"]
                else:
                    record["projections"]["pptx"]["placements"][0]["unit_ids"] = ["U2"]

                self.assert_invalid(record, plan=valid_pptx_plan())

    def test_explicit_authorized_exclusion_allows_a_core_claim_to_leave_one_format(self):
        record = valid_content()
        record["projections"]["docx"]["sections"].pop(0)
        record["exclusions"] = [{"claim_id": "C1", "format": "docx",
                                 "reason": "User requested the invariant only in the deck",
                                 "authority": "user", "source": "Approved scope decision Q1"}]

        problems = records.validate_content(record, pptx_plan=valid_pptx_plan())

        self.assertEqual(problems, [])

    def test_exclusions_need_known_claim_format_and_explicit_authority(self):
        valid = {"claim_id": "C1", "format": "docx", "reason": "Requested scope",
                 "authority": "user", "source": "Scope answer Q1"}
        for field, value in (("claim_id", "UNKNOWN"), ("format", "xlsx"),
                             ("authority", ""), ("source", "")):
            with self.subTest(field=field):
                record = valid_content(("docx",))
                exclusion = dict(valid)
                exclusion[field] = value
                record["exclusions"] = [exclusion]

                self.assert_invalid(record)

    def test_locked_claims_cannot_be_rewritten_or_silently_reworded(self):
        for mutation in ("mode", "text"):
            with self.subTest(mutation=mutation):
                record = valid_content(("docx",))
                if mutation == "mode":
                    record["units"][0]["transformation"] = "summarize"
                else:
                    record["units"][0]["text"] = "Office may use several editorial authorities."

                self.assert_invalid(record)

    def test_unknown_transformation_modes_are_rejected_at_each_boundary(self):
        for owner in ("brief", "unit", "map"):
            with self.subTest(owner=owner):
                record = valid_content(("docx",))
                if owner == "brief":
                    record["brief"]["transformation"] = "invent"
                elif owner == "unit":
                    record["units"][1]["transformation"] = "invent"
                else:
                    record["transformations"] = [{"unit_id": "U2", "mode": "invent",
                        "source_ids": ["SRC1"], "destination": {"format": "docx", "id": "D2"},
                        "reason": "Unsupported invention"}]

                self.assert_invalid(record)

    def test_approved_transformation_modes_are_available_for_unlocked_content(self):
        for mode in ("verbatim", "copyedit", "restructure", "rewrite", "summarize", "synthesize", "expand"):
            with self.subTest(mode=mode):
                record = valid_content(("docx",))
                record["brief"]["transformation"] = mode
                record["units"][1]["transformation"] = mode

                self.assertEqual(records.validate_content(record), [])

    def test_transformation_map_links_sources_units_and_real_destinations(self):
        record = valid_content(("docx",))
        transformation = {"unit_id": "U2", "mode": "rewrite", "source_ids": ["SRC1"],
                          "destination": {"format": "docx", "id": "D2"},
                          "reason": "Adapt the source explanation to the maintainers"}
        record["transformations"] = [transformation]

        self.assertEqual(records.validate_content(record), [])
        for target in ("source", "unit", "destination"):
            with self.subTest(target=target):
                changed = copy.deepcopy(record)
                item = changed["transformations"][0]
                if target == "source":
                    item["source_ids"] = ["UNKNOWN"]
                elif target == "unit":
                    item["unit_id"] = "UNKNOWN"
                else:
                    item["destination"]["id"] = "UNKNOWN"

                self.assert_invalid(changed)

    def test_transformation_map_cannot_override_a_locked_unit(self):
        record = valid_content(("docx",))
        record["transformations"] = [{"unit_id": "U1", "mode": "rewrite", "source_ids": ["SRC1"],
            "destination": {"format": "docx", "id": "D1"}, "reason": "Unapproved rewrite"}]

        self.assert_invalid(record)

    def test_requested_formats_reject_missing_extra_duplicate_and_unknown_projections(self):
        for mutation in ("missing", "extra", "duplicate", "unknown", "empty"):
            with self.subTest(mutation=mutation):
                record = valid_content(("docx",))
                if mutation == "missing":
                    del record["projections"]["docx"]
                elif mutation == "extra":
                    record["projections"]["pptx"] = valid_content()["projections"]["pptx"]
                elif mutation == "duplicate":
                    record["brief"]["formats"] = ["docx", "docx"]
                elif mutation == "unknown":
                    record["brief"]["formats"] = ["xlsx"]
                else:
                    record["brief"]["formats"] = []

                self.assert_invalid(record)

    def test_projection_revision_must_match_the_editorial_record(self):
        for output in ("docx", "pptx"):
            with self.subTest(output=output):
                record = valid_content()
                record["projections"][output]["content_revision"] = 2

                self.assert_invalid(record, plan=valid_pptx_plan())

    def test_supplied_plan_must_match_its_hash_and_editorial_revision(self):
        for mutation in ("hash", "revision"):
            with self.subTest(mutation=mutation):
                record, plan = valid_content(), valid_pptx_plan()
                if mutation == "hash":
                    plan["deck_title"] = "A different plan"
                else:
                    plan["content_revision"] = 2
                    record["projections"]["pptx"]["plan"]["sha256"] = _plan_digest(plan)

                self.assert_invalid(record, plan=plan)

    def test_pptx_plan_metadata_requires_path_and_sha256(self):
        for field, value in (("path", ""), ("sha256", "invalid")):
            with self.subTest(field=field):
                record = valid_content()
                record["projections"]["pptx"]["plan"][field] = value

                self.assert_invalid(record, plan=valid_pptx_plan())

    def test_pptx_plan_hash_mode_must_explicitly_name_the_canonical_json_contract(self):
        for value in (None, "file-bytes", "unknown"):
            with self.subTest(value=value):
                record = valid_content()
                binding = record["projections"]["pptx"]["plan"]
                if value is None:
                    del binding["hash_mode"]
                else:
                    binding["hash_mode"] = value

                self.assert_invalid(record, plan=valid_pptx_plan())

    def test_pptx_placements_reject_unknown_unit_and_slide_ids(self):
        for target in ("unit", "slide"):
            with self.subTest(target=target):
                record = valid_content()
                placement = record["projections"]["pptx"]["placements"][0]
                placement["unit_ids" if target == "unit" else "slide_id"] = (
                    ["UNKNOWN"] if target == "unit" else "UNKNOWN")

                self.assert_invalid(record, plan=valid_pptx_plan())

    def test_supplied_plan_rejects_duplicate_slide_and_unknown_claim_ids(self):
        for mutation in ("duplicate_slide", "unknown_claim", "mismatched_claim"):
            with self.subTest(mutation=mutation):
                record, plan = valid_content(), valid_pptx_plan()
                if mutation == "duplicate_slide":
                    plan["slides"][1]["id"] = "S1"
                else:
                    plan["slides"][0]["claims"] = ["UNKNOWN" if mutation == "unknown_claim" else "C2"]
                record["projections"]["pptx"]["plan"]["sha256"] = _plan_digest(plan)

                self.assert_invalid(record, plan=plan)


class DesignRecordTests(unittest.TestCase):
    def assert_invalid(self, record):
        problems = records.validate_design(record)
        self.assertIsInstance(problems, list)
        self.assertTrue(problems, "The incomplete or unsafe visual record was accepted")
        self.assertTrue(all(isinstance(problem, str) and problem for problem in problems))

    def test_complete_selected_designs_validate_for_requested_formats_only(self):
        for formats in (("docx", "pptx"), ("docx",), ("pptx",)):
            with self.subTest(formats=formats):
                record = valid_design(formats)
                original = copy.deepcopy(record)

                problems = records.validate_design(record)

                self.assertEqual(problems, [])
                self.assertEqual(record, original)

    def test_design_identity_and_content_link_are_required(self):
        for field, value in (("schema", "other"), ("project_id", ""), ("revision", 0),
                             ("revision", True), ("content", {})):
            with self.subTest(field=field, value=value):
                record = valid_design()
                record[field] = value

                self.assert_invalid(record)
        for field, value in (("project_id", "different-project"), ("revision", 0), ("revision", True)):
            with self.subTest(content_field=field):
                record = valid_design()
                record["content"][field] = value

                self.assert_invalid(record)

    def test_complete_visual_sections_are_required(self):
        for field in ("direction", "palette", "typography", "spacing", "imagery", "data",
                      "components", "adaptations"):
            with self.subTest(field=field):
                record = valid_design()
                del record[field]

                self.assert_invalid(record)

    def test_direction_requires_name_idea_and_principles(self):
        for field in ("name", "idea", "principles"):
            with self.subTest(field=field):
                record = valid_design()
                del record["direction"][field]

                self.assert_invalid(record)

    def test_palette_requires_existing_semantic_roles_and_provenance(self):
        for field in ("background", "surface", "ink", "accent", "muted", "data", "provenance", "proportions"):
            with self.subTest(field=field):
                record = valid_design()
                del record["palette"][field]

                self.assert_invalid(record)

    def test_heading_body_and_caption_require_font_families_and_fallbacks(self):
        for role in ("heading", "body", "caption"):
            for field in (None, "family", "fallbacks"):
                with self.subTest(role=role, field=field):
                    record = valid_design()
                    if field is None:
                        del record["typography"][role]
                    else:
                        del record["typography"][role][field]

                    self.assert_invalid(record)

    def test_final_selection_requires_candidate_authority_and_decision_source(self):
        for field in (None, "candidate_id", "authority", "source"):
            with self.subTest(field=field):
                record = valid_design()
                if field is None:
                    del record["selection"]
                else:
                    record["selection"][field] = ""

                self.assert_invalid(record)
        record = valid_design()
        record["selection"]["authority"] = "browser-highlight"

        self.assert_invalid(record)

    def test_user_and_autonomous_selection_authorities_are_accepted(self):
        record = valid_design()
        record["selection"]["authority"] = "user"
        record["selection"]["source"] = "User selected candidate engineering-A"

        self.assertEqual(records.validate_design(record), [])

    def test_proposal_validation_can_omit_selection_without_approving_it(self):
        record = valid_design()
        del record["selection"]

        problems = records.validate_design(record, require_selected=False)

        self.assertEqual(problems, [])
        self.assertNotIn("selection", record)
        self.assert_invalid(record)

    def test_proposal_validation_still_rejects_a_malformed_supplied_selection(self):
        record = valid_design()
        record["selection"]["authority"] = "implied"

        self.assertTrue(records.validate_design(record, require_selected=False))

    def test_formats_and_adaptations_are_exactly_the_requested_docx_or_pptx_set(self):
        for mutation in ("duplicate", "unknown", "empty", "missing", "extra"):
            with self.subTest(mutation=mutation):
                record = valid_design(("docx",))
                if mutation == "duplicate":
                    record["formats"] = ["docx", "docx"]
                elif mutation == "unknown":
                    record["formats"] = ["xlsx"]
                elif mutation == "empty":
                    record["formats"] = []
                elif mutation == "missing":
                    del record["adaptations"]["docx"]
                else:
                    record["adaptations"]["pptx"] = {"reading": "projected"}

                self.assert_invalid(record)

    def test_colours_fonts_and_spacing_cannot_carry_css_or_markup(self):
        for target, value in (("colour", "red; background:url(https://invalid.test/x)"),
                              ("colour", "#GGGGGG"), ("data", "var(--unbound)"),
                              ("font", "Arial; color:red"), ("font", "</style><script>bad()</script>"),
                              ("fallback", "serif; display:none"), ("weight", "400; color:red"),
                              ("component", "solid; background:url(https://invalid.test/x)"),
                              ("table", "url(https://invalid.test/x)"),
                              ("spacing", "calc(1px + var(--x))")):
            with self.subTest(target=target, value=value):
                record = valid_design()
                if target == "colour":
                    record["palette"]["accent"] = value
                elif target == "data":
                    record["palette"]["data"][0] = value
                elif target == "font":
                    record["typography"]["body"]["family"] = value
                elif target == "fallback":
                    record["typography"]["body"]["fallbacks"] = [value]
                elif target == "weight":
                    record["typography"]["body"]["weight"] = value
                elif target == "component":
                    record["components"]["callout"] = value
                elif target == "table":
                    record["data"]["table"] = value
                else:
                    record["spacing"]["unit"] = value

                self.assert_invalid(record)


class RecordFileTests(unittest.TestCase):
    """Real file/CLI boundaries, isolated under the assigned run's temporary root."""

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="office-records-")
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)

    def input_file(self, record=None, *, name="input.json", text=None):
        path = self.directory / name
        path.write_text(json.dumps(valid_content(("docx",)) if record is None else record,
                                   ensure_ascii=False) if text is None else text, encoding="utf-8")
        return path

    def run_cli(self, *arguments):
        return subprocess.run([sys.executable, str(SCRIPT), *map(str, arguments)],
                              cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=30)

    def test_json_and_a_single_fenced_markdown_object_load_the_same_actual_data(self):
        record = valid_content(("docx",))
        record["units"][1]["text"] = "Preserve Unicode: qualità, α and 日本語."
        source = self.input_file(record)
        markdown = self.input_file(name="CONTENT.md", text=(
            "# Editorial record\n\n```json\n" + json.dumps(record, ensure_ascii=False) + "\n```\n"))

        self.assertEqual(records.load_record(source), record)
        self.assertEqual(records.load_record(markdown), record)

    def test_parser_rejects_duplicate_keys_at_top_level_and_nested_objects(self):
        for payload in ('{"schema":"office/content/v1","schema":"office/design/v1"}',
                        '{"brief":{"formats":["docx"],"formats":["pptx"]}}'):
            with self.subTest(payload=payload):
                source = self.input_file(text=payload)

                with self.assertRaises(ValueError):
                    records.load_record(source)

    def test_parser_rejects_nonfinite_numbers_including_overflow(self):
        for token in ("NaN", "Infinity", "-Infinity", "1e999"):
            with self.subTest(token=token):
                source = self.input_file(text='{"revision":' + token + '}')

                with self.assertRaises(ValueError):
                    records.load_record(source)

    def test_parser_rejects_malformed_nonobject_and_ambiguous_markdown_records(self):
        payloads = ("{broken", "[]", '"text"', "", "# No JSON object\n",
                    "```json\n{}\n```\n```json\n{}\n```\n",
                    "```json\n[]\n```\n", "```json\n{broken\n```\n")
        for index, payload in enumerate(payloads):
            with self.subTest(payload=payload):
                source = self.input_file(name=f"bad-{index}.md" if "```" in payload else f"bad-{index}.json",
                                         text=payload)

                with self.assertRaises(ValueError):
                    records.load_record(source)

    def test_parser_rejects_records_larger_than_four_mib_without_mutating_input(self):
        source = self.input_file(text='{"padding":"' + "x" * (4 * 1024 * 1024) + '"}')
        before = source.read_bytes()

        with self.assertRaises(ValueError):
            records.load_record(source)

        self.assertEqual(source.read_bytes(), before)

    def test_write_record_serializes_the_data_and_round_trips_through_its_public_loader(self):
        for name, record in (("CONTENT.md", valid_content(("docx",))),
                             ("DESIGN.md", valid_design(("docx",)))):
            with self.subTest(name=name):
                output = self.directory / name
                original = copy.deepcopy(record)

                result = records.write_record(record, output)

                self.assertIsNone(result)
                self.assertEqual(records.load_record(output), original)
                self.assertEqual(record, original)
                self.assertEqual(output.read_text(encoding="utf-8").count("```json"), 1)

    def test_write_record_refuses_to_replace_an_existing_artifact(self):
        output = self.directory / "CONTENT.md"
        output.write_bytes(b"Approved content artifact\r\n")
        before = output.read_bytes()

        with self.assertRaises((ValueError, OSError)):
            records.write_record(valid_content(("docx",)), output)

        self.assertEqual(output.read_bytes(), before)

    def test_write_record_validates_before_creating_an_output(self):
        for name, record in (("CONTENT.md", valid_content(("docx",))),
                             ("DESIGN.md", valid_design(("docx",)))):
            with self.subTest(name=name):
                if name == "CONTENT.md":
                    record["units"][0]["claim_ids"] = ["UNKNOWN"]
                else:
                    del record["selection"]
                output = self.directory / name

                with self.assertRaises((ValueError, OSError)):
                    records.write_record(record, output)

                self.assertFalse(output.exists())

    def test_cli_validate_accepts_paired_content_with_the_supplied_existing_plan(self):
        source = self.input_file(valid_content())
        plan = self.input_file(valid_pptx_plan(), name="plan.json")
        before = {path.name: path.read_bytes() for path in self.directory.iterdir()}

        result = self.run_cli("validate", source, "--pptx-plan", plan)

        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn(hashlib.sha256(plan.read_bytes()).hexdigest(), result.stdout,
                      "The CLI must report the plan file's original byte hash as input evidence")
        self.assertEqual({path.name: path.read_bytes() for path in self.directory.iterdir()}, before)

    def test_cli_write_creates_a_new_valid_record(self):
        source = self.input_file()
        output = self.directory / "CONTENT.md"
        before = source.read_bytes()

        result = self.run_cli("write", source, "--out", output)

        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual(records.load_record(output), valid_content(("docx",)))
        self.assertEqual(source.read_bytes(), before)

    def test_cli_rejects_invalid_records_without_creating_output(self):
        for payload in ('{"schema":"office/content/v1"}', '{"bad":NaN}', '{broken'):
            with self.subTest(payload=payload):
                source = self.input_file(text=payload)
                output = self.directory / "rejected.md"
                before = source.read_bytes()

                result = self.run_cli("write", source, "--out", output)

                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(output.exists())
                self.assertEqual(source.read_bytes(), before)

    def test_cli_write_refuses_an_existing_output_and_preserves_both_files(self):
        source = self.input_file()
        output = self.directory / "CONTENT.md"
        output.write_bytes(b"Approved content")
        before = source.read_bytes(), output.read_bytes()

        result = self.run_cli("write", source, "--out", output)

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((source.read_bytes(), output.read_bytes()), before)

    def test_cli_write_refuses_same_path_and_hard_link_aliases_without_changing_input(self):
        source = self.input_file()
        alias = self.directory / "alias.md"
        alias.hardlink_to(source)
        before = source.read_bytes()

        for output in (source, alias):
            with self.subTest(output=output.name):
                result = self.run_cli("write", source, "--out", output)

                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(source.read_bytes(), before)
                self.assertEqual(alias.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
