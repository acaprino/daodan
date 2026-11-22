# Stack dal fork, piano 3 di 3: il passaggio

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Il passo `stack` di Daodan riconosce solo attraverso il fork di stack-analyser, in entrambe le scansioni; ogni segno porta la sua fonte e la scansione da cui viene; il registro resta come anagrafica.

**Architecture:** Parte A, nel fork: un rilascio `.3` che legge il perimetro da un file invece che dalla riga di comando e sa scrivere il proprio catalogo. Parte B, in Daodan: la traduzione oggi nel benchmark diventa il modulo `stack_recognition.py`; `technologies.derive` la chiama al posto di `service_registry.run` e unisce i segni nuovi con quelli delle fonti che in questa scansione non hanno girato; il registro si genera dal catalogo del rilascio e perde i segni.

**Tech Stack:** TypeScript/Vitest (fork, `C:\Users\alfio\Documents\ChatGPT\Daodan\stack-analyser`, ramo `feature/stack-detection`); Python 3.12/pytest (Daodan, ramo nuovo `stack-dal-fork` da `develop`). Gli strumenti veri girano su Modal.

**Spec:** `docs/specs/2026-11-21-stack-dal-fork.md`, «Disegno» 2.2–2.6, «Ordine» punto 4, «Verifica». Il piano 2 ha misurato e ha scritto ciò che ha trovato in `benchmarks/project-model/README.md`, sezione «Lo step `stack` dal fork».

## Che cosa consegnano i piani 1 e 2

- Rilascio `1.27.6-daodan.2` del fork, fissato in `daodan/core/stack_analyser.py` (`VERSION`, `URL`, `SHA256`), in `tests/modal_pytest.py` e in `benchmarks/project-model/modal_stack_fork.py`; due test legano i tre punti.
- `stack_analyser.run(project, *, declarations=(), skip_dirs=None, ignore=()) -> dict`, `cli()`, `node(project)`: lo strumento, provato su Modal con il rilascio vero ma con `cli` e `node` sostituiti.
- `benchmarks/project-model/tools/fork_stack.py`: la traduzione (`declarations`, `perimeter`, `_signs`, `found`, `recognize`) e le misure del confronto (`compare`, `measure`, `summary`, …), con 70 test.
- Il giro sul corpus (178 progetti su 180): nessun nome atteso perso; scansione veloce 0,52 s di mediana contro 0,013 s.
- Uscita del fork: componenti con `evidence: [{tech, kind, value, path, line?, source}]`, `kind` in `package | image | action | terraform | file | extension | env | source`.

## Che cosa il piano 2 ha trovato e questo piano deve chiudere

1. `--ignore` e `--skip-dirs` stanno sulla riga di comando: `real-stack-owncast` chiede 36.678 caratteri, oltre il limite di Windows (32.767). Il costo della lista cresce con la sua lunghezza (il fork confronta ogni voce con ogni prefisso di ogni percorso).
2. Il fork apre `.env*.example|sample|template`, che `source_files.FORBIDDEN_GLOBS` vieta a Daodan.
3. L'installazione vera (`cli()`, `runtime.node()`) non ha mai girato con i file veri; la prova è girata su Node 24, su Linux.
4. Un'installazione fallita viene ritentata a ogni scansione (tre tentativi, 12 secondi di attese) sotto `project_lock`.
5. Un'uscita o un fatto malformato solleva `KeyError` invece di diventare un buco; lo store della snapshot resta aperto durante la corsa di Node.
6. La scansione veloce riscrive `premap.json` e `technologies.json` da capo: i fatti delle fonti con comandi (Renovate, Compose, BuildKit, go-enry, i build tool) spariscono fino alla completa successiva.
7. `develop` ha cambiato `technologies.py` e la pre-mappa dopo il giro: i numeri vanno rimisurati.

## Scelte di chi scrive, da confermare con il proprietario

