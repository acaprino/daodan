# Benchmark: cosa danno gli indicizzatori e cosa ne usa Daodan

Verifica, per ogni linguaggio, il grafo che Daodan costruisce dall'indice SCIP di un indicizzatore esistente e, accanto, le seconde fonti del programma intero: cosa l'indice dichiara, cosa arriva al grafo e ai collegamenti dei flussi, dove resta un buco e di che classe. Nessun modello; tutto gira su Modal.

## Domande

| Domanda | Cosa si conta |
| --- | --- |
| Cosa arriva al grafo dal passo del prodotto | riferimenti risolti nella vista degli archi (`edge_view`), candidati e conflitti; fra i riferimenti risolti, quelli che diventano un collegamento dei flussi e quelli che si perdono (destinazione senza dichiarazione, chiamata fuori da un simbolo) |

## Parametri

| Parametro | Valore |
| --- | --- |
| casi | tududi `71da9d7b34dfd1600657e9c5ddf40420206fd263` (JavaScript, TypeScript), javapoet `b9017a9503b76e11b4ad4c1a9f050e2d29112cb0` (Java), klaxon `1173bdc568a6d339b45cf24a6a9c5c2f6847f42d` (Kotlin), semver `280ebcb6edac3aa4cdc545dbff8a26c5ac4861fe` (Rust), chi `c64ed7d6635f33a8b2feaff7dcfa55677023ac7d` (Go) |
| passo | quello del prodotto: `snapshot.py write --no-engine --no-index`, poi `resolve_edges.py --pass` |
| regole dei flussi | `benchmarks/tududi-flow/rules.json`; gli altri casi senza regole contano solo la vista degli archi |

Esecuzione: `modal run --detach benchmarks/inference-audit/modal_audit.py`; un container per caso, risultati sul volume `daodan-flow-results`.

## Risultati

### 13 novembre 2026, indice SCIP contro motori

Strada A: il passo dei motori per posizione, misurato come il prodotto lo eseguiva il 13 novembre (`resolve_edges.py --pass`, una posizione per volta, solo chiamate). Strada B: l'indice SCIP dell'intero progetto da un indicizzatore esistente, unito per posizione ai riferimenti dello snapshot (`call` e `read`) e graduato con le stesse regole del passo (`grade_all`, simboli `local` compresi). App `daodan-scip-audit` (`modal_scip.py`), risultati in `results/scip-<caso>.json`.

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

Confermato su Modal dopo il passaggio al modulo comune (esecuzione `confirm`, pipeline completa, codice uguale al checkout per hash): stessi 3.541 nodi, 19.189 archi e 10 buchi, verifica a mano 20 su 20, stesso indice (2.266.831 byte). Indicizzatore 37,7 s e 639 MB, container 48,1 s, 0,010 USD. I file in `results/` vengono da questa esecuzione.

Non verificato:
- L'overload dei simboli del JDK direttamente sul JDK: la regola del class file è provata solo sui metodi del progetto, e `javap` copre solo le classi esterne della verifica a mano.
- Le destinazioni delle letture e dei riferimenti a tipi, oltre ai 20 casi e alle 289 chiamate.
- Che il build con Error Prone avrebbe dato gli stessi simboli.
- I picchi di RAM fra un campione e l'altro (due al secondo).
- Perché scip-java scrive solo alcune occorrenze di `this` e `super`.
- Altri progetti, Gradle, Java oltre la 17.

### 13 novembre 2026, grafo completo dall'indice: Python

