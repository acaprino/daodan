# Fase 2: flussi e unità ricavati dal grafo

**Stato:** abbozzo, da rifinire dopo la [fase 1](2026-11-09-working-run-and-review-fixes.md). **Data:** 9 novembre 2026. Fase 2 di 3; l'uso nella review si decide nella [fase 3](2026-11-09-flows-in-review.md).

Codebase Map deve saper rispondere a due domande: «chi scrive il dato che questa schermata mostra, e cosa significa?» e «cosa succede quando l'utente fa questa azione?». Riapre l'esclusione dei flussi nel [FRD](../frd/2026-11-07-codebase-explorer.md) e nell'[ADR](../adr/2026-11-07-codebase-explorer.md) dell'esploratore.

## Parole

Ogni parola ha un solo significato in queste tre spec.

| Parola | Significato |
| --- | --- |
| Collegamento | Da un simbolo a un altro, con tipo e `file:line`. **Diretto** se sta nel codice (chiamata, import). **Dedotto** se si ricava accoppiando nomi: stesso store, stessa rotta, stessa collezione |
| Tipo di collegamento | `chiama`, `scrive`, `legge`, `attiva` (un'azione dell'utente attiva il suo handler) |
| Flusso | Sequenza ordinata di collegamenti, da un punto d'ingresso a un fatto mostrato |
| Punto d'ingresso | Dove un flusso comincia: rotta, comando, azione dell'utente, lavoro pianificato |
| Store | Dove un dato vive: stato globale, tabella o collezione, file, cache |
| Fatto mostrato | Un valore o un testo che l'applicativo mostra o restituisce |
| Granularità | L'unità a cui un dato si riferisce: uno slot, un singolo alimento, un utente |
| Significato | Una frase: cosa afferma quel dato |
| Strato | Interfaccia, servizio, dati |
| Unità | I file affidati a un revisore in un solo incarico |
| Punto di partenza | Ciò che la richiesta nomina e da cui si comincia a seguire i collegamenti |
| Revisore | Chi esamina un incarico seguendo un mandato: logica, sicurezza, e così via |
| Regola di collegamento | Come, in questo progetto, si riconosce chi offre e chi usa uno store o una rotta |

Un flusso non è un'entità nuova: usa i simboli che la mappa e l'esploratore hanno già, con gli stessi riferimenti.

## Comportamento attuale

- `03-flows.md` descrive i flussi in prosa e diagrammi, al massimo cinque per categoria. Non si può interrogare e la review non lo legge.
- La review divide i file con `pack()`: ordine per percorso, un gruppo ogni 120.000 byte. Nelle run di [`benchmarks/phazly-flow`](../../benchmarks/phazly-flow/README.md) chi scrive, chi legge e chi mostra lo stesso dato sono finiti in tre incarichi diversi.
- Nessuno strumento risponde a «chi scrive questo dato». Due simboli che usano lo stesso store non si chiamano, quindi il grafo non li collega.
- La [rassegna della letteratura](../research/2026-11-09-flow-reconstruction-literature.md) riporta tre fatti utili: i collegamenti dedotti si ottengono elencando chi offre e chi usa e accoppiandoli per nome (in un caso misurato, 135 trovati su 153); la qualità dei collegamenti conta più del modo di raggrupparli; dare al modello tutto il vicinato a due salti fa peggio che non darlo. Nessun lavoro verificato unisce i tre strati in un grafo né confronta il significato fra chi scrive e chi legge.

## Proposta

### 1. Collegamenti dedotti

1. Il modello legge il progetto una volta e scrive le regole di collegamento. Esempi: «lo stato globale si legge con `useAppStore`», «le chiamate al servizio passano da `apiPostUnwrap` con gli URL di `config/api.ts`».
2. La macchina applica le regole a tutto il sorgente: elenca chi offre e chi usa, e li accoppia per nome.
3. Ogni coppia diventa un collegamento dedotto, con la sua evidenza. Ciò che resta spaiato è contato e dichiarato.

Le regole sono legate ai digest dei file che citano: se quei file cambiano, vanno rilette.

### 2. Granularità e significato

Su richiesta, il modello legge un collegamento `scrive` o `legge` e ne scrive granularità e significato. Sono legati ai digest dei due simboli e seguono la freschezza delle schede: se chi scrive cambia, l'etichetta di chi legge risulta da rileggere. Senza etichetta il campo resta vuoto: non si deduce.

