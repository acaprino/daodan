# Daodan: architettura e contratto della pipeline

**Stato:** contratto stabile di riferimento (estratto dal refactoring del 25 novembre 2026). Descrive *com'è Daodan a refactoring finito*. Il lavoro attivo è in [`docs/plans/refactoring.md`](../plans/refactoring.md); tutto ciò che è differito o ritirato è in [`docs/backlog.md`](../backlog.md) (non normativo). Le 19 spec e i 13 piani precedenti sono nella storia di git al commit `614c940`.

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

- **La pre-mappa è il modello di build**, uscita di `find_modules`: non tiene più rotte, pagine ed eventi. Il lanciatore nel container (`premap/container_runner.py`) diventa un servizio comune a `find_modules` e `find_entry_points`.
- **Chi riconosce è uno solo.** Uno strumento di build o un framework che il fork `stack-analyser` non conosce si aggiunge al fork. In Daodan `daodan/data/build-tools.json` lega ogni voce dello stack all'adattatore di `find_modules` che la usa.
- **Che cosa usa ogni step**, per linguaggio, strumento di build e framework: `docs/pipeline/`, generata dalle dichiarazioni del codice (`daodan/core/pipeline_tree.py`).

### Strumenti nativi, Noir e sorgenti dedicate

| Famiglia | Esempi | Che cosa dà | Step |
| --- | --- | --- | --- |
| Strumento di build | cargo, gradle, maven, npm, `tsc`, cmake, meson, bazel, make, `dotnet`, uv, go | Moduli, unità, pacchetti risolti, comandi | `find_modules` |
| Strumento / introspezione del framework | `next typegen`, `react-router routes`, `nuxt prepare`, `svelte-kit sync`, compilatori Angular/Astro, sorgenti **Django, FastAPI, Flask** `[deciso]` | Rotte, pagine, eventi dei template | `find_entry_points` |
| Compilatore del linguaggio (via SCIP) | TypeScript, Pyright, Java (Maven/Gradle), rust-analyzer, Clang | Dove arriva ogni chiamata | `link_calls` |
| Esecutore dell'interfaccia | browser (Playwright/Chromium), webview (CDP/WebDriver) | Quale controllo fa partire quale funzione | `run_and_observe` |

- **Framework senza strumento proprio:** letti dall'albero sintattico (tree-sitter) con query in `daodan/data/entry-queries.json` (es. `onClick` in React).
- **Convivenza tra sorgente dedicata e Noir in `find_entry_points`:** quando il container è disponibile e l'introspezione ufficiale del framework riesce, la sorgente dedicata è **primaria**; Noir funge da integrazione/fallback statico con provenienza dichiarata. Unione deduplicata su chiave che includa contesto/mount/router dove serve; eventuali conflitti restano in diagnostica. Senza container o a introspezione fallita, Noir fa da fallback con motivo dichiarato; un'introspezione riuscita con 0 ingressi non è un errore.
- **Un controllo ha due prove:** quella statica (legato a una funzione) e quella dinamica (azionato, quella funzione parte).

### Chiamate HTTP e punti di connessione

- **Chi offre la rotta:** strumento del framework o Noir (`find_entry_points`).
- **Chi la chiama:** compilatore del linguaggio fino a una funzione di `daodan/data/http-clients.json` (`link_calls`). Un wrapper del progetto si prova dai dati del compilatore, non dal nome.
- **Unione:** in `assemble_graph` dove percorso e metodo coincidono. Lo stesso vale per eventi, code e tabelle: un adattatore per tipo di legame, senza nominare framework nel codice dei legami.

### Superfici attive e regole comuni

Un'interfaccia nasce da un ingresso, non da un manifesto. Il campo `surface` dell'anagrafica decide con che cosa `run_and_observe` la esegue:

- **`web`** (attiva): Chromium senza interfaccia con Playwright (albero di accessibilità, azionamento controlli, registrazione funzioni partite).
- **`webview`** (attiva in T3): Electron (CDP), Tauri e Wails (WebDriver) su `Xvfb`. Dove manca il driver si esercita la sola pagina e lo si dichiara.
- **Superfici differite** (`desktop` Linux, GUI Python, `android`, `windows`): tracciate in [`docs/backlog.md`](../backlog.md). Finché non implementate emettono la lacuna `ui_execution_deferred:<superficie>`. macOS e iOS restano fuori perimetro.

Regole valide per tutte le superfici: nulla dell'host; download con licenza o di qualche GB solo dopo consenso esplicito (altrimenti `approval_required`); solo dati e credenziali di prova già preparati dalla CI del progetto; progetti multipiattaforma eseguiti sul bersaglio `web` quando dichiarato.

