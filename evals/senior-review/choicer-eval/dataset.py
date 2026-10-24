"""Read-only, standard-library extraction of the Choicer pilot's source evidence.

This module does not write files, check out revisions, or import model runtimes.
The caller owns persistence under choicer-eval and keeps labels out of requests.
"""

from __future__ import annotations

import ast
import fnmatch
import hashlib
import re
import subprocess
import textwrap
import tomllib
from pathlib import Path


SPEC = "docs/superpowers/specs/2026-10-19-graph-grounded-economy-routing-design.md"
DISPATCH = "plugins/daodan/workflows/review-branch.toml"
DIMENSION_SOURCE = (
    "plugins/senior-review/skills/review-method/references/team-review.md"
)
NON_REVIEW_DISPATCH = {
    "codebase-map:map-analyst",
    "codebase-map:semantic-interconnect-mapper",
}
DIMENSION_MAPPING = {
    "architecture": "senior-review:code-auditor",
    "data-integrity": "senior-review:data-integrity-auditor",
    "distributed-flow": "senior-review:distributed-flow-auditor",
    "documentation": "senior-review:cleanup-auditor",
    "hygiene": "senior-review:cleanup-auditor",
    "logic-integrity": "senior-review:logic-integrity-auditor",
    "premise": "senior-review:premise-auditor",
    "resource": "senior-review:resource-lifecycle-auditor",
    "resource-lifecycle": "senior-review:resource-lifecycle-auditor",
    "security": "senior-review:security-auditor",
    "temporal": "senior-review:temporal-resilience-auditor",
    "temporal-resilience": "senior-review:temporal-resilience-auditor",
    "ui": "senior-review:ui-race-auditor",
}
PROTOCOL = {
    "version": "choicer-pilot-source-v1",
    "case_order": "Lexicographic case-directory order, opaque IDs C01..C11.",
    "history_rule": (
        "For fix-history cases, git diff --no-ext-diff --no-textconv --no-renames "
        "--unified=3 REVIEW FIX, restricted to the case's explicit paths. "
        "Each unified block becomes one hunk containing only the OLD side "
        "(unchanged context and removed lines). No fixed lines, commit messages "
        "or labels enter model state. Added-only blocks retain their old context. "
        "Empty old-side blocks are omitted and recorded. Later fixes localize "
        "these retrospective inputs; this is not a prospective routing sample."
    ),
    "updater_rule": (
        "The case explicitly permits 936ba644~1..936ba644. Use the full diff "
        "alternative, including its docs, tests and configuration. Each unified "
        "block contains only the NEW side, which is the buggy reviewed revision."
    ),
    "synthetic_rule": (
        "Each verbatim fenced buggy source file is one contiguous introduced "
        "block, including its source-path comment. Do not invent companion "
        "files or missing model/schema declarations."
    ),
    "credential_rule": (
        "No diff is supplied. Read complete alive_agent.py and "
        "middleware/heartbeat_monitor.py at a0bb4f10. Split all top-level "
        "declarations and class members by Python AST source ranges. Attach "
        "intervening lines, imports, class headers and comments to the following "
        "declaration; append trailing source to the final declaration. Functions "
        "remain complete and decorators remain attached. No method is selected "
        "using the precision oracle or case narrative. This case is unlabeled."
    ),
    "line_coordinates": (
        "start_line and end_line are 1-based in the reviewed source blob. "
        "Hunk text has no diff prefix; no cross-hunk source rewriting occurs."
    ),
    "symbol_cards": (
        "No case supplies a symbol card. All symbol_cards are empty; no inferred "
        "cards or undocumented one-hop context are synthesized."
    ),
    "labels": (
        "Union roles from Expected dimension cells, dropping parenthetical "
        "qualifiers and deduplicating roles. No Expected dimension table means "
        "unlabeled, not a negative example. Labels are case-level only."
    ),
    "threshold": "noul P(true) >= 0.5 fixed a priori; full curve is descriptive.",
    "leakage_boundary": (
        "Only hunk id, path, source line coordinates, source text and supplied "
        "symbol_cards are model-state fields. source_case, labels, revisions, "
        "case Markdown, provenance and anomalies are scorer-side metadata."
    ),
}


