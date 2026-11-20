# Piano: ricerca dei flussi e pacchetto di una review

**Obiettivo:** da una richiesta in parole al flusso, al modulo logico o al componente giusto, e da lì al pacchetto da dare a un revisore; l'embedder propone, la macchina verifica.
**Parte di:** [piano della pipeline intera](2026-11-20-pipeline-intera.md), diviso per aspetto il 20 novembre 2026 su richiesta del proprietario. Quel piano tiene l'ordine fra i tre piani (sezione 3), che cosa gira dove (sezione 2) e la prova da zero (sezione 4); i numeri dei task sono rimasti gli stessi. **Spec:** [ricerca dei flussi e pacchetto di una review](../specs/2026-11-20-ricerca-e-pacchetto-di-review.md).
**Vincoli:** quelli del piano della pipeline intera. Ogni task: prima il test rosso, poi il codice; tocca solo i file che nomina. Vengono dopo il task 8: l'anagrafica lega flussi che devono prima esistere (task 7).

## Task

- **9.** **Anagrafica e legami fra flussi** (G1, G2). Una voce per flusso: nome, area, tipi, ingressi con l'etichetta, effetti, nodi, file; `avvia`, `condivide` e `stesso dato` dai collegamenti; `about` li dà.
   Test: come G1 e G2, passo 1. Riusa: `system_map.load`, `flows.cached_links`.

- **10.** **La ricerca sull'anagrafica** (G2b, passo 2). `embedding_worker` indicizza le voci del task 9 e i nodi di profondità da 0 a 2 (269 delle 531 richieste chiedono una parte, non un flusso), una volta dopo la mappa; `score.py system` restituisce gli abbinamenti di nodi e flussi, che oggi calcola e non dà: servono alla colonna della ricerca; la ricerca dà tre voci con il punteggio; senza modello preparato risponde con le parole in comune e lo dice.
   Test: con un fornitore finto. Riusa: `refresh_index`, `search`.

- **10b.** **Il pacchetto di una review dalla ricerca** (spec, 11.1, 11.2 e 12.3). Da una richiesta in parole: le tre voci più vicine con il punteggio (task 10); la voce scelta dà i punti di partenza, `flows.units` i file e le unità, i legami del task 9 il contesto (`condivide`, `avvia`); il brief elenca flussi, frecce, servizi esterni e lacune, non solo i file. La ricerca sceglie da dove partire; che cosa entra lo decide il grafo.
   Test: con un fornitore finto, una richiesta scritta senza le parole del nome porta al suo flusso, e il pacchetto ha i suoi file e, come contesto, quelli di un flusso che `condivide`; due voci con il punteggio vicino restano tutte e due proposte; senza modello preparato il pacchetto nasce dalle parole in comune e lo dice. Riusa: `scope_planner.py`, che passa già `embedding_result` a `retrieval.search`; `flows.units`; `about`.

- **10c.** **L'embedder propone gli abbinamenti, non li decide** (spec, 12.4; piano del 19 novembre, G2b, usi 2 e 3). Prima la misura, a costo zero sulle schede dei percorsi già scritte: quante coppie «stesso flusso» proposte per vicinanza sono giuste contro i riferimenti, e quante forme prendono il tipo giusto dalla più vicina già classificata. Entra nel codice solo se la misura regge: le coppie proposte vanno nella coda di domande (spec degli ingressi, 7.7) e nessun abbinamento si registra per sola vicinanza.
   Test: uno script in `benchmarks/system-map/` con il suo numero nel README; poi, se entra, con un fornitore finto: una coppia proposta che la macchina rifiuta non unisce i due percorsi. Riusa: `embed_probe.py rank`, `traces.py cards`.
