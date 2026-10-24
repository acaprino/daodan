"""Evaluate deterministic static routing (review_roster.py + AST/lexical signals) on C01..C11."""

from __future__ import annotations

import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(REPO / "plugins/project-protocol/skills/project-protocol/scripts"))
sys.path.insert(0, str(REPO / "plugins/codebase-map/skills/map-method/scripts"))

import review_roster  # noqa: E402
from languages import detect_language, get_adapter  # noqa: E402
import metrics  # noqa: E402
import probe_julia_facts  # noqa: E402
import run_eval  # noqa: E402

RUN_ID = "20261020T100258Z"

PERSISTENCE_ROLE = "senior-review:data-integrity-auditor"
SECURITY_ROLE = "senior-review:security-auditor"
DISTRIBUTED_ROLE = "senior-review:distributed-flow-auditor"
TEMPORAL_ROLE = "senior-review:temporal-resilience-auditor"
RESOURCE_ROLE = "senior-review:resource-lifecycle-auditor"
UI_ROLE = "senior-review:ui-race-auditor"
REACT_ROLE = "react-development:react-performance-optimizer"
TYPESCRIPT_ROLE = "typescript-development:type-safety-auditor"
CONTRACT_ROLE = "senior-review:api-contract-auditor"
STARTUP_ROLE = "senior-review:chicken-egg-detector"
PLATFORM_ROLE = "platform-engineering:platform-reviewer"
CODE_ROLE = "senior-review:code-auditor"

AST_PERSISTENCE_MODULES = {
    "sqlite3",
    "psycopg",
    "psycopg2",
    "asyncpg",
    "sqlalchemy",
    "pymongo",
    "motor",
    "redis",
    "aioredis",
    "prisma",
    "typeorm",
    "drizzle",
    "mongoose",
}
AST_PERSISTENCE_RECEIVERS = {
    "db",
    "database",
    "session",
    "conn",
    "connection",
    "cursor",
    "repo",
    "repository",
    "collection",
    "store",
    "cache",
    "redis",
    "mongo",
    "tx",
    "transaction",
}
AST_PERSISTENCE_METHODS = {
    "execute",
    "executemany",
    "commit",
    "rollback",
    "insert",
    "insert_one",
    "insert_many",
    "update",
    "update_one",
    "update_many",
    "delete",
    "delete_one",
    "delete_many",
    "find_one",
    "find_one_and_update",
    "upsert",
    "bulk_write",
    "save",
    "add",
    "flush",
    "hset",
    "hmset",
    "hdel",
    "setex",
    "mset",
    "zadd",
    "xadd",
}

AST_DISTRIBUTED_MODULES = {
    "httpx",
    "requests",
    "aiohttp",
    "urllib",
    "grpc",
    "pika",
    "aiokafka",
    "kafka",
    "celery",
    "nats",
    "zmq",
    "websockets",
}
AST_DISTRIBUTED_RECEIVERS = {
    "http",
    "client",
    "http_client",
    "api_client",
    "rpc",
    "broker",
    "bus",
    "event_bus",
    "queue",
    "producer",
    "consumer",
    "publisher",
    "webhook",
    "notifier",
}
AST_DISTRIBUTED_METHODS = {
    "post",
    "put",
    "patch",
    "request",
    "send",
    "publish",
    "emit",
    "broadcast",
    "notify",
    "dispatch",
    "invoke",
    "rpc",
}

AST_TEMPORAL_MODULES = {"asyncio", "schedule", "apscheduler", "tenacity", "backoff", "time"}
AST_TEMPORAL_CALLS = {
    "sleep",
    "create_task",
    "gather",
    "wait_for",
    "set_interval",
    "setInterval",
    "setTimeout",
    "requestAnimationFrame",
    "retry",
    "backoff",
    "poll",
    "heartbeat",
}

AST_RESOURCE_CALLS = {
    "open",
    "connect",
    "close",
    "acquire",
    "release",
    "Popen",
    "create_subprocess_exec",
    "create_subprocess_shell",
    "Lock",
    "RLock",
    "Semaphore",
    "ThreadPoolExecutor",
    "ProcessPoolExecutor",
    "addEventListener",
    "removeEventListener",
    "watch",
    "unwatch",
}

AST_SECURITY_MODULES = {
    "jwt",
    "jose",
    "cryptography",
    "hashlib",
    "hmac",
    "secrets",
    "ssl",
    "subprocess",
    "shlex",
}
AST_SECURITY_CALLS = {
    "eval",
    "exec",
    "loads",
    "yaml.load",
    "verify_token",
    "decode_token",
    "check_password",
    "authenticate",
    "authorize",
    "Popen",
    "system",
}

