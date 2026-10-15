"""Protect the isolated classic analysis owner and coordinator boundaries."""

import re
import sys
import tempfile
import tomllib
import unittest
from dataclasses import replace
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "codebase-map"
METHOD = PLUGIN / "skills" / "map-method"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.daodan.adapter import HOSTS, load_adapter  # noqa: E402
from scripts.daodan.load import load_plugin  # noqa: E402
from scripts.daodan.render import render_plugin  # noqa: E402
from scripts.daodan.templates import render_path  # noqa: E402

TEAM_ROLE_TRIGGERS = {
    "partition-structure-worker": "spawned by /codebase-map:team-analyze in its first wave.",
    "partition-synthesizer": "spawned by /codebase-map:team-analyze in its consolidation phase.",
}


def read(relative):
    return (PLUGIN / relative).read_text(encoding="utf-8")


def loads(body):
    """Resource/section/condition triples declared in the current load table."""
    active = False
    result = []
    for line in body.splitlines():
        if re.match(r"^#{1,2} ", line):
            active = line == "## Method loads"
        if active and line.startswith("| `"):
            result.append(tuple(item.strip().strip("`") for item in line.strip("|").split("|")))
    return result


def description(body):
    """Read the folded source or quoted rendered scalar without a YAML dependency."""
    lines = body.split("\n---\n", 1)[0].splitlines()
    index = next(index for index, line in enumerate(lines) if line.startswith("description:"))
    value = lines[index].partition(":")[2].strip()
    if value == ">":
        folded = []
        for line in lines[index + 1:]:
            if not line.startswith("  "):
                break
            folded.append(line.strip())
        value = " ".join(folded)
    return " ".join(value.strip("'\"").split())


class CodebaseMapAnalysisOwnerTests(unittest.TestCase):
    def test_analysis_is_required_isolation_between_shared_preflight_and_publish(self):
        workflow = tomllib.loads(read("workflows/analyze.toml"))
        self.assertEqual([phase["id"] for phase in workflow["phases"]], ["preflight", "analysis", "publish"])
        preflight, analysis, publish = workflow["phases"]
        self.assertEqual(preflight["isolation"], "shared")
        self.assertEqual(analysis["role"], "map-analyst")
        self.assertEqual(analysis["isolation"], "required")
        self.assertEqual(analysis["needs"], ["preflight"])
        self.assertEqual(publish["isolation"], "shared")
        self.assertEqual(publish["needs"], ["analysis"])
        self.assertEqual(analysis["consumes"], preflight["produces"])
        self.assertEqual(publish["consumes"], analysis["produces"])

    def test_coordinator_loads_no_source_or_phase_procedure(self):
        entry = read("skills/map-method/references/entry-analyze.md")
        rows = loads(entry)
        resources = {row[0].rsplit("/", 1)[-1] for row in rows if row[2] == "always"}
        self.assertEqual(resources, {"SKILL.md", "run.md", "snapshot.md"})
        router = next(row for row in rows if row[0].endswith("SKILL.md"))
        self.assertIn("before: Method loads", router[1])
        self.assertEqual({row[2] for row in rows}, {"always", "migration"})
        self.assertNotIn("execute phases inline", entry.lower())
        self.assertNotIn("before applying changes", entry)
        self.assertIn("codebase-map:map-analyst", entry)
        self.assertRegex(entry, r"Do not read analyzed\s+source")

    def test_worker_reads_only_selected_phase_sections_and_never_publishes(self):
        analyst = read("roles/map-analyst.md")
        rows = loads(analyst)
        conditions = {when for _, _, when in rows}
        self.assertTrue({f"phase-{phase}" for phase in range(1, 8)} <= conditions)
        self.assertIn("update", conditions)
        self.assertNotIn("references/run.md", {resource.removeprefix("${CLAUDE_PLUGIN_ROOT}/skills/map-method/") for resource, _, _ in rows})
        for resource, selector, when in rows:
            if resource.endswith(("phases-1-2.md", "phases-3-4.md", "phases-5-6.md", "phase-7.md")):
                self.assertNotEqual(selector, "all", (resource, when))
        self.assertIn("Ask no questions", analyst)
        self.assertIn("Never edit analyzed source", analyst)
        self.assertIn("Never publish", analyst)
        self.assertRegex(analyst, r"snapshot\s+owner")
        self.assertNotIn("scripts/snapshot.py\" publish", analyst)

    def test_partial_and_resume_controls_are_entry_owned(self):
        entry = read("skills/map-method/references/entry-analyze.md")
        self.assertIn("--phase 7", entry)
        self.assertIn("--resume-from [N]", entry)
        self.assertIn("--stop-after N", entry)
        self.assertIn("--run-name", entry)
        self.assertIn("same mode and flags", entry)
        self.assertIn("first_incomplete_phase", entry)
        self.assertIn("not_yet_produced", entry)
        self.assertIn("may_publish", entry)
        self.assertNotIn("start at phase N", entry)
        self.assertIn("check $RUN_DIR --json", entry)
        self.assertIn("publish $RUN_DIR", entry)

    def test_shared_run_contract_has_whole_mirror_replacement(self):
        run = read("skills/map-method/references/run.md")
        self.assertIn("whole mirror", run)
        self.assertIn("08-interconnect-map.md", run)
        self.assertIn("may_publish", run)
        self.assertNotIn("runs every phase inline", run)

    def test_team_publication_uses_same_gate_without_changing_worker_topology(self):
        team = read("skills/map-method/references/entry-team-analyze.md")
        self.assertIn("prepare $RUN_DIR", team)
        self.assertIn("check $RUN_DIR --json", team)
        self.assertIn("publish $RUN_DIR", team)
        self.assertIn("08-interconnect-map.md", team)
        self.assertIn("skip-interconnect", team)
        self.assertIn("Wave 2 starts only after every Wave 1 worker", team)
        self.assertIn("may_publish", team)


class CodebaseMapTeamRoleMetadataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="daodan-map-role-metadata-")
        cls.addClassCleanup(cls.temp.cleanup)
        cls.plugins = {name: load_plugin(ROOT / "plugins" / name)
                       for name in ("codebase-map", "codebase-xray")}
        cls.adapters = {host: load_adapter(ROOT / "adapters", host) for host in HOSTS}
        cls.packages = {}
        for host, adapter in cls.adapters.items():
            for name, plugin in cls.plugins.items():
                # Render only the affected role components. This fixture proves
                # metadata adaptation, not a runnable installed package.
                fixture = replace(plugin, components=replace(
                    plugin.components, skills=(), roles=tuple(TEAM_ROLE_TRIGGERS),
                    workflows=(), policies=(),
                ), workflows=(), contract_exports=())
                package = Path(cls.temp.name) / host / name
                render_plugin(fixture, adapter, package, adapters_root=ROOT / "adapters")
                cls.packages[(host, name)] = package

    def assert_team_only(self, text, role):
        trigger, exclusion = text.split("TRIGGER WHEN:", 1)[1].split("DO NOT TRIGGER WHEN:", 1)
        self.assertEqual(trigger.strip(), TEAM_ROLE_TRIGGERS[role])
        self.assertNotIn("/codebase-map:analyze", trigger)
        self.assertIn("Classic /codebase-map:analyze dispatches isolated codebase-map:map-analyst.",
                      exclusion)
        self.assertRegex(exclusion, r"outside that (?:team )?pipeline")
        for obsolete in ("inline without an agent", "writes its phase files directly", "no-agent"):
            self.assertNotIn(obsolete, text)

    def test_source_role_metadata_keeps_team_triggers_and_redirects_classic_to_the_analyst(self):
        for role in TEAM_ROLE_TRIGGERS:
            canonical = read(f"roles/{role}.md")
            legacy = (self.plugins["codebase-xray"].root / "roles" / f"{role}.md").read_text(
                encoding="utf-8"
            )
            self.assertEqual(canonical.split("\n---\n", 1)[0], legacy.split("\n---\n", 1)[0])
            for name, body in (("codebase-map", canonical), ("codebase-xray", legacy)):
                with self.subTest(plugin=name, role=role):
                    self.assert_team_only(description(body), role)

    def test_all_five_hosts_preserve_the_complete_team_role_description(self):
        for host, adapter in self.adapters.items():
            for name, plugin in self.plugins.items():
                for role in TEAM_ROLE_TRIGGERS:
                    with self.subTest(host=host, plugin=name, role=role):
                        relative = render_path(adapter.layout["roles"], {"plugin": name, "role": role})
                        rendered = (self.packages[(host, name)] / relative).read_text(encoding="utf-8")
                        source = (plugin.root / "roles" / f"{role}.md").read_text(encoding="utf-8")
                        self.assertEqual(description(rendered), description(source))
                        self.assert_team_only(description(rendered), role)


if __name__ == "__main__":
    unittest.main()
