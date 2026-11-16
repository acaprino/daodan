"""scip-clang for C and C++: how it runs, and what its index leaves to the reader.

`index` takes the pre-map's units and workspaces as they are and discovers no unit itself: each `cmake-target`
is configured from the root of the CMake workspace holding it, or from its own. A configure runs the project's
CMake code, so it runs only in a container (`container.run_in_container`), in one phase with no network, over a
copy of the project: `clang_run.py` there configures each root (a fetched dependency is never downloaded: a unit
that needs one to configure is not indexed, `unavailable` with what CMake recorded and its own output, as is one
whose configure reads a submodule the pre-map finds not checked out) and runs scip-clang over the compilation
database. CMake, scip-clang and that script are what the copy carries under
`TOOLS`, CMake and scip-clang downloaded once by Daodan into the shared directory and checked by sha256. A CMake
minimum the pre-map states above `CMAKE` (`toolchains`) is installed at that version by mise in a preparation
before it, the only phase with a network, which reaches mise's hosts only (`preparation.toolchains`); what it
could not install is a gap and the configure runs with `CMAKE`. A root that declares vcpkg or Conan is restored
in that preparation, with the registries and the manager's hosts open and a CMake on the path, as the pre-map's
configure of it is (`restores`): the configure reads the initial cache the restore writes, which names the
manager's toolchain file; a restore that fails is a `restore_failed` gap. The image
(`IMAGE`) gives gcc and g++ with their headers, which scip-clang needs to read the system includes, glibc 2.39
(scip-clang v0.4.1 needs 2.38), dpkg, whose file lists name the package of each system header, and python3.

The other builds give the database from their own run (`builds`), the ways scip-clang's README names: Meson's
setup, whose Ninja backend writes it; the project's make under Bear, with the targets the pre-map states; a Go
module's cgo packages built by the go command under Bear; Bazel's compile actions, from `bazel aquery` (what
hedron's extractor reads), run in the preparation with Bazel's hosts open since it fetches what the analysis reads.
Meson, make and the go build run the project's code: in the execution, with no network; the preparation downloads
the modules a cgo build requires. Bear is Ubuntu's package (`BEAR`); a Bazel the project states and a Go minimum
above the pin are installed by mise in the preparation (`wanted`). Each unit states the build that gave its
commands; a build that writes no database is a gap with the tool's own output; MSBuild gives none (`unbuilt`).

Symbols carry no file: a function declared in a header and defined in a source file is one symbol, defined at
its body; the declaration is a reference. Two `static` functions of one name in two files are one symbol too.
scip-clang writes what a macro expands to at the expansion: the call `SQUARE(n)` references the macro and the
function its body calls, at the same range, so macros need no hop; what its arguments name sits there too, and
`prepare` moves it back to the argument (`macro_arguments`).

`prepare(index, snapshot)` fills in place what the index leaves out, before anything reads it: each
occurrence once (a file compiled by several translation units comes as several documents, which the shared
reader appends), columns in UTF-8 bytes (no position encoding is written, and the shared reader would take
UTF-16) and each function and class definition's enclosing range, the body the snapshot declares, so edges
start at the function that holds them rather than at the file. It keeps the snapshot's declarations of the
indexed files on the index (`index.declarations`) for `hops`.

`hops` states two things the index leaves implicit: a function the index defines nowhere leads to its
prototype in the project (`declaration`); in C++, a variable declared `auto` with a lambda leads to that
lambda (`lambda`, the closure type is its own). A call through a function pointer, a struct field or a
parameter ends on that value: nothing is guessed. `same_range` keeps the shared rule from reading a variable
defined where a constructor or a macro is referenced as an alias: only a using-declaration aliases at a shared
range. `classify` names namespaces and the package of an external symbol. `refine` marks an edge `uncertain`
when its symbol has bodies at several places, each place a candidate. `unanswered` names the cause of a site in a branch of
`#if` where the index has no occurrence at all: the build's configuration does not compile it (`INACTIVE`).
"""
from __future__ import annotations

import collections
import json
import posixpath
import re
import shlex
import shutil
import tarfile
import time
from pathlib import Path

import code_graph
import preparation

VERSION = "v0.4.1"  # github.com/sourcegraph/scip-clang, released 2026-10-22, LLVM 21
URL = f"https://github.com/sourcegraph/scip-clang/releases/download/{VERSION}/scip-clang-x86_64-linux"
SHA256 = "a434d26a079fd80e1996ba79276cb1ef86b2b2ad28b13e24386285db32c59046"  # the release asset's digest
# The builtin headers of the clang scip-clang VERSION is built on (its Version.h's LLVM commit is 21.1.8): the
# folder lib/Headers of clang's release source (Apache-2.0 WITH LLVM-exception), which clang installs as its
# resource folder's include (`clang_headers`). scip-clang gives a GCC command, as clang's resource folder, GCC's
# install folder, whose headers call builtins clang lacks: those commands read these instead (`clang_run.py`).
CLANG_HEADERS = ("21.1.8",
                 "https://github.com/llvm/llvm-project/releases/download/llvmorg-21.1.8/clang-21.1.8.src.tar.xz",
                 "6090e3f23720d003cdd84483a47d0eec6d01adbb5e0c714ac0c8b58de546aa62")
IMAGE = "buildpack-deps:noble@sha256:890e8b5c0040e1deff5cc7dc7b4414e67069f79e3301afc4ec5bd49d64ef13e5"
CMAKE = ("3.28.3", "https://github.com/Kitware/CMake/releases/download/v3.28.3/cmake-3.28.3-linux-x86_64.tar.gz",
         "804d231460ab3c8b556a42d2660af4ac7a0e21c98a7f8ee3318a74b4a9a187a6")  # Ubuntu 24.04's own CMake
TOOLS = "/daodan/state/clang"  # where the copy carries the tools (clang_run.py reads them there); under the
# operation's state, which a preparation keeps for the run
OUT = "/tmp/daodan-clang/out"
# What a restore builds a dependency with, as the pre-map's preparation has a CMake on the path: the pin, where
# `preparation.PATH` finds it (mise's, when it installs one, comes first).
CMAKE_ON_PATH = (f"{{ tar -xzf {TOOLS}/cmake.tar.gz -C {preparation.T}"
                 f" && mv {preparation.T}/cmake-{CMAKE[0]}-linux-x86_64 {preparation.T}/cmake ; }} >&2"
                 f" || echo 'DAODAN-MISSING cmake@{CMAKE[0]}' >&2")
MIN_FREE = 2 * 2**30  # the container's memory
PIDS = 1024
CMAKE_UNIT = "cmake-target"
OTHER_BUILDS = {"meson-target": "meson", "make-target": "make", "bazel-target": "bazel",
                "autotools-project": "autotools", "msbuild-project": "MSBuild"}  # the native builds beside CMake, which the dynamic step does not run
BUILDS = {"meson-target": "meson", "make-target": "make", "bazel-target": "bazel",
          "autotools-project": "autotools", "go-module": "go"}  # the builds beside CMake that give a unit's compilation database (`clang_run.py`)
NO_UNIT = "no C or C++ unit in the pre-map: no build of the project compiles C or C++"
# Bear 3.1.3 (GPL-3.0-or-later), for Make and cgo: Bear ships no binaries and names the distributions' packages
# first (its INSTALL.md); these are Ubuntu 24.04's, the image's distribution, from the release pocket, with the
# libraries Bear needs that the image lacks. dpkg installs them in the execution.
BEAR = [(f"https://archive.ubuntu.com/ubuntu/pool/{path}", digest) for path, digest in (
    ("universe/b/bear/bear_3.1.3-1build4_amd64.deb",
     "3ff4fed98a4328a02993adf2d4ebde25685bb28ff29c78791fe4fbe9023ec6f0"),
    ("universe/b/bear/libear_3.1.3-1build4_amd64.deb",
     "b011fd461189bc30340196bdaf6c2f5835057d952e9b1ca99d292c88cb7de1a0"),
    ("main/a/abseil/libabsl20220623t64_20220623.1-3.1ubuntu3_amd64.deb",
     "eafc5f26ba910468a6d5d5f154ed8fcf4beed2d5bc45619907ea9f517cdaf401"),
    ("main/c/c-ares/libcares2_1.27.0-1.0ubuntu1_amd64.deb",
     "f84475f79e5b95c4caf98a7aef781bada3de44e9db05438b45b231da8fc7fc04"),
    ("universe/f/fmtlib/libfmt9_9.1.0+ds1-2_amd64.deb",
     "0a9dd337aea7ae59aba44994a92dd2780365b534a714518477c4e906f0efd297"),
    ("universe/g/grpc/libgrpc++1.51t64_1.51.1-4.1build5_amd64.deb",
     "7f0b9e0498bd74bd4ebb40a1d972d66a3652ecae4cbc9d6da32627613d453c83"),
    ("universe/g/grpc/libgrpc29t64_1.51.1-4.1build5_amd64.deb",
     "afd30f8d573a88dd74d5b2439cfade615d1c1829fd9fa7aa66ff90a2091be341"),
    ("main/p/protobuf/libprotobuf32t64_3.21.12-8.2build1_amd64.deb",
     "2e6875c5467e4d4e823886c91caccfa972ad7b4166531a3a48ebf0561850391a"),
    ("main/p/protobuf/libprotoc32t64_3.21.12-8.2build1_amd64.deb",
     "a2594bf74e2ba5b15347e37084a66908376d0e7c87d439f548aad9d85121d80f"),
    ("main/r/re2/libre2-10_20230301-3build1_amd64.deb",
     "4ce429c1254f57c96feb80536fe4418ea326603fa797d8311a50f946273fd29b"),
    ("universe/s/spdlog/libspdlog1.12_1.12.0+ds-2build1_amd64.deb",
     "e69e315e1596b6cf97a714ae797e55d42765664a739a0b30beac35164a4edaff"))]
