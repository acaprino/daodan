# Fase 2: flussi e unità ricavati dal grafo

**Stato:** abbozzo, da rifinire dopo la [fase 1](2026-11-09-working-run-and-review-fixes.md). **Data:** 9 novembre 2026; aggiornata l'11 novembre 2026. Fase 2 di 3; l'uso nella review si decide nella [fase 3](2026-11-09-flows-in-review.md).

Codebase Map deve saper rispondere a due domande: «chi scrive il dato che l'applicativo mostra o restituisce, e cosa significa?» e «cosa succede quando arriva questa azione o questa richiesta?». Vale per qualsiasi app o servizio: i casi concreti stanno nei README dei benchmark. Riapre l'esclusione dei flussi nel [FRD](../frd/2026-11-07-codebase-explorer.md) e nell'[ADR](../adr/2026-11-07-codebase-explorer.md) dell'esploratore.

## Parole

Ogni parola ha un solo significato in queste tre spec.

| Parola | Significato |
| --- | --- |
| Collegamento | Da un simbolo a un altro, con tipo e `file:line`. **Diretto** se sta nel codice (chiamata, import). **Dedotto** se una regola di collegamento riconosce lo stesso dato o la stessa rotta in chi offre e in chi usa |
| Tipo di collegamento | `chiama`, `scrive`, `legge`, `attiva` (un'azione dell'utente attiva il suo handler) |
| Flusso | Sequenza ordinata di collegamenti, da un punto d'ingresso a un fatto mostrato |
| Punto d'ingresso | Dove un flusso comincia: rotta, comando, azione dell'utente, lavoro pianificato |
| Store | Dove un dato vive: stato globale, tabella o collezione, file, cache |
| Fatto mostrato | Un valore o un testo che l'applicativo mostra o restituisce |
| Granularità | Ciò a cui un dato si riferisce: un ordine, una sua riga, un utente |
| Significato | Una frase: cosa afferma quel dato |
| Strato | Interfaccia, servizio, dati |
| Perimetro | I file che un lavoro copre: quelli che un run mappa, quelli che una review giudica |
| Contesto | I file che si consultano per giudicare il perimetro, senza giudicarli |
| Unità | I file affidati a un revisore in un solo incarico |
| Punto di partenza | Ciò che la richiesta nomina e da cui si comincia a seguire i collegamenti |
| Revisore | Chi esamina un incarico seguendo un mandato: logica, sicurezza, e così via |
| Regola di collegamento | Come, in questo progetto, si riconosce chi offre e chi usa uno store o una rotta |

Un flusso non è un'entità nuova: usa i simboli che la mappa e l'esploratore hanno già, con gli stessi riferimenti.

## Comportamento attuale

- `03-flows.md` descrive i flussi in prosa e diagrammi, al massimo cinque per categoria. Non si può interrogare e la review non lo legge.
- La review divide i file con `pack()`: ordine per percorso del file, un gruppo ogni 120.000 byte. Nelle run di [`benchmarks/phazly-flow`](../../benchmarks/phazly-flow/README.md) chi scrive, chi legge e chi mostra lo stesso dato sono finiti in tre incarichi diversi; la mappa di quelle run non aveva collegamenti `chiama` per TypeScript.
- Nessuno strumento risponde a «chi scrive questo dato». Due simboli che usano lo stesso store non si chiamano, quindi il grafo non li collega.
- La [rassegna della letteratura](../research/2026-11-09-flow-reconstruction-literature.md) riporta tre fatti utili: i collegamenti dedotti si ottengono elencando chi offre e chi usa e accoppiandoli per nome (in un caso misurato, 135 trovati su 153); la qualità dei collegamenti conta più del modo di raggrupparli; dare al modello tutto il vicinato a due salti fa peggio che non darlo. Nessun lavoro verificato unisce i tre strati in un grafo né confronta il significato fra chi scrive e chi legge.

## Proposta

### 1. Collegamenti dedotti

1. Il modello legge il progetto una volta e scrive le regole di collegamento. Una regola ha questa forma: «lo stato globale si legge con `<hook>`», «le chiamate al servizio passano da `<client>`, con gli URL di `<file>`», «la tabella `<nome>` si scrive solo da `<modulo>`».
2. La macchina applica le regole a tutto il sorgente: elenca chi offre e chi usa, e li accoppia sull'identità riconosciuta. Ogni regola precisa cosa confrontare: store o collezione e campo/chiave del dato; servizio, metodo e URL per una rotta. Condividere lo store o il solo nome non basta: scrivere `store.theme` non collega a chi legge `store.cart`.
3. Ogni coppia riconosciuta diventa un collegamento dedotto, con la sua evidenza. Identità ambigue, accessi dinamici non risolti e accessi spaiati restano lacune dichiarate: non diventano collegamenti.

Le regole sono legate ai digest dei file che citano: se quei file cambiano, vanno rilette.

### 2. Granularità e significato

