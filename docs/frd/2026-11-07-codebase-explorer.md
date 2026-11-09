# Esploratore visuale della codebase

**Stato:** approvato l'8 novembre 2026; implementazione non iniziata. **Data:** 7 novembre 2026.
**Scelta acquisita:** UI Daodan originale, ispirata alle idee di esplorazione di Floorplan, costruita con librerie esistenti. Dinamico significa interattivo, non monitoraggio runtime.
**Decisioni tecniche e fonti:** [ADR](../adr/2026-11-07-codebase-explorer.md).

## 1. Obiettivo e contenuti

Consentire a sviluppatori, consulenti e interlocutori di progetto di capire un sistema passando dalla panoramica alle sorgenti. I flussi (percorsi tecnici, dati, user journey) sono cammini sulle stesse entità, riaperti il 9 novembre 2026: li definisce la [spec dei flussi](../specs/2026-11-09-flow-model.md). La stessa entità deve rimanere riconoscibile fra le viste.

| Vista | Domanda a cui risponde | Contenuti |
| --- | --- | --- |
| Logica | Quali responsabilità collaborano? | Funzionalità, moduli, responsabilità e servizi esterni con relazioni e appartenenze anche multiple |
| Fisica | Dove sono implementate e configurate? | Repository, unità di build/package, cartelle, file, simboli; processi, database e indirizzi soltanto quando supportati da evidenze |

La vista fisica descrive ciò che risulta dal codice/configurazione; non certifica il deployment. Un import o una chiamata statica non provano comportamento a runtime. Le relazioni mancanti restano lacune.

Codebase Map resta proprietario di dati, spiegazioni e freschezza. senior-review continua a giudicare la correttezza; l'esploratore funziona anche senza una review. La scelta dei modelli resta dell'host.

## 2. Esperienza richiesta

**Struttura proposta:** barra con progetto/run, ricerca e selettore Logica/Fisica; navigatore laterale con filtri; area centrale del grafo; ispettore contestuale. I pannelli si possono chiudere e ridimensionare. Su schermi stretti diventano pannelli alternativi, mantenendo raggiungibili ricerca e dettagli.

1. **Esplorare:** zoom, pan, adatta alla vista, breadcrumb, espandi/contrai gruppi e approfondisci un modulo. Il livello iniziale mostra responsabilità o unità di build, non tutti i simboli. Una vista elenco espone le stesse entità e relazioni per ricerca e navigazione da tastiera.
2. **Filtrare:** combinare testo, modulo/repository, tipo di entità, tipo di relazione e stati disponibili. I filtri nascondono elementi; selezione ed evidenziazione non li eliminano. Conteggi distinti indicano elementi filtrati, aggregati e non caricati. Una vista vuota propone il ripristino dei filtri.
3. **Collegare le viste:** la selezione si conserva tramite riferimenti canonici. Se un file appartiene a più moduli si mostrano tutte le corrispondenze, senza inventare un unico proprietario. Una contrazione evidenzia il gruppo contenitore e conserva gli archi originali consultabili.
4. **Capire un elemento:** icona per tipo, nome leggibile e identificatore tecnico; ispettore con ruolo, relazioni in/out, moduli, percorso e righe, spiegazione, endpoint/indirizzo se disponibile, evidenze e stato di freschezza. Copia del riferimento sempre disponibile; apertura nell'editor solo con integrazione host configurata. Gli indirizzi non vengono contattati automaticamente.

La disposizione non salta durante selezione o evidenziazione: si ricalcola quando cambia la struttura visibile o su «Riordina». Nessuna modifica ai sorgenti, alle relazioni o alle schede è prodotta da spostamenti, selezioni o filtri.

## 3. Evidenze, aggiornamenti e stati

L'interfaccia mantiene distinti **provenienza**, **stato del contenuto** e **freschezza**, riusando i significati di Codebase Map. Non converte un modulo proposto in confermato e non equipara un rilievo statico a comportamento osservato.

