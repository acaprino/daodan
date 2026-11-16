"""The report of a round of `modal_pipeline.py`: one page to read it, and its numbers to compare it with the next.

    python pipeline_report.py ROUND.json [MORE.json ...] [--out REPORT.md] [--compare OLD.json]

The files are the driver's outputs; a case in a later file replaces the same case of an earlier one. The report is
written as Markdown and, beside it with the suffix `.json`, as the same numbers (default: `<last file>.report.md`).
`--compare` takes the `.json` of an earlier report, or an earlier round's output, and prints what changed per
language and per case: states, and holes up or down.
"""
from __future__ import annotations

import argparse
import collections
import json
import statistics
import sys
from pathlib import Path

STATES = ("fresh", "failed", "unavailable")
STEPS = ("scan", "analyze", "union")
TOP = 3  # reasons, examples and cases shown per row


def _error(case: dict) -> str | None:
    """Why the case failed: its own error, or the first step that stopped the pipeline."""
    if case.get("error"):
        return case["error"]
    return next((f"{name}: {step['failed']}" for name, step in (case.get("steps") or {}).items()
                 if isinstance(step, dict) and step.get("failed")), None)


def _languages(case: dict) -> dict:
    steps = case.get("steps") or {}
    return (steps.get("union") or {}).get("languages") or (steps.get("analyze") or {}).get("languages") or {}


def _gaps(case: dict):
    """(step, gap) of the case: the pre-map's, then each analyzer's."""
    for gap in case.get("gaps") or []:
        yield "scan", gap
    for engine in ((case.get("steps") or {}).get("analyze") or {}).get("engines", {}).values():
        for gap in engine.get("gaps") or []:
            yield "analyze", gap


def build(round_: dict) -> dict:
    """The numbers of the round `round_` (case -> the driver's result), as plain JSON."""
    seconds = {name: case.get("seconds") or 0 for name, case in round_.items()}
    languages = collections.defaultdict(lambda: {
        "cases": 0, "states": collections.Counter(), "reasons": collections.defaultdict(collections.Counter),
        "files": collections.Counter(snapshot=0, indexed=0), "sites": 0, "answered": collections.Counter(),
        "holes": collections.Counter()})
    missing, unserved, by_case = [], collections.defaultdict(collections.Counter), {}
    premap = collections.defaultdict(lambda: dict.fromkeys(("given", "not_given", "found", "expected", "extra",
                                                            "wrong"), 0))
    gaps, runs = collections.defaultdict(list), collections.defaultdict(list)
    phases = collections.defaultdict(lambda: {"runs": 0, "seconds": 0.0})
    for name, case in round_.items():
        error = _error(case)
        by_case[name] = {"seconds": seconds[name], **({"error": error} if error else {}), "languages": {}}
        for language, entry in sorted(_languages(case).items()):
            total, state, coverage = languages[language], entry.get("state"), entry.get("coverage") or {}
            total["cases"] += 1
            total["states"][state] += 1
            if state != "fresh" and entry.get("reason"):
                total["reasons"][state][entry["reason"]] += 1
            files = coverage.get("files") or {}
            total["files"].update(snapshot=files.get("snapshot", 0), indexed=files.get("indexed", 0))
            total["sites"] += coverage.get("sites", 0)
            total["answered"].update(coverage.get("answered") or {})
            holes = {kind: hole["count"] for kind, hole in (coverage.get("holes") or {}).items()}
            total["holes"].update(holes)
            by_case[name]["languages"][language] = {"state": state, "holes": sum(holes.values())}
            if state == "fresh" and files.get("missing"):
                reasons = collections.Counter(item["reason"] for item in files["missing"]).most_common(TOP)
                missing.append({"case": name, "language": language, "missing": len(files["missing"]),
                                "snapshot": files["snapshot"], "reasons": dict(reasons)})
        for language, count in ((case.get("steps") or {}).get("union") or {}).get("no_analyzer", {}).items():
            unserved[language].update(cases=1, files=count)
        for facet, score in (case.get("premap") or {}).items():
            total = premap[facet]
            total["given" if score.get("given") else "not_given"] += 1
            if score.get("given"):
                for key in ("found", "expected"):
                    total[key] += score[key]
                for key in ("extra", "wrong"):
                    total[key] += len(score[key])
        for step, gap in _gaps(case):
            gaps[step, gap.get("kind")].append(": ".join(str(part) for part in (name, gap.get("path"),
                                                                                 gap.get("detail")) if part))
        for run in case.get("containers") or []:
            phases[run.get("phase")]["runs"] += 1
            phases[run.get("phase")]["seconds"] += run.get("duration_seconds") or 0
            if run.get("outcome") != "exited" or run.get("exit_code") != 0:
                runs[run.get("phase"), (run.get("image") or "").split("@")[0], run.get("outcome"),
                     run.get("exit_code"), run.get("cause")].append(name)
    failed = {name: case["error"] for name, case in by_case.items() if "error" in case}
    return {
        "cases": {"run": len(round_), "failed": failed, "seconds": {
            "total": round(sum(seconds.values()), 1),
            "median": round(statistics.median(seconds.values()), 1) if seconds else 0,
            "slowest": [list(item) for item in sorted(seconds.items(), key=lambda item: -item[1])[:5]]}},
        "languages": {language: {
            **total, "states": dict(total["states"]), "files": dict(total["files"]),
            "reasons": {state: [list(item) for item in reasons.most_common(TOP)]
                        for state, reasons in sorted(total["reasons"].items())},
            "answered": dict(sorted(total["answered"].items())), "holes": dict(sorted(total["holes"].items())),
            "share": round(sum(total["answered"].values()) / total["sites"], 4) if total["sites"] else None}
            for language, total in sorted(languages.items())},
        "missing": missing,
        "no_analyzer": {language: dict(total) for language, total in sorted(unserved.items())},
        "premap": dict(premap),
        "gaps": [{"step": step, "kind": kind, "count": len(found), "examples": found[:TOP]}
                 for (step, kind), found in sorted(gaps.items(), key=lambda item: (
                     STEPS.index(item[0][0]), -len(item[1]), str(item[0][1])))],
        "containers": {
            "runs": sum(phase["runs"] for phase in phases.values()),
            "seconds": round(sum(phase["seconds"] for phase in phases.values()), 1),
            "phases": {name: {"runs": phase["runs"], "seconds": round(phase["seconds"], 1)}
                       for name, phase in sorted(phases.items(), key=lambda item: str(item[0]))},
            "not_zero": [{"phase": phase, "image": image, "outcome": outcome, "exit_code": code, "cause": cause,
                          "count": len(cases), "cases": sorted(set(cases))[:TOP]}
                         for (phase, image, outcome, code, cause), cases in sorted(
                             runs.items(), key=lambda item: (-len(item[1]), [str(part) for part in item[0]]))]},
        "by_case": by_case,
    }