AST_UI_CALLS = {
    "scrollTo",
    "scrollIntoView",
    "focus",
    "blur",
    "getBoundingClientRect",
    "ResizeObserver",
    "IntersectionObserver",
    "MutationObserver",
    "useLayoutEffect",
    "requestAnimationFrame",
}


def _language_for_path(path: str) -> str:
    suffix = Path(path).suffix.lower()
    if suffix in {".py", ".pyi"}:
        return "python"
    if suffix in {".ts", ".tsx", ".mts", ".cts"}:
        return "typescript"
    if suffix in {".js", ".jsx", ".mjs", ".cjs"}:
        return "javascript"
    return "python"


def _synthetic_diff_and_numstat(case: dict) -> tuple[str, str]:
    diff_chunks: list[str] = []
    numstat_ByPath: dict[str, int] = {}
    for hunk in case["hunks"]:
        path = hunk["path"]
        lines = hunk["text"].splitlines()
        count = max(1, len(lines))
        numstat_ByPath[path] = numstat_ByPath.get(path, 0) + count
        start = hunk["start_line"]
        header = f"diff --git a/{path} b/{path}\n--- a/{path}\n+++ b/{path}\n@@ -0,0 +{start},{count} @@\n"
        body = "".join(f"+{line}\n" for line in lines)
        diff_chunks.append(header + body)
    numstat = "".join(f"{added}\t0\t{path}\n" for path, added in sorted(numstat_ByPath.items()))
    return "".join(diff_chunks), numstat


