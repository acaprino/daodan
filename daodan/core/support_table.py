#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# ///
"""Write the document of what Daodan supports, per kind, from the product's own declarations and the committed
benchmark results. A development tool: it reads repository files only, with no network and nothing run.

    python support_table.py build [--out FILE]
    python support_table.py check [FILE]

Each measure names its result file and date; a kind or a row with no measure says `non misurato`.
"""
from __future__ import annotations

import argparse
import collections
import importlib
import json
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import build_units  # noqa: E402
import dynamic  # noqa: E402
import engine_pass  # noqa: E402
import flows  # noqa: E402
import languages  # noqa: E402
import module_derive  # noqa: E402
import premap  # noqa: E402
import preparation  # noqa: E402
import registry_build  # noqa: E402
import service_registry  # noqa: E402
from indexers import components, css, css_tailwind  # noqa: E402
from languages import sfc  # noqa: E402
from premap import suffix_table  # noqa: E402

ROOT = SCRIPT_DIR.parents[1]
DOC = ROOT / "docs/plugins/codebase-map-supporto.md"
RESULTS = ROOT / "benchmarks/project-model/results"
RUN = "2026-11-16-finale"  # the last pipeline run over the whole corpus; the later ones have a few cases each
STACK = ("daodan_stack.json", "19 novembre 2026", "c6be10745cedb94d")  # file, date, the code its records name
REGISTER = ROOT / "docs/verification/2026-11-16-registro-difetti.md"
CENSUS = ROOT / "docs/research/2026-11-14-punti-di-connessione.md"
ENGINES_PACKAGE = SCRIPT_DIR / "indexers/css_engines/package.json"
FAMILIES = ("js", "py", "jvm", "sys", "mix", "real", "stack")
MONTHS = ("gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre",
          "novembre", "dicembre")
RANKS = {"model": "modello: il comando del build tool, nel container", "reader": "lettore: legge i file",
         "scanner": "scanner: legge ogni file"}
# An ecosystem of the registry's package signs and the languages, by the snapshot's names, of the code that declares
# its packages; an image or a CI action is no code.
PACKAGE_LANGUAGES = {"npm": ("javascript", "typescript"), "deno": ("javascript", "typescript"), "pypi": ("python",),
                     "crates": ("rust",), "go": ("go",), "maven": ("java", "kotlin"), "nuget": ("csharp",),
                     "composer": ("php",), "rubygems": ("ruby",), "hex": ("elixir",), "pub": ("dart",),
                     "terraform": ("hcl",), "terraform-resource": ("hcl",), "docker": (), "github-actions": ()}
# A registry entry Daodan reads beyond its language, and what its readers key that reading on: a file suffix or the
# package `indexers/css_tailwind.py` asks for. `own_reading` says the reading from the readers' own constants.
OWN_READINGS = {"vue": ".vue", "sveltejs": ".svelte", "astro": ".astro", "tailwind": css_tailwind.PACKAGE}


def _rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def _json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _n(value: int) -> str:
    return f"{value:,}".replace(",", ".")


def _of(count: int, one: str, many: str) -> str:
    return f"{_n(count)} {one if count == 1 else many}"


def _ratio(part: int, whole: int, none: str = "non misurato") -> str:
    if not whole:
        return none
    return f"{_n(part)} / {_n(whole)} ({f'{100 * part / whole:.1f}'.replace('.', ',')} %)"


def _date(stem: str) -> str:
    year, month, day = stem[:10].split("-")
    return f"{int(day)} {MONTHS[int(month) - 1]} {year}"


def _table(head: list[str], rows: list[list[str]]) -> list[str]:
    out = ["| " + " | ".join(head) + " |", "| " + " | ".join("---" for _ in head) + " |"]
    return out + ["| " + " | ".join(str(cell).replace("|", "\\|") for cell in row) + " |" for row in rows]


def _codes(values) -> str:
    return " ".join(f"`{value}`" for value in values) or "—"


