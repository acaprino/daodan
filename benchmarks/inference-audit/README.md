# Benchmark: cosa danno gli indicizzatori e le seconde fonti statiche

**Stato:** In uso. Misura il solo passo statico: il grafo che Daodan legge dall'indice SCIP di un indicizzatore (step `analyze` della pipeline, `engine_pass.index_stage`) e, accanto, le seconde fonti statiche del programma intero. Un buco di questo README è un buco dopo il passo statico, non dopo l'analisi: che cosa ne chiude il passo dinamico è misurato in [`call-provenance`](../call-provenance/README.md) e riassunto in «Che cosa resta aperto dopo l'intera pipeline».

## Domanda

Per ogni linguaggio: che cosa dichiara l'indice, che cosa arriva al grafo, dove resta un buco e di che classe, e quale seconda fonte statica lo chiude senza inventare archi? Nessun modello; tutto gira su Modal.

## Parametri

| Parametro | Valore |
| --- | --- |
| casi | chi `c64ed7d6635f33a8b2feaff7dcfa55677023ac7d` (Go), semver `280ebcb6edac3aa4cdc545dbff8a26c5ac4861fe` (Rust), tududi `71da9d7b34dfd1600657e9c5ddf40420206fd263` (JavaScript, TypeScript, fogli di stile), python-semver `b6e83e3e40d3a7570386e8d694ae8011477a55c1` (Python), phazly `46c92b28` (archivio privato: Python, TypeScript, JavaScript, Rust), javapoet `b9017a9503b76e11b4ad4c1a9f050e2d29112cb0` (Java), klaxon `1173bdc568a6d339b45cf24a6a9c5c2f6847f42d` (Kotlin), zlib 1.3.1 `51b7f2abdade71cd9bb0e7a373ef2610ec6f9daf` (C), tinyxml2 11.0.0 `9148bdf719e997d1f474be6bcc7943881046dba1` (C++) |
| codice misurato | la parte comune `daodan/core/code_graph.py` (lettura dell'indice, catene, grafo, store) e un modulo per indicizzatore in `daodan/core/indexers/`, con `index(...)` e `hops(index)`. I driver di questa cartella li collegano a Modal e al volume `daodan-flow-results`, e controllano per hash che il container esegua il codice del checkout (`plugin_scripts.code_sha256`) |
| riferimenti indipendenti | `sem_references` dello snapshot, `call` e `read` |
| verifica a mano | per ogni caso, chiamate lette nel sorgente con l'attesa scritta prima di guardare il grafo (`HAND`, `HAND_CHECK` nei driver) |
| date | 13-17 novembre 2026; versioni degli indicizzatori nella sezione di ogni linguaggio |

Dal 13 novembre il prodotto è cambiato in due punti che questo benchmark non rimisura: scip-typescript è alla 0.6.2 (qui 0.5.2) e rust-analyzer gira nel container con build script e macro procedurali (qui senza). Le versioni di oggi sono in `docs/plugins/codebase-map-linguaggi.md`; i giri della pipeline intera sugli stessi casi in [`project-model`](../project-model/README.md), «Il grafo completo sul corpus».

| Script | Che cosa fa | File in `results/` |
| --- | --- | --- |
| `modal_scip.py` | chi, semver, tududi, phazly: il grafo di ogni lingua dall'indice, il confronto con il passo per posizione, la verifica a mano | `scip-<caso>.json`, `-full.json`, `-confirm.json`: tre letture successive dello stesso indice, vale `-confirm`; phazly `scip-phazly-graph.json`, `-before.json`, `-final.json`, vale `-final` |
| `modal_stage.py` | lo stage vero del prodotto contro il grafo del benchmark | `scip-{chi,semver,tududi,phazly}-stage.json`, `scip-python-semver-stage.json` |
| `lang_python.py` | python-semver | `graph-python-semver.json`, `-checks.json`, `graph-python-semver-plugin-checks.json` |
| `lang_java.py`, `lang_kotlin.py`, con `adapters/java.py`, `kotlin.py`, `jvm_here.py` | javapoet, klaxon | `graph-java-javapoet.json`, `-checks.json`; `graph-kotlin-klaxon.json` |
| `lang_clang.py`, con `adapters/clang.py`; `test_clang_graph.py` su `fixtures/c` e `fixtures/cpp` | zlib, tinyxml2 | `graph-c-zlib.json`, `graph-cpp-tinyxml2.json` e i loro `-checks.json` |
| `lang_css.py` | fogli di stile | `graph-css-<caso>-checks.json` |
| `strong_go.py`, con `adapters/go_callgraph.py` | callgraph VTA su chi | `strong-go-chi.json` |
| `strong_jvm.py`, con `adapters/kotlin_analysis.py`, `KotlinAsk.kt`, `jvm_callgraph.py`, `JvmCallGraph.java` | Kotlin Analysis API e WALA su javapoet e klaxon | `strong-jvm.json` |
| `strong_js.py`, con `adapters/ts_compiler.py`, `ts_compiler.js`, `js_jelly.py` | compilatore TypeScript e Jelly su tududi | `strong-js-tududi.json`, `-split.json` |
| `fixture_indexes.py` | gli indici committati delle fixture di `tests/fixtures/code-graph/` | — |
| `plugin_scripts.py`, `test_plugin_scripts.py`, `test_scripts_on_modal.py` | dove i driver trovano il codice del prodotto e l'hash di ciò che un container esegue | — |
| `modal_audit.py` | il passaggio del prodotto su ogni caso (`resolve_edges.py --pass`); `CASES`, `_run` e `_source` servono agli altri driver | nessuno: `audit-<caso>.json` resta sul volume |
| `clang_toolchain.py` | C e C++ con una toolchain scompattata in una cartella, senza compilatore nell'immagine | nessuno: `clang-toolchain.json` non c'è |

Ciò che i risultati citano e non sta più in questa cartella è passato nel prodotto: `scip_graph.py` è `daodan/core/code_graph.py`; gli adattatori dei fogli di stile sono `daodan/core/indexers/css*.py` con i motori fissati in `indexers/css_engines/`; le fixture e i test sono `tests/fixtures/code-graph/`, `tests/fixtures/css-graph/`, `tests/test_codebase_map_code_graph.py` e `tests/test_codebase_map_css_graph.py`.

Risultati senza sezione: `scip-{chi,semver,tududi}-plugin.json`, `scip-chi-graph.json` e `scip-tududi-graph.json` sono esecuzioni etichettate di `modal_scip.py` che nessuna sezione descrive. I grafi dell'etichetta `plugin` di tududi, che `benchmarks/connection-points` prende in ingresso, non sono nel repository: stanno sul volume Modal `daodan-flow-results`, in `inference-audit/scip-inputs/tududi/plugin/graph-<lingua>.json.gz`. La seconda fonte Python (Jedi su python-semver, `inference-audit/strong-python/semver.json` sul volume) non ha qui né script né risultato.

## Risultati validi oggi

| Linguaggio, caso | Indicizzatore | Nodi | Archi | Buchi dopo il solo indice | Verifica a mano |
| --- | --- | --- | --- | --- | --- |
| Go, chi | scip-go v0.2.9 | 4.847 | 20.102 | 309 chiamate: 266 senza occorrenza (261 builtin, 5 `err.Error`), 43 callee dinamici | 15 / 15 |
| Rust, semver | rust-analyzer 2026-11-09 | 1.073 | 3.960 | 24: 18 in un file senza documento, 5 callee dinamici, 1 senza occorrenza; 59 archi in vicolo cieco | 15 / 15 |
| JavaScript, tududi | scip-typescript 0.5.2 | 86.225 | 182.593 | 15.445 chiamate senza occorrenza, 61 su un `local` senza definizione, 208 senza posizione | 12 / 15 |
| TypeScript, tududi | scip-typescript 0.5.2 | 41.107 | 171.821 | 3.755 chiamate su un `local` senza definizione (`t`), 1.282 senza occorrenza, 98 senza posizione | 14 / 15 |
| Python, python-semver | scip-python 0.6.8 | 1.289 | 3.679 | 64; 19 chiamate mancate, 3 bersagli sbagliati | 18 / 20 |
| Python, phazly | scip-python 0.6.8 | 35.662 | 147.150 | 2.584 chiamate senza occorrenza; 528 riferimenti in file senza documento | 15 / 15 |
| TypeScript, phazly | scip-typescript 0.5.2 | 26.158 | 102.734 | 2.293 riferimenti su un `local` senza definizione | 9 / 15 |
| JavaScript, phazly | scip-typescript 0.5.2 | 889 | 2.814 | 208 riferimenti senza occorrenza | 13 / 15 |
| Java, javapoet | scip-java 0.13.2, identico con 0.14.2 | 3.541 | 19.189 | 10 letture `args.length` | 20 / 20 |
| Kotlin, klaxon | scip-java 0.14.2 | 5.223 | 16.191, di cui 251 incerti | 330 | 16 / 20 |
| C, zlib | scip-clang v0.4.1 | 1.874 | 14.137 | su 3.396 chiamate: 2.125 in file senza documento, 257 senza occorrenza | 20 / 20 |
| C++, tinyxml2 | scip-clang v0.4.1 | 2.063 | 7.978 | su 2.380 chiamate: 135 senza occorrenza, 10 in file senza documento | 16 / 20 |

- I conteggi di JavaScript e TypeScript senza posizione, e la divisione dei 1.282, vengono da `results/scip-tududi-confirm.json` (`holes_by_class`, `holes`).
- Rust e Kotlin su phazly non sono misurati (sezione phazly).
- Fogli di stile: le misure del 14 novembre sono di un codice che non c'è più; l'ultima sugli stessi casi è in [`css-parser`](../css-parser/README.md) (sezione «Fogli di stile»).
- Lo stage del prodotto dà lo stesso grafo del benchmark, store uguale riga per riga (sezione 3).

## Che cosa resta aperto dopo l'intera pipeline

Per ogni classe di buco lasciata dal passo statico: il passo successivo che la chiude, con il numero e dove è misurato. «Pipeline» sono i giri del 16 novembre 2026 in `benchmarks/project-model/results/pipeline/` (campo `steps.dynamic.languages.<lingua>`: `sites` osservati, buchi `closed`). Dopo il modello nessuna di queste classi è misurata.

| Classe di buco dopo l'indice | Quanto | Passo che la chiude | Misura |
| --- | --- | --- | --- |
| JavaScript: chiamata senza occorrenza (ricevente `any`, callee dinamico, legame ambiguo) | tududi 15.445 | passo dinamico, registro esatto | 13.677 delle 16.527 chiamate senza bersaglio (82,8%): 13.001 verso librerie, 676 verso il progetto; sorgenti 3.735 su 6.166, test 9.942 su 10.361 ([`call-provenance`](../call-provenance/README.md), sezione 1). Restano 2.850. Il denominatore è del passo per posizione, non dell'indice (sotto). Pipeline: 691, 2.329 e 2.073 buchi chiusi in tre giri (`-conferma`, `-ci-steps`, `-dotenv`). **Aperta: da approfondire:** la distanza fra i due numeri non è spiegata |
| JavaScript: stesse chiamate, seconde fonti statiche | tududi 15.429 nelle tre classi | compilatore TypeScript, Jelly (sezione 4) | compilatore: 0 bersagli del progetto, 767 + 1.455 + 121 esterni con i `@types` mancanti; Jelly solo progetto: 44 + 10 + 40 bersagli del progetto. Non chiudono la classe |
| TypeScript: `t` di `useTranslation` e `fireEvent` | tududi 3.748 e 564 | compilatore TypeScript (sezione 4) | tutti esterni con pacchetto (`i18next`, `@testing-library/dom`). Pipeline: TypeScript 777 buchi chiusi con 20.202 siti (`-ci-steps`), 2.186 con 20.204 (`-finale`) |
| TypeScript e JavaScript: funzione che arriva attraverso un contratto (prop, membro d'interfaccia, Provider di un contesto, store zustand) | tududi 13 disaccordi letti; phazly `startCheckout`, `clearError`, azioni degli slice | Jelly su tududi: 11 giuste, 2 parziali | su phazly nessuna fonte provata; dopo il passo dinamico non misurato |
| Go: valore funzione, callee dinamico, liste di implementazioni troppo larghe | chi 43 callee dinamici, 31 valori del progetto, 537 siti su interfacce | callgraph VTA (sezione 4), non nel prodotto | 42 su 43 e 26 su 31 con un bersaglio; 237 candidati scartati. Pipeline: 6 buchi chiusi con 1.344 siti (`-finale`) |
| Kotlin: overload e override fra task, operatori impliciti | klaxon 251 archi incerti, 93 chiamate implicite | Kotlin Analysis API (sezione 4), non nel prodotto | 251 su 251 certi, 93 su 93 con un bersaglio. Pipeline: 2 buchi chiusi con 1.777 siti (`-finale`) |
| Java | javapoet 10 letture `args.length` | nessuno: non sono chiamate | Pipeline: 6.021 siti, 0 buchi chiusi (`-finale`) |
| Python: valore creato da un decoratore, parametro chiamato, attributo dinamico, fixture senza tipo | python-semver 19 chiamate mancate, 64 buchi | passo dinamico, registro esatto | 16 su 16 delle chiamate senza bersaglio da nessuna fonte statica, 31 buchi su 64 ([`call-provenance`](../call-provenance/README.md), sezione 2). Pipeline: 32 buchi chiusi con 1.046 siti (`-conferma`) |
| Python su phazly: riceventi senza tipo | 2.584 chiamate senza occorrenza | passo dinamico | non misurato |
| C: file senza comando di compilazione, rami `#if` spenti, puntatori a funzione | zlib 2.125, 234 e 46 chiamate | passo dinamico (Callgrind) | Pipeline: 148 siti, 0 buchi chiusi (`-conferma`) |
| C++: funzioni C dietro `extern "C"`, argomenti di macro | tinyxml2 91 e 13 chiamate | passo dinamico (Callgrind) | Pipeline: 26 buchi chiusi con 552 siti (`-conferma`), 31 in `-giro-2` |
| Rust: file senza documento, callee dinamici | semver 18 e 5 | passo dinamico (Callgrind) | Pipeline: 558 siti, 0 buchi chiusi (`-conferma`) |
| Fogli di stile: classe costruita a runtime (`parameter`, `call`, `property`, `template`) | tududi 68, 67, 28 e 1 | esplorazione dell'app avviata | non misurato |

I numeri della pipeline che il README di `project-model` non riporta (buchi chiusi di chi, javapoet, klaxon, python-semver, zlib, semver e dei giri `-ci-steps` e `-dotenv` di tududi) sono letti dai file JSON dei giri.

### I conteggi delle chiamate senza bersaglio su tududi JavaScript

Quattro numeri vicini, da quattro conteggi diversi sullo stesso commit:

- **15.445**: chiamate dello snapshot (72.890) senza alcuna occorrenza nell'indice di scip-typescript (`results/scip-tududi-confirm.json`, `holes_by_class`, `no-occurrence call`). Per motivo: ricevente `any` 9.166, callee dinamico 3.698, legame ambiguo 2.565, nome non legato 16. Le prime tre classi sommano 15.429.
- **15.104**: di quelle 15.445, le chiamate a cui nemmeno il passo per posizione dava una risposta (stesso file, cella `A none | B no-occurrence`); delle altre, 311 erano esterne per il passo e 30 mai chieste.
- **15.077**: chiamate con verdetto `unresolved` del passo per posizione, su 72.842 chiamate, prima della correzione dell'estrattore (`benchmarks/call-provenance/results/environment/engine-count-tududi.json`).
- **16.527**: le stesse 15.077 più 1.082 `project-not-a-symbol` e 368 `ambiguous-target`: tutte le chiamate che il passo per posizione lasciava senza bersaglio (`UNRESOLVED` in `benchmarks/call-provenance/dynamic_join.py`). È il denominatore del registro esatto.

**Aperta: da approfondire.** Il registro esatto è stato unito ai verdetti del passo per posizione del 12 novembre, non ai buchi dell'indice: quante delle 15.445 chiuda non è misurato in questo benchmark né in `call-provenance`.

## 1. Che cosa dà l'indice, per linguaggio

L'indice di un indicizzatore di progetto intero si legge tutto, ogni documento, occorrenza e simbolo, e diventa il grafo del codice.

- **Arco.** Dalla definizione più interna che contiene l'occorrenza (il file, fuori da ogni definizione) a ogni fine del simbolo riferito, lungo ciò che l'indice afferma e i salti dell'adattatore, senza limite di passi e con protezione dai cicli. Il tipo (`call`, `read`) è quello del riferimento dello snapshot nella stessa posizione, `unknown` dove lo snapshot non ne ha uno.
- **Che cosa si segue.** Una definizione che condivide il suo intervallo con un riferimento a un altro simbolo (proprietà abbreviata, destrutturazione, `module.exports = { f }`); una definizione la cui istruzione lega il nome a un altro nome che l'indice risolve (`a = b`, `k: b.c`, `{ k: nome } = …`) o a una funzione dello snapshot; le implementazioni dichiarate (`is_implementation`) di un membro, mai di un tipo, tranne nei siti a dispatch statico che l'adattatore dichiara (`static`).
- **Fine.** Una funzione, un metodo o una classe che lo snapshot dichiara (`project-callable`), un valore del progetto (parametro, locale, campo, risultato di chiamata), un esterno con pacchetto e versione, o un vicolo cieco. Ogni arco porta la sua catena: salti e tipo di salto.
- **Buco.** Un riferimento dello snapshot senza occorrenza nell'indice, o che finisce solo in un vicolo cieco, con la sua classe.

### Go, Rust, JavaScript e TypeScript: chi, semver, tududi

App `daodan-scip-audit` (`modal_scip.py`); conteggi in `results/scip-<caso>-confirm.json`, dall'esecuzione di conferma (indicizzatori rieseguiti, codice uguale al checkout per hash). Il grafo di ogni lingua è sul volume, in `scip-inputs/<caso>/graph-<lingua>.json.gz`.

| Parametro | Valore |
| --- | --- |
| casi | chi `c64ed7d6`, semver `280ebcb6`, tududi `71da9d7b` |
| indicizzatori | scip-go v0.2.9 con Go 1.27.3; `rust-analyzer scip` 2026-11-09 con Rust 1.99.1, senza build script né macro procedurali; scip-typescript 0.5.2 su Node 22.23.4 |
| dipendenze | Go `go mod download`; Rust quelle di cargo; JS/TS `npm ci --ignore-scripts` |
| perimetro | una copia del checkout; Go e Rust: un'esecuzione in più per ogni modulo o crate annidato e le cartelle `_x` di Go nominate come pacchetti; TypeScript: un tsconfig generato con ogni file JS/TS dello snapshot e `allowJs`, che estende quello del progetto |

I salti degli adattatori (`daodan/core/indexers/go.py`, `rust.py`, `typescript.py`):
- `initializer`, `pattern-key` e `value`: un nome definito come alias di un altro, come chiave di un pattern, o con una funzione come valore;
- `declared:@types/react.useCallback` e `declared:@types/react.useMemo`: librerie che per contratto restituiscono il loro argomento, riconosciute dal simbolo esterno e dal pacchetto, mai dal nome;
- `rust:module-file`: un modulo incluso da più crate.

Archi per fine della catena:

| Lingua | File snapshot / indicizzati | Nodi | Archi | Funzione, metodo o classe del progetto | Valore del progetto | Esterno | Vicolo cieco |
| --- | --- | --- | --- | --- | --- | --- | --- |
| chi Go | 90 / 90 | 4.847 | 20.102 | 3.357 | 9.094 | 7.651 | 0 |
| semver Rust | 19 / 18 | 1.073 | 3.960 | 1.023 | 1.306 | 1.572 | 59 |
| tududi JavaScript | 1.038 / 1.038 | 86.225 | 182.593 | 16.407 | 86.442 | 70.944 | 8.800 |
| tududi TypeScript | 650 / 650 | 41.107 | 171.821 | 15.147 | 64.977 | 84.067 | 7.630 |

Simboli del progetto per tipo:

| Lingua | Funzioni | Metodi | Classi | Tipi | Variabili | Parametri | Proprietà | Moduli |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| chi | 292 | 169 | 44 | 18 | 3.439 | 0 | 272 | 109 |
| JavaScript | 1.440 | 1.255 | 85 | 0 | 25.291 | 9.557 | 42.533 | 2.076 |
| TypeScript | 230 | 60 | 18 | 714 | 12.963 | 8.818 | 13.231 | 1.303 |

- Simboli esterni: 504 per chi, 1.347 per JavaScript, 2.000 per TypeScript.
- `local` senza definizione: 2.639 in JavaScript, 1.768 in TypeScript.
- chi conta zero parametri perché scip-go dà ai parametri il tipo `Variable`.

Salti sugli archi che arrivano a una funzione del progetto:

| Lingua | 0 salti | 1 | 2 | 3 o più | Tipi di salto |
| --- | --- | --- | --- | --- | --- |
| chi | 2.088 | 1.267 | 2 | 0 | implementazione 1.138, inizializzatore 207, funzione assegnata 102, intervallo condiviso 61 |
| JavaScript | 12.608 | 3.774 | 25 | 0 | intervallo condiviso 7.721, inizializzatore 897, funzione assegnata 71, chiave di pattern 20, implementazione 6 |
| TypeScript | 13.324 | 1.753 | 63 | 7 | intervallo condiviso 10.968, inizializzatore 1.053, `declared:@types/react.useCallback` 287, chiave di pattern 54, funzione assegnata 33, `declared:@types/react.useMemo` 1 |

chi: 538 chiamate portano 1.126 implementazioni accanto al metodo chiamato (`Router.Get` e `Mux.Get`); 384 chiamate arrivano al progetto solo da implementazioni nel progetto di un metodo di un'interfaccia esterna (`w.WriteHeader` di `net/http.ResponseWriter` → `basicWriter.WriteHeader`, `middleware/basic_auth.go:32`).

Chiamate dello snapshot senza alcuna occorrenza dell'indice, per classe:

| Lingua | Chiamate | Classe | Esempi |
| --- | --- | --- | --- |
| chi | 261 | builtin del linguaggio | `_examples/fileserver/main.go:50` `panic`, `middleware/route_headers.go:66` `append`, `tree.go:80` `panic` |
| chi | 43 | callee dinamico, senza nome | `_examples/graceful/main.go:30`, `middleware/maybe_test.go:19`, `middleware/throttle_test.go:138` |
| chi | 5 | `err.Error` sull'interfaccia builtin `error` | `_examples/rest/main.go:268`, `:420`, `_examples/router-walk/main.go:35` |
| JavaScript | 9.166 | ricevente di tipo `any` (modelli Sequelize, `req`) | `backend/app.js:110`, `backend/modules/spreadsheets/importService.js:607`, `backend/tests/integration/mcp/mcp-tools.test.js:2914` |
| JavaScript | 3.698 | ricevente che è un'espressione | `backend/config/database-settings.js:39`, `backend/tests/integration/caldav-protocol.test.js:57`, `backend/tests/integration/profile-ai-settings.test.js:153` |
| JavaScript | 2.565 | legame ambiguo per lo snapshot | `backend/modules/ai-assistant/service.js:839`, `backend/tests/integration/hosted-shared-roster.test.js:233`, `backend/tests/integration/shared-areas-access.test.js:222` |
| TypeScript | 564 | `fireEvent.click`, `fireEvent.change` | `frontend/__tests__/Layout.test.tsx:262`, `frontend/components/Inbox/__tests__/QuickCaptureInput.nlp.test.tsx:73`, `frontend/components/Shared/__tests__/BlankSlate.test.tsx:39` |
| TypeScript | 408 | ricevente sconosciuto allo snapshot | `e2e/tests/inbox-task-project.spec.ts:59`, `frontend/components/Inbox/__tests__/QuickCaptureInput.slash.test.tsx:305`, `frontend/components/Task/TaskDetails.tsx:663` |

Classi minori, dal file dei risultati: JavaScript 16 nomi non legati; TypeScript 164 con ricevente o forma di import sconosciuta, 144 callee dinamici, 2 legami ambigui. I riceventi `any` di JavaScript restano senza bersaglio per ogni fonte statica provata (sezione 4); li chiude il passo dinamico: «Che cosa resta aperto dopo l'intera pipeline».

Lacune dell'indice, contate come buchi:
- TypeScript, 3.755 chiamate finiscono su un `local` che nessun documento definisce (`t` di `useTranslation`, `frontend/Layout.tsx:497`).
- JavaScript, 61 chiamate sono metodi abbreviati di un oggetto in un altro file (`backend/modules/admin/service.js:1085`, `backend/modules/inbox/operations/attachments.js:59`, `backend/modules/onboarding/controller.js:26`). L'indice non ha nessun dato nello stesso file e intervallo, quindi restano buchi.
- Rust, modulo di test condiviso: lo recupera `rust:module-file`, sulla fixture 2 chiamate su 2. Su semver arrivano così 181 delle 186 chiamate che solo il passo per posizione risolveva, tutte sullo stesso bersaglio. Le 5 restanti non sono nell'indice: 3 `string.parse` (`core`) e 2 in `tests/node/mod.rs`, senza documento.
- Fini su un valore senza alias dichiarato, chiamate (`results/scip-tududi-full.json`): risultato di chiamata JavaScript 897, TypeScript 3.426; parametro 649 e 281.

semver, il resto dei conteggi: archi `call` 776, `read` 713, `unknown` 2.471. Catene verso una funzione del progetto: 733 a 0 salti, 290 a 1 (`rust:module-file` 260, inizializzatore 22, funzione assegnata 8). Buchi 24: 18 in `tests/node/mod.rs`, senza documento; 5 callee dinamici senza nome (`benches/parse.rs:8`); 1 senza occorrenza (`src/identifier.rs:326` `repr.trailing_zeros`). I 59 vicoli ciechi sono simboli del progetto che rust-analyzer riferisce senza definirli: 57 impl generati da `derive` (`impl#[Op][PartialEq<Self>]eq()`), 2 `QuotedChar#0.`; rust-analyzer registra 84 errori `definition should have been in an SCIP document`.

Pacchetti esterni più riferiti, per archi (i venti completi sono nei file dei risultati):
- chi, otto in tutto: Go standard 1.24 7.128, Go 1.22 168, Go 1.16 117, `go-chi/chi/v5@v5.1.0` 99, `go-chi/render@v1.0.1` 57, `go-chi/chi/v5@v5.2.4` 51, `go-chi/render@v1.0.3` 24, `go-chi/docgen@v1.2.0` 7;
- JavaScript: `@types/jest` 28.976, `typescript` 24.037, `@types/node` 10.600, `sequelize` 2.935, `@types/express-serve-static-core` 886, `@testing-library/jest-dom` 702, `moment` 684, `stripe` 566, `moment-timezone` 326, `@types/express` 324;
- TypeScript: `@types/react` 30.064, `typescript` 25.244, `@types/jest` 8.879, `@testing-library/dom` 4.151, `@types/node` 2.733, `@testing-library/jest-dom` 2.328, `react-i18next` 2.020, pacchetto `. .` 2.015, `react-router` 1.396, `playwright` 761.

Prova a mano: 15 chiamate per lingua, scelte a caso fra tutte quelle del checkout (seme 20261113). La destinazione attesa è scritta leggendo il sorgente, prima di guardare il grafo; le attese sono in `HAND` di `modal_scip.py`.

| Lingua | Giuste per il grafo | Giuste per il passo per posizione |
| --- | --- | --- |
| chi | 15 / 15 | 13 / 15 (`NewRouter` e `GetLogEntry` non chieste) |
| semver Rust | 15 / 15 | 12 / 15 (`Some`, `ok`, `Ok` non chieste o senza risposta) |
| JavaScript | 12 / 15 | 7 / 15 |
| TypeScript | 14 / 15 | 10 / 15 |

Le quattro sbagliate non hanno nessuna occorrenza nell'indice:
- `queryInterface.addIndex`: parametro senza tipo;
- `lastModified.toJSDate`: valore `any` di ical.js;
- `Task.create`: modello Sequelize costruito a runtime;
- `tag.slice`, in `frontend/components/Inbox/__tests__/QuickCaptureInput.focus.test.tsx:88`.

Indicizzatore nell'esecuzione di conferma: gli indici di chi, semver e tududi sono identici byte per byte fra le esecuzioni; quello di tududi pesa 44.550.689 byte e si scrive in 55,2 s con 2.264 MB. Container: chi 14,9 s, semver 28,4 s, tududi 651,4 s (installazione dei pacchetti JS e indice rifatti). Costo fatturato da Modal: 0,082 USD per i tre casi.

Non verificato:
- perché `fireEvent.click` non ha occorrenze (il compilatore lo risolve: sezione 4);
- il pacchetto `. .` (968 chiamate TypeScript).

### Python: python-semver

scip-python indicizza python-semver. Ciò che è proprio del motore sta in `daodan/core/indexers/python.py`: `index` (dipendenze dichiarate in un ambiente della cartella condivisa, solo wheel, date a scip-python con `--environment`; `pyrightconfig.json` per il layout `src`; indice di uno specchio del progetto) e `hops`. `lang_python.py` collega modulo, lettura comune e volume. Esecuzione: `modal deploy benchmarks/inference-audit/lang_python.py`, poi `python benchmarks/inference-audit/lang_python.py spawn --cases semver` e `fetch --cases semver`; `spawn --graph-only` rifà il grafo dai file sul volume (`inference-audit/graph-python/semver/`) senza rieseguire l'indicizzatore. Risultati: `results/graph-python-semver.json` (nodi, archi, buchi; 1,1 MB) e `results/graph-python-semver-checks.json` (fatti dell'indice, conteggi, buchi per classe, verifica a mano).

| Parametro | Valore |
| --- | --- |
| caso | python-semver `b6e83e3e40d3a7570386e8d694ae8011477a55c1`, 35 file Python: 7 sorgenti, 25 test, 3 di documentazione; due test sono symlink a file di `docs/advanced/` |
| indicizzatore | scip-python 0.6.8 (npm), Node v22.23.4, Python 3.13 |
| dipendenze | le 14 dichiarate in `pyproject.toml` (dipendenze opzionali e gruppi PEP 735), installate con uv in una sola chiamata: 87 pacchetti nella venv |
| configurazione | il progetto non configura Pyright: l'adattatore scrive nella copia un `pyrightconfig.json` con `src` come radice e come percorso aggiuntivo. Senza, nessun import assoluto del pacchetto `semver` si risolve e 112 chiamate su 995 arrivano al progetto invece di 458 (prima esecuzione, stesso indicizzatore) |
| snapshot | da una copia dove i symlink sono file normali: `snapshot.py write` sul checkout va in errore con `UNIQUE constraint failed: files.path`, perché nomina un link con il percorso del suo bersaglio |
| arco | quello comune; scip-python scrive solo i ruoli definizione e lettura |
| salti | `import-binding`: un nome di `from m import a [as b]` su una riga va al modulo `m`. `builtin`: un nome libero presente in `builtins`, che non sia un attributo o il nome di un argomento, va a `builtins/<nome>`. `classmethod-cls`: il primo parametro di un metodo decorato `classmethod` va alla sua classe. `type-of-self`: un locale `x = type(self)` va alla classe del metodo. Dopo questa misura: `initializer`, un nome assegnato a un solo nome, semplice o puntato (`f = area`, `self.f = area`), porta a ciò a cui rimanda l'ultimo nome; `rebinding`, la chiamata di una funzione con stub `@overload` finisce sull'ultimo `def` senza `overload`. Ogni salto resta nella `chain` con il suo nome |
| verifica a mano | 20 chiamate lette nel sorgente prima di leggere il grafo (`HAND` in `lang_python.py`) |

Copertura: 35 file su 35 hanno un documento con occorrenze; i due symlink sono indicizzati due volte, anche dal loro bersaglio. L'indice ha 4.590 occorrenze e 919 definizioni. I ruoli sono solo definizione e lettura, mai import o scrittura. `SymbolInformation.kind` non è mai valorizzato: la specie viene dal suffisso del simbolo. Relazioni: 11 `is_implementation`, dalle sottoclassi a `Version` e dagli override di `parse`. Nessun alias a intervallo condiviso, nessun campo protobuf non letto.

Nodi: 1.289, cioè 914 simboli definiti, 173 esterni, 167 simboli riferiti senza definizione (locali e moduli) e un nodo per documento.

Archi: 3.679, cioè 3.671 dai riferimenti (`call` 980, `read` 1.319, `unknown` 1.372) e 8 implementazioni, da `cls.parse` (`version.py:479`, `:833`) verso i quattro override `SemVerWithVPrefix.parse`.
- Catene dei 3.671: 3.605 senza salti. Le altre 66 hanno un salto: `builtin` 33, `type-of-self` 21, `import-binding` 7, `classmethod-cls` 5.
- Dispatch statico: `C.m` su un simbolo di classe e `super().m`, 109 siti. Senza dichiararli le implementazioni sarebbero 372: ogni `Version.parse(...)` e `super().parse(...)` riceverebbe anche gli override, che lì non vengono mai eseguiti.
- Con `initializer` e `rebinding` (stage del prodotto, sezione 3) i salti `initializer` sono 28 e 11 archi passano da un valore a una funzione del progetto; i file in `results/` vengono dal modulo precedente.

| Fine del riferimento dello snapshot | Chiamate | Letture |
| --- | --- | --- |
| funzione, metodo o classe del progetto | 468 | 131 |
| valore del progetto | 7 | 71 |
| esterno con pacchetto e versione | 487 | 319 |
| parametro | 4 | 390 |
| locale | 3 | 399 |
| locale senza definizione | 9 | 1 |
| simbolo del progetto senza definizione | 2 | 8 |
| nessuna occorrenza | 15 | 29 |
| totale | 995 | 1.348 |

Mancati veri, cioè chiamate che dovrebbero arrivare a una funzione del progetto e non ci arrivano: 19.
- Valori creati da un decoratore, 7: `main = deprecated(cli.main)` e `createparser`, chiamati in `tests/test_pysemver-cli.py` (righe 41, 109, 116, 124, 129, 133, 156). Il grafo si ferma al valore.
- Parametri chiamati, 4: `_deprecated.py:81 func(...)`, `version.py:68 operator(self, other)`, `tests/test_deprecated_functions.py:63`, `tests/test_pysemver-cli.py:104`.
- Attributi dinamici, 3: `cli.py:152 args.func(args)`, `cli.py:46 func()` con `func = getattr(...)`, `version.py:556 getattr(version, "bump_" + part)()`.
- `type(self)` fuori da un metodo o chiamato subito, 3: `version.py:65` (due, dentro il wrapper di `_comparator`) e `version.py:807 type(self)(**version)`.
- Ricevitori fixture senza tipo, 2: `tests/test_semver.py:30 version.to_dict()`, `:36 version.to_tuple()`.

I 9 locali senza definizione fra le chiamate sono metodi di valori che l'indice non lega a nulla: `str.format` 6, `sys.exit`, `importlib.util.find_spec`, `assert_called_once`.

Bersagli sbagliati, 3:
- `self._major` e gli altri attributi dichiarati solo in `__slots__` (`version.py:160`-`164`, 29 letture) puntano alla classe `Version`.
- `operator.lt` e `operator.gt` (`tests/test_compare_invalid_operands.py:52`, `:67`) puntano a `_operator/index().`.
- `pytest.skip` e `pytest.fail` (`tests/test_optional_native_backend.py:16`, `tests/test_deprecated_functions.py:65`) hanno il simbolo `_pytest.outcomes/...` con il pacchetto del progetto, non con quello di pytest.

Buchi: 64. Senza occorrenza 15 chiamate e 29 letture:
- Su un parametro senza tipo, 7 chiamate e 20 letture: attributi di `argparse.Namespace` messi a runtime e fixture pytest (`cli.py:152 args.func`, `cli.py:38 args.bump`, `tests/test_pysemver-cli.py:118 capsys.readouterr`).
- Catene di attributi su valori senza tipo, 5 chiamate (`cli.py:41 args.parser.parse_args`, `tests/test_pysemver-cli.py:119 captured.err.startswith`).
- Callee calcolato, 2 chiamate (`version.py:556`, `:807`).
- `setter` di property, 5 letture (`version.py:217 @major.setter`); `String.__args__` di un alias `typing`, 3 letture (`version.py:56`).
- Locale di tipo ignoto, 1 chiamata e 1 lettura (`tests/test_pysemver-cli.py:43`, `:136`).
- In più, 20 riferimenti che finiscono solo in un vicolo cieco: 10 locali senza definizione, 10 simboli del progetto senza definizione.

Il passo dinamico dà la destinazione osservata a 16 delle chiamate mancate e a 31 dei 64 buchi: [`call-provenance`](../call-provenance/README.md), sezione 2.

Verifica a mano: 18 su 20.
- Giusti anche: decoratore, chiamate in metodi decorati, callback passati come valore, metodo sul risultato di una chiamata, metodo ereditato e `super()`, riesportazione da `semver/__init__.py`, parametri chiamati come vicolo cieco, nessuna occorrenza su `args.func`.
- Mancato `version.py:65 cls(**other)`: locale da `type(self)` dentro un wrapper, atteso la classe `Version`.
- Mancato `version.py:769 _native_parse_parts`: alias `as`; il salto arriva al pacchetto giusto, `fast-semver-rs-backend`, ma al modulo e non a `parse_parts`.

Pacchetti esterni (4 in tutto, siti):

| Pacchetto | Siti |
| --- | --- |
| python-stdlib 3.11 | 821 |
| pytest 9.1.1 | 390 |
| fast-semver-rs-backend 0.1.2 | 5 |
| packaging 26.3 | 3 |

Tempo e memoria, esecuzione di conferma (pipeline completa, codice uguale al checkout per hash), da cui vengono i file in `results/`: indicizzatore 7,5 s e 369 MB il processo più grande, container 15,3 s. Costo fatturato da Modal: 0,034 USD per le prime dieci chiamate, 0,004 per quella di conferma.

Non verificato:
- Se nella prima esecuzione pesa anche la TomlError di scip-python su `pyproject.toml` (riga 105, probabilmente un array misto, ammesso da TOML 1.0 e non da TOML 0.5), oltre al layout `src` non dichiarato.
- Perché la libreria standard è etichettata 3.11 con Python 3.13.
- La regola `builtin` assume che il file non abbia `import *`: semver non ne ha, l'adattatore non lo controlla. `import-binding` copre solo gli import su una riga.
- Jedi su questo caso: le sue risposte esistono solo sul volume (`inference-audit/strong-python/semver.json`, lette da `benchmarks/call-provenance/modal_dynamic_python.py`); lo script che le scrive e i suoi conteggi non sono nel repository.
- Altri progetti Python oltre a phazly (sotto).

### Python, TypeScript, JavaScript e Rust: phazly

phazly è privato. Archivio: `git archive 46c92b28 react-app shared functions-python`, senza `google-services.json`, file `.env`, keystore e `functions-python/app/core/secrets.py`; restano fuori i tre sottomoduli `vendor/` (plugin Tauri). App `daodan-scip-audit`, caso `phazly` di `modal_scip.py`; l'archivio sta sul volume. Nello stesso container: snapshot, passo per posizione (risposte in `scip-inputs/phazly/answers.sqlite`), scip-python su `functions-python`, scip-typescript su ogni file JS/TS con `react-app/tsconfig.app.json` come base (alias `@/` e `@shared/`) e i pacchetti di `react-app` e `shared` installati a parte, rust-analyzer su `react-app/src-tauri`. Risultati: `results/scip-phazly-graph.json`; dopo le due regole Python `initializer` e `rebinding`, `results/scip-phazly-final.json`. Il confronto con il passo per posizione è nella sezione 2.

Rust e Kotlin su phazly non sono misurati. L'archivio non ha i sottomoduli `vendor/`, da cui dipendono sia il crate Tauri sia la build Android: `cargo metadata` fallisce e rust-analyzer indicizza senza dipendenze (grafo: 2 chiamate su 29); la build Android vuole anche l'SDK Android e `google-services.json`, un file segreto che resta fuori dall'archivio, quindi Kotlin non ha indice.

| Lingua | File snapshot / indicizzati | Nodi | Archi | Funzione, metodo o classe del progetto | Valore del progetto | Esterno | Vicolo cieco | Incerti |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Python | 336 / 333 | 35.662 | 147.143 | 16.877 | 83.699 | 43.718 | 2.849 | 0 |
| TypeScript | 437 / 437 | 26.158 | 102.734 | 7.975 | 49.893 | 41.090 | 3.776 | 0 |
| JavaScript | 11 / 11 | 889 | 2.814 | 68 | 1.020 | 1.549 | 177 | 0 |
| Rust | 3 / 3 | 12 | 8 | 1 | 6 | 1 | 0 | 0 |

- Python, i 3 file mancanti sono script fuori dalla cartella indicizzata: `react-app/scripts/generate-emoji-font.py`, `react-app/scripts/store-art/finalize.py`, `react-app/scripts/store-art/verify-gallery-png.py`.
- Rust: i 3 file hanno un documento ma quasi nessuna occorrenza.
- Nessun adapter di queste lingue marca archi incerti.
- Salti sulle chiamate che arrivano al progetto: Python `builtin` 2.371, `import-binding` 259, implementazione 194, `classmethod-cls` 19; TypeScript intervallo condiviso 8.238, inizializzatore 1.994, `declared:@types/react.useCallback` 663, chiave di pattern 213.
- Dopo le due regole Python: 147.150 archi, stessi 35.662 nodi; `initializer` porta 24 chiamate a una funzione del progetto (9 lette nel sorgente, tutte giuste).

#### Buchi per classe (chiamate e letture)

| Lingua | Classe | Riferimenti | Esempi |
| --- | --- | --- | --- |
| Python | nessuna occorrenza | 4.398 (2.584 chiamate) | `functions-python/app/api/deps.py:83` `doc.get`, `functions-python/app/planner/solver.py:783` `model.NewBoolVar`, `functions-python/app/handlers/admin/analytics.py:141` `(expr).to_list` |
| Python | file senza documento | 528 | `react-app/scripts/generate-emoji-font.py:103`, `react-app/scripts/store-art/finalize.py:116`, `react-app/scripts/store-art/verify-gallery-png.py:26` |
| Python | simbolo del progetto senza definizione | 394 | `functions-python/app/api/deps.py:51` `__name__`, `functions-python/tests/unit/test_billing_regressions.py:743` `asyncio.Event`, `functions-python/app/handlers/admin/meal_images.py:143` `httpx.AsyncClient` |
| Python | locale senza definizione | 308 | `functions-python/app/api/deps.py:227` `task.add_done_callback`, `functions-python/tests/unit/test_billing_regressions.py:910` `entered.wait`, `functions-python/app/handlers/process_meal_images.py:767` `_worker_task.done` |
| TypeScript | locale senza definizione | 2.293 | `react-app/src/App.tsx:81` `t`, `react-app/src/components/common/AddMealTypeSheet.tsx:76` `toast.success`, `react-app/src/components/features/AIAlternatives.tsx:386` `DialogPrimitive.Portal` |
| TypeScript | nessuna occorrenza | 517 (7 chiamate) | `react-app/src/components/common/DesktopTabRenderer.tsx:29` `TAB_MAP.home`, `react-app/src/services/mealPlanService.ts:176` `data.proof.policyHash`, `react-app/src/utils/plannerPlanWire.ts:85` `value.inputBasis` |
| TypeScript | chiamata senza posizione (callee dinamico) | 80 | `react-app/src/contexts/SubscriptionContext.tsx:197`, `react-app/src/components/settings/MealTypesConfig.tsx:326`, `react-app/scripts/screenshots/take-screenshots.ts:82` |
| JavaScript | nessuna occorrenza | 208 | `react-app/scripts/android-version.mjs:41` `v.match`, `react-app/scripts/store-art/export-feature.mjs:136` `page.screenshot`, `react-app/scripts/store-art/export-gallery.mjs:86` `page.setContent` |
| Rust | nessuna occorrenza | 29 | `react-app/src-tauri/build.rs:2` `tauri_build.build`, `react-app/src-tauri/src/lib.rs:22` `(expr).plugin`, `react-app/src-tauri/src/lib.rs:33` `app.handle` |

Classi minori: Python senza posizione 6, TypeScript simbolo senza definizione 7, JavaScript senza posizione 3. Fra i locali TypeScript senza definizione, 1.923 riferimenti sono quelli che il lessicale chiama `non-callable-binding`, negli esempi tutti `t`; altri 193 hanno negli esempi `toast.*` di sonner.

#### Esterni con pacchetto e versione (archi)

- Python: python-stdlib 3.11 37.363, pydantic 2.12.5 2.173, pytest 9.2.0 1.541, fastapi 0.136.3 781, ortools 9.12.4544 345, motor 3.7.0 272, starlette 1.10.0 232, firebase_admin 7.1.0 231, pymongo 4.18.3 225, httpx 0.28.1 168, stripe 14.3.0 92.
- TypeScript: typescript 6.0.3 16.483, @types/react 19.3.0 13.099 (e 19.2.14 1.513, dall'installazione di `shared`), pacchetto `. .` 1.713, @phosphor-icons/react 2.1.10 1.602, framer-motion 12.43.0 1.456, motion-dom 12.43.0 1.201, @types/node 24.19.2 1.143, react-i18next 16.6.6 560, sonner 2.0.8 316, playwright-core 1.65.1 302, i18next 25.10.10 267, zustand 5.1.0 183.
- JavaScript: typescript 6.0.3 872, @types/node 24.19.2 638, pacchetti di eslint 26.
- Rust: `core` 1.

#### Controllo a mano

59 siti, scelti fra file diversi e con casi difficili (decoratori, `Depends`, funzioni annidate, fixture, `useCallback`, valori del contesto, JSX a una e a due parti, callback). L'atteso è stato scritto leggendo il sorgente prima che il grafo esistesse; sta in `HAND["phazly"]` di `modal_scip.py`. Kotlin non ha siti, perché non ha grafo.

| Lingua | Siti | Grafo | Passo |
| --- | --- | --- | --- |
| Python | 15 | 15 | 15 |
| TypeScript | 15 | 9 | 6 |
| JavaScript | 15 | 13 | 6 |
| Rust | 14 | 2 | 0 |

Mancati del grafo:
- TypeScript, 6:
  - `react-app/src/components/subscription/PaywallModal.tsx:132` `startCheckout` e `:130` `clearError`: il grafo, come il passo, dà il membro del contratto (`react-app/src/contexts/SubscriptionContext.tsx:151`, `:155`). L'atteso era la funzione in `useCallback` (`:296`, `:237`): il valore del contesto è legato al contratto solo dal tipo.
  - `PaywallModal.tsx:239` `onOpenChange`: l'atteso era un valore, perché a runtime sono i setter dei chiamanti. Il grafo prende per funzione la firma della prop (`PaywallModal.tsx:38`).
  - `react-app/src/components/home/SortableHomeCards.tsx:73` `Reorder.Item`: un `local` senza definizione; l'atteso era framer-motion.
  - `react-app/src/hooks/useHomeTabController.ts:393` `addMealAddition`: è il risultato del selettore `useAppStore(...)` e il grafo si ferma alla variabile; l'atteso era `react-app/src/stores/slices/mealPlanSlice.ts:260`.
  - `react-app/src/hooks/useHomeTabController.ts:413` `t`: un `local` senza definizione. Il passo dà un esterno senza pacchetto.
- JavaScript, 2: `react-app/.design-sync/prebuild.mjs:21` e `:24` non sono nello snapshot, che esclude le cartelle che iniziano con un punto. L'errore è mio, nella scelta dei siti.
- Rust, 12: nessuna occorrenza, perché senza le dipendenze non c'è nessun simbolo di tauri.

Mancati del passo:
- TypeScript: i cinque siti sopra, più due rese di `PaywallModal` e `SubscriptionContext.Provider`, che non chiede, e `showUsageLimitPaywall` (`project-not-a-symbol`).
- JavaScript: sette esterni non chiesti o senza risposta, più i due siti fuori dallo snapshot.
- Rust: tutti e 14.

#### Funzioni che arrivano attraverso un contratto

- `<PaywallModal` è reso da 11 componenti, contati nel sorgente, tutti con un nome di una sola parte. Nel grafo arrivano tutti e 11 a `react-app/src/components/subscription/PaywallModal.tsx:68`, senza salti: 23 archi, cioè 11 letture JSX, 11 import e il re-export di `react-app/src/components/subscription/index.ts:1`.
- Il passo non chiede le letture. Dei 3 siti di resa controllati a mano ne ha 1, grazie al lessicale (import diretto, `react-app/src/components/subscription/ExpiredBanner.tsx:66`). Gli altri due passano dal barrel `@/components/subscription` o `../subscription`.
- In phazly a questo commit non c'è nessun `<X.Paywall />`. Le forme JSX a due parti presenti: `react-app/src/contexts/SubscriptionContext.tsx:699` `SubscriptionContext.Provider` è giusta (esterno `@types/react`), `Reorder.Item` è mancata.
- `startCheckout` ha 3 archi, tutti verso il contratto `react-app/src/contexts/SubscriptionContext.tsx:151`: la chiamata `PaywallModal.tsx:132`, la destrutturazione `PaywallModal.tsx:71` e la proprietà dell'oggetto valore `SubscriptionContext.tsx:687`. Nessuno arriva alla funzione `:296`. Il grafo conserva il contratto. Per arrivare alla funzione bisognerebbe legare la proprietà dell'oggetto passato al Provider al membro del contratto, e l'indice questo legame non lo scrive.
- Classe aperta: quando una funzione arriva a chi la chiama attraverso un oggetto passato al Provider di un contesto o a un creatore di store (zustand), l'indice si ferma al membro del contratto. Su phazly: `startCheckout` e `clearError` del contesto, le azioni degli slice (`setTheme`, `setCurrentPlan`, `addMealAddition`). Nessuna fonte statica provata la chiude; dopo il passo dinamico non è misurato.

Tempi: scip-python 0.6.8 (47 requisiti dichiarati, 127 pacchetti nella venv) 72,4 s e 1.850 MB; scip-typescript 0.5.2 (TypeScript 6.0.3) 40,0 s e 1.834 MB; rust-analyzer 2,5 s e 891 MB; snapshot 52,8 s; grafo e confronto 30,2 s. Costo fatturato da Modal: circa 0,23 USD, più 0,02 per il ricongiungimento dopo le due regole.

Non verificato:
- perché scip-python attribuisce al progetto `asyncio.Event` e `httpx.AsyncClient` (394 riferimenti), e perché la libreria standard è etichettata 3.11 con Python 3.13;
- il pacchetto `. .` (1.713 archi TypeScript);
- Kotlin, che non ha indice;

### Java: javapoet

scip-java compila javapoet. Ciò che è proprio del motore sta in `daodan/core/indexers/java.py`: `index` (installazione, build, seconda aggregazione), `hops`, vuoto, `static` e `same_range`; `adapters/java.py` lo esegue su Modal e legge l'ordine dei membri nei class file. `lang_java.py` collega adattatore, lettura comune e volume. Esecuzione: `modal deploy benchmarks/inference-audit/lang_java.py`, poi `python benchmarks/inference-audit/lang_java.py spawn` e `fetch`; `fetch --files DIR` e `graph --dir DIR` rifanno il grafo dai file sul volume (`inference-audit/graph-java/javapoet/`) senza rieseguire l'indicizzatore. Risultati: `results/graph-java-javapoet.json` (nodi, archi, buchi; 8,5 MB) e `results/graph-java-javapoet-checks.json` (il resoconto comune, accordo con il lessicale, verifica a mano).

| Parametro | Valore |
| --- | --- |
| caso | javapoet `b9017a9503b76e11b4ad4c1a9f050e2d29112cb0` (Maven), 39 file Java: 17 sorgenti, 22 test |
| indicizzatore | scip-java 0.13.2 (`org.scip-code:scip-java`, assemblato con coursier 2.1.24), OpenJDK 17.0.21, Maven 3.8.7 |
| build | il pom senza modifiche non compila su Java 17: Error Prone 2.3.1 dà `class file has wrong version 61.0, should be 53.0`. L'adattatore toglie dal plugin del compilatore `<compilerId>`, `<forceJavacCompilerUse>` e le dipendenze di Error Prone, solo nella copia del checkout |
| relazioni | lo stesso build aggregato una seconda volta con `--no-emit-inverse-relationships`: l'aggregazione di default scrive ogni `is_implementation` anche dal padre al figlio, con gli stessi flag. Si legge l'indice della seconda aggregazione, con occorrenze verificate uguali a quelle del primo |
| arco | quello comune; scip-java non scrive ruoli di accesso |
| verifica a mano | 20 chiamate lette nel sorgente prima di leggere il grafo (`HAND_CHECK` in `lang_java.py`) |

Copertura: 39 file su 39 hanno occorrenze. L'indice ha 21.601 occorrenze e 2.780 definizioni, ogni `SymbolInformation` ha una firma, nessun campo protobuf resta non letto e `external_symbols` è vuoto.

Nodi: 3.541, cioè 39 file, 2.780 simboli definiti e 722 simboli riferiti senza definizione.
- Simboli del progetto: Method 690, StaticMethod 93, AbstractMethod 25, Constructor 93 (52 impliciti, definiti sul nome della classe e senza corpo), Class 79, Interface 13, Enum 3, Field 180, StaticField 32, TypeParameter 25, costanti enum senza kind 11.
- Simboli locali: Variable 848, senza kind 659 (dalla firma sono parametri), metodi di classi anonime 27, Field 2.

Archi: 19.189, cioè 18.821 dai riferimenti e 368 implementazioni. Per tipo: `call` 6.811, `read` 2.680, `unknown` 9.698. Per fine, nella lettura comune: `project-callable` 6.951, `project-value` 4.286, `external` 6.265, `dead-end` 1.687. La tabella sotto divide le stesse fini con il kind dell'indice; le due letture differiscono su 8 archi, i nomi degli elementi di annotazione (`AnnotationSpecTest.java:95-102`): per l'indice sono metodi, lo snapshot non li dichiara e la lettura comune li conta come valori.

| Fine del riferimento | Archi |
| --- | --- |
| metodo del progetto | 3.911 |
| costruttore del progetto | 141 |
| classe del progetto | 2.539 |
| campo o valore del progetto | 4.278 |
| esterno con pacchetto e versione | 6.265 |
| vicolo cieco | 1.687 |

- Vicoli ciechi: 1.540 nomi di package (SCIP non li definisce), 133 letterali `X.class`, 10 `array.length`, 2 `X#super.` e `X#this.`, 2 `super` locali nelle classi anonime.
- Catene: tutti i riferimenti hanno catena 0, perché l'indice non scrive `is_definition` e Java non ha alias. Le 368 implementazioni sono a un salto e stanno su 69 riferimenti; per esempio `Object#toString` porta 12 override del progetto.
- Lette alla lettera, le relazioni dell'aggregazione di default cambierebbero 11 archi. Per esempio `ParameterizedTypeName.java:44 annotated` riceverebbe come implementazioni il padre `TypeName#annotated(+1)` e quattro fratelli.
- Casi propri di Java, dichiarati dall'adattatore al modulo comune:
  - `static`: le chiamate `super.m()` non passano dalla dispatch, quindi in quei 3 siti nessuna fine raggiunta per implementazione. Toglie 2 archi (`ClassName.java:82`, `TypesEclipseTest.java:82`);
  - `same_range`: al nome di ogni costante enum scip-java scrive la definizione e un riferimento al costruttore che la costante esegue. Le 9 coppie sono dichiarate mai alias; altrimenti 33 letture di costanti finirebbero sul costruttore (`LineWrapper.java:77` `FlushType.WRAP`).

Buchi: ogni chiamata e ogni lettura dello snapshot (6.443 e 2.699) ha la sua occorrenza nell'indice. Il modulo comune conta come buco anche un riferimento che finisce solo in un vicolo cieco: 10 letture `args.length` (`CodeBlock.java:243`), con un simbolo che SCIP non definisce. Al contrario, l'indice ha 36 chiamate che lo snapshot non elenca: `this(...)` 10, `super(...)` 7, costruttori impliciti delle costanti enum 9, nomi degli elementi di annotazione 8, `@Test(expected=...)` 2.

Accordo con il lessicale, sulle 289 chiamate che risolve: 283 sulla stessa dichiarazione, 6 diverse, dove il lessicale indica un costruttore scritto (`AnnotationSpec.java:249`) e la fine indica la classe (regola del costruttore nel grafo, `88c21ea89`). Il file salvato porta la lettura precedente: 264 uguali, 25 dove il lessicale dà la classe e l'indice il suo costruttore.

Overload: l'indice nomina un metodo esterno solo come `nome(+n)`, senza firma. L'overload si legge dall'ordine dei membri nel class file (`javap`), quindi non dall'indice. La regola regge sui metodi del progetto: 808 su 808 hanno gli stessi parametri della firma dell'indice.

Verifica a mano: 20 su 20, destinazione e implementazioni.
- I casi: overload, costruttori anche con `this(...)` e `super(...)`, lambda e method reference, metodo ereditato, import statici, chiamate su interfacce del JDK implementate nel progetto e nei test, dispatch con 5 override, `super.isAnnotated()`.
- Sei destinazioni sono overload esterni letti dal class file.
- Due correzioni dopo le esecuzioni: la riga di `out.emit("")` era scritta 236 invece di 235 (dopo r1); l'`Appendable` anonimo di `JavaFile.java:48`, che avevo mancato, è confermato dal sorgente (dopo r2).

Pacchetti esterni (9 in tutto, occorrenze e simboli):

| Pacchetto | Occorrenze | Simboli |
| --- | --- | --- |
| jdk 17 | 4.501 | 534 |
| truth 1.4.4 | 1.002 | 22 |
| junit 4.13.2 | 647 | 26 |
| compile-testing 0.21.0 | 53 | 15 |
| guava 33.2.1-android | 29 | 16 |
| mockito-core 4.11.0 | 23 | 7 |
| jimfs 1.3.0 | 6 | 4 |
| jsr305 3.0.2 | 2 | 1 |
| ecj 4.6.1 | 2 | 2 |

Tempo e memoria, esecuzione di conferma (pipeline completa, codice uguale al checkout per hash), da cui vengono i file in `results/`:
- Indicizzatore 37,7 s e 639 MB il processo più grande; container 48,1 s.
- L'indice è lo stesso in tutte le esecuzioni (2.266.831 byte).
- Costo fatturato da Modal: 0,028 USD per le prime due esecuzioni, 0,010 per quella di conferma.

Non verificato:
- L'overload dei simboli del JDK direttamente sul JDK: la regola del class file è provata solo sui metodi del progetto, e `javap` copre solo le classi esterne della verifica a mano.
- Le destinazioni delle letture e dei riferimenti a tipi, oltre ai 20 casi e alle 289 chiamate.
- Che il build con Error Prone avrebbe dato gli stessi simboli.
- I picchi di RAM fra un campione e l'altro (due al secondo).
- Perché scip-java scrive solo alcune occorrenze di `this` e `super`.
- Altri progetti, Gradle, Java oltre la 17.

### Kotlin: klaxon

scip-java indicizza klaxon con la build Gradle del progetto. Ciò che è proprio del motore sta in `daodan/core/indexers/kotlin.py`:
- `index`: JDK, scip-java, build e copia dell'indice senza le relazioni inverse (`forward_only`);
- `hops`, vuoto;
- `classify`, `missing` e `refine`, descritti sotto.

`adapters/kotlin.py` lo esegue su Modal; `lang_kotlin.py` collega adattatore, lettura comune e volume e tiene la verifica a mano.

Esecuzione: `modal deploy benchmarks/inference-audit/lang_kotlin.py`, poi `python benchmarks/inference-audit/lang_kotlin.py spawn --stage index` e `fetch`. `spawn --stage graph` rifà il grafo dai file sul volume (`inference-audit/graph-kotlin/klaxon/`: index.scip, index-forward.scip, manifest.sqlite, indexer.json, kotlin-configs/) senza rieseguire l'indicizzatore, e scrive lì anche `graph.json` (nodi, archi con catena e incertezza, buchi). `graph --index --manifest --source --configs --out` fa lo stesso in locale. Risultato: `results/graph-kotlin-klaxon.json` (il resoconto comune, archi incerti, buchi, verifica a mano).

| Parametro | Valore |
| --- | --- |
| caso | klaxon `1173bdc568a6d339b45cf24a6a9c5c2f6847f42d`, Gradle wrapper 7.3, Kotlin 1.6.0; 103 file Kotlin nello snapshot, test compresi |
| indicizzatore | scip-java 0.14.2 (`org.scip-code:scip-java`, classpath di coursier 2.1.24) con scip-kotlin-analysis 0.14.2, cioè la Kotlin Analysis API di kotlin-compiler 2.4.0; Temurin 17.0.21 |
| build | `scip-java index`: `gradlew` con l'init script di scip-java (`clean scipPrintDependencies scipCompileAll`). Ogni task KotlinCompile scrive sorgenti e classpath in `kotlin-configs/`, poi l'indicizzatore li analizza fuori dal compilatore, quindi la versione Kotlin del progetto non conta. La 0.13.0 ha tolto il supporto ufficiale per Gradle < 8, ma con la 7.3 la build va al primo tentativo |
| relazioni | l'indicizzatore scrive `is_implementation` sul membro che sovrascrive, verso quello sovrascritto. L'aggregatore aggiunge l'inversa sul sovrascritto, con `is_implementation` e `is_reference` (`ScipAggregator.java`). `forward_only` ne toglie 30, tutte doppioni di una relazione diretta, e si legge `index-forward.scip` |
| pacchetti | scip-java scrive il segnaposto `. .` sia per i simboli dei test del progetto sia per ogni builtin e simbolo della stdlib. `classify` lo tiene simbolo del progetto solo sotto un percorso di package dove l'indice definisce simboli `. .`; altrove è un esterno con manager `unknown`, il percorso Kotlin (`kotlin/collections`) e versione `unknown`. I simboli di package (righe `package` e `import`) sono namespace |
| arco | quello comune, come per Java; la regola comune di `same-range` non fa alias fra due definizioni allo stesso range |
| incertezza | `refine` marca `overload-across-tasks` un arco verso una funzione del progetto con overload, riferita da un altro task di compilazione; `override-across-tasks` un'implementazione con overload fra task diversi. I candidati sono tutti gli overload del nome nella classe. Un arco incerto resta nel grafo |
| buchi impliciti | `x[k]`, `x[k] = v`, l'iteratore del `for`, i delegati `by` e i `componentN`, trovati con tree-sitter dove l'indice non ha un'occorrenza non locale: classe `implicit-operator` |
| verifica a mano | 20 chiamate lette nel sorgente prima di leggere il grafo (`HAND_CHECK` in `lang_kotlin.py`) |

Copertura: 96 file su 103 hanno occorrenze. Mancano:
- 5 script Gradle `.kts`: nessun task KotlinCompile li compila;
- `buildSrc/src/main/kotlin/KlaxonConfig.kt`: buildSrc ha una sua build, dove i task di scip-java non girano;
- `kobalt/src/Build.kt`: non sta in nessun source set.

L'indice ha 98 documenti (97 Kotlin più `KlaxonDoc.java`), 15.014 occorrenze, 4.508 definizioni con `SymbolInformation`, `external_symbols` vuoto. La codifica delle posizioni non è dichiarata e si legge come UTF-16.

Nodi: 5.223.
- Del progetto: metodi 1.907 (compresi getter e setter sintetici), parametri 1.220, proprietà 1.057, classi 310, tipi 12, file 97.
- Esterni: metodi 340, classi 99, proprietà 95, funzioni 40, variabili 3.
- Senza definizione: 41 package e 2 membri delegati.

Archi: 16.191, di cui 15.940 certi e 251 incerti.

| Fine | Archi |
| --- | --- |
| funzione, metodo o classe del progetto | 7.650 (1.967 diretti, 5.683 implementazioni) |
| valore del progetto (proprietà, getter sintetici, parametri, locali) | 3.762 |
| esterno Maven con versione | 1.594 |
| esterno con manager `unknown` e percorso Kotlin | 2.104 |
| namespace | 1.079 |
| vicolo cieco | 2 |

- Tipo dell'arco: `call` 3.274, `read` 2.215, `unknown` 10.702. scip-java non scrive ruoli di accesso, quindi il tipo viene dal riferimento dello snapshot nella stessa posizione.
- Catene: un riferimento alla proprietà porta anche al getter (e al setter se è `var`), scritti dall'indice allo stesso range, quindi nessun salto. Le implementazioni sono tutte a un salto. Ne portano di più `kotlin/Any#equals` e `toString`, con 94 e 98 override del progetto, compresi quelli generati delle data class. Solo 6 archi passano per `same-range`.
- `klaxon/src/test/kotlin/com/beust/klaxon/Issue118Test.kt` lo snapshot lo legge solo come lessicale, senza dichiarazioni: i suoi 23 simboli riferiti finiscono come valori del progetto.

Archi incerti: 238 `overload-across-tasks` e 13 `override-across-tasks`.
- Il motivo: per una dichiarazione con sorgente, il numero `(+N)` segue l'ordine del sorgente (`SymbolsCache.kt`). Per una letta dal classpath di un altro task segue l'ordine della classe compilata, quindi la stessa stringa può nominare un altro overload.
- Overload: `Klaxon#parse` 78, `Klaxon#toJsonString` 49, `KlaxonJson#obj` 38, `Parser#parse` 33, `KlaxonJson#array` 17, `Klaxon#parseArray` 12, il costruttore di `JsonArray` 9, `Klaxon#parseJsonObject` 2.
- Override: i 13 sono tutti verso `JacksonParser#parse()`.

Buchi: 330.
- `no-document` 226: negli script `.kts` 132 chiamate e 60 letture; in `kobalt/src/Build.kt` 18 chiamate e 16 letture.
- `implicit-operator` 93:
  - `get` 63 (`klaxon/src/main/kotlin/com/beust/klaxon/Annotations.kt:37`);
  - `set` 21 (`klaxon/src/main/kotlin/com/beust/klaxon/KlaxonParser.kt:175`);
  - iteratore del `for` 5;
  - delegati `by` 2;
  - `componentN` 2, nel `for ((k, v) in map)` di `klaxon/src/main/kotlin/com/beust/klaxon/JsonObject.kt:22`.
  - Gli operatori binari (`==`, `+`, `in`, `..`) hanno invece la loro occorrenza.
- `no-occurrence` 8: etichette di argomenti nominati, come `klaxon/src/test/kotlin/com/beust/klaxon/InstanceSettingsTest.kt:46 instanceSettings`. L'indice scrive l'etichetta solo quando la funzione chiamata ha sorgente nello stesso task: 8 su 110.
- `undefined-project-symbol` 2: i membri delegati con `by map` e `by value`, che l'indice non definisce (`src/test/kotlin/com/beust/klaxon/TestTypes.kt:100`, `src/test/kotlin/com/beust/klaxon/KlaxonTest.kt:318`).
- `no-position` 1: il riferimento dello snapshot senza nome a `klaxon/src/test/kotlin/com/beust/klaxon/PrettyPrintTest.kt:10`.

Verifica a mano: 16 su 20. I quattro errori sono tutti marcati, come incerti o come buchi; nessuno resta un arco certo sbagliato.
- Giusti: membri di companion object dalla classe, lambda con receiver, estensioni anche dai test della root, getter Java e getter personalizzato, costruttore primario, overload nello stesso task, chiamate su interfacce con le implementazioni, typealias di `ArrayList`, invoke di un parametro funzione con receiver.
- `klaxon-jackson/src/main/kotlin/com/beust/klaxon/jackson/JacksonParser.kt:86 obj`: l'indice dà `KlaxonJson#obj(+2)` invece di `obj(Iterable)`. L'arco è `overload-across-tasks`, e fra i tre candidati c'è quello giusto.
- `klaxon/src/main/kotlin/com/beust/klaxon/Klaxon.kt:31 parse`: il bersaglio `Parser#parse(Reader)` è giusto. L'implementazione di `JacksonParser` è sbagliata ed è `override-across-tasks`.
- `klaxon/src/main/kotlin/com/beust/klaxon/JsonArray.kt:53` `it[key]` e `klaxon/src/main/kotlin/com/beust/klaxon/KlaxonJson.kt:30` `newMap[key] = ...`: buchi `implicit-operator`.

Pacchetti esterni (riferimenti):

| Pacchetto | Riferimenti |
| --- | --- |
| `unknown` kotlin | 1.220 |
| jdk 17 | 591 |
| `unknown` kotlin/collections | 459 |
| testng 7.0.0 | 359 |
| kotlin-stdlib 1.6.0 | 323 |
| assertj-core 3.10.0 | 237 |
| `unknown` kotlin/jvm | 170 |
| jackson-databind 2.9.6 | 71 |
| `unknown` kotlin/test | 68 |
| `unknown` kotlin/io | 52 |
| `unknown` kotlin/text | 49 |
| `unknown` kotlin/reflect/full | 46 |
| `unknown` kotlin/reflect/jvm | 38 |
| jackson-core 2.9.6 | 11 |
| `unknown` kotlin/sequences | 2 |
| annotations 13.0 | 2 |

Tempo e memoria, esecuzione di conferma (`spawn --stage index`, pipeline completa, codice uguale al checkout per hash):
- Indicizzatore 107,2 s e 2.205 MB il processo più grande; container 125,6 s; il solo grafo dal volume 3,3 s.
- Prima esecuzione: indicizzatore 111,0 s, compresi lo scaricamento di Gradle e la build (1m33s); 4.688 MB come somma dei processi del container, campionata ogni 0,5 s.
- Costo fatturato da Modal: 0,029 USD per un'esecuzione con l'indicizzatore e tre solo per il grafo, circa 0,016 per quella di conferma.

Gli archi incerti e le chiamate implicite li chiude la Kotlin Analysis API, una seconda fonte che il prodotto non usa (sezione 4).

Non verificato:
- Uno per uno, gli archi incerti che il numero di argomenti non smentisce.
- La regola dell'ordine compilato: osservata nei dati, non letta nel codice dell'Analysis API.
- Perché i task di scip-java non girano in buildSrc: lo dice solo il log.
- I picchi di RAM fra un campione e l'altro, sotto gVisor.
- Altri progetti Kotlin, Gradle 8 e oltre, Android, Kotlin Multiplatform.

### C: zlib

scip-clang indicizza zlib con la build CMake del progetto. È l'unico produttore SCIP mantenuto per C e C++: lsif-clang, il suo predecessore, scrive LSIF ed è fermo; clangd non esporta SCIP. Nel prodotto l'adattatore è `daodan/core/indexers/clang.py`; questa misura usa `adapters/clang.py`, che serve C e C++, e `lang_clang.py`, che collega adattatore, lettura comune e volume. Esecuzione: `modal deploy benchmarks/inference-audit/lang_clang.py`, poi `python benchmarks/inference-audit/lang_clang.py spawn` e `fetch`; `fetch --files DIR` e `graph --case zlib --dir DIR` rifanno il grafo dai file sul volume (`inference-audit/graph-clang/<caso>/`) senza rieseguire l'indicizzatore. `spawn --fixtures` e `fetch --fixtures` rifanno gli indici delle fixture. Risultati: `results/graph-c-zlib.json` e `results/graph-c-zlib-checks.json`.

| Parametro | Valore |
| --- | --- |
| caso | zlib 1.3.1 `51b7f2abdade71cd9bb0e7a373ef2610ec6f9daf` (CMake): 3.396 chiamate, puntatori a funzione nello stream e nella tabella di configurazione, macro fitte, molti `#ifdef`, `contrib/` ed `examples/` che il build non compila |
| indicizzatore | scip-clang v0.4.1 (LLVM 21, rilasciato il 22 ottobre 2026), binario della release con sha256 verificato, `--jobs=4`; Ubuntu 24.04 con gcc 13 e CMake. Le note dicono Debian 10 o più, ma il binario vuole glibc 2.38: su Debian 12 (2.36) non parte (prima esecuzione) |
| database di compilazione | `cmake -S . -B build -DCMAKE_EXPORT_COMPILE_COMMANDS=ON -DCMAKE_BUILD_TYPE=Debug`, poi `cmake --build`, su una copia nel container: il configure esegue gli script del progetto. 34 comandi su 17 file: ogni file è compilato due volte (libreria condivisa e statica, `example` ed `example64`) |
| pacchetti | una mappa di pacchetti: la radice è `zlib@51b7f2abdade`, ogni cartella delle include di sistema il pacchetto Debian che ne possiede più file (162 voci; due cartelle miste) |
| snapshot del prodotto | allora nessun file C o C++: `snapshot.py write` elencava 42 file di zlib, nessuno `.c` o `.h`. Oggi lo snapshot li legge («Lettore C e C++ dello snapshot»); i risultati salvati restano misurati con il sostituto |
| riferimenti indipendenti | al posto dello snapshot, tree-sitter: perimetro (file tracciati da Git, cartelle punto escluse), funzioni, classi e prototipi dichiarati, chiamate (`call_expression`, `new_expression`, cast scritti come chiamate esclusi) |
| verifica a mano | 20 chiamate lette nel sorgente prima del grafo (`HAND_CHECK` in `lang_clang.py`) |

Cosa l'adattatore aggiunge a quello che scrive l'indice:
- `SyntaxSnapshot`: tree-sitter fa le veci dello snapshot del prodotto, che allora non leggeva C né C++; le macro di annotazione (`int ZEXPORT inflate(`, `class TINYXML2_LIB XMLNode`) sono sostituite da spazi prima del parsing, posizioni invariate (349 in zlib);
- `dedupe`: un file compilato da più unità arriva come più documenti, che la lettura comune accoda; 20.031 occorrenze ripetute su 35.993;
- `utf8_columns`: l'indice non dichiara la codifica delle posizioni e le scrive in byte UTF-8, la lettura comune le prende come UTF-16 (provato sulle righe non ASCII delle fixture);
- `enclose`: l'indice non scrive intervalli di definizione; ogni funzione e classe prende quello del suo nodo sintattico (176), così un arco parte dalla funzione e non dal file;
- `same_range`: scip-clang scrive tutto ciò che una macro espande sul nome della macro, e il costruttore di una dichiarazione sul nome della variabile; una variabile definita lì non è mai alias (770 coppie), solo una using-declaration lo è;
- `hops`: `declaration` (una funzione che l'indice non definisce va al suo prototipo nel progetto), `lambda` (C++, sotto); `refine`: un simbolo con corpi in più punti dà archi incerti con i candidati.

Copertura: 69 file C nel perimetro, 27 con occorrenze, più `build/zconf.h` generato dal build. I 42 senza documento:
- 24 sorgenti senza comando di compilazione: 14 in `contrib/`, 9 in `examples/`, `test/infcover.c`;
- 17 intestazioni incluse solo da quelli;
- `zconf.h`: il configure di zlib lo rinomina `zconf.h.included` nella copia e genera `build/zconf.h`, che è indicizzato al suo posto. I suoi simboli sono del progetto (valore, "generato dal build").
- In più 5 file C++ di `contrib/iostream*`, senza comando.

L'indice: 28 documenti, 15.962 occorrenze dopo la fusione, 1.777 definizioni, 1.427 `SymbolInformation`; nessuna relazione oltre a 726 simboli esterni, nessun ruolo oltre a `definition`.

Nodi: 1.874. Simboli del progetto: funzioni 167, macro 209, campi 167, variabili 1.137 (quasi tutte locali), tipi 58, moduli 55 (file e intestazioni). Esterni: 33 funzioni, 29 macro, 5 tipi, 3 variabili.

Archi: 14.137.

| Fine | Archi | Catene |
| --- | --- | --- |
| funzione o tipo del progetto | 583 | tutte a 0 salti |
| valore del progetto | 12.913 | |
| esterno | 579 | |
| namespace (file di intestazione) | 53 | |
| vicolo cieco | 9 | |

Le 3.396 chiamate:

| Esito | Chiamate |
| --- | --- |
| file senza documento | 2.125 |
| funzione del progetto | 386 |
| esterna | 257 |
| solo valori | 370: 356 macro che non espandono una chiamata a funzione, 11 cast C scritti come chiamata (`(Byte)(x)`), 1 campo, 1 parametro, 1 funzione che tree-sitter non riconosce |
| nessuna occorrenza | 257 |
| nessuna posizione | 1 (`contrib/minizip/ioapi.c:58`) |

Buchi senza occorrenza, per causa:
- 234 in un ramo `#if` senza alcuna occorrenza, cioè non compilato: `crc32.c:237` `atomic_load`, `deflate.c:1578` `putc`, `test/minigzip.c:195` `deflateEnd`;
- 16 dentro gli argomenti di una macro: l'indice li scrive sul nome della macro, non dove stanno. `deflate.c:905`, `:1161`, `:1239`, il cast `(Byte)` dentro `put_byte(...)`;
- 6 dentro argomenti che l'espansione scarta: `trees.c:229` e `:917` `isgraph` in `Tracecv`, vuota senza `ZLIB_DEBUG`;
- 1 altro: `gzlib.c:233` `_wopen`, in un `#ifdef` dentro un'espressione.

Casi propri di C:
- Macro: una chiamata dentro una macro è scritta sulla chiamata della macro, quindi `UPDATE_CHECK(...)` arriva a `crc32` e `adler32`, `zmemcpy(...)` a `memcpy`, `deflateInit(...)` a `deflateInit_`; nessun salto serve.
- Puntatori a funzione: 46 chiamate contate nel sorgente, tutte finiscono sul valore (campo o parametro), nessuna indovinata. 2 dirette (`deflate.c:1185` `func`, `infback.c:612` `out`), 44 attraverso macro (`ZALLOC` 15, `ZFREE` 7, `TRY_FREE` 4, in `infback.c` `PULL`, `PULLBYTE`, `NEEDBITS` e `ROOM` 18).
- Dichiarazione e definizione: un simbolo per funzione, definito al corpo, il prototipo è un riferimento. Ogni funzione del progetto ha il corpo in un file compilato, quindi 0 salti `declaration`.
- Rami non compilati: `crc32_z` ha due corpi, sotto `#ifdef ARMCRC32` e nel suo `#else`; l'indice tiene solo quello attivo (`crc32.c:694`).
- Archi incerti: 4, su 2 chiamate. `fixedtables` è `static` sia in `infback.c:76` sia in `inflate.c:252`: scip-clang dà ai due un solo simbolo, quindi ogni chiamata porta i due candidati (`infback.c:296`, `inflate.c:843`).
- Vicoli ciechi: 9, macro di `zlib.h:1878-1880` (`gzopen` per `gzopen64`), attive solo nelle unità `*64`. Di ogni intestazione l'indice tiene un solo documento, da un'unità dove quel ramo è spento.

Esterni: 375 archi senza pacchetto, 195 `libc6-dev` 2.39, 9 `libgcc-13-dev`. Una funzione solo dichiarata in un'unità ha pacchetto vuoto (`cxx . . $`): `exit`, `fprintf`, `memcpy`, `free`, `strlen`. Dalla mappa ricevono il pacchetto solo tipi, macro e file di intestazione di sistema, quindi per le funzioni della libreria C l'indice non dà identità.

Verifica a mano: 20 su 20.
- I casi: funzioni `static` e di altri file, macro con e senza chiamate dentro, macro a tre definizioni sotto `#ifdef`, macro catena (`send_bits`, `put_short`, `put_byte`), puntatore in tabella e parametro callback, funzione con due corpi sotto `#ifdef`, chiamata in un ramo non compilato, libreria C (`malloc`, `open`, `strerror` con `__errno_location` da `errno`), file compilato due volte.
- Una correzione dopo r1, solo al conteggio: `valore` vuol dire che nessuna funzione è raggiunta, e il primo conteggio trattava un tipo esterno come non valore (`trees.c:775`).

Tempo e memoria, esecuzione r5:
- configure 2,0 s, build 2,1 s, indice 0,7 s: 4,8 s in tutto;
- snapshot 2,0 s, container 12,4 s;
- RAM: 69 MB il processo più grande (scip-clang), 402 MB la somma dei processi del container.

L'indice non è uguale da un'esecuzione all'altra: su cinque esecuzioni fino a 57 occorrenze su circa 16.000 cambiano (0,4%), perché di un file compilato più volte vince la copia di un'unità o dell'altra (`<limits.h>` di glibc o di gcc, le macro di `stddef.h`).

Costo fatturato da Modal per l'app `daodan-graph-clang`: 0,088 USD in tutto, per le fixture e cinque esecuzioni per caso; ogni esecuzione di un caso costa meno di un centesimo.

Non verificato:
- altri generatori del database (Bear, Meson): i due casi usano CMake;
- le opzioni di sviluppo di scip-clang (`--help-all`), fra cui una per indici stabili;
- i 37 tipi che tree-sitter non dichiara: dagli esempi sono `typedef` (`zutil.h:39` `uch`), non tutti controllati;
- i 2 corpi che tree-sitter non riconosce (`deflate.c:635` `deflateResetKeep`, `trees.c:995` `_tr_flush_block`): le loro chiamate finiscono su un valore;
- i picchi di RAM fra un campione e l'altro (due al secondo).

### C++: tinyxml2

Stesso indicizzatore, adattatore e driver di zlib. Risultati: `results/graph-cpp-tinyxml2.json` e `results/graph-cpp-tinyxml2-checks.json`. Fixture: `fixtures/c` e `fixtures/cpp`, con l'indice scritto da scip-clang, provate in `test_clang_graph.py` (45 prove).

| Parametro | Valore |
| --- | --- |
| caso | tinyxml2 11.0.0 `9148bdf719e997d1f474be6bcc7943881046dba1` (CMake, libreria e `xmltest`): 2.380 chiamate, gerarchia virtuale (`XMLNode`, `XMLVisitor`), 50 nomi sovraccaricati, template (`DynArray`, `MemPoolT`), operatori, costruttori e distruttori, namespace |
| database di compilazione | 2 comandi su 2 file; `contrib/html5-printer.cpp` non è compilato |
| snapshot del prodotto | 206 file, nessuno C o C++ |
| verifica a mano | 20 chiamate lette nel sorgente prima del grafo |

Copertura: 4 file nel perimetro, 3 con occorrenze; manca `contrib/html5-printer.cpp`, senza comando. L'indice: 3 documenti, 9.849 occorrenze (15 ripetute), 2.010 definizioni, 845 `SymbolInformation`. Relazioni: 70 `is_implementation`, 61 `is_reference` (la lettura comune non le legge), 247 simboli esterni.

Nodi: 2.063. Simboli del progetto: metodi 412, classi 31, funzioni 12, campi 88, variabili 1.448, macro 11; 26 metodi riferiti e mai definiti.

Archi: 7.978.

| Fine | Archi | Catene |
| --- | --- | --- |
| funzione, metodo o classe del progetto | 3.736 | 3.573 a 0 salti, 163 a 1: implementazione 139, `declaration` 24 |
| valore del progetto | 4.133 | |
| esterno | 80 | |
| namespace | 21 | |
| vicolo cieco | 8 | |

Le 2.380 chiamate (76 cast scritti come chiamata esclusi):

| Esito | Chiamate |
| --- | --- |
| metodo o funzione del progetto | 1.999 |
| del progetto, con le implementazioni | 75 |
| esterna | 6 (`va_start`, `va_end`) |
| solo valori | 155: 153 macro (`TIXMLASSERT`, sotto), 2 variabili |
| nessuna occorrenza | 135 |
| file senza documento | 10 |

Buchi senza occorrenza, per causa:
- 91 chiamate alla libreria C: `printf` 28, `fclose` 10, `fopen` 9, `strlen` 7, `memcpy` 5, `clock` 5 (`tinyxml2.cpp:198`, `:201`, `xmltest.cpp:708`). In C++ scip-clang non scrive nessuna occorrenza per una funzione dichiarata `extern "C"`, né la definizione, né il prototipo, né le chiamate. La fixture lo conferma con una funzione `extern "C"` del progetto (`c_helper`);
- 29 in rami `#if` senza occorrenze, codice solo MSVC: `tinyxml2.cpp:47` `va_start`;
- 13 dentro gli argomenti di una macro, scritti sul nome della macro: `tinyxml2.cpp:2249` `CurrentAllocs` e `Untracked` dentro `TIXMLASSERT(...)`;
- 2 chiamate esplicite di distruttore: `tinyxml2.cpp:1199` `node->~XMLNode()`, `:2024`. L'indice riferisce la classe, non il distruttore.

Casi propri di C++:
- Virtuali: 34 simboli, classi e metodi, con implementazioni dichiarate. Le 75 chiamate con dispatch portano il metodo di base e ogni override (`node->Accept(visitor)` sei); una chiamata con tipo statico senza override porta solo quello (`PrintSpace`).
- Overload: 50 nomi con più simboli; ogni simbolo ha un hash della firma, la scelta è del compilatore (`SetAttribute(int)` fra otto, `FirstChildElement` non const, `XMLTest` fra tre overload e un template).
- Template: un simbolo per template, nessuna istanza. Membri di un template di classe giusti (`Push`, `Free` di `MemPoolT`), anche su un tipo dipendente (`pool.Alloc()`). `new (...) NodeType(this)` finisce sul parametro di template: il costruttore dipende dall'istanza, nessuno è scelto.
- Costruttori: riferiti sul nome della variabile (`XMLDocument doc;`) o dove inizia il tipo in un `new`. Il costruttore di un template di classe ha due simboli, `DynArray<T, INITIAL_SIZE>` alla definizione e `DynArray(...)` ai riferimenti: 8 archi in vicolo cieco.
- Distruttori: 14 definiti, 7 riferiti, scritti sul solo `~`.
- Operatori: 4 definiti, 15 riferiti, sul simbolo dell'operatore (`_unlinked[i]`, `operator[]`).
- Lambda: nessuna in tinyxml2. Sulla fixture, la variabile `auto` che tiene una lambda arriva alla lambda con il salto `lambda`; l'`operator()` della chiusura, riferito sulla parentesi, non è mai definito (vicolo cieco).
- Using e namespace: 3 using-declaration, nessuna di nomi (alias 0); sulla fixture `using geo::twice;` arriva al template con un salto di intervallo condiviso. I namespace sono 21 archi `namespace`.
- Prototipi senza corpo: 24 salti `declaration`, costruttori di copia e assegnazioni privati mai definiti. L'indice dà loro pacchetto vuoto come a ogni funzione solo dichiarata.

Esterni: `libc6-dev` 58 archi, `libgcc-13-dev` 12, senza pacchetto 10. Le funzioni di `libstdc++` hanno il pacchetto (`std::printf`, `push_back` nella fixture); tinyxml2 non ne chiama.

Verifica a mano: 16 su 20.
- I quattro sbagliati: tre funzioni C dietro `extern "C"`, assenti dall'indice: `TIXML_SNPRINTF` per `snprintf`, `TIXMLASSERT` per `assert`, cioè `__assert_fail`, e `printf` (`xmltest.cpp:166`). Il quarto è la chiamata esplicita `node->~XMLNode()`, di cui l'indice riferisce la classe.
- Giusti: dispatch con sei override, overload anche su `const`, template e membri dipendenti, operatore, costruttori, `static`, template contro overload.
- Una correzione dopo r1: gli override di `Visit` e `VisitEnter` nella classe `TestUtil`, locale a `main` in `xmltest.cpp` (`:2567`, `:2584`), mi erano sfuggiti; confermati dal sorgente.

Tempo e memoria, esecuzione r5:
- configure 1,0 s, build 1,5 s, indice 0,4 s: 2,9 s in tutto;
- snapshot 6,7 s, container 15,8 s;
- RAM: 83 MB il processo più grande (il compilatore nel build), 61 MB scip-clang, 225 MB la somma del container.
- Fra le esecuzioni cambiano fino a 8 occorrenze su 9.849.

Non verificato:
- un progetto C++ con template pesanti (fmt, nlohmann/json), lambda e `using` di nomi oltre alla fixture;
- perché scip-clang perde `extern "C"`: visto sulla fixture e su tinyxml2, non cercato nel suo sorgente;
- i 26 metodi riferiti e mai definiti, oltre ai costruttori dei template e ai prototipi privati.

### Lettore C e C++ dello snapshot

Lo snapshot del prodotto legge C e C++ (`daodan/core/languages/cfamily.py`, prove in `tests/test_codebase_map_clang_reader.py`) e passa al lettore le macro dei file con cui un file condivide un'unità di traduzione: ciò che include e chi lo include. Il lettore toglie le macro che il sorgente definisce come decorazione (`#define local static`, `FAR`) o come involucro di un prototipo (`OF((args))`). Un nome che arriva da un header incluso porta alla sua unica definizione con collegamento esterno. Misurato in locale il 14 novembre 2026.

| Parametro | Valore |
| --- | --- |
| fixture | `test_clang_graph.py` gira anche sullo snapshot del prodotto: fini uguali in C 17 su 17, in C++ 14 su 15 |
| la differenza | `new geo::Square(3.0)`: lo snapshot legge la chiamata su `Square` (8:33), dove l'indice nomina la classe; il sostituto la legge dove inizia il tipo (8:28), dove nomina il costruttore |
| zlib `51b7f2abdade` | 74 file letti, 66 C e 8 C++ (`contrib/iostream*`); file C senza fatti semantici 12 su 66; 2.278 chiamate nei file con fatti, 510 risolte (470 nel file, 40 per include); 9,7 s |
| chiamate senza definizione | 198, verso funzioni di `zlib.h` definite in uno dei 12 file senza fatti (`inflateEnd`, `inflate`, `gz_error`, `deflate`) |
| tinyxml2 `9148bdf719e9` | fatti per 3 file su 4 (`xmltest.cpp:336` diviso da un `#if`); nessuna chiamata risolta per include, perché le funzioni libere stanno nel namespace `tinyxml2` o nei corpi dei membri |
| cosa resta | 9 file per un `#if` che divide un'istruzione (`gzlib.c:187`, `inflate.c:196`, `infback.c:45`, `puff.c:494`, `miniunz.c:630`, `unzip.c:1897`, `deflate.c:184`, una funzione di `trees.c` e una di `zip.c`); 3 per parole di un compilatore in un ramo spento (`ioapi.h:87`, `zutil.h:98`, `testzlib.c:20`). Per entrambi serve il ramo che il build sceglie, cioè l'indice |

Senza le macro degli include i file C di zlib senza fatti erano 37 su 66, e le chiamate risolte 303 su 1.523.

### Fogli di stile

**Stato:** In uso nel prodotto come stage `stylesheet` (`daodan/core/indexers/css.py`, un adattatore per motore con il suo `.js`, motori fissati in `indexers/css_engines/`). Le misure di questa sezione sono del 14 novembre 2026, con il lettore CSS scritto a mano che il prodotto aveva allora (`languages/stylesheet.py`). Il CSS semplice oggi si legge con `@eslint/css-tree`: la misura sugli stessi casi con il codice di oggi, nodi, archi e buchi, è in [`css-parser`](../css-parser/README.md), che dichiara i file `results/graph-css-*` di questa cartella «older runs of other code». Qui restano la definizione del grafo, gli strumenti valutati, le classi dei buchi per caso e ciò che manca.

Nessuno strumento esistente collega i nomi CSS fra file e markup: gli strumenti leggono e dicono cosa c'è; il collegamento per nome lo fa `css.graph`, con gli ambiti di Sass e dei CSS Module.

#### Che cos'è il grafo di un foglio di stile

Non ci sono chiamate: ci sono nomi che la cascata risolve quando la pagina gira.

- Nodi: regole (per selettore appiattito, con le at-rule intorno), `@keyframes`, `@font-face` (per famiglia), `@property`, dichiarazioni di proprietà custom (`--x`, nei fogli, negli attributi `style`, negli oggetti `style` e in `setProperty` degli script, nelle proprietà arbitrarie Tailwind `[--x:...]`), nomi di container, prima comparsa di un `@layer` nel file, variabili e mixin Sass, file. Le utility Tailwind sono nodi esterni (pacchetto e versione).
- Fogli esterni: un foglio che il progetto carica da fuori dello snapshot (un pacchetto in `node_modules`, un file del checkout fuori perimetro come `vendor/`, un link CDN) è letto come esterno. I nomi che dichiara diventano nodi esterni (`<foglio> .classe`, `<foglio> --x`, `<foglio> @keyframes x`), creati solo quando un riferimento li raggiunge.
  - Pacchetto e versione: dal `package.json`, dall'URL della CDN (jsDelivr, unpkg, cdnjs), dal commento iniziale (`/*! Font Awesome Free 6.4.0 ...`) o dalla cartella dopo `vendor/`. Altrimenti `unknown`. Il campo `from` dice da dove vengono.
- Classi e id non sono nodi del progetto. Sono nomi portati dalle regole: l'arco va a ogni regola che li nomina. Le classi di un CSS Module sono nomi della regola con l'ambito del modulo.
- Archi nei fogli: `var(--x)` a tutte le dichiarazioni di `--x`; `animation` a `@keyframes`; `font-family` e `font` a ogni `@font-face` della famiglia; `@container` al nome; un `@layer` ripetuto alla sua prima comparsa (che fissa l'ordine); `@import`, `@use`, `@forward` al file; `composes` alle regole; `$x`, `ns.$x` e `@include` attraverso gli ambiti di `@use`, `@forward` e `@import`.
- Archi da markup e codice: `class`, `className`, `*ClassName`, `id`, `classList`, `setAttribute`, `clsx`, `classnames` e `tailwind-merge` (riconosciuti dal pacchetto che dichiara la funzione, mai dal nome), `@apply`, `@extend`, `styles.foo` dei CSS Module, `<link rel=stylesheet>` e `import './x.css'`.
- Un percorso URL (`/landing-assets/x.css`) va ai file del checkout che finiscono con la sua coda più lunga. La coda è il percorso intero, o almeno i suoi ultimi due segmenti. La regola è `url-suffix`; più file trovati danno archi incerti.
- Più dichiarazioni dello stesso nome. Per proprietà custom, keyframes e container la cascata ne sceglie una per elemento: sono archi `uncertain`, uno per candidato, ciascuno con la lista intera. Le regole di una classe e i `@font-face` di una famiglia valgono tutti insieme: archi certi.
- Buco: un nome che nessuno dichiara (`no-rule`, `undeclared`...). Il buco è `css-in-js` quando un oggetto di uno script ha una chiave selettore, con un blocco di dichiarazioni come valore, che nomina quella classe; `tailwind-named-group` per `group/x` e `peer/x`. Buco anche una classe costruita a runtime, con la sua forma: `template`, `concatenation`, `ejs` (solo il tag), `ejs-glued` (testo incollato al tag), `parameter`, `call`, `property`, `element-access`, `variable`. Mai una supposizione.
- File non letti: un foglio o un file di markup che nessun lettore prende va in `files.missing` con il motivo. `indexed` conta solo i file letti per intero.
- Dialetti: SCSS e Sass indentato con `sass-parser`, Less con `less`, Stylus con `stylus`, Vue, Svelte e Astro con i loro compilatori (blocchi `<style>` per dialetto, scoped, module, `:global`, `:deep`, `v-bind()`, `class:list`, `:class`, `class:name`). Restano fuori solo i linguaggi di template diversi da HTML ed EJS (Handlebars, Nunjucks, Twig, Pug, Liquid, Jinja).
- Regola di pagina: un'unità è una pagina HTML/EJS che nessun template include, con i suoi include, i fogli che linka o contiene, gli script che carica e i loro import; oppure un bundle di moduli che nessuna pagina carica, con i fogli importati e i blocchi `<style>` dei componenti. Un foglio porta i fogli che importa; Tailwind viene con il foglio che lo carica. Un arco di classe, id, proprietà custom, keyframes, font-face o container è certo se un'unità contiene sito e foglio del bersaglio; altrimenti resta, incerto, con `sheet-not-proven-loaded`. `@apply`, `@extend`, `:extend`, `composes` e `safelist` sono a compilazione: fuori dalla regola.
- CSS-in-JS: letto dal programma TypeScript, riconosciuto dal pacchetto che dichiara il nome. Template di styled-components ed emotion, oggetti di vanilla-extract, `EditorView.theme` di CodeMirror, Stitches, MUI `styled` e `sx`: le loro regole sono nodi. Un selettore con un'interpolazione non letterale è un buco `interpolated-selector` con la forma.
- Altre fonti di classi: `[class.x]`, `[ngClass]` e `[class]` di Angular, con `@Component` che lega template e fogli; le tabelle di `cva` e `tailwind-variants`; un helper del progetto (`cn`) che rende la chiamata di clsx o tailwind-merge sul suo parametro.
- Vue: una regola `scoped` arriva al markup del suo componente e, con catena `child-root`, all'elemento radice di ogni figlio che il suo template rende (anche attraverso un barrel `export { default as X } from "./X.vue"`); un nome dentro `:deep()` arriva al componente e a tutto ciò che sta sotto di lui, mai agli altri; `:global()` e i blocchi senza `scoped` sono globali; `<style module>` si legge da `$style.x`. Gli alias di `paths` del tsconfig (`@/x`, con catena `paths`) valgono per import di script e di fogli, anche dentro un blocco SCSS.
- `chain` dice la regola che ha portato al bersaglio: `literal-type` (tipo stringa letterale del checker), `initializer` (una const o una proprietà di un oggetto const), `clsx`, `classList`, `@apply`, `composes`, `style-object`, `css-text`, `url-suffix`.

Nel prodotto, in più rispetto al driver:
- Nessun adattatore installa o lancia un motore: riceve un runner, `runner(script, payload)`. Su Modal è `node_runner` di `lang_css.py`.
- Payload e uscite nominano i file con il percorso relativo alla radice del progetto, con `/`.
- Un'esecuzione senza dati porta `state` e `reason`: con `unavailable` il grafo si ferma con quella causa; con `failed` i file di quell'esecuzione restano fra i mancanti, con il motivo.
- `units` sono le unità che la pre-mappa afferma, accanto a pagine e bundle presi dagli import.
- I fogli CDN sono un dato in ingresso, `remote`: il lettore non scarica nulla. Senza il testo del foglio, un nome che nessun altro dichiara è un buco `remote-sheet` con l'URL. `lang_css.py` passa `remote` vuoto.
- `rows` dà le righe dello store, tutte sotto l'etichetta `stylesheet`; la fine è `external`, `namespace` (un file) o `project-value`. Un sito senza righe è una violazione.
- TypeScript è sempre il 5.9.3 fissato con i motori, mai quello del progetto.

Test: `tests/test_codebase_map_css_graph.py`, sulle fixture di `tests/fixtures/css-graph/`, con archi, buchi e incerti scritti a mano prima del codice; le esecuzioni dei motori sono registrate su Modal (`lang_css.py fixtures`, `fetch --fixtures`) e rigiocate, quindi non servono né Node né npm.

#### Quale strumento dà cosa

| Strumento | Cosa dà | Usato |
| --- | --- | --- |
| parser del prodotto `languages/stylesheet.py` (CSS, SCSS, LESS) | albero delle regole: selettori appiattiti, contesto delle at-rule, layer, keyframes, mixin, import, `@apply` espanso | sì in questa misura; per il CSS semplice sostituito poi da `@eslint/css-tree` ([`css-parser`](../css-parser/README.md)) |
| `html.parser` della libreria standard | `class`, `id`, `style`, `<style>`, `<link>` di HTML ed EJS | sì |
| TypeScript del progetto (5.9.3), un programma | attributi JSX, `classList`, helper di classi, tipi letterali, inizializzatori const, import e membri dei CSS Module, oggetti `style`, `setProperty`, import di fogli, chiavi selettore degli oggetti | sì |
| Tailwind del progetto (3.4.19), `getClassOrder` col suo `tailwind.config.js` | quali token sono utility | sì |
| PostCSS (con selector e value parser) | l'albero di un file; niente fra file | no: lo stesso albero lo dà il parser del prodotto |
| `vscode-css-languageservice` | definizioni, riferimenti e link di un documento alla volta (`findReferences(document, position, stylesheet)`) | no: niente fra file, niente markup |
| API JS di Sass | `loadedUrls` (i file caricati) e la source map dell'uscita | no: dà i file, non variabili e mixin; tududi non ha Sass |
| `typescript-plugin-css-modules` | i tipi di `styles.foo` nell'editor | no: plugin del language service, non un'esecuzione unica; il compilatore basta |
| stylelint `no-unknown-custom-properties`, `no-unknown-animations` | sì o no su un nome, "nella stessa sorgente o nei `referenceFiles`" | no: un verdetto, non archi |
| `sass-parser` 0.5.6 (team di Sass, MIT) | l'albero del parser di Dart Sass per SCSS e Sass indentato, con espressioni, `@use`/`@forward` (prefisso, show, hide), flag delle variabili | sì: SCSS e Sass; il README lo dice in sviluppo, ma sui casi ha letto tutto tranne il getter `important`, che si evita |
| `postcss-scss` 4.0.9, `postcss-sass` 0.5.0, `sugarss` 5.0.2 | sintassi PostCSS senza i fatti Sass; `postcss-sass` è fermo al 2022; `sugarss` non è Sass | no |
| `less` 4.9.1 (Apache-2.0) | il parser di riferimento: variabili a ogni livello, mixin e chiamate, guard, `:extend`, opzioni di `@import`, `@plugin`, senza valutare | sì; la riga d'inizio di un mixin si prende dove il parser comincia a leggerlo, perché non la conserva |
| `postcss-less` 7.1.1 | la sintassi, con le chiamate di mixin come regole marcate | no: il parser di Less dice di più |
| `stylus` 0.64.0 (MIT, ultima uscita ottobre 2024) | l'unico parser di Stylus | sì |
| `@vue/compiler-sfc` 3.5.45, `svelte/compiler` 5.57.3, `@astrojs/compiler` 4.0.0 (MIT) | i blocchi, gli attributi e le espressioni dei template, gli import | sì; le espressioni di Astro e Vue sono testo, lette con acorn (dipendenza di Svelte) |
| Tailwind 4 (`__unstable__loadDesignSystem` di `@tailwindcss/node`) | il design system del foglio d'ingresso: `@theme`, `@utility`, `@custom-variant`, `@source`, `@plugin` | sì, con `getClassOrder` come per la 3 |
| indicizzatori SCIP o LSIF | nessuno per CSS (elenco nel README di SCIP) | — |

Nessuno dà il nome usato collegato alle sue dichiarazioni fra file e markup.

#### Casi, 14 novembre 2026

Giro di conferma con un solo hash di codice per tutti i casi (`css.py` `49854bf56415`; Bulma rigirato dopo la correzione dei keyframe in percentuale). Container da 2 CPU e 8 GiB; i progetti si clonano e installano solo su Modal (`npm ci --ignore-scripts`, o pnpm col suo lockfile quando npm non installa). Esecuzione: `modal deploy benchmarks/inference-audit/lang_css.py`, poi `python benchmarks/inference-audit/lang_css.py spawn --cases v3-admin-vite,tududi,bootstrap3,hn-svelte,saas-starter,bulma` e `fetch`. La verifica a mano sono 15 usi per caso (16 per hn.svelte.dev, 20 per tududi), con le attese scritte dal sorgente prima del grafo (`HAND` in `lang_css.py`). Costo fatturato da Modal: 0,3101 USD. La tabella completa dei buchi per classe, con gli esempi, è in `results/graph-css-<caso>-checks.json` (`summary.holes_by_class`).

| Caso | File trovati / letti interi | Verifica a mano | Buchi | Archi incerti (riferimenti) |
| --- | --- | --- | --- | --- |
| v3-admin-vite `c2c895d71d57` (Vue 3.5, SCSS scoped) | 131 / 131 | 15 su 15 | 21 | 425 (144) |
| tududi `71da9d7b34df` | 1.708 / 1.708 | 20 su 20 | 350 | 924 (667) |
| Bootstrap 3.4.1 `68b0d231a132` (Less) | 282 / 280 | 15 su 15 | 1.577 | 143.210 (7.234) |
| hn.svelte.dev `0010bbea0678` (Svelte 3) | 20 / 20 | 16 su 16 | 17 | 27 (13) |
| saas-starter `6e33e58b1e55` (Tailwind 4.1.7) | 43 / 43 | 15 su 15 | 39 | 1.279 (1.113) |
| Bulma 1.0.4 `e133d45b7a82` (SCSS con `@use`, `@forward`, mixin) | 602 / 602 | 7 su 11 | 7.778 | 8.846.500 (98.895) |
| styled-components-website `e70dc5c3f513` | non misurato qui | — | — | — |

I totali dei buchi di tutti i casi tranne tududi sono la somma delle classi nei file dei risultati.

**v3-admin-vite.**
- Nodi: rule 284, custom-property 167, custom-property external 80, module 68, variable 7, class external 6, module external 5, script-binding 4, keyframes 2, mixin 1.
- Archi: class external 12, class project 392, custom-property external 222, custom-property project 235, id project 6, import external 5, import project 26, keyframes project 2, mixin project 6, placeholder project 25, sass-variable project 12, script project 2, v-bind project 7.
- Buchi: `no-font-face` 8, proprietà custom non dichiarate 5 (`view-transition.scss:15 --v3-theme-x`), `no-rule` classe 3, `variable` classe 2, un selettore interpolato (`.#{$theme-name}`), uno `spread`, un import `virtual:uno.css`.
- `.vue` trovati 47, letti 47. Blocchi `<style>`: 36 scoped SCSS, 1 globale SCSS; nessun `module`, nessun CSS semplice.
- Archi delle classi dai template: 314 verso il componente proprio, 10 verso il padre con `child-root` (`.app-main` dei tre layout sulla radice di `AppMain`), 55 verso fogli globali importati da `main.ts`, 11 verso un altro componente (il blocco globale o un `:deep()` di un antenato), 10 verso fogli di pacchetti. Tutti certi.
- Regola di pagina: nessun arco `sheet-not-proven-loaded`. `index.html` carica `/src/main.ts`; da lì il grafo dei moduli arriva a ogni componente per import, router (`() => import("@/pages/...")`) e barrel. I 425 incerti sono della cascata: 421 proprietà custom con più dichiarazioni (temi chiaro, scuro, dark-blue), 4 variabili Sass dichiarate in più file.
- npm non installa senza un lockfile npm: è entrato il ripiego su pnpm (dal `pnpm-lock.yaml`, senza script).
- Snapshot del prodotto: per ogni `.vue` i simboli dello script e una regola per selettore dei blocchi `<style>`, con il selettore appiattito; non sa se un blocco è `scoped` o `module` e non legge le classi del template. Il resto (tipo dei blocchi, classi del template, `v-bind()`, padre e figli, alias, fogli da `main`, regola di pagina) lo vede solo il grafo.

**tududi.**
- Nodi: class external 1.849, rule 707, font-face 69, module 20, custom-property 13, keyframes 9, module external 2, layer external 2, font-face external 1.
- Archi: class external 37.158, class project 1.703, custom-property project 51, font-face external 1, font-face project 670, id project 1, import external 4, import project 3, include project 26, keyframes project 9, layer external 3.
- Buchi: `no-rule` id 98 (etichette, `aria` e ancore che nessun foglio nomina), `parameter` classe 68 (`TrialLockNotice.tsx:46 className`), `call` classe 67 (`NoteBackgroundPicker.tsx:42 swatch(!value)`), `no-rule` classe 55, `property` classe 28, `no-font-face` 9 (font di sistema), `property` id 6, `ejs-glued` 5, `element-access` 5, `ejs` 3 classi e 1 id, e cinque classi da un buco.
- I 55 `no-rule` di classe sono veri: classi senza effetto (`bg-black/2`, `text-md`, `max-w`, `transition-width`, `scrollbar-*` di un plugin non installato, `prose`, `dark:prose-invert` e `not-prose` con typography non configurato); agganci per JS e test (`task-list-container` 11 volte); `HabitCheckIn.tsx:154 ${ACCENT.solid}`, un errore di tududi: il segnaposto sta in una stringa normale e la classe accento non arriva mai.
- Font Awesome 6.4.0 sta in `vendor/`, fuori dallo snapshot, ma `head-assets.ejs:12` lo carica: è letto come foglio esterno (`url-suffix`), con pacchetto e versione dal commento iniziale.
- Le regole `cm-*` di `EditorView.theme` (`Note/editor/livePreviewTheme.ts`, `blockHandle.ts`) sono 69 archi; `group/x` va a `tailwindcss group` (catena `named-group`).
- I 7 archi da `sr-only` dell'app React a Font Awesome restano e sono incerti (`sheet-not-proven-loaded`): l'app non carica il foglio della landing.
- 26 archi `include` fra template EJS: le pagine della landing sono un'unità con i loro partial.
- 897 archi incerti per la regola di pagina: 639 verso Tailwind da sette file che il bundle dell'app non raggiunge (366 da `ProjectInsightsPanel.tsx`, 203 da `ProjectBanner.tsx`, poi due test), 144 verso `markdown.css`, 59 `@font-face` di `fonts.css` da pagine della landing; queste due ultime cause non sono indagate.
- Le 13 proprietà custom sono tutte negli script: 6 chiavi di oggetti `style`, 6 proprietà arbitrarie Tailwind, 1 `setProperty`. 27 archi incerti sono della cascata, su 3 letture di `--note-tint` con 9 candidati ciascuna.

Verifica a mano di tududi, 20 usi scelti leggendo il sorgente prima che esistesse un grafo; l'atteso «tutte le regole che nominano la classe» è contato da una scansione indipendente (`_rules_naming`):

| Gruppo | Giusti | Siti |
| --- | --- | --- |
| markup verso regole | 10 su 10 | `TabsNav.tsx:17 scrollbar-hide` (2 regole); `AreaDetails.tsx:357` `task-sheet-rails` (5) e `task-sheet` da `${TASK_SHEET_CLASS}` importata (15); `MarkdownRenderer.tsx:245 markdown-content` (36); `SidebarResizeHandle.tsx:60 classList.add(RESIZING_CLASS)`; `AdminGroupsPanel.tsx:621 line-clamp-1` (2 regole del progetto più l'utility); `TaskContentCard.tsx:111 prose` (buco); `nav.ejs:5 nav-wrap` (blocco `<style>` di `styles.ejs`); `App.tsx:337 classList.toggle('dark')` (19 regole più Tailwind); `HabitCheckIn.tsx:147 ${FORM.input} w-20` (19 utility da un oggetto const) |
| proprietà custom | 5 su 5 | `CaptureHost.tsx:151 --capture-dock-left` (dentro un valore arbitrario Tailwind); `NoteFocusMode.tsx:53 --note-tint` (6 siti); `CaptureHost.tsx:27` e `tailwind.config.js:11 --sidebar-width` (`setProperty`); `colorPalette.ts:72 --accent-light` |
| altri | 5 su 5 | `tailwind.css:18 spin` e `:37 border-pulse-dark` (keyframes); `styles.ejs:12` `Manrope` e `Inter` (24 e 35 `@font-face`); `Layout.tsx:12 import './styles/tailwind.css'`; `tailwind.css:121 @apply outline-none` (utility) |

**Bootstrap 3.4.1.**
- File: 2 mancanti con il motivo, `docs/_pug/customizer-nav.pug` e `customizer-variables.pug` (template language: no reader).
- Nodi: rule 2.775, class external 654, variable 399, module 264, mixin 115, module external 5, keyframes 2, font-face external 2, font-face 1, id external 1.
- Archi: class external 14.612, class project 130.517, font-face external 2, font-face project 1, id external 1, id project 31, import external 34, import project 137, less-variable project 1.521, mixin project 281, script project 95.
- Buchi: `no-rule` id 1.353, `no-rule` classe 118, script non risolti 56 (`../../dist/js/bootstrap.min.js`), `no-font-face` 22, selettori interpolati 15 (`.col-@{class}-pull-@{index}`), import non risolti 7 (`{{ site.cdn.css }}`).
- La lista a mano è stata corretta dopo il primo giro, rileggendo il sorgente: nominava un foglio che nessuna pagina carica (`dist/css/bootstrap.css`, citato solo in una stringa di un test JS), una riga sbagliata (`.starter-template` è alla 59) e un buco sbagliato per `.collapsed` (nessuna regola lo nomina, lo legge solo il JavaScript del plugin collapse).
- Un mixin definito dentro un altro mixin si cerca dallo scope più interno; i tag Liquid (`{{ }}`, `{% %}`) sono buchi `template-tag`.
- 143.165 archi incerti per la regola di pagina: le pagine caricano i fogli compilati di `dist`, mai i sorgenti Less. Che `dist/css/bootstrap.css` nasca da `less/bootstrap.less` lo dice il Gruntfile, non il codice dei fogli.

**hn.svelte.dev.**
- Nodi: rule 60, module 14, custom-property 6, keyframes 1.
- Archi: class project 48, custom-property project 24, keyframes project 1.
- Buchi: `no-font-face` 12, `no-rule` classe 3, un import non risolto, un `no-rule` id.
- Le regole di un componente arrivano solo al suo markup; `:global(html).dark .x` dà `dark` a tutti. Un composto aperto da `:global(...)` è globale per intero, come in Svelte.
- `src/template.html` linka `global.css`, che Sapper serve da `static/`: la convenzione non è nel codice, quindi buco `unresolved-import` e archi verso `static/global.css` incerti.

**saas-starter.**
- Nodi: class external 364, custom-property 177, rule 10, layer external 3, module external 2, custom-property external 2, variant 1, module 1.
- Archi: class external 1.063, custom-property external 8, custom-property project 222, import external 2, import project 1, layer external 5, variant project 9.
- Buchi: `parameter` classe 23 (`components/ui/card.tsx:9 className`), `no-rule` id 11, `no-font-face` 3, una `property`, un `no-rule` classe.
- Tailwind 4 letto dal suo design system (`@theme`, `@custom-variant dark`, `@import "tw-animate-css"` come foglio esterno).
- L'helper `cn` del progetto (tailwind-merge su clsx) è riconosciuto: le utility scritte nelle sue chiamate diventano archi; resta buco `parameter` il `className` passato dal chiamante.
- 1.050 archi `sheet-not-proven-loaded`: con l'App Router di Next.js il layout `app/layout.tsx`, che importa `globals.css`, avvolge le pagine per convenzione, senza import. Da leggere come regola di framework.

**Bulma 1.0.4.**
- Nodi: custom-property 56.445, rule 51.160, variable 991, module 507, keyframes 86, mixin 62, function 17, container 15, property 12, module external 12.
- Archi: class project 5.052.873, container project 807, custom-property project 3.791.991, function external 188, function project 1.520, id project 35, import external 36, import project 359, keyframes project 962, mixin project 374, module-member project 62, placeholder project 103, sass-variable project 2.905, script project 1.
- Buchi: proprietà custom non dichiarate 4.001, selettori interpolati 1.157, `no-rule` classe 1.072, `no-rule` id 268, funzioni non dichiarate 246, `no-font-face` 233, `template-tag-glued` classe 219, classi su selettori interpolati 165, import non risolti 127, mixin non dichiarati 81, e altre sedici classi sotto i 40.
- sass-parser 0.5.6 rifiuta un selettore di keyframe in percentuale (`0% { ... }`, «expected selector»), che Dart Sass legge. Dentro `@keyframes` quel selettore si scrive `to`, sulla stessa riga, prima del parser: il grafo non tiene i selettori dei keyframe, solo le dichiarazioni. Prova nella fixture `css-sass`.
- 8.852.216 archi, quasi tutti incerti per la regola di pagina: le pagine della documentazione linkano i fogli con URL Liquid (`{{ site.url }}/...`), che non si risolvono, quindi nessuna pagina prova di caricare un foglio; e il checkout contiene 14 copie compilate di Bulma (`css/`, `css/versions/`, `docs/assets/css/website.css`), ciascuna con tutte le regole.
- 1.157 buchi `interpolated-selector`: `.#{iv.$class-prefix}button` e simili. Il prefisso è una variabile di modulo con `!default`, che chi usa Bulma può cambiare: non è un valore letterale e locale, quindi buco per scelta.
- 246 `undeclared function` (`cv.getVar`) e 81 `undeclared mixin` (`mx.mobile`): i fogli di `docs/_sass` caricano `sass/utilities/...` per un load path di Jekyll (`_config.yml`), che non è nel codice dei fogli; l'import resta `unresolved-import` e lo spazio dei nomi è sconosciuto.
- Verifica a mano 7 su 11, quattro differenze, nessuna un errore del grafo: `.button` (la scansione conta anche `App.module.css:53`, che è una classe locale di un CSS Module); `.fas` (attesa sbagliata: `docs/_sass/docs/docs.scss:124` e `:162` nominano `.fas`); `.algolia-content` e `#js-menu-toggle` (nessuna regola li nomina, l'attesa «tutte le regole» doveva essere un buco: il grafo dà `no-rule` per l'id e `interpolated-selector` per la classe, perché un selettore costruito a compilazione che finisce con `content` potrebbe nominarla). Le attese sono lasciate come erano state scritte.

**styled-components-website.** Non misurato in questo giro: `npm install` fallisce con `EOVERRIDE` (gli `overrides` di npm contro una dipendenza diretta; il progetto usa pnpm), e il ripiego su pnpm rileggeva lo stesso `package.json`. Senza pacchetti il programma TypeScript non vede styled-components. Il caso è misurato in [`css-parser`](../css-parser/README.md), 12 su 15. Le 15 attese sono in `HAND` di `lang_css.py`; quelle su `error.tsx` stanno nello `<style>` dentro JSX, che il grafo non legge.

#### Che cosa manca

- Le convenzioni dei framework per il caricamento: il layout di Next.js sulle sue pagine, `static/` di Sapper, `styles` di `angular.json`, HtmlWebpackPlugin. Lì gli archi restano incerti.
- Lo `<style>` dentro JSX (`<style>{`...`}</style>`) e gli script inline delle pagine HTML: non letti.
- Le proprietà custom create a run time (`createTheme` di styled-components): buchi `undeclared`.
- Un selettore costruito da una variabile di modulo (`.#{iv.$class-prefix}button` di Bulma): buco, perché `!default` si può sovrascrivere.
- L'incapsulamento di Angular: le regole di `styleUrls` sono nomi globali.
- `@counter-style`, `anchor-name`, `@position-try`, `keyframes``…`` di CSS-in-JS: non letti.
- UnoCSS: le sue utility non sono lette (servirebbe il generatore di UnoCSS con il `uno.config.ts` del progetto, come per Tailwind); i loro token restano buchi `no-rule`. Neanche la modalità attributify (`un-` sugli attributi).
- Vue: i componenti registrati senza import (`unplugin-vue-components`, registrazione globale) non entrano nell'albero padre-figlio; `:slotted()` è letto come globale.
- Classi incollate a un tag EJS (`plan-step`, `compare-cell`, `lang-chip`, `nav-dd-item`, `nav-mobile-lang`): hanno regole ma restano buchi `ejs-glued`, perché l'uscita del tag non è valutata.
- Variabili e mixin Sass dei pacchetti esterni: non letti.
- v3-admin-vite non ha un lockfile npm: senza pnpm i fogli di Element Plus e vxe-table diventano buchi e i conteggi cambiano.

Non verificato:
- Gli archi di tududi fuori dai 20 siti: controllati i conteggi, le classi dei buchi e gli archi verso Font Awesome, non ogni arco. I 37.056 archi Tailwind valgono quanto il verdetto di `getClassOrder`.
- Che ogni token con tipo letterale sia davvero una classe: il tipo di un parametro dichiara i valori possibili (`literal-type` su 3.312 archi), ma con `strict: false` il tipo può mentire.
- I 42 attributi `style` uno per uno, e quelli con EJS dentro.
- Le tre regole di `tailwind.config.js` (`keyframes`, `animation`): stanno dentro l'esterno Tailwind, non sono nodi.
- Il download da CDN: nella fixture è un sostituto, su tududi non ci sono link CDN.
- Un caso Svelte 5 e uno Stylus reali: provati solo sulle fixture.
- Le due cause degli archi incerti di tududi verso `markdown.css` (144) e `fonts.css` (59).

## 2. Termine di confronto: l'indice contro il passo per posizione

Il prodotto chiedeva a un motore la destinazione di ogni chiamata, una posizione per volta (Jedi, typescript-language-server, rust-analyzer, Kotlin Analysis API). Quel passo non è più nel prodotto: ogni linguaggio si legge dall'indice, e lo stadio per posizione resta solo per un indice SCIP dato a mano (`resolve_edges.py --engine scip`). Il confronto resta perché è il motivo della scelta e perché dice che cosa l'indice non dà e il passo dava. L'indice è unito per posizione ai riferimenti dello snapshot e graduato con le stesse regole del passo (`grade_all`).

Chiamate con una destinazione del progetto (`results/scip-<caso>-confirm.json`, phazly `scip-phazly-final.json`, celle del confronto):

| Caso | Chiamate | Stesso bersaglio | Bersaglio diverso | Solo il passo | Solo il grafo |
| --- | --- | --- | --- | --- | --- |
| chi (Go) | 4.133 | 1.014 | 0 | 0 | 861 |
| semver (Rust) | 793 | 433 | 0 | 5 | 3 |
| tududi JavaScript | 72.890 | 12.709 | 0 | 58 | 119 |
| tududi TypeScript | 38.477 | 7.023 | 0 | 0 | 155 |
| phazly Python | 32.116 | 10.234 | 1 | 94 | 321 |
| phazly TypeScript | 15.160 | 3.257 | 0 | 0 | 329 |
| phazly JavaScript | 639 | 65 | 0 | 0 | 0 |
| phazly Rust | 29 | 0 | 0 | 0 | 1 |

Che cosa dava solo il passo, ogni classe con un dato assente dall'indice:

| Caso | Chiamate | Classe | Esempi |
| --- | --- | --- | --- |
| semver | 3 | `string.parse()`: l'indice dà `core str::parse`; rust-analyzer non scrive relazioni, quindi l'implementazione `FromStr` del progetto non c'è | `src/serde.rs:51`, `:77`, `:103` |
| semver | 2 | `tests/node/mod.rs`: nessun crate lo include, nessun documento | `tests/node/mod.rs:11`, `:42` |
| tududi JavaScript | 58 | metodi di un oggetto letterale di un altro file: scip-typescript dà al membro un `local` del suo documento, il chiamante tiene un `local` senza definizione (buco `dangling-local`) | `backend/modules/admin/service.js:1085`, `backend/modules/blog/hostSwitch.js:114`, `backend/modules/comments/routes.js:24` |
| phazly Python | 56 | ricevente senza tipo (parametro senza annotazione, fixture, attributo di un risultato): scip-python non scrive l'occorrenza; Jedi deduceva il tipo dai chiamanti o dagli assegnamenti | `functions-python/app/services/meal_images.py:166` `corpus.match`, `functions-python/tests/unit/test_api_keys.py:165` `fake_db.apiKeys.count_documents` |
| phazly Python | 29 | il grafo si ferma su un valore del progetto: spacchettamento di tupla 14 (`seed`, `build`, `request`), fixture pytest iniettate come parametro 13 (`repo_at`, `configured_billing_app`), attributo da un parametro del costruttore 1 (`self._food_loader`), nome preso da un indice 1 (`find_user`) | `functions-python/tests/unit/test_planner_revision_repository.py:2920` |
| phazly Python | 8 | file fuori dalla cartella indicizzata: i tre script di `react-app/scripts` | `react-app/scripts/store-art/finalize.py:134` `mean_rgb` |
| phazly Python | 1 | riesportazione via attributo di modulo | `functions-python/tests/unit/test_billing_regressions.py:2539` `play_billing.get_settings` |

Il bersaglio diverso di phazly Python è `functions-python/app/services/llm/providers/__init__.py:28` `provider.handles`: il passo dava il metodo del `Protocol` (`providers/base.py:37`), il grafo una sola delle due implementazioni, `providers/vertex.py:229`; manca `providers/openai_compat.py:98`.

Che cosa dà il grafo e il passo non dava (prima colonna da `results/scip-<caso>-confirm.json`, le altre da `-full.json`; fra parentesi le letture senza il lessicale e le chiamate che il passo non dava come esterne):

| Caso | Chiamate con destinazione solo dal grafo | Letture con destinazione (senza lessicale) | Esterne con pacchetto e versione, chiamate (il passo senza esterno) | Esterne, letture |
| --- | --- | --- | --- | --- |
| chi | 861: 463 mai chieste dal passo, perché il lessicale le lascia `unbound-name` (`ClientIPFromHeader` da un file di test dello stesso pacchetto, `chi.NewRouter`), 384 implementazioni, 14 funzioni tenute in un `local` | 173 (148) | 1.918 (8) | 526 |
| semver | 3 | 61 (58) | 337 (83) | 27 |
| tududi JavaScript | 119: 104 dove il passo rispondeva `binding` o `project-not-a-symbol` (`plans._resetCache`), 15 mai chieste | 1.546 (421) | 42.794 (25.624) | 2.629 |
| tududi TypeScript | 155: 145 per `declared:@types/react.useCallback`, dove il passo rispondeva `project-not-a-symbol` | 3.339 (599) | 22.357 (8.225) | 5.293 |

- Il passo non chiedeva le letture. Su phazly il grafo dà una destinazione del progetto a 2.878 letture Python (1.478 senza il lessicale), 1.616 TypeScript (933) e 3 JavaScript; esterni con pacchetto e versione nelle chiamate: Python 18.260, TypeScript 7.448, JavaScript 504, contro 11.239, 7.359 e 131 del passo, sempre senza pacchetto.
- Solo il grafo su phazly, letti 20 esempi per lingua. Python (317 prima delle due regole, ora 321; il passo rispondeva `project-not-a-symbol` o `ambiguous-target` in 132, un esterno in 112, niente in 73): metodi `@classmethod`, dove Jedi rispondeva con il decoratore (`functions-python/app/planner/proof.py:936` `Residual.between`); handler decorati da `@router.post`, dove Jedi dava il valore del decoratore; metodi su locali tipizzati, dove Jedi taceva (`proof.py:275` `r.as_dict`); 6 destinazioni ambigue per Jedi, una sola per il grafo. TypeScript (329, il passo `project-not-a-symbol` in 328): 15 funzioni avvolte in `useCallback`, 1 funzione dentro un oggetto, 4 azioni di uno slice zustand che arrivano al membro dell'interfaccia e non alla funzione eseguita.
- Prima delle regole `initializer` e `rebinding` phazly Python dava 10.202 stessi bersagli, 13 diversi (12 `generate` di `gateway.py` sul primo `@overload` invece che sull'implementazione), 114 solo dal passo e 317 solo dal grafo (`results/scip-phazly-before.json`).

Tempo e memoria (picco del processo più grande):

| Caso | Indicizzatore | Passo per posizione |
| --- | --- | --- |
| chi | 12,2 s, 335 MB | 56,4 s, 787 MB |
| semver | 8,7 s, 1.170 MB | 33,3 s, 1.094 MB |
| tududi | 62,5 s, 2.257 MB | 2.400 s, memoria non misurata |
| phazly | scip-python 72,4 s e 1.850 MB, scip-typescript 40,0 s e 1.834 MB, rust-analyzer 2,5 s e 891 MB | 2.347,3 s, 1.216 MB |

Copertura del passo su phazly in quell'esecuzione, risolte su risolvibili: Python 10.329 su 13.383 (77,2%), TypeScript 3.257 su 5.763 (56,5%), JavaScript 65 su 329 (19,8%), Kotlin 41 su 192 (21,4%), Rust 0 su 17. Le misure del passo sui tre casi di `flow-model`, con e senza ambiente, sono in [`call-provenance`](../call-provenance/README.md), sezione 4.

Non verificato: dei 56 riceventi senza tipo di phazly sono letti 20 esempi, e nel sorgente un caso per classe; i 6 siti che Jedi dava ambigui e il grafo dà con un solo bersaglio non sono controllati.

## 3. Lo stage del prodotto dà lo stesso grafo del benchmark

Il passaggio del prodotto legge ogni linguaggio dal suo indicizzatore (`engine_pass.ENGINES`, `index_stage`). `modal_stage.py` fa girare lo stage vero sul caso e, dallo stesso indice, scrive lo store come lo scrive il benchmark; poi li confronta.

### Go, Rust, JavaScript e TypeScript

| Parametro | Valore |
| --- | --- |
| casi | chi, semver e tududi, con snapshot e passo per posizione tenuti in `scip-inputs/<caso>` |
| voci | `scip-go`, `scip-rust`, `scip-typescript`; resolver `nome della voce@versione` |
| macchina | Modal, 4 CPU e 12 GB, solo il sistema di base: ogni stage scarica il suo indicizzatore |
| soglia | conteggi del grafo e celle del confronto con il passo per posizione uguali a `results/scip-<caso>-confirm.json`; store dello stage uguale riga per riga a quello del benchmark; ogni «solo passo per posizione» con una riga nello store; verifica a mano pari |
| risultati | `results/scip-{chi,semver,tududi}-stage.json` |

Risultati, con il codice del prodotto verificato per hash. Costo: 0,10 USD.
- Conteggi uguali: chi 4.847 nodi e 20.102 archi; semver 1.073 e 3.960; tududi JavaScript 86.225 e 182.593, TypeScript 41.107 e 171.821. Anche le celle del confronto con il passo per posizione sono identiche.
- Lo store dello stage è identico a quello del benchmark, riga per riga, in archi, buchi ed esterni.
- «Solo passo per posizione»:
  - chi 0 e tududi TypeScript 0;
  - semver 5: 3 archi esterni (`string.parse`, che l'indice porta a `core`) e 2 buchi `no-document` (`tests/node/mod.rs`);
  - tududi JavaScript 58, tutti buchi `dangling-local` (per esempio `backend/modules/admin/service.js:1085` `blogService.status`).
- Verifica a mano: chi 15 su 15, semver 15 su 15, tududi 26 su 30, come prima.
- Indicizzatore: scip-go 10,1 s e 318 MB; rust-analyzer 9,7 s e 1.172 MB; scip-typescript 59,1 s e 2.116 MB.
- Lo stage intero su una macchina nuova dura 54 s, 27 s e 885 s. Per tududi quasi tutto il tempo è installazione al primo uso: Node, scip-typescript e i pacchetti npm del progetto.
- Il test del passaggio TypeScript attraverso MCP (`tests/test_codebase_map_mcp_wire.py`, con l'SDK MCP vero, su Modal) dà la voce `fresh` con `scip-typescript@0.5.2`. In questa misura «risolte su risolvibili» dà 0 su 1, perché legge campi che solo il passo per posizione scrive; il prodotto non dà più quel numero.

### Python

`modal_stage.py --entries scip-python` fa girare solo lo stage di scip-python (`_serving`). Nel prodotto scip-python gira nelle cartelle che gli dà la pre-mappa; qui il driver gli dà i progetti Python (`UNITS`): l'adattatore non ne cerca.

| Parametro | Valore |
| --- | --- |
| casi | python-semver `b6e83e3e40d3a7570386e8d694ae8011477a55c1`, sulla copia con i link come file normali e sullo snapshot che `lang_python.py` tiene in `graph-python/semver-plugin` (`snapshot.py write` si ferma su un file linkato); phazly `46c92b28`, dall'archivio, con snapshot e passo per posizione in `scip-inputs/phazly` |
| unità | python-semver la radice; phazly `functions-python`, come il risultato salvato; un'esecuzione di scip-python per unità, con prefisso, nome, ambiente e configurazione di Pyright suoi |
| macchina | Modal, 4 CPU e 12 GB, solo il sistema di base |
| soglia | conteggi uguali a `results/graph-python-semver-plugin-checks.json` e `results/scip-phazly-final.json`; celle del confronto con il passo uguali; store dello stage uguale riga per riga a quello del benchmark; ogni «solo passo per posizione» con una riga nello store; verifica a mano pari |
| risultati | `results/scip-python-semver-stage.json`, `results/scip-phazly-stage.json` (phazly senza i log dell'indicizzatore) |

Risultati, codice del prodotto verificato per hash (`indexers/python.py` `3d8472aeb568`, `code_graph.py` `40bd846bcab4`):
- python-semver: 1.289 nodi e 3.679 archi, 64 buchi, 35 file su 35, come il salvato. Il controllo a mano dei 20 siti è identico. Lo store dello stage è identico a quello del benchmark, riga per riga. Il report differisce solo nei salti `initializer` (28): il risultato salvato viene da un `indexers/python.py` precedente alle regole `initializer` e `rebinding` (`f201bd46a865`), e 11 archi passano da un valore a una funzione del progetto.
- phazly: 35.662 nodi e 147.150 archi, 333 file su 336, come `scip-phazly-final.json`. Le celle del confronto con il passo sono identiche: stesso bersaglio 10.234, bersaglio diverso 1, solo passo 94, solo grafo 321. Verifica a mano 15 su 15. Lo store dello stage è identico a quello del benchmark, riga per riga.
- Le 94 «solo passo» nello store dello stage: 56 buchi `no-occurrence`, 8 buchi `no-document` (gli script di `react-app/scripts`, fuori da ogni unità), 1 buco `undefined-project-symbol`, 29 archi che finiscono su un valore del progetto (`project-value`: spacchettamento di tupla, fixture pytest, attributo dal costruttore, nome preso da un indice). Nessuna resta senza riga.
- Ambiente: 47 requisiti dichiarati, 116 pacchetti installati da Daodan (solo wheel) contro i 127 del benchmark, che installava anche da sorgenti. Mancano `aiohttp` e le sue dipendenze, `cbor2`, `grpclib`, `pip`; nessun esterno del grafo cambia.
- Indicizzatore: python-semver 9,4 s e 347 MB; phazly 91,0 s e 1.815 MB. `MIN_FREE` di scip-python è 1.920 MB, dal picco di phazly. Lo stage intero: 41 s e 136 s.

Cosa cambia negli id: la versione del progetto è `_` in ogni esecuzione, e il nome è quello dell'unità (`phazly-functions`, `semver`). Gli id del risultato salvato di python-semver contengono il commit (`semver b6e83e3e40d3`), quelli nuovi `semver _`: un confronto fra i due va fatto dopo aver sostituito la versione, come fa `against_confirm`.

Una prova con una sola esecuzione dalla radice e un `executionEnvironments` di Pyright per ogni progetto non regge. Su phazly il modulo di `functions-python` ha un nome dove è definito e un altro dove è importato: `app.api.deps/__init__:` resta senza definizione, e circa 2.200 archi `unknown` passano da un valore a un vicolo cieco. Le chiamate cambiano in 222 siti, quasi tutti in `run_tests.py` e `test_bootstrap/`. Per questo ogni unità ha la sua esecuzione, come i moduli di Go.

Costo fatturato da Modal: 0,192 USD, con quattro giri e la prova scartata.

### Java e Kotlin nel container del prodotto

`index()` di `daodan/core/indexers/java.py` e `kotlin.py` fa girare la build solo nel container, in due tempi: la preparazione con la rete aperta ai soli registri, poi l'esecuzione senza rete. Su Modal un container non si avvia, quindi gli stessi script girano nel container della funzione (`adapters/jvm_here.py`), con la stessa copia del perimetro e gli stessi strumenti portati da Daodan, dietro lo stesso proxy dei registri, che lì fa solo da controllo.

| Parametro | Valore |
| --- | --- |
| casi | javapoet e klaxon; `jvm-ver-gradle-tc21` della pipeline di `benchmarks/project-model` |
| immagine | la base che tutti i linguaggi condivideranno, `debian:trixie-slim@sha256:a72b4433de1cf7d6bae0c4cee74d0547f58601a643b3375f070c51600d63b6b2` (`preparation.IMAGE`), glibc 2.41, senza certificati di sistema; locale `C.UTF-8` |
| JDK | Temurin 17.0.21+9 (`preparation.TEMURIN`): Daodan lo scarica sull'host e lo verifica con lo sha256; la preparazione lo scompatta nel volume di stato e lo collega in `/opt/java/openjdk` |
| scip-java | 0.14.2: i 26 jar che coursier 2.1.24 risolve, ciascuno con il suo sha256 (`indexers.jvm.CLASSPATH`) |
| strumento di build | quello del wrapper, scaricato da Daodan e verificato; senza wrapper Gradle 9.9.1 o Maven 3.10.0. Nessun host di GitHub aperto, nessun `services.gradle.org` |
| soglia | conteggi uguali a `results/graph-java-javapoet-checks.json` (scip-java 0.13.2) e a `results/graph-kotlin-klaxon.json` |

Su Modal, 17 novembre 2026, codice verificato per hash, 0,068 USD con i test:
- javapoet: resoconto identico (3.541 nodi, 19.189 archi), verifica a mano invariata. Indicizzatore 28,6 s, picco 652 MB; 1.290 MB per tutti i processi.
- klaxon: i conteggi dell'indice sono identici: 15.940 archi certi, 238 e 13 incerti, gli stessi 7 file mancanti. Indicizzatore 100,9 s, picco 1.278 MB. Tre valori della lettura di Daodan sono cambiati rispetto al file salvato: un buco è lo stesso sito, che `334ea4d96` sposta da `no-position` a `computed-callee`; un file mancante ha la ragione scritta con altre parole; quattro archi passano da «project-value unknown» a «project-value read». La misura non separa la causa fra codice e immagine.
- `jvm-ver-gradle-tc21`: indice `fresh`. Il JDK 21 della toolchain lo installa mise sulla base senza certificati di sistema; l'indice nomina `jdk@21`. Il passo dinamico osserva 10 siti e 10 archi, con 2 test passati. 248 s.
- Test di `tests/test_codebase_map_indexers_jvm.py`, `test_codebase_map_dynamic_jvm.py` e `test_codebase_map_container.py`, in un container Linux: 169 passati e 19 saltati (le prove con un container vero, quelle solo per Windows e quelle che chiedono un JDK sul PATH).

Con l'immagine precedente, `eclipse-temurin:17-jdk-noble`, su Modal il 14 novembre 2026:
- javapoet: resoconto identico anche in archi per fine, buchi, pacchetti, `same_range` 9, `static` 3 e ordine degli overload 808 su 808; verifica a mano 20 su 20. La prima build fallisce come con la 0.13.2; la seconda, con il javac semplice, dà l'indice. Il proxy rifiuta `maven.java.net`, `oss.sonatype.org` e `repository.apache.org`, che la build chiede ma non usa.
- klaxon: ogni conteggio identico (15.940 archi certi, 251 incerti, buchi, 30 relazioni inverse tolte, verifica a mano 16 su 20). Gradle 7.3 è quello del wrapper, portato da Daodan, e il proxy non rifiuta nulla.

In un container vero, sul PC del proprietario (Kiri 0.2.0, CLI docker 29.9.2, `RealContainerSmokeTest`), 14 novembre 2026, con l'immagine di allora `eclipse-temurin:17-jdk-noble`:
- fixture Java senza wrapper: Maven 3.10.0 portato da Daodan e dipendenze da Maven Central attraverso il proxy; l'indice è scritto e le 7 attese di `expected.json` tengono. Con i due volumi con nome che la preparazione passa all'esecuzione: 22 s, indicizzatore 13,5 s e 584 MB; `system df`, strati, volumi e container di Kiri e il suo disco uguali prima e dopo, registro vuoto.
- la stessa fixture con `mvnw` in CRLF, senza bit di esecuzione, e `.mvn/` tracciato da Git: la copia porta `.mvn/` e il container chiama il Maven portato, senza scaricare distribuzioni. 15,6 s.
- fixture Kotlin, con un container da 4 GB: senza wrapper si usa il Gradle 9.9.1 portato da Daodan. Il plugin Kotlin 2.1.0 compila e le 7 attese tengono. 84 s; indicizzatore 63,4 s, picco 1.788 MB.
- wrapper di Gradle che indica `downloads.example.com`: `unavailable`, senza container e senza richieste a quel sito.
- impostazioni dell'utente uguali prima e dopo (PATH, configurazione e contesti di Docker, distribuzioni WSL).

Perché non l'immagine di rilascio di scip-java: 1.700 MB compressi e 2.748 MB su disco, di cui 1.538 MB la cache di coursier; il wrapper di Gradle vi scaricava da `services.gradle.org`, che rimanda a `github.com`; klaxon vi impiegava 130,2 s e 4.050 MB.

Cosa manca a questa misura:
- klaxon in un container vero;
- le fixture Java e Kotlin in un container vero sulla base comune, e la fixture Kotlin con i volumi, con `system df` uguale prima e dopo;
- la pre-mappa, C, C++, C#, TypeScript e Python usano ancora le loro immagini (`IMAGE` in `daodan/core/indexers/` e `premap/container_runner.py`).

## 4. Che cosa chiudono le seconde fonti statiche

**Stato:** Aperta: da approfondire. Nessuna di queste fonti aggiunge archi nel prodotto (controllato in `daodan/core/indexers/`: nessun callgraph di Go, nessun Jelly, nessun WALA; la Kotlin Analysis API è usata dall'indicizzatore, non per le domande mirate). Il checker di TypeScript gira dopo l'indice solo per dire perché un membro non ha occorrenza (`typescript_unbound.js`), e i `@types` mancanti li installa `typescript_types.py`. Le misure restano come base per decidere quali fondere.

### Go: grafo delle chiamate del programma intero

Domanda: l'analisi del programma intero di Go chiude i due buchi dell'indice di chi (quale funzione gira dietro un'interfaccia o un valore funzione) senza inventare archi?

| Parametro | Valore |
| --- | --- |
| motore | `golang.org/x/tools/cmd/callgraph` v0.52.0 (10 ottobre 2026), `-algo=vta -test`, Go 1.27.3, installato con `go install` (somme controllate dal database dei checksum) |
| perimetro | il modulo radice in un colpo: `./...` più le dieci cartelle `_examples/*` che il pattern salta; fuori i moduli annidati `_examples/rest` e `_examples/versions` |
| caso | chi `c64ed7d6`, con snapshot, indici e grafo già sul volume (`scip-inputs/chi/`) |
| unione | ogni chiamata dello snapshot va al sito che SSA dichiara: la `(` della chiamata, o la parola `go` / `defer` |
| file | `adapters/go_callgraph.py`, `strong_go.py` (app `daodan-strong-go`), `results/strong-go-chi.json`; l'uscita dell'adattatore resta sul volume (`strong-go-chi-callgraph.json.gz`) |

Esecuzione: `modal deploy benchmarks/inference-audit/strong_go.py`, poi `python benchmarks/inference-audit/strong_go.py spawn` e `fetch`.

Il grafo dell'indice è rifatto nel container con la lettura comune e gli `hops` di Go invariati: 20.102 archi, identici uno per uno a quelli sul volume.

Verdetto: chiude il buco dei valori funzione e restringe le liste delle interfacce; sulle chiamate dirette non contraddice mai l'indice. Si può unire per aggiungere e confermare, non per togliere: VTA vede solo i tipi che il codice del modulo crea. Una funzione esportata che il modulo non chiama non riceve archi, e un candidato scartato è "non raggiunto da questo modulo", non "impossibile" per chi usa la libreria. VTA a volte tiene candidati impossibili (prova a mano, sotto).

Uscita del motore: 84.072 archi (libreria standard compresa), 5.766 con il sito nel progetto, su 3.512 siti; 2.499 verso una funzione del progetto. Si legano 3.511 chiamate dello snapshot. Un solo sito non ha chiamata nello snapshot: `chain.go:45` `middlewares[i](h)`, 62 middleware; lo snapshot non registra quella chiamata.

1. Interfacce con implementazioni nell'indice: 537 siti, 1.122 candidati. Il motore ne tiene 885, ne scarta 237 (in 116 siti) e non aggiunge nessuna funzione del progetto. In 25 siti restano solo tipi della libreria standard. Altre 94 chiamate su interfacce senza implementazioni nell'indice: nessuna aggiunta.
   - `middleware/middleware.go:9` `h.ServeHTTP`: da 4 a 1, `middleware/middleware_test.go:27`, l'unico handler dato a `New`;
   - `middleware/recoverer.go:66` `recovererErrorWriter.Write`: da 2 a 0, restano `*os.File` e `*bytes.Buffer`;
   - `mux.go:90` `mx.handler.ServeHTTP`: da 4 a 2, via `chain.go:30` e `middleware/middleware_test.go:27`.
2. Valori funzione:
   - callee dinamici senza nome: 42 dei 43 analizzati (il 43° è in `_examples/versions`), 42 con un bersaglio del progetto. Sono 35 letterali chiamati sul posto (`defer func() {…}()`, `go func() {…}()`) e 7 chiamate di una funzione restituita: `chain.go:43` → 62 middleware, `middleware/request_id_test.go:48` `defer maintainDefaultRequestID()()` → `:15`, `middleware/maybe_test.go:19` → `middleware/maybe.go:9`;
   - valori del progetto (variabili, parametri, campi): 26 su 31 con un bersaglio. Le altre 5 sono chiusure della libreria standard (`cancel` di `context.WithCancel`, `stop` di `signal.NotifyContext`), risposta giusta;
   - funzioni tenute in un locale (salto `value`): 14 su 14, stesso bersaglio dell'indice;
   - esempi: `tree.go:913` `walkFn` → i 6 `WalkFunc` del programma, `middleware/throttle.go:155` `t.retryAfterFn` → `middleware/throttle_test.go:204` e `:280`, `middleware/client_ip_test.go:848` `buildReq` → `:343`, `:358`, `:372`.
3. Chiamate dirette: 2.832 siti, 2.797 uguali, 0 con bersagli diversi, 0 dove solo l'indice ha un bersaglio. I 35 dove solo il motore ne ha uno sono i letterali chiamati sul posto del punto 2, buchi per l'indice: `middleware/throttle.go:91` → `:89`, `middleware/timeout.go:41` → `:36`, `mux_test.go:1754` → `:1752`.
4. Cosa ha l'indice e il motore no:
   - moduli annidati: 197 chiamate in 7 file, 26 con un bersaglio del progetto (`_examples/rest/main.go:97` `adminRouter`, `_examples/rest/main.go:132` `dbGetArticleBySlug`, `_examples/versions/main.go:32` `articleRouter`);
   - conversioni di tipo, che per SSA non sono chiamate: 169, di cui 4 verso tipi del progetto (`chain.go:7` `Middlewares(…)`, `_examples/custom-handler/main.go:22` `Handler(…)`, `middleware/content_type.go:11` `http.HandlerFunc(…)`);
   - builtin: 255, muti per entrambi (`tree.go:202` `len`, `tree.go:508` `append`, `_examples/fileserver/main.go:50` `panic`);
   - funzione esportata che il modulo non chiama: 1, `middleware/page_route.go:14` `handler.ServeHTTP`. Nessun tipo arriva al parametro di `PageRoute`; l'indice elenca 4 implementazioni;
   - riflessione: nessuna perdita, chi usa `reflect` solo per confrontare funzioni (`tree.go:701`). Tag di build: solo `middleware/profiler.go` (`!tinygo`), compreso nella build di default. Il codice non raggiunto da un `main` è analizzato: VTA tipa ogni funzione;
   - file: 82 su 90 hanno almeno un sito. Gli 8 senza sono i 7 dei moduli annidati e `_examples/logging/main.go`, un `main` vuoto.
5. Prova a mano: 15 chiamate su interfacce o valori funzione, lette nel sorgente prima di ogni risultato (`HAND` in `strong_go.py`). Il bersaglio atteso è ogni funzione che può arrivare al valore chiamato lungo assegnamenti e chiamate, senza valutare le condizioni. Per l'indice contano le implementazioni, non il metodo dell'interfaccia.

| Fonte | Giuste | Sbagliate |
| --- | --- | --- |
| indice | 5 / 15 | i 9 valori funzione (nessun bersaglio) e `middleware/maybe.go:13` `wrapped.ServeHTTP` (4 implementazioni dove gira solo `http.HandlerFunc`) |
| motore | 14 / 15 | `middleware/maybe.go:13`: tiene anche `mux.go:63` e `_examples/custom-handler/main.go:12` |

L'errore del motore viene da come VTA lega le chiamate fatte tramite un valore funzione: usa un grafo CHA, cioè ogni funzione con la stessa firma. Così il risultato di `mw(next)` riceve i ritorni di tutte le `func(http.Handler) http.Handler`.

Motore: 5,5 s e 840 MB di picco (prima esecuzione 7,8 s e 879 MB); 13,6 s contando `go install` dello strumento; container 19,2 s. Costo fatturato da Modal: 0,016 USD per le due esecuzioni; i numeri sono della seconda, dopo la correzione del sito di `defer f()()`.

Non verificato:
- i 237 candidati scartati uno per uno (letti 4: `middleware/middleware.go:9`, `middleware/recoverer.go:66`, `mux.go:90`, `middleware/wrap_writer.go:102`);
- uno per uno, i 62 bersagli di `chain.go:43` e i 46 di `mux.go:283`;
- un secondo giro di VTA con il primo come grafo iniziale (solo da libreria, non dal comando), che potrebbe togliere l'errore di `maybe.go:13`;
- i moduli annidati analizzati a parte, i generici (il pacchetto `vta` si dichiara sperimentale e ha un TODO sulle istanze), altri progetti Go.

### Java e Kotlin: domande mirate e grafo dal compilato

Verdetto:
- Domande mirate (Kotlin Analysis API): sì, chiudono i casi di Kotlin. Tutti i 251 archi incerti di klaxon diventano certi e l'overload scelto è sempre fra i candidati del grafo; quello dell'indice è giusto solo in 14. Tutte le 93 chiamate implicite hanno un bersaglio. 2.258 domande in 9,5 s. Dei 2.104 riferimenti senza pacchetto, 831 finiscono in un jar con versione; 1.236 restano builtin di Kotlin, senza jar.
- Grafo dal compilato (WALA): non vale come potatura della dispatch. Con il test runner modellato, RTA su javapoet non toglie nulla oltre CHA. Su klaxon toglie solo implementazioni create per riflessione, che a runtime girano. Vale invece come controllo economico sull'indice, sulla build già fatta (17-22 s, 2,5-2,8 GB): toglie la dispatch dove non c'è (`==` di Kotlin, `super`, metodi astratti, tipo statico del ricevente).

Esecuzione: `modal deploy benchmarks/inference-audit/strong_jvm.py`, poi `python benchmarks/inference-audit/strong_jvm.py spawn` e `fetch --raw DIR`. `compare --raw DIR --graphs DIR --javapoet SRC --klaxon SRC` rifà il confronto in locale dalle risposte grezze, che restano sul volume in `inference-audit/strong-jvm/`. Risultato: `results/strong-jvm.json`.

| Parametro | Valore |
| --- | --- |
| casi | javapoet `b9017a9` e klaxon `1173bdc`, ricostruiti con la build dei grafi (`adapters/java.py`, `adapters/kotlin.py`); grafi e indice di klaxon presi dal volume |
| domande mirate | `adapters/kotlin_analysis.py` con `adapters/KotlinAsk.kt`, una copia del resolver della mappa (Analysis API di KSP 2.3.13, Kotlin 2.4.21, standalone). Un modulo sorgente per task di compilazione e un modulo libreria per jar, letti dai `kotlin-configs/` di scip-java. Ogni risposta dice callable, parametri, origine, posizione o jar. Modi: `ref` sull'occorrenza, `implicit` sulla riga, `overridden` sulla dichiarazione |
| grafo dal compilato | `adapters/jvm_callgraph.py` con `adapters/JvmCallGraph.java`, WALA 1.9.0 (30 ottobre 2026). Lambda e method reference passano da `LambdaMethodTargetSelector`; la riga viene dal program counter. SootUp 3.0.1 è scartato perché il suo CHA e RTA rilasciati non danno bersaglio a `invokedynamic` (`resolveCall` restituisce vuoto) |
| algoritmi | CHA, con i soli bersagli del progetto. RTA: ogni metodo concreto del progetto è un entry point che non alloca nulla, quindi conta solo il `new` raggiungibile. RTAT: lo stesso RTA, più il test runner che crea ogni classe concreta con `@Test` (JUnit, TestNG) su di sé, su un metodo o su una superclasse. JDK dai jmods di Temurin 17, meno `EXCLUSIONS` |
| confronto | per riga e nome del metodo. Un'implementazione dell'indice diventa una classe JVM dai descrittori se è globale, dalla posizione se è locale. Un `$default` si segue per un passo |
| verifica a mano | 20 siti scritti dal sorgente prima di leggere le risposte (`HAND_CHECK` in `strong_jvm.py`) |

Domande mirate su klaxon: 2.258 domande (2.166 `ref`, 86 righe `implicit`, 6 `overridden`).
- Archi incerti: 251, tutti certi, l'overload scelto sempre fra i candidati.
  - 238 `overload-across-tasks`: l'indice ha l'overload giusto in 14 (3 diretti, 11 implementazioni), un altro candidato in 224 (213 diretti, 11 implementazioni).
  - 13 `override-across-tasks`: tutti verso l'altro candidato, `JacksonParser.parse(Reader)` a `JacksonParser.kt:38` e non `parse(StringBuilder)` a `:29`.
  - Esempi: `JacksonParser.kt:86` `obj` va a `KlaxonJson.kt:19` (indice `:25`); `JacksonParser.kt:95` `array` a `KlaxonJson.kt:14` (indice `:17`); in `Klaxon.kt:24` l'implementazione è `JacksonParser.kt:38` (indice `:29`).
- Chiamate implicite: 93, tutte con un bersaglio.
  - kotlin-stdlib 1.6.0: 30 (`set` 21, `iterator` 4, `componentN` 2, `getValue` 2, `get` 1), per esempio `DefaultConverter.kt:198` → `kotlin.collections.set`, inline;
  - builtin di Kotlin, senza jar: 43 (`Annotations.kt:37` `List.get`, `DefaultConverter.kt:206` `Array.get`);
  - membro delegato del progetto: 11 (`JsonArray.kt:53` `JsonObject.get`, delegato alla mappa);
  - JDK 8 (`Klaxon.kt:248` `HashMap.get`), progetto 1 (`Lookup.kt:14` `JsonArray.get`).
- Riferimenti senza pacchetto: 2.104.
  - In un jar con versione: 831. kotlin-stdlib 1.6.0 679, kotlin-reflect 1.6.0 84, kotlin-test 1.6.0 68 (`JacksonParser.kt:30` `KClass.java` → `kotlin/jvm/java`).
  - Builtin senza jar: 1.236 (`kotlin/Any`, `String`, le interfacce delle collezioni). L'Analysis API li risolve nel suo modulo dei builtin, non nel kotlin-stdlib del classpath.
  - Membri delegati del progetto 31 (`DefaultConverter.kt:189` `MutableMap#entries` → `JsonObject.entries`), costruttori SAM 2 (`Annotations.kt:48` `Comparator`), locali del progetto 2, nessuna risposta 2 (`Issue95Test.kt:39`, `component1` di una destrutturazione).
- Tempo e memoria: compilazione del resolver 6,7 s, una volta sola; avvio 1,9 s; domande 9,5 s; RSS 1.043 MB con heap massimo 3 GB.

Grafo dal compilato:

| | javapoet | klaxon |
| --- | --- | --- |
| classi del progetto, entry point | 116, 1.030 | 437, 2.534 |
| classi create dal test runner (RTAT) | 19 | 63 |
| metodi del progetto con chiamate: CHA, RTA, RTAT | 951, 476, 922 | 1.891, 820, 1.546 |
| archi CHA, RTA, RTAT (di cui esterni) | 7.669 (3.154), 19.816 (18.496), 34.702 (30.197) | 13.573 (4.746), 30.508 (28.659), 49.736 (44.586) |
| secondi: gerarchia, CHA, RTA, RTAT, totale | 1,6, 0,9, 6,4, 7,1, 16,6 | 1,4, 0,7, 10,0, 9,7, 22,4 |
| RSS del processo WALA | 2.510 MB | 2.819 MB |
| build di scip-java riusata | 48,6 s | 98,9 s |

RTA puro raggiunge circa metà dei metodi. Senza un `new`, i metodi delle classi di test non sono raggiungibili, perché JUnit e TestNG le creano per riflessione. Per questo il confronto usa anche RTAT.

Dispatch: i candidati dell'indice in ogni sito, come classi JVM.
- javapoet: 69 siti, 368 candidati.
  - CHA e RTAT tengono 347 e ne tolgono 21, a ragione. 19 sono `MethodSpecTest$HasAnnotation#toString`, astratto (`AnnotationSpec.java:149`, `AnnotationSpec.java:177`, `ClassName.java:229`). 2 sono `ClassName#isAnnotated` dove il ricevente è un `ArrayTypeName` o un `ParameterizedTypeName` (`ArrayTypeName.java:67`, `ParameterizedTypeName.java:71`).
  - RTA puro: in 33 siti il chiamante non è raggiunto (78 candidati). Sui 36 raggiunti tiene 233 e toglie 57; 37 di questi non sono mai creati da un `new` raggiungibile (`TypeSpecTest$1`, `TypeSpecTest$2`, `TestFiler` a `JavaFile.java:169`).
  - Aggiunti dal compilato: 2, il metodo ereditato che il ricevente esegue davvero. RTAT aggiunge anche 7.820 bersagli esterni (JDK e jar), sommati sui siti.
- klaxon: 104 siti con implementazioni.
  - 49 siti sono `==` o `!=`, con 4.508 implementazioni di `Any#equals` nell'indice. In 26 il compilato fa un confronto senza chiamata, per `null` o identità (`Annotations.kt:26`, `Annotations.kt:33`, `Annotations.kt:113`). Negli altri 23 chiama `Intrinsics.areEqual`, e la dispatch avviene dentro la stdlib per tutti i siti insieme (`Annotations.kt:30`, `DefaultConverter.kt:102`, `DefaultConverter.kt:105`).
  - 1 sito è `super.equals` (`Token.kt:13`): l'indice dà 92 implementazioni che non possono girare. 1 sito non ha la chiamata nel compilato (`Main.kt:52`).
  - 53 siti di dispatch, 897 candidati. CHA tiene 805 e ne toglie 92, a ragione: in `Token.kt:16` `javaClass.hashCode()` ha ricevente `Class`.
  - RTAT tiene 532 e toglie 365: quei 92 più 273 candidati di 52 classi che nessun `new` del progetto crea, perché nascono per riflessione e a runtime girano. Sono gli 8 TypeAdapter creati da `createInstance()` (`TypeFor.kt:8`, `JsonObjectConverter.kt:237`) e 44 data class dei test che crea solo il parser di Klaxon (`DefaultConverter.kt:55`, `DefaultConverter.kt:56`, `Render.kt:19`, `toString`, 44 ciascuno).
  - RTA puro: 17 siti non raggiunti (314 candidati); sui 36 raggiunti toglie 486 candidati su 583.
  - La dispatch che il compilato sposta in un `$default` si segue per un passo: `Parser.kt:22` `parse(it)` passa da `Parser$DefaultImpls.parse$default`.

Lambda e method reference:
- javapoet: 7 lambda e 6 method reference con `invokedynamic`. CHA raggiunge 7 lambda e 5 method reference, RTA e RTAT 6 e 5.
  - Non raggiunte: `Method::getName` (`AnnotationSpec.java:118`), con bersaglio nel JDK, fuori da CHA e mai chiamato in RTA. La lambda di Mockito in `ClassNameTest.java:136` la raggiunge solo CHA.
  - javac attribuisce le tre method reference di `Collector.of(...)` alla riga 123, non alle righe 124-126 del sorgente. L'indice nomina tutte e sei le method reference entro cinque righe.
  - Le lambda diventano metodi propri (`CodeWriter.java:198` → `lambda$emitTypeVariables$0`); l'indice attribuisce il corpo al metodo che le contiene.
- klaxon: Kotlin 1.6 compila le lambda in 96 classi `kotlin/jvm/internal/Lambda`.
  - `invokedynamic` compare solo per 4 conversioni SAM (`Annotations.kt:48`, `PropertyOrderTest.kt:17`, `ParseFromEmptyNameTest.kt:25`): CHA e RTAT le raggiungono tutte e 4, RTA 1.
  - Le 11 chiamate `FunctionN.invoke` (`block(it)`) hanno con CHA e RTAT in media 44,7 bersagli del progetto e fino a 59, cioè ogni lambda della stessa arità. L'indice lì ha solo la lettura del parametro.

Cosa perde o distorce il compilato per Kotlin, su klaxon, con javapoet come riferimento:
- Chiamate dell'indice ritrovate alla stessa riga: klaxon 1.773 su 2.211 (80%); javapoet 6.416 su 6.441 (99,6%), più 12 entro due righe e 13 creazioni di classi anonime.
- Perse in klaxon:
  - inline 346. Del progetto 110 (`Klaxon.parse<T>` 76, `parseArray` 12). Della libreria 236, inline secondo l'Analysis API (`arrayOf` 48, `forEach` 20, `use` 20, `map` 16; `JacksonParser.kt:44` `apply`, `JacksonParser.kt:99` `checkNotNull`);
  - operatori e conversioni primitive, che diventano istruzioni JVM: 28 (`Annotations.kt:52` `compareTo`, `DefaultConverter.kt:28` `toFloat`, `DefaultConverter.kt:31` `toDouble`);
  - altre 53 (`Annotations.kt:48` costruttore SAM `Comparator`, `JsonReader.kt:90`, `Render.kt:10`), più 10 che passano da un accessor sintetico (`JacksonParser.kt:72`, `JacksonParser.kt:76`, `JacksonParser.kt:84`).
- Aggiunte o spostate dal compilato in klaxon, sui 7.656 siti di chiamata di CHA:
  - 1.183 a righe oltre la fine del file: sono corpi inline copiati, con le righe della SMAP (`Issue236Test.kt:35`);
  - 1.050 controlli di null (`Intrinsics.checkNotNull*`), 924 costruzioni di stringhe, 260 boxing;
  - 300 chiamate a un metodo `$default` (`BindingTest.kt:28` `toJsonString$default`, `TestTypes.kt:31` `Parser$DefaultImpls.parse$default`), 39 a `DefaultImpls`, 19 ad accessor sintetici (`Debug.kt:5` `access$getVerbose$cp`);
  - coroutine: klaxon non ne ha (0 metodi con `Continuation`), quindi non sono misurate.

Verifica a mano, 20 siti:

| Fonte | Giusti | Il resto |
| --- | --- | --- |
| grafo dell'indice | 8 | 10 sbagliati (overload e override fra task), 2 buchi |
| Analysis API | 12 su 12 | gli 8 siti di dispatch e lambda non sono domande sue |
| CHA | 17 | 2 distorti da `$default` (`BindingTest.kt:28`, `TestTypes.kt:31`), 1 sbagliato (`KlaxonJson.kt:30`: il `set` inline diventa `Map.put`) |
| RTAT | 16 | 2 distorti, 2 sbagliati: `KlaxonJson.kt:30` e `TypeFor.kt:8`, con i TypeAdapter creati per riflessione |
| RTA puro | 10 | 6 con il chiamante non raggiunto (test), 4 sbagliati: anche `Klaxon.kt:268` e `JavaFile.java:169` |

I quattro errori dell'indice sono tutti risolti dall'Analysis API: `JacksonParser.kt:86` → `obj(Iterable)`, `Klaxon.kt:31` con l'implementazione `JacksonParser.kt:38`, `JsonArray.kt:53` → `JsonObject.get` delegato, `KlaxonJson.kt:30` → `kotlin.collections.set` in kotlin-stdlib 1.6.0. Il compilato ne risolve tre e il quarto lo trasforma in `Map.put`.

Costo fatturato da Modal: 0,085 USD, per tre esecuzioni complete e una build dell'immagine fallita (`coursier --intransitive` vuole un argomento per ogni modulo). Nelle prime due il lettore del compilato sbagliava righe e file sorgente: il program counter è già l'indice nel bytecode, e l'attributo `SourceFile` va letto dal class file. `results/strong-jvm.json` viene dalla terza, ricalcolato in locale con `compare` dopo una correzione che cambia classe a 2 chiamate implicite (`componentN`). I bersagli attesi della verifica a mano non sono cambiati.

Non verificato:
- Gli overload scelti dall'Analysis API uno per uno, oltre i 20 siti: sono confrontati solo con i candidati dell'indice.
- La regola che metterebbe i 1.236 builtin nel kotlin-stdlib 1.6.0 del classpath: è dedotta, non chiesta.
- RTA con altri entry point (main, servizi, framework diversi da JUnit e TestNG) e con la riflessione modellata: qui i TypeAdapter e le data class di Klaxon cadono.
- I bersagli nei pacchetti del JDK esclusi da `EXCLUSIONS`.
- La corrispondenza fra implementazione locale e classe JVM, fatta per vicinanza di riga: in questi due casi nessuna resta senza classe.
- Kotlin 2.x, che compila le lambda con `invokedynamic`; le coroutine; altri progetti; Gradle 8.
- I picchi di RAM fra un campione e l'altro (due al secondo, sotto gVisor).

### JavaScript e TypeScript: compilatore e Jelly

Accanto al grafo letto dall'indice SCIP ci sono due seconde fonti, ciascuna in un suo adapter con la stessa forma
(`analyze(project_dir, work_dir) -> {"edges", "engine"}`). Provate sulla fixture TypeScript (oggi `tests/fixtures/code-graph/ts`) e poi su tududi (commit
`71da9d7b`, 1.688 file JS/TS) su Modal con `strong_js.py`, app `daodan-strong-js`: una sola esecuzione completa,
più una ripresa del solo confronto sugli archi tenuti (`--reuse`, 65 s).

- `adapters/ts_compiler.py` con `adapters/ts_compiler.js`: un processo Node, `ts.createProgram` con `allowJs`;
  per ogni chiamata `checker.getResolvedSignature(call).declaration`, altrimenti `getSymbolAtLocation` +
  `getAliasedSymbol`. TypeScript 7.0 è uscito senza API JavaScript ("it does not ship with an API", annuncio
  ufficiale); l'API sta in `@typescript/typescript6@6.0.2`, che carica TypeScript 6.0.3.
- `adapters/js_jelly.py`: `@cs-au-dk/jelly@0.13.0`, solo modo statico (`-j`, `--diagnostics-json`, `-i` timeout,
  `--no-callgraph-external`; mai `--approx`, `-d`, `--npm-test`). Due giri: solo file del progetto
  (`--ignore-dependencies`) e con `node_modules`.
- Il confronto è fatto chiamata per chiamata sul grafo dell'indice, ricostruito dagli input tenuti sul volume
  (`scip-inputs/tududi`). I risultati sono in `results/strong-js-tududi.json` e
  `results/strong-js-tududi-split.json`: stessi archi, ma il secondo separa le funzioni che Jelly trova dentro
  gli argomenti della chiamata.

#### Motori

| fonte | secondi | RAM di picco | note |
|---|---:|---:|---|
| compilatore TS | 35 | 1,8 GB | 111.366 chiamate: 93.241 per firma, 1.089 per simbolo, 17.036 senza dichiarazione |
| compilatore TS + 22 `@types/*` mancanti | 35 | 1,8 GB | per firma 96.070 |
| Jelly solo progetto | 35 | 2,4 GB | 1.688 moduli, 23.495 funzioni, nessun timeout |
| Jelly con `node_modules` | 1.286 | 21,4 GB | fermato dal suo timeout di 1.200 s: 702 pacchetti, 10.425 moduli, 161 errori; grafo parziale |

Costo fatturato da Modal per l'app: 0,085 USD (ora 23 UTC) + 0,056 USD (ora 00 UTC) = 0,14 USD.

#### Per classe di buco (chiamate dove l'indice non ha un obiettivo del progetto)

"Callback" vuol dire che Jelly collega la chiamata alla funzione passata come argomento: `tasks.map(fn)` diventa
`tasks.map -> fn`. L'arco è vero, perché il codice nativo chiama `fn`, ma `fn` non è il chiamato.

| buco (indice) | chiamate | TS | TS + `@types` | Jelly solo progetto | Jelly con dipendenze |
|---|---:|---|---|---|---|
| JS ricevitore senza tipo | 9.166 | 0 | 767 esterni | 44 progetto + 231 callback | 3 progetto + 31 callback + 297 esterni |
| JS chiamato dinamico | 3.698 | 0 | 1.455 esterni | 10 progetto + 84 callback | 36 callback + 1 esterno |
| JS legame ambiguo | 2.565 | 0 | 121 esterni | 40 progetto + 18 callback | 14 callback + 1 esterno |
| JS metodo abbreviato di un oggetto in un altro file | 60 | 57 progetto + 3 esterni | uguale | 57 progetto | 48 progetto + 1 esterno |
| TS `t` di `useTranslation` | 3.748 | 3.748 esterni (`i18next`) | uguale | 0 | 0 |
| TS `fireEvent.*` | 564 | 564 esterni (`@testing-library/dom`) | uguale | 0 | 0 |
| TS ricevitore senza tipo | 408 | 0 | 0 | 4 progetto | 4 progetto |
| TS `useCallback` (salto dichiarato dell'indice) | 145 | 145 uguali, senza salto | uguale | 0 | 0 |

Esempi per classe:
- Metodo abbreviato:
  - `backend/modules/blog/hostSwitch.js:79` `blogService.page` -> `backend/modules/blog/service.js:317`;
  - `backend/modules/notes/routes.js:76` `notesController.getNoteUidForAuth` -> `notes/controller.js:277`;
  - `backend/modules/quotes/quotesService.js:26` `yaml.load` -> js-yaml, un esterno che l'indice prendeva per
    un metodo del progetto.
- `t`: `frontend/components/Admin/AdminUsersPage.tsx:634`, `AdminFeedbackPage.tsx:162`,
  `AdminRolesPanel.tsx:88` -> `i18next@24.2.3`.
- `fireEvent`: `frontend/components/Admin/__tests__/AdminGroupsPanel.test.tsx:163`,
  `Shared/__tests__/ShareModal.test.tsx:204`, `Admin/__tests__/AdminUserStatusTable.test.tsx:183` ->
  `@testing-library/dom@9.3.4`. Il compilatore li risolve tutti, quindi il buco è di scip-typescript.
- `useCallback`: `frontend/components/Everyone/PeopleBoard.tsx:483` -> `:433`, `Note/NoteModal.tsx:255` ->
  `:184`, `Admin/AdminFeedbackPage.tsx:128` -> `:109`. La firma risolta arriva alla funzione freccia da sola.
- Esterni dopo `@types`:
  - `backend/tests/integration/demo.test.js:71` `agent.get` -> `@types/supertest@7.2.1`;
  - `caldav-projects.test.js:15` `bcrypt.hash` -> `@types/bcrypt@6.0.0`;
  - `caldav-protocol.test.js:102` `.set` -> `@types/superagent`.

  Il pacchetto identificato è quello dei tipi: per fonderlo serve la regola `@types/x -> x`.
- Jelly, chiamato vero su un ricevitore senza tipo:
  - `backend/modules/billing/service.js:156` `provider.configuredPrices` -> `billing/stripeClient.js:39`;
  - `backend/services/entityAttachments.js:350` `store.add` -> `:89`;
  - `backend/modules/mcp/server.js:85` `tool.handler` -> `mcp/tools/taskTools.js:223`.

Con `node_modules` Jelly peggiora, perché il timeout taglia l'analisi. Dove l'indice ha già un obiettivo del
progetto, 5.384 chiamate restano senza obiettivo, contro 1.047 nel giro solo progetto.

#### Dove l'indice ha già un obiettivo del progetto

- Compilatore TS: 19.105 uguali, nessun disaccordo.
  - 882 casi si fermano su un parametro o su un tipo funzione: è il caso della callback, che il compilatore
    non segue.
  - 12 casi danno un esterno, 6 meno obiettivi, 1 più obiettivi.
- Jelly solo progetto: 18.939 uguali, 1.047 senza obiettivo, 13 disaccordi (12 disgiunti, 1 sovrapposto).
- Jelly con dipendenze: 3 disaccordi, già compresi nei 13.

Ho letto nel sorgente tutti i 13 disaccordi, e hanno la stessa forma: l'indice (e con lui il compilatore) punta
alla firma di un membro d'interfaccia o di una prop, Jelly alla funzione che quel membro contiene davvero.

Jelly ha ragione in 11:
- `frontend/components/Admin/AdminUserFilter.tsx:132` `choice.matches` -> le frecce `:101`, `:106`, `:111`;
- `DailyPlan/tips.ts:132` e `:141` `durationFor` -> `PlanMyDay.tsx:414`, `TodayPage.tsx:399`;
- `Inbox/QuickCaptureInput.tsx:2141` e `Note/MarkdownEditor.tsx:380` `upload` -> `utils/attachmentsService.ts:220`;
- `Note/SlashCommandMenu.tsx:300` e `:341` `cmd.insert` -> `:16` (`makeInserter`) e `:210`;
- `Note/editor/linkClicks.ts:30` `onOpenWikilink` -> `MarkdownEditor.tsx:478`;
- `Shared/UsageBar.tsx:29` e `:32` `format` -> il default `:15` (nessun chiamante passa `format`);
- `utils/slashMenu.ts:145` `labels.create` -> `QuickCaptureInput.tsx:2341`.

Jelly è parziale in 2:
- `Shared/MarkdownRenderer.tsx:420` `publicNoteHref`: dà solo il default `:158`; mancano le frecce di
  `Blog/BlogIndexPage.tsx:108` e `PublicNote/PublicNoteArticle.tsx:84`.
- `backend/shared/middleware/errorHandler.js:20` `err.toJSON`: l'indice dà `AppError.js:18` e gli override di
  `shared/errors/index.js`, Jelly dà `AppError.js:18` e la freccia assegnata in `spreadsheets/core/errors.js:8`.
  La verità è l'unione delle due.

Il grafo dell'indice tratta come funzione chiamata la firma di un tipo: è un difetto dell'indice, non di Jelly.

#### Precisione di Jelly: 20 archi letti su ricevitori senza tipo

Solo progetto: 20 archi, nessuno inventato.
- 15 sono callback negli argomenti: veri come flusso, ma non sono il chiamato. Per esempio
  `backend/modules/tasks/core/serializers.js:243` `tasks.map`, `backend/modules/people/service.js:27`
  `people.map`, `backend/services/accountsService.js:157` `ids.filter`.
- 4 sono `tool.handler` verso gli handler registrati con `tools.push`: veri. Sono `mcp/tools/habitTools.js:99`,
  `taskTools.js:223`, `taskTools.js:1372`, `tagTools.js:87`.
- 1 è `backend/modules/auth/service.js:389` `session.destroy` verso lo stub di
  `tests/unit/modules/auth/authService-edge-cases.test.js:264`: vero, ma solo nel test.

Con dipendenze: 20 su 20 veri.
- 16 sono esterni: `request.agent` -> supertest 11 volte, `bcrypt.hash`/`compare` -> bcrypt 4 volte,
  `ejs.renderFile` -> ejs.
- 4 sono callback negli argomenti, per esempio `backend/services/userDataTransfer.js:283` `linkedUsers.map`.

Non ho misurato il richiamo di Jelly, cioè quante chiamate gli mancano: non è completo per costruzione.

#### Controllo a mano (20 casi, attese scritte prima dei risultati)

Corretti: indice 3, TS 3, TS + `@types` 4, Jelly solo progetto 3, Jelly con dipendenze 3.

- Nessuna fonte risolve i 4 casi che l'indice sbagliava: `queryInterface.addIndex`, `lastModified.toJSDate`,
  `Task.create`, `tag.slice`.
- Lo stesso vale per altri 6: `findAll` (2 casi), `findOrCreate`, `update`, `toJSON` dei modelli Sequelize,
  `req.get` di Express. Il ricevitore è `any` anche per il compilatore, e Jelly non segue gli oggetti Sequelize.
- Callback:
  - Jelly trova tutte le 7 frecce di `backend/modules/webhooks/controller.js:15` e tutte le 3 di
    `webhooks/taskEvents.js:88`.
  - Per `frontend/components/Habits/HabitDayPanel.tsx:94` ne trova 2 su 3: manca `HabitDetails.tsx:446`.
  - Su `caldav/services/safe-request.js:107` Jelly solo progetto aggiunge la freccia del test
    `caldav-safe-request.test.js:257`.
  - Nessuna fonte trova le callback passate come prop (`MissingNotePrompt.tsx:75`, `TagModal.tsx:76`); l'indice
    lì punta alla firma della prop.
- `@types/multer` fa trovare a TS il `cb` di `backend/modules/backup/routes.js:27`.
- `res.status` (`tasks/routes.js:612`) era già esterno, perché i tipi di Express ci sono.

#### Verdetto

- Compilatore TS: chiude il metodo abbreviato (57 di 60), `t` (3.748), `fireEvent` (564) e `useCallback` senza
  salto dichiarato. Non chiude i ricevitori `any`: 0 obiettivi del progetto; 767 esterni se si installano i
  `@types` mancanti. Nessun disaccordo: i suoi archi si fondono come certi, con la regola `@types/x -> x` per gli
  esterni.
- Jelly solo progetto: è l'unica fonte per callback e valori funzione (le 7 + 3 frecce dei webhooks, le 11
  correzioni ai membri d'interfaccia). Sui ricevitori senza tipo dà poco: 44 chiamati veri su 9.166. Non ha
  inventato archi nei 20 letti, ma non è completo per costruzione: va fuso come candidato marcato, separando le
  callback negli argomenti dal chiamato.
- Jelly con `node_modules`: no, perché costa 21 GB, va in timeout e dà meno archi.
- I ricevitori `any` restano aperti per ogni fonte statica. Li chiude il passo dinamico: il registro esatto dà un
  bersaglio a 13.677 delle 16.527 chiamate che il passo per posizione lasciava senza
  ([`call-provenance`](../call-provenance/README.md), sezione 1; i due conteggi in «I conteggi delle chiamate senza
  bersaglio su tududi JavaScript»).

Non verificato:
- il richiamo di Jelly;
- gli 882 casi TS fermi su un parametro;
- se le versioni `@types` installate (le ultime) corrispondono a quelle dei pacchetti;
- 198 siti TS e 72 di Jelly che non trovano la chiamata nello snapshot (0,2%);
- test automatici per i due adapter.
