# Flussi nella mappa: dati, attività e percorsi dell'utente

**Stato:** proposta, da approvare. **Data:** 9 novembre 2026.

Codebase Map deve rispondere a due domande che oggi non sa trattare: «chi scrive il dato che questa schermata mostra, e con quale significato?» e «cosa succede, passo per passo, quando l'utente fa questo?». La risposta è un solo modello, i flussi, con tre consumatori: la review, l'esploratore visuale e la mappa funzionale dell'applicativo per chi non legge il codice. Riapre l'esclusione dei flussi nel [FRD](../frd/2026-11-07-codebase-explorer.md) e nell'[ADR](../adr/2026-11-07-codebase-explorer.md) dell'esploratore, che la rimandavano a una scelta dell'utente.

## Comportamento attuale

- La Phase 3 produce `03-flows.md`: percorsi critici, data flow ed end-to-end in prosa e Mermaid, al massimo cinque diagrammi per categoria, per partizione. Non è interrogabile e non ha un'unità ripetibile.
- La Phase 0 della review risolve la richiesta in una lista di file (`codebase_map_graph` un salto alla volta). `03-flows.md` entra solo nel contesto della review leggera.
- Nessuno strumento risponde a «chi scrive questo dato» o «cosa deve reagire a questa azione». I link dinamici (provider, DI, registri) il grafo non li vede.
- Esito misurato in [`benchmarks/phazly-flow`](../../benchmarks/phazly-flow/README.md): un bug reale di provenienza (un record di slot letto come «piatto mangiato») è sfuggito alla review per area in quattro run su cinque, perché nessuno vedeva insieme scrittori e lettori dello stesso dato.

## Il modello

**Un flusso è un cammino su entità già esistenti, non un'entità nuova.** Usa gli stessi riferimenti canonici di snapshot, moduli e schede, e quindi di `daodan/visual@1` dell'esploratore: lo stesso nodo resta riconoscibile fra le viste.

| Elemento | Contenuto minimo |
| --- | --- |
| Passo | Coppia ordinata di riferimenti canonici, tipo, `file:line`, digest dei due capi, stato |
| Tipo di passo | `chiama`, `scrive`, `legge`, `invia`, `riceve`, `naviga` (azione dell'utente verso una schermata) |
| Ingresso | Un simbolo o file che avvia un flusso: rotta, comando, schermata o azione dell'interfaccia, job, consumer di coda |
| Store | Dove un dato vive: tabella o collezione, stato globale, file, cache, topic |
| Fatto | Un valore o testo che l'applicativo mostra o emette, con il simbolo che lo calcola |
| Livello (su `scrive` e `legge`) | L'unità del dato: per esempio slot, singolo alimento, utente |
| Significato (su `scrive` e `legge`) | Una frase: cosa afferma il record o il valore |

`livello` e `significato` sono ciò che mancava nel caso phazly: lo scrittore registra un fatto di livello slot, il lettore lo usa come fatto di livello alimento. Senza etichetta il campo resta `non letto`: mai dedotto.

**Una famiglia, una struttura.** Il flusso tecnico (richiesta e risposta), quello dei dati (provenienza e consumo di uno store) e il percorso dell'utente (azioni verso un obiettivo) sono lo stesso grafo di passi. La famiglia è l'etichetta della radice: un ingresso, uno store o un obiettivo funzionale.

## Unità di lavoro

Il lavoro di analisi si taglia attraversando il grafo, non ordinando i file. Oggi `pack()` della review ordina per percorso e chiude un gruppo a 120.000 byte, e la mappa a team divide per manifest, layer o linguaggio: nelle run di `benchmarks/phazly-flow` chi scrive, chi legge e chi mostra lo stesso dato sono finiti in tre job diversi.

- **La richiesta decide il taglio.** Una cartella o un modulo nominati esplicitamente restano il perimetro, tagliato per percorso. Una richiesta su un flusso, un fatto o un'azione ha come perimetro la catena, trasversale a moduli e livelli (interfaccia, servizio, dati).
- **Costruzione.** Dai semi nominati nella richiesta (ingresso, store o fatto) si attraversano tre tipi di arco: chiamate e import; stato condiviso, perché scrittore e lettore dello stesso store non si chiamano; collegamenti fra livelli accoppiati per nome (rotta HTTP, collezione, schema condiviso), sempre `inferito`.
- **Tetto.** Un'unità ha un limite di byte. Ciò che resta oltre il limite è la sua frontiera, dichiarata con il motivo: mai omessa in silenzio.
- **Prerequisito.** Una catena fra livelli richiede la mappa di tutti i livelli che attraversa.

Le unità sono un'opzione accanto a `pack()`; servono anche alle partizioni della mappa e all'esploratore.

## Derivazione

1. **Struttura, senza modello.** Dallo snapshot: chiamate, import, riferimenti esterni risolti, più i pattern di framework che riconoscono ingressi e store (rotte, hook di stato, collezioni, schermate). I collegamenti dinamici che il grafo non vede si cercano per nome e restano `inferito` con la loro evidenza: mai un arco certo.
2. **Significato, con il modello, a richiesta.** Un worker legge un arco e scrive livello e significato, legati ai digest dei simboli ai capi. Si rietichettano a lotti solo gli archi non più freschi, come per le schede.
3. **Freschezza.** Calcolata a ogni lettura, mai ricontrollata a tappeto: `fresh`, `stale_body`, `stale_callee`, `orphan`, `uncovered`. Un flusso è fresco se tutti i suoi archi lo sono; altrimenti la risposta segna quelli stantii. Un cambio di scrittore cambia il digest dei suoi effetti e rende `stale_callee` l'etichetta del lettore: è il segnale della deriva dopo un refactor che oggi non esiste.
4. **Aggiornamento.** Il livello macchina si ricalcola con lo snapshot incrementale (`write --reuse`), dal comando o dall'hook `PostToolUse` descritto a parte. Il livello semantico non si rigenera da solo.

## Consumatori

- **Review.** Per una richiesta su un fatto o un'azione la Phase 0 produce, oltre ai file, la catena: store, scrittori, lettori, livello. La catena entra in `01-context.md` come invarianti da verificare, con il livello dichiarato: nessuna affermazione sul modello dei dati senza il suo livello. I lettori dello stesso store fuori dal perimetro entrano nel contesto e nel perimetro come lettori da giudicare. `logic-integrity` resta il reviewer.
- **Esploratore.** Una terza prospettiva, «Flusso», o una sovrapposizione sulla vista logica e su quella fisica: scegliere un flusso evidenzia i suoi nodi e archi; un nodo elenca i flussi che lo attraversano. I riferimenti multipli sono occorrenze visuali, come già nell'ADR. L'envelope `daodan/visual@1` ottiene un elenco `flows` di passi che riferiscono entità e relazioni esistenti; nessuna seconda tassonomia di stati.
- **Mappa funzionale.** L'elenco dei percorsi dell'utente e delle funzionalità, ciascuno con i flussi che lo realizzano e i dati che consuma, leggibile da chi non legge il codice. `03-flows.md` si genera dalla struttura invece che dalla prosa libera, così il racconto non diverge dal dato.

## Interrogazione

`codebase_map_flows`: `from` un ingresso o un'azione (in avanti: cosa deve reagire), `to` un fatto o uno store (all'indietro: chi lo scrive e con quale significato), `through` un nodo (quali flussi lo attraversano). La risposta porta passi, livello, significato, stato di freschezza, lacune e omissioni per budget dichiarate.

