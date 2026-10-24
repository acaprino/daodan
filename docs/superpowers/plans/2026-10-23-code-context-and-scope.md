# Code Context and Scope Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Reuse Daodan's existing protocol, specialist ownership and measured review roster; do not create a second scheduler or duplicate review process.

**Goal:** Collegare mappa semantica Markdown, grafo con archi Jedi e ricerca locale con embedding ai processi Daodan, selezionando un perimetro verificabile che riduca il contesto LLM.

**Architecture:** `codebase-map` possiede evidenza, ricerca, selezione del perimetro e pacchetti. `project-lifecycle` li prepara per le fasi del ciclo; gli altri proprietari consumano gli artefatti pertinenti. `project-protocol` conserva run, autorizzazioni, consegne e gate; non interroga il database della mappa.

**Tech Stack:** Python >= 3.12, stdlib AST, SQLite e FTS5, Jedi esistente. Runtime embedding locale isolato e opzionale, selezionato nel gate P5; nessuna nuova dipendenza nella toolchain del compiler. CLI e MCP condividono le stesse implementazioni.

**Spec:** [Contesto e algoritmo di perimetrazione](../specs/2026-10-23-code-context-and-scope-design.md), [grafo §3.2](../specs/2026-10-19-graph-grounded-economy-routing-design.md), [composizione I1/I2](../specs/2026-10-20-system1-work-graph-composition-design.md).

**Research intake:** [valutazione del materiale ricevuto](../reports/2026-10-23-code-context-research-assessment.md).
Le integrazioni seguenti precisano P3/P5/P6/P7/P10; non chiudono alcun passo.

## Global Constraints

- Primo percorso completo: Python/Jedi. Nessun nuovo engine per altri linguaggi.
- Snapshot immutabili; derivati della mappa in `.codebase-map/`; stato operativo in `.daodan/runs/<id>/` del checkout principale.
- Identità, revision anchor, digest, parser/resolver/model version e copertura accompagnano ogni derivato.
- Nessun LLM per scansione, inferenza Jedi, embedding locale, ranking, navigazione e rendering. Card e ragionamento LLM hanno un costo distinto e misurato.
- Perimetro inventariato da `tree_scope`, confini autorizzati e gate del processo non si riducono per rispettare un budget.
- Grafo del codice e DAG di lavoro restano distinti. I1 fornisce evidenza; I2 e i contratti approvati determinano le dipendenze delle task.
- Modificare kernel e adapter; rigenerare tutti i cinque host. Nessuna modifica manuale agli export, nessun aumento dei tetti di parole per far passare i controlli.
- Conservare modifiche estranee. Commit intermedi della consegna, pubblicazione e installazioni hanno perimetri distinti; questa richiesta non autorizza un commit globale o un push indiscriminato.
- Milestone e micro-task sono livelli diversi: prima dell'esecuzione dividere ogni milestone in unità da massimo quattro file, eccezione motivata fino a sei, e validare con `plan-check`. La pubblicazione degli export è una fase separata posseduta dal coordinatore, non un finto micro-task entro quel limite.

## Review Focus

1. Un arco rimosso o riscritto deve restare visibile nel confronto base/candidato: P2.
2. Un engine valido ma senza archi, oppure con copertura parziale, non deve sembrare assente né completo: P1/P2.
3. Un hub o un obbligo più grande del budget deve produrre residui riprendibili, senza perdere verifiche: P6/P7.
4. Snapshot, vettori o cursori obsoleti e aggiornamenti concorrenti devono essere rifiutati o aggiornati esplicitamente: P3/P5/P6.
5. Query italiane e descrizioni senza nomi del codice non devono essere dichiarate risolte da benchmark derivati dagli stessi identificatori: P5/P10.

---

## Stato e ordine di consegna

Questo documento pianifica l'implementazione. Nessuna casella di esecuzione è
chiusa dalla sola stesura del piano. La consegna Python precedente è descritta
nel [report](../reports/2026-10-22-codebase-map-python-resolver-delivery.md);
le sue verifiche non certificano il candidato futuro.

| Passo | Dipende da | Risultato consegnabile | Commit proposto |
|---|---|---|---|
| P0 | Piano | Baseline posseduta e riprendibile | `Record the code context implementation baseline` |
| P1 | P0 | Vista verificata degli archi lessicali e Jedi | `Expose verified Jedi edges through a shared read view` |
| P2 | P1 | Grafo e impatto consumano la vista, anche fra revisioni | `Use engine evidence in graph and impact queries` |
| P3 | P1 | Ricerca esatta e testuale locale di produzione | `Add incremental local code retrieval` |
| P4 | P3 | Vista Markdown semantica collegata alle entità | `Render source-bound semantic maps from stored cards` |
| P5 | P3 | Provider embedding locale incrementale, opt-in | `Add an optional local embedding retrieval provider` |
| P6 | P2, P3 | Algoritmo di perimetrazione con test autonomi | `Select progressive analysis and intervention scopes` |
| P7 | P4, P5, P6 | Pacchetti CLI/MCP con budget e ripresa | `Assemble bounded resumable code context packets` |
| P8 | P7 | Preflight, task e post-task del ciclo collegati | `Prepare code context throughout the lifecycle` |
| P9 | P8 | Documentazione, review, testing nel ciclo e finish coerenti | `Connect context packets to Daodan consumer methods` |
| P10 | P9 | Misure, cinque export e prove operative dichiarate | `Verify and document the code context delivery` |