Ogni apertura è legata a un run e ai digest degli input dell'export. «Aggiorna» carica un altro export completato, non avvia analisi o LLM dal browser. Il nuovo dataset si applica interamente o non si applica; le selezioni si conservano solo se i riferimenti risolvono. Riferimenti scomparsi generano un avviso e vengono rimossi dalla selezione, senza associazioni per somiglianza.

La freschezza visualizzata è relativa allo snapshot: senza un nuovo controllo Daodan non si dichiara che il working tree sia invariato.

Un dato strutturalmente corrotto blocca il caricamento del nuovo export; una lacuna dichiarata è invece contenuto visualizzabile. Le descrizioni obsolete restano consultabili ma etichettate.

## 4. Accettazione

| Caso | Risultato osservabile |
| --- | --- |
| File condiviso da due moduli | Due occorrenze visive possono puntare alla stessa entità; il totale dei file unici non raddoppia; entrambe le appartenenze restano raggiungibili |
| Cambia Logica/Fisica con un elemento selezionato | La selezione resta se il riferimento risolve nell'altra vista e mostra le corrispondenze multiple; nessun collegamento viene inventato |
| Collassa un gruppo con archi evidenziati | Il gruppo e gli archi aggregati conservano l'evidenziazione; l'ispettore elenca gli archi originali |
| Filtra e poi ripristina | Stato iniziale ripristinato; contatori corretti |
| Scheda obsoleta e modulo inferito | Stati separati leggibili su grafo/elenco e ispettore; non promossi dalla proiezione |
| Nuovo export invalido o schema ignoto | Errore comprensibile, vecchia mappa utilizzabile; niente dataset parzialmente sostituito |
| Due layout asincroni terminano fuori ordine | Appare soltanto il layout della struttura corrente; selezione e viewport non vengono riportati allo stato precedente |
| Nomi ostili e indirizzi sensibili | Testo non eseguito come HTML; credenziali, query e frammenti URL non esportati; copia dei riferimenti senza esecuzione shell |
| Tastiera e movimento ridotto | Filtri, selezione e dettagli utilizzabili senza drag; focus visibile, significato non affidato solo al colore; animazioni opzionali |

Benchmark previsto in `benchmarks/codebase-explorer/` dopo approvazione: fixture piccola con due moduli, file condiviso, gerarchia, stato obsoleto e gap; fixture scalate con 100/300/1.000 nodi visibili e archi dichiarati; un run reale anonimizzato. Il README dovrà registrare hardware/browser/versioni, numero totale e visibile di entità/archi, campionamento, memoria, layout, interazioni e risultati, distinguendo sintetico e reale.

**Obiettivi iniziali proposti, non misurati:** fino a 300 nodi visibili, layout più primo disegno entro 2 s; p95 evidenziazione/selezione entro 100 ms su 20 interazioni dopo il caricamento, sulla macchina di riferimento dichiarata. Il caso a 1.000 nodi è stress diagnostico, non capacità promessa. Nessun risparmio token è assunto: l'esplorazione non effettua chiamate AI.

## 5. Stato e approcci

La scelta dell'utente sostituisce l'ipotesi precedente di adattare il viewer Floorplan: il prodotto sarà originale. Le alternative tecniche rimaste sono una composizione React Flow + ELK o il riuso del renderer di architetture LikeC4; confronto e motivazione sono nell'ADR, senza duplicarli qui.

Componenti proposti per Daodan stesso, usati dalla prima preview: [proposte](2026-11-07-codebase-explorer-proposals.json), da caricare con `modules.py propose`. Restano inferiti finché il progetto non li copia in `codebase-modules.json`.

La proposta comprende le due prospettive logica e fisica; l'ordine di implementazione non riduce l'obiettivo a una mappa dei file. I flussi sono stati riaperti il 9 novembre 2026 e hanno una spec propria; non cambiano l'implementazione già approvata finché il modello non è misurato. L'eventuale strumentazione runtime è un requisito distinto e non è stata richiesta. Aspetto finale, spaziature e shortcut precisi restano al design UI; non sono state approvate schermate o installate librerie.
