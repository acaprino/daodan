#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# ///
"""Write the tree of the pipeline: for each step, what runs, when, with which tool at which version, where, and what it
gives. A development tool: it reads the code's own declarations and runs nothing of a project.

What is declared is read from the code (`declared`): the sources of the pre-map (`premap.SOURCES`), the analyzers
(`indexers.analyzers`), the observers (`dynamic.observers`), the languages and their rules (`file_formats`,
`languages.detect`) and the pins of the tools. What each one is for is a line of Italian written here, by its name.
`check` says what the two disagree on: a source with no line, a line whose source is gone, a file a line names that is
not there, and a page's data that is not what `build` writes. The page is `viewer/pipeline/` (Sigrid's `Steps` and `ItemList`),
built by the Viewer workflow into `docs/pipeline/`.

Today's order is the code's; the plan's is `docs/specs/architettura.md` («La pipeline a otto step»). The tie
between a language and its build tools, and between a framework and its languages, is this file's own (`CHOICES`).

    python pipeline_tree.py build
    python pipeline_tree.py check
"""
from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

OUT = SCRIPT_DIR.parents[1] / "viewer" / "pipeline" / "data.ts"
HEAD = ("// Written by daodan/core/pipeline_tree.py from the code's declarations: not edited by hand. `python pipeline_tree.py build`\n"
        "// writes it again, and `check` (tests/test_codebase_map_pipeline_tree.py) fails when it is behind.\n"
        "import type { Data } from './tree.ts';\n\nexport const DATA: Data = ")


def _is_release(value: str) -> bool:
    """A source's VERSION that is a tool's release, not `daodan/premap/v3`."""
    parts = value.removeprefix("v").split(".")
    return len(parts) > 1 and all(part.isascii() and part.isdigit() for part in parts)


def declared() -> dict:
    """What the code declares: sources, analyzers, observers, languages, and the version of each tool by the name of its row."""
    import container
    import dynamic
    import engine_tools
    import file_formats
    import format_catalog
    import indexers
    import languages
    import premap
    import preparation
    import secret_mask
    import stack_analyser
    from dynamic import app as dynamic_app, callgrind
    from indexers import components, jvm, python as scip_python, runtime
    from languages import detect
    versions = {source.NAME: str(source.VERSION) for source in premap.SOURCES if _is_release(str(source.VERSION))}
    analyzers = []
    for analyzer in indexers.analyzers():
        module = analyzer.__name__.rsplit(".", 1)[-1]
        analyzers.append({"module": module, "name": analyzer.NAME, "languages": list(analyzer.LANGUAGES), "container": analyzer.NEEDS_CONTAINER})
        version = getattr(analyzer, "VERSION", None) or {"java": jvm.VERSION, "kotlin": jvm.VERSION,
                                                         "rust": engine_tools.RUST_ANALYZER_RELEASE}.get(module)
        if version:
            versions[analyzer.NAME] = str(version)
    observers = [{"module": observer.__name__.rsplit(".", 1)[-1], "name": observer.NAME, "languages": list(observer.LANGUAGES)}
                 for observer in dynamic.observers()]
    for observer in observers:
        if "callgrind" in observer["name"]:
            versions[observer["name"]] = "Valgrind " + callgrind.VALGRIND_VERSION
    readers = {language: importlib.import_module("languages." + module).__name__.replace(".", "/") + ".py"
               for language, module in READERS.items()}
    read = [{"id": language, "extensions": [e for e, l in file_formats.SOURCES.items() if l == language], "reader_module": readers[language]}
            for language in languages.SUPPORTED_LANGUAGES if language in readers]
    mise = next((part for part in preparation.MISE[0].split("/") if part.startswith("v") and _is_release(part)), None)
    versions.update({"stack-analyser": stack_analyser.VERSION, "buchi di Python": "Pyright " + scip_python.PYRIGHT,
                     "componenti": "Volar " + components.PIN.rsplit("@", 1)[1], "esplorazione": "Playwright " + dynamic_app.PLAYWRIGHT,
                     "mascheratura dei segreti": secret_mask.VERSION, "ambienti Python": engine_tools.UV_VERSION,
                     "Node di Daodan": runtime.NODE_VERSION, "motore di container": "Kiri " + container.KIRI_VERSION,
                     "anagrafica dei formati": "Linguist " + format_catalog.VERSION, **({"toolchain del progetto": mise} if mise else {})})
    return {"sources": [source.NAME for source in premap.SOURCES], "analyzers": analyzers, "observers": observers, "languages": read,
            "supported": list(languages.SUPPORTED_LANGUAGES), "rules": sorted({rule.id for group in detect.RULES.values() for rule in group}),
            "versions": versions}


# The module of `languages/` that reads each language.
READERS = {"python": "python", "java": "java", "javascript": "javascript", "typescript": "typescript", "sql": "sql", "plsql": "plsql",
           "rust": "rust", "go": "go", "css": "stylesheet", "kotlin": "kotlin", "csharp": "csharp", "vue": "sfc", "svelte": "sfc",
           "astro": "sfc", "markup": "markup", "c": "cfamily", "cpp": "cfamily"}