def _ast_signals_for_hunk(hunk: dict) -> tuple[set[str], dict[str, list[str]]]:
    path = hunk["path"]
    text = hunk["text"]
    lang = detect_language(Path(path), text) or _language_for_path(path)
    adapter = get_adapter(lang)
    parse_res = adapter.parse(text, path) if adapter else None
    facts = probe_julia_facts.source_facts(text)

    imports = {m.split(".")[0].lower() for m in facts.get("imported_modules", []) if m}
    named_imports: set[str] = set()
    decorators: list[str] = []
    if parse_res is not None:
        for imp in parse_res.imports:
            if imp.module:
                imports.add(imp.module.split(".")[0].lower())
            for name in imp.names:
                named_imports.add(name.lower())
        for fn in parse_res.functions:
            decorators.extend(getattr(fn, "decorators", ()))
        for cls in parse_res.classes:
            decorators.extend(getattr(cls, "decorators", ()))
            for m in cls.methods:
                decorators.extend(getattr(m, "decorators", ()))

    call_parts: list[list[str]] = [
        [part for part in call.split(".") if part]
        for call in facts.get("called_names", [])
        if call
    ]
    external_call_types: set[str] = set()
    if parse_res is not None:
        for ext in parse_res.external_calls:
            external_call_types.add(ext.call_type)
            parts = [p for p in ext.pattern.split(".") if p]
            if parts and parts not in call_parts:
                call_parts.append(parts)
        for fn in parse_res.functions:
            for c in fn.calls_made:
                parts = [p for p in c.split(".") if p]
                if parts and parts not in call_parts:
                    call_parts.append(parts)
        for cls in parse_res.classes:
            for m in cls.methods:
                for c in m.calls_made:
                    parts = [p for p in c.split(".") if p]
                    if parts and parts not in call_parts:
                        call_parts.append(parts)

    jsx_elements = list(facts.get("jsx_element_names", []))

    roles: set[str] = set()
    evidence: dict[str, list[str]] = {}

    def mark(role: str, reason: str) -> None:
        roles.add(role)
        evidence.setdefault(role, []).append(reason)

    # Language / React / UI / TypeScript
    if lang == "typescript" and (
        any(tok in text for tok in (" as ", ": any", "<any>", "unknown", "zod", "valibot", "io-ts", "!.", "satisfies"))
    ):
        mark(TYPESCRIPT_ROLE, "ts_boundary_or_cast")
    if jsx_elements or "react" in imports or any(name.startswith("use") for name in named_imports):
        mark(REACT_ROLE, "jsx_or_react_import")

    # Persistence / Data integrity
    if "database" in external_call_types:
        mark(PERSISTENCE_ROLE, "external_call_type:database")
    if imports & AST_PERSISTENCE_MODULES:
        mark(PERSISTENCE_ROLE, f"import:{sorted(imports & AST_PERSISTENCE_MODULES)[0]}")
    for parts in call_parts:
        lower = [p.lower() for p in parts]
        leaf = lower[-1]
        recv = lower[0] if len(lower) > 1 else ""
        if leaf in AST_PERSISTENCE_METHODS and (
            not recv
            or any(tok in recv for tok in AST_PERSISTENCE_RECEIVERS)
            or leaf in {"insert_one", "insert_many", "update_one", "update_many", "find_one_and_update", "executemany", "commit", "rollback", "hset", "setex"}
        ):
            mark(PERSISTENCE_ROLE, f"call:{'.'.join(parts)}")
        elif any(tok in recv for tok in ("cache", "redis", "mongo", "db", "session", "repo", "store")) and leaf in {"get", "set", "delete", "pop", "put", "fetch", "write", "read"}:
            mark(PERSISTENCE_ROLE, f"store_call:{'.'.join(parts)}")
    if any(k in path.lower() for k in ("repo", "repository", "store", "cache", "db", "model", "migration", "persistence")):
        if any(w in text.lower() for w in ("select ", "insert ", "update ", "delete ", "transaction", "atomic", "commit", "cache", "redis", "mongo", "upsert", "balance", "payment", "order")):
            mark(PERSISTENCE_ROLE, f"path_and_domain:{path}")

    # Distributed / cross-service flow
    if imports & AST_DISTRIBUTED_MODULES:
        mark(DISTRIBUTED_ROLE, f"import:{sorted(imports & AST_DISTRIBUTED_MODULES)[0]}")
    for parts in call_parts:
        lower = [p.lower() for p in parts]
        leaf = lower[-1]
        recv = lower[0] if len(lower) > 1 else ""
        if leaf in AST_DISTRIBUTED_METHODS and any(tok in recv for tok in AST_DISTRIBUTED_RECEIVERS):
            mark(DISTRIBUTED_ROLE, f"call:{'.'.join(parts)}")
    if any(k in path.lower() for k in ("notifier", "webhook", "client", "gateway", "broker", "consumer", "producer", "sync", "dispatch", "middleware", "agent")):
        if any(w in text.lower() for w in ("http", "request", "webhook", "notify", "event", "message", "payload", "remote", "rpc", "broadcast", "heartbeat", "register")):
            mark(DISTRIBUTED_ROLE, f"path_and_flow:{path}")

    # Temporal resilience (timers, loops, retries, background tasks, heartbeats)
    if imports & AST_TEMPORAL_MODULES:
        mark(TEMPORAL_ROLE, f"import:{sorted(imports & AST_TEMPORAL_MODULES)[0]}")
    for parts in call_parts:
        leaf = parts[-1]
        if leaf in AST_TEMPORAL_CALLS or leaf.lower() in {c.lower() for c in AST_TEMPORAL_CALLS}:
            mark(TEMPORAL_ROLE, f"call:{'.'.join(parts)}")
    if any(w in text.lower() for w in ("while true", "retry", "backoff", "interval", "timeout", "heartbeat", "cooldown", "schedule", "every_", "periodic")):
        mark(TEMPORAL_ROLE, "temporal_keyword")

    # Resource lifecycle (sockets, files, subprocesses, locks, pools, listeners)
    for parts in call_parts:
        leaf = parts[-1]
        if leaf in AST_RESOURCE_CALLS:
            mark(RESOURCE_ROLE, f"call:{'.'.join(parts)}")
    if any(w in text for w in ("__enter__", "__exit__", "__aenter__", "__aexit__", "with open(", "async with ", "subprocess.", "socket.")):
        mark(RESOURCE_ROLE, "resource_context_or_handle")

    # Security / trust boundary
    if imports & AST_SECURITY_MODULES:
        mark(SECURITY_ROLE, f"import:{sorted(imports & AST_SECURITY_MODULES)[0]}")
    for parts in call_parts:
        joined = ".".join(parts)
        leaf = parts[-1]
        if leaf in AST_SECURITY_CALLS or joined in AST_SECURITY_CALLS:
            mark(SECURITY_ROLE, f"call:{joined}")
    if any(w in text.lower() for w in ("password", "secret", "token", "apikey", "api_key", "credential", "bearer", "permission", "auth", "csrf", "xss", "sanitize", "shell=true")):
        mark(SECURITY_ROLE, "security_keyword")

    # UI race conditions
    for parts in call_parts:
        if parts[-1] in AST_UI_CALLS:
            mark(UI_ROLE, f"call:{'.'.join(parts)}")
    if jsx_elements and any(w in text for w in ("useEffect", "useLayoutEffect", "scroll", "focus", "offsetHeight", "clientHeight", "innerWidth")):
        mark(UI_ROLE, "jsx_and_layout_timing")

    # API contract auditor
    if any(d.startswith(("app.", "router.", "api.", "bp.")) for d in decorators) or any(
        w in text for w in ("BaseModel", "TypedDict", "dataclass", "openapi", " json_schema", "Response(", "StatusCode", "status_code")
    ):
        mark(CONTRACT_ROLE, "schema_or_route_decorator")

    # Startup / chicken-egg detector
    if any(k in path.lower() for k in ("init", "bootstrap", "startup", "config", "lifespan", "loader", "updater")) and any(
        w in text.lower() for w in ("startup", "bootstrap", "initialize", "lifespan", "depend", "ready", "migrate", "register", "update")
    ):
        mark(STARTUP_ROLE, f"startup_path:{path}")

    return roles, evidence


