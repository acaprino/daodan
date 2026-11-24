# Run di lavoro: la mappa segue il codice

**Stato:** In uso. `snapshot.refresh_working` (`daodan/core/snapshot.py`, comando `snapshot.py refresh`), hook `PostToolUse` in `plugins/codebase-map/hooks/hooks.json` (`daodan mcp --hook`), riga in `plugins/codebase-map/skills/map/references/tools-guide.md`. Prova: `tests/test_codebase_map_working_run.py`. Le quattro regole per la review che stavano qui sono nella [spec della review](2026-11-03-semantic-review-foundation.md), sezione 5.

Dopo ogni modifica al codice la mappa si aggiorna da sola, nella parte che una macchina può ricalcolare. Schede e documenti di analisi li scrive un modello: l'aggiornamento non li rigenera, segnala quali non sono più validi.

## Parole

| Parola | Significato |
| --- | --- |
| Run | Una mappa del progetto fatta in un certo momento: lo snapshot dei file più i documenti di analisi |
| Run pubblicato | L'ultimo run completo. Non cambia più: è la prova su cui poggiano analisi e review |
| Run di lavoro | Un solo run, `working`, che segue il codice mentre cambia. Non contiene documenti di analisi |

## Regole

1. **Il run di lavoro nasce dal run pubblicato**, in `.daodan/map/runs/working/`, con lo stesso perimetro, e riparte da ogni nuovo run pubblicato. Senza un run pubblicato non nasce: la prima mappa si fa su richiesta. Un run con documenti di analisi non si riscrive (ogni documento è legato all'impronta del suo snapshot), e un run nuovo a ogni modifica costerebbe troppo spazio.
2. **Un aggiornamento,** in fila: rilegge solo i file cambiati (`compare_files(..., verify=True)`); rifà sullo stesso snapshot indice di ricerca, moduli e collegamenti `chiama` lessicali; esegue la scansione veloce e lo stack e avvia in background il passaggio degli indicizzatori ([pipeline di analisi](2026-11-15-pipeline-di-analisi.md), sezione 6); scrive `refresh.json` con esito, ora, stato del passaggio, file e simboli cambiati rispetto al run pubblicato e le frasi dei documenti pubblicati che li citano. Sotto il blocco del progetto nulla aspetta il container.
3. **Un hook lo lancia dopo ogni modifica:** evento `PostToolUse`, strumenti `Edit`, `Write`, `NotebookEdit`, `Bash`, in background. Dove gli hook non esistono lo stesso comando si lancia a mano.
4. **Un aggiornamento alla volta.** Una modifica arrivata durante un aggiornamento ne fa partire un altro alla fine, mai due insieme.
5. **Oltre il 40% dei file cambiati** (`FULL_REBUILD_SHARE`) si rifà tutto per intero, sempre senza modello.

## Quale run si usa

| Per | Run |
| --- | --- |
| Cercare, leggere, vedere chi chiama chi, valutare l'impatto di una modifica | Il run di lavoro, solo se l'aggiornamento è completo e coerente con il codice corrente; se manca, il run pubblicato con lo stesso controllo di freschezza |
| Leggere i documenti di analisi | Il run pubblicato |
| Fare una review | Mai il run di lavoro: un run che non cambia, creato per quella review |

L'esistenza della cartella non basta. Prima di rispondere gli strumenti leggono l'esito in `refresh.json` e confrontano lo snapshot con il sorgente: elenco dei file, dimensione e data, e il contenuto solo dove queste differiscono. Un run da aggiornare risponde `needs_refresh` con il motivo e l'azione, mai con un run obsoleto né con artefatti di aggiornamenti diversi.

## Limiti

- Una modifica che conserva dimensione e data non viene vista.
- Il passaggio degli indicizzatori gira in background: finché non finisce, `refresh.json` ne dice lo stato.

## Misure

9 novembre 2026, su questo repository (569 file), prima della pipeline a step: non rifatte dopo.

| Operazione | Tempo |
| --- | --- |
| Snapshot da zero | 15,7 s |
| Aggiornamento senza modifiche | 3,4 s |
| Aggiornamento con un file modificato | 3,6 s |
| Aggiornamento con i collegamenti `chiama` | 4,4 s |

## Aperto

- Avvisare l'agente a ogni aggiornamento.
- Rileggere solo i file indicati dall'hook invece di controllarli tutti: si fa se un aggiornamento supera 10 s su un progetto reale.
- **Aperta: da approfondire:** il tempo di un aggiornamento, del controllo di freschezza a ogni interrogazione e di una ricostruzione completa su un progetto reale, con la pipeline di oggi.
