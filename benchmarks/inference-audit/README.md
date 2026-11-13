# Benchmark: cosa danno i motori di inferenza e cosa ne usa Daodan

Verifica, per ogni motore del passo di inferenza ([spec del motore](../../docs/specs/2026-11-08-risoluzione-chiamate-motore.md)), il percorso di un fatto dal motore al grafo che usano mappa e flussi: cosa si chiede, cosa il motore risponde, cosa si registra, cosa arriva ai collegamenti. Lo scopo è trovare ogni punto in cui un'informazione utile che il motore dà, o darebbe se gli si chiedesse, va persa. Nessun modello; tutto gira su Modal.

## Domande

| Punto | Cosa si conta |
| --- | --- |
| P1 Cosa non si chiede | riferimenti per tipo e stato (chiamate risolte, non risolte, letture); fra le letture, quelle che nominano una funzione, un metodo o una classe del progetto (un componente reso, una funzione passata come valore) |
| P2 Cosa si chiede | chiamate non risolte per classe (`askable`, `dynamic`, `builtin`) e per esito del passo (`edge-call`, `external-definition`, `project-not-a-symbol`, `ambiguous-target`, `unresolved`, errori, posizioni non verificate) |
| P3 Cosa il motore risponde e Daodan riduce | su un campione per esito, la risposta grezza: dove cade ogni destinazione (dichiarazione del progetto e suo tipo, contratto, valore, file del progetto senza dichiarazione, libreria esterna con il suo pacchetto, destinazione non su file); dal 13 novembre anche graduata alla posizione esatta come la gradua il passo, e per un valore che cosa contiene (parametro, proprietà, destrutturazione, chiamata con o senza una funzione scritta sul posto, con il nome della funzione chiamata) |
| P4 Cosa il motore darebbe se gli si chiedesse | sullo stesso campione, per i server LSP, `implementation` e `typeDefinition` accanto a `definition`; per Jedi, `goto` accanto a `infer`, con il nome completo delle destinazioni esterne |
| P5 Cosa si registra | archi confermati e candidati per esito e per tipo della dichiarazione di destinazione |
| P6 Cosa arriva al grafo | riferimenti risolti dal motore nella vista degli archi (`edge_view`), candidati e conflitti; fra i riferimenti risolti, quelli che diventano un collegamento dei flussi e quelli che si perdono (destinazione senza dichiarazione, chiamata fuori da un simbolo) |
| P7 Accordo con il lessicale | su un campione di chiamate già risolte dal risolutore lessicale, quante volte il motore indica la stessa dichiarazione |

## Parametri

| Parametro | Valore |
| --- | --- |
| casi | phazly (archivio privato: Python, TypeScript, Rust), tududi `71da9d7b34dfd1600657e9c5ddf40420206fd263` (JavaScript, TypeScript), javapoet `b9017a9503b76e11b4ad4c1a9f050e2d29112cb0` (Java), klaxon `1173bdc568a6d339b45cf24a6a9c5c2f6847f42d` (Kotlin), semver `280ebcb6edac3aa4cdc545dbff8a26c5ac4861fe` (Rust), chi `c64ed7d6635f33a8b2feaff7dcfa55677023ac7d` (Go) |
| passo | quello del prodotto: `snapshot.py write --no-engine --no-index`, poi `resolve_edges.py --pass`, tutte le posizioni |
| campione P3 e P4 | fino a 20 posizioni per esito e per linguaggio, a passo fisso sull'ordine degli identificativi |
| campione P1 | fino a 60 letture che nominano una funzione, un metodo o una classe del progetto, per linguaggio |
| campione P7 | fino a 30 chiamate risolte dal lessicale, per linguaggio; dal 13 novembre fino a 2.000, confrontate anche alla posizione esatta, con ogni disaccordo registrato (fino a 200) |
| regole dei flussi (P6) | `benchmarks/phazly-flow/rules.json`, `benchmarks/tududi-flow/rules.json`; gli altri casi senza regole contano solo la vista degli archi |

Esecuzione: `modal run --detach benchmarks/inference-audit/modal_audit.py --phazly-tar PATH`; un container per caso, risultati in `results/audit-<caso>.json` e sul volume `daodan-flow-results`.

## Risultati

### 13 novembre 2026

Sei casi su Modal, un container ciascuno (app `ap-BDU0cjbbx8vImvzZqpgAFZ`), nessun modello. Valori per caso in `results/audit-<caso>.json`. Le perdite in ordine di peso:

| # | Dove si perde | Misura |
| --- | --- | --- |
| 1 | Chiamate risolte fuori da una funzione con nome (codice al livello del modulo: registrazioni delle rotte, composizione dell'app) non diventano collegamenti dei flussi | tududi 8.314 su 17.377 chiamate risolte (48%: 2.780 del motore, 5.534 del lessicale); phazly 485 su 13.339; javapoet 15; semver 3; chi 0 |
| 2 | Letture che nominano una funzione, un metodo o una classe del progetto (componenti resi, funzioni passate come valore, riferimenti) non si chiedono al motore né diventano collegamenti | tududi 29.380, phazly Python 14.071, phazly TypeScript 3.614, javapoet 296, klaxon 260, chi 181, semver 82; chieste a campione, la definizione cade su una funzione o una classe del progetto nel 25-55% dei casi |
| 3 | Archi confermati verso un metodo (anche di un contratto) scartati dalla vista degli archi, che tiene solo destinazioni `function` e `class` | tududi 2.199 su 7.681 (29%: 1.303 metodi, 896 contratti); phazly TypeScript 304 su 733 (41%); chi 156 su 783; semver 19 su 371 |
| 4 | Una risposta che cade in una libreria si registra come `external-definition`, senza il pacchetto | tududi 35.863, phazly 18.763 (Python 11.273, TypeScript 7.490), chi 2.299, javapoet 1.076, semver 242: nessun arco verso un servizio esterno nasce dall'inferenza |
| 5 | Una funzione assegnata a una costante (funzione freccia, espressione di funzione) è graduata `project-not-a-symbol`: il motore indica il nome della costante, che è un valore | tududi JavaScript 1.087, metà dei casi a campione cadono su una funzione; phazly TypeScript 2.072, in parte valori veri (setter di `useState`), in parte funzioni (`handleClose`); restano candidati che i flussi non usano |
| 6 | Il motore Kotlin non si installa | phazly e klaxon: «could not install the Kotlin Analysis API: HTTP Error 403: Forbidden»; klaxon resta al 17,7% |
| 7 | `implementation` non si chiede mai | dove la definizione cade su un contratto o su un valore, a campione trova la funzione concreta in 11 casi su 20 (phazly TypeScript, chiamate), 11 su 20 (tududi JavaScript, destinazioni ambigue), 5 su 20 (phazly TypeScript, non simboli); `type_definition` non aggiunge destinazioni utili |

- Il motore tace (`unresolved`) su tududi JavaScript 15.109, phazly Python 2.868, javapoet 1.213: a campione sono metodi di librerie su valori senza tipo (`res.status`, `dict.get`, collezioni di Motor). Non sono collegamenti persi, ma contano fra le chiamate risolvibili e abbassano la copertura dichiarata.
- Il risolutore lessicale e il motore indicano la stessa dichiarazione in 28-30 casi su 30 per caso (semver 25 su 30).
- Jedi `goto` e `infer` danno le stesse destinazioni a campione.
- Nessun conflitto fra lessicale e motore in nessun caso.

### 13 novembre 2026, rimisura dopo le correzioni

Stessi sei casi (app `ap-2Cwf3qAFgMtesOgHaex1Qa`, plugin del working tree al commit `4adbde359`, con le modifiche locali non committate di `store_graph.py`, `store_consumers.py`, `snapshot.py` e `mcp_service.py`), P7 fino a 2.000 chiamate. Costo fatturato da Modal: 0,66 USD (la prima misura 0,48 USD).

| Caso | Chiamate risolte su risolvibili, prima | Dopo | Collegamenti persi nel grafo, prima | Dopo |
| --- | --- | --- | --- | --- |
| chi | 858 su 1.100 (78,0%) | 1.014 su 1.100 (92,2%) | 0 | 0 |
| javapoet | 2.864 su 4.077 (70,2%) | 2.864 su 2.874 (99,7%) | 15 | 0 |
| klaxon | 311 su 1.755 (17,7%) | 812 su 917 (88,5%) | 12 | 0 |
| phazly | 13.339 su 19.763 (67,5%) | 13.655 su 19.648 (69,5%) | 485 | 0 |
| semver | 428 su 484 (88,4%) | 447 su 484 (92,4%) | 3 | 0 |
| tududi | 17.377 su 41.695 (41,7%) | 19.794 su 41.715 (47,5%) | 8.314 | 0 |

- Il motore Kotlin si installa in un container senza Java: klaxon passa da 17,7% a 88,5%; in phazly risponde su 269 chiamate (5 archi, 151 senza risposta).
- In javapoet 1.203 chiamate prima senza risposta ora cadono in una libreria (`external-definition` da 1.076 a 2.279): escono dalle risolvibili.

P7, lessicale e motore alla posizione esatta:

| Caso e motore | Confrontate | Stessa dichiarazione | Divergenze |
| --- | --- | --- | --- |
| chi, gopls | 231 | 231 | 0 |
| klaxon, Kotlin | 311 | 311 | 0 |
| phazly, Kotlin | 36 | 36 | 0 |
| phazly, TypeScript | 2.000 su 2.582 | 2.000 | 0 |
| tududi, TypeScript | 2.000 su 11.895 | 2.000 | 0 |
| javapoet, JDT LS | 289 | 264 | 25: il lessicale indica la classe, il motore il suo costruttore |
| semver, rust-analyzer | 76 | 65 | 9: il lessicale lega `Err(...)` al tipo associato `type Err` dell'`impl`, il motore alla libreria standard; 2 senza risposta del motore |
| phazly, Jedi | 2.000 su 4.815 | 1.956 | 44: funzioni decorate con `@cache` o `@lru_cache`; `infer` dà l'oggetto restituito dal decoratore (`functools._lru_cache_wrapper`, senza posizione), graduato `external-definition`; ha ragione il lessicale |

Due difetti che la tabella mostra: il grafo tiene i 9 archi lessicali sbagliati di semver, perché il passo non interroga il motore sulle chiamate già risolte dal lessicale; Jedi classifica come esterne le chiamate a funzioni del progetto decorate (`@contextmanager` compreso: `infer` dà `typing.Callable`).

### 13 novembre 2026, il motore controlla anche le chiamate già risolte

Stessi sei casi con le correzioni `1f5c55ac5` (il motore interroga anche le chiamate legate dal lessicale e la sua risposta vince) ed `e86bdb39c` (Jedi usa `goto` quando `infer` non dà una funzione o una classe). chi, javapoet, klaxon e semver dall'app `ap-aE8qBaqhrNAjhSe0Y1IsQo`; phazly e tududi da chiamate `spawn` dell'app distribuita, perché `modal run` annulla i casi in corso quando il client locale perde la rete. Costo fatturato: 0,33 USD per i primi quattro, 0,43 USD per phazly e tududi; 0,27 USD di una run annullata.

| Caso | Chiamate già risolte controllate | Uguali | Corrette | Esterne | Copertura |
| --- | --- | --- | --- | --- | --- |
| chi | 231 | 231 | 0 | 0 | 92,2% |
| javapoet | 289 | 264 | 25 (dalla classe al costruttore) | 0 | 99,7% |
| klaxon | 311 | 311 | 0 | 0 | 88,5% |
| semver | 76 | 65 | 0 | 9 (`Err(...)` tolto dal tipo associato) | 92,2% (438 su 475) |
| phazly | 7.433 | 7.433 | 0 | 0 | 69,6% (13.692 su 19.686) |
| tududi | 11.895 | 11.894 | 0 | 0 (1 senza risposta) | 47,4% (19.790 su 41.715) |

- Jedi su phazly: P7 2.000 su 2.000 alla stessa dichiarazione (prima 1.956); 37 chiamate Python in più risolte dal motore (10.329 su 13.385).
- Tempo del passo dei motori: tududi da 1.676 a 2.138 s (+28%); phazly da 2.285 a 1.594 s, ma la misura precedente comprende un riavvio per preemption e non è confrontabile.
- tududi TypeScript perde 4 archi del motore (7.027 → 7.023) senza una chiamata corretta o esterna che li spieghi: causa da guardare.

### 13 novembre 2026, indice SCIP contro motori

Strada A: il passo dei motori del prodotto (`resolve_edges.py --pass`, una posizione per volta, solo chiamate). Strada B: l'indice SCIP dell'intero progetto da un indicizzatore esistente, unito per posizione ai riferimenti dello snapshot (`call` e `read`) e graduato con le stesse regole del passo (`grade_all`, simboli `local` compresi). App `daodan-scip-audit` (`modal_scip.py`), risultati in `results/scip-<caso>.json`.

| Parametro | Valore |
| --- | --- |
| casi | chi `c64ed7d6`, semver `280ebcb6`, tududi `71da9d7b` (come sopra) |
| indicizzatori | scip-go v0.2.9 con Go 1.27.3; `rust-analyzer scip` 2026-11-09 con Rust 1.99.1, senza build script né macro procedurali; scip-typescript 0.5.2 su Node 22.23.4 |
| dipendenze | Go `go mod download`; Rust quelle di cargo; JS/TS `npm ci --ignore-scripts` (l'installazione del passo, `npm_modules`) |
| perimetro | una copia del checkout; Go e Rust: un'esecuzione in più per ogni modulo o crate annidato e le cartelle `_x` di Go nominate come pacchetti; TypeScript: un tsconfig generato con ogni file JS/TS dello snapshot e `allowJs`, che estende quello del progetto |
| strada A | chi e semver rieseguita nel container; tududi dalle risposte per chiamata di `answers-tududi-r1.sqlite` (stesso commit), 0 righe fuori posizione |

Chiamate con una destinazione del progetto:

| Caso | Chiamate | A | B | Uguali | Diverse | Solo A | Solo B |
| --- | --- | --- | --- | --- | --- | --- | --- |
| chi (Go) | 4.133 | 1.014 | 1.477 | 861 | 153 | 0 | 463 |
| semver (Rust) | 793 | 438 | 254 | 252 | 0 | 186 | 2 |
| tududi JavaScript | 72.890 | 12.767 | 11.022 | 11.013 | 0 | 1.754 | 9 |
| tududi TypeScript | 38.477 | 7.023 | 7.007 | 7.002 | 0 | 21 | 5 |

- Solo B, chi: 463 chiamate che il passo non chiede mai, perché il lessicale le lascia `unbound-name` e il passo le esclude come builtin (`ClientIPFromHeader` da un file di test dello stesso pacchetto, `chi.NewRouter`).
- Diverse, chi: B dà il metodo dell'interfaccia (`Router.Get`, `chi.go:101`), A l'unica implementazione (`Mux.Get`, `mux.go:155`) grazie a `implementation`.
- Solo A, semver: 181 chiamate dai test di integrazione agli aiuti di `tests/util/mod.rs`, modulo incluso da più crate di test: l'indice lo definisce una volta sola e gli altri crate lo nominano con un simbolo senza definizione; 3 cadono nella libreria standard (a campione `string.parse()`, che A segue fino all'implementazione `FromStr` del progetto); 2 in `tests/node/mod.rs`, che nessun crate include.
- Solo A, tududi JavaScript: 1.675 chiamate su un oggetto di modulo CommonJS (`logger.logError`), dove B si ferma alla proprietà di `module.exports = { … }`; 79 su membri di un oggetto letterale di un altro file, che scip-typescript marca `local`.
- B senza occorrenza sulle chiamate: chi 266 builtin del linguaggio (`len`, `append`); tududi JavaScript 15.445, chiamate su valori `any` (`res.json`, modelli Sequelize), 15.104 delle quali senza risposta anche da A.

Letture con una destinazione del progetto (A non chiede letture):

| Caso | Letture | B | Anche il lessicale | Solo B |
| --- | --- | --- | --- | --- |
| chi | 5.966 | 73 | 21 | 52 |
| semver | 703 | 40 | 3 | 37 |
| tududi JavaScript | 62.059 | 1.476 | 1.125 | 351 |
| tududi TypeScript | 39.420 | 3.227 | 2.734 | 493 |

Tempo e memoria (picco del processo più grande):

| Caso | Indicizzatore | Passo dei motori |
| --- | --- | --- |
| chi | 12,2 s, 335 MB | 56,4 s, 787 MB |
| semver | 8,7 s, 1.170 MB | 33,3 s, 1.094 MB |
| tududi | 62,5 s, 2.257 MB | 2.400 s (run r1, memoria non misurata) |

Costo fatturato da Modal: 0,29 USD per quattro iterazioni (l'ultima fascia oraria non ancora chiusa).

### 13 novembre 2026, indice SCIP letto per intero

Bozza. Strada B legge ora tutto l'indice (`join` in `modal_scip.py`): ogni occorrenza e ogni `SymbolInformation`. Dal nome riferito segue, senza limite di passi e con protezione dai cicli, solo ciò che l'indice afferma: una definizione che condivide il suo intervallo con un riferimento a un altro simbolo (proprietà abbreviata, destrutturazione, `module.exports = { f }`); una definizione la cui istruzione lega il nome a un altro nome che l'indice risolve (`a = b`, `k: b.c`, `{ k: nome } = …`) o a una funzione dello snapshot; le implementazioni dichiarate (`is_implementation`) di un membro, mai di un tipo. Dove la catena finisce su un valore senza alias dichiarato (parametro, risultato di chiamata, campo senza valore, `local` senza definizione) quella è la risposta, contata per classe. Ogni riferimento risolto porta la sua catena (salti e tipo di salto). Strada A, indici e snapshot sono quelli della sezione precedente, ora tenuti sul volume in `scip-inputs/<caso>`: una nuova esecuzione rifà solo il join. Risultati in `results/scip-<caso>-full.json`.

Prova locale prima di Modal: una fixture JS/TS di 17 file e una Rust con due crate di test che includono lo stesso `tests/util/mod.rs`, 30 fini di catena scritte a mano. Il join precedente ne raggiungeva 7, questo 30.

Chiamate con una destinazione del progetto:

| Caso | Chiamate | A | B prima | B ora | Solo A prima → ora | Solo B prima → ora | Diverse prima → ora |
| --- | --- | --- | --- | --- | --- | --- | --- |
| chi (Go) | 4.133 | 1.014 | 1.477 | 1.875 | 0 → 0 | 463 → 861 | 153 → 0 |
| semver (Rust) | 793 | 438 | 254 | 255 | 186 → 186 | 2 → 3 | 0 → 0 |
| tududi JavaScript | 72.890 | 12.767 | 11.022 | 12.828 | 1.754 → 58 | 9 → 119 | 0 → 0 |
| tududi TypeScript | 38.477 | 7.023 | 7.007 | 7.033 | 21 → 0 | 5 → 10 | 0 → 0 |

- Diverse, chi: B dà ora il metodo dell'interfaccia e le sue implementazioni (`Router.Get` e `Mux.Get`); le 153 risposte di A sono tra queste. In tutto 538 chiamate portano 1.126 implementazioni accanto al metodo chiamato.
- Dei 1.875 di chi, 384 vengono solo da implementazioni nel progetto di un metodo di un'interfaccia esterna che A dà come esterno (`w.WriteHeader` di `net/http.ResponseWriter` → `basicWriter.WriteHeader`, `middleware/basic_auth.go:32`).

Solo A dopo la lettura completa, ogni classe con dato assente dall'indice:

| Caso | Chiamate | Classe | Esempi |
| --- | --- | --- | --- |
| semver | 181 | aiuti di `tests/util/mod.rs` chiamati da altri crate di test: rust-analyzer scrive il documento una volta, con i simboli di un solo crate, e registra `Bug: definition at tests/util/mod.rs:… should have been in an SCIP document but was not`; tutti e 181 coincidono per nome con un simbolo definito in un altro crate, legame non seguito perché è un nome | `tests/test_version.rs:15`, `:37`, `:54` |
| semver | 3 | `string.parse()`: l'indice dà `core str::parse`; rust-analyzer non scrive relazioni (0 nell'indice), quindi l'implementazione `FromStr` che A raggiunge non c'è | `src/serde.rs:51`, `:77`, `:103` |
| semver | 2 | `tests/node/mod.rs`: nessun crate lo include, nessun documento | `tests/node/mod.rs:11`, `:42` |
| tududi JavaScript | 58 | metodi di un oggetto letterale di un altro file: scip-typescript dà al membro un `local` del suo documento, il chiamante tiene un `local` senza definizione | `backend/modules/admin/service.js:1085`, `backend/modules/blog/hostSwitch.js:114`, `backend/modules/comments/routes.js:24` |

Cosa dà B che A non ha:

| Caso | Chiamate con destinazione solo da B | Letture con destinazione (senza lessicale) | Esterne con pacchetto e versione, chiamate (A senza esterno) | Esterne, letture |
| --- | --- | --- | --- | --- |
| chi | 861: 463 mai chieste da A, 384 implementazioni, 14 funzioni tenute in un `local` | 173 (148) | 1.918 (8) | 526 |
| semver | 3 | 61 (58) | 337 (83) | 27 |
| tududi JavaScript | 119: 104 dove A risponde `binding` o `project-not-a-symbol` (`plans._resetCache`), 15 mai chieste | 1.546 (421) | 42.794 (25.624) | 2.629 |
| tududi TypeScript | 10 | 3.339 (599) | 22.357 (8.225) | 5.293 |

Lunghezza delle catene con destinazione del progetto, chiamate (letture):

| Caso | 0 salti | 1 | 2 | 3 o più |
| --- | --- | --- | --- | --- |
| chi | 1.477 (73) | 398 (98) | 0 (2) | 0 |
| semver | 254 (40) | 1 (21) | 0 | 0 |
| tududi JavaScript | 11.022 (1.476) | 1.782 (69) | 24 (1) | 0 |
| tududi TypeScript | 6.154 (2.800) | 862 (503) | 17 (36) | 0 |

Salti delle chiamate risolte: JavaScript 1.686 intervallo condiviso, 53 inizializzatore, 43 funzione assegnata, 24 di due salti; TypeScript 856 intervallo condiviso, 3 chiave di un pattern, 20 altri; chi 384 implementazione, 14 funzione assegnata.

Fini senza destinazione da notare: TypeScript 3.755 chiamate finiscono su un `local` che nessun documento definisce (`t` di `useTranslation`, `frontend/Layout.tsx:497`), tutte esterne per A; l'indice non nomina il pacchetto. Risultati di chiamata: JavaScript 897, TypeScript 3.426; parametri: 649 e 281.

Tempo del join: chi 2,9 s, semver 3,5 s, tududi 67,1 s (prima 3,7, 0,8 e 103,7 s). Con gli input sul volume il container intero dura 4,6, 5,7 e 69,9 s; la prima esecuzione, che li ha costruiti, 82,2, 48,4 e 845,1 s. Costo fatturato da Modal per l'app nell'ora 20 UTC: 0,175 USD per tre esecuzioni (una completa, due solo join); la coda dopo le 21:00 UTC non è ancora fatturata.

Non verificato: 968 chiamate TypeScript su simboli con pacchetto `. .`; che i 3.755 `local` senza definizione siano tutti di `react-i18next`; le regole Go per `:=` e `var` sono provate su frammenti di sintassi e sui risultati di chi, senza una fixture Go indicizzata in locale.

### 13 novembre 2026, grafo completo dall'indice: Java

Un indicizzatore di progetto intero, scip-java, compila javapoet; il suo indice si legge tutto, ogni documento, occorrenza e simbolo, e diventa il grafo del codice. Ciò che è proprio del motore sta in `adapters/java.py`: `index` (installazione, build, seconda aggregazione, ordine dei membri nei class file) e `hops`, vuoto, più `static` e `same_range` (sotto). Lettura, percorso e grafo sono quelli comuni di `scip_graph.py`; `lang_java.py` collega adattatore, modulo comune e volume. Esecuzione: `modal deploy benchmarks/inference-audit/lang_java.py`, poi `python benchmarks/inference-audit/lang_java.py spawn` e `fetch`; `fetch --files DIR` e `graph --dir DIR` rifanno il grafo dai file sul volume (`inference-audit/graph-java/javapoet/`) senza rieseguire l'indicizzatore. Risultati: `results/graph-java-javapoet.json` (nodi, archi, buchi; 8,5 MB) e `results/graph-java-javapoet-checks.json` (il resoconto comune, accordo con il lessicale, verifica a mano).

| Parametro | Valore |
| --- | --- |
| caso | javapoet `b9017a9503b76e11b4ad4c1a9f050e2d29112cb0` (Maven), 39 file Java: 17 sorgenti, 22 test |
| indicizzatore | scip-java 0.13.2 (`org.scip-code:scip-java`, assemblato con coursier 2.1.24), OpenJDK 17.0.21, Maven 3.8.7 |
| build | il pom senza modifiche non compila su Java 17: Error Prone 2.3.1 dà `class file has wrong version 61.0, should be 53.0`. L'adattatore toglie dal plugin del compilatore `<compilerId>`, `<forceJavacCompilerUse>` e le dipendenze di Error Prone, solo nella copia del checkout |
| relazioni | lo stesso build aggregato una seconda volta con `--no-emit-inverse-relationships`: l'aggregazione di default scrive ogni `is_implementation` anche dal padre al figlio, con gli stessi flag. Si legge l'indice della seconda aggregazione, con occorrenze verificate uguali a quelle del primo |
| arco | quello di `scip_graph.build`: dalla definizione più interna che contiene l'occorrenza (il file, fuori da ogni definizione) a ogni fine del simbolo riferito. Una fine è una funzione, un metodo o una classe che lo snapshot dichiara alla definizione (`project-callable`), un valore del progetto, un esterno con il pacchetto, o un vicolo cieco. Il tipo (`call`, `read`) è quello del riferimento dello snapshot nella stessa posizione, `unknown` dove lo snapshot non ne ha uno: scip-java non scrive ruoli di accesso |
| riferimenti indipendenti | `sem_references` dello snapshot, `call` e `read` |
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

Accordo con il lessicale, sulle 289 chiamate che risolve: 264 sulla stessa dichiarazione, 25 dove il lessicale dà la classe e l'indice il suo costruttore. Il confronto usa la dichiarazione dello snapshot che la lettura comune dà a ogni fine.

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

Tempo e memoria:
- Indicizzatore: 41,1 s, cioè build e indice 39,9 s con la cache Maven vuota più la seconda aggregazione 1,2 s.
- Snapshot 4,4 s; container 54,4 s in tutto.
- RAM: 688 MB il processo più grande, 1.433 MB la somma dei processi del container.
- Costo fatturato da Modal: 0,028 USD per due esecuzioni. In r1 il build senza modifiche è fallito in 28,4 s; r2 ha usato solo il javac semplice. L'indice è lo stesso nelle due esecuzioni (2.266.831 byte).

Il grafo è rifatto in locale dai file di r2 sul volume.

Non verificato:
- Il collegamento Modal dopo il passaggio al modulo comune: `index` di `adapters/java.py` non è stato rieseguito. I comandi di build sono quelli di r2.
- L'overload dei simboli del JDK direttamente sul JDK: la regola del class file è provata solo sui metodi del progetto, e `javap` copre solo le classi esterne della verifica a mano.
- Le destinazioni delle letture e dei riferimenti a tipi, oltre ai 20 casi e alle 289 chiamate.
- Che il build con Error Prone avrebbe dato gli stessi simboli.
- I picchi di RAM fra un campione e l'altro (due al secondo).
- Perché scip-java scrive solo alcune occorrenze di `this` e `super`.
- Altri progetti, Gradle, Java oltre la 17.

### 13 novembre 2026, grafo completo dall'indice: Python

Un indicizzatore di progetto intero, scip-python, indicizza python-semver; il suo indice si legge tutto, ogni documento, occorrenza e simbolo, e diventa il grafo del codice. Ciò che è proprio del motore sta in `adapters/python.py`: `index` (dipendenze dichiarate in una venv, `pyrightconfig.json` per il layout `src`, indice di una copia) e `hops` (quattro salti per ciò che l'indice lascia implicito). `lang_python.py` collega adattatore, lettura SCIP e volume. Esecuzione: `modal deploy benchmarks/inference-audit/lang_python.py`, poi `python benchmarks/inference-audit/lang_python.py spawn --cases semver` e `fetch --cases semver`; `spawn --graph-only` rifà il grafo dai file sul volume (`inference-audit/graph-python/semver/`) senza rieseguire l'indicizzatore. Risultati: `results/graph-python-semver.json` (nodi, archi, buchi; 1,1 MB) e `results/graph-python-semver-checks.json` (fatti dell'indice, conteggi, buchi per classe, verifica a mano).

| Parametro | Valore |
| --- | --- |
| caso | python-semver `b6e83e3e40d3a7570386e8d694ae8011477a55c1`, 35 file Python: 7 sorgenti, 25 test, 3 di documentazione; due test sono symlink a file di `docs/advanced/` |
| indicizzatore | scip-python 0.6.8 (npm), Node v22.23.4, Python 3.13 |
| dipendenze | le 14 dichiarate in `pyproject.toml` (dipendenze opzionali e gruppi PEP 735), installate con uv in una sola chiamata: 87 pacchetti nella venv |
| configurazione | il progetto non configura Pyright: l'adattatore scrive nella copia un `pyrightconfig.json` con `src` come radice e come percorso aggiuntivo. Senza, nessun import assoluto del pacchetto `semver` si risolve e 112 chiamate su 995 arrivano al progetto invece di 458 (prima esecuzione, stesso indicizzatore) |
| snapshot | da una copia dove i symlink sono file normali: `snapshot.py write` sul checkout va in errore con `UNIQUE constraint failed: files.path`, perché nomina un link con il percorso del suo bersaglio |
| arco | dalla definizione più interna che contiene l'occorrenza (`enclosing_range`; il file, fuori da ogni definizione) al simbolo riferito, poi lungo gli alias dichiarati (stesso intervallo, `is_definition`, `is_reference`, `is_implementation`) e i salti dell'adattatore, senza limite di passi e con protezione dai cicli. Si ferma a una funzione, un metodo o una classe del progetto, a un esterno con il suo pacchetto o a un vicolo cieco. Il tipo (`call`, `read`) è quello del riferimento dello snapshot nella stessa posizione, `unknown` altrove: scip-python scrive solo i ruoli definizione e lettura |
| salti | `import-binding`: un nome di `from m import a [as b]` su una riga va al modulo `m`. `builtin`: un nome libero presente in `builtins`, che non sia un attributo o il nome di un argomento, va a `builtins/<nome>`. `classmethod-cls`: il primo parametro di un metodo decorato `classmethod` va alla sua classe. `type-of-self`: un locale `x = type(self)` va alla classe del metodo. Ogni salto resta nella `chain` con il suo nome |
| riferimenti indipendenti | `sem_references` dello snapshot, `call` e `read` |
| verifica a mano | 20 chiamate lette nel sorgente prima di leggere il grafo (`HAND` in `lang_python.py`) |

Copertura: 35 file su 35 hanno un documento con occorrenze; i due symlink sono indicizzati due volte, anche dal loro bersaglio. L'indice ha 4.590 occorrenze e 919 definizioni. I ruoli sono solo definizione e lettura, mai import o scrittura. `SymbolInformation.kind` non è mai valorizzato: la specie viene dal suffisso del simbolo. Relazioni: 11 `is_implementation`, dalle sottoclassi a `Version` e dagli override di `parse`. Nessun alias a intervallo condiviso, nessun campo protobuf non letto.

Nodi: 1.288, cioè 914 simboli definiti, 173 esterni, 34 file da cui partono archi fuori da ogni definizione e 167 simboli riferiti senza definizione (locali e moduli).

Archi: 3.671, per tipo `call` 980, `read` 1.319, `unknown` 1.372.
- Catene: 3.605 senza salti. Le altre 66 hanno un salto: `builtin` 33, `type-of-self` 21, `import-binding` 7, `classmethod-cls` 5.
- Alias e relazioni dell'indice non allungano mai una catena: le relazioni stanno su classi e metodi, che sono già punti di arrivo.

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

Buchi: 15 chiamate e 29 letture dello snapshot senza occorrenza.
- Su un parametro senza tipo, 7 chiamate e 20 letture: attributi di `argparse.Namespace` messi a runtime e fixture pytest (`cli.py:152 args.func`, `cli.py:38 args.bump`, `tests/test_pysemver-cli.py:118 capsys.readouterr`).
- Catene di attributi su valori senza tipo, 5 chiamate (`cli.py:41 args.parser.parse_args`, `tests/test_pysemver-cli.py:119 captured.err.startswith`).
- Callee calcolato, 2 chiamate (`version.py:556`, `:807`).
- `setter` di property, 5 letture (`version.py:217 @major.setter`); `String.__args__` di un alias `typing`, 3 letture (`version.py:56`).
- Locale di tipo ignoto, 1 chiamata e 1 lettura (`tests/test_pysemver-cli.py:43`, `:136`).

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

Tempo e memoria:
- Indicizzatore 9,3 s, 368 MB il processo più grande; snapshot 2,8 s; container 17,6 s; grafo 0,3 s.
- Costo fatturato da Modal: 0,034 USD in tutto, cioè 0,0246 USD per le prime sette chiamate (indice senza e con configurazione, grafi rifatti dal volume) e 0,0096 USD per le ultime tre (due fallite, poi quella buona).

Non verificato:
- Se nella prima esecuzione pesa anche la TomlError di scip-python su `pyproject.toml` (riga 105, probabilmente un array misto, ammesso da TOML 1.0 e non da TOML 0.5), oltre al layout `src` non dichiarato.
- Perché la libreria standard è etichettata 3.11 con Python 3.13.
- La regola `builtin` assume che il file non abbia `import *`: semver non ne ha, l'adattatore non lo controlla. `import-binding` copre solo gli import su una riga.
- Altri progetti Python: httpx non è stato aggiunto perché semver ha 995 chiamate. Nessun confronto con il passo dei motori (Jedi) su questo caso.

Con il modulo comune `scip_graph.py`, la stessa sera:
- `lang_python.py` ora collega solo adattatore, `scip_graph.py` e volume; `adapters/python.py` segue il contratto del modulo (`index` restituisce `indexes`, `indexer` e `runs`; `hops` le quattro regole sopra).
- Il grafo in `results/` è rifatto in locale dall'indice di questa esecuzione (`python benchmarks/inference-audit/lang_python.py graph --cases semver --dir DIR`), senza nuove esecuzioni su Modal. Il nuovo collegamento non è ancora stato eseguito su Modal.
- Le fini dirette coincidono con i conteggi sopra: chiamate e letture divise allo stesso modo, verifica a mano 18 su 20, 3.671 archi dai riferimenti.
- 3.679 archi invece di 3.671: il modulo dà a ogni riferimento a un membro anche le sue implementazioni, tranne nei siti a dispatch statico che l'adattatore dichiara (`static`: `C.m` su un simbolo di classe e `super().m`, 109 siti). Restano 8 archi `implementation`, da `cls.parse` (`version.py:479`, `:833`) verso i quattro override `SemVerWithVPrefix.parse`. Senza `static` sarebbero 372: ogni `Version.parse(...)` e `super().parse(...)` riceveva anche gli override, che lì non vengono mai eseguiti.
- 64 buchi invece di 44: il modulo conta anche i riferimenti che finiscono solo in un vicolo cieco (10 locali senza definizione, 10 simboli del progetto senza definizione).
- 1.289 nodi invece di 1.288: ogni documento è un nodo. Un parametro o un locale definito è un `project-value`, non un vicolo cieco.

### 13 novembre 2026, grafo completo dall'indice: Go, Rust, JavaScript e TypeScript

Bozza. Il codice ora è diviso in due parti:
- `scip_graph.py`, comune e senza linguaggi: legge l'indice, segue le catene e monta il grafo;
- un adattatore per indicizzatore (`adapters/go.py`, `adapters/rust.py`, `adapters/typescript.py`) con due funzioni. `index(...)` installa ed esegue l'indicizzatore. `hops(index)` dichiara gli alias che quel motore scrive a modo suo.

Gli alias degli adattatori:
- `initializer`, `pattern-key` e `value`: un nome definito come alias di un altro, come chiave di un pattern, o con una funzione come valore;
- `declared:@types/react.useCallback` e `declared:@types/react.useMemo`: librerie che per contratto restituiscono il loro argomento, riconosciute dal simbolo esterno e dal pacchetto, mai dal nome;
- `rust:module-file`: un modulo incluso da più crate.

Dove sono i risultati:
- il grafo di ogni lingua è sul volume, in `scip-inputs/<caso>/graph-<lingua>.json.gz`;
- i conteggi sono in `results/scip-chi-graph.json` e `results/scip-tududi-graph.json`;
- per tududi li ho calcolati in locale dai file del grafo, perché ho fermato l'esecuzione al tetto di spesa prima che scrivesse il suo risultato.

Prima del grafo gli indicizzatori sono stati rieseguiti con gli adattatori:
- l'indice di chi è identico byte per byte (1.632.115, 64.652 e 39.509 byte);
- tududi è stato reindicizzato in 55,3 s, con un picco di 2.193 MB;
- semver non ha un grafo: l'esecuzione si è fermata due volte per la stessa causa, le sorgenti dello snapshot cercate in `/work/semver`.

Archi per fine della catena:

| Lingua | File snapshot / indicizzati | Nodi | Archi | Funzione, metodo o classe del progetto | Valore del progetto | Esterno | Vicolo cieco |
| --- | --- | --- | --- | --- | --- | --- | --- |
| chi Go | 90 / 90 | 4.847 | 20.102 | 3.357 | 9.094 | 7.651 | 0 |
| tududi JavaScript | 1.038 / 1.038 | 86.225 | 182.593 | 16.407 | 86.442 | 70.944 | 8.800 |
| tududi TypeScript | 650 / 650 | 41.107 | 171.821 | 15.147 | 64.977 | 84.067 | 7.630 |

Un arco va dalla definizione che racchiude l'occorrenza alla fine della catena. Ha tipo `call` o `read` quando lo snapshot ha un riferimento in quella posizione, `unknown` altrimenti.

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

Lacune dell'indice, contate come buchi:
- TypeScript, 3.755 chiamate finiscono su un `local` che nessun documento definisce (`t` di `useTranslation`, `frontend/Layout.tsx:497`).
- JavaScript, 61 chiamate sono metodi abbreviati di un oggetto in un altro file (`backend/modules/admin/service.js:1085`, `backend/modules/inbox/operations/attachments.js:59`, `backend/modules/onboarding/controller.js:26`). L'indice non ha nessun dato nello stesso file e intervallo, quindi restano buchi.
- Rust, modulo di test condiviso: lo recupera `rust:module-file`, sulla fixture 2 chiamate su 2; su semver non è misurato.

Pacchetti esterni più riferiti, per archi (i venti completi sono nei file dei risultati):
- chi, otto in tutto: Go standard 1.24 7.128, Go 1.22 168, Go 1.16 117, `go-chi/chi/v5@v5.1.0` 99, `go-chi/render@v1.0.1` 57, `go-chi/chi/v5@v5.2.4` 51, `go-chi/render@v1.0.3` 24, `go-chi/docgen@v1.2.0` 7;
- JavaScript: `@types/jest` 28.976, `typescript` 24.037, `@types/node` 10.600, `sequelize` 2.935, `@types/express-serve-static-core` 886, `@testing-library/jest-dom` 702, `moment` 684, `stripe` 566, `moment-timezone` 326, `@types/express` 324;
- TypeScript: `@types/react` 30.064, `typescript` 25.244, `@types/jest` 8.879, `@testing-library/dom` 4.151, `@types/node` 2.733, `@testing-library/jest-dom` 2.328, `react-i18next` 2.020, pacchetto `. .` 2.015, `react-router` 1.396, `playwright` 761.

Prova a mano: 15 chiamate per lingua, scelte a caso fra tutte quelle del checkout (seme 20261113). Ho scritto la destinazione attesa leggendo il sorgente, prima di guardare il grafo; le attese sono in `HAND` di `modal_scip.py`.

| Lingua | Giuste per il grafo | Giuste per A |
| --- | --- | --- |
| chi | 15 / 15 | 13 / 15 (`NewRouter` e `GetLogEntry` non chieste) |
| JavaScript | 12 / 15 | non confrontata |
| TypeScript | 14 / 15 | non confrontata |

Le quattro sbagliate non hanno nessuna occorrenza nell'indice:
- `queryInterface.addIndex`: parametro senza tipo;
- `lastModified.toJSDate`: valore `any` di ical.js;
- `Task.create`: modello Sequelize costruito a runtime;
- `tag.slice`, in `frontend/components/Inbox/__tests__/QuickCaptureInput.focus.test.tsx:88`.

Costo fatturato da Modal per l'app: 0,175 USD nell'ora 20 UTC e 0,108 nell'ora 21 UTC, 0,283 in tutto. Il totale comprende i riavvii a vuoto di un container che non trovava le sorgenti del plugin e l'esecuzione di tududi fermata al tetto.

Non verificato:
- il grafo di semver;
- il confronto con A sul codice nuovo, per tududi;
- perché `fireEvent.click` non ha occorrenze;
- il pacchetto `. .`.

### 13 novembre 2026, grafo completo dall'indice: Kotlin

scip-java indicizza klaxon con la build Gradle del progetto. Il suo indice si legge tutto, ogni documento, occorrenza e simbolo, e diventa il grafo del codice. Ciò che è proprio del motore sta in `adapters/kotlin.py`:
- `index`: JDK, scip-java, build e copia dell'indice senza le relazioni inverse;
- `hops`, vuoto;
- `classify`, `missing` e `refine`, descritti sotto.

Lettura, percorso e grafo sono quelli comuni di `scip_graph.py`; `lang_kotlin.py` collega adattatore, modulo comune e volume e tiene la verifica a mano.

Esecuzione: `modal deploy benchmarks/inference-audit/lang_kotlin.py`, poi `python benchmarks/inference-audit/lang_kotlin.py spawn --stage index` e `fetch`. `spawn --stage graph` rifà il grafo dai file sul volume (`inference-audit/graph-kotlin/klaxon/`: index.scip, index-forward.scip, manifest.sqlite, indexer.json, kotlin-configs/) senza rieseguire l'indicizzatore, e scrive lì anche `graph.json` (nodi, archi con catena e incertezza, buchi). `graph --index --manifest --source --configs --out` fa lo stesso in locale. Risultato: `results/graph-kotlin-klaxon.json` (il resoconto comune, archi incerti, buchi, verifica a mano).

| Parametro | Valore |
| --- | --- |
| caso | klaxon `1173bdc568a6d339b45cf24a6a9c5c2f6847f42d`, Gradle wrapper 7.3, Kotlin 1.6.0; 103 file Kotlin nello snapshot, test compresi |
| indicizzatore | scip-java 0.14.2 (`org.scip-code:scip-java`, classpath di coursier 2.1.24) con scip-kotlin-analysis 0.14.2, cioè la Kotlin Analysis API di kotlin-compiler 2.4.0; Temurin 17.0.21 |
| build | `scip-java index`: `gradlew` con l'init script di scip-java (`clean scipPrintDependencies scipCompileAll`). Ogni task KotlinCompile scrive sorgenti e classpath in `kotlin-configs/`, poi l'indicizzatore li analizza fuori dal compilatore, quindi la versione Kotlin del progetto non conta. La 0.13.0 ha tolto il supporto ufficiale per Gradle < 8, ma con la 7.3 la build va al primo tentativo |
| relazioni | l'indicizzatore scrive `is_implementation` sul membro che sovrascrive, verso quello sovrascritto. L'aggregatore aggiunge l'inversa sul sovrascritto, con `is_implementation` e `is_reference` (`ScipAggregator.java`). `forward_only` ne toglie 30, tutte doppioni di una relazione diretta, e si legge `index-forward.scip` |
| pacchetti | scip-java scrive il segnaposto `. .` sia per i simboli dei test del progetto sia per ogni builtin e simbolo della stdlib. `classify` lo tiene simbolo del progetto solo sotto un percorso di package dove l'indice definisce simboli `. .`; altrove è un esterno con manager `unknown`, il percorso Kotlin (`kotlin/collections`) e versione `unknown`. I simboli di package (righe `package` e `import`) sono namespace |
| arco | quello di `scip_graph.build`, come per Java; la regola comune di `same-range` non fa alias fra due definizioni allo stesso range |
| incertezza | `refine` marca `overload-across-tasks` un arco verso una funzione del progetto con overload, riferita da un altro task di compilazione; `override-across-tasks` un'implementazione con overload fra task diversi. I candidati sono tutti gli overload del nome nella classe. Un arco incerto resta nel grafo |
| buchi impliciti | `x[k]`, `x[k] = v`, l'iteratore del `for`, i delegati `by` e i `componentN`, trovati con tree-sitter dove l'indice non ha un'occorrenza non locale: classe `implicit-operator` |
| riferimenti indipendenti | `sem_references` dello snapshot, `call` e `read` |
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
| valore del progetto (proprietà, getter sintetici, parametri, locali) | 3.739 |
| esterno Maven con versione | 1.594 |
| esterno con manager `unknown` e percorso Kotlin | 2.104 |
| esterno "fuori dallo snapshot" | 23 |
| namespace | 1.079 |
| vicolo cieco | 2 |

- Tipo dell'arco: `call` 3.274, `read` 2.215, `unknown` 10.702. scip-java non scrive ruoli di accesso, quindi il tipo viene dal riferimento dello snapshot nella stessa posizione.
- Catene: un riferimento alla proprietà porta anche al getter (e al setter se è `var`), scritti dall'indice allo stesso range, quindi nessun salto. Le implementazioni sono tutte a un salto. Ne portano di più `kotlin/Any#equals` e `toString`, con 94 e 98 override del progetto, compresi quelli generati delle data class. Solo 6 archi passano per `same-range`.
- I 23 esterni "fuori dallo snapshot" sono simboli di `klaxon/src/test/kotlin/com/beust/klaxon/Issue118Test.kt`. Lo snapshot tiene quel file solo come lessicale e la lettura comune non lo riconosce come file del progetto.

Archi incerti: 238 `overload-across-tasks` e 13 `override-across-tasks`.
- Il motivo: per una dichiarazione con sorgente, il numero `(+N)` segue l'ordine del sorgente (`SymbolsCache.kt`). Per una letta dal classpath di un altro task segue l'ordine della classe compilata, quindi la stessa stringa può nominare un altro overload.
- Overload: `Klaxon#parse` 78, `Klaxon#toJsonString` 49, `KlaxonJson#obj` 38, `Parser#parse` 33, `KlaxonJson#array` 17, `Klaxon#parseArray` 12, il costruttore di `JsonArray` 9, `Klaxon#parseJsonObject` 2.
- Override: i 13 sono tutti verso `JacksonParser#parse()`.
- Nella misura precedente con controllo del numero di argomenti, la stessa causa dava 86 chiamate da un altro task in contraddizione con il bersaglio e 14 su 14 sbagliate in un campione letto a mano. Nello stesso task le contraddizioni erano 0 su 37.

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

Tempo e memoria:
- Indicizzatore 111,0 s, compresi lo scaricamento di Gradle e la build (1m33s).
- Prima esecuzione completa (clone, snapshot, indice, grafo) 128,9 s; il solo grafo dal volume 3,3 s.
- RAM: 4.688 MB come somma dei processi del container, campionata ogni 0,5 s.
- Costo fatturato da Modal: 0,029 USD per un'esecuzione con l'indicizzatore e tre solo per il grafo (l'ultima fascia oraria forse non ancora chiusa).

Non verificato:
- Il collegamento Modal di `index` in `adapters/kotlin.py` dopo il passaggio al modulo comune: non è stato rieseguito. I comandi sono quelli della prima esecuzione, ma la memoria ora si misura sul processo più grande.
- Uno per uno, gli archi incerti che il numero di argomenti non smentisce.
- La regola dell'ordine compilato: osservata nei dati, non letta nel codice dell'Analysis API.
- Perché i task di scip-java non girano in buildSrc: lo dice solo il log.
- I picchi di RAM fra un campione e l'altro, sotto gVisor.
- Altri progetti Kotlin, Gradle 8 e oltre, Android, Kotlin Multiplatform.
