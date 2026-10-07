# Coerenza dei progetti sviluppati con agenti AI: test, documentazione e residui delle prove

Rapporto del 7 ottobre 2026. Ricerca avviata il 6 ottobre e ripresa il 7 ottobre. Domanda: quali evidenze descrivono test inutili, errati o obsoleti, informazioni contraddittorie e accumulo di artefatti, e quali pratiche permettono di consolidare la conoscenza prima di ripulire un progetto?

## Sintesi

Le osservazioni da cui nasce questa ricerca corrispondono a problemi documentati, ma di natura diversa. Esistono evidenze sperimentali di test generati che consolidano un bug; osservazioni di istruzioni obsolete o contraddittorie; studi sui costi della ridondanza e della fragilità delle suite; pratiche mature per rimuovere gli output pesanti conservando risultati e riproducibilità. Queste evidenze non autorizzano una percentuale generale di “progetti di vibe coding disordinati”. I campioni, i modelli e gli obiettivi studiati sono molto differenti. [1](https://arxiv.org/html/2607.22883v1) [2](https://arxiv.org/html/2606.09090) [3](https://mir.cs.illinois.edu/gyori/pubs/issta18.pdf) [4](https://docs.qameta.io/administer/maintenance/cleanup-policies/)

La distinzione più importante è fra tre oggetti: una verifica eseguibile che protegge il comportamento futuro, il risultato di una prova conclusa e i file prodotti dalla sua esecuzione. Un test mantenuto può essere utile anche dopo un refactor; un esperimento concluso può essere trasformato in un record compatto; log, video e copie rigenerabili possono avere un ciclo di vita più breve. Le fonti supportano queste distinzioni, mentre il workflow che le combina è una proposta progettuale da validare. [5](https://yanmeng.github.io/papers/TOSEM231.pdf) [6](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1003285) [7](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1009823)

Il criterio di pulizia dovrebbe essere il valore informativo e di protezione di ciò che rimane. Numero di file, percentuale di copertura e dimensione su disco sono segnali utili, ma da soli non stabiliscono quali contenuti siano corretti, quali test siano ridondanti o quali dati si possano ricostruire. [8](https://philmcminn.com/publications/barr2015.pdf) [3](https://mir.cs.illinois.edu/gyori/pubs/issta18.pdf) [9](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1005097)

## 1. Test che confermano errori e test che fotografano il codice

### Il problema dell'aspettativa corretta

Un test ha bisogno di un oracolo: un criterio per stabilire il risultato desiderato. Ricavare l'aspettativa soltanto dall'implementazione corrente può trasformare il comportamento osservato in un obbligo, anche quando quel comportamento contiene un difetto. La letteratura sul problema dell'oracolo distingue esplicitamente osservazione e correttezza. [8](https://philmcminn.com/publications/barr2015.pdf)

Lo studio *Evaluating and Mitigating the Misguidance Effect* definisce come fuorviante un test che passa sulla versione difettosa e fallisce sulla sua correzione. Analizza 318 metodi Java relativi a 233 difetti reali di Defects4J. Per GPT-4.1, l'input difettoso produce 92 test fuorvianti e 86 capaci di esporre il difetto su 2.841 test generati; l'input corretto ne produce rispettivamente 11 e 236 su 2.905. Il contesto difettoso può quindi influenzare la verifica. Un test che passa sia sulla versione difettosa sia su quella corretta può verificare un comportamento valido senza esporre quel particolare bug. Limiti: benchmark Java a livello di metodo, correzione di riferimento come oracolo e possibile sovrapposizione con dati di addestramento. [1](https://arxiv.org/html/2607.22883v1)

Una seconda ricerca su 287 programmi Python difettosi, provenienti da quattro esercizi universitari, mostra un problema di selezione. CoverAgent conserva 171 suite che passano sul programma difettoso e falliscono sul riferimento corretto; CoverUp ne conserva 62 delle 91 finali, mentre 196 input non producono una suite. Le pipeline scartano anche candidati che rivelano il bug perché falliscono sull'implementazione da testare. Sono conteggi di suite e di candidati in strumenti e versioni specifici, non percentuali dei singoli test AI o di progetti professionali. [10](https://arxiv.org/html/2412.14137v1)

**Implicazione progettuale:** distinguere la generazione di protezione per un comportamento già accettato dalla ricerca di difetti nel comportamento corrente. Il filtro “mantieni soltanto i test verdi” può essere sensato per il primo obiettivo e controproducente per il secondo. Una verifica fallita richiede di valutare tanto il prodotto quanto l'aspettativa del test. Questa è una sintesi delle due ricerche.

### Mock, tautologie e dettagli interni

Il libro *Software Engineering at Google* documenta problemi anteriori all'AI: un'asserzione sulle chiamate interne può confermare che una richiesta sia stata emessa senza verificare il suo effetto; uno stub può codificare un contratto sbagliato o superato; anche un fake richiede manutenzione e verifica rispetto all'implementazione reale. Le verifiche delle interazioni restano appropriate quando ordine, numero di chiamate o effetti sono parte del contratto. La presenza di mock, da sola, non dimostra che un test sia inutile. [11](https://abseil.io/resources/swe-book/html/ch13.html)

Per valutare un test autoreferenziale occorre chiedere quale proprietà indipendente controlli. Sono candidati alla revisione i test che riproducono la stessa logica della funzione, usano la funzione testata per calcolare l'aspettativa, controllano soltanto valori costruiti al loro interno o prescrivono dettagli accidentali. Sono criteri di analisi semantica, non una classificazione automatica dimostrata dalla sola forma del codice. [8](https://philmcminn.com/publications/barr2015.pdf) [11](https://abseil.io/resources/swe-book/html/ch13.html)

I rilevatori di *test smells* possono aiutare a trovare candidati. Lo studio TOSEM del 2026 compara suite LLM, strumenti tradizionali e test umani e mostra problemi di leggibilità e manutenzione anche nei test scritti da persone. Rilevatori differenti non concordano sempre. Un odore del codice non equivale a un oracolo errato e non costituisce, da solo, una ragione per eliminare la verifica. [12](https://arxiv.org/html/2410.10628v3)

## 2. Test obsoleti dopo modifiche, migrazioni e refactor

I test evolvono insieme al prodotto, ma cambiare il loro codice non significa necessariamente cambiare il comportamento protetto. Lo studio TOSEM sulla coevoluzione analizza 44 progetti e revisiona manualmente 380 coppie di modifiche: include migrazioni da JUnit a JUnit Jupiter, adattamenti delle dipendenze dei test, correzioni nei test stessi ed estrazione di casi comuni. Questi interventi possono essere manutenzione necessaria di verifiche ancora valide. [5](https://yanmeng.github.io/papers/TOSEM231.pdf)

Un refactor, nel senso di trasformazione che conserva il comportamento previsto, mantiene il valore dei test su quel comportamento. Una migrazione può cambiare API e strumenti lasciando intatti requisiti e garanzie. L'obsolescenza semantica dipende invece dalla dismissione del contratto protetto o da una sua sostituzione intenzionale. Questa distinzione deriva dalle fonti sulla manutenzione e sull'oracolo, non da una regola basata sull'età del file. [5](https://yanmeng.github.io/papers/TOSEM231.pdf) [8](https://philmcminn.com/publications/barr2015.pdf)

Una ricerca FSE 2021 sui test disabilitati esamina circa 122.000 commit e 3.111 cambiamenti di disabilitazione in 15 progetti Java. Nel periodo osservato, il 41% dei test disabilitati non viene riabilitato; l'analisi trova motivi quali incompatibilità di dipendenze, ridondanza e obsolescenza, oltre a test dimenticati dopo la correzione del problema associato. Il 41% non è una misura dei test obsoleti e il termine “mai” è limitato alla storia osservata. È una prova dell'esistenza di residui da rivedere, senza una decisione automatica sulla loro eliminazione. [13](https://petertsehsun.github.io/papers/fse2021_disabled_test.pdf)

Un preprint del 2026 valuta 22.374 attività di generazione su programmi Java/Python trasformati senza cambiarne la semantica. Le nuove suite generate degradano rispetto a una baseline appositamente selezionata per passare. L'esperimento include trasformazioni artificiali o avversarie. Non misura la sopravvivenza della stessa suite a un normale refactor e non dimostra che i vecchi test diventino inutili. È evidenza sulla sensibilità della rigenerazione alla forma del programma. [14](https://arxiv.org/html/2603.23443v1)

**Criterio proposto di dismissione:** associare ogni famiglia di test a requisito, confini degli input, proprietà verificata e regressioni storiche. Se il requisito rimane, adattare la verifica. Se è dismesso, registrare la decisione. Se la stessa protezione è garantita altrove, dimostrare l'equivalenza rilevante prima di rimuovere il duplicato.

### Ulteriori evidenze longitudinali e interventi concreti

Il lavoro FSE 2012 su sei programmi e 88 versioni studia 14.312 test e 17.427 cambiamenti. Solo 111 delle 1.121 riparazioni cambiano esclusivamente asserzioni. Un esempio adatta setup e chiamate API mantenendo il risultato atteso; un altro abbandona una vecchia aspettativa quando il supporto del prodotto cambia. Spostamenti e rinominazioni possono inoltre sembrare cancellazioni. La manutenzione del test e la dismissione del comportamento sono eventi distinti anche nella storia reale dei progetti. [15](https://web.archive.org/web/20240413135742if_/https://citeseerx.ist.psu.edu/document?repid=rep1&type=pdf&doi=efe8079160bb66d4df86b1531ec03c17b0ecd3e2)

DelTest, nel 2025, conferma cancellazioni di test in progetti Java ed esclude esplicitamente spostamenti e refactor. Nel sottoinsieme di sei progetti, classifica il 91,4% delle 7.326 cancellazioni come obsolescenza operativa per rimozione di metodi o mancata compilazione. È una definizione basata sul codice, senza dimostrare da sola la scomparsa del requisito. La categoria dei test cancellati che ancora passano include casi con perdita di copertura: il 20% dei 518 casi esaminati. Il campione estende progetti del precedente studio e i criteri cambiano; le percentuali non costituiscono una misura storica dell'aumento di test inutili. [16](https://hifromajay.github.io/papers/msr25.pdf)

ARUS trova e rimuove configurazioni di stub non utilizzate in suite Java. L'intervento mantiene i test eseguibili e porta a modifiche accettate dagli sviluppatori; non certifica la correttezza delle loro aspettative. È un precedente di pulizia del setup che conserva la verifica utile, distinto dall'eliminazione dell'intero test. [17](https://arxiv.org/html/2407.20924v1)

Due resoconti diretti illustrano il contesto necessario. Una richiesta del manutentore di OpenClaw collega la rimozione di vecchie compatibilità a una politica di aggiornamento e conserva import ancora supportati. Una segnalazione Vitest riguarda invece test rotti dopo una migrazione per ordine dei progetti e isolamento del runner. Sono testimonianze di casi specifici; l'implementazione dei relativi PR non è stata verificata in questa ricerca e non viene presentata come intervento riuscito. [18](https://github.com/openclaw/openclaw/issues/104648) [19](https://github.com/vitest-dev/vitest/issues/8894)

## 3. Proliferazione delle suite e costo di manutenzione

### Evidenze di duplicazione

Nella sperimentazione industriale di TestGen-LLM, gli ingegneri di Meta trovano un gruppo di quattro test solo superficialmente diversi e introducono una misura del contributo del singolo caso per evitare sforzo duplicato. Rifiutano inoltre una proposta che aumentava la copertura eseguendo un metodo ma non conteneva asserzioni. Sono esempi osservati; non stimano la frequenza generale dei test inutili generati dagli agenti. [20](https://arxiv.org/html/2402.09171v1)

Un piccolo studio su sei modelli e un componente Python osserva più test e scenari duplicati con prompting articolato. I conteggi medi della Tabella IV sono 36 contro 59, 43 contro 64 e 45 contro 62 nei tre livelli di contesto. Alcune suite sono anche efficaci nell'individuare modifiche errate. I risultati mostrano che quantità, unicità degli scenari ed efficacia sono dimensioni distinte; non descrivono una crescita longitudinale di repository professionali. [21](https://arxiv.org/html/2507.14256v1)

### Copertura conservata non significa protezione equivalente

Lo studio ISSTA 2018 valuta suite ridotte rispetto a 1.478 build fallite di 32 progetti Java/Maven. In una configurazione pessimistica, la perdita di rilevazione delle build raggiunge il 52,2%. La misura richiede di conservare la rilevazione di tutti i difetti inferiti dalle verifiche fallite; non significa che il 52,2% di tutti i bug o progetti sia sfuggito ai test. Il risultato rilevante è che metriche di copertura e mutazione predicono debolmente questa perdita futura. [3](https://mir.cs.illinois.edu/gyori/pubs/issta18.pdf)

Uno studio ISSRE 2011 su 19 versioni di quattro progetti trova invece riduzioni utili senza perdita grave nel proprio contesto; tecniche, granularità e criteri modificano il compromesso. Le due ricerche non stabiliscono una soglia universale: misurano sistemi e obiettivi differenti. [22](https://mir.cs.illinois.edu/marinov/publications/ZhangETAL11JUnitReduction.pdf)

Due casi che eseguono le stesse righe possono verificare input, risultati ed effetti diversi. Accorpare il codice comune può migliorare la manutenzione senza eliminare gli scenari; rimuovere casi soltanto perché non aggiungono righe coperte può perdere protezione. Questa è una conseguenza progettuale dei risultati, da verificare sul progetto concreto.

### Tre operazioni diverse

| Operazione | Oggetto | Domanda da risolvere |
|---|---|---|
| Rimozione permanente | Test mantenuto | Quale protezione viene persa o sostituita? |
| Selezione per una modifica | Esecuzione di una parte della suite | Quali verifiche sono pertinenti a questo cambiamento? |
| Pulizia degli artefatti | Log, video, dati temporanei | Quali evidenze e informazioni di riproducibilità devono restare? |

Il sistema di selezione predittiva descritto da Facebook esegue circa un terzo dei test dipendenti dai cambiamenti e intercetta oltre il 99,9% dei cambiamenti problematici. L'obiettivo è trovare almeno una verifica fallita per cambiamento, che è diverso dal conservare la rilevazione di ogni difetto. I test non selezionati continuano a esistere: questa è ottimizzazione dell'esecuzione, non prova della loro inutilità. [23](https://engineering.fb.com/2018/11/21/developer-tools/predictive-test-selection/)

Anche la flakiness ha un costo. Google riporta, nel suo contesto del 2016, circa l'1,5% di esecuzioni instabili, quasi il 16% di test con qualche instabilità e circa l'84% di transizioni da pass a fail collegate a flakiness. Sono tre denominatori diversi. L'instabilità può dipendere anche dal prodotto o dall'infrastruttura, quindi richiede diagnosi prima di decidere come trattare la verifica. [24](https://testing.googleblog.com/2016/05/flaky-tests-at-google-and-how-we.html)

## 4. Documentazione frammentata e istruzioni contraddittorie

### Riscontri diretti e limiti dei campioni

Lo studio qualitativo *Vibe Coding in Product Teams* raccoglie interviste a 22 persone e documenta copie in documenti temporanei, strumenti AI che annullano o interpretano male il lavoro di altri strumenti, crescita disordinata e difficoltà a ricostruire modifiche e decisioni. Solo quattro partecipanti sono ingegneri software; molti lavorano alla prototipazione. È una fonte diretta delle esperienze descritte, non un censimento dei repository di vibe coding. [25](https://arxiv.org/html/2509.10652v3)

*Context Rot* analizza 612 file di istruzioni in 356 repository. Segnala riferimenti potenzialmente obsoleti in 82 repository. La verifica manuale di 50 segnalazioni ne trova 32 corrette, 12 false e sei ambigue. Il paper tratta il 23% dei repository segnalati come un segnale di fattibilità, non come prevalenza precisa. Documenta script rimossi, funzioni rinominate e percorsi inesistenti, ma non misura il danno causato agli agenti. [2](https://arxiv.org/html/2606.09090)

*Configuration Smells in AGENTS.md* analizza i file root di 100 applicazioni selezionate per popolarità. Il rilevatore segnala 28 file con contraddizioni; la revisione ne conferma 16. Il numero grezzo di segnalazioni non va presentato come numero di casi accertati. Soglie quali almeno 200 righe o un solo commit sono proxy di rischio, non prove di un difetto. [26](https://arxiv.org/html/2606.15828v5)

Lo studio su 2.853 repository e il lavoro longitudinale *Agent READMEs* mostrano diffusione di più configurazioni e manutenzione spesso orientata ad aggiunte. Conteggi e crescita dei file descrivono una pratica, senza dimostrare da soli incoerenza o danno. Un nucleo condiviso e riferimenti espliciti sono proposte ragionevoli; la loro efficacia richiede una valutazione del contenuto e dell'uso. [27](https://arxiv.org/html/2602.14690v5) [28](https://arxiv.org/html/2511.12884v2)

### AGENTS.md e CLAUDE.md: conta cosa aggiungono

La versione settembre 2026 di *Evaluating AGENTS.md* non trova un miglioramento generale significativo nel successo dei compiti e misura maggiori costi. I file scritti dagli sviluppatori hanno un piccolo vantaggio non significativo rispetto all'assenza; in una condizione distinta, rimuovendo altra documentazione dopo aver generato il contesto e omettendo Claude per ragioni di costo, si osserva invece un guadagno medio di 2,7 punti percentuali. Il lavoro non trova una relazione chiara fra lunghezza e risultato: anche gli obblighi aggiunti e rispettati dagli agenti contribuiscono al costo. [29](https://arxiv.org/html/2602.11988v3)

Altre ricerche pongono domande diverse. Una piccola ablation non trova un effetto significativo sulla correttezza, con potenza statistica limitata. Lo studio sull'efficienza di 124 piccoli PR osserva meno tempo e token di output, ma non valuta completamente la correttezza. Il test Vercel riguarda conoscenze di una versione specifica di Next.js e riporta miglioramenti, senza pubblicare tutti i denominatori necessari a una generalizzazione indipendente. Questi risultati non dimostrano che i file siano sempre utili o sempre inutili. [30](https://arxiv.org/html/2607.27250) [31](https://arxiv.org/html/2601.20404v2) [32](https://vercel.com/blog/agents-md-outperforms-skills-in-our-agent-evals)

**Implicazione progettuale:** rendere autorevoli istruzioni che aggiungano conoscenze necessarie, comandi verificati e vincoli durevoli. Distinguere queste informazioni da esiti di sessione, esperimenti e decisioni superate; le modalità di separazione sono una proposta di organizzazione, non una soglia universale di lunghezza.

## 5. Preservare comprensione e ragioni delle decisioni

Conoscere il comportamento corrente e sapere perché quel comportamento è stato scelto sono attività diverse. Il modello di *intent debt* distingue codice, comprensione condivisa e perdita di obiettivi, vincoli e rationale. È un'argomentazione concettuale: aiuta a formulare la domanda, senza misurare una diffusione generale del problema. [33](https://arxiv.org/pdf/2603.22106v4)

Uno studio su 621 diari riflessivi di 207 studenti descrive accettazione di codice poco compreso, dipendenza dalle spiegazioni dell'AI e controlli omessi. Rileva anche usi positivi dell'AI come supporto alla comprensione. Non dispone di un gruppo di controllo e non stima un effetto causale nei team professionali. [34](https://arxiv.org/html/2604.13277)

Il resoconto generato dall'agente non costituisce automaticamente la verifica del lavoro. Lo studio MSR sulle incoerenze fra messaggi e codice nei PR trova casi di modifiche dichiarate ma non implementate. La rilevazione è euristica e l'associazione con gli esiti dei PR è osservazionale. Per il consolidamento, una conclusione importante deve essere collegata a evidenze leggibili e pertinenti. [35](https://arxiv.org/html/2601.04886v2)

La tesi di un deterioramento inevitabile sarebbe eccessiva. *Echoes of AI*, studio preregistrato su sviluppo ed evoluzione di una piccola applicazione Java, non trova differenze sistematiche significative nella manutenzione successiva. Coinvolge soprattutto professionisti e un uso dell'AI affiancato alla persona, non progetti autonomi di lunga durata. È una controevidenza necessaria, con un perimetro limitato. [36](https://arxiv.org/html/2507.00788v3)

## 6. Ridurre i dati delle prove conservando i risultati

### Un report compatto può essere utile, ma deve avere provenienza

Anthropic descrive compaction e registri di avanzamento per mantenere continuità fra sessioni: conservare decisioni, problemi irrisolti e dettagli necessari, riducendo output ripetitivi. Avverte che una compressione troppo aggressiva perde informazioni utili. Il resoconto riguarda il contesto conversazionale e il funzionamento dei propri harness; estenderlo alla pulizia del disco è una scelta progettuale. [37](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) [38](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)

Le linee guida PLOS richiedono input, parametri, versioni del software, script, semi casuali quando pertinenti e collegamenti fra risultati e affermazioni. Suggeriscono anche di conservare intermedi che possono aiutare a capire errori. La guida sui notebook propone di ripulire e annotare esplorazioni significative, poi rieseguire da uno stato pulito per accertare che il percorso conservato sia sufficiente. La conservazione selettiva deve quindi mantenere una possibilità concreta di controllo, non soltanto un racconto. [6](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1003285) [39](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1007007)

### Esempi implementati di ciclo di vita degli artefatti

Allure TestOps elimina allegati, dati delle fixture e scenari, conservando i metadati delle esecuzioni e dei risultati. Le regole distinguono stato e tipi di file e operano sulle esecuzioni chiuse. Questo dimostra la separazione tecnica fra esito durevole e materiale voluminoso. Non dimostra che i metadati rimasti siano sufficienti a ripetere ogni esperimento. [4](https://docs.qameta.io/administer/maintenance/cleanup-policies/)

Playwright permette di conservare video, trace e screenshot in funzione del fallimento; pytest gestisce directory temporanee dedicate e politiche di conservazione. La guida PLOS per strumenti integrabili nei workflow raccomanda di gestire grandi output e molti piccoli file, ripulire i temporanei dopo il successo e offrire conservazione per il debug. Sono pratiche per prevenire l'accumulo, senza interpretare da sole il significato delle prove. [40](https://playwright.dev/docs/test-use-options) [41](https://docs.pytest.org/en/stable/how-to/tmp_path.html) [7](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1009823)

La guida sullo storage rende esplicito il compromesso fra archiviare e rigenerare. Una copia derivata può essere rigenerabile solo se restano input, versioni e procedura; dati irriproducibili possono avere un valore superiore al loro costo di spazio. Dimensione e anzianità del file sono quindi elementi di una decisione, non il criterio completo. [9](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1005097)

### Record minimo proposto per una prova consolidata

La seguente struttura è una sintesi delle pratiche lette, da adattare e validare:

| Campo | Scopo |
|---|---|
| Scopo e ipotesi | Conservare cosa si voleva verificare |
| Revisione del codice e ambiente | Identificare ciò che è stato realmente eseguito |
| Input e provenienza | Conservare dati necessari o il modo per ricostruirli |
| Comando, parametri e seed | Rendere ripetibile la procedura quando possibile |
| Esito e misure | Distinguere successo, fallimento, risultato parziale e inconcludente |
| Evidenze essenziali | Sostenere le conclusioni con estratti, risultati o immagini pertinenti |
| Interpretazione e limiti | Separare il risultato osservato dalla spiegazione proposta |
| Decisione e stato | Registrare ciò che è stato adottato, superato o lasciato aperto |
| Riproducibilità verificata | Dichiarare se il percorso conservato è stato rieseguito |
| Disposizione dei file | Elencare cosa resta, cosa è rigenerabile e cosa viene rimosso |

Un esito non ricostruibile deve restare esplicitamente sconosciuto. Una spiegazione plausibile generata a posteriori non va presentata come decisione storica recuperata. Quest'ultima regola deriva dalla distinzione fra evidenza e interpretazione; non è una capacità che il report può garantire automaticamente.

## 7. Precedenti per una pulizia che conservi conoscenza

### Rilevare e correggere discrepanze reali

DOCER, nella documentazione tradizionale, porta segnalazioni a manutentori di 15 progetti: cinque delle 19 istanze riportate vengono corrette; quattro progetti rispondono positivamente, quattro segnalano falsi positivi e sette non rispondono. Il risultato dimostra un intervento con correzioni osservate, senza un confronto controllato su produttività o comprensione. [42](https://arxiv.org/html/2212.01479)

DocChecker misura rilevazione di incoerenze nei commenti e generazione di commenti su benchmark. ArDoCo collega descrizioni architetturali e modelli formali e identifica elementi mancanti o non documentati. Sono precedenti di controllo della coerenza; correggere commenti o discrepanze rilevate non equivale a recuperare la ragione storica di una decisione. Le prestazioni su campioni e difetti simulati richiedono validazione prima di trasferirle a istruzioni per agenti. [43](https://arxiv.org/html/2306.06347v3) [44](https://publikationen.bibliothek.kit.edu/1000158208/150680132)

### Recuperare una decisione e proporre una spiegazione sono cose diverse

Uno studio su cinque modelli e 100 problemi architetturali valuta rationale generati rispetto a quelli umani e alla loro utilità. Molte ragioni non coincidenti vengono giudicate utili: la precisione di sovrapposizione non è un tasso di allucinazione. Il punto pertinente al consolidamento è che l'esperimento genera nuove ragioni, senza dimostrare il recupero fedele dell'intenzione storica. Occorre etichettare una spiegazione ricostruita come inferenza, conservando i riferimenti alla decisione originale quando esistono. [45](https://arxiv.org/html/2504.20781v3)

La guida Microsoft sugli ADR propone di registrare contesto, alternative, compromessi, grado di confidenza e stato della decisione, compresa la sua sostituzione. È una pratica di documentazione, non una prova sperimentale della bontà di un particolare template. Per il workflow proposto, è utile conservare una decisione superata come storia riconoscibile, impedendo che venga letta come istruzione ancora vigente. [46](https://learn.microsoft.com/en-us/azure/well-architected/architect-role/architecture-decision-record)

### Provenienza eseguibile e verificabile

W3C PROV modella entità, attività e responsabili: quali input sono stati usati, quale elaborazione è avvenuta e quali output sono stati prodotti. Aiuta a rappresentare la catena conclusione → misura → esecuzione → input. La conformità del modello non certifica che le sue affermazioni siano vere. [47](https://www.w3.org/TR/prov-primer/)

Workflow Run RO-Crate implementa registri di esecuzione in più sistemi e documenta la riesecuzione di un workflow di patologia digitale. L'articolo dichiara che la riesecuzione generale non è garantita: mappatura degli input e ambiente contano, e i dati possono essere soltanto collegati da URI. ReproZip mostra invece come catturare comandi, ambiente e dipendenze, permettendo esclusioni curate di temporanei o file reperibili altrove; anche qui esclusione e compatibilità devono essere verificate. [48](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0309210) [49](https://www.usenix.org/system/files/conference/tapp13/tapp13-final16.pdf)

Sumatra registra motivo, risultato, dati, versioni di codice ed eseguibile, argomenti e dipendenze. Per i dati può conservare percorsi e checksum, con archiviazione opzionale. Un checksum identifica o verifica un file disponibile, senza ricostruire un file cancellato. La guida raccomanda directory distinte per esecuzioni contemporanee, perché condividere la stessa destinazione rende ambigua l'attribuzione dei risultati. [50](https://sumatra.readthedocs.io/en/latest/web_interface.html) [51](https://sumatra.readthedocs.io/en/latest/handling_data.html)

La policy ACM distingue artefatti disponibili, artefatti valutati e risultati riprodotti. Per quest'ultimo stato richiede che un'altra squadra ottenga i risultati principali con gli artefatti degli autori, entro tolleranze accettabili. Un report dovrebbe quindi dichiarare che cosa è stato soltanto raccolto, che cosa è stato ispezionato e che cosa è stato rieseguito. Un risultato negativo o inconcludente mantiene valore informativo e può essere conservato in un registro compatto. [52](https://www.acm.org/publications/policies/artifact-review-and-badging-current) [53](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1004385)

### Un precedente operativo vicino alla richiesta

La guida NVIDIA NeMo-RL Brev conserva nel repository ipotesi e registri sintetici di riproducibilità; separa log, checkpoint e dump pesanti in directory effimere per campagna e distingue le cache riutilizzabili. La chiusura riporta metriche e percorsi nel registro e limita la pulizia ai file della campagna interessata. È un'istruzione operativa pubblicata e versionata, vicina alla richiesta dell'utente, senza una misura dell'efficacia generale del processo. [54](https://raw.githubusercontent.com/NVIDIA/skills/63c02e122e/skills/nemo-rl-brev-etiquette/SKILL.md)

Uno studio sul prototipo YoloFS documenta incidenti pubblici e valuta effetti sul filesystem trattenuti in uno stato revisionabile. Il corpus selezionato non stima una probabilità di incidente; il prototipo Linux viene provato su 11 piccoli compiti artificiali e non è una soluzione di pulizia pronta per ogni ambiente. È un precedente per osservare e verificare gli effetti dei file prima di renderli definitivi, pertinente soprattutto alle operazioni di rimozione. [55](https://arxiv.org/html/2604.13536v1)

### Risparmi misurati attraverso deduplicazione

Sciunits conserva versioni ricostruibili con deduplicazione: quattro versioni del workflow Food Inspection Evaluation passano da 907 MB a 333 MB; quattro versioni del Variable Infiltration Capacity da 7 GB a 3 GB. Sono due workflow scientifici, con costi di esecuzione dipendenti dal carico, non una misura dei residui tipici lasciati dagli agenti. La riduzione della vista di provenienza mantiene dettaglio espandibile: una sintesi dell'interfaccia non coincide con la cancellazione dei dati sottostanti. [56](https://cdmdicewebprd01.dpu.depaul.edu/pdfs/pubs/C23.pdf)

Per recuperare spazio esistono quindi almeno tre strategie da distinguere: eliminare materiale senza valore residuo, rigenerare output a partire da input e procedura conservati, deduplicare ciò che deve essere mantenuto. La scelta dipende dal contenuto e dal costo di ricostruzione.

## 8. Verifica della fedeltà e contraddizioni nelle fonti

Un report generato richiede confronto con i risultati conservati. Lo stress test DELEGATE-52 studia trasformazioni ripetute e ricostruzione semantica in molti domini testuali. Il chiarimento degli autori precisa che è un test diagnostico con harness semplificato, non una misura della riuscita complessiva del lavoro. Le percentuali del test non possono essere applicate a un singolo riassunto di esperimento. La lezione trasferibile è valutare proprietà del dominio, cifre, stati e riferimenti, invece di affidarsi soltanto alla somiglianza testuale o al giudizio di un altro modello. [57](https://arxiv.org/html/2604.15597v1) [58](https://www.microsoft.com/en-us/research/blog/further-notes-on-our-recent-research-on-ai-delegation-and-long-horizon-reliability/)

| Risultati apparentemente incompatibili | Distinzione necessaria |
|---|---|
| AGENTS.md non migliora generalmente il successo / AGENTS.md migliora un benchmark del produttore | Trattamenti e conoscenze aggiunte differenti; successo, costo e conoscenza di una versione sono misure distinte |
| Ridurre la suite conserva copertura / ridurre la suite perde rilevazione di fallimenti | Copertura eseguita e proprietà controllate non coincidono; criteri e sistemi cambiano |
| Test verde / test che aggiunge protezione | L'oracolo può essere errato, l'asserzione può mancare, il caso può non contribuire |
| Rilevatore segnala contraddizioni / revisione conferma meno casi | Segnalazioni sono candidati; servono precisione e denominatori della validazione |
| Conservare intermedi / ripulire temporanei dopo il successo | Valore probatorio e riproducibilità differiscono fra output |
| Rationale generato utile / rationale storico recuperato | Utilità di una spiegazione e provenienza della decisione sono proprietà diverse |

La tabella sintetizza i confronti discussi sopra e non introduce una nuova misura sperimentale.

### Due precisazioni rispetto alla ricerca preliminare in chat

1. **Meta:** la sezione dettagliata di TestGen-LLM usa 86 classi/componenti come denominatore: almeno un nuovo caso compilabile, affidabile o con copertura aggiuntiva. Le percentuali 75/57/25 non descrivono tutti i singoli test. L'abstract e alcune etichette del paper usano un linguaggio meno preciso; questo rapporto adotta il denominatore dei metodi. [20](https://arxiv.org/html/2402.09171v1)
2. **Prompting e quantità:** il testo di Walczak et al. parla di circa 20–40% di test in più; i conteggi medi della sua tabella mostrano aumenti diversi fra condizioni. Questo rapporto usa i conteggi e il risultato qualitativo di maggiore ridondanza, evitando una percentuale generalizzata. [21](https://arxiv.org/html/2507.14256v1)

## 9. Workflow di consolidamento proposto

Il seguente processo è una proposta derivata dalla ricerca. Le sue parti hanno precedenti; la loro combinazione non è stata validata come intervento completo su progetti di vibe coding.

1. **Inventario con provenienza.** Identificare documenti, istruzioni, test, script esplorativi, esecuzioni e output. Collegarli a revisioni, requisiti, decisioni e campagne quando le evidenze lo permettono. Un nome quale “temp” è un indizio, senza determinare da solo la destinazione del file.
2. **Confronto semantico.** Verificare se istruzioni e aspettative descrivono il contratto attuale; distinguere comportamento implementato, comportamento desiderato e ipotesi. Portare in evidenza contraddizioni e assenza di informazioni.
3. **Riesame delle verifiche.** Conservare regressioni e casi significativi; correggere oracoli errati; aggiornare scaffolding e framework; accorpare duplicazioni mantenendo scenari distinti. L'obsolescenza va motivata dal requisito dismesso o dalla protezione equivalente disponibile.
4. **Consolidamento delle prove.** Registrare scopo, condizioni, risultati, errori, limiti e decisioni. Conservare anche tentativi negativi quando spiegano scelte o escludono alternative. Collegare le conclusioni a evidenze minime e alla procedura ripetibile.
5. **Verifica del materiale conservato.** Controllare numeri e stati rispetto agli output; quando possibile rieseguire il percorso necessario da uno stato pulito. Dichiarare espressamente cosa è stato verificato e cosa rimane non riproducibile.
6. **Disposizione dei file.** Distinguere dati indispensabili, evidenze di problemi irrisolti, file rigenerabili, cache riutilizzabili e residui conclusi. Rendere revisionabile l'elenco delle rimozioni e verificarne gli effetti e l'ambito.
7. **Fonti correnti e storia leggibile.** Integrare le conclusioni durevoli nella sede che governa quel tipo di informazione. Registrare sostituzioni e incertezze; mantenere gli esiti di sessione separati dalle istruzioni durevoli.
8. **Prevenzione e misura.** Usare destinazioni esplicite per gli output, identificatori per le prove e politiche di conservazione. Confrontare spazio recuperato, coerenza delle informazioni, capacità di ripetere le prove e protezione delle regressioni.

### Come valutare il risultato

| Dimensione | Misura proposta | Limite da dichiarare |
|---|---|---|
| Coerenza delle istruzioni | Riferimenti validi e conflitti accertati prima/dopo | Precisione del rilevatore e casi ambigui |
| Recupero delle decisioni | Requisiti, ragioni e alternative ritrovabili con provenienza | Spiegazioni inferite separate dalle decisioni registrate |
| Qualità della suite | Regressioni storiche e difetti rilevanti ancora rilevati | Copertura e mutazione usate come segnali complementari |
| Costo della suite | Tempo e manutenzione sui cambiamenti rappresentativi | Selezione temporanea distinta dalla rimozione permanente |
| Fedeltà del report | Cifre e conclusioni confermate dalle evidenze | Nessuna auto-certificazione del riassunto |
| Riproducibilità | Prove rieseguite e risultati confrontati | Input irriproducibili o ambiente non disponibile |
| Spazio | Byte recuperati e dati ancora ricostruibili | File eliminati non equivalgono a valore preservato |
| Continuità | Nuova persona/agente ricostruisce stato e vincoli | Tempo, correttezza e incertezza valutati insieme |

Sono criteri di valutazione suggeriti; non sono soglie empiriche universali.

## 10. Confidenza e limiti della ricerca

**Confidenza alta nel fatto che i meccanismi esistano:** test generati che impongono il bug, aspettative legate ai dettagli interni, riferimenti obsoleti, contraddizioni accertate, crescita di materiale ripetitivo e separazione tecnica fra risultati e artefatti. “Alta” riguarda l'esistenza documentata, non quanto spesso si verifichino in qualsiasi progetto.

**Confidenza intermedia sul trasferimento delle pratiche:** i precedenti provengono da benchmark Java/Python, sistemi industriali specifici, progetti scientifici e documentazione tradizionale. I risultati con modelli storici non sono tassi delle versioni attuali. Testi, immagini e checkpoint hanno requisiti di conservazione differenti.

**Lacune non colmate in questa ricerca:** una prevalenza rappresentativa di progetti di vibe coding incoerenti; percentuali generali di test inutili o errati; MB/GB medi di residui dovuti agli agenti; un intervento completo e controllato che riconcili intenti, consolidi prove, riduca i file e dimostri beneficio durevole. Si tratta di risultati non trovati nel perimetro e nel budget, senza affermare che nessuno possa esistere.

Gli articoli con campioni selezionati o rilevazione euristica non vengono trattati come censimenti. I resoconti dei produttori sono precedenti operativi con un livello di prova diverso dagli studi controllati. I preprint sono distinti dalle pubblicazioni sottoposte a revisione. Dove è stato letto soltanto un abstract, questo limite resta nelle schede della ricerca e non sostiene dettagli di metodo.

## 11. Metodologia e tracciabilità

La ricerca è stata condotta in due passate, con sei incarichi distinti: tre di raccolta per validità dei test, memoria del progetto e suite/artefatti; tre di verifica e approfondimento per ciclo di vita dei test, interventi sulla documentazione e conservazione delle evidenze. La prima passata usa il limite del 6 ottobre 2026; la seconda estende il perimetro al 7 ottobre. Il perimetro era definito dai messaggi dell'utente: problemi simili a frammentazione, contraddizioni, prove residue e test inutili, errati o obsoleti.

Sono state dichiarate 105 query e 93 consultazioni sostantive di opere o pagine, compresi i riesami indipendenti. I sei elenchi contengono 93 voci e 80 URL primari distinti prendendo il primo URL di ciascuna voce. URL alternativi, metadati, tentativi falliti e ricerche di sezioni non gonfiano il conteggio. Lo stesso articolo riletto da due ricercatori resta una sola fonte bibliografica; pagine diverse sulla stessa ricerca non sono esperimenti indipendenti. Questa distinzione evita di chiamare “copertura” un semplice numero di file o letture.

Le fonti tecniche privilegiano studi primari, manoscritti degli autori, dati e resoconti diretti, documentazione ufficiale e specifiche. Un risultato di ricerca è stato usato come candidato, con affermazioni ricavate dalle pagine o sezioni effettivamente lette. Blocchi di accesso sono stati affrontati con copie degli autori, archivi dell'originale, browser o il fallback di lettura; un errore HTTP da solo non è stato considerato prova dell'assenza di una fonte. Gli abstract letti senza il testo integrale sono marcati nelle schede.

Le verifiche mirate hanno controllato denominatori, versioni, definizioni operative e outcome. Le percentuali sulle classi Meta, le tabelle sulla quantità dei test, i falsi positivi dei rilevatori e la differenza fra rigenerazione e sopravvivenza delle suite hanno richiesto precisazioni esplicite. Le contraddizioni non risolte sono rimaste limiti; raccomandazioni nuove sono etichettate come sintesi progettuale.

Il backend è la ricerca web nativa. La ricerca è stata interrotta fra il 6 e il 7 ottobre e poi ripresa; un tempo totale di calendario sarebbe poco informativo sul lavoro attivo. Le schede dei sei incarichi sono conservate nel file compagno, in ordine di assegnazione, con fonti, budget, limiti di accesso e filoni non risolti.

Controllo delle citazioni: completato sul rapporto. Le 58 fonti della bibliografia sono tutte richiamate nel testo; i collegamenti numerati corrispondono alla fonte riportata. Il controllo verifica la tracciabilità delle affermazioni e dei numeri nelle schede; non riproduce gli esperimenti originali.

## 12. Fonti impiegate nel rapporto

I titoli sono abbreviati o descrittivi dove indicato dalle schede. La data appartiene alla versione letta; la data di consultazione è usata soltanto per pagine vive senza una data editoriale stabile.

| N. | Fonte primaria | Data o versione | Tipo di evidenza |
|---|---|---|---|
| 1 | [Evaluating and Mitigating the Misguidance Effect of Buggy Code in LLM-Generated Unit Tests](https://arxiv.org/html/2607.22883v1) | 24 luglio 2026 | Studio accettato ISSTA/PACMSE, manoscritto degli autori |
| 2 | [Context Rot in AI-Assisted Software Development](https://arxiv.org/html/2606.09090) | 8 giugno 2026 | Preprint esplorativo |
| 3 | [Evaluating Test-Suite Reduction in Real Software Evolution](https://mir.cs.illinois.edu/gyori/pubs/issta18.pdf) | ISSTA 2018 | Studio empirico |
| 4 | [Allure TestOps: Cleanup policies](https://docs.qameta.io/administer/maintenance/cleanup-policies/) | Documentazione consultata il 6 ottobre 2026 | Documentazione ufficiale |
| 5 | [Revisiting the Identification of the Co-evolution of Production and Test Code](https://yanmeng.github.io/papers/TOSEM231.pdf) | settembre 2023 | Studio TOSEM |
| 6 | [Ten Simple Rules for Reproducible Computational Research](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1003285) | 24 ottobre 2013 | Linee guida PLOS |
| 7 | [Ten simple rules for making a software tool workflow-ready](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1009823) | 24 marzo 2022 | Linee guida PLOS |
| 8 | [The Oracle Problem in Software Testing: A Survey](https://philmcminn.com/publications/barr2015.pdf) | 2015 | Survey IEEE TSE |
| 9 | [Ten Simple Rules for Digital Data Storage](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1005097) | 20 ottobre 2016 | Linee guida PLOS |
| 10 | [Design choices made by LLM-based test generators prevent them from finding bugs](https://arxiv.org/html/2412.14137v1) | 18 dicembre 2024 | Preprint empirico |
| 11 | [Software Engineering at Google, capitolo 13](https://abseil.io/resources/swe-book/html/ch13.html) | 2020 | Libro tecnico degli autori |
| 12 | [On the Diffusion of Test Smells in LLM-Generated Unit Tests](https://arxiv.org/html/2410.10628v3) | 1 agosto 2026 | Studio TOSEM |
| 13 | [Studio sui test disabilitati](https://petertsehsun.github.io/papers/fse2021_disabled_test.pdf) | FSE 2021 | Studio empirico |
| 14 | [Evaluating LLM-Based Test Generation Under Software Evolution](https://arxiv.org/html/2603.23443v1) | 24 marzo 2026 | Preprint empirico |
| 15 | [Understanding Myths and Realities of Test-Suite Evolution](https://web.archive.org/web/20240413135742if_/https://citeseerx.ist.psu.edu/document?repid=rep1&type=pdf&doi=efe8079160bb66d4df86b1531ec03c17b0ecd3e2) | FSE, 11–16 novembre 2012 | Studio longitudinale, manoscritto originale archiviato |
| 16 | [Understanding Test Deletion in Java Applications](https://hifromajay.github.io/papers/msr25.pdf) | MSR, 28–29 aprile 2025 | Studio longitudinale |
| 17 | [Automatically Removing Unnecessary Stubbings from Test Suites](https://arxiv.org/html/2407.20924v1) | 30 luglio 2024 | Preprint e interventi accettati |
| 18 | [Remove pre-2026.4 compatibility shims and legacy migrations](https://github.com/openclaw/openclaw/issues/104648) | 11 luglio 2026 | Resoconto diretto di un manutentore |
| 19 | [Project order changed with v4](https://github.com/vitest-dev/vitest/issues/8894) | 31 ottobre 2025 | Segnalazione diretta di problema |
| 20 | [Automated Unit Test Improvement using Large Language Models at Meta](https://arxiv.org/html/2402.09171v1) | 14 febbraio 2024; FSE 2024 | Studio industriale |
| 21 | [Impact of Code Context and Prompting Strategies on Automated Unit Test Generation](https://arxiv.org/html/2507.14256v1) | 18 luglio 2025 | Preprint; versione JSS nel 2026 |
| 22 | [An Empirical Study of JUnit Test-Suite Reduction](https://mir.cs.illinois.edu/marinov/publications/ZhangETAL11JUnitReduction.pdf) | ISSRE 2011 | Studio empirico |
| 23 | [Predictive test selection](https://engineering.fb.com/2018/11/21/developer-tools/predictive-test-selection/) | 21 novembre 2018 | Resoconto tecnico Meta |
| 24 | [Flaky Tests at Google and How We Mitigate Them](https://testing.googleblog.com/2016/05/flaky-tests-at-google-and-how-we.html) | 27 maggio 2016 | Resoconto tecnico Google |
| 25 | [Vibe Coding in Product Teams](https://arxiv.org/html/2509.10652v3) | 1 maggio 2026 | Studio qualitativo HCI |
| 26 | [Configuration Smells in AGENTS.md](https://arxiv.org/html/2606.15828v5) | 30 luglio 2026 | Preprint empirico |
| 27 | [Harness Engineering for Agentic AI Coding Tools: An Exploratory Study](https://arxiv.org/html/2602.14690v5) | 30 giugno 2026 | Estensione di studio AIware |
| 28 | [Agent READMEs](https://arxiv.org/html/2511.12884v2) | 9 agosto 2026 | Preprint longitudinale |
| 29 | [Evaluating AGENTS.md: Are Repository-Level Context Files Helpful for Coding Agents?](https://arxiv.org/html/2602.11988v3) | 29 settembre 2026 | Studio sperimentale, preprint aggiornato |
| 30 | [Do Context Files Help Coding Agents?](https://arxiv.org/html/2607.27250) | 28 luglio 2026 | Preprint sperimentale |
| 31 | [On the Impact of AGENTS.md Files on the Efficiency of AI Coding Agents](https://arxiv.org/html/2601.20404v2) | 30 marzo 2026 | Studio JAWs |
| 32 | [AGENTS.md outperforms skills in our agent evals](https://vercel.com/blog/agents-md-outperforms-skills-in-our-agent-evals) | 27 gennaio 2026 | Esperimento del produttore |
| 33 | [From Technical Debt to Cognitive and Intent Debt](https://arxiv.org/pdf/2603.22106v4) | 6 aprile 2026 | Argomentazione concettuale |
| 34 | [Comprehension Debt in GenAI-Assisted Projects](https://arxiv.org/html/2604.13277) | 14 aprile 2026 | Preprint qualitativo |
| 35 | [Message-Code Inconsistency in AI Agent Pull Requests](https://arxiv.org/html/2601.04886v2) | 26 gennaio 2026 | Studio MSR |
| 36 | [Echoes of AI](https://arxiv.org/html/2507.00788v3) | 26 febbraio 2026 | Studio preregistrato |
| 37 | [Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) | 29 settembre 2025 | Resoconto tecnico Anthropic |
| 38 | [Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) | 26 novembre 2025 | Resoconto tecnico Anthropic |
| 39 | [Ten simple rules for writing and sharing computational analyses in Jupyter Notebooks](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1007007) | 25 luglio 2019 | Linee guida PLOS |
| 40 | [Playwright: Configuration (use)](https://playwright.dev/docs/test-use-options) | Documentazione consultata il 6 ottobre 2026 | Documentazione ufficiale |
| 41 | [pytest: Temporary directories and files](https://docs.pytest.org/en/stable/how-to/tmp_path.html) | Documentazione consultata il 6 ottobre 2026 | Documentazione ufficiale |
| 42 | [Detecting Outdated Code Element References in Software Documentation](https://arxiv.org/html/2212.01479) | 2 dicembre 2022; pubblicazione EMSE 2024 | Studio e intervento sul campo |
| 43 | [DocChecker](https://arxiv.org/html/2306.06347v3) | 3 febbraio 2024 | Studio su benchmark e strumento |
| 44 | [ArDoCo: Architecture Documentation Consistency](https://publikationen.bibliothek.kit.edu/1000158208/150680132) | ICSA 2023 | Studio di rilevazione delle incoerenze |
| 45 | [Using LLMs in Generating Design Rationale](https://arxiv.org/html/2504.20781v3) | 9 dicembre 2025; pubblicazione TOSEM nel 2026 | Studio sperimentale |
| 46 | [Maintain an architecture decision record](https://learn.microsoft.com/en-us/azure/well-architected/architect-role/architecture-decision-record) | Documentazione consultata il 7 ottobre 2026 | Linee guida ufficiali Microsoft |
| 47 | [PROV Model Primer](https://www.w3.org/TR/prov-primer/) | 30 aprile 2013 | W3C Note sul modello di provenienza |
| 48 | [Recording provenance of workflow runs with RO-Crate](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0309210) | 10 settembre 2024 | Studio PLOS e implementazioni |
| 49 | [ReproZip: Using Provenance to Support Computational Reproducibility](https://www.usenix.org/system/files/conference/tapp13/tapp13-final16.pdf) | TaPP 2013 | Studio di sistema |
| 50 | [Sumatra: Using the web interface](https://sumatra.readthedocs.io/en/latest/web_interface.html) | Documentazione consultata il 7 ottobre 2026 | Documentazione ufficiale |
| 51 | [Sumatra: Input and output data](https://sumatra.readthedocs.io/en/latest/handling_data.html) | Documentazione consultata il 7 ottobre 2026 | Documentazione ufficiale |
| 52 | [Artifact Review and Badging](https://www.acm.org/publications/policies/artifact-review-and-badging-current) | 24 agosto 2020, versione 1.1 | Policy ACM |
| 53 | [Ten Simple Rules for a Computational Biologist's Laboratory Notebook](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1004385) | 10 settembre 2015 | Linee guida editoriali PLOS |
| 54 | [NeMo-RL Brev Etiquette](https://raw.githubusercontent.com/NVIDIA/skills/63c02e122e/skills/nemo-rl-brev-etiquette/SKILL.md) | Commit 63c02e122e, 2 luglio 2026 | Istruzioni operative pubblicate da NVIDIA |
| 55 | [Don't Let AI Agents YOLO Your Files](https://arxiv.org/html/2604.13536v1) | 15 aprile 2026 | Preprint, casi e prototipo |
| 56 | [Sciunits: Reusable Research Objects](https://cdmdicewebprd01.dpu.depaul.edu/pdfs/pubs/C23.pdf) | IEEE eScience 2017 | Studio di sistema |
| 57 | [LLMs Corrupt Your Documents When You Delegate](https://arxiv.org/html/2604.15597v1) | 17 aprile 2026 | Preprint, stress test |
| 58 | [Further Notes on AI Delegation and Long-Horizon Reliability](https://www.microsoft.com/en-us/research/blog/further-notes-on-our-recent-research-on-ai-delegation-and-long-horizon-reliability/) | 15 maggio 2026 | Chiarimento metodologico degli autori |

