# Piano: esploratore visuale della codebase

> **Per chi esegue:** usare superpowers:subagent-driven-development o superpowers:executing-plans, un task alla volta; segnare solo i passi verificati.

**Obiettivo:** Codebase Map esporta un run in un file `daodan/visual@1` e un viewer locale lo rende navigabile nelle viste Logica e Fisica, con ispettore, filtri ed evidenze, senza flussi.

**Architettura:** `visual.py` (Python, solo libreria standard) legge snapshot, grafo dei moduli e schede di un run tramite le API esistenti e scrive un export immutabile in `.daodan/map/views/<run-id>/<export-digest>/`. Lo stesso script lo serve su `127.0.0.1` insieme agli asset precompilati del viewer. Il viewer (React + TypeScript, React Flow, ELK in Web Worker) proietta l'export e non rianalizza nulla.

**Tecnologie:** Python ≥ 3.12 stdlib, `unittest` eseguito con pytest; React 19, @xyflow/react, elkjs, Radix (via Button/Tabs adattati da Unlumen), Lucide, react-resizable-panels, Vite; test del viewer con `node --test` sui file `.ts` (type stripping di Node 24).

**Spec:** `docs/frd/2026-11-07-codebase-explorer.md` (requisiti) e `docs/adr/2026-11-07-codebase-explorer.md` (decisioni), approvati l'8 novembre 2026.

**Punto di partenza:** la preview in `.jcode/local/mockups/codebase-explorer/` (ignorata da Git) contiene un exporter e un viewer funzionanti su dati reali: `scripts/export_map.py`, `src/model.mjs`, `src/layout.mjs` (posizioni e percorsi ELK), `src/app.jsx`, `src/ui/`. Si riusano come base, non come contratto: il contratto è l'envelope di questo piano.

## Vincoli

- Flussi solo come li definisce la [fase 2](../specs/2026-11-09-flow-model.md): l'envelope li riceve in `flows` quando il run ha regole di collegamento; nessuna inferenza nell'esportatore o nel viewer.
- `visual.py` usa solo la libreria standard e le API di `snapshot_store`, `modules`, `source_reader`, `semantic_store`; non legge tabelle SQLite direttamente e non richiede il server MCP.
- Stati mai promossi: `provenance` (`build`, `declared`, `proposed`), `status` (`confirmed`, `inferred`, `incomplete`) e freschezza delle schede (`fresh`, `stale_body`, `stale_interface`, `stale_callee`, `orphan`, `uncovered`) restano campi distinti, con i valori dei produttori.
- Export legato al run e al digest dei suoi input, mai al mirror; scritto solo se valido, mai sovrascrivendo un export precedente.
- Server: solo `127.0.0.1`, porta libera, allowlist di file, nessun listing, controllo `Host`, nessun CORS, nessuna API che legga percorsi arbitrari o esegua comandi.
- Viewer: nessuna risorsa remota (CDN, font, worker); testo sempre come testo; React Flow in sola esplorazione (archi non creabili, eliminabili o riconnettibili).
- Layout: budget 5 s per tentativo, worker terminato a scadenza, risultati di generazioni superate scartati.
- Obiettivi da misurare, non promessi: fino a 300 nodi visibili layout + primo disegno ≤ 2 s; p95 selezione/evidenziazione ≤ 100 ms su 20 interazioni. 1.000 nodi è stress diagnostico.
- Node serve solo a sviluppo e build; gli asset compilati sono committati in `plugins/codebase-map/assets/viewer/`.
- Nessun bump di versione. Documenti in italiano al presente. Commit solo su richiesta dell'utente, formato `area: cosa`.
- Test Python: `python -B -m pytest -q <file>`. Test viewer: `npm test` in `plugins/codebase-map/viewer/`.

## Controlli essenziali

