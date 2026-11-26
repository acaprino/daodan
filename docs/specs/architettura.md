# Daodan: architettura e contratto della pipeline

**Stato:** contratto di arrivo (estratto dal refactoring del 25 novembre 2026). Descrive *com'è Daodan a refactoring finito*. Il lavoro attivo è in [`docs/plans/refactoring.md`](../plans/refactoring.md); tutto ciò che è differito o ritirato è in [`docs/backlog.md`](../backlog.md) (non normativo). Le 19 spec e i 13 piani precedenti sono nella storia di git al commit `614c940`.

**Legenda:** `[deciso]` è una scelta approvata dal proprietario. Nella colonna «Stato»: «Nel codice» c'è oggi, «Parziale» c'è in parte, «Da creare» non c'è, «Proposta» non è mai stata approvata; fra parentesi il traguardo del piano.

## Il problema

`[deciso]` Oggi in Daodan ci sono confusione, errori e incongruenze nell'ordine in cui avvengono i passi, duplicazioni e ripetizioni, inefficienze e passi con troppi compiti. Il codice prova a riconoscere cose che non può e non deve riconoscere, con troppo codice scritto sul singolo caso (overfitting) e incoerente. C'erano anche troppe spec e troppi piani che si sovrapponevano, e troppe sessioni di lavoro. Occorreva fare il punto della situazione e ripartire. Abbiamo quindi pulito, riordinato e unificato i documenti: una spec e un piano. Il codice segue, con il piano.

`[deciso]` **Obiettivo del refactoring:** punti chiari e moduli con una sola responsabilità, così sappiamo chi fa che cosa, quando e come.

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
| 1 | `list_files` | L'elenco dei file | Cartella e perimetro: da chi avvia | Di ogni file percorso, dimensione, hash e linguaggio; quanti file non legge, per linguaggio, come lacuna |
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
| Strumento / introspezione del framework | `next typegen`, `react-router routes`, `nuxt prepare`, `svelte-kit sync`, compilatori Angular/Astro | Rotte, pagine, eventi dei template | `find_entry_points` |
| Compilatore del linguaggio (via SCIP) | TypeScript, Pyright, Java (Maven/Gradle), rust-analyzer, Clang | Risoluzione dei destinatari di chiamata (primo adattatore dietro il modello di evidenza interno) | `link_calls` |
| Esecutore dell'interfaccia e osservazione runtime | browser (Playwright/Chromium), webview (CDP/WebDriver), registratori `*_record.*` per le chiamate; per le frontiere OpenTelemetry, da valutare | Quale controllo fa partire quale funzione, archi osservati e frontiere | `run_and_observe` |

- **Metodo di GitNexus `[deciso]`:** dove nessuno strumento ufficiale dà il dato (le rotte di Express), il lettore è un modulo nostro riscritto da capo, che segue gli aggiornamenti di GitNexus senza copiarne il testo (non ancora nel codice; `T1.C`).
- **Django, FastAPI e Flask `[deciso]`:** nessuna sorgente dedicata; le rotte vengono da Noir e dalle query tree-sitter.
- **Framework senza strumento proprio:** letti dall'albero sintattico (tree-sitter) con query in `daodan/data/entry-queries.json` (es. `onClick` in React).
- **Convivenza tra sorgente dedicata e Noir in `find_entry_points`:** quando il container è disponibile e l'introspezione ufficiale del framework riesce, la sorgente dedicata è **primaria**; Noir funge da integrazione/ripiego statico con provenienza dichiarata. Unione deduplicata su chiave che includa contesto/mount/router dove serve; eventuali conflitti restano in diagnostica. A introspezione fallita Noir fa da ripiego, con il motivo dichiarato. Senza container non girano né la sorgente dedicata né Noir: restano le query tree-sitter, che girano sull'host, e una lacuna. Un'introspezione riuscita con 0 ingressi non è un errore.
- **Modello di evidenza in `link_calls` `[deciso]`:** un riferimento SCIP non equivale a una chiamata (es. in `f(g)` solo `f` è chiamato). Tree-sitter individua il sito di chiamata; SCIP agisce come primo adattatore risolutore dietro un piccolo modello di evidenza interno (`sito`, `candidati`, `fonte`, stato `risolto`/`ambiguo`/`ignoto`). Nelle strutture di oggi `sito` è il riferimento dello snapshot, `candidati` sono le righe `uncertain`, `fonte` è il campo `resolver`, `ignoto` sono i `holes`: nessun campo nuovo. Nessuna migrazione a LSIF/LSP; compiler API dedicate solo dove SCIP mostra lacune misurate.
- **Osservazione runtime in `run_and_observe` `[deciso]`:** le chiamate le registrano i `*_record.*` (Python usa già `sys.monitoring`); per le frontiere si valuta OpenTelemetry prima di scrivere codice.
- **Un controllo ha due prove:** quella statica (legato a una funzione) e quella dinamica (azionato, quella funzione parte).

