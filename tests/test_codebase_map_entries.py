"""Entry candidates: what each reader finds where a flow may start, grouped by the shape it is written in."""

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "daodan/core"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
import flows  # noqa: E402
import snapshot  # noqa: E402
from daodan.core import entries  # noqa: E402  (by its package: benchmarks/system-map has an entries.py too)


def edge(source: str, target: str, kind: str, site: str) -> dict:
    return {"from": source, "to": target, "type": kind, "origin": "diretto", "site": site}


LINKS = {"edges": [edge("a.ts::main", "b.ts::helper", "chiama", "a.ts:9"),
                   edge("a.ts::main", "c.ts::leaf", "chiama", "a.ts:3"),
                   edge("b.ts::helper", "c.ts::leaf", "chiama", "b.ts:2"),
                   edge("d.ts::pay", "module:stripe", "usa", "d.ts"),
                   edge("store:db/orders", "e.ts::list", "legge", "e.ts:7"),
                   edge("e.ts::list", "b.ts::helper", "chiama", "e.ts:5"),
                   edge("f.ts::save", "store:db/orders", "scrive", "f.ts:2"),
                   edge("a.ts::main", "f.ts::save", "chiama", "a.ts:12"),
                   edge("store:db/orders", "g.ts::show", "legge", "g.ts:3")]}


class ResidualTests(unittest.TestCase):
    def test_a_candidate_is_reader_shape_site_and_symbol(self):
        self.assertEqual(entries.residual(LINKS), [
            {"reader": "residuo", "shape": "residuo", "site": "a.ts:3", "symbol": "a.ts::main"},  # its first call
            {"reader": "residuo", "shape": "residuo", "site": "d.ts", "symbol": "d.ts::pay"},     # it uses a library
            {"reader": "residuo", "shape": "residuo", "site": "e.ts:5", "symbol": "e.ts::list"},  # a read calls no one
            {"reader": "residuo", "shape": "residuo", "site": "g.ts:3", "symbol": "g.ts::show"}])  # it reads a store

    def test_shapes_count_the_candidates_of_a_shape_with_one_example(self):
        found = [{"reader": "argomento", "shape": "*.on#arg1", "site": "x.ts:4", "symbol": "x.ts::a"},
                 *entries.residual(LINKS),
                 {"reader": "argomento", "shape": "*.on#arg1", "site": "y.ts:8", "symbol": "y.ts::b"}]
        self.assertEqual(entries.shapes(found), [
            {"reader": "residuo", "shape": "residuo", "count": 4, "example": {"site": "a.ts:3", "symbol": "a.ts::main"}},
            {"reader": "argomento", "shape": "*.on#arg1", "count": 2, "example": {"site": "x.ts:4", "symbol": "x.ts::a"}}])

    def test_a_shape_s_example_carries_the_label_of_its_first_candidate(self):
        found = [{"reader": "attributo", "shape": "onClick", "site": "v.tsx:4", "symbol": "v.tsx::save", "label": "Salva"}]
        self.assertEqual(entries.shapes(found)[0]["example"], {"site": "v.tsx:4", "symbol": "v.tsx::save", "label": "Salva"})


