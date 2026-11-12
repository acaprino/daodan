# Codebase Map: riferimento

Codebase Map legge un repository con analisi statica e ne serve all'agente inventario, simboli, relazioni, moduli e descrizioni semantiche, con riferimenti verificabili alle sorgenti. Non esegue il programma: la copertura a runtime è sempre nulla, salvo evidenza fornita dall'utente. Dei quattro passi di analisi (statico, inferenza, dinamico, semantico) il terzo, i test in un container, è una proposta: `docs/specs/2026-11-12-passo-dinamico.md`. Non seleziona reviewer e non emette verdetti di correttezza: quello è senior-review, che ne usa i tool. Versione del plugin `1.0.1` (`plugins/codebase-map/plugin.toml`); nessuna dipendenza da altri plugin.

Ogni affermazione di questo documento rimanda a un file del plugin. Il testo operativo che il modello esegue è `skills/map/SKILL.md` con i suoi `references/`; questo documento lo descrive e non lo sostituisce.

## Perimetro

Sotto il target, la mappa non analizza ciò che Git ignora, le directory il cui nome inizia con un punto e le directory di dipendenze e build (`__pycache__`, `build`, `dist`, `node_modules`, `target`, `vendor`, `venv`). La regola ha un solo proprietario, `scripts/tree_scope.py`, e la applica ogni script che percorre l'albero: snapshot, scansione del cascade, ricerca degli usi, scansione dei commenti e revisione della documentazione.

Il target è analizzato com'è dato: `.github/` come target è il modo di mappare la CI, e un dot file accanto al codice (`.eslintrc.json`) non è una directory e resta. Un target che il suo repository ignora è analizzato intero come radice propria, senza prendere commit o branch dal repository che lo ignora. L'esclusione è dichiarata: `snapshot.py scope <target>` la stampa, il blocco `scope` del manifest la conserva (`git_ignore` vale `applied` o `unavailable`) e il rapporto finale la ripete. Un file tracciato da Git non è mai ignorato.

Riferimenti: `references/run.md` sezione Perimeter; docstring di `tree_scope.py`.

## Run e snapshot

Ogni analisi è un run isolato in `.daodan/map/runs/<run-id>/`, registrato in `.daodan/map/runs.json` (`schema` 2: `active` e `latest_completed`). Il run-id è lo slug del target più `-YYYYMMDD-HHMMSS`, oppure `--run-name` normalizzato a `[a-z0-9-]`, con suffisso `-2`, `-3` in caso di collisione. Più run possono procedere insieme senza condividere file.

Il run contiene `state.json`, `snapshot/manifest.sqlite` (o `manifest.json` con `--format json`), `changes.json` e `changes.md` per gli aggiornamenti, `knowledge/` della Phase 0 e i file di fase `01-structure.md` fino a `07-final-report.md`; in modalità team anche `partitions/<nome>/` e `08-interconnect-map.md`. La radice `.daodan/map/` è lo specchio dell'ultimo run pubblicato: lo sostituisce intero solo `snapshot.py publish`, dopo che `snapshot.py check` riporta `complete` e `may_publish`. Run parziali, a fase singola, solo documentazione o fermati non pubblicano mai. Chi consuma un run preciso conserva la sua directory; lo specchio serve a chi vuole l'ultimo stato.

Lo snapshot registra ogni file con dimensione, mtime e hash del contenuto, ogni simbolo con intervallo di righe e hash del corpo. L'inventario ha tre insiemi: sorgenti nei linguaggi analizzati, configurazione e documentazione, presentazione senza simboli (markup, template e Sass indentato: `PRESENTATION_EXTENSIONS` in `snapshot.py`). Un foglio di stile con una riga oltre 10.000 caratteri resta a livello di file (`MAX_STYLESHEET_LINE`). I file vietati (`.env`, credenziali, chiavi: lista in `references/evidence.md`) non entrano nel manifest nemmeno come hash. SQLite è il formato predefinito; `snapshot.py resolve <run-dir>` restituisce percorso e formato dichiarati dallo stato. `snapshot.py write` costruisce accanto al manifest anche l'indice lessicale `retrieval.sqlite` e il grafo dei moduli `modules.json` (`--no-index`, `--no-modules` li saltano).