C_SOURCES = {".c"}
CPP_SOURCES = {".cc", ".cpp", ".cxx", ".c++"}
CALLABLES = ("function", "method", "class")


# ---------------------------------------------------------------------------------------------------------
# What the index leaves to the reader


def dedupe(index) -> int:
    """Keep each occurrence of a document once, and rebuild the lookups; returns how many it dropped."""
    dropped = 0
    for occurrences in index.documents.values():
        unique = list(dict.fromkeys(occurrences))
        dropped += len(occurrences) - len(unique)
        occurrences[:] = unique
    index.at.clear()
    index.defs.clear()
    for rel, occurrences in index.documents.items():
        for item in occurrences:
            index.at[(rel, item.line, item.start)].append(item)
            if item.definition:
                index.defs[item.key].append((rel, item))
    return dropped


def utf8_columns(index) -> int:
    """scip-clang's columns are UTF-8 bytes, whatever the document states: every document is read so."""
    for rel in index.documents:
        index.units[rel] = "utf-8"
    return len(index.documents)


def _declarations(index, snapshot) -> dict:
    """`{checkout rel: [(kind, (l0, c0, l1, c1), payload)]}`: the snapshot's callables in the indexed files."""
    from snapshot_store import _unpack
    out = collections.defaultdict(list)
    for rel, kind, l0, c0, l1, c1, blob in snapshot.connection.execute(
            "SELECT file, kind, l0, c0, l1, c1, payload FROM sem_declarations WHERE kind IN (?,?,?) "
            "ORDER BY file, l0, c0", CALLABLES):
        checkout = snapshot.checkout.get(rel)
        if checkout in index.documents:
            out[checkout].append((kind, (l0, c0, l1, c1), _unpack(blob) or {}))
    return dict(out)


def enclose(index) -> int:
    """Give each definition of a function or class the range of the body the snapshot declares at its name.
    Returns how many it set."""
    done = 0
    for rel, declared in getattr(index, "declarations", {}).items():
        spans = {}
        for _kind, (l0, c0, l1, c1), payload in declared:
            if payload.get("contract"):  # a prototype: no body
                continue
            body = (l0, index.from_bytes(rel, l0, c0), l1, index.from_bytes(rel, l1, c1))
            for name in [payload.get("name_span"), *payload.get("signature_spans", ())]:
                if name and None not in body:
                    spans[(name[0], index.from_bytes(rel, name[0], name[1]))] = body
        occurrences = index.documents[rel]
        for i, item in enumerate(occurrences):
            span = spans.get((item.line, item.start)) if item.definition and item.enclosing is None else None
            if span:
                occurrences[i] = item._replace(enclosing=span)
                done += 1
    if done:  # the lookups hold the occurrences themselves
        dedupe(index)
    return done


MACRO = re.compile(r"`[^`]*:\d+:\d+`!$")  # a macro's symbol: scip-clang names it by where it is defined
IDENTIFIER = re.compile(rb"[A-Za-z_]\w*")
LITERAL = re.compile(rb'"(?:\\.|[^"\\])*"' rb"|'(?:\\.|[^'\\])*'|//.*|/\*.*?\*/")  # blanked: no names there


def _arguments(lines: list[bytes], line: int, end: int) -> list[tuple[int, int, bytes]]:
    """`(line, byte column, name)` of each identifier in the arguments of a macro invoked at `line`, its name ending
    at byte `end`: the parenthesized list after it, across lines; none without one."""
    row, column = line - 1, end
    while row < len(lines) and not lines[row][column:].strip():
        row, column = row + 1, 0
    if row >= len(lines):
        return []
    column += len(lines[row][column:]) - len(lines[row][column:].lstrip())
    if lines[row][column:column + 1] != b"(":
        return []
    depth, out = 0, []
    for row in range(row, min(len(lines), row + 200)):
        text = LITERAL.sub(lambda found: b" " * len(found.group()), lines[row])
        while column < len(text):
            byte = text[column:column + 1]
            word = IDENTIFIER.match(text, column) if depth and (column == 0 or not (
                text[column - 1:column].isalnum() or text[column - 1:column] == b"_")) else None
            if word:
                out.append((row + 1, column, word.group()))
                column = word.end()
                continue
            depth += byte == b"("
            depth -= byte == b")"
            if depth == 0:
                return out
            column += 1
        column = 0
    return []


def _written(index, key: str) -> set[str]:
    """The names a symbol is written with: a local's, at its definitions (a file two translation units compile
    numbers its locals twice: one key, two)."""
    if "#local " not in key:
        return {_last_name(key)} - {None}
    sources = index.__dict__.setdefault("_clang_sources", {})  # each file's lines, as bytes
    out = set()
    for rel, item in index.defs.get(key, ()):
        if rel not in sources:
            try:
                sources[rel] = (index.root / rel).read_bytes().split(b"\n")
            except OSError:
                sources[rel] = []
        if item.end_line == item.line <= len(sources[rel]):
            out.add(sources[rel][item.line - 1][item.start:item.end].decode("utf-8", errors="replace"))
    return out


def macro_arguments(index) -> int:
    """scip-clang writes a reference at its expansion location (Indexer.cc, `saveReference`): what a macro's
    arguments name sits at the macro's name. Each identifier of the arguments takes the symbol of its name written
    there, when one symbol has that name, and the macro's name keeps what no argument took: its body's own;
    returns how many occurrences it placed."""
    sources: dict[str, list[bytes]] = {}

    def lines(rel: str) -> list[bytes]:
        if rel not in sources:
            try:
                sources[rel] = (index.root / rel).read_bytes().split(b"\n")
            except OSError:
                sources[rel] = []
        return sources[rel]

    added = 0
    for rel, occurrences in index.documents.items():
        groups, moved = collections.defaultdict(list), set()
        for item in occurrences:
            if not item.definition and item.end_line == item.line:
                groups[(item.line, item.start, item.end)].append(item)
        for (line, _start, end), items in groups.items():
            if not any(MACRO.search(item.key) for item in items):
                continue
            named = collections.defaultdict(set)
            for item in items:
                for name in () if MACRO.search(item.key) else _written(index, item.key):
                    named[name].add(item.key)
            taken = set()
            for row, column, word in _arguments(lines(rel), line, end):
                keys = named.get(word.decode("utf-8", errors="replace"), ())
                if len(keys) == 1 and not index.at.get((rel, row, column)):
                    occurrences.append(code_graph.Occurrence(row, column, row, column + len(word), next(iter(keys)),
                                                             False, None))
                    taken |= keys
                    added += 1
            moved |= {item for item in items if item.key in taken}
        if moved:
            occurrences[:] = [item for item in occurrences if item not in moved]
    if added:
        dedupe(index)
    return added


def prepare(index, snapshot) -> dict:
    """Fill in what the index leaves to the reader (see the module docstring); returns what each step did."""
    deduplicated = dedupe(index)
    documents = utf8_columns(index)
    index.declarations = _declarations(index, snapshot)
    index.languages = {snapshot.checkout[rel]: language for rel, language in snapshot.languages.items()
                       if rel in snapshot.checkout and language in ("c", "cpp")}
    return {"deduplicated": deduplicated, "utf8_documents": documents, "enclosed": enclose(index),
            "macro_arguments": macro_arguments(index)}


