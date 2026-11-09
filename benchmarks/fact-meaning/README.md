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

Giro 1 del 2026-11-09, ruolo al commit `4ac9475`: P1 e P2 trovati, 1 altro reale (`ring` divide per zero con obiettivo 0). `slot_badge` è segnalato con confidenza bassa come accoppiamento per `meal_id`: l'esca era mal costruita, perché l'ADR scritto per la fixture vieta ogni accoppiamento per slot e quindi anche quello. Nessuna modifica al ruolo. Il risultato sovrastima il caso reale: l'ADR sta accanto al codice e dice proprio la regola violata.

## Giro 2: `app2/`, senza ADR

I due flussi si capiscono solo dal codice: store separati, scritture separate (`add_food` dalla ricerca, `log_planned` dal piano), un solo aggancio per valore (`type == "planned"` con `dish_id`). Criterio, dichiarato prima della run: se il ruolo non trova Q1 e Q2 si aggiunge il controllo esplicito sul flusso e sul livello del fatto mostrato.

| Seme | Dove | Difetto |
|---|---|---|
| Q1 | `today.rows` | La spunta di un piatto del piano viene da `is_logged(meal_id)`: qualunque alimento aggiunto al pranzo spunta i piatti del pranzo |
| Q2 | `week.adherence` | L'aderenza al piano conta gli slot con una voce di diario, comprese le aggiunte libere, invece dei piatti del piano registrati |

Esche: `today.slot_kcal` somma le kcal del diario per slot (domanda sullo slot) e `diary.log_planned` è l'aggancio legittimo per valore.

Giro 2 del 2026-11-09, ruolo al commit `4ac9475`: Q1 e Q2 trovati in un solo finding, con il meccanismo esatto (`type` e `dish_id` esistono per separare piatto pianificato e cibo libero, nessun lettore li usa); esche non segnalate. Altri plausibili: `log_planned` non idempotente, un doppio tocco raddoppia le kcal; una modifica del piano lascia nel diario riferimenti orfani. Nessuna modifica al ruolo.

Costo: giro 1 82.888 token, 6 strumenti, 41 s; giro 2 81.664 token, 7 strumenti, 50 s.

Limite: fixture piccole e un solo modello; il caso reale ha più codice tra i due flussi e la review completa diluisce il ruolo nella composizione `code-auditor`.
