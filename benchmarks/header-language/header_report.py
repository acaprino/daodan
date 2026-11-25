"""Scores the measured records: the answers of each route against the label of each header, their costs, the pools of
headers to annotate by hand, and the estimate of what the unannotated part of a pool hides. Standard library only.

    python benchmarks/header-language/header_report.py [--results results] [--labels labels.json] [--out results/summary.json]
    python benchmarks/header-language/header_report.py --sample 90,30,25     # the headers to annotate, per declared label

A header's label is its project's, moved by a path prefix (`header_corpus`), and by its hand annotation if it has one
(`labels.json`: `project/path` -> {label, why}). Only a sample of each pool is annotated: the rest of the pool is
estimated from the sample, with its stratum weights (`estimate`), and reported beside the plain count.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

import header_corpus as corpus
import header_routes as routes

HERE = Path(__file__).resolve().parent
MAIN = ("R0", "R1dg", "R1eg", "R1dgo", "R1ego", "R2", "R2o", "R3", "R3d")  # the routes whose pools are annotated
CATEGORIES = ("c", "cpp", "objc", "either")


def key(record: dict) -> str:
    return f"{record['p']}/{record['path']}"


def features(record: dict) -> dict:
    """The record's features and the answer of the rule before (R0 of the records), which the `x` routes read."""
    return {**record["f"], "r0": record["r0"]}


def answer(record: dict, route: str) -> str:
    return record["r0"] if route == "R0" else routes.decide(route, features(record))


def cost_ms(record: dict, route: str) -> float:
    """What the route costs for this header: the parse and query of each grammar it needs, and for an `x` route the rule
    of today that comes first."""
    if route == "R0":
        return record["r0ms"]
    f = features(record)
    return sum(f[g]["ms"] + f[g]["q_ms"] for g in routes.needs(route, f)) + (record["r0ms"] if route.endswith("x") else 0.0)


def marginal_ms(record: dict, route: str) -> float:
    """The cost that is not paid anyway: the product parses the header with the grammar of the language it is given, and
    a route that parsed it with that grammar already (its tree can be kept) does not pay that parse twice. A header read
    as Objective-C is not parsed by the product, and the rule before parses nothing."""
    got, total = answer(record, route), cost_ms(record, route)
    if route == "R0" or got not in ("c", "cpp") or got not in routes.needs(route, features(record)):
        return total
    return total - record["f"][got]["ms"]


# ---- the pools of headers to annotate, and the estimate -----------------------------------------------------

def pools(records: list[dict], routes_in: tuple[str, ...] = MAIN) -> dict[str, dict[str, list[dict]]]:
    """For each declared label, the headers some of `routes` reads as another label: `all` of the routes do, or
    `some` do. An annotated sample of a stratum stands for the whole stratum."""
    out = {label: {"all": [], "some": []} for label in corpus.LABELS}
    for record in records:
        wrong = sum(answer(record, route) != record["decl"] for route in routes_in)
        if wrong:
            out[record["decl"]]["all" if wrong == len(routes_in) else "some"].append(record)
    return out


def annotation_sample(strata: dict[str, list[str]], total: int, seed: str, minimum: int = 2) -> list[str]:
    """`total` keys over the strata, in proportion to their sizes and at least `minimum` of each, seeded."""
    size = sum(len(keys) for keys in strata.values())
    take = {name: min(len(keys), max(minimum, round(total * len(keys) / size))) for name, keys in strata.items()}
    biggest = max(strata, key=lambda name: len(strata[name]))  # rounding is settled on the biggest stratum
    wanted = take[biggest] + total - sum(take.values())
    take[biggest] = min(len(strata[biggest]), max(min(minimum, len(strata[biggest])), wanted))
    chosen = []
    for name, keys in strata.items():
        ordered = sorted(keys, key=lambda k: hashlib.sha256(f"{seed}:{k}".encode()).hexdigest())
        chosen += ordered[:take[name]]
    return chosen


