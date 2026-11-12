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

## Flussi dalle regole di collegamento, 11-12 novembre 2026

Prima applicazione di `flows.py` a un'app reale, su Modal. Riepiloghi in `results/` (`python benchmarks/phazly-flow/summarize.py LINKS.json`).

### Con e senza il passaggio del motore

`rules.json`: 18 regole scritte da Claude leggendo lo stato Zustand, il client delle API, i router FastAPI e l'accesso a MongoDB.

| Misura | Solo lessicale | Con il motore |
| --- | --- | --- |
| Punti d'ingresso | 235: 124 azioni, 111 rotte | gli stessi |
| Chiamate del client collegate a una rotta | 46 su 46 | 46 su 46 |
| Store | 123: 75 campi dello stato, 38 collezioni, 10 campi del planner | gli stessi |
| Store con chi scrive e chi legge | 85 | 85 |
| Collegamenti `chiama` diretti | 6.704 | 12.688 |
| Flussi che arrivano a uno store | 62 | 132 |
| Flussi fra interfaccia e servizio | 11 | 16 |
| Flussi di un solo nodo | 119 | 60 |
| Lacune dichiarate | 33 | 33 |

- **Caso fra strati (misura 3 della fase 2).** Con il motore, da `QuickAddSheet` il flusso a ritroso arriva alla collezione `diaryDays` passando per `POST /getDiaryDays`. Da `useDayProgress` arriva a `POST /getPlanForDate` e a nessuna collezione: riuscita per G2, non per G1.
- Senza il motore 119 flussi restano di un solo nodo: le rotte chiamano i servizi come attributo di un modulo importato, le azioni chiamano funzioni ricevute o importate con un alias di percorso.
- Lacune restanti: 13 letture dello stato con un selettore non letterale, 5 scritture con chiave calcolata, 15 chiamate fuori da un simbolo con nome o con rotta calcolata.

### Regole scritte alla cieca

`rules-blind.json`: 17 regole scritte da un agente senza contesto, con il solo formato e il sorgente, in circa 14 letture. Così come scritte sono rifiutate: `strip` stava dentro `route`. Misurate dopo aver spostato quel campo, senza altre modifiche, sullo snapshot lessicale e con `flows.py` al commit `7db9b003b`, contro le 14 regole di `rules.json` di quel commit.

| Misura | `rules.json` | `rules-blind.json` |
| --- | --- | --- |
| Punti d'ingresso | 234 | 234 |
| Chiamate del client collegate a una rotta | 46 | 32 |
| Store | 123 | 123, gli stessi |
| Store con chi scrive e chi legge | 70 | 68 |
| Flussi che arrivano a uno store | 59 | 59 |
| Lacune dichiarate | 60 | 57 |

- Un modello scrive le regole da solo: le colonne differiscono solo sulle rotte. L'agente ha nominato il client delle API come funzione del progetto (`callee`), che non vale per le chiamate importate con un alias di percorso; `written` le prende tutte.
- Il suo elenco «non esprimibile» ha dato quattro correzioni, ciascuna con un test in `tests/test_codebase_map_flows.py`: il selettore passato da un wrapper, la collezione tenuta in una variabile (`holder`), il campo sconosciuto rifiutato per nome, il valore chiamabile nominato da `callee`. Restano non esprimibili: `fetch` con il metodo nell'oggetto delle opzioni, il prefisso di rotta aggiunto dal servizio, la collezione scelta a runtime.

### File di un difetto noto (misura 1 della fase 2)

Perimetro `react-app/src` senza i test, 568 file, limite di 120.000 byte, collegamenti con il motore. Per G1 e per G2 si contano il file del difetto e i file di chi scrive gli store che esso legge: 4 file ciascuno. «Condivisione» è il numero massimo di unità di cui un file è membro; nelle altre è contesto, da consultare e non da giudicare (`flows.py units --share`).

