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

## Prestazioni del viewer, prima misura

Passo 2 del Task 7 del piano. Obiettivi da misurare, non promessi: fino a 300 nodi visibili, layout più primo disegno entro 2 s; p95 della selezione entro 100 ms su 20 interazioni. 1.000 nodi è stress diagnostico.

### Parametri

| Parametro | Valore |
| --- | --- |
| Export | sintetici, da `scale.py 100 300 1000`: dell'80% dei nodi visibili ogni componente ha una cartella di quattro file con tre simboli; il 10% sono servizi esterni e il 10% store, con un flusso per store |
| Vista misurata | quella all'apertura: Logica, alla radice |
| Strumento | `measure.js` con lo strumento `browser_run_code_unsafe` di Playwright MCP, sull'indirizzo di `visual.py serve` |
| Browser | Chrome 157.0.8103.51 headless, finestra 1440 × 900 |
| Macchina | Intel Core Ultra 7 155H, 16 core e 22 thread, 31 GB, Windows 11 |
| Versioni | `@xyflow/react` 12.12.1, `elkjs` 0.12.1, React 19.3.1, viewer al commit `156607044` |
| Cosa si misura | layout nel worker, dalla richiesta alla risposta; dal caricamento al grafo disegnato (tutti i nodi nel DOM, poi due frame); 20 selezioni distribuite sui nodi, dal clic al frame dopo l'aggiornamento della scheda; heap JavaScript della pagina dopo una raccolta, senza quello del worker; nodi del DOM |

### Risultati, 12 novembre 2026

Una esecuzione per dimensione.

| Nodi visibili | Archi visibili | Entità e relazioni dell'export | Layout, primo e ripetuto | Grafo disegnato | Selezione p50, p95, massimo | Heap | Nodi del DOM |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 100 | 241 | 1.460 e 1.989 | 1.380 e 1.361 ms | 1.748 ms | 120, 265, 407 ms | 10,1 MB | 5.263 |
| 300 | 721 | 4.380 e 5.946 | 3.969 e 4.948 ms | 4.643 ms | 290, 378, 388 ms | 21,6 MB | 15.403 |
| 1.000 | 2.413 | 14.600 e 19.816 | oltre il budget di 5.000 ms | nessuno: «Impossibile disporre il grafo» | non misurata | non misurato | non misurato |

- **Nessuno dei due obiettivi è raggiunto.** A 300 nodi il grafo arriva in 4,6 s contro 2 s. La selezione supera 100 ms già a 100 nodi.
- Il layout ripetuto sullo stesso grafo costa quanto il primo: il tempo è di ELK, non del caricamento del worker.
- Con la finestra visibile, a 100 nodi: layout 934 e 1.169 ms, grafo disegnato in 1.165 e 1.492 ms, selezione p50 70 e 91 ms, p95 116 e 144 ms (due esecuzioni). Una finestra nascosta o coperta riduce i frame a circa uno al secondo e falsa ogni tempo: per questo `measure.js` apre un browser headless e si rifiuta sotto 30 frame al secondo.
- Cause non verificate con un profilo: a ogni selezione il viewer ricalcola la proiezione e ricrea gli oggetti di tutti i nodi e di tutti gli archi, che React Flow ridisegna.
- Non misurato: un run reale.
- La [mappa del sistema](../../docs/specs/2026-11-12-mappa-del-sistema.md), una proposta, mostra nodi con nome e non simboli: un grafo avrebbe una decina di nodi. Conviene decidere su quella prima di ottimizzare questo viewer per centinaia di nodi.
