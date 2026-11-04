# Identificazione del perimetro di review

Data: 4 novembre 2026.

**Stato:** proposta iniziale.

**Collocazione:** Phase 0 "Target Resolution" di `plugins/senior-review/skills/review-preparation/references/team-review.md`. Oggi la Phase 0 risolve solo file/directory, diff range, PR e plan/spec/doc; modulo, feature e termini di dominio non sono gestiti. Questa spec la sostituisce. La Phase 1 "Context Building" resta invariata.

**Prerequisito:** Codebase Map deve aver già completato la mappatura dell'intero progetto prima di avviare la review. La Phase 0 usa gli indici di quel run esistente; la Phase 1 costruisce il contesto della review e non sostituisce questo prerequisito. Se la mappa completa manca, eseguire prima Codebase Map.

## Phase 0 — Che cosa rivedere

La Phase 0 traduce il prompt nel perimetro motivato della review: cartelle, file o un mix dei due, con eventuali lacune dichiarate. Non prepara il contesto e non sceglie i reviewer.

```text
Prompt + Codebase Map → cartelle e/o file → contesto → review
        Phase 0                         Phase 1
```

Un modulo non coincide con una directory o un package: Codebase Map lo definisce come un insieme di funzioni, classi, file o componenti con una responsabilità comune. La Phase 0 verifica i membri e li converte in path.

Una cartella entra nel perimetro solo se tutto il suo contenuto pertinente è nel target; altrimenti si elencano i singoli file.

## Dal prompt ai path

La Phase 0 localizza il target con gli indici del run (lessicale, grafo dei moduli, grafo statico) e letture mirate a verificarne i membri. Descrizioni e proposte di modulo servono a trovare sorgenti, non a stabilire premesse sul loro comportamento. Fino al completamento della Phase 0c, il coordinatore non legge artefatti di analisi `01..07.md`, card semantiche o knowledge leads prodotti da Codebase Map. La Phase 0c resta inline e ricava i propri leads dai sorgenti; la Phase 1c resta in un contesto isolato, riceve solo riferimenti di localizzazione nel perimetro e non accede a Codebase Map. Le interpretazioni del grafo e le descrizioni dei moduli non entrano nel suo prompt.

1. **Estrai gli anchor.** Dal prompt: path, identificatori (`path::Nome` o nome semplice), nomi di modulo o componente, messaggi di errore, termini di dominio. Un changeset è un anchor: i suoi file vengono dal diff.
2. **Risolvi ogni anchor con lo strumento adatto.**

| Anchor | Strumento | Risultato |
|---|---|---|
| path, documento, changeset | nessuno: i path sono già noti; per un diff `codebase_map_symbols_at` dà i simboli toccati | file |
| intero progetto | `codebase_map_scope`: radice ed esclusioni dell'inventario | radice |
| nome di modulo o sub-app | `codebase_map_modules(query=nome)` sul grafo dei moduli: `resolved` (un solo modulo confermato con nome o alias esatto, senza conflitti e con grafo aggiornato) dà membri e `read_scope`; `needs_clarification` (più moduli, conflitti o solo match parziali) chiede; `incomplete` (modulo proposto, membri mancanti o grafo non aggiornato) dà i membri da verificare. Altrimenti `codebase_map_modules()` senza argomenti elenca ogni modulo con nome e `responsibility` (o `description` dal manifest): il modello sceglie quello che corrisponde all'intento. Nessun modulo adatto: ricerca lessicale sullo stesso nome | cartelle e file membri |
| identificatore, errore, termine di dominio | `codebase_map_search(query)` sull'indice lessicale: simboli esatti e frame di traceback primi, poi match per subtoken; una query per gruppo di nomi, `limit` 20 | simboli con path e righe |
| feature (flusso) | `codebase_map_graph(paths, hops=1)` sui file dei simboli trovati (`paths` accetta file, non `file::simbolo`): archi di chiamata caller e callee, filtrati sui simboli pertinenti del passo corrente. Un hop è il passo di navigazione, non il criterio di arresto: si ripete dai simboli entrati nel target secondo le regole di copertura e arresto sotto | file del flusso |
| impatto di una modifica | `codebase_map_edit_impact(targets)`; con un run base, `codebase_map_stale_callers` | caller, test, obblighi |