P3 può seguire P1 prima di P2; P4 e l'esperimento P5 sono indipendenti dopo P3.
P6 funziona senza embedding, quindi non attende un download o una scelta di
modello. P7 verifica anche il percorso embedding. Con `IN_PLACE`, eseguire in
sequenza; il parallelismo richiede worktree e ownership conformi al protocollo.
La [ricerca](../specs/2026-10-23-code-context-research-prompt.md) procede a fianco
di P1/P2 e alimenta P5/P6 senza bloccare i contratti già necessari.

## Ripresa e commit

Usare il ledger esistente `daodan/work/v1`. Per ogni passo registrare nel run:
input e digest, scope posseduto, stato pre-fase, consegne attese, log dei gate,
hash del candidato, commit prodotto, eventuale interruzione e prossimo passo.
I dettagli stanno nei report del run; questa checklist ne riassume l'avanzamento.

All'inizio di una sessione:

```powershell
python plugins/project-protocol/skills/project-protocol/scripts/run_state.py agenda --project . --branch master
python plugins/project-protocol/skills/project-protocol/scripts/run_state.py show --project . --run-id <RUN_ID>
python plugins/project-protocol/skills/project-protocol/scripts/run_state.py resume --project . --run-id <RUN_ID> --session <SESSION_ID> --payload <RUN_DIR>/resume.json
```

`resume.json` conserva scope e autorizzazioni del run. La ripresa è una verifica,
non il permesso di ignorare un HEAD cambiato: `run_state.py resume` rifiuta un
`candidate` o un workspace diverso da quello registrato, quindi se i file dello
scope sono cambiati fuori sessione occorre prima verificare il delta ed eseguire
`run_state.py update` (oppure aprire un nuovo run collegato se cambia lo scope).
Sul runtime attivo passare `--out .tritech/daodan` a tutte le operazioni di
`run_state.py`. Un holder diverso richiede il percorso di takeover già definito,
non un nuovo run concorrente.

Prima di ogni fase mutante acquisire `pre_phase_sha` e contenuto dei file posseduti.
Prima del commit: verifica mirata, docs, versioni dei plugin modificati e versione
marketplace, build di tutti gli export, gate di pubblicazione, revisione dello
staged diff. Stage solo il candidato posseduto; mai `git add .`. Dopo il commit
registrare SHA e binding nel ledger. Una wave senza commit non è `sealed`.
Un fallimento mantiene aperto il passo; non annulla le consegne precedenti.
Recovery dai byte pre-fase, mai da `HEAD~1`, `git clean` o reset globale.

## Struttura e interfacce nuove proposte

Le firme seguenti sono il contratto da implementare, non API già esistenti.
`S` indica `plugins/codebase-map/skills/map-method/scripts/`.

| Unità | Responsabilità e interfaccia |
|---|---|
| `S/edge_view.py` | `load_edge_view(store, *, engine_store: Path | None = None) -> dict`: referenze effettive, prove, profilo, copertura e conflitti. Nessuna inferenza al momento della query. |
| `S/retrieval.py` | `refresh_index(manifest: Path, index_path: Path) -> dict`; `search(index_path: Path, query: str, *, anchors: list[dict], limit: int, embedding_result: dict | None = None) -> dict`. |
| `S/semantic_map.py` | `render_map(manifest: Path, *, cards_path: Path, paths: list[str], out: Path) -> dict`: Markdown deterministico e relativo manifest di provenienza. |
| `S/embedding_worker.py` | Sidecar a input/output file, `index` e `query`; import del runtime solo qui. Nessun download durante una normale query. |
| `S/scope_planner.py` | `prepare_scope(request, *, authority, indexes=None) -> dict`; `advance_scope(plan, request, *, authority, indexes=None, evidence=None, max_steps=100) -> dict`; `persist_scope(plan, output, *, authority) -> dict`. Snapshot descriptors live in the request; independent run authority is required again on resume. |
| `S/context_packet.py` | `assemble_packet(plan: dict, *, candidate, cards_path: Path, budget: dict, cursor: dict | None = None) -> dict`. Non crea o chiude run. |
| `plugins/project-lifecycle/skills/lifecycle-method/scripts/cycle_packets.py` | Adapter di orchestrazione `preflight`, `task-packet`, `post-task`; usa il provider tramite CLI/MCP e artefatti vincolati, mai import da percorsi privati di un altro plugin. |

Definire le regole dei payload JSON in
`plugins/codebase-map/contracts/context.toml`, nello stile dei contratti del
repository, e dichiararne l'export in `plugins/codebase-map/plugin.toml`
(`[contracts] exports = ["contracts/context.toml"]`): schemi
`daodan/context-request/v1`, `daodan/scope-plan/v1`, `daodan/context-packet/v1`
e `daodan/map-slice/v1` (proiezione I1 emessa da `codebase-map`).
Richiesta, piano, pacchetto e slice seguono i campi della specifica. I payload di
algoritmo non sostituiscono `work.json`; nei consumatori `[contracts]` non è
usato nei rispettivi `plugin.toml` (che ammettono solo `exports`), mentre i
workflow sidecar in `plugins/daodan/workflows/*.toml` dichiarano
`codebase-map/contracts/context.toml` in `[contract].shared_schemas`. Non riusare
`semantic_index.py` per i vettori: quel nome identifica già il resolver in memoria.