Un secondo run sullo stesso target confronta lo snapshot del genitore con il worktree (`snapshot.py diff --verify`, che calcola gli hash di ogni file) senza spendere token del modello: file e simboli cambiati, raggio di impatto a un salto di import, affermazioni delle fasi che citano simboli cambiati. L'ingresso classico porta avanti le affermazioni non toccate riga per riga (`snapshot.py carry`) e ri-deriva solo quelle marcate stale; un gate meccanico rifiuta la pubblicazione finché una marca resta. L'ingresso team aggiorna a grana di partizione: una partizione senza file toccati è copiata intera, una con un file toccato è rianalizzata per intero. Oltre il 40% di file toccati (`--threshold`) la raccomandazione è un run completo. `--update` esige un genitore utilizzabile e si ferma senza; `--no-update` salta il rilevamento.

Riferimenti: `references/run.md`, `references/snapshot.md`, `references/update.md`.

## Ingressi

Il plugin non ha comandi propri: un entry point dell'host carica `codebase-map:map` e sceglie fra due ingressi.

**Analyze** (`references/entry-analyze.md`). Il coordinatore risolve scope e flag, scrive lo snapshot iniziale, prepara il run (`snapshot.py prepare`) e dispaccia un solo `codebase-map:map-analyst` isolato, che esegue le fasi dichiarate e scrive gli artefatti. Il coordinatore non legge le sorgenti; verifica la consegna con `snapshot.py check` e pubblica. Controlli: `--critical` (priorità ad autenticazione, pagamenti e persistenza nelle fasi 3 e 4), `--format sqlite|json`, `--run-name`, `--update`, `--no-update`, `--comments` (audit dei commenti in fase 6), `--docs-only` (fasi 0 e 6), `--phase N` con N da 1 a 6 (fasi 0 e N; 0 e 7 rifiutate), `--stop-after N` e `--resume-from [N]` con `--run-name` esatto.

**Team** (`references/entry-team-analyze.md`), per monorepo, repository multilinguaggio e target oltre un contesto. Dopo la Phase 0 globale, rileva le partizioni: manifest di workspace (pnpm, npm, Lerna, Nx, Turbo, Cargo, uv), layout per convenzione (`apps/`, `packages/`, `services/`), divisione per layer (`backend`/`frontend`), divisione per linguaggio (almeno due linguaggi con almeno 20 file; i fogli di stile non formano mai una partizione), altrimenti una partizione `root`. Mostra l'anteprima dello scope con il conteggio reale di worker e procede se la scelta è già autorizzata. Onda 1: uno `partition-structure-worker` per partizione. Onda 2: `partition-behavior-worker` e `partition-quality-worker` per partizione, che leggono l'output dell'onda 1 di tutte le partizioni per citare i confini incrociati. Poi `partition-synthesizer` consolida in `01..07.md` e `semantic-interconnect-mapper` scrive `08-interconnect-map.md` sulla superficie fra partizioni. Controlli in più: `--depth=lite|full`, `--partition <path>` e `--partition-name`, `--skip-interconnect`, `--skip-synthesis`, `--yes`; `--phase` e `--docs-only` sono rifiutati.

**Fasi.** La Phase 0 legge le istruzioni del progetto (`CLAUDE.md`, `AGENTS.md`) e gli indici di documentazione e scrive `knowledge/navigation.md` e `knowledge/documentation-leads.md`: indizi `documented` o `unverified`, mai `verified`, perché non legge codice. Le fasi 1 a 7: struttura, interfacce, flussi, semantica, pattern e rischi, salute della documentazione, rapporto finale. I percorsi che danno accesso al prodotto (autenticazione, onboarding, consenso, primo avvio) sono percorsi critici obbligatori in fase 3 e una categoria `Usability-blocking` in fase 5; per il codice client la traccia include il cascade degli stili, con `cascade_scan.py` eseguito sull'intero target. La profondità `lite` esegue 0, 1, 2 e 5 e condensa 7; in team non dispaccia i worker di comportamento e il worker di qualità scrive solo `05-risks.md` (`SKILL.md`, sezione Depth). Ogni file di fase termina con il registro `## Source reading`: manifest, seed del grafo, file e intervalli letti, diagnostica dei parser, lacune. Il rapporto finale dichiara tre coperture distinte: file in inventario, file letti in profondità, file esercitati a runtime.

