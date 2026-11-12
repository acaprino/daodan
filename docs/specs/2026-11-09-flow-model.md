# Fase 2: flussi e unità ricavati dal grafo

**Stato:** in prova. `flows.py` applica le regole, traccia i flussi ai quattro livelli e forma le unità; `codebase_map_flows` li espone; misure 2, 3 e 5 sulla fixture e prima applicazione a un caso reale in [`benchmarks/flow-model`](../../benchmarks/flow-model/README.md) e [`benchmarks/phazly-flow`](../../benchmarks/phazly-flow/README.md). Misure 1 e 4 fatte su phazly; la scheda del flusso si registra con `codebase_map_flows(card=...)`. Restano il tipo dei nodi con le icone e i flussi nell'esploratore. **Data:** 9 novembre 2026; aggiornata l'11 novembre 2026. Fase 2 di 3; l'uso nella review si decide nella [fase 3](2026-11-09-flows-in-review.md).

Codebase Map deve saper rispondere a due domande: «chi scrive il dato che l'applicativo mostra o restituisce, e cosa significa?» e «cosa succede quando arriva questa azione o questa richiesta?». Vale per qualsiasi app o servizio: i casi concreti stanno nei README dei benchmark. Riapre l'esclusione dei flussi nel [FRD](../frd/2026-11-07-codebase-explorer.md) e nell'[ADR](../adr/2026-11-07-codebase-explorer.md) dell'esploratore.

## Parole

Ogni parola ha un solo significato in queste tre spec.

| Parola | Significato |
| --- | --- |
| Nodo | Un estremo di un collegamento: un simbolo, oppure un modulo della mappa. Tutto ciò che partecipa a un flusso è un nodo, anche senza codice nel repository: un attore, una schermata, una funzionalità, un servizio esterno, un elemento dell'infrastruttura (server, gateway, database, coda), un dispositivo. Ridefinito dalla [mappa del sistema](2026-11-12-mappa-del-sistema.md): una cosa con un nome che raccoglie i suoi membri; un simbolo da solo non è un nodo |
| Tipo di nodo | Cosa fa il nodo nel flusso, da un elenco breve e chiuso: attore, schermata, funzionalità, servizio o API, gateway, database, coda, autenticazione, dispositivo, altro. Un nodo è anche interno o esterno al progetto |
| Collegamento | Da un nodo a un altro, con tipo ed evidenza. **Diretto** se sta nel codice (chiamata, import). **Dedotto** se una regola di collegamento riconosce lo stesso dato o la stessa rotta in chi offre e in chi usa. **Dichiarato** se tocca un nodo senza codice: è il collegamento `uses` del grafo dei moduli |
| Tipo di collegamento | `chiama`, `scrive`, `legge`, `attiva` (un'azione dell'utente attiva il suo handler) |
| Flusso | Sequenza ordinata di collegamenti, da un punto d'ingresso a un fatto mostrato. Nella [mappa del sistema](2026-11-12-mappa-del-sistema.md) questo è un percorso; il flusso è un processo con un nome |
| Punto d'ingresso | Dove un flusso comincia: rotta, comando, azione dell'utente, lavoro pianificato |
| Store | Dove un dato vive: stato globale, tabella o collezione, file, cache |
| Fatto mostrato | Un valore o un testo che l'applicativo mostra o restituisce |
| Granularità | Ciò a cui un dato si riferisce: un ordine, una sua riga, un utente |
| Significato | Una frase: cosa afferma quel dato |
| Strato | Interfaccia, servizio, dati |
| Livello | Il modo di guardare un flusso: fisico, logico, UX, dati, misto. Sostituito dai livelli della [mappa del sistema](2026-11-12-mappa-del-sistema.md): persone, funzioni, dati, codice, infrastruttura |
| Perimetro | I file che un lavoro copre: quelli che un run mappa, quelli che una review giudica |
| Contesto | I file che si consultano per giudicare il perimetro, senza giudicarli |
| Unità | I file affidati a un revisore in un solo incarico |
| Punto di partenza | Ciò che la richiesta nomina e da cui si comincia a seguire i collegamenti |
| Revisore | Chi esamina un incarico seguendo un mandato: logica, sicurezza, e così via |
| Regola di collegamento | Come, in questo progetto, si riconosce chi offre e chi usa uno store o una rotta |

Un flusso non introduce entità nuove: i suoi nodi sono i simboli e i moduli che la mappa e l'esploratore hanno già, con gli stessi riferimenti.

## Comportamento attuale

