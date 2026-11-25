# Daodan: architettura e contratto della pipeline

**Stato:** contratto di arrivo (estratto dal refactoring del 25 novembre 2026). Descrive *com'è Daodan a refactoring finito*. Il lavoro attivo è in [`docs/plans/refactoring.md`](../plans/refactoring.md); tutto ciò che è differito o ritirato è in [`docs/backlog.md`](../backlog.md) (non normativo). Le 19 spec e i 13 piani precedenti sono nella storia di git al commit `614c940`.

**Legenda:** `[deciso]` è una scelta approvata dal proprietario. Nella colonna «Stato»: «Nel codice» c'è oggi, «Parziale» c'è in parte, «Da creare» non c'è, «Proposta» non è mai stata approvata; fra parentesi il traguardo del piano.

## Principi

1. **Una competenza per step.** Chi analizza lo stack non trova i moduli; chi trova i moduli non cerca da sé quale strumento di build c'è; chi tiene il modello di build non tiene rotte ed eventi.
2. **Un padrone per fatto.** Uno step non riscopre ciò che un altro stabilisce: lo chiede a lui. Dove il padrone non ha potuto stabilirlo, chi ne ha bisogno usa un ripiego e lo scrive accanto al dato.
3. **Ogni step è un modulo a sé.** Dichiara ciò che legge, ciò che scrive e che cosa succede se fallisce; si può usare da solo per il suo compito, e nella pipeline lavora con gli altri. Non conosce l'interfaccia, il trasporto né il motore LLM.
4. **Le anagrafiche sono dati globali** (`daodan/data/`), non costanti sparse nel codice: gli step le consultano, e una voce nuova è una riga, non un `if`.
5. **Lo strumento ufficiale, mai una regola a mano.** Per ogni linguaggio, strumento di build e framework Daodan usa il suo parser, il suo compilatore, il suo comando. Dove nessuno dà il dato resta un lettore nostro, con scritto accanto quale strumento è stato valutato.
6. **Il codice del progetto gira solo nel container di Daodan**, mai sull'host. Senza container il passo è una lacuna con la sua causa.
7. **Ciò che non si è potuto fare si scrive:** una lacuna con causa e rimedio, mai un silenzio.

## La pipeline a otto step

Gli identificatori degli step sono **semantici e stabili** per codice, eventi, giornale e cartelle (`list_files`, `read_code`, `recognize_stack`, `find_modules`, `find_entry_points`, `link_calls`, `run_and_observe`, `assemble_graph`). La numerazione `1`–`8` indica l'ordine di presentazione, non l'identità tecnica. Il piano non è uno step: è una funzione che Daodan espone al chiamante.

| # | ID step | Competenza | Deve sapere prima, e da chi | Che cosa scrive |
| --- | --- | --- | --- | --- |
| 1 | `list_files` | L'elenco dei file | Cartella e perimetro: da chi avvia | Di ogni file percorso, dimensione, hash e linguaggio |
| 2 | `read_code` | Il contenuto di ogni file | Quali file e in che linguaggio: da `list_files` | Simboli, import e riferimenti, e come è andata la lettura |
| 3 | `recognize_stack` | Lo stack | I file: da `list_files` | Strumenti di build, toolchain, framework, librerie e servizi, ognuno con il file che lo prova. Nessun modulo |
| 4 | `find_modules` | Il modello di build | Quali strumenti di build ci sono e dove: da `recognize_stack` | Moduli, unità, toolchain, pacchetti e grafo dei pacchetti, comandi di test/avvio/build, servizi. Poi tecnologie di `recognize_stack` assegnate ai moduli |
| 5 | `find_entry_points` | Dove entra un utente o una richiesta | Framework e dove: da `recognize_stack`. Simboli: da `read_code`. Pacchetti ripristinati: da `find_modules` | Rotte, pagine ed eventi, ognuno legato alla sua funzione |
| 6 | `link_calls` | Dove arriva ogni chiamata | Riferimenti: da `read_code`. Unità e build: da `find_modules`. Ambiente preparato | Gli archi provati |
| 7 | `run_and_observe` | Ciò che viene chiamato davvero | Comandi di test/avvio/build: da `find_modules`. Pagine da aprire: da `find_entry_points`. Grafo statico: da `link_calls` | Archi osservati; controlli premuti, con le funzioni partite |
| 8 | `assemble_graph` | L'unione, e ciò che manca | Tutto | Grafo completo: archi fra moduli, ingressi uniti alle definizioni, osservato contro provato, lacune |

