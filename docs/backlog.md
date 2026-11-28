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
- Importazione del vecchio esempio Bank of Anthos (ZIP con `project.json` e `v2/graph.sqlite`, cinque tabelle, un altro identificativo SQLite) nel `.daodan` (uscita da `T2.E.1`): conserverebbe l'originale e recupererebbe dal manifest revisioni e provenienza, con «unknown» e una lacuna per ciò che non si recupera; cambiare estensione o solo `user_version` non converte il contenuto. Nessuno scrive oggi quel formato.
- Renovate come terzo lettore pacchetti (ex ondata 2, voce 10); corsa settimanale confronto Linguist (ex ondata 1, voce 5).

### 5b. Ingressi dai manifesti di rilascio (deciso dal proprietario il 28 novembre 2026)

- Deployment, StatefulSet e Job di Kubernetes, profili di Skaffold, trigger di Cloud Build in Terraform (5 dei 7 flussi persi su Bank of Anthos, `benchmarks/system-map/README.md`, «Da dove verrebbero gli ingressi persi»). Strumenti ufficiali: `kustomize build`, `skaffold render`/`diagnose`, il lettore HCL di HashiCorp. Si riprende solo se una misura sul corpus mostra che contano su più progetti.
- Orari e thread scritti nel codice: nessuna tabella nostra; restano al modello come candidati `residuo` (provenienza «modello»), con i fatti del compilatore sul candidato quando la build gira.

### 5c. Lacune dei framework sotto la soglia (misurate in `T1.C.14`, 28 novembre 2026)

*Usate da meno di 3 progetti del corpus (`benchmarks/project-model/README.md`, «Le lacune dei framework sul corpus», Modal `ap-qp05LDKvpZZjl0xxLrffh8`). I casi di API e di `pages/` sono contati sulle 122 fixture con i file: «non misurate» sono le clonate che dichiarano il framework. Si riprende quando una misura le porta a 3, prima di tutto clonando quelle fixture su Modal.*
- **Next.js senza `typegen`** (prima della 15.5): 2 (`js-nextjs`, `real-next-subscriptions`). Fonte ufficiale per quelle versioni: da valutare.
- **Next.js `pages/`**: 0; non misurate 6. Fonte da provare: ciò che `next typegen` scrive per `pages/` (non misurato).
- **React Router `createBrowserRouter`** e **`basename`**: 0 e 0; non misurate 7 (5 senza `@react-router/dev`, che hanno già la lacuna `model_partial` di `react_router`). Fonte: per `basename` il modulo `virtual:react-router/server-build`; per le rotte scritte nel codice nessun comando, l'esplorazione.
- **SvelteKit 1**: 0. **SvelteKit `actions`**: 0; non misurata 1 (`real-sveltekit-realworld`). Nessun file di `svelte-kit sync` nomina le azioni (`benchmarks/sveltekit-routes`): fonte da valutare.
- **Nuxt 2**: 0 (il corpus ha solo Nuxt 4).
- **Angular `@HostListener` e `host`**: 0; non misurate 3. Fonte: `getHostElement` del controllore dei template (`benchmarks/angular-compiler`).
- **Astro, `astro:routes:resolved`**: 1 (`real-stack-astro-paper`). Fonte: `sync()` dell'API con l'hook (`benchmarks/astro-compiler`).
- **Go senza framework (`net/http`)**: 0; non misurate 11 con l'id `golang`. Fonte: go/types o scip-go sull'ultimo argomento della registrazione.
- **Wrapper HTTP, client sotto soglia**: `httpx` 1 (`mix-edge-submodules`), `axios` 1 (`mix-php-laravel`): un progetto ciascuno, nessuna riga in `daodan/data/http-clients.json` (`T1.C.15` ha messo solo `requests`, 6). Fonte quando una misura li porta a 3: il simbolo che scip-python scrive per le funzioni di `httpx` e scip-typescript per `AxiosInstance` (`index.d.ts`), letto da un indice registrato come per `requests`.
- **Wrapper HTTP, parti aperte**: il wrapper di un wrapper (serve la prova del wrapper che chiama); i client di altri linguaggi; in Python l'URL passato per nome (`requests.request(method="POST", url=url)`: una lacuna, perché `flows._value` legge gli argomenti per posto; scip-python nomina già il parametro di ogni parola chiave, `request().(url)`), una funzione decorata (una lacuna: il decoratore decide che cosa passa la chiamata) e i metodi di `requests.Session` (non misurati).