def estimate(records: list[dict], strata: dict[str, list[str]], labels: dict[str, str], test) -> tuple[float, float]:
    """The sum of `test(truth, record)` over all the headers (a bool counts 1, a number is itself: a difference of two
    routes' misses is a test too), and the standard error. Outside the pools a header's truth is its declared label;
    inside, each stratum's mean over its annotated headers times the stratum's size. A sample with no header of the
    kind has error 0 whatever the pool holds: read a 0 as 'none seen', not 'none'."""
    by = {key(r): r for r in records}
    pooled = {k for keys in strata.values() for k in keys}
    total, variance = float(sum(test(r["decl"], r) for r in records if key(r) not in pooled)), 0.0
    for name, keys in strata.items():
        annotated = [k for k in keys if k in labels]
        if not annotated:
            raise ValueError(f"stratum {name!r} has no annotated header")
        n, size = len(annotated), len(keys)
        values = [test(labels[k], by[k]) for k in annotated]
        mean = sum(values) / n
        total += size * mean
        if n < size:
            variance += size * size * (1 - n / size) * sum((v - mean) ** 2 for v in values) / max(n - 1, 1) / n
    return total, math.sqrt(variance)


def flat_strata(pool: dict[str, dict[str, list[dict]]]) -> dict[str, list[str]]:
    """`pools` as {"cpp/all": keys, ...}, the empty ones left out."""
    return {f"{label}/{name}": [key(r) for r in rows] for label, sides in pool.items() for name, rows in sides.items() if rows}


def audit_labels(records: list[dict], annotations: dict, strata: dict[str, list[str]]) -> list[str]:
    """What is wrong with the hand annotations against this run's records and strata: a header gone, its content
    changed (sha), its declared label or its stratum not the ones it was annotated in. Empty when they all hold,
    which is what makes the estimate's weights right."""
    by = {key(r): r for r in records}
    stratum = {k: name for name, keys in strata.items() for k in keys}
    problems = []
    for k, note in annotations.items():
        r = by.get(k)
        if r is None:
            problems.append(f"{k}: no such header")
        elif r["sha"] != note["sha"]:
            problems.append(f"{k}: content changed")
        elif r["decl"] != note["declared"] or stratum.get(k) != f"{note['declared']}/{note['stratum']}":
            problems.append(f"{k}: now in {stratum.get(k)}, annotated in {note['declared']}/{note['stratum']}")
    return problems


# ---- the line that shows an error ---------------------------------------------------------------------------

def _first(kinds: dict, tier: frozenset, guarded: bool) -> int | None:
    lines = [v[2] for k, v in kinds.items() if k in tier and v[1 if guarded else 0]]
    return min(lines) if lines else None


def evidence_line(record: dict, route: str, truth: str, answer: str) -> int | None:  # noqa: A002
    """The line a wrong answer can be read from: for a header missed, its first node of the language the route
    did not name; for one misread, the node that misled the route, or the first error of the grammar it should have kept.
    The rule before (R0) has no node of its own: a C header it reads wrong has no line."""
    if answer == truth or truth == "either" or (route == "R0" and truth == "c"):  # R0 has no node to point at
        return None
    f = record["f"]
    if truth == "cpp":
        return _first(f["cpp"]["kinds"], routes.CPP_ALL, False)
    if truth == "objc":
        return _first(f["objc"]["kinds"], routes.OBJC_EXT, False)
    if answer == "cpp" and (route.startswith("R1") or route.startswith("R3")):
        tier = route[2] if route.startswith("R1") else ("e" if route == "R3" else "d")
        guarded = route.startswith("R3") or "g" in route[3:]
        return _first(f["cpp"]["kinds"], routes._CPP_TIER[tier], guarded)
    if answer == "objc" and route.startswith("R1"):
        return _first(f["objc"]["kinds"], routes.OBJC_EXT, False)
    return f["c"]["err_line"] or None


# ---- the summary --------------------------------------------------------------------------------------------

def load(path: Path) -> dict:
    with (gzip.open(path, "rt", encoding="utf-8") if path.suffix == ".gz" else open(path, encoding="utf-8")) as handle:
        return json.load(handle)


def final_label(record: dict, annotations: dict) -> str:
    note = annotations.get(key(record))
    return note["label"] if note else record["decl"]


def _stats(values: list[float]) -> dict:
    return {"median": round(routes.percentile(values, 50), 4), "p95": round(routes.percentile(values, 95), 4),
            "max": round(max(values), 4), "total_s": round(sum(values) / 1000, 2)}