- **La pre-mappa è il modello di build**, uscita di `find_modules`: non tiene più rotte, pagine ed eventi. Il lanciatore nel container (`premap/container_runner.py`) esce dalla pre-mappa ed è un servizio comune (vedi «Servizi comuni»).
- **Chi riconosce è uno solo.** Uno strumento di build o un framework che il fork `stack-analyser` non conosce si aggiunge al fork. In Daodan `daodan/data/build-tools.json` lega ogni voce dello stack all'adattatore di `find_modules` che la usa.
- **Che cosa usa ogni step**, per linguaggio, strumento di build e framework: `docs/pipeline/`, generata dalle dichiarazioni del codice (`daodan/core/pipeline_tree.py`).

### Strumenti nativi, Noir e sorgenti dedicate

**Noir** è lo scanner di rotte che gira nel container (`premap/noir.py`).

| Famiglia | Esempi | Che cosa dà | Step |
| --- | --- | --- | --- |
| Strumento di build | cargo, gradle, maven, npm, `tsc`, cmake, meson, bazel, make, `dotnet`, uv, go | Moduli, unità, pacchetti risolti, comandi | `find_modules` |
| Strumento / introspezione del framework | `next typegen`, `react-router routes`, `nuxt prepare`, `svelte-kit sync`, compilatori Angular/Astro, sorgenti **Django, FastAPI, Flask** `[deciso]` *(verifica aperta: `B1` nel piano)* | Rotte, pagine, eventi dei template | `find_entry_points` |
| Compilatore del linguaggio (via SCIP) | TypeScript, Pyright, Java (Maven/Gradle), rust-analyzer, Clang | Risoluzione dei destinatari di chiamata (primo adattatore dietro il modello di evidenza interno) | `link_calls` |
| Esecutore dell'interfaccia e osservazione runtime | browser (Playwright/Chromium), webview (CDP/WebDriver), backend standard per tipo di evidenza (`sys.monitoring`, V8 coverage, OpenTelemetry, `strace`/eBPF) o registratori `*_record.*` *(verifica aperta: `M6` nel piano)* | Quale controllo fa partire quale funzione, archi osservati e frontiere | `run_and_observe` |

- **Framework senza strumento proprio:** letti dall'albero sintattico (tree-sitter) con query in `daodan/data/entry-queries.json` (es. `onClick` in React).
- **Convivenza tra sorgente dedicata e Noir in `find_entry_points`:** quando il container è disponibile e l'introspezione ufficiale del framework riesce, la sorgente dedicata è **primaria**; Noir funge da integrazione/ripiego statico con provenienza dichiarata. Unione deduplicata su chiave che includa contesto/mount/router dove serve; eventuali conflitti restano in diagnostica. A introspezione fallita Noir fa da ripiego, con il motivo dichiarato. Senza container non girano né la sorgente dedicata né Noir: restano le query tree-sitter, che girano sull'host, e una lacuna. Un'introspezione riuscita con 0 ingressi non è un errore.
- **Modello di evidenza in `link_calls` `[deciso]` *(verifica aperta: `M5` nel piano)*:** un riferimento SCIP non equivale a una chiamata (es. in `f(g)` solo `f` è chiamato). Tree-sitter individua il sito di chiamata; SCIP agisce come primo adattatore risolutore dietro un piccolo modello di evidenza interno (`sito`, `candidati`, `fonte`, stato `risolto`/`ambiguo`/`ignoto`). Nessuna migrazione a LSIF/LSP; compiler API dedicate solo dove SCIP mostra lacune misurate.
- **Osservazione runtime in `run_and_observe` *(verifica aperta: `M6` nel piano)*:** i backend standard si scelgono per tipo di evidenza (`sys.monitoring` su Python 3.12+ per call events; V8 per copertura, non call graph; OpenTelemetry per frontiere/span; `strace`/eBPF solo processi/rete). Gli hook custom `*_record.*` si ritirano solo dopo prova di equivalenza e overhead.
- **Un controllo ha due prove:** quella statica (legato a una funzione) e quella dinamica (azionato, quella funzione parte).

