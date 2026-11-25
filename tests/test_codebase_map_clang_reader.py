"""The C and C++ source reader: what the snapshot holds for the fixtures in `fixtures/clang-reader/{c,cpp}`.

Every expectation below was written by reading the fixture's source, before the reader existed. A reference is
named `"LINE NAME"` (its name parts joined by `.`, `#2` for the second one of that name on the line) and ends at
a declaration (`FILE:LINE` of the declaration's name) or at the reason it stays unresolved.

    python -B -m pytest -q -p no:cacheprovider tests/test_codebase_map_clang_reader.py
"""
from __future__ import annotations

import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "daodan/core"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import resolution  # noqa: E402
import snapshot  # noqa: E402
from languages import SUPPORTED_EXTENSIONS, cfamily, detect_language, get_adapter  # noqa: E402
from snapshot_store import _unpack, open_snapshot  # noqa: E402
from read_manifest import read_manifest  # noqa: E402

FIXTURES = HERE / "fixtures/clang-reader"

# Both C files and both C++ files: the reader's language, by suffix.
LANGUAGES = {"c": {"main.c", "util.c", "util.h", "platform_win.c", "decoy.c", "caller.c"},
             "cpp": {"main.cpp", "shapes.cpp", "shapes.hpp"}}

# The declarations that can be a reference's target, by qualified name: kind, name line and column, flags
# (`contract` a prototype without a body, `nonlexical` no name a lookup can find).
C_DECLARATIONS = {
    "util.h": {"handler": ("class", 7, 7, {"nonlexical"}),
               "add": ("function", 12, 4, {"contract"}), "mul": ("function", 13, 4, {"contract"}),
               "log_message": ("function", 14, 5, {"contract"}), "run_callback": ("function", 15, 5, {"contract"}),
               "platform_init": ("function", 16, 4, {"contract"})},
    # The prototype of `twice` gives way to its definition in the same file.
    "util.c": {"twice": [("function", 4, 11, {"contract", "nonlexical"}), ("function", 10, 11, set())],
               "add": ("function", 6, 4, set()), "mul": ("function", 8, 4, set()),
               "log_message": ("function", 12, 5, set()), "run_callback": ("function", 14, 5, set())},
    "main.c": {"on_event_impl": ("function", 4, 12, set()), "main": ("function", 6, 4, set())},
    "platform_win.c": {"platform_init": ("function", 3, 4, set())},
    "decoy.c": {"twice": ("function", 1, 11, set()), "quad": ("function", 3, 4, set())},
    "caller.c": {"use_twice": ("function", 3, 4, set())},
}
CPP_DECLARATIONS = {
    "shapes.hpp": {
        "geo.Shape": ("class", 6, 7, set()), "geo.Shape.~Shape": ("method", 7, 12, {"contract"}),
        "geo.Shape.area": ("method", 8, 19, {"contract"}), "geo.Shape.name": ("function", 9, 24, set()),
        "geo.Circle": ("class", 12, 7, set()), "geo.Circle.Circle": ("method", 13, 13, {"contract"}),
        "geo.Circle.area": ("method", 14, 11, {"contract"}), "geo.Circle.name": ("method", 15, 16, {"contract"}),
        "geo.Square": ("class", 19, 7, set()), "geo.Square.Square": ("function", 20, 13, set()),
        "geo.Square.area": ("function", 21, 11, set()),
        "geo.Vec": ("class", 25, 7, set()), "geo.Vec.operator+": ("method", 27, 8, {"contract"}),
        # Free functions: the translation unit can add an overload, so no lookup finds them.
        "geo.twice": ("function", 30, 24, {"nonlexical"}),
        "geo.scale": [("function", 32, 4, {"contract", "nonlexical"}), ("function", 33, 7, {"contract", "nonlexical"})],
        "geo.total": ("function", 34, 7, {"contract", "nonlexical"}),
        "c_helper": ("function", 38, 15, {"contract", "nonlexical"}),
        "geo": ("class", 4, 0, {"nonlexical"}),  # a namespace: qualifies its members, names nothing an engine answers
    },
    "shapes.cpp": {
        "geo.Shape.~Shape": ("function", 5, 7, {"nonlexical"}), "geo.Circle.Circle": ("function", 7, 8, {"nonlexical"}),
        "geo.Circle.area": ("function", 9, 15, {"nonlexical"}), "geo.Circle.name": ("function", 11, 20, {"nonlexical"}),
        "geo.Vec.operator+": ("function", 13, 9, {"nonlexical"}),
        "geo.scale": [("function", 15, 4, {"nonlexical"}), ("function", 17, 7, {"nonlexical"})],
        "geo.total": ("function", 19, 7, {"nonlexical"}), "c_helper": ("function", 27, 15, {"nonlexical"}),
        "geo": ("class", 3, 0, {"nonlexical"}),
    },
    "main.cpp": {"main": ("function", 6, 4, {"nonlexical"}), "main.(lambda)": ("function", 10, 19, {"nonlexical"})},
}

EXPORTS = {
    "util.h": {"add", "mul", "log_message", "run_callback", "platform_init"},
    "util.c": {"add", "mul", "log_message", "run_callback"},  # `static int twice` stays in its file
    "main.c": {"main"}, "platform_win.c": {"platform_init"}, "decoy.c": {"quad"}, "caller.c": {"use_twice"},
    "shapes.hpp": {"c_helper"}, "shapes.cpp": {"c_helper"}, "main.cpp": {"main"},
}

# `#include "x.h"`: the project file it names; `<x.h>`: external, no file.
INCLUDES = {
    "util.c": {"<stdio.h>": [], "util.h": ["util.h"]}, "main.c": {"<string.h>": [], "util.h": ["util.h"]},
    "platform_win.c": {"util.h": ["util.h"]}, "caller.c": {"util.h": ["util.h"]}, "util.h": {}, "decoy.c": {},
    "main.cpp": {"<cstdio>": [], "shapes.hpp": ["shapes.hpp"]}, "shapes.cpp": {"shapes.hpp": ["shapes.hpp"]},
    "shapes.hpp": {"<vector>": []},
}

