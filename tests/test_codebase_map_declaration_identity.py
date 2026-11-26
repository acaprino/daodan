"""The declaration the engine names for a read of a project value reaches the view and the links (plan, task 18b).

scip-python resolves `self.CLAIMS` to the class's `CLAIMS` and `consts.TABLE` to the module's `TABLE` (the review
of 23 November 2026 on phazly): the definition of each symbol is where the snapshot declares a binding. The view's
read then names that binding (`binding_id`), which `flows.Facts.constants` reads, so the constant is a store key
with no reader written by hand; an inherited attribute no subclass defines again keeps it.

A value that can be another at run time names no binding, and the read stays a gap. The engine shows a write as an
occurrence that is neither the symbol's one definition nor inside a read, a call or an import the snapshot records,
whatever role it gives it: a second assignment in the class, `self.OWN = own`, a tuple target, `+=`,
`Patched.PATCHED = ...` at module level, `consts.MOVED = ...` from another file. The writes it has no occurrence for
are refused on the snapshot's own facts, as `resolution.instance_method` refuses a receiver's member: a decorated
class (`@dataclass`), `setattr`, a member a subclass defines again. A binding reached through a hop, a file of the
language the index has no document for, a module scope the reader cannot close (`import *`), and a language whose
reader records an assignment's target as a read (Go here) give none.

The documents are written as scip-python and scip-go write them, the way the other adapters' tests write theirs;
scip-python 0.6.8 gives a redefinition the read role (8: `def convert` at
tests/fixtures/code-graph/python/fx/over.py:15), and the test tries each role.
"""
from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
import unittest.mock
from pathlib import Path

TESTS = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTS.parent / "daodan/core"))
sys.path.insert(0, str(TESTS))
import code_graph  # noqa: E402
import edge_view  # noqa: E402
import engine_pass  # noqa: E402
import flows  # noqa: E402
import resolve_edges  # noqa: E402
import test_codebase_map_code_graph as graph_tests  # noqa: E402
from indexers import python as python_indexer  # noqa: E402
from test_codebase_map_flows import read_project  # noqa: E402