### Come si sa che cosa lanciare (test, avvio, build)

Un comando non si indovina mai: viene da una fonte, e porta scritto da quale. Senza fonti il passo è una lacuna.

| Fonte | Che cosa dice | Grado | Stato |
| --- | --- | --- | --- |
| L'utente | Comando scritto da chi conosce il progetto, tenuto nell'archivio di Daodan (mai nel progetto) | `confermato` | Proposta (T3) |
| Lo strumento di build | Comando previsto dallo strumento (`npm test`, `go test`, `cargo test`, Gradle/Maven, `dotnet test`, CTest) | `dichiarato` | Nel codice |
| I file del progetto | Script `test`/`start`/`dev`, config pytest, makefile (vale per il runner lanciato, non per il nome) | `dichiarato` | Nel codice |
| La CI del progetto | Passo dei test in CI, con servizi e passi preliminari | `dichiarato` | Parziale (T3) |
| Modello piccolo locale | Sceglie solo fra comandi già presenti nei file del progetto | `proposto` | Differito ([`docs/backlog.md`](../backlog.md)) |

### Il piano: completo nei vincoli, incrementale nelle azioni

Un solo oggetto condiviso tra interfaccia, MCP e riga di comando (il giornale degli eventi resta come cronaca).

1. **Completo nei vincoli prima dell'avvio:** prima che parta qualunque cosa, il piano espone tutti gli step, le politiche, i permessi e le condizioni di arresto.
2. **Incrementale nelle azioni concrete:** le azioni che dipendono dalla scoperta (moduli, download, build, suite di test, avvio app) vengono aggiunte e aggiornate nello stesso piano man mano che gli step `recognize_stack`, `find_modules` e `find_entry_points` le determinano. Se emerge un'azione che richiede consenso (download pesante, licenza) o eccede i permessi, l'esecuzione si ferma su quell'azione.
3. **Dice che cosa fa, non come:** frasi leggibili («lancia i test di `api`»), con strumento/comando/versione come dettaglio apribile. Ogni azione indica bersaglio e tre fatti: se esegue codice del progetto, se gira nel container, se scarica dalla rete e quanto pesa.
4. **Stato per azione** aggiornato in tempo reale: `da fare`, `in corso`, `fatta`, `fallita`, `saltata` (già fresca), `non possibile` (con causa e rimedio). Tipi di azione da elenco chiuso.

### L'interfaccia segue la pipeline

La UI (solo componenti Sigrid nella shell Imago) legge il piano e i risultati degli step senza ricostruirli dagli eventi e senza tenere elenchi propri di fasi. Mostra gli otto step con i loro risultati, i consensi prima dell'esecuzione, l'azione in corso e le lacune. Le parole interne («pre-mappa», «scan», «stack», «analyze») escono dall'interfaccia.

### Le anagrafiche (`daodan/data/`)

Ogni anagrafica ha un controllo automatico di coerenza con il codice:

| Anagrafica | Contenuto | Chi la usa | Stato |
| --- | --- | --- | --- |
| `file-formats.json` | Formati accettati, linguaggi, cartelle/nomi esclusi | `list_files` | Nel codice |
| `linguist-catalog.json` | Nomi Linguist per ogni formato accettato | `list_files` | Nel codice |
| `language-rules.toml` | Regole di disambiguazione estensioni condivise | `list_files` | Nel codice (mancano `.h` e nomi file) |
| `service-registry.json`, `registry-additions.json` | Metadati tecnologie (+ `surface`) | `recognize_stack`, UI | Nel codice (senza `surface`) |
| `build-tools.json` | Strumenti di build/toolchain -> adattatore | `find_modules` | Da creare (T1) |
| `package-managers.json` | Registri pacchetti consentiti nella preparazione | Preparazione container | Nel codice |
| `entry-queries.json` | Query tree-sitter per ingressi | `find_entry_points` | Nel codice |
| `http-clients.json` | Client HTTP come nominati dal compilatore | `link_calls`, `assemble_graph` | Nel codice |

### Servizi comuni

- **Motore di container:** isola sempre il codice del progetto.
- **Preparazione (una per analisi):** toolchain (`mise`), dipendenze ripristinate via proxy sui soli registri ammessi, strumenti verificati per sha256; tutto il resto gira senza rete.
- **Lanciatore dei comandi:** servizio comune a `find_modules`, `find_entry_points`, `link_calls` e `run_and_observe`.
- **Giornale:** traccia inizio, avanzamento, lacune e fine di ogni step e adattatore.
- **Secretlint:** ogni testo che lascia la macchina o va a un LLM passa prima da Secretlint.