ANSWERS = ("c", "cpp", "objc")


def _estimates(records: list[dict], strata: dict, labels: dict, ans: dict[str, str], base: dict[str, str]) -> dict:
    """For a route: the headers truly of each category, how many of them it reads wrong, and the full matrix (truth ->
    answer), each as [count, standard error]. A header outside the pools (all nine main routes read it as its project
    does) is the declared label: an error of another route there is counted as an error."""
    def at(test):
        count, se = estimate(records, strata, labels, test)
        return [round(count, 1), round(se, 1)]
    def less(t):  # misses of this route minus today's on the same headers: negative is better than R0
        return at(lambda truth, r: (truth == t and ans[key(r)] != t) - (truth == t and base[key(r)] != t))
    return {"total": {t: at(lambda truth, r, t=t: truth == t) for t in CATEGORIES},
            "against_r0": {t: less(t) for t in ("c", "cpp", "objc")},
            "wrong": {t: at(lambda truth, r, t=t: truth == t and ans[key(r)] != t) for t in CATEGORIES if t != "either"},
            "matrix": {t: {a: at(lambda truth, r, t=t, a=a: truth == t and ans[key(r)] == a) for a in ANSWERS} for t in CATEGORIES}}


def _loss(records: list[dict], ans: dict[str, str], truth_of) -> dict:
    """Per `truth>answer` of a C or C++ header read wrong: how many, how many lose symbols, how many they lose and of how
    many the true reading finds. An `objc` answer loses them all (the header is not read)."""
    out = defaultdict(lambda: {"errors": 0, "with_loss": 0, "lost": 0, "of": 0})
    for r in records:
        truth, got = truth_of(r), ans[key(r)]
        if "sym" in r and truth in ("c", "cpp") and got != truth:
            lost, row = routes.symbol_loss(r["sym"], truth, got), out[f"{truth}>{got}"]
            row["errors"] += 1
            row["with_loss"] += lost > 0
            row["lost"] += lost
            row["of"] += r["sym"][truth]
    return dict(out)


def _route_summary(records: list[dict], route: str, annotations: dict, strata: dict, labels: dict, examples: int) -> dict:
    ans = {key(r): answer(r, route) for r in records}
    base = {key(r): answer(r, "R0") for r in records}
    pairs = [(final_label(r, annotations), ans[key(r)]) for r in records]
    m = routes.matrix(pairs)
    errors: dict[str, list] = defaultdict(list)
    for r, (truth, got) in zip(records, pairs):
        if not routes.correct(truth, got):
            errors[f"{truth}>{got}"].append((r, evidence_line(r, route, truth, got)))
    costs = [cost_ms(r, route) for r in records]
    marginals = [marginal_ms(r, route) for r in records]
    size_kb = sum(r["size"] for r in records) / 1024
    return {"matrix": m, "accuracy": {t: list(v) for t, v in routes.accuracy(m).items()},
            "cost_ms": {**_stats(costs), "per_kb": round(sum(costs) / size_kb, 5)}, "marginal_ms": _stats(marginals),
            "errors": {kind: {"count": len(rows), "examples": [{"path": key(r), "line": line, "annotated": key(r) in annotations}
                                                              for r, line in sorted(rows, key=lambda row: key(row[0]) not in annotations)[:examples]]}
                       for kind, rows in errors.items()},  # the hand-annotated ones first: their error is confirmed
            "symbol_loss": _loss(records, ans, lambda r: final_label(r, annotations)),
            "symbol_loss_declared": _loss(records, ans, lambda r: r["decl"]),
            "agreement": sum(routes.correct(note["label"], ans[k]) for k, note in annotations.items() if k in ans),
            "estimate": _estimates(records, strata, labels, ans, base) if strata is not None else None}


def _no_cpp_node(r: dict) -> bool:
    """The C++ parse of the header holds no node that only C++ has."""
    return not any(v[0] for k, v in r["f"]["cpp"]["kinds"].items() if k in routes.CPP_ALL)