1. Run con snapshot non più leggibile (`parser fingerprint changed`): l'export si rifiuta con un messaggio che nomina la riparazione, senza lasciare directory parziali. Test in Task 3.
2. File condiviso da due moduli: due occorrenze nella vista, conteggio dei file unici non raddoppiato, entrambe le appartenenze nell'ispettore. Test in Task 5.
3. Nomi ostili (`<img src=x onerror=1>`) e indirizzi con credenziali (`https://u:p@host/x?token=1#f`): mostrati come testo; l'indirizzo esportato è `https://host/x`. Test in Task 2 e Task 6.
4. Due layout che terminano fuori ordine: compare solo quello della struttura corrente; selezione e viewport non tornano indietro. Test in Task 6.
5. Richieste al server con `/../`, `%2e%2e`, link simbolici o `Host` diverso da `127.0.0.1:<porta>`: rifiutate, nessun listing. Test in Task 4.

---

### Task 1: prova del renderer (gate dell'ADR)

L'ADR chiede di confrontare React Flow + ELK e LikeC4 Model Builder sulla stessa piccola fixture prima di fissare il renderer.

**File:**
- Crea: `benchmarks/codebase-explorer/README.md`, `benchmarks/codebase-explorer/fixture/visual.json`, `benchmarks/codebase-explorer/likec4-probe/` (prova minima, non un prodotto)
- Modifica: `docs/adr/2026-11-07-codebase-explorer.md` (sezione 2, una riga con l'esito)

- [x] **Passo 1:** scrivere a mano `fixture/visual.json` nel formato del Task 2: due moduli logici, un file condiviso da entrambi, una gerarchia directory → file → simbolo, una scheda `stale_body`, un modulo `inferred`, una lacuna dichiarata, un esterno.
- [x] **Passo 2:** proiettarla in LikeC4 Model Builder (`likec4-probe/`) e in React Flow + ELK (base: la preview). Misurare per entrambe: membership multiple senza proprietario unico, stati distinti leggibili, gerarchia espandibile, focus e ripristino filtri, righe di adattamento scritte.
- [x] **Passo 3:** registrare nel README parametri, versioni, misure e verdetto. Se LikeC4 soddisfa gli stessi requisiti con adattamento più semplice, **fermarsi**: i Task 5–7 vanno ripianificati. Altrimenti annotare nell'ADR «Renderer confermato: React Flow + ELK» con il rimando al README.

### Task 2: envelope `daodan/visual@1`

**File:**
- Crea: `plugins/codebase-map/skills/map/scripts/visual.py`
- Test: `tests/test_codebase_map_visual.py`

**Interfacce:**
- Produce: `build_envelope(run_dir: Path) -> dict`; `sanitize_address(text: str) -> str`; costante `SCHEMA = "daodan/visual@1"`.

Forma dell'envelope (i Task 3, 5 e 6 dipendono da questi nomi):

| Campo | Contenuto |
|---|---|
| `schema`, `meta` | `meta`: `project_root`, `run_id`, `target`, `git`, `snapshot_digest` (logical digest), `modules_digest` (`inputs_digest` di `modules.json`), `cards_digest` (o `null`), `created_at` |
| `entities` | lista di `{ref, type, name, technical, description, provenance?, status?, freshness?, path?, lines?, address?, evidence[], gaps[]}`; `ref` = `"<type>:<id originale>"`; `type` ∈ `component`, `feature`, `external`, `build`, `directory`, `file`, `symbol`, `store`; `location` (`internal`, `external`) e `node_type` dall'elenco chiuso della fase 2, quando noto |
| `relations` | `{ref, kind, source, target, status, counts?, evidence[]}`; `kind` ∈ `declares`, `contains`, `imports`, `calls`, `uses`, `defines`; `ref` derivato da `kind:source->target` |
| `memberships` | `{member, group, view}` con `view` ∈ `logical`, `physical`; un file può comparire in più gruppi |
| `gaps` | `{refs[], reason}`: lacune del grafo dei moduli, conflitti `shared_member`, simboli troncati, esterni senza evidenza risolta |
| `flows` | `{ref, entry, entry_kind, complete, nodes[], steps[]}` per ogni punto d'ingresso, dai collegamenti di `flows.py`; `steps`: `{source, target, type, origin, site, route?}`; vuoto senza regole di collegamento |

- [x] **Passo 1:** test con un progetto temporaneo (stile `tests/test_codebase_map_mcp.py`: `src/a.py` importa `src/b.py`, un `pyproject.toml`, un `codebase-modules.json` con due componenti che condividono `src/b.py` e una feature). Creare il run con `MapService(project).create_run("src", "r1", engine=False)`. Asserzioni: `build_envelope(run)["schema"] == "daodan/visual@1"`; esiste `relations` con `kind == "imports"` tra `file:src/a.py` e `file:src/b.py`; `memberships` contiene `file:src/b.py` due volte con `view == "logical"`; nessuna entità ha `type == "feature"` come gruppo fisico; ogni `relation.source/target` è un `ref` di `entities`; senza regole di collegamento `flows` è vuoto.
- [x] **Passo 2:** test `sanitize_address`: `"https://u:p@host:8443/x?token=1#f"` → `"https://host:8443/x"`; `"not a url"` → invariato; stringa con `password=` → `""`.
- [x] **Passo 3:** eseguire i test e verificarne il fallimento.
- [x] **Passo 4:** implementare. Fonti: `snapshot_store.resolve_run_snapshot` + `open_snapshot`; `modules.ensure_graph(manifest)` poi `load_graph`; `source_reader.outline_manifest` per i simboli (limite 1000 per file, troncamento → `gaps`); `source_reader.graph_packet(manifest, paths, 1, 1000)` a blocchi di percorsi per gli import tra file (il limite di 1000 per lista va rispettato: suddividere, mai troncare in silenzio). Directory derivate dai percorsi dell'inventario; `defines` collega file → simbolo, `contains` directory → file e build unit → directory.
- [x] **Passo 5:** test verdi; `python -B -m pytest -q tests/test_codebase_map_visual.py`.

### Task 3: schede, freschezza ed export immutabile

**File:**
- Modifica: `plugins/codebase-map/skills/map/scripts/visual.py`
- Test: `tests/test_codebase_map_visual.py`

**Interfacce:**
- Consuma: `build_envelope`.
- Produce: `export(run_dir: Path, store_root: Path) -> Path` (restituisce la directory pubblicata); CLI `visual.py export RUN_DIR` che stampa il percorso; file pubblicato `visual.json`.

- [x] **Passo 1:** test schede: con una scheda scritta via `snapshot.py meta-upsert` su `src/a.py::f` e poi modificato il corpo di `f` in un nuovo run, l'entità `symbol:src/a.py::f` ha `freshness == "stale_body"` e la sua `description`; un simbolo senza scheda ha `freshness == "uncovered"`.
- [x] **Passo 2:** test export: `export()` scrive `.daodan/map/views/r1/<digest>/visual.json`; una seconda chiamata con input invariati restituisce lo stesso percorso senza riscriverlo; cambiare una scheda produce un digest diverso e lascia intatta la directory precedente.
- [x] **Passo 3:** test di rifiuto (Controllo 1): con `metadata.parser_fingerprint` alterato nel manifest, `export()` solleva `ValueError` il cui testo contiene `refresh` e nessuna directory nuova esiste sotto `views/r1/`. Un envelope con un `relation.target` sconosciuto (iniettato con `mock.patch` su `build_envelope`) viene rifiutato prima della pubblicazione.
- [x] **Passo 4:** test digest concorrente: se `cards.sqlite` cambia tra lettura e pubblicazione (mock del secondo digest), l'export fallisce senza pubblicare.
- [x] **Passo 5:** implementare: schede da `semantic_store.query_meta_code(store, cards_path=…, limit=…)` a pagine fino a esaurimento; digest = SHA-256 del JSON canonico dell'envelope; scrittura in directory temporanea accanto alla destinazione, validazione dei riferimenti, `os.replace` sulla directory finale; confinamento con `confinement.reject_link_chain`.
- [x] **Passo 6:** test verdi; poi eseguire `python plugins/codebase-map/skills/map/scripts/visual.py export .daodan/map/runs/<run reale>` e verificare che il file sia valido e privo di sorgente completo. Verificato il 12 novembre 2026 su un run fresco della fixture dei flussi; il run `working` di questo repository si rifiuta finché non viene rinfrescato (parser cambiato).

### Task 4: server locale in sola lettura

**File:**
- Modifica: `plugins/codebase-map/skills/map/scripts/visual.py`
- Test: `tests/test_codebase_map_visual_server.py`

**Interfacce:**
- Consuma: directory prodotta da `export`.
- Produce: `make_server(export_dir: Path, assets_dir: Path, port: int = 0) -> http.server.ThreadingHTTPServer`; CLI `visual.py serve EXPORT_DIR` che stampa `http://127.0.0.1:<porta>/`. Rotte: `/` e gli asset elencati in `assets_dir` (allowlist calcolata all'avvio), `/data/visual.json`.

- [x] **Passo 1:** test con server in thread e `http.client`: `GET /` → 200 `text/html`; `GET /data/visual.json` → 200 e corpo uguale al file; `GET /assets/` → 404 senza listing; `GET /../visual.py`, `/%2e%2e/visual.py`, `/data/../../state.json` → 404; `Host: evil.example` → 421; risposta senza `Access-Control-Allow-Origin`; header `Content-Security-Policy` con `default-src 'self'`; un link simbolico in `assets_dir` non entra nell'allowlist. Il server ascolta su `127.0.0.1`.
- [x] **Passo 2:** verificarne il fallimento, implementare con `http.server` e `BaseHTTPRequestHandler` (nessun `SimpleHTTPRequestHandler`), test verdi.

### Task 5: modello del viewer

**File:**
- Crea: `plugins/codebase-map/viewer/package.json`, `vite.config.ts`, `tsconfig.json`, `src/envelope.ts`, `src/projection.ts`, `src/state.ts`, `test/projection.test.ts`, `test/state.test.ts`, `test/fixture.json` (copia della fixture del Task 1)

**Interfacce:**
- Consuma: envelope del Task 2.
- Produce: `parseEnvelope(json: unknown): Envelope` (lancia `EnvelopeError` con motivo); `project(env: Envelope, view: "logical" | "physical", scope: string | null, filters: Filters): Projection` con `nodes: {id, ref, type, label, collapsed, count}[]`, `edges: {id, source, target, relations: string[]}[]`, `counts: {filtered, aggregated, unloaded}`; `reduce(state: ExplorerState, action: Action): ExplorerState` con azioni `select`, `open`, `up`, `view`, `filter`, `resetFilters`, `toggleGroup`, `replaceEnvelope`.

- [x] **Passo 1:** test (con i nomi del Controllo 2): `shared file yields two occurrences and one unique count`; `collapsed group keeps the underlying relation refs`; `edges inside a collapsed group become a count, not external edges`; `filters hide but never delete the selection`; `empty projection exposes resetFilters`; `switching view keeps the selection only when its ref resolves`; `replaceEnvelope with an unknown schema leaves the previous envelope and reports the error`; `replaceEnvelope drops vanished refs from the selection and returns a warning`; `inferred and stale_body stay distinct fields`.
- [x] **Passo 2:** verificarne il fallimento (`npm test`), implementare, test verdi. ID d'occorrenza = `ref@container`; i conteggi deduplicano per `ref`.

Fatto il 12 novembre 2026, con due aggiunte della fase 2: `flowFocus` (i passi di un flusso sollevati ai nodi visibili) e `flowsThrough` (i flussi che attraversano un nodo); i nodi proiettati portano `nodeType` e `location`. `project` riceve anche i gruppi aperti e la selezione. `vite.config.ts` e `tsconfig.json` arrivano con il Task 6.

### Task 6: interfaccia del viewer

**File:**
- Crea: `plugins/codebase-map/viewer/index.html`, `src/main.tsx`, `src/layout.worker.ts`, `src/layoutClient.ts`, `src/components/` (`Graph.tsx`, `ListView.tsx`, `Inspector.tsx`, `Filters.tsx`, `Breadcrumbs.tsx`), `src/ui/` (Button e Tabs da Unlumen con la loro licenza), `src/style.css`, `test/layoutClient.test.ts`

**Interfacce:**
- Consuma: `parseEnvelope`, `project`, `reduce`.
- Produce: `createLayoutClient(worker: WorkerLike, timeoutMs = 5000): { request(graph, direction): Promise<Layout> }`, che scarta i risultati superati e termina il worker a scadenza.

- [x] **Passo 1:** test `layoutClient` con un worker finto (Controllo 4): due richieste, la prima risolta dopo la seconda → la promessa della prima viene rifiutata come `superseded`; scadenza a 5000 ms → `terminate()` chiamato ed errore `timeout`.
- [ ] **Passo 2:** implementare il client, poi la UI: layout a pannelli ridimensionabili (navigatore con filtri, grafo, ispettore), vista elenco con le stesse entità per tastiera, breadcrumb, ispettore con ruolo, relazioni in/out, moduli, percorso e righe, scheda e freschezza, evidenze, copia del riferimento. Filtri per testo, modulo, tipo di entità, tipo di relazione e stato. «Apri altro export» carica un `visual.json` scelto dall'utente tramite `replaceEnvelope`. Preferenze UI (vista, filtri, gruppi aperti) in `localStorage` per `run_id`, letture e scritture in try/catch, mai dati del progetto. Archi lungo i percorsi ELK (come la preview). In caso di errore del layout: vista elenco e «Riprova».
- [ ] **Passo 3:** verifica nel browser con `visual.py serve` sull'export del Task 3, a 1440 e 390 px: selezione, ingresso in un modulo e ritorno, cambio Logica/Fisica con selezione conservata, file condiviso con due appartenenze, nome ostile mostrato come testo (Controllo 3), solo tastiera, `prefers-reduced-motion`, console senza errori, nessuna richiesta di rete esterna.

Stato al 12 novembre 2026: client del layout con i due test, worker ELK, grafo React Flow con icone per tipo di nodo e marca degli esterni, flussi evidenziati al livello della vista con i loro passi, collegamenti di dati tratteggiati a riposo, gruppo «Fuori dai componenti» nella vista logica, ricerca e filtro per tipo, ispettore con stato, freschezza, evidenze, lacune e flussi del nodo, ingresso in un gruppo e ritorno, «Apri altro export». Verificato nel browser a 1440 e 390 px su un export della fixture dei flussi. Restano del passo 2: pannelli ridimensionabili, filtri per modulo, relazione e stato, preferenze in `localStorage`; del passo 3: solo tastiera, nome ostile, `prefers-reduced-motion`.

### Task 7: build distribuita, benchmark e documentazione

**File:**
- Crea: `plugins/codebase-map/assets/viewer/` (output di `npm run build`, con `LICENSES.txt`), `benchmarks/codebase-explorer/scale.py` (genera fixture da 100, 300, 1.000 nodi visibili)
- Modifica: `benchmarks/codebase-explorer/README.md`, `plugins/codebase-map/skills/map/references/mcp.md` o una nuova sezione in `references/standalone.md` per i comandi `visual.py`, `docs/plugins/codebase-map.md` (coordinarsi: il file ha modifiche altrui in corso)

- [x] **Passo 1:** `npm run build` scrive in `assets/viewer/`; test Python che verifica che `make_server` trovi `index.html` e che nessun asset referenzi `http://` o `https://`.
- [ ] **Passo 2:** misurare con Playwright sulle fixture scalate e su un run reale: layout + primo disegno, p95 su 20 selezioni, memoria; registrare hardware, browser, versioni, nodi e archi visibili e totali, distinguendo sintetico e reale. Stato al 12 novembre 2026: misurato sulle fixture sintetiche, obiettivi non raggiunti (`benchmarks/codebase-explorer/README.md`); manca il run reale.
- [x] **Passo 3:** documentare `visual.py export` e `visual.py serve` nella reference scelta, una riga nel README del plugin.

## Fuori da questo piano

Flussi; vista fisica di processi, database e indirizzi oltre a quanto già dichiarato dalle evidenze; apertura nell'editor (richiede un'integrazione host); scelta dei modelli; promozione dei moduli proposti a dichiarati.
