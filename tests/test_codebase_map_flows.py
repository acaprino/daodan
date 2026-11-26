"""Flows of the fixture in benchmarks/flow-model: deduced links, traces and units against expected.json."""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest

import pytest
from unittest import mock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "daodan/core"
BENCH = ROOT / "benchmarks/flow-model"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
import flows  # noqa: E402
import snapshot  # noqa: E402


def read_project(work: Path, sources: dict) -> Path:
    """A snapshot, under `work`, of a project of these files (git-tracked, as the fixtures are)."""
    app = work / "app"
    for rel, text in sources.items():
        (app / rel).parent.mkdir(parents=True, exist_ok=True)
        (app / rel).write_text(text, encoding="utf-8", newline="\n")
    for command in (["git", "init", "-q"], ["git", "add", "-A"],
                    ["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "fixture"]):
        subprocess.run(command, cwd=app, check=True, capture_output=True)
    manifest = work / "snapshot/manifest.sqlite"
    snapshot.main(["write", str(app), "--out", str(manifest), "--no-engine", "--no-index"])
    return manifest


class FlowFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.work = Path(tempfile.mkdtemp(prefix="flow-model-")).resolve()
        app = cls.work / "app"
        shutil.copytree(BENCH / "app", app)
        for command in (["git", "init", "-q"], ["git", "add", "-A"],
                        ["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "fixture"]):
            subprocess.run(command, cwd=app, check=True, capture_output=True)
        cls.manifest = cls.work / "snapshot/manifest.sqlite"
        snapshot.main(["write", str(app), "--out", str(cls.manifest), "--no-engine", "--no-index"])
        cls.links = flows.link_facts(cls.manifest, flows.load_rules(BENCH / "rules.json"))
        cls.expected = json.loads((BENCH / "expected.json").read_text(encoding="utf-8"))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.work, True)

    def deduced(self, kind):
        return {(edge["from"], edge["to"]) for edge in self.links["edges"]
                if edge["type"] == kind and edge["origin"] != "diretto"}

    def test_stores_pair_writers_and_readers_by_key(self):
        stores = {name: {k: sorted(v) for k, v in store.items()} for name, store in self.expected["stores"].items()}
        self.assertEqual(self.links["stores"], stores)

    def test_routes_match_service_method_and_path(self):
        routes = {(r["caller"], r["handler"]) for r in self.expected["routes"]}
        self.assertEqual(self.deduced("chiama"), routes)

    def test_actions_entries_external_node_and_gaps(self):
        self.assertEqual(self.deduced("attiva"), {(a["in"], a["handler"]) for a in self.expected["actions"]})
        entries = {}
        for entry in self.links["entries"]:
            entries.setdefault({"rotta": "route", "lavoro pianificato": "scheduled", "azione": "action"}[entry["kind"]],
                               []).append(entry["symbol"])
        self.assertEqual({k: sorted(v) for k, v in entries.items()},
                         {k: sorted(v) for k, v in self.expected["entry_points"].items()})
        for node in self.expected["external_nodes"]:
            self.assertIn((node["reached_by"], f"module:{node['module']}"), self.deduced("usa"))
        self.assertEqual([(g["symbol"], "not a literal" in g["reason"]) for g in self.links["gaps"]],
                         [(g["symbol"], True) for g in self.expected["gaps"]])

    def test_no_link_between_independent_fields_or_homonymous_routes(self):
        for source, target in self.expected["forbidden_links"]:
            flow = flows.trace(self.links, source, "from")
            self.assertNotIn(target, flow["nodes"], f"{source} reaches {target}")

    def test_display_reaches_the_service_store_through_the_route(self):
        case = self.expected["cross_layer"]
        flow = flows.trace(self.links, case["from"], "to")
        self.assertIn(f"store:{case['store']}", flow["nodes"])
        self.assertIn(case["through_route"], [edge.get("route") for edge in flow["edges"]])
        self.assertTrue(flow["complete"])

    def test_feature_entry_points_chain_and_cycle(self):
        through = flows.trace(self.links, self.expected["call_chain"][0], "through")
        for entry in self.expected["features"]["payment"]["entry_points"]:
            self.assertIn(entry, through["entries"])
        calls = {(e["from"], e["to"]) for e in self.links["edges"] if e["type"] == "chiama"}
        chain = self.expected["call_chain"]
        self.assertTrue(all(pair in calls for pair in zip(chain, chain[1:])))
        first, second = self.expected["cycle"]
        self.assertTrue({(first, second), (second, first)} <= calls)

    def test_a_stop_leaves_the_flow_incomplete(self):
        start = "web/checkout.ts::onPayClick"
        self.assertEqual(flows.trace(self.links, start, "from", max_edges=2)["stopped"], "budget")
        self.assertFalse(flows.trace(self.links, start, "from", boundary=["web"])["complete"])
        self.assertFalse(flows.trace(self.links, "web/debug.ts::probe", "from")["complete"])

    def test_reaching_a_reader_by_call_expands_its_effects_in_both_orders(self):
        start, via, reader, effect = ("app.py::" + n for n in ("start", "via", "reader", "effect"))
        edges = [{"from": a, "to": b, "type": t} for a, b, t in [
            (start, "store:state", "scrive"), (start, via, "chiama"),
            ("store:state", reader, "legge"), (via, reader, "chiama"), (reader, effect, "chiama")]]
        for order in (edges, list(reversed(edges))):
            flow = flows.trace({"gaps": [], "edges": order}, start, "from")
            self.assertIn(effect, flow["nodes"])
            self.assertEqual(len(flow["edges"]), len(edges))

    def test_an_unowned_gap_and_a_truncated_entry_prevent_completeness(self):
        start = "app.py::entry"
        links = {"entries": [{"symbol": start}], "gaps": [{"site": "app.py:9", "reason": "unknown callee"}],
                 "edges": [{"from": start, "to": "app.py::helper", "type": "chiama"},
                           {"from": "app.py::helper", "to": "app.py::charge", "type": "chiama"}]}
        self.assertFalse(flows.trace(links, start, "from")["complete"])
        links["gaps"] = []
        through = flows.trace(links, "app.py::charge", "through", max_edges=1)
        self.assertEqual((through["entries"], through["complete"]), ([], False))
        self.assertEqual(through["incomplete_entries"], [{"entry": start, "reason": "budget"}])
        self.assertTrue(flows.trace(links, "app.py::unrelated", "through")["complete"])
        self.assertEqual(flows.trace({**links, "entries": []}, start, "through")["stopped"], "no_entries")

    def test_one_flow_is_seen_at_each_level_without_changing(self):
        flow = flows.trace(self.links, "web/checkout.ts::onPayClick", "from")
        modules_of = flows.file_modules(self.manifest)
        self.assertEqual(modules_of["server/payments.py"], "payment")
        logical = flows.at_level(flow, "logico", modules_of)
        self.assertIn("module:payment", logical["nodes"])
        self.assertNotIn("server/payments.py::charge_order", logical["nodes"])
        # A symbol whose file belongs to no module stays a symbol.
        self.assertIn("server/billing.py::amount_for", logical["nodes"])
        self.assertEqual(sum(edge["links"] for edge in logical["edges"])
                         + sum(1 for edge in flow["edges"] if modules_of.get(edge["from"].split("::")[0])
                               and modules_of.get(edge["from"].split("::")[0]) == modules_of.get(edge["to"].split("::")[0])),
                         len(flow["edges"]))
        data = flows.at_level(flow, "dati", {})
        self.assertEqual({edge["type"] for edge in data["edges"]}, {"scrive", "legge"})
        self.assertIn("store:db/payments", data["nodes"])
        ux = flows.at_level(flows.trace(self.links, "web/checkout.ts::renderCheckout", "from"), "ux", {})
        self.assertIn(("web/checkout.ts::renderCheckout", "web/checkout.ts::onPayClick"),
                      {(edge["from"], edge["to"]) for edge in ux["edges"] if edge["type"] == "attiva"})
        self.assertEqual(flows.at_level(flow, "fisico", {}), flow)

    @pytest.mark.usefixtures("real_stack")
    def test_the_service_asks_for_rules_records_them_and_answers_at_a_level(self):
        import mcp_service
        project = self.work / "service"
        shutil.copytree(BENCH / "app", project / "app")
        subprocess.run(["git", "init", "-q", str(project)], check=True, capture_output=True)
        service = mcp_service.MapService(project)
        (project / "app/web/package.json").write_text('{"name": "web", "dependencies": {"express": "5"}}', encoding="utf-8")
        service.create_run("app", "flows", engine=False)
        asked = service.flows("flows")
        self.assertEqual(asked["status"], "needs_rules")
        self.assertEqual([(unit["paths"], unit["technologies"]) for unit in asked["technologies"]],
                         [(["app/web"], ["express", "nodejs"])])
        import technologies
        with mock.patch.object(technologies, "ensure", side_effect=OSError("disk full")):
            failed = service.flows("flows")
        self.assertEqual((failed["status"], failed["technologies_unavailable"]), ("needs_rules", "OSError: disk full"))
        self.assertNotIn("technologies", failed)
        rules = json.loads((BENCH / "rules.json").read_text(encoding="utf-8"))["rules"]
        rules = [{**rule, "callee": "app/" + rule["callee"]} for rule in rules]
        with self.assertRaisesRegex(ValueError, "unknown field"):
            service.flows("flows", rules=[{**rules[0], "where": "x"}])
        summary = service.flows("flows", rules=rules)
        self.assertEqual((summary["status"], summary["entry_count"], summary["routes"]["linked"]), ("ok", 6, 2))
        self.assertEqual(summary["stores"]["db/payments"], {"reads": 3, "writes": 1})
        flow = service.flows("flows", start="app/web/badge.ts::renderBadge", direction="to", level="dati")
        self.assertIn("store:db/payments", flow["nodes"])
        through = service.flows("flows", start="app/server/payments.py::charge_order", direction="through")
        self.assertIn("app/server/jobs.py::retry_declined", through["entries"])

        badge = "app/web/badge.ts::renderBadge"
        card = {"name": "Stato del pagamento", "type": "dati",
                "text": "Il badge legge lo stato del pagamento dallo stato del client (app/web/badge.ts:4).\n"
                        "Lo stato arriva dalla risposta di POST /payments (app/web/checkout.ts:12)."}
        with self.assertRaisesRegex(ValueError, "line 2 cites no step"):
            service.flows("flows", start=badge, direction="to",
                          card={**card, "text": card["text"].replace("checkout.ts:12", "checkout.ts:99")})
        recorded = service.flows("flows", start=badge, direction="to", card=card)
        self.assertEqual((recorded["card"]["name"], recorded["card"]["fresh"]), ("Stato del pagamento", True))
        self.assertNotIn("card", service.flows("flows", start=badge, direction="from"))
        service.flows("flows", rules=[rule for rule in rules if rule["link"] != "legge"])
        changed = service.flows("flows", start=badge, direction="to")["card"]
        self.assertEqual((changed["fresh"], changed["changed_files"], changed["evidence_changed"]), (False, [], True))
        service.flows("flows", rules=rules)
        self.assertTrue(service.flows("flows", start=badge, direction="to")["card"]["fresh"])
        cards = json.loads((project / ".daodan/map/runs/flows/snapshot/flow-cards.json").read_text(encoding="utf-8"))
        files = cards["cards"]["to:" + badge]["files"]
        files["app/web/checkout.ts"] = "edited"
        (project / ".daodan/map/runs/flows/snapshot/flow-cards.json").write_text(json.dumps(cards), encoding="utf-8")
        stale = service.flows("flows", start=badge, direction="to")["card"]
        self.assertEqual((stale["fresh"], stale["changed_files"]), (False, ["app/web/checkout.ts"]))

    def test_units_keep_writers_with_readers_and_assign_every_file(self):
        sizes = flows.file_sizes(self.manifest)
        for limit in (120_000, 1_500):
            result = flows.units(self.links, sizes, ["."], limit)
            self.assertEqual((result["assigned"], result["files"]), (len(sizes), len(sizes)))
            for store in self.links["stores"].values():
                block = {s.split("::")[0] for s in store["writes"] + store["reads"]}
                self.assertTrue(any(block <= set(unit["files"]) for unit in result["units"]), block)
        self.assertEqual(flows.units(self.links, sizes, ["."], 1_500), flows.units(self.links, sizes, ["."], 1_500))

    def test_a_shared_file_is_a_member_of_few_units_and_context_in_the_others(self):
        sizes = flows.file_sizes(self.manifest)
        free = flows.units(self.links, sizes, ["."], 1_500)
        shared = flows.units(self.links, sizes, ["."], 1_500, share=1)
        self.assertGreater(free["in_several_units"], 0)
        self.assertEqual((shared["in_several_units"], shared["assigned"]), (0, len(sizes)))
        context = [file for unit in shared["units"] for file in unit.get("context", [])]
        self.assertTrue(context)
        for unit in shared["units"]:
            self.assertFalse(set(unit["files"]) & set(unit.get("context", [])))
        self.assertLessEqual(len(shared["cuts"]), len(free["cuts"]) + len(context))



class StoreUnitTests(unittest.TestCase):
    def test_cuts_name_only_readers_separated_from_the_writer(self):
        writer, reader = "a.py::write", "b.py::read"
        links = {"stores": {"orders/status": {"writes": [writer], "reads": [writer, reader]}},
                 "entries": [], "edges": [], "gaps": []}
        sizes = {"a.py": 8, "b.py": 8, "large.py": 13}
        small = flows.units(links, sizes, ["."], 10)
        self.assertEqual(small["cuts"], [{"type": "store", "store": "orders/status",
                                         "writer_file": "a.py", "reader_files": ["b.py"]}])
        self.assertEqual(small["oversized"], [{"file": "large.py", "bytes": 13, "limit": 10}])
        self.assertIn(["large.py"], [unit["files"] for unit in small["units"]])
        together = flows.units(links, sizes, ["a.py", "b.py"], 16)
        self.assertEqual((together["cuts"], together["oversized"]), ([], []))
        self.assertEqual(flows.units(links, sizes, ["a.py"], 10)["cuts"], [])
        store = "store:orders/status"
        links["entries"] = [{"symbol": writer}]
        links["edges"] = [{"from": writer, "to": store, "type": "scrive", "site": "a.py:2"},
                          {"from": store, "to": reader, "type": "legge", "site": "b.py:2"}]
        self.assertEqual(flows.units(links, sizes, ["."], 10)["cuts"], small["cuts"])


class WrittenRuleTests(unittest.TestCase):
    """Constructs that pass through library objects: a store created by a library, markup
    handlers, a decorated route on a router object, a collection reached by attribute."""

    SOURCES = {
        "web/store.ts": ("import { create } from 'state-lib';\n"
                         "export const useStore = create((set, get) => ({\n  count: 0,\n"
                         "  add: (n: number) => set((s) => ({ count: s.count + n })),\n"
                         "  bump: () => set((s) => {\n    // the user's tap, see https://example.org/a\n"
                         "    return { count: s.count + 1 };\n  }),\n"
                         "  reset: () => {\n    if (get().count === 0) return;\n    set({ count: 0 });\n  },\n"
                         "  label: 'n',\n  title: () => {\n    const state = get();\n    return state.label;\n  },\n"
                         "  total: () => {\n    const state = get();\n    return state.count;\n  },\n}));\n"
                         "export function report(): string {\n  const state = useStore.getState();\n"
                         "  if (state.count > 9) state.reset();\n  return `${state.count}`;\n}\n"),
        "web/urls.ts": "const BASE = '/api';\nexport const SAVE_URL = `${BASE}/save`;\n",
        "web/view.tsx": ("import { useStore } from './store';\nimport { SAVE_URL } from './urls';\n"
                         "declare function post(url: string, body: unknown): void;\n"
                         "interface Props { onClose: () => void; onPick(id: string): void }\n"
                         "export function View(props: Props) {\n  const { onPick } = props;\n"
                         "  const count = useStore((s) => s.count);\n  const add = useStore((s) => s.add);\n"
                         "  const save = () => {\n    post(SAVE_URL, { count });\n  };\n"
                         "  return (\n    <div>\n      <button onClick={() => add(1)}>+</button>\n"
                         "      <button onClick={save}>save</button>\n      <button onClick={props.onClose}>x</button>\n      <button onClick={onPick}>p</button>\n"
                         "      <button onClick={(add) => add(1)}>shadow</button>\n"
                         "      {count}\n    </div>\n  );\n}\n"),
        "api/handlers.py": ("from lib import APIRouter, db\n\nrouter = APIRouter()\n\n\n@router.post(\"/save\")\n"
                            "async def save(body):\n    await db.counters.update_one(  # the user's counter\n"
                            "        {\"half\": 7 // 2}, body)\n\n\n"
                            "async def total():\n    return await db.counters.find_one({})\n"),
        "api/repository.py": ("from lib import db\n\nCOUNTERS = \"counters\"\n\n\nclass Repository:\n"
                              "    def __init__(self, database):\n        self._collection = database[COUNTERS]\n\n"
                              "    async def load(self):\n        return await self._collection.find_one({})\n\n\n"
                              "async def audit(cache):\n    events = db.events\n    await events.find_one({})\n"
                              "    return await cache.find_one({})\n"),
    }
    RULES = [
        {"callee": "web/store.ts::useStore", "link": "legge", "store": "state", "key": "selector", "actions_in": ["web/store.ts"]},
        {"written": "get", "in": ["web/store.ts"], "link": "legge", "store": "state", "key": "member"},
        {"written": "useStore.getState", "in": ["web"], "link": "legge", "store": "state", "key": "member",
         "actions_in": ["web/store.ts"]},
        {"written": "set", "in": ["web/store.ts"], "link": "scrive", "store": "state", "key": "object"},
        {"written": "post", "in": ["web"], "link": "rotta", "strip": "${BASE}",
         "route": {"service": "api", "method": "POST", "path": "arg0"}},
        {"written": "router.get|post", "in": ["api"], "link": "offre", "decorates": True,
         "route": {"service": "api", "method": "part1", "path": "arg0"}},
        {"written": "db.*.find_one", "in": ["api"], "link": "legge", "store": "db", "key": "part1"},
        {"written": "db.*.update_one", "in": ["api"], "link": "scrive", "store": "db", "key": "part1"},
        {"written": "*.find_one", "in": ["api"], "link": "legge", "store": "db", "key": "holder"},
        {"written": "self.*.find_one", "in": ["api"], "link": "legge", "store": "db", "key": "holder"},
        {"attribute": "on*", "in": ["web"], "link": "attiva"},
    ]

    @classmethod
    def setUpClass(cls):
        cls.work = Path(tempfile.mkdtemp(prefix="flow-written-")).resolve()
        app = cls.work / "app"
        for rel, text in cls.SOURCES.items():
            (app / rel).parent.mkdir(parents=True, exist_ok=True)
            (app / rel).write_text(text, encoding="utf-8", newline="\n")
        for command in (["git", "init", "-q"], ["git", "add", "-A"],
                        ["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "fixture"]):
            subprocess.run(command, cwd=app, check=True, capture_output=True)
        manifest = cls.work / "snapshot/manifest.sqlite"
        snapshot.main(["write", str(app), "--out", str(manifest), "--no-engine", "--no-index"])
        rules = cls.work / "rules.json"
        rules.write_text(json.dumps({"schema": flows.RULES_SCHEMA, "rules": cls.RULES}), encoding="utf-8")
        cls.links = flows.link_facts(manifest, flows.load_rules(rules))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.work, True)

    def edges(self, kind):
        return {(edge["from"], edge["to"]) for edge in self.links["edges"] if edge["type"] == kind}

    def test_a_misplaced_or_unknown_field_is_refused_by_name(self):
        rules = self.work / "bad.json"
        for rule, message in (
                ({"written": "post", "link": "rotta", "route": {"service": "a", "method": "GET", "path": "arg0", "strip": "x"}},
                 "exactly service, method and path"),
                ({"written": "post", "link": "legge", "store": "s", "key": "arg0", "within": ["web"]}, "unknown field within")):
            rules.write_text(json.dumps({"schema": flows.RULES_SCHEMA, "rules": [rule]}), encoding="utf-8")
            with self.subTest(message=message), self.assertRaisesRegex(ValueError, message):
                flows.load_rules(rules)

    def test_a_store_function_is_named_by_its_property_and_keyed_by_what_it_returns(self):
        self.assertEqual(self.links["stores"]["state/count"],
                         {"writes": ["web/store.ts::add", "web/store.ts::bump", "web/store.ts::reset"],
                          "reads": ["web/store.ts::report", "web/store.ts::reset", "web/store.ts::total",
                                    "web/view.tsx::View"]})

    def test_a_selector_reads_every_field_it_names_through_a_wrapper_and_in_python(self):
        import entries

        def keys(expression: str, grammar: str):
            source = expression.encode()
            root = entries._parse(source, grammar)
            call = root.named_children[0]
            call = call if call.child_by_field_name("arguments") is not None else call.named_children[0]
            args = [value for _, value in entries._arguments(call, source)]
            call = {"args": args, "tree": flows.Tree("x", source, root, grammar), "parts": ["useStore"], "file": "x", "node": call}
            return flows._keys("selector", call, None)
        self.assertEqual(keys("useStore(shallow((s) => ({ n: s.count, r: s.reset })))", "typescript"), ["count", "reset"])
        self.assertEqual(keys("useStore((s) => s.count)", "typescript"), ["count"])
        self.assertEqual(keys("useStore(lambda s: (s.count, s.reset))", "python"), ["count", "reset"])
        self.assertIsNone(keys("useStore(selectCount)", "typescript"))  # a name: no parameter is read

    def test_a_held_state_is_read_only_inside_the_function_that_holds_it(self):
        # `title` holds the state and reads `label`; the `count` read a few lines below belongs to `total`.
        self.assertEqual(self.links["stores"]["state/label"]["reads"], ["web/store.ts::title"])
        self.assertNotIn("web/store.ts::title", self.links["stores"]["state/count"]["reads"])
        self.assertIn("web/store.ts::total", self.links["stores"]["state/count"]["reads"])

    def test_a_state_held_whole_gives_the_properties_read_on_its_variable(self):
        self.assertIn(("web/store.ts::report", "web/store.ts::reset"), self.edges("chiama"))

    def test_a_held_store_function_is_called_where_its_variable_is(self):
        handler = "web/view.tsx::function@14:23"
        self.assertIn(("web/view.tsx::View", handler), self.edges("attiva"))
        self.assertIn((handler, "web/store.ts::add"), self.edges("chiama"))
        shadow = next(e["to"] for e in self.links["edges"] if e.get("label") == "shadow")
        self.assertNotIn((shadow, "web/store.ts::add"), self.edges("chiama"))
        self.assertNotIn("state/add", self.links["stores"])

    def test_markup_handlers_are_entry_points_and_a_passed_parameter_is_not(self):
        actions = sorted(entry["symbol"] for entry in self.links["entries"] if entry["kind"] == "azione")
        self.assertEqual(actions, ["web/view.tsx::View.save", "web/view.tsx::function@14:23", "web/view.tsx::function@18:23"])

    def test_a_templated_constant_reaches_the_decorated_route_and_its_collection(self):
        self.assertIn(("web/view.tsx::View.save", "api/handlers.py::save"), self.edges("chiama"))
        self.assertEqual(self.links["stores"]["db/counters"],
                         {"writes": ["api/handlers.py::save"],
                          "reads": ["api/handlers.py::total", "api/repository.py::Repository.load"]})
        # A handle assigned from the store gives its key; a receiver never assigned from it is no access.
        self.assertEqual(self.links["stores"]["db/events"], {"writes": [], "reads": ["api/repository.py::audit"]})
        flow = flows.trace(self.links, "web/view.tsx::View.save", "from")
        self.assertIn("api/handlers.py::total", flow["nodes"])
        self.assertEqual(self.links["gaps"], [])


class HandlerRouteTests(unittest.TestCase):
    """Routes registered outside any function, with the handler passed as an argument (Express and the like)."""

    SOURCES = {
        "api/db.js": "module.exports = { find() {}, save() {} };\n",
        "api/controller.js": ("const db = require('./db');\n\nconst controller = {\n"
                              "    async status(req, res) {\n        res.json(await db.find('plans'));\n    },\n};\n\n"
                              "module.exports = controller;\n"),
        "api/routes.js": ("const express = require('express');\nconst router = express.Router();\n"
                          "const controller = require('./controller');\nconst db = require('./db');\n\n"
                          "function requireAuth(req, res, next) {\n    next();\n}\n\n"
                          "router.get('/billing', controller.status);\n"
                          "router.post('/task', requireAuth, async (req, res) => {\n"
                          "    await db.save('tasks', req.body);\n    res.json({});\n});\n"
                          "router.get('/odd', makeHandler());\n\nmodule.exports = router;\n"),
        # Code outside any named function: at module level, and in a callback passed as an argument.
        "api/app.js": ("const routes = require('./routes');\nfunction mount(r) {\n    return r;\n}\n"
                       "mount(routes);\nsetup(() => {\n    mount(routes);\n});\n"),
        # A component written as an element: React calls it, so the parent reaches it.
        "web/Paywall.tsx": "export function Paywall() {\n  return null;\n}\n",
        "web/Home.tsx": ("import { Paywall } from './Paywall';\n"
                         "export function Home() {\n  return <div><Paywall /></div>;\n}\n"),
        "web/client.ts": ("declare function apiGet(url: string): void;\ndeclare function apiPath(p: string): string;\n"
                          "export function loadPlans() {\n  apiGet('/billing');\n}\n"
                          "export function addTask() {\n  fetch(apiPath('/task'), { method: 'POST', credentials: 'include' });\n}\n"
                          "export function readBilling() {\n  fetch(apiPath('/billing'));\n}\n"
                          "export function openTask(id: string) {\n  fetch(apiPath(`/task/${id}`));\n}\n"),
    }
    RULES = [
        {"written": "router.get|post", "in": ["api"], "link": "offre", "handler": "last",
         "route": {"service": "api", "method": "part1", "path": "arg0"}},
        {"written": "db.find", "in": ["api"], "link": "legge", "store": "db", "key": "arg0"},
        {"written": "db.save", "in": ["api"], "link": "scrive", "store": "db", "key": "arg0"},
        {"written": "apiGet", "in": ["web"], "link": "rotta", "route": {"service": "api", "method": "GET", "path": "arg0"}},
        # The path is the argument of the call written first; the method a key of the options, GET when absent.
        {"written": "fetch", "in": ["web"], "link": "rotta",
         "route": {"service": "api", "method": "arg1.method|GET", "path": "arg0.arg0"}},
    ]

    @classmethod
    def setUpClass(cls):
        cls.work = Path(tempfile.mkdtemp(prefix="flow-handler-")).resolve()
        app = cls.work / "app"
        for rel, text in cls.SOURCES.items():
            (app / rel).parent.mkdir(parents=True, exist_ok=True)
            (app / rel).write_text(text, encoding="utf-8", newline="\n")
        for command in (["git", "init", "-q"], ["git", "add", "-A"],
                        ["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "fixture"]):
            subprocess.run(command, cwd=app, check=True, capture_output=True)
        cls.manifest = cls.work / "snapshot/manifest.sqlite"
        snapshot.main(["write", str(app), "--out", str(cls.manifest), "--no-engine", "--no-index"])
        cls.links = flows.link_facts(cls.manifest, flows.validate_rules(cls.RULES))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.work, True)

    def test_the_route_belongs_to_the_handler_it_is_given(self):
        routes = {e["symbol"] for e in self.links["entries"] if e["kind"] == "rotta"}
        self.assertEqual(routes, {"api/controller.js::status", "api/routes.js::POST /task"})
        linked = {(e["from"], e["to"]) for e in self.links["edges"] if e.get("route")}
        self.assertEqual(linked, {("web/client.ts::loadPlans", "api/controller.js::status"),
                                  ("web/client.ts::readBilling", "api/controller.js::status"),
                                  ("web/client.ts::addTask", "api/routes.js::POST /task")})
        self.assertEqual(self.links["routes"], {"offered": 2, "called": 4, "linked": 3})  # GET /task/{}: no route

    def test_an_inline_handler_is_named_by_its_route_and_holds_its_accesses(self):
        self.assertEqual(self.links["stores"]["db/tasks"], {"writes": ["api/routes.js::POST /task"], "reads": []})
        self.assertEqual(self.links["stores"]["db/plans"], {"writes": [], "reads": ["api/controller.js::status"]})

    def test_code_outside_a_named_function_belongs_to_its_module(self):
        calls = {(e["from"], e["to"], e["site"]) for e in self.links["edges"] if e["type"] == "chiama"}
        self.assertIn(("api/app.js::<module>", "api/app.js::mount", "api/app.js:5"), calls)
        self.assertIn(("api/app.js::<module>", "api/app.js::mount", "api/app.js:7"), calls)

    def test_a_component_written_as_an_element_is_reached_by_its_parent(self):
        calls = {(e["from"], e["to"], e["site"]) for e in self.links["edges"] if e["type"] == "chiama"}
        self.assertIn(("web/Home.tsx::Home", "web/Paywall.tsx::Paywall", "web/Home.tsx:3"), calls)

    def test_a_handler_that_is_no_function_is_a_gap(self):
        self.assertEqual([g["reason"] for g in self.links["gaps"]],
                         ["offre: handler not a function", "route api GET /task/{}: no handler"])  # a single side

    def test_handler_is_an_argument_or_last_and_excludes_decorates(self):
        for rule, message in (
                ({"written": "r.get", "link": "offre", "handler": "first", "route": {"service": "a", "method": "GET", "path": "arg0"}},
                 "handler is argN or last"),
                ({"written": "r.get", "link": "offre", "handler": "last", "decorates": True,
                  "route": {"service": "a", "method": "GET", "path": "arg0"}}, "handler or decorates")):
            with self.subTest(message=message), self.assertRaisesRegex(ValueError, message):
                flows.validate_rules([rule])


class TreeReadTests(unittest.TestCase):
    """A call's arguments, the value of a constant, the handle a call is made on and the keys it names are read from
    the file's syntax tree and the snapshot's resolution of its names: never from the lines of the file."""

    SOURCES = {
        "api/handles.js": ("// const users = db.legacy_users;\nconst users = db.users;\n"
                           "export function load() {\n  return users.find({});\n}\n"
                           "export function admins() {\n  const users = db.admins;\n  return users.find({});\n}\n"
                           "export function stray() {\n  return elsewhere.find({});\n}\n"
                           "export function viaParameter(users) {\n  return users.find({});\n}\n"
                           "export function viaExpression(items) {\n  return items.filter(Boolean).find({});\n}\n"
                           "export function late() {\n  let rows;\n  rows = db.late;\n  return rows.find({});\n}\n"),
        "api/handles.py": ("from lib import db\n\nusers = db.users; orders = db.orders\n\n\ndef load():\n"
                           "    return users.find()\n\n\nclass Left:\n    def __init__(self):\n        self._c = db.alpha\n\n"
                           "    def load(self):\n        return self._c.find()\n\n\nclass Right:\n"
                           "    def __init__(self):\n        self._c = db.beta\n\n    def load(self):\n        return self._c.find()\n"),
        "api/routes.js": ("function create(req, res) {}\nfunction save(req, res) {}\nfunction list(req, res) {}\n"
                          "router.post('/orders', create);\nrouter.post('/api/save', save);\nrouter.get('/orders', list);\n"),
        "web/consts.ts": ("declare const version: string;\ndeclare function post(url: string): void;\n"
                          "declare function fetch(url: string, init?: { method?: string }): void;\n"
                          "const BASE = \"/api\" + version;\nconst SAVE = \"/api/save\";\nconst method = \"POST\";\n"
                          "export function computed() {\n  post(BASE);\n}\nexport function literal() {\n  post(SAVE);\n}\n"
                          "export function viaShorthand() {\n  fetch(\"/orders\", { method });\n}\n"
                          "export function viaParameter(method: string) {\n  fetch(\"/orders\", { method });\n}\n"
                          "export function viaDefault() {\n  fetch(\"/orders\");\n}\n"
                          "declare const key: string;\n"
                          "export function viaQuoted() {\n  fetch(\"/orders\", { 'method': 'POST' });\n}\n"
                          "export function viaNumeric() {\n  fetch(\"/orders\", { 1: 'x', method: 'POST' });\n}\n"
                          "export function viaComputed() {\n  fetch(\"/orders\", { ['method']: 'POST' });\n}\n"
                          "export function viaComputedBeside() {\n  fetch(\"/orders\", { [key]: 'x', method: 'POST' });\n}\n"
                          "export function viaPrototype() {\n  fetch(\"/orders\", { __proto__: { method: 'POST' } } as any);\n}\n"),
        "web/state.ts": ("declare function useStore(): any;\ndeclare function pick(f: any): any;\n"
                         "declare function shallow(f: any): any;\ndeclare function put(v: any): void;\n"
                         "declare function log(m: string): void;\n"
                         "export function show() {\n  const user = useStore();\n  log(\"user.password is masked\");\n"
                         "  return user.name;\n}\n"
                         "export function unpack() {\n  const { items = [], total } = useStore();\n  return items.length + total;\n}\n"
                         "export function chosen() {\n  return pick((s: any) => [s.a, s.list.map((s: any) => s.id)]);\n}\n"
                         "export function either() {\n  return pick((s: any) => s.a ?? s.b);\n}\n"
                         "export function wrapped() {\n  return pick(shallow((s: any) => ({ n: s.count, r: s.reset })));\n}\n"
                         "export function written() {\n  put(() => { // it's\n    log(\"return {secret}\");\n    return { a: '//x' }; /* b's */\n  });\n}\n"
                         "export function methods() {\n  put({ save() { return 1; }, load: log });\n}\n"),
        "web/label.ts": ("function run() {}\nfunction fallback() {}\nexport function setup(ready: boolean) {\n"
                         "  const choose = ready ? fallback : () => run();\n  return choose;\n}\n"),
        "web/keyword.py": "def keyword():\n    post(path=\"/api/save\")\n\n\ndef positional():\n    post(\"/api/save\")\n",
        "web/Compare.tsx": ("export function Paywall() {\n  return null;\n}\n"
                            "export function Home(a: number) {\n  return a <Paywall;\n}\n"),
    }
    RULES = [
        {"written": "*.find", "in": ["api"], "link": "legge", "store": "db", "key": "holder"},
        {"written": "self.*.find", "in": ["api"], "link": "legge", "store": "db", "key": "holder"},
        {"written": "router.get|post", "in": ["api"], "link": "offre", "handler": "last",
         "route": {"service": "api", "method": "part1", "path": "arg0"}},
        {"written": "post", "in": ["web"], "link": "rotta", "route": {"service": "api", "method": "POST", "path": "arg0"}},
        {"written": "fetch", "in": ["web"], "link": "rotta",
         "route": {"service": "api", "method": "arg1.method|GET", "path": "arg0"}},
        {"written": "useStore", "in": ["web"], "link": "legge", "store": "s", "key": "member"},
        {"written": "pick", "in": ["web"], "link": "legge", "store": "sel", "key": "selector"},
        {"written": "put", "in": ["web"], "link": "scrive", "store": "obj", "key": "object"},
    ]

    @classmethod
    def setUpClass(cls):
        cls.work = Path(tempfile.mkdtemp(prefix="flow-tree-")).resolve()
        cls.manifest = read_project(cls.work, cls.SOURCES)
        cls.links = flows.link_facts(cls.manifest, flows.validate_rules(cls.RULES))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.work, True)

    def reads(self, store: str, file: str) -> list[str]:
        return [symbol for symbol in self.links["stores"].get(store, {"reads": []})["reads"] if symbol.startswith(file)]

    def test_a_handle_is_the_assignment_the_snapshot_resolves_its_name_to(self):
        # `// const users = db.legacy_users;` is a comment; the `users` of each function is its own.
        self.assertEqual(self.reads("db/users", "api/handles.js"), ["api/handles.js::load"])
        self.assertEqual(self.reads("db/admins", "api/handles.js"), ["api/handles.js::admins"])
        self.assertNotIn("db/legacy_users", self.links["stores"])
        # a declaration with no value, assigned after: the only assignment is the handle's.
        self.assertEqual(self.reads("db/late", "api/handles.js"), ["api/handles.js::late"])
        # two statements on one line: the handle is the one assigned to its own name.
        self.assertEqual(self.reads("db/users", "api/handles.py"), ["api/handles.py::load"])
        self.assertNotIn("db/orders", self.links["stores"])

    def test_a_handle_held_by_an_attribute_is_the_assignment_of_the_class_that_holds_it(self):
        for name, owner in (("alpha", "Left"), ("beta", "Right")):
            self.assertEqual(self.links["stores"][f"db/{name}"]["reads"], [f"api/handles.py::{owner}.load"], name)

    def test_a_receiver_the_snapshot_does_not_resolve_is_a_gap_and_a_parameter_is_no_handle(self):
        reasons = [g["reason"] for g in self.links["gaps"] if g["site"].startswith("api/handles.js")]
        self.assertEqual(len(reasons), 1)
        self.assertIn("elsewhere", reasons[0])
        self.assertFalse([s for store in self.links["stores"].values() for s in store["reads"] if "viaParameter" in s])

    def test_a_constant_that_is_computed_is_a_gap_not_its_literal_half(self):
        gaps = {g["symbol"]: g["reason"] for g in self.links["gaps"] if g["site"].startswith("web/consts.ts")}
        self.assertEqual(gaps["web/consts.ts::computed"], "rotta: route not a literal")

    def test_a_key_of_an_object_argument_is_its_constant_or_a_gap_and_the_default_only_when_absent(self):
        linked = {(e["from"], e["to"], tuple(e["route"])) for e in self.links["edges"]
                  if e.get("route") and e["from"].startswith("web/consts.ts")}
        self.assertEqual(linked, {
            ("web/consts.ts::literal", "api/routes.js::save", ("api", "POST", "/api/save")),
            ("web/consts.ts::viaShorthand", "api/routes.js::create", ("api", "POST", "/orders")),  # `{ method }`: a constant
            ("web/consts.ts::viaDefault", "api/routes.js::list", ("api", "GET", "/orders")),  # no options: the default
            ("web/consts.ts::viaQuoted", "api/routes.js::create", ("api", "POST", "/orders")),  # a string key is a key
            ("web/consts.ts::viaNumeric", "api/routes.js::create", ("api", "POST", "/orders"))})  # a number is no `method`
        gaps = {g["symbol"]: g["reason"] for g in self.links["gaps"] if g["site"].startswith("web/consts.ts")}
        self.assertEqual(gaps["web/consts.ts::viaParameter"], "rotta: route not a literal")  # `{ method }`, a parameter

    def test_a_computed_key_or_a_prototype_makes_the_members_of_the_options_unknown_as_a_spread_does(self):
        """`{ ['method']: 'POST' }` and `{ __proto__: { method: 'POST' } }` hold a `method` the reader cannot see as a key:
        reading the default `GET` there would be a false route."""
        linked = {e["from"] for e in self.links["edges"] if e.get("route") and e["from"].startswith("web/consts.ts")}
        gaps = {g["symbol"]: g["reason"] for g in self.links["gaps"] if g["site"].startswith("web/consts.ts")}
        for name in ("viaComputed", "viaComputedBeside", "viaPrototype"):
            with self.subTest(name):
                self.assertNotIn(f"web/consts.ts::{name}", linked)
                self.assertEqual(gaps[f"web/consts.ts::{name}"], "rotta: route not a literal")

    def test_the_keys_read_on_a_held_value_are_the_snapshots_not_those_of_a_string_or_a_default(self):
        self.assertEqual({k: v["reads"] for k, v in self.links["stores"].items() if k.startswith("s/")},
                         {"s/items": ["web/state.ts::unpack"], "s/name": ["web/state.ts::show"],
                          "s/total": ["web/state.ts::unpack"]})

    def test_a_selector_reads_every_field_of_its_own_parameter(self):
        chosen, either, wrapped = ("web/state.ts::" + n for n in ("chosen", "either", "wrapped"))
        self.assertEqual({k: v["reads"] for k, v in self.links["stores"].items() if k.startswith("sel/")},
                         {"sel/a": sorted([chosen, either]), "sel/b": [either], "sel/list": [chosen],
                          "sel/count": [wrapped], "sel/reset": [wrapped]})

    def test_an_object_names_its_keys_and_the_keys_of_what_a_function_returns_not_those_of_a_string(self):
        self.assertEqual({k: v["writes"] for k, v in self.links["stores"].items() if k.startswith("obj/")},
                         {"obj/a": ["web/state.ts::written"], "obj/load": ["web/state.ts::methods"],
                          "obj/save": ["web/state.ts::methods"]})

    def test_an_anonymous_function_is_named_by_the_property_it_is_the_value_of_not_by_a_ternary_branch(self):
        calls = {(e["from"], e["to"]) for e in self.links["edges"] if e["type"] == "chiama"}
        self.assertIn(("web/label.ts::setup", "web/label.ts::run"), calls)

    def test_an_argument_with_a_keyword_is_not_the_one_a_rule_counts_by_position(self):
        gaps = {g["symbol"]: g["reason"] for g in self.links["gaps"] if g["site"].startswith("web/keyword.py")}
        self.assertEqual(gaps, {"web/keyword.py::keyword": "rotta: route not a literal"})  # `post(path=...)` is no arg0
        self.assertIn(("web/keyword.py::positional", "api/routes.js::save"),
                      {(e["from"], e["to"]) for e in self.links["edges"] if e.get("route")})

    def test_a_comparison_is_no_element(self):
        calls = {(e["from"], e["to"]) for e in self.links["edges"] if e["type"] == "chiama"}
        self.assertNotIn(("web/Compare.tsx::Home", "web/Compare.tsx::Paywall"), calls)

    def test_a_file_edited_since_the_snapshot_is_a_gap_not_a_link_read_from_the_new_text(self):
        work = Path(tempfile.mkdtemp(prefix="flow-edited-")).resolve()
        self.addCleanup(shutil.rmtree, work, True)
        manifest = read_project(work, {"web/save.ts": "declare function post(url: string): void;\nexport function save() {\n  post('/api/save');\n}\n"})
        rules = flows.validate_rules([rule for rule in self.RULES if rule.get("written") == "post"])
        self.assertEqual(flows.link_facts(manifest, rules)["routes"]["called"], 1)
        (work / "app/web/save.ts").write_text("declare function post(url: string): void;\nexport function save() {\n  post('/api/other');\n}\n",
                                              encoding="utf-8", newline="\n")
        links = flows.link_facts(manifest, rules)
        self.assertEqual(links["routes"]["called"], 0)
        self.assertEqual([g["reason"] for g in links["gaps"]], ["call arguments not readable"])

    def test_a_grammar_that_does_not_load_is_a_gap_with_its_cause_not_a_link_read_from_the_text(self):
        import entries
        self.assertGreater(self.links["routes"]["called"], 0)
        with mock.patch.object(entries._treesitter, "get_parser", return_value=None), \
                mock.patch.object(entries._treesitter, "load_failure", return_value="OSError: no library"):
            links = flows.link_facts(self.manifest, flows.validate_rules(self.RULES))
        reasons = {g["reason"] for g in links["gaps"] if g["site"].startswith("web/consts.ts")}
        self.assertIn("call arguments not readable: grammar typescript not loaded: OSError: no library", reasons)
        self.assertEqual((links["routes"]["called"], links["stores"]), (0, {}))


class RestSchemaTests(unittest.TestCase):
    """REST links by method and path schema, on the fixture in benchmarks/connection-points/fixtures/pets."""

    CASE = ROOT / "benchmarks/connection-points/fixtures/pets"

    @classmethod
    def setUpClass(cls):
        cls.work = Path(tempfile.mkdtemp(prefix="flow-rest-")).resolve()
        app = cls.work / "app"
        shutil.copytree(cls.CASE / "app", app)
        for command in (["git", "init", "-q"], ["git", "add", "-A"],
                        ["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "fixture"]):
            subprocess.run(command, cwd=app, check=True, capture_output=True)
        manifest = cls.work / "snapshot/manifest.sqlite"
        snapshot.main(["write", str(app), "--out", str(manifest), "--no-engine", "--no-index"])
        cls.links = flows.link_facts(manifest, flows.load_rules(cls.CASE / "rules.json"))
        cls.expected = json.loads((cls.CASE / "expected.json").read_text(encoding="utf-8"))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.work, True)

    def test_a_call_joins_the_route_its_method_and_path_schema_meet(self):
        linked = {(e["from"], e["to"], tuple(e["route"])) for e in self.links["edges"] if e.get("route")}
        self.assertEqual(linked, {(l["caller"], l["handler"], tuple(l["route"])) for l in self.expected["links"]})
        self.assertEqual(self.links["routes"], self.expected["routes"])

    def test_a_schema_that_meets_several_routes_is_uncertain_and_no_link(self):
        uncertain = [(g["symbol"], g["candidates"]) for g in self.links["gaps"] if g.get("candidates")]
        self.assertEqual(uncertain, [(u["caller"], u["candidates"]) for u in self.expected["uncertain"]])
        self.assertNotIn("web/api.ts::fetchBreed", {e["from"] for e in self.links["edges"] if e.get("route")})

    def test_a_computed_path_is_a_gap_and_a_route_nobody_calls_a_single_side(self):
        self.assertEqual([(g["symbol"], g["reason"]) for g in self.links["gaps"] if not g.get("candidates")],
                         [(g["caller"], "rotta: route not a literal") for g in self.expected["gaps"]])
        for side in self.expected["uncalled"]:
            self.assertIn((side["handler"], "rotta"), {(e["symbol"], e["kind"]) for e in self.links["entries"]})
            self.assertNotIn(side["handler"], {e["to"] for e in self.links["edges"] if e.get("route")})
            self.assertNotIn(side["handler"], {g.get("symbol") for g in self.links["gaps"]})

    def test_a_path_key_keeps_the_schema_and_drops_base_url_and_query(self):
        key = flows.REST.key
        for path in ("/api/dogs/${dogId}", "/api/dogs/<int:id>", "/api/dogs/<id>", "/api/dogs/:id",
                     "/api/dogs/{id}", "api/dogs/{id:int}/", "${BASE}/api/dogs/${id}?full=1#top",
                     "https://example.org:5000/api/dogs/${id}", "${A}${B}/api/dogs/${x ? '?' : y}"):
            with self.subTest(path=path):
                self.assertEqual(key("api", "get", path), ("api", "GET", "/api/dogs/{}"))
        self.assertEqual(key("api", "GET", "/<lang>/about"), ("api", "GET", "/{}/about"))  # declared, not computed
        self.assertEqual(key("api", "GET", "/api/tasks${query}"), ("api", "GET", "/api/tasks{}"))
        for path in ("${API}${path}", "${API}/${path}", "${API}api/dogs", "${API}", "", "/api/${x"):
            with self.subTest(path=path):
                self.assertIsNone(key("api", "GET", path))
        self.assertIsNone(key(None, "GET", "/a"))
        self.assertEqual(key("api", "GET", "//cdn.example.com/v1/items"), ("api", "GET", "/v1/items"))  # the host is no segment
        self.assertEqual(key("api", "GET", "file:///etc/x?y"), ("api", "GET", "/etc/x"))
        self.assertEqual(key("api", "GET", "items:batch?x=1"), ("api", "GET", "/items:batch"))  # a scheme with no host stays
        self.assertIsNone(key("api", "GET", "//[x/api"))  # a host in brackets that never closes: no reader accepts it
        self.assertIsNone(key("api", "GET", "https://example.org"))  # nothing after the base

    def test_the_most_literal_route_wins_and_a_tie_is_uncertain(self):
        routes = [{"id": r, "key": flows.REST.key("api", "GET", r)}
                  for r in ("/api/dogs/search", "/api/dogs/<int:id>", "/api/tasks", "/api/cats/<a>", "/api/cats/<b>")]

        def met(path, method="GET"):
            [(_, found)] = flows.join(flows.REST, [{"key": flows.REST.key("api", method, path)}], routes)
            return [r["id"] for r in found]
        self.assertEqual(met("/api/dogs/search"), ["/api/dogs/search"])
        self.assertEqual(met("/api/dogs/7"), ["/api/dogs/<int:id>"])
        self.assertEqual(met("/api/dogs/${id}"), ["/api/dogs/<int:id>"])  # a placeholder meets a placeholder first
        self.assertEqual(met("/api/tasks${query}"), ["/api/tasks"])  # loose: the hole glued to a literal
        self.assertEqual(met("/api/cats/${id}"), ["/api/cats/<a>", "/api/cats/<b>"])
        self.assertEqual(len(met("/api/${kind}/${id}")), 4)  # holes meet literals loosely: every candidate stays
        self.assertEqual(met("/api/dogs/7", "POST"), [])
        self.assertEqual(met("/api/dogs/7/x"), [])


class StoreReadTests(unittest.TestCase):
    """A component the lexical resolver cannot place, named by a read the edge store answers."""

    SOURCES = {
        "web/Paywall.tsx": "export function Paywall() {\n  return null;\n}\n",
        "web/ui.ts": "import { Paywall } from './Paywall';\nexport const Gate = Paywall;\n",
        "web/Home.tsx": "import { Gate } from './ui';\nexport function Home() {\n  return <div><Gate /></div>;\n}\n",
    }

    def test_a_read_known_only_to_the_store_links_the_parent_to_the_component(self):
        import resolve_edges
        from snapshot_store import open_snapshot
        work = Path(tempfile.mkdtemp(prefix="flow-store-")).resolve()
        self.addCleanup(shutil.rmtree, work, True)
        for rel, text in self.SOURCES.items():
            (work / "app" / rel).parent.mkdir(parents=True, exist_ok=True)
            (work / "app" / rel).write_text(text, encoding="utf-8", newline="\n")
        manifest = work / "manifest.sqlite"
        snapshot.read_project(work / "app", manifest)
        link = ("web/Home.tsx::Home", "web/Paywall.tsx::Paywall", "web/Home.tsx:3")

        def calls():
            return {(e["from"], e["to"], e["site"]) for e in flows.link_facts(manifest, [])["edges"]
                    if e["type"] == "chiama"}

        self.assertNotIn(link, calls())
        with open_snapshot(manifest) as store:
            identity, caller, resolution = store.connection.execute(
                "SELECT id, caller, resolution FROM sem_references WHERE file='web/Home.tsx' AND kind='read'").fetchone()
            target = store.connection.execute(
                "SELECT id FROM sem_declarations WHERE file='web/Paywall.tsx' AND name='Paywall'").fetchone()[0]
            self.assertEqual(resolution, "unresolved")
            binding = resolve_edges.store_binding(store, manifest, store.metadata.get("parser_fingerprint"),
                                                  {"typescript": {"engine": "scip-typescript@0.5.2", "state": "fresh"}},
                                                  {})
        resolve_edges.write_edge_store(resolve_edges.default_edge_store(manifest), [{
            "reference_id": identity, "file": "web/Home.tsx", "language": "typescript", "kind": "read",
            "caller": caller, "l0": 3, "c0": 15, "verdict": "project-callable", "target_id": target,
            "symbol": "scip-typescript npm app 1.0.0 web/`Paywall.tsx`/Paywall().", "resolver": "scip-typescript@0.5.2",
            "confidence": "confirmed", "payload": {"chain": ["same-range"]}}], binding)
        self.assertIn(link, calls())


class RenderOfAnImportedNameTests(unittest.TestCase):
    """A component written as an element is rendered by the project's function of that name only when the file
    imports the name from a file of the project: a package's `Button` is not the project's."""

    BUTTON = "export function Button(props: any) {\n  return null;\n}\n"

    def renders(self, imported: str) -> set[tuple[str, str]]:
        work = Path(tempfile.mkdtemp(prefix="flow-render-")).resolve()
        self.addCleanup(shutil.rmtree, work, True)
        project = work / "app"
        for rel, text in {"web/ui/Button.tsx": self.BUTTON,
                          "web/Bar.tsx": f"{imported}\nexport function Bar() {{\n  return <div><Button /></div>;\n}}\n"}.items():
            (project / rel).parent.mkdir(parents=True, exist_ok=True)
            (project / rel).write_text(text, encoding="utf-8")
        manifest = work / "out" / "manifest.sqlite"
        snapshot.read_project(project, manifest)
        return {(e["from"], e["to"]) for e in flows.link_facts(manifest, [])["edges"] if e["type"] == "chiama"}

    def test_a_component_a_package_exports_is_not_rendered_as_the_project_s_of_that_name(self):
        self.assertEqual(self.renders("import { Button } from '@mui/material';"), set())

    def test_a_component_imported_from_a_file_of_the_project_is_rendered(self):
        self.assertEqual(self.renders("import { Button } from './ui/Button';"),
                         {("web/Bar.tsx::Bar", "web/ui/Button.tsx::Button")})


class ExternalServiceTests(unittest.TestCase):
    """The services of others the links know are the ones the stack step and the module graph give, by id."""

    CODE = {"app/pay.py": "def charge(amount):\n    return amount\n\n\ndef refund(amount):\n    return amount\n",
            "app/hook.py": "def event(body):\n    return body\n"}
    PROVIDER = {"codebase-modules.json": json.dumps({"schema": "daodan/declared-modules/v1", "modules": [
        {"name": "card payment provider", "kind": "component", "location": "external", "responsibility": "Charges cards",
         "members": [], "evidence": ["app/pay.py"]}]})}

    def setUp(self):
        self.work = Path(tempfile.mkdtemp(prefix="flow-services-")).resolve()
        self.addCleanup(shutil.rmtree, self.work, True)

    def snapshot(self, files) -> Path:
        project = self.work / "proj"
        for rel, text in files.items():
            (project / rel).parent.mkdir(parents=True, exist_ok=True)
            (project / rel).write_text(text, encoding="utf-8")
        manifest = self.work / "out" / "manifest.sqlite"
        snapshot.read_project(project, manifest)
        return manifest

    @staticmethod
    def stack(manifest: Path, *services, libraries=(), kind="service") -> None:
        """The stack step's record with each service `(id, name, the files that declare it)`, and the packages
        `(ecosystem, name, id)` a module of the project declares that the registry knows for a service."""
        record = {"schema": "daodan/technologies/v1", "technologies": [
            {"id": ident, "name": name, "kind": kind, "type": "gateway",
             "signs": [{"sign": "package", "strength": "declared", "path": path, "line": 1, "value": ident}
                       for path in paths]} for ident, name, paths in services],
            "modules": [{"libraries": [{"ecosystem": ecosystem, "name": name, "path": "requirements.txt", "id": ident}
                                       for ecosystem, name, ident in libraries]}]}
        manifest.with_name("technologies.json").write_text(json.dumps(record), encoding="utf-8")

    @staticmethod
    def engine(manifest: Path, calls: dict, *, language="python", left_out=(), types=()) -> None:
        """The edge store of an engine that ran for `language`: the call of the snapshot at each `(file, line)` of
        `calls` ends in the package given there (`(manager, package)`); `left_out` are files its index has no
        document of; `types` the type packages its indexer added (`name@version`)."""
        import resolve_edges
        from snapshot_store import open_snapshot
        with open_snapshot(manifest) as store:
            sites = store.connection.execute(
                "SELECT id, file, caller, l0, c0 FROM sem_references WHERE kind='call'").fetchall()
            files = {"snapshot": 3, "indexed": 3 - len(left_out), "missing": [{"path": p, "reason": "no document in the index"}
                                                                       for p in left_out]}
            entry = {"engine": "scip-python@0.6.8", "state": "fresh", "coverage": {"state": "complete", "files": files}}
            if types:  # an entry of a native index names the adapter that wrote it: the view drops one it does not know
                import engine_pass
                import importlib
                spec = engine_pass.ENGINE_LANGUAGES[language]
                version = importlib.import_module(f"indexers.{spec.indexer}").VERSION
                entry.update(engine=f"{spec.name}@{version}", adapter_digest=engine_pass.adapter_fingerprint(spec.indexer),
                             indexer={"version": version, "types": list(types)})
            entries = {language: entry}
            binding = resolve_edges.store_binding(store, manifest, store.metadata.get("parser_fingerprint"), entries, {})
        edges = [{"reference_id": identity, "file": file, "language": language, "kind": "call", "caller": caller,
                  "l0": line, "c0": column, "verdict": "external", "target_id": None,
                  "symbol": f"scip-python {calls[file, line][0]} {calls[file, line][1]} 1.0 `{calls[file, line][1]}`/send().",
                  "resolver": "scip-python@0.6.8", "confidence": "confirmed", "payload": {"reason": "external"},
                  "external": {"manager": calls[file, line][0], "package": calls[file, line][1], "version": "1.0"}}
                 for identity, file, caller, line, column in sites if (file, line) in calls]
        resolve_edges.write_edge_store(resolve_edges.default_edge_store(manifest), edges, binding)

    @staticmethod
    def used(links) -> list[tuple]:
        return [(e["from"], e["to"], e["site"], e["origin"]) for e in links["edges"] if e["type"] == "usa"]

    def test_a_service_only_the_stack_step_recognises_is_a_node_the_symbols_of_its_files_use(self):
        manifest = self.snapshot(self.CODE)
        self.stack(manifest, ("cardpay", "Card Pay", ["app/pay.py"]))
        links = flows.link_facts(manifest, [])
        self.assertEqual(links["external"], [{"id": "cardpay", "name": "cardpay", "status": "inferred"}])
        self.assertEqual(self.used(links), [("app/pay.py::charge", "module:cardpay", "app/pay.py", "dichiarato"),
                                            ("app/pay.py::refund", "module:cardpay", "app/pay.py", "dichiarato")])

    def test_a_service_only_the_module_graph_knows_is_as_it_was(self):
        links = flows.link_facts(self.snapshot({**self.CODE, **self.PROVIDER}), [])
        self.assertEqual([(m["name"], m["status"]) for m in links["external"]], [("card payment provider", "confirmed")])
        self.assertEqual(self.used(links), [
            ("app/pay.py::charge", "module:card payment provider", "app/pay.py", "dichiarato"),
            ("app/pay.py::refund", "module:card payment provider", "app/pay.py", "dichiarato")])

    def test_a_service_both_know_is_one_node_named_as_the_graph_names_it_with_the_files_of_both(self):
        manifest = self.snapshot({**self.CODE, **self.PROVIDER})
        self.stack(manifest, ("card-payment-provider", "Card payment provider", ["app/hook.py"]))
        links = flows.link_facts(manifest, [])
        self.assertEqual([m["name"] for m in links["external"]], ["card payment provider"])
        self.assertEqual(sorted(edge[:2] for edge in self.used(links)), [
            ("app/hook.py::event", "module:card payment provider"), ("app/pay.py::charge", "module:card payment provider"),
            ("app/pay.py::refund", "module:card payment provider")])

    def test_cached_links_are_not_current_when_the_stack_record_changes(self):
        manifest = self.snapshot(self.CODE)
        self.assertEqual(flows.cached_links(manifest, [])["external"], [])
        self.stack(manifest, ("cardpay", "Card Pay", ["app/pay.py"]))
        self.assertEqual([m["id"] for m in flows.cached_links(manifest, [])["external"]], ["cardpay"])
        self.stack(manifest)  # the service is no longer recognised
        self.assertEqual(flows.cached_links(manifest, [])["external"], [])

    # A call the engine resolved into a package the stack step ties to a service: the caller uses the service.
    CALLS = {"app/pay.py": "import cardpay\n\n\ndef charge(amount):\n    cardpay.send(amount)\n"
                           "    return cardpay.send(amount)\n\n\ndef refund(amount):\n    return amount\n\n\n"
                           "cardpay.configure()\n",
             "app/hook.py": "def event(body):\n    return body\n",
             "tests/test_pay.py": "import cardpay\n\n\ndef test_charge():\n    cardpay.send(1)\n"}
    CARDPAY = [("pypi", "cardpay", "cardpay")]
    PACKAGE = ("python", "cardpay")

    def tied(self, files=None, *, paths=("requirements.txt",), libraries=CARDPAY, **stack):
        """A snapshot of `files` (`CALLS`) whose stack record ties the package `cardpay` to the service Card Pay."""
        manifest = self.snapshot(files or {k: self.CALLS[k] for k in ("app/pay.py", "app/hook.py")})
        self.stack(manifest, ("cardpay", "Card Pay", list(paths)), libraries=libraries, **stack)
        return manifest

    def test_a_function_that_calls_the_package_of_a_service_uses_it_and_its_neighbour_does_not(self):
        manifest = self.tied()
        self.engine(manifest, {("app/pay.py", 5): self.PACKAGE, ("app/pay.py", 6): self.PACKAGE})
        links = flows.link_facts(manifest, [])
        # one edge for the caller and the service, however many references, at the first
        self.assertEqual(self.used(links), [("app/pay.py::charge", "module:cardpay", "app/pay.py:5", "dedotto")])
        [edge] = [e for e in links["edges"] if e["type"] == "usa"]
        self.assertEqual(edge["resolver"], "scip-python@0.6.8")  # the engine that resolved the call
        self.assertNotIn("in_tests", links["external"][0])

    def test_a_reference_outside_any_function_is_the_use_of_the_module_of_its_file(self):
        manifest = self.tied()
        self.engine(manifest, {("app/pay.py", 13): self.PACKAGE})
        self.assertEqual([e[:3] for e in self.used(flows.link_facts(manifest, []))],
                         [("app/pay.py::<module>", "module:cardpay", "app/pay.py:13")])

    def test_the_files_a_service_cites_give_no_edge_where_the_engine_ran_for_them(self):
        """A file that names the service, as a configuration does, no longer makes each of its functions use it."""
        manifest = self.tied(paths=("app/pay.py",))
        self.assertEqual([(e[0], e[3]) for e in self.used(flows.link_facts(manifest, []))],
                         [("app/pay.py::charge", "dichiarato"), ("app/pay.py::refund", "dichiarato")])  # no engine
        self.engine(manifest, {("app/pay.py", 5): self.PACKAGE})
        self.assertEqual([(e[0], e[3]) for e in self.used(flows.link_facts(manifest, []))],
                         [("app/pay.py::charge", "dedotto")])

    def test_the_files_a_service_cites_keep_their_edges_where_no_engine_gave_them_a_call(self):
        for engine in ({"language": "typescript"},  # the engine ran for another language
                       {"left_out": ("app/pay.py",)}):  # or has no document of this file
            manifest = self.tied(paths=("app/pay.py",))
            self.engine(manifest, {}, **engine)  # the index holds no call of this file
            self.assertEqual([(e[0], e[3]) for e in self.used(flows.link_facts(manifest, []))],
                             [("app/pay.py::charge", "dichiarato"), ("app/pay.py::refund", "dichiarato")], engine)

    def test_a_service_no_package_ties_keeps_the_edges_of_the_files_it_cites_where_the_engine_ran(self):
        """A service of the module graph, or one the stack step knows by no package: nothing precise replaces them."""
        manifest = self.tied(paths=("app/pay.py",), libraries=())
        self.engine(manifest, {("app/pay.py", 5): self.PACKAGE})
        self.assertEqual([(e[0], e[3]) for e in self.used(flows.link_facts(manifest, []))],
                         [("app/pay.py::charge", "dichiarato"), ("app/pay.py::refund", "dichiarato")])

    def test_a_service_whose_calls_the_engine_could_not_name_a_package_for_keeps_its_declared_edges(self):
        """Kotlin's index names every external with the manager `unknown`: the engine ran and no call ties to a package."""
        manifest = self.tied(paths=("app/pay.py",))
        self.engine(manifest, {("app/pay.py", 5): ("unknown", "kotlin.io")})
        self.assertEqual([(e[0], e[3]) for e in self.used(flows.link_facts(manifest, []))],
                         [("app/pay.py::charge", "dichiarato"), ("app/pay.py::refund", "dichiarato")])

    def test_a_file_loses_the_declared_edges_of_a_service_only_when_it_gave_a_call_into_that_service(self):
        manifest = self.snapshot({k: self.CALLS[k] for k in ("app/pay.py", "app/hook.py")})
        self.stack(manifest, ("cardpay", "Card Pay", ["app/pay.py"]), ("mailer", "Mailer", ["app/pay.py"]),
                   libraries=[*self.CARDPAY, ("pypi", "mailer", "mailer")])
        self.engine(manifest, {("app/pay.py", 5): self.PACKAGE})  # a call into cardpay; none into mailer
        self.assertEqual([(e[0], e[1], e[3]) for e in self.used(flows.link_facts(manifest, []))], [
            ("app/pay.py::charge", "module:cardpay", "dedotto"),
            ("app/pay.py::charge", "module:mailer", "dichiarato"), ("app/pay.py::refund", "module:mailer", "dichiarato")])

    TYPED = {"app/pay.ts": 'import { send } from "cardpay";\n\nexport function charge(amount: number) {\n  send(amount);\n}\n\n'
                           "export function refund(amount: number) {\n  return amount;\n}\n"}

    def test_a_call_into_the_types_package_the_indexer_added_for_a_library_is_a_call_into_the_library(self):
        """The indexer installs `@types/<library>` for a declared library with no types and records it (`types`); the
        calls then end in that package, which the stack step never saw. The one it did not add is another package."""
        for library, types in (("cardpay", "@types/cardpay"), ("@acme/pay", "@types/acme__pay")):
            manifest = self.snapshot(self.TYPED)
            self.stack(manifest, ("cardpay", "Card Pay", ["package.json"]), libraries=[("npm", library, "cardpay")])
            calls = {("app/pay.ts", 4): ("npm", types)}
            self.engine(manifest, calls, language="typescript", types=[f"{types}@1.2.3"])
            self.assertEqual(self.used(flows.link_facts(manifest, [])),
                             [("app/pay.ts::charge", "module:cardpay", "app/pay.ts:4", "dedotto")], library)
            self.engine(manifest, calls, language="typescript")  # the project declares its own types package
            self.assertEqual(self.used(flows.link_facts(manifest, [])), [], library)

    def test_a_package_no_service_owns_and_a_package_of_a_framework_give_no_edge(self):
        manifest = self.tied()
        self.engine(manifest, {("app/pay.py", 5): ("python", "requests"), ("app/pay.py", 6): self.PACKAGE})
        self.assertEqual([e[:2] for e in self.used(flows.link_facts(manifest, []))],
                         [("app/pay.py::charge", "module:cardpay")])  # `requests` belongs to no service
        manifest = self.tied(kind="project")  # a framework of the stack step is no service of others
        self.engine(manifest, {("app/pay.py", 5): self.PACKAGE})
        self.assertEqual(self.used(flows.link_facts(manifest, [])), [])

    def test_the_manager_of_the_engine_names_the_ecosystem_the_stack_step_ties_the_package_in(self):
        manifest = self.tied(libraries=[("npm", "cardpay", "cardpay")])  # tied in npm: a python call is another package
        self.engine(manifest, {("app/pay.py", 5): self.PACKAGE})
        self.assertEqual(self.used(flows.link_facts(manifest, [])), [])
        manifest = self.tied(libraries=[("pypi", "CardPay", "cardpay")])  # PyPI names compare as PEP 503 does
        self.engine(manifest, {("app/pay.py", 5): self.PACKAGE})
        self.assertEqual(len(self.used(flows.link_facts(manifest, []))), 1)

    def test_a_test_file_calling_the_package_is_no_use_of_the_service_and_is_counted(self):
        manifest = self.tied({k: self.CALLS[k] for k in ("app/pay.py", "tests/test_pay.py")})
        self.engine(manifest, {("app/pay.py", 5): self.PACKAGE, ("tests/test_pay.py", 5): self.PACKAGE})
        links = flows.link_facts(manifest, [])
        self.assertEqual([e[:2] for e in self.used(links)], [("app/pay.py::charge", "module:cardpay")])
        self.assertEqual(links["external"], [{"id": "cardpay", "name": "cardpay", "status": "inferred",
                                              "in_tests": {"files": 1, "callers": 1}}])


if __name__ == "__main__":
    unittest.main()
