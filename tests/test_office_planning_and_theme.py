"""Content planning before design, and a theme that reaches the file as a real template.

The template kit tests open generated packages and check their parts; they do not
establish how PowerPoint, Word or an engine renders them.
"""

import contextlib
import importlib.util
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


REPO_ROOT = Path(__file__).resolve().parents[1]
for import_root in (REPO_ROOT, REPO_ROOT / "tests"):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from scripts.daodan.adapter import HOSTS, load_adapter  # noqa: E402
from scripts.daodan.load import load_plugin  # noqa: E402
from scripts.daodan.render import render_plugin  # noqa: E402
from host_binding_assertions import loaded_instruction_text  # noqa: E402
import office_entries  # noqa: E402

OFFICE = REPO_ROOT / "plugins/office"
SKILLS = OFFICE / "skills"


def _load(name, relative):
    spec = importlib.util.spec_from_file_location(name, SKILLS / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


kit = _load("office_template_kit", "design/scripts/template_kit.py")
palette_tool = _load("office_palette", "design/scripts/palette.py")
preview = _load("office_design_preview", "pptx/scripts/design_preview.py")
verifier = _load("office_verify_for_kit", "integrity/scripts/office_verify.py")

A = "http://schemas.openxmlformats.org/drawingml/2006/main"
P = "http://schemas.openxmlformats.org/presentationml/2006/main"
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
ROLE_PATHS = {
    "claude": "agents/{role}.md",
    "copilot": "agents/{role}.agent.md",
    "codex": "roles/{role}.md",
    "pi": "skills/office-{role}/SKILL.md",
    "opencode": "agents/{role}.md",
}
ENTRY_PATHS = {
    "claude": "commands/{name}.md",
    "copilot": "prompts/{name}.prompt.md",
    "codex": "skills/{name}-workflow/SKILL.md",
    "pi": "prompts/office-{name}.md",
    "opencode": "commands/{name}.md",
}


def _normalized(text):
    return " ".join(text.split())


class ContentPlanningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plugin = load_plugin(OFFICE)
        cls.temporary = tempfile.TemporaryDirectory(dir=str(REPO_ROOT) if os.name == "nt" else None)
        cls.packages = {}
        cls.entries = office_entries.render_entries(cls.temporary.name, ("presentation",))
        for host in HOSTS:
            package = Path(cls.temporary.name) / host / "office"
            render_plugin(cls.plugin, load_adapter(REPO_ROOT / "adapters", host), package,
                          adapters_root=REPO_ROOT / "adapters")
            cls.packages[host] = package

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def test_intake_asks_the_planning_decisions_once(self):
        intake = _normalized((SKILLS / "intake/SKILL.md").read_text(encoding="utf-8"))
        for decision in ("purpose and goal", "audience", "scope", "delivery", "length or slides to add", "density"):
            self.assertIn(decision, intake)
        self.assertIn("propose a length with its reasoning instead of asking an open question", intake)

    def test_planning_reference_owns_budget_density_ledger_and_deck_delta(self):
        plan = _normalized((SKILLS / "pptx/references/content-planning.md").read_text(encoding="utf-8"))
        for obligation in ("one content slide per 1 to 2 minutes", "Never shrink text or exceed the density caps",
                           "| Light |", "| Standard |", "| Dense |", "claim ledger",
                           "Quotes, figures and names come only from sources",
                           "A core claim with no slide is a defect of the plan",
                           "only with the user's approval", "never a second slide with the opposite claim",
                           "pptx_inspect.py coverage", "The plan never decides colours, fonts or object geometry"):
            self.assertIn(obligation, plan)
        statuses = set(re.findall(r"^\| `([a-z]+)` \|", (SKILLS / "pptx/references/content-planning.md")
                                  .read_text(encoding="utf-8"), re.M))
        self.assertEqual(statuses, set(preview.SLIDE_STATUSES) | {"cut"})

    def test_strategist_is_dispatched_first_and_never_designs(self):
        sidecar = (office_entries.DAODAN / "workflows/presentation.toml").read_text(encoding="utf-8")
        self.assertIn('"office/content-strategist"', sidecar)
        method = _normalized((SKILLS / "pptx/SKILL.md").read_text(encoding="utf-8"))
        self.assertLess(method.index("Dispatch `office:content-strategist` first"),
                        method.index("Dispatch `office:presentation-designer`"))
        self.assertIn("The designer keeps the plan's slide order, claims and patterns", method)
        for host, package in self.packages.items():
            with self.subTest(host=host):
                body = _normalized((package / ROLE_PATHS[host].format(role="content-strategist")).read_text(encoding="utf-8"))
                self.assertIn("references/content-planning.md", body)
                self.assertIn("Do not choose colours, fonts, directions or object geometry", body)
                self.assertIn("Never write a figure, quote, name or result that no source contains", body)
                self.assertIn("must pass `design_preview.py` validation", body)
                # The presentation entry is a `daodan` workflow; Copilot's prompt
                # entry hands off to a coordinator agent that holds the method.
                entry = office_entries.entry_path(self.entries[host], host, "presentation")
                harness = _normalized(loaded_instruction_text(self, entry, host))
                self.assertIn("dispatch `office:content-strategist` first", harness)

    def test_preview_shows_plan_status_and_rejects_unknown_status(self):
        library = preview.load_library()
        slides = [{"pattern": "cover", "title": "Review"},
                  {"pattern": "chart and insight", "headline": "Revenue grew in every region",
                   "status": "updated", "claims": ["C1", "C4"]}]
        document, problems = preview.build_document({"direction": {"library": "A"}, "slides": slides}, library)
        self.assertEqual([], problems)
        self.assertIn("<th>Status</th><th>Claims</th>", document)
        self.assertIn("<td>updated</td><td>C1, C4</td>", document)
        slides[1]["status"] = "rewritten"
        _, problems = preview.build_document({"direction": {"library": "A"}, "slides": slides}, library)
        self.assertTrue(any("status 'rewritten'" in problem for problem in problems))


OPERATIONS = ("Create", "Derive", "Expand", "Revise", "Restyle", "Edit", "Review or export")


class OperationTests(unittest.TestCase):
    """The workflow runs only the steps an operation needs; an existing file supplies the rest."""

    @staticmethod
    def table_rows(path, heading):
        """Rows of the first table under the heading, keyed by their first cell."""
        lines = path.read_text(encoding="utf-8").split(heading, 1)[1].splitlines()
        start = next(index for index, line in enumerate(lines) if line.startswith("|"))
        table = []
        for line in lines[start:]:
            if not line.startswith("|"):
                break
            table.append(line)
        return {cells[0]: cells for cells in (
            [cell.strip() for cell in line.strip().strip("|").split("|")] for line in table[2:])}

    def test_intake_names_every_operation_with_its_route_and_inheritance(self):
        rows = self.table_rows(SKILLS / "intake/SKILL.md", "## Resolve the operation")
        self.assertEqual(set(OPERATIONS), set(rows))
        routes = {name: row[2] for name, row in rows.items()}
        self.assertEqual({"Substantial"}, {routes[name] for name in ("Create", "Derive", "Expand", "Revise", "Restyle")})
        self.assertEqual(("Narrow", "Read-only"), (routes["Edit"], routes["Review or export"]))
        self.assertIn("direction, palette, fonts, template", rows["Expand"][3])
        intake = _normalized((SKILLS / "intake/SKILL.md").read_text(encoding="utf-8"))
        self.assertIn("Everything the file supplies is inherited and stated back, never asked again", intake)
        self.assertIn("run the union of their steps", intake)

    def test_presentation_runs_only_the_operations_steps(self):
        rows = self.table_rows(SKILLS / "pptx/SKILL.md", "## Run only the steps the operation needs")
        self.assertEqual(set(OPERATIONS), set(rows))
        plan, theme, design = 1, 2, 3
        self.assertTrue(rows["Create"][plan].startswith("Full plan"))
        for operation in ("Expand", "Revise"):
            self.assertTrue(rows[operation][plan].startswith("Delta plan"), operation)
            self.assertTrue(rows[operation][theme].startswith("Inherited"), operation)
            self.assertNotIn("Every slide", rows[operation][design])
        for operation in ("Restyle", "Edit", "Review or export"):
            self.assertTrue(rows[operation][plan].startswith("None"), operation)
        self.assertIn("generate the base", rows["Restyle"][theme])
        self.assertEqual("None", rows["Edit"][design])

    def test_planning_and_design_skip_what_the_operation_inherits(self):
        rows = self.table_rows(SKILLS / "pptx/references/content-planning.md", "## Which plan the operation needs")
        self.assertEqual("Delta", rows["Expand"][1])
        self.assertIn("argument mode", rows["Expand"][3])
        planning = _normalized((SKILLS / "pptx/references/content-planning.md").read_text(encoding="utf-8"))
        self.assertIn("Do not re-plan, reword or re-pattern a slide the request does not touch", planning)
        design = _normalized((SKILLS / "design/SKILL.md").read_text(encoding="utf-8"))
        self.assertIn("An expansion or revision inherits the file's direction, palette, pairing and template", design)
        docx = _normalized((SKILLS / "docx/SKILL.md").read_text(encoding="utf-8"))
        self.assertIn("Expand and revise inherit the document's type, styles, theme and template", docx)
        for role in ("presentation-designer", "document-designer"):
            body = _normalized((OFFICE / "roles" / f"{role}.md").read_text(encoding="utf-8"))
            self.assertIn("Design only the", body)
            self.assertIn("leave every other", body)
        strategist = _normalized((OFFICE / "roles/content-strategist.md").read_text(encoding="utf-8"))
        self.assertIn("a delta plan for expand and revise", strategist)


class RoutingTests(unittest.TestCase):
    """One entry reads the inputs, maps the decisions and routes to the right workflows."""

    ROUTING = SKILLS / "intake/references/routing.md"

    def test_route_table_reaches_every_workflow_and_operation(self):
        plugin = load_plugin(OFFICE)
        rows = OperationTests.table_rows(self.ROUTING, "## 3. Route to workflows and operations")
        cells = " ".join(" ".join(row) for row in rows.values())
        for workflow in set(plugin.components.workflows) - {"start"}:
            with self.subTest(workflow=workflow):
                self.assertTrue(f"`{workflow}`" in cells or "the format's workflow" in cells)
        for operation in OPERATIONS:
            with self.subTest(operation=operation):
                self.assertIn(operation.split(" or ")[0], cells)

    def test_routing_settles_from_inputs_and_leaves_the_conversation_to_work_controller(self):
        routing = _normalized(self.ROUTING.read_text(encoding="utf-8"))
        for rule in ("belongs to `work-controller:work-record`",
                     "settle every decision the request states or an input supplies",
                     "the agent never answers a user decision itself",
                     "in one round, one decision per question, with the recommended option first",
                     "A recorded brief is that workflow's intake round",
                     "A URL is fetched only to read it"):
            self.assertIn(rule, routing)
        for duplicate in ("| Settled |", "Discoverable", "## 4. Build the decision map"):
            self.assertNotIn(duplicate, routing, "the decision map is work-controller's, not duplicated here")
        intake = _normalized((SKILLS / "intake/SKILL.md").read_text(encoding="utf-8"))
        self.assertIn("A brief already recorded by routing is this round", intake)
        self.assertIn("`work-controller:work-record`", intake)
        plugin = load_plugin(OFFICE)
        self.assertIn("work-controller", plugin.required_dependencies)

    def test_start_declares_every_role_and_ships_on_every_host(self):
        plugin = load_plugin(OFFICE)
        # The start entry is a `daodan` workflow that dispatches every office role.
        entry_plugin = office_entries.entry_plugin(("start",))
        start = next(item for item in entry_plugin.workflows if item.name == "start")
        self.assertTrue(start.dispatch.isolated)
        self.assertEqual({f"office/{role}" for role in plugin.components.roles}, set(start.dispatch.roles))
        with tempfile.TemporaryDirectory(dir=str(REPO_ROOT) if os.name == "nt" else None) as temporary:
            entries = office_entries.render_entries(temporary, ("start",))
            for host in HOSTS:
                package = Path(temporary) / host / "office"
                render_plugin(plugin, load_adapter(REPO_ROOT / "adapters", host), package,
                              adapters_root=REPO_ROOT / "adapters")
                with self.subTest(host=host):
                    text = _normalized(loaded_instruction_text(
                        self, office_entries.entry_path(entries[host], host, "start"), host))
                    self.assertIn("`references/routing.md`", text)
                    for method in ("`office:pptx`", "`office:docx`", "`office:xlsx`", "`office:integrity`"):
                        self.assertIn(method, text)
                    self.assertTrue((package / "skills/intake/references/routing.md").is_file())


class TemplateKitTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.candidates = self.directory / "candidates.json"
        result = {"candidates": [palette_tool.build_palette(variant, ["#1D4ED8", "#E76F51"])
                                 for variant in ("faithful", "dark")]}
        self.candidates.write_text(json.dumps(result), encoding="utf-8")

    def generate(self, name, *extra, variant="faithful"):
        out = self.directory / name
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            status = kit.main([str(out), "--palette", str(self.candidates), "--variant", variant, *extra])
        return status, json.loads(stream.getvalue()), out

    def parts(self, path):
        with zipfile.ZipFile(path) as archive:
            return {name: archive.read(name) for name in archive.namelist()}

    def test_potx_carries_template_type_master_layouts_and_theme(self):
        status, report, out = self.generate("base.potx", "--pairing", "2")
        self.assertEqual(0, status, report)
        parts = self.parts(out)
        self.assertIn(b"presentationml.template.main+xml", parts["[Content_Types].xml"])
        layouts = sorted(name for name in parts if re.fullmatch(r"ppt/slideLayouts/slideLayout\d+\.xml", name))
        self.assertEqual(9, len(layouts))
        self.assertNotIn(b"<p:sldIdLst>", parts["ppt/presentation.xml"])
        theme = ET.fromstring(parts["ppt/theme/theme1.xml"])
        latin = {font.get("typeface") for font in theme.iter(f"{{{A}}}latin")}
        self.assertEqual({"Source Serif 4", "Source Sans 3"}, latin)
        chosen = json.loads(self.candidates.read_text(encoding="utf-8"))["candidates"][0]
        dk1 = theme.find(f".//{{{A}}}dk1/{{{A}}}srgbClr").get("val")
        accent1 = theme.find(f".//{{{A}}}accent1/{{{A}}}srgbClr").get("val")
        self.assertEqual(chosen["ink"].lstrip("#").upper(), dk1)
        self.assertEqual(chosen["data"][0].lstrip("#").upper(), accent1)
        served = {pattern for layout in report["layouts"] for pattern in layout["patterns"]}
        catalogue = set(re.findall(r"^\| \d+ \| ([^|]+?) \|", (SKILLS / "pptx/references/layout-patterns.md")
                                   .read_text(encoding="utf-8"), re.M))
        self.assertEqual(catalogue, served, "every layout pattern is served by exactly the kit's layouts")
        for name, data in parts.items():
            if name.endswith((".xml", ".rels")):
                ET.fromstring(data)

    def test_samples_build_one_slide_per_layout_and_pass_verify(self):
        status, report, out = self.generate("sample.pptx", "--pairing", "1", "--samples")
        self.assertEqual(0, status, report)
        self.assertEqual(8, report["sample_slides"])
        # A sample inherits insets and anchoring from its layout: the 2026-10-25 render
        # showed card text flush against the edge when the slide carried its own bodyPr.
        for name, data in self.parts(out).items():
            if re.fullmatch(r"ppt/slides/slide\d+\.xml", name):
                self.assertNotIn(b"lIns=", data, name)
                self.assertNotIn(b"anchor=", data, name)
        result = verifier.verify(out)
        self.assertEqual("pass", result["verdict"], result["findings"])
        self.assertTrue(result["package_valid"])

    def test_dark_palette_swaps_the_colour_map(self):
        status, report, out = self.generate("dark.potx", "--pairing", "1", variant="dark")
        self.assertEqual(0, status, report)
        self.assertEqual({"bg1": "dk1", "tx1": "lt1", "bg2": "dk2", "tx2": "lt2"}, report["colour_map"])
        master = self.parts(out)["ppt/slideMasters/slideMaster1.xml"].decode("utf-8")
        self.assertIn('bg1="dk1" tx1="lt1"', master)

    def test_dotx_carries_template_type_styles_and_theme_fonts(self):
        status, report, out = self.generate("base.dotx", "--pairing", "4", "--page", "letter", "--samples")
        self.assertEqual(0, status, report)
        parts = self.parts(out)
        self.assertIn(b"wordprocessingml.template.main+xml", parts["[Content_Types].xml"])
        styles = ET.fromstring(parts["word/styles.xml"])
        ids = {style.get(f"{{{W}}}styleId") for style in styles.iter(f"{{{W}}}style")}
        self.assertTrue({"Title", "Heading1", "Heading2", "Heading3", "Quote", "Caption", "KitTable"} <= ids)
        heading = next(style for style in styles.iter(f"{{{W}}}style") if style.get(f"{{{W}}}styleId") == "Heading1")
        self.assertEqual("majorHAnsi", heading.find(f".//{{{W}}}rFonts").get(f"{{{W}}}asciiTheme"))
        self.assertIn(b'w:w="12240"', parts["word/document.xml"])
        self.assertIn(b" PAGE ", parts["word/footer1.xml"])
        docx = self.directory / "base.docx"
        self.generate("base.docx", "--pairing", "4", "--samples")
        self.assertEqual("pass", verifier.verify(docx)["verdict"])

    def test_brand_fonts_override_the_pairing_and_odd_weights_are_noted(self):
        status, report, _ = self.generate("brand.potx", "--heading-font", "Brand Sans", "--body-font", "Brand Text")
        self.assertEqual(0, status, report)
        self.assertEqual(("Brand Sans", "Brand Text"), (report["fonts"]["major"], report["fonts"]["minor"]))
        _, semibold, _ = self.generate("semibold.potx", "--pairing", "2")
        self.assertTrue(any("600" in note for note in semibold["notes"]))

    def test_output_is_deterministic_and_never_overwritten(self):
        _, _, first = self.generate("a.potx", "--pairing", "1")
        _, _, second = self.generate("b.potx", "--pairing", "1")
        self.assertEqual(first.read_bytes(), second.read_bytes())
        status, report, _ = self.generate("a.potx", "--pairing", "1")
        self.assertEqual(1, status)
        self.assertIn("never overwritten", report["error"])

    def test_invalid_inputs_fail_without_writing(self):
        status, report, out = self.generate("bad.potx")
        self.assertEqual(1, status)
        self.assertFalse(out.exists())
        status, report, _ = self.generate("bad.pdf", "--pairing", "1")
        self.assertEqual(1, status)
        self.assertIn(".potx", report["error"])

    def test_design_method_and_theme_entry_use_the_kit(self):
        design = _normalized((SKILLS / "design/SKILL.md").read_text(encoding="utf-8"))
        self.assertIn("template_kit.py", design)
        self.assertIn("build on that file itself", design)
        pptx = _normalized((SKILLS / "pptx/SKILL.md").read_text(encoding="utf-8"))
        self.assertNotIn("Do not label a PPTX exemplar as a PowerPoint `.potx` template", pptx)
        self.assertIn("template_kit.py", pptx)
        plugin = load_plugin(OFFICE)
        # The theme entry is a `daodan` workflow; office owns the design method.
        self.assertEqual(set(plugin.components.workflows), set())
        self.assertIn("theme", load_plugin(office_entries.DAODAN).components.workflows)
        theme = _normalized((office_entries.DAODAN / "workflows/theme.md").read_text(encoding="utf-8"))
        for obligation in ("Load `office:design`", "inherit it as direction `H`", "template_kit.py", "office:integrity"):
            self.assertIn(obligation, theme)


if __name__ == "__main__":
    unittest.main()
