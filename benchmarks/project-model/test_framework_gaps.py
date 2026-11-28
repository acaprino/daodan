"""Quanti progetti del corpus usano le lacune aperte dei framework (T1.C.14).

Regola scritta prima della corsa (decisione del proprietario, 28 novembre 2026): un caso usato da almeno `AT_LEAST`
progetti diventa un passo di codice in `T1.C` con la fonte ufficiale del framework; gli altri vanno in `docs/backlog.md`
con il conto. Il dato di ogni caso è quello ufficiale, mai un'espressione regolare:

- versione (`VERSIONS`): gli intervalli dichiarati nei `packages` della pre-mappa registrata
  (`results/daodan_premap_corpus.json`, Renovate sui manifesti), letti con il `semver` di npm (`intersects`) che il Node
  dell'immagine porta, su ogni fixture con il record, anche clonata; `results/daodan_stack.json` ha gli id, non le versioni;
- API (`API`): il nodo tree-sitter (le grammatiche di `tree-sitter-language-pack`, come le carica Daodan) nei file che
  l'inventario di Daodan elenca (`file_inventory.write`), solo per le fixture con i file nel repository;
- `pages/` di Next.js: la regola di Next.js stesso (`findDir` di `packages/next/src/lib/find-pages-dir.ts`: `<dir>/pages`,
  poi `<dir>/src/pages`) sui percorsi dell'inventario, accanto a ogni `package.json` che dichiara `next`.

Una fixture clonata (`source.json`) per un caso di API o di percorso è «non misurata», con il motivo per cui potrebbe usarlo
(il pacchetto dichiarato, l'id dello stack); per un caso di versione lo è una fixture senza pre-mappa registrata.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path, PurePosixPath

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "daodan" / "core"))

import file_inventory  # noqa: E402
import premap  # noqa: E402
import score  # noqa: E402
from languages import _treesitter  # noqa: E402
from snapshot_store import open_snapshot  # noqa: E402

FIXTURES, RESULTS = HERE / "fixtures", HERE / "results"
AT_LEAST = 3  # la regola scritta prima della corsa

# caso -> (pacchetto npm, intervallo del caso): lo usa un progetto con un intervallo dichiarato che lo interseca
VERSIONS = {
    "Next.js senza `typegen`": ("next", "<15.5.0"),  # `next typegen` c'è da Next.js 15.5 (nextjs.org/blog/next-15-5)
    "SvelteKit 1": ("@sveltejs/kit", "<2.0.0"),
    "Nuxt 2": ("nuxt", "<3.0.0"),
    "Astro, `astro:routes:resolved`": ("astro", "*"),  # ogni progetto Astro: le sue pagine non sono lette
}
NEXT_PAGES = "Next.js `pages/`"
PAGES = ("pages", "src/pages")  # `findDir` di Next.js, nell'ordine in cui li cerca

JS = ("javascript", "typescript", "tsx")
# caso -> `declares`: pacchetti dichiarati (o `ids` dello stack) che fanno di una clonata un candidato non misurato;
# `imports`: un file conta solo se importa uno di questi (la cattura `@pkg`, se c'è, è il nome locale dell'import);
# `stem`: il nome del file senza estensione; `query`: il nodo dell'API per grammatica, nessuna = l'import è l'uso.
API = {
    "React Router `createBrowserRouter`": {
        "declares": ("react-router", "react-router-dom"), "imports": ("react-router", "react-router-dom"),
        "query": {g: ['(call_expression function: (identifier) @api (#eq? @api "createBrowserRouter"))'] for g in JS}},
    "React Router `basename`": {
        "declares": ("react-router", "react-router-dom", "@react-router/dev"),
        "imports": ("react-router", "react-router-dom", "@react-router/dev"),
        "query": {g: [*(['(jsx_attribute (property_identifier) @api (#eq? @api "basename"))'] if g != "typescript" else []),
                      '(pair key: (property_identifier) @api (#eq? @api "basename"))',
                      '((shorthand_property_identifier) @api (#eq? @api "basename"))'] for g in JS}},  # .ts: niente JSX
    "SvelteKit `actions`": {  # le azioni dei moduli stanno in `+page.server.(js|ts)`, che importa i tipi da `./$types`
        "declares": ("@sveltejs/kit",), "stem": "+page.server",
        "query": {g: ['(export_statement declaration: (lexical_declaration (variable_declarator name: (identifier) @api'
                      ' (#eq? @api "actions"))))',
                      '(export_statement (export_clause (export_specifier name: (identifier) @api (#eq? @api "actions"))))']
                  for g in ("javascript", "typescript")}},
    "Angular `@HostListener` e `host`": {
        "declares": ("@angular/core",), "imports": ("@angular/core",),
        "query": {"typescript": ['(decorator (call_expression function: (identifier) @api (#eq? @api "HostListener")))',
                                 '(decorator (call_expression function: (identifier) @kind arguments: (arguments (object'
                                 ' (pair key: (property_identifier) @api)))) (#any-of? @kind "Component" "Directive")'
                                 ' (#eq? @api "host"))']}},
    "Go senza framework (`net/http`)": {  # le funzioni con cui `net/http` registra un gestore o crea un multiplexer
        "ids": ("golang",), "imports": ("net/http",),
        "query": {"go": ['(call_expression function: (selector_expression operand: (identifier) @pkg'
                         ' field: (field_identifier) @api) (#any-of? @api "Handle" "HandleFunc" "NewServeMux"))']}},
    "Wrapper HTTP: client fuori dalla tabella": {  # `daodan/data/http-clients.json` ha solo `fetch`
        "declares": ("axios", "requests", "httpx"), "imports": ("axios", "requests", "httpx"), "query": None},
}
# dove un file importa un modulo: `@source` è lo specificatore (JS), il primo nome del modulo (Python), il percorso (Go)
IMPORTS = {
    "javascript": ['(import_statement source: (string (string_fragment) @source))',
                   '(call_expression function: (identifier) @require arguments: (arguments . (string (string_fragment)'
                   ' @source)) (#eq? @require "require"))'],
    "python": ['(import_statement name: (dotted_name . (identifier) @source))',
               '(import_statement name: (aliased_import name: (dotted_name . (identifier) @source)))',
               '(import_from_statement module_name: (dotted_name . (identifier) @source))'],
    "go": ['(import_spec path: (interpreted_string_literal (interpreted_string_literal_content) @source)) @spec'],
}
IMPORTS["typescript"] = IMPORTS["tsx"] = IMPORTS["javascript"]
GRAMMARS = {"javascript": "javascript", "typescript": "typescript", "python": "python", "go": "go"}  # lingua -> grammatica

# Il `semver` di npm (quello che npm stesso usa), accanto al Node che lo esegue
SEMVER = r"""
const path = require("path");
const where = path.join(path.dirname(process.execPath), "..", "lib", "node_modules", "npm", "node_modules", "semver");
const semver = require(where);
const pairs = JSON.parse(require("fs").readFileSync(0, "utf8"));
const answer = ([declared, wanted]) => {
  try { return semver.validRange(declared) === null ? null : semver.intersects(declared, wanted); } catch { return null; }
};
console.log(JSON.stringify({version: require(path.join(where, "package.json")).version, answers: pairs.map(answer)}));
"""

MEASURED = {  # progetti che usano il caso, misurati il 28 novembre 2026 (README, «Le lacune dei framework sul corpus»)
    "Next.js senza `typegen`": 2, "SvelteKit 1": 0, "Nuxt 2": 0, "Astro, `astro:routes:resolved`": 1,
    NEXT_PAGES: 0, "React Router `createBrowserRouter`": 0, "React Router `basename`": 0, "SvelteKit `actions`": 0,
    "Angular `@HostListener` e `host`": 0, "Go senza framework (`net/http`)": 0, "Wrapper HTTP: client fuori dalla tabella": 8,
}
STEPS = {"Wrapper HTTP: client fuori dalla tabella": "T1.C.15"}  # i casi che la regola fa diventare passi di codice


def intersects(pairs: list[tuple[str, str]]) -> tuple[str, list[bool | None]]:
    """La versione del `semver` di npm e, per ogni (intervallo dichiarato, intervallo del caso), se si intersecano;
    None per un intervallo che `semver` non legge (`workspace:*`, `catalog:`, un tag)."""
    done = subprocess.run(["node", "-e", SEMVER], input=json.dumps(pairs), capture_output=True, text=True,
                          timeout=120, check=True)
    read = json.loads(done.stdout)
    return read["version"], read["answers"]


def _text(source: bytes, node) -> str:
    return source[node.start_byte:node.end_byte].decode("utf-8", errors="replace")


def _matches(grammar: str, lines: list[str], root) -> list[dict]:
    from tree_sitter import QueryCursor

    query = _treesitter.get_query(grammar, "\n".join(lines))
    assert query is not None, f"la query di {grammar} non compila: {lines}"
    return [captures for _, captures in QueryCursor(query).matches(root)]


def _package(grammar: str, source: str) -> str:
    """Il pacchetto di uno specificatore npm (`@scope/nome/...` o `nome/...`: testo senza grammatica); in Python e Go la
    cattura è già il modulo."""
    if grammar not in JS:
        return source
    parts = source.split("/")
    return "/".join(parts[:2]) if source.startswith("@") else parts[0]


def _imports(grammar: str, root, source: bytes) -> dict[str, set[str]]:
    """I pacchetti che il file importa, ciascuno con i nomi locali (Go: l'alias, altrimenti l'ultimo elemento del
    percorso, che per `net/http` è il nome del pacchetto, `http`)."""
    found: dict[str, set[str]] = {}
    for match in _matches(grammar, IMPORTS[grammar], root):
        written = _text(source, match["source"][0])
        names = found.setdefault(_package(grammar, written), set())
        if grammar == "go":
            alias = match["spec"][0].child_by_field_name("name")
            names.add(_text(source, alias) if alias is not None else written.rpartition("/")[2])
    return found


def uses(case: dict, path: str, grammar: str, source: bytes) -> list[str] | None:
    """I pacchetti del caso che il file importa (vuoto per un caso senza `imports`) se il file usa il caso, altrimenti None."""
    lines = (case["query"] or {}).get(grammar) if case["query"] is not None else ()
    if lines is None or (case["query"] is None and grammar not in IMPORTS):
        return None
    if case.get("stem") and PurePosixPath(path).stem != case["stem"]:
        return None
    loaded = _treesitter.get_parser(grammar)
    assert loaded is not None, f"nessuna grammatica {grammar}: {_treesitter.load_failure(grammar)}"
    root = loaded[0].parse(source).root_node
    imported = _imports(grammar, root, source) if case.get("imports") else {}
    wanted = {p: imported[p] for p in case.get("imports") or () if p in imported}
    if case.get("imports") and not wanted:
        return None
    if lines and not any("pkg" not in m or _text(source, m["pkg"][0]) in set().union(*wanted.values())
                         for m in _matches(grammar, lines, root)):
        return None
    return sorted(wanted)


def next_pages(files: list[str], folders: set[str]) -> list[str]:
    """Le cartelle `pages` che Next.js trova (`findDir`) accanto a un `package.json` che dichiara `next`."""
    return sorted({str(PurePosixPath(f, d)) for f in folders for d in PAGES
                   if any(PurePosixPath(f, d) in PurePosixPath(rel).parents for rel in files)})


def _declared(record: dict) -> list[dict]:
    return [{"name": p["name"], "version": p.get("version"), "file": p["declared_in"].partition("#")[0]}
            for p in (record.get("output") or {}).get("packages") or ()]


def _committed(name: str, out: Path) -> tuple[list[str], dict[str, tuple[str, bytes]]]:
    """I file della fixture che l'inventario di Daodan elenca e non esclude, relativi alla fixture, e quelli che una
    grammatica dei casi legge, col loro testo."""
    manifest = out / name / "inventory.sqlite"
    manifest.parent.mkdir(parents=True)
    file_inventory.write(FIXTURES / name, manifest)
    with open_snapshot(manifest) as store:
        inventory = premap.Context(manifest, store).inventory
        left_out = {row["path"] for row in store.get("excluded") or ()}
        files, read = [], {}
        for rel in inventory.files:
            if rel in left_out:
                continue
            own = (inventory.root / rel).relative_to(FIXTURES / name).as_posix()
            files.append(own)
            grammar = GRAMMARS.get(inventory.headers[rel].get("language"))
            if grammar:
                grammar = "tsx" if grammar == "typescript" and own.endswith(".tsx") else grammar
                read[own] = (grammar, inventory.text(rel).encode("utf-8"))
    return files, read


def measure(out: Path) -> dict:
    """Per caso: i progetti che lo usano (col dettaglio), quelli non misurati (col motivo), le dichiarazioni non lette."""
    stack = json.loads((RESULTS / "daodan_stack.json").read_text(encoding="utf-8"))["fixtures"]
    recorded = json.loads((RESULTS / "daodan_premap_corpus.json").read_text(encoding="utf-8"))
    names = score._fixtures("all")
    declared = {n: _declared(recorded[n]) for n in names if "output" in (recorded.get(n) or {})}
    cloned = {n for n in names if (FIXTURES / n / "source.json").is_file()}
    found = {case: {"uses": {}, "not_measured": {}, "unread": []} for case in [*VERSIONS, NEXT_PAGES, *API]}

    pairs = [(d["version"], wanted) for package, wanted in VERSIONS.values() for rows in declared.values()
             for d in rows if d["name"] == package and d["version"]]
    version, answers = intersects(pairs)
    answer = dict(zip(pairs, answers))
    for case, (package, wanted) in VERSIONS.items():
        row = found[case]
        row["semver"] = version
        row["not_measured"] = {n: "nessuna pre-mappa registrata" for n in names if n not in declared}
        for name, rows in declared.items():
            for d in rows:
                if d["name"] != package or not d["version"]:
                    continue
                if answer[(d["version"], wanted)] is None:
                    row["unread"].append(f"{name}: {d['file']} {d['version']}")
                elif answer[(d["version"], wanted)]:
                    row["uses"].setdefault(name, []).append(f"{d['file']} {d['version']}")

    for name in sorted(names):
        rows = declared.get(name, [])
        if name in cloned:
            for case, spec in [(NEXT_PAGES, {"declares": ("next",)}), *API.items()]:
                why = sorted({d["name"] for d in rows if d["name"] in spec.get("declares", ())}
                             | set(spec.get("ids", ())).intersection(stack.get(name, {}).get("ids") or ()))
                if why:
                    found[case]["not_measured"][name] = ", ".join(why)
            continue
        files, read = _committed(name, out)
        folders = {str(PurePosixPath(d["file"]).parent) for d in rows
                   if d["name"] == "next" and PurePosixPath(d["file"]).name == "package.json"}
        if pages := next_pages(files, folders):
            found[NEXT_PAGES]["uses"][name] = pages
        for case, spec in API.items():
            hits = {path: got for path, (grammar, source) in sorted(read.items())
                    if (got := uses(spec, path, grammar, source)) is not None}
            if hits:
                found[case]["uses"][name] = hits
    return found


def test_each_case_reads_its_official_datum_on_a_written_example():
    """Un caso a 0 non è una query rotta: ogni API si legge su un esempio scritto, e ciò che le somiglia no."""
    cases = {
        "React Router `createBrowserRouter`": [
            ("src/main.tsx", "tsx", 'import { createBrowserRouter } from "react-router-dom";\n'
                                    'const router = createBrowserRouter([{ path: "/", element: <Home /> }]);\n',
             ["react-router-dom"])],
        "React Router `basename`": [
            ("src/App.tsx", "tsx", 'import { BrowserRouter } from "react-router";\n'
                                   'export const App = () => <BrowserRouter basename="/app" />;\n', ["react-router"]),
            ("react-router.config.ts", "typescript", 'import type { Config } from "@react-router/dev/config";\n'
                                                     'export default { basename: "/base/" } satisfies Config;\n',
             ["@react-router/dev"]),
            ("src/util.ts", "typescript", 'import path from "node:path";\nconst p = { basename: path.basename(x) };\n',
             None)],
        "SvelteKit `actions`": [
            ("src/routes/+page.server.ts", "typescript",
             'import type { Actions } from "./$types";\nexport const actions = { default: async () => {} } satisfies Actions;\n',
             []),
            ("src/routes/+page.ts", "typescript", "export const actions = {};\n", None)],
        "Angular `@HostListener` e `host`": [
            ("a.ts", "typescript", 'import { Directive, HostListener } from "@angular/core";\n@Directive({ selector: "[x]" })\n'
                                   'export class X {\n  @HostListener("click") on() {}\n}\n', ["@angular/core"]),
            ("b.ts", "typescript", 'import { Component } from "@angular/core";\n'
                                   '@Component({ selector: "b", host: { "(click)": "on()" } })\nexport class B {}\n',
             ["@angular/core"]),
            ("c.ts", "typescript", 'import { Component, Input } from "@angular/core";\n'
                                   '@Component({ selector: "c" })\nexport class C {\n  @Input() label = "";\n}\n', None)],
        "Go senza framework (`net/http`)": [
            ("main.go", "go", 'package main\n\nimport "net/http"\n\nfunc main() { http.HandleFunc("/", h) }\n', ["net/http"]),
            ("alias.go", "go", 'package main\n\nimport web "net/http"\n\nfunc main() { mux := web.NewServeMux(); _ = mux }\n',
             ["net/http"]),
            ("chi.go", "go", 'package main\n\nimport (\n\t"net/http"\n\n\t"github.com/go-chi/chi/v5"\n)\n\n'
                             'func main() { r := chi.NewRouter(); r.HandleFunc("/", h); http.ListenAndServe(":80", r) }\n',
             None)],
        "Wrapper HTTP: client fuori dalla tabella": [
            ("a.js", "javascript", 'import axios from "axios";\n', ["axios"]),
            ("b.js", "javascript", 'const axios = require("axios");\n', ["axios"]),
            ("c.py", "python", "import requests\nrequests.get(url)\n", ["requests"]),
            ("d.py", "python", "from httpx import AsyncClient\n", ["httpx"]),
            ("e.py", "python", "import urllib.request\n", None)],
    }
    assert set(cases) == set(API)
    for case, examples in cases.items():
        for path, grammar, text, expected in examples:
            assert uses(API[case], path, grammar, text.encode()) == expected, (case, path)
    assert next_pages(["web/pages/index.tsx", "web/app/page.tsx"], {"web"}) == ["web/pages"]
    assert next_pages(["src/pages/index.tsx"], {"."}) == ["src/pages"]
    assert next_pages(["app/page.tsx", "lib/pages/x.ts"], {"."}) == []
    assert intersects([("14.2.15", "<15.5.0"), ("^16.3.3", "<15.5.0"), ("workspace:*", "<15.5.0")])[1] == [True, False, None]


def test_how_many_projects_use_each_case_and_which_become_steps(tmp_path):
    found = measure(tmp_path)
    print(json.dumps(found, indent=1, ensure_ascii=False))
    counts = {case: len(row["uses"]) for case, row in found.items()}
    print(json.dumps(counts, indent=1, ensure_ascii=False))
    assert counts == MEASURED
    assert {case for case, n in counts.items() if n >= AT_LEAST} == set(STEPS)