## Limiti dichiarati

Analisi statica: un cammino non prova il comportamento a runtime, e la strumentazione runtime resta un requisito distinto. I linguaggi senza fatti semantici non producono archi di chiamata. Le relazioni mancanti restano lacune. Il costo del livello semantico è per richiesta e non copre l'intero progetto.

## Prova

Benchmark `benchmarks/flow-model/`, criterio dichiarato prima della run.

1. **Fixture** di 8-10 moduli con collegamenti via registro o iniezione, non per import diretto; due semi: un lettore con livello sbagliato (il caso phazly) e un'azione che non invalida un suo lettore. Catena attesa scritta a parte.
2. **Derivazione.** Archi ricostruiti contro la catena attesa: richiamo e precisione, collegamenti dinamici segnati `inferito`. Costo della derivazione strutturale e di quella semantica.
3. **Review.** Stessa richiesta con e senza catena, due run ciascuna: la catena resta se fa trovare almeno un seme che il metodo attuale non trova, a costo entro due volte.
4. **Caso reale.** La catena dello store del diario di phazly-app al commit prima della correzione contiene i due lettori `G1` e `G2` di `benchmarks/phazly-flow`.

## Ordine di lavoro

1. **Ciò che è deciso e usa meccanismi esistenti.** Hook `PostToolUse` che aggiorna il livello macchina in un run dedicato; quattro correzioni al metodo di review emerse da `benchmarks/phazly-flow` (ingresso, livello nel contesto, gravità, cluster per ancora e trigger).
2. **Identificare i pezzi dal grafo e dall'analisi semantica.** Archi di stato condiviso e fra livelli, pianificatore di unità, etichette di livello e significato. Prima misura, senza modello: in quante unità finiscono gli insiemi noti di phazly-app, con `pack()` e con le unità. Poi `codebase_map_flows`.
3. **Decidere se aiutano l'analisi.** La stessa review in tre versioni, con roster fisso e due run ciascuna: gruppi per percorso, unità sul grafo, gruppi per percorso con la catena nel contesto. Qui si misurano anche le correzioni del punto 1 e il canale testuale di schede ed etichette nell'indice.

**Da decidere:** quali framework riconoscere per primi (React e hook di stato, rotte HTTP Python e TypeScript); se «Flusso» è una terza prospettiva o una sovrapposizione.
