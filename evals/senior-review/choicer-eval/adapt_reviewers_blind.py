"""Author and audit outcome-blind reviewer descriptions from frozen role metadata.

This script never opens benchmark cases, labels, captures, results or predictions.
Its only project inputs are the frozen catalog, frozen prompts and three original
role files; the installed tokenizer and upstream serializer establish API limits.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
FROZEN = ROOT / "runs" / "20261020T100258Z"
SNAPSHOT = ROOT / (
    ".cache/huggingface/hub/models--SupersonicLabs--Julia-1/"
    "snapshots/a85b127321d580d65176c89ced8273f305745d85"
)
for key, value in {
    "PYTHONDONTWRITEBYTECODE": "1",
    "HF_HUB_OFFLINE": "1",
    "TRANSFORMERS_OFFLINE": "1",
    "HF_HOME": str(ROOT / ".cache/huggingface"),
    "TORCH_HOME": str(ROOT / ".cache/torch"),
}.items():
    os.environ[key] = value
sys.dont_write_bytecode = True
sys.path.insert(0, str(SNAPSHOT))

from tokenizers import Tokenizer
from transformers import AutoTokenizer
from julia.data import sequence


CATALOG_PATH = FROZEN / "catalog.json"
PROMPTS_PATH = FROZEN / "prompts.json"
TOKENIZER_PATH = SNAPSHOT / "tokenizer/tokenizer.json"
SEQUENCE_PATH = SNAPSHOT / "julia/data.py"
BINARY_QUESTION = "Does this hunk satisfy the reviewer's TRIGGER WHEN?"
CHOICE_QUESTION = "Which reviewer's TRIGGER WHEN is best satisfied by this hunk?"

# None means preserve the original criterion exactly. Authored criteria are
# independent of benchmark examples; changes are grounded in the named sources.
ADAPTATIONS = {
    "abstraction-architect:abstraction-architect-agent": {
        "true": "Duplicated domain concepts or logic, competing sources of truth, wrong abstractions, or unclear canonical ownership of facts, policies or state.",
        "false": "Implementation, security, distributed flows, dead code, or dependency cycles and cohesion, without duplicated domain concepts or competing ownership.",
        "choice": "Duplicate domain logic or competing sources of truth; excludes dead code, security, and dependency cycles.",
        "rationale": "Replace dispatch instructions with the role's structural-entropy remit; remove owner names and qualify exclusions to preserve overlapping relevant lenses.",
    },
    "platform-engineering:platform-reviewer": {
        "true": "Security, architecture or performance compliance in SPA, PWA, mobile, Electron or Tauri applications, including platform permissions, client trust, IPC, service workers, storage or rendering.",
        "false": "Platform-independent code or documents with no SPA, PWA, mobile or desktop application security, architecture or performance concern.",
        "choice": "Web, mobile or desktop platform security, architecture or performance; excludes platform-independent code.",
        "rationale": "Remove dispatch prose and express observable platform context from the role body. Author the missing negative from its platform applicability rule.",
        "role_sections": ["Phase 1: Detect Platform Context", "Phase 2: Security Audit", "Phase 3: Architecture Audit", "Phase 4: Performance Audit", "Rules"],
    },
    "react-development:react-performance-optimizer": {
        "true": "Reviewing or optimizing React performance: re-renders, React Compiler, Server Components, bundle size, state subscriptions or profiling.",
        "false": None,
        "choice": "React renders, state subscriptions, components or bundle performance; excludes CSS polish and native backends.",
        "rationale": "Remove dispatch prose and compress examples while retaining React-specific performance signals. Preserve the original negative criterion.",
    },
    "repo-hygiene:workspace-auditor": {
        "true": "Finding tracked build artifacts, ignore-rule gaps, scratch directories, orphan documentation assets or stale Git stashes, worktrees and branches.",
        "false": "Source-level dead code or unused dependencies, or applying removals rather than auditing workspace hygiene.",
        "choice": "Tracked build output, ignore gaps, scratch files or stale Git state; excludes source dead code.",
        "rationale": "Replace dispatch instructions with the catalog's filesystem and Git hygiene remit; remove execution-owner references from the exclusion.",
    },
    "senior-review:api-contract-auditor": {
        "true": None,
        "false": None,
        "choice": "Declared API schemas versus implementations or API changes; excludes absent contracts and internal invariants.",
        "rationale": "Both original criteria are complete, code-relevant and within the option limit; preserve them exactly.",
    },
    "senior-review:chicken-egg-detector": {
        "true": None,
        "false": None,
        "choice": "Startup ordering, bootstrap, configuration or migration dependencies; excludes steady-state flows.",
        "rationale": "Both original criteria are complete, code-relevant and within the option limit; preserve them exactly.",
    },
    "senior-review:cleanup-auditor": {
        "true": "Auditing dead code, orphan application assets, unused dependencies, stale documentation, or migration and debug leftovers.",
        "false": "Applying removals, filesystem or Git tidying, or a standalone language-specific unused-code scan.",
        "choice": "Dead code, unused dependencies, orphan assets or stale documentation; excludes filesystem and Git tidying.",
        "rationale": "Replace workflow activation with the catalog's application-hygiene remit and compress exclusions without changing their ownership boundaries.",
    },
    "senior-review:code-auditor": {
        "true": None,
        "false": None,
        "choice": "Architecture, coupling, failure paths, stale caches or code quality; excludes security-only audits.",
        "rationale": "Preserve the original broad code-review criterion and its security-specific exclusion; both fit the option limit.",
    },
    "senior-review:data-integrity-auditor": {
        "true": None,
        "false": None,
        "choice": "Database writes, transactions, caches or persistence races; excludes domain-only rules and messaging.",
        "rationale": "Both original criteria are complete, code-relevant and within the option limit; preserve them exactly.",
    },
    "senior-review:distributed-flow-auditor": {
        "true": None,
        "false": "A single local operation with no cross-service, agent or module interaction, producer-consumer contract, or integration boundary.",
        "choice": "Cross-service flows, messaging, idempotency and compensation; excludes isolated local operations.",
        "rationale": "Preserve the original positive. Author the missing negative as the absence of the stated cross-boundary remit.",
    },
    "senior-review:logic-integrity-auditor": {
        "true": "Cross-component ordering, idempotency, state machines, terminal states, domain rules or invariants require a logic or contract audit.",
        "false": "Only style, lint or security concerns are present, without domain logic, contracts, ordering or state invariants.",
        "choice": "Domain rules, state machines, ordering or idempotency; excludes styling and security alone.",
        "rationale": "Replace phase activation with the catalog's logic remit. A missing interconnect map is a preparation requirement, not irrelevance, under frozen selection rule 6.",
        "prompt_rules": ["SELECTION RULES 6"],
    },
    "senior-review:premise-auditor": {
        "true": "Code claims or assumptions require independent verification; touched functions have optional/default parameters, numeric/date thresholds, sign handling, or business-rule boundary cases.",
        "false": "Only defect hunting, map construction, style or wording is requested, without code claims, optional/default parameters, thresholds, sign handling or business-rule boundaries.",
        "choice": "Code claims, defaults, thresholds, signs or business boundaries; excludes styling and map construction.",
        "rationale": "Replace workflow-only activation with independent derivation and claim checking from the role body, plus frozen mandatory rule 3. Qualify the original exclusion so it cannot negate mandatory boundary checks.",
        "role_sections": ["Mode 1: Independent derivation (Phase 1c)", "Mode 2: Adversarial premise challenge (Phase 4b, Lens 0)", "Mode 3: Claim check (a plan, a specification or a document)"],
        "prompt_rules": ["SELECTION RULES 3: premise mandatory check"],
    },
    "senior-review:resource-lifecycle-auditor": {
        "true": None,
        "false": None,
        "choice": "Handles, sockets, connections, listeners, locks or timers need release; excludes general architecture and exploitation.",
        "rationale": "Both original criteria are complete, code-relevant and within the option limit; preserve them exactly.",
    },
    "senior-review:security-auditor": {
        "true": "Security review or changes to URLs, routes, endpoints, public functions, login, sessions, roles, permissions, data access by ID, injection, secrets, cryptography or security headers.",
        "false": "Only style, internal code quality or infrastructure/network configuration, without application interfaces, authentication, authorization, ID-based data access, secrets, injection, cryptography or security-header changes.",
        "choice": "URLs, public functions, auth, permissions, ID access or secrets; excludes internal styling.",
        "rationale": "The original fits 48 tokens but omits the frozen mandatory interface triggers. Integrate selection rule 3 with the role's application-security remit; qualify its general-quality and infrastructure exclusions accordingly.",
        "role_sections": ["Input Trust Boundaries", "Auth & Authorization", "Secrets & Credentials", "Cryptographic Mistakes", "API & Header Security"],
        "prompt_rules": ["SELECTION RULES 3: security mandatory check"],
    },
    "senior-review:temporal-resilience-auditor": {
        "true": None,
        "false": None,
        "choice": "Retries, timers, queues, polling or workers surviving repeated failure; excludes startup and UI races.",
        "rationale": "Both original criteria are complete, code-relevant and within the option limit; preserve them exactly.",
    },
    "senior-review:ui-race-auditor": {
        "true": "UI races between async data loading, rendering, layout and event handlers; scroll, focus, resize, stale measurements or layout reads before rendering completes.",
        "false": "No UI timing or layout interaction: only backend concurrency, static visual styling, or non-UI operations.",
        "choice": "Async UI rendering, layout, scroll, focus or measurements race; excludes static styling and backend concurrency.",
        "rationale": "Compress the original 49-token positive without dropping its timing remit. Author the missing negative from that framework-agnostic UI scope.",
    },
    "testing:test-suite-auditor": {
        "true": None,
        "false": None,
        "choice": "Test hygiene, flakiness, redundancy, placement or layer distribution; excludes writing tests or applying quarantine.",
        "rationale": "Both original criteria are complete, code-relevant and within the option limit; preserve them exactly.",
    },
    "typescript-development:type-safety-auditor": {
        "true": "TypeScript type safety: any leakage, unsound casts or assertions, missing runtime boundary validation, non-exhaustive handling, or strict tsconfig drift.",
        "false": None,
        "choice": "TypeScript any, casts, boundary validation or exhaustiveness; excludes naming, React performance and dead code.",
        "rationale": "Remove dispatch prose and retain the type-safety remit from the catalog description and trigger. Preserve the original negative criterion.",
    },
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    prompts = json.loads(PROMPTS_PATH.read_text(encoding="utf-8"))
    ids = catalog["reviewer_ids"]
    assert len(ids) == 18 and set(ids) == set(ADAPTATIONS)
    source_roles = {role["id"]: role for role in catalog["roles"]}
    tokenizer = Tokenizer.from_file(str(TOKENIZER_PATH))
    auto_tokenizer = AutoTokenizer.from_pretrained(
        SNAPSHOT / "tokenizer", local_files_only=True,
    )
    token_count = lambda text: len(tokenizer.encode(" " + text, add_special_tokens=False).ids)
    reviewers = []
    binary_audit = []
    source_reads = [CATALOG_PATH, PROMPTS_PATH, SEQUENCE_PATH, TOKENIZER_PATH]

    for role_id in ids:
        source = source_roles[role_id]
        edit = ADAPTATIONS[role_id]
        original = {"true": source["trigger_when"], "false": source["do_not_trigger_when"]}
        adapted = {
            side: original[side] if edit[side] is None else edit[side]
            for side in ("true", "false")
        }
        assert all(isinstance(value, str) and value.strip() for value in adapted.values())
        counts = {
            "original": {
                side: token_count(value) if value is not None else None
                for side, value in original.items()
            },
            "adapted": {side: token_count(value) for side, value in adapted.items()},
            "choice_description": token_count(edit["choice"]),
        }
        assert max(counts["adapted"].values()) <= 48, (role_id, counts)
        assert counts["choice_description"] <= 20, (role_id, counts)
        field_status = {
            side: (
                "preserved_exactly" if edit[side] is None else
                "authored_missing_criterion" if original[side] is None else
                "adapted_from_source"
            )
            for side in ("true", "false")
        }
        provenance = {
            "catalog": {
                "path": str(CATALOG_PATH.relative_to(ROOT)).replace("\\", "/"),
                "sha256": digest(CATALOG_PATH),
                "role_id": role_id,
                "original_field_mapping": {"true": "trigger_when", "false": "do_not_trigger_when"},
            },
            "role_source": {
                "path": source["source"],
                "sha256_frozen": source["source_sha256"],
                "description_start_line": source["description_start_line"],
                "body_consulted": bool(edit.get("role_sections")),
                "sections_consulted": edit.get("role_sections", []),
            },
            "field_status": field_status,
            "choice_description_status": "authored_compact_summary",
            "prompt_rules": edit.get("prompt_rules", []),
        }
        if edit.get("role_sections"):
            source_path = REPO / source["source"]
            actual_hash = digest(source_path)
            assert actual_hash == source["source_sha256"], role_id
            provenance["role_source"]["sha256_current_verified"] = actual_hash
            source_reads.append(source_path)
        if edit.get("prompt_rules"):
            provenance["prompt_source"] = {
                "path": str(PROMPTS_PATH.relative_to(ROOT)).replace("\\", "/"),
                "sha256": digest(PROMPTS_PATH),
                "key": "REVIEWER_CHOICER",
                "text_sha256": prompts["REVIEWER_CHOICER"]["sha256"],
            }
        reviewers.append({
            "id": role_id,
            "original": original,
            "adapted": adapted,
            "choice_description": edit["choice"],
            "provenance": provenance,
            "rationale": edit["rationale"],
            "policy_adaptation": {
                "substantive": bool(edit.get("prompt_rules")),
                "source_rules": edit.get("prompt_rules", []),
                "equivalent_to_original_criteria": not any(edit[side] is not None for side in ("true", "false")),
                "meaning_change": (
                    "Align activation and exclusions with the frozen reviewer-selection policy; this is not equivalent compression of the role metadata."
                    if edit.get("prompt_rules") else
                    "No additional prompt-policy rule is introduced. Changed criteria re-express the original remit for code relevance; missing negatives are authored, not extracted."
                ),
                "activation_is_evidence_conditioned": True,
            },
            "token_counts": counts,
        })
        encoded = sequence(auto_tokenizer, {
            "state": "probe",
            "question": BINARY_QUESTION,
            "type": "noul",
            "options": [adapted["false"], adapted["true"]],
        }, max_length=8192, head_length=512, strict=True)
        assert encoded["option_tokens"] == [counts["adapted"]["false"], counts["adapted"]["true"]]
        binary_audit.append({
            "id": role_id,
            "strict_sequence_passed": True,
            "option_order": ["false", "true"],
            "option_tokens": encoded["option_tokens"],
            "sequence_tokens_with_synthetic_probe": len(encoded["ids"]),
            "state_truncated": encoded["truncated"],
        })

    choices = [reviewer["choice_description"] for reviewer in reviewers]
    encoded_choice = sequence(auto_tokenizer, {
        "state": "probe",
        "question": CHOICE_QUESTION,
        "type": "choice",
        "options": choices,
    }, max_length=8192, head_length=512, strict=True)
    question_tokens = len(auto_tokenizer(
        "choice question: " + CHOICE_QUESTION, add_special_tokens=False,
    )["input_ids"])
    choice_options_tokens = sum(encoded_choice["option_tokens"])
    head_budget_tokens = question_tokens + choice_options_tokens + len(choices)
    assert head_budget_tokens <= 512
    output = {
        "schema": "choicer-eval/adapted-reviewers-v1",
        "language": "en",
        "purpose": "Outcome-blind adaptation of all 18 reviewer lenses to code-relevance decisions within the installed model's input limits.",
        "authoring_blindness": {
            "labels_or_outputs_provided_to_author": False,
            "labels_or_outputs_read_by_author": False,
            "statement": "The author was not given and did not read benchmark cases, labels, captures, results, model predictions, or other agents' work. Adaptation used only the frozen catalog, frozen reviewer prompt, the three identified original role bodies, and tokenizer/serializer source.",
            "iterations": "Token-count and serializer validation only; no output-guided tuning.",
        },
        "reviewer_ids": ids,
        "reviewer_count": len(reviewers),
        "decision_contract": {
            "binary_question": BINARY_QUESTION,
            "binary_option_order": ["false", "true"],
            "binary_probability_threshold": 0.5,
            "choice_question": CHOICE_QUESTION,
            "choice_option_order": "reviewer_ids order",
            "choice_options_field": "choice_description",
            "criterion_max_tokens": 48,
            "choice_description_target_tokens": 20,
            "head_length": 512,
            "max_length": 8192,
            "strict": True,
            "token_counting": "tokenizer.encode(' ' + criterion, add_special_tokens=False)",
            "question_scope": "Code relevance, not permission to dispatch or execute a reviewer. Prerequisite recovery and mandatory selection rules remain coordinator responsibilities.",
        },
        "reviewers": reviewers,
    }
    output_path = ROOT / "adapted_reviewers.json"
    write_json(output_path, output)
    audit = {
        "schema": "choicer-eval/adapted-reviewers-audit-v1",
        "adapted_reviewers_sha256": digest(output_path),
        "generator_sha256": digest(Path(__file__)),
        "model_snapshot_revision": SNAPSHOT.name,
        "tokenizer_sha256": digest(TOKENIZER_PATH),
        "serializer_sha256": digest(SEQUENCE_PATH),
        "serializer": "Installed julia.data.sequence; tokenizer only; no model weights loaded.",
        "source_reads": [
            {"path": str(path.relative_to(REPO)).replace("\\", "/"), "sha256": digest(path)}
            for path in source_reads
        ],
        "complete_reviewer_id_match": True,
        "original_criteria_preserved_losslessly": True,
        "original_true_preserved_exactly": sum(r["original"]["true"] == r["adapted"]["true"] for r in reviewers),
        "original_false_preserved_exactly": sum(r["original"]["false"] == r["adapted"]["false"] for r in reviewers),
        "authored_missing_false_ids": [
            r["id"] for r in reviewers if r["original"]["false"] is None
        ],
        "maximum_adapted_criterion_tokens": max(
            max(r["token_counts"]["adapted"].values()) for r in reviewers
        ),
        "maximum_choice_description_tokens": max(
            r["token_counts"]["choice_description"] for r in reviewers
        ),
        "binary": binary_audit,
        "choice": {
            "strict_sequence_passed": True,
            "question": CHOICE_QUESTION,
            "question_tokens_including_type_prefix": question_tokens,
            "option_tokens": encoded_choice["option_tokens"],
            "option_tokens_total": choice_options_tokens,
            "option_marker_tokens": len(choices),
            "head_budget_tokens": head_budget_tokens,
            "head_budget_limit": 512,
            "head_budget_remaining": 512 - head_budget_tokens,
            "serialization_boundary_tokens": 3,
            "sequence_tokens_with_synthetic_probe": len(encoded_choice["ids"]),
            "state_truncated": encoded_choice["truncated"],
        },
        "threshold": 0.5,
        "weights_loaded": False,
        "model_inference_calls": 0,
        "paid_baseline_calls": 0,
        "benchmark_data_read": False,
    }
    write_json(ROOT / "adapted_reviewers_audit.json", audit)
    rows = "\n".join(
        f"| {reviewer['id']} | {reviewer['token_counts']['adapted']['false']} | "
        f"{reviewer['token_counts']['adapted']['true']} | "
        f"{reviewer['token_counts']['choice_description']} |"
        for reviewer in reviewers
    )
    documentation = f"""# Blind reviewer adaptation