INACTIVE = "in a branch of `{}` the build does not compile: the index has no occurrence in it"
DROPPED = ("in an argument of macro `{}` ({}), whose expansion in this build drops it: the index has no occurrence "
           "of what it names")
BUILT_IN = "a conversion to `{}`, a type the language builds in: no symbol to name"
AMBIGUOUS = ("in an argument of macro `{}` ({}), where the index writes {} symbols named `{}` (the expansion's own "
             "and the argument's): which one the argument names it does not say")
UNDEFINED = ("a name a conditional directive tests, read as code because the directive sits inside an "
             "expression: the index names no symbol there")
# scip-clang v0.4.1 names no symbol declared in a `LinkageSpecDecl` (SymbolFormatter.cc, getContextSymbol: "Pending:
# LinkageSpecDecl"), and the C library's headers declare theirs in one under C++ (`__BEGIN_DECLS`).
EXTERN_C = ("`{}`, declared for C++ only in an `extern \"C\"` block (the C library's, or the project's C): "
            "scip-clang v0.4.1 names no symbol declared there")
DIRECTIVE = re.compile(rb"\s*#\s*(?:if|ifdef|ifndef|elif|elifdef|elifndef)\b")
BRANCHES = ("preproc_if", "preproc_ifdef", "preproc_elif", "preproc_elifdef", "preproc_else")
# The types C and C++ build in, the callee of a conversion like `unsigned(1)` (the reader's grammar reads the
# keyword as a function's name).
TYPES = frozenset({"bool", "char", "char8_t", "char16_t", "char32_t", "double", "float", "int", "long", "short",
                   "signed", "unsigned", "void", "wchar_t"})
OPENS, ENDS = re.compile(rb"\s*#\s*if"), re.compile(rb"\s*#\s*endif\b")
TURNS = re.compile(rb"\s*#\s*(?:elif|else)\b")


def _branch(source: list[bytes], line: int) -> tuple[int, int, int] | None:
    """The innermost branch of a conditional directive holding `line`, by the directives' lines alone (where the
    reader's tree has none: a directive inside an expression): its directive's line, the `#if`'s, and the line of
    the directive that ends it, 1-based."""
    groups = []  # per open `#if`: its line and its current branch's
    for number, text in enumerate(source[:line - 1], 1):
        if OPENS.match(text):
            groups.append([number, number])
        elif TURNS.match(text) and groups:
            groups[-1][1] = number
        elif ENDS.match(text) and groups:
            groups.pop()
    if not groups:
        return None
    depth = 0
    for number, text in enumerate(source[line:], line + 1):
        if depth == 0 and (TURNS.match(text) or ENDS.match(text)):
            return groups[-1][1], groups[-1][0], number
        depth += bool(OPENS.match(text)) - bool(ENDS.match(text))
    return None


def _dropped(index, rel: str) -> dict[tuple[int, int], str]:
    """Each identifier, by `(line, byte column)`, in the arguments of a macro whose name holds no symbol of that
    identifier's name (`macro_arguments` placed the others): the expansion drops it (`DROPPED`); or two or more
    (`AMBIGUOUS`): the expansion's own and the argument's, which `macro_arguments` does not tell apart."""
    source = (index.root / rel).read_bytes().split(b"\n")
    groups = collections.defaultdict(list)
    for item in index.documents.get(rel, ()):
        if not item.definition and item.end_line == item.line:
            groups[(item.line, item.start, item.end)].append(item)
    out = {}
    for (line, start, end), items in groups.items():
        macro = next((item.key for item in items if MACRO.search(item.key)), None)
        if macro is None:
            continue
        held = collections.defaultdict(set)
        for item in items:
            for name in () if MACRO.search(item.key) else _written(index, item.key):
                held[name].add(item.key)
        defined = re.search(r"`([^`]*):(\d+):\d+`!$", macro)
        name = source[line - 1][start:end].decode("utf-8", errors="replace")
        where = f"{posixpath.basename(defined.group(1))}:{defined.group(2)}"
        for row, column, word in _arguments(source, line, end):
            word = word.decode("utf-8", errors="replace")
            keys = held.get(word, ())
            if not keys:
                out.setdefault((row, column), DROPPED.format(name, where))
            elif len(keys) > 1:
                out.setdefault((row, column), AMBIGUOUS.format(name, where, len(keys), word))
    return out


def unanswered(index):
    """Why the index has no occurrence at a site: the site is in a branch of a conditional directive where the
    index has no occurrence at all, one the build's configuration leaves out (`INACTIVE`), found by the reader's
    tree or by the directives' lines (a directive inside an expression, which the tree misplaces); in an argument
    a macro's expansion drops (`DROPPED`) or whose name two symbols written at the macro have (`AMBIGUOUS`); a
    name a conditional directive tests (`UNDEFINED`); a conversion to a type the language builds in (`BUILT_IN`);
    or, in C++, a name declared only in an `extern "C"` block (`EXTERN_C`)."""
    lines: dict[str, set[int]] = {}
    dropped: dict[str, dict] = {}
    defined: dict[str, set[str]] = {}  # each name the index defines: the languages of the files defining it

    def silent(rel: str, first: int, last: int) -> bool:  # no occurrence strictly between two lines
        if rel not in lines:
            lines[rel] = {item.line for item in index.documents[rel]}
        return not any(first < row < last for row in lines[rel])

    def extern_c(rel: str, source: list[bytes], line: int, column: int) -> str | None:
        """In a C++ file, an unqualified name (or `std::`'s) the index defines nowhere, or in C files only: the C
        library's, or the project's own C, which C++ reaches only through an `extern "C"` declaration."""
        if _language(index, rel) != "cpp":
            return None
        text = source[line - 1]
        found = IDENTIFIER.match(text, column)
        before = text[:column].rstrip()
        if not found or before.endswith((b".", b"->")) or (before.endswith(b"::") and not re.search(
                rb"(?<![\w:])std\s*::$", before)):
            return None
        if not defined:
            for key, places in index.defs.items():
                if "#local " not in key:
                    for name in _written(index, key):
                        defined.setdefault(name, set()).update(_language(index, place) for place, _item in places)
        name = found.group().decode("utf-8", errors="replace")
        return EXTERN_C.format(name) if defined.get(name, set()) <= {"c"} else None

    def cause(position: tuple) -> str | None:
        rel, line, column = position
        if rel not in index.documents or column is None:
            return None
        if rel not in dropped:
            dropped[rel] = _dropped(index, rel)
        if (line, column) in dropped[rel]:
            return dropped[rel][(line, column)]
        source = (index.root / rel).read_bytes().split(b"\n")
        if DIRECTIVE.match(source[line - 1]):
            return UNDEFINED
        tree = _tree(index, rel)
        node = tree.root_node.descendant_for_point_range((line - 1, column), (line - 1, column + 1)) \
            if tree is not None else None
        callee = node.parent.child_by_field_name("function") if node is not None and node.parent is not None \
            and node.parent.type == "call_expression" else None
        if callee is not None and callee.id == node.id and node.text.decode("utf-8", "replace") in TYPES:
            return BUILT_IN.format(node.text.decode("utf-8", errors="replace"))
        while node is not None and node.type not in BRANCHES:
            node = node.parent

        def said(*rows: int) -> str:  # `#else` of `#if X`: the branch and the condition it opens
            return INACTIVE.format("` of `".join(" ".join(source[row - 1].decode("utf-8", "replace").split())[:80]
                                                 for row in dict.fromkeys(rows)))
        if node is not None:
            alternative = node.child_by_field_name("alternative")
            holder = node
            while holder is not None and holder.type not in ("preproc_if", "preproc_ifdef"):
                holder = holder.parent
            closing = alternative or next((child for child in (holder.children if holder else ()) if child.type ==
                                           "#endif"), None)
            last = closing.start_point[0] + 1 if closing is not None else node.end_point[0] + 2
            if silent(rel, node.start_point[0] + 1, last):
                return said(*(at.start_point[0] + 1 for at in (node, holder) if at is not None))
        branch = _branch(source, line)  # where the tree has no branch here, or one it misplaces
        if branch and silent(rel, branch[0], branch[2]):
            return said(branch[0], branch[1])
        return extern_c(rel, source, line, column)
    return cause


# ---------------------------------------------------------------------------------------------------------
# Hops


def _language(index, rel: str) -> str:
    known = getattr(index, "languages", {}).get(rel)
    return known or ("c" if Path(rel).suffix.lower() in C_SOURCES else "cpp")


