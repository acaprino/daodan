# Daodan: il refactoring completo, il disegno e le sue ondate

**Stato:** chiesta dal proprietario il 25 novembre 2026. È l'unica spec di Daodan. Non è l'elenco di ciò che resta: è un refactoring completo. Daodan si riorganizza attorno a una pipeline di otto step, ognuno con una competenza sola, moduli a sé che attingono da anagrafiche globali; tutto il resto (ciò che ogni step usa, le superfici e come si eseguono, i servizi comuni, flussi, review, app) si ordina su quella. Una decisione nuova si scrive qui.

**Due parti.** Prima il disegno: com'è Daodan a refactoring finito. Poi le ondate: il lavoro per arrivarci, nell'ordine in cui si fa, ognuna con il suo cancello. Nelle ondate entra anche ciò che le spec e i piani di prima avevano lasciato da fare o fatto in parte, riordinato sul disegno nuovo: nulla di quel lavoro resta fuori da qui.

**Le spec e i piani di prima sono stati tolti dal repository il 25 novembre**, su richiesta del proprietario. Una voce cita il documento e la sezione da cui viene, con i suoi motivi e le sue misure: si leggono nella storia di git, al commit `614c940` (`git show 614c940:docs/specs/<nome>.md`). L'elenco è in fondo.

**Da dove viene lo stato.** Per ciò che è del 25 novembre, dalle decisioni di quel giorno e dal codice letto. Per ciò che viene dai documenti di prima (19 spec, 13 piani, la roadmap), dallo stato che quei documenti dichiaravano, non riverificato sul codice salvo dove è scritto «visto nel codice».

**Come si legge.** Un'ondata è un insieme di voci che si chiudono insieme e ha un cancello: la prova che la dichiara finita. Un'ondata parte quando quelle da cui dipende hanno passato il cancello. Dentro un'ondata l'ordine è quello scritto. Ogni voce è marcata: **[deciso]** approvata dal proprietario, **[proposta]** mai approvata, **[misura]** una misura da fare, **[difetto]** un errore noto.

| Ondata | Che cosa chiude | Dipende da |
| --- | --- | --- |
| 0 | Il punto di partenza: ciò che è scritto e non è mai stato verificato | — |
| 1 | `1_list_files`: il linguaggio di ogni file | 0 |
| 2 | `3_recognize_stack` e `4_find_modules`: lo stack prima, i moduli dopo | 0 |
| 3 | `5_find_entry_points`: rotte, pagine ed eventi fuori dalla pre-mappa | 2 |
| 4 | L'orchestratore e i nomi degli step | 2, 3 |
| 5 | `6_link_calls`: ciò che resta degli indicizzatori | 2 |
| 6 | Il container e la preparazione | — |
| 7 | `7_run_and_observe`: test, programma, interfacce | 3, 6 |
| 8 | `8_assemble_graph`, flussi e mappa del sistema | 3, 5 |
| 9 | Ricerca e review | 8 |
| 10 | L'app e l'esploratore, adeguati alla pipeline | 4, 8 |
| 11 | Le superfici differite: desktop Linux, Android, Windows | 7 |

Le ondate 1, 2 e 6 non dipendono l'una dall'altra e possono procedere insieme.

## I principi

1. **Una competenza per step.** Chi analizza lo stack non trova i moduli; chi trova i moduli non cerca da sé quale strumento di build c'è; chi tiene il modello di build non tiene rotte ed eventi.
2. **Un padrone per fatto.** Uno step non riscopre ciò che un altro stabilisce: lo chiede a lui. Dove il padrone non ha potuto stabilirlo, chi ne ha bisogno usa un ripiego e lo scrive accanto al dato.
3. **Ogni step è un modulo a sé.** Dichiara ciò che legge, ciò che scrive e che cosa succede se fallisce; si può usare da solo per il suo compito, e nella pipeline lavora con gli altri. Non conosce l'interfaccia, il trasporto né il motore LLM.
4. **Le anagrafiche sono dati globali** (`daodan/data/`), non costanti sparse nel codice: gli step le consultano, e una voce nuova è una riga, non un `if`.
5. **Lo strumento ufficiale, mai una regola a mano.** Per ogni linguaggio, strumento di build e framework Daodan usa il suo parser, il suo compilatore, il suo comando. Dove nessuno dà il dato resta un lettore nostro, con scritto accanto quale strumento è stato valutato.
6. **Il codice del progetto gira solo nel container di Daodan**, mai sull'host. Senza container il passo è una lacuna con la sua causa.
7. **Ciò che non si è potuto fare si scrive**: una lacuna con causa e rimedio, mai un silenzio.

## La pipeline, com'è decisa

Otto step, ognuno con una competenza sola, decisi dal proprietario il 25 novembre 2026. Nel codice del riordino non c'è ancora nulla: oggi gli step sono `scan`, `stack`, `parse`, `analyze`, `dynamic`, `union`, con l'elenco dei file e la lettura del codice fatti prima della pipeline.

