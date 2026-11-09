# Benchmark: un fatto letto con un altro significato

Prova se `senior-review:logic-integrity-auditor`, così com'è, trova un lettore che risponde a una domanda con un fatto che significa altro. Il caso riproduce un bug trovato in un'app di piani alimentari: «lo slot ha una registrazione» letto come «il piatto del piano è stato mangiato».

## Parametri

| Parametro | Valore |
|---|---|
| prova | `logic-integrity-auditor` al commit `4ac9475` (invariato) |
| richiesta | «Rivedi `app/`: vista del piano dei pasti e diario.» |
| esecuzione | un sotto-agente `general-purpose` dell'host, modello Sonnet, con il file ruolo come istruzioni, vincolato a una copia di `app/` e del plugin |

Criterio, dichiarato prima dei risultati: se il ruolo trova P1 e P2 senza segnalare le esche, non si cambia nulla; altrimenti si aggiunge il controllo che manca e lo si prova su una variante nuova.

## Fixture

`app/`: piano per slot e piatti (`plan.py`), diario per slot con additions, tombstone e saltato (`log.py`), vista (`view.py`) e `docs/adr-0013.md`, per cui piano e diario si toccano solo per valore, con `type == "planned"`.

| Seme | Dove | Difetto |
|---|---|---|
| P1 | `view.dish_eaten` | Un fatto per slot (record non vuoto) è usato come fatto per piatto: un'aggiunta libera spunta tutti i piatti dello slot; accoppia piano e diario per `meal_id`, contro l'ADR-0013 |
| P2 | `view.skipped` | `states_nothing` («niente registrato») è usato come «saltato», che il diario registra in `Record.skipped` |

Esche: `slot_badge` usa `states_nothing` per una domanda sullo slot, e `ring` somma le kcal dal diario; entrambi corretti.

## Prove senza modello

`python -B -m pytest -q benchmarks/fact-meaning`

## Misure

Run in corso.
