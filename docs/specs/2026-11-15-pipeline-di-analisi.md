# Pipeline di analisi: step, analyzer con adattatori, listener

**Stato:** approvata dal proprietario il 15 novembre 2026, che ha lasciato a Claude le scelte rimaste (sezione «Scelte»). Lo step 3 è applicato (`pipeline.Dynamic`, `dynamic/`), con gli osservatori di Python, JavaScript e TypeScript, Go, Java e Kotlin, Rust, C e C++, C#. Le regole della mappa dei moduli e dello stack (sezione 1, «Scansione: la mappa dei moduli» e «Stack») e della reattività (sezione 6) le ha decise il proprietario il 17 novembre 2026 e sono applicate; i motivi sono in «Scelte», 4–6. Il 20 novembre 2026, con la divisione per aspetto della [spec dei flussi](2026-11-18-flussi-e-mappa-del-sistema.md), stanno qui l'analisi unificata: una preparazione per analisi («Preparazione»), uno strumento ufficiale per linguaggio (sezione 2), la scelta 7 con i suoi limiti e ciò che resta da decidere. Il 22 e il 23 novembre 2026 il proprietario approva la sezione 8: i nomi, l'ordine degli step da ciò che ognuno deve sapere prima di partire, il piano. Nel codice ci sono la solidità (8.9), i passi 1, 2 e 4 di 8.11, parte dei passi 3 e 5 e il formato comune degli adattatori di ingressi (8.13), del 23 novembre 2026; lo stack riconosce solo attraverso stack-analyser ([spec dello stack dal fork](2026-11-21-stack-dal-fork.md), «Stato»); il resto non è applicato, e il processo con i nomi nuovi è spiegato in [Codebase Map, sezione Pipeline](../plugins/codebase-map.md#pipeline). **Piano:** [analisi unificata](../plans/2026-11-20-analisi-unificata.md).

Il proprietario chiede (15 novembre 2026) un codice modulare, pulito e manutenibile: un'architettura a step, il pattern adapter, e la possibilità di registrare listener dell'intero processo di analisi. Primo step: una scansione veloce di moduli e tecnologie; poi, per ogni linguaggio o framework trovato, un'istanza dell'analyzer che sotto usa lo strumento specifico. Il processo dà feedback, informazioni, log, eventi e avanzamento fino alla generazione del grafo completo.

## Parole

- **Step:** una fase dell'analisi, con ingressi e uscite dichiarati. Uno step legge solo ciò che gli step prima hanno scritto.
- **Analyzer:** l'istanza che analizza una tecnologia del progetto. Ha un'interfaccia comune.
- **Adattatore:** il codice sotto un analyzer che usa uno strumento esistente (scip-go, scip-java, scip-clang, i parser dei fogli di stile) e ne normalizza l'uscita. Nessuna logica di uno strumento fuori dal suo adattatore.
- **Evento:** un fatto del processo, dal primo file letto al grafo completo: uno step inizia, un analyzer finisce, una lacuna, un messaggio, l'avanzamento. **Listener:** chi lo riceve.
- **Grafo completo:** l'uscita della pipeline: i grafi di ogni tecnologia, con gli archi osservati nell'esecuzione, uniti ai punti di connessione.

## Comportamento attuale