def _cards() -> dict[str, collections.Counter]:
    """Per language tag of the register, its cards by state: `aperto`, `buco dichiarato`, `risolto`."""
    by_language: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    for card in re.split(r"^#### D-\d+", REGISTER.read_text(encoding="utf-8"), flags=re.M)[1:]:
        tag = re.search(r"^- \*\*Tag:\*\* lingua (.+?) ·", card, re.M)
        state = re.search(r"^- \*\*Stato:\*\* (.+)$", card, re.M)
        if not tag or not state:
            continue
        text = state.group(1)
        kind = next((k for k in ("aperto", "buco dichiarato", "risolto") if text.startswith(k)), "altro")
        for language in tag.group(1).split(","):
            by_language[language.strip()][kind] += 1
    return by_language


def _analyzer_reads() -> dict[str, list[str]]:
    """Per snapshot language, the analyzers whose module reads its files (`SNAPSHOT_LANGUAGES`, else `LANGUAGES`)."""
    reads: dict[str, list[str]] = collections.defaultdict(list)
    for spec in engine_pass.ENGINES:
        module = importlib.import_module(f"indexers.{spec.indexer}")
        for language in getattr(module, "SNAPSHOT_LANGUAGES", spec.languages):
            reads[language].append(spec.name)
    return reads


def languages_section(cards, run_path: Path) -> list[str]:
    reads, observers = _analyzer_reads(), dynamic.observers()
    by_language = collections.defaultdict(list)
    for suffix, language in languages.SUPPORTED_EXTENSIONS.items():
        by_language[language].append(suffix)
    rows = []
    for language in languages.SUPPORTED_LANGUAGES:
        count = cards.get(language, collections.Counter())
        rows.append([suffix_table.NAMES.get(language, language.capitalize()), _codes(by_language[language]),
                     ", ".join(reads.get(language, [])) or "nessuno",
                     ", ".join(o.ENTRY for o in observers if language in o.LANGUAGES) or "nessuno",
                     f"{count['aperto']} / {count['buco dichiarato']} / {count['risolto']}"])
    others = sorted((k, sum(v.values())) for k, v in cards.items()
                    if k not in languages.SUPPORTED_LANGUAGES and k != "tutti")
    out = ["## Linguaggi", "",
           f"{len(languages.SUPPORTED_LANGUAGES)} linguaggi letti dallo snapshot con "
           f"{len(languages.SUPPORTED_EXTENSIONS)} estensioni (`daodan/core/languages/__init__.py`), "
           f"{len(engine_pass.ENGINES)} analizzatori (`daodan/core/indexers/`) e {len(observers)} osservatori del "
           "passo dinamico (`daodan/core/dynamic/`). Schede: aperte / buchi dichiarati / risolte del registro dei difetti "
           f"([{REGISTER.name}](../verification/{REGISTER.name})) con quel linguaggio fra i tag.", "",
           *_table(["Linguaggio", "Estensioni", "Analizzatore", "Osservatore", "Schede"], rows), ""]
    if others:
        out += ["Linguaggi che il registro nomina e lo snapshot non legge: "
                + ", ".join(f"{k} ({_of(v, 'scheda', 'schede')})" for k, v in others) + ".", ""]
    return out


def analyzers_section(report: dict, raw: dict, run_path: Path) -> list[str]:
    observed = collections.defaultdict(lambda: [0, 0, 0, set()])  # observed cases, cases, sites, states
    for case in raw.values():
        for language, item in ((case.get("steps") or {}).get("dynamic") or {}).get("languages", {}).items():
            entry = observed[language]
            entry[1] += 1
            entry[3].add(item.get("state"))
            if item.get("state") == "observed":
                entry[0] += 1
                entry[2] += item.get("sites") or 0
    rows = []
    for language, item in sorted(report["languages"].items()):
        spec = engine_pass.ENGINE_LANGUAGES.get(language)
        seen = observed.get(language)
        if not seen:
            dyn = "non misurato"
        elif seen[3] == {"no-observer"}:
            dyn = "nessun osservatore nel giro"
        else:
            dyn = f"{seen[0]} / {_of(seen[1], 'caso', 'casi')}, {_of(seen[2], 'sito', 'siti')}"
        rows.append([language, spec.name if spec else "—",
                     _ratio(item["states"].get("fresh", 0), item["cases"]),
                     _ratio(sum(item["answered"].values()), item["sites"]),
                     _ratio(item["files"]["indexed"], item["files"]["snapshot"]), dyn])
    missing = [f"{k} ({_of(v['cases'], 'caso', 'casi')}, {_n(v['files'])} file)" for k, v in sorted(report.get("no_analyzer", {}).items())]
    measured = set(report["languages"])
    unmeasured = sorted({lang for spec in engine_pass.ENGINES for lang in spec.languages} - measured)
    out = ["## Analizzatori e passo dinamico, misurati", "",
           f"Giro della pipeline del {_date(run_path.name)} su {report['cases']['run']} casi "
           f"(`{_rel(run_path.with_suffix('.report.json'))}`; il passo dinamico da `{_rel(run_path)}`). "
           "Il linguaggio è quello del giro: `stylesheet` è il grafo dei fogli di stile, su CSS, markup, Vue e "
           "Svelte. Il registro dei difetti e il README del benchmark dicono che cosa è cambiato dopo il giro.", "",
           *_table(["Linguaggio", "Analizzatore", "Esito", "Copertura delle chiamate", "File nell'indice",
                    "Passo dinamico: casi osservati, siti"], rows), ""]
    if missing:
        out += ["Nel giro senza analizzatore: " + ", ".join(missing) + ".", ""]
    if unmeasured:
        out += ["Analizzatori senza un caso nel giro, non misurati: " + ", ".join(unmeasured) + ".", ""]
    return out


