# Identificazione del perimetro di review

Data: 4 novembre 2026.

**Stato:** proposta iniziale.

**Collocazione:** Phase 0 "Target Resolution" di `plugins/senior-review/skills/review-preparation/references/team-review.md`. Oggi la Phase 0 risolve solo file/directory, diff range, PR e plan/spec/doc; modulo, feature e termini di dominio non sono gestiti. Questa spec la sostituisce. La Phase 1 "Context Building" resta invariata.

## Phase 0 — Che cosa rivedere

La Phase 0 traduce il prompt nel perimetro esatto della review: cartelle, file o un mix dei due. Non prepara il contesto e non sceglie i reviewer.

```text
Prompt + Codebase Map → cartelle e/o file → contesto → review
        Phase 0                         Phase 1
```

Un modulo non coincide con una directory o un package: Codebase Map lo definisce come un insieme di funzioni, classi, file o componenti con una responsabilità comune. La Phase 0 verifica i membri e li converte in path.

Una cartella entra nel perimetro solo se tutto il suo contenuto pertinente è nel target; altrimenti si elencano i singoli file.

## Dal prompt ai path

La Phase 0 non esplora il codice: converte il prompt in interrogazioni di Codebase Map e lavora sui loro risultati. Usa solo gli indici del run (lessicale, grafo dei moduli, grafo statico), mai gli artefatti di analisi `01..07.md`: la regola di indipendenza della Phase 0c e della Phase 1c protegge le conclusioni analitiche, non gli indici.

1. **Estrai gli anchor.** Dal prompt: path, identificatori (`path::Nome` o nome semplice), nomi di modulo o componente, messaggi di errore, termini di dominio. Un changeset è un anchor: i suoi file vengono dal diff.
2. **Risolvi ogni anchor con lo strumento adatto.**

| Anchor | Strumento | Risultato |
|---|---|---|
| path, documento, changeset | nessuno: i path sono già noti; per un diff `codebase_map_symbols_at` dà i simboli toccati | file |
| intero progetto | `codebase_map_scope`: radice ed esclusioni dell'inventario | radice |
| nome di modulo o sub-app | `codebase_map_modules(query=nome)` sul grafo dei moduli: `resolved` dà membri e `read_scope`. Altrimenti `codebase_map_modules()` senza argomenti elenca ogni modulo con nome e `responsibility` (o `description` dal manifest): il modello sceglie quello che corrisponde all'intento. Nessun modulo adatto: ricerca lessicale sullo stesso nome | cartelle e file membri |
| identificatore, errore, termine di dominio | `codebase_map_search(query)` sull'indice lessicale: simboli esatti e frame di traceback primi, poi match per subtoken; una query per gruppo di nomi, `limit` 20 | simboli con path e righe |
| feature (flusso) | `codebase_map_graph(paths, hops=1)` dai simboli trovati: caller e callee; un hop in più solo per attraversare un wrapper | file del flusso |
| impatto di una modifica | `codebase_map_edit_impact(targets)`; con un run base, `codebase_map_stale_callers` | caller, test, obblighi |

3. **Verifica le candidate.** `codebase_map_outline` sul file di un hit mostra i suoi altri simboli; `codebase_map_read` solo sulle sezioni che decidono se una candidata appartiene al target. Documentazione e `AGENTS.md` confermano responsabilità e confini senza caricare interi archivi.
4. **Riduci a path.** I simboli confermati diventano i loro file; una cartella sostituisce i file solo se tutto il suo contenuto pertinente è nel target.

Gli embedding si usano solo se abilitati e se l'indice lessicale non trova gli anchor. Ricerche e query non consumano token di modello; entrano nel contesto solo i risultati letti. Budget indicativo: circa 6 ricerche e 10 letture per simbolo. La Phase 0 si ferma quando ogni anchor è risolto: nessuna lettura di ogni hit, nessuna espansione per aumentare la recall. Se restano due target materialmente diversi, chiede quale rivedere.

## Esempi

Difficoltà crescente. Path reali di questo repository; hit illustrativi.

### 1. Path esplicito: nessuna ricerca

> Rivedi `plugins/codebase-map/skills/map-method/scripts/snapshot.py`.

```text
Anchor:    path
Chiamate:  nessuna
Perimetro: plugins/codebase-map/skills/map-method/scripts/snapshot.py
```

### 2. Changeset: il diff decide

> Rivedi gli ultimi due commit.

