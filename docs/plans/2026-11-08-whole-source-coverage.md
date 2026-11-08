# Piano: review dell'intero sorgente con copertura esplicita

Eseguire i task nell'ordine e segnare solo i passi verificati. La Parte A produce una review completa; la Parte B resta subordinata alle misure e al via dell'utente.

**Obiettivo:** dalla richiesta, anche incompleta, e dal contesto del progetto la preparazione ricava i sorgenti da esaminare e i controlli pertinenti. Dichiara i due perimetri e procede; chiede chiarimenti solo per alternative che cambiano sostanzialmente correttezza, ampiezza o costo, proseguendo sulle parti indipendenti già chiare. La review `branch` con base `content` divide i file in gruppi e restituisce problemi trovati, controlli conclusi e lavoro rimasto aperto. Nei dati, una `cella` è la coppia file × reviewer e un `job` è l'incarico su un gruppo.

**Funzionamento:** Codebase Map espone l'inventario (`snapshot.py files`). `composition.py bind` lo limita al perimetro già risolto e crea i gruppi; ogni job scrive un unico risultato JSON secondo `reviewer-result`. `composition.py account` combina letture e completamento dei controlli nel registro della review. La preparazione si orienta con la mappa; le letture integrali spettano ai job.

**Tecnologie:** Python 3 solo libreria standard, `unittest` eseguito con pytest, Markdown.

**Spec:** `docs/specs/2026-11-07-whole-source-coverage.md`

## Vincoli

- Script solo libreria standard, come i loro docstring dichiarano.
- Senza `coverage` nei bindings l'uscita di `bind` resta identica a oggi: i test esistenti di `tests/test_senior_review_composition.py` passano senza modifiche.
- `coverage` vale solo per shape `branch` e base `content`; le altre combinazioni lo rifiutano. Il limite in byte dimensiona i gruppi, non garantisce un costo in token; il parallelismo resta dell'host.
- Nessun bump di versione di plugin o marketplace.
- Documenti in italiano al presente, senza etichette storiche; riferimenti e brief in inglese, come sono.
- Difetti seminati e oracolo mai su `main`, mai in `MEMORY.md`, mai in questo piano; le run alla cieca girano in un processo `claude -p` nuovo.
- Run con il modello: chiedere prima all'utente, un processo alla volta, memoria libera controllata.
- Test: `python -B -m pytest -q <file>`. I commit indicati nei task si eseguono solo su richiesta dell'utente, sul branch di lavoro autorizzato; formato `area: cosa`, in italiano, attribuzioni solo effettive. Worktree sotto `.jcode/local/worktrees/`.

## Controlli essenziali

1. Percorsi in `read` con backslash o assoluti (host Windows): devono contare come il percorso relativo. Test in Task 3.
2. Risultato assente, non valido, fallito o con membri incompleti: gruppo aperto con motivo, anche se tutti i file risultano letti. Test in Task 3.
3. Perimetro di directory rispettato; file richiesti assenti dalla mappa visibili come aperti; file inventariato ma assente su disco blocca `bind` e richiede aggiornamento. Test in Task 2.
4. Configurazioni e linguaggi sconosciuti non vengono esclusi automaticamente. Reviewer con tutte le celle realmente `not-applicable`: nessun job, celle riportate. Test in Task 2.
5. Directory e file assegnati ad altri job non coprono nulla. Il benchmark distingue lettura integrale, parziale e riuso. Test in Task 3 e Task 5.

---

## Parte A: copertura di una review (spec, interventi 1-5)

### Task 1: inventario della snapshot

**Files:**
- Modify: `plugins/codebase-map/skills/map/scripts/snapshot.py` (sottocomando accanto a `scope`, :3447)
- Test: `tests/test_codebase_map_files.py` (nuovo)

**Interfaces:**
- Produces: `inventory_rows(manifest: Path) -> list[dict]`, righe `{"path": str, "sha256": str, "size": int, "lines": int | None, "language": str | None}` ordinate per percorso, da `file_headers` (`raw_hash`, `size`, `lines`, `language`). CLI `python snapshot.py files MANIFEST --out FILES.json` scrive `{"schema": "codebase-map/files/v1", "manifest": "<posix>", "files": [...]}` e stampa `{"files": n}`.