**La regola.** Ogni step parte da ciò che gli step prima hanno stabilito. Ogni fatto ha un padrone solo: uno step non riscopre ciò che un altro stabilisce, lo chiede a lui; dove il padrone non ha potuto stabilirlo (manca il container), chi ne ha bisogno usa un ripiego e lo scrive accanto al dato. Ogni step ha una competenza sola: chi analizza lo stack non trova i moduli, chi trova i moduli non cerca da sé quale strumento di build c'è, chi tiene il modello di build non tiene rotte ed eventi.

| Step | Competenza | Deve sapere prima, e da chi | Che cosa scrive |
| --- | --- | --- | --- |
| `1_list_files` | L'elenco dei file | La cartella e il perimetro: da chi avvia l'analisi | Di ogni file percorso, dimensione, hash e linguaggio |
| `2_read_code` | Il contenuto di ogni file | Quali file e in che linguaggio: dal 1 | Simboli, import e riferimenti, e come è andata la lettura |
| `3_recognize_stack` | Lo stack | I file: dal 1 | Strumenti di build, toolchain, framework, librerie e servizi, ognuno con il file che lo prova. Nessun modulo |
| `4_find_modules` | Il modello di build | Quali strumenti di build ci sono e dove: dal 3 | Moduli, unità, toolchain, pacchetti e grafo dei pacchetti, comandi di test, di avvio e di build, servizi. Poi le tecnologie del 3 assegnate ai moduli |
| `5_find_entry_points` | Dove entra un utente o una richiesta | Quali framework ci sono e dove: dal 3. I simboli: dal 2. I pacchetti ripristinati: dal 4 | Rotte, pagine ed eventi, ognuno legato alla sua funzione |
| `6_link_calls` | Dove arriva ogni chiamata | I riferimenti: dal 2. Unità e build: dal 4. L'ambiente preparato | Gli archi provati |
| `7_run_and_observe` | Ciò che viene chiamato davvero | I comandi di test, di avvio e di build: dal 4. Le pagine da aprire: dal 5. Il grafo statico: dal 6 | Gli archi osservati; i controlli premuti, con le funzioni partite |
| `8_assemble_graph` | L'unione, e ciò che manca | Tutto | Il grafo completo: gli archi fra moduli, gli ingressi uniti alle loro definizioni, l'osservato contro il provato, le lacune |

| Step | Strumento sotto | Oggi nel codice |
| --- | --- | --- |
| `1_list_files` | Git per ciò che è ignorato (`tree_scope.py`); l'anagrafica dei formati (`data/file-formats.json`); le regole del linguaggio (`languages/detect/`) | `file_inventory.write`, prima della pipeline. go-enry gira in `scan` e la lettura non lo usa |
| `2_read_code` | tree-sitter, `ast` di Python; SQL e PL/SQL con lettori nostri | `snapshot.write_reading`, prima della pipeline. Lo step `parse` dice solo il piano e sparisce |
| `3_recognize_stack` | stack-analyser, il nostro fork | Step `stack`, secondo in `STEPS`: gira dopo `scan` e ne legge moduli e pacchetti |
| `4_find_modules` | Lo strumento di build vero nel container (cargo, gradle, maven, npm, `tsc`, cmake, …); senza container i lettori dei manifest | Step `scan`, primo in `STEPS`: ogni sorgente cerca da sé il suo file nell'inventario |
| `5_find_entry_points` | Lo strumento del framework (`next typegen`, `react-router routes`, `nuxt prepare`, `svelte-kit sync`, i compilatori di Angular e Astro), Noir, e tree-sitter con le query di `data/entry-queries.json` | Diviso in due: le sorgenti dei framework sono in `scan` e scrivono nella pre-mappa (`framework_entries`, `noir_entries`); il legame alle funzioni (`binder.py`, `entries.py`) avviene dopo la pipeline |
| `6_link_calls` | Un indicizzatore SCIP per tecnologia; per i fogli di stile i loro compilatori | Step `analyze` |
| `7_run_and_observe` | Un registratore per linguaggio (`*_record.*`); per l'app, Chromium senza interfaccia di Playwright | Step `dynamic`; l'app si avvia solo con npm |
| `8_assemble_graph` | Nessuno | Step `union`: dice ciò che il grafo ha e non ha, non unisce ancora |

**La pre-mappa è il modello di build**, l'uscita del 4: non tiene più rotte, pagine ed eventi. Il meccanismo che esegue un comando nel container e ne legge l'uscita (`premap/container_runner.py`) è un servizio comune agli step 4 e 5: oggi è della pre-mappa, ed è per questo che gli strumenti dei framework erano finiti lì.

**Chi riconosce è uno solo.** Uno strumento di build o un framework che stack-analyser non conosce si aggiunge al fork (oggi mancano CMake, Bazel, Meson, Make, autotools, sbt, .NET SDK, Mix). In Daodan un'anagrafica, `data/build-tools.json`, lega ogni voce dello stack all'adattatore del 4 che la usa.

