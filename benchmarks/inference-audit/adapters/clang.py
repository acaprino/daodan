"""scip-clang for C and C++: how the indexer runs and what its index leaves to the reader.

`index` produces the compilation database by configuring and building a copy of the checkout with CMake
(`CMAKE_EXPORT_COMPILE_COMMANDS`; the build runs the project's own scripts, so only inside the container),
writes a package map (the checkout's root as the project's package, each system include directory as the
Debian package owning most of its headers) and runs scip-clang from the copy's root. Symbols carry no file:
a function declared in a header and defined in a source file is one symbol, defined at its body; the
declaration is a reference.

The product snapshot reads C and C++ (`languages/cfamily.py`), but gives no semantic facts for a file
tree-sitter cannot parse whole (51 of 66 zlib C files, 2 of 4 tinyxml2 files), so the stored results keep
`SyntaxSnapshot`, which reads every tree as it is: the perimeter (files Git tracks, dot directories left out),
the functions, methods, classes, prototypes and lambdas declared at each name, and the call sites
(`call_expression` and `new_expression`, casts written as calls left out) the graph's holes are counted on.
Annotation macros (`class EXPORT Name`, `int ZEXPORT f(`) are blanked before parsing, positions unchanged.

scip-clang writes what a macro expands to at the expansion: the call `SQUARE(n)` references the macro and the
function its body calls, at the same range, so macros need no hop. `hops` states two things the index leaves
implicit: a function the index defines nowhere leads to its prototype in the project (`declaration`); a
variable declared `auto` with a lambda leads to that lambda (`lambda`, the closure type is unique). A call
through a function pointer, a struct field or a parameter ends on that value: nothing is guessed. `same_range`
keeps the shared rule from reading a variable defined where a constructor or a macro is referenced as an alias:
only a using-declaration aliases at a shared range.

Three thin steps fill what the index leaves to the reader: `dedupe` (a file compiled by several translation
units comes as several documents, which the shared reader appends), `utf8_columns` (no position encoding is written, and the
columns are UTF-8 bytes, not the UTF-16 the shared reader assumes) and `enclose` (no enclosing range is
written; each function and class definition gets the range of its syntax node, so edges start at the
function that holds them rather than at the file). `refine` marks an edge `uncertain` when its symbol has
bodies at several places (two translation units defining one name). Anything C-only or C++-only is in a
function named so.
"""
from __future__ import annotations

import collections
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import plugin_scripts  # noqa: E402,F401  (puts the plugin's scripts on the path)
import code_graph as scip_graph  # noqa: E402

VERSION = "v0.4.1"  # github.com/sourcegraph/scip-clang, released 2026-10-22, LLVM 21
URL = f"https://github.com/sourcegraph/scip-clang/releases/download/{VERSION}/scip-clang-x86_64-linux"
SHA256 = "a434d26a079fd80e1996ba79276cb1ef86b2b2ad28b13e24386285db32c59046"  # the release asset's digest
BINARY = "/opt/scip-clang/scip-clang"
APT = ("cmake", "build-essential")
C_SUFFIXES = {".c"}
CPP_SOURCES = {".cc", ".cpp", ".cxx", ".c++"}
CPP_SUFFIXES = CPP_SOURCES | {".hpp", ".hh", ".hxx", ".h++", ".ipp", ".inl", ".tpp", ".txx"}
HEADER = ".h"  # C or C++: the case's language
NAMES = {"identifier", "field_identifier", "destructor_name", "operator_name", "type_identifier"}
BRANCHES = {"preproc_if", "preproc_ifdef", "preproc_elif", "preproc_elifdef", "preproc_else"}
CASTS = {"static_cast", "dynamic_cast", "reinterpret_cast", "const_cast"}
# Annotation macros (export, visibility, calling convention) break tree-sitter: an upper-case word between
# `class` and the name (`class EXPORT Name {`), or, on a line that starts a top-level definition, between the
# return type and the name (`int ZEXPORT inflate(`), can only be a macro. Blanked to spaces before parsing.
ANNOTATIONS = (
    re.compile(rb"\b(?:class|struct|union)\s+([A-Z][A-Z0-9_]*)\s+(?=[A-Za-z_]\w*\s*(?:final\s*)?[:{])"),
    re.compile(rb"(?m)^[A-Za-z_][\w \t*]*?[\w*][ \t]+([A-Z][A-Z0-9_]*)[ \t]+(?=\**[ \t]*[A-Za-z_]\w*[ \t]*\()"),
)
COUNTED = ("using_declaration", "alias_declaration", "namespace_definition", "template_declaration",
           "lambda_expression", "operator_name", "destructor_name", "preproc_function_def", "preproc_def",
           "preproc_ifdef", "preproc_if", "virtual")


