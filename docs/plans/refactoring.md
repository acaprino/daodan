# Piano di refactoring di Daodan (coda attiva)

**Stato:** unico piano attivo. Si lavora su una sola tranche aperta alla volta. Contratto di arrivo in [`docs/specs/architettura.md`](../specs/architettura.md); tutto ciò che è differito o ritirato è in [`docs/backlog.md`](../backlog.md).

**Traguardo aperto:** **T0** — **Tranche aperta:** **T0.A** (`1/5`).

**Legenda:** `[deciso]` scelta approvata dal proprietario; `[deciso — riaperto da X]` scelta del proprietario su cui la review del 25 novembre ha aperto una verifica nelle «Scelte aperte»; `[misura]` prova da eseguire su Modal; `[difetto]` errore noto da correggere o mettere in quarantena; `[spike]` prova tecnica a tempo/perimetro chiuso; `[accertato nel repository]` fatto verificato sul codice attuale. Le sigle `B` (bloccante), `M` (importante, da [`zoom_out_report.md`](../reviews/2026-11-25-refactoring/zoom_out_report.md)) e `I` (da `inventive catalyst` nello stesso rapporto) rimandano a [`goldfish_review_report.md`](../reviews/2026-11-25-refactoring/goldfish_review_report.md); i rimandi storici «ex ondata/scelta/Task» vengono da `git show 66e09dbca~1:docs/specs/2026-11-25-refactoring-completo.md`.

## Mappa di avanzamento globale (per tranche autonome)

| Tranche | Consegna autonoma (punti coperti) | Stato | Passi | Scelte aperte da chiudere prima | SHA verificato | Verifica remota / statica |
| --- | --- | --- | --- | --- | --- | --- |
| **T0.A** | Contraddizioni (`T0.4`), doppia corsa `suite`, verifica fork, protezione tessere e quarantena difetti (`T0.1`–`T0.3`) | **APERTA** | `1/5` | — | `78e070129` (`T0.4`) | Solo diff statico (`T0.4`); attesa `modal.yml` |
| **T0.B** | Scelte `T0`, eventuali sonde anticipate, doc operativa, campione/protocollo cieco e Cancello T0 (`T0.5`–`T0.7`) | Bloccata da `T0.A` | `0/4` | `B2`, `M1/I1`, `I2` | — | `test_codebase_map_support_table.py` + Cancello `T0` |
| **T1.A** | `list_files`: collegamento `header.py`, nomi file, tetto lineare, `.ts` XML, 180/122 progetti + prova SQL (`T1.1`–`T1.5`) | Bloccata da `T0.B` | — | Regola `.ts` XML | — | `modal_headers.py` + `modal_lang.py` su Modal |
| **T1.B** | `recognize_stack`, `find_modules`, `build-tools.json`, `container_runner` comune, residui build (`T1.6`–`T1.10`) | Bloccata da `T1.A` | — | `M2`, `M3`, `go-enry`, `build_units`, `technologies.merge` | — | `test_codebase_map_premap*.py` + `modal.yml` `corpus` |
| **T1.C** | `find_entry_points`: estrazione da `premap.SOURCES`, Django/FastAPI/Flask (`READERS`), binder, Noir (`T1.11`–`T1.14`) | Bloccata da `T1.B` | — | `B1`, PolyForm / valutatore stringhe | — | `test_codebase_map_premap_{django,fastapi,flask}.py` + `modal.yml` `suite` |
| **T1.D** | Orchestratore a 8 ID semantici, piano unico (`in attesa di approvazione`), `step.skipped`, Cancello T1 (`T1.15`–`T1.17`) | Bloccata da `T1.C` | — | `M4`, `M7`, `M8` | — | `test_codebase_map_pipeline*.py` + `modal.yml` `suite` |
| **T2.A** | Modello di evidenza in `link_calls` (estensione `edge_grading`/`edge_store`/`resolve_edges`) e misure (`T2.1`) | Bloccata da `T1.D` | — | `M5` | — | `test_codebase_map_edge*.py` + fixture su Modal |
| **T2.B** | SCIP incrementale e mirato, JVM (`KotlinResolver.kt`), C/C++, CSS, pulizia doppioni/timeout/SQL (`T2.2`–`T2.4`) | Bloccata da `T2.A` | — | Esito prova SQL `T1.5` | — | Benchmark SCIP su Modal (`chi`, `tududi`, JVM, C/C++) |
| **T2.C** | Unione statica in `assemble_graph` (archi fra moduli, legami senza framework nel codice) e Cancello T2 (`T2.5`) | Bloccata da `T2.B` | — | — | — | Test assenza framework + `modal.yml` `suite` |
| **T3.A** | Uscita di rete con approvazione, prova Smokescreen vs proxy, rifiuto host dichiarati/lockfile, `--cap-drop`/`--user` (`T3.1`) | Bloccata da `T2.C` | — | Esito `M1/I1`, popup GUI vs solo `approval_required` | — | `test_codebase_map_container.py` su container reale Modal |
| **T3.B** | Comandi CI/utente (`builds`/`starts`), `surface`/`ui_execution_deferred`, `run_and_observe` `web`/`webview` (`T3.2`–`T3.3`) | Bloccata da `T3.A` | — | `M6`, `M8`, ordine albero/corsa, primo linguaggio | — | Progetto reale non-npm tracciato su Modal |
| **T3.C** | Correzione `on`/`verified`, sottocartella/archivio, diagnosi `0/19`, confronto cieco e Cancello T3 (`T3.4`) | Bloccata da `T3.B` | — | Soglie e definizione ingresso `system-map`, esito `I2` | — | `benchmarks/system-map` su Modal + `modal.yml` `suite` |

