"""score.py of benchmarks/system-map on two minimal maps."""

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SCORE = Path(__file__).resolve().parents[1] / "benchmarks/system-map/score.py"
spec = importlib.util.spec_from_file_location("system_map_score", SCORE)
score = importlib.util.module_from_spec(spec)
spec.loader.exec_module(score)

EXPECTED = {"nodes": [{"name": "Paywall", "type": "schermata", "files": ["app/Paywall.tsx", "app/Plans.tsx"]},
                      {"name": "API acquisti", "type": "servizio o API", "files": ["api/checkout.py", "api/webhook.py"]},
                      {"name": "Stripe", "type": "gateway", "files": ["api/stripe_client.py"]}],
            "flows": [{"name": "Pagamento", "nodes": ["Paywall", "API acquisti", "Stripe"]}]}
PROPOSED = {"nodes": [{"name": "Schermata dei piani", "type": "schermata", "files": ["app/Paywall.tsx"], "evidence": []},
                      {"name": "Pagamenti", "type": "servizio o API", "files": ["api/checkout.py", "api/webhook.py",
                                                                                "api/other.py"], "evidence": []},
                      {"name": "Stripe", "type": "gateway", "files": [], "evidence": ["api/stripe_client.py"]}],
            "flows": [{"name": "Pagare", "nodes": ["Schermata dei piani", "Pagamenti"],
                       "arrows": [{"status": "proved"}, {"status": "declared"}]}],
            "refused_arrows": 1,
            "coverage": {"entries": {"in": 2, "of": 4}, "stores": {"in": 1, "of": 1}, "routes": {"in": 1, "of": 2}}}


class ScoreTests(unittest.TestCase):
    def test_nodes_by_files_flows_by_nodes(self):
        result = score.score_map(PROPOSED, EXPECTED)
        self.assertEqual(result["nodes"], {"found": 3, "of": 3, "missing": []})   # half the files, or more
        self.assertEqual(result["flows"], {"found": 1, "of": 1, "missing": []})   # two thirds of the nodes
        self.assertEqual(result["arrows"], {"proved": 1, "declared": 1, "refused": 1, "refused_share": 0.333})
        self.assertEqual(result["coverage"]["entries"], {"in": 2, "of": 4})

    def test_a_node_with_less_than_half_the_files_is_missing(self):
        thin = {**PROPOSED, "nodes": [{**PROPOSED["nodes"][1], "files": ["api/checkout.py", "api/a.py", "api/b.py"]}]}
        self.assertIn("API acquisti", score.score_map(thin, EXPECTED)["nodes"]["missing"])

    def test_an_entity_is_found_by_its_store_keys(self):
        expected = {"nodes": [{"name": "Abbonamento", "type": "entità", "members": ["store:mongo/subscriptions"]}],
                    "flows": []}
        proposed = {"nodes": [{"name": "Piano", "type": "entità", "members": ["store:mongo/subscriptions"],
                               "files": [], "evidence": []}], "flows": []}
        self.assertEqual(score.score_map(proposed, expected)["nodes"]["found"], 1)

    def test_a_node_without_code_is_found_by_one_cited_file_in_the_same_position(self):
        expected = {"nodes": [{"name": "Stripe", "type": "gateway", "position": "external",
                               "evidence": ["api/stripe_client.py", "api/webhook.py", "requirements.txt"]},
                              {"name": "Landing", "type": "schermata", "position": "unseen", "where": "landing-app"}],
                    "flows": []}
        cited = {"name": "Pagamenti con carta", "type": "servizio o API", "position": "external", "files": [],
                 "evidence": ["requirements.txt#stripe"]}
        unseen = {"name": "Sito", "type": "schermata", "position": "unseen", "files": [], "evidence": []}
        inside = {"name": "Client", "type": "servizio o API", "files": ["api/stripe_client.py"], "evidence": []}
        self.assertEqual(score.score_map({"nodes": [cited, unseen], "flows": []}, expected)["nodes"],
                         {"found": 2, "of": 2, "missing": []})
        self.assertEqual(score.score_map({"nodes": [inside], "flows": []}, expected)["nodes"]["missing"],
                         ["Stripe", "Landing"])

    def test_two_runs_agree_on_the_nodes_they_share_by_files(self):
        first = {"nodes": PROPOSED["nodes"], "flows": []}
        second = {"nodes": [PROPOSED["nodes"][1], {**PROPOSED["nodes"][0], "files": ["app/Other.tsx"]}], "flows": []}
        # Pagamenti matches; Stripe (no code) has no counterpart; the screen changed its files.
        self.assertEqual(score.stability(first, second), {"same": 1, "of": 3, "share": 0.333})

    def test_externals_recall_and_wrong(self):
        result = score.score_externals({"externals": [{"id": "stripe"}, {"id": "react"}, {"id": "redis"}]},
                                       {"externals": ["stripe", "react", "fastapi"]})
        self.assertEqual(result, {"recall": 0.667, "found": ["react", "stripe"], "missed": ["fastapi"], "wrong": ["redis"]})

    def test_externals_by_source_and_used_but_not_named(self):
        brief = {"externals": [{"id": "stripe", "from": ["registry"]}, {"id": "react", "from": ["stack-analyser"]},
                               {"id": "eslint", "from": ["registry", "stack-analyser"]},
                               {"id": "billing", "from": ["modules"]}]}
        expected = {"externals": ["stripe", "react"], "also": ["eslint"]}
        self.assertEqual(score.score_externals(brief, expected, "registry"),
                         {"recall": 0.5, "found": ["stripe"], "missed": ["react"], "wrong": []})
        self.assertEqual(score.score_externals(brief, expected, "stack-analyser")["found"], ["react"])
        self.assertEqual(score.score_externals(brief, expected, "both"),
                         {"recall": 1.0, "found": ["react", "stripe"], "missed": [], "wrong": []})
        self.assertEqual(score.score_externals(brief, expected)["wrong"], ["billing"])


