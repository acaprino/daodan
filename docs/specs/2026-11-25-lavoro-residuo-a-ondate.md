# Il lavoro che resta, in ondate

**Stato:** chiesta dal proprietario il 25 novembre 2026. Condensa in un documento solo ciò che le spec e i piani dichiarano ancora da fare o fatto in parte. Non decide nulla di nuovo: ogni voce rimanda alla sezione da cui viene, dove restano i motivi e le misure.

**Come è stata scritta.** Letti il 25 novembre tutte le spec e i piani di `docs/` (19 spec, 13 piani, la roadmap). Lo stato di ogni voce è quello che il suo documento dichiara, non riverificato sul codice, salvo dove è scritto «visto nel codice». Dove due documenti si contraddicono è detto.

**Come si legge.** Un'ondata è un insieme di voci che si chiudono insieme e ha un cancello: la prova che la dichiara finita. Un'ondata parte quando quelle da cui dipende hanno passato il cancello. Dentro un'ondata l'ordine è quello scritto. Ogni voce è marcata: **[deciso]** approvata dal proprietario, **[proposta]** mai approvata, **[misura]** una misura da fare, **[difetto]** un errore noto.

| Ondata | Che cosa chiude | Dipende da |
| --- | --- | --- |
| 0 | Le verifiche in sospeso e i documenti che dicono il falso | — |
| 1 | `1_list_files`: il linguaggio di ogni file | 0 |
| 2 | `3_recognize_stack` e `4_find_modules`: lo stack prima, i moduli dopo | 0 |
| 3 | `5_find_entry_points`: rotte, pagine ed eventi fuori dalla pre-mappa | 2 |
| 4 | L'orchestratore e i nomi degli step | 2, 3 |
| 5 | `6_link_calls`: ciò che resta degli indicizzatori | 2 |
| 6 | Il container e la preparazione | — |
| 7 | `7_run_and_observe`: test, programma, interfacce | 3, 6 |
| 8 | `8_assemble_graph`, flussi e mappa del sistema | 3, 5 |
| 9 | Ricerca e review | 8 |
| 10 | L'app e l'esploratore | 8 |

Le ondate 1, 2 e 6 non dipendono l'una dall'altra e possono procedere insieme.

## Ondata 0: verifiche in sospeso e documenti allineati

Nessun disegno nuovo: si chiude ciò che è già scritto e non è mai girato, e si toglie dai documenti ciò che non è più vero.

1. **[misura]** La suite intera su Modal sul codice del 25 novembre: anagrafica dei formati, modulo del linguaggio, generatore dell'albero della pipeline. Non è mai girata (visto: nessun workflow parte da solo sui test Python).
2. **[misura]** La «Verifica» dello stack dal fork, ferma perché Modal non era raggiungibile: nessuna perdita sul corpus dopo il passaggio, tempo della scansione veloce, prova che nulla del progetto viene eseguito con `cli()` e il Node veri, nuova misura su `develop` (spec stack dal fork, «Verifica»; piano 3, B4 passo 4, B6, B7).
3. **[difetto]** Gli «aperti noti» dello stack: il test instabile di `test_codebase_map_app.py`, `replace => ../local` di Go e i repository `path` di Composer letti come esterni dal fork, 37 marchi senza cornice, Avro duplicato, `technologies.state` che non scrive più la pre-mappa (spec stack dal fork, «Aperti noti»).
4. La pagina costruita `docs/pipeline/` nel repository: oggi è solo nell'artifact `built-docs` del workflow Viewer (visto).
5. `docs/plugins/codebase-map-supporto.md` da rigenerare (`support_table.py build`): cita percorsi che non esistono più (visto; piano ingressi, 14c).
6. **Documenti da allineare**, perché dichiarano uno stato superato:
   - i piani 1 e 2 dello stack dal fork e il piano della copertura dell'intero sorgente hanno tutte le caselle vuote, mentre altri documenti li dicono consegnati o in parte applicati;
   - il task 12 del piano «grafo dall'indice» ha le caselle vuote, mentre la spec della pipeline dichiara pre-mappa e moduli applicati;
   - la spec della risoluzione delle chiamate descrive i motori per posizione (Jedi, gopls, JDT LS), che la spec della pipeline dice tolti; dice anche C e C++ non analizzati, che il piano «grafo dall'indice» ha aggiunto;
   - la roadmap è ferma al 19 novembre: dice che nessun passo avvia `system-mapper` (la spec delle interfacce dice che parte da solo) e parla ancora della «navigazione delle pagine d'ingresso», sostituita dall'esplorazione;
   - la spec degli ingressi dà «non eseguite» tre sonde che il piano dà misurate (`"use server"`, Flask, Spring);
   - la spec del benchmark di scope resolution usa gli esiti `resolved/incomplete/needs_clarification`, la spec ridotta `resolved/partial/clarify`.