def build_section(report: dict, raw: dict, run_path: Path) -> list[str]:
    states = collections.defaultdict(collections.Counter)
    for case in raw.values():
        for source in case.get("sources") or ():
            states[source["source"].split("@")[0]][source["state"]] += 1
    rows = []
    for source in premap.SOURCES:
        count = states.get(source.NAME)
        cell = ("non misurato: non era nel giro" if not count else
                ", ".join(f"{state} {n}" for state, n in sorted(count.items())))
        rows.append([f"`{source.NAME}`", source.VERSION, RANKS[source.RANK],
                     f"`premap/{source.__name__.rsplit('.', 1)[-1]}.py`", cell])
    facets = [[f"`{face}`", _ratio(item["found"], item["expected"]), _n(item["extra"]), _n(item["wrong"])]
              for face, item in report["premap"].items() if item["given"] and item["expected"]]
    manifests = collections.defaultdict(list)
    for name, (ecosystem, _) in build_units.READERS.items():
        manifests[ecosystem].append(name)
    for suffix, (ecosystem, _) in build_units.SUFFIX_READERS.items():
        manifests[ecosystem].append(f"*{suffix}")
    tools = sorted({t for v in module_derive.ECOSYSTEM_TOOLS.values() for t in v}
                   | set(module_derive.LANGUAGE_TOOLS.values())
                   | {t for v in module_derive.INHERITED_TOOLS.values() for t in v})
    return ["## Build tool e toolchain", "",
            f"La pre-mappa ha {len(premap.SOURCES)} fonti (`daodan/core/premap/`, `SOURCES`); il grafo dei moduli legge "
            f"{sum(len(v) for v in manifests.values())} manifest di {len(manifests)} ecosistemi "
            f"(`daodan/core/build_units.py`); un modulo riceve {len(tools)} toolchain dal suo ecosistema o linguaggio "
            f"(`daodan/core/module_derive.py`); la preparazione porta {len(preparation.NEEDS)} toolchain nel container "
            "(`daodan/core/preparation.py`, `NEEDS`).", "",
            "### Fonti della pre-mappa", "",
            f"Stati di ogni fonte nei casi del giro del {_date(run_path.name)} (`{_rel(run_path)}`): `ran` ha girato, "
            "`not_needed` il caso non aveva i suoi file.", "",
            *_table(["Fonte", "Versione", "Modo", "Modulo", "Casi per stato"], rows), "",
            f"### Pre-mappa per faccia", "",
            f"Dallo stesso giro (`{_rel(run_path.with_suffix('.report.json'))}`, `premap`): ogni faccia contro "
            "`expected.json` dei casi che la danno.", "",
            *_table(["Faccia", "Riconoscimento", "In più", "Sbagliati"], facets), "",
            "### Manifest di build", "",
            "Riconoscimento per ecosistema: non misurato (il giro misura le unità tutte insieme, faccia `units`).", "",
            *_table(["Ecosistema", "Manifest"], [[k, _codes(sorted(v))] for k, v in sorted(manifests.items())]), "",
            "### Toolchain", "",
            "Riconosciute: " + _codes(tools) + ".", "",
            *_table(["Toolchain della preparazione", "Versione"],
                    [[k, v.get("version") or "—"] for k, v in sorted(preparation.NEEDS.items())]), ""]


