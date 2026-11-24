# Piano: il grafo del codice dall'indice del progetto

**Stato:** In parte. Il grafo nasce dall'indice di tutto il progetto, letto per intero: la parte comune è `daodan/core/code_graph.py`, lo store degli archi è `edge_store.py` (schema 5: archi, buchi con la classe, esterni), la vista da cui leggono i consumatori è `edge_view.py`, la copertura è per linguaggio (`complete` oppure `lower-bound`). Ogni linguaggio ha il suo adattatore in `daodan/core/indexers/`, che dichiara nome, linguaggi e se chiede il container: scip-go, scip-rust, scip-typescript (TypeScript, JavaScript, Vue, Svelte), scip-python, scip-java, scip-kotlin, scip-clang (C e C++), scip-dotnet, e il grafo dei fogli di stile. La pre-mappa (`daodan/core/premap/`) dice a ogni indicizzatore unità, radice e configurazione. Restano i task sotto.

**Dove sta il resto:** lo stato per linguaggio in [`docs/plugins/codebase-map-linguaggi.md`](../plugins/codebase-map-linguaggi.md) e [`codebase-map-supporto.md`](../plugins/codebase-map-supporto.md); il disegno in `docs/specs/2026-11-15-pipeline-di-analisi.md` e `docs/specs/2026-11-08-risoluzione-chiamate-motore.md`; le misure in [`benchmarks/inference-audit`](../../benchmarks/inference-audit/README.md) e [`benchmarks/project-model`](../../benchmarks/project-model/README.md).

**Convenzione:** un buco dell'indice non è un buco dell'analisi. Ciò che lo step `analyze` lascia aperto lo prende il passo dinamico: la misura è in [`benchmarks/call-provenance`](../../benchmarks/call-provenance/README.md).

**Vincoli:** i test si scrivono prima del codice; nessun codice del progetto gira sull'host; nessun filtro silenzioso: ogni chiamata e lettura dello snapshot finisce in un arco o in un buco con la sua classe.

## Decisioni del proprietario ancora in uso

1. Le domande per posizione si fanno solo su richiesta (un file appena cambiato, un buco, un arco incerto), mai in background: dopo la lettura completa dell'indice il passo per posizione aggiungeva 58 chiamate su 72.890 in tududi JavaScript, 5 in semver, 0 in chi e in tududi TypeScript.
2. Il numero di copertura è per linguaggio: siti con risposta su siti, buchi per classe, archi incerti, stato `complete` oppure `lower-bound`. «Risolte su risolvibili» è uscito dal prodotto; i benchmark lo calcolano con i loro script.
3. Renovate (AGPL-3.0) è un programma separato: Daodan lo scarica, lo avvia, legge il risultato e lo chiude; il codice di Daodan non contiene nulla di Renovate.
4. Codice senza build file, chart Helm, moduli buf e target Xcode sono unità come le altre, con il loro tipo.
5. Il codice del progetto non gira mai con la rete aperta; un comando che non esegue codice del progetto (un gestore di pacchetti che solo scarica, con gli script spenti) può usare la rete pubblica.

## Task aperti

### Aggiornamento incrementale

Oggi dopo una modifica a un solo modulo ripartono la pre-mappa intera e tutti gli indicizzatori: il 95% del tempo di un'analisi da zero (`benchmarks/project-model`, «Tre corse sullo stesso progetto»).

- [ ] **Test prima**, sulla fixture TypeScript con un file cambiato: l'indicizzatore riceve solo il file cambiato e chi lo importa; il grafo fuso è uguale al grafo completo della fixture cambiata; con lo snapshot invariato l'indicizzatore non parte; un lockfile cambiato rifà tutto.
- [ ] Che cosa si rifà, per indicizzatore: scip-go i pacchetti dei file da rifare; scip-typescript il file e chi lo importa, anche in modo transitivo; rust-analyzer il crate; scip-python tutto, salvo un'opzione per un sottoinsieme da verificare; scip-java il modulo della build. Ripiego: tutto il linguaggio.
- [ ] **Misura:** un file cambiato su chi e su tududi: file rifatti, secondi, uguaglianza con il grafo completo.

Le regole di riuso sono nella spec della pipeline, sezione 7.3 e punto aperto U2.

### Fine del passo per posizione

I motori per posizione dei linguaggi non ci sono più. Resta il loro telaio: `daodan/core/position_stage.py` (popolazione, `--stride`, `--limit`, cache `engine-answers.sqlite`), `scip_engine.py` con `--engine scip --scip-index` in `resolve_edges.py`, `classify_reference` e `project_callee_names` in `edge_grading.py`, e `daodan/core/engines/KotlinResolver.kt`, che nessun file nomina.

