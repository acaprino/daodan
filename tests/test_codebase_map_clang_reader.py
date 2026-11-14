"""The C and C++ source reader: what the snapshot holds for the fixtures in `fixtures/clang-reader/{c,cpp}`.

Every expectation below was written by reading the fixture's source, before the reader existed. A reference is
named `"LINE NAME"` (its name parts joined by `.`, `#2` for the second one of that name on the line) and ends at
a declaration (`FILE:LINE` of the declaration's name) or at the reason it stays unresolved.

    python -B -m pytest -q -p no:cacheprovider tests/test_codebase_map_clang_reader.py
"""
from __future__ import annotations

import re
import shutil
import sqlite3
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "plugins/codebase-map/skills/map/scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import resolution  # noqa: E402
import snapshot  # noqa: E402
from languages import SUPPORTED_EXTENSIONS, cfamily, detect_language, get_adapter  # noqa: E402
from snapshot_store import _unpack, open_snapshot  # noqa: E402

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
CALLS = {
    "util.c": {"8 twice": "util.c:10", "10 add": "util.c:6", "12 printf": OUTSIDE, "15 h.on_event": "unknown-receiver",
               "17 fast_path": OUTSIDE, "19 log_message": "util.c:12"},
    "main.c": {"4 LOG": OUTSIDE, "9 add": OUTSIDE, "10 SQUARE": OUTSIDE, "11 h.compute": "unknown-receiver",
               "12 fp": "dynamic-callee", "13 run_callback": OUTSIDE, "14 strlen": OUTSIDE, "15 SQUARE": OUTSIDE,
               "15 add": OUTSIDE, "16 platform_init": OUTSIDE},
    "platform_win.c": {"3 add": OUTSIDE},
    "decoy.c": {"3 twice": "decoy.c:1", "3 twice#2": "decoy.c:1"},
    "caller.c": {"3 twice": OUTSIDE},  # neither `static int twice` of util.c nor that of decoy.c
    "util.h": {},
    "shapes.hpp": {},
    "shapes.cpp": {"15 twice": OUTSIDE, "21 shape.area": "unknown-receiver"},
    "main.cpp": {"8 geo.Square": OUTSIDE, "10 geo.scale": OUTSIDE, "13 geo.total": OUTSIDE,
                 "13 shape.area": "unknown-receiver", "13 circle.area": "unknown-receiver",
                 "14 twice": "import-target-missing-or-ambiguous", "14 geo.scale": OUTSIDE,
                 "14 doubled": "non-callable-binding", "15 std.printf": OUTSIDE, "15 shape.name": "unknown-receiver",
                 "16 shapes.push_back": "unknown-receiver", "17 c_helper": OUTSIDE, "18 printf": OUTSIDE},
}
# A variable assigned after its declaration has two binding sites, so a read of it is ambiguous, as in every
# language (`n += ...` in main.c, `sum += ...` in shapes.cpp).
READS = {
    "util.c": {"6 a#2": "non-callable-binding", "10 v#2": "non-callable-binding", "15 value": "non-callable-binding"},
    "main.c": {"7 on_event_impl": "main.c:4", "7 add": OUTSIDE, "8 on_event_impl": "main.c:4",
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
           "template <typename T> T twice(T v);\n", "using namespace std;\n"]
    c = ["#ifdef __cplusplus\nextern \"C\" {\n#endif\nint f(void);\n#ifdef __cplusplus\n}\n#endif\n",
         "/* a class of errors */\nstruct node { int x; };\n", "const char *s = \"namespace x {\";\n",
         "// template <typename T>\nint f(void);\n"]
    assert [detect_language(Path("a.h"), text) for text in cpp] == ["cpp"] * len(cpp)
    assert [detect_language(Path("a.h"), text) for text in c] == ["c"] * len(c)


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


def test_a_broken_file_keeps_its_outline_and_gives_no_semantic_facts():
    result = get_adapter("c").parse("int ok(void) { return 1; }\nint broken( { return; \n", "a.c")
    assert [f.name for f in result.functions][:1] == ["ok"]
    assert result.semantic is None and any(note.startswith("syntax error:") for note in result.notes)



# ---------------------------------------------------------------------------------------------------------------
# Macros the grammar cannot read: each cause in `fixtures/clang-reader/macros`, expectations from the source.

MACROS = FIXTURES / "macros"
LINK = FIXTURES / "link"


def _sources(root: Path) -> dict:
    return {path.relative_to(root).as_posix(): path.read_text(encoding="utf-8")
            for path in sorted(root.rglob("*")) if path.is_file()}


def _contexts(root: Path) -> dict:
    """The macros of each file's included project headers, as the snapshot would hand them to the reader."""
    files = _sources(root)
    known = snapshot._by_basename(files)
    return cfamily.include_contexts(files, lambda module, importer: snapshot.resolve_module(module, importer, known))


def _parse(root: Path, rel: str, context: bool = True):
    text = (root / rel).read_text(encoding="utf-8")
    language = detect_language(Path(rel), text)
    return get_adapter(language).parse(text, str(root / rel), macros=_contexts(root)[rel] if context else None)


def test_a_macro_is_blanked_only_when_its_definitions_decorate_a_declaration():
    definitions = {"far_ptr": ["far", ""], "local": ["static"], "zextern": ["extern __declspec(dllexport)", "extern"],
                   "zlimit": ["15"], "word": ["unsigned"], "ROUND": [None], "noop": [""], "ptr": ["char *"],
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
    """An included header's annotation macro (`local`, `far_ptr`, `zextern`), the file's own (`api_local`), a
    comment in a continued `#define`, a null directive, the `__cplusplus` guards and a K&R definition. A statement
    split by `#ifdef` branches still breaks the grammar."""
    whole = {rel: _parse(MACROS, rel).semantic is not None for rel in _sources(MACROS)}
    assert whole == {"checksum.c": True, "guard.hpp": True, "kr.c": True, "own.c": True, "split.c": False,
                     "zdefs.h": True}


def test_without_its_headers_a_file_using_their_macros_is_not_read():
    result = _parse(MACROS, "checksum.c", context=False)
    assert result.semantic is None and any(note.startswith("syntax error:") for note in result.notes)


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


def test_the_snapshot_reads_what_needs_no_other_file(macro_snapshot):
    """checksum.c needs the macros of zdefs.h, which the snapshot does not hand the reader yet."""
    assert macro_snapshot["status"] == {"checksum.c": "lexical", "guard.hpp": "ast", "kr.c": "ast", "own.c": "ast",
                                        "split.c": "lexical", "zdefs.h": "ast"}
    assert _outcome(macro_snapshot, _found(macro_snapshot, "own.c", "call", "5 helper")) == "own.c:3"
    assert _outcome(macro_snapshot, _found(macro_snapshot, "kr.c", "call", "8 add")) == "kr.c:1"
    assert macro_snapshot["exports"]["own.c"] == {"run"}


# ---------------------------------------------------------------------------------------------------------------
# A name from an included project header: `resolution.included_definition`, over the snapshot's tables.

class TableLookup:
    """The lookups the rule asks, answered from a snapshot's tables as `semantic_store._Resolver` would."""

    def __init__(self, db):
        self.db = db

    def language(self, rel):
        row = self.db.execute("SELECT language FROM sem_coverage WHERE file=?", (rel,)).fetchone()
        return row[0] if row else None

    def scope_record(self, rel, scope_id):
        row = self.db.execute("SELECT payload FROM sem_scopes WHERE file=? AND id=?", (rel, scope_id)).fetchone()
        return _unpack(row[0]) if row else None

    def bindings_named(self, rel, scope_id, name):
        return [(kind, identity if kind == "declaration" else _unpack(blob)) for kind, identity, blob in self.db.execute(
            "SELECT kind, identity, payload FROM sem_bindings WHERE file=? AND scope=? AND name=? ORDER BY rowid",
            (rel, scope_id, name))]

    def targets(self, rel, module):
        return [row[0] for row in self.db.execute(
            "SELECT target FROM sem_modules WHERE file=? AND module=? ORDER BY target", (rel, module))]

    def declarations_named(self, name):
        return [_unpack(row[0]) for row in self.db.execute(
            "SELECT payload FROM sem_declarations WHERE name=? AND kind='function' ORDER BY id", (name,))]


def _rule(source: Path) -> dict:
    """`{file: {"LINE NAME": outcome}}` of the rule on every unresolved reference it applies to."""
    manifest = source.parent / f"{source.name}.sqlite"
    snapshot.write_snapshot(source, manifest)
    db = sqlite3.connect(manifest)
    try:
        lookup, out, rows = TableLookup(db), {}, []
        for rel, l1, blob in db.execute("SELECT file, l1, payload FROM sem_references WHERE resolution='unresolved' "
                                        "ORDER BY file, l0, c0"):
            rows.append((rel, l1, _unpack(blob)))
        for rel, line, item in rows:
            # Where the call site in both owners asks the rule: the lexical walk stopped at a blocked scope.
            if len(item["parts"]) != 1 or item.get("reason") != "scope-unresolved":
                continue
            identity, reason = resolution.included_definition(lookup, rel, item["scope"], item["parts"][0])
            if reason is None:
                continue
            if identity is not None:
                found = lookup.declarations_named(item["parts"][0])
                target = next(d for d in found if d["id"] == identity)
                reason = f"{target['file']}:{target['name_span'][0]}"
            key = f"{line} {item['parts'][0]}"
            key = key if key not in out.setdefault(rel, {}) else f"{key}#2"
            out[rel][key] = reason
    finally:
        db.close()
    return out


@pytest.fixture(scope="module")
def ruled(tmp_path_factory):
    out = {}
    for root in (LINK, FIXTURES / "c", FIXTURES / "cpp"):
        source = tmp_path_factory.mktemp(root.name) / root.name
        shutil.copytree(root, source)
        out[root.name] = _rule(source)
    return out


UNDECLARED = "included-name-undeclared"
RULED = {
    "link": {"main.c": {"5 add": "math.c:3", "6 deep": "deep.c:1", "7 helper": "included-definition-ambiguous",
                        "8 quiet": "included-definition-missing", "9 hidden": UNDECLARED, "10 printf": UNDECLARED}},
    "c": {"main.c": {"4 LOG": UNDECLARED, "7 add": "util.c:6", "9 add": "util.c:6", "10 SQUARE": UNDECLARED,
                     "13 run_callback": "util.c:14", "14 strlen": UNDECLARED, "15 SQUARE": UNDECLARED,
                     "15 add": "util.c:6", "16 platform_init": "platform_win.c:3"},
          "util.c": {"12 printf": UNDECLARED, "17 fast_path": UNDECLARED},
          "platform_win.c": {"3 add": "util.c:6"}, "caller.c": {"3 twice": UNDECLARED}},
    # A name in a namespace, a member and a qualified call are no file-scope names: the rule does not apply.
    "cpp": {"main.cpp": {"17 c_helper": "shapes.cpp:27", "18 printf": UNDECLARED},
            "shapes.cpp": {"15 twice": UNDECLARED}},
}


@pytest.mark.parametrize("project", sorted(RULED))
def test_included_name_reaches_its_one_external_definition(ruled, project):
    assert ruled[project] == RULED[project]
