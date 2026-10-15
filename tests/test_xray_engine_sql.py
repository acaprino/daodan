"""SQL extraction ignores lexical non-code while retaining declaration names."""

import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "plugins/codebase-map/skills/map-method/scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from languages import sql, plsql


class SqlLexicalTests(unittest.TestCase):
    def test_nested_comments_and_literals_do_not_create_objects(self):
        source = (
            "/* outer /* nested */ CREATE TABLE fake_comment (id INT); */\n"
            "SELECT 'CREATE TABLE fake_string (id INT)', $$CREATE VIEW fake_dollar AS SELECT 1$$;\n"
            "CREATE TABLE actual (id INT);\n"
        )
        result = sql.adapter.parse(source, "schema.sql")
        self.assertEqual([(item.name, item.kind, item.line_number) for item in result.classes],
                         [("actual", "table", 3)])

    def test_quoted_identifier_text_is_not_another_declaration(self):
        result = sql.adapter.parse('CREATE TABLE "CREATE VIEW ghost AS SELECT 1" (id INT);', "schema.sql")
        self.assertEqual([(item.name, item.kind) for item in result.classes],
                         [("CREATE VIEW ghost AS SELECT 1", "table")])

    def test_qualified_and_escaped_quoted_names_are_retained(self):
        result = sql.adapter.parse('CREATE TABLE "sales data"."order""items" (id INT);', "schema.sql")
        self.assertEqual([item.name for item in result.classes], ['sales data.order"items'])

    def test_literal_and_comment_calls_do_not_pollute_external_calls(self):
        result = sql.adapter.parse("-- UTL_HTTP.request(x)\nSELECT 'UTL_FILE.open(x)';\nUTL_HTTP.request(x);\n", "calls.sql")
        self.assertEqual([(item.call_type, item.line_number) for item in result.external_calls],
                         [("database", 2), ("network", 3)])

    def test_oracle_q_quotes_allow_embedded_single_quotes_and_comment_markers(self):
        result = plsql.adapter.parse(
            "CREATE PACKAGE BODY actual AS\n"
            "  PROCEDURE run IS BEGIN\n"
            "    x := q'[it's -- CREATE PACKAGE fake AS END; /* not comment */]';\n"
            "  END;\nEND;\n", "actual.pkb",
        )
        self.assertEqual([item.name for item in result.classes], ["actual"])
        self.assertEqual([item.name for item in result.functions], ["run"])

    def test_inner_plsql_procedure_retains_quoted_parameter_type(self):
        result = plsql.adapter.parse(
            'CREATE PACKAGE p AS\n  PROCEDURE run(x "PERSON");\nEND;\n', "p.pks",
        )
        self.assertEqual(result.functions[0].parameters[0].annotation, '"PERSON"')

    def test_inner_plsql_function_retains_literal_parameter_default(self):
        result = plsql.adapter.parse(
            "CREATE PACKAGE p AS\n  FUNCTION run(x VARCHAR2 DEFAULT 'abc') RETURN NUMBER;\nEND;\n", "p.pks",
        )
        self.assertEqual(result.functions[0].parameters[0].annotation, "VARCHAR2 DEFAULT 'abc'")


if __name__ == "__main__":
    unittest.main()
