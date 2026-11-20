#!/usr/bin/env python3
"""Requests in words whose right flow or part is known, written by a model from the reference maps.

    GATEWAY_URL=... GATEWAY_KEY=... GATEWAY_MODEL=... python embed_queries.py OUT.json EXPECTED-system.json [...]

For every flow of a reference a model writes two requests a person could make without knowing its name (one as who
uses the product, one as who asks for a review of the code); for every part of depth 0 to 2, one question. The model
is told not to reuse the words of the name: a request that repeats the name proves nothing. OUT.json is what
`embed_probe.py rank` reads: per case and kind the names, a longer record for each (what the registry of flows
would hold) and the requests with their right name. The references are private: OUT.json stays out of git.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request
from pathlib import Path

BATCH = 8
ASK = {"flusso": ("Per ognuno di questi flussi di un prodotto software scrivi due richieste brevi, in italiano: «utente», "
                  "come la direbbe chi usa il prodotto e vuole fare quella cosa; «review», come la direbbe uno sviluppatore "
                  "che chiede di controllare quel pezzo. Non usare le parole del nome del flusso: usa sinonimi o descrivi "
                  "che cosa succede. Rispondi solo con JSON: {\"richieste\": [{\"n\": numero, \"utente\": \"...\", "
                  "\"review\": \"...\"}]}."),
       "parte": ("Per ognuna di queste parti di un sistema software scrivi una domanda breve, in italiano, che uno "
                 "sviluppatore farebbe per trovare quella parte senza conoscerne il nome. Non usare le parole del nome. "
                 "Rispondi solo con JSON: {\"richieste\": [{\"n\": numero, \"review\": \"...\"}]}.")}


def said(prompt: str) -> dict:
    url, key, model = (os.environ[name] for name in ("GATEWAY_URL", "GATEWAY_KEY", "GATEWAY_MODEL"))
    body = {"model": model, "temperature": 0, "max_tokens": 2500, "messages": [{"role": "user", "content": prompt}]}
    request = urllib.request.Request(url.rstrip("/") + "/v1/chat/completions", data=json.dumps(body).encode("utf-8"),
                                     headers={"Authorization": f"Bearer {key}", "content-type": "application/json"})
    with urllib.request.urlopen(request, timeout=300) as response:
        text = json.load(response)["choices"][0]["message"].get("content") or ""
    try:
        return json.JSONDecoder().raw_decode(text, text.index("{"))[0]
    except ValueError:
        return {}


def requests(kind: str, items: list[tuple[str, str]]) -> list[dict]:
    """The requests a model writes for `(name, description)` items, each with its right name."""
    out = []
    for start in range(0, len(items), BATCH):
        part = items[start:start + BATCH]
        listed = "\n".join(f"{n}. {name}: {about}" for n, (name, about) in enumerate(part, 1))
        for answer in said(f"{listed}\n\n{ASK[kind]}").get("richieste") or []:
            if isinstance(answer, dict) and isinstance(answer.get("n"), int) and 1 <= answer["n"] <= len(part):
                out += [{"query": answer[voice], "voice": voice, "right": [part[answer["n"] - 1][0]]}
                        for voice in ("utente", "review") if isinstance(answer.get(voice), str) and answer[voice].strip()]
    return out


def depth(node: dict, by: dict) -> int:
    level = 0
    while node.get("inside") in by and level < 20:
        node, level = by[node["inside"]], level + 1
    return level


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print(__doc__)
        return 2
    sets = []
    for path in argv[2:]:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
        by = {node["name"]: node for node in value["nodes"]}
        flows = [(f["name"], "; ".join([*(e.get("what", "") for e in f.get("entries", [])), "→",
                                        *(e.get("what", "") for e in f.get("effects", [])), "| passa per",
                                        ", ".join(f["nodes"])])) for f in value["flows"]]
        parts = [(n["name"], n.get("what", "")) for n in value["nodes"]
                 if n.get("position", "internal") == "internal" and depth(n, by) <= 2 and n.get("what")]
        for kind, items in (("flusso", flows), ("parte", parts)):
            sets.append({"case": value.get("case"), "kind": kind, "names": [name for name, _ in items],
                         "records": [f"{name}. {about}" for name, about in items], "wanted": requests(kind, items)})
            print(value.get("case"), kind, len(items), "names,", len(sets[-1]["wanted"]), "requests", flush=True)
    Path(argv[1]).write_bytes(json.dumps({"sets": sets}, ensure_ascii=False, indent=1).encode("utf-8"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
