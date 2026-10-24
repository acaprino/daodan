"""Rebuild detailed reports and the cross-experiment pilot summary offline."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.dont_write_bytecode = True

from metrics import CRITICAL_ROLES, _role_metrics, render_report, score
from run_eval import (
    BASE, THRESHOLD, build_requests, confined, digest, read_json, required_inputs,
    verified_results, write_json, write_text,
)


def number(value: float | None, percent: bool = False) -> str:
    if value is None:
        return "unknown"
    return f"{value:.1%}" if percent else f"{value:.3f}"


def short(role: str) -> str:
    name = role.split(":", 1)[-1]
    return {
        "resource-lifecycle-auditor": "resource",
        "temporal-resilience-auditor": "temporal",
        "abstraction-architect-agent": "abstraction",
        "react-performance-optimizer": "React-performance",
        "typescript-reviewer": "TypeScript",
        "workspace-auditor": "workspace",
        "platform-reviewer": "platform",
    }.get(name, name.removesuffix("-auditor"))


def roles(values: list[str] | None) -> str:
    return "unavailable" if values is None else ", ".join(short(value) for value in values) or "none"


def table(headers: list[str], rows: list[list[object]]) -> list[str]:
    clean = lambda value: str(value).replace("|", "\\|").replace("\n", " ")
    return [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
        *["| " + " | ".join(clean(cell) for cell in row) + " |" for row in rows],
        "",
    ]


def refresh(run: Path, required_variants: tuple[str, ...]) -> tuple[dict, dict, dict, dict]:
    dataset, catalog, prompts = required_inputs(run)
    metadata = read_json(run / "metadata.json")
    records = verified_results(run, dataset, catalog, prompts)
    for key in required_variants:
        impl, variant = key.split("/")
        requests = build_requests(dataset, catalog, prompts, impl, variant)
        expected = {(row["case_id"], row["hunk_id"]) for row in requests}
        actual = [(row["case_id"], row["hunk_id"]) for row in records
                  if row["impl"] == impl and row["variant"] == variant]
        if len(actual) != len(expected) or set(actual) != expected:
            raise ValueError(f"Execution incomplete for {run.name}/{key}: {len(actual)}/{len(expected)} records")
    scored = score(dataset, catalog, records, threshold=THRESHOLD)
    write_json(run / "scores.json", scored)
    write_text(run / "RESULTS.md", render_report(dataset, catalog, scored, metadata))
    return dataset, catalog, metadata, scored


def cross_catalog_reference(original: dict, adapted: dict) -> dict:
    """Explicit exploratory comparison; never inserted into primary scores."""
    baseline = {row["case_id"]: row for row in original["models"]["llm/noul"]["case_results"]}
    candidate = {row["case_id"]: row for row in adapted["models"]["julia/noul"]["case_results"]}
    ids = sorted(
        key for key in baseline.keys() & candidate.keys()
        if baseline[key]["status"] == candidate[key]["status"] == "complete"
    )
    agreements = []
    for key in ids:
        left, right = set(baseline[key]["selected"]), set(candidate[key]["selected"])
        agreements.append({
            "case_id": key, "exact": left == right,
            "jaccard": len(left & right) / len(left | right) if left | right else 1.0,
        })
    return {
        "interpretation": "Exploratory reference across different reviewer criteria; not a same-catalog A/B test.",
        "paired_case_ids": ids,
        "baseline_metrics": _role_metrics([baseline[key] for key in ids]),
        "adapted_metrics": _role_metrics([candidate[key] for key in ids]),
        "agreement": agreements,
        "exact_agreement_rate": sum(row["exact"] for row in agreements) / len(ids) if ids else None,
        "mean_jaccard": sum(row["jaccard"] for row in agreements) / len(ids) if ids else None,
        "matched_adapted_llm_calls": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original", required=True)
    parser.add_argument("--adapted", required=True)
    args = parser.parse_args()
    original_path, adapted_path = confined(args.original), confined(args.adapted)
    dataset, catalog, original_meta, original = refresh(
        original_path, ("llm/noul", "julia/noul", "julia/choice"),
    )
    adapted_data, _, adapted_meta, adapted = refresh(
        adapted_path, ("julia/noul", "julia/choice"),
    )
    comparison = cross_catalog_reference(original, adapted)
    comparison["source_scores_sha256"] = {
        str(path.relative_to(BASE)): digest((path / "scores.json").read_bytes())
        for path in (original_path, adapted_path)
    }
    write_json(original_path / "adapted-comparison.json", comparison)
    a = original["models"]["llm/noul"]
    b = original["models"]["julia/noul"]
    c = original["models"]["julia/choice"]
    adapted_b = adapted["models"]["julia/noul"]
    adapted_c = adapted["models"]["julia/choice"]
    declared = original["raw_declared_llm_diagnostic"]
    relative = lambda path: path.relative_to(BASE).as_posix()
    lines = [
        "# Choicer offline pilot results",
        "",
        "**Verdict: this pilot does not justify opening Decision Log shadow mode or promoting Julia as a replacement.** "
        "The exact catalog is incompatible with Julia's lossless input contract. "
        "Adaptation is a separate exploratory experiment, and critical-role coverage remains incomplete.",
        "",
        "This verdict applies to the evaluated input formulations. It does not establish that local "
        "reviewer routing is infeasible. The [follow-up usage diagnosis](DIAGNOSIS.md) finds a measured "
        "source-presentation effect and tests alternative questions, runtime parity and fresh controls.",
        "",
        "See the [all-reviewer selection follow-up](ALL_REVIEWERS_RESULTS.md) for the expanded "
        "22-role applicability experiment.",
        "",
        f"Execution date: {original_meta['generated_at'][:10]}. "
        "All changes are development assets under this benchmark directory.",
        "",
        f"[Original detailed results]({relative(original_path)}/RESULTS.md) and "
        f"[adapted detailed results]({relative(adapted_path)}/RESULTS.md) contain "
        "the reliability tables, individual-role diagnostics, per-case wall/CPU timings, "
        "runtime identities and anomalies. The full threshold curves are in the "
        f"[original scoring JSON]({relative(original_path)}/scores.json) and "
        f"[adapted scoring JSON]({relative(adapted_path)}/scores.json). "
        f"[Comparison data]({relative(original_path)}/adapted-comparison.json) is derived offline.",
        "",
        "## Results and coverage",
        "",
        "A uses the frozen full-mode prompt with the original catalog. "
        "Its passing responses satisfy limited citation checks; base/candidate identity "
        "was omitted from the supplied hunks and remains unverified. "
        "B and C use the exact catalog; B is binary noul at 0.5, C is one categorical choice per hunk.",
        "",
        "Adapted B/C use all 18 reviewer IDs with independently authored compact criteria. "
        "Three missing negatives and security/premise/logic policy changes are explicit. "
        "The author read no cases, labels or predictions. "
        "Whole cases C02 and C07 were excluded using pre-inference context-size evidence, "
        f"leaving {len(adapted_data['cases'])} cases and "
        f"{sum(len(case['hunks']) for case in adapted_data['cases'])} unchanged hunks. "
        "There is no adapted LLM baseline.",
        "",
    ]
    rows = []
    for label, model, count in (
        ("A: original LLM, limited checks", a, len(dataset["cases"])),
        ("B: exact Julia noul", b, len(dataset["cases"])),
        ("C: exact Julia choice", c, len(dataset["cases"])),
        ("Adapted Julia noul", adapted_b, len(adapted_data["cases"])),
        ("Adapted Julia choice", adapted_c, len(adapted_data["cases"])),
    ):
        metric = model["metrics"]
        rows.append([
            label, f"{model['complete_cases']}/{count}", metric["labeled_cases"],
            f"{metric['matched_expected_roles']}/{metric['expected_role_activations']} "
            f"({number(metric['expected_role_recall'], True)})",
            f"{metric['critical_overall']['true_positives']}/{metric['critical_overall']['support']} "
            f"({number(metric['critical_overall']['recall'], True)})",
            number(metric["benchmark_excess_per_case"]),
            number(model["calibration"].get("ece")),
        ])
    lines.extend(table(
        ["Implementation", "Complete cases", "Labeled scored", "Expected-role recall",
         "Critical recall", "Excess / labeled case", "Descriptive ECE"], rows,
    ))
    lines.extend([
        f"Adapted binary routing selects "
        f"{sum(len(row['selected']) for row in adapted_b['case_results'] if row['status'] == 'complete') / adapted_b['complete_cases']:.1f} "
        "of 18 reviewers per case on average. Its measured critical recall therefore "
        "comes with broad selection; this pilot does not demonstrate economical routing. "
        "The categorical control misses every expected activation on the adapted subset.",
        "",
        "The rows have different coverage and must not be read as a controlled accuracy ranking. "
        "Expected dimensions are partial positive labels: excess selections are a benchmark "
        "proxy, not proof of wasted reviewer work. Missing predictions never become negatives.",
        "",
        "## Critical roles",
        "",
    ])
    lines.extend(table(
        ["Role", "A hits / support", "Exact B hits / support", "Adapted B hits / support"],
        [[short(role), *[
            f"{model['metrics']['critical'][role]['true_positives']}/"
            f"{model['metrics']['critical'][role]['support']} "
            f"({number(model['metrics']['critical'][role]['recall'], True)})"
            for model in (a, b, adapted_b)
        ]] for role in CRITICAL_ROLES],
    ))
    partial = original["partial_capability_diagnostics"]["julia/noul"]["roles"]
    lines.extend(table(
        ["Exact B diagnostic only", "Accepted encodings", "Conditional hits / support", "Conditional recall"],
        [[short(role), partial[role]["accepted_encodings"],
          f"{partial[role]['true_positives']}/{partial[role]['scored_positive_support']}",
          number(partial[role]["expected_role_recall"], True)] for role in CRITICAL_ROLES],
    ))
    lines.extend([
        "The conditional table evaluates one representable role at a time across all hunks "
        "of its supporting cases. It does not establish a valid full-catalog routing decision.",
        "",
        "There are no premise-positive cases. Its recall is undefined, so this pilot cannot "
        "establish the full critical-role non-inferiority condition even if other measured roles pass.",
        "",
        "## Per-case selections and agreement",
        "",
        "A/B is the required exact-catalog comparison. The separate A/adapted column is "
        "exploratory and combines changes to the model and reviewer criteria. "
        "Each agreement cell gives exact equality and Jaccard overlap.",
        "",
    ])
    indices = [{row["case_id"]: row for row in model["case_results"]} for model in (a, b, adapted_b, adapted_c)]
    exploratory = {row["case_id"]: row for row in comparison["agreement"]}
    case_rows = []
    for case in dataset["cases"]:
        key = case["id"]
        entries = [index.get(key) for index in indices]
        selections = [entry["selected"] if entry and entry["status"] == "complete" else None for entry in entries]
        original_agreement = "unavailable"
        if selections[0] is not None and selections[1] is not None:
            left, right = set(selections[0]), set(selections[1])
            overlap = len(left & right) / len(left | right) if left | right else 1.0
            original_agreement = f"{left == right}; {overlap:.3f}"
        exploratory_row = exploratory.get(key)
        case_rows.append([
            key, roles(case["expected_roles"]) if case["label_status"] == "labeled" else "unlabeled",
            *[roles(selected) if entry is not None else "excluded by context rule" for selected, entry in zip(selections, entries)],
            original_agreement,
            f"{exploratory_row['exact']}; {exploratory_row['jaccard']:.3f}" if exploratory_row else "unavailable",
        ])
    lines.extend(table(
        ["Case", "Expected", "A", "Exact B", "Adapted B", "Adapted choice",
         "A/B agreement", "A/adapted reference"], case_rows,
    ))
    lines.extend([
        f"Cross-catalog reference: {len(comparison['paired_case_ids'])} paired cases, "
        f"exact agreement {number(comparison['exact_agreement_rate'], True)}, "
        f"mean Jaccard {number(comparison['mean_jaccard'])}. "
        "This is not evidence of an isolated classifier effect.",
        "",
    ])
    lines.extend(table(
        ["Exploratory common-case reference", "Labeled cases", "Expected-role recall", "Critical recall", "Excess / case"],
        [[label, metric["labeled_cases"],
          f"{metric['matched_expected_roles']}/{metric['expected_role_activations']} "
          f"({number(metric['expected_role_recall'], True)})",
          f"{metric['critical_overall']['true_positives']}/{metric['critical_overall']['support']} "
          f"({number(metric['critical_overall']['recall'], True)})",
          number(metric["benchmark_excess_per_case"])]
         for label, metric in (
             ("Original A on common cases", comparison["baseline_metrics"]),
             ("Adapted B on common cases", comparison["adapted_metrics"]),
         )],
    ))
    lines.extend([
        "## Output validity and exact-input failures",
        "",
        "Four native A outputs fail the limited checks: C02/C03/C07 cite an incorrect "
        "hunk or snippet; C08 contains a 16-word reason against the prompt's 15-word limit. "
        "Their raw declarations are retained in a separate diagnostic, never used in "
        "primary recall, agreement or the verdict. The marker omission affects all A "
        "outputs regardless of whether their other checks pass.",
        "",
        f"Unvalidated declaration diagnostic only: {declared['available_cases']} readable "
        f"role sets, {declared['metrics']['matched_expected_roles']}/"
        f"{declared['metrics']['expected_role_activations']} expected activations, "
        f"critical recall {number(declared['metrics']['critical_overall']['recall'], True)}, "
        f"and {number(declared['metrics']['benchmark_excess_per_case'])} excess selections "
        "per labeled case. These numbers show the effect of validation attrition; "
        "they are not a replacement baseline.",
        "",
        "The exact binary catalog has three missing negatives and additional criteria "
        "beyond Julia's 48-token option limit. Only nine of 18 reviewer pairs fit losslessly; "
        "the critical premise criterion does not. The exact choice control also fails its "
        "input contract. Successful partial answers remain visible in the detailed report. "
        "Four original source states already exceed 8192 tokens; no truncation was applied.",
        "",
        "After establishing that universal catalog failure, execution switched to atomic "
        "full-catalog validation: every remaining question is checked, but any rejected "
        "question prevents classification of that incomplete batch. Historical partial "
        "inference is retained as such. Validation-only attempts are not classifier "
        "predictions or measurements of classifier inference speed.",
        "",
        "## Execution and reproducibility",
        "",
        "A: OpenAI through native Codex tasks, requested and accepted model override "
        "`gpt-6-luna`, low effort, 11 isolated case tasks and no reruns. Provider-reported "
        "model identity, API-call count, usage and inference timing are unknown. "
        "Exact loader prompts and returned responses are saved. The transport includes "
        "the loader and host system/tool context; cheapest-model pricing was not independently verified.",
        "",
        "B: `SupersonicLabs/Julia-1`, revision "
        "`a85b127321d580d65176c89ced8273f305745d85`, CPU FP32, weight SHA-256 "
        "`df853bf7fe424420011f3d0c47a05d7341aa9eefa7fb9f203ea4aada4ad95b72`. "
        "The recorded environment uses torch 2.14.0, transformers 5.0.0, safetensors "
        "0.8.0 and numpy 2.5.4. Hardware: Intel Core Ultra 7 155H, 22 logical processors, "
        "33,775,378,432 bytes physical RAM; four inference threads, no GPU.",
        "",
        "The original local run began with batch size 16 (nine representable questions "
        "per hunk) and was resumed with batch size 1 after an observed memory peak of "
        "19,316,727,808 bytes resident and 26,873,974,784 bytes private allocation. "
        "Saved outputs are retained unchanged; interrupted attempts and runtime segments "
        "are recorded under `execution/`. These timings describe the executed workload, "
        "not a controlled model-speed comparison. Cold means first inference in a process; "
        "OS caches were not flushed. Load and interrupted work are separate from completed-call totals.",
        "",
        "All model inputs and outputs are JSON. Scores are bound to the exact input, catalog "
        "and prompt hashes. Frozen prompts match the current spec bodies despite concurrent "
        "edits elsewhere in that document. All 129 original hunks were independently "
        "rematerialized from their recorded source revisions or inline case sources. Historical fix localization "
        "is retrospective sampling, and no symbol cards were supplied.",
        "",
        "Rebuild both detailed reports and this summary without inference:",
        "",
        "```powershell",
        "python -B evals/senior-review/choicer-eval/summarize_runs.py `",
        f"  --original {relative(original_path)} `",
        f"  --adapted {relative(adapted_path)}",
        "```",
        "",
        "## Dimension mapping and display names",
        "",
    ])
    lines.extend(table(
        ["Expected dimension", "Exact role ID", "Display name"],
        [[dimension, role, short(role)] for dimension, role in sorted(dataset["dimension_mapping"].items())],
    ))
    lines.extend([
        "Other selected roles retain their registered names with the `-auditor` suffix "
        "omitted in compact tables; all exact IDs appear in the detailed JSON and reports.",
        "",
        "## Gates and token economics",
        "",
        "The user explicitly authorized the benchmark-local uv environment, approximately "
        "584 MiB of Julia snapshot files plus runtime dependencies, and 11 native "
        "gpt-6-luna case tasks after disclosure of the 184,073-token planning estimate "
        "(characters/4, not measured usage). Reviewer adaptation was separately authorized. "
        "No additional paid adapted baseline, secondary laya run or optional task-tier run "
        "was performed. No plugin dependency or kernel file was changed.",
        "",
        "Net tokens saved per run = tier1 Choicer tokens avoided + downstream reviewer "
        "tokens avoided - routing-error costs. **Unknown**: provider usage, actual downstream "
        "spend and the cost of missed reviews were not measured. Local inference itself "
        "does not establish a positive token balance.",
        "",
        "## Proposed spec update",
        "",
        "Treat Julia-1 as an unpromoted experimental adapter. The 11-case pilot found "
        "that exact reviewer metadata cannot be encoded losslessly, while a separately "
        "authored nine-case adaptation changes the routing contract and lacks a matched "
        "LLM baseline. Before opening Decision Log shadow mode, define canonical typed "
        "criteria, repair the evidence-side binding, specify handling for oversized hunks, "
        "and rerun with an independent premise-positive set and provider-level telemetry. "
        "Keep the fixed threshold and full provenance; require critical-role false negatives "
        "no worse than the matched baseline and measured positive net token savings before "
        "considering promotion.",
        "",
    ])
    write_text(BASE / "RESULTS.md", "\n".join(lines))
    print(f"Wrote {BASE / 'RESULTS.md'}")


if __name__ == "__main__":
    main()