def _tree(index, rel: str):
    """The file's tree as the snapshot's reader parses it without an include context; None without a grammar."""
    key = (rel, "cfamily")
    if key not in index._trees:
        from languages import cfamily
        from languages._treesitter import get_parser
        language = _language(index, rel)
        loaded = get_parser(language)
        try:
            source = (index.root / rel).read_bytes()
        except OSError:
            source = None
        index._trees[key] = loaded[0].parse(cfamily.prepare(source, language)[0]) \
            if loaded and source is not None else None
    return index._trees[key]


def _references(index, rel: str, line: int, byte_column: int, definition: bool) -> list:
    native = index.from_bytes(rel, line, byte_column)
    return [item for item in index.at.get((rel, line, native), ()) if item.definition == definition]


def declaration_hops(index) -> dict:
    """A function the index defines nowhere leads to its prototype in the project, where the snapshot declares it."""
    out = collections.defaultdict(list)
    for rel, declared in getattr(index, "declarations", {}).items():
        for _kind, (l0, c0, _l1, _c1), payload in declared:
            name = payload.get("name_span")
            if not payload.get("contract") or not name:
                continue
            for item in _references(index, rel, name[0], name[1], False):
                if item.key not in index.defs and "#local " not in item.key:
                    out[item.key].append(((rel, l0, c0), "declaration"))
    return out


def lambda_hops(index) -> dict:
    """C++: a variable declared `auto` with a lambda leads to the lambda (its closure type is its own)."""
    out = collections.defaultdict(list)
    for rel in index.documents:
        if _language(index, rel) != "cpp":
            continue
        tree = _tree(index, rel)
        stack = [tree.root_node] if tree is not None else []
        while stack:
            node = stack.pop()
            stack.extend(node.children)
            holder = node.parent
            if node.type != "lambda_expression" or holder is None or holder.type != "init_declarator" \
                    or holder.child_by_field_name("value") != node:
                continue
            declaration = holder.parent
            kind = declaration.child_by_field_name("type") if declaration is not None else None
            name = holder.child_by_field_name("declarator")
            if kind is None or kind.type != "placeholder_type_specifier" or name is None or name.type != "identifier":
                continue
            for item in _references(index, rel, name.start_point[0] + 1, name.start_point[1], True):
                out[item.key].append(((rel, node.start_point[0] + 1, node.start_point[1]), "lambda"))
    return out


def hops(index) -> dict:
    """The adapter's hops over every C and C++ document of the index (after `prepare`)."""
    out = collections.defaultdict(list)
    for found in (declaration_hops(index), lambda_hops(index)):
        for key, items in found.items():
            out[key] += items
    return {key: list(dict.fromkeys(items)) for key, items in out.items()}


# ---------------------------------------------------------------------------------------------------------
# Rules


def _last_name(key: str) -> str | None:
    parts = code_graph.split_symbol(code_graph._global(key))
    items = code_graph.descriptors(parts[4]) if parts else []
    return items[-1][0] if items else None


def same_range(index) -> dict[tuple[str, str], bool]:
    """At a shared range only a using-declaration aliases: a global definition and a reference to a symbol of the
    same name (`using geo::twice;`). Never otherwise: scip-clang writes the constructor a declaration runs at the
    variable's name (`Circle circle(2.0);`) and everything a macro expands to at the macro's name, so a variable
    defined there would read as a call of the constructor or of the macro's contents."""
    out = {}
    for rel, occurrences in index.documents.items():
        for item in occurrences:
            if not item.definition:
                continue
            for other in index.at.get((rel, item.line, item.start), ()):
                if other.definition or other.key == item.key or (other.end_line, other.end) != (item.end_line, item.end):
                    continue
                out[(item.key, other.key)] = "#local " not in item.key and _last_name(item.key) == _last_name(other.key)
    return out


def classify(index):
    """`project` for a package the index defines symbols of, `namespace` for a namespace, the stated package of
    any other symbol (`(none)` for the package scip-clang writes `.`)."""
    own = set()
    for key in index.defs:
        parts = code_graph.split_symbol(code_graph._global(key))
        if parts is not None:
            own.add((parts[2], parts[3].rstrip("$")))

    def stated(key: str):
        parts = code_graph.split_symbol(code_graph._global(key))
        if parts is None:
            return None
        items = code_graph.descriptors(parts[4])
        if items and items[-1][1] == "namespace":
            return "namespace"
        package, version = parts[2], parts[3].rstrip("$")
        if (package, version) in own:
            return "project"
        return {"manager": parts[1], "package": package, "version": version} if package != "." else \
            {"manager": parts[1], "package": "(none)", "version": "-"}
    return stated


def refine(index, graph: dict, configs: dict | None = None) -> None:
    """An edge to a symbol with bodies at several places is `uncertain`: each place, `rel:line`, a candidate."""
    places = {}
    for edge in graph["edges"]:
        if edge["end"] != "project-callable" or edge["chain"]:
            continue
        key = edge["to"]
        if key not in places:
            places[key] = sorted({f"{rel}:{occurrence.line}" for rel, occurrence in index.defs.get(key, ())})
        if len(places[key]) > 1:
            edge["uncertain"] = {"reason": "one symbol defined at several places", "candidates": places[key]}


def tasks(configs) -> dict:
    """What the run brought back for `missing`: `{"compiled": {rel: commands}, "units": [state]}`, empty without
    it."""
    return configs if isinstance(configs, dict) else {}


def _unit(rel: str, units: list[dict]) -> dict | None:
    """The innermost unit holding a file, by its root; where two builds share a folder, the indexed one."""
    holding = [unit for unit in units if unit["root"] in (".", "") or rel.startswith(unit["root"].rstrip("/") + "/")]
    return max(holding, key=lambda unit: (len(unit["root"].strip(".")), unit["state"] == "indexed"), default=None)


def missing(index, rels: list[str], configs: dict | None = None) -> dict:
    """Why a C or C++ file of the snapshot has no document."""
    reasons, compiled, units = {}, (configs or {}).get("compiled") or {}, (configs or {}).get("units") or []
    for rel in rels:
        unit = _unit(rel, units)
        if unit is not None and unit["state"] != "indexed":
            reasons[rel] = f"the index of unit {unit['root']} is {unit['state']}: {unit['cause']}"
        elif rel in compiled:
            reasons[rel] = "compiled, yet no document in the index"
        elif Path(rel).suffix.lower() not in C_SOURCES | CPP_SOURCES:
            reasons[rel] = "header no indexed translation unit includes in an active branch"
        elif units and unit is None:
            reasons[rel] = "in no C or C++ unit of the pre-map"
        else:  # the folder no build compiles, or the files of it the build left out; a build that stopped says so
            folder = posixpath.dirname(rel)
            named = folder or "the root"
            where = (f"the build compiles other files of {named}, not this one"
                     if any(posixpath.dirname(other) == folder for other in compiled)
                     else f"no build compiles a file of {named}")
            cause = (unit or {}).get("cause")
            reasons[rel] = f"no compile command: {where}" + (f"; {cause}" if cause else "")
    return reasons


def nothing_failed(reason: str) -> bool:
    """Whether a reason `missing` gives says nothing failed for the file: no build compiles it (a build that stopped
    says so after `;`), no file a build compiles includes it, or its one build cannot run here (`unavailable`). A
    language none of whose files is indexed for such reasons only is `unavailable`, not `failed`
    (`engine_pass.index_stage`)."""
    return (reason in ("header no indexed translation unit includes in an active branch",
                       "in no C or C++ unit of the pre-map")
            or re.fullmatch(r"no compile command: [^;]+", reason) is not None
            or re.match(r"the index of unit .+? is unavailable: ", reason) is not None)


# ---------------------------------------------------------------------------------------------------------
# Running the indexer


def _sha256(path: Path) -> str:
    import hashlib
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def _carried(builds) -> list[tuple[str, str, str]]:
    """`(name, url, sha256)` of what the other `builds` run: Meson and Ninja, its backend; Bear for Make and cgo;
    the Go and Bazel pins, which a version the project states, installed by the preparation, replaces."""
    from premap import bazel, meson
    return [*((name, url, digest) for name, (url, digest) in zip(("meson.whl", "ninja.whl"), meson.DOWNLOAD)
              if "meson" in builds),
            *((f"bear/{posixpath.basename(url)}", url, digest) for url, digest in BEAR
              if {"make", "go", "autotools"} & set(builds)),
            *([("go.tar.gz", *preparation.GO[:2])] if "go" in builds else []),
            *([("bazel", *bazel.DOWNLOAD[0])] if "bazel" in builds else [])]


