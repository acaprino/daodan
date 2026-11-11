# Benchmark: un bug di flusso reale, review per area

Prova se senior-review trova, in una review per area e non per commit, un bug reale di phazly-app: un fatto registrato sullo slot del diario (record presente) letto come fatto sul piatto del piano (piatto mangiato). Il codice di phazly-app non è copiato qui; le run e i loro artefatti restano fuori dal repository.

## Parametri

| Parametro | Valore |
|---|---|
| target | phazly-app al commit `46c92b28`, il genitore della prima fix, copiato senza storia successiva: i messaggi delle fix non sono leggibili |
| difetto atteso | G1 `react-app/src/hooks/useDayProgress.ts:190`: la riga del piano è fatta per un record qualsiasi nello slot. G2 `react-app/src/components/common/QuickAddSheet.tsx:268`: l'offerta «Dal piano» sparisce per un record qualsiasi. Fix: `b511e814`, `239819dd` |
| criterio | trovato se un finding consegnato nel rapporto afferma, con `file:line`, che un record dello slot è usato come «piatto del piano mangiato»; parziale se compare solo in un job o come lead |
| plugin | Daodan al commit `cf0ffe6`, installato dalla checkout locale |
| esecuzione | `claude -p` 2.1.319, una sessione nuova per run, modello `claude-sonnet-5-5`; strumenti: Read, Glob, Grep, Write, Edit, sotto-agenti, Skill, Bash solo per `python3`, `uv`, `git` in lettura e `ls` |
| mappa | `/codebase-map:map` lite su `react-app/` (630 file, 590 con simboli) |

## Parametri per le misure sui flussi

Questo benchmark è uno dei casi delle spec [fase 2](../../docs/specs/2026-11-09-flow-model.md) e [fase 3](../../docs/specs/2026-11-09-flows-in-review.md), sullo stesso target.

| Misura | Valore |
|---|---|
| fase 2, file di un difetto noto | i file di G1, di G2 e dei due scrittori dello stato «saltato»; con `pack()` i file di G1 sono in tre incarichi |
| fase 2, caso fra strati | dalla riga «Completato» della home il flusso arriva alla collezione `diaryDays` passando per `/getDiaryDays` |
| fase 3, richiesta | «la logica dei widget della home e dell'inserimento» |
| fase 3, perimetro | i file dei widget della home, dell'inserimento e di chi scrive lo stato che essi leggono; G2 sta nel file dell'inserimento, che i soli widget non comprendono |
| fase 3, difetti attesi | G1, G2 e lo scrittore che lascia lo stato «saltato» |
| fase 3, stima | 15-21 USD a run, da ricalibrare sul perimetro |

## Run del 2026-11-09

| Run | Richiesta | Metodo | Job | G1 | G2 | Costo | Tempo |
|---|---|---|---|---|---|---|---|
| mappa | lite di `react-app/` | analista isolato, pubblicata | 1 | – | – | 2,06 USD | 548 s |
| A | widget della home, in parole | saltato: il modello revisiona da solo e lo dichiara solo alla fine | 0 | no | no | 1,04 USD | 207 s |
| A2 | A, con il metodo nominato | si ferma sul prerequisito della mappa dell'intero progetto e propone due strade | 0 | – | – | 0,34 USD | 37 s |
| A3 | A2, con la deroga: solo `react-app` | completo, 12 job, 81 finding, 21 cluster | 12 | parziale | fuori perimetro | 15,09 USD | 981 s |
| A3b | A3 ripetuta sulla stessa copia | completo, 30 job (6 ruoli su 5 gruppi; A3 ne aveva 12) | 30 | un job, solo il caso «saltato» | fuori perimetro | 20,82 USD | 781 s |
| B | inserimento e scansione, metodo e deroga | completo, 49 job, 29 dei quali dispacciati due volte per il tetto di 20 sotto-agenti dell'host | 49 | no | no | 26,16 USD | 772 s |

- A: il revisore legge per intero il file di G1 e scrive che i tombstone sono esclusi in modo uniforme; il difetto non compare.
- A3: il job `logic-integrity` descrive G1 esattamente («uno slot che contiene solo un alimento estraneo è annunciato come completato e il piatto del piano non si può più registrare»). Il job stesso lo classifica Low. Il consolidamento lo fonde nel cluster L2 «un pasto saltato è mostrato Completato», Low, con altri cinque finding sulla stessa ancora: il caso del cibo estraneo resta tracciato in `99-consolidated.md` ma sparisce dal titolo e dal rapporto. Con rigor standard nessun Low è verificato. `QuickAddSheet` non entra nel perimetro dei widget.
- B: `QuickAddSheet` e `useDayProgress` sono nel perimetro. `01-context.md` del coordinatore afferma che non esiste un tipo «planned»: vero per il record dello slot, falso per le sue aggiunte, che hanno `type: 'planned'`. Il job che legge la riga di G2 la descrive («nasconde il tile quando lo slot ha un record») senza segnalarla.
- In A3 un job segnala lo stesso schema in `useDayLogSlots.ts` (proposta del piano solo su uno slot senza record), ancora presente nell'HEAD di phazly-app dopo le fix: da verificare con l'autore.
- Risultati di strumento in errore: 17 nella mappa (7 per permessi), 30 in A3 (16 per permessi), 64 in B (20 per permessi); il resto sono errori ordinari dei comandi. Il coordinatore di A3 dichiara che due job non hanno letto il file del proprio ruolo.