MORE = '''from dataclasses import dataclass
from api import consts


class Pair:
    PAIR = "pair"

    def __init__(self, other):
        self.x, self.PAIR = 1, other

    def load(self, db):
        return db[self.PAIR].find()


class Grown:
    GROWN = "grown"

    def __init__(self):
        self.GROWN += "_v2"

    def load(self, db):
        return db[self.GROWN].find()


class Patched:
    PATCHED = "patched"

    def load(self, db):
        return db[self.PATCHED].find()


Patched.PATCHED = "elsewhere"


@dataclass
class Defaulted:
    NAME: str = "defaulted"

    def load(self, db):
        return db[self.NAME].find()


class BySetattr:
    SET = "set"

    def __init__(self, name):
        setattr(self, "SET", name)

    def load(self, db):
        return db[self.SET].find()


class Base:
    BASE = "base"

    def load(self, db):
        return db[self.BASE].find()


class Sub(Base):
    BASE = "sub"


class Holder:
    def __init__(self):
        self.table = consts.TABLE

    def use(self, other):
        self.table = other

    def load(self, db):
        return db[self.table].find()


def label():
    return consts.TABLE.upper()


class Kept:
    KEPT = "kept"

    def load(self, db):
        return db[self.KEPT].find()


class Front:
    KEPT = "front"


class Mixed(Front, Kept):
    pass


class Counted:
    COUNT = "count"

    @classmethod
    def reset(cls, name):
        cls.COUNT = name

    def load(self, db):
        return db[self.COUNT].find()
'''
SOURCES = {
    "api/repo.py": (
        'class Repo:\n    CLAIMS = "claims"\n\n    def load(self, db):\n        return db[self.CLAIMS].find()\n\n\n'
        'class Twice:\n    TWICE = "first"\n    TWICE = "second"\n\n    def load(self, db):\n'
        '        return db[self.TWICE].find()\n\n\n'
        'class Own:\n    OWN = "class"\n\n    def __init__(self, own):\n        self.OWN = own\n\n'
        '    def load(self, db):\n        return db[self.OWN].find()\n\n\n'
        'class Child(Repo):\n    def child(self, db):\n        return db[self.CLAIMS].find()\n'),
    "api/consts.py": 'TABLE = "orders"\nMOVED = "before"\n',
    "api/use.py": ('from api import consts\n\n\ndef read(db):\n    return db[consts.TABLE].find()\n\n\n'
                   'def moved(db):\n    return db[consts.MOVED].find()\n'),
    "api/patch.py": 'from api import consts\n\nconsts.MOVED = "after"\n',
    "api/named.py": 'from api.consts import TABLE\n\n\ndef named(db):\n    return db[TABLE].find()\n',
    "api/more.py": MORE,
    "api/star.py": 'STAR = "star"\nfrom api.consts import *\n',
    "api/stars.py": 'from api import star\n\n\ndef starred(db):\n    return db[star.STAR].find()\n',
}
P = "scip-python python python _ "
DEFINITION, READ = 1, 8
WRITTEN = "written"  # an occurrence of a symbol written again, given each role in turn
# (line, or a text only that line holds; word; n-th on its line; symbol; role), as scip-python writes them: a
# definition where a name is bound, a read access where it is read, the symbol of a member at the member's name.
OCCURRENCES = {
    "api/repo.py": [
        (1, "Repo", 1, "`api.repo`/Repo#", DEFINITION), (2, "CLAIMS", 1, "`api.repo`/Repo#CLAIMS.", DEFINITION),
        (4, "load", 1, "`api.repo`/Repo#load().", DEFINITION), (5, "CLAIMS", 1, "`api.repo`/Repo#CLAIMS.", READ),
        # the parameters, as scip-python names them: a parameter differs from call to call
        (4, "self", 1, "`api.repo`/Repo#load().(self)", DEFINITION), (4, "db", 1, "`api.repo`/Repo#load().(db)", DEFINITION),
        (5, "db", 1, "`api.repo`/Repo#load().(db)", READ), (5, "self", 1, "`api.repo`/Repo#load().(self)", READ),
        (8, "Twice", 1, "`api.repo`/Twice#", DEFINITION), (9, "TWICE", 1, "`api.repo`/Twice#TWICE.", DEFINITION),
        (10, "TWICE", 1, "`api.repo`/Twice#TWICE.", WRITTEN),
        (12, "load", 1, "`api.repo`/Twice#load().", DEFINITION), (13, "TWICE", 1, "`api.repo`/Twice#TWICE.", READ),
        (16, "Own", 1, "`api.repo`/Own#", DEFINITION), (17, "OWN", 1, "`api.repo`/Own#OWN.", DEFINITION),
        (19, "__init__", 1, "`api.repo`/Own#__init__().", DEFINITION), (20, "OWN", 1, "`api.repo`/Own#OWN.", WRITTEN),
        (22, "load", 1, "`api.repo`/Own#load().", DEFINITION), (23, "OWN", 1, "`api.repo`/Own#OWN.", READ),
        # the inherited attribute: scip-python names the parent's symbol at the child's read
        (26, "Child", 1, "`api.repo`/Child#", DEFINITION), (26, "Repo", 1, "`api.repo`/Repo#", READ),
        (27, "child", 1, "`api.repo`/Child#child().", DEFINITION), (28, "CLAIMS", 1, "`api.repo`/Repo#CLAIMS.", READ)],
    "api/consts.py": [(1, "TABLE", 1, "`api.consts`/TABLE.", DEFINITION),
                      (2, "MOVED", 1, "`api.consts`/MOVED.", DEFINITION)],
    "api/use.py": [
        (1, "consts", 1, "`api.consts`/__init__:", READ), (4, "read", 1, "`api.use`/read().", DEFINITION),
        (5, "consts", 1, "`api.consts`/__init__:", READ), (5, "TABLE", 1, "`api.consts`/TABLE.", READ),
        (8, "moved", 1, "`api.use`/moved().", DEFINITION), (9, "consts", 1, "`api.consts`/__init__:", READ),
        (9, "MOVED", 1, "`api.consts`/MOVED.", READ)],
    "api/patch.py": [(1, "consts", 1, "`api.consts`/__init__:", READ),
                     (3, "consts", 1, "`api.consts`/__init__:", READ), (3, "MOVED", 1, "`api.consts`/MOVED.", WRITTEN)],
    # an import of the constant by its name is no write of it
    "api/named.py": [(1, "TABLE", 1, "`api.consts`/TABLE.", READ), (4, "named", 1, "`api.named`/named().", DEFINITION),
                     (5, "TABLE", 1, "`api.consts`/TABLE.", READ)],
    "api/more.py": [
        ("from api import consts", "consts", 1, "`api.consts`/__init__:", READ),
        ("class Pair:", "Pair", 1, "`api.more`/Pair#", DEFINITION),
        ('PAIR = "pair"', "PAIR", 1, "`api.more`/Pair#PAIR.", DEFINITION),
        ("self.x, self.PAIR", "PAIR", 1, "`api.more`/Pair#PAIR.", WRITTEN),
        ("db[self.PAIR]", "PAIR", 1, "`api.more`/Pair#PAIR.", READ),
        ("class Grown:", "Grown", 1, "`api.more`/Grown#", DEFINITION),
        ('GROWN = "grown"', "GROWN", 1, "`api.more`/Grown#GROWN.", DEFINITION),
        ("self.GROWN +=", "GROWN", 1, "`api.more`/Grown#GROWN.", WRITTEN),
        ("db[self.GROWN]", "GROWN", 1, "`api.more`/Grown#GROWN.", READ),
        ("class Patched:", "Patched", 1, "`api.more`/Patched#", DEFINITION),
        ('PATCHED = "patched"', "PATCHED", 1, "`api.more`/Patched#PATCHED.", DEFINITION),
        ("db[self.PATCHED]", "PATCHED", 1, "`api.more`/Patched#PATCHED.", READ),
        ('Patched.PATCHED = "elsewhere"', "Patched", 1, "`api.more`/Patched#", READ),
        ('Patched.PATCHED = "elsewhere"', "PATCHED", 1, "`api.more`/Patched#PATCHED.", WRITTEN),
        ("class Defaulted:", "Defaulted", 1, "`api.more`/Defaulted#", DEFINITION),
        ('NAME: str = "defaulted"', "NAME", 1, "`api.more`/Defaulted#NAME.", DEFINITION),
        ("db[self.NAME]", "NAME", 1, "`api.more`/Defaulted#NAME.", READ),
        ("class BySetattr:", "BySetattr", 1, "`api.more`/BySetattr#", DEFINITION),
        ('SET = "set"', "SET", 1, "`api.more`/BySetattr#SET.", DEFINITION),
        ("db[self.SET]", "SET", 1, "`api.more`/BySetattr#SET.", READ),
        ("class Base:", "Base", 1, "`api.more`/Base#", DEFINITION),
        ('BASE = "base"', "BASE", 1, "`api.more`/Base#BASE.", DEFINITION),
        ("db[self.BASE]", "BASE", 1, "`api.more`/Base#BASE.", READ),
        ("class Sub(Base):", "Sub", 1, "`api.more`/Sub#", DEFINITION),
        ("class Sub(Base):", "Base", 1, "`api.more`/Base#", READ),
        ('BASE = "sub"', "BASE", 1, "`api.more`/Sub#BASE.", DEFINITION),
        ("class Holder:", "Holder", 1, "`api.more`/Holder#", DEFINITION),
        ("self.table = consts.TABLE", "table", 1, "`api.more`/Holder#table.", DEFINITION),
        ("self.table = consts.TABLE", "consts", 1, "`api.consts`/__init__:", READ),
        ("self.table = consts.TABLE", "TABLE", 1, "`api.consts`/TABLE.", READ),
        ("self.table = other", "table", 1, "`api.more`/Holder#table.", WRITTEN),
        ("db[self.table]", "table", 1, "`api.more`/Holder#table.", READ),
        ("def label", "label", 1, "`api.more`/label().", DEFINITION),
        ("return consts.TABLE.upper()", "consts", 1, "`api.consts`/__init__:", READ),
        ("return consts.TABLE.upper()", "TABLE", 1, "`api.consts`/TABLE.", READ),
        ("return consts.TABLE.upper()", "upper", 1, "scip-python python python-stdlib 3.13 builtins/str#upper().",
         READ),
        ("class Kept:", "Kept", 1, "`api.more`/Kept#", DEFINITION),
        ('KEPT = "kept"', "KEPT", 1, "`api.more`/Kept#KEPT.", DEFINITION),
        ("db[self.KEPT]", "KEPT", 1, "`api.more`/Kept#KEPT.", READ),
        ("class Front:", "Front", 1, "`api.more`/Front#", DEFINITION),
        ('KEPT = "front"', "KEPT", 1, "`api.more`/Front#KEPT.", DEFINITION),
        ("class Mixed(Front, Kept):", "Mixed", 1, "`api.more`/Mixed#", DEFINITION),
        ("class Mixed(Front, Kept):", "Front", 1, "`api.more`/Front#", READ),
        ("class Mixed(Front, Kept):", "Kept", 1, "`api.more`/Kept#", READ),
        ("class Counted:", "Counted", 1, "`api.more`/Counted#", DEFINITION),
        ('COUNT = "count"', "COUNT", 1, "`api.more`/Counted#COUNT.", DEFINITION),
        ("cls.COUNT = name", "COUNT", 1, "`api.more`/Counted#COUNT.", WRITTEN),
        ("db[self.COUNT]", "COUNT", 1, "`api.more`/Counted#COUNT.", READ)],
    "api/star.py": [(1, "STAR", 1, "`api.star`/STAR.", DEFINITION)],
    "api/stars.py": [(1, "star", 1, "`api.star`/__init__:", READ), (4, "starred", 1, "`api.stars`/starred().", DEFINITION),
                     (5, "star", 1, "`api.star`/__init__:", READ), (5, "STAR", 1, "`api.star`/STAR.", READ)],
}
# A class's base, as scip-python relates it (`Shape# <- Square#` in the recorded fixture of tests/fixtures/code-graph).
IMPLEMENTS = {"api/repo.py": [("`api.repo`/Child#", "`api.repo`/Repo#")],
              "api/more.py": [("`api.more`/Sub#", "`api.more`/Base#"), ("`api.more`/Mixed#", "`api.more`/Front#"),
                              ("`api.more`/Mixed#", "`api.more`/Kept#")]}
