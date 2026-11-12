"""The phase-3 runs downloaded from the volume: cost, time, jobs, and every passage citing a known defect's lines.

Whether a passage states the defect is judged by reading it (criterion in the benchmark README):
this script only finds the passages, in the final report and in the jobs.

    modal volume get daodan-flow-results <tag> <dir>
    python benchmarks/phazly-flow/phase3/collect.py <dir>/<tag>
"""
from __future__ import annotations

import json
import re
import sys
import tarfile
from pathlib import Path

DEFECTS = {"G1": ("useDayProgress.ts", 190), "G2": ("QuickAddSheet.tsx", 268)}
WINDOW = 15


def citing(text: str, name: str, line: int) -> list[str]:
    """Paragraphs of `text` that cite `name:N` (or a range) within WINDOW lines of `line`."""
    out = []
    for paragraph in re.split(r"\n\s*\n", text):
        for found in re.finditer(re.escape(name) + r"[`'\"]?\s*[:#L]+\s*(\d+)(?:\s*[-–]\s*(\d+))?", paragraph):
            first, last = int(found.group(1)), int(found.group(2) or found.group(1))
            if first - WINDOW <= line <= last + WINDOW:
                out.append(paragraph.strip()[:1200])
                break
    return out


def final_message(stream: Path) -> str:
    result = ""
    for row in stream.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            event = json.loads(row)
        except ValueError:
            continue
        if event.get("type") == "result":
            result = event.get("result") or ""
    return result


_HEREDOC = re.compile(r"cat\s*>\s*['\"]?([^\s<'\"]+)['\"]?\s*<<\s*-?['\"]?(\w+)['\"]?\n(.*?)\n\2(?:\n|$)", re.S)


def stream_texts(stream: Path) -> dict[str, str]:
    """The files a session wrote (Write, or a shell heredoc), the agents' messages, commands and tool results.

    The review keeps its directory inside the container; when the directory is lost, the
    session's event stream still holds what every agent wrote and read.
    """
    files: dict[str, str] = {}
    other = {"coordinator messages": [], "subagent messages": [], "commands and results": []}
    for row in stream.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            event = json.loads(row)
        except ValueError:
            continue
        content = (event.get("message") or {}).get("content")
        if not isinstance(content, list):
            continue
        sub = bool(event.get("parent_tool_use_id"))
        for block in content:
            kind = block.get("type")
            if kind == "text":
                other["subagent messages" if sub else "coordinator messages"].append(block.get("text") or "")
            elif kind == "tool_use":
                given = block.get("input") or {}
                if block.get("name") == "Write":
                    files[str(given.get("file_path"))] = given.get("content") or ""
                elif block.get("name") == "Bash":
                    command = given.get("command") or ""
                    for found in _HEREDOC.finditer(command):
                        files[found.group(1)] = found.group(3)
                    other["commands and results"].append(command)
            elif kind == "tool_result":
                result = block.get("content")
                other["commands and results"].append(result if isinstance(result, str) else json.dumps(result, ensure_ascii=False))
    texts = {f"file {path}": text for path, text in files.items()}
    texts.update({name: "\n\n".join(parts) for name, parts in other.items()})
    return texts


def collect(run: Path) -> dict:
    summary = json.loads((run / "summary.json").read_text(encoding="utf-8")) if (run / "summary.json").is_file() else {}
    texts = {"final message": final_message(run / "stream.jsonl") if (run / "stream.jsonl").is_file() else ""}
    if (run / "stream.jsonl").is_file():
        texts.update(stream_texts(run / "stream.jsonl"))
    for saved in (run / "team-review").rglob("*") if (run / "team-review").is_dir() else []:
        if saved.is_file() and saved.suffix in (".md", ".json"):
            texts[f"saved {saved.relative_to(run).as_posix()}"] = saved.read_text(encoding="utf-8", errors="replace")
    jobs = 0
    archive = run / "review.tar.gz"
    if archive.is_file():
        with tarfile.open(archive) as tar:
            for member in tar.getmembers():
                if not member.isfile() or not member.name.endswith((".md", ".json")):
                    continue
                name = member.name.lstrip("./")
                if "/jobs/" in f"/{name}" and name.endswith((".md", ".json")) and "/verification/" not in f"/{name}":
                    jobs += 1
                texts[name] = tar.extractfile(member).read().decode("utf-8", errors="replace")
    report = {"run": run.name, "cost_usd": summary.get("cost_usd"), "seconds": summary.get("seconds"),
              "turns": summary.get("turns"), "timed_out": summary.get("timed_out"), "jobs": jobs, "defects": {}}
    for defect, (name, line) in DEFECTS.items():
        found = {}
        for source, text in texts.items():
            passages = citing(text, name, line)
            if passages:
                found[source] = passages
        report["defects"][defect] = found
    return report


def main(argv: list[str]) -> int:
    root = Path(argv[0])
    for run in sorted(path for path in root.iterdir() if path.is_dir()):
        report = collect(run)
        print(f"== {report['run']}: {report['cost_usd']} USD, {report['seconds']} s, {report['turns']} turns, "
              f"{report['jobs']} job files, timed out {report['timed_out']}")
        for defect, found in report["defects"].items():
            where = sorted(found)
            final = [source for source in where if source == "final message"
                     or source.endswith(("99-consolidated.md", "report.md"))]
            print(f"   {defect}: final {final or '-'}; elsewhere {len(where) - len(final)} files")
        (run / "collect.json").write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
