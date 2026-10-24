"""Fact-anchor linter for the plugin marketplace.

Stdlib only, no dependencies, runs from the repository root:

    python scripts/lint_fact_anchors.py            # check
    python scripts/lint_fact_anchors.py --report   # print every anchored value found

A knowledge plugin states the same load-bearing fact in several places on purpose.
The `ibkr` skill is the worked example: its execution-correction rule appears in five
files, its trigger-method guidance in four, and every fact worth knowing is echoed
from a reference into the agent's digest and again into an audit checklist. That
redundancy is deliberate. Each artifact is loaded on its own, so an agent reading
only the digest must still get the right number.

The cost is that a correction has to land in every copy at once. On 2026-08-13 a
single research pass corrected ten such facts across ten releases, by hand, and the
Web API rate limit had already been wrong in one file for months: a per-endpoint
number (10 req/s) stated as the global one (50 req/s per authenticated username).
Nothing mechanical would have caught it, because every copy was internally
plausible and no two were compared.

This linter compares them. Each anchor names a fact, the file that owns it, and a
regex whose first group captures the value. Every tracked or nonignored new repository source is scanned
for that regex; if two files report different values, the anchor fails and both are
named. It also checks explicitly required independent copies: a missing statement
is a coverage failure. Value comparison remains narrow, comparing statements of
the same fact rather than judging unrelated prose.

Three failure modes are reported:

  1. conflicts     two or more files state different values for one anchor. This is
                   the drift the linter exists for.
  2. orphans       an explicitly required copy is missing its statement, or
                   the owning file no longer states its own fact, so the anchor is
                   watching something that moved. Re-point the anchor or restore the
                   statement; do not delete the anchor to make the build pass.
  3. unanchored    (report mode only) not a failure. Lists anchors found in exactly
                   one file, i.e. facts with no echo to drift against yet.

Adding an anchor is cheap and is the right response to correcting a fact twice.
Pick a phrasing stable enough to survive an edit, capture the value in group 1, and
prefer a number or a short verbatim quote over a sentence.
"""
import os
import re
import subprocess
import sys
from pathlib import Path

# Anchors: id -> (owner, pattern, description).
#
# The pattern's first group must capture the value being compared. Write it to
# match the fact rather than the sentence around it, so a rewording does not
# orphan the anchor. Values are compared case-insensitively after whitespace
# collapse, so "3 Minutes" and "3  minutes" agree.
# A count written as an English word or as digits. Anchors that compare a threshold use this
# rather than naming one spelling: a mutation that rewords "four" to "two" must produce a value
# conflict, not silently stop matching and drop that file out of the comparison.
_COUNT = r"(?:zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|\d+)"

ANCHORS = {
    "working-principle-material-assumptions": (
        "plugins/work-controller/skills/work-record/SKILL.md",
        r"(?m)^Working assumptions: ([^\n]+)$",
        "Material assumptions and essential decisions must agree across independently loaded instructions",
    ),
    "working-principle-sufficient-simplicity": (
        "plugins/work-controller/skills/work-record/SKILL.md",
        r"(?m)^Working simplicity: ([^\n]+)$",
        "Sufficient design and existing ownership must agree across independently loaded instructions",
    ),
    "working-principle-authorized-scope": (
        "plugins/work-controller/skills/work-record/SKILL.md",
        r"(?m)^Working scope: ([^\n]+)$",
        "Owned edits and authorized removal must agree across independently loaded instructions",
    ),
    "working-principle-observable-verification": (
        "plugins/work-controller/skills/work-record/SKILL.md",
        r"(?m)^Working verification: ([^\n]+)$",
        "Observable criteria and required completion gates must agree across independently loaded instructions",
    ),
    "test-assertion-protection": (
        "plugins/testing/skills/test-hygiene/SKILL.md",
        r"(?m)^Assertion protection: ([^\n]+)$",
        "Independent oracle corrections and active product protection must agree across instruction copies",
    ),
    "test-retirement-protection": (
        "plugins/testing/skills/test-hygiene/SKILL.md",
        r"(?m)^Test retirement: ([^\n]+)$",
        "Retirement needs retired behavior or verified equivalent replacement in the same candidate",
    ),
    "test-layer-ownership": (
        "plugins/testing/skills/test-hygiene/SKILL.md",
        r"(?m)^Test ownership: ([^\n]+)$",
        "Unit and flow ownership must agree in canonical testing and independently loaded instruction blocks",
    ),
    "working-principle-shared-concept-owner": (
        "plugins/project-knowledge/skills/instructions-method/references/working-principles.md",
        r"### 5\. Centralize Shared Logic\n([^\n]+)",
        "Shared concept ownership rule: instruction examples and the canonical working block must agree",
    ),
    "xray-incident-apply-share": (
        "docs/plugins/codebase-map.md",
        r"(\d+)% of the applied rules used `@apply`",
        "share of the incident tree's applied rules written with Tailwind @apply, which justifies the expansion in the stylesheet adapter; corrected once from a figure that measured something else",
    ),
    "xray-snapshot-path": (
        "plugins/codebase-map/skills/map-method/references/snapshot.md",
        r"snapshot/([\w.-]+\.json)",
        "Codebase Map snapshot manifest path, stated in the skill and the plugin doc",
    ),
}

