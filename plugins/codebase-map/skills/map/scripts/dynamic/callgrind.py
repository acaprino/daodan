"""Valgrind's Callgrind as the recorder of native code's tests: what the Rust and the C and C++ observers share.

Callgrind runs the compiled tests as they are, with no rebuild, and counts every call instruction the program
executes and the function it enters, whatever the call goes through (a function pointer, a trait object, a
virtual method): valgrind.org/docs/manual/cl-manual.html. It needs no ptrace, no perf event and no kernel
tracing (it runs the program in its own process), so an unprivileged container runs it; only Memcheck needs
the C library's symbols (`m_redir.c`), and Callgrind is not Memcheck. Valgrind is adopted as Ubuntu builds it
for the image's release (`VALGRIND`: the image is Ubuntu 24.04), pinned by version and sha256, GPL-2.0-or-later,
unpacked in the preparation and never installed in the system. Its cost: a run is tens of times slower, and its
threads run one at a time. It maps a program's main stack down to one page below its arguments
(initimg-linux.c, `setup_client_stack`) and grows it on a fault below only when the kernel reports SEGV_MAPERR,
as Linux does (m_signals.c, `extend_stack_if_appropriate`); no option changes either. The gVisor of a Modal
Sandbox reports SEGV_ACCERR there (`--trace-signals`, measured on 16 November 2026; gVisor's KVM platform does
so for any write, pkg/sentry/platform/kvm/machine_amd64.go), and --main-stacksize, --max-stackframe,
--aspace-minaddr or the stack's ulimit change nothing: a program dies at its start, in ld.so, once its main
stack outgrows those pages, and `recorder_failed` and `gaps` say why (`_cause`). Modal's Functions (measured),
Docker, Podman and Kiri (runc, Linux's semantics) report SEGV_MAPERR.

Each traced process writes `callgrind.out.<pid>` (`OPTIONS`); after the tests `callgrind_sites.py`, in the
container, turns them into call sites with their columns, which Callgrind does not write, by the objects' DWARF
line tables (pyelftools, `PYELFTOOLS`, public domain). `read`, on the host, places each site on the project's
source as tree-sitter reads it, as the snapshot does: a site is the call expression a compiler's column names
(its start, its callee's name or its arguments: compilers differ), at its callee's last name; a callee of the
project is the function or closure whose header holds the line it was entered at (with none there, its name on
that line and no column), and any other is external, with the package its file is in. Valgrind runs with no
gdbserver (`--vgdb=no`: no FIFO, no polling). Not seen, and counted by cause: a call the compiler inlined (no call
instruction), a call written inside a macro's arguments or made by an operator or a destructor (no call
expression there: Rust's `assert_eq!(f(x), y)` is one), code without line tables.
"""
from __future__ import annotations

import collections
import json
import posixpath
import re
from pathlib import Path

import preparation

VALGRIND_VERSION = "3.22.0"
VALGRIND = ("https://launchpad.net/ubuntu/+archive/primary/+files/valgrind_3.22.0-0ubuntu3_amd64.deb",
            "744e081e5cf3d5c598b499dbb7d2250ea3f2869dde4a4d7b231fe6114f347d7d", "valgrind.deb")  # Ubuntu noble
PYELFTOOLS = ("https://files.pythonhosted.org/packages/46/2a/f9697576603dae937727827505a6126a066affb227034e77e6f9"
              "068910da/pyelftools-0.33-py3-none-any.whl",
              "f215ad5f47d3f1373a21496a6c9e0707c622840d0622f23ff7ce08678b020036", "pyelftools.whl")
READER = Path(__file__).with_name("callgrind_sites.py")
IN, T, WORK = preparation.IN, preparation.T, "/work"
VALGRIND_BIN = f"{T}/valgrind/usr/bin/valgrind"
TRACES = "/tmp/daodan-callgrind"  # the traced processes' outputs: large, read in the container and left there
OPTIONS = ["-q", "--tool=callgrind", "--vgdb=no", "--dump-instr=yes", "--compress-strings=no", "--compress-pos=no",
           "--trace-children=yes", f"--trace-children-skip=/usr/*,/bin/*,/sbin/*,{T}/*",  # the system's, Daodan's
           f"--callgrind-out-file={TRACES}/callgrind.out.%p", f"--log-file={TRACES}/valgrind.%p.log"]
SETUP = (f"{{ mkdir -p {T}/valgrind && dpkg-deb -x {IN}/valgrind.deb {T}/valgrind ; }} >&2"
         f" || echo 'DAODAN-MISSING valgrind@{VALGRIND_VERSION}' >&2")
