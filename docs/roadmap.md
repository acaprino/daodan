# Roadmap di Daodan

> Ciò che di questo documento resta da fare è condensato in [Il lavoro che resta, in ondate](specs/2026-11-25-lavoro-residuo-a-ondate.md), ondata 7: lo stato di una voce si aggiorna là.

Aggiornata al 19 novembre 2026. Distingue ciò che è in uso nel repository, ciò che è specificato per le prossime iterazioni e ciò che è rimandato come lacuna dichiarata. Vale ovunque la regola invalicabile di [`AGENTS.md`](../AGENTS.md): nessun codice, build, test o interfaccia del progetto analizzato gira mai sull'host, nemmeno su un browser o emulatore installato sulla macchina dell'utente.

## Stato generale dei filoni

| Filone | Stato | Riferimento |
| --- | --- | --- |
| Mappa statica, moduli unificati (Step 1 `scan`) e stack per modulo (Step 2 `stack`) | In uso | [pipeline, sezioni 1 e 6](specs/2026-11-25-lavoro-residuo-a-ondate.md) |
| Indicizzatori per linguaggio nel container e passo dinamico sui test (`tests`) | In uso | [passo dinamico](specs/2026-11-25-lavoro-residuo-a-ondate.md), [supporto misurato](plugins/codebase-map-supporto.md) |
| Flussi, mappa del sistema e grafo dei moduli dai flussi | In uso / prova sui benchmark | [flussi e mappa, «Principi»](specs/2026-11-25-lavoro-residuo-a-ondate.md) |
| Registro dell'esecuzione: albero delle chiamate, frontiere, conto di sistema e corsa HTTP | Proposto | [esecuzione del programma](specs/2026-11-25-lavoro-residuo-a-ondate.md) |
| Riconoscimento statico delle interfacce, `builds` e `starts` risolti con `toolchains` | Proposto (priorità immediata) | [interfacce del progetto](specs/2026-11-25-lavoro-residuo-a-ondate.md) |
| Esecuzione dinamica delle interfacce `web` e `webview` (Electron, Tauri, Wails) | Proposto (subito dopo il riconoscimento) | [interfacce del progetto, sezione 7](specs/2026-11-25-lavoro-residuo-a-ondate.md) |
| Esecuzione dinamica di desktop Linux, Android e Windows nativo (emulatori/VM in container) | Rimandato (oggi lacuna dichiarata) | Sezione seguente |
| Mappa del sistema a fine di ogni analisi, con il giro del modello sui resti | Da collegare: il ruolo `system-mapper` esiste nel plugin, nessun passo lo avvia | [flussi e mappa, sezione 7](specs/2026-11-25-lavoro-residuo-a-ondate.md), [flussi e mappa, Principio 4](specs/2026-11-25-lavoro-residuo-a-ondate.md) |

## Sequenza per le interfacce e l'avvio dei programmi

### Fase 1 — Riconoscimento statico di interfacce, `builds` e `starts` (prossimo passo)

Zero esecuzione di codice del progetto; verificato sui 180 progetti di `benchmarks/project-model` su Modal:

1. **Catalogo delle superfici:** campo `surface` e `type: "schermata"` sulle voci `web` e `webview` che `service-registry.json` ha già. Le voci desktop, Windows e Android, con i loro segni fuori dai gestori di pacchetti, entrano ciascuna con un caso reale nel corpus: oggi il corpus non ne ha.
2. **Comandi `builds` e `starts` legati a `toolchains`:** estrazione in `premap.json` dei comandi di build e di avvio (`start` e `dev`, `angular.json`, `tauri.conf.*`, `wails.json`, `pyproject.toml`, binari Cargo/.NET, `Dockerfile` e `Compose`), scegliendo l'esecutore effettivo (`npm`/`pnpm`/`yarn`/`bun`, `uv`/`poetry`, wrapper JVM) dalle `toolchains` e dai lockfile del modulo e calcolando `needs_build` quando l'avvio punta ad artefatti compilati non presenti nello snapshot.
3. **Interfaccia come nodo:** una schermata nasce da un ingresso (pagina dichiarata, pagina di un meta-framework, pagina che il codice incorpora o offre su una rotta), non da un manifesto. Servono due collegamenti che oggi mancano: ciò che un documento HTML carica e ciò che il codice incorpora. Sopra ogni interfaccia sta il dispositivo dedotto; guscio e pagina sono due nodi collegati. Lacune dichiarate: `interface_uncertain`, `entry_not_found`, `no_start_command`, `build_command_missing`, `port_not_declared`, `ui_execution_deferred:<surface>`.