# A whole-system reference made up here: depth 0 to 3, folders, children of their parent's type, store keys,
# symbols of one file in two nodes, a generated file, an actor and an external with its registry id.
FILES = ["README.md", ".github/workflows/ci.yml", "docs/guide.md", "scripts/deploy.sh",
         "web/app.tsx", "web/lib/api.ts", "web/pages/login.tsx", "web/pages/cart.tsx", "web/pages/cart_item.tsx",
         "web/components/button.tsx", "web/components/modal.tsx", "web/hooks/use_cart.ts",
         "api/main.py", "api/models.py", "api/routes/auth.py", "api/routes/orders.py", "api/routes/orders_admin.py",
         "api/tests/test_orders.py", "api/migrations/001_init.sql", "jobs/nightly.py", "jobs/cleanup.py"]


def _node(name, kind, inside=None, members=(), **more):
    return {"name": name, "type": kind, **({"inside": inside} if inside else {}),
            **({"members": list(members)} if members else {}), **more}


def _flow(name, kinds, nodes, entries, effects):
    return {"name": name, "types": kinds, "nodes": nodes, "entries": [{"node": n} for n in entries],
            "effects": [{"node": n} for n in effects]}


REFERENCE = {
    "nodes": [_node("Shop", "altro", None, ["web", "api", "jobs"]),
              _node("Web app", "applicazione", "Shop", ["web"]),
              _node("Login", "schermata", "Web app", ["web/pages/login.tsx"]),
              _node("Cart", "schermata", "Web app", ["web/pages/cart.tsx", "web/lib/api.ts", "web/hooks/use_cart.ts"]),
              _node("Cart item", "schermata", "Cart", ["web/pages/cart_item.tsx"]),
              _node("API", "servizio o API", "Shop", ["api/main.py::app", "api/routes"]),
              _node("Auth routes", "servizio o API", "API", ["api/routes/auth.py"]),
              _node("Order routes", "servizio o API", "API", ["api/routes/orders.py", "api/routes/orders_admin.py"]),
              _node("Database", "database", "Shop", ["store:pg/orders", "store:pg/users"]),
              _node("Order", "entità", "Database", ["store:pg/orders", "api/models.py::Order"]),
              _node("User", "entità", "Database", ["store:pg/users", "api/models.py::User"]),
              _node("Cache", "database", "Shop", ["store:redis/users"]),
              _node("Nightly job", "lavoro a orario", "Shop",
                    ["jobs", "jobs/generated/a.py", "jobs/generated/b.py", "jobs/generated/c.py"]),
              _node("Customer", "attore", position="external"),
              _node("Stripe", "gateway", position="external", registry="stripe", family="provider",
                    role="charges the cards", mode="SDK")],
    "flows": [_flow("Sign in", ["funzionale"], ["Customer", "Login", "Auth routes", "User"], ["Customer"], ["User"]),
              _flow("Checkout", ["funzionale"], ["Customer", "Cart", "Cart item", "Order routes", "Stripe", "Order"],
                    ["Cart"], ["Order", "Stripe"]),
              _flow("Nightly cleanup", ["operativo"], ["Nightly job", "Order", "Cache"], ["Nightly job"], ["Cache"])]}


