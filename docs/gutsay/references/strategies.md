# Campagna Gutsy CPU: strategie, percorsi e singolo lancio Modal

Data: 26 ottobre 2026. Stato: proposta di disegno; nessun codice, corpus, risorsa o nuova inferenza creati da questa ricerca. Il [primo pilot](../pilot-results-2026-10-26.md) è la fonte osservata: 314 domande, 47 richieste, 36/45 segnali essenziali routing, tool sufficienti 5/14, tre perdite critiche per ciascun braccio compaction. Il pilot serve come diagnostica già osservata, non come nuovo test di conferma.

## 1. La struttura causale

La campagna principale usa un profilo CPU fissato. Confronta le strategie sugli stessi casi e sullo stesso contenuto informativo. Solo dopo confronta profili di runtime su un sottoinsieme bloccato in anticipo. Un unico lancio può eseguire tutti questi blocchi in sequenza; non occorre incrociare ogni strategia con ogni thread, contesto e ordine.

Fissare separatamente cinque fattori: rappresentazione dello stato; forma delle domande; politica di astensione/soglia; protezioni del controller; profilo di inferenza. Il primo confronto cambia un fattore alla volta o un piccolo fattoriale esplicito. La successiva composizione dei componenti migliori si verifica su famiglie non usate per sceglierli. La selezione adattiva del vincitore deve essere preregistrata e non usare il gruppo finale.

## 2. Routing: bracci comparabili

| Braccio | Procedura | Costo e interpretazione |
|---|---|---|
| R0 | Soli fatti verificabili del run e fallback prudente per il resto | Zero inferenze. Baseline che isola quanto valore aggiunge davvero il modello |
| R1 | Dieci segnali Gutsy, formato del primo pilot | Dieci domande; controllo della procedura originale |
| R2 | Fatti verificabili più `choice` sulla profondità e sull'ambiguità | Due domande residue al massimo; candidato principale per leggerezza |
| R3 | Stessi fatti di R2, profondità tramite domande binarie con confini positivi/negativi e chiarimento separato | Tre o quattro domande, secondo l'albero dichiarato. Non fingere che due bit producano tutte le cinque classi di profondità più ambiguità |
| R4 | R2 con astensione e fallback derivati dal gruppo di calibrazione | Riusa le probabilità di R2; non richiede ulteriori inferenze, salvo la verifica finale di runtime |

I fatti derivati non devono essere etichette dell'oracle reinserite nello stato. Usare soltanto campi che il controller avrebbe davvero al momento della richiesta: ruolo dichiarato, scope autorizzato, allegati effettivi, fase, capabilities necessarie e dimensioni misurate. Se una fonte è assente, il valore rimane sconosciuto. Nessuna regola può abbassare un minimo di rischio già accertato.

R1 e R2 ricevono lo stesso insieme di fatti: se R2 vede metadati aggiuntivi, si sta confrontando l'intera procedura, non la sola qualità del classificatore. Per ogni fatto derivato conservare provenienza, regola e valore prima di interrogare Gutsy. Separare errore della derivazione, errore della classificazione ed errore finale del tier.

Per R3 dichiarare l'albero esatto prima del test. Esempio: prima discriminare la necessità di analisi architetturale/review avversaria, poi distinguere quella classe se necessario; altrimenti scegliere lookup/local_edit/multi_step; chiarimento resta una decisione indipendente. Se l'albero produce soltanto un minimo tier invece degli enum esistenti, è un contratto diverso e non si può attribuirgli accuratezza su tutti i dieci segnali.

Una baseline LLM corrente è utile su un sottoinsieme rappresentativo, ma aggiunge chiamate provider e costo separato. Un modello eseguito da remoto non diventa CPU locale perché il controller è su Modal. La verità rimane l'oracle indipendente e, dove disponibile, il successo verificato del lavoro, non l'accordo con l'LLM.

## 3. Tool selection: cinque procedure