# What a name from the translation unit reaches is not read: the lookup stops there, never at a builtin.
OUTSIDE = "scope-unresolved"
UNDECLARED = "included-name-undeclared"
NAMESPACED = "included-namespace-member"
CALLS = {
    "util.c": {"8 twice": "util.c:10", "10 add": "util.c:6", "12 printf": UNDECLARED,
               "15 h.on_event": "unknown-receiver", "17 fast_path": UNDECLARED, "19 log_message": "util.c:12"},
    "main.c": {"4 LOG": UNDECLARED, "9 add": "util.c:6", "10 SQUARE": UNDECLARED, "11 h.compute": "unknown-receiver",
               "12 fp": "dynamic-callee", "13 run_callback": "util.c:14", "14 strlen": UNDECLARED,
               "15 SQUARE": UNDECLARED, "15 add": "util.c:6", "16 platform_init": "platform_win.c:3"},
    "platform_win.c": {"3 add": "util.c:6"},
    "decoy.c": {"3 twice": "decoy.c:1", "3 twice#2": "decoy.c:1"},
    "caller.c": {"3 twice": UNDECLARED},  # neither `static int twice` of util.c nor that of decoy.c
    "util.h": {},
    "shapes.hpp": {},
    "shapes.cpp": {"15 twice": NAMESPACED, "21 shape.area": "unknown-receiver"},
    "main.cpp": {"8 geo.Square": OUTSIDE, "10 geo.scale": OUTSIDE, "13 geo.total": OUTSIDE,
                 "13 shape.area": "unknown-receiver", "13 circle.area": "unknown-receiver",
                 "14 twice": "import-target-missing-or-ambiguous", "14 geo.scale": OUTSIDE,
                 "14 doubled": "non-callable-binding", "15 std.printf": OUTSIDE, "15 shape.name": "unknown-receiver",
                 "16 shapes.push_back": "unknown-receiver", "17 c_helper": "shapes.cpp:27", "18 printf": UNDECLARED},
}
# A variable assigned after its declaration has two binding sites, so a read of it is ambiguous, as in every
# language (`n += ...` in main.c, `sum += ...` in shapes.cpp).
READS = {
    "util.c": {"6 a#2": "non-callable-binding", "10 v#2": "non-callable-binding", "15 value": "non-callable-binding"},
    "main.c": {"7 on_event_impl": "main.c:4", "7 add": "util.c:6", "8 on_event_impl": "main.c:4",
               "13 h": "non-callable-binding", "16 n": "ambiguous-binding"},
    "shapes.hpp": {"20 side#3": "non-callable-binding", "21 side": OUTSIDE, "30 value#2": "non-callable-binding"},
    "shapes.cpp": {"7 radius#3": "non-callable-binding", "9 radius": OUTSIDE, "13 x": OUTSIDE,
                   "13 other.x": "unknown-receiver", "21 shapes": "non-callable-binding", "22 sum": "ambiguous-binding"},
    "main.cpp": {"9 circle": "non-callable-binding", "12 a": "non-callable-binding", "15 c.x": "unknown-receiver",
                 "19 shape": "non-callable-binding"},
}

# The file outline: symbols with their kind and line span, qualified like the declarations.
SYMBOLS = {
    "util.h": {"handler": ("struct", 7, 10)},
    "util.c": {"add": ("function", 6, 6), "mul": ("function", 8, 8), "twice": ("function", 10, 10),
               "log_message": ("function", 12, 12), "run_callback": ("function", 14, 21)},
    "shapes.hpp": {"geo.Shape": ("struct", 6, 10), "geo.Shape.name": ("method", 9, 9), "geo.Circle": ("struct", 12, 17),
                   "geo.Square": ("struct", 19, 23), "geo.Square.Square": ("method", 20, 20),
                   "geo.Square.area": ("method", 21, 21), "geo.Vec": ("struct", 25, 28), "geo.twice": ("function", 30, 30)},
    "shapes.cpp": {"geo.Shape.~Shape": ("function", 5, 5), "geo.Circle.Circle": ("function", 7, 7),
                   "geo.Circle.area": ("function", 9, 9), "geo.Circle.name": ("function", 11, 11),
                   "geo.Vec.operator+": ("function", 13, 13), "geo.scale": ("function", 15, 17),
                   "geo.total": ("function", 19, 23), "c_helper": ("function", 27, 27)},
}


def _built(source: Path, manifest: Path) -> dict:
    snapshot.write_snapshot(source, manifest)
    db = sqlite3.connect(manifest)
    try:
        out = {"languages": dict(db.execute("SELECT file, language FROM sem_coverage")),
               "status": dict(db.execute("SELECT file, status FROM sem_coverage")),
               "declarations": {}, "references": {}, "exports": {}, "modules": {}, "imports": {}, "scopes": {},
               "lines": {}, "symbols": {}}
        for identity, rel, name, kind, blob in db.execute(
                "SELECT id, file, name, kind, payload FROM sem_declarations"):
            out["declarations"][identity] = {"file": rel, "name": name, "kind": kind, **_unpack(blob)}
        for rel, kind, resolution, target, blob in db.execute(
                "SELECT file, kind, resolution, target_id, payload FROM sem_references ORDER BY file, l0, c0"):
            out["references"].setdefault(rel, []).append(
                {"kind": kind, "resolution": resolution, "target": target, **_unpack(blob)})
        for rel, name in db.execute("SELECT file, name FROM sem_exports"):
            out["exports"].setdefault(rel, set()).add(name)
        for rel, module, target in db.execute("SELECT file, module, target FROM sem_modules"):
            out["modules"].setdefault(rel, {}).setdefault(module, []).append(target)
        for rel, kind, blob in db.execute("SELECT file, kind, payload FROM sem_bindings WHERE kind='import'"):
            out["imports"].setdefault(rel, []).append(_unpack(blob))
        for rel, identity, blob in db.execute("SELECT file, id, payload FROM sem_scopes"):
            out["scopes"].setdefault(rel, {})[identity] = _unpack(blob)
    finally:
        db.close()
    for rel in out["languages"]:
        out["lines"][rel] = (source / rel).read_bytes().split(b"\n")
    with open_snapshot(manifest) as store:
        for rel, entry in store.iter_files():
            out["symbols"][rel] = entry.get("symbols") or {}
    return out


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    out = {}
    for name in ("c", "cpp"):
        source = tmp_path_factory.mktemp(name) / name
        shutil.copytree(FIXTURES / name, source)
        out[name] = _built(source, source.parent / "manifest.sqlite")
    return out