def snapshot_of(work: Path, sources: dict[str, str] | Path) -> Path:
    """The manifest of a fixture: a folder copied, or files written, then committed."""
    app = work / "app"
    if isinstance(sources, Path):
        shutil.copytree(sources, app)
    else:
        for rel, text in sources.items():
            (app / rel).parent.mkdir(parents=True, exist_ok=True)
            (app / rel).write_text(text, encoding="utf-8", newline="\n")
    for command in (["git", "init", "-q"], ["git", "add", "-A"],
                    ["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "fixture"]):
        subprocess.run(command, cwd=app, check=True, capture_output=True)
    manifest = work / "snapshot/manifest.sqlite"
    snapshot.main(["write", str(app), "--out", str(manifest), "--no-engine", "--no-index"])
    return manifest


class FixtureTests(unittest.TestCase):
    """On benchmarks/flow-model, without rules: the job that nothing calls is a candidate, what it calls is not."""

    @classmethod
    def setUpClass(cls):
        cls.work = Path(tempfile.mkdtemp(prefix="entries-")).resolve()
        manifest = snapshot_of(cls.work, ROOT / "benchmarks/flow-model/app")
        cls.links = flows.link_facts(manifest, [])
        cls.found = entries.candidates(cls.links, manifest)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.work, True)

    def test_the_job_is_a_residual_candidate_and_what_it_calls_is_not(self):
        symbols = {candidate["symbol"] for candidate in self.found}
        self.assertIn("server/jobs.py::retry_declined", symbols)
        self.assertNotIn("server/payments.py::charge_order", symbols)
        job = next(c for c in self.found if c["symbol"] == "server/jobs.py::retry_declined")
        self.assertEqual(job["site"], "server/jobs.py:8")

    def test_candidates_are_every_reader_s(self):
        self.assertEqual([c for c in self.found if c["reader"] == "residuo"], entries.residual(self.links))
        passed = sorted((c["shape"], c["site"], c["symbol"]) for c in self.found if c["reader"] != "residuo")
        self.assertEqual(passed, [("button#arg1", "web/cart.ts:18", "web/cart.ts::toggleTheme"),
                                  ("button#arg1", "web/checkout.ts:22", "web/checkout.ts::onPayClick"),
                                  ("route", "admin/orders.py:6", "admin/orders.py::list_all_orders"),
                                  ("route", "server/orders.py:10", "server/orders.py::list_orders"),
                                  ("route", "server/payments.py:16", "server/payments.py::create_payment"),
                                  ("scheduled", "server/jobs.py:5", "server/jobs.py::retry_declined")])

    def test_the_job_s_decorator_carries_its_schedule(self):
        self.assertEqual([c.get("argument") for c in self.found if c["reader"] == "decoratore"
                          and c["symbol"] == "server/jobs.py::retry_declined"], ["*/10 * * * *"])



class PassedTests(unittest.TestCase):
    """A function of the project given as a value to a call or to a markup attribute, with the shape it is written in."""

    SOURCES = {
        "web/actions.ts": "export function save(): void {}\n",
        "web/bus.ts": "export const bus: any = null;\n",
        "web/page.ts": ("import { on } from 'events-lib';\nimport { save } from './actions';\nimport { bus } from './bus';\n"
                        "export function mount(): void {\n  const btn = document.querySelector('#s');\n"
                        "  btn.addEventListener('click', onSave);\n  on('ready', save);\n  bus.on('paid', () => save());\n"
                        "  document.addEventListener('keyup', onSave);\n  helper(42, 'x');\n  bus.on(/[)]/, onSave);\n}\n"
                        "function onSave(): void { save(); }\nfunction helper(n: number, s: string): void {}\n"),
        "api/server.py": ("import threading\nfrom lib import Router\n\nrouter = Router()\n\n\ndef save(body):\n    return body\n\n\n"
                          "router.post('/x', save)\nthreading.Thread(target=save)\nrouter.get('/y', 'save')\n\n\n"
                          "class Win:\n    def build(self):\n        self.button.connect('clicked', self.on_click)\n\n"
                          "    def on_click(self):\n        pass\n\n    def wire(self):\n"
                          "        self.button.connect('closed', self.on_close)\n\n\n"
                          "def items():\n    pass\n\n\ndef value():\n    pass\n\n\ndef x():\n    pass\n\n\n"
                          "def handle(items, value, x):\n    len(items)\n    str(value)\n    hasattr(value, 'a')\n"
                          "    isinstance(x, Win)\n"),
        "web/view.tsx": ("declare function t(key: string): string;\n"
                         "export function View(props: { label: string; onClose: () => void }) {\n"
                         "  const save = () => {};\n  const close = () => {};\n  const open = () => {};\n"
                         "  const pick = () => {};\n  const clear = () => {};\n  return (\n    <form>\n"
                         "      <button aria-label=\"Salva il carrello\" onClick={save}>x</button>\n"
                         "      <button onClick={() => close()}>\n        <b>Chiudi</b>\n      </button>\n"
                         "      <input placeholder=\"Cerca\" onChange={pick} />\n"
                         "      <a href=\"#\" onClick={open}>{t('apri')}</a>\n"
                         "      <button onClick={clear}>{props.label}</button>\n"
                         "      <a onClick={open}>{t('esci')}</a>\n"
                         "      <button onClick={props.onClose}>y</button>\n    </form>\n  );\n}\n"
                         "export class Panel {\n  save() {}\n  render() {\n    return <button onClick={this.save}>Salva</button>;\n  }\n}\n"),
        "web/cart.tsx": ("declare function t(key: string): string;\nexport function Cart() {\n  const save = () => {};\n"
                         "  const pay = () => {};\n  return <p><button onClick={save}>{t('cart.save')}</button>"
                         "<a onClick={pay}>{t('cart.pay')}</a></p>;\n}\n"),
        "web/locales/it.json": '{\n  "apri": "Apri il carrello",\n  "esci": "Esci",\n  "cart": {"save": "Salva"}\n}\n',
        "web/locales/it.yml": "cart:\n  pay: Paga\n",
        "web/locales/en.json": '{\n  "esci": "Log out"\n}\n',
    }

    @classmethod
    def setUpClass(cls):
        cls.work = Path(tempfile.mkdtemp(prefix="entries-passed-")).resolve()
        manifest = snapshot_of(cls.work, cls.SOURCES)
        cls.found = [c for c in entries.candidates(flows.link_facts(manifest, []), manifest) if c["reader"] != "residuo"]

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.work, True)

    def of(self, reader):
        return sorted((c for c in self.found if c["reader"] == reader), key=lambda c: c["site"])

    def test_a_function_given_to_a_call_is_a_candidate_with_the_call_as_written(self):
        self.assertEqual([(c["shape"], c["site"], c["symbol"]) for c in self.of("argomento") if "gap" not in c], [
            ("*.post#arg1", "api/server.py:11", "api/server.py::save"),          # a project variable is *
            ("threading.Thread#target", "api/server.py:12", "api/server.py::save"),  # a keyword is its position
            ("*.*.connect#arg1", "api/server.py:18", "api/server.py::Win.on_click"),  # the method of its class (D5)
            ("*.on#arg1", "web/page.ts:11", "web/page.ts::onSave"),             # a `)` the text split on
            ("*.addEventListener#arg1", "web/page.ts:6", "web/page.ts::onSave"),
            ("on#arg1", "web/page.ts:7", "web/actions.ts::save"),               # a library's name stays
            ("*.on#arg1", "web/page.ts:8", "web/page.ts::function@8:17"),       # the inline event handler
            ("document.addEventListener#arg1", "web/page.ts:9", "web/page.ts::onSave")])  # a global stays

    def test_a_method_its_class_does_not_define_is_a_candidate_without_handler_that_says_why(self):
        self.assertEqual([c for c in self.of("argomento") if "gap" in c], [
            {"reader": "argomento", "shape": "*.*.connect#arg1", "site": "api/server.py:24",
             "symbol": "api/server.py::Win.wire",
             "gap": "handler self.on_close not resolved: Win does not define on_close"}])

    def test_a_variable_that_shares_its_name_with_a_function_is_no_candidate(self):
        self.assertEqual([c["shape"] for c in self.of("argomento")
                          if c["shape"].split("#")[0] in ("len", "str", "hasattr", "isinstance")], [])

    def test_a_markup_attribute_bound_to_a_function_has_its_name_as_shape_and_the_label_of_its_element(self):
        self.assertEqual([(c["shape"], c["site"], c["symbol"], c["label"]) for c in self.of("attributo")], [
            ("onClick", "web/cart.tsx:5", "web/cart.tsx::Cart.save", "Salva"),               # a dotted key, nested
            ("onClick", "web/cart.tsx:5", "web/cart.tsx::Cart.pay", "cart.pay"),             # only a .yml defines it
            ("onClick", "web/view.tsx:10", "web/view.tsx::View.save", "Salva il carrello"),  # aria-label first
            ("onClick", "web/view.tsx:11", "web/view.tsx::function@11:23", "Chiudi"),             # the element's text
            ("onChange", "web/view.tsx:14", "web/view.tsx::View.pick", "Cerca"),              # its placeholder
            ("onClick", "web/view.tsx:15", "web/view.tsx::View.open", "Apri il carrello"),    # one file defines the key
            ("onClick", "web/view.tsx:16", "web/view.tsx::View.clear", None),                 # computed: no label
            ("onClick", "web/view.tsx:17", "web/view.tsx::View.open", "esci"),                # two files: the key
            ("onClick", "web/view.tsx:25", "web/view.tsx::Panel.save", "Salva")])             # this.save: its class's
        self.assertNotIn("gap", self.of("attributo")[-1])
        self.assertEqual([c.get("key") for c in self.of("attributo")],
                         ["cart.save", "cart.pay", None, None, None, "apri", None, "esci", None])
        self.assertEqual([c["label_gap"] for c in self.of("attributo") if "label_gap" in c], [
            "key cart.pay stays: 0 .json or .toml files define it as text, and a locale in another format is not read",
            "key esci stays: 2 .json or .toml files define it as text, and a locale in another format is not read"])


