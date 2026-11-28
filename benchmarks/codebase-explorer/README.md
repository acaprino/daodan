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
- La [mappa del sistema](../../docs/specs/2026-11-18-flussi-e-mappa-del-sistema.md), una proposta, mostra nodi con nome e non simboli: un grafo avrebbe una decina di nodi. Conviene decidere su quella prima di ottimizzare questo viewer per centinaia di nodi.
- Dal porting a Sigrid (novembre 2026) la tela disegna solo i nodi nella vista: `measure.js` legge la pagina nuova e distingue i nodi della vista (`nodes`) da quelli nel DOM (`drawn`). La misura non è ancora rifatta.

## Vista dal servizio

Passo `T2.C.12` di [`docs/plans/refactoring.md`](../../docs/plans/refactoring.md): quanto costa `app_view.view`, la vista che l'App chiede a `/api/app/graph`, con un archivio grande e 300 nodi nel primo grafo. Obiettivo da misurare, non promesso.

### Parametri

| Parametro | Valore |
| --- | --- |
| Involucro | `scale.envelope(334, files=73, wide=432)` (`view_scale.py`): 267 componenti con 73 file di tre simboli, il primo con 432 file (più di un blocco, `BLOCK = 300`), 33 servizi esterni, 34 store con un flusso ciascuno; 80.001 entità, 104.262 relazioni, 38,6 MB di JSON, costruito in 0,5 s |
| Casi | primo grafo; un gruppo aperto (`component:c0001`); il gruppo largo aperto (`component:c0000`: 300 file e «altri 132»); il blocco seguente (`more:component:c0000#1`); filtro `logico` in `hide` e in `highlight` |
| Cosa si misura | tempo di `app_view.view` sull'involucro già in memoria (mediana e massimo di 5 chiamate); peso: byte del JSON che il servizio manda (compatto, non ASCII-escaped); nodi, attenuati, archi |
| Macchina | Modal, 2 core e 4 GB (`modal_view_scale.py`), Python 3.13 |
| Codice | `develop` `5b8edc3` con gli script di questo passo |
| Comando | `modal run benchmarks/codebase-explorer/modal_view_scale.py`; il test del calcolo è `tests/test_benchmark_view_scale.py` |

### Risultati, 28 novembre 2026

Due esecuzioni (`ap-pxLM0Tuqaupm0TPq2f0rNw`, `ap-7JQvqQwXyRFEaOOgiUskyp`); i tempi sono le mediane delle due, il massimo il peggiore.

| Caso | Nodi (attenuati) | Archi | Mediana | Massimo | Peso |
| --- | --- | --- | --- | --- | --- |
| Primo grafo | 300 | 3.643 | 301 e 263 ms | 524 ms | 1,31 MB |
| Gruppo aperto, 73 file | 372 | 3.718 | 304 e 261 ms | 617 ms | 1,35 MB |
| Gruppo largo aperto: 300 file e «altri 132» | 600 | 3.997 | 298 e 256 ms | 477 ms | 1,50 MB |
| Blocco «altri N» aperto | 731 | 4.134 | 293 e 262 ms | 496 ms | 1,57 MB |
| Filtro `logico`, `hide` | 33 | 0 | 299 e 343 ms | 707 ms | 8,5 kB |
| Filtro `logico`, `highlight` | 300 (267) | 3.643 | 306 e 364 ms | 482 ms | 1,32 MB |

- Il tempo non dipende dalla vista: ogni caso costa circa 0,3 s, cioè una passata sulle 80.001 entità e 104.262 relazioni dell'involucro. Aprire, filtrare o chiedere un blocco non aggiunge tempo misurabile.
- Il peso segue gli archi, non i nodi: 3.643 frecce fra 300 nodi fanno 1,3 MB, circa 360 byte per freccia; con `hide` restano 33 nodi e 8,5 kB. Non scomposto per campo (conteggi, punti citati, `relations`).
- Il blocco fa il suo lavoro: il gruppo di 432 file si apre su 300 e «altri 132», e aprire il blocco li dà tutti, senza figli persi (il test).
- Non misurato: il servizio HTTP (`app.App`, la sua cache delle viste), la lettura di `visual.json` dal disco e un run reale.