- `03-flows.md` descrive i flussi in prosa e diagrammi, al massimo cinque per categoria. Non si può interrogare e la review non lo legge.
- La review divide i file con `pack()`: ordine per percorso del file, un gruppo ogni 120.000 byte. Nelle run di [`benchmarks/phazly-flow`](../../benchmarks/phazly-flow/README.md) chi scrive, chi legge e chi mostra lo stesso dato sono finiti in tre incarichi diversi; la mappa di quelle run non aveva collegamenti `chiama` per TypeScript.
- Nessuno strumento risponde a «chi scrive questo dato». Due simboli che usano lo stesso store non si chiamano, quindi il grafo non li collega.
- Le due rassegne ([letteratura](../research/2026-11-09-flow-reconstruction-literature.md), [dettagliata](../research/2026-11-11-flow-reconstruction-detailed.md)) riportano quattro fatti utili:
  - i collegamenti dedotti si ottengono elencando chi offre e chi usa e accoppiandoli (in un caso misurato, 135 trovati su 153);
  - nell'interfaccia le direzioni sono due: dal fatto mostrato a chi lo scrive, dall'azione ai suoi effetti;
  - la qualità dei collegamenti conta più del modo di raggrupparli;
  - più contesto senza selezione peggiora i risultati.

  Nessun lavoro verificato unisce i tre strati in un grafo né confronta il significato fra chi scrive e chi legge.

## Proposta

### 1. Collegamenti dedotti

1. Il modello legge il progetto una volta e scrive una tabella di regole di collegamento. Una regola dice come si riconosce chi offre e chi usa: «lo stato globale si legge con `<hook>`», «le chiamate al servizio passano da `<client>`, con gli URL di `<file>`», «la tabella `<nome>` si scrive solo da `<modulo>`». Una regola indica il costrutto in uno di tre modi: una funzione del progetto; una chiamata così come è scritta, quando passa da un oggetto di libreria (`router.post`, `db.<collezione>.find_one`), limitata a un insieme di cartelle; un attributo del markup che lega un'azione al suo handler.
2. La macchina applica la tabella a tutto il sorgente: elenca chi offre e chi usa, e li accoppia sull'identità riconosciuta. Ogni regola precisa cosa confrontare: store o collezione e campo/chiave del dato; servizio, metodo e URL per una rotta. Condividere lo store o il solo nome non basta: scrivere `store.theme` non collega a chi legge `store.cart`.
3. Ogni coppia riconosciuta diventa un collegamento dedotto, con la sua evidenza. Identità ambigue, accessi dinamici non risolti e accessi spaiati restano lacune dichiarate: non diventano collegamenti. Il modello si prova in `benchmarks/flow-model/` prima di esporre `codebase_map_flows`.
4. Un nodo senza codice è un modulo `external`: lo dichiara il progetto o lo propone il modello, con la sua evidenza. Il collegamento che lo raggiunge è dichiarato, non ricavato dal sorgente. Se il modulo è solo proposto, anche il collegamento resta `inferred`.
5. *Sostituito dalla [mappa del sistema](2026-11-12-mappa-del-sistema.md), sezione 3: un registro proprio e stack-analyser.* Un servizio con nome proprio si riconosce dalle dipendenze e dalla configurazione del progetto. Nome, sito e descrizione vengono dai metadati del pacchetto che il progetto usa; senza pacchetto li propone il modello. Nome e logo del marchio vengono da una raccolta pubblica già esistente, usata come registro: Simple Icons (CC0, oltre 3.400 marchi). Se il marchio manca, resta l'icona generica del tipo. Daodan non mantiene un registro proprio.

Le regole sono legate ai digest dei file che citano: se quei file cambiano, vanno rilette.

### 2. Granularità e significato

Su richiesta, il modello legge un collegamento `scrive` o `legge` e ne scrive granularità e significato. Sono legati ai digest dei due simboli e seguono la freschezza delle schede: se chi scrive cambia, l'etichetta di chi legge risulta da rileggere. Senza etichetta il campo resta vuoto: non si deduce.

Servono a vedere quando chi scrive e chi legge lo stesso store intendono granularità diverse: il caso misurato è in [`benchmarks/phazly-flow`](../../benchmarks/phazly-flow/README.md).

### 3. Lettura del flusso da parte del modello

La macchina trova dove passa un dato; cosa significa lo dice il modello, che legge la strada già tracciata e non il codice intero.

1. **Dalla domanda ai punti di partenza.** Per «dove va questo dato» il modello cerca dove il dato vive, cioè il campo del form, la chiave dello stato, la colonna o la collezione, e li consegna come punti di partenza.
2. **La macchina traccia** i collegamenti da quei punti, senza modello.
3. **Il modello riceve l'elenco dei passaggi:** nodi, tipo di nodo, tipo di collegamento ed evidenza. Apre il sorgente solo dove il dato si scrive, si legge o si trasforma.
4. **Il modello scrive la scheda del flusso:** nome, tipo (dati, UX, servizio, dispositivo, misto), rami principali e secondari, cosa accade al dato a ogni tappa, dove vive. Ogni frase cita un passaggio dell'elenco: ciò che l'elenco non contiene non entra nella scheda.
5. *Sostituito dalla [mappa del sistema](2026-11-12-mappa-del-sistema.md), sezioni 4 e 5.* **All'inizio di un progetto** il modello riceve i punti d'ingresso trovati dalla macchina e sceglie i flussi principali, con nome e tipo; gli altri restano interrogabili.

