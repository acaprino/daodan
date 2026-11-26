"""The tables of the README, written from the JSON the benchmark leaves (`results/summary.json`, `results/loc.json`), so no
number of the README is typed by hand. Standard library only.

    python benchmarks/header-language/header_tables.py            # print the tables
    python benchmarks/header-language/header_tables.py --write    # replace the blocks of README.md

A block of the README is `<!-- table:NAME -->` ... `<!-- /table -->`; `test_header_tables.py` fails when a block is not what
this module writes from the JSON in `results/`.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


HERE = Path(__file__).resolve().parent
LABELS = {"c": "C", "cpp": "C++", "objc": "Objective-C", "either": "indifferenti"}
MAIN = ("R0", "R1dg", "R1eg", "R1dgo", "R1ego", "R2", "R2o", "R3", "R3d")
ROWS = MAIN + ("R1dx", "R1ex", "R3dx")  # the routes the tables compare: the nine of the pools, and three with the Objective-C rule in front
SHOWN = ("R0", "R1eg", "R1dx", "R3d")  # the routes whose matrix and examples are shown: the rule before, the best R1 on C++, the hybrid, the best R3
WAY = {"R0": "R0 regola di prima", "R1dg": "R1 nodi dichiarazione, guardia", "R1eg": "R1 nodi + espressioni, guardia",
       "R1dgo": "R1 dichiarazione, guardia, ObjC prima", "R1ego": "R1 espressioni, guardia, ObjC prima",
       "R2": "R2 meno ERROR, C e C++", "R2o": "R2 meno ERROR, C, C++, ObjC", "R3": "R3 nodi, poi meno ERROR",
       "R3d": "R3 (dichiarazioni, poi meno ERROR)", "R1dx": "R1 dichiarazioni, senza guardia, regola ObjC davanti",
       "R1ex": "R1 espressioni, senza guardia, regola ObjC davanti", "R3dx": "R3 (dichiarazioni, poi meno ERROR) senza grammatica ObjC, regola ObjC davanti"}
BS = chr(92)  # the backslash of the regular expressions the table names
BAD = ("blank_lines", "open_comment", "open_comment_repeat", "open_comment_lines", "class_repeat", "nested_brace", "open_string",
       "escaped_dq", "escaped_sq")
TARGETS = ("r0", "r0fix", "r0fixq", "r0fixqc", "c", "cpp", "scan")  # the Objective-C grammar grows as the C one: it is in summary.json
CAP = "8192"


def est(pair: list[float], digits: int = 1) -> str:
    return f"{pair[0]:.{digits}f} ± {pair[1]:.{digits}f}"


def table(header: list[str], rows: list[list]) -> str:
    lines = ["| " + " | ".join(header) + " |", "|" + "|".join(" --- " for _ in header) + "|"]
    lines += ["| " + " | ".join(str(cell) for cell in row) + " |" for row in rows]
    return "\n".join(lines)


def corpus(summary: dict, loc: dict) -> str:
    rows = []
    for label in ("c", "cpp", "objc"):
        parts = [p for p in summary["projects"].values() if p["label"] == label]
        rows.append([LABELS[label], len(parts), f"{sum(p['headers'] for p in parts):,}", f"{sum(p['bytes'] for p in parts) / 2**20:.1f}"])
    sizes = summary["sizes"]
    out = table(["Etichetta del progetto", "Progetti", "Header", "MB"], rows)
    return out + (f"\n\nGrandezza di un header: mediana {sizes['median']:,} byte, p95 {sizes['p95']:,}, massimo {sizes['max']:,}; "
                  f"{sizes['over_8192']:,} sopra 8 KB, {sizes['over_16384']:,} sopra 16 KB, {sizes['over_32768']:,} sopra 32 KB.")


def truth(summary: dict, loc: dict) -> str:
    rows = []
    for label in ("c", "cpp", "objc"):
        row, pooled = summary["indifference"][label], [k for k in summary["pools"] if k.startswith(label + "/")]
        either = est(row["either"]) if row["either"] else "—"
        rows.append([LABELS[label], f"{row['headers']:,}", sum(summary["pools"][k] for k in pooled), sum(summary["annotated"][k] for k in pooled),
                     either, f"{row['same_symbols']:,}", f"{row['c_reading_loses_nothing']:,}", f"{row['no_cpp_node']:,}"])
    first = table(["Header di progetti", "Header", "In un pool", "Annotati", "Indifferenti (stima ± e.s.)",
                   "Stessi simboli letti C o C++", "Letto C non perde nulla", "Nessun nodo solo-C++"], rows)
    r0, check = summary["r0_c_of_cpp"], summary["label_check"]
    notes = ", ".join(f"{n} {LABELS.get(k, k)}" for k, n in sorted(r0["annotated"].items(), key=lambda kv: -kv[1]))
    return first + (f"\n\nI {r0['headers']} header di progetti C++ che la regola di prima legge C: {sum(r0['annotated'].values())} annotati ({notes}); "
                    f"{r0['with_loss']} perdono simboli ({r0['lost']} su {r0['of']} che hanno); {r0['no_cpp_node']} non hanno alcun nodo solo-C++ nell'albero."
                    f"\n\nLe etichette a mano contro i soli simboli: {check['either']['same']} dei {check['either']['n']} «indifferenti» danno gli stessi simboli letti C o C++; "
                    f"dei {check['cpp']['n']} «C++», {check['cpp']['cpp_more']} ne danno di più letti C++, {check['cpp']['same']} gli stessi, {check['cpp'].get('c_more', 0)} di meno.")


def right(summary: dict, loc: dict) -> str:
    first = summary["routes"]["R0"]["estimate"]["total"]
    rows = []
    for name in ROWS:
        route = summary["routes"][name]
        cells = [f"{est(route['estimate']['wrong'][t])} ({100 * (1 - route['estimate']['wrong'][t][0] / first[t][0]):.1f}%)" for t in ("c", "cpp", "objc")]
        rows.append([WAY[name], *cells, f"{route['agreement']}/{summary['annotated_total']}"])
    totals = ", ".join(f"{LABELS[t]} {est(first[t])}" for t in ("c", "cpp", "objc", "either"))
    return table(["Via", f"C sbagliati su {first['c'][0]:.0f}", f"C++ sbagliati su {first['cpp'][0]:.0f}",
                  f"ObjC sbagliati su {first['objc'][0]:.0f}", "Accordo con le etichette a mano"], rows) + f"\n\nVeri per categoria (stima ± e.s.): {totals}."


def versus(summary: dict, loc: dict) -> str:
    """Each route's misses minus R0's on the same headers (a difference of the two, with its own error): the comparison
    that does not carry the doubt about which headers are truly of a label, which both routes share."""
    rows = [[WAY[name], *(f"{summary['routes'][name]['estimate']['against_r0'][t][0]:+.1f} ± {summary['routes'][name]['estimate']['against_r0'][t][1]:.1f}"
                          for t in ("c", "cpp", "objc"))] for name in ROWS if name != "R0"]
    r0 = summary["r0_c_of_cpp"]
    return table(["Via", "C: sbagliati in più", "C++: sbagliati in più", "ObjC: sbagliati in più"], rows) + (
        f"\n\nDa dove viene il vantaggio sul C++: gli header annotati «C++» che R0 legge C sono {r0['annotated'].get('cpp', 0)} e perdono {r0['annotated_cpp_lost']} simboli; "
        f"i simboli che R0 perde sul C++ ({r0['lost']}) stanno in {r0['with_loss']} header, tutti non annotati.")


def matrix(summary: dict, loc: dict) -> str:
    rows = []
    for name in SHOWN:
        for truth_label in ("c", "cpp", "objc", "either"):
            cells = summary["routes"][name]["estimate"]["matrix"][truth_label]
            rows.append([WAY[name] if truth_label == "c" else "", LABELS[truth_label], *(est(cells[a]) for a in ("c", "cpp", "objc"))])
    return table(["Via", "Vero", "letto C", "letto C++", "letto ObjC"], rows)


def examples(summary: dict, loc: dict) -> str:
    lines = []
    for name in SHOWN:
        for kind, row in sorted(summary["routes"][name]["errors"].items()):
            if kind.startswith("objc>") and not any(row.get("objc") for row in summary["routes"][name]["matrix"].values()):
                continue  # a route with no Objective-C answer misses all of them: no example says more than the count
            shown = ", ".join(f"`{e['path']}{':' + str(e['line']) if e['line'] else ''}`{'' if e['annotated'] else '*'}" for e in row["examples"][:2])
            lines.append(f"- {WAY[name]}, {kind.replace('>', ' letto ')}: {row['count']} (es. {shown})")
    return "\n".join(lines) + "\n\n`*` = non annotato a mano: la sua etichetta è quella del progetto."


def loss(summary: dict, loc: dict) -> str:
    def cell(route: dict, kind: str) -> str:
        row = route["symbol_loss"].get(kind)
        return f"{row['errors']} / {row['with_loss']} / {row['lost']} di {row['of']}" if row else "0"
    rows = []
    for name in ROWS:
        route = summary["routes"][name]
        everything = sum(row["lost"] for row in route["symbol_loss"].values())
        unread = [row for kind, row in route["symbol_loss"].items() if kind.endswith(">objc")]
        rows.append([WAY[name], cell(route, "cpp>c"), cell(route, "c>cpp"),
                     f"{sum(row['errors'] for row in unread)} header, {sum(row['lost'] for row in unread)} simboli" if unread else "0", everything])
    return table(["Via", "C++ letto C: header / con perdita / simboli persi", "C letto C++: header / con perdita / simboli persi",
                  "C o C++ letto ObjC (non letto affatto)", "Simboli persi in tutto"], rows)


def loss_declared(summary: dict, loc: dict) -> str:
    """The same losses with no annotation at all (the label is the project's): one sentence, since an indifferent header
    loses nothing whichever way it is read."""
    def pick(route: dict, field: str) -> list:
        return [(route[field].get(kind) or {}).get(count) for kind in ("cpp>c", "c>cpp") for count in ("with_loss", "lost")]
    differ = [WAY[name] for name in ROWS if pick(summary["routes"][name], "symbol_loss") != pick(summary["routes"][name], "symbol_loss_declared")]
    if not differ:
        return ("Con la sola etichetta del progetto, senza alcuna annotazione, gli header con perdita e i simboli persi (C++ letto C, C letto C++) "
                "sono gli stessi in tutte le vie: un header indifferente non perde nulla comunque lo si legga.")
    return "Con la sola etichetta del progetto le perdite cambiano in: " + ", ".join(differ) + " (summary.json, `symbol_loss_declared`)."


def cost(summary: dict, loc: dict) -> str:
    """The cost of a header by route: total, and marginal (what is not paid anyway: the product parses the header with the
    grammar of its language after the detection, so a parse the route made with that grammar is not paid twice)."""
    def ms(stats: dict) -> str:
        return f"{stats['median']:.2f} / {stats['p95']:.1f} / {stats['max']:,.0f}"
    capped, rows = summary.get("capcost", {}), []
    for name in ("R0", "R1dg", "R1eg", "R1dx", "R1ex", "R1ego", "R2", "R2o", "R3d", "R3dx"):
        route = summary["routes"][name]
        with_cap = capped.get(name, {}).get(CAP)
        rows.append([WAY[name], f"{route['cost_ms']['total_s']:.1f}", f"{route['marginal_ms']['total_s']:.1f}", ms(route["cost_ms"]),
                     ms(route["marginal_ms"]), f"{with_cap['median']:.2f} / {with_cap['p95']:.1f} / {with_cap['max']:,.1f}" if with_cap else "—"])
    if "r0check" in summary:  # the rule before and its candidate from the same run: they are the two rows to compare
        for label, field in (("R0 regola di prima (corsa r0check)", "r0"), ("R0 con `fixqc` (ora nel prodotto) (corsa r0check)", "fixqc")):
            raw = summary["r0check"]["cost_ms"][field]
            rows.insert(1 if field == "r0" else 2, [label, f"{raw['total_s']:.1f}", f"{raw['total_s']:.1f}", ms(raw), ms(raw), "—"])
    slow = summary["slowest"][0]
    return table(["Via", "Totale s", "Marginale s", "Totale ms: mediana / p95 / massimo", "Marginale ms: mediana / p95 / massimo",
                  "Con tetto 8 KB, totale ms"], rows) + (
        f"\n\nSu tutte le {summary['headers']:,} header, senza tetto. Marginale = totale meno il parse che il prodotto farebbe comunque con la grammatica "
        f"del linguaggio dato (l'albero si può tenere); la regola di prima non parsa nulla, quindi il suo costo è tutto marginale. "
        f"Le due righe «corsa r0check» sono della stessa corsa e si confrontano tra loro; le altre sono di un'altra corsa, su un altro host. "
        f"Il massimo è `{slow['path']}` ({slow['size']:,} byte, una tabella di numeri): {slow['ms']['c']:,.0f} ms con la grammatica C, "
        f"{slow['ms']['cpp']:,.0f} con C++, {slow['r0_ms']:.0f} ms con la regola di prima; il prodotto la parsa comunque.")


def growth(summary: dict, loc: dict) -> str:
    rows = []
    for kind in BAD:
        cells = []
        for target in TARGETS:
            series = summary["growth"].get(f"{target}|{kind}|raw")
            if series is None:
                cells.append("—")
                continue
            top = max(int(size) for size in series["ms"])
            at = f"{series['ms'][str(top)]:,.0f} ms a {top // 1024} KB"
            if series["timeout"]:
                at = f">{series['timeout']['seconds'] * 1000:,.0f} ms a {series['timeout']['size'] // 1024} KB"
            cells.append(f"{series['exponent']:.1f} ({at})")
        rows.append([f"`{kind}`", *cells])
    check = summary.get("r0check")
    note = "" if check is None else (
        f"\n\nSulle {check['headers']:,} header reali i tre candidati danno le stesse risposte della regola di prima "
        f"(differiscono {check['differ']['fix']}, {check['differ']['fixq']}, {check['differ']['fixqc']}); costo mediano "
        f"{check['cost_ms']['r0']['median']:.2f} / {check['cost_ms']['fix']['median']:.2f} / {check['cost_ms']['fixq']['median']:.2f} / "
        f"{check['cost_ms']['fixqc']['median']:.2f} ms, totale {check['cost_ms']['r0']['total_s']:.1f} / {check['cost_ms']['fix']['total_s']:.1f} / "
        f"{check['cost_ms']['fixq']['total_s']:.1f} / {check['cost_ms']['fixqc']['total_s']:.1f} s (prima / `" + BS + "Z` / + virgolette / + class).")
    return table(["Testo cattivo", "R0 di prima", "R0 con `" + BS + "Z`", "R0 con `" + BS + "Z` e le virgolette", "R0 con `" + BS + "Z`, virgolette e `class`",
                  "Grammatica C", "Grammatica C++", "Controllo lineare"], rows) + note


def caps_bad(summary: dict, loc: dict) -> str:
    def at(target: str, kind: str, mode: str, worst: bool) -> str:
        series = summary["growth"].get(f"{target}|{kind}|{mode}")
        if series is None:
            return "—"
        ms = series["ms"]
        return f"{max(ms.values()) if worst else ms[CAP]:,.1f}"
    rows = [[f"`{kind}`", at("r0", kind, "raw", False), at("cpp", kind, "raw", False), at("cpp", kind, "safe:8192", True), at("scan", kind, "raw", True)]
            for kind in BAD if kind != "blank_lines"]
    return table(["Testo cattivo", "Regola di prima, 8 KB", "Grammatica C++, 8 KB (tetto solo)", "Grammatica C++, tetto e controllo (peggiore)",
                  "Il controllo da solo (fino a 32 KB)"], rows)


def cap_accuracy(summary: dict, loc: dict) -> str:
    rows = []
    for name in ("R0", "R1eg", "R2"):
        for cap, mode in (("none", "full"), ("8192", "safe"), ("16384", "safe"), ("32768", "safe")):
            part = summary["caps"][cap][mode][name]
            acc = part["accuracy"]
            lost = sum(row["lost"] for row in part["loss"].values())
            rows.append([WAY[name] if cap == "none" else "", "nessun tetto" if cap == "none" else f"{int(cap) // 1024} KB",
                         *(acc[t][1] - acc[t][0] for t in ("c", "cpp", "objc")), lost])
    return table(["Via", "Tetto", "C sbagliati (grezzi)", "C++ sbagliati (grezzi)", "ObjC sbagliati (grezzi)", "Simboli persi"], rows)


def worst_growth(summary: dict, targets: tuple[str, ...]) -> str:
    """The steepest growth over the bad texts of the targets a route parses with: the exponent and the text."""
    rows = [(summary["growth"][f"{t}|{k}|raw"]["exponent"], k) for t in targets for k in BAD if f"{t}|{k}|raw" in summary["growth"]]
    exponent, kind = max(rows)
    return f"{exponent:.1f} (`{kind}`)"


def verdict(summary: dict, loc: dict) -> str:
    """One row for each way: wrong answers on C++, right on the others, symbols lost, cost of a header (total and marginal),
    growth on the bad texts, lines of code. The first two rows are the rule before and `fixqc`, now the product's."""
    first = summary["routes"]["R0"]["estimate"]["total"]
    parses = {"R0": ("r0",), "R0c": ("r0fixqc",), "R1dg": ("cpp",), "R1eg": ("cpp",), "R1dx": ("r0", "cpp"), "R1ex": ("r0", "cpp"),
              "R2": ("c", "cpp"), "R2o": ("c", "cpp", "objc"), "R3": ("c", "cpp", "objc"), "R3d": ("c", "cpp", "objc"), "R3dx": ("r0", "c", "cpp")}
    totals = loc["totals"]
    own = {"R0": totals["R0"], "R0c": totals["R0"], "R1dg": totals["R1"], "R1eg": totals["R1"], "R1dx": totals["R1x"], "R1ex": totals["R1x"],
           "R2": totals["R2"], "R2o": totals["R2"], "R3": totals["R3"], "R3d": totals["R3"], "R3dx": totals["R3x"]}
    rows = []
    for name, targets in parses.items():
        route = summary["routes"]["R0" if name == "R0c" else name]
        if name in ("R0", "R0c") and "r0check" in summary:  # the rule before and `fixqc`: one run
            cost_total = marginal = summary["r0check"]["cost_ms"]["r0" if name == "R0" else "fixqc"]
        else:
            cost_total, marginal = route["cost_ms"], route["marginal_ms"]
        added = own[name] + (0 if name in ("R0", "R0c") else totals["check"]) - totals["R0"]
        rows.append([WAY.get(name, "R0 con `fixqc` (ora nel prodotto)"),
                     f"{100 * (1 - route['estimate']['wrong']['c'][0] / first['c'][0]):.1f}%", est(route["estimate"]["wrong"]["cpp"]),
                     f"{100 * (1 - route['estimate']['wrong']['objc'][0] / first['objc'][0]):.1f}%",
                     sum(row["lost"] for row in route["symbol_loss"].values()),
                     f"{cost_total['total_s']:.1f} / {marginal['total_s']:.1f}",
                     f"{marginal['median']:.2f} / {marginal['p95']:.1f} / {marginal['max']:,.0f}", worst_growth(summary, targets), f"{added:+d}"])
    return table(["Via", "C giusti (*)", "C++ sbagliati", "ObjC giusti", "Simboli persi", "Costo s: totale / marginale",
                  "Marginale ms: mediana / p95 / massimo", "Crescita peggiore (esponente)", "Righe rispetto a prima"], rows)


def lines(summary: dict, loc: dict) -> str:
    totals = loc["totals"]
    today, check = totals["R0"], totals["check"]
    rows = [["R0 regola di prima", today, "—", today, "0"], ["R0 con `fixqc` (ora nel prodotto: pattern riscritti, non aggiunti)", today, "—", today, "0"]]
    for label, own in (("R1 nodi C++ (dichiarazioni o espressioni, guardia)", totals["R1"]), ("R1 con la grammatica ObjC", totals["R1+objc"]),
                       ("R1 senza guardia, con la regola ObjC (R1dx, R1ex)", totals["R1x"]), ("R2 meno ERROR (C e C++, o anche ObjC)", totals["R2"]),
                       ("R3 nodi, poi meno ERROR", totals["R3"]), ("R3 senza grammatica ObjC, con la regola ObjC (R3dx)", totals["R3x"])):
        rows.append([label, own, check, own + check, f"{own + check - today:+d}"])
    detection, first_last = loc["today"]["detection"], loc["today"]["detection_range"]
    return table(["Via", "Righe di codice della via", "Più il controllo prima del parse", "Totale", "Rispetto a prima"], rows) + (
        f"\n\nLa regola `.h` del prodotto sono {today} righe di codice (le stesse prima e dopo `fixqc`), di cui {loc['today']['objc_rule']} sono la parte Objective-C (che le vie con «regola ObjC» "
        f"tengono e contano); tutta la parte di rilevamento di `languages/__init__.py` (righe {first_last[0]}-{first_last[1]}) ne ha {detection}.")


TABLES = {"verdict": verdict, "corpus": corpus, "truth": truth, "right": right, "versus": versus, "matrix": matrix, "examples": examples, "loss": loss,
          "loss_declared": loss_declared, "cost": cost, "growth": growth, "caps_bad": caps_bad, "cap_accuracy": cap_accuracy, "lines": lines}
# The markers of the README's own blocks (a text, no code); a block never holds a marker, so an empty one cannot swallow the next.
BLOCK = re.compile(r"(<!-- table:(\w+) -->\n)((?:(?!<!-- /?table).)*)(<!-- /table -->)", re.DOTALL)


def tables(summary: dict, loc: dict) -> dict[str, str]:
    return {name: build(summary, loc) for name, build in TABLES.items()}


def render(readme: str, written: dict[str, str]) -> str:
    """The README with each block replaced by the table of its name; a block with an unknown name raises."""
    def swap(match: re.Match) -> str:
        if match.group(2) not in written:
            raise KeyError(f"no table named {match.group(2)}")
        return match.group(1) + written[match.group(2)] + "\n" + match.group(4)
    return BLOCK.sub(swap, readme)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="replace the table blocks of README.md")
    args = parser.parse_args()
    summary = json.loads((HERE / "results" / "summary.json").read_text(encoding="utf-8"))
    loc = json.loads((HERE / "results" / "loc.json").read_text(encoding="utf-8"))
    written = tables(summary, loc)
    if args.write:
        readme = HERE / "README.md"
        readme.write_text(render(readme.read_text(encoding="utf-8"), written), encoding="utf-8")
        print(f"wrote {readme}")
    else:
        for name, text in written.items():
            print(f"### {name}\n{text}\n")


if __name__ == "__main__":
    main()
