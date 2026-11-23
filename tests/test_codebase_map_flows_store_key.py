"""The key of a store written as the constant index of the receiver itself: `db[COLLECTION].insert_one(x)` (`flows.link_facts`)."""
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "daodan/core"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import flows  # noqa: E402
from test_codebase_map_flows import write_snapshot  # noqa: E402

COMPUTED = "legge db: receiver index not a literal"
SOURCES = {
    "api/consts.py": 'USAGE = "usage"\n',
    "api/usage.py": (
        "from api import consts\nfrom api.consts import USAGE\n\nCOLLECTION = \"runs\"\n\n\n"
        "def log(db, event):\n    db[COLLECTION].insert_one(event)\n\n\n"
        "def imported(db, event):\n    db[USAGE].insert_one(event)\n\n\n"
        "def literal(db):\n    return db[\"literal\"].find()\n\n\n"
        "def by_name(db, name):\n    return db[name].find()\n\n\n"
        "def by_template(db, x):\n    return db[f\"{x}\"].find()\n\n\n"
        "def by_concatenation(db, x):\n    return db[\"a\" + x].find()\n\n\n"
        "def by_call(db, get):\n    return db[get()].find()\n\n\n"
        "def by_module(db):\n    return db[consts.USAGE].find()\n\n\n"
        "def attribute(db):\n    return db.plain.find()\n\n\n"
        "def handle(db):\n    runs = db[COLLECTION]\n    return runs.find()\n\n\n"
        "def other(cache):\n    return cache[COLLECTION].get()\n\n\n"
        "def parenthesized(db):\n    return (db[COLLECTION]).find()\n\n\n"
        "def of_a_call(make):\n    return make()[COLLECTION].find()\n\n\n"
        "def of_a_call_by_name(make, name):\n    return make()[name].find()\n\n\n"
        "def of_a_result(items):\n    return items()[0].find()\n"),
    "api/store.js": (
        "const NAME = \"events\";\n\nexport function byConstant(db) {\n  return db[NAME].find({});\n}\n"
        "export function byLiteral(db) {\n  return db['literal'].find({});\n}\n"
        "export function byParameter(db, name) {\n  return db[name].find({});\n}\n"
        "export function byTemplate(db, x) {\n  return db[`${x}`].find({});\n}\n"
        "export function ofText(db) {\n  return db[`plain`].find({});\n}\n"
        "export function ofACall(make) {\n  return make()[NAME].find({});\n}\n"),
}
RULES = [
    {"written": "*.find", "in": ["api"], "link": "legge", "store": "db", "key": "holder"},
    {"written": "*.insert_one", "in": ["api"], "link": "scrive", "store": "db", "key": "holder"},
    {"written": "db.*.find", "in": ["api"], "link": "legge", "store": "db", "key": "part1"},
]


def users(links: dict) -> list[str]:
    return sorted(s for store in links["stores"].values() for s in store["reads"] + store["writes"])


class StoreKeyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.work = Path(tempfile.mkdtemp(prefix="flow-store-key-")).resolve()
        cls.links = flows.link_facts(write_snapshot(cls.work, SOURCES), flows.validate_rules(RULES))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.work, True)

    def users(self, key: str, side: str = "reads") -> list[str]:
        return self.links["stores"].get(f"db/{key}", {side: []})[side]

    def gaps(self, file: str) -> dict[str, str]:
        return {g["symbol"]: g["reason"] for g in self.links["gaps"] if g["site"].startswith(file)}

    def test_a_constant_of_the_file_is_the_key(self):
        self.assertEqual(self.users("runs", "writes"), ["api/usage.py::log"])
        self.assertEqual(self.users("runs"), ["api/usage.py::handle", "api/usage.py::of_a_call",
                                              "api/usage.py::parenthesized"])  # the same key, held, wrapped or on a call's result

    def test_a_constant_another_file_declares_is_the_key(self):
        self.assertEqual(self.users("usage", "writes"), ["api/usage.py::imported"])

    def test_a_literal_is_the_key(self):
        self.assertEqual(self.users("literal"), ["api/store.js::byLiteral", "api/usage.py::literal"])
        self.assertEqual(self.users("events"), ["api/store.js::byConstant", "api/store.js::ofACall"])  # a constant, in another grammar
        self.assertIn("api/store.js::ofText", self.users("plain"))  # a template with no hole is a text

    def test_a_computed_index_is_a_gap_with_its_cause_never_a_key(self):
        for file, names in (("api/usage.py", ("by_name", "by_template", "by_concatenation", "by_call")),
                            ("api/store.js", ("byParameter", "byTemplate"))):
            gaps = self.gaps(file)
            for name in names:
                self.assertEqual(gaps[f"{file}::{name}"], COMPUTED, name)
        self.assertFalse([k for k in self.links["stores"] if k in ("db/name", "db/x", "db/a")])

    def test_each_index_that_is_no_constant_has_its_own_cause(self):
        gaps = self.gaps("api/usage.py")
        self.assertIn("dotted name", gaps["api/usage.py::by_module"])  # `module.NAME`: `Facts.literal` reads no dotted name
        self.assertNotIn("api/usage.py::by_module", users(self.links))
        self.assertNotEqual(gaps["api/usage.py::by_module"], gaps["api/usage.py::by_name"])

    def test_a_property_of_the_object_is_the_key_as_before(self):
        self.assertIn("api/usage.py::attribute", self.users("plain"))  # `db.plain.find()`, a rule of `part1`

    def test_a_method_the_rule_does_not_name_is_no_store_call_on_whatever_receiver(self):
        # `cache[KEY].get()`: the rule names the calls of the store (`find`, `insert_one`), and `get` is not one of them
        self.assertEqual([s for s in users(self.links) if s == "api/usage.py::other"], [])

    def test_a_call_as_the_object_indexed_is_read_as_a_name_is(self):
        # `make()[NAME]`: a key when the index is a constant (the runs above), else a gap; never silence
        self.assertEqual(self.gaps("api/usage.py")["api/usage.py::of_a_call_by_name"], COMPUTED)
        self.assertEqual(self.gaps("api/usage.py")["api/usage.py::of_a_result"], COMPUTED)  # `items()[0]`: no text, no key


CLASSES = {"api/repository.py": (
    "from dataclasses import dataclass\n\n\n"
    "class Repo:\n    CLAIMS = \"claims\"\n\n    def __init__(self, db):\n        self._db = db\n\n"
    "    def load(self):\n        return self._db[self.CLAIMS].find()\n\n"
    "    def inherited(self):\n        return self._db[self.REVISIONS].find()\n\n"
    "    def foreign(self, obj):\n        return self._db[obj.CLAIMS].find()\n\n\n"
    "class Other:\n    CLAIMS = \"other\"\n\n    def load(self):\n        return self._db[self.CLAIMS].find()\n\n\n"
    "class Twice:\n    TWICE = \"first\"\n    TWICE = \"second\"\n\n    def load(self):\n        return self._db[self.TWICE].find()\n\n\n"
    "class Own:\n    OWN = \"class\"\n\n    def __init__(self, own):\n        self.OWN = own\n\n"
    "    def load(self):\n        return self._db[self.OWN].find()\n\n\n"
    "class Pair:\n    PAIR = \"pair\"\n\n    def __init__(self, other):\n        self.x, self.PAIR = 1, other\n\n"
    "    def load(self):\n        return self._db[self.PAIR].find()\n\n\n"
    "class Grown:\n    GROWN = \"grown\"\n\n    def __init__(self):\n        self.GROWN += \"_v2\"\n\n"
    "    def load(self):\n        return self._db[self.GROWN].find()\n\n\n"
    "class Cls:\n    KIND = \"kind\"\n\n    @classmethod\n    def load(cls, db, name):\n        cls.KIND = name\n"
    "        return db[cls.KIND].find()\n\n\n"
    "class Patched:\n    PATCHED = \"patched\"\n\n    def load(self):\n        return self._db[self.PATCHED].find()\n\n\n"
    "Patched.PATCHED = \"elsewhere\"\n\n\n"
    "@dataclass\nclass Defaulted:\n    NAME: str = \"defaulted\"\n\n    def load(self):\n        return self._db[self.NAME].find()\n\n\n"
    "class BySetattr:\n    SET = \"set\"\n\n    def __init__(self, name):\n        setattr(self, \"SET\", name)\n\n"
    "    def load(self):\n        return self._db[self.SET].find()\n"),
    "api/view.js": ("class View {\n  static KEY = \"events\";\n  constructor(db) { this.db = db; }\n"
                    "  load() { return this.db[this.KEY].find({}); }\n}\n")}