def _flags(item: dict) -> set:
    return {flag for flag, on in (("contract", item.get("contract")), ("nonlexical", item.get("lexical") is False)) if on}


def _declared(data: dict, rel: str) -> dict:
    out = {}
    for item in data["declarations"].values():
        if item["file"] != rel or item["kind"] not in ("function", "method", "class"):
            continue
        span = item.get("name_span") or item["span"]
        out.setdefault(item["qualified_name"], []).append((item["kind"], span[0], span[1], _flags(item)))
    return out


def _site(data: dict, rel: str, key: str) -> tuple[int, int]:
    """`(line, byte column)` of the last name of the `#n`-th text on the line spelling the reference's parts."""
    line, name = key.split(" ", 1)
    name, _, nth = name.partition("#")
    parts = name.split(".")
    pattern = rb"(?<!\w)" + rb"\s*(?:\.|->|::)\s*".join(re.escape(part.encode("utf-8")) for part in parts) + rb"(?!\w)"
    found = list(re.finditer(pattern, data["lines"][rel][int(line) - 1]))
    assert len(found) >= int(nth or 1), key
    return int(line), found[int(nth or 1) - 1].end() - len(parts[-1].encode("utf-8"))


def _outcome(data: dict, reference: dict) -> str:
    if reference["resolution"] == "resolved":
        target = data["declarations"][reference["target"]]
        span = target.get("name_span") or target["span"]
        return f"{target['file']}:{span[0]}"
    return reference.get("reason") or "unresolved"


def _found(data: dict, rel: str, kind: str, key: str) -> dict:
    line, column = _site(data, rel, key)
    name = key.split(" ", 1)[1].partition("#")[0]
    found = [r for r in data["references"].get(rel, ()) if r["kind"] == kind and ".".join(r["parts"]) == name
             and r["span"][2] == line and r["span"][3] - len(r["parts"][-1].encode("utf-8")) == column]
    assert len(found) == 1, (rel, key, [(r["parts"], r["span"]) for r in data["references"].get(rel, ())
                                       if r["span"][0] == line])
    return found[0]


def _cases(table: dict, project: str):
    return [(project, rel, key) for rel in sorted(table) for key in sorted(table[rel])
            if rel in LANGUAGES[project]]


def test_suffixes_name_the_two_languages():
    for suffix in (".c", ".h"):
        assert SUPPORTED_EXTENSIONS[suffix] == "c"
    for suffix in (".cc", ".cpp", ".cxx", ".hpp", ".hh", ".hxx"):
        assert SUPPORTED_EXTENSIONS[suffix] == "cpp"
    assert get_adapter("c").language == "c" and get_adapter("cpp").language == "cpp"


def test_a_header_is_cpp_only_when_its_text_has_what_c_lacks():
    cpp = ["namespace geo {\nint f();\n}\n", "class Node {\n public:\n  int x;\n};\n",
           "template <typename T> T twice(T v);\n", "using namespace std;\n",
           # otel-demo's meter_common.h: a namespace alias, an anonymous namespace, `std::` names; a standard
           # library header, as Linguist's own rule for `.h` has it.
           "namespace sdk = opentelemetry::sdk;\nnamespace\n{\nstd::shared_ptr<int> init();\n}\n",
           "std::size_t bound(std::size_t n);\n", "#include <vector>\nint f(void);\n"]
    c = ["#ifdef __cplusplus\nextern \"C\" {\n#endif\nint f(void);\n#ifdef __cplusplus\n}\n#endif\n",
         "/* a class of errors */\nstruct node { int x; };\n", "const char *s = \"namespace x {\";\n",
         "// template <typename T>\nint f(void);\n", "#include <string.h>\n[[gnu::unused]] static int x;\n",
         "int namespace_count; /* std::x */\n",
         # `namespace` as a C name: a struct tag, a member, a variable.
         "struct namespace {\n  int id;\n};\n", "union namespace { int a; };\n", "p->namespace = name;\n",
         "int namespace = 0;\n"]
    assert [detect_language(Path("a.h"), text) for text in cpp] == ["cpp"] * len(cpp)
    assert [detect_language(Path("a.h"), text) for text in c] == ["c"] * len(c)


def test_a_file_whose_suffix_another_language_shares_is_read_in_the_language_of_its_text(tmp_path):
    """A C++ header whose namespace has a nested name (C++17), an Objective-C header, a Qt Linguist translation
    (`.ts`, an XML document): each is read in its own language, or not at all where the snapshot reads none; the
    suffix's parser would stop at a syntax error and leave the file lexical."""
    files = {"archive.h": ("#pragma once\n#include <cstddef>\n\nnamespace calc::detail {\n"
                           "std::size_t pack_bound(std::size_t n);\n}  // namespace calc::detail\n", "cpp", "parsed"),
             "Widget.h": ("#import <Foundation/Foundation.h>\n\n@interface Widget : NSObject\n"
                          "@property (nonatomic, copy) NSString *title;\n- (NSString *)render;\n@end\n",
                          None, "file-level"),
             "app_it.ts": ('<?xml version="1.0" encoding="utf-8"?>\n<!DOCTYPE TS>\n<TS version="2.1" language="it_IT">'
                           "\n<context>\n    <name>MainWindow</name>\n</context>\n</TS>\n", None, "file-level")}
    for name, (text, language, status) in files.items():
        (tmp_path / name).write_text(text, encoding="utf-8")
        entry = snapshot.file_entry(tmp_path / name)
        assert (name, entry["language"], entry["status"]) == (name, language, status)
    assert detect_language(Path("a.h"), "namespace a::inline b {\nint f();\n}\n") == "cpp"
    # The markers count in code only, and TypeScript's own `<` is no XML document.
    assert detect_language(Path("a.h"), "// @interface, namespace a::b {\nconst char *s = \"@end\";\n") == "c"
    assert detect_language(Path("a.ts"), "const tags: Array<TS> = [];\n") == "typescript"


