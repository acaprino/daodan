# Reviewer specializzati e reviewer composti

Decisione chiarita il 23 ottobre 2026: scrivere prima tutti gli specialisti
necessari. I reviewer ampi possono esistere come unione generata di specialisti,
raggruppati per temi o controlli affini. La priorità resta la copertura; ridurre
codice, istruzioni e costo senza sacrificare efficacia, evidenza o verifiche.

## Modello approvato

- **Specialista:** una responsabilità focalizzata, un metodo canonico, input,
  controlli e controevidenza propri. Può essere incaricato singolarmente oppure
  incluso in una composizione. Non serve un reviewer per ciascuna voce tematica
  se più controlli rispondono alla stessa domanda con evidenza affine.
- **Reviewer composto:** un incarico generato dall'unione degli specialisti
  pertinenti. Può rappresentare un'area ampia oppure un contesto specifico.
  Le sue istruzioni specialistiche provengono dalle definizioni canoniche;
  nessuna checklist parallela mantenuta a mano.
- **Regole comuni:** scope, snapshot, autorizzazioni, evidenza, provenienza,
  copertura e consegna definiti una volta e riusati da entrambi.

La composizione riguarda il contenuto del reviewer: non equivale semplicemente
ad avviare i vecchi reviewer ampi e aggregarne i report. Un composto può coprire
più specialisti in un incarico compatibile; il numero di esecuzioni segue il
contesto, i limiti e i requisiti di indipendenza. Il consolidamento dei finding
rimane un passaggio distinto.

Sono previste due forme della stessa composizione: insiemi tematici predefiniti
e insiemi ad hoc selezionati per la review. I primi dichiarano membri nel registro
esistente; i secondi derivano da target, requisiti, sorgenti/configurazioni e
grafo di Codebase Map. Non serve riprogettare ogni insieme a runtime. Il grafo
aiuta la selezione e dichiara i propri limiti; un dato assente non dimostra che
un controllo sia inapplicabile. Entrambe le forme usano gli stessi specialisti
e conservano gli obblighi di copertura e indipendenza.

Il mandato dei contratti resta in `api-contract-auditor`: verificare la fonte
autorevole, i tipi e mock derivati, il payload realmente serializzato,
varianti/errori/nullabilità e compatibilità producer/consumer. Un tipo condiviso
può bastare in un confine atomico; non si impone un formato nuovo senza necessità.
La sequenza di concordare il contratto prima di dividere il lavoro tra producer
e consumer appartiene al lifecycle. Lo specialista ne verifica gli esiti.

## Esempi di composizione

| Reviewer ampio generato | Specialisti riusati, secondo il target |
|---|---|
| Sicurezza | Autorizzazioni/tenant, sessioni/deleghe, segreti, ingressi non fidati, confine browser, callback, confini AI, audit e dipendenze |
| Prestazioni | Query SQL, capacità/quote, costi, pool, efficacia della cache e specialisti dello stack applicabili |
| Operatività | Osservabilità, compatibilità dei rilasci, ambienti, recupero e salute del servizio |
| Accessibilità | Navigazione/semantica/focus e percezione/feedback/reflow |
| Review di un consumer AMQP | Consegna messaggi, idempotenza degli effetti, consistenza delle scritture e contratti del payload pertinenti |

Le righe sono esempi, non nuovi profili o registri runtime. Uno stesso specialista
può partecipare a più composizioni. Il nome ampio non rende applicabile ogni suo
membro; la selezione conserva tutti i controlli richiesti dal target e dichiara
l'incertezza. Controlli mancanti nel composto si correggono nello specialista
canonico o aggiungendo lo specialista necessario.

## Mapping iniziale per la scrittura degli specialisti

I nomi seguenti sono mandati da materializzare o verificare, non nuove identità
già registrate. Gli ID T/S richiamano l'inventario allegato. Questa mappa copre i
temi ma non certifica la completezza dei corpi o fissa un numero di agenti.
Una riga che riveli domande indipendenti va ulteriormente scomposta durante la
scrittura; controlli con lo stesso metodo possono condividere uno specialista.