RULES = [{"written": "*.find", "in": ["api"], "link": "legge", "store": "db", "key": "holder"}]
KEYS = {"db/claims": ["api/repo.py::Child.child", "api/repo.py::Repo.load"],
        "db/orders": ["api/named.py::named", "api/use.py::read"]}
# The reads that must name no binding: (file, a text only that line holds).
UNBOUND = [("api/repo.py", "db[self.TWICE]"), ("api/repo.py", "db[self.OWN]"), ("api/use.py", "consts.MOVED"),
           *(("api/more.py", f"db[self.{name}]") for name in ("PAIR", "GROWN", "PATCHED", "NAME", "SET", "BASE",
                                                             "table", "KEPT", "COUNT")),
           ("api/stars.py", "star.STAR")]


def _line(rel: str, at) -> int:
    if isinstance(at, int):
        return at
    [number] = [n for n, text in enumerate(SOURCES[rel].split("\n"), 1) if at in text]
    return number


def _occurrence(line: int, start: int, end: int, symbol: str, role: int) -> bytes:
    return (graph_tests._field(1, b"".join(graph_tests._varint(n) for n in (line - 1, start, end)))
            + graph_tests._field(2, symbol) + graph_tests._field(3, role))


def _index(written: int, without=()) -> bytes:
    documents = []
    for rel, items in OCCURRENCES.items():
        if rel in without:
            continue
        lines = SOURCES[rel].split("\n")
        occurrences = []
        for at, word, nth, symbol, role in items:
            line = _line(rel, at)
            start = -1
            for _ in range(nth):
                start = lines[line - 1].index(word, start + 1)
            occurrences.append(_occurrence(line, start, start + len(word),
                                           symbol if symbol.startswith("scip-python ") else P + symbol,
                                           written if role == WRITTEN else role))
        informations = [graph_tests.information(P + symbol, P + base) for symbol, base in IMPLEMENTS.get(rel, ())]
        documents.append(graph_tests._field(2, graph_tests._field(1, rel)
                                            + b"".join(graph_tests._field(2, o) for o in occurrences)
                                            + b"".join(graph_tests._field(3, i) for i in informations)))
    return b"".join(documents)


