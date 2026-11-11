# Benchmark: flussi e unità della fase 2

Prova la [spec della fase 2](../../docs/specs/2026-11-09-flow-model.md). Le soglie sono scritte qui prima di ogni misura; i casi reali sono [`polar-flow`](../polar-flow/README.md), [`tududi-flow`](../tududi-flow/README.md) e [`phazly-flow`](../phazly-flow/README.md), ognuno con i propri valori attesi. Tutto gira su Modal; sulla macchina locale solo caricamento degli input e lettura dei risultati.

## Parametri e soglie

| Misura | Cosa si conta | Soglia |
|---|---|---|
| 0. Collegamenti `chiama` | risolte su risolvibili, per caso e per linguaggio del perimetro | un caso entra nelle misure 1 e 3 con almeno il 70% |
| 1. File di un difetto noto | incarichi di `pack()` e unità che contengono i file di ogni difetto atteso, a parità di perimetro e limite di byte | ogni difetto in meno unità che incarichi di `pack()`; stessi file distinti assegnati; due esecuzioni identiche |
| 2. Fixture a due strati | collegamenti trovati contro attesi, dedotti a parte; collegamenti falsi; lacune dichiarate | tutti i collegamenti attesi; nessun collegamento falso fra campi indipendenti o rotte omonime; ogni identità ambigua è una lacuna |
| 3. Caso fra strati | dal fatto mostrato allo store, attraverso la rotta del caso | il flusso arriva allo store in tududi e phazly |
| 4. Etichette | granularità e significato contro una lettura manuale, su 20 collegamenti; costo per collegamento | almeno 16 su 20 concordi |
| 5. Simboli e funzionalità | flussi attesi ritrovati; file entrati senza appartenere a quelli attesi; flussi incompleti | tutti i flussi attesi, zero file estranei; ogni causa di arresto lascia il flusso incompleto; un nodo senza codice compare con il collegamento dichiarato |

## Fixture

`app/` è un negozio su due strati: interfaccia in TypeScript (`web/`), servizio `shop` e servizio `admin` in Python. Contiene uno stato globale con campi indipendenti, due rotte omonime in servizi diversi, una rotta chiamata con un percorso dinamico, due azioni dell'utente, un lavoro pianificato, un fornitore di pagamento esterno dichiarato in `codebase-modules.json`, una catena di chiamate fra tre file con un ciclo e due lettori della stessa collezione, uno coerente con chi scrive e uno no. I valori attesi stanno in `expected.json`, fuori da `app/`: chi analizza la fixture non li vede.

## Esecuzione

| Misura | Comando |
|---|---|
| 0 | `modal run benchmarks/flow-model/modal_engine_count.py --phazly-tar <archivio>`; l'archivio è `git archive 46c92b28 react-app shared functions-python` di phazly-app, senza file `.env` |

## Risultati

### Misura 0, 11 novembre 2026, Modal (4 CPU, 16 GB per caso)

| Caso | Risolte su risolvibili | Per linguaggio | Snapshot | Passaggio motore |
|---|---|---|---|---|
| polar `server/` | 55,9% (34.535 su 61.758) | Python 55,9% | 179 s | 41 min |
| tududi | 52,8% (17.282 su 32.717) | JavaScript 46,7%, TypeScript 69,4% | 92 s | 11 min |
| phazly | 59,7% (13.288 su 22.271) | Python 73,4%, TypeScript 36,8%, JavaScript 26,6% | 51 s | 10 min |

Nessun caso raggiunge la soglia del 70%. Note: polar senza l'ambiente Python del progetto; in phazly il motore Kotlin non si è installato (HTTP 403 sul download) e il TypeScript è sotto il campione del 9 novembre (circa 72% su `react-app` da solo). Valori per caso in `results/`.

### Misure 2 e 5 sulla fixture

`tests/test_codebase_map_flows.py`, regole scritte a mano in `rules.json`: tutti i collegamenti attesi, nessun collegamento vietato, la lacuna del percorso dinamico dichiarata, il flusso dal badge arriva alla collezione passando per la rotta, unità che tengono insieme chi scrive e chi legge con limite di 120.000 e di 1.500 byte. Le regole scritte da un modello non sono ancora provate.