Indici per snapshot accanto al manifest: `retrieval.sqlite` e `embeddings.sqlite`.
Cache riusabili di modelli e vettori sotto `.codebase-map/cache/`, con hash e
versioni; il file bound allo snapshot espone soltanto le entità della propria
generazione. Markdown, pacchetti e cursori prodotti dal provider restano sotto
il run della mappa. Aggiornare `plugins/codebase-map/policies/write-confinement.toml`
e le validazioni di percorso in `S/mcp_service.py` (`_validate_artifact_paths`)
per confinare esplicitamente `engine-edges.sqlite`, `retrieval.sqlite`,
`embeddings.sqlite`, `.codebase-map/cache/`, pacchetti e cursori. Il coordinatore
li referenzia per digest o ne conserva copie nel proprio run; registra avanzamento
e consegne in `.daodan/` (o `.tritech/daodan` sul runtime attivo) senza concedere
al provider di scrivere fuori dai propri confini.

## P0: baseline, ownership e checkpoint

**Files:** piano e specifica; report Python esistente; payload e log nel nuovo
run posseduto. Nessuna modifica al prodotto.

**Interfaces:** consuma il working tree reale e l'agenda; produce scope, baseline,
ambiente verificato, grant di commit riferito alla richiesta e piano del run.

- [x] Inventariare modifiche tracked/untracked e dipendenze della consegna Python. Il checkout iniziale contiene molto lavoro estraneo; non costruire un commit da tutto l'albero.
- [x] Rendere disponibile una baseline riproducibile della sola consegna Python e delle dipendenze adottate (`6095026738ebbabcf2386380183b827c9d8be8fc`). Se resta non committata, preparare il suo commit posseduto con kernel/export coerenti prima di P1; riportare lo SHA reale. Non fingere che il vecchio HEAD contenga già Jedi.
- [x] Inizializzare o riprendere il run tramite protocollo, dichiarando fasi, consegne, gate e modalità workspace scelta nel ciclo. In assenza di una scelta necessaria risolvibile dal contesto, chiarirla prima delle modifiche al prodotto.
- [x] Scomporre i passi in micro-task ($\le 4$ file per task, max 6 con `granularity_exception`: `P2a` per `store_graph.py`/`semantic_store.py`/`store_consumers.py`, `P2b` per `source_reader.py` e test stale-callers/edit-impact, `P2c` per `snapshot.py`/`mcp_service.py`/`mcp_server.py`, `P7a` per `context_packet.py` e test, `P7b` per CLI/MCP senza mai condividere la wave con `P2c`, `P8a` per `cycle_packets.py` e test, `P8b` per i riferimenti prosa, `P9` diviso per plugin) e validare `run_state.py plan-check --project . --payload <RUN_DIR>/plan.json`; atteso: exit 0.
- [x] Registrare baseline dei test pertinenti con Python >=3.12, disponibilità Jedi, MCP SDK e grammatiche; distinguere fallimenti, skip e prerequisiti mancanti.
- [x] Salvare checkpoint e commit documentale P0. **Done:** nuova sessione può identificare baseline, scope, prossimo passo e verifiche senza la chat.

## P1: archivio Jedi e vista comune

**Files:** `S/resolve_edges.py`, nuovo `S/edge_view.py`,
`tests/test_codebase_map_resolve_edges.py`, nuovo `tests/test_codebase_map_edge_view.py`.
Docs: `docs/plugins/codebase-map.md`, riferimento `snapshot.md` nel budget esistente.

**Interfaces:** conserva `read_edge_store(path, store)`; `load_edge_view` produce
`references`, `profile`, `coverage`, `conflicts`, `gaps`, con schema versionato
(`EDGE_VIEW_VERSION`) e `target_kind` (`protocol|interface|concrete`).

- [x] Aggiungere regressioni: `test_resolver_version_mismatch_is_rejected`, `test_completed_empty_pass_is_distinct_from_missing_store`, `test_engine_target_must_belong_to_snapshot`, `test_divergent_targets_remain_conflicts`. Assert: nessun target incompatibile entra nelle relazioni effettive; byte del manifest invariati.
- [x] Eseguire i nuovi casi e conservare il fallimento che dimostra il gap, non un errore di fixture.
- [x] Validare versione resolver, reference/callsite/target, profilo engine e copertura. Persistire anche una passata valida con zero archi (con `no_edges_reason` nei metadati); un fallimento conserva il derivato precedente senza presentarlo come corrente.
- [x] Implementare la vista: riferimenti lessicali più inferenze confermate su irrisolti, deduplicazione con provenance, conflitti separati, candidati fuori dalle relazioni confermate. Distinguere dichiarazione di protocollo/ABC da implementazione concreta tramite `sem_declarations` e `signatures`.
- [x] Aggiungere report completo su file e modalità di risposta compatta esplicita, mantenendo la compatibilità della CLI esistente; i futuri wrapper usano quella compatta.
- [x] Verificare `python -B -m unittest discover -s tests -p 'test_codebase_map_resolve_edges.py'` e `... -p 'test_codebase_map_edge_view.py'`; atteso: nessun failure, skip motivati.
- [x] Aggiornare docs, gate comuni e commit P1. **Done:** una sola vista verificata utilizzabile senza avviare Jedi o caricare report completi nel contesto LLM.

## P2: consumatori del grafo e impatto fra revisioni

**Files:** `S/store_graph.py`, `S/semantic_store.py`, `S/store_consumers.py`,
`S/source_reader.py`, `S/snapshot.py`, `S/mcp_service.py`, `S/mcp_server.py`;
test esistenti di graph, edit-impact, stale-callers e MCP. Dividere core/store
(`P2a`), analisi/stale-callers (`P2b`) e CLI/MCP (`P2c`) in micro-task.