La scheda è legata ai digest dei file del flusso: si rilegge solo se uno di quei file cambia. Una riga che non cita un passaggio dell'elenco (`file:line` di un collegamento del flusso) rifiuta la scheda.

### 4. Unità

1. **Il modello legge la richiesta** e dichiara in `00-scope.md` che cosa è nominato, i punti di partenza con i riferimenti della mappa, il perimetro e il contesto. Per una funzionalità include i diversi punti d'ingresso pertinenti. Rispetta i confini che la richiesta dichiara. Chiede solo se due letture cambiano correttezza o costo.

   | La richiesta nomina | Punti di partenza | Come si forma l'unità |
   | --- | --- | --- |
   | Una cartella o un modulo | I suoi file | Per percorso del file, come oggi |
   | Una funzione | La funzione | Con chi la chiama e chi chiama |
   | Un componente dell'interfaccia | Il componente | Dal fatto mostrato a chi lo scrive; dalle azioni a chi reagisce |
   | Una funzionalità | I suoi punti d'ingresso | Seguendo i collegamenti, anche fra strati |
   | Un flusso di dati | Lo store o il fatto mostrato | Chi scrive e chi legge, anche fra strati |
   | Un aspetto (sicurezza, prestazioni, stabilità, concorrenza, leggerezza) | L'aspetto sceglie i revisori, non i file | Dai punti d'ingresso se l'aspetto segue il dato, altrimenti per percorso del file |

2. **La macchina segue i collegamenti** `chiama`, `scrive`, `legge` e `attiva` dai punti di partenza, senza limite di salti e ciascuno una volta sola, così un ciclo non si ripete. Si ferma in tre casi, con i confini e il budget di `scope_planner.py`: il collegamento esce dal confine di lettura della richiesta (`read_boundary`); un limite del budget si esaurisce (`max_edges`, `max_rounds`, `max_seconds`); il collegamento non si risolve. Ciò che non è stato seguito resta elencato, rispettivamente come fuori confine, da esplorare o lacuna, e il flusso è dichiarato incompleto. Come contesto si aggiunge solo ciò che dista un `chiama` dal flusso.
3. **Divide il perimetro in unità entro un limite di byte.**
   - Chi scrive e chi legge lo stesso dato stanno nella stessa unità. Se insieme superano il limite, il taglio è registrato e il flusso resta incompleto.
   - Un file condiviso da due flussi compare in entrambe le unità: i flussi non si fondono.
   - Un file che molti flussi toccano è membro di poche unità, in numero fissato, e contesto nelle altre: senza questo tetto i file dello stato si ripetono in quasi ogni unità (su un caso reale, il doppio dei byte).
   - I file che nessun flusso tocca vengono dopo, per percorso del file. Un file più grande del limite resta da solo, come in `pack()`.
   - Ogni file del perimetro è assegnato almeno una volta: `composition.py account` conta i file distinti e, a parte, quelli presenti in più unità.
   - Le unità mantengono i riferimenti ai collegamenti che le attraversano. I file non esaminati mantengono incompleta la copertura della review.
4. **Le unità vanno a chi le usa:** il revisore, l'esploratore, la mappa funzionale. La divisione limita i file di un incarico, non il flusso: i suoi collegamenti restano tutti consultabili.

Un flusso fra strati richiede la mappa di tutti gli strati che attraversa, con i collegamenti `chiama` presenti per i loro linguaggi.

### 5. Livelli

*Sostituita dalla [mappa del sistema](2026-11-12-mappa-del-sistema.md), sezione 2.*

Un flusso è uno solo; si guarda a livelli diversi, come le viste Logica e Fisica dell'esploratore.

| Livello | Nodi mostrati |
| --- | --- |
| Fisico | File e simboli |
| Logico | Moduli e funzionalità: i simboli dello stesso modulo si contraggono in un nodo |
| UX | Attori, azioni, schermate e fatti mostrati |
| Dati | Store, con chi scrive e chi legge |
| Misto | Nodi di livelli diversi nello stesso flusso |

Una contrazione conserva consultabili i collegamenti originali. Un simbolo senza modulo resta un simbolo: nessuna appartenenza viene inventata.

### 6. Interrogazione