- [ ] **Step 1: test che fallisce** — `test_files_lists_every_snapshot_file`: albero temporaneo con `pkg/a.py` (`"def f():\n    return 1\n"`), `web/b.ts` (`"export const x = 1;\n"`), `README.md`; manifest con `snapshot.write_snapshot` come in `tests/test_codebase_map_stale_callers.py`; `snapshot.main(["files", str(manifest), "--out", str(dest)])`. Assert: percorsi `["README.md", "pkg/a.py", "web/b.ts"]`; `sha256 == hashlib.sha256(bytes).hexdigest()` e `size == len(bytes)` per ogni file; `language` `"python"` per `a.py`, `"typescript"` per `b.ts`.
- [ ] **Step 2:** `python -B -m pytest -q tests/test_codebase_map_files.py` → FAIL (`invalid choice: 'files'`).
- [ ] **Step 3:** implementa `inventory_rows` e `cmd_files` con `open_snapshot` e `file_headers`; percorso `manifest` posix.
- [ ] **Step 4:** stesso comando → PASS.
- [ ] **Step 5:** commit `codebase-map: snapshot.py files elenca l'inventario della snapshot con hash, dimensione e linguaggio`.

### Task 2: `bind` crea celle e job per gruppo

**Files:**
- Modify: `plugins/senior-review/skills/review-preparation/scripts/composition.py` (`bind`, nuovi helper, docstring)
- Test: `tests/test_senior_review_composition.py` (classe nuova `CoverageBindTest`)

**Interfaces:**
- Consumes: `FILES.json` di Task 1 e `grounding.conclusion_paths` del roster, già risolti dalla richiesta. La preparazione passa al roster solo l'inventario del perimetro, evitando che `compute` lo allarghi. `bind` richiede la lista esplicita e non interpreta una lista vuota come «tutto il progetto».
- Bindings: `"coverage": {"files": "FILES.json", "root": ".", "budget": 120000}`; `root` predefinito `"."`, `budget` predefinito `GROUP_BYTES = 120_000` (costante in testa, tarata dal Task 5).
- Produces in `PREPARED-REVIEW.json`: `coverage = {"schema": "daodan/review-coverage/v1", "files": str, "root": str, "budget": int, "reviewers": {identity: body_sha256}, "cells": [{"path", "reviewer", "sha256": str | None, "status": "open" | "not-applicable", "job_id": str | None, "note": str}]}`; `root` è assoluta. Ogni job di gruppo ha `"paths": [str]`, `"bytes": int` e `output_path` con estensione `.json`: è l'unico risultato del job. Conserva lo `scope_id` originale; `job_id` e `paths` distinguono già i gruppi.
- Helper piccoli per applicabilità e raggruppamento; riusare `leaf_roles`, `LANGUAGE_ROLE`, `SIGNAL_ROLE` e i segnali Tauri, senza un secondo catalogo. `pack(rows, budget)` resta puro.

Regole:
- Perimetro: una cella per file richiesto e identità pianificata sullo scope predefinito, inclusi specialisti esplicitamente richiesti. Una riga assente dall'inventario resta `open`, `sha256: null`, `job_id: null`, nota `"missing from map inventory"`; non si inventano metadati. Nessuna cella per file fuori perimetro.
- Applicabilità: una composizione con un membro non di stack resta applicabile. TypeScript e React conservano file JavaScript/TypeScript; Tauri conserva percorsi/API riconosciuti dai segnali esistenti. Prima di escludere, conservare sempre file con linguaggio sconosciuto, configurazioni (JSON, TOML, YAML, INI, CFG, lockfile e quelle indicate nei materiali preparati) e file oggetto di obblighi espliciti. Solo negli altri casi si assegna `not-applicable`, con motivo. Il testo si legge solo per verificare Tauri, una volta per file e solo quando necessario.
- `pack`: ordine di percorso; un gruppo nuovo quando il file seguente supera il limite e il gruppo non è vuoto. Limite strettamente positivo, nessun gruppo vuoto.
- `bind`: ogni job sullo scope predefinito diventa un job per gruppo delle sue celle aperte e inventariate; senza file da assegnare sparisce, le celle restano nel conteggio. I job su altri scope restano invariati e mantengono i controlli esistenti sulle consegne.
- Ogni file inventariato nel perimetro deve esistere sotto `root`, altrimenti `ValueError("inventory file missing on disk: <path>; refresh the map")`. Riutilizzare il controllo di freschezza della preparazione; l'esistenza da sola non prova che il contenuto sia attuale.

