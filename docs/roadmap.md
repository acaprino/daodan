# Roadmap di Daodan: indice dello stato

Stato verificato nel codice il 24 novembre 2026. Ogni riga dice che cosa c'è oggi e rimanda al documento che lo descrive; i numeri misurati stanno nei README dei benchmark.

Due regole di [`AGENTS.md`](../AGENTS.md) valgono per ogni riga: nessun codice del progetto analizzato gira mai sull'host, e «analisi» è l'intera pipeline, quindi un buco si dichiara e si misura dopo l'ultimo passo.

Stati: **In uso** (nel codice, con la sua prova), **In parte** (dice cosa c'è e cosa manca), **Proposta** (nulla nel codice), **Aperta** (una domanda senza decisione o senza misura), **Rimandata**.

## Analisi: dalla lettura al grafo

| Filone | Stato | Dove |
| --- | --- | --- |
| Pipeline, un passo dopo l'altro | **In parte.** `pipeline.STEPS` ha `scan`, `stack`, `parse`, `analyze`, `dynamic`, `union`. `plan` è una funzione (`pipeline/plan.py`), non uno step; `union` elenca ciò che manca e non unisce ancora i grafi di linguaggi indicizzati a parte | [`README`](../README.md), «How the graph is built»; [spec](specs/2026-11-15-pipeline-di-analisi.md); [riferimento](plugins/codebase-map.md#pipeline) |
| Pre-mappa e mappa dei moduli (`scan`) | **In uso** (`daodan/core/premap/`, una sorgente per strumento, i comandi di modello nel container) | [spec della pipeline](specs/2026-11-15-pipeline-di-analisi.md), sezione 1; [`benchmarks/project-model`](../benchmarks/project-model/README.md) |
| Stack per modulo (`stack`) | **In uso** sul registro (`service_registry.py`, `technologies.py`) | [spec della pipeline](specs/2026-11-15-pipeline-di-analisi.md), sezione 1 |
| Stack dal fork di stack-analyser | **In parte.** Il rilascio `1.27.6-daodan.2` è fissato in `stack_analyser.py` e misurato sul corpus; il passo `stack` non lo usa ancora | [spec](specs/2026-11-21-stack-dal-fork.md); [piano del passaggio](plans/2026-11-22-stack-dal-fork-3-passaggio.md) |
| Indicizzatori per linguaggio (`analyze`) | **In uso:** Go, Rust, TypeScript e JavaScript con Vue e Svelte, Python, Java, Kotlin, C e C++, C#, fogli di stile (`daodan/core/indexers/`). Aperti: richieste mirate e resti del passo per posizione, secondo configure di CMake | [linguaggi](plugins/codebase-map-linguaggi.md), [supporto misurato](plugins/codebase-map-supporto.md); [spec](specs/2026-11-08-risoluzione-chiamate-motore.md); [piano](plans/2026-11-14-grafo-dall-indice.md); [`benchmarks/inference-audit`](../benchmarks/inference-audit/README.md) |
| Passo dinamico sui test (`dynamic`) | **In uso** per Python, JavaScript e TypeScript, Go, Java e Kotlin, Rust, C e C++, C# (`daodan/core/dynamic/`). È il passo che chiude le chiamate che l'indice lascia aperte | [spec](specs/2026-11-12-passo-dinamico.md); misura in [`benchmarks/call-provenance`](../benchmarks/call-provenance/README.md) |
| Esplorazione dell'app avviata (`dynamic`) | **In parte.** L'app parte nel container e un browser ne preme i controlli (`dynamic/app.py`, `explore.cjs`), solo con `npm` e per le pagine web. Mancano pnpm, Yarn e Bun, le altre fonti di avvio, le credenziali di prova | [piano degli ingressi](plans/2026-11-20-ingressi-e-flussi.md), task 11; [spec delle interfacce](specs/2026-11-19-interfacce-del-progetto.md), sezione 7; [`benchmarks/project-model`](../benchmarks/project-model/README.md) |
| Aggiornamento incrementale | **Aperta.** Dopo una modifica a un modulo riparte quasi tutto; le regole di riuso per file non sono nel codice | [piano](plans/2026-11-14-grafo-dall-indice.md), «Aggiornamento incrementale»; [`benchmarks/project-model`](../benchmarks/project-model/README.md), «Tre corse sullo stesso progetto» |
| Una preparazione per analisi, un job per tutta la catena | **In parte.** Nel codice (`node_preparation.py`, `modal_map.py whole`); il guadagno su Modal non è misurato | [piano](plans/2026-11-20-analisi-unificata.md) |
| Registro dell'esecuzione: albero delle chiamate, frontiere, corsa HTTP | **Proposta** | [spec](specs/2026-11-19-esecuzione-del-programma.md) |

## Dopo la pipeline: ingressi, flussi, mappa del sistema

| Filone | Stato | Dove |
| --- | --- | --- |
| Ingressi dai framework e dagli endpoint | **In parte.** Sorgenti nel container per Next.js, React Router e Remix, SvelteKit, Nuxt, Astro, Angular; Noir per le rotte, legate alle funzioni dello snapshot (`binder.py`). Le sorgenti che caricano il framework all'avvio sono misurate e non collegate | [spec](specs/2026-11-20-ingressi-e-scoperta-dei-flussi.md); [piano](plans/2026-11-20-ingressi-e-flussi.md); [`benchmarks/noir-binding`](../benchmarks/noir-binding/README.md) |
| Collegamenti, flussi e mappa del sistema | **In uso** (`flows.py`, `flow_paths.py`, `system_map.py`, `system_levels.py`); la mappa parte a fine analisi, nell'app (`App._follow`) e nel plugin (`system-mapper`). Il mappatore con un modello debole non ricostruisce il sistema alla cieca | [spec](specs/2026-11-18-flussi-e-mappa-del-sistema.md); [`benchmarks/system-map`](../benchmarks/system-map/README.md) |
| Anagrafica dei flussi, ricerca, pacchetto di una review | **Proposta** | [spec](specs/2026-11-20-ricerca-e-pacchetto-di-review.md); [piano](plans/2026-11-20-ricerca-e-pacchetto-di-review.md) |
| Interfacce: riconoscimento statico | **In parte.** `starts` e `builds` da `package.json` (`premap/npm_start.py`); comandi ed eventi fra pagina e guscio Tauri come legami. Mancano il catalogo delle superfici e l'interfaccia come nodo | [spec](specs/2026-11-19-interfacce-del-progetto.md) |
| Esecuzione di `webview` (Electron, Tauri, Wails) | **Proposta** | [spec delle interfacce](specs/2026-11-19-interfacce-del-progetto.md), sezione 7 |
| Desktop Linux, Android, Windows nativo | **Rimandata:** riconosciute, non eseguite | sezione sotto |

L'ordine dei task di questi filoni e la prova da zero sui cinque casi: [piano della pipeline intera](plans/2026-11-20-pipeline-intera.md).

## Review

| Filone | Stato | Dove |
| --- | --- | --- |
| Review `branch`: perimetro, selezione, rigor, copertura dell'intero sorgente | **In uso** (Parte A della copertura). Il riuso dei controlli fra review è una **Proposta** | [spec](specs/2026-11-03-semantic-review-foundation.md); [piano](plans/2026-11-08-whole-source-coverage.md); [`benchmarks/whole-source-coverage`](../benchmarks/whole-source-coverage/README.md) |
| Run di lavoro e regole di review | **In uso** | [spec](specs/2026-11-09-working-run-and-review-fixes.md) |
| Unità e flussi dentro la review | **Aperta:** un caso misurato su tre, senza guadagno | [spec](specs/2026-11-09-flows-in-review.md); [`benchmarks/phazly-flow`](../benchmarks/phazly-flow/README.md) |
| Revisori per framework e librerie | **Proposta:** il pilota non promuove nessuna voce | [spec](specs/2026-11-19-revisori-per-framework-e-librerie.md); [`benchmarks/stack-reviewers`](../benchmarks/stack-reviewers/README.md) |
| Review dinamiche: riprodurre un finding nel container | **Proposta;** oggi i ruoli chiedono il container e senza è una lacuna | [spec dell'esecuzione](specs/2026-11-19-esecuzione-del-programma.md) |

## Interfaccia

| Filone | Stato | Dove |
| --- | --- | --- |
| Esploratore visuale | **In uso** (`visual.py`, `viewer/`), sui componenti di Imago; il passaggio a Sigrid è in corso. Prestazioni non misurate sul viewer di oggi | [ADR](adr/2026-11-07-codebase-explorer.md), [FRD](frd/2026-11-07-codebase-explorer.md) |
| App standalone (`daodan app`) | **In uso** (`app.py`, motori `openai`, `claude`, `codex` in `engines.py`) | [spec](specs/2026-11-16-app-standalone.md) |
| La mappa del sistema nel grafo dell'app | **Proposta** | [piano della pipeline intera](plans/2026-11-20-pipeline-intera.md), task 12 |

Difetti trovati e corretti, con la loro prova: [registro](verification/2026-11-16-registro-difetti.md).

## Piattaforme rimandate

I moduli con superficie `desktop`, `windows` o `android`, quando non hanno anche una superficie `web`, sono riconosciuti e non eseguiti: lacuna `ui_execution_deferred:<surface>`. Quando si faranno, nessun emulatore o runtime dell'host: tutto si scarica nel magazzino di Daodan e gira nel container, dopo l'approvazione dell'utente per download, licenze e spazio su disco.

1. **Desktop Linux** (PyQt, PySide, Tkinter, GTK, Kivy, Flet, Avalonia, Uno Platform, JavaFX).
   - `Xvfb` o un compositor Wayland senza schermo nel container, con i registratori di linguaggio che ci sono: basta a tracciare avvio e costruzione delle finestre.
   - Per premere i controlli serve un pilota su AT-SPI o sull'introspezione del toolkit: fino ad allora lacuna `ui_driver_not_implemented`.
2. **Android** (Android SDK, React Native, Expo, Flutter e MAUI per Android).
   - Prima i target `web` o desktop Linux, quando il modulo multipiattaforma li dichiara: nessun emulatore.
   - Per i moduli solo Android: `emulator` e un'immagine di sistema senza finestra, scaricati con `cmdline-tools` e `sdkmanager` (termini dell'Android SDK, circa 4 GB). Chiede `/dev/kvm`; dove manca, lacuna `kvm_unavailable`.
3. **Windows nativo** (WinForms, WPF, WinUI 3, UWP).
   - Gradino leggero: Wine con `Xvfb` (circa 500 MB, senza KVM) per WinForms e WPF compatibili.
   - Gradino completo per WinUI 3, UWP e WPF che Wine non regge: una VM Windows 11 in un container con QEMU e KVM (`dockur/windows`, MIT, che scarica la ISO di valutazione di Microsoft). Chiede `/dev/kvm`, circa 4 GB di RAM e 25–32 GB di disco; senza, lacune `kvm_unavailable` o `approval_required`.
4. **macOS e iOS** (AppKit, SwiftUI, UIKit): fuori perimetro. Nessun simulatore gira in un container Linux e la licenza di Apple lega l'esecuzione a hardware Mac.