| | `pack()` | Unità, condivisione libera | Unità, condivisione 2 | Unità, condivisione 1 |
| --- | --- | --- | --- | --- |
| Incarichi | 34 | 79 | 39 | 34 |
| File in più unità | 0 | 79 | 52 | 0 |
| Byte inviati sul perimetro | 1,00 | 2,09 | 1,12 | 1,00 |
| G1: file nell'unità del difetto, membri | i 4 file in 3 incarichi | 2 | 1 | 1 |
| G1: con il contesto | | 2 | 3 | 4 |
| G2: file nell'unità del difetto, membri | i 4 file in 3 incarichi | 3 | 1 | 1 |
| G2: con il contesto | | 3 | 4 | 3 |
| Due esecuzioni | uguali | uguali | uguali | uguali |

- Con la condivisione libera i file dello stato, che ogni flusso tocca, si ripetono in quasi tutte le unità: il doppio dei byte.
- Con condivisione 2 il costo torna vicino a `pack()` (1,12) e l'unità del difetto nomina come contesto i file di chi scrive il suo dato: 3 su 4 per G1, 4 su 4 per G2. Con `pack()` quei file stanno in tre incarichi senza che uno nomini gli altri.
- Se il contesto basti al revisore per trovare il difetto è la domanda della fase 3, che richiede run di review.
- Tutti i 568 file sono assegnati in ogni colonna. Circa 2.500 collegamenti restano fra unità diverse.

### Etichette di granularità e significato (misura 4 della fase 2), 12 novembre 2026

Un agente senza contesto riceve coppie «chi scrive / chi legge» uscite da `flows.py` (store, lettore con `file:line`, scrittori con `file:line`) e il sorgente; per ogni coppia scrive cosa significa una voce per chi scrive, cosa assume chi legge, e se sono coerenti, con le righe che lo provano. Nessun altro contesto, nessun accenno ai difetti attesi. Voci e risposte in `results/`.

| Giro | Coppie | Fra cui | Coerenti | Incoerenti | Letture |
| --- | --- | --- | --- | --- | --- |
| 1 (`label-items.json`, `labels.json`) | 20, estratte a caso con seme fisso più le due di G1 e G2 | G1 (n. 17), G2 (n. 10) | 19 | 1 (n. 5) | 41 file |
| 2 (`relabel-items.json`, `relabels.json`) | 6: G1, G2 e 4 controlli, con l'elenco completo degli scrittori | G1 (n. 5), G2 (n. 1) | 6 | 0 | 22 file |

- **I due difetti noti non sono trovati, in nessuno dei due giri.**
  - Nel giro 1 mancava lo scrittore che produce il caso del difetto, `addMealAddition` (un cibo fuori piano nello slot): un commento con un apostrofo dentro `set(...)` rompeva la lettura degli argomenti. Corretto in `flows.py` (`mask_comments`, con test); l'elenco degli scrittori di `completedMeals` passa da 8 a 12.
  - Nel giro 2, con l'elenco completo: per G1 l'agente segue la lettura fino al conteggio dei pasti registrati (`useDayProgress.ts:86`) e non fino alla riga che mostra il piatto del piano come mangiato (`useDayProgress.ts:190`). Per G2 vede il comportamento (l'offerta del piano sparisce per qualsiasi record nello slot) e lo giudica corretto: decidere che è un difetto richiede di sapere cosa l'offerta deve significare.
- La coppia n. 5 del giro 1 è una pista nuova, non verificata: spegnendo e riaccendendo gli slot di allenamento lo spuntino torna con id `afternoon_snack` (`types/index.ts:246`) invece di `snack` (`types/index.ts:263`), e i giorni registrati sotto `snack` mostrano lo slot vuoto più una riga orfana (`useDayLogSlots.ts:95`, `useDayLogSlots.ts:98-115`).
- La coppia n. 12 del giro 1 era un collegamento falso: `getFavoritesByMealSlot` non legge `foodStack`. Lo stato tenuto in una variabile veniva letto fino alla fine della funzione esterna; ora solo nella funzione che lo dichiara (con test).
- Soglia della misura, 16 concordanze su 20 con una lettura manuale: non valutata, perché la lettura manuale di tutte le 20 coppie non è stata fatta; sulle due coppie dei difetti la concordanza è 0 su 2.
- Il prompt non è stato adattato a G1 e G2: sarebbe overfitting su questo caso. Ciò che la misura indica è un limite: un'etichetta per coppia giudica il dato dove viene letto, non dove il lettore lo trasforma in un fatto mostrato, e non conosce l'intento del prodotto.

### Scheda del flusso scritta dal modello, 12 novembre 2026

Un agente senza contesto riceve i passaggi del flusso «ripristino dell'account» (`RestoreAccountModal.handleRestore`, 74 collegamenti con il motore, dall'interfaccia alle collezioni `users` e `deletionAuditLog`) e il sorgente, e scrive la scheda nel formato di `codebase_map_flows(card=...)`. Passaggi e scheda in `results/card-restore-account*.json`.