### Chiamate HTTP e punti di connessione

- **Chi offre la rotta:** strumento del framework o Noir (`find_entry_points`).
- **Chi la chiama:** compilatore del linguaggio fino a una funzione di `daodan/data/http-clients.json` (`link_calls`). Un wrapper del progetto si prova dai dati del compilatore, non dal nome.
- **Unione:** in `assemble_graph` dove percorso e metodo coincidono. Lo stesso vale per eventi, code e tabelle: un adattatore per tipo di legame, senza nominare framework nel codice dei legami.

### Superfici attive e regole comuni

Un'interfaccia nasce da un ingresso, non da un manifesto. Il campo `surface` dell'anagrafica decide con che cosa `run_and_observe` la esegue (non ancora nel codice; assegnato a `T3.B` nel piano):

- **`web`** (attiva): Chromium senza interfaccia con Playwright (albero di accessibilità, azionamento controlli, registrazione funzioni partite).
- **`webview`** (attiva in T3): Electron (CDP), Tauri e Wails (WebDriver) su `Xvfb`. Dove manca il driver si esercita la sola pagina e lo si dichiara.
- **Superfici differite** (`desktop` Linux, GUI Python, `android`, `windows`): finché non implementate emettono la lacuna `ui_execution_deferred:<superficie>` (non ancora nel codice; assegnata a `T3.B` nel piano). macOS e iOS restano fuori perimetro.

Regole valide per tutte le superfici: nulla dell'host; download con licenza o di qualche GB solo dopo consenso esplicito (altrimenti `approval_required`, non ancora nel codice; assegnata a `T1.D` e `T3.A` nel piano); solo dati e credenziali di prova già preparati dalla CI del progetto; progetti multipiattaforma eseguiti sul bersaglio `web` quando dichiarato.

### Come si sa che cosa lanciare (test, avvio, build)

Un comando non si indovina mai: viene da una fonte, e porta scritto da quale. Senza fonti il passo è una lacuna.

| Fonte | Che cosa dice | Grado | Stato |
| --- | --- | --- | --- |
| L'utente | Comando scritto da chi conosce il progetto, tenuto nell'archivio di Daodan (mai nel progetto) | `confermato` | Proposta (da confermare prima di `T3.B`) |
| Lo strumento di build | Comando previsto dallo strumento (`npm test`, `go test`, `cargo test`, Gradle/Maven, `dotnet test`, CTest) | `dichiarato` | Nel codice |
| I file del progetto | Script `test`/`start`/`dev`, config pytest, makefile (vale per il runner lanciato, non per il nome) | `dichiarato` | Nel codice |
| La CI del progetto | Passo dei test in CI, con servizi e passi preliminari | `dichiarato` | Parziale (`T3.B`) |

## Nodi del grafo: tipo e logo

L'anagrafica delle tecnologie (`daodan/data/service-registry.json`) dà a ogni framework, libreria, strumento e servizio un tipo di nodo e, dove la voce li ha, una categoria e un logo (`recognize_stack` e `find_modules` attribuiscono le tecnologie ai moduli; `assemble_graph` costruisce i nodi del grafo). Senza `category`, una voce di `kind` `service` vale `service` e le altre `framework`. Il tipo di nodo è `type` nell'anagrafica e `node_type` sul nodo. Il grafo consulta l'anagrafica, senza nominare tecnologie nel codice.

