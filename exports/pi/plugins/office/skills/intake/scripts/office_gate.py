"""Office delivery gate: the evidence that lets a coordinator call a PPTX or DOCX finished.

`start` runs before any write. It records the source's identity and keeps a byte
copy beside the record, so an overwritten source can always be restored.
`check` proves one candidate: a separate file, the source unchanged, opened by the
pinned engine, rendered page by page into a folder the gate owns, source text
carried over except approved cuts, and an independent review bound to this
candidate's SHA-256 that names every rendered page. It prints one verdict and the
single next step. Only `deliverable` (exit 0) allows a finished claim.
The gate checks evidence; it does not build, repair or judge the design.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import engine_install  # noqa: E402

SCHEMA = "daodan/office-gate/v1"
SKILLS = Path(__file__).resolve().parents[2]
FORMATS = {
    "pptx": {"engine": "deckcraft", "count": "slides", "unit": "slide",
             "inspector": SKILLS / "deckcraft/scripts/pptx_inspect.py",
             "reviewer": "office:presentation-reviewer"},
    "docx": {"engine": "wordcraft", "count": "pages", "unit": "page",
             "inspector": SKILLS / "docx/scripts/docx_inspect.py",
             "reviewer": "office:document-reviewer"},
}
VERDICTS = ("deliverable", "review-needed", "needs-fix", "blocked")
REVIEW_VERDICT = re.compile(r"verdict\W{0,12}(pass|needs-fix|blocked)\b", re.IGNORECASE)
MAX_REVIEW_BYTES = 2 << 20
ENGINE_TIMEOUT = 900
SHOWN = 10


class GateError(ValueError):
    """The request cannot be evaluated at all."""


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def format_of(path):
    kind = Path(path).suffix.lower().lstrip(".")
    if kind not in FORMATS:
        raise GateError(f"{Path(path).name}: only .pptx and .docx files pass through this gate.")
    return kind


def start(source=None, directory=None, kind=None, now=None):
    """Create a record. With a source, keep its identity and a byte copy; never touch the source."""
    if source is not None:
        source = Path(source).resolve()
        if not source.is_file():
            raise GateError(f"The source {source} does not exist.")
        kind = format_of(source)
        directory = Path(directory).resolve() if directory else source.parent
        stem = source.stem
    else:
        if kind not in FORMATS or directory is None:
            raise GateError("A new file needs --dir and --format pptx|docx.")
        directory = Path(directory).resolve()
        stem = "new-" + kind
    stamp = (now or datetime.now(timezone.utc)).strftime("%Y%m%dT%H%M%SZ")
    base = directory / ".daodan" / "office"
    record_dir, suffix = base / f"{stem}-{stamp}", 1
    while record_dir.exists():
        suffix += 1
        record_dir = base / f"{stem}-{stamp}-{suffix}"
    record_dir.mkdir(parents=True)
    record = {"schema": SCHEMA, "format": kind, "created": stamp, "source": None}
    if source is not None:
        copy = record_dir / ("source." + kind)
        shutil.copy2(source, copy)
        digest = sha256(source)
        if sha256(copy) != digest:
            raise GateError("The source changed while it was being copied; start again.")
        record["source"] = {"path": str(source), "sha256": digest, "size": source.stat().st_size,
                            "copy": copy.name}
    (record_dir / "gate.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    return record_dir


def load_record(path):
    path = Path(path).resolve()
    record_file = path / "gate.json" if path.is_dir() else path
    try:
        record = json.loads(record_file.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise GateError(f"No gate record at {path}: run `start` before building ({exc}).") from exc
    if record.get("schema") != SCHEMA or record.get("format") not in FORMATS:
        raise GateError(f"{record_file} is not an Office gate record.")
    return record_file.parent, record


def engine_count(binary, kind, candidate, run):
    result = run([str(binary), "info", str(candidate)], capture_output=True, text=True, encoding="utf-8",
                 errors="replace", timeout=ENGINE_TIMEOUT)
    if result.returncode:
        raise GateError((result.stderr or result.stdout).strip()[:400] or f"exit code {result.returncode}")
    try:
        count = json.loads(result.stdout)[FORMATS[kind]["count"]]
    except (ValueError, KeyError, TypeError) as exc:
        raise GateError(f"unexpected info output: {exc}") from exc
    if isinstance(count, list):  # DeckCraft lists one object per slide; WordCraft counts pages.
        count = len(count)
    if isinstance(count, bool) or not isinstance(count, int) or count < 1:
        raise GateError(f"the engine reports {str(count)[:80]} {FORMATS[kind]['count']}")
    return count


def render(binary, kind, candidate, count, folder, run):
    """Render every page into a folder named by the candidate digest; reuse a complete earlier render."""
    unit = FORMATS[kind]["unit"]
    names = [f"{unit}-{number:02d}.png" for number in range(1, count + 1)]
    if folder.is_dir() and sorted(p.name for p in folder.iterdir()) == names and all(
            (folder / name).stat().st_size for name in names):
        return names
    partial = folder.with_name(folder.name + ".partial")
    shutil.rmtree(partial, ignore_errors=True)
    partial.mkdir(parents=True)
    if kind == "pptx":
        commands = [[str(binary), "render", str(candidate), "--all", str(partial)]]
    else:
        commands = [[str(binary), "render", str(candidate), str(partial / name), "--page", str(number)]
                    for number, name in enumerate(names, 1)]
    for command in commands:
        result = run(command, capture_output=True, text=True, encoding="utf-8", errors="replace",
                     timeout=ENGINE_TIMEOUT)
        if result.returncode:
            raise GateError((result.stderr or result.stdout).strip()[:400] or f"exit code {result.returncode}")
    produced = sorted(p.name for p in partial.iterdir())
    if produced != names or not all((partial / name).stat().st_size for name in names):
        raise GateError(f"expected {count} images {names[0]} to {names[-1]}, the engine wrote {len(produced)}")
    shutil.rmtree(folder, ignore_errors=True)
    partial.rename(folder)
    return names


def inspector(kind, *arguments):
    result = subprocess.run([sys.executable, "-I", "-X", "utf8", "-B", str(FORMATS[kind]["inspector"]), *map(str, arguments)],
                            capture_output=True, text=True, encoding="utf-8", errors="replace",
                            timeout=ENGINE_TIMEOUT)
    try:
        return json.loads(result.stdout)
    except ValueError as exc:
        raise GateError((result.stderr or result.stdout).strip()[:400] or str(exc)) from exc


def read_review(path, digest, names):
    """Return (verdict or None, problems) for a review report bound to this candidate."""
    try:
        with open(path, "rb") as stream:
            text = stream.read(MAX_REVIEW_BYTES + 1).decode("utf-8", "replace")
    except OSError as exc:
        return None, [f"the review report cannot be read: {exc}"]
    if len(text) > MAX_REVIEW_BYTES:
        return None, ["the review report exceeds 2 MB"]
    problems = []
    if digest not in text.lower():
        problems.append("the review does not state this candidate's SHA-256, so it reviewed another file")
    unnamed = [name for name in names if name not in text]
    if unnamed:
        problems.append(f"the review does not name {len(unnamed)} rendered pages: " + ", ".join(unnamed[:SHOWN]))
    found = REVIEW_VERDICT.findall(text)
    if not found:
        problems.append("the review states no verdict (pass, needs-fix or blocked)")
    return (found[-1].lower() if found else None), problems


def check(record_path, candidate, review=None, cuts=None, run=subprocess.run, locate=engine_install.find):
    """Evaluate one candidate. Returns the result dictionary; never raises for a failed check."""
    result = {"schema": SCHEMA + "/check", "verdict": "blocked", "problems": [], "next": "", "candidate": None}
    problems = result["problems"]

    def finish(verdict, step):
        result["verdict"], result["next"] = verdict, step
        return result

    try:
        record_dir, record = load_record(record_path)
    except GateError as exc:
        problems.append(str(exc))
        return finish("blocked", "Run `start` on the source (or `start --dir --format` for a new file), "
                                 "then build the candidate.")
    kind, source = record["format"], record["source"]
    spec = FORMATS[kind]
    result["record"] = str(record_dir)
    candidate = Path(candidate).resolve()
    result["candidate"] = str(candidate)
    if not candidate.is_file() or candidate.suffix.lower() != "." + kind:
        problems.append(f"no .{kind} candidate at {candidate}")
        return finish("blocked", f"Build the candidate with {spec['engine']} and pass its path.")
    if source:
        copy = record_dir / source["copy"]
        if candidate == Path(source["path"]) or candidate == copy:
            problems.append("the candidate is the source itself: the original was overwritten")
            return finish("blocked", f"Restore the original from {copy}, then save the candidate under a new name.")
        if not Path(source["path"]).is_file() or sha256(source["path"]) != source["sha256"]:
            problems.append(f"the source {source['path']} was changed or removed after `start`")
            return finish("blocked", f"Tell the user, restore the original from {copy}, and never write to the source.")
    digest = sha256(candidate)
    result["sha256"] = digest
    binary = locate(spec["engine"])
    if binary is None:
        problems.append(f"{spec['engine']} is not installed, so the candidate cannot be opened or rendered")
        return finish("blocked", f"Install it with engine_install.py plan/install {spec['engine']}; "
                                 "without the engine nothing is built or delivered.")
    try:
        count = engine_count(binary, kind, candidate, run)
    except GateError as exc:
        problems.append(f"{spec['engine']} cannot open the candidate: {exc}")
        return finish("needs-fix", "Rebuild the candidate with the engine.")
    folder = record_dir / f"renders-{digest[:12]}"
    try:
        names = render(binary, kind, candidate, count, folder, run)
    except GateError as exc:
        problems.append(f"rendering failed: {exc}")
        return finish("blocked", "Report the render failure; an unrendered candidate cannot be reviewed.")
    result["renders"] = {"folder": str(folder), "pages": count}
    verdict, step = "review-needed", ""
    structure = inspector(kind, "inspect", candidate)
    if not structure.get("valid", False):
        problems.append("package errors: " + "; ".join(map(str, structure.get("errors", [])[:SHOWN])))
        verdict, step = "needs-fix", "Rebuild the candidate with the engine; do not edit package XML."
    if source:
        extra = ["--cuts", cuts] if cuts else []
        coverage = inspector(kind, "coverage", record_dir / source["copy"], candidate, *extra)
        result["coverage"] = coverage.get("summary")
        if not coverage.get("valid", False):
            problems.append("coverage cannot run: " + "; ".join(map(str, coverage.get("errors", [])[:SHOWN])))
            verdict, step = "blocked", "Fix the cuts file and check again."
        elif not coverage.get("complete", False):
            missing = [item for item in coverage.get("items", []) if item.get("status") == "missing"]
            listed = "; ".join((f"{spec['unit']} {item[spec['unit']]}: " if spec["unit"] in item else "")
                               + repr(item.get("text", ""))[:80] for item in missing[:SHOWN])
            problems.append(f"{len(missing)} source texts are missing from the candidate: {listed}")
            if verdict != "blocked":
                verdict, step = "needs-fix", ("Restore each missing text, or ask the user to approve it as a cut "
                                              "and pass the approved cuts with --cuts.")
    if verdict in ("blocked", "needs-fix"):
        return finish(verdict, step)
    request = (f"Dispatch {spec['reviewer']} in final mode on {candidate} (SHA-256 {digest}) with the renders in "
               f"{folder}. Its report must state that SHA-256, name every render file and end with its verdict; "
               "then run check again with --review REPORT.")
    if not review:
        problems.append("no independent review of this candidate")
        return finish("review-needed", request)
    review_verdict, review_problems = read_review(review, digest, names)
    result["review"] = {"path": str(Path(review).resolve()), "verdict": review_verdict}
    if review_problems:
        problems.extend(review_problems)
        return finish("review-needed", request)
    if review_verdict == "needs-fix":
        problems.append("the reviewer found blocking defects")
        return finish("needs-fix", "Fix every blocking defect at its source, build a new candidate and check it.")
    if review_verdict == "blocked":
        problems.append("the reviewer could not judge the candidate")
        return finish("blocked", "Resolve what the review names as missing, then review again.")
    return finish("deliverable", "Deliver the candidate with the render folder and the review.")


def report(result):
    lines = [f"verdict: {result['verdict']}"]
    if result.get("candidate"):
        lines.append(f"candidate: {result['candidate']}")
    if result.get("sha256"):
        lines.append(f"sha256: {result['sha256']}")
    if result.get("renders"):
        lines.append(f"renders: {result['renders']['folder']} ({result['renders']['pages']} pages)")
    lines += [f"{number}. {problem}" for number, problem in enumerate(result["problems"], 1)]
    lines.append(f"next: {result['next']}")
    if result["verdict"] != "deliverable":
        lines.append("Report this verdict as it is: the file is not finished.")
    return "\n".join(lines)


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    begin = commands.add_parser("start", help="Protect the source and open a record, before any write.")
    begin.add_argument("source", nargs="?", type=Path, help="The existing PPTX or DOCX the work starts from.")
    begin.add_argument("--dir", type=Path, help="Project folder for a new file (default: the source's folder).")
    begin.add_argument("--format", choices=sorted(FORMATS), help="Format of a new file without a source.")
    verify = commands.add_parser("check", help="Render, compare and verify one candidate; print the verdict.")
    verify.add_argument("record", type=Path, help="The folder `start` printed.")
    verify.add_argument("candidate", type=Path)
    verify.add_argument("--review", type=Path, help="The independent reviewer's report for this candidate.")
    verify.add_argument("--cuts", type=Path, help="Cuts the user approved, in the inspector's cuts format.")
    args = parser.parse_args(argv)
    try:
        if args.command == "start":
            folder = start(args.source, args.dir, args.format)
            print(f"record: {folder}")
            print("Build every candidate under a new name; never write to the source. "
                  f"The original is kept in {folder}. Before any delivery run: check {folder} CANDIDATE")
            return 0
        result = check(args.record, args.candidate, args.review, args.cuts)
    except GateError as exc:
        print(f"office-gate: {exc}", file=sys.stderr)
        return 2
    if result.get("sha256") and result.get("record"):
        target = Path(result["record"]) / f"check-{result['sha256'][:12]}.json"
        target.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(report(result))
    return 0 if result["verdict"] == "deliverable" else 1


if __name__ == "__main__":
    sys.exit(main())
