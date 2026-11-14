"""C and C++ through scip-clang: the ends of two small projects in `fixtures/c` and `fixtures/cpp`, each with
the index scip-clang v0.4.1 wrote, read with `adapters/clang.py` and the shared `scip_graph.py`.

    python -m pytest benchmarks/inference-audit/test_clang_graph.py

Rebuild a fixture's index after changing its sources (scip-clang runs on Linux only, so on Modal):
`python benchmarks/inference-audit/lang_clang.py spawn --fixtures`, then `fetch --fixtures`.
"""
from __future__ import annotations

import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import scip_graph  # noqa: E402
from adapters import clang  # noqa: E402

FIXTURES = HERE / "fixtures"
PROJECTS = {"c": "cfixture@0", "cpp": "cppfixture@0"}

# Each syntactic call site (`file:line:byte column`) -> what its ends reach: a project function by the
# `file:line` of its body or prototype (`impl` through dispatch), an external function by name, `value`
# when no function is reached, or the hole's class.
C_ENDS = {
    "main.c:4:39 LOG": {"util.c:10"},  # the macro's expansion is referenced at the call
    "main.c:9:21 add": {"util.c:6"},  # after a non-ASCII comment: byte columns
    "main.c:10:9 SQUARE": {"util.c:8"},
    "main.c:11:11 compute": {"value"},  # function pointer in a struct
    "main.c:12:6 fp": {"value"},  # function pointer variable
    "main.c:13:4 run_callback": {"util.c:12"},
    "main.c:14:14 strlen": {"external strlen"},
    "main.c:15:9 SQUARE": {"util.c:6", "util.c:8"},  # mul from the body, add from the argument
    "main.c:15:16 add": {"hole no-occurrence"},  # inside a macro's argument: reported at the macro's name
    "main.c:16:11 platform_init": {"util.h:16"},  # defined only in a file no compile command covers
    "util.c:4:33 add": {"util.c:6"},
    "util.c:8:31 twice": {"util.c:4"},
    "util.c:10:36 printf": {"external printf"},
    "util.c:13:7 on_event": {"value"},
    "util.c:15:4 fast_path": {"hole no-occurrence"},  # branch not compiled
    "util.c:17:4 log_message": {"util.c:10"},
    "platform_win.c:3:33 add": {"hole no-document"},
}
CPP_ENDS = {
    "shapes.cpp:15:30 twice": {"shapes.hpp:30"},  # template
    "shapes.cpp:21:52 area": {"shapes.hpp:8", "impl shapes.cpp:9", "impl shapes.hpp:21"},  # virtual
    "main.cpp:8:28 Square": {"shapes.hpp:20"},  # new: the constructor is named where the type starts
    "main.cpp:10:43 scale": {"shapes.cpp:15"},  # overload (int), inside a lambda
    "main.cpp:13:31 total": {"shapes.cpp:19"},
    "main.cpp:13:54 area": {"shapes.hpp:8", "impl shapes.cpp:9", "impl shapes.hpp:21"},
    "main.cpp:13:70 area": {"shapes.cpp:9"},  # static type Circle, no override below it
    "main.cpp:14:11 twice": {"shapes.hpp:30"},  # through `using geo::twice`
    "main.cpp:14:29 scale": {"shapes.cpp:17"},  # overload (double)
    "main.cpp:14:42 doubled": {"main.cpp:10"},  # the lambda held by an `auto` variable
    "main.cpp:15:9 printf": {"external printf"},
    "main.cpp:15:37 name": {"shapes.hpp:9", "impl shapes.cpp:11"},
    "main.cpp:16:11 push_back": {"external push_back"},
    "main.cpp:17:31 c_helper": {"hole no-occurrence"},  # `extern "C"`: scip-clang writes no occurrence at all
    "main.cpp:18:4 printf": {"hole no-occurrence"},  # the C library, `extern "C"` in C++
}
# Occurrences that are no syntactic call: `file:line`, the text the index names, its ends.
CPP_OCCURRENCES = {
    ("main.cpp", 12, "+"): {"shapes.cpp:13"},  # operator+
    ("main.cpp", 7, "circle"): {"shapes.cpp:7"},  # constructor of a declared variable
}