`codebase_map_flows` con le regole di collegamento del progetto, registrate accanto allo snapshot, una di tre domande e un livello: `from` un punto d'ingresso (cosa deve reagire), `to` un fatto mostrato o uno store (chi lo scrive e cosa significa), `through` un nodo (quali flussi lo attraversano). La risposta elenca i collegamenti, diretti, dedotti o dichiarati, con granularità, significato, freschezza, lacune e ciò che resta da esplorare. Distingue un flusso incompleto da un flusso completo diviso in più unità.

### 7. Chi usa flussi e unità

*Sostituita dalla [mappa del sistema](2026-11-12-mappa-del-sistema.md), sezione 7.*

- **Esploratore:** un flusso scelto evidenzia i suoi nodi al livello della vista; un nodo elenca i flussi che lo attraversano. Ogni nodo mostra un'icona generica per il suo tipo e se è interno o esterno. `daodan/visual@1` ottiene un elenco `flows`.
- **Mappa funzionale:** l'elenco delle funzionalità con i loro flussi, per chi non legge il codice. `03-flows.md` si genera da qui.
- **Review:** si decide nella fase 3.

## Limiti

Analisi statica: un flusso dice cosa il codice rende possibile, non cosa avviene in esecuzione né quali percorsi seguano davvero gli utenti. Il [passo dinamico](2026-11-12-passo-dinamico.md), una proposta, aggiunge i collegamenti `chiama` osservati nei test, con la loro provenienza. Granularità e significato sono affermazioni del modello, da verificare sul sorgente. Un nodo senza codice e i collegamenti che lo toccano sono dichiarati o proposti, mai ricavati dal sorgente; dove la mappa non analizza un linguaggio, la macchina non deduce collegamenti. La parte calcolata dalla macchina si aggiorna con `snapshot.py refresh` della fase 1; quella scritta dal modello no.

## Prova

Benchmark `benchmarks/flow-model/`, soglie scritte nel README prima di ogni misura. Senza modello, tranne il punto 4. I casi reali sono [`benchmarks/polar-flow`](../../benchmarks/polar-flow/README.md), [`benchmarks/tududi-flow`](../../benchmarks/tududi-flow/README.md) e [`benchmarks/phazly-flow`](../../benchmarks/phazly-flow/README.md): ognuno dichiara i valori attesi nel suo README.

1. **File di un difetto noto.** Su un caso reale, a parità di perimetro e di limite di byte: in quanti incarichi `pack()` mette i file dei difetti attesi e in quante unità li mette la proposta. L'unione dei file distinti assegnati è identica e due esecuzioni danno le stesse unità.
2. **Fixture** di 8-10 moduli su due strati, con uno store condiviso tra due funzionalità distinte, una rotta HTTP, una violazione writer-reader e una variante lecita simile. Collegamenti trovati contro quelli attesi, con i dedotti contati a parte; verificare che le due funzionalità restino in flussi distinti. Includere campi indipendenti nello stesso store, rotte omonime in servizi diversi e identità ambigue: contare anche i collegamenti falsi e le lacune dichiarate.
3. **Caso reale fra strati.** Da un fatto mostrato il flusso arriva allo store che lo contiene, attraverso la rotta dichiarata dal caso.
4. **Etichette.** Granularità e significato su un campione di collegamenti, contro una lettura manuale; costo per collegamento.
5. **Simboli e funzionalità.** Nella fixture, una catena di almeno tre chiamate fra file diversi, un ciclo e una funzionalità con più punti d'ingresso. Partendo da un simbolo e dalla funzionalità si ritrovano i flussi attesi; si contano i file entrati in un flusso senza appartenere a quelli attesi. Con un limite di byte basso tutti i file restano assegnati, in più unità, e i collegamenti fra unità restano consultabili. Un collegamento irrisolto, un'uscita dal confine di lettura e un budget esaurito lasciano ciascuno il flusso incompleto. Un nodo senza codice, dichiarato con la sua evidenza, compare nel flusso con il collegamento marcato come dichiarato; al livello logico i simboli dello stesso modulo diventano un nodo e i collegamenti originali restano consultabili.

## Ordine di lavoro

1. Collegamenti `chiama` per i linguaggi dei casi di prova, con il conteggio di quelli risolti.
2. Regole di collegamento e collegamenti dedotti per store e azioni dell'utente.
3. Flussi senza limite di salti e unità che coprono tutto il perimetro; misure 1 e 5.
4. Collegamenti dedotti fra strati; misure 2 e 3.
5. `codebase_map_flows`, poi le etichette; misura 4.

**Da decidere alla rifinitura:** il limite di un'unità; dove si registra il tipo di un nodo; come distribuire i loghi rispettando l'avvertenza sui marchi della raccolta; se l'esploratore mostra i flussi come vista propria o sopra le viste esistenti; se le unità estendono `scope_planner.py` o nascono accanto.