Il rapporto `07-final-report.md` è la vista per le persone: non esiste un renderer HTML.

## Ruoli

| Ruolo | Modello, strumenti | Chi lo dispaccia | Scrive |
|---|---|---|---|
| `map-analyst` | inherit; Read, Glob, Grep, Bash, Write | il coordinatore dell'ingresso analyze | gli artefatti del proprio run; in modalità `cards` le schede di un'area |
| `partition-structure-worker` | inherit; Read, Glob, Grep, Bash, Write | ingresso team, onda 1 | `partitions/<nome>/01-structure.md`, `02-interfaces.md` |
| `partition-behavior-worker` | inherit; Read, Glob, Grep, Bash, Write | ingresso team, onda 2 (non in lite) | `partitions/<nome>/03-flows.md`, `04-semantics.md` |
| `partition-quality-worker` | inherit; Read, Glob, Grep, Bash, Write | ingresso team, onda 2 | `partitions/<nome>/05-risks.md`, `06-documentation.md` (solo 05 in lite) |
| `partition-synthesizer` | inherit; Read, Glob, Grep, Write | ingresso team, dopo l'onda 2 | `01-structure.md` fino a `07-final-report.md` del run |
| `semantic-interconnect-mapper` | inherit; Read, Write, Glob, Grep, Bash | ingresso team dopo la sintesi, o un workflow di documentazione dell'host | `08-interconnect-map.md`, o il percorso che il prompt nomina |

Ogni ruolo dichiara una tabella `Method loads`: quali sezioni dei riferimenti legge e quando. I worker scrivono solo i file che possiedono e non toccano `state.json` né la radice `.daodan/map/`; l'analista non pubblica e non pone domande. Il mapper produce una mappa di contratti, invarianti, regole di dominio, assunzioni e punti di integrazione, ogni riga con `file:line` e uno stato (`verified`, `documented`, `unverified`, `disputed`), e si dichiara un indice di ipotesi fallibile. senior-review non lo dispaccia: la sua Phase 1 legge il run completo con i tool della mappa.

## Linguaggi e parser

Tredici linguaggi e 32 estensioni (`SUPPORTED_EXTENSIONS` in `scripts/languages/__init__.py`):

| Linguaggio | Estensioni | Estrazione |
|---|---|---|
| Python | `.py`, `.pyi` | `ast` della libreria standard |
| Java | `.java` | tree-sitter, altrimenti regex |
| JavaScript | `.js`, `.mjs`, `.cjs`, `.jsx` | tree-sitter, altrimenti regex |
| TypeScript | `.ts`, `.tsx`, `.mts`, `.cts` | tree-sitter, altrimenti regex; interfacce, enum, alias di tipo |
| SQL | `.sql`, `.ddl`, `.dml` | DDL e grafo di riferimento tabelle e viste; `sqlglot` opzionale |
| PL/SQL | `.pks`, `.pkb`, `.plsql`, `.pls`, `.pck`, `.prc`, `.fnc`, `.trg` | regex: package, body, cursori, eccezioni, `%TYPE` e `%ROWTYPE` |
| Rust | `.rs` | tree-sitter, altrimenti regex; `impl Trait for Type`, `#[tauri::command]` |
| Go | `.go` | tree-sitter, altrimenti regex; i metodi sono funzioni `Receiver.Method` |
| Kotlin | `.kt`, `.kts` | tree-sitter, altrimenti regex |
| C# | `.cs` | tree-sitter, altrimenti regex |
| Vue, Svelte | `.vue`, `.svelte` | blocco `<script>` estratto e passato agli adattatori JS/TS |
| CSS, SCSS, LESS | `.css`, `.scss`, `.less` | tokenizer della libreria standard; un simbolo per regola applicata; `@apply` di Tailwind espanso |