**Interfaces:** estendere le API esistenti con parametri keyword opzionali per
gli store engine; `build_stale_callers(base, candidate, *, limit=100,
base_engine_store=None, candidate_engine_store=None)`. La lettura del default
bound store può avvenire automaticamente; una query non avvia una passata engine.
`_callee_interface_digests` per la freshness persistente di `cards.sqlite` resta
lessicale (`freshness_basis="lexical"`), mentre il drift su chiamati risolti via
engine è esposto separatamente (`engine_callee_drift`) senza invalidare `cards.sqlite`.

- [x] Scrivere regressioni per arco Jedi presente in graph, primo/secondo hop, `store_consumers` e callsite; rimuovere il falso blind spot mantenendo il resolver originale visibile.
- [x] Scrivere i casi di staleness del codice (`removed_target`, `rewired_call`, `dispatch_set_changed` per implementazioni di un protocollo) separati dai casi di comparabilità dell'engine (`only_base_has_engine`, `only_candidate_has_engine`, `different_engine_version`, `sampled_coverage_differs`): nessun caso asimmetrico o flip protocollo/concreto può dichiarare indipendenza o generare un falso `rewired_call` confermato.
- [x] Collegare tutti i consumatori alla vista P1 e confrontare i grafi di entrambe le revisioni. Calcolare sempre lo strato lessicale e riportare separatamente lo stato dello strato engine (`complete|partial|unavailable|incomparable`) con `{items, total, truncated}`.
- [x] Propagare gli stessi campi in CLI, servizio e wire MCP; verificare percorsi consentiti e binding dello store. Nessun altro resolver copiato negli adapter.
- [x] Eseguire `test_codebase_map_edit_impact.py`, `test_codebase_map_stale_callers.py`, `test_xray_source_reader.py`, `test_codebase_map_mcp.py`, `test_codebase_map_mcp_wire.py` con unittest discover, un modulo per processo.
- [x] Aggiornare docs, gate comuni e commit P2. **Done:** impatto e grafo usano le prove Jedi disponibili senza perdere relazioni della base o nascondere copertura mancante.

Checkpoint P2 (2026-10-23): implementazione e regressioni verificate, inclusa
la chiusura dei cinque rilievi della revisione congiunta P2/P3. Commit
`2f55484a5591`. Il blocco del budget istruzioni è risolto con la
[riparazione verificata](../reports/2026-10-23-instruction-budget-repair.md).
Gate obbligatori superati; evidenze nel run `code-context-scope-20261023`.

## P3: indice locale e ricerca dei punti di partenza

**Files:** nuovo `S/retrieval.py`, contratti in `plugins/codebase-map/contracts/`,
nuovo `tests/test_codebase_map_retrieval.py`; harness
`evals/codebase-map/retrieval-benchmark/run_benchmark.py` come riferimento da riusare.
Docs: `docs/plugins/codebase-map.md` e README del benchmark.

**Interfaces:** `refresh_index` pubblica un indice derivato bound allo snapshot;
`search` restituisce ID, anchor, provenienza, rank, matched/returned e troncamenti.

- [x] Congelare fixture con nome esatto, traceback, nome ambiguo, omonimi, rename, simbolo cancellato, file escluso e query italiana. Assert: gli exact verificati precedono i candidati e nessun risultato esce dall'inventario.
- [x] Portare in produzione soltanto le parti necessarie della baseline exact/subtoken/FTS5 già misurata, con query parametrizzate. Rilevare FTS5 indisponibile e dichiarare la capacità mancante.
- [x] Aggiornare per hash i documenti modificati, eliminare quelli rimossi e pubblicare atomicamente. Indicizzare metadati, firma e sorgente senza generare riassunti LLM; card fresche sono arricchimenti tracciati, mai un prerequisito della ricerca.
- [x] Registrare gli input necessari al riuso, incluse assenze rilevanti e cambi di ambiente/configurazione; testare aggiunta di un export prima assente e passaggio da registro vuoto a popolato. Se il tracciamento manca, rebuild dichiarato, non cache considerata fresca.
- [x] Verificare `test_codebase_map_retrieval.py` e `test_codebase_map_retrieval_benchmark.py`; confronto incrementale/full rebuild identico per lo stesso input e schema.
- [x] Aggiornare docs, gate comuni e commit P3. **Done:** localizzazione locale utilizzabile anche senza embedding.

Checkpoint P3 (2026-10-23): ricerca exact/subtoken/FTS5, indice incrementale
e contratti implementati nel commit `8694a96dfda8`. I test coprono anche il
contesto fuori dai simboli, i caratteri form-feed e i traceback misti. Gate
obbligatori superati dopo la riparazione documentata in P2. Embedding,
selezione del perimetro e pacchetti automatici restano rispettivamente P5,
P6 e P7.

## P4: mappa semantica Markdown riutilizzabile

**Files:** nuovo `S/semantic_map.py`, `S/card_store.py` soltanto se un campo necessario
manca, nuovo `tests/test_codebase_map_semantic_map.py`; riferimenti `deepen.md` e
`reading.md` sotto `plugins/codebase-map/skills/map-method/references/` (entrambi a
headroom 0 parole in `test_xray_load_budget.py`: applicare modifiche a saldo parole
$\Delta \le 0$).

