"""Office routing hook: a prompt naming an Office file reaches the Daodan Office entries.

Search-before-write found no suite for this hook; test_daodan_hooks.py covers the
generic declaration-to-execution contract on a fixture, not this script. Runs the
shipped script as a subprocess on JSON payloads, no network. Target runtime: under 10 seconds.
"""

import json
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.daodan.load import load_plugin  # noqa: E402

OFFICE = REPO_ROOT / "plugins/office"
SCRIPT = OFFICE / "skills/intake/scripts/office_hook.py"


def run_hook(stdin):
    return subprocess.run([sys.executable, "-I", str(SCRIPT)], input=stdin, capture_output=True,
                          text=True, timeout=30, check=False)


def prompt(text, event="UserPromptSubmit"):
    return json.dumps({"hook_event_name": event, "cwd": "/project", "prompt": text})


class OfficeRoutingHookTests(unittest.TestCase):
    def test_kernel_declares_the_hook_on_a_shipped_skill_script(self):
        plugin = load_plugin(OFFICE)
        self.assertEqual([(h.name, h.event, h.script.as_posix()) for h in plugin.hooks],
                         [("office-routing", "user-prompt-submit", "skills/intake/scripts/office_hook.py")])

    def test_office_prompts_name_the_entries_and_forbid_generic_libraries(self):
        for text in ("espandiamo il pptx, facciamo prima un backup", "Fix the formulas in budget.xlsx",
                     "crea una presentazione per il cliente", "open this PowerPoint deck",
                     "analizza il foglio di calcolo", "convert the Word document to a workbook"):
            with self.subTest(text=text):
                result = run_hook(prompt(text))
                self.assertEqual(result.returncode, 0, result.stderr)
                specific = json.loads(result.stdout)["hookSpecificOutput"]
                self.assertEqual(specific["hookEventName"], "UserPromptSubmit")
                for needle in ("presentation, document, workbook", "python-pptx", "missing provider"):
                    self.assertIn(needle, specific["additionalContext"])

    def test_other_prompts_stay_silent(self):
        for stdin in (prompt("fix the login bug in auth.ts"), prompt("run the tests"),
                      prompt("espandiamo il pptx", event="SessionStart"),
                      json.dumps({"hook_event_name": "UserPromptSubmit"}),
                      json.dumps({"hook_event_name": "UserPromptSubmit", "prompt": 3}),
                      "[]", "not json", ""):
            with self.subTest(stdin=stdin):
                result = run_hook(stdin)
                self.assertEqual((result.returncode, result.stdout), (0, ""))


if __name__ == "__main__":
    unittest.main()