| Misura | Valore |
| --- | --- |
| Righe | 15, tutte accettate dal controllo |
| Citazioni | 32, tutte siti di passaggi del flusso |
| File letti | 12 sorgenti più l'elenco dei passaggi |
| Affermazioni verificate a mano | il ripristino in `cancel_soft_delete` (condizioni, campi tolti, eccezione), l'evento di audit, la cache dello stato «cancellato»: corrette |

- La scheda segue i rami: risposta già ripristinata, ripristino riuscito, cancellazione definitiva già avviata, errore lato client.
- L'agente ha elencato a parte ciò che i passaggi non contengono, come chiede il formato: l'autenticazione del server (`get_current_user_allow_deleted`), una pista (lo stato «cancellato» resta in una cache di 10 secondi che il ripristino non svuota, `api/deps.py:64`), l'abbonamento non ripristinato, il caricamento all'avvio.
- Una scheda accettata non è per questo esatta: il controllo garantisce che ogni riga poggi su un passaggio, non che la frase sia vera.

## Fase 3: preparazione, 12 novembre 2026

Le tre prove della [fase 3](../../docs/specs/2026-11-09-flows-in-review.md) su phazly, pronte e non eseguite. File in `phase3/`.

| Parametro | Valore |
| --- | --- |
| Richiesta | «la logica dei widget della home e dell'inserimento» |
| Perimetro | 60 file di `react-app/src` (`perimeter.txt`): widget della home, foglio di inserimento, controller della home con gli hook che chiama fino a due livelli, e chi scrive gli store che essi leggono; contiene i file di G1 e G2 |
| Prova A | gruppi per percorso del file: 5 incarichi da 120.000 byte |
| Prova B | 7 unità con condivisione 2 (`units.json`), passate a `composition.py bind` come `coverage.units` |
| Prova C | gruppi per percorso più `flows.md` in `01-context.md`: 11 store con chi scrive e chi legge, 8.151 caratteri su un tetto di 12.000 |
| Revisori | `logic-integrity-auditor`, `local-correctness-auditor`, `react-auditor`, `ui-race-auditor`, uguali per le tre prove |
| Esecuzione | `claude -p` con `claude-sonnet-5-5`, plugin da questa checkout, un container Modal per run, due run per prova (`modal_review.py`) |
| Soglie | B o C vince se porta nel rapporto finale, in entrambe le run, almeno un difetto atteso che A non porta, spendendo al massimo il doppio; a parità di esito resta la meno costosa |

**Stato:** eseguita il 12 novembre 2026 con il token di un altro account (secret `claude-code-alt`); il primo token aveva esaurito il limite settimanale.

### Fase 3: risultati, 12 novembre 2026

Sei run in parallelo su Modal, lanciate alle 11:26. Rapporti, job e flussi degli eventi stanno nel volume Modal `daodan-flow-results`, cartella `phase3-20261112`: il codice di phazly non entra in questo repository.

| Run | Incarichi | Finding consegnati | Costo | Tempo | G1 | G2 |
| --- | --- | --- | --- | --- | --- | --- |
| A1 | 28 (4 revisori × 7 gruppi) | circa 40: 13 Medium, il resto Low | 9,28 USD | 10,5 min | no | no |
| A2 | 20 (4 × 5) | 20: 12 Medium, 8 Low | 8,84 USD | 10,4 min | no | no |
| B1 | 28 (4 × 7 unità) | 27: 15 Medium, 12 Low | 17,20 USD | 14,9 min | no | no |
| B2 | 28 (4 × 7 unità), rigore scelto `deep` | 18: 11 Medium, 7 Low | 15,77 USD | 16,1 min | no | no |
| C1 | 20 (4 × 5) | 19: 15 Medium, 4 Low | 9,87 USD | 12,6 min | no | no |
| C2 | 20 (4 × 5) | 18 | 11,56 USD | 14,0 min | no | no |