def _analyzed(work: Path, written: int, without=()) -> Path:
    """The snapshot of the sources and its edge store, built from the documents as the Python stage builds it."""
    manifest = read_project(work, SOURCES)
    (work / "index.scip").write_bytes(_index(written, without))
    with code_graph.Snapshot(manifest) as snapshot:
        index = code_graph.Index(snapshot.root)
        index.load(work / "index.scip")
        hops, traversal, _prepared = code_graph.adapter_traversal(python_indexer, index, snapshot)
        # the indexer and the resolver named as the pass names them, so the view takes the store as its own
        name, version = engine_pass.ENGINE_LANGUAGES["python"].name, python_indexer.VERSION
        absent = sorted(rel for rel in SOURCES if rel not in index.documents)
        built = code_graph.build(index, snapshot, "python", hops, {"name": name, "version": version},
                                 python_indexer.missing(index, absent) if absent else {},
                                 traversal, python_indexer.static(index))
        code_graph.write_store(snapshot, resolve_edges.default_edge_store(manifest), {"python": built},
                               f"{name}@{version}")
    return manifest


def _bindings(manifest: Path) -> dict[tuple, str]:
    """`(file, name) -> id` of the snapshot's bindings."""
    import semantic_store
    from snapshot_store import open_snapshot
    with open_snapshot(manifest) as store, semantic_store.semantic_reader(store) as db:
        return {(file, name): identity for identity, file, name in db.execute(
            "SELECT id, file, name FROM sem_declarations WHERE kind='binding'")}