3. **Verifica le candidate e copri il comportamento richiesto.** `codebase_map_outline` sul file di un hit elenca i suoi simboli con kind e righe, niente import né corpo; `codebase_map_read` solo sulle sezioni che decidono se una candidata appartiene al target. Documentazione e `AGENTS.md` confermano responsabilità e confini senza caricare interi archivi.
   Per una feature il target è il percorso dall'ingresso al risultato osservabile, inclusi i rami pertinenti alla richiesta: ogni simbolo entra perché svolge un passaggio di quel percorso, con la riga che lo dimostra; logging, utilità e altre dipendenze restano fuori quando sono accessorie al comportamento richiesto. Un percorso endpoint → servizio → repository → database richiede più hop; ognuno parte solo dai simboli già entrati, mai da tutto il vicinato. Un file o changeset richiesto esplicitamente mantiene il suo perimetro: le sue dipendenze sono contesto di Phase 1. Per ogni passaggio individuato si stabilisce se è nel target, se è una dipendenza esterna con confine identificato o se resta irrisolto. Un arco assente nel grafo non chiude il percorso: chiamate dinamiche, eventi e collegamenti via configurazione si localizzano con una ricerca mirata e si confermano leggendo registrazione, instradamento e destinazione pertinenti. Un collegamento non dimostrabile resta irrisolto.
4. **Riduci a path.** I simboli confermati diventano i loro file; una cartella sostituisce i file solo se tutto il suo contenuto pertinente è nel target.

Una ricerca lessicale valida senza hit si riformula una sola volta, con un sinonimo, una traduzione del termine o un identificatore già individuato. Se anche la riformulazione è vuota, si usano gli embedding solo se abilitati; senza risultati il collegamento resta irrisolto. Un indice mancante, non aggiornato o corrotto è una lacuna del prerequisito, non un risultato vuoto che autorizza il fallback.

Le interrogazioni non invocano un modello; i risultati letti entrano nel contesto. Budget iniziale per task: circa 6 interrogazioni, incluse quelle al grafo e la riformulazione, e 10 letture complessive, con nodi deduplicati; non si moltiplica per anchor. Nessuna lettura di ogni hit, nessuna espansione indiscriminata del vicinato.

La Phase 0 si arresta quando il comportamento richiesto è delimitato da evidenze oppure quando sono esauriti i collegamenti pertinenti del grafo e le altre piste concrete individuate; gli anchor sono punti di partenza. Si arresta anche al budget esaurito. L'esaurimento della ricerca non dimostra da solo la completezza della copertura: troncamenti e chiamate non risolte non provano che il grafo sia esaurito. Se restano lacune che impediscono di delimitare il comportamento richiesto, la risoluzione è incompleta: si restituiscono il perimetro trovato e i collegamenti ancora da risolvere, con il motivo dell'arresto. Se restano due target materialmente diversi, chiede quale rivedere.

**Checkpoint di ricerca: riuso del principio.** L'espansione filtrata è coerente con [context-building-research](../research/context-building-research.md), sezione "What holds and what literature supports", principio 4. Quella fonte non valida questo criterio di arresto: efficacia, copertura e costo della procedura restano da misurare con le verifiche sotto.

## Esempi

Difficoltà crescente. Path reali di questo repository; hit illustrativi. Le chiamate sono abbreviate: `run_id` è sottinteso, i file indicano i path del perimetro e le letture indicano selezioni da passare in `requests`.

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
             → status resolved, match exact
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
           codebase_map_outline(context_packet.py)  → build_packet e i suoi helper, con le righe
           codebase_map_read(context_packet.py::build_packet)  → importa scope_planner e semantic_index
Decisione: i tre file hanno una responsabilità comune → perimetro; mcp.md è documentazione, resta a Phase 1
Perimetro: plugins/codebase-map/skills/map-method/scripts/context_packet.py
           plugins/codebase-map/skills/map-method/scripts/scope_planner.py
           plugins/codebase-map/skills/map-method/scripts/semantic_index.py
Dopo:      codebase_map_modules(proposals=[{name, responsibility, members, evidence}])
           registra il modulo come inferred: la prossima query dà `incomplete` con i tre membri,
           non `resolved`; per promuovere questa proposta serve la dichiarazione in codebase-modules.json
```

### 5. Feature per flusso: un hop alla volta

> Rivedi come una ricerca MCP arriva all'indice lessicale.

```text
Anchor:    "ricerca MCP", "indice lessicale" → identificatori: search, lexical, index
Chiamate:  codebase_map_search("codebase_map_search")  → posizione della callback in mcp_server.py
           codebase_map_graph(paths=[mcp_server.py], hops=1)
             → seleziona gli archi della callback; non presume risolto il passaggio dinamico
           codebase_map_read(mcp_server.py:28–44,109–114)
             → service è MapService; la callback passa service.search a _invoke,
               che esegue operation tramite partial e run_sync e ne restituisce il risultato
           codebase_map_graph(paths=[mcp_service.py], hops=1)
             → seleziona gli archi di MapService.search, conservando eventuali irrisolti
           codebase_map_read(mcp_service.py::MapService.search)
             → verifica lo stato dell'indice, chiama retrieval.search e restituisce public_result
           codebase_map_graph(paths=[retrieval.py], hops=1)
             → seleziona gli archi di search e degli helper pertinenti
           codebase_map_read(retrieval.py::{search,_read,index_name,public_result})
             → verifica path retrieval.sqlite, apertura SQLite, query FTS5, ranking e risultato