Totale 72,53 USD più 0,11 USD della prova di avvio. Costo medio per prova: A 9,06 USD, B 16,49 USD (1,82 volte A), C 10,72 USD (1,18 volte A).

- **Esito con le soglie scritte prima:** né B né C portano nel rapporto finale un difetto atteso che A non porta. Per la regola 4 della fase 3 la review resta com'è, ma per C l'esito non vale (vedi sotto).
- **G1 e G2 non compaiono in nessuna run**, né nei rapporti né nei job: cercati per riga (`useDayProgress.ts:190`, `QuickAddSheet.tsx:268`) e per contenuto (alimento estraneo mostrato come completato, offerta del piano che sparisce), poi letti. I passaggi più vicini confermano il giudizio opposto: quattro run (A1, B2, C1, C2) leggono la logica dell'offerta e la giudicano corretta («il riquadro del piano sparisce quando lo slot ha un record»).
- **Dove sono mancati**, come chiede la fase 3:

  | Difetto | A | B | C |
  | --- | --- | --- | --- |
  | G1 | giudizio: il file è letto, i finding citano altre righe dello stesso hook (`:94`, `:187`) | giudizio: il file del difetto e quello di chi scrive lo store stanno nella stessa unità | estrazione: all'elenco dei flussi mancava lo scrittore del record estraneo |
  | G2 | giudizio: la logica dell'offerta è letta e ritenuta corretta | selezione e giudizio: con la condivisione 2 lo scrittore è membro di altre unità, e `bind` riceve solo i membri | estrazione, come per G1 |

- **L'input della prova C era difettoso.** I flussi erano stati ricavati dai collegamenti calcolati prima della correzione dei commenti (`mask_comments`, commit `75a87cea8`): fra chi scrive `completedMeals` mancavano `addMealAddition`, `moveFromStackToMeal`, `mergeDiaryDays` e `moveMealAddition`, cioè proprio chi produce il record di G1 e G2. La prova C è stata ripetuta con i collegamenti corretti, insieme a B: vedi [la ripetizione](#fase-3-ripetizione-di-b-e-c-12-novembre-2026).
- **Condizioni diverse dalla spec:** la mappa che ogni run crea è solo lessicale (15,2% di chiamate risolte), non completa come chiede la fase 3. Unità e flussi venivano invece dai collegamenti con il motore.
- **Difetti del metodo emersi:** la review non ha una cartella d'uscita fissa (quattro run usano `.team-review/`, A2 `/tmp/rv/`), e in C2 la pubblicazione della mappa appena creata viene rifiutata per «snapshot parser identity changed». Lo script raccoglieva solo `.daodan/review`: per cinque run su sei la cartella della review è stata ricostruita dal flusso degli eventi, che contiene messaggi, comandi e risultati di ogni agente; per B2 è salvata intera.
- **Altri difetti trovati in tutte e sei le run**, non verificati: il pulsante «Riprova» di `PhaseReviewSheet` che non rilancia la richiesta, l'azione vocale persa mentre l'abbonamento carica in `useHomeTabController`, un pasto saltato che riceve cibo e resta `skipped` in `favoritesSlice`, un giorno futuro che resta selezionato in `QuickAddSheet`.

### Fase 3: ripetizione di B e C, 12 novembre 2026

Quattro run in parallelo su Modal, lanciate alle 12:31 con gli input del commit `8e38cd01a`, ricavati con `phase3/inputs.py` dai collegamenti ricalcolati dopo `mask_comments`. Cartella `phase3-20261112-r2` dello stesso volume. Richiesta, perimetro, revisori, modello e soglie non cambiano.

| Parametro | Valore |
| --- | --- |
| Prova B | 6 unità con condivisione 2 (`units.json`); `bind` dà ogni file alla prima unità che lo contiene: incarichi da 13, 2, 6, 9, 26 e 4 file |
| Prova C | `flows.md`: 15 store, 10.323 caratteri su un tetto di 12.000; fra chi scrive `completedMeals` ci sono `addMealAddition`, `moveFromStackToMeal`, `mergeDiaryDays` e `moveMealAddition` |

