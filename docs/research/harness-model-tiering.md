# Tiering dei modelli dell'harness: evidenze e applicazione al plugin

Data: 2026-11-07. Stato: ricerca e proposta di sviluppo; nessun modello qualificato e nessuna modifica applicativa.

Documento collegato: [routing automatico programmatico](programmatic-review-routing.md). Qui si costruisce il profilo dei candidati; nell'altro report si decide quale configurazione usare per ciascun job.

## TL;DR

1. **Scoprire non significa qualificare.** Il catalogo del runner identifica i candidati configurati; un probe verifica un comportamento attraverso quell'harness; soltanto una valutazione pertinente alla review può sostenere un livello di capacità.
2. **Prezzo, contesto e qualità restano separati.** Il prezzo serve a scegliere tra candidati idonei, il contesto a verificare compatibilità e uso delle informazioni. Nessuno dei due assegna da solo T1–T4.
3. **Qualificare configurazioni, non nomi commerciali.** La misura riguarda modello/alias, provider, effort, prompt, tool e metodo di review. I risultati di un modello senza tool non qualificano automaticamente il relativo agente.
4. **T1–T4 sono una convenzione del plugin, non uno standard scientifico.** Se utili, devono rappresentare livelli di qualificazione per famiglia di review, con criteri pubblici. Un candidato sconosciuto resta non classificato, non diventa T1.
5. **Prima implementazione consigliata:** catalogo normalizzato, piccoli probe deterministici, benchmark di review con oracolo dei finding e tabella versionata. QueRE è un possibile esperimento successivo: richiede molte interrogazioni e un predittore appreso.

## Perimetro e metodo

Lettura dei testi primari HTML delle versioni indicate, con controllo delle sezioni metodologiche, dei risultati e dei limiti pertinenti; consultazione delle appendici rilevanti quando disponibili. Questo report sostituisce, per questi riferimenti, le precedenti descrizioni basate sui soli estratti della ricerca fallita. Non è una revisione sistematica dell'intera letteratura né una riproduzione degli esperimenti.

I risultati numerici sotto sono **riportati dagli autori**, non misure del nostro plugin. Le proposte operative sono esplicitamente distinte dalle conclusioni dei paper. Gli artifact collegati sono quelli indicati dalle fonti: il loro codice non è stato eseguito o sottoposto ad audit. Le versioni sono fissate per rendere tracciabile la lettura, senza sostenere che siano sempre le più recenti.

## Paper citati