Un `.sql` con marcatori Oracle è PL/SQL. Python richiesto `>= 3.12`: gli script lo dichiarano nell'intestazione PEP 723 e si rifiutano sotto, perché la grammatica di `ast` è quella dell'interprete in esecuzione. `tree-sitter` e `tree-sitter-language-pack` (`scripts/requirements.txt`) sono opzionali: senza, Java, JavaScript, TypeScript, Rust e Go usano regex e il parser lo scrive nelle note. La risoluzione lessicale dei riferimenti (`resolution.py`, `semantic_index.py`) lega solo funzioni e classi con binding unico e import interni diretti; ricevitori dinamici, proprietà calcolate e import solo di tipo restano riferimenti non risolti con la ragione. Un elenco di chiamanti vuoto non prova che un simbolo sia inutilizzato.

## Script

In `skills/map/scripts/`, Python con sola libreria standard salvo gli opzionali detti. Punti d'ingresso (`SKILL.md`, sezione Resources):

- `snapshot.py`: `scope`, `write`, `index`, `search`, `resolve`, `diff`, `carry`, `prepare`, `check`, `publish`, `register`, `unregister`, `meta-query`, `meta-upsert`, `edit-impact`, `symbols-at`, `stale-callers`, `context`.
- `source_reader.py`: `outline` (metadati dei simboli), `graph` (chiamanti e chiamati dal manifest, 1-3 salti), `read` (blocchi di sorgente verificati per simbolo, intervallo o file intero).
- `modules.py`: `build`, `query`, `brief`, `propose`.
- `resolve_edges.py`: risoluzione delle chiamate con un motore (`--engine jedi`, predefinito, o `--engine scip`) in `engine-edges.sqlite`; la avviano `snapshot.py write` e `codebase_map_create_run`.
- `semantic_map.py`: vista `semantic-map.md` delle schede di un'area.
- `embedding_worker.py`: embedding locali opzionali, su richiesta esplicita.
- `analyze_file.py`, `ast_parser.py`, `classifier.py`, `usage_finder.py`: analisi di un file, estrazione grezza, criticità, usi di un simbolo.
- `cascade_scan.py`: regole di stile con portata globale che possono rompere una schermata (fase 5).
- `doc_review.py`, `rewrite_comments.py`, `comment_rewriter.py`: salute della documentazione e qualità dei commenti (fase 6); Codebase Map usa solo analisi e rapporto, mai la riscrittura.
- `confinement.py`, `tree_scope.py`: binding al progetto con rifiuto dei link e lock per progetto; perimetro.
- `mcp_server.py` su `mcp_service.py`: il server MCP.

Gli altri moduli sono librerie: `snapshot_store.py` e `semantic_store.py` (storage SQLite e binding semantici), `retrieval.py` (indice FTS5), `edge_view.py` (vista unita di riferimenti lessicali e archi del motore), `scope_planner.py`, `context_packet.py` e `map_slice.py` (contesto delimitato), `card_store.py` (schede), `dependency_graph.py` e `store_graph*.py` (grafo di import e metriche), `languages/` (adattatori per linguaggio).

## Server MCP

`uv run --no-config --no-project --script <plugin>/skills/map/scripts/mcp_server.py --project <radice>` (`.mcp.json`). I due flag impediscono che il progetto analizzato scelga interprete o indice dei pacchetti del proprio analizzatore. Il progetto è fissato all'avvio; ogni target è relativo, ogni run-id seleziona esattamente `.daodan/map/runs/<run-id>/`; percorsi esterni, traversal, symlink e junction sono rifiutati. `--store <percorso>` sposta l'intero store in una dot directory del progetto, marcata da `.daodan-map-store.json`. La mappa va costruita con lo stesso runtime che la serve: l'indice lessicale registra versione di SQLite e impronta dei parser, e una mappa scritta da un altro Python risulta `stale` (`codebase_map_index` ricostruisce l'indice).