The author was not given and did not read benchmark cases, labels, captures,
results, model predictions, or other agents' work. This adaptation was authored
from the frozen catalog, frozen reviewer-selection prompt, three original role
bodies, and the installed tokenizer and serializer. Revisions used token counts
and serialization checks only. No model weights were loaded and no inference or
paid baseline calls were made.

The canonical artifact is [adapted_reviewers.json](adapted_reviewers.json).
It contains all 18 original reviewer IDs, the exact original positive and
negative strings (including the three original null negatives), complete adapted
criteria, compact choice descriptions, per-field provenance, and rationales.
[adapted_reviewers_audit.json](adapted_reviewers_audit.json) records hashes and
the exact serializer checks. The generator is [adapt_reviewers_blind.py](adapt_reviewers_blind.py).

The original catalog and runs are unchanged. The binary threshold remains 0.5.
The frozen catalog's strict extraction rule is preserved in the `original`
fields. Newly authored negatives exist only in `adapted` and are explicitly
marked `authored_missing_criterion`.

## Meaning and policy

Eight original positive criteria and {audit['original_false_preserved_exactly']}
original negative criteria are reused exactly. Other role-derived changes remove
workflow dispatch language or compress the documented remit for code relevance.
The three missing negatives (platform, distributed flow, UI race) are authored
scope exclusions, not purported quotations from the source.