def as_proposal(reference: dict) -> dict:
    """A reference as a proposed map: what a map carries, every arrow proved."""
    fields = ("name", "type", "position", "inside", "members", "registry", "family", "role", "mode")
    return {"nodes": [{k: n[k] for k in fields if k in n} for n in reference["nodes"]],
            "flows": [{"name": f["name"], "types": f["types"], "nodes": f["nodes"],
                       "arrows": [{"from": a, "to": b, "status": "proved"} for a, b in zip(f["nodes"], f["nodes"][1:])]}
                      for f in reference["flows"]]}


def _depth(node: dict, by: dict) -> int:
    depth = 0
    while node.get("inside") in by and depth < 20:
        node, depth = by[node["inside"]], depth + 1
    return depth


def fuse_level_2(proposal: dict) -> dict:
    """Every node of depth 2 merged into its parent: its members, its children and its place in the flows."""
    by = {n["name"]: n for n in proposal["nodes"]}
    fused = {n["name"]: n["inside"] for n in proposal["nodes"] if _depth(n, by) == 2}
    nodes = []
    for node in proposal["nodes"]:
        if node["name"] in fused:
            continue
        taken = [m for c in proposal["nodes"] if fused.get(c["name"]) == node["name"] for m in c.get("members", [])]
        node = {**node, **({"members": list(dict.fromkeys(node.get("members", []) + taken))} if taken else {})}
        if node.get("inside") in fused:
            node["inside"] = fused[node["inside"]]
        nodes.append(node)
    flows = []
    for flow in proposal["flows"]:
        names = list(dict.fromkeys(fused.get(n, n) for n in flow["nodes"]))
        arrows = [{**a, "from": fused.get(a["from"], a["from"]), "to": fused.get(a["to"], a["to"])}
                  for a in flow["arrows"]]
        flows.append({**flow, "nodes": names, "arrows": [a for a in arrows if a["from"] != a["to"]]})
    return {**proposal, "nodes": nodes, "flows": flows}


def rename(proposal: dict) -> dict:
    new = {n["name"]: f"node {i}" for i, n in enumerate(proposal["nodes"])}
    nodes = [{**n, "name": new[n["name"]], **({"inside": new[n["inside"]]} if n.get("inside") in new else {})}
             for n in proposal["nodes"]]
    flows = [{**f, "name": f"flow {i}", "nodes": [new[n] for n in f["nodes"]],
              "arrows": [{**a, "from": new[a["from"]], "to": new[a["to"]]} for a in f["arrows"]]}
             for i, f in enumerate(proposal["flows"])]
    return {**proposal, "nodes": nodes, "flows": flows}


def swap_types(proposal: dict) -> dict:
    kinds = sorted({n["type"] for n in proposal["nodes"]})
    return {**proposal, "nodes": [{**n, "type": kinds[(kinds.index(n["type"]) + 1) % len(kinds)]}
                                  for n in proposal["nodes"]]}


def folder_mirror(files: list[str]) -> dict:
    """One node per folder of the snapshot, inside the folder that holds it: the tree, not the system."""
    folders = sorted({"/".join(f.split("/")[:k]) for f in files for k in range(f.count("/") + 1)})
    return {"nodes": [{"name": d or ".", "type": "altro", "members": [d or "."],
                       **({"inside": d.rpartition("/")[0] or "."} if d else {})} for d in folders], "flows": []}