| Mandato specialistico | Temi e confini |
|---|---|
| Autorizzazioni e isolamento tenant | T01 RLS, T02 bypass, T03 IDOR, T05 least privilege |
| Sessioni e deleghe temporanee | T04 scadenza/rinnovo/revoca, T06 URL firmati e binding della risorsa |
| Protezione dei segreti | T08 esposizione, accesso e gestione delle credenziali |
| Validazione degli ingressi | T07 controlli server e contratto effettivo dell'input |
| Accesso a destinazioni e file non fidati | T14 SSRF, T15 upload: risoluzione, storage e uso effettivo della risorsa |
| Sicurezza del confine browser | T12 XSS, T13 CSRF, T16 header e policy effettiva |
| Autenticità dei callback | T09 e parte sicurezza di T44 webhook di pagamento |
| Confini AI e autorizzazione dei tool | T11 prompt injection e parte sicurezza di S03 |
| Attribuzione e integrità dell'audit | T33 attore, azione, integrità e accesso al log |
| Rischi delle dipendenze | T10, riusando il metodo esistente |
| Atomicità e consistenza delle scritture | T17 race persistenti, T18 idempotenza locale, T19 transazioni, S01 vincoli SQL |
| Coerenza delle rappresentazioni persistenti | `schema-coherence-auditor`: DDL applicato, ORM, SQL, trigger e viste; nuove constraint confrontate con i writer esistenti |
| Coerenza della cache | T23 chiavi, invalidazione e relazione con il dato autorevole |
| Retention e cancellazione | T50 copie, derivati, replay e ripristino |
| Efficienza delle query SQL | T20 indici, T21 N+1, piani, cardinalità e round trip |
| Lifecycle di connessioni e pool | T22 acquisizione, capacità, restituzione, cancellazione e shutdown |
| Capacità e quote | T24 limiti, identità e amplificazione del carico |
| Consumo e costi | T36 unità fatturate, moltiplicatori, budget e segnali |
| Progresso dell'esecuzione locale | T26 job, T27 attese locali, T28 retry, T29 backoff; conservare il mandato temporal focalizzato |
| Consegna dei messaggi | T30 DLQ, S02 ack/redelivery e ordinamento |
| Idempotenza degli effetti remoti | T18 remoto e parte effetti/replay di T44 |
| Deadline tra servizi | T27 budget end-to-end e propagazione |
| Prerequisiti e ordine di inizializzazione | T34 prima readiness, T37 ordering; mandato di chicken-egg |
| Rilevazione e diagnosi dei guasti | T31 error monitoring, T32 log, T34 salute a regime, T35 alert |
| Compatibilità del rilascio | T37 coesistenza schema/versioni, T38 rollback, T41 continuità |
| Configurazione e isolamento degli ambienti | T40 staging e binding effettivi |
| Ciclo di vita dei feature flag | T39 default, attivazione e disattivazione; regole di dominio all'owner relativo |
| Recuperabilità di dati e servizio | T47 backup, T48 restore, T49 disaster recovery |
| Navigazione accessibile | T45 semantica, tastiera, focus e raggiungibilità dei percorsi critici |
| Percezione e feedback accessibili | T45 alternative, errori/stati, contrasto, reflow e cascata effettiva |
| Interleaving della UI | T17 UI/render/eventi; mandato di ui-race |
| Compatibilità browser e dispositivi | T46 target/versioni, API, input e lifecycle |
| Contratti producer/consumer | T43 implementazione, S02 payload, S03 output/tool schema |
| Protezione delle journey e dei contratti | T42 E2E, T43 test e oracoli indipendenti |
| Protezione della capacità | T25 workload, oracoli ed evidenza dei test di carico |
| Valutazione e regressioni AI | S03 variabilità, requisiti e protezione delle regressioni |
| Invarianti del processo di dominio | T17 dominio, T18 identità business, T39 regole dei rami, T44 pagamento |

La mappa non esaurisce i mandati già presenti. Correttezza locale, cleanup,
workspace, astrazioni e specialisti di linguaggio/stack vanno censiti con la stessa
regola: conservare una responsabilità focalizzata oppure derivare l'area ampia
unendo specialisti. Chicken-egg e UI race possono restare specialisti canonici
quando il loro mandato soddisfa quel criterio. La loro conservazione non autorizza
checklist generiche aggiuntive.

Derivazione delle premesse, verificatori e critic mantengono i propri mandati di
processo e contesti indipendenti. Non vengono assorbiti in una composizione che
ne comprometta l'indipendenza.

## Fonte unica e semplicità

Riusare registro, contratti, selettore e consegne esistenti. Nessun secondo
catalogo runtime o framework di agenti è richiesto da questa decisione.
Il registro deve riconoscere le unità specialistiche e, quando implementata,
la composizione deve riferire quelle unità anziché copiare controlli tra owner.
Le definizioni degli insiemi e il brief del contesto non contengono nuovi metodi.

Ogni controllo si scrive una volta, nel suo specialista. Il composto riusa i
contenuti selezionati, rimuove soltanto ripetizioni identiche e include le regole
comuni una volta. Una generazione non riscrive liberamente i metodi con un modello.
Le correzioni alla fonte si propagano alle composizioni che la usano.
Non unire incarichi incompatibili per input, autorizzazioni o indipendenza.
Budget e limiti non trasformano omissioni in copertura riuscita.