class DesktopTests(unittest.TestCase):
    """A desktop interface written in code, read statically like markup: the event, the method it starts, the
    label. Two files in the style of two Python toolkits; neither is installed nor imported."""

    SOURCES = {
        "ui/tk_app.py": ("import tkinter as tk\n\n\nclass App:\n    def __init__(self, root):\n"
                         "        self.title = \"App\"\n        self.choice = tk.StringVar()\n"
                         "        tk.Button(root, text=\"Avvia\", command=self.start).pack()\n"
                         "        tk.Button(root, text=self.title, command=self.stop)\n"
                         "        tk.OptionMenu(root, self.choice, \"a\", \"b\", command=self.pick)\n"
                         "        tk.Button(root, text=\"Esci\", command=self.quit_all)\n"
                         "        self.done = root.done\n        tk.Button(root, text=\"Fine\", command=self.done)\n\n"
                         "    def start(self):\n        pass\n\n    def stop(self):\n        pass\n\n"
                         "    def pick(self, value):\n        pass\n"),
        "ui/qt_app.py": ("from PySide6.QtWidgets import QPushButton, QWidget\n\n\nclass Window(QWidget):\n"
                         "    def __init__(self):\n        super().__init__()\n        self.name = \"Apri file\"\n"
                         "        self.save_btn = QPushButton(\"Salva\")\n        self.open_btn = QPushButton(self.name)\n"
                         "        self.quit_btn = QPushButton(\"Esci\")\n        self.build()\n\n    def build(self):\n"
                         "        self.save_btn.clicked.connect(self.save)\n        self.open_btn.setText(\"Apri\")\n"
                         "        self.open_btn.clicked.connect(self.open)\n"
                         "        self.quit_btn.clicked.connect(self.close)\n\n"
                         "    def save(self):\n        pass\n\n    def open(self):\n        pass\n"),
    }

    @classmethod
    def setUpClass(cls):
        cls.work = Path(tempfile.mkdtemp(prefix="entries-desktop-")).resolve()
        manifest = snapshot_of(cls.work, cls.SOURCES)
        found = entries.candidates(flows.link_facts(manifest, []), manifest)
        cls.found = sorted((c for c in found if c["reader"] == "argomento"), key=lambda c: c["site"])

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.work, True)

    def of(self, file):
        return [(c["shape"], c["site"], c["symbol"], c.get("label"), c.get("gap"))
                for c in sorted(self.found, key=lambda c: int(c["site"].rpartition(":")[2])) if c["site"].startswith(file)]

    def test_a_signal_connected_on_an_attribute_takes_the_label_of_the_call_that_made_it(self):
        self.assertTrue(all(row["event"] == "clicked" for row in self.found if "qt_app" in row["site"]))
        self.assertEqual(self.of("ui/qt_app.py"), [
            ("*.*.*.connect#arg0", "ui/qt_app.py:14", "ui/qt_app.py::Window.save", "Salva", None),  # its creator
            ("*.*.*.connect#arg0", "ui/qt_app.py:16", "ui/qt_app.py::Window.open", "Apri", None),   # a later setText
            ("*.*.*.connect#arg0", "ui/qt_app.py:17", "ui/qt_app.py::Window.build", "Esci",
             "handler self.close not resolved: Window does not define close")])                   # inherited

    def test_a_constructor_s_command_takes_the_label_of_its_text(self):
        self.assertEqual(self.of("ui/tk_app.py"), [  # `self.choice`, `self.title`: values the object holds, none
            ("tk.Button#command", "ui/tk_app.py:8", "ui/tk_app.py::App.start", "Avvia", None),     # text= beside it
            ("tk.Button#command", "ui/tk_app.py:9", "ui/tk_app.py::App.stop", None, None),         # computed: none
            ("tk.OptionMenu#command", "ui/tk_app.py:10", "ui/tk_app.py::App.pick", None, None),    # values, no label
            ("tk.Button#command", "ui/tk_app.py:11", "ui/tk_app.py::App.__init__", "Esci",
             "handler self.quit_all not resolved: App does not define quit_all"),
            ("tk.Button#command", "ui/tk_app.py:13", "ui/tk_app.py::App.__init__", "Fine",
             "handler self.done not resolved: App assigns done at run time")])