def install_commands() -> list[str]:
    return ["mkdir -p /opt/scip-clang", f"curl -fsSL {URL} -o {BINARY}",
            f"echo '{SHA256}  {BINARY}' | sha256sum -c -", f"chmod +x {BINARY}"]


def language_of(rel: str, primary: str) -> str | None:
    suffix = Path(rel).suffix.lower()
    if suffix in C_SUFFIXES:
        return "c"
    if suffix in CPP_SUFFIXES:
        return "cpp"
    return primary if suffix == HEADER else None


def perimeter(root: Path, primary: str) -> list[str]:
    """C and C++ files of the checkout: what Git tracks (every file without Git), no dot directory."""
    root = Path(root)
    done = subprocess.run(["git", "ls-files", "-z"], cwd=root, capture_output=True) \
        if (root / ".git").exists() else None
    if done is not None and done.returncode == 0:
        rels = [item for item in done.stdout.decode("utf-8", errors="replace").split("\0") if item]
    else:
        rels = [path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()]
    return sorted(rel for rel in rels if language_of(rel, primary) and (root / rel).is_file()
                  and not any(part.startswith(".") for part in rel.split("/")[:-1]))


# ---------------------------------------------------------------------------------------------------------
# Running the indexer


def _search_dirs(compiler: str, language: str) -> list[str]:
    err = subprocess.run([compiler, f"-x{language}", "-E", "-v", "-"], input="", capture_output=True,
                         text=True).stderr.split("\n")
    try:
        start = err.index("#include <...> search starts here:") + 1
        end = err.index("End of search list.")
    except ValueError:
        return []
    return [os.path.realpath(line.strip()) for line in err[start:end] if line.strip()]


def _clean(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.\-]", "_", text)


def package_map(project: str) -> tuple[list[dict], dict]:
    """The checkout's root as the project, each directory under the system include paths as the Debian package
    owning most of its direct files (dpkg's file lists): the package identity scip-clang writes in symbols."""
    owners = collections.defaultdict(set)
    for listing in Path("/var/lib/dpkg/info").glob("*.list"):
        name = listing.stem.split(":")[0]
        for line in listing.read_text(encoding="utf-8", errors="replace").split("\n"):
            if line:
                owners[os.path.realpath(line)].add(name)
    versions = dict(line.split(" ", 1) for line in subprocess.run(
        ["dpkg-query", "-W", "-f", "${Package} ${Version}\\n"], capture_output=True, text=True).stdout.split("\n")
        if " " in line)
    roots = list(dict.fromkeys(_search_dirs("cc", "c") + _search_dirs("c++", "c++")))
    entries, notes = [{"path": ".", "package": project}], {"search_dirs": roots, "mixed": [], "renamed": {}}
    for root in roots:
        for here, _dirs, names in os.walk(root):
            votes = collections.Counter(owner for name in names
                                        for owner in owners.get(os.path.realpath(os.path.join(here, name)), ()))
            if not votes:
                continue
            owner, count = votes.most_common(1)[0]
            version = versions.get(owner, "unknown")
            package = f"{_clean(owner)}@{_clean(version)}"
            if f"{owner}@{version}" != package:
                notes["renamed"][f"{owner} {version}"] = package
            if len(votes) > 1:
                notes["mixed"].append({"path": here, "package": owner, "files": count,
                                       "others": dict(votes.most_common()[1:])})
            entries.append({"path": here, "package": package})
    return entries, notes