def test_every_file_is_read_in_its_language(built):
    for project in ("c", "cpp"):
        assert {rel: language for rel, language in built[project]["languages"].items() if rel in LANGUAGES[project]} \
            == dict.fromkeys(LANGUAGES[project], project)
        assert {rel: status for rel, status in built[project]["status"].items() if rel in LANGUAGES[project]} \
            == dict.fromkeys(LANGUAGES[project], "ast")


@pytest.mark.parametrize("project, table", [("c", C_DECLARATIONS), ("cpp", CPP_DECLARATIONS)])
def test_declarations(built, project, table):
    for rel, expected in table.items():
        wanted = {name: sorted(value if isinstance(value, list) else [value], key=lambda item: item[1:3])
                  for name, value in expected.items()}
        found = {name: sorted(items, key=lambda item: item[1:3]) for name, items in _declared(built[project], rel).items()}
        assert found == wanted, rel


@pytest.mark.parametrize("project", ["c", "cpp"])
def test_exports_leave_out_static_and_namespace_members(built, project):
    found = {rel: built[project]["exports"].get(rel, set()) for rel in LANGUAGES[project]}
    assert found == {rel: EXPORTS[rel] for rel in LANGUAGES[project]}


@pytest.mark.parametrize("project", ["c", "cpp"])
def test_includes_name_project_headers_and_leave_system_ones_external(built, project):
    for rel in LANGUAGES[project]:
        includes = {item["module"] for item in built[project]["imports"].get(rel, ()) if item["local"] == "*"}
        assert includes == set(INCLUDES[rel]), rel
        modules = built[project]["modules"].get(rel, {})
        assert {module: sorted(modules.get(module, [])) for module in includes} == INCLUDES[rel], rel


def test_every_file_stops_the_lookup_at_its_module_scope(built):
    """What the translation unit brings is not read, even in a file without an include (util.h, decoy.c): a
    header sees the names of the file that includes it."""
    for project in ("c", "cpp"):
        for rel in LANGUAGES[project]:
            assert built[project]["scopes"][rel]["module"].get("unresolved") is True, rel


@pytest.mark.parametrize("project, rel, key", _cases(CALLS, "c") + _cases(CALLS, "cpp"))
def test_call(built, project, rel, key):
    assert _outcome(built[project], _found(built[project], rel, "call", key)) == CALLS[rel][key]


@pytest.mark.parametrize("project, rel, key", _cases(READS, "c") + _cases(READS, "cpp"))
def test_read(built, project, rel, key):
    assert _outcome(built[project], _found(built[project], rel, "read", key)) == READS[rel][key]


@pytest.mark.parametrize("project", ["c", "cpp"])
def test_no_call_is_left_out_or_invented(built, project):
    """Every call the reader writes is one of the expected ones: casts, `sizeof` and member initializers are none."""
    for rel in LANGUAGES[project]:
        found = sorted(f"{r['span'][2]} {'.'.join(r['parts'])}" for r in built[project]["references"].get(rel, ())
                       if r["kind"] == "call")
        assert found == sorted(key.partition("#")[0] for key in CALLS[rel]), rel


def test_calls_record_their_caller(built):
    calls = {".".join(r["parts"]): r for r in built["c"]["references"]["util.c"] if r["kind"] == "call"}
    caller = built["c"]["declarations"][calls["add"]["caller"]] if calls["add"].get("caller") else None
    assert caller is not None and caller["qualified_name"] == "twice" and caller["span"][0] == 10
    lambda_call = next(r for r in built["cpp"]["references"]["main.cpp"] if r["parts"] == ["geo", "scale"])
    assert built["cpp"]["declarations"][lambda_call["caller"]]["name"] == "(lambda)"


def test_class_scopes_with_a_base_stop_the_lookup(built):
    scopes = {item["id"]: item for item in built["cpp"]["scopes"]["shapes.hpp"].values()}
    declarations = built["cpp"]["declarations"]
    blocked = {declarations[f"shapes.hpp::{scope['declaration']}"]["qualified_name"]: bool(scope.get("unresolved"))
               for scope in scopes.values() if scope["kind"] == "class"}
    assert blocked == {"geo.Shape": False, "geo.Circle": True, "geo.Square": True, "geo.Vec": False}


@pytest.mark.parametrize("project", ["c", "cpp"])
def test_outline_symbols(built, project):
    for rel, expected in SYMBOLS.items():
        if rel not in LANGUAGES[project]:
            continue
        found = {name: (item["kind"], item["start"], item["end"]) for name, item in built[project]["symbols"][rel].items()}
        assert found == expected, rel


def _semantic(source: str, language: str = "c") -> dict:
    result = get_adapter(language).parse(source, "a.c" if language == "c" else "a.cpp")
    assert result.semantic is not None, result.notes
    return result


def test_annotation_macros_do_not_hide_a_definition_or_a_class():
    source = ("#define ZEXPORT\nint ZEXPORT inflate(int strm) { return strm; }\n"
              "class LIB Node : public Base {\n  virtual bool Accept() const = 0;\n};\n")
    c = _semantic(source.split("class")[0])
    assert [(d["name"], d["name_span"][:2]) for d in c.semantic["declarations"] if d["kind"] == "function"] == \
        [("inflate", [2, 12])]
    cpp = _semantic("#define LIB\n" + "class" + source.split("class")[1], "cpp")
    assert [(d["qualified_name"], d["name_span"][:2]) for d in cpp.semantic["declarations"]
            if d["kind"] in ("class", "method")] == [("Node", [2, 10]), ("Node.Accept", [3, 15])]