### Invarianti recuperati ed esclusioni esplicite

Dalle quattro specifiche storiche del 22 ottobre restano vincolanti cinque
invarianti operativi, integrati nei contratti esistenti:

1. **Modalità e base di giudizio (`review_basis`):** `changeset` valuta il delta;
   `full` e `dir` valutano il contenuto corrente (`content`) senza fabbricare un
   diff artificiale e senza scartare difetti preesistenti fuori dagli hunk;
   `doc`/`spec`/`plan` valuta le affermazioni del documento.
2. **Perimetro delle conclusioni vs letture (`conclusion_paths` e `read_scope`):**
   i finding sono emessi sui percorsi in scope, ma il reviewer legge caller,
   callee, contratti e guardie in `read_scope` per verificare la premessa e la
   controevidenza.
3. **Incertezza a tre stati e dipendenze:** un prerequisito o controllo non
   verificabile resta `unknown` (gap esplicito), mai `no` o non applicabile.
   Le modifiche a `dependencies` propagano l'attivazione ai consumer pertinenti.
4. **Contabilità per incarico e scope:** ogni job è tracciato con identità logica
   e scope distinti; due method binding su `project-protocol:isolated-worker`
   (`python-method` e `dependencies-method`) o due scope diversi dello stesso
   specialista non si soddisfano a vicenda.
5. **Deconflitto per causa:** l'owner segue il contratto o meccanismo violato
   (es. blocco statico CSS a `accessible-perception-auditor` /
   `accessible-navigation-auditor`, race di render/focus a `ui-race-auditor`,
   race persistente su DB a `transaction-integrity-auditor`, race locale in
   memoria a `local-concurrency-auditor`).

Sono esclusi (non-goal): l'introduzione dei nove nuovi schemi `v2` separati,
l'espansione a otto gate obbligatori distinti per ogni review in `required_gates`,
la macchina di authoring a dodici stati con `reviewer_authoring.py` e il doppio
freeze separato per il passaggio blind di `premise-auditor`.

## Ordine del lavoro e criteri di completamento

1. Censire gli attuali reviewer e completare la suddivisione in responsabilità
   focalizzate, mantenendo la copertura oltre ai cinquanta temi dell'allegato.
2. Scrivere e registrare tutti gli specialisti canonici, riusando quelli già
   adeguati. Per ciascuno: quando serve, input, controlli, controevidenza,
   confini, risultato compatto e lacune esplicite.
3. Verificare specialisti su casi con difetto e alternative corrette, integrazione
   nei cinque host e consegne. Conservare evidenza e protezione indipendente.
4. Generare i reviewer ampi e quelli ad hoc dall'unione degli specialisti validati.
   Verificare che ogni membro richiesto sia presente e che i suoi controlli,
   provenienza e limiti siano conservati, senza aggiunte manuali divergenti.
5. Migrare i vecchi corpi ampi quando la sostituzione ha copertura verificata.
   Preservare floor e gate obbligatori fino al loro riallineamento esplicito.

I passi 1-3 costituiscono la prima fase richiesta. Il passo 4 viene dopo:
la composizione è il modello di destinazione approvato, non un'infrastruttura
che deve precedere la scrittura degli specialisti.

Il [piano di implementazione](../plans/2026-10-23-specialist-reviewers-and-composition.md)
definisce file, migrazione, consegne e verifiche per queste due fasi.

## Stato e verifiche dell'implementazione precedente

Il lavoro del 22 ottobre ha aggiunto tre reviewer ancora ampi e riscritto altri
corpi, centralizzando convenzioni e migliorando integrazione e selezione.
Non ha completato la specializzazione qui richiesta e non ha implementato la
composizione. I suoi test e misure documentano quel candidato intermedio, non
l'avvenuta realizzazione del modello chiarito.

Conservare le parti riusabili e trattare i corpi ampi come materiale da scomporre;
non considerarli fonti parallele definitive. Il
[resoconto precedente](../reports/2026-10-22-specialized-reviewers-verification.md)
conserva risultati e limiti. Le quattro proposte storiche restano inventari di
rischi e scenari; le loro strutture aggiuntive non diventano requisiti impliciti.

Il mantra in CLAUDE.md e AGENTS.md resta vincolante. Misurare copertura utile,
falsi positivi e costo dell'intero run. Parole in meno nei sorgenti non dimostrano
risparmio di token o efficacia equivalente. La semplificazione delle modalità
pubbliche full/changeset/dir/doc resta un intervento distinto.
