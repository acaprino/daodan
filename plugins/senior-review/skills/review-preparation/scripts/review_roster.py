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
        --diff DIFF.patch [--numstat NUMSTAT.txt] [--impact IMPACT.json] [--context CONTEXT.json] [--deeper]
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
# A generated generalist must preserve the former body's boundary checks.
# Preparation may exclude a family only with candidate/scope-bound source evidence.
CODE_FLOOR = [f"senior-review:{name}" for name in (
    "input-validation-auditor", "resource-lifecycle-auditor", "algorithmic-cost-auditor",
    "security-auditor", "data-integrity-auditor", "chicken-egg-detector",
    "temporal-resilience-auditor", "distributed-flow-auditor", "api-contract-auditor",
)] + ["testing:test-reliability-auditor"]
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
SUPPORT = ["senior-review:premise-auditor", "work-controller:isolated-worker"]
LARGE_SUPPORT = SUPPORT + ["codebase-map:map-analyst", "codebase-map:semantic-interconnect-mapper"]
# Signal-activated specialists, added at any branch tier when the signal is present.
LANGUAGE_ROLE = {
    "python": "work-controller:isolated-worker#python",
    "typescript": "typescript-development:type-safety-auditor",
    "javascript": "typescript-development:type-safety-auditor",
}
SIGNAL_ROLE = {
    "accessibility": "senior-review:accessibility-auditor",
    "performance": "senior-review:performance-auditor",
    "operability": "senior-review:operability-auditor",
    "platform": "platform-engineering:platform-reviewer",
    "react": "react-development:react-performance-optimizer",
    "timers": "senior-review:temporal-resilience-auditor",
    "resources": "senior-review:resource-lifecycle-auditor",
    "ui": "senior-review:ui-race-auditor",
    "startup": "senior-review:chicken-egg-detector",
    "distributed": "senior-review:distributed-flow-auditor",
    "contract": "senior-review:api-contract-auditor",
    "manifest": "work-controller:isolated-worker#dependencies",
    "persistence": "senior-review:data-integrity-auditor",
    "trust": "senior-review:security-auditor",
}
# A trust word in prose is a specification touching a boundary; in code it is
# everywhere, and code reaches the security auditor through sensitive paths.
PROSE_ONLY_SIGNALS = {"trust"}
VERIFICATION = {"light": "critical-high", "small": "high-and-above", "medium": "all-above-floor", "large": "all-above-floor"}

