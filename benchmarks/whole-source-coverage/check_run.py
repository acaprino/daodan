"""Check a group review run from its stream-json transcript and its coverage register.

Every cell the run newly covered must have been read in full by the job holding it:
successful Read or codebase_map_read results whose line ranges, merged, span every
line of the file. A call without a result, a search, an error or a short result does
not count, and the job's own dispatch must exist and must not have failed; the job's
delivered and complete outcome comes from the register, which account derives from the
job's result. Events belong to
a job through its Agent dispatch (the job ID as dispatch name or in the prompt) and
the parent_tool_use_id of the worker's events. A reused cell (no job) needs its
provenance and no new read. Tokens count once per assistant message; the final
result event's aggregate is reported apart, never added.

Usage: python check_run.py RUN.jsonl COVERAGE.json [--root DIR]
Exit 0 when every newly covered cell is verified, 1 otherwise, 2 on unreadable input.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "plugins/senior-review/skills/review-preparation/scripts"))
from composition import relative  # noqa: E402

TOKENS = ("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")
JOB_ID = re.compile(r"\bjob-\d{2,}\b")
NUMBERED = re.compile(r"^\s*(\d+)\t", re.MULTILINE)


def text_of(content) -> str:
    """A tool result's text, given as a string or as a list of text blocks."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(block.get("text", "") for block in content if isinstance(block, dict))
    return ""


def read_ranges(name: str, tool_input: dict, content, structured, root: str) -> list[tuple[str, int, int]] | None:
    """(path, first line, last line) of a successful read; [] for other tools; None for an unknown read format."""
    if name == "Read":
        file = structured.get("file") if isinstance(structured, dict) else None
        path = relative(str((file or {}).get("filePath") or tool_input.get("file_path", "")), root)
        if isinstance(file, dict) and isinstance(file.get("startLine"), int) and isinstance(file.get("numLines"), int):
            return [(path, file["startLine"], file["startLine"] + file["numLines"] - 1)]
        numbers = [int(number) for number in NUMBERED.findall(text_of(content))]
        return [(path, min(numbers), max(numbers))] if numbers else None
    if name.endswith("codebase_map_read"):
        packet = structured if isinstance(structured, dict) and "files" in structured else None
        if packet is None:
            try:
                packet = json.loads(text_of(content))
            except ValueError:
                return None
        if not isinstance(packet, dict) or not isinstance(packet.get("files"), list):
            return None
        return [(relative(entry["path"], root), block["start"], block["end"])
                for entry in packet["files"] for block in entry.get("blocks", [])]
    return []


def spans_all(ranges: list[tuple[int, int]], lines: int) -> bool:
    """Whether at least one read happened and the merged ranges cover lines 1..lines."""
    reached = 0
    for start, end in sorted(ranges):
        if start > reached + 1:
            return False
        reached = max(reached, end)
    return bool(ranges) and reached >= lines


