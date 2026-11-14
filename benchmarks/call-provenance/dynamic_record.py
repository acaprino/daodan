"""Exact recorder of the calls a Python run executes, on sys.monitoring (Python 3.12+).

    python dynamic_record.py site <dir>
    PYTHONPATH=<dir> DYN_ROOT=<project root> DYN_OUT=<out>-%p.json python -m pytest

`site` writes <dir>/sitecustomize.py, which loads this file and then the sitecustomize it shadows. Loaded this
way the recorder starts before any project code, in every interpreter that inherits the environment
(subprocesses included), and changes neither the project nor its environment. `-X` has no option that loads a
module; a pytest plugin would start later and only under pytest.

Two events. CALL gives the code object, the instruction offset and the object called; PY_START a Python
function that starts, counted only when its caller's current instruction is not a call: a property, a dunder
such as __lt__, __enter__ or __hash__, a descriptor's __get__. A site is an instruction in a file under DYN_ROOT.
`co_positions` gives each instruction the span of its expression (start and end line, UTF-8 columns), so two
calls on one line are two sites; the offset alone does not say where on the line. On exit each site is placed
with `ast` at the name token of the call whose span it is and written to DYN_OUT in the shape of
dynamic_record.js, "exact": true, lines from 0, columns in bytes. "role" says how the site is reached: "call",
"decorator" (applying what a decorator call returned), "WITH_EXIT" (a with block's exit, a call instruction on
the context expression in CPython 3.12-3.13), the instruction's name for an implicit call (LOAD_ATTR,
COMPARE_OP, BEFORE_WITH...), or the syntax node when no call node has the span (ClassDef for __build_class__,
GeneratorExp). A callee is its definition (file, line, qualified name) for project code, else its module with
the package and version; C functions carry "native": true; a function made by functools.wraps carries "wraps",
the function it wraps; a mock carries "mock": true.

Not recorded: a function called back by a C function (sorted's key, a class's __init__ under the class call:
the site keeps the C callee or the class), attribute access that runs no Python code (__slots__, instance and
module attributes), a generator's steps after its call, imports, code without a file (doctests, exec of a
string), processes started with -I or -E or without this environment, and anything after os._exit.
"""
from __future__ import annotations

import os
import sys

TOOL_IDS = (4, 3, 5)
CALLS = {"CALL", "CALL_KW", "CALL_FUNCTION_EX", "LOAD_SUPER_ATTR"}  # CALL reports their callee
NOT_CALLS = {"IMPORT_NAME", "IMPORT_FROM", "CALL_INTRINSIC_1", "CALL_INTRINSIC_2"}
STEPS = 0x20 | 0x80 | 0x200  # CO_GENERATOR, CO_COROUTINE, CO_ASYNC_GENERATOR: a start is a first step
SITE = '''# Written by dynamic_record.py site: loads the recorder, then the sitecustomize this file shadows.
import importlib.machinery
import importlib.util
import os
import sys


def _load(name, spec):
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)


_load("daodan_dynamic_record", importlib.util.spec_from_file_location("daodan_dynamic_record", {recorder!r}))
_shadowed = importlib.machinery.PathFinder.find_spec(
    "sitecustomize", [p for p in sys.path if os.path.abspath(p or os.curdir) != {folder!r}])
if _shadowed is not None:
    _load("sitecustomize", _shadowed)
'''


