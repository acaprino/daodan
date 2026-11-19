"""Incremental change sets over a parent run's phase files: the claims a change
touches, line citations moved onto their new lines, the carried phase files with
stale markers, the publication check of an incremental run, and changes.md."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

from import_resolution import _STYLESHEET_SUFFIXES, _by_basename
from languages import SUPPORTED_EXTENSIONS
from run_store import own_store, _read_json, _reject_links_below, RunControlError, store_of
from snapshot_store import artifact_digest, resolve_run_snapshot
from source_files import read_text


def _cell(text: str) -> str:
    """A markdown table cell: a pipe splits a row even inside a code span, so it is escaped."""
    return str(text).replace("|", "\\|")


PHASE_FILES = (
    "01-structure.md", "02-interfaces.md", "03-flows.md", "04-semantics.md",
    "05-risks.md", "06-documentation.md", "07-final-report.md",
    "08-interconnect-map.md",
)

# `src/app/service.py::Class.method`
CITE_SYMBOL = re.compile(r"([\w./\\-]+\.[A-Za-z0-9_]+)::([A-Za-z_][\w.]*)")
# Files whose symbols include stylesheet rules: their selectors are cited whole.
_RULE_SUFFIXES = _STYLESHEET_SUFFIXES + (".vue", ".svelte", ".astro") + tuple(
    suffix for suffix, language in SUPPORTED_EXTENSIONS.items() if language == "markup")
# `theme.css::.dark #root > div:first-child`: a stylesheet symbol carries spaces
# and punctuation the bare form cannot, so it is cited inside backticks and
# matched whole.
CITE_SYMBOL_QUOTED = re.compile(r"`([\w./\\-]+\.[A-Za-z0-9_]+)::([^`\n]+)`")
# `src/app/service.py:42`
CITE_LINE = re.compile(r"([\w./\\-]+\.[A-Za-z0-9_]+):(\d+)\b")
# A bare path inside backticks or a table cell.
CITE_PATH = re.compile(r"[`|\s(\[]([\w./\\-]+\.[A-Za-z0-9_]+)[`|\s),\]]")


def cited_symbols(line: str) -> list[tuple[str, str]]:
    """Every `path::symbol` citation on a line, bare or quoted, without repeats."""
    quoted = CITE_SYMBOL_QUOTED.findall(line)
    # A quoted stylesheet selector is matched whole and never also by its leading
    # word: `theme.css::body > div` names `body > div`, not `body`. Its span is
    # blanked before the bare pattern runs.
    bare = CITE_SYMBOL_QUOTED.sub(
        lambda m: " " * len(m.group(0)) if m.group(1).lower().endswith(_RULE_SUFFIXES) else m.group(0),
        line,
    )
    return list(dict.fromkeys(CITE_SYMBOL.findall(bare) + quoted))


def _path_index(paths) -> dict[str, list[str]]:
    return _by_basename(paths)


def _match_cited_path(cited: str, index: dict[str, list[str]]) -> str | None:
    """A phase file cites a path as the model wrote it; match at a segment boundary."""
    normalized = cited.replace("\\", "/").lstrip("./")
    if not normalized:
        return None
    for candidate in index.get(normalized.rsplit("/", 1)[-1], []):
        if candidate == normalized or candidate.endswith("/" + normalized) or normalized.endswith("/" + candidate):
            return candidate
    return None


def _symbol_verdict(path: str, symbol: str, changed: set, removed: set, added_files: set,
                    removed_files: set) -> str | None:
    """
    A claim about a symbol is affected by what happened to THAT symbol, matched
    exactly. Never by what happened to its enclosing class: a class span
    encloses its methods, so editing any one method moves the class hash, and
    walking up to the class would mark every claim about every sibling method.
    A claim about the class as a whole cites the class, and is caught by the
    exact match on it.
    """
    if path in removed_files:
        return "file-removed"
    if path in added_files:
        return "file-added"
    if (path, symbol) in removed:
        return "symbol-removed"
    if (path, symbol) in changed:
        return "symbol-changed"
    return None


class _ChangeView:
    """What a change set touched, in the shape a claim is judged against."""

    def __init__(self, comparison: dict, symbols: dict, importers: list[dict]):
        self.modified = set(comparison["modified"])
        self.added_files = set(comparison["added"])
        self.removed_files = set(comparison["removed"])
        self.importer_files = {entry["file"] for entry in importers}
        self.changed = {(item["file"], item["symbol"]) for item in symbols["changed"]}
        self.removed = {(item["file"], item["symbol"]) for item in symbols["removed"]}
        self.spans = {
            rel: {entry["symbol"]: entry for entry in entries}
            for rel, entries in symbols["renumber"].items()
        }
        self.fresh = symbols.get("fresh", {})
        self.index = _path_index(
            set(comparison["unchanged"]) | self.modified | self.added_files | self.removed_files | self.importer_files
        )

    def symbol_citations(self, line: str, cites: list[str], reason: str | None) -> str | None:
        for path_text, symbol in cited_symbols(line):
            path = _match_cited_path(path_text, self.index)
            if not path:
                continue
            cites.append(f"{path}::{symbol}")
            verdict = _symbol_verdict(path, symbol, self.changed, self.removed, self.added_files, self.removed_files)
            reason = reason or verdict
            if verdict is None and path in self.modified and not self.fresh.get(path, {}).get("symbols"):
                # A file kept file-level (a minified stylesheet) has no symbol to
                # judge by, so a symbol citation into it is judged by the file.
                reason = reason or "file-modified"
            if verdict is None and path in self.importer_files:
                reason = reason or "importer"
        return reason

    def line_citations(self, line: str, cites: list[str], reason: str | None) -> str | None:
        for path_text, line_text in CITE_LINE.findall(line):
            path = _match_cited_path(path_text, self.index)
            if not path:
                continue
            cites.append(f"{path}:{line_text}")
            if path in self.removed_files:
                reason = reason or "file-removed"
            elif path in self.added_files:
                reason = reason or "file-added"
            elif path in self.modified:
                inside = any(
                    entry["start_old"] <= int(line_text) <= entry["end_old"]
                    for entry in self.spans.get(path, {}).values()
                )
                if not inside:
                    reason = reason or "line-outside-known-symbol"
            elif path in self.importer_files:
                reason = reason or "importer"
        return reason

    def path_citation(self, line: str, cites: list[str]) -> str | None:
        for path_text in CITE_PATH.findall(line):
            path = _match_cited_path(path_text, self.index)
            if not path:
                continue
            reason = None
            if path in self.removed_files:
                reason = "file-removed"
            elif path in self.added_files:
                reason = "file-added"
            elif path in self.modified:
                reason = "file-modified"
            elif path in self.importer_files:
                reason = "importer"
            if reason:
                cites.append(path)
                return reason
        return None

    def judge(self, line: str) -> tuple[list[str], str | None]:
        """The citations on a line and why the change touches them, or None."""
        cites: list[str] = []
        reason = self.symbol_citations(line, cites, None)
        reason = self.line_citations(line, cites, reason)
        # The bare-path fallback runs ONLY when the line carried no precise
        # citation. A line that named a symbol or a line number has already
        # been judged at that precision, and re-judging it by its file would
        # mark every claim about every unchanged symbol in a modified file:
        # the symbol-level granularity, thrown away at the last step.
        if reason is None and not cites:
            reason = self.path_citation(line, cites)
        return cites, reason


def scan_claims(parent_dir: Path, comparison: dict, symbols: dict, importers: list[dict]) -> list[dict]:
    """
    Every line in the parent's phase files that cites something the change set
    touched, with the reason it is affected. Excludes 07-final-report.md:
    Phase 7 is regenerated on every run, never carried, so a claim living only
    there is not a work item, and counting it would inflate claims_affected
    and the per-phase breakdown the checkpoint prints.
    """
    view = _ChangeView(comparison, symbols, importers)
    claims: list[dict] = []
    for name in PHASE_FILES:
        if name == "07-final-report.md":
            continue  # Phase 7 is regenerated, never carried; see docstring.
        phase_path = parent_dir / name
        if not phase_path.exists():
            continue
        section = ""
        for number, line in enumerate(read_text(phase_path).split("\n"), start=1):
            if line.startswith("#"):
                section = line.strip()
                continue
            cites, reason = view.judge(line)
            if reason:
                claims.append({
                    "phase_file": name,
                    "line": number,
                    "section": section,
                    "cites": sorted(set(cites)),
                    "reason": reason,
                })
    return claims


def recommend(ratio: float, threshold: float, affected: int, reasons: list[str]) -> str:
    if reasons:
        return "full"
    if affected == 0:
        return "none"
    if ratio > threshold:
        reasons.append(f"ratio {ratio:.2f} over threshold {threshold:.2f}")
        return "full"
    return "incremental"


def _changes_markdown(changes: dict) -> str:
    files = changes["files"]
    lines = ["# Codebase Map Change Set", ""]
    parent = changes.get("parent_run") or "none"
    git = changes.get("git") or {}
    head = f"Parent run: {parent}."
    if git.get("commit"):
        head += f" Worktree at {git['commit']}" + (
            f" (dirty unknown: {git['dirty_unknown']})." if git.get("dirty_unknown") else " (dirty)." if git.get("dirty")
            else ".")
    lines += [head, "", "## Code changes", ""]
    lines.append(
        f"{len(files['modified'])} modified, {len(files['added'])} added, "
        f"{len(files['removed'])} removed, of {changes['totals']['files_in_snapshot']} in the snapshot."
    )
    lines.append("")
    for label, key in (("Modified", "modified"), ("Added", "added"), ("Removed", "removed")):
        if files[key]:
            lines.append(f"**{label}:**")
            lines += [f"- `{path}`" for path in files[key]]
            lines.append("")
    if any(changes["symbols"].values()):
        lines += ["| Symbol | File | Kind | Change |", "|---|---|---|---|"]
        for state in ("changed", "added", "removed"):
            for item in changes["symbols"][state]:
                lines.append(f"| `{_cell(item['symbol'])}` | `{_cell(item['file'])}` | {item['kind']} | {state} |")
        lines.append("")
    lines += ["## Blast radius", ""]
    if changes["importers"]:
        lines += ["| Importer | Imports |", "|---|---|"]
        lines += [
            f"| `{_cell(entry['file'])}` | {', '.join('`' + _cell(i) + '`' for i in entry['imports'])} |"
            for entry in changes["importers"]
        ]
    else:
        lines.append("No file imports anything that changed.")
    if "transitive_importers" in changes:
        reachable = changes["transitive_importers"]
        cycles = changes.get("import_cycles", [])
        lines += ["", "## Transitive import diagnostics", "",
                  "Static reachability is separate from the one-hop blast radius and update recommendation.",
                  f"Reachable importing files: {len(reachable)}. Cycle components: {len(cycles)}.", ""]
        if reachable:
            lines += ["| File | Shortest hops | Via | Seed |", "|---|---:|---|---|"]
            lines += [f"| `{_cell(item['file'])}` | {item['depth']} | `{_cell(item['via'])}` | `{_cell(item['seed'])}` |"
                      for item in reachable[:50]]
            if len(reachable) > 50:
                lines += ["", f"Showing 50 of {len(reachable)} importers; changes.json contains every record."]
            lines.append("")
        for component in cycles[:20]:
            lines.append("- Cycle component: " + ", ".join(f"`{_cell(path)}`" for path in component))
        if len(cycles) > 20:
            lines.append(f"Showing 20 of {len(cycles)} components; changes.json contains every component.")
    lines += ["", "## Affected claims", ""]
    if changes["claims"]:
        lines += ["| Phase file | Line | Section | Cites | Reason |", "|---|---|---|---|---|"]
        lines += [
            f"| {c['phase_file']} | {c['line']} | {_cell(c['section'])} | "
            f"{', '.join('`' + _cell(x) + '`' for x in c['cites'])} | {c['reason']} |"
            for c in changes["claims"]
        ]
    else:
        lines.append("No claim in the parent run cites anything that changed.")
    lines.append("")
    return "\n".join(lines)


MARKER_PREFIX = "<!-- xray:stale"


def renumber_line(text: str, renumber: dict, index: dict) -> str:
    """
    Move every `path:line` citation of a modified file onto its new line, when
    the old line falls inside a symbol that survived the edit. A citation
    outside every surviving span is left alone: the diff already marked its
    claim affected, so the model rewrites it rather than trusting the number.
    """
    def replace(match: "re.Match[str]") -> str:
        cited, number = match.group(1), int(match.group(2))
        path = _match_cited_path(cited, index)
        entries = renumber.get(path or "", [])
        for entry in entries:
            if entry["start_old"] <= number <= entry["end_old"]:
                return f"{cited}:{entry['start_new'] + (number - entry['start_old'])}"
        return match.group(0)

    return CITE_LINE.sub(replace, text)


def _carry_phase(source: Path, target: Path, marks: dict[int, dict], renumber: dict, index: dict) -> int:
    """Copy one phase file, a stale marker above each affected claim, every other line renumbered."""
    out_lines: list[str] = []
    marked = 0
    # A carried claim must survive byte for byte, so the source is read
    # raw here rather than through read_text: that helper deliberately
    # normalizes CRLF and CR to LF for the hashing and diff paths it was
    # written for, which would silently rewrite a CRLF parent phase file
    # to LF. Splitting and joining on "\n" alone, with no newline style
    # detected or re-normalized, keeps each line's own trailing "\r" (if
    # it has one) attached to it, so mixed line endings survive too.
    raw = source.read_bytes().decode("utf-8", errors="replace")
    for number, line in enumerate(raw.split("\n"), start=1):
        claim = marks.get(number)
        if claim:
            cites = " ".join(claim["cites"])
            # The inserted marker takes the same line ending as the claim
            # line it sits above, so it does not break that file's style.
            ending = "\r" if line.endswith("\r") else ""
            out_lines.append(f"{MARKER_PREFIX} reason={claim['reason']} cites={cites} -->{ending}")
            out_lines.append(line)
            marked += 1
        else:
            out_lines.append(renumber_line(line, renumber, index))
    # newline="" so Python writes "\n" literally instead of translating
    # it to the platform's line separator, the other half of preserving
    # whatever ending style each line already carries.
    with target.open("w", encoding="utf-8", newline="") as handle:
        handle.write("\n".join(out_lines))
    return marked


def _carry_record(parent_dir: Path, carried: dict) -> dict:
    parent_state = _read_json(parent_dir / "state.json") or {}
    return {
        "schema": 1, "parent_run": parent_state.get("run_id") or parent_dir.name,
        "parent_path": parent_dir.resolve().as_posix(), "artifacts": carried,
        "parent_manifest_sha256": artifact_digest(resolve_run_snapshot(parent_dir, _read_json(parent_dir / "state.json") or {}))
        if any((parent_dir / f"snapshot/manifest.{format}").is_file() for format in ("sqlite", "json")) else None,
    }


def _append_added_symbols(run_dir: Path, added: list[dict]) -> None:
    with (run_dir / "changes.md").open("a", encoding="utf-8") as handle:
        handle.write("\n## Added symbols\n\n")
        handle.write("No claim cites these yet. Phases 01 and 02 always; 03 to 06 at full depth.\n\n")
        handle.write("| Symbol | File | Kind |\n|---|---|---|\n")
        for item in added:
            handle.write(f"| `{_cell(item['symbol'])}` | `{_cell(item['file'])}` | {item['kind']} |\n")


def cmd_carry(args: argparse.Namespace) -> int:
    parent_dir = Path(args.parent_run)
    run_dir = Path(args.run_dir)
    try:
        _reject_links_below(parent_dir)  # a parent run can come with the project
        store = store_of(parent_dir / "snapshot" / "manifest")
        if store is not None:
            own_store(store)
    except RunControlError as error:
        print(f"carry: {error}", file=sys.stderr)
        return 2
    changes = _read_json(run_dir / "changes.json")
    if changes is None:
        print("carry: no changes.json in the run directory; run `diff` first", file=sys.stderr)
        return 2

    knowledge = parent_dir / "knowledge"
    if knowledge.is_dir():
        shutil.copytree(knowledge, run_dir / "knowledge", dirs_exist_ok=True)

    renumber = changes.get("renumber", {})
    child_state = _read_json(run_dir / "state.json") or {}
    parent_phases = child_state.get("parent_phases")
    if parent_phases is not None and parent_phases != [1, 2, 3, 4]:
        print("carry: bound parent_phases must be [1, 2, 3, 4]", file=sys.stderr)
        return 2
    index = _path_index(
        set(renumber)
        | set(changes["files"]["modified"])
        | set(changes["files"]["added"])
        | set(changes["files"]["removed"])
    )
    by_file: dict[str, dict[int, dict]] = {}
    for claim in changes.get("claims", []):
        by_file.setdefault(claim["phase_file"], {})[claim["line"]] = claim

    marked = 0
    carried = {}
    for name in PHASE_FILES:
        phase = PHASE_FILES.index(name) + 1
        source = parent_dir / name
        if not source.exists() or name == "07-final-report.md":
            continue  # Phase 7 is regenerated, never carried.
        if child_state.get("mode") == "classic" and phase == 8:
            continue
        if parent_phases is not None and phase not in parent_phases:
            continue
        marked += _carry_phase(source, run_dir / name, by_file.get(name, {}), renumber, index)
        carried[name] = {
            "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "sha256": hashlib.sha256((run_dir / name).read_bytes()).hexdigest(),
        }

    (run_dir / "carry.json").write_text(json.dumps(_carry_record(parent_dir, carried), indent=2, sort_keys=True) + "\n",
                                        encoding="utf-8")
    added = changes.get("symbols", {}).get("added", [])
    if added:
        _append_added_symbols(run_dir, added)
    print(f"carry: {len(carried)} phase files copied, {marked} claims marked stale, {len(added)} symbols added")
    return 0


def _legacy_check(args: argparse.Namespace) -> int:
    """
    The publication gate for an incremental run: no claim may still be marked
    stale, and every symbol the change set added must be cited somewhere.

    "Cited" means a phase file names it through the same `path::symbol` form
    every other citation in this file is matched by, on a line that is not
    itself a stale marker: a marker's own `cites=` field is written in that
    same shape, so it must be excluded before matching, or a claim's own
    unresolved marker would count as the documentation that resolves it. The
    citation must also resolve to the SAME file the symbol was added in, not
    merely carry the same bare name: two files can each define a `handler`,
    and a citation of one must never document an addition to the other. The
    path index is built from the added symbols' own files only, so a
    citation of an unrelated file never even attempts to resolve.
    """
    run_dir = Path(args.run_dir)
    changes = _read_json(run_dir / "changes.json")
    if changes is None:
        print("check: no changes.json in the run directory; run `diff` first", file=sys.stderr)
        return 2

    added = changes.get("symbols", {}).get("added", [])
    index = _path_index({item["file"] for item in added})

    problems: list[str] = []
    documented: set[tuple[str, str]] = set()
    for name in PHASE_FILES:
        path = run_dir / name
        if not path.exists():
            continue
        for number, line in enumerate(read_text(path).split("\n"), start=1):
            if line.startswith(MARKER_PREFIX):
                problems.append(f"{name}:{number}: claim still marked stale: {line.strip()}")
                continue
            for path_text, symbol in cited_symbols(line):
                resolved = _match_cited_path(path_text, index)
                if resolved:
                    documented.add((resolved, symbol))

    for item in added:
        if (item["file"], item["symbol"]) not in documented:
            problems.append(
                f"added symbol never documented: {item['file']}::{item['symbol']}"
            )

    if problems:
        print("check: FAILED")
        for problem in problems:
            print(f"  {problem}")
        return 1
    print("check: clean")
    return 0
