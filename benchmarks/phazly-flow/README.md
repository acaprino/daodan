# Benchmark: phazly, un bug di flusso reale

**Stato:** In uso. È il caso reale su cui si misurano i flussi, le unità di review e la mappa del sistema. Le run di review con un modello sono chiuse (nessuna configurazione trova i due difetti); le misure senza modello sui 38 flussi del riferimento si rifanno a ogni modifica dei collegamenti.

**Domanda.** Su phazly-app, un'app reale con interfaccia e servizio:

1. una review per area trova un difetto di flusso reale (un fatto sullo slot del diario letto come fatto sul piatto del piano)?
2. i flussi e le unità che la macchina ricava aiutano la review a trovarlo?
3. quanti flussi del riferimento dell'intero sistema il grafo chiude senza modello, e che cosa aggiunge un modello?

Il codice di phazly-app non è copiato qui; le run e i loro artefatti restano fuori dal repository.

**Risultati validi oggi.**

| Domanda | Risultato | Con un modello? |
| --- | --- | --- |
| La review per area trova G1 e G2? | no, in 14 run di review: una sola descrizione esatta di G1, in un job, mai nel rapporto | sì (Sonnet 5.5) |
| Unità o elenco dei flussi dati alla review cambiano l'esito? | no: né B né C portano un difetto che A non porta; la review resta com'è | sì |
| Un modello scrive da solo le regole di collegamento? | sì, salvo le rotte: 32 chiamate collegate contro 46 | sì, regole scritte alla cieca |
| Un modello che etichetta le coppie «chi scrive / chi legge» trova i difetti? | no: 0 su 2 | sì |
| Una scheda di flusso scritta da un modello è accettata dal controllo? | sì: 15 righe su 15, 32 citazioni | sì |
| Quanti flussi del riferimento chiude il grafo? | 18 su 38 con i collegamenti certi, 19 con i possibili; 129 frecce certe su 240 | no |
| Quanti flussi può provare una scheda del percorso? | al più 7 su 38 | no |