def index(project_dir: Path, work_dir: Path, files: list[str] | None = None, *, project: str = "project@0",
          configure: tuple = ()) -> dict:
    """Configure and build a copy with CMake, then scip-clang over its compilation database."""
    work_dir.mkdir(parents=True, exist_ok=True)
    mirror = work_dir / "mirror"
    if not mirror.exists():
        shutil.copytree(project_dir, mirror, symlinks=True, ignore=shutil.ignore_patterns(".git"))
    before = {path.relative_to(mirror).as_posix() for path in mirror.rglob("*") if path.is_file()}
    env, runs = dict(os.environ), []
    runs.append({"step": "configure", **scip_graph.measured(
        ["cmake", "-S", ".", "-B", "build", "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON", "-DCMAKE_BUILD_TYPE=Debug",
         *configure], str(mirror), env, 1800)})
    runs.append({"step": "build", **scip_graph.measured(["cmake", "--build", "build", "-j", "4"], str(mirror),
                                                        env, 3600)})
    after = {path.relative_to(mirror).as_posix() for path in mirror.rglob("*") if path.is_file()}
    entries, notes = package_map(project)
    package_path = work_dir / "package-map.json"
    package_path.write_text(json.dumps(entries, indent=1) + "\n", encoding="utf-8")
    compdb = mirror / "build/compile_commands.json"
    help_text = subprocess.run([BINARY, "--help"], capture_output=True, text=True)
    log = work_dir / "scip-clang.log"
    runs.append({"step": "index", **scip_graph.measured(
        ["sh", "-c", f"{BINARY} --compdb-path={compdb} --package-map-path={package_path} "
                     f"--jobs=4 --show-compiler-diagnostics > {log} 2>&1"], str(mirror), env, 3600)})
    output = work_dir / "index.scip"
    if (mirror / "index.scip").is_file():
        shutil.move(mirror / "index.scip", output)
    runs[-1]["index_bytes"] = output.stat().st_size if output.is_file() else 0
    if compdb.is_file():
        shutil.copyfile(compdb, work_dir / "compile_commands.json")
    text = log.read_text(encoding="utf-8", errors="replace") if log.is_file() else ""
    runs[-1]["diagnostics"] = {
        "errors": len(re.findall(r": (?:fatal )?error: ", text)), "warnings": len(re.findall(r": warning: ", text)),
        "error_examples": list(dict.fromkeys(re.findall(r"\S+: (?:fatal )?error: .*", text)))[:8],
        "tail": text[-2000:]}
    return {"indexes": [[str(output), ""]] if output.is_file() else [], "runs": runs,
            "indexer": scip_graph.indexer("scip-clang", VERSION, runs), "help": help_text.stdout[-6000:],
            "package_map": {"entries": len(entries), **notes},
            "removed_by_build": sorted(before - after), "created_by_build": len(after - before)}


def compiled_files(compdb: Path, root: str) -> collections.Counter:
    """Checkout-relative files of the compilation database, with how many commands compile each."""
    out = collections.Counter()
    for entry in json.loads(Path(compdb).read_text(encoding="utf-8")):
        path = Path(entry["directory"], entry["file"]).as_posix()
        path = os.path.normpath(path).replace("\\", "/")
        out[path[len(root) + 1:] if path.startswith(root + "/") else path] += 1
    return out


def missing(index, rels: list[str], compiled: dict = (), removed: list = ()) -> dict:
    """Why a C or C++ file of the perimeter has no document."""
    reasons = {}
    for rel in rels:
        if rel in removed:
            reasons[rel] = "removed from the copy by the build's configure step"
        elif rel in compiled:
            reasons[rel] = "compiled, yet no document in the index"
        elif Path(rel).suffix.lower() in C_SUFFIXES | CPP_SOURCES:
            reasons[rel] = "no compile command: not built by the default configuration"
        else:
            reasons[rel] = "header no indexed translation unit includes in an active branch"
    return reasons