Ogni voce dice il suo `support`, calcolato da `registry_build.support` e mai scritto a mano. `none`: il fork non ha una regola per la voce, quindi nessun progetto la mostra. Un servizio o uno strumento chiede solo di essere riconosciuto: con una regola è `full`, perché il grafo ha il suo nodo e le frecce che ci arrivano. Un framework o una libreria è `full` quando un lettore di Daodan legge come il progetto lo usa (rotte, eventi dei template, stili: la tabella `READERS`), `partial` quando è riconosciuto e basta. Una sorgente scritta e scollegata non conta: Django, FastAPI e Flask sono `partial` finché non entrano in `find_entry_points`.

| Che cosa | Nel grafo | Tipo di nodo |
| --- | --- | --- |
| Voce con `category: service` che un file dichiara | Nodo esterno con il logo della voce; arco `uses` da ogni file che la mostra (`uncertain` dove la menziona soltanto). Una voce solo menzionata nel progetto non è un nodo | `type` della voce |
| Voce con `category: framework` o `library` | Non è un nodo: sta nel gruppo i cui file la dichiarano, con il suo logo. Il gruppo porta il logo del framework quando ne dichiara uno solo | — |
| Voce con `category: tool` | Non è un nodo, e nel grafo dell'app non è fra le tessere del gruppo; il modulo la elenca nel campo `tools` dell'involucro (`daodan/core/visual.py`) | — |
| Modulo esterno dichiarato dal progetto | Nodo esterno; se ha l'id di una voce con `category: service`, prende tipo e logo della voce | `servizio o API` |
| Funzione di una rotta; funzione che lega un'azione dell'utente | Il simbolo, se non ha già un tipo | `servizio o API`; `schermata` |
| Store | Nodo `store` | `node_type` della regola di collegamento |

- **Tipi di nodo:** elenco chiuso `NODE_TYPES` (`daodan/core/flows.py`): `attore`, `schermata`, `funzionalità`, `servizio o API`, `gateway`, `database`, `coda`, `autenticazione`, `dispositivo`, `filesystem`, `altro`. La mappa di sistema aggiunge `entità`, `applicazione` e `lavoro a orario` (`daodan/core/system_map.py`). Un nodo di cui non si sa il tipo non ne ha.
- **Tipo di framework, librerie e strumenti:** l'anagrafica lo dà anche a loro dove la tecnologia lo determina: è ciò che più plausibilmente è la parte di programma costruita con essa; dove non lo dice resta `altro`. Questi tipi stanno in `daodan/data/registry-additions.json` con `by: model` e non sono verificati a campione.
  - **Oggi nel codice:** il grafo non li usa. Un nodo prende il tipo dall'anagrafica solo se la voce ha `category: service` (`daodan/core/visual.py`); delle altre voci il tipo viaggia nell'elenco `technologies`, e il pannello dei dettagli lo mostra come testo nell'elenco delle tecnologie (`viewer/src/details.tsx`). Il brief del mappatore (`daodan/core/system_brief.py`, sezione Externals) stampa invece il tipo di ogni tecnologia riconosciuta, `altro` dove manca (`technologies.externals`).
  - **Scelta aperta (tracciata nel piano, `T1`):** se un modulo prende il tipo del suo framework.
- **Logo di una tecnologia:** una tessera di Daodan in `daodan/data/marks/`; i servizi di AWS, Azure e Google Cloud hanno pittogrammi di Daodan.
- **Senza logo:** il nodo ha l'icona del suo tipo (`viewer/src/icons.ts`). `filesystem` e `altro` prendono quella dell'entità, `funzionalità` nessuna.
- **Mappa di sistema:** i suoi nodi esterni portano l'id dell'anagrafica (`registry`), ma oggi la vista (`system_levels.view`) non passa il logo (allineamento tracciato nel piano, `T2.C`).

## Il piano: completo nei vincoli, incrementale nelle azioni

Un solo oggetto condiviso tra interfaccia, MCP e riga di comando (il giornale degli eventi resta come cronaca).