Three entries explicitly record a substantive alignment with the frozen prompt:

- Security includes selection rule 3's URLs, routes, endpoints, public functions,
  login, sessions, roles, permissions and access by ID, alongside the role's
  application-security concerns. Its general-quality exclusion cannot override
  those evidence-conditioned triggers.
- Premise includes selection rule 3's optional/default parameters, numeric/date
  thresholds, sign handling and business-rule boundaries, alongside independent
  derivation and claim checking. Its exclusion cannot negate those checks.
- Logic integrity follows selection rule 6: a missing interconnect map is a
  preparation requirement, not a reason to declare the lens irrelevant.

These policy adaptations are not represented as equivalent compression. They
require matching code evidence and do not create universal activation. Embedding
a mandatory rule in a classifier criterion does not itself enforce the rule;
selection enforcement remains a coordinator responsibility.

## Input compatibility

The existing questions are unchanged:

- Binary: `{BINARY_QUESTION}`
- Choice: `{CHOICE_QUESTION}`

The installed `julia.data.sequence` passes with `strict=True`, `max_length=8192`
and `head_length=512` for all 18 binary pairs and the full 18-choice list.
Binary options are ordered false, true. Choice options are exactly the
`choice_description` strings, in `reviewer_ids` order, with no role IDs appended.