| ID | Paper, autori e versione | Che cosa studia | Uso nel plugin e limite principale |
|---|---|---|---|
| H1 | Dylan Sam, Marc Finzi, J. Zico Kolter. [Predicting the Performance of Black-box LLMs through Self-Queries](https://arxiv.org/html/2501.01558v2), 2025, arXiv v2. [Codice QueRE](https://github.com/dsam99/QueRE). | Feature ottenute interrogando modelli black-box; predizione di correttezza, rilevamento di prompt avversari e distinzione tra modelli. | Profilazione comportamentale possibile, ma supervisionata e costosa rispetto a un semplice controllo di compatibilità. |
| H2 | Xiaoyan Bai, Aryan Shrivastava, Ari Holtzman, Chenhao Tan. [Know Thyself? On the Incapability and Implications of AI Self-Recognition](https://arxiv.org/html/2510.03399v1), 2025, arXiv v1. [Codice](https://github.com/ChicagoHAI/self-recognition). | Riconoscimento degli output e consapevolezza della famiglia del modello. | Non usare un modello come autorità sul ranking; non confondere attribuzione degli output e autodescrizione. |
| H3 | Kiran Kate, Yara Rizk, Poulami Ghosh, Ashu Gulati, Tathagata Chakraborti, Zidane Wright, Mayank Agarwal. [How Good Are LLMs at Processing Tool Outputs?](https://arxiv.org/html/2510.15955v2), 2025, arXiv v2. [Dataset e codice](https://github.com/LongFuncEval/toolJSONprocessing). | Comprensione di risposte JSON reali, lunghezza, posizione, schema, generazione di codice e risposta diretta. | I probe devono controllare anche l'uso del risultato del tool; non è una valutazione del tool calling end-to-end. |
| H4 | Adarsh Prasad Behera, Jaya Prakash Champati, Roberto Morabito, Sasu Tarkoma, James Gross. [Towards Efficient Multi-LLM Inference: Characterization and Analysis of LLM Routing and Hierarchical Techniques](https://arxiv.org/html/2506.06579v1), 2025, arXiv v1. | Survey di routing, cascata e vincoli operativi. | Separare qualità, latenza e costo; non fornisce una classificazione universale dei modelli o una validazione sulla nostra review. |
| H5 | Shweta Ramesh et al. [Automated Code Review Using Large Language Models at Ericsson: An Experience Report](https://arxiv.org/html/2507.19115v2), 2025, arXiv v2; la [scheda](https://arxiv.org/abs/2507.19115v2) dichiara accettazione a ICSME 2025. | Review Java con metodo contenitore estratto da Tree-sitter e valutazione di sviluppatori. | Valutare il sistema nel workflow reale; campione piccolo, risultati preliminari e nessun classificatore automatico dei modelli. |

La presenza su arXiv non è, da sola, attestazione di peer review. Lo stato editoriale è indicato soltanto quando risulta dalla fonte consultata. I paper su review difettuale e agenti di sicurezza, condivisi dai due filoni, sono analizzati come R4–R5 nel [report sul routing](programmatic-review-routing.md#paper-citati).

## Lettura critica

### H1 — QueRE: segnali utili, non un'intervista sulle capabilities

Il metodo genera una risposta al task, pone domande successive e usa le probabilità di risposta, insieme ad altri segnali, come input di un classificatore lineare. Il paper descrive circa **50 domande di elicitazione** come sufficienti per buone prestazioni nel suo setting (§3.1); quando le probabilità non sono esposte dall'API, propone di stimarle tramite campionamento, con costo aggiuntivo. Parte delle domande è stata generata con GPT-4 (§3.2).

Gli esperimenti (§4) comprendono QA aperto e chiuso, fra cui Natural Questions, SQuAD, BoolQ, HaluEval e DHate, e modelli Llama e GPT. La valutazione principale usa AUROC per predire la correttezza di una risposta: è una misura diversa dal successo del revisore nel trovare un difetto. Nella Tabella 1, su BoolQ e GPT-4o-mini, la classificazione fra modello con prompt di sistema innocuo e avversario raggiunge **0,9547** con QueRE, contro **0,5725** per la sola pre-confidence. Sul setting CodeContests la relativa accuracy arriva a **1,0000**: questo è riconoscimento dell'influenza avversaria predisposta dagli autori, non rilevamento perfetto di bug in codice arbitrario.

La distinzione tra architetture/dimensioni (§4.3) è promettente per rilevare sostituzioni fra candidati conosciuti. Non è attestazione crittografica dell'identità, né qualificazione garantita di un modello mai osservato. Il paper osserva anche che sequenze di linguaggio non interpretabili come domande possono fornire feature utili (§4.5): il segnale predittivo non dimostra introspezione fedele.

**Da usare:** l'idea di misurare comportamento e stabilità di un servizio black-box. **Da non importare nell'MVP:** decine di follow-up per ogni review o un classificatore appreso presentato come routing senza IA. Se sperimentato, confrontarlo con una semplice tabella di risultati, includendo etichette, chiamate aggiuntive e costo di riqualificazione.

### H2 — Identità dichiarata e riconoscimento degli output sono problemi diversi

Dieci modelli producono due corpora da **1.000 testi**, rispettivamente di circa 100 e 500 parole; ogni modello valuta i testi propri e degli altri (§3). Il task binario ha una baseline apparentemente forte: rispondere sempre «non mio» dà il **90%** di accuracy. L'attribuzione a uno dei dieci modelli ha baseline casuale del **10%**.

Il riconoscimento dell'autore resta vicino al caso. Esiste però un'incongruenza nella versione letta: introduzione e §4 scambiano l'associazione fra lunghezza del corpus e valori **10,3% / 10,9%**. Il risultato robusto da riportare è l'intervallo vicino al 10%, non quale lunghezza vinca. Nel corpus da 500 parole, **97,7%** delle attribuzioni va a GPT o Claude, che costituiscono solo il 40% dei generatori.

**Correzione importante alla lettura preliminare:** il test «Who are you?» (§5) dà riconoscimento della propria famiglia al **100% per nove modelli**, mentre GLM arriva al 50%, su dieci rollout. Questa sottovalutazione usa GPT-4.1-mini come giudice. Il paper non dimostra che tutte le autodescrizioni siano false: mostra che riconoscere la famiglia non implica attribuire correttamente gli output, conoscere l'esatto ID o classificare imparzialmente gli altri modelli.

**Da usare:** nomi come `mini`, `flash`, il marchio e l'opinione del modello non sono rubriche di qualificazione. **Gap:** il paper non testa prezzi, tool disponibili, limiti del gateway o mapping dell'effort; l'autorità di questi dati deve quindi restare nel runner/configurazione, per scelta ingegneristica e non per un risultato sperimentale di H2.

### H3 — Tool calling e comprensione del risultato richiedono prove separate

Il dataset comprende **1.298** domande su risposte di sei endpoint reali: 580 estrattive, 394 di filtraggio, 324 di aggregazione. Gli autori costruiscono il ground truth con codice Python e valutano **15 modelli** (§§2–3). Le risposte JSON medie dei diversi endpoint vanno da circa 24.000 a 74.000 **caratteri**, da non confondere con token. Gli esperimenti controllati sulla lunghezza arrivano invece a 80.000 token secondo il tokenizer indicato dal paper.

Il testo riporta come miglior accuracy di GPT-4o il **77%** e rileva sensibilità a lunghezza, posizione dei record, struttura e tipo di domanda. Generare codice per filtrare/aggregare e fornire lo schema può aiutare; non è un vantaggio uniforme per ogni domanda e modello (§§4.1–4.6). Le metriche includono exact match normalizzato, `contains` e un LLM judge: quest'ultimo viene esplicitamente descritto come permissivo e soggetto a falsi positivi (§3.1).

La proiezione JSON di §4.7 riduce la dimensione media da **60.968 a 5.056 caratteri**, con miglioramenti riportati di 8–38 punti a seconda del modello. Ma seleziona i dati conoscendo già la risposta corretta: è un **oracolo sperimentale**, non un filtro pronto per produzione.

**Da usare:** fixture con JSON realistico, record omonimi, campi simili, valori cambiati a ogni prova e risposta verificabile via codice. Testare estrazione e aggregazione separatamente. Per i nostri tool, preferire output strutturati piccoli e pertinenti, preservando prove e identificatori. **Da non dedurre:** JSON prodotto correttamente non prova structured outputs nativi; trovare un valore in 80k token non certifica review interprocedurale a 80k token.

### H4 — Profilo multidimensionale invece di graduatoria unica

La survey distingue routing iniziale e inferenza gerarchica/cascata, e considera vincoli di calcolo, memoria, energia, latenza, costo, scalabilità e modalità (§§II–IV). Molti metodi descritti impiegano predittori appresi: la presenza di un `argmax` o di una soglia nell'ultimo passo non rende l'intero sistema privo di ML.

**Da usare:** misurare costo e latenza del percorso completo e filtrare prima la compatibilità. La proposta di una metrica aggregata della survey non giustifica sommare direttamente dollari, secondi e recall senza normalizzazione e preferenze esplicite. Per un plugin piccolo bastano metriche distinte e selezione fra configurazioni qualificate; non serve implementare tutta la tassonomia.

### H5 — Review reale: contesto e utilità prima della dimensione del modello

La pipeline estrae diff e metodo Java contenitore con Tree-sitter, invoca l'LLM e raccoglie feedback nel workflow Gerrit/VS Code (§§III–V). Otto dei nove esperti completano il primo survey su dieci metodi. Nel trial di quindici giorni, **4/9** dichiarano risparmio di tempo; le critiche comprendono spiegazioni inutili, inesattezze e contenuti irrilevanti (§VI).

I confronti fra modelli 7B e 13B non sostengono una classifica universale. Il testo dichiara 36 valutazioni pairwise, ma i voti mostrati nella Tabella II sommano a **22**, senza una riconciliazione esplicita: riportare la discrepanza, non usare quei numeri per assegnare tier. Anche i 15 snippet con bug artificialmente inseriti, tutti trovati, sono dichiarati facili dagli autori.

**Da usare:** benchmark con contesto fornito dal nostro plugin e giudizio dei finding, più una verifica di utilità con sviluppatori. **Da non dedurre:** il metodo contenitore basta per qualsiasi difetto; 13B è sempre migliore di 7B; una review piacevole equivale a una review corretta.

## Cosa significa per il nostro plugin

### Stato attuale verificato

Il componente pertinente è `plugins/senior-review`. Il suo [review_roster.py](../../plugins/senior-review/skills/review-preparation/scripts/review_roster.py), `compute`, produce `tier`, `roster`, `signals`, `required_specialists`, `grounding` e `gaps`. Quel `tier` descrive il **rigore della review** (`light/small/medium/large`), non un modello LLM.

[composition.py](../../plugins/senior-review/skills/review-preparation/scripts/composition.py), `bind`, costruisce i job con scope, modalità, permessi, candidato, selezione della conoscenza e digest dei corpi. Nel contratto ispezionato non seleziona modello o effort. Il [verification panel](../../plugins/senior-review/skills/review-quality-gates/references/verification-panel.md) prescrive di ereditare il modello della sessione; un override richiede richiesta esplicita e supporto dell'host. La ricerca non modifica tale regola.

Nella precedente osservazione di questa sessione, il catalogo `opencode.models` del provider selezionato esponeva ID, varianti e costi, ma non limiti del contesto o capacità tool/schema. Una soglia `cost.tier.context.size` era una **fascia tariffaria**, non una context window. Questa osservazione non è una garanzia per ogni provider né una nuova verifica runtime; l'adapter deve seguire lo schema effettivo dell'host.

### Proposta: cinque passaggi, una sola tabella di qualificazione

1. **Enumerare tramite il runner che eseguirà i job.** Usare SDK/API/configurazione realmente disponibili, gestire paginazione e allowlist, conservare ID esatti. Il catalogo dei revisori in `plugin.toml` contiene ruoli, non modelli. Un catalogo di un altro servizio non allarga automaticamente i candidati eseguibili.
2. **Normalizzare solo dati utilizzati.** Identità provider/modello e varianti; prezzi con unità e condizioni; limiti/capacità solo quando dichiarati dalla fonte. Un valore assente resta sconosciuto. `active` non prova accessibilità, prezzo assente non significa gratuito, alias `auto` non significa modello fisso.
3. **Verificare compatibilità attraverso lo stesso adapter.** Una piccola suite controlla risposta, round-trip tool, struttura dell'output e contesto necessario. Il risultato è pass/fail/unknown con evidenza: non è ancora un tier.
4. **Misurare review reali su configurazioni selezionate.** Pochi candidati ed effort iniziali, stessi input e contratto, difetti confermati e controlli corretti. Separare valutazione del modello a contesto fisso e valutazione end-to-end dell'agente.
5. **Pubblicare qualificazioni riutilizzabili.** Per famiglia di review e configurazione, salvare copertura misurata, precision/recall, costo, latenza, numerosità e versione della prova. Il router legge questa tabella; non ripete i probe a ogni dispatch.

Non occorre un nuovo database: per il primo esperimento bastano artifact JSON/JSONL versionati nel benchmark e il meccanismo di stato già usato dall'host. La scelta definitiva della persistenza dipende dall'integrazione, non da questi paper.

### Probe minimi e significato del risultato

| Prova | Fixture concreta | Oracolo locale | Cosa non dimostra |
|---|---|---|---|
| Accesso | Richiesta breve al candidato e variante esatti | Esito API, timeout, errore provider, risposta | Qualità, identità fisica del backend o stabilità futura |
| Tool round-trip | Tool fittizio read-only con argomenti tipizzati; restituisce un valore casuale noto al test | Nome/argomenti validi e uso esatto del valore restituito | Affidabilità su tutti i tool o correttezza della review |
| Output | Schema semplice con campi obbligatori, enum e tipi | Validatore deterministico sul risultato | Supporto nativo allo schema se l'adapter usa solo un prompt; non bastano i backtick JSON |
| Contesto | Informazioni note a inizio/centro/fine, dipendenza fra due porzioni e distrattori; taglie vicine ai job previsti | Risposta attesa, richiesta accettata, token e truncation osservabile | Massima finestra reale o affidabilità su codice arbitrario; un errore di retrieval non prova truncation |
| Effort | Stesso caso e stessi limiti, due varianti documentate o esposte, repliche appaiate | Accettazione del parametro, telemetria disponibile, qualità e costo | Corrispondenza universale `high = high`; latenza/token diversi non provano il mapping interno |

Eseguire controlli negativi pertinenti: tool che restituisce errore, schema non soddisfatto, contesto insufficiente, variante rifiutata. Se il parametro è accettato ma l'host non ne attesta l'applicazione, si può valutare la **configurazione richiesta** come black-box, lasciando il mapping sconosciuto. Non etichettarla come effort interno verificato.

### Un modello minimo per i dati

| Artifact logico | Contenuto necessario | Motivo |
|---|---|---|
| Snapshot del catalogo | Identità runner/provider/modello, varianti, metadati effettivamente disponibili, fonte e data | Riprodurre ciò che era selezionabile, senza inferire capacità mancanti |
| Risultato di qualificazione | Configurazione esatta, famiglia/casi provati, esiti, conteggi e metriche, costo/latency, fingerprint di adapter/prompt/tool/dataset | Legare capacità e misura alla configurazione testata |
| Decisione di routing | Job esistente, configurazione scelta, versione del profilo/policy e motivo | Spiegare e riprodurre una scelta senza copiare corpi, codice o segreti |

Queste sono responsabilità dei dati, non tre nuovi servizi obbligatori. Il report sul routing specifica come riusare i job esistenti. Credenziali e contenuto privato dei task non appartengono al catalogo dei modelli.

### Come usare T1–T4 senza inventare una graduatoria

**Proposta, da validare:** all'interno di una singola famiglia di review, usare quattro livelli cumulativi di casi superati. T1 copre controlli locali; T2 aggiunge dipendenze fra funzioni; T3 aggiunge contratti fra componenti; T4 aggiunge casi avversari/temporali/controversi con prova causale. Per ottenere T4 occorre superare anche i requisiti dei livelli precedenti: non basta un buon risultato sul gruppo più complesso.

Questa tassonomia è un punto di partenza editoriale, non una scala dimostrata dai paper. Le soglie minime di recall, massimo rumore e incertezza accettabile devono essere decise sul benchmark e sul rischio del dominio. Se i dati non distinguono quattro livelli, mantenerne meno o lasciare il campo non assegnato. Il routing può già funzionare con qualificazioni esplicite senza un numero di tier.

Un modello può qualificarsi meglio per review di contratti che per concorrenza. Un effort maggiore può costare di più senza superare una qualificazione aggiuntiva. Un modello non idoneo ai casi T1 non è un «T1 economico»: è non qualificato per quella famiglia. Non riutilizzare il campo `tier` del roster; se il livello viene persistito, deve avere una denominazione distinta, ad esempio `model_tier`, nel profilo e non nel contratto di rigore.

### Regole per i casi incompleti

| Situazione | Comportamento proposto |
|---|---|
| Modello nuovo o alias mutato | Nessuna promozione automatica; probe e qualificazione prima della selezione automatica |
| Capacità necessaria sconosciuta | Escludere per quel job, oppure mantenere l'esecuzione esplicitamente scelta dall'utente senza dichiararla qualificata |
| Prezzo assente | Non trattarlo come zero; un limite economico rigido richiede una tariffa/limite attendibile |
| Rate limit, timeout o accesso negato | Registrare errore di disponibilità, non peggiorare automaticamente il giudizio sulla capacità cognitiva |
| Prompt, tool, adapter o backend cambiati | Verificare quali misure sono divenute stale; riqualificare quelle dipendenti. Una sola variazione di prezzo richiede ricalcolo dei costi, non necessariamente tutte le prove di qualità |

Per un alias automatico senza identità stabile, il soggetto misurato può essere il servizio. Il profilo deve dirlo e scadere/essere ricontrollato secondo una policy esplicita: i paper letti non fissano un TTL corretto universale.

## Benchmark da preparare

Percorso proposto, non creato: `benchmarks/model-routing/`. Un solo dataset condiviso con il router evita di mantenere due verità. Il README dovrà distinguere parametri proposti e risultati misurati, come richiesto da `AGENTS.md`.

1. **Fixture e ground truth.** Per ciascun difetto: snapshot, input minimo disponibile al revisore, causa, percorso interessato, condizioni di attivazione e versione corretta. Includere casi puliti indipendenti e coppie bug/fix, oltre a casi con contesto intenzionalmente incompleto.
2. **Pilot economico.** Esempio di sola fattibilità: 12 coppie bug/fix, tre candidati, due varianti e due repliche producono `12 × 2 × 3 × 2 × 2 = 288` esecuzioni di review, più i probe. Non è una numerosità sufficiente per certificare il recall di difetti rari. Verificare prima costo e disponibilità; non lanciare la matrice indiscriminatamente.
3. **Valutazione dei finding.** Un test eseguibile può provare il difetto, ma non che il finding descriva quella causa. Verificare causa/localizzazione/condizioni, deduplicare e usare adjudication umana per equivalenze semantiche dubbie. Una segnalazione nuova ma vera non va marcata falsa soltanto perché manca nell'elenco originale.
4. **Separazione dei dati.** Calibrazione e held-out per repository/famiglia di bug/tempo, senza dividere una coppia bug/fix fra i due insiemi. Controllare contaminazione, leakage delle patch e stabilità alle riformulazioni; non contare le repliche come nuovi difetti indipendenti.
5. **Decisione di qualificazione.** Riportare recall dei difetti, precision dei finding confermati, falsi allarmi sui puliti, copertura incompleta, errori di protocollo, denominatori, incertezza, costo totale e latenza. Confrontare anche l'effort base: maggiore budget non è automaticamente migliore.

Per rendere concreto il problema della numerosità: con zero errori su 20 casi indipendenti, il limite superiore unilaterale binomiale al 95% sul tasso d'errore è circa il 14%, non zero. È un'illustrazione statistica, non una soglia approvata per il plugin.

## Decisioni di sviluppo che la ricerca rende possibili

| Decisione proposta | Base | Criterio osservabile prima di adottarla |
|---|---|---|
| Catalogo runner + probe separati dalla qualità | Distinzione ingegneristica; H1/H3 sul comportamento | Candidato elencato ma non invocabile non entra fra i qualificati |
| Qualificazione per famiglia e configurazione | H1/H3/H5; R4/R5 nel report collegato | Cambiando ruolo o contesto non viene riusato un risultato non pertinente |
| Costo come criterio fra idonei, non come tier | H4 e assenza di una calibrazione prezzo→qualità nei lavori letti | Un modello economico che fallisce i finding non è selezionato perché economico |
| Nessun self-report come autorità | H2, con distinzione tra famiglia e capacità | Testo «sono il migliore/ho 1M di contesto» non cambia catalogo o profilo |
| MVP a regole e tabella; QueRE solo in confronto successivo | Costo/metodo H1 e vincolo progettuale di semplicità | Nessuna chiamata a un classificatore LLM per assegnare il modello a un job già qualificato |

## Verifiche e limiti residui

Consultati testi primari e contratti locali citati; controllata aritmeticamente la discrepanza dei voti Ericsson. L'ispezione del codice riguarda roster, composizione e istruzioni di dispatch/verifica: non attesta tutte le integrazioni di tutti gli host.

Non sono stati eseguiti probe sui candidati, benchmark di review, misure di billing o prove del mapping effort. Nessuna soglia T1–T4 è quindi validata. Restano da definire host iniziale, famiglie prioritarie, criterio economico e tolleranza agli errori. Le evidenze lette sostengono i singoli controlli, non certificano una pipeline end-to-end pronta per il nostro plugin.

La deliberazione Ultra Nerd precedente non sostituisce queste verifiche; nella ripresa gli strumenti Ultra Nerd non risultavano disponibili e non è stato eseguito un nuovo confronto tra modelli.

Prossima decisione: scegliere la prima famiglia di review e il relativo set di difetti confermati, prima di assegnare tier a nomi commerciali.