# ---------------------------------------------------------------------------------------------------------
# Syntax: what the Daodan snapshot would give if it read C and C++


def _parser(language: str):
    from tree_sitter_language_pack import get_parser
    return get_parser(language)


def _innermost(node):
    while node is not None and node.type == "qualified_identifier":
        node = node.child_by_field_name("name")
    if node is not None and node.type in ("template_function", "template_method", "template_type"):
        node = node.child_by_field_name("name")
    return node if node is not None and node.type in NAMES else None


def _function_name(declarator):
    """The name of a function declarator chain; None for a variable or a function pointer."""
    node = declarator
    while node is not None and node.type in ("pointer_declarator", "reference_declarator", "attributed_declarator",
                                             "init_declarator"):  # `f() = 0`, `= default`, `= delete`
        node = node.child_by_field_name("declarator") or (node.named_children[-1] if node.named_children else None)
    if node is None or node.type != "function_declarator":
        return None
    return _innermost(node.child_by_field_name("declarator"))


def _places(node) -> list[tuple[int, int]]:
    """`(line, byte column)` where an indexer may start the name: the node, and the identifier of `~Name`."""
    out = [(node.start_point[0] + 1, node.start_point[1])]
    if node.type == "destructor_name" and node.named_children:
        out.append((node.named_children[0].start_point[0] + 1, node.named_children[0].start_point[1]))
    return out


def _callee(function):
    """`(name node, shape)` of a call's callee, `(None, shape)` without a name."""
    shape = None
    while function is not None and function.type in ("parenthesized_expression", "pointer_expression"):
        if function.type == "pointer_expression":
            operator = function.child_by_field_name("operator")
            if operator is None or operator.type != "*":
                break
            function, shape = function.child_by_field_name("argument"), "dereference"
        else:
            function = function.named_children[0] if function.named_children else None
            shape = shape or "parenthesized"  # a call through `(f)`, or a C cast `(T)(x)` the syntax cannot tell
    if function is None:
        return None, shape or "none"
    if function.type == "identifier":
        return function, shape or "identifier"
    if function.type == "qualified_identifier":
        return _innermost(function), shape or "qualified"
    if function.type == "template_function":
        return _innermost(function), shape or "template"
    if function.type == "field_expression":
        return _innermost(function.child_by_field_name("field")), shape or "member"
    return None, function.type