SYMBOLIZE = 900  # the seconds the reading of the traces may take
LANGUAGE = {".rs": "rust", ".c": "c", **{suffix: "cpp" for suffix in (
    ".cc", ".cpp", ".cxx", ".c++", ".h", ".hh", ".hpp", ".hxx", ".h++", ".inl", ".ipp", ".tpp", ".cppm", ".ixx")}}
CALLABLES = {"function_item": "", "function_definition": "", "closure_expression": "(closure)",
             "lambda_expression": "(lambda)"}
NAMED = {"scoped_identifier": "name", "field_expression": "field", "qualified_identifier": "name",
         "generic_function": "function", "template_function": "name", "template_method": "name"}
DECLARATORS = ("identifier", "field_identifier", "qualified_identifier", "destructor_name", "operator_name")
RUSTC = re.compile(r"^/rustc/[0-9a-f]+/library/([^/]+)/")
REGISTRY = re.compile(r"/registry/src/[^/]+/([^/]+)-(\d+\.\d+\.\d+[^/]*)/")
CHECKOUT = re.compile(r"/git/checkouts/([^/]+)-[0-9a-f]+/[^/]+/")
OUTSIDE, NOT_READ, NOT_AT_CALL, AMBIGUOUS = ("made outside the project", "a file tree-sitter does not read",
                                             "not at a call expression", "more than one call at the position")
ACCERR = "Bad permissions for mapped region"  # how Valgrind words a fatal SIGSEGV whose code is SEGV_ACCERR


def inputs() -> dict:
    """What the copy carries: the reader of the traces, Valgrind and pyelftools, downloaded once and checked."""
    return {f"{IN}/{READER.name}": READER,
            **{f"{IN}/{name}": preparation.fetched(url, digest, name) for url, digest, name in (VALGRIND, PYELFTOOLS)}}


def recorder(out: str) -> list[str]:
    """The execution's lines before the tests: Valgrind from its unpacked folder, and a traced `true` that says
    whether it runs here (`recorder.code`, `recorder.log`)."""
    return [f"export VALGRIND_LIB=$(dirname \"$(find {T}/valgrind -name callgrind-amd64-linux | head -n 1)\")",
            f"mkdir -p {TRACES}", f"{{ uname -r; dmesg | head -n 1; }} > {out}/kernel 2>/dev/null",
            f"{VALGRIND_BIN} -q --tool=callgrind --vgdb=no --callgrind-out-file=/dev/null true"
            f" > {out}/recorder.log 2>&1",
            f"echo $? > {out}/recorder.code"]


def symbolize(out: str) -> list[str]:
    """The execution's lines after the tests: the traces read into `calls.json`, and what Valgrind said."""
    return [f"timeout {SYMBOLIZE} python3 -I {IN}/{READER.name} {IN}/pyelftools.whl {TRACES} {WORK}"
            f" {out}/calls.json > {out}/sites.log 2>&1",
            f"echo $? > {out}/sites.code",
            f"for f in {TRACES}/valgrind.*.log; do [ -s \"$f\" ] && head -n 5 \"$f\"; done"
            f" > {out}/valgrind.log 2>/dev/null"]


def gaps(back: Path) -> list[dict]:
    """What the recorder's own files say went wrong: the reading of the traces, Valgrind's messages."""
    out = []
    if _text(back / "sites.code").strip() != "0":
        said = " | ".join(_text(back / "sites.log").strip().splitlines()[-6:])[-600:]
        out.append({"kind": "recorder_failed", "detail": f"the traces were not read, so no call is observed: {said}"})
    text = _text(back / "valgrind.log")
    said = [line.strip() for line in text.splitlines() if line.strip()]
    if said:
        out.append({"kind": "recorder_messages",
                    "detail": f"Valgrind wrote {len(said)} lines, a process it could not run among the causes: "
                              + _cause(back, text) + " | ".join(said[:6])[:600]})
    return out


def _cause(back: Path, said: str) -> str:
    """The sentence that names why Valgrind stopped a program at its start, where its words and the kernel say it
    (`uname -r` and the first line of dmesg, which gVisor fills): a fault below the main stack reported as
    SEGV_ACCERR under gVisor (the module's docstring)."""
    kernel = _text(back / "kernel")
    if ACCERR not in said or "gvisor" not in kernel.lower():
        return ""
    return (f"under gVisor ({kernel.split(chr(10), 1)[0].strip()}) a fault below a program's main stack comes as "
            "SEGV_ACCERR, where Linux says SEGV_MAPERR, so Valgrind cannot grow that stack and the program dies at "
            "its start; Docker, Podman and Kiri (runc) run it: ")


