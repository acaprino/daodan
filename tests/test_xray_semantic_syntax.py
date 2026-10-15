"""Source syntax evidence, independently checked against binding and span rules."""

import ast
import sys
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1] / "plugins/codebase-map/skills/map-method/scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from languages import javascript, python, typescript
from languages import _treesitter as ts
from languages.base import ParseResult


class PythonSemanticTests(unittest.TestCase):
    def parse(self, source):
        result = python.adapter.parse(source, "sample.py")
        semantic = getattr(result, "semantic", None)
        self.assertIsNotNone(semantic)
        return semantic

    def test_additive_default_and_malformed_input(self):
        self.assertIsNone(getattr(ParseResult("x"), "semantic", "missing"))
        self.assertIsNone(getattr(python.adapter.parse("def broken(\n", "x.py"), "semantic", "missing"))

    def test_aliases_decoys_and_exact_repeated_call_positions(self):
        source = ('from .core import save as persist\nimport tools as ns\n'
                  '# persist()\ntext = "persist()"\né = 1; persist(); persist()\n'
                  'value = f"text persist() {ns.save()}"\n')
        semantic = self.parse(source)
        self.assertEqual((semantic["version"], semantic["backend"], semantic["status"]), (1, "stdlib-ast", "ast"))
        self.assertEqual([(x["local"], x["module"], x["imported"], x["mode"]) for x in semantic["imports"]],
                         [("persist", ".core", "save", "named"), ("ns", "tools", "*", "namespace")])
        calls = [r for r in semantic["references"] if r["kind"] == "call"]
        self.assertEqual([r["parts"] for r in calls], [["persist"], ["persist"], ["ns", "save"]])
        self.assertEqual([r["span"] for r in calls[:2]], [[5, 8, 5, 15], [5, 19, 5, 26]])

    def test_shadowing_nested_owners_and_comprehension_scope(self):
        semantic = self.parse('from core import save\ndef outer(save):\n    save()\n    def inner():\n        save()\n    return [save() for save in values]\nsave()\n')
        declarations = {d["id"]: d for d in semantic["declarations"]}
        calls = [r for r in semantic["references"] if r["kind"] == "call"]
        self.assertEqual([declarations[r["caller"]]["name"] if r["caller"] else None for r in calls],
                         ["outer", "inner", "outer", None])
        parameter = next(d for d in semantic["declarations"] if d["kind"] == "parameter" and d["name"] == "save")
        self.assertEqual(parameter["scope"], calls[0]["scope"])
        scopes = {s["id"]: s for s in semantic["scopes"]}
        self.assertEqual(scopes[calls[2]["scope"]]["kind"], "comprehension")
        self.assertTrue(any(d["name"] == "save" and d["scope"] == calls[2]["scope"] for d in semantic["declarations"]))

    def test_global_nonlocal_class_and_unsupported_bindings_are_conservative(self):
        semantic = self.parse('from core import save\ndef outer():\n    save = replacement\n    def inner():\n        nonlocal save\n        save()\nclass Item:\n    def save(self): pass\n    def run(self): save(); self.save()\ndef change():\n    global save\n    save()\n')
        calls = [r for r in semantic["references"] if r["kind"] == "call"]
        scopes = {s["id"]: s for s in semantic["scopes"]}
        blocked = [d for d in semantic["declarations"] if d["kind"] == "unknown" and d["name"] == "save"]
        self.assertEqual(sum(d["scope"] != "module" for d in blocked), 3)
        run = next(r for r in calls if r["parts"] == ["self", "save"])
        self.assertEqual(scopes[run["scope"]]["parent"], "module")
        self.assertTrue(any(s["kind"] == "class" and s.get("unresolved") for s in scopes.values()))

    def test_dynamic_receivers_and_assignment_bindings_do_not_guess(self):
        semantic = self.parse('from core import save\nsave = other\ndef use():\n    (factory()).save()\n    values[index]()\n    for save in values: save()\n')
        calls = [r for r in semantic["references"] if r["kind"] == "call"]
        self.assertEqual(sum(not r["parts"] for r in calls), 2)
        self.assertTrue(any(d["name"] == "save" and d["kind"] == "binding" for d in semantic["declarations"]))

    def test_reuses_the_python_ast(self):
        with mock.patch.object(ast, "parse", wraps=ast.parse) as parse:
            self.parse("def save(): pass\nsave()\n")
        self.assertEqual(parse.call_count, 1)

    def test_global_and_nonlocal_mutation_block_affected_outer_bindings(self):
        semantic = self.parse('def save(): pass\ndef mutate():\n    global save\n    save = other\nsave()\n'
                              'def outer():\n    def work(): pass\n    def inner():\n        nonlocal work\n        work = other\n    work()\n')
        declarations = semantic["declarations"]
        self.assertTrue(any(d["name"] == "save" and d["kind"] == "unknown" and d["scope"] == "module" for d in declarations))
        work = next(d for d in declarations if d["name"] == "work" and d["kind"] == "function")
        self.assertTrue(any(d["name"] == "work" and d["kind"] == "unknown" and d["scope"] == work["scope"] for d in declarations))

    def test_class_methods_keep_qualified_identity_without_class_lexical_capture(self):
        semantic = self.parse('class Item:\n    def run(self): pass\n')
        method = next(d for d in semantic["declarations"] if d["name"] == "run")
        self.assertEqual(method.get("qualified_name"), "Item.run")

    def test_namespace_attribute_mutation_blocks_the_import_owner(self):
        semantic = self.parse('import core as c\ndef patch():\n    c.save = lambda: None\nc.save()\n')
        self.assertTrue(any(d["name"] == "c" and d["scope"] == "module" and d["kind"] == "unknown" for d in semantic["declarations"]))
        self.assertIn("attribute mutation invalidates a namespace binding", semantic["notes"])

    def test_nonlocal_mutation_finds_an_enclosing_import_binding(self):
        semantic = self.parse('def outer():\n    from core import save as keep\n    def change():\n        nonlocal keep\n        keep = lambda: None\n    change()\n    keep()\n')
        imported = next(i for i in semantic["imports"] if i["local"] == "keep")
        self.assertTrue(any(d["name"] == "keep" and d["scope"] == imported["scope"] and d["kind"] == "unknown" for d in semantic["declarations"]))

    def test_exec_blocks_affected_scope_even_with_known_declarations(self):
        semantic = self.parse('from core import save\nexec("save=lambda:None")\nsave()\n')
        module = next(s for s in semantic["scopes"] if s["id"] == "module")
        self.assertTrue(module.get("unresolved"))
        self.assertIn("exec", module.get("reason", ""))


