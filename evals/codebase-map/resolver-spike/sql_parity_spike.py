# /// script
# requires-python = ">=3.11"
# dependencies = ["tree-sitter>=0.23", "tree-sitter-sql==0.3.11"]
# ///
"""SQL parity spike: what tree-sitter-sql extracts versus the current scanner.

Also probes the lexical traps the existing tests pin (nested comments, quoted
identifiers, dollar-quoted strings), because those are where a regex scanner is
fragile and a grammar should be stronger.
"""
from __future__ import annotations

import collections
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "plugins" / "codebase-map" / "skills" / "map-method" / "scripts"))

import tree_sitter_sql
from tree_sitter import Language, Parser

from languages import sql as sql_adapter  # noqa: E402

SAMPLE = """
/* outer /* nested */ CREATE TABLE fake_comment (id INT); */
SELECT 'CREATE TABLE fake_string (id INT)', $$CREATE VIEW fake_dollar AS SELECT 1$$;
CREATE TABLE "sales data"."order""items" (id INT, name TEXT);
CREATE TABLE orders (id SERIAL PRIMARY KEY, total NUMERIC(10,2) NOT NULL);
CREATE OR REPLACE VIEW v_orders AS SELECT id, total FROM orders;
CREATE INDEX idx_orders_total ON orders (total);
CREATE SEQUENCE seq_orders START 1;
CREATE TYPE order_state AS ENUM ('new', 'paid');
CREATE FUNCTION add_order(total NUMERIC) RETURNS INT AS $$ BEGIN RETURN 1; END; $$ LANGUAGE plpgsql;
CREATE TRIGGER trg_orders BEFORE INSERT ON orders FOR EACH ROW EXECUTE PROCEDURE add_order();
CREATE SCHEMA reporting;
"""

TRAP = 'CREATE TABLE "CREATE VIEW ghost AS SELECT 1" (id INT);\n'


def node_types(tree) -> collections.Counter:
    counts = collections.Counter()
    stack = [tree.root_node]
    while stack:
        node = stack.pop()
        counts[node.type] += 1
        stack.extend(node.children)
    return counts


def top_level(tree) -> list[tuple[str, int]]:
    return [(child.type, child.start_point[0] + 1) for child in tree.root_node.children
            if child.type not in (";", "\n")]


def main() -> int:
    print("tree_sitter_sql version:", getattr(tree_sitter_sql, "__version__", "unknown"))
    print("exported:", [name for name in dir(tree_sitter_sql) if not name.startswith("_")])

    language = Language(tree_sitter_sql.language())
    parser = Parser(language)

    for label, source in (("sample", SAMPLE), ("quoted-identifier trap", TRAP)):
        tree = parser.parse(source.encode("utf-8"))
        print(f"\n===== tree-sitter-sql on {label}")
        print("  root:", tree.root_node.type, "has_error:", tree.root_node.has_error)
        print("  top-level statements:", top_level(tree))
        interesting = {key: value for key, value in node_types(tree).items()
                       if "name" in key or "create" in key or key in ("object_reference", "column_name")}
        print("  declaration-ish node counts:", dict(sorted(interesting.items(), key=lambda i: -i[1])[:18]))

        result = sql_adapter.adapter.parse(source, "schema.sql")
        print(f"  current adapter classes: {[(c.name, c.kind, c.line_number) for c in result.classes]}")
        print(f"  current adapter functions: {[(f.name, f.line_number) for f in result.functions]}")
        print(f"  current adapter notes: {result.notes}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
