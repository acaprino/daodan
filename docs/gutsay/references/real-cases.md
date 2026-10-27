# Casi reali e provenienza per la campagna Gutsy

Data: 26 ottobre 2026. Ricerca e progettazione soltanto. Nessun corpus scaricato, nessuna inferenza o esecuzione Modal, nessun invio di materiale locale al cloud.

## Conclusione operativa

Il repository contiene materiale reale utile per costruire il corpus, ma non contiene già un grande gold set indipendente per i tre compiti richiesti. Il codice reale, il bug comprovato, una traccia realmente eseguita e un esempio sintetico con oracle sono evidenze diverse. Le etichette di attivazione dei revisori non diventano automaticamente etichette del task router, dei tool o della compattazione.

Proposta: tre pool separati, con provenienza nel manifest e risultati riportati distintamente: scenari sintetici controllati; casi derivati da codice pubblico autorizzato; benchmark esterni adattati con trasformazione esplicita. Le tracce private restano escluse dal pacchetto cloud finché non esiste una specifica autorizzazione sul loro contenuto.

## Materiale locale effettivamente disponibile

| Fonte | Che cosa è verificato | Limiti prima dell'uso |
|---|---|---|
| `evals/gutsy-decision-pilot/` | Primo pilot effettivamente eseguito su Modal: 47 richieste, 314 domande, casi sintetici e oracle parziali | Diagnostica e regressioni, non nuovo test cieco; non sono sessioni reali di lavoro |
| `evals/senior-review/choicer-eval/runs/20261020T100258Z/dataset.json` | 11 casi di review con provenienza Git e mapping dimensioni/revisori | Etichette per review, non ground truth dei tre compiti; parte del codice proviene da `D:/Projects/jupiter` |
| `runs/20261020-gutsy-followup-ctx1536/cases.json` nello stesso benchmark | 10 casi: due storici e otto funzioni reali da una revisione Jupiter fissata | Un progetto; selezione e giudizi dello stesso coordinatore; funzioni reali, non otto bug riprodotti |
| `runs/20261021-external-corpus-frozen/cases.json` | 52 casi esterni congelati: 9 CommitBench, 10 Devign, 15 Multi-SWE-bench, 18 SWE-bench Verified; 27 development e 25 verification | 42 dichiarati `adjudicated_silver`, 10 `adjudicated_gold`, ma sempre per applicabilità dei revisori. Nuovi oracle richiesti per routing/tool/compaction |
| `ALL_REVIEWERS_RESULTS.md` | 132 controlli bilanciati e 12 problemi completi, inventario di 44 ruoli | La fonte li dichiara nuova suite sintetica; un contesto con codice concreto non rende reale l'intera situazione |

Riferimenti di lettura: [risultati primo pilot](../pilot-results-2026-10-26.md); [README del benchmark](../../../evals/senior-review/choicer-eval/README.md); [limiti dei casi source-derived](../../../evals/senior-review/choicer-eval/QUESTION_REFINEMENT.md), righe 30, 42 e 59-61; [suite revisori](../../../evals/senior-review/choicer-eval/ALL_REVIEWERS_RESULTS.md), righe 5 e 84. I path `runs/...` della tabella sono relativi a `evals/senior-review/choicer-eval/`.

### Casi concreti per variare percorsi e rami

- `jupiter-credential-refill/case.md`: incidente di produzione del 10 agosto 2026, revisione `a0bb4f10`. Un finding critico era falso perché considerava solo il heartbeat periodico e ignorava il percorso di probe response che rifornisce le credenziali. È un ottimo caso di molteplicità dei percorsi e di premessa incompleta, non un esempio positivo di vulnerabilità.
- `jupiter-economic-events-upsert/case.md`: review `77381da4~1`, fix `77381da4`. Upsert su chiave naturale e revisioni del provider: caso di identità e aggiornamento dei dati. Il fix e la spiegazione sono materiale dell'oracle, non input del classificatore.
- `jupiter-cache-convergence/case.md`: review `cea26146~1`, fix `cea26146`. Divergenza della cache dopo restart e mancato recupero: più rami temporali, stato obsoleto e conseguenze distribuite.
- Otto funzioni Jupiter a revisione `936ba644e2cee4680be1d2c29c7aadfbfb86e1bf`: filtro visibilità account, cache TTL, correlazione publish/ACK, conversione timestamp, circuit breaker, ID derivato da hash, lock strumentato, masking di dati nei log. Sono esempi di codice autentico con giudizi di applicabilità; la documentazione dice esplicitamente che non sono nuovi bug verificati.

Fonti locali: [credential refill](../../../evals/senior-review/cases/jupiter-credential-refill/case.md), [upsert](../../../evals/senior-review/cases/jupiter-economic-events-upsert/case.md), [cache convergence](../../../evals/senior-review/cases/jupiter-cache-convergence/case.md), [tabella delle otto funzioni](../../../evals/senior-review/choicer-eval/QUESTION_REFINEMENT.md).