**Interfaces:** `render_map` emette indice per area e sezioni con entity ID,
anchor, purpose, contratti, effetti, collegamenti al grafo e stato della card
(`freshness_basis="lexical"`).

- [x] Scrivere fixture fresh/stale/unread e simbolo rimosso; assert: nessuna purpose inventata, provenienza completa, output deterministico, sorgenti intatti.
- [x] Rendere le card nello store canonico come Markdown generato. Preservare i report di fase esistenti e usare link, non copie concorrenti da mantenere a mano.
- [x] Collegare il bisogno di una card mancante al metodo di approfondimento già esistente, limitato all'area richiesta; riusare le card fresche e registrare il costo LLM effettivamente osservato.
- [x] Eseguire `test_codebase_map_semantic_map.py`, `test_codebase_map_card_store.py`, `test_xray_load_budget.py`.
- [x] Aggiornare docs, gate comuni e commit P4. **Done:** Markdown navigabile e coerente con lo snapshot, con copertura semantica dichiarata.


Checkpoint P4 (2026-10-23): renderer, metodo e documentazione consegnati nel commit `1602f97490df`; test semantici 15/15 e card store 23/23 superati sul candidato isolato. La riparazione documentata in P2 supera il gate condiviso skill-load-budget e l'intera suite del candidato: nessun blocco residuo per P4.

## P5: embedding locale, cache e gate di adozione

**Esperimento preliminare, 23 ottobre 2026:** completata
[prova reale locale CodeRankEmbed](../../../evals/codebase-map/retrieval-benchmark/RESULTS-2026-10-23-coderank-local.md)
su 1.423 simboli e 36 query. Con soli metadati migliora Recall@20 da 0,7778 a
0,8333; con corpi Python la baseline lessicale raggiunge 0,9167 e la combinazione
con CodeRank 0,8611. Runtime offline verificato; nessuna promozione a default.
Cache per contenuto, integrazione e holdout separato sono implementati e verificati nel checkpoint P5.

**Files:** nuovo `S/embedding_worker.py`, `S/retrieval.py`, nuovo
`tests/test_codebase_map_embeddings.py`; estensioni del benchmark e report di
selezione in `evals/codebase-map/retrieval-benchmark/`. Nessun Qdrant obbligatorio.

**Interfaces:** file di richiesta `index`/`query` con schema, model revision,
tokenizer, document schema e hash; risposta con stato, artifact digest, metriche
e ID/rank. I vettori restano nel derivato, non nello stdout.

- [x] Riesaminare candidati e fonti primarie della ricerca: manutenzione, licenza, Windows/Linux e Python, sicurezza del caricamento, dimensione, qualità italiana/inglese e costo totale. Registrare una scelta verificata prima di installare il backend. Se nessun candidato è ammissibile, P5 resta aperto con blocco specifico; P6 continua sulla baseline.
- [x] Separare runtime opzionale e toolchain. Riutilizzare il sidecar del benchmark dove idoneo, avvio del solo encoder con il runtime installato esplicitamente selezionato e `-I` (motivazione nel report P5); nessun import di codice del progetto, modello remoto non fissato o download implicito durante le query.
- [x] Testare con provider deterministico: modifica dello stesso ID invalida il vettore; modello/tokenizer/document schema diversi invalidano la cache; rename/cancellazione aggiornano l'indice; crash conserva l'ultima generazione valida; offline usa soltanto artefatti già disponibili.
- [x] Verificare l'hash dell'intero input codificato, path incluso quando presente; confrontare inventario, vettori e replay delle query con un rebuild indipendente. L'uguaglianza dei soli top-k non certifica che l'indice non conservi documenti rimossi.
- [x] Implementare cache per contenuto e provider, ranking locale e fusione versionata con P3. Usare storage derivato con ricerca esatta iniziale; introdurre ANN o un database dedicato solo se una misura ne dimostra la necessità.
- [x] Eseguire `test_codebase_map_embeddings.py`, regressioni retrieval e un'inferenza reale del provider scelto. Stubs provano il contratto, non supporto del runtime o qualità del modello.
- [x] Misurare baseline e embedding su holdout distinto, query italiane incluse. Rendere disponibile opt-in; abilitarlo come default solo se supera i criteri R9 della specifica. Documentare espressamente un esito non favorevole.
- [x] Aggiornare docs, requisiti opzionali, gate comuni e commit P5. **Done:** provider locale riproducibile, incrementale e disattivabile, con benefici e limiti misurati.

Checkpoint P5 (2026-10-23): provider opzionale offline, cache incrementale e fusione verificata, con pesi condivisibili tra progetti. Le 26 regressioni embedding e i 1.537 test del candidato passano; 10 controlli SDK sono esercitati separatamente. Holdout sintetico di 20 query: Recall@5 da 0,80 a 0,95, senza regressioni sugli exact. La versione 2 rende ogni vettore indipendente dal batch. Nessuna adozione a default: i risultati reali e i token complessivi restano da misurare in P10. Dettagli nel [report P5](../reports/2026-10-23-code-context-p5.md). P6-P10 restano da completare.

## P6: algoritmo di perimetrazione

**Files:** nuovo `S/scope_planner.py`, contratti di richiesta/piano,
nuovo `tests/test_codebase_map_scope_planner.py`.

**Interfaces:** `prepare_scope` e `advance_scope` seguono la procedura della
specifica; output `analysis`, `edit_candidates`, `potential_impact`, `validation_obligations`,
`deferred`, `unresolved`, `outside_boundary` con motivi e binding.

