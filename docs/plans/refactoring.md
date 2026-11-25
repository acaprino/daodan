# Piano di refactoring di Daodan (coda attiva)

**Stato:** unico piano attivo. Si lavora su **un solo traguardo alla volta**. Contratto architetturale in [`docs/specs/architettura.md`](../specs/architettura.md); tutto ciò che è differito o ritirato è in [`docs/backlog.md`](../backlog.md).

**Traguardo attualmente aperto:** **T0**.

| Traguardo | Che cosa chiude | Dipende da | Stato |
| --- | --- | --- | --- |
| **T0** | Baseline verificata su Modal e chiusura contraddizioni codice/doc | — | **APERTO** |
| **T1** | Pipeline statica (`list_files` -> `find_entry_points`), Django/FastAPI/Flask, orchestratore e piano unico | T0 | Bloccato |
| **T2** | Collegamenti statici (`link_calls` SCIP) e vista statica del grafo | T1 | Bloccato |
| **T3** | Isolamento minimo, esecuzione osservata (`run_and_observe`) e mappa (`assemble_graph`) | T2 | Bloccato |

---

## T0 — Baseline verificata su Modal *(APERTO)*

Nessun riordino della pipeline prima di chiudere T0. Obiettivo: partire da uno stato reale misurato e ripetibile.

1. **[misura]** Eseguire la suite intera su Modal sul codice attuale (anagrafica formati, modulo linguaggio, `pipeline_tree.py`) e registrare revisione, comando ed esiti; confermare con una seconda esecuzione.
2. **[misura]** Chiudere la «Verifica» dello stack dal fork su Modal: nessuna perdita sul corpus, tempo scansione veloce, prova che nulla del progetto gira sull'host con `cli()`/Node veri (rif. commit `614c940`, spec stack dal fork).
3. **[difetto]** Classificare e risolvere (o documentare con riproduzione) i difetti bloccanti dello stack: test instabile `test_codebase_map_app.py`, `replace => ../local` Go e repo `path` Composer letti come esterni dal fork, 37 marchi senza cornice, Avro duplicato, `technologies.state`.
4. **[accertato nel codice]** Contraddizioni dei vecchi documenti risolte:
   - **Run di lavoro (`snapshot.py refresh`), hook e regole 1–4 review:** **implementati nel codice** (`daodan/core/snapshot.py`: `WORKING_RUN`, `query_gate`, `refresh_working`, `_refresh_locked`; hook `PostToolUse` in `plugins/codebase-map/hooks/hooks.json` -> `daodan mcp --hook`; `tests/test_codebase_map_working_run.py`; regole 1–4 presenti in `review-method/SKILL.md:15-17`, `review-preparation/references/team-review.md:164`, `daodan/review/reviewer-common.md:32-34`, `review-consolidation/references/team-review.md:5`). Esito test da confermare su Modal (punto 1).
   - **Copertura dell'intero sorgente (`whole-source-coverage`):** **Parte A implementata e misurata** (`daodan/core/composition.py`: `GROUP_BYTES`, `pack`, `coverage_scope`, `reviewer_cells`, `coverage_groups`, `bind`, `account`; `tests/test_senior_review_composition.py`; 3 run misurate l'8 novembre 2026 in `benchmarks/whole-source-coverage/README.md:54-86`). **Parte B (riuso celle) e prova preparazione 3 richieste:** non implementate / non eseguite (restano in [`docs/backlog.md`](../backlog.md)).
   - **Task 12 modello di build (pre-mappa):** **base implementata** (`daodan/core/premap/__init__.py` con 35 `SOURCES`, `join`, `derive`, `write`, `EXECUTES`, `python_runs`, 25 test `tests/test_codebase_map_premap*.py`; già gestiti `WRAPPER_SELF`, `WRITTEN_ELSEWHERE`, vincoli runtime come `toolchains` in `renovate.py`, `libs.versions.toml` in `jvm_files.py`, `Directory.Packages.props` in `project_files.py`, `external_packages` PyPI e `angular-project` in `module_graph.py`). **Restano aperti in T1 (punto 10):** `external_packages` oltre PyPI (Go/Maven/Gradle/Cargo/npm), tipo/campo dedicato per BOM/`platform()`/POM genitore, scope/extra toolchain residui e separazione delle 35 sorgenti autonome da `premap.SOURCES`.