def _indifference(records: list[dict], strata: dict, labels: dict) -> dict:
    """How many headers of each declared label are indifferent (any answer is right), by two roads: the annotations
    (an estimate, with its standard error) and the symbols (a census, no annotation: the C reading of the header finds
    as many as the C++ one; and the C++ parse found no node C does not have)."""
    out = {}
    for declared in ("c", "cpp", "objc"):
        rows = [r for r in records if r["decl"] == declared]
        either = None if strata is None else [round(x, 1) for x in estimate(
            records, strata, labels, lambda truth, r, d=declared: truth == "either" and r["decl"] == d)]
        both = [r for r in rows if "sym" in r]
        out[declared] = {"headers": len(rows), "either": either,
                         "c_reading_loses_nothing": sum(r["sym"]["c"] >= r["sym"]["cpp"] for r in both),
                         "same_symbols": sum(r["sym"]["c"] == r["sym"]["cpp"] for r in both),
                         "no_cpp_node": sum(_no_cpp_node(r) for r in rows)}
    return out


def _r0_c_of_cpp(records: list[dict], annotations: dict) -> dict:
    """The headers of C++ projects that the rule before (R0) reads as C: how many, as what the annotated ones were labelled, how
    many would lose symbols and how many, and how many have no C++-only node in the parse."""
    rows = [r for r in records if r["decl"] == "cpp" and r["r0"] != "cpp"]
    lost = [routes.symbol_loss(r["sym"], "cpp", "c") for r in rows]
    truly_cpp = [x for r, x in zip(rows, lost) if annotations.get(key(r), {}).get("label") == "cpp"]
    return {"headers": len(rows), "annotated": dict(Counter(annotations[key(r)]["label"] for r in rows if key(r) in annotations)),
            "with_loss": sum(x > 0 for x in lost), "lost": sum(lost), "of": sum(r["sym"]["cpp"] for r in rows),
            "annotated_cpp_lost": sum(truly_cpp), "no_cpp_node": sum(_no_cpp_node(r) for r in rows)}


def _label_check(records: list[dict], annotations: dict) -> dict:
    """Each hand label against the symbols alone, which no route and no annotator touched: for the headers given a label,
    how many are read with more symbols by C++, by C, or by both alike. An `either` that C++ reads with more symbols, or
    a `cpp` that C reads with more, is a label to doubt."""
    by = {key(r): r for r in records}
    out: dict[str, Counter] = defaultdict(Counter)
    for k, note in annotations.items():
        r = by.get(k)
        if r and "sym" in r:
            relation = "cpp_more" if r["sym"]["cpp"] > r["sym"]["c"] else "c_more" if r["sym"]["c"] > r["sym"]["cpp"] else "same"
            out[note["label"]]["n"] += 1
            out[note["label"]][relation] += 1
    return {label: dict(c) for label, c in out.items()}


def _slowest(records: list[dict], route: str, count: int = 5) -> list[dict]:
    return [{"path": key(r), "size": r["size"], "ms": {g: round(r["f"][g]["ms"], 1) for g in routes.GRAMMARS}, "r0_ms": r["r0ms"]}
            for r in sorted(records, key=lambda r: -cost_ms(r, route))[:count]]


def _r0check(rows: list[dict]) -> dict:
    """The candidates for the rule before (`header_patterns`: fix, fixq, fixqc) against it on every header: how
    many answers differ, and the cost of each (`modal_headers.py --step r0check`)."""
    names = ("r0", "fix", "fixq", "fixqc")
    return {"headers": len(rows), "differ": {name: sum(r[name] != r["r0"] for r in rows) for name in names[1:]},
            "cost_ms": {name: _stats([r["ms"][i] for r in rows]) for i, name in enumerate(names)}}


