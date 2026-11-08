"""check_run verifies, per job, full reads of every newly covered file and counts tokens once."""
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import check_run  # noqa: E402

TEN_LINES = "".join(f"line {number}\n" for number in range(1, 11))
MAP_READ = "mcp__plugin_codebase-map_codebase-map__codebase_map_read"


class Transcript:
    """Stream-json events of one coordinator dispatching job workers."""

    def __init__(self, root: Path):
        self.root = root
        self.events = []
        self.count = 0

    def _id(self, prefix):
        self.count += 1
        return f"{prefix}{self.count}"

    def assistant(self, blocks, parent=None, message_id=None, usage=None):
        self.events.append({"type": "assistant", "parent_tool_use_id": parent,
                            "message": {"id": message_id or self._id("msg"), "content": blocks,
                                        "usage": usage or {"input_tokens": 10, "output_tokens": 5}}})

    def result(self, use, parent, content, structured=None, error=False):
        event = {"type": "user", "parent_tool_use_id": parent,
                 "message": {"content": [{"type": "tool_result", "tool_use_id": use, "content": content,
                                          "is_error": error}]}}
        if structured is not None:
            event["tool_use_result"] = structured
        self.events.append(event)

    def dispatch(self, job_id, failed=False):
        use = self._id("agent")
        self.assistant([{"type": "tool_use", "id": use, "name": "Agent",
                         "input": {"name": job_id, "prompt": f"Write .team-review/jobs/{job_id}.json"}}])
        self.result(use, None, "failed" if failed else "delivered", error=failed)
        return use

    def read(self, agent, path, start, count, error=False):
        use = self._id("read")
        file_path = str(self.root / path)
        self.assistant([{"type": "tool_use", "id": use, "name": "Read", "input": {"file_path": file_path}}], agent)
        self.result(use, agent, "...", {"type": "text", "file": {"filePath": file_path, "startLine": start,
                                                                "numLines": count, "totalLines": 10}}, error)


def cell(path, job_id="job-01", **extra):
    return {"path": path, "reviewer": "senior-review:security-auditor", "status": "covered", "job_id": job_id,
            "sha256": "0" * 64, "note": "", **extra}


class CheckRunTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="check-run-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        for name in ("a.py", "b.py"):
            (self.root / name).write_text(TEN_LINES, encoding="utf-8", newline="\n")
        self.run_ = Transcript(self.root)

    def analyze(self, cells):
        return check_run.analyze(self.run_.events, cells, self.root.as_posix())

    def test_full_read_verifies_the_cell(self):
        agent = self.run_.dispatch("job-01")
        self.run_.read(agent, "a.py", 1, 10)
        report = self.analyze([cell("a.py")])
        self.assertEqual((report["cells"]["verified"], report["violations"], report["unverified"]), (1, [], []))

    def test_ranges_merge_and_a_gap_fails(self):
        agent = self.run_.dispatch("job-01")
        self.run_.read(agent, "a.py", 1, 4)
        self.run_.read(agent, "a.py", 5, 6)
        self.run_.read(agent, "b.py", 1, 4)
        self.run_.read(agent, "b.py", 6, 5)
        report = self.analyze([cell("a.py"), cell("b.py")])
        self.assertEqual(report["cells"]["verified"], 1)
        self.assertEqual([(item["path"], item["problem"][:16]) for item in report["violations"]],
                         [("b.py", "not read in full")])

    def test_short_or_failed_read_is_not_full(self):
        agent = self.run_.dispatch("job-01")
        self.run_.read(agent, "a.py", 1, 6)
        self.run_.read(agent, "b.py", 1, 10, error=True)
        report = self.analyze([cell("a.py"), cell("b.py")])
        self.assertEqual(sorted(item["path"] for item in report["violations"]), ["a.py", "b.py"])

    def test_read_outside_the_job_does_not_count(self):
        self.run_.dispatch("job-01")
        other = self.run_.dispatch("job-02")
        self.run_.read(other, "a.py", 1, 10)
        report = self.analyze([cell("a.py"), cell("b.py", "job-02")])
        self.assertEqual([item["path"] for item in report["violations"]], ["a.py", "b.py"])

    def test_failed_job_is_a_violation(self):
        agent = self.run_.dispatch("job-01", failed=True)
        self.run_.read(agent, "a.py", 1, 10)
        report = self.analyze([cell("a.py")])
        self.assertIn("successful result", report["violations"][0]["problem"])

    def test_reused_cell_needs_provenance(self):
        report = self.analyze([cell("a.py", None, source_review_id="r1", source_report="reports/r1.md"),
                               cell("b.py", None)])
        self.assertEqual(report["cells"]["reused"], 1)
        self.assertEqual([(item["path"], item["problem"]) for item in report["violations"]],
                         [("b.py", "reused without provenance")])

    def test_codebase_map_read_blocks_count(self):
        agent = self.run_.dispatch("job-01")
        use = "map1"
        self.run_.assistant([{"type": "tool_use", "id": use, "name": MAP_READ,
                              "input": {"run_id": "r", "requests": [{"path": "a.py", "full_file": True}]}}], agent)
        packet = {"files": [{"path": "a.py", "blocks": [{"start": 1, "end": 10, "source": "..."}]}]}
        self.run_.result(use, agent, [{"type": "text", "text": json.dumps(packet)}])
        self.assertEqual(self.analyze([cell("a.py")])["cells"]["verified"], 1)

    def test_unknown_read_format_is_unverifiable(self):
        agent = self.run_.dispatch("job-01")
        self.run_.assistant([{"type": "tool_use", "id": "r9", "name": "Read",
                              "input": {"file_path": str(self.root / "a.py")}}], agent)
        self.run_.result("r9", agent, "content without line numbers")
        report = self.analyze([cell("a.py")])
        self.assertEqual((report["violations"], len(report["unverified"])), ([], 1))

    def test_unverifiable_read_marks_only_its_own_file(self):
        agent = self.run_.dispatch("job-01")
        self.run_.assistant([{"type": "tool_use", "id": "r9", "name": "Read",
                              "input": {"file_path": str(self.root / "a.py")}}], agent)
        self.run_.result("r9", agent, "content without line numbers")
        report = self.analyze([cell("a.py"), cell("b.py")])
        self.assertEqual([item["path"] for item in report["unverified"]], ["a.py"])
        self.assertEqual([item["path"] for item in report["violations"]], ["b.py"])

    def test_lines_count_newlines_only(self):
        (self.root / "a.py").write_text(TEN_LINES.replace("line 3", "line\x0c3"), encoding="utf-8", newline="\n")
        agent = self.run_.dispatch("job-01")
        self.run_.read(agent, "a.py", 1, 10)
        self.assertEqual(self.analyze([cell("a.py")])["cells"]["verified"], 1)

    def test_tokens_count_each_message_once(self):
        agent = self.run_.dispatch("job-01")
        usage = {"input_tokens": 100, "output_tokens": 7, "cache_read_input_tokens": 50}
        for _ in range(2):  # one message streamed as two events
            self.run_.assistant([{"type": "text", "text": "thinking"}], agent, message_id="m-same", usage=usage)
        self.run_.events.append({"type": "result", "duration_ms": 1234, "total_cost_usd": 0.5,
                                 "usage": {"input_tokens": 999999}})
        report = self.analyze([cell("a.py", status="open")])
        self.assertEqual(report["tokens"]["by_job"]["job-01"]["input_tokens"], 100)
        self.assertEqual(report["tokens"]["total"]["input_tokens"], 110)
        self.assertEqual(report["run"]["duration_ms"], 1234)

    def test_cli_exit_status(self):
        agent = self.run_.dispatch("job-01")
        self.run_.read(agent, "a.py", 1, 10)
        run = self.root / "run.jsonl"
        run.write_text("\n".join(json.dumps(event) for event in self.run_.events) + "\n", encoding="utf-8")
        team = self.root / ".team-review"
        team.mkdir()
        for cells, expected in (([cell("a.py")], 0), ([cell("a.py"), cell("b.py")], 1)):
            (team / "coverage.json").write_text(json.dumps({"cells": cells}), encoding="utf-8")
            with redirect_stdout(StringIO()):
                self.assertEqual(check_run.main([str(run), str(team / "coverage.json")]), expected)


if __name__ == "__main__":
    unittest.main()
