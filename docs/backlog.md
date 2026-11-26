# Daodan: backlog differito, approcci ritirati e storico

**Documento non normativo.** Nulla in questo file può essere citato come requisito da `docs/specs/architettura.md`, dall'orchestratore, dai contratti degli step o dalla UI. Ogni voce differita rientra nel piano attivo ([`docs/plans/refactoring.md`](plans/refactoring.md)) solo quando un caso concreto e misurato ne giustifica la riapertura.

---

## Differito (fuori dal perimetro attivo T0–T3)

### 1. Infrastruttura estesa e modello locale per comandi (parti delle ex ondate 6 e 7)
- **Kiri di Daodan su ogni sistema operativo** (fuori da Windows) e immagine unica glibc con strumenti scaricati al primo uso; verifica cgroup v1 e passi accanto ai servizi su Kiri; servizi dichiarati altrove (include GitLab, Compose da Makefile).
- **Modello piccolo locale per scegliere i comandi** (candidati: Gemma 3 / FunctionGemma, solo selezione di comandi già nei file, grado `proposto`): richiede prima il benchmark a 4 bracci sul corpus. Fase B, con una spec sua (proprietario, 26 novembre 2026).
- **Riproduzione finding e indagine nel container** (dopo fix `review-quality-gates`).
- **Anagrafica globale delle versioni degli strumenti esterni** (nome, versione, origine, sha256 al posto delle ~60 costanti negli adattatori).
- **Contratti aggiuntivi:** forma della risposta contro ciò che il client legge; contratti fra repository; coda di domande imposta dalla macchina, fusione varianti e flussi di interfaccia (ex ondata 8, voci 6, 9, 12).

### 2. Ricerca, embedding e review (ex ondata 9)
- Anagrafica dei flussi e legami `avvia`, `condivide`, `stesso dato` calcolati dalla mappa.
- Embedding su anagrafica e nodi (EmbeddingGemma 2 non misurato; scelta aperta su chi scarica i pesi).
- Pacchetto di review dalla ricerca: **onere della prova aperto** — la fase 3 ha già misurato che i flussi non aiutano la review; va esplicitata l'ipotesi nuova e misurata prima di adottarlo.
- **Copertura dell'intero sorgente — Parte B (riuso celle) e prova preparazione 3 richieste:** non implementate / non eseguite *(accertato nel codice: la Parte A è già implementata in `daodan/core/composition.py` e misurata in `benchmarks/whole-source-coverage/README.md`)*.
- **Run di lavoro e regole 1–4 della review:** già implementati nel codice *(accertato in T0 punto 4)*; restano in backlog solo le eventuali prove con modello delle regole 1 e 4.
- Phase 0 «dalla richiesta ai file» (scritta, mai eseguita in review completa), micro skill e baseline per stack (confronto a 4 bracci mai fatto).
- Revisori per framework: soppressione senza import per `react` e `tauri`, 3 segni al registro `[deciso]`.
- **[difetto]** `graph` (`ValueError`) e `edit_impact` (`missing_store`).

### 3. App standalone, UI completa ed esploratore (ex ondata 10)
- Server applicativo, coordinatore della coda, adattatori motori con prova di capacità, annullamento e ripresa.
- Accesso GitHub: GitHub App, device flow, token nel portachiavi.
- Servizio locale portabile HTTP con token; verifica licenza Kiri per ridistribuzione e portachiavi Linux headless.
- Salvataggio del percorso e stato della scheda; pannelli ridimensionabili e tastiera dell'esploratore. La mappa a livelli sullo schermo è nel piano (`T2.D`).
- Riduzione di `docs/pipeline/` da due viste («Oggi nel codice» e «Piano») a una sola.

