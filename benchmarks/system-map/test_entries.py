"""The measure of the entries: per kind and per reader, the entries of a reference its candidates find."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import entries  # noqa: E402

FILES = ["web/page.tsx", "web/util.ts", "jobs/nightly.ts", "mail/send.ts", "lib/a.ts", "tests/x.test.ts",
         *(f"big/f{n}.ts" for n in range(13))]


def node(name: str, *members: str, position: str = "internal") -> dict:
    return {"name": name, "type": "modulo", "position": position, "members": list(members)}


EXPECTED = {"nodes": [node("Pagina", "web/page.tsx"), node("Lavori", "jobs/"), node("Ricevute", "mail/send.ts::send"),
                      node("Grande", "big/"), node("Stripe", position="external"),
                      node("Prove", "tests/")],                                  # a node no entry names
            "flows": [{"name": "Pagamento", "entries": [
                {"node": "Pagina", "kind": "controllo dell'interfaccia", "what": "il pulsante"},
                {"node": "Ricevute", "kind": "messaggio", "what": "la coda"},
                {"node": "Grande", "kind": "comando", "what": "la riga di comando"},       # 13 files: apart
                {"node": "Stripe", "kind": "rotta", "what": "il webhook"}]},               # not internal: apart
                      {"name": "Rinnovo", "entries": [{"node": "lavori", "kind": "orario", "what": "di notte"}]}]}


def candidate(symbol: str) -> dict:
    return {"reader": "residuo", "shape": "residuo", "site": symbol.split("::")[0] + ":1", "symbol": symbol}


CANDIDATES = {"case": "sintetico",
              "candidates": [candidate("web/page.tsx::Page"), candidate("jobs/nightly.ts::run"),
                             candidate("tests/x.test.ts::t")],
              "calls": [["web/page.tsx::Page", "web/util.ts::fmt"]]}


def test_an_entry_is_found_by_a_candidate_in_a_file_of_its_node():
    measured = entries.measure(CANDIDATES, EXPECTED, FILES)
    assert measured["readers"] == [{"reader": "residuo", "candidates": 3, "not_entries": 1, "by_kind": {
        "controllo dell'interfaccia": {"found": 1, "of": 1}, "messaggio": {"found": 0, "of": 1},
        "orario": {"found": 1, "of": 1}}}]                       # the folder of a node is its files in the snapshot
    assert measured["apart"] == {"comando": 1, "rotta": 1}


def test_the_files_no_candidate_reaches_are_counted_by_folder():
    unreached = entries.measure(CANDIDATES, EXPECTED, FILES)["unreached"]
    assert unreached == {"files": 15, "of": 19, "by_folder": {"big": 13, "lib": 1, "mail": 1}}


def test_the_command_prints_the_measure(tmp_path, capsys):
    paths = [tmp_path / name for name in ("candidates.json", "expected.json", "files.txt")]
    paths[0].write_text(json.dumps(CANDIDATES), encoding="utf-8")
    paths[1].write_text(json.dumps(EXPECTED), encoding="utf-8")
    paths[2].write_text("".join(f"{path}\n" for path in FILES), encoding="utf-8")
    assert entries.main(["entries.py", "measure", *map(str, paths)]) == 0
    assert json.loads(capsys.readouterr().out) == entries.measure(CANDIDATES, EXPECTED, FILES)
