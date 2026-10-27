"""Published Office handoffs and executable shared-record pipelines on five hosts.

Published packages are real compiler output. Executing their Python helpers
does not establish installed-host dispatch or saved Office application fidelity.
"""

import atexit
import base64
from dataclasses import replace
from functools import lru_cache
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import tomllib
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
for import_root in (ROOT, ROOT / "tests"):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from scripts.daodan.adapter import HOSTS, load_adapter
from scripts.daodan.load import load_plugin
from scripts.daodan.render import RenderError, publish_plugin
from host_binding_assertions import loaded_instruction_text
import office_entries
from test_office_records import valid_content, valid_pptx_plan
from test_office_design_compare import Document, valid_comparison
from test_office_creative_comparison import canonical_digest, creative_comparison


ROLE_PATHS = {"claude": "agents/{role}.md", "copilot": "agents/{role}.agent.md",
              "codex": "roles/{role}.md", "pi": "skills/office-{role}/SKILL.md",
              "opencode": "agents/{role}.md"}


def normalized(path):
    return " ".join(Path(path).read_text(encoding="utf-8").split())


@lru_cache(maxsize=1)
def published_office():
    """One immutable candidate per process; publish once, clean up at process exit."""
    temporary = tempfile.TemporaryDirectory(prefix="office-published-")
    atexit.register(temporary.cleanup)
    registry = {path.parent.name: load_plugin(path.parent)
                for path in sorted((ROOT / "plugins").glob("*/plugin.toml"))}
    office = registry["office"]
    entries = office_entries.entry_plugin()
    adapters, packages, entry_packages = {}, {}, {}
    for host in HOSTS:
        adapter = load_adapter(ROOT / "adapters", host)
        package = Path(temporary.name) / host / "office"
        entry_package = package.with_name("daodan")
        publish_plugin(office, adapter, package, adapters_root=ROOT / "adapters", plugin_registry=registry)
        publish_plugin(entries, adapter, entry_package, adapters_root=ROOT / "adapters", plugin_registry=registry)
        adapters[host], packages[host], entry_packages[host] = adapter, package, entry_package
    return {"temporary": temporary, "registry": registry, "plugin": office,
            "packages": packages, "entries": entry_packages, "adapters": adapters}


def use_published_office(cls):
    fixture = published_office()
    for name in ("plugin", "packages", "entries", "adapters"):
        setattr(cls, name, fixture[name])


class UnifiedOfficeContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        use_published_office(cls)

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="office-contract-")
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        write_text = Path.write_text

        def write_inside_fixture(path, *arguments, **keywords):
            self.assertTrue(path.resolve().is_relative_to(self.directory.resolve()),
                            f"Test write escapes invocation fixture: {path}")
            return write_text(path, *arguments, **keywords)

        writes = mock.patch.object(Path, "write_text", write_inside_fixture)
        writes.start()
        self.addCleanup(writes.stop)

    def cli(self, script, *arguments):
        return subprocess.run([sys.executable, "-B", str(script), *map(str, arguments)], cwd=self.directory,
                              capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)

    def assert_success(self, result):
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_shared_owners_are_reached_through_entries_methods_and_nested_references(self):
        for host, package in self.packages.items():
            with self.subTest(host=host):
                for entry_name in ("document", "presentation", "start", "theme"):
                    path = office_entries.entry_path(self.entries[host], host, entry_name)
                    entry = " ".join(loaded_instruction_text(self, path, host).split())
                    for owner in ("office:content", "office:design"):
                        self.assertIn(owner, entry)
                content = normalized(package / "skills/content/SKILL.md")
                self.assertIn("references/records.md", content)
                self.assertIn("requested", content)
                design = normalized(package / "skills/design/SKILL.md")
                self.assertIn("design_compare.py", design)
                self.assertIn("office_records.py", design)
                self.assertIn("content.revision", design)
                self.assertIn("exact `formats`", design)
                self.assertIn("optional for ordinary work", design)
                for format_name in ("docx", "pptx"):
                    method = normalized(package / f"skills/{format_name}/SKILL.md")
                    for reference in ("content-planning.md", "structure.md", "layout-patterns.md"):
                        self.assertIn("references/" + reference, method)
                        self.assertTrue((package / f"skills/{format_name}/references" / reference).is_file())
                    for old in ("document-types.md", "document-design.md", "design-library.md"):
                        self.assertNotIn(old, method)
                record_contract = normalized(package / "skills/content/references/records.md")
                self.assertIn("canonical-json-v1", record_contract)
                self.assertIn("original source bytes", record_contract)
                self.assertIn("source fidelity", record_contract)
                comparison_contract = normalized(package / "skills/design/references/records.md")
                self.assertIn("parent_ids", comparison_contract)
                self.assertIn("preview", comparison_contract)

    def test_each_worker_receives_its_real_record_contract_and_isolated_dispatch_body(self):
        document_roles = {"content-strategist", "document-designer", "document-reviewer"}
        presentation_roles = {"content-strategist", "presentation-designer", "presentation-reviewer"}
        for host, package in self.packages.items():
            with self.subTest(host=host):
                for entry_name, roles in (("document", document_roles), ("presentation", presentation_roles)):
                    sidecar = tomllib.loads((self.entries[host] / f"contracts/{entry_name}.workflow.toml").read_text())
                    self.assertEqual(set(sidecar["dispatch"]["roles"]), {"office/" + role for role in roles})
                    self.assertTrue(sidecar["dispatch"]["isolated"])
                    entry = loaded_instruction_text(self, office_entries.entry_path(self.entries[host], host, entry_name), host)
                    for role in roles:
                        path = package / ROLE_PATHS[host].format(role=role)
                        body = normalized(path)
                        self.assertIn("office:content", body)
                        self.assertIn("references/records.md", body)
                        if role != "content-strategist":
                            self.assertIn("CONTENT.md", body)
                            self.assertIn("DESIGN.md", body)
                            self.assertIn("content revision", body)
                        if host in {"codex", "pi"}:
                            relative = f"contracts/dispatch/office/{role}.md"
                            self.assertIn(relative, entry)
                            dispatched = normalized(self.entries[host] / relative)
                            self.assertIn("office:content", dispatched)
                            self.assertIn("references/records.md", dispatched)
                            self.assertIn("Return", dispatched)
                        else:
                            self.assertIn("office:" + role, entry)

    def test_inherited_design_rebinds_to_changed_content_without_a_new_visual_choice(self):
        """A content delta must not make an inherited visual identity unusably stale."""
        for host, package in self.packages.items():
            with self.subTest(host=host):
                procedure = normalized(package / "skills/design/references/records.md")
                self.assertRegex(procedure, r"(?i)inherit\w*.{0,100}(?:rebind|binding)")
                self.assertIn("content.revision", procedure)
                self.assertRegex(procedure, r"(?i)(?:new|increment|greater).{0,60}(?:design.{0,30})?revision")
                self.assertRegex(procedure, r"(?i)(?:new|fresh|separate).{0,40}(?:path|candidate)")
                self.assertRegex(procedure, r"(?i)predecessor|previous design")
                self.assertRegex(procedure, r"(?i)(?:preserve|copy|unchanged|same).{0,80}visual|"
                                            r"visual.{0,80}(?:preserve|unchanged|same)")
                self.assertRegex(procedure, r"(?i)(?:preserve|copy|same|original).{0,80}selection|"
                                            r"selection.{0,80}(?:preserve|unchanged|same)")
                self.assertRegex(procedure, r"(?i)no (?:new )?(?:creative|visual|theme).{0,30}(?:choice|selection)|"
                                            r"without.{0,50}(?:creative|visual|theme)")
                self.assertIn("legacy", procedure.lower())
                self.assertRegex(procedure, r"(?i)expand|revise")
                for consumer in ("docx", "pptx", "wordcraft", "deckcraft"):
                    method = normalized(package / f"skills/{consumer}/SKILL.md")
                    self.assertIn("rebind", method.lower())
                    self.assertIn("office:design", method)
                    self.assertIn("records.md", method)

    def test_docx_brand_values_do_not_require_a_catalog_direction_letter(self):
        for host, package in self.packages.items():
            with self.subTest(host=host):
                layout = normalized(package / "skills/docx/references/layout-patterns.md")
                design = normalized(package / "skills/design/SKILL.md")
                self.assertNotRegex(layout, r"(?i)(?:supplied|binding) brand/template "
                                            r"(?:is|must.{0,30}be|requires?) direction `H`")
                self.assertIn("brand or template always wins", design)
                self.assertIn("not compulsory letters", design)
                self.assertIn("same palette roles and font families", layout)

    def test_proposal_and_final_modes_reach_every_native_consumer_and_dispatch_resource(self):
        format_roles = ("document-designer", "document-reviewer", "presentation-designer", "presentation-reviewer")
        for host, package in self.packages.items():
            with self.subTest(host=host):
                for name in ("docx", "pptx", "wordcraft", "deckcraft"):
                    method = normalized(package / f"skills/{name}/SKILL.md")
                    self.assertIn("references/art-direction.md", method)
                    self.assertIn("proposal", method)
                    self.assertIn("final", method)
                    if name in {"wordcraft", "deckcraft"}:
                        self.assertIn("require_selected=False", method)
                        self.assertIn("unselected DESIGN", method)
                        self.assertIn("selected `office:design` record", method)
                        self.assertRegex(method, r"(?i)(?:never fabricate|not selected).{0,100}selection|never fabricate selection")
                for role in format_roles:
                    paths = [package / ROLE_PATHS[host].format(role=role)]
                    if host in {"codex", "pi"}:
                        paths.append(self.entries[host] / f"contracts/dispatch/office/{role}.md")
                    for path in paths:
                        body = normalized(path)
                        self.assertIn("references/art-direction.md", body)
                        self.assertIn("require_selected=False", body)
                        self.assertIn("selected DESIGN.md", body)
                        self.assertIn("content revision and requested formats", body)
                        self.assertIn("candidate", body)
                        self.assertIn("slot", body)
                boundary = normalized(package / "skills/design/references/art-direction.md")
                self.assertIn("copy the existing plan per candidate", boundary)
                self.assertIn("do not freeze final CONTENT.md", boundary)
                self.assertIn("Missing proof or visual access is `blocked`", boundary)
                self.assertIn("actual hardest reading", boundary)
                preview = normalized(package / "skills/pptx/references/design-preview.md")
                self.assertIn("candidate-specific working plans/display bindings", preview)
                self.assertIn("After visual selection", preview)
                self.assertIn("native proposal proof is a different artifact", preview)

    def test_missing_taste_provider_has_phase_scoped_recovery_without_a_new_intake_or_fallback(self):
        self.assertIn("taste-skill@taste-skill", self.plugin.required_dependencies)
        claude = " ".join(loaded_instruction_text(self, office_entries.entry_path(
            self.entries["claude"], "claude", "document"), "claude").split())
        for prerequisite in ("claude plugin enable", "claude plugin list --json", "before the first phase",
                             "stop with that command", "dependency closure, direct or transitive, is off"):
            self.assertIn(prerequisite, claude)
        standalone = {"copilot": "~/.copilot/skills/design-taste-frontend/",
                      "pi": "~/.agents/skills/design-taste-frontend/",
                      "opencode": "~/.config/opencode/skills/design-taste-frontend/"}
        for host, package in self.packages.items():
            with self.subTest(host=host):
                boundary = normalized(package / "skills/design/references/art-direction.md")
                intake = normalized(package / "skills/intake/SKILL.md")
                for location, text in (("art direction", boundary), ("intake", intake)):
                    activation = re.search(r"(?i)required[- ]package activation", text)
                    self.assertIsNotNone(activation, f"{location} omits the host activation prerequisite")
                    context = text[max(0, activation.start() - 160):activation.end() + 160]
                    self.assertRegex(context, r"(?i)\b(?:first|before|prerequisite)\b")
                    if location == "intake":
                        self.assertLess(activation.start(), text.index("Inherited/narrow/read-only"))
                recovery = re.search(r"(?i)(?:unavailable|missing).{0,100}(?:art[- ]direction|Taste) knowledge",
                                     boundary)
                self.assertIsNotNone(recovery, "Recovery must distinguish missing art knowledge from package activation")
                self.assertLess(re.search(r"(?i)required[- ]package activation", boundary).start(), recovery.start())
                context = boundary[max(0, recovery.start() - 180):recovery.end() + 180]
                self.assertRegex(context, r"(?i)\b(?:after|once)\b.{0,100}(?:activation|prerequisite)")
                self.assertRegex(context, r"(?i)blocks? only.{0,80}(?:art[- ]direction|consuming|dependent)")
                self.assertIn("Continue independent authorized work and report actual host recovery", boundary)
                self.assertIn("Do not replace missing Taste with an unrelated provider", boundary)
                self.assertIn("register `Leonxlnx/taste-skill`", boundary)
                self.assertIn("taste-skill@taste-skill", boundary)
                self.assertIn("complete upstream `skills/taste-skill/` folder", boundary)
                self.assertIn("Resource presence is not installed-host execution evidence", boundary)
                self.assertIn("An inherited content-only change", boundary)
                self.assertIn("without new proposals", boundary)
                self.assertIn("Narrow edits and read-only work do not load a new direction or reopen intake", boundary)
                if host in standalone:
                    self.assertIn(standalone[host], boundary)
                    self.assertIn("registry resolution", boundary)

    def test_missing_emitted_native_runtime_produces_no_candidate_and_leaves_record_checks_available(self):
        for host, package in self.packages.items():
            with self.subTest(host=host):
                commands = self.directory / (host + "-commands.json")
                commands.write_text(json.dumps([{"command": "file.new", "params": {"blank": True}}]), encoding="utf-8")
                before = commands.read_bytes()
                output = self.directory / (host + "-blocked.pptx")

                result = self.cli(package / "skills/deckcraft/scripts/deckcraft_bridge.py", "--binary",
                                  self.directory / "unavailable-deckcraft.exe", "apply", "--commands", commands,
                                  "--output", output)

                self.assertNotEqual(result.returncode, 0)
                self.assertIn("DeckCraft executable is missing", result.stderr)
                self.assertFalse(output.exists())
                self.assertEqual(commands.read_bytes(), before)
                source = self.directory / (host + "-independent-content.json")
                source.write_text(json.dumps(valid_content(("docx",))), encoding="utf-8")
                self.assert_success(self.cli(package / "skills/content/scripts/office_records.py", "validate", source))
                producer = normalized(package / "skills/wordcraft/SKILL.md")
                self.assertIn("Missing runtime blocks dependent production while design/source work can", producer)

    def test_published_sibling_helpers_select_and_validate_the_actual_final_plan(self):
        observations = {}
        for host, package in self.packages.items():
            with self.subTest(host=host):
                directory = self.directory / host
                directory.mkdir()
                candidates = creative_comparison(directory)
                input_path = directory / "candidates.json"
                input_path.write_text(json.dumps(candidates), encoding="utf-8")
                compare = package / "skills/design/scripts/design_compare.py"
                record_tool = package / "skills/content/scripts/office_records.py"
                html, selected_path = directory / "COMPARE.html", directory / "DESIGN.md"
                spec = importlib.util.spec_from_file_location("published_office_records_" + host, record_tool)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                for candidate in candidates["candidates"]:
                    self.assertEqual(module.validate_design(candidate["design"], require_selected=False), [])
                    working_plan, working_content = valid_pptx_plan(), valid_content()
                    working_plan["direction"] = {"name": candidate["design"]["direction"]["name"],
                        "palette": {role: candidate["design"]["palette"][role]
                                    for role in ("background", "ink", "surface", "accent")}}
                    working_content["projections"]["pptx"]["plan"]["sha256"] = canonical_digest(working_plan)
                    self.assertEqual(module.validate_content(working_content, pptx_plan=working_plan), [])
                    self.assertNotIn("selection", candidate["design"])

                self.assert_success(self.cli(compare, input_path, "--out", html))
                rendered = Document(html.read_text(encoding="utf-8"))
                self.assertEqual({node.attributes["data-format"] for node in rendered.frames()}, {"docx", "pptx"})
                image_digests = [hashlib.sha256(base64.b64decode(
                    node.attributes["src"].split(",", 1)[1], validate=True)).hexdigest()
                    for node in rendered.elements if node.tag == "img"]
                self.assertCountEqual(image_digests, [frame["sha256"] for candidate in candidates["candidates"]
                    for proposal in candidate["previews"].values() for frame in proposal["frames"]])
                self.assertEqual(rendered.root.text().count(candidates["sample"]["body"]), 1)
                decision = "Authorized integration contract exercise"
                self.assert_success(self.cli(compare, input_path, "--select", "technical", "--authority", "autonomous",
                                             "--source", decision, "--out", selected_path))
                self.assert_success(self.cli(record_tool, "validate", selected_path))
                selected = module.load_record(selected_path)
                candidate = candidates["candidates"][1]
                expected_selection = {"candidate_id": "technical", "authority": "autonomous", "source": decision,
                    "preview": {"comparison_sha256": canonical_digest(candidates), "hash_mode": "canonical-json-v1",
                                "sample_sha256": canonical_digest(candidates["sample"]),
                                "design_sha256": canonical_digest(candidate["design"]),
                                "frames": {output: [{"slot_id": frame["slot_id"], "sha256": frame["sha256"]}
                                                     for frame in proposal["frames"]]
                                           for output, proposal in candidate["previews"].items()}}}
                self.assertEqual(selected["selection"], expected_selection)
                self.assertEqual({key: value for key, value in selected.items() if key != "selection"},
                                 candidate["design"])
                plan, content = valid_pptx_plan(), valid_content()
                source_bytes = b"Office uses one shared editorial record.\nDOCX and PPTX keep independent composition methods.\nSeparate reusable templates are optional unless requested.\n"
                source = directory / "source-brief.md"
                source.write_bytes(source_bytes)
                content["sources"][0].update(path=str(source), sha256=hashlib.sha256(source_bytes).hexdigest())
                for index, claim in enumerate(content["claims"], 1):
                    claim["sources"][0]["locator"] = "line " + str(index)
                optional_source = ROOT / "plugins/office/skills/design/SKILL.md"
                optional_text = "A separate DOTX/POTX is optional for ordinary work; generate one when useful or when reusable templates are requested."
                self.assertIn(optional_text, " ".join(optional_source.read_text(encoding="utf-8").split()))
                content["sources"].append({"id": "SRC2", "path": str(optional_source), "role": "information",
                    "sha256": hashlib.sha256(optional_source.read_bytes()).hexdigest()})
                content["claims"].append({"id": "C3", "text": optional_text,
                    "priority": "optional", "sources": [{"source_id": "SRC2",
                        "locator": "Materialize native styles and optional templates, opening paragraph"}],
                    "locked": False, "conditions": [], "conflicts": []})
                plan["direction"] = {"name": selected["direction"]["name"],
                    "palette": {role: selected["palette"][role] for role in ("background", "ink", "surface", "accent")}}
                content["projections"]["pptx"]["plan"]["sha256"] = hashlib.sha256(json.dumps(
                    plan, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
                plan_path, content_input = directory / "plan.json", directory / "content.json"
                plan_path.write_text(json.dumps(plan), encoding="utf-8")
                content_input.write_text(json.dumps(content), encoding="utf-8")
                content_path = directory / "CONTENT.md"
                self.assert_success(self.cli(record_tool, "write", content_input, "--out", content_path))
                self.assert_success(self.cli(record_tool, "validate", content_path, "--pptx-plan", plan_path))
                loaded = module.load_record(content_path)
                self.assertEqual(loaded["claims"][-1]["priority"], "optional")
                self.assertEqual(loaded["revision"], selected["content"]["revision"])
                self.assertEqual(loaded["project_id"], selected["project_id"])
                self.assertEqual(loaded["brief"]["formats"], selected["formats"])
                native_preview = directory / "plan-preview.html"
                self.assert_success(self.cli(package / "skills/pptx/scripts/design_preview.py", "--plan", plan_path,
                                             "--out", native_preview))
                self.assertIn(plan["slides"][0]["title"], native_preview.read_text(encoding="utf-8"))
                observations[host] = {"schema": candidates["schema"], "selected": "technical",
                    "formats": selected["formats"], "proof_images": len(image_digests),
                    "sha256": {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                               for path in (compare, record_tool, input_path, html, selected_path,
                                            plan_path, content_path, native_preview)}}
                original = content_path.read_bytes()
                plan["deck_title"] = "Changed after the content binding was frozen"
                plan_path.write_text(json.dumps(plan), encoding="utf-8")

                rejected = self.cli(record_tool, "validate", content_path, "--pptx-plan", plan_path)

                self.assertNotEqual(rejected.returncode, 0)
                self.assertIn("digest", rejected.stderr)
                self.assertEqual(content_path.read_bytes(), original)
        self.assertEqual(set(observations), set(HOSTS))
        (self.directory / "creative-emitted-evidence.json").write_text(
            json.dumps(observations, sort_keys=True, indent=2) + "\n", encoding="utf-8")

    def test_published_docx_only_preview_does_not_add_a_deck_projection(self):
        for host, package in self.packages.items():
            with self.subTest(host=host):
                source = self.directory / (host + ".json")
                source.write_text(json.dumps(valid_comparison(("docx",))), encoding="utf-8")
                output = self.directory / (host + ".html")

                self.assert_success(self.cli(package / "skills/design/scripts/design_compare.py", source, "--out", output))

                rendered = Document(output.read_text(encoding="utf-8"))
                self.assertEqual(len(rendered.frames()), 2)
                self.assertEqual({node.attributes["data-format"] for node in rendered.frames()}, {"docx"})

    def test_unsupported_isolation_or_dispatch_never_replaces_a_published_entry(self):
        fixture = published_office()
        for host, adapter in self.adapters.items():
            for entry_name in ("document", "presentation", "theme"):
                entry = office_entries.entry_plugin((entry_name,))
                for missing in ("isolation", "dispatch"):
                    with self.subTest(host=host, entry=entry_name, missing=missing):
                        self.assert_publication_blocked(entry, adapter, host + "-" + entry_name + "-" + missing,
                                                        missing, fixture["registry"])

    def assert_publication_blocked(self, entry, adapter, label, missing, registry):
        if missing == "isolation":
            unsupported = replace(adapter, strategies=tuple(replace(strategy, isolated=False)
                                                           for strategy in adapter.strategies))
        else:
            bindings = dict(adapter.bindings)
            del bindings["roles.dispatch"]
            unsupported = replace(adapter, bindings=bindings)
        destination = self.directory / label
        destination.mkdir()
        sentinel = destination / "previous-entry"
        sentinel.write_bytes(b"preserve accepted published entry")

        with self.assertRaises(RenderError):
            publish_plugin(entry, unsupported, destination, adapters_root=ROOT / "adapters", plugin_registry=registry)

        self.assertEqual(list(destination.iterdir()), [sentinel])
        self.assertEqual(sentinel.read_bytes(), b"preserve accepted published entry")


if __name__ == "__main__":
    unittest.main()