class JavaScriptSemanticTests(unittest.TestCase):
    def parse(self, source, adapter=javascript.adapter, suffix="js"):
        language = "tsx" if suffix == "tsx" else adapter.language
        if ts.get_parser(language) is None:
            self.skipTest(f"{language} grammar unavailable")
        result = adapter.parse(source, "sample." + suffix)
        self.assertIsNotNone(getattr(result, "semantic", None), result.notes)
        return result.semantic

    def test_aliases_exports_template_and_literal_decoys(self):
        semantic = self.parse('import persist, {save as store} from "./core"; import * as ns from "./other";\n'
                              '// store()\nconst text = "store()";\n'
                              'export {store as publicSave}; export default persist;\n'
                              'const x = `store() ${ns.save()}`; store(); store();')
        self.assertEqual([(x["local"], x["imported"], x["mode"]) for x in semantic["imports"]],
                         [("persist", "default", "default"), ("store", "save", "named"), ("ns", "*", "namespace")])
        self.assertIn({"exported": "publicSave", "local": "store"}, semantic["exports"])
        self.assertIn({"exported": "default", "local": "persist"}, semantic["exports"])
        self.assertEqual([r["parts"] for r in semantic["references"] if r["kind"] == "call"],
                         [["ns", "save"], ["store"], ["store"]])

    def test_lexical_var_catch_destructured_parameters_and_nested_owners(self):
        semantic = self.parse('import {save} from "./core";\nfunction run({save: local}, [save]) {\n'
                              ' save(); { let save = other; save(); }\n'
                              ' try {} catch (save) { save(); }\n'
                              ' const nested = () => save();\n'
                              ' { var save = other; }\n}\nsave();')
        declarations = semantic["declarations"]
        run = next(d for d in declarations if d["name"] == "run")
        calls = [r for r in semantic["references"] if r["kind"] == "call"]
        self.assertEqual(calls[0]["caller"], run["id"])
        self.assertNotEqual(calls[0]["scope"], calls[1]["scope"])
        self.assertNotEqual(calls[0]["scope"], calls[2]["scope"])
        nested = next(d for d in declarations if d["name"] == "nested")
        self.assertEqual(calls[3]["caller"], nested["id"])
        self.assertTrue(any(d["name"] == "save" and d["kind"] == "binding" and d["scope"] == calls[0]["scope"] for d in declarations))
        self.assertEqual({d["name"] for d in declarations if d["kind"] == "parameter"}, {"local", "save"})

    def test_type_only_imports_and_direct_reexports_are_preserved(self):
        semantic = self.parse('import type {Runner as R} from "./types";\n'
                              'import {type Item, save as persist} from "./core";\n'
                              'export {persist as save}; export {save as again} from "./other";\n'
                              'persist();', typescript.adapter, "ts")
        by_local = {x["local"]: x for x in semantic["imports"]}
        self.assertTrue(by_local["R"]["type_only"])
        self.assertTrue(by_local["Item"]["type_only"])
        self.assertFalse(by_local["persist"].get("type_only", False))
        self.assertIn({"exported": "again", "local": "save", "module": "./other"}, semantic["exports"])

    def test_dynamic_callees_unicode_positions_and_same_line_calls(self):
        semantic = self.parse('const é = 1; save(); save(); obj[key](); factory().save();')
        calls = [r for r in semantic["references"] if r["kind"] == "call"]
        self.assertEqual([r["span"] for r in calls[:2]], [[1, 14, 1, 18], [1, 22, 1, 26]])
        self.assertEqual(sum(not r["parts"] for r in calls), 2)

    def test_for_bindings_and_var_arrow_capture_keep_lexical_scope(self):
        semantic = self.parse('import {save} from "./core"; function run(){\n'
                              ' for(let save of values) save();\n'
                              ' {let save = local; var nested = () => save();}\n'
                              ' for(var save of values) save();\n}')
        calls = [r for r in semantic["references"] if r["kind"] == "call"]
        scopes = {s["id"]: s for s in semantic["scopes"]}
        self.assertTrue(any(d["name"] == "save" and d["scope"] == calls[0]["scope"] for d in semantic["declarations"]))
        parent = scopes[calls[1]["scope"]]["parent"]
        self.assertEqual(scopes[parent]["kind"], "block")
        self.assertTrue(any(d["name"] == "save" and d["scope"] == parent for d in semantic["declarations"]))
        run = next(s for s in scopes.values() if s["kind"] == "function" and s["parent"] == "module")
        self.assertTrue(any(d["name"] == "save" and d["scope"] == run["id"] and d["kind"] == "binding" for d in semantic["declarations"]))

    def test_method_names_are_not_lexical_bindings_and_overloads_block_guessing(self):
        semantic = self.parse('import {save} from "./core"; class C { save() {} run(){save()} }\n'
                              'function work(x: string): void; function work(x: number): void;\n'
                              'function work(x: unknown) {} work(1);', typescript.adapter, "ts")
        self.assertTrue(all(d.get("lexical") is False for d in semantic["declarations"] if d["kind"] == "method"))
        self.assertEqual(sum(d["name"] == "work" and d["kind"] == "unknown" for d in semantic["declarations"]), 2)

    def test_assignment_inside_a_block_rebinds_the_existing_owner(self):
        semantic = self.parse('function save() {} function run(){ if(flag){save = other;} save(); }')
        self.assertTrue(any(d["name"] == "save" and d["scope"] == "module" and d["kind"] == "binding" for d in semantic["declarations"]))

    def test_default_parameter_calls_cannot_link_to_body_only_declarations(self):
        semantic = self.parse('import {save} from "./core"; function run(x = save()) { function save() {} save(); }')
        calls = [r for r in semantic["references"] if r["kind"] == "call"]
        body_save = next(d for d in semantic["declarations"] if d["name"] == "save" and d["kind"] == "function")
        self.assertNotEqual(calls[0]["scope"], body_save["scope"])
        scopes = {s["id"]: s for s in semantic["scopes"]}
        self.assertEqual(scopes[calls[0]["scope"]]["parent"], "module")
        self.assertEqual(scopes[calls[1]["scope"]]["parent"], calls[0]["scope"])

    def test_type_names_and_runtime_enum_bindings_do_not_become_outer_calls(self):
        semantic = self.parse('import {save} from "./core";\nfunction run(){ enum save {One}; save(); }\n'
                              'function generic<save>(arg: save) { save(); }', typescript.adapter, "ts")
        run = next(s for s in semantic["scopes"] if s["kind"] == "function")
        self.assertTrue(any(d["name"] == "save" and d["scope"] == run["id"] and d["kind"] in ("binding", "unknown") for d in semantic["declarations"]))
        generic = next(d for d in semantic["declarations"] if d["name"] == "generic")
        scope = next(s for s in semantic["scopes"] if s.get("caller") == generic["id"])
        self.assertTrue(scope.get("unresolved"))

    def test_block_function_legacy_hoisting_is_explicitly_unresolved(self):
        semantic = self.parse('function save(){} function run(){ if(flag){function save(){}} save(); }')
        run = next(d for d in semantic["declarations"] if d["name"] == "run")
        scope = next(s for s in semantic["scopes"] if s.get("caller") == run["id"])
        self.assertTrue(any(d["name"] == "save" and d["kind"] == "unknown" and d["scope"] == scope["id"] for d in semantic["declarations"]))

    def test_class_method_qualified_names_and_object_method_owners(self):
        semantic = self.parse('class Item { run(){save()} } const object = {method(){save()}};')
        method = next(d for d in semantic["declarations"] if d["name"] == "run")
        self.assertEqual(method.get("qualified_name"), "Item.run")
        self.assertTrue(all(r["caller"] for r in semantic["references"] if r["kind"] == "call"))

    def test_named_function_and_class_expressions_do_not_leak_bindings(self):
        semantic = self.parse('consume(function save(){save()}); save(); const Holder = class Save {}; new Save();')
        leaked = [d for d in semantic["declarations"] if d["scope"] == "module" and d["name"] in ("save", "Save")]
        self.assertTrue(leaked)
        self.assertTrue(all(d.get("lexical") is False for d in leaked))
        internal = next(d for d in semantic["declarations"] if d["name"] == "Save" and d["scope"] != "module")
        self.assertEqual(internal["kind"], "class-name")

    def test_computed_method_keys_keep_calls_in_the_defining_context(self):
        semantic = self.parse('function save(){}; class Holder { [save()]() {} }')
        calls = [r for r in semantic["references"] if r["kind"] == "call"]
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["parts"], ["save"])
        self.assertIsNone(calls[0]["caller"])
        self.assertEqual(calls[0]["scope"], "module")

    def test_jsx_intrinsic_tags_attributes_and_closing_tags_are_not_lexical_reads(self):
        semantic = self.parse('function save(){} function Save(){}\n'
                              'const view = <><save save={save()}/><Save onClick={save}></Save><ns:save/></>;')
        save_refs = [r for r in semantic["references"] if r["parts"] == ["save"]]
        self.assertEqual([r["kind"] for r in save_refs], ["call", "read"])
        self.assertEqual(sum(r["parts"] == ["Save"] for r in semantic["references"]), 1)
        self.assertFalse(any(r["parts"] == ["ns"] for r in semantic["references"]))

    def test_malformed_and_no_grammar_do_not_claim_ast_semantics(self):
        if ts.get_parser("javascript") is not None:
            self.assertIsNone(javascript.adapter.parse("function broken( {", "x.js").semantic)
        with mock.patch.object(javascript, "get_parser", return_value=None):
            self.assertIsNone(getattr(javascript.adapter.parse("save()", "x.js"), "semantic", "missing"))

    def test_typescript_semantic_extraction_does_not_parse_twice(self):
        pair = ts.get_parser("typescript")
        if pair is None:
            self.skipTest("TypeScript grammar unavailable")
        parser, language = pair
        counted = mock.Mock(wraps=parser)
        with mock.patch.object(typescript, "get_parser", return_value=(counted, language)):
            self.parse('export const save = () => 1; save();', typescript.adapter, "ts")
        self.assertEqual(counted.parse.call_count, 1)


if __name__ == "__main__":
    unittest.main()