Fixture comune: `app/a.py` (python, 50000 byte), `app/b.py` (python, 50000), `docs/d.md` (None, 1000), `web/c.ts` (typescript, 30000), scritti su disco in una root temporanea con quelle dimensioni.

- [ ] **Step 1: test che falliscono**
  - `test_every_file_has_one_cell_per_reviewer`: roster `code-auditor`, `typescript-auditor` → 8 celle, coppie (path, reviewer) uniche.
  - `test_open_cells_belong_to_exactly_one_job`: ogni cella aperta e inventariata ha un solo job assegnato; `scope_id` e obblighi restano quelli originali. Le celle mancanti dalla mappa restano aperte senza job.
  - `test_groups_respect_budget`: budget 60000, gruppi di `code-auditor` `[["app/a.py"], ["app/b.py", "docs/d.md"], ["web/c.ts"]]`; budget 40000, `app/a.py` da solo con `bytes == 50000`.
  - `test_typescript_reviewer_skips_known_other_languages`: `web/c.ts` e `docs/d.md` (linguaggio sconosciuto) aperte; solo i due Python `not-applicable`.
  - `test_configuration_and_explicit_obligations_stay_open`: `tsconfig.json`, `package.json`, configurazione indicata nei materiali e un file con obbligo esplicito non vengono esclusi.
  - `test_directory_scope_and_missing_map_paths`: l'inventario dell'intero progetto non allarga `conclusion_paths`; un file richiesto assente dalla mappa resta aperto con motivo. Lista vuota: nessun gruppo.
  - `test_tauri_needs_path_or_api`: roster `tauri-auditor`; `src-tauri/src/main.rs` aperta, `web/api.ts` con `import { invoke } from "@tauri-apps/api/core";` aperta, `web/view.ts` senza Tauri `not-applicable`.
  - `test_reviewer_with_no_open_cell_has_no_job`: `typescript-auditor` su soli file Python → nessun job suo, celle `not-applicable`.
  - `test_missing_inventory_file_fails`: un path di `FILES.json` assente su disco → `ValueError` con `refresh the map`.
  - `test_invalid_basis_or_shape_rejects_coverage`: shape `light` oppure base diversa da `content` con `coverage` → `ValueError`.
  - `test_group_output_is_single_json_result`: percorso `.json` univoco per job; senza `coverage`, output invariato. Budget nullo o negativo rifiutato.
- [ ] **Step 2:** `python -B -m pytest -q tests/test_senior_review_composition.py` → i nuovi FAIL, i vecchi PASS.
- [ ] **Step 3:** implementa helper e ramo `coverage` di `bind`.
- [ ] **Step 4:** stesso comando → tutto PASS.
- [ ] **Step 5:** commit `senior-review: bind divide il sorgente intero in celle file × reviewer e in job per gruppo sotto un budget`.

### Task 3: `account` deriva gli stati

**Files:**
- Modify: `plugins/senior-review/skills/review-preparation/scripts/composition.py` (funzione e sottocomando `account`, docstring)
- Test: `tests/test_senior_review_composition.py` (classe nuova `CoverageAccountTest`)