def install(root: str, out: str) -> None:
    import atexit
    import functools
    import types

    monitoring = sys.monitoring
    tool = next((i for i in TOOL_IDS if monitoring.get_tool(i) is None), None)
    if tool is None:
        return
    monitoring.use_tool_id(tool, "daodan-dynamic-record")
    events = monitoring.events
    DISABLE = monitoring.DISABLE
    prefix = os.path.normcase(os.path.abspath(root)) + os.sep
    skip = [os.path.normcase(os.path.abspath(p)) + os.sep for p in {sys.prefix, sys.base_prefix}]
    skip.append(os.path.normcase(os.path.abspath(__file__)))
    owned: dict = {}            # code -> path from the root, or None
    keys: dict = {}             # callee key -> index
    callees: list = []          # index -> (key, module of a Python function)
    calls: dict = {}            # (code, offset) -> set of callee indexes
    implicit: dict = {}         # (code, offset) -> set of callee indexes
    counts = {"calls": 0, "starts": 0, "errors": 0}
    getframe = sys._getframe
    Function, Method, Builtin = types.FunctionType, types.MethodType, types.BuiltinFunctionType
    descriptors = (types.MethodDescriptorType, types.WrapperDescriptorType, types.ClassMethodDescriptorType)
    opnames: dict = {}          # code -> {offset: opname}

    def inside(name):
        """The path of a file from the root, None outside the project."""
        if not name or name.startswith("<"):
            return None
        path = os.path.abspath(name)
        folded = os.path.normcase(path)
        if not folded.startswith(prefix) or any(folded.startswith(p) for p in skip) \
                or "site-packages" in folded or "dist-packages" in folded:
            return None
        return path[len(prefix):].replace(os.sep, "/")

    def relative(code):
        rel = owned.get(code, False)
        if rel is False:
            rel = owned[code] = inside(code.co_filename)
        return rel

    def key_of(fn, depth=0):
        kind = type(fn)
        if kind is Function:
            wrapped = fn.__dict__.get("__wrapped__")
            return ("code", fn.__code__, key_of(wrapped, depth + 1) if wrapped is not None and depth < 8 else None)
        if kind is Method:
            return key_of(fn.__func__, depth)
        if kind is Builtin:
            owner = fn.__self__
            module = fn.__module__
            if module is None and owner is not None and not isinstance(owner, types.ModuleType):
                module = type(owner).__module__
            return ("c", module, fn.__qualname__)
        if isinstance(fn, type):
            return ("class", fn)
        if kind is functools.partial:
            return ("partial", key_of(fn.func, depth + 1) if depth < 8 else None)
        if kind in descriptors:
            return ("c", fn.__objclass__.__module__, fn.__qualname__)
        if kind is types.MethodWrapperType:
            return ("c", type(fn.__self__).__module__, fn.__qualname__)
        return ("instance", kind.__module__, kind.__qualname__)

    def add(table, site, key, fn):
        index = keys.get(key)
        if index is None:
            index = keys[key] = len(callees)
            callees.append((key, getattr(fn, "__module__", None) if type(fn) in (Function, Method) else None))
        seen = table.get(site)
        if seen is None:
            table[site] = {index}
        else:
            seen.add(index)

    def on_call(code, offset, fn, arg0):
        try:
            if relative(code) is None:
                return DISABLE
            counts["calls"] += 1
            add(calls, (code, offset), key_of(fn), fn)
        except Exception:
            counts["errors"] += 1
        return None

    def on_start(code, offset):
        try:
            if code.co_flags & STEPS:
                return None
            caller = getframe(1).f_back
            if caller is None or relative(caller.f_code) is None:
                return None
            names = opnames.get(caller.f_code)
            if names is None:
                import dis
                names = opnames[caller.f_code] = {i.offset: i.opname for i in dis.get_instructions(caller.f_code)}
            name = names.get(caller.f_lasti)
            if name in CALLS or name in NOT_CALLS:
                return None
            counts["starts"] += 1
            add(implicit, (caller.f_code, caller.f_lasti), ("code", code, None), None)
        except Exception:
            counts["errors"] += 1
        return None

    def flush():
        monitoring.set_events(tool, 0)
        try:
            write(out.replace("%p", str(os.getpid())), root, inside, relative, callees, calls, implicit, counts)
        finally:
            monitoring.free_tool_id(tool)

    monitoring.register_callback(tool, events.CALL, on_call)
    monitoring.register_callback(tool, events.PY_START, on_start)
    monitoring.set_events(tool, events.CALL | events.PY_START)
    atexit.register(flush)


class Places:
    """Each project file's syntax: nodes by span, decorators, definitions."""

    def __init__(self, root: str):
        self.root = root
        self.files: dict = {}

    def file(self, rel: str):
        if rel not in self.files:
            import ast
            import collections
            spans, decorators, definitions, text = collections.defaultdict(list), {}, [], []
            try:
                with open(os.path.join(self.root, rel), encoding="utf-8") as stream:
                    source = stream.read()
                text = source.split("\n")
                tree = ast.parse(source)
            except (OSError, SyntaxError, ValueError):
                tree = None
            for node in ast.walk(tree) if tree else ():
                if getattr(node, "end_col_offset", None) is None:
                    continue
                spans[(node.lineno, node.col_offset, node.end_lineno, node.end_col_offset)].append(node)
                # An attribute on a later line than its value moves the instruction's start to the name.
                member = node.func if isinstance(node, ast.Call) else node
                if isinstance(member, ast.Attribute) and member.end_lineno != node.lineno:
                    spans[(member.end_lineno, member.end_col_offset - len(member.attr), node.end_lineno,
                           node.end_col_offset)].append(node)
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    for decorator in node.decorator_list:
                        decorators[(decorator.lineno, decorator.col_offset, decorator.end_lineno,
                                    decorator.end_col_offset)] = decorator
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda,
                                     ast.GeneratorExp)):
                    definitions.append(node)
            self.files[rel] = (spans, decorators, definitions, text)
        return self.files[rel]

    def definition(self, rel: str, name: str, first: int):
        """(line, column) of the definition `name` whose first line, decorators included, is `first`."""
        import ast
        for node in self.file(rel)[2]:
            start = min([node.lineno] + [d.lineno for d in getattr(node, "decorator_list", ())])
            found = (getattr(node, "name", None) == name if hasattr(node, "name") else
                     name == "<lambda>" if isinstance(node, ast.Lambda) else name == "<genexpr>")
            if found and start == first:
                return node.lineno, node.col_offset
        return first, 0