- [x] Scrivere i cinque casi della Review Focus e due controlli: un cambio di corpo non prescrive edit dei chiamanti; un file fuori write boundary resta un obbligo segnalato, non un edit autorizzato.
- [x] Aggiungere `test_impacted_caller_is_not_automatically_an_edit` e `test_similarity_cannot_satisfy_hard_support`: impatto e intervento restano distinti; una card pertinente non sostituisce il corpo corrente richiesto.
- [x] Implementare seed da diff/anchor e ricerca, classificazione degli obblighi prima del budget, espansione direzionale e frontiera deduplicata. Non inventare tipi di arco mancanti, né collegare test e requisiti per sola similarità.
- [x] Implementare arresti espliciti `needs_localization`, `needs_split` e ripresa legata agli input. Non usare un limite fisso di hop come prova di completezza e non trasformare una frontiera vuota in successo del task.
- [x] Aggiungere budget indipendenti di candidati, archi, round, tempo e token cumulativi; testare frontier checkpoint e azioni guidate dai gap senza retry equivalente. `ready_for_attempt` non chiude validazione né autorizza integrazione; l'arresto è `uncalibrated`.
- [x] Eseguire `test_codebase_map_scope_planner.py`: ordine deterministico, nessun obbligo perso, ripresa equivalente alla corsa continua, cursori obsoleti rifiutati.
- [x] Aggiornare specifica se la ricerca cambia la politica, con motivazione e confronto; docs, gate comuni e commit P6. **Done:** algoritmo verificabile e utilizzabile indipendentemente dal modello embedding.

## P7: contesto limitato e interfacce CLI/MCP

**Files:** nuovo `S/context_packet.py`, adapter `S/snapshot.py`, `S/mcp_service.py`,
`S/mcp_server.py`; nuovi `tests/test_codebase_map_context_packet.py` e casi MCP.
Docs: riferimenti `mcp.md`, `snapshot.md`, `reading.md` (con saldo parole $\Delta \le 0$
su `reading.md`). Dividere packer (`P7a`) e CLI/MCP (`P7b`) in micro-task, in wave
distinta da `P2c`.

**Interfaces:** CLI `snapshot.py context MANIFEST --request REQUEST.json
--recipient RECIPIENT.json --authority AUTHORITY.json --out OUTPUT_DIR [--cursor CURSOR.json]`; tool `codebase_map_context`
(registrato con annotazione `writes` in `mcp_server.py`, percorsi validati in
`_validate_artifact_paths`, senza avviare implicitamente `refresh_index` o
`embedding_worker.py`) con run ID e richiesta vincolata. Risposta: stato, packet
path/digest, contatori, gap, costo e cursore. Le letture del pacchetto riusano il
provider della mappa.

- [x] Testare budget con wrapper e metadati inclusi, deduplicazione di sorgenti sovrapposte, nucleo troppo grande e cursor replay. Assert: nessun `ready` se il nucleo eccede; tutti gli elementi omessi hanno motivo.
- [x] Implementare e confrontare con la baseline il packing con prerequisiti della specifica. Condensare eventuali cicli di prerequisiti (SCC) in unità tutto-o-niente (`needs_split` se la SCC eccede il budget). Testare prerequisito condiviso che rende ammissibile un bundle prima scartato, sostituzione card/corpo che perde un supporto, corpi identici con identità diverse e overflow dopo serializzazione. Limiti di lavoro espliciti; nessuna pretesa di ottimo o garanzia `1-1/e`.
- [x] Riutilizzare L0-L4 e letture verificate di `edit-impact`, senza costruire una seconda logica di impatto. Aggiungere card fresche, `engine_callee_drift` e riferimenti Markdown; dettaglio dei vicini progressivo.
- [x] Distinguere conteggio token del destinatario da stima e limite caratteri. Il caller passa lo spazio effettivamente disponibile e la riserva; non usare `chars/4` come garanzia. Conservare il packet completo su disco e stdout compatto.
- [x] Vincolare cursori ai digest di `{manifest, retrieval_index, edge_view, cards, request, policy_version}` e destinatario (`cursor_stale` su qualsiasi mismatch); scrittura atomica e collisioni rilevate. Stesso cursore/input restituisce gli stessi blocchi, non una nuova selezione casuale.
- [x] Eseguire test context, scope, edit-impact, MCP servizio e wire; verificare gli stessi esiti attraverso CLI e MCP.
- [x] Aggiornare docs, gate comuni e commit P7. **Done:** un agente riceve contesto circoscritto e può richiedere l'approfondimento successivo senza perdere il perimetro.

## P8: integrazione nel ciclo di lavoro

**Files:** nuovo `plugins/project-lifecycle/skills/lifecycle-method/scripts/cycle_packets.py`,
riferimenti lifecycle `preflight.md`, `waves.md`, `verify.md`, `realign.md` (a
headroom 1-6 parole in `test_skill_load_budget.py`: applicare modifiche a saldo
parole $\Delta \le 0$ sia per unità sia per step combinato);
nuovo `tests/test_cycle_context_packets.py`; `shared_schemas` nei workflow sidecar
`plugins/daodan/workflows/*.toml` pertinenti (mai in `project-lifecycle/plugin.toml`).
Dividere script/test (`P8a`) e riferimenti prosa (`P8b`) in micro-task.

**Interfaces:** `preflight` prepara richiesta, congela snapshot/store base ed emette
il pacchetto iniziale; `task-packet` (in sola lettura sugli indici condivisi, con
boundary uguale a `record["scope"]`) lega task, requisiti, write set e contesto;
`post-task` legge il delta aggiornato a barriera e produce obblighi residui. Il
coordinatore registra gli output tramite protocollo.