def analyze(events: list[dict], cells: list[dict], root: str) -> dict:
    uses, results, messages, final = {}, {}, {}, None
    for event in events:
        kind, parent = event.get("type"), event.get("parent_tool_use_id")
        message = event.get("message") if isinstance(event.get("message"), dict) else {}
        blocks = message.get("content") if isinstance(message.get("content"), list) else []
        if kind == "assistant":
            if message.get("id"):
                messages[message["id"]] = (message.get("usage") or {}, parent)
            for block in blocks:
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    uses[block.get("id")] = (block.get("name", ""), block.get("input") or {}, parent)
        elif kind == "user":
            for block in blocks:
                if isinstance(block, dict) and block.get("type") == "tool_result":
                    results[block.get("tool_use_id")] = (block.get("content"), event.get("tool_use_result"),
                                                         bool(block.get("is_error")))
        elif kind == "result":
            final = event

    job_ids = {item["job_id"] for item in cells if item.get("job_id")}
    agents = {}
    for use, (name, tool_input, _) in uses.items():
        if name in ("Agent", "Task"):
            named = tool_input.get("name")
            found = [named] if named in job_ids else [job for job in JOB_ID.findall(str(tool_input.get("prompt", "")))
                                                       if job in job_ids]
            if found:
                agents[use] = found[0]

    reads, unverifiable = defaultdict(list), []
    for use, (name, tool_input, parent) in uses.items():
        job = agents.get(parent)
        if job is None or use not in results or results[use][2]:
            continue
        ranges = read_ranges(name, tool_input, results[use][0], results[use][1], root)
        if ranges is None:
            targets = [tool_input.get("file_path", "")] + [request.get("path", "") for request in
                                                           tool_input.get("requests", []) if isinstance(request, dict)]
            unverifiable.append({"job_id": job, "tool": name, "input": tool_input,
                                 "paths": [relative(str(target), root) for target in targets if target]})
            continue
        for path, start, end in ranges:
            reads[(job, path)].append((start, end))

    counts = {"covered": 0, "verified": 0, "reused": 0}
    violations, unverified = [], []
    for item in cells:
        if item.get("status") != "covered":
            continue
        counts["covered"] += 1
        where = {"path": item["path"], "reviewer": item.get("reviewer"), "job_id": item.get("job_id")}
        if item.get("job_id") is None:
            if item.get("source_review_id") and item.get("source_report"):
                counts["reused"] += 1
            else:
                violations.append({**where, "problem": "reused without provenance"})
            continue
        dispatches = [use for use, job in agents.items() if job == item["job_id"]]
        if not any(use in results and not results[use][2] for use in dispatches):
            violations.append({**where, "problem": "job without a successful result in the transcript"})
            continue
        try:
            text = (Path(root) / item["path"]).read_bytes().decode("utf-8", errors="replace")
            # Count newline-separated lines only, as Read numbers them; splitlines also splits on \x0c and others.
            lines = text.count("\n") + (0 if text.endswith("\n") or not text else 1)
        except OSError:
            unverified.append({**where, "problem": "file not on disk"})
            continue
        ranges = reads[(item["job_id"], item["path"])]
        if spans_all(ranges, lines):
            counts["verified"] += 1
        elif any(read["job_id"] == item["job_id"] and item["path"] in read["paths"] for read in unverifiable):
            unverified.append({**where, "problem": "read in a format this checker cannot verify"})
        else:
            violations.append({**where, "problem": f"not read in full: {sorted(ranges)} of {lines} lines"})

    def total(rows):
        return {key: sum(int(usage.get(key) or 0) for usage in rows) for key in TOKENS}

    by_job = defaultdict(list)
    for usage, parent in messages.values():
        by_job[agents.get(parent) or ("coordinator" if parent is None else "other-workers")].append(usage)
    tokens = {"total": total([usage for usage, _ in messages.values()]),
              "by_job": {job: total(rows) for job, rows in sorted(by_job.items())}}
    new_cells = counts["covered"] - counts["reused"]
    review = sum(sum(row.values()) for job, row in tokens["by_job"].items() if job in job_ids)
    tokens["review_per_new_cell"] = round(review / new_cells) if new_cells else None
    run = ({key: final.get(key) for key in ("duration_ms", "duration_api_ms", "total_cost_usd", "num_turns",
                                             "usage", "is_error")} if final else None)
    return {"cells": counts, "violations": violations, "unverified": unverified,
            "unverifiable_reads": unverifiable, "tokens": tokens, "run": run}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("run")
    parser.add_argument("coverage")
    parser.add_argument("--root", help="the review's project root; default: the directory holding .team-review/")
    args = parser.parse_args(argv)
    coverage = Path(args.coverage)
    root = Path(args.root) if args.root else coverage.resolve().parent.parent
    try:
        lines = Path(args.run).read_text(encoding="utf-8").splitlines()
        cells = json.loads(coverage.read_text(encoding="utf-8"))["cells"]
    except (OSError, ValueError, KeyError) as error:
        print(json.dumps({"error": str(error)}), file=sys.stderr)
        return 2
    events, unparsed = [], 0
    for line in filter(str.strip, lines):
        try:
            events.append(json.loads(line))
        except ValueError:
            unparsed += 1
    report = {**analyze(events, cells, root.as_posix()), "unparsed_lines": unparsed}
    print(json.dumps(report, indent=2))
    return 0 if not report["violations"] and not report["unverified"] else 1


if __name__ == "__main__":
    sys.exit(main())