def test_typedef_names_are_declared_types():
    result = _semantic("typedef unsigned char uch;\ntypedef struct { int x; } point;\n"
                       "typedef struct node { struct node *next; } node_t;\n")
    assert sorted((d["name"], d.get("lexical", True)) for d in result.semantic["declarations"] if d["kind"] == "class") \
        == [("node", False), ("node_t", True), ("point", True), ("uch", True)]
    assert sorted(c.name for c in result.classes) == ["node", "node_t", "point", "uch"]


def test_a_call_to_a_macro_of_the_file_is_dynamic():
    result = _semantic("#define CALL(f, x) f(x)\nstatic int one(int v) { return v; }\n"
                       "int two(void) { return CALL(one, 2) + one(1); }\n")
    calls = [(r["parts"], r.get("reason")) for r in result.semantic["references"] if r["kind"] == "call"]
    assert calls == [(["CALL"], "dynamic-callee"), (["one"], None)]


def test_a_call_through_a_pointer_names_the_pointer_and_stays_dynamic():
    source = "int run(int (*cb)(int), int v) { return cb(v) + (*cb)(v) + (cb)(v); }\n"
    calls = [(r["parts"], r.get("reason"), r["span"][1]) for r in _semantic(source).semantic["references"]
             if r["kind"] == "call"]
    assert calls == [(["cb"], None, source.index("cb(v)")), (["cb"], "dynamic-callee", source.index("*cb)(v)") + 1),
                     (["cb"], "dynamic-callee", source.index("(cb)(v)") + 1)]


def test_a_broken_file_keeps_its_outline_and_its_facts_around_the_error():
    """The facts outside the parser's ERROR nodes stay, the lines of each named unread (`semantic._around`)."""
    result = get_adapter("c").parse("int ok(void) { return 1; }\nint broken( { return; \n", "a.c")
    assert [f.name for f in result.functions][:1] == ["ok"]
    assert result.semantic["unread"] and any(note.startswith("syntax error:") for note in result.notes)



# ---------------------------------------------------------------------------------------------------------------
# Macros the grammar cannot read: each cause in `fixtures/clang-reader/macros`, expectations from the source.

MACROS = FIXTURES / "macros"
LINK = FIXTURES / "link"


def _sources(root: Path) -> dict:
    return {path.relative_to(root).as_posix(): path.read_text(encoding="utf-8")
            for path in sorted(root.rglob("*")) if path.is_file()}


def _contexts(root: Path) -> dict:
    """Each file's include context, as the snapshot hands it to the reader."""
    return snapshot.c_family_contexts({rel: text.encode("utf-8") for rel, text in _sources(root).items()})


def _whole(result) -> bool:
    """The reader read every line of the file: its facts, and none it could not read."""
    return result.semantic is not None and not result.semantic.get("unread")


def _parse(root: Path, rel: str, context: bool = True):
    text = (root / rel).read_text(encoding="utf-8")
    language = detect_language(Path(rel), text)
    return get_adapter(language).parse(text, str(root / rel), macros=_contexts(root)[rel] if context else None)


def test_a_macro_is_blanked_only_when_its_definitions_decorate_a_declaration():
    definitions = {"far_ptr": ["far", ""], "local": ["static"], "zextern": ["extern __declspec(dllexport)", "extern"],
                   "zlimit": ["15"], "word": ["unsigned"], "ROUND": [(("a",), "do { (a) %= zlimit; } while (0)")],
                   "noop": [""], "ptr": ["char *"],
                   "api": ["__attribute__((visibility(\"default\")))", ""], "conv": ["WINAPI", ""]}
    assert cfamily.decorating(definitions) == ({"far_ptr", "local", "zextern", "noop", "api", "conv"}, {"local"})


def test_blanking_keeps_every_position():
    for rel, text in _sources(MACROS).items():
        language = detect_language(Path(rel), text)
        before = text.encode("utf-8")
        after = cfamily.prepare(before, language, _contexts(MACROS)[rel])[0]
        assert len(after) == len(before) and [i for i, b in enumerate(after) if b == 10] == \
            [i for i, b in enumerate(before) if b == 10], rel


def test_each_cause_parses_whole_with_the_macros_of_its_headers():
    """An included header's annotation macro (`local`, `far_ptr`, `zextern`), the file's own (`api_local`), an
    includer's (`local` in tables.h, from crc.c), a comment in a continued `#define`, a null directive, the
    `__cplusplus` guards and a K&R definition. A statement split by `#ifdef` branches still breaks the grammar."""
    whole = {rel: _whole(_parse(MACROS, rel)) for rel in _sources(MACROS)}
    assert whole == {"checksum.c": True, "crc.c": True, "guard.hpp": True, "kr.c": True, "own.c": True,
                     "split.c": False, "tables.h": True, "zdefs.h": True}


def test_a_header_reads_with_the_macros_of_every_file_that_includes_it():
    """A header is read inside the translation units of the files that include it, directly or not: their macros
    reach it, for the names it uses. Includers that disagree give two definitions: the macro decorates nothing."""
    files = {"t.h": "local int g(void);\n", "inner.h": '#include "t.h"\nlocal int k(void);\n',
             "a.c": '#define local static\n#include "inner.h"\n', "b.c": '#include "inner.h"\n',
             "u.h": "local int h(void);\n", "c.c": '#define local 2\n#include "u.h"\n',
             "d.c": '#define local static\n#include "u.h"\n'}
    contexts = cfamily.include_contexts(files, lambda module, importer: module if module in files else None)
    assert contexts["t.h"] == contexts["inner.h"] == {"local": ["static"]}
    assert contexts["a.c"] == contexts["b.c"] == contexts["c.c"] == {}
    assert sorted(contexts["u.h"]["local"]) == ["2", "static"] and cfamily.decorating(contexts["u.h"])[0] == set()


