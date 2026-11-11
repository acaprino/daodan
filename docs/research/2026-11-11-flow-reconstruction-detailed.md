# Identificare e rappresentare automaticamente i flussi di un sistema software

## Rassegna scientifica ragionata su analisi statica, configurazione, interfacce, sistemi distribuiti, LLM e hardware

**Verifica delle fonti:** 11 novembre 2026.  
**Corpus:** 38 lavori, di cui 34 dal 2015 in poi e 4 antecedenti fondativi o direttamente pertinenti.  
**Natura del documento:** ricerca bibliografica mirata con verifica delle fonti, confronto delle evidenze e proposte metodologiche esplicitamente separate. Non è una revisione sistematica esaustiva.  
**Lingua:** italiano; titoli dei lavori, nomi dei benchmark e termini tecnici conservati quando utili alla ricerca.

Il documento considera un **flusso come un percorso ordinato attraverso componenti di un sistema**, eventualmente distribuiti fra interfaccia, servizi, dati persistenti e dispositivi. La domanda non è soltanto quali componenti siano collegati, ma **quale informazione o azione attraversi il collegamento, con quale significato, a quale granularità e sotto quali condizioni**.

Le tabelle contengono i risultati pubblicati e i relativi limiti. Le sezioni progettuali propongono come combinare le tecniche: non descrivono uno strumento già implementato né una capacità dimostrata unitariamente dai paper. Gli esempi applicativi sono inventati a scopo didattico e sono identificati come tali.

## Indice