Su richiesta, il modello legge un collegamento `scrive` o `legge` e ne scrive granularità e significato. Sono legati ai digest dei due simboli e seguono la freschezza delle schede: se chi scrive cambia, l'etichetta di chi legge risulta da rileggere. Senza etichetta il campo resta vuoto: non si deduce.

Servono a vedere quando chi scrive e chi legge lo stesso store intendono granularità diverse: il caso misurato è in [`benchmarks/phazly-flow`](../../benchmarks/phazly-flow/README.md).

### 3. Unità

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
3. **Divide il perimetro in unità entro un limite di byte.** I file entrano nell'ordine in cui i flussi li incontrano, con i punti di partenza ordinati per riferimento; i file che nessun flusso tocca vengono dopo, per percorso del file. Una nuova unità comincia quando il file successivo supererebbe il limite; un file più grande del limite resta da solo, come in `pack()`. Le unità mantengono i riferimenti ai collegamenti che le attraversano. Ogni file del perimetro resta assegnato e i file non esaminati mantengono incompleta la copertura della review.
4. **Le unità vanno a chi le usa:** il revisore, l'esploratore, la mappa funzionale. La divisione limita i file di un incarico, non il flusso: i suoi collegamenti restano tutti consultabili.

Un flusso fra strati richiede la mappa di tutti gli strati che attraversa, con i collegamenti `chiama` presenti per i loro linguaggi.

### 4. Interrogazione

`codebase_map_flows` con una di tre domande: `from` un punto d'ingresso (cosa deve reagire), `to` un fatto mostrato o uno store (chi lo scrive e cosa significa), `through` un simbolo (quali flussi lo attraversano). La risposta elenca i collegamenti, diretti o dedotti, con granularità, significato, freschezza, lacune e ciò che resta da esplorare. Distingue un flusso incompleto da un flusso completo diviso in più unità.

### 5. Chi usa flussi e unità

- **Esploratore:** un flusso scelto evidenzia i suoi simboli; un simbolo elenca i flussi che lo attraversano. `daodan/visual@1` ottiene un elenco `flows`.
- **Mappa funzionale:** l'elenco delle funzionalità con i loro flussi, per chi non legge il codice. `03-flows.md` si genera da qui.
- **Review:** si decide nella fase 3.

## Limiti

Analisi statica: un flusso dice cosa il codice rende possibile, non cosa avviene in esecuzione. Granularità e significato sono affermazioni del modello, da verificare sul sorgente. La parte calcolata dalla macchina si aggiorna con `snapshot.py refresh` della fase 1; quella scritta dal modello no.

## Prova

Benchmark `benchmarks/flow-model/`, soglie scritte nel README prima di ogni misura. Senza modello, tranne il punto 4. I casi reali sono [`benchmarks/polar-flow`](../../benchmarks/polar-flow/README.md), [`benchmarks/tududi-flow`](../../benchmarks/tududi-flow/README.md) e [`benchmarks/phazly-flow`](../../benchmarks/phazly-flow/README.md): ognuno dichiara i valori attesi nel suo README.

1. **File di un difetto noto.** Su un caso reale, a parità di perimetro e di limite di byte: in quanti incarichi `pack()` mette i file dei difetti attesi e in quante unità li mette la proposta. L'unione dei file assegnati è identica e due esecuzioni danno le stesse unità.
2. **Fixture** di 8-10 moduli su due strati, con uno store condiviso e una rotta HTTP. Collegamenti trovati contro quelli attesi, con i dedotti contati a parte. Includere campi indipendenti nello stesso store, rotte omonime in servizi diversi e identità ambigue: contare anche i collegamenti falsi e le lacune dichiarate.
3. **Caso reale fra strati.** Da un fatto mostrato il flusso arriva allo store che lo contiene, attraverso la rotta dichiarata dal caso.
4. **Etichette.** Granularità e significato su un campione di collegamenti, contro una lettura manuale; costo per collegamento.
5. **Simboli e funzionalità.** Nella fixture, una catena di almeno tre chiamate fra file diversi, un ciclo e una funzionalità con più punti d'ingresso. Partendo da un simbolo e dalla funzionalità si ritrovano i flussi attesi; si contano i file entrati in un flusso senza appartenere a quelli attesi. Con un limite di byte basso tutti i file restano assegnati, in più unità, e i collegamenti fra unità restano consultabili. Un collegamento irrisolto, un'uscita dal confine di lettura e un budget esaurito lasciano ciascuno il flusso incompleto.

## Ordine di lavoro

1. Collegamenti `chiama` per i linguaggi dei casi di prova, con il conteggio di quelli risolti.
2. Regole di collegamento e collegamenti dedotti per store e azioni dell'utente.
3. Flussi senza limite di salti e unità che coprono tutto il perimetro; misure 1 e 5.
4. Collegamenti dedotti fra strati; misure 2 e 3.
5. `codebase_map_flows`, poi le etichette; misura 4.

**Da decidere alla rifinitura:** il limite di un'unità; se l'esploratore mostra i flussi come vista propria o sopra le viste esistenti; se le unità estendono `scope_planner.py` o nascono accanto.
