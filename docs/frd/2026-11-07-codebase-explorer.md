# Esploratore visuale della codebase: requisiti

**Stato:** In parte. In uso le viste Logica e Fisica con ispettore, filtri, evidenze e flussi evidenziati (`daodan/core/visual.py`, `viewer/`). Proposta l'estensione per funzionalità (sezione 5). Aperti le prestazioni, tre casi di accettazione senza prova e la vista a elenco (sezione 6). **Decisioni tecniche:** [ADR](../adr/2026-11-07-codebase-explorer.md).

## 1. Obiettivo e viste

Chi sviluppa, chi fa consulenza e chi segue il progetto capisce un sistema passando dalla panoramica alle sorgenti. «Dinamico» qui vuol dire interattivo, non monitoraggio a runtime. La stessa entità resta riconoscibile fra le viste.

| Vista | Domanda | Contenuti |
| --- | --- | --- |
| Logica | Quali responsabilità collaborano? | Funzionalità, moduli e servizi esterni, con relazioni e appartenenze anche multiple |
| Fisica | Dove sono implementate e configurate? | Unità di build, cartelle, file, simboli; processi, database e indirizzi solo quando un'evidenza li sostiene |

- La vista fisica descrive ciò che risulta da codice e configurazione: non certifica il deployment.
- Un import o una chiamata statica non provano il comportamento a runtime; una relazione che manca resta una lacuna.
- Codebase Map resta proprietario di dati, spiegazioni e freschezza; senior-review giudica la correttezza. L'esploratore funziona anche senza una review.
- I flussi sono cammini sulle stesse entità: li definisce `docs/specs/2026-11-18-flussi-e-mappa-del-sistema.md`.

## 2. Esperienza richiesta

1. **Esplorare:** zoom, spostamento, inquadra tutto, ingresso in un gruppo e ritorno. Il livello iniziale mostra responsabilità o unità di build, non tutti i simboli. Ricerca per nome e palette dei comandi da tastiera.
2. **Filtrare:** per testo, tipo di entità, tipo di relazione e stato. I filtri nascondono, non eliminano la selezione; una vista vuota propone il ripristino. Conteggi distinti per elementi filtrati, aggregati e non caricati.
3. **Collegare le viste:** la selezione si conserva per riferimento canonico. Un file di più moduli mostra tutte le appartenenze, senza un proprietario inventato.
4. **Capire un elemento:** icona per tipo, nome leggibile e identificatore tecnico; nell'ispettore ruolo, relazioni in entrata e in uscita, moduli, percorso e righe, spiegazione, evidenze, stato e freschezza. Gli indirizzi non vengono contattati.
5. Nessuno spostamento, selezione o filtro modifica sorgenti, relazioni o schede.
6. Su schermi stretti barra laterale e ispettore diventano pannelli alternativi; ricerca e dettagli restano raggiungibili.
7. Ogni run si apre pulito; in `localStorage` restano solo aspetto e tema, mai dati del progetto.

## 3. Evidenze, aggiornamenti e stati

- **Provenienza**, **stato** e **freschezza** restano distinti, con i significati di Codebase Map: un modulo proposto non diventa confermato, un rilievo statico non diventa comportamento osservato.
- Ogni apertura è legata a un run e ai digest dei suoi input. Caricare un altro export non avvia analisi né modelli; il nuovo dataset si applica per intero o non si applica.
- Una selezione si conserva solo se il riferimento risolve; un riferimento scomparso dà un avviso e si toglie, senza associazioni per somiglianza.
- La freschezza è relativa allo snapshot: senza un nuovo controllo non si dichiara invariato il working tree.
- Un dato corrotto blocca il caricamento; una lacuna dichiarata è contenuto da mostrare; una descrizione obsoleta resta consultabile, etichettata.

## 4. Accettazione

| Caso | Risultato | Prova |
| --- | --- | --- |
| File condiviso da due moduli | Due occorrenze, un solo file nel conteggio, entrambe le appartenenze raggiungibili | `viewer/test/projection.test.ts`; `tests/test_codebase_map_visual.py` |
| Cambio di vista con un elemento selezionato | La selezione resta se il riferimento risolve nell'altra vista | `viewer/test/state.test.ts` |
| Gruppo chiuso con archi | L'arco aggregato conserva le relazioni originali; gli archi interni sono un conteggio | `projection.test.ts` |
| Filtra e ripristina | Stato iniziale ripristinato; la selezione non si perde | `projection.test.ts`, `state.test.ts` |
| Scheda obsoleta e modulo inferito | Stati separati, mai promossi | `projection.test.ts`; `test_codebase_map_visual.py` |
| Export invalido o schema ignoto | Errore comprensibile, la mappa di prima resta | `state.test.ts`; `test_codebase_map_visual.py` |
| Due layout che finiscono fuori ordine | Compare solo quello della struttura corrente | `viewer/test/layoutClient.test.ts` |
| Indirizzi con credenziali | Esportati senza credenziali, query e frammento | `test_codebase_map_visual.py` |
| Richieste al server con traversal, link simbolici o un altro `Host` | Rifiutate, nessun listing | `tests/test_codebase_map_visual_server.py` |
| Nome ostile (`<img src=x onerror=1>`) | Mostrato come testo | il nome è in `viewer/test/fixture.json`; nessuna asserzione trovata |
| Solo tastiera | Filtri, selezione e dettagli senza trascinare | in parte: i passi da tastiera di `viewer/test/browser.mjs` |
| Movimento ridotto | Animazioni facoltative | nessuna prova trovata nel viewer: dipende da Imago |

## 5. Estensione proposta: dalla mappa alle funzionalità

**Stato:** Proposta. Oggi il viewer evidenzia un flusso al livello della vista ed elenca i flussi che attraversano un nodo (`projection.test.ts`); il resto dipende dall'anagrafica dei flussi ([piano della ricerca](../plans/2026-11-20-ricerca-e-pacchetto-di-review.md)) e dal task 12 del [piano della pipeline](../plans/2026-11-20-pipeline-intera.md).

| Caso | Risultato atteso |
| --- | --- |
| Esplorare una funzionalità con un ingresso utente e uno automatico | Aprendo la funzionalità si vedono entrambi i rami; cambiare prospettiva conserva la selezione; richiuderla ripristina il nodo iniziale |
| Chiedere una review della funzionalità | Il perimetro comprende tutte le varianti, motiva file e simboli e segnala i tratti irrisolti; per un solo ramo include il codice condiviso che può determinarne l'esito |
| Chiedere una review di un componente | La mappa dà i flussi che attraversano il componente e dove ciascuno lo usa |

## 6. Aperto: da approfondire

- **Prestazioni.** Obiettivi: fino a 300 nodi visibili, layout più primo disegno entro 2 s; selezione entro 100 ms al p95 su 20 interazioni; 1.000 nodi è stress diagnostico. La sola misura ([`benchmarks/codebase-explorer`](../../benchmarks/codebase-explorer/README.md)) è sul viewer di prima, con React Flow, su export sintetici: nessuno dei due obiettivi era raggiunto. Sul grafo di Imago e su un run reale non sono misurati.
- **Tre casi senza prova:** nome ostile, uso da sola tastiera per intero, movimento ridotto (tabella sopra).
- **Vista a elenco** delle stesse entità e relazioni, per la navigazione da tastiera: richiesta in origine, non trovata nel viewer. Con lei il ridimensionamento dei pannelli.
- **Apertura nell'editor:** solo con un'integrazione dell'host; non c'è.