def _signs(entry: dict) -> str:
    signs = entry.get("signs") or {}
    parts = sorted({*(signs.get("packages") or {}), *(signs.get("patterns") or {})})
    parts += [k for k in ("files", "env", "hosts") if signs.get(k)]
    return ", ".join(parts)


def own_reading(key: str) -> str:
    """What Daodan reads beyond the language of the files or the package `key`, from its readers' constants; empty
    when no reader takes it."""
    parts = []
    if key in components.SUFFIXES:
        parts.append("componenti nell'indice di scip-typescript (`indexers/components.py`)")
    language = languages.SUPPORTED_EXTENSIONS.get(key)
    adapter = languages.get_adapter(language) if language else None
    if isinstance(adapter, type(sfc.vue_adapter)):
        parts.append("frontmatter e `<script>` nello snapshot (`languages/sfc.py`), del template solo gli eventi (`premap/astro.py`)"
                     if adapter.frontmatter else "`<script>` e template nello snapshot (`languages/sfc.py`)")
    if key in css.COMPONENTS:
        parts.append("stili con il compilatore del framework "
                     f"(`indexers/{css.COMPONENTS[key].__name__.rsplit('.', 1)[-1]}.py`)")
    if key == css_tailwind.PACKAGE:
        parts.append("quali classi sono sue utility, dal Tailwind del progetto nel container "
                     "(`indexers/css_tailwind.py`)")
    return "; ".join(parts)


def _analysed(entry: dict, reads: dict) -> str:
    """The languages of the entry's package ecosystems (`PACKAGE_LANGUAGES`) an analyzer reads, then those none reads."""
    signs = entry.get("signs") or {}
    names = dict.fromkeys(language for ecosystem in sorted({*(signs.get("packages") or {}), *(signs.get("patterns") or {})})
                          for language in PACKAGE_LANGUAGES[ecosystem])
    return ", ".join([suffix_table.NAMES.get(name, name) for name in names if reads.get(name)]
                     + [f"{name}: nessun analizzatore" for name in names if not reads.get(name)]) or "—"


