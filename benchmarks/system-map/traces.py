#!/usr/bin/env python3
"""Trace cards: the model finds, corrects and certifies flows on edges the machine has; it does not guess from names.

    python traces.py cards LINKS.json ENTRY_GLOB OUT.json [--limit 20] [--source ARCHIVE_OR_FOLDER]
    GATEWAY_URL=... GATEWAY_KEY=... GATEWAY_MODEL=... python traces.py ask CARDS.json OUT.json
    python traces.py verify CARDS.json ANSWERS.json LINKS.json OUT.json [--source ARCHIVE_OR_FOLDER]

A proof of the plan's Task C4 (20 November 2026), on the links of a run (`links.json`); it opens files and runs
nothing. The contract, in four points:

1. Find. A card is the typed, numbered edges an entry reaches (`A --[chiama|onSubmit|HTTP POST /x|scrive]--> B`, each
   the edge of the links with its `file:line`), kept only on the branches that reach an effect (a store, a service of
   others) or a point where the links stop. What leads nowhere (a logo, a formatter) and what most entries reach (the
   shell) is left out and counted.
2. Correct. Where a chain stops, the card shows that point of the source. The model either cites a line of it with
   its exact text, saying what is reached there, or records the gap with its cause. It never continues by guess.
3. Certify. A flow is a contiguous chain of edge numbers from the entry to an effect; a card may give no flow.
4. Verify. Before a flow counts, `verify` checks that every cited edge is in the links, that the chain is contiguous
   from the entry, that the cited lines exist and that a correction's text is on its line. The rest is refused with
   its reason, never promoted.

An entry is a candidate of the core's residual reader (`daodan/core/entries.py`: a symbol that calls and that
nothing calls), in a file matching ENTRY_GLOB. `ask` gives one card per
request to a model behind an OpenAI-compatible address, the key from the environment only.
"""
from __future__ import annotations

import fnmatch
import json
import os
import sys
import tarfile
import urllib.request
from collections import Counter, defaultdict, deque
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from daodan.core import entries as readers  # noqa: E402  the core's readers of entries; `entries.py` here is the measure

STEPS = 60      # the edges a card shows at most
COMMON = 0.15   # a symbol more than this share of the entries reach is common to them, not a step of one
WINDOW = 4      # the lines of source shown around a point where the links stop; a correction cites one of them
END = ("store:", "module:")  # where a chain arrives: a store, a service or a project of others
AREAS = ("accesso e identità", "funzioni principali", "pagamenti e abbonamenti", "dati dell'utente",
         "integrazioni esterne", "comunicazioni", "amministrazione", "esercizio")
READ = ("Archi che il codice esegue davvero, da un ingresso. Ogni riga numerata è un arco "
        "SORGENTE --[tipo]--> DESTINAZIONE, con file e riga. Il rientro dice la catena: una riga più rientrata parte "
        "dalla destinazione della riga meno rientrata sopra di lei; due righe con lo stesso rientro sono rami diversi, "
        "non una sequenza. «◼ effetto» chiude una catena: lì il dato arriva. Un arco «lacuna» è un punto dove i "
        "collegamenti si fermano: sotto c'è quel punto del sorgente, con i numeri di riga.")
ASK = ("Quali flussi sono provati da questi archi? Rispondi solo con JSON: "
       '{"flussi": [{"nome": "...", "area": "...", "passi": [numeri]}], '
       '"correzioni": [{"passo": numero, "riga": "file:riga", "testo": "...", "verso": "..."}], '
       '"lacune": [{"passo": numero, "causa": "..."}]}. '
       "Un flusso è una catena contigua di archi dall'ingresso a un effetto: la sorgente del primo arco è l'ingresso, "
       "la sorgente di ogni arco è la destinazione del precedente, l'ultimo è un «◼ effetto». Se nessuna catena arriva "
       "a un effetto, \"flussi\" è []. Dove una catena finisce su una «lacuna» non indovinare il seguito: leggi il "
       "sorgente sotto di lei. Se una riga dice che cosa viene raggiunto (un indirizzo, una chiave, un servizio) dai "
       "una correzione con quella riga, il suo testo esatto e in «verso» che cosa raggiunge: allora un flusso può "
       "finire su quel passo. Altrimenti metti il passo in \"lacune\" con la causa. Al massimo 5 flussi. Il nome è il "
       "sostantivo dell'azione e il suo oggetto, in italiano, con le parole del prodotto (Pagamento dell'abbonamento), "
       "mai un verbo, mai «Gestione». L'area è una di: " + ", ".join(AREAS) + ".")