5. **Allineare documentazione operativa:** rigenerare `docs/plugins/codebase-map-supporto.md` (`support_table.py build`), portare `docs/pipeline/` nel repo, aggiornare i rimandi a 8 step in `README.md` e `docs/plugins/codebase-map.md`.
6. **Fissare il campione di riferimento** (1 stack + 1 progetto reale con domande verificate, inclusi casi con callback, overload e dispatch dinamico per `link_calls`) e il protocollo del confronto cieco prima di aprire T1.
7. **[deciso] Fissare il criterio di isolamento rete:** nessuna uscita diretta dal container, solo proxy verso registri autorizzati (inclusi redirect, DNS e IP letterali); il parser dei lockfile resta controllo preventivo. Se T0 scarica dipendenze, eseguire questo test già in T0; altrimenti collaudarlo in T3 prima del primo uso con rete.

**Cancello T0:** due run coerenti su Modal; ogni difetto noto è corretto oppure riproducibile e classificato; contraddizioni del punto 4 accertate sul codice; campione di riferimento e criterio di rete fissati. Da T1 in poi vale **zero nuove regressioni** rispetto a T0.

---

## T1 — Pipeline statica e piano unico *(Bloccato da T0)*

Accorpa le ex ondate 1–4. Fuori: SCIP, Kiri, esecuzione dinamica e nuova UI.

### `list_files` (ex ondata 1)
1. **[deciso]** Regola `.h` in `languages/detect/rules/` su tree-sitter con tetto deterministico (aggiornare `benchmarks/header-language`).
2. **[deciso]** Riconoscimento per nome file (`Dockerfile`, `Makefile`) nello stesso formato.
3. Tetto ai byte letti per regola e prova di costo lineare; fix **[difetto]** regola `.ts` su `<?xml` / `<!DOCTYPE` (112 divergenze).
4. **[misura]** Gate su 180 progetti + piano 122 progetti invariato su Modal; verificare che nessun percorso invochi `go-enry`, poi rimuoverlo dall'immagine.

### `read_code` — SQL e PL/SQL
5. **[spike]** Provare una grammatica `tree-sitter` SQL su fixture reali (package body, trigger, quoting, SQL dinamico) verificando oggetti estratti e intervalli sorgente prima di estendere i lettori custom. Usare `SQLGlot` (SQL) e `ANTLR grammars-v4` (PL/SQL, comunitaria) solo come comparatori: l'adozione primaria richiede deroga esplicita al vincolo tree-sitter.

### `recognize_stack` e `find_modules` (ex ondata 2)
6. **[deciso] / [misura]** Prima di aggiungere le 10 nuove famiglie di regole al fork `stack-analyser`, eseguire un confronto affiancato con **Syft** su monorepo e lockfile (tenendo il classificatore proprio per build system e moduli), insieme a `benchmarks/stack-build-tools/` su Modal.
7. **[deciso]** Aggiungere al fork `stack-analyser` (rilascio `.6`) solo ciò che il confronto del punto 6 lascia scoperto: CMake, Bazel, Meson, Make, autotools, sbt, .NET SDK, Mix, Nx (`project.json`), Python su `pyproject.toml`/`requirements.txt`.
8. **[deciso]** Creare `daodan/data/build-tools.json` con test di coerenza rispetto agli adattatori.
9. **[deciso]** `recognize_stack` gira per primo su `list_files` (senza moduli); `find_modules` gira dopo per ogni strumento trovato e assegna le tecnologie ai moduli. Nessuna sorgente in `premap.SOURCES` decide più da sé se applicarsi.
10. Chiudere i residui verificati del modello di build (estendere `external_packages` oltre PyPI per unità interne vs esterne, campo/tipo dedicato per BOM/`platform()`/POM genitore **[deciso]**, voce unica unità/pacchetto **[deciso]**, scope/`declared_in` residui) e ripristino cartelle annidate (Lerna, Cargo, .NET, `requirements.txt`).