class SystemScoreTests(unittest.TestCase):
    def setUp(self):
        self.full = score.score_system(as_proposal(REFERENCE), REFERENCE, FILES)

    def test_the_reference_against_itself_finds_everything(self):
        result = self.full
        self.assertEqual(result["nodes"]["by_depth"], {"0-1": {"found": 7, "of": 7}, "2": {"found": 6, "of": 6},
                                                       "3+": {"found": 1, "of": 1}})
        self.assertEqual((result["nodes"]["found"], result["nodes"]["of"], result["nodes"]["missing"]), (14, 14, []))
        self.assertEqual(result["nodes"]["by_type"]["schermata"], {"found": 3, "of": 3})
        self.assertEqual(result["apart"], {"found": 1, "of": 1})   # the actor: no files, no registry id
        self.assertEqual(result["precision"], {"found": 15, "of": 15, "share": 1.0})
        self.assertEqual(result["single_folder"], 0.133)            # Web app and Nightly job are one folder each
        self.assertEqual(result["type"], {"same": 15, "of": 15, "share": 1.0})
        self.assertEqual(result["inside"], {"kept": 12, "of_found": 12, "of": 12, "share": 1.0})
        self.assertEqual(result["flows"], {"found": 3, "of": 3, "missing": [],
                                           "by_type": {"funzionale": {"found": 2, "of": 2},
                                                       "operativo": {"found": 1, "of": 1}}})
        self.assertEqual(result["flows_depth_1"], {"share": 1.0, "of": 3})
        self.assertEqual((result["entries"], result["effects"]), ({"found": 3, "of": 3}, {"found": 4, "of": 4}))
        self.assertEqual(result["arrows"], {"proved": 10, "declared": 0, "refused": 0, "refused_share": 0.0})
        self.assertEqual(result["reach"], {"found": 7, "of": 7})
        self.assertEqual(result["services"], {"of": 1, "family": 1, "role": 1, "mode": 1})

    def test_a_node_that_names_one_file_of_a_part_reaches_the_part_without_finding_it(self):
        pointer = {"nodes": [{"name": "Shop site", "type": "schermata", "members": ["web/pages/cart.tsx"]},
                             {"name": "Backend", "type": "servizio o API", "members": ["api/main.py"]},
                             {"name": "Buyer", "type": "attore", "position": "external"},
                             {"name": "Stripe", "type": "gateway", "position": "external"},   # no registry id
                             {"name": "Spread", "type": "altro", "members": ["jobs/nightly.py", "api/models.py"]}],
                   "flows": []}
        result = score.score_system(pointer, REFERENCE, FILES)
        self.assertEqual((result["nodes"]["found"], result["precision"]["found"]), (0, 1))
        # Shop, Web app, API, and Stripe by its name; half of a node's files in a part do not reach it
        self.assertEqual(result["reach"], {"found": 4, "of": 7})

    def test_names_never_count(self):
        self.assertEqual(score.score_system(rename(as_proposal(REFERENCE)), REFERENCE, FILES), self.full)

    def test_fusing_level_2_into_the_parents_loses_level_2_and_the_fine_flows(self):
        result = score.score_system(fuse_level_2(as_proposal(REFERENCE)), REFERENCE, FILES)
        self.assertEqual(result["nodes"]["by_depth"], {"0-1": {"found": 7, "of": 7}, "2": {"found": 0, "of": 6},
                                                       "3+": {"found": 1, "of": 1}})
        self.assertEqual(result["nodes"]["found"], 8)
        self.assertEqual(result["precision"]["share"], 1.0)
        self.assertEqual(result["inside"], {"kept": 5, "of_found": 5, "of": 12, "share": 1.0})
        self.assertEqual((result["flows"]["found"], result["flows_depth_1"]["share"]), (1, 1.0))
        self.assertEqual((result["entries"], result["effects"]), ({"found": 1, "of": 3}, {"found": 1, "of": 4}))

    def test_swapping_the_types_loses_the_type_and_what_has_no_files(self):
        result = score.score_system(swap_types(as_proposal(REFERENCE)), REFERENCE, FILES)
        self.assertEqual(result["type"], {"same": 0, "of": 14, "share": 0.0})
        self.assertEqual((result["nodes"]["found"], result["apart"]["found"]), (14, 0))
        self.assertEqual(result["precision"]["share"], 0.933)
        self.assertEqual((result["flows"]["found"], result["entries"]["found"]), (2, 2))

    def test_a_folder_mirror_has_low_precision(self):
        result = score.score_system(folder_mirror(FILES), REFERENCE, FILES)
        self.assertEqual(result["precision"], {"found": 4, "of": 15, "share": 0.267})
        self.assertEqual(result["single_folder"], 1.0)
        self.assertEqual((result["nodes"]["found"], result["flows"]["found"]), (4, 0))

    def test_a_generated_file_out_of_the_snapshot_does_not_count(self):
        jobs = {"nodes": [{"name": "Jobs", "type": "altro", "members": ["jobs"]}], "flows": []}
        self.assertNotIn("Nightly job", score.score_system(jobs, REFERENCE, FILES)["nodes"]["missing"])

    def test_a_loaded_node_counts_its_files_and_keeps_the_symbols_the_reference_splits(self):
        loaded = {"nodes": [{"name": "Backend", "type": "servizio o API", "members": ["api/routes"],
                             "files": ["api/main.py", "api/routes/auth.py", "api/routes/orders.py",
                                       "api/routes/orders_admin.py"]},
                            {"name": "Orders", "type": "entità", "members": ["store:db/orders", "api/models.py::Order"],
                             "files": ["api/models.py"]},   # "orders" is one store key only: the store's name drops
                            {"name": "Users", "type": "entità", "members": ["store:db/users", "api/models.py::User"],
                             "files": ["api/models.py"]}],  # "users" is in two stores: it keeps the name
                  "flows": []}
        missing = score.score_system(loaded, REFERENCE, FILES)["nodes"]["missing"]
        self.assertIn("User", missing)
        self.assertFalse({"API", "Order"} & set(missing))

    def test_an_external_with_a_registry_id_never_stands_for_an_actor(self):
        stripe = {"nodes": [{"name": "Pay", "type": "attore", "position": "external", "registry": "stripe"}],
                  "flows": []}
        result = score.score_system(stripe, REFERENCE, FILES)
        self.assertEqual((result["apart"]["found"], result["nodes"]["found"]), (0, 1))

    def test_one_flow_holding_every_node_finds_no_flow(self):
        proposal = as_proposal(REFERENCE)
        everything = {"name": "All", "types": ["funzionale"], "nodes": [n["name"] for n in proposal["nodes"]],
                      "arrows": []}
        self.assertEqual(score.score_system({**proposal, "flows": [everything]}, REFERENCE, FILES)["flows"]["found"], 0)

    def test_node_overlap_does_not_credit_missing_reversed_refused_or_stale_arrows(self):
        for defect in ("missing", "reversed", "refused", "stale"):
            with self.subTest(defect=defect):
                proposal = as_proposal(REFERENCE)
                for flow in proposal["flows"]:
                    if defect == "missing":
                        flow["arrows"] = []
                    elif defect == "reversed":
                        flow["arrows"] = [{**a, "from": a["to"], "to": a["from"]} for a in flow["arrows"]]
                    else:
                        for arrow in flow["arrows"]:
                            arrow.update({"status": "refused"} if defect == "refused" else {"fresh": False})
                result = score.score_system(proposal, REFERENCE, FILES)
                self.assertEqual(result["flows_by_nodes"], {"found": 3, "of": 3})
                self.assertEqual([result[k]["found"] for k in ("flows", "entries", "effects")], [0, 0, 0])

    def test_only_reached_effects_and_correct_flow_types_get_credit(self):
        proposal = as_proposal(REFERENCE)
        checkout = proposal["flows"][1]
        checkout["arrows"].pop()  # Cart still reaches Stripe, but Order is isolated.
        checkout["types"] = ["operativo"]
        result = score.score_system(proposal, REFERENCE, FILES)
        self.assertEqual((result["flows"]["found"], result["entries"]["found"], result["effects"]["found"]), (3, 3, 3))
        self.assertEqual(result["flows"]["by_type"]["funzionale"], {"found": 1, "of": 2})
        self.assertEqual(result["flow_type_precision"], {"found": 2, "of": 3, "share": 0.667})

    def test_a_found_service_counts_the_same_family_and_whether_role_and_mode_are_there(self):
        expected = {"nodes": [_node("Stripe", "gateway", position="external", registry="stripe", family="provider",
                                    role="charges the cards", mode="SDK"),
                              _node("Sendgrid", "servizio o API", position="external", registry="sendgrid",
                                    family="provider", role="sends the mails", mode="HTTP API")], "flows": []}
        proposed = {"nodes": [_node("Pay", "gateway", position="external", registry="stripe", family="provider",
                                    role="payments", mode="library"),
                              _node("Mail", "servizio o API", position="external", registry="sendgrid",
                                    family="piattaforma di integrazione", role="mail")], "flows": []}
        result = score.score_system(proposed, expected, FILES)
        self.assertEqual(result["nodes"]["found"], 2)
        self.assertEqual(result["services"], {"of": 2, "family": 1, "role": 2, "mode": 1})