class LabelTests(unittest.TestCase):
    """The label a person reads on a control, from the syntax tree of the element that carries the attribute."""

    def label(self, text: str) -> str | None:
        grammar = entries.QUERIES["grammars"]["markup"]  # the grammar the data gives a page of markup
        return next(b for b in entries.bindings(text.encode("utf-8"), grammar) if b["shape"] == "onclick")["label"]

    def test_on_html_the_order_is_aria_label_text_title_or_placeholder_then_a_translation_key(self):
        for text, want in (
                ('<button onclick="go()" aria-label="Vai">Go</button>', "Vai"),
                ('<button type="button" title="Invia il modulo"\n  onclick="send()">\n  Invia\n</button>', "Invia"),
                ('<input onclick="pick()" placeholder="Cerca">\n<p>dopo</p>', "Cerca"),
                ('<button title="Chiudi" onclick="x()">{{ $t(\'close\') }}</button>', "Chiudi"),
                ('<button onclick="x()">{{ $t(\'salva\') }}</button>', "salva"),
                ('<button onclick="x()">{{ name }}</button>', None),
                ('<button onclick="x()" title="{{ name }}"></button>', None)):
            with self.subTest(text=text):
                self.assertEqual(self.label(text), want)

    def test_every_grammar_s_query_compiles(self):
        for section in ("queries", "decorators"):
            for grammar in entries.QUERIES[section]:
                with self.subTest(section=section, grammar=grammar):
                    self.assertIsNotNone(entries._query(grammar, section))


class MarkupTests(unittest.TestCase):
    """What lines cannot hold: an attribute over several lines, an element inside another, a self-closing one, a
    string with `>`, and the other ways of writing a binding, each file read by its own grammar."""

    SOURCES = {
        "web/form.tsx": ("export function Form() {\n  const save = () => {};\n  const close = () => {};\n"
                         "  const toggle = () => {};\n  return (\n    <div onClick={toggle}>\n      <button\n"
                         "        aria-label=\"a > b\"\n        onClick={\n          save\n        }\n      >x</button>\n"
                         "      <input placeholder=\"Cerca\" onChange={close} />\n    </div>\n  );\n}\n"),
        "web/panel.vue": ("<template>\n  <div>\n    <button @click=\"save\" aria-label=\"Salva\">x</button>\n"
                          "    <button v-on:click=\"close()\">{{ $t('chiudi') }}</button>\n  </div>\n</template>\n"
                          "<script setup lang=\"ts\">\nfunction save(): void {}\nfunction close(): void {}\n"
                          "window.addEventListener('resize', close);\n</script>\n"),
        "web/box.svelte": ("<script>\n  function save() {}\n  function go() {}\n</script>\n"
                           "<button on:click={save} title=\"Salva\">{$t('x')}</button>\n"
                           "<button onclick={() => go()}>Vai</button>\n"),
        "web/app.component.html": "<button (click)=\"save()\">{{ 'salva' | translate }}</button>\n",
        "web/page.html": "<form>\n  <button onclick=\"send()\">\n    Invia\n  </button>\n</form>\n",
    }

    @classmethod
    def setUpClass(cls):
        cls.work = Path(tempfile.mkdtemp(prefix="entries-markup-")).resolve()
        manifest = snapshot_of(cls.work, cls.SOURCES)
        cls.all = entries.candidates(flows.link_facts(manifest, []), manifest)
        cls.found = sorted((c for c in cls.all if c["reader"] == "attributo"), key=lambda c: c["site"])

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.work, True)

    def test_each_binding_comes_from_the_tree_with_its_shape_symbol_and_label(self):
        self.assertEqual([(c["shape"], c["site"], c["symbol"], c["label"], c.get("key"), c.get("gap"))
                          for c in self.found], [
            ("(click)", "web/app.component.html:1", "web/app.component.html::<module>", "salva", "salva",
             "handler save not resolved"),                       # a method of the component: D5 resolves it
            ("on:click", "web/box.svelte:5", "web/box.svelte::save", "Salva", None, None),  # computed text: title
            ("onclick", "web/box.svelte:6", "web/box.svelte::go", "Vai", None, None),
            ("onChange", "web/form.tsx:13", "web/form.tsx::Form.close", "Cerca", None, None),  # self-closing
            ("onClick", "web/form.tsx:6", "web/form.tsx::Form.toggle", "x", None, None),  # the text inside
            ("onClick", "web/form.tsx:9", "web/form.tsx::Form.save", "a > b", None, None),  # over lines, inner label
            ("onclick", "web/page.html:2", "web/page.html::<module>", "Invia", None, "handler send not resolved"),
            ("@click", "web/panel.vue:3", "web/panel.vue::save", "Salva", None, None),
            ("v-on:click", "web/panel.vue:4", "web/panel.vue::close", "chiudi", "chiudi", None)])

    def test_a_call_in_a_component_s_script_is_read_with_the_markup_blanked(self):
        self.assertEqual([(c["shape"], c["site"], c["symbol"]) for c in self.all if c["reader"] == "argomento"],
                         [("window.addEventListener#arg1", "web/panel.vue:10", "web/panel.vue::close")])


