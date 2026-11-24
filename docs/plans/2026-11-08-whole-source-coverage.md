# Piano: review dell'intero sorgente con copertura esplicita

**Stato:** In parte. La Parte A (celle file × reviewer, job per gruppo, conto della copertura) è nel codice e misurata: `inventory_rows` e il comando `files` di `daodan/core/snapshot.py`, `bind` con `coverage` e `account` in `daodan/core/composition.py`, i campi `read` e `partial` di `daodan/review/contracts/reviewer-result.toml`, i testi della review in `plugins/senior-review/skills/`, i test `CoverageBindTest` e `CoverageAccountTest` di `tests/test_senior_review_composition.py`. Manca una prova della Parte A (task 5b) e tutta la Parte B (task 6 e 7): nulla nel codice.

**Spec:** `docs/specs/2026-11-03-semantic-review-foundation.md`, sezione 4. **Misure:** [`benchmarks/whole-source-coverage`](../../benchmarks/whole-source-coverage/README.md).

## Vincoli

- Script con la sola libreria standard. `coverage` vale solo per shape `branch` e base `content`.
- Difetti seminati e risultati attesi mai su `main` né in questo piano; le run alla cieca girano in un processo nuovo.
- Run con il modello: prima il via del proprietario, un processo alla volta.
- Il registro conserva evidenze di review; sorgente e cache ricostruibile restano della mappa.

## Task aperti

### 5b. Preparazione con tre richieste

Gli esiti attesi sono dichiarati nel README del benchmark («Preparazione: tre richieste»): una richiesta incompleta ma risolvibile dal contesto, una con un limite esplicito, una con un'ambiguità sostanziale e una parte indipendente chiara. Non eseguita.

- [ ] Eseguire le tre richieste e registrare nel README sorgenti e controlli scelti, assunzioni, domande e avanzamento: nessuna conferma inutile, nessun ampliamento automatico, nessun blocco della parte chiara.

### 6. Registro di progetto e riuso (Parte B)

Parte dopo il via del proprietario: sulla fixture del benchmark, che un solo job legge per intero, i gruppi non trovano più difetti; il vantaggio misurato è la copertura per file verificabile. Se il riuso non giustifica la complessità, ci si ferma alla Parte A.

**File:** `daodan/core/composition.py`; `plugins/senior-review/skills/review-preparation/references/composition.md` (procedura in tre righe); test in `tests/test_senior_review_composition.py` (classe nuova `CoverageInheritTest`).

**Interfacce:**

- Riusa `review_experience.locate(project)` e `review_experience.writer_lock(path, boundary)` di `daodan/core/review_experience.py`.
- `account ... --project ROOT --review-id ID --map-run RUN` aggiunge una riga per reviewer e review a `<home>/.daodan/review-experience/coverage.jsonl`: `{"schema": "daodan/review-coverage-row/v1", "reviewer", "body_sha256", "knowledge_selection", "review_id", "map_run", "at", "covered": [{"path", "sha256", "source_review_id", "source_report"}]}`. `covered` può essere vuoto: la review resta registrata. Per un controllo nuovo l'origine è la review corrente e il suo rapporto persistente; per uno riusato l'origine si conserva. Senza un rapporto in un percorso che la review seguente non sovrascrive non si riusa. Nessuna copia del sorgente. Senza home stampa `"coverage ledger unavailable: <motivo>"` ed esce 0.
- `previous(project, reviewers) -> dict[str, dict]`: l'ultima registrazione per reviewer, anche con `covered: []`, senza recuperare celle da registrazioni più vecchie. CLI `composition.py previous --project ROOT --reviewer ID [--reviewer ID]` stampa `{reviewer: {"review_id", "map_run"}}`.
- Bindings: `coverage.inherit = {"project": ROOT, "changes": {map_run: "changes.json"}}`, con `changes.json` da `snapshot.py diff MAP_RUN TARGET --verify --out DIR`, generato nella preparazione corrente sul candidato verificato. Servono run di origine presente, `parent_run` corrispondente, root e target compatibili, `reasons` vuoto e dati di modifiche e dipendenze validi: exit 0 da solo non basta. Un confronto mancante, incompatibile o riferito a un altro candidato impedisce il riuso per quel reviewer e aggiunge una lacuna.

**Regole:**

- Una cella si riusa solo se è nell'ultima registrazione, `sha256`, `body_sha256` e `knowledge_selection` coincidono e il percorso non è modificato né compare in `transitive_importers[].file` di `snapshot.py diff`. `transitive_seeds` deve corrispondere all'unione di file aggiunti, rimossi e modificati; `importers` da solo non basta, perché filtra alcune modifiche. Nessun nuovo calcolo del grafo. Se i dati mancano, niente riuso.
- Una configurazione o un requisito cambiato, con dipendenze che la mappa non rappresenta, impedisce il riuso per il reviewer interessato: nell'incertezza si riesamina.
- Cella riusata: `status: covered`, `job_id: None`, `source_review_id` e `source_report` originali, nota `"inherited from <source_review_id>"`. `account` conserva queste celle; il rapporto distingue controlli nuovi e riusati e rimanda ai finding originali. La registrazione corrente usa il run corrente come base del confronto successivo, senza riscrivere la provenienza.
- Il conteggio locale resta prima della consolidazione, la registrazione persistente dopo il rapporto finale. `account` è idempotente per la stessa coppia review e reviewer.

- [ ] **Test prima:** invariati riusati; file, reviewer o `knowledge_selection` cambiati riesaminati; dipendenze dirette e indirette di file aggiunti, rimossi o modificati riesaminate anche senza cambiamenti ai simboli; configurazione cambiata senza dipendenze note impedisce il riuso; snapshot assente, `parent_run` diverso, `reasons` non vuoto o dati incompleti impediscono il riuso; una review con zero copertura rimane l'ultima; R1 → R2 → R3 conserva l'origine R1; rapporto originario mancante impedisce il riuso; `account` conserva le celle riusate; home assente produce una lacuna.
- [ ] Implementare; poi la procedura in `composition.md`: `previous` → `snapshot.py diff` verificato per ogni `map_run` → `inherit.changes`.

### 7. Misura del riuso

- [ ] Sul branch dei semi, un commit che cambia un file senza semi.
- [ ] Dopo il via del proprietario: sullo stesso commit una review completa e una con riuso, in processi nuovi, stesso modello, reviewer, rigor e materiali del benchmark, entrambe dallo stesso registro precedente. `benchmarks/whole-source-coverage/check_run.py` verifica le letture integrali dei controlli nuovi, la provenienza dei riusati e l'insieme dei job avviati.
- [ ] Nel README: difetti trovati e segnalazioni errate, poi token e tempo totali, separando aggiornamento della mappa, review e verifica dei finding. Un risparmio con perdita di efficacia non supera la prova.