**Passo successivo della pipeline.** I collegamenti di queste misure vengono dalla pipeline fino ad `analyze` (statico). Il passo dinamico (`observe`) non è misurato su phazly; sulle chiamate lo misura [`call-provenance`](../call-provenance/README.md). Un modello che conferma i collegamenti possibili o legge le schede dei percorsi su questi 38 flussi non è misurato: il protocollo è in [`system-map`](../system-map/README.md#quanta-base-serve-a-un-modello-il-confronto-ancora-da-fare).

## Parametri del caso

| Parametro | Valore |
|---|---|
| target | phazly-app al commit `46c92b28`, il genitore della prima fix, copiato senza storia successiva |
| difetti attesi | G1 `react-app/src/hooks/useDayProgress.ts:190`: la riga del piano è fatta per un record qualsiasi nello slot. G2 `react-app/src/components/common/QuickAddSheet.tsx:268`: l'offerta «Dal piano» sparisce per un record qualsiasi. Fix: `b511e814`, `239819dd` |
| criterio | trovato se un finding consegnato nel rapporto afferma, con `file:line`, che un record dello slot è usato come «piatto del piano mangiato»; parziale se compare solo in un job o come pista |
| regole di collegamento | `rules.json`, 18 regole scritte da Claude leggendo lo stato Zustand, il client delle API, i router FastAPI e l'accesso a MongoDB; `rules-blind.json`, 17 regole scritte alla cieca |
| riferimento dell'intero sistema | 38 flussi, 240 frecce; privato del proprietario, letto a runtime con `--expected`, non copiato |
| caso fra strati (fase 2) | dalla riga «Completato» della home il flusso arriva alla collezione `diaryDays` passando per `/getDiaryDays` |

Spec: [fase 2](../../docs/specs/2026-11-18-flussi-e-mappa-del-sistema.md) e [fase 3](../../docs/specs/2026-11-09-flows-in-review.md).

| Script | Cosa fa |
|---|---|
| `summarize.py LINKS.json` | i riepiloghi dei collegamenti in `results/` |
| `measure_links.py` | su Modal: la pipeline fino ad `analyze`, i collegamenti e il confronto con il riferimento |
| `check_store_keys.py` | in locale: controlla le chiavi di store sull'albero sintattico del sorgente |
| `phase3/inputs.py`, `modal_review.py`, `collect.py` | gli input delle tre prove della fase 3 (`perimeter.txt`, `units.json`, `flows.md`: generati, non si modificano a mano), le run e la raccolta |

## La review per area trova il difetto?

### La review com'è, su una richiesta in parole

9 novembre 2026. Plugin al commit `cf0ffe6`, `claude -p` 2.1.319, una sessione nuova per run, `claude-sonnet-5-5`; mappa lite di `react-app/` (630 file), senza il grafo delle chiamate TypeScript.

| Run | Richiesta | Metodo | Job | G1 | G2 | Costo | Tempo |
|---|---|---|---|---|---|---|---|
| mappa | lite di `react-app/` | analista isolato, pubblicata | 1 | – | – | 2,06 USD | 548 s |
| A | widget della home, in parole | saltato: il modello revisiona da solo e lo dichiara solo alla fine | 0 | no | no | 1,04 USD | 207 s |
| A2 | A, con il metodo nominato | si ferma sul prerequisito della mappa dell'intero progetto | 0 | – | – | 0,34 USD | 37 s |
| A3 | A2, con la deroga: solo `react-app` | completo, 81 finding, 21 cluster | 12 | parziale | fuori perimetro | 15,09 USD | 981 s |
| A3b | A3 ripetuta sulla stessa copia | completo, 6 ruoli su 5 gruppi | 30 | un job, solo il caso «saltato» | fuori perimetro | 20,82 USD | 781 s |
| B | inserimento e scansione, metodo e deroga | completo, 29 job dispacciati due volte | 49 | no | no | 26,16 USD | 772 s |

- **A3:** il job `logic-integrity` descrive G1 esattamente e lo classifica Low; il consolidamento lo fonde in un cluster con altri cinque finding sulla stessa ancora e il caso sparisce dal titolo e dal rapporto.
- **A3b:** stesso prompt e stessa mappa, roster e gruppi diversi (30 job contro 12); un solo job tocca `useDayProgress.ts:190` e descrive solo il caso «pasto saltato». La run ha letto la cartella `.team-review/` di B rimasta nella copia: il confronto con A3 è indicativo.
- **B:** `01-context.md` afferma che non esiste un tipo «planned» (falso per le aggiunte) e l'affermazione arriva a tutti i worker; il job che legge la riga di G2 la descrive senza segnalarla.
- **Dove si perde il difetto:** l'ingresso (una richiesta in parole può saltare il metodo), il contesto (un'affermazione sul modello dei dati senza livello), gravità e consolidamento (Low, poi fuso per ancora), il perimetro (i lettori dello stesso fatto in altre aree). Una descrizione esatta di G1 in un job su 12 e in 0 su 30: il ruolo non la trova in modo affidabile.
- In A3 un job segnala lo stesso schema in `useDayLogSlots.ts`, ancora presente dopo le fix: da verificare con l'autore.

### Con le unità o con l'elenco dei flussi (fase 3)

12 novembre 2026, su Modal, un container per run, `claude -p` con `claude-sonnet-5-5`, due run per prova. Rapporti e flussi degli eventi nel volume Modal `daodan-flow-results`, cartelle `phase3-20261112` (A) e `phase3-20261112-r2` (B e C).

| Parametro | Valore |
| --- | --- |
| Richiesta | «la logica dei widget della home e dell'inserimento» |
| Perimetro | 60 file di `react-app/src` (`phase3/perimeter.txt`); contiene i file di G1 e G2 |
| Prova A | gruppi per percorso del file: 5 incarichi da 120.000 byte |
| Prova B | 6 unità con condivisione 2 (`phase3/units.json`), passate a `composition.py bind` come `coverage.units`: incarichi da 13, 2, 6, 9, 26 e 4 file |
| Prova C | gruppi per percorso più `phase3/flows.md` in `01-context.md`: 15 store con chi scrive e chi legge, 10.323 caratteri su un tetto di 12.000 |
| Revisori | `logic-integrity-auditor`, `local-correctness-auditor`, `react-auditor`, `ui-race-auditor` |
| Soglie | B o C vince se porta nel rapporto finale, in entrambe le run, almeno un difetto atteso che A non porta, spendendo al massimo il doppio |