Un indicizzatore di progetto intero, scip-python, indicizza python-semver; il suo indice si legge tutto, ogni documento, occorrenza e simbolo, e diventa il grafo del codice. Ciò che è proprio del motore sta nel modulo `indexers/python.py` del plugin: `index` (dipendenze dichiarate in un ambiente della cartella condivisa, solo wheel, date a scip-python con `--environment`; `pyrightconfig.json` per il layout `src`; indice di uno specchio del progetto) e `hops` (quattro salti per ciò che l'indice lascia implicito). `lang_python.py` collega modulo, lettura SCIP e volume. Esecuzione: `modal deploy benchmarks/inference-audit/lang_python.py`, poi `python benchmarks/inference-audit/lang_python.py spawn --cases semver` e `fetch --cases semver`; `spawn --graph-only` rifà il grafo dai file sul volume (`inference-audit/graph-python/semver/`) senza rieseguire l'indicizzatore. Risultati: `results/graph-python-semver.json` (nodi, archi, buchi; 1,1 MB) e `results/graph-python-semver-checks.json` (fatti dell'indice, conteggi, buchi per classe, verifica a mano).

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
- `lang_python.py` collega solo il modulo `indexers/python.py`, `scip_graph.py` e volume; il modulo segue il contratto (`index` restituisce `indexes`, `indexer` e `runs`; `hops` le quattro regole sopra).
- Confermato su Modal (pipeline completa, codice uguale al checkout per hash): stessi 1.289 nodi, 3.679 archi e 64 buchi del rifacimento locale. Indicizzatore 7,5 s e 369 MB, container 15,3 s, 0,004 USD. I file in `results/` vengono da questa esecuzione.
- Le fini dirette coincidono con i conteggi sopra: chiamate e letture divise allo stesso modo, verifica a mano 18 su 20, 3.671 archi dai riferimenti.
- 3.679 archi invece di 3.671: il modulo dà a ogni riferimento a un membro anche le sue implementazioni, tranne nei siti a dispatch statico che l'adattatore dichiara (`static`: `C.m` su un simbolo di classe e `super().m`, 109 siti). Restano 8 archi `implementation`, da `cls.parse` (`version.py:479`, `:833`) verso i quattro override `SemVerWithVPrefix.parse`. Senza `static` sarebbero 372: ogni `Version.parse(...)` e `super().parse(...)` riceveva anche gli override, che lì non vengono mai eseguiti.
- 64 buchi invece di 44: il modulo conta anche i riferimenti che finiscono solo in un vicolo cieco (10 locali senza definizione, 10 simboli del progetto senza definizione).
- 1.289 nodi invece di 1.288: ogni documento è un nodo. Un parametro o un locale definito è un `project-value`, non un vicolo cieco.

### 13 novembre 2026, grafo completo dall'indice: Go, Rust, JavaScript e TypeScript

Bozza. Il codice ora è diviso in due parti:
- `scip_graph.py`, comune e senza linguaggi: legge l'indice, segue le catene e monta il grafo;
- un modulo per indicizzatore nel plugin (`indexers/go.py`, `indexers/rust.py`, `indexers/typescript.py`, `indexers/python.py`) con due funzioni. `index(...)` scarica l'indicizzatore nella cartella condivisa e lo esegue in uno specchio del progetto. `hops(index)` dichiara gli alias che quel motore scrive a modo suo.

Gli alias degli adattatori:
- `initializer`, `pattern-key` e `value`: un nome definito come alias di un altro, come chiave di un pattern, o con una funzione come valore;
- `declared:@types/react.useCallback` e `declared:@types/react.useMemo`: librerie che per contratto restituiscono il loro argomento, riconosciute dal simbolo esterno e dal pacchetto, mai dal nome;
- `rust:module-file`: un modulo incluso da più crate.

Dove sono i risultati:
- il grafo di ogni lingua è sul volume, in `scip-inputs/<caso>/graph-<lingua>.json.gz`;
- i conteggi sono in `results/scip-<caso>-confirm.json`, dall'esecuzione di conferma (sotto).

Prima del grafo gli indicizzatori sono stati rieseguiti con gli adattatori:
- l'indice di chi è identico byte per byte (1.632.115, 64.652 e 39.509 byte);
- tududi è stato reindicizzato in 55,3 s, con un picco di 2.193 MB;
- semver è stato reindicizzato in 8,7 s, 1.180 MB, con un indice identico byte per byte (496.873 e 14.108 byte).

Archi per fine della catena:

| Lingua | File snapshot / indicizzati | Nodi | Archi | Funzione, metodo o classe del progetto | Valore del progetto | Esterno | Vicolo cieco |
| --- | --- | --- | --- | --- | --- | --- | --- |
| chi Go | 90 / 90 | 4.847 | 20.102 | 3.357 | 9.094 | 7.651 | 0 |
| semver Rust | 19 / 18 | 1.073 | 3.960 | 1.023 | 1.306 | 1.572 | 59 |
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
- Rust, modulo di test condiviso: lo recupera `rust:module-file`, sulla fixture 2 chiamate su 2. Su semver arrivano così 181 delle 186 chiamate che solo A risolveva, tutte sullo stesso bersaglio di A. Le 5 restanti non sono nell'indice: 3 `string.parse` (`core`) e 2 in `tests/node/mod.rs`, senza documento.

Pacchetti esterni più riferiti, per archi (i venti completi sono nei file dei risultati):
- chi, otto in tutto: Go standard 1.24 7.128, Go 1.22 168, Go 1.16 117, `go-chi/chi/v5@v5.1.0` 99, `go-chi/render@v1.0.1` 57, `go-chi/chi/v5@v5.2.4` 51, `go-chi/render@v1.0.3` 24, `go-chi/docgen@v1.2.0` 7;
- JavaScript: `@types/jest` 28.976, `typescript` 24.037, `@types/node` 10.600, `sequelize` 2.935, `@types/express-serve-static-core` 886, `@testing-library/jest-dom` 702, `moment` 684, `stripe` 566, `moment-timezone` 326, `@types/express` 324;
- TypeScript: `@types/react` 30.064, `typescript` 25.244, `@types/jest` 8.879, `@testing-library/dom` 4.151, `@types/node` 2.733, `@testing-library/jest-dom` 2.328, `react-i18next` 2.020, pacchetto `. .` 2.015, `react-router` 1.396, `playwright` 761.

Prova a mano: 15 chiamate per lingua, scelte a caso fra tutte quelle del checkout (seme 20261113). Ho scritto la destinazione attesa leggendo il sorgente, prima di guardare il grafo; le attese sono in `HAND` di `modal_scip.py`.

| Lingua | Giuste per il grafo | Giuste per A |
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

Costo fatturato da Modal per l'app: 0,175 USD nell'ora 20 UTC e 0,108 nell'ora 21 UTC, 0,283 in tutto. Il totale comprende i riavvii a vuoto di un container che non trovava le sorgenti del plugin e l'esecuzione di tududi fermata al tetto.

Confermato su Modal con un'esecuzione completa per caso (etichetta `confirm`, indicizzatori rieseguiti, codice uguale al checkout per hash):
- chi e tududi: stessi nodi, archi e fini della tabella; indici identici byte per byte (tududi 44.550.689 byte, 55,2 s, 2.264 MB);
- semver Rust, la prima volta: la riga della tabella. Archi `call` 776, `read` 713, `unknown` 2.471. Catene verso una funzione del progetto: 733 a 0 salti, 290 a 1 (`rust:module-file` 260, inizializzatore 22, funzione assegnata 8). Buchi 24: 18 in `tests/node/mod.rs`, senza documento; 5 callee dinamici senza nome (`benches/parse.rs:8`); 1 senza occorrenza (`src/identifier.rs:326` `repr.trailing_zeros`). I 59 vicoli ciechi sono simboli del progetto che rust-analyzer riferisce senza definirli: 57 impl generati da `derive` (`impl#[Op][PartialEq<Self>]eq()`), 2 `QuotedChar#0.`; rust-analyzer registra 84 errori `definition should have been in an SCIP document`;
- A contro il grafo sul codice nuovo, tududi: JavaScript 12.709 stesse destinazioni, 58 solo A, 119 solo B, 0 diverse; TypeScript 7.023, 0, 155, 0. I solo B di TypeScript salgono da 10 a 155: la crescita è pari alle 145 chiamate che ora arrivano al progetto per `declared:@types/react.useCallback`, dove A, negli esempi, risponde `project-not-a-symbol`;
- container: chi 14,9 s, semver 28,4 s, tududi 651,4 s (snapshot e risposte di A dal volume, installazione dei pacchetti JS e indice rifatti). Costo fatturato: 0,082 USD per chi, semver e tududi, nella fascia delle 22 UTC non ancora chiusa.

Non verificato:
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
- Confermato su Modal dopo il passaggio al modulo comune (`spawn --stage index`, pipeline completa, codice uguale al checkout per hash): stessi conteggi, archi incerti e buchi, verifica a mano 16 su 20. Indicizzatore 107,2 s e 2.205 MB il processo più grande, container 125,6 s, circa 0,016 USD (0,028 nella fascia delle 22 UTC, meno 0,013 delle esecuzioni precedenti).
- Costo fatturato da Modal: 0,029 USD per un'esecuzione con l'indicizzatore e tre solo per il grafo (l'ultima fascia oraria forse non ancora chiusa).

Non verificato:
- Uno per uno, gli archi incerti che il numero di argomenti non smentisce.
- La regola dell'ordine compilato: osservata nei dati, non letta nel codice dell'Analysis API.
- Perché i task di scip-java non girano in buildSrc: lo dice solo il log.
- I picchi di RAM fra un campione e l'altro, sotto gVisor.
- Altri progetti Kotlin, Gradle 8 e oltre, Android, Kotlin Multiplatform.

### 14 novembre 2026, grafo delle chiamate del programma intero: Go

Domanda: l'analisi del programma intero di Go chiude i due buchi dell'indice di chi (quale funzione gira dietro un'interfaccia o un valore funzione) senza inventare archi?

| Parametro | Valore |
| --- | --- |
| motore | `golang.org/x/tools/cmd/callgraph` v0.52.0 (10 ottobre 2026), `-algo=vta -test`, Go 1.27.3, installato con `go install` (somme controllate dal database dei checksum) |
| perimetro | il modulo radice in un colpo: `./...` più le dieci cartelle `_examples/*` che il pattern salta; fuori i moduli annidati `_examples/rest` e `_examples/versions` |
| caso | chi `c64ed7d6`, con snapshot, indici e grafo già sul volume (`scip-inputs/chi/`) |
| unione | ogni chiamata dello snapshot va al sito che SSA dichiara: la `(` della chiamata, o la parola `go` / `defer` |
| file | `adapters/go_callgraph.py`, `strong_go.py` (app `daodan-strong-go`), `results/strong-go-chi.json`; l'uscita dell'adattatore resta sul volume (`strong-go-chi-callgraph.json.gz`) |

Esecuzione: `modal deploy benchmarks/inference-audit/strong_go.py`, poi `python benchmarks/inference-audit/strong_go.py spawn` e `fetch`.

Il grafo dell'indice è rifatto nel container con `scip_graph.py` e gli `hops` di Go invariati: 20.102 archi, identici uno per uno a quelli sul volume.

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

Motore: 5,5 s e 840 MB di picco (prima esecuzione 7,8 s e 879 MB); 13,6 s contando `go install` dello strumento; container 19,2 s. Costo fatturato da Modal: 0,016 USD per le due esecuzioni, fascia delle 23 UTC forse non chiusa. La prima esecuzione assegnava la parola `defer` di `defer f()()` alla chiamata interna; corretto, i numeri sopra sono della seconda.

Non verificato:
- i 237 candidati scartati uno per uno (letti 4: `middleware/middleware.go:9`, `middleware/recoverer.go:66`, `mux.go:90`, `middleware/wrap_writer.go:102`);
- uno per uno, i 62 bersagli di `chain.go:43` e i 46 di `mux.go:283`;
- un secondo giro di VTA con il primo come grafo iniziale (solo da libreria, non dal comando), che potrebbe togliere l'errore di `maybe.go:13`;
- i moduli annidati analizzati a parte, i generici (il pacchetto `vta` si dichiara sperimentale e ha un TODO sulle istanze), altri progetti Go.

### 14 novembre 2026, domande mirate e grafo dal compilato: Java e Kotlin

Verdetto:
- Domande mirate (Kotlin Analysis API): sì, chiudono i casi di Kotlin. Tutti i 251 archi incerti di klaxon diventano certi e l'overload scelto è sempre fra i candidati del grafo; quello dell'indice è giusto solo in 14. Tutte le 93 chiamate implicite hanno un bersaglio. 2.258 domande in 9,5 s. Dei 2.104 riferimenti senza pacchetto, 831 finiscono in un jar con versione; 1.236 restano builtin di Kotlin, senza jar.
- Grafo dal compilato (WALA): non vale come potatura della dispatch. Con il test runner modellato, RTA su javapoet non toglie nulla oltre CHA. Su klaxon toglie solo implementazioni create per riflessione, che a runtime girano. Vale invece come controllo economico sull'indice, sulla build già fatta (17-22 s, 2,5-2,8 GB): toglie la dispatch dove non c'è (`==` di Kotlin, `super`, metodi astratti, tipo statico del ricevente).

Esecuzione: `modal deploy benchmarks/inference-audit/strong_jvm.py`, poi `python benchmarks/inference-audit/strong_jvm.py spawn` e `fetch --raw DIR`. `compare --raw DIR --graphs DIR --javapoet SRC --klaxon SRC` rifà il confronto in locale dalle risposte grezze, che restano sul volume in `inference-audit/strong-jvm/`. Risultato: `results/strong-jvm.json`.

| Parametro | Valore |
| --- | --- |
| casi | javapoet `b9017a9` e klaxon `1173bdc`, ricostruiti con la build dei grafi (`adapters/java.py`, `adapters/kotlin.py`); grafi e indice di klaxon presi dal volume |
| domande mirate | `adapters/kotlin_analysis.py` con `adapters/KotlinAsk.kt` (dal 27 novembre 2026 `daodan/core/indexers/KotlinAsk.kt`, del prodotto), una copia del resolver della mappa (Analysis API di KSP 2.3.13, Kotlin 2.4.21, standalone). Un modulo sorgente per task di compilazione e un modulo libreria per jar, letti dai `kotlin-configs/` di scip-java. Ogni risposta dice callable, parametri, origine, posizione o jar. Modi: `ref` sull'occorrenza, `implicit` sulla riga, `overridden` sulla dichiarazione |
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

### 14 novembre 2026, grafo dei fogli di stile: CSS

Aggiornato lo stesso giorno con tutti i dialetti, i blocchi `<style>` e la regola di pagina: cosa cambia è nei punti marcati «Ora», le misure nuove nelle sezioni in fondo («fogli di stile su progetti reali»). Le cifre qui sotto restano quelle dei primi due giri su tududi.

Verdetto: su tududi il grafo è corretto e completo per i file che legge. La verifica a mano dà 20 su 20. Su 1.708 file dati non ne manca nessuno, e un file che nessun lettore prende ora finisce fra i mancanti con il motivo, mai perso.

Font Awesome 6.4.0 sta in `vendor/`, fuori dallo snapshot, ma le pagine della landing lo caricano: ora è letto come foglio esterno, e le sue classi finiscono su nodi esterni con pacchetto e versione. I buchi rimasti hanno ciascuno la sua classe. I falsi `no-rule` non ci sono più: diventano `css-in-js` (24), `tailwind-named-group` (2) ed `ejs-glued` (5).

Un difetto nuovo: con Font Awesome letto si vede il buco della pagina. 7 archi vanno da `sr-only` dell'app React alla regola `.sr-only` di Font Awesome, che l'app non carica.

Nessuno strumento esistente collega i nomi CSS fra file e markup. Gli strumenti leggono e dicono cosa c'è; il collegamento per nome lo fa `adapters/css.py`.

Cos'è il grafo di un foglio di stile. Non ci sono chiamate: ci sono nomi che la cascata risolve quando la pagina gira.
- Nodi: regole (per selettore appiattito, con le at-rule intorno), `@keyframes`, `@font-face` (per famiglia), `@property`, dichiarazioni di proprietà custom (`--x`, nei fogli, negli attributi `style`, negli oggetti `style` e in `setProperty` degli script, nelle proprietà arbitrarie Tailwind `[--x:...]`), nomi di container, prima comparsa di un `@layer` nel file, variabili e mixin Sass, file. Le utility Tailwind sono nodi esterni (pacchetto e versione).
- Fogli esterni: un foglio che il progetto carica da fuori dello snapshot (un pacchetto in `node_modules`, un file del checkout fuori perimetro come `vendor/`, un link CDN) è letto come esterno. I nomi che dichiara diventano nodi esterni (`<foglio> .classe`, `<foglio> --x`, `<foglio> @keyframes x`), creati solo quando un riferimento li raggiunge.
  - Pacchetto e versione: dal `package.json`, dall'URL della CDN (jsDelivr, unpkg, cdnjs), dal commento iniziale (`/*! Font Awesome Free 6.4.0 ...`) o dalla cartella dopo `vendor/`. Altrimenti `unknown`. Il campo `from` dice da dove vengono.
- Correzione rispetto alla richiesta: classi e id non sono nodi del progetto. Sono nomi portati dalle regole: l'arco va a ogni regola che li nomina. Le classi di un CSS Module sono nomi della regola con l'ambito del modulo.
- Archi nei fogli: `var(--x)` a tutte le dichiarazioni di `--x`; `animation` a `@keyframes`; `font-family` e `font` a ogni `@font-face` della famiglia; `@container` al nome; un `@layer` ripetuto alla sua prima comparsa (che fissa l'ordine); `@import`, `@use`, `@forward` al file; `composes` alle regole; `$x`, `ns.$x` e `@include` attraverso gli ambiti di `@use`, `@forward` e `@import`.
- Archi da markup e codice: `class`, `className`, `*ClassName`, `id`, `classList`, `setAttribute`, `clsx`, `classnames` e `tailwind-merge` (riconosciuti dal pacchetto che dichiara la funzione, mai dal nome), `@apply`, `@extend`, `styles.foo` dei CSS Module, `<link rel=stylesheet>` e `import './x.css'`.
- Un percorso URL (`/landing-assets/x.css`) va ai file del checkout che finiscono con la sua coda più lunga. La coda è il percorso intero, o almeno i suoi ultimi due segmenti. La regola è `url-suffix`; più file trovati danno archi incerti.
- Più dichiarazioni dello stesso nome. Per proprietà custom, keyframes e container la cascata ne sceglie una per elemento: sono archi `uncertain`, uno per candidato, ciascuno con la lista intera. Le regole di una classe e i `@font-face` di una famiglia valgono tutti insieme: archi certi.
- Buco: un nome che nessuno dichiara (`no-rule`, `undeclared`...). Il buco è `css-in-js` quando un oggetto di uno script ha una chiave selettore, con un blocco di dichiarazioni come valore, che nomina quella classe; `tailwind-named-group` per `group/x` e `peer/x`. Buco anche una classe costruita a runtime, con la sua forma: `template`, `concatenation`, `ejs` (solo il tag), `ejs-glued` (testo incollato al tag), `parameter`, `call`, `property`, `element-access`, `variable`. Mai una supposizione.
- File non letti: un foglio o un file di markup che nessun lettore prende va in `files.missing` con il motivo. `indexed` conta solo i file letti per intero.
  - Ora: SCSS e Sass indentato con `sass-parser`, Less con `less`, Stylus con `stylus`, Vue, Svelte e Astro con i loro compilatori (blocchi `<style>` per dialetto, scoped, module, `:global`, `:deep`, `v-bind()`, `class:list`, `:class`, `class:name`). Restano fuori solo i linguaggi di template diversi da HTML ed EJS (Handlebars, Nunjucks, Twig, Pug, Liquid, Jinja).
- Ora, regola di pagina: un'unità è una pagina HTML/EJS che nessun template include, con i suoi include, i fogli che linka o contiene, gli script che carica e i loro import; oppure un bundle di moduli che nessuna pagina carica, con i fogli importati e i blocchi `<style>` dei componenti. Un foglio porta i fogli che importa; Tailwind viene con il foglio che lo carica. Un arco di classe, id, proprietà custom, keyframes, font-face o container è certo se un'unità contiene sito e foglio del bersaglio; altrimenti resta, incerto, con `sheet-not-proven-loaded`. `@apply`, `@extend`, `:extend`, `composes` e `safelist` sono a compilazione: fuori dalla regola.
- Ora, CSS-in-JS: letto dal programma TypeScript, riconosciuto dal pacchetto che dichiara il nome. Template di styled-components ed emotion, oggetti di vanilla-extract, `EditorView.theme` di CodeMirror, Stitches, MUI `styled` e `sx`: le loro regole sono nodi. Un selettore con un'interpolazione non letterale è un buco `interpolated-selector` con la forma.
- Ora, altre fonti di classi: `[class.x]`, `[ngClass]` e `[class]` di Angular, con `@Component` che lega template e fogli; le tabelle di `cva` e `tailwind-variants`; un helper del progetto (`cn`) che rende la chiamata di clsx o tailwind-merge sul suo parametro.
- Ora, Vue: una regola `scoped` arriva al markup del suo componente e, con catena `child-root`, all'elemento radice di ogni figlio che il suo template rende (anche attraverso un barrel `export { default as X } from "./X.vue"`); un nome dentro `:deep()` arriva al componente e a tutto ciò che sta sotto di lui, mai agli altri; `:global()` e i blocchi senza `scoped` sono globali; `<style module>` si legge da `$style.x`. Gli alias di `paths` del tsconfig (`@/x`, con catena `paths`) valgono per import di script e di fogli, anche dentro un blocco SCSS.
- `chain` dice la regola che ha portato al bersaglio: `literal-type` (tipo stringa letterale del checker), `initializer` (una const o una proprietà di un oggetto const), `clsx`, `classList`, `@apply`, `composes`, `style-object`, `css-text`, `url-suffix`.

Quale strumento dà cosa (fonti primarie):

| Strumento | Cosa dà | Usato |
| --- | --- | --- |
| parser del prodotto `languages/stylesheet.py` (CSS, SCSS, LESS) | albero delle regole: selettori appiattiti, contesto delle at-rule, layer, keyframes, mixin, import, `@apply` espanso | sì: i nodi, anche dei fogli esterni; l'adattatore guarda ogni istruzione mentre il parser la legge, per `var()`, `animation`, `font-family`, `composes`, `@include`, `$x`, `@layer` |
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

Nessuno dà il nome usato collegato alle sue dichiarazioni fra file e markup. Questo lavoro lo fa `css.graph`: è un confronto di nomi su ciò che i quattro strumenti hanno letto, con gli ambiti di Sass e dei CSS Module.

| Parametro | Valore |
| --- | --- |
| caso | tududi `71da9d7b34dfd1600657e9c5ddf40420206fd263`, i file dello snapshot già sul volume (`scip-inputs/tududi/manifest.sqlite`): 3 CSS, 15 EJS, 2 HTML, 1.038 JS, 650 TS |
| pacchetti | `npm ci --ignore-scripts` come il passo dei motori (`resolve_edges.npm_modules`), 695,0 s |
| motori | parser del prodotto (sha `5986a74f4b18`); TypeScript 5.9.3, picco 1.458 MB; Tailwind 3.4.19; insieme 23,3 s |
| container | 2 CPU, 8 GiB, 723,4 s; hash dei cinque file degli adattatori stampato all'avvio, uguale a quello locale (`css.py` `d1e4c319a3ec`, `css_typescript.js` `6d12fd6caa80`) |
| file | `adapters/css.py` (fogli, HTML/EJS, fogli esterni, montaggio del grafo), `adapters/css_typescript.py` e `.js`, `adapters/css_tailwind.py` e `.js`, `lang_css.py` (app `daodan-graph-css`), `test_css_graph.py`, `fixtures/css/`, `results/graph-css-tududi-checks.json`; il grafo resta sul volume (`graph-css-tududi.json.gz`, `fetch --graph`) |

Esecuzione: `modal deploy benchmarks/inference-audit/lang_css.py`, poi `python benchmarks/inference-audit/lang_css.py spawn --cases tududi` e `fetch --cases tududi`.

Prova locale: `python -B -m pytest -q -p no:cacheprovider tests/test_codebase_map_css_graph.py`, sulle fixture di `tests/fixtures/css-graph/`, con archi, buchi e incerti scritti a mano prima del codice. Le esecuzioni dei motori sono registrate su Modal e rigiocate, quindi non servono né Node né npm (sezione «il grafo dei fogli di stile nel plugin»). La prima fixture contiene:
- un foglio vendorizzato, raggiunto da un percorso URL;
- `animate.css` da npm;
- un link CDN, servito da un sostituto del download;
- `.sass`, `.vue`, `.svelte` e `.less` attesi fra i mancanti.

Fogli trovati e letti:
- Nel checkout: 4 file `.css`, 6 blocchi `<style>` (5 EJS e `public/index.html`) e 42 attributi `style`.
- Nello snapshot: 3 file `.css`. Font Awesome Free 6.4.0 (`backend/modules/landing/public/vendor/fontawesome/css/all.min.css`) è fuori, perché il perimetro esclude `vendor` (`tree_scope.py:59`).
- Font Awesome è letto come foglio esterno, perché `head-assets.ejs:12` lo carica (`/landing-assets/vendor/...`, `url-suffix`).
- Letti: tutti i 1.708 file dati, 0 mancanti. tududi non ha `.sass`, `.vue`, `.svelte` né `.less`.

Nodi, 2.573:
- 1.849 classi esterne: 1.815 utility Tailwind e 34 classi di Font Awesome;
- 608 regole: `styles.ejs` 474, `markdown.css` 56, `tailwind.css` 39, gli altri blocchi `<style>` 39;
- 69 `@font-face` (più 1 di Font Awesome), 20 file del progetto, 13 proprietà custom, 9 `@keyframes`;
- 2 moduli esterni (`tailwindcss` e il foglio di Font Awesome), 2 layer di Tailwind.

Le 13 proprietà custom sono tutte negli script: 6 chiavi di oggetti `style`, 6 proprietà arbitrarie Tailwind, 1 `setProperty`. I fogli di tududi non ne dichiarano.

Archi, 39.544:

| Tipo | Verso il progetto | Verso l'esterno |
| --- | --- | --- |
| classe | 1.646 | 37.156 (Tailwind 37.056, Font Awesome 100) |
| `@font-face` | 670 | 1 (Font Awesome 6 Free, `styles.ejs:1249`) |
| proprietà custom | 51 | 0 |
| `@keyframes` | 9 | 0 |
| import | 3 | 4 (3 `@tailwind`, Font Awesome) |
| layer | 0 | 3 (`@layer base`, `utilities` di Tailwind) |
| id | 1 | 0 |

Per regola: diretto 35.476, `literal-type` 2.736, `initializer` 939 (564 col tipo letterale), `classList` 305, `css-text` 51, `className=` 14, `@apply` 11, `style-object` 10, `url-suffix` 2 (`head-assets.ejs:11` a `fonts.css` e `:12` a Font Awesome).

Pagina: il grafo non sa quale foglio carica ogni pagina. Una classe va a ogni regola che la nomina.
- Fra app React e landing non passa nessun arco di classe verso regole del progetto.
- I 100 archi verso Font Awesome sono 93 dalla landing, che lo carica, e 7 da `sr-only` dell'app React, che non lo carica. Per esempio `Shared/ToggleSwitch.tsx:46` e `Tasks.tsx:627`. Questi 7 sono sbagliati. La classe va anche all'utility Tailwind, che è quella giusta.
- `SearchMenu.tsx:507` `Lora` va ai 10 `@font-face` di `public/index.html`, la pagina dell'app: giusto.

Archi incerti: 27, su 3 letture di `--note-tint` (`NoteFocusMode.tsx:53`, `NoteSidePanel.tsx:131`, `Notes.tsx:101`). Ognuna ha 9 candidati: 3 chiavi di oggetti `style` e 6 proprietà arbitrarie `[--note-tint:...]`, chiare e scure. Le altre quattro proprietà custom hanno una sola dichiarazione.

Esterni: `tailwindcss` 3.4.19 (npm, 37.062 archi) e Font Awesome Free 6.4.0 (file del checkout, versione dal commento iniziale, 102 archi). Nessun foglio importato da `node_modules`, nessun link CDN.

Buchi, 375 (erano 472):

| Classe | Quanti | Esempi |
| --- | --- | --- |
| `no-rule` id | 98 | `cloud.ejs:71 cloud-pricing`, `PublicShareModal.tsx:226 public-share-access`, `AppLauncherModal.tsx:333 app-launcher-title` |
| `parameter` | 69 | `TrialLockNotice.tsx:46 className`, `FileIcon.tsx:29 className`, `ProjectItem.tsx:507 ring` |
| `call` | 67 | `NoteBackgroundPicker.tsx:42 swatch(!value)`, `TaskRowCollapsed.tsx:333 sheetTitleWeightClass(...)`, `SidebarNotesTree.tsx:284 itemClass(false)` |
| `no-rule` classe | 55 | `MermaidDiagram.tsx:149 mermaid-diagram`, `BlankSlate.tsx:47 max-w`, `Views.tsx:216 task-list-container` |
| `property` | 34 | `CalloutBlock.tsx:62 config.borderClass`, `ApiKeysTab.tsx:248 status.className`, `TaskList.tsx:147 task.uid` |
| `css-in-js` | 24 | `Note/editor/inlineMarkdown.ts:43 cm-md-wikilink`, `widgets.tsx:187 cm-md-image`, `blockHandle.ts:83 cm-block-handle-plus` |
| `no-font-face` | 9 | `styles.ejs:6 -apple-system`, `styles.ejs:679 -apple-system`, `styles.ejs:740 SFMono-Regular` (font di sistema) |
| `ejs-glued` | 5 | `landing.ejs:413 plan-step<%= ... %>`, `landing.ejs:752 compare-cell<%= ... %>`, `nav.ejs:34 nav-dd-item<%= ... %>` |
| `element-access` | 5 | `ImportWizard.tsx:368 styles[row.action]`, `QuickCaptureInput.tsx:3196 TOKEN_TEXT_CLASS[...]`, `GoalHero.tsx:133 GOAL_STATUS_TINT[goal.status]` |
| `ejs` | 4 | `landing.ejs:384 <%= pain.icon %>`, `landing.ejs:415 <%= step.icon %>`, `landing.ejs:805 <%= faqAnchor(item) %>` |
| `tailwind-named-group` | 2 | `ReportsOverview.tsx:129 group/tip`, `BoardTaskRow.tsx:98 group/check` |
| `template` | 2 | `CalloutBlock.tsx:62 callout-${type.toLowerCase()}`, `OidcProviderConfig.tsx:352 oidc-auto-provision-${index}` |
| `variable` | 1 | `HabitHeatmap.tsx:127 className` |

Dal primo giro:
- i 94 buchi di Font Awesome sono diventati 93 archi esterni dalla landing (la differenza di uno non è stata indagata), e 1 famiglia (`Font Awesome 6 Free`) è diventata un arco esterno;
- i 2 `url-path` sono diventati import (`url-suffix`);
- 24 `no-rule` sono diventati `css-in-js` e 2 `tailwind-named-group`;
- 5 `ejs` sono diventati `ejs-glued`.

I 24 `css-in-js` sono classi `cm-*` dichiarate come chiavi di `EditorView.theme({...})` in `Note/editor/livePreviewTheme.ts` e `blockHandle.ts`: le regole esistono, il grafo non le legge ancora.

I 55 `no-rule` restanti sono veri:
- classi senza effetto: `bg-black/2`, `text-md`, `max-w`, `transition-width`, `scrollbar-*` (plugin non installato), `prose`, `dark:prose-invert` e `not-prose` (typography non configurato);
- agganci per JS e test: `task-list-container` 11 volte;
- `HabitCheckIn.tsx:154 ${ACCENT.solid}`, un errore di tududi: il segnaposto sta in una stringa normale, non in un template, e la classe accento non arriva mai.

I 98 id senza regola sono etichette, `aria` e ancore che nessun foglio nomina.

Verifica a mano: 20 usi scelti leggendo il sorgente prima che esistesse un grafo di tududi (`HAND` in `lang_css.py`), uguali nei due giri. L'atteso "tutte le regole che nominano la classe" è contato da una scansione indipendente (`_rules_naming`), non dal parser del prodotto.

| Gruppo | Giusti | Siti |
| --- | --- | --- |
| markup verso regole | 10 su 10 | `TabsNav.tsx:17 scrollbar-hide` (2 regole); `AreaDetails.tsx:357` `task-sheet-rails` (5) e `task-sheet` da `${TASK_SHEET_CLASS}` importata (15); `MarkdownRenderer.tsx:245 markdown-content` (36); `SidebarResizeHandle.tsx:60 classList.add(RESIZING_CLASS)`; `AdminGroupsPanel.tsx:621 line-clamp-1` (2 regole del progetto più l'utility); `TaskContentCard.tsx:111 prose` (buco); `nav.ejs:5 nav-wrap` (blocco `<style>` di `styles.ejs`); `App.tsx:337 classList.toggle('dark')` (19 regole più Tailwind); `HabitCheckIn.tsx:147 ${FORM.input} w-20` (19 utility da un oggetto const) |
| proprietà custom | 5 su 5 | `CaptureHost.tsx:151 --capture-dock-left` (dentro un valore arbitrario Tailwind); `NoteFocusMode.tsx:53 --note-tint` (6 siti); `CaptureHost.tsx:27` e `tailwind.config.js:11 --sidebar-width` (`setProperty`); `colorPalette.ts:72 --accent-light` |
| altri | 5 su 5 | `tailwind.css:18 spin` e `:37 border-pulse-dark` (keyframes); `styles.ejs:12` `Manrope` e `Inter` (24 e 35 `@font-face`); `Layout.tsx:12 import './styles/tailwind.css'`; `tailwind.css:121 @apply outline-none` (utility) |

Nessun errore da spiegare. Nessuno dei 7 archi sbagliati verso `.sr-only` di Font Awesome cade fra i 20 siti.

Cosa manca (ora):
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

Cosa manca a `scip_graph.py`, che non è stato toccato:
- `build` e `Traversal` richiedono un indice SCIP: per il CSS non servono. Dal modulo uso `report`, `measured`, `_examples` e la forma del JSON. Gli archi incerti con i candidati entrano nella forma attuale, un arco per candidato: non serve altro.
- `code_sha256` fa l'hash solo di `adapters/*.py`. I due `.js` di questo lavoro e `ts_compiler.js` restano fuori: `lang_css.py` fa l'hash dei suoi cinque file da sé.
- `files.snapshot` e `indexed` contano una lingua; il CSS legge tre tipi di file, quindi conto tutti i file dati.
- L'esterno `{manager, package, version}` ha in più `from` per i fogli esterni; `report` lo ignora.

Costo: due chiamate, una per giro, letti dal conto di Modal: 0,0307 USD e 0,0323 USD, insieme 0,0630 USD. Il 96% del tempo è `npm ci`. Nessun fallimento.

Non verificato:
- Gli archi fuori dai 20 siti: ho controllato i conteggi, le classi dei buchi e gli archi verso Font Awesome, non ogni arco. I 37.056 archi Tailwind valgono quanto il verdetto di `getClassOrder`.
- Che ogni token con tipo letterale sia davvero una classe: il tipo di un parametro dichiara i valori possibili (`literal-type` su 3.312 archi), ma con `strict: false` il tipo può mentire.
- I 42 attributi `style` uno per uno, e quelli con EJS dentro.
- Le tre regole di `tailwind.config.js` (`keyframes`, `animation`): stanno dentro l'esterno Tailwind, non sono nodi.
- Il download da CDN: nella fixture è un sostituto, su tududi non ci sono link CDN.
- La fixture gira su Windows con un junction per `node_modules`; su Modal ha girato solo tududi.

### 14 novembre 2026, grafo completo dall'indice: C

scip-clang indicizza zlib con la build CMake del progetto; il suo indice si legge tutto, ogni documento, occorrenza e simbolo, e diventa il grafo del codice. È l'unico produttore SCIP mantenuto per C e C++: lsif-clang, il suo predecessore, scrive LSIF ed è fermo; clangd non esporta SCIP. Ciò che è proprio del motore sta in `adapters/clang.py`, che serve C e C++; `lang_clang.py` collega adattatore, lettura comune e volume. Esecuzione: `modal deploy benchmarks/inference-audit/lang_clang.py`, poi `python benchmarks/inference-audit/lang_clang.py spawn` e `fetch`; `fetch --files DIR` e `graph --case zlib --dir DIR` rifanno il grafo dai file sul volume (`inference-audit/graph-clang/<caso>/`) senza rieseguire l'indicizzatore. `spawn --fixtures` e `fetch --fixtures` rifanno gli indici delle fixture. Risultati: `results/graph-c-zlib.json` e `results/graph-c-zlib-checks.json`.

| Parametro | Valore |
| --- | --- |
| caso | zlib 1.3.1 `51b7f2abdade71cd9bb0e7a373ef2610ec6f9daf` (CMake): 3.396 chiamate, puntatori a funzione nello stream e nella tabella di configurazione, macro fitte, molti `#ifdef`, `contrib/` ed `examples/` che il build non compila |
| indicizzatore | scip-clang v0.4.1 (LLVM 21, rilasciato il 22 ottobre 2026), binario della release con sha256 verificato, `--jobs=4`; Ubuntu 24.04 con gcc 13 e CMake. Le note dicono Debian 10 o più, ma il binario vuole glibc 2.38: su Debian 12 (2.36) non parte (prima esecuzione) |
| database di compilazione | `cmake -S . -B build -DCMAKE_EXPORT_COMPILE_COMMANDS=ON -DCMAKE_BUILD_TYPE=Debug`, poi `cmake --build`, su una copia nel container: il configure esegue gli script del progetto. 34 comandi su 17 file: ogni file è compilato due volte (libreria condivisa e statica, `example` ed `example64`) |
| pacchetti | una mappa di pacchetti: la radice è `zlib@51b7f2abdade`, ogni cartella delle include di sistema il pacchetto Debian che ne possiede più file (162 voci; due cartelle miste) |
| snapshot del prodotto | nessun file C o C++: `snapshot.py write` elenca 42 file di zlib, nessuno `.c` o `.h` (33 senza linguaggio, 9 C#) |
| riferimenti indipendenti | al posto dello snapshot, tree-sitter: perimetro (file tracciati da Git, cartelle punto escluse), funzioni, classi e prototipi dichiarati, chiamate (`call_expression`, `new_expression`, cast scritti come chiamate esclusi) |
| verifica a mano | 20 chiamate lette nel sorgente prima del grafo (`HAND_CHECK` in `lang_clang.py`) |

Cosa l'adattatore aggiunge a quello che scrive l'indice:
- `SyntaxSnapshot`: lo snapshot del prodotto non legge C né C++, quindi tree-sitter ne fa le veci; le macro di annotazione (`int ZEXPORT inflate(`, `class TINYXML2_LIB XMLNode`) sono sostituite da spazi prima del parsing, posizioni invariate (349 in zlib);
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

Cosa manca al modulo comune, tenuto nell'adattatore:
- uno snapshot per i linguaggi che il prodotto non legge: `Snapshot` vuole i fatti del prodotto, che per C e C++ non elenca neanche i file;
- `Index.tree` usa `languages._treesitter.get_parser`, che non ha `c` né `cpp`;
- un aggancio per l'unità delle posizioni, quando l'indicizzatore non la dichiara ma scrive byte;
- un aggancio per gli intervalli di definizione, quando l'indicizzatore non li scrive: l'adattatore li sostituisce in `index.documents`;
- `Index.load` accoda le occorrenze di un documento ripetuto: l'adattatore le fonde e ricostruisce `at` e `defs`;
- un arco porta solo il simbolo d'arrivo: con più corpi per un simbolo, il grafo non sa quale (qui lo dice `refine`, incerto);
- minore: `build` aggiunge i nodi dei moduli scorrendo un insieme, quindi l'ordine cambia da un processo all'altro; rifatto in locale dai file del volume, il grafo è uguale come insieme.

Costo fatturato da Modal per l'app `daodan-graph-clang`: 0,088 USD in tutto, 0,009 nell'ora 23 UTC e 0,079 nell'ora 00 UTC, non ancora chiusa. Comprende l'esecuzione fallita su Debian 12, quattro indicizzazioni delle fixture e cinque esecuzioni per caso; ogni esecuzione di un caso costa meno di un centesimo.

Non verificato:
- altri generatori del database (Bear, Meson): i due casi usano CMake;
- le opzioni di sviluppo di scip-clang (`--help-all`), fra cui una per indici stabili;
- i 37 tipi che tree-sitter non dichiara: dagli esempi sono `typedef` (`zutil.h:39` `uch`), non tutti controllati;
- i 2 corpi che tree-sitter non riconosce (`deflate.c:635` `deflateResetKeep`, `trees.c:995` `_tr_flush_block`): le loro chiamate finiscono su un valore;
- i picchi di RAM fra un campione e l'altro (due al secondo).

### 14 novembre 2026, grafo completo dall'indice: C++

Stesso indicizzatore, adattatore e driver della sezione C; caso tinyxml2. Risultati: `results/graph-cpp-tinyxml2.json` e `results/graph-cpp-tinyxml2-checks.json`. Fixture: `fixtures/c` e `fixtures/cpp`, con l'indice scritto da scip-clang, provate in `test_clang_graph.py` (45 prove).

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

### 14 novembre 2026, lettore C e C++ dello snapshot

Lo snapshot del prodotto legge C e C++ (`languages/cfamily.py`, prove in `tests/test_codebase_map_clang_reader.py`). Le due sezioni sopra restano misurate con `SyntaxSnapshot`, che resta per i risultati salvati. `Index.tree` ha ora `c` e `cpp`.

| Parametro | Valore |
| --- | --- |
| fixture | `test_clang_graph.py` gira anche sullo snapshot del prodotto: fini uguali in C 17 su 17, in C++ 14 su 15 |
| la differenza | `new geo::Square(3.0)`: lo snapshot legge la chiamata su `Square` (8:33), dove l'indice nomina la classe; il sostituto la legge dove inizia il tipo (8:28), dove nomina il costruttore |
| zlib `51b7f2abdade` | 74 file letti, 66 C e 8 C++ (`contrib/iostream*`); fatti semantici per 15 file C e gli 8 C++; 664 chiamate, 63 risolte nel file; 3,7 s |
| tinyxml2 `9148bdf719e9` | 4 file C++, fatti semantici per 2 (`tinyxml2.h` e `xmltest.cpp` hanno errori di sintassi); 706 chiamate, nessuna risolta nel file; 12,2 s |
| file con errori | 51 file C di zlib: macro come `local int f(`, `uch FAR uchf`, `z_const`. Togliendo sei nomi di zlib (`local`, `FAR`, `z_const`, `ZEXTERN`, `ZEXPORTVA`, `OF`) i file interi diventano 39 su 66 |

### 14 novembre 2026, macro e include nello snapshot

Lo snapshot passa al lettore le macro dei file con cui un file condivide un'unità di traduzione: ciò che include e chi lo include. Il lettore toglie le macro che il sorgente definisce come decorazione (`#define local static`, `FAR`) o come involucro di un prototipo (`OF((args))`). Un nome che arriva da un header incluso porta alla sua unica definizione con collegamento esterno. Misurato in locale, prima e dopo sullo stesso sorgente.

| Parametro | Valore |
| --- | --- |
| zlib `51b7f2abdade` | file C senza fatti semantici: 37 su 66 prima, 12 dopo; chiamate nei file con fatti 1.523 prima, 2.278 dopo; risolte 303 prima, 510 dopo (470 nel file, 40 per include); 9,7 s contro 4,7 |
| chiamate senza definizione | 198, verso funzioni di `zlib.h` definite in uno dei 12 file senza fatti (`inflateEnd`, `inflate`, `gz_error`, `deflate`) |
| tinyxml2 `9148bdf719e9` | invariato: fatti per 3 file su 4 (`xmltest.cpp:336` diviso da un `#if`); nessuna chiamata risolta per include, perché le funzioni libere stanno nel namespace `tinyxml2` o nei corpi dei membri |
| cosa resta | 9 file per un `#if` che divide un'istruzione (`gzlib.c:187`, `inflate.c:196`, `infback.c:45`, `puff.c:494`, `miniunz.c:630`, `unzip.c:1897`, `deflate.c:184`, una funzione di `trees.c` e una di `zip.c`); 3 per parole di un compilatore in un ramo spento (`ioapi.h:87`, `zutil.h:98`, `testzlib.c:20`). Per entrambi serve il ramo che il build sceglie, cioè l'indice |

## 14 novembre 2026, fonti del programma intero: JavaScript e TypeScript

Accanto al grafo letto dall'indice SCIP ci sono due seconde fonti, ciascuna in un suo adapter con la stessa forma
(`analyze(project_dir, work_dir) -> {"edges", "engine"}`). Le ho provate su `fixtures/ts` e poi su tududi (commit
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

### Motori

| fonte | secondi | RAM di picco | note |
|---|---:|---:|---|
| compilatore TS | 35 | 1,8 GB | 111.366 chiamate: 93.241 per firma, 1.089 per simbolo, 17.036 senza dichiarazione |
| compilatore TS + 22 `@types/*` mancanti | 35 | 1,8 GB | per firma 96.070 |
| Jelly solo progetto | 35 | 2,4 GB | 1.688 moduli, 23.495 funzioni, nessun timeout |
| Jelly con `node_modules` | 1.286 | 21,4 GB | fermato dal suo timeout di 1.200 s: 702 pacchetti, 10.425 moduli, 161 errori; grafo parziale |

Costo fatturato da Modal per l'app: 0,085 USD (ora 23 UTC) + 0,056 USD (ora 00 UTC) = 0,14 USD.

### Per classe di buco (chiamate dove l'indice non ha un obiettivo del progetto)

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

### Dove l'indice ha già un obiettivo del progetto

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

### Precisione di Jelly: 20 archi letti su ricevitori senza tipo

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

### Controllo a mano (20 casi, attese scritte prima dei risultati)

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

### Verdetto

- Compilatore TS: chiude il metodo abbreviato (57 di 60), `t` (3.748), `fireEvent` (564) e `useCallback` senza
  salto dichiarato. Non chiude i ricevitori `any`: 0 obiettivi del progetto; 767 esterni se si installano i
  `@types` mancanti. Nessun disaccordo: i suoi archi si fondono come certi, con la regola `@types/x -> x` per gli
  esterni.
- Jelly solo progetto: è l'unica fonte per callback e valori funzione (le 7 + 3 frecce dei webhooks, le 11
  correzioni ai membri d'interfaccia). Sui ricevitori senza tipo dà poco: 44 chiamati veri su 9.166. Non ha
  inventato archi nei 20 letti, ma non è completo per costruzione: va fuso come candidato marcato, separando le
  callback negli argomenti dal chiamato.
- Jelly con `node_modules`: no, perché costa 21 GB, va in timeout e dà meno archi.

Non verificato:
- il richiamo di Jelly;
- gli 882 casi TS fermi su un parametro;
- se le versioni `@types` installate (le ultime) corrispondono a quelle dei pacchetti;
- 198 siti TS e 72 di Jelly che non trovano la chiamata nello snapshot (0,2%);
- test automatici per i due adapter.


## 14 novembre 2026, fogli di stile su progetti reali: tutti i dialetti e la regola di pagina

Verdetto: giro di conferma con il codice finale, un solo hash per tutti i casi (`css.py` `49854bf56415`; Bulma rigirato dopo la correzione dei keyframe in percentuale, `css_sass.js` `040e6256e5ac`). Verifica a mano: v3-admin-vite 15 su 15, tududi 20 su 20, Bootstrap 3 15 su 15, hn.svelte.dev 16 su 16, saas-starter 15 su 15, Bulma 7 su 11. styled-components-website non è misurato: secondo fallimento per la stessa causa, caso fermato. Nessun file perso senza motivo. La regola di pagina rende incerti, senza toglierli, gli archi verso fogli che il codice non prova caricati: su tududi i 7 archi `sr-only` verso Font Awesome.

| Parametro | Valore |
| --- | --- |
| casi | v3-admin-vite `c2c895d71d57` (Vue 3.5, SCSS scoped), tududi `71da9d7b34df`, Bootstrap 3.4.1 `68b0d231a132` (Less), hn.svelte.dev `0010bbea0678` (Svelte 3), saas-starter `6e33e58b1e55` (Tailwind 4.1.7), Bulma 1.0.4 `e133d45b7a82` (SCSS con `@use`, `@forward`, mixin), styled-components-website `e70dc5c3f513` |
| motori | `adapters/css_engines.json`: sass-parser 0.5.6, less 4.9.1, stylus 0.64.0, @vue/compiler-sfc 3.5.45, svelte 5.57.3, @astrojs/compiler 4.0.0, TypeScript 5.9.3 quando il progetto non ha il suo; Tailwind e i pacchetti del progetto da `npm ci --ignore-scripts`, o da pnpm col suo lockfile quando npm non installa |
| container | 2 CPU, 8 GiB; i progetti si clonano e installano solo su Modal, tornano solo i file `-checks.json`; hash dei file `css*` stampato all'avvio e uguale a quello locale |
| verifica a mano | 15 usi per caso (16 per hn.svelte.dev, i 20 di prima per tududi), attese scritte dal sorgente prima del grafo (`HAND` in `lang_css.py`); `all` è una scansione propria che appiattisce il nesting |
| costo | letto dal conto di Modal: 0,0217 USD nell'ora 11 UTC e 0,2649 + 0,0235 USD nell'ora 12 UTC (la seconda voce è l'app ridistribuita dopo un arresto), insieme 0,3101 USD; dentro ci sono circa 0,09 USD sprecati da un container del primo giro di Bulma rimasto acceso e da un lancio doppio, fermati entrambi. Altri 0,0677 USD nell'ora 00 UTC sono di giri precedenti sulla stessa app, non di questo lavoro |

Esecuzione: `modal deploy benchmarks/inference-audit/lang_css.py`, poi `python benchmarks/inference-audit/lang_css.py spawn --cases v3-admin-vite,tududi,bootstrap3,hn-svelte,saas-starter,bulma` e `fetch`.

### v3-admin-vite (Vue 3)

- File: 131 trovati, 131 letti interi, 0 mancanti. Pacchetti installati in 29,9 s, giro intero 37,2 s.
- Nodi: rule 284, custom-property 167, custom-property external 80, module 68, variable 7, class external 6, module external 5, script-binding 4, keyframes 2, mixin 1.
- Archi: class external 12, class project 392, custom-property external 222, custom-property project 235, id project 6, import external 5, import project 26, keyframes project 2, mixin project 6, placeholder project 25, sass-variable project 12, script project 2, v-bind project 7.
- Incerti: 425 archi su 144 riferimenti.

| Buco | Quanti | Esempi |
| --- | --- | --- |
| `no-font-face font-face` | 8 | `src/common/assets/styles/index.scss:41 Inter`, `src/common/assets/styles/index.scss:41 Helvetica`, `src/common/assets/styles/index.scss:41 Microsoft YaHei` |
| `undeclared custom-property` | 5 | `src/common/assets/styles/view-transition.scss:15 --v3-theme-x`, `src/common/assets/styles/view-transition.scss:15 --v3-theme-y`, `src/common/assets/styles/view-transition.scss:18 --v3-theme-x` |
| `no-rule class` | 3 | `src/common/components/Notify/index.vue:55 notify`, `src/common/components/Notify/index.vue:67 demo-tabs`, `src/common/composables/useTheme.ts:52 normal` |
| `variable class` | 2 | `src/layouts/modes/LeftMode.vue:36 layoutClasses`, `src/layouts/modes/LeftTopMode.vue:21 layoutClasses` |
| `interpolated-selector rule` | 1 | `src/common/assets/styles/theme/core/index.scss:1 .#{$theme-name}` |
| `spread class` | 1 | `src/common/composables/useTheme.ts:58 ...otherThemeNameList` |
| `url-scheme import` | 1 | `src/main.ts:15 virtual:uno.css` |

Verifica a mano: 15 su 15.

Note:
- Scelto dalle pagine del repository, senza clone locale: 47 `.vue`, fogli globali importati da `src/main.ts` (normalize, Element Plus, vxe-table, `@@/assets/styles/index.scss`), alias `@` e `@@`, componenti di layout attraverso un barrel `src/layouts/components/index.ts`.
- `.vue` trovati 47, letti 47. Blocchi `<style>`: 36 scoped SCSS, 1 globale SCSS; nessun `module`, nessun CSS semplice.
- Archi delle classi dai template: 314 verso il componente proprio, 10 verso il padre con `child-root` (`.app-main` dei tre layout sulla radice di `AppMain`), 55 verso fogli globali importati da `main.ts`, 11 verso un altro componente (il blocco globale o un `:deep()` di un antenato), 10 verso fogli di pacchetti. Tutti certi.
- Regola di pagina: nessun arco `sheet-not-proven-loaded`. `index.html` carica `/src/main.ts`; da lì il grafo dei moduli arriva a ogni componente per import, router (`() => import("@/pages/...")`) e barrel. I 425 incerti sono della cascata: 421 proprietà custom con più dichiarazioni (temi chiaro, scuro, dark-blue), 4 variabili Sass dichiarate in più file.
- npm non installa senza un lockfile npm: è entrato il ripiego su pnpm (dal `pnpm-lock.yaml`, senza script).
- Snapshot del prodotto: per ogni `.vue` i simboli dello script e una regola per selettore dei blocchi `<style>`, con il selettore appiattito; non sa se un blocco è `scoped` o `module` e non legge le classi del template. Il resto (tipo dei blocchi, classi del template, `v-bind()`, padre e figli, alias, fogli da `main`, regola di pagina) lo vede solo il grafo.

### tududi, prima e dopo

- File: 1.708 trovati, 1.708 letti interi, 0 mancanti. Pacchetti installati in 536,4 s, giro intero 565,6 s.
- Nodi: class external 1.849, rule 707, font-face 69, module 20, custom-property 13, keyframes 9, module external 2, layer external 2, font-face external 1.
- Archi: class external 37.158, class project 1.703, custom-property project 51, font-face external 1, font-face project 670, id project 1, import external 4, import project 3, include project 26, keyframes project 9, layer external 3.
- Incerti: 924 archi su 667 riferimenti.

| Buco | Quanti | Esempi |
| --- | --- | --- |
| `no-rule id` | 98 | `backend/modules/landing/views/cloud.ejs:71 cloud-pricing`, `frontend/components/Note/PublicShareModal.tsx:226 public-share-access`, `frontend/components/Sidebar/AppLauncherModal.tsx:333 app-launcher-title` |
| `parameter class` | 68 | `frontend/components/Billing/TrialLockNotice.tsx:46 className`, `frontend/components/Shared/Icons/FileIcon.tsx:29 className`, `frontend/components/Project/ProjectItem.tsx:507 ring` |
| `call class` | 67 | `frontend/components/Note/NoteBackgroundPicker.tsx:42 swatch(!value)`, `frontend/components/Task/TaskRow/TaskRowCollapsed.tsx:333 sheetTitleWeightClass( toPriorit`, `frontend/components/Sidebar/SidebarNotesTree.tsx:284 itemClass(false)` |
| `no-rule class` | 55 | `frontend/components/Shared/MermaidDiagram.tsx:149 mermaid-diagram`, `frontend/components/Shared/BlankSlate.tsx:47 max-w`, `frontend/components/Views.tsx:216 task-list-container` |
| `property class` | 28 | `frontend/components/Shared/CalloutBlock.tsx:62 config.borderClass`, `frontend/components/Profile/tabs/ApiKeysTab.tsx:248 status.className`, `frontend/components/Kanban/KanbanBoard.tsx:371 cfg.bg` |
| `no-font-face font-face` | 9 | `backend/modules/landing/views/partials/styles.ejs:6 -apple-system`, `backend/modules/landing/views/partials/styles.ejs:679 -apple-system`, `backend/modules/landing/views/partials/styles.ejs:740 SFMono-Regular` |
| `property id` | 6 | `frontend/components/Task/TaskList.tsx:147 task.uid`, `frontend/components/Areas.tsx:437 area.uid`, `frontend/components/Goals.tsx:347 goal.uid` |
| `ejs-glued class` | 5 | `backend/modules/landing/views/landing.ejs:413 plan-step<%= i % 2 ? ' plan-step-flip' : '' `, `backend/modules/landing/views/landing.ejs:752 compare-cell<%= i === 0 ? ' compare-us' : ''`, `backend/modules/landing/views/partials/nav.ejs:34 nav-dd-item<%= l.code === i18n.locale ? ` |
| `element-access class` | 5 | `frontend/components/Spreadsheet/ImportWizard.tsx:368 styles[row.action]`, `frontend/components/Inbox/QuickCaptureInput.tsx:3196 TOKEN_TEXT_CLASS[ segment .kind ]`, `frontend/components/Goal/GoalHero.tsx:133 GOAL_STATUS_TINT[goal.status]` |
| `ejs class` | 3 | `backend/modules/landing/views/landing.ejs:384 <%= pain.icon %>`, `backend/modules/landing/views/landing.ejs:415 <%= step.icon %>`, `backend/modules/landing/views/landing.ejs:462 <%= card.icon %>` |
| `ejs id` | 1 | `backend/modules/landing/views/landing.ejs:805 <%= faqAnchor(item) %>` |
| `template class` | 1 | `frontend/components/Shared/CalloutBlock.tsx:62 callout-${type.toLowerCase()}` |
| `parameter id` | 1 | `frontend/components/Shared/SelectMenu.tsx:87 id` |
| `template id` | 1 | `frontend/components/Profile/tabs/OidcProviderConfig.tsx:352 oidc-auto-provision-${index}` |
| `variable class` | 1 | `frontend/components/Habits/HabitHeatmap.tsx:127 className` |
| `unresolved-import script` | 1 | `backend/modules/landing/views/partials/head-assets.ejs:10 https://dyneteq.com/admin/s.js` |

Verifica a mano: 20 su 20.

Note:
- Buchi da 375 a 350: i 24 `css-in-js` sono diventati 69 archi verso le regole di `EditorView.theme` (`Note/editor/livePreviewTheme.ts`, `blockHandle.ts`), i 2 `tailwind-named-group` archi a `tailwindcss group` (catena `named-group`).
- I 7 archi da `sr-only` dell'app React a Font Awesome restano e sono incerti (`sheet-not-proven-loaded`): l'app non carica il foglio della landing.
- 26 archi `include` fra template EJS: le pagine della landing sono un'unità con i loro partial.
- 897 archi incerti per la regola di pagina: 639 verso Tailwind da sette file che il bundle dell'app non raggiunge (366 da `ProjectInsightsPanel.tsx`, 203 da `ProjectBanner.tsx`, poi due test), 144 verso `markdown.css`, 59 `@font-face` di `fonts.css` da pagine della landing; queste due ultime cause non sono indagate. Uguale al giro precedente: nessuna correzione successiva tocca tududi.

### Bootstrap 3.4.1 (Less)

- File: 282 trovati, 280 letti interi, 2 mancanti: `docs/_pug/customizer-nav.pug` (template language: no reader); `docs/_pug/customizer-variables.pug` (template language: no reader). Pacchetti installati in 239,4 s, giro intero 249,9 s.
- Nodi: rule 2.775, class external 654, variable 399, module 264, mixin 115, module external 5, keyframes 2, font-face external 2, font-face 1, id external 1.
- Archi: class external 14.612, class project 130.517, font-face external 2, font-face project 1, id external 1, id project 31, import external 34, import project 137, less-variable project 1.521, mixin project 281, script project 95.
- Incerti: 143.210 archi su 7.234 riferimenti.

| Buco | Quanti | Esempi |
| --- | --- | --- |
| `no-rule id` | 1.353 | `docs/_includes/ads.html:1 _carbonads_js`, `docs/_includes/customizer-variables.html:103 input-@font-family-base`, `docs/_includes/customizer-variables.html:1630 help-block-@thumbnail-padding` |
| `no-rule class` | 118 | `docs/_includes/components/navbar.html:36 collapsed`, `docs/_includes/js/scrollspy.html:10 collapsed`, `docs/examples/tooltip-viewport/index.html:38 tooltip-right` |
| `unresolved-import script` | 56 | `docs/_includes/ads.html:1 https://cdn.carbonads.com/carbon.js?zoneid=1673&serve=C6AILKT&pl`, `docs/examples/cover/index.html:80 ../../dist/js/bootstrap.min.js`, `docs/examples/sticky-footer-navbar/index.html:91 ../../dist/js/bootstrap.min.js` |
| `no-font-face font-face` | 22 | `docs/assets/css/docs.css:1241 Menlo`, `docs/assets/css/docs.min.css:10 Courier New`, `docs/assets/less/customizer.less:31 Menlo` |
| `interpolated-selector rule` | 15 | `less/mixins/grid-framework.less:17 @{list}`, `less/mixins/grid-framework.less:62 .col-@{class}-pull-@{index}`, `less/mixins/list-group.less:12 a.list-group-item-@{state} .list-group-item-heading, button` |
| `unresolved-import import` | 7 | `docs/_includes/getting-started/download.html:34 {{ site.cdn.css }}`, `docs/_includes/getting-started/template.html:18 {{ site.cdn.css }}`, `docs/_includes/header.html:19 {{ site.baseurl }}/dist/css/bootstrap.css` |
| `url-scheme import` | 2 | `docs/_includes/header.html:25 data:text/css;charset=utf-8,`, `docs/_includes/header.html:27 data:text/css;charset=utf-8,` |
| `template-tag class` | 1 | `docs/_includes/components/glyphicons.html:10 {{ iconClassName }}` |
| `template-tag-glued class` | 1 | `docs/_layouts/default.html:23 col-md-{% if page.fullwidth == true %}12{% else %}9{% endif ` |
| `variable id` | 1 | `docs/assets/js/docs.min.js:1 c` |
| `element-access class` | 1 | `docs/assets/js/docs.min.js:1 this.options["class"]` |

Verifica a mano: 15 su 15.

Note:
- La lista a mano è stata corretta dopo il primo giro, rileggendo il sorgente: nominava un foglio che nessuna pagina carica (`dist/css/bootstrap.css`, citato solo in una stringa di un test JS), una riga sbagliata (`.starter-template` è alla 59) e un buco sbagliato per `.collapsed` (nessuna regola lo nomina, lo legge solo il JavaScript del plugin collapse).
- Corretto nel codice dopo il primo giro: un selettore interpolato senza prefisso né suffisso (`@{list}`) dichiarava di poter generare ogni nome; un mixin definito dentro un altro mixin ora si cerca dallo scope più interno (i 6 `undeclared mixin .col` sono spariti); i tag Liquid (`{{ }}`, `{% %}`) sono buchi `template-tag`.
- 143.165 archi incerti per la regola di pagina: le pagine caricano i fogli compilati di `dist`, mai i sorgenti Less. Che `dist/css/bootstrap.css` nasca da `less/bootstrap.less` lo dice il Gruntfile, non il codice dei fogli.

### hn.svelte.dev (Svelte 3, stili scoped)

- File: 20 trovati, 20 letti interi, 0 mancanti. Pacchetti installati in 61,7 s, giro intero 64,1 s.
- Nodi: rule 60, module 14, custom-property 6, keyframes 1.
- Archi: class project 48, custom-property project 24, keyframes project 1.
- Incerti: 27 archi su 13 riferimenti.

| Buco | Quanti | Esempi |
| --- | --- | --- |
| `no-font-face font-face` | 12 | `static/global.css:15 Roboto`, `static/global.css:15 Oxygen`, `static/global.css:15 Droid Sans` |
| `no-rule class` | 3 | `src/components/ThemeToggler.svelte:39 light`, `src/routes/[list]/[page].svelte:55 more`, `src/routes/user/[name].svelte:37 about` |
| `unresolved-import import` | 1 | `src/template.html:24 global.css` |
| `no-rule id` | 1 | `src/template.html:45 sapper` |

Verifica a mano: 16 su 16.

Note:
- Le regole di un componente arrivano solo al suo markup; `:global(html).dark .x` dà `dark` a tutti. Un composto aperto da `:global(...)` è globale per intero, come in Svelte: il primo giro lo leggeva a metà.
- `src/template.html` linka `global.css`, che Sapper serve da `static/`: la convenzione non è nel codice, quindi buco `unresolved-import` e archi verso `static/global.css` incerti.

### saas-starter (Tailwind 4.1.7)

- File: 43 trovati, 43 letti interi, 0 mancanti. Pacchetti installati in 36,2 s, giro intero 41,7 s.
- Nodi: class external 364, custom-property 177, rule 10, layer external 3, module external 2, custom-property external 2, variant 1, module 1.
- Archi: class external 1.063, custom-property external 8, custom-property project 222, import external 2, import project 1, layer external 5, variant project 9.
- Incerti: 1.279 archi su 1.113 riferimenti.

| Buco | Quanti | Esempi |
| --- | --- | --- |
| `parameter class` | 23 | `components/ui/card.tsx:9 className`, `components/ui/input.tsx:10 className`, `components/ui/dropdown-menu.tsx:76 className` |
| `no-rule id` | 11 | `app/(dashboard)/dashboard/general/page.tsx:40 name`, `app/(dashboard)/dashboard/page.tsx:227 member`, `app/(dashboard)/dashboard/security/page.tsx:82 confirm-password` |
| `no-font-face font-face` | 3 | `app/globals.css:80 Manrope`, `app/globals.css:80 Arial`, `app/globals.css:80 Helvetica` |
| `property class` | 1 | `app/layout.tsx:26 manrope.className` |
| `no-rule class` | 1 | `app/(dashboard)/dashboard/security/page.tsx:38 bold` |

Verifica a mano: 15 su 15.

Note:
- Tailwind 4 letto dal suo design system (`@theme`, `@custom-variant dark`, `@import "tw-animate-css"` come foglio esterno).
- L'helper `cn` del progetto (tailwind-merge su clsx) ora è riconosciuto: le utility scritte nelle sue chiamate diventano archi (verso l'esterno da 818 a 1.063); resta buco `parameter` il `className` passato dal chiamante.
- 1.050 archi `sheet-not-proven-loaded`: con l'App Router di Next.js il layout `app/layout.tsx`, che importa `globals.css`, avvolge le pagine per convenzione, senza import. Da leggere come regola di framework (task 11 del piano).

### Bulma 1.0.4 (SCSS)

- File: 602 trovati, 602 letti interi, 0 mancanti. Pacchetti installati in 7,0 s, giro intero 117,8 s.
- Nodi: custom-property 56.445, rule 51.160, variable 991, module 507, keyframes 86, mixin 62, function 17, container 15, property 12, module external 12.
- Archi: class project 5.052.873, container project 807, custom-property project 3.791.991, function external 188, function project 1.520, id project 35, import external 36, import project 359, keyframes project 962, mixin project 374, module-member project 62, placeholder project 103, sass-variable project 2.905, script project 1.
- Incerti: 8.846.500 archi su 98.895 riferimenti.

| Buco | Quanti | Esempi |
| --- | --- | --- |
| `undeclared custom-property` | 4.001 | `css/bulma.css:3336 --bulma-link-focus-border`, `css/versions/bulma-no-dark-mode.css:12863 --bulma-dark-15-l`, `css/versions/bulma-prefixed.min.css:3 --bulma-black-70-l` |
| `interpolated-selector rule` | 1.157 | `docs/_sass/docs/notification.scss:55 .bd-notification.is-#{$name}`, `sass/elements/button.scss:628 .#{iv.$class-prefix}buttons.#{iv.$class-prefix}has-addons .#`, `sass/grid/columns.scss:195 .#{iv.$class-prefix}column.#{iv.$class-prefix}is-three-fifths-m` |
| `no-rule class` | 1.072 | `docs/_includes/about/author.html:5 bd-footer-iframe`, `docs/_includes/library/layout/level.html:62 link`, `docs/documentation/elements/icon.html:521 fa-home` |
| `no-rule id` | 268 | `docs/_includes/book/book-banner.html:1 bulma-book`, `docs/cyp/components/pagination.html:64 pagination-medium`, `docs/cyp/form/tools.html:57 field-is-grouped-centered` |
| `undeclared function` | 246 | `docs/_sass/docs/backers.scss:27 cv.getVar`, `docs/_sass/docs/menu.scss:150 cv.getVar`, `docs/_sass/global/nav.scss:83 cv.getVar` |
| `no-font-face font-face` | 233 | `css/bulma.css:21044 Inter`, `css/versions/bulma-no-dark-mode.css:18249 Ubuntu`, `css/versions/bulma-prefixed.min.css:3 Arial` |
| `template-tag-glued class` | 219 | `docs/_includes/docs/components/call.html:1 bd-theme-{{ include.color }}`, `docs/_includes/docs/subnav/subnav-form.html:35 {% if page.doc-subtab == 'radio' %}is-activ`, `docs/cyp/elements/button.html:56 is-{{ color }}` |
| `interpolated-selector class` | 165 | `docs/_includes/book/book-banner.html:5 bd-book-columns`, `docs/_includes/global/navbar.html:1 bd-navbar`, `docs/documentation/components/navbar.html:733 is-paddingless` |
| `unresolved-import import` | 127 | `docs/_includes/docs/snippets/custom-page.html:7 my-bulma-project.css`, `docs/_sass/docs/tw.scss:1 sass/utilities/mixins`, `test/ruby-sass/sass/customize.scss:32 ../../../sass/elements/container.sass` |
| `undeclared mixin` | 81 | `docs/_sass/docs/backers.scss:139 mx.mobile`, `docs/_sass/docs/examples.scss:106 mx.ltr`, `docs/_sass/global/nav.scss:243 mx.from` |
| `template-tag-glued id` | 39 | `docs/_includes/docs/examples/navbar-bottom.html:14 navbarExample{{ include.id }}`, `docs/cyp/elements/button.html:38 button-{{ color }}-active`, `docs/cyp/elements/title.html:21 subtitle-{{ i }}` |
| `unresolved-import module-member` | 34 | `docs/_react/bulma-customizer/src/pages/Colors.jsx:9 .colors`, `docs/_react/bulma-customizer/src/pages/components/Modal.jsx:10 .items`, `docs/_react/bulma-customizer/src/pages/elements/Table.jsx:10 .items` |
| `parameter id` | 33 | `docs/_react/bulma-customizer/src/pages/Scheme.jsx:12 schemeId`, `docs/_react/bulma-customizer/src/pages/components/Navbar.jsx:12 id`, `docs/_react/bulma-customizer/src/pages/elements/Tag.jsx:12 id` |
| `undeclared sass-variable` | 23 | `docs/_sass/docs/notification.scss:54 dv.$colors`, `docs/_sass/examples/custom.scss:9 $control-border-width`, `docs/website.scss:357 iv.$gap` |
| `template-tag class` | 22 | `docs/_includes/docs/components/heading.html:5 {{ include.icon }}`, `docs/_includes/docs/elements/snippet.html:18 {{ include.wrapper }}`, `docs/_includes/global/nav-item.html:5 {% if link.icon_only %}` |
| `unresolved-import script` | 15 | `docs/_includes/docs/content/klmn.html:111 {{ site.url }}/assets/javascript/klmn.js`, `docs/_layouts/default.html:24 {{ site.url }}/assets/vendor/clipboard-2.0.11.min.js`, `docs/index.html:16 {{ site.url }}/assets/javascript/home.js` |
| `interpolated-selector id` | 12 | `docs/_includes/library/components/modal.html:26 modal-box`, `docs/cyp/elements/container.html:18 container-widescreen`, `docs/cyp/grid/columns.html:107 columns-mobile` |
| `call class` | 11 | `docs/_react/bulma-customizer/src/components/Slider.jsx:150 classNames({ [cn.main]: true, [`, `docs/_react/bulma-customizer/src/components/VarItem.jsx:78 classNames({ "button is-small":`, `docs/_react/bulma-customizer/src/App.jsx:575 classNames({ [cn.button]: true, "is-hidden": ` |
| `not-read import` | 6 | `docs/_includes/docs/snippets/getting-started.html:7 https://cdn.jsdelivr.net/npm/bulma@{{ `, `docs/documentation/start/installation.html:23 https://cdn.jsdelivr.net/npm/bulma@{{ site.d`, `docs/_sass/examples/custom.scss:41 https://fonts.googleapis.com/css?family=Nunito:400,700` |
| `template id` | 3 | `docs/_react/bulma-customizer/src/components/Color.jsx:201 ${color}-h`, `docs/_react/bulma-customizer/src/components/Color.jsx:218 ${color}-s`, `docs/_react/bulma-customizer/src/components/Color.jsx:235 ${color}-l` |
| `template class` | 3 | `docs/_react/bulma-customizer/src/components/Color.jsx:251 is-${color}`, `docs/assets/javascript/klmn.js:27 is-${n}`, `docs/assets/javascript/shop.js:398 shop-product-${getId(product.id)}` |
| `template-tag id` | 2 | `docs/_includes/docs/elements/anchor-bis.html:1 {{ include.name | slugify }}`, `docs/_includes/docs/elements/anchor.html:1 {{ include.name | slugify }}` |
| `dynamic-member module-member` | 2 | `docs/_react/bulma-customizer/src/components/Slider.jsx:133 cn[kind]`, `docs/_react/bulma-customizer/src/components/Picker.jsx:46 cn[kind]` |
| `parameter class` | 2 | `docs/assets/javascript/shop.js:846 className`, `docs/assets/javascript/shop.js:854 icon` |
| `property id` | 1 | `docs/_react/bulma-customizer/src/components/VarItem.jsx:47 cssvar.id` |
| `unknown-member module-member` | 1 | `docs/_react/bulma-customizer/src/components/Color.jsx:175 side` |

Verifica a mano: 7 su 11.
- `docs/_layouts/docs.html:15` `.button`: mancano {'.button': ['docs/_react/bulma-customizer/src/App.module.css:53']}, in più {}.
- `docs/_layouts/docs.html:16` `.fas`: mancano {'.fas': ['hole:no-rule']}, in più {'.fas': ['docs/_sass/docs/docs.scss:124', 'docs/_sass/docs/docs.scss:162', 'docs/assets/css/website.css:33713', 'docs/assets/css/website.css:33745', 'docs/assets/css/website.min.css:2']}.
- `docs/_layouts/docs.html:35` `.algolia-content`: mancano {}, in più {'.algolia-content': ['hole:interpolated-selector']}.
- `docs/_layouts/docs.html:15` `#js-menu-toggle`: mancano {}, in più {'#js-menu-toggle': ['hole:no-rule']}.

Note:
- 602 file trovati, tutti letti. Nel primo giro di conferma 4 fogli restavano fuori (`sass/base/animations.scss`, `docs/website.scss` e altri due): sass-parser 0.5.6 rifiuta un selettore di keyframe in percentuale (`0% { ... }`, «expected selector»), che Dart Sass legge. Dentro `@keyframes` quel selettore ora si scrive `to`, sulla stessa riga, prima del parser: il grafo non tiene i selettori dei keyframe, solo le dichiarazioni. Prova nella fixture `css-sass`.
- 8.852.216 archi, quasi tutti incerti per la regola di pagina: le pagine della documentazione linkano i fogli con URL Liquid (`{{ site.url }}/...`), che non si risolvono, quindi nessuna pagina prova di caricare un foglio; e il checkout contiene 14 copie compilate di Bulma (`css/`, `css/versions/`, `docs/assets/css/website.css`), ciascuna con tutte le regole.
- 1.157 buchi `interpolated-selector`: `.#{iv.$class-prefix}button` e simili. Il prefisso è una variabile di modulo con `!default`, che chi usa Bulma può cambiare: non è un valore letterale e locale, quindi buco per scelta.
- 246 `undeclared function` (`cv.getVar`) e 81 `undeclared mixin` (`mx.mobile`): i fogli di `docs/_sass` caricano `sass/utilities/...` per un load path di Jekyll (`_config.yml`), che non è nel codice dei fogli; l'import resta `unresolved-import` e lo spazio dei nomi è sconosciuto.
- Verifica a mano 7 su 11, quattro differenze, nessuna un errore del grafo: `.button` (la scansione conta anche `App.module.css:53`, che è una classe locale di un CSS Module); `.fas` (attesa sbagliata: `docs/_sass/docs/docs.scss:124` e `:162` nominano `.fas`); `.algolia-content` e `#js-menu-toggle` (nessuna regola li nomina, l'attesa «tutte le regole» doveva essere un buco: il grafo dà `no-rule` per l'id e `interpolated-selector` per la classe, perché un selettore costruito a compilazione che finisce con `content` potrebbe nominarla). Le attese sono lasciate come erano state scritte.

### styled-components-website: non misurato

- Primo giro: `npm install` fallisce con `EOVERRIDE` (gli `overrides` di npm contro una dipendenza diretta; il progetto usa pnpm). Secondo giro, con il ripiego su pnpm: `npx` girava nella copia dei manifest e rileggeva lo stesso `package.json`, con lo stesso `EOVERRIDE`. Seconda volta per la stessa causa: caso fermato.
- Corretto dopo, non provato: `npx pnpm --dir <copia>` da una cartella sua.
- Senza pacchetti il programma TypeScript non vede styled-components e i template non sono riconosciuti; il giro (8,2 s) non vale come misura. Il file `graph-css-sc-website-checks.json` non è salvato.

Cosa manca a questa misura:
- styled-components-website, e un caso Svelte 5 e uno Stylus reali: provati solo sulle fixture;
- le convenzioni dei framework per il caricamento (layout di Next.js, `static/` di Sapper);
- UnoCSS (v3-admin-vite lo usa poco: i suoi token restano `no-rule`).

### 14 novembre 2026, il grafo dei fogli di stile nel plugin

Il grafo dei fogli di stile ora sta nel plugin, in `daodan/core/indexers/`: `css.py`, un adattatore per motore con il suo `.js`, e i motori fissati in `css_engines/` (`package.json`, `package-lock.json` con l'integrity sha512 di tutti i 126 pacchetti). `lang_css.py` resta il driver per Modal e importa dal plugin. Nel prodotto lo stage non è ancora attivo: arriva con il giro guidato dalla pre-mappa.

Cosa cambia rispetto al benchmark:
- Nessun adattatore installa o lancia un motore. Ognuno riceve un runner, `runner(script, payload)`, che lancia lo script nella radice del progetto e aggiunge `engines`, la cartella del `package.json` dei motori. Su Modal è `node_runner` di `lang_css.py`; nel prodotto lo darà il container.
- Payload e uscite nominano i file con il percorso relativo alla radice del progetto, con `/`. Il runner decide quindi dove girano i motori (nel container la radice è `/work`). Un test lo controlla su ogni esecuzione registrata.
- Un'esecuzione senza dati porta `state` e `reason`. Con `unavailable` (un limite di memoria, un motore assente) il grafo si ferma con quella causa; con `failed` i file di quell'esecuzione restano fra i mancanti, con il motivo.
- Ciò che il codice carica insieme è un dato in ingresso. `units` sono le unità che la pre-mappa afferma, e valgono accanto a pagine e bundle presi dagli import del grafo.
- Anche i fogli CDN sono un dato in ingresso, `remote`: il lettore non scarica nulla. Senza il testo del foglio, un nome che nessun altro dichiara diventa un buco `remote-sheet` con l'URL, su ogni pagina che lo carica. `lang_css.py` passa `remote` vuoto, quindi i fogli CDN di Bootstrap 3 e di Bulma lasciano buchi `remote-sheet` (conteggi nel task 11 del piano).
- `rows` dà le righe dello store. Tutte sono sotto l'etichetta `stylesheet` e hanno `reference_id` nullo; la fine è `external`, `namespace` (un file) o `project-value`. La copertura conta ogni sito del grafo, e un sito senza righe è una violazione.
- TypeScript è sempre il 5.9.3 fissato con i motori, mai quello del progetto.

| Parametro | Valore |
| --- | --- |
| registrazione | `lang_css.py fixtures` su Modal, una funzione per le undici fixture: i pacchetti di ogni fixture con `npm install --ignore-scripts`, i motori installati con `npm ci` dal lockfile; per ogni fixture le esecuzioni dei motori e i file di `node_modules` che il grafo stesso guarda; `fetch --fixtures` li scrive in `tests/fixtures/css-graph/recorded/` (245 KB) |
| codice | hash dei file `indexers/css*` e `css_engines/*.json` stampato su Modal, uguale a quello locale |
| costo | 0,0270 USD dal conto di Modal (ora 19 UTC: sette registrazioni e i deploy, letto alle 19:58) |
| test | `tests/test_codebase_map_css_graph.py`: 34 test in circa 2 s. Sono i 26 del benchmark e 8 nuovi: un foglio CDN senza testo, un'unità affermata dalla pre-mappa, le righe dello store, la copertura, una violazione, nessun percorso assoluto nelle esecuzioni registrate, un motore `unavailable`, un'esecuzione `failed` |

styled-components-website ha ora 15 attese scritte dal sorgente al commit fissato, prima di ogni giro (`HAND` in `lang_css.py`). Rispetto alle 14 di prima:
- `.error-page` ha 5 regole, non 3;
- `--sc-color-textSecondary` è dichiarata due volte in `GlobalStyles.tsx` (388 e 398), quindi non è un buco;
- si aggiunge `homepage.css:34 --sc-color-textMuted` verso `GlobalStyles.tsx` 389 e 399.

Le attese su `error.tsx` stanno nello `<style>` dentro JSX, che il grafo non legge: lì il grafo deve risultare sbagliato finché non lo legge.

Differenza dichiarata per il prossimo giro: v3-admin-vite non ha un lockfile npm. Senza pnpm, che arriva con la pre-mappa, i fogli di Element Plus e vxe-table diventano buchi e i suoi conteggi cambiano.

### 14 novembre 2026, Java e Kotlin nel container del plugin

Il prodotto indicizza Java e Kotlin con `index()` di `indexers/java.py` e `indexers/kotlin.py`. La build gira solo nel container, in due tempi: la preparazione con la rete aperta ai soli registri, poi l'esecuzione senza rete. Su Modal un container non si avvia, quindi gli stessi script girano nel container della funzione (`adapters/jvm_here.py`). Ricevono la stessa copia del perimetro e gli stessi strumenti portati da Daodan, e stanno dietro lo stesso proxy dei registri, che lì fa solo da controllo. `lang_java.py`, `lang_kotlin.py` e `fixture_indexes.py` usano l'immagine e le funzioni del plugin, più `git` per il checkout.

| Parametro | Valore |
| --- | --- |
| casi | javapoet e klaxon, ai commit sopra; la fixture Java sul PC del proprietario |
| immagine | `eclipse-temurin:17-jdk-noble@sha256:1bedb04434bd275ef072355e9caec2a22be5240fbe82ad51a59323f2bbcab4a6` (`indexers.jvm.IMAGE`) |
| scip-java | 0.14.2: i 26 jar che coursier 2.1.24 risolve, ciascuno con il suo sha256 (`indexers.jvm.CLASSPATH`) |
| strumento di build | quello del wrapper, scaricato da Daodan e verificato; senza wrapper Gradle 9.9.1 o Maven 3.10.0 |
| registri | quelli di `container.REGISTRIES` più `indexers.jvm.REGISTRIES_ADDED`; nessun host di GitHub, nessun `services.gradle.org` |
| soglia | conteggi uguali a `results/graph-java-javapoet-checks.json` (scip-java 0.13.2) e a `results/graph-kotlin-klaxon.json` |

Risultati su Modal, con il codice del plugin verificato per hash. Costo di tutte le prove del giorno: 0,10 USD.
- javapoet: resoconto del grafo identico (3.541 nodi, 19.189 archi, archi per fine, buchi, pacchetti, `same_range` 9, `static` 3, ordine degli overload 808 su 808); verifica a mano 20 su 20.
  - La prima build fallisce come con la 0.13.2. La seconda, con il javac semplice (ora un programma Java: l'immagine non ha Python), dà l'indice.
  - Indicizzatore 28,2 s, picco 733 MB; 1.596 MB per tutti i processi.
  - Il proxy rifiuta `maven.java.net`, `oss.sonatype.org` e `repository.apache.org`, che la build chiede ma non usa.
- L'accordo con il lessicale passa da 264 uguali e 25 «il lessicale la classe, l'indice il costruttore» a 283 uguali e 6 diversi. Lo causa la regola del costruttore nel grafo (commit `88c21ea89`), non l'indicizzatore: nei 6 il lessicale indica un costruttore scritto, come `AnnotationSpec.java:249`, mentre la fine ora indica la classe.
- klaxon: ogni conteggio identico (15.940 archi certi, 251 incerti, buchi, 30 relazioni inverse tolte, verifica a mano 16 su 20). Gradle 7.3 è quello del wrapper, portato da Daodan, e il proxy non rifiuta nulla.
  - Indicizzatore 84,9 s, picco 1.636 MB.
  - Con l'immagine di rilascio di scip-java erano 130,2 s e 4.050 MB; nella misura salvata 107,2 s e 2.205 MB.
- Con l'immagine di rilascio il wrapper di Gradle scaricava da `services.gradle.org`, che lo rimanda a `github.com`. Ora la distribuzione la porta Daodan, e nessun host di GitHub è aperto.
- Rifatto su Modal dopo il passaggio ai volumi (scip-java, strumenti, `HOME` e indice in `/daodan/state`), con il codice verificato per hash, per 0,03 USD.
  - javapoet: stesso resoconto e verifica a mano 20 su 20. Indicizzatore 20,0 s, picco 763 MB.
  - klaxon: ogni conteggio identico. Indicizzatore 108,6 s, picco 1.813 MB.

Peso su disco, misurato su Modal leggendo gli strati dal registro:
- immagine di rilascio di scip-java: 1.700 MB compressi, 2.748 MB su disco. Di questi, 1.538 MB sono la cache di coursier (i JDK 17, 21 e 25 e le dipendenze), 251 MB il JDK 25 della base, 145 MB Gradle e 110 MB gcc.
- immagine del plugin: Temurin 17, 190 MB compressi e 403 MB su disco. Gli strumenti restano nella cartella condivisa sull'host: scip-java 81 MB, Maven 10 MB, Gradle 129 MB.

Sul PC del proprietario (Kiri 0.2.0, CLI docker 29.9.2, un container da 2 GB, `RealContainerSmokeTest`):
- fixture Java senza wrapper: Maven 3.10.0 portato da Daodan e dipendenze da Maven Central attraverso il proxy. L'indice è scritto e le 7 attese di `expected.json` tengono. 31,7 s, indicizzatore 10,2 s, picco 346 MB.
- la stessa fixture con `mvnw` in CRLF, senza bit di esecuzione, e `.mvn/` tracciato da Git: la copia porta `.mvn/` e il container chiama il Maven portato, senza scaricare distribuzioni. 15,6 s.
- impostazioni dell'utente uguali prima e dopo (PATH, configurazione e contesti di Docker, PATH dell'utente, distribuzioni WSL).
- in Kiri restano Temurin (438 MB) e il proxy `python:3.13-alpine` (53 MB). Il disco di Kiri resta di 1,66 GB.
- fixture Kotlin, con un container da 4 GB: senza wrapper si usa il Gradle 9.9.1 portato da Daodan, verificato con il suo sha256. Il plugin Kotlin 2.1.0 compila, e le 7 attese di `expected.json` tengono. 84 s; indicizzatore 63,4 s, picco 1.788 MB.
- wrapper di Gradle che indica `downloads.example.com`: risulta `unavailable`, senza container e senza richieste a quel sito.
- con il `commit` di allora ogni run lasciava in `/var/lib/kiri/layers` lo strato dell'immagine preparata: Kiri 0.2.0 non lo cancella con `rmi -f` e la CLI non lo elenca. Pesava 118 MB per Java (scip-java 83, `.m2` 24, Maven 12) e 426 MB per Kotlin (`.gradle` 195, Gradle 148, scip-java 83), e il disco di Kiri è passato da 1,66 a 2,26 GB. Ora la preparazione passa all'esecuzione due volumi con nome, tolti per nome alla fine; i tre strati sono stati tolti per nome con il via del proprietario.
- fixture Java con i volumi: indice e attese come prima, 22 s, indicizzatore 13,5 s e 584 MB. `system df`, strati, volumi e container di Kiri e il suo disco uguali prima e dopo, registro vuoto. Il commit di Windows sale di 0,62 GB al picco (da 39,01 a 39,63 GB su 43,46).

Cosa manca a questa misura:
- klaxon in un container vero;
- la fixture Kotlin con i volumi, con `system df` uguale prima e dopo.

### 17 novembre 2026, Java e Kotlin sulla base comune

Java e Kotlin passano all'immagine che tutti i linguaggi condividono (decisione A del proprietario, 15 novembre). Il JDK 17 entra nella run come gli strumenti di build: Daodan lo scarica sull'host e lo verifica con lo sha256. La preparazione lo scompatta nel volume di stato e lo collega in `/opt/java/openjdk`, prima di ogni passo che usa Java; l'esecuzione lo riusa. Il locale è `C.UTF-8`, l'unico che la base porta, dentro la glibc.

| Parametro | Valore |
| --- | --- |
| casi | javapoet e klaxon, ai commit sopra; `jvm-ver-gradle-tc21` della pipeline di `benchmarks/project-model` |
| immagine | `debian:trixie-slim@sha256:a72b4433de1cf7d6bae0c4cee74d0547f58601a643b3375f070c51600d63b6b2` (`indexers.jvm.IMAGE`), glibc 2.41, senza certificati di sistema |
| JDK | Temurin 17.0.21+9, `OpenJDK17U-jdk_x64_linux_hotspot_17.0.21_9.tar.gz`, sha256 `8b9b611d…8711` (`indexers.jvm.TEMURIN`) |
| soglia | conteggi uguali a `results/graph-java-javapoet-checks.json` e a `results/graph-kotlin-klaxon.json` |

Risultati su Modal, con il codice verificato per hash. Costo di tutto il giro, test compresi: 0,068 USD.
- Test di `tests/test_codebase_map_indexers_jvm.py`, `test_codebase_map_dynamic_jvm.py` e `test_codebase_map_container.py`, in un container Linux: 169 passati e 19 saltati, cioè le prove con un container vero, quelle solo per Windows e quelle che chiedono un JDK sul PATH. I nuovi test erano rossi prima del codice.
- javapoet: resoconto identico (3.541 nodi, 19.189 archi), verifica a mano invariata. Indicizzatore 28,6 s, picco 652 MB; 1.290 MB per tutti i processi.
- klaxon: i conteggi dell'indice sono identici: 15.940 archi certi, 238 e 13 incerti, gli stessi 7 file mancanti. Il risultato salvato è del 13 novembre, 288 commit fa, e tre valori della lettura di Daodan sono cambiati:
  - un buco è lo stesso sito (`dynamic-callee`), che `334ea4d96` sposta da `no-position` a `computed-callee`;
  - un file mancante ha la ragione scritta con le parole di oggi;
  - quattro archi passano da «project-value unknown» a «project-value read». Questa misura non separa la causa fra codice e immagine.
  - Indicizzatore 100,9 s, picco 1.278 MB.
- `jvm-ver-gradle-tc21`: indice `fresh`. Il JDK 21 della toolchain lo installa mise sulla base senza certificati di sistema; l'indice nomina `jdk@21`. Il passo dinamico osserva 10 siti e 10 archi, con 2 test passati; la toolchain attesa è trovata. 248 s.

Cosa manca a questa misura:
- le fixture Java e Kotlin in un container vero sul PC, con `system df` prima e dopo;
- la pre-mappa (`premap/maven.py`, `gradle.py`, `sbt.py`), C, C++, C#, TypeScript, Python e il proxy, che usano ancora le loro immagini.

## 14 novembre 2026, due regole nuove dell'adapter Python

Due regole nuove nell'adapter Python (`indexers/python.py`, `hops`), provate prima sulla fixture
(`tests/fixtures/code-graph/python/fx/held.py`, `fx/over.py`, nove casi in `expected.json`, indice rigenerato su
Modal con `fixture_indexes.py`):

- `initializer`: un nome assegnato a un solo nome, semplice o puntato (`f = area`, `f = shapes.area`,
  `self.f = area`), porta a ciò a cui rimanda l'ultimo nome. Il risultato di una chiamata no.
- `rebinding`: scip-python definisce una funzione solo al suo primo `def`, cioè allo stub `@overload`. Gli altri
  `def` sono riferimenti allo stesso simbolo. La chiamata finisce sull'ultimo `def` senza `overload`. Un
  Protocol fatto di soli stub li tiene. In `code_graph.Traversal.ends` un salto `rebinding` prende il posto della
  definizione, e l'arco lo dice nella sua catena. Senza questo cambio lo stub, che è già una funzione, ferma
  ogni salto. La parte comune non sa nulla di `overload`: decide l'adapter quando emettere il salto.
  `tests/test_codebase_map_code_graph.py`: 95 test verdi, uno nuovo per `rebinding` nella parte comune.

## 14 novembre 2026, gli stage degli indicizzatori nel passaggio

Il passaggio del prodotto legge ogni linguaggio dal suo indicizzatore (`ENGINES` di `resolve_edges.py`); questa misura copre Go, TypeScript e JavaScript, Rust. `modal_stage.py` fa girare lo stage vero (`index_stage`) sul caso e, dallo stesso indice, scrive lo store come lo scrive il benchmark; poi li confronta.

| Parametro | Valore |
| --- | --- |
| casi | chi, semver e tududi ai commit sopra, con snapshot e passo per posizione tenuti in `scip-inputs/<caso>` |
| voci | `scip-go`, `scip-rust`, `scip-typescript`; resolver `nome della voce@versione` |
| macchina | Modal, 4 CPU e 12 GB, solo il sistema di base: ogni stage scarica il suo indicizzatore |
| soglia | conteggi del grafo e celle del confronto con il passo per posizione uguali a `results/scip-<caso>-confirm.json`; store dello stage uguale riga per riga a quello del benchmark; ogni «solo passo per posizione» con una riga nello store; verifica a mano pari |
| risultati | `results/scip-{chi,semver,tududi}-stage.json` |

Risultati, con il codice del plugin verificato per hash. Costo: 0,10 USD.
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

## 14 novembre 2026, Python dall'indice nello stage, senza cambio di fonte

`modal_stage.py --entries scip-python` fa girare solo lo stage vero di scip-python (`_serving`). Nel prodotto Python viene da scip-python, nelle cartelle che gli dà la pre-mappa. Qui il driver dà a scip-python i progetti Python (`UNITS`), come la pre-mappa: l'adattatore non ne cerca.

| Parametro | Valore |
| --- | --- |
| casi | python-semver `b6e83e3e40d3a7570386e8d694ae8011477a55c1`, sulla copia con i link come file normali e sullo snapshot che `lang_python.py` tiene in `graph-python/semver-plugin` (`snapshot.py write` si ferma su un file linkato) |
| unità | python-semver la radice; un'esecuzione di scip-python per unità, con prefisso, nome, ambiente e configurazione di Pyright suoi |
| macchina | Modal, 4 CPU e 12 GB, solo il sistema di base |
| soglia | conteggi uguali a `results/graph-python-semver-plugin-checks.json`; celle del confronto con il passo uguali; store dello stage uguale riga per riga a quello del benchmark; ogni «solo passo per posizione» con una riga nello store; verifica a mano pari |
| risultati | `results/scip-python-semver-stage.json` |

Risultati, codice del plugin verificato per hash (`indexers/python.py` `3d8472aeb568`, `code_graph.py` `40bd846bcab4`):
- python-semver: 1.289 nodi e 3.679 archi, 64 buchi, 35 file su 35, come il salvato. Il controllo a mano dei 20 siti è identico. Lo store dello stage è identico a quello del benchmark, riga per riga. Il report differisce solo nei salti `initializer` (28): il risultato salvato viene da un `indexers/python.py` precedente alle due regole del 14 novembre (`f201bd46a865`), e 11 archi passano da un valore a una funzione del progetto.
- Indicizzatore: python-semver 9,4 s e 347 MB. `MIN_FREE` di scip-python è 1.920 MB, dal picco di un caso privato. Lo stage intero: 41 s.

Cosa cambia negli id: la versione del progetto è `_` in ogni esecuzione, e il nome è quello dell'unità (`semver`). Gli id del risultato salvato di python-semver contengono il commit (`semver b6e83e3e40d3`), quelli nuovi `semver _`: un confronto fra i due va fatto dopo aver sostituito la versione, come fa `against_confirm`.

Una prova con una sola esecuzione dalla radice e un `executionEnvironments` di Pyright per ogni progetto non regge. Su un caso privato il modulo di un progetto Python ha un nome dove è definito e un altro dove è importato: resta senza definizione, e circa 2.200 archi `unknown` passano da un valore a un vicolo cieco. Le chiamate cambiano in 222 siti. Per questo ogni unità ha la sua esecuzione, come i moduli di Go.

Costo fatturato da Modal: 0,192 USD. Nell'ora 19 UTC 0,162 (`daodan-stage-audit` 0,142, test MCP 0,015, confronto degli indici 0,006), con quattro giri di python-semver e di un caso privato e la prova scartata; nell'ora 20 0,030 per il giro finale, con le unità date dal driver.

## 27 novembre 2026, evidenza per indicizzatore (T2.A)

Dai `results/` esistenti, nessuna corsa nuova: `python -B benchmarks/inference-audit/evidence_summary.py`, risultato in `results/evidence-summary.tsv`. TypeScript c'era già (scip-typescript su tududi, JavaScript e TypeScript): nessuna corsa del passo `T2.A.4`.

- **Confermati e falsi archi** vengono solo dai `scip-*-full.json` (seconda fonte A contro indice B): confermato = «same project target», falso arco = solo «different project target» (entrambi i lati hanno una destinazione del progetto e differiscono). Le celle `mixed` non sono falsi archi.
- **Incerti e buchi** dei motori senza seconda fonte vengono dai `report` dei `graph-*-checks.json` e di `graph-kotlin-klaxon.json`; lì confermati e falsi archi restano vuoti.
- `hand_check` (quattro forme diverse) e `other_languages` (i rapporti in più di zlib) non sono letti.

| Indicizzatore | Confermati | Falsi archi | Incerti | Buchi | Secondi | MB |
| --- | --- | --- | --- | --- | --- | --- |
| scip-go (chi) | 1.014 | 0 | n/d | 0 | 12,8 | 338 |
| rust-analyzer (semver) | 252 | 0 | n/d | 186 | 8,9 | 1.176 |
| scip-typescript (tududi, JS) | 12.709 | 0 | n/d | 58 | 67,4 | 2.154 |
| scip-typescript (tududi, TS) | 7.023 | 0 | n/d | 0 | 67,4 | 2.154 |
| scip-clang (zlib C; tinyxml2 C++) | n/d | n/d | 4; 0 | 2.383; 145 | 4,8; 2,9 | 69; 83 |
| scip-java (javapoet) | n/d | n/d | 0 | 10 | 37,7 | 639 |
| scip-java (klaxon, Kotlin) | n/d | n/d | 251 | 330 | 107,2 | 2.205 |
| scip-python (semver) | n/d | n/d | 0 | 64 | 7,5 | 369 |

I sei grafi dei fogli di stile (pipeline `stylesheet.py`, non un indicizzatore) sono nel TSV, non qui. Tempo e memoria di scip-typescript sono una sola esecuzione per i due linguaggi.

### Verdetto

Falsi archi: zero in tutti i quattro indicizzatori con seconda fonte (go, rust-analyzer, scip-typescript JS e TS). Limiti: la seconda fonte (il passo dei motori) non è una verità, e i casi in cui A dà una destinazione del progetto e B finisce su un valore (`mixed: A project-other, B parameter`, `call-result`: chi 29, tududi JavaScript 1.082, tududi TypeScript 3.952) non sono contati come falsi archi per definizione; sono la classe da guardare se si vuole una misura più severa. Le 153 chiamate «diverse» di chi del primo join erano interfaccia contro implementazione e sono scomparse con la lettura completa.

Modello di evidenza: nessun campo nuovo. Ciò che l'indice non decide si dice con `uncertain.reason` nel `refine` dell'adattatore, come già fa `adapters/clang.py` («one symbol defined at several places»); i buchi restano `holes`. Un campo nuovo si apre solo se una misura futura mostra un falso arco che `reason` non esprime.
