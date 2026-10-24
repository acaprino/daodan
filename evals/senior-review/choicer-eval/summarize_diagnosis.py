"""Rebuild the usage-diagnosis report without inference."""
from __future__ import annotations

import sys
from pathlib import Path

sys.dont_write_bytecode = True

from run_eval import BASE, digest, encoded, read_json, write_json, write_text

RUN = BASE / "runs/20261020T-diagnostic"


def scored_control(control: dict, answers: dict) -> dict:
    result = {"id": control["id"]}
    for key, expected in (
        ("family", control["expected_family"]),
        ("react", control["expected_has_react"]),
        ("persistence", control["expected_has_persistence"]),
    ):
        if key not in answers:
            continue
        answer = answers[key]
        actual = answer["choice"] if key == "family" else answer["noul"] >= 0.5
        result[key] = {
            "expected": expected, "actual": actual, "correct": actual == expected,
            "p_true": answer.get("noul"),
        }
    return result


def metrics(rows: list[dict]) -> dict:
    output = {}
    for key in ("family", "react", "persistence"):
        data = [row[key] for row in rows if key in row]
        output[key] = {
            "correct": sum(row["correct"] for row in data), "count": len(data),
            "positive_hits": sum(row["expected"] is True and row["actual"] is True for row in data),
            "positive_support": sum(row["expected"] is True for row in data),
            "false_positives": sum(row["expected"] is False and row["actual"] is True for row in data),
            "negative_support": sum(row["expected"] is False for row in data),
        }
    return output


def bound_result(request: dict, path: Path) -> dict:
    result = read_json(path)
    assert result["request_sha256"] == digest(encoded(request)), str(path)
    assert set(result["raw_output"]["answers"]) == set(request["questions"]), str(path)
    return result["raw_output"]["answers"]


