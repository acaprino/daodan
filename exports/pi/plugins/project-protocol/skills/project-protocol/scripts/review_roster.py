"""Compute a review roster from measured signals, so the model never chooses its own rigor.

The first live run of the task cycle (2026-10-19) dispatched seven reviewers, a
security auditor and a Git-history pass among them, for a change inside one
function: 40 minutes and 30.90 USD. The method said "proportionate to risk"
and the model, reading it, did everything. This helper turns that sentence into
data: it reads a diff and, when available, the Codebase Map's impact packet,
decides the tier and the roster, and writes them so the protocol can refuse a
dispatch the roster does not contain.

Two shapes, four kinds:

- ``light``: the review before each commit, and of a decision record or a plan
  inside the cycle. Project tools, then one reviewer: the generalist for code,
  the premise auditor's claim check for a plan, a specification or a document.
- ``branch``: the review before a merge. A changeset gets a tier, ``small``,
  ``medium`` or ``large``; ``large`` is forced by a changed public interface, a
  sensitive path or a changed manifest, and ``medium`` by several modules or many
  callers. A plan, a specification or a document gets its kind's fixed set.

Beside the roster, ``support`` names the roles the procedure itself dispatches:
the verification lenses, and at ``large`` the map analyst and the interconnect
mapper. The protocol accepts a delivery bound to a review only from the two.

Signals come from three sources, all mechanical: ``git diff --numstat`` and the
unified diff of the candidate, the impact packet of ``snapshot.py edit-impact``
when a map exists, and path patterns. A missing map is recorded as a gap and
never raises or lowers the tier by itself.

Standard library only. Thresholds live in one place at the top and are tuned
on probes; every change to them is recorded with the probe that motivated it.

Usage:

    python review_roster.py compute --shape light|branch [--kind changeset|plan|spec|doc]
        --diff DIFF.patch [--numstat NUMSTAT.txt] [--impact IMPACT.json] [--deeper]
        [--id REVIEW_ID --stage STAGE] --out ROSTER.json
    python review_roster.py check --roster ROSTER.json --dispatch DISPATCH.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SCHEMA = "daodan/review-roster/v1"

# Thresholds. Tuned on the probe of 2026-10-19 (humanize #379: 2 files, 9 hunks,
# 1 function, 0 production callers, no interface change -> small).
MEDIUM_MODULES = 3          # distinct top-level source directories touched
MEDIUM_CALLERS = 5          # one-hop callers of any changed symbol, from the map
MEDIUM_FILES = 6            # production files changed
LARGE_CALLERS = 20

SENSITIVE_PATH = re.compile(
    r"(^|/)(auth|authn|authz|authentication|authorization|oauth|session|login|"
    r"payment|payments|billing|checkout|stripe|"
    r"persistence|repository|repositories|db|database|migrations?|schema|"
    r"concurrency|lock|locks|worker|workers|queue|queues|"
    r"crypto|cryptography|secret|secrets|security)(/|\.|$)",
    re.IGNORECASE,
)
MANIFEST_NAME = re.compile(
    r"(^|/)(pyproject\.toml|setup\.py|setup\.cfg|uv\.lock|poetry\.lock|requirements[^/]*\.txt|"
    r"package\.json|package-lock\.json|pnpm-lock\.yaml|yarn\.lock|bun\.lockb?|"
    r"Cargo\.toml|Cargo\.lock|go\.mod|go\.sum|Gemfile(\.lock)?|composer\.(json|lock)|"
    r"pom\.xml|build\.gradle(\.kts)?|[^/]*\.csproj|packages\.lock\.json)$"
)
CONTRACT_NAME = re.compile(
    r"(^|/)([^/]*openapi[^/]*\.(ya?ml|json)|[^/]*swagger[^/]*\.(ya?ml|json)|[^/]*\.proto|"
    r"[^/]*\.graphql|[^/]*schema[^/]*\.(json|ya?ml|graphql)|[^/]*asyncapi[^/]*\.(ya?ml|json))$",
    re.IGNORECASE,
)
TEST_PATH = re.compile(r"(^|/)(tests?|spec|specs|__tests__)(/|$)|(^|/)(test_[^/]+|[^/]+_test|[^/]+\.(test|spec))\.[a-z]+$")
DOC_PATH = re.compile(r"\.(md|rst|txt|adoc)$", re.IGNORECASE)
LANGUAGE_BY_SUFFIX = {
    ".py": "python", ".pyi": "python",
    ".ts": "typescript", ".tsx": "typescript", ".js": "javascript", ".jsx": "javascript",
    ".rs": "rust", ".go": "go", ".java": "java", ".kt": "kotlin", ".sql": "sql",
    ".css": "stylesheet", ".scss": "stylesheet", ".less": "stylesheet",
}

KINDS = ("changeset", "plan", "spec", "doc")

# Roles by tier. The light shape has one reviewer by decision of 2026-10-19.
LIGHT_ROSTER = {"changeset": ["senior-review:code-auditor"]}
LIGHT_ROSTER.update({kind: ["senior-review:premise-auditor"] for kind in ("plan", "spec", "doc")})
SMALL_ROSTER = ["senior-review:code-auditor", "testing:test-suite-auditor"]
MEDIUM_ROSTER = SMALL_ROSTER + [
    "senior-review:logic-integrity-auditor",
    "abstraction-architect:abstraction-architect-agent",
    "senior-review:premise-auditor",
]
LARGE_ROSTER = MEDIUM_ROSTER + [
    "senior-review:security-auditor",
    "senior-review:data-integrity-auditor",
    "senior-review:cleanup-auditor",
    "repo-hygiene:workspace-auditor",
]
# The fixed set of a plan, a specification or a document under a branch review.
KIND_ROSTER = {
    "plan": ["senior-review:premise-auditor", "testing:test-suite-auditor",
             "senior-review:chicken-egg-detector", "abstraction-architect:abstraction-architect-agent"],
    "spec": ["senior-review:premise-auditor", "senior-review:logic-integrity-auditor",
             "abstraction-architect:abstraction-architect-agent", "testing:test-suite-auditor"],
    "doc": ["senior-review:premise-auditor"],
}
# Roles the procedure dispatches beside the reviewers: verification lenses always
# (lens 0 is the premise auditor, the other lenses and the critic isolated workers),
# the map and the interconnect map at the large tier.
SUPPORT = ["senior-review:premise-auditor", "project-protocol:isolated-worker"]
LARGE_SUPPORT = SUPPORT + ["codebase-map:map-analyst", "codebase-map:semantic-interconnect-mapper"]
# Signal-activated specialists, added at any branch tier when the signal is present.
LANGUAGE_ROLE = {
    "python": "project-protocol:isolated-worker#python",
    "typescript": "typescript-development:type-safety-auditor",
    "javascript": "typescript-development:type-safety-auditor",
}
SIGNAL_ROLE = {
    "react": "react-development:react-performance-optimizer",
    "timers": "senior-review:temporal-resilience-auditor",
    "resources": "senior-review:resource-lifecycle-auditor",
    "ui": "senior-review:ui-race-auditor",
    "startup": "senior-review:chicken-egg-detector",
    "distributed": "senior-review:distributed-flow-auditor",
    "contract": "senior-review:api-contract-auditor",
    "manifest": "project-protocol:isolated-worker#dependencies",
    "persistence": "senior-review:data-integrity-auditor",
    "trust": "senior-review:security-auditor",
}
# A trust word in prose is a specification touching a boundary; in code it is
# everywhere, and code reaches the security auditor through sensitive paths.
PROSE_ONLY_SIGNALS = {"trust"}
VERIFICATION = {"light": "critical-high", "small": "high-and-above", "medium": "all-above-floor", "large": "all-above-floor"}

ADDED_LINE = re.compile(r"^\+(?!\+\+)")
HUNK = re.compile(r"^@@ .* @@\s*(.*)$")
PY_DEF = re.compile(r"^[+-]\s*(?:async\s+)?def\s+([A-Za-z_]\w*)\s*\(")
TS_EXPORT = re.compile(r"^[+-]\s*export\s+(?:default\s+)?(?:async\s+)?(?:function|class|const|let|interface|type|enum)\s+([A-Za-z_$][\w$]*)")
SIGNAL_PATTERNS = {
    "timers": re.compile(r"\b(setTimeout|setInterval|time\.sleep|asyncio\.sleep|retry|backoff|cron|schedule|threading\.Timer)\b"),
    "resources": re.compile(r"\b(open\(|socket\.|subprocess\.|Popen|connect\(|ThreadPool|ProcessPool|acquire\(|release\(|close\(\))"),
    "ui": re.compile(r"\b(useEffect|useLayoutEffect|requestAnimationFrame|scrollTo|focus\(\)|ResizeObserver|IntersectionObserver)\b"),
    "startup": re.compile(r"\b(__main__|bootstrap|on_startup|lifespan|init_app|configure\(|register\()"),
    "distributed": re.compile(r"\b(requests\.|httpx\.|fetch\(|grpc|kafka|rabbit|celery|sqs|pubsub|publish\(|consume\()"),
    "react": re.compile(r"\b(from ['\"]react['\"]|useState|useEffect|React\.)"),
    "persistence": re.compile(r"\b(SELECT|INSERT INTO|DELETE FROM|CREATE TABLE|ALTER TABLE|transaction|"
                              r"rollback|bulk_create|session\.add|migrations?)\b"),
    "trust": re.compile(r"\b(authentication|authorization|credentials?|passwords?|tokens?|permissions?|"
                        r"encrypt\w*|trust boundary)\b", re.IGNORECASE),
}


def read_numstat(text: str) -> list[dict]:
    rows = []
    for line in text.splitlines():
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        added, removed, path = parts
        rows.append({
            "path": path.strip(),
            "added": None if added == "-" else int(added),
            "removed": None if removed == "-" else int(removed),
        })
    return rows


def numstat_from_diff(diff: str) -> list[dict]:
    rows: dict[str, dict] = {}
    current = None
    for line in diff.splitlines():
        if line.startswith("+++ "):
            path = line[4:].strip()
            if path.startswith("b/"):
                path = path[2:]
            current = None if path == "/dev/null" else path
            if current:
                rows.setdefault(current, {"path": current, "added": 0, "removed": 0})
        elif line.startswith("--- ") or line.startswith("diff ") or line.startswith("@@"):
            continue
        elif current and line.startswith("+"):
            rows[current]["added"] += 1
        elif current and line.startswith("-"):
            rows[current]["removed"] += 1
    return list(rows.values())


def classify_path(path: str) -> str:
    if MANIFEST_NAME.search(path):
        return "manifest"
    if CONTRACT_NAME.search(path):
        return "contract"
    if TEST_PATH.search(path):
        return "test"
    if DOC_PATH.search(path):
        return "doc"
    return "production"


def interface_changes(diff: str) -> list[str]:
    """Public signatures whose definition line changed on both sides of the diff."""
    removed, added = set(), set()
    for line in diff.splitlines():
        for pattern in (PY_DEF, TS_EXPORT):
            match = pattern.match(line)
            if match:
                name = match.group(1)
                if line.startswith("-"):
                    removed.add(name)
                elif line.startswith("+"):
                    added.add(name)
    # A changed signature appears as a removed and an added def of the same name
    # whose lines differ; a renamed or new function is not an interface change of
    # an existing caller. Names that are private by convention are skipped.
    changed = {name for name in removed & added if not name.startswith("_")}
    return sorted(changed)


def touched_symbols(diff: str) -> list[str]:
    names = set()
    for line in diff.splitlines():
        match = HUNK.match(line)
        if match:
            context = match.group(1)
            found = re.search(r"(?:def|class|function|fn|func)\s+([A-Za-z_]\w*)", context)
            if found:
                names.add(found.group(1))
    return sorted(names)


def content_signals(diff: str) -> dict[str, bool]:
    added = "\n".join(line for line in diff.splitlines() if ADDED_LINE.match(line))
    return {name: bool(pattern.search(added)) for name, pattern in SIGNAL_PATTERNS.items()}


def impact_signals(impact: dict | None) -> dict:
    """Read the map's impact packet: callers and digest changes per target."""
    if not impact:
        return {"available": False, "max_callers": 0, "interface_changed": [], "effects_changed": []}
    max_callers, interface_changed, effects_changed = 0, [], []
    for target in impact.get("targets", []):
        callers = target.get("callers") or {}
        total = callers.get("total") if isinstance(callers, dict) else len(callers)
        max_callers = max(max_callers, int(total or 0))
        history = target.get("recent_changes") or target.get("history") or []
        for change in history:
            kind = change.get("kind") if isinstance(change, dict) else change
            name = target.get("id") or target.get("symbol") or "?"
            if kind == "interface_changed":
                interface_changed.append(name)
            elif kind == "effects_changed":
                effects_changed.append(name)
    return {
        "available": True,
        "max_callers": max_callers,
        "interface_changed": sorted(set(interface_changed)),
        "effects_changed": sorted(set(effects_changed)),
    }