def test_the_annotation_guess_is_left_out_when_the_include_context_is_known():
    """Without the include context an upper-case word between a return type and a name is taken for a macro.
    With it only the macros the sources define are blanked, so a type such as `BOOL` stays."""
    src = b"static BOOL set_pointer(HANDLE h);\nint ZEXPORT inflate(int v);\n"
    assert cfamily.prepare(src, "c")[0] == b"static      set_pointer(HANDLE h);\nint         inflate(int v);\n"
    assert cfamily.prepare(src, "c", {"ZEXPORT": [""]})[0] == \
        b"static BOOL set_pointer(HANDLE h);\nint         inflate(int v);\n"


def test_without_its_headers_a_file_using_their_macros_is_not_read_whole():
    result = _parse(MACROS, "checksum.c", context=False)
    assert not _whole(result) and any(note.startswith("syntax error:") for note in result.notes)


def _functions(result) -> dict:
    return {d["qualified_name"]: (d["name_span"][:2], d.get("linkage"), bool(d.get("contract")))
            for d in result.semantic["declarations"] if d["kind"] == "function"}


def test_a_macro_that_expands_to_static_keeps_the_function_internal():
    result = _parse(MACROS, "checksum.c")
    assert _functions(result) == {"fold": ([10, 10], "internal", False), "checksum": ([12, 4], "external", False)}
    assert [e["exported"] for e in result.semantic["exports"]] == ["checksum"]
    assert [f.name for f in result.functions] == ["fold", "checksum"]
    assert [f.visibility for f in result.functions] == ["private", "public"]
    assert [(r["parts"], r.get("reason")) for r in result.semantic["references"] if r["kind"] == "call"] == \
        [(["fold"], None), (["ROUND"], "dynamic-callee")]
    assert ("count", "binding") in {(d["name"], d["kind"]) for d in result.semantic["declarations"]}


def test_header_with_decorating_macros_and_cplusplus_guards():
    zdefs, guard = _parse(MACROS, "zdefs.h"), _parse(MACROS, "guard.hpp")
    assert _functions(zdefs) == {"checksum": ([22, 12], "external", True)}
    assert _functions(guard) == {"c_api": ([4, 4], "external", True), "geo.area": ([9, 20], None, True)}
    assert [e["exported"] for e in guard.semantic["exports"]] == ["c_api"]


def test_kr_definition_binds_its_parameters():
    result = _parse(MACROS, "kr.c")
    assert _functions(result) == {"add": ([1, 4], "external", False), "twice": ([8, 4], "external", False)}
    assert sorted(d["name"] for d in result.semantic["declarations"] if d["kind"] == "parameter") == ["a", "b", "v"]


@pytest.fixture(scope="module")
def macro_snapshot(tmp_path_factory):
    source = tmp_path_factory.mktemp("macros") / "macros"
    shutil.copytree(MACROS, source)
    return _built(source, source.parent / "manifest.sqlite")


def test_the_snapshot_reads_each_file_with_its_include_context(macro_snapshot):
    """checksum.c needs the macros of zdefs.h, tables.h those of crc.c: the snapshot hands both to the reader."""
    assert macro_snapshot["status"] == {"checksum.c": "ast", "crc.c": "ast", "guard.hpp": "ast", "kr.c": "ast",
                                        "own.c": "ast", "split.c": "partial", "tables.h": "ast", "zdefs.h": "ast"}
    assert _outcome(macro_snapshot, _found(macro_snapshot, "checksum.c", "call", "15 fold")) == "checksum.c:10"
    assert macro_snapshot["exports"]["checksum.c"] == {"checksum"}
    assert _outcome(macro_snapshot, _found(macro_snapshot, "own.c", "call", "5 helper")) == "own.c:3"
    assert _outcome(macro_snapshot, _found(macro_snapshot, "kr.c", "call", "8 add")) == "kr.c:1"
    assert macro_snapshot["exports"]["own.c"] == {"run"}


# ---------------------------------------------------------------------------------------------------------------
# A name from an included project header: `resolution.included_definition`, over the snapshot's tables.

def _rule(source: Path) -> dict:
    """`{file: {"LINE NAME": outcome}}` of every single name the snapshot answered with the include rule."""
    data = _built(source, source.parent / f"{source.name}.sqlite")
    out = {}
    for rel, references in data["references"].items():
        for item in references:
            if len(item["parts"]) != 1 or not (item.get("reason") or "").startswith("included-"):
                continue
            key = f"{item['span'][2]} {item['parts'][0]}"
            key = key if key not in out.setdefault(rel, {}) else f"{key}#2"
            out[rel][key] = _outcome(data, item)
    return {rel: keys for rel, keys in out.items() if keys}


@pytest.fixture(scope="module")
def ruled(tmp_path_factory):
    out = {}
    for root in (LINK, FIXTURES / "c", FIXTURES / "cpp", FIXTURES / "namespaces"):
        source = tmp_path_factory.mktemp(root.name) / root.name
        shutil.copytree(root, source)
        out[root.name] = _rule(source)
    return out


RULED = {
    "link": {"main.c": {"5 add": "math.c:3", "6 deep": "deep.c:1", "7 helper": "included-definition-ambiguous",
                        "8 quiet": "included-definition-missing", "9 hidden": UNDECLARED, "10 printf": UNDECLARED}},
    "c": {"main.c": {"4 LOG": UNDECLARED, "7 add": "util.c:6", "9 add": "util.c:6", "10 SQUARE": UNDECLARED,
                     "13 run_callback": "util.c:14", "14 strlen": UNDECLARED, "15 SQUARE": UNDECLARED,
                     "15 add": "util.c:6", "16 platform_init": "platform_win.c:3"},
          "util.c": {"12 printf": UNDECLARED, "17 fast_path": UNDECLARED},
          "platform_win.c": {"3 add": "util.c:6"}, "caller.c": {"3 twice": UNDECLARED}},
    # A member and a qualified call are no file-scope names: the rule does not apply. A function of the same
    # name in a namespace the file sees can be what the call reaches: no target.
    "cpp": {"main.cpp": {"17 c_helper": "shapes.cpp:27", "18 printf": UNDECLARED},
            "shapes.cpp": {"15 twice": NAMESPACED}},
    # Inside `namespace geo`, geo::area hides ::area. Outside it, geo::area and geo::size can still be reached
    # through the namespaces of the arguments' types, which a lexical reader does not know.
    "namespaces": {"main.cpp": {"5 area": NAMESPACED, "8 area": NAMESPACED, "9 size": NAMESPACED,
                                "10 square": "area.cpp:4"}},
}