def main() -> None:
    controls = read_json(RUN / "fresh-controls.json")["cases"]
    by_id = {row["id"]: row for row in controls}
    raw_requests = {row["id"]: row for row in read_json(RUN / "phase2/fresh-requests.json")}
    rows = {"raw": [], "facts": [], "statements": []}
    for control in controls:
        answers = bound_result(raw_requests[control["id"]], RUN / "phase2/fresh-results" / f"{control['id']}.json")
        rows["raw"].append(scored_control(control, answers))
    official = {row["id"]: row for row in read_json(RUN / "official-controls.json")["expected"]}
    published = []
    requests = read_json(RUN / "phase3/requests.json")
    assert len(requests) == 2 * len(controls) + len(official)
    for request in requests:
        answers = bound_result(request, RUN / "phase3/results" / f"{request['id']}.json")
        if request["id"].startswith("official-"):
            key = request["id"].removeprefix("official-")
            for qid, answer in answers.items():
                expected = official[key]["questions"][qid]["label"] == "true"
                published.append({
                    "id": key, "question": qid, "expected": expected,
                    "actual": answer["noul"] >= 0.5, "p_true": answer["noul"],
                    "correct": (answer["noul"] >= 0.5) == expected,
                })
        else:
            key, variant = request["id"].split("-", 1)
            rows[variant].append(scored_control(by_id[key], answers))
    summaries = {key: metrics(value) for key, value in rows.items()}
    parity = read_json(RUN / "phase2/encoder-parity.json")
    first = read_json(RUN / "diagnostic-summary.json")["rows"]
    typed = read_json(RUN / "phase2/type-results.json")
    assert len(parity) == 8 and len(typed) == 48
    findings = {
        "scope": "Follow-up usage diagnosis; development examples, not independent routing validation.",
        "fresh_control_rows": rows, "fresh_metrics": summaries,
        "published_rows": published,
        "published_correct": sum(row["correct"] for row in published),
        "published_count": len(published),
        "encoder_parity_rows": len(parity),
        "encoder_max_logit_delta": max(row["max_absolute_delta"] for row in parity),
        "encoder_all_decisions_equal": all(row["same_argmax"] for row in parity),
        "phase1_rows": first,
    }
    write_json(RUN / "diagnosis-scores.json", findings)
    lines = [
        "# Julia usage diagnosis",
        "",
        "The original pilot rejects its tested input formulations. It does not establish that local reviewer routing is impossible. "
        "The follow-up confirms sensitivity to source presentation and option wording, while elementary code decisions remain unreliable in these controls.",
        "",
        "## What was measured",
        "",
        "All probes reused the same pinned Julia weights, CPU FP32 runtime and four threads. No new model download, "
        "environment or paid LLM call was needed. Original pilot requests, outputs and scores remain unchanged.",
        "",
        "1. Reproduced the adapted pilot's irrelevant React activation on the Python cache hunk: "
        "P(true)=0.999919164. The diagnostic key `original_react` means that prior adapted criterion; "
        "it is not the original exact kernel criterion.",
        "2. In a fixed two-option code-family choice, the numbered/path-annotated Python state is classified as React. "
        "The same code without those annotations is classified as Python database/cache code. Reversing the two "
        "option positions retains both decisions. This establishes a presentation effect on this example, "
        "not a universal benefit of removing line numbers or a separation of path effects from numbering effects.",
        "3. Tested complementary criteria, explicit observable questions, literal Boolean options, raw code "
        "and manually authored natural-language summaries. Some corrections break positive controls. "
        "Complementary wording alone is not a demonstrated fix.",
        "4. Compared `noul` and `choice` with identical question/description text and permuted description order "
        "in 48 low-level probes. Reversed `noul` rows are intentional position diagnostics with explicit semantic "
        "index tracking, not standard typed-API probabilities. No threshold was fitted.",
        f"5. Compared the optimized and original encoder forward paths on {len(parity)} identical probes: "
        f"maximum absolute logit difference {findings['encoder_max_logit_delta']}; all decisions equal "
        f"{findings['encoder_all_decisions_equal']}. This checks the exercised path, not every runtime configuration.",
        "",
        "The official billing example also selects billing. Source audits found no false/true reversal, "
        "state loss, output-row mismatch, checkpoint mismatch, or truncation in the short failing example. "
        "Question IDs and role IDs are not model text: the generic reviewer question relies on the descriptions alone.",
        "",
        "## Fresh source controls",
        "",
        "An independent author supplied eight new snippets before inference: two React, two Python persistence/cache, "
        "two Python computations and two TypeScript computations. Gold stays outside model input. These are "
        "small development controls, not a representative test set or a validated reviewer-activation oracle.",
        "",
        "| Input/question formulation | Family correct | React positive hits | React false positives | Persistence positive hits | Persistence false positives |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for key, name in (
        ("raw", "Raw source, concrete questions"),
        ("facts", "Automatic structural facts, same questions"),
        ("statements", "Raw source, declarative Boolean instructions"),
    ):
        values = summaries[key]
        family = values["family"]
        lines.append(
            f"| {name} | {family['correct']}/{family['count']} | "
            f"{values['react']['positive_hits']}/{values['react']['positive_support']} | "
            f"{values['react']['false_positives']}/{values['react']['negative_support']} | "
            f"{values['persistence']['positive_hits']}/{values['persistence']['positive_support']} | "
            f"{values['persistence']['false_positives']}/{values['persistence']['negative_support']} |"
        )
    lines.extend([
        "",
        "A 0/0 family entry means that formulation did not ask a family question. Boolean overall accuracy "
        "can hide an always-negative response, so the table shows positive detection and false positives explicitly. "
        "Declarative persistence detects both positives but falsely selects five of six negatives; "
        "its overall correctness is only 3/8. It is not a repair.",
        "",
        "Structural facts are automatically extracted imports, called names, JSX elements and language. "
        "Python uses its standard AST; JavaScript/TypeScript uses a bounded diagnostic heuristic. "
        "The extractor receives no labels and emits no reviewer, bug or relevance assessment. "
        "These cards approximate an input boundary; they do not exercise the actual Codebase Map or prove "
        "that richer semantic cards would have the same outcome. Manually authored summaries in phase 1 "
        "are a separate representation experiment and do not establish free production preprocessing.",
        "",
        "## Published Boolean sanity sample",
        "",
        f"On the first three published rows from each of three domains, Julia agrees with the provided "
        f"Boolean gold on {findings['published_correct']}/{findings['published_count']} questions. "
        "These nine rows are a small convenience sample, not a reproduction of the full published benchmark. "
        "Gold probabilities are dataset annotations and are never substituted for Julia outputs.",
        "",
        "The exact state strings, questions, original rows, source URLs and pinned/current Parquet identities "
        "are retained in `official-controls.json`. The test-file hashes match the model card's pinned dataset "
        "revision despite a newer dataset HEAD.",
        "",
        "## Decision",
        "",
        "Keep the architecture question open. The pilot's broad negative result was insufficient to diagnose "
        "why routing failed. These probes establish that our representation matters and that importing dispatch "
        "descriptions as classification options is not a validated routing contract. They do not establish a "
        "working replacement by changing a flag or wording one question differently.",
        "",
        "A further routing experiment should define self-contained, code-grounded predicates, bind them to "
        "actual map evidence, test both positive and negative controls, and evaluate on new cases before "
        "reusing the pilot as a reported accuracy set. Any semantic-card authoring, model adaptation or fallback "
        "cost belongs in the token accounting. Thresholds and criteria should be fixed before that evaluation. "
        "No production routing or reviewer definition was changed here.",
        "",
        "## Reproduce and inspect",
        "",
        "[Scored evidence](runs/20261020T-diagnostic/diagnosis-scores.json), "
        "[frozen diagnostic plan](runs/20261020T-diagnostic/plan.json), "
        "[fresh controls](runs/20261020T-diagnostic/fresh-controls.json), "
        "[published controls](runs/20261020T-diagnostic/official-controls.json).",
        "",
        "Rebuild this report without inference:",
        "",
        "```powershell",
        "python -B evals/senior-review/choicer-eval/summarize_diagnosis.py",
        "```",
        "",
        "The inference entry points are `diagnose_julia.py`, `probe_julia_runtime.py` and "
        "`probe_julia_facts.py`; each separates preparation from execution and refuses to overwrite "
        "existing inference outputs. Their `run` actions require the already provisioned model environment.",
        "",
        "Official references: [Julia model card](https://huggingface.co/SupersonicLabs/Julia-1), "
        "[typed-decisions dataset](https://huggingface.co/datasets/LocalLLaMA/typed-decisions).",
        "",
    ])
    write_text(BASE / "DIAGNOSIS.md", "\n".join(lines))
    print(encoded(summaries))
    print(f"Published: {findings['published_correct']}/{findings['published_count']}")


if __name__ == "__main__":
    main()