class Syntax:
    """The declarations, call sites, bodies and preprocessor branches of one file."""

    def __init__(self, root: Path, rel: str, language: str):
        self.rel, self.language = rel, language
        self.source = (Path(root) / rel).read_bytes()
        blanked = self.source
        for pattern in ANNOTATIONS:
            blanked = pattern.sub(lambda m: m.group(0)[:m.start(1) - m.start(0)] + b" " * len(m.group(1))
                                  + m.group(0)[m.end(1) - m.start(0):], blanked)
        self.tree = _parser(language).parse(blanked)
        self.declared, self.calls, self.prototypes, self.lambdas = {}, [], [], []
        self.branches, self.bodies, self.counts = [], [], collections.Counter()
        self.counts["annotation macro blanked"] = sum(len(pattern.findall(self.source)) for pattern in ANNOTATIONS)
        stack = [self.tree.root_node]
        while stack:
            node = stack.pop()
            self._visit(node)
            stack.extend(reversed(node.children))

    def _declare(self, node, kind: str) -> None:
        name = node.text.decode("utf-8", errors="replace")
        line = node.start_point[0] + 1
        identity = f"{self.rel}:{line} {name}" + (" (declaration)" if kind == "declaration" else "")
        for place in _places(node):
            self.declared.setdefault(place, identity)
        if kind == "declaration":
            self.prototypes.append((node, identity))

    def _visit(self, node) -> None:
        kind = node.type
        if kind in COUNTED:
            self.counts[kind] += 1
        if kind == "function_definition":
            name = _function_name(node.child_by_field_name("declarator"))
            if name is not None:
                self._declare(name, "function")
                self.bodies.append((name, node))
        elif kind in ("declaration", "field_declaration"):
            for declarator in node.children_by_field_name("declarator"):
                name = _function_name(declarator)
                if name is not None:
                    self._declare(name, "declaration")
        elif kind in ("class_specifier", "struct_specifier", "union_specifier"):
            name = node.child_by_field_name("name")
            if node.child_by_field_name("body") is not None and name is not None:
                self._declare(_innermost(name) or name, "class")
                self.bodies.append((_innermost(name) or name, node))
        elif kind == "lambda_expression":
            line = node.start_point[0] + 1
            self.declared.setdefault((line, node.start_point[1]), f"{self.rel}:{line} lambda")
            self.lambdas.append(node)
        elif kind == "call_expression":
            function = node.child_by_field_name("function")
            name, shape = _callee(function)
            # `static_cast<T>(x)`, `int(x)` and `unsigned(x)` are casts, not calls.
            text = name.text.decode() if name is not None else ""
            if not (shape == "template" and text in CASTS) and text not in ("unsigned", "signed")                     and shape not in ("primitive_type", "sized_type_specifier"):
                self.calls.append((node, name, shape, name))
            else:
                self.counts["cast written as a call"] += 1
        elif kind == "new_expression":  # the indexer names the constructor where the type starts
            kind_node = node.child_by_field_name("type")
            if kind_node is not None and kind_node.type != "primitive_type":
                self.calls.append((node, _innermost(kind_node), "new", kind_node))
        elif kind in BRANCHES:
            self.branches.append(node)

    def branch(self, line: int) -> tuple[int, int] | None:
        """`(first line, last line)` of the innermost preprocessor branch holding a line, its directives left out."""
        best = None
        for node in self.branches:
            start, end = node.start_point[0] + 1, node.end_point[0] + 1
            alternative = node.child_by_field_name("alternative")
            if alternative is not None:
                end = alternative.start_point[0]
            if start < line <= end and (best is None or start >= best[0] - 1):
                best = (start + 1, end)
        return best


class SyntaxSnapshot:
    """What `scip_graph.Traversal` and `build` ask of a snapshot, from tree-sitter, for C and C++ files."""

    def __init__(self, root: Path, files: list[str], primary: str, generated: list[str] = ()):
        self.root, self.primary, self.generated = Path(root), primary, set(generated)
        self.languages = {rel: language_of(rel, primary) for rel in files}
        self.inventory = sorted(files)
        self.paths = {rel: self.root / rel for rel in files}
        self.checkout = {rel: rel for rel in files}
        self.rel = dict(self.checkout)
        self._syntax: dict[str, Syntax | None] = {}

    def syntax(self, rel: str) -> Syntax | None:
        if rel not in self._syntax:
            language, path = language_of(rel, self.primary), self.root / rel
            self._syntax[rel] = Syntax(self.root, rel, language) if language and path.is_file() else None
        return self._syntax[rel]

    def grade(self, rel: str, line: int, column: int | None) -> tuple[str, str | None]:
        if rel in self.generated:  # written by the build inside the copy: the project's, not in the checkout
            return "value", "generated by the build"
        if column is None or rel not in self.paths:
            return "outside", None
        found = self.syntax(rel)
        identity = found.declared.get((line, column)) if found else None
        return ("callable", identity) if identity else ("value", "not a function, method or class")

    def function_at(self, rel: str, line: int, column: int) -> str | None:
        found = self.syntax(rel) if rel in self.paths else None
        return found.declared.get((line, column)) if found else None

    def references(self, language: str):
        """The call sites of a language's files: `call`, unresolved, the callee's name and its shape as reason."""
        for rel in self.inventory:
            if self.languages[rel] != language or self.syntax(rel) is None:
                continue
            for node, name, shape, at in self.syntax(rel).calls:
                at = at if name is not None else node
                line, column = at.start_point[0] + 1, at.start_point[1]
                parts = [name.text.decode("utf-8", errors="replace")] if name is not None else []
                yield (f"{rel}:{line}:{column}", rel, "call", "unresolved", None,
                       (line, column, at.end_point[0] + 1, at.end_point[1]), parts, shape)

    def callee(self, rel: str, span: tuple, parts: list) -> tuple[int, int] | None:
        return (span[0], span[1]) if parts else None