**I nomi.** Il numero d'ordine è nel nome dello step (`NAME`, eventi, giornale, documenti, interfaccia). Un modulo Python non può iniziare con una cifra: la cartella è `step_1_list_files/`, la classe `ListFiles`. Il piano non è uno step: è ciò che Daodan dà al chiamante prima e durante («Il piano: sempre intero, sempre al chiamante»).

**Che cosa usa ogni step**, per linguaggio, strumento di build e framework: la pagina `docs/pipeline/`, scritta dalle dichiarazioni del codice (`daodan/core/pipeline_tree.py`).

### Gli strumenti nativi, e dove entrano

Lo stack dice *quali* linguaggi, strumenti di build e framework ci sono. I loro strumenti nativi si chiamano dopo, negli step che producono nodi e archi, ognuno per ciò che solo lui sa. Sono quattro famiglie.

| Famiglia | Esempi | Che cosa dà | Step |
| --- | --- | --- | --- |
| Strumento di build | cargo, gradle, maven, npm, `tsc`, cmake, meson, bazel, make, `dotnet`, uv, go | Moduli, unità, pacchetti risolti, comandi | `4_find_modules` |
| Strumento del framework | `next typegen`, `react-router routes`, `nuxt prepare`, `svelte-kit sync`, i compilatori di Angular e Astro | Rotte, pagine, eventi dei template | `5_find_entry_points` |
| Compilatore del linguaggio, attraverso un indicizzatore SCIP | il compilatore TypeScript, Pyright, il compilatore Java dentro Maven o Gradle, rust-analyzer, Clang | Dove arriva ogni chiamata | `6_link_calls` |
| Ciò che esegue l'interfaccia | il browser; una webview; un emulatore | Quale controllo fa partire quale funzione, davvero | `7_run_and_observe` |

- **Un framework senza uno strumento suo** si legge dall'albero sintattico (tree-sitter) con una query per grammatica; le query sono dati (`data/entry-queries.json`). È il caso di React: il JSX lo legge il compilatore TypeScript, un `onClick` una query.
- **Noir** dà le rotte dei backend senza eseguire il progetto, per ogni framework che non ha uno strumento che le elenchi.
- **Un controllo ha due prove.** Quella statica dice che è legato a una funzione; quella dinamica dice che, azionato, quella funzione è partita. La seconda conferma la prima.

### Le chiamate HTTP hanno due capi

- **Chi offre la rotta:** lo dice lo strumento del framework, oppure Noir (`5_find_entry_points`).
- **Chi la chiama:** lo dice il compilatore del linguaggio, che risolve la chiamata fino a una funzione dell'anagrafica dei client HTTP (`data/http-clients.json`). Una funzione del progetto che avvolge un client si prova dai dati del compilatore, non dal suo nome (`6_link_calls`).
- **I due capi si uniscono** dove percorso e metodo coincidono, in `8_assemble_graph`. Lo stesso vale per eventi, code e tabelle: ogni tipo di legame ha il suo adattatore, e il codice dei legami non nomina un framework.

### Le superfici e come si eseguono

Un'interfaccia nasce da un ingresso (una pagina dichiarata, la pagina di un meta-framework, una pagina che il codice incorpora o offre su una rotta), non da un manifesto. La sua superficie è un campo dell'anagrafica delle tecnologie (`surface`), e decide con che cosa `7_run_and_observe` la esegue. Sopra ogni interfaccia sta il dispositivo dedotto dalla superficie: il browser, il PC, il telefono.

| Superficie | Esempi | Con che cosa si esegue | Che cosa serve | Stato |
| --- | --- | --- | --- | --- |
| `web` | React, Vue, Angular, Svelte, Next.js, Nuxt, Astro, Streamlit, Gradio | Chromium senza interfaccia con Playwright: legge i controlli dall'albero di accessibilità, li aziona uno per uno e registra quale funzione parte | L'avvio dichiarato del progetto | Nel codice, solo per app avviate con npm |
| `webview` | Electron, Tauri, Wails | Uno schermo virtuale (`Xvfb`) e lo stesso pilota del browser collegato alla webview: CDP per Electron, WebDriver per Tauri e Wails. Si osservano insieme la pagina e il processo nativo del guscio | Il driver della webview; dove manca si esercita la sola pagina e lo si dichiara | Ondata 7 |
| `desktop` (Linux) | PyQt, PySide, Tkinter, GTK, Kivy, Flet, Avalonia, Uno Platform, JavaFX | `Xvfb` o un compositor Wayland senza schermo, con i registratori di linguaggio che esistono già; un pilota su AT-SPI o sull'introspezione del toolkit per azionare i controlli | Il pilota, da costruire | Ondata 11 |
| `android` | Android SDK, React Native, Expo, Flutter, MAUI | L'emulatore ufficiale senza finestra, con una system image scaricata da `sdkmanager` | `/dev/kvm` dal motore; il consenso ai termini dell'SDK e a circa 4 GB | Ondata 11 |
| `windows` | WinForms, WPF, WinUI 3, UWP | Wine con `Xvfb` per WinForms e WPF compatibili; una VM Windows in un container (QEMU/KVM) per WinUI 3, UWP e il resto | Per la VM `/dev/kvm`, circa 4 GB di RAM e da 25 a 32 GB di disco, con il consenso | Ondata 11 |
| macOS e iOS | AppKit, SwiftUI, UIKit | — | — | Fuori perimetro: nessun simulatore gira in un container Linux e la licenza Apple lega l'esecuzione a un Mac |