CHANGED_LINE = re.compile(r"^[+-](?![+-]{2})")
HUNK = re.compile(r"^@@ .* @@\s*(.*)$")
HUNK_COUNTS = re.compile(r"^@@ -\d+(?:,(\d+))? \+\d+(?:,(\d+))? @@")
PY_DEF = re.compile(r"^[+-]\s*(?:async\s+)?def\s+([A-Za-z_]\w*)\s*\(")
TS_EXPORT = re.compile(r"^[+-]\s*export\s+(?:default\s+)?(?:async\s+)?(?:function|class|const|let|interface|type|enum)\s+([A-Za-z_$][\w$]*)")
SIGNAL_PATTERNS = {
    "accessibility": re.compile(
        r"\b(?:aria-[a-z-]+|tab[Ii]ndex|accessibilityLabel|accessibilityRole|"
        r"screen.?reader|focusTrap|preventDefault|onKeyDown|onKeyUp)\b|"
        r"\b(?:document\.(?:querySelector|createElement|getElementById)|event\.key|"
        r"addEventListener\(['\"](?:key|focus))|<\s*(?:button|input|select|textarea|dialog|form)\b",
        re.IGNORECASE,
    ),
    "performance": re.compile(
        r"\b(?:SELECT\s+.+\s+FROM|CREATE\s+(?:UNIQUE\s+)?INDEX|EXPLAIN\s+(?:ANALYZE|SELECT))\b|"
        r"\b(?:select_related|prefetch_related|joinedload|selectinload|executemany|bulk_create|"
        r"bulkWrite|findMany|sorted|lru_cache|re\.compile)\s*\(|\.sort\s*\(|"
        r"\b(?:rate_limit|rateLimit|cache_ttl|cacheTTL|page_size|pageSize|pool_size|"
        r"max_connections|memory_limit|cpu_limit|requests_per_second)\b|Cache-Control",
        re.IGNORECASE,
    ),
    "operability": re.compile(
        r"\b(?:logger|logging|log)\.(?:debug|info|warning|warn|error|exception|critical|fatal)\b|"
        r"\b(?:opentelemetry|prometheus|healthcheck|readinessProbe|livenessProbe|startupProbe|"
        r"featureFlag|feature_flag|pg_dump|pg_restore|mysqldump|restore_backup|create_backup|"
        r"sentry_sdk|graceful_shutdown|terminationGracePeriodSeconds|maxUnavailable|rollingUpdate)\b|"
        r"\b(?:helm\s+rollback|kubectl\s+rollout|Sentry\.init)\b",
        re.IGNORECASE,
    ),
    "platform": re.compile(
        r"\b(?:localStorage|sessionStorage|indexedDB|serviceWorker|ipcRenderer|contextBridge|"
        r"BrowserWindow|NSAppTransportSecurity|WKWebView|WebView|document\.cookie)\b|"
        r"@tauri-apps/|\b(?:Content-Security-Policy|SameSite|httpOnly|Notification\.requestPermission)\b",
        re.IGNORECASE,
    ),
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

# A changed presentation or deployment file is evidence even when its diff has
# no framework-specific API. Tests and documents do not activate these by path.
SIGNAL_PATHS = {
    "accessibility": re.compile(r"\.(?:html?|xhtml|jsx|tsx|vue|svelte|css|scss|less)(?:\.j2)?$", re.IGNORECASE),
    "performance": re.compile(r"\.sql$|(?:^|/)(?:queries|cache|caching|pagination|rate[-_]?limit)(?:/|\.|$)", re.IGNORECASE),
    "operability": re.compile(
        r"(?:^|/)(?:\.github/workflows|deploy(?:ment)?|infra(?:structure)?|k8s|kubernetes|helm|"
        r"migrations?|backup|restore)(?:/|\.|$)|(?:^|/)(?:Dockerfile(?:\.[^/]+)?|"
        r"(?:docker-)?compose[^/]*\.ya?ml)$|\.(?:tf|tfvars)$", re.IGNORECASE),
    "platform": re.compile(
        r"(?:^|/)(?:tauri\.conf\.json|capacitor\.config\.[^/]+|electron[^/]*|"
        r"AndroidManifest\.xml|Info\.plist|(?:service-worker|sw)\.[jt]s)$|\.webmanifest$", re.IGNORECASE),
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
    old_path = None
    in_hunk = False
    old_left = new_left = None
    for line in diff.splitlines():
        if line.startswith("diff "):
            current = None
            old_path = None
            in_hunk = False
        elif line.startswith("rename from "):
            old_path = line.removeprefix("rename from ")
        elif line.startswith("rename to "):
            current = line.removeprefix("rename to ")
            rows[current] = {"path": current, "old_path": old_path, "added": 0, "removed": 0}
        elif line.startswith("--- ") and not in_hunk:
            path = line[4:].strip()
            current = None if path == "/dev/null" else path.removeprefix("a/")
            old_path = current
        elif line.startswith("+++ ") and not in_hunk:
            path = line[4:].strip()
            if path.startswith("b/"):
                path = path[2:]
            # A deleted file still supplies its old path and removed controls.
            if path != "/dev/null":
                current = path
            if current:
                rows.setdefault(current, {"path": current, "added": 0, "removed": 0})
                if old_path and old_path != current:
                    rows[current]["old_path"] = old_path
        elif line.startswith("@@"):
            in_hunk = True
            counts = HUNK_COUNTS.match(line)
            old_left = int(counts.group(1) or 1) if counts else None
            new_left = int(counts.group(2) or 1) if counts else None
        elif current and line.startswith("+"):
            rows[current]["added"] += 1
        elif current and line.startswith("-"):
            rows[current]["removed"] += 1
        # Unified diffs need no Git separator between files. Consume the hunk
        # before interpreting header-like source lines as the next file's paths.
        if in_hunk and old_left is not None and new_left is not None:
            if line.startswith((" ", "-")):
                old_left -= 1
            if line.startswith((" ", "+")):
                new_left -= 1
            if old_left == new_left == 0:
                in_hunk = False
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
    changed = "\n".join(line[1:] for line in diff.splitlines() if CHANGED_LINE.match(line))
    return {name: bool(pattern.search(changed)) for name, pattern in SIGNAL_PATTERNS.items()}


def evidence_gaps(value, label: str) -> list[str]:
    """Retain producer uncertainty, including positive totals beyond listed rows."""
    gaps = []
    if isinstance(value, dict):
        total, listed = value.get("total"), value.get("listed", value.get("items"))
        if type(total) is int and isinstance(listed, list) and total > len(listed):
            gaps.append(f"{label}: {total - len(listed)} omitted of {total}")
        for key, item in value.items():
            path = f"{label}.{key}"
            if item and (key in {"error", "errors", "gaps", "unknown_targets", "incompatible",
                                  "unavailable_edge_kinds", "blind_spots", "unbound_names"}
                         or key.startswith(("omitted", "truncated")) or key.endswith("_omitted")
                         or key == "exceeded"):
                if key != "blind_spots" or item.get("total") or item.get("unbound_names"):
                    gaps.append(f"{path}: {json.dumps(item, sort_keys=True)}")
            if key in {"status", "freshness"} and item not in {
                    "parsed", "file-level", "available", "fresh", "complete", "completed_empty",
                    "resolved", "ok", "ast", "RED", "GREEN", "untracked"}:
                gaps.append(f"{path}: {item}")
            if key == "applicability" and item not in {True, False, "yes", "no"}:
                gaps.append(f"{path}: {item}")
            if key not in {"source", "text", "blocks"}:
                gaps.extend(evidence_gaps(item, path))
            elif key == "source" and isinstance(item, dict):
                gaps.extend(evidence_gaps(item, path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            gaps.extend(evidence_gaps(item, f"{label}[{index}]"))
    return list(dict.fromkeys(gaps))


def snapshot_matches(actual, expected) -> bool:
    # These are the actual stale-callers producer's snapshot locators, not a
    # content digest. The preparer must independently retain the expected ones.
    fields = ("root", "target", "created_at", "parser_fingerprint")
    return (isinstance(actual, dict) and isinstance(expected, dict)
            and all(expected.get(key) and actual.get(key) == expected[key] for key in fields)
            and actual.get("repo_revision") == expected.get("repo_revision"))


def in_scope(path: str, paths: list[str]) -> bool:
    return any(item in {".", ""} or path == item or path.startswith(item.rstrip("/") + "/")
               for item in paths)


def impact_signals(impact: dict | None, context: dict | None = None,
                   paths: list[str] | None = None) -> dict:
    """Use snapshot-bound stale-callers deltas; edit-impact history is context."""
    context = context or {}
    paths = paths or []
    delta = context.get("stale_callers") or {}
    gaps = evidence_gaps(impact, "edit-impact") + evidence_gaps(delta, "stale-callers")
    valid_impact = isinstance(impact, dict) and impact.get("schema") == "daodan/edit-impact/v2"
    if not impact:
        gaps.insert(0, "no Codebase Map impact packet: callers and digest changes unknown")
    elif not valid_impact:
        gaps.append("edit-impact schema is unsupported or legacy; snapshot binding unknown")
    bound = (delta.get("schema") == "daodan/stale-callers/v1"
             and all(snapshot_matches(delta.get(side), context.get(side)) for side in ("base", "candidate")))
    if bound:
        bound = all(delta["base"].get(key) == delta["candidate"].get(key)
                    for key in ("root", "target", "parser_fingerprint"))
    if not bound:
        gaps.append("stale-callers schema or base/candidate snapshot binding unavailable or mismatched")
    targets = impact.get("targets", []) if valid_impact else []
    by_id = {row.get("symbol_id"): row for row in targets}
    candidate = context.get("candidate") or {}
    located = valid_impact and all(impact.get(key) == candidate.get(key) and candidate.get(key)
                                  for key in ("root", "target"))
    changed, bound_targets = [], []
    hashes = ("body_hash", "interface_hash", "effects_hash")
    for row in delta.get("changed", []) if bound else ():
        symbol = row.get("symbol_id")
        if not symbol or not in_scope(row.get("file", symbol.split("::")[0]), paths):
            continue
        before, after, kind = row.get("old"), row.get("new"), row.get("change_kind")
        sides = [side for side in (before, after) if side is not None]
        valid = bool(sides) and all(isinstance(side, dict) and all(side.get(key) for key in hashes)
                                    for side in sides)
        if before and after:
            expected = next((name for key, name in zip(hashes[1:] + hashes[:1],
                             ("interface_changed", "effects_changed", "body_only"))
                             if before.get(key) != after.get(key)), None)
        else:
            expected = "added" if before is None else "removed"
        target = by_id.get(symbol)
        if target is not None:
            valid = valid and located and after is not None and all(target.get(key) == after[key] for key in hashes)
        if not valid or kind != expected:
            gaps.append(f"stale-callers digest binding or change_kind mismatched: {symbol}")
            continue
        changed.append(row)
        if target is not None:
            bound_targets.append(target)
    unbound = [row.get("symbol_id", "?") for row in targets if row not in bound_targets]
    if unbound:
        gaps.append("edit-impact targets lack candidate delta digest binding: " + ", ".join(unbound))
    read_paths = {row.get("file") for row in bound_targets if row.get("file")}
    for target in bound_targets:
        for key in ("callers", "callees", "second_hop"):
            read_paths.update(row["file"] for row in target.get(key, {}).get("listed", []) if row.get("file"))
    if bound:
        # GREEN is an editing boundary, not an exclusion from validation reads.
        for key in ("edit_impact", "validation_impact", "do_not_touch"):
            read_paths.update(row["file"] for row in delta.get(key, {}).get("listed", []) if row.get("file"))
    return {
        "available": bool(bound_targets),
        "max_callers": max((row.get("callers", {}).get("total", 0) for row in bound_targets), default=0),
        "interface_changed": sorted(row["symbol_id"] for row in changed if row["change_kind"] == "interface_changed"),
        "effects_changed": sorted(row["symbol_id"] for row in changed if row["change_kind"] == "effects_changed"),
        "changed": changed, "read_scope": sorted(read_paths), "gaps": list(dict.fromkeys(gaps)),
        "graph": {
            "freshness_basis": {"impact": (impact or {}).get("freshness_basis"), "delta": delta.get("freshness_basis")},
            "history": {row["symbol_id"]: row.get("recent_changes", []) for row in targets if row.get("symbol_id")},
            "targets": targets, "delta": delta,
        },
    }


def specialist_obligations(roster: list[str], context: dict, scope_id: str,
                           map_signals: dict, gaps: list[str]) -> list[dict]:
    """Expand the existing catalog only; keep one obligation per member/scope."""
    entries = {row["id"]: row for row in context.get("catalog", {}).get("entries", [])}
    obligations: dict[tuple[str, str], dict] = {}

    def excluded(identity, scope):
        if identity in {"senior-review:code-auditor", "senior-review:local-correctness-auditor",
                        "senior-review:local-concurrency-auditor", "senior-review:premise-auditor"}:
            return False
        decisions = [row for row in context.get("applicability", [])
                     if isinstance(row, dict) and row.get("specialist_id") == identity
                     and row.get("scope_id") == scope]
        return len(decisions) == 1 and bool(context.get("candidate")) and all(
            row.get("status") == "not-applicable" and row.get("candidate") == context["candidate"]
            and isinstance(row.get("evidence"), list) and row["evidence"]
            and all(isinstance(item, dict) and item.get("path") and item.get("reason")
                    for item in row["evidence"]) for row in decisions)

    def add(identity, scope, evidence, trail=(), *, allow_exclusion=False):
        if (not isinstance(identity, str) or not identity or not isinstance(scope, str) or not scope
                or not isinstance(evidence, list) or not evidence
                or any(not isinstance(item, (str, dict)) or not item for item in evidence)):
            raise ValueError("specialist obligations require specialist_id, scope_id and evidence")
        if identity in trail:
            raise ValueError("cyclic specialist composition: " + identity)
        entry = entries.get(identity)
        if entry is not None and allow_exclusion and excluded(identity, scope):
            return
        if entry is not None and "members" in entry:
            if not entry["members"]:
                raise ValueError("empty specialist composition: " + identity)
            for member in entry["members"]:
                add(member, scope, evidence, (*trail, identity), allow_exclusion=allow_exclusion)
            if entry.get("kind") != "method-binding":
                return
        if entries and entry is None:
            gaps.append("specialist absent from supplied catalog: " + identity)
        key = identity, scope
        record = obligations.setdefault(key, {"specialist_id": identity, "scope_id": scope, "evidence": []})
        for item in evidence:
            if item not in record["evidence"]:
                record["evidence"].append(item)

    methods = {row.get("dimension"): row["id"] for row in entries.values()
               if row.get("kind") == "method-binding"}
    # Calls without prepared context keep the historical roster-only shape.
    for role in (roster if context else ()):
        identity = methods.get(role.partition("#")[2], role) if "#" in role else role
        # Missing catalog metadata is not permission to shrink the required set.
        # Keep the unresolved identity so composition fails before dispatch.
        add(identity, scope_id, [{"source": "computed-roster", "role": role}], allow_exclusion=True)
    if entries:
        code = entries.get("senior-review:code-auditor", {})
        if "senior-review:code-auditor" in roster and code.get("members"):
            for identity in CODE_FLOOR:
                if identity in entries and excluded(identity, scope_id):
                    continue
                if identity not in entries:
                    gaps.append("canonical code floor missing from specialist catalog: " + identity)
                add(identity, scope_id, [{"source": "code-review-floor",
                                          "reason": "no evidenced candidate/scope exclusion"}], allow_exclusion=True)
    elif context:
        gaps.append("specialist catalog unavailable; existing roster floor remains required")
    for item in context.get("required_specialists", []):
        add(item.get("specialist_id"), item.get("scope_id"), item.get("evidence"))
    for key in ("requirements", "sources", "configurations"):
        for item in context.get(key, []):
            for identity in item.get("specialist_ids", []):
                add(identity, item.get("scope_id", scope_id), [{"source": key, **item}])
    for row in map_signals["changed"]:
        if row["change_kind"] in {"interface_changed", "effects_changed"}:
            add("senior-review:api-contract-auditor", scope_id, [{
                "source": "stale-callers.changed", "symbol_id": row["symbol_id"],
                "change_kind": row["change_kind"], "old": row["old"], "new": row["new"],
                "reason": "changed callable contract requires validation at its callers",
            }])
    return list(obligations.values())


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
            kind: str = "changeset", review_id: str | None = None, stage: str | None = None,
            *, context: dict | None = None) -> dict:
    if kind not in KINDS:
        raise ValueError(f"kind must be one of {', '.join(KINDS)}")
    context = context or {}
    basis = context.get("review_basis", "changeset" if kind == "changeset" else "claims")
    if basis not in {"changeset", "content", "claims"}:
        raise ValueError("review_basis must be changeset, content or claims")
    scope_id = context.get("scope_id") or review_id or "candidate"
    rows = numstat if numstat else numstat_from_diff(diff)
    if basis == "changeset":
        # Diff metadata keeps both names even when --numstat is supplied.
        old_paths = {row["path"]: row["old_path"] for row in numstat_from_diff(diff) if row.get("old_path")}
        rows = [{**row, **({"old_path": old_paths[row["path"]]} if row["path"] in old_paths else {})} for row in rows]
        known = {row["path"] for row in rows}
        rows += [{"path": item["path"], "added": len(item.get("text", "").splitlines()),
                  "removed": 0, "status": "untracked"}
                 for item in context.get("sources", [])
                 if item.get("status") == "untracked" and item.get("path") and item["path"] not in known]
    if basis == "content":
        paths = set(context.get("conclusion_paths", []))
        for key in ("inventory", "sources", "configurations"):
            paths.update(item["path"] for item in context.get(key, []) if item.get("path"))
        rows = [{"path": path, "added": 0, "removed": 0} for path in sorted(paths)]
    conclusion_paths = sorted(set(context.get("conclusion_paths", [])) | {row["path"] for row in rows}
                              | {row["old_path"] for row in rows if row.get("old_path")})
    kinds = {row["path"]: classify_path(row["path"]) for row in rows}
    production = [p for p, k in kinds.items() if k == "production"]
    modules = sorted({Path(p).parts[0] if len(Path(p).parts) > 1 else "." for p in production})
    languages = sorted({LANGUAGE_BY_SUFFIX[Path(p).suffix] for p in production if Path(p).suffix in LANGUAGE_BY_SUFFIX})
    lines = sum((row["added"] or 0) + (row["removed"] or 0) for row in rows)
    interfaces = interface_changes(diff) if basis == "changeset" else []
    map_signals = impact_signals(impact, context, conclusion_paths if basis == "changeset" else [])
    content = content_signals(diff) if basis != "content" else {name: False for name in SIGNAL_PATTERNS}
    text = "\n".join(item.get("text", "") for key in ("requirements", "sources", "configurations")
                     for item in context.get(key, []))
    for name, pattern in SIGNAL_PATTERNS.items():
        content[name] = content[name] or bool(pattern.search(text))
    changed_paths = [row["path"] for row in rows if row["path"] in production
                     and (basis == "content" or row.get("old_path") or row.get("status") == "untracked"
                          or row["added"] or row["removed"] or row["added"] is None)]
    changed_paths += [row["old_path"] for row in rows if row.get("old_path") and classify_path(row["old_path"]) == "production"]
    for name, pattern in SIGNAL_PATHS.items():
        content[name] = content[name] or any(pattern.search(path) for path in changed_paths)
    signals = {
        "files": len(rows),
        "production_files": len(production),
        "lines": lines,
        "modules": modules,
        "languages": languages,
        "symbols": touched_symbols(diff) if basis == "changeset" else [],
        "interface_changed": sorted(set(interfaces) | set(map_signals["interface_changed"])),
        "effects_changed": map_signals["effects_changed"],
        "max_callers": map_signals["max_callers"],
        "sensitive_paths": sorted(p for p in set(production + changed_paths) if SENSITIVE_PATH.search(p)),
        "manifest": sorted(p for p, k in kinds.items() if k == "manifest"),
        "contract": sorted(p for p, k in kinds.items() if k == "contract"),
        "content": content,
        "applicability": {name: "yes" if present else "unknown" for name, present in content.items()},
        "map_available": map_signals["available"],
    }
    gaps = map_signals["gaps"] + evidence_gaps({key: context.get(key, []) for key in
                                               ("inventory", "sources", "configurations", "requirements")}, "context")
    if basis == "content" and not context.get("inventory"):
        gaps.append("content inventory unavailable or empty; explicit target paths remain in scope")
    if not all(content.values()):
        gaps.append("unmatched content signals have unknown applicability; preparation must ground skip decisions")

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
    obligation_roles = list(roster)
    if shape == "light" and kind == "changeset":
        # The one discovery job retains applicable domain checks after splitting
        # its former generalist. This never widens the dispatch count or tier.
        obligation_roles += signal_roles(signals, kind, obligation_roles)
        if signals["sensitive_paths"] and "senior-review:security-auditor" not in obligation_roles:
            obligation_roles.append("senior-review:security-auditor")
    required = specialist_obligations(obligation_roles, context, scope_id, map_signals, gaps)
    if shape == "light" and required:
        advice.append("required specialist obligations must fit the single discovery; otherwise review-branch is required")
    if not reasons:
        reasons.append("no raising signal")
    review = {} if review_id is None else {"id": review_id, "stage": stage or shape}
    return {
        **review,
        "schema": SCHEMA,
        "shape": shape,
        "kind": kind,
        "review_basis": basis,
        "tier": tier,
        "reasons": reasons,
        "roster": roster,
        "support": list(LARGE_SUPPORT if tier == "large" and kind == "changeset" else SUPPORT),
        "verification": VERIFICATION[tier],
        "blind_derivation": tier in ("medium", "large"),
        "critic": tier == "large",
        "signals": signals,
        "required_specialists": required,
        "jobs": [],
        "grounding": {
            "scope_id": scope_id, "conclusion_paths": conclusion_paths,
            **{side: context[side] for side in ("base", "candidate") if context.get(side)},
            "changes": rows if basis == "changeset" else [],
            "read_scope": sorted(set(conclusion_paths) | set(context.get("read_scope", [])) | set(map_signals["read_scope"])),
            "requirements": context.get("requirements", []), "graph": map_signals["graph"],
            "applicability": context.get("applicability", []),
        },
        "gaps": list(dict.fromkeys(gaps)),
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
    compute_parser.add_argument("--context", help="prepared review basis, scope, snapshot locators and evidence JSON")
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
        context = json.loads(Path(args.context).read_text(encoding="utf-8")) if args.context else None
        result = compute(args.shape, diff, numstat, impact, args.deeper, args.kind, args.review_id, args.stage, context=context)
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