| Braccio | Procedura | Rischio da rendere osservabile |
|---|---|---|
| T0 | Tutti i tool eleggibili dopo permessi e disponibilità | Controllo di sufficienza; massimo costo schemi, zero inferenze |
| T1 | `noul` per ogni tool eleggibile | Baseline piatta; domande proporzionali al catalogo |
| T2 | Multi-label sulle famiglie, poi sui tool delle famiglie selezionate | Una famiglia esclusa può rendere irrecuperabile il tool necessario; misurare l'intera catena |
| T3 | Retrieval deterministico di candidati, poi Gutsy sui candidati | Misurare recall del retrieval prima del reranking; non attribuire al modello un candidato già perso |
| T4 | Minimo obbligatorio del metodo, Gutsy sui dubbi opzionali e discovery recuperabile | Il minimo deve provenire da un contratto preesistente, non dall'oracle scritto per il caso |

Nella prima fase tenere uguali descrizioni e catalogo; variare la procedura. In un blocco distinto usare cataloghi di 8/16/64/256 strumenti con distrattori, alias, ordine permutato, famiglie nuove, tool equivalenti e tool necessari complementari. Il catalogo grande non obbliga a interrogare tutti i candidati per ogni caso della campagna: usarlo come strato di stress preregistrato, con un budget dedicato.

Per T3 congelare retrieval e K prima del gruppo finale. Un BM25/lexical retriever può essere un confronto semplice, ma la qualità va misurata; il nome del tool non è una fonte di verità. Una lista esclusiva `choice` sull'intero catalogo non modella un set multi-label. Le alternative OR, come lettura via tool specializzato o fetch pubblico equivalente, devono restare accettabili.

La discovery conserva un percorso di recupero, non rende già riuscito il lavoro. Contare richieste aggiuntive, schemi effettivamente caricati, tempo totale e casi in cui l'utente deve intervenire. Ordinare i tool senza ridurre lo schema non dimostra risparmio di contesto. Non consentire che il recupero o un minimo obbligatorio nascondano le omissioni grezze.

## 4. Compattazione: un fattoriale piccolo ma utile

Conservare `compact` upstream per accoppiamento e ricostruzione. Per ogni caso breve confrontare 3 rappresentazioni per 2 domande, cioè **sei bracci**, ognuno con due domande per coppia candidata:

| Rappresentazione | Q0: domande upstream | Q1: domande coerenti con ripetibilità e compito aperto |
|---|---|---|
| C0: output omesso, come upstream | Controllo originale | Isola la formulazione pur senza contenuto |
| C1: risultato completo visibile | Ripete il braccio B del pilot | Isola la formulazione quando l'evidenza è accessibile |
| C2: scheda breve meccanica con provenienza, errori/estratti e riferimenti | Isola la perdita dovuta alla scheda | Candidato più leggero, se conserva i fatti necessari |

La scheda non deve essere costruita scegliendo gli estratti perché si conosce la risposta del caso. Se non contiene un fatto necessario, classificare l'errore come perdita di rappresentazione prima della decisione Gutsy. Gli output che non entrano integralmente non vanno tagliati silenziosamente: registrare il limite e usare il braccio di recupero previsto.

Esempio di Q1 da affinare solo sul gruppo di sviluppo: «Does this result contain evidence required for the current open task that is not preserved elsewhere or recoverable from the same immutable source?». Il testo deve distinguere fonte immutabile recuperabile, fonte mutabile e azione non ripetibile. La conservazione in caso di incertezza è una politica del controller, non una risposta positiva inventata del modello.

Applicare protezioni off/on **alle stesse risposte salvate**, senza moltiplicare le inferenze. Separare qualità grezza, evidenza salvata dalle regole, byte/token recuperati e costo del recupero. La soglia può essere valutata offline con curve sul gruppo di calibrazione, poi fissata prima del test finale.

Per stati lunghi aggiungere un blocco separato: finestre per candidato con unione; retrieval di risultati/estratti; struttura gerarchica con riferimenti. Il precedente locale con 312 chiamate su un caso mostra perché una semplice unione di molte finestre non è già una strategia economica. Misurare anche inflazione delle conservazioni e dipendenze fra finestre.