# These independent instruction surfaces must each carry the compact rules.
# Rendered host copies are checked by the host contract suite.
_WORKING_PRINCIPLE_COPIES = (
    "plugins/work-controller/skills/work-record/SKILL.md",
    "CLAUDE.md",
    "AGENTS.md",
    "plugins/project-knowledge/skills/instructions-method/references/working-principles.md",
    "plugins/project-knowledge/skills/instructions-method/references/instruction-example.md",
)
REQUIRED_COPIES = {
    "working-principle-material-assumptions": _WORKING_PRINCIPLE_COPIES,
    "working-principle-sufficient-simplicity": _WORKING_PRINCIPLE_COPIES,
    "working-principle-authorized-scope": _WORKING_PRINCIPLE_COPIES,
    "working-principle-observable-verification": _WORKING_PRINCIPLE_COPIES,
}

# Directories that are not shipped content and may legitimately restate a fact in
# a historical context (a changelog entry describes what a release said at the
# time, and must not be rewritten when the fact is later corrected).
#
# `docs/superpowers/` is deliberately absent from this tuple: two design documents
# under it currently state anchored facts, and whether they belong in the scan was
# analysed and left open rather than decided, because widening this list on a
# hypothesis is how coverage dies quietly. The changelog argument above cuts both
# ways here: a dated plan is a historical record the same way a changelog entry
# is, so rewriting it to keep a build green falsifies history, but unlike a
# changelog it does not announce itself as historical to a reader who does not
# already know the convention. Revisit only when a real conflict names a
# `docs/superpowers/` file as one of the two disagreeing copies, not on a hunch.
#
# `.peer-review` is excluded for the changelog reason at its strongest. A run
# directory holds an external model's words quoted verbatim, and the protocol that
# writes it forbids editing them: a claim and its falsifier are byte-identical for
# the whole run, and a ledger is never hand-edited. So a transcript that happens to
# quote an anchored fact, or to propose a mutation of one, cannot be corrected to
# keep this check green without destroying the evidence. It is also git-ignored, so
# it exists in one working tree and never in CI or another clone, which means a
# conflict it raises is invisible to everyone but the person who ran the review.
# Found on 2026-09-07, when a peer review of the constraint-saturation threshold
# quoted a proposed mutation of the verifier trigger, with a different lower bound
# than the shipped one, and failed this linter locally while CI stayed green.
EXCLUDED = (
    ".git",
    "evals",
    "node_modules",
    "__pycache__",
    ".superpowers",
    ".peer-review",
)
EXCLUDED_FILES = {
    Path("exports/vscode/CHANGELOG.md"),
}

SCANNED_SUFFIXES = {".md", ".py", ".json", ".tsv"}

failures = []


def scan_files():
    """Scan current repository sources, never private caches or historical run data.

    Git includes tracked files even when an ignore rule matches them, and new
    untracked sources remain visible. Required copies are still checked below;
    a missing required source fails rather than silently reducing coverage.
    """
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    paths = {Path(os.fsdecode(value)) for value in result.stdout.split(b"\0") if value}
    for path in sorted(paths):
        if not path.is_file() or path.suffix not in SCANNED_SUFFIXES:
            continue
        parts = set(path.parts)
        if parts & set(EXCLUDED) or path in EXCLUDED_FILES:
            continue
        yield path


