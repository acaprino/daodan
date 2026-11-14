# Piano: il grafo del codice dall'indice del progetto

**Stato:** approvato il 14 novembre 2026; risposte del proprietario nella sezione 6.
C e C++ aggiunti il 14 novembre 2026 su richiesta del proprietario: task 10.
Fogli di stile e loro dialetti aggiunti il 14 novembre 2026 su richiesta del proprietario: task 11.

> **Per chi esegue:** un task alla volta, nell'ordine. Si segnano solo i passi verificati. Ogni task lascia il prodotto funzionante e non peggiore sulle misure indicate.

**Obiettivo:** il grafo del codice del prodotto nasce dall'indice SCIP di tutto il progetto, letto per intero. Le domande per posizione restano solo per le richieste mirate.

**Funzionamento:**
- Un indicizzatore per linguaggio scrive l'indice di tutto il progetto in uno specchio.
- La parte comune (`code_graph.py`) legge tutto l'indice e segue le catene che l'indice afferma.
- Un adattatore per indicizzatore (`indexers/<lingua>.py`) dichiara ciò che quel motore scrive a modo suo.
- Il risultato entra nello store degli archi con fonte, catena, incertezza, buchi ed esterni.
- La vista degli archi resta l'unico punto da cui leggono i consumatori, con una sola fonte per riferimento.

**Tecnologie** (versioni misurate il 13 novembre 2026): Python 3, libreria standard più i pacchetti di parsing dello snapshot; scip-go v0.2.9 con Go 1.27.3; rust-analyzer 2026-11-09 con Rust 1.99.1; scip-typescript 0.5.2 e scip-python 0.6.8 su Node 22.23.4; scip-java 0.14.2 per Java e Kotlin su Temurin 17, con Maven e Gradle portati da Daodan (task 9).

**Spec:**
- `docs/specs/2026-11-08-risoluzione-chiamate-motore.md` resta. Cambiano i requisiti 5, 11, 12 (Node), 18 e 20: il task 6 li riscrive come revisione della stessa spec.
- `docs/specs/2026-11-12-passo-dinamico.md` fornisce il container.
- `docs/specs/2026-11-12-mappa-del-sistema.md` usa archi, buchi ed esterni.

**Misure di partenza:** `benchmarks/inference-audit/README.md`, sezioni del 13 novembre 2026.

## Vincoli

- I test si scrivono prima del codice. Ogni task si verifica in locale in pochi secondi, con indici SCIP committati e senza indicizzatori.
- Nessun codice del progetto gira sull'host. scip-java con Maven o Gradle e i build script di Rust girano solo nel container del passo dinamico.
- Daodan scarica indicizzatori, runtime e dipendenze nella cartella condivisa, con checksum e una riga di log, senza domande. Nel progetto non scrive nulla: lavora in uno specchio (requisito 22).
- Nessun filtro silenzioso. Ogni chiamata e lettura dello snapshot finisce in un arco o in un buco con la sua classe.
- Modal serve solo a confermare: una volta per linguaggio, con il codice del plugin verificato per hash. Un run locale pesante parte solo dopo aver chiesto, un processo alla volta.
- Nessun bump di versione. Commit solo su richiesta, su main. Documenti in italiano, al presente.
- Comando dei test: `python -B -m pytest -q -p no:cacheprovider tests/<file>`.

## 1. Dove vive il codice, cosa resta e cosa si toglie

Percorsi relativi a plugins/codebase-map/skills/map/scripts/ salvo dove indicato.

**Nuovo nel plugin**
- `code_graph.py`, da `benchmarks/inference-audit/scip_graph.py`: la parte comune. `Index`, `Snapshot`, `Traversal`, `build`, `report`, `module_runs`, `measured`.
- `indexers/{go,rust,typescript,python,java,kotlin}.py`, da `adapters/`: `index` (installa ed esegue con le funzioni del prodotto) e `hops`; dove servono anche `missing`, `same_range`, `classify`, `static`, `refine`. La cartella si chiama `indexers/` perché nel plugin «adattatore» indica già `languages/*.py`.

**`resolve_edges.py`, cosa resta**
- I motori per posizione, per le richieste mirate e per i linguaggi senza indicizzatore: `JediEngine` :245, `LspEngine` :503 con i derivati, `KotlinEngine` :2055.
- La graduazione che la parte comune già usa: `Location` :109, `callee_column` :2422, `symbol_table` :2470, `inventory_files` :2515, `grade` :2520, `verify_sources` :2760.
- Toolchain e ambienti: `go_toolchain` :1096, `rust_toolchain` :1121, `java_runtime` :2011, `npm_modules` :976, `python_environment` :3624; poi `dependency_digests` :2991.
- Il passaggio staccato e il suo stato: `ensure_edges` :4049, `edge_state` :3748, `pass_state` :3715, `stop_pass` :4119, `reset_pass` :4100; l'I/O dello store.

**`resolve_edges.py`, cosa si toglie**
- `ScipEngine` :2272, superato da `code_graph.Index`.
- I contatori di risolvibilità, :2645-:2760.
- Del passaggio completo: popolazione, `stride`, rango dei file :3048, pubblicazione ogni 30 s :2971.

**Gli altri**
- `edge_view.py`: unico lettore dello store, con una fonte per riferimento. Legge chiamate e letture; oggi legge solo `kind='call'` (:234).
- `resolution.py`, `semantic_store._Resolver`, `semantic_index`: invariati. Sono il passo statico e la base per ogni riferimento senza risposta dallo store. Restano l'unica fonte per C#, SQL e PL/SQL e per un linguaggio senza indicizzatore.
- Consumatori: `store_graph`, `store_consumers`, `modules` e `semantic_map` leggono `effective_references` (`semantic_store.install_edge_view` :982). `flows`, `map_slice` e `scope_planner` leggono `load_edge_view`. `usage_finder` non legge archi: usa grep e il grafo degli import.
- Eccezione da chiudere: `flows.py` :335, :435 e :769 leggono ancora `sem_references` direttamente. Passano alla vista nel task 3.

**Regola d'ordine**
1. Un linguaggio cambia fonte in un punto solo: la sua voce in `ENGINES` (`resolve_edges.py:3829`), sotto la vista.
2. Nessun linguaggio cambia fonte prima che `flows` legga solo dalla vista.
3. Così un consumatore non legge mai due fonti per lo stesso linguaggio.

## 2. Forma salvata

Lo store resta `engine-edges.sqlite` accanto al manifest, legato allo snapshot come oggi: digest, impronta del parser, versione. `EDGE_SCHEMA` passa da 4 a 5. Uno store di schema 4 si rifiuta e si rifà, come oggi uno store di un altro snapshot.

```
meta(key, value)            -- come oggi; una voce per linguaggio
edges(reference_id, file, language, kind, caller, l0, c0,
      verdict, target_id, symbol, resolver, confidence, payload)
holes(reference_id, file, language, kind, l0, c0, class, reason, resolver)
externals(symbol PRIMARY KEY, manager, package, version)
```