@pytest.mark.parametrize("project", sorted(RULED))
def test_included_name_reaches_its_one_external_definition(ruled, project):
    assert ruled[project] == RULED[project]


# ---------------------------------------------------------------------------
# `fixtures/clang-reader/annotations`: the sources of `benchmarks/project-model/fixtures/sys-c-macro-annotations`,
# a C library in the declarator style of zlib (`ZEXPORT`, `ZEXTERN`, `FAR`, `local`, `OF((args))`, K&R
# definitions) and its C++ wrapper.
# ---------------------------------------------------------------------------

ANNOTATED = FIXTURES / "annotations"


def _declared_functions(result) -> list:
    """`(qualified name, name line, name column, linkage, prototype)` of every function, in source order."""
    return [(d["qualified_name"], *d["name_span"][:2], d.get("linkage"), bool(d.get("contract")))
            for d in result.semantic["declarations"] if d["kind"] == "function"]


def _calls(result) -> list:
    return [(".".join(r["parts"]), r["span"][0], r.get("reason")) for r in result.semantic["references"]
            if r["kind"] == "call"]


def test_a_header_with_extern_c_guards_stays_c_and_a_header_with_namespaces_is_cpp():
    assert {rel: detect_language(Path(rel), text) for rel, text in _sources(ANNOTATED).items()} == {
        "c/zmini.c": "c", "c/zutil.h": "c", "include/zmconf.h": "c", "include/zmini.h": "c",
        "cpp/checksum.cpp": "cpp", "cpp/checksum.hpp": "cpp", "cpp/detail.h": "cpp"}


def test_a_one_parameter_macro_that_expands_to_its_argument_or_to_no_parameters_wraps_a_prototype():
    """`#define OF(args) args`, and `__P(protos)` that is `protos` or `()` for compilers without prototypes."""
    definitions = cfamily.macro_definitions(_sources(ANNOTATED)["include/zmconf.h"])
    assert cfamily.decorating(definitions) == ({"ZMCONF_H", "ZEXPORT", "ZEXTERN", "FAR", "local"}, {"local"})
    assert cfamily.wrappers(definitions) == {"OF"}
    assert cfamily.wrappers(cfamily.macro_definitions(
        "#ifdef __STDC__\n#define __P(protos) protos\n#else\n#define __P(protos) ()\n#endif\n"
        "#define TWICE(x) ((x) * 2)\n#define FIRST(a, b) a\n#define SAME(x) x\n#define SAME(x) (x)\n")) == {"__P"}


def test_a_wrapper_call_keeps_its_argument_and_every_position():
    src = (b"int f OF((int a,\n           int b));\n#define OF(args) args\n"
           b"int g OF((const char *s /* ) */, char c = ')'));\nint h(int OF_x) { return OF_x; }\n")
    macros = cfamily.macro_definitions("#define OF(args) args\n")
    out = cfamily.prepare(src, "c", macros)[0]
    assert out == (b"int f    (int a,\n           int b) ;\n#define OF(args) args\n"
                   b"int g    (const char *s /* ) */, char c = ')') ;\nint h(int OF_x) { return OF_x; }\n")


def test_every_annotated_file_parses_whole_with_the_macros_of_its_headers():
    assert {rel: _whole(_parse(ANNOTATED, rel)) for rel in _sources(ANNOTATED)} == dict.fromkeys(
        _sources(ANNOTATED), True)
    # Without its headers, what uses their macros breaks: the reader alone cannot know `local` or `ZEXPORT`.
    assert {rel for rel in _sources(ANNOTATED) if not _whole(_parse(ANNOTATED, rel, context=False))} == {
        "c/zmini.c", "include/zmini.h"}


def test_annotated_prototypes_and_kr_definitions_declare_their_functions():
    assert _declared_functions(_parse(ANNOTATED, "include/zmini.h")) == [
        ("zm_adler", 13, 22, "external", True), ("zm_version", 14, 29, "external", True)]
    zmini = _parse(ANNOTATED, "c/zmini.c")
    assert _declared_functions(zmini) == [
        ("mod_base", 4, 16, "internal", True), ("mod_base", 6, 16, "internal", False),
        ("zm_adler", 12, 14, "external", False), ("zm_version", 27, 21, "external", False)]
    assert [(f.name, f.visibility) for f in zmini.functions] == [
        ("mod_base", "private"), ("zm_adler", "public"), ("zm_version", "public")]
    assert [e["exported"] for e in zmini.semantic["exports"]] == ["zm_adler", "zm_version"]
    assert {"x", "adler", "buf", "len"} <= {d["name"] for d in zmini.semantic["declarations"]
                                           if d["kind"] == "parameter"}
    # A wrapped parameter list is no call, and neither is a macro used as a value.
    assert _calls(zmini) == [("mod_base", 21, None), ("mod_base", 22, None)]
    assert _calls(_parse(ANNOTATED, "include/zmini.h")) == []


def test_the_cpp_wrapper_declares_its_namespaced_functions_and_calls_the_c_api():
    assert _declared_functions(_parse(ANNOTATED, "cpp/detail.h")) == [("zminipp.detail.data_of", 9, 19, None, False)]
    assert _declared_functions(_parse(ANNOTATED, "cpp/checksum.hpp")) == [("zminipp.adler32", 9, 14, None, True)]
    checksum = _parse(ANNOTATED, "cpp/checksum.cpp")
    assert _declared_functions(checksum) == [("zminipp.adler32", 8, 14, None, False)]
    # Casts are conversions, not calls.
    assert _calls(checksum) == [("detail.data_of", 9, None), ("zm_adler", 10, None), ("bytes.size", 10, None)]
    # Without the build's include paths an angle include is never taken for a project header: `<zmini.h>` is
    # include/zmini.h only because CMake puts include/ on the path.
    assert [(i.module, i.is_internal) for i in checksum.imports] == [
        ("checksum.hpp", True), ("detail.h", True), ("<zmini.h>", False)]