- [x] Scrivere fixture di workflow: bug senza diff, cambio firma, documento da aggiornare, task test e candidata modificata durante la preparazione. Un packet di un'altra revisione deve bloccare il dispatch dipendente.
- [x] Collegare P7 attraverso un adapter esplicito al provider, senza importare file privati cross-plugin. Il provider prepara dati; il coordinatore mantiene dispatch, stato, autorizzazioni e consegne.
- [x] Portare I1 (`daodan/map-slice/v1`, definito in `contracts/context.toml` e proiettato da `codebase-map`) come artefatto con digest al pianificatore. Non creare precedenze dal solo call graph e non allargare il write set a tutti gli `edit_candidates` (`edit_candidates` resta disgiunto da `outside_boundary`).
- [x] Dopo una modifica aggiornare snapshot/derivati necessari, invalidare pacchetti interessati e conservare obblighi aperti. Il budget non chiude una fase con contesto insufficiente.
- [x] Eseguire `test_cycle_context_packets.py`, `test_project_protocol.py`, `test_codebase_map_composition.py` e prove di interruzione prima/dopo la scrittura del pacchetto.
- [x] Aggiornare docs lifecycle/codebase-map, gate comuni e commit P8. **Done:** preflight, esecuzione e verifica usano il contesto della revisione corretta e si riprendono dal ledger.