def num(value) -> str:
    """A number the Italian way: 1.234 and 1.234,5."""
    text = f"{value:,.1f}" if isinstance(value, float) else f"{value:,}"
    return text.translate(str.maketrans(",.", ".,"))


def _cell(value) -> str:
    if value is None:
        return "—"
    if isinstance(value, list):
        return "<br>".join(_cell(item) for item in value)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return num(value)
    return " ".join(str(value).split()).replace("|", "\\|")[:300]


def _table(head: tuple, rows: list) -> list[str]:
    if not rows:
        return ["Nessuno.", ""]
    return ["| " + " | ".join(head) + " |", "|" + " --- |" * len(head),
            *("| " + " | ".join(_cell(cell) for cell in row) + " |" for row in rows), ""]


def _counts(counts: dict) -> str:
    return ", ".join(f"{name} {num(count)}" for name, count in counts.items()) or "—"


def render(report: dict, files: list) -> str:
    """The report as Markdown; `files` names the round's files."""
    cases, languages, containers = report["cases"], report["languages"], report["containers"]
    states = STATES + tuple(sorted({state for total in languages.values() for state in total["states"]}
                                   - set(STATES)))
    lines = ["# Giro della pipeline sul corpus", "", "File: " + ", ".join(f"`{name}`" for name in files) + ".", "",
             "## Casi", "",
             f"- Eseguiti: {num(cases['run'])}; falliti: {num(len(cases['failed']))}.",
             f"- Secondi: {num(float(cases['seconds']['total']))} in totale; mediana "
             f"{num(float(cases['seconds']['median']))}.", "",
             "### Casi più lenti", "",
             *_table(("Caso", "Secondi"), [(name, float(seconds)) for name, seconds in cases["seconds"]["slowest"]]),
             "### Casi falliti", "", *_table(("Caso", "Errore"), list(cases["failed"].items())),
             "## Linguaggi", "",
             *_table(("Linguaggio", "Casi", *states, "File indicizzati / nello snapshot", "Siti", "Risposti", "Buchi",
                      "Quota risposta"),
                     [(language, total["cases"], *(total["states"].get(state, 0) for state in states),
                       f"{num(total['files']['indexed'])} / {num(total['files']['snapshot'])}", total["sites"],
                       sum(total["answered"].values()), sum(total["holes"].values()),
                       None if total["share"] is None else f"{num(total['share'] * 100)} %")
                      for language, total in languages.items()]),
             "### Risposte per tipo e buchi per classe", "",
             *_table(("Linguaggio", "Risposte", "Buchi"),
                     [(language, _counts(total["answered"]), _counts(total["holes"]))
                      for language, total in languages.items() if total["sites"]]),
             "### Stati diversi da fresh", "",
             *_table(("Linguaggio", "Stato", "Casi", "Motivo"),
                     [(language, state, count, reason) for language, total in languages.items()
                      for state, reasons in total["reasons"].items() for reason, count in reasons]),
             "### Linguaggi fresh con file fuori dall'indice", "",
             *_table(("Caso", "Linguaggio", "Mancanti / nello snapshot", "Motivi"),
                     [(row["case"], row["language"], f"{num(row['missing'])} / {num(row['snapshot'])}",
                       "; ".join(f"{reason} ({num(count)})" for reason, count in row["reasons"].items()))
                      for row in report["missing"]]),
             "### Linguaggi senza analizzatore", "",
             *_table(("Linguaggio", "Casi", "File"), [(language, total["cases"], total["files"])
                                                      for language, total in report["no_analyzer"].items()]),
             "## Pre-mappa", "",
             *_table(("Faccetta", "Casi che la danno", "Casi che non la danno", "Trovate", "Attese", "In più",
                      "Sbagliate"),
                     [(facet, *(total[key] for key in ("given", "not_given", "found", "expected", "extra", "wrong")))
                      for facet, total in report["premap"].items()]),
             "## Gap", "",
             *_table(("Passo", "Tipo", "Numero", "Esempi"),
                     [(gap["step"], gap["kind"], gap["count"], gap["examples"]) for gap in report["gaps"]]),
             "## Container", "",
             f"- Corse: {num(containers['runs'])}; secondi: {num(float(containers['seconds']))}.", "",
             *_table(("Fase", "Corse", "Secondi"), [(name, phase["runs"], float(phase["seconds"]))
                                                    for name, phase in containers["phases"].items()]),
             "### Esiti diversi da exit 0", "",
             *_table(("Fase", "Immagine", "Esito", "Codice", "Causa", "Corse", "Casi"),
                     [(row["phase"], row["image"], row["outcome"],
                       None if row["exit_code"] is None else str(row["exit_code"]), row["cause"], row["count"],
                       ", ".join(row["cases"])) for row in containers["not_zero"]])]
    return "\n".join(lines)


