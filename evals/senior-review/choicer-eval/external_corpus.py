"""Stage 1 external corpus sourcing for the Gutsy reviewer-routing benchmark.

This script only inventories public sources and builds an unadjudicated candidate
pool. It never calls the local model and never freezes benchmark labels.

Actions:
  inventory  Fetch public source metadata and write source_inventory.json.
  pool       Fetch selected public rows and write candidate_pool.json.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import time
import urllib.error
import urllib.request

HERE = Path(__file__).resolve().parent
ROWS = "https://datasets-server.huggingface.co/rows"
HF_API = "https://huggingface.co/api/datasets"
MAX_INPUT_CHARS = 5600

ROLES = [
    "security-auditor",
    "data-integrity-auditor",
    "temporal-resilience-auditor",
    "resource-lifecycle-auditor",
    "ui-race-auditor",
    "distributed-flow-auditor",
    "logic-integrity-auditor",
    "cleanup-auditor",
]

SIGNALS = {
    "security-auditor": ["security", "vulnerab", "cve-", "xss", "injection", "authentication", "authorization", "permission", "credential", "password", "token leak", "path traversal", "sandbox escape"],
    "data-integrity-auditor": ["database", "cache", "stale", "persist", "transaction", "migration", "duplicate", "upsert", "consistency", "orm", "query result", "storage"],
    "temporal-resilience-auditor": ["timeout", "retry", "retries", "hang", "stuck", "blocking", "deadlock", "infinite loop", "scheduler", "polling", "background job", "blocked forever", "never returns"],
    "resource-lifecycle-auditor": ["leak", "connection pool", "pool", "connection", "socket", "file handle", "descriptor", "lock", "mutex", "semaphore", "acquire", "release", "thread pool", "not closed", "not released", "unclosed", "cleanup of resource", "resource exhaustion"],
    "ui-race-auditor": ["render", "layout", "scroll", "focus", "click", "component", "dom", "browser", "dialog", "tooltip", "displayed", "visible", "stale ui"],
    "distributed-flow-auditor": ["grpc", "rpc", "http", "api", "client", "server", "request", "response", "network", "protocol", "endpoint", "transport", "message", "stream", "channel", "webhook", "message queue", "protobuf", "serialization contract", "client-server"],
    "logic-integrity-auditor": ["incorrect", "wrong", "invalid", "should return", "expected", "invariant", "state transition", "idempot", "ordering", "does not compute", "fails to"],
    "cleanup-auditor": ["dead code", "unused", "deprecated", "obsolete", "remove unused", "cleanup", "clean up", "documentation mismatch", "outdated documentation"],
}

SOURCES = [
    {
        "id": "swe-bench-verified",
        "name": "SWE-bench Verified",
        "kind": "huggingface",
        "dataset": "princeton-nlp/SWE-bench_Verified",
        "url": "https://huggingface.co/datasets/princeton-nlp/SWE-bench_Verified",
        "access": "datasets-server rows API, default/test",
        "label_signal": "Human-validated issue/PR pair; problem_statement and FAIL_TO_PASS tests are adjudication evidence only.",
        "planned_use": "Python candidates for logic, data, temporal, resource and distributed lenses.",
        "limits": "Python only. Issue text, test names and titles must not enter model jobs.",
    },
    {
        "id": "multi-swe-bench",
        "name": "Multi-SWE-bench",
        "kind": "huggingface",
        "dataset": "ByteDance-Seed/Multi-SWE-bench",
        "url": "https://huggingface.co/datasets/ByteDance-Seed/Multi-SWE-bench",
        "access": "per-repository JSONL files under resolve/main",
        "label_signal": "Expert-curated issue/PR pairs; PR title, resolved issues and fail-to-pass tests are adjudication evidence only.",
        "planned_use": "TypeScript, JavaScript, Go, Java and Rust candidates, especially UI and distributed cases.",
        "limits": "Large aggregate dataset; fetch only selected repository files. Per-repository licenses apply.",
    },
    {
        "id": "devign",
        "name": "Devign",
        "kind": "huggingface",
        "dataset": "DetectVul/devign",
        "url": "https://huggingface.co/datasets/DetectVul/devign",
        "access": "datasets-server rows API, default/test",
        "label_signal": "Dataset-native vulnerable/non-vulnerable function target.",
        "planned_use": "Gold security positives and security-only explicit negatives.",
        "limits": "C/C++ only. A non-vulnerable target labels only the security lens.",
    },
    {
        "id": "cvefixes",
        "name": "CVEfixes v1.0.8",
        "kind": "zenodo",
        "url": "https://doi.org/10.5281/zenodo.13118970",
        "access": "Zenodo record 13118970",
        "label_signal": "CVE/CWE provenance at commit, file and method level.",
        "planned_use": "Later targeted security provenance if a selective query path is justified.",
        "limits": "Zenodo ZIP is 12,708,711,268 bytes; not downloaded in Stage 1.",
    },
    {
        "id": "hapy-bug",
        "name": "HaPy-Bug",
        "kind": "github",
        "url": "https://github.com/ncusi/HaPy-Bug",
        "access": "public Git repository",
        "label_signal": "793 Python bug-fix commits annotated by three experts.",
        "planned_use": "Small high-confidence development pool and label-protocol checks.",
        "limits": "Python only; annotations describe changes, not reviewer applicability directly.",
    },
    {
        "id": "commitbench",
        "name": "CommitBench",
        "kind": "huggingface",
        "dataset": "Maxscha/commitbench",
        "url": "https://huggingface.co/datasets/Maxscha/commitbench",
        "access": "datasets-server rows API, default/test",
        "label_signal": "Real diffs plus commit messages as weak evidence.",
        "planned_use": "Backup candidate generation only.",
        "limits": "Dataset license is CC BY-NC 4.0; excluded from any commercial path and from gold labels.",
    },
]

MULTI_FILES = [
    ("ts/mui__material-ui_dataset.jsonl", "development"),
    ("js/axios__axios_dataset.jsonl", "development"),
    ("go/grpc__grpc-go_dataset.jsonl", "development"),
    ("java/fasterxml__jackson-databind_dataset.jsonl", "development"),
    ("ts/vuejs__core_dataset.jsonl", "verification"),
    ("js/sveltejs__svelte_dataset.jsonl", "verification"),
    ("java/apache__dubbo_dataset.jsonl", "verification"),
    ("rust/tokio-rs__tokio_dataset.jsonl", "verification"),
]


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def save(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def fetch_json(url: str):
    """Fetch JSON, retrying only transient gateway/rate-limit responses."""
    last_error = None
    for delay in (0, 3, 10, 30):
        if delay:
            time.sleep(delay)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "daodan-choicer-eval/1.0"})
            with urllib.request.urlopen(req, timeout=120) as response:
                raw = response.read()
            return json.loads(raw.decode("utf-8")), raw
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code not in {429, 502, 503, 504}:
                raise
    raise last_error


def parse_old_side(patch: str) -> list[dict]:
    """Extract context plus removed lines from a unified diff, grouped by hunk."""
    hunks = []
    path = None
    start = 0
    lines: list[str] = []
    header = re.compile(r"^@@ -(\d+)(?:,\d+)? \+\d+(?:,\d+)? @@")

    def flush():
        if path and lines:
            text = "\n".join(lines) + "\n"
            hunks.append({"id": f"H{len(hunks) + 1}", "path": path, "start_line": start,
                          "text": text, "sha256": digest(text.encode())})

    for line in patch.splitlines():
        if line.startswith("diff --git "):
            flush()
            lines = []
            parts = line.split(" b/", 1)
            path = parts[1] if len(parts) == 2 else None
        elif line.startswith("--- "):
            continue
        elif line.startswith("+++ "):
            if line[4:] != "/dev/null":
                path = line[6:] if line[4:].startswith("b/") else line[4:]
        elif (match := header.match(line)):
            flush()
            lines = []
            start = int(match.group(1))
        elif line.startswith("-") and not line.startswith("---"):
            lines.append(line[1:])
        elif line.startswith(" "):
            lines.append(line[1:])
    flush()
    return hunks


def signal_scores(text: str) -> dict[str, int]:
    low = text.lower()
    return {role: sum(term in low for term in SIGNALS[role]) for role in ROLES
            if sum(term in low for term in SIGNALS[role])}


def signal_roles(text: str) -> list[str]:
    hits = sorted(signal_scores(text).items(), key=lambda item: (-item[1], ROLES.index(item[0])))
    strong = [role for role, score in hits if score >= 2]
    return strong[:4] if strong else [role for role, _ in hits[:1]]


def split_for_repo(repo: str, dev_repos: set[str], ver_repos: set[str]) -> str:
    if repo in dev_repos:
        return "development"
    if repo in ver_repos:
        return "verification"
    return "development" if int(digest(repo.encode())[:2], 16) % 2 == 0 else "verification"


def make_candidate(cid: str, source: str, instance: str, repo: str, revision: str, language: str,
                   split: str, label_status: str, positives: list[str], negatives: list[str],
                   evidence: dict, hunks: list[dict], provenance: dict,
                   scores: dict[str, int] | None = None) -> dict | None:
    total = sum(len(h["text"]) for h in hunks)
    if not hunks or total < 20:
        return None
    language = {"py": "python", "js": "javascript", "ts": "typescript"}.get(language, language)
    candidate = {
        "id": cid,
        "source": source,
        "source_instance_id": instance,
        "repo": repo,
        "revision": revision,
        "language": language,
        "split_proposal": split,
        "label_status": label_status,
        "candidate_positive_roles": positives,
        "candidate_negative_roles": negatives,
        "candidate_signal_scores": scores or {},
        "label_evidence": evidence,
        "input": {"kind": "function" if source == "devign" else "old-side-diff",
                  "hunks": hunks, "chars": total, "sha256": digest("".join(h["text"] for h in hunks).encode())},
        "provenance": provenance,
    }
    if total > MAX_INPUT_CHARS:
        candidate["exclusion"] = f"input is {total} chars; Stage 1 limit is {MAX_INPUT_CHARS}"
        return candidate
    candidate["exclusion"] = None
    return candidate


def inventory(out: Path) -> None:
    sources = []
    for source in SOURCES:
        item = dict(source)
        if source["kind"] == "huggingface":
            data, raw = fetch_json(f"{HF_API}/{source['dataset']}")
            item["live_metadata"] = {
                "sha": data.get("sha"), "last_modified": data.get("lastModified"),
                "downloads": data.get("downloads"), "used_storage_bytes": data.get("usedStorage"),
                "license": (data.get("cardData") or {}).get("license"),
                "siblings": [s.get("rfilename") for s in data.get("siblings", [])][:20],
                "response_sha256": digest(raw),
            }
        elif source["kind"] == "zenodo":
            data, raw = fetch_json("https://zenodo.org/api/records/13118970")
            item["live_metadata"] = {
                "doi": data.get("doi"), "version": (data.get("metadata") or {}).get("version"),
                "license": ((data.get("metadata") or {}).get("license") or {}).get("id"),
                "files": [{"key": f.get("key"), "size": f.get("size"), "checksum": f.get("checksum")} for f in data.get("files", [])],
                "response_sha256": digest(raw),
            }
        sources.append(item)
    save(out / "source_inventory.json", {
        "schema": "choicer-eval/external-sources-v1",
        "fetched_at_unix": int(time.time()),
        "sources": sources,
        "rules": [
            "No bulk CVEfixes download in Stage 1.",
            "CommitBench is backup only because its dataset license is CC BY-NC 4.0.",
            "Label evidence stays in provenance and never enters model jobs.",
            "Unknown lenses are omitted, never converted to negatives.",
        ],
    })
    print(json.dumps({"sources": len(sources), "out": str(out)}, indent=2))


def fetch_rows(dataset: str, split: str, offset: int, length: int) -> list[dict]:
    url = f"{ROWS}?dataset={urllib.request.quote(dataset, safe='')}&config=default&split={split}&offset={offset}&length={length}"
    data, _ = fetch_json(url)
    return [row["row"] for row in data.get("rows", [])]


def swe_candidates(start: int) -> tuple[list[dict], int]:
    candidates = []
    seen_repos: dict[str, int] = {}
    rows = []
    for offset in range(0, 500, 100):
        rows.extend(fetch_rows("princeton-nlp/SWE-bench_Verified", "test", offset, 100))
    dev = {"astropy/astropy", "django/django", "matplotlib/matplotlib", "scikit-learn/scikit-learn", "sympy/sympy", "psf/requests"}
    ver = {"pydata/xarray", "pytest-dev/pytest", "pylint-dev/pylint", "mwaskom/seaborn", "sphinx-doc/sphinx", "pallets/flask"}
    ranked = []
    for row in rows:
        evidence_text = row["problem_statement"] + "\n" + row["FAIL_TO_PASS"] + "\n" + row["patch"]
        roles = signal_roles(evidence_text)
        if roles:
            ranked.append((len(roles), row, roles))
    ranked.sort(key=lambda item: (-item[0], item[1]["instance_id"]))
    for _, row, roles in ranked:
        repo = row["repo"]
        if seen_repos.get(repo, 0) >= 3:
            continue
        hunks = parse_old_side(row["patch"])
        cand = make_candidate(
            f"X{start + len(candidates):03}", "swe-bench-verified", row["instance_id"], repo,
            row["base_commit"], "python", split_for_repo(repo, dev, ver), "silver",
            roles, [], {
                "problem_statement_sha256": digest(row["problem_statement"].encode()),
                "problem_statement_excerpt": row["problem_statement"][:2000],
                "fail_to_pass": row["FAIL_TO_PASS"],
                "patch_paths": sorted({h["path"] for h in hunks}),
            }, hunks, {
                "dataset": "princeton-nlp/SWE-bench_Verified", "dataset_revision": "c104f840cc67f8b6eec6f759ebc8b2693d585d4a",
                "url": f"https://github.com/{repo}/commit/{row['base_commit']}",
                "license": "not stated in the Hugging Face API response; upstream project licenses apply",
            }, signal_scores(row["problem_statement"] + "\n" + row["FAIL_TO_PASS"] + "\n" + row["patch"]))
        if cand and not cand["exclusion"]:
            candidates.append(cand)
            seen_repos[repo] = seen_repos.get(repo, 0) + 1
        if len(candidates) >= 24:
            break
    return candidates, start + len(candidates)


def multi_candidates(start: int) -> tuple[list[dict], int]:
    candidates = []
    for rel, split in MULTI_FILES:
        url = f"https://huggingface.co/datasets/ByteDance-Seed/Multi-SWE-bench/resolve/main/{rel}"
        req = urllib.request.Request(url, headers={"User-Agent": "daodan-choicer-eval/1.0"})
        scanned = 0
        selected = 0
        with urllib.request.urlopen(req, timeout=120) as response:
            for raw in response:
                if selected >= 3 or scanned >= 200:
                    break
                scanned += 1
                row = json.loads(raw.decode("utf-8"))
                issues = row.get("resolved_issues") or []
                evidence_text = " ".join([
                    row.get("title") or "",
                    " ".join((issue.get("title") or "") + " " + (issue.get("body") or "") for issue in issues),
                    json.dumps(row.get("f2p_tests") or {}),
                    row.get("fix_patch") or "",
                ])
                roles = signal_roles(evidence_text)
                if not roles:
                    continue
                hunks = parse_old_side(row.get("fix_patch") or "")
                repo = f"{row.get('org')}/{row.get('repo')}"
                cand = make_candidate(
                    f"X{start + len(candidates):03}", "multi-swe-bench", f"{repo}-{row.get('instance_id')}",
                    repo, (row.get("base") or {}).get("sha"), rel.split("/")[0], split, "silver",
                    roles, [], {
                        "pr_title": row.get("title"),
                        "resolved_issues": [{"number": i.get("number"), "title": i.get("title"),
                                             "body_sha256": digest((i.get("body") or "").encode()),
                                             "body_excerpt": (i.get("body") or "")[:1500]} for i in issues],
                        "fail_to_pass": row.get("f2p_tests"),
                        "patch_paths": sorted({h["path"] for h in hunks}),
                    }, hunks, {
                        "dataset": "ByteDance-Seed/Multi-SWE-bench", "dataset_revision": "56ff018c04a38e27ada1e9d0a6d5839a51f88f0d",
                        "file": rel, "scanned_rows": scanned,
                        "license": "other in the Hugging Face API response; upstream project licenses apply",
                    }, signal_scores(evidence_text))
                if cand and not cand["exclusion"]:
                    candidates.append(cand)
                    selected += 1
    return candidates, start + len(candidates)


def devign_candidates(start: int) -> tuple[list[dict], int]:
    candidates = []
    wanted = {("FFmpeg", True): 3, ("FFmpeg", False): 3, ("qemu", True): 3, ("qemu", False): 3}
    counts = {key: 0 for key in wanted}
    for offset in range(0, 600, 100):
        if all(counts[key] >= wanted[key] for key in wanted):
            break
        for row in fetch_rows("DetectVul/devign", "test", offset, 100):
            key = (row["project"], bool(row["target"]))
            if key not in wanted or counts[key] >= wanted[key]:
                continue
            text = row["func"]
            hunks = [{"id": "H1", "path": f"{row['project']}/function-{row['id']}.c", "start_line": 1,
                      "text": text, "sha256": digest(text.encode())}]
            cand = make_candidate(
                f"X{start + len(candidates):03}", "devign", str(row["id"]), row["project"],
                row["commit_id"], "c", "development" if row["project"] == "FFmpeg" else "verification",
                "gold", ["security-auditor"] if row["target"] else [], [] if row["target"] else ["security-auditor"],
                {"dataset_target": bool(row["target"]), "vulnerable_line_count": len((row.get("vul_lines") or {}).get("code", []))},
                hunks, {
                    "dataset": "DetectVul/devign", "dataset_revision": "see source_inventory.json",
                    "commit_id": row["commit_id"], "license": "not stated in the Hugging Face API response; upstream project licenses apply",
                }, {"security-auditor": 1} if row["target"] else {})
            if cand and not cand["exclusion"]:
                candidates.append(cand)
                counts[key] += 1
    return candidates, start + len(candidates)


def commitbench_candidates(start: int) -> tuple[list[dict], int]:
    """Backup candidates for families that issue corpora rarely name: cleanup and distribution."""
    candidates = []
    seen: dict[str, int] = {}
    target = {"cleanup-auditor", "distributed-flow-auditor", "resource-lifecycle-auditor"}
    counts = {role: 0 for role in target}
    languages = {"py", "js", "ts", "java", "go"}
    for offset in range(0, 5000, 100):
        if len(candidates) >= 12 or all(count >= 4 for count in counts.values()):
            break
        for row in fetch_rows("Maxscha/commitbench", "test", offset, 100):
            if len(candidates) >= 12 or all(count >= 4 for count in counts.values()):
                break
            if row.get("diff_languages") not in languages:
                continue
            evidence_text = row["message"] + "\n" + row["diff"]
            roles = [role for role in signal_roles(evidence_text) if role in target and counts[role] < 4]
            if not roles:
                continue
            repo = row["project"]
            if seen.get(repo, 0) >= 1:
                continue
            hunks = parse_old_side(row["diff"])
            cand = make_candidate(
                f"X{start + len(candidates):03}", "commitbench", row["hash"], repo,
                row["hash"], row["diff_languages"], split_for_repo(repo, set(), set()), "silver",
                roles, [], {
                    "commit_message": row["message"],
                    "patch_paths": sorted({h["path"] for h in hunks}),
                }, hunks, {
                    "dataset": "Maxscha/commitbench", "dataset_revision": "1500792cd6998308da046ba72b688156b2ffa471",
                    "license": "CC BY-NC 4.0; backup candidate generation only, no commercial path and no gold labels",
                }, signal_scores(evidence_text))
            if cand and not cand["exclusion"]:
                candidates.append(cand)
                seen[repo] = 1
                for role in roles:
                    counts[role] += 1
    return candidates, start + len(candidates)


def pool(out: Path) -> None:
    candidates = []
    for builder in (swe_candidates, multi_candidates, devign_candidates, commitbench_candidates):
        found, _ = builder(len(candidates) + 1)
        candidates.extend(found)
    projects = sorted({c["repo"] for c in candidates})
    assignments = {role: sum(role in c["candidate_positive_roles"] for c in candidates) for role in ROLES}
    save(out / "candidate_pool.json", {
        "schema": "choicer-eval/external-candidate-pool-v1",
        "status": "candidate_unadjudicated_except_devign_security",
        "rules": [
            "Candidate positive roles are source-signal proposals, not frozen labels, except Devign security.",
            "Unknown lenses are omitted and must never be scored as negatives.",
            "Issue text, CVE identifiers, commit messages, test names and titles stay in label_evidence only.",
            "No model calls are authorized by this file.",
        ],
        "counts": {"candidates": len(candidates), "projects": len(projects),
                   "projects_list": projects, "candidate_positive_assignments": assignments},
        "candidates": candidates,
    })
    print(json.dumps({"candidates": len(candidates), "projects": len(projects), "assignments": assignments}, indent=2))


def evidence_summary(candidate: dict) -> str:
    evidence = candidate["label_evidence"]
    if "commit_message" in evidence:
        text = evidence["commit_message"]
    elif "problem_statement_excerpt" in evidence:
        text = evidence["problem_statement_excerpt"]
    elif "resolved_issues" in evidence:
        text = "; ".join(issue.get("title") or "" for issue in evidence["resolved_issues"])
        if evidence.get("pr_title"):
            text = f"{evidence['pr_title']}; {text}"
    elif "dataset_target" in evidence:
        text = f"Devign dataset target={evidence['dataset_target']}"
    else:
        text = json.dumps(evidence)[:300]
    return " ".join(text.split())[:300]


def lens_decision(candidate: dict, role: str) -> dict:
    """Stage 2 decision state. Only Devign security is already gold."""
    if candidate["source"] == "devign":
        if role != "security-auditor":
            return {"status": "unknown", "reason": "Devign labels only the security lens."}
        if "security-auditor" in candidate["candidate_positive_roles"]:
            return {"status": "gold_positive", "reason": "Dataset-native vulnerable target."}
        return {"status": "gold_negative", "reason": "Dataset-native non-vulnerable target."}
    score = candidate.get("candidate_signal_scores", {}).get(role, 0)
    if role in candidate["candidate_positive_roles"]:
        status = "proposed_positive_silver" if score >= 2 else "proposed_positive_weak"
        return {"status": status, "reason": f"Source signal score {score}; adjudicate from label evidence."}
    if score == 0:
        return {"status": "candidate_negative_from_absence",
                "reason": "No source signal; not usable as an explicit negative until adjudicated."}
    return {"status": "unknown_below_threshold", "reason": f"Source signal score {score} below the proposal threshold."}


def label_packet(out: Path) -> None:
    pool_data = load(out / "candidate_pool.json")
    candidates = pool_data["candidates"]
    packet_candidates = []
    counts: dict[str, dict[str, int]] = {role: {} for role in ROLES}
    for cand in candidates:
        decisions = {role: lens_decision(cand, role) for role in ROLES}
        for role, decision in decisions.items():
            counts[role][decision["status"]] = counts[role].get(decision["status"], 0) + 1
        packet_candidates.append({
            "id": cand["id"], "source": cand["source"], "repo": cand["repo"],
            "language": cand["language"], "split_proposal": cand["split_proposal"],
            "label_status": cand["label_status"], "evidence_summary": evidence_summary(cand),
            "decisions": decisions,
        })
    save(out / "label_packet.json", {
        "schema": "choicer-eval/external-label-packet-v1",
        "status": "stage2_adjudication_packet_not_frozen_labels",
        "rules": [
            "Only gold_positive and gold_negative may enter a frozen benchmark without adjudication.",
            "proposed_positive_silver and proposed_positive_weak require evidence adjudication.",
            "candidate_negative_from_absence is not an explicit negative until adjudicated.",
            "Unknown lenses remain omitted from scoring.",
        ],
        "counts_by_role": counts,
        "candidates": packet_candidates,
    })
    lines = ["# External corpus Stage 2 label packet", "",
             "Only Devign security decisions are gold. Every other status is an adjudication state, not a frozen label.", ""]
    for role in ROLES:
        lines += [f"## {role}", "", "| Status | Count |", "| --- | ---: |"]
        for status, count in sorted(counts[role].items()):
            lines.append(f"| {status} | {count} |")
        lines += ["", "Proposed or gold positives:", ""]
        for cand in packet_candidates:
            if cand["decisions"][role]["status"] in {"gold_positive", "proposed_positive_silver", "proposed_positive_weak"}:
                lines.append(f"- {cand['id']} ({cand['source']}, {cand['repo']}, {cand['split_proposal']}): "
                             f"{cand['decisions'][role]['status']}; {cand['evidence_summary']}")
        lines.append("")
    (out / "label_packet.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"candidates": len(candidates), "counts_by_role": counts}, indent=2))


def evidence_text(candidate: dict) -> str:
    """External label evidence only. Patch/code text is deliberately excluded."""
    evidence = candidate["label_evidence"]
    parts = []
    if "problem_statement_excerpt" in evidence:
        parts.append(evidence["problem_statement_excerpt"])
    if "commit_message" in evidence:
        parts.append(evidence["commit_message"])
    if "pr_title" in evidence:
        parts.append(evidence["pr_title"] or "")
    for issue in evidence.get("resolved_issues", []):
        parts.append(issue.get("title") or "")
        parts.append(issue.get("body_excerpt") or "")
    if "fail_to_pass" in evidence:
        parts.append(json.dumps(evidence["fail_to_pass"]))
    return "\n".join(parts)


STRONG_RESOURCE_PHRASES = ["memory leak", "resource leak", "file descriptor leak", "connection pool",
                           "too many open files", "file handle", "not closed", "unclosed file"]


def has_strong_resource(text: str) -> bool:
    low = text.lower()
    return any(term in low for term in STRONG_RESOURCE_PHRASES)


def adjudicate_candidate(candidate: dict) -> dict:
    """Conservative Stage 2 adjudication from external evidence, not patch keywords."""
    if candidate["source"] == "devign":
        positive = ["security-auditor"] if "security-auditor" in candidate["candidate_positive_roles"] else []
        negative = [] if positive else ["security-auditor"]
        return {"id": candidate["id"], "label_status": "adjudicated_gold",
                "positive_roles": positive, "negative_roles": negative,
                "unknown_roles": [role for role in ROLES if role not in positive + negative],
                "rationale": "Devign dataset-native security target."}
    scores = signal_scores(evidence_text(candidate))
    positive = []
    for role in candidate["candidate_positive_roles"]:
        if scores.get(role, 0) >= 2 and candidate["source"] in {"swe-bench-verified", "multi-swe-bench"}:
            positive.append(role)
    if candidate["source"] == "commitbench":
        message = candidate["label_evidence"].get("commit_message", "").lower()
        strong_cleanup = ["remove unused", "removed unused", "dead code", "remove deprecated",
                          "removed deprecated", "remove obsolete", "removed obsolete"]
        if "cleanup-auditor" in candidate["candidate_positive_roles"] and any(term in message for term in strong_cleanup):
            positive.append("cleanup-auditor")
    if ("resource-lifecycle-auditor" in candidate["candidate_positive_roles"]
            and candidate["source"] in {"swe-bench-verified", "multi-swe-bench", "commitbench"}
            and has_strong_resource(evidence_text(candidate))):
        positive.append("resource-lifecycle-auditor")
    positive = sorted(set(positive), key=ROLES.index)
    negative = []
    if positive and candidate["input"]["chars"] <= 2800:
        negative = [role for role in ROLES if role not in positive and scores.get(role, 0) == 0]
    unknown = [role for role in ROLES if role not in positive + negative]
    status = "adjudicated_silver" if positive else "needs_manual_adjudication"
    rationale = ("Accepted positives require at least two external-evidence signal terms. "
                 "Explicit negatives require an accepted positive scope and no external-evidence signal for that lens.")
    return {"id": candidate["id"], "label_status": status, "positive_roles": positive,
            "negative_roles": negative, "unknown_roles": unknown, "rationale": rationale,
            "evidence_signal_scores": scores}


def adjudicate(out: Path) -> None:
    pool_data = load(out / "candidate_pool.json")
    candidates = pool_data["candidates"]
    by_id = {cand["id"]: cand for cand in candidates}
    adjudicated = [adjudicate_candidate(cand) for cand in candidates]
    positives = {role: sum(role in item["positive_roles"] for item in adjudicated) for role in ROLES}
    negatives = {role: sum(role in item["negative_roles"] for item in adjudicated) for role in ROLES}
    positive_projects = {role: len({by_id[item["id"]]["repo"] for item in adjudicated if role in item["positive_roles"]})
                         for role in ROLES}
    gate = {
        "positives_at_least_6_per_lens": all(count >= 6 for count in positives.values()),
        "explicit_negatives_at_least_24": sum(negatives.values()) >= 24,
        "positive_projects_at_least_2_per_lens": all(count >= 2 for count in positive_projects.values()),
        "adjudicated_candidates_at_least_48": sum(item["label_status"] != "needs_manual_adjudication" for item in adjudicated) >= 48,
    }
    save(out / "adjudicated_candidates.json", {
        "schema": "choicer-eval/external-adjudication-v1",
        "status": "stage2_conservative_adjudication_not_frozen",
        "gate": gate,
        "gate_passed": all(gate.values()),
        "positive_counts": positives,
        "negative_counts": negatives,
        "positive_projects": positive_projects,
        "candidates": adjudicated,
    })
    lines = ["# External corpus Stage 2 adjudication", "",
             f"Gate passed: {all(gate.values())}. This file is not a frozen benchmark.", "",
             "| Lens | Positives | Explicit negatives | Positive projects |", "| --- | ---: | ---: | ---: |"]
    for role in ROLES:
        lines.append(f"| {role} | {positives[role]} | {negatives[role]} | {positive_projects[role]} |")
    lines += ["", "## Gate", ""]
    for name, passed in gate.items():
        lines.append(f"- {name}: {'pass' if passed else 'fail'}")
    lines += ["", "## Accepted positives", ""]
    for item in adjudicated:
        if item["positive_roles"]:
            cand = by_id[item["id"]]
            lines.append(f"- {item['id']} ({cand['source']}, {cand['repo']}, {cand['split_proposal']}): "
                         f"{', '.join(item['positive_roles'])}; {evidence_summary(cand)}")
    (out / "ADJUDICATION.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"gate_passed": all(gate.values()), "gate": gate,
                      "positives": positives, "negatives": negatives}, indent=2))


TARGET_FILL_ROLES = ["temporal-resilience-auditor", "resource-lifecycle-auditor", "cleanup-auditor",
                     "data-integrity-auditor", "ui-race-auditor"]


def strong_roles(scores: dict[str, int], roles: list[str] | None = None) -> list[str]:
    wanted = roles or ROLES
    return [role for role in wanted if scores.get(role, 0) >= 2]


def fill(out: Path) -> None:
    """Targeted fill from external evidence only; never from patch keywords."""
    pool_data = load(out / "candidate_pool.json")
    existing = {(cand["source"], cand["source_instance_id"]) for cand in pool_data["candidates"]}
    start = max(int(cand["id"][1:]) for cand in pool_data["candidates"]) + 1
    selected: list[dict] = []
    selected_keys: set[tuple[str, str]] = set()
    repo_counts: dict[str, int] = {}
    role_counts = {role: 0 for role in TARGET_FILL_ROLES}

    def try_add(cand: dict | None, roles: list[str]) -> None:
        if not cand or cand["exclusion"]:
            return
        key = (cand["source"], cand["source_instance_id"])
        if key in existing or key in selected_keys:
            return
        if repo_counts.get(cand["repo"], 0) >= 2:
            return
        selected.append(cand)
        selected_keys.add(key)
        repo_counts[cand["repo"]] = repo_counts.get(cand["repo"], 0) + 1
        for role in roles:
            if role in role_counts:
                role_counts[role] += 1

    def needs_more() -> bool:
        return any(role_counts[role] < 6 for role in TARGET_FILL_ROLES)

    def write_fill(status: str, error: str | None = None) -> None:
        adjudicated_local = [adjudicate_candidate(cand) for cand in selected]
        save(out / "fill_candidates.json", {
            "schema": "choicer-eval/external-fill-v1",
            "status": status,
            "target_roles": TARGET_FILL_ROLES,
            "error": error,
            "counts": {"candidates": len(selected), "role_proposals": role_counts,
                       "adjudicated_positive_counts": {role: sum(role in item["positive_roles"] for item in adjudicated_local) for role in ROLES}},
            "candidates": selected,
            "adjudicated": adjudicated_local,
        })

    # SWE-bench Verified: issue text and failing tests only.
    rows = []
    for offset in range(0, 500, 100):
        rows.extend(fetch_rows("princeton-nlp/SWE-bench_Verified", "test", offset, 100))
    ranked = []
    for row in rows:
        scores = signal_scores(row["problem_statement"] + "\n" + row["FAIL_TO_PASS"])
        roles = strong_roles(scores, TARGET_FILL_ROLES)
        if roles:
            ranked.append((sum(scores[role] for role in roles), row, roles, scores))
    ranked.sort(key=lambda item: (-item[0], item[1]["instance_id"]))
    dev = {"astropy/astropy", "django/django", "matplotlib/matplotlib", "scikit-learn/scikit-learn", "sympy/sympy", "psf/requests"}
    ver = {"pydata/xarray", "pytest-dev/pytest", "pylint-dev/pylint", "mwaskom/seaborn", "sphinx-doc/sphinx", "pallets/flask"}
    for _, row, roles, scores in ranked:
        if not needs_more():
            break
        hunks = parse_old_side(row["patch"])
        cand = make_candidate(
            f"X{start + len(selected):03}", "swe-bench-verified", row["instance_id"], row["repo"],
            row["base_commit"], "python", split_for_repo(row["repo"], dev, ver), "silver",
            roles, [], {
                "problem_statement_sha256": digest(row["problem_statement"].encode()),
                "problem_statement_excerpt": row["problem_statement"][:2000],
                "fail_to_pass": row["FAIL_TO_PASS"],
                "patch_paths": sorted({h["path"] for h in hunks}),
                "fill_basis": "external evidence only: problem statement and FAIL_TO_PASS",
            }, hunks, {
                "dataset": "princeton-nlp/SWE-bench_Verified", "dataset_revision": "c104f840cc67f8b6eec6f759ebc8b2693d585d4a",
                "license": "not stated in the Hugging Face API response; upstream project licenses apply",
            }, scores)
        try_add(cand, roles)

    # Strong resource phrases can be decisive even when only one signal term appears.
    for row in rows:
        if role_counts["resource-lifecycle-auditor"] >= 6:
            break
        text = row["problem_statement"] + "\n" + row["FAIL_TO_PASS"]
        if not has_strong_resource(text):
            continue
        hunks = parse_old_side(row["patch"])
        cand = make_candidate(
            f"X{start + len(selected):03}", "swe-bench-verified", row["instance_id"], row["repo"],
            row["base_commit"], "python", split_for_repo(row["repo"], dev, ver), "silver",
            ["resource-lifecycle-auditor"], [], {
                "problem_statement_sha256": digest(row["problem_statement"].encode()),
                "problem_statement_excerpt": row["problem_statement"][:2000],
                "fail_to_pass": row["FAIL_TO_PASS"],
                "patch_paths": sorted({h["path"] for h in hunks}),
                "fill_basis": "external evidence only: strong resource phrase in problem statement or FAIL_TO_PASS",
            }, hunks, {
                "dataset": "princeton-nlp/SWE-bench_Verified", "dataset_revision": "c104f840cc67f8b6eec6f759ebc8b2693d585d4a",
                "license": "not stated in the Hugging Face API response; upstream project licenses apply",
            }, signal_scores(text))
        try_add(cand, ["resource-lifecycle-auditor"])

    # Multi-SWE-bench: PR titles, resolved issues and failing tests only.
    for rel, split in MULTI_FILES:
        if not needs_more():
            break
        url = f"https://huggingface.co/datasets/ByteDance-Seed/Multi-SWE-bench/resolve/main/{rel}"
        req = urllib.request.Request(url, headers={"User-Agent": "daodan-choicer-eval/1.0"})
        scanned = 0
        with urllib.request.urlopen(req, timeout=120) as response:
            for raw in response:
                if not needs_more() or scanned >= 300:
                    break
                scanned += 1
                row = json.loads(raw.decode("utf-8"))
                issues = row.get("resolved_issues") or []
                text = " ".join([row.get("title") or "",
                                 " ".join((issue.get("title") or "") + " " + (issue.get("body") or "") for issue in issues),
                                 json.dumps(row.get("f2p_tests") or {})])
                scores = signal_scores(text)
                roles = strong_roles(scores, TARGET_FILL_ROLES)
                if not roles:
                    continue
                hunks = parse_old_side(row.get("fix_patch") or "")
                repo = f"{row.get('org')}/{row.get('repo')}"
                cand = make_candidate(
                    f"X{start + len(selected):03}", "multi-swe-bench", f"{repo}-{row.get('instance_id')}",
                    repo, (row.get("base") or {}).get("sha"), rel.split("/")[0], split, "silver",
                    roles, [], {
                        "pr_title": row.get("title"),
                        "resolved_issues": [{"number": i.get("number"), "title": i.get("title"),
                                             "body_sha256": digest((i.get("body") or "").encode()),
                                             "body_excerpt": (i.get("body") or "")[:1500]} for i in issues],
                        "fail_to_pass": row.get("f2p_tests"),
                        "patch_paths": sorted({h["path"] for h in hunks}),
                        "fill_basis": "external evidence only: PR title, resolved issues and failing tests",
                    }, hunks, {
                        "dataset": "ByteDance-Seed/Multi-SWE-bench", "dataset_revision": "56ff018c04a38e27ada1e9d0a6d5839a51f88f0d",
                        "file": rel, "scanned_rows": scanned,
                        "license": "other in the Hugging Face API response; upstream project licenses apply",
                    }, scores)
                try_add(cand, roles)

    write_fill("partial_before_commitbench")
    # CommitBench: commit message only, and only for cleanup/temporal/resource filling.
    commitbench_error = None
    if needs_more():
        try:
            for offset in range(0, 2000, 100):
                if not needs_more():
                    break
                for row in fetch_rows("Maxscha/commitbench", "test", offset, 100):
                    if not needs_more():
                        break
                    scores = signal_scores(row["message"])
                    roles = strong_roles(scores, TARGET_FILL_ROLES)
                    message = row["message"].lower()
                    if "cleanup-auditor" not in roles and any(term in message for term in
                                                             ["remove unused", "removed unused", "dead code", "remove deprecated", "removed deprecated"]):
                        roles.append("cleanup-auditor")
                    if "resource-lifecycle-auditor" not in roles and has_strong_resource(row["message"]):
                        roles.append("resource-lifecycle-auditor")
                    if not roles:
                        continue
                    hunks = parse_old_side(row["diff"])
                    cand = make_candidate(
                        f"X{start + len(selected):03}", "commitbench", row["hash"], row["project"],
                        row["hash"], row["diff_languages"], split_for_repo(row["project"], set(), set()), "silver",
                        roles, [], {
                            "commit_message": row["message"],
                            "patch_paths": sorted({h["path"] for h in hunks}),
                            "fill_basis": "external evidence only: commit message",
                        }, hunks, {
                            "dataset": "Maxscha/commitbench", "dataset_revision": "1500792cd6998308da046ba72b688156b2ffa471",
                            "license": "CC BY-NC 4.0; backup candidate generation only, no commercial path and no gold labels",
                        }, scores)
                    try_add(cand, roles)
        except urllib.error.HTTPError as exc:
            commitbench_error = f"CommitBench fill stopped after HTTP {exc.code}; SWE/Multi fill is preserved."
    write_fill("targeted_fill_from_external_evidence_only", commitbench_error)
    adjudicated = [adjudicate_candidate(cand) for cand in selected]
    print(json.dumps({"candidates": len(selected), "role_proposals": role_counts, "commitbench_error": commitbench_error,
                      "adjudicated_positive_counts": {role: sum(role in item["positive_roles"] for item in adjudicated) for role in ROLES}}, indent=2))


def select_freeze(candidates: list[dict], adjudicated: list[dict]) -> list[str]:
    """Down-select adjudicated candidates while preserving lens and split quotas."""
    by_id = {cand["id"]: cand for cand in candidates}
    adj = {item["id"]: item for item in adjudicated}
    eligible = [cand for cand in candidates
                if adj[cand["id"]]["label_status"] != "needs_manual_adjudication"
                and (adj[cand["id"]]["positive_roles"] or adj[cand["id"]]["negative_roles"])]
    selected: list[str] = []
    chosen: set[str] = set()

    def repo_count(repo: str) -> int:
        return sum(by_id[cid]["repo"] == repo for cid in selected)

    def add(cand: dict) -> None:
        if cand["id"] not in chosen:
            chosen.add(cand["id"])
            selected.append(cand["id"])

    def positives(role: str, split: str | None = None) -> int:
        return sum(role in adj[cid]["positive_roles"] and (split is None or by_id[cid]["split_proposal"] == split)
                   for cid in selected)

    scarce = {role for role in ROLES if sum(role in item["positive_roles"] for item in adjudicated) <= 8}
    # Per-lens split quotas first: 4 development and 2 verification positives.
    for role in sorted(ROLES, key=lambda r: sum(r in item["positive_roles"] for item in adjudicated)):
        for split, quota in (("development", 4), ("verification", 2)):
            while positives(role, split) < quota:
                options = [cand for cand in eligible
                           if cand["id"] not in chosen and cand["split_proposal"] == split
                           and role in adj[cand["id"]]["positive_roles"] and repo_count(cand["repo"]) < 4]
                if not options:
                    break
                options.sort(key=lambda cand: (repo_count(cand["repo"]),
                                               -len(set(adj[cand["id"]]["positive_roles"]) & scarce),
                                               -len(adj[cand["id"]]["positive_roles"]), cand["id"]))
                add(options[0])
    # Security-negative Devign cases give no-specialist coverage.
    for split in ("development", "verification"):
        negatives = [cand for cand in eligible
                     if cand["id"] not in chosen and cand["split_proposal"] == split
                     and not adj[cand["id"]]["positive_roles"] and adj[cand["id"]]["negative_roles"]]
        for cand in sorted(negatives, key=lambda c: c["id"])[:3]:
            add(cand)
    # Fill toward 52 without letting distributed-only cases dominate.
    while len(selected) < 52:
        options = [cand for cand in eligible if cand["id"] not in chosen and repo_count(cand["repo"]) < 4]
        if not options:
            break
        def fill_key(cand: dict):
            roles = adj[cand["id"]]["positive_roles"]
            distributed_only = roles == ["distributed-flow-auditor"] and positives("distributed-flow-auditor") >= 8
            return (distributed_only, repo_count(cand["repo"]),
                    -len(set(roles) & scarce), -len(roles), cand["id"])
        add(sorted(options, key=fill_key)[0])
    return selected


def freeze(out: Path, stage: Path) -> None:
    """Freeze a 48-60 case external benchmark from the adjudicated pool plus fill."""
    import gutsy_followup as followup

    pool_data = load(stage / "candidate_pool.json")
    fill_data = load(stage / "fill_candidates.json")
    candidates = pool_data["candidates"] + fill_data["candidates"]
    adjudicated = (load(stage / "adjudicated_candidates.json")["candidates"] + fill_data["adjudicated"])
    by_id = {cand["id"]: cand for cand in candidates}
    adj = {item["id"]: item for item in adjudicated}
    selected_ids = select_freeze(candidates, adjudicated)
    if not 48 <= len(selected_ids) <= 60:
        raise ValueError(f"Freeze selection has {len(selected_ids)} cases; expected 48 to 60")
    positives = {role: sum(role in adj[cid]["positive_roles"] for cid in selected_ids) for role in ROLES}
    negatives = {role: sum(role in adj[cid]["negative_roles"] for cid in selected_ids) for role in ROLES}
    projects = {role: len({by_id[cid]["repo"] for cid in selected_ids if role in adj[cid]["positive_roles"]}) for role in ROLES}
    gate = {"positives_at_least_6_per_lens": all(count >= 6 for count in positives.values()),
            "explicit_negatives_at_least_24": sum(negatives.values()) >= 24,
            "positive_projects_at_least_2_per_lens": all(count >= 2 for count in projects.values()),
            "cases_48_to_60": True}
    if not all(gate.values()):
        raise ValueError(f"Freeze gate failed: {gate}; positives={positives}; projects={projects}")
    out.mkdir(parents=True, exist_ok=False)
    values = followup.legacy_constants()
    roles = [role for role, _, _ in values["lenses"]]
    prompts = {
        "v2": {role: {"question": question, "options": [f"Yes: activate {role.split(':')[-1]}",
                                                        f"No: do not activate {role.split(':')[-1]}"]}
               for role, question, _ in values["lenses"]},
        "candidate": {followup.PREFIX + role: {"question": question, "options": ["Yes", "No"]}
                      for role, question in followup.NEW_QUESTIONS.items()},
    }
    ordered = sorted(selected_ids, key=lambda cid: (by_id[cid]["split_proposal"] != "development", by_id[cid]["source"], by_id[cid]["repo"], cid))
    cases, jobs, selection = [], [], []
    for index, cid in enumerate(ordered, 1):
        cand, item = by_id[cid], adj[cid]
        fid = f"F{index:02}"
        hunks = [{"id": hunk["id"], "path": hunk["path"], "start_line": hunk["start_line"],
                  "end_line": hunk["start_line"] + hunk["text"].count("\n"), "text": hunk["text"],
                  "sha256": hunk["sha256"]} for hunk in cand["input"]["hunks"]]
        cases.append({"id": fid, "source_candidate_id": cid, "source": cand["source"],
                      "split": cand["split_proposal"], "label_status": item["label_status"],
                      "expected_roles": [f"{followup.PREFIX}{role}" if not role.startswith(followup.PREFIX) else role for role in item["positive_roles"]],
                      "negative_roles": [f"{followup.PREFIX}{role}" if not role.startswith(followup.PREFIX) else role for role in item["negative_roles"]],
                      "label_rationale": item["rationale"],
                      "provenance": {**cand["provenance"], "repo": cand["repo"], "revision": cand["revision"],
                                     "source_candidate_id": cid, "evidence_summary": evidence_summary(cand)},
                      "hunks": hunks})
        selection.append({"id": fid, "source_candidate_id": cid, "repo": cand["repo"], "split": cand["split_proposal"],
                          "positive_roles": item["positive_roles"], "negative_roles": item["negative_roles"]})
        for window in followup.window_hunks(hunks):
            state = followup.window_state(fid, window)
            for variant in ("v2", "candidate"):
                for role in roles:
                    jobs.append({"case_id": fid, "mode": "windowed", "window": window, "variant": variant,
                                 "role": role, "state": state, **prompts[variant][role]})
    jobs.sort(key=lambda job: (job["case_id"] >= "F", job["case_id"], job["window"]["id"], job["variant"], job["role"]))
    # Verification cases were numbered after development cases; keep them last by split instead.
    dev_ids = {case["id"] for case in cases if case["split"] == "development"}
    jobs.sort(key=lambda job: (job["case_id"] not in dev_ids, job["case_id"], job["window"]["id"], job["variant"], job["role"]))
    for index, job in enumerate(jobs, 1):
        job["id"] = f"Q{index:04}"
    save(out / "selection.json", {"selected": selection, "gate": gate, "positives": positives,
                                  "negatives": negatives, "positive_projects": projects})
    save(out / "cases.json", cases)
    save(out / "jobs.json", jobs)
    save(out / "prompts.json", prompts)
    plan = {
        "status": "frozen", "roles": roles, "jobs": len(jobs), "cases": len(cases),
        "prefix_mode": "slot-restore",
        "prefix_mode_basis": "Slot restore adopted in runs/20261021-gutsy-followup-slot/COMPARISON.md. Compare only within one prefix mode.",
        "memory_limit_bytes": 1_000_000_000, "server_context_tokens": 1536,
        "selection": "exact generated A only; Z and invalid outputs never become No",
        "scope": "External corpus freeze from SWE-bench Verified, Multi-SWE-bench, Devign and CommitBench backup candidates; no production changes",
        "label_basis": "Conservative adjudication from external evidence only; Devign security is gold, other accepted positives are silver.",
        "splits": "development and verification split proposals preserved from candidate generation; verification locked at freeze",
        "inference_inputs": "opaque case ID, source path/range/text and frozen questions; no issue text, CVE IDs, commit messages, test names, titles or expected roles",
        "predeclared_success": "Report recall and explicit-negative activations by lens and split; no prompt tuning on verification outcomes",
        "stage_run": stage.relative_to(HERE).as_posix(),
        "hashes": {name: digest((out / name).read_bytes()) for name in ("cases.json", "jobs.json", "prompts.json")},
        "runner_sha256": digest((HERE / "gutsy_followup.py").read_bytes()),
        "freeze_runner_sha256": digest(Path(__file__).read_bytes()),
        "legacy_sha256": digest((HERE / "run_gutsy_v2_eval.py").read_bytes()),
    }
    save(out / "plan.json", plan)
    print(json.dumps({"cases": len(cases), "jobs": len(jobs), "gate": gate, "positives": positives}, indent=2))


def visibility_category(role: str, code_text: str) -> str:
    """First-pass code-visibility audit from the shown input only."""
    if role == "resource-lifecycle-auditor" and has_strong_resource(code_text):
        return "visible_signal_in_code"
    score = signal_scores(code_text).get(role, 0)
    if score >= 2:
        return "visible_signal_in_code"
    if score == 1:
        return "weak_signal_in_code"
    return "no_signal_in_code_external_only"


def audit_visibility(out: Path, stage: Path) -> None:
    """Audit development positives only: is the concern visible from shown code?"""
    cases = load(out / "cases.json")
    pool_data = load(stage / "candidate_pool.json")
    fill_data = load(stage / "fill_candidates.json")
    stage_candidates = {cand["id"]: cand for cand in pool_data["candidates"] + fill_data["candidates"]}
    rows = []
    counts: dict[str, dict[str, int]] = {role: {} for role in ROLES}
    for case in cases:
        if case["split"] != "development":
            continue
        cand = stage_candidates[case["source_candidate_id"]]
        code_text = "".join(hunk["text"] for hunk in case["hunks"])
        for full_role in case["expected_roles"]:
            role = full_role.split(":")[-1]
            category = visibility_category(role, code_text)
            counts[role][category] = counts[role].get(category, 0) + 1
            rows.append({"case_id": case["id"], "source_candidate_id": case["source_candidate_id"],
                         "source": case["source"], "repo": cand["repo"], "role": role,
                         "category": category, "code_signal_score": signal_scores(code_text).get(role, 0),
                         "evidence_signal_score": signal_scores(evidence_text(cand)).get(role, 0),
                         "evidence_summary": evidence_summary(cand)})
    save(out / "visibility_audit.json", {
        "schema": "choicer-eval/external-visibility-audit-v1",
        "scope": "development cases only; verification locked",
        "categories": {
            "visible_signal_in_code": "At least two code signal terms, or a strong resource phrase, in the shown input.",
            "weak_signal_in_code": "Exactly one code signal term in the shown input.",
            "no_signal_in_code_external_only": "No code signal term in the shown input; the label came from external evidence.",
        },
        "counts_by_role": counts,
        "rows": rows,
    })
    lines = ["# External corpus development visibility audit", "",
             "Development cases only. Verification remains locked.", "",
             "| Lens | Visible signal | Weak signal | External only |", "| --- | ---: | ---: | ---: |"]
    for role in ROLES:
        c = counts[role]
        lines.append(f"| {role} | {c.get('visible_signal_in_code', 0)} | {c.get('weak_signal_in_code', 0)} | {c.get('no_signal_in_code_external_only', 0)} |")
    lines += ["", "## External-only positives", ""]
    for row in rows:
        if row["category"] == "no_signal_in_code_external_only":
            lines.append(f"- {row['case_id']} ({row['source_candidate_id']}, {row['repo']}) {row['role']}: {row['evidence_summary']}")
    (out / "VISIBILITY_AUDIT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"rows": len(rows), "counts_by_role": counts}, indent=2))


RUBRIC = {
    "security-auditor": {
        "applies": "Controls access to accounts or private data, validates untrusted input, or handles credentials, secrets or sensitive output.",
        "excludes": "Pure internal computation, non-security hashing/IDs, or generic error handling without a trust boundary.",
    },
    "data-integrity-auditor": {
        "applies": "Reads, writes, invalidates or reconciles persisted records or cached copies of external state.",
        "excludes": "Temporary local dictionaries, sets or counters used only inside a computation.",
    },
    "temporal-resilience-auditor": {
        "applies": "Governs retries, timeouts, timers, polling, backoff, recovery after failure or visibility of background errors over time.",
        "excludes": "Merely using async syntax or converting a timestamp/date value.",
    },
    "resource-lifecycle-auditor": {
        "applies": "Acquires, retains or releases a lock, file, connection, subscription, worker or bounded resource slot across normal, error or cancel paths.",
        "excludes": "Ordinary value allocation, string connection URLs or plain async calls without owned resource lifecycle.",
    },
    "ui-race-auditor": {
        "applies": "Coordinates UI events or asynchronous results with rendered state, visibility, focus, scroll or layout.",
        "excludes": "Backend logic, static text or styling without asynchronous UI state coordination.",
    },
    "distributed-flow-auditor": {
        "applies": "Publishes, receives, acknowledges or routes messages across a service/process boundary or defines producer-consumer transport contracts.",
        "excludes": "In-process function calls or local data transformations.",
    },
    "logic-integrity-auditor": {
        "applies": "Enforces a domain rule, allowed state transition, ordering requirement, idempotency condition, fallback semantics or ownership invariant.",
        "excludes": "Generic formatting, logging or numerical/date conversion without a domain invariant.",
    },
    "cleanup-auditor": {
        "applies": "Shows unused or obsolete code, dependencies or assets, or documentation/comments that disagree with the implementation.",
        "excludes": "Normal code or comments with no visible obsolescence or contradiction in the supplied input.",
    },
}


def blind_packet(out: Path) -> None:
    """Create a blind code-only adjudication packet for development cases plus Jupiter calibration."""
    import gutsy_followup as followup

    jupiter_ref = HERE / "runs/20261020-gutsy-followup-ctx1536/cases.json"
    jupiter_cases = [case for case in load(jupiter_ref) if case["id"].startswith("E")] if jupiter_ref.exists() else []
    dev_cases = [case for case in load(out / "cases.json") if case["split"] == "development"]

    def pack(case: dict, index: int, group: str) -> dict:
        windows = followup.window_hunks(case["hunks"])
        return {
            "blind_id": f"{group}{index:02}",
            "group": group,
            "input_sha256": digest("".join(h["text"] for h in case["hunks"]).encode()),
            "windows": [{"window_id": w["id"], "text": followup.window_state(f"{group}{index:02}", w)} for w in windows],
            "slots": {role: {"judgment": None, "confidence": None, "code_anchor_or_exclusion": None} for role in ROLES},
        }

    blind_items = ([pack(case, idx, "J") for idx, case in enumerate(jupiter_cases, 1)]
                   + [pack(case, idx, "D") for idx, case in enumerate(dev_cases, 1)])
    answer_key = {
        f"J{idx:02}": {"case_id": case["id"], "split": case["split"], "expected_roles": case["expected_roles"],
                       "negative_roles": case.get("negative_roles", []), "rationale": case.get("label_rationale")}
        for idx, case in enumerate(jupiter_cases, 1)
    } | {
        f"D{idx:02}": {"case_id": case["id"], "source_candidate_id": case.get("source_candidate_id"),
                       "source": case.get("source"), "expected_roles": case["expected_roles"],
                       "negative_roles": case.get("negative_roles", []), "provenance": case.get("provenance")}
        for idx, case in enumerate(dev_cases, 1)
    }
    save(out / "blind_audit_packet.json", {
        "schema": "choicer-eval/blind-audit-packet-v1",
        "status": "unfilled_blind_packet",
        "instructions": [
            "Judge each lens from the shown code windows and rubric only.",
            "Mark judgment as applicable, not_applicable or insufficient_evidence.",
            "Provide a line/range anchor for applicable and an exclusion reason for not_applicable.",
            "Calibrate on J01..J08 before judging D01..D27.",
        ],
        "decision_rules": {
            "jupiter_rubric_gate": "Two blind readers should recover at least 9/11 Jupiter positives and activate at most 2/30 explicit negatives before the rubric is used to rebuild external labels.",
            "external_visibility_refuted_if": "At least 50% of the 32 development positive assignments are judged applicable with defensible code anchors, while frozen-model recall on that supported subset remains near the overall 11%.",
            "external_visibility_supported_if": "At most 35% of the 32 development positive assignments are judged applicable from code alone, and frozen-model recall is materially higher on the code-supported subset than on the remaining assignments.",
        },
        "rubric": RUBRIC,
        "items": blind_items,
    })
    save(out / "blind_audit_key_DO_NOT_READ_DURING_AUDIT.json", {
        "schema": "choicer-eval/blind-audit-key-v1",
        "warning": "Read only after blind_audit_packet.json judgments are frozen.",
        "key": answer_key,
    })
    lines = ["# Blind code-only audit packet", "",
             "Do not read `blind_audit_key_DO_NOT_READ_DURING_AUDIT.json`, `cases.json` or external issue text while filling this packet.",
             "", "## Rubric", ""]
    for role, rule in RUBRIC.items():
        lines += [f"### {role}", f"- Applies: {rule['applies']}", f"- Excludes: {rule['excludes']}", ""]
    lines += ["## Items", "", f"- Jupiter calibration items: {len(jupiter_cases)} (`J01`..`J{len(jupiter_cases):02}`)",
              f"- External development items: {len(dev_cases)} (`D01`..`D{len(dev_cases):02}`)",
              "- Fill judgments in `blind_audit_packet.json`."]
    (out / "BLIND_AUDIT_PACKET.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"jupiter_items": len(jupiter_cases), "development_items": len(dev_cases),
                      "total_items": len(blind_items)}, indent=2))


def resolve_slot(r1: dict, r2: dict) -> dict:
    """Resolve two blind reader judgments into a visibility class."""
    j1, j2 = r1["judgment"], r2["judgment"]
    if j1 == "applicable" and j2 == "applicable":
        status = "code_supported"
    elif j1 == "not_applicable" and j2 == "not_applicable":
        status = "code_not_applicable"
    elif "applicable" in (j1, j2):
        status = "disputed_applicable"
    else:
        status = "insufficient_or_external_only"
    return {
        "reader_1": r1,
        "reader_2": r2,
        "agreed": j1 == j2,
        "visibility_status": status,
    }


def score_blind(out: Path) -> None:
    """Score two blind code-only readers against the key and frozen model answers."""
    r1_data = load(out / "blind_reader_1.json")
    r2_data = load(out / "blind_reader_2.json")
    key_data = load(out / "blind_audit_key_DO_NOT_READ_DURING_AUDIT.json")["key"]
    scores_data = load(out / "scores.json")
    r1_items = {item["blind_id"]: item for item in r1_data["items"]}
    r2_items = {item["blind_id"]: item for item in r2_data["items"]}
    assert set(r1_items) == set(r2_items) == set(key_data), "reader item IDs do not match key"

    model_rows = {}
    for row in scores_data["rows"]:
        model_rows[(row["case_id"], row["variant"])] = set(row["selected_model"])

    jupiter_pos_total = 0
    jupiter_pos_r1 = 0
    jupiter_pos_r2 = 0
    jupiter_pos_both = 0
    jupiter_neg_total = 0
    jupiter_neg_r1 = 0
    jupiter_neg_r2 = 0
    jupiter_neg_any = 0

    dev_positive_rows = []
    agreement_slots = 0
    total_slots = 0
    per_lens_agreement = {role: {"agreed": 0, "total": 0, "both_applicable": 0, "any_applicable": 0} for role in ROLES}

    for blind_id in sorted(key_data):
        meta = key_data[blind_id]
        expected = {role.split(":")[-1] for role in meta["expected_roles"]}
        negatives = {role.split(":")[-1] for role in meta.get("negative_roles", [])}
        for role in ROLES:
            s1 = r1_items[blind_id]["slots"][role]
            s2 = r2_items[blind_id]["slots"][role]
            resolved = resolve_slot(s1, s2)
            total_slots += 1
            per_lens_agreement[role]["total"] += 1
            if resolved["agreed"]:
                agreement_slots += 1
                per_lens_agreement[role]["agreed"] += 1
            if s1["judgment"] == "applicable" or s2["judgment"] == "applicable":
                per_lens_agreement[role]["any_applicable"] += 1
            if s1["judgment"] == "applicable" and s2["judgment"] == "applicable":
                per_lens_agreement[role]["both_applicable"] += 1

            if blind_id.startswith("J"):
                if role in expected:
                    jupiter_pos_total += 1
                    jupiter_pos_r1 += int(s1["judgment"] == "applicable")
                    jupiter_pos_r2 += int(s2["judgment"] == "applicable")
                    jupiter_pos_both += int(resolved["visibility_status"] == "code_supported")
                if role in negatives:
                    jupiter_neg_total += 1
                    jupiter_neg_r1 += int(s1["judgment"] == "applicable")
                    jupiter_neg_r2 += int(s2["judgment"] == "applicable")
                    jupiter_neg_any += int("applicable" in (s1["judgment"], s2["judgment"]))
            elif role in expected:
                case_id = meta["case_id"]
                full_role = f"senior-review:{role}"
                v2_hit = full_role in model_rows.get((case_id, "v2"), set())
                cand_hit = full_role in model_rows.get((case_id, "candidate"), set())
                dev_positive_rows.append({
                    "blind_id": blind_id,
                    "case_id": case_id,
                    "source_candidate_id": meta.get("source_candidate_id"),
                    "source": meta.get("source"),
                    "repo": (meta.get("provenance") or {}).get("repo"),
                    "role": role,
                    "visibility_status": resolved["visibility_status"],
                    "reader_1": s1,
                    "reader_2": s2,
                    "model_v2_activated": v2_hit,
                    "model_candidate_activated": cand_hit,
                })

    strata = {}
    for status in ("code_supported", "disputed_applicable", "insufficient_or_external_only", "code_not_applicable"):
        subset = [row for row in dev_positive_rows if row["visibility_status"] == status]
        v2_hits = sum(int(row["model_v2_activated"]) for row in subset)
        cand_hits = sum(int(row["model_candidate_activated"]) for row in subset)
        strata[status] = {
            "count": len(subset),
            "v2_hits": v2_hits,
            "v2_recall": round(v2_hits / len(subset), 4) if subset else None,
            "candidate_hits": cand_hits,
            "candidate_recall": round(cand_hits / len(subset), 4) if subset else None,
        }

    supported_count = strata["code_supported"]["count"]
    any_supported_count = supported_count + strata["disputed_applicable"]["count"]
    jupiter_gate_passed = (jupiter_pos_r1 >= 9 and jupiter_pos_r2 >= 9
                           and jupiter_neg_r1 <= 2 and jupiter_neg_r2 <= 2)
    summary = {
        "schema": "choicer-eval/blind-audit-results-v1",
        "total_slots": total_slots,
        "exact_slot_agreement": f"{agreement_slots}/{total_slots} ({100 * agreement_slots / total_slots:.1f}%)",
        "jupiter_calibration": {
            "positives_total": jupiter_pos_total,
            "reader_1_recovered": jupiter_pos_r1,
            "reader_2_recovered": jupiter_pos_r2,
            "both_recovered": jupiter_pos_both,
            "explicit_negatives_total": jupiter_neg_total,
            "reader_1_false_positives": jupiter_neg_r1,
            "reader_2_false_positives": jupiter_neg_r2,
            "either_false_positive": jupiter_neg_any,
            "rubric_gate_passed": jupiter_gate_passed,
        },
        "development_positives_total": len(dev_positive_rows),
        "code_supported_positives": supported_count,
        "any_reader_applicable_positives": any_supported_count,
        "strata": strata,
        "per_lens_agreement": per_lens_agreement,
        "development_positive_rows": dev_positive_rows,
    }
    save(out / "blind_audit_results.json", summary)
    lines = [
        "# Blind code-only audit results",
        "",
        f"- Exact slot agreement across all 35 items x 8 lenses: `{summary['exact_slot_agreement']}`",
        f"- Jupiter rubric gate (`>=9/11` positives and `<=2/30` explicit negatives per reader): `{'pass' if jupiter_gate_passed else 'fail'}`",
        f"  - Reader 1: `{jupiter_pos_r1}/{jupiter_pos_total}` positives, `{jupiter_neg_r1}/{jupiter_neg_total}` explicit negatives activated",
        f"  - Reader 2: `{jupiter_pos_r2}/{jupiter_pos_total}` positives, `{jupiter_neg_r2}/{jupiter_neg_total}` explicit negatives activated",
        f"  - Both readers applicable: `{jupiter_pos_both}/{jupiter_pos_total}` positives",
        "",
        "## External development positive assignments (`32` total)",
        "",
        "| Visibility stratum | Assignments | V2 recall | Candidate recall |",
        "| --- | ---: | ---: | ---: |",
    ]
    for status, info in strata.items():
        v2_str = f"{info['v2_hits']}/{info['count']} ({100 * info['v2_recall']:.1f}%)" if info["count"] else "0/0"
        cand_str = f"{info['candidate_hits']}/{info['count']} ({100 * info['candidate_recall']:.1f}%)" if info["count"] else "0/0"
        lines.append(f"| {status} | {info['count']} | {v2_str} | {cand_str} |")
    lines += ["", "## Per-assignment breakdown", ""]
    for row in dev_positive_rows:
        lines.append(
            f"- {row['blind_id']} / {row['case_id']} ({row['source_candidate_id']}, {row['repo']}) `{row['role']}` -> "
            f"`{row['visibility_status']}` | R1={row['reader_1']['judgment']} | R2={row['reader_2']['judgment']} | "
            f"V2={row['model_v2_activated']} | Cand={row['model_candidate_activated']}"
        )
    (out / "BLIND_AUDIT_RESULTS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "development_positive_rows"}, indent=2))


def validate(out: Path) -> None:
    pool_data = load(out / "candidate_pool.json")
    candidates = pool_data["candidates"]
    assert len({c["id"] for c in candidates}) == len(candidates), "duplicate candidate IDs"
    assert pool_data["counts"]["candidates"] == len(candidates)
    for cand in candidates:
        assert cand["exclusion"] is None, cand["id"]
        assert cand["input"]["chars"] <= MAX_INPUT_CHARS, cand["id"]
        text = "".join(h["text"] for h in cand["input"]["hunks"])
        assert cand["input"]["sha256"] == digest(text.encode()), cand["id"]
        assert cand["input"]["chars"] == len(text), cand["id"]
        for hunk in cand["input"]["hunks"]:
            assert hunk["sha256"] == digest(hunk["text"].encode()), cand["id"]
        assert "expected_roles" not in cand and "negative_roles" not in cand, cand["id"]
    fill_path = out / "fill_candidates.json"
    fill_count = 0
    if fill_path.exists():
        fill_data = load(fill_path)
        pool_ids = {cand["id"] for cand in candidates}
        for cand in fill_data["candidates"]:
            assert cand["id"] not in pool_ids, cand["id"]
            assert cand["exclusion"] is None, cand["id"]
            text = "".join(h["text"] for h in cand["input"]["hunks"])
            assert cand["input"]["sha256"] == digest(text.encode()), cand["id"]
        fill_count = len(fill_data["candidates"])
    print(json.dumps({"status": "passed", "candidates": len(candidates), "fill_candidates": fill_count,
                      "projects": len({c["repo"] for c in candidates})}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("inventory", "pool", "label-packet", "adjudicate", "fill", "freeze", "audit-visibility", "blind-packet", "score-blind", "validate"))
    parser.add_argument("--out", required=True, help="Run directory relative to this benchmark")
    parser.add_argument("--stage", help="Stage 1 run directory, required for freeze")
    args = parser.parse_args()
    target = (HERE / args.out).resolve()
    if not target.is_relative_to(HERE / "runs"):
        parser.error("Output must be inside this benchmark's runs directory")
    if args.action in ("freeze", "audit-visibility"):
        if not args.stage:
            parser.error(f"{args.action} requires --stage")
        stage = (HERE / args.stage).resolve()
        if not stage.is_relative_to(HERE / "runs"):
            parser.error("Stage directory must be inside this benchmark's runs directory")
        {"freeze": freeze, "audit-visibility": audit_visibility}[args.action](target, stage)
    else:
        target.mkdir(parents=True, exist_ok=True)
        {"inventory": inventory, "pool": pool, "label-packet": label_packet,
         "adjudicate": adjudicate, "fill": fill, "blind-packet": blind_packet,
         "score-blind": score_blind, "validate": validate}[args.action](target)
