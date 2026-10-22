"""Isolate each divergence found on the full corpora, one construct per parse.

1. tree-sitter reads `type(x).__name__ = "..."` (an assignment through a call to
   the builtin `type`) as a PEP 695 type alias statement.
2. tree-sitter ends a definition after trailing comments, stdlib ast at the last
   statement.
3. tree-sitter accepts a PEP 696 type-parameter default only with an ERROR node.
4. tree-sitter accepts invalid Python (a Python 2 print statement, mixed tabs and
   spaces) without any ERROR node, i.e. it is not a validator.
"""
import ast

import tree_sitter_python
from tree_sitter import Language, Parser

PARSER = Parser(Language(tree_sitter_python.language()))


def ts_types(source: str):
    tree = PARSER.parse(source.encode("utf-8"))
    out, stack = [], [tree.root_node]
    while stack:
        node = stack.pop()
        if node.type in ("type_alias_statement", "function_definition", "class_definition", "ERROR"):
            out.append((node.type, node.start_point[0] + 1, node.end_point[0] + 1,
                        node.text.decode()[:40].replace("\n", "\\n")))
        stack.extend(node.children)
    return tree.root_node.has_error, sorted(out, key=lambda t: t[1])


def ast_view(source: str):
    try:
        tree = ast.parse(source)
    except SyntaxError as error:
        return f"SyntaxError: {error.msg}"
    return [(type(n).__name__, n.lineno, getattr(n, "end_lineno", None))
            for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.ClassDef))
            or type(n).__name__ == "TypeAlias"]


CASES = {
    "1 assignment through type(x)": 'class A: pass\ntype(A).__name__ = "B"\n',
    "1b real type alias, control": "type Pair = tuple[int, int]\n",
    "1c type used as a function": "x = type(3)\n",
    "2 trailing comment after the body": "def f():\n    x = 1\n\n    # trailing comment\n\ny = 2\n",
    "3 PEP 696 default": "def f[T = int](x: T) -> T: return x\n",
    "4a Python 2 print": "print 'hello'\n",
    "4b mixed tabs and spaces": "def f():\n\tif True:\n        return 1\n\treturn 2\n",
}

for label, source in CASES.items():
    error, nodes = ts_types(source)
    print(f"--- {label}")
    print(f"    tree-sitter has_error={error} nodes={nodes}")
    print(f"    stdlib ast {ast_view(source)}")