def _sha(data: bytes | str) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _read(path: Path) -> str:
    """Preserve source line endings so extracted prompt bytes are verifiable."""
    return path.read_bytes().decode("utf-8-sig")


def _source(path: Path, repo: Path) -> dict:
    return {
        "path": path.relative_to(repo).as_posix(),
        "sha256": _sha(path.read_bytes()),
    }


def _git(root: Path, *args: str) -> bytes:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode:
        message = result.stderr.decode("utf-8", errors="replace").strip()
        raise ValueError(f"Read-only git {' '.join(args)} failed: {message}")
    return result.stdout


def _revision(root: Path, rev: str) -> str:
    return _git(root, "rev-parse", "--verify", f"{rev}^{{commit}}").decode().strip()


def _frontmatter_description(text: str) -> tuple[str, str, int]:
    """Parse the repository's restricted YAML description scalar, fail closed.

    All current role descriptions are folded block scalars. This parser also
    accepts literal block scalars and plain one-line scalars; unsupported YAML
    quoting/anchors are rejected instead of being guessed at.
    """
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        raise ValueError("Role has no YAML frontmatter")
    end = next(
        (i for i, line in enumerate(lines[1:], 1) if line.strip() == "---"),
        None,
    )
    if end is None:
        raise ValueError("Role has unterminated YAML frontmatter")
    for index in range(1, end):
        match = re.fullmatch(r"description:\s*(.*?)\s*", lines[index].rstrip())
        if not match:
            continue
        indicator = match.group(1)
        if indicator in {">", ">-", ">+", "|", "|-", "|+"}:
            stop = index + 1
            while stop < end and (
                lines[stop].startswith((" ", "\t")) or not lines[stop].strip()
            ):
                stop += 1
            raw = "".join(lines[index + 1 : stop])
            unindented = textwrap.dedent(raw).strip()
            if indicator.startswith(">"):
                # Preserve paragraph boundaries while implementing YAML folding.
                description = "\n".join(
                    " ".join(line.strip() for line in paragraph.splitlines())
                    for paragraph in re.split(r"\r?\n\s*\r?\n", unindented)
                )
            else:
                description = unindented
            return description, raw, index + 2
        if not indicator or indicator[0] in "'\"&*!{[":
            raise ValueError("Unsupported YAML description syntax")
        return indicator, indicator, index + 1
    raise ValueError("Role has no description")


def _trigger(description: str, marker: str) -> str | None:
    markers = list(re.finditer(r"(?<!\w)(?:DO NOT TRIGGER WHEN|TRIGGER WHEN):", description))
    matches = [entry for entry in markers if entry.group() == marker + ":"]
    if not matches:
        return None
    if len(matches) != 1:
        raise ValueError(f"Description repeats {marker}")
    match = matches[0]
    stop = next((entry.start() for entry in markers if entry.start() > match.start()), len(description))
    return description[match.end() : stop].strip()


