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

- **La pre-mappa è il modello di build**, uscita di `find_modules`: non tiene più rotte, pagine ed eventi. Il lanciatore (`container_runner.py`) esce dalla pre-mappa; il servizio comune è `container.run_in_container` con `egress.preflight` (vedi «Servizi comuni»).
- **Chi riconosce è uno solo.** Uno strumento di build o un framework che il fork `stack-analyser` non conosce si aggiunge al fork. In Daodan `daodan/data/build-tools.json` lega ogni voce dello stack all'adattatore di `find_modules` che la usa.
- **Che cosa usa ogni step**, per linguaggio, strumento di build e framework: `docs/pipeline/`, generata dalle dichiarazioni del codice (`daodan/core/pipeline_tree.py`).

### Strumenti nativi, Noir e sorgenti dedicate

**Noir** è lo scanner di rotte che gira nel container (`entry_points/noir.py`).

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
- **Modello di evidenza in `link_calls` `[deciso]`:** un riferimento SCIP non equivale a una chiamata (es. in `f(g)` solo `f` è chiamato). Tree-sitter individua il sito di chiamata; SCIP agisce come primo adattatore risolutore dietro un piccolo modello di evidenza interno (`sito`, `candidati`, `fonte`, stato `risolto`/`ambiguo`/`ignoto`). Nelle strutture di oggi `sito` è il riferimento dello snapshot, `candidati` sono le righe `uncertain`, `fonte` è il campo `resolver`, `ignoto` sono i `holes`: nessun campo nuovo (misurato il 27 novembre 2026: zero falsi archi per indicizzatore su `benchmarks/inference-audit`; ciò che l'indice non decide va in `uncertain.reason`). Nessuna migrazione a LSIF/LSP; compiler API dedicate solo dove SCIP mostra lacune misurate.
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

Regole valide per tutte le superfici: nulla dell'host; download con licenza o di qualche GB solo dopo consenso esplicito (altrimenti `approval_required`, nel codice da `T0.C`: `egress.approval_gap`); solo dati e credenziali di prova già preparati dalla CI del progetto; progetti multipiattaforma eseguiti sul bersaglio `web` quando dichiarato.

### Come si sa che cosa lanciare (test, avvio, build)

Un comando non si indovina mai: viene da una fonte, e porta scritto da quale. Senza fonti il passo è una lacuna.

| Fonte | Che cosa dice | Grado | Stato |
| --- | --- | --- | --- |
| L'utente | `[deciso]` Comando impostato in Daodan da chi conosce il progetto, tenuto nell'archivio di Daodan (mai nel progetto) | `confermato` | Da creare (`T3.B`) |
| L'assistente | `[deciso]` Anche un assistente (via MCP) può impostare il comando. Resta scritto che l'ha impostato un assistente; è `proposto`, non `confermato`. Gira solo nel container, e gli indirizzi di rete si approvano solo dalla GUI | `proposto` | Da creare (`T3.B`) |
| Lo strumento di build | Comando previsto dallo strumento (`npm test`, `go test`, `cargo test`, Gradle/Maven, `dotnet test`, CTest) | `dichiarato` | Nel codice |
| I file del progetto | Script `test`/`start`/`dev`, config pytest, makefile (vale per il runner lanciato, non per il nome) | `dichiarato` | Nel codice |
| La CI del progetto | Passo dei test in CI, con servizi e passi preliminari | `dichiarato` | Parziale (`T3.B`) |

## La mappa: nodi, nature e profondità

`[deciso]` La mappa non ha limiti di nodi: possono essere 2 o 80.000. Si legge in due versi. In verticale, per **profondità**: si parte da un grafo semplice, che dice come funziona il sistema ad alto livello, e si scende di nodo in nodo aprendo un padre (drill down) o richiudendolo (drill up). In orizzontale, per **natura**: si mettono in vista tutti e soli i nodi di una o più nature.

### Che cos'è un nodo

Una cosa del sistema con un nome e un identificativo stabile. Oggi i nodi stanno in due archivi: l'involucro del codice (`daodan/visual@1`: moduli, cartelle, file, simboli, store, esterni) e la mappa di sistema (`daodan/system-map/v1`: le cose con il nome che dà una persona). Sono una mappa sola: i `members` di un nodo della mappa di sistema sono nodi dell'involucro. I nodi del grafo li costruisce `assemble_graph`; le tecnologie e i file che le dichiarano vengono da `recognize_stack` e `find_modules`. *Parziale: l'unione serve oggi un flusso alla volta (`system_levels.py`).*

`[deciso]` Il file di progetto, con estensione `.daodan` (per esempio `negozio.daodan`), conserva in SQLite il grafo, i flussi e la loro storia. L’albero di contenimento e gli archi diretti hanno ruoli distinti. Nodi e archi hanno ID stabili. Per ogni revisione si distinguono la versione e la configurazione di Daodan, la versione dei sorgenti (commit e data, oppure impronta dei file analizzati se manca Git o ci sono modifiche locali; in quest’ultimo caso si conserva anche il commit di base, se disponibile) e la revisione interna di grafo e flussi. Un edit manuale registra autore, modifica e revisione di partenza. Alla rianalisi si mantengono gli edit compatibili; se cambia lo stesso campo in modo incompatibile si mostrano entrambe le versioni con la provenienza. Le modifiche di un file ricevuto da altri valgono come le altre: chi le ha fatte si vede nella cronologia del file ricevuto, che l’app mostra. Due copie dello stesso file, modificate ognuna per conto proprio, divergono. La sezione [File di progetto](#file-di-progetto) specifica le tabelle, le chiavi, la lettura storica e i vincoli di salvataggio. *Contratto del formato; da implementare nell’app.*

### Proprietà

| Proprietà | Valori | Oggi nel codice |
| --- | --- | --- |
| Specie: che cosa è | Elenco chiuso: attore, applicazione, schermata; funzionalità, servizio o API, gateway, autenticazione, lavoro a orario, altro; entità, store; modulo, cartella, file, simbolo; database, coda, filesystem, dispositivo, container, servizio in esecuzione, rete; tecnologia; gruppo | Nel codice: `node_model.SPECIES`, scritta su ogni entità dell'involucro (`species`) e ricavata dal `type` della mappa di sistema (`node_model.species_of`); container, servizio in esecuzione e rete senza nodi ancora |
| Natura `[deciso]`, anche più d'una `[deciso]` | persone, logico, dati, codice, fisico (elenco approvato dal proprietario il 26 novembre 2026). `[deciso]` **Fisico** è dove le cose girano e ogni apparecchio: server, container, database, terminali, PC, smartphone, dispositivi hardware di ogni tipo; cartelle e file sono codice. Non si scrive: si ricava da specie e posizione | Nel codice: `node_model.natures`, usata dai livelli della mappa di sistema (`system_levels`); l'app ne costruisce due (`codice`, `fisico`); i nomi vecchi (`funzioni`, `infrastruttura`) si accettano fino a `T2.D` |
| Concreto o astratto `[deciso]` | Concreto: c'è una cosa da indicare (un file, una riga, una risorsa dichiarata, un servizio di altri). Astratto, o sintetico: un nome che riassume altre cose senza una cosa sua da indicare, in particolare una funzionalità o un modulo che corrisponde a un insieme di funzionalità o responsabilità affini, o a una sola: per esempio «Gestione ordini», che logicamente è un macro-modulo astratto anche quando è composto da più microservizi, sotto-applicazioni o moduli concreti. Sono astratti anche attore ed entità: un attore come «Cliente» non è per forza una persona, può essere una società o un'organizzazione. La cartella o il pacchetto che realizza un modulo è concreto | Nel codice: `node_model.concrete`, scritto su ogni entità dell'involucro (`concrete`); per un modulo dalla sua concretezza nel grafo dei moduli (`nature` `logical` è astratto) |
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

`[deciso]` Si vede il grafo estrapolando, evidenziando tutti e soli i nodi di una o più nature. Si supportano tutti e due i modi. La scelta è un'impostazione con un interruttore, presente in ogni interfaccia che mostra la mappa: la GUI dell'app o la pagina HTML dinamica. La scelta resta salvata fra un'apertura e l'altra. Il filtro non apre mai un gruppo da solo.

- **Evidenziare:** gli altri nodi si attenuano; un gruppo chiuso che contiene nodi della natura scelta si accende e dice quanti. *Da creare; non chiede calcoli nuovi.*
- **Nascondere gli altri:** restano solo quei nodi e le frecce passano attraverso gli altri. *Parziale: per un flusso alla volta (`system_levels.view`); sull'intero grafo da creare.*

### Aprire, chiudere e filtrare senza disorientare

- `[deciso]` Aprire, chiudere o filtrare aggiorna il disegno che c'è, senza rifarlo da capo: i nodi che restano non si spostano più del necessario ([Dogrusoz e altri, 2018](https://doi.org/10.1371/journal.pone.0197238)). *Da creare (`T2.D`).*
- `[deciso]` Apri e chiudi e filtro si calcolano insieme, in un solo punto: applicati uno dopo l'altro da parti diverse danno viste incoerenti ([CMGV](https://doi.org/10.1177/14738716251383173)). *Da creare (`T2.C`).*

**Criteri di accettazione.** A parità di revisione, profilo, gruppi aperti, nature e modalità del filtro, invertire l’ordine dei comandi produce gli stessi nodi, archi, gradi, conteggi e riferimenti alle prove. Riaprire un gruppo col filtro attivo mostra solo i figli ammessi in modalità «nascondere». In modalità «evidenziare» gli altri restano visibili attenuati. In modalità «nascondere», se due nodi ammessi erano collegati attraverso un nodo nascosto, il dettaglio della freccia conserva i passaggi intermedi e le loro prove. Con spazio libero, aprire e richiudere un gruppo conserva l’ordine e la posizione dei nodi di un ramo disgiunto. Se occorre fare spazio si misura lo spostamento dei nodi esterni a parità di zoom e si mantiene il riferimento visivo al gruppo aperto.

### Vista compatta

`[deciso]` Una vista compatta mostra solo nodi piccoli, con logo e nome (dove non c'è un logo, l'icona della specie). *Da creare (`T2.D`).*

### Frecce riassunte

- Chiuso un gruppo, le frecce di ciò che contiene salgono su di lui: una freccia per coppia di nodi in vista e per grado, con il numero dei collegamenti per tipo e fino a 20 punti citati. Aprirlo le sostituisce con le frecce che le compongono.
- Il riassunto non promuove mai: una freccia incerta, osservata o solo dichiarata resta distinta, e le lacune restano.
- Le frecce interne a un gruppo chiuso non si disegnano: si contano sul gruppo. *Nell'esploratore sì; l'app oggi non le conta.*
- Un nodo in vista in due posti porta le sue frecce in entrambi; i totali contano ogni collegamento una volta.

*Parziale: `app_view._edges`, `viewer/src/projection.ts`, `system_levels._contract`.*

### Seguire un flusso attraverso i gruppi

- `[deciso]` Ogni freccia riassunta permette di risalire agli archi originali. Per presentare più frecce come un flusso occorrono passi collegati, con verso, condizioni, profilo e prove compatibili. Se il frontend chiama A e B scrive nel registro, raggruppare A e B in «Pagamenti» mostra due dipendenze. Se manca il collegamento interno fra A e B, il percorso dal frontend al registro resta da dimostrare.
- `[deciso]` La GUI affianca alla mappa i passi della variante selezionata. Un clic su un passo evidenzia l’arco esatto, anche fra archi paralleli, e permette di aprirne la prova. La mappa e la lista dei passi si selezionano a vicenda. Una diramazione mostra la condizione e un ciclo può visitare di nuovo lo stesso arco. Al confine di un gruppo il flusso selezionato indica il punto di ingresso o uscita. Daodan fornisce passi, condizioni e prove; Sigrid disegna la scena e ne gestisce la selezione. *Da completare nell’app e nell’esploratore.*
- **Caso di accettazione:** per «Pagamento a un contatto» in Bank of Anthos allo stesso commit, il profilo Kubernetes standard mostra Ledgerwriter che verifica il saldo tramite Balancereader; il profilo monolitico mostra Ledgermonolith che legge la cache locale. Selezionando la divergenza si arriva alla configurazione e al codice corrispondenti. Entrambi i percorsi conservano il grado dichiarato fino a una prova ulteriore. [Configurazione standard](https://github.com/GoogleCloudPlatform/bank-of-anthos/blob/db35fea9fd090150e2398106aadb475576f80d94/kubernetes-manifests/config.yaml#L28) · [Configurazione monolitica](https://github.com/GoogleCloudPlatform/bank-of-anthos/blob/db35fea9fd090150e2398106aadb475576f80d94/src/ledgermonolith/config.yaml#L31)

### Nessun limite

- `[deciso]` Nessun tetto al numero di nodi, né minimo né massimo.
- Nessun taglio in silenzio: un tetto di calcolo è una lacuna, con il numero di ciò che resta fuori. *Nel codice: gli elenchi oltre 1.000 voci si dividono; le frecce che attraversano nodi nascosti si fermano a 2.000 passi, con la lacuna.*
- Alla pagina: si disegna solo ciò che è aperto e in vista. La vista la calcola il servizio, che manda solo quei nodi e le loro frecce: la pagina non riceve mai l'intero grafo. *Parziale: l'app sì (`app_view.view`); l'esploratore carica tutto l'involucro. La pagina è nel piano in `T2.D`.*
- Un gruppo con più figli di quanti la vista ne regge si apre a blocchi, con un nodo sintetico «altri N». *Da creare.*
- Al calcolo: il costo di una vista cresce con ciò che mostra, non con il totale dei simboli. *Parziale: non misurato su un progetto grande.*
- Misura che manca: tempo e peso di una vista con 80.000 nodi in archivio e 300 in vista. Prima del passaggio a Sigrid, 300 nodi in vista chiedevano 4,6 s e 1.000 non si disponevano (`benchmarks/codebase-explorer/README.md`).
- Per valutare il renderer si misurano separatamente preparazione della vista, disposizione e tracciamento degli archi, primo disegno utilizzabile e risposta alla selezione. Il confronto usa stessa vista, etichette e scala. Il primo confronto riguarda l’apertura sul posto con il renderer attuale di Sigrid.

### Le tecnologie come nodi

L'anagrafica delle tecnologie (`daodan/data/service-registry.json`) dà a ogni voce nome, categoria (`framework`, `library`, `tool`, `service`), tipo e, dove c'è, logo. Senza `category`, una voce di `kind` `service` vale `service` e le altre `framework`. Il grafo consulta l'anagrafica, senza nominare tecnologie nel codice. I tipi di framework, librerie e strumenti stanno in `registry-additions.json` con `by: model` e non sono verificati a campione.

Ogni voce dice il suo `support`, calcolato da `registry_build.support` e mai scritto a mano. `none`: il fork non ha una regola per la voce, quindi nessun progetto la mostra. Un servizio o uno strumento chiede solo di essere riconosciuto: con una regola è `full`, perché il grafo ha il suo nodo e le frecce che ci arrivano. Un framework o una libreria è `full` quando un lettore di Daodan legge come il progetto lo usa (rotte, eventi dei template, stili: la tabella `READERS`), `partial` quando è riconosciuto e basta. Una sorgente scritta e scollegata non conta: Django, FastAPI e Flask sono `partial`.

- `[deciso]` Un modulo è collegato ai nodi di tutte le tecnologie che lo compongono, strumenti di sviluppo compresi, con una freccia «usa» che cita il file che le dichiara. Il nodo tecnologia è concreto, esterno, con il tipo e il logo della sua voce; uno per tecnologia e per progetto. *Nel codice: `technology:<id>` per ogni voce `framework`, `library` o `tool` dello stack, con la freccia `uses` da ogni modulo al sito che la dichiara (per una libreria con versione centrale, il sito del suo uso: `used_in`) (`visual.py`).*
- Un servizio che un file dichiara è un nodo esterno, con una freccia `uses` da ogni file che lo mostra (`uncertain` dove lo menziona soltanto). Un modulo esterno dichiarato dal progetto è un nodo esterno; se ha l'id di una voce `service` ne prende tipo e logo. Uno store è un nodo di specie store. *Nel codice.*
- `[deciso]` Una tecnologia solo menzionata non è un nodo; un pacchetto fuori dal catalogo resta contato sul modulo. *Nel codice.*
- Un nodo di tecnologia resta nella mappa anche se nessun flusso lo usa.
- `[deciso]` Per tenere semplice il primo grafo, i servizi restano in vista accanto a chi li usa; framework, librerie e strumenti stanno sotto un nodo astratto «Tecnologie», che si apre. Il logo sul modulo resta la forma chiusa della freccia. *Nel codice: `group:technologies` (`visual.py`), un gruppo accanto ai moduli che non decide il raggruppamento (`app_view.py`); le tessere restano (`TILES`).*
- **Logo di una tecnologia:** una tessera di Daodan in `daodan/data/marks/`; i servizi di AWS, Azure e Google Cloud hanno pittogrammi di Daodan.
- **Senza logo:** il nodo ha l'icona della sua specie (`viewer/src/icons.ts`). `filesystem` e `altro` prendono quella dell'entità, `funzionalità` nessuna.
- **Mappa di sistema:** i suoi nodi esterni portano l'id dell'anagrafica (`registry`) e, quando la voce ha un logo, la vista (`system_levels.view`) lo passa in `mark`, come l'involucro. *Nel codice.*
- `[deciso]` **Due ingressi con lo stesso esito** sono due varianti di un solo flusso, che si apre per vederle (nel piano, `T3.C`).

## File di progetto

`[deciso]` Un file `.daodan` è un database SQLite. Il [DDL normativo, schema 2](#schema-sqlite-v2) (`daodan/core/project_schema.sql`) definisce le tabelle, i vincoli e gli indici. Le regole di identità e integrità qui sotto completano il DDL. Apertura, salvataggio e rianalisi nell’app sono assegnati a T2.E.

### Come riconoscere il file

Il formato richiede SQLite 3.38 o successivo con funzioni JSON disponibili. Le tabelle usano tipi STRICT. L'intestazione è quella di SQLite. Il lettore verifica `application_id = 0x44414F44` (DAOD), `user_version = 2` e lo schema atteso prima di usare il file. Il DDL inizializza soltanto un database vuoto. Un lettore che incontra una versione sconosciuta spiega quale versione serve. Per migrare, si crea prima una copia consistente, si applicano le modifiche e si aggiorna `user_version` nella stessa transazione. Una copia da condividere a database aperto si ottiene con l'API di backup di SQLite, così include anche i commit già visibili in WAL. [Intestazione e pragma](https://sqlite.org/pragma.html) · [Backup SQLite](https://sqlite.org/backup.html)

La v1 al commit `c7bc75b` ha le stesse 21 tabelle e accetta specie libere in SQL. Per portare un file v1 alla v2, leggere uno snapshot coerente e validare **tutte le versioni** dei nodi, comprese quelle chiuse. Se una specie è sconosciuta si indica ID, revisione e valore, lasciando intatto il file di partenza. Se i dati sono validi, si copiano tutte le righe in un nuovo database inizializzato col DDL v2, mantenendo chiavi, UUID e storia. Inserimento in un'unica transazione con vincoli esterni differiti; prima di sostituire il file si verificano chiavi esterne, integrità e uguaglianza dei dati delle 21 tabelle. Il nuovo vincolo rifiuta specie estranee anche con un inserimento SQL diretto.

### Tabelle

| Tabelle | Contenuto e collegamenti |
|---|---|
| `project`, `revisions` | Un progetto, UUID persistente e revisione corrente. Ogni revisione ha UUID proprio, genitore, autore, istante UTC, motivo, descrizione e analisi di riferimento. |
| `source_snapshots`, `analyses` | Sorgenti effettivamente analizzati, versione e configurazione di Daodan. Ogni esecuzione punta a uno snapshot. Più esecuzioni possono usare lo stesso snapshot. |
| `objects`, `versions` | Identità stabili e versioni dei soli oggetti cambiati. Una versione include provenienza e intervallo di validità. |
| `nodes`, `edges` | Il padre di un nodo e gli estremi di un arco puntano a ID stabili. Ogni arco ha ID proprio anche a parità di estremi, più tipo, grado, eventuale profilo e attributi come metodo e rotta. |
| `flows`, `variants`, `variant_endpoints` | Il flusso ha un nome, la variante ha profilo e condizione. Gli ingressi e gli esiti sono elenchi di nodi distinti per ruolo. |
| `steps`, `step_edges`, `step_transitions` | Occorrenze dei passi di una variante, archi originali attraversati da ciascun passo e passaggi condizionati verso i successivi. Si possono interrogare diramazioni, ricongiungimenti e cicli. |
| `evidence`, `version_evidence` | Ogni prova è ancorata all’analisi che l’ha prodotta. Può indicare un percorso del progetto, righe, simbolo e oggetto Git, oppure una posizione dentro una precisa versione di un risultato tecnico. Più oggetti possono citare la stessa prova. |
| `technical_records`, `gaps` | Risultati dei singoli strumenti con il loro payload JSON, e lacune con oggetto interessato, causa e possibile rimedio. Entrambi hanno una storia. |
| `manual_edits`, `conflicts`, `conflict_evidence` | Campo modificato, valore di partenza, scelta dell’utente e revisione di partenza. Il conflitto conserva il valore proposto dalla rianalisi, la sua provenienza e le sue prove fino alla risoluzione e dopo. |

`[deciso, su delega]` Che cosa si versiona: l'involucro della mappa che l'app mostra (`daodan/visual@1` senza simboli: un simbolo è un oggetto solo dove è estremo di un passo di flusso), non i risultati dei singoli strumenti, che restano nello snapshot della corsa citato da `analyses.config_json`; `technical_records` porta solo le proposte `identity_match`. Un'entità dell'involucro è un nodo; il suo padre è l'appartenenza fisica (la cartella che lo contiene), le appartenenze logiche (il modulo che tiene un file) sono archi `member`. La chiave d'identità di un nodo e di una relazione è il suo `ref` nell'involucro; un passo di un flusso è un arco a sé, con sito e tipo nella chiave, e un arco che cambia grado è un arco nuovo. Un flusso dell'involucro ha una sola variante, senza profilo, finché non arrivano le varianti per profilo.

### Identità e storia

- `user_version` identifica il formato su disco. `analyses.daodan_version` identifica l'analizzatore. La versione dei sorgenti viene da `source_snapshots`; `revisions.revision_uuid` identifica la revisione della mappa. Un edit manuale eredita l'analisi di riferimento. Una rianalisi ne registra una nuova, anche sullo stesso commit. Le date sono UTC in formato RFC 3339.
- Per un checkout Git pulito si conserva il commit completo con la sua data. Per cartelle senza Git o alberi modificati è obbligatoria l'impronta del perimetro effettivamente analizzato. L'eventuale commit di base resta disponibile. La politica d'inventario versionata in `inventory_policy` dichiara selezione e algoritmo. Un file cambiato mentre si calcola l'impronta richiede di rileggere l'input, affinché il digest descriva i byte analizzati. In ordine binario dei percorsi relativi UTF-8 con separatore `/`, si concatena per ogni file la lunghezza del percorso in byte (intero senza segno a 64 bit big endian), il percorso e il digest SHA-256 binario dei byte analizzati. `tree_sha256` è il digest SHA-256 esadecimale minuscolo della concatenazione. Il perimetro rispetta le esclusioni di Daodan anche per gli hash.
- Ogni copia porta la storia lineare e gli UUID già assegnati. Una nuova revisione usa un UUID nuovo. Dopo una copia, due revisioni con numero locale 8 e genitore comune possono così rappresentare storie diverse. Per confrontare copie si usano UUID di progetto e revisione; gli ID numerici delle righe valgono dentro una copia.
- Lo stato alla revisione R comprende le versioni con `from_rev <= R` e `until_rev IS NULL OR R < until_rev`. Creare apre un intervallo, modificare chiude il vecchio e apre il nuovo, eliminare chiude quello attivo. Anche prove, ingressi, archi di un passo e transizioni appartengono alla versione del loro proprietario: cambiarli apre una nuova versione. Un diff confronta le versioni ai due estremi per ID oggetto e dettaglia i campi e le relazioni cambiati. Il changelog usa le revisioni, i loro autori e le versioni aperte o chiuse in ciascuna.
- `[deciso, su delega, provvisorio]` Il `.daodan` è il solo posto dove l'app scrive una modifica a mano; Daodan non scrive mai i file del progetto. `codebase-modules.json` e `codebase-system-map.json` restano ingressi dell'analisi: un valore dichiarato arriva come gli altri valori dell'analisi (provenienza `declared` nella versione e `origin` nel conflitto), e se cambia sotto un edit è un conflitto, mai una precedenza silenziosa. La regola sta in una funzione sola, `project_file.incoming`: un'altra risposta del proprietario cambia solo quella, il suo test e questa frase.
- Le nature si ricavano da specie, posizione e contenuto dei gruppi secondo l'architettura. «Realizzato da» e «gira su» sono archi. Frecce riassunte, conteggi e geometria della GUI sono dati derivati. Per un profilo, una riga con `profile IS NULL` è comune a tutti. I gradi di Daodan (per esempio dichiarato, provato, osservato e incerto) si conservano senza promozione; eventuali qualificatori del produttore, come il campionamento, restano negli attributi. La provenienza dell'edit appartiene alla versione.

### Riconoscere lo stesso nodo alla rianalisi

L'identità persistente è `objects.object_id`. Ogni analisi riconcilia le osservazioni con i nodi della revisione di partenza **prima** di calcolare il diff o riapplicare gli edit. Il confronto usa i dati estratti dai sorgenti, indipendentemente dal nome e dal padre scelti a mano nella mappa. In `nodes.attributes_json.identity` si conservano le chiavi di confronto disponibili per quella versione (produttore, spazio dei nomi e chiave nativa; per un file, percorso relativo e SHA-256 dei byte dell'inventario). Una rinomina crea una versione con i nuovi riferimenti e conserva quelli precedenti nella storia.

| Caso | Regola |
|---|---|
| File ancora allo stesso percorso nel medesimo progetto | Riusa l'ID anche se il contenuto è cambiato, salvo evidenza di cancellazione e successiva creazione di un altro file. Il percorso rioccupato dopo una cancellazione confermata riceve un nuovo ID. |
| File spostato o rinominato, con o senza Git | Confronta i due inventari effettivi nello stesso perimetro. Un solo vecchio percorso scomparso e un solo nuovo percorso comparso, con digest uguale e unico in ciascun inventario, conservano l'ID. Una rinomina accompagnata da modifiche conserva l'ID se una chiave nativa persistente indipendente dal percorso o una conferma dell'utente identifica univocamente la coppia. La similarità suggerita da Git propone un candidato. |
| Copia, sostituzione o candidati multipli | Se l'originale rimane e viene aggiunta una copia, l'originale conserva il suo ID e la copia ne riceve uno nuovo. Evidenze incompatibili, un nuovo percorso con più sorgenti possibili o il solo nome simile richiedono conferma. |
| Simboli e altri nodi | Un simbolo conserva l'ID con una chiave stabile del resolver nel suo spazio dei nomi, oppure con un descrittore univoco (contenitore e firma) nel file già riconciliato. Righe e numeri locali dell'indice possono cambiare. Per un servizio, una tecnologia o un'altra entità vale la chiave qualificata stabile del produttore (per esempio l'ID del catalogo). Per un nodo sintetico servono un'identità dichiarata o una corrispondenza confermata. |
| Analisi parziale o chiavi storiche mancanti | L'assenza da una scansione incompleta lascia l'identità precedente in sospeso e apre una lacuna. Per un file v1 privo di chiavi si usano solo prove ancora verificabili alla revisione di origine. |

Una nuova osservazione senza alcun candidato riceve un nuovo `object_id`. Una corrispondenza automatica è uno a uno, nello stesso progetto e tra tipi di nodo compatibili. In presenza di evidenze contrastanti prevale l'ambiguità. Per un candidato ambiguo si conserva l'edit sull'ID originario, si mostra la proposta con i riferimenti vecchi e nuovi e si lascia il nuovo nodo senza quell'edit. La proposta si registra come `technical_records` di tipo `identity_match`, con ID precedenti, nuovi, snapshot e prove; una lacuna ne richiama l’ID in `gaps.subject_id`. Alla conferma si registra una nuova revisione con autore e scelta: si riusa l'ID originario, si chiude l'eventuale identità provvisoria e si aggiornano insieme i riferimenti della revisione corrente. Se nel frattempo è stato modificato anche il candidato provvisorio, gli edit compatibili si conservano e i valori incompatibili richiedono risoluzione per campo. Le revisioni precedenti conservano gli ID che contenevano. Se si conferma «sono distinti», si mantiene l'ID nuovo. Una cancellazione accertata chiude la versione secondo le regole sugli edit manuali.

Per gli archi si riconciliano prima i nodi. Gli estremi stabili, il tipo, il profilo e il sito di origine devono identificare un solo arco per riusarne l'ID. Due chiamate parallele fra gli stessi servizi rimangono distinguibili. Gli edit di un passo o di una variante seguono l'ID persistente della rispettiva occorrenza; un cambiamento dell'ordine di presentazione da solo non trasferisce un edit a un altro passo.

### Integrità al salvataggio

Le chiavi esterne vanno abilitate a ogni apertura. In una sola transazione di scrittura il writer confronta la revisione attesa con `project.head_rev`, inserisce la revisione e i cambiamenti, verifica lo stato risultante e aggiorna la testa. Un errore annulla tutto. A testa cambiata si rilegge il progetto e si ricalcola la modifica. Creare il progetto inserisce snapshot, analisi, revisione 1 e unica riga di `project` insieme. [Chiavi esterne SQLite](https://sqlite.org/foreignkeys.html)

Oltre ai vincoli SQL, chi scrive verifica queste condizioni prima del commit; chi importa un file le verifica sulla storia importata.

1. La testa coincide con l'ultima revisione. Per un oggetto gli intervalli sono disgiunti. Ogni versione ha una sola riga nella tabella del suo tipo. Gli ID oggetto restano unici e conservano il tipo. Gli oggetti creati manualmente ricevono un UUID, così le aggiunte indipendenti in due copie restano distinguibili. Nella storia già salvata sono modificabili soltanto la fine di un intervallo aperto e il riferimento alla risoluzione di un conflitto. La riga di progetto avanza alla nuova testa. Ogni altro cambiamento aggiunge una revisione.
2. La specie di ogni nodo appartiene all'elenco chiuso in [Proprietà](#proprietà). Scrittura, importazione e migrazione rifiutano valori sconosciuti, anche nelle revisioni storiche. Un padre è un nodo attivo e la gerarchia è aciclica. Gli estremi degli archi, gli ingressi, gli esiti e l'eventuale funzionalità di un flusso sono nodi attivi nella medesima revisione. Una variante appartiene a un flusso attivo e un passo a una variante attiva. Spostamenti e cancellazioni sistemano nello stesso commit tutti i riferimenti coinvolti. Le prove storiche continuano a puntare alla fonte originaria.
3. Gli archi di un passo sono attivi per quel profilo e ne rispettano verso e condizioni. Le transizioni collegano solo passi della stessa variante. L'ordine di presentazione è distinto dalla causalità. Due transizioni possono ricongiungersi sullo stesso passo; due passi distinti possono citare lo stesso arco. Un passaggio non dimostrato resta una lacuna. Una prova `artifact` cita una versione immutabile di un record tecnico e il punto del risultato che la sostiene.
4. Un edit identifica il campo con JSON Pointer relativo all'oggetto, anche per i dettagli del flusso; la stringa vuota riguarda l'oggetto intero. I passi si modificano tramite ID di occorrenza. Per un elenco ordinato, come gli archi di un passo, un edit confronta l'intero campo: l'indice numerico di una riga non identifica un elemento dopo un riordino. Il valore ha la forma `{"present":true,"value":...}` oppure `{"present":false}`, così un campo assente si distingue da JSON null. Per ogni campo si applica l'ultimo edit attivo. `release` chiude la scelta manuale. Anche un intervento sul medesimo campo o una rimozione del suo oggetto da parte dell'analizzatore usa il confronto a tre vie. Un conflitto aperto conserva visibile la scelta manuale e permette di consultare il valore in arrivo. La risoluzione registra un nuovo edit nella revisione indicata da `resolved_rev`, scegliendo quale valore tenere o tornando a seguire l'analisi.

### Esempio di lettura e revisione

Per leggere i figli di un gruppo in una revisione storica:

```sql
SELECT v.object_id, n.name
FROM nodes AS n
JOIN versions AS v ON v.version_id = n.version_id
WHERE n.parent_id = :group_id
  AND v.from_rev <= :rev AND (v.until_rev IS NULL OR :rev < v.until_rev)
ORDER BY n.name, v.object_id;
```

In Bank of Anthos, «Pagamento a un contatto» ha un solo ID di flusso. Sullo stesso commit il profilo `kubernetes-standard` porta da Ledgerwriter a Balancereader e `ledger-monolith` legge il saldo dalla cache di Ledgermonolith. Le varianti collegano i rispettivi passi e ciascun passo cita i propri archi. Cambiare profilo nella GUI seleziona una variante della stessa revisione.

| Revisione esemplificativa | Righe interessate |
|---|---|
| R1, analisi | Inserisce snapshot S1, analisi A1 e flusso F con nome originale. |
| R2, una persona rinomina F | Stessa A1. Chiude la versione precedente di F, ne apre una con il nuovo nome e registra un edit su `/name` con base R1. Nodi e archi conservano le righe esistenti. |
| R3, rianalisi | Registra A2. Se cambia solo un arco, F conserva il nome manuale. Se l'analisi propone un terzo nome, `conflicts` collega tale valore all'edit R2. |
| R4, risoluzione | La scelta viene registrata con autore. Riaprendo R3 il conflitto risulta ancora aperto; in R4 si vede l’esito. |

### Prove di accettazione del formato

Rinomina `payment.py` in `transfer.py` dopo un edit manuale: con un'unica corrispondenza verificabile restano lo stesso ID e l'edit, anche dopo riapertura. Ripeti senza Git. Copia invece il file lasciando l'originale: la copia ha un nuovo ID e l'edit resta sull'originale. Con due candidati uguali o una rinomina più modifica segnalata solo per similarità, richiedi conferma e verifica autore, decisione e storia. Verifica infine che tutte le 24 specie siano accettate, che una inventata venga rifiutata nel DDL e dall'importatore, e che un ciclo tra padri venga rifiutato dal writer. Per la migrazione v1 → v2 verifica ID e revisioni dopo riapertura, e il rifiuto di una specie sconosciuta presente solo nello storico. La prova del proprietario, su v1 in memoria, copre creazione e rilettura di un progetto minimo. Le prove end-to-end usano un file su disco attraverso l'app.

### Schema SQLite v2

Il DDL completo per creare un file vuoto è [`daodan/core/project_schema.sql`](../../daodan/core/project_schema.sql): un solo posto, che il codice esegue per creare un file e per confrontare lo schema di quello che apre.

## Il piano: completo nei vincoli, incrementale nelle azioni

Un solo oggetto condiviso tra interfaccia, MCP e riga di comando (il giornale degli eventi resta come cronaca).

1. **Completo nei vincoli prima dell'avvio:** prima che parta qualunque cosa, il piano espone tutti gli step, le politiche, i permessi e le condizioni di arresto.
2. **Incrementale nelle azioni concrete:** le azioni che dipendono dalla scoperta (moduli, download, build, suite di test, avvio app) vengono aggiunte e aggiornate nello stesso piano man mano che gli step `recognize_stack`, `find_modules` e `find_entry_points` le determinano. Se emerge un'azione che richiede consenso (download pesante, licenza) o eccede i permessi, l'esecuzione si ferma su quell'azione; per un host da approvare vale «Servizi comuni».
3. **Dice che cosa fa, non come:** frasi leggibili («lancia i test di `api`»), con strumento/comando/versione come dettaglio apribile. Ogni azione indica bersaglio e tre fatti: se esegue codice del progetto, se gira nel container, se scarica dalla rete e quanto pesa.
4. **Stato per azione** aggiornato in tempo reale: `da fare`, `in corso`, `fatta`, `fallita`, `saltata` (già fresca), `non possibile` (con causa e rimedio), `in attesa di approvazione` (un suo host attende la risposta di una persona). Tipi di azione da elenco chiuso.

**Nel codice:** `pipeline.plan.current(manifest)` dà `{steps, policy, actions, gaps}`, calcolato a ogni chiamata da record, giornale ed `egress`, senza un file suo. Gli step hanno `state` (`pending`, `running`, `done`, `failed`, `skipped`), `executes` e `stops`; le azioni `kind` da `plan.ACTIONS` (`read`, `recognize`, `model`, `entries`, `resolve`, `observe`, `explore`, `assemble`), `target`, `project_code`, `container` e `state` da `plan.ACTION_STATES` (in più `not_possible` e `awaiting_approval`, che porta solo `hosts`; i dettagli restano in `egress`). Lo leggono l'app (`run.plan` dello stato), MCP (`plan` di `codebase_map_status`) e la riga di comando (`daodan snapshot plan MANIFEST`); il peso dei download è la lacuna `download_size_unknown`.

## L'interfaccia segue la pipeline

La UI (solo componenti Sigrid nella shell Imago) legge il piano e i risultati degli step senza ricostruirli dagli eventi e senza tenere elenchi propri di fasi. Mostra gli otto step con i loro risultati, i consensi prima dell'esecuzione, l'azione in corso e le lacune. Un host da approvare («Servizi comuni») è una notifica e un popup con host, porta, indirizzo risolto e il file che lo dichiara; un tentativo verso un host in blacklist è solo una notifica. Le parole interne («pre-mappa», «scan», «stack», «analyze») escono dall'interfaccia.

**Nel codice:** l'app legge `run.plan` dello stato (lo stesso piano di `codebase_map_status` e di `daodan snapshot plan`) con `viewer/app/plan.ts` (passi, azioni, azione in corso, lacune, riga di stato e politica, senza eventi); il percorso dell'Analisi è «Repository» più i passi del piano, nel suo ordine (`viewer/app/path.ts`), con le parole dei passi di `pipeline_tree.py` per `id`; ogni passo è `viewer/app/plan-step.tsx`, con il suo risultato, le sue azioni e la piega «Eventi» con la cronaca del giornale; le viste si rileggono quando un passo del piano diventa `done` o `skipped`. Il popup degli host di `T0.C` (`hosts-dialog.tsx`) si apre da un'azione `awaiting_approval` e dalla palette.

## Le anagrafiche (`daodan/data/`)

Ogni anagrafica deve avere un controllo automatico di coerenza con il codice:

| Anagrafica | Contenuto | Chi la usa | Stato |
| --- | --- | --- | --- |
| `file-formats.json` | Formati accettati, linguaggi, cartelle/nomi esclusi | `list_files` | Nel codice |
| `linguist-catalog.json` | Nomi Linguist per ogni formato accettato | `list_files` | Nel codice |
| `language-rules.toml` | Regole di disambiguazione estensioni condivise | `list_files` | Nel codice (manca il nome file) |
| `service-registry.json`, `registry-additions.json`, `marks/` | Di ogni tecnologia nome, `kind` (`service`, `project`), tipo di nodo e sito; `support` (`full`, `partial`, `none`); dove ci sono, `category` (`framework`, `library`, `tool`, `service`) e logo (+ `surface`) | `recognize_stack`, il grafo, UI | Nel codice (senza `surface`) |
| `build-tools.json` | Strumenti di build/toolchain -> adattatore | `find_modules` | Nel codice (CMake, Meson, Bazel, Make, autotools, sbt, .NET, Mix dopo il `.6` del fork) |
| `package-managers.json` | Registri pacchetti consentiti nella preparazione | Preparazione container | Nel codice |
| `entry-queries.json` | Query tree-sitter per ingressi | `find_entry_points` | Nel codice |
| `http-clients.json` | Client HTTP come nominati dal compilatore | `link_calls`, `assemble_graph` | Nel codice |

## Servizi comuni

- **Motore di container:** isola sempre il codice del progetto. Su Windows è il **Kiri** di Daodan, in una distribuzione WSL 2 propria; altrove è quello dell'utente (`docker`, poi `podman`).
- **Preparazione (una per analisi):** toolchain (`mise`), dipendenze ripristinate via proxy, strumenti verificati per sha256; tutto il resto gira senza rete. I controlli preventivi non sono il confine di isolamento (da creare, `T3.A`): i comandi vengono solo da una tabella chiusa; un lockfile con `file:` o `-e` è rifiutato con una lacuna, mentre un indirizzo `git+` o URL non si rifiuta `[deciso]`: il suo host si approva come ogni altro; gli script di lifecycle dei gestori sono spenti nel ripristino. Il container gira con `--cap-drop ALL` e un utente non root (da creare, `T3.A`).
  - **Nel codice** (`daodan/core/container.py`): esecuzione con `--network none`; preparazione su una rete interna con il proxy (`container.PROXY_SCRIPT`) come sola uscita; `--security-opt no-new-privileges`. Il proxy apre senza chiedere solo i registri di `package-managers.json` e gli host approvati (`egress.decide`); ogni altro host, anche dichiarato (`preparation.declared`, `python_vcs`) o fisso di uno strumento, è rifiutato e chiede (`T0.C`). Non passa `--cap-drop` né `--user`. La prova su un container vero è `benchmarks/egress/modal_probe.py` (`T0.C.8`).
- **Uscita di rete con approvazione `[deciso]`** (nel codice: `egress`, da `T0.C`; lo stato di attesa è `awaiting_approval` nel piano unico, `T1.D`). Sostituisce «solo proxy verso registri autorizzati» e ritira l'apertura «come una CI» degli host dichiarati.
  - **Confine:** nessuna uscita diretta dal container di analisi; il controllo sta fuori, nel proxy, unica uscita (inclusi redirect, DNS e IP letterali).
  - **In whitelist:** passa senza chiedere. Sono gli host canonici (`daodan/data/package-managers.json`: i gestori dell'elenco di Wikipedia, con gli host scritti a mano e provati da `benchmarks/registry-hosts/`) e quelli approvati dall'utente.
  - **In blacklist:** rifiutato subito; solo una notifica del tentativo, nessun popup.
  - **Ogni altro host** (anche dichiarato dal progetto o assegnato da Daodan a uno strumento): notifica e popup, e l'utente deve approvare. Il proxy rifiuta subito, e dopo il sì il passo si rilancia; gli host dichiarati si chiedono prima che il passo parta. Se il passo riesce comunque con un host rifiutato, il risultato vale e la richiesta resta visibile. Il popup mostra l'indirizzo risolto e segnala quando è una macchina della rete dell'utente.
  - **Richiesta preventiva per passo:** un host dichiarato dal progetto e non deciso ferma ogni passo che costruisce in container e che lo raggiungerebbe, qualunque sia lo strumento: per gli analizzatori, ogni indicizzatore con container (`engine_pass.index_stage`) aspetta finché l'host non ha una risposta.
  - **Risposte:** «sempre per questo progetto», «solo per questa analisi», «no», «blocca sempre» (va in blacklist). Whitelist e blacklist stanno nella cartella condivisa di Daodan, mai nel progetto.
  - **Si approva solo dalla GUI.** MCP e riga di comando mostrano le richieste in attesa e non approvano mai: il modello legge il progetto analizzato, e un client MCP che è un agente può rispondere da sé a una elicitation.
  - **Lacune:** `approval_required` senza risposta o senza schermo; `host_denied` dopo un no o per un host in blacklist.
  - **Strumento del proxy:** `PROXY_SCRIPT` esteso, scelto dalla prova di `T3.A.2` (`benchmarks/egress/README.md`, «Proxy: la prova di `T3.A.2`») con la regola di `T3.A.3` (vince Smokescreen solo se da solo, con ACL `enforce`, non dà righe rosse): Smokescreen apre le porte 80 e 8443 di un host ammesso e ne inoltra l'HTTP in chiaro a ogni percorso; `PROXY_SCRIPT` apre un host ammesso che risolve a un indirizzo interno, e l'estensione risolve l'host, rifiuta un indirizzo che non è `ipaddress.ip_address(...).is_global` e si connette a quell'IP, non al nome. Criteri: solo porta 443, eccezione apt per percorso, whitelist e blacklist da file, nessun host rifiutato risolto dal proxy (lo risolve `egress`), nessun host ammesso aperto verso un indirizzo privato, loopback o link-local, rifiuti leggibili come `{host, port}`.
- **Lanciatore dei comandi:** `container_runner.py` per le sorgenti di `find_modules` e `find_entry_points`; `link_calls` e `run_and_observe` passano da `container.run_in_container`, il servizio comune con `egress.preflight`.
- **Giornale:** traccia inizio, avanzamento, lacune e fine di ogni step e adattatore.
- **Secretlint:** ogni testo che lascia la macchina o va a un LLM passa prima da Secretlint. **Nel codice:** `secret_mask`, che lo lancia, è chiamato da `daodan/core/app.py` (risultati degli strumenti e prompt) e da `daodan/core/mcp_server.py` (risultati ed errori).

## Termini

- **Cartella condivisa:** la cartella di Daodan sulla macchina, fuori da ogni progetto, dove stanno gli strumenti installati al primo uso (`embedding_worker.shared_cache_dir`).
- **Host fisso, host dichiarato:** fisso è quello che il codice di Daodan assegna a uno strumento; dichiarato è quello che i file del progetto nominano per dipendenze o build.
- **Kiri:** il motore di container che Daodan porta su Windows, in una distribuzione WSL 2 propria (`daodan/core/container.py`).
- **Noir:** lo scanner di rotte OWASP Noir, che gira nel container (`daodan/core/entry_points/noir.py`).
- **Fork `stack-analyser`:** il riconoscitore delle tecnologie, un fork di quello di Specfy (`daodan/core/stack_analyser.py`).
- **Pre-mappa:** nel disegno il modello di build, uscita di `find_modules`; rotte ed eventi sono di `find_entry_points` (`daodan/core/entry_points/`, `entry-points.json`).
- **Smokescreen:** il proxy di uscita di Stripe, candidato a proxy della preparazione.
- **SCIP:** il formato di indice del codice di un intero progetto, che `daodan/core/code_graph.py` legge come un grafo.
- **Store:** ciò a cui il codice accede in scrittura o lettura, nominato con la sua chiave da una regola di collegamento (`daodan/core/flows.py`).
- **Tessera:** il logo di una tecnologia dentro la cornice di Daodan.
