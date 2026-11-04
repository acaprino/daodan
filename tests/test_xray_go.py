"""Go through the whole chain: adapter, snapshot spans, selective reading.

The tree-sitter cases run wherever the grammar is installed; the regex cases
force the fallback, whose contract is that it never claims an exact span.
"""
import re
import shutil
import sys
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "plugins/codebase-map/skills/map-method/scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import snapshot  # noqa: E402
import source_reader  # noqa: E402
from languages import SUPPORTED_EXTENSIONS, SUPPORTED_LANGUAGES, _treesitter, detect_language, get_adapter  # noqa: E402
from languages import go as go_module  # noqa: E402

HAS_GRAMMAR = _treesitter.get_parser("go") is not None

SOURCE = '''package billing

import (
	"fmt"
	alias "github.com/acme/ledger"
)

const MaxRetries = 3
const (
	minimum = 1
	Ceiling = 9
)

type Invoice struct {
	ID    string
	Total float64
}

type Payer interface {
	Pay(amount float64) error
}

type Money = float64

func (i *Invoice) Pay(amount float64) error {
	fmt.Println("PAY_BODY_MARKER", amount)
	return nil
}

func NewInvoice(id string) (*Invoice, error) {
	return &Invoice{ID: id}, nil // NEW_BODY_MARKER
}

func helper() {
	fmt.Println("HELPER_BODY_MARKER")
}
'''


@contextmanager
def grammar_unavailable():
    with mock.patch.object(_treesitter, "get_parser", return_value=None), \
            mock.patch.object(go_module, "get_parser", return_value=None):
        yield


def parse(content=SOURCE):
    return get_adapter("go").parse(content, "billing.go")


def emitted_lines(packet):
    found = {}
    for item in packet["files"]:
        for block in item["blocks"]:
            for line in block["source"].splitlines():
                number, _, text = line.partition(": ")
                found[int(number)] = text
    return found


class GoRegistrationTests(unittest.TestCase):
    def test_go_is_a_supported_language(self):
        self.assertEqual(SUPPORTED_EXTENSIONS[".go"], "go")
        self.assertIn("go", SUPPORTED_LANGUAGES)
        self.assertEqual(detect_language(Path("billing.go")), "go")
        self.assertEqual(snapshot.parser_profile(Path("billing.go"))["language"], "go")


@unittest.skipUnless(HAS_GRAMMAR, "requires the Go tree-sitter grammar")
class GoTreeSitterTests(unittest.TestCase):
    def test_types_functions_and_methods_carry_exact_spans(self):
        result = parse()

        self.assertEqual(result.notes, ["parser=tree-sitter"])
        types = {c.name: c for c in result.classes}
        self.assertEqual(types["Invoice"].kind, "struct")
        self.assertEqual((types["Invoice"].line_number, types["Invoice"].end_line), (14, 17))
        self.assertEqual(types["Invoice"].class_variables, ["ID", "Total"])
        self.assertEqual(types["Payer"].kind, "interface")
        self.assertEqual(types["Payer"].class_variables, ["Pay"])
        self.assertEqual(types["Payer"].methods, [], "a signature has no body to elide")
        self.assertEqual(types["Money"].kind, "type-alias")
        functions = {f.name: f for f in result.functions}
        self.assertEqual((functions["Invoice.Pay"].line_number, functions["Invoice.Pay"].end_line), (25, 28))
        self.assertEqual((functions["NewInvoice"].line_number, functions["NewInvoice"].end_line), (30, 32))
        self.assertEqual(functions["Invoice.Pay"].calls_made, ["fmt.Println"])

    def test_exported_names_follow_the_capital_letter_rule(self):
        result = parse()

        self.assertEqual({f.name: f.visibility for f in result.functions},
                         {"Invoice.Pay": "public", "NewInvoice": "public", "helper": "private"})
        self.assertIn("Invoice", result.exported_symbols)
        self.assertIn("Ceiling", result.exported_symbols)
        self.assertNotIn("minimum", result.exported_symbols)
        self.assertEqual(result.constants, ["MaxRetries", "minimum", "Ceiling"])

    def test_imports_keep_the_alias_and_resolve_no_project_edge(self):
        imports = {i.module: i for i in parse().imports}

        self.assertEqual(imports["fmt"].names, ["fmt"])
        self.assertEqual(imports["github.com/acme/ledger"].names, ["alias"])
        self.assertFalse(any(i.is_internal for i in imports.values()))

    def test_method_receivers_name_their_type_without_pointer_or_generics(self):
        source = ("package p\n"
                  "func (b *Box[T]) Put(x T) {\n}\n"
                  "func (Invoice) Name() string {\n\treturn \"x\"\n}\n"
                  "func F[T any](a, b T, rest ...string) (T, error) {\n\treturn a, nil\n}\n")

        functions = {f.name: f for f in parse(source).functions}

        self.assertEqual(set(functions), {"Box.Put", "Invoice.Name", "F"})
        self.assertEqual([p.name for p in functions["F"].parameters], ["a", "b", "rest"])
        self.assertEqual(functions["F"].parameters[2].annotation, "...string")

    def test_grouped_type_declarations_and_embedded_fields_are_read(self):
        source = ("package p\ntype (\n\tA struct {\n\t\tio.Writer\n\t\tX, Y int\n\t}\n\tB int\n)\n")

        types = {c.name: c for c in parse(source).classes}

        self.assertEqual(types["A"].class_variables, ["io.Writer", "X", "Y"])
        self.assertEqual(types["B"].kind, "type")

    def test_interface_members_are_listed_and_embedded_interfaces_become_bases(self):
        source = "package p\ntype R interface {\n\tio.Reader\n\tPay(a int) error\n\tClose()\n}\n"

        interface = parse(source).classes[0]

        self.assertEqual((interface.kind, interface.class_variables, interface.bases),
                         ("interface", ["Pay", "Close"], ["io.Reader"]))

    def test_external_calls_are_classified_by_call_target(self):
        source = ('package p\nimport "os"\nfunc f() {\n\tos.ReadFile("a")\n\thttp.Get("u")\n'
                  '\tsql.Open("x", "y")\n\texec.Command("ls")\n\tfmt.Println("not external")\n}\n')

        found = {call.call_type for call in parse(source).external_calls}

        self.assertEqual(found, {"filesystem", "network", "database", "ipc"})

    def test_a_syntax_error_is_reported_and_degrades_the_snapshot_entry(self):
        result = parse("package p\nfunc broken( {\n")

        self.assertTrue(any(note.startswith("syntax error:") for note in result.notes))