### 5d. Collegamenti CSS sotto soglia (`T2.B.17`)

- bulma 7/11 e styled-components-website 12/15 (`benchmarks/inference-audit/README.md`, «Soglia ≥15/15 a mano»): `.button` che non raggiunge il suo CSS Module, `.fas` e `.algolia-content`, `#js-menu-toggle`, lo `<style>` dentro JSX, due variabili CSS di `GlobalStyles.tsx`. Casi di due progetti: si riprendono solo se una misura ne mostra di simili su più progetti, o li chiude l'osservazione nel browser.

### 6. Soluzioni provvisorie da sostituire con quella pulita
*Decisione del proprietario (27 novembre 2026): ogni ripiego accettato per andare avanti si sostituisce, appena possibile, con la soluzione pulita qui accanto.*
- **Lettori SQL e PL/SQL a regex** (`daodan/core/languages/sql.py`, `plsql.py`, deroga di `T1.A.6`): pulita = una grammatica tree-sitter PL/SQL completa (package body, trigger, type body), misurata con `benchmarks/sql-grammar`.
- **Isolamento della rete su Kiri** (Windows, `T0.C.8`): pulita = un motore che isoli il container dall'host in modo nativo (`com.docker.network.bridge.inhibit_ipv4` o equivalente) su tutte le piattaforme; finché Kiri non lo offre si usa il pod senza rete con il proxy su socket.
- **Regex rimaste su testo con grammatica** in `daodan/core/indexers/clang.py` (si tolgono in `T2.B.13`), `daodan/core/requirements.py` `EDITABLE` e `preparation.py` `VCS_URL` (si tolgono in `T3.A.8a`): pulita = albero tree-sitter o parser ufficiale.
- **Quarantene di `T0`** (`docs/verification/2026-11-25-baseline-t0.md`): Go `replace` e Composer `path` del fork (pulita = rilascio `.6` del fork, `T1.B.4`), test Playwright instabile (`T3.B`), smoke test Desktop con WebView2 vivo dopo l'uscita (Cancello `T1`).
- **Preparatori ancora root** (`T3.A`, decisione 2): passati a `65532` con `--cap-drop ALL` dopo la riga `preparer:` di `benchmarks/egress/modal_hardening.py` il seme Node, la pre-mappa, `indexers/go`, `indexers/rust`, `dynamic/go`, `dynamic/rust`, `dynamic/python` senza requisiti VCS. Restano root: `dynamic/python` con requisiti VCS e la pre-mappa con `git` (apt installa nell'immagine, `IMAGE_NEEDS`); `dynamic/app` con l'esplorazione e `dynamic/javascript` con Playwright (`playwright install --with-deps` usa apt, `keep_root`); i passi della CI (`steps_script`: un job di CI gira da root, `sudo`/apt); `docker_build` (`keep_root`: lo stadio scrive nelle cartelle dell'immagine); non ancora provati, da portare con una riga `preparer:` ciascuno: `indexers/typescript`, `indexers/css`, `indexers/python`, `indexers/jvm`, `indexers/csharp`, `indexers/clang`, `dynamic/dotnet`, `dynamic/clang`, `dynamic/javascript` e `dynamic/app` senza browser. Pulita = ogni preparatorio come `65532`, con apt fuori dalla preparazione (un'immagine con git e le librerie del browser).
- **File generati riconosciuti solo da `.gitattributes`** (`T1.B`, senza go-enry): pulita = un rilevatore ufficiale del codice generato utilizzabile senza compilare (oggi nessuno: binding `enry` senza wheel, gem Linguist con estensioni native).

---

- **Gruppi `(nome)` di SvelteKit nello schema (`T1.C.7`):** `svelte-kit sync` non scrive un manifesto con il percorso senza gruppi, quindi una rotta in un gruppo ha `schema` `None` e la riga di Noir `/cart` resta separata da `/(shop)/cart`. Pulito: il percorso dal materiale ufficiale di SvelteKit (`@sveltejs/kit`, risoluzione delle rotte), non una regola nostra.
- **Righe senza metodo (`T1.C.7`):** React Router, SvelteKit e Nitro `default` danno la lacuna «senza metodo» nei collegamenti, come Django; per `+server` di SvelteKit i metodi vengono dalle esportazioni (`methods` in `entry-queries.json`).

- **Campi Tauri nello snapshot (`T2.C.6`):** `flows.link_facts` legge ancora `tauri_event` e `tauri_command` dello snapshot; pulito: campi generici `event` e `command` scritti da `languages/semantic.py`.

- **Vista dei flussi (`T2.C.9`–`T2.C.11`):** `to_prove` prende archi interni e uscite dai passi di tutti i flussi (un'uscita che nessun flusso raggiunge non si controlla); condizione e profilo non hanno fonte su nessun passo (domanda «`T2.C`, profili e condizioni»); in `hide` una freccia che parte da un nodo nascosto senza un visibile prima si perde; i segni «Da creare» di `architettura.md` per questi tre passi vanno aggiornati.

- **Genere dei simboli C (`T2.B.20`):** scip-clang 0.4.1 scrive `SymbolInformation.kind` 0, quindi un tipo C è un valore dal descrittore di tipo `#` di SCIP più la lingua del file; pulito: il `kind` dell'indicizzatore quando scip-clang lo scrive. Un `typedef` C++ usato in un cast resta chiamabile.

- **CSS e markup «lessicali» nello snapshot (Cancello T1, 28 novembre 2026):** su Bank of Anthos i file CSS (8) e di markup (9) hanno lo stato `lexical` nello snapshot e il piano dà `read_code:css` e `read_code:markup` `failed` (`engine_pass.unparsed`: nessun file `ast` o `partial`), con il rimedio «install the snapshot's parser packages». Succede in ogni giro di `modal_pipeline.py` dal 16 novembre (`results/pipeline/2026-11-16-*.json`). Non è il download delle grammatiche: il lettore dei fogli di stile non usa tree-sitter (`languages/stylesheet.py`). Causa da trovare: o lo snapshot non dà `ast` a lingue che un lettore legge, o il piano tratta da fallimento uno stato voluto.

- **Percorso verticale in una colonna (`T1.E`):** provvisorio finché Sigrid non sistema lo `Steps` orizzontale stretto ([acaprino/sigrid#76](https://github.com/acaprino/sigrid/issues/76)); poi l'App torna alla riga orizzontale.

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
| Unità e flussi dentro la review | Su un caso privato nessun difetto in più, dieci run | Flussi nella review |
| Quattro revisori per framework e le undici voci del catalogo | Nessun valore in più sulla baseline | Revisori per framework |
| Il profiler V8 per JavaScript | 47,1%, sotto la soglia: sostituito dal registro esatto | Passo dinamico |
| `plan` come step | Resta una funzione | Pipeline, 8.4 |

---

## Storico documenti rimossi

Le 19 spec e i 13 piani precedenti sono stati rimossi dal repository il 25 novembre 2026 e restano consultabili nella storia di git al commit `614c940` (`git show 614c940:docs/specs/<nome>.md`). Anche la spec monolitica `docs/specs/2026-11-25-refactoring-completo.md` da cui derivano i tre file attuali resta nella storia di git.
