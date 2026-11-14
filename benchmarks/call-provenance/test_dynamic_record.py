"""dynamic_record.py on fixtures/python: every executed call seen, with the callee written here by hand.

    python -m unittest benchmarks/call-provenance/test_dynamic_record.py

Needs Python 3.12+ (sys.monitoring). The fixture runs in a child process loaded through sitecustomize, as in
the container; nothing is installed.
"""
from __future__ import annotations

import ast
import glob
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIXTURE = HERE / "fixtures" / "python"
RECORDER = HERE / "dynamic_record.py"


def lines(name: str) -> list[str]:
    return (FIXTURE / name).read_text(encoding="utf-8").split("\n")


def line_of(name: str, text: str, nth: int = 0) -> int:
    """0-based line whose stripped text is `text` (the nth such line)."""
    return [i for i, line in enumerate(lines(name)) if line.strip() == text][nth]


def site(name: str, text: str, token: str, start: str = "") -> tuple:
    """(file, line, byte column of `token`, token) on the line `text`; token "" is the call's start, where the
    text `start` begins or else at the line's first character."""
    number = line_of(name, text)
    line = lines(name)[number]
    if token:
        column = re.search(rf"(?<![A-Za-z0-9_]){re.escape(token)}(?![A-Za-z0-9_])", line).start()
    else:
        column = line.index(start) if start else len(line) - len(line.lstrip())
    return name, number, len(line[:column].encode("utf-8")), token


def project(name: str, qualname: str, text: str, nth: int = 0) -> str:
    return f"{name}::{qualname}@{line_of(name, text, nth)}"


def describe(callee: dict) -> str:
    if callee["kind"] == "project":
        return f"{callee['file']}::{callee['name']}@{callee['line']}"
    return f"{callee['kind']}:{callee['module']}.{callee['name']}"


WRAPPER = project("lib.py", "trace.<locals>.wrapper", "def wrapper(*args):")
ADD = project("lib.py", "add", "def add(a, b):")
APPLY = project("lib.py", "apply", "def apply(fn, value):")
BOX = project("lib.py", "Box", "class Box:")
CHILD = project("lib.py", "Child", "class Child(Base):")
CALL_LINE = 'getattr(Child(), "speak")()'
DUMPS_LINE = 'json.dumps(len("ab"))'

# Every observed pair the run must produce at these sites: (file, line text, token) -> callees.
EXPECTED = {
    site("main.py", "add(1, 2)", "add"): {WRAPPER},
    site("main.py", "apply(double, 3)", "apply"): {APPLY},
    site("main.py", "apply(lambda v: v, 4)", "apply"): {APPLY},
    site("main.py", CALL_LINE, "getattr"): {"runtime:builtins.getattr"},
    site("main.py", CALL_LINE, "Child"): {CHILD},
    site("main.py", CALL_LINE, ""): {project("lib.py", "Child.speak", "def speak(self):", 1)},
    site("main.py", "Child.make()", "make"): {project("lib.py", "Base.make", "def make(cls):")},
    site("main.py", "box = Box(1)", "Box"): {BOX},
    site("main.py", "box.size", "size"): {project("lib.py", "Box.size", "def size(self):")},
    site("main.py", "box.size = 2", "size"): {project("lib.py", "Box.size", "def size(self, value):")},
    site("main.py", "box < Box(3)", "Box"): {BOX},
    site("main.py", "box < Box(3)", ""): {project("lib.py", "Box.__lt__", "def __lt__(self, other):")},
    site("main.py", "for i in count(2):", "count"): {project("lib.py", "count", "def count(n):")},
    site("main.py", "fail()", "fail"): {project("lib.py", "fail", "def fail():")},
    site("main.py", DUMPS_LINE, "dumps"): {"runtime:json.dumps"},
    site("main.py", DUMPS_LINE, "len"): {"runtime:builtins.len"},
    site("main.py", "sorted([2, 1], key=double)", "sorted"): {"runtime:builtins.sorted"},
    site("main.py", "run()", "run"): {project("main.py", "run", "def run():")},
    site("lib.py", "@functools.wraps(fn)", "wraps"): {"runtime:functools.wraps"},
    site("lib.py", "@functools.wraps(fn)", "", "functools"): {"runtime:functools.partial"},
    site("lib.py", "return fn(*args)", "fn"): {ADD},
    site("lib.py", "@trace", "trace"): {project("lib.py", "trace", "def trace(fn):")},
    site("lib.py", "return fn(value)", "fn"): {project("main.py", "double", "def double(x):"),
                                              project("main.py", "run.<locals>.<lambda>", "apply(lambda v: v, 4)")},
    site("lib.py", "return cls()", "cls"): {CHILD},
    site("lib.py", 'raise ValueError("no")', "ValueError"): {"runtime:builtins.ValueError"},
    site("lib.py", "@property", "property"): {"runtime:builtins.property"},
    site("lib.py", "@size.setter", "setter"): {"runtime:builtins.property.setter"},
    site("lib.py", "@classmethod", "classmethod"): {"runtime:builtins.classmethod"},
    site("main.py", "with Guard():", "Guard"): {project("lib.py", "Guard", "class Guard:")},
    site("lib.py", 'return "child" + super().speak()', "super"): {"runtime:builtins.super"},
    site("lib.py", 'return "child" + super().speak()', "speak"): {project("lib.py", "Base.speak", "def speak(self):")},
    # A wrapper made by functools.wraps keeps the module of its own file, not the one wraps copies.
    site("main.py", "opened()", "opened"): {"runtime:contextlib.contextmanager.<locals>.helper"},
}
# The exit of a with block is a call instruction placed on the context expression: a site of its own.
WITH_LINE = line_of("main.py", "with Guard():")
# How a site is reached: a call instruction, an instruction that calls implicitly, a decorator's application.
ROLES = {
    site("main.py", "add(1, 2)", "add"): "call",
    site("main.py", "box.size", "size"): "LOAD_ATTR",
    site("main.py", "box.size = 2", "size"): "STORE_ATTR",
    site("main.py", "box < Box(3)", ""): "COMPARE_OP",
    site("lib.py", "@functools.wraps(fn)", "", "functools"): "decorator",
    site("lib.py", "@trace", "trace"): "call",
    site("main.py", "with Guard():", "Guard"): "call",
}


class RecorderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        folder = Path(cls.temp.name)
        subprocess.run([sys.executable, "-I", str(RECORDER), "site", str(folder / "site")], check=True)
        env = {key: value for key, value in os.environ.items() if not key.startswith(("PYTHON", "DYN_"))}
        env.update(PYTHONPATH=str(folder / "site"), DYN_ROOT=str(FIXTURE),
                   DYN_OUT=str(folder / "observed-%p.json"), PYTHONDONTWRITEBYTECODE="1")
        cls.done = subprocess.run([sys.executable, "main.py"], cwd=FIXTURE, env=env, capture_output=True, text=True)
        cls.files = glob.glob(str(folder / "observed-*.json"))
        cls.data = json.loads(Path(cls.files[0]).read_text(encoding="utf-8")) if cls.files else {"sites": []}
        cls.sites = {(s["file"], s["line"], s["column"], s["name"]): s for s in cls.data["sites"]}

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_the_program_runs_unchanged_and_writes_one_exact_file(self):
        self.assertEqual((self.done.returncode, self.done.stdout, self.done.stderr), (0, "", ""))
        self.assertEqual(len(self.files), 1)
        self.assertIs(self.data["exact"], True)
        self.assertEqual(self.data["stats"]["errors"], 0)

    def test_each_site_has_the_callees_written_by_hand(self):
        for key, expected in EXPECTED.items():
            with self.subTest(site=key):
                self.assertIn(key, self.sites)
                self.assertEqual({describe(c) for c in self.sites[key]["callees"]}, expected)

    def test_each_site_is_reached_the_way_written_by_hand(self):
        for key, role in ROLES.items():
            with self.subTest(site=key):
                self.assertEqual(self.sites[key]["role"], role)

    def test_a_wrapper_names_the_function_it_wraps(self):
        [callee] = self.sites[site("main.py", "add(1, 2)", "add")]["callees"]
        self.assertEqual(describe(callee["wraps"]), ADD)
        [partial] = self.sites[site("lib.py", "@functools.wraps(fn)", "", "functools")]["callees"]
        self.assertEqual(describe(partial["wraps"]), "runtime:functools.update_wrapper")

    def test_a_with_block_enters_and_exits_at_sites_of_their_own(self):
        line = WITH_LINE
        roles = {s["role"]: {describe(c) for c in s["callees"]} for s in self.data["sites"]
                 if (s["file"], s["line"], s["name"]) == ("main.py", line, "")}
        self.assertEqual(roles, {"BEFORE_WITH": {project("lib.py", "Guard.__enter__", "def __enter__(self):")},
                                 "WITH_EXIT": {project("lib.py", "Guard.__exit__", "def __exit__(self, *exc):")}})
        [opened] = self.sites[site("main.py", "opened()", "opened")]["callees"]
        self.assertEqual(describe(opened["wraps"]), project("lib.py", "opened", "def opened():"))

    def test_c_functions_are_externals_with_their_module(self):
        for token, text in (("len", DUMPS_LINE), ("sorted", "sorted([2, 1], key=double)")):
            [callee] = self.sites[site("main.py", text, token)]["callees"]
            self.assertTrue(callee["native"])
        [dumps] = self.sites[site("main.py", DUMPS_LINE, "dumps")]["callees"]
        self.assertFalse(dumps["native"])

    def test_every_call_of_run_is_recorded_and_nothing_else_lands_on_its_lines(self):
        """Each call node of main.py's run() has its site; a callback called by a C function (sorted's key)
        and a generator's first step (the for loop) add none."""
        tree = ast.parse((FIXTURE / "main.py").read_text(encoding="utf-8"))
        run = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "run")
        wanted = set()
        for node in ast.walk(run):
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name):
                    wanted.add(("main.py", func.lineno - 1, func.col_offset, func.id))
                elif isinstance(func, ast.Attribute):
                    wanted.add(("main.py", func.end_lineno - 1, func.end_col_offset - len(func.attr), func.attr))
                else:
                    wanted.add(("main.py", node.lineno - 1, node.col_offset, ""))
        calls = {key for key, s in self.sites.items() if key[0] == "main.py" and s["role"] == "call"
                 and run.lineno - 1 <= key[1] < run.end_lineno}
        self.assertEqual(calls, wanted)
        for text, tokens in (("for i in count(2):", ["count"]), ("sorted([2, 1], key=double)", ["sorted"])):
            number = line_of("main.py", text)
            self.assertEqual([key[3] for key in self.sites if key[:2] == ("main.py", number)], tokens)

    def test_without_an_output_the_recorder_stays_off(self):
        folder = Path(self.temp.name)
        env = {key: value for key, value in os.environ.items() if not key.startswith(("PYTHON", "DYN_"))}
        env.update(PYTHONPATH=str(folder / "site"), PYTHONDONTWRITEBYTECODE="1")
        done = subprocess.run([sys.executable, "-c", "import sys; print(sys.monitoring.get_tool(4))"],
                              cwd=FIXTURE, env=env, capture_output=True, text=True)
        self.assertEqual((done.returncode, done.stdout.strip()), (0, "None"))


if __name__ == "__main__":
    unittest.main()