7. `README.md` («How the graph is built») e `docs/plugins/codebase-map.md` («Il disegno», «Dal codice al disegno») descrivono ancora i sette step: vanno portati agli otto (piano del 25 novembre, task 8).

**Cancello:** la suite passa su Modal; la «Verifica» dello stack ha il suo verdetto nel README del benchmark; nessun documento dell'elenco 6 contraddice più un altro.

## Ondata 1: `1_list_files`, il linguaggio di ogni file

Da: spec del linguaggio (24 novembre, ripristinata il 25); spec della pipeline, 8.3 punto 2.

1. **[deciso]** La regola dei `.h` diventa una classe di `languages/detect/rules/` e legge l'albero sintattico (scelta «T», via `R3dx`): prima Objective-C con la regola di oggi, poi i nodi C++ che C non ha, poi la grammatica con meno errori. Il lavoro del parser ha un tetto deterministico, mai un orologio; oltre il tetto la risposta è quella dell'estensione, dichiarata. `benchmarks/header-language` misura la regola dov'è oggi: si aggiorna con lo spostamento.
2. **[deciso]** Il riconoscimento per nome di file (Dockerfile, Makefile), con lo stesso formato delle regole.
3. Il tetto ai byte guardati da ogni regola, e la prova che il costo cresce in linea con la lunghezza (garanzia 4).
4. **[difetto]** La regola `.ts` nuova non chiede la fine di parola dopo `<?xml` e `<!DOCTYPE`: 112 risposte diverse su 186.124 testi generati. Da correggere o accettare.
5. La corsa settimanale che confronta il catalogo con l'ultima versione di Linguist e propone le estensioni aggiunte, tolte o spostate, da accettare una per una.
6. **[misura]** I gate di «Come si prova»: i 180 progetti contro il lettore di prima, il piano dell'analisi dei 122 progetti invariato, suite e phazly su Modal.
7. **[scelta aperta]** go-enry gira ancora nel container e la lettura non lo usa: resta o si toglie?

**Cancello:** i gate del punto 6 passano e `languages.detect_language` non contiene più nessuna regola sua.

## Ondata 2: `3_recognize_stack` e `4_find_modules`

Da: spec della pipeline, 8.1 e 8.2; piano del 25 novembre, task 1–5; piano «grafo dall'indice», task 12; spec della pipeline, «Preparazione».

