# Interfacce del progetto: schermate come nodi, comandi di build e avvio, esecuzione web

**Stato:** proposta, 19 novembre 2026, riscritta lo stesso giorno. Nulla è applicato. Allineata il 20 novembre alle decisioni del proprietario di quei due giorni (1.6, 3.6, 6.5, 7.1, 7.4); ogni scelta rimanda al suo motivo, in «Motivi delle scelte». Usa le parole di [Flussi e mappa del sistema](2026-11-18-flussi-e-mappa-del-sistema.md) (nodo, tipo di nodo, ingresso, estremi, candidato) e completa il [registro dell'esecuzione](2026-11-19-esecuzione-del-programma.md). Le piattaforme rimandate stanno nella [roadmap](../roadmap.md).

Daodan deve dire, senza eseguire codice del progetto: quali schermate ha il progetto, da dove cominciano, a che cosa sono collegate, e con quali comandi dichiarati si compilano e si avviano. Una schermata è un nodo del grafo, perché un flusso ci entra o ci esce. Non è un'etichetta su un pacchetto: il modulo che la toolchain vede e la parte dell'app che una persona nomina sono due cose diverse.

## Parole

- **Interfaccia:** un nodo di tipo `schermata` con codice nello snapshot. Nasce da un ingresso, non da un manifesto. Dal 19 novembre la mappa ha anche il tipo `applicazione` ([flussi e mappa](2026-11-18-flussi-e-mappa-del-sistema.md), Parole): il piano del 19 novembre (Parte D) propone `applicazione` per un'interfaccia che nasce da un ingresso, e `schermata` solo per una pagina sola dentro un'altra parte; questa spec dice ancora `schermata`.
- **Ingresso dell'interfaccia:** il file o il simbolo da cui una schermata comincia: un documento HTML, una pagina di un meta-framework, la radice di un'applicazione grafica.
- **Superficie:** dove l'interfaccia gira: `web`, `webview`, `desktop`, `windows`, `android`. Dice quale dispositivo sta sopra e se Daodan la sa eseguire. macOS e iOS sono fuori perimetro.
- **Guscio:** il processo nativo che apre la finestra e ospita la pagina di una `webview`.
- **Dispositivo sottinteso:** il nodo `dispositivo` sopra un'interfaccia: browser, PC, telefono. Si deduce dalla superficie.
- **`builds`, `starts`:** i comandi che il progetto dichiara per compilare e per avviare un modulo, con l'esecutore preso dalle `toolchains` del modulo.

## Comportamento attuale

- **Stack** (`daodan/core/technologies.py`): assegna a ogni modulo framework, librerie, servizi e strumenti dai segni dichiarati del registro (`daodan/data/service-registry.json`, 2.345 voci), senza eseguire nulla.
- **Registro:** `type: "schermata"` sta su sei voci (`angularjs`, `blazor`, `compose-multiplatform`, `flutter`, `phoenix-liveview`, `vue-router`). `react`, `angular`, `sveltejs`, `vue`, `nextjs`, `nuxtjs`, `astro`, `solidjs`, `streamlit`, `gradio`, `electron` e `tauri` hanno `"altro"`. `"dispositivo"` sta su `android`, `dotnet-maui` e `react-native`: il registro chiama dispositivo l'app, non il telefono. `tauri` ha il solo segno `tauri.conf.js`. Mancano `wails`, `nicegui` e i toolkit desktop (Qt, Tkinter, GTK, WPF, WinForms, WinUI, Avalonia, JavaFX).
- **Moduli** (`module_derive.py`): un modulo nasce da un manifesto, da una dichiarazione del progetto o dalla proposta di un modello. Nessuna regola ricava dal codice una parte dell'app che non ha un manifesto.
- **Due collegamenti non letti:** di un documento HTML Daodan legge solo le regole dei blocchi `<style>` (`languages/__init__.py`), non `<script src>` né `<link href>`. Un file del progetto che il codice incorpora alla compilazione non è un collegamento.
- **Pre-mappa:** estrae `tests` e `toolchains`, non `builds` né `starts`. `premap/npm.py` legge gli ingressi solo da `main`, `module`, `browser`, `bin`, `exports`. `premap/project_files.py` legge `<UseMaui>`, non `<UseWPF>`, `<UseWindowsForms>`, `<UseWinUI>`, `<OutputType>`.
- **Mappa del sistema:** il ruolo `system-mapper` dà nome e taglio ai nodi sui candidati della macchina, nel plugin. Dal 19 novembre la proposta parte da sola a fine analisi, nel plugin e nell'app ([flussi e mappa](2026-11-18-flussi-e-mappa-del-sistema.md), sezione 7); la pagina dell'app non la mostra.
- **Caso reale che oggi sfugge.** Un server Rust (Axum) ha un pannello di amministrazione fatto di tre file (`index.html`, `app.js`, `app.css`) in una sottocartella di `src/`. Il server li incorpora con `include_str!` e li offre su tre rotte; la pagina carica lo script; lo script chiama le rotte dell'API. Non ha un manifesto suo né un framework: oggi non è un modulo e non è una schermata. Lo stesso progetto ha un'app Tauri con due pagine dichiarate nella configurazione del bundler, `index.html` e una seconda.

## Proposta

### 1. Un'interfaccia nasce da un ingresso

Motivo 1.

1. Dove c'è un ingresso c'è un'interfaccia. Gli ingressi sono un elenco chiuso:
   - un documento HTML del progetto che una configurazione dichiara come pagina: gli ingressi del bundler, `angular.json`, `tauri.conf.*`, `wails.json`;
   - una pagina secondo la convenzione del meta-framework che il modulo dichiara (sezione 3);
   - un documento HTML del progetto che il codice del progetto incorpora oppure offre su una rotta;
   - la radice di un'applicazione grafica nel codice, per le superfici rimandate.
2. L'interfaccia è un candidato (spec del 18 novembre, sezione 6): l'ingresso più ciò che si raggiunge solo da lui. La macchina gli dà il tipo `schermata`. Il nome lo dà il modello; fino ad allora vale il titolo del documento o il nome del file.
3. Un'interfaccia senza un manifesto suo sta dentro il modulo `build` che possiede i suoi file: aprendo quel modulo la si vede come parte. Non diventa un modulo `build`.
4. Più ingressi nello stesso modulo sono più interfacce.
5. Un modulo con un framework UI e nessun ingresso non ha interfacce: è una libreria, oppure Daodan non ha letto l'ingresso. Non si sceglie a intuito. Dove i segni si contraddicono (un `index.html` in un pacchetto che espone `exports` o `types`; un framework applicativo senza nessun ingresso) è una lacuna `interface_uncertain` con i due segni.
6. **Le interfacce desktop Python si riconoscono leggendo il codice;** eseguirle resta fuori (deciso dal proprietario il 19 novembre 2026; motivo 8). La radice dell'applicazione e le classi di finestre, dialoghi e schede di un toolkit sono dati del registro, non codice ([flussi e mappa](2026-11-18-flussi-e-mappa-del-sistema.md), Principio 2).

### 2. Due collegamenti in più

Motivo 2.

Sono import statici risolti, come quelli fra file di codice: nessun tipo di collegamento nuovo.

1. **Ciò che un documento HTML carica:** lo script di `<script src>` e il foglio di `<link rel="stylesheet" href>`. Un percorso relativo si risolve sul file. Un percorso assoluto si risolve attraverso la rotta che lo offre, quando le regole di collegamento coprono quella rotta: è un collegamento dedotto. Senza rotta, il file con lo stesso nome nella cartella del documento è un candidato incerto, mai un legame.
2. **Ciò che il codice incorpora:** il file del progetto incluso alla compilazione. Primo costrutto, dal caso reale: `include_str!` e `include_bytes!` di Rust. Ogni altro costrutto entra con il suo caso ([flussi e mappa](2026-11-18-flussi-e-mappa-del-sistema.md), 1.7).
3. Chi offre una cartella di file statici con una chiamata di libreria si esprime nelle regole di collegamento del progetto, come ogni rotta.

### 3. Catalogo delle superfici

Motivo 3.

1. Il registro prende un campo opzionale `surface`, dominio chiuso `web`, `webview`, `desktop`, `windows`, `android`, ammesso solo con `category: "framework"`. Una voce con `surface` ha `type: "schermata"`.
2. Prima iterazione, sulle voci che il registro ha già:
   - `web`: `react`, `vue`, `angular`, `angularjs`, `sveltejs`, `sveltekit`, `solidjs`, `qwikjs`, `preactjs`, `litjs`, `alpinejs`, `nextjs`, `nuxtjs`, `astro`, `remixrun`, `gatsby`, `blazor`, `phoenix-liveview`, `streamlit`, `gradio`;
   - `webview`: `electron`, `tauri`, con i segni `tauri.conf.json` e `tauri.conf.json5` accanto a `tauri.conf.js`.
3. Le pagine per convenzione: `app/**/page.*` e `pages/**` per Next.js, `app.vue` e `pages/**/*.vue` per Nuxt, `src/routes/**/+page.svelte` per SvelteKit, `src/pages/**` per Astro, `app/routes/**` per Remix, i `.razor` con `@page` per Blazor.
4. `react-native`, `android` e `dotnet-maui` passano da `"dispositivo"` a `"schermata"`: sono l'app. `"dispositivo"` resta per l'hardware e per il nodo della sezione 4.
5. `htmx` è una libreria e resta senza `surface`: una pagina HTML che la usa è già un ingresso per la sezione 1. `vuejs` non ha una categoria: va chiarito se è un doppione di `vue`.
6. Ogni voce nuova (`wails`, `nicegui`, i toolkit desktop e Windows, i loro segni fuori dai gestori di pacchetti come le proprietà MSBuild o l'import di `tkinter`) entra con un caso reale nel corpus. Oggi il corpus non ne ha. Le interfacce desktop Python entrano con il loro caso reale (1.6).

### 4. La catena: dispositivo, guscio, pagina

Motivo 4.

1. Sopra ogni interfaccia c'è un nodo `dispositivo`, dedotto dalla superficie: `web` dà il browser; `webview`, `desktop` e `windows` danno il PC; `android` dà il telefono. Un nodo per tipo di dispositivo nel sistema. La freccia verso l'interfaccia è dichiarata: un capo non ha codice.
2. Guscio e pagina sono due nodi collegati quando la configurazione del guscio punta ai file della pagina: `frontendDist` e `devUrl` di Tauri e Wails, `main` e i file caricati per Electron. Vale nello stesso modulo e fra due moduli.
3. Ciò che passa fra pagina e guscio (i comandi che il guscio offre, gli eventi) è un tipo di legame con il suo adattatore ([flussi e mappa](2026-11-18-flussi-e-mappa-del-sistema.md), Principio 3) e non è di questa spec. Senza, la freccia dice solo che sono collegati.
4. Dall'alto la catena è una linea; da vicino fra due anelli possono passare molte frecce nei due sensi.

### 5. `builds` e `starts`

Motivo 5.

Due faccette della pre-mappa, come `tests`, con identità `(root, declared_in)`. Questa sezione sostituisce la sezione 3 del registro dell'esecuzione.

1. **Fonti, solo dichiarate:** `package.json#scripts` (`build`; `start` e `dev`, distinti da `mode`), `angular.json` (`architect.build`, `architect.serve` dei progetti `application`), `tauri.conf.*` (`beforeBuildCommand`, `beforeDevCommand`, `devUrl`), `wails.json`, `pyproject.toml` (`gui-scripts`, `scripts`), i target `bin` di Cargo, i `.csproj` eseguibili, `CMD` ed `ENTRYPOINT` con `EXPOSE` di un Dockerfile che copia il modulo, il servizio di Compose che lo costruisce.
2. **Esecutore:** quello delle `toolchains` del modulo o del suo workspace; poi quello del lockfile (`pnpm-lock.yaml`, `yarn.lock`, `bun.lock`, `bun.lockb`); altrimenti `npm`. Per la JVM il wrapper dichiarato, per Python `uv` o `poetry` dal loro lockfile. Il parser dei rinvii fra script (`THROUGH` in `premap/npm_tests.py`) oggi conosce `npm`, `pnpm` e `yarn`: va esteso a `bun`.
3. **Scarti:** uno script `dev` o `start` che lancia solo un test runner, un controllo in watch o un comando nudo senza sottocomando (`"tauri": "tauri"`) non è un avvio.
4. **Porta:** solo da un letterale: `--port N`, `-p N`, `PORT=N`, la configurazione statica dello strumento, `devUrl`, `EXPOSE`, `ports`. Altrimenti `port: null`, mai un valore predefinito presunto.
5. **`needs_build`:** vero quando il comando è il server di produzione di un framework che legge artefatti compilati (tabella chiusa: `next start`, `nuxt start`, `vite preview`, `astro preview`) o punta a un percorso del modulo che non è nello snapshot. Rimanda alla voce `builds` dello stesso modulo.
6. **Lacune:** `no_start_command`, `port_not_declared`, `build_command_missing`.

### 6. Dove sta il risultato

Motivo 6.

1. `builds` e `starts` stanno in `premap.json`.
2. Le interfacce stanno fra i candidati della scheda del sistema, ciascuna con: ingresso, membri, superficie, dispositivo, guscio o pagina collegati, il suo `starts`, lo stato di esecuzione e le lacune.
3. Lo stato di esecuzione è `supported` per `web` e `webview` con un ingresso e un avvio, `incomplete` quando manca uno dei due, `deferred` per le altre superfici.
4. `technologies.json` non cambia.
5. **Il gestore di un controllo** e la funzione che un legame nomina li dà l'indicizzatore ufficiale del linguaggio nel container preparato (scip-typescript per JSX, TSX e Svelte; lo strumento di Vue; scip-python), dopo il ripristino delle dipendenze del progetto: nessun lettore scritto a mano accanto a lui. Senza container resta la lettura generica dall'albero, e il passo dice il buco (deciso dal proprietario il 20 novembre 2026; motivo 9).

### 7. Esecuzione: solo `web` e `webview`

Motivo 7.

Si innesta sulla corsa del programma (registro dell'esecuzione, sezione 4): stesso pod senza rete, servizi della CI accanto, registri attivi sui processi del progetto.

1. **Preparazione:** le `toolchains` del modulo, le dipendenze del progetto e, dal magazzino di Daodan, un browser senza interfaccia. La preparazione è una per analisi: questa corsa parte dal container che la prima preparazione ha lasciato, senza un'installazione sua ([pipeline di analisi](2026-11-15-pipeline-di-analisi.md), «Preparazione»; motivo 10). Il progetto non deve usare Playwright. Se l'avvio scelto ha `needs_build`, gira prima `builds`; un fallimento è una lacuna `build_failed` con la coda del log.
2. **Comando:** una voce `starts` con `mode: "start"`, altrimenti `mode: "dev"`. Daodan non modifica il comando dichiarato.
3. **Porta:** quella dichiarata. Senza, Daodan legge l'indirizzo locale che il processo stampa all'avvio, entro il limite; se non lo stampa, `port_not_declared`. Mai una scansione.
4. **Pagine: un'esplorazione.** Deciso dal proprietario il 20 novembre 2026, al posto di «il browser apre ogni ingresso di ogni interfaccia e le rotte senza parametri» (motivo 11). Si prova ogni rotta, ogni collegamento e ogni controllo raggiungibile. Semi: le rotte lette in modo statico (pre-mappa, Noir, le pagine del meta-framework) e i collegamenti trovati aprendo le pagine; per ogni pagina i controlli dall'albero di accessibilità, ognuno azionato una volta, con il registratore che dice quali funzioni partono. Prima si valuta uno strumento pronto per l'esplorazione. Nel container, senza rete verso l'esterno e su dati di prova: un controllo che cancella, paga o invia agisce solo lì. Per ogni pagina si tengono gli scambi verso il backend, gli errori della pagina e le catene dell'albero delle chiamate; la radice di quelle catene è l'ingresso. La risposta dichiara i limiti: pagine dietro un accesso senza una credenziale di prova, moduli che chiedono valori, stati non raggiunti entro il tetto di passi.
5. **Pagina offerta dal server del progetto:** si avvia il modulo che offre la rotta e il browser apre quella rotta.
6. **`webview`:** Electron si avvia con uno schermo virtuale e il browser si collega alla sua finestra. Tauri e Wails chiedono un driver della webview; dove manca è una lacuna `webview_driver_unavailable` e si esercita la sola pagina come `web`, dichiarando `shell_not_exercised`.

Le superfici `desktop`, `windows` e `android` sono riconosciute e non eseguite: lacuna `ui_execution_deferred:<surface>`. Il loro disegno è nella [roadmap](../roadmap.md).

## Limiti

- Una pagina composta dal server con un template è un ingresso solo se le regole di collegamento dicono quale rotta la offre.
- Una pagina che il bundler crea senza un file nello snapshot non ha un ingresso: lacuna `entry_not_found`.
- Il dispositivo dedotto dice il tipo, non quale telefono o quale browser.
- La tabella di `needs_build` è chiusa: un server di produzione fuori tabella parte senza build e fallisce con il suo errore.
- Un processo che non dichiara la porta e non stampa l'indirizzo non si esercita.
- Senza l'adattatore dei comandi fra pagina e guscio, si vede ciò che il guscio offre e non chi lo chiama.

## Prova

Parametri e soglie nel README del benchmark, scritti prima di ogni misura.

1. **Registro** (`tests/test_codebase_map_service_registry.py`): `surface` nel dominio chiuso, solo su `framework`, sempre con `type: "schermata"`; le aggiunte sono idempotenti.
2. **Fixture nuove** in `benchmarks/project-model`, con le attese scritte prima del codice:
   - un server che incorpora e offre una pagina senza manifesto né framework, in miniatura dal caso reale;
   - un pacchetto con due pagine dichiarate nel bundler;
   - una libreria con un `index.html` di prova, che deve dare `interface_uncertain`.
3. **Fixture esistenti:** `js-vite-react-ts`, `js-nextjs` (`needs_build`), `js-angular` (la libreria `projects/ui-kit` non è un'interfaccia), `js-static-html`, `sys-rust-tauri` e `mix-poly-firebase` (guscio e pagina).
4. **Corpus** (le 180 fixture con `expected.json`, su Modal): nessuna regressione su framework, servizi e pre-mappa; interfacce trovate per superficie, copertura di ingressi, `builds` e `starts`, lacune per tipo, falsi positivi sui moduli backend, CLI e libreria. La misura vale per `web` e `webview`: il corpus non ha toolkit desktop o Windows, ed Electron non è in nessun `package.json`.
5. **Esecuzione** (su Modal): su `js-vite-react-ts`, su `js-nextjs` e sulla fixture del server con la pagina incorporata il browser nel pod apre gli ingressi, le catene hanno l'ingresso come radice e sull'host non compare nessun file. Su una pagina con due controlli che azionano gestori diversi, ogni chiamata è attribuita al suo controllo, in un progetto che non usa Playwright (revisione esterna del 20 novembre).

## Motivi delle scelte

Una voce per scelta; la regola la cita con «(motivo n)». Nessuna è ancora misurata: le prove sono quelle della sezione «Prova».

1. **Un'interfaccia nasce da un ingresso** (1). Perché: il caso reale del pannello di amministrazione di tre file, incorporato da un server Rust e offerto su tre rotte, non è oggi né un modulo né una schermata («Comportamento attuale»): il modulo che la toolchain vede e la parte che una persona nomina sono due cose. Scartato: un'interfaccia per manifesto o per framework UI dichiarato, che darebbe interfacce alle librerie e nessuna al pannello.
2. **Due collegamenti in più, come import** (2). Perché: lo stesso caso: la pagina carica lo script e il server la incorpora, e oggi nessuno dei due legami si legge. Scartato: un tipo di collegamento nuovo; ogni altro costrutto entra con il suo caso reale ([flussi e mappa](2026-11-18-flussi-e-mappa-del-sistema.md), 1.7).
3. **Il catalogo delle superfici nel registro** (3). Perché: il registro mette `schermata` su sei voci, `altro` sui framework web principali e `dispositivo` sull'app invece che sul telefono. Scartato: dedurre la superficie dal codice ogni volta.
4. **Dispositivo, guscio, pagina** (4). Perché: un flusso entra in una schermata da un dispositivo, e la superficie basta a dedurne il tipo. Scartato: un nodo per ogni browser o telefono, che lo snapshot non dice (vedi «Limiti»).
5. **`builds` e `starts` dichiarati** (5). Perché: la pre-mappa estrae `tests` e `toolchains`, non come si compila e si avvia un modulo, e una porta presunta avvierebbe il programma sbagliato. Scartato: comandi e porte per convenzione di Daodan.
6. **Il risultato fra i candidati della scheda** (6). Perché: non chiede una provenienza nuova e `technologies.json` non cambia. Scartato, per ora: un modulo logico nel grafo dei moduli («Da decidere»).
7. **Eseguire solo `web` e `webview`** (7). Perché: un browser nel container basta; desktop, Windows e Android chiedono emulatori o macchine virtuali ([roadmap](../roadmap.md)). Scartato: eseguire tutte le superfici nella prima iterazione.
8. **Le interfacce desktop Python dal codice** (1.6). Deciso dal proprietario il 19 novembre 2026. Perché: nel caso con interfacce Python le regole del modello avevano `attiva` per due segnali di una scheda e nulla per l'app Tkinter, la finestra principale e i dialoghi, mentre il riferimento ha 3 applicazioni, 8 schermate e 6 flussi che partono da un controllo su 62 nodi e 19 flussi; letti dall'albero, 26 legami di un controllo, 26 con il gestore risolto e 14 con l'etichetta. Scartato: eseguirle, che chiede un esecutore desktop. Prova: README di [`benchmarks/system-map`](../../benchmarks/system-map/README.md), «Dopo la riparazione della lettura dall'albero».
9. **Il gestore dall'indicizzatore ufficiale** (6.5). Deciso dal proprietario il 20 novembre 2026. Perché: un gestore che arriva da un altro file o passa come proprietà lo risolve l'indice, non la forma; un lettore scritto a mano accanto a scip-typescript (`framework.cjs`) è stato cancellato quel giorno perché va contro la regola delle soluzioni pronte. Motivo e numeri: [flussi e mappa](2026-11-18-flussi-e-mappa-del-sistema.md), motivo 14.
10. **Una preparazione per analisi** (7.1). Deciso dal proprietario il 20 novembre 2026, contro la raccomandazione di rimandarlo. Perché: un progetto Node ripristina oggi le dipendenze tre volte. Motivo: [flussi e mappa](2026-11-18-flussi-e-mappa-del-sistema.md), motivo 15.
11. **L'esplorazione al posto delle sole pagine dichiarate** (7.4). Deciso dal proprietario il 20 novembre 2026, diverso dalla raccomandazione (aprire solo le pagine del `webServer` che il progetto dichiara). Perché: l'obiettivo del proprietario è tutti o quasi i controlli, ognuno mancato con la sua causa ([flussi e mappa](2026-11-18-flussi-e-mappa-del-sistema.md), motivo 14); il documento non dà un altro motivo. Scartato: le sole pagine dichiarate. Prova: nessuna ancora (piano del 20 novembre, task 11).

## Da decidere

- Dove vive un'interfaccia: fra i candidati della scheda del sistema, come nella sezione 6, oppure come modulo logico che la macchina ricava nel grafo dei moduli. La prima non chiede una provenienza nuova, ma poggia su una parte della spec del 18 novembre non ancora applicata.
- Se Daodan può passare host e porta a un dev server di una tabella chiusa quando il progetto non li dichiara. Oggi no: il comando dichiarato non si tocca.
- Se un progetto multipiattaforma con un bersaglio web (`flutter`, `expojs`, MAUI) si esegue come `web` già nella prima iterazione.
- Un solo pilota o due: il browser dove c'è un'interfaccia e il richiedente del registro dell'esecuzione per gli ingressi senza pagina. È la divisione consigliata.
- Quali file contano per il nodo `filesystem` proposto nella spec del 18 novembre: i file incorporati alla compilazione sono codice e non contano.

**Per modificare questa spec:** una regola o un campo in più solo per un caso reale del corpus mancato o classificato male in modo riproducibile.