def stack_section(registry: dict, stack: dict) -> list[str]:
    entries = registry["entries"]
    known = [e for e in entries if e.get("signs")]
    classes = collections.Counter(service_registry.entry_category(e) for e in known)
    written = collections.Counter(e["category"] for e in entries if e.get("category"))
    found_in = collections.Counter(i for record in stack["fixtures"].values() for i in record.get("ids") or ())
    scored = {name: r["score"] for name, r in stack["fixtures"].items() if r.get("score")}
    projects = [e for e in known if e["kind"] == "project"]
    defaulted = [e for e in projects if not e.get("category")]
    face_rows = []
    for family in (*FAMILIES, None):
        names = [n for n in scored if family is None or ("stack" if n.startswith("real-stack-") else n.split("-")[0])
                 == family]
        total = collections.Counter()
        for name in names:
            for face in ("frameworks_by_name", "frameworks", "services"):
                item = scored[name].get(face) or {}
                if item.get("given"):
                    total[face, "found"] += item["found"]
                    total[face, "expected"] += item["expected"]
                    total[face, "wrong"] += len(item.get("wrong") or ())
                    total[face, "extra"] += len(item.get("extra") or ())
        face_rows.append([family or "tutte", len(names),
                          _ratio(total["frameworks_by_name", "found"], total["frameworks_by_name", "expected"]),
                          f"{_ratio(total['frameworks', 'found'], total['frameworks', 'expected'])}, "
                          + _of(total['frameworks', 'wrong'], 'sbagliato', 'sbagliati'),
                          f"{_ratio(total['services', 'found'], total['services', 'expected'], 'nessuno atteso')}, "
                          f"{_n(total['services', 'extra'])} in più"])
    listed = sorted((e for e in known if service_registry.entry_category(e) != "service"),
                    key=lambda e: (service_registry.entry_category(e), e["name"].casefold()))
    file, date, _ = STACK
    reads, by_id = _analyzer_reads(), {e["id"]: e for e in entries}
    readings = {ident: own_reading(key) for ident, key in OWN_READINGS.items()}
    read_names = [by_id[ident]["name"] for ident in OWN_READINGS if ident in by_id]
    default = (f"Delle {_n(len(projects))} voci `project` riconoscibili, {_of(len(defaulted), 'è', 'sono')} "
               "`framework` solo per il default, senza una `category` scritta: per distinguerle serve una `category` "
               "(`framework`, `library` o `tool`) su ognuna." if defaulted else
               f"Ognuna delle {_n(len(projects))} voci `project` riconoscibili ha la sua `category` scritta: nessuna "
               "è `framework` solo per il default.")
    return ["## Framework, librerie e strumenti", "",
            "Lo step `stack` (`daodan/core/technologies.py`) dà a ogni unità `frameworks`, `libraries`, `services` e "
            "`tools`. La classe di una voce del catalogo (`data/service-registry.json`) la decide "
            "`service_registry.entry_category`: la `category` della voce se c'è, altrimenti `service` per una voce "
            "`service` e `framework` per ogni altra. I `frameworks` di un'unità sono le voci `framework`; le "
            "`libraries` sono tutti i pacchetti che dichiara, nel catalogo o no, con l'id della voce che il catalogo "
            "ne ha. Sul grafo dell'app un modulo mostra come tessere le voci `framework` e `library` che un suo file "
            "dichiara; uno strumento non è una tessera, un servizio è un nodo esterno.", "",
            *_table(["Classe", "Voci riconoscibili (con segni)", "Voci con la categoria scritta, fra tutte"],
                    [[c, _n(classes.get(c, 0)), _n(written.get(c, 0))] for c in registry_build.CATEGORIES]), "",
            default, "",
            f"Riconoscimento dello stack sul corpus, giro del {date} (`{_rel(RESULTS / file)}`), "
            f"{len(scored)} fixture su {len(stack['fixtures'])} con record; per nome conta un nome una volta per "
            "fixture, per unità ogni unità che lo tiene.", "",
            *_table(["Famiglia", "Fixture", "Framework per nome", "Framework per unità", "Servizi"], face_rows), "",
            "Che cosa vuol dire «supportata» per una voce della tabella che segue, a livelli. Riconosciuta: un suo "
            "segno (un pacchetto, un'immagine, un file) è nel progetto; vale per ogni voce. Codice analizzato: il "
            "codice del progetto che la dichiara è letto dall'analizzatore del suo linguaggio; la colonna dà questi "
            "linguaggi fra quelli degli ecosistemi dei segni della voce, e dice quando un linguaggio non ha "
            "analizzatore. Lettura propria: ciò che Daodan legge del framework oltre al suo linguaggio, e vale solo "
            f"per {_of(len(read_names), 'voce', 'voci')} ({', '.join(read_names)}). Rotte e collegamenti fra le parti "
            "vengono dalle regole di collegamento che un modello scrive per ogni progetto e che `daodan/core/flows.py` "
            "applica a chiamate, decoratori e attributi, per qualunque framework. Le rotte lette dallo strumento "
            "del framework, nel container, sono quelle di Next.js (`next typegen`), React Router e Remix "
            "(`routes --json`), le rotte del server e le pagine di Nuxt (`nuxt prepare`, `loadNuxt`) e i moduli delle "
            "rotte di SvelteKit (`svelte-kit sync`). Gli eventi dei template li legge il compilatore del framework: "
            "con il metodo che chiamano per Angular (`parseTemplate`), con la riga e la colonna ma senza la funzione "
            "per Astro (`parse`: il gestore è una stringa di JavaScript). Non sono lette le pagine di Astro (`sync()` "
            "dell'API le elenca con l'hook `astro:routes:resolved` senza avviare l'app: misurato, non scritto) né le "
            "pagine di SvelteKit che sono solo un componente: per queste la rotta dal posto di un file è un buco "
            "dichiarato.", "",
            "<details><summary>Framework, librerie e strumenti riconoscibili: "
            f"{len(listed)} voci</summary>", "",
            *_table(["Voce", "Id", "Classe", "Segni", "Codice analizzato", "Lettura propria",
                     f"Fixture in cui lo step la trova ({date})"],
                    [[e["name"], f"`{e['id']}`", service_registry.entry_category(e), _signs(e), _analysed(e, reads),
                      readings.get(e["id"]) or "—", found_in.get(e["id"], 0)]
                     for e in listed]), "", "</details>", ""]