def extract_catalog(repo: Path | str) -> dict:
    """Return all parsed role descriptions plus the evidenced reviewer subset."""
    repo = Path(repo).resolve()
    dispatch_path = repo / DISPATCH
    dispatch = tomllib.loads(_read(dispatch_path))["dispatch"]["roles"]
    dispatched = {role.replace("/", ":", 1) for role in dispatch}
    reviewers = dispatched - NON_REVIEW_DISPATCH
    roles = []
    sources = [_source(dispatch_path, repo)]
    for path in sorted((repo / "plugins").glob("*/roles/*.md")):
        plugin = path.parent.parent.name
        manifest_path = path.parent.parent / "plugin.toml"
        manifest = tomllib.loads(_read(manifest_path))
        name = path.stem
        if name not in manifest.get("components", {}).get("roles", []):
            raise ValueError(f"Unregistered source role: {path}")
        text = _read(path)
        description, raw, start = _frontmatter_description(text)
        declared = re.search(r"(?m)^name:\s*(\S+)\s*$", text)
        if not declared or declared.group(1) != name:
            raise ValueError(f"Role filename/name mismatch: {path}")
        role_id = f"{plugin}:{name}"
        trigger = _trigger(description, "TRIGGER WHEN")
        negative = _trigger(description, "DO NOT TRIGGER WHEN")
        roles.append({
            "id": role_id,
            "source": path.relative_to(repo).as_posix(),
            "source_sha256": _sha(path.read_bytes()),
            "description": description,
            "description_raw": raw,
            "description_start_line": start,
            "trigger_when": trigger,
            "do_not_trigger_when": negative,
            "is_reviewer": role_id in reviewers,
            "is_review_dispatch": role_id in dispatched,
            "plugin_version": manifest["version"],
            "manifest_source": _source(manifest_path, repo),
        })
    ids = {role["id"] for role in roles}
    if reviewers - ids:
        raise ValueError(f"Dispatch roles absent from catalog: {sorted(reviewers - ids)}")
    missing_negative = [role["id"] for role in roles if role["is_reviewer"] and role["do_not_trigger_when"] is None]
    missing_positive = [role["id"] for role in roles if role["is_reviewer"] and role["trigger_when"] is None]
    return {
        "schema": "choicer-eval/catalog-v1",
        "roles": roles,
        "reviewer_ids": sorted(reviewers),
        "role_count": len(roles),
        "reviewer_count": len(reviewers),
        "reviewer_selection": {
            "rule": "review-branch dispatch roles, excluding its two codebase-map evidence producers",
            "source": _source(dispatch_path, repo),
            "excluded_producers": sorted(NON_REVIEW_DISPATCH),
            "dimension_source": _source(repo / DIMENSION_SOURCE, repo),
            "why_not_all_roles": "Writers, maintainers, map producers and protocol workers are not reviewer lenses.",
        },
        "sources": sources,
        "anomalies": [
            {"kind": "missing_negative_trigger", "roles": missing_negative, "policy": "Preserve null; do not invent a negative criterion."},
            {"kind": "missing_positive_trigger", "roles": missing_positive, "policy": "Preserve null; do not invent a positive criterion."},
            {"kind": "spec_role_count", "observed": len(reviewers), "claim": "approximately 20 or 20+"},
            {
                "kind": "current_security_trigger_differs_from_proposed_spec",
                "policy": "Use actual role frontmatter, never the replacement proposed in spec section 3.1.",
            },
        ],
    }


def extract_prompts(repo: Path | str) -> dict:
    """Extract the three fenced prompt bodies verbatim, including line endings."""
    repo = Path(repo).resolve()
    path = repo / SPEC
    text = _read(path)
    result = {}
    for name in ("TASK_TIER_CHOICER", "REVIEWER_CHOICER", "RETRY_TRIAGER"):
        pattern = rf"(?m)^#### Prompt [123]: `{name}`[^\r\n]*\r?\n(?:\r?\n)*```text\r?\n(.*?)^```[ \t]*\r?$"
        match = re.search(pattern, text, flags=re.DOTALL | re.MULTILINE)
        if not match:
            raise ValueError(f"Missing exact prompt block {name}")
        prompt = match.group(1)
        result[name] = {
            "text": prompt,
            "sha256": _sha(prompt),
            "source": SPEC,
            "source_sha256": _sha(path.read_bytes()),
            "start_line": text.count("\n", 0, match.start(1)) + 1,
            "end_line": text.count("\n", 0, match.end(1)),
        }
    return result