class Source:
    """The project's files as the run saw them, from a code archive or a folder: opened, never run."""

    def __init__(self, path: Path | str):
        self.root, self.cache = Path(path), {}
        self.tar = tarfile.open(self.root) if self.root.is_file() else None

    def lines(self, rel: str) -> list[str] | None:
        if rel not in self.cache:
            try:
                data = self.tar.extractfile(rel).read() if self.tar else (self.root / rel).read_bytes()
                self.cache[rel] = data.decode("utf-8", "replace").splitlines()
            except (KeyError, OSError, AttributeError):
                self.cache[rel] = None
        return self.cache[rel]


def label(edge: dict) -> str:
    """What an edge is, as a card shows it: the route it calls, the event that activates, or its type."""
    if edge.get("route"):
        return "HTTP " + " ".join(edge["route"][1:])
    return edge.get("label") or edge.get("type", "chiama")


def moves(links: dict) -> tuple[dict, dict, set[str]]:
    """Per symbol the edges that leave it (a read leaves its reader, towards the store) and the points where the
    links stop inside it; and the symbols something calls."""
    out, stops, called = defaultdict(list), defaultdict(list), set()
    for index, edge in enumerate(links["edges"]):
        if edge.get("type") == "legge" and edge["from"].startswith("store:"):
            out[edge["to"]].append((edge["from"], "legge", edge.get("site", ""), index))
        else:
            out[edge["from"]].append((edge["to"], label(edge), edge.get("site", ""), index))
            called.add(edge["to"])
    for index, gap in enumerate(links.get("gaps", ())):
        if gap.get("symbol"):
            stops[gap["symbol"]].append((gap.get("reason", ""), gap.get("site", ""), index))
    return out, stops, called


def reached(out: dict, entry: str) -> set[str]:
    """The symbols an entry reaches."""
    seen, queue = {entry}, deque([entry])
    while queue:
        for target, *_ in out.get(queue.popleft(), ()):
            if target not in seen and not target.startswith(END):
                seen.add(target)
                queue.append(target)
    return seen - {entry}


def branches(out: dict, stops: dict, entry: str, skip: set[str]) -> tuple[dict, int]:
    """The tree from an entry, each symbol under the nearest one that reaches it: per symbol its edges and the points
    where the links stop in it; and how many edges go to a symbol common to most entries."""
    seen, queue, tree, common = {entry}, deque([entry]), defaultdict(list), 0
    while queue:
        source = queue.popleft()
        for target, kind, site, index in out.get(source, ()):
            end = target.startswith(END)
            if target in skip:
                common += 1
                continue
            if not end:
                if target in seen:
                    continue
                seen.add(target)
                queue.append(target)
            tree[source].append({"from": source, "to": target, "type": kind, "site": site, "edge": index,
                                 "end": "effetto" if end else None})
        tree[source] += [{"from": source, "to": "?", "type": "lacuna", "site": site, "gap": index, "end": "lacuna",
                          "reason": reason} for reason, site, index in stops.get(source, ())]
    return tree, common