```text
Anchor:    range HEAD~2..HEAD
Chiamate:  git diff HEAD~2..HEAD --name-only
           codebase_map_symbols_at(diff)        → simboli toccati, per il contesto
Perimetro: plugins/codebase-map/skills/map-method/references/entry-team-analyze.md
           plugins/codebase-map/skills/map-method/SKILL.md
```

### 3. Nomi di file senza path: l'indice li trova

> Rivedi le modifiche a snapshot e retrieval.

```text
Anchor:    "snapshot", "retrieval"
Chiamate:  codebase_map_search("snapshot")      → scripts/snapshot.py, snapshot_store.py, json_snapshot.py
           codebase_map_search("retrieval")     → scripts/retrieval.py
Decisione: "modifiche" = changeset → tieni solo i file nel diff corrente
Perimetro: plugins/codebase-map/skills/map-method/scripts/snapshot.py
           plugins/codebase-map/skills/map-method/scripts/retrieval.py
```

### 4. Modulo per nome: il grafo dei moduli risponde

> Rivedi il modulo di context building e la sua documentazione.

```text
Anchor:    modulo "context building", "documentazione"
Chiamate:  codebase_map_modules(query="context building")
             → status resolved, match partial
             → membri: scripts/context_packet.py, scope_planner.py, semantic_index.py
           codebase_map_search("context building")  → docs/research/context-building-*.md
Decisione: i membri non coprono tutta scripts/ → file singoli, non la cartella
Perimetro: plugins/codebase-map/skills/map-method/scripts/context_packet.py
           plugins/codebase-map/skills/map-method/scripts/scope_planner.py
           plugins/codebase-map/skills/map-method/scripts/semantic_index.py
           docs/research/context-building-research.md
           docs/research/context-building-benchmarks.md
```

### 4b. Modulo che il grafo non conosce: si scende al lessicale

> Rivedi il modulo di context building.

```text
Anchor:    modulo "context building"
Chiamate:  codebase_map_modules(query="context building")  → status unknown
           codebase_map_modules()  → 9 moduli con responsibility; nessuno parla di contesto o packet
           codebase_map_search("context building")
             → context_packet.py::build_packet, scope_planner.py::plan_scope,
               semantic_index.py::ContextIndex, mcp.md#preparing-the-context-tool
           codebase_map_outline(context_packet.py)  → importa scope_planner e semantic_index
Decisione: i tre file hanno una responsabilità comune → perimetro; mcp.md è documentazione, resta a Phase 1
Perimetro: plugins/codebase-map/skills/map-method/scripts/context_packet.py
           plugins/codebase-map/skills/map-method/scripts/scope_planner.py
           plugins/codebase-map/skills/map-method/scripts/semantic_index.py
Dopo:      codebase_map_modules(proposals=[{name, responsibility, members, evidence}])
           registra il modulo come inferred: la prossima review lo risolve al passo 1
```

### 5. Feature per flusso: un hop di grafo

> Rivedi come una ricerca MCP arriva all'indice lessicale.

```text
Anchor:    "ricerca MCP", "indice lessicale" → identificatori: search, lexical, index
Chiamate:  codebase_map_search("codebase_map_search")  → mcp_server.py::codebase_map_search
           codebase_map_graph(paths=[mcp_server.py::codebase_map_search], hops=1)
             → callee: mcp_service.py::search, retrieval.py::query_index
           codebase_map_outline(retrieval.py)  → conferma: query_index legge retrieval.sqlite
Decisione: tre file del flusso, niente secondo hop (nessun wrapper)
Perimetro: plugins/codebase-map/skills/map-method/scripts/mcp_server.py
           plugins/codebase-map/skills/map-method/scripts/mcp_service.py
           plugins/codebase-map/skills/map-method/scripts/retrieval.py
```

### 6. Termine di dominio che non è nel codice: fallback e domanda

> Rivedi la gestione della concorrenza.

```text
Anchor:    "concorrenza"
Chiamate:  codebase_map_search("concorrenza")  → 0 hit
           codebase_map_search("concurrency lock thread")  → riformulazione una volta
             → confinement.py::acquire_lock, embedding_worker.py::_spawn, store_graph.py::_txn
           embedding (se abilitato)  → stessi file più snapshot_store.py
Decisione: due target materialmente diversi: lock dell'indice vs processo embedding
Esito:     domanda all'utente: "Lock dell'indice (confinement.py, store_graph.py)
           o processo di encoding (embedding_worker.py)?"
```