class WholeTableTests(unittest.TestCase):
    """`score.py whole` on synthetic outputs of a whole job: no run, no model."""

    @staticmethod
    def _write(path: Path, value) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value if isinstance(value, str) else json.dumps(value), encoding="utf-8")

    def _run(self, tag: Path, label: str, case: str, rep: int, **summary) -> Path:
        run = tag / label
        self._write(run / "summary.json", {"case": case, "model": "haiku", "scope": "system", "rules": "session",
                                           "rep": rep, **summary})
        return run

    def test_a_measured_case_gives_its_columns_and_says_what_it_did_not_measure(self):
        with tempfile.TemporaryDirectory() as folder:
            tag, expected = Path(folder) / "tag", Path(folder) / "expected"
            # the reference lists the kind of each entry, as `entries.py measure` reads it
            reference = {**REFERENCE, "flows": [{**flow, "entries": [{**item, "kind": "controllo dell'interfaccia"}
                                                                      for item in flow["entries"]]}
                                                for flow in REFERENCE["flows"]]}
            self._write(expected / "shop-system.json", reference)
            for rep in (1, 2):
                run = self._run(tag, f"shop-{rep}", "shop", rep, cost_usd=0.5 * rep, budget_stop=False,
                                prepared_seconds=90, engine={"exit": 0, "timed_out": False,
                                                             "languages": {"javascript": "fresh"}})
                self._write(run / "map.json", as_proposal(REFERENCE))
                self._write(run / "files.txt", "\n".join(FILES))
            self._write(tag / "cases/shop/archive.json",
                        {"/repo": {"kept": 21, "left": 0, "bytes": 1, "masked": {"web/lib/api.ts": 2}, "withheld": []}})
            self._write(tag / "cases/shop/candidates.json",
                        {"case": "shop", "candidates": [{"reader": "attribute", "symbol": "web/pages/cart.tsx::onClick"}],
                         "calls": []})
            self._write(tag / "cases/shop/files.txt", "\n".join(FILES))
            row = score.whole(tag, expected)["shop"]["haiku system session"]
        self.assertEqual(row["runs"], 2)
        self.assertEqual(row["input"], {"state": "misurato", "value": "nothing left out"})
        self.assertEqual(row["secrets"]["value"]["masked_in_the_archive"], 2)
        self.assertEqual(row["secrets"]["value"]["in_the_texts_sent_out"]["state"], "non misurato")
        self.assertEqual(row["engine"], {"state": "misurato", "value": {"javascript": "fresh"}})
        self.assertEqual(row["entries"]["state"], "misurato")
        self.assertEqual(row["entries"]["value"]["readers"][0]["by_kind"]["controllo dell'interfaccia"],
                         {"found": 1, "of": 2})   # the Cart screen holds the candidate's file, the nightly job does not
        self.assertEqual((row["system"]["state"], row["system"]["value"]["nodes"]["found"]), ("misurato", 14))
        self.assertEqual((row["stable"]["state"], row["stable"]["value"]["of"]), ("misurato", 15))
        self.assertEqual(row["cost"]["value"]["cost_usd"], 1.5)
        for column, name in (("paths", "paths.json"), ("search", "search.json")):
            self.assertEqual(row[column]["state"], "non misurato", column)
            self.assertIn(name, row[column]["cause"])
        self.assertEqual(row["handlers"]["state"], "non misurato")

    def test_a_failed_run_is_not_a_zero_and_an_archive_that_left_files_out_is_said(self):
        with tempfile.TemporaryDirectory() as folder:
            tag, expected = Path(folder) / "tag", Path(folder) / "expected"
            self._run(tag, "lost-1", "lost", 1, stopped="the rules session recorded no rules",
                      engine={"exit": None, "timed_out": True})
            self._write(tag / "cases/lost/archive.json",
                        {"/repo": {"kept": 5, "left": 2, "bytes": 1, "masked": {}, "withheld": ["a.bin"]}})
            self._run(tag, "bare-1", "bare", 1, cost_usd=None, engine=None)
            row = score.whole(tag, expected)["lost"]["haiku system session"]
            bare = score.whole(tag, expected)["bare"]["haiku system session"]
        self.assertEqual(row["input"], {"state": "ingresso omesso", "left": 2, "withheld": 1})
        self.assertEqual(row["entries"]["state"], "non misurato")
        self.assertIn("candidates.json", row["entries"]["cause"])
        self.assertEqual(row["engine"], {"state": "passo fallito", "cause": "the engine pass timed out"})
        self.assertEqual(row["system"], {"state": "non misurato", "cause": "the rules session recorded no rules"})
        self.assertEqual(row["stable"]["state"], "non misurato")
        self.assertEqual(row["cost"]["state"], "non misurato")
        self.assertEqual(bare["engine"]["state"], "non misurato")
        self.assertEqual(bare["input"]["state"], "non misurato")

    def test_a_map_with_no_node_found_is_zero_found_and_a_missing_reference_is_not_measured(self):
        with tempfile.TemporaryDirectory() as folder:
            tag, expected = Path(folder) / "tag", Path(folder) / "expected"
            self._write(expected / "shop-system.json", REFERENCE)
            run = self._run(tag, "shop-1", "shop", 1, cost_usd=0.1, engine={"exit": 0, "timed_out": False})
            self._write(run / "map.json", {"nodes": [{"name": "Ghost", "type": "altro", "members": ["nowhere/ghost.py"]}],
                                           "flows": []})
            self._write(run / "files.txt", "\n".join(FILES))
            other = self._run(tag, "free-1", "free", 1, cost_usd=0.1, engine={"exit": 0, "timed_out": False})
            self._write(other / "map.json", as_proposal(REFERENCE))
            self._write(other / "files.txt", "\n".join(FILES))
            table = score.whole(tag, expected)
        self.assertEqual(table["shop"]["haiku system session"]["system"]["state"], "zero trovati")
        self.assertEqual(table["free"]["haiku system session"]["system"],
                         {"state": "non misurato", "cause": "free-system.json is not there"})

    def test_a_job_with_no_model_has_a_row_for_each_case_it_ran(self):
        with tempfile.TemporaryDirectory() as folder:
            tag, expected = Path(folder) / "tag", Path(folder) / "expected"
            self._write(tag / "cases/only/archive.json",
                        {"/repo": {"kept": 5, "left": 0, "bytes": 1, "masked": {"a.py": 3}, "withheld": []}})
            self._write(tag / "cases/only/engine.json", {"exit": 2, "timed_out": False, "stderr": "boom"})
            table = score.whole(tag, expected)
        row = table["only"]["no model"]
        self.assertEqual(row["runs"], 0)
        self.assertEqual(row["input"], {"state": "misurato", "value": "nothing left out"})
        self.assertEqual(row["secrets"]["value"]["masked_in_the_archive"], 3)
        self.assertEqual(row["engine"], {"state": "passo fallito", "cause": "the engine pass exited with 2: boom"})
        self.assertEqual(row["entries"]["state"], "non misurato")
        self.assertNotIn("system", row)

    def test_a_run_given_the_rules_of_another_is_not_a_second_independent_run(self):
        with tempfile.TemporaryDirectory() as folder:
            tag, expected = Path(folder) / "tag", Path(folder) / "expected"
            for rep, origin in ((1, None), (2, "shop-1")):
                run = self._run(tag, f"shop-{rep}", "shop", rep, rules_from=origin,
                                engine={"exit": 1, "timed_out": False, "stderr": "Traceback: boom"})
                self._write(run / "map.json", as_proposal(REFERENCE))
            row = score.whole(tag, expected)["shop"]["haiku system session"]
        self.assertEqual(row["stable"]["state"], "non misurato")
        self.assertIn("given the first one's rules", row["stable"]["cause"])
        # exit 1 with no report is a crash, not a measured engine
        self.assertEqual(row["engine"], {"state": "passo fallito",
                                         "cause": "the engine pass wrote no report: Traceback: boom"})


