# Benchmark: renderer dell'esploratore

Gate del Task 1 di [`docs/plans/2026-11-08-codebase-explorer.md`](../../docs/plans/2026-11-08-codebase-explorer.md): React Flow + ELK contro LikeC4 Model Builder sulla stessa fixture, prima di fissare il renderer. Le due prove sono minime, non prodotti.

## Parametri

| Parametro | Valore |
| --- | --- |
| Fixture | `fixture/visual.json`, scritta a mano nel formato `daodan/visual@1`: due componenti con un file condiviso, una funzionalità inferita, quattro esterni (uno incompleto), gerarchia directory → file → simbolo, una scheda `stale_body`, due flussi con store, i dieci tipi di nodo del modello dei flussi |
| LikeC4 | `@likec4/core` 1.60.0, Model Builder; `likec4-probe/probe.mjs`, 47 righe |
| React Flow + ELK | `@xyflow/react` 12.12.1, `elkjs` 0.12.1; `reactflow-probe/probe.mjs`, 44 righe; l'interfaccia è la preview `.jcode/local/mockups/codebase-explorer/` (fuori da Git) |
| Esecuzione | Node 24.14.1, `npm install` in ciascuna cartella, poi `node probe.mjs` |

## Risultati, 12 novembre 2026

| Requisito | LikeC4 | React Flow + ELK |
| --- | --- | --- |
| Appartenenze multiple senza proprietario unico | No: il genitore viene dal nome qualificato, perse 2 appartenenze su 2 (`shared/money.ts` in `server`, `server/payments.ts` in `payment`); il file condiviso compare una volta | Sì: un'occorrenza per gruppo, il file condiviso compare in `web` e in `server` |
| Stati distinti | Come etichette: `stale_body` leggibile, ma provenienza, stato e freschezza finiscono in un unico insieme di tag | Campi distinti nei dati del nodo: `confirmed`, `incomplete`, `inferred`, `fresh`, `stale_body`, `uncovered` |
| Gerarchia espandibile | Sì, per nome qualificato e viste calcolate | Sì: nodi composti di ELK (`INCLUDE_CHILDREN`); nella preview, ingresso nel componente e ritorno |
| Flussi | Relazioni del modello: un passo verso il file condiviso arriva a una sola delle sue posizioni | Due flussi evidenziati, su 9 e 4 occorrenze |
| Tipi di nodo | Metadati per elemento | Dieci tipi, icona per tipo e marca interno o esterno nei dati del nodo |
| Focus e ripristino dei filtri | Viste statiche del modello | Già nella preview: selezione, viste per funzionalità e cicli, ritorno al sistema |
| Tempo | Modello calcolato in 30 ms | Layout ELK in 227 ms, primo calcolo |

## Verdetto

**React Flow + ELK.** LikeC4 non rappresenta un file in due gruppi senza duplicarlo nel modello, con ogni relazione da duplicare per ogni copia: l'adattamento è più complesso, non più semplice. Con React Flow le occorrenze multiple sono una scelta della proiezione, che Daodan controlla.