def evaluate_static_variants() -> dict:
    run_dir = HERE / "runs" / RUN_ID
    dataset = json.loads((run_dir / "dataset.json").read_text(encoding="utf-8"))
    catalog = json.loads((run_dir / "catalog.json").read_text(encoding="utf-8"))
    reviewer_ids = set(catalog["reviewer_ids"])

    variants = {
        "roster_signals_only": {},
        "roster_full_tier": {},
        "ast_domain_router": {},
        "hybrid_union_candidates": {},
    }
    per_case_details: dict[str, dict] = {}

    for case in dataset["cases"]:
        cid = case["id"]
        diff_text, _ = _synthetic_diff_and_numstat(case)
        roster_out = review_roster.compute("branch", diff_text, None, None, False)

        # 1. Signals-only from review_roster.py (what review_roster triggers purely from SIGNAL_ROLE + LANGUAGE_ROLE, mapped to reviewer_ids)
        signal_roles: set[str] = {CODE_ROLE}
        for sig, matched in roster_out["signals"]["content"].items():
            if matched and sig in review_roster.SIGNAL_ROLE:
                role = review_roster.SIGNAL_ROLE[sig]
                if role in reviewer_ids:
                    signal_roles.add(role)
        for lang in roster_out["signals"]["languages"]:
            role = review_roster.LANGUAGE_ROLE.get(lang)
            if role and role in reviewer_ids:
                signal_roles.add(role)
        for name in ("contract", "manifest"):
            if roster_out["signals"][name] and review_roster.SIGNAL_ROLE[name] in reviewer_ids:
                signal_roles.add(review_roster.SIGNAL_ROLE[name])

        # 2. Full review_roster.py output (filtered to the 18 review-branch reviewer_ids)
        full_roster_roles = {r for r in roster_out["roster"] if r in reviewer_ids}

        # 3. Enriched AST + lexical domain router (using codebase-map's languages.parse_source + domain rules)
        ast_roles: set[str] = {CODE_ROLE}
        case_evidence: dict[str, list[str]] = {}
        for hunk in case["hunks"]:
            h_roles, h_ev = _ast_signals_for_hunk(hunk)
            ast_roles |= (h_roles & reviewer_ids)
            for r, reasons in h_ev.items():
                if r in reviewer_ids:
                    case_evidence.setdefault(r, []).extend(f"{hunk['id']}:{reason}" for reason in reasons)

        # Add logic-integrity-auditor when state transitions / multi-step branches / cache-state coordination appear
        joined_text = "\n".join(h["text"] for h in case["hunks"])
        if any(w in joined_text.lower() for w in ("state", "status", "transition", "idempoten", "lock", "version", "sequence", "order", "balance", "converge", "stale")):
            ast_roles.add("senior-review:logic-integrity-auditor")

        # 4. Hybrid candidate pool (union of review_roster signals + AST domain router + logic/abstraction core)
        hybrid_roles = signal_roles | ast_roles | {"senior-review:logic-integrity-auditor", "abstraction-architect:abstraction-architect-agent"}

        variants["roster_signals_only"][cid] = sorted(signal_roles)
        variants["roster_full_tier"][cid] = sorted(full_roster_roles)
        variants["ast_domain_router"][cid] = sorted(ast_roles)
        variants["hybrid_union_candidates"][cid] = sorted(hybrid_roles)

        per_case_details[cid] = {
            "source_case": case["source_case"],
            "label_status": case["label_status"],
            "expected_roles": case["expected_roles"],
            "roster_tier": roster_out["tier"],
            "roster_signals_only": sorted(signal_roles),
            "roster_full_tier": sorted(full_roster_roles),
            "ast_domain_router": sorted(ast_roles),
            "hybrid_union_candidates": sorted(hybrid_roles),
            "ast_evidence": {k: sorted(set(v)) for k, v in sorted(case_evidence.items())},
        }

    # Score each static variant using metrics._role_metrics()
    scored_variants: dict[str, dict] = {}
    for name, selections_by_case in variants.items():
        case_rows = [
            {
                "case_id": case["id"],
                "label_status": case["label_status"],
                "expected_roles": case["expected_roles"],
                "selected": selections_by_case[case["id"]],
            }
            for case in dataset["cases"]
        ]
        scored_variants[name] = metrics._role_metrics(case_rows)

    # Load existing scored JSONs for LLM and Adapted Julia
    orig_scores = json.loads((run_dir / "scores.json").read_text(encoding="utf-8"))
    adapted_dir = HERE / "runs" / f"{RUN_ID}-adapted"
    adapted_scores = json.loads((adapted_dir / "scores.json").read_text(encoding="utf-8"))
    adapted_dataset = json.loads((adapted_dir / "dataset.json").read_text(encoding="utf-8"))

    # Also test: what if we intersect Adapted Julia noul with AST candidate pruning?
    julia_noul_case_results = adapted_scores["models"]["julia/noul"]["case_results"]
    pruned_case_rows = []
    for row in julia_noul_case_results:
        if row["status"] == "complete":
            cid = row["case_id"]
            allowed_pool = set(variants["hybrid_union_candidates"][cid])
            pruned_case_rows.append({
                "case_id": cid,
                "label_status": row["label_status"],
                "expected_roles": row["expected_roles"],
                "selected": sorted(set(row["selected"]) & allowed_pool),
            })
    pruned_julia_metrics = metrics._role_metrics(pruned_case_rows)

    # Also compute static variants restricted to the 9 adapted cases (8 labeled) for direct parity with Adapted Julia
    adapted_case_ids = {c["id"] for c in adapted_dataset["cases"]}
    scored_variants_on_9_cases: dict[str, dict] = {}
    for name, selections_by_case in variants.items():
        case_rows_9 = [
            {
                "case_id": case["id"],
                "label_status": case["label_status"],
                "expected_roles": case["expected_roles"],
                "selected": selections_by_case[case["id"]],
            }
            for case in dataset["cases"]
            if case["id"] in adapted_case_ids
        ]
        scored_variants_on_9_cases[name] = metrics._role_metrics(case_rows_9)

    summary = {
        "schema": "choicer-eval/static-router-comparison-v1",
        "variants_all_11_cases_10_labeled": {
            name: {
                "labeled_cases": sc["labeled_cases"],
                "expected_role_recall": f"{sc['matched_expected_roles']}/{sc['expected_role_activations']} ({sc['expected_role_recall']*100:.1f}%)",
                "critical_recall": f"{sc['critical_overall']['true_positives']}/{sc['critical_overall']['support']} ({sc['critical_overall']['recall']*100:.1f}%)",
                "excess_activations_per_case": round(sc["benchmark_excess_per_case"], 3),
                "mean_selected_per_labeled_case": round(
                    sum(len(variants[name][c["id"]]) for c in dataset["cases"] if c["label_status"] == "labeled") / 10.0,
                    3,
                ),
            }
            for name, sc in scored_variants.items()
        },
        "variants_on_9_adapted_cases_8_labeled": {
            name: {
                "labeled_cases": sc["labeled_cases"],
                "expected_role_recall": f"{sc['matched_expected_roles']}/{sc['expected_role_activations']} ({sc['expected_role_recall']*100:.1f}%)",
                "critical_recall": f"{sc['critical_overall']['true_positives']}/{sc['critical_overall']['support']} ({sc['critical_overall']['recall']*100:.1f}%)",
                "excess_activations_per_case": round(sc["benchmark_excess_per_case"], 3),
            }
            for name, sc in scored_variants_on_9_cases.items()
        },
        "baselines": {
            "llm_validated_7_labeled_cases": orig_scores["models"]["llm/noul"]["metrics"],
            "llm_raw_declared_10_labeled_cases": orig_scores["raw_declared_llm_diagnostic"]["metrics"],
            "julia_adapted_noul_8_labeled_cases": adapted_scores["models"]["julia/noul"]["metrics"],
            "julia_adapted_noul_pruned_by_hybrid_ast_8_labeled_cases": pruned_julia_metrics,
        },
        "per_case_details": per_case_details,
    }

    out_path = run_dir / "static-router-comparison.json"
    out_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


if __name__ == "__main__":
    res = evaluate_static_variants()
    print("=== All 10 labeled cases (11 total) ===")
    print(json.dumps(res["variants_all_11_cases_10_labeled"], indent=2))
    print("\n=== On 8 labeled adapted cases (9 total) ===")
    print(json.dumps(res["variants_on_9_adapted_cases_8_labeled"], indent=2))
    print("\n=== Baselines ===")
    print(json.dumps(res["baselines"], indent=2))