def clang_headers() -> Path:
    """A tar of clang's builtin headers (`CLANG_HEADERS`) under `include/`, as the resource folder holds them:
    the files of lib/Headers in clang's release source, downloaded once and checked by sha256, packed once beside
    it. A plain tar, which any tar unpacks."""
    version, url, digest = CLANG_HEADERS
    source = preparation.fetched(url, digest, posixpath.basename(url))
    target = source.with_name(f"clang-{version}-headers.tar")
    if not target.is_file():
        prefix, partial = f"clang-{version}.src/lib/Headers/", target.with_suffix(".partial")
        with tarfile.open(source) as bundle, tarfile.open(partial, "w") as packed:
            for member in bundle:
                if member.isfile() and member.name.startswith(prefix) and not member.name.endswith("CMakeLists.txt"):
                    data = bundle.extractfile(member)
                    member.name = "include/" + member.name.removeprefix(prefix)
                    packed.addfile(member, data)
        partial.replace(target)
    return target


def tools(builds=()) -> dict[str, Path]:
    """The container paths and host files the copy carries: CMake and scip-clang, downloaded once into the shared
    directory and checked by sha256 each time, clang's builtin headers (`clang_headers`), `clang_run.py`, and
    what the other `builds` run (`_carried`). A Gap when one cannot be downloaded and verified."""
    import container
    from resolve_edges import download, shared_engine_dir
    version, cmake_url, cmake_sha = CMAKE
    wanted = (("scip-clang", URL, SHA256, shared_engine_dir("scip-clang") / VERSION / "scip-clang-x86_64-linux"),
              ("cmake.tar.gz", cmake_url, cmake_sha, shared_engine_dir("cmake") / version / Path(cmake_url).name))
    inputs = {}
    for name, url, digest, target in wanted:
        try:
            if target.is_file() and _sha256(target) != digest:
                target.unlink()
            if not target.is_file():
                download(url, target, sha256=digest)
        except (OSError, ValueError) as error:
            raise container.Gap(f"{url} could not be downloaded and verified: {error}",
                                "check the network, then index again") from error
        inputs[f"{TOOLS}/{name}"] = target
    inputs[f"{TOOLS}/clang-{CLANG_HEADERS[0]}-headers.tar"] = clang_headers()
    inputs[f"{TOOLS}/clang_run.py"] = Path(__file__).with_name("clang_run.py")
    for name, url, digest in _carried(builds):
        inputs[f"{TOOLS}/{name}"] = preparation.fetched(url, digest, posixpath.basename(url))
    return inputs


def unavailable(cause: str, remedy: str) -> dict:
    return {"indexes": [], "runs": [], "indexer": {"name": "scip-clang", "version": VERSION, "seconds": 0,
                                                   "peak_mb": None},
            "state": "unavailable", "reason": cause, "install": remedy}


def failed(cause: str, runs: list[dict]) -> dict:
    tail = (runs[-1].get("stderr_tail") or "").strip()[-800:] if runs else ""
    return {"indexes": [], "runs": runs, "indexer": code_graph.indexer("scip-clang", VERSION, runs),
            "state": "failed", "reason": f"scip-clang wrote no index ({cause})" + (f": {tail}" if tail else "")}


def _folder(path: str | None) -> str:
    return (path or ".").strip("/").removeprefix("./") or "."


NATIVE = frozenset({CMAKE_UNIT, *OTHER_BUILDS, *BUILDS})  # the units that build C and C++ (a go-module through cgo)
# The analyzer this adapter is: the pass's entry, the languages it indexes, the unit kinds of the pre-map it takes
# its structure from, and whether its build runs only in a container (`indexers.analyzers`).
ENTRY, LANGUAGES, UNIT_KINDS, NEEDS_CONTAINER = "scip-clang", ("c", "cpp"), NATIVE, True



def structure(record: dict) -> dict:
    """What `index` takes from the pre-map: its native units, the workspaces that hold them, the CMake versions
    it states, the submodules it finds not checked out and the Dockerfiles as BuildKit reads them."""
    builds = record.get("docker_builds") or []
    return {"units": [unit for unit in record.get("units", []) if unit["kind"] in NATIVE
                      and (unit["kind"] != "go-module" or cgo(unit))],
            "workspace": record.get("workspace", []),
            "toolchains": [item for item in record.get("toolchains", []) if item.get("tool") in STATED],
            "absent": [gap["path"] for gap in record.get("gaps", []) if gap.get("kind") == "submodule_absent"],
            **({"docker": builds} if builds else {})}


STATED = ("cmake", "bazel", "go")  # the toolchains of the pre-map a build here runs with


def _version(text) -> tuple[int, ...]:
    return tuple(int(part) for part in str(text or "").removeprefix("go").split(".")[:3] if part.isdigit())


def newest_above(stated, pin: str) -> dict | None:
    """The newest minimum `stated` above `pin`, which the pin does not meet; None when it meets them all."""
    above = [item for item in stated or () if _version(item.get("version")) > _version(pin)]
    return max(above, key=lambda item: _version(item["version"])) if above else None


def wanted_cmake(stated) -> dict | None:
    """The newest CMake minimum `stated` above `CMAKE`, which the pin does not meet; None when it meets them all."""
    return newest_above(stated, CMAKE[0])


def wanted(stated, builds) -> list[dict]:
    """The toolchains the preparation installs with mise for these `builds`: the newest CMake and Go minimums above
    the pins, and the Bazel the project states, exactly (`.bazelversion`: Bazel's releases are not compatible)."""
    of = {tool: [item for item in stated or () if item.get("tool") == tool] for tool in STATED}
    cmake = wanted_cmake(of["cmake"])
    go = newest_above(of["go"], preparation.NEEDS["go"]["version"]) if "go" in builds else None
    return [*([cmake] if cmake else []), *([{**go, "version": str(go["version"]).removeprefix("go")}] if go else []),
            *(of["bazel"] if "bazel" in builds else [])]


def configure_roots(units, workspace) -> tuple[list[str], list[dict]]:
    """The folders CMake configures, each once: a `cmake-target`'s CMake workspace root, else its own root; and
    the state of each folder another native build declares, once per build."""
    owner = {_folder(member): _folder(item["root"]) for item in workspace or () if item.get("tool") == "cmake"
             for member in item.get("members", ())}
    roots = list(dict.fromkeys(owner.get(_folder(unit.get("root")), _folder(unit.get("root")))
                               for unit in units or () if unit.get("kind") == CMAKE_UNIT))
    others = dict.fromkeys((_folder(unit.get("root")), OTHER_BUILDS[unit["kind"]])
                           for unit in units or () if unit.get("kind") in OTHER_BUILDS)
    states = [{"root": root, "state": "unavailable", "kind": "not-cmake",
               "cause": f"built with {build}: Daodan configures C and C++ units with CMake only"}
              for root, build in others]
    return roots, states


def unbuilt(units) -> list[dict]:
    """The state of each folder a build declares that gives no compilation database here, once per build."""
    return [{"root": root, "state": "unavailable", "kind": "no-database",
             "cause": f"built with {build}: Daodan takes no compilation database from {build}"}
            for root, build in dict.fromkeys((_folder(unit.get("root")), OTHER_BUILDS[unit["kind"]])
                                             for unit in units or () if unit.get("kind") in OTHER_BUILDS
                                             and unit["kind"] not in BUILDS)]


def cgo(unit: dict) -> list[str]:
    """The packages of a `go-module` whose C files cgo compiles."""
    return [item["package"] for item in (unit.get("config") or {}).get("cgo", ()) if item.get("c_files")]


def meson_top(project_dir: Path, root: str) -> str:
    """The folder Meson configures a meson.build of `root` from: the outermost one holding a meson.build, from the
    checkout's root down to `root` (a subdir's meson.build is read only from its project's)."""
    parts = [] if root == "." else root.split("/")
    return next((folder for folder in ("/".join(parts[:depth]) or "." for depth in range(len(parts) + 1))
                 if (Path(project_dir) / folder / "meson.build").is_file()), root)