**Caso indispensabile:** due risultati duplicano lo stesso fatto. Ciascuno è eliminabile se l'altro resta; decisioni indipendenti possono eliminarli entrambi. L'oracle deve quindi verificare il set finale e la continuità del compito, non soltanto keep/drop per ogni risultato isolato.

## 5. Percorsi e rami da coprire

| Gruppo | Esempi di percorsi |
|---|---|
| Operazione ordinaria | ingresso, diagnosi, modifica, test, review, report; stesso obiettivo ma fase e prove differenti |
| Informazione incompleta | metadato assente, allegato dichiarato ma mancante, conflitto fra fonti, ambiguità, nessuna opzione valida, dato fuori finestra |
| Permessi e disponibilità | tool revocato, provider assente, discovery presente/assente, inventario cambiato dopo classificazione, authorization scaduta |
| Stato e recupero | timeout prima/dopo risposta, retry, cancellazione, risultato pendente, fonte modificata, errore su SHA A seguito da candidato B, duplicati e riordinamento |
| File e Git | path Windows/POSIX, rename, file omonimi, generated/vendor; stessi path su due commit/branch con contenuti diversi, merge-base, dirty overlay e patch non applicata |

I branch Git sono snapshot read-only con commit identificati, non branch di lavoro da creare, checkoutare o modificare durante la prova. Rappresentare separatamente commit, branch label e contenuto: la branch chiamata `production` non è prova da sola che l'operazione tocchi dati di produzione. Le prove su SHA diversi non si trasferiscono automaticamente. Non simulare successo semplicemente cambiando una label mentre i byte rimangono identici.

Per i percorsi multi-step controllare invarianti dopo ogni transizione e al termine: nessun binding obsoleto, nessun tool inventato, nessun fatto critico perso e nessuna riesecuzione con effetto esterno. Se sono esecutori simulati, chiamarli replay/contratti, non successo reale di un agente software.

## 6. Profili runtime e significato di “una macchina”

