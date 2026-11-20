"""A trace card gives typed, numbered edges from one entry to its effects; the model's answer is accepted only where
every cited edge is in the links, the chain is contiguous from the entry and its lines exist."""
from __future__ import annotations

import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import traces  # noqa: E402


def edge(source: str, target: str, line: int, kind: str = "chiama", **more) -> dict:
    return {"from": source, "to": target, "site": f"{source.split('::')[0]}:{line}", "type": kind, **more}


PAGES = [f"app/p{n}/page.tsx::Page{n}" for n in range(8)]
VIEW, SUBMIT, API, PAY = ("billing/view.tsx::Subscription", "billing/view.tsx::Subscription.handleSubmit",
                          "lib/api.ts::startCheckout", "server/pay.py::checkout")
LINKS = {"edges": [edge(page, "ui/shell.tsx::Shell", 3) for page in PAGES]                 # every page: common
         + [edge("ui/shell.tsx::Shell", "ui/icon.tsx::Icon", 9),
            edge(PAGES[0], VIEW, 5),
            edge(PAGES[0], "ui/brand.tsx::BrandMark", 6),                                    # a logo: it leads nowhere
            edge(VIEW, SUBMIT, 12, "attiva", label="onSubmit"),
            {"from": "store:db/plans", "to": VIEW, "site": "billing/view.tsx:8", "type": "legge"},
            edge(SUBMIT, API, 20),
            edge(API, PAY, 4, route=["api", "POST", "/checkout"], offered="server/pay.py:2"),
            edge(PAY, "store:db/payments", 3, "scrive")],
         "gaps": [{"reason": "rotta: route not a literal", "site": "lib/api.ts:6", "symbol": API}]}
FILES = {"app/p0/page.tsx": "\n" * 8, "billing/view.tsx": "\n" * 25, "server/pay.py": "\n" * 5,
         "lib/api.ts": "a\nb\nc\nd\ne\nreturn request(`/refunds/${id}`, {method: 'POST'})\ng\n"}


def source(tmp_path: Path) -> traces.Source:
    for rel, content in FILES.items():
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text(content, encoding="utf-8")
    return traces.Source(tmp_path)


def card(tmp_path: Path | None = None) -> dict:
    return traces.cards(LINKS, "app/*/page.tsx", limit=1, source=source(tmp_path) if tmp_path else None)[0]


def test_a_card_is_the_branches_that_reach_an_effect_or_a_broken_point_as_typed_edges():
    made = traces.cards(LINKS, "app/*/page.tsx")
    assert [c["entry"] for c in made] == sorted(PAGES)
    steps = made[0]["steps"]
    assert [(s["n"], s["depth"], s["from"].split("::")[-1], s["type"], s["to"].split("::")[-1], s["end"]) for s in steps] == [
        (1, 0, "Page0", "chiama", "Subscription", None),
        (2, 1, "Subscription", "onSubmit", "Subscription.handleSubmit", None),   # the event, not «attiva»
        (3, 2, "Subscription.handleSubmit", "chiama", "startCheckout", None),
        (4, 3, "startCheckout", "HTTP POST /checkout", "checkout", None),        # a linked route goes on in the server
        (5, 4, "checkout", "scrive", "store:db/payments", "effetto"),
        (6, 3, "startCheckout", "lacuna", "?", "lacuna"),                         # where the links stop, with why
        (7, 1, "Subscription", "legge", "store:db/plans", "effetto")]             # a read is shown from its reader
    assert steps[5]["reason"] == "rotta: route not a literal" and steps[5]["site"] == "lib/api.ts:6"
    assert LINKS["edges"][steps[1]["edge"]]["label"] == "onSubmit"               # the id is the edge of the links
    assert (made[0]["pruned"], made[0]["common"]) == (1, 1)                       # the logo; the shell every page has
    assert made[1]["steps"] == []                                                  # only utilities: nothing to ask


def test_the_card_reads_how_to_read_it_then_the_edges_then_the_question(tmp_path):
    said = traces.text(card(tmp_path))
    marks = ("<come_leggere>", "app/p0/page.tsx", "1. Page0 --[chiama]--> Subscription",
             "  2. Subscription --[onSubmit]--> Subscription.handleSubmit", "chiamata in billing/view.tsx:12",
             "5. checkout --[scrive]--> store:db/payments  ◼ effetto", "6. startCheckout --[lacuna]--> ?",
             "6| return request(`/refunds/${id}`", "<domanda>")
    order = [said.index(mark) for mark in marks]
    assert order == sorted(order)
    assert "<sorgente" not in traces.text(card())                                 # without the source, no excerpt