def kept(tree: dict, entry: str) -> tuple[list[dict], int]:
    """The edges on a branch that reaches an end, as a person reads a tree, each with its depth; and how many edges
    lead nowhere."""
    order, stack = [], [entry]
    while stack:
        order.append(stack.pop())
        stack += [step["to"] for step in tree.get(order[-1], ()) if not step["end"]]
    useful = set()
    for node in reversed(order):  # a symbol comes after the one that reaches it
        if any(step["end"] or step["to"] in useful for step in tree.get(node, ())):
            useful.add(node)
    steps, stack = [], [(step, 0) for step in reversed(tree.get(entry, ()))]
    while stack:
        step, depth = stack.pop()
        if step["end"] or step["to"] in useful:
            steps.append({**step, "depth": depth})
            if not step["end"]:
                stack += [(below, depth + 1) for below in reversed(tree.get(step["to"], ()))]
    return steps, sum(len(found) for found in tree.values()) - len(steps)


def excerpt(source: Source, site: str) -> dict | None:
    """The lines of the source around a site."""
    rel, _, line = site.rpartition(":")
    lines = source.lines(rel) if line.isdigit() else None
    if not lines or not 1 <= int(line) <= len(lines):
        return None
    first = max(1, int(line) - WINDOW)
    return {"file": rel, "first": first, "lines": lines[first - 1:int(line) + WINDOW]}


def cards(links: dict, pattern: str, limit: int | None = None, source: Source | None = None) -> list[dict]:
    """One card per entry whose file matches `pattern`."""
    out, stops, _ = moves(links)
    entries = sorted(c["symbol"] for c in readers.residual(links) if fnmatch.fnmatchcase(c["symbol"].split("::")[0], pattern))
    holders = Counter(symbol for entry in entries for symbol in reached(out, entry))
    skip = {symbol for symbol, count in holders.items() if count > max(2, int(len(entries) * COMMON))}
    made = []
    for entry in entries[:limit]:
        tree, common = branches(out, stops, entry, skip)
        steps, pruned = kept(tree, entry)
        for n, step in enumerate(steps[:STEPS], 1):
            step["n"] = n
            if step["end"] == "lacuna" and source is not None:
                step["excerpt"] = excerpt(source, step["site"])
        made.append({"entry": entry, "steps": steps[:STEPS], "more": max(0, len(steps) - STEPS), "pruned": pruned,
                     "common": common})
    return made


def text(card: dict) -> str:
    """A card as the model reads it: how to read it, the edges, the question last."""
    lines = [f"<come_leggere>{READ}</come_leggere>",
             f'<percorso parte_da="{card["entry"].split("::")[0]}" ingresso="{card["entry"].split("::", 1)[-1]}">']
    for step in card["steps"]:
        pad, source, target = "  " * step["depth"], step["from"].split("::", 1)[-1], step["to"].split("::", 1)[-1]
        head = f'{pad}{step["n"]}. {source} --[{step["type"]}]--> {target}'
        if step["end"] == "lacuna":
            lines.append(f'{head}  ⚠ {step["reason"]}  (in {step["site"]})')
            if step.get("excerpt"):
                shown = step["excerpt"]
                lines.append(f'{pad}<sorgente {shown["file"]}:{shown["first"]}-{shown["first"] + len(shown["lines"]) - 1}>')
                lines += [f'{pad}{shown["first"] + i}| {line}' for i, line in enumerate(shown["lines"])]
                lines.append(f"{pad}</sorgente>")
        elif step["end"]:
            lines.append(f'{head}  ◼ effetto  (chiamata in {step["site"]})')
        else:
            lines.append(f'{head}  —  {step["to"].split("::")[0]}  (chiamata in {step["site"]})')
    if card["more"]:
        lines.append(f"… altri {card['more']} archi")
    return "\n".join([*lines, "</percorso>", f"<domanda>{ASK}</domanda>"])


def _line_exists(source: Source, site: str) -> bool:
    rel, _, line = site.rpartition(":")
    lines = source.lines(rel) if line.isdigit() else None
    return bool(lines) and 1 <= int(line) <= len(lines)