def _read(view: dict, file: str, at) -> dict:
    """The read of a dotted name on that line: `self.CLAIMS`, `consts.TABLE`."""
    line = _line(file, at)
    [found] = [ref for ref in view["reads"] if ref["file"] == file and ref["span"][0] == line
               and len(ref["parts"]) == 2]
    return found


class DeclarationIdentityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.work = Path(tempfile.mkdtemp(prefix="declaration-identity-")).resolve()
        cls.runs = {}
        for written in (DEFINITION, 4, READ):
            manifest = _analyzed(cls.work / str(written), written)
            cls.runs[written] = (manifest, edge_view.load_edge_view(manifest),
                                 flows.link_facts(manifest, flows.validate_rules(RULES)))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.work, True)

    def test_a_read_of_a_value_written_once_names_its_binding_in_the_view(self):
        for written, (manifest, view, _links) in self.runs.items():
            with self.subTest(written=written):
                bindings = _bindings(manifest)
                claims, table = bindings[("api/repo.py", "CLAIMS")], bindings[("api/consts.py", "TABLE")]
                self.assertEqual(_read(view, "api/repo.py", 5).get("binding_id"), claims)
                self.assertEqual(_read(view, "api/repo.py", 28).get("binding_id"), claims)  # inherited
                self.assertEqual(_read(view, "api/use.py", 5).get("binding_id"), table)  # beside a chained read

    def test_a_value_that_can_be_another_at_run_time_names_no_binding_whatever_role_the_engine_gives_the_write(self):
        for written, (_manifest, view, _links) in self.runs.items():
            for file, at in UNBOUND:
                with self.subTest(written=written, read=at):
                    self.assertNotIn("binding_id", _read(view, file, at))

    def test_the_constant_is_the_store_key_and_every_other_value_a_gap(self):
        for written, (_manifest, _view, links) in self.runs.items():
            with self.subTest(written=written):
                self.assertEqual({key: sorted(store["reads"]) for key, store in links["stores"].items()}, KEYS)
                gapped = {gap["symbol"] for gap in links["gaps"]}
                self.assertLessEqual({"api/repo.py::Twice.load", "api/repo.py::Own.load", "api/use.py::moved",
                                      *(f"api/more.py::{name}.load" for name in ("Pair", "Grown", "Patched",
                                                                                  "Defaulted", "BySetattr", "Base",
                                                                                  "Holder", "Kept", "Counted")),
                                      "api/stars.py::starred"}, gapped)

    def test_the_engine_names_only_a_modules_or_a_classs_binding(self):
        """A parameter or a local differs from call to call: no row of the engine's store names it. (The view keeps
        the lexical resolver's `binding_id` of a bare name beside the engine's answer, as before: `Facts.constants`
        keeps only a `binding`.)"""
        import semantic_store
        from snapshot_store import open_snapshot
        for written, (manifest, _view, _links) in self.runs.items():
            with self.subTest(written=written), open_snapshot(manifest) as store, \
                    semantic_store.semantic_reader(store) as db:
                lookup = semantic_store._Resolver(db)
                rows, _binding, reason = resolve_edges.read_edge_store(resolve_edges.default_edge_store(manifest), store)
                self.assertIsNone(reason)
                named = [row["payload"]["binding_id"] for row in rows if (row.get("payload") or {}).get("binding_id")]
                self.assertTrue(named)
                for identity in named:
                    declaration = lookup.declaration(identity)
                    scope = lookup.scope_record(declaration["file"], declaration["scope"])
                    self.assertEqual((declaration["kind"], scope["kind"] in ("module", "class")), ("binding", True),
                                     identity)

    def test_a_file_the_index_has_no_document_for_takes_every_binding_of_the_language_away(self):
        """A write in that file would have no occurrence: no value of the language is known to be written once."""
        manifest = _analyzed(self.work / "without", READ, without={"api/patch.py"})
        view = edge_view.load_edge_view(manifest)
        self.assertEqual([ref for ref in view["reads"] if len(ref["parts"]) == 2 and ref.get("binding_id")], [])