Regole che valgono per tutte:

1. **Nulla dell'host.** Browser, emulatori e runtime si scaricano nel magazzino di Daodan e girano nel container, senza rete verso l'esterno e sui soli dati e credenziali di prova che la CI del progetto già prepara.
2. **Il consenso prima del peso.** Un download con termini di licenza o di qualche gigabyte parte solo dopo l'approvazione esplicita dell'utente; senza, il passo è la lacuna `approval_required`.
3. **Una superficie riconosciuta e non eseguita è una lacuna**, `ui_execution_deferred:<superficie>`; senza `/dev/kvm` è `kvm_unavailable`; senza pilota è `ui_driver_not_implemented`.
4. **Un progetto multipiattaforma** (Flutter, Expo, Compose) si esegue sul suo bersaglio `web` o desktop Linux, quando lo dichiara: senza emulatore.
5. **Le interfacce desktop Python** si riconoscono dal codice (deciso il 19 novembre); la loro osservazione dinamica ha avuto un «no per ora» (20 novembre) ed entra con l'ondata 11.
6. **Una voce nuova dell'anagrafica** (NiceGUI, Wails, un toolkit desktop) entra con un caso reale nel corpus.

### Come si sa che cosa lanciare

Vale per ogni ecosistema, e per tre cose: come si lanciano i test, come parte l'app, come si costruisce. Un comando non si indovina mai: viene da una fonte, e porta scritto da quale. Dove nessuna fonte lo dà, il passo è una lacuna e non lancia nulla.

Le fonti, dalla più forte alla più debole. Una fonte più forte vince su una più debole, che resta annotata.

| Fonte | Che cosa dice | Grado | Stato |
| --- | --- | --- | --- |
| L'utente | Il comando, scritto da chi conosce il progetto, tenuto nell'archivio di Daodan e mai nel progetto | `confermato` | **[proposta del proprietario, 25 novembre]** |
| Lo strumento di build | Il comando che lo strumento stesso prevede: `npm test`, `go test`, `cargo test`, i test di Gradle e Maven, `dotnet test`, CTest | `dichiarato` | Nel codice |
| I file del progetto | Lo script `test`, `start` o `dev`; la configurazione di pytest; una riga `python -m unittest` in `tox.ini` o in un makefile. Uno script con un nome qualsiasi vale per il runner che lancia, non per come si chiama | `dichiarato` | Nel codice |
| La CI del progetto | Il passo che la CI esegue per i test, con i servizi che avvia accanto e i passi di prima | `dichiarato` | In parte: servizi e passi di prima sì, il comando dei test no |
| Un modello piccolo, in locale | Sceglie fra i comandi che il progetto scrive da qualche parte (script, bersagli di un makefile, passi della CI, blocchi di codice del README) quello che lancia i test | `proposto` | **[proposta del proprietario, 25 novembre]** |

Regole per il modello:

1. **Sceglie, non scrive.** Risponde con una chiamata di funzione il cui argomento è un comando già presente in un file del progetto, con file e riga. Un comando che non è in nessun file viene rifiutato.
2. **Il suo esito è `proposto`**, mai `dichiarato`: lo si vede nel grafo e nelle lacune, e l'utente può confermarlo o correggerlo.
3. **Gira dove gira tutto il resto:** il comando scelto parte solo nel container, senza rete. Il modello è facoltativo, in locale e senza rete, come gli embedding: senza, resta la lacuna.
4. **Non entra nel nucleo:** è un adattatore dietro lo stesso contratto dei motori, e lo step che trova i comandi non sa quale modello risponde.
5. **Prima la misura.** Il corpus ha già i comandi attesi di ogni progetto. Si confrontano, sugli stessi casi: i lettori di oggi; con la CI come fonte; un modello piccolo così com'è, con le chiamate di funzione; lo stesso modello specializzato. Si specializza solo se la versione così com'è non basta e quella specializzata sì.

### Il piano: sempre intero, sempre al chiamante

