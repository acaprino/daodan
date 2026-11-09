# Fase 2: flussi e unità di lavoro ricavati dal grafo

**Stato:** abbozzo, da rifinire dopo l'implementazione della [fase 1](2026-11-09-working-run-and-review-fixes.md). **Data:** 9 novembre 2026. Fase 2 di 3; l'uso nella review si decide nella [fase 3](2026-11-09-flows-in-review.md).

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

- **Il modello inferisce il perimetro, la macchina lo costruisce.** Dalla richiesta e dal contesto del progetto il modello ricava che cosa è nominato e da quali semi partire, lo dichiara in `00-scope.md` con l'evidenza e procede; chiede solo se due letture cambiano correttezza o costo, come già nella Phase 0.

  | La richiesta nomina | Semi | Taglio |
  | --- | --- | --- |
  | Una cartella o un modulo | I suoi file | Per percorso |
  | Una funzione o un simbolo | Il simbolo | Il simbolo con chiamanti e chiamati |
  | Un componente dell'interfaccia | Il componente | Ciò che mostra fino a chi lo scrive, e le sue interazioni fino a chi reagisce |
  | Una funzionalità | I suoi ingressi | Attraversamento, anche fra livelli |
  | Un flusso di dati | Lo store o il fatto | Catena di scrittori e lettori, anche fra livelli |
  | Un aspetto (sicurezza, prestazioni, stabilità, concorrenza, leggerezza) | L'aspetto sceglie i reviewer, non i file | Dagli ingressi quando l'aspetto segue il dato, altrimenti per percorso |

  Una richiesta può nominare più righe insieme: «la sicurezza del flusso di registrazione» è un aspetto su un flusso.
- **Costruzione.** Dai semi nominati nella richiesta (ingresso, store o fatto) si seguono due percorsi insieme. Il **dato**: chi lo scrive, dove passa di livello, chi lo legge, cosa mostra. L'**interazione**: l'azione dell'utente, il suo handler, gli effetti che produce, le schermate che devono reagire.
- **Archi attraversati.** Chiamate e import; legame fra un evento dell'interfaccia e il suo handler; stato condiviso, perché scrittore e lettore dello stesso store non si chiamano; collegamenti fra livelli accoppiati per nome (rotta HTTP, collezione, schema condiviso), sempre `inferito`.
- **Tetto.** Un'unità ha un limite di byte. Ciò che resta oltre il limite è la sua frontiera, dichiarata con il motivo: mai omessa in silenzio.
- **Prerequisito.** Una catena fra livelli richiede la mappa di tutti i livelli che attraversa.

Le unità sono un'opzione accanto a `pack()`; servono anche alle partizioni della mappa e all'esploratore.

## Derivazione

1. **Struttura, senza modello.** Dallo snapshot: chiamate, import, riferimenti esterni risolti, più i pattern di framework che riconoscono ingressi e store (rotte, hook di stato, collezioni, schermate). I collegamenti dinamici che il grafo non vede si cercano per nome e restano `inferito` con la loro evidenza: mai un arco certo.
2. **Significato, con il modello, a richiesta.** Un worker legge un arco e scrive livello e significato, legati ai digest dei simboli ai capi. Si rietichettano a lotti solo gli archi non più freschi, come per le schede.
3. **Freschezza.** Calcolata a ogni lettura, mai ricontrollata a tappeto: `fresh`, `stale_body`, `stale_callee`, `orphan`, `uncovered`. Un flusso è fresco se tutti i suoi archi lo sono; altrimenti la risposta segna quelli stantii. Un cambio di scrittore cambia il digest dei suoi effetti e rende `stale_callee` l'etichetta del lettore: è il segnale della deriva dopo un refactor che oggi non esiste.
4. **Aggiornamento.** Il livello macchina si ricalcola con `snapshot.py refresh` sul run di lavoro della fase 1. Il livello semantico non si rigenera da solo.

## Consumatori

- **Review.** Riceve unità e catene; se e come usarle è l'oggetto della fase 3.
- **Esploratore.** Una terza prospettiva, «Flusso», o una sovrapposizione sulla vista logica e su quella fisica: scegliere un flusso evidenzia i suoi nodi e archi; un nodo elenca i flussi che lo attraversano. I riferimenti multipli sono occorrenze visuali, come già nell'ADR. L'envelope `daodan/visual@1` ottiene un elenco `flows` di passi che riferiscono entità e relazioni esistenti; nessuna seconda tassonomia di stati.
- **Mappa funzionale.** L'elenco dei percorsi dell'utente e delle funzionalità, ciascuno con i flussi che lo realizzano e i dati che consuma, leggibile da chi non legge il codice. `03-flows.md` si genera dalla struttura invece che dalla prosa libera, così il racconto non diverge dal dato.

## Interrogazione

`codebase_map_flows`: `from` un ingresso o un'azione (in avanti: cosa deve reagire), `to` un fatto o uno store (all'indietro: chi lo scrive e con quale significato), `through` un nodo (quali flussi lo attraversano). La risposta porta passi, livello, significato, stato di freschezza, lacune e omissioni per budget dichiarate.

## Limiti dichiarati

Analisi statica: un cammino non prova il comportamento a runtime, e la strumentazione runtime resta un requisito distinto. I linguaggi senza fatti semantici non producono archi di chiamata. Le relazioni mancanti restano lacune. Il costo del livello semantico è per richiesta e non copre l'intero progetto.

## Prova

Benchmark `benchmarks/flow-model/`, soglie dichiarate nel README prima di ogni misura. Tutto senza modello, tranne le etichette.

1. **Insiemi noti di phazly-app.** I file di `G1` (lettore, helper, sanitizer, riga mostrata), di `G2` e i due scrittori dello stato «saltato»: in quanti job li mette `pack()` e in quante unità il pianificatore. Oggi `G1` è su tre job.
2. **Fixture** di 8-10 moduli su due livelli, con collegamenti via registro, stato condiviso e una rotta HTTP; catena attesa scritta a parte. Richiamo e precisione degli archi, con gli `inferito` contati a parte.
3. **Caso reale fra livelli.** Dalla riga «Completato» della home di phazly-app la catena arriva alla collezione `diaryDays` passando per `/getDiaryDays`; richiede la mappa di `react-app`, `functions-python` e `shared`.
4. **Etichette.** Livello e significato su un campione di archi, confrontati con una lettura manuale; costo per arco.

## Ordine di lavoro

1. Archi di stato condiviso e legame evento-handler per il primo framework.
2. Pianificatore di unità con tetto e frontiera; misura 1.
3. Archi fra livelli per nome; misure 2 e 3.
4. `codebase_map_flows`.
5. Etichette semantiche con freschezza; misura 4.

**Da decidere alla rifinitura:** primo framework da riconoscere (proposta: React con store Zustand, rotte FastAPI); tetto di un'unità; se «Flusso» nell'esploratore è una terza prospettiva o una sovrapposizione; se il pianificatore estende `scope_planner.py` o nasce accanto.