### Chiamate HTTP e punti di connessione

- **Chi offre la rotta:** strumento del framework o Noir (`find_entry_points`).
- **Chi la chiama:** compilatore del linguaggio fino a una funzione di `daodan/data/http-clients.json` (`link_calls`). Un wrapper del progetto si prova dai dati del compilatore, non dal nome.
- **Unione:** in `assemble_graph` dove percorso e metodo coincidono. Lo stesso vale per eventi, code e tabelle: un adattatore per tipo di legame, senza nominare framework nel codice dei legami.

### Superfici attive e regole comuni

`[deciso]` Daodan deve saper avviare qualsiasi tipo di applicazione, anche grazie agli strumenti di build e alle toolchain riconosciuti: nessun linguaggio è privilegiato. Ciò che non sa ancora avviare, o non può, lo dice come lacuna.

Un'interfaccia nasce da un ingresso, non da un manifesto. Il campo `surface` dell'anagrafica decide con che cosa `run_and_observe` la esegue (non ancora nel codice; assegnato a `T3.B` nel piano):

- **`web`** (attiva): Chromium senza interfaccia con Playwright (albero di accessibilità, azionamento controlli, registrazione funzioni partite).
- **`webview`** (attiva in T3): Electron (CDP), Tauri e Wails (WebDriver) su `Xvfb`. Dove manca il driver si esercita la sola pagina e lo si dichiara.
- **Superfici differite** (`desktop` Linux, GUI Python, `android`, `windows`): finché non implementate emettono la lacuna `ui_execution_deferred:<superficie>` (non ancora nel codice; assegnata a `T3.B` nel piano). macOS e iOS restano fuori perimetro.

Regole valide per tutte le superfici: nulla dell'host; download con licenza o di qualche GB solo dopo consenso esplicito (altrimenti `approval_required`, non ancora nel codice; il nome nasce in `T0.C` e compare nel piano unico in `T1.D`); solo dati e credenziali di prova già preparati dalla CI del progetto; progetti multipiattaforma eseguiti sul bersaglio `web` quando dichiarato.

### Come si sa che cosa lanciare (test, avvio, build)

Un comando non si indovina mai: viene da una fonte, e porta scritto da quale. Senza fonti il passo è una lacuna.

| Fonte | Che cosa dice | Grado | Stato |
| --- | --- | --- | --- |
| L'utente | `[deciso]` Comando impostato in Daodan da chi conosce il progetto, tenuto nell'archivio di Daodan (mai nel progetto). *Proposta:* si imposta solo dalla GUI, come le approvazioni, perché un client MCP può essere un agente | `confermato` | Da creare (`T3.B`) |
| Lo strumento di build | Comando previsto dallo strumento (`npm test`, `go test`, `cargo test`, Gradle/Maven, `dotnet test`, CTest) | `dichiarato` | Nel codice |
| I file del progetto | Script `test`/`start`/`dev`, config pytest, makefile (vale per il runner lanciato, non per il nome) | `dichiarato` | Nel codice |
| La CI del progetto | Passo dei test in CI, con servizi e passi preliminari | `dichiarato` | Parziale (`T3.B`) |

## La mappa: nodi, nature e profondità

`[deciso]` La mappa non ha limiti di nodi: possono essere 2 o 80.000. Si legge in due versi. In verticale, per **profondità**: si parte da un grafo semplice, che dice come funziona il sistema ad alto livello, e si scende di nodo in nodo aprendo un padre (drill down) o richiudendolo (drill up). In orizzontale, per **natura**: si mettono in vista tutti e soli i nodi di una o più nature.

### Che cos'è un nodo