Deciso dal proprietario il 25 novembre 2026. Daodan dà sempre a chi lo chiama (l'interfaccia, un harness via MCP, la riga di comando) il piano completo di ciò che farà, e lo tiene aggiornato mentre lo fa.

1. **Intero, e prima.** Il piano c'è prima che parta qualunque cosa, e contiene ogni step e, sotto ogni step, ogni azione: non solo le analisi, anche scaricare uno strumento, scaricare le dipendenze, preparare un container, costruire il progetto, lanciare una suite di test, avviare l'app, provare l'interfaccia.
2. **Dice che cosa fa, non come.** Un'azione è una frase che chi usa Daodan capisce: «scarica le dipendenze del modulo `web`», «lancia i test di `api`», «avvia l'app `web` e prova i suoi controlli nel browser», «collega le chiamate del codice TypeScript». Lo strumento, il comando e la versione sono un dettaglio che si apre a richiesta, non il testo del piano.
3. **Ogni azione dice su che cosa agisce** (quale modulo, quale cartella, quanti file) e tre fatti che contano per chi guarda: se esegue codice del progetto, se gira nel container, se scarica qualcosa dalla rete e quanto pesa.
4. **Uno stato per azione, aggiornato mentre accade:** da fare, in corso (con l'avanzamento), fatta, fallita, saltata perché è già fresca, non possibile. Fallita e non possibile portano la causa e il rimedio.
5. **Anche ciò che non si farà è nel piano**, con il motivo: manca il container, il progetto non dichiara come lanciare i test, serve un consenso. Un'azione che aspetta il consenso dell'utente (un download pesante, una licenza) si vede come tale, e parte solo dopo.
6. **Un oggetto solo, uguale per ogni chiamante.** Chi chiama legge il piano con i suoi stati; non lo ricostruisce mettendo insieme gli eventi. Il giornale degli eventi resta, come cronaca.
7. **I tipi di azione sono un elenco chiuso**, con le sue parole: così l'interfaccia, MCP e la riga di comando dicono la stessa cosa allo stesso modo.

Oggi il piano copre solo la lettura, il collegamento delle chiamate e gli osservatori, e li nomina per come sono fatti (`resolve:scip-python`); esce una volta sola, come evento; preparazione, download, container, test e avvio dell'app non ci sono.

### L'interfaccia segue la pipeline

Deciso dal proprietario il 25 novembre 2026: l'interfaccia si adegua alla pipeline nuova in tutto e per tutto. Non ha un'idea sua di come è fatta un'analisi: mostra ciò che Daodan le dà.

1. **Mostra il piano, non lo ricostruisce.** Gli step, le azioni e i loro stati sono quelli del piano che riceve. L'interfaccia non tiene un elenco suo di step né dei loro nomi, e non deduce lo stato dagli eventi.
2. **Il percorso sullo schermo sono gli otto step**, con le loro parole: elenco dei file, lettura del codice, stack, moduli, punti di ingresso, chiamate, esecuzione, grafo. Prima c'è la scelta della repository, dopo ciò che si fa sul grafo (flussi, mappa, domande).
3. **Di ogni step si vede che cosa ha trovato**, non solo che è finito: i file per linguaggio; le tecnologie con il file che le prova; i moduli con lo strumento che li ha dati; rotte, pagine ed eventi con la funzione a cui sono legati; le chiamate collegate e quelle rimaste aperte; i test lanciati e i controlli azionati; il grafo e le sue lacune.
4. **Prima di partire si vede che cosa succederà:** che cosa verrà scaricato e quanto pesa, che cosa verrà eseguito e dove. Un consenso si dà lì, sull'azione che lo chiede.
5. **Mentre accade si vede l'azione in corso**, detta per ciò che fa. Un'azione fallita o non possibile dice la causa e il rimedio nel punto in cui sta.
6. **La parola «pre-mappa» esce dall'interfaccia**, con «scan», «stack», «analyze» e gli altri nomi di come è fatto: chi guarda legge ciò che Daodan fa.
7. **La stessa cosa in ogni posto:** la pagina dell'analisi, la mappa e un harness che chiama via MCP leggono lo stesso piano e lo dicono con le stesse parole.
8. **Con i componenti della suite e nient'altro:** Sigrid nella shell di Imago, come ogni schermata di Daodan.

Oggi la pagina dell'analisi ha quattro tappe (Repository, Pre-mappa, Analisi, Sintesi e grafo). Dentro «Analisi» mostra sei fasi con i nomi di prima (Parse, Scan, Stack, Analyze, Dynamic, Union), tenute in un elenco suo e ricostruite dagli eventi. La tappa «Pre-mappa» mostra insieme inventario, linguaggi, tecnologie, unità e dipendenze, cioè il risultato di quattro step diversi.

### Le anagrafiche

Dati globali in `daodan/data/`. Ognuna ha un controllo che dice dove lei e il codice non concordano.

| Anagrafica | Che cosa tiene | Chi la usa | Stato |
| --- | --- | --- | --- |
| `file-formats.json` | Quali file si registrano e con che linguaggio; cartelle in cui non si entra; nomi che non si aprono | `1_list_files` | Nel codice |
| `linguist-catalog.json` | Come Linguist chiama ogni formato accettato | `1_list_files` | Nel codice, scritto dal gem di Linguist |
| `language-rules.toml` | Le regole che distinguono dal contenuto un'estensione condivisa | `1_list_files` | Nel codice; mancano i `.h` e i nomi di file |
| `service-registry.json`, `registry-additions.json` | Nome, tipo, categoria, sito e marchio di ogni tecnologia; in futuro la `surface` | `3_recognize_stack`, l'interfaccia | Nel codice, senza `surface` |
| `build-tools.json` | Ogni strumento di build o toolchain dello stack, con l'adattatore che lo usa | `4_find_modules` | Da fare, ondata 2 |
| `package-managers.json` | I registri dei pacchetti che la preparazione può raggiungere | La preparazione del container | Nel codice |
| `entry-queries.json` | Le query sull'albero sintattico con cui si leggono gli ingressi | `5_find_entry_points` | Nel codice |
| `http-clients.json` | Le funzioni che fanno una richiesta HTTP, come le nomina il compilatore | `6_link_calls`, `8_assemble_graph` | Nel codice |
| Le versioni degli strumenti esterni | Nome, versione, origine (upstream o fork nostro), sha256 | Ogni step | **[proposta]** Oggi sono una sessantina di costanti nei singoli adattatori |

### I servizi comuni

Non sono step: li usa ogni step che deve eseguire qualcosa.

- **Il motore di container:** il Kiri di Daodan su ogni sistema; oggi fuori da Windows è il Docker o il Podman dell'utente.
- **La preparazione, una per analisi:** le toolchain che il progetto dichiara (mise), le dipendenze ripristinate, gli strumenti scaricati nel magazzino e verificati per sha256. Raggiunge solo i registri dei pacchetti, attraverso un proxy; tutto il resto gira senza rete.
- **Il lanciatore dei comandi:** esegue un comando nel container e ne riporta l'uscita. Oggi è della pre-mappa; diventa comune agli step 4 e 5, come lo è già per gli indicizzatori e gli osservatori.
- **Il giornale:** ogni step e ogni adattatore dice quando inizia, come avanza, che cosa non ha potuto fare e come finisce.

### Dopo la pipeline

Sul grafo completo: i flussi (chi scrive, chi legge, le azioni dell'utente), la mappa del sistema, le schede scritte da un motore LLM a scelta, la ricerca, la review. Ogni testo che lascia la macchina o va a un modello passa prima da Secretlint.

## Ondata 0: il punto di partenza

Prima di spostare il codice si chiude ciò che è già scritto e non è mai girato, e si toglie dai documenti ciò che non è più vero: il refactoring parte da uno stato verificato.

1. **[misura]** La suite intera su Modal sul codice del 25 novembre: anagrafica dei formati, modulo del linguaggio, generatore dell'albero della pipeline. Non è mai girata (visto: nessun workflow parte da solo sui test Python).
2. **[misura]** La «Verifica» dello stack dal fork, ferma perché Modal non era raggiungibile: nessuna perdita sul corpus dopo il passaggio, tempo della scansione veloce, prova che nulla del progetto viene eseguito con `cli()` e il Node veri, nuova misura su `develop` (spec stack dal fork, «Verifica»; piano 3, B4 passo 4, B6, B7).
3. **[difetto]** Gli «aperti noti» dello stack: il test instabile di `test_codebase_map_app.py`, `replace => ../local` di Go e i repository `path` di Composer letti come esterni dal fork, 37 marchi senza cornice, Avro duplicato, `technologies.state` che non scrive più la pre-mappa (spec stack dal fork, «Aperti noti»).
4. La pagina costruita `docs/pipeline/` nel repository: oggi è solo nell'artifact `built-docs` del workflow Viewer (visto).
5. `docs/plugins/codebase-map-supporto.md` da rigenerare (`support_table.py build`): cita percorsi che non esistono più (visto; piano ingressi, 14c).
6. Lo stato di due lavori è da accertare sul codice, perché i documenti di prima si contraddicevano: il run di lavoro con il suo aggiornamento, e la copertura dell'intero sorgente (ondata 9, voci 4 e 5). Lo stesso per il task 12 del piano «grafo dall'indice» (ondata 2, voce 8): le caselle erano vuote, la spec della pipeline dichiarava pre-mappa e moduli applicati.
7. `README.md` («How the graph is built») e `docs/plugins/codebase-map.md` («Il disegno», «Dal codice al disegno») descrivono ancora i sette step: vanno portati agli otto. `docs/roadmap.md` è ferma al 19 novembre.
8. Sessantuno file citano ancora le spec e i piani tolti (README dei benchmark, commenti nel codice, documenti di ricerca): sono citazioni di provenienza, valide nella storia di git. Un collegamento che deve restare vivo va portato a questa spec.

**Cancello:** la suite passa su Modal; la «Verifica» dello stack ha il suo verdetto nel README del benchmark; le voci del punto 6 hanno uno stato letto sul codice.

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

1. **[misura]** `benchmarks/stack-build-tools/` su Modal: per ogni fixture, gli strumenti di build che il fork nomina (con la cartella) contro quelli che le sorgenti di oggi trovano da sé. La prova esplorativa del 25 novembre non è una verifica: rilascio `1.27.6-daodan.5` su 104 fixture, fuori da Modal e non salvata. Lì il fork nominava uno strumento o un runtime sul manifest di 124 moduli su 147: tutti quelli npm, Cargo, Go e Maven, 17 su 18 di Gradle, 21 su 24 di Python (ma nominando il backend di build, non Python), nessuno dei 15 di CMake (task 1).
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
2. **[deciso]** Il piano intero al chiamante («Il piano: sempre intero, sempre al chiamante»): ogni step e ogni azione, detti per ciò che fanno, con lo stato aggiornato mentre accade; uguale per interfaccia, MCP e riga di comando. Entrano nel piano la preparazione, i download, i container, la build, le suite di test, l'avvio dell'app e la prova dell'interfaccia, che oggi non ci sono.
3. La dichiarazione comune per ogni famiglia di adattatori (8.8 punto 1): ogni adattatore dichiara anche le azioni che compie, nelle parole del piano.
4. La freschezza controllata in un punto solo, con `step.skipped` (8.8 punto 2); l'uscita degli strumenti come `log` di livello `debug`.
5. **[misura]** Un limite di tempo per stage, dalle durate registrate. Prima va letto che cosa resta del container di uno stage chiuso da fuori (8.9).
6. Il giornale cresce e ogni lettura lo rilegge tutto: un cursore in byte cambierebbe il contratto MCP (8.9).
7. Le prove 2 e 5 di 8.10, mai scritte: le due modalità danno lo stesso grafo; un ripiego è dichiarato accanto al dato.
8. Tre funzioni oltre le 80 righe: `engine_pass.index_stage`, `snapshot.write_reading`, `snapshot._refresh_locked`.
9. **[scelta aperta]** L'ordine delle sorgenti (lista scritta o bisogno dichiarato), `pass` contro `run`, quando cambiano i nomi sul disco, la colonna `producer` (A1).

**Cancello:** nessun nome di prima resta nel codice, salvo il lettore dei giornali vecchi; le prove 2 e 5 passano; su un progetto vero il piano letto prima dell'analisi elenca ogni azione che poi avviene, e nessuna azione avviene senza essere nel piano.

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
9. **[proposta]** Il comando dei test dalla CI del progetto: oggi dalla CI si leggono i servizi e i passi di prima, non il passo che lancia i test («Come si sa che cosa lanciare»).
10. **[proposta]** Il comando detto dall'utente, nell'archivio di Daodan, con il grado `confermato`.
11. **[proposta, misura]** Il modello piccolo che sceglie il comando fra quelli scritti nel progetto: prima il benchmark a quattro bracci sul corpus, poi la scelta fra il modello così com'è e uno specializzato (candidati: Gemma 3 con le chiamate di funzione, FunctionGemma).
12. **[misura]** La corsa Python su Daodan con `--continue-on-collection-errors`; per C# il limite che il registro può chiudere (passo dinamico, «Stato» e 7).
13. Finché l'ondata 11 non è fatta, un modulo con superficie `desktop`, `windows` o `android` è riconosciuto e non eseguito: lacuna `ui_execution_deferred:<superficie>`.

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

## Ondata 10: l'app e l'esploratore, adeguati alla pipeline

Da: spec dell'app standalone; piano dell'esploratore; spec dei flussi, sezione 4.

1. **[deciso]** L'interfaccia segue la pipeline («L'interfaccia segue la pipeline»): il percorso a otto step al posto delle quattro tappe e delle sei fasi; ogni step con ciò che ha trovato; il piano prima di partire, con i consensi; l'azione in corso detta per ciò che fa. L'elenco delle fasi e la ricostruzione dagli eventi che oggi stanno nella pagina (`viewer/app/run.ts`, `stages.ts`) vanno via: la pagina legge il piano.
2. **[deciso]** La tappa «Pre-mappa» si divide nei risultati dei suoi step: elenco dei file, stack, moduli. Le parole di come è fatto («pre-mappa», «scan», «analyzer») escono da ogni schermata.
3. Il server dà alla pagina il piano e ciò che ogni step ha trovato, nella stessa forma che dà a MCP.
4. La pagina dell'albero della pipeline (`docs/pipeline/`) ha oggi due viste, «Oggi nel codice» e «Piano»: a refactoring finito ne resta una.
5. Da implementare: il server applicativo, il coordinatore della coda, gli adattatori dei motori con la prova di capacità, l'annullamento e la ripresa (app standalone, «Stato»).
6. L'ingresso da GitHub con accesso: GitHub App, device flow, token nel portachiavi. Registrare l'App è un prerequisito.
7. **[proposta]** Il servizio sul PC: la cartella applicativa portabile, l'app che parla solo via HTTP con un token. **[da verificare]** La licenza di Kiri per la ridistribuzione; il portachiavi su Linux senza desktop.
8. La mappa nella pagina dell'app: oggi non la mostra. Il grafo dell'app non è mai stato misurato su un progetto grande (spec dei flussi, tabella di stato).
9. **[difetto]** La pagina dell'app non ha un comando per salvare un percorso e, riaperta, non mostra lo stato della scheda (spec degli ingressi, collaudo).
10. L'esploratore: i pannelli ridimensionabili e i filtri; la verifica da tastiera; la misura su un run reale, i cui obiettivi di prestazione non sono raggiunti sul sintetico. Il parametro `level` usa ancora i nomi vecchi.
11. **[deciso]** L'albero della pipeline (`docs/pipeline/`) resta scritto dal codice: una sorgente, un analizzatore o una regola nuova senza la sua voce fa fallire `pipeline_tree.py check`.

**Cancello:** un lavoro intero con un motore controllato passa (eventi, errore, timeout, annullamento, riavvio); la mappa è nella pagina dell'app; nessuna schermata nomina uno step o una fase che il piano non contiene, e il workflow Viewer passa con le sue prove nel browser.

## Ondata 11: le superfici differite

Da: «Le superfici e come si eseguono», sopra; `docs/roadmap.md`, fase 3. **[deciso]** il 25 novembre che queste superfici fanno parte del disegno; nulla è costruito. Ogni download pesante o con una licenza chiede il consenso dell'utente.

1. **Desktop Linux.** L'esecuzione sotto `Xvfb` o Wayland senza schermo con i registratori che esistono già (Python, JVM, .NET): basta a tracciare l'avvio e la costruzione delle finestre.
2. **Desktop Linux, il pilota.** Uno strumento che aziona i controlli attraverso AT-SPI o l'introspezione del toolkit; prima si valuta uno strumento pronto. Fino ad allora `ui_driver_not_implemented`.
3. **GUI Python** (Tkinter, PyQt, PySide, Kivy, Flet): il riconoscimento dal codice è deciso; l'osservazione dinamica entra qui, con un caso reale nel corpus per ogni toolkit.
4. **Android.** Prima il bersaglio `web` o desktop del progetto multipiattaforma. Per i moduli solo Android: `emulator` e una system image senza finestra scaricati con `sdkmanager` (già nella preparazione), dentro il container; serve `/dev/kvm`, altrimenti `kvm_unavailable`.
5. **Windows, gradino leggero.** Wine con `Xvfb` (circa 500 MB, senza KVM) per WinForms e WPF compatibili, con il registratore .NET.
6. **Windows, gradino completo.** Una VM Windows in un container per WinUI 3, UWP e ciò che Wine non regge; scarica la ISO di valutazione di Microsoft dopo il consenso. Senza `/dev/kvm` o senza consenso, `kvm_unavailable` o `approval_required`.
7. **[misura]** Su quali motori di container `/dev/kvm` è disponibile: Linux nativo, WSL 2 con la virtualizzazione annidata, le VM Sandbox di Modal.
8. macOS e iOS restano fuori perimetro.

**Cancello:** per ognuna delle tre superfici un progetto vero del corpus viene avviato e almeno un controllo azionato, con la funzione partita registrata; dove manca un requisito la lacuna dice quale.

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
14. Il comando dei test quando il progetto non lo dichiara: dall'utente, dalla CI, da un modello piccolo. Quali delle tre, e in che ordine (ondata 7).

## I documenti tolti

Tolti dal repository il 25 novembre 2026; si leggono al commit `614c940`. Accanto, le ondate in cui è finito ciò che di ognuno restava.

| Documento | Ondate |
| --- | --- |
| `specs/2026-11-15-pipeline-di-analisi.md`, `plans/2026-11-25-stack-prima-degli-strumenti-di-build.md` | La pipeline, 0, 2, 3, 4 |
| `specs/2026-11-24-libreria-del-linguaggio.md` | 1 |
| `specs/2026-11-21-stack-dal-fork.md` e i suoi tre piani | 0, 2 |
| `plans/2026-11-14-grafo-dall-indice.md`, `specs/2026-11-08-risoluzione-chiamate-motore.md` | 2, 5 |
| `plans/2026-11-20-analisi-unificata.md`, `plans/2026-11-20-pipeline-intera.md` | 3, 5, 6 |
| `specs/2026-11-12-passo-dinamico.md` e il suo piano | 6, 7 |
| `specs/2026-11-19-esecuzione-del-programma.md`, `specs/2026-11-19-interfacce-del-progetto.md` | 7 |
| `specs/2026-11-20-ingressi-e-scoperta-dei-flussi.md`, `plans/2026-11-20-ingressi-e-flussi.md` | 3, 7, 8 |
| `specs/2026-11-18-flussi-e-mappa-del-sistema.md`, `plans/2026-11-12-mappa-del-sistema.md` | 8, 10 |
| `specs/2026-11-20-ricerca-e-pacchetto-di-review.md` e il suo piano | 9 |
| Le spec della review del 3, 4, 7 e 9 novembre, `plans/2026-11-08-whole-source-coverage.md`, `specs/2026-11-19-revisori-per-framework-e-librerie.md` | 9 |
| `specs/2026-11-16-app-standalone.md`, `plans/2026-11-08-codebase-explorer.md` | 10 |

`docs/roadmap.md` resta: le sue tre fasi sono ora in «Le superfici e come si eseguono» e nelle ondate 7 e 11.