Ventidue tool, tutti con risposta JSON (`references/mcp.md` ha i parametri completi):

| Gruppo | Tool |
|---|---|
| Run | `codebase_map_scope`, `codebase_map_create_run`, `codebase_map_runs`, `codebase_map_status`, `codebase_map_diff`, `codebase_map_artifact` |
| Navigazione | `codebase_map_search`, `codebase_map_index`, `codebase_map_outline`, `codebase_map_graph`, `codebase_map_read`, `codebase_map_modules`, `codebase_map_flows` |
| Impatto | `codebase_map_edit_impact`, `codebase_map_symbols_at`, `codebase_map_stale_callers`, `codebase_map_meta_query`, `codebase_map_context` |
| Ciclo di vita | `codebase_map_checkpoint`, `codebase_map_events`, `codebase_map_resume`, `codebase_map_stop`, `codebase_map_publish` |
| Esploratore | `codebase_map_ui` |

Limiti nel codice (`mcp_service.py`): una lettura oltre 4.000.000 caratteri è rifiutata e va divisa; un artefatto si ferma a 2.000.000 byte con `truncated: true`; il giornale `mcp-events.json` tiene al massimo 10.000 eventi. Il server non avvia modelli, non ha scheduler e non cancella analisi: l'host dispaccia i worker e, per fermare un run, ferma prima i propri worker e poi chiama `stop`. `MapService(project_root, store)` espone le stesse operazioni a un backend nativo senza SDK.

## Trovare il codice di una richiesta

Il ciclo misurato è in `references/locate.md`; la scelta del tool per domanda in `references/tools-guide.md`.

1. Estrarre dalla richiesta i nomi concreti: identificatori, file, testo di errore, frame di traceback, termini di dominio.
2. `codebase_map_search` per gruppo di nomi: simbolo esatto e frame di traceback prima, poi corrispondenze per sottotoken (`InvoiceTotal` trova `invoice_total`). Pesi BM25 0/10/5/3/1 su id, nome, percorso, firma e corpo (`retrieval.py`). La ricerca non rilegge l'albero: un indice mancante o stale è una voce `gaps` che nomina `codebase_map_index`, non un risultato vuoto.
3. `codebase_map_outline` sul file del risultato e `codebase_map_graph` a un salto per vicini, chiamanti e chiamati.
4. `codebase_map_read` sui simboli tenuti: verifica i byte contro lo snapshot e fallisce con «source changed; refresh the manifest» su un file modificato.
5. `codebase_map_edit_impact` sui simboli da cambiare; poi riprodurre con un test e correggere.

Budget: circa 6 ricerche e 10 letture per compito; una ricerca vuota si riformula una volta. Misura del 2026-10-27 su 23 compiti reali con test nascosti (`docs/research/context-building-benchmarks.md`): 21 risolti con ricerca lessicale, 19 con ricerca ibrida, 19 con pacchetto statico senza ricerca; per questo la ricerca lessicale è il percorso predefinito e gli embedding restano opzionali.

## Grafo, risoluzione e moduli

`source_reader.py graph` interroga i binding statici del manifest senza rianalizzare: gli archi risolti si espandono verso chiamanti e chiamati, le chiamate non risolte non guidano l'espansione. `dependency_graph.py` aggiunge cicli di import, importatori transitivi e PageRank (damping 0,85, tolleranza 1e-10, 100 iterazioni al massimo) come aiuto alla lettura, non come prova di propagazione a runtime. Il classificatore considera alta complessità un file oltre 300 righe e hub un file con almeno 8 importatori, critico con 15 (`classifier.py`).