## Regole di esecuzione: passi, verifiche e commit

1. **Dettaglio progressivo:** solo il traguardo `APERTO` espande i passi operativi `- [ ]` con file, verifica e commit; prima del primo commit di una nuova tranche i suoi passi vengono dettagliati e controllati sulle scelte già chiuse.
2. **Autonomia di tranche:** ogni tranche consegna un incremento committabile da solo e rispetta l'ordine delle dipendenze reali (es. `T1.B` crea `build-tools.json` prima che `T1.C` svuoti `premap.SOURCES` di rotte ed eventi e `T1.D` rinomini gli step).
3. **Zero esecuzioni sull'host (`AGENTS.md`):** nessun workflow automatico esegue `pytest` al push (`viewer.yml` copre `viewer/**`, `desktop.yml` compila Tauri e testa solo `tests/test_daodan_desktop.py`). Su richiesta del proprietario e con `git status` pulito, un singolo passo Python si verifica su container remoto Modal con `python tests/modal_pytest.py <file_test> -q`, mentre i cancelli usano `.github/workflows/modal.yml` (`workflow_dispatch` con `run=suite|proof|corpus|baseline`).
4. **Tracciamento SHA e bot CI:** si verifica il commit candidato `C` su albero pulito e si registra nella mappa lo SHA `C` insieme all'ID/URL della corsa in un commit documentale successivo (nota: `modal.yml` con `run=corpus` o `run=baseline` aggiunge un commit `github-actions[bot]` su `benchmarks/project-model/results/`; per i passi solo documentali vale l'ispezione statica del diff). Un esito rosso non avanza il contatore `Passi`.
5. **Quarantena esplicita:** i fallimenti o test instabili ammessi al Cancello T0 sono elencati in `docs/verification/2026-11-25-baseline-t0.md` con nome esatto del test, causa, comando di riproduzione e tranche di chiusura; da `T1.A` ogni fallimento fuori da quell'elenco è una regressione bloccante.

---

## T0 — Baseline verificata su Modal *(APERTO)*

Nessun riordino della pipeline prima di chiudere T0. Obiettivo: partire da uno stato misurato e ripetibile.

1. **[misura]** Eseguire due volte l'intera suite su Modal sul codice attuale e registrare revisione, comando, conteggi ed eventuali differenze fra le due corse (riferimento precedente in `tests/modal_pytest.py:18`: 3.919–3.920 passati, 75 saltati).
2. **[misura]** Chiudere la verifica dello stack dal fork su Modal: zero esecuzioni del progetto sull'host con `cli()`/Node veri (`run=proof`), e confronto sul corpus (`run=corpus`) contro `benchmarks/project-model/results/daodan_stack_fork_develop_68b784e.json` tramite `benchmarks/project-model/test_fork_stack.py` registrando tempi e differenze.
3. **[difetto]** Classificare e correggere (o mettere in quarantena riproducibile) i difetti aperti dello stack e del registro:
   - **Tessere dei marchi:** `daodan/core/registry_build.py` (`apply_marks`, chiamato da `build` e `set_marks`) sovrascrive le tessere con il simbolo nudo di Simple Icons e cancella i file senza `mark` (come `doctrinephp` in `daodan/data/registry-additions.json`); le 37 tessere mancanti e quella di Doctrine sono state copiate a mano il 25 novembre e il generatore non è tracciato nel repository.
   - **Test instabili:** isolare il flake documentato `test_playwright_keeps_control_event_and_state_after_the_page_closes` in `tests/test_codebase_map_playwright_controls.py` (fallito 2 volte su 10 con `-n 2`, `tests/modal_pytest.py:27-28`) e verificare se in `tests/test_codebase_map_app.py` esista un test instabile riproducibile.
   - **Difetti stack dal fork:** `replace => ../local` Go e repository `path` Composer letti come esterni dal fork, Avro duplicato, `technologies.state` che non scrive più la pre-mappa.
