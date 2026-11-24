# Piano: analisi unificata, una preparazione sola e un job per tutta la catena

**Stato:** In parte. I cinque task (0, 1, 1b, 2, 2b) sono nel codice e hanno la loro prova; restano i punti aperti sotto, quasi tutti misure o verifiche su Modal.

**Obiettivo:** il codice del progetto gira solo nel container, anche nelle review, nei test e nelle misure su Modal; le dipendenze si installano una volta per analisi; statico, inferenza, dinamico e unione girano in un job solo, con la sua tabella.

**Spec:** `docs/specs/2026-11-15-pipeline-di-analisi.md`, «Preparazione» e sezione 7. **Ordine fra i piani e prova da zero:** [pipeline intera](2026-11-20-pipeline-intera.md).

## Che cosa c'è

| Task | Nel codice | Prova e misura |
| --- | --- | --- |
| 0. Nessuna esecuzione sull'host nelle review e nei test | `review-quality-gates` e `investigation-method` di `plugins/senior-review` chiedono il container; senza, la riproduzione è una lacuna con la causa | test statico in `tests/test_senior_review_worker.py`; guardia `MODAL_TASK_ID` in `tests/test_codebase_map_indexers_python_runs.py` |
| 1. Il container nella run della mappa su Modal | `benchmarks/system-map/modal_map.py` lancia la pass come processo figlio con `modal_pipeline.engine_environment()`; `sandbox_run` prende `registries` come allowlist per host; ogni sandbox monta solo la cartella della sua run | `modal_map.py::engine_proof_run`, 5 controlli su 5: [`benchmarks/system-map`](../../benchmarks/system-map/README.md), «Il container nella run della mappa su Modal» |
| 1b. Una preparazione sola per analisi | `daodan/core/node_preparation.py`: due volumi di partenza che il primo ripristino popola e ogni passo clona; si tolgono a fine analisi, anche dopo un errore | `tests/test_codebase_map_shared_node.py` |
| 2. Un job per tutta la catena e la sua tabella | `modal_map.py whole`, `benchmarks/system-map/score.py whole` | `WholeTableTests` in `tests/test_benchmark_system_map_score.py`; prova 0 sui cinque casi, senza modello e con Haiku 5.5: README di `benchmarks/system-map`, «Il mappatore con un modello, sull'intero sistema, alla cieca» |
| 2b. Tre corse sullo stesso progetto | `benchmarks/project-model/modal_runs.py`, `score.py runs` | [`benchmarks/project-model`](../../benchmarks/project-model/README.md), «Tre corse sullo stesso progetto» |

## Aperto

### Task 1

- I test di `benchmarks/project-model/test_modal_pipeline.py` non risultano eseguiti (la prova su fixture sì).
- L'allowlist per host è una funzione Beta di Modal e non filtra il traffico che non è TLS sulla porta 443: gli archivi apt `http://` passano per indirizzo, su ogni porta.
- Con servizi accanto la preparazione non è confinata: la rete resta aperta e il risultato lo dice (lacuna `network_open`).
- Le liste di host di ogni strumento non sono mai state osservate su Modal: un host mancante fa fallire una preparazione che prima passava. La modifica di `sandbox_run` vale per ogni giro su Modal, non solo per la mappa.
- Non verificato: se una VM Sandbox accetta il montaggio con `sub_path` in sola lettura e l'allowlist per host; se le liste per host e per indirizzo valgono insieme; se un CDN risolve nella sandbox come nella funzione.
- Il controllo 5 della prova conta le sandbox vive dell'app condivisa: nessun altro giro deve girare in quel momento.
- Una pass scaduta riceve un'interruzione e poi un kill: le sandbox di un processo ucciso restano fino al loro limite, e uno stadio che non passa da uv può non fare in tempo a pulire.

### Task 1b

- Su Modal ogni run ripristina per sé: `sandbox_run` non condivide i volumi. Il guadagno del ripristino condiviso non è misurato: serve un motore Docker vero in una VM Sandbox.
- `test_a_step_without_a_container_is_a_gap_with_its_cause_and_starts_nothing` è scritto; non risulta eseguito.

### Task 2

- La prova 0 con Qwen e con Opus non è fatta. Le soglie le deve confermare il proprietario.
- Mancano le colonne delle schede dei percorsi con il modello e della ricerca: arrivano con i task 9 e 10 del [piano della ricerca](2026-11-20-ricerca-e-pacchetto-di-review.md).
- `entries_case` e `links_case` di `modal_map.py`, senza container, restano: si tolgono dopo la prova completa.

### Task 2b

- Una sola corsa per tipo, sulla fixture `mix-poly-firebase`.
- CPU, picco di memoria e spazio temporaneo non sono in nessun evento: non misurati.
- Dopo un modulo cambiato riparte tutto (il 95% del tempo da zero): la pre-mappa si rifà intera e ripartono tutti gli indicizzatori. Le regole di riuso della sezione 7.3 della spec della pipeline entrano dopo questo numero: [grafo dall'indice](2026-11-14-grafo-dall-indice.md), «Aggiornamento incrementale».