Every criterion is nonempty and at most {audit['maximum_adapted_criterion_tokens']}
tokens (limit 48). Every compact description is at most
{audit['maximum_choice_description_tokens']} tokens. Token counts encode a
leading space with special tokens disabled, matching the serializer.

The choice head consumes {head_budget_tokens} of 512 budgeted tokens:
{question_tokens} question tokens, {choice_options_tokens} option tokens and
18 option markers. The serializer adds three framing tokens outside that head
budget. It retains every option without truncation. The synthetic state is only
`probe`; actual benchmark state lengths must be checked separately. This audit
establishes input compatibility, not prediction accuracy.

| Reviewer | False tokens | True tokens | Choice tokens |
|---|---:|---:|---:|
{rows}

Artifact SHA-256: `{audit['adapted_reviewers_sha256']}`.
Tokenizer SHA-256: `{audit['tokenizer_sha256']}`.
Serializer SHA-256: `{audit['serializer_sha256']}`.
"""
    (ROOT / "adapted_reviewers.md").write_text(documentation, encoding="utf-8")
    print(json.dumps({
        "reviewer_count": len(reviewers),
        "maximum_criterion_tokens": audit["maximum_adapted_criterion_tokens"],
        "maximum_choice_tokens": audit["maximum_choice_description_tokens"],
        "choice_head_tokens": head_budget_tokens,
        "head_remaining": 512 - head_budget_tokens,
        "original_true_preserved": audit["original_true_preserved_exactly"],
        "original_false_preserved": audit["original_false_preserved_exactly"],
        "adapted_reviewers_sha256": audit["adapted_reviewers_sha256"],
    }, indent=2))


if __name__ == "__main__":
    main()
