"""Four interface events followed on projects analyzed with the real indexers, in Daodan's container.

    python benchmarks/system-map/real_paths.py [web] [tk] [tauri] [next] [--work DIR]

Each case is copied to a work folder and analyzed through `MapService.create_run` with its engine pass: the
official indexer of the language runs in Daodan's container, never on the host (the pass is a gap without a
container engine). Then, as an MCP client would: the candidates before any rule, the shapes still to classify,
the answers and rules of the case, each card with its numbered steps and the entries the links end with. The
answer is JSON, with `checks` naming what held; the script ends with 1 when one did not. `--work` keeps the runs,
for the app to open them.
"""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "daodan" / "core"))

from mcp_service import MapService  # noqa: E402

RUN = "real-paths"
HERE = Path(__file__).resolve().parent
WEB_RULES = json.loads((REPO / "benchmarks/flow-model/rules.json").read_text(encoding="utf-8"))["rules"]
CASES = {
    "web": {"source": REPO / "benchmarks/flow-model/app", "answers": {}, "rules": WEB_RULES},
    "tk": {"source": HERE / "real-paths/tk-desk", "answers": {"tk.Button#command": "controllo dell'interfaccia"},
           "rules": [{"written": "store.put", "link": "scrive", "store": "disk", "key": "arg0"}]},
    "tauri": {"source": HERE / "real-paths/tauri-desk", "answers": {}, "rules": []},
    # a form's `action` is a shape the registry does not know: the case answers it, as the owner would
    "next": {"source": HERE / "real-paths/next-shop", "answers": {"action": "controllo dell'interfaccia"}, "rules": []},
}
LIMIT = 3600  # seconds one engine pass may take: rust-analyzer builds the dependencies of a Tauri crate


def analyzed(name: str, work: Path) -> tuple[MapService, dict]:
    case = CASES[name]
    project = work / name / "checkout"  # as the app lays it: the analysis beside the checkout, never inside it
    shutil.rmtree(work / name, ignore_errors=True)
    shutil.copytree(case["source"], project)
    subprocess.run(["git", "init", "-q", str(project)], check=True)
    service = MapService(project.parent)
    started = time.monotonic()
    status = service.create_run(project.name, RUN, engine=True)
    while status["engine"].get("state") == "running" and time.monotonic() - started < LIMIT:
        time.sleep(10)
        status = service.status(RUN)
    engine = status["engine"]
    return service, {"seconds": round(time.monotonic() - started), "state": engine.get("state"),
                     "reason": engine.get("reason"), "pipeline": status.get("pipeline"),
                     "languages": {language: {key: entry.get(key) for key in ("state", "engine", "reason")}
                                   for language, entry in (engine.get("languages") or {}).items()}}


def followed(service: MapService, case: dict) -> dict:
    before = service.flows(RUN, entry_offset=0)
    service.flows(RUN, rules=case["rules"])
    asked = service.flows(RUN, shape_offset=0)
    answers = {str(q["row"]): case["answers"][q["shape"]] for q in asked.get("questions", ())
               if q.get("shape") in case["answers"]}
    if answers:
        service.flows(RUN, shape_answers={"id": asked["id"], "answers": answers})
    cards = []
    for card in service.flows(RUN, trace_offset=0, limit=100)["cards"]:
        steps = service.flows(RUN, trace_id=card["card_id"])["steps"]
        cards.append({**{key: card.get(key) for key in ("label", "event", "handler", "site", "source")},
                      "steps": [{key: step.get(key) for key in ("n", "parent", "from", "to", "type", "site", "origin",
                                                              "resolver", "end", "reason") if step.get(key) is not None}
                                for step in steps]})
    return {"candidates_before_rules": [{key: c.get(key) for key in ("shape", "event", "label", "symbol", "site",
                                                                    "handler_source")}
                                        for c in before.get("candidates", ())],
            "shapes_asked": [q.get("shape") for q in asked.get("questions", ())], "answered": answers, "cards": cards,
            "entries": [{key: entry.get(key) for key in ("kind", "symbol", "site", "path", "method", "reader",
                                                         "handler_source") if entry.get(key) is not None}
                        for entry in service.flows(RUN)["entries"]]}


def reaches(card: dict, target: str) -> dict | None:
    return next((step for step in card["steps"] if step.get("to") == target), None)


def checks(name: str, found: dict, engine: dict) -> list[dict]:
    by_label = {card["label"]: card for card in found["cards"] if card.get("label")}
    by_handler = {card["handler"]: card for card in found["cards"]}
    if name == "web":
        card = by_handler.get("web/checkout.ts::onPayClick")
        return [{"check": "the pay click reaches the payment key of the web state",
                 "ok": bool(card and reaches(card, "store:web state/payment"))}]
    if name == "tk":
        card = by_label.get("Salva")
        return [{"check": "the Tk command is bound to App.save", "ok": bool(card and card["handler"].endswith("::App.save"))},
                {"check": "App.save reaches the write of disk/orders", "ok": bool(card and reaches(card, "store:disk/orders"))}]
    if name == "next":
        by_path = {}
        for entry in found["entries"]:
            by_path.setdefault(entry.get("path"), []).append(entry)
        action, card = "app/checkout/actions.ts::pay", by_label.get("Paga")
        return [{"check": "/checkout is an entry on the page's function, with its line",
                 "ok": [(e["symbol"], e["site"]) for e in by_path.get("/checkout", ())] == [
                     ("app/checkout/page.tsx::Checkout", "app/checkout/page.tsx:3")]},
                {"check": "/api/pay is exactly one entry, on the route handler's POST",
                 "ok": [e["symbol"] for e in by_path.get("/api/pay", ())] == ["app/api/pay/route.ts::POST"]},
                {"check": "no entry is the route /pay", "ok": "/pay" not in by_path},
                {"check": "the Paga card reaches the server action",
                 "ok": bool(card and (card["handler"] == action or reaches(card, action)))}]
    command = "src-tauri/src/main.rs::"
    typescript = (engine["languages"].get("typescript") or {}).get("state")
    # The Node restore is shared between the runs of the analysis: each still installs its own indexer.
    rows = [{"check": "scip-typescript indexes after the shared Node restore", "ok": typescript == "fresh"}, {"check": "the click reaches the registered Rust command",
             "ok": bool(by_label.get("Salva profilo") and reaches(by_label["Salva profilo"], command + "persist"))}]
    for label, function in (("Prova", "only_in_tests"), ("Bozza", "on_idle_builder")):
        card = by_label.get(label)
        rows.append({"check": f"{function} stays unresolved", "ok": bool(card and not reaches(card, command + function))})
    return rows


def main(argv: list[str]) -> int:
    work = Path(argv[argv.index("--work") + 1]).resolve() if "--work" in argv else None
    names = [name for name in argv if name in CASES] or list(CASES)
    with tempfile.TemporaryDirectory(prefix="daodan-real-paths-") as temp:
        out = {}
        for name in names:
            service, engine = analyzed(name, work or Path(temp))
            found = followed(service, CASES[name])
            out[name] = {"engine": engine, **found, "checks": checks(name, found, engine)}
        print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0 if all(row["ok"] for case in out.values() for row in case["checks"]) else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
