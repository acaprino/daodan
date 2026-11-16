# Pipeline di analisi: step, analyzer con adattatori, listener

**Stato:** approvata dal proprietario il 15 novembre 2026, che ha lasciato a Claude le scelte rimaste (sezione «Scelte»). Lo step 3 è applicato (`pipeline.Dynamic`, `dynamic/`), con gli osservatori di Python e Go; gli altri sono in corso.

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
| 2. Analisi | Un analyzer per ogni tecnologia della pre-mappa, ognuno con le sue unità | Una voce per tecnologia nello store dei collegamenti |
| 3. Dinamico | I test nel container; ciò che si osserva entra nel grafo della sua tecnologia | Archi osservati, i campionati a parte |
| 4. Unione | I grafi delle tecnologie in uno solo, ai punti di connessione (rotte, chiamate HTTP, eventi, tabelle) | Il grafo completo |

La pipeline finisce con il grafo completo; i flussi lo leggono dopo, fuori da essa. Un modulo `pipeline` elenca gli step in ordine; ogni step ha lo stesso contratto: `inputs` (ciò che legge), `run(context)`, `outputs` (ciò che scrive). Uno step è fresco quando i suoi ingressi non sono cambiati: lo stesso controllo per impronta che pre-mappa e store usano già, scritto una volta. Lo step 3 segue il disegno del [passo dinamico](2026-11-12-passo-dinamico.md) ed è applicato (`pipeline.Dynamic`, `dynamic/`); lo step 4 entra con il disegno dei punti di connessione (`benchmarks/connection-points/`).

Lo step 3 ha un osservatore per tecnologia, con lo stesso pattern degli analyzer: un modulo di `dynamic/` che si dichiara (`ENTRY`, `VERSION`, `LANGUAGES`), elencato da `dynamic.observers()`. Parte per le tecnologie che hanno un grafo statico nello store, prende il comando dei test dalla pre-mappa e usa gli eventi degli analyzer (`analyzer.started`, `progress`, `gap`, `analyzer.finished`, `analyzer.unavailable`). Una tecnologia senza osservatore, un progetto senza un comando dichiarato e una corsa senza motore di container sono lacune: la pipeline arriva comunque all'unione. `DAODAN_DYNAMIC=off` salta lo step.

### 2. Analyzer: un'istanza per tecnologia trovata

- Ogni adattatore si dichiara da solo (`ENTRY`, `LANGUAGES`, `UNIT_KINDS`, `NEEDS_CONTAINER`): i linguaggi che indicizza e i tipi di unità della pre-mappa da cui prende la struttura (`go-module`, `gradle-project`, `cmake-target`, …). Le voci del passaggio si costruiscono da queste dichiarazioni (`indexers.analyzers`), dal più leggero in memoria al più pesante: uno che esaurisce la memoria ferma quelli dopo.
- Lo step 2 crea un'istanza per ogni tecnologia presente: parte quando lo snapshot ha file dei suoi linguaggi, anche fuori da ogni unità (il codice senza file di build non si perde), e prende le sue unità dalla pre-mappa.
- Interfaccia comune: `structure(premap)`, `index(...)`, le correzioni del grafo opzionali di oggi (`hops`, `same_range`, `classify`, `static`, `refine`, `missing`, `tasks`).
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

## Scelte

1. **La scansione resta intera.** Lo step 1 comprende i comandi di modello della pre-mappa (Renovate, npm, Go, Cargo, uv, tsc), nel container. Misurato sui 122 progetti il 15 novembre 2026: la pre-mappa dura 5 s di mediana e 103 s al massimo, Renovate 4,8 s di mediana; un indicizzatore dura minuti. Spostarli negli analyzer dividerebbe la struttura del progetto fra due step e farebbe cambiare la pre-mappa a chi la legge. Lo step 1 emette avanzamento per fonte: chi guarda vede i lettori finire subito e i comandi dopo.
2. **Un'istanza per tecnologia, non per unità.** Un analyzer riceve tutte le unità della sua tecnologia e decide come girarle (una build per cartella, un configure per unità): le unità della stessa tecnologia condividono strumenti e dipendenze, e un container per unità costerebbe il tempo fisso ogni volta.
3. **Lo step 4 dice ciò che il 3 ha osservato.** Per ogni tecnologia con archi osservati: quanti siti e quanti buchi chiusi, quelli campionati a parte; come lacune, i test che non sono arrivati in fondo, i file con chiamate che nessun test ha eseguito e gli archi osservati che contraddicono un arco provato. Una tecnologia senza archi osservati resta una lacuna, con la causa che lo step 3 ha dato.