def builds(units, workspace, top) -> list[dict]:
    """The builds beside CMake that give a compilation database, each once: Meson's from the top folder of its
    meson.build files (`top(root)`), Make's per folder with the targets the pre-map states there (`configure` when
    the project's own configure writes its Makefile, `premap.make`), Bazel's from its
    workspace's root, Go's per module with its cgo packages, `download` when the module requires others."""
    owner = {_folder(member): _folder(item["root"]) for item in workspace or () if item.get("tool") == "bazel"
             for member in item.get("members", ())}
    plan: dict[tuple[str, str], dict] = {}
    for unit in units or ():
        kind, root = unit.get("kind"), _folder(unit.get("root"))
        if kind == "meson-target":
            plan.setdefault((top(root), "meson"), {})
        elif kind == "make-target":
            entry = plan.setdefault((root, "make"), {"targets": []})
            entry["targets"].append(unit["name"])
            if (unit.get("config") or {}).get("configure"):  # its Makefile is what the project's configure writes
                entry["configure"] = True
        elif kind == "bazel-target":
            plan.setdefault((owner.get(root, root), "bazel"), {})
        elif kind == "autotools-project":
            plan.setdefault((root, "autotools"), {})
        elif kind == "go-module" and cgo(unit):
            plan[(root, "go")] = {"packages": cgo(unit), **({"download": True} if unit.get("registries") else {})}
    return [{"root": root, "build": build, **extra} for (root, build), extra in plan.items()]


def restores(project_dir: Path, roots) -> dict[str, dict]:
    """Per configure root that declares vcpkg or Conan, the restore the pre-map's configure of it has
    (`premap.cmake`; both declared, the one a configure preset's CMAKE_TOOLCHAIN_FILE names, else vcpkg):
    `{manager, line, init}`, the preparation's line installing the root's dependencies, its failure printed as
    `preparation.restore` prints one, and the initial cache it writes, which names the manager's toolchain file."""
    import container
    from types import SimpleNamespace
    from premap import cmake as premap_cmake
    project_dir = Path(project_dir)
    names = [*(mark for _name, marks, _line in premap_cmake.MANAGERS for mark in marks), premap_cmake.PRESETS]
    held = {posixpath.join(root, name).removeprefix("./") for root in roots for name in names
            if (project_dir / root / name).is_file()}
    read = SimpleNamespace(inventory=SimpleNamespace(  # what `premap.cmake` reads of the snapshot, from the copy
        headers=held, text=lambda rel: (project_dir / rel).read_text(encoding="utf-8", errors="replace")))
    out = {}
    for root in roots:
        try:
            manager = premap_cmake._manager(read, root)[0]
        except ValueError:  # a CMakePresets.json that is no JSON: the pre-map prepares no configure either
            manager = None
        if manager is None:
            continue
        name, _marks, script = manager
        key, folder = premap_cmake._key(root), shlex.quote(posixpath.normpath(f"{container.WORKDIR}/{root}"))
        line = (f"( cd {folder} && mkdir -p {premap_cmake.PREP}/{key} && sh -c {shlex.quote(script)} prepare {key} )"
                f" > {preparation.LOG} 2>&1 || {{ printf 'DAODAN-RESTORE-FAILED {name} %s\\n' {shlex.quote(root)};"
                f" {{ grep -Ei '^error|error:' {preparation.LOG} || tail -n 30 {preparation.LOG}; }} | head -n 30;"
                " echo DAODAN-RESTORE-END; } >&2")
        out[root] = {"manager": name, "line": line, "init": f"{premap_cmake.PREP}/{key}/init.cmake"}
    return out


def index(project_dir: Path, work_dir: Path, files: list[str] | None = None, *, units: list[dict] | None = None,
          workspace: list[dict] | None = None, toolchains=(), absent=(), engine=None, memory: int = MIN_FREE,
          cpus: int = 1, timeout: float = 3600, declared: dict | None = None, docker=()) -> dict:
    """The index of each configured root, with its runs and each root's state; `units`, `workspace` and the
    submodules not checked out (`absent`) are the pre-map's (`files` is not used: a unit's compilation database
    decides what is indexed). `cpus` is the container's share, as the caller gives it: its limit and scip-clang's
    jobs. A unit whose build gives no database (`unbuilt`), or whose configure needs a download outside the
    allowed registries or an absent submodule, is `unavailable`; one whose build fails otherwise, `failed`; either
    keeps its static facts from the snapshot. Without a unit indexed, or without a container, the result's state
    is `unavailable` (no unit failed) or `failed`. `gaps` says what the preparation could not install: a CMake of
    `toolchains`, a root's dependencies (`restores`). A CMake root not indexed here is built in the stage of the
    Dockerfile (`docker`, the pre-map's) that copies in its CMakeLists.txt (`_docker`)."""
    import container
    project_dir, work_dir = Path(project_dir).resolve(), Path(work_dir).resolve()
    work_dir.mkdir(parents=True, exist_ok=True)
    roots, _observed = configure_roots(units, workspace)  # its states are the dynamic step's: these builds run here
    others = builds(units, workspace, lambda root: meson_top(project_dir, root))
    states = unbuilt(units)
    if not roots and not others:
        return unavailable("; ".join(dict.fromkeys(item["cause"] for item in states)) or NO_UNIT,
                           "none: the project's C and C++ files keep their static facts")
    if container.architecture() != "x64":
        return unavailable(f"scip-clang {VERSION} has an x86_64 Linux build only", "index on an x86_64 machine")
    restored = restores(project_dir, roots)
    chosen = [*({"root": root, **({"init": restored[root]["init"]} if root in restored else {}),
                 **({"absent": list(absent)} if absent else {})} for root in roots), *others]
    plan = work_dir / "units.json"
    plan.write_text(json.dumps(chosen, indent=1) + "\n", encoding="utf-8")
    out_dir = work_dir / "container"
    back = out_dir / Path(OUT).name
    shutil.rmtree(back, ignore_errors=True)
    kinds = {item["build"] for item in others}
    fetches = "bazel" in kinds or any(item.get("download") for item in others)  # Bazel's aquery, Go's modules
    cmake = wanted_cmake([item for item in toolchains or () if item.get("tool") == "cmake"])
    chains = preparation.toolchains(wanted(toolchains, kinds))
    needs = preparation.setup(sorted({item["manager"] for item in restored.values()}))
    lines = [*chains["lines"], *needs["lines"], *([CMAKE_ON_PATH] if restored else []),
             *(item["line"] for item in restored.values()),
             *([f"python3 {TOOLS}/clang_run.py prepare {TOOLS}/units.json || true"] if fetches else [])]
    from premap.container_runner import TOOLS as RUNNERS
    command = ["python3", f"{TOOLS}/clang_run.py", f"{TOOLS}/units.json", OUT, str(cpus)]
    options = {"prepare": ["sh", "-c", "\n".join([f"mkdir -p {preparation.T}/bin {preparation.ENV['HOME']}", *lines])],
               "registries": tuple(dict.fromkeys([*(container.REGISTRIES if needs["registries"] or fetches else ()),
                                                  *chains["hosts"], *needs["hosts"],
                                                  *(RUNNERS["bazel"]["hosts"] if "bazel" in kinds else ()),
                                                  *(declared or {}).get("hosts", ())])),
               "env": {**preparation.ENV, "TERM": "dumb"}} if lines else {"env": {"TERM": "dumb"}}
    if cmake:
        command.append(f"{preparation.T}/bin/cmake")  # mise's, linked there; the pin when it is not
    if "bazel" in kinds:  # the memory Bazel's server needs, as the pre-map's runner gives it
        memory = max(memory, int(RUNNERS["bazel"]["memory"] * 2**30))
    (out_dir / "prepare.log").unlink(missing_ok=True)
    result = container.run_in_container(
        project_dir, command, image=IMAGE, out_dir=out_dir, outputs=[OUT], timeout=timeout,
        memory=memory, pids=PIDS, cpus=cpus, engine=engine, **options,
        inputs=lambda: {**tools(kinds), f"{TOOLS}/units.json": plan,
                        **{f"{preparation.IN}/{name}": preparation.fetched(url, digest, name)
                           for url, digest, name in [*chains["files"], *needs["files"]]}})
    log = out_dir / "prepare.log"
    prepared = log.read_text(encoding="utf-8", errors="replace") if log.is_file() else ""
    gaps = chains["gaps"] + preparation.missing(prepared) + preparation.restore_gaps(prepared) + list(
        result.get("gaps") or ())  # and what the copy left out (`container.copy_perimeter`)
    contract = _contract(result, back, work_dir, states)
    if docker:
        contract, staged = _docker(project_dir, work_dir, roots, contract, docker, memory=memory, cpus=cpus,
                                   engine=engine, timeout=timeout)
        gaps += staged
    return {**contract, **({"gaps": gaps} if gaps else {})}