def signal_roles(signals: dict, kind: str, roster: list[str]) -> list[str]:
    added = []
    for language in signals["languages"] if kind == "changeset" else ():
        role = LANGUAGE_ROLE.get(language)
        if role and role not in roster + added:
            added.append(role)
    for name, present in signals["content"].items():
        if present and (kind != "changeset" or name not in PROSE_ONLY_SIGNALS) and SIGNAL_ROLE[name] not in roster + added:
            added.append(SIGNAL_ROLE[name])
    for name in ("contract", "manifest"):
        if signals[name] and SIGNAL_ROLE[name] not in roster + added:
            added.append(SIGNAL_ROLE[name])
    return added


def compute(shape: str, diff: str, numstat: list[dict] | None, impact: dict | None, deeper: bool,
            kind: str = "changeset", review_id: str | None = None, stage: str | None = None) -> dict:
    if kind not in KINDS:
        raise ValueError(f"kind must be one of {', '.join(KINDS)}")
    rows = numstat if numstat else numstat_from_diff(diff)
    kinds = {row["path"]: classify_path(row["path"]) for row in rows}
    production = [p for p, k in kinds.items() if k == "production"]
    modules = sorted({Path(p).parts[0] if len(Path(p).parts) > 1 else "." for p in production})
    languages = sorted({LANGUAGE_BY_SUFFIX[Path(p).suffix] for p in production if Path(p).suffix in LANGUAGE_BY_SUFFIX})
    lines = sum((row["added"] or 0) + (row["removed"] or 0) for row in rows)
    interfaces = interface_changes(diff)
    map_signals = impact_signals(impact)
    signals = {
        "files": len(rows),
        "production_files": len(production),
        "lines": lines,
        "modules": modules,
        "languages": languages,
        "symbols": touched_symbols(diff),
        "interface_changed": sorted(set(interfaces) | set(map_signals["interface_changed"])),
        "effects_changed": map_signals["effects_changed"],
        "max_callers": map_signals["max_callers"],
        "sensitive_paths": sorted(p for p in production if SENSITIVE_PATH.search(p)),
        "manifest": sorted(p for p, k in kinds.items() if k == "manifest"),
        "contract": sorted(p for p, k in kinds.items() if k == "contract"),
        "content": content_signals(diff),
        "map_available": map_signals["available"],
    }
    gaps = [] if map_signals["available"] else ["no Codebase Map impact packet: callers and digest changes unknown"]

    reasons: list[str] = []
    advice: list[str] = []
    if shape == "light":
        tier = "light"
        roster = list(LIGHT_ROSTER[kind])
        if signals["interface_changed"] or signals["sensitive_paths"] or signals["manifest"] or signals["contract"]:
            advice.append("strong signals: run review-branch before merging")
        if deeper:
            advice.append("a deeper review is review-branch; the light review has one reviewer")
    elif kind != "changeset":
        tier = "small"
        reasons.append(f"fixed set of a {kind}")
        roster = list(KIND_ROSTER[kind])
        roster += signal_roles(signals, kind, roster)
        if deeper:
            advice.append(f"a {kind} has one fixed set and no deeper tier")
    else:
        tier = "small"
        if signals["interface_changed"]:
            tier, reasons = "large", reasons + [f"public interface changed: {', '.join(signals['interface_changed'])}"]
        if signals["sensitive_paths"]:
            tier, reasons = "large", reasons + [f"sensitive paths: {', '.join(signals['sensitive_paths'])}"]
        if signals["manifest"] or signals["contract"]:
            tier, reasons = "large", reasons + [f"manifest or contract changed: {', '.join(signals['manifest'] + signals['contract'])}"]
        if signals["max_callers"] >= LARGE_CALLERS:
            tier, reasons = "large", reasons + [f"{signals['max_callers']} callers of a changed symbol"]
        if tier != "large":
            if len(modules) >= MEDIUM_MODULES:
                tier, reasons = "medium", reasons + [f"{len(modules)} modules touched"]
            if signals["max_callers"] >= MEDIUM_CALLERS:
                tier, reasons = "medium", reasons + [f"{signals['max_callers']} callers of a changed symbol"]
            if len(production) >= MEDIUM_FILES:
                tier, reasons = "medium", reasons + [f"{len(production)} production files changed"]
            if signals["effects_changed"]:
                tier, reasons = "medium", reasons + [f"effects changed: {', '.join(signals['effects_changed'])}"]
        if deeper and tier != "large":
            tier = {"small": "medium", "medium": "large"}[tier]
            reasons.append("caller asked for a deeper review")
        roster = list({"small": SMALL_ROSTER, "medium": MEDIUM_ROSTER, "large": LARGE_ROSTER}[tier])
        roster += signal_roles(signals, kind, roster)
    if not reasons:
        reasons.append("no raising signal")
    review = {} if review_id is None else {"id": review_id, "stage": stage or shape}
    return {
        **review,
        "schema": SCHEMA,
        "shape": shape,
        "kind": kind,
        "tier": tier,
        "reasons": reasons,
        "roster": roster,
        "support": list(LARGE_SUPPORT if tier == "large" and kind == "changeset" else SUPPORT),
        "verification": VERIFICATION[tier],
        "blind_derivation": tier in ("medium", "large"),
        "critic": tier == "large",
        "signals": signals,
        "gaps": gaps,
        "advice": advice,
    }