def target(end) -> str | None:
    if end.cls == "project-callable":
        return ("impl " if "implementation" in end.chain else "") + (end.target.split(" ")[0] if end.target else end.key)
    parts = scip_graph.split_symbol(scip_graph._global(end.key)) if end.cls == "external" else None
    items = scip_graph.descriptors(parts[4]) if parts else []
    return f"external {items[-1][0]}" if items and items[-1][1] == "method" else None


def labels(ends, hole: str = "") -> set:
    if hole:
        return {f"hole {hole}"}
    return {label for label in map(target, ends) if label} or {"value" if end.cls == "project-value" else end.cls
                                                               for end in ends}


@pytest.fixture(scope="module")
def graphs():
    out = {}
    for name, project in PROJECTS.items():
        root = FIXTURES / name
        index = scip_graph.Index(root)
        index.load(root / "index.scip")
        clang.dedupe(index)
        clang.utf8_columns(index)
        files = clang.perimeter(root, name)
        snapshot = clang.SyntaxSnapshot(root, files, name)
        clang.enclose(index, snapshot)
        hops = clang.hops(index, name)
        traversal = scip_graph.Traversal(index, snapshot, hops, same_range=clang.same_range(index),
                                         classify=clang.classifier(project))
        reasons = clang.missing(index, [rel for rel in files if not index.documents.get(rel)])
        graph, references = scip_graph.build(index, snapshot, name, hops, {}, reasons, traversal,
                                             refine=clang.refine)
        rows = {f"{identity} {row['name']}": row for identity, row in references.items()}
        out[name] = {"index": index, "snapshot": snapshot, "traversal": traversal, "graph": graph, "rows": rows}
    return out


@pytest.mark.parametrize("site", sorted(C_ENDS))
def test_c_fixture_end(graphs, site):
    row = graphs["c"]["rows"][site]
    assert labels(row["ends"], row["hole"]) == C_ENDS[site]


@pytest.mark.parametrize("site", sorted(CPP_ENDS))
def test_cpp_fixture_end(graphs, site):
    row = graphs["cpp"]["rows"][site]
    assert labels(row["ends"], row["hole"]) == CPP_ENDS[site]


@pytest.mark.parametrize("place", sorted(CPP_OCCURRENCES))
def test_cpp_occurrence_end(graphs, place):
    index, traversal = graphs["cpp"]["index"], graphs["cpp"]["traversal"]
    rel, line, name = place
    text = index.line(rel, line)
    keys = {o.key for o in index.documents[rel] if o.line == line and not o.definition and text[o.start:o.end] == name}
    assert labels([end for key in sorted(keys) for end in traversal.ends(key)]) == CPP_OCCURRENCES[place]


def test_chains_name_the_declaration_the_lambda_and_the_using(graphs):
    chains = {site: {tuple(end.chain) for end in graphs[name]["rows"][site]["ends"] if end.cls == "project-callable"}
              for name, site in (("c", "main.c:16:11 platform_init"), ("cpp", "main.cpp:14:42 doubled"),
                                 ("cpp", "main.cpp:14:11 twice"), ("c", "main.c:9:21 add"))}
    assert chains == {"main.c:16:11 platform_init": {("declaration",)}, "main.cpp:14:42 doubled": {("lambda",)},
                      "main.cpp:14:11 twice": {("same-range",)}, "main.c:9:21 add": {()}}