### 4. Superfici differite (ex ondata 11)
*Decise come parte della visione il 25 novembre; finché non implementate emettono `ui_execution_deferred:<superficie>`.*
- **Desktop Linux** (PyQt, PySide, Tkinter, GTK, Kivy, Flet, Avalonia, Uno, JavaFX): esecuzione sotto `Xvfb`/Wayland headless con registratori esistenti + pilota su AT-SPI o introspezione toolkit (prima valutare strumenti pronti; fino ad allora `ui_driver_not_implemented`).
- **GUI Python** (Tkinter, PyQt, PySide, Kivy, Flet): osservazione dinamica con un caso reale per toolkit.
- **Android** (Android SDK, React Native, Expo, Flutter, MAUI): emulatore headless via `sdkmanager` (richiede `/dev/kvm` e consenso ~4 GB/licenza), `assembleDebug` -> `aapt2 dump badging` -> `adb install`/`am start` -> UI Automator (valutare Appium/Maestro) -> `am profile` (strumento per RN/Flutter da scegliere).
- **Windows:** gradino leggero Wine + `Xvfb` (~500 MB) per WinForms/WPF; gradino completo VM Windows QEMU/KVM (richiede `/dev/kvm`, 4 GB RAM, 25–32 GB disco, consenso ISO valutazione) per WinUI 3/UWP.
- **[misura]** Disponibilità `/dev/kvm` su Linux nativo, WSL 2 nested, Modal Sandbox.
- **macOS e iOS:** fuori perimetro (nessun simulatore in container Linux; vincolo licenza Apple).

### 5. Scelte aperte non bloccanti
- Chi prepara il modello degli embedding (ex scelta 10).
- Ordine sorgenti (lista scritta vs bisogno dichiarato), `pass` vs `run`, colonna `producer` (ex ondata 4, voce 9).
- Limite di tempo per stage e cursore in byte sul giornale (ex ondata 4, voci 5 e 6).
- Renovate come terzo lettore pacchetti (ex ondata 2, voce 10); corsa settimanale confronto Linguist (ex ondata 1, voce 5).

---

## Fermo o ritirato: non si rifà

| Che cosa | Perché | Dove (`614c940`) |
| --- | --- | --- |
| I file che la pre-mappa esclude non si leggono (E1) | Toglierebbe 1.496 file veri, verso cui vanno 96 import | Pipeline, 8.3 |
| Radici e alias degli import da `tsc` | Su 25 progetti veri 0 import guadagnati e 110 persi | Pipeline, 8.3 |
| Un lettore dei soli dati di Linguist | 95 header C++ letti come C, da 8 a 48 s su file costruiti male | Linguaggio |
| Sorgente di Spring | Sulle applicazioni vere Noir dà lo stesso | Piano degli ingressi, 14a–14f |
| Sorgenti di Django, FastAPI e Flask (scritte, non collegate) | Sulle applicazioni vere Django non aggiunge funzioni a Noir, FastAPI non le carica, Flask costa più di quanto dà; tornano in discussione con un'applicazione dove Noir non lega e la sorgente sì | `benchmarks/{django,fastapi,flask}-routes/README.md` |
| Sorgenti di Laravel e Rails | Daodan non legge PHP né Ruby | Piano degli ingressi, 14d e 14e |
| `framework.cjs`, lettore di framework scritto a mano | Contro la regola d'oro | Decisione 20 novembre |
| Unità e flussi dentro la review | Su phazly nessun difetto in più, dieci run | Flussi nella review |
| Quattro revisori per framework e le undici voci del catalogo | Nessun valore in più sulla baseline | Revisori per framework |
| Il profiler V8 per JavaScript | 47,1%, sotto la soglia: sostituito dal registro esatto | Passo dinamico |
| `plan` come step | Resta una funzione | Pipeline, 8.4 |

---

## Storico documenti rimossi

Le 19 spec e i 13 piani precedenti sono stati rimossi dal repository il 25 novembre 2026 e restano consultabili nella storia di git al commit `614c940` (`git show 614c940:docs/specs/<nome>.md`). Anche la spec monolitica `docs/specs/2026-11-25-refactoring-completo.md` da cui derivano i tre file attuali resta nella storia di git.