# ---------------------------------------------------------------------------------------------------------
# Hops


def _at(index, rel: str, line: int, byte_column: int, definition: bool | None = None) -> list:
    native = index.from_bytes(rel, line, byte_column)
    return [item for item in index.at.get((rel, line, native), ())
            if definition is None or item.definition == definition]


def declaration_hops(index, rel: str, syntax: Syntax) -> dict:
    """A function the index defines nowhere leads to its prototype in the project."""
    out = collections.defaultdict(list)
    for node, _identity in syntax.prototypes:
        line, column = node.start_point[0] + 1, node.start_point[1]
        for item in _at(index, rel, line, column, False):
            if item.key not in index.defs and "#local " not in item.key:
                out[item.key].append(((rel, line, column), "declaration"))
    return out


def lambda_hops_cpp(index, rel: str, syntax: Syntax) -> dict:
    """C++: a variable declared `auto` with a lambda leads to the lambda (its closure type is its own)."""
    out = collections.defaultdict(list)
    for node in syntax.lambdas:
        holder = node.parent
        if holder is None or holder.type != "init_declarator" or holder.child_by_field_name("value") != node:
            continue
        declaration = holder.parent
        kind = declaration.child_by_field_name("type") if declaration is not None else None
        name = holder.child_by_field_name("declarator")
        if kind is None or kind.type != "placeholder_type_specifier" or name is None or name.type != "identifier":
            continue
        for item in _at(index, rel, name.start_point[0] + 1, name.start_point[1], True):
            out[item.key].append(((rel, node.start_point[0] + 1, node.start_point[1]), "lambda"))
    return out


def hops(index, primary: str = "c") -> dict:
    """The adapter's hops over every C and C++ document of the index."""
    out = collections.defaultdict(list)
    for rel in index.documents:
        language = language_of(rel, primary)
        if not language or not (index.root / rel).is_file():
            continue
        syntax = Syntax(index.root, rel, language)
        for found in (declaration_hops(index, rel, syntax),
                      lambda_hops_cpp(index, rel, syntax) if language == "cpp" else {}):
            for key, items in found.items():
                out[key] += items
    return {key: list(dict.fromkeys(items)) for key, items in out.items()}


def enclose(index, snapshot: SyntaxSnapshot) -> int:
    """Give each definition of a function or class the range of its syntax node as enclosing range (the shared
    reader's `Occurrence.enclosing`, which scip-clang leaves empty). Returns how many it set."""
    done = 0
    for rel, occurrences in index.documents.items():
        found = snapshot.syntax(rel) if rel in snapshot.paths else None
        if found is None:
            continue
        spans = {}
        for name, node in found.bodies:
            (line, column), end = _places(name)[0], node.end_point
            spans[(line, index.from_bytes(rel, line, column))] = (
                node.start_point[0] + 1, index.from_bytes(rel, node.start_point[0] + 1, node.start_point[1]),
                end[0] + 1, index.from_bytes(rel, end[0] + 1, end[1]))
        for i, item in enumerate(occurrences):
            span = spans.get((item.line, item.start)) if item.definition and item.enclosing is None else None
            if span and None not in span:
                occurrences[i] = item._replace(enclosing=span)
                done += 1
    return done


def dedupe(index) -> int:
    """scip-clang writes one document per translation unit that compiles a file (a library built shared and
    static compiles each source twice, a header prototype is referenced once per includer): the shared reader
    appends them, so each occurrence is kept once. Returns how many it dropped."""
    dropped = 0
    for rel, occurrences in index.documents.items():
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
    """scip-clang writes columns as UTF-8 bytes without saying so (no position encoding, which the shared
    reader takes as UTF-16; checked by `byte_columns` and the fixtures' non-ASCII lines): every document is
    read in bytes. Returns how many documents it set."""
    for rel in index.documents:
        index.units[rel] = "utf-8"
    return len(index.documents)