def _labels(text: str) -> tuple[str, list[str], list[str]]:
    lines = text.splitlines()
    header = next((i for i, line in enumerate(lines) if line.startswith("|") and "Expected dimension" in line), None)
    if header is None:
        return "unlabeled", [], []
    dimensions = set()
    for line in lines[header + 2 :]:
        if not line.startswith("|"):
            break
        cell = line.strip("|").split("|")[-1].strip()
        for dimension in re.sub(r"\([^)]*\)", "", cell).split("/"):
            dimension = dimension.strip().lower()
            if dimension not in DIMENSION_MAPPING:
                raise ValueError(f"Unmapped expected dimension: {dimension}")
            dimensions.add(dimension)
    return "labeled", sorted({DIMENSION_MAPPING[d] for d in dimensions}), sorted(dimensions)


def _hunk(path: str, start: int, text: str, **extra: object) -> dict:
    return {
        "path": path,
        "start_line": start,
        "end_line": start + len(text.splitlines()) - 1,
        "text": text,
        "sha256": _sha(text),
        "symbol_cards": [],
        **extra,
    }


def _synthetic(text: str) -> tuple[list[dict], dict]:
    section = re.search(r"(?ms)^## Buggy code\s*\r?\n(.*?)(?=^## |\Z)", text)
    if not section:
        raise ValueError("Synthetic case has no Buggy code section")
    blocks = re.findall(r"(?ms)^```(?:python|typescript)\r?\n(.*?)^```\s*$", section.group(1))
    hunks = []
    for block in blocks:
        first_line = block.splitlines()[0]
        path_match = re.fullmatch(r"(?:#|//)\s+([\w./-]+)", first_line)
        if not path_match:
            raise ValueError("Synthetic source does not supply an explicit file path")
        hunks.append(_hunk(path_match.group(1), 1, block, extraction="verbatim-inline-added-block"))
    if not hunks:
        raise ValueError("Synthetic case has no source fences")
    return hunks, {"kind": "inline", "source_file_count": len(hunks)}


def _diff_blocks(diff: str, side: str) -> list[tuple[int, str]]:
    blocks = []
    start = None
    content = []
    for line in diff.splitlines(keepends=True):
        match = re.match(r"^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@", line)
        if match:
            if start is not None:
                blocks.append((start, "".join(content)))
            start = int(match.group(1 if side == "old" else 2))
            content = []
        elif start is not None and line.startswith((" ", "-" if side == "old" else "+")):
            content.append(line[1:])
        elif line.startswith("\\ No newline at end of file") and content:
            content[-1] = content[-1].rstrip("\r\n")
    if start is not None:
        blocks.append((start, "".join(content)))
    return blocks