def _correction(by: dict, item: dict, source: Source | None) -> str | None:
    """Why a correction does not hold: it cites a line of the source shown under a gap, with a text that is there."""
    step = by.get(item.get("passo"))
    if step is None or step["end"] != "lacuna":
        return "il passo non è una lacuna"
    if source is None:
        return "senza il sorgente la correzione non si può verificare"
    rel, _, line = str(item.get("riga", "")).rpartition(":")
    shown, _, at = step["site"].rpartition(":")
    if rel != shown or not line.isdigit() or not at.isdigit() or abs(int(line) - int(at)) > WINDOW:
        return "la riga non è nel sorgente mostrato"
    lines, said = source.lines(rel) or [], str(item.get("testo", "")).strip()
    if len(said) < 4 or not 1 <= int(line) <= len(lines) or said not in lines[int(line) - 1]:
        return "il testo non è su quella riga"
    return None


def _in_links(step: dict, links: dict) -> bool:
    """Whether a card's step is the edge, or the gap, of the links it names."""
    if "gap" in step:
        gaps = links.get("gaps", [])
        real = gaps[step["gap"]] if 0 <= step["gap"] < len(gaps) else None
        return bool(real) and real.get("symbol") == step["from"] and real.get("site", "") == step["site"]
    real = links["edges"][step["edge"]] if 0 <= step["edge"] < len(links["edges"]) else None
    return bool(real) and {real["from"], real["to"]} == {step["from"], step["to"]} and real.get("site", "") == step["site"]


def _flow(card: dict, by: dict, flow: dict, links: dict, source: Source | None, corrected: set) -> str | None:
    """Why a flow is not certified."""
    steps = flow.get("passi")
    if not isinstance(steps, list) or not steps or not all(type(n) is int for n in steps):
        return "passi mancanti o non validi"
    missing = [n for n in steps if n not in by]
    if missing:
        return f"archi inesistenti: {missing}"
    for n in steps:
        if not _in_links(by[n], links):
            return f"il passo {n} non è nei collegamenti"
        if source is not None and not _line_exists(source, by[n]["site"]):
            return f"riga inesistente: {by[n]['site']}"
    if by[steps[0]]["from"] != card["entry"]:
        return f"non parte dall'ingresso: passo {steps[0]}"
    broken = next((f"{a}->{b}" for a, b in zip(steps, steps[1:]) if by[a]["end"] or by[a]["to"] != by[b]["from"]), None)
    if broken:
        return f"catena non contigua: {broken}"
    last = by[steps[-1]]
    if last["end"] is None:
        return f"termina senza effetto: passo {steps[-1]}"
    if last["end"] == "lacuna" and steps[-1] not in corrected:
        return f"termina su una lacuna non corretta: passo {steps[-1]}"
    return None


def verify(card: dict, answer: dict | None, links: dict, source: Source | None = None) -> dict:
    """What of a model's answer holds: the flows certified and refused, the corrections, and the gaps left, each with
    the model's cause when it gave one."""
    by = {step["n"]: step for step in card.get("steps", ())}
    answer = answer if isinstance(answer, dict) else {}
    held, refused, accepted, rejected = [], [], [], []
    for item in answer.get("correzioni") or ():
        why = _correction(by, item, source) if isinstance(item, dict) else "correzione non valida"
        refused.append({"correction": item, "reason": why}) if why else held.append(item)
    corrected = {item["passo"] for item in held}
    for flow in answer.get("flussi") or ():
        why = _flow(card, by, flow, links, source, corrected) if isinstance(flow, dict) else "flusso non valido"
        rejected.append({"flow": flow, "reason": why}) if why else accepted.append(flow)
    causes = {gap.get("passo"): gap.get("causa") for gap in answer.get("lacune") or () if isinstance(gap, dict)}
    gaps = [{"passo": n, "site": step["site"], "reason": step["reason"], "causa": causes.get(n)}
            for n, step in by.items() if step["end"] == "lacuna" and n not in corrected]
    return {"accepted": accepted, "rejected": rejected, "corrections": {"accepted": held, "rejected": refused},
            "gaps": gaps, "lines_checked": source is not None}