def tree(decl: dict) -> dict:
    """The data of the page: the rows (one per thing a step uses), the steps in the two orders, and the choices."""
    JS, NPM = ["javascript", "typescript"], ["javascript", "typescript", "vue", "svelte", "astro"]
    rows = []
    def row(today, plan, name, file, kind, where, tool, does, langs=(), fam=(), fw=(), all=False, status=None, declared=None):
        rows.append({"today": today, "plan": plan, "name": name, "file": file, "kind": kind, "where": where, "tool": tool,
                     "does": does, "langs": list(langs), "fam": list(fam), "fw": list(fw), "all": all, "status": status, "declared": declared})

    # 1 elenco dei file
    row("s1", "p1", "perimetro", "tree_scope.py", "regola", "host", "Git: git ls-files --others --ignored", "Decide dove non entrare: ciò che Git ignora, cartelle con il punto, dipendenze e build, link.", all=True)
    row("s1", "p1", "anagrafica dei formati", "data/file-formats.json", "dato", "host", "Dato nostro; nomi di Linguist in linguist-catalog.json", "Quali file si registrano, con quale linguaggio; quali nomi non si aprono mai.", all=True)
    row("s1", "p1", "segreti", "source_files.py", "regola", "host", "Elenco di nomi, più entropia del contenuto (scritta a mano)", "Esclude .env, chiavi e file con valori generati prima di leggerli.", all=True)
    row("s1", "p1", "ts.xml-document", "data/language-rules.toml", "regola", "host", "Confronto letterale sul testo", "Un .ts che inizia come XML è una traduzione Qt, non TypeScript: non si legge.", langs=["typescript"])
    row("s1", "p1", "sql.oracle-words", "data/language-rules.toml", "regola", "host", "Confronto letterale sul testo", "Un .sql con parole solo di Oracle è PL/SQL.", langs=["sql", "plsql"])
    row("s1", "p1", "sql.anchored-type", "languages/detect/rules/sql_rowtype.py", "regola", "host", "Classe con un'espressione regolare", "%TYPE e %ROWTYPE dopo un nome: PL/SQL.", langs=["sql", "plsql"])
    row("s1", "p1", "h.syntax-tree", "languages/detect/rules/header.py", "regola", "host", "Albero sintattico C/C++ (tree-sitter); regex per Objective-C", "Un .h è C, C++ oppure Objective-C (che non si legge).", langs=["c", "cpp"])

    # 2 lettura del codice
    READ = {"python": ("ast della libreria standard di Python", "Classi, funzioni, import e chiamate."),
            "java": ("tree-sitter, grammatica Java", "Classi, metodi, import e chiamate."),
            "javascript": ("tree-sitter, grammatica JavaScript", "Funzioni, classi, import e chiamate; anche JSX."),
            "typescript": ("tree-sitter, grammatiche TypeScript e TSX", "Come JavaScript, più interfacce, enum e alias di tipo."),
            "sql": ("Lettore SQL nostro; sqlglot è fra le dipendenze", "Tabelle, viste e i riferimenti fra loro."),
            "plsql": ("Lettore PL/SQL nostro", "Package, body, cursori, eccezioni."),
            "rust": ("tree-sitter, grammatica Rust", "Funzioni, impl, trait, use e chiamate."),
            "go": ("tree-sitter, grammatica Go", "Funzioni, metodi come Receiver.Method, import e chiamate."),
            "css": ("Lettore dei fogli di stile nostro (CSS, SCSS, LESS)", "Un simbolo per ogni regola."),
            "kotlin": ("tree-sitter, grammatica Kotlin", "Classi, funzioni, import e chiamate."),
            "csharp": ("tree-sitter, grammatica C#", "Classi, metodi, using e chiamate."),
            "vue": ("Blocco <script> ai lettori JS/TS; template con la grammatica Vue di tree-sitter", "Script e template del componente."),
            "svelte": ("Blocco <script> ai lettori JS/TS; template con la grammatica Svelte di tree-sitter", "Script e template del componente."),
            "astro": ("Frontmatter ai lettori JS/TS", "Script del file .astro."),
            "markup": ("Lettore dei blocchi <style>", "Le regole di stile dentro HTML e template."),
            "c": ("tree-sitter, grammatica C", "Funzioni, struct, include e chiamate."),
            "cpp": ("tree-sitter, grammatica C++", "Classi, funzioni, namespace, include e chiamate.")}
    for lang in decl["languages"]:
        tool, does = READ.get(lang["id"], ("", ""))
        row("s2", "p2", f"lettore {lang['id']}", lang["reader_module"], "lettore", "host", tool, does + " Estensioni: " + " ".join(lang["extensions"]), langs=[lang["id"]])
    row("s2", "p2", "Python più nuovo", "languages/python_newer.py", "lettore", "host", "L'interprete che uv dà per la versione che il progetto dichiara", "Rilegge un file che il Python di Daodan rifiuta, senza pacchetti e fuori dal progetto.", langs=["python"])
    row("s2", "p2", "collegamenti lessicali", "resolution.py", "regola", "host", "Codice nostro", "Lega una chiamata solo quando il nome ha un unico candidato. Nessun tipo inferito.", all=True)

    # 3 scan: struttura del progetto (piano: 4 moduli)
    row("s3", "p4", "lettori dei manifest", "build_units.py", "lettore", "host", "Circa 35 lettori scritti a mano, uno per tipo di manifest", "Le unità di build da package.json, pyproject.toml, Cargo.toml, go.mod, pom.xml e altri. È ciò che fa i moduli senza container.", fam=["npm", "python", "jvm", "go", "cargo", "dotnet", "native"], status="doppione con lo stack: da decidere", declared="modules.py")
    B = [("python-build", "python_build.py", "lettore", "host", "File di configurazione della build Python", "Le cartelle dei pacchetti che la build dichiara.", ["python"]),
         ("requirements", "requirements.py", "lettore", "host", "File requirements, letti come li legge pip", "I pacchetti dichiarati.", ["python"]),
         ("python-tests", "python_tests.py", "lettore", "host", "pyproject.toml, tox.ini, setup.cfg, Makefile", "Come si lanciano i test.", ["python"]),
         ("uv", "uv.py", "comando", "container", "uv, dal uv.lock, senza rifare il lock e senza rete", "Il modello del progetto Python e i pacchetti locali.", ["python"]),
         ("npm-files", "npm_lock.py", "lettore", "host", "package.json e lockfile", "Come si installa il progetto.", ["npm"]),
         ("npm-tests", "npm_tests.py", "lettore", "host", "package.json", "Come si lanciano i test.", ["npm"]),
         ("npm-start", "npm_start.py", "lettore", "host", "package.json", "Come parte e come si costruisce un pacchetto.", ["npm"]),
         ("npm", "npm.py", "comando", "container", "npm: npm query \":root, .workspace\"", "I pacchetti e i membri del workspace come li vede npm.", ["npm"]),
         ("tsc", "tsc.py", "comando", "container", "TypeScript: tsc --showConfig", "Ogni tsconfig come lo risolve il compilatore.", ["npm"]),
         ("jvm-files", "jvm_files.py", "lettore", "host", "File di Gradle e Maven", "Gli strumenti e le versioni che la build chiede.", ["jvm"]),
         ("gradle", "gradle.py", "comando", "container", "Gradle, con un init script mentre configura la build", "Il modello dei progetti Gradle.", ["jvm"]),
         ("maven", "maven.py", "comando", "container", "Maven: help:effective-pom", "Il reactor e i moduli.", ["jvm"]),
         ("sbt", "sbt.py", "comando", "container", "sbt: show thisProject", "I progetti della build sbt.", ["jvm"]),
         ("go", "go.py", "comando", "container", "Il comando go", "Il modello di ogni modulo Go, anche annidato.", ["go"]),
         ("cargo", "cargo.py", "comando", "container", "Cargo: cargo metadata", "Crate, workspace e grafo dei pacchetti.", ["cargo"]),
         ("dotnet", "dotnet.py", "comando", "container", "MSBuild: dotnet msbuild -getProperty -getItem", "Ogni progetto .NET come lo valuta MSBuild.", ["dotnet"]),
         ("project-files", "project_files.py", "lettore", "host", "Package.swift, .csproj, Directory.Build.props", "La versione del linguaggio dichiarata.", ["dotnet"]),
         ("cmake", "cmake.py", "comando", "container", "CMake: file API codemodel-v2 dopo il configure", "I target e i comandi di compilazione.", ["native"]),
         ("meson", "meson.py", "comando", "container", "Meson: meson introspect", "Target e informazioni del progetto.", ["native"]),
         ("bazel", "bazel.py", "comando", "container", "Bazel: bazel query, bazel mod graph", "Il modello della build.", ["native"]),
         ("make", "make.py", "comando", "container", "GNU Make: make -pn", "Il database delle regole.", ["native"]),
         ("autotools", "autotools.py", "lettore", "host", "configure.ac e Makefile.am", "La build Autotools, letta come file.", ["native"]),
         ("compose", "compose.py", "comando", "container", "Docker Compose: docker compose config", "I servizi dei file Compose che la CI avvia.", ["docker"]),
         ("buildkit", "dockerfile.py", "comando", "container", "Il frontend di BuildKit", "Gli stadi di ogni Dockerfile.", ["docker"])]
    for name, file, kind, where, tool, does, fam in B:
        row("s3", "p4", name, "premap/" + file, kind, where, tool, does, fam=fam, declared=name)
    row("s3", "p4", "gitmodules", "premap/gitmodules.py", "lettore", "host", ".gitmodules", "I submodule Git dichiarati.", all=True, declared="gitmodules")
    row("s3", "p4", "renovate", "premap/renovate.py", "comando", "container", "Renovate, estrazione locale", "I pacchetti dichiarati per ogni gestore: un terzo lettore degli stessi manifest.", all=True, status="doppione: da misurare", declared="renovate")

    # framework: oggi in scan, nel piano 5 punti di ingresso
    F = [("next", "nextjs.py", "Il comando del progetto: next typegen", "Ogni rotta con il file che la serve.", ["next"], JS),
         ("react-router", "react_router.py", "react-router routes --json, remix routes --json", "Le rotte di React Router e Remix.", ["react-router"], JS),
         ("nuxt", "nuxt.py", "nuxt prepare e @nuxt/kit del progetto", "Rotte server di Nitro e pagine.", ["nuxt"], JS + ["vue"]),
         ("sveltekit", "sveltekit.py", "svelte-kit sync", "I file di ogni rotta.", ["sveltekit"], JS + ["svelte"]),
         ("angular", "angular.py", "Il compilatore di Angular (parseTemplate) e il suo type checker dei template", "Gli eventi dei template e che cosa chiamano.", ["angular"], ["typescript", "markup"]),
         ("astro", "astro.py", "Il compilatore di Astro (@astrojs/compiler)", "Gli eventi nei file .astro.", ["astro-fw"], JS + ["astro"])]
    for name, file, tool, does, fw, langs in F:
        row("s3", "p5", name, "premap/" + file, "comando", "container", tool, does, langs=langs, fw=fw, fam=["npm"], declared=name)
    row("s3", "p5", "noir", "premap/noir.py", "comando", "container", "Noir, scanner di rotte (OWASP)", "Le rotte dei backend, senza eseguire il progetto.", all=True, declared="noir")
    for name, tool in (("django", "L'URLconf caricato da Django"), ("fastapi", "Il loader e gli oggetti rotta di FastAPI"), ("flask", "La url_map dell'applicazione Flask")):
        row("s3", "p5", name, f"premap/{name}_app.py", "comando", "container", tool, "Le rotte con la funzione che le serve. Sulle app misurate Noir dava lo stesso.", langs=["python"], fw=["backend"], status="scritto, non collegato")
    row("after", "p5", "lettori degli ingressi", "entries.py + data/entry-queries.json", "lettore", "host", "tree-sitter, una query per grammatica (le query sono dati)", "Dove può partire un flusso: un onClick nel JSX, un decoratore, un gestore di evento.", langs=JS + ["vue", "svelte", "python", "java", "kotlin", "go", "rust", "csharp"], fw=["react", "next", "react-router", "nuxt", "sveltekit", "angular", "astro-fw", "backend"])
    row("after", "p5", "legatore", "binder.py", "regola", "host", "Codice nostro", "Lega ogni rotta o evento trovato alla funzione dello snapshot.", all=True)

    # 4 stack (piano: 3)
    row("s4", "p3", "stack-analyser", "stack_analyser.py, stack_recognition.py", "strumento", "host", "Il nostro fork, con il Node di Daodan", "Framework, librerie, strumenti di build e servizi, ognuno con il file che lo prova. Legge file, non esegue nulla.", all=True)
    row("s4", "p3", "menzioni di host", "registry_hosts.py", "regola", "host", "Codice nostro sull'anagrafica dei servizi", "Un host di un servizio noto in un URL dei sorgenti è una menzione, non una prova.", all=True)
    row("s4", "p4", "tecnologie per modulo", "technologies.py", "regola", "host", "Codice nostro", "Assegna a ogni modulo le tecnologie dichiarate nei suoi file. Nel piano avviene dopo i moduli.", all=True)

    # 5 chiamate (piano: 6)
    A = {"scip-python": ("scip-python (Pyright sotto)", "Dove punta ogni chiamata Python."),
         "scip-typescript": ("scip-typescript (il compilatore TypeScript sotto)", "Dove punta ogni chiamata JS e TS, anche dentro Vue e Svelte."),
         "scip-java": ("scip-java, dentro la build Maven o Gradle", "Dove punta ogni chiamata Java."),
         "scip-kotlin": ("scip-java, dentro la build Gradle", "Dove punta ogni chiamata Kotlin."),
         "scip-dotnet": ("scip-dotnet", "Dove punta ogni chiamata C#."),
         "scip-go": ("scip-go", "Dove punta ogni chiamata Go."),
         "scip-rust": ("rust-analyzer, uscita SCIP; lancia cargo check e le macro", "Dove punta ogni chiamata Rust."),
         "scip-clang": ("scip-clang, sul database di compilazione di CMake", "Dove punta ogni chiamata C e C++."),
         "stylesheet": ("Grafo nostro, con i compilatori dei dialetti", "Lega classi, id, variabili e animazioni alle regole che le dichiarano. Nessun indice SCIP.")}
    for a in decl["analyzers"]:
        tool, does = A.get(a["name"], ("", ""))
        langs = ["css", "markup", "vue", "svelte", "astro"] if a["name"] == "stylesheet" else a["languages"]
        row("s5", "p6", a["name"], f"indexers/{a['module']}.py", "analizzatore", "container" if a["container"] else "host", tool, does, langs=langs)
    row("s5", "p6", "buchi di Python", "indexers/python_unbound.py", "analizzatore", "host", "Il language server di Pyright, interrogato su ogni accesso x.y", "Dà la causa di una chiamata che l'indice non lega (Any, Unknown).", langs=["python"])
    row("s5", "p6", "buchi di TypeScript", "indexers/typescript_unbound.js", "analizzatore", "container", "Il type checker di TypeScript", "Dà la causa di un membro che l'indice non lega.", langs=JS)
    row("s5", "p6", "tipi mancanti", "indexers/typescript_types.py", "analizzatore", "container", "npm, pacchetti @types", "Installa a parte i tipi che il progetto non ha, senza toccarne l'albero.", langs=JS)
    row("s5", "p6", "componenti", "indexers/components.py", "analizzatore", "container", "Vue: @vue/language-core (Volar). Svelte: svelte2tsx", "Traduce i componenti in TypeScript perché scip-typescript li indicizzi.", langs=["vue", "svelte"], fw=["nuxt", "sveltekit"])
    row("s5", "p6", "dialetti CSS", "indexers/css_*.py", "analizzatore", "host", "Sass, Less, Stylus, Tailwind, css-tree", "Compila ogni dialetto per leggere le regole che produce.", langs=["css", "markup", "vue", "svelte", "astro"])
    row("s5", "p6", "lettore dell'indice", "code_graph.py", "regola", "host", "Codice nostro, con tree-sitter per il nodo di ogni occorrenza", "Trasforma un indice SCIP in archi e buchi, uguale per ogni linguaggio.", all=True)

    # 6 esecuzione (piano: 7)
    O = {"dynamic-record-python": ("I test del progetto sotto un registratore (sys.monitoring)", "Le chiamate che avvengono davvero nei test."),
         "dynamic-record-javascript": ("I test del progetto sotto un registratore nostro", "Le chiamate osservate nei test JS e TS."),
         "dynamic-record-jvm": ("I test Gradle o Maven sotto un agente Java", "Le chiamate osservate in Java e Kotlin."),
         "dynamic-record-go": ("I test dei moduli, su una copia dei sorgenti riscritta", "Le chiamate osservate in Go."),
         "dynamic-record-dotnet": ("dotnet test sotto un registratore nostro", "Le chiamate osservate in C#."),
         "dynamic-callgrind-rust": ("cargo test sotto Callgrind di Valgrind", "Le chiamate osservate in Rust."),
         "dynamic-callgrind-clang": ("CTest sotto Callgrind di Valgrind", "Le chiamate osservate in C e C++.")}
    for o in decl["observers"]:
        tool, does = O.get(o["name"], ("", ""))
        row("s6", "p7", o["name"], f"dynamic/{o['module']}.py", "osservatore", "container", tool, does, langs=o["languages"])
    row("s6", "p7", "avvio dell'app", "dynamic/app.py", "osservatore", "container", "Lo script start o dev di package.json, con npm run", "Avvia l'app dichiarata dal progetto. pnpm, Yarn e Bun non ancora.", langs=NPM, fam=["npm"], fw=["react", "next", "react-router", "nuxt", "sveltekit", "angular", "astro-fw"])
    row("s6", "p7", "esplorazione", "dynamic/explore.cjs", "osservatore", "container", "Chromium con Playwright: albero di accessibilità e coverage di V8", "Legge i controlli di ogni pagina, li preme uno per uno e registra quale funzione parte.", langs=NPM, fam=["npm"], fw=["react", "next", "react-router", "nuxt", "sveltekit", "angular", "astro-fw"])

    row("s6", "p7", "test Playwright del progetto", "dynamic/playwright_prepare.cjs", "osservatore", "container", "La CLI Playwright del progetto stesso", "Legge la configurazione dei test Playwright che il progetto dichiara e installa il browser della revisione giusta.", langs=NPM, fam=["npm"], fw=["react", "next", "react-router", "nuxt", "sveltekit", "angular", "astro-fw"])
    row("s6", "p7", "controlli nei test Playwright", "dynamic/playwright_controls.cjs", "osservatore", "container", "Un preload di Node dentro i test Playwright del progetto", "Registra lo stato del controllo che ogni test aziona davvero, con lo stesso lettore del DOM dell'esplorazione.", langs=NPM, fam=["npm"], fw=["react", "next", "react-router", "nuxt", "sveltekit", "angular", "astro-fw"])
    row("s6", "p7", "funzioni partite", "dynamic/control_coverage.js", "osservatore", "container", "La coverage precisa di V8 e il debugger di Chrome", "Dice quale funzione del progetto parte quando un controllo viene premuto.", langs=NPM, fam=["npm"], fw=["react", "next", "react-router", "nuxt", "sveltekit", "angular", "astro-fw"])

    # dopo la pipeline
    row("after", "pafter", "schede e regole di collegamento", "engines.py", "strumento", "host", "Un motore LLM a scelta: API compatibile OpenAI, Claude (CLI) o Codex (CLI)", "Scrive le schede semantiche e le regole dei collegamenti, legate all'impronta dello snapshot.", all=True)
    row("after", "pafter", "mascheratura dei segreti", "secret_mask.py", "strumento", "host", "Secretlint", "Trova e maschera i segreti in ogni testo che lascia la macchina o va a un modello.", all=True)
    row("after", "pafter", "flussi", "flows.py", "regola", "host", "Codice nostro", "Collega chi scrive, chi legge e le azioni dell'utente lungo il grafo.", all=True)
    row("after", "pafter", "embedding", "embedding_worker.py", "strumento", "host", "onnxruntime e tokenizers, facoltativi e offline", "Ricerca per significato sulla mappa.", all=True, status="facoltativo")

    # servizi comuni
    C = [("motore di container", "container.py", "Docker, Podman o Kiri (il motore di Daodan)", "Dove gira ogni comando che esegue codice del progetto. Senza motore il passo è una lacuna."),
         ("immagine di base", "preparation.py", "debian:trixie-slim, fissata per digest", "Il sistema di ogni container."),
         ("proxy dei registri", "container.py", "Un proxy nostro su python:3.13-alpine", "La preparazione raggiunge solo i registri dei pacchetti (data/package-managers.json); i test girano senza rete."),
         ("toolchain del progetto", "preparation.py", "mise", "Installa le versioni che il progetto dichiara (Node, Python, Go, Rust…)."),
         ("ambienti Python", "preparation.py, engine_tools.py", "uv, scaricato e fissato da Daodan", "Ripristina i pacchetti Python e fa girare gli stadi con i pacchetti dello snapshot."),
         ("Node di Daodan", "indexers/runtime.py", "Node da nodejs.org", "Fa girare stack-analyser, scip-python e i motori dei fogli di stile sull'host."),
         ("JDK", "preparation.py", "Temurin 17, più quello che la build chiede", "Per Gradle, Maven, sbt e scip-java."),
         ("SDK Android", "preparation.py", "sdkmanager di Google", "I pacchetti dell'SDK che una build Android dichiara."),
         ("dipendenze native", "preparation.py", "vcpkg e Conan", "Ripristina le librerie C e C++ che una radice CMake dichiara."),
         ("lanciatore dei comandi", "premap/container_runner.py", "Codice nostro sopra il motore di container", "Esegue i comandi delle sorgenti in un container e ne riporta l'uscita. Oggi è della pre-mappa: nel piano diventa comune.")]
    for name, file, tool, does in C:
        row("common", "common", name, file, "strumento", "container" if name not in ("Node di Daodan", "motore di container") else "host", tool, does, all=True, status="da rendere comune" if name == "lanciatore dei comandi" else None)

    # 7 unione (piano: 8)
    row("s7", "p8", "archi fra moduli", "modules.py", "regola", "host", "Codice nostro", "Import e chiamate fra un modulo e l'altro, dagli archi provati.", all=True)
    row("s7", "p8", "lacune", "pipeline/__init__.py", "regola", "host", "Codice nostro", "Dice cosa manca: file fuori dall'indice, linguaggi senza analizzatore, chiamate fra due linguaggi (Java e Kotlin, Go e C, Python e C).", all=True)


    ALWAYS = "sempre"
    WHEN = {"perimetro": ALWAYS, "anagrafica dei formati": ALWAYS, "segreti": "per ogni file", "ts.xml-document": "per ogni file .ts",
            "sql.oracle-words": "per ogni file .sql, .ddl, .dml", "sql.anchored-type": "per ogni file .sql, .ddl, .dml", "h.syntax-tree": "per ogni file .h",
            "Python più nuovo": "se un .py non si legge con il Python di Daodan", "collegamenti lessicali": ALWAYS,
            "lettori dei manifest": "per ogni manifest nell'elenco dei file", "python-build": "se c'è una configurazione di build Python",
            "requirements": "se c'è un file requirements", "python-tests": "se c'è pyproject.toml, tox.ini, setup.cfg o un Makefile", "uv": "se c'è uv.lock",
            "npm-files": "se c'è package.json", "npm-tests": "se c'è package.json", "npm-start": "se c'è package.json", "npm": "se c'è package.json",
            "tsc": "se c'è un tsconfig", "jvm-files": "se c'è una build Gradle o un pom.xml", "gradle": "se c'è settings.gradle o build.gradle",
            "maven": "se c'è pom.xml", "sbt": "se c'è build.sbt", "go": "se c'è go.mod", "cargo": "se c'è Cargo.toml", "dotnet": "se c'è un progetto .NET",
            "project-files": "se c'è Package.swift, .csproj o Directory.Build.props", "cmake": "se c'è CMakeLists.txt", "meson": "se c'è meson.build",
            "bazel": "se è dichiarato un workspace Bazel", "make": "se c'è un makefile che GNU Make legge", "autotools": "se c'è configure.ac o Makefile.am",
            "compose": "se un passo della CI avvia Docker Compose", "buildkit": "se c'è un Dockerfile", "gitmodules": "se c'è .gitmodules",
            "renovate": "sempre, se c'è il container", "next": "se un package.json dichiara next",
            "react-router": "se un package.json dichiara @react-router/dev o @remix-run/dev", "nuxt": "se un package.json dichiara nuxt",
            "sveltekit": "se un package.json dichiara @sveltejs/kit", "angular": "se un package.json dichiara @angular/core",
            "astro": "se un package.json dichiara astro", "noir": "sempre, se c'è il container", "django": "mai: non è collegato",
            "fastapi": "mai: non è collegato", "flask": "mai: non è collegato", "lettori degli ingressi": "per ogni file letto",
            "legatore": "per ogni rotta o evento trovato", "stack-analyser": ALWAYS, "menzioni di host": "per ogni URL nei sorgenti",
            "tecnologie per modulo": ALWAYS, "buchi di Python": "dopo scip-python", "buchi di TypeScript": "dopo scip-typescript",
            "tipi mancanti": "se un pacchetto non ha i suoi tipi", "componenti": "se ci sono file .vue o .svelte",
            "dialetti CSS": "se ci sono fogli Sass, Less, Stylus o Tailwind", "lettore dell'indice": "per ogni indice prodotto",
            "avvio dell'app": "se un package.json ha uno script start o dev", "esplorazione": "se l'app è partita",
            "archi fra moduli": ALWAYS, "lacune": ALWAYS,
            "test Playwright del progetto": "se il progetto dichiara test Playwright", "controlli nei test Playwright": "durante i test Playwright del progetto",
            "funzioni partite": "a ogni controllo premuto", "schede e regole di collegamento": "quando la mappa è pronta",
            "mascheratura dei segreti": "per ogni testo che va a un modello", "flussi": "quando gli archi sono freschi", "embedding": "se attivati",
            "motore di container": "per ogni comando che esegue il progetto", "immagine di base": "per ogni container", "proxy dei registri": "durante la preparazione",
            "toolchain del progetto": "se il progetto dichiara una versione", "ambienti Python": "se c'è un progetto Python", "Node di Daodan": "al primo uso",
            "JDK": "se c'è una build JVM", "SDK Android": "se una build dichiara Android", "dipendenze native": "se una radice CMake dichiara vcpkg o Conan",
            "lanciatore dei comandi": "per ogni comando di una sorgente"}
    FOUND = {"python-build": "Python", "requirements": "Python", "python-tests": "Python", "uv": "uv", "npm-files": "Node.js", "npm-tests": "Node.js",
             "npm-start": "Node.js", "npm": "Node.js", "tsc": "TypeScript", "jvm-files": "Gradle o Maven", "gradle": "Gradle", "maven": "Maven", "sbt": "sbt",
             "go": "Go", "cargo": "Cargo", "dotnet": ".NET", "project-files": ".NET o Swift", "cmake": "CMake", "meson": "Meson", "bazel": "Bazel",
             "make": "Make", "autotools": "Autotools", "compose": "Docker Compose", "buildkit": "Docker", "next": "Next.js", "react-router": "React Router o Remix",
             "nuxt": "Nuxt", "sveltekit": "SvelteKit", "angular": "Angular", "astro": "Astro", "lettori dei manifest": "uno strumento di build, senza container"}
    for r in rows:
        name = r["name"]
        if name.startswith("lettore ") and name not in WHEN:
            exts = r["does"].split("Estensioni: ")[1]
            r["when"] = "per ogni file " + exts
        elif r["kind"] == "analizzatore" and name not in WHEN:
            r["when"] = "se ci sono file " + ", ".join(r["langs"]) + (" e c'è il container" if r["where"] == "container" else "")
        elif r["kind"] == "osservatore" and name not in WHEN:
            r["when"] = "se il modulo dichiara come lanciare i test"
        else:
            r["when"] = WHEN.get(name, "")
        r["when_plan"] = ("se il passo 3 ha trovato " + FOUND[name]) if name in FOUND else r["when"]
    WRITES = {"pafter": "flussi e schede", "common": "", "s1": "l'elenco dei file", "s2": "lo snapshot: simboli, import, chiamate", "s3": "modules.json e premap.json", "s4": "technologies.json",
              "s5": "gli archi provati (engine-edges.sqlite)", "s6": "gli archi osservati", "s7": "il grafo completo", "after": "i flussi",
              "p1": "l'elenco dei file", "p2": "lo snapshot: simboli, import, chiamate", "p3": "lo stack, con il file che prova ogni voce",
              "p4": "il modello di build: moduli, dipendenze, comandi", "p5": "i punti di ingresso, legati alle funzioni",
              "p6": "gli archi provati", "p7": "gli archi osservati", "p8": "il grafo completo"}

    for r in rows:
        r["ver"] = decl["versions"].get(r["name"], "")

    STEPS = {"today": [("s1", "Elenco dei file", "inventario", "Percorre la cartella. Di ogni file: hash e linguaggio."),
                       ("s2", "Lettura del codice", "lettura", "Apre ogni file dell'elenco: simboli, import, chiamate."),
                       ("s3", "Struttura del progetto", "scan", "Scrive moduli e pre-mappa. Oggi contiene tre competenze: build, punti di ingresso, pacchetti."),
                       ("s4", "Tecnologie", "stack", "Riconosce framework, librerie, strumenti e servizi, e li assegna ai moduli."),
                       ("s5", "Chiamate", "analyze", "Per ogni linguaggio, l'analizzatore ufficiale dice dove punta ogni chiamata."),
                       ("s6", "Esecuzione", "dynamic", "Test e app nel container: ciò che viene chiamato davvero."),
                       ("s7", "Grafo finale", "union", "Unisce e dice cosa manca."),
                       ("after", "Dopo la pipeline", "flussi e schede", "Legame di rotte ed eventi alle funzioni, flussi, schede del modello. Oggi il legame avviene fuori dagli step."),
                       ("common", "Servizi comuni", "container e preparazione", "Ciò che ogni step usa quando deve eseguire qualcosa: il motore, l'immagine, le toolchain, i registri.")],
             "plan": [("p1", "Elenco dei file", "1_list_files", "Percorre la cartella. Di ogni file: hash e linguaggio."),
                      ("p2", "Lettura del codice", "2_read_code", "Apre ogni file dell'elenco: simboli, import, chiamate."),
                      ("p3", "Stack", "3_recognize_stack", "Solo analisi: quali strumenti di build, framework e tecnologie ci sono, e dove. Nessun modulo."),
                      ("p4", "Moduli", "4_find_modules", "Per ogni strumento di build trovato al 3, il suo adattatore dà moduli, dipendenze, comandi."),
                      ("p5", "Punti di ingresso", "5_find_entry_points", "Per ogni framework trovato al 3, il suo strumento dà rotte, pagine ed eventi, legati alle funzioni."),
                      ("p6", "Chiamate", "6_link_calls", "Per ogni linguaggio, l'analizzatore ufficiale dice dove punta ogni chiamata."),
                      ("p7", "Esecuzione", "7_run_and_observe", "Test e app nel container: ciò che viene chiamato davvero."),
                      ("p8", "Grafo finale", "8_assemble_graph", "Unisce e dice cosa manca."),
                      ("pafter", "Dopo la pipeline", "flussi e schede", "Flussi e schede del modello, sul grafo completo."),
                      ("common", "Servizi comuni", "container e preparazione", "Ciò che ogni step usa quando deve eseguire qualcosa: il motore, l'immagine, le toolchain, i registri.")]}
    LANG_NAMES = {"python": "Python", "java": "Java", "javascript": "JavaScript", "typescript": "TypeScript", "sql": "SQL", "plsql": "PL/SQL", "rust": "Rust", "go": "Go", "css": "CSS e dialetti", "kotlin": "Kotlin", "csharp": "C#", "vue": "Vue (.vue)", "svelte": "Svelte (.svelte)", "astro": "Astro (.astro)", "markup": "HTML e template", "c": "C", "cpp": "C++"}
    # what a choice brings with it: a language its build family, a framework its languages and family
    CHOICES = [("Linguaggi", [(f"lang:{k}", v, {"langs": [k], "fam": {"python": ["python"], "javascript": ["npm"], "typescript": ["npm"], "vue": ["npm"], "svelte": ["npm"], "astro": ["npm"], "java": ["jvm"], "kotlin": ["jvm"], "go": ["go"], "rust": ["cargo"], "csharp": ["dotnet"], "c": ["native"], "cpp": ["native"]}.get(k, []), "fw": []}) for k, v in LANG_NAMES.items()]),
               ("Strumenti di build", [("fam:npm", "npm, tsc", {"langs": [], "fam": ["npm"], "fw": []}), ("fam:python", "pip, uv", {"langs": [], "fam": ["python"], "fw": []}), ("fam:jvm", "Gradle, Maven, sbt", {"langs": [], "fam": ["jvm"], "fw": []}), ("fam:go", "Go modules", {"langs": [], "fam": ["go"], "fw": []}), ("fam:cargo", "Cargo", {"langs": [], "fam": ["cargo"], "fw": []}), ("fam:dotnet", ".NET, MSBuild", {"langs": [], "fam": ["dotnet"], "fw": []}), ("fam:native", "CMake, Meson, Bazel, Make, Autotools", {"langs": [], "fam": ["native"], "fw": []}), ("fam:docker", "Docker Compose, Dockerfile", {"langs": [], "fam": ["docker"], "fw": []})]),
               ("Framework", [("fw:react", "React (senza router con comando)", {"langs": JS, "fam": ["npm"], "fw": ["react"]}), ("fw:next", "Next.js", {"langs": JS, "fam": ["npm"], "fw": ["next"]}), ("fw:react-router", "React Router, Remix", {"langs": JS, "fam": ["npm"], "fw": ["react-router"]}), ("fw:nuxt", "Nuxt", {"langs": JS + ["vue"], "fam": ["npm"], "fw": ["nuxt"]}), ("fw:sveltekit", "SvelteKit", {"langs": JS + ["svelte"], "fam": ["npm"], "fw": ["sveltekit"]}), ("fw:angular", "Angular", {"langs": ["typescript", "markup"], "fam": ["npm"], "fw": ["angular"]}), ("fw:astro-fw", "Astro", {"langs": JS + ["astro"], "fam": ["npm"], "fw": ["astro-fw"]}), ("fw:backend", "Backend con rotte (Django, FastAPI, Flask, Spring…)", {"langs": [], "fam": [], "fw": ["backend"]})])]

    steps = {mode: [{"key": key, "title": title, "code": code, "what": what, "writes": WRITES.get(key, "")}
                    for key, title, code, what in listed] for mode, listed in STEPS.items()}
    choices = [{"id": key, "name": name, "group": group, **tags} for group, items in CHOICES for key, name, tags in items]
    return {"rows": rows, "steps": steps, "choices": choices}