CMAKE_BUILD = r"\bcmake\b"  # the RUN of a Dockerfile's stage that configures and builds its CMake project
STAGE_OUT = "/daodan/out"  # what the run in a Dockerfile's stage brings back
BUILD_EXIT = re.compile(r"DAODAN-BUILD-EXIT (\d+)")
MUSL = "/lib/ld-musl-x86_64.so.1"  # a base whose C library is musl (Alpine), where scip-clang needs glibc beside it
STAGE_MEMORY = 8 * 2**30  # a stage's steps build its dependencies as its Dockerfile does (`make -j$(nproc)`)
# The stage's package map, the main route's (`clang_run.package_map`) in POSIX sh and awk, which a base without
# python3 has: the folder the build runs in as the project; each folder under the C and C++ compilers' include
# paths as the apk or dpkg package owning most of its files there, named as `clang_run._clean` writes it. What a
# CMake install of the stage's steps wrote (its install_manifest.txt, the build's own record) belongs to the package
# that build's CMakeCache names, project and version; the build in the folder the stage's build runs in is the
# project's. A folder no package owns has none. DAODAN_ROOT is where the stage's filesystem lies: the container's
# own, unset.
PACKAGE_MAP = r"""R=${DAODAN_ROOT:-}
dirs=$( { cc -xc -E -v /dev/null; c++ -xc++ -E -v /dev/null; } 2>&1 </dev/null |
  sed -n '/^#include <\.\.\.> search starts here:/,/^End of search list\./s/^ //p' |
  while read -r d; do realpath "$d" 2>/dev/null; done | sort -u )
{
  [ -f "$R/lib/apk/db/installed" ] && awk '/^P:/ { p = substr($0, 3) } /^V:/ { print "V\t" p "\t" substr($0, 3) }
    /^F:/ { f = "/" substr($0, 3) } /^R:/ { print "O\t" f "/" substr($0, 3) "\t" p }' "$R/lib/apk/db/installed"
  if [ -d "$R/var/lib/dpkg/info" ]; then
    dpkg-query --admindir="$R/var/lib/dpkg" -W -f '${Package}\t${Version}\n' 2>/dev/null | sed 's/^/V\t/'
    for list in "$R"/var/lib/dpkg/info/*.list; do
      [ -f "$list" ] || continue
      name=${list##*/}; name=${name%.list}
      awk -v name="${name%%:*}" '{ print "O\t" $0 "\t" name }' "$list"
    done
  fi
  find "$R/" -xdev -name install_manifest.txt -type f 2>/dev/null | while read -r manifest; do
    case "$manifest" in "$PWD"/*) continue ;; esac
    cache="${manifest%/*}/CMakeCache.txt"
    name=$(sed -n 's/^CMAKE_PROJECT_NAME:[A-Z]*=//p' "$cache" 2>/dev/null | head -n 1)
    [ -n "$name" ] || continue
    printf 'V\t%s\t%s\n' "$name" "$(sed -n 's/^CMAKE_PROJECT_VERSION:[A-Z]*=//p' "$cache" | head -n 1)"
    awk -v name="$name" '{ print "O\t" $0 "\t" name }' "$manifest"
  done
  printf '%s\n' "$dirs" | while read -r d; do [ -n "$d" ] && find "$d" -type f 2>/dev/null; done |
    awk -v root="$R" '{ print "F\t" substr($0, length(root) + 1) }'
} | awk -F '\t' '
  function clean(s) { gsub(/[^A-Za-z0-9_.-]/, "_", s); return s }
  $1 == "V" { version[$2] = $3; next }
  $1 == "O" { owner[$2] = $3; next }
  $1 == "F" && ($2 in owner) { dir = $2; sub(/\/[^\/]*$/, "", dir); votes[dir "\t" owner[$2]]++ }
  END {
    for (key in votes) { split(key, k, "\t"); if (votes[key] > best[k[1]]) { best[k[1]] = votes[key]; won[k[1]] = k[2] } }
    printf "[{\"path\": \".\", \"package\": \"project@0\"}"
    for (dir in won) if (dir !~ /["\\]/)
      printf ",\n{\"path\": \"%s\", \"package\": \"%s@%s\"}", dir, clean(won[dir]),
             clean(version[won[dir]] == "" ? "unknown" : version[won[dir]])
    print "]" }'"""
HEADERS = f"{preparation.T}/clang/include"  # clang's builtin headers in the stage (`clang_headers`, `_staged`)
# `clang_run.builtin_headers` and the compiler's target, in POSIX sh: the compilation database `$db` into `$out`,
# each command given `--target=` its compiler's `-dumpmachine` (clang otherwise looks for the compiler's headers
# under its own default target: Alpine's are x86_64-alpine-linux-musl's) and, for a compiler that is not clang (no
# `-print-resource-dir`), `-nobuiltininc -isystem HEADERS -idirafter <its include folder>`, on a musl target
# `-idirafter HEADERS`, after the C library's headers, where clang's own driver puts them (Linux.cpp of
# llvmorg-21.1.8); a command with -nostdinc or -nobuiltininc keeps its builtin headers as they are.
COMPDB = r"""rules=/tmp/daodan-compdb.sed
: > "$rules"
for c in $(sed -n 's/^ *"command": "\([^ ]*\) .*/\1/p' "$db" | sort -u); do
  t=$("$c" -dumpmachine) || exit 4
  if ! "$c" -print-resource-dir >/dev/null 2>&1; then
    case "$t" in *musl*) f=" -nobuiltininc -idirafter HEADERS" ;; *) f=" -nobuiltininc -isystem HEADERS" ;; esac
    i=$("$c" -print-file-name=include 2>/dev/null | tail -n 1)
    case "$i" in /*) [ -d "$i" ] && f="$f -idirafter $i" ;; esac
    printf '/-nostdinc[ "]/!{\n/-nobuiltininc[ "]/!s|"command": "%s |"command": "%s%s |\n}\n' "$c" "$c" "$f" >> "$rules"
  fi
  printf 's|"command": "%s |"command": "%s --target=%s |\n' "$c" "$c" "$t" >> "$rules"
done
sed -f "$rules" "$db" > "$out"
""".replace("HEADERS", HEADERS)


def _stage_script(build: list[str], jobs: int) -> str:
    """POSIX sh, as a stage's base may have no python3 (Alpine): the stage's own build with CMake writing its
    compilation database, its exit code printed; that database (the first under the build's folder) with each
    command given its compiler's target and clang's builtin headers (`COMPDB`); then scip-clang where the build
    runs, its documents relative to that folder, the system's named by the stage's packages (`PACKAGE_MAP`) and
    clang's headers as clang at their version, as the main route names them."""
    return "\n".join([
        "export CMAKE_EXPORT_COMPILE_COMMANDS=ON",
        f'{shlex.join(build)} ; echo "DAODAN-BUILD-EXIT $?"',
        "db=$(find . -name compile_commands.json -type f | head -n 1)",
        '[ -n "$db" ] || { echo DAODAN-NO-DATABASE ; exit 3 ; }',
        f'mkdir -p {STAGE_OUT} && cp "$db" {STAGE_OUT}/compile_commands.json',
        f"out=/tmp/daodan-compdb.json\n{COMPDB}",
        f"(\n{PACKAGE_MAP}\n) | sed '1s|^\\[|[{{\"path\": \"{HEADERS}\", \"package\": \"clang@{CLANG_HEADERS[0]}\"}},|'"
        " > /tmp/daodan-packages.json",
        f"exec {preparation.T}/bin/scip-clang --compdb-path=/tmp/daodan-compdb.json"
        f" --package-map-path=/tmp/daodan-packages.json --jobs={jobs} --show-compiler-diagnostics"
        f" --index-output-path={STAGE_OUT}/index.scip"])