1. **Completo nei vincoli prima dell'avvio:** prima che parta qualunque cosa, il piano espone tutti gli step, le politiche, i permessi e le condizioni di arresto.
2. **Incrementale nelle azioni concrete:** le azioni che dipendono dalla scoperta (moduli, download, build, suite di test, avvio app) vengono aggiunte e aggiornate nello stesso piano man mano che gli step `recognize_stack`, `find_modules` e `find_entry_points` le determinano. Se emerge un'azione che richiede consenso (download pesante, licenza) o eccede i permessi, l'esecuzione si ferma su quell'azione; per un host da approvare vale «Servizi comuni».
3. **Dice che cosa fa, non come:** frasi leggibili («lancia i test di `api`»), con strumento/comando/versione come dettaglio apribile. Ogni azione indica bersaglio e tre fatti: se esegue codice del progetto, se gira nel container, se scarica dalla rete e quanto pesa.
4. **Stato per azione** aggiornato in tempo reale: `da fare`, `in corso`, `fatta`, `fallita`, `saltata` (già fresca), `non possibile` (con causa e rimedio), `in attesa di approvazione` (un suo host attende la risposta di una persona). Tipi di azione da elenco chiuso.

## L'interfaccia segue la pipeline

La UI (solo componenti Sigrid nella shell Imago) legge il piano e i risultati degli step senza ricostruirli dagli eventi e senza tenere elenchi propri di fasi. Mostra gli otto step con i loro risultati, i consensi prima dell'esecuzione, l'azione in corso e le lacune. Un host da approvare («Servizi comuni») è una notifica e un popup con host, porta, indirizzo risolto e il file che lo dichiara; un tentativo verso un host in blacklist è solo una notifica. Le parole interne («pre-mappa», «scan», «stack», «analyze») escono dall'interfaccia.

## Le anagrafiche (`daodan/data/`)

Ogni anagrafica deve avere un controllo automatico di coerenza con il codice:

| Anagrafica | Contenuto | Chi la usa | Stato |
| --- | --- | --- | --- |
| `file-formats.json` | Formati accettati, linguaggi, cartelle/nomi esclusi | `list_files` | Nel codice |
| `linguist-catalog.json` | Nomi Linguist per ogni formato accettato | `list_files` | Nel codice |
| `language-rules.toml` | Regole di disambiguazione estensioni condivise | `list_files` | Nel codice (mancano `.h` e nomi file) |
| `service-registry.json`, `registry-additions.json`, `marks/` | Di ogni tecnologia nome, `kind` (`service`, `project`), tipo di nodo e sito; `support` (`full`, `partial`, `none`); dove ci sono, `category` (`framework`, `library`, `tool`, `service`) e logo (+ `surface`) | `recognize_stack`, il grafo, UI | Nel codice (senza `surface`) |
| `build-tools.json` | Strumenti di build/toolchain -> adattatore | `find_modules` | Da creare (T1) |
| `package-managers.json` | Registri pacchetti consentiti nella preparazione | Preparazione container | Nel codice |
| `entry-queries.json` | Query tree-sitter per ingressi | `find_entry_points` | Nel codice |
| `http-clients.json` | Client HTTP come nominati dal compilatore | `link_calls`, `assemble_graph` | Nel codice |

## Servizi comuni

- **Motore di container:** isola sempre il codice del progetto. Su Windows è il **Kiri** di Daodan, in una distribuzione WSL 2 propria; altrove è quello dell'utente (`docker`, poi `podman`).
- **Preparazione (una per analisi):** toolchain (`mise`), dipendenze ripristinate via proxy, strumenti verificati per sha256; tutto il resto gira senza rete. Il parser dei lockfile resta un controllo preventivo, non il confine di isolamento.
  - **Nel codice** (`daodan/core/container.py`): esecuzione con `--network none`; preparazione su una rete interna con il proxy (`container.PROXY_SCRIPT`) come sola uscita; `--security-opt no-new-privileges`. Il proxy apre senza chiedere i registri di `package-managers.json`, gli host fissi degli strumenti (`premap/container_runner.py`, `preparation.py`) e gli host che il progetto dichiara, fra cui quelli delle sue dipendenze (`preparation.declared`), dei requisiti Python da Git (`preparation.python_vcs`) e, al secondo tentativo di Gradle, dei repository della build. Non passa `--cap-drop` né `--user`. La prova su un container vero è nel piano (`T3.A`, salvo anticipo in `T0.B.2a` per `M1/I1`).