def text(data: dict) -> str:
    """The page's data as it is written: a TypeScript module, one row per line."""
    def lines(items: list) -> str:
        return "[\n" + ",\n".join("    " + json.dumps(item, ensure_ascii=False) for item in items) + ",\n  ]"
    steps = "{\n" + "".join(f"    {mode}: {lines(listed).replace(chr(10) + '    ', chr(10) + '      ').replace(chr(10) + '  ]', chr(10) + '    ]')},\n"
                             for mode, listed in data["steps"].items()) + "  }"
    return HEAD + "{\n  rows: " + lines(data["rows"]) + ",\n  steps: " + steps + ",\n  choices: " + lines(data["choices"]) + ",\n};\n"


def check(decl: dict | None = None, written: str | None = None) -> list[str]:
    """What the tree and the code disagree on, one line each; empty when they agree."""
    decl = declared() if decl is None else decl
    data = tree(decl)
    rows, problems = data["rows"], []
    names = [row["name"] for row in rows]
    problems += [f"{name}: two rows have this name" for name in sorted({n for n in names if names.count(n) > 1})]
    told = {row["declared"] for row in rows if row["declared"]}
    problems += [f"{name}: a source of the pre-map with no row here" for name in sorted(set(decl["sources"]) - told)]
    problems += [f"{name}: a row for a source the pre-map no longer has" for name in sorted(told - set(decl["sources"]))]
    problems += [f"{language}: a language with no reader named in READERS" for language in decl["supported"] if language not in READERS]
    problems += [f"{row['name']}: no words say what it is for" for row in rows if not row["tool"] or not row["does"] or not row["when"]]
    said = {row["name"] for row in rows}
    problems += [f"{rule}: a rule of the language with no row here" for rule in decl["rules"] if rule not in said]
    keys = {mode: {step["key"] for step in listed} for mode, listed in data["steps"].items()}
    for row in rows:
        for mode in keys:
            if row[mode] not in keys[mode]:
                problems.append(f"{row['name']}: `{row[mode]}` is no step of `{mode}`")
        for part in row["file"].replace(" + ", ", ").split(", "):
            base = SCRIPT_DIR.parent if part.startswith("data/") else SCRIPT_DIR
            if not (any(base.glob(part)) if "*" in part else (base / part).exists()):
                problems.append(f"{row['name']}: names {part}, which is not there")
    for choice in data["choices"]:
        for language in choice["langs"]:
            if language not in decl["supported"]:
                problems.append(f"{choice['id']}: names the language {language}, which the snapshot does not read")
    written = OUT.read_text(encoding="utf-8") if written is None and OUT.is_file() else written
    if written != text(data):
        problems.append(f"{OUT.name}: not what `pipeline_tree.py build` writes")
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("command", choices=("build", "check"))
    args = parser.parse_args(argv)
    decl = declared()
    if args.command == "build":
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(text(tree(decl)), encoding="utf-8", newline="\n")
    problems = check(decl)
    print("\n".join(problems) or f"{OUT.name}: holds", file=sys.stderr if problems else sys.stdout)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