## Confine con la Phase 1

La Phase 1 riceve l'elenco e raccoglie il contesto: file completi, caller, test, contratti, documentazione. Queste letture non allargano il perimetro.

Il perimetro è ciò che la review giudica (`conclusion_paths`), non ciò che legge (`read_scope`). Per impatti, modifiche di signature, interfacce ed errori di flusso la lettura segue il grafo fin dove la propagazione si ferma, e lo strumento lo decide da solo: `codebase_map_stale_callers` mette in RED i caller diretti di un'interfaccia cambiata e si ferma al primo caller la cui interfaccia non cambia; i caller oltre quel punto sono GREEN, da ritestare e non da riscrivere. `codebase_map_edit_impact` aggiunge le signature di secondo livello con `hops=2`. Un hop in Phase 0 serve a trovare il perimetro; la profondità in Phase 1 serve a giudicarlo. Un difetto trovato in un caller fuori perimetro resta un finding con `introduced_by_candidate`, non un allargamento.

## Testo proposto per la Phase 0

Sostituisce il punto 1 della Phase 0 attuale; i punti 2–4 (diff, estensioni, `00-scope.md`) restano.

```markdown
## Phase 0: Target Resolution

1. Convert the request into paths, after `references/candidate-grounding.md`
   has fixed the target kind. Use only the run's indexes (lexical index, module
   graph, static graph), never its analysis artifacts.
   - Anchors: paths, `path::Name` or bare identifiers, module or component
     names, error text, domain terms. A commit, range or PR is an anchor: its
     files come from `git diff {range} --name-only` or `gh pr diff {number} --name-only`.
   - Resolve each anchor, cheapest first:
     - file, directory, document, changeset: no search; `codebase_map_symbols_at`
       for the symbols a diff touches.
     - whole project: `codebase_map_scope`.
     - module or sub-app: `codebase_map_modules(query=NAME)`; `resolved` gives
       members and `read_scope`, `needs_clarification` asks, else fall through.
     - identifier, error, domain term: `codebase_map_search(query)`, one query
       per name group, `limit` 20; embeddings only when enabled and lexical
       search finds nothing.
     - feature: `codebase_map_graph(paths, hops=1)` from the hits found; one
       more hop only through a thin wrapper.
   - Confirm with `codebase_map_outline`; `codebase_map_read` only the section
     that decides membership. `AGENTS.md` and docs confirm boundaries.
   - Reduce symbols to files; a directory only when all its pertinent content is
     in target. Plan, specification or document: the paths, symbols and contracts
     it names are the scope; the file itself is the artifact under review.
     Two materially different targets: ask. Stop when every anchor is resolved.
```

## Verifica

Nessun caso è ancora eseguito. Due livelli, nell'ordine.

**Livello 1, deterministico (pytest, zero token).** Un fixture con sette file e un `codebase-modules.json`, costruito come in `scripts/tests/test_modules.py`. Un test per esempio: il prompt è fisso, le chiamate sono quelle della riga "Chiamate", l'asserzione è sui risultati dello strumento.

| Esempio | Asserzione |
|---|---|
| 1, 2 | `symbols_at` su un diff di due righe restituisce il simbolo toccato e nessun altro |
| 3 | `search("snapshot")` mette `snapshot.py` al primo posto; `search("retrieval")` trova solo `retrieval.py` |
| 4 | `query("context building")` è `resolved` quando il modulo è dichiarato, con i tre membri attesi |
| 4b | senza dichiarazione: `unknown`; l'elenco senza argomenti contiene `responsibility` di ogni modulo; `search("context building")` trova i tre file per subtoken |
| 5 | `graph(hops=1)` dal simbolo d'ingresso restituisce esattamente le due callee |
| 6 | `search("concorrenza")` è vuota; `search("concurrency lock thread")` trova file di due moduli diversi |

Fallimento = lo strumento non restituisce ciò che la spec presume. A quel punto si corregge la spec, non il test.

**Livello 2, con modello (esperimento, costa token).** Il testo proposto per la Phase 0 viene eseguito su questo repository con i sette prompt. Metrica fissata prima: perimetro uguale a quello atteso, file per file; chiamate al massimo quelle elencate più una riformulazione; esempio 6 termina con una domanda, non con un perimetro. Baseline: la Phase 0 attuale, che su 3, 4, 4b, 5 e 6 non produce alcun perimetro. Un replicato per prompt; un modello economico e uno forte.