class ClassAttributeTests(unittest.TestCase):
    """`self.NAME` as an index is the attribute of a class: the engine names its declaration, the view does not carry it
    (edge_grading drops it), so it is a gap with that cause and never a key, whatever else the class does to the name."""

    @classmethod
    def setUpClass(cls):
        cls.work = Path(tempfile.mkdtemp(prefix="flow-store-class-")).resolve()
        cls.links = flows.link_facts(write_snapshot(cls.work, CLASSES), flows.validate_rules(RULES[:1]))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.work, True)

    def test_no_attribute_is_a_key_whatever_the_class_does_to_it(self):
        self.assertEqual(self.links["stores"], {})
        self.assertEqual([e for e in self.links["edges"] if e["type"] in ("scrive", "legge")], [])

    def test_a_gap_with_the_cause_for_each_one(self):
        gaps = {g["symbol"]: g["reason"] for g in self.links["gaps"]}
        for name in ("Repo.load", "Repo.inherited", "Other.load", "Twice.load", "Own.load", "Pair.load", "Grown.load",
                     "Patched.load", "Defaulted.load", "BySetattr.load"):
            self.assertIn("attribute of self", gaps[f"api/repository.py::{name}"], name)
            self.assertIn("edge_grading", gaps[f"api/repository.py::{name}"], name)
        self.assertIn("attribute of this", gaps["api/view.js::View.load"])

    def test_an_attribute_of_another_object_is_a_dotted_name_not_an_attribute_of_self(self):
        gaps = {g["symbol"]: g["reason"] for g in self.links["gaps"]}
        for name in ("Repo.foreign", "Cls.load"):  # `obj.NAME` in a class, `cls.NAME`
            self.assertIn("dotted name", gaps[f"api/repository.py::{name}"], name)


NESTED = {"svc/app/consts.py": 'X = "x"\n',
          "svc/app/a.py": "from app.consts import X\n\n\ndef f(db):\n    return db[X].find()\n"}


class ImportedNameTests(unittest.TestCase):
    def test_an_import_the_snapshot_links_to_no_file_is_a_gap_with_that_cause(self):
        # the sources are under `svc/` and imported as `app.consts`: the snapshot reads that import as outside the project
        work = Path(tempfile.mkdtemp(prefix="flow-store-import-")).resolve()
        self.addCleanup(shutil.rmtree, work, True)
        links = flows.link_facts(write_snapshot(work, NESTED), flows.validate_rules([{**RULES[0], "in": ["svc"]}]))
        self.assertEqual(links["stores"], {})
        self.assertEqual([(g["symbol"], "imported" in g["reason"] and "links it to no declaration" in g["reason"])
                          for g in links["gaps"]], [("svc/app/a.py::f", True)])


class LooseRuleTests(unittest.TestCase):
    """The limit, not a goal: a rule that names a method every object has (`find`) takes it on any indexed receiver."""

    SOURCES = {"api/loose.py": (
        "COLLECTION = \"runs\"\n\n\ndef cached(cache):\n    return cache[COLLECTION].find()\n\n\n"
        "def text(data):\n    return data[\"k\"].find(\"x\")\n\n\n"
        "def first(rows):\n    return rows[0].find(\"x\")\n")}

    def test_the_object_indexed_is_not_told_from_the_store_so_the_rule_is_what_narrows_it(self):
        work = Path(tempfile.mkdtemp(prefix="flow-store-loose-")).resolve()
        self.addCleanup(shutil.rmtree, work, True)
        links = flows.link_facts(write_snapshot(work, self.SOURCES), flows.validate_rules(RULES[:1]))
        self.assertEqual({k: v["reads"] for k, v in links["stores"].items()},
                         {"db/runs": ["api/loose.py::cached"], "db/k": ["api/loose.py::text"]})
        self.assertEqual([(g["symbol"], g["reason"]) for g in links["gaps"]],  # an index that is no text is no key
                         [("api/loose.py::first", COMPUTED)])


if __name__ == "__main__":
    unittest.main()