1. [Risultato della ricerca e risposte alle cinque domande](#sintesi)
2. [Metodo, criteri di selezione e qualità dell'evidenza](#metodo)
3. [Tassonomia dei flussi e delle rappresentazioni](#tassonomia)
4. [Matrice bibliografica: tutti i 38 lavori](#matrice)
5. [Percorsi di lettura per i sei tipi di flusso](#percorsi-lettura)
6. [Collegare componenti senza chiamate dirette](#collegamenti-indiretti)
7. [Costruire unità coerenti di analisi e review](#unita-review)
8. [Individuare bug fra chi scrive e chi legge](#bug-writer-reader)
9. [Dall'interfaccia al codice e ai dati](#ui-codice-dati)
10. [Il contributo degli LLM](#contributo-llm)
11. [Contesto per la review: budget e fallimenti](#contesto-review)
12. [Proposta di rappresentazione comune e JSON di esempio](#rappresentazione-proposta)
13. [Come valutare ricostruzione e utilità](#valutazione-proposta)
14. [Lacune e programma sperimentale suggerito](#lacune-ricerca)
15. [Dataset, strumenti e condizioni di riuso](#artefatti)
16. [Fonti primarie e punti del testo da controllare](#fonti)
17. [Stringhe di ricerca per aggiornare la rassegna](#query)
18. [Glossario e convenzioni di lettura](#glossario)

<a id="sintesi"></a>

## 1. Risultato della ricerca e risposte alle cinque domande

**Conclusione della nostra sintesi:** il percorso più supportato da questo corpus è combinare analisi specializzate e conservare le prove che giustificano i raccordi. Il call graph è utile per le invocazioni; dipendenze, modelli dei framework, configurazioni, query e tracce servono a recuperare altre relazioni. I lavori verificati coprono porzioni significative del problema, ma nessuno dimostra da solo l'intera catena UI–servizio–database–dispositivo, insieme a tutti i significati funzionali richiesti. Questa conclusione riguarda il corpus selezionato, non prova l'assenza di altri contributi nella letteratura. [C1](#c1), [C3](#c3), [C4](#c4), [C5](#c5), [C7](#c7), [U5](#u5), [E1](#e1), [H4](#h4)

La distinzione principale riguarda l'**oggetto recuperato**. Un elenco di endpoint, una dipendenza fra colonne, una sequenza di callback, un diagramma BPMN e una spiegazione linguistica possono essere tutti utili, ma sostengono affermazioni diverse. Persino un cammino nel grafo può essere composto da segmenti incompatibili. Per questa ragione il documento distingue sempre struttura, dipendenza, fattibilità, osservazione e correttezza rispetto a una proprietà. [F1](#f1), [U1](#u1), [D3](#d3), [U8](#u8)

### 1.1 Risposte orientative

La tabella è una **sintesi interpretativa**, da leggere insieme alle schede e ai capitoli di approfondimento. Non contiene nuove misure sperimentali.

| Domanda | Risposta supportata e proposta di utilizzo | Lavori da cui iniziare | Limite decisivo |
|---|---|---|---|
| **1. Come ricostruire collegamenti indiretti?** | Comporre alias/points-to, binding del framework, valori di destinazione, contratti di comunicazione e dipendenze persistenti. Conservare configurazione e condizioni del raccordo. | [IC3](#c2), [Jasmine](#c4), [Micans](#c7), [Code2DFD](#c5), [CLOTHO](#d3). | Uguale nome di route, topic o tabella individua un candidato; non identifica automaticamente lo stesso valore, messaggio, record o istante. |
| **2. Come collegare schermo, codice e dati?** | Risalire da widget/binding al valore che lo alimenta; seguire dall'azione gli handler e gli effetti. Mantenere distinte le due direzioni. | [SUPOR](#u5), [FlowCog](#u6), [StoryDistiller](#u3), [GUITA](#f3). | La prova più diretta riguarda Android e Java/SWT; il trasferimento a frontend reattivi moderni resta da validare nel perimetro di questa ricerca. |
| **3. Come organizzare la review per grafo?** | Usare una proprietà, una feature o una modifica come criterio; selezionare cause ed effetti pertinenti e rendere visibili i confini. | [SDG](#f1), [CLUSTERCHANGES](#r1), [SmartCommit](#r2). | Concordanza del clustering e accettazione dei gruppi non equivalgono a indipendenza semantica o diminuzione dei bug sfuggiti. |
| **4. Che cosa aggiungono gli LLM?** | Semantica e descrizioni, ranking, espansione del contesto, query sul grafo e specifiche source–sink da sottoporre ad analisi. | [SLiCE](#d2), [RepoHyper](#l1), [CodexGraph](#l2), [RepoGraph](#l3), [IRIS](#l4). | Risolvere issue o completare codice non misura la completezza dei flussi. Una spiegazione plausibile non certifica un percorso. |
| **5. Quali bug emergono seguendo il flusso?** | Il percorso permette di mettere in relazione produzioni, consumi e condizioni; una proprietà stabilisce se il comportamento sia errato. | [CLOTHO](#d3), [BolaRay](#c6), [IRIS](#l4), [analisi FreeRTOS](#e3), [SecVerilog](#h1). | Granularità, unità, stato derivato e significato aziendale non sono specificati automaticamente dalla sola dipendenza. |

### 1.2 Come usare il documento

Per un orientamento rapido, leggere i sei percorsi consigliati nella [sezione 5](#percorsi-lettura). Per progettare un sistema di analisi, affiancare la [matrice dei raccordi](#collegamenti-indiretti) alla [rappresentazione proposta](#rappresentazione-proposta). Per valutare una tesi o un prototipo, partire dal [protocollo di valutazione](#valutazione-proposta), quindi scegliere gli artefatti compatibili con la proprietà e la granularità desiderate.

Ogni riferimento del tipo **C7** o **U5** porta a una riga della matrice. Le righe riportano autori, anno, sede, collegamento bibliografico, tecnica, piattaforma, rappresentazione, valutazione, numeri e limiti. Il riferimento **fonti** collega alle versioni consultate e alle sezioni o tabelle rilevanti. La disponibilità degli artefatti è trattata separatamente: verificare una pagina non equivale a eseguire e riprodurre l'esperimento.

<a id="metodo"></a>

## 2. Metodo, criteri di selezione e qualità dell'evidenza

### 2.1 Perimetro della selezione

La ricerca è stata organizzata per sei famiglie: dati; funzionalità; comunicazioni tecniche; controllo e stato; interfaccia e operatività; hardware ed embedded. Sono stati combinati i termini forniti nella richiesta con nomi di tecniche, piattaforme e rappresentazioni. La selezione privilegia lavori dal 2015, peer-reviewed o preprint dotati di valutazione, e quattro antecedenti utili a capire slicing, CPG, taint e tracciabilità UI.

Sono stati inclusi contributi sperimentali di natura diversa: benchmark controllati, corpus reali, studi con sviluppatori, confronti fra strumenti, verifiche formali accompagnate da casi applicativi e analisi di vulnerabilità. I risultati sono stati recuperati da testo integrale, fonti degli autori, atti ufficiali, pagine editoriali o arXiv. Non sono stati usati blog o documentazione di prodotto come prova di efficacia scientifica. I repository sono riportati per la riusabilità, non come sostituti della valutazione dei paper.

**Limite metodologico della rassegna:** non sono disponibili un protocollo preregistrato, un censimento esaustivo dei risultati per banca dati o un diagramma di esclusione di tipo PRISMA. Il corpus non permette una stima della quota di letteratura coperta, una classifica universale degli strumenti o una metanalisi di metriche eterogenee. L'apertura delle fonti serve a rendere controllabili le affermazioni sui lavori inclusi.

### 2.2 Pertinenza diretta, contributi abilitanti e casi deboli

La pertinenza non coincide sempre con il titolo. Un lavoro può ricostruire direttamente una sequenza; un altro può recuperare il raccordo necessario a costruirla; un terzo può soltanto aiutare a localizzare il codice. La matrice conserva queste differenze.

| Livello di pertinenza | Esempi nel corpus | Come utilizzare l'evidenza |
|---|---|---|
| Recupero di relazioni o sequenze vicine al flusso richiesto | [WTG](#u1), [WebSlice](#c3), [Micans](#c7), [RTL Paths](#h4). | Esaminare semantica degli archi, ordine, condizioni e limiti di fattibilità. |
| Infrastruttura per dipendenze, policy o provenance | [SDG](#f1), [CPG](#f2), [Vamsa](#d1), [CellIFT](#h2). | Individuare che cosa occorra aggiungere per ottenere il percorso e la proprietà desiderati. |
| Localizzazione, contesto e organizzazione del lavoro | [Feature location da screencast](#u7), [SmartCommit](#r2), [RepoGraph](#l3). | Valutare il vantaggio per il compito umano o dell'agente senza rinominarlo accuratezza dei flussi. |
| Dimostrazione limitata ma pertinente a un raccordo poco coperto | [AUTOSAR](#e1). | Considerare il meccanismo illustrato; la piccola dimostrazione non sostiene una stima di efficacia industriale. |

Il caso AUTOSAR è conservato perché collega esplicitamente modello, porte, runnable e RTE, ma ha una valutazione illustrativa molto piccola. Non deve avere lo stesso peso probatorio di uno studio con ground truth indipendente e più sistemi. Anche gli studi su sistemi industriali possono avere limiti di riproducibilità quando modelli, dati o configurazioni non sono pubblici. [E1](#e1), [E2](#e2), [R1](#r1)

### 2.3 Versioni bibliografiche e disponibilità dei link

I titoli collegano a DOI o arXiv verificati. Per **SUPOR, FlowCog e CellIFT** non è stato reperito un DOI o arXiv nelle fonti primarie consultate: il collegamento conduce agli atti ufficiali USENIX. Questa eccezione è dichiarata; nessun identificatore viene ricostruito per analogia. La presenza di un arXiv non implica che il lavoro sia ancora soltanto un preprint: lo stato editoriale compare separatamente nella tabella. [U5](#u5), [U6](#u6), [H2](#h2)

Sono state conservate le seguenti distinzioni:

- **RepoHyper:** sede FORGE 2025 verificata; numeri ricavati dalla versione arXiv v4 consultata. [L1](#l1)
- **CodexGraph:** schema e risultati della versione NAACL 2025. Il rapporto non gli attribuisce archi di chiamata indicati come sviluppo futuro. [L2](#l2)
- **Isadora:** versione estesa di rivista, anno bibliografico 2023 e pubblicazione online nel 2022; la precedente versione non è contata come lavoro indipendente. [H3](#h3)
- **Code2DFD e confronto EMSE:** condividono microSecEnD; non sono due validazioni su corpus indipendenti. [C5](#c5), [C8](#c8)
- **StoryDroid e StoryDistiller:** appartengono a una linea evolutiva; differenze di corpus e protocollo vanno controllate prima di confrontarne i numeri. [U2](#u2), [U3](#u3)
- **SLiCE, SWE-PRBench e RTL Paths:** lo stato di preprint e l'eventuale incertezza sulla pubblicazione definitiva restano espliciti. [D2](#d2), [L6](#l6), [H4](#h4)

Per FlowCog esiste una discrepanza fra il BibTeX ufficiale e la lista sul frontespizio/pagina: qui si usano i sei autori concordanti fra PDF e pagina. Per Vamsa viene usato il DOI confermato dai metadati editoriali, evitando il segnaposto presente nella copia autore. Queste precisazioni riguardano la tracciabilità bibliografica, non la qualità del metodo. [U6](#u6), [D1](#d1)

### 2.4 Regole per leggere i risultati

**Risultati misurati:** le colonne di valutazione e risultati riportano gli esperimenti degli autori. Un conteggio o una percentuale calcolati qui sono identificati come derivati. **Limiti dichiarati:** sintetizzano limitazioni, minacce e restrizioni documentate nel lavoro; quando una discussione sistematica manca, viene segnalato. **Interpretazione:** contiene le nostre cautele e deduzioni, senza presentarle come conclusioni sperimentali degli autori.

Le sigle **NR** e **NV** hanno significati diversi. NR significa che la misura non è riportata nel lavoro consultato; NV significa che non è stato possibile verificarla nella ricerca. «Non applicabile» indica invece che la metrica non corrisponde al tipo di contributo, come una precisione empirica richiesta a un algoritmo fondativo presentato soprattutto formalmente.

Un risultato va letto insieme a cinque informazioni: **unità valutata, denominatore, criterio di verità, selezione dei casi e costo**. La precisione dei campi UI non misura quella dei cammini; il recall su vulnerabilità note eleggibili non misura tutti i bug di un'applicazione; il successo sui casi terminati non descrive gli input esclusi per timeout. Le schede evidenziano questi punti dove incidono sull'interpretazione. [U5](#u5), [C6](#c6), [U6](#u6)

<a id="tassonomia"></a>

## 3. Tassonomia dei flussi e delle rappresentazioni

### 3.1 I sei tipi richiesti

La classificazione seguente è **una nostra organizzazione del problema**. Le categorie si sovrappongono: un'azione dell'utente può attivare un flusso tecnico, modificare un dato e determinare una transizione di stato. L'appartenenza a una categoria non implica che un paper copra tutti questi passaggi.

| Tipo | Domanda caratteristica | Oggetti da distinguere | Forma utile della risposta |
|---|---|---|---|
| **Dati** | Da dove viene questo valore, chi lo modifica e chi lo interpreta? | Valore, campo, trasformazione, tabella/colonna/riga, aggregazione, versione. | Grafo di provenance con trasformazioni e condizioni; percorso writer–reader quando identificabile. |
| **Funzionale** | Quali passi realizzano la funzionalità? | Feature, attività, regole, effetti osservabili, alternative. | Slice relativa all'effetto, sequenza o modello di processo, con raccordi al codice. |
| **Tecnico** | Come viaggiano richieste, chiamate, messaggi ed eventi? | Entrypoint, handler, endpoint, canale, payload, risposta. | Grafo di comunicazione e sequenze condizionate; correlazione tra richiesta ed effetto. |
| **Logico e controllo** | Quali operazioni sono abilitate, in quale ordine e in quali stati? | Guardie, stato, callback, sincronizzazione, eccezioni, retry. | CFG/ICFG, macchina a stati, ordine parziale o schedule con vincoli. |
| **Operativo e UX** | Che cosa vede e fa l'utente, e come cambia il sistema? | Widget, schermata, binding, evento, sessione, esito. | Grafo di finestre/scene e collegamenti al codice; journey osservato se esistono dati d'uso. |
| **Hardware ed embedded** | Quale segnale o campione arriva a quale operazione o attuatore? | Porte, registri, bus, MMIO, ISR, task, runnable, clock e campioni. | Dipendenze di segnale, proprietà IFT e percorsi temporalmente qualificati. |

### 3.2 Famiglie di rappresentazioni presenti nei lavori

| Rappresentazione | Relazioni che rende esplicite | Domanda a cui aiuta a rispondere | Cautela |
|---|---|---|---|
| **AST** | Struttura sintattica di espressioni e dichiarazioni. | Dove è scritto un costrutto? | La struttura sintattica non fornisce da sola ordine, alias o dipendenze dinamiche. È un ingrediente dei grafi integrati. [F2](#f2) |
| **CFG / ICFG** | Possibili trasferimenti di controllo, anche fra procedure. | Quali istruzioni possono seguire altre istruzioni? | Occorre modellare chiamate implicite, callback e framework. [F4](#f4), [C4](#c4) |
| **PDG / SDG** | Dipendenze di dati e controllo; il SDG aggiunge raccordi interprocedurali. | Che cosa può influire su un criterio, o esserne influenzato? | Lo slice non è una singola esecuzione; chiamata e ritorno devono rispettare il contesto. [F1](#f1) |
| **CPG** | Integrazione di AST, controllo e dipendenze per query. | Quali pattern attraversano più viste del programma? | Le relazioni effettivamente supportate dipendono dall'implementazione e dalla versione. [F2](#f2), [L5](#l5) |
| **Call graph e points-to** | Invocazioni possibili e oggetti astratti raggiungibili. | Quale implementazione e quale oggetto partecipano al trasferimento? | La risoluzione di framework e comunicazioni richiede modelli aggiuntivi. [C4](#c4), [C7](#c7) |
| **DFD architetturale** | Servizi, database, sistemi esterni e connessioni. | Qual è la struttura di comunicazione recuperata? | Una connessione non equivale a lineage del payload o a una sequenza fattibile. [C5](#c5), [C8](#c8) |
| **WIR e lineage strutturata** | Operazioni, ruoli dei dati e provenienza di colonne/campi. | Quali sorgenti e trasformazioni producono una feature o un campo? | La granularità di schema non prova identità di record, finestra temporale o significato aziendale. [D1](#d1), [D2](#d2) |
| **WTG / ATG / SceneTG** | Finestre, activity o scene e transizioni associate agli eventi. | Quali navigazioni possono essere recuperate o esplorate? | La granularità dei nodi cambia; un grafo della GUI non equivale al journey delle persone. [U1](#u1), [U3](#u3), [U4](#u4) |
| **BPMN recuperato** | Attività, gateway, sequenze e oggetti dati derivati dal programma. | Quale processo viene suggerito dalla struttura del codice? | Il recupero dei task non certifica tutti gli ordini e le regole del processo. [U8](#u8) |
| **Grafi transazionali e sync-CFG** | Letture/scritture, visibilità, sincronizzazione e interleaving. | Quale ordine concorrente può violare una proprietà? | Bounds, modello della memoria e semantica degli interrupt delimitano la conclusione. [D3](#d3), [E3](#e3) |
| **Grafi di repository per LLM** | Simboli, appartenenza, riferimenti e altre relazioni selezionate. | Quale contesto recuperare per un compito? | Non assumere archi assenti dallo schema né dedurre completezza dal successo del compito. [L1](#l1), [L2](#l2), [L3](#l3) |
| **IFT, proprietà e cammini RTL** | Influenze su segnali, condizioni di flusso e successioni derivate da tracce. | Quali sorgenti possono influire su segnali o uscite? | Copertura del testbench e raccordo HW/SW restano da specificare. [H2](#h2), [H3](#h3), [H4](#h4) |

### 3.3 Lineage, taint, causalità e correttezza semantica

Nel lessico di questo rapporto, **lineage/provenance** riguarda l'origine e le trasformazioni di un risultato, mentre **taint** riguarda la propagazione di un'informazione marcata verso usi o destinazioni di interesse. Un'analisi può deliberatamente astrarre i valori e conservare soltanto la possibilità di influenza. Le etichette di sicurezza e le policy restringono poi quali influenze siano ammesse. Queste distinzioni aiutano a leggere Vamsa, FlowDroid e SecVerilog senza attribuire loro il medesimo obiettivo. [D1](#d1), [F4](#f4), [H1](#h1)

**Deduzione metodologica:** sapere che un dato dipende da un altro non basta a stabilire che il calcolo abbia il significato desiderato. Se il requisito riguarda un totale mensile, occorre una proprietà sulla finestra e sulla popolazione aggregata; se riguarda autorizzazione, serve un rapporto fra identità, oggetto e operazione. Un cammino corretto può quindi trasportare un valore semanticamente errato. La [sezione 8](#bug-writer-reader) sviluppa questa distinzione con esempi dichiaratamente sintetici.

La causalità richiede a sua volta cautela. La vicinanza temporale di eventi osservati non identifica automaticamente una relazione produttore–consumatore. Proponiamo di registrare anche correlazioni, identità dei dati e vincoli d'ordine quando disponibili, lasciando esplicite le relazioni ancora candidate. Questa indicazione è una scelta metodologica del rapporto, non una proprietà garantita da ogni strumento censito.

<a id="matrice"></a>

## 4. Matrice bibliografica: tutti i 38 lavori

Le tabelle sono divise per argomento per facilitarne la lettura. Ogni lavoro compare **una sola volta**; le raccomandazioni successive rinviano alla stessa scheda. Le colonne accorpano alcuni campi per mantenere una riga per paper, conservando tutti gli elementi richiesti.

**Convenzioni:** P = precision; R = recall; TP/FP/FN = veri positivi/falsi positivi/falsi negativi; GT = ground truth; LOC/KLOC = righe/migliaia di righe di codice. I numeri non sono normalizzati fra studi. Le cautele nell'ultima colonna sono **nostra interpretazione**; i risultati precedenti descrivono i paper. Il link «fonti» permette di controllare versione e localizzazione del dato.

### 4.1 Dati, provenance e transazioni

| ID, titolo e link verificato | Autori; anno; sede e stato | Flusso; tecnica; linguaggi e piattaforme | Rappresentazione del flusso | Valutazione e benchmark | Risultati principali misurati | Limiti dichiarati / restrizioni documentate | Nostra interpretazione e cautele |
|---|---|---|---|---|---|---|---|
| <a id="d1"></a>**D1** — [Vamsa: Automated Provenance Tracking in Data Science Scripts](https://doi.org/10.1145/3394486.3403205). [Fonti](#src-d1). | Mohammad Hossein Namaki; Avrilia Floratou; Fotis Psallidas; Subru Krishnan; Ashvin Agrawal; Yinghui Wu; Yiwen Zhu; Markus Weimer.<br>**2020**. KDD 2020.<br>**Stato:** Peer-reviewed. | **Flusso:** Dati; funzionale (pipeline ML)<br>**Tecnica:** Statica; AST, flussi di dipendenza, knowledge base di API<br>**Piattaforme:** Python 3; pandas e librerie ML (scikit-learn, XGBoost, LightGBM, ecc.). | Workflow Intermediate Representation (WIR): variabili e operazioni, annotazioni semantiche di modello/dataset/feature/label; provenance di colonne incluse/escluse. | 26.000 script (24.800 NTBK, 1.200 Kaggle) per copertura/prestazioni; 150+150 script manualmente annotati, selezionati fra quelli per cui Vamsa produce output, per accuratezza. | Feature inclusion: Kaggle precision 91,37%, recall 92,89%; NTBK 90,54% / 94,08%. Copertura provenance non vuota: 80,85% Kaggle, 74,48% NTBK. Tab.2–3. | KB costruita manualmente; API/costrutti non supportati e selezione colonne basata sui valori; errori merge/split train-test. Provenance delle partizioni e uso di runtime indicati come futuro. | Le alte P/R non si riferiscono a tutti i 26.000 script. Granularità colonna, non dimostrazione della corretta granularità di aggregazione di una applicazione arbitraria. |
| <a id="d2"></a>**D2** — [Schema Lineage Extraction at Scale: Multilingual Pipelines, Composite Evaluation, and Language-Model Benchmarks](https://arxiv.org/abs/2508.07179). [Fonti](#src-d2). | Jiaqi Yin; Yi-Wei Chen; Meng-Lung Lee; Xiya Liu.<br>**2025**. arXiv:2508.07179v1.<br>**Stato:** Preprint con valutazione; peer review non verificata. | **Flusso:** Dati; trasformazioni e aggregazioni<br>**Tecnica:** LLM; estrazione strutturata con prompting<br>**Piattaforme:** SQL, Python/PySpark, C#/Scope; pipeline enterprise Microsoft. | Lineage per campo/schema: colonne e tabelle sorgenti, logica di trasformazione, aggregazioni; record strutturati confrontati con SLiCE. | 50 script industriali, 1.700 lineage annotate, 12 modelli, 7 strategie di prompting, 6 trial randomizzati. | SLiCE medio GPT-4.1: 0,418±0,005 base, 0,673±0,008 one-shot, 0,767±0,007 con 1 traccia di ragionamento umana. Qwen2.5-Coder32B: 0,355→0,623→0,734. Tab.2. | Il paper mostra calo con maggiore complessità e benefici CoT non uniformi sui modelli più piccoli; usa tracce di esperti. Nessuna sezione dedicata ai limiti generali. | SLiCE è un punteggio composito strutturale/testuale, mediato prima per schema e poi per script; non è una percentuale di lineage corretti né una prova di equivalenza eseguibile. Il data-flow matching di CodeBLEU è escluso. Rilascio pubblico dei 50 script non verificato. |
| <a id="d3"></a>**D3** — [CLOTHO: Directed Test Generation for Weakly Consistent Database Systems](https://arxiv.org/abs/1908.05655). [Fonti](#src-d3). | Kia Rahmani; Kartik Nagar; Benjamin Delaware; Suresh Jagannathan.<br>**2019**. OOPSLA / PACMPL 2019.<br>**Stato:** Peer-reviewed; preprint verificato. | **Flusso:** Dati; logico/controllo; writer-reader via DB distribuito<br>**Tecnica:** Ibrida: analisi statica + vincoli/model checking + replay di test<br>**Piattaforme:** Java/JDBC + SQL; valutazione su Cassandra. | Rappresentazione astratta di transazioni; grafo di dipendenze WR/RW/WW e ordine; vincoli di visibilità/consistenza; schedule e input concreti. | 7 programmi OLTP-Bench: SEATS, TATP, TPC-C, SmallBank, Voter, Twitter, Wikipedia; confronto con test random basati su Jepsen. | Tabella 2: 119 anomalie in totale, di cui 98 riprodotte automaticamente e 21 con intervento manuale (somme nostre dei conteggi pubblicati). Ricerca esecuzioni che violano 12 requisiti TPC-C; gli autori identificano 7 requisiti aggiuntivi esaminando le anomalie. | Ricerca limitata da bound; SQL non interamente supportato: 11 query con JOIN su 131 riscritte a mano. Replay talvolta richiede aggiustamenti ai limiti dei cicli e all’ordine delle righe; non tutte le anomalie sono bug funzionali. | I 7 requisiti aggiuntivi sono identificati dagli autori, non sintetizzati automaticamente. 98/119 misura la riproduzione automatica delle anomalie già rilevate entro i limiti della ricerca; non misura recall. |

### 4.2 Collegamenti fra componenti, framework e architetture

| ID, titolo e link verificato | Autori; anno; sede e stato | Flusso; tecnica; linguaggi e piattaforme | Rappresentazione del flusso | Valutazione e benchmark | Risultati principali misurati | Limiti dichiarati / restrizioni documentate | Nostra interpretazione e cautele |
|---|---|---|---|---|---|---|---|
| <a id="c1"></a>**C1** — [IccTA: Detecting Inter-Component Privacy Leaks in Android Apps](https://doi.org/10.1109/ICSE.2015.48). [Fonti](#src-c1). | Li Li; Alexandre Bartel; Tegawendé F. Bissyandé; Jacques Klein; Yves Le Traon; Steven Arzt; Siegfried Rasthofer; Eric Bodden; Damien Octeau; Patrick McDaniel.<br>**2015**. ICSE 2015, pp. 280–291.<br>**Stato:** Peer-reviewed. | **Flusso:** Controllo e dati attraverso inter-component communication (ICC) Android; privacy leak source-to-sink.<br>**Tecnica:** Statica: risoluzione Intent/URI con IC3/Epicc; riscrittura degli archi ICC in chiamate esplicite; modellazione lifecycle/callback e taint analysis FlowDroid.<br>**Piattaforme:** Android Dalvik/Java, IR Jimple/Soot; AndroidManifest e registrazioni dei receiver. | CFG/ICFG connesso fra componenti; dummyMain per lifecycle e callback; access path e percorsi di propagazione dei dati. | 31 microapp: 22 aggiunte a DroidBench e 9 ICC-Bench. Corpus reali: 15.000 app Google Play e 1.260 MalGenome. | Microbenchmark: IccTA 28 TP, 1 FP, 1 FN, precision e recall 96,6%; Amandroid 15 TP, 4 FP, 14 FN, precision 78,9% e recall 51,7%. Nei corpus: 2.395 segnalazioni in 337 app Google Play e 534 in 108 app MalGenome. | Reflection risolta solo con stringhe costanti; native e multithreading incompleti; alcune API ICC e operazioni sulle stringhe non modellate; inter-app non valutato; fallimenti di memoria/tempo. | Le segnalazioni nei corpus non sono tutte vulnerabilità confermate e non stimano precisione real-world. Il numero di app per cui l’analisi è completata non è verificato. Nessuna provenienza DB. |
| <a id="c2"></a>**C2** — [Composite Constant Propagation: Application to Android Inter-Component Communication Analysis](https://doi.org/10.1109/ICSE.2015.30). [Fonti](#src-c2). | Damien Octeau; Daniel Luchaup; Matthew Dering; Somesh Jha; Patrick McDaniel.<br>**2015**. ICSE 2015, pp. 77–88.<br>**Stato:** Peer-reviewed. | **Flusso:** Archi di comunicazione sender–receiver Android; risoluzione indiretta abilitante analisi successive dei dati.<br>**Tecnica:** Statica: composite constant propagation multi-valore, flow/context-sensitive; specifiche COAL e riduzione a un problema IDE; matching Intent/filter/URI.<br>**Piattaforme:** Java/Android, bytecode e Soot; metadata di Intent, filtri e URI. | Valori astratti correlati di oggetti compositi e insieme di archi ICC candidati. | 500 app campionate casualmente da 453.525 Google Play; 460 analisi completate, 40 timeout/OOM. Baseline Epicc. | Su 5.306 valori Intent/filter, IC3 ne ricostruisce precisamente 4.575 contro 3.660 di Epicc; su 522 URI, 374 contro 176. Archi candidati: 26.872 contro 120.817, riduzione riportata del 78%. Tempo totale 64.571 s sulle 460 app completate, circa 140 s/app. | Native/reflection non coperti; insieme limitato di operazioni sulle stringhe; confronto con tracce dinamiche e ablation della correlazione rinviati. | Il 78% misura la riduzione dei candidati, non precision o recall rispetto a tutti gli archi runtime. IC3 non è da solo un’analisi taint end-to-end. Non mescolare questi risultati con l’estensione TSE 2016. |
| <a id="c3"></a>**C3** — [Cross-Language Program Slicing for Dynamic Web Applications](https://doi.org/10.1145/2786805.2786872). [Fonti](#src-c3). | Hung Viet Nguyen; Christian Kästner; Tien N. Nguyen.<br>**2015**. ESEC/FSE 2015, pp. 369–380.<br>**Stato:** Peer-reviewed. | **Flusso:** Dipendenze di controllo e dati cross-language, cross-file e cross-page; slicing di applicazioni web.<br>**Tecnica:** Statica: esecuzione simbolica PHP, string origins, parsing variability-aware e VarDOM; collegamento GET/POST mediante URL e nomi dei form; SQL SELECT verso accessi fetch-array.<br>**Piattaforme:** PHP, SQL, HTML e JavaScript; prototipo Eclipse con TypeChef e JavaBDD. | Grafo di dipendenze fra entità di programma, contenuto generato e colonne SQL lette; slice ottenute per raggiungibilità. | 5 app SourceForge: AddressBook, SchoolMate, TimeClock, UPB e WebChess, da 8.183 a 104.640 LOC. 100 test SchoolMate, inclusi 20 inter-page; oracle Quercus per PHP e manuale per cross-language. | 40.670 slice: 4.105 cross-language, 15.317 cross-file, 5.101 cross-string e 2.303 cross-page; 9.367 archi cross-language su 76.961 totali. 98/100 test superati; 2 falliscono per archi inter-page infeasible. Tempo 4,6–37,6 s/app. Nessuna baseline comparabile disponibile. | Implementato SQL→PHP; PHP→SQL INSERT/UPDATE e dipendenze intra-SQL sono lavoro futuro. No AJAX, document.write o eval; loop limitati a due iterazioni, ricorsione saltata; possibili percorsi infeasible. | Il numero di slice non misura bug recall né produttività degli sviluppatori. Non ricostruisce un ciclo DB read/write completo o l’identità della riga/versione fra writer e reader. |
| <a id="c4"></a>**C4** — [Jasmine: A Static Analysis Framework for Spring Core Technologies](https://doi.org/10.1145/3551349.3556910). [Fonti](#src-c4). | Miao Chen; Tengfei Tu; Hua Zhang; Qiaoyan Wen; Weihang Wang.<br>**2022**. ASE 2022.<br>**Stato:** Peer-reviewed. | **Flusso:** Controllo e dati attraverso dependency injection, proxy/AOP ed entrypoint Spring.<br>**Tecnica:** Statica: simulazione della creazione e injection dei bean singleton/prototype e degli aspetti; trasformazione IR per Soot, Doop e FlowDroid.<br>**Piattaforme:** Java/Spring, IR Soot, annotazioni, XML e regole di matching. | Callgraph e IR con chiamate del framework rese esplicite; access path per downstream taint analysis. | 18 progetti reali rappresentati da 21 moduli; microbenchmark in 8 categorie, numero complessivo di casi non verificato. Confronti con JackEE, CHA e SPARK. | Esempio pybbs: Jasmine+JackEE produce 2.896 archi contro 1.168 di JackEE, e 715 metodi raggiungibili contro 438. FlowDroid+Jasmine: 44 percorsi sensibili candidati in 9 progetti; 12 confermati dinamicamente in 3 progetti, 32 esclusi per control flow. Confermati per modulo: mall-admin 3, mall-portal 3, Halo 4, favorites-web 2; CHA/SPARK riportano zero leak su questi moduli. | Nessun oracle completo per misurare precision/recall del callgraph reale; bean della stessa classe con ID diversi confusi; AOP su interfacce non supportato; alias spurî e path feasibility. | Più archi prodotti non dimostrano da soli maggiore accuratezza. I 44 candidati non sono 44 vulnerabilità; 12/44 non è la precisione generale di Jasmine. Nessun collegamento inter-servizio completo. |
| <a id="c5"></a>**C5** — [Automatic Extraction of Security-Rich Dataflow Diagrams for Microservice Applications written in Java](https://doi.org/10.1016/j.jss.2023.111722). [Fonti](#src-c5). | Simon Schneider; Riccardo Scandariato.<br>**2023**. Journal of Systems and Software 202, article 111722.<br>**Stato:** Peer-reviewed. | **Flusso:** Connessioni fra microservizi, DB, sistemi esterni e broker; proprietà di sicurezza architetturali.<br>**Tecnica:** Statica: parsing del codice/configurazioni, ricerca iterativa di keyword e identificatori, estrattori specifici per tecnologia.<br>**Piattaforme:** Java/Spring; Docker Compose, Dockerfile e configurazioni/variabili ambiente; REST, Feign, JDBC, Kafka e RabbitMQ. | DFD con nodi servizio/DB/esterno, connessioni dirette, security tags e riferimenti file/riga. Kafka/RabbitMQ modellati come connessioni producer–consumer. | 17 app microSecEnD: 7 di sviluppo e 10 di validazione; DFD manuali sottoposti a controllo. Tempi misurati con 5 run/app. | Sulle 10 app di validazione, tutti gli elementi: 836 TP, 63 FP, 151 FN, precision 93% e recall 85% riportati. Solo information flows: 152 TP, 7 FP, 29 FN, precision derivata 95,60% e recall 83,98%. Tempo medio 4 s, massimo 22 s, escluso clone. | Campione piccolo/medio di convenienza; copertura tecnologica specifica e incompleta; ground truth manuale; nomi DB ambigui. Confronti con baseline non sempre sul medesimo insieme di app. | L’arco Kafka/DB non equivale a tracciamento del payload, lineage di colonna/riga o fattibilità end-to-end. Le metriche su tutti gli elementi includono più delle sole connessioni. |
| <a id="c6"></a>**C6** — [Detecting Broken Object-Level Authorization Vulnerabilities in Database-Backed Applications](https://doi.org/10.1145/3658644.3690227). [Fonti](#src-c6). | Yongheng Huang; Chenghang Shi; Jie Lu; Haofeng Li; Haining Meng; Lian Li.<br>**2024**. ACM CCS 2024.<br>**Stato:** Peer-reviewed. | **Flusso:** Dati applicazione–database e relazioni di autorizzazione; bug di broken object-level authorization (BOLA).<br>**Tecnica:** Statica: TChecker context-sensitive, ricostruzione SQL/JSQLParser, binding variabile–colonna, alias/dominanza e FK implicite; inferenza di ownership/membership/hierarchy/status e verifica di WHERE/controlli dominanti.<br>**Piattaforme:** PHP e SQL, schema CREATE; API dei database abstraction layer specificate manualmente. | Relazioni fra tabelle/colonne e modelli di autorizzazione collegati al controllo e ai flussi del programma; non provenienza di versioni di righe. | Studio di 101 BOLA; valutazione su 25 app PHP. Set di vulnerabilità note eleggibili: 15, dopo l’esclusione di 16 casi SELECT dai 31 casi PHP. | 247 alert: 193 TP e 54 FP, precision derivata 78,14%. I 193 includono 15 noti e 178 nuovi; 155 nuovi confermati o risolti dai maintainer, 52 CVE alla pubblicazione. Recall sui noti eleggibili: 15/15. Per missing ownership checks: BolaRay 104 TP contro 25 del comparatore Mace reimplementato. Tempo massimo 427,5 s. | Euristiche non sound/complete; PHP; SQL non parseabile scartato; SELECT non sink sensibile; controlli sulla variabile sbagliata non coperti; DAL manuali (~13 righe/API). | Il “false positive rate” 21,86% è 54/247 alert, non FP/(FP+TN). Il 100% recall non riguarda tutte le vulnerabilità possibili. Mace ha scope minore: evitare 193 vs 25 senza qualifica. Non è verifica universale della business logic. |
| <a id="c7"></a>**C7** — [Bridge the Islands: Pointer Analysis for Microservice Systems](https://doi.org/10.1145/3728896). [Fonti](#src-c7). | Teng Zhang; Yufei Liang; Ganlin Li; Tian Tan; Chang Xu; Yue Li.<br>**2025**. Proceedings of the ACM on Software Engineering 2, ISSTA, article ISSTA023, 23 pages.<br>**Stato:** Peer-reviewed. | **Flusso:** Controllo e dati fra microservizi, RPC e code di messaggi; DI e web entrypoint; taint cross-service.<br>**Tecnica:** Statica: ciclo on-the-fly fra modellazione DI/web entrypoint, kernel points-to e risoluzione RPC/messaging; matching HTTP/path e exchange/routing-key/queue; trasferimento di argomenti, payload e ritorni.<br>**Piattaforme:** Java/Spring; OpenFeign, Apache Dubbo, RabbitMQ e RocketMQ. | Callgraph, insiemi points-to e relazioni di comunicazione connesse ai flussi dei valori; versioni context-insensitive e context-sensitive. | 10 app reali containerizzate, media 49,8k LOC applicativi; driver >4k LOC. Taint simulato/iniettato: 1.733 sorgenti, 408 sink e 335 flussi veri. Oracle del callgraph da tracce dinamiche. | RPC macro R 94,9%, P 99,8%; totali 744 TP, 1 FP su 778 GT (micro R derivata 95,63%). Messaging context-sensitive: 49 TP, 2 FP su 55 GT; macro P/R 70,8%. Taint: CS 335 TP/524 report, CI 335/1.601; entrambi recuperano tutti i 335 GT simulati. | AOP/lifecycle Spring e reflection incompleti; modelli di side effect omettono chiamate interne; tracce dinamiche non esaustive; campione/framework limitati. | 335 flussi simulati non sono vulnerabilità reali scoperte. Non confondere medie macro e micro. Kafka, polyglot e identità writer–reader DB non valutati; nessuna verifica generale di invarianti business. |
| <a id="c8"></a>**C8** — [Comparison of static analysis architecture recovery tools for microservice applications](https://doi.org/10.1007/s10664-025-10686-2). [Fonti](#src-c8). | Simon Schneider; Alexander Bakhtin; Xiaozhou Li; Jacopo Soldani; Antonio Brogi; Tomas Cerny; Riccardo Scandariato; Davide Taibi.<br>**2025**. Empirical Software Engineering 30, article 128.<br>**Stato:** Peer-reviewed. | **Flusso:** Architettura di comunicazione: componenti, connessioni ed endpoint REST.<br>**Tecnica:** Confronto sperimentale di strumenti statici e delle loro combinazioni; 13 identificati e 9 eseguiti. Non introduce un nuovo algoritmo di analisi.<br>**Piattaforme:** Applicazioni Java/Spring, sorgenti e configurazioni di deployment. | Grafi architetturali/DFD: componenti, connessioni ed endpoint; aggregazione di output con operatori AND/OR. | 17 app del dataset microSecEnD già usato da Code2DFD; 727 caratteristiche ground truth. Aggiunti 63 endpoint mediante annotazioni manuali ricontrollate. | F1 complessivo pubblicato: 0,86 per Code2DFD, 0,91 per la migliore combinazione di Code2DFD, MicroDepGraph, RAD e RAD-source. Questi valori concordano fra abstract, risultati e scheda arXiv. TP/FP/FN complessivi non verificati. | App piccole/medie omogenee Java/Spring; ground truth manuale; problemi esecutivi e caratteristiche non comparabili; per gli strumenti ibridi esaminata solo la parte statica. | Non è una replica indipendente su un secondo corpus: stesso dataset di Code2DFD e autori parzialmente sovrapposti. Alcuni numeri narrativi per singole caratteristiche sono incoerenti e qui omessi. F1 architetturale non dimostra correttezza semantica end-to-end. |

### 4.3 Interfacce, navigazione e recupero delle funzionalità

| ID, titolo e link verificato | Autori; anno; sede e stato | Flusso; tecnica; linguaggi e piattaforme | Rappresentazione del flusso | Valutazione e benchmark | Risultati principali misurati | Limiti dichiarati / restrizioni documentate | Nostra interpretazione e cautele |
|---|---|---|---|---|---|---|---|
| <a id="u1"></a>**U1** — [Static Window Transition Graphs for Android](https://doi.org/10.1109/ASE.2015.76). [Fonti](#src-u1). | Shengqian Yang; Hailong Zhang; Haowei Wu; Yan Wang; Dacong Yan; Atanas Rountev.<br>**2015**. ASE 2015, pp. 658–668.<br>**Stato:** Peer-reviewed. | **Flusso:** Operativo/UX; logico e controllo: finestre, callback e navigazione.<br>**Tecnica:** Statica; analisi GUI e semantica dello stack delle finestre.<br>**Piattaforme:** Java; Android. | Window Transition Graph (WTG): nodi per le finestre; archi annotati con eventi, widget, callback e operazioni push/pop. I percorsi rappresentano sequenze ordinate di interazione. | 20 app open source; controllo manuale degli archi su sei app scelte perché più piccole; 1.581 test generati ed eseguiti. Confronto dell'enumerazione dei percorsi con e senza controllo dello stack. | Sei app controllate: 31/525 archi non fattibili, circa 6% (somma della Tab. III). BarcodeScanner: 88/516 test fattibili. In dieci app, il controllo dello stack riduce almeno del 26% i percorsi di tre eventi rispetto alla visita senza tale controllo. | La versione del 2015 non modella thread, interazioni fra app, transizioni asincrone, widget personalizzati, intent impliciti e launch mode; circa il 13% dei nodi risulta privo di archi entranti. | La precisione degli archi non garantisce la fattibilità delle loro concatenazioni. Il lavoro collega gesti, callback e navigazione, ma non dimostra gli effetti sul database o sul backend. L'estensione del 2018 non va contata come replica indipendente. |
| <a id="u2"></a>**U2** — [StoryDroid: Automated Generation of Storyboard for Android Apps](https://doi.org/10.1109/ICSE.2019.00070). [Fonti](#src-u2). | Sen Chen; Lingling Fan; Chunyang Chen; Ting Su; Wenhe Li; Yang Liu; Lihua Xu.<br>**2019**. ICSE 2019, pp. 596–607.<br>**Stato:** Peer-reviewed. | **Flusso:** Operativo/UX; tracciabilità schermata–codice.<br>**Tecnica:** Ibrida: recupero statico di transizioni e codice; rendering/esecuzione delle activity.<br>**Piattaforme:** Java e XML; Android APK. | Storyboard navigabile con schermate e Activity Transition Graph (ATG); collegamenti ai layout, al codice delle activity e alle gerarchie dei metodi. | 10 app costruite; 100 reali (50 open source, 50 closed source); confronto con STOAT, 30 min/app. Studio separato con 8 persone e 4 app. | Activity coperte: 87% open source e 74% closed source, rispetto al manifest; meno di 3 min/app in media. Tutte le transizioni nei 10 benchmark costruiti. Studio utenti: esplorazione 2,5 contro 5,2 min; copertura 86,5% contro 40,8% senza strumento. | Decompilazione e call graph incompleti, caricamenti dinamici; rendering problematico con onDraw e componenti personalizzati. | Studio utenti e corpus delle 100 app hanno denominatori distinti. Il collegamento schermata–codice non dimostra la catena fino a servizi remoti e persistenza. |
| <a id="u3"></a>**U3** — [Automatically Distilling Storyboard With Rich Features for Android Apps](https://doi.org/10.1109/TSE.2022.3159548). [Fonti](#src-u3). | Sen Chen; Lingling Fan; Chunyang Chen; Yang Liu.<br>**2023**. IEEE Transactions on Software Engineering 49(2), pp. 667–683.<br>**Stato:** Peer-reviewed; preprint arXiv del 2022. | **Flusso:** Operativo/UX; funzionale: storyboard, transizioni e dati di attivazione.<br>**Tecnica:** Ibrida: analisi statica, recupero degli input e rendering dinamico.<br>**Piattaforme:** Java e XML; Android APK. | Storyboard arricchito e ATG; schermate collegate a componenti, layout, logica e chiamate all'interno delle activity, con informazioni sui dati necessari all'attivazione. | 150 app: 75 da F-Droid e 75 da Google Play; timeout di 30 minuti. Confronti con IC3, Gator, StoryDroid e STOAT. | Transizioni medie/app: 23,30 contro IC3 7,78 e Gator 9,96. Launch ratio (activity renderizzate/considerate): 82,37% open source, 80,14% closed source; StoryDroid 55% sul sottoinsieme open source. Somiglianza immagini basata su MAE/MSE: 96,5%/91,6%. | Autenticazione; dati richiesti in SharedPreferences, SQLite o server non forniti; decompilazione e call graph incompleti; rappresentazioni incomplete dei fragment. | Conteggi di transizioni e somiglianza visiva non misurano correttezza dei percorsi. Non recupera tutti gli stati persistenti necessari; stessa linea evolutiva di StoryDroid. |
| <a id="u4"></a>**U4** — [Scene-Driven Exploration and GUI Modeling for Android Apps](https://arxiv.org/abs/2308.10228). [Fonti](#src-u4). | Xiangyu Zhang; Lingling Fan; Sen Chen; Yucheng Su; Boyuan Li.<br>**2023**. ASE 2023, Research Papers.<br>**Stato:** Peer-reviewed; arXiv 2308.10228 verificato. | **Flusso:** Operativo/UX; logico: navigazione a granularità di scena.<br>**Tecnica:** Ibrida; esplorazione dinamica assistita da analisi statica.<br>**Piattaforme:** Android nativo; analisi di APK e gerarchie UI. | Scene Transition Graph (SceneTG), con scene e transizioni per activity, fragment, dialoghi, menu e altri stati dell'interfaccia. | Dieci app sintetiche con scene, transizioni e percorsi di riferimento; 100 app reali, 50 open source e 50 closed source. Confronti con GoalExplorer, ICCBot, StoryDistiller e Gator. | Nei dieci benchmark sintetici recupera tutte le scene e transizioni riportate, con percorsi verificati. Nel corpus reale, transizioni medie per app: SceneDroid 30,25; GoalExplorer 0,81; ICCBot 13,52; StoryDistiller 12,03; Gator 18,68. Scene medie per app, nello stesso ordine: 22,93; 1,63; 9,53; 13,83; 9,95. | Login e altri fallimenti di lancio, interazioni non supportate e supporto limitato per app non native. | Maggiori conteggi non provano recall sulle 100 app reali. Il +168,74% aggregato dell’abstract non vale per ogni baseline; granularità e versioni contano. Si usa arXiv perché il DOI candidato non è stato verificato. |
| <a id="u5"></a>**U5** — [SUPOR: Precise and Scalable Sensitive User Input Detection for Android Apps](https://www.usenix.org/conference/usenixsecurity15/technical-sessions/presentation/huang). [Fonti](#src-u5). | Jianjun Huang; Zhichun Li; Xusheng Xiao; Zhenyu Wu; Kangjie Lu; Xiangyu Zhang; Guofei Jiang.<br>**2015**. 24th USENIX Security Symposium, pp. 977–992.<br>**Stato:** Peer-reviewed; DOI/arXiv non reperito nelle fonti primarie consultate. | **Flusso:** Dati; operativo/UX: campo di input → variabile → sink.<br>**Tecnica:** Statica; geometria/testi del layout, ID dei widget, backward slicing e taint.<br>**Piattaforme:** Java e XML; Android APK. | Associazioni fra campi UI e variabili del codice; percorsi di propagazione dei dati verso rete, SMS, log e content provider. | 16.000 app; classificazione campi controllata su 40. Verifica flussi: 104 app segnalate fra le prime 6.000 analizzate, distinta dalle 355 segnalate complessivamente. | Campi: P = 145/149 = 97,3%; R = 145/(145+4) = 97,3%. Segnalate 355 app. Fra le 104 controllate, 9 contengono almeno un flusso falso: 8,7%. | Dipendenza dalle UI definite staticamente nei layout, ambiguità lessicale e di associazione spaziale, limiti della taint analysis e timeout dell'analisi. | Il 97,3% riguarda campi, non catene complete. L’8,7% è 9/104 app segnalate e controllate, non FP/(FP+TN). Privacy, non recupero generale di transazioni. DOI/arXiv non reperito: atti USENIX. |
| <a id="u6"></a>**U6** — [FlowCog: Context-aware Semantics Extraction and Analysis of Information Flow Leaks in Android Apps](https://www.usenix.org/conference/usenixsecurity18/presentation/pan). [Fonti](#src-u6). | Xiang Pan; Yinzhi Cao; Xuechao Du; Boyuan He; Gan Fang; Yan Chen.<br>**2018**. 27th USENIX Security Symposium, pp. 1669–1685.<br>**Stato:** Peer-reviewed; DOI/arXiv non reperito nelle fonti primarie consultate. | **Flusso:** Dati e operativo/UX: contesto UI associato a source–sink.<br>**Tecnica:** Ibrida; dipendenze, NLP e classificatori, senza LLM.<br>**Piattaforme:** Android; APK, codice dell'app, layout, testi e immagini UI. | Flussi source–sink annotati con contesto semantico proveniente dalle view e dai layout collegati tramite dipendenze di controllo e di dati. | 6.000 APK iniziali; FlowDroid termina su 1.885; 616 app producono 2.342 flussi annotati da tre persone. Training su 1.100 flussi e test su 1.242, con separazione per app. Le metriche di classificazione si riferiscono al test, non a tutte le 6.000 app. | Test su 1.242 flussi: P 90,1%, R 93,1%, accuracy 90,2%. Positivo = UI sufficiente a giustificare il flusso. Accuracy baseline keyword 73,5%; keyword+NLP semplice 80,9%. | Dipendenza dai flussi estratti da FlowDroid, bassa terminazione dell'analisi e assenza di analisi fra componenti; difficoltà della value analysis e dei dati o testi dinamici. | La classe positiva non indica malware o leak accertato, né prova l’intenzione dell’utente. DOI/arXiv non reperito. Usati i sei autori concordanti fra PDF e pagina; il BibTeX USENIX aggiunge Rui Shao. |
| <a id="u7"></a>**U7** — [A feature location approach for mapping application features extracted from crowd-based screencasts to source code](https://doi.org/10.1007/s10664-020-09874-z). [Fonti](#src-u7). | Parisa Moslehi; Bram Adams; Juergen Rilling.<br>**2020**. Empirical Software Engineering 25, pp. 4873–4926.<br>**Stato:** Peer-reviewed. | **Flusso:** Funzionale; localizzazione di feature visibili o narrate.<br>**Tecnica:** OCR, speech-to-text, topic modeling LDA e ranking; tracce dinamiche come riferimento.<br>**Piattaforme:** WordPress/PHP; Firefox/JavaScript e C/C++. | Classifiche di file o directory associati alla funzionalità mostrata nel video; non un grafo di esecuzione o una sequenza causale. | WordPress: 554 file PHP, 2 scenari, 10 screencast; valutati i primi 10 file. Firefox: 6 scenari, 89 screencast (somma Tab. 1), 7.433 directory; valutate le prime 100. Oracle Xdebug/Gecko; confronti anche con random e guided search. | Mediana reciprocal rank: WordPress 0,5 (Unique) e 1 (All); Firefox 0,2 alla granularità di directory. RR = 1/rango del primo elemento rilevante, non percentuale di file corretti. | Risultati scarsi a livello di file per Firefox, che motivano il passaggio alle directory; il campionamento del profiler può omettere chiamate; migliore accuratezza sul frontend che sul backend. | Localizzazione semantica, non prova di esecuzione o ordine UI→servizio→DB. Le metriche WordPress/Firefox hanno granularità diverse. |
| <a id="u8"></a>**U8** — [An Approach to Business Process Recovery from Source Code](https://doi.org/10.1109/ITNG.2015.64). [Fonti](#src-u8). | Luiz A. Pacini Rabelo; Antonio F. do Prado; Wanderley Lopes de Souza; Luís Ferreira Pires.<br>**2015**. ITNG 2015, pp. 361–366.<br>**Stato:** Peer-reviewed. | **Flusso:** Funzionale: recupero di attività e processo business.<br>**Tecnica:** Statica; MoDisco → KDM → regole euristiche → BPMN/jBPM.<br>**Piattaforme:** Java; caso di studio ProGradWeb. | BPMN derivato da KDM: chiamate → task e sequenze; condizioni → gateway; input/output → oggetti dati. Le classi GUI sono escluse e le classi database sono astratte come pool con flussi di comunicazione. | ProGradWeb: 60,9 KLOC, 7 package, 167 classi. 257 task recuperati: 204 rilevanti, 53 non rilevanti; 24 rilevanti mancanti. Baseline quantitativa diretta non verificata. | P = 204/257 = 0,79; R = 204/(204+24) = 0,89; F1 = 0,84 (arrotondamenti pubblicati). Unità: task del singolo caso. | Recupero incompleto delle attività rilevanti; manca una sezione sistematica sulle minacce alla validità. La conclusione afferma applicabilità a sistemi oltre 100 KLOC, ma il caso documentato ha 60,9 KLOC. | L’esclusione GUI impedisce una catena completa UI→dati. P/R dei task non misurano sequenze, condizioni o dati; l’affermazione oltre 100 KLOC non è un benchmark verificato. |

### 4.4 Decomposizione delle modifiche e unità di review

| ID, titolo e link verificato | Autori; anno; sede e stato | Flusso; tecnica; linguaggi e piattaforme | Rappresentazione del flusso | Valutazione e benchmark | Risultati principali misurati | Limiti dichiarati / restrizioni documentate | Nostra interpretazione e cautele |
|---|---|---|---|---|---|---|---|
| <a id="r1"></a>**R1** — [Helping Developers Help Themselves: Automatic Decomposition of Code Review Changesets](https://doi.org/10.1109/ICSE.2015.35). [Fonti](#src-r1). | Mike Barnett; Christian Bird; João Brunet; Shuvendu K. Lahiri.<br>**2015**. ICSE 2015.<br>**Stato:** Peer-reviewed. | **Flusso:** Funzionale; unità di review e impatto di modifiche<br>**Tecnica:** Statica (CLUSTERCHANGES)<br>**Piattaforme:** C#; Roslyn; changeset Bing/Office/Microsoft. | Grafo di regioni modificate collegate da def-use e use-use; componenti connesse come partizioni di review. | 1.000 changeset quantitativi; oltre 100 review analizzate manualmente; interviste a 20 sviluppatori di 13 progetti Microsoft. | Oltre il 40% dei changeset potenzialmente decomponibili; 18/20 sviluppatori positivi sull’uso futuro. Non misura una riduzione dei bug o del tempo di review. | Solo C#/Microsoft e piccolo campione utente; relazioni mancanti da XML/config, integrazione tra linguaggi, callback e cancellazioni; non può recuperare ogni intenzione condivisa. | Fornisce una base per review secondo dipendenze, ma non dimostra che ogni componente connessa sia un flusso end-to-end indipendente. |
| <a id="r2"></a>**R2** — [SmartCommit: A Graph-Based Interactive Assistant for Activity-Oriented Commits](https://doi.org/10.1145/3468264.3468551). [Fonti](#src-r2). | Bo Shen; Wei Zhang; Christian Kästner; Haiyan Zhao; Zhao Wei; Guangtai Liang; Zhi Jin.<br>**2021**. ESEC/FSE 2021.<br>**Stato:** Peer-reviewed; artefatti disponibili/riusabili. | **Flusso:** Funzionale; unità di review/commit<br>**Tecnica:** Statica + clustering/partizionamento interattivo (non LLM)<br>**Piattaforme:** Java/Git; collegamenti anche a modifiche non-code. | Grafo diretto, etichettato e pesato di diff hunk; archi dipendenze, refactoring, similarità, prossimità e altre relazioni. | 3.000 commit compositi sintetici da 10 progetti Java; studio sul campo con 83 ingegneri per 9 mesi, su 2 progetti industriali. | Rand Index mediano 71,00–83,50% sui dati sintetici; 74,70% e 70,45% sui due progetti industriali. Oltre il 60% dei gruppi accettato senza modifiche; il 90% dei commit elaborato in meno di 5 secondi. | Commit sintetici proxy di quelli reali; campione aziendale limitato, effetto novità e bias interviste. Richiede talvolta aggiustamenti umani. | Accuratezza significa concordanza di clustering dei diff hunk, non precisione dei flussi né correttezza semantica del commit. |

### 4.5 LLM, grafi di repository, retrieval e rilevamento di bug

| ID, titolo e link verificato | Autori; anno; sede e stato | Flusso; tecnica; linguaggi e piattaforme | Rappresentazione del flusso | Valutazione e benchmark | Risultati principali misurati | Limiti dichiarati / restrizioni documentate | Nostra interpretazione e cautele |
|---|---|---|---|---|---|---|---|
| <a id="l1"></a>**L1** — [RepoHyper: Search-Expand-Refine on Semantic Graphs for Repository-Level Code Completion](https://arxiv.org/abs/2403.06095). [Fonti](#src-l1). | Huy N. Phan; Hoang N. Phan; Tien N. Nguyen; Nghi D. Q. Bui.<br>**2025**. FORGE 2025; preprint arXiv dal 2024.<br>**Stato:** Peer-reviewed; sede verificata nel programma ufficiale. Risultati dalla versione arXiv v4 aperta. | **Flusso:** Tecnico/strutturale; contesto di repository<br>**Tecnica:** Grafo statico + retrieval, GNN/link prediction, LLM di completamento<br>**Piattaforme:** Python; RepoBench. | Repo-level Semantic Graph (RSG) di file, classi e funzioni; relazioni import/call/ownership/ereditarietà; ricerca semantica, espansione per percorsi e reranking. | RepoBench-R/C/P. Retrieval easy e hard: ciascuno con 12.000 casi XF-F e 6.000 XF-R; valutazione aggiuntiva di completamento cross-file. | Retrieval hard XF-F: acc@1 25,81% con RepoHyper + UniXcoder, contro 17,70% con UniXcoder; acc@3 49,51% contro 39,02%. Stesso encoder, Tabella 1. | Tipi di percorso selezionati manualmente; valutato solo RepoBench; costo dei CodeLLM e output non sempre conformi all'intento. | Il termine semantic graph indica struttura di repository e retrieval, non un modello completo di eventi, DB e semantica aziendale; la metrica è retrieval. |
| <a id="l2"></a>**L2** — [CodexGraph: Bridging Large Language Models and Code Repositories via Code Graph Databases](https://doi.org/10.18653/v1/2025.naacl-long.7). [Fonti](#src-l2). | Xiangyan Liu; Bo Lan; Zhiyuan Hu; Yang Liu; Zhicheng Zhang; Fei Wang; Michael Qizhe Shieh; Wenmeng Zhou.<br>**2025**. NAACL-HLT 2025.<br>**Stato:** Peer-reviewed; risultati dalla versione pubblicata. | **Flusso:** Tecnico/strutturale; comprensione repository<br>**Tecnica:** Estrazione statica + agenti LLM che formulano query Cypher<br>**Piattaforme:** Python; Neo4j. | Grafo di MODULE, CLASS, FUNCTION, METHOD, FIELD e GLOBAL_VARIABLE; relazioni CONTAINS, HAS_METHOD, HAS_FIELD, INHERITS e USES. USES collega funzioni/metodi a globali/campi, non chiamante e chiamato. Query Cypher multi-hop. | CrossCodeEval Lite Python, SWE-bench Lite, EvoCodeBench; GPT-4o, DeepSeek-CoderV2 e Qwen2-72B. | GPT-4o: CrossCodeEval exact match 27,90% contro 21,20% BM25; SWE-bench Lite 22,96% sia CodexGraph sia AutoCodeRover. Token medi su SWE: 102,25 mila contro 76,01 mila. Tabelle 1–2. | Solo Python; schema incompleto: archi function-call indicati come futura aggiunta; costo token superiore, possibili loop di generazione query; dipendenza dalla capacità del modello. | Il grafo pubblicato non include archi di chiamata. I benefici dipendono dal modello: con Qwen2 il tasso SWE è 1,95% contro 9,34% di AutoCodeRover. Non è una ricostruzione comportamentale end-to-end. |
| <a id="l3"></a>**L3** — [RepoGraph: Enhancing AI Software Engineering with Repository-level Code Graph](https://arxiv.org/abs/2410.14684). [Fonti](#src-l3). | Siru Ouyang; Wenhao Yu; Kaixin Ma; Zilin Xiao; Zhihan Zhang; Mengzhao Jia; Jiawei Han; Hongming Zhang; Dong Yu.<br>**2025**. ICLR 2025.<br>**Stato:** Peer-reviewed. | **Flusso:** Tecnico/strutturale; localizzazione e impatto modifiche<br>**Tecnica:** Grafo statico AST/tree-sitter + retrieval per agenti LLM<br>**Piattaforme:** Python nei principali esperimenti. | Nodi per righe di definizione/riferimento, archi invoke/contain; ego-graph per contesto locale e globale. | SWE-bench Lite: 300 issue, 4 framework (RAG, Agentless, AutoCodeRover, SWE-agent). Valutazione aggiuntiva CrossCodeEval. | Issue risolte: Agentless 27,33% → 29,67% (82 → 89 su 300); SWE-agent 18,33% → 20,33% (55 → 61). Costo medio Agentless: 0,34 → 0,39 dollari per issue. | Esperimenti principali su Python, SWE-bench Lite e modelli proprietari; costi limitano la scala; filtra librerie e dettagli esterni al repository. | Incrementi assoluti di 2–2,66 punti percentuali sui quattro framework; non misurano correttezza o completezza dei flussi. Il grafo è estratto dal codice, non generato liberamente dal modello. |
| <a id="l4"></a>**L4** — [IRIS: LLM-Assisted Static Analysis for Detecting Security Vulnerabilities](https://arxiv.org/abs/2405.17238). [Fonti](#src-l4). | Ziyang Li; Saikat Dutta; Mayur Naik.<br>**2025**. ICLR 2025.<br>**Stato:** Peer-reviewed. | **Flusso:** Dati; tecnico; vulnerabilità interprocedurali<br>**Tecnica:** LLM inferisce source/sink e filtra allarmi; CodeQL esegue taint analysis statica<br>**Piattaforme:** Java/Maven; CodeQL. | Specifiche di taint, cammini source→sink e contesto del repository. | CWE-Bench-Java: 120 CVE validate, 4 classi (CWE-22, CWE-78, CWE-79, CWE-94); confronto con CodeQL 2.15.3 e altri analizzatori e LLM. | GPT-4: 55/120 CVE rilevate contro 27/120 di CodeQL; recall 45,83% contro 22,50%; false discovery rate medio 84,82% contro 90,03%; F1 medio 0,177 contro 0,076. Quattro vulnerabilità prima sconosciute. | Molte vulnerabilità mancate; costo delle chiamate al modello; generalizzazione oltre Java non valutata. Il false discovery rate del benchmark è un limite superiore perché vulnerabilità non etichettate possono essere contate come falsi allarmi. | La riduzione di 5,21 punti del false discovery rate non significa un tasso residuo del 5%. Il risultato riguarda vulnerabilità da taint, non specifiche funzionali arbitrarie. |
| <a id="l5"></a>**L5** — [LLMxCPG: Context-Aware Vulnerability Detection Through Code Property Graph-Guided Large Language Models](https://arxiv.org/abs/2507.16585). [Fonti](#src-l5). | Ahmed Lekssays; Hamza Mouhcine; Khang Tran; Ting Yu; Issa Khalil.<br>**2025**. USENIX Security 2025.<br>**Stato:** Peer-reviewed. | **Flusso:** Dati; controllo; vulnerabilità multifunzione<br>**Tecnica:** Statica CPG/Joern + backward slicing + LLM fine-tuned<br>**Piattaforme:** C/C++; modelli DeepSeek-Coder, StarCoder, CodeLlama. | CPG con AST/CFG/dipendenze, slice focalizzate sui percorsi potenzialmente vulnerabili. | FormAI-v2, PrimeVul e SVEN; ReposVul: campione bilanciato di 120 esempi da 53 progetti; PKCO-25: 57 CVE del 2025 con patch, 114 esempi complessivi. | Riduzione del codice 67,84–90,93%; ReposVul accuracy 0,634 e F1 0,610; PKCO-25 accuracy 0,600 e F1 0,617; SVEN F1 0,7048 contro 0,55 di ReGVD. | Race/design error difficili da modellare; qualità/rumore dataset; generalizzazione a progetti complessi incompleta; selezione CVE anche per lunghezza del contesto. | La riduzione di codice non è direttamente una misura di risparmio token o assenza di perdita semantica. Non risolve invarianti aziendali arbitrari. |
| <a id="l6"></a>**L6** — [SWE-PRBench: Benchmarking AI Code Review Quality Against Pull Request Feedback](https://arxiv.org/abs/2603.26130). [Fonti](#src-l6). | Deepak Kumar.<br>**2026**. arXiv:2603.26130v1.<br>**Stato:** Preprint con valutazione; peer review non verificata. | **Flusso:** Contesto di review; ragionamento cross-file (benchmark)<br>**Tecnica:** LLM; confronto contesti diff/file/AST/import graph<br>**Piattaforme:** Python (69,1% del corpus), Go, TypeScript e altri. | Contesti testuali organizzati per diff, file e AST/import graph; commenti di review confrontati con problemi segnalati dagli sviluppatori. | Corpus di 350 PR, esperimenti su 100 PR (40/40/20 per difficoltà), 8 modelli e 3 configurazioni. Giudice GPT-5.2; validazione della rubrica su 30 classificazioni (κ = 0,75); secondo giudice su 10 PR e 127 commenti (κ = 0,616). | La configurazione A, detta diff-only ma comprensiva di task focus, riepilogo LLM e metadati, rileva il 15–31% dei problemi umani. Tutti gli 8 modelli peggiorano nel passaggio A → B → C nelle configurazioni provate. | Esperimento su 100/350 PR, sovrarappresentazione dei casi difficili, Python dominante, giudice LLM con validazione piccola; nessuna baseline umana diretta. Bias e contaminazione non esclusi. | Il confronto non dimostra causalmente che più contesto o il retrieval su grafo peggiorino sempre i risultati: cambiano rappresentazione, budget e selezione. L’attenzione diluita è un’interpretazione degli autori. |

### 4.6 Hardware, segnali, modelli e interrupt

| ID, titolo e link verificato | Autori; anno; sede e stato | Flusso; tecnica; linguaggi e piattaforme | Rappresentazione del flusso | Valutazione e benchmark | Risultati principali misurati | Limiti dichiarati / restrizioni documentate | Nostra interpretazione e cautele |
|---|---|---|---|---|---|---|---|
| <a id="h1"></a>**H1** — [A Hardware Design Language for Timing-Sensitive Information-Flow Security](https://doi.org/10.1145/2694344.2694372). [Fonti](#src-h1). | Danfeng Zhang; Yao Wang; G. Edward Suh; Andrew C. Myers.<br>**2015**. ASPLOS 2015, pp. 503–516.<br>**Stato:** Peer-reviewed. | **Flusso:** Informazione e sicurezza; influenze esplicite, implicite e temporali in hardware<br>**Tecnica:** Statica; sistema di tipi di sicurezza dipendenti, lattice e obblighi SMT risolti con Z3. Nessun LLM.<br>**Piattaforme:** SecVerilog, estensione di Verilog; processore MIPS e cache. | Etichette di sicurezza su variabili, registri e fili; semantica formale e obblighi di noninterferenza sensibile al tempo. Non produce un catalogo di cammini ordinati. | Processore MIPS a 5 stadi, 1.719 LOC esclusa la FPU, cache istruzioni e dati da 32 kB; benchmark MiBench e OpenSSL. Confronto fra baseline senza protezione, progetto protetto non verificato e progetto verificato. | Verifica in 2 s. Rispetto alla baseline senza protezione: area +0,67% e ritardo critico senza FPU +1,22%. Overhead medio OpenSSL: 8,8% con policy mista e 21,0% con policy coarse-grained. Sono costi del processore protetto, non tempi di estrazione dei flussi. | Annotazioni manuali per variabile, salvo l'etichetta predefinita; circuiti sincroni a frequenza fissa; attacchi fisici e analisi del consumo fuori dal modello. | È una base per verificare politiche sui flussi, ma non identifica automaticamente la catena sensore–driver–stato–attuatore. La prova di noninterferenza non equivale alla ricostruzione funzionale di un percorso. |
| <a id="h2"></a>**H2** — [CellIFT: Leveraging Cells for Scalable and Precise Dynamic Information Flow Tracking in RTL](https://www.usenix.org/conference/usenixsecurity22/presentation/solt). [Fonti](#src-h2). | Flavien Solt; Ben Gras; Kaveh Razavi.<br>**2022**. 31st USENIX Security Symposium, pp. 2549–2566.<br>**Stato:** Peer-reviewed; DOI/arXiv non reperito nelle fonti primarie consultate. | **Flusso:** Informazione in hardware; propagazione fra segnali, registri e memoria, incluse influenze microarchitetturali del software<br>**Tecnica:** Dinamica; IFT con logica di taint per bit, inserita a livello di macrocelle tramite pass Yosys. Nessun LLM.<br>**Piattaforme:** RTL Verilog/SystemVerilog; sv2v, Yosys, Verilator; emulazione FPGA. | Design strumentato con shadow logic e segnali di taint; tracce delle influenze su elementi interni e uscite. La taint è infrastruttura per l'analisi, non un cammino funzionale già ricostruito. | Cinque design RISC-V: Ibex, Rocket, PULPissimo, Ariane e BOOM; microbenchmark e benchmark RISC-V; confronto con GLIFT e, per le celle supportate, RTLIFT; ulteriori scenari di vulnerabilità. | Runtime di simulazione 21–61× più veloce di GLIFT senza perdita di precisione nella valutazione. GLIFT fallisce su Ariane per memoria e su BOOM dopo 96 h. Sintesi FPGA BOOM: CellIFT 5,93 h contro GLIFT 27,57 h; Ariane: CellIFT 4,57 h, GLIFT timeout a 48 h. | Il meccanismo richiede scenari o politiche per individuare vulnerabilità; non verifica genericamente la funzionalità né parametri hardcoded. Le memorie sono comunemente sostituite con modelli. | La completezza dei tipi di celle strumentabili non dimostra copertura completa delle esecuzioni o dei cammini sensore–attuatore. È una base promettente per un estrattore successivo di percorsi. |
| <a id="h3"></a>**H3** — [Isadora: automated information-flow property generation for hardware security verification](https://doi.org/10.1007/s13389-022-00306-w). [Fonti](#src-h3). | Calvin Deutschbein; Andres Meza; Francesco Restuccia; Ryan Kastner; Cynthia Sturton.<br>**2023**. Journal of Cryptographic Engineering 13, pp. 391–407; online dal 11 novembre 2022.<br>**Stato:** Peer-reviewed; versione estesa del lavoro ASHES 2021. | **Flusso:** Informazione e sicurezza in RTL; relazioni sorgente–sink e condizioni che consentono o impediscono il flusso<br>**Tecnica:** Dinamica; IFT Radix-S, simulazione QuestaSim e invariant mining con Daikon. Nessun LLM.<br>**Piattaforme:** RTL Verilog/SystemVerilog; testbench hardware. | Proprietà no-flow e conditional-flow con predicati; relazioni fra segnali e heatmap. Non ricostruisce integralmente i cammini intermedi. | Aker ACW: 1.940 LOC, 229 sorgenti/segnali, 598 cicli, 0,7 GB di tracce. PicoRV32: 3.140 LOC, 181 sorgenti/segnali, 1.099 cicli, 0,6 GB. OpenTitan: 1,8 milioni di LOC, ma solo 5 sorgenti e 365 segnali considerati, 3,6 miliardi di cicli e 140 GB. | Proprietà e tempi di mining (min:s): ACW 303 / 29:51; PicoRV32 153 / 15:09; OpenTitan 22 / 2:50. Generazione tracce: 9 h 33 min, 8 h 35 min, più giorni. Nove proprietà ACW coprono le asserzioni dei progettisti. Il 10% di falsi positivi riguarda 2 proprietà funzionali su 20 campionate. | Dipendenza dalla copertura del testbench; predicati spurii e imprecisioni nell’inizializzazione; scalabilità. OpenTitan usa cinque sorgenti tutte nel modulo `u_otp_ctrl`; i sink considerati sono nel modulo e nei suoi submoduli immediati. Esclude i clock e non completa il postprocessing dell’intero SoC. | Il caso OpenTitan non dimostra estrazione completa dei flussi su 1,8 milioni di LOC. I tempi non sono direttamente comparabili: OpenTitan usa hardware più veloce e una selezione diversa. Il 10% non è precision/recall dei cammini. |
| <a id="h4"></a>**H4** — [Information Flow Paths from RTL Traces](https://arxiv.org/abs/2606.13860). [Fonti](#src-h4). | Calvin Deutschbein; Owyn Wyatt.<br>**2026**. arXiv:2606.13860; pagina autore indica INTCEC 2026.<br>**Stato:** Preprint con valutazione; pagina autore conserva “Forthcoming”; pubblicazione definitiva negli atti e DOI IEEE non verificati. | **Flusso:** Cammini ordinati di informazione fra registri RTL<br>**Tecnica:** Dinamica; analisi dei tempi del primo taint su tracce IFT, ricostruzione di grafo e ricerca di cammini. Nessun LLM.<br>**Piattaforme:** Tracce VCD di design Verilog, strumentazione Radix; Python e strutture dati tabellari/sparse. | Grafo diretto con archi noti e candidati, matrice di adiacenza e alberi JSON; cammini temporalmente ordinati. Può operare sulle tracce IFT senza accesso diretto al sorgente. | PicoRV32: 232 registri, 3.049 LOC, testbench di 86 LOC e 2.201 cicli; 182 sorgenti con flusso non banale. Caso aggiuntivo con due access controller e tre periferiche. | Generazione delle tracce: 8 h 45 min. Costruzione grafo: 0,846 s; estrazione cammini: 0,445 s. Conteggi per lunghezze dichiarate 2/3/4/5: 151/130/71/59. Storage: VCD 64 MB, dataframe 525 MB, rappresentazione sparsa 419 kB. Baseline comparativa e precision/recall dei cammini non riportate. | Copertura limitata dalle tracce; alcuni archi diretti restano indistinguibili dai flussi indiretti; scalabilità da verificare su altri design. Il paper distingue archi confermati dall'algoritmo e candidati residui. | È il contributo più aderente alla definizione di percorso ordinato, ma non ricostruisce automaticamente il raccordo fra componenti fisici, firmware e configurazioni. I tempi paralleli prospettati sono stime, non misure sperimentali. |
| <a id="e1"></a>**E1** — [Verifying Data Secure Flow in AUTOSAR Models by Static Analysis](https://doi.org/10.5220/0006288707040713). [Fonti](#src-e1). | Cinzia Bernardeschi; Marco Di Natale; Gianluca Dini; Maurizio Palmieri.<br>**2017**. ForSE, nell'ICISSP 2017, pp. 704–713.<br>**Stato:** Peer-reviewed. | **Flusso:** Dipendenze funzionali e di sicurezza fra porte, runnable, variabili inter-runnable e comunicazioni AUTOSAR<br>**Tecnica:** Statica; interpretazione astratta del codice dei runnable, flussi espliciti/impliciti e punto fisso fra runnable. Nessun LLM.<br>**Piattaforme:** MISRA-C dei runnable; modello AUTOSAR annotato; API RTE. | Porte mappate a variabili, chiamate RTE a letture/scritture/invocazioni, IRV e globali a memoria astratta condivisa; dominio a insiemi di dipendenze, contesti e livelli di sicurezza. | Esempio di un componente con 3 runnable, 2 ingressi, 4 uscite e 4 IRV. Esempio architetturale con sensori/GPS, PathPlanning e Throttle. Non sono riportati corpus industriale, runtime o precision/recall. | out4, irv2 e irv4 dipendono dai due ingressi; irv1 dipende solo da in1. Rispetto all'approccio tutti-input→tutti-output, l'analisi evita la dipendenza spuria di irv1 da in2. Non è presentata una percentuale aggregata di accuratezza. | L'esecuzione astratta di tutti i rami può introdurre dipendenze spurie; gli indici degli array sono astratti. | È un raccordo esplicito fra modello e codice, ma la valutazione è piccola e l'output consiste in dipendenze, non in cammini ordinati comprendenti MMIO, interrupt, ECU e bus. L'aggettivo “dynamic” nelle conclusioni indica il confronto con approcci solo sintattici, non un monitoraggio runtime. |
| <a id="e2"></a>**E2** — [A Toolset for Simulink: Improving Software Engineering Practices in Development with Simulink](https://doi.org/10.5220/0005236100500061). [Fonti](#src-e2). | Vera Pantelic; Steven Postma; Mark Lawford; Alexandre Korobkine; Bennett Mackenzie; Jeff Ong; Marc Bender.<br>**2015**. MODELSWARD 2015, pp. 50–61.<br>**Stato:** Peer-reviewed. | **Flusso:** Dipendenze dati e controllo nei modelli Simulink, incluse comunicazioni nascoste<br>**Tecnica:** Statica; algoritmi MATLAB a punto fisso per Reach/Coreach e model slicing; estrazione delle interfacce con Signature. Nessun LLM.<br>**Piattaforme:** MATLAB/Simulink; implementazione MATLAB. | Interfacce esplicite dei sottosistemi, dipendenze in avanti/indietro e slice che preservano la gerarchia. Gestisce linee di segnale, Data Store, Goto/From e bus a granularità fine. | Modelli automotive industriali con media di 800 blocchi e profondità gerarchica circa 6; esempi pubblicati piccoli. Numero di modelli, precision/recall e confronto temporale con una baseline non riportati. | Reach/Coreach non supera 2 s sui modelli industriali utilizzati. Confronto concettuale con slicing precedente: trattamento delle dipendenze nascoste tramite Data Store e Goto/From e dei singoli flussi nei bus. | I modelli industriali sono proprietari e non vengono pubblicati. Auto Layout è ancora proof of concept; questo limite riguarda quel componente del toolset e non va attribuito automaticamente a Reach/Coreach. | Recupera dipendenze strutturali dal modello, non soltanto dati di simulazione. Una slice è un insieme o sottografo: da sola non certifica un ordine realizzabile di eventi attraverso campionamenti, firmware e hardware. |
| <a id="e3"></a>**E3** — [Data Races and Static Analysis for Interrupt-Driven Kernels](https://doi.org/10.1007/978-3-030-17184-1_25). [Fonti](#src-e3). | Nikita Chopra; Rekha Pai; Deepak D’Souza.<br>**2019**. ESOP 2019, LNCS 11423, pp. 697–723.<br>**Stato:** Peer-reviewed; open access. | **Flusso:** Flussi di controllo, sincronizzazione e stato condiviso fra task e interrupt<br>**Tecnica:** Statica; blocchi disgiunti, happens-before, lockset e domini numerici di interpretazione astratta. Nessun LLM.<br>**Piattaforme:** C del kernel FreeRTOS; frontend CIL e libreria Apron. | Sync-CFG: unione dei CFG di task/ISR con archi di sincronizzazione; insiemi di lock e invarianti numerici su regioni di variabili. | FreeRTOS 10.0.0: 49 API task/queue, oltre 3.500 LOC trasformate e 24 variabili. Analisi relazionale su circa 1.500 LOC astratte, 15 API prive di region race e 15 invarianti. | 64 coppie segnalate, 18 giudicate vere manualmente, in 3,91 s. Fra queste: 14 ritenute non-problemi dai progettisti, 2 benigne e 2 sulle liste ritardate corrette indipendentemente in v10.1.1. Intervalli: 11/15 invarianti in meno di 5 min; poliedri: 15/15 in circa 30 min; ottagoni: circa 20 min. | ISR non preemptibili nella semantica considerata; API semafori/mutex escluse. L'astrazione delle liste produce falsi positivi. Preemption a priorità e priority inheritance più generali richiedono ulteriore lavoro. | Fornisce una base semantica per modellare archi attraverso gli interrupt, ma non estrae catene sensore–attuatore. Le garanzie sugli invarianti dipendono dalle condizioni di assenza di race; i conteggi di race non misurano accuratezza dei cammini funzionali. |

### 4.7 Antecedenti fondativi e direttamente pertinenti

| ID, titolo e link verificato | Autori; anno; sede e stato | Flusso; tecnica; linguaggi e piattaforme | Rappresentazione del flusso | Valutazione e benchmark | Risultati principali misurati | Limiti dichiarati / restrizioni documentate | Nostra interpretazione e cautele |
|---|---|---|---|---|---|---|---|
| <a id="f1"></a>**F1** — [Interprocedural Slicing Using Dependence Graphs](https://doi.org/10.1145/77606.77608). [Fonti](#src-f1). | Susan Horwitz; Thomas Reps; David Binkley.<br>**1990**. ACM TOPLAS 12(1), 1990; prima versione PLDI 1988..<br>**Stato:** Fondativo peer-reviewed. | **Flusso:** Dati; controllo; interprocedurale<br>**Tecnica:** Statica; slicing context-sensitive<br>**Piattaforme:** Linguaggio imperativo procedurale formalizzato. | System Dependence Graph (SDG): dipendenze dati/controllo, parametri e summary edges; slicing con rispetto dei contesti di chiamata. | Contributo algoritmico/formale, esempi e analisi di complessità; non benchmark moderno. | Algoritmo di slicing interprocedurale con summary edges. P/R empiriche: non applicabili. | Formalismo e criterio di slicing ristretto a variabile definita/usata nel punto; non descrive framework, HTTP, DB, eventi moderni. | Fondamento per selezionare le porzioni pertinenti: raggiungibilità generica non basta a rispettare call/return. Uno slice non coincide con un'unica sequenza eseguibile. |
| <a id="f2"></a>**F2** — [Modeling and Discovering Vulnerabilities with Code Property Graphs](https://doi.org/10.1109/SP.2014.44). [Fonti](#src-f2). | Fabian Yamaguchi; Nico Golde; Daniel Arp; Konrad Rieck.<br>**2014**. IEEE Symposium on Security and Privacy, 2014.<br>**Stato:** Fondativo peer-reviewed. | **Flusso:** Dati; controllo; pattern di vulnerabilità<br>**Tecnica:** Statica; query su grafo<br>**Piattaforme:** C; Linux kernel; Joern. | Code Property Graph: combinazione di AST, CFG e PDG, interrogabile tramite attraversamenti del grafo. | Analisi vulnerabilità note e nuove nel Linux kernel. | 18 vulnerabilità prima sconosciute identificate. | Implementazione originale senza analisi interprocedurale completa; solo potenziali vulnerabilità, runtime/race non modellati. | Le capacità dei CPG moderni non vanno attribuite al prototipo del 2014. Combinare più grafi non fornisce automaticamente la semantica delle comunicazioni fra servizi. |
| <a id="f3"></a>**F3** — [GUI code tracing through direct program interaction](https://doi.org/10.1002/smr.1650). [Fonti](#src-f3). | André L. Santos.<br>**2014**. Journal of Software: Evolution and Process 26(6), pp. 552–568.<br>**Stato:** Peer-reviewed; antecedente fondativo pre-2015. | **Flusso:** Operativo/UX: widget visibile → istruzioni del programma.<br>**Tecnica:** Dinamica; strumentazione e tracciamento dell’interazione diretta (GUITA).<br>**Piattaforme:** Java; SWT; AspectJ; Eclipse. | Tracce e timeline delle istruzioni relative alla UI, con navigazione ai punti corrispondenti del codice sorgente. | Sei studenti MSc; tre programmi e due attività di manutenzione per programma. Text Editor: 1.642 LOC; Deinonychus: 4.134 LOC; Feed N'Read: 24.367 LOC. Studio distinto dell'overhead su una demo SWT con oltre 1.000 widget. | Tempi medi strumento/controllo, nell'ordine dei tre programmi: 7,5/6,4 minuti; 4,2/12,2 minuti; 5,5/21,0 minuti. Speed-up riportati: 0,9×, 2,9× e 3,8×; nel primo programma lo strumento è più lento. Sulla demo SWT, overhead riportato nell'ordine del 30–40% per la memoria e del 5–15% per la CPU. | Campione di studenti piccolo e generalizzabilità limitata; alcuni menu non intercettabili; widget istanziati all'interno di framework richiedono disponibilità del relativo codice. | Collega il widget al codice, senza recuperare workflow completi o effetti remoti. Anno bibliografico 2014; intestazioni di lavorazione 2013 nella copia autore. |
| <a id="f4"></a>**F4** — [FlowDroid: Precise Context, Flow, Field, Object-sensitive and Lifecycle-aware Taint Analysis for Android Apps](https://doi.org/10.1145/2594291.2594299). [Fonti](#src-f4). | Steven Arzt; Siegfried Rasthofer; Christian Fritz; Eric Bodden; Alexandre Bartel; Jacques Klein; Yves Le Traon; Damien Octeau; Patrick McDaniel.<br>**2014**. PLDI 2014, pp. 259–269.<br>**Stato:** Peer-reviewed; fondativo precedente al 2015. | **Flusso:** Taint source-to-sink intrapplicazione Android; lifecycle e callback.<br>**Tecnica:** Statica: IFDS forward taint e backward alias on-demand; dummyMain per modellare lifecycle/callback; ricostruzione dei percorsi.<br>**Piattaforme:** Android Dalvik/Java e Jimple; manifest e layout XML; Java/J2EE con entrypoint manuali. | ICFG, access path e grafo di propagazione dei dati; sensibilità a contesto, flusso, campo e oggetto. | DroidBench 1.0: 39 app; denominatore dei leak attesi 28. Baseline IBM AppScan Source 8.7 e Fortify SCA 5.14. Anche SecuriBench Micro con esclusioni e app Google Play/VirusShare. | DroidBench: FlowDroid 26 TP, 4 FP, 2 FN; precision 86% e recall 93% riportati (26/30 = 86,67%; 26/28 = 92,86%). AppScan: 14 TP, 5 FP, 14 FN; Fortify: 17 TP, 4 FP, 11 FN. SecuriBench nel perimetro valutato: 117/121 leak veri trovati e 9 FP. | Nel 2014 invio Intent trattato come sink e ricezione come source; collegamento ICC preciso futuro. Array/list index imprecisi; native approssimati; reflection costante; thread, implicit flows e sanitization fuori scope. | Fondativo precedente al 2015: non presentarlo come risoluzione inter-app end-to-end già completa. 39 app non è il denominatore del recall; conservare distinti valori pubblicati e derivati. |

<a id="percorsi-lettura"></a>

## 5. Percorsi di lettura per i sei tipi di flusso

Per ogni tipo sono indicati **cinque lavori prioritari**, con una motivazione. La scelta privilegia complementarità e aderenza alle domande, non una graduatoria di accuratezza fra metriche diverse. Tecniche ricorrenti, problemi aperti e uso dei dataset sono una **nostra sintesi**. Per disponibilità e vincoli, consultare anche il [catalogo degli artefatti](#artefatti).

### 5.1 Flusso dati

- **[Vamsa (D1)](#d1)**: ruoli semantici e provenienza delle colonne.
- **[WebSlice (C3)](#c3)**: collega PHP, SQL, HTML e JavaScript.
- **[CLOTHO (D3)](#d3)**: aggiunge dipendenze e ordine delle transazioni.
- **[SLiCE (D2)](#d2)**: valuta gli LLM sulla lineage di trasformazioni e aggregazioni.
- **[BolaRay (C6)](#c6)**: collega colonne, identità e controlli di autorizzazione.

**Tecniche ricorrenti.** Slicing avanti/indietro, alias e points-to; modelli di API e query; lineage a colonne; vincoli su transazioni; estrazione strutturata LLM.

**Problemi ancora aperti.** Identità di riga e versione, tenant, unità e granularità delle aggregazioni; SQL dinamico/ORM; letture e scritture distribuite. La correttezza semantica richiede una proprietà o un oracolo oltre al cammino.

**Benchmark e dataset da considerare.**

- CLOTHO/OLTP-Bench: [Kiarahmani/CLOTHO](https://github.com/Kiarahmani/CLOTHO)
- BolaRay: [BolaRay-d/BolaRay](https://github.com/BolaRay-d/BolaRay)
- Vamsa: corpus dichiarato nel paper, link attuale non accessibile. SLiCE: rilascio pubblico NV.

### 5.2 Flusso funzionale

- **[Rabelo et al. (U8)](#u8)**: recupera attività e BPMN da Java.
- **[Moslehi et al. (U7)](#u7)**: collega feature visibili negli screencast al codice.
- **[CLUSTERCHANGES (R1)](#r1)**: separa review seguendo dipendenze.
- **[SmartCommit (R2)](#r2)**: raggruppa modifiche per attività.
- **[RepoGraph (L3)](#l3)**: usa il grafo per localizzazione e riparazione.

**Tecniche ricorrenti.** Feature/concept location; retrieval testuale; KDM→BPMN; slicing; clustering di modifiche con dipendenze e similarità.

**Problemi ancora aperti.** Intenzione aziendale e confini delle feature spesso non sono espliciti nel codice. Clustering e ranking non certificano un percorso funzionale. Manca una misura comune della completezza delle funzionalità.

**Benchmark e dataset da considerare.**

- SmartCommit: 3.000 commit sintetici da 10 progetti Java; artefatto citato nel paper.
- RepoGraph/SWE-bench Lite: [ozyyshr/RepoGraph](https://github.com/ozyyshr/RepoGraph)
- [U7](#u7): WordPress/Firefox e screencast; pacchetto originale NV.

### 5.3 Flusso tecnico

- **[Micans (C7)](#c7)**: DI, endpoint, RPC e messaging con payload.
- **[Jasmine (C4)](#c4)**: recupera le chiamate nascoste da Spring DI/AOP.
- **[IccTA (C1)](#c1)**: concatena il taint attraverso componenti Android.
- **[IC3 (C2)](#c2)**: risolve messaggi Intent/URI e destinazioni.
- **[Code2DFD (C5)](#c5)**: recupera connessioni e configurazioni a livello architetturale.

**Tecniche ricorrenti.** Modelli del framework; propagazione di costanti e stringhe; matching route/metodo HTTP; binding broker/topic/queue; trasformazione delle chiamate implicite; punti fissi tra analisi.

**Problemi ancora aperti.** Deserializzazione, reflection, discovery dinamico, deployment multipli, framework non modellati e sistemi polyglot. Le connessioni architetturali non dimostrano il passaggio del singolo campo o della stessa riga.

**Benchmark e dataset da considerare.**

- microSecEnD: [tuhh-softsec/microSecEnD](https://github.com/tuhh-softsec/microSecEnD)
- Micans: [DOI 10.5281/zenodo.15050505](https://doi.org/10.5281/zenodo.15050505) (artifact citato; download NV).
- DroidBench: [secure-software-engineering/DroidBench](https://github.com/secure-software-engineering/DroidBench) ; DroidBench nelle versioni usate da [C1](#c1)/[F4](#f4); ICC-Bench nella valutazione di [C1](#c1).
- Jasmine: Spring microbenchmarks citati in [C4](#c4).

### 5.4 Flusso logico e controllo

- **[SDG (F1)](#f1)**: conserva dipendenze di dati/controllo e contesti di chiamata.
- **[WTG (U1)](#u1)**: ordina callback, eventi e operazioni sullo stack delle finestre.
- **[CLOTHO (D3)](#d3)**: genera schedule che espongono anomalie.
- **[Chopra et al. (E3)](#e3)**: modella interrupt e sincronizzazione con sync-CFG.
- **[Toolset Simulink (E2)](#e2)**: include dipendenze di controllo e flussi nascosti.

**Tecniche ricorrenti.** CFG/SDG e summary edges; macchine a stati; lifecycle e stack; happens-before; interpretazione astratta; SMT/model checking; slicing sui modelli.

**Problemi ancora aperti.** Fattibilità dei cammini, esplosione degli stati, asincronia, cancellazioni, retry e interrupt. Un percorso nel grafo può combinare eventi incompatibili; una traccia non copre i percorsi non eseguiti.

**Benchmark e dataset da considerare.**

- CLOTHO/OLTP-Bench e FreeRTOS 10.0.0 ([E3](#e3)).
- Reach/Coreach: [McSCert/Reach-Coreach](https://github.com/McSCert/Reach-Coreach) (link attribuito al progetto).
- Corpus automotive [E2](#e2) proprietario; corpus WTG storico, disponibilità NV.

### 5.5 Flusso operativo e ux

- **[WTG (U1)](#u1)**: navigazione con semantica di finestre e callback.
- **[SUPOR (U5)](#u5)**: campo di input→variabile→taint.
- **[FlowCog (U6)](#u6)**: mette il flusso dati in relazione con il contesto UI.
- **[StoryDistiller (U3)](#u3)**: storyboard con navigazione e informazioni d’ingresso.
- **[SceneDroid (U4)](#u4)**: stati UI più fini delle sole activity.

**Tecniche ricorrenti.** Parsing dei layout, ID dei widget, binding e slicing; graph di finestre/activity/scene; esplorazione dinamica; OCR/NLP; correlazione fra testo visibile e codice.

**Problemi ancora aperti.** Login e stato remoto, componenti UI dinamici, viste personalizzate, frammenti e app non native. I grafi della GUI non equivalgono ai journey realmente seguiti dagli utenti; questi richiedono osservazioni d’uso.

**Benchmark e dataset da considerare.**

- SceneDroid: [SceneDroid/SceneDroid](https://github.com/SceneDroid/SceneDroid) (codice e dati sperimentali).
- StoryDroid/StoryDistiller: corpus descritti nei paper; disponibilità completa NV.
- SUPOR/FlowCog: APK e annotazioni storiche, rilascio completo NV.

### 5.6 Flusso hardware e embedded

- **[CellIFT (H2)](#h2)**: motore di information-flow tracking per RTL.
- **[Isadora (H3)](#h3)**: ricava relazioni di flusso e condizioni.
- **[RTL Paths (H4)](#h4)**: ricostruisce esplicitamente cammini ordinati.
- **[AUTOSAR (E1)](#e1)**: collega modello, porte, runnable MISRA-C e RTE.
- **[Interrupt-driven kernels (E3)](#e3)**: cattura dipendenze via ISR e stato condiviso.

**Tecniche ricorrenti.** IFT a livello di bit/cella; tracce VCD; mining di invarianti; tipi di sicurezza e SMT (H1); interpretazione astratta del codice e dei modelli.

**Problemi ancora aperti.** Raccordo sensore→MMIO→driver/ISR→runnable→attuatore, bus/ECU e temporalità multirate. Copertura del testbench e proprietà spurie. Nessun benchmark unificato di tutta questa catena nei lavori verificati.

**Benchmark e dataset da considerare.**

- CellIFT: [comsec-group/cellift-meta](https://github.com/comsec-group/cellift-meta)
- Isadora: [cd-public/Isadora_soc](https://github.com/cd-public/Isadora_soc)
- PicoRV32, Ibex, Rocket, PULPissimo, Ariane/CVA6, BOOM; FreeRTOS.
- AUTOSAR [E1](#e1): solo esempio, tool/dataset NV.

<a id="collegamenti-indiretti"></a>

## 6. Collegare i componenti quando manca una chiamata diretta

Ricostruire un flusso significa spiegare come un effetto possa attraversare i confini del programma: quale implementazione riceve una chiamata, quale endpoint interpreta una richiesta, quale consumatore legge un messaggio e quale operazione osserva un dato persistito. Il riferimento sintattico al destinatario può essere assente, distribuito nella configurazione oppure costruito a runtime. Il grafo delle chiamate è quindi una parte della rappresentazione necessaria.

La letteratura selezionata affronta raccordi diversi. [IC3](#c2) ricostruisce valori e destinazioni della comunicazione Android; [IccTA](#c1) usa collegamenti fra componenti per propagare informazioni sensibili. [Jasmine](#c4) rende analizzabili meccanismi Spring; [Micans](#c7) integra la modellazione del framework con comunicazioni fra microservizi. [Code2DFD](#c5) ricostruisce invece una vista architetturale con connessioni e annotazioni. Questi contributi permettono di distinguere il recupero di un destinatario dalla ricostruzione di ciò che gli viene trasferito.

### Matrice dei raccordi e delle evidenze

La matrice seguente è una **sintesi interpretativa** dei lavori, non una classificazione sperimentale proposta da uno dei paper. La colonna finale indica ciò che occorre ancora stabilire prima di attribuire al collegamento un significato end-to-end.

| Raccordo | Evidenza da collegare | Contributi pertinenti e capacità documentata | Questione ancora da risolvere |
|---|---|---|---|
| Alias e memoria | Riferimenti, oggetti astratti, campi, parametri e ritorni | [FlowDroid](#f4) combina taint e alias analysis; [Micans](#c7) usa points-to anche per collegare comunicazioni fra servizi. | Due riferimenti possono denotare lo stesso oggetto senza riferirsi allo stesso campo, valore o istante. |
| Dependency injection e framework | Tipo richiesto, bean, annotazioni, XML, proxy ed entrypoint | [Jasmine](#c4) modella DI e AOP; [Micans](#c7) integra parte di questi raccordi nell’analisi inter-servizio. | Quale istanza e configurazione sono attive? La compatibilità di tipo non identifica necessariamente il bean corretto. |
| HTTP e pagine web | Destinazione, metodo, route, parametri, form e ritorni | [WebSlice](#c3) collega pagine PHP, form e dipendenze cross-language; [Micans](#c7) raccorda RPC e flussi di valori nel perimetro Java valutato. | Il campo inviato deve corrispondere a quello letto, considerando trasformazioni e condizioni; una route compatibile non basta. |
| Code di messaggi ed eventi | Producer, destinazione, binding, routing e consumer | [Code2DFD](#c5) comprende connessioni Kafka/RabbitMQ; [Micans](#c7) collega anche valori nelle comunicazioni RabbitMQ/RocketMQ valutate. | Identità del messaggio, versione dello schema, duplicazione, ordine e condizioni di consumo richiedono evidenze ulteriori. |
| Database e persistenza | Query, colonne, chiavi, predicati e transazioni | [WebSlice](#c3) copre letture SQL→PHP; [BolaRay](#c6) collega relazioni DB e autorizzazione; [CLOTHO](#d3) ragiona su dipendenze transazionali e visibilità. | Condividere tabella o colonna non stabilisce che una lettura osservi il valore della scrittura considerata. |

Le differenze di granularità sono sostanziali. Un arco servizio→database localizza una dipendenza architetturale; un legame parametro→colonna descrive una trasformazione più precisa; una relazione fra operazioni e versioni persistite aggiunge una dimensione temporale. Non è corretto trasferire l’accuratezza misurata al primo livello agli altri. In particolare, il supporto Kafka di [Code2DFD](#c5) non dimostra lineage del payload fino alle righe del database; [WebSlice](#c3) non implementa il ciclo completo INSERT/UPDATE→SELECT.

### Comporre gli archi senza cancellare le incertezze

**Proposta operativa originale.** Un sistema di ricostruzione dovrebbe conservare, per ogni arco, almeno il tipo di relazione, la granularità, l’evidenza nel codice o nella configurazione e le condizioni necessarie alla sua attivazione. Dovrebbe inoltre distinguere un collegamento possibile nell’astrazione statica, un trasferimento di valori analizzato e un comportamento osservato in una specifica esecuzione. Sono informazioni complementari, con limiti differenti.

La composizione va verificata sul confine condiviso. Se un producer costruisce `customerId`, una serializzazione lo rinomina e il consumer legge `account.owner`, occorre spiegare la trasformazione che rende compatibili i due accessi. Collegare soltanto il nome della coda lascia aperta questa domanda. Analogamente, una route HTTP e un metodo possono individuare un handler, mentre il collegamento fra corpo della richiesta e parametro dipende dal binding adottato.

**Esempio didattico inventato.** Un servizio seleziona tramite DI un client di pagamento, invia una richiesta HTTP e pubblica un evento di ordine pagato. Il destinatario HTTP cambia fra due configurazioni, mentre il consumer legge solo una versione dell’evento. Una rappresentazione che unisse tutte le configurazioni potrebbe mostrare un percorso composto da segmenti che non coesistono. Il rimedio proposto è conservare condizioni di configurazione e contratti sui dati lungo la composizione, evidenziando i punti non risolti.

L’assenza di un arco estratto dovrebbe quindi essere accompagnata dalla copertura del relativo estrattore. Una tecnologia non supportata, una stringa non risolta o un callback sconosciuto lasciano una lacuna nell’analisi. Trattare automaticamente tale lacuna come assenza di comportamento trasformerebbe un limite dello strumento in una conclusione sul sistema. Questa è una **deduzione metodologica** dai limiti dichiarati di [IC3](#c2), [Jasmine](#c4) e [Micans](#c7).

<a id="unita-review"></a>

## 7. Costruire unità coerenti di review mediante slice e grafi

### Dal file modificato alla domanda da verificare

La coerenza di una review dipende dalla proprietà che il revisore deve valutare. “Il totale è calcolato correttamente”, “l’utente può modificare soltanto i propri oggetti” e “la modifica conserva la compatibilità del messaggio” richiedono contesti diversi, anche quando coinvolgono lo stesso file. Partire dai file resta utile per localizzare il cambiamento, ma non determina da solo l’unità di ragionamento.

Lo [slicing interprocedurale](#f1) fornisce una base per selezionare istruzioni pertinenti a un criterio rispettando i contesti di chiamata. Una slice resta un insieme o sottografo di dipendenze: può comprendere alternative e sovra-approssimazioni, senza descrivere un’unica sequenza eseguibile. [WebSlice](#c3) estende il ragionamento attraverso linguaggi e pagine, con i limiti di fattibilità e copertura specificati nella sua scheda.

I lavori sulla decomposizione delle modifiche affrontano un obiettivo vicino, ma distinto. [CLUSTERCHANGES](#r1) usa relazioni fra regioni modificate per proporre partizioni di review; [SmartCommit](#r2) combina dipendenze e ulteriori relazioni fra diff hunk, mantenendo l’interazione umana. Le valutazioni riguardano decomposizione, concordanza dei gruppi e utilità. Non dimostrano che ciascun gruppo costituisca un flusso eseguibile completo o una modifica semanticamente indipendente.

### Una procedura proposta per delimitare la review

**Proposta operativa originale.** La preparazione di una review può articolarsi in quattro passaggi, usando il grafo come evidenza navigabile:

1. **Formulare una domanda verificabile.** Collegare il cambiamento a un effetto osservabile: dato restituito, aggiornamento persistito, evento pubblicato o decisione di autorizzazione.
2. **Espandere a ritroso.** Cercare input, condizioni, configurazioni e trasformazioni da cui dipende l’effetto. Il codice invariato può contenere presupposti decisivi.
3. **Espandere in avanti.** Identificare lettori, consumer ed effetti successivi che possono essere influenzati dalla modifica, inclusi i passaggi tramite persistenza.
4. **Dichiarare i confini.** Per ogni tratto escluso, registrare il contratto assunto e il motivo dell’esclusione. Per ogni tratto irrisolto, mostrare la domanda ancora aperta.

Questa procedura è una proposta di utilizzo delle rappresentazioni studiate; la sua efficacia non è misurata dai paper selezionati. Il risultato atteso sarebbe un insieme motivato di porzioni di codice, configurazioni e verifiche, accompagnato dalle dipendenze che ne giustificano l’inclusione.

La profondità dell’espansione dovrebbe dipendere dall’incertezza e dalla proprietà. Per una rinomina interna può bastare controllare gli utilizzatori del simbolo; per un cambio di significato di un campo persistito servono anche lettori invariati, dati già presenti e compatibilità delle versioni. Un limite uniforme di pochi salti nel grafo non distingue questi casi. È un criterio progettuale proposto, non una soglia validata sperimentalmente.

### Confini sovrapposti e codice condiviso

**Esempio didattico inventato.** Una modifica introduce uno sconto, aggiorna il totale dell’ordine e aggiunge il valore al messaggio usato dal servizio di fatturazione. Il calcolo compare nella review del prezzo; la serializzazione compare nella review del contratto dell’evento; il consumer compare nella review della fattura. Costringere ogni istruzione in un solo gruppo potrebbe separare una trasformazione dai suoi presupposti.

Una soluzione proposta è consentire sovrapposizioni esplicite. Il medesimo frammento può essere richiamato da più unità, indicando quale obbligo viene controllato in ciascuna. La duplicazione della vista non richiede duplicazione del lavoro: un controllo già svolto può essere riutilizzato quando ipotesi e versione coincidono. Una libreria comune, invece, non dovrebbe fondere automaticamente tutte le unità solo perché rende connesso il grafo.

Per stabilire se questa impostazione aiuti, una futura valutazione dovrebbe misurare errori individuati, dipendenze rilevanti omesse, tempo e accordo sui confini. Ridurre righe o numero di gruppi sarebbe soltanto un indicatore intermedio. Questa distinzione evita di usare i risultati di [SmartCommit](#r2) e [CLUSTERCHANGES](#r1) come prove di una riduzione dei bug end-to-end che quei lavori non hanno misurato.

<a id="bug-writer-reader"></a>

## 8. Individuare bug fra chi scrive e chi legge i dati

### Identità del dato, granularità e significato

Un collegamento writer–reader è utile quando chiarisce che cosa viene prodotto e a quali condizioni un altro componente lo interpreta. La coincidenza del nome di tabella o colonna è un indizio iniziale. Per collegare operazioni specifiche occorre considerare chiavi, filtri, trasformazioni, partizioni logiche e versione del dato. Per valutarne la correttezza occorre inoltre conoscere la proprietà attesa.

La ricerca selezionata fornisce contributi a livelli diversi: [Vamsa](#d1) ricostruisce provenance di colonne nelle pipeline studiate; [BolaRay](#c6) inferisce relazioni DB utili all’autorizzazione; [CLOTHO](#d3) modella dipendenze fra operazioni transazionali e cerca esecuzioni anomale. Non sono tre misure intercambiabili della medesima nozione di lineage. La provenienza di una colonna non prova che una sua aggregazione abbia il significato richiesto dal processo aziendale.

**Esempio didattico inventato.** Un job scrive `revenue` per negozio e mese, mentre un servizio la legge come ricavo giornaliero del singolo punto vendita. Tabella, colonna e tipo numerico possono corrispondere; l’errore è nella granularità temporale. Se il job aggrega tutti i tenant e il reader applica soltanto un filtro sul negozio, il problema riguarda anche la partizione logica. Un grafo che conserva soltanto i nomi dei campi non rende evidente nessuna delle due differenze.

**Proposta operativa originale.** Al lineage andrebbero affiancate proprietà del valore: unità di misura, granularità, chiavi di raggruppamento, filtri, trattamento dei null, finestra temporale e popolazione di riferimento. Alcune informazioni potrebbero essere ricavate dal codice; altre richiederebbero contratti o chiarimenti umani. Il sistema dovrebbe separare ciò che ha dedotto da ciò che è stato assunto, evitando di presentare un nome suggestivo come una specifica.

### Stato derivato e aggiornamenti parziali

Uno stato derivato rende il raccordo più complesso: cache, contatori, totali materializzati e proiezioni di eventi dipendono da altri valori e da una politica di aggiornamento. La domanda diventa se il reader osservi una rappresentazione coerente con la versione dei dati di origine che il processo gli consente di usare.

**Esempio didattico inventato.** Il servizio ordini modifica le righe e il totale; il servizio spedizioni legge una proiezione aggiornata da eventi. Una proiezione temporaneamente precedente può essere accettabile per una schermata informativa, ma incompatibile con l’obbligo di non spedire un ordine annullato. Il medesimo ritardo assume quindi significati diversi secondo l’effetto che abilita.

Una possibile specifica dovrebbe dichiarare quale stato è autorevole, quando la proiezione deve convergere e quali azioni richiedono una verifica aggiornata. Per consumatori di eventi servirebbero inoltre regole su duplicati, ordine e versioni: applicare due volte un incremento non equivale a ricevere due aggiornamenti distinti. Queste sono **proposte di proprietà da verificare**, non capacità attribuite all’estrazione delle connessioni di [Code2DFD](#c5) o al taint inter-servizio di [Micans](#c7).

### Concorrenza e proprietà necessarie per parlare di bug

[CLOTHO](#d3) mostra perché l’ordine e la visibilità delle operazioni siano parte del problema: una ricostruzione delle dipendenze può essere usata per cercare anomalie e produrre test, entro i limiti dell’analisi. Il passaggio successivo è stabilire quali anomalie violino un requisito funzionale. La scheda distingue infatti le anomalie riprodotte dai bug di business, e i requisiti identificati dagli autori da quelli che il sistema sintetizzerebbe autonomamente.

**Proposta operativa originale.** Per valutare un sospetto bug writer–reader conviene esplicitare quattro elementi: una proprietà, le operazioni che possono violarla, le condizioni di esecuzione e un’evidenza riproducibile o un obbligo di verifica ancora aperto. Proprietà possibili sono unicità, conservazione di un totale, autorizzazione dell’operazione, validità di una transizione di stato o aggiornamento entro una finestra ammessa. Sono esempi di specifiche, non un catalogo esaustivo di bug rilevabili dagli strumenti esaminati.

[BolaRay](#c6) offre un caso concreto di questo passaggio: usa modelli di autorizzazione derivati dalle relazioni DB per individuare controlli mancanti, nel proprio perimetro PHP/SQL. I suoi risultati non autorizzano a inferire la verifica di tutte le regole aziendali. Analogamente, i flussi simulati della valutazione di [Micans](#c7) misurano una capacità di analisi, senza costituire vulnerabilità reali scoperte.

Nel rapporto di review proposto, un collegamento ricostruito, un percorso candidato, un’esecuzione riprodotta e una violazione confermata dovrebbero rimanere categorie esplicite. Il revisore potrebbe così vedere quale parte dell’argomentazione è sostenuta dal codice, quale da un test e quale dalla specifica funzionale, concentrando il lavoro sul passaggio ancora necessario per decidere.

<a id="ui-codice-dati"></a>

## 9. Dall'interfaccia ai dati: che cosa significa ricostruire un flusso

La domanda «quale codice produce questo elemento e che cosa succede quando lo uso?» contiene due ricerche complementari. La prima parte dall'informazione visibile e risale alle sue cause: **schermo → binding → stato → dato**. La seconda parte da un evento e segue le sue conseguenze: **azione → handler → trasformazioni → effetti**. La nostra sintesi propone di mantenerle entrambe, perché conoscere il gestore di un pulsante non spiega necessariamente il valore visualizzato accanto, e conoscere la provenienza del valore non identifica tutte le operazioni attivate dal pulsante. I lavori selezionati verificano parti di queste catene, con granularità differenti; non documentano una soluzione unica per qualunque stack applicativo. [U1](#u1), [U3](#u3), [U5](#u5), [U6](#u6), [F3](#f3)

### Schermo, binding e stato non sono identificatori intercambiabili

**Risultati documentati.** SUPOR associa campi di input a variabili del programma usando informazioni del layout, identificatori dei widget e slicing, quindi integra tale associazione con l'analisi di propagazione verso destinazioni informative. È una delle evidenze più dirette del passaggio dall'elemento visibile al codice e ai dati. Il prototipo GUITA, invece, parte dall'interazione con un widget a runtime e consente di raggiungere le istruzioni che lo creano o modificano. StoryDroid e StoryDistiller aggiungono una rappresentazione navigabile delle schermate e riferimenti ai layout, alle activity e al codice. Sono collegamenti diversi: campo–variabile, widget–istruzione e schermata–componente non vanno trattati come la stessa relazione. [SUPOR, U5](#u5), [GUITA, F3](#f3), [StoryDroid, U2](#u2), [StoryDistiller, U3](#u3)

**Proposta di sintesi.** Per un elemento visualizzato, il modello dovrebbe distinguere almeno l'istanza UI, l'espressione che ne determina il contenuto, lo stato letto, la trasformazione applicata e la sorgente persistente o remota. Il binding è il collegamento concreto fra un valore del programma e una proprietà visuale; l'etichetta «Totale» offre un indizio semantico, ma non identifica da sola tabella, colonna o regola di calcolo. Occorre conservare anche chiavi dell'entità, condizioni di visibilità e versione del dato, quando recuperabili.

> **Esempio didattico, nostra deduzione.** Una schermata mostra «Totale ordine: 120». Il testo può provenire da una risposta del server, da un valore ricalcolato nel client oppure da una cache precedente. I tre casi producono la stessa immagine. Per spiegare il numero bisogna collegare l'elemento all'espressione di rendering e al valore effettivamente letto, quindi seguire la trasformazione fino alle righe pertinenti. Una semplice corrispondenza fra il nome `total` e una colonna del database non basta.

Per l'altra direzione, proponiamo di conservare il passaggio dall'evento al suo handler e alle scritture, distinguendo l'aggiornamento locale, l'invio di una richiesta e la conferma della persistenza. Un invio non prova che la transazione sia riuscita. Risposte asincrone, errori, annullamenti e retry possono modificare il percorso; il modello dovrebbe mostrare dove queste condizioni sono conosciute e dove restano mancanti.

FlowCog aggiunge una dimensione utile: collega flussi informativi al contesto semantico della UI per valutare se quel contesto li giustifichi. La sua classificazione non dimostra l'intenzione dell'utente né trasforma automaticamente un trasferimento in un errore. Analogamente, localizzare file a partire da uno screencast individua codice pertinente alla funzionalità descritta, senza dimostrare che ciascun file sia stato eseguito durante quella specifica azione. [FlowCog, U6](#u6), [Feature location da screencast, U7](#u7)

### Navigazione possibile, percorso fattibile e journey osservato

**Risultati documentati.** Il Window Transition Graph modella finestre, eventi, callback e operazioni sullo stack; il controllo dello stack elimina parte delle sequenze impossibili. SceneDroid distingue stati UI più fini della sola activity, includendo scene associate a fragment, dialoghi e menu. StoryDistiller mostra inoltre che raggiungere e renderizzare una schermata può richiedere input di attivazione, autenticazione o dati persistenti non disponibili. Questi risultati spiegano perché un elenco di pagine collegate sia una rappresentazione insufficiente. [WTG, U1](#u1), [SceneDroid, U4](#u4), [StoryDistiller, U3](#u3)

Nella nostra lettura, un arco statico esprime una possibilità ammessa dal modello; una traccia dinamica documenta un comportamento osservato sotto particolari condizioni. La concatenazione di archi non garantisce che esista uno stato iniziale compatibile con l'intera sequenza. Anche uno slice raccoglie istruzioni potenzialmente pertinenti e può contenere rami alternativi: non coincide con una singola esecuzione. [U1](#u1), [Fondamento dello slicing interprocedurale, F1](#f1)

> **Esempio didattico, nostra deduzione.** Il grafo contiene «Catalogo → Carrello» e «Carrello → Conferma». Il secondo passaggio richiede però una sessione autenticata e disponibilità dei prodotti. Aver trovato entrambi gli archi non dimostra che la concatenazione sia eseguibile per un utente anonimo o con un prodotto esaurito. Una traccia riuscita prova un caso concreto, non tutti i casi possibili.

Un *journey osservato* richiede inoltre informazioni sull'uso: successione degli eventi, stato iniziale rilevante, esito e contesto della sessione. Le sequenze prodotte da un esploratore automatico sono evidenza di esplorazione; non descrivono necessariamente i percorsi scelti dalle persone. Come proposta, conviene annotare separatamente archi estratti, archi osservati e percorsi riprodotti, senza convertire il numero di scene o transizioni recuperate in una misura di soddisfazione o di comportamento degli utenti. [U3](#u3), [U4](#u4)

### Trasferimento a React e store reattivi: ipotesi da valutare

La validazione GUI del corpus riguarda soprattutto Android nativo e Java/SWT. WebSlice offre un precedente per collegare PHP, SQL, HTML e JavaScript, ma presenta limiti espliciti su AJAX e sul recupero del ciclo completo di letture e scritture SQL. Non costituisce una validazione del comportamento di un frontend React moderno. [F3](#f3), [U1](#u1), [U2](#u2), [U3](#u3), [U4](#u4), [WebSlice, C3](#c3)

> **Esempio didattico, proposta non validata dal corpus.** In un'applicazione React ipotetica, il pulsante «Salva indirizzo» invoca un handler che aggiorna uno store e avvia una richiesta. Un altro componente legge lo store e mostra subito l'indirizzo aggiornato; una risposta negativa ripristina il valore precedente. Ricostruire soltanto handler e chiamata HTTP perderebbe il cambiamento anticipato della schermata e il suo successivo ripristino.

Per questo esempio proponiamo relazioni distinte fra componente e binding, lettura e scrittura dello stato, richiesta e risposta, stato temporaneo e persistente. Sarebbe necessario identificare i writer alternativi e le condizioni che rendono visibile una versione del valore. Il nodo da seguire non sarebbe soltanto la funzione chiamata, ma anche lo stato condiviso che collega componenti diversi. È un trasferimento metodologico da sottoporre a valutazione: la ricerca raccolta non misura quanto bene tale modello gestisca store reattivi, cache client, aggiornamenti ottimistici o concorrenza fra risposte.

<a id="contributo-llm"></a>

## 10. Quale contributo aggiungono gli LLM

I lavori selezionati suggeriscono quattro ruoli distinti: interpretare la semantica, recuperare contesto, interrogare strutture del codice e proporre specifiche per un analizzatore. Le metriche di questi ruoli restano separate: migliorare il completamento o risolvere più issue non misura automaticamente la completezza del grafo dei flussi. [RepoHyper, L1](#l1), [CodexGraph, L2](#l2), [RepoGraph, L3](#l3), [IRIS, L4](#l4)

**Interpretazione semantica.** Schema Lineage valuta l'estrazione strutturata di sorgenti, trasformazioni e aggregazioni. Il miglioramento con esempi e tracce di ragionamento preparate da esperti documenta un beneficio del contesto fornito. Il punteggio SLiCE, tuttavia, combina corrispondenze strutturali e testuali; non dimostra equivalenza eseguibile. Applicare questo ruolo alle etichette UI, proponendo che «disponibilità» corrisponda a una certa proprietà, sarebbe una nostra estensione: il collegamento proposto dovrebbe essere controllato sul codice. [Schema Lineage, D2](#d2)

**Recupero e selezione.** RepoHyper combina ricerca semantica, espansione nel grafo e affinamento del contesto; RepoGraph fornisce strutture del repository ad agenti di localizzazione e riparazione. In questi casi il grafo viene estratto dal codice e orienta la ricerca. Il modello può selezionare evidenze pertinenti, ma non bisogna attribuire agli incrementi nei benchmark una prova di ricostruzione dell'intero comportamento applicativo. [L1](#l1), [L3](#l3)

**Interrogazione.** CodexGraph consente agli agenti di formulare query Cypher su entità e relazioni del repository. Una precisazione è decisiva: nella versione NAACL analizzata non ci sono archi di chiamata fra funzioni. La relazione `USES` collega funzioni o metodi a variabili globali o campi. Una query può quindi attraversare la struttura presente, ma non ricavare automaticamente una catena di chiamate assente dallo schema. I risultati dipendono anche dal modello utilizzato e dal costo dell'interazione. [CodexGraph, L2](#l2)

**Specifiche source–sink.** IRIS usa l'LLM per inferire sorgenti e destinazioni rilevanti e per filtrare allarmi; CodeQL esegue l'analisi statica di taint. La separazione dei compiti è sostanziale: la proposta semantica alimenta il motore che calcola le dipendenze, senza dimostrare da sola la fattibilità dei percorsi. Restano vulnerabilità mancate e allarmi da esaminare. LLMxCPG segue una combinazione diversa, selezionando contesto tramite CPG e slicing per la classificazione di vulnerabilità. Nessuno dei due risultati autorizza a concludere che un LLM riconosca invarianti aziendali arbitrarie dal solo codice. [IRIS, L4](#l4), [LLMxCPG, L5](#l5)

La nostra proposta operativa è accompagnare ogni interpretazione con il simbolo, la configurazione o il percorso analitico che la sostiene. Quando l'evidenza manca, il sistema dovrebbe presentare un candidato o una lacuna. Una spiegazione linguistica coerente non dimostra la fattibilità dell'esecuzione descritta.

<a id="contesto-review"></a>

## 11. Contesto per la review: selezione, budget e fallimenti

Per organizzare una review, proponiamo di partire da una modifica, un evento o un campo e combinare le cause pertinenti con gli effetti possibili. Il contesto dovrebbe includere reader, writer, condizioni e contratti necessari a valutare quella modifica, rendendo visibili le dipendenze che attraversano il confine. Una componente connessa troppo grande può diventare inutilizzabile; gruppi distinti possono invece condividere stato e non essere indipendenti.

CLUSTERCHANGES e SmartCommit documentano il valore delle dipendenze e del raggruppamento delle modifiche, ma misurano decomposizione, concordanza dei gruppi e accettazione, non una riduzione generale dei bug sfuggiti alla review. Questa differenza determina quale evidenza manca per valutare una review organizzata per flussi. [CLUSTERCHANGES, R1](#r1), [SmartCommit, R2](#r2)

SWE-PRBench, preprint con valutazione, osserva un peggioramento passando alle configurazioni di contesto più estese sperimentate. La configurazione chiamata *diff-only* include anche riepilogo, task focus e metadati; cambiano composizione e budget del contesto. Inoltre, l'esperimento usa un campione del corpus e un giudice LLM con validazione contenuta. Il risultato segnala un rischio da studiare, ma non prova che più contesto, o qualunque retrieval su grafo, peggiori sempre la review. [SWE-PRBench, L6](#l6)

**Protocollo proposto, non risultato già validato.** Un confronto utile dovrebbe controllare almeno quattro aspetti:

1. **Budget.** Confrontare strategie a parità di token disponibili e registrare token effettivi, chiamate, latenza e costo. Tenere costanti istruzioni e riepiloghi. Una riduzione delle righe di codice non equivale direttamente a risparmio di token, come richiede di precisare la valutazione di LLMxCPG. [L5](#l5)
2. **Ablation.** Rimuovere separatamente espansione nel grafo, ranking semantico, condizioni di esecuzione e specifiche inferite, mantenendo stabile il resto. Variare poi il budget indipendentemente dalla strategia, per distinguere qualità della selezione e quantità del contesto.
3. **Esito.** Misurare problemi confermati, problemi mancati, allarmi infondati e utilità per i revisori. Un rilievo corretto assente dai commenti storici non dovrebbe diventare automaticamente un falso positivo; occorre un controllo indipendente, coerentemente con l'incompletezza del riferimento discussa da SWE-PRBench. [L6](#l6)
4. **Fallimenti.** Contare analisi non terminate, query invalide, loop dell'agente, simboli irrisolti e contesti troncati. Riportare i denominatori iniziali e quelli effettivamente valutati, evitando che l'esclusione dei casi difficili sembri un miglioramento.

Infine, proponiamo di separare nel rapporto gli errori di estrazione, selezione e interpretazione. Se manca un writer, il limite è nel modello recuperato; se il writer esiste ma non arriva al revisore, è nella selezione; se viene mostrato ma interpretato male, è nel ragionamento. Questa distinzione rende il fallimento correggibile e collega ogni miglioramento alla parte del sistema che lo ha prodotto.

<a id="rappresentazione-proposta"></a>

## 12. Una rappresentazione comune dei flussi e delle prove

Questa sezione sviluppa **una nostra sintesi metodologica**, non uno standard adottato dai lavori esaminati né un sistema già implementato e valutato. La proposta serve a confrontare risultati eterogenei senza attribuire a un analizzatore capacità che non dimostra. Riprende il valore dei grafi di dipendenza e delle rappresentazioni integrate [F1](#f1), [F2](#f2), ma richiede che ogni collegamento conservi significato, granularità, contesto e prova di origine. L’obiettivo è rispondere a una domanda precisa: quale percorso collega una sorgente a un effetto, e che cosa autorizza a considerarlo possibile, osservato o ancora ipotetico?

### Dipendenza, slice, cammino fattibile e traccia

Occorre mantenere distinti quattro oggetti.

| Oggetto | Significato nella rappresentazione proposta | Informazione che non garantisce da solo |
|---|---|---|
| Dipendenza | Una relazione esplicita di influenza, uso, controllo o comunicazione | Quali componenti intermedi siano attraversati in una stessa esecuzione |
| Slice | La porzione selezionata rispetto a un criterio, con determinate dipendenze | Una sequenza unica, ordinata e realizzabile |
| Cammino fattibile | Una sequenza compatibile con dati, guardie e vincoli del modello | Che sia stata osservata o che il modello copra l’ambiente reale |
| Traccia | Una successione finita di eventi osservati in una specifica esecuzione | Che eventi vicini siano causalmente collegati o che flussi assenti siano impossibili |

Una dipendenza conservativa può essere corretta come risposta alla domanda «questo valore potrebbe contribuire?» pur generando un cammino irrealizzabile quando viene combinata con altre dipendenze. Analogamente, lo slicing interprocedurale richiede rispetto dei contesti di chiamata: una semplice visita del grafo può connettere chiamate e ritorni incompatibili [F1](#f1). Proponiamo quindi di distinguere il **cammino strutturale candidato** dal cammino per cui è stato trovato un testimone di fattibilità.

Per un candidato, la fattibilità dovrebbe significare che esistono input, versioni dello stato e un ordinamento degli eventi compatibili con tutti i vincoli accumulati. Se il risolutore non termina, il risultato resta sconosciuto. Se un modello astratto ammette comportamenti aggiuntivi, anche una soluzione soddisfacibile può richiedere concretizzazione. Una traccia con taint o relazioni di lettura/scrittura esplicite offre una prova più specifica della sola coincidenza temporale; conserva comunque la portata di quella esecuzione.

### Un multigrafo tipizzato con provenienza degli archi

Proponiamo un multigrafo diretto:

$$
G=(V,E,\tau_V,\tau_E,\alpha,\Pi),
$$

dove le funzioni $\tau_V$ e $\tau_E$ assegnano tipi a nodi e archi, $\alpha$ registra attributi semantici e $\Pi$ collega gli elementi alle prove. Più archi possono unire gli stessi nodi: un valore può contribuire sia al dato prodotto sia alla condizione che ne autorizza la scrittura. Collassare queste relazioni cancellerebbe una distinzione utile durante la verifica.

I nodi rappresenterebbero operazioni, valori, oggetti persistenti, interfacce ed eventi. Gli archi distinguerebbero almeno dipendenza dati, controllo, selezione dell’indirizzo, chiamata/ritorno, comunicazione, sincronizzazione e corrispondenza fra rappresentazioni. Un collegamento fra una porta AUTOSAR e una chiamata RTE è diverso da un trasferimento fra due registri. I lavori su AUTOSAR e IFT mostrano due punti di osservazione utili, ma il raccordo fra essi richiede una relazione esplicita [E1](#e1), [H2](#h2).

Per operazioni con più ingressi, come un’aggregazione, è preferibile introdurre un nodo operazione con ingressi nominati. Un insieme di archi indipendenti non esprime necessariamente che gli ingressi debbano contribuire congiuntamente. Ogni arco dovrebbe inoltre riportare versione dell’artefatto, localizzazione, metodo di estrazione, assunzioni ambientali e precisione disponibile. La provenienza da un file non prova automaticamente la correttezza semantica del collegamento: rende controllabile la spiegazione.

### Granularità dei dati, identità e tempo

La granularità deve essere un attributo interrogabile, non una proprietà implicita dell’intero strumento. Un percorso potrebbe essere preciso per campo nello strato applicativo e aggregato per intera tabella nello strato dati. La granularità a colonna, presente nei lavori sulla provenance, non determina automaticamente quali righe contribuiscano a un risultato [D1](#d1).

| Dimensione | Distinzione da conservare | Rischio della fusione |
|---|---|---|
| Dato, oggetto e campo | Variabile, istanza e membro effettivamente letto | Attribuire a tutti i campi l’influenza di uno solo |
| Tabella, colonna e riga | Schema, attributo, chiave o predicato di selezione | Confondere provenienza dello schema con contributo dei record |
| Versione dello stato | Scrittura produttrice e lettura consumatrice | Collegare una lettura a uno stato già sovrascritto |
| Evento e tempo | Attivazione, task/ISR, ciclo RTL e dominio di clock | Unire eventi appartenenti a campioni o esecuzioni diversi |

Proponiamo identità composte da simbolo, contesto e versione, con riferimenti opzionali a campione, messaggio o transazione. Dove l’identità non sia disponibile, la perdita di precisione dovrebbe restare visibile. Un filtro può mantenere il contributo di campioni precedenti; una coda può separare produzione e consumo; un interrupt può aggiornare lo stato fra due istruzioni apparentemente consecutive.

Il tempo richiede sia valori misurati sia relazioni d’ordine. Timestamp di domini differenti non sono confrontabili senza una corrispondenza dichiarata. Una relazione happens-before o un arco di sincronizzazione può essere informativa anche quando non esiste un orologio globale affidabile. Il sync-CFG offre un riferimento per ragionare su questi collegamenti negli specifici modelli di interrupt studiati [E3](#e3).

### Un esempio JSON progettato per rendere controllabile una prova

Il seguente record è **un esempio sintetico progettato qui**: nomi, file e righe sono inventati; non è un formato standard dei paper. Rappresenta un’ipotesi di collegamento fra una lettura MMIO e un campione software, mantenendo esplicito ciò che manca.

```json
{
  "schema": "proposta.flow-evidence.v0",
  "example_only": true,
  "id": "edge_mmio_sample",
  "from": {
    "id": "ADC_DATA",
    "kind": "mmio_register",
    "version": "conversion_k"
  },
  "to": {
    "id": "sample_buffer.value",
    "kind": "software_field",
    "version": "write_k"
  },
  "edge_type": "read_from",
  "guard": {
    "expression": "adc_ready && irq_enabled",
    "satisfiability": "unknown"
  },
  "granularity": {
    "source": "register",
    "destination": "field",
    "sample_identity": "k",
    "time_context": "ADC_ISR activation k"
  },
  "status": "hypothesized",
  "evidence": [
    {
      "kind": "source_location",
      "file": "example/drivers/adc.c",
      "line_start": 40,
      "line_end": 43,
      "revision": "example-revision"
    }
  ],
  "missing_evidence": [
    "board_config_to_register_mapping",
    "interrupt_delivery_model"
  ]
}
```

Nella proposta, `extracted` indicherebbe una relazione ricavata da sorgente, configurazione o modello mediante una regola identificata; `observed` richiederebbe un evento e un’esecuzione associati; `hypothesized` segnalerebbe un collegamento plausibile ancora privo della prova richiesta. Questi valori descrivono **l’origine della singola affermazione**, non livelli universali di verità. Una dipendenza estratta può essere conservativa; un arco osservato può non generalizzare.

Per lo stesso arco si potrebbero mantenere record distinti, uno statico e uno osservato, senza sovrascrivere la storia. Un eventuale punteggio di confidenza non dovrebbe sostituire assunzioni e prove: essere molto sicuri di un’ipotesi non la trasforma in osservazione.

### La catena sensore–MMIO–ISR–runnable–attuatore

Questa catena è un caso utile per verificare la proposta. Il sensore fisico dovrebbe essere collegato a un’interfaccia hardware tramite configurazione di scheda e periferica; il registro MMIO, alla lettura effettiva del driver; l’interrupt, alla sua abilitazione e al gestore; il campione, alla versione consumata dal runnable; il comando finale, alla scrittura e al canale dell’attuatore.

Ogni attraversamento richiede una prova diversa. Il sorgente può mostrare una lettura volatile senza identificare il dispositivo collegato. Una configurazione può nominare il gestore senza provare quando venga eseguito. Una dipendenza RTE può collegare porte e variabili senza identificare quale campione attraversi una coda. Un registro PWM aggiornato dimostra un comando digitale nel modello considerato, non l’effetto meccanico realmente ottenuto.

Proponiamo quindi una restituzione che permetta **interruzioni esplicite della catena**: tratto estratto, raccordo ipotizzato, tratto osservato. Il percorso non dovrebbe ricevere automaticamente lo stato del suo arco meglio documentato. Le semantiche di interrupt e i modelli delle memorie devono accompagnare la spiegazione. L’ambiguità fra cammini indiretti e archi diretti discussa nella ricostruzione da tracce RTL rende particolarmente importante conservare archi candidati residui [H4](#h4).

<a id="valutazione-proposta"></a>

## 13. Come valutare ricostruzione e utilità senza confondere le metriche

### Quattro unità di valutazione

Proponiamo quattro livelli separati: **archi, cammini, proprietà e utilità**. Un risultato può migliorare a un livello e peggiorare a un altro. Eliminare molti archi spurii può rimuovere anche un unico raccordo necessario a una catena critica; produrre numerose proprietà non dimostra che esse descrivano il requisito funzionale cercato. La distinzione è rilevante per interpretare mining di proprietà e controllo di politiche [H3](#h3), [H1](#h1).

Per archi o cammini, fissata l’unità $k$, proponiamo:

$$
P_k=\frac{TP_k}{TP_k+FP_k},\qquad
R_k=\frac{TP_k}{TP_k+FN_k}.
$$

I conteggi richiedono prima un criterio di corrispondenza: tipo dell’arco, direzione, identità dei nodi, contesto, granularità ed eventuale guardia. Le corrispondenze devono impedire che duplicati dello stesso risultato aumentino i veri positivi. Un denominatore nullo va riportato come non definito, con i conteggi, evitando convenzioni che migliorino artificialmente la media.

Per gli **archi**, distinguerei corrispondenza esatta e compatibilità a granularità più grossolana. Un arco corretto fra componenti non equivale a un arco corretto fra campi. Per i **cammini**, registrerei separatamente raggiungibilità sorgente–destinazione, correttezza della sequenza intermedia e disponibilità di un testimone fattibile. La corrispondenza degli estremi non dovrebbe contare come ricostruzione esatta.

### Ground truth, limiti della ricerca e proprietà

Il ground truth dovrebbe specificare se deriva da annotazione manuale, generatore controllato, prova formale o traccia. La traccia fornisce positivi osservati, ma normalmente non giustifica classificare come falsi tutti gli archi statici non esercitati. I casi non decidibili con l’oracolo disponibile devono restare «non classificati» e comparire nei risultati. Anche gli oracoli dinamici usati per comunicazioni fra servizi richiedono questa cautela [C7](#c7).

Con cicli e stato persistente, il numero di cammini può essere illimitato. Occorre dichiarare lunghezza massima, unrolling, numero di attivazioni e criterio di equivalenza. Distinguerei recall rispetto al ground truth entro questi limiti dalla copertura del sistema complessivo. La riproduzione di anomalie già individuate misura inoltre una capacità diversa dalla scoperta di tutte le anomalie possibili [D3](#d3).

Per le **proprietà**, valuterei soddisfazione o violazione rispetto a requisiti fissati indipendentemente, validità del controesempio, assunzioni necessarie e copertura delle classi di requisito. La classificazione «interessante per la sicurezza» non coincide con la verità della proprietà. Medie macro per progetto e micro sui conteggi dovrebbero essere presentate insieme quando le dimensioni dei progetti differiscono.

### Copertura, costo temporale e riproducibilità

La copertura dovrebbe avere denominatori espliciti. Una possibile misura operativa è:

$$
C_{output}=\frac{N_{input\ con\ risultato}}{N_{input\ ammissibili\ a\ priori}}.
$$

Timeout, crash e risultati vuoti devono rimanere nel rendiconto degli input ammessi. La precisione calcolata solo sui casi completati va accompagnata da questa copertura. Separerei inoltre copertura dei linguaggi/framework dichiarati, dei tipi di comunicazione, delle sorgenti e dei comportamenti esercitati. La copertura di rami o segnali strumentabili non va rinominata copertura di tutti gli stati possibili.

Per i costi, registrerei parsing, collegamento fra artefatti, risoluzione dei vincoli, generazione delle tracce ed estrazione dei percorsi. Il tempo complessivo misurato dall’inizio alla disponibilità del risultato è diverso dal solo tempo dell’ultima fase. In esecuzione parallela, somma dei tempi dei processi, tempo trascorso e risorse utilizzate devono essere distinti. Confrontare direttamente strumentazione, mining e ricostruzione ignorerebbe le diverse attività misurate da [H2](#h2), [H3](#h3) e [H4](#h4).

Proporrei distribuzioni dei tempi, mediana, quantili dichiarati, memoria massima, dimensione degli artefatti e frequenza dei timeout, insieme a hardware, cache, licenze e budget di parallelismo. Nessuna misura viene assegnata qui: sono elementi del protocollo da raccogliere.

### Artefatti riusabili e utilità per chi verifica

Gli artefatti CellIFT offrono design e infrastruttura sperimentale; i repository Isadora offrono tracce e output; le implementazioni Simulink permettono di studiare dipendenze e slicing [H2](#h2), [H3](#h3), [E2](#e2). Sono punti di partenza, non automaticamente dataset con ground truth di catene complete. Le tracce pubbliche non eliminano eventuali dipendenze proprietarie per rigenerarle; i modelli industriali non pubblicati non diventano riproducibili grazie alla disponibilità del tool.

Proponiamo di costruire casi controllati con sorgenti, configurazioni, stato e osservazioni versionati, affiancandoli a sistemi reali. Le modifiche introdotte per creare errori dovrebbero variare il raccordo semantico, non soltanto un nome: canale sbagliato, campione sovrascritto, condizione incompatibile, aggiornamento interrotto. I casi reali servirebbero a verificare quanto le assunzioni del laboratorio sopravvivano all’integrazione.

L’**utilità** richiede infine compiti concreti: localizzare l’origine di un comando, spiegare una dipendenza inattesa, valutare l’impatto di una modifica. Misurerei completamento corretto, tempo alla spiegazione verificata, interventi manuali e quota di archi senza prova sufficiente. Il risultato utile è una spiegazione controllabile, con raccordi mancanti visibili; il numero di nodi visualizzati o la plausibilità della descrizione testuale non bastano a dimostrarlo.

<a id="lacune-ricerca"></a>

## 14. Lacune e programma sperimentale suggerito

### 14.1 Che cosa resta aperto nel corpus verificato

Questa sezione esprime **la nostra valutazione comparativa**. «Aperto» significa che i lavori inclusi non forniscono una validazione sufficiente per la domanda formulata; non significa che nessun ricercatore abbia affrontato il tema. La rassegna ha copertura maggiore su Android, Java/Spring, sicurezza del flusso informativo e RTL, mentre copre meno direttamente frontend reattivi, process mining da log d'uso e sistemi polyglot con configurazioni di deployment complesse.

| Problema di ricerca | Che cosa offre il corpus | Quale prova aggiuntiva servirebbe |
|---|---|---|
| **Identità end-to-end del dato** | Provenance a colonne, modelli di comunicazione e dipendenze transazionali, in perimetri distinti. [D1](#d1), [C7](#c7), [D3](#d3) | Annotazioni che seguano lo stesso campo, record o aggregato attraverso serializzazioni, chiavi, filtri e versioni persistite. |
| **Semantica delle trasformazioni** | Ruoli nelle pipeline, estrazione LLM di lineage e inferenza di modelli specifici di autorizzazione. [D1](#d1), [D2](#d2), [C6](#c6) | Requisiti indipendenti su unità, granularità, popolazione e stato atteso; valutazione dei casi in cui il nome è plausibile ma il significato è errato. |
| **Composizione polyglot e configurazioni** | Raccordi web specifici e modelli di framework/microservizi nel perimetro studiato. [C3](#c3), [C4](#c4), [C7](#c7) | Sistemi con più linguaggi, configurazioni alternative, proxy, servizi scoperti a runtime e versioni incompatibili; misure per tipo di confine. |
| **UI reattiva fino alla persistenza** | Binding UI–variabile e modelli di navigazione, soprattutto Android. [U1](#u1), [U5](#u5), [U6](#u6) | Casi con store condivisi, cache, invalidazione, aggiornamenti ottimistici e risposta concorrente; oracoli sul valore effettivamente visualizzato. |
| **Unità di review semanticamente coerenti** | Partizioni dei cambiamenti e accettazione dei gruppi. [R1](#r1), [R2](#r2) | Compiti con bug indipendentemente confermati, controlli del contesto e revisori che verifichino proprietà, includendo codice invariato pertinente. |
| **LLM e fedeltà del flusso** | Retrieval, completion, issue solving, specifiche e classificazione di vulnerabilità. [L1](#l1), [L3](#l3), [L4](#l4), [L5](#l5) | Metriche sulla fedeltà dei singoli raccordi e sulle spiegazioni; separazione fra errori del grafo e interpretazioni aggiunte dal modello. |
| **Flussi temporali HW/SW completi** | IFT, mining di proprietà, cammini RTL, dipendenze AUTOSAR e semantica degli interrupt. [H2](#h2), [H3](#h3), [H4](#h4), [E1](#e1), [E3](#e3) | Un benchmark che unisca configurazione fisica, MMIO, ISR, stato software, runnable, bus e attuazione, con identità dei campioni. |
| **Journey effettivamente seguiti dagli utenti** | Grafi della GUI e percorsi esplorati o generati. [U2](#u2), [U3](#u3), [U4](#u4) | Eventi d'uso con sessioni e contesto, correlati alle versioni del codice; la navigabilità estratta non basta a misurare il comportamento umano. |

### 14.2 Un insieme iniziale di casi sperimentali

**Proposta originale da valutare.** Un benchmark iniziale dovrebbe privilegiare confini espliciti e verificabili prima di aumentare le dimensioni. Ogni caso dovrebbe contenere una versione corretta, una modifica che introduca una violazione documentata e una variante lecita apparentemente simile. Le varianti lecite sono necessarie per verificare se l'analizzatore riconosca la proprietà o segnali soltanto un pattern sospetto.

| Famiglia di caso | Informazioni da fornire | Violazione sintetica da introdurre | Variante lecita utile come controllo |
|---|---|---|---|
| UI e persistenza | Rendering, handler, store, endpoint, risposta, transazione. | La UI mantiene un valore ottimistico dopo un errore e lo presenta come confermato. | La UI mantiene una bozza esplicitamente non confermata, prevista dal requisito. |
| Writer–reader e granularità | Query, chiavi, filtri, trasformazioni e specifica dell'aggregato. | Un reader tratta un totale mensile come valore giornaliero. | Il reader applica una trasformazione dichiarata e verificabile della granularità. |
| Eventi e stato derivato | Producer, schema, consumer, policy di aggiornamento e duplicazione. | Un retry applica due volte un incremento non idempotente. | Il secondo messaggio rappresenta una seconda operazione distinta con identità propria. |
| Configurazione e DI | Profili, bean, endpoint e contratti per ogni ambiente. | Il percorso combina una configurazione client con un servizio incompatibile. | Due configurazioni mutuamente esclusive realizzano entrambe il contratto previsto. |
| Concorrenza e transazioni | Invarianti, modello di consistenza, schedule e dati iniziali. | Una lettura usa uno stato parzialmente aggiornato e viola l'invariante. | La lettura precedente è esplicitamente ammessa per un effetto non critico. |
| Hardware e campioni | Configurazione periferica, MMIO, ISR, buffering e periodicità. | Il runnable usa un campione sovrascritto o associato all'attivazione sbagliata. | Il requisito ammette l'ultimo campione disponibile e ne conserva l'identità. |

Questi esempi non sono nuovi bug scoperti né benchmark già pubblicati. Servono a rendere verificabile la differenza fra recuperare un collegamento e riconoscere la correttezza del comportamento. Il caso dovrebbe documentare una proprietà prima dell'esecuzione dello strumento, così da evitare di reinterpretare a posteriori ciò che lo strumento riesce a trovare.

### 14.3 Confronti e ablation suggeriti

Proponiamo di confrontare una base di relazioni sintattiche con estensioni successive: modelli del framework, collegamenti di configurazione, analisi di valori e dipendenze, evidenza dinamica e contributo semantico dell'LLM. Ogni estensione dovrebbe essere valutata sul confine che intende risolvere, mantenendo costanti gli altri elementi quando possibile. Una pipeline più grande può migliorare il risultato finale senza chiarire quale parte abbia prodotto il vantaggio.

Per l'LLM, il confronto dovrebbe includere lo stesso modello con contesto selezionato testualmente e con contesto selezionato dal grafo, controllando il budget. Un ulteriore esperimento dovrebbe fornire il grafo corretto annotato manualmente: se il risultato resta errato, il problema non può essere attribuito soltanto all'estrattore. In direzione opposta, interrogazioni deterministiche sul grafo permetterebbero di misurare quanto sia ottenibile senza interpretazione linguistica. Sono controlli progettati qui, non risultati dei paper.

Per i sistemi reali, proponiamo uno split per repository e, quando pertinente, per famiglia di framework. Una separazione casuale di frammenti dello stesso sistema può mantenere nel test convenzioni e strutture già incontrate. Revisioni, configurazioni, versioni dei modelli e prompt dovrebbero essere congelati; i casi che richiedono componenti esterni non disponibili dovrebbero restare documentati come esclusioni o risultati non classificabili.

Il rapporto sperimentale finale dovrebbe permettere di ricostruire l'argomento di ogni rilievo: **proprietà → sorgente → trasformazioni → raccordi → effetto → prova o incertezza**. Le metriche aggregate servirebbero a confrontare i metodi; i casi controllabili servirebbero a capire perché funzionino o falliscano.

<a id="artefatti"></a>

## 15. Dataset, strumenti e condizioni di riuso

**Come interpretare la disponibilità.** «Pagina/repository aperto» significa che la risorsa è stata consultabile durante la ricerca; non significa che dipendenze, build, dataset o esperimenti siano stati eseguiti. «Citato nel paper» significa che il collegamento è documentato dalla fonte, ma accesso e download possono restare NV. Gli URL storici non raggiunti non sono dichiarati definitivamente cessati. La data di riferimento resta l'11 novembre 2026.

Gli artefatti non sono intercambiabili: un benchmark di taint contiene sorgenti e sink; un corpus GUI contiene stati e navigazioni; un insieme di PR contiene problemi di review; un progetto RTL può offrire testbench e tracce. Per costruire un benchmark unificato occorrerebbero ulteriori annotazioni e raccordi. Questa è una nostra valutazione del loro impiego.

| Lavoro | Artefatto, disponibilità verificata e condizioni |
|---|---|
| [D1](#d1) | Corpus e ground truth indicati nel paper a [aka.ms/vamsa](https://aka.ms/vamsa) ; collegamento attuale non accessibile nella verifica. |
| [D2](#d2) | Benchmark descritto nel paper; release pubblica del corpus industriale non verificata. |
| [D3](#d3) | Tool, benchmark ed esperimenti: [Kiarahmani/CLOTHO](https://github.com/Kiarahmani/CLOTHO) (repository aperto). OLTP-Bench, inclusi TPC-C e SmallBank. |
| [C1](#c1) | Tool aperto: [lilicoding/soot-infoflow-android-iccta](https://github.com/lilicoding/soot-infoflow-android-iccta) ; artefatti autore: [lilicoding.github.io/artefacts.html](https://lilicoding.github.io/artefacts.html) . |
| [C2](#c2) | Pagina autore aperta: [docteau.github.io/tools.html](https://docteau.github.io/tools.html) ; rimanda a [siis.cse.psu.edu/ic3](http://siis.cse.psu.edu/ic3) , disponibilità attuale del download non verificata. |
| [C3](#c3) | URL citato nel paper: [home.engineering.iastate.edu/~hungnv/Research/WebSlice](http://home.engineering.iastate.edu/~hungnv/Research/WebSlice) ; disponibilità corrente non verificata. |
| [C4](#c4) | [SpringJasmine/Jasmine](https://github.com/SpringJasmine/Jasmine) (aperto); microbenchmark: [SpringJasmine/Spring-micro-benchmarks](https://github.com/SpringJasmine/Spring-micro-benchmarks) ; integrazione taint: [SpringJasmine/FlowDroid_Jasmine](https://github.com/SpringJasmine/FlowDroid_Jasmine) . |
| [C5](#c5) | Tool aperto: [tuhh-softsec/code2DFD](https://github.com/tuhh-softsec/code2DFD) ; dataset: [tuhh-softsec/microSecEnD](https://github.com/tuhh-softsec/microSecEnD) e DOI 10.5281/zenodo.7714926 . Repository del dataset microSecEnD aperto anche nella verifica finale. |
| [C6](#c6) | Tool e dataset aperti: [BolaRay-d/BolaRay](https://github.com/BolaRay-d/BolaRay) ; appendice dello studio: [BolaRay-d/BolaRay/blob/main/appendix-study.pdf](https://github.com/BolaRay-d/BolaRay/blob/main/appendix-study.pdf) . Repository aperto nella verifica finale. |
| [C7](#c7) | Artifact DOI verificato nella bibliografia: [DOI 10.5281/zenodo.15050505](https://doi.org/10.5281/zenodo.15050505) ; download non riuscito durante la verifica. |
| [C8](#c8) | Replication package aperto: [M3SOulu/EMSE2025SAR-Replication](https://github.com/M3SOulu/EMSE2025SAR-Replication) ; benchmark: [M3SOulu/EMSE2025SAR-Benchmarks](https://github.com/M3SOulu/EMSE2025SAR-Benchmarks) ; strumenti: [M3SOulu/EMSE2025SAR-Tools](https://github.com/M3SOulu/EMSE2025SAR-Tools) . |
| [U1](#u1) | Toolkit GATOR: [web.cse.ohio-state.edu/presto/software/gator/](http://web.cse.ohio-state.edu/presto/software/gator/) . URL storico citato nel paper; disponibilità attuale non verificata perché non raggiungibile durante la ricerca. |
| [U2](#u2) | [sites.google.com/view/storydroid/](https://sites.google.com/view/storydroid/) offre il benchmark di dieci app; disponibilità di un repository completo dello strumento non verificata. |
| [U3](#u3) | [sites.google.com/view/storydistiller/](https://sites.google.com/view/storydistiller/) verificato come pagina del progetto; download completo di strumento e dataset non verificato. Preprint verificato: [arXiv 2203.06420](https://arxiv.org/abs/2203.06420) . |
| [U4](#u4) | [SceneDroid/SceneDroid](https://github.com/SceneDroid/SceneDroid) verificato: cartelle sourcecode ed experimentaldata, licenza GPL-3.0. Repository SceneDroid aperto nella verifica finale. |
| [U5](#u5) | Tool SUPOR e vocabolario descritti nel paper; repository e dataset pubblico verificabile non reperiti nelle fonti consultate. |
| [U6](#u6) | [SocietyMaster/FlowCog](https://github.com/SocietyMaster/FlowCog) dichiarato open source nel paper e nella pagina ufficiale; apertura del repository non riuscita durante la ricerca, quindi disponibilità attuale non verificata. |
| [U7](#u7) | Archivi citati nel paper: [mcislab.github.io/publications/2020/emse_parisa/Firefox-File-Level-Analysis.zip](https://mcislab.github.io/publications/2020/emse_parisa/Firefox-File-Level-Analysis.zip) e [mcislab.github.io/publications/2020/emse_parisa/Firefox-Directory-Level-Analysis.zip](https://mcislab.github.io/publications/2020/emse_parisa/Firefox-Directory-Level-Analysis.zip) . URL verificati nel testo; download non provato. |
| [U8](#u8) | MoDisco, KDM e jBPM descritti; codice dello specifico prototipo e dataset replicabile non verificati. |
| [R1](#r1) | Corpus industriale non pubblico; prototipo di studio. |
| [R2](#r2) | Tool: [Symbolk/SmartCommitCore](https://github.com/Symbolk/SmartCommitCore) ; dati: [Symbolk/SmartCommitEvaluation-Viz](https://github.com/Symbolk/SmartCommitEvaluation-Viz) (link verificati nel paper; apertura del secondo non riuscita). Artefatti con badge FSE disponibili/riusabili. |
| [L1](#l1) | [FSoft-AI4Code/RepoHyper](https://github.com/FSoft-AI4Code/RepoHyper) (repository aperto; checkpoint e RSG RepoBench-R dichiarati disponibili). RepoBench. |
| [L2](#l2) | [modelscope/modelscope-agent/tree/master/apps/codexgraph_agent](https://github.com/modelscope/modelscope-agent/tree/master/apps/codexgraph_agent) ; benchmark pubblici. |
| [L3](#l3) | [ozyyshr/RepoGraph](https://github.com/ozyyshr/RepoGraph) (repository aperto); SWE-bench Lite e CrossCodeEval. |
| [L4](#l4) | Tool [iris-sast/iris](https://github.com/iris-sast/iris) ; dataset [iris-sast/CWE-Bench-Java](https://huggingface.co/datasets/iris-sast/CWE-Bench-Java) (entrambi aperti). |
| [L5](#l5) | Artefatto LLMxCPG indicato nella fonte ufficiale USENIX; FormAI/PrimeVul/ReposVul/SVEN. Non è stato verificato qui un download completo di tutti gli esperimenti e delle versioni dei dataset. |
| [L6](#l6) | [FoundryHQ-AI/swe-prbench](https://github.com/FoundryHQ-AI/swe-prbench) (repository aperto); dataset indicato a [foundry-ai/swe-prbench](https://huggingface.co/datasets/foundry-ai/swe-prbench) . |
| [H1](#h1) | Implementazione pubblica: [aferr/secverilog](https://github.com/aferr/secverilog). Dataset di cammini con ground truth non verificato. |
| [H2](#h2) | [comsec-group/cellift-meta](https://github.com/comsec-group/cellift-meta) contiene toolchain, benchmark, esperimenti e versioni congelate dei cinque design. Nel repository Ariane è denominato CVA6. Repository cellift-meta aperto nella verifica finale. |
| [H3](#h3) | [cd-public/Isadora](https://github.com/cd-public/Isadora) e [cd-public/Isadora_soc](https://github.com/cd-public/Isadora_soc) includono tracce VCD e output. Isadora_soc aperto nella verifica. Radix è proprietario: disponibilità delle tracce e rigenerazione sono condizioni diverse. |
| [H4](#h4) | Riusa VCD pubblici di [cd-public/Isadora](https://github.com/cd-public/Isadora). Il paper dichiara script GitHub, ma l'URL specifico del nuovo estrattore non è stato verificato. DOI arXiv verificato: 10.48550/arXiv.2606.13860. |
| [E1](#e1) | Repository dell’analizzatore e dataset dedicato non verificati. Il caso illustrativo è descritto nel paper; non è disponibile qui un benchmark industriale replicabile. |
| [E2](#e2) | [McSCert/Reach-Coreach](https://github.com/McSCert/Reach-Coreach), attestato dalla pagina MATLAB Central degli autori; [McSCert/Signature](https://github.com/McSCert/Signature). Corpus industriale non disponibile. |
| [E3](#e3) | Benchmark FreeRTOS 10.0.0, [freertos.org](https://freertos.org). Repository dedicato dell'analizzatore non verificato. |
| [F1](#f1) | Paper completo; Wisconsin Program-Slicing project (storico). |
| [F2](#f2) | Il paper descrive il prototipo Joern e l’analisi del Linux kernel. Un pacchetto congelato che riproduca integralmente gli esperimenti del 2014 non è stato verificato. |
| [F3](#f3) | Prototipo GUITA; repository attuale non verificato. Programmi del benchmark e link SourceForge descritti nella tabella I. |
| [F4](#f4) | Sito citato nel paper: [sseblog.ec-spride.de/tools/flowdroid/](http://sseblog.ec-spride.de/tools/flowdroid/) ; pagina autore: [blogs.uni-paderborn.de/sse/tools/flowdroid/](https://blogs.uni-paderborn.de/sse/tools/flowdroid/) . Disponibilità attuale del download non verificata. DroidBench aperto: [secure-software-engineering/DroidBench](https://github.com/secure-software-engineering/DroidBench) ; fissare la versione 1.0 per confrontare i risultati del 2014. |

<a id="fonti"></a>

## 16. Fonti primarie e punti del testo da controllare

I link seguenti individuano il testo o la pagina primaria usati per verificare le schede. Quando esistono più versioni, la versione che sostiene i numeri è specificata nella matrice o nel riferimento. Le risorse progettuali con disponibilità incerta restano nella [sezione 15](#artefatti), non vengono usate come prova di un risultato sperimentale. Non sono inclusi riferimenti non verificati per completare artificialmente la copertura tematica.

<a id="src-d1"></a>

### D1 — Fonti e localizzazione

[Scheda bibliografica e risultati](#d1) · [Link bibliografico principale](https://doi.org/10.1145/3394486.3403205).

- [Testo integrale PDF](https://www.weimo.de/files/pub/2020/2020-KDD-Vamsa.pdf)
- [Pagina autore o istituzionale (2)](https://www.microsoft.com/en-us/research/publication/vamsa-automated-provenance-tracking-in-data-science-scripts/)

**Dove controllare:** §§ 5–7; Tabelle 2–3; § 9 e Reproducibility

<a id="src-d2"></a>

### D2 — Fonti e localizzazione

[Scheda bibliografica e risultati](#d2) · [Link bibliografico principale](https://arxiv.org/abs/2508.07179).

- [Testo arXiv 2508.07179v1](https://arxiv.org/html/2508.07179v1)
- [Scheda arXiv 2508.07179](https://arxiv.org/abs/2508.07179)

**Dove controllare:** §§ 2,3,5; Tabelle 1–2

<a id="src-d3"></a>

### D3 — Fonti e localizzazione

[Scheda bibliografica e risultati](#d3) · [Link bibliografico principale](https://arxiv.org/abs/1908.05655).

- [Testo arXiv 1908.05655v1](https://arxiv.org/html/1908.05655v1)
- [Scheda arXiv 1908.05655](https://arxiv.org/abs/1908.05655)

**Dove controllare:** §§ 6–7; Tabelle 2–3

<a id="src-c1"></a>

### C1 — Fonti e localizzazione

[Scheda bibliografica e risultati](#c1) · [Link bibliografico principale](https://doi.org/10.1109/ICSE.2015.48).

- [Testo integrale PDF](https://www.bodden.de/pubs/lbb+15iccta.pdf)
- [Pagina autore o istituzionale (2)](https://research.monash.edu/en/publications/iccta-detecting-inter-component-privacy-leaks-in-android-apps/)

**Dove controllare:** Table III; risultati corpus; sezione sulle limitazioni.

<a id="src-c2"></a>

### C2 — Fonti e localizzazione

[Scheda bibliografica e risultati](#c2) · [Link bibliografico principale](https://doi.org/10.1109/ICSE.2015.30).

- [Testo integrale PDF](https://patrickmcdaniel.org/pubs/icse15b.pdf)
- [Pagina autore o istituzionale (2)](https://pure.psu.edu/en/publications/composite-constant-propagation-application-to-android-inter-compo/)

**Dove controllare:** Table I; confronto degli archi candidati con Epicc; tempi e limitazioni.

<a id="src-c3"></a>

### C3 — Fonti e localizzazione

[Scheda bibliografica e risultati](#c3) · [Link bibliografico principale](https://doi.org/10.1145/2786805.2786872).

- [Testo integrale PDF](https://www.cs.cmu.edu/~ckaestne/pdf/fse15_webslice.pdf)

**Dove controllare:** Tabelle delle applicazioni e delle slice; test di correttezza; limitazioni.

<a id="src-c4"></a>

### C4 — Fonti e localizzazione

[Scheda bibliografica e risultati](#c4) · [Link bibliografico principale](https://doi.org/10.1145/3551349.3556910).

- [Testo integrale PDF](https://weihang-wang.github.io/papers/ASE2022-Jasmine.pdf)

**Dove controllare:** Table V; esperimenti sul callgraph; limitazioni.

<a id="src-c5"></a>

### C5 — Fonti e localizzazione

[Scheda bibliografica e risultati](#c5) · [Link bibliografico principale](https://doi.org/10.1016/j.jss.2023.111722).

- [PDF arXiv 2304.12769](https://arxiv.org/pdf/2304.12769)
- [Pagina autore o istituzionale (2)](https://tore.tuhh.de/entities/publication/9e9162e6-4baa-4202-b007-84883526ec9a)
- [Scheda arXiv 2304.12769](https://arxiv.org/abs/2304.12769)

**Dove controllare:** Table 2 (tecnologie); Table 4 (TP/FP/FN); risultati dei tempi.

<a id="src-c6"></a>

### C6 — Fonti e localizzazione

[Scheda bibliografica e risultati](#c6) · [Link bibliografico principale](https://doi.org/10.1145/3658644.3690227).

- [Testo integrale PDF](https://leehaofeng.github.io/papers/2024-BolaRay.pdf)

**Dove controllare:** §5, Table 5; selezione dei casi noti; discussione SELECT/DAL; confronto Mace.

<a id="src-c7"></a>

### C7 — Fonti e localizzazione

[Scheda bibliografica e risultati](#c7) · [Link bibliografico principale](https://doi.org/10.1145/3728896).

- [Testo integrale PDF](https://zhangt2333.github.io/pdf/issta25.pdf)

**Dove controllare:** Table 2 RPC/MBC; tabelle callgraph e taint; limitazioni; riferimento artifact.

<a id="src-c8"></a>

### C8 — Fonti e localizzazione

[Scheda bibliografica e risultati](#c8) · [Link bibliografico principale](https://doi.org/10.1007/s10664-025-10686-2).

- [Pagina editore](https://link.springer.com/article/10.1007/s10664-025-10686-2)
- [Scheda arXiv 2412.08352](https://arxiv.org/abs/2412.08352)

**Dove controllare:** §2.3 dataset; §§4–5 risultati/combinazioni; §6 limitazioni.

<a id="src-u1"></a>

### U1 — Fonti e localizzazione

[Scheda bibliografica e risultati](#u1) · [Link bibliografico principale](https://doi.org/10.1109/ASE.2015.76).

- [Testo integrale PDF](https://lilicoding.github.io/SA3Repo/papers/2015_yang2015static2.pdf)

**Dove controllare:** Tabelle II–V: corpus, archi e test; discussione dei limiti; prima pagina per DOI.

<a id="src-u2"></a>

### U2 — Fonti e localizzazione

[Scheda bibliografica e risultati](#u2) · [Link bibliografico principale](https://doi.org/10.1109/ICSE.2019.00070).

- [Testo integrale PDF](https://lingling-fan.github.io/llfan_files/icse2019_storydroid.pdf)
- [Pagina autore o istituzionale (2)](https://research.monash.edu/en/publications/storydroid-automated-generation-of-storyboard-for-android-apps/)

**Dove controllare:** Valutazione su app costruite e reali; confronto con STOAT; studio utenti e discussione del rendering.

<a id="src-u3"></a>

### U3 — Fonti e localizzazione

[Scheda bibliografica e risultati](#u3) · [Link bibliografico principale](https://doi.org/10.1109/TSE.2022.3159548).

- [PDF arXiv 2203.06420](https://arxiv.org/pdf/2203.06420)
- [Scheda arXiv 2203.06420](https://arxiv.org/abs/2203.06420)
- [Pagina autore o istituzionale (3)](https://research.monash.edu/en/publications/automatically-distilling-storyboard-with-rich-features-for-androi/)

**Dove controllare:** §§5.1–5.2 per i risultati; §7 per i limiti. I valori MAE/MSE sono quelli espliciti, evitando un riepilogo che apparentemente ne inverte l’ordine.

<a id="src-u4"></a>

### U4 — Fonti e localizzazione

[Scheda bibliografica e risultati](#u4) · [Link bibliografico principale](https://arxiv.org/abs/2308.10228).

- [Testo arXiv 2308.10228v1](https://arxiv.org/html/2308.10228v1)
- [Programma ufficiale](https://conf.researchr.org/details/ase-2023/ase-2023-papers/56/Scene-Driven-Exploration-and-GUI-Modeling-for-Android-Apps)

**Dove controllare:** Valutazione su benchmark sintetici e app reali; programma ufficiale ASE per la sede.

<a id="src-u5"></a>

### U5 — Fonti e localizzazione

[Scheda bibliografica e risultati](#u5) · [Link bibliografico principale](https://www.usenix.org/conference/usenixsecurity15/technical-sessions/presentation/huang).

- [Pagina ufficiale negli atti](https://www.usenix.org/conference/usenixsecurity15/technical-sessions/presentation/huang)
- [Testo integrale PDF (2)](https://files.usenix.org/s3fs-public/cdn/sec15-paper-huang.pdf)

**Dove controllare:** §3.5 per il binding; §§5.1–5.4 per valutazione e denominatori; metadati ufficiali USENIX.

<a id="src-u6"></a>

### U6 — Fonti e localizzazione

[Scheda bibliografica e risultati](#u6) · [Link bibliografico principale](https://www.usenix.org/conference/usenixsecurity18/presentation/pan).

- [Pagina ufficiale negli atti](https://www.usenix.org/conference/usenixsecurity18/presentation/pan)
- [Testo integrale PDF (2)](https://cs.uwaterloo.ca/~yaafer/teaching/papers/sec18-pan.pdf)

**Dove controllare:** Dataset e protocollo sperimentale; Tabella 5 per metriche e baseline. Accuracy 90,2% e recall 93,1% secondo le intestazioni. Frontespizio e lista autori ufficiale per la discrepanza BibTeX.

<a id="src-u7"></a>

### U7 — Fonti e localizzazione

[Scheda bibliografica e risultati](#u7) · [Link bibliografico principale](https://doi.org/10.1007/s10664-020-09874-z).

- [Testo integrale PDF](https://mcis.cs.queensu.ca/publications/2020/emse_parisa.pdf)
- [Pagina editore](https://link.springer.com/article/10.1007/s10664-020-09874-z)

**Dove controllare:** Tabella 1 e descrizione dei corpus; protocolli di ground truth; valutazione a livello di file e directory.

<a id="src-u8"></a>

### U8 — Fonti e localizzazione

[Scheda bibliografica e risultati](#u8) · [Link bibliografico principale](https://doi.org/10.1109/ITNG.2015.64).

- [Testo integrale PDF](https://ris.utwente.nl/ws/files/5365897/07113499.pdf)
- [Pagina autore o istituzionale (2)](https://research.utwente.nl/en/publications/an-approach-to-business-process-recovery-from-source-code/)

**Dove controllare:** Regole di trasformazione; Tabella I del caso di studio; conclusione; metadati istituzionali.

<a id="src-r1"></a>

### R1 — Fonti e localizzazione

[Scheda bibliografica e risultati](#r1) · [Link bibliografico principale](https://doi.org/10.1109/ICSE.2015.35).

- [Testo integrale PDF](https://cabird.com/pdfs/barnett2015helping.pdf)
- [Pagina autore o istituzionale (2)](https://www.microsoft.com/en-us/research/publication/helping-developers-help-themselves-automatic-decomposition-of-code-review-changesets/)

**Dove controllare:** Introduzione; §§IV–VI

<a id="src-r2"></a>

### R2 — Fonti e localizzazione

[Scheda bibliografica e risultati](#r2) · [Link bibliografico principale](https://doi.org/10.1145/3468264.3468551).

- [Testo integrale PDF](https://www.cs.cmu.edu/~ckaestne/pdf/fse21_sc.pdf)
- [Programma ufficiale](https://2021.esec-fse.org/details/fse-2021-papers/20/SmartCommit-A-Graph-Based-Interactive-Assistant-for-Activity-Oriented-Commits)

**Dove controllare:** § 3; § 4.2–4.3; Tabella2

<a id="src-l1"></a>

### L1 — Fonti e localizzazione

[Scheda bibliografica e risultati](#l1) · [Link bibliografico principale](https://arxiv.org/abs/2403.06095).

- [Testo arXiv 2403.06095v4](https://arxiv.org/html/2403.06095v4)
- [Scheda arXiv 2403.06095](https://arxiv.org/abs/2403.06095)
- [Programma ufficiale](https://conf.researchr.org/details/forge-2025/forge-2025-papers/14/RepoHyper-Search-Expand-Refine-on-Semantic-Graphs-for-Repository-Level-Code-Completi)

**Dove controllare:** Tabella1; § 8; AppendiceA.5

<a id="src-l2"></a>

### L2 — Fonti e localizzazione

[Scheda bibliografica e risultati](#l2) · [Link bibliografico principale](https://doi.org/10.18653/v1/2025.naacl-long.7).

- [Testo integrale PDF](https://aclanthology.org/2025.naacl-long.7.pdf)
- [Pagina ufficiale negli atti](https://aclanthology.org/2025.naacl-long.7/)

**Dove controllare:** Tabelle 1–2; § 8; App.A.4

<a id="src-l3"></a>

### L3 — Fonti e localizzazione

[Scheda bibliografica e risultati](#l3) · [Link bibliografico principale](https://arxiv.org/abs/2410.14684).

- [Testo integrale PDF](https://proceedings.iclr.cc/paper_files/paper/2025/file/4a4a3c197deac042461c677219efd36c-Paper-Conference.pdf)
- [Pagina ufficiale negli atti](https://proceedings.iclr.cc/paper_files/paper/2025/hash/4a4a3c197deac042461c677219efd36c-Abstract-Conference.html)

**Dove controllare:** § 3.1; Tabella2; AppendiceE

<a id="src-l4"></a>

### L4 — Fonti e localizzazione

[Scheda bibliografica e risultati](#l4) · [Link bibliografico principale](https://arxiv.org/abs/2405.17238).

- [Testo integrale PDF](https://proceedings.iclr.cc/paper_files/paper/2025/file/582d4e27fa24168f3af1f4582655034b-Paper-Conference.pdf)
- [Pagina ufficiale negli atti](https://proceedings.iclr.cc/paper_files/paper/2025/hash/582d4e27fa24168f3af1f4582655034b-Abstract-Conference.html)

**Dove controllare:** § 5; Tabella1; § 7

<a id="src-l5"></a>

### L5 — Fonti e localizzazione

[Scheda bibliografica e risultati](#l5) · [Link bibliografico principale](https://arxiv.org/abs/2507.16585).

- [Testo integrale PDF](https://www.usenix.org/system/files/usenixsecurity25-lekssays.pdf)
- [Pagina ufficiale negli atti](https://www.usenix.org/conference/usenixsecurity25/presentation/lekssays)

**Dove controllare:** § 4.4; Tabelle 5–7; § 5

<a id="src-l6"></a>

### L6 — Fonti e localizzazione

[Scheda bibliografica e risultati](#l6) · [Link bibliografico principale](https://arxiv.org/abs/2603.26130).

- [Testo arXiv 2603.26130v1](https://arxiv.org/html/2603.26130v1)
- [Scheda arXiv 2603.26130](https://arxiv.org/abs/2603.26130)

**Dove controllare:** §§ 5–6; § 8

<a id="src-h1"></a>

### H1 — Fonti e localizzazione

[Scheda bibliografica e risultati](#h1) · [Link bibliografico principale](https://doi.org/10.1145/2694344.2694372).

- [Testo integrale PDF](https://www.cs.cornell.edu/andru/papers/asplos15/asplos15.pdf)

**Dove controllare:** §2.2 (modello di minaccia); §6 e Tabelle 1–3 (valutazione); §6.2 (annotazioni e verifica); §6.3 (overhead)

<a id="src-h2"></a>

### H2 — Fonti e localizzazione

[Scheda bibliografica e risultati](#h2) · [Link bibliografico principale](https://www.usenix.org/conference/usenixsecurity22/presentation/solt).

- [Pagina ufficiale negli atti](https://www.usenix.org/conference/usenixsecurity22/presentation/solt)
- [Testo integrale PDF (2)](https://www.usenix.org/system/files/sec22-solt.pdf)

**Dove controllare:** §6 (implementazione); §§7.2–7.4 e Figure 7–9 (prestazioni); §§8.4 e 9 (limiti). Il paper è sec22-solt.pdf; usenixsecurity22-solt.pdf è l'appendice artefatto.

<a id="src-h3"></a>

### H3 — Fonti e localizzazione

[Scheda bibliografica e risultati](#h3) · [Link bibliografico principale](https://doi.org/10.1007/s13389-022-00306-w).

- [Pagina editore](https://link.springer.com/article/10.1007/s13389-022-00306-w)
- [Testo integrale PDF (2)](https://cd-public.github.io/papers/2022/JCEN2022.pdf)

**Dove controllare:** §§5–6; Tabella 1; §§5.2, 5.3, 5.5, 6.1–6.4. PDF autore composto da immagini: pagine PDF 6–14 verificate visivamente.

<a id="src-h4"></a>

### H4 — Fonti e localizzazione

[Scheda bibliografica e risultati](#h4) · [Link bibliografico principale](https://arxiv.org/abs/2606.13860).

- [Scheda arXiv 2606.13860](https://arxiv.org/abs/2606.13860)
- [Testo integrale PDF (2)](https://cd-public.github.io/papers/2026/INTCEC26.pdf)
- [Bibliografia dell’autore](https://cd-public.github.io/papers/byYear.html)

**Dove controllare:** §III (algoritmo e ambiguità degli archi); §§IV–V (implementazione e misure); §§VI–VII (caso esteso e limiti)

<a id="src-e1"></a>

### E1 — Fonti e localizzazione

[Scheda bibliografica e risultati](#e1) · [Link bibliografico principale](https://doi.org/10.5220/0006288707040713).

- [Pagina editore](https://www.scitepress.org/PublishedPapers/2017/62887/)
- [Testo integrale PDF (2)](https://www.scitepress.org/PublishedPapers/2017/62887/62887.pdf)

**Dove controllare:** §§4–6; Figure 3, 6–8; Tabelle 1–2; §7. Testo integrale editore consultato.

<a id="src-e2"></a>

### E2 — Fonti e localizzazione

[Scheda bibliografica e risultati](#e2) · [Link bibliografico principale](https://doi.org/10.5220/0005236100500061).

- [Testo integrale PDF](https://www.scitepress.org/papers/2015/52361/52361.pdf)

**Dove controllare:** §1 per le dimensioni dei modelli; §3 per Reach/Coreach e tempi; §6 per la riservatezza dei modelli.

<a id="src-e3"></a>

### E3 — Fonti e localizzazione

[Scheda bibliografica e risultati](#e3) · [Link bibliografico principale](https://doi.org/10.1007/978-3-030-17184-1_25).

- [Pagina editore](https://link.springer.com/chapter/10.1007/978-3-030-17184-1_25)
- [Testo integrale PDF (2)](https://link.springer.com/content/pdf/10.1007/978-3-030-17184-1_25.pdf)

**Dove controllare:** §3 (semantica task/ISR); §§5–6 (sync-CFG e analisi); §§7.1–7.2 e Tabelle 2–3 (valutazione); §9 (sviluppi e limiti)

<a id="src-f1"></a>

### F1 — Fonti e localizzazione

[Scheda bibliografica e risultati](#f1) · [Link bibliografico principale](https://doi.org/10.1145/77606.77608).

- [Testo integrale PDF](https://www.cs.odu.edu/~cmo/classes/old/cs791sp05/readings/HorwitzRepsBinkley90.pdf)
- [Pagina autore o istituzionale (2)](https://research.cs.wisc.edu/wpis/abstracts/toplas90.abs.html)

**Dove controllare:** Abstract; algoritmo SDG e slicing

<a id="src-f2"></a>

### F2 — Fonti e localizzazione

[Scheda bibliografica e risultati](#f2) · [Link bibliografico principale](https://doi.org/10.1109/SP.2014.44).

- [Testo integrale PDF](https://comsecuris.com/papers/06956589.pdf)

**Dove controllare:** Abstract; §VII

<a id="src-f3"></a>

### F3 — Fonti e localizzazione

[Scheda bibliografica e risultati](#f3) · [Link bibliografico principale](https://doi.org/10.1002/smr.1650).

- [Testo condiviso dall’autore](https://www.researchgate.net/publication/261442641_GUI_code_tracing_through_direct_program_interaction)
- [Pagina autore o istituzionale (2)](https://repositorio.iscte-iul.pt/entities/publication/a13c5cf4-cf1b-4443-b19a-62d131cd687a/full)

**Dove controllare:** Tabella I per benchmark e dimensioni; Figura 7 per tempi e speed-up; discussione dei limiti; metadati istituzionali per anno e DOI.

<a id="src-f4"></a>

### F4 — Fonti e localizzazione

[Scheda bibliografica e risultati](#f4) · [Link bibliografico principale](https://doi.org/10.1145/2594291.2594299).

- [Testo integrale PDF](https://jacquesklein2302.github.io/papers/2014-PLDI-flowdroid.pdf)

**Dove controllare:** Table 1 DroidBench; Table 2 SecuriBench; §5 ICC e limitazioni.

<a id="query"></a>

## 17. Stringhe di ricerca per aggiornare la rassegna

Le stringhe seguenti sono **proposte per estendere o aggiornare la ricerca**. Non sono presentate come un registro esaustivo delle query eseguite. La sintassi di virgolette, parentesi e operatori va adattata alla banca dati. Dopo il recupero, occorre controllare testo integrale, sede, versione, valutazione e artefatti; il solo titolo non determina l'inclusione.

### 17.1 Provenance e bug di dati

```text
("data lineage from source code" OR "data provenance static analysis")
AND ("column-level" OR "field-sensitive" OR "row-level" OR aggregation)

("program slicing" OR "system dependence graph" OR "code property graph")
AND (database OR SQL OR ORM OR persistence OR "shared state")

("semantic bug detection" OR "business logic")
AND ("data flow" OR "writer reader" OR granularity OR "derived state")
```

### 17.2 Raccordi fra componenti e linguaggi

```text
("inter-component communication analysis" OR "microservice dependency extraction")
AND ("static analysis" OR "taint analysis")

("dependency injection" AND "call graph")
OR ("frontend-backend" AND "API linking")

("cross-language call graph" OR "polyglot program analysis")
AND (HTTP OR RPC OR message OR event OR configuration)

("software architecture recovery" OR "data flow diagram")
AND (microservice OR Kafka OR RabbitMQ OR "service discovery")
```

### 17.3 Funzionalità, processi e unità di review

```text
("feature location" OR "concept location" OR "program comprehension")
AND (graph OR slicing OR "traceability link recovery")

("business process recovery from source code" OR "process mining from software")
AND (evaluation OR benchmark OR "case study")

("module clustering" OR "change impact analysis" OR "code review")
AND ("dependency graph" OR "activity-oriented" OR changeset)
```

### 17.4 UI, navigazione e journey

```text
("UI-to-code traceability" OR "GUI code tracing" OR "GUI ripping")
AND (data OR source OR binding OR callback)

("event-flow graph" OR "window transition graph" OR "scene transition graph")
AND (Android OR GUI OR testing OR reconstruction)

("user journey mining" OR "interaction trace" OR screencast)
AND ("source code" OR "feature location" OR "process mining")
```

### 17.5 LLM, repository e retrieval

```text
("repository-level code graph" OR "graph retrieval for code")
AND (LLM OR "large language model")

("LLM code review context" OR "repository-level code review")
AND (evaluation OR benchmark OR ablation OR graph)

("LLM-assisted static analysis" OR "code property graph")
AND (vulnerability OR "source sink" OR "semantic bug")
```

### 17.6 Hardware, interrupt e modelli embedded

```text
("hardware information flow tracking" OR "RTL information flow")
AND (path OR property OR trace OR evaluation)

("embedded software signal flow" OR "AUTOSAR data flow analysis")
AND ("static analysis" OR slicing OR runnable OR RTE)

("interrupt-driven" OR MMIO OR "sensor actuator")
AND ("program analysis" OR "data flow" OR "dependency graph")
```

Per mantenere l'aggiornamento coerente con la richiesta, suggeriamo il filtro temporale dal 2015 e un recupero separato degli antecedenti citati dai lavori selezionati. Le sedi indicate nella domanda sono un punto di partenza, non una condizione sufficiente di qualità: vanno controllati contributo, unità della valutazione, baseline e accesso alla prova. I lavori di venue adiacenti restano pertinenti quando rispondono direttamente al raccordo studiato.

<a id="glossario"></a>

## 18. Glossario e convenzioni di lettura

Le definizioni seguenti fissano l'uso dei termini nel rapporto. Non sostituiscono la definizione formale adottata da ciascun paper.

| Termine | Significato usato nel documento |
|---|---|
| **Alias / points-to** | Possibile identità o relazione fra riferimenti del programma e oggetti astratti; utile per seguire stato condiviso e accessi ai campi. |
| **AST** | Abstract Syntax Tree: struttura sintattica del programma. |
| **CFG / ICFG** | Control-Flow Graph, intra/interprocedurale: possibili trasferimenti di controllo nel modello. |
| **PDG / SDG** | Program/System Dependence Graph: dipendenze di dati e controllo; nel SDG anche collegamenti e riepiloghi interprocedurali. |
| **CPG** | Code Property Graph: rappresentazione che integra viste del codice per attraversamenti e query; lo schema concreto dipende dallo strumento. |
| **Slice** | Porzione del programma selezionata rispetto a un criterio e a determinate dipendenze. Non necessariamente una sequenza eseguibile unica. |
| **Backward / forward slice** | Porzione che può influenzare il criterio / porzione che può esserne influenzata. |
| **Taint source / sink** | Origine marcata e punto di uso o uscita rilevante per una politica di analisi. Il significato dipende dalla specifica. |
| **Lineage / provenance** | Origine e trasformazioni di un dato o risultato, a una granularità dichiarata. |
| **Granularità** | Unità a cui vale un'informazione: servizio, funzione, oggetto, campo, colonna, riga, messaggio, campione o bit. |
| **DFD** | Data Flow Diagram: qui prevalentemente vista architetturale di entità e comunicazioni; non necessariamente lineage di singoli valori. |
| **WTG / ATG / SceneTG** | Grafi con nodi per finestre, activity o scene della UI; cambiano granularità e semantica delle transizioni. |
| **BPMN / KDM** | Notazione di processo / metamodel per rappresentare conoscenza recuperata dal software; usati nel corpus per una trasformazione dal codice al processo. |
| **Cammino strutturale** | Successione di archi presenti nel grafo; potrebbe combinare condizioni incompatibili. |
| **Cammino fattibile** | Successione per cui esistono condizioni compatibili nel modello dichiarato; una soluzione astratta può richiedere concretizzazione. |
| **Traccia** | Sequenza finita osservata durante una specifica esecuzione o simulazione. |
| **Journey osservato** | Percorso d'uso ricavato da eventi di interazione contestualizzati; va distinto dalle sequenze generate da un esploratore. |
| **Ground truth / oracle** | Riferimento usato per giudicare il risultato: annotazioni, generatori, tracce, specifiche o verifiche indipendenti. Va dichiarata la sua copertura. |
| **Precision (P)** | Quota di risultati positivi giudicati corretti: TP/(TP+FP), con unità e denominatore espliciti. |
| **Recall (R)** | Quota di positivi del riferimento recuperati: TP/(TP+FN), nel perimetro dichiarato. |
| **F1** | Media armonica di precision e recall: 2PR/(P+R). Non rende confrontabili unità diverse. |
| **False discovery rate (FDR)** | Quota di segnalazioni positive giudicate false: FP/(TP+FP). |
| **False positive rate (FPR)** | FP/(FP+TN). Non coincide con FDR; alcuni paper usano una denominazione informale, che qui viene chiarita. |
| **Macro / micro** | Media delle metriche sui gruppi / metrica calcolata aggregando i conteggi. Possono produrre risultati diversi. |
| **Punti percentuali (pp)** | Differenza assoluta fra percentuali; distinta dalla variazione percentuale relativa. |
| **RR / reciprocal rank** | Inverso del rango del primo risultato rilevante; non è la percentuale di elementi recuperati correttamente. |
| **acc@k** | Successo di retrieval entro i primi k risultati, secondo il protocollo specifico del benchmark. |
| **Rand Index** | Misura di accordo fra partizioni mediante coppie di elementi; qui usata per clustering di modifiche. |
| **Ablation** | Esperimento che rimuove o sostituisce un componente mantenendo controllati gli altri, per attribuire il contributo. |
| **RTE / runnable / IRV** | Runtime Environment AUTOSAR / unità eseguibile del componente / Inter-Runnable Variable. |
| **ISR / MMIO** | Interrupt Service Routine / Memory-Mapped I/O: gestore di interrupt e accesso a dispositivi tramite indirizzi di memoria. |
| **RTL / IFT / VCD** | Register-Transfer Level / Information Flow Tracking / Value Change Dump per tracce di simulazione. |
| **Happens-before** | Relazione d'ordine associata al modello di esecuzione e sincronizzazione; non richiede sempre timestamp globali. |
| **Noninterferenza** | Proprietà che limita l'influenza di certe informazioni su osservazioni; modello di attaccante e dimensione temporale fanno parte della definizione. |
| **NR / NV** | Non riportato nella fonte consultata / non verificato nella ricerca. |

**Nota di uso del rapporto.** Le proposte di grafo, protocollo ed esempi sono riusabili come base di discussione o di progetto sperimentale, mantenendo la loro etichetta di sintesi non validata. Per attribuire un risultato scientifico, citare il lavoro e la versione indicati nella matrice, insieme alla metrica e al suo perimetro. Per selezionare uno strumento, controllare nuovamente compatibilità e disponibilità dell'artefatto: il rapporto registra la verifica bibliografica alla data dichiarata, non l'esecuzione degli esperimenti.
