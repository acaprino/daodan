"""The count of possible links on the flow-model fixture, with a webhook the card provider calls."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import possible  # noqa: E402

WEBHOOK = '''from . import db
from .http import route


@route("POST", "/card-events")
def card_event(body: dict) -> dict:
    db.put("payments", body["reference"], {"status": body["status"]})
    return {}
'''
PROVIDER = "card payment provider"
REFERENCE = {
    "nodes": [
        {"name": "Cliente", "type": "attore", "position": "external", "evidence": ["web/checkout.ts"]},
        {"name": "Checkout", "type": "schermata", "members": ["web/checkout.ts"]},
        {"name": "Badge pagamento", "type": "schermata", "members": ["web/badge.ts"]},
        {"name": "API pagamenti", "type": "servizio o API", "members": ["server/payments.py", "server/gateway.py"]},
        {"name": "Eventi della carta", "type": "servizio o API", "members": ["server/events.py"]},
        {"name": "Pagamento", "type": "entità", "members": ["store:db/payments", "store:web state/payment"]},
        {"name": "Fornitore delle carte", "type": "gateway", "position": "external", "evidence": ["server/gateway.py"]},
        {"name": "Posta", "type": "gateway", "position": "external", "evidence": ["web/badge.ts"]},  # no module
        {"name": "Landing", "type": "schermata", "position": "unseen", "where": "un altro repository"},
    ],
    "flows": [{
        "name": "Pagare un ordine", "types": ["funzionale", "operativo"],
        "nodes": ["Cliente", "Checkout", "Badge pagamento", "API pagamenti", "Eventi della carta", "Pagamento",
                  "Fornitore delle carte", "Posta", "Landing"],
        "entries": [{"node": "Cliente", "kind": "controllo dell'interfaccia", "what": "Paga"},
                    {"node": "Fornitore delle carte", "kind": "rotta", "what": "il webhook"},
                    {"node": "Landing", "kind": "controllo dell'interfaccia", "what": "Abbonati"}],
        "effects": [{"node": "Pagamento", "what": "il pagamento registrato"}],
        "arrows": [
            {"from": "Cliente", "to": "Checkout", "data": "clic su Paga", "kind": "attiva", "cite": "web/checkout.ts:22"},
            {"from": "Checkout", "to": "API pagamenti", "data": "ordine da pagare"},
            {"from": "API pagamenti", "to": "Fornitore delle carte", "data": "importo", "kind": "usa",
             "cite": "server/gateway.py:8"},
            {"from": "Fornitore delle carte", "to": "Eventi della carta", "data": "esito", "kind": "chiama",
             "cite": "server/events.py:5"},
            {"from": "Eventi della carta", "to": "Pagamento", "data": "esito registrato"},
            {"from": "Badge pagamento", "to": "API pagamenti", "data": "richiesta di stato"},  # nothing links it
            {"from": "Landing", "to": "Checkout", "data": "piano scelto", "kind": "attiva", "cite": "web/checkout.ts:22"},
            {"from": "API pagamenti", "to": "Posta", "data": "ricevuta", "kind": "usa", "cite": "server/payments.py:1"},
        ]}],
}


def run(command: list[str], cwd: Path | None = None) -> str:
    """The command's output; on failure its own message, and never a wait past the timeout."""
    done = subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=300)
    if done.returncode:
        raise RuntimeError(f"{command[:3]} exited {done.returncode}: {done.stderr.strip()[-2000:]}")
    return done.stdout


class PossibleLinks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.work = Path(tempfile.mkdtemp(prefix="possible-")).resolve()
        cls.addClassCleanup(shutil.rmtree, cls.work, True)  # tearDownClass does not run when setUpClass fails
        project = cls.work / "app"
        shutil.copytree(ROOT / "benchmarks/flow-model/app", project)
        (project / "server/events.py").write_text(WEBHOOK, encoding="utf-8")
        declared = json.loads((project / "codebase-modules.json").read_text(encoding="utf-8"))
        provider = next(m for m in declared["modules"] if m["name"] == PROVIDER)
        provider["evidence"] += ["server/events.py", "server/payments.py"]  # payments.py: a route its client calls
        (project / "codebase-modules.json").write_text(json.dumps(declared), encoding="utf-8")
        for command in (["git", "init", "-q"], ["git", "add", "-A"],
                        ["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "fixture"]):
            run(command, cwd=project)
        cls.manifest = cls.work / "snapshot/manifest.sqlite"
        # Each in a process of its own, as the README runs them: this folder's entries.py hides the core's.
        core = ROOT / "daodan" / "core"
        run([sys.executable, str(core / "snapshot.py"), "write", str(project), "--out", str(cls.manifest),
             "--no-engine", "--no-index"])
        cls.links = json.loads(run([sys.executable, str(core / "flows.py"), "links", str(cls.manifest), "--rules",
                                    str(ROOT / "benchmarks/flow-model/rules.json")]))
        cls.result = possible.measure(cls.manifest, cls.links, REFERENCE)
        cls.flow = cls.result["flows"][0]

    def test_an_uncalled_route_in_a_file_of_the_provider_is_called_by_it(self):
        self.assertIn({"from": f"module:{PROVIDER}", "to": "server/events.py::card_event", "type": "chiama",
                       "site": "server/events.py:5", "origin": "possibile:ritorno"}, possible.possible(self.links))
        self.assertEqual(self.flow["entries_from_others"], {"possibile:ritorno": 1, "non visto": 1})
        self.assertEqual(self.result["services"], {"Fornitore delle carte": [f"module:{PROVIDER}"], "Posta": []})

    def test_a_route_its_client_calls_or_one_in_a_file_of_no_provider_gets_no_return(self):
        targets = {e["to"] for e in possible.possible(self.links)}
        self.assertNotIn("server/payments.py::create_payment", targets)        # called by the web client
        self.assertNotIn("admin/orders.py::list_all_orders", targets)          # nobody calls it, no provider there
        self.assertEqual(self.result["possible"]["ritorno"], {"links": 1, "inside_node": 0, "outside_reference": 0})

    def test_each_arrow_lands_in_its_bucket_in_its_direction(self):
        self.assertEqual(self.flow["arrows"], {"dichiarata": 1, "certo": 3, "possibile:ritorno": 1, "mancante": 1,
                                               "non visto": 1, "senza modulo": 1})
        self.assertEqual(self.flow["missing"], ["Badge pagamento -> API pagamenti"])

    def test_a_call_that_meets_several_routes_goes_to_each_of_them(self):
        gap = {"site": "web/a.ts:3", "symbol": "web/a.ts::load", "reason": "route GET /x/{}: several handlers",
               "candidates": ["server/x.py::one", "server/y.py::two"]}
        self.assertEqual([(e["to"], e["origin"]) for e in possible.possible({"edges": [], "entries": [], "gaps": [gap]})],
                         [("server/x.py::one", "possibile:incerto"), ("server/y.py::two", "possibile:incerto")])

    def test_a_reference_written_for_the_checker_is_taken_as_it_is(self):
        import system_map
        import test_reference
        value = system_map.validate(possible._as_map(test_reference.GOOD))
        self.assertEqual(value["flows"][0]["entries"], ["API ordini"])

    def test_links_of_another_schema_are_refused(self):
        with self.assertRaisesRegex(ValueError, "links schema"):
            possible.measure(self.manifest, {**self.links, "schema": "daodan/flow-links/v2"}, REFERENCE)


if __name__ == "__main__":
    unittest.main()
