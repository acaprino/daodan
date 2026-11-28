"""The code that links the flows names no framework, library or tool (`link_types.py` and the link functions of `flows.py`).

The tree is Python's own (`ast` of the standard library, the language's parser); the names come from Daodan's data: the ids of
the service registry of category `framework`, `library` or `tool` (`service_registry.entry_category`) and the `NAME` of every
source of `premap.SOURCES` and `entry_points.SOURCES`. A name, an attribute, an import or a string equal to one of them fails.
A string written as the key of a record (a key of a dict, an index, the key `get`, `setdefault` or `pop` reads) is a field of
Daodan's own rows, not a name of a tool: the registry holds ids such as `kind`, which is also the field of an entry.
"""
import ast
import sys
from pathlib import Path

CORE = Path(__file__).resolve().parents[1] / "daodan/core"
sys.path.insert(0, str(CORE))
import entry_points  # noqa: E402
import premap  # noqa: E402
import service_registry  # noqa: E402

LINK_FUNCTIONS = ("link_facts", "_declared_routes", "_spec_routes")
FIELD_READS = ("get", "setdefault", "pop")


def forbidden() -> set[str]:
    registry = service_registry.load()["entries"]
    ids = {entry["id"] for entry in registry if service_registry.entry_category(entry) in ("framework", "library", "tool")}
    return {name.lower() for name in ids | {source.NAME for source in (*premap.SOURCES, *entry_points.SOURCES)}}


def words(tree: ast.AST) -> set[str]:
    """Names, attributes, imports and strings of `tree`, less the strings that are fields of a record."""
    fields = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            fields.update(id(key) for key in node.keys if key is not None)
        elif isinstance(node, ast.Subscript):
            fields.add(id(node.slice))
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in FIELD_READS and node.args:
            fields.add(id(node.args[0]))
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            found.add(node.id)
        elif isinstance(node, ast.Attribute):
            found.add(node.attr)
        elif isinstance(node, ast.arg):
            found.add(node.arg)
        elif isinstance(node, ast.keyword) and node.arg:
            found.add(node.arg)
        elif isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            found.add(node.name)
        elif isinstance(node, ast.alias):
            found.update(part for name in (node.name, node.asname) if name for part in name.split("."))
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.update(node.module.split("."))
        elif isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in fields:
            found.add(node.value)
    return {word.lower() for word in found}


def link_trees() -> dict[str, ast.AST]:
    flows = ast.parse((CORE / "flows.py").read_text(encoding="utf-8"))
    functions = {node.name: node for node in flows.body if isinstance(node, ast.FunctionDef)}
    return {"link_types.py": ast.parse((CORE / "link_types.py").read_text(encoding="utf-8")),
            **{f"flows.{name}": functions[name] for name in LINK_FUNCTIONS}}


def test_the_link_code_names_no_framework_library_or_tool():
    names = forbidden()
    found = {where: sorted(words(tree) & names) for where, tree in link_trees().items()}
    assert {where: hit for where, hit in found.items() if hit} == {}


def test_the_check_sees_a_name_and_skips_a_field():
    """The same reading on a function that names a source: the name is caught, the field `kind` is not."""
    source = ("def bad(row):\n    from entry_points import noir\n    return row.get('kind') == 'rotta' and row['reader'] == 'Noir'\n")
    hit = words(ast.parse(source)) & forbidden()
    assert hit == {"noir"}