### Fase 2 — Esecuzione `web` e `webview` nel container

1. **Albero delle chiamate e frontiere sui test esistenti**, come primo passo della [spec del 19 novembre](specs/2026-11-25-lavoro-residuo-a-ondate.md).
2. **Corsa `web`:** avvio del modulo tramite `builds` + `starts` nel pod senza rete (`--network none`, servizi CI accanto) e navigazione delle pagine d'ingresso con **Playwright + Chromium headless** forniti da Daodan nel container, unendo gli scambi browser-server e le catene registrate.
3. **Corsa `webview` (Electron, Tauri, Wails):** avvio sotto `Xvfb` nel container Linux e collegamento dello stesso pilota browser alla webview dell'app (CDP per Electron, WebDriver per Tauri/Wails), osservando insieme vista web e processo nativo del guscio.

### Fase 3 — Piattaforme differite ed emulatori nel container (futuro, su consenso utente)

Finché questa fase non è implementata, i moduli con superficie `desktop`, `windows` o `android` (quando non dispongono anche di una superficie `web` eseguibile in Fase 2) sono riconosciuti nello stack ma riportano nel passo dinamico la lacuna `ui_execution_deferred:<surface>`. Quando verranno attivati, nessun emulatore o runtime dell'host verrà mai usato: tutto verrà scaricato nel magazzino di Daodan ed eseguito **dentro il container** dietro approvazione esplicita dell'utente per download, licenze e spazio disco.

1. **Desktop Linux (`surface: "desktop"` — PyQt, PySide, Tkinter, GTK, Kivy, Flet, Avalonia, Uno Platform, JavaFX):**
   - Esecuzione sotto `Xvfb` o compositor Wayland headless nel container Linux con i registratori di linguaggio esistenti (`python_record.py`, agente JVM, rewriter `.NET`), già sufficiente a tracciare l'avvio e la costruzione delle finestre.
   - Costruzione di un pilota leggero basato su AT-SPI / introspezione del toolkit per esercitare azioni utente sui controlli (fino ad allora lacuna `ui_driver_not_implemented`).
2. **Android (`surface: "android"` — Android SDK, React Native, Expo, Flutter/MAUI Android):**
   - Priorità ai target `web` o `desktop` Linux quando il modulo multipiattaforma (Flutter, Expo, Compose) li dichiara già, a costo zero emulatori.
   - Per i moduli solo-Android: su approvazione esplicita dell'utente (termini Android SDK + ~4 GB di download), riuso di `cmdline-tools` e `sdkmanager` già presenti in `daodan/core/preparation.py` per scaricare `emulator` e una system image headless (`-no-window -no-audio`) dentro il container/VM di Daodan. Richiede `/dev/kvm` esposto dal motore (Linux nativo, WSL 2 con nested virtualization attiva o VM Sandbox di Modal); dove `/dev/kvm` manca resta la lacuna dichiarata `kvm_unavailable`.
3. **Windows nativo (`surface: "windows"` — WinForms, WPF, WinUI 3, UWP):**
   - **Gradino leggero (`Wine + Xvfb`, ~500 MB, nessun KVM, su consenso utente):** per applicazioni `WinForms` e `WPF` compatibili sotto `.NET` + registratore Mono.Cecil di Daodan.
   - **Gradino completo per `WinUI 3` (`Windows App SDK`), `UWP` e `WPF` non retti da Wine (`dockur/windows`, MIT):** poiché nessun compatibility layer su Linux (`Wine 10`, `Proton`) implementa `DirectComposition`/DWM completi e `AppContainer` WinRT richiesti da `WinUI 3` e `UWP`, l'esecuzione userà una VM Windows 11 isolata in container Docker tramite QEMU/KVM (`dockur/windows`, puro codice MIT che non ridistribuisce Windows ma scarica automaticamente la ISO di valutazione ufficiale Microsoft dopo il consenso dell'utente). Richiede `/dev/kvm`, ~4 GB di RAM e una deroga esplicita dell'utente per ~25–32 GB di spazio disco; senza `/dev/kvm` o senza consenso resta lacuna dichiarata (`kvm_unavailable` / `approval_required`).
4. **Fuori perimetro attuale — macOS e iOS (`AppKit`, `SwiftUI`, `UIKit`):**
   - Ignorati sia nel riconoscimento delle superfici sia nell'esecuzione: non esiste un simulatore eseguibile in un container Linux e l'EULA Apple vincola l'esecuzione ad hardware Mac.