def recorder_failed(back: Path, state: str) -> dict | None:
    """The gap of a Valgrind that does not run here, None where it does."""
    if _text(back / "recorder.code").strip() == "0":
        return None
    text = _text(back / "recorder.log")
    lines = [line.strip() for line in text.strip().splitlines()]  # from Valgrind's verdict, its backtrace after
    start = next((n for n, line in enumerate(lines) if "Process terminating" in line), max(len(lines) - 8, 0))
    said = " | ".join(lines[start:start + 8])[-600:]
    return {"kind": "recorder_failed",
            "detail": f"Valgrind did not run here, so no test ran ({state}): {_cause(back, text)}{said}"}


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""


def timed(number: int, line: str) -> list[str]:
    """Run `number`'s execution lines: `line`, its output in `tests-<number>.log`, then its exit code and its
    seconds in `tests-<number>.code`."""
    return [f"  s=$(date +%s); {line} > $OUT/tests-{number}.log 2>&1",
            f'  echo "$? $(( $(date +%s) - s ))" > $OUT/tests-{number}.code']


def stopped(entry: dict, given: str, limit: int, memory: int) -> dict | None:
    """Fill `entry`'s `exit_code` and `seconds` from its code file's text `given`; where the run was stopped, its
    `state` (`timeout` at the limit, `killed` before it: the memory limit, most often) and the gap that says so."""
    code, _, seconds = given.strip().partition(" ")
    entry["exit_code"] = int(code) if code.isdigit() else None
    entry["seconds"] = int(seconds) if seconds.isdigit() else None
    command = f"{' '.join(entry['argv'])} in {entry['root']}"
    if entry["exit_code"] == 124 or (entry["exit_code"] == 137 and (entry["seconds"] or 0) >= limit):
        entry["state"] = "timeout"
        return {"kind": "tests_timeout", "path": entry["root"],
                "detail": f"{command} did not end in {limit} s: what ran until then is observed"}
    if entry["exit_code"] == 137:
        entry["state"] = "killed"
        return {"kind": "tests_killed", "path": entry["root"],
                "detail": f"{command} was killed after {entry['seconds']} s, as a process is when the container's "
                          f"memory limit ({memory // 2**30} GB) is reached: a killed process writes no trace"}
    return None


def short(name: str) -> str:
    """The last name of a demangled function, its generic or template arguments and parameters left out:
    `<shapes::Square as shapes::Shape>::area` is `area`, `ns::Box<int>::get(int) const` is `get`."""
    depth, kept = 0, []
    for char in name:
        if char in "<(":
            depth += 1
        elif char in ">)":
            depth = max(depth - 1, 0)
        elif not depth:
            kept.append(char)
    found = re.match(r"[A-Za-z_]\w*", "".join(kept).split("::")[-1].strip())
    return found.group(0) if found else ""


def package(file: str, obj: str) -> dict:
    """`{manager, package, version}` of a callee outside the project, by the file its code is in: Rust's
    library, a crate of Cargo's registry or of a git checkout, else the object it is in."""
    if found := RUSTC.match(file):
        return {"manager": "rust", "package": found.group(1), "version": None}
    if found := REGISTRY.search(file):
        return {"manager": "cargo", "package": found.group(1), "version": found.group(2)}
    if found := CHECKOUT.search(file):
        return {"manager": "cargo", "package": found.group(1), "version": None}
    return {"manager": "system", "package": posixpath.basename(obj) or posixpath.basename(file), "version": None}


def external(callee: dict) -> dict:
    return {key: callee.get(key) for key in ("manager", "package", "version")}


def _named(node):
    """The node of a callee's last name, None where the callee is computed."""
    while node is not None and node.type in NAMED:
        node = node.child_by_field_name(NAMED[node.type])
    return node if node is not None and node.type in ("identifier", "field_identifier") else None


