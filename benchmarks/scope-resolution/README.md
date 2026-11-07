# Benchmark: scope resolution (Phase 0 della review)

Mette alla prova `docs/specs/2026-11-04-review-scope-resolution.md` su un run reale di Codebase Map
(mini-app `app/`: ordini, pagamenti, spedizioni). Il testo provato è quello di
`plugins/senior-review/skills/review-preparation/references/team-review.md`, sezione "Request to files".

```text
python -B -m pytest -q                                  # strutture, protocollo, resolver (1 xfail dichiarato)
python -B run_cases.py --run-id bench-1 --label final   # resolver sui 9 casi → results/run-<ts>-final/report.md
python -B mapcli.py SESSION search "sconto"             # i tool reali, con traccia, per una sessione del modello
python -B model_eval.py SESSION C4                      # valuta la sessione contro il ground truth
```

## Cosa misura

| Domanda | Con che cosa |
|---|---|
| Il protocollo regge sui tool reali? (budget, una riformulazione, indice rotto ≠ ricerca vuota, collegamenti non inventati, tre esiti) | `resolver.py`, `tracecheck.py`, `run_cases.py`: deterministico, zero token |
| Il perimetro è giusto? | sessioni del modello via `mapcli.py`, valutate da `model_eval.py`: costano token |

Tre misure per caso: file indispensabili mancanti (`required`), file che è un errore includere (`forbidden`), violazioni
di protocollo. Precision e recall sono riportate ma non asserite: oltre i file indispensabili decide il reviewer, motivando.

## Parametri da provare

| Parametro | Dove | Valori provati | Risultato misurato |
|---|---|---|---|
| Modello | sessioni | Haiku, Opus | Esito 7/9 e 9/9; file indispensabili 9/9 per entrambi; precision 0.82 e 0.90 |
| Phase 1 della review `branch` | `review-preparation/references/team-review.md` | attuale (1a-1d, quattro dispatch), ridisegnata (contesto, domande, selezione), semplificata (comprensione, scelta dei reviewer, avvio sull'intero perimetro; [spec](../../docs/specs/2026-11-07-review-context-and-selection.md)) | Caso: commit `943bdc44c` (sconto sottratto due volte, oracolo in `f52f7352c`), Opus, un giro. Tabella e formula in `results/review-branch-943bdc44c/tokens.md`. Semplificata alla cieca: i 2 reviewer scelti trovano entrambi il difetto e il contesto non lo nomina; run fermato dal sistema per memoria durante Lens 0, senza riproduzione né rapporto. Completa ma non alla cieca: trovato e riprodotto, 6 agenti, 1,17M token nuovi contro 1,58M della ridisegnata e 637K della `light`. Baseline dichiarata mancante: python. Il criterio di costo non è raggiunto: 1,8x la `light`. Review senza diff («Cerca problemi nel modulo ordini», basis `content`), alla cieca in un processo nuovo: Phase 0 `resolved` con 3 query e 1 outline, 8 file; Phase 1 sceglie 7 reviewer con il motivo, un job ciascuno, tier medium; il difetto seminato è F01 (High, confidenza 97, trovato da 2 reviewer su 7, il contesto non lo nomina) tra 23 finding. Fermata dal controllo di memoria (commit libero 2,2 GB, soglia 3) prima della verifica: nessuna riproduzione né rapporto. Contesto del coordinatore 367K, output 272K, 1,22M token nuovi, 44 minuti. La verifica di ogni finding (`all-above-floor`) richiederebbe 65-88 lenti: è il costo dominante e non è misurato. Attuale (1a-1d): non misurata |
| Budget | testo, `POLICY` | circa 6 query, 10 letture | Query medie: Haiku 5.7, Opus 8.4 (massimo 13). Opus supera 6 query in 7 casi su 9. Costo da valutare |
| Frase sui chiamanti di una modifica | testo | senza, con | C1 su Opus: `service.py` mancante in 2 prove su 2, presente con la frase (n=1) |
| Formulazione di `partial` | testo | «what is missing», «what the request still needs» | Nessun effetto: Haiku resta `partial` su C2 e C3b |
| `top_files` | `POLICY` del resolver | 5, 2 | Precision 0.65 e 0.70, misurata su una fixture precedente |
| Filtro `anchor-in-read` | resolver | attivo, spento | Precision 0.77 ma recall 0.93 (perde `service.py`): tolto |

## Risultati

Tabella per caso in `results/model-runs/SUMMARY.md`.

| | Esito uguale all'atteso | File indispensabili | File vietati inclusi | Precision | Recall |
|---|---|---|---|---|---|
| Resolver | 9/9 | 8/9 | 0 | 0.53 | 0.94 |
| Haiku | 7/9 | 9/9 | 0 | 0.82 | 1.00 |
| Opus | 9/9 | 9/9 | 0 | 0.90 | 1.00 |

Nessun modello ha inventato un collegamento: su C6 entrambi dichiarano che la destinazione non è confermabile. Le due
mancate corrispondenze di Haiku sono `partial` al posto di `resolved`, con i file richiesti presenti: i due esiti proseguono
allo stesso modo. Lezioni e correzioni in `results/findings.md`.

## Limiti

- Una sola esecuzione per caso e per testo: è una prova di fumo, non una misura di affidabilità.
- C3, C4, C5 e C7 vengono dal giro precedente alle due correzioni del testo.
- Isolamento dichiarato dalle sessioni, non verificabile dalla traccia. Opus è lo stesso modello che ha scritto il benchmark.
- Attese scritte da chi ha scritto spec e fixture; quella di C8 è cambiata dopo aver visto le sessioni.
- Non provati: diff e PR reali, `symbols_at`, `stale_callers`, repository grandi, import tra package, una review completa con questa Phase 0.