class RunsTableTests(unittest.TestCase):
    """`score.py runs` on synthetic outputs of three runs of one project."""

    @staticmethod
    def _run(folder: Path, name: str, seconds: int, restores: int, found: int | None) -> Path:
        run = folder / name
        run.mkdir(parents=True)
        events = [("step.started", "scan", None), ("analyzer.started", "analyze", "scip-typescript"),
                  ("analyzer.started", "dynamic", "app"), ("step.finished", "union", None)]
        stamps = ["2026-11-23T10:00:00.000000Z", "2026-11-23T10:00:01.000000Z", "2026-11-23T10:00:02.000000Z",
                  f"2026-11-23T10:{seconds // 60:02d}:{seconds % 60:02d}.000000Z"]
        (run / "pipeline-events.jsonl").write_text(
            "\n".join(json.dumps({"at": at, "step": step, "analyzer": analyzer, "kind": kind, "data": {}})
                      for at, (kind, step, analyzer) in zip(stamps, events)), encoding="utf-8")
        (run / "dynamic-runs").mkdir()
        (run / "dynamic-runs" / "container-runs.jsonl").write_text(
            "\n".join(json.dumps({"phase": phase}) for phase in ["node-restore"] * restores + ["execute"]),
            encoding="utf-8")
        if found is not None:
            (run / "links.json").write_text(json.dumps({"found": found, "of": 10}), encoding="utf-8")
        return run

    def test_three_runs_side_by_side_and_a_cheaper_run_that_finds_less_is_marked(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            first = self._run(base, "from-scratch", 600, 3, 8)
            second = self._run(base, "unchanged", 60, 0, 8)
            third = self._run(base, "one-module", 120, 1, 5)
            table = score.runs([first, second, third])["runs"]
        self.assertEqual([row["run"] for row in table], ["from-scratch", "unchanged", "one-module"])
        self.assertEqual(table[0]["seconds"], {"state": "misurato", "value": 600.0})
        self.assertEqual(table[0]["restores"]["value"], 3)
        self.assertEqual(table[1]["restores"], {"state": "misurato", "value": 0})
        self.assertEqual((table[0]["analyzer_starts"]["value"], table[0]["app_starts"]["value"]), (1, 1))
        self.assertEqual(table[0]["links"]["value"], {"found": 8, "of": 10})
        self.assertNotIn("flag", table[1])   # cheaper and as many links: a gain
        self.assertEqual(table[2]["flag"], "costs less and finds fewer links: not a gain")
        for column in ("cpu", "peak_memory", "temporary_space"):
            self.assertEqual(table[0][column]["state"], "non misurato", column)

    def test_a_run_without_its_files_says_what_is_missing(self):
        with tempfile.TemporaryDirectory() as folder:
            empty = Path(folder) / "empty"
            empty.mkdir()
            row = score.runs([empty])["runs"][0]
        self.assertEqual(row["seconds"]["state"], "non misurato")
        self.assertEqual(row["restores"]["state"], "non misurato")
        self.assertEqual((row["analyzer_starts"]["state"], row["app_starts"]["state"]), ("non misurato",) * 2)
        self.assertIn("links.json", row["links"]["cause"])


if __name__ == "__main__":
    unittest.main()