### `find_entry_points` (ex ondata 3)
11. **[deciso]** Spostare sorgenti framework e Noir fuori da `premap.SOURCES`; `binder.bind` dentro lo step; `premap/container_runner.py` servizio comune a `find_modules` e `find_entry_points`.
12. **[deciso]** Integrare le tre sorgenti **Django, FastAPI e Flask** (già scritte, oggi scollegate) in `find_entry_points`, secondo Principio 5 (introspezione nel container come primaria, Noir come integrazione/fallback con provenienza dichiarata).
13. **[difetto]** Correggere `premap/flask_app.py` (`read()` raccoglie solo dati grezzi, il binder lega alle funzioni) e i difetti del binder (anonime in Go/C#, default anonimi).
14. Estendere l'unione Noir + framework oltre Next.js (React Router, SvelteKit, Nuxt) e completare i gap aperti dei framework (Next.js, React Router, SvelteKit, Nuxt, Angular da `read_code`, Astro, Go generico, wrapper HTTP).

### Orchestratore, nomi semantici e piano unico (ex ondata 4)
15. **[deciso]** Adottare gli identificatori semantici stabili (`list_files` … `assemble_graph`) in codice, eventi, giornale e cartelle (mantenendo lettura dei giornali vecchi); rimuovere lo step `parse`.
16. **[deciso]** Implementare il piano unico al chiamante (completo nei vincoli prima dell'avvio, incrementale nelle azioni scoperte in `recognize_stack`/`find_modules`/`find_entry_points`), uguale per UI, MCP e CLI.
17. Freschezza controllata in un punto solo (`step.skipped`); prove 2 e 5 (equivalenza modalità e ripiego dichiarato accanto al dato); spezzare le 3 funzioni >80 righe (`engine_pass.index_stage`, `snapshot.write_reading`, `snapshot._refresh_locked`).

**Scelte aperte da chiudere prima/durante T1:**
- `go-enry`: resta o si toglie? (ex scelta 5)
- `build_units.py` senza container: parser statico puro come ripiego dichiarato, o lacuna? (ex scelta 1 — qualunque comando che può eseguire codice progetto richiede il container)
- Pacchetti noti solo a `find_modules` (lock/Compose/Renovate): `technologies.merge` senza rilanciare il fork? (ex scelta 2)
- Licenza PolyForm dei lettori GitNexus e valutatore stringhe per percorsi calcolati (ex scelte 6, 7).

**Cancello T1:** sul campione fissato in T0, il chiamante riceve un solo piano; moduli, entry point (inclusi Django/FastAPI/Flask con test di regressione su `Flask.read()`) e lacune sono verificati; `premap.SOURCES` non contiene più sorgenti autonome né rotte/eventi; zero nuove regressioni rispetto a T0.

---

## T2 — Collegamenti statici (`link_calls` SCIP) e vista statica *(Bloccato da T1)*

Accorpa la ex ondata 5 e la parte statica della ex ondata 8.

1. **[deciso]** Introdurre il piccolo *evidence model* interno di `link_calls`: tree-sitter identifica il sito di chiamata, SCIP agisce come primo adapter risolutore (`sito`, `candidati`, `fonte`, stato `risolto`/`ambiguo`/`ignoto`). **[misura]** Su fixture con callback, overload e dispatch dinamico misurare precisione, falsi archi, irrisolti, tempo e memoria per indicizzatore; nessuna migrazione a LSIF/LSP, compiler API solo dove colmano lacune misurate.
2. Aggiornamento incrementale indice SCIP (test su file cambiato, misura su `chi` e `tududi`, rimozione `engine-answers.sqlite`) e richieste mirate (`codebase_map_index` con `targets`, rimozione passo per posizione e `--engine scip`).
3. JVM (`javapoet`, `klaxon`, rimozione `JavaEngine`/`KotlinEngine`/`KotlinResolver.kt`), C/C++ (immagine unica + `FETCHCONTENT_SOURCE_DIR_*` **[deciso]**, `zlib`, `tinyxml2`), fogli di stile.
4. Pulizia doppioni (secondo Pyright, `typescript_unbound.js`), indagine **[difetto]** timeout ~6 min su 1/4 passaggi staccati e 154 chiamate `self.metodo()`, chiusura eventuale migrazione SQL/PL-SQL dallo spike di T1.
5. **[deciso]** Unione statica in `assemble_graph` (archi cross-modulo, ingressi legati alle definizioni, motore generale dei legami da `feat/link-key-shape`, test che il codice dei legami non nomini framework).

**Cancello T2:** soglie SCIP (JVM, C/C++, CSS) registrate nei README dei benchmark; passo per posizione rimosso; *evidence model* e vista statica verificati sul campione fissato in T0; zero nuove regressioni rispetto a T1.

---

## T3 — Isolamento minimo, esecuzione osservata e mappa *(Bloccato da T2)*

Accorpa la parte minima necessaria delle ex ondate 6, 7 e 8. **Fuori da T3:** «Kiri ovunque», modello locale per comandi, superfici desktop/Android/Windows.

1. **Isolamento minimo verificato (ex ondata 6):** proxy pubblico con controllo host, tabella chiusa comandi, rifiuto lockfile con git/URL/`file:`/`-e` (controllo preventivo), neutralizzazioni package manager, `--cap-drop ALL`, utente non root. **Test decisivo di rete `[deciso]`:** blocco di ogni uscita diretta dal container (inclusi redirect, DNS e IP letterali), solo traffico via proxy verso registri autorizzati.
2. **Comandi da CI e utente (ex ondata 7):** lettura passo test dalla CI del progetto; comando `confermato` dell'utente nell'archivio Daodan; `builds`/`starts` da `angular.json`, `tauri.conf.*`, `pyproject.toml`, Cargo, Dockerfile, Compose, pnpm/Yarn/Bun.
3. **Esecuzione osservata (`run_and_observe`):** su un programma e una superficie (`web` o `webview`), albero chiamate/frontiere, esplorazione browser/webview con soli dati/credenziali CI, collegamento fino all'arco osservato in `assemble_graph`. **[misura]** Confrontare i registratori `*_record.*` con backend standard per tipo di evidenza (`sys.monitoring` su Python 3.12+ per call events, V8 per copertura, OpenTelemetry per frontiere/span, `strace`/eBPF per processi/rete), ritirando gli hook custom solo dopo equivalenza e overhead verificati.
4. **Diagnosi e verifica mappa (ex ondata 8):** correggere **[difetto]** `on` senza punto citato e `verified` senza store provato; fix collaudo su sottocartella/archivio nel progetto; diagnosticare lo `0/19` del confronto cieco e rieseguire la misura con protocollo fissato in T0.

**Scelte aperte da chiudere prima di T3:**
- Ordine tra albero delle chiamate e corsa del programma; primo linguaggio (ex scelta 12).
- Definizione di «ingresso» / varianti vs due flussi e soglie `benchmarks/system-map` (ex scelte 8, 9, 11, 13).

**Cancello T3:** sonda di rete e rifiuto lockfile URL verdi; 1 progetto reale con gestore diverso da npm tracciato dal comando fino all'arco osservato nella mappa; verbale del confronto cieco e verdetti di `benchmarks/system-map` salvati nei rispettivi README.