Il runtime verificato supporta n_ctx e thread; il limite modello è 8.192 token per stato più singola domanda e involucro. Fino a 64 domande possono stare nello stesso POST, ma ogni domanda è una valutazione separata. `choice` supera 16 opzioni solo tramite shortlisting, con altre chiamate; `score` non è intercambiabile con il tipo score di fast-jev e non serve a questi contratti. [Engine fissato](https://github.com/kouhxp/gutsy/blob/db5c2ec62fc81703938adbd714915b53a9fb0de1/gutsy-inference/gutsy_inference/engine.py).

Eseguire la qualità principale su un solo profilo. Profilare un sottoinsieme bilanciato con n_ctx 1.536/4.096/8.192, thread 1/2/4, stati utili più distrattori da circa 512/1.200/3.500/7.000 token nei soli incroci che entrano realmente. Le lunghezze includono domanda e involucro; 7.000 è un ordine di grandezza da rendere esatto col tokenizer, non una licenza a superare il budget.

Un container con quattro core e thread 1/2/4 misura scaling dei thread sul medesimo host, **non** quote fisiche da uno/due/quattro core. Quote CPU differenti richiedono contenitori differenti o un meccanismo di limitazione verificato; non attribuire loro identica macchina o identico hardware. Fissare richiesta e limite della Function, registrare topologia e disponibilità effettiva. [Risorse Modal](https://modal.com/docs/guide/resources).

Tre condizioni cache da distinguere:

1. Full re-encoding: `Engine(use_cache=False)` richiede un bootstrap sperimentale, perché Registry/CLI non espongono quel parametro.
2. Cache intra-POST con LRU tra richieste disattivata: `cache_entries=0` non elimina lo snapshot locale condiviso fra le domande dello stesso POST.
3. Cache intra/inter-POST: configurazione ordinaria con LRU una entry e budget dichiarato.

Questa distinzione è verificata nel sorgente `_run_with`; non inventare un flag CLI cache-off. Per una sola domanda, la misura deve stabilire se il costo di snapshot è utile. Conservare sempre self-check, state_cached, cache hit, evaluated_tokens, model_calls e differenze delle risposte. La calibrazione generica non garantisce equivalenza fra percorsi numerici diversi.

Riavviare il server come sottoprocesso fresco per ogni profilo; lasciare un solo modello residente. Escludere warm-up dal percentile a caldo ma conteggiarlo nel costo. Congelare ordine controbilanciato dei profili/casi, ripetizioni e seed, così cache, page cache e ordine non rendono artificialmente vincente il primo o l'ultimo braccio.

## 7. Un lancio lungo su Modal: contratto da costruire

Una Function Modal può avere timeout fino a 24 ore, per tentativo. Un lancio da 6–12 ore è quindi compatibile con il limite documentato; scheduling e build restano separati. Il codice deve avere anche una deadline propria. Il pilot corrente ha hard-code a 1.800/2.400 secondi e filesystem effimero: non è già un esecutore di questa campagna. [Timeout](https://modal.com/docs/guide/timeouts).

Proposta: un'App effimera, una Function, `max_containers=1`, un input contenente l'intera schedule preregistrata e nessuna `Function.map` parallela. Nel container, blocchi e profili sono sequenziali. È un singolo lancio riuscito su un container; non si può promettere lo stesso host fisico se il container viene perso e rischedulato.

Usare un Volume dedicato per manifest, ledger, risultati e asset verificati. Salvare risultati immutabili per chiave composta da caso/variante/profilo/tentativo e hash degli input. Prima dell'inferenza registrare e committare l'avvio del tentativo; dopo salvare risposta e commit. Un tentativo iniziato ma senza esito rimane unknown e non viene scambiato per un No. Su ripresa verificare gli hash e saltare soltanto risultati completi validati. Il Volume richiede commit per rendere visibili le modifiche all'esterno; il filesystem effimero del pilot non basta. [Volumes](https://modal.com/docs/guide/volumes).

**Limite importante:** `retries=0` non garantisce zero rischedulazioni dopo un crash/OOM del container. Le App effimere possono riprovare fino alla soglia di guasto; i deployment possono continuare a riprovare. Contatore tentativi e deadline globali devono sopravvivere nel Volume, così un restart non ricrea il budget da zero. Terminare il sottoprocesso colpevole prima che esaurisca la memoria dell'intero container. [Crash e retry](https://modal.com/docs/guide/retries).

Il percorso predefinito deve conservare esiti parziali e marcare failure/incomplete quando scadono limite economico, tempo o numero di domande. Non selezionare automaticamente i casi più facili per far rientrare il costo e dichiarare poi “tutti completati”. Per un run lungo usare detach o una modalità di lancio persistente supportata, trattenendo app ID, stop esplicito e possibilità di scaricare il Volume anche senza client locale. [App effimere](https://modal.com/docs/guide/apps).

## Priorità e decisione finale proposta

1. Congelare casi, oracle, manifest e schedule causale; il volume di varianti non sostituisce famiglie indipendenti.
2. Misurare prima il valore marginale di R2 e T4 rispetto a regole e fallback, mantenendo R1/T1 come controlli.
3. Eseguire il fattoriale 3×2 della compattazione e le invarianti sul set finale; nessuna omissione critica può essere compensata da token risparmiati.
4. Separare profilazione CPU/cache dalla selezione semantica; tenere conto dell'intero percorso e dei recuperi.
5. Costruire checkpoint e budget globali prima del run lungo; concludere per dominio: promettente da verificare sul locale, limitato a shadow/advisory, oppure inadatto al contratto testato.

Il go richiede sicurezza, utilità e leggerezza insieme sull'insieme finale non usato per scegliere la strategia. Un risultato negativo può essere utile: input carente richiede una rappresentazione migliore; buona selezione ma ritardo alto richiede meno domande o invocazioni meno frequenti; false esclusioni richiedono astensione/protezioni; fallimenti persistenti anche con evidenza completa e domanda adeguata giustificano solo allora valutare un diverso modello o una specializzazione futura.
