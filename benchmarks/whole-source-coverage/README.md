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
3. Sulla run a gruppi eseguire `python -B benchmarks/whole-source-coverage/check_run.py run.jsonl <OUT>/.team-review/coverage.json --root <checkout>`; `--root` è la radice dei percorsi dell'inventario, cioè la checkout. Il controllo fallisce se una cella appena coperta non ha una lettura integrale verificabile nel suo job, o se il job non ha concluso.
4. Confrontare i finding delle due run con i risultati attesi, incluso il difetto tra gruppi.

`check_run.py` lega gli eventi al job con il `job_id` sulla prima riga della dispatch e il `parent_tool_use_id`. I token di un worker arrivano solo nel suo `task_notification`; quelli del coordinatore, una volta per messaggio. Il costo in USD è quello cumulativo dell'ultimo evento `result`; il tempo è misurato dalla shell, perché una sessione con worker in background scrive un `result` per segmento.

## Preparazione: tre richieste

Esiti attesi, dichiarati prima della run:

| Richiesta | Esito atteso |
|---|---|
| «Controlla la sicurezza delle note.» | `resolved`: tutto `app/`, controllo di sicurezza, assunzione scritta in `00-scope.md`, nessuna domanda |
| «Review di sicurezza solo del server, non del client.» | `resolved`: solo `server/`, nessuna cella per `client/` |
| «Rivedi la sicurezza del server e fai una review completa del client.» | `clarify` solo per il client: «completa» può indicare tutte le dimensioni o i reviewer pertinenti su ogni file, con costi molto diversi; la sicurezza di `server/` procede e il rapporto segna aperta la parte sospesa |

Per ogni richiesta si registrano sorgenti e controlli scelti, assunzioni, domande e avanzamento.

## Misure

Run del 2026-11-08. Modello `claude-sonnet-5-5` per mappa e review; reviewer `security-auditor` (10 membri); il rigor richiesto `standard` è stato alzato a `deep` dall'helper per i percorsi sensibili, quindi verifica `all-above-floor` e critic in entrambe le run. Metodo a gruppi: plugin al commit `f227b4941`. Mappa comune: lite, senza indice semantico, 442 s e 2,77 USD.

| Metodo | Semi trovati (4) | Altri reali | Segnalazioni errate | Celle coperte / aperte | Token job di review | Token verifica e critic | USD review | Tempo review |
|---|---|---|---|---|---|---|---|---|
| attuale | 4 | 1 | 0 | – | 197.549 (1 job) | 2.577.572 (19 worker) | 9,48 | 1.991 s |
| a gruppi | 4 | 1 | 0 | 8 / 4 | 671.404 (4 job) | 2.707.009 (21 worker) | 13,42 | 2.817 s |
| a gruppi, aiutante leggero e ondate | 4 | 2 | 0 | 10 / 2 | 240.866 (4 job) | 649.692 (25 worker) | 6,49 | 909 s |

- Entrambe trovano tutti i semi, compreso quello tra gruppi: nel metodo a gruppi lo trova il job del file che valida (`storage.py`), non quello del file chiamante. Il comportamento reale in più è lo stesso.
- Severità: il metodo a gruppi abbassa un seme da High a Medium (voto di Lens 3) e ne lascia uno `contested` (Lens 1 e 2 in disaccordo); il metodo attuale li conferma.
- Le 8 celle coperte hanno tutte una lettura integrale nel job assegnato (`check_run.py`: 8 verificate, nessuna violazione). Le 4 aperte (`client/api.ts`, `client/view.ts`, `config.json`, `server/audit.py`) sono `partial` perché pagina ospite, deployment e politica di audit stanno fuori dal progetto: il job ha usato `partial` per limiti di contesto, non per letture o controlli incompleti.
- Costo: +42% in USD e +41% in tempo. I token dei job di review sono 3,4 volte quelli del job unico, perché ogni job paga circa 120.000 token di contesto fisso; 83.926 token per cella coperta. La verifica costa quasi uguale nelle due run e domina il totale.
- Strumenti della mappa assenti in entrambe le sessioni `claude -p` (ToolSearch non attivo); i coordinatori hanno usato `MapService` via Python.
- Preparazione con tre richieste: non eseguita.

Terza run, stesso giorno, plugin al commit `0ead554c3`: job, lenti 1-3 e critico su `senior-review:isolated-worker`, chiamate a ondate. Mappa nuova sullo stesso commit della fixture, 345 s e 2,61 USD, completa ma non pubblicata («snapshot parser identity changed»), come la precedente leggibile da `MapService`.

| Misura, token equivalenti ai prezzi Sonnet | attuale | a gruppi | a gruppi, leggero e ondate |
|---|---|---|---|
| Coordinatore | 2,48 M, 67 turni | 3,82 M, 103 turni | 2,11 M, 56 turni |
| Job di review | 0,69 M | 1,67 M | 0,70 M |
| Lenti | 2,26 M | 2,88 M | 0,88 M |
| Critico | 0,57 M | 0,50 M | 0,13 M |
| Totale | 6,00 M | 8,87 M | 3,82 M |
| Contesto iniziale di un worker | 121.000 | 111.000 | 18.000 |

- Tutti i semi trovati e confermati: nessuna severità abbassata, nessun `contested`. In più C2 (`auth.py:29`) e un limite mancante sul numero di note per utente (`storage.py:30`), reale: esiste solo il limite per nota.
- Le 10 celle coperte hanno tutte una lettura integrale nel job assegnato (`check_run.py`: 10 verificate, nessuna violazione). Le 2 aperte (`server/routes.py`, `server/storage.py`) restano aperte perché il membro `browser-security-auditor` di job-04 ha dichiarato `incomplete` per i file `client/`, assegnati a job-01: un'etichetta sbagliata, non una lettura mancata.
- Rispetto al metodo a gruppi precedente: −52% in USD, −68% in tempo, −57% in token. Rispetto al metodo attuale: −32% in USD e −54% in tempo, con la copertura per file in più.

Esito delle prime due run: su una fixture che un solo job legge per intero, i gruppi non trovano più difetti e costano di più. Con l'aiutante leggero e le ondate costano meno del metodo attuale. Il vantaggio misurato è la copertura per file verificabile; il risparmio resta da provare su un perimetro che un solo job non riesce a leggere.

## Limiti

- La fixture è piccola: il metodo attuale la legge in un solo job. Il confronto misura la divisione, non il caso in cui un job non basta.
- La lettura integrale si verifica solo per `Read` e `codebase_map_read`; altre letture risultano non verificabili. Il troncamento di righe molto lunghe da parte di `Read` non è rilevato.
- Il metodo attuale non ha celle: per lui «Controlli aperti» non si applica.
- Un solo campione per metodo: nessuna stima di varianza. La terza run usa una mappa nuova, non la stessa delle prime due.