**Interfaces:**
- Consumes: `coverage` di Task 2 e il JSON in `job["output_path"]`: contratto `reviewer-result` esistente, comprensivo dei legami al job e di `status`, `member_results`, `read: [str]`, `partial: {str: str}`. Nessun file `.coverage.json` accanto al risultato e nessuna seconda copia di questi campi.
- Produces: `account(prepared: dict, deliveries: dict[str, dict | None], root: Path) -> dict` (chiave `job_id`; `None` = risultato assente o illeggibile) → `{"schema": "daodan/review-coverage/v1", "cells": [...], "summary": {reviewer: {"covered": int, "open": int, "not-applicable": int}}}`. CLI `python composition.py account --prepared PREPARED-REVIEW.json --out COVERAGE.json`: usa `coverage.root`, scrive il registro e stampa `{"summary": ..., "open_total": n, "open": <prime 20 celle aperte>}`; esce 0 anche con celle aperte. Questo indica che il conteggio è riuscito, non che la review sia completa.

Regole: normalizzare i percorsi rispetto a `coverage.root` (backslash, assoluti interni alla root, `./`); contano solo file assegnati a quel job, mai directory o percorsi esterni. Validare tipi dei campi e corrispondenza con job, candidato, reviewer, membri, scope e digest preparati, riusando il contratto di consegna. `covered` richiede risultato valido, `status: delivered`, una riga completa e consegnata per ogni membro assegnato, file in `read` e non in `partial`. Un risultato fallito o con membri incompleti mantiene aperto tutto il gruppo, anche se letto: scelta conservativa senza introdurre esiti per membro e file. Le note distinguono risultato mancante/non valido, controllo incompleto, motivo di `partial` e `"not read"`. Le celle non assegnate e `not-applicable` restano invariate.

- [ ] **Step 1: test che falliscono**
  - `test_read_files_with_completed_checks_are_covered`
  - `test_read_but_failed_or_incomplete_result_stays_open`: fallimento del job, membro assente, fallito o incompleto mantengono aperto il gruppo.
  - `test_foreign_or_malformed_result_stays_open`: binding diverso, tipi errati di `read`/`partial` o JSON non valido non chiudono celle e producono un motivo.
  - `test_partial_stays_open_with_reason`
  - `test_missing_delivery_leaves_cells_open`: nota `"no result file"`.
  - `test_unassigned_and_directory_paths_do_not_count`: `read` con `"web/"` e un path di un altro job.
  - `test_windows_and_absolute_paths_normalize`: `read` con `"app\\a.py"` e `str(root / "app/b.py")` → entrambe `covered`.
  - `test_summary_counts`
  - `test_account_cli_uses_prepared_root`: invocazione da directory diversa → stessi conteggi; risultato mancante/non valido → celle aperte con motivo, exit 0.
- [ ] **Step 2:** `python -B -m pytest -q tests/test_senior_review_composition.py` → i nuovi FAIL.
- [ ] **Step 3:** implementa `account` e il sottocomando.
- [ ] **Step 4:** stesso comando → PASS.
- [ ] **Step 5:** commit `senior-review: account combina letture ed esiti dei controlli`.

### Task 4: testi della review