Decisione: la catena callback → _invoke → MapService.search → retrieval.search è
           ricostruita dalle letture, senza attribuirla a un solo hop del grafo.
           Il confine con SQLite è esplicito; le altre dipendenze lette per capire
           il contesto non entrano automaticamente nel target. Il percorso individuato
           copre ricezione, instradamento, interrogazione e restituzione.
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
Decisione: due target materialmente diversi: lock dell'indice vs processo embedding
Esito:     domanda all'utente: "Lock dell'indice (confinement.py, store_graph.py)
           o processo di encoding (embedding_worker.py)?"
```

## Confine con la Phase 1

La Phase 1 riceve l'elenco e raccoglie il contesto: file completi, caller, test, contratti, documentazione. Queste letture non allargano il perimetro.

Il perimetro è ciò che la review giudica (`conclusion_paths`), non ciò che legge (`read_scope`). Gli strumenti segnalano dipendenze e obblighi: `codebase_map_stale_callers` classifica gli impatti di modifica e validazione sul confronto dei run; `codebase_map_edit_impact` aggiunge le signature di secondo livello con `hops=2`. GREEN orienta gli obblighi, non chiude la lettura: una funzione che mantiene la firma ma cambia il significato del risultato (secondi in millisecondi) può alterare i consumatori oltre il primo caller.

La lettura termina quando le evidenze chiariscono il contratto pertinente oppure quando sono esauriti i collegamenti pertinenti del grafo e le altre piste concrete individuate. Nel secondo caso, eventuali lacune ancora aperte restano dichiarate: l'esaurimento della ricerca non dimostra da solo la completezza della copertura. Un troncamento o una chiamata non risolta non prova che il grafo sia esaurito. In Phase 0 il grafo serve a delimitare il perimetro; la profondità in Phase 1 serve a giudicarlo. Un difetto trovato in un caller fuori perimetro resta un finding con `introduced_by_candidate` quando causato dalla modifica, non un allargamento automatico del target.

## Testo proposto per la Phase 0

Sostituisce il punto 1 della Phase 0 attuale; i passi successivi (diff, estensioni, intento, `00-scope.md`) restano.

```markdown
## Phase 0: Target Resolution

Prerequisite: Codebase Map has already completed the entire project's map.
Use that existing run's indexes; Phase 1 context building does not replace
this prerequisite. If the complete map is unavailable, run Codebase Map first.

1. Convert the request into paths, after `references/candidate-grounding.md`
   has fixed the target kind. Use the run's lexical index, module graph and
   static graph for localization, then verify membership from source. Module
   descriptions and proposals are locating hints, not behavioral premises.
   Until Phase 0c completes, the coordinator reads no Codebase Map analysis
   artifacts, semantic cards or knowledge leads. Phase 0c derives its own leads
   from source. Phase 1c keeps its isolated context and no-map-access rule: its
   scope carries locators, never graph interpretations or module descriptions.
   - Anchors: paths, `path::Name` or bare identifiers, module or component
     names, error text, domain terms. A commit, range or PR is an anchor: its
     files come from `git diff {range} --name-only` or `gh pr diff {number} --name-only`.
   - Resolve each anchor, cheapest first:
     - file, directory, document, changeset: no search; `codebase_map_symbols_at`
       for the symbols a diff touches.
     - whole project: `codebase_map_scope`.
      - module or sub-app: `codebase_map_modules(query=NAME)`; `resolved` gives
        members and `read_scope`, `needs_clarification` asks, `incomplete` gives
        members to confirm. If unknown, list modules without a query and compare
        their responsibilities. If none fits, search lexically.
      - identifier, error, domain term: `codebase_map_search(query)`, one query
        per name group, `limit` 20. Reword a valid empty search once using a
        synonym, translation or already located identifier. Only if that search
         is also empty may enabled embeddings be used. If neither route finds
         hits, keep the anchor unresolved. A missing, stale or corrupt index is a prerequisite
        gap, not an empty search. Rewording counts against the task budget.
      - feature: `codebase_map_graph(paths, hops=1)` on the files of the hits
        (`paths` takes files, not `file::symbol`), keeping the edges of the current
        symbol. A hop is the navigation step, not the stop rule: repeat it from
        the symbols that entered the target under the stop rules below. Cover
        entry to observable result and branches pertinent to the request. A symbol
        enters because it performs a step of that path, with the line that shows
        it; exclude logging and utilities only when incidental to that behavior.
        A missing edge does not close the path: localize dynamic calls, events and
        configuration links with targeted search, then read the relevant
        registration, routing and destination to confirm them. Keep unproven
        links unresolved. Explicit file and changeset targets keep their scope.
   - Confirm with `codebase_map_outline` (symbols, kinds, lines; no imports or
      bodies); `codebase_map_read` only the section that decides membership.
      `AGENTS.md` and docs confirm boundaries. Classify each step as in target,
      an external dependency with an identified boundary, or unresolved.
   - Reduce symbols to files; a directory only when all its pertinent content is
     in target. Plan, specification or document: the paths, symbols and contracts
     it names are the scope; the file itself is the artifact under review.
      Two materially different targets: ask. Anchors are starting points. Stop
      when evidence delimits the requested behavior, or when all relevant graph
      links and other concrete leads have been explored, or at the budget limit.
      Initial task-wide budget: about 6 queries, including graph queries, and
      10 reads in total, with nodes deduplicated. Exhausting the search does not
      prove coverage; truncation and unresolved calls do not prove graph exhaustion.
      If gaps still prevent delimiting the requested behavior, report incomplete
      resolution with the perimeter found, unresolved links and stopping reason.