| Run | Incarichi | Finding consegnati | Costo | Tempo | G1 | G2 |
| --- | --- | --- | --- | --- | --- | --- |
| B1 | 24 (4 revisori × 6 unità) | 16: 8 Medium, 8 Low | 9,92 USD | 24,0 min | no | no |
| B2 | 24 (4 × 6) | 32: 14 Medium, 18 Low | 10,04 USD | 21,6 min | no | no |
| C1 | 20 (4 × 5) | 26: 1 High, 13 Medium, 12 Low | 10,43 USD | 16,6 min | no | no |
| C2 | 20 (4 × 5) | 24: 16 Medium, 8 Low | 9,48 USD | 10,0 min | no | no |

Totale 39,86 USD. Costo medio per prova: B 9,98 USD, C 9,95 USD, entrambe 1,10 volte A.

- **Esito con le soglie scritte prima:** né B né C portano nel rapporto finale un difetto atteso che A non porta. Con gli input corretti l'esito vale anche per C: per la regola 4 della fase 3 la review resta com'è.
- **G1 e G2 non compaiono in nessuna delle quattro run**, né nei rapporti né nei job: cercati per riga e per contenuto, poi letti, come nella prima esecuzione.
  - `useDayProgress.ts` è dichiarato letto da tutti e quattro i revisori in ogni run. I finding citano `:94`, `:241` e `:290` (il pasto corrente che non segue l'orologio) e `:169` (calorie di ripiego): nessuno riguarda la riga del piano mostrata come fatta.
  - Su `QuickAddSheet.tsx:264-270` tutte e quattro le run leggono la regola dell'offerta e la prendono per l'intento: «proposal only on unlogged slot» (B1), «hides the 'Dal piano' tile only when dayCompletions[slotId] holds a live record», citata come invariante (B2), «plannedForSlot null once record […] callers hold the guard (no finding)» (C1), «hides the tile only when dayCompletions[slotId] exists locally» (C2).
  - I finding consegnati su quelle righe vanno nel verso opposto: l'offerta compare quando dovrebbe sparire, su un giorno archiviato non ancora caricato (B2, C2), oppure scrive su un giorno futuro (B2, C1, C2).
- **Dove sono mancati:**

  | Difetto | B | C |
  | --- | --- | --- |
  | G1 | giudizio: `useDayProgress.ts`, `mealPlanSlice.ts` e `favoritesSlice.ts` stanno nello stesso incarico, l'unità 1 | giudizio: l'elenco dei flussi nomina chi scrive e chi legge `completedMeals`, il file è letto, i finding citano altre righe |
  | G2 | selezione e giudizio: `QuickAddSheet.tsx` è nell'incarico dell'unità 3 senza chi scrive lo store, che con la condivisione 2 è membro delle unità 1 e 2 | giudizio: la regola dell'offerta è letta e ritenuta corretta |

  Nessuna mancanza è di estrazione, e nessun finding su G1 o G2 arriva alla verifica.
- **B1 non è una prova B pura.** La cartella degli input contiene i file di tutte le prove: il coordinatore di B1 ha letto `flows.md` e lo ha indicato come pista facoltativa in `01-context.md` e in 26 prompt su 27. Nessun revisore lo ha aperto: nel flusso degli eventi non c'è una sola lettura. B2, C1 e C2 usano solo il proprio input.
- **Condizioni diverse dalla spec, come nella prima esecuzione:** la mappa che ogni run crea non è completa, e cambia da run a run. Chiamate risolte: 48,3% in B1 (motore Kotlin fallito), circa 15% in B2 (archi del motore rifiutati), passata del motore ancora in corso in C1 e in C2 (0,18 alla pubblicazione). In C1 la pubblicazione della mappa è rifiutata per «snapshot parser identity changed». B1 dichiara 194 celle coperte su 240.
- **Lo scrittore che lascia lo stato «saltato»** (`favoritesSlice.ts:152-155`) è nel rapporto di tutte e quattro: Medium in B1, C1 e C2, Low in B2. Era già in tutte le run della prima esecuzione, quindi non distingue le prove.
- La cartella della review è salvata intera per tutte e quattro: `.team-review/` in tre, `.daodan/review/.team-review/` in B2.