- [ ] Decidere se le richieste mirate entrano: una richiesta su un file cambiato, su un buco e su un arco incerto, le cui righe riempiono solo buchi, non sostituiscono mai una fine dell'indicizzatore e riportano una contraddizione. Nel codice non c'è nulla: `codebase_map_index` non ha `targets`.
- [ ] Togliere il telaio, o dire per che cosa resta.

Confronto fra passo per posizione e indice, sulle stesse chiamate: fatto per Go, Rust, JavaScript, TypeScript e Python (README di `benchmarks/inference-audit`); per Java e Kotlin (javapoet, klaxon) non verificato in questo riordino; phazly TypeScript e Rust non risultano mai misurati così.

### C e C++

- [ ] **Secondo tentativo di configure:** `clang_run.second_attempt` restituisce sempre `None`. Il passo deciso: Daodan scarica, senza eseguire nulla del progetto, ciò che il fornitore di dipendenze di CMake ha registrato, poi il configure gira di nuovo senza rete con `FETCHCONTENT_SOURCE_DIR_<NAME>`. Oggi l'unità è `unavailable` con `download-outside-registries` e gli URL registrati.
- [ ] **`extern "C"`:** in C++ scip-clang v0.4.1 non scrive occorrenze per ciò che è dichiarato in un blocco `extern "C"` (91 chiamate in tinyxml2). Sono buchi dichiarati con questa causa (`EXTERN_C` in `indexers/clang.py`); la correzione è upstream: [`docs/research/2026-11-16-scip-clang-extern-c.md`](../research/2026-11-16-scip-clang-extern-c.md).
- [ ] **Soglia** su zlib e tinyxml2 con il codice del prodotto (conteggi contro `results/graph-c-zlib.json` e `results/graph-cpp-tinyxml2.json`, verifica a mano 20 su 20 e almeno 16 su 20): non verificata in questo riordino.
- [ ] `SyntaxSnapshot` di `benchmarks/inference-audit/lang_clang.py` resta finché lo snapshot del prodotto non legge interi i file di zlib e tinyxml2 con macro.

### Java e Kotlin

- [ ] Run reale su klaxon nel container con i volumi, e soglia su javapoet e klaxon: non verificate in questo riordino (il README di `benchmarks/inference-audit` ha un confronto dei conteggi su Modal).

### Fogli di stile

- [ ] **Convenzioni dei framework per il caricamento:** il layout di Next.js sulle pagine del suo albero, `static/` di Sapper, `angular.json` `styles`, HtmlWebpackPlugin. Dovevano arrivare dalla pre-mappa come `units`, ciascuna con una fixture; in `daodan/core/premap/` non ce n'è traccia. Senza, quegli archi restano incerti (`sheet-not-proven-loaded`).
- [ ] **Soglia** sui casi reali: styled-components-website non è misurato (README di `benchmarks/inference-audit`).

### Pre-mappa

- [ ] `daodan/core/premap/suffix_table.py` resta accanto a go-enry (`premap/enry.py`): il piano la toglieva.
- [ ] **Voci in più per causa**, dalla misura sui 122 progetti (`benchmarks/project-model`): un'unità dello stesso progetto riportata come pacchetto esterno; una voce di una tabella condivisa di versioni riportata come dipendenza (pnpm `catalog:`, `[workspace.dependencies]`, `Directory.Packages.props`, `dependencyManagement`, catalogo Gradle); un vincolo di linguaggio, runtime o SDK contato come pacchetto; la stessa dipendenza sotto un secondo nome; un file di pip-compile letto come dichiarazioni; `scope` e `declared_in` sbagliati; toolchain e unità in più. Stato di ognuna non verificato in questo riordino: vale l'ultima misura del README.
- [ ] Da decidere: `ext-*` di Composer e `flutter: sdk` sono dipendenze o toolchain.

## Rischi ancora da verificare

- TypeScript: pnpm e yarn; il pacchetto `. .` (968 chiamate); `fireEvent.click` senza occorrenze.
- Python: con i soli wheel alcuni pacchetti possono mancare e i loro esterni diventano buchi; la libreria standard marcata 3.11; `import *` per il salto `builtin`.
- JVM: l'overload dei simboli del JDK; l'ordine compilato in Kotlin; Gradle 8 e oltre, Android, Kotlin Multiplatform.
- Codice generato: i processori di annotazioni Java producono codice senza dichiarazione nell'indice, che diventa buco.
- Tempo della lettura: su tududi la lettura dell'indice in Python (67,1 s) pesava quanto l'indicizzatore (55 s).