class ReactTests(unittest.TestCase):
    """The ways a React component binds a handler, one per line: a function written in place binds what it calls,
    as the snapshot resolved it; a prop, a state setter or a library's function names no function of the project."""

    SOURCES = {
        "web/actions.ts": "".join(f"export function {name}(): void {{}}\n"
                                  for name in ("act", "save", "a", "b", "valid", "done", "fail", "onClose")),
        "web/dialog.tsx": ("import { fail } from './actions';\n"
                           "export function Dialog({ onClose }: { onClose: () => void }) {\n"
                           "  return <p><button onClick={onClose}>x</button><button onClick={() => onClose()}>y</button>\n"
                           "    <button onClick={() => fail()}>z</button></p>;\n}\n"),
        "web/forms.tsx": "\n".join([
            "import { useState } from 'react';", "import { useNavigate } from 'react-router-dom';",
            "import { act, save, a, b, valid, done, fail } from './actions';", "import { Dialog } from './dialog';",
            "export function Forms(props: { busy: boolean; onClose: () => void }) {",
            "  const [value, setValue] = useState('');", "  const navigate = useNavigate();",
            "  const handleSave = () => {};", "  return (", "    <div>",
            "      <button onClick={handleSave}>a name</button>",
            "      <button onClick={() => handleSave()}>its one call</button>",
            "      <button onClick={() => void act('X')}>void</button>",
            "      <button onClick={() => { a(); b(); }}>a block</button>",
            "      <button onClick={async () => { await save(); }}>await in a block</button>",
            "      <button onClick={async () => await save()}>await</button>",
            "      <button onClick={(e) => { e.preventDefault(); save(); }}>prevent, then call</button>",
            "      <button onClick={() => save().then(done)}>a chain</button>",
            "      <button onClick={() => valid() && save()}>and</button>",
            "      <button onClick={() => { try { save(); } catch { fail(); } }}>try</button>",
            "      <button onClick={function () { save(); }}>function</button>",
            "      <button onClick={() => save() as unknown}>as</button>",
            "      <button onClick={e =>", "        save()", "      }>over lines</button>",
            "      <button onClick={props.busy ? undefined : below}>one branch</button>",
            "      <button onClick={props.busy ? () => done() : save}>both branches</button>",
            "      <Dialog onClose={handleSave} />",
            "      <button onClick={props.onClose}>a prop</button>",
            "      <input onChange={(event) => setValue(event.target.value)} value={value} />",
            "      <button onClick={() => navigate('/x')}>navigate</button>",
            "    </div>", "  );", "}", "function below(): void {}", ""]),
    }

    @classmethod
    def setUpClass(cls):
        cls.work = Path(tempfile.mkdtemp(prefix="entries-react-")).resolve()
        manifest = snapshot_of(cls.work, cls.SOURCES)
        cls.links = flows.link_facts(manifest, [])
        found = entries.candidates(cls.links, manifest)
        cls.found = [c for c in found if c["reader"] == "attributo"]

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.work, True)

    def of(self, file):
        return sorted((int(c["site"].rpartition(":")[2]), c["symbol"], c["label"], c.get("gap"))
                      for c in self.found if c["site"].startswith(f"{file}:"))

    def test_each_inline_handler_is_a_single_declaration_and_its_calls_are_separate_edges(self):
        sites = {(line, label): symbol for line, symbol, label, gap in self.of("web/forms.tsx")
                 if "::function@" in symbol and gap is None}
        expected = {
            (12, "its one call"): ["web/forms.tsx::Forms.handleSave"], (13, "void"): ["web/actions.ts::act"],
            (14, "a block"): ["web/actions.ts::a", "web/actions.ts::b"], (15, "await in a block"): ["web/actions.ts::save"],
            (16, "await"): ["web/actions.ts::save"], (17, "prevent, then call"): ["web/actions.ts::save"],
            (18, "a chain"): ["web/actions.ts::save"], (19, "and"): ["web/actions.ts::save", "web/actions.ts::valid"],
            (20, "try"): ["web/actions.ts::fail", "web/actions.ts::save"], (21, "function"): ["web/actions.ts::save"],
            (22, "as"): ["web/actions.ts::save"], (23, "over lines"): ["web/actions.ts::save"],
            (27, "both branches"): ["web/actions.ts::done"], (30, None): [], (31, "navigate"): [],
        }
        self.assertEqual({site: sorted(e["to"] for e in self.links["edges"]
                                       if e["from"] == symbol and e["type"] == "chiama")
                          for site, symbol in sites.items()}, expected)
        direct = [(line, symbol) for line, symbol, _, _ in self.of("web/forms.tsx") if "::function@" not in symbol]
        self.assertEqual(direct, [(11, "web/forms.tsx::Forms.handleSave"), (26, "web/forms.tsx::below"),
                                  (27, "web/actions.ts::save"), (28, "web/forms.tsx::Forms.handleSave")])

    def test_an_inline_handler_calling_an_unknown_prop_has_no_edge_to_the_unrelated_local_function(self):
        handlers = {label: symbol for _, symbol, label, _ in self.of("web/dialog.tsx")}
        self.assertEqual(set(handlers), {"y", "z"})
        self.assertEqual([(e["from"], e["to"]) for e in self.links["edges"]
                          if e["type"] == "chiama" and e["from"] in handlers.values()],
                         [(handlers["z"], "web/actions.ts::fail")])