def _history(root: Path, text: str, slug: str) -> tuple[list[dict], dict]:
    review_match = re.search(r"\*\*Review rev:\*\*\s*`([^`]+)`", text)
    fix_match = re.search(r"\*\*Fix rev \(do not show the reviewer\):\*\*\s*`([^`]+)`", text)
    if not review_match or not fix_match:
        raise ValueError(f"Missing source revisions for {slug}")
    review_ref, fix_ref = review_match.group(1), fix_match.group(1)
    review = _revision(root, review_ref)
    fix = _revision(root, fix_ref)
    source_side = "new" if slug == "jupiter-updater" else "old"
    before = _revision(root, review_ref + "~1") if source_side == "new" else review
    after = review if source_side == "new" else fix
    changed = _git(root, "diff", "--no-ext-diff", "--no-renames", "--name-only", "-z", before, after).decode("utf-8").split("\0")
    changed = sorted(p for p in changed if p)
    if source_side == "new":
        scope = changed
        scope_rule = "Explicit full review-commit diff alternative in the case."
    else:
        scope_line = re.search(r"(?m)^- \*\*Review scope:\*\*(.*)$", text)
        if not scope_line:
            raise ValueError(f"Missing explicit review scope for {slug}")
        scope = re.findall(r"`([^`]+)`", scope_line.group(1))
        scope_rule = "Explicit backticked scope paths in the case."
        if slug == "jupiter-cache-convergence":
            scope.append("jupiter-core/jupiter_core/notifiers/notifier_market_state.py")
            scope_rule += " Resolve 'market-state notifier path the diff touches' to notifier_market_state.py."
    paths = [p for p in changed if any(fnmatch.fnmatchcase(p, pattern) for pattern in scope)]
    if not paths:
        raise ValueError(f"No changed source path matches {slug}: {scope}")
    hunks, blobs, omissions = [], [], []
    for path in paths:
        diff_bytes = _git(root, "diff", "--no-ext-diff", "--no-textconv", "--no-renames", "--unified=3", before, after, "--", path)
        # The chosen side is always exactly the reviewed revision.
        blob = _git(root, "show", f"{review}:{path}")
        lines = blob.decode("utf-8").splitlines(keepends=True)
        blocks = _diff_blocks(diff_bytes.decode("utf-8"), source_side)
        for block_index, (start, block) in enumerate(blocks, 1):
            if not block:
                omissions.append({"path": path, "block": block_index, "reason": "selected diff side has zero source lines"})
                continue
            actual = "".join(lines[start - 1 : start - 1 + len(block.splitlines())])
            if actual != block:
                raise ValueError(f"Diff source integrity mismatch at {review}:{path}:{start}")
            hunks.append(_hunk(path, start, block, extraction=f"unified-3-{source_side}-side", source_block=block_index))
        blobs.append({
            "path": path,
            "revision": review,
            "blob_id": _git(root, "rev-parse", f"{review}:{path}").decode().strip(),
            "sha256": _sha(blob),
            "diff_sha256": _sha(diff_bytes),
        })
    return hunks, {
        "kind": "git-history",
        "source_repo": str(root),
        "review_ref": review_ref,
        "review_revision": review,
        "fix_ref": fix_ref,
        "fix_revision": fix,
        "diff_before": before,
        "diff_after": after,
        "selected_side": source_side,
        "scope": scope,
        "scope_rule": scope_rule,
        "source_blobs": blobs,
        "omitted_empty_blocks": omissions,
    }


def _python_blocks(path: str, source: str) -> list[dict]:
    """Partition a whole Python module; never discard non-function source."""
    tree = ast.parse(source, filename=path)
    lines = source.splitlines(keepends=True)
    ranges = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            nodes = node.body
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            nodes = [node]
        else:
            continue
        for child in nodes:
            if not isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            start = min([child.lineno] + [dec.lineno for dec in child.decorator_list])
            ranges.append((start, child.end_lineno))
    ranges.sort()
    hunks, cursor = [], 1
    for start, end in ranges:
        hunks.append(_hunk(
            path,
            cursor,
            "".join(lines[cursor - 1 : end]),
            extraction="whole-module-complete-declaration-with-prefix",
            declaration_start_line=start,
        ))
        cursor = end + 1
    if cursor <= len(lines):
        if hunks:
            last = hunks[-1]
            hunks[-1] = _hunk(
                path,
                last["start_line"],
                last["text"] + "".join(lines[cursor - 1 :]),
                extraction=last["extraction"],
                declaration_start_line=last["declaration_start_line"],
            )
        else:
            hunks.append(_hunk(path, 1, source, extraction="whole-module-no-declarations"))
    if "".join(h["text"] for h in hunks) != source:
        raise ValueError(f"Whole-module partition lost source: {path}")
    return hunks


def _credential(root: Path, text: str) -> tuple[list[dict], dict]:
    match = re.search(r"(?m)^review_rev:\s*(\S+)", text)
    if not match:
        raise ValueError("Precision case has no review_rev")
    revision = _revision(root, match.group(1))
    paths = [
        "jupiter-core/jupiter_core/agents/alive_agent.py",
        "jupiter-core/jupiter_core/middleware/heartbeat_monitor.py",
    ]
    hunks, blobs = [], []
    for path in paths:
        blob = _git(root, "show", f"{revision}:{path}")
        hunks.extend(_python_blocks(path, blob.decode("utf-8")))
        blobs.append({
            "path": path,
            "revision": revision,
            "blob_id": _git(root, "rev-parse", f"{revision}:{path}").decode().strip(),
            "sha256": _sha(blob),
        })
    return hunks, {
        "kind": "git-whole-scope",
        "source_repo": str(root),
        "review_ref": match.group(1),
        "review_revision": revision,
        "scope_rule": "The complete agent heartbeat and middleware heartbeat/auto-registration modules named by the case scope.",
        "scope": paths,
        "source_blobs": blobs,
        "no_diff_available": True,
    }


