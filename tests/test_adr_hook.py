"""Decision-record session hook: context per project state, silence on a no or on bad input.

Search-before-write found no suite for this hook; test_daodan_hooks.py covers the
generic declaration-to-execution contract on a fixture, not this script. Runs the
shipped script as a subprocess on JSON payloads, no network. Target runtime: under 30 seconds.
"""

import json
import os
import re
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.daodan.load import load_plugin  # noqa: E402

DELIVERY = REPO_ROOT / "plugins/project-delivery"
SCRIPT = DELIVERY / "skills/adr-method/scripts/adr_hook.py"


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))


class AdrHookTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.project = self.root / "project"
        self.project.mkdir()
        self.env = {**os.environ, "GIT_CEILING_DIRECTORIES": str(self.root)}

    def git(self, *arguments):
        subprocess.run(["git", "-C", str(self.project), *arguments], capture_output=True, check=True, env=self.env)

    def run_hook(self, stdin):
        started = time.monotonic()
        result = subprocess.run([sys.executable, "-I", str(SCRIPT)], input=stdin, capture_output=True, text=True,
                                timeout=30, check=False, env=self.env)
        self.assertLess(time.monotonic() - started, 10)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def session(self, cwd=None, event="SessionStart"):
        return json.dumps({"hook_event_name": event, "cwd": str(cwd or self.project), "source": "startup"})

    def context(self):
        specific = json.loads(self.run_hook(self.session()))["hookSpecificOutput"]
        self.assertEqual(specific["hookEventName"], "SessionStart")
        return specific["additionalContext"]

    def tree(self):
        return {path.relative_to(self.project).as_posix(): path.read_bytes() if path.is_file() else None
                for path in sorted(self.project.rglob("*")) if "objects" not in path.parts}

    def test_kernel_declares_an_optional_session_start_hook_on_a_shipped_skill_script(self):
        plugin = load_plugin(DELIVERY)
        self.assertEqual([(h.name, h.event, h.script.as_posix(), h.timeout) for h in plugin.hooks],
                         [("decision-records", "session-start", "skills/adr-method/scripts/adr_hook.py", 10)])
        self.assertIn("hooks.lifecycle", plugin.capabilities.optional)
        self.assertNotIn("hooks.lifecycle", plugin.capabilities.required)

    def test_active_project_records_settled_decisions_and_cites_foreign_records(self):
        self.git("init", "-q")
        write(self.project / "docs/adr/README.md",
              "# Architecture decision records\n\n<!-- adr-index:start -->\n<!-- adr-index:end -->\n")
        write(self.project / "doc/adr/0001-use-postgres.md", "# 1. Use Postgres\n")
        self.git("add", "doc")
        before = self.tree()
        text = self.context()
        for needle in ("project-delivery:adr-method", "Proposed", "whatever brainstorming or design method",
                       "approves its exact text", '["doc/adr"]', "never write them"):
            self.assertIn(needle, text)
        self.assertEqual(self.tree(), before)

    def test_undecided_project_asks_once_at_the_first_settled_decision(self):
        self.git("init", "-q")
        before = self.tree()
        text = self.context()
        for needle in ("ask the user once", "yes is the default", "Never ask at session start",
                       "init-index", "decline", "/daodan:record-decision"):
            self.assertIn(needle, text)
        self.assertEqual(self.tree(), before)

    def test_context_names_no_other_plugin_or_skill(self):
        self.git("init", "-q")
        undecided = self.context()
        write(self.project / "docs/frd/README.md", "# Requirements\n")
        active = self.context()
        for text in (undecided, active):
            with self.subTest(text=text[:40]):
                names = set(re.findall(r"/?[a-z][a-z0-9-]*:[a-z][a-z0-9-]*", text))
                self.assertLessEqual(names, {"project-delivery:adr-method", "/daodan:record-decision"})

    def test_declined_project_prints_nothing_in_git_and_outside_git(self):
        self.git("init", "-q")
        self.assertIn("ask the user once", self.context())
        self.git("config", "--local", "daodan.decisionRecords", "declined")
        self.assertEqual(self.run_hook(self.session()), "")
        outside = self.root / "outside"
        outside.mkdir()
        self.assertIn("ask the user once", self.run_hook(self.session(outside)))
        write(outside / ".daodan/adr-declined", "declined\n")
        self.assertEqual(self.run_hook(self.session(outside)), "")

    def test_a_subdirectory_session_classifies_the_work_tree_root_and_names_it(self):
        self.git("init", "-q")
        write(self.project / "docs/frd/README.md", "# Requirements\n")
        nested = self.project / "src/app"
        nested.mkdir(parents=True)
        specific = json.loads(self.run_hook(self.session(nested)))["hookSpecificOutput"]
        text = specific["additionalContext"]
        self.assertIn("project-delivery:adr-method", text)
        self.assertIn("--project", text)
        self.assertEqual(text.splitlines()[-1], "Project root (data): " + json.dumps(str(self.project)))

    def test_foreign_directories_are_one_bounded_data_line_after_the_instructions(self):
        self.git("init", "-q")
        names = [f"part{number}/adr" for number in range(1, 8)]
        for name in names:
            write(self.project / name / "0001-use-postgres.md", "# 1. Use Postgres\n")
        self.git("add", ".")
        lines = self.context().splitlines()
        data = [line for line in lines if any(name in line for name in names)]
        self.assertEqual(data, ["Foreign record directories (data): " + json.dumps(names[:5]) + " and 2 more"])
        self.assertEqual(lines[-1], data[0])

    def test_malformed_or_foreign_input_prints_nothing(self):
        for stdin in ("", "not json", "[]", "{}", json.dumps({"hook_event_name": "SessionStart"}),
                      json.dumps({"hook_event_name": "SessionStart", "cwd": 7}),
                      json.dumps({"hook_event_name": "SessionStart", "cwd": str(self.root / "missing")}),
                      self.session(event="UserPromptSubmit")):
            with self.subTest(stdin=stdin):
                self.assertEqual(self.run_hook(stdin), "")


if __name__ == "__main__":
    unittest.main()