class DecoratorTests(unittest.TestCase):
    """A function or method carrying a decorator or an annotation, one file per grammar, each with a decorator that
    is no entry (`staticmethod`, `Override`, `Deprecated`, `Obsolete`, `test`, `Memo`): no classification here."""

    SOURCES = {
        "api/app.py": ("from fastapi import FastAPI\n\napp = FastAPI()\n\n\n@app.get(\"/items/{id}\")\n@auth\ndef read(id):\n"
                       "    return id\n\n\nclass Repo:\n    @staticmethod\n    def make():\n        pass\n\n\n"
                       "@app.post(f\"/x/{read}\")\ndef computed():\n    pass\n\n\n@celery.task(name=\"jobs.nightly\")\n"
                       "async def nightly():\n    pass\n"),
        "api/broken.py": "@app.get(\"/broken\")\ndef broken(:\n    pass\n",
        "src/Jobs.java": ("package x;\n\npublic class Jobs {\n    @Scheduled(cron = \"0 0 3 * * *\")\n"
                          "    public void nightly() {}\n\n    @GetMapping(\"/orders\")\n    public String list() { return \"\"; }\n\n"
                          "    @Override\n    public String toString() { return \"\"; }\n}\n"),
        "src/Listen.kt": ("class Listen {\n    @KafkaListener(topics = [\"orders\"])\n    fun onOrder(msg: String) {}\n\n"
                          "    @Deprecated(\"old\")\n    fun old() {}\n}\n"),
        "src/Ctl.cs": ("public class Ctl {\n    [HttpGet(\"/users\")]\n    public string Get() { return \"\"; }\n\n"
                       "    [Obsolete]\n    public void Old() {}\n}\n"),
        "src/main.rs": "#[tauri::command]\nfn greet(name: &str) -> String { name.to_string() }\n\n#[test]\nfn checks() {}\n",
        "web/cats.ts": "export class Cats {\n  @Get(':id')\n  find() {}\n\n  @Memo\n  other() {}\n}\n",
        "web/store.js": "class Store {\n  @action('save')\n  save() {}\n}\n",
    }

    @classmethod
    def setUpClass(cls):
        cls.work = Path(tempfile.mkdtemp(prefix="entries-decorators-")).resolve()
        cls.manifest = snapshot_of(cls.work, cls.SOURCES)
        found = entries.candidates(flows.link_facts(cls.manifest, []), cls.manifest)
        cls.found = sorted((c for c in found if c["reader"] == "decoratore"), key=lambda c: c["site"])

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.work, True)

    def test_a_decorated_function_has_the_decorator_s_name_as_shape_and_its_first_text_beside(self):
        self.assertEqual([(c["shape"], c["site"], c["symbol"], c.get("argument")) for c in self.found if "gap" not in c], [
            ("staticmethod", "api/app.py:13", "api/app.py::Repo.make", None),
            ("app.post", "api/app.py:18", "api/app.py::computed", None),                    # computed text: none
            ("celery.task", "api/app.py:23", "api/app.py::nightly", "jobs.nightly"),        # a keyword's text
            ("app.get", "api/app.py:6", "api/app.py::read", "/items/{id}"),
            ("auth", "api/app.py:7", "api/app.py::read", None),                             # two on one function
            ("HttpGet", "src/Ctl.cs:2", "src/Ctl.cs::Ctl.Get", "/users"),
            ("Obsolete", "src/Ctl.cs:5", "src/Ctl.cs::Ctl.Old", None),
            ("Override", "src/Jobs.java:10", "src/Jobs.java::Jobs.toString", None),
            ("Scheduled", "src/Jobs.java:4", "src/Jobs.java::Jobs.nightly", "0 0 3 * * *"),  # a cron expression
            ("GetMapping", "src/Jobs.java:7", "src/Jobs.java::Jobs.list", "/orders"),
            ("KafkaListener", "src/Listen.kt:2", "src/Listen.kt::Listen.onOrder", None),    # a list is no text
            ("Deprecated", "src/Listen.kt:5", "src/Listen.kt::Listen.old", "old"),
            ("tauri::command", "src/main.rs:1", "src/main.rs::greet", None),
            ("test", "src/main.rs:4", "src/main.rs::checks", None),
            ("Get", "web/cats.ts:2", "web/cats.ts::Cats.find", ":id"),
            ("Memo", "web/cats.ts:5", "web/cats.ts::Cats.other", None),
            ("action", "web/store.js:2", "web/store.js::Store.save", "save")])

    def test_a_decorator_on_a_function_the_snapshot_does_not_declare_is_of_the_file_and_says_so(self):
        self.assertEqual([c for c in self.found if "gap" in c], [
            {"reader": "decoratore", "shape": "app.get", "site": "api/broken.py:1", "symbol": "api/broken.py::<module>",
             "gap": "the snapshot declares no function at line 2", "argument": "/broken"}])

    def test_a_written_rule_with_decorates_reaches_a_python_decorator_and_not_a_java_annotation(self):
        rules = flows.validate_rules([{"written": "app.get", "link": "ingresso", "entry": "rotta", "decorates": True},
                                      {"written": "GetMapping", "link": "ingresso", "entry": "rotta", "decorates": True}])
        rows = flows.link_facts(self.manifest, rules)["entries"]
        self.assertEqual([e["symbol"] for e in rows if e["kind"] == "rotta"], ["api/app.py::read"])
        self.assertIn(("src/main.rs::greet", "comando"), [(e["symbol"], e["kind"]) for e in rows])