def check(roster: dict, dispatch: dict) -> list[str]:
    """Return the reasons a dispatch exceeds the roster; empty when it conforms."""
    problems = []
    allowed = set(roster.get("roster", [])) | set(roster.get("support", []))
    requested = dispatch.get("roles", [])
    extra = sorted(set(requested) - allowed)
    if extra:
        problems.append("roles outside the computed roster: " + ", ".join(extra))
    if dispatch.get("blind_derivation") and not roster.get("blind_derivation"):
        problems.append("blind derivation is not in this tier")
    if dispatch.get("critic") and not roster.get("critic"):
        problems.append("the completeness critic is not in this tier")
    if roster.get("schema") != SCHEMA:
        problems.append("roster schema is not " + SCHEMA)
    return problems


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    compute_parser = sub.add_parser("compute")
    compute_parser.add_argument("--shape", choices=("light", "branch"), required=True)
    compute_parser.add_argument("--kind", choices=KINDS, default="changeset")
    compute_parser.add_argument("--id", dest="review_id", help="the review's id in the run's reviews list")
    compute_parser.add_argument("--stage", help="record, plan, wave-<n>, candidate or standalone")
    compute_parser.add_argument("--diff", required=True, help="unified diff of the candidate")
    compute_parser.add_argument("--numstat", help="git diff --numstat output; derived from the diff when absent")
    compute_parser.add_argument("--impact", help="snapshot.py edit-impact JSON for the changed symbols")
    compute_parser.add_argument("--deeper", action="store_true", help="the caller asked for one tier more")
    compute_parser.add_argument("--out", required=True)
    check_parser = sub.add_parser("check")
    check_parser.add_argument("--roster", required=True)
    check_parser.add_argument("--dispatch", required=True, help='JSON {"roles": [...], "blind_derivation": bool, "critic": bool}')
    args = parser.parse_args(argv)

    if args.command == "compute":
        diff = Path(args.diff).read_text(encoding="utf-8", errors="replace")
        numstat = read_numstat(Path(args.numstat).read_text(encoding="utf-8")) if args.numstat else None
        impact = json.loads(Path(args.impact).read_text(encoding="utf-8")) if args.impact else None
        result = compute(args.shape, diff, numstat, impact, args.deeper, args.kind, args.review_id, args.stage)
        Path(args.out).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({"tier": result["tier"], "roster": result["roster"], "reasons": result["reasons"], "gaps": result["gaps"]}))
        return 0
    roster = json.loads(Path(args.roster).read_text(encoding="utf-8"))
    dispatch = json.loads(Path(args.dispatch).read_text(encoding="utf-8"))
    problems = check(roster, dispatch)
    print(json.dumps({"conforms": not problems, "problems": problems}))
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