4. **[accertato nel repository]** Contraddizioni dei vecchi documenti accertate sul codice (commit `78e070129`, esito dei relativi test da confermare al punto 1):
   - **Run di lavoro (`snapshot.py refresh`), hook e regole 1–4 review:** presenti in `daodan/core/snapshot.py` (`WORKING_RUN`, `query_gate`, `refresh_working`, `_refresh_locked`), `plugins/codebase-map/hooks/hooks.json` (`daodan mcp --hook`), `tests/test_codebase_map_working_run.py` e `plugins/senior-review/skills/{review-method/SKILL.md:15-17,review-preparation/references/team-review.md:164,review-consolidation/references/team-review.md:5}` più `daodan/review/reviewer-common.md:32-34`.
   - **Copertura dell'intero sorgente (`whole-source-coverage`):** Parte A implementata in `daodan/core/composition.py` (`tests/test_senior_review_composition.py`) e misurata in `benchmarks/whole-source-coverage/README.md:54-86`; Parte B (riuso celle) e prova preparazione 3 richieste non implementate né eseguite (spostate in [`docs/backlog.md`](../backlog.md)).
   - **Modello di build nella pre-mappa:** presenti in `daodan/core/premap/__init__.py` 35 `SOURCES`, `join`, `derive`, `write`, `EXECUTES`, `python_runs` e 27 file `tests/test_codebase_map_premap*.py` (`WRAPPER_SELF` e `WRITTEN_ELSEWHERE` in `daodan/core/premap/renovate.py`, `libs.versions.toml` in `daodan/core/premap/jvm_files.py`, `Directory.Packages.props` in `daodan/core/premap/project_files.py`, `external_packages` PyPI e `angular-project` in `daodan/core/premap/module_graph.py`). I residui aperti sono elencati in `T1.10`.
5. **Allineare documentazione operativa:** rigenerare `docs/plugins/codebase-map-supporto.md` (`daodan/core/support_table.py build`, verificato da `tests/test_codebase_map_support_table.py`) e allineare i rimandi agli step della pipeline in `README.md` e `docs/plugins/codebase-map.md` in coerenza con la decisione `B2`.
6. **Fissare il campione di riferimento** (1 stack + 1 progetto reale con commit fissato e domande verificate su callback, overload e dispatch dinamico per `link_calls`) e il protocollo del confronto cieco prima di aprire `T1`.
7. **[deciso]** Recepire il contratto **«Uscita di rete con approvazione»** (`docs/specs/architettura.md`, «Servizi comuni») e decidere se la prova del proxy / sonda su container reale entra già prima di `T1` o resta in `T3.A`:
   - **[accertato nel repository]** Oggi la rete è usata prima di `T3` e apre più dei soli registri: `daodan/core/container.py` (`PROXY_SCRIPT`) apre `package-managers.json`, gli host fissi degli strumenti (`daodan/core/premap/container_runner.py` `TOOLS`, `daodan/core/preparation.py` `RESTORES`), gli host dichiarati dal progetto (`preparation.declared`, `preparation.python_vcs`), il `retry` di `container_runner.py` e il secondo tentativo di Gradle; `npm install` gira anche in `dynamic/` e `indexers/`; `premap.EXECUTES` esegue codice del progetto nel container. In `container.py` esistono già le sonde `leaves` (`:1355`) e `reached` (`:1408`), non ancora estese a redirect, DNS, IP letterali e indirizzi interni.

**Scelte aperte da chiudere prima del Cancello T0:**
- **Problema risolto dal refactoring (`B2`):** quale difetto concreto di oggi giustifica gli otto step, il piano unico e lo spostamento delle sorgenti, da scrivere in apertura di `architettura.md`?
- **Collocazione della prova proxy / sonda di rete (`M1`, `I1`):** la sonda su container reale (ed eventuale confronto Smokescreen vs `PROXY_SCRIPT`) si anticipa subito prima di `T1` o resta in `T3.A`?
- **Collocazione della diagnosi dello `0/19` (`I2`):** la classificazione per causa dei 19 flussi mancati su `poc-data-extraction` si esegue ora in `T0.B` sulla mappa esistente (rieseguendo il confronto a ogni cancello) o resta in `T3.C`?

**Cancello T0:** due corse `modal.yml` `run=suite` sullo SHA finale di `T0` con l'identico insieme di esiti fuori dalla tabella di quarantena (`docs/verification/2026-11-25-baseline-t0.md`); `apply_marks` protetto da test; contraddizioni del punto 4 accertate; scelte `B2`, `M1/I1`, `I2` registrate; campione di riferimento e protocollo cieco scritti. Da `T1.A` vale zero fallimenti fuori dalla quarantena di `T0`.

### Passi operativi di T0 (`T0.A` – `T0.B`)