def _moved(label: str, old: int, new: int) -> str:
    return f"{label} {num(old)} → {num(new)} ({'+' if new > old else '-'}{num(abs(new - old))})"


def compare(old: dict, new: dict) -> list[str]:
    """What changed from the report `old` to `new`, per language and per case: states, holes up or down."""
    by_language, by_case = [], []
    for language in sorted(set(old["languages"]) | set(new["languages"])):
        before, after = (report["languages"].get(language) or {"states": {}, "holes": {}} for report in (old, new))
        names = STATES + tuple(sorted((set(before["states"]) | set(after["states"])) - set(STATES)))
        parts = [", ".join(f"{state} {before['states'].get(state, 0)} → {after['states'].get(state, 0)}"
                           for state in names if before["states"].get(state, 0) != after["states"].get(state, 0))]
        holes = [sum(total["holes"].values()) for total in (before, after)]
        if holes[0] != holes[1]:
            parts.append(_moved("buchi", *holes))
        if any(parts):
            by_language.append(f"- {language}: " + "; ".join(filter(None, parts)))
    for name in sorted(set(old["by_case"]) | set(new["by_case"])):
        before, after = old["by_case"].get(name), new["by_case"].get(name)
        if before is None or after is None:
            by_case.append(f"- {name}: " + ("nuovo" if before is None else "non più nel giro"))
            continue
        parts = []
        if before.get("error") != after.get("error"):
            parts.append(f"errore: {_cell(after['error'])}" if after.get("error") else "non fallisce più")
        for language in sorted(set(before["languages"]) | set(after["languages"])):
            was, now = (case["languages"].get(language) or {"state": "assente", "holes": 0}
                        for case in (before, after))
            if was["state"] != now["state"]:
                parts.append(f"{language} {was['state']} → {now['state']}")
            if was["holes"] != now["holes"]:
                parts.append(_moved(f"{language} buchi", was["holes"], now["holes"]))
        if parts:
            by_case.append(f"- {name}: " + "; ".join(parts))
    return [*(["Per linguaggio:", *by_language] if by_language else []),
            *(["Per caso:", *by_case] if by_case else [])] or ["Nessuna differenza."]


def main(argv: list) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("files", nargs="+", help="outputs of modal_pipeline.py; later ones replace earlier cases")
    parser.add_argument("--out", help="the Markdown to write; the numbers go beside it as .json")
    parser.add_argument("--compare", help="the .json of an earlier report, or an earlier round's output")
    args = parser.parse_args(argv)
    round_ = {}
    for file in args.files:
        round_.update(json.loads(Path(file).read_text(encoding="utf-8")))
    report = build(round_)
    out = Path(args.out) if args.out else Path(args.files[-1]).with_suffix(".report.md")
    out.with_suffix(".json").write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")
    out.write_text(render(report, [Path(file).name for file in args.files]), encoding="utf-8")
    print(out, out.with_suffix(".json"))
    if args.compare:
        old = json.loads(Path(args.compare).read_text(encoding="utf-8"))
        print("\n".join(compare(old if "by_case" in old else build(old), report)))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # a Windows console's code page holds no arrow
    main(sys.argv[1:])
