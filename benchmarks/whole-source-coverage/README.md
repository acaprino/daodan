# Benchmark: review dell'intero sorgente divisa in gruppi

Prova la spec [`docs/specs/2026-11-07-whole-source-coverage.md`](../../docs/specs/2026-11-07-whole-source-coverage.md): la review `branch` con base `content` divide i file in gruppi sotto un budget, conta i controlli conclusi e mostra quelli aperti con il motivo.

## Parametri

| Parametro | Valore |
|---|---|
| `budget` | 4000 byte |
| reviewer | `senior-review:security-auditor` |
| rigor | `standard` |
| modello | da registrare alla run, uguale per le due review |
| materiali | mappa completa del target sullo stesso commit, nessuna conoscenza aggiuntiva |
| metodo attuale | plugin al commit `42a63a9ac`, prima dell'intervento |
| metodo a gruppi | plugin al commit del branch `whole-source-coverage`, da registrare alla run |
| fixture | `app/` a questo commit; semi e risultati attesi fuori da `main` |

## Fixture

`app/` è un piccolo servizio di note: server Python (token firmati, note per utente su disco, handler HTTP, pagina HTML, registro di audit) e client TypeScript (sessione, API, vista), 12 file per circa 13 KB. Con il budget indicato `server/handlers.py` cade in un gruppo diverso da `server/storage.py` e `server/auth.py`, che importa.

I difetti seminati appartengono a una sola classe, la sicurezza, e almeno uno attraversa uno di questi collegamenti. Semi e risultati attesi stanno su due branch locali distinti, che non si uniscono a `main`.

## Prove senza modello

`python -B -m pytest -q benchmarks/whole-source-coverage`

- `test_fixture.py`: snapshot di `app/`, `snapshot.py files`, `bind` con il budget indicato. Richiede almeno tre gruppi per `security-auditor`, ogni gruppo entro il budget o di un solo file, e i file collegati in gruppi diversi.
- `test_check_run.py`: il verificatore su trascrizioni sintetiche. Copre lettura integrale, intervalli uniti, risultato troncato o fallito, provenienza di una cella riusata e token contati una volta.

## Run con il modello

Ogni run richiede prima il via dell'utente, un processo alla volta e la memoria libera controllata.

1. Creare un worktree staccato del branch dei semi sotto `.jcode/local/worktrees/` e fare la mappa completa con `/codebase-map:map` in un processo a parte.
2. Sullo stesso commit eseguire il metodo attuale e il metodo a gruppi, ciascuno in un processo nuovo: `claude -p "<richiesta>" --output-format stream-json --verbose > run.jsonl`. La stessa richiesta indica il budget («gruppi da 4000 byte»): il metodo a gruppi lo passa a `coverage.budget`, il metodo attuale non ha gruppi. Conservare gli output in directory distinte.
3. Sulla run a gruppi eseguire `python -B benchmarks/whole-source-coverage/check_run.py run.jsonl <worktree>/.team-review/coverage.json`. Il controllo fallisce se una cella appena coperta non ha una lettura integrale verificabile nel suo job, o se il job non ha concluso.
4. Confrontare i finding delle due run con i risultati attesi, incluso il difetto tra gruppi.

`check_run.py` lega gli eventi al job con il `job_id` della dispatch e il `parent_tool_use_id`. Conta i token una volta per messaggio, separando coordinatore, job della review e altri worker (verifica dei finding, critic); l'aggregato dell'evento finale resta a parte.

## Preparazione: tre richieste

Esiti attesi, dichiarati prima della run:

| Richiesta | Esito atteso |
|---|---|
| «Controlla la sicurezza delle note.» | `resolved`: tutto `app/`, controllo di sicurezza, assunzione scritta in `00-scope.md`, nessuna domanda |
| «Review di sicurezza solo del server, non del client.» | `resolved`: solo `server/`, nessuna cella per `client/` |
| «Rivedi la sicurezza del server e fai una review completa del client.» | `clarify` solo per il client: «completa» può indicare tutte le dimensioni o i reviewer pertinenti su ogni file, con costi molto diversi; la sicurezza di `server/` procede e il rapporto segna aperta la parte sospesa |

Per ogni richiesta si registrano sorgenti e controlli scelti, assunzioni, domande e avanzamento.

## Misure

Non ancora misurato.

| Metodo | Difetti trovati | Segnalazioni errate | Controlli aperti | Token mappa | Token review | Token verifica | Tempo |
|---|---|---|---|---|---|---|---|
| attuale | – | – | – | – | – | – | – |
| a gruppi | – | – | – | – | – | – | – |

Il dato secondario è il numero di token per cella coperta.

## Limiti

- La fixture è piccola: il metodo attuale la legge in un solo job. Il confronto misura la divisione, non il caso in cui un job non basta.
- La lettura integrale si verifica solo per `Read` e `codebase_map_read`; altre letture risultano non verificabili.
- Un solo campione per metodo: nessuna stima di varianza.