def summarize(data: dict, annotations: dict, growth: dict | None = None, examples: int = 6, capcost: dict | None = None,
              r0check: dict | None = None) -> dict:
    records = [r for r in data["records"] if "error" not in r]
    labels = {k: v["label"] for k, v in annotations.items()}
    strata = flat_strata(pools(records))
    usable = strata if all(any(k in labels for k in keys) for keys in strata.values()) else None  # an estimate needs a sample of each pool
    names = list(routes.ROUTES) + ["R0"]
    project_label = {p.name: p.label for p in corpus.PROJECTS}  # the project's, not that of its first header (llvm-c is C)
    sizes = [r["size"] for r in records]
    out = {"code": data.get("code"), "headers": len(records), "errors": len(data["records"]) - len(records),
           "projects": {}, "labels": dict(Counter(final_label(r, annotations) for r in records)),
           "pools": {name: len(keys) for name, keys in strata.items()},
           "annotated": {name: sum(k in labels for k in keys) for name, keys in strata.items()},
           "annotated_total": len(labels), "label_problems": audit_labels(records, annotations, strata),
           "sizes": {"median": int(routes.percentile(sizes, 50)), "p95": int(routes.percentile(sizes, 95)), "max": max(sizes),
                     **{f"over_{cap}": sum(size > cap for size in sizes) for cap in (4096, 8192, 16384, 32768)}}}
    for r in records:
        row = out["projects"].setdefault(r["p"], {"label": project_label.get(r["p"], r["decl"]), "headers": 0, "bytes": 0})
        row["headers"] += 1
        row["bytes"] += r["size"]
    out["routes"] = {name: _route_summary(records, name, annotations, usable, labels, examples) for name in names}
    out["indifference"] = _indifference(records, usable, labels)
    out["r0_c_of_cpp"] = _r0_c_of_cpp(records, annotations)
    out["label_check"] = _label_check(records, annotations)
    out["slowest"] = _slowest(records, "R2o")
    out["ties"] = _ties(records, annotations)
    out["symbols"] = _symbols(records, annotations)
    out["caps"] = _caps(records, annotations)
    if growth:
        out["growth"] = _growth(growth["rows"])
    if capcost:
        out["capcost"] = _capcost(records, capcost["rows"])
    if r0check:
        out["r0check"] = _r0check(r0check["rows"])
    return out


def _ties(records: list[dict], annotations: dict) -> dict:
    """How often the error counts of C and C++ (and of the three) are equal: the cases a tie order decides."""
    out: dict[str, Counter] = defaultdict(Counter)
    for r in records:
        scores = [r["f"][g]["err"] + r["f"][g]["missing"] for g in routes.GRAMMARS]
        label = final_label(r, annotations)
        out[label]["n"] += 1
        out[label]["tie_c_cpp"] += scores[0] == scores[1]
        out[label]["tie_all"] += scores[0] == scores[1] == scores[2]
        out[label]["clean_c_and_cpp"] += scores[0] == scores[1] == 0
    return {label: dict(c) for label, c in out.items()}


def _symbols(records: list[dict], annotations: dict) -> dict:
    """What reading every header of a label with the other language costs in definitions Daodan extracts."""
    out: dict[str, Counter] = defaultdict(Counter)
    for r in records:
        if "sym" not in r:
            continue
        label = final_label(r, annotations)
        for g in ("c", "cpp"):
            out[label][g] += r["sym"][g]
        out[label]["n"] += 1
        out[label]["cpp_more"] += r["sym"]["cpp"] > r["sym"]["c"]
        out[label]["c_more"] += r["sym"]["c"] > r["sym"]["cpp"]
    return {label: dict(c) for label, c in out.items()}


def _caps(records: list[dict], annotations: dict) -> dict:
    """What a cap costs in right answers and in symbols when only the first `cap` bytes are read: `cut` at a line, `safe`
    also before an open `/*`. Per cap, mode and route: the accuracy by label (raw, as `matrix`) and the symbol loss."""
    out: dict = {}
    for cap in ("none", *map(str, (4096, 8192, 16384, 32768))):
        for mode in (("full",) if cap == "none" else ("cut", "safe")):
            for route in ("R0", "R1dg", "R1eg", "R1ego", "R2", "R2o", "R3"):
                ans = {}
                for r in records:
                    shown = r.get("caps", {}).get(cap, {}).get(mode, {}) if cap != "none" else {}  # a header within the cap has none
                    ans[key(r)] = shown.get(route) or answer(r, route)
                pairs = [(final_label(r, annotations), ans[key(r)]) for r in records]
                out.setdefault(cap, {}).setdefault(mode, {})[route] = {
                    "accuracy": {t: list(v) for t, v in routes.accuracy(routes.matrix(pairs)).items()},
                    "loss": _loss(records, ans, lambda r: final_label(r, annotations))}
    return out


