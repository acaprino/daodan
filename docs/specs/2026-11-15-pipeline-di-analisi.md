# Pipeline di analisi: step, adattatori, listener

**Stato:** In parte. Nel codice (`daodan/core/pipeline/`): gli step `scan`, `stack`, `parse`, `analyze`, `dynamic`, `union` (`pipeline.STEPS`), gli adattatori che si dichiarano, il bus degli eventi, la preparazione, la mappa dei moduli e lo stack, che riconosce solo attraverso stack-analyser ([spec](2026-11-21-stack-dal-fork.md)) (sezione 1), la reattività (sezione 6), la solidità (8.9), la funzione del piano (8.4), lo snapshot in due scritture (8.6, punti 1, 3 e 5), i pezzi A–D del passo 5 di 8.11 (E1 tolto e F fermo per le scelte del 24 novembre, 8.3), il formato comune degli adattatori di ingressi (8.13). Mancano: i nomi di 8.7 (fatto solo `NAME` in `indexers/`), la freschezza in un punto solo e `step.skipped` (8.8), `connect` che unisce (`union` oggi elenca), `plan` come step, il linguaggio dei file da una libreria nostra ([spec](2026-11-24-libreria-del-linguaggio.md), nulla nel prodotto), le prove 2 e 5 di 8.10, le regole di 7.3. Che cosa gira oggi e in che ordine: [Codebase Map, «Oggi nel codice»](../plugins/codebase-map.md#oggi-nel-codice). **Piano:** [analisi unificata](../plans/2026-11-20-analisi-unificata.md).

Un codice modulare a step, con il pattern adapter e listener dell'intero processo: una scansione di moduli e tecnologie, poi per ogni linguaggio o framework un adattatore sopra lo strumento ufficiale, con eventi e avanzamento fino al grafo completo.

## L'analisi è l'intera catena

«Analisi» è tutta la pipeline, dallo statico al dinamico fino al modello. Ogni step parte da ciò che i precedenti hanno stabilito e passa al successivo ciò che non ha potuto stabilire, come lacuna con la causa. **Un buco si dichiara e si misura dopo l'ultimo passo, mai sul risultato di uno solo.**

| Step (nome nuovo) | Che cosa stabilisce | Che cosa lascia, e a chi |
| --- | --- | --- |
| `scan` | Inventario dei file e modello del progetto: moduli, unità, toolchain, pacchetti, comandi di test e di avvio, servizi | Senza container i comandi di modello sono `model_not_run`: restano i ripieghi dichiarati (8.3). I file fuori da ogni unità vanno al modulo `source-tree` |
| `stack` (`recognize`) | Le tecnologie che il progetto dichiara | Ciò che il codice usa senza dichiararlo (una chiamata HTTP a un servizio senza SDK): ai collegamenti e ai flussi |
| `parse` | Simboli, import e riferimenti; il risolutore lessicale lega solo un binding unico | Ogni altra chiamata: a `analyze` |
| `analyze` (`resolve`) | Gli archi provati dall'indice di ogni linguaggio | I buchi per classe (destinazione decisa in esecuzione, valori senza tipo): a `dynamic`. [Spec del passaggio](2026-11-08-risoluzione-chiamate-motore.md), requisiti 5 e 23 |
| `dynamic` (`observe`) | Gli archi osservati nei test e nell'app avviata; chiude un buco dove una corsa esegue la chiamata | Ciò che nessuna corsa esegue: a `union` come lacuna. [Passo dinamico](2026-11-12-passo-dinamico.md), sezione 5 |
| `union` (`connect`) | Che cosa il grafo ha e che cosa manca, per linguaggio | L'elenco dei resti; non unisce ancora i grafi delle tecnologie |
| Dopo la pipeline | Il modello scrive regole di collegamento e schede, la macchina le verifica; i flussi uniscono chi scrive, chi legge e le azioni | Lati singoli e lacune dichiarati: [flussi e mappa del sistema](2026-11-18-flussi-e-mappa-del-sistema.md), 1.3 e 1.6 |

Il passaggio misurato fra `analyze` e `dynamic`: su tududi, JavaScript, delle 16.527 chiamate che `analyze` lascia senza risposta il registro esatto ne risolve 13.677, l'82,8% ([`benchmarks/call-provenance`](../../benchmarks/call-provenance/README.md)). Gli altri passaggi non hanno una misura dopo il passo successivo: vedi «Da decidere».

## Parole

- **Step:** una fase dell'analisi, con ingressi e uscite dichiarati. Legge solo ciò che gli step prima hanno scritto.
- **Adattatore:** il codice che usa uno strumento esistente (scip-go, scip-java, scip-clang, i parser dei fogli di stile) e ne normalizza l'uscita. Nessuna logica di uno strumento fuori dal suo adattatore. Nel codice si chiama ancora anche analyzer, indexer, observer, source (8.7).
- **Evento:** un fatto del processo, dal primo file letto al grafo completo. **Listener:** chi lo riceve.
- **Grafo completo:** l'uscita della pipeline: i grafi di ogni tecnologia, con gli archi osservati, e ciò che manca.

## 1. Gli step, dichiarati in un punto solo

**In uso.** `pipeline.STEPS`; ogni step ha lo stesso contratto: `inputs`, `run(context)`, `outputs`. L'ingresso della pipeline è `pipeline.INPUTS` (l'inventario). Lo snapshot lo scrive ancora `snapshot.py write`, in due scritture (inventario, poi lettura), che poi esegue la pipeline fino a `stack` e avvia in background il passaggio (`resolve_edges.ensure_edges`). Chi scrive lo snapshot, chi esegue quali step e quando: [Codebase Map, «Oggi nel codice»](../plugins/codebase-map.md#oggi-nel-codice).

| Step | Cosa fa | Uscita |
| --- | --- | --- |
| `scan` | Grafo dei moduli e pre-mappa: moduli, tecnologie dichiarate, versioni, comandi | `modules.json`, `premap.json` |
| `stack` | Le tecnologie di ogni unità di build, dai fatti di `scan` | `technologies.json` |
| `parse` | La lettura dei sorgenti che il piano gli dà | Simboli, import e riferimenti nello store dello snapshot |
| `analyze` | Un adattatore per ogni tecnologia, ognuno con le sue unità | Una voce per tecnologia nello store dei collegamenti |
| `dynamic` | I test nel container, e l'app che il progetto dichiara | Archi osservati, i campionati a parte |
| `union` | Dice che cosa il grafo ha e che cosa manca | Il rapporto del grafo completo |

**Scansione: la mappa dei moduli.** Prova: `tests/test_codebase_map_modules.py` (`test_contract_directory_and_source_do_not_declare_module`), `tests/test_codebase_map_premap_packages.py`, `tests/test_codebase_map_stack_rationalized.py`.

1. `modules.json` è la mappa sola dei moduli. Ogni modulo dichiara `nature`: `concrete`, un'unità di build con un artefatto o sorgenti compilati; `logical`, un modulo dichiarato (`codebase-modules.json`) o proposto (`proposals.json`); `virtual`, un workspace, una solution o un reactor senza artefatto proprio, e il modulo implicito `source-tree` dei file che nessuna unità di build copre.
2. Ogni modulo dice `languages`, i file per linguaggio al netto di `excluded`, e `toolchains`, `{tool, version, declared_in}`.
3. La pre-mappa ha la faccetta `packages`, `{ecosystem, name, declared_in, version}`: la versione è il testo che il manifest scrive, mai risolta né letta da un lockfile, senza dipendenze transitive.
4. `modules.sync_with_premap` allinea `modules.json` alla pre-mappa in una scrittura sola.
5. `modules.json`, `premap.json` e `technologies.json` restano negli stessi percorsi, per CLI, MCP, viewer e benchmark.

**Stack.** Applicato (Scelte, 5); dal fork di stack-analyser ([spec](2026-11-21-stack-dal-fork.md); il processo: [Codebase Map, «Lo step `stack`»](../plugins/codebase-map.md#lo-step-stack)). Prova: `tests/test_codebase_map_stack_rationalized.py`, `tests/test_codebase_map_stack_recognition.py`, `tests/test_codebase_map_stack_sources.py`; README di [`benchmarks/project-model`](../../benchmarks/project-model/README.md), «Lo step `stack` sul corpus» e «Lo step `stack` dal fork».

1. `stack_recognition.run` manda a stack-analyser i fatti della scansione (`packages`, `services`, `docker_builds`) come dichiarazioni, senza rileggere i manifest, lascia fuori `excluded` dal perimetro e dalle prove, e `service_registry.entry_category` dà a ogni voce la sua categoria (framework, libreria, strumento, servizio: [flussi e mappa del sistema](2026-11-18-flussi-e-mappa-del-sistema.md), 5.1).
2. `technologies.json` dà per ogni modulo, anche `logical` e `virtual`, `{id, name, kind, nature, provenance, paths, languages, toolchains, frameworks, libraries, services, tools, technologies}`, più la vista `units` delle unità fisiche e virtuali. `libraries` elenca tutte le librerie che il modulo dichiara: arricchite dall'id e dal nome della tecnologia riconosciuta sullo stesso pacchetto e file, mai tolte se nessuna lo è.
3. Il registro è l'anagrafica, senza segni: la categoria tiene framework ed esecutori dei test separati dai servizi esterni (`registry_build.CATEGORY_OF_TYPE`, le categorie curate delle aggiunte).

**Dinamico.** Un osservatore per tecnologia, un modulo di `dynamic/` che si dichiara (`ENTRY`, `VERSION`, `LANGUAGES`), elencato da `dynamic.observers()`. Parte per le tecnologie che hanno un grafo statico nello store e prende il comando dei test dalla pre-mappa. Una tecnologia senza osservatore, un progetto senza comando dichiarato e una corsa senza motore di container sono lacune: la pipeline arriva comunque a `union`. `DAODAN_DYNAMIC=off` salta lo step.

## 2. Un adattatore per tecnologia trovata

**In uso.** `indexers.analyzers()`; `ENGINES` è derivato dalle dichiarazioni (`engine_pass.py`).

- Ogni adattatore si dichiara (`NAME`, `LANGUAGES`, `UNIT_KINDS`, `NEEDS_CONTAINER`): i linguaggi che indicizza e i tipi di unità della pre-mappa da cui prende la struttura. Le voci del passaggio vanno dal più leggero in memoria al più pesante: uno che esaurisce la memoria ferma quelli dopo.
- Lo step crea un'istanza per ogni tecnologia presente: parte quando lo snapshot ha file dei suoi linguaggi, anche fuori da ogni unità, e prende le sue unità dalla pre-mappa. Un'istanza per tecnologia, non per unità (Scelte, 2).
- Interfaccia comune: `structure(premap)`, `index(...)` e le correzioni opzionali del grafo (`hops`, `same_range`, `classify`, `static`, `refine`, `missing`, `tasks`). Un test impedisce di saltarne una o di cercare file da soli.
- **Uno strumento ufficiale per linguaggio, nessun lettore scritto a mano accanto** (decisione del proprietario). Chi ha bisogno di un fatto del codice lo prende dall'indice che l'adattatore scrive già nel container preparato: nessun secondo programma e nessuna seconda installazione. Motivo: [ingressi e scoperta dei flussi](2026-11-20-ingressi-e-scoperta-dei-flussi.md), motivo 14.
- I fogli di stile sono un adattatore come gli altri (`indexers/css.py`). Vue e Svelte passano da scip-typescript (`indexers/components.py`). `position_stage.py` resta per un indice SCIP dato a mano.

## 3. Listener

**In uso,** tranne `step.skipped` e l'uscita degli strumenti come `log`. Codice: `pipeline/events.py`.

- Un bus di eventi dal primo step al grafo completo. Ogni evento ha la run, lo step, l'adattatore quando c'è, l'ora, un `kind`, un livello (`debug`, `info`, `warning`, `error`), un messaggio da leggere e i dati.
- I `kind`: `step.started`, `step.finished`, `step.failed`, `analyzer.started`, `analyzer.finished`, `analyzer.unavailable` (li emettono anche gli osservatori; diventano `adapter.*`, 8.7), `progress`, `gap`, `log`, `graph.ready`.
- **Avanzamento:** `progress` dice, per lo step e per la run, quante unità sono fatte su quante, e la fase dentro l'adattatore. L'interfaccia mostra la percentuale e che cosa sta facendo, senza parlare di container o volumi.
- **Feedback:** un `warning` o un `error` ha sempre causa e rimedio.
- Un listener si registra con una funzione (`on(event)`) da Python, o legge gli eventi dal servizio MCP con il cursore di `codebase_map_events`. Gli eventi si scrivono nel giornale della run, così un listener che arriva dopo li rilegge. Un listener che fallisce non ferma l'analisi: il suo errore diventa un evento.
- **Mancano:** `step.skipped` (la freschezza la controlla ogni `ensure`, non `_run`: 8.8, punto 2); l'uscita degli strumenti come `log` di livello `debug` (oggi va in un file, `engine_pass._log_tail`), che non è in nessun passo di 8.11.

## Preparazione

**In uso,** con i limiti scritti qui. Ogni comando nel container, della pre-mappa o di un adattatore, ha prima ciò che serve alla CI del progetto: strumenti, toolchain e dipendenze. È uno strato solo del runner del container (`preparation.py`), con la rete verso i registri dei pacchetti e gli host che ogni strumento dichiara, mai altro. Gli strumenti Java ricevono il proxy come proprietà di sistema e Maven anche nelle sue impostazioni (`JAVA_PROXY`).

- **Toolchain:** le versioni che la faccetta `toolchains` dichiara le installa mise, ognuna alla versione scritta: mise non sceglie mai una versione da sé, ed è un pin con sha256 (`MISE`). Una versione che è un intervallo, o uno strumento che mise non installa, è una lacuna `toolchain_unavailable`. **Daodan ha qualunque JDK serva, marca compresa** (decisione del proprietario): una build che fallisce nominando un JDK più nuovo o di un'altra marca non è una lacuna; Daodan lo installa e riprova una volta, nella pre-mappa (`jdk_from_build_error`) e nell'indicizzatore, mai una terza. `gradle/gradle-daemon-jvm.properties` è una dichiarazione: la pre-mappa ne legge versione e marca (`premap/jvm_files.py`); le righe `toolchainUrl` non si scaricano mai. Le marche stanno in `preparation.JDK_VENDORS` (undici con un JDK in mise; AdoptOpenJDK, Apple e HP-UX sono `toolchain_unavailable`). Provato su Modal su due fixture (`benchmarks/project-model/fixtures/_jvm-kotlin-jdk-from-error`, `_jvm-kotlin-daemon-vendor`): Kotlin passa da non indicizzato a `fresh`. Installate davvero solo JetBrains e Temurin; le altre nove marche sono verificate sul catalogo di mise; gli host non sono osservati nel proxy, perché su Modal la rete è aperta. Daodan tiene un proprio pin (`NEEDS`) solo dove mise non ha un backend verificabile: lo strumento di vcpkg e l'Arm GNU Toolchain.
- **Host:** ogni strumento dichiara i suoi in un punto solo, oltre ai registri di `container.REGISTRIES`: mise in `preparation.MISE_HOSTS` e `MISE_OWN`; vcpkg e Conan in `preparation.NEEDS`; Bazel in `premap/container_runner.TOOLS`.
- **Dipendenze:** `preparation.RESTORES`, una riga per gestore: il comando di ripristino che il progetto dichiara, con gli script spenti dove lo strumento lo consente (`vcpkg install` in modalità manifest, `conan install` con il suo lockfile, poi npm, pnpm, yarn, uv, pip, poetry, Go, Cargo, Maven, Gradle, .NET, Composer, Bundler, SwiftPM, pub). Una cartella che fallisce è una lacuna `restore_failed` con gestore, cartella e righe d'errore, e la preparazione va avanti.
- **La ricerca è ricorsiva** (decisione del proprietario): ogni progetto trovato nell'albero, a qualsiasi profondità, riceve il suo ripristino, tranne il membro che la cartella sopra nomina nel suo workspace. Fatto per npm, pnpm e Yarn (fixture `_js-nested-npm-apps` su Modal: nessuna lacuna, TypeScript `fresh`); su un progetto reale con tre app sotto la radice, in una di esse le chiamate senza esito scendono da 5.918 a 1.472. Mancano: una cartella annidata senza lockfile che nessun workspace nomina (`restore_failed`; `lerna.json` non è letto); un crate Cargo annidato con il suo `Cargo.lock`, un progetto .NET annidato e un `requirements.txt` annidato.
- **Compilatori:** un file di toolchain CMake, un file cross di Meson o un profilo Conan che nomina un compilatore noto (`COMPILERS`) lo porta sul path; ogni preset di configure gira. Con due gestori dichiarati (vcpkg e Conan) vince quello che i preset nominano, altrimenti vcpkg, con una lacuna `choice`.
- **Un comando dichiara ciò che gli serve** (`needs`), il runner lo prepara una volta per run. Ciò che non si può installare resta una lacuna che lo nomina.
- **Una preparazione per analisi.** La pipeline riusa il ripristino Node fra `tsc`, scip-typescript e l'osservatore JavaScript quando coincidono checkout, contenuto dei file e lockfile, toolchain, immagine, registri e accesso ai valori dei file `.env`. Ogni strumento copia i volumi preparati in volumi privati (`node_preparation.clone`), rimossi a fine analisi. Un ripristino parziale conserva le lacune e viene ritentato dal consumatore successivo. Prova: `tests/test_codebase_map_shared_node.py` (motore simulato); con un motore vero `tsc` e scip-typescript girano su una fixture Tauri ([`real_paths.py`](../../benchmarks/system-map/real_paths.py)). Su Modal ogni run ripristina per sé: lì la condivisione non si misura. Il guadagno su un progetto Node reale non è misurato.

## 6. Sotto il blocco del progetto nulla aspetta il container

**In uso.** Prova: `tests/test_codebase_map_reactive_server.py`; `tests/test_codebase_map_mcp.py` (`test_events_and_status_follow_the_analysis_pipeline_of_the_run`). I numeri 4 e 5 erano il riordino del codice e il suo ordine di lavoro, fatti o passati a 8.7 e 8.11: non si riusano.

1. Sotto `project_lock` girano solo letture dello snapshot: la scansione veloce (`Context.fast_scan`, senza runner) e lo stack, che lancia stack-analyser sull'host con il Node di Daodan. Il piano 2 dello stack dal fork ha misurato lo stack della veloce, con il rilascio `.2`: mediana 0,523 s, massimo 5,791 s su 178 fixture, contro 0,013 s del registro ([README di project-model](../../benchmarks/project-model/README.md), «Lo step `stack` dal fork»); dopo il passaggio non è misurato. Così fanno `MapService.create_run` e l'aggiornamento dell'hook `PostToolUse` (`snapshot.refresh_working --hook`). Il resto lo fa il processo staccato (`resolve_edges.py --pass`), fuori dal blocco: la scansione, se restano comandi di modello `not_run`, poi stack, analisi, dinamico e unione.
2. `snapshot.py write` da riga di comando fa la scansione intera e lo stack prima di avviare il passaggio del motore.
3. `MapService` dà `stack(run_id, module=None)`; `status(run_id)` dice lo stato degli step della pipeline e del run `working`; `modules(run_id)` porta `nature`, `languages` e `toolchains`; a ogni evento del servizio o aggiornamento dell'hook si registra un impulso (`live-pulse.jsonl`).
4. Il server MCP espone lo strumento `codebase_map_stack`, la risorsa `daodan://project/live` e notifiche di avanzamento e di aggiornamento che non bloccano.
5. Il server dell'interfaccia inoltra `pipeline_after` e `run=working` in `/api/events`, aggiunge `/api/modules`, `/api/stack` e lo stream `/api/stream`, solo da loopback e con il token, chiuso in modo pulito allo spegnimento, e dà `nature`, `languages`, `toolchains`, `frameworks`, `libraries`, `services` e `tools` nelle entità senza aspettare il container.

## 7. Analisi unificata: niente si fa due volte

**In parte:** 7.1 in uso, 7.3 proposta, 7.4 misurata una volta.

**Scopo.** Dato uno snapshot, Daodan produce il grafo più completo che riesce a verificare, nel minor tempo e con il minor consumo di CPU, RAM e disco, a parità di copertura. Pre-mappa, moduli, statico, inferenza e dinamico condividono preparazione e risultati; le interfacce fanno parte del progetto analizzato dall'inizio.

1. **Che cosa si condivide.** Il ripristino Node («Preparazione»). Uno step fresco non si rifà, e un linguaggio già osservato con lo stesso registratore non si osserva di nuovo (`dynamic.run`). Il gestore di un controllo viene dall'indice che l'adattatore scrive già ([interfacce del progetto](2026-11-19-interfacce-del-progetto.md), 6.5). L'esplorazione delle interfacce parte dal container preparato, senza un'installazione sua.
2. **Che cosa si fa ancora più di una volta.**
   - Lo stesso codice è caricato da più programmi in `analyze`: dopo scip-python gira un secondo passaggio di Pyright sullo stesso ambiente (`indexers/python_unbound.py`); dopo scip-typescript il controllore ricostruisce il programma in un altro processo (`indexers/typescript_unbound.js`), e il grafo dei fogli di stile ne costruisce un terzo (`indexers/css_typescript.py`). Ognuno risponde a una domanda diversa; il costo di caricare il programma si paga ogni volta.
   - Lo stato del passaggio è per linguaggio, non per modulo (`engine_pass.py`): un solo modulo cambiato costa il 95% di una corsa da zero (7.4).
   - L'app può partire più volte: come `webServer` dei test Playwright e nell'esplorazione delle interfacce. La corsa del programma del [registro dell'esecuzione](2026-11-19-esecuzione-del-programma.md) sarebbe una terza.
   - L'esplorazione aziona ogni controllo una volta, anche quelli che un test del progetto ha già azionato.
3. **Regole proposte.**
   - **Un indice per unità e tecnologia, letto da tutti:** interfacce, flussi e review. Un secondo programma sullo stesso codice entra solo se riusa il programma già caricato dal primo, oppure con il suo costo misurato e scritto.
   - **Un avvio dell'app per stato dei dati.** Esplorazione e corsa del programma riusano l'avvio dei test quando lo stato lo consente; se un test ha cambiato i dati ripartono da uno stato pulito, dal container preparato, senza un nuovo ripristino.
   - **L'esplorazione lavora sullo scoperto.** Un controllo si può saltare solo quando la traccia dei test identifica lo stesso elemento, lo stesso evento e lo stesso stato osservabile della schermata. Due pulsanti che chiamano lo stesso gestore restano due controlli. L'osservatore dei test Playwright raccoglie già le terne per il documento principale, e il rapporto le conta in `ui_controls` (`observed`, `pending`); gli identificativi valgono solo in quel documento.
   - **Una superficie nuova dichiara** come si riconosce, quali indici riusa e come si osserva in esecuzione: entra nella stessa pipeline, senza una pre-mappa, una build o un'analisi per linguaggio sue.
4. **La misura.** Tre corse sullo stesso progetto: da zero, senza modifiche, dopo una modifica a un solo modulo; per ognuna tempo, ripristini, indicizzazioni, avvii dell'app e, accanto, i collegamenti attesi ritrovati, perché senza quella colonna un costo che scende può voler dire che si è analizzato meno. Fatta una volta, il 24 novembre 2026, su una fixture sintetica: README di [`benchmarks/project-model`](../../benchmarks/project-model/README.md), «Tre corse sullo stesso progetto». CPU, picco di RAM, spazio temporaneo, varianza e un progetto reale non sono misurati.

## 8. La pipeline riordinata: ordine, piano, nomi

*Chiesta dal proprietario il 22 e il 23 novembre 2026 e approvata: i nomi con «sì a tutto», l'ordine e la regola di 8.1 con parole sue. **Stato al 24 novembre 2026:** il codice ha 8.9, i passi 1, 2 e 4 di 8.11, parte dei passi 3 e 5 (pezzi A–D; E1 tolto e F fermo, per le misure: 8.3) e 8.13. Non ha i nomi nuovi (8.7), `plan` come step, la freschezza in un punto solo (8.8) e l'unione di `connect`. Che cosa gira oggi e in che ordine: [Codebase Map, «Oggi nel codice»](../plugins/codebase-map.md#oggi-nel-codice). Dove il testo sotto dice «oggi» senza una data, è il codice del 22 e 23 novembre, prima di quei passi; fanno eccezione le colonne «Oggi nel codice» di 8.2 e «Step oggi» di 8.7, aggiornate al 24 novembre. I fatti sul codice sono letti in quei due giorni in `pipeline/`, `snapshot.py`, `engine_pass.py`, `import_resolution.py`, `technologies.py` e nei contratti di `languages/`, `premap/`, `indexers/` e `dynamic/`, non in ogni adattatore.*

**8.1 La regola.** Ogni step parte da ciò che gli step prima hanno stabilito. **Ogni fatto ha un padrone solo:** uno step non riscopre ciò che un altro stabilisce, lo chiede a lui. Dove il padrone non ha potuto stabilirlo (manca il container), chi ne ha bisogno usa un ripiego e lo scrive accanto al dato.

**8.2 Gli step.** L'ordine viene dalla colonna «Deve sapere prima»: `scan`, `recognize`, `plan`, `parse`, `resolve`, `observe`, `connect`.

| Step | Che cosa fa | Deve sapere prima, e da chi | Che cosa scrive |
| --- | --- | --- | --- |
| 1 `scan` | Percorre tutte le cartelle e i file; chiede agli strumenti di build com'è fatto il progetto | La cartella e il perimetro: da chi avvia l'analisi | L'inventario dei file (percorso, dimensione, hash, linguaggio, motivo di esclusione) e il modello del progetto (moduli, unità, toolchain, pacchetti, comandi di test, servizi, radici e alias degli import) |
| 2 `recognize` | Riconosce framework, librerie, strumenti e servizi | Pacchetti, servizi, immagini e unità: da `scan` | Le tecnologie di ogni modulo |
| 3 `plan` | Decide quale adattatore gira su quale parte, e che cosa gli serve prima | File e linguaggi per modulo: da `scan`. Tecnologie: da `recognize`. Le dichiarazioni degli adattatori | Il piano (8.4) |
| 4 `parse` | Legge i sorgenti | Quali file, in che linguaggio, in quale modulo, con quali letture di framework: dal piano. Radici e alias degli import: da `scan` | Simboli, import e riferimenti di ogni file, e come è andata la sua lettura (letto, escluso, errore, ripiego) |
| 5 `resolve` | Trova dove arriva ogni chiamata | I riferimenti: da `parse`. Unità e build: da `scan`. L'ambiente preparato | Gli archi provati, e i buchi per classe |
| 6 `observe` | Esegue i test e registra che cosa chiamano; avvia l'app che il progetto dichiara e ne preme i controlli in un browser | I comandi di test, di avvio e di build: da `scan`. I riferimenti: da `parse`. Il grafo statico del linguaggio e i suoi buchi: da `resolve`. L'ambiente preparato | Gli archi osservati, i campionati a parte; i controlli premuti, con le funzioni del progetto che hanno fatto girare |
| 7 `connect` | Unisce, e dice che cosa manca | Tutto | Il grafo completo: gli archi fra moduli, gli ingressi dei flussi uniti alle loro definizioni, l'osservato contro il provato, e le lacune |

| Step | Adattatore | Strumento sotto | Oggi nel codice |
| --- | --- | --- | --- |
| 1 `scan` | scanner | Il percorso dell'albero (`tree_scope.py`); go-enry; cargo, gradle, maven, npm, `tsc`, cmake, … | Lo step `scan` c'è; l'inventario lo scrive lo snapshot, prima della pipeline |
| 2 `recognize` | recognizer | stack-analyser, il fork ([spec del 21 novembre](2026-11-21-stack-dal-fork.md)) | Step `stack`, con il fork (`stack_recognition.py`); legge solo i fatti dello step 1 e i file che il fork legge da sé |
| 3 `plan` | nessuno | — | Una funzione, non uno step (`pipeline/plan.py`; 8.11, passo 4): la chiamano la lettura, `engine_pass.pass_plan` e il passo dinamico; lo step `parse` la emette come evento |
| 4 `parse` | parser | tree-sitter, `ast` di Python; SQL e PL/SQL ancora con espressioni regolari (`languages/sql.py`, `plsql.py`) | Step `parse`, terzo in `STEPS` (8.11, passi 3 e 5); ogni chiamante legge ancora prima, con `write_snapshot`, e lo step trova lo store letto |
| 5 `resolve` | resolver | Un indicizzatore SCIP per tecnologia (scip-typescript serve quattro linguaggi); per i fogli di stile i loro parser | Step `analyze` |
| 6 `observe` | observer | Un registratore per linguaggio (`*_record.*`); per l'app, Chromium senza interfaccia di Playwright (`dynamic/app.py`, `explore.cjs`) | Step `dynamic`; senza grafo statico non parte (`no-static-graph`); l'app si avvia solo con npm (`start_runner_not_supported` per pnpm, Yarn e Bun) |
| 7 `connect` | nessuno | — | Step `union`: dice ciò che il grafo ha e non ha, non unisce ancora |

Perché `recognize` e `plan` stanno prima di `parse`: `recognize` non legge nulla di ciò che `parse` produce (`technologies.py`: solo i fatti dello step 1), mentre `parse` deve sapere che cosa leggere e come. Perché gli archi fra moduli e gli ingressi dei flussi stanno in `connect`: uniscono ciò che `parse` legge a ciò che `scan` stabilisce, e cambiano quando cambia uno dei due; in `parse`, a un modulo che lo strumento di build corregge dopo si dovrebbero rileggere file che non sono cambiati. Fino al 23 novembre li scriveva lo step `scan` (`module_derive`, `premap/flow_entries.py`), perché girava dopo la lettura; ora gli archi li aggiunge il primo lettore del grafo intero (`modules.ensure_graph`, anche lo step `union`) e il legame lo fanno i collegamenti (`binder.bind`): 8.11, passo 5, pezzi A e B.

**8.3 Che cosa `parse` smette di scoprire da sé.** *Stato al 24 novembre 2026: il punto 1 è fatto (8.11, passo 2). Del punto 2 il linguaggio è dell'inventario, che lo decide ancora con estensione e contenuto (`file_inventory.write`), non con go-enry. Il punto 3 è tolto (deciso il 24 novembre, sotto). Il punto 4 resta. Il testo sotto descrive il codice del 22 novembre.* Oggi gira per primo, e stabilisce da solo quattro fatti che non sono suoi:

1. **Quali file ci sono.** Fatto: li riceve dall'inventario, non percorre l'albero.
2. **Il linguaggio di un file.** Fatto a metà: la lettura non sceglie il linguaggio, ma l'inventario lo dà ancora per estensione, più espressioni regolari sul contenuto per `.h`, `.ts` e `.sql` (`languages.detect_language`). Da fare: il linguaggio da go-enry, con l'estensione come ripiego dichiarato.
3. **Quali file lasciare fuori.** Fatto sul percorso inventario → pipeline (8.11, pezzo E1); `write_snapshot`, che ogni chiamante usa ancora, legge come prima.
4. **La configurazione degli import.** Da fare: oggi legge `tsconfig`, `jsconfig` e i workspace a mano (`import_resolution.py`); diventa: radici e alias da `tsc`, la lettura a mano come ripiego dove `tsc` non è girato.

**Scelte del 24 novembre 2026, dopo le misure di 8.10.** Criterio del proprietario: meno codice nostro possibile, e dati da sorgenti aggiornate. Le misure sono in [`benchmarks/project-model`](../../benchmarks/project-model/README.md).

| Punto | Che cosa si fa | Chi l'ha deciso | Perché |
| --- | --- | --- | --- |
| 2, il linguaggio | Verrà da una libreria nostra, con il catalogo di Linguist come punto di partenza ([spec](2026-11-24-libreria-del-linguaggio.md)). **Nel prodotto oggi non c'è nulla:** resta `languages.detect_language` | Proprietario | go-enry gira nel container, dopo la lettura: la nostra tabella sarebbe rimasta come ripiego. Su 47.543 file i due linguaggi divergono in 87. Un primo lettore dei soli dati di Linguist, provato e non entrato: leggeva come C 95 header C++ su 6.857 e perdeva 8 `.ts` su 47.999 |
| 3, quali file lasciare fuori | `parse` non esclude nulla: l'esclusione resta l'etichetta `excluded` della pre-mappa. E1 è tolto | Proprietario («C») | I predicati di Linguist rispondono a «conta nelle statistiche», non a «non è codice del progetto»: su 56 progetti veri toglierebbero 1.496 file letti, verso cui vanno 96 import (`CTFd/cache/__init__.py`, importato da 45 file) |
| La lettura dentro lo step `parse` | Tolta: l'unica lettura è `write_snapshot`. Lo step dice solo il piano, e uno store di solo inventario ferma la pipeline | Proprietario («C») | Nessun chiamante la usava |
| 4, la configurazione degli import | Ferma: resta la lettura a mano | Chi scrive | Sui 25 progetti veri la configurazione di `tsc` guadagna 0 import e ne perde 110. Da rivalutare un risolutore pronto (`ts.resolveModuleName`, oxc-resolver) solo se riduce il codice |
| I chiamanti verso «inventario + pipeline» | Fermi | Chi scrive | Con E1 e la lettura in `parse` tolti, non cambia nulla per il prodotto, e `create_run` e l'hook leggerebbero sotto il blocco del progetto |

**8.4 Il piano.** Una funzione sola, dall'inventario, dal modello del progetto, dalle tecnologie e dalle dichiarazioni degli adattatori. Non stabilisce fatti sul progetto: solo scelte.

- **Un nodo** è un adattatore sulle sue unità o sui suoi file: lo step, l'adattatore con la versione, su che cosa gira, se chiede il container, di quali altri nodi ha bisogno. **Una lacuna** è ciò che nessun adattatore serve, con la causa.
- **I bisogni fanno il grafo.** Un resolver ha bisogno del parser del suo linguaggio; un observer del resolver. La preparazione (toolchain e dipendenze nel container, «Preparazione») è un nodo, fatto una volta per analisi, di cui hanno bisogno gli strumenti di build di `scan`, i resolver e gli observer: non è uno step.
- **Un nodo il cui bisogno è fallito non parte,** e dice quale. Il 22 novembre lo facevano due casi, ognuno a modo suo (dal 23 lo dice il piano, `plan.blocked` e `plan.need`: 8.11, passo 4): un linguaggio che la lettura non ha letto lascia il suo analyzer `unavailable` (`engine_pass.run_pass`), e un linguaggio senza grafo statico non ha osservatore (`no-static-graph`).
- **Ogni file dell'inventario è in un nodo di `parse` o ha un motivo di esclusione.** Nessun adattatore gira fuori dal piano.
- **Si ricalcola quando un fatto cambia,** e rifà solo i nodi che leggono quel fatto (8.8).
- È il risultato dello step e un suo evento. Un file a parte entra quando l'interfaccia mostra il piano prima che l'analisi parta.

Gli step restano una lista ordinata; dentro uno step i nodi girano nell'ordine del piano. Nessun motore generico di grafi e nessun sistema di plugin.

**8.5 Le due parti di `scan` e la prima analisi.** La prima parte gira sull'host, subito: l'albero, il linguaggio per estensione, i lettori dei file. La seconda gira nel container: gli strumenti di build, go-enry, `tsc` (Scelte, 1). L'obiettivo fissato dal proprietario: alla fine dell'analisi il grafo è quello di un `parse` che ha lavorato sui file, i linguaggi e i moduli che `scan` ha stabilito per intero, comunque ci si arrivi.

**Scelta di chi scrive:** alla prima analisi `parse` parte dopo la prima parte, mentre la seconda gira; la mappa resta utilizzabile subito e la sezione 6 resta com'è. Quando la seconda parte corregge un fatto, si rifà solo ciò che lo legge:

| La seconda parte corregge | Si rifà |
| --- | --- |
| Il linguaggio di un file, o la sua esclusione | La lettura di quel file |
| Radici e alias degli import | La risoluzione degli import, senza rileggere |
| I file di un modulo | Gli archi fra moduli, in `connect` |
| Le unità di una tecnologia | I nodi di `resolve` e `observe` di quella tecnologia |

Vincolo: il risultato finale è uguale a quello che si avrebbe aspettando tutto `scan`, e un test li confronta (8.10, prova 2). Senza container la seconda parte è una lacuna (`model_not_run`) e i ripieghi di 8.3 restano il dato, dichiarati.

**8.6 Lo snapshot si divide.**

1. **Due scritture sullo stesso store.** L'inventario scrive di ogni file percorso, dimensione, data, hash, linguaggio e motivo di esclusione; `parse` aggiunge simboli, import e riferimenti. *Fatto:* `file_inventory.write`, `snapshot.write_reading`, la tabella `inventory` dello store. `write_snapshot` resta la chiamata di tutti i chiamanti: l'inventario va in un file di appoggio accanto allo store, poi la lettura pubblica una volta sola.
2. **Due impronte.** Quella dell'inventario lega ciò che legge solo l'inventario; `logical_digest` continua a legare ciò che legge i simboli. *Fatto per pre-mappa, struttura del grafo dei moduli e tecnologie* (`snapshot_store.inventory_digest`, 8.11 pezzo C).
3. **Uno store con l'inventario e senza simboli lo dice** (`reading: "not-started"` nell'header). Chi cerca un simbolo riceve «la lettura è in corso» o «non è partita», mai un risultato vuoto. *Fatto.*
4. **Il riuso resta dov'è utile.** *Fatto per `parse`,* che rilegge solo i file che non copia in blocco dallo snapshot di prima. L'inventario legge e calcola l'hash di ogni file: riusare per dimensione e data salterebbe un file cambiato con la stessa dimensione e la stessa data, e si decide con la misura del punto 6.
5. **Le uscite non cambiano:** sullo stesso albero lo store dopo inventario e lettura ha lo stesso `logical_digest` del passaggio solo. *Fatto:* prova 1.
6. **Da misurare prima di scegliere come.** Il contenuto di un sorgente si legge due volte, per l'hash e per la lettura: il tempo sul corpus dice se l'inventario deve passare i byte a `parse`.

**8.7 Nomi.** Regola: uno step è un verbo che dice ciò che Daodan fa; l'adattatore che lo serve è il nome d'agente di quel verbo; **adattatore** è la parola per tutti; una parola per concetto. *Fatto solo `NAME` in `indexers/`.*

| Step oggi | Step | Adattatore | Cartella oggi → nuova |
| --- | --- | --- | --- |
| `scan`, più l'inventario di `snapshot.py write` | `scan` | scanner | `premap/` → `scanners/` |
| `stack` | `recognize` | recognizer | `stack_analyser.py` |
| manca come step; la funzione è `pipeline/plan.py` | `plan` | nessuno | `pipeline/` |
| `parse`, più la lettura di `write_snapshot` | `parse` | parser | `languages/` → `parsers/` |
| `analyze` | `resolve` | resolver | `indexers/` → `resolvers/` |
| `dynamic` | `observe` | observer | `dynamic/` → `observers/` |
| `union` | `connect` | nessuno | `pipeline/` |

| Parola oggi | Problema | Proposta |
| --- | --- | --- |
| `engine` | Tre cose: il motore di container (`container.find_engine`), i modelli a cui l'app dà un compito (`engines.py`), il passaggio degli indicizzatori (`engine_pass.py`, `EngineSpec`, `engine-edges.sqlite`, `engine-report.json`) | `engine` resta solo al motore di container; il passaggio prende i nomi di `resolve`; i modelli diventano `reasoner` |
| analyzer, indexer, adapter | Tre parole per l'adattatore di `analyze` | resolver |
| `resolver` (colonna dello store) | Nomina chiunque abbia prodotto un arco: un resolver, un observer, il resolver lessicale | `producer` al prossimo cambio di schema; fino ad allora resta |
| `analyzer.started`, `.finished`, `.unavailable` | Li emettono anche gli osservatori | `adapter.started`, `.finished`, `.unavailable`, con il campo `adapter` |
| source (in `premap/`) | Si confonde con il sorgente del progetto | scanner; il grado `scanner` di `RANKS` (go-enry, noir) diventa `detector` |
| premap, pre-map | Due grafie; dice quando viene, non che cosa è | project model, già il nome di `benchmarks/project-model` |
| `ENTRY`, `NAME` | Due parole per il nome di un adattatore | `NAME`: fatto per `indexers/`, `dynamic/` aspetta |
| step, stage, phase, pass | Quattro livelli senza una regola scritta | `step` della pipeline; `stage` un adattatore sulle sue unità, il nodo del piano; `phase` dentro uno stage; `pass` da confrontare con `run` |

**Costo e limiti.** I nomi degli step e degli eventi sono letti da `mcp_service.py`, dall'interfaccia in `daodan/assets/app/` e dai test; i nomi sul disco (`premap.json`, `engine-edges.sqlite`, `engine-report.json`) da CLI, MCP, viewer e benchmark. Il cambio entra una famiglia per volta, con le uscite uguali; i nomi sul disco cambiano solo con un cambio di schema, da decidere. Quanti punti del codice tocca non è contato.

**8.8 Dichiarazione comune e controlli dell'orchestratore.**

1. **Una dichiarazione per ogni adattatore:** `NAME` e `VERSION`, più ciò che serve alla sua famiglia (`LANGUAGES`, `UNIT_KINDS`, `NEEDS_CONTAINER`, `RANK`). Oggi `premap/` dichiara `NAME`, `VERSION`, `RANK` in una lista scritta (`SOURCES`); `indexers/` `NAME`, `LANGUAGES`, `UNIT_KINDS`, `NEEDS_CONTAINER`; `dynamic/` `ENTRY`, `VERSION`, `LANGUAGES`; `languages/` `language`, scelto dall'estensione. L'ordine di `SOURCES` porta significato (una fonte legge ciò che le precedenti dichiarano; fra pari vince la prima): resta scritto, o diventa un bisogno dichiarato come quelli del piano. Aperto.
2. **La freschezza si controlla in un punto solo,** `pipeline._run`, sull'impronta degli ingressi dichiarati. *Da fare:* oggi `_run` non la controlla e non emette `step.skipped`; ogni step chiama il suo `ensure`.
3. **Un test controlla gli ingressi:** ogni ingresso di uno step è l'uscita di uno step prima, o un ingresso della pipeline. *Fatto:* prova 6.

**8.9 Solidità del processo.** **In uso.** Prova: `tests/test_codebase_map_pipeline.py`.

1. Un giornale che non si può scrivere (disco pieno, permessi) non ferma l'analisi: i listener lo sanno una volta, con causa e rimedio, e gli eventi continuano ad arrivare loro.
2. Una riga rotta del giornale conta nel cursore e si salta. Ogni evento è una scrittura sola, così le righe di due processi non si mescolano.
3. Un programma di stage che non parte, o un rapporto di stage che non è un oggetto, fa fallire quello stage: gli altri girano.
4. Uno step tollerato che fallisce porta `failed` con la causa nel suo `step.finished`.
5. La lacuna «nessun arco osservato» dice la causa anche quando lo step dinamico fallisce o non gira.
6. Un `start` o `stop` che non nomina uno step è rifiutato prima di ogni evento, con i nomi validi.
7. Un'analisi interrotta chiude i suoi step nel giornale: lo step stesso su un'interruzione; `stop_pass` e `reset_pass` dopo aver chiuso il passaggio; `ensure_edges` prima di avviarne uno nuovo, per quello morto senza una parola (`events.close_open`). Limite: chi chiude non distingue uno step di un'altra analisi che gira nello stesso momento sullo stesso snapshot.
8. Il rapporto del passaggio tiene la durata di ogni stage (`engines.<nome>.seconds`).

Aperto:

- **Uno stage non ha un limite di tempo suo** (`_launch`): un indicizzatore che non risponde ferma l'analisi finché qualcuno non la interrompe. Serve un limite dichiarato da ogni adattatore accanto a `MIN_FREE`, preso dalle durate registrate sul corpus. Da leggere prima: che cosa resta del container di uno stage chiuso da fuori.
- **Il giornale cresce a ogni analisi dello stesso snapshot** e `events.read` lo scorre dall'inizio: il cursore è un numero di righe, parte del contratto di MCP. Un cursore in byte lo toglierebbe, cambiando quel contratto.

**8.10 Prove.** Ogni prova resta nel repository. Scritte la 1, la 3, la 4 e la 6.

1. **Lo snapshot diviso dà lo stesso store:** `tests/test_codebase_map_snapshot_split.py`, sulle 27 fixture di `code-graph`, `css-graph` e `clang-reader`, contro `snapshot.build_manifest`. Lo step `parse` ha la sua prova in `tests/test_codebase_map_pipeline.py`.
2. **Le due modalità danno lo stesso grafo** (8.5): su una fixture con un file che go-enry dichiara generato e un alias di `tsconfig`. *Non scritta.*
3. **Il piano copre tutto:** ogni file dell'inventario è in un nodo di `parse` o ha un motivo di esclusione; nessun adattatore parte senza il suo nodo. `tests/test_codebase_map_plan.py`.
4. **Un bisogno fallito ferma solo chi ne ha bisogno.** `tests/test_codebase_map_plan.py`.
5. **Un ripiego è dichiarato:** senza container, il linguaggio di un `.h` e gli alias di un `tsconfig` portano scritto che vengono dal ripiego. *Non scritta.*
6. **Gli ingressi degli step:** `tests/test_codebase_map_pipeline.py`; uno step fuori posto rende il test rosso.

Misure da fare, su Modal con gli strumenti veri, nel README di [`benchmarks/project-model`](../../benchmarks/project-model/README.md): il tempo della doppia lettura (8.6, punto 6); il tempo di una prima analisi nelle due modalità; quanti file la lettura di oggi legge e `scan` poi esclude.

**8.11 Ordine del lavoro.** Ogni passo lascia i test verdi e le uscite uguali, controllate con le registrazioni dei 122 progetti (`benchmarks/project-model/tools/premap_replay.py`) e con le fixture del grafo.

1. `write_snapshot` in due scritture: fatto (8.6).
2. La lettura prende file e linguaggio dall'inventario: fatto. Un file cambiato fra le due scritture è letto com'è, e la sua riga dell'inventario si corregge.
3. La lettura diventa lo step `parse`: fatto. `parse` legge uno store che ha solo l'inventario. L'inventario entra davvero in `scan` quando la pipeline riceve la cartella: oggi i chiamanti le danno ancora lo store di `write_snapshot`.
4. La funzione del piano: fatto (8.4).
5. `parse` prende da `scan` linguaggio, esclusioni e configurazione degli import, con i ripieghi dichiarati; archi fra moduli e ingressi dei flussi passano a `connect`. In parte:
   - **A, fatto:** gli archi `imports` e `calls` fra moduli escono da `scan`. Li aggiunge il primo lettore del grafo intero (`modules.ensure_graph`, anche lo step `union`).
   - **B, fatto:** nessuna sorgente della pre-mappa legge simboli. Il legame al simbolo si fa nei collegamenti: `binder.bind`, `angular.bind`, `flow_entries.evidence`.
   - **C, fatto:** pre-mappa, struttura del grafo dei moduli e tecnologie si legano all'impronta dell'inventario.
   - **D, fatto:** gli step sono `scan, stack, parse, …`; `scan` e `stack` leggono le righe dell'inventario e su uno store di solo inventario scrivono ciò che scrivono su uno letto (`tests/test_codebase_map_scan_before_parse.py`). Da misurare su Modal: in un progetto Angular `scan` legge l'albero di ogni file TypeScript, prima solo dei file che importavano `Component`.
   - **E1, tolto il 24 novembre 2026** (decisione del proprietario, 8.3): escludeva dalla lettura i file della faccia `excluded` della pre-mappa; nessun chiamante l'ha mai usato.
   - **F0, misurato:** i `paths` di `tsc` registrati contro `import_resolution.ts_path_config`, sulle 11 fixture con albero: 5 coppie unità-pattern uguali, 4 che Daodan non vede, 0 diverse, 0 in più (README di [`benchmarks/project-model`](../../benchmarks/project-model/README.md), «I percorsi TypeScript di Daodan contro `tsc`»). **F, fermo** (8.3): sui progetti veri la configurazione di `tsc` non guadagna import.
   - **Misurato su Modal il 24 novembre 2026,** da un clone pulito di `76f1e2aa9` con un'analisi fresca: phazly 15/38 flussi chiusi e 105/240 frecce certe (base 15 e 104); Kotlin fallito come nella corsa di base (build Android).
   - **Restano:** la sorgente Flask, che lega ancora i gestori ai simboli quando legge la risposta del comando; le prove 2 e 5. Fermi per le scelte del 24 novembre (8.3): i chiamanti verso «inventario + pipeline», la configurazione degli import da `tsc`.
6. I nomi, una famiglia per volta (8.7), e la dichiarazione comune (8.8).

Il recognizer entra con il passaggio al fork, nella sua spec: lo step `stack` riconosce solo con stack-analyser.

**8.12 Non letto.** Se le fonti della pre-mappa che guardano un framework (`noir`, `nextjs`) siano lavoro che dipende da `recognize`, e vadano quindi nel piano. Che cosa resta del container di uno stage chiuso da fuori (8.9). `pass` contro `run`. Quanti punti del codice tocca la rinomina.

**8.13 Il formato comune degli adattatori di ingressi.** **In uso** per le sorgenti di `premap.FRAMEWORK_SOURCES` (`nextjs`, `react_router`, `nuxt`, `sveltekit`) e `TEMPLATE_SOURCES` (`angular`, `astro`), accanto a `noir`. Chiesto dal proprietario: «un adapter che riesca ad adattare l'output di ogni strumento in un formato unico e condiviso in tutto Daodan».

**Scelta di chi scrive:** il formato comune vale per la famiglia delle sorgenti di ingressi. Le altre famiglie hanno già la loro uscita nello store (simboli, import, archi), e un formato unico fra famiglie sarebbe un sistema di plugin, che 8.4 esclude.

1. **Una riga.** L'adattatore dà `{"facts": {"framework_entries": [righe]}, "gaps": [...]}`. I campi: `reader` e `shape`; `kind`; `site` e `symbol`; `path` e `schema` (il percorso nello schema `{}` di `REST`: ogni adattatore traduce l'ortografia del suo strumento, un catch-all non ha schema); `method` (solo il metodo che lo strumento dà alla riga: una pagina non ne ha); `exports` o `methods`; `handler` con `site:riga`; `handler_source`; `page` (la riga è una pagina da aprire). `schema` e `page` li scrivono oggi solo Next.js e Noir.
2. **Nessun adattatore lega una riga a una funzione dello snapshot.** Lo fa un binder solo (`binder.bind`, chiamato da `flows.link_facts` e da `entries._declared_rows`), su due forme: il nome di un'esportazione in un file e un nome a una posizione dentro una dichiarazione. Ciò che non si riduce a una delle due resta nel suo adattatore, con scritto accanto perché: l'`export default defineEventHandler(...)` di Nuxt, `this.save()` e `svc.cancel()` di Angular, Astro. Prova: `tests/test_codebase_map_entry_binder.py`, con una sorgente finta aggiunta alla tupla senza una riga modificata fuori dal suo file.
3. **Una tupla e una dichiarazione.** Le tuple di `premap` elencano le sorgenti che danno righe; la chiave dei collegamenti in cache si ricava da lì.
4. **La lettura dell'uscita di uno strumento sta nel suo adattatore** (`premap/noir.rows`, `nuxt.nitro_routes`, `nextjs.typegen`); gli aiutanti comuni in `premap/frameworks.py`. Prova: `tests/test_codebase_map_premap_frameworks.py`.
5. **Le lacune non si unificano.** L'adattatore dà la forma della pre-mappa (`kind`, `path`, `detail`, `source`) e una stringa `gap` sulla riga; il binder dà la forma dei collegamenti (`site`, `symbol`, `reason`).

Aperto: le sorgenti di Flask, FastAPI e Django sono scritte e fuori dalle tuple ([ingressi e scoperta dei flussi](2026-11-20-ingressi-e-scoperta-dei-flussi.md), «Le rotte che nascono all'avvio»); un default anonimo (`export default function () {}`) si legge come `export-missing` e sparisce senza lacuna; `handler_source` vale due cose, il nome dell'adattatore e un modo (`inline`, `classe`, `locale`); il nome di un simbolo si costruisce in tre modi (`Facts.node`, `_starts`, Angular) e per un'esportazione anonima possono divergere (dedotto, non provato); una lacuna su una riga senza regola, o di tipo «nessun ingresso», sembra sparire da `links["gaps"]` (dedotto, da provare); chi assorbe chi fra Noir e Next lo decide il grado `detector` di 8.7, e oggi hanno lo stesso grado.

## Scelte

1. **La scansione resta intera.** `scan` comprende i comandi di modello della pre-mappa (Renovate, npm, Go, Cargo, uv, tsc), nel container. Misurato sui 122 progetti il 15 novembre 2026: la pre-mappa dura 5 s di mediana e 103 s al massimo, Renovate 4,8 s di mediana; un indicizzatore dura minuti. Spostarli negli adattatori dividerebbe la struttura del progetto fra due step. `scan` emette avanzamento per fonte.
2. **Un'istanza per tecnologia, non per unità.** Le unità della stessa tecnologia condividono strumenti e dipendenze, e un container per unità costerebbe il tempo fisso ogni volta.
3. **`union` dice ciò che `dynamic` ha osservato.** Per ogni tecnologia con archi osservati: quanti siti e quanti buchi chiusi, quelli campionati a parte; come lacune, i test che non sono arrivati in fondo, i file con chiamate che nessun test ha eseguito e gli archi osservati che contraddicono un arco provato. Una tecnologia senza archi osservati resta una lacuna, con la causa.
4. **Una mappa dei moduli sola** (sezione 1; decisione del proprietario). Perché: `modules.json`, `premap.json` e `technologies.json` davano unità e tipi diversi; i file fuori da ogni manifest restavano senza modulo (17 fixture su 140 del corpus; il numero non ha una misura che lo rifà) e né linguaggi né toolchain erano del singolo modulo. Scartato: tre modelli di modulo affiancati.
5. **Lo stack dai fatti della scansione** (sezione 1; decisione del proprietario). Perché: `service_registry.py` e `system_brief.py` rileggevano `Dockerfile`, `compose*.yml` e `requirements*.txt` con espressioni regolari, ignoravano cinque ecosistemi e confondevano framework ed esecutori dei test con servizi esterni. Misure prima e dopo: README di `benchmarks/project-model`, «Lo step `stack` sul corpus». Scartato: rileggere i file nello stack.
6. **Sotto il blocco del progetto nulla aspetta il container** (sezione 6; decisione del proprietario). Perché: l'aggiornamento dell'hook eseguiva la pipeline fino alla scansione con il runner del container dentro `project_lock`, e bloccava `MapService`, l'interfaccia e gli strumenti MCP. Scartato: aspettare il container sotto il blocco.
7. **Il container su Modal e una preparazione per analisi** (decisioni del proprietario). Perché: le misure di `benchmarks/system-map` su Modal giravano senza container (limite 10), e un progetto Node ripristinava le dipendenze tre volte (`tsc`, scip-typescript, l'osservatore). Scartato: restare senza container per il costo delle Sandbox. Prova: `engine-report.json` con scip-typescript `fresh` su `js-vite-react-ts`; per la condivisione, il motore simulato conta tre consumatori e un ripristino. Manca la prova reale del guadagno.

## Limiti delle prove

I numeri sono quelli di «Assunzioni e limiti noti» della [spec dei flussi e della mappa del sistema](2026-11-18-flussi-e-mappa-del-sistema.md).

- **10.** **Senza container.** Le misure di `benchmarks/system-map` su Modal precedenti al 23 novembre 2026 sono girate senza motore di container: scip-typescript `unavailable`, nessun passo dinamico, nessun collegamento osservato. Sono misure del solo statico, su albero nudo: i buchi che dichiarano non sono misurati dopo `analyze` con l'indice né dopo il passo dinamico. Dal 23 novembre la run della mappa su Modal ha il container (README di [`benchmarks/system-map`](../../benchmarks/system-map/README.md), «Il container nella run della mappa su Modal»); quante frecce mancanti dei flussi chiuda il passo dinamico non è misurato su nessun caso con riferimento.
- **20.** **Il container su Modal non è quello di Daodan:** nella sandbox la preparazione ha la rete aperta ai soli `registries` della run, per host, senza il proxy di Daodan; con i servizi tiene tutta la rete e il risultato lo dice (`network_open`) (`benchmarks/project-model/modal_pipeline.py`). Una prova su Modal non prova il confine del proxy.

## Da decidere

- **Aperta: da approfondire: review a strati contro il modello da solo.** La questione del proprietario è una review in cui il modello riceve pacchetti sempre più dettagliati costruiti dal grafo, contro il modello che legge il codice da solo: sta in [ricerca dei flussi e pacchetto di una review](2026-11-20-ricerca-e-pacchetto-di-review.md), «Decisioni aperte», con l'unica misura in [flussi nella review](2026-11-09-flows-in-review.md). Non è il confronto sulla mappa del sistema del README di `benchmarks/system-map` («Grafo contro modello»). Da questa spec dipende ciò che i pacchetti possono contenere: il grafo dopo l'ultimo passo («L'analisi è l'intera catena»).
- **Aperta: da approfondire: gli strati non sono incrementali.** Un modulo cambiato costa il 95% di una corsa da zero (7.4): lo stato del passaggio è per linguaggio, non per modulo.
- **Aperta: da approfondire: U2, le regole di 7.3.** La misura delle tre corse c'è (7.4): dice quanto costa oggi ogni doppione su una fixture sintetica; la decisione non è presa.
- **3.** La prova 0 sui cinque casi di `benchmarks/system-map`, dopo il via del proprietario con il costo stimato (piano del 20 novembre, task 2).
- **A1.** I nomi della sezione 8 sono approvati, anche `reasoner`. Restano aperte le scelte che non sono un sì o un no: l'ordine di `SOURCES` (8.8), `pass` contro `run`, quando cambiano i nomi sul disco, il nome `producer`, il limite di tempo di uno stage e la dimensione del giornale (8.9).
- **U1, deciso: no.** Non tutta l'analisi nel container: snapshot, stack e unione leggono il progetto e non lo eseguono, restano sull'host; così vale la sezione 6 e l'uso senza motore di container, dove Daodan dà comunque snapshot e grafo statico con le lacune.
- Le decisioni sulle superfici (osservare le interfacce desktop Python, il ponte Tauri) sono in [interfacce del progetto](2026-11-19-interfacce-del-progetto.md), «Da decidere».