Nel caso phazly chi scrive registra un fatto per slot e chi legge lo usa come fatto per singolo alimento: due granularità diverse sullo stesso store.

### 3. Unità

1. **Il modello legge la richiesta** e dichiara in `00-scope.md` che cosa è nominato e i punti di partenza. Chiede solo se due letture cambiano correttezza o costo.

   | La richiesta nomina | Punti di partenza | Come si forma l'unità |
   | --- | --- | --- |
   | Una cartella o un modulo | I suoi file | Per percorso, come oggi |
   | Una funzione | La funzione | Con chi la chiama e chi chiama |
   | Un componente dell'interfaccia | Il componente | Dal fatto mostrato a chi lo scrive; dalle azioni a chi reagisce |
   | Una funzionalità | I suoi punti d'ingresso | Seguendo i collegamenti, anche fra strati |
   | Un flusso di dati | Lo store o il fatto mostrato | Chi scrive e chi legge, anche fra strati |
   | Un aspetto (sicurezza, prestazioni, stabilità, concorrenza, leggerezza) | L'aspetto sceglie i revisori, non i file | Dai punti d'ingresso se l'aspetto segue il dato, altrimenti per percorso |

2. **La macchina segue i collegamenti** dai punti di partenza: un salto lungo `chiama`; senza limite di salti lungo `scrive`, `legge` e `attiva`.
3. **Si ferma a un limite di byte.** I file che non entrano sono elencati con il motivo.
4. **L'unità va a chi la usa:** il revisore, l'esploratore, la mappa funzionale.

Un flusso fra strati richiede la mappa di tutti gli strati che attraversa, con i collegamenti `chiama` presenti per i loro linguaggi. Nel run di phazly usato dal benchmark i 412 file TypeScript non ne avevano, perché nell'ambiente mancava `tree-sitter`.

### 4. Interrogazione

`codebase_map_flows` con una di tre domande: `from` un punto d'ingresso (cosa deve reagire), `to` un fatto mostrato o uno store (chi lo scrive e cosa significa), `through` un simbolo (quali flussi lo attraversano). La risposta elenca i collegamenti, diretti o dedotti, con granularità, significato, freschezza e ciò che è rimasto fuori.

### 5. Chi usa flussi e unità

- **Esploratore:** un flusso scelto evidenzia i suoi simboli; un simbolo elenca i flussi che lo attraversano. `daodan/visual@1` ottiene un elenco `flows`.
- **Mappa funzionale:** l'elenco delle funzionalità con i loro flussi, per chi non legge il codice. `03-flows.md` si genera da qui.
- **Review:** si decide nella fase 3.

## Limiti

Analisi statica: un flusso dice cosa il codice rende possibile, non cosa avviene in esecuzione. Granularità e significato sono affermazioni del modello, da verificare sul sorgente. La parte calcolata dalla macchina si aggiorna con `snapshot.py refresh` della fase 1; quella scritta dal modello no.

## Prova

Benchmark `benchmarks/flow-model/`, soglie scritte nel README prima di ogni misura. Senza modello, tranne il punto 4.

1. **File noti di phazly-app.** In quanti incarichi `pack()` mette i file di `G1`, di `G2` e dei due scrittori dello stato «saltato», e in quante unità li mette la proposta. Oggi `G1` è in tre incarichi.
2. **Fixture** di 8-10 moduli su due strati, con uno store condiviso e una rotta HTTP. Collegamenti trovati contro quelli attesi, con i dedotti contati a parte.
3. **Caso reale fra strati.** Dalla riga «Completato» della home di phazly-app il flusso arriva alla collezione `diaryDays` passando per `/getDiaryDays`.
4. **Etichette.** Granularità e significato su un campione di collegamenti, contro una lettura manuale; costo per collegamento.

## Ordine di lavoro

1. Collegamenti `chiama` per TypeScript nell'ambiente di prova, con il conteggio di quelli risolti.
2. Regole di collegamento e collegamenti dedotti per store e azioni dell'utente.
3. Unità con limite ed elenco degli esclusi; misura 1.
4. Collegamenti dedotti fra strati; misure 2 e 3.
5. `codebase_map_flows`, poi le etichette; misura 4.

**Da decidere alla rifinitura:** il limite di un'unità; se l'esploratore mostra i flussi come vista propria o sopra le viste esistenti; se le unità estendono `scope_planner.py` o nascono accanto.