class NoirTests(unittest.TestCase):
    """OWASP Noir's JSON (`noir scan -f json`) as candidates: a recorded report with invented names and the tool's
    shape, its paths absolute under the root it scanned."""

    REPORT = {"endpoints": [
        {"url": "/healthz", "method": "GET", "protocol": "http",
         "handler": {"name": "GET", "path": "/work/app/api/healthz/route.ts", "line": 3},
         "details": {"code_paths": [{"path": "/work/app/api/healthz/route.ts", "line": 3}], "technology": "js_nextjs"},
         "params": []},
        {"url": "/orders/:id", "method": "POST", "protocol": "http",
         "details": {"code_paths": [{"path": "/work/server/routes.js", "line": 12}], "technology": "js_express"},
         "params": [{"name": "id", "value": "", "param_type": "path", "tags": []}]},
        {"url": "cli://deploy", "method": "CLI", "protocol": "cli",
         "details": {"code_paths": [{"path": "/work/bin/tool.py", "line": 8}], "technology": "py_click"}, "params": []},
        {"url": "https://shop.example/cart", "method": "GET", "protocol": "universal-link",
         "details": {"code_paths": [{"path": "/work/ios/Shop.entitlements", "line": 6}], "technology": "ios"},
         "params": []},
        {"url": "shop://open", "method": "GET", "protocol": "mobile-scheme",
         "details": {"code_paths": [{"path": "/work/android/AndroidManifest.xml", "line": 21}], "technology": "android"},
         "params": []},
        {"url": "/live", "method": "GET", "protocol": "ws",
         "details": {"code_paths": [{"path": "/work/server/live.js", "line": 4}], "technology": "js_express"},
         "params": []},
        {"url": "/spec", "method": "GET", "protocol": "http", "details": {"code_paths": [], "technology": "oas3"},
         "params": []}],
        "passive_results": [], "errors": []}

    def test_each_protocol_decides_the_kind_and_the_site_is_relative_to_the_scanned_root(self):
        self.assertEqual(entries.noir(self.REPORT, "/work"), [
            {"reader": "noir", "shape": "http", "site": "app/api/healthz/route.ts:3",
             "symbol": "app/api/healthz/route.ts::GET", "method": "GET", "path": "/healthz", "kind": "rotta",
             "handler": "GET"},
            {"reader": "noir", "shape": "http", "site": "server/routes.js:12", "symbol": "server/routes.js::<module>",
             "method": "POST", "path": "/orders/:id", "kind": "rotta"},                   # no handler: its code path
            {"reader": "noir", "shape": "cli", "site": "bin/tool.py:8", "symbol": "bin/tool.py::<module>",
             "method": "CLI", "path": "cli://deploy", "kind": "comando"},
            {"reader": "noir", "shape": "universal-link", "site": "ios/Shop.entitlements:6",
             "symbol": "ios/Shop.entitlements::<module>", "method": "GET", "path": "https://shop.example/cart",
             "kind": "evento del sistema operativo"},
            {"reader": "noir", "shape": "mobile-scheme", "site": "android/AndroidManifest.xml:21",
             "symbol": "android/AndroidManifest.xml::<module>", "method": "GET", "path": "shop://open",
             "kind": "evento del sistema operativo"},
            {"reader": "noir", "shape": "ws", "site": "server/live.js:4", "symbol": "server/live.js::<module>",
             "method": "GET", "path": "/live"}])                                           # a shape to classify

    def test_a_report_of_another_root_is_refused(self):
        with self.assertRaises(ValueError):
            entries.noir(self.REPORT, "/elsewhere")