Il risolutore lessicale (`resolution.py`) lega solo un binding unico e non inferisce tipi. Il resto lo risolve un motore: `resolve_edges.py` con Jedi per Python, o un indice SCIP. Il passaggio motore è uno store derivato dello snapshot come l'indice lessicale: `snapshot.py write` e `codebase_map_create_run` lo avviano in background (`--no-engine`, `engine=false` per saltarlo), `codebase_map_status` ne riporta lo stato (`running`, `fresh`, `sampled`, `stale`, `failed`, `unavailable`, `stopped`, `off`) e `codebase_map_index` lo riavvia se non è fresco. Il processo usa `uv` con Jedi e gli stessi pacchetti di parsing dello snapshot, così l'impronta del parser coincide; senza `uv` usa l'interprete corrente se ha Jedi; altrimenti lo stato è `unavailable` con l'istruzione di installazione. L'ambiente del progetto (`.venv`, `venv` o `VIRTUAL_ENV`) entra da solo nell'inferenza, insieme alle cartelle che il progetto mette su `sys.path` a runtime: un modulo importato per nome nudo che lo snapshot non colloca e che nell'inventario ha un solo file. Ogni arco nomina il proprio risolutore (`builtin-lexical` o `<engine>@<versione>`) e la confidenza (`confirmed`, `candidate`); `edge_view.py` unisce gli archi ai riferimenti lessicali tenendo questi ultimi come autorità e mostrando le divergenze in `conflicts`.

### Risolvibilità

Il rapporto delle chiamate si legge come **risolte su risolvibili**, in `edge_view.coverage.resolution` e nello stato del motore. Escono dal denominatore i builtin riconosciuti e le destinazioni provate esterne dal motore. Un nome assente dal progetto resta da risolvere: può essere un alias di una funzione interna. I nomi del progetto danno soltanto priorità alle richieste. Le risposte su variabili, parametri e proprietà vengono seguite con lo stesso motore; cicli, ambiguità, mancanza di prove o limiti di ricerca mantengono la chiamata non risolta. Il solo fatto che il valore provenga da una libreria non prova che la funzione chiamata sia esterna.

Le misure seguenti usano il criterio precedente e non sono confrontabili direttamente con il nuovo denominatore.

Misura su Daodan dell'8 novembre 2026, 27.187 chiamate, solo risolutore lessicale:

| Insieme | Chiamate | Esempio | Come si risolve |
|---|---|---|---|
| Builtin | 4.926 | `len`, `isinstance`, `sorted` | esterna |
| Metodi di `unittest.TestCase` | 3.113 | `self.assertEqual` | esterna |
| Moduli stdlib e terzi | 2.663 | `json.dumps`, `re.compile`, `Path` | esterna |
| Metodo senza omonimi nel progetto su un ricevitore di tipo ignoto | 3.529 | `fields.append`, `db.execute` | esterna |
| Callee dinamico | 2.154 | `handler()`, `callbacks[k]()` | non risolvibile staticamente |
| `self.metodo()` in una classe con base esterna | 1.612 | `self._parts` in un `ast.NodeVisitor` | motore |
| Import di uno script del progetto via `sys.path` | 594 | `snapshot.write_snapshot` nei test | motore |
| Metodo con omonimi nel progetto su un ricevitore di tipo ignoto | 2.528 | `store.get_file` | motore |
| Altro: binding ambigui, catene `self.a.b` | 2.141 | `res.get` | motore, in parte |
| Risolte dal risolutore lessicale | 3.927 | `helper()` importato | lessicale |

Con il criterio applicato, sullo snapshot di HEAD (27.586 chiamate): 3.968 risolte su 11.753 risolvibili con il solo risolutore lessicale (33,8%), 7.399 su 9.083 con Jedi e le cartelle di `sys.path` (81,5%). Il motore sposta anche 2.670 chiamate fra le esterne, perché le trova definite fuori dal progetto. Il passaggio dura circa 13 minuti in background.

Ogni linguaggio ha il suo motore, eseguito uno alla volta nello stesso passaggio e installato al primo uso nella cartella condivisa di Daodan, con le librerie del progetto lette dai file di build senza eseguirli. Linguaggi, motori, versioni, licenze e copertura misurata: `docs/plugins/codebase-map-linguaggi.md`.