#### Tranche `T0.A` — Baseline su Modal, protezione tessere e quarantena difetti *(APERTA — 1/5)*
- [x] **Passo `T0.A.0` — Accertamento contraddizioni (`T0.4`):** verificato sul codice e registrato in `docs/plans/refactoring.md` e `docs/backlog.md` (`78e070129`).
- [ ] **Passo `T0.A.1` — Doppia corsa `suite` su Modal (`T0.1`):** su albero pulito lanciare due volte `.github/workflows/modal.yml` (`run=suite`) e salvare SHA, URL delle due corse, conteggi e differenze in `docs/verification/2026-11-25-baseline-t0.md`. *Verifica:* 2 corse completate sullo stesso SHA. *Commit:* `docs(verification): registra doppia corsa Modal suite per T0.1`.
- [ ] **Passo `T0.A.2` — Verifica stack dal fork (`T0.2`):** lanciare `modal.yml` con `run=proof` e `run=corpus` (il bot aggiorna `benchmarks/project-model/results/`), verificare il confronto con `daodan_stack_fork_develop_68b784e.json` tramite `python tests/modal_pytest.py benchmarks/project-model/test_fork_stack.py -q` e annotare esito e tempi in `docs/verification/2026-11-25-baseline-t0.md`. *Verifica:* `run=proof` e `test_fork_stack.py` verdi su Modal. *Commit:* `docs(verification): esito proof e corpus stack dal fork per T0.2`.
- [ ] **Passo `T0.A.3` — Protezione tessere in `registry_build.apply_marks` (`T0.3a`):** aggiornare `daodan/core/registry_build.py` e `daodan/data/registry-additions.json` (`mark` per `doctrinephp` e conservazione delle tessere con cornice Daodan sia da `build` sia da `set_marks`), con test di regressione in `tests/test_codebase_map_service_registry.py`. *Verifica:* `python tests/modal_pytest.py tests/test_codebase_map_service_registry.py -q` verde su Modal. *Commit:* `fix(registry): preserva le tessere di Daodan e doctrinephp in apply_marks`.
- [ ] **Passo `T0.A.4` — Tabella di quarantena e classificazione difetti stack (`T0.3b`):** riprodurre su Modal e registrare in `docs/verification/2026-11-25-baseline-t0.md` (una riga per voce: file, test, causa, riproduzione, tranche di correzione) il flake Playwright, la verifica di `tests/test_codebase_map_app.py` e i 4 difetti stack (`replace` Go, `path` Composer, Avro duplicato, `technologies.state`). *Verifica:* ogni voce riprodotta o dimostrata verde su Modal. *Commit:* `docs(verification): quarantena e classificazione difetti noti T0.3`.

#### Tranche `T0.B` — Scelte T0, allineamento doc, campione e Cancello T0 *(Bloccata da `T0.A` — 0/4)*
- [ ] **Passo `T0.B.1` — Registrazione scelte del proprietario (`B2`, `M1/I1`, `I2`):** scrivere la motivazione `B2` in `docs/specs/architettura.md` e registrare in `docs/plans/refactoring.md` la collocazione decisa per `M1/I1` e `I2`. *Verifica:* zero scelte aperte in `T0`. *Commit:* `docs(spec,plan): chiude scelte B2, M1/I1 e I2 di T0`.
- [ ] **Passo `T0.B.2` — Eventuali sonde o diagnosi anticipate da `T0.B.1`:** eseguire solo ciò che `T0.B.1` colloca in `T0` (sonda container reale su Modal in `tests/test_codebase_map_container.py` oppure classificazione statica dei 19 flussi in `benchmarks/system-map/README.md`); se entrambe restano in `T3`, marcare il passo saltato con rimando a `T0.B.1`. *Verifica:* `modal_pytest.py` verde o diff statico. *Commit:* un commit per artefatto prodotto.
- [ ] **Passo `T0.B.3` — Allineamento documentazione operativa (`T0.5`):** rigenerare `docs/plugins/codebase-map-supporto.md` con `support_table.py build` e allineare `README.md` e `docs/plugins/codebase-map.md`. *Verifica:* `python tests/modal_pytest.py tests/test_codebase_map_support_table.py -q` verde su Modal. *Commit:* `docs: rigenera tabella supporto e allinea rimandi pipeline (T0.5)`.
- [ ] **Passo `T0.B.4` — Campione di riferimento, protocollo cieco e chiusura Cancello T0 (`T0.6`, `T0.7`):** fissare progetto, commit, domande/oracolo e protocollo cieco in `benchmarks/system-map/README.md`, rieseguire due corse `modal.yml` `run=suite` se `T0.A.3`/`T0.B.2` hanno cambiato codice, chiudere `T0` nella mappa ed espandere i passi `- [ ]` di `T1.A`. *Verifica:* tutti i criteri del Cancello T0 soddisfatti. *Commit:* `docs(plan): chiude Cancello T0 e dettaglia passi T1.A`.

---

## T1 — Pipeline statica e piano unico *(Bloccato da T0)*

Fuori da T1: SCIP, Kiri, esecuzione dinamica e adeguamento della vista UI agli 8 step. Taglio in tranche `T1.A`–`T1.D` nella mappa di avanzamento.