class GoRegexFallbackTests(unittest.TestCase):
    def test_fallback_finds_the_symbols_but_never_claims_an_end_line(self):
        with grammar_unavailable():
            result = parse()

        self.assertIn("parser=regex-fallback", result.notes)
        self.assertEqual({f.name for f in result.functions}, {"Invoice.Pay", "NewInvoice", "helper"})
        self.assertEqual({c.name: c.kind for c in result.classes},
                         {"Invoice": "struct", "Payer": "interface", "Money": "type-alias"})
        self.assertTrue(all(f.end_line is None for f in result.functions))
        self.assertTrue(all(c.end_line is None for c in result.classes))
        self.assertEqual({i.module for i in result.imports}, {"fmt", "github.com/acme/ledger"})
        self.assertEqual(set(result.constants), {"MaxRetries", "minimum", "Ceiling"})


class GoSnapshotAndReadingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="xray-go-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.src = self.tmp / "src"
        self.src.mkdir()
        (self.src / "billing.go").write_text(SOURCE, encoding="utf-8", newline="")

    def manifest(self):
        manifest = snapshot.build_manifest(self.src)
        key = next(k for k in manifest["files"] if k.endswith("billing.go"))
        return manifest, key

    @unittest.skipUnless(HAS_GRAMMAR, "requires the Go tree-sitter grammar")
    def test_manifest_records_exact_symbol_spans_and_the_native_profile(self):
        manifest, key = self.manifest()

        entry = manifest["files"][key]
        self.assertEqual((entry["language"], entry["status"]), ("go", "parsed"))
        self.assertEqual(entry["parser_profile"]["backend"], "tree-sitter")
        self.assertEqual(entry["symbols"]["Invoice.Pay"]["span_precision"], "exact")
        self.assertEqual((entry["symbols"]["Invoice.Pay"]["start"], entry["symbols"]["Invoice.Pay"]["end"]), (25, 28))

    @unittest.skipUnless(HAS_GRAMMAR, "requires the Go tree-sitter grammar")
    def test_selected_method_reads_its_own_body_and_not_a_sibling_function(self):
        manifest, key = self.manifest()

        packet = source_reader.read_packet(manifest, [{"path": key, "symbols": ["Invoice.Pay"]}])

        text = "\n".join(emitted_lines(packet).values())
        self.assertIn("PAY_BODY_MARKER", text)
        self.assertNotIn("NEW_BODY_MARKER", text)
        self.assertNotIn("HELPER_BODY_MARKER", text)
        self.assertIn("package billing", text)
        self.assertEqual(packet["files"][0]["blocks"][0]["reason"], "context-and-selection")

    @unittest.skipUnless(HAS_GRAMMAR, "requires the Go tree-sitter grammar")
    def test_a_one_line_function_makes_the_reader_fall_back_to_the_whole_file(self):
        (self.src / "billing.go").write_text(
            SOURCE.replace('func helper() {\n\tfmt.Println("HELPER_BODY_MARKER")\n}\n', "func helper() { return }\n"),
            encoding="utf-8", newline="")
        manifest, key = self.manifest()

        packet = source_reader.read_packet(manifest, [{"path": key, "symbols": ["Invoice.Pay"]}])

        self.assertEqual(packet["files"][0]["blocks"][0]["reason"], "full-file-fallback")

    def test_without_the_grammar_spans_are_inferred_and_the_reader_reads_the_file(self):
        with grammar_unavailable():
            manifest, key = self.manifest()
            entry = manifest["files"][key]
            self.assertEqual(entry["parser_profile"]["backend"], "regex-fallback")
            self.assertEqual(entry["symbols"]["Invoice.Pay"]["span_precision"], "inferred")

            packet = source_reader.read_packet(manifest, [{"path": key, "symbols": ["Invoice.Pay"]}])

        text = "\n".join(emitted_lines(packet).values())
        self.assertIn("HELPER_BODY_MARKER", text, "an inferred span must not be trusted to cut the file")
        self.assertEqual(packet["files"][0]["blocks"][0]["reason"], "full-file-fallback")

    def test_comments_use_the_c_style_lexer(self):
        comments = get_adapter("go").extract_comments('x := "// not a comment" // real\n/* block */\n')

        self.assertEqual([c.text for c in comments], ["real", "block"])
        self.assertTrue(re.fullmatch(r"\d+", str(comments[0].line_number)))


if __name__ == "__main__":
    unittest.main()
