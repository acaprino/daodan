# Esploratore visuale della codebase

**Stato:** proposta da approvare; nessuna implementazione. **Data:** 7 novembre 2026.
**Scelta acquisita:** UI Daodan originale, ispirata alle idee di esplorazione di Floorplan, costruita con librerie esistenti. Dinamico significa interattivo, non monitoraggio runtime.
**Decisioni tecniche e fonti:** [ADR](../adr/2026-11-07-codebase-explorer.md).

## 1. Obiettivo e contenuti

Consentire a sviluppatori, consulenti e interlocutori di progetto di capire un sistema passando dalla panoramica alle sorgenti e seguendo architetture, dati e percorsi utente. La stessa entità deve rimanere riconoscibile fra le viste.

| Vista | Domanda a cui risponde | Contenuti |
| --- | --- | --- |
| Logica | Quali responsabilità collaborano? | Funzionalità, moduli, responsabilità e servizi esterni con relazioni e appartenenze anche multiple |
| Fisica | Dove sono implementate e configurate? | Repository, unità di build/package, cartelle, file, simboli; processi, database e indirizzi soltanto quando supportati da evidenze |
| Flussi | Come si svolge questa operazione? | Percorsi tecnici, trasformazioni dati e user journey con passi, condizioni, rami, ritorni, effetti ed errori documentati |

La vista fisica descrive ciò che risulta dal codice/configurazione; non certifica il deployment. Un import non prova un trasferimento dati e un cammino del grafo non prova un percorso utente. Le relazioni mancanti restano lacune.

Codebase Map resta proprietario di dati, spiegazioni e freschezza. senior-review continua a giudicare la correttezza; l'esploratore funziona anche senza una review. La scelta dei modelli resta dell'host.

## 2. Esperienza richiesta

**Struttura proposta:** barra con progetto/run, ricerca e selettore Logica/Fisica; navigatore laterale con filtri e catalogo flussi; area centrale del grafo; ispettore contestuale; sequenza dei passi quando è selezionato un flusso. I pannelli si possono chiudere e ridimensionare. Su schermi stretti diventano pannelli alternativi, mantenendo raggiungibili ricerca e dettagli.

1. **Esplorare:** zoom, pan, adatta alla vista, breadcrumb, espandi/contrai gruppi e approfondisci un modulo. Il livello iniziale mostra responsabilità o unità di build, non tutti i simboli. Una vista elenco espone le stesse entità e relazioni per ricerca e navigazione da tastiera.
2. **Filtrare:** combinare testo, modulo/repository, tipo di entità, tipo di relazione e stati disponibili. I filtri nascondono elementi; selezione ed evidenziazione non li eliminano. Conteggi distinti indicano elementi filtrati, aggregati e non caricati. Una vista vuota propone il ripristino dei filtri.
3. **Seguire un flusso:** selezionare un percorso sovrappone passi e direzioni alla vista logica o fisica. Modalità «Evidenzia» attenua il contesto, «Solo flusso» lo esclude. Avanti/indietro segue i passi; una diramazione chiede quale ramo esplorare, non sceglie arbitrariamente. Loop e ritorni sono visitabili senza esecuzione o ripetizione automatica. Gli errori sono distinguibili anche senza colore.
4. **Collegare le viste:** selezione e passo corrente si conservano tramite riferimenti canonici. Se un file appartiene a più moduli si mostrano tutte le corrispondenze, senza inventare un unico proprietario. Una contrazione evidenzia il gruppo contenitore e quanti passi racchiude; il dettaglio dei passi non scompare. Il focus su un flusso sospende temporaneamente i filtri incompatibili, segnalandolo; uscendo li ripristina.
5. **Capire un elemento:** icona per tipo, nome leggibile e identificatore tecnico; ispettore con ruolo, relazioni in/out, moduli, percorso e righe, spiegazione, endpoint/indirizzo se disponibile, evidenze e stato di freschezza. Copia del riferimento sempre disponibile; apertura nell'editor solo con integrazione host configurata. Gli indirizzi non vengono contattati automaticamente.

La disposizione non salta durante selezione o evidenziazione: si ricalcola quando cambia la struttura visibile o su «Riordina». Nessuna modifica ai sorgenti, alle relazioni o alle schede è prodotta da spostamenti, selezioni o filtri.

## 3. Evidenze, aggiornamenti e stati