**`edges`**: una riga per ogni fine di un riferimento. Un riferimento a un metodo porta anche le sue implementazioni.
- `reference_id`: il riferimento dello snapshot. Nullo per un'occorrenza che lo snapshot non elenca: queste righe esistono solo se la domanda 4 dice sì.
- `kind`: `call` o `read` dallo snapshot; `unknown` dove lo snapshot non ha riferimento.
- `caller`: la dichiarazione dello snapshot che contiene il sito.
- `verdict` (colonna riusata): la classe della fine, `project-callable`, `project-value`, `external`, `namespace` o `dead-end`.
- `target_id`: la dichiarazione dello snapshot, per una fine `project-callable`.
- `symbol`: la chiave SCIP riferita.
- `resolver`: la fonte, per esempio `scip-typescript@0.5.2` o `jedi@…`; poi il registratore del passo dinamico.
- `confidence`: `confirmed`, `uncertain` oppure `observed` (passo dinamico).
- `payload`: `from` (simbolo SCIP del contenitore), `chain` (salti in ordine: `same-range`, `implementation`, `rust:module-file`, `declared:@types/react.useCallback` …), `detail` e, per un arco incerto, `uncertain {reason, candidates}`.

**`holes`**: un riferimento senza risposta, con `class` e `reason`.
- Classi dell'indice: `no-position`, `no-document`, `no-occurrence`, `dangling-local`, `undefined-project-symbol`, `cycle`, più quelle degli adattatori (`implicit-operator`).
- Di un motore per posizione: `engine-unresolved`, `not-asked`.
- Senza voce del linguaggio nello store: `no-index`.

**`externals`**: manager, pacchetto e versione di ogni simbolo esterno; Kotlin ha manager `unknown` e il percorso del package. La legge la mappa del sistema per i progetti esterni.