### `list_files` (`T1.A`)
1. **[deciso]** Collegare `daodan/core/languages/header.py` (già scritto in WIP al commit `2d6a2881d` con `tests/test_codebase_map_header_language.py`) al posto della regola in `daodan/core/languages/__init__.py:125-137`, aggiornando `benchmarks/header-language` (`modal_headers.py`).
2. **[deciso]** Riconoscimento per nome file (`Dockerfile`, `Makefile`) nello stesso formato in `daodan/data/language-rules.toml`.
3. Tetto ai byte letti per regola e prova di costo lineare (`tests/test_codebase_map_language_cost.py`); decidere se correggere o confermare la regola `.ts` su `<?xml` / `<!DOCTYPE` in `daodan/data/language-rules.toml:20-25` (112 divergenze su 186.124 testi sintetici).
4. **[misura]** Verifica sui 180 progetti (`benchmarks/project-model/modal_lang.py`) e piano sui 122 progetti invariato su Modal. `go-enry` esce dall'immagine solo se la scelta aperta lo toglie dall'intero suo perimetro (`daodan/core/premap/enry.py`, `enry_facts.go`, `daodan-enry` in `container_runner.py`, `suffix_table.py`, `pipeline_tree.py`).

### `read_code` — SQL e PL/SQL (`T1.A`)
5. **[spike]** Provare una grammatica `tree-sitter` SQL su fixture reali (package body, trigger, quoting, SQL dinamico) verificando oggetti estratti e intervalli sorgente prima di toccare `daodan/core/languages/sql.py` e `plsql.py`. Usare `SQLGlot` e `ANTLR grammars-v4` solo come comparatori: l'adozione primaria richiede deroga esplicita al vincolo tree-sitter.

### `recognize_stack` e `find_modules` (`T1.B`)
6. **[deciso — riaperto da M2] / [misura]** Prima di aggiungere le 10 famiglie di regole al fork `stack-analyser`, chiarire e misurare su Modal ciò che resta da decidere oltre al confronto con Syft già presente (`benchmarks/stack-build-tools/`, da creare se confermato).
   - **[accertato nel repository]** Syft 1.57.1 è già misurato in `benchmarks/project-model/REPORT.md` (`tools/syft.py`, `results/syft.json`): dà i pacchetti e non le unità; 360 dipendenze dirette contro 673 di Renovate, senza separare le transitive (+1.827).
7. **[deciso — riaperto da M3]** Aggiungere al fork `stack-analyser` (rilascio `.6`) solo ciò che resta scoperto: CMake, Bazel, Meson, Make, autotools, sbt, .NET SDK, Mix, Nx (`project.json`), Python su `pyproject.toml` e `requirements.txt`.
   - **[accertato nel repository]** `daodan/core/premap/` ha già `cmake.py`, `bazel.py`, `meson.py`, `make.py`, `autotools.py`, `sbt.py` e `dotnet.py`; `cmake.py` e `bazel.py` trovano da sé il proprio manifesto; `mix-project` è in `premap.EXECUTES` senza file proprio, mentre Nx non ha adattatore in `premap/`.
8. **[deciso — riaperto da M3]** Creare `daodan/data/build-tools.json` con test di coerenza rispetto agli adattatori di `find_modules`.
9. **[deciso]** `recognize_stack` gira per primo su `list_files` (senza moduli); `find_modules` gira dopo (usando `build-tools.json` del punto 8) per ogni strumento trovato e assegna le tecnologie ai moduli. Nessuna sorgente in `premap.SOURCES` decide più da sé se applicarsi; `premap/container_runner.py` diventa servizio comune ai quattro step `find_modules`, `find_entry_points`, `link_calls` e `run_and_observe`.
10. Chiudere i residui del modello di build: estendere `external_packages` oltre PyPI (Go, Maven, Gradle, Cargo, npm), campo/tipo dedicato per BOM/`platform()`/POM genitore **[deciso]**, voce unica unità/pacchetto **[deciso]**, scope/`declared_in` residui e ripristino cartelle annidate (Lerna, Cargo, .NET, `requirements.txt`).

### `find_entry_points` (`T1.C`)
11. **[deciso]** Spostare le sorgenti framework (`FRAMEWORK_SOURCES`) e Noir fuori da `premap.SOURCES`; portare `binder.bind` dentro `find_entry_points`. Senza container non girano né sorgente dedicata né Noir: restano le query tree-sitter (`daodan/data/entry-queries.json`) e una lacuna dichiarata (`architettura.md`, «Strumenti nativi, Noir e sorgenti dedicate»).
12. **[deciso — riaperto da B1]** Integrare le tre sorgenti **Django, FastAPI e Flask** (`daodan/core/premap/{django_app,fastapi_app,flask_app}.py`, patch di collegamento già in `benchmarks/fastapi-routes/wiring/`) in `find_entry_points` secondo il Principio 5 di `architettura.md` (introspezione nel container come primaria, Noir come integrazione/ripiego con provenienza dichiarata). Con l'integrazione le tre voci entrano in `daodan/core/registry_build.py` (`READERS`) e il loro `support` nel registro passa da `partial` a `full`.
    - **[accertato nel repository]** I tre benchmark chiudono con «no» sulle applicazioni vere: `benchmarks/flask-routes/README.md` (collegamento tolto il 24 novembre 2026), `benchmarks/fastapi-routes/README.md` (24 novembre 2026: nelle condizioni di Daodan non carica nessuna delle due applicazioni), `benchmarks/django-routes/README.md` (0 funzioni su 132 su `healthchecks`; eventuale complemento di Noir solo per `djangorestframework`). Nessuna delle tre è in `premap.SOURCES` né in `FRAMEWORK_SOURCES`.