L'interfaccia mantiene distinti **provenienza**, **stato del contenuto** e **freschezza**, riusando i significati di Codebase Map. Non converte un modulo proposto in confermato e non equipara un rilievo statico a comportamento osservato.

Ogni apertura è legata a un run e ai digest degli input dell'export. «Aggiorna» carica un altro export completato, non avvia analisi o LLM dal browser. Il nuovo dataset si applica interamente o non si applica; le selezioni si conservano solo se i riferimenti risolvono. Riferimenti scomparsi generano un avviso e vengono rimossi dalla selezione, senza associazioni per somiglianza.

La freschezza visualizzata è relativa allo snapshot: senza un nuovo controllo Daodan non si dichiara che il working tree sia invariato. L'assenza di flussi strutturati lascia funzionanti le viste architetturali e mostra «Flussi non disponibili per questo run», con rinvio al report presente. Non si inventano flussi per riempire la vista.

Una transizione sconosciuta viene rappresentata come interruzione esplicita, non collegando artificialmente i suoi estremi. Un dato strutturalmente corrotto blocca il caricamento del nuovo export; una lacuna dichiarata è invece contenuto visualizzabile. Le descrizioni obsolete restano consultabili ma etichettate.

## 4. Accettazione

| Caso | Risultato osservabile |
| --- | --- |
| File condiviso da due moduli | Due occorrenze visive possono puntare alla stessa entità; il totale dei file unici non raddoppia; entrambe le appartenenze restano raggiungibili |
| Cambia Logica/Fisica con un flusso selezionato | Il percorso mantiene i riferimenti risolvibili e mostra le corrispondenze multiple; nessun collegamento viene inventato |
| Collassa un gruppo attraversato dal flusso | Il gruppo e gli archi aggregati conservano l'evidenziazione; l'ispettore elenca i passi e gli archi originali |
| Filtra, entra in «Solo flusso», esci | Sospensione dei filtri visibile e stato iniziale ripristinato; contatori corretti |
| Flusso con ramo, ritorno e gap | Ramo selezionabile, ritorno esplicito, gap visibile; nessuna animazione suggerisce traffico runtime |
| Scheda obsoleta e modulo inferito | Stati separati leggibili su grafo/elenco e ispettore; non promossi dalla proiezione |
| Nuovo export invalido o schema ignoto | Errore comprensibile, vecchia mappa utilizzabile; niente dataset parzialmente sostituito |
| Due layout asincroni terminano fuori ordine | Appare soltanto il layout della struttura corrente; selezione e viewport non vengono riportati allo stato precedente |
| Nomi ostili e indirizzi sensibili | Testo non eseguito come HTML; credenziali, query e frammenti URL non esportati; copia dei riferimenti senza esecuzione shell |
| Tastiera e movimento ridotto | Filtri, selezione, flussi e dettagli utilizzabili senza drag; focus visibile, significato non affidato solo al colore; animazioni opzionali |

Benchmark previsto in `benchmarks/codebase-explorer/` dopo approvazione: fixture piccola con due moduli, file condiviso, gerarchia, stato obsoleto, ramo e gap; fixture scalate con 100/300/1.000 nodi visibili e archi dichiarati; un run reale anonimizzato. Il README dovrà registrare hardware/browser/versioni, numero totale e visibile di entità/archi, campionamento, memoria, layout, interazioni e risultati, distinguendo sintetico e reale.

**Obiettivi iniziali proposti, non misurati:** fino a 300 nodi visibili, layout più primo disegno entro 2 s; p95 evidenziazione/selezione entro 100 ms su 20 interazioni dopo il caricamento, sulla macchina di riferimento dichiarata. Il caso a 1.000 nodi è stress diagnostico, non capacità promessa. Nessun risparmio token è assunto: l'esplorazione non effettua chiamate AI.

## 5. Stato e approcci

La scelta dell'utente sostituisce l'ipotesi precedente di adattare il viewer Floorplan: il prodotto sarà originale. Le alternative tecniche rimaste sono una composizione React Flow + ELK o il riuso del renderer di architetture LikeC4; confronto e motivazione sono nell'ADR, senza duplicarli qui.

La proposta comprende tutte e tre le prospettive e il collegamento ai flussi; l'ordine di implementazione non riduce l'obiettivo a una mappa dei file. L'eventuale strumentazione runtime è un requisito distinto e non è stata richiesta. Aspetto finale, spaziature e shortcut precisi restano al design UI; non sono state approvate schermate o installate librerie.