| Run | Incarichi | Finding consegnati | Costo | Tempo | G1 | G2 |
| --- | --- | --- | --- | --- | --- | --- |
| A1 | 28 (4 revisori × 7 gruppi) | circa 40: 13 Medium, il resto Low | 9,28 USD | 10,5 min | no | no |
| A2 | 20 (4 × 5) | 20: 12 Medium, 8 Low | 8,84 USD | 10,4 min | no | no |
| B1 | 24 (4 × 6 unità) | 16: 8 Medium, 8 Low | 9,92 USD | 24,0 min | no | no |
| B2 | 24 (4 × 6) | 32: 14 Medium, 18 Low | 10,04 USD | 21,6 min | no | no |
| C1 | 20 (4 × 5) | 26: 1 High, 13 Medium, 12 Low | 10,43 USD | 16,6 min | no | no |
| C2 | 20 (4 × 5) | 24: 16 Medium, 8 Low | 9,48 USD | 10,0 min | no | no |

Costo medio: A 9,06 USD, B 9,98, C 9,95 (1,10 volte A).

- **Esito con le soglie scritte prima:** né B né C portano un difetto atteso che A non porta. Per la regola 4 della fase 3 la review resta com'è.
- **G1 e G2 non compaiono in nessuna run,** né nei rapporti né nei job: cercati per riga e per contenuto, poi letti.
  - `useDayProgress.ts` è dichiarato letto da tutti i revisori in ogni run di B e C; i finding citano altre righe (`:94`, `:169`, `:241`, `:290`).
  - Su `QuickAddSheet.tsx:264-270` tutte le run di B e C leggono la regola dell'offerta e la prendono per l'intento («proposal only on unlogged slot»); i finding su quelle righe vanno nel verso opposto.
- **Dove sono mancati:**

  | Difetto | A | B | C |
  | --- | --- | --- | --- |
  | G1 | giudizio: il file è letto, i finding citano altre righe dello stesso hook | giudizio: `useDayProgress.ts`, `mealPlanSlice.ts` e `favoritesSlice.ts` stanno nello stesso incarico | giudizio: l'elenco dei flussi nomina chi scrive e chi legge `completedMeals`, il file è letto |
  | G2 | giudizio: la logica dell'offerta è letta e ritenuta corretta | selezione e giudizio: `QuickAddSheet.tsx` è in un incarico senza chi scrive lo store | giudizio: la regola dell'offerta è letta e ritenuta corretta |

  Nessuna mancanza è di estrazione: il difetto si perde nel giudizio, che chiede di sapere cosa l'offerta deve significare.
- **Condizioni diverse dalla spec:** la mappa che ogni run crea non è completa e cambia da run a run (chiamate risolte: 48,3% in B1, circa 15% in B2, passata del motore ancora in corso in C1 e C2). B1 non è una prova B pura: il coordinatore ha letto `flows.md` e lo ha indicato come pista facoltativa; nessun revisore lo ha aperto.
- **Difetti del metodo emersi:** la review non ha una cartella d'uscita fissa; in due run la pubblicazione della mappa è rifiutata per «snapshot parser identity changed».
- **Altri difetti trovati,** non verificati: lo scrittore che lascia lo stato «saltato» (`favoritesSlice.ts:152-155`, in tutte le run), il pulsante «Riprova» di `PhaseReviewSheet`, l'azione vocale persa mentre l'abbonamento carica, un giorno futuro che resta selezionato in `QuickAddSheet`.

Una prima esecuzione di B e C dello stesso giorno aveva gli input ricavati prima di una correzione alla lettura dei commenti (commit `75a87cea8`): fra chi scrive `completedMeals` mancavano i quattro scrittori del record di G1 e G2. È superata dalla tabella qui sopra. Spesa delle due esecuzioni: 72,53 e 39,86 USD.

## Le regole di collegamento e i flussi

### Con e senza il passaggio del motore

11-12 novembre 2026, su Modal, `rules.json`. Riepiloghi in `results/flow-links-summary.json` e `flow-links-summary-engine.json`.

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
- Senza il motore 119 flussi restano di un solo nodo: le rotte chiamano i servizi come attributo di un modulo importato, le azioni chiamano funzioni ricevute o importate con un alias di percorso. Con il motore ne restano 60.
- Lacune restanti: 13 letture dello stato con un selettore non letterale, 5 scritture con chiave calcolata, 15 chiamate fuori da un simbolo con nome o con rotta calcolata.