GO = {
    "consts/consts.go": 'package consts\n\nvar Table = "orders"\n',
    "use/use.go": ('package use\n\nimport "example.com/app/consts"\n\nfunc Patch() {\n\tconsts.Table = "other"\n}\n\n'
                   'func Read() string {\n\treturn consts.Table\n}\n'),
}
G = "scip-go gomod example.com/app . "
GO_OCCURRENCES = {  # (line, word, symbol, role), as scip-go writes them
    "consts/consts.go": [(3, "Table", "`example.com/app/consts`/Table.", 1)],
    "use/use.go": [(5, "Patch", "`example.com/app/use`/Patch().", 1), (6, "Table", "`example.com/app/consts`/Table.", 4),
                   (9, "Read", "`example.com/app/use`/Read().", 1), (10, "Table", "`example.com/app/consts`/Table.", 8)],
}


class ReaderDeclarationTests(unittest.TestCase):
    def test_a_language_whose_reader_records_an_assignments_target_as_a_read_gives_no_binding(self):
        """The Go reader records `consts.Table = "other"` as a read, so the write lies inside a read the snapshot
        records and the written-again check cannot see it: only the reader's declaration keeps the binding away.
        With the declaration the Python reader makes, the same documents would give one."""
        import languages
        work = Path(tempfile.mkdtemp(prefix="declaration-identity-go-")).resolve()
        self.addCleanup(shutil.rmtree, work, True)
        manifest = read_project(work, GO)
        documents = b""
        for rel, items in GO_OCCURRENCES.items():
            lines = GO[rel].split("\n")
            occurrences = b""
            for line, word, symbol, role in items:
                start = lines[line - 1].index(word)
                occurrences += graph_tests._field(2, _occurrence(line, start, start + len(word), G + symbol, role))
            documents += graph_tests._field(2, graph_tests._field(1, rel) + occurrences)
        (work / "index.scip").write_bytes(documents)

        def bindings() -> list:
            with code_graph.Snapshot(manifest) as snapshot:
                index = code_graph.Index(snapshot.root)
                index.load(work / "index.scip")
                _graph, references = code_graph.build(index, snapshot, "go", {}, {"name": "scip-go", "version": "t"},
                                                      {}, code_graph.Traversal(index, snapshot, {}))
            ends = [end for reference in references.values() if reference["name"] == "consts.Table"
                    and reference["site"] == "use/use.go:10" for end in reference["ends"]]
            self.assertTrue(ends and all(end.cls == "project-value" for end in ends), ends)
            return [end.binding for end in ends if end.binding]

        self.assertEqual(bindings(), [])
        reader = type(languages.get_adapter("go"))
        with unittest.mock.patch.object(reader, "assignment_targets_are_reads", False, create=True):
            self.assertEqual(len(bindings()), 1)  # the declaration alone decides it


if __name__ == "__main__":
    unittest.main()