def services_section(registry: dict, stack: dict) -> list[str]:
    services = [e for e in registry["entries"]
                if e["kind"] == "service" or service_registry.entry_category(e) == "service"]
    projects = sum(1 for e in services if e["kind"] == "project")
    by_type = collections.defaultdict(lambda: [0, 0, 0])
    for e in services:
        row = by_type[e.get("type") or "—"]
        row[0] += 1
        row[1] += bool(e.get("signs"))
        row[2] += bool(e.get("mark") or e.get("mark_source"))
    signs = collections.Counter(k for e in services if e.get("signs") for k, v in e["signs"].items() if v)
    found_in = collections.Counter(i for record in stack["fixtures"].values() for i in record.get("ids") or ())
    listed = sorted((e for e in services if e.get("signs") and service_registry.entry_category(e) == "service"),
                    key=lambda e: e["name"].casefold())
    apart = collections.Counter(service_registry.entry_category(e) for e in services if e.get("signs")
                                and service_registry.entry_category(e) != "service")
    return ["## Servizi esterni", "",
            f"Le voci di servizio del catalogo: {_n(len(services))}, {_n(len(services) - projects)} di `kind` "
            f"`service` e {_n(projects)} di `kind` `project` con la `category` `service` (un software che gira "
            f"accanto al sistema e a cui il codice si connette); {_n(sum(r[1] for r in by_type.values()))} con "
            f"segni per riconoscerle, {_n(sum(r[2] for r in by_type.values()))} con un marchio: {_n(sum(1 for e in services if e.get("mark")))} con il file nel prodotto (`mark`), "
            f"{_n(sum(1 for e in services if e.get("mark_source")))} scaricato al primo uso dalla fonte ufficiale (`mark_source`). Segni per "
            "specie, sulle voci che ne hanno: " + ", ".join(f"`{k}` {_n(v)}" for k, v in sorted(signs.items())) + ". "
            + (f"Di quelle con segni, {_n(sum(apart.values()))} hanno un'altra categoria ("
               + ", ".join(f"`{c}` {_n(n)}" for c, n in sorted(apart.items())) + ") e stanno nella lista della "
               "sezione precedente. " if apart else "")
            + "Il riconoscimento misurato è la colonna Servizi della sezione precedente.", "",
            *_table(["Tipo", "Voci", "Con segni", "Con marchio"],
                    [[k, _n(a), _n(b), _n(c)] for k, (a, b, c) in sorted(by_type.items(), key=lambda x: -x[1][0])]),
            "", f"<details><summary>Servizi riconoscibili: {len(listed)} voci</summary>", "",
            *_table(["Servizio", "Id", "Tipo", "Segni", "Marchio", f"Fixture in cui lo step lo trova ({STACK[1]})"],
                    [[e["name"], f"`{e['id']}`", e.get("type") or "—", _signs(e), "sì" if e.get("mark") else "al primo uso" if e.get("mark_source") else "no",
                      found_in.get(e["id"], 0)] for e in listed]), "", "</details>", ""]


def framework_reading_section() -> list[str]:
    pins = _json(ENGINES_PACKAGE)["dependencies"]
    rows = [[_codes(css.STYLESHEETS), "fogli di stile, nel dialetto del suffisso"],
            [_codes(css.MARKUP), "markup: classi, id e blocchi `<style>`"],
            *[[f"`{suffix}`", f"componenti, con il compilatore del framework (`indexers/{module.__name__.rsplit('.', 1)[-1]}.py`)"]
              for suffix, module in sorted(css.COMPONENTS.items())],
            *[[_codes(sorted(s for s, r in css.UNREAD.items() if r == reason)), f"non letti; il motivo nel codice: «{reason}»"]
              for reason in sorted(set(css.UNREAD.values()))]]
    return ["## Letture proprie di framework e dialetti", "",
            "Oltre al riconoscimento: i componenti Vue e Svelte entrano nell'indice di scip-typescript "
            "(`indexers/components.py`) e il loro `<script>` nello snapshot (`languages/sfc.py`); il grafo dei fogli "
            "di stile (`indexers/css.py`) legge questi file con i parser fissati in "
            f"`{_rel(ENGINES_PACKAGE)}`: " + ", ".join(f"{k} {v}" for k, v in sorted(pins.items())) + ". "
            "La sua misura è la riga `stylesheet` della sezione Analizzatori.", "",
            *_table(["Estensioni", "Lettura"], rows), ""]


