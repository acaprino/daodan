"""Published phase headings have one owner and preserve real consumer lookups."""

import re
import unittest
from pathlib import Path

from test_xray_load_budget import _rows, _selected


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins/codebase-xray"
METHOD = PLUGIN / "skills/xray-method"
PHASE_UNITS = {
    1: "phases-1-2", 2: "phases-1-2", 3: "phases-3-4",
    4: "phases-3-4", 5: "phases-5-6", 6: "phases-5-6", 7: "phase-7",
}
FILES = {
    1: "01-structure.md", 2: "02-interfaces.md", 3: "03-flows.md",
    4: "04-semantics.md", 5: "05-risks.md", 6: "06-documentation.md",
    7: "07-final-report.md",
}
LOOKUPS = {
    "02-interfaces.md": "Cross-Partition Exports",
    "03-flows.md": "Cross-Partition Flows",
    "04-semantics.md": "Hidden Contracts (cross-partition)",
    "05-risks.md": "Cross-Partition Risk Attribution",
}
CONSOLIDATED_HEADINGS = {
    1: ["Partition Map", "File Inventory", "Dependency Graph", "Entry Points", "Cross-Partition Reference Summary", "Key Observations", "Where to Add New Code", "Naming Conventions", "Source reading"],
    2: ["Public APIs", "Cross-Partition Exports", "Contracts", "External Dependencies", "How to Add a New Module", "Source reading"],
    3: ["Critical Paths", "Cross-Partition Flows", "Data Flow", "Error Handling Paths", "Side Effects", "Process Diagrams", "Source reading"],
    4: ["Module Purposes", "Design Decisions", "Architecture Decision Records", "Cross-Partition ADR", "Embedded Assumptions", "Hidden Contracts", "Hidden Contracts (cross-partition)", "Conventions to Follow", "Source reading"],
    5: ["Anti-Patterns Found", "Red Flags", "Technical Debt Inventory", "Failure Mode Analysis", "Cross-Partition Risk Attribution", "Source reading"],
    6: ["Documentation vs Code Accuracy", "Coverage Gaps", "Broken References", "Comment Quality", "Source reading"],
    7: ["Partial Completeness Warning", "Target", "Executive Summary", "Project at a Glance", "Partition Map", "Cross-Partition Topology", "Architecture Overview", "Technology Decisions", "Critical Paths", "Key Process Diagrams", "Design Insights", "Per-Partition Health Scorecard", "Risk Assessment", "Documentation vs Reality", "Top Priority Actions", "Detailed Findings", "Quick Reference: Which File to Consult", "Analysis Metadata"],
}


def blocks(text):
    return re.findall(r"^```markdown\n(.*?)^```\s*$", text, re.M | re.S)


def headings(text):
    return re.findall(r"^## (.+)$", text, re.M)


def extensions(text):
    """Read the documented team-extension table, independently of role prose."""
    rows = []
    if "## Team mode\n" not in text:
        return rows
    team = text.split("## Team mode\n", 1)[1]
    for line in team.splitlines():
        if not line.startswith("| "):
            continue
        cells = [cell.strip().strip("`") for cell in line.strip("|").split("|")]
        if len(cells) == 6 and cells[1] in FILES.values():
            rows.append(dict(zip(("heading", "file", "mode", "writer", "after", "aggregation"), cells)))
    return rows