- **Uscita di rete con approvazione `[deciso]`** (non ancora nel codice; assegnata a `T3.A` nel piano, con esposizione dello stato di attesa nel piano unico in `T1.D`). Sostituisce «solo proxy verso registri autorizzati» e ritira l'apertura «come una CI» degli host dichiarati.
  - **Confine:** nessuna uscita diretta dal container di analisi; il controllo sta fuori, nel proxy, unica uscita (inclusi redirect, DNS e IP letterali).
  - **In whitelist:** passa senza chiedere. Sono gli host canonici (`daodan/data/package-managers.json`: i gestori dell'elenco di Wikipedia, con gli host scritti a mano e provati da `benchmarks/registry-hosts/`) e quelli approvati dall'utente.
  - **In blacklist:** rifiutato subito; solo una notifica del tentativo, nessun popup.
  - **Ogni altro host** (anche dichiarato dal progetto o assegnato da Daodan a uno strumento): notifica e popup, e l'utente deve approvare. Il proxy rifiuta subito, e dopo il sì il passo si rilancia; gli host dichiarati si chiedono prima che il passo parta. Se il passo riesce comunque con un host rifiutato, il risultato vale e la richiesta resta visibile. Il popup mostra l'indirizzo risolto e segnala quando è una macchina della rete dell'utente.
  - **Risposte:** «sempre per questo progetto», «solo per questa analisi», «no», «blocca sempre» (va in blacklist). Whitelist e blacklist stanno nella cartella condivisa di Daodan, mai nel progetto.
  - **Si approva solo dalla GUI.** MCP e riga di comando mostrano le richieste in attesa e non approvano mai: il modello legge il progetto analizzato, e un client MCP che è un agente può rispondere da sé a una elicitation.
  - **Lacune:** `approval_required` senza risposta o senza schermo; `host_denied` dopo un no o per un host in blacklist.
  - **Strumento del proxy:** lo sceglie una prova su Modal fra Smokescreen e il proxy attuale esteso, sugli stessi criteri: solo porta 443, eccezione apt, whitelist e blacklist da file, rifiuti leggibili con l'indirizzo risolto.
- **Lanciatore dei comandi:** servizio comune a `find_modules`, `find_entry_points`, `link_calls` e `run_and_observe`.
- **Giornale:** traccia inizio, avanzamento, lacune e fine di ogni step e adattatore.
- **Secretlint:** ogni testo che lascia la macchina o va a un LLM passa prima da Secretlint. **Nel codice:** `secret_mask`, che lo lancia, è chiamato da `daodan/core/app.py` (risultati degli strumenti e prompt) e da `daodan/core/mcp_server.py` (risultati ed errori).

## Termini

- **Cartella condivisa:** la cartella di Daodan sulla macchina, fuori da ogni progetto, dove stanno gli strumenti installati al primo uso (`embedding_worker.shared_cache_dir`).
- **Host fisso, host dichiarato:** fisso è quello che il codice di Daodan assegna a uno strumento; dichiarato è quello che i file del progetto nominano per dipendenze o build.
- **Kiri:** il motore di container che Daodan porta su Windows, in una distribuzione WSL 2 propria (`daodan/core/container.py`).
- **Noir:** lo scanner di rotte OWASP Noir, che gira nel container (`daodan/core/premap/noir.py`).
- **Fork `stack-analyser`:** il riconoscitore delle tecnologie, un fork di quello di Specfy (`daodan/core/stack_analyser.py`).
- **Pre-mappa:** nel disegno il modello di build, uscita di `find_modules`; oggi `daodan/core/premap/` tiene anche rotte ed eventi.
- **Smokescreen:** il proxy di uscita di Stripe, candidato a proxy della preparazione.
- **SCIP:** il formato di indice del codice di un intero progetto, che `daodan/core/code_graph.py` legge come un grafo.
- **Store:** ciò a cui il codice accede in scrittura o lettura, nominato con la sua chiave da una regola di collegamento (`daodan/core/flows.py`).
- **Tessera:** il logo di una tecnologia dentro la cornice di Daodan.