I conteggi di oggi sono diversi (1.105 ingressi, 25.843 legami): vedi [i flussi del riferimento](#flussi-del-riferimento-chiusi-dal-grafo-senza-modello).

### Regole scritte alla cieca da un modello

`rules-blind.json`: 17 regole scritte da un agente senza contesto, con il solo formato e il sorgente, in circa 14 letture. Così come scritte sono rifiutate: `strip` stava dentro `route`. Misurate dopo aver spostato quel campo, sullo snapshot lessicale e con `flows.py` al commit `7db9b003b`, contro le 14 regole di `rules.json` di quel commit. Riepilogo in `results/flow-links-summary-blind.json`.

| Misura | `rules.json` | `rules-blind.json` |
| --- | --- | --- |
| Punti d'ingresso | 234 | 234 |
| Chiamate del client collegate a una rotta | 46 | 32 |
| Store | 123 | 123, gli stessi |
| Store con chi scrive e chi legge | 70 | 68 |
| Flussi che arrivano a uno store | 59 | 59 |
| Lacune dichiarate | 60 | 57 |

- Le colonne differiscono solo sulle rotte: l'agente ha nominato il client delle API come funzione del progetto (`callee`), che non vale per le chiamate importate con un alias di percorso.
- Il suo elenco «non esprimibile» ha dato quattro correzioni, ciascuna con un test in `tests/test_codebase_map_flows.py`. Restano non esprimibili: `fetch` con il metodo nell'oggetto delle opzioni, il prefisso di rotta aggiunto dal servizio, la collezione scelta a runtime.

### File di un difetto noto (misura 1 della fase 2)

Perimetro `react-app/src` senza i test, 568 file, limite di 120.000 byte, collegamenti con il motore. Per G1 e per G2 si contano il file del difetto e i file di chi scrive gli store che esso legge: 4 file ciascuno. «Condivisione» è il numero massimo di unità di cui un file è membro; nelle altre è contesto (`flows.py units --share`).

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

Con condivisione 2 il costo resta vicino a `pack()` (1,12) e l'unità del difetto nomina come contesto i file di chi scrive il suo dato. Tutti i 568 file sono assegnati in ogni colonna. Che il contesto basti al revisore l'ha misurato la fase 3, sopra: non basta.

### Etichette di granularità e significato scritte da un modello (misura 4 della fase 2)

12 novembre 2026. Un agente senza contesto riceve coppie «chi scrive / chi legge» uscite da `flows.py` e il sorgente; per ogni coppia scrive cosa significa una voce per chi scrive, cosa assume chi legge e se sono coerenti. Nessun accenno ai difetti attesi. Voci e risposte in `results/`.

| Giro | Coppie | Fra cui | Coerenti | Incoerenti | Letture |
| --- | --- | --- | --- | --- | --- |
| 1 (`label-items.json`, `labels.json`) | 20, estratte a caso con seme fisso più le due di G1 e G2 | G1 (n. 17), G2 (n. 10) | 19 | 1 (n. 5) | 41 file |
| 2 (`relabel-items.json`, `relabels.json`) | 6: G1, G2 e 4 controlli, con l'elenco completo degli scrittori | G1 (n. 5), G2 (n. 1) | 6 | 0 | 22 file |

- **I due difetti noti non sono trovati.** Nel giro 1 mancava lo scrittore che produce il caso (un commento con un apostrofo rompeva la lettura degli argomenti: corretto, l'elenco degli scrittori di `completedMeals` passa da 8 a 12). Nel giro 2, con l'elenco completo: per G1 l'agente segue la lettura fino al conteggio dei pasti (`useDayProgress.ts:86`) e non fino alla riga `:190`; per G2 vede il comportamento e lo giudica corretto.
- La soglia (16 concordanze su 20 con una lettura manuale) non è valutata: la lettura manuale delle 20 coppie non è stata fatta; sulle due coppie dei difetti la concordanza è 0 su 2.
- Il limite che la misura indica: un'etichetta per coppia giudica il dato dove viene letto, non dove il lettore lo trasforma in un fatto mostrato, e non conosce l'intento del prodotto.
- La coppia n. 5 del giro 1 è una pista non verificata: lo spuntino torna con id `afternoon_snack` (`types/index.ts:246`) invece di `snack` (`types/index.ts:263`). La n. 12 era un collegamento falso, corretto con un test.

### Scheda del flusso scritta da un modello

12 novembre 2026. Un agente senza contesto riceve i passaggi del flusso «ripristino dell'account» (`RestoreAccountModal.handleRestore`, 74 collegamenti con il motore) e il sorgente, e scrive la scheda nel formato di `codebase_map_flows(card=...)`. Passaggi e scheda in `results/card-restore-account*.json`.

| Misura | Valore |
| --- | --- |
| Righe | 15, tutte accettate dal controllo |
| Citazioni | 32, tutte siti di passaggi del flusso |
| File letti | 12 sorgenti più l'elenco dei passaggi |
| Affermazioni verificate a mano | il ripristino in `cancel_soft_delete`, l'evento di audit, la cache dello stato «cancellato»: corrette |

L'agente elenca a parte ciò che i passaggi non contengono, fra cui una pista (lo stato «cancellato» resta in una cache di 10 secondi che il ripristino non svuota, `api/deps.py:64`). Una scheda accettata non è per questo esatta: il controllo garantisce che ogni riga poggi su un passaggio, non che la frase sia vera.

## Flussi del riferimento chiusi dal grafo, senza modello

23 novembre 2026. Riferimento dell'intero sistema: 38 flussi, 240 frecce. `rules.json`, nessun modello, nessuna regola scritta a mano in più. Metodo e generatori dei collegamenti possibili: [`system-map`](../system-map/README.md#collegamenti-possibili).

| Collegamenti | Frecce certe su 240 | Flussi chiusi su 38, solo certi | Con i possibili |
|---|---:|---:|---:|
| prima delle tre modifiche qui sotto | 101 | 14 | 15 |
| con la chiave dello store come indice costante | 104 | 15 | 16 |
| con il membro `store:` senza chiave | 118 | 16 | |
| analisi fresca, `rules.json` | 119 | 16 | 17 |
| analisi fresca, più le regole dei wrapper HTTP | **129** | **18** | **19** |

Le prime tre righe sono misurate sui collegamenti di un run registrato (`possible-in/phazly5` sul volume `daodan-flow-results`), le ultime due su un'analisi fresca con l'albero di quel giorno (`measure_links.py`).

**La chiave dello store come indice costante.** Una regola di store con `key: holder` legge la chiave anche quando il ricevente è `store[INDICE]` (`db[COLLECTION].insert_one(x)`).

| Misura | Prima | Dopo |
|---|---|---|
| Frecce mancante / non misurabile / mancante con lacuna | 39 / 26 / 10 | 30 / 25 / 17 |
| Legami `scrive` / `legge` | 459 / 463 | 507 / 489 |
| Chiavi di store (mongo) | 121 (38) | 127 (44) |
| Store con scrittori e lettori | 88 | 95 |
| Lacune | 261 | 303 |
| Flussi tracciati da un ingresso, incompleti su 1.105 | 119 | 205 |

- Le 74 chiavi nuove (48 `scrive`, 26 `legge`, nessuna persa) sono controllate sull'albero sintattico del sorgente (`check_store_keys.py`): 74 giuste, 0 sbagliate. Un campione di 10 (seme 11) è stato riletto a mano.
- Le 42 lacune nuove: 24 `self.NOME`, 10 indici calcolati, 5 nomi puntati (`modulo.NOME`), 3 nomi importati che lo snapshot non lega a una dichiarazione. Gli 86 flussi che diventano incompleti hanno una di queste lacune sul percorso: prima la chiamata era muta.
- Leggere `self.NOME` dalla dichiarazione della classe che racchiude dava 17 flussi chiusi ma legami certi sbagliati con il motore vero: non è nel codice.

**Il membro `store:` senza chiave.** `system_map._check_nodes` accetta il nodo con `unlinked`: «non misurabile» 25 → 4, «mancante con lacuna» 17 → 24. Il flusso in più si chiude sul file dello store locale, membro dello stesso nodo.

**Il wrapper di un client HTTP.** `daodan/core/http_wrappers.py` (`python flows.py wrappers MANIFEST`, tabella dei client in `daodan/data/http-clients.json`) propone le regole `rotta` per le funzioni del progetto che avvolgono un client.

| Misura | `rules.json` | più le regole dei wrapper |
|---|---|---|
| Chiamate a rotte, e di queste collegate | 50, 50 | 119, 119 |
| Lacune dei collegamenti | 296 | 298 |

La prova propone tre regole e una lacuna: `adminFetch` (70 chiamate, 69 con l'URL letterale), `apiGet` (nessuna chiamata risolta) e `fetchAsDataUrl` (una chiamata, URL non letterale); rifiuta con la causa `checkVerificationStatus`, che costruisce l'URL con un template. I due flussi in più sono «Revisione delle immagini dei piatti» e «Chiavi API». Limiti: `fetchAsDataUrl` chiama un URL di altri ed è una regola candidata, da confermare; un wrapper di un wrapper non è provato; la tabella dei client ha solo `fetch`.

**Non misurato:** un altro progetto; i flussi ancora aperti dopo il passo dinamico; un modello che conferma i collegamenti possibili.

## Il tetto della scheda del percorso, senza modello

23 novembre 2026. Domanda: prima di pagare un modello, quanti flussi del riferimento una scheda del percorso del prodotto (`daodan/core/flow_paths.py`) può provare, e gli altri perché no. Serve a non scambiare un buco del grafo per un difetto di come la scheda è data al modello.

| Parametro | Valore |
|---|---|
| Script | `python benchmarks/system-map/card_ceiling.py MANIFEST LINKS.json EXPECTED-system.json`, in locale; prova `benchmarks/system-map/test_card_ceiling.py` |
| Collegamenti | quelli della riga «chiave dello store come indice costante»: 25.843 legami, 1.105 ingressi, 303 lacune |
| Scheda | una per ingresso classificato; i passi sono quelli di `flow_paths._steps`; l'effetto è quello di `flow_paths._effect`, una scrittura certa su uno store |
| Scheda all'ingresso | il nodo d'ingresso del flusso tiene il gestore della scheda o il file dove il controllo è legato |

| Esito del flusso (il primo che vale) | Flussi su 38 |
|---|---:|
| `provata`: una scheda all'ingresso arriva a ogni effetto su store del flusso | **7** |
| `effetto non esprimibile`: nessun effetto del flusso è una scrittura su uno store | 14 |
| `nessuna scheda all'ingresso` | 3 |
| `tagliata dalla scheda`: i collegamenti arrivano all'effetto, la scheda no | 0 |
| `buco del grafo`: dal gestore i collegamenti non arrivano all'effetto | 14 |

| Altra misura | Valore |
|---|---|
| Effetti del riferimento: su store, non su store | 25, 25 (17 «valore mostrato», 4 cambi di stato in un sistema di altri o senza store, 3 «evento emesso», 1 comando a un dispositivo) |
| Schede in tutto, con almeno un effetto | 1.105, 297 |
| Passi per scheda: mediana, massimo | 2, 1.305 |
| Nei 7 flussi provati: schede all'ingresso | da 2 a 46 |
| Nei 7 flussi provati: passi dal gestore all'effetto, caratteri di passi letti fino all'effetto | da 1 a 5, da 274 a 7.167 |

Incrocio flusso per flusso (esito della scheda × flusso chiuso sulle frecce certe):

| Esito della scheda | Chiuso sulle frecce | Non chiuso |
|---|---:|---:|
| `provata` | 3 | 4 |
| `effetto non esprimibile` | 9 | 5 |
| `nessuna scheda all'ingresso` | 1 | 2 |
| `buco del grafo` | 2 | 12 |

- **La forma della scheda non taglia nulla:** dove il grafo arriva, la scheda arriva.
- **Il limite maggiore è che cosa conta come effetto:** quattordici flussi finiscono su un valore mostrato, un evento emesso o un comando, e la scheda chiude solo su una scrittura in uno store. Nove di questi il grafo li chiude già sulle frecce.
- **Dove la prova c'è è corta, ma va trovata:** al più 5 passi e 7.167 caratteri, in mezzo a 2-46 schede per ingresso e 1.105 in tutto. Nelle run cieche del mappatore con Haiku le schede erano in coda e nessuna è stata aperta ([`system-map`](../system-map/README.md#il-mappatore-con-un-modello-sullintero-sistema-alla-cieca)).
- **Non si confronta come totale con i flussi chiusi sulle frecce:** quella misura segue le frecce del riferimento da nodo a nodo e chiede ogni effetto, schermate comprese; questa segue i collegamenti dal gestore di una scheda e chiede ogni effetto su store.
- **Due denominatori per la prova con il modello:** per certificare contro il riferimento contano al più 7 flussi; per trovare e aprire la scheda giusta ne contano 31, quelli con almeno una scheda all'ingresso.
- Dei 14 «buco del grafo», 12 mancano anche sulle frecce; 2 sono chiusi sulle frecce ma nessun gestore di scheda avvia il percorso.
- Non misurato: un altro progetto; le schede dei 14 flussi con effetto non esprimibile, se arrivano almeno al file della schermata; le schede lette da un modello.