CAPCOST_ROUTES = ("R0", "R1eg", "R1ego", "R2", "R2o", "R3d")  # a route of each family, with and without the Objective-C grammar


def _capcost(records: list[dict], rows: list[dict]) -> dict:
    """Cost per header, by route and byte cap, when the product cuts a header longer than the cap (`modal_headers.py
    --step capcost`): a header within the cap costs what it did, one beyond it costs its prefix; the routes on a grammar
    also pay the check before the parse (`scan_ms`)."""
    caps = {key(r): r["caps"] for r in rows}
    out: dict = {}
    for route in CAPCOST_ROUTES:
        for cap in sorted({c for r in rows for c in r["caps"]}, key=int):
            costs = []
            for r in records:
                entry = caps[key(r)][cap]
                if route == "R0":
                    costs.append(entry.get("r0_cut", r["r0ms"]))
                else:
                    own = entry.get("safe") or {g: r["f"][g]["ms"] + r["f"][g]["q_ms"] for g in routes.GRAMMARS}
                    costs.append(sum(own[g] for g in routes.needs(route, features(r))) + entry["scan_ms"])
            out.setdefault(route, {})[cap] = _stats(costs)
    return out


def _growth(rows: list[dict]) -> dict:
    """ms by size for each (target, kind, mode), t(2n)/t(n), and the first timeout."""
    series: dict[str, dict] = defaultdict(lambda: {"ms": {}, "timeout": None})
    for row in rows:
        entry = series[f"{row['target']}|{row['kind']}|{row['mode']}"]
        if "timeout" in row:
            entry["timeout"] = {"size": row["size"], "seconds": row["timeout"]}
        elif "ms" in row:
            entry["ms"][row["size"]] = row["ms"]
    out = {}
    for name, e in series.items():
        slope = routes.exponent(e["ms"])
        out[name] = {"ms": e["ms"], "ratios": [[n, round(x, 2)] for n, x in routes.growth(e["ms"])], "timeout": e["timeout"],
                     "exponent": None if slope is None else round(slope, 2)}
    return out


def build(results: Path, labels: Path) -> dict:
    """The summary of everything `results` holds: the records, every `growth*.json`, and the capcost and r0check files if
    they are there, against the hand annotations in `labels`."""
    files = sorted(results.glob("growth*.json"))
    growth = {"rows": [row for f in files for row in load(f)["rows"]]} if files else None
    optional = {name: load(results / f"{name}.json.gz") if (results / f"{name}.json.gz").exists() else None for name in ("capcost", "r0check")}
    return summarize(load(results / "headers.json.gz"), json.loads(labels.read_text(encoding="utf-8")) if labels.exists() else {}, growth, **optional)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", default=str(HERE / "results"), help="the folder of headers.json.gz, growth*.json, capcost.json.gz, r0check.json.gz")
    parser.add_argument("--labels", default=str(HERE / "labels.json"))
    parser.add_argument("--out", default="", help="default: summary.json in the results folder")
    parser.add_argument("--sample", default="", help="totals for cpp,c,objc (90,30,25): print the keys to annotate")
    args = parser.parse_args()
    results = Path(args.results)
    if args.sample:
        pool = pools([r for r in load(results / "headers.json.gz")["records"] if "error" not in r])
        for label, total in zip(("cpp", "c", "objc"), map(int, args.sample.split(","))):
            strata = {name: [key(r) for r in rows] for name, rows in pool[label].items() if rows}
            keys = annotation_sample(strata, total, seed=f"annotate-{label}")
            for name, keys_of in sorted(strata.items()):
                for k in sorted(set(keys) & set(keys_of)):
                    print(label, name, k)
        return
    summary = build(results, Path(args.labels))
    out = Path(args.out) if args.out else results / "summary.json"
    out.write_text(json.dumps(summary, indent=1), encoding="utf-8")
    print(f"wrote {out}: {summary['headers']} headers, {summary['annotated_total']} annotated, {len(summary['label_problems'])} label problems")


if __name__ == "__main__":
    main()