def token(node) -> tuple:
    """(line, byte column, name) of the name that a call or a member access names."""
    import ast
    func = node.func if isinstance(node, ast.Call) else node
    if isinstance(func, ast.Name):
        return func.lineno, func.col_offset, func.id
    if isinstance(func, ast.Attribute):
        return func.end_lineno, func.end_col_offset - len(func.attr.encode("utf-8")), func.attr
    return node.lineno, node.col_offset, ""


def write(path, root, inside, relative, callees, calls, implicit, counts) -> None:
    import ast
    import dis
    import importlib.metadata
    import json
    import sysconfig

    places = Places(os.path.abspath(root))
    stdlib = {os.path.normcase(os.path.abspath(sysconfig.get_paths()[k])) + os.sep for k in ("stdlib", "platstdlib")}
    version = "%d.%d.%d" % sys.version_info[:3]
    packages: dict = {}

    def package_of(file):
        if not packages:
            packages[None] = None
            for dist in importlib.metadata.distributions():
                for item in dist.files or ():
                    packages[os.path.normcase(os.path.abspath(dist.locate_file(item)))] = (
                        dist.metadata["Name"], dist.version)
        return packages.get(os.path.normcase(os.path.abspath(file)))

    def where(module, file=None) -> dict:
        if file and not file.startswith("<"):
            folded = os.path.normcase(os.path.abspath(file))
            if any(folded.startswith(p) for p in stdlib) and "site-packages" not in folded:
                return {"kind": "runtime", "module": module, "version": version}
            found = package_of(file)
            if found:
                return {"kind": "package", "module": module, "package": found[0], "version": found[1]}
            return {"kind": "other", "module": module or file}
        if file and file.startswith("<frozen "):
            return {"kind": "runtime", "module": module or file[8:-1], "version": version}
        top = (module or "").split(".")[0]
        if top == "builtins" or top in sys.stdlib_module_names:
            return {"kind": "runtime", "module": module, "version": version}
        loaded = sys.modules.get(module or "") or sys.modules.get(top)
        if getattr(loaded, "__file__", None):
            return where(module, loaded.__file__)
        return {"kind": "other", "module": module}

    def module_of(file):
        for name, module in list(sys.modules.items()):
            if getattr(module, "__file__", None) and os.path.abspath(module.__file__) == os.path.abspath(file):
                return name
        return None

    def describe(key, module=None) -> dict:
        kind = key[0]
        if kind == "code":
            code = key[1]
            rel = relative(code)
            if rel is not None:
                line, column = places.definition(rel, code.co_name, code.co_firstlineno)
                out = {"kind": "project", "file": rel, "name": code.co_qualname, "line": line - 1,
                       "column": column, "type": "function"}
            else:
                # The module of the code's file: functools.wraps copies __module__ from the wrapped function.
                out = {**where(module_of(code.co_filename) or module, code.co_filename), "name": code.co_qualname,
                       "line": code.co_firstlineno - 1, "type": "function"}
            out["native"] = False
            if key[2] is not None:
                out["wraps"] = describe(key[2])
            return out
        if kind == "class":
            cls = key[1]
            loaded = sys.modules.get(cls.__module__)
            file = getattr(loaded, "__file__", None)
            first = cls.__dict__.get("__firstlineno__")
            if first and not file:  # a module imported under another name: the file of one of its methods
                file = next((getattr(getattr(v, "__func__", v), "__code__", None).co_filename
                             for v in cls.__dict__.values()
                             if getattr(getattr(v, "__func__", v), "__code__", None) is not None), None)
            rel = inside(file)
            if rel is not None and first:
                line, column = places.definition(rel, cls.__name__, first)
                return {"kind": "project", "file": rel, "name": cls.__qualname__, "line": line - 1,
                        "column": column, "type": "class", "native": False}
            return {**where(cls.__module__, file if first else None), "name": cls.__qualname__, "type": "class",
                    "native": not first}
        if kind == "c":
            return {**where(key[1]), "name": key[2], "type": "builtin", "native": True}
        if kind == "partial":
            out = {**where("functools"), "name": "partial", "type": "instance", "native": True}
            if key[1] is not None:
                out["wraps"] = describe(key[1])
            return out
        out = {**where(key[1]), "name": key[2], "type": "instance", "native": False}
        if (key[1] or "").startswith(("unittest.mock", "pytest_mock")):
            out["mock"] = True
        return out

    described = [describe(key, module) for key, module in callees]
    merged: dict = {}
    unplaced = {"no-position": 0, "no-node": 0}
    for table, implicit_table in ((calls, False), (implicit, True)):
        by_code: dict = {}
        for code, offset in table:
            by_code.setdefault(code, []).append(offset)
        for code, offsets in by_code.items():
            rel = relative(code)
            positions = list(code.co_positions())
            instructions = list(dis.get_instructions(code))
            before = {}
            previous = []
            for instruction in instructions:
                before[instruction.offset] = (instruction, previous[-1] if previous else None,
                                              # a with block's exit: __exit__(None, None, None)
                                              instruction.opname == "CALL" and instruction.arg == 2 and
                                              [(p.opname, p.argval) for p in previous[-3:]] ==
                                              [("LOAD_CONST", None)] * 3)
                if instruction.opname not in ("EXTENDED_ARG", "NOP", "CACHE"):
                    previous.append(instruction)
            spans, decorators = places.file(rel)[:2]
            for offset in offsets:
                span = positions[offset // 2] if offset // 2 < len(positions) else (None,) * 4
                if span[0] is None or span[2] is None:
                    unplaced["no-position"] += 1
                    continue
                key = (span[0], span[2], span[1], span[3])
                instruction, prior, exit_call = before.get(offset, (None, None, False))
                op = instruction.opname if instruction else ""
                nodes = spans.get(key, [])
                role = "call"
                node = None
                decorator = decorators.get(key)
                if implicit_table:
                    role = op
                    node = next((n for n in nodes if isinstance(n, ast.Attribute)), None)
                elif exit_call:
                    role = "WITH_EXIT"
                elif op == "LOAD_SUPER_ATTR":
                    # super() is called by the instruction that loads super().name: its span is the attribute's.
                    member = next((n for n in nodes if isinstance(n, ast.Attribute)), None)
                    node = member.value if member is not None and isinstance(member.value, ast.Call) else None
                elif decorator is not None and not isinstance(decorator, ast.Call):
                    node = decorator  # a bare decorator: its application is the call of its name
                elif decorator is not None and op == "CALL" and instruction.arg == 0 and prior is not None \
                        and prior.opname in ("MAKE_FUNCTION", "SET_FUNCTION_ATTRIBUTE", "CALL", "CALL_KW"):
                    role = "decorator"  # the application of what the decorator's call returned
                else:
                    node = next((n for n in nodes if isinstance(n, ast.Call)), None)
                    if node is None:
                        unplaced["no-node"] += 1
                        role = type(nodes[0]).__name__ if nodes else "unplaced"
                line, column, name = token(node) if node is not None else (key[0], key[1], "")
                site = (rel, line - 1, column, name, role)
                entry = merged.setdefault(site, {"end": list(key), "callees": set()})
                entry["callees"].update(table[(code, offset)])
    sites = [{"file": rel, "line": line, "column": column, "name": name, "role": role, "end": entry["end"],
              "callees": [described[i] for i in sorted(entry["callees"])]}
             for (rel, line, column, name, role), entry in sorted(merged.items(), key=lambda item: str(item[0]))]
    stats = {"sites": len(sites), "callees": len(described), **counts, **unplaced}
    with open(path, "w", encoding="utf-8") as stream:
        json.dump({"exact": True, "python": version, "stats": stats, "sites": sites}, stream)


def write_site(folder: str) -> None:
    folder = os.path.abspath(folder)
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, "sitecustomize.py"), "w", encoding="utf-8", newline="\n") as stream:
        stream.write(SITE.format(recorder=os.path.abspath(__file__), folder=folder))


if __name__ == "__main__":
    if sys.argv[1:2] == ["site"] and len(sys.argv) == 3:
        write_site(sys.argv[2])
    else:
        sys.exit("usage: dynamic_record.py site <dir>")
elif os.environ.get("DYN_OUT") and os.environ.get("DYN_ROOT") and hasattr(sys, "monitoring"):
    install(os.environ["DYN_ROOT"], os.environ["DYN_OUT"])