def byte_columns(index) -> dict:
    """On lines with non-ASCII text, does the name at each occurrence read right as UTF-8 bytes or UTF-16 units?
    scip-clang writes no position encoding, which the shared reader takes as UTF-16."""
    counts = collections.Counter()
    for rel, occurrences in index.documents.items():
        for item in occurrences:
            text = index.line(rel, item.line)
            parts = scip_graph.split_symbol(scip_graph._global(item.key))
            items = scip_graph.descriptors(parts[4]) if parts else []
            if not text or text.isascii() or item.line != item.end_line or not items or not items[-1][0].isidentifier():
                continue
            raw, wanted = text.encode("utf-8"), items[-1][0]
            as_bytes = raw[item.start:item.end].decode("utf-8", errors="replace") == wanted
            units = text.encode("utf-16-le")[2 * item.start:2 * item.end].decode("utf-16-le", errors="replace") == wanted
            counts[f"bytes {as_bytes}, utf-16 {units}"] += 1
    return dict(counts)


def _last_name(key: str) -> str | None:
    parts = scip_graph.split_symbol(scip_graph._global(key))
    items = scip_graph.descriptors(parts[4]) if parts else []
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


def classifier(project: str):
    """`project` for the project's package, `namespace` for a namespace, the package any other symbol names."""
    name, version = project.split("@", 1)

    def classify(key: str):
        parts = scip_graph.split_symbol(scip_graph._global(key))
        if parts is None:
            return None
        items = scip_graph.descriptors(parts[4])
        if items and items[-1][1] == "namespace":
            return "namespace"
        stated = {"manager": parts[0], "package": parts[2], "version": parts[3].rstrip("$")}
        if (stated["package"], stated["version"]) == (name, version):
            return "project"
        return stated if stated["package"] != "." else {"manager": parts[0], "package": "(none)", "version": "-"}
    return classify


def refine(index, graph: dict) -> None:
    """An edge to a symbol with bodies at several places is `uncertain`: each place is a candidate."""
    places = {}
    for edge in graph["edges"]:
        if edge["end"] != "project-callable" or edge["chain"]:
            continue
        key = edge["to"]
        if key not in places:
            places[key] = sorted({f"{rel}:{occurrence.line}" for rel, occurrence in index.defs.get(key, ())})
        if len(places[key]) > 1:
            edge["uncertain"] = {"reason": "one symbol defined at several places", "candidates": places[key]}


def roles(path: Path) -> dict:
    """What the shared reader drops: occurrence role bits and relationship kinds, counted from the raw index."""
    bits, relationships = collections.Counter(), collections.Counter()
    names = {1: "definition", 2: "import", 4: "write", 8: "read", 16: "generated", 32: "test", 64: "forward-definition"}
    flags = {2: "is_reference", 3: "is_implementation", 4: "is_type_definition", 5: "is_definition"}

    def information(data):
        for number, wire, value in scip_graph._fields(data):
            if number == 4 and wire == 2:
                for field, kind, item in scip_graph._fields(value):
                    if field in flags and kind == 0 and item:
                        relationships[flags[field]] += 1

    for number, wire, value in scip_graph._fields(Path(path).read_bytes()):
        if number == 3 and wire == 2:
            relationships["external symbols"] += 1
            information(value)
        if number != 2 or wire != 2:
            continue
        for field, kind, item in scip_graph._fields(value):
            if field == 2 and kind == 2:
                role = next((int(v) for f, k, v in scip_graph._fields(item) if f == 3 and k == 0), 0)
                bits.update(name for bit, name in names.items() if role & bit)
                bits["none"] += role == 0
            elif field == 3 and kind == 2:
                information(item)
    return {"roles": dict(bits), "relationships": dict(relationships)}