Checkpoint P8 (2026-10-24): `cycle_packets.py` collega preflight, task e post-task
solo tramite le CLI pubbliche di protocollo e mappa. I receipt legano candidato,
task, scope, requisiti, gate e destinatario; la sola registrazione nel ledger non
invalida gli input di esecuzione, una modifica di codice o di indici sì. La
proiezione I1 viaggia come artefatto con percorso e digest, `edit_candidates`
restano disgiunti dal write set. La CLI distingue l'invocazione incompleta o
illeggibile (uscita 2, nessun traceback) dall'operazione rifiutata (uscita 1).
Il brief `context-cycle.md` (22 parole) entra nei passi del ciclo senza aumentare
i tetti esistenti: la skill lifecycle resta sotto il tetto di 630 parole (597
sull'albero principale, 599 sul candidato). I 17 test del ciclo e i 5
del budget passano su albero principale e candidato; la milestone si chiude con
la revisione indipendente e i gate registrati nel run. Dettagli nel
[report P8](../reports/2026-10-24-code-context-p8.md). P9-P10 restano da completare.

## P9: consumatori e chiusura

**Files:** `plugins/project-knowledge/skills/project-knowledge/references/preparation.md`
e `guide-method.md`; riferimenti di review effettivamente registrati nel candidato;
lifecycle `finish.md`, `realign.md`, `waves.md`; test di contratti dei consumatori.
Verificare i file correnti: la riorganizzazione dei revisori (`2026-10-23-specialist-reviewers-and-composition.md`, T9)
è un lavoro concorrente su `review_roster.py`, `candidate-grounding.md` e
`stack-dimensions.md`; non sovrapporre il `write_set` mentre T9 è aperto e mantenere
saldo parole $\Delta \le 0$ sui file soggetti a `test_skill_load_budget.py` (`light.md`,
`candidate-grounding.md`, `finish.md`, `realign.md`, `waves.md`). Dividere P9 in un
micro-task per plugin consumatore.

**Interfaces:** ciascun consumatore riceve packet e digest, scopo, gap e obblighi;
restituisce il proprio artefatto e le evidenze di verifica nel ledger esistente.

- [ ] Testare che documentazione consumi card e sorgenti fresche; review riceva il contesto consentito dalla propria lente. Il premise auditor conserva la propria indipendenza e non riceve conclusioni/card vietate dal suo contratto.
- [ ] Collegare testing attraverso lifecycle: requisiti e obblighi di validazione al proprietario dei test, che conferma gli oracoli. Il plugin testing resta leaf; nessuna dipendenza dura aggiunta soltanto per questo flusso.
- [ ] Collegare finish e realign: gate sul candidato, report degli obblighi residui, mappa e documentazione aggiornate dopo integrazione. Nessun deploy o pubblicazione automatica dedotta dal grafo.
- [ ] Eseguire i test pertinenti `test_review_knowledge_ports.py`, `test_review_pipeline_ports.py`, `test_codebase_map_composition.py`, `test_project_protocol.py` e nuovi casi consumatore; verificare i budget delle skill.
- [ ] Aggiornare docs per ogni proprietario, gate comuni e commit P9. **Done:** una matrice documenta per ciascun comando input usato, output, freshness, recovery e limiti.

## P10: verifica complessiva e consegna

**Files:** benchmark retrieval, nuovo `evals/codebase-map/context-scope/` per
fixture/harness/risultati, test di host binding, docs dei plugin e report finale
`docs/superpowers/reports/2026-10-23-code-context-delivery.md` (crearlo alla consegna).

**Interfaces:** consuma i checkpoint P0-P9; produce evidenza riproducibile e
tabella delle capacità effettivamente verificate, per percorso e host.

- [ ] Congelare holdout separato dalla taratura in un run dedicato (distinto dal run principale di questo repository per non invalidare `project_binding` in `run_state.py`): almeno un secondo progetto Python, query reali in italiano/inglese e scenari di firma/corpo/rimozione/hub/dinamismo. Gold verificato indipendentemente; pubblicare dimensione e limiti, non solo medie aggregate.
- [ ] Congelare il corpus alla revisione di partenza: escludere patch gold, documentazione post-fix e test di sola valutazione dalla ricerca runtime. Distinguere recall di localizzazione, impatto e supporti obbligatori; includere astensioni, timeout, OOM e run senza misura d'uso.
- [ ] Confrontare baseline testuale, Jedi, scope planner, embedding e composizione completa a pari budget. Includere full context solo quando entra; non contare un input impossibile come baseline battuta.
- [ ] Misurare recall dei target/obblighi, risultato dei task, token di preparazione/card/dispatch/retry, cache, latenza, memoria e aggiornamenti. Dati di fatturazione assenti restano `unavailable`, distinti dalle stime locali.
- [ ] Eseguire l'intero percorso Python su un host disponibile: richiesta naturale -> indice -> scope -> packet -> task -> delta -> verifiche -> aggiornamento documentale -> ripresa. Registrare modello/host/versione, tool reali e consegne; un mock non prova l'esecuzione.
- [ ] Verificare staticamente tutti i cinque export host (`exports/{claude,copilot,codex,pi,opencode}`), i 4 schemi esportati in `plugins/codebase-map/contracts/context.toml` e i percorsi annidati. Eseguire i probe degli host disponibili; riportare separatamente quelli non esercitati, senza dichiarare compatibilità runtime universale.
- [ ] Eseguire la suite completa e i gate comuni sul candidato effettivo; risolvere i difetti, conservare log e motivi degli skip. Aggiornare report, stato della specifica, indice docs e commit P10.
- [ ] Validare `run_state.py validate --project . --run-id <RUN_ID> --current`; chiudere solo se tutte le consegne e i gate obbligatori sono soddisfatti. Pubblicazione e refresh delle installazioni seguono il percorso autorizzato del repository.

## Gate comuni per ogni commit che cambia il kernel

Prima i test della milestone; poi docs/versioni, rigenerazione e controlli:

```powershell
python scripts/sync_plugin_docs.py
python scripts/sync_plugin_docs.py --check
python scripts/sync_codex_instructions.py --check
python scripts/daodan_build.py
python scripts/daodan_build.py --check --support
python scripts/lint_dependency_graph.py
python scripts/lint_bundled_paths.py
python scripts/lint_host_vocabulary.py
python scripts/lint_plugin_registration.py
python scripts/lint_fact_anchors.py
python adapters/copilot/policies/xray-guard/test_xray_guard.py
python -B -m unittest discover -s tests -p 'test_skill_load_budget.py'
python -B -m unittest discover -s tests -p 'test_xray_load_budget.py'
```

Per modifiche a CLI/MCP/dispatch/contratti aggiungere `test_daodan_host_rendering.py`
e `test_daodan_operational_binding.py`. Alla chiusura eseguire tutta la suite di
`.github/workflows/consistency.yml`. Sulla workstation Windows, la verifica
precedente ha richiesto processi separati per modulo per evitare esaurimento
di memoria: enumerare ogni `tests/test_*.py`, eseguirlo con unittest discover,
conservare un risultato per modulo e aggregare senza duplicare i retry. Non
saltare moduli per ottenere una suite verde. Grammatiche e MCP SDK mancanti
devono risultare come prerequisiti/skip reali, non come pass.

Aggiornare `version` nei plugin modificati e la versione marketplace prima del
build secondo il workflow corrente. Kernel e output generati di tutti gli host
entrano insieme nel commit. Un rebuild da un albero misto richiede prima una
baseline posseduta: non selezionare export a caso per nascondere la contaminazione.

## Tracciabilità dei requisiti e consegna finale

| Requisito | Passi e prova principale |
|---|---|
| R1 | P3/P4/P7: identità e freshness condivise; Markdown riproducibile |
| R2 | P1/P2: vista unica, conflitti, CLI/MCP |
| R3 | P2: archi rimossi/riscritti e comparabilità dei profili |
| R4 | P3/P5: baseline locale e sidecar senza chiamate LLM |
| R5 | P6: insiemi distinti e confini autorizzati |
| R6 | P6/P7: hub, budget, nucleo indivisibile e residui |
| R7 | P0/P6/P7/P8: ripresa equivalente e invalidazione |
| R8 | P8/P9: contratti dei proprietari e gate preservati |
| R9 | P5/P10: holdout, token totali e qualità |
| R10 | P2/P7/P10: parity, contratti e probe separati |

La consegna comprende mappa Markdown, grafo e ricerca interrogabili; algoritmo
e pacchetti riprendibili; integrazione nei processi; documentazione aggiornata;
storia dei commit e report dei limiti. Nessuna percentuale di risparmio è promessa
prima della misura. L'indice embedding disponibile e l'abilitazione di default
sono due esiti distinti, da riportare entrambi.

## Prompt per riprendere

> Riprendi `docs/superpowers/plans/2026-10-23-code-context-and-scope.md`.
> Leggi la specifica collegata e l'agenda di project-protocol; verifica il run,
> l'ultimo checkpoint, il candidato e le modifiche estranee. Continua dal primo
> passo aperto mantenendo gli scope e le autorizzazioni già registrati. Esegui i
> controlli del passo, aggiorna docs e ledger e prepara il commit intermedio
> posseduto con tutti gli export richiesti. Non ripetere fasi concluse su input
> identici e non usare verifiche di una vecchia revisione per chiudere la nuova.