13. **[difetto]** Correggere la funzione `read` in `daodan/core/premap/flask_app.py` (raccoglie solo dati grezzi, il binder lega alle funzioni) e i difetti del binder (anonime in Go e C#, default anonimi).
14. Estendere l'unione Noir + framework oltre Next.js (React Router, SvelteKit, Nuxt) e completare le lacune aperte dei framework (Next.js, React Router, SvelteKit, Nuxt, Angular da `read_code`, Astro, Go generico, wrapper HTTP).

### Orchestratore, nomi semantici e piano unico (`T1.D`)
15. **[deciso]** Adottare gli identificatori semantici stabili (`list_files` … `assemble_graph`) in codice, eventi, giornale e cartelle (mantenendo la lettura dei giornali vecchi); rimuovere lo step `parse`.
    - **[accertato nel repository]** Oggi gli step sono sei: `STEPS = (Scan, Stack, Parse, Analyze, Dynamic, Union)` (`daodan/core/pipeline/__init__.py`). `README.md` porta sette nomi approvati il 22 novembre 2026; `daodan/core/pipeline_tree.py` tiene sia l'elenco attuale sia quello degli otto step.
16. **[deciso — riaperto da M4]** Estendere il piano unico (`daodan/core/pipeline/plan.py`) per UI, MCP e CLI: completo nei vincoli prima dell'avvio, incrementale nelle azioni scoperte in `recognize_stack`, `find_modules` e `find_entry_points`, incluso lo stato `in attesa di approvazione` e l'esposizione in sola lettura su MCP e CLI delle richieste di host bloccati dal proxy (`architettura.md`, «Il piano» e «Servizi comuni»).
    - **[accertato nel repository]** `daodan/core/pipeline/plan.py` espone già nodi `{id, step, adapter, [version], on, container, needs}`, lacune e `blocked`. `approval_required` e `host_denied` non sono ancora in `daodan/`. L'adeguamento completo della vista UI agli otto step è in [`docs/backlog.md`](../backlog.md).
17. Freschezza controllata in un punto solo (`step.skipped`); verifica dell'equivalenza tra modalità e del ripiego dichiarato accanto al dato; divisione delle 3 funzioni oltre 80 righe (`engine_pass.index_stage`, `snapshot.write_reading`, `snapshot._refresh_locked`).

**Scelte aperte da chiudere prima/durante T1:**
- `go-enry` (`T1.B`): mantenere o rimuovere l'intero perimetro (`premap/enry.py`, `enry_facts.go`, `daodan-enry`, `suffix_table.py`, `pipeline_tree.py`)?
- `daodan/core/build_units.py` senza container (`T1.B`): parser statico puro come ripiego dichiarato, o lacuna? Qualunque comando che può eseguire codice del progetto richiede sempre il container.
- Pacchetti noti solo a `find_modules` (`T1.B`): mantenere `technologies.merge` senza rilanciare il fork?
- Licenza PolyForm dei lettori GitNexus e valutatore di stringhe per percorsi calcolati (`T1.C`: ammessi o scartati?).
- Regola `.ts` su `<?xml` (`T1.A`): confermare la scelta documentata in `language-rules.toml:20-25` o modificarla?
- Django, FastAPI e Flask (`B1`, `T1.C`): quale ragione e quale misura in `T1.C` confermano la sorgente dedicata come primaria contro i tre verdetti «no» del punto 12?
- Confronto con Syft (`M2`, `T1.B`): quale decisione deve informare sulle famiglie del punto 7 oltre a `benchmarks/project-model/REPORT.md`?
- Famiglie nel fork e `build-tools.json` (`M3`, `T1.B`): quale difetto attuale correggono e con quale costo di manutenzione sul fork?
- Perimetro del piano unico in `T1.D` (`M4`): entrano subito tutti i 7 stati (incluso `in attesa di approvazione`) e i 3 fatti per azione, o in `T1.D` si estende `plan.py` alle azioni scoperte rimandando gli stati di consenso a `T3.A`?
- Taglio dei cancelli (`M7`): confermare un cancello intermedio per ciascuna sotto-tranche `T1.A`–`T1.D` e `T2.A`–`T2.C`?
- Collocazione di `surface`, `ui_execution_deferred`, `approval_required` (`M8`) e scelta se un modulo prenda il tipo del suo framework (`architettura.md`, «Nodi del grafo»): confermare `approval_required`/`host_denied` tra `T1.D` e `T3.A`, `surface` e `ui_execution_deferred` in `T3.B`, e decidere la regola sul tipo del modulo.

**Cancello T1:** sul campione fissato in `T0.B.4`, il chiamante riceve un solo piano; moduli, ingressi (inclusi Django/FastAPI/Flask in `READERS` con `support: full` e test su `flask_app.read`, se confermati da `B1`) e lacune sono verificati; `premap.SOURCES` non contiene più sorgenti autonome né rotte/eventi; zero fallimenti fuori dalla quarantena di `T0` su `modal.yml` `run=suite`.

---

## T2 — Collegamenti statici (`link_calls` SCIP) e vista statica *(Bloccato da T1)*

Taglio in tranche `T2.A`–`T2.C` nella mappa di avanzamento.

1. **[deciso — riaperto da M5]** Estendere il modello di evidenza interno di `link_calls` (`T2.A`): tree-sitter individua il sito di chiamata, SCIP agisce come primo adattatore risolutore (`sito`, `candidati`, `fonte`, stato `risolto`, `ambiguo`, `ignoto`). **[misura]** Su fixture con callback, overload e dispatch dinamico misurare precisione, falsi archi, irrisolti, tempo e memoria per indicizzatore; nessuna migrazione a LSIF/LSP, compiler API solo dove colmano lacune misurate.
   - **[accertato nel repository]** Strutture già presenti da estendere: `daodan/core/edge_grading.py` (`ambiguous-target`, `unresolved`, `project-callable`), `daodan/core/edge_store.py` (`verdict`, `resolver`, `confidence`), `daodan/core/resolve_edges.py` (`<engine>@<version>`).
2. Aggiornamento incrementale dell'indice SCIP (`T2.B`: test su file cambiato, misura su `chi` e `tududi`, rimozione `engine-answers.sqlite`) e richieste mirate (`codebase_map_index` con `targets`, rimozione passo per posizione e `--engine scip`).
3. Coperture SCIP per linguaggio (`T2.B`): JVM (`javapoet`, `klaxon`, rimozione `daodan/core/engines/KotlinResolver.kt`), C/C++ (immagine unica + `FETCHCONTENT_SOURCE_DIR_*` **[deciso]**, `zlib`, `tinyxml2`), fogli di stile.
4. Pulizia e difetti di risoluzione (`T2.B`): rimozione doppioni (secondo Pyright, `daodan/core/indexers/typescript_unbound.js`), indagine **[difetto]** timeout ~6 min su 1/4 passaggi staccati e 154 chiamate `self.metodo()`, eventuale migrazione SQL/PL-SQL in base allo spike `T1.5`.
5. **[deciso]** Unione statica in `assemble_graph` (`T2.C`): archi fra moduli, ingressi legati alle definizioni, adattatori di legame per tipo (HTTP, eventi, code, tabelle) con test che il codice dei legami non nomini framework. Il ramo `feat/link-key-shape` non esiste nel repository; oggi `daodan/core/flows.py` accoppia richiesta e rotta per metodo e schema del percorso.

**Scelte aperte da chiudere prima di T2:**
- Modello di evidenza (`M5`): quali campi o stati mancano esattamente a `edge_grading.py` ed `edge_store.py` per distinguere sito di chiamata tree-sitter e riferimento SCIP?

**Cancello T2:** soglie SCIP (JVM, C/C++, CSS) registrate nei rispettivi `benchmarks/*/README.md`; passo per posizione e `engine-answers.sqlite` rimossi; modello di evidenza e vista statica verificati sul campione fissato in `T0.B.4`; zero fallimenti fuori dalla quarantena su `modal.yml` `run=suite`.

---

## T3 — Uscita di rete con approvazione, esecuzione osservata e mappa *(Bloccato da T2)*

**Fuori da T3:** «Kiri ovunque», modello locale per comandi, superfici desktop/Android/Windows. Taglio in tranche `T3.A`–`T3.C` nella mappa di avanzamento.

1. **[deciso] Uscita di rete con approvazione e isolamento container (`T3.A`, salvo anticipo in `T0` per `M1/I1`):** attuare il contratto di `docs/specs/architettura.md` («Servizi comuni», «Il piano», «L'interfaccia segue la pipeline»):
   - **[misura] Scelta dello strumento proxy su Modal:** prova affiancata tra **Smokescreen** e `container.PROXY_SCRIPT` esteso sugli stessi criteri: solo porta 443, eccezione `apt`, lista da file, rifiuti leggibili, rifiuto degli indirizzi interni anche quando il nome è approvato (salvo sì apposito).
   - **Ritiro dell'apertura automatica degli host dichiarati:** senza chiedere si aprono solo i registri di `daodan/data/package-managers.json` e gli host fissi degli strumenti di Daodan; rimuovere l'apertura silenziosa di `preparation.declared`, `preparation.python_vcs`, il `retry` automatico di `premap/container_runner.py` e il secondo tentativo di Gradle.
   - **Consenso umano, whitelist e lacune:** richiesta preventiva per gli host dichiarati, rifiuto immediato per gli altri con rilancio del passo dopo il sì (se il passo riesce comunque con host rifiutato il risultato vale e la richiesta resta visibile); risposte «sempre per questo progetto», «solo per questa analisi», «no» salvate in `embedding_worker.shared_cache_dir` (mai nel progetto); approvazione **solo dalla GUI** (popup Sigrid su Imago con host, porta, indirizzo risolto e file dichiarante), mentre MCP e CLI mostrano le richieste in attesa senza poter approvare; lacune `approval_required` (senza risposta o senza schermo) e `host_denied` (dopo un no).
   - **Indurimento container e controlli preventivi (da creare):** `--cap-drop ALL` e `--user` nei punti di esecuzione di `daodan/core/container.py`, tabella chiusa dei comandi, rifiuto preventivo dei lockfile con `git+`/URL/`file:`/`-e`, neutralizzazioni degli script di lifecycle nei ripristini, e prova su container vero su Modal (estendendo `container.leaves` e `container.reached` a uscita diretta, redirect, DNS, IP letterali e indirizzi interni).
   - **[accertato nel repository]** Oggi `daodan/core/container.py` usa `--network none` in esecuzione, rete `--internal` con `PROXY_SCRIPT` in preparazione e `--security-opt no-new-privileges`, ma apre anche gli host dichiarati dal progetto, controlla solo nome e porta 443 (non l'IP risolto) e non passa `--cap-drop` né `--user`; `tests/test_codebase_map_container.py` verifica argomenti CLI e tre rifiuti dello script proxy, non un container reale. Rifiuto lockfile, tabella chiusa comandi e neutralizzazioni nei `RESTORES` non esistono ancora nel codice.
2. **Comandi da CI e utente (`T3.B`):** lettura del passo test dalla CI del progetto; comando `confermato` dell'utente nella cartella condivisa di Daodan; `builds` e `starts` da `angular.json`, `tauri.conf.*`, `pyproject.toml`, Cargo, Dockerfile, Compose, pnpm, Yarn e Bun.
3. **Superfici ed esecuzione osservata in `run_and_observe` (`T3.B`):** introduzione del campo `surface` nell'anagrafica (`web`, `webview` e lacuna `ui_execution_deferred:<superficie>` per le superfici differite), albero chiamate e frontiere, esplorazione browser/webview con soli dati e credenziali della CI, collegamento fino all'arco osservato in `assemble_graph`, e pulizia del percorso morto `join_sampled` (`daodan/core/dynamic/__init__.py:248`). **[misura — riaperto da M6]** Confrontare i registratori `*_record.*` con backend standard per tipo di evidenza (`sys.monitoring`, copertura V8, OpenTelemetry, `strace`/eBPF), ritirando gli hook solo dopo prova di equivalenza e costo.
   - **[accertato nel repository]** `daodan/core/dynamic/python_record.py` usa già `sys.monitoring`; esistono `javascript_record.js`, `go_record.go`, `jvm_record/` e `dotnet_record/`; `clang.py` e `rust.py` usano Callgrind (il container non concede eBPF); `explore.cjs` usa già la copertura precisa di V8 per i controlli; il profiler V8 è ritirato in `docs/backlog.md` ma `join_sampled` resta nel codice; `strace` è assente da `daodan/core/dynamic/`.
4. **Diagnosi e verifica della mappa (`T3.C`):** correggere **[difetto]** `on` senza punto citato e `verified` senza store provato; correggere il collaudo su sottocartella e su archivio dentro il progetto; diagnosticare lo `0/19` (se non già fatto in `T0.B.2`) e rieseguire il confronto cieco con il protocollo fissato in `T0.B.4`.
   - **[accertato nel repository]** `0/19`: con il modello debole, 0 flussi ritrovati su 19 nel caso più piccolo (`poc-data-extraction`), in due ripetizioni (`benchmarks/system-map/README.md:548-554`, «Scoperta cieca con il modello debole, variante A, 21 novembre 2026»).

**Scelte aperte da chiudere prima di T3:**
- Popup GUI di approvazione host (`T3.A`): entra un popup minimale nella GUI attuale già in `T3.A`, oppure fino all'adeguamento UI del backlog ogni host fuori da registri e host fissi resta in fail-closed con lacuna `approval_required`?
- Ordine tra albero delle chiamate e corsa del programma, e scelta del primo linguaggio in `T3.B` (ex scelta 12).
- Definizione di «ingresso» (varianti contro due flussi) e soglie numeriche di `benchmarks/system-map` in `T3.C` (ex scelte 8, 9, 11, 13).
- Backend runtime (`M6`, `T3.B`): mantenere il confronto del punto 3 senza un difetto misurato sui registratori attuali (ed escludendo Python, già su `sys.monitoring`, e il profiler V8 ritirato)?

**Cancello T3:** su Modal sono verdi la sonda su container reale (uscita diretta, redirect, DNS, IP letterali, IP interni), il proxy con blocco degli host non approvati (`approval_required` / `host_denied`) e il rifiuto preventivo dei lockfile con URL; 1 progetto reale con gestore diverso da npm è tracciato dal comando fino all'arco osservato nella mappa; verbale del confronto cieco e verdetti di `benchmarks/system-map` sono salvati nei rispettivi `README.md`, con `modal.yml` `run=suite` verde.