def test_declared_only_functions_carry_no_package(graphs):
    """The index gives a function only declared in a translation unit an empty package; C++ library symbols
    defined in libstdc++ headers carry the package the package map names."""
    packages = {}
    for name, site in (("c", "main.c:14:14 strlen"), ("cpp", "main.cpp:16:11 push_back")):
        traversal = graphs[name]["traversal"]
        packages[site] = {traversal.package(end.key)["package"] for end in graphs[name]["rows"][site]["ends"]
                          if end.cls == "external"}
    assert packages["main.c:14:14 strlen"] == {"(none)"}
    assert all(item.startswith("libstdc") for item in packages["main.cpp:16:11 push_back"])


def test_edges_start_at_the_enclosing_function(graphs):
    edges = [edge for edge in graphs["c"]["graph"]["edges"] if edge["site"] == "main.c:13"]
    assert {edge["from"] for edge in edges} == {"cxx . cfixture 0$ main(b126dc7c1de90089)."}


def test_files_without_document_say_why(graphs):
    missing = {item["path"]: item["reason"] for item in graphs["c"]["graph"]["files"]["missing"]}
    assert missing == {"platform_win.c": "no compile command: not built by the default configuration"}


def test_non_ascii_lines_read_in_bytes(graphs):
    for name in PROJECTS:
        assert clang.byte_columns(graphs[name]["index"]) and all(
            key.startswith("bytes True, utf-16 False") for key in clang.byte_columns(graphs[name]["index"]))


def test_a_variable_is_no_alias_of_its_constructor(graphs):
    """`geo::Circle circle(2.0)`: the constructor is referenced at the variable's name; a use of the variable is
    not a call of the constructor."""
    ends = graphs["cpp"]["traversal"].ends("main.cpp#local 0")
    assert [(end.cls, end.chain) for end in ends] == [("project-value", ())]


def test_casts_are_no_call_sites(graphs):
    names = {row["name"] for row in graphs["cpp"]["rows"].values() if row["site"] == "main.cpp:17"}
    assert names == {"c_helper"}


def test_extern_c_functions_have_no_occurrence(graphs):
    index = graphs["cpp"]["index"]
    assert not [o for rel in ("shapes.hpp", "shapes.cpp", "main.cpp") for o in index.documents[rel]
                if "c_helper" in o.key]


def test_export_macro_does_not_hide_a_class(tmp_path):
    source = ["#define LIB", "class LIB Node : public Base {", "    virtual bool Accept() const = 0;",
              "    Node( const Node& );", "};", ""]
    (tmp_path / "a.hpp").write_text("\n".join(source), encoding="utf-8")
    syntax = clang.Syntax(tmp_path, "a.hpp", "cpp")
    assert sorted(set(syntax.declared.values())) == ["a.hpp:2 Node", "a.hpp:3 Accept (declaration)",
                                                     "a.hpp:4 Node (declaration)"]
    assert syntax.counts["annotation macro blanked"] == 1 and not syntax.calls


def test_repeated_occurrences_are_kept_once():
    index = scip_graph.Index(FIXTURES / "cpp")
    index.load(FIXTURES / "cpp" / "index.scip")
    assert clang.dedupe(index) > 0
    assert all(len(items) == len(set(items)) for items in index.documents.values())


def test_product_snapshot_holds_no_c_or_cpp(tmp_path):
    """The reason the adapter stands in for the snapshot: the product reads no C or C++ file."""
    source = tmp_path / "c"
    shutil.copytree(FIXTURES / "c", source, ignore=shutil.ignore_patterns("index.scip"))
    manifest = tmp_path / "manifest.sqlite"
    done = subprocess.run([sys.executable, "-I", "snapshot.py", "write", str(source), "--out", str(manifest),
                           "--no-engine", "--no-index", "--no-modules"], cwd=scip_graph._SCRIPTS,
                          capture_output=True, text=True, timeout=300)
    assert done.returncode == 0, done.stderr
    with sqlite3.connect(manifest) as connection:
        files = {row[0] for row in connection.execute("SELECT path FROM files")}
    assert files == {"CMakeLists.txt"}