def _docker(project_dir: Path, work_dir: Path, roots: list[str], contract: dict, builds, *, memory: int,
            cpus: int, engine, timeout: float) -> tuple[dict, list[dict]]:
    """The contract with each CMake root the run here did not index built and indexed in the stage of a
    Dockerfile that copies in its CMakeLists.txt (`docker_build.plan`): the stage's steps in the preparation on
    its base by digest, with scip-clang and, on a musl base, glibc's libraries where only glibc's loader looks
    (`docker_build.glibc`); then offline the stage's own build and scip-clang (`_stage_script`), the documents
    named as the checkout's files. The unit's state is that run's, with the Dockerfile, the stage and the steps
    run (`docker`); a stage not reproduced or a step that fails is the unit's cause with its line. Also the gaps
    of the stages: `not_reproduced`, `restore_failed`, `host_unreachable`."""
    import docker_build
    units = list(contract.get("units") or ())
    indexes, runs, gaps = list(contract.get("indexes") or ()), list(contract.get("runs") or ()), []
    compiled = collections.Counter((contract.get("configs") or {}).get("compiled") or {})
    changed, seen = False, {}

    def staged(build: dict, plan: dict, root: str) -> dict:
        return _staged(project_dir, work_dir, build, plan, root, indexes, runs, compiled, gaps, memory=memory,
                       cpus=cpus, engine=engine, timeout=timeout)

    for root in roots:
        if any(unit["root"] == root and unit["state"] == "indexed" for unit in units):
            continue
        wanted = [posixpath.join(root, "CMakeLists.txt") if root not in ("", ".") else "CMakeLists.txt"]
        found = next(((build, plan) for build in builds
                      if (plan := docker_build.plan(build, project_dir, wanted, CMAKE_BUILD)) is not None), None)
        if found is None:
            continue
        build, plan = found
        changed, state = True, next((unit for unit in units if unit["root"] == root), None)
        if state is None:
            state = {"root": root, "state": "failed", "cause": contract.get("reason") or "not configured here"}
            units.append(state)
        key = (plan["dockerfile"], plan["stage"])
        if key not in seen:  # one plan and one run for the units one stage builds
            plan = docker_build.sourced(plan, work_dir / f"sources-{len(seen)}", engine=engine)
            gaps += plan["gaps"]
            seen[key] = (plan, None if plan["gaps"] else staged(build, plan, root))
        plan, outcome = seen[key]
        if plan["gaps"]:
            first = plan["gaps"][0]
            state["cause"] = (f"{state.get('cause')}; its Dockerfile's build stage is not reproduced: "
                              f"{first['path']}: {first['detail']}")
            continue
        state.pop("cause", None)
        state.update(outcome)
    return (_assembled(indexes, runs, compiled, units), gaps) if changed else (contract, [])


def _staged(project_dir: Path, work_dir: Path, build: dict, plan: dict, root: str, indexes: list, runs: list,
            compiled: collections.Counter, gaps: list, *, memory: int, cpus: int, engine, timeout: float) -> dict:
    """The run of `plan`'s stage for `root` (`_docker`): what the unit's state becomes; its index, run, compiled
    files and gaps added to the lists given."""
    import docker_build
    from indexers.clang_run import _diagnostics  # scip-clang's diagnostics, as the main route counts them
    out_dir, started = work_dir / f"docker-{len(runs)}", time.monotonic()
    result = docker_build.run(
        project_dir, out_dir, plan, ["sh", "-c", _stage_script(plan["build"]["argv"], cpus)],
        setup=[f"mkdir -p {preparation.T}/bin", f"if [ -e {MUSL} ]; then tar -xf {preparation.IN}/glibc.tar -C / ; fi",
               f"cp {preparation.IN}/scip-clang {preparation.T}/bin/scip-clang && chmod 755 {preparation.T}/bin/scip-clang",
               f"mkdir -p {posixpath.dirname(HEADERS)} && tar -xf {preparation.IN}/clang-headers.tar"
               f" -C {posixpath.dirname(HEADERS)}"],
        carried=lambda: {f"{preparation.IN}/scip-clang": tools()[f"{TOOLS}/scip-clang"],
                         f"{preparation.IN}/glibc.tar": docker_build.glibc(),
                         f"{preparation.IN}/clang-headers.tar": clang_headers()},
        outputs=[STAGE_OUT], memory=max(memory, STAGE_MEMORY), cpus=cpus, pids=PIDS, engine=engine, timeout=timeout,
        prepare_timeout=3600)
    logs = {name: (out_dir / f"{name}.log").read_text(encoding="utf-8", errors="replace")
            if (out_dir / f"{name}.log").is_file() else "" for name in ("prepare", "execute")}
    step, ended = docker_build.failed_step(plan, build, logs["prepare"]), BUILD_EXIT.search(logs["execute"])
    gaps += result.get("gaps") or []  # what the copy left out (`container.copy_perimeter`)
    built = f"{plan['dockerfile']}:{plan['build']['line']} `{plan['build']['original']}`"
    provenance = docker_build.provenance(plan)
    runs.append({"unit": root, "step": "docker", "returncode": result.get("exit_code"),
                 "seconds": round(time.monotonic() - started, 1), "peak_mb": None,
                 "stderr_tail": (logs["execute"] or logs["prepare"])[-2500:], "docker": provenance,
                 **({"diagnostics": _diagnostics(logs["execute"])} if logs["execute"] else {})})
    if step:
        gaps += step["gaps"]
        return {"state": "failed", "cause": f"{step['path']} `{step['original']}` failed: {step['error']}"}
    if ended is None:
        last = docker_build.last_line(logs["prepare"]).strip()
        return {"state": "failed", "cause": f"its Dockerfile's build stage did not run: {result.get('cause')}"
                                            + (f": {last}" if last else "")}
    code = int(ended.group(1))
    if "DAODAN-NO-DATABASE" in logs["execute"]:
        return {"state": "failed", "cause": f"{built} ended with exit code {code} and wrote no compilation database: "
                                            f"{docker_build.last_line(logs['execute'], ended.start())}"}
    database = out_dir / "out" / "compile_commands.json"
    for entry in json.loads(database.read_text(encoding="utf-8")) if database.is_file() else ():
        rel = docker_build.origin(plan, posixpath.join(entry.get("directory") or plan["workdir"], entry["file"]))
        if rel:
            compiled[rel] += 1
    written, target = out_dir / "out" / "index.scip", work_dir / f"scip-clang-docker-{len(indexes)}.scip"
    if written.is_file() and docker_build.rewritten(written, plan, target):
        indexes.append([str(target), ""])
        return {"state": "indexed", "docker": provenance,
                **({"cause": f"{built} ended with exit code {code}"} if code else {})}
    said = f"; {result['cause']}" if result.get("cause") else ""  # the engine's own words
    return {"state": "failed", "cause": f"scip-clang in its Dockerfile's build stage wrote no index of the checkout's "
                                        f"files (exit code {result.get('exit_code')}{said}): "
                                        f"{docker_build.last_line(logs['execute']).strip()}"}


def _contract(result: dict, back: Path, work_dir: Path, states: list[dict]) -> dict:
    """The contract from what the container run brought back into `back`, its indexes moved into `work_dir`,
    after the `states` of the units it did not configure."""
    if result["state"] == "gap":
        return unavailable(result["cause"], result["remedy"])
    report = back / "result.json"
    if result["state"] != "done" or not report.is_file():
        return failed(result.get("cause") or f"the container run ended {result['state']}", [])
    data = json.loads(report.read_text(encoding="utf-8"))
    indexes, runs, compiled = [], [], collections.Counter()
    for unit in data["units"]:
        for step in unit["steps"]:
            runs.append({"unit": unit["root"], "step": step["step"], "returncode": step["returncode"],
                         "seconds": step["seconds"], "peak_mb": data.get("peak_mb"), "stderr_tail": step["tail"],
                         **({"diagnostics": step["diagnostics"]} if "diagnostics" in step else {})})
        states.append({key: unit[key] for key in ("root", "build", "state", "kind", "cause", "fetched", "error")
                       if key in unit})
        compiled.update(unit["compiled"])
        if unit["index"] and (back / unit["index"]).is_file():
            target = work_dir / unit["index"]
            target.unlink(missing_ok=True)
            shutil.move(str(back / unit["index"]), str(target))
            indexes.append([str(target), ""])
    return _assembled(indexes, runs, compiled, states)


def _assembled(indexes: list, runs: list[dict], compiled: collections.Counter, states: list[dict]) -> dict:
    """The contract of the units' `states`, with their indexes, runs and compiled files."""
    if not indexes:
        causes = "; ".join(f"{item['root']}: {item['cause']}" for item in states)
        if all(item["state"] == "unavailable" for item in states):
            return {**unavailable(causes, "none: the units keep their static facts"), "runs": runs, "units": states}
        return {**failed(causes, runs), "units": states}
    indexer = code_graph.indexer("scip-clang", VERSION, runs)
    staged = [run["diagnostics"] for run in runs if run.get("step") == "docker" and run.get("diagnostics")]
    if staged:  # the stage's log stays in the work folder: what scip-clang said of its compiles is on record here
        indexer["diagnostics"] = {"errors": sum(item["errors"] for item in staged),
                                  "warnings": sum(item["warnings"] for item in staged),
                                  "error_examples": list(dict.fromkeys(
                                      example for item in staged for example in item["error_examples"]))[:8]}
    return {"indexes": indexes, "runs": runs, "indexer": indexer,
            "units": states, "configs": {"compiled": dict(sorted(compiled.items())), "units": states}}