Il passaggio chiede al motore solo ciò che può essere cambiato: una risposta si riusa finché non cambiano il suo file, i file che importa e il file in cui punta. Le risposte stanno in `engine-answers.sqlite`, accanto alle schede. Prima vengono i file modificati, poi quelli di rango più alto, e lo store esce subito con le risposte riusate e poi ogni 30 secondi. Su ky uno snapshot invariato richiede 2 secondi senza avviare il motore, la modifica di un test 8 secondi, quella di un file importato quasi ovunque 38 secondi contro i 50 del primo passaggio. Spec e misura: `docs/specs/2026-11-08-risoluzione-chiamate-motore.md`.

`modules.py` deriva il grafo dei moduli accanto al manifest (`daodan/module-graph/v1`). Tre provenienze: `build`, letta dai manifest di 27 ecosistemi e 32 manifest (npm, pnpm, Lerna, Deno, Nx, Python, Cargo, Go, Maven, Gradle, .NET, Composer, RubyGems, Bundler, pub, melos, Swift, Mix, CMake, Cabal, Stack, sbt, Terraform, Zig, Julia, dune, plugin Daodan), stato `confirmed`; `declared`, da `codebase-modules.json` alla radice (`daodan/declared-modules/v1`), con `kind` `component` o `feature`, `location` `internal` o `external`, membri `path::Symbol`, file o directory ed evidenza, verificati sullo snapshot; `proposed`, da un modello attraverso `modules.py propose` o `codebase_map_modules(proposals=...)` dopo il `brief`, verificati allo stesso modo e mai oltre `inferred`. Nessuna directory diventa modulo per il nome. La query (`daodan/module-query/v1`) risponde `resolved`, `needs_clarification`, `incomplete` o `unknown` e non promuove mai un candidato. Contratto completo in `references/modules.md`.

## Digest, schede e impatto

Ogni simbolo di uno snapshot SQLite ha tre digest (`semantic_store.py`): `body_hash` sul testo dell'intervallo, `interface_hash` su genere, nome, esportazione, parametri e firme (prefisso `v2:`), `effects_hash` sulle chiamate e i riferimenti esterni risolti dentro l'intervallo, nominati per file e nome qualificato e non per posizione. Fra due refresh, `meta_changesets` registra i delta (`added`, `removed`, `body_only`, `effects_changed`, `interface_changed`) in un buffer di 16 changeset e 4 MB.

Una scheda è la lettura di un simbolo da parte di un modello: `purpose`, `preconditions`, `postconditions`, `invariants`, `side_effects`, `failure_modes`, `notes`, `confidence`. Le schede sopravvivono ai run e vivono in `.daodan/map/cards.sqlite`, con i digest del simbolo al momento della scrittura; la freschezza si calcola a ogni lettura: `fresh`, `stale_body`, `stale_interface`, `stale_callee`, `orphan`, e `uncovered` per un simbolo senza scheda. `snapshot.py meta-upsert` le scrive, `meta-query` e `codebase_map_meta_query` le leggono; il server MCP non scrive mai schede. Le scrive l'approfondimento di un'area (`references/deepen.md`): il coordinatore elenca i simboli senza scheda fresca con `semantic_map.py` e dispaccia `map-analyst` in modalità `cards`, a lotti di al massimo 100 simboli.

