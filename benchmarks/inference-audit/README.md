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