**Voce di linguaggio in `meta`**: `engine`, `state`, `indexer {name, version, seconds, peak_mb}`, `files {snapshot, indexed, missing: [{path, reason}]}`, `coverage` (sezione 5), `runs` (codice di uscita, errori dell'indicizzatore), `edges_removed` per motivo. Un arco che `refine` toglie si conta con il motivo e non si salva.

**Un motore per posizione scrive le stesse righe** (task 3):
- `edge-*` confermato → `edges`, `project-callable`, `confirmed`;
- `external-definition` → `edges`, `external`, pacchetto ignoto;
- `project-not-a-symbol` → `edges`, `project-value`;
- `ambiguous-target` → `edges`, `uncertain`, con i candidati;
- `unresolved` o errore → `holes`, `engine-unresolved`; non chiesto → `holes`, `not-asked`.

**Regola della vista, per ogni riferimento:**
1. La fonte sono gli archi dello store per il suo linguaggio.
2. Senza archi (un buco non è una risposta), se il lessicale ha risolto la fonte è il lessicale, `builtin-lexical`.
3. Altrimenti il riferimento è un buco.
4. Due risposte non si fondono mai. Se lessicale e store indicano dichiarazioni diverse vince lo store, e la differenza si conta in `lexical_disagreements`. In javapoet sono 25: il lessicale dà la classe, l'indice il suo costruttore.

**Bersaglio unico di `effective_references`**, con la regola di oggi (`ImplementationTests`):
1. la fine chiamabile diretta, senza `implementation` nella catena;
2. un contratto con una sola implementazione del progetto, e nessuna esterna, punta all'implementazione;
3. più fini chiamabili non danno bersaglio: vanno in `candidates`, insieme agli archi `uncertain`;
4. con sole fini esterne il riferimento è esterno; con soli valori resta non risolto, motivo `project-value`.

## 3. Come girano gli indicizzatori

- **scip-go.** Installazione: `go install` alla versione fissata, con il Go di Daodan (`go_toolchain`). Dipendenze: `go mod download` nello specchio. Codice del progetto eseguito: no.
- **rust-analyzer `scip`.** Installazione: il binario che il prodotto già scarica (`RUST_ANALYZER_RELEASE`). Dipendenze: cargo nello specchio, build script e macro procedurali spenti. Codice eseguito: no; ciò che generano diventa un buco (semver: 57 impl da `derive`).
- **scip-typescript.** Installazione: npm `--ignore-scripts` su Node fissato. Node è nuovo: oggi `npm_modules` (`resolve_edges.py:985`) e `TypeScriptEngine` (:1446) lo vogliono sul PATH. Dipendenze: `npm_modules` (`npm ci --ignore-scripts`). Codice eseguito: no.
- **scip-python.** Installazione: come sopra, su Node. Dipendenze: `python_environment`, solo wheel; il benchmark installava con uv anche da sorgenti, la differenza va misurata. Codice eseguito: no.
- **scip-java (Java, Kotlin).** Installazione: coursier fissato, dentro l'immagine del container. Dipendenze: la build Maven o Gradle. Codice eseguito: sì, solo nel container.

**Regole di esecuzione**
- Un indicizzatore alla volta, nello specchio di `MirroredEngine.build_mirror`.
- Ogni indicizzatore dichiara la memoria libera minima, dal picco misurato. scip-typescript su tududi arriva a 2.264 MB, sopra `ENGINE_MIN_FREE` (2 GB).
- Senza container Java e Kotlin sono `unavailable`. Lo stato dice la causa («la build gira solo in un container: nessun motore di container») e il rimedio, come la sezione 3 della spec del passo dinamico. La build non parte mai sull'host. Cosa fa intanto il linguaggio lo dice la domanda 1.
- Un indicizzatore che fallisce lascia `failed`, con la coda dello stderr e il conteggio dei suoi `ERROR`. Uno che non si può scaricare lascia `unavailable`, con la causa.

## 4. Aggiornamento incrementale

**Cache dei documenti**, accanto a `engine-answers.sqlite` (`default_answers_path`): un file `.scip` per esecuzione e una tabella documento → (esecuzione, digest delle dipendenze, contesto). Contesto: indicizzatore e versione, toolchain, digest di lockfile e manifest, impronta del parser, versione del grafo.

**Riuso.** Un documento si riusa quando sono invariati il digest del suo file (`dependency_digests`, la regola del requisito 18) e il contesto. Un lockfile o un manifest cambiato rifà tutto il linguaggio.

**Cosa si rifà quando cambia un file, e il ripiego**
- scip-go: i pacchetti dei file da rifare, nominati uno per uno; servono nominati comunque, perché `./...` potrebbe non seguire i collegamenti dello specchio (assunto, da verificare). Ripiego: tutto il modulo.
- scip-typescript: il file cambiato e chi lo importa, anche in modo transitivo, come lista `files` del tsconfig generato. Assunto: l'indicizzatore scrive documenti solo per i file elencati. Ripiego: tutto il progetto.
- rust-analyzer: il crate del file; `module_runs` lavora già per crate. Ripiego: tutto il workspace (semver 8,7 s).
- scip-python: tutto, salvo un'opzione per un sottoinsieme (da verificare). python-semver 9,3 s.
- scip-java: il modulo della build, nel container. Ripiego: tutta la build.

**Ricostruzione del grafo**
1. Prima si ricostruisce da tutti i documenti salvati, e si misura il tempo.
2. Su tududi oggi la lettura dura 67,1 s e l'indicizzatore 55 s.
3. Se la lettura pesa quanto l'indicizzatore, si rifanno solo le fini dei simboli la cui catena tocca un documento rifatto. Per questo il memo tiene i documenti visitati.

**Mentre l'indice si rifà**
- Il linguaggio è `running`.
- Gli archi dei file cambiati sono marcati stantii nella vista, e i loro file compaiono in `gaps`.
- Un file appena cambiato si può chiedere a un motore per posizione (domanda 2).

## 5. Copertura e stato

Per ogni linguaggio: nella voce di `meta`, in `edge_view.coverage` e negli strumenti MCP. Sostituisce «risolte su risolvibili» (domanda 3).

- `files`: file dello snapshot, file indicizzati, file mancanti con il motivo.
- `sites`: chiamate e letture dello snapshot.
- `answered`: siti con almeno una fine diversa da `dead-end`, divisi per classe della fine; in `lexical` quelli con la sola risposta lessicale.
- `holes`: per classe, con fino a tre esempi.
- `uncertain`: siti con un arco incerto.
- `externals`: pacchetti e conteggi.
- `state`: `complete` quando ogni file è indicizzato, non ci sono buchi e nessuna chiamata finisce solo in un valore o in un vicolo cieco; altrimenti `lower-bound`.
- Invariante: `sites` = `answered` + `holes`. Una violazione fa fallire lo stage con l'elenco per categoria; non diventa mai un numero.
- Lo stato del passaggio resta `running`, `fresh`, `stale`, `failed`, `unavailable`, `stopped` oppure `off`. `sampled` sparisce.

## 6. Domande per il proprietario

1. **Java e Kotlin fino al container.** L'indice si fa solo con la build Maven o Gradle, che può girare solo nel container. Il container non è ancora nel prodotto: la Parte B del passo dinamico aspetta il via.
   - Consiglio: fino ad allora Java e Kotlin restano sul passo per posizione di oggi (javapoet 99,7%, klaxon 88,5%) e passano all'indice quando arriva il container.
   - Alternativa: provare l'indice senza build, sull'host, con javac più il plugin di scip-java, il classpath che Daodan già risolve e `-proc:none`. È compilare il progetto sull'host: serve il tuo sì.
   - Quale scegli?
   - **Risposta del proprietario (14 novembre 2026):** la scelta consigliata.
2. **Domande per posizione.** Dopo la lettura completa dell'indice, il passo per posizione aggiunge poco: 58 chiamate su 72.890 in tududi JavaScript, 5 in semver, 0 in chi e in tududi TypeScript.
   - Consiglio: si chiedono solo su richiesta (un file appena cambiato, un buco, un arco incerto), mai in background.
   - Va bene così?
   - **Risposta del proprietario (14 novembre 2026):** la scelta consigliata.
3. **Il numero di copertura.** Oggi Daodan riporta «risolte su risolvibili» (requisito 5).
   - Consiglio: per linguaggio, siti con risposta su siti, buchi per classe, archi incerti e lo stato `complete` oppure `lower-bound`.
   - Il vecchio numero esce dal prodotto; i benchmark lo calcolano con i loro script.
   - Sei d'accordo?
   - **Risposta del proprietario (14 novembre 2026):** la scelta consigliata.
4. **Occorrenze che lo snapshot non elenca.** L'indice ha anche riferimenti che lo snapshot non registra come chiamata o lettura. In javapoet sono 9.698 archi su 19.189: tipi nominati, `this(...)`, `super(...)`, costruttori impliciti, annotazioni.
   - Consiglio: salvarli con tipo `unknown`, senza che nessun consumatore li usi. Una misura su `edit_impact` decide poi se usarli.
   - Alternativa: contarli per classe senza salvarli.
   - Quale scegli?
   - **Risposta del proprietario (14 novembre 2026):** la scelta consigliata.

## 7. Task

Percorsi `scripts/` = plugins/codebase-map/skills/map/scripts/.

### Task 1: parte comune e adattatori nel plugin, senza cambiare comportamento

**File:**
- Si crea `scripts/code_graph.py`, senza `code_sha256` e senza la ricerca di `_SCRIPTS`.
- Si crea `scripts/indexers/` con le parti di lettura degli adattatori. `index()` e `install_commands()` restano nel benchmark fino al task 4.
- `benchmarks/inference-audit/test_scip_graph.py` diventa `tests/test_codebase_map_code_graph.py`.
- `benchmarks/inference-audit/fixtures/{ts,rust}` passano in `tests/fixtures/code-graph/`: indici di 35 KB e 4 KB.
- `lang_{java,kotlin,python}.py` e `modal_scip.py` importano dagli script del plugin, montati in `/daodan/map/scripts`. `code_sha256` resta nel benchmark e fa l'hash dei file del plugin.

- [x] **Test prima:** il test spostato importa `code_graph`; è rosso finché il modulo non esiste.
- [x] **Verifica:** `tests/test_codebase_map_code_graph.py`, in pochi secondi.
- [x] **Si cancella:** `benchmarks/inference-audit/scip_graph.py`, le parti di lettura di `adapters/`, `test_scip_graph.py`, `fixtures/`.

### Task 2: contratto e una fixture per linguaggio

**File:** `tests/fixtures/code-graph/{go,python,java,kotlin}/`. Ognuna ha i sorgenti, l'indice committato e `expected.json`. Le attese si scrivono leggendo il sorgente, mai dal grafo.

- [x] **Test prima:** ogni regola di adattatore ha almeno un caso atteso.
  - Go: `:=`, `var`, letterale di funzione, implementazioni.
  - Python: `import-binding`, `builtin`, `classmethod-cls`, `type-of-self`, `static`.
  - Java: `super.m()` statico, costanti enum con `same_range`.
  - Kotlin: `. .`, overload fra task (incerto), `implicit-operator`.
- [x] **Test prima:** un controllo d'invariante su ogni fixture. Ogni chiamata e lettura dello snapshot finisce in fini o in un buco con classe; le violazioni si elencano tutte insieme, per categoria.
- [x] Gli indici delle fixture si generano una volta con l'indicizzatore fissato, su Modal, perché Java e Kotlin richiedono la build. Il comando per rigenerarli va nella docstring del test.
- [x] **Verifica:** `tests/test_codebase_map_code_graph.py`, in pochi secondi.
- [x] **Si cancella:** nulla.

### Task 3: schema 5 dello store, una fonte per riferimento, flussi solo dalla vista

**File:**
- `resolve_edges.py`: `EDGE_SCHEMA`, `write_edge_store` :2855, `read_edge_store` :2887; diventano validi anche i riferimenti `read` e quelli nulli. Lo stage per posizione scrive righe dello schema 5, secondo la tabella della sezione 2.
- `code_graph.py`: scrive lo store da `build`.
- `edge_view.py`: aggiunge le letture (oggi solo `kind='call'`, :234) e la regola della sezione 2.
- `semantic_store.install_edge_view` (:982): aggiorna anche le letture.
- `flows.py` :335, :435 e :769: leggono dalla vista.
- `scope_planner.py` :514: `conflicts` resta solo per i linguaggi con motore per posizione.

- [x] **Test prima:** in `tests/test_codebase_map_edge_view.py`, una classe che scrive lo store dal grafo della fixture TS. Controlla, per ogni chiamata e lettura attesa: bersaglio, `resolver`, esterno con pacchetto, incerto come candidato, buco, una sola fonte.
- [x] **Test prima:** in `tests/test_codebase_map_flows.py`, un collegamento che nasce da una lettura nota solo allo store.
- [x] Restano verdi: `EdgeViewTests`, `MethodTargetTests`, `ImplementationTests`, `test_codebase_map_flows.py`, `test_codebase_map_stale_callers.py`, `test_codebase_map_edit_impact.py`. Per i linguaggi con motore per posizione il comportamento non cambia.
- [x] Un test decide se una fine «costruttore» nomina la sua classe (requisito 14) o il costruttore: sono i 25 casi di javapoet.
- [x] **Verifica:** i file di test sopra, in pochi secondi.
- [x] **Si cancella:** la lettura dello schema 4 e le letture dirette di `sem_references` in `flows.py`.

### Task 4: stage dell'indicizzatore nel passaggio

**File:**
- `resolve_edges.py`:
  - `ENGINES` (:3829) riceve una voce per indicizzatore, ma ogni linguaggio resta assegnato al suo motore di oggi;
  - download di Node alla versione fissata, con `SHASUMS256`;
  - installazione npm `--ignore-scripts` in `shared_engine_dir`;
  - `min_free` per indicizzatore e il flag `needs_container`.
- `indexers/*.py`: `index()` riscritto sulle funzioni del prodotto. Spariscono i percorsi `/opt`, `apt-get` e `shutil.copytree` al posto dello specchio.
- `lang_*.py` e `modal_scip.py`: chiamano `index()` del plugin. Le immagini Modal tengono solo il sistema di base.

- [x] **Test prima:** in `tests/test_codebase_map_resolve_edges.py`, la classe `IndexerStageTests`, con un indicizzatore finto che restituisce l'indice di una fixture. Controlla:
  - la voce del linguaggio è `fresh`, con il `resolver` giusto;
  - gli hash del progetto sono uguali prima e dopo, e lo specchio viene rimosso;
  - nel log c'è la riga d'installazione;
  - un fallimento dà `failed` con la coda dello stderr;
  - un download impossibile dà `unavailable` con la causa;
  - un checksum sbagliato viene rifiutato;
  - un linguaggio che ha bisogno del container dà `unavailable` se il container manca;
  - con la memoria sotto `min_free` lo stage non parte.
- [ ] Un test con l'indicizzatore vero in `tests/test_codebase_map_mcp_wire.py`, saltato quando lo strumento non è nella cache, come oggi.
- [x] **Verifica:** i test sopra, in pochi secondi. Un run vero su chi e semver in locale solo dopo aver chiesto, altrimenti su Modal.
- [x] **Si cancella:** `index()`, `install_commands()` e `_install()` del benchmark.

**Prima metà (14 novembre 2026): gli `index()` del plugin per Go, Rust, TypeScript e JavaScript, Python.**
- [x] `index(project_dir, work_dir, files=None)` in `indexers/{go,rust,typescript,python}.py`, sulle funzioni del prodotto: `build_mirror` (specchio rimosso dopo il run), `GoEngine.go_environment`, `RustEngine.prepare`, `npm_modules`, `python_environment`. La parte comune è `indexers/runtime.py`: Node fissato con `SHASUMS256`, pacchetti npm con `--ignore-scripts`, `MIN_FREE` per indicizzatore (512, 1.280, 2.304 e 512 MB, dai picchi misurati), niente download sotto 1 GB di disco, `unavailable` con `install` e `failed` con coda dello stderr ed `errors`.
- [x] Nello specchio è reale ogni cartella con un file Go e ogni cartella con un `Cargo.toml`: `./...` non segue i collegamenti, e `go.sum` e `Cargo.lock` finiscono in una copia.
- [x] `tests/test_codebase_map_indexers.py`: 29 test in circa 1 s, con indicizzatore e download finti. Coprono hash del progetto, specchio rimosso, riga d'installazione, `failed`, download impossibile, checksum sbagliato, memoria, disco, e il contratto letto da `code_graph.build` sulle fixture committate.
- [x] Cancellati `adapters/{go,rust,typescript,python}.py` del benchmark. `modal_scip.py` e `lang_python.py` chiamano gli `index()` del plugin e le loro immagini hanno solo il sistema di base. Un run con etichetta e `--reindex` tiene gli indici in `scip-inputs/<case>/<label>`.
- [x] Conferma su Modal con il codice del plugin, hash uguali al locale, risultati `results/scip-{chi,semver,tududi}-plugin.json` e `results/graph-python-semver-plugin-checks.json`. Conteggi, report e verifica a mano sono uguali alle conferme:
  - chi 4.847 / 20.102;
  - semver 1.073 / 3.960;
  - tududi javascript 86.225 / 182.593, typescript 41.107 / 171.821;
  - python-semver 1.289 / 3.679 / 64 buchi.

  Due differenze:
  - in chi la versione del modulo nei simboli del progetto è `.` invece del commit, perché lo specchio salta `.git`;
  - in python-semver fast-semver-rs-backend è 0.1.1, la versione dell'`uv.lock`, invece di 0.1.2: l'ambiente segue il lockfile.
- [x] I simboli del progetto hanno `.` come versione del modulo, non il commit: gli id dei nodi restano uguali da uno snapshot all'altro e nessun processo git tocca il progetto. Un test indicizza la stessa fixture da due specchi con nomi diversi e ottiene gli stessi nodi del progetto. Python segue la stessa regola: `--project-version` è sempre `_`, senza `git rev-parse`.

**Seconda metà (14 novembre 2026): gli stage degli indicizzatori nel passaggio.**
- [x] In `ENGINES` sei voci: `scip-go`, `scip-rust`, `scip-typescript` (typescript, javascript), `scip-python`, `scip-java` e `scip-kotlin`. `EngineSpec` ha due campi nuovi: `indexer`, il modulo sotto `indexers/`, e `needs_container`, vero per Java e Kotlin. `min_free` è il `MIN_FREE` del modulo, letto quando serve, altrimenti `ENGINE_MIN_FREE`.
- [x] Un linguaggio resta sul motore della prima voce che lo elenca (`ENGINE_LANGUAGES`), e il passaggio lancia per lui solo quella. Nessun linguaggio ha cambiato fonte: per spostarlo basta toglierlo dalla voce di oggi.
- [x] `index_stage` chiama `indexers.<modulo>.index()` in una cartella rimossa dopo. Costruisce il grafo con `hops`, `static`, `missing` e `refine` del modulo e lo salva con `code_graph.write_store`, che ora tiene le voci degli altri linguaggi (`kept_languages`, la stessa regola del passo per posizione). Il `resolver` è `nome@versione` dell'indicizzatore; rust-analyzer porta la release fissata e mette la riga di `--version` in `build`.
- [x] Per uno stage che `needs_container`, il motore di container lo trova lo stage. Senza motore il linguaggio è `unavailable`, con causa «the build runs only in a container: …» e rimedio, e l'indicizzatore non parte.
- [x] Test: 6 in `IndexerStageTests` (i cinque del piano e `test_the_stage_keeps_the_entries_of_the_other_languages`), con lo stage eseguito davvero nel processo del test e l'`index()` finto. `test_every_language_stays_on_the_engine_of_today` fissa linguaggio → motore.
- Contratto di `indexers/{java,kotlin}.py`, diverso dagli altri: `index()` accetta `engine=`; Kotlin chiede a `missing` e `refine` anche le compile task (`tasks(result["configs"])`), che lo stage passa.
- Restano: il test con l'indicizzatore vero in `tests/test_codebase_map_mcp_wire.py`; Node e npm da `indexers/runtime.py` a `resolve_edges.py` quando `TypeScriptEngine` e `npm_modules` useranno il Node fissato invece di quello sul PATH (requisito 12).

Su Windows (14 novembre 2026: le quattro fixture, cache condivisa in una cartella di D:, un indicizzatore alla volta):
- [x] Go: Go 1.27.3 e scip-go v0.2.9 si installano in 75 s, l'indice in 10,8 s. Rust: rust-analyzer, e Rust 1.99.1 quando rustup non è sul PATH; il primo indice di un sysroot richiede circa 95 s, il successivo 4,4 s. TypeScript e JavaScript: Node, scip-typescript e pacchetti del progetto in 46 s, l'indice in 2,3 s. I grafi sono uguali arco per arco a quelli degli indici committati, con `expected.json`, `RUST_ENDS` e `ts-ends.json` tutti verdi; il progetto resta invariato e lo specchio di junction viene rimosso.
- [x] Python: scip-python 0.6.8 non parte su Windows, perché al caricamento esegue `new RegExp(path.sep, 'g')` e con `\` dà errore. Il difetto è noto e non corretto: la issue sourcegraph/scip-python#210 è aperta dal 4 aprile 2026, la PR #211 è stata chiusa senza merge, la #224 è aperta. La 0.6.8 (22 ottobre 2026) è l'ultima release, e sul branch `scip` la riga 4 di `PythonEnvironment.ts` è uguale dal 2022.
- [x] Su Windows scip-python gira quindi nel container (`container.run_in_container`), senza rete, con l'immagine `python:3.13-slim` fissata per digest. La copia del progetto porta Node per Linux, verificato con `SHASUMS256` come quello dell'host, scip-python come l'ha installato npm sull'host e i site-packages dell'ambiente dell'host: il Python dell'immagine li aggiunge al suo percorso, e da lì Pyright li trova. Senza motore di container il linguaggio è `unavailable`, con causa e rimedio, e nulla si scarica. Sulla fixture `python`, con il motore dell'utente: 7,3 s nel container, picco 325 MB, 55 s in tutto con i download; grafo uguale arco per arco all'indice committato, 12 su 12 attesi.
- [x] rust-analyzer lascia cartelle `proc-macro-srv*` nella cartella temporanea: il run usa una cartella sua in `work_dir`, rimossa dopo. `failed` e le installazioni fallite riportano inizio e fine dell'errore, perché un crash dichiara la causa in testa.
- [x] Corretti nel prodotto, con test prima:
  - `free_memory` su Windows è il minore fra memoria fisica libera e memoria impegnabile libera (`ullAvailPageFile`). Prima, con 5,3 GB fisici liberi e 2,0 GB impegnabili, il compilatore Go si era fermato per memoria esaurita. Su Linux resta `MemAvailable`; su macOS è `None`, quindi lì nessun controllo di memoria;
  - `go install` di scip-go e di gopls lancia al massimo 4 compilatori (`-p`, `go_jobs`);
  - Go tiene la sua configurazione nella cartella condivisa (`APPDATA`, `XDG_CONFIG_HOME` o `HOME` su macOS, la variabile che legge `os.UserConfigDir`), con la telemetria spenta da `go telemetry off`, una volta. `GOTELEMETRY` non serviva: Go lo tratta come sola lettura;
  - npm e Node tengono la cache nella cartella condivisa (`npm_config_cache`, `NODE_COMPILE_CACHE`) per ogni processo che Daodan lancia: `npm_modules`, gli indicizzatori Node e gli stage del passaggio;
  - `peak_mb` è `None` quando nessun run lo misura, mai 0.
- [x] Riprova su Windows con `LOCALAPPDATA`, `APPDATA`, `USERPROFILE` e `TEMP` spostati in una cartella vuota. Go (81 s compresa l'installazione) e TypeScript (42 s) danno grafi uguali a quelli degli indici committati. Fuori dalla cartella condivisa e dalla cartella di lavoro non resta nulla; il vero `%APPDATA%\go` e il vero `%LOCALAPPDATA%\npm-cache` sono invariati.
- La radice `file://D:%5C...` che scip-typescript scrive su Windows non è un URI valido. Non ha effetto: il grafo non la legge.
- Gli indici committati delle fixture `rust` e `ts` vengono da questo PC Windows, come dice la loro radice; `go`, `python`, `java` e `kotlin` vengono da Linux. Non si rigenerano ora.

### Task 5: cambio di fonte, un linguaggio alla volta

**Ordine:**
1. Go, TypeScript e JavaScript, Rust: il confronto fra passo per posizione e indice è già misurato.
2. Python, dopo averlo misurato.
3. Java e Kotlin, secondo la domanda 1, nel task 9.

Vue e Svelte restano sul motore TypeScript per posizione: scip-typescript non legge `.vue` né `.svelte` (assunto). C#, SQL e PL/SQL restano lessicali.

- [ ] **Test prima:** un test che fissa linguaggio → fonte per ogni linguaggio, così ogni cambio è esplicito.
- [ ] **Soglia per linguaggio:** una conferma su Modal con il codice del plugin. Deve valere tutto questo:
  - conteggi uguali a `results/scip-*-confirm.json` e `results/graph-*.json`;
  - nel confronto, ogni riga «solo passo per posizione» è classificata come buco dichiarato;
  - verifica a mano almeno pari a quella del README;
  - tempo e picco annotati.
- [ ] **Cambio:** il linguaggio passa alla voce del suo indicizzatore in `ENGINES`. È una riga.
- [ ] **Si cancella:** nulla. Per quel linguaggio lo stage per posizione semplicemente non parte più.

### Task 6: copertura e stato (dopo la domanda 3)

**File:**
- `resolve_edges.py`: `edge_state` e la voce in `meta`.
- `edge_view.py`: `coverage`.
- `mcp_server.py`: descrizioni di `codebase_map_create_run`, `codebase_map_index`, `codebase_map_status`.
- `scope_planner.py` :448 e :513.
- Documenti: `docs/plugins/codebase-map.md` (sezione Risolvibilità), `docs/plugins/codebase-map-linguaggi.md`, `mcp.md`, `evidence.md`.
- Spec del motore: una revisione che riscrive i requisiti 5, 11, 12 (Node), 18 e 20.

- [ ] **Test prima:** tre casi.
  - Una fixture con un file mancante e un buco dà `lower-bound`, con i conteggi.
  - Una fixture tutta indicizzata e senza buchi dà `complete`.
  - Una violazione dell'invariante dà uno stage `failed`, con l'elenco.
- [ ] **Verifica:** `tests/test_codebase_map_resolve_edges.py`, `tests/test_codebase_map_edge_view.py`, `tests/test_codebase_map_mcp.py`.
- [ ] **Si cancella:** `ResolutionCounter` :2669, `resolution_summary` :2750, `classify_reference` :2656, `project_callee_names` :2645, `REFERENCE_CLASSES` :2666, lo stato `sampled`, e `ResolvabilityTests`, sostituiti dai test nuovi.

### Task 7: aggiornamento incrementale

**File:** `code_graph.py` (cache dei documenti, riuso, memo con i documenti visitati), `indexers/*.py` (comando per un sottoinsieme), `snapshot.py` :3310-:3322 (refresh).

- [ ] **Test prima, sulla fixture TS con un file cambiato:**
  - l'indicizzatore finto riceve solo il file cambiato e chi lo importa;
  - il grafo fuso è uguale al grafo completo della fixture cambiata, che ha un secondo indice committato;
  - con lo snapshot invariato l'indicizzatore non parte;
  - un lockfile cambiato rifà tutto.
- [ ] **Misura:** un file cambiato su chi e su tududi. Si annotano file rifatti, secondi e uguaglianza con il grafo completo.
- [ ] **Si cancella:** per i linguaggi con indicizzatore, l'uso di `engine-answers.sqlite`.

### Task 8: richieste mirate e fine del passaggio per posizione (dopo la domanda 2)

- [ ] **Test prima:** in `resolve_edges(manifest, engine, positions=…)`, una richiesta su un file cambiato, su un buco e su un arco incerto. Le sue righe:
  - riempiono solo buchi;
  - non sostituiscono mai una fine dell'indicizzatore;
  - se contraddicono un arco, la contraddizione si riporta.
- [ ] Una sola entrata: `codebase_map_index` con `targets` (percorso oppure `percorso::simbolo`).
- [ ] **Misure obbligatorie prima di cancellare:** sezione 9 (parte 10).
- [ ] **Si cancella:**
  - popolazione, `stride`, `--limit`, rango e pubblicazione del passaggio completo;
  - `ScipEngine` e l'opzione `--engine scip`;
  - le parti di `MultiLanguageTests` e `DistributionTests` sulla popolazione;
  - `benchmarks/inference-audit/modal_audit.py` e `probe.py`, che usano `--pass`. Una riga nel README lo annota; i risultati restano.

### Task 9: Java e Kotlin (dopo la domanda 1)

- [x] **Immagine:** Temurin con JDK 17, fissata per digest (`IMAGE` in `scripts/indexers/jvm.py`): 190 MB compressi, 403 MB su disco. Il motore la scarica al primo `create` e la tiene. L'immagine di rilascio di scip-java pesava 2,7 GB su disco, di cui 1,5 GB per i JDK 17, 21 e 25.
  - Cosa perde: gli altri JDK. Una build che chiede un JDK più nuovo (toolchain di Gradle, `release` di javac, versione dei file di classe) è `unavailable` con la causa (`newer_jdk`), finché non esiste un'immagine per quel JDK.
  - Non ci sono scip-java, Maven e Gradle. Daodan li scarica sull'host nella cartella condivisa, verificati, e la copia li porta nel container (`tools`, `inputs` di `run_in_container`). scip-java 0.14.2 sono i 26 jar che coursier 2.1.24 risolve, ciascuno con il suo sha256.
- [x] **Lo strumento di build lo porta Daodan:** quello che chiede il wrapper, cioè `distributionUrl` in `gradle/wrapper/gradle-wrapper.properties` o `.mvn/wrapper/maven-wrapper.properties`. Si verifica con `distributionSha256Sum`, altrimenti con il checksum pubblicato dal sito. Senza wrapper si usano Gradle 9.9.1 o Maven 3.10.0, fissati per sha256.
  - Nel container il wrapper chiama solo quello strumento: nessuna build scarica una distribuzione.
  - Un wrapper che indica un sito diverso da services.gradle.org o Maven Central è `unavailable`, e da lì non si scarica nulla. Un checksum diverso è rifiutato prima di ogni container.
  - Fuori da ogni elenco: `services.gradle.org`, `github.com` e gli host dei suoi rilasci. Un GitHub raggiungibile lascerebbe uno script di build caricare la copia del progetto.
- [x] **Due tempi:** `index()` in `scripts/indexers/{java,kotlin}.py`, sopra `container.run_in_container`.
  - Preparazione, con la rete aperta solo ai registri (`registries()`): build e `scip-java index`.
  - Esecuzione, senza rete: seconda aggregazione, `javap`, `kotlin-configs/`.
  - Escono l'indice, l'aggregazione in avanti, `javap.json` e `kotlin-configs/`.
  - Senza container il risultato è `unavailable`, con causa e rimedio; senza indice è `failed`, con la coda dell'output.
  - Registri: `container.REGISTRIES` ora comprende anche `plugins-artifacts.gradle.org`, dove il portale dei plugin di Gradle manda i download; gli indicizzatori JVM aggiungono JCenter e il Maven di Google.
  - La copia porta anche i file che Git traccia nelle cartelle con il punto, come `.mvn/`, con il bit di esecuzione che Git registra; restano fuori i file ignorati e i segreti.
  - Test: `tests/test_codebase_map_indexers_jvm.py`, 17 prove con la riga di comando finta; in `tests/test_codebase_map_container.py` 3 prove nuove per la copia e `inputs`.
- [x] **Una versione sola, 0.14.2:** confermata su Modal il 14 novembre 2026 con gli script del plugin, senza container (`benchmarks/inference-audit/adapters/jvm_here.py`).
  - javapoet: resoconto del grafo uguale a quello della 0.13.2 (3.541 nodi, 19.189 archi, buchi e pacchetti), verifica a mano 20 su 20. Cambia solo l'accordo con il lessicale: i 25 casi diventano 19 uguali e 6 diversi, per la regola del costruttore del task 3, non per l'indicizzatore. Indicizzatore 28 s, picco 733 MB. Il proxy rifiuta solo `maven.java.net`, `oss.sonatype.org` e `repository.apache.org`, che la build chiede ma non usa.
  - klaxon: ogni conteggio uguale (15.940 archi certi, 251 incerti, buchi, verifica a mano 16 su 20). Gradle 7.3 è quello del wrapper, portato da Daodan, e il proxy non rifiuta nulla. Indicizzatore 85 s, picco 1.636 MB; con l'immagine di rilascio erano 130 s e 4.050 MB.
- [x] **Con il container vero:** provato il 14 novembre 2026 sul PC del proprietario, con Kiri 0.2.0 e la CLI docker 29.9.2. `RealContainerSmokeTest` usa un container e 2 GB.
  - Fixture Java senza wrapper: Maven 3.10.0 portato da Daodan, le dipendenze da Maven Central attraverso il proxy, l'indice scritto e le 7 attese di `expected.json` tenute. 32 s, picco 346 MB.
  - La stessa fixture con `mvnw` in CRLF, senza bit di esecuzione, e `.mvn/` tracciato da Git: la copia porta `.mvn/`, il container chiama solo il Maven portato e nessuna distribuzione si scarica. 16 s.
  - Le impostazioni dell'utente restano uguali prima e dopo: PATH, configurazione e contesti di Docker, PATH dell'utente, distribuzioni WSL.
  - In Kiri restano le due immagini per digest, Temurin (438 MB) e il proxy (53 MB).
  - Ogni run lascia anche uno strato orfano in `/var/lib/kiri/layers`: è lo strato dell'immagine preparata, che Kiri 0.2.0 non cancella con `rmi -f`. La CLI non lo elenca e lo conta solo `system df`. Per Java pesa 118 MB, cioè `app/scip-java` 83, `root/.m2` 24 e `daodan/tools` 12.
- [x] **Gradle in un container vero:** fixture Kotlin, provata il 14 novembre 2026 sullo stesso PC con un limite di 4 GB.
  - Senza wrapper si usa il Gradle 9.9.1 portato da Daodan, verificato con il suo sha256. Il plugin Kotlin 2.1.0 della fixture compila con quel Gradle.
  - Le 7 attese di `expected.json` tengono sull'indice scritto, quindi la fixture non va rigenerata.
  - Tempi: 84 s; indicizzatore 63 s, picco 1.788 MB.
  - Un wrapper che indica un altro sito risulta `unavailable`: nessun container, nessuna richiesta a quel sito.
  - Lo strato orfano di questo run pesa 426 MB: `root/.gradle` 195, Gradle spacchettato 148, scip-java 83. Il disco di Kiri passa da 1,66 a 2,26 GB.
- [ ] **Strati orfani di Kiri:** da togliere per nome, con il via del proprietario. Da correggere in `container.py`: gli strumenti portati non devono finire nello strato preparato.
- [ ] **Soglia:** come nel task 5, su javapoet e klaxon, con il confronto fra passo per posizione e indice misurato.
- [ ] **Si cancella:** `JavaEngine`, `KotlinEngine` e `engines/KotlinResolver.kt`, solo se la domanda 2 esclude le richieste mirate per la JVM.

### Task 10: C e C++

**File:**
- Lettore: `scripts/languages/cfamily.py`, `_CFamilyEvidence` in `scripts/languages/semantic.py`, `scripts/languages/__init__.py`, `scripts/languages/_treesitter.py`, `scripts/snapshot.py` (`parser_profile`, `resolve_module` per `#include`).
- Indicizzatore: `scripts/indexers/clang.py`, la parte di lettura di `benchmarks/inference-audit/adapters/clang.py`.

- [x] **Test prima:** `tests/test_codebase_map_clang_reader.py` su `tests/fixtures/clang-reader/{c,cpp}`, 77 prove con le attese scritte dal sorgente:
  - dichiarazioni, con il prototipo come `contract`; export senza `static`;
  - `#include "x.h"` arriva al file del progetto, `<x.h>` è esterno;
  - chiamate e letture con la loro fine; il `static` omonimo di un altro file non è mai scelto.
- [x] **Regola per `.h`:** è C++ se il testo, commenti e stringhe esclusi, ha un namespace, una classe, un template, un'etichetta di accesso o `using namespace`; altrimenti è C.
- [x] **Verifica:** `benchmarks/inference-audit/test_clang_graph.py` gira anche sullo snapshot del prodotto. In C le fini sono uguali in 17 chiamate su 17, in C++ in 14 su 15.
  - La differenza: `new geo::Square(3.0)` si legge su `Square`, dove l'indice nomina la classe. Il sostituto lo leggeva dove inizia il tipo, dove l'indice nomina il costruttore. Decide il requisito 14 (task 3).
- [ ] **File con macro:** su zlib si leggono interi 15 file C su 66. Gli altri 51 hanno errori di sintassi da macro (`local int f(`, `uch FAR uchf`, `z_const`) e restano senza fatti semantici.
  - Togliendo sei macro di zlib i file interi diventano 39 su 66.
  - Serve una regola che legga i `#define` del progetto, non un elenco di nomi.
- [ ] **Nomi dalle intestazioni:** oggi un nome che arriva da un `#include` resta `scope-unresolved`. Serve una regola in `resolution.py`, usata da entrambi i proprietari: cerca fra gli export delle intestazioni incluse che si risolvono a un solo file, e accetta un solo bersaglio.
- [ ] **Indicizzatore nel container:** dopo il task 9, nello stesso container.
  - Immagine Ubuntu 24.04 (glibc 2.38) con CMake e gcc; scip-clang v0.4.1 fissato con sha256.
  - Database di compilazione dal configure e dalla build di CMake su una copia, con le regole di rete del task 9.
  - `indexers/clang.py`: `dedupe`, `utf8_columns`, `enclose`, `same_range`, `hops`, `refine`, `classifier`.
- [ ] **Richieste mirate per `extern "C"`:** in C++ scip-clang non scrive occorrenze per una funzione `extern "C"`. Sono 91 chiamate della libreria C in tinyxml2, più `c_helper` nella fixture. Il task 8 le chiede per posizione; senza risposta restano buchi con questa causa.
- [ ] **Soglia:** come nel task 5, su zlib e tinyxml2.
  - Conteggi uguali a `results/graph-c-zlib.json` e `results/graph-cpp-tinyxml2.json`.
  - Verifica a mano 20 su 20 su zlib e almeno 16 su 20 su tinyxml2.
  - Tempo e picco annotati.
- [ ] **Si cancella:** `SyntaxSnapshot` del benchmark, quando lo snapshot del prodotto dà i fatti semantici anche ai file di zlib e tinyxml2 che oggi non legge interi. Fino ad allora i risultati salvati dipendono da lui.

### Task 11: fogli di stile

**File:**
- Lettore: `scripts/languages/stylesheet.py` (Sass indentato come lo SCSS che l'indentazione implica), `scripts/languages/markup.py` (le regole dei blocchi `<style>` di HTML, EJS, Astro e template), `scripts/languages/sfc.py` (le regole dei blocchi `<style>` di Vue e Svelte accanto allo script), `scripts/languages/__init__.py` (`.sass`, `.pcss`, `.postcss`, la lingua `markup`), `scripts/snapshot.py` (Stylus e Pug a livello di file con il motivo, citazioni dei selettori), `scripts/doc_review.py`.
- Grafo: `benchmarks/inference-audit/adapters/css.py` e un adattatore per motore, con il suo `.js`: `css_sass` (sass-parser), `css_less` (less), `css_stylus` (stylus), `css_vue` (@vue/compiler-sfc), `css_svelte` (svelte/compiler), `css_astro` (@astrojs/compiler), `css_typescript` (TypeScript: CSS-in-JS, cva, tailwind-variants, Angular), `css_tailwind` (Tailwind 3 e 4); `css_expressions.js` per le espressioni di classe dei template; motori fissati in `css_engines.json`.

- [x] **Test prima:** `tests/test_codebase_map_stylesheet_dialects.py`, attese scritte dal sorgente: Sass indentato uguale al suo SCSS riga per riga, PostCSS come CSS, Stylus e Pug elencati con il motivo, blocchi `<style>` di Vue, Svelte, HTML, EJS e Astro, CSS moderno blocco per blocco.
- [x] **Test prima:** `benchmarks/inference-audit/test_css_graph.py` su dieci fixture (`fixtures/css*`), archi, buchi e incerti scritti a mano prima del codice: Sass, Less, Stylus, componenti, pagine, CSS-in-JS, Tailwind 4, CSS moderno, CSS Modules, Angular e tabelle di varianti.
- [x] **Regola di pagina:** un arco di classe, id, proprietà custom, keyframes, font-face o container è certo solo se un'unità del codice contiene il sito e il foglio del bersaglio: una pagina HTML/EJS con i suoi include, i fogli che linka o contiene e gli script che carica, oppure un bundle di moduli che nessuna pagina carica. Altrimenti resta, incerto, con `sheet-not-proven-loaded`.
- [ ] **Adattatori nel plugin, dopo lo store del task 3:** la parte di lettura in `scripts/indexers/css*.py`; i motori Node installati da Daodan nella sua cache, mai dal progetto.
- [ ] **Convenzioni dei framework per il caricamento:** il layout di Next.js sulle pagine del suo albero, `static/` di Sapper, `angular.json` `styles`, HtmlWebpackPlugin. Oggi i loro archi restano incerti.
- [ ] **Soglia:** su v3-admin-vite, tududi, Bulma, Bootstrap 3, hn.svelte.dev, saas-starter e styled-components-website i conteggi di `results/graph-css-<caso>-checks.json`, nessun file perso senza motivo, verifica a mano almeno 15 su 15 per caso. Giro di conferma del 14 novembre 2026: v3-admin-vite 15 su 15, tududi 20 su 20, Bootstrap 3 15 su 15, hn.svelte.dev 16 su 16, saas-starter 15 su 15, Bulma 7 su 11 (quattro attese scritte male, nessun errore del grafo); styled-components-website non misurato (`benchmarks/inference-audit/README.md`, «fogli di stile su progetti reali»).
- [ ] **Si cancella:** `adapters/css*.py` del benchmark, quando le parti di lettura sono nel plugin.

## 8. Rischi

- **Strumenti attivi.** Nessun indicizzatore è stato controllato con la regola dei motori: licenza che consente l'uso, repository non archiviato, commit e release nell'ultimo anno. Vale per scip-go, scip-typescript, scip-python, scip-java e rust-analyzer. Va fatto prima di fissarli.
- **Windows.** Tutte le misure sono su Linux (Modal). Non sono misurati:
  - scip-go compilato su Windows;
  - `rust-analyzer scip` su Windows;
  - Node su Windows;
  - lo specchio fatto di giunzioni, se Go non segue i collegamenti;
  - le fini riga CRLF.
- **Memoria.** scip-typescript su tududi arriva a 2.264 MB, e il benchmark gli concedeva `--max-old-space-size=12288`. Il container Kotlin arriva a 4.688 MB in totale.
- **Tempo della lettura.** In Python la lettura di tududi (67,1 s) pesa quanto l'indicizzatore (55 s).
- **TypeScript.** Il tsconfig generato è uno solo ed estende quello della radice: provato solo su tududi. pnpm e yarn non passano da `npm_modules`, che gestisce solo npm: i loro esterni diventano buchi.
- **Python.** Con i soli wheel alcuni pacchetti possono mancare, e i loro esterni diventano buchi.
- **Codice generato.** Le macro di Rust e i processori di annotazioni Java producono codice senza dichiarazione nell'indice: diventa buco.
- **Dal README, ancora non verificati:**
  - il pacchetto `. .` di TypeScript (968 chiamate);
  - `fireEvent.click` senza occorrenze;
  - la libreria standard Python marcata 3.11;
  - `import *` per il salto `builtin`;
  - l'overload dei simboli del JDK;
  - l'ordine compilato in Kotlin;
  - Gradle 8 e oltre, Android, Kotlin Multiplatform.
- **Risultati che cambiano per i consumatori.** Dove lessicale e indice divergono vince l'indice: `edit_impact`, `stale_callers` e i flussi possono cambiare. Il conteggio `lexical_disagreements` lo rende visibile.

## 9. Da misurare prima di cancellare il passaggio per posizione

- **Confronto per linguaggio** sulle stesse chiamate dello snapshot: uguali, diverse, solo passo per posizione, solo indice; ogni «solo passo per posizione» classificato.
  - Fatto per Go (chi: 0 solo passo per posizione), Rust (semver: 5, dichiarati), JavaScript (tududi: 58), TypeScript (tududi: 0).
  - Manca per Python (python-semver e phazly), Java (javapoet) e Kotlin (klaxon).
  - Manca per phazly TypeScript e Rust: è il progetto principale del proprietario e non è mai passato dal grafo.
- **Verifica a mano** almeno pari a quella del passo per posizione. Oggi: chi 15/15 contro 13/15; semver 15/15 contro 12/15; JavaScript 12/15 contro 7/15; TypeScript 14/15 contro 10/15.
- **Sul PC del proprietario**, dopo aver chiesto: un caso piccolo per linguaggio, con tempo, picco e spazio della cartella condivisa.
- **Incrementale:** le misure del task 7.
- **Riferimento di costo:** la conferma completa su Modal è costata circa 0,3 USD.