**Files (Modify):**
- `plugins/senior-review/skills/review-quality-gates/references/reviewer-common.md`, «Deliver once»: con `paths` il job conclude su quei file e legge altro quanto serve; salva il solo risultato JSON in `job.output_path`, con i campi esistenti e `read`/`partial`. `partial` indica anche controlli incompleti dopo una lettura integrale; mantenere coerenti `status`, `member_results` e motivi. Allineare la consegna al formato JSON senza introdurre un rapporto duplicato.
- `plugins/senior-review/contracts/reviewer-result.toml`: campi `read` (array di stringhe) e `partial` (oggetto), obbligatori solo per job con `paths`; documentare che non sostituiscono gli esiti già presenti.
- `plugins/senior-review/skills/review-preparation/references/composition.md`: `coverage` solo per `branch/content`; inventario limitato al perimetro prima di `compute`, `FILES.json` dal run legato, root e limite. Descrivere unico risultato JSON, stato dei file mancanti e `account` dopo la barriera di consegna, prima della consolidazione, con uscita `.team-review/coverage.json`.
- `plugins/senior-review/skills/review-preparation/references/team-review.md`, Phase 0 e Phase 1: ricavare dalla richiesta e dai riscontri del progetto sia i sorgenti sia i controlli, rispettando i limiti espliciti. Dichiarare sinteticamente scelta e assunzioni nei documenti già previsti (`00-scope.md`, `02-selection.md`), senza nuovi campi o passaggi di approvazione. Allineare l'esito `clarify`: una normale ambiguità risolta dal contesto non blocca; se resta una scelta sostanziale, porre una domanda mirata e sospendere solo la parte che dipende dalla risposta. Proseguire sulle parti indipendenti già chiare, senza presentare l'intera review come completa. Non ampliare a tutto il progetto o a tutti i reviewer per prudenza. Su base `content` orientarsi con moduli, outline e ricerca della mappa; ogni job legge i propri file.
- `plugins/senior-review/skills/review-preparation/references/candidate-grounding.md`, «Live source»: per `branch/content` la lettura integrale avviene nei job, non anche nella preparazione; restano verifica di freschezza, requisiti e perimetro. Gli altri tipi di review mantengono le regole attuali.
- `plugins/senior-review/skills/review-method/references/team-review.md`: il job copre l'intero scope o i suoi `paths`; sostituire nel template l'obbligo incondizionato «Review the whole scope» con il perimetro assegnato. Phase 3 accetta il risultato JSON da `job.output_path` e verifica esiti e membri come per le altre consegne.
- `plugins/senior-review/skills/review-consolidation/references/team-review.md`: leggere finding e lacune dall'unico risultato di ciascun job; sezione copertura con riepilogo per reviewer, prime 20 celle aperte e rimando a `.team-review/coverage.json`. `covered` non significa privo di difetti.
- `plugins/senior-review/skills/review-quality-gates/references/panel-and-critic-prompts.md` §3, «## Examined coverage»: con celle, il riepilogo stampato da `account`.
- `plugins/senior-review/README.md` :5 e :27: «sull'intero perimetro», diviso in gruppi sotto un budget quando la base è `content`.

- [ ] **Step 1:** applica le modifiche.
- [ ] **Step 2:** `python -B -m pytest -q tests/test_senior_review_composition.py tests/test_senior_review_roster.py` → PASS.
- [ ] **Step 3:** `rg -n 'whole scope|intero perimetro|Live source|read every|Read every|clarify|without an answer' plugins/senior-review` → nessuna istruzione impone una doppia lettura integrale per `branch/content`, allarga un gruppo all'intero perimetro o blocca le parti indipendenti per una richiesta ambigua. Controllare il percorso preparazione → risultato JSON → barriera → `account` → rapporto, senza file di consegna duplicati.
- [ ] **Step 4:** commit `senior-review: Phase 1, brief, consegna e rapporto del sorgente intero diviso in celle`.

### Task 5: benchmark

**Files (Create):**
- `benchmarks/whole-source-coverage/README.md`: spec provata; revisioni del plugin e della fixture, limite, reviewer, modello, rigor e materiali; confronto metodo attuale/metodo a gruppi. Misurare difetti trovati, segnalazioni errate, controlli aperti, token e tempo totali, distinguendo mappa, review e verifica dei finding; token per cella come dato secondario. Dichiarare limiti e misure mancanti, senza anticipare risparmi.
- Nello stesso benchmark, provare la preparazione con tre richieste: incompleta ma risolvibile dal contesto; con un limite esplicito; con ambiguità sostanziale non risolvibile e una parte indipendente chiara. Dichiarare prima gli esiti attesi e registrare sorgenti scelti, controlli scelti, assunzioni, domande e avanzamento: niente conferme inutili, ampliamenti automatici o blocco totale della parte chiara. Bastano i prompt e i risultati nel README, senza un nuovo sistema di valutazione.
- `benchmarks/whole-source-coverage/app/`: una decina di file Python e TypeScript eseguibili senza dipendere dal repository; nomi e commenti neutri. Prevedere un collegamento tra file che il limite scelto assegna a gruppi diversi; almeno un difetto seminato deve attraversarlo.
- `benchmarks/whole-source-coverage/test_fixture.py`: senza token; snapshot di `app/`, `snapshot.py files`, `bind` con il budget del README → almeno tre gruppi per reviewer di una classe di sicurezza (`security-auditor`).
- `benchmarks/whole-source-coverage/check_run.py`: dagli eventi `stream-json` e da `.team-review/coverage.json`, per ogni cella appena coperta verificare risposte di lettura riuscite che coprono tutto il file, anche unendo intervalli; una chiamata, una ricerca o un risultato troncato non bastano. Legare gli eventi al job tramite `job_id` nel prompt e `parent_tool_use_id`; supportare i formati effettivamente osservati di `Read` e `codebase_map_read`, segnalando quelli non verificabili. Controllare anche gli esiti del risultato. In Parte B distinguere celle riusate (provenienza richiesta, nessuna nuova lettura attesa) e riesaminate. Estrarre token per job e totali senza sommare due volte aggregati e sottochiamate; tempi dall'intero percorso registrato.