class XraySkeletonTests(unittest.TestCase):
    def test_each_phase_has_one_canonical_skeleton(self):
        for phase, name in PHASE_UNITS.items():
            text = (METHOD / "references" / f"{name}.md").read_text(encoding="utf-8")
            title = "# Codebase X-Ray Analysis Report" if phase == 7 else f"# Phase {phase}:"
            matched = [block for block in blocks(text) if block.startswith(title)]
            with self.subTest(phase=phase):
                self.assertEqual(len(matched), 1)
                if phase < 7:
                    self.assertIn("Source reading", headings(matched[0]))

    def test_roles_do_not_carry_secondary_phase_skeletons(self):
        for path in [*PLUGIN.glob("roles/*.md"), *PLUGIN.glob("workflows/*.md")]:
            for block in blocks(path.read_text(encoding="utf-8")):
                self.assertNotRegex(block, r"^# (?:Phase [1-7]:|Partition:|Codebase X-Ray Analysis Report)", path.name)

    def test_common_headings_have_no_mode_qualifiers(self):
        qualifiers = r"\((?:by partition|per partition|consolidated|global|within this partition|Team Mode)\)|\[if"
        for name in set(PHASE_UNITS.values()):
            for block in blocks((METHOD / "references" / f"{name}.md").read_text(encoding="utf-8")):
                for heading in headings(block):
                    self.assertNotRegex(heading, qualifiers)

    def test_extensions_declare_writer_position_and_aggregation(self):
        declared = []
        for name in set(PHASE_UNITS.values()):
            text = (METHOD / "references" / f"{name}.md").read_text(encoding="utf-8")
            rows = extensions(text)
            self.assertTrue(rows, name)
            canonical = {heading for block in blocks(text) for heading in headings(block)}
            for row in rows:
                self.assertIn(row["mode"], ("partition", "consolidated"))
                self.assertTrue((PLUGIN / "roles" / f"{row['writer']}.md").is_file(), row)
                self.assertTrue(row["aggregation"], row)
                self.assertTrue(row["after"] in canonical or row["after"] == "first", row)
                self.assertNotIn((row["file"], row["mode"], row["heading"]), declared)
                declared.append((row["file"], row["mode"], row["heading"]))
        for filename, heading in LOOKUPS.items():
            self.assertIn((filename, "consolidated", heading), declared)

    def test_real_mapper_and_coordinator_lookups_resolve(self):
        available = set()
        for name in set(PHASE_UNITS.values()):
            for row in extensions((METHOD / "references" / f"{name}.md").read_text(encoding="utf-8")):
                if row["mode"] == "consolidated":
                    available.add((row["file"], row["heading"]))
        for rel in ("roles/semantic-interconnect-mapper.md", "workflows/team-analyze.md"):
            text = (PLUGIN / rel).read_text(encoding="utf-8")
            found = re.findall(r"`(?:<RUN_DIR>/)?(0[1-7]-[a-z-]+\.md) ## ([^`]+)`", text)
            self.assertGreaterEqual(len(found), 4, rel)
            for lookup in found:
                self.assertIn(lookup, available, (rel, lookup))

    def test_workers_and_synthesizer_load_the_owned_skeletons(self):
        units = {
            "partition-structure-worker": ("phases-1-2",),
            "partition-behavior-worker": ("phases-3-4",),
            "partition-quality-worker": ("phases-5-6",),
            "partition-synthesizer": ("phases-1-2", "phases-3-4", "phases-5-6", "phase-7"),
        }
        for role, names in units.items():
            text = (PLUGIN / "roles" / f"{role}.md").read_text(encoding="utf-8")
            for name in names:
                self.assertIn(f"references/{name}.md", text, role)

    def test_retired_templates_have_no_runtime_citers(self):
        retired = ("references/analysis-templates.md", "templates/semantic_analysis.md", "templates/analysis_report.md")
        for path in PLUGIN.rglob("*.md"):
            if any(path.name == Path(name).name for name in retired):
                continue
            text = path.read_text(encoding="utf-8")
            for name in retired:
                self.assertNotIn(name, text, str(path))
        for name in retired:
            self.assertFalse((METHOD / name).exists(), name)

    def test_selected_behavior_instructions_identify_cross_partition_contracts(self):
        worker = (PLUGIN / "roles/partition-behavior-worker.md").read_text(encoding="utf-8")
        selected = []
        for path, selector, when in _rows(worker):
            if path != "references/phases-3-4.md":
                continue
            self.assertEqual(when, "always")
            text = (METHOD / path).read_text(encoding="utf-8")
            lines = text.splitlines()
            selected.extend(lines[index] for index in sorted(_selected(text, selector)))
        instructions = "\n".join(selected)
        self.assertRegex(instructions, r"Hidden Contracts[^\n]*<this-partition> ↔ <other-partition>")
        phase = (METHOD / "references/phases-3-4.md").read_text(encoding="utf-8")
        registry = next(row for row in extensions(phase) if row["heading"] == "Hidden Contracts (cross-partition)")
        self.assertIn("<this> ↔ <other>", registry["aggregation"])

    def test_consolidated_heading_order_matches_the_published_contract(self):
        for phase, expected in CONSOLIDATED_HEADINGS.items():
            text = (METHOD / "references" / f"{PHASE_UNITS[phase]}.md").read_text(encoding="utf-8")
            title = "# Codebase X-Ray" if phase == 7 else f"# Phase {phase}:"
            skeleton = next(block for block in blocks(text) if block.startswith(title))
            rows = [row for row in extensions(text) if row["file"] == FILES[phase] and row["mode"] == "consolidated"]
            ordered = [row["heading"] for row in rows if row["after"] == "first"]
            for heading in headings(skeleton):
                ordered.append(heading)
                ordered.extend(row["heading"] for row in rows if row["after"] == heading)
            with self.subTest(phase=phase):
                self.assertEqual(ordered, expected)

    def test_consolidation_and_quick_reference_targets_exist(self):
        for name in set(PHASE_UNITS.values()):
            text = (METHOD / "references" / f"{name}.md").read_text(encoding="utf-8")
            for line in text.split("### Consolidation\n", 1)[1].splitlines():
                cells = [cell.strip() for cell in line.strip("|").split("|")]
                if len(cells) != 3 or cells[0] not in FILES.values():
                    continue
                phase = next(phase for phase, file in FILES.items() if file == cells[0])
                self.assertIn(cells[1], CONSOLIDATED_HEADINGS[phase])
        report = (METHOD / "references/phase-7.md").read_text(encoding="utf-8")
        quick_reference = report.split("## Quick Reference: Which File to Consult", 1)[1].split("## Analysis Metadata", 1)[0]
        names = {Path(file).stem for file in FILES.values()}
        for target in re.findall(r"0[1-7]-[a-z-]+", quick_reference):
            self.assertIn(target, names)
        for phase, heading in ((4, "Cross-Partition ADR"), (2, "Cross-Partition Exports")):
            self.assertIn(f"0{phase} {heading}", report)
            self.assertIn(heading, CONSOLIDATED_HEADINGS[phase])


if __name__ == "__main__":
    unittest.main()