def _decode_json(said: str) -> dict | None:
    """First JSON object found in `said`, tolerating stray braces before or after it."""
    decoder, pos = json.JSONDecoder(), 0
    while (start := said.find("{", pos)) >= 0:
        try:
            obj, _ = decoder.raw_decode(said, start)
            if isinstance(obj, dict):
                return obj
        except ValueError:
            pass
        pos = start + 1
    return None


def ask(card: dict, url: str, key: str, model: str) -> dict:
    """The model's answer to one card, as it gave it, and the JSON read from it when it is JSON."""
    body = {"model": model, "temperature": 0, "max_tokens": 2000, "messages": [{"role": "user", "content": text(card)}]}
    request = urllib.request.Request(url.rstrip("/") + "/v1/chat/completions", data=json.dumps(body).encode("utf-8"),
                                     headers={"Authorization": f"Bearer {key}", "content-type": "application/json"})
    with urllib.request.urlopen(request, timeout=300) as response:
        answer = json.load(response)
    said = answer["choices"][0]["message"].get("content") or ""
    read = _decode_json(said)
    return {"entry": card["entry"], "said": said, "answer": read, "usage": answer.get("usage")}


def _option(argv: list[str], name: str) -> str | None:
    """The value of an option, taken out of the arguments."""
    if name not in argv:
        return None
    at = argv.index(name)
    if at + 1 >= len(argv):
        raise ValueError(f"missing value for {name}")
    value = argv[at + 1]
    del argv[at:at + 2]
    return value


def _load(path: str):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _save(path: str, value) -> None:
    Path(path).write_bytes(json.dumps(value, ensure_ascii=False, indent=1).encode("utf-8"))


def main(argv: list[str]) -> int:
    argv = list(argv)
    try:
        limit, files = _option(argv, "--limit"), _option(argv, "--source")
    except ValueError:
        print(__doc__)
        return 2
    source = Source(files) if files else None
    if len(argv) == 5 and argv[1] == "cards":
        made = cards(_load(argv[2]), argv[3], int(limit) if limit else None, source)
        _save(argv[4], made)
        print(json.dumps({"cards": len(made), "with_edges": sum(1 for c in made if c["steps"]),
                          "edges": sum(len(c["steps"]) for c in made), "pruned": sum(c["pruned"] for c in made),
                          "gaps": sum(1 for c in made for s in c["steps"] if s["end"] == "lacuna")}))
        return 0
    if len(argv) == 4 and argv[1] == "ask":
        url, key, model = (os.environ[name] for name in ("GATEWAY_URL", "GATEWAY_KEY", "GATEWAY_MODEL"))
        answers = [ask(card, url, key, model) for card in _load(argv[2]) if card["steps"]]
        _save(argv[3], answers)
        print(json.dumps({"asked": len(answers), "read": sum(1 for a in answers if a["answer"] is not None)}))
        return 0
    if len(argv) == 6 and argv[1] == "verify":
        by_entry, links, answers = {card["entry"]: card for card in _load(argv[2])}, _load(argv[4]), _load(argv[3])
        matched = [a for a in answers if a["entry"] in by_entry]
        report = [{"entry": a["entry"], **verify(by_entry[a["entry"]], a.get("answer"), links, source)}
                  for a in matched]
        _save(argv[5], report)
        print(json.dumps({"checked": len(report),
                          "unparsed": sum(1 for a in matched if a.get("answer") is None),
                          "accepted": sum(len(r["accepted"]) for r in report),
                          "rejected": dict(Counter(x["reason"].split(":")[0] for r in report for x in r["rejected"])),
                          "corrections": sum(len(r["corrections"]["accepted"]) for r in report),
                          "corrections_refused": sum(len(r["corrections"]["rejected"]) for r in report),
                          "gaps": sum(len(r["gaps"]) for r in report),
                          "gaps_with_cause": sum(1 for r in report for g in r["gaps"] if g["causa"]),
                          "lines_checked": source is not None}))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
