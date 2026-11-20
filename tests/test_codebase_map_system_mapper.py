"""The system mapper closes every analysis.

Pinned: the tools its role names are tools the MCP server serves, under the name the plugin gives them; both
analysis entries start it in their last step, after publication; the sequence it follows is written once, in the map
format that `brief` returns (`daodan/references/system-map.md`), and the role points to it without a copy.
"""

import json
import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PLUGIN = REPO / "plugins/codebase-map"
ROLE = PLUGIN / "roles/system-mapper.md"
FORMAT = REPO / "daodan/references/system-map.md"
MAPPER = "codebase-map:system-mapper"
LAST_STEP = {"entry-analyze.md": "## ", "entry-team-analyze.md": "## Phase "}  # the last section with this heading


def section(text: str, heading: str) -> str:
    """The last second-level section whose heading starts with `heading`, up to the next one."""
    start = [m.start() for m in re.finditer(rf"^{re.escape(heading)}", text, re.M)][-1]
    end = text.find("\n## ", start)
    return text[start:] if end == -1 else text[start:end]


class SystemMapperTest(unittest.TestCase):
    def test_the_tools_of_the_role_exist(self):
        role = ROLE.read_text(encoding="utf-8")
        served = set(re.findall(r"async def (codebase_map_\w+)\(",
                                (REPO / "daodan/core/mcp_server.py").read_text(encoding="utf-8")))
        named = set(re.findall(r"codebase_map_\w+", role))
        self.assertTrue(named)
        self.assertLessEqual(named, served)
        plugin = json.loads((PLUGIN / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))["name"]
        [server] = json.loads((PLUGIN / ".mcp.json").read_text(encoding="utf-8"))["mcpServers"]
        tools = re.search(r"^tools: (.+)$", role, re.M).group(1).split(", ")
        self.assertEqual({t.removeprefix(f"mcp__plugin_{plugin}_{server}__") for t in tools}, named)

    def test_both_entries_start_the_mapper_in_their_last_step(self):
        for name, heading in LAST_STEP.items():
            text = (PLUGIN / "skills/map/references" / name).read_text(encoding="utf-8")
            last = section(text, heading)
            with self.subTest(entry=name):
                self.assertIn(MAPPER, last)
                self.assertNotIn(MAPPER, text[:text.index(last)])
                self.assertLess(last.index("publish $RUN_DIR"), last.index(MAPPER))

    def test_the_role_points_to_the_one_sequence(self):
        role, text = ROLE.read_text(encoding="utf-8"), FORMAT.read_text(encoding="utf-8")
        self.assertEqual(text.count("\n## Sequence\n"), 1)
        steps = re.findall(r"^\d+\. (.+)$", section(text, "## Sequence"), re.M)
        self.assertGreaterEqual(len(steps), 3)
        self.assertIn("«Sequence»", role)
        self.assertNotRegex(role, r"(?m)^(#+ Sequence|\d+\. )")
        self.assertFalse([step for step in steps if step in role])
        self.assertNotIn("no link rules", role)


if __name__ == "__main__":
    unittest.main()