def flows_section() -> list[str]:
    text = CENSUS.read_text(encoding="utf-8")
    pairs = []
    for title, body in re.findall(r"^### (.+?)\n(.*?)(?=^##|\Z)", text.split("## Catalogo", 1)[1], re.M | re.S):
        kinds = [row.split("|")[1].strip() for row in body.splitlines()
                 if row.startswith("| ") and not row.startswith(("| Tipo", "| ---"))]
        pairs.append([title, len(kinds), "; ".join(kinds)])
    return ["## Collegamenti dei flussi", "",
            f"`daodan/core/flows.py` applica regole di collegamento di {len(flows.LINKS)} specie: "
            + _codes(flows.LINKS) + "; un nodo di store ha uno di " + str(len(flows.NODE_TYPES)) + " tipi: "
            + _codes(flows.NODE_TYPES) + ". Il censimento "
            f"([{CENSUS.name}](../research/{CENSUS.name})) cataloga "
            f"{sum(p[1] for p in pairs)} tipi di punto di connessione; quali il prodotto unisce lo dice la sua "
            "sezione «Stato». Riconoscimento per tipo: non misurato.", "",
            *_table(["Coppia", "Tipi nel censimento", "Tipi"], pairs), ""]


def render() -> str:
    run_path = RESULTS / "pipeline" / f"{RUN}.json"
    report = _json(run_path.with_suffix(".report.json"))
    raw = _json(run_path)
    registry = _json(service_registry.REGISTRY)
    file, date, code = STACK
    stack = _json(RESULTS / file)
    if stack["code"]["local"] != code:
        raise SystemExit(f"{file} is from code {stack['code']['local']}, not {code}: write its date in STACK")
    cards = _cards()
    lines = ["# Codebase Map: che cosa supporta", "",
             "Scritto da `daodan/core/support_table.py` con i dati del prodotto e i "
             "risultati dei benchmark nel repository: non si modifica a mano, si riscrive con "
             "`python support_table.py build`, e `tests/test_codebase_map_support_table.py` fallisce se il file non "
             "è quello che lo script scrive.", "",
             "Misure, ognuna con il suo file e la sua data:", "",
             "- Esito: i casi del giro in cui l'analizzatore è finito `fresh` sui casi del giro che hanno il "
             "linguaggio.",
             "- Copertura delle chiamate: i siti con una risposta sui siti del linguaggio "
             "(`benchmarks/project-model/README.md`, «Il grafo completo sul corpus»).",
             "- File nell'indice: i file indicizzati sui file dello snapshot.",
             "- Riconoscimento: le voci attese trovate sulle voci attese di `expected.json`.",
             "- Il resto sono conteggi; dove non c'è misura la cella dice «non misurato».", "",
             *languages_section(cards, run_path), *analyzers_section(report, raw, run_path),
             *build_section(report, raw, run_path), *stack_section(registry, stack),
             *services_section(registry, stack), *framework_reading_section(), *flows_section()]
    return "\n".join(lines).rstrip("\n") + "\n"


def check(path: Path = DOC) -> list[str]:
    """Problems of the document at `path`: none when it is what `render` writes now."""
    if not path.is_file():
        return [f"{path}: missing; run `python support_table.py build`"]
    if path.read_text(encoding="utf-8") != render():
        return [f"{path}: not what support_table.py writes now; run `python support_table.py build`"]
    return []


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("build").add_argument("--out", type=Path, default=DOC)
    sub.add_parser("check").add_argument("file", type=Path, nargs="?", default=DOC)
    args = parser.parse_args(argv)
    if args.command == "build":
        args.out.write_text(render(), encoding="utf-8", newline="\n")
        return 0
    problems = check(args.file)
    print("\n".join(problems) or "ok")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