def materialize_cases(repo: Path | str, jupiter_root: Path | str) -> dict:
    """Materialize all case inputs without mutating either repository."""
    repo, root = Path(repo).resolve(), Path(jupiter_root).resolve()
    case_paths = sorted((repo / "evals/senior-review/cases").glob("*/case.md"))
    if len(case_paths) != 11:
        raise ValueError(f"Expected the pinned 11-case pilot, found {len(case_paths)}")
    cases, anomalies = [], []
    for index, case_path in enumerate(case_paths, 1):
        text = _read(case_path)
        slug = case_path.parent.name
        label_status, roles, dimensions = _labels(text)
        if slug.startswith("synthetic-"):
            hunks, provenance = _synthetic(text)
        elif slug == "jupiter-credential-refill":
            hunks, provenance = _credential(root, text)
            anomalies.append({
                "case_id": f"C{index:02}",
                "kind": "missing_reviewer_ground_truth",
                "detail": "Precision-only must_not_report case has no Expected dimension table; exclude from recall, false activations and calibration.",
            })
        else:
            hunks, provenance = _history(root, text, slug)
        for hunk_index, hunk in enumerate(hunks, 1):
            hunk["id"] = f"H{hunk_index}"
        if not hunks:
            raise ValueError(f"No source materialized for {slug}")
        cases.append({
            "id": f"C{index:02}",
            "source_case": slug,
            "label_status": label_status,
            "expected_roles": roles,
            "expected_dimensions": dimensions,
            "hunks": hunks,
            "provenance": {"case_source": _source(case_path, repo), **provenance},
        })
        if slug == "synthetic-payment-double-insert":
            anomalies.append({
                "case_id": f"C{index:02}",
                "kind": "unspecified_companion_model",
                "detail": "Case requests payments/models.py with no unique constraint but supplies no model source. Only verbatim service code is materialized; no schema is invented.",
            })
    anomalies.extend([
        {"kind": "no_supplied_symbol_cards", "detail": "All 11 case inputs omit symbol cards because the source cases supply none."},
        {"kind": "no_positive_premise_label", "detail": "The labeled case tables contain no premise expected role; premise recall is unmeasurable in this pilot."},
        {
            "kind": "case_labels_are_not_exhaustive_trigger_labels",
            "detail": "Expected dimension attributes known defects. Treat non-listed roles as negatives only for the requested pilot proxy; a selected role may be relevant without owning a listed defect.",
        },
        {
            "kind": "proposed_router_not_in_working_tree",
            "observed": not (repo / "plugins/model-routing/skills/model-routing/scripts/tier_router.py").exists(),
            "detail": "The spec prompt is the baseline definition; do not describe it as a verified live implementation.",
        },
    ])
    return {
        "schema": "choicer-eval/cases-v1",
        "cases": cases,
        "dimension_mapping": DIMENSION_MAPPING,
        "dimension_mapping_provenance": {
            "source": _source(repo / DIMENSION_SOURCE, repo),
            "documentation_and_hygiene": _source(repo / "plugins/senior-review/roles/cleanup-auditor.md", repo),
            "rule": "Architecture follows the method's code-auditor row; UI follows UI race conditions; documentation/hygiene use the codebase-hygiene owner, whose remit explicitly includes stale docs.",
        },
        "protocol": PROTOCOL,
        "anomalies": anomalies,
    }
