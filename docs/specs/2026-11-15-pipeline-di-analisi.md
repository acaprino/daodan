# Pipeline di analisi: step, analyzer con adattatori, listener

**Stato:** approvata dal proprietario il 15 novembre 2026, che ha lasciato a Claude le scelte rimaste (sezione «Scelte»). Lo step 3 è applicato (`pipeline.Dynamic`, `dynamic/`), con gli osservatori di Python, JavaScript e TypeScript, Go, Java e Kotlin, Rust, C e C++, C#. Le regole della mappa dei moduli e dello stack (sezione 1, «Scansione: la mappa dei moduli» e «Stack») e della reattività (sezione 6) le ha decise il proprietario il 17 novembre 2026 e sono applicate; i motivi sono in «Scelte», 4–6. Il 20 novembre 2026, con la divisione per aspetto della [spec dei flussi](2026-11-18-flussi-e-mappa-del-sistema.md), stanno qui l'analisi unificata: una preparazione per analisi («Preparazione»), uno strumento ufficiale per linguaggio (sezione 2), la scelta 7 con i suoi limiti e ciò che resta da decidere. **Piano:** [analisi unificata](../plans/2026-11-20-analisi-unificata.md).

Il proprietario chiede (15 novembre 2026) un codice modulare, pulito e manutenibile: un'architettura a step, il pattern adapter, e la possibilità di registrare listener dell'intero processo di analisi. Primo step: una scansione veloce di moduli e tecnologie; poi, per ogni linguaggio o framework trovato, un'istanza dell'analyzer che sotto usa lo strumento specifico. Il processo dà feedback, informazioni, log, eventi e avanzamento fino alla generazione del grafo completo.

## Parole

- **Step:** una fase dell'analisi, con ingressi e uscite dichiarati. Uno step legge solo ciò che gli step prima hanno scritto.
- **Analyzer:** l'istanza che analizza una tecnologia del progetto. Ha un'interfaccia comune.
- **Adattatore:** il codice sotto un analyzer che usa uno strumento esistente (scip-go, scip-java, scip-clang, i parser dei fogli di stile) e ne normalizza l'uscita. Nessuna logica di uno strumento fuori dal suo adattatore.
- **Evento:** un fatto del processo, dal primo file letto al grafo completo: uno step inizia, un analyzer finisce, una lacuna, un messaggio, l'avanzamento. **Listener:** chi lo riceve.
- **Grafo completo:** l'uscita della pipeline: i grafi di ogni tecnologia, con gli archi osservati nell'esecuzione, uniti ai punti di connessione.

## Comportamento attuale

- Ci sono già due famiglie di adattatori con un contratto: le fonti della pre-mappa (`premap/`, una per strumento, 50-250 righe ciascuna, unite in un punto solo) e gli indicizzatori (`indexers/`, `structure`, `index` e correzioni opzionali; un test impedisce di saltarne una o di cercare file da soli). La parte comune del grafo è `code_graph.py`; il container è `container.py`.
- Gli step non sono scritti da nessuna parte: `snapshot.py write` costruisce lo snapshot, poi chiama il grafo dei moduli, poi la pre-mappa, poi avvia in background il passaggio del motore (`resolve_edges.ensure_edges`).
- Gli analyzer non partono da ciò che la pre-mappa trova: una tabella fissa per linguaggio (`ENGINES`) li sceglie dai linguaggi dei file, e un indicizzatore gira una volta per linguaggio con tutte le sue cartelle.
- Due sistemi convivono in `resolve_edges.py` (4.439 righe, una funzione da 463): i motori per posizione di prima (9 classi: Jedi, JDT LS, Kotlin, LSP) e gli indicizzatori. I primi servono ancora per Vue, Svelte e il passaggio per posizione di Python.
- `snapshot.py` ha 4.038 righe; `modules.py` una funzione da 323.
- I fogli di stile hanno un percorso proprio, fuori dal contratto degli indicizzatori.
- Gli eventi esistono in parte: il servizio MCP registra eventi persistenti di una run (`codebase_map_events`), ma il passaggio del motore e gli indicizzatori non ne emettono.

## Proposta

### 1. Gli step, dichiarati in un punto solo

| Step | Cosa fa | Uscita |
| --- | --- | --- |
| 1. Scansione | Inventario dei file, grafo dei moduli, pre-mappa: moduli, tecnologie, versioni, dipendenze | Snapshot, `modules.json`, `premap.json` |
| Stack (16 novembre 2026, fra 1 e 2) | Le tecnologie di ogni unità di build: framework, librerie, strumenti e servizi, dai segni del registro; ricalcolato quando cambiano snapshot, registro o servizi della pre-mappa | `technologies.json` |
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

**Stack.** Applicato (Scelte, 5). Prova: `tests/test_codebase_map_stack_rationalized.py`; README di [`benchmarks/project-model`](../../benchmarks/project-model/README.md), «Lo step `stack` sul corpus».

1. `service_registry.recognize` legge i fatti della scansione (`packages`, `services`, `docker_builds`, `excluded`) senza rileggere i file, applica `excluded` a ogni tipo di segno e dà a ogni voce la sua categoria (framework, libreria, strumento, servizio: [flussi e mappa del sistema](2026-11-18-flussi-e-mappa-del-sistema.md), 5.1).
2. `technologies.json` dà per ogni modulo, anche `logical` e `virtual`, `{id, name, kind, nature, provenance, paths, languages, toolchains, frameworks, libraries, services, tools, technologies}`, più la vista `units` delle unità fisiche e virtuali. `libraries` elenca tutte le librerie che il modulo dichiara: arricchite dal registro quando le conosce, mai tolte se sono fuori catalogo.
3. Il registro copre anche gli ecosistemi `maven`, `nuget`, `pub`, `hex` e `swiftpm`, e tiene framework ed esecutori dei test (Playwright, Cypress, JUnit, Spring Boot, ASP.NET Core, Flutter, OpenTelemetry SDK) separati dai servizi esterni.