Una cosa del sistema con un nome e un identificativo stabile. Oggi i nodi stanno in due archivi: l'involucro del codice (`daodan/visual@1`: moduli, cartelle, file, simboli, store, esterni) e la mappa di sistema (`daodan/system-map/v1`: le cose con il nome che dà una persona). Sono una mappa sola: i `members` di un nodo della mappa di sistema sono nodi dell'involucro. I nodi del grafo li costruisce `assemble_graph`; le tecnologie e i file che le dichiarano vengono da `recognize_stack` e `find_modules`. *Parziale: l'unione serve oggi un flusso alla volta (`system_levels.py`).*

### Proprietà

| Proprietà | Valori | Oggi nel codice |
| --- | --- | --- |
| Specie: che cosa è | Elenco chiuso: attore, applicazione, schermata; funzionalità, servizio o API, gateway, autenticazione, lavoro a orario, altro; entità, store; modulo, cartella, file, simbolo; database, coda, filesystem, dispositivo, container, servizio in esecuzione, rete; tecnologia; gruppo | Parziale: `type` dell'involucro e `type` della mappa di sistema, con le stesse parole; container, servizio in esecuzione e rete da creare |
| Natura `[deciso]`, anche più d'una `[deciso]` | persone, logico, dati, codice, fisico (elenco approvato dal proprietario il 26 novembre 2026). `[deciso]` **Fisico** è dove le cose girano e ogni apparecchio: server, container, database, terminali, PC, smartphone, dispositivi hardware di ogni tipo; cartelle e file sono codice. Non si scrive: si ricava da specie e posizione | Parziale: `system_levels.levels_of`, con cinque livelli; l'app ne costruisce due |
| Concreto o astratto `[deciso]` (la definizione è proposta) | Concreto: c'è una cosa da indicare (un file, una riga, una risorsa dichiarata, un servizio di altri). Astratto, o sintetico: un nome che riassume altre cose | Parziale: solo sui moduli (`nature`: `concrete`, `logical`, `virtual`); altrove da creare, dalla specie |
| Padre | Uno solo, o nessuno; i figli sono l'inverso. Un cerchio di padri è rifiutato | Nel codice: `inside` nella mappa di sistema, `memberships` nell'involucro |
| Posizione | interno (ha codice nel progetto), esterno (è di altri), non visto (è del sistema ma i suoi file sono altrove: dice dove) | Parziale: `position`; l'involucro ha solo interno ed esterno |
| Provenienza e stato | Chi lo dice (strumento di build, progetto, modello, Daodan, catalogo) e con quale stato (confermato, dedotto, incompleto), sempre con il file che lo prova. «Osservato, provato, dichiarato» sono gradi delle frecce | Parziale: `provenance`, `status`, `evidence` |
| Tipo `[deciso]` | Lo ha solo il nodo legato a una voce del catalogo, ed è il tipo della voce. Non ogni nodo ha un tipo | Parziale: `node_type` e `registry`. Da cambiare: la mappa di sistema lo chiede a ogni nodo, e la funzione di una rotta o di un controllo ne riceve uno |

Natura per specie: **persone** (attore, applicazione, schermata); **logico** (funzionalità, servizio o API, gateway, autenticazione, lavoro a orario, altro); **dati** (entità, store); **codice** (modulo, cartella, file, simbolo; tecnologia di categoria framework, libreria o strumento); **fisico** (database, coda, filesystem, dispositivo, cioè terminale, PC, smartphone e ogni altro hardware, container, servizio in esecuzione, rete). Un servizio esterno è logico e fisico. Un gruppo ha la natura di ciò che contiene. Una natura senza nodi si dichiara assente.

### Profondità: aprire e richiudere

- `[deciso]` Il primo grafo è semplice: sono i nodi senza padre.
- `[deciso]` Aprire un nodo mostra i suoi figli al suo posto; il resto resta com'è. Richiudere riporta al nodo. *Nel codice per moduli, cartelle, file e simboli (`app_view.view`).*
- Un nodo senza figli si apre su ciò che lo realizza: una funzionalità sui suoi file. Richiudere riporta alla funzionalità, non alla cartella. *Parziale (`system_levels.inside`).*
- Si legge solo ciò che si apre: il primo grafo non legge i simboli di nessun file, e un simbolo compare solo dentro il suo file aperto. *Nel codice.*

### Corrispondenze