def normalize(value):
    return re.sub(r"\s+", " ", value).strip().lower().replace(",", "")


def find(pattern, text):
    """All captured values for a pattern, normalized. Groups may be alternated,
    so take the first group that actually matched."""
    out = []
    for match in re.finditer(pattern, text):
        value = next((g for g in match.groups() if g), None)
        if value is not None:
            out.append(normalize(value))
    return out


def check():
    files = list(scan_files())
    texts = {}
    for path in files:
        try:
            texts[path] = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue

    conflicts, orphans, singles, checked = [], [], [], 0

    for anchor_id, (owner, pattern, description) in sorted(ANCHORS.items()):
        owner_path = Path(owner)
        compiled = re.compile(pattern)
        for required_path in REQUIRED_COPIES.get(anchor_id, ()):
            if not find(compiled, texts.get(Path(required_path), "")):
                orphans.append((anchor_id, owner, description,
                                "required copy is silent: " + required_path))
        by_value = {}
        for path, text in texts.items():
            for value in find(compiled, text):
                by_value.setdefault(value, []).append(path.as_posix())

        if not by_value:
            orphans.append((anchor_id, owner, description, "stated nowhere"))
            continue

        owner_values = find(compiled, texts.get(owner_path, ""))
        if not owner_values:
            where = sorted({p for paths in by_value.values() for p in paths})
            orphans.append((anchor_id, owner, description,
                            "owner is silent; stated in " + ", ".join(where[:3])))
            continue

        checked += 1
        if len(by_value) > 1:
            conflicts.append((anchor_id, description, owner, by_value))
        elif sum(len(v) for v in by_value.values()) == 1:
            singles.append((anchor_id, description))

    return conflicts, orphans, singles, checked, len(texts)


def report(name, rows, formatter, hint):
    if rows:
        failures.append(name)
        print(f"FAIL  {name}: {len(rows)}")
        for row in rows:
            for line in formatter(row):
                print(f"      {line}")
        print(f"      fix: {hint}")
    else:
        print(f"ok    {name}")


def format_conflict(row):
    anchor_id, description, owner, by_value = row
    lines = [f"{anchor_id}: {description}", f"  owner: {owner}"]
    for value, paths in sorted(by_value.items()):
        lines.append(f"  value {value!r} in:")
        lines.extend(f"    {p}" for p in sorted(paths))
    return lines


def format_orphan(row):
    anchor_id, owner, description, why = row
    return [f"{anchor_id}: {description}", f"  owner {owner}: {why}"]


def main():
    if not Path(".claude-plugin/marketplace.json").is_file():
        sys.exit("run from the repository root: .claude-plugin/marketplace.json not found")

    report_mode = "--report" in sys.argv
    conflicts, orphans, singles, checked, scanned = check()

    print(f"{scanned} files scanned, {len(ANCHORS)} anchor(s) declared, {checked} verified")
    if singles:
        print(f"{len(singles)} anchor(s) stated in one place only (nothing to drift against)")
    print()

    if report_mode:
        print("--- anchored values ---")
        for anchor_id, (owner, pattern, description) in sorted(ANCHORS.items()):
            values = find(re.compile(pattern), Path(owner).read_text(encoding="utf-8")
                          if Path(owner).is_file() else "")
            shown = ", ".join(sorted(set(values))) or "(not found)"
            print(f"  {anchor_id:32} {shown:24} {description}")
        print()

    report("value conflicts", conflicts, format_conflict,
           "one fact, one value: correct every copy, or delete the echo and point "
           "at the owning reference instead")
    report("anchor owners", orphans, format_orphan,
           "re-point the anchor at the file that now owns the fact, or restore the "
           "statement in the owner and every required copy; never delete an anchor to go green")

    if failures:
        sys.exit(f"\n{len(failures)} check(s) failed: {', '.join(failures)}")
    print("\nall checks passed")


if __name__ == "__main__":
    main()