- [ ] **Step 1:** scrivi `app/`, `test_fixture.py`, `check_run.py` e prove del verificatore (lettura integrale, intervalli, troncamento, risultato fallito, provenienza ereditata, token aggregati); `python -B -m pytest -q benchmarks/whole-source-coverage` → PASS; commit sul branch autorizzato solo se richiesto.
- [ ] **Step 2:** semina i difetti di una classe su un branch locale di fixture e scrivi l'oracolo solo su un secondo branch; nessuno dei due si unisce a `main`.
- [ ] **Step 3: gate** — chiedi all'utente prima della run (costo, memoria, un processo).
- [ ] **Step 4:** worktree staccato del branch dei semi sotto `.jcode/local/worktrees/`; mappa completa con `/codebase-map:map` in un processo a parte. Sullo stesso commit eseguire separatamente il metodo attuale (revisione del plugin registrata prima dell'intervento) e il metodo a gruppi, con stesso modello, reviewer, rigor e materiali; ciascuna review in un processo nuovo: `claude -p "<review di sicurezza dell'intero sorgente>" --output-format stream-json --verbose > run.jsonl`. Conservare gli output in directory distinte; se il metodo attuale non termina, registrare limite ed esito senza attribuirgli un costo completo.
- [ ] **Step 5:** sulla run a gruppi, `python -B benchmarks/whole-source-coverage/check_run.py run.jsonl <worktree>/.team-review/coverage.json` → nessuna cella appena coperta senza lettura integrale verificabile e controlli conclusi. Per entrambe le run confrontare i finding con l'oracolo, incluso il difetto tra gruppi; scrivere misure nel README e valutare insieme efficacia e costo. Commit solo se richiesto.

---

## Parte B: riuso tra review (dopo il benchmark)

Parte dopo i risultati del Task 5 nel README e il via dell'utente. Se il vantaggio non giustifica la complessità, ci si ferma alla Parte A. Il registro conserva evidenze di review, mentre sorgente e cache ricostruibile restano della mappa.

### Task 6: registro di progetto e riuso

**Files:**
- Modify: `plugins/senior-review/skills/review-preparation/scripts/composition.py`; `plugins/senior-review/skills/review-preparation/references/composition.md` (procedura in tre righe)
- Test: `tests/test_senior_review_composition.py` (classe nuova `CoverageInheritTest`)

**Interfaces:**
- Riuso: `review_experience.locate(project)` e `review_experience.writer_lock(path, boundary)` da `skills/review-consolidation/scripts/` (import con `sys.path` dalla cartella sorella).
- `account ... --project ROOT --review-id ID --map-run RUN`: aggiunge una riga per reviewer e review a `<home>/.daodan/review-experience/coverage.jsonl`: `{"schema": "daodan/review-coverage-row/v1", "reviewer", "body_sha256", "knowledge_selection", "review_id", "map_run", "at", "covered": [{"path", "sha256", "source_review_id", "source_report"}]}`. `covered` può essere vuoto: la review resta registrata. Per un controllo nuovo, l'origine è la review corrente e il suo rapporto persistente; per uno riusato, preservare l'origine. Il rapporto deve essere conservato in un percorso non sovrascritto dalla review seguente; senza riferimento disponibile non si riusa. Nessuna copia del sorgente. Senza home stampa `"coverage ledger unavailable: <motivo>"` ed esce 0.
- `previous(project: Path, reviewers: list[str]) -> dict[str, dict]`: restituisce l'ultima registrazione per reviewer, anche con `covered: []`, senza recuperare celle da registrazioni più vecchie. CLI `python composition.py previous --project ROOT --reviewer ID [--reviewer ID]` stampa `{reviewer: {"review_id", "map_run"}}`.
- Bindings: `coverage.inherit = {"project": ROOT, "changes": {map_run: "changes.json"}}`, con `changes.json` da `snapshot.py diff MAP_RUN TARGET --verify --out DIR`, generato nella preparazione corrente sul candidato verificato. Richiedere run di origine presente, `parent_run` corrispondente, root/target compatibili, `reasons` vuoto e dati di modifiche/dipendenze validi. Exit 0 da solo non basta. Un confronto mancante, incompatibile o riferito ad altro candidato impedisce il riuso per quel reviewer e aggiunge una lacuna.
- Una cella si riusa solo se presente nell'ultima registrazione, `sha256`, `body_sha256` e `knowledge_selection` coincidono e il path non è modificato né compare in `transitive_importers[].file`. Verificare che `transitive_seeds` corrisponda all'unione di file aggiunti, rimossi e modificati; non usare il solo `importers`, che filtra alcune modifiche. Questi dati esistono già in `snapshot.py diff`: nessun nuovo calcolo del grafo. Se mancano, niente riuso. Una configurazione o requisito cambiato con dipendenze non rappresentate nella mappa impedisce il riuso per il reviewer interessato; nell'incertezza si riesamina.
- Cella riusata: `status: covered`, `job_id: None`, `source_review_id`, `source_report` originali e nota `"inherited from <source_review_id>"`. `account` conserva queste celle; il rapporto distingue controlli nuovi e riusati e rimanda ai finding originali. La registrazione corrente usa il run corrente come base del confronto successivo, senza riscrivere la provenienza del controllo.

- [ ] **Step 1: test che falliscono** — invariati riusati; file, reviewer o `knowledge_selection` cambiati riesaminati; dipendenze dirette e indirette di file aggiunti/rimossi/modificati riesaminate anche senza cambiamenti ai simboli; configurazione cambiata senza dipendenze note impedisce riuso; snapshot assente, `parent_run` diverso, `reasons` non vuoto o dati incompleti impediscono riuso; review con zero copertura rimane l'ultima; R1 → R2 → R3 conserva origine R1; rapporto originario mancante impedisce riuso; `account` conserva celle riusate e registra solo celle coperte nell'elenco; home assente produce lacuna.
- [ ] **Step 2:** `python -B -m pytest -q tests/test_senior_review_composition.py` → i nuovi FAIL.
- [ ] **Step 3:** implementa, poi la procedura in `composition.md`: `previous` → `snapshot.py diff` verificato per ogni `map_run` → `inherit.changes`. Il coordinatore conserva il rapporto finale prima di scrivere il registro di progetto: il conteggio locale resta prima della consolidazione, la registrazione persistente dopo il rapporto. `account` resta idempotente per la stessa coppia review/reviewer e non aggiunge duplicati.
- [ ] **Step 4:** stesso comando → PASS.
- [ ] **Step 5:** commit `senior-review: riusa i controlli con provenienza e dipendenze valide`.

### Task 7: misura del riuso

- [ ] **Step 1:** sul branch dei semi un commit che cambia un file senza semi.
- [ ] **Step 2: gate** — chiedi all'utente prima della run.
- [ ] **Step 3:** sullo stesso nuovo commit eseguire una review completa e una con riuso, in processi nuovi e con le stesse condizioni del Task 5; entrambe partono dallo stesso registro precedente, senza contaminarsi. `check_run.py` verifica letture integrali dei controlli nuovi, provenienza dei riusati e insieme dei job avviati: file cambiato, dipendenti e controlli rimasti aperti, più eventuali invalidazioni dichiarate.
- [ ] **Step 4:** confrontare difetti trovati e segnalazioni errate, quindi token e tempo totali; separare aggiornamento mappa, review e verifica dei finding. Riportare nel README il rapporto completo/riuso sullo stesso commit; un risparmio con perdita di efficacia non supera la prova. Commit solo se richiesto.