@pytest.fixture(scope="module")
def annotated_snapshot(tmp_path_factory):
    source = tmp_path_factory.mktemp("annotations") / "annotations"
    shutil.copytree(ANNOTATED, source)
    return _built(source, source.parent / "manifest.sqlite")


def test_the_snapshot_reads_every_annotated_file(annotated_snapshot):
    assert set(annotated_snapshot["status"].values()) == {"ast"}
    assert _outcome(annotated_snapshot, _found(annotated_snapshot, "c/zmini.c", "call", "21 mod_base")) == \
        "c/zmini.c:6"
    # `<zmini.h>` is an angle include, never a project header without the build's include paths: the C API the
    # wrapper calls stays without a target.
    assert _outcome(annotated_snapshot, _found(annotated_snapshot, "cpp/checksum.cpp", "call", "10 zm_adler")) == \
        UNDECLARED


def test_a_changed_header_reparses_the_files_whose_context_it_changes(tmp_path):
    """The reuse key of a C or C++ file holds its include context: a header that changes a macro the file uses
    reparses the file, the others are reused."""
    source = tmp_path / "macros"
    shutil.copytree(MACROS, source)
    first = snapshot.write_snapshot(source, tmp_path / "first.sqlite")
    header = source / "zdefs.h"
    header.write_bytes(header.read_bytes().replace(b"#define local static", b"#define local"))
    with open_snapshot(tmp_path / "first.sqlite") as previous:
        second = snapshot.write_snapshot(source, tmp_path / "second.sqlite", previous=previous)
    # zdefs.h changed; checksum.c, crc.c and tables.h use its `local`; split.c does not parse, so it is never kept.
    assert first["metrics"]["cache_hits"] == 0 and second["metrics"]["cache_hits"] == 3
    db = sqlite3.connect(tmp_path / "second.sqlite")
    try:
        exported = {name for (name,) in db.execute("SELECT name FROM sem_exports WHERE file='checksum.c'")}
    finally:
        db.close()
    assert exported == {"checksum", "fold"}  # `local` no longer makes fold static


def test_the_index_and_the_store_answer_the_rule_alike(tmp_path):
    """`semantic_index` asks the same rule as the snapshot's store, over the manifest it builds."""
    import semantic_index

    for root in (LINK, FIXTURES / "namespaces"):
        source = tmp_path / root.name
        shutil.copytree(root, source)
        index = semantic_index.build_semantic_index(read_manifest(source))
        found = {}
        for item in index["references"]:
            if len(item["parts"]) == 1 and (item.get("reason") or "").startswith("included-"):
                target = index["declarations"].get(item["target_id"]) if item["target_id"] else None
                outcome = f"{target['file']}:{target['name_span'][0]}" if target else item["reason"]
                found.setdefault(item["file"], {})[f"{item['span'][2]} {item['parts'][0]}"] = outcome
        assert found == RULED[root.name], root.name


# zlib at the commit the corpus pins (mix-real-zlib), and the C files no build for Linux compiles (D-136): the
# examples, contrib/infback9, minizip's iowin32.c (Windows only) and contrib/testzlib (Visual Studio only).
ZLIB = ("https://github.com/madler/zlib.git", "51b7f2abdade71cd9bb0e7a373ef2610ec6f9daf")
UNBUILT = ("examples", "contrib/infback9", "contrib/minizip/iowin32.c", "contrib/testzlib")


@pytest.mark.skipif(not os.environ.get("MODAL_TASK_ID"), reason="a real proof on Modal (tests/modal_pytest.py)")
def test_on_modal_the_reference_sites_of_zlib_s_files_no_build_compiles(tmp_path):
    """The C reference sites (calls and reads) the snapshot of zlib gives each file no build compiles: the
    `no-document` holes a run counts there, as the C indexer indexes only what a build compiles. The pre-map's
    readers alone give minizip's Autotools unit with iowin32.c and mztools.c among its sources."""
    import premap
    source = tmp_path / "zlib"
    source.mkdir()
    for command in (["git", "init", "-q"], ["git", "remote", "add", "origin", ZLIB[0]],
                    ["git", "fetch", "-q", "--depth", "1", "origin", ZLIB[1]],
                    ["git", "-c", "core.hooksPath=/dev/null", "checkout", "-q", "FETCH_HEAD"]):
        subprocess.run(command, cwd=source, check=True, timeout=600)
    manifest = tmp_path / "snapshot/manifest.sqlite"
    snapshot.write_snapshot(source, manifest)
    connection = sqlite3.connect(manifest)
    sites = dict(connection.execute(
        "SELECT r.file, COUNT(*) FROM sem_references r JOIN sem_coverage c ON c.file = r.file "
        "WHERE r.kind IN ('call', 'read') AND c.language = 'c' GROUP BY r.file").fetchall())
    connection.close()
    unbuilt = {place: sum(count for rel, count in sites.items() if rel == place or rel.startswith(place + "/"))
               for place in UNBUILT}
    print("SITES", sum(sites.values()), json.dumps(unbuilt))
    assert unbuilt == {"examples": 3446, "contrib/infback9": 633, "contrib/minizip/iowin32.c": 352,
                       "contrib/testzlib": 12}  # 4,443, the `no-document` holes of the run on f992db560
    # what a build compiles since the conferma: test/infcover.c (Makefile's `cover`), mztools.c (Autotools)
    assert (sites["test/infcover.c"], sites["contrib/minizip/mztools.c"]) == (785, 251)
    [unit] = [unit for unit in premap.ensure(manifest).get("units", []) if unit["root"] == "contrib/minizip"]
    assert (unit["kind"], unit["name"]) == ("autotools-project", "minizip")
    assert {"contrib/minizip/iowin32.c", "contrib/minizip/mztools.c"} <= set(unit["config"]["sources"])