`snapshot.py edit-impact --target <simbolo o file>` e `codebase_map_edit_impact` (`daodan/edit-impact/v2`) rispondono a cosa sapere prima di modificare: digest, firme e scheda del target, chiamanti e chiamati a un salto con i siti di riferimento esatti, riferimenti non risolti, cambiamenti recenti, sorgente verificata. Livelli di `disclosure`: L0 sorgente del target, L1 vicini a un salto, L2 con `--hops 2`, L3 con `--slices` (slice Python all'indietro), L4 test correlati, obblighi e stato DO NOT TOUCH, che resta `unavailable` senza un confronto fra due snapshot. Default: 20 vicini, 5 cambiamenti, budget 120.000 caratteri; le omissioni per budget sono dichiarate. Un linguaggio senza fatti semantici (SQL, PL/SQL, fallback regex) non produce chiamanti.

`snapshot.py symbols-at` e `codebase_map_symbols_at` portano intervalli di righe, o un diff unificato con lo snapshot base, ai simboli che li contengono, separando l'identità stabile dall'ancora di revisione. `snapshot.py stale-callers <candidato> --base <base>` e `codebase_map_stale_callers` confrontano i digest di due snapshot e classificano i chiamanti dei simboli cambiati: `edit_impact` (RED, da ispezionare o modificare), `validation_impact` (GREEN, da rieseguire i test), `do_not_touch`; la classificazione non legge schede.

## Contesto delimitato

`scope_planner.py` seleziona l'evidenza di un intervento da snapshot, archi e indice (`daodan/scope-plan/v1`, stati `incomplete`, `needs_localization`, `needs_split`, `ready_for_attempt`); `context_packet.py` la impacchetta per un destinatario (`daodan/context-packet/v1`, stati `ready`, `incomplete`, `needs_split` con `status_reason` `missing_support`, `core_too_large`, `core_conflict`, `projection_limit`, `work_limit`, `not_localized`, `empty_core`); `map_slice.py` proietta la stessa evidenza per i pianificatori (`daodan/map-slice/v1`). Ingressi: `snapshot.py context` e `codebase_map_context`. Tutto è lavoro di macchina: nessuna chiamata a un modello, nessun refresh implicito di indici. Un pacchetto è evidenza per un tentativo: non autorizza scritture, non completa compiti, non supera gate. I quattro contratti sono in `contracts/context.toml`; il testo in `references/scope.md` e `references/context.md`. Nella misura del 2026-10-27 il pacchetto statico è stato il percorso più costoso e non è il default.

## Embedding opzionali

`embedding_worker.py` indicizza e interroga con EmbeddingGemma 2 in ONNX q4 (circa 206 MB, pesi condivisi per utente), in un interprete separato scelto esplicitamente, senza scaricare nulla durante una query. `retrieval.search` li fonde per rango reciproco (`exact-rrf75-25-k60-v1`: 0,75 denso, 0,25 lessicale, k 60), sempre sotto le ancore esatte. La misura del 2026-10-27 non ha trovato un compito in cui battessero l'indice lessicale, quindi restano disattivati per default (`references/embeddings.md`).

## Consumo della mappa

`references/standalone.md` è il contratto di lettura per ogni consumatore, ingressi inclusi: trovare un run completo (`codebase_map_runs`, `codebase_map_status`), navigare prima di leggere a tappeto, verificare l'impatto prima di modificare, dichiarare evidenza assente o alla deriva (`codebase_map_diff`) e proseguire con l'esplorazione ordinaria, senza avviare analisi, aggiornamenti o approfondimenti implicitamente. Senza MCP valgono i Markdown pubblicati e gli script.

senior-review esige una mappa completa dell'intero progetto prima di una review: la sua Phase 0 e la sua Phase 1 usano `search`, `outline`, `graph`, `read`, `edit_impact`, `symbols_at` e `modules` del run esistente, e nessuna fase della review analizza il progetto al suo posto (`plugins/senior-review/README.md`, sezione Prerequisito).

## Policy e contratti

`policies/write-confinement.toml`: ogni scrittore della mappa crea file solo nella directory del proprio run, più lo store delle schede; gli indici derivati (`retrieval.sqlite`, `engine-edges.sqlite` con `engine-report.json`, `engine-pass.running` e `engine-pass.log`, `embeddings.sqlite`) stanno accanto al manifest sotto `snapshot/`. L'enforcement è a livello di prompt e di contratto di proprietà nei ruoli: un hook di plugin sarebbe globale alla sessione e un hook per agente non è provato funzionante da un plugin installato (`mechanical_wired = false`).

`contracts/context.toml` esporta i quattro record del contesto delimitato: richiesta, piano di scope, pacchetto e map slice.

## Test

In `tests/` alla radice del repository: 22 file `test_codebase_map_*.py` e 13 file `test_xray_*.py`, 884 test in tutto, più `skills/map/scripts/tests/test_modules.py` (6 test). Esecuzione: `python -B -m pytest -q tests` dalla radice.