class _Source:
    """One file as tree-sitter reads it: its call expressions by the lines they can be placed at, its callables."""

    def __init__(self, path: Path, language: str):
        from languages._treesitter import get_parser
        loaded = get_parser(language)
        if loaded is None:
            raise OSError(f"no tree-sitter grammar of {language}")
        data = path.read_bytes()
        if language in ("c", "cpp"):
            from languages import cfamily
            data = cfamily.prepare(data, language)[0]  # what the snapshot's reader parses: lengths kept
        self.data, self.calls, self.callables = data, collections.defaultdict(list), []
        stack = [loaded[0].parse(data).root_node]
        while stack:
            node = stack.pop()
            stack.extend(node.children)
            if node.type in CALLABLES:
                self.callables.append(node)
            function = node.child_by_field_name("function") if node.type == "call_expression" else None
            if function is None:
                continue
            named, arguments = _named(function), node.child_by_field_name("arguments")
            anchors = {tuple(item.start_point) for item in (node, function, named, arguments) if item is not None}
            for row in {row for row, _column in anchors}:
                self.calls[row].append((anchors, named, function))

    def text(self, node) -> str:
        return self.data[node.start_byte:node.end_byte].decode("utf-8", "replace")

    def site(self, line: int, column: int, name: str) -> tuple[tuple | None, str | None]:
        """`(line, byte column, name)` from 0 of the call a compiler places at `line` and `column` (from 1; 0:
        none), the one calling `name` where several are, or why there is none."""
        row = line - 1
        found = [call for call in self.calls.get(row, ()) if not column or (row, column - 1) in call[0]]
        if len(found) > 1 and name:
            found = [call for call in found if call[1] is not None and self.text(call[1]) == name] or found
        if len({tuple((call[1] or call[2]).start_point) for call in found}) != 1:
            return None, AMBIGUOUS if found else NOT_AT_CALL
        _anchors, named, function = found[0]
        at = named or function
        return (at.start_point[0], at.start_point[1], self.text(named) if named is not None else ""), None

    def callable(self, line: int):
        """The innermost function or closure whose header, from its start to its body's, holds `line` (from 1)."""
        row, best = line - 1, None
        for node in self.callables:
            body = node.child_by_field_name("body")
            last = body.start_point[0] if body is not None else node.end_point[0]
            if node.start_point[0] <= row <= last and (best is None or node.start_byte > best.start_byte):
                best = node
        return best

    def declared(self, node) -> str:
        if CALLABLES[node.type]:
            return CALLABLES[node.type]
        name = node.child_by_field_name("name") or node.child_by_field_name("declarator")
        while name is not None and name.type not in DECLARATORS:
            name = name.child_by_field_name("declarator")
        if name is not None and name.type == "qualified_identifier":
            name = _named(name)
        return self.text(name) if name is not None else ""


def read(folder: Path, project: Path, root: str = WORK) -> tuple[list[dict], dict]:
    """The sites of an observation, `calls.json` in `folder` as `callgrind_sites.py` wrote it, placed on the
    sources of `project`; and what it says of itself: the traced `processes`, the `calls` read, the calls with no
    site by cause (`unplaced`, the container's causes among them)."""
    try:
        data = json.loads((Path(folder) / "calls.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return [], {}
    prefix, sources = root.rstrip("/") + "/", {}

    def source(file: str):
        rel = file[len(prefix):] if file.startswith(prefix) else None
        if rel is None:
            return None, OUTSIDE
        if rel not in sources:
            language, path = LANGUAGE.get(posixpath.splitext(rel)[1].lower()), Path(project) / rel
            try:
                sources[rel] = _Source(path, language) if language and path.is_file() else None
            except OSError:
                sources[rel] = None
        return (rel, sources[rel]) if sources[rel] is not None else (None, NOT_READ)

    found, unplaced = collections.defaultdict(dict), collections.Counter(data.get("unread") or {})
    for file, line, column, callee_file, callee_line, _callee_column, callee, obj, _count in data["calls"]:
        rel, held = source(file)
        if rel is None:
            unplaced[held] += 1
            continue
        if callee_file.startswith(prefix):  # the function whose header holds the line, else the one of its name there
            home, owner = source(callee_file)
            node = owner.callable(callee_line) if home is not None else None
            end = {"kind": "project", "file": callee_file[len(prefix):], "type": "function",
                   **({"line": node.start_point[0], "column": node.start_point[1], "name": owner.declared(node)}
                      if node is not None else {"line": callee_line - 1, "column": None, "name": short(callee)})}
        else:
            given = package(callee_file, obj)
            end = {"kind": "external", "module": given["package"], "name": callee, **given}
        place, why = held.site(line, column, end["name"] if end["kind"] == "project" else short(callee))
        if place is None:
            unplaced[why] += 1
            continue
        found[(rel, *place)][json.dumps(end, sort_keys=True)] = end
    sites = [{"file": rel, "line": row, "column": col, "name": name, "role": "call",
              "callees": [end for _key, end in sorted(ends.items())]}
             for (rel, row, col, name), ends in sorted(found.items())]
    return sites, {"processes": data.get("processes", 0), "calls": len(data["calls"]),
                   "unplaced": dict(sorted(unplaced.items()))}