1. **[misura]** `benchmarks/stack-build-tools/` su Modal: per ogni fixture, gli strumenti di build che il fork nomina (con la cartella) contro quelli che le sorgenti di oggi trovano da sé. La prova esplorativa del 25 novembre non è una verifica (task 1).
2. **[deciso]** Nel fork le regole per ciò che non conosce: CMake, Bazel, Meson, Make, autotools, sbt, .NET SDK, Mix, Nx (`project.json`), e Python nominato su `pyproject.toml` e `requirements.txt`. Solo riconoscimento. Rilascio `.6`, fissato in Daodan (task 2).
3. **[deciso]** `daodan/data/build-tools.json`: ogni voce dello stack che è uno strumento di build o una toolchain, con l'adattatore che la usa; un test dice quale adattatore non ha una voce e viceversa (task 3).
4. **[deciso]** `3_recognize_stack` gira per primo, sull'elenco dei file, senza moduli e senza pre-mappa (task 4).
5. **[deciso]** `4_find_modules` dopo: parte l'adattatore di ogni strumento trovato; nessuna sorgente cerca più da sé il suo file. Poi le tecnologie si assegnano ai moduli (task 5).
6. **[scelta aperta]** I pacchetti che solo il passo 4 conosce (lock, Compose, Renovate): proposta, il fork gira una volta e il 4 aggiunge i suoi segni con `technologies.merge`.
7. **[scelta aperta]** I lettori dei manifest (`build_units.py`) restano come ripiego senza container, o i moduli diventano una lacuna?
8. Ciò che resta del modello di build (piano «grafo dall'indice», task 12): unità interne contate come pacchetto esterno, la tabella condivisa delle versioni, i vincoli di runtime contati come pacchetti, BOM e `platform()` con un tipo loro **[deciso]**, una voce sola per unità e pacchetto **[deciso]**, scope e `declared_in` sbagliati, toolchain e unità in più.
9. Ripristino nelle cartelle annidate, quattro casi aperti: una cartella senza lockfile che nessun workspace nomina (Lerna), un crate Cargo, un progetto .NET, un `requirements.txt` (spec della pipeline, «Preparazione»).
10. **[misura]** Renovate è un terzo lettore dei pacchetti: che cosa dà in più del fork.

**Cancello:** sul corpus i moduli sono quelli di prima o una differenza è spiegata riga per riga; `premap.SOURCES` non contiene più una sorgente che decide da sé se applicarsi.

## Ondata 3: `5_find_entry_points`

Da: spec della pipeline, 8.2 e 8.13; piano del 25 novembre, task 6; spec e piano degli ingressi (task 13a–13f, 14, 17).

1. **[deciso]** Le sorgenti dei framework e Noir escono da `premap.SOURCES` e scrivono un'uscita loro; `binder.bind` gira dentro lo step. Chi legge `framework_entries` e `noir_entries` dalla pre-mappa passa alla nuova uscita: `dynamic/app.py`, `flow_entries.py`, 15 file di test, 10 benchmark.
2. **[deciso]** Il lanciatore dei comandi nel container (`premap/container_runner.py`) diventa un servizio comune agli step 4 e 5.
3. La sorgente di Angular non legge più i componenti per conto suo: li trova letti da `2_read_code`. **[misura]** Quanto costa oggi quella lettura su un progetto grande (spec della pipeline, 8.11 passo 5, pezzo D).
4. **[difetto]** Il legatore: una funzione anonima dentro una closure di rotta in Go o C#, una anonima citata per posizione legata con qualunque nome, il registratore anonimo sulla stessa riga della closure. `premap/flask_app.py` lega ancora dentro `read()`. Un default anonimo sparisce senza lacuna (8.13).
5. L'unione fra Noir e lo strumento del framework vale solo per Next.js: manca per React Router, SvelteKit e Nuxt. La tavola `http` di `flows._declared_routes` nomina solo Noir e Next.js.
6. Per framework, ciò che resta aperto (piano degli ingressi, 13a–13f):
   - **Next.js:** versioni senza `typegen`, Pages Router, `<form action>`, `ParamMap`, segmenti come `a-[id]`; le azioni che girano sul server non hanno un lettore.
   - **React Router e Remix:** `basename`, cartella dell'app diversa da `app`, monorepo, `createBrowserRouter`, che non ha un comando.
   - **SvelteKit:** `actions`, `+page.svelte`, `outDir`, SvelteKit 1.
   - **Nuxt:** il campo `page`, `defineEventHandler` non legato, pnpm e Yarn, Nuxt 2.
   - **Angular:** `host` e `@HostListener`, uscita di un figlio contro evento DOM (misurata, non collegata), il gestore scritto come proprietà-freccia.
   - **Astro:** le rotte da `astro:routes:resolved`; il legame del gestore a una funzione, che oggi dà zero ingressi.
   - Nessuna delle sei è mai girata su un progetto vero.
7. **Go:** il legame generico «dall'ultimo argomento della chiamata alla riga di registrazione», da go/types o scip-go, per gin, echo, chi, fiber e `net/http` (piano, 14g).
8. Il gestore dall'estremo del motore (`onClick={salva}`, `command=self.salva`) e le due regole dall'albero: una funzione che restituisce solo markup non è un evento; l'etichetta segue il nome accessibile del W3C (piano della pipeline intera, task 3 e 4).
9. **[proposta]** Il valutatore di stringhe per i percorsi calcolati; mancano il lettore di stringhe per le concatenazioni e `format` in Java, Python e Go (piano dell'analisi unificata, task 2).
10. La prova del wrapper HTTP: il wrapper di un wrapper, i client axios, requests e httpx, gli altri linguaggi (piano, 17).
11. **[scelta aperta]** Django, FastAPI e Flask: le tre sorgenti sono scritte e scollegate. Restano fuori o entrano?
12. **[scelta aperta]** La licenza PolyForm dei lettori di GitNexus: tenerli fuori o riscriverli dal metodo. Il risolutore per Express resta da valutare eseguendolo (14j).

**Cancello:** la pre-mappa non contiene più rotte, pagine né eventi; i flussi dei casi di `benchmarks/system-map` sono quelli di prima.

## Ondata 4: l'orchestratore e i nomi

Da: spec della pipeline, 8.7–8.12; piano del 25 novembre, task 7.

1. **[deciso]** I nomi con il numero (`1_list_files` … `8_assemble_graph`) in `NAME`, eventi, giornale, cartelle (`step_N_…`), documenti e interfaccia. Un giornale scritto con i nomi di prima si legge ancora. Lo step `parse` di oggi, che dice solo il piano, sparisce.
2. La dichiarazione comune per ogni famiglia di adattatori (8.8 punto 1).
3. La freschezza controllata in un punto solo, con `step.skipped` (8.8 punto 2); l'uscita degli strumenti come `log` di livello `debug`.
4. **[misura]** Un limite di tempo per stage, dalle durate registrate. Prima va letto che cosa resta del container di uno stage chiuso da fuori (8.9).
5. Il giornale cresce e ogni lettura lo rilegge tutto: un cursore in byte cambierebbe il contratto MCP (8.9).
6. Le prove 2 e 5 di 8.10, mai scritte: le due modalità danno lo stesso grafo; un ripiego è dichiarato accanto al dato.
7. Tre funzioni oltre le 80 righe: `engine_pass.index_stage`, `snapshot.write_reading`, `snapshot._refresh_locked`.
8. **[scelta aperta]** L'ordine delle sorgenti (lista scritta o bisogno dichiarato), `pass` contro `run`, quando cambiano i nomi sul disco, la colonna `producer` (A1).

**Cancello:** nessun nome di prima resta nel codice, salvo il lettore dei giornali vecchi; le prove 2 e 5 passano.

## Ondata 5: `6_link_calls`

Da: piano «grafo dall'indice», task 4–11; spec della risoluzione delle chiamate; spec della pipeline, 7.2.

1. L'aggiornamento incrementale dell'indice: test con un file cambiato, misura su chi e tududi, cancellazione di `engine-answers.sqlite` (task 7).
2. Le richieste mirate: `positions=` che riempiono solo i buchi, l'entrata unica `codebase_map_index` con `targets`, la cancellazione del passo per posizione e di `--engine scip` (task 8).
3. JVM: la run reale su klaxon, la soglia su javapoet e klaxon, la cancellazione di `JavaEngine`, `KotlinEngine` e `KotlinResolver.kt` (task 9).
4. C e C++: l'immagine unica con il compilatore come archivi **[deciso]**, il secondo tentativo dello scaricamento con `FETCHCONTENT_SOURCE_DIR_*` **[deciso]**, il driver guidato dalla pre-mappa, la soglia su zlib e tinyxml2. Meson, Make e Bazel restano `unavailable` (task 10).
5. Fogli di stile: le convenzioni di caricamento dei framework come unità della pre-mappa; la soglia da rifare con il codice del prodotto (task 11).
6. I doppioni di 7.2: il secondo Pyright, `typescript_unbound.js` accanto a `css_typescript.py`, lo stato per linguaggio e non per modulo. Le regole di 7.3 entrano dopo la misura 2b.
7. **[difetto]** Un passaggio staccato su quattro si chiude dopo circa sei minuti senza store né log: c'è solo la mitigazione, la causa è aperta. Le 154 chiamate `self.metodo()` che la regola lessicale dovrebbe già risolvere.
8. **[misura]** Una modifica a un modulo rifà il 95% del lavoro: pre-mappa intera e cinque indicizzatori (piano dell'analisi unificata, 2b). Il guadagno del ripristino condiviso non è misurato.
9. Mai controllate: licenza e attività degli indicizzatori prima di fissarli; su Windows scip-go, rust-analyzer, giunzioni e CRLF (§8 del piano).

**Cancello:** le soglie dei task 9, 10 e 11 sono nel README dei loro benchmark; il passo per posizione non esiste più.

## Ondata 6: il container e la preparazione

Da: spec e piano del passo dinamico, sezioni 2–4; piano dell'analisi unificata, task 1 e 1b.

1. **[deciso]** Fuori da Windows il motore è ancora il Docker o il Podman dell'utente: il proprietario ha chiesto sempre il Kiri di Daodan (sezione 3). La prova reale con il Kiri di Daodan e la lacuna con cgroup v1 non sono verificate (piano, task 4).
2. Lo scaricamento, tutto specificato e non costruito: il proxy pubblico con il controllo degli indirizzi, la tabella chiusa dei comandi, la lettura del lockfile che rifiuta git, URL, `file:` e `-e`, la versione del gestore fissata da Daodan, il registro di indirizzi e checksum (4.1).
3. Le neutralizzazioni per npm, pnpm, Yarn, Cargo, Go, pip, uv e curl, con le loro fixture; l'ambiente git comune; le credenziali (`HOME` di Daodan, helper spenti, un registro privato rende l'unità `unavailable`) (sezione 4).
4. Gli script di installazione girano nella preparazione solo per Gradle e Maven (4.2).
5. **[misura]** Che le due reti vengano onorate su ogni motore; che i registri ammessi non accettino caricamenti; `--cap-drop ALL`, utente non root e tetto sul log, specificati e non costruiti (2.3, 4).
6. L'immagine unica con base glibc per digest e strumenti scaricati al primo uso: oggi le immagini sono per linguaggio (sezione 3).
7. Su Modal: l'allowlist per host non filtra il traffico non TLS; con i servizi la preparazione non è confinata; le liste di host non sono mai state osservate (piano dell'analisi unificata, task 1).
8. **[scelta aperta]** Come avviare i servizi dichiarati altrove (include di GitLab, Compose da un Makefile); i passi prima dei test in GitLab; su Kiri i passi accanto ai servizi.

**Cancello:** su ogni motore la sonda di rete passa, e un progetto con un lockfile che punta a un URL viene rifiutato con la sua lacuna.

## Ondata 7: `7_run_and_observe`

Da: spec dell'esecuzione del programma e delle interfacce (entrambe proposte del 19 novembre: nulla è applicato, salvo dove scritto); roadmap; piano degli ingressi, task 11.

1. **[proposta]** L'albero delle chiamate in ogni registro esatto, e le frontiere (accesso e risorsa) con la tabella chiusa per linguaggio (esecuzione, 1 e 2).
2. **[proposta, con decisioni del 20 novembre]** La corsa del programma dal container preparato: attesa della porta, il richiedente solo sugli ingressi senza pagina. I dati e le credenziali di prova sono solo quelli che la CI del progetto già prepara **[deciso il 25 novembre]** (esecuzione, 4).
3. **[proposta]** Il catalogo delle superfici: il campo `surface` nell'anagrafica (`web`, `webview`, `desktop`, `windows`, `android`). Entrano subito le voci web, tra cui Streamlit e Gradio, e le webview (Electron, Tauri). NiceGUI, Wails e i toolkit desktop, compresi quelli Python, entrano ognuno con un caso reale nel corpus (interfacce, 3).
4. **[deciso il 19 novembre]** Le interfacce desktop Python riconosciute dal codice; l'osservazione dinamica ha avuto un «no per ora» (interfacce, 1.6).
5. **[proposta]** `builds` e `starts` dalle altre fonti: `angular.json`, `tauri.conf.*`, `pyproject.toml`, i target di Cargo, Dockerfile e Compose. Oggi l'app parte solo con npm: mancano pnpm, Yarn e Bun (interfacce, 5; piano degli ingressi, 11).
6. L'esplorazione nel browser: la pagina offerta dal server del progetto, Electron con uno schermo virtuale, Tauri e Wails con il driver della webview. I controlli dietro un accesso non si raggiungono senza credenziali (interfacce, 7; piano, 11).
7. La fonte osservata per i flussi: ruolo e nome dei controlli, le chiamate di un clic. Qt non è provato; mancano osservazioni dal vivo (spec degli ingressi, «Stato»).
8. **[proposta]** La riproduzione di un finding e un'indagine nel container, dopo la correzione di `review-quality-gates` (esecuzione, 5).
9. **[misura]** La corsa Python su Daodan con `--continue-on-collection-errors`; per C# il limite che il registro può chiudere (passo dinamico, «Stato» e 7).
10. Desktop Linux, Android e Windows restano la lacuna `ui_execution_deferred`: futuro, su consenso (roadmap, fase 3).

**Cancello:** le cinque prove della spec dell'esecuzione sono misurate; l'esplorazione gira su un progetto vero con un gestore diverso da npm.

## Ondata 8: `8_assemble_graph`, flussi e mappa del sistema

Da: spec della pipeline, 8.2; spec dei flussi e della mappa; spec degli ingressi, sezione 7; piano della mappa del sistema.

1. **[deciso]** `8_assemble_graph` unisce davvero ai punti di connessione (rotte, chiamate HTTP, eventi, tabelle): oggi dice solo ciò che c'è e ciò che manca. Gli archi fra moduli li scrive lo step, non il primo lettore.
2. Il motore generale dei legami, con un adattatore per tipo: esiste solo nel ramo `feat/link-key-shape` (Principio 3).
3. I candidati dalla macchina: i membri dei nodi vengono dai candidati, non da chi propone; la copertura e i doppioni contano i candidati (2.1, 6.2, 8.1, 8.4, 8.5).
4. Le prove mai scritte per sezioni dichiarate applicate: 2.3, 2.5, 5.5, 6.3, 6.4 e altre; il test che il codice dei legami non nomini un framework (Principio 2).
5. **[difetto]** `on` fra due nodi con codice è accettato senza un punto citato; un flusso può risultare `verified` senza che lo store sia provato (8.3; piano degli ingressi, 7b).
6. **[proposta]** La coda di domande che la macchina impone; i collegamenti certi e possibili; la fusione delle varianti (spec degli ingressi, 7.3, 7.7, 7.8).
7. **[misura]** Il confronto cieco: con il modello debole 0 flussi su 19. La sezione 7 non passa la sua prova decisiva; la spesa del modello non è misurata.
8. Le misure 1, 5 e 6 di `benchmarks/system-map` non raggiunte; il modello dell'agente non fissato; le misure 7 e 8 da fare (la 8 è a pagamento); la scoperta cieca.
9. **[proposta]** Varianti ed estremi dei flussi; i flussi di interfaccia; cambiare livello conservando flusso e nodo (3.2, 3.3, 3.7, 4.6).
10. I servizi in ingresso senza pacchetto: manca un dato ufficiale (piano degli ingressi, 19). Di Kubernetes, hosting e CI si legge solo il nome del file (5.7). Gli host non sono letti da nessun controllo (5.2).
11. **[difetto]** Dal collaudo: un run su una sottocartella fa fallire l'indicizzatore nel container; con l'archivio dell'analisi dentro il progetto gli strumenti della pre-mappa sono rifiutati.
12. **[proposta]** Due misure in più: la forma della risposta contro ciò che il client legge; i contratti fra repository (piano degli ingressi, 15 e 16).

**Cancello:** le misure di `benchmarks/system-map` hanno il loro verdetto nel README; il confronto cieco ha un numero per ognuno dei due modelli.

## Ondata 9: ricerca e review

Da: spec della ricerca e del pacchetto di review; spec della review (3, 4, 7 e 9 novembre); spec dei revisori per framework.

1. **[proposta]** L'anagrafica dei flussi e i legami `avvia`, `condivide`, `stesso dato`, calcolati dalla mappa (ricerca, 3.8; piano, task 9).
2. **[proposta]** Gli embedding sulle voci dell'anagrafica e sui nodi; **[misura]** EmbeddingGemma 2 non è misurato; **[scelta aperta]** chi prepara il modello, visto che oggi nessuno scarica i pesi (12.1, 12.2; decisione aperta 11).
3. **[proposta]** Il pacchetto di review dalla ricerca; la fase 3 ha misurato che i flussi non aiutano la review, quindi va misurato prima di adottarlo (11.6, 12.3).
4. **Stato da accertare sul codice:** il run di lavoro e il suo aggiornamento (`snapshot.py refresh`, l'hook, il controllo di freschezza) e le regole 1–4 della review. La spec è «approvata, pronta da implementare» e non dichiara nulla di fatto, ma altri documenti citano un run `working` (spec del 9 novembre, fase 1).
5. **Stato da accertare sul codice:** la copertura dell'intero sorgente, parte A. Il piano ha tutte le caselle vuote, altri documenti la usano. Il benchmark `benchmarks/whole-source-coverage` e la parte B (riuso delle celle) aspettano la misura e il via del proprietario.
6. La Phase 0 «dalla richiesta ai file» è scritta e mai eseguita in una review completa (spec del 4 novembre).
7. Le micro skill e le baseline per stack non esistono: ogni review dichiara la lacuna. Il confronto a quattro bracci non è mai stato fatto (spec del 3 e del 7 novembre).
8. Revisori per framework: estendere la soppressione senza import a `react` e `tauri`; i tre segni da aggiungere al registro **[deciso]**; un caso in cui la baseline manchi il difetto riaprirebbe la valutazione.
9. **[difetto]** `graph` dà `ValueError` e `edit_impact` dà `missing_store` sul run (spec del 7 novembre, «Gap»).

**Cancello:** i punti 4 e 5 hanno uno stato scritto dopo aver letto il codice; ogni proposta adottata ha la sua misura.

## Ondata 10: l'app e l'esploratore

Da: spec dell'app standalone; piano dell'esploratore; spec dei flussi, sezione 4.

1. Da implementare: il server applicativo, il coordinatore della coda, gli adattatori dei motori con la prova di capacità, l'annullamento e la ripresa (app standalone, «Stato»).
2. L'ingresso da GitHub con accesso: GitHub App, device flow, token nel portachiavi. Registrare l'App è un prerequisito.
3. **[proposta]** Il servizio sul PC: la cartella applicativa portabile, l'app che parla solo via HTTP con un token. **[da verificare]** La licenza di Kiri per la ridistribuzione; il portachiavi su Linux senza desktop.
4. La mappa nella pagina dell'app: oggi non la mostra. Il grafo dell'app non è mai stato misurato su un progetto grande (spec dei flussi, tabella di stato).
5. **[difetto]** La pagina dell'app non ha un comando per salvare un percorso e, riaperta, non mostra lo stato della scheda (spec degli ingressi, collaudo).
6. L'esploratore: i pannelli ridimensionabili e i filtri; la verifica da tastiera; la misura su un run reale, i cui obiettivi di prestazione non sono raggiunti sul sintetico. Il parametro `level` usa ancora i nomi vecchi.
7. **[deciso]** L'albero della pipeline (`docs/pipeline/`) resta scritto dal codice: una sorgente, un analizzatore o una regola nuova senza la sua voce fa fallire `pipeline_tree.py check`.

**Cancello:** un lavoro intero con un motore controllato passa (eventi, errore, timeout, annullamento, riavvio); la mappa è nella pagina dell'app.

## Fermo o ritirato: non si rifà

| Che cosa | Perché | Dove |
| --- | --- | --- |
| I file che la pre-mappa esclude non si leggono (E1) | Toglierebbe 1.496 file veri, verso cui vanno 96 import | Pipeline, 8.3 |
| Radici e alias degli import da `tsc` | Su 25 progetti veri 0 import guadagnati e 110 persi | Pipeline, 8.3 |
| Un lettore dei soli dati di Linguist | 95 header C++ letti come C, da 8 a 48 secondi su file costruiti male | Linguaggio |
| Sorgenti di FastAPI, Django, Flask e Spring | Sulle applicazioni vere Noir dà lo stesso | Piano degli ingressi, 14a–14f |
| Sorgenti di Laravel e Rails | Daodan non legge PHP né Ruby | Piano degli ingressi, 14d e 14e |
| `framework.cjs`, il lettore di framework scritto a mano | Contro la regola d'oro | Decisione del 20 novembre |
| Unità e flussi dentro la review | Su phazly nessun difetto in più, dieci run | Flussi nella review |
| Quattro revisori per framework e le undici voci del catalogo | Nessun valore in più sulla baseline | Revisori per framework |
| Il profiler V8 per JavaScript | 47,1%, sotto la soglia: sostituito dal registro esatto | Passo dinamico |
| `plan` come step | Resta una funzione | Pipeline, 8.4 |

## Scelte aperte del proprietario

1. `build_units.py` senza container: ripiego o lacuna (ondata 2).
2. I pacchetti che solo il passo 4 conosce: `technologies.merge` senza rilanciare il fork (ondata 2).
3. `2_read_code` prima di `3_recognize_stack`: se si sposta cambiano i nomi da 2 a 4 (ondata 4).
4. Django, FastAPI e Flask dentro `5_find_entry_points` (ondata 3).
5. go-enry: resta o si toglie (ondata 1).
6. La licenza dei lettori di GitNexus (ondata 3).
7. Il valutatore di stringhe per i percorsi calcolati (ondata 3).
8. Il metro dei gate dei flussi: Opus o il modello debole, con il tetto di 2 USD (ondata 8).
9. Due ingressi con lo stesso esito: varianti o due flussi; che cosa vuol dire «ingresso» nelle tre spec (ondata 8).
10. Chi prepara il modello degli embedding (ondata 9).
11. Le soglie di `benchmarks/system-map` e i riferimenti, mai confermati: ogni numero è una bozza (ondata 8).
12. L'ordine fra albero delle chiamate e corsa del programma; il primo linguaggio (ondata 7).
13. Il via per le prove a pagamento: la prova 0 con Qwen e Opus, la misura 8.

## I documenti che questa spec condensa

Restano dove sono, come dettaglio e storia; in testa a ognuno una riga rimanda qui. Lo stato di una voce si aggiorna qui.

| Documento | Ondate |
| --- | --- |
| `specs/2026-11-15-pipeline-di-analisi.md`, `plans/2026-11-25-stack-prima-degli-strumenti-di-build.md` | 0, 2, 3, 4 |
| `specs/2026-11-24-libreria-del-linguaggio.md` | 1 |
| `specs/2026-11-21-stack-dal-fork.md` e i suoi tre piani | 0, 2 |
| `plans/2026-11-14-grafo-dall-indice.md`, `specs/2026-11-08-risoluzione-chiamate-motore.md` | 2, 5 |
| `plans/2026-11-20-analisi-unificata.md`, `plans/2026-11-20-pipeline-intera.md` | 3, 5, 6 |
| `specs/2026-11-12-passo-dinamico.md` e il suo piano | 6, 7 |
| `specs/2026-11-19-esecuzione-del-programma.md`, `specs/2026-11-19-interfacce-del-progetto.md`, `roadmap.md` | 7 |
| `specs/2026-11-20-ingressi-e-scoperta-dei-flussi.md`, `plans/2026-11-20-ingressi-e-flussi.md` | 3, 7, 8 |
| `specs/2026-11-18-flussi-e-mappa-del-sistema.md`, `plans/2026-11-12-mappa-del-sistema.md` | 8, 10 |
| `specs/2026-11-20-ricerca-e-pacchetto-di-review.md` e il suo piano | 9 |
| Le spec della review del 3, 4, 7 e 9 novembre, `plans/2026-11-08-whole-source-coverage.md`, `specs/2026-11-19-revisori-per-framework-e-librerie.md` | 9 |
| `specs/2026-11-16-app-standalone.md`, `plans/2026-11-08-codebase-explorer.md` | 10 |