def test_verify_accepts_only_contiguous_chains_from_the_entry_to_an_effect(tmp_path):
    made, files = card(tmp_path), source(tmp_path)
    answer = {"flussi": [{"nome": "Pagamento", "passi": [1, 2, 3, 4, 5]},
                         {"nome": "Lettura dei piani", "passi": [1, 7]},
                         {"nome": "Fratelli in fila", "passi": [1, 2, 7]},
                         {"nome": "Non dall'ingresso", "passi": [2, 3, 4, 5]},
                         {"nome": "Arco inventato", "passi": [1, 99]},
                         {"nome": "Senza effetto", "passi": [1, 2, 3]},
                         {"nome": "Sulla lacuna", "passi": [1, 2, 3, 6]}],
              "lacune": [{"passo": 6, "causa": "l'indirizzo è composto da una variabile"}]}
    checked = traces.verify(made, answer, LINKS, files)
    assert [f["nome"] for f in checked["accepted"]] == ["Pagamento", "Lettura dei piani"]
    assert [r["reason"].split(":")[0] for r in checked["rejected"]] == [
        "catena non contigua", "non parte dall'ingresso", "archi inesistenti", "termina senza effetto",
        "termina su una lacuna non corretta"]
    assert checked["gaps"] == [{"passo": 6, "site": "lib/api.ts:6", "reason": "rotta: route not a literal",
                                "causa": "l'indirizzo è composto da una variabile"}]


def test_a_correction_holds_only_with_the_text_of_the_cited_line(tmp_path):
    made, files = card(tmp_path), source(tmp_path)
    flow = {"nome": "Rimborso", "passi": [1, 2, 3, 6]}
    good = {"passo": 6, "riga": "lib/api.ts:6", "testo": "request(`/refunds/${id}`", "verso": "POST /refunds/{id}"}
    checked = traces.verify(made, {"flussi": [flow], "correzioni": [good]}, LINKS, files)
    assert [f["nome"] for f in checked["accepted"]] == ["Rimborso"] and checked["corrections"]["accepted"] == [good]
    for bad, why in (({**good, "testo": "fetch('/refunds')"}, "il testo non è su quella riga"),
                     ({**good, "riga": "server/pay.py:1"}, "la riga non è nel sorgente mostrato"),
                     ({**good, "passo": 3}, "il passo non è una lacuna")):
        checked = traces.verify(made, {"flussi": [flow], "correzioni": [bad]}, LINKS, files)
        assert checked["accepted"] == [] and why in checked["corrections"]["rejected"][0]["reason"]
    without = traces.verify(made, {"flussi": [flow], "correzioni": [good]}, LINKS, None)
    assert without["accepted"] == [] and "sorgente" in without["corrections"]["rejected"][0]["reason"]


def test_verify_refuses_an_edge_that_is_not_in_the_links_and_a_line_that_does_not_exist(tmp_path):
    made, files = card(tmp_path), source(tmp_path)
    flow = {"flussi": [{"nome": "Pagamento", "passi": [1, 2, 3, 4, 5]}]}
    forged = copy.deepcopy(made)
    forged["steps"][2]["to"] = "lib/api.ts::somethingElse"
    forged["steps"][3]["from"] = "lib/api.ts::somethingElse"
    assert "non è nei collegamenti" in traces.verify(forged, flow, LINKS, files)["rejected"][0]["reason"]
    short = copy.deepcopy(LINKS)
    short["edges"][made["steps"][4]["edge"]]["site"] = "server/pay.py:400"
    moved = traces.cards(short, "app/*/page.tsx", limit=1)[0]
    assert "riga inesistente" in traces.verify(moved, flow, short, files)["rejected"][0]["reason"]
    assert traces.verify(moved, flow, short, None)["lines_checked"] is False     # without the source it says so


def test_decode_json_and_cli_edge_cases():
    assert traces._decode_json('Nota {breve}: {"flussi": [], "lacune": []} fine {x}') == {"flussi": [], "lacune": []}
    checked = traces.verify(card(), {"flussi": ["testo", {"nome": "Bool", "passi": [True]}]}, LINKS)
    assert checked["accepted"] == [] and len(checked["rejected"]) == 2
    assert traces.main(["traces.py", "cards", "in.json", "*", "out.json", "--limit"]) == 2