Il fatto che Jupiter sia leggibile localmente non prova che sia pubblico, redistribuibile o autorizzato per Modal. In questa ricognizione non è stata verificata la sua licenza o la disponibilità pubblica. Questi esempi sono quindi candidati per analisi locale, non input cloud automaticamente ammessi.

### Licenze del corpus esterno locale

La ricognizione di `source_inventory.json` e dei 52 record mostra:

- 9 record CommitBench riportano CC BY-NC 4.0 e la nota esplicita “backup candidate generation only, no commercial path and no gold labels”. Non includerli di default nella campagna operativa di Daodan.
- 28 record riportano licenza non dichiarata dalla risposta API Hugging Face; si applicano le licenze dei progetti di origine.
- 15 record Multi-SWE-bench riportano `other` nella risposta API, ancora con licenze dei repository di origine da verificare.

La disponibilità pubblica dei record non completa il controllo dei diritti. Prima dell'inclusione servono origine esatta, licenza applicabile al file/dataset e obblighi di attribuzione. Non interpretare un campo mancante come licenza permissiva. Le etichette `gold` o `silver` locali non sono un certificato indipendente della nuova domanda di valutazione.

## Fonti pubbliche primarie pertinenti

### ToolRet: candidato principale per retrieval

[ToolRet ufficiale](https://github.com/mangopy/tool-retrieval-benchmark) valuta il recupero di tool da un catalogo e pubblica esempi con query, documenti dei tool e rilevanza. È più vicino alla selezione degli schemi rispetto a un benchmark che richiede la generazione degli argomenti. Il codice è Apache-2.0; la README precisa che il benchmark aggrega dataset esistenti. Occorre verificare le condizioni dei dati costituenti al pin scelto, oltre alla licenza del codice. Non è stato verificato un download del corpus in questa ricerca.

Uso proposto: 120 query stratificate con cataloghi congelati e negativi difficili. Le metriche native di ranking, per esempio nDCG/recall@K, rimangono distinte dal criterio Daodan “set di capacità sufficiente per il prossimo passo”. Un tool non etichettato non è automaticamente un negativo certo. [README e protocollo](https://github.com/mangopy/tool-retrieval-benchmark/blob/main/README.md), [licenza del codice](https://github.com/mangopy/tool-retrieval-benchmark/blob/main/LICENSE).

### BFCL: copertura di forme e rami, con oracle derivato dichiarato

Il [dataset README ufficiale BFCL](https://github.com/ShishirPatil/gorilla/blob/main/berkeley-function-call-leaderboard/bfcl_eval/data/README.md) dichiara Apache-2.0 e distingue chiamate singole, più funzioni, parallele, multi-turn e categorie agentiche. Le annotazioni rispondono soprattutto a “quale chiamata con quali argomenti”, non alla scelta dell'intero sottoinsieme di tool da esporre.

Uso proposto: 80 casi pubblici fra alternative simili, multi-tool e irrilevanza, convertiti a requisito di capacità. La conversione è un nuovo oracle locale: va revisionata e non pubblicata come “score BFCL ufficiale”. Conservare alternative valide e tool equivalenti invece di trattare come vietato ogni tool non apparso nella chiamata gold. Nessun tool remoto deve essere realmente invocato nella campagna di sola selezione.

### ToolBench: documentazione reale, istruzioni e tracce generate

Il [README ufficiale ToolBench](https://github.com/OpenBMB/ToolBench) descrive API reali raccolte da RapidAPI, istruzioni costruite automaticamente e annotazioni di solution path; la sezione dati dichiara Apache-2.0 e finalità di ricerca/educazione. Una vera API non rende umana o reale l'intera sessione generata. L'esecuzione live richiede server/chiave e introduce instabilità esterna.

Uso proposto: sorgente secondaria di documentazione e hard negatives, oppure replay statico di tracce pubblicate dopo verifica dei termini. Evitare chiamate live e servizi a pagamento nel corpus Gutsy. Citare la provenienza “API reale, scenario generato”, senza chiamarlo sessione utente reale.

### LongMemEval: utile per memoria, non prova diretta di fast-jev

[LongMemEval ufficiale](https://github.com/xiaowu0162/LongMemEval) pubblica 500 istanze per variante, storie user/assistant, domande temporali/aggiornamenti/astensione e identificativi delle sessioni di evidenza. Il codice ha [licenza MIT](https://github.com/xiaowu0162/LongMemEval/blob/main/LICENSE). La generazione custom include sessioni simulate e filler da altre fonti: anche qui vanno distinti codice, corpus e provenienza delle conversazioni.

Fast-jev conserva il testo user/assistant e compatta call/results. Applicarlo senza modifiche alle sole storie chat di LongMemEval non mette alla prova il suo percorso principale. Convertire i turni in `tool_result` cambia il contratto e deve essere dichiarato come dataset trasformato. `has_answer`, risposta gold e answer_session_ids rimangono solo nello scorer. Il modello vede soltanto il prefisso cronologico ammesso. Questo benchmark può essere un braccio separato di recall/memoria, non una validazione della ricostruzione fast-jev originale. [Formato ufficiale](https://github.com/xiaowu0162/LongMemEval/blob/main/README.md).

## Volumi realistici da preparare, non già disponibili come gold

Proposta di pool iniziale per la grande campagna, da conciliare con il budget statistico del coordinatore:

| Dominio | Famiglie indipendenti proposte | Origine e prerequisito |
|---|---:|---|
| Routing | 120 | 60 compiti derivati da issue/commit pubblici di almeno 6 progetti più 60 scenari controllati; nuova etichettatura sui segnali Daodan |
| Tool selection | 240 | 120 ToolRet, 80 BFCL adattati, 40 task contestuali controllati; preservare metriche native e metriche di sufficienza separate |
| Compattazione | 120 | 60 episodi di replay costruiti da evidenza pubblica e 60 transcript controllati con oracle; nessuna pretesa che siano tracce utente reali |
| Memoria separata opzionale | 60 | Campione LongMemEval con evidenze note; non conteggiarlo come compaction fast-jev |

I numeri sono obiettivi di preparazione, non il conteggio di esempi già verificati. Selezionare 120 task real-source non equivale a possedere il gold del modello più economico sufficiente: per quello occorrono esiti reali di più modelli sui medesimi compiti, con relativi costi. Nel primo stadio si può etichettare soltanto la descrizione del lavoro e i floor verificabili.

Non moltiplicare il numero di famiglie indipendenti contando parafrasi, traduzioni o più finestre dello stesso bug. Tutte le forme dello stesso task, patch, repository o episodio devono restare nello split concordato. Per testare trasferimento, tenere almeno alcuni progetti e famiglie di tool interamente fuori da sviluppo e calibrazione.

## Procedura per ottenere oracle affidabili

1. Scegliere il materiale con un criterio di campionamento scritto prima delle risposte. Non partire solo dai casi dove Gutsy ha già fallito. Registrare campioni scartati e motivi.
2. Due lettori etichettano indipendentemente senza vedere output Gutsy: segnali essenziali/insiemi accettabili per routing; gruppi AND/OR di capacità per tool; fatti necessari, recuperabilità e stato candidato per compaction. Disaccordi e dati insufficienti rimangono espliciti.
3. Adjudicare il disaccordo con un terzo passaggio e fonti. Una traccia osservata indica cosa è stato usato, non l'unica soluzione corretta; l'assenza di uso non basta a etichettare un tool o risultato come inutile.
4. Per compaction creare continuazioni controfattuali su stato pieno, troncato e recuperato. Il test deve misurare un requisito osservabile, non soltanto una parola citata nel seguito. Il futuro aiuta lo scorer, ma non entra nell'input alla decisione di compattare.
5. Congelare input, oracle, criteri di incompletezza e split per famiglia/provenienza prima del lancio unico. Non trasformare una successiva correzione dell'oracle in una modifica silenziosa del test già visto.

## Manifest del pacchetto cloud

Per ogni record: URL pubblico, repository/dataset, commit o revisione integrale, path e range, SHA256 dei byte, licenza verificata, autore/provenienza dell'etichetta, qualità gold/silver/unknown, famiglia e split, trasformazioni, permessi di distribuzione e stato di approvazione per l'upload.

Usare un'allowlist esplicita degli artefatti pubblici. Escludere `.env`, credenziali, chat personali, email, contenuti di account collegati e sorgenti privati. Un secret scan locale è un controllo aggiuntivo, non un'autorizzazione a caricare il resto; la redazione automatica non dimostra anonimizzazione o diritti.

Rimuovere dagli input titoli dei bug che rivelano la soluzione, messaggi del commit fix, test fail-to-pass, spiegazioni delle etichette e path scelti a posteriori come indizio del difetto. Se il path è un'informazione legittima della decisione, conservarlo in un braccio e anonimizzarlo in un altro, con mapping nello scorer. Non nascondere indiscriminatamente i path: il contrasto serve proprio a misurare una dipendenza indebita da nomi.

Per Git branches usare `git show` e `git diff` su revisioni fissate, non checkout del ramo di lavoro corrente. Coprire prima/dopo fix, stessa modifica su base diversa, candidato cambiato dopo un test, merge base e parent differenti, file rinominato/spostato e più rami di controllo nel codice. La coppia prima/dopo non è automaticamente positiva/negativa per i tool: anche il codice corretto può richiedere la medesima verifica.

## Limiti della ricognizione

Sono state lette fonti primarie e metadata locali, non scaricati o eseguiti i benchmark esterni. Le licenze del codice BFCL/ToolRet/LongMemEval sono state controllate; la catena completa dei diritti dei dati aggregati non è stata verificata. Non è stata verificata la pubblicità/licenza di Jupiter. Questa nota propone selezione e labeling; non attesta che il corpus proposto sia già pronto per Modal.