Lo step 3 ha un osservatore per tecnologia, con lo stesso pattern degli analyzer: un modulo di `dynamic/` che si dichiara (`ENTRY`, `VERSION`, `LANGUAGES`), elencato da `dynamic.observers()`. Parte per le tecnologie che hanno un grafo statico nello store, prende il comando dei test dalla pre-mappa e usa gli eventi degli analyzer (`analyzer.started`, `progress`, `gap`, `analyzer.finished`, `analyzer.unavailable`). Una tecnologia senza osservatore, un progetto senza un comando dichiarato e una corsa senza motore di container sono lacune: la pipeline arriva comunque all'unione. `DAODAN_DYNAMIC=off` salta lo step.

### 2. Analyzer: un'istanza per tecnologia trovata

- Ogni adattatore si dichiara da solo (`ENTRY`, `LANGUAGES`, `UNIT_KINDS`, `NEEDS_CONTAINER`): i linguaggi che indicizza e i tipi di unità della pre-mappa da cui prende la struttura (`go-module`, `gradle-project`, `cmake-target`, …). Le voci del passaggio si costruiscono da queste dichiarazioni (`indexers.analyzers`), dal più leggero in memoria al più pesante: uno che esaurisce la memoria ferma quelli dopo.
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

- **Toolchain:** le versioni che la faccetta `toolchains` della pre-mappa dichiara le installa mise, ognuna alla versione scritta (`mise install strumento@versione`): mise non sceglie mai una versione da sé. mise stesso è un pin con sha256 (`MISE`). Una versione che è un intervallo, o uno strumento che mise non installa, è una lacuna `toolchain_unavailable` che nomina strumento e versione; un'installazione fallita lo scrive e la run va avanti con ciò che si è installato. Daodan tiene un proprio pin con sha256 (`NEEDS`) solo dove mise non ha un backend verificabile: lo strumento di vcpkg e l'Arm GNU Toolchain.
- **Host:** ogni strumento dichiara i suoi in un punto solo, oltre ai registri di `container.REGISTRIES`: mise in `preparation.MISE_HOSTS` (per strumento: nodejs.org; go.dev e dl.google.com; static.rust-lang.org; builds.dotnet.microsoft.com; download.swift.org; ziglang.org; services.gradle.org; api.adoptium.net; GitHub per le release) più `MISE_OWN` (mise-versions.jdx.dev); vcpkg e Conan in `preparation.NEEDS` (GitHub, center2.conan.io); Bazel in `premap/container_runner.TOOLS` (bcr.bazel.build, mirror.bazel.build, GitHub).
- **Dipendenze:** (`preparation.RESTORES`, una riga per gestore, eseguita dove la sua build parte: la cartella con un suo file che nessun'altra contiene; una cartella che fallisce è una lacuna `restore_failed` con gestore, cartella e righe d'errore dello strumento, e la preparazione va avanti) il comando di ripristino del gestore che il progetto dichiara, con gli script spenti dove lo strumento lo consente: `vcpkg install` in modalità manifest alla baseline che il progetto nomina, `conan install` con il suo lockfile (`--build=missing` solo per ciò che non ha un binario), e dopo npm, pnpm, yarn, uv, pip, poetry, Go, Cargo, Maven, Gradle, .NET, Composer, Bundler, SwiftPM, pub.
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

1. Sotto `project_lock` girano solo letture dello snapshot: la scansione veloce (`Scan(fast=True)`, senza runner, pochi millisecondi) e lo stack. Così fanno `MapService.create_run` e l'aggiornamento dell'hook `PostToolUse` (`snapshot.refresh_working --hook`). Il resto lo fa il processo staccato (`resolve_edges.py --pass`), fuori dal blocco: la scansione, se restano comandi di modello `not_run`, poi stack, analisi, dinamico e unione.
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

- **U1. Tutta l'analisi nel container?** La revisione propone di lasciare all'host solo avvio, avanzamento e lettura dei risultati. Oggi snapshot, stack e unione girano sull'host, e scip-python sull'host su Linux e macOS: leggono il progetto e non lo eseguono, che è ciò che la regola di `AGENTS.md` chiede. A favore: un ambiente solo e artefatti condivisi senza copie. Contro: la sezione 6 (sotto il blocco del progetto nulla aspetta il container, e la scansione veloce dura pochi millisecondi a ogni modifica) e l'uso senza motore di container, dove oggi Daodan dà comunque snapshot e grafo statico con le lacune. Raccomandazione: no; condividere gli artefatti attraverso lo store e tenere sull'host ciò che solo legge. **Deciso dal proprietario il 20 novembre 2026: no**, come la raccomandazione.
- **U2. Le regole della sezione 7.3** (un indice letto da tutti, un avvio per stato dei dati, l'esplorazione sullo scoperto): entrano dopo la misura del task 2b, che dice quanto costa oggi ogni doppione.
- Le decisioni sulle superfici (osservare le interfacce desktop Python, il ponte Tauri) sono in [interfacce del progetto](2026-11-19-interfacce-del-progetto.md), «Da decidere».