1. **Nome.** Il pacchetto e il repository diventano `stack-analyser-daodan` (con la s, come l'originale), dal rilascio `.3`. Il file `LICENSE` conserva la nota di Specfy.
2. **Menzioni delle variabili.** Non si tengono: `check_env` si toglie come dice la spec (2.6). Nessun modulo di Daodan legge `mentioned`.
3. **File vietati.** Daodan passa al fork, nel perimetro, i file che `is_forbidden` vieta. Il fork quindi non apre più i `.env` di esempio e la prova di tipo `env` non compare più.
4. **Test con il riconoscimento vero.** Girano dove c'è il rilascio, cioè nell'immagine dei test su Modal (`DAODAN_STACK_ANALYSER`); in locale si saltano con il motivo. È la regola di AGENTS.md sugli strumenti veri.
5. **Segni conservati.** Un segno di una fonte che non ha girato resta, con la scansione da cui viene, finché il suo file esiste sul disco; se il file non c'è più, il segno si toglie.
6. **Servizi generici in più** (`azure`, `aws`, `google`, `gcp`, `firebase`…): restano come li dà il fork; il giro li riporta fra i servizi «in più».
7. **La tabella di supporto** perde la colonna dei segni per tipo e dice se il fork ha una regola per la voce.

## Global Constraints

- **Regola invalicabile.** Il fork legge file e non esegue nulla del progetto; la prova su Modal passa con l'installazione vera e con il Node di Daodan.
- **Un solo riconoscitore.** Dopo il Task B4 nessun modulo sotto `daodan/` confronta nomi di pacchetti, file o variabili con segni del registro. `registry_hosts.py` resta l'unica lettura di Daodan (2.4).
- **Forma di `technologies.json`.** Restano `schema`, `technologies`, `mentioned`, `units`, `modules`, `configured_services`, `checkers`, `gaps` e, di ogni segno, `sign`, `value`, `path`, `line`, `strength`. Si aggiungono a ogni segno `source` e `scan`. I consumatori provano solo `sign == "package"` e `strength`: un'immagine, un'azione e una risorsa Terraform restano `sign: "package"`, come oggi; `file` e `source` restano tali; le prove `extension` non escono.
- **ID stabili**, con le rinomine del porting (`react-email` → `reactemail`, `kafka` → `apache_kafka`, `vault` → `hashicorp_vault`).
- **Riuso**: `engine_tools`, `indexers.runtime.node`, `source_files.is_forbidden`, `snapshot_store`, `registry_hosts.check_hosts`. Nessuna espressione regolare su sorgenti; `tests/test_codebase_map_patterns.py` non concede `re` a un file nuovo.
- **Errori come buchi**: nessun errore del fork o della traduzione ferma il passo; diventa un controllore `failed` e un buco con la causa, e i segni di prima restano.
- **Nel fork**: nessun concetto di Daodan nel codice (il nome del pacchetto non è codice); `reason`, `dependencies.detect`, `tech.detectInFileList` invariati; `npx vitest run --coverage.enabled=false`; mai `npm install`/`npm ci` nel repository.
- **Modal e pubblicazioni**: ogni giro su Modal, ogni push, tag, rilascio e la rinomina del repository si fanno solo dopo la conferma del proprietario, e li lancia chi coordina.
- Commit nello stile di ciascun repository (fork: `feat: …` in inglese; Daodan: prefisso e frase in italiano).

## Review Focus

1. **Dopo una modifica spariscono tecnologie.** Scansione completa, poi modifica di un file e scansione veloce: le tecnologie che venivano da Renovate o da un build tool devono restare, con la scansione da cui vengono. Test: B3, `test_a_fast_scan_keeps_the_signs_of_the_sources_it_did_not_run`.
2. **Il fork non parte.** Senza rete al primo uso, senza disco, Node non installabile: il passo finisce, conserva i risultati e scrive il buco; non ritenta a ogni scansione. Test: B1, `test_an_install_that_failed_is_not_tried_again_in_the_same_process`; B3, `test_without_the_tool_the_previous_signs_stay_and_a_gap_says_why`.
3. **Un progetto grosso su Windows.** 760 percorsi esclusi: il perimetro viaggia in un file. Test: A1, `reads a perimeter of five thousand paths`; B1, `test_the_perimeter_reaches_the_fork_in_a_file`.
4. **Un file vietato viene aperto.** `.env.example` in una cartella viva: deve stare nel perimetro. Test: B2, `test_a_forbidden_file_is_in_the_perimeter`; e sul rilascio vero la prova di B6.
5. **Un segno conservato su un file cancellato.** Deve sparire con il file. Test: B3, `test_a_kept_sign_leaves_with_its_file`.

---

## Parte A — il fork

### Task A1: Il perimetro da un file

**Files:**
- Modify: `src/cli.ts`, `src/provider/fs.ts`, `README.md`
- Test: `src/cli.test.ts`, `src/provider/fs.test.ts`

**Interfaces:**
- Produces: l'opzione `--perimeter <FILE>`: un JSON UTF-8 `{"skipDirs": [nomi], "ignore": [percorsi]}`; ciascuna chiave è facoltativa e vale come l'opzione omonima. Non si usa insieme a `--skip-dirs` o `--ignore` (codice 1, con il messaggio). Le stesse regole di validità delle due opzioni; un file che manca o non è quel JSON è un errore che lo nomina.

- [ ] **Step 1: test che falliscono**

`src/cli.test.ts`: `gives the same output from --perimeter as from --skip-dirs and --ignore`; `exits with 1 when --perimeter is given with --ignore`; `exits with 1 and writes nothing when the perimeter file is not the expected JSON`. `src/provider/fs.test.ts`: `reads a perimeter of five thousand paths` (5.000 voci `ignore`, un albero di 200 file: sotto 2 secondi).

- [ ] **Step 2: implementare**

In `FSProvider.allowed` le regole stringa si normalizzano una volta e si cercano in un `Set`; le espressioni regolari restano come sono.

- [ ] **Step 3: suite e commit**

Run: `npx vitest run --coverage.enabled=false --maxWorkers=4` e `npx tsc --noEmit`.
Commit: `feat: read the perimeter from a file`.

### Task A2: Il catalogo

**Files:**
- Modify: `src/cli.ts`, `README.md`
- Create: `src/catalogue.ts`, `src/catalogue.test.ts`

**Interfaces:**
- Produces: `node dist/cli.mjs --catalogue <FILE>` scrive, senza analizzare nulla, un array JSON ordinato per `tech`: `{tech, name, type, hosts: [..], dependencies: [{type, name} | {type, pattern}], files: [..] | {pattern}, dotenv: [..], extensions: [..]}`, con le chiavi assenti omesse. `pattern` è la sorgente dell'espressione. Con `--catalogue` l'argomento del progetto non serve.

- [ ] **Step 1: test che falliscono**

`src/catalogue.test.ts`: `lists every registered rule once`; `writes a pattern as its source`; `spring-mvc lists the Spring web starter`; in `src/cli.test.ts`: `gives the same catalogue from the bundle as from the modules`.

- [ ] **Step 2: implementare, suite, commit**

Commit: `feat: write the catalogue of rules`.

### Task A3: Il nome e il rilascio `.3`

**Files:**
- Modify: `package.json`, `package-lock.json` (a mano: nome e versione nei campi di radice), `README.md`, `benchmarks/verify-package.mjs` (il nome dell'archivio), `benchmarks/README.md`

**Interfaces:**
- Produces, per la Parte B: il rilascio `v1.27.6-daodan.3`, l'URL dell'asset e il suo sha256; `package/dist/cli.mjs` con `--perimeter` e `--catalogue`.

`package.json`: `"name": "stack-analyser-daodan"` (scelta 1), `"version": "1.27.6-daodan.3"`, `"bin"` verso `./dist/cli.mjs`. `verify-package.mjs` prova anche `--catalogue` e `--perimeter` sul pacchetto scompattato.

- [ ] **Step 1**: modifiche, `npm run build`, suite, `node benchmarks/verify-package.mjs` (lo lancia chi coordina).
- [ ] **Step 2**: commit `chore(release): 1.27.6-daodan.3 as stack-analyser-daodan`.
- [ ] **Step 3 (chi coordina, dopo la conferma del proprietario)**: rinomina del repository (`gh repo rename`), aggiornamento del remoto locale, tag, push, `gh release create`, verifica dello sha256 dell'asset scaricato.

---

## Parte B — Daodan

### Task B1: Lo strumento sul rilascio `.3`

**Files:**
- Modify: `daodan/core/stack_analyser.py`, `daodan/core/engine_tools.py`, `tests/modal_pytest.py`, `benchmarks/project-model/modal_stack_fork.py` (solo i valori fissati)
- Test: `tests/test_codebase_map_stack_analyser.py`, `tests/fake_stack_analyser.py`

**Interfaces:**
- Consumes: il rilascio di A3.
- Produces:
  - `run(project: Path, *, declarations: list[dict] = (), skip_dirs: tuple[str, ...] = (), ignore: tuple[str, ...] = ()) -> dict`: perimetro e dichiarazioni viaggiano in file della cartella temporanea (`--perimeter`, `--declarations`); `skip_dirs` è sempre passato.
  - `catalogue() -> list[dict]`: l'uscita di `--catalogue`.
  - `cli()` e `node()` ricordano per il processo un'installazione fallita: la seconda chiamata dà lo stesso `Gap` senza riprovare.
  - `engine_tools.download` ritenta anche su `http.client.HTTPException`.
  - Ogni errore di `shared_engine_dir()` e `node_environment()` dentro `run`/`catalogue` è un `Gap`.

- [ ] **Step 1: test che falliscono**

`test_the_perimeter_reaches_the_fork_in_a_file` (10.000 percorsi: nessun argomento della riga di comando supera 300 caratteri); `test_an_install_that_failed_is_not_tried_again_in_the_same_process`; `test_a_download_cut_off_is_tried_again`; `test_the_catalogue_is_what_the_fork_writes`; `test_a_cache_folder_that_cannot_be_used_is_a_gap`. I test dei valori fissati passano al `.3`.

- [ ] **Step 2: implementare; Step 3: i tre file di test in locale; commit** `feat: lo strumento passa il perimetro in un file e legge il catalogo del rilascio .3`.

### Task B2: La traduzione nel prodotto

**Files:**
- Create: `daodan/core/stack_recognition.py`, `tests/test_codebase_map_stack_recognition.py`, `tests/fixtures/stack/py-fastapi-compose.payload.json`
- Modify: `benchmarks/project-model/tools/fork_stack.py` (importa la traduzione dal prodotto e tiene solo le misure), `benchmarks/project-model/test_fork_stack.py`

**Interfaces:**
- Consumes: `stack_analyser.run` (B1); da `service_registry`: `service_site`, `_split_declared_in`, `_is_excluded`, `entry_category`; `registry_hosts.check_hosts`; `source_files.is_forbidden`; `snapshot_store.open_snapshot`; `registry_build.ECOSYSTEMS`.
- Produces: `stack_recognition.run(manifest: Path, registry: dict | None = None, facts: dict | None = None) -> dict` con `{"found", "checkers", "gaps", "ran"}`: la forma di `service_registry.run`, più `ran`, le etichette delle fonti i cui segni questa corsa ha prodotto (`stack-analyser`, `registry_hosts`, e le fonti della pre-mappa con stato `ran`).

Dal benchmark si spostano `declarations`, `perimeter`, `_signs`, `found`, `recognize` (che diventa `run`), con i loro test. Cambia:
- **Segni.** `sign` è `package` per le prove `package`, `image`, `action`, `terraform`; `file`, `source`, `env` restano; ogni segno ha `source`. `scan` lo mette B3.
- **Perimetro.** `ignore` contiene anche i file che `is_forbidden` vieta, trovati elencando le cartelle vive. I nomi con la virgola non sono più un caso a parte. Un nome di cartella con `/` o `\`, e un percorso con lettera di disco o `..`, non entrano nel perimetro e danno un buco `perimeter_entry_left_out`.
- **Forma.** Una prova o un fatto senza le chiavi attese non solleva: la prova si scarta e si conta (`evidence_malformed`), il fatto dà `declaration_not_sent`.
- **Store.** Lo store della snapshot si chiude prima di lanciare il fork e si riapre per le menzioni di host.
- **Host.** `check_hosts` riceve le voci del registro come oggi (B5 cambia da dove vengono gli host).

- [ ] **Step 1: spostare i test e aggiungere quelli che falliscono**

`test_a_forbidden_file_is_in_the_perimeter`; `test_an_image_an_action_and_a_terraform_resource_are_package_signs`; `test_a_malformed_evidence_item_is_counted_not_raised`; `test_a_perimeter_entry_the_fork_would_refuse_is_left_out_with_a_gap`; `test_the_store_is_closed_while_the_fork_runs`; `test_ran_names_the_sources_of_this_run`.

- [ ] **Step 2: implementare; Step 3: test in locale** (`tests/test_codebase_map_stack_recognition.py`, `benchmarks/project-model/test_fork_stack.py`); commit `feat: la traduzione fra la pre-mappa e stack-analyser entra nel prodotto`.

### Task B3: La regola delle fonti

**Files:**
- Modify: `daodan/core/technologies.py`
- Test: `tests/test_codebase_map_stack_sources.py` (nuovo)

**Interfaces:**
- Consumes: `stack_recognition.run` (B2), sostituito nei test da una funzione che restituisce `found`, `gaps`, `ran` scritti a mano.
- Produces: `technologies.merge(found: list[dict], ran: set[str], previous: dict | None, scan: str, exists) -> tuple[list[dict], list[dict]]`: le voci con i segni uniti e i buchi; e in `derive` il suo uso.

Regole:
- `scan` è l'`inputs_digest` della pre-mappa di questa scansione. Ogni segno prodotto ora lo porta.
- Una fonte è «eseguita» se il suo nome (l'etichetta fino a `@`) è in `ran`. Di una fonte eseguita valgono solo i segni di ora.
- Dal record precedente (`technologies` e `mentioned`) si conservano i segni la cui fonte non è eseguita, con il loro `scan`, se `exists(path)` è vero. Un record precedente di un'altra versione dello schema dei segni (senza `source`) non conserva nulla.
- Una voce esiste finché ha un segno. L'anagrafica di una voce conservata viene dal registro di ora.
- Quando qualcosa è conservato, un buco `{"kind": "signs_kept", "sources": [...], "scans": [...]}`.
- `_inputs` comprende `stack_analyser.VERSION` e `SHA256`; `MATCHER_VERSION` passa a 4. `_read` considera fresco il record come oggi.

- [ ] **Step 1: test che falliscono**

`test_a_fast_scan_keeps_the_signs_of_the_sources_it_did_not_run` (completa con `renovate@…` e `stack-analyser`; veloce con `ran = {"stack-analyser", "requirements"}`: i segni di `renovate` restano con il vecchio `scan`, quelli di `stack-analyser` sono i nuovi); `test_a_source_that_ran_replaces_its_signs` (un pacchetto tolto da un manifest sparisce); `test_a_technology_stays_while_it_has_a_sign`; `test_a_kept_sign_leaves_with_its_file`; `test_without_the_tool_the_previous_signs_stay_and_a_gap_says_why` (`ran` senza `stack-analyser`, controllore `failed`); `test_a_record_of_the_old_shape_keeps_nothing`; `test_a_new_release_makes_the_record_stale`.

- [ ] **Step 2: implementare `merge`; Step 3: test; commit** `feat: una scansione sostituisce i segni delle fonti che ha eseguito e conserva gli altri`.

### Task B4: Il passaggio e le rimozioni

**Files:**
- Modify: `daodan/core/technologies.py`, `daodan/core/service_registry.py`, `daodan/core/registry_build.py` (toglie l'import di `stack_source`), `tests/conftest.py`
- Delete: `daodan/core/stack_source.py`, `daodan/core/specfy_rules.mjs`, `tests/specfy_rules.test.mjs`, `benchmarks/project-model/tools/specfy_daodan.py`, `benchmarks/project-model/replay_registry_coverage.py`, `benchmarks/project-model/replay_stack_packages.py`, `benchmarks/project-model/tools/daodan_registry.py` e i loro test
- Modify (test): `tests/test_codebase_map_service_registry.py`, `tests/test_corpus_backend_rules.py`, `tests/test_corpus_docker_images.py`, `tests/test_corpus_service_rules.py`, `tests/test_corpus_system_rules.py`, `tests/test_corpus_web_rules.py`, `tests/test_registry_hosts.py`, `tests/test_codebase_map_stack_rationalized.py`, `tests/test_daodan_package.py`, e i test che passano da `technologies.ensure` (`premap_packages`, `stack_compose`, `flows`, `mcp`, `app`, `visual`, `pipeline`)

**Interfaces:**
- Consumes: B2, B3.
- Produces: `technologies.derive` chiama `stack_recognition.run`; `service_registry` conserva `load`, `mark_file`, `entry_category`, `step1_packages`, `package_key`, `service_site`, `_is_excluded`, `_split_declared_in`, `Project`, `REGISTRY`; non ha più `check_packages`, `check_files`, `check_env`, `CHECKERS`, `run`, `recognize`.

`source_files.STACK_SOURCE_LANGUAGES` resta: è ciò che fa entrare nella snapshot i file `.swift`, `.ex`, `.exs`, `.php`, che il fork legge da solo.

Test:
- `tests/conftest.py` offre `real_stack`: con `DAODAN_STACK_ANALYSER` nell'ambiente sostituisce `stack_analyser.cli` e `node` con quelli dell'immagine; senza, salta il test con il motivo «il riconoscimento vero gira dove c'è il rilascio (tests/modal_pytest.py)» (scelta 4).
- I test che affermano una tecnologia riconosciuta da un progetto (i `test_corpus_*`, `RecognizeTests`, quelli indiretti) usano `real_stack` e le loro attese restano, con gli ID del fork.
- I test dei controllori (`CheckerTests`, i casi parametrizzati di `check_packages`/`check_files`) si tolgono: per ognuno si cerca il caso equivalente nei test del fork (`src/rules/packageIdentities.test.ts`, `files.test.ts`); quelli che mancano si elencano nel rapporto del task, e chi coordina decide se portarli nel fork.
- I test che costruiscono un record a mano non cambiano.

- [ ] **Step 1**: `conftest.py` e i test adattati; **Step 2**: il cambio in `derive` e le rimozioni; **Step 3**: `python -B -m pytest -q -p no:cacheprovider tests` in locale (nessun fallimento; i salti con il motivo); **Step 4 (chi coordina, dopo conferma)**: la suite su Modal, dove `real_stack` è attivo; commit `feat: lo stack riconosce solo attraverso stack-analyser`.

### Task B5: Il registro come anagrafica

**Files:**
- Modify: `daodan/core/registry_build.py`, `daodan/core/registry_hosts.py`, `daodan/core/support_table.py`, `daodan/data/service-registry.json`, `daodan/data/registry-additions.json`, `daodan/data/REGISTRY-NOTICES.md`, `docs/plugins/codebase-map-supporto.md` (generato)
- Test: `tests/test_codebase_map_service_registry.py`, `tests/test_registry_hosts.py`, `tests/test_codebase_map_support_table.py`

**Interfaces:**
- Consumes: `stack_analyser.catalogue()` (B1).
- Produces: `service-registry.json` con, per voce, `id, name, kind, type, site, mark, from, category?, hosts?` e senza `signs`; `versions["stack-analyser"]` uguale a `stack_analyser.VERSION`; `registry_hosts.check_hosts` legge `entry["hosts"]`.

- `build` prende le regole da `stack_analyser.catalogue()` al posto del pacchetto npm e di `_COLLECT`, che si tolgono. `hosts` viene dal catalogo.
- La `category` curata resta dalle aggiunte; per un ID senza categoria vale una tabella tipologia → categoria (`CATEGORY_OF_TYPE`), completa per ogni `type` del catalogo: un test lo verifica.
- Le aggiunte perdono `signs` e `wrong_signs`; `check` rifiuta un record che li ha. Si tolgono i comandi `derive`, `verify-additions`, `model-input`, `accept` e il loro codice.
- Un ID che il fork riconosce e il registro non ha non deve più esistere: `test_every_rule_of_the_release_has_a_registry_entry`.
- La tabella di supporto (scelta 7) si rigenera.

- [ ] **Step 1: test; Step 2: codice; Step 3 (chi coordina)**: `registry_build build` con il rilascio vero, che scarica anche Simple Icons e CNCF; **Step 4**: test, tabella rigenerata, commit `feat: il registro è l'anagrafica, generata dal catalogo di stack-analyser`.

### Task B6: Le prove vere

**Files:**
- Modify: `tests/test_codebase_map_host_programs.py`, `tests/modal_pytest.py`, `benchmarks/project-model/modal_stack.py`, `benchmarks/project-model/README.md`, `benchmarks/project-model/results/daodan_stack.json`
- Delete: `benchmarks/project-model/modal_stack_fork.py`, le misure del confronto in `tools/fork_stack.py` e i loro test, `accepted-losses.json`

- La prova «nulla viene eseguito» chiama il `cli()` vero (con `shared_engine_dir` in una cartella temporanea) e il Node di Daodan (`runtime.node`), e ha un vettore in più: un `.env.example` in una cartella viva, che il fork non deve aprire. Il controllo è sul perimetro passato e sull'assenza di prove `env`.
- `modal_stack.py` misura il prodotto: l'immagine ha Node 22 e il rilascio; per fixture registra anche il tempo della scansione veloce, il numero di dichiarazioni e la lunghezza del perimetro.
- Il confronto con il registro non esiste più nel codice: il README confronta il giro nuovo con l'ultimo giro del piano 2, che resta nei risultati committati.

- [ ] **Step 1**: codice e test locali; **Step 2 (chi coordina, dopo conferma)**: la prova su Modal; il giro sul corpus; **Step 3**: la sezione del README con parametri, risultati, «Non misurato» e verdetto sulla «Verifica»; commit.

### Task B7: I documenti

**Files:**
- Modify: `docs/specs/2026-11-15-pipeline-di-analisi.md` (la riga «Stack» della tabella; il punto che dice «pochi millisecondi»; «Stack. Applicato»), `docs/plugins/codebase-map.md`, `README.md` (il paragrafo sullo stack e le «regole in più»), `plugins/codebase-map/skills/map/references/premap.md` (la riga `services`), `daodan/core/technologies.py` e `daodan/core/pipeline/__init__.py` (le docstring), `docs/specs/2026-11-21-stack-dal-fork.md` (lo «Stato»: applicata, con le scelte confermate)

Ogni frase dice ciò che il codice fa dopo B4–B5, con i tempi misurati in B6. Nessun riepilogo.

- [ ] **Step 1**: modifiche; **Step 2**: `git grep` di `check_packages`, `specfy_rules`, `stack_source`, `pochi millisecondi`, `segni del registro` fuori da `docs/plans` e `docs/reviews`: nessun riferimento rimasto al comportamento di prima; commit `docs: lo stack dal fork, com'è dopo il passaggio`.