## Ripetizione di A3 (A3b)

- **Contaminata.** La cartella `.team-review/` di B era rimasta nella copia cieca: A3b l'ha letta (stato, binding, scope e un brief di job) e ha lavorato in una sottocartella. Ha ereditato il formato dei job, non risulta aver letto `01-context.md` con l'affermazione errata su `planned`. Il confronto con A3 è indicativo, non pulito.
- **Variabilità alta.** Stesso prompt, stessa mappa: roster diverso (A3b aggiunge `ui-race`, toglie `cache-consistency`) e gruppi diversi, 30 job contro 12. Un solo job su 30 tocca `useDayProgress.ts:190`, `job-01-F4`, Low, e descrive solo il caso «pasto saltato»: il caso «cibo estraneo» che A3 aveva trovato non compare. G1 non è nel rapporto.
- Una descrizione esatta di G1 su due run, in un job su 12 e 0 su 30: con questi numeri il ruolo non la trova in modo affidabile, né la perde in modo affidabile.

## Diagnosi

I reviewer vedono il difetto quando leggono chi scrive il fatto e cosa afferma la schermata; lo perdono quattro passi del metodo, non un ruolo mancante:

1. **Ingresso.** Una richiesta in parole può saltare l'intero metodo senza dichiararlo all'inizio (A).
2. **Contesto.** Un'affermazione sul modello dei dati senza livello («nessun tipo planned») si propaga a tutti i worker (B).
3. **Gravità e consolidamento.** Il reviewer valuta Low un fatto mostrato falso che blocca un'azione; il raggruppamento per ancora fonde finding con la stessa riga e trigger diversi, e il trigger più grave sparisce dal titolo (A3). Con rigor standard il risultato è lo stesso anche senza la fusione: nessuna verifica.
4. **Perimetro.** I lettori dello stesso fatto in altre aree restano fuori (G2 in A3).

Limite: due run per A, una per B, un modello, permessi ristretti. **La mappa non aveva il grafo delle chiamate TypeScript:** nell'ambiente mancava `tree-sitter`, quindi i 412 file TS e TSX di `react-app` hanno simboli e import ma nessun riferimento di chiamata (le 202 chiamate dello snapshot sono tutte Python). La Phase 0 e i job hanno lavorato con ricerca, outline e lettura; le conclusioni su perimetro e roster valgono per questa condizione. Dopo A3b il problema di partenza è la variabilità del reviewer su un difetto sottile, prima ancora del consolidamento: la correzione del punto 3 non basta se il reviewer non scrive il trigger.

## Flussi dalle regole di collegamento, 11 novembre 2026

Prima applicazione di `flows.py` a un'app reale. Regole in `rules.json` (14, scritte da Claude leggendo lo stato Zustand, il client delle API, i router FastAPI e l'accesso a MongoDB). Snapshot senza passaggio del motore, su Modal; riepilogo in `results/flow-links-summary.json`.

| Misura | Valore |
| --- | --- |
| Punti d'ingresso | 330: 219 azioni dell'utente, 111 rotte |
| Chiamate del client a una rotta | 46, tutte collegate al loro handler |
| Store | 123: 75 campi dello stato, 38 collezioni, 10 campi dello stato del planner |
| Store con chi scrive e chi legge | 64; solo scritti 41, solo letti 18 |
| Flussi | 330: 58 arrivano a uno store, 9 attraversano interfaccia e servizio, 217 restano di un solo nodo |
| Lacune dichiarate | 88: 67 letture dello stato tenuto intero in una variabile |

- 217 flussi di un solo nodo: il punto d'ingresso chiama funzioni che lo snapshot non risolve (TypeScript 26% con il motore, qui solo lessicale).
- Solo 9 flussi attraversano i due strati benché le rotte collegate siano 46: le chiamate alle API stanno in servizi e hook che le azioni raggiungono attraverso chiamate non risolte.
- `const state = useAppStore.getState()` seguito da `state.campo` non dà la chiave: 67 lacune, e campi come `favoriteFoods` risultano senza lettori.
- Le regole sono scritte da un modello che ha visto il codice, non da un modello cieco con un mandato fisso: la misura con regole scritte alla cieca resta da fare.