class ClassifiedBindingsTests(unittest.TestCase):
    SOURCES = {
        "web/view.tsx": (
            "import { post } from './actions';\n"
            "export function Form() {\n"
            "  function paint() { return <span>OK</span>; }\n"
            "  function save() { post(); return 1; }\n"
            "  return <div><span id=\"verb\">Invia</span><span id=\"what\">ordine</span>\n"
            "    <button aria-labelledby=\"verb what\" aria-label=\"ignorato\"\n"
            "       onClick={save}>x</button><button onClick={save}>Ripeti</button>\n"
            "    <Widget onClick={save} render={paint} />\n"
            "    <button customEvent={save}>A</button><button customEvent={save}>B</button>\n"
            "  </div>;\n}\n"),
        "web/actions.ts": "export function post() {}\n",
    }

    @classmethod
    def setUpClass(cls):
        cls.work = Path(tempfile.mkdtemp(prefix="entries-classified-")).resolve()
        cls.manifest = snapshot_of(cls.work, cls.SOURCES)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.work, True)

    def test_two_buttons_on_one_line_keep_distinct_evidence_and_composed_accessible_names(self):
        links = flows.link_facts(self.manifest, [])
        buttons = [e for e in links["entries"] if e.get("shape") == "onClick"]
        self.assertEqual([e["label"] for e in buttons], ["Invia ordine", "Ripeti"])
        self.assertEqual({e["event"] for e in buttons}, {"click"})
        self.assertEqual(len({(e["site"], e["column"]) for e in buttons}), 2)
        self.assertEqual({e["symbol"] for e in buttons}, {"web/view.tsx::Form.save"})
        self.assertTrue(all(e["source"] == "registro" and e["handler_source"] for e in buttons))

    def test_known_shapes_are_not_asked_and_a_numbered_decision_applies_to_all_matching_sites(self):
        found = entries.cached_syntax(self.manifest)
        questions = entries.shape_questions(found)
        self.assertEqual([(q["count"], q["shape"]) for q in questions if q["reader"] == entries.ATTRIBUTE],
                         [(2, "customEvent")])
        row = next(q["row"] for q in questions if q["shape"] == "customEvent")
        with self.assertRaises(ValueError):
            entries.shape_rules(questions, {str(row): "forse"})
        excluded = entries.shape_rules(questions, {str(row): entries.NO_ENTRY})
        self.assertFalse(any(e.get("shape") == "customEvent" for e in flows.link_facts(self.manifest, excluded)["entries"]))
        rules = entries.shape_rules(questions, {str(row): entries.ENTRY_KINDS[0]})
        with self.assertRaisesRegex(ValueError, "source"):
            flows.validate_rules([{**rules[0], "source": "registro"}])
        links = flows.link_facts(self.manifest, flows.validate_rules(rules))
        self.assertEqual([e["label"] for e in links["entries"] if e.get("shape") == "customEvent"], ["A", "B"])
        self.assertNotIn("customEvent", {q["shape"] for q in entries.shape_questions(found, rules)})

    def test_an_ast_attribute_rule_uses_the_same_multiline_binding_and_excludes_render_and_forwarded_props(self):
        links = flows.link_facts(self.manifest, [{"attribute": "*", "link": "attiva"}])
        bindings = [e for e in links["edges"] if e["type"] == "attiva"]
        self.assertEqual({(e["to"], e["label"]) for e in bindings},
                         {("web/view.tsx::Form.save", x) for x in ("Invia ordine", "Ripeti", "A", "B")})


    def test_indexed_read_of_destructured_and_imported_handler_wins_at_its_own_column(self):
        import resolve_edges
        from snapshot_store import open_snapshot

        sources = {
            "actions.ts": "export function persist() {}\nexport function useSave(){ return { onPress: persist }; }\n",
            "view.tsx": ("import { useSave, persist as direct } from './actions';\nexport function View(){\n"
                         " const { onPress }=useSave();\n return <div><button onClick={onPress}>A</button>"
                         "<button onClick={direct}>B</button></div>;\n}\n"),
        }
        with tempfile.TemporaryDirectory() as folder:
            m = snapshot_of(Path(folder), sources)
            self.assertEqual([c["label"] for c in entries.cached_syntax(m) if c["reader"] == entries.ATTRIBUTE], ["B"])
            with open_snapshot(m) as store:
                target = store.connection.execute("SELECT id FROM sem_declarations WHERE file='actions.ts' AND name='persist'").fetchone()[0]
                binding = resolve_edges.store_binding(store, m, store.metadata.get("parser_fingerprint"),
                                                      {"typescript": {"engine": "scip-typescript", "state": "fresh"}}, {})
                edges = [{"reference_id": ref, "file": "view.tsx", "language": "typescript", "kind": "read",
                          "caller": caller, "l0": 4, "c0": col, "verdict": "project-callable", "target_id": target,
                          "symbol": "persist", "resolver": "scip-typescript", "confidence": "confirmed",
                          "payload": {"chain": ["same-range"]}}
                         for ref, caller, col in store.connection.execute(
                             "SELECT id, caller, c0 FROM sem_references WHERE file='view.tsx' AND l0=4 AND kind='read'")]
            resolve_edges.write_edge_store(resolve_edges.default_edge_store(m), edges, binding)
            got = [(e["label"], e["symbol"], e["handler_source"]) for e in flows.link_facts(m, [])["entries"]]
            self.assertEqual(got, [("A", "actions.ts::persist", "scip-typescript"), ("B", "actions.ts::persist", "scip-typescript")])


    def test_python_command_reaches_a_write_only_after_the_two_shapes_are_classified(self):
        sources = {"ui.py": ("import tkinter as tk\nfrom disk import store\nclass App:\n    def wire(self):\n"
                             "        tk.Button(text='Salva', command=self.save)\n"
                             "    def save(self):\n        store.put('orders')\n"),
                   "disk.py": "store = None\n"}
        with tempfile.TemporaryDirectory() as folder:
            manifest = snapshot_of(Path(folder), sources)
            candidates = entries.cached_syntax(manifest)
            [button] = [c for c in candidates if c["shape"] == "tk.Button#command"]
            self.assertEqual((button["event"], button["label"], button["symbol"]), ("command", "Salva", "ui.py::App.save"))
            self.assertEqual(flows.link_facts(manifest, [])["entries"], [])
            questions = entries.shape_questions(candidates)
            q = next(q for q in questions if q["shape"] == button["shape"])
            rules = entries.shape_rules(questions, {q["row"]: entries.ENTRY_KINDS[0]})
            rules += [{"written": "store.put", "link": "scrive", "store": "disk", "key": "arg0"}]
            links = flows.cached_links(manifest, rules)
            [confirmed] = links["entries"]
            self.assertEqual((confirmed["event"], confirmed["label"], confirmed["source"]), ("command", "Salva", "modello"))
            flow = flows.trace(links, confirmed["symbol"], "from")
            self.assertIn(("scrive", "store:disk/orders"), [(e["type"], e["to"]) for e in flow["edges"]])


    def test_call_attribute_and_decorator_queries_share_the_file_tree(self):
        from unittest.mock import patch
        sources = {"ui.tsx": ("export function View(){ function save(){ log(); } "
                              "listen('go', save); return <button onClick={save}>Go</button>; }\n")}
        with tempfile.TemporaryDirectory() as folder:
            manifest = snapshot_of(Path(folder), sources)
            original = entries._treesitter.get_parser
            parsed = []

            class Counter:
                def __init__(self, parser):
                    self.parser = parser

                def parse(self, source):
                    parsed.append(source)
                    return self.parser.parse(source)

            def parser(grammar):
                loaded = original(grammar)
                return (Counter(loaded[0]), loaded[1]) if loaded else None

            with patch.object(entries._treesitter, "get_parser", side_effect=parser):
                first = entries.cached_syntax(manifest)
                self.assertEqual(entries.cached_syntax(manifest), first)
            self.assertEqual(parsed.count(sources["ui.tsx"].encode()), 1)


if __name__ == "__main__":
    unittest.main()
