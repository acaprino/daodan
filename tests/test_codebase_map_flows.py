"""Flows of the fixture in benchmarks/flow-model: deduced links, traces and units against expected.json."""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "plugins/codebase-map/skills/map/scripts"
BENCH = ROOT / "benchmarks/flow-model"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
import flows  # noqa: E402
import snapshot  # noqa: E402


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

    def test_the_service_asks_for_rules_records_them_and_answers_at_a_level(self):
        import mcp_service
        project = self.work / "service"
        shutil.copytree(BENCH / "app", project / "app")
        subprocess.run(["git", "init", "-q", str(project)], check=True, capture_output=True)
        service = mcp_service.MapService(project)
        service.create_run("app", "flows", engine=False)
        self.assertEqual(service.flows("flows")["status"], "needs_rules")
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

    def test_comments_are_blanked_and_strings_and_divisions_are_kept(self):
        js = "set(() => { // it's\n  return { a: '//x' }; /* b's */ })"
        masked = flows.mask_comments(js, python=False)
        self.assertEqual(len(masked), len(js))
        self.assertNotIn("it's", masked)
        self.assertIn("'//x'", masked)
        self.assertNotIn("b's", masked)
        py = "f(7 // 2,  # it's\n  '#no')"
        self.assertEqual(flows.mask_comments(py, python=True), py.replace("# it's", " " * len("# it's")))

    def test_a_wrapped_selector_reads_every_field_it_names(self):
        call = {"args": [("shallow((s) => ({ n: s.count, r: s.reset }))", 1, 0)], "parts": ["useStore"], "file": "x"}
        self.assertEqual(flows._keys("selector", call, None), ["count", "reset"])
        call["args"] = [("(s) => s.count", 1, 0)]
        self.assertEqual(flows._keys("selector", call, None), ["count"])

    def test_a_held_state_is_read_only_inside_the_function_that_holds_it(self):
        # `title` holds the state and reads `label`; the `count` read a few lines below belongs to `total`.
        self.assertEqual(self.links["stores"]["state/label"]["reads"], ["web/store.ts::title"])
        self.assertNotIn("web/store.ts::title", self.links["stores"]["state/count"]["reads"])
        self.assertIn("web/store.ts::total", self.links["stores"]["state/count"]["reads"])

    def test_a_state_held_whole_gives_the_properties_read_on_its_variable(self):
        self.assertIn(("web/store.ts::report", "web/store.ts::reset"), self.edges("chiama"))

    def test_a_held_store_function_is_called_where_its_variable_is(self):
        self.assertIn(("web/view.tsx::View", "web/store.ts::add"), self.edges("attiva"))
        self.assertNotIn("state/add", self.links["stores"])

    def test_markup_handlers_are_entry_points_and_a_passed_parameter_is_not(self):
        actions = sorted(entry["symbol"] for entry in self.links["entries"] if entry["kind"] == "azione")
        self.assertEqual(actions, ["web/store.ts::add", "web/view.tsx::View.save"])

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


if __name__ == "__main__":
    unittest.main()