```

## Verifica

La procedura proposta non è ancora validata. Due livelli, nell'ordine: il primo verifica i contratti degli strumenti, il secondo le decisioni del modello.

**Livello 1, deterministico (pytest, zero token).** Fixture minimali con un `codebase-modules.json`, costruite come in `scripts/tests/test_modules.py`. Le chiamate riprendono gli esempi; le asserzioni riguardano i risultati degli strumenti, non la completezza del perimetro scelto dal modello.

| Esempio | Asserzione |
|---|---|
| 1, 2 | `symbols_at` su un diff di due righe restituisce il simbolo toccato e nessun altro |
| 3 | `search("snapshot")` mette `snapshot.py` al primo posto; `search("retrieval")` trova solo `retrieval.py` |
| 4 | `query("context building")` è `resolved` quando il modulo è dichiarato, con i tre membri attesi |
| 4b | senza dichiarazione: `unknown`; l'elenco senza argomenti contiene `responsibility` di ogni modulo; `search("context building")` trova i tre file per subtoken; dopo la proposta `query` dà `incomplete` con i tre membri |
| 5 | Una catena di quattro funzioni in file distinti richiede tre espansioni successive a un hop dal simbolo corrente; letture mirate confermano i collegamenti. Una callback non risolta resta una chiamata con `resolution` diversa da `resolved`, mai un arco; `paths=["mcp_server.py::codebase_map_search"]` solleva `ValueError` |
| 6 | `search("concorrenza")` è vuota; `search("concurrency lock thread")` trova file di due moduli diversi |

Controllare anche che un risultato troncato esponga il troncamento e che l'esaurimento dei nodi risolti non cancelli le chiamate irrisolte. Riutilizzare le fixture di `tests/test_xray_source_reader.py` per catene, receiver dinamici e troncamenti.

Un fallimento segnala un conflitto fra l'assunzione della spec e il contratto dello strumento: confrontare sorgente e contratto prima di correggere l'assunzione, senza piegare il test all'esempio.

**Livello 2, con modello (esperimento, costa token).** Eseguire i sette prompt su uno snapshot fissato; anche il changeset è fisso. Fissare prima perimetri attesi, budget e criteri: file pertinenti inclusi, file estranei esclusi, collegamenti dimostrati o dichiarati irrisolti, motivo dell'arresto, chiamate e costo effettivi. L'esempio 6 termina con una domanda. Le chiamate illustrate non sono un tetto: vale il budget complessivo del task.

Aggiungere al caso feature tre varianti: percorso di almeno tre hop con una dipendenza accessoria da escludere; collegamento necessario non risolvibile dopo l'esaurimento delle piste, con esito incompleto; budget esaurito prima della copertura, con perimetro parziale e lavoro residuo dichiarati. Eseguire anche la Phase 0 attuale sugli stessi input: il suo esito è una baseline da misurare, non un fallimento presunto. Un'esecuzione per caso su un modello economico e uno forte è uno smoke test; l'affidabilità richiede repliche prima di essere dichiarata.

Controllare nella traccia anche il fallback dei moduli prima della ricerca lessicale, una sola riformulazione per ricerca vuota e nessun embedding dopo hit lessicali. Il passaggio alla Phase 1c deve contenere riferimenti e leads derivati dai sorgenti, senza interpretazioni o conclusioni di Codebase Map.