*Letto sul codice il 23 novembre 2026 (commit `7f0bd7cbe`); il punto degli step, le righe e `ENGINES` riletti il 24 novembre (commit `03161c8a6`). Il processo di oggi, passo per passo e con chi chiama che cosa, è in [Codebase Map, «Oggi nel codice»](../plugins/codebase-map.md#oggi-nel-codice): qui non si ripete.*

- Due famiglie di adattatori hanno un contratto: le fonti della pre-mappa (`premap/`, una per strumento, unite in un punto solo) e gli indicizzatori (`indexers/`, `structure`, `index` e correzioni opzionali; un test impedisce di saltarne una o di cercare file da soli). La parte comune del grafo è `code_graph.py`; il container è `container.py`.
- Gli step sono in `pipeline.STEPS`, sei: `scan` (struttura del grafo dei moduli e pre-mappa), `stack`, `parse`, `analyze`, `dynamic`, `union`. L'ingresso della pipeline è l'inventario (`pipeline.INPUTS`). Chi scrive lo snapshot, chi esegue quali step e quando: [Codebase Map, «Oggi nel codice»](../plugins/codebase-map.md#oggi-nel-codice).
- `ENGINES` si costruisce dalle dichiarazioni degli indicizzatori (`engine_pass.py:866`); il passaggio parte per i linguaggi che la lettura dello snapshot ha trovato (`pass_plan`) e prende le unità dalla pre-mappa.
- I motori per posizione di prima non ci sono più: Vue e Svelte passano da scip-typescript (`indexers/components.py`), Jedi è tolto. Resta `position_stage.py` per un indice SCIP dato a mano (`resolve_edges.py --engine scip`).
- Righe: `resolve_edges.py` 187, `engine_pass.py` 871, `snapshot.py` 2.267, `modules.py` 493. Le funzioni oltre le 80 righe: `engine_pass.index_stage` (98), `snapshot.write_reading` (83), `snapshot._refresh_locked` (83).
- I fogli di stile sono un indicizzatore (`indexers/css.py` e i suoi `css_*`).
- Eventi: il bus di `pipeline/events.py`, scritto nel giornale della run; il passaggio emette `analyzer.*`, `progress` e `gap`. Non emessi: `step.skipped` (la freschezza la controlla ogni `ensure`, non `_run`) e l'uscita degli strumenti come `log` (va in un file, `engine_pass._log_tail`).

**Le sezioni 1–7 sul codice.**

| Sezione | Stato | Dove, o che cosa manca |
| --- | --- | --- |
| 1, gli step in un punto solo | Applicato | `pipeline.STEPS`; la freschezza per impronta in un punto solo è assorbita da 8.8, punto 2 |
| 1, mappa dei moduli e stack | Applicato | Le prove della sezione |
| 1, lo step 4 come unione | Assorbito | `union` dice ciò che manca e non unisce: è `connect` (8.2) |
| 2, adattatori che si dichiarano, uno per tecnologia | Applicato | `indexers.analyzers()`, `ENGINES` derivato; la scelta dai linguaggi letti è assorbita dal piano (8.4) |
| 2, fogli di stile e motori per posizione | Applicato | `indexers/css.py`; Vue e Svelte in scip-typescript; Jedi tolto |
| 3, bus, giornale, listener che fallisce | Applicato | `pipeline/events.py`, 8.9 |
| 3, `step.skipped` e l'uscita degli strumenti come `log` | Aperto | `step.skipped` è 8.8, punto 2; il `log` di livello `debug` non è in nessun passo di 8.11 |
| 3, i nomi `analyzer.*` | Assorbito | `adapter.*` (8.7) |
| Preparazione | Applicato | Con i limiti scritti lì |
| 4, `pipeline/`, `resolve_edges.py` diviso | Applicato | Restano tre funzioni oltre le 80 righe (sopra) |
| 4, la cartella `analyzers/` | Assorbito | I nomi di 8.7 (`resolvers/`, `parsers/`, …) |
| 4, `snapshot.py` e `modules.py` spezzati | In parte | `modules.py` sì; `snapshot.py` è assorbito da 8.6 |
| 5, passi 1–4 | Applicato | Il passo 2 è assorbito dal piano (8.4) |
| 5, passo 5 | In parte | Come la riga di `snapshot.py` |
| 6 | Applicato | Le prove della sezione |
| 7 | Aperto | Legata alla misura 2b, fuori da 8.11 |

## Proposta

### 1. Gli step, dichiarati in un punto solo

| Step | Cosa fa | Uscita |
| --- | --- | --- |
| 1. Scansione | Inventario dei file, grafo dei moduli, pre-mappa: moduli, tecnologie, versioni, dipendenze | Snapshot, `modules.json`, `premap.json` |
| Stack (16 novembre 2026, fra 1 e 2) | Le tecnologie di ogni unità di build: framework, librerie, strumenti e servizi, riconosciute da stack-analyser; ricalcolato quando cambiano inventario, moduli, registro, fatti o stato delle fonti della pre-mappa, o il rilascio fissato | `technologies.json` |
| 2. Analisi | Un analyzer per ogni tecnologia della pre-mappa, ognuno con le sue unità | Una voce per tecnologia nello store dei collegamenti |
| 3. Dinamico | I test nel container; ciò che si osserva entra nel grafo della sua tecnologia | Archi osservati, i campionati a parte |
| 4. Unione | I grafi delle tecnologie in uno solo, ai punti di connessione (rotte, chiamate HTTP, eventi, tabelle) | Il grafo completo |

La pipeline finisce con il grafo completo; i flussi lo leggono dopo, fuori da essa. Un modulo `pipeline` elenca gli step in ordine; ogni step ha lo stesso contratto: `inputs` (ciò che legge), `run(context)`, `outputs` (ciò che scrive). Uno step è fresco quando i suoi ingressi non sono cambiati: lo stesso controllo per impronta che pre-mappa e store usano già, scritto una volta. Lo step 3 segue il disegno del [passo dinamico](2026-11-12-passo-dinamico.md) ed è applicato (`pipeline.Dynamic`, `dynamic/`); lo step 4 entra con il disegno dei punti di connessione (`benchmarks/connection-points/`).

**Scansione: la mappa dei moduli.** Applicato (Scelte, 4). Prova: `tests/test_codebase_map_modules.py` (`test_contract_directory_and_source_do_not_declare_module`), `tests/test_codebase_map_premap_packages.py`, `tests/test_codebase_map_stack_rationalized.py`.

1. `modules.json` è la mappa sola dei moduli. Ogni modulo dichiara `nature`: `concrete`, un'unità di build con un artefatto o sorgenti compilati (i manifest letti e le unità che i comandi di modello della pre-mappa scoprono); `logical`, un modulo dichiarato (`codebase-modules.json`) o proposto (`proposals.json`), interno o esterno; `virtual`, un workspace, una solution o un reactor senza artefatto proprio (`provenance: "build"`), e il modulo implicito `source-tree` (`provenance: "virtual"`) dei file sorgente o di esecuzione che nessuna unità di build copre e che non sono già letti come manifest.
2. Ogni modulo dice `languages`, i file per linguaggio al netto di `excluded`, e `toolchains`, `{tool, version, declared_in}`: quelle dichiarate nei suoi file o ereditate dal workspace che lo contiene, più gli strumenti che i suoi ecosistemi e linguaggi chiedono.
3. La pre-mappa ha la faccetta `packages`, `{ecosystem, name, declared_in, version}`: la versione è il testo che il manifest scrive in quel punto, assente dove non ne scrive, mai risolta né letta da un lockfile, senza dipendenze transitive; `dependencies` resta rifiutata dal contratto. La popolano i lettori che ci sono (`module_graph`, `requirements`, `jvm_files`, `project_files`) e i comandi di modello (`renovate`, `maven`, `gradle`, `dotnet`), con gli stessi `argv`.
4. `modules.sync_with_premap` allinea `modules.json` alla pre-mappa (unità di modello, `excluded`, `languages`, `toolchains`) in una scrittura sola.
5. `modules.json`, `premap.json` e `technologies.json` restano negli stessi percorsi, per CLI, MCP, viewer e benchmark.

**Stack.** Applicato (Scelte, 5); dal fork di stack-analyser ([spec](2026-11-21-stack-dal-fork.md); il processo: [Codebase Map, «Lo step `stack`»](../plugins/codebase-map.md#lo-step-stack)). Prova: `tests/test_codebase_map_stack_rationalized.py`, `tests/test_codebase_map_stack_recognition.py`, `tests/test_codebase_map_stack_sources.py`; README di [`benchmarks/project-model`](../../benchmarks/project-model/README.md), «Lo step `stack` sul corpus» e «Lo step `stack` dal fork».

1. `stack_recognition.run` manda a stack-analyser i fatti della scansione (`packages`, `services`, `docker_builds`) come dichiarazioni, senza rileggere i manifest, lascia fuori `excluded` dal perimetro e dalle prove, e `service_registry.entry_category` dà a ogni voce la sua categoria (framework, libreria, strumento, servizio: [flussi e mappa del sistema](2026-11-18-flussi-e-mappa-del-sistema.md), 5.1).
2. `technologies.json` dà per ogni modulo, anche `logical` e `virtual`, `{id, name, kind, nature, provenance, paths, languages, toolchains, frameworks, libraries, services, tools, technologies}`, più la vista `units` delle unità fisiche e virtuali. `libraries` elenca tutte le librerie che il modulo dichiara: arricchite dall'id e dal nome della tecnologia riconosciuta sullo stesso pacchetto e file, mai tolte se nessuna lo è.
3. Il registro è l'anagrafica, senza segni: la categoria tiene framework ed esecutori dei test separati dai servizi esterni (`registry_build.CATEGORY_OF_TYPE`, le categorie curate delle aggiunte).

Lo step 3 ha un osservatore per tecnologia, con lo stesso pattern degli analyzer: un modulo di `dynamic/` che si dichiara (`NAME`, `VERSION`, `LANGUAGES`), elencato da `dynamic.observers()`. Parte per le tecnologie che hanno un grafo statico nello store, prende il comando dei test dalla pre-mappa e usa gli eventi degli analyzer (`analyzer.started`, `progress`, `gap`, `analyzer.finished`, `analyzer.unavailable`). Una tecnologia senza osservatore, un progetto senza un comando dichiarato e una corsa senza motore di container sono lacune: la pipeline arriva comunque all'unione. `DAODAN_DYNAMIC=off` salta lo step.

### 2. Analyzer: un'istanza per tecnologia trovata

- Ogni adattatore si dichiara da solo (`NAME`, `LANGUAGES`, `UNIT_KINDS`, `NEEDS_CONTAINER`): i linguaggi che indicizza e i tipi di unità della pre-mappa da cui prende la struttura (`go-module`, `gradle-project`, `cmake-target`, …). Le voci del passaggio si costruiscono da queste dichiarazioni (`indexers.analyzers`), dal più leggero in memoria al più pesante: uno che esaurisce la memoria ferma quelli dopo.
- Lo step 2 crea un'istanza per ogni tecnologia presente: parte quando lo snapshot ha file dei suoi linguaggi, anche fuori da ogni unità (il codice senza file di build non si perde), e prende le sue unità dalla pre-mappa.
- Interfaccia comune: `structure(premap)`, `index(...)`, le correzioni del grafo opzionali di oggi (`hops`, `same_range`, `classify`, `static`, `refine`, `missing`, `tasks`).
- **Uno strumento ufficiale per linguaggio, nessun lettore scritto a mano accanto.** *Deciso dal proprietario il 20 novembre 2026.* Chi ha bisogno di un fatto del codice (la funzione che un legame nomina, il tipo di un attributo) lo prende dall'indice che l'analyzer scrive già nel container preparato: nessun secondo programma e nessuna seconda installazione. Motivo: [ingressi e scoperta dei flussi](2026-11-20-ingressi-e-scoperta-dei-flussi.md), motivo 14.
- I fogli di stile diventano un adattatore come gli altri. I motori per posizione restano solo dove nessun indicizzatore serve la tecnologia (Vue, Svelte), come adattatori; Jedi per Python si toglie.

### 3. Listener

- Un bus di eventi in `pipeline`, dal primo step al grafo completo. Ogni evento ha la run, lo step, l'analyzer quando c'è, l'ora, un `kind`, un livello (`debug`, `info`, `warning`, `error`), un messaggio da leggere e i dati.
- I `kind`: `step.started`, `step.finished`, `step.failed`, `step.skipped` (fresco), `analyzer.started`, `analyzer.finished`, `analyzer.unavailable`, `progress`, `gap`, `log`, `graph.ready`.
- **Avanzamento:** `progress` dice, per lo step e per l'intera run, quante unità sono fatte su quante, e la fase dentro l'analyzer (preparazione, indice, grafo). L'interfaccia mostra la percentuale e cosa sta facendo, senza parlare di container o volumi.
- **Feedback:** un `warning` o un `error` ha sempre causa e rimedio, come le lacune di oggi.
- **Log:** l'uscita degli strumenti diventa `log` di livello `debug`, con il limite di lunghezza che i registri delle run hanno già.
- Un listener si registra con una funzione (`on(event)`) da Python, o legge gli eventi dal servizio MCP con il cursore che `codebase_map_events` ha già.
- Gli eventi si scrivono anche nel registro della run, così un listener che arriva dopo li rilegge.
- Un listener che fallisce non ferma l'analisi: il suo errore diventa un evento.

### Preparazione

Ogni comando nel container, della pre-mappa o di un analyzer, ha prima ciò che serve alla CI del progetto: strumenti, toolchain e dipendenze. È uno strato solo del runner del container (`preparation.py`), che gira nella preparazione, con la rete verso i registri dei pacchetti e verso gli host che ogni strumento dichiara (come quelli di Bazel), mai altro. Gli strumenti Java ricevono il proxy come proprietà di sistema e Maven anche nelle sue impostazioni (`JAVA_PROXY`).

- **Toolchain:** le versioni che la faccetta `toolchains` della pre-mappa dichiara le installa mise, ognuna alla versione scritta (`mise install strumento@versione`): mise non sceglie mai una versione da sé. mise stesso è un pin con sha256 (`MISE`). Una versione che è un intervallo, o uno strumento che mise non installa, è una lacuna `toolchain_unavailable` che nomina strumento e versione; un'installazione fallita lo scrive e la run va avanti con ciò che si è installato. **Deciso dal proprietario il 21 novembre 2026: Daodan ha qualunque JDK serva, marca compresa.** Una build che fallisce nominando un JDK più nuovo, o di un'altra marca, non è una lacuna: Daodan lo installa e riprova una volta, nella pre-mappa (`jdk_from_build_error`) e nell'indicizzatore, mai una terza. Il file `gradle/gradle-daemon-jvm.properties` è una dichiarazione: la pre-mappa ne legge versione e marca (`premap/jvm_files.py`), Gradle parte su quel JDK e i toolchain degli script si installano accanto; le righe `toolchainUrl` non si scaricano mai. Le marche stanno in una tabella (`preparation.JDK_VENDORS`, undici con un JDK in mise; AdoptOpenJDK, Apple e HP-UX sono una lacuna `toolchain_unavailable`), con i loro host. *Fatto il 22 novembre. Su due fixture (`benchmarks/project-model/fixtures/_jvm-kotlin-jdk-from-error`, `_jvm-kotlin-daemon-vendor`) su Modal Kotlin passa da non indicizzato a `fresh`. Installate davvero solo JetBrains e Temurin; le altre nove marche sono verificate sul catalogo di mise, non con un'installazione; gli host non sono osservati nel proxy del container, perché su Modal la rete è aperta. Su un progetto reale il JDK ora è quello giusto e la build Android generata da Tauri fallisce più avanti, per un file che nasce solo durante la build: resta una lacuna con la causa.* Daodan tiene un proprio pin con sha256 (`NEEDS`) solo dove mise non ha un backend verificabile: lo strumento di vcpkg e l'Arm GNU Toolchain.
- **Host:** ogni strumento dichiara i suoi in un punto solo, oltre ai registri di `container.REGISTRIES`: mise in `preparation.MISE_HOSTS` (per strumento: nodejs.org; go.dev e dl.google.com; static.rust-lang.org; builds.dotnet.microsoft.com; download.swift.org; ziglang.org; services.gradle.org; api.adoptium.net; GitHub per le release) più `MISE_OWN` (mise-versions.jdx.dev); vcpkg e Conan in `preparation.NEEDS` (GitHub, center2.conan.io); Bazel in `premap/container_runner.TOOLS` (bcr.bazel.build, mirror.bazel.build, GitHub).
- **Dipendenze:** (`preparation.RESTORES`, una riga per gestore, eseguita dove la sua build parte: la cartella con un suo file che nessun'altra contiene; una cartella che fallisce è una lacuna `restore_failed` con gestore, cartella e righe d'errore dello strumento, e la preparazione va avanti) il comando di ripristino del gestore che il progetto dichiara, con gli script spenti dove lo strumento lo consente: `vcpkg install` in modalità manifest alla baseline che il progetto nomina, `conan install` con il suo lockfile (`--build=missing` solo per ciò che non ha un binario), e dopo npm, pnpm, yarn, uv, pip, poetry, Go, Cargo, Maven, Gradle, .NET, Composer, Bundler, SwiftPM, pub.
- **La ricerca è ricorsiva (deciso dal proprietario il 21 novembre 2026).** Ogni progetto trovato nell'albero, a qualsiasi profondità, riceve il suo ripristino: una cartella con il suo manifest non si salta perché un altro manifest sta sopra. Fa eccezione solo il membro che la cartella sopra nomina nel suo workspace, letto dove lo legge il gestore che ripristina quella cartella (`workspaces` per npm e Yarn, `pnpm-workspace.yaml` per pnpm): quello lo ripristina la radice. Corregge la regola del punto sopra («la cartella con un suo file che nessun'altra contiene») dove salta un progetto indipendente. *Fatto il 22 novembre per npm: una cartella con il suo `package-lock.json` o `npm-shrinkwrap.json` sotto un'altra è un ripristino a sé, come già con `pnpm-lock.yaml` e `yarn.lock` (fixture `_js-nested-npm-apps` su Modal: nessuna lacuna, TypeScript `fresh`). Su un progetto reale con tre app sotto la radice, in una di esse le chiamate senza esito scendono da 5.918 a 1.472. Aperti: una cartella annidata senza lockfile che nessun workspace nomina resta `restore_failed` (ripristinarla da sola prenderebbe dal registro un pacchetto che in un progetto Lerna sta nel repository, e `lerna.json` non è letto); un crate Cargo annidato con il suo `Cargo.lock`, un progetto .NET annidato e un `requirements.txt` annidato non si ripristinano da soli.*
- **Compilatori:** un file di toolchain CMake (o un file cross di Meson, un profilo Conan) che nomina un compilatore noto (`COMPILERS`) lo porta sul path; ogni preset di configure gira.
- **Un comando dichiara ciò che gli serve** (`needs`), il runner lo prepara una volta per run. Ciò che non si può installare o ripristinare resta una lacuna che lo nomina: un configure che fallisce dice quale compilatore o pacchetto manca.
- Se un progetto dichiara due gestori (vcpkg e Conan), vince quello che i preset nominano, altrimenti vcpkg; una lacuna `choice` lo dice.
- **Una preparazione per analisi.** La pipeline riusa il ripristino Node fra `tsc`, scip-typescript e l’osservatore JavaScript quando coincidono checkout, contenuto dei file e lockfile, toolchain, immagine, registri e accesso ai valori dei file .env. Ogni strumento copia i volumi preparati in volumi privati. A fine analisi i volumi vengono rimossi. Un ripristino parziale conserva le lacune e viene ritentato dal consumatore successivo. L’installazione che richiede l’ambiente specifico della CI resta privata. Il test `tests/test_codebase_map_shared_node.py` verifica i tre ingressi con un motore simulato. La misura su progetto reale resta da eseguire. Motivo 7 e task 1b del [piano del 20 novembre](../plans/2026-11-20-pipeline-intera.md).

### 4. Codice

- `pipeline/`: gli step, l'orchestratore, gli eventi.
- `premap/`: come oggi (step 1).
- `analyzers/`: gli adattatori di oggi sotto `indexers/`, più i fogli di stile e i motori per posizione rimasti.
- `resolve_edges.py` si divide: l'orchestrazione va in `pipeline/`, i motori in `analyzers/`, la preparazione delle dipendenze nel container. Una funzione oltre le 80 righe si spezza.
- `snapshot.py` e `modules.py` si spezzano per responsabilità, senza cambiare ciò che scrivono.

### 5. Ordine del lavoro

Ogni passo lascia i test verdi e le uscite uguali, controllate con le registrazioni dei 122 progetti (`tools/premap_replay.py`) e con le fixture del grafo.

1. `pipeline/` con gli step 1, 2 e 4 e il bus degli eventi, sopra il codice di oggi; ogni step e ogni analyzer emette i suoi eventi.
2. Lo step 2 sceglie gli analyzer dalla pre-mappa; `ENGINES` sparisce.
3. I fogli di stile come adattatore.
4. `resolve_edges.py` diviso; i motori per posizione rimasti come adattatori, Jedi tolto.
5. `snapshot.py` e `modules.py` spezzati.

### 6. Sotto il blocco del progetto nulla aspetta il container

Applicato (Scelte, 6). Prova: `tests/test_codebase_map_reactive_server.py`; `tests/test_codebase_map_mcp.py` (`test_events_and_status_follow_the_analysis_pipeline_of_the_run`).

1. Sotto `project_lock` girano solo letture dello snapshot: la scansione veloce (`Context.fast_scan`, senza runner) e lo stack, che lancia stack-analyser sull'host con il Node di Daodan. Il piano 2 dello stack dal fork ha misurato lo stack della veloce, con il rilascio `.2`: mediana 0,523 s, massimo 5,791 s su 178 fixture, contro 0,013 s del registro ([README di project-model](../../benchmarks/project-model/README.md), «Lo step `stack` dal fork»); dopo il passaggio non è misurato. Così fanno `MapService.create_run` e l'aggiornamento dell'hook `PostToolUse` (`snapshot.refresh_working --hook`). Il resto lo fa il processo staccato (`resolve_edges.py --pass`), fuori dal blocco: la scansione, se restano comandi di modello `not_run`, poi stack, analisi, dinamico e unione.
2. `snapshot.py write` da riga di comando fa la scansione intera e lo stack prima di avviare il passaggio del motore.
3. `MapService` dà `stack(run_id, module=None)`; `status(run_id)` dice lo stato degli step della pipeline e del run `working`; `modules(run_id)` porta `nature`, `languages` e `toolchains`; a ogni evento del servizio o aggiornamento dell'hook si registra un impulso (`live-pulse.jsonl`).
4. Il server MCP espone lo strumento `codebase_map_stack`, la risorsa `daodan://project/live` e notifiche di avanzamento e di aggiornamento che non bloccano.
5. Il server dell'interfaccia inoltra `pipeline_after` e `run=working` in `/api/events`, aggiunge `/api/modules`, `/api/stack` e lo stream `/api/stream`, solo da loopback e con il token, chiuso in modo pulito allo spegnimento, e dà `nature`, `languages`, `toolchains`, `frameworks`, `libraries`, `services` e `tools` nelle entità senza aspettare il container.

### 7. Analisi unificata: niente si fa due volte

*Proposta della seconda revisione esterna del 20 novembre 2026, fatta sulla spec divisa (commit `98f360b73`): il proprietario la conferma punto per punto. I fatti sul codice sono verificati lo stesso giorno, non misurati.*

**Scopo.** Dato uno snapshot del progetto, Daodan produce il grafo più completo che riesce a verificare, nel minor tempo e con il minor consumo di CPU, RAM e disco, a parità di copertura. Pre-mappa, moduli, statico, inferenza e dinamico condividono preparazione e risultati; le interfacce fanno parte del progetto analizzato dall'inizio.

1. **Che cosa si condivide già.**
   - Condivisione del ripristino Node applicata nel percorso della pipeline e verificata con motore simulato («Preparazione», task 1b). Con un motore di container vero i volumi clonati sono girati la prima volta il 21 novembre 2026, e fallivano: i file d'ingresso di ogni run (`node.tar.gz`) arrivavano dopo la clonazione, quando il volume non è più vuoto e il motore non lo riempie più da ciò che si copia prima dell'avvio; `tsc` e scip-typescript non partivano. Ora entrano con la fase di clonazione (`node_preparation.clone`; `tests/test_codebase_map_shared_node.py` simula quella regola del motore), e su una fixture Tauri `tsc` e scip-typescript girano ([`real_paths.py`](../../benchmarks/system-map/real_paths.py)). Su Modal ogni run ripristina per sé (`sandbox_run`, [README di project-model](../../benchmarks/project-model/README.md), 21 novembre 2026): lì la condivisione non si misura.
   - Uno step fresco non si rifà (sezione 1), e un linguaggio già osservato con lo stesso registratore non si osserva di nuovo (`dynamic.run`).
   - Il gestore di un controllo viene dall'indice che l'analyzer scrive già (sezione 2; [interfacce del progetto](2026-11-19-interfacce-del-progetto.md), 6.5).
   - L'esplorazione delle interfacce e la corsa del programma partono dal container preparato, senza un'installazione loro (interfacce, 7.1; [registro dell'esecuzione](2026-11-19-esecuzione-del-programma.md), sezione 4): proposta.
2. **Che cosa si fa ancora più di una volta.**
   - Il costo del ripristino condiviso su un progetto Node reale è da misurare (task 1b).
   - Lo stesso codice è caricato da più programmi nello step 2. Dopo scip-python gira un secondo passaggio di Pyright sullo stesso ambiente (`indexers/python_unbound.py`). Dopo scip-typescript il passaggio del controllore ricostruisce il programma in un altro processo (`indexers/typescript_unbound.js`), e il grafo dei fogli di stile ne costruisce un terzo (`indexers/css_typescript.py`). Ognuno risponde a una domanda diversa; il costo di caricare il programma si paga ogni volta.
   - Lo stato del passaggio è per linguaggio, non per modulo (`engine_pass.py`): quanto si rifà dopo una modifica a un solo modulo non è misurato.
   - L'app può partire tre volte: come `webServer` dei test Playwright (step 3), nella corsa del programma e nell'esplorazione delle interfacce. Le ultime due sono proposta, e nessun testo dice che condividono un avvio.
   - L'esplorazione aziona ogni controllo una volta, anche quelli che un test del progetto ha già azionato.
3. **Regole proposte.**
   - **Un indice per unità e tecnologia, letto da tutti:** interfacce, flussi e review. Un secondo programma sullo stesso codice entra solo se riusa il programma già caricato dal primo, oppure con il suo costo misurato e scritto.
   - **Un avvio dell'app per stato dei dati.** Esplorazione e corsa del programma riusano l'avvio dei test quando lo stato lo consente; se un test ha cambiato i dati ripartono da uno stato pulito, dal container preparato, senza un nuovo ripristino.
   - **L'esplorazione lavora sullo scoperto.** Un controllo si può saltare solo quando la traccia dei test identifica lo stesso elemento, lo stesso evento e lo stesso stato osservabile della schermata. Due pulsanti che chiamano lo stesso gestore restano due controlli. Un elemento ricreato, una nuova pagina o un cambio di stato richiedono una nuova osservazione. I collegamenti da provare si contano separatamente.
     L'osservatore dei test Playwright raccoglie le terne per il documento principale. Il rapporto di esecuzione le conta in `ui_controls`: `observed` sono le terne osservate nei vari stati, `pending` quelle ancora aperte all'ultima lettura di ciascun documento. Gli identificativi valgono solo in quel documento. Il lettore copre `click` e `change` sui controlli supportati del DOM e usa le variazioni osservabili della pagina e dei campi per distinguere gli stati. L'esplorazione automatica resta al task 11, dopo la misura 2b.
   - **Una superficie nuova dichiara** come si riconosce, quali indici riusa e come si osserva in esecuzione: entra nella stessa pipeline, senza una pre-mappa, una build o un'analisi per linguaggio sue (interfacce, sezione 3).
4. **La misura.** Tre corse sullo stesso progetto: da zero, senza modifiche, dopo una modifica a un solo modulo. Per ognuna: tempo totale, CPU, picco di RAM, spazio temporaneo, ripristini, indicizzazioni, avvii dell'app. Accanto, i collegamenti attesi ritrovati, prima di tutto interfaccia → gestore → backend o comando nativo: senza questa colonna un costo che scende può voler dire che si è analizzato meno. Parametri e risultati nel README di [`benchmarks/project-model`](../../benchmarks/project-model/README.md) (task 2b del [piano](../plans/2026-11-20-analisi-unificata.md)).

### 8. La pipeline riordinata: ordine, piano, nomi

*Chiesta dal proprietario il 22 e il 23 novembre 2026 e approvata: i nomi con «sì a tutto», l'ordine e la regola di 8.1 con parole sue. **Stato al 24 novembre 2026:** il codice ha 8.9, i passi 1, 2 e 4 di 8.11, parte dei passi 3 e 5 (pezzi A–D; E1 tolto e F fermo, per le misure: 8.3) e 8.13. Non ha i nomi nuovi (8.7), `plan` come step, la freschezza in un punto solo (8.8) e l'unione di `connect`. Che cosa gira oggi e in che ordine: [Codebase Map, «Oggi nel codice»](../plugins/codebase-map.md#oggi-nel-codice). Dove il testo sotto dice «oggi» senza una data, è il codice del 22 e 23 novembre, prima di quei passi; fanno eccezione le colonne «Oggi nel codice» di 8.2 e «Step oggi» di 8.7, aggiornate al 24 novembre. I fatti sul codice sono letti in quei due giorni in `pipeline/`, `snapshot.py`, `engine_pass.py`, `import_resolution.py`, `technologies.py` e nei contratti di `languages/`, `premap/`, `indexers/` e `dynamic/`, non in ogni adattatore.*

**8.1 La regola.** Ogni step parte da ciò che gli step prima hanno stabilito. **Ogni fatto ha un padrone solo:** uno step non riscopre ciò che un altro stabilisce, lo chiede a lui. Dove il padrone non ha potuto stabilirlo (manca il container), chi ne ha bisogno usa un ripiego e lo scrive accanto al dato.

**8.2 Gli step.** L'ordine viene dalla colonna «Deve sapere prima»: `scan`, `recognize`, `plan`, `parse`, `resolve`, `observe`, `connect`.

| Step | Che cosa fa | Deve sapere prima, e da chi | Che cosa scrive |
| --- | --- | --- | --- |
| 1 `scan` | Percorre tutte le cartelle e i file; chiede agli strumenti di build com'è fatto il progetto | La cartella e il perimetro: da chi avvia l'analisi | L'inventario dei file (percorso, dimensione, hash, linguaggio, motivo di esclusione) e il modello del progetto (moduli, unità, toolchain, pacchetti, comandi di test, servizi, radici e alias degli import) |
| 2 `recognize` | Riconosce framework, librerie, strumenti e servizi | Pacchetti, servizi, immagini e unità: da `scan` | Le tecnologie di ogni modulo |
| 3 `plan` | Decide quale adattatore gira su quale parte, e che cosa gli serve prima | File e linguaggi per modulo: da `scan`. Tecnologie: da `recognize`. Le dichiarazioni degli adattatori | Il piano (8.4) |
| 4 `parse` | Legge i sorgenti | Quali file, in che linguaggio, in quale modulo, con quali letture di framework: dal piano. Radici e alias degli import: da `scan` | Simboli, import e riferimenti di ogni file, e come è andata la sua lettura (letto, escluso, errore, ripiego) |
| 5 `resolve` | Trova dove arriva ogni chiamata | I riferimenti: da `parse`. Unità e build: da `scan`. L'ambiente preparato | Gli archi provati |
| 6 `observe` | Esegue i test e registra che cosa chiamano; avvia l'app che il progetto dichiara e ne preme i controlli in un browser | I comandi di test, di avvio e di build: da `scan`. I riferimenti: da `parse`. Il grafo statico del linguaggio: da `resolve`. L'ambiente preparato | Gli archi osservati, i campionati a parte; i controlli premuti, con le funzioni del progetto che hanno fatto girare |
| 7 `connect` | Unisce, e dice che cosa manca | Tutto | Il grafo completo: gli archi fra moduli, gli ingressi dei flussi uniti alle loro definizioni, l'osservato contro il provato, e le lacune |

| Step | Adattatore | Strumento sotto | Oggi nel codice |
| --- | --- | --- | --- |
| 1 `scan` | scanner | Il percorso dell'albero (`tree_scope.py`); go-enry; cargo, gradle, maven, npm, `tsc`, cmake, … | Lo step `scan` c'è; l'inventario lo scrive lo snapshot, prima della pipeline |
| 2 `recognize` | recognizer | stack-analyser, il fork ([spec del 21 novembre](2026-11-21-stack-dal-fork.md)) | Step `stack`, con il fork (`stack_recognition.py`); legge solo i fatti dello step 1 e i file che il fork legge da sé |
| 3 `plan` | nessuno | — | Una funzione, non uno step (`pipeline/plan.py`; 8.11, passo 4): la chiamano la lettura, `engine_pass.pass_plan` e il passo dinamico; lo step `parse` la emette come evento |
| 4 `parse` | parser | tree-sitter, `ast` di Python; SQL e PL/SQL ancora con espressioni regolari (`languages/sql.py`, `plsql.py`) | Step `parse`, terzo in `STEPS` (8.11, passi 3 e 5); ogni chiamante legge ancora prima, con `read_project`, e lo step trova lo store letto |
| 5 `resolve` | resolver | Un indicizzatore SCIP per tecnologia (scip-typescript serve quattro linguaggi); per i fogli di stile i loro parser | Step `analyze` |
| 6 `observe` | observer | Un registratore per linguaggio (`*_record.*`); per l'app, Chromium senza interfaccia di Playwright (`dynamic/app.py`, `explore.cjs`) | Step `dynamic`; senza grafo statico non parte (`no-static-graph`); l'app si avvia solo con npm (`start_runner_not_supported` per pnpm, Yarn e Bun) |
| 7 `connect` | nessuno | — | Step `union`: dice ciò che il grafo ha e non ha, non unisce ancora |

Perché `recognize` e `plan` stanno prima di `parse`: `recognize` non legge nulla di ciò che `parse` produce (`technologies.py`: solo i fatti dello step 1), mentre `parse` deve sapere che cosa leggere e come. Perché gli archi fra moduli e gli ingressi dei flussi stanno in `connect`: uniscono ciò che `parse` legge a ciò che `scan` stabilisce, e cambiano quando cambia uno dei due; in `parse`, a un modulo che lo strumento di build corregge dopo si dovrebbero rileggere file che non sono cambiati. Fino al 23 novembre li scriveva lo step `scan` (`module_derive`, `premap/flow_entries.py`), perché girava dopo la lettura; ora gli archi li aggiunge il primo lettore del grafo intero (`modules.ensure_graph`, anche lo step `union`) e il legame lo fanno i collegamenti (`binder.bind`): 8.11, passo 5, pezzi A e B.

**8.3 Che cosa `parse` smette di scoprire da sé.** *Stato al 24 novembre 2026: il punto 1 è fatto (8.11, passo 2). Del punto 2 il linguaggio è dell'inventario, che lo decide ancora con estensione e contenuto (`file_inventory.write`), non con go-enry. Il punto 3 è tolto (deciso il 24 novembre, sotto). Il punto 4 resta. Il testo sotto descrive il codice del 22 novembre.* Oggi gira per primo, e stabilisce da solo quattro fatti che non sono suoi:

1. **Quali file ci sono:** percorre l'albero (`_SnapshotPass.sources`). Diventa: li riceve dall'inventario.
2. **Il linguaggio di un file:** estensione, più espressioni regolari sul contenuto per `.h`, `.ts` e `.sql` (`languages.detect_language`). `scan` lo chiede a go-enry, il port di Linguist. Diventa: il linguaggio è dell'inventario; l'estensione è il ripiego finché go-enry non ha risposto.
3. **Quali file lasciare fuori:** legge anche quelli che `scan` poi dichiara generati, di terze parti o binari, e l'esclusione arriva dopo, come stato. Diventa: non li legge.
4. **La configurazione degli import:** legge `tsconfig`, `jsconfig` e i workspace a mano (`import_resolution.py`: commenti, `extends`, `baseUrl`, `paths`). `scan` lo chiede a `tsc`. Diventa: radici e alias sono del modello del progetto; la lettura a mano è il ripiego dove `tsc` non è girato.

*Nome: `read_project` si chiamava `write_snapshot` fino al 25 novembre 2026 (proprietario: il nome non diceva che legge).*

**Scelte del 24 novembre 2026, dopo le misure di 8.10.** Criterio del proprietario: meno codice nostro possibile, e dati da sorgenti aggiornate. Le misure sono in [`benchmarks/project-model`](../../benchmarks/project-model/README.md).

| Punto | Che cosa si fa | Chi l'ha deciso | Perché |
| --- | --- | --- | --- |
| 2, il linguaggio | Verrà da una libreria nostra, con il catalogo di Linguist come punto di partenza ([spec](2026-11-24-libreria-del-linguaggio.md)). **Nel prodotto oggi non c'è nulla:** resta `languages.detect_language` | Proprietario | go-enry gira nel container, dopo la lettura: la nostra tabella sarebbe rimasta come ripiego. Su 47.543 file i due linguaggi divergono in 87. Un primo lettore dei soli dati di Linguist, provato e non entrato: leggeva come C 95 header C++ su 6.857 e perdeva 8 `.ts` su 47.999 |
| 3, quali file lasciare fuori | `parse` non esclude nulla: l'esclusione resta l'etichetta `excluded` della pre-mappa. E1 è tolto | Proprietario («C») | I predicati di Linguist rispondono a «conta nelle statistiche», non a «non è codice del progetto»: su 56 progetti veri toglierebbero 1.496 file letti, verso cui vanno 96 import (`CTFd/cache/__init__.py`, importato da 45 file) |
| La lettura dentro lo step `parse` | Tolta: l'unica lettura è `read_project`. Lo step dice solo il piano, e uno store di solo inventario ferma la pipeline | Proprietario («C») | Nessun chiamante la usava |
| 4, la configurazione degli import | Ferma: resta la lettura a mano | Chi scrive; confermato dal proprietario il 25 novembre | Sui 25 progetti veri la configurazione di `tsc` guadagna 0 import e ne perde 110. Da rivalutare un risolutore pronto (`ts.resolveModuleName`, oxc-resolver) solo se riduce il codice |
| I chiamanti verso «inventario + pipeline» | Fermi | Chi scrive; confermato dal proprietario il 25 novembre | Con E1 e la lettura in `parse` tolti, non cambia nulla per il prodotto, e `create_run` e l'hook leggerebbero sotto il blocco del progetto |

**8.4 Il piano.** Una funzione sola, dall'inventario, dal modello del progetto, dalle tecnologie e dalle dichiarazioni degli adattatori. Non stabilisce fatti sul progetto: solo scelte.

- **Un nodo** è un adattatore sulle sue unità o sui suoi file: lo step, l'adattatore con la versione, su che cosa gira, se chiede il container, di quali altri nodi ha bisogno. **Una lacuna** è ciò che nessun adattatore serve, con la causa.
- **I bisogni fanno il grafo.** Un resolver ha bisogno del parser del suo linguaggio; un observer del resolver. La preparazione (toolchain e dipendenze nel container, «Preparazione») è un nodo, fatto una volta per analisi, di cui hanno bisogno gli strumenti di build di `scan`, i resolver e gli observer: non è uno step.
- **Un nodo il cui bisogno è fallito non parte,** e dice quale. Il 22 novembre lo facevano due casi, ognuno a modo suo (dal 23 lo dice il piano, `plan.blocked` e `plan.need`: 8.11, passo 4): un linguaggio che la lettura non ha letto lascia il suo analyzer `unavailable` (`engine_pass.run_pass`), e un linguaggio senza grafo statico non ha osservatore (`no-static-graph`).
- **Ogni file dell'inventario è in un nodo di `parse` o ha un motivo di esclusione.** Nessun adattatore gira fuori dal piano.
- **Si ricalcola quando un fatto cambia,** e rifà solo i nodi che leggono quel fatto: un nodo è fresco quando l'impronta di ciò che legge non è cambiata (8.8).
- È il risultato dello step e un suo evento. Un file a parte entra quando l'interfaccia mostra il piano prima che l'analisi parta, non prima: sarebbe un doppione di ciò che il modello del progetto dichiara già.

Gli step restano una lista ordinata; dentro uno step i nodi girano nell'ordine del piano, i resolver dal più leggero al più pesante in memoria come oggi. Nessun motore generico di grafi e nessun sistema di plugin.

**8.5 Le due parti di `scan` e la prima analisi.** La prima parte gira sull'host, subito: l'albero, il linguaggio per estensione, i lettori dei file. La seconda gira nel container: gli strumenti di build, go-enry, `tsc` (5 s di mediana e 103 s al massimo sui 122 progetti, Scelte 1).

Il proprietario, il 23 novembre 2026, fissa l'obiettivo e non la modalità («alla fine l'obiettivo quello è, al di là della modalità»): alla fine dell'analisi il grafo è quello di un `parse` che ha lavorato sui file, i linguaggi e i moduli che `scan` ha stabilito per intero, comunque ci si arrivi.

**Scelta di chi scrive:** alla prima analisi `parse` parte dopo la prima parte, mentre la seconda gira; la mappa resta utilizzabile subito, come oggi, e la sezione 6 resta com'è. Quando la seconda parte corregge un fatto, si rifà solo ciò che lo legge:

| La seconda parte corregge | Si rifà |
| --- | --- |
| Il linguaggio di un file, o la sua esclusione | La lettura di quel file |
| Radici e alias degli import | La risoluzione degli import, senza rileggere |
| I file di un modulo | Gli archi fra moduli, in `connect` |
| Le unità di una tecnologia | I nodi di `resolve` e `observe` di quella tecnologia |

Vincolo: il risultato finale è uguale a quello che si avrebbe aspettando tutto `scan`, e un test li confronta (8.10). L'altra modalità si ottiene cambiando solo ciò che i nodi di `parse` dichiarano di aspettare. Dopo la prima analisi le due coincidono: la struttura è nota e si aggiorna solo ciò che è cambiato. Senza container la seconda parte è una lacuna (`model_not_run`) e i ripieghi di 8.3 restano il dato, dichiarati.

**8.6 Lo snapshot si divide.** Oggi `read_project` è un passaggio solo sul perimetro (`_SnapshotPass`): per ogni file lo legge, ne calcola l'hash, riusa la voce di prima se vale ancora oppure lo legge a fondo, e scrive; lo store si pubblica intero, con una sostituzione. La sua impronta (`logical_digest`) lega ciò che viene dopo: pre-mappa, grafo dei moduli, tecnologie, schede, archi.

1. **Due scritture sullo stesso store.** L'inventario (`scan`) scrive di ogni file percorso, dimensione, data, hash, linguaggio e motivo di esclusione. `parse` aggiunge simboli, import e riferimenti dei file che il piano gli dà. Ognuna pubblica intera, come oggi.
2. **Due impronte.** Quella dell'inventario lega ciò che legge solo l'inventario: `scan`, `recognize`, `plan`. `logical_digest` continua a legare ciò che legge i simboli: `resolve`, `connect`, le schede. Oggi pre-mappa, moduli e tecnologie si legano a `logical_digest` (`premap/__init__.py`, `modules.py`, `technologies.py`): con `scan` per primo non potrebbero esistere prima di `parse`, e scadrebbero a ogni sua modifica.
3. **Uno store con l'inventario e senza simboli lo dice.** Chi cerca un simbolo riceve «la lettura è in corso» o «non è partita», mai un risultato vuoto.
4. **Il riuso resta dov'è utile.** L'inventario riusa per dimensione e data, come `compare_files`; `parse` riusa la voce di prima per hash e impronta del parser, come `_entry`. I file C e C++ che aspettano il contesto degli include (`c_family`) e i file Python che l'interprete di Daodan rifiuta (`newer`) restano di `parse`.
5. **Le uscite non cambiano.** Sullo stesso albero, lo store dopo inventario e lettura ha lo stesso `logical_digest` del passaggio solo di oggi (8.10). *Il passaggio solo (`build_manifest`) è tolto il 24 novembre: una strada sola.*

*Applicati il 23 novembre 2026 i punti 1, 3 e 5* (`file_inventory.write`, `snapshot.write_reading`, la tabella `inventory` dello store). Lo store di solo inventario porta `reading: "not-started"` nell'header; quello letto non lo porta, così il `logical_digest` resta quello di prima. `files_read` e `source_bytes_read` contano solo le letture dell'inventario, perché l'header resta uguale. Il punto 2 è applicato con il passo 5 di 8.11, pezzo C: pre-mappa, struttura del grafo dei moduli e tecnologie si legano a `snapshot_store.inventory_digest`. Del punto 4 c'è il riuso di `parse`: la lettura rilegge solo i file che non copia in blocco dallo snapshot di prima. L'inventario invece legge e calcola l'hash di ogni file come prima: riusare per dimensione e data salterebbe un file cambiato con la stessa dimensione e la stessa data, e si decide con la misura del punto 6, che resta da fare su Modal.
6. **Da misurare prima di scegliere come.** Il contenuto di un sorgente si legge due volte, per l'hash e per la lettura, dove oggi una: il tempo sul corpus dice se l'inventario deve passare i byte a `parse` o se la seconda lettura non pesa.

**8.7 Nomi.** Regola: uno step è un verbo che dice ciò che Daodan fa; l'adattatore che lo serve è il nome d'agente di quel verbo; **adattatore** è la parola per tutti; una parola per concetto.

| Step oggi | Step | Adattatore | Cartella oggi → nuova |
| --- | --- | --- | --- |
| `scan`, più l'inventario di `snapshot.py write` | `scan` | scanner | `premap/` → `scanners/` |
| `stack` | `recognize` | recognizer | `stack_analyser.py` |
| manca come step; la funzione è `pipeline/plan.py` | `plan` | nessuno | `pipeline/` |
| `parse`, più la lettura di `read_project` | `parse` | parser | `languages/` → `parsers/` |
| `analyze` | `resolve` | resolver | `indexers/` → `resolvers/` |
| `dynamic` | `observe` | observer | `dynamic/` → `observers/` |
| `union` | `connect` | nessuno | `pipeline/` |

| Parola oggi | Problema | Proposta |
| --- | --- | --- |
| `engine` | Tre cose: il motore di container (`container.find_engine`), i modelli a cui l'app dà un compito (`engines.py`), il passaggio degli indicizzatori (`engine_pass.py`, `EngineSpec`, `engine-edges.sqlite`, `engine-report.json`) | `engine` resta solo al motore di container, che è la parola di Docker e Podman; il passaggio prende i nomi di `resolve`; i modelli diventano `reasoner` (aperto) |
| analyzer, indexer, adapter | Tre parole per l'adattatore dello step 2; «analyzer» vale per ogni step | resolver. Sostituisce `analyzers/` della sezione 4 |
| `resolver` (colonna dello store) | Nomina chiunque abbia prodotto un arco: un resolver, ma anche un observer e il resolver lessicale dello snapshot. Con il nome nuovo dello step 5 la parola avrebbe due sensi | La colonna diventa `producer` al prossimo cambio di schema; fino ad allora resta. Aperto (A1) |
| `analyzer.started`, `.finished`, `.unavailable` | Li emettono anche gli osservatori | `adapter.started`, `.finished`, `.unavailable`, con il campo `adapter` |
| source (in `premap/`) | Si confonde con il sorgente del progetto | scanner; il grado `scanner` di `RANKS` (go-enry, noir) diventa `detector` |
| premap, pre-map | Due grafie; dice quando viene, non che cosa è | project model, già il nome di `benchmarks/project-model` e dei comandi di modello |
| `ENTRY`, `NAME` | Due parole per il nome di un adattatore | `NAME`; *fatto il 23 novembre per `indexers/` e il 25 per `dynamic/`* |
| step, stage, phase, pass | Quattro livelli senza una regola scritta | `step` della pipeline; `stage` un adattatore sulle sue unità, il nodo del piano; `phase` dentro uno stage; `pass` da confrontare con `run`, non letto |
| I passi del README (Static, Inference, Dynamic, Semantic) | Non sono i nomi degli step | Il README usa i nomi degli step; Semantic resta dopo la pipeline |

**Costo e limiti.** I nomi degli step e degli eventi sono letti da `mcp_service.py`, dall'interfaccia costruita in `daodan/assets/app/` e dai test che nominano step ed eventi; i nomi sul disco (`premap.json`, `engine-edges.sqlite`, `engine-report.json`) da CLI, MCP, viewer e benchmark (sezione 1, «Scansione», punto 5). Il cambio entra una famiglia per volta, con le uscite uguali (sezione 5); i nomi sul disco cambiano solo con un cambio di schema, da decidere. Quanti punti del codice tocca non è contato.

**8.8 Dichiarazione comune e controlli dell'orchestratore.**

1. **Una dichiarazione per ogni adattatore:** `NAME` e `VERSION`, più ciò che serve alla sua famiglia (`LANGUAGES`, `UNIT_KINDS`, `NEEDS_CONTAINER`, `RANK`). Oggi `premap/` dichiara `NAME`, `VERSION`, `RANK` in una lista scritta (`SOURCES`); `indexers/` `NAME` (era `ENTRY` fino al 23 novembre), `LANGUAGES`, `UNIT_KINDS`, `NEEDS_CONTAINER`; `dynamic/` `NAME` (era `ENTRY` fino al 25 novembre), `VERSION`, `LANGUAGES`; `languages/` `language`, scelto dall'estensione. Le famiglie si scoprono dalla dichiarazione, come fa `indexers.analyzers()`. L'ordine di `SOURCES` porta significato (una fonte legge ciò che le precedenti dichiarano; fra pari vince la prima): resta scritto, o diventa un bisogno dichiarato come quelli del piano. Aperto (A1).
2. **La freschezza si controlla in un punto solo,** `pipeline._run`, sull'impronta degli ingressi dichiarati (sezione 1). Oggi `_run` non la controlla e non emette mai `step.skipped`: ogni step chiama il suo `ensure`.
3. **Un test controlla gli ingressi:** ogni ingresso di uno step è l'uscita di uno step prima, o un ingresso della pipeline. *Fatto il 23 novembre:* prova 6.

**8.9 Solidità del processo.** *Revisione del 23 novembre 2026 su `pipeline/` e su `engine_pass.run_pass`: applicata.* Prova: `tests/test_codebase_map_pipeline.py`.

Corretto:

1. **Un giornale che non si può scrivere fermava l'analisi** (disco pieno, permessi): l'errore usciva da `Bus.emit`. Ora i listener lo sanno una volta, con causa e rimedio, e gli eventi continuano ad arrivare loro.
2. **Una riga rotta rendeva il giornale illeggibile per sempre:** `events.read` falliva su di essa a ogni lettura, e con lui `follow` e `runtime`. Ora la riga conta nel cursore e si salta. Ogni evento è una scrittura sola, così le righe di due processi che scrivono insieme non si mescolano.
3. **Un programma di stage che non parte chiudeva l'intera analisi** (`OSError` in `engine_pass._launch`), e così un rapporto di stage che non è un oggetto. Ora fallisce quello stage e gli altri girano.
4. **Uno step tollerato che fallisce finiva con uno `step.finished` uguale a quello di un successo.** Ora porta `failed` con la causa.
5. **La lacuna «nessun arco osservato» perdeva la causa** quando lo step dinamico falliva o non girava in quell'analisi. Ora la dice.
6. **Un `start` o `stop` che non nomina uno step** dava un errore di lista; ora è rifiutato prima di ogni evento, con i nomi validi.
7. **Un'analisi interrotta lasciava nel giornale uno step iniziato e mai finito.** Ora la fine la dice chi sa che l'analisi è finita: lo step stesso su un'interruzione (Ctrl-C, l'uscita dell'interprete); `stop_pass` e `reset_pass` dopo aver chiuso il passaggio; `ensure_edges` prima di avviarne uno nuovo, per quello morto senza una parola (`events.close_open`: uno `step.failed` per step, un `analyzer.finished` di errore per analyzer, con la causa). Limite: chi chiude non distingue uno step di un'altra analisi che gira nello stesso momento sullo stesso snapshot; nessuno dei tre chiamanti di `ensure_edges` la chiama da dentro uno step.
8. **La durata di ogni stage non era registrata.** Ora il rapporto del passaggio la tiene (`engines.<nome>.seconds`): è la misura che serve al limite di tempo qui sotto.

Aperto:

- **Uno stage non ha un limite di tempo suo** (`_launch`): i comandi nel container hanno i loro, ma un indicizzatore che non risponde ferma l'analisi finché qualcuno non la interrompe (`stop_pass`). Serve un limite dichiarato da ogni analyzer accanto a `MIN_FREE`, preso dalle durate che il rapporto ora registra (punto 8) sul corpus; un numero scelto senza misura fermerebbe indicizzazioni lunghe ma sane. Da leggere prima: che cosa resta del container di uno stage chiuso da fuori.
- **Il giornale cresce a ogni analisi dello stesso snapshot** e `events.read` lo scorre dall'inizio a ogni lettura: il cursore è un numero di righe, parte del contratto di MCP. Un cursore in byte lo toglierebbe, cambiando quel contratto.

**8.10 Prove.** Ogni prova resta nel repository. Sono scritte la 1, la 3, la 4 e la 6; le altre no.

1. **Lo snapshot diviso dà lo stesso store.** *Ha fatto il suo lavoro:* sulle 27 fixture del grafo `logical_digest` dopo inventario e lettura era quello del passaggio solo, `build_manifest`, tolto il 24 novembre 2026. Oggi `tests/test_codebase_map_snapshot_split.py` confronta, sulle stesse fixture, `read_project` con inventario più lettura, JSON con SQLite, e l'ordine delle righe con quello del perimetro. Lo step `parse` ha la sua prova in `tests/test_codebase_map_pipeline.py`.
2. **Le due modalità danno lo stesso grafo:** su una fixture con un file che go-enry dichiara generato e un alias di `tsconfig`, il grafo finale di «`parse` dopo la prima parte» è quello di «`parse` dopo tutto `scan`» (8.5).
3. **Il piano copre tutto:** ogni file dell'inventario è in un nodo di `parse` o ha un motivo di esclusione; nessun adattatore parte senza il suo nodo (come il test che oggi impedisce a un indicizzatore di cercare file da solo).
4. **Un bisogno fallito ferma solo chi ne ha bisogno:** con un parser che manca, il resolver di quel linguaggio non parte e dice perché; gli altri girano.
5. **Un ripiego è dichiarato:** senza container, il linguaggio di un `.h` e gli alias di un `tsconfig` portano scritto che vengono dal ripiego.
6. **Gli ingressi degli step** (8.8, punto 3). *Scritta:* `tests/test_codebase_map_pipeline.py`. L'ingresso della pipeline è `pipeline.INPUTS` (l'inventario); uno step fuori posto rende il test rosso.

Misure, su Modal con gli strumenti veri, nel README di [`benchmarks/project-model`](../../benchmarks/project-model/README.md): il tempo della doppia lettura (8.6, punto 6); il tempo di una prima analisi nelle due modalità; quanti file la lettura di oggi legge e `scan` poi esclude.

**8.11 Ordine del lavoro.** Ogni passo lascia i test verdi e le uscite uguali (sezione 5).

1. `read_project` in due scritture, inventario e lettura, chiamate una dopo l'altra come oggi: prova 1. *Fatto il 23 novembre:* `read_project` resta la chiamata di tutti i chiamanti. L'inventario va in un file di appoggio accanto allo store, poi la lettura pubblica una volta sola: una scrittura fallita o interrotta lascia lo store di prima, come prima.
2. La lettura prende file e linguaggio dall'inventario invece di percorrere l'albero. *Fatto il 23 novembre:* la lettura non percorre l'albero e non sceglie il linguaggio. Un file cambiato fra le due scritture è letto com'è, e la sua riga dell'inventario si corregge.
3. L'inventario entra nello step `scan` e la lettura diventa lo step `parse`; le due impronte (8.6, punto 2). *Fatto il 23 novembre, con il passo 5:* `parse` legge uno store che ha solo l'inventario; dopo `read_project` è fresco. `scan` e `stack` vengono prima e leggono solo l'inventario. L'inventario entra davvero in `scan` quando la pipeline riceve la cartella: oggi i chiamanti le danno ancora lo store di `read_project`.
4. La funzione del piano; `parse`, `resolve` e `observe` la eseguono: prove 3 e 4. *Fatto il 23 novembre* (`pipeline/plan.py`; prove in `tests/test_codebase_map_plan.py`, che guardano i lanci veri, spiati, e non il piano). Il piano non è uno step: è una funzione che `write_reading` (solo la parte di `parse`), il passaggio e il passo dinamico chiamano con i fatti che hanno. Un bisogno fallito dice quale (`need`); il blocco vale per linguaggio, come prima. Un file senza nodo di `parse` resta a livello di file, con il suo linguaggio e il motivo. Fuori dal passo: il nodo di preparazione, i comandi degli osservatori, la freschezza per nodo.
5. `parse` prende da `scan` linguaggio, esclusioni e configurazione degli import, con i ripieghi dichiarati; archi fra moduli e ingressi dei flussi passano a `connect`: prove 2 e 5. Con loro passano a valle le letture dei simboli delle quattro sorgenti di framework (passo 3), `parse` va dopo `scan`, e ogni consumatore che smette di leggere simboli si lega all'impronta dell'inventario. *Fatto in parte il 23 novembre, in quattro pezzi:*
   - A: gli archi `imports` e `calls` fra moduli escono da `scan`. Li aggiunge il primo lettore del grafo intero (`modules.ensure_graph`, anche lo step `union`): il grafo che i lettori ricevono è quello di prima.
   - B: nessuna sorgente della pre-mappa legge simboli. Il legame al simbolo si fa nei collegamenti: `binder.bind`, `angular.bind`, `flow_entries.evidence`.
   - C: pre-mappa, struttura del grafo dei moduli e tecnologie si legano all'impronta dell'inventario (`snapshot_store.inventory_digest`). Una nuova lettura degli stessi file le lascia fresche; un file cambiato le rende vecchie.
   - D: gli step sono `scan, stack, parse, …`. `scan` e `stack` leggono le righe dell'inventario (`SnapshotStore.iter_listed`) e su uno store di solo inventario scrivono ciò che scrivono su uno letto (`tests/test_codebase_map_scan_before_parse.py`). Cinque letture di ciò che scrive `parse` sono passate all'inventario: Angular sceglie i file dei componenti dal loro albero sintattico, non dagli import; Noir conta le righe dal testo; il registro dello stack verifica il testo contro l'hash dell'inventario; l'inventario registra lo stato git del work tree; un membro `percorso::simbolo` di un modulo dichiarato o proposto ha in `scan` solo il file verificato (`pending`), e il simbolo lo verifica il grafo intero, che ne riprende membri, gap e stato. Da misurare su Modal: in un progetto Angular `scan` legge l'albero di ogni file TypeScript, prima solo dei file che importavano `Component`.
   - E1: *tolto il 24 novembre 2026 (decisione del proprietario, 8.3).* Escludeva dalla lettura i file della faccia `excluded` della pre-mappa, sul percorso inventario → pipeline. Era fatto il 23 novembre; nessun chiamante l'ha mai usato.
   - F0: i `paths` di `tsc` registrati contro `import_resolution.ts_path_config`, sulle 11 fixture con albero: 5 coppie unità-pattern uguali, 4 che Daodan non vede (`paths` in `tsconfig.base.json` e `tsconfig.app.json`, che non legge), 0 diverse, 0 in più ([README di `benchmarks/project-model`](../../benchmarks/project-model/README.md)). *F1, 24 novembre:* l'adattatore del benchmark legge l'API del compilatore (`ts.getParsedCommandLineOfConfigFile`, `pathsBasePath`) al posto di `tsc --showConfig`, che non dice dove un `paths` ereditato è dichiarato; era quella l'unica coppia diversa. F nel prodotto, la configurazione da `tsc` con la lettura a mano come ripiego dichiarato, aspetta la misura degli import che guadagna sui progetti veri.
   - Misurato su Modal il 24 novembre 2026, da un clone pulito di `76f1e2aa9` con un'analisi fresca: phazly 15/38 flussi chiusi e 105/240 frecce certe (base 15 e 104); Kotlin fallito come nella corsa di base (build Android).
   - Suite: 4054 passati, 0 falliti, dopo `68b784ee7` (prima 2 falliti: la mappa dell'app costruita due volte, il documento di supporto vecchio).
   - Rimisurato il 25 novembre su `3960973d8`, dopo i due pezzi della lettura unica: phazly 16/38 e 119/240 con `rules.json`, 18/38 e 129/240 con le regole dei wrapper; gli stessi numeri della misura dei wrapper del 23 novembre, quindi la lettura unica non cambia nulla. Kotlin fallito come prima.
   - Restano: la sorgente Flask (task 14, in un'altra sessione), che lega ancora i gestori ai simboli quando legge la risposta del comando; i chiamanti che passano da `read_project` all'inventario seguito dalla pipeline, dopo la misura di 8.10 (quanti file la lettura di oggi legge e `scan` poi esclude); il linguaggio da go-enry; la configurazione degli import da `tsc`, con la lettura a mano come ripiego dichiarato; le prove 2 e 5.
6. I nomi, una famiglia per volta (8.7), e la dichiarazione comune (8.8).

Il recognizer entra con il passaggio al fork, nella sua spec: lo step `stack` riconosce solo con stack-analyser.

**8.12 Non letto.** Se le fonti della pre-mappa che guardano un framework (`noir`, `nextjs`) siano lavoro che dipende da `recognize`, e vada quindi nel piano. Che cosa resta del container di uno stage chiuso da fuori (8.9). `pass` contro `run`. Quanti punti del codice tocca la rinomina.

**8.13 Il formato comune degli adattatori di ingressi.** *Chiesto dal proprietario il 23 novembre 2026: «un adapter che riesca ad adattare l'output di ogni strumento in un formato unico e condiviso in tutto Daodan». L'inventario che lo regge è letto lo stesso giorno in `premap/`, `entries.py`, `flows.py` e `dynamic/app.py`, in sola lettura (due sonde eseguite). Applicato lo stesso giorno, tranne i task 14: vedi «Fatto» qui sotto.*

**Scelta di chi scrive: il formato comune parte dalla famiglia delle sorgenti di ingressi** (`noir`, `nextjs`, `react_router`, `angular`, `sveltekit`, `nuxt`, `astro` e i task 14 del [piano](../plans/2026-11-20-ingressi-e-flussi.md)). Le altre famiglie hanno già la loro uscita nello store (simboli, import, archi), e un formato unico fra famiglie sarebbe un sistema di plugin, che 8.4 esclude. È l'applicazione di 8.8 a questa famiglia.

L'adattatore c'è già: `commands(context)`, `read(context, commands, results)` che dà `{"facts": {"framework_entries": [righe]}, "gaps": [...]}`, e `from_record(report)`. Mancano la riga dichiarata e chi la legge per campi: oggi circa venti righe fuori da `premap/` decidono dal **nome** del lettore (`flows.link_facts` per Noir e Next, `_next_handlers`, `_next_path`, `_declared_routes`, la lista dei lettori di `validate_rules`, `entries.compiled`, `registry_rules`, `dynamic/app.py`), e una sorgente nuova le tocca tutte.

1. **Una riga.** I campi: `reader` e `shape` (chiave delle regole e degli id delle schede); `kind`; `site` e `symbol` (`file[:riga]` e `file::<module>` finché la riga non è legata); `path` e `schema` (il percorso nello schema `{}` di `REST`: ogni adattatore traduce l'ortografia del suo strumento, un catch-all non ha schema); `method` (**solo il metodo che lo strumento dà alla riga**: una pagina non ne ha, e il metodo di Noir non si copia più su una pagina di Next); `exports` o `methods` (le esportazioni del modulo che avviano una funzione, su una riga di modulo non legata); `handler` con `site:riga` (il nome di una funzione a una posizione); `handler_source` (il nome dell'adattatore, scritto dal binder); `page` (la riga è una pagina da aprire). Un campo che nessun consumatore ricostruisce per nome non entra: `owner`, `event`, `column` e `label` restano come sono.
2. **Nessun adattatore lega una riga a una funzione dello snapshot.** Lo fa `connect`, con un binder solo, su due forme: il nome di un'esportazione in un file (oggi `_next_handlers`, copiata in `react_router._starts` e importata da SvelteKit e Nuxt) e un nome a una posizione dentro una dichiarazione (oggi il legame di Noir). Ciò che non si riduce a una delle due resta nel suo adattatore, con scritto accanto perché: l'`export default defineEventHandler(...)` di Nuxt (la funzione è l'argomento di una chiamata), `this.save()` e `svc.cancel()` di Angular (la classe del componente e la risposta del controllore dei tipi), Astro (lo strumento non dà la funzione). Oggi cinque sorgenti legano dentro `read()`, e rompono 8.2: nel piano di 8.4 `scan` non ha le dichiarazioni dello snapshot.
3. **Una tupla e una dichiarazione.** `premap.FRAMEWORK_SOURCES` elenca tutte le sorgenti che danno righe, anche Angular e Astro, che oggi si nominano a mano in `entries.compiled` e in `flow_entries.evidence`. La chiave dei collegamenti in cache (`_links_reader_digest`) si ricava da lì: oggi `astro.py` non c'è, e modificarlo non invalida nulla.
4. **La lettura dell'uscita di uno strumento sta nel suo adattatore.** `entries.noir`, `entries.nitro_routes` e `entries.typegen` (circa 65 righe) vanno nei loro adattatori; gli helper che le sorgenti si prestano (`react_router._starts` e `_excerpt`, `angular._folder` e `_bytes`) vanno in un modulo comune delle sorgenti.
5. **Le lacune non si unificano.** L'adattatore dà la forma della pre-mappa (`kind`, `path`, `detail`, `source`) e una stringa `gap` sulla riga; il binder dà la forma dei collegamenti (`site`, `symbol`, `reason`). Unificarle toccherebbe 16 punti di `flows.py`, il trace, `mcp_service.py` e la scheda, senza beneficio oggi.

**Prova prima del codice.** Un adattatore finto aggiunto alla tupla: la sua riga di modulo è legata, fusa con una riga di Noir sulla stessa rotta, classificata e offerta, **senza una riga modificata fuori dal suo file e dalla sua tabella**. Il test estende quello di 13b. Poi, a ogni passo: test verdi e uscite uguali sulle pre-mappe registrate.

**Ordine.** (1) La misura di phazly e la suite su Modal sullo stato di oggi, come base. (2) La tupla, la chiave dei collegamenti e il modulo comune. (3) Il binder unico per Next, React Router e SvelteKit. (4) I campi `schema`, `page` e `method` come sopra, e la lettura di Noir, Nuxt e Next negli adattatori. (5) I task 14, una sorgente per volta, solo dopo il passo 4. Una revisione alla fine del passo 4 e di ogni sorgente.

*Fatto il 23 novembre 2026*, in quattro commit, ognuno con la sua prova vista rossa prima del codice:

| Punto | Dove | Prova |
| --- | --- | --- |
| 4, gli aiutanti comuni | `premap/frameworks.py`: `folders`, `nearest_first`, `folder_of`, `excerpt`, `column_bytes` | `tests/test_codebase_map_premap_frameworks.py`, con la guardia su ogni modulo di `premap/` |
| 2, il binder | `binder.bind`, chiamato da `flows.link_facts` e da `entries._declared_rows`; tolti `_next_handlers` e il ciclo di Noir | `tests/test_codebase_map_entry_binder.py`: una sorgente finta aggiunta alla tupla |
| 1, i campi | `schema` (Next.js e Noir), il `method` dello strumento, `page` (Next.js); `_next_path` in `premap/nextjs.py`; i lettori di `validate_rules` dalle tuple | la stessa sorgente finta offre le sue rotte e assorbe Noir; `dynamic/app._pages` legge `page` |
| 4, le letture | `premap/noir.rows`, `nuxt.nitro_routes`, `nextjs.typegen` | `test_the_reading_of_a_tools_output_is_in_its_adapter` |

Le uscite: il replay delle 122 pre-mappe registrate cambia solo nelle versioni delle quattro sorgenti. Su 482 collegamenti ricalcolati prima e dopo il binder cambiano solo le sue diciture delle lacune. Su 489 dopo i campi restano uguali rotte, archi e store; cambiano i campi nuovi degli ingressi, il metodo di Noir non più copiato su una pagina e la dicitura del catch-all. Due revisioni Opus.

Scelte fatte nel lavoro:
- Il nome di un simbolo legato è quello di `Facts.node`; per le esportazioni provate coincide con quello di prima.
- Una riga di una sorgente fuori dalla tupla (Noir) sulla stessa rotta di una riga di una sorgente della tupla è quella riga, per ogni sorgente della tupla.
- Noir scrive sempre `handler`, anche vuoto: una riga senza nome è una lacuna del binder.
- `schema` e `page` li scrivono oggi solo Next.js e Noir: le altre sorgenti li prendono con i loro task, senza cambiare le uscite prima.

Aperti:
- `premap/flask_app.py` (task 14, in corso altrove) lega ancora dentro `read()`: la guardia lo ferma quando entra nella tupla.
- Un default anonimo (`export default function () {}`) si legge come `export-missing` e sparisce senza lacuna, come prima.

**Da decidere o non letto.** `handler_source` vale due cose, il nome dell'adattatore e un modo (`inline`, `classe`, `locale`), e il viewer lo mostra. Il nome di un simbolo si costruisce in tre modi (`Facts.node`, `_starts`, Angular) e per un'esportazione anonima possono divergere: dedotto, non provato. Una lacuna su una riga senza regola, o di tipo «nessun ingresso», sembra sparire da `links["gaps"]`: dedotto, da provare. Chi assorbe chi fra Noir e Next lo decide il grado `detector` di 8.7: oggi Noir e Next hanno lo stesso grado.

## Scelte

1. **La scansione resta intera.** Lo step 1 comprende i comandi di modello della pre-mappa (Renovate, npm, Go, Cargo, uv, tsc), nel container. Misurato sui 122 progetti il 15 novembre 2026: la pre-mappa dura 5 s di mediana e 103 s al massimo, Renovate 4,8 s di mediana; un indicizzatore dura minuti. Spostarli negli analyzer dividerebbe la struttura del progetto fra due step e farebbe cambiare la pre-mappa a chi la legge. Lo step 1 emette avanzamento per fonte: chi guarda vede i lettori finire subito e i comandi dopo.
2. **Un'istanza per tecnologia, non per unità.** Un analyzer riceve tutte le unità della sua tecnologia e decide come girarle (una build per cartella, un configure per unità): le unità della stessa tecnologia condividono strumenti e dipendenze, e un container per unità costerebbe il tempo fisso ogni volta.
3. **Lo step 4 dice ciò che il 3 ha osservato.** Per ogni tecnologia con archi osservati: quanti siti e quanti buchi chiusi, quelli campionati a parte; come lacune, i test che non sono arrivati in fondo, i file con chiamate che nessun test ha eseguito e gli archi osservati che contraddicono un arco provato. Una tecnologia senza archi osservati resta una lacuna, con la causa che lo step 3 ha dato.
4. **Una mappa dei moduli sola** (sezione 1, «Scansione»). Deciso dal proprietario il 17 novembre 2026. Perché: `modules.py` (`modules.json`), `premap/module_graph.py` (`premap.json`) e `technologies.py` (`technologies.json`) davano unità e tipi diversi; i file fuori da ogni manifest restavano senza modulo (17 fixture su 140 del corpus) e né linguaggi né toolchain erano del singolo modulo; la pre-mappa leggeva i pacchetti e li scartava. Scartato: tenere tre modelli di modulo affiancati. Prova: quella della sezione; il numero 17 su 140 non ha una misura che lo rifà.
5. **Lo stack dai fatti della scansione** (sezione 1, «Stack»). Deciso dal proprietario il 17 novembre 2026. Perché: `service_registry.py` e `system_brief.py` rileggevano `Dockerfile`, `compose*.yml` e `requirements*.txt` con espressioni regolari, ignoravano cinque ecosistemi, confondevano framework ed esecutori dei test con servizi esterni e tacevano le librerie fuori catalogo. Dopo il cambio, sul corpus, i framework per nome salgono da 211 a 363 su 568; per unità i trovati da 268 a 364 su 1.001 ma gli sbagliati da 35 a 208 (la tecnologia giusta sull'unità sbagliata), poi corretti a 553 con 50 sbagliati. Scartato: rileggere i file nello stack. Prova: README di `benchmarks/project-model`, «Lo step `stack` sul corpus». La scheda del sistema legge ancora `Dockerfile` e Compose a righe (`system_brief._declared`).
6. **Sotto il blocco del progetto nulla aspetta il container** (sezione 6). Deciso dal proprietario il 17 novembre 2026. Perché: l'aggiornamento dell'hook `PostToolUse` eseguiva la pipeline fino alla scansione con il runner del container dentro `project_lock`, e così bloccava `MapService`, l'interfaccia e gli strumenti MCP; `create_run` non eseguiva scansione né stack nel passaggio asincrono, e `/api/events` non inoltrava `pipeline_after` né dava uno stream. Scartato: aspettare il container sotto il blocco. Prova: quella della sezione.
7. **Il container su Modal e una preparazione per analisi** (già motivo 15 della spec dei flussi; «Limiti delle prove», 10). Decisi dal proprietario il 20 novembre: la prova da zero gira con il container di Daodan nelle Modal Sandbox (piano del 20 novembre, task 1); le dipendenze si installano una volta per analisi, subito (task 1b; la raccomandazione era di rimandarlo). Perché: finora ogni misura di `benchmarks/system-map` su Modal è girata senza container (scip-typescript `unavailable`, nessun passo dinamico), e prima della condivisione un progetto Node ripristinava le dipendenze tre volte (`tsc`, scip-typescript, l'osservatore). Scartato: restare senza container per il costo delle Sandbox. La prova del task 1 resta `engine-report.json` con scip-typescript `fresh` su `js-vite-react-ts`, per il task 1b il motore simulato conta tre consumatori e un ripristino. Manca la prova reale.

## Limiti delle prove

Dalla [spec dei flussi e della mappa del sistema](2026-11-18-flussi-e-mappa-del-sistema.md), «Assunzioni e limiti noti», con il loro numero.

- **10.** **Senza container.** Ogni misura di `benchmarks/system-map` su Modal è girata senza motore di container: scip-typescript `unavailable`, nessun passo dinamico, nessun collegamento osservato. Sono misure statiche le mappe delle run, le reti degli ingressi, le schede dei percorsi e il lettore del framework, su albero nudo e poi tolto; non ne dipendono l'accordo fra mappatori, i legami fra flussi, la ricerca e Noir. Quali indicizzatori nativi abbiano girato in ogni run non è registrato (Scelte, 7).
- **20.** **Il container su Modal non è quello di Daodan** (B2): la preparazione nella sandbox ha la rete aperta, senza il proxy dei soli registri, e `registries` è ignorato (`benchmarks/project-model/modal_pipeline.py`, docstring). Una prova su Modal non prova quel confine (task 1).

## Da decidere

Dalla [spec dei flussi e della mappa del sistema](2026-11-18-flussi-e-mappa-del-sistema.md), «Decisioni aperte», con il suo numero.

- **3.** La prova 0 sui cinque casi, dopo il via del proprietario con il costo stimato (piano del 20 novembre, task 2).

Dalla seconda revisione esterna del 20 novembre 2026 (sezione 7):

- **U1. Tutta l'analisi nel container?** La revisione propone di lasciare all'host solo avvio, avanzamento e lettura dei risultati. Oggi snapshot, stack e unione girano sull'host, e scip-python sull'host su Linux e macOS: leggono il progetto e non lo eseguono, che è ciò che la regola di `AGENTS.md` chiede. A favore: un ambiente solo e artefatti condivisi senza copie. Contro: la sezione 6 (sotto il blocco del progetto nulla aspetta il container, e la scansione veloce, allora di millisecondi, gira a ogni modifica) e l'uso senza motore di container, dove oggi Daodan dà comunque snapshot e grafo statico con le lacune. Raccomandazione: no; condividere gli artefatti attraverso lo store e tenere sull'host ciò che solo legge. **Deciso dal proprietario il 20 novembre 2026: no**, come la raccomandazione.
- **U2. Le regole della sezione 7.3** (un indice letto da tutti, un avvio per stato dei dati, l'esplorazione sullo scoperto): entrano dopo la misura del task 2b, che dice quanto costa oggi ogni doppione.
- **A1. L'armonizzazione e i nomi della sezione 8.** **Deciso dal proprietario il 22 novembre 2026: sì**, anche `reasoner`. Il 23 novembre fissa l'ordine degli step (8.2) e l'obiettivo della prima analisi (8.5). Restano aperte le scelte che non sono un sì o un no: l'ordine di `SOURCES` (scritto, o bisogno dichiarato: 8.8), `pass` contro `run`, quando cambiano i nomi sul disco, il nome `producer` per la colonna `resolver` dello store, e in 8.9 il limite di tempo di uno stage e la dimensione del giornale.
- Le decisioni sulle superfici (osservare le interfacce desktop Python, il ponte Tauri) sono in [interfacce del progetto](2026-11-19-interfacce-del-progetto.md), «Da decidere».