Legano nodi di nature diverse che sono la stessa cosa: «realizzato da» (una funzionalità e i suoi file: `members`), «gira su» (un modulo e il suo container: `on`), «vive in» (un'entità e il suo database). Ognuna cita il file che la prova. È **un nodo solo** con più nature quando la cosa è una, con un nome solo (Stripe); sono **due nodi** con una corrispondenza quando ogni natura ha nome, padre o figli suoi (la cartella `api/` e il container `api`). Lo stesso nodo può realizzarne più d'uno: si vede in ciascuno, e il suo padre resta uno. *Parziale: `members` e `on` nella mappa di sistema.*

### Filtro per natura

`[deciso]` Si vede il grafo estrapolando, evidenziando tutti e soli i nodi di una o più nature. I due modi qui sotto sono la lettura proposta di queste parole. Il filtro non apre mai un gruppo da solo.

- **Evidenziare:** gli altri nodi si attenuano; un gruppo chiuso che contiene nodi della natura scelta si accende e dice quanti. *Da creare; non chiede calcoli nuovi.*
- **Estrarre:** restano solo quei nodi e le frecce passano attraverso gli altri. *Parziale: per un flusso alla volta (`system_levels.view`); sull'intero grafo da creare.*

### Frecce riassunte

- Chiuso un gruppo, le frecce di ciò che contiene salgono su di lui: una freccia per coppia di nodi in vista e per grado, con il numero dei collegamenti per tipo e fino a 20 punti citati. Aprirlo le sostituisce con le frecce che le compongono.
- Il riassunto non promuove mai: una freccia incerta, osservata o solo dichiarata resta distinta, e le lacune restano.
- Le frecce interne a un gruppo chiuso non si disegnano: si contano sul gruppo. *Nell'esploratore sì; l'app oggi non le conta.*
- Un nodo in vista in due posti porta le sue frecce in entrambi; i totali contano ogni collegamento una volta.

*Parziale: `app_view._edges`, `viewer/src/projection.ts`, `system_levels._contract`.*

### Nessun limite

- `[deciso]` Nessun tetto al numero di nodi, né minimo né massimo.
- Nessun taglio in silenzio: un tetto di calcolo è una lacuna, con il numero di ciò che resta fuori. *Nel codice: gli elenchi oltre 1.000 voci si dividono; le frecce che attraversano nodi nascosti si fermano a 2.000 passi, con la lacuna.*
- Alla pagina: si disegna solo ciò che è aperto e in vista. La vista la calcola il servizio, che manda solo quei nodi e le loro frecce: la pagina non riceve mai l'intero grafo. *Parziale: l'app sì (`app_view.view`); l'esploratore carica tutto l'involucro. La pagina è nel piano in `T2.D`.*
- Un gruppo con più figli di quanti la vista ne regge si apre a blocchi, con un nodo sintetico «altri N». *Da creare.*
- Al calcolo: il costo di una vista cresce con ciò che mostra, non con il totale dei simboli. *Parziale: non misurato su un progetto grande.*
- Misura che manca: tempo e peso di una vista con 80.000 nodi in archivio e 300 in vista. Prima del passaggio a Sigrid, 300 nodi in vista chiedevano 4,6 s e 1.000 non si disponevano (`benchmarks/codebase-explorer/README.md`).

### Le tecnologie come nodi

L'anagrafica delle tecnologie (`daodan/data/service-registry.json`) dà a ogni voce nome, categoria (`framework`, `library`, `tool`, `service`), tipo e, dove c'è, logo. Senza `category`, una voce di `kind` `service` vale `service` e le altre `framework`. Il grafo consulta l'anagrafica, senza nominare tecnologie nel codice. I tipi di framework, librerie e strumenti stanno in `registry-additions.json` con `by: model` e non sono verificati a campione.

Ogni voce dice il suo `support`, calcolato da `registry_build.support` e mai scritto a mano. `none`: il fork non ha una regola per la voce, quindi nessun progetto la mostra. Un servizio o uno strumento chiede solo di essere riconosciuto: con una regola è `full`, perché il grafo ha il suo nodo e le frecce che ci arrivano. Un framework o una libreria è `full` quando un lettore di Daodan legge come il progetto lo usa (rotte, eventi dei template, stili: la tabella `READERS`), `partial` quando è riconosciuto e basta. Una sorgente scritta e scollegata non conta: Django, FastAPI e Flask sono `partial`.

- `[deciso]` Un modulo è collegato ai nodi di tutte le tecnologie che lo compongono, strumenti di sviluppo compresi, con una freccia «usa» che cita il file che le dichiara. Il nodo tecnologia è concreto, esterno, con il tipo e il logo della sua voce; uno per tecnologia e per progetto. *Da creare: oggi sono nodi solo le voci `service` (`visual.py`), framework e librerie sono tessere del modulo e uno strumento non compare (`app_view.py`, `TILES`).*
- Un servizio che un file dichiara è un nodo esterno, con una freccia `uses` da ogni file che lo mostra (`uncertain` dove lo menziona soltanto). Un modulo esterno dichiarato dal progetto è un nodo esterno; se ha l'id di una voce `service` ne prende tipo e logo. Uno store è un nodo di specie store. *Nel codice.*
- Una tecnologia solo menzionata non è un nodo; un pacchetto fuori dal catalogo resta contato sul modulo. *Nel codice; non deciso.*
- Un nodo di tecnologia resta nella mappa anche se nessun flusso lo usa.
- `[deciso]` Per tenere semplice il primo grafo, i servizi restano in vista accanto a chi li usa; framework, librerie e strumenti stanno sotto un nodo astratto «Tecnologie», che si apre. Il logo sul modulo resta la forma chiusa della freccia *(proposta)*.
- **Logo di una tecnologia:** una tessera di Daodan in `daodan/data/marks/`; i servizi di AWS, Azure e Google Cloud hanno pittogrammi di Daodan.
- **Senza logo:** il nodo ha l'icona della sua specie (`viewer/src/icons.ts`). `filesystem` e `altro` prendono quella dell'entità, `funzionalità` nessuna.
- **Mappa di sistema:** i suoi nodi esterni portano l'id dell'anagrafica (`registry`), ma oggi la vista (`system_levels.view`) non passa il logo (allineamento tracciato nel piano, `T2.C`).
- `[deciso]` **Due ingressi con lo stesso esito** sono due varianti di un solo flusso, che si apre per vederle (nel piano, `T3.C`).

## Il piano: completo nei vincoli, incrementale nelle azioni

Un solo oggetto condiviso tra interfaccia, MCP e riga di comando (il giornale degli eventi resta come cronaca).

1. **Completo nei vincoli prima dell'avvio:** prima che parta qualunque cosa, il piano espone tutti gli step, le politiche, i permessi e le condizioni di arresto.
2. **Incrementale nelle azioni concrete:** le azioni che dipendono dalla scoperta (moduli, download, build, suite di test, avvio app) vengono aggiunte e aggiornate nello stesso piano man mano che gli step `recognize_stack`, `find_modules` e `find_entry_points` le determinano. Se emerge un'azione che richiede consenso (download pesante, licenza) o eccede i permessi, l'esecuzione si ferma su quell'azione; per un host da approvare vale «Servizi comuni».
3. **Dice che cosa fa, non come:** frasi leggibili («lancia i test di `api`»), con strumento/comando/versione come dettaglio apribile. Ogni azione indica bersaglio e tre fatti: se esegue codice del progetto, se gira nel container, se scarica dalla rete e quanto pesa.
4. **Stato per azione** aggiornato in tempo reale: `da fare`, `in corso`, `fatta`, `fallita`, `saltata` (già fresca), `non possibile` (con causa e rimedio), `in attesa di approvazione` (un suo host attende la risposta di una persona). Tipi di azione da elenco chiuso.

## L'interfaccia segue la pipeline

*Nel piano in `T1.E`; il popup degli host in `T0.C`.*

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
  - **Nel codice** (`daodan/core/container.py`): esecuzione con `--network none`; preparazione su una rete interna con il proxy (`container.PROXY_SCRIPT`) come sola uscita; `--security-opt no-new-privileges`. Il proxy apre senza chiedere i registri di `package-managers.json`, gli host fissi degli strumenti (`premap/container_runner.py`, `preparation.py`) e gli host che il progetto dichiara, fra cui quelli delle sue dipendenze (`preparation.declared`), dei requisiti Python da Git (`preparation.python_vcs`) e, al secondo tentativo di Gradle, dei repository della build. Non passa `--cap-drop` né `--user`. La prova su un container vero è nel piano (`T0.C`).
- **Uscita di rete con approvazione `[deciso]`** (non ancora nel codice; nel piano è in `T0.C`, con lo stato di attesa nel piano unico in `T1.D`). Sostituisce «solo proxy verso registri autorizzati» e ritira l'apertura «come una CI» degli host dichiarati.
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
