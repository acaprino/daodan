# Ricostruire i "flussi" di un sistema software dal codice: rassegna verificata su analisi statica, dinamica e LLM (2014-2026)

La letteratura verificata indica che i flussi end-to-end si ricostruiscono in modo affidabile solo modellando esplicitamente i "punti di aggancio" indiretti (callback del framework, dependency injection, intent, endpoint HTTP, query SQL/ORM, confini fra linguaggi) come archi di un grafo unificato. Gli LLM, nei lavori misurati, rendono meglio quando *etichettano* o *navigano* quel grafo (sorgenti e sink, ricerca multi-hop) che quando sostituiscono l'analisi. Nessun lavoro verificato copre però in un unico grafo tutti i livelli UI → servizio → DB → dispositivo: questo resta il problema aperto principale.

## TL;DR

- **Flussi indiretti:** la tecnica che ricorre è sempre la stessa: un modello del framework o del protocollo trasforma collegamenti impliciti in archi espliciti. Esempi: ciclo di vita Android in FlowDroid, intent in IccTA, bean Spring in Jasmine, matching endpoint/chiamata REST nei microservizi, query SQL ricostruite da JDBC/Hibernate, eventi fra Python e C in PolyCruise. Ognuno copre un solo tipo di aggancio. La composizione dei vari tipi è una mia deduzione e non è stata misurata da nessun lavoro.
- **LLM:** i guadagni misurati sono reali ma modesti e condizionati. RepoGraph porta Agentless da 27,33% a 29,67% su SWE-bench Lite (+32,8% relativo medio fra quattro framework).\[1\] LocAgent arriva al 92,7% di accuratezza nella localizzazione a livello di file.\[2\] IRIS, con GPT-4, secondo la versione camera-ready ICLR 2025 rileva su CWE-Bench-Java 55 vulnerabilità contro le 27 di CodeQL, più del doppio. LLMDFA raggiunge in media l'87,10% di precisione e l'80,77% di recall.\[3\] I limiti dichiarati sono gli stessi ovunque: allucinazioni, costo in token, valutazione su un solo linguaggio (spesso Python o Java).
- **Code review per grafo:** è l'unica area con evidenza diretta. Il partizionamento per relazioni def-use (Barnett et al., ICSE 2015) trova che "nearly 42%" dei changeset Microsoft è decomponibile, e 16 sviluppatori su 20 giudicano corrette le partizioni.\[4\] Flexeme e SmartCommit portano l'accuratezza a 0,81 e al 71-84% (mediana).\[5\]\[6\] Per UX/CHI, AUTOSAR e lineage dei dati fra scrittore e lettore **non ho potuto verificare** lavori con valutazione: lo segnalo come lacuna.

## Metodo e convenzioni

- Ho incluso solo lavori di cui ho aperto la pagina arXiv, DOI/editore o un record bibliografico affidabile (dblp, Crossref, ACM, USENIX).
- Dove ho estratto un numero da un riassunto secondario, o non ho potuto verificarlo nel testo, lo dico esplicitamente.
- **[Misurato]** indica ciò che il paper misura. **[Mia deduzione]** indica una mia inferenza.
- Lavori citati nelle note dell'utente che **non** ho potuto verificare in questa sessione, e quindi esclusi dalla tabella: Amandroid, Joern come strumento separato, GUITAR come strumento, ARCADE come sistema, Bunch, lavori AUTOSAR, lavori CHI sul user journey mining.

## Key Findings

1. **[Misurato]** Senza modellare il framework, l'analisi perde i flussi. Jasmine mostra che le call graph di Soot non vedono i collegamenti creati dalla DI e dall'AOP di Spring. Con il modello aggiunto, FlowDroid trova 12 percorsi di fuga di informazioni sensibili nei benchmark degli autori.\[7\] IccTA migliora FlowDroid propagando il contesto fra componenti Android collegati da intent.\[8\]
2. **[Misurato]** Nei microservizi, il matching statico fra endpoint dichiarati e chiamate client (RestTemplate) ha trovato 135 delle 153 connessioni individuate manualmente su un testbed reale; le 18 mancanti sono falsi negativi.\[9\]
3. **[Misurato]** La qualità delle dipendenze in ingresso conta più dell'algoritmo di clustering per l'architecture recovery: le dipendenze "symbol" battono le "include" (Lutellier et al.).\[10\]\[11\]
4. **[Misurato]** Gli LLM funzionano meglio come *specificatori* (IRIS: etichettano sorgenti e sink per CodeQL) o *navigatori* (RepoGraph, LocAgent: interrogano un grafo) che come analizzatori end-to-end. LLMDFA mostra che l'analisi end-to-end via LLM soffre di allucinazioni, che si riducono scomponendo il problema e delegando a parser e risolutori SMT.\[3\]
5. **[Misurato]** Più contesto da grafo non è sempre meglio. In RepoGraph l'ego-graph a 2 hop "appiattito" fa scendere il resolve rate a 26,00%, sotto il baseline di 27,33%.\[1\]
6. **[Mia deduzione]** Nessuno dei lavori verificati collega in modo misurato un elemento a schermo (widget o vista) al dato persistito che lo alimenta attraverso backend e DB. Esistono solo i pezzi: WTG e GUI ripping per UI → callback, analisi JS → endpoint, endpoint → servizi, codice → tabelle SQL.

## Tabella dei lavori verificati

| # | Titolo | Autori | Anno | Sede | Link verificato | Tipo di flusso | Tecnica | Linguaggi / piattaforme | Rappresentazione | Valutazione / benchmark | Risultati principali | Limiti dichiarati |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | FlowDroid: Precise Context, Flow, Field, Object-sensitive and Lifecycle-aware Taint Analysis for Android Apps | Arzt, Rasthofer, Fritz, Bodden, Bartel, Klein, Le Traon, Octeau, McDaniel | 2014 | PLDI | https://doi.org/10.1145/2594291.2594299 | Dati (taint), controllo (ciclo di vita) | Statica (IFDS, Soot) | Java/Android | Grafo inter-procedurale (ICFG) con main fittizio che modella il lifecycle | DroidBench (suite proposta dagli autori); 500 app Google Play e ~1.000 malware VirusShare\[12\] | Trova fughe nelle app reali. Il paper PLDI'14 riporta: "On DROIDBENCH 1.0, FLOWDROID achieves 93% recall and 86% precision", contro 50%/61% di recall e 74%/81% di precisione per gli strumenti commerciali AppScan Source e Fortify SCA | Path-insensitive. Modello del ciclo di vita necessario e manuale\[13\] |
| 2 | IccTA: Detecting Inter-Component Privacy Leaks in Android Apps | Li, Bartel, Bissyandé, Klein, Le Traon, Arzt, Rasthofer, Bodden, Octeau, McDaniel | 2015 | ICSE | https://doi.org/10.1109/ICSE.2015.48 | Dati fra componenti (intent, ICC) | Statica (strumentazione + taint) | Android | CFG cross-componente: gli intent diventano chiamate esplicite | DroidBench, ICC-Bench; MalGenome; 15.000 app Google Play | Supera gli strumenti esistenti su entrambi i benchmark. Secondo una mapping study secondaria: 534 fughe ICC in 108 app MalGenome e 2.395 in 337 app Google Play\[8\]\[14\] | Copre solo l'ICC risolvibile staticamente |
| 3 | Jasmine: A Static Analysis Framework for Spring Core Technologies | Chen et al. | 2022 | ASE | https://doi.org/10.1145/3551349.3556910 | Tecnico/chiamate via DI e AOP | Statica (estensione Soot) | Java/Spring | Call graph completato con bean, iniezioni e weaving AOP | Micro-benchmark Spring e applicazioni Spring reali; confronto con call graph dinamico | Call graph più completo con overhead "accettabile". Con FlowDroid: 12 percorsi di fuga sensibili\[7\]\[15\] | Solo applicazioni Spring\[15\] |
| 4 | Static Window Transition Graphs for Android | Yang, Zhang, Wu, Wang, Yan, Rountev | 2015 (estesa 2018) | ASE; versione estesa in Automated Software Engineering (journal) | https://doi.org/10.1109/ASE.2015.76; https://doi.org/10.1007/s10515-018-0237-6 | UX/navigazione, controllo GUI | Statica | Android | Window Transition Graph: finestre, eventi, callback, stack delle finestre\[16\] | App Android; applicazione alla generazione di test GUI via traversal\[17\] | Primo studio dettagliato del problema secondo gli autori. Numeri non estratti in questa sessione\[18\] | Gestione parziale del flusso asincrono (estensioni proposte)\[17\] |
| 5 | GUI Ripping: Reverse Engineering of Graphical User Interfaces for Testing | Memon, Banerjee, Nagarajan | 2003 (fondativo) | WCRE | https://doi.org/10.1109/WCRE.2003.1287256 | UX, event-flow | Dinamica (traversal DFS della GUI in esecuzione) | Windows, Java Swing | GUI forest, event-flow graph per componente, integration tree | 4 app Java, WordPad, Yahoo Messenger, WinZip | Motivazione: un test case di 50 eventi richiede 20-30 minuti con capture-replay. In WordPad, Main: 69 eventi system-interaction. Tempi di ripping del paper non verificati\[19\] | Il modello va verificato e corretto dal tester\[19\] |
| 6 | Modeling and Discovering Vulnerabilities with Code Property Graphs | Yamaguchi, Golde, Arp, Rieck | 2014 (fondativo) | IEEE S&P | https://doi.org/10.1109/SP.2014.44 | Dati e controllo (taint-style) | Statica | C | Code Property Graph = AST + CFG + PDG in un multigrafo interrogabile\[20\] | Codice reale (kernel Linux, secondo la letteratura secondaria); numeri non verificati qui | Le vulnerabilità diventano traversal su grafo\[21\] | Pattern di traversal scritti a mano |
| 7 | PolyCruise: A Cross-Language Dynamic Information Flow Analysis | Li, Ming, Luo, Cai | 2022 | USENIX Security | https://www.usenix.org/conference/usenixsecurity22/presentation/li-wen | Dati cross-language | Ibrida (dipendenze simboliche statiche per linguaggio + analisi dinamica language-agnostic)\[22\] | Python-C | Dynamic Information Flow Graph costruito incrementalmente da eventi\[23\] | Micro, medi e grandi benchmark; primo benchmark per DIFA multilingue\[22\] | 14 vulnerabilità cross-language sconosciute (es. NumPy): 11 confermate, 8 CVE, 8 corrette\[22\] | Dinamica: copre solo i percorsi eseguiti. Implementata per Python-C |
| 8 | Reconstructing the Holistic Architecture of Microservice Systems using Static Analysis | Bushong, Das, Cerny (Baylor University; autori da Crossref) | 2022 | CLOSER (SciTePress), pp. 149-157 | https://doi.org/10.5220/0011032100003200 | Tecnico (HTTP fra servizi), dati (entità) | Statica (bytecode Java)\[24\] | Java/Spring Boot | Diagramma di comunicazione, context map, bounded context\[24\] | Testbed di microservizi (Texas Teacher Examination); confronto con analisi manuale | 135 delle 153 connessioni manuali individuate (18 mancanti). Enumerazione manuale ~1,5 h\[9\] | Tecnologie client specifiche (RestTemplate)\[25\] |
| 9 | Static Analysis of Dynamic Database Usage in Java Systems | Meurice, Nagy, Cleve | 2016 | CAiSE | https://doi.org/10.1007/978-3-319-39696-5_30 | Dati (codice → tabelle/colonne) | Statica | Java (JDBC, Hibernate, JPA) | Insieme di access location con le query SQL ricostruite e le tabelle/colonne toccate\[26\] | Sistemi Java reali; numeri non estratti | Secondo gli autori è il primo approccio che traduce gli accessi ORM in query\[26\] | Query molto dinamiche ricostruite solo parzialmente |
| 10 | Statically Checking Web API Requests in JavaScript | Wittern et al. | 2017 | ICSE (preprint arXiv) | https://arxiv.org/abs/1702.03906 | Tecnico frontend → API | Statica (string analysis) | JavaScript | Richieste estratte (URL, metodo, dati) confrontate con specifiche Swagger\[27\] | Codice JS reale contro specifiche OpenAPI; numeri non verificati | Estrae le richieste e verifica la conformità agli endpoint\[27\] | Difficoltà intrinseche dell'analisi di JS\[27\] |
| 11 | Comparing Software Architecture Recovery Techniques Using Accurate Dependencies | Lutellier, Chollak, Garcia, Tan, Rayside, Medvidovic, Kroeger | 2015 | ICSE (SEIP) | https://doi.org/10.1109/ICSE.2015.136 | Architetturale/strutturale | Statica + clustering | C/C++, Java | Partizioni di moduli | Sistemi con architetture ground truth pubblicate dagli autori\[28\] | Le dipendenze symbol migliorano il recovery rispetto alle include. Servono tecniche più accurate\[10\]\[29\] | Ground truth costosa da costruire |
| 12 | Feature location in source code: a taxonomy and survey | Dit, Revelle, Gethers, Poshyvanyk | 2013 (fondativo) | J. Softw. Evol. Process | https://doi.org/10.1002/smr.567 | Funzionale (feature → codice) | Survey (statica, dinamica, testuale) | Vari | Tassonomia a 9 dimensioni\[30\] | 89 articoli classificati\[30\] | Base concettuale per feature/concept location | Survey: nessun nuovo esperimento |
| 13 | Helping Developers Help Themselves: Automatic Decomposition of Code Review Changesets | Barnett, Bird, Brunet, Lahiri | 2015 | ICSE | https://doi.org/10.1109/ICSE.2015.35 | Dati (def-use) per la review | Statica (Roslyn) | C# | Partizioni = chiusura transitiva di link def-use e use-use fra diff-region | 1.000 changeset Microsoft Office; studio con 20 sviluppatori | ~42% dei changeset decomponibili. Per 16 sviluppatori su 20 le partizioni sono corrette e complete. Nessun falso positivo, molti falsi negativi\[4\] | Non vede override/interfacce, config/XML, dipendenze cross-language e dinamiche\[4\] |
| 14 | Flexeme: Untangling Commits Using Lexical Flows | Pârțachi, Dash, Allamanis, Barr | 2020 | ESEC/FSE | https://doi.org/10.1145/3368089.3409693 | Dati, controllo, nomi | Statica + graph kernel | C# | δ-PDG multi-versione + name flow (δ-NFG), clustering agglomerativo con kernel Weisfeiler-Lehman\[6\] | Corpus artificiale di commit "tangled" C# | Accuratezza 0,81 (+0,14 sullo stato dell'arte), 32 volte più veloce\[6\] | Troppo lento per l'uso interattivo (~10 s per untangling). Tangle sintetici\[6\] |
| 15 | SmartCommit: A Graph-Based Interactive Assistant for Activity-Oriented Commits | Shen, Zhang, Kästner, Zhao, Wei, Liang, Jin | 2021 | ESEC/FSE | https://doi.org/10.1145/3468264.3468551 | Dati, chiamate, refactoring | Statica + interazione umana | Java (dedotto, non confermato) | Diff Hunk Graph con archi pesati (hard/soft/refactoring/cosmetic)\[5\] | Field study con 83 ingegneri per 9 mesi; 3.000 commit compositi sintetici da 10 progetti\[5\] | Accuratezza mediana 71-84% senza intervento umano; in media 3,41 aggiustamenti; meno di 5 s nel 90% dei casi\[5\] | Il concetto di "attività" dipende dallo sviluppatore: serve un umano nel loop\[5\] |
| 16 | RepoGraph: Enhancing AI Software Engineering with Repository-level Code Graph | Ouyang, Yu, Ma, Xiao, Zhang, Jia, Han, Zhang, Yu | 2025 | ICLR | https://arxiv.org/abs/2410.14684 | Chiamate/definizioni (strutturale) | LLM + statica (tree-sitter) | Python | Grafo a livello di riga (nodi def/ref; archi invoke/contain), ego-graph k-hop\[1\] | SWE-bench Lite; CrossCodeEval (2.665 campioni Python)\[1\] | +32,8% relativo medio. Agentless+RepoGraph: 29,67%. RAG: da 2,67 a 5,33. CrossCodeEval GPT-4o, EM codice: da 10,5 a 28,7\[1\] | Solo Python. Solo LLM proprietari. Solo il set Lite. Costo in token più alto negli agenti\[1\] |
| 17 | CodexGraph: Bridging Large Language Models and Code Repositories via Code Graph Databases | Liu, Lan, Hu, Liu, Zhang, Zhou, Wang, Shieh | 2024 | Preprint arXiv | https://arxiv.org/abs/2408.03910 | Strutturale (simboli e relazioni) | LLM + graph DB (Neo4j/Cypher)\[31\] | Python | Code graph con schema unificato, interrogato dall'agente via query | Benchmark repository-level (CrossCodeEval, SWE-bench, EvoCodeBench); numeri non estratti | Prestazioni "competitive" secondo gli autori\[32\] | Gli autori dichiarano un aumento del consumo di token\[31\] |
| 18 | LocAgent: Graph-Guided LLM Agents for Code Localization | Chen, Tang, Deng, Wu, Wu, Jiang, Prasanna, Cohan, Wang | 2025 | ACL | https://arxiv.org/abs/2503.09089 | Funzionale (issue → codice) | LLM + grafo eterogeneo | Python | Grafo diretto eterogeneo: file, classi, funzioni; import, invocazioni, ereditarietà\[2\] | SWE-Bench-Lite e benchmark reali di localizzazione | 92,7% di accuratezza a livello di file. Costo ~86% più basso con Qwen-2.5-Coder-32B fine-tuned. +12% Pass@10 nella risoluzione delle issue\[2\] | Valutazione centrata su Python |
| 19 | LLMDFA: Analyzing Dataflow in Code with Large Language Models | Wang, Zhang, Su, Xu, Xie, Zhang | 2024 | NeurIPS | https://arxiv.org/abs/2402.10754 | Dati (sorgente → sink) | LLM + strumenti esterni (parser, SMT) | Java, app Android | Fatti dataflow per funzione composti in percorsi; fattibilità validata con SMT | Programmi sintetici (3 tipi di bug) e app Android reali\[3\] | Media: 87,10% precisione, 80,77% recall; F1 fino a +0,35. Supera CodeFuseQuery\[3\]\[33\] | Allucinazioni mitigate ma non eliminate. Serve il CFG in ingresso\[34\] |
| 20 | IRIS: LLM-Assisted Static Analysis for Detecting Security Vulnerabilities | Li, Dutta, Naik | 2025 | ICLR | https://arxiv.org/abs/2405.17238 | Dati (taint, whole-repo) | Neuro-simbolica: LLM inferisce le specifiche + CodeQL | Java | Specifiche sorgente/sink → query CodeQL → percorsi filtrati da LLM | CWE-Bench-Java: 120 vulnerabilità validate, 4 CWE\[35\] | Secondo la camera-ready ICLR 2025 (arXiv v3): "CodeQL detects only 27 of these vulnerabilities whereas IRIS with GPT-4 detects 55 (+28)". Il valore 69 di versioni precedenti del preprint è superato. FDR migliorata di 5 punti. 4 vulnerabilità nuove | Solo Java. Serve un progetto compilabile |
| 21 | An Empirical Study on Concurrency Bugs in Interrupt-Driven Embedded Software | Chao Li, Rui Chen et al. (Beijing Institute of Control Engineering; da Crossref) | 2023 | ISSTA, pp. 1345-1356 | https://doi.org/10.1145/3597926.3598140 | Controllo/concorrenza HW-SW (interrupt) | Studio empirico | Embedded industriale | Tassonomia di pattern | 132 bug da 102 software industriali\[36\] | 5 pattern di bug. Solo il 14% coinvolge interrupt annidati\[36\] | Dati industriali non pubblici (deduzione dal contesto) |
| 22 | Automatic Detection, Validation and Repair of Race Conditions in Interrupt-Driven Embedded Software (SDRacer) | Wang et al. | 2023 (preprint) | arXiv (versione journal non verificata) | https://arxiv.org/abs/2305.17869 | Controllo/dati su variabili condivise fra task e ISR | Ibrida: statica + esecuzione simbolica + simulazione\[37\] | C embedded | Coppie di accessi condivisi + percorsi | Software interrupt-driven (numeri non estratti) | Rileva, valida e ripara le race\[38\] | La statica da sola produce falsi positivi (motivazione del lavoro)\[37\] |
| 23 | Efficient data race detection for interrupt-driven programs via path feasibility analysis (IntRace) | Jingwen Zhao, Yanxia Wu, Jibin Dong (da Crossref) | 2024 | J. Supercomputing, vol. 80, n. 15, pp. 21699-21725 | https://doi.org/10.1007/s11227-024-06189-4 | Controllo/dati (race con ISR) | Statica + fattibilità dei percorsi\[39\] | C embedded | Coppie di accessi filtrate per concorrenza e raggiungibilità\[39\] | Benchmark + 9 programmi embedded reali\[39\] | Meno falsi positivi delle analisi statiche precedenti (numeri non estratti)\[39\] | Non estratti |
| 24 | Hardware Information Flow Tracking | Hu, Ardeshiricham, Kastner | 2021 | ACM Computing Surveys | https://doi.org/10.1145/3447867 | Flusso hardware (bit, gate, RTL) | Survey (statica/simulazione/verifica formale) | Netlist, RTL, HDL | Etichette di taint + logica di tracking (shadow logic)\[40\] | Survey | GLIFT è la prima tecnica IFT precisa consolidata. A livello di gate tutti i flussi (anche impliciti e di timing) diventano espliciti\[41\]\[42\] | Overhead e scalabilità a livello di gate\[43\] |
| 25 | LLM-IFT: LLM-Powered Information Flow Tracking for Secure Hardware | Mashnoor, Akyash, Kamali, Azar (University of Central Florida) | 2025 | Preprint arXiv | https://arxiv.org/abs/2504.07015 | Flusso hardware | LLM (analisi gerarchica multi-step delle dipendenze) + IFT | RTL | Dipendenze gerarchiche estratte da LLM sull'RTL | Casi di test Trust-Hub a livello di IP e di SoC | Secondo l'abstract: "a 100% success rate in accurate IFT analysis for confidentiality and integrity checks in hardware" | Motivazione: GLIFT non scala sui SoC grandi e CellIFT ha costi di strumentazione\[43\] |

Nota sulla verifica: per le righe 21-25 e 8 alcuni metadati (numeri, e gli autori di SDRacer) non sono stati estratti dal testo; li includo perché la pagina DOI o arXiv è stata trovata e il contenuto principale è confermato da abstract, record Crossref o snippet dell'editore.

## Details: per tipo di flusso

### 1. Flusso dati (provenienza, consumo, granularità)

**Lavori più rilevanti**
- **FlowDroid:** è la base di riferimento per il taint statico con modello del framework, e quasi tutti gli altri ne derivano.\[44\]
- **IRIS:** dimostra il ruolo più efficace dell'LLM, cioè scrivere le specifiche (sorgenti e sink delle librerie) che mancano all'analisi statica.
- **LLMDFA:** è il riferimento per l'analisi dataflow senza compilazione via LLM, con mitigazione esplicita delle allucinazioni.
- **Meurice et al.:** collega il codice Java alle tabelle e colonne anche attraverso un ORM, cioè l'aggancio "per nome di tabella" che serve all'utente.\[26\]
- **PolyCruise:** è l'unico lavoro verificato che misura flussi di dati attraverso due linguaggi.\[22\]

**Tecniche ricorrenti:** IFDS/taint con alias on-demand; specifiche sorgente/sink (manuali, oppure inferite da LLM); string analysis per ricostruire SQL e URL; DIFG dinamici.\[13\]\[23\]\[45\]

**Problemi aperti**
- **[Mia deduzione]** Nessun lavoro verificato misura la *coerenza semantica* fra chi scrive e chi legge un dato persistito, cioè unità, granularità e significato. I lavori trovano percorsi, non incompatibilità di contratto.
- Il lineage attraverso il DB, dove uno scrive una colonna e un altro servizio la legge, richiede di unire l'output alla Meurice con il taint. Non ho trovato una valutazione di questa composizione.

**Benchmark riusabili:** DroidBench, ICC-Bench, CWE-Bench-Java (esteso nel repository con 93 nuove CVE secondo la pagina del progetto),\[46\] il benchmark multilingue di PolyCruise.

### 2. Flusso funzionale (passi che realizzano una funzionalità)

**Lavori più rilevanti**
- **Dit et al.:** tassonomia di riferimento della feature location, su 89 articoli.\[30\]
- **LocAgent:** localizzazione da descrizione in linguaggio naturale al codice, con navigazione multi-hop su grafo.
- **RepoGraph:** ego-graph attorno al termine di ricerca come contesto per l'LLM.
- **CodexGraph:** grafo interrogabile in Cypher dall'agente.

**Tecniche ricorrenti:** grafi eterogenei file/classe/funzione; retrieval k-hop; agenti con azioni "search graph"; riassunto LLM del sottografo.

**Problemi aperti**
- **[Misurato]** In RepoGraph il sottografo a 2 hop appiattito peggiora il risultato, quindi il dimensionamento del contesto è un problema non risolto.\[1\]
- **[Mia deduzione]** La feature location LLM-based è valutata su issue (SWE-bench), non su "funzionalità utente" end-to-end. Il passo dalla localizzazione di un punto alla ricostruzione della sequenza dei passi non è misurato.

**Benchmark riusabili:** SWE-bench Lite, CrossCodeEval, i dataset di localizzazione di LocAgent.

### 3. Flusso tecnico (richiesta-risposta, chiamate, messaggi, eventi)

**Lavori più rilevanti**
- **Jasmine:** dependency injection e AOP di Spring.
- **IccTA:** intent come messaggi fra componenti.
- **Ricostruzione dei microservizi (Bushong, Das, Cerny):** matching endpoint/chiamata HTTP.
- **Wittern et al.:** estrazione delle richieste dal JavaScript del frontend.\[27\]
- **PolyCruise:** confini fra linguaggi.

**Tecniche ricorrenti:**
- **Due fasi:** (a) estrarre i "provider", cioè endpoint, bean, intent filter; (b) estrarre i "consumer", cioè chiamate client, punti di iniezione, intent; poi fare il matching per stringa, tipo o firma.\[25\]\[47\]
- **Strumentazione:** l'IR viene riscritta così che l'aggancio implicito diventi una chiamata esplicita (IccTA, Jasmine).

**Problemi aperti**
- **[Misurato]** Il 12% circa delle connessioni (18 su 153) sfugge al matching statico nei microservizi.\[9\]
- **[Mia deduzione]** Code e broker (Kafka, RabbitMQ) compaiono solo come event bus nel lavoro su C#.\[48\] Non ho verificato valutazioni dedicate al matching topic produttore/consumatore.
- **[Mia deduzione]** Il frontend-backend linking è valutato sulla conformità a Swagger, non sulla precisione del collegamento al codice del controller.

**Benchmark riusabili:** testbed di microservizi usati da Bushong, Das e Cerny; micro-benchmark Spring di Jasmine; DroidBench/ICC-Bench per l'ICC.

### 4. Flusso logico e di controllo (stati, transizioni, ordine)

**Lavori più rilevanti**
- **Code Property Graph (Yamaguchi et al.):** unifica AST, CFG e PDG ed è la rappresentazione da cui derivano molti strumenti.\[21\]
- **FlowDroid:** modella l'ordine del ciclo di vita.\[49\]
- **WTG:** transizioni di stato della GUI con modello dello stack.\[16\]
- **Studio ISSTA 2023:** ordine delle operazioni sotto interruzioni.

**Tecniche ricorrenti:** main fittizio o harness che enumera gli ordini possibili; modelli a stack; sequenzializzazione dei programmi con interrupt.\[50\]

**Problemi aperti:** gli ordini realmente possibili, nella concorrenza event-driven, restano sovra-approssimati. Lo dimostra il fatto che tutti i lavori sugli interrupt nascono per ridurre i falsi positivi.\[39\]\[51\]

### 5. Flusso operativo e UX (azioni, schermate, navigazione)

**Lavori più rilevanti**
- **GUI Ripping (fondativo):** event-flow graph estratto dinamicamente.\[19\]
- **WTG statico per Android:** sequenze di finestre con eventi e callback, cioè il collegamento fra azione utente e codice che reagisce.\[18\]
- **[Mia deduzione]** FlowDroid e IccTA chiudono la catena callback → effetto sui dati, se usati insieme al WTG.

**Tecniche ricorrenti:** ripping dinamico; modellazione statica di layout, listener e stack delle activity.

**Problemi aperti**
- **[Mia deduzione]** Non ho verificato lavori CHI con valutazione sperimentale sul *user journey mining* dal codice: è una lacuna di questa rassegna, non necessariamente della letteratura.
- Il collegamento widget → dato del backend che lo popola non è coperto da nessun lavoro verificato.

**Benchmark riusabili:** le app dei paper WTG e GUITAR. Rico è un dataset UI citato in un lavoro collegato, ma non l'ho verificato direttamente.\[52\]

### 6. Flusso hardware ed embedded (segnali, interrupt, HW/SW)

**Lavori più rilevanti**
- **Hu, Ardeshiricham, Kastner (survey HW IFT):** mappa dei livelli di astrazione, dal gate al sistema.\[53\]
- **Studio empirico ISSTA 2023:** 132 bug reali da interrupt.\[36\]
- **SDRacer e IntRace:** rilevazione delle race fra task e ISR.\[38\]\[39\]
- **LLM-IFT (Mashnoor et al.):** primo tentativo LLM nel tracking hardware; l'abstract dichiara il 100% di successo sui casi di test Trust-Hub a livello di IP e di SoC.

**Tecniche ricorrenti:** etichette di taint per bit con shadow logic (GLIFT); IFT a livello RTL per scalare (CellIFT, citato); lockset e fattibilità dei percorsi per gli interrupt.\[39\]\[40\]\[43\]\[51\]

**Problemi aperti**
- **[Misurato, dalla survey]** La precisione a livello di gate costa troppo sui SoC grandi.\[43\]
- **[Mia deduzione]** Non ho potuto verificare lavori su AUTOSAR o sul signal flow nel software embedded con valutazione. La copertura DAC/DATE di questa rassegna è quindi solo indiretta, tramite la survey.

## Sintesi trasversale: risposte alle 5 domande

**1. Flussi end-to-end con componenti non collegati direttamente.**
- **[Misurato]** Ogni tipo di aggancio indiretto è stato risolto separatamente con lo stesso schema: si modella il framework e si inserisce un arco esplicito.
  - Intent: IccTA.
  - DI/AOP Spring: Jasmine, 12 nuovi percorsi di fuga.
  - HTTP fra servizi: 135 connessioni su 153.\[9\]
  - Codice → tabella via ORM: Meurice et al.\[26\]
  - Python ↔ C: PolyCruise.\[22\]
- **[Mia deduzione]** Per un flusso UI → backend → DB servono almeno tre di questi modelli componiti in un unico grafo, con l'endpoint e il nome della tabella come chiavi di giunzione. Nessun lavoro verificato misura questa composizione.

**2. Elemento a schermo ↔ codice e dati; azione utente ↔ effetti.**
- **[Misurato]** WTG e GUI ripping collegano evento → callback → finestra successiva. FlowDroid collega callback → sink di dati.\[18\]\[54\]
- **[Mia deduzione]** La catena completa widget → handler → richiesta HTTP → controller → query → colonna è ricostruibile solo concatenando WTG, analisi JS/endpoint, matching dei servizi e analisi SQL. Il punto debole atteso è l'anello stringa-URL, dove l'analisi statica dei microservizi perde già il 12% circa delle connessioni.

**3. Dividere analisi e code review per grafo, non per cartelle.**
- **[Misurato]**
  - **Barnett et al.:** il 42% circa dei changeset è decomponibile per def-use; 16 sviluppatori su 20 approvano le partizioni; nessun falso positivo.\[4\]
  - **Flexeme:** accuratezza 0,81 con PDG + flussi di nomi.\[6\]
  - **SmartCommit:** 71-84% mediano, 3,41 correzioni umane in media.\[5\]
  - **Lutellier et al.:** per i moduli la qualità delle dipendenze è decisiva.\[11\]
- **[Mia deduzione]** La ricetta pratica è usare componenti connesse del grafo def-use/call come unità e poi lasciare all'umano l'aggiustamento delle soglie. I falsi negativi (override, config, cross-language) sono proprio gli archi indiretti della domanda 1.

**4. Cosa aggiungono gli LLM, e con quali limiti misurati.**
- **[Misurato]** Specifiche di taint (IRIS: da 27 a 55 vulnerabilità rilevate secondo la camera-ready ICLR 2025). Analisi senza compilazione (LLMDFA: 87,10% di precisione e 80,77% di recall). Navigazione del grafo (LocAgent: 92,7% a livello di file; RepoGraph: +2,34 punti assoluti su Agentless).
- **[Misurato]** Limiti:
  - allucinazioni nell'analisi end-to-end (LLMDFA);
  - degrado con troppo contesto (RepoGraph a 2 hop);
  - costo in token (CodexGraph, RepoGraph negli agenti);
  - valutazione quasi sempre su un solo linguaggio.
- **[Mia deduzione]** Le descrizioni semantiche generate da LLM ("questo campo è in centesimi") sarebbero il pezzo mancante per rilevare le incoerenze di significato. Non ho trovato una valutazione verificata di questo uso.

**5. Bug visibili solo seguendo il flusso.**
- **[Misurato]** Fughe di dati fra componenti (IccTA), fra framework (Jasmine) e fra linguaggi (PolyCruise: 8 CVE). Vulnerabilità taint whole-repo (IRIS). Race fra task e ISR (5 pattern su 132 bug industriali).\[22\]\[36\]
- **[Mia deduzione]** Alcuni bug sono ancora senza strumenti valutati in questa rassegna: incoerenze scrittore/lettore su unità o granularità, stato derivato falso (cache o campo calcolato non aggiornato). Il rilevamento plausibile combina lineage per colonna (Meurice) con l'annotazione semantica delle due estremità (LLM) e un controllo di compatibilità. È un'ipotesi di ricerca, non un risultato.

## Recommendations

1. **Per un prototipo end-to-end:** CPG o Soot/WALA come base; modelli di framework alla Jasmine per la DI; matching endpoint/chiamata alla Cerny per HTTP; estrazione SQL alla Meurice per il DB. Usate l'LLM solo per etichettare sorgenti, sink e semantica dei campi (schema IRIS), non per tracciare i percorsi.
2. **Per la code review:** partite da Barnett (def-use), aggiungete gli archi indiretti della domanda 1 e un controllo umano alla SmartCommit. Misurate con il protocollo di Flexeme, cioè commit "tangled" sintetici.
3. **Per il retrieval LLM:** ego-graph da 1 hop non riassunto come default, perché in RepoGraph è il migliore.\[1\]
4. **Per valutare:** riusate DroidBench/ICC-Bench, CWE-Bench-Java, SWE-bench Lite e il benchmark multilingue di PolyCruise. Per i flussi UI → DB va costruito un benchmark nuovo: è la lacuna più evidente.

## Caveats

- Il budget di ricerca non ha permesso di verificare diversi lavori classici richiesti (Amandroid, ARCADE, Bunch, GUITAR come strumento, lavori AUTOSAR e CHI). La loro assenza dalla tabella non è un giudizio sulla loro rilevanza.
- Alcuni numeri provengono da abstract o da riassunti secondari e non dalle tabelle dei paper; sono segnalati nelle celle. Per IRIS la camera-ready ICLR 2025 (arXiv v3) riporta 55 vulnerabilità rilevate con GPT-4 contro 27 di CodeQL; il valore 69 delle versioni precedenti del preprint va considerato superato.
- Per alcuni lavori (righe 3, 10, 22) gli elenchi completi degli autori non sono stati verificati; per le righe 8, 21, 23 e 25 gli autori provengono da Crossref o dall'abstract arXiv.
- Tutte le affermazioni marcate **[Mia deduzione]** sono ipotesi non misurate.

## Fonti

1. <https://arxiv.org/pdf/2410.14684>
2. [LocAgent: Graph-Guided LLM Agents for Code Localization](https://arxiv.org/abs/2503.09089)
3. [LLMDFA: Analyzing Dataflow in Code with Large Language Models](https://arxiv.org/abs/2402.10754)
4. <https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/barnett2015hdh.pdf>
5. <https://www.cs.cmu.edu/~ckaestne/pdf/fse21_sc.pdf>
6. <https://partachi.com/papers/untangle.pdf>
7. [Jasmine: A Static Analysis Framework for Spring Core Technologies (ASE 2022 - Research Papers) - ASE 2022](https://conf.researchr.org/details/ase-2022/ase-2022-research-papers/26/Jasmine-A-Static-Analysis-Framework-for-Spring-Core-Technologies)
8. [ORBilu: IccTA: Detecting Inter-Component Privacy Leaks in Android Apps - 2015](https://orbilu.uni.lu/handle/10993/20058?locale=en)
9. [(PDF) Using Static Analysis to Address Microservice Architecture Reconstruction](https://www.researchgate.net/publication/357990564_Using_Static_Analysis_to_Address_Microservice_Architecture_Reconstruction)
10. [(PDF) Evolution in Software Architecture Recovery Techniques](https://www.researchgate.net/publication/321025813_Evolution_in_Software_Architecture_Recovery_Techniques_-_A_Survey)
11. [(PDF) Measuring the Impact of Code Dependencies on Software Architecture Recovery Techniques](https://www.researchgate.net/publication/313866417_Measuring_the_Impact_of_Code_Dependencies_on_Software_Architecture_Recovery_Techniques)
12. [ORBilu: FlowDroid: Precise context, flow, field, object-sensitive and lifecycle-aware taint analysis for android apps - 2014](https://orbilu.uni.lu/handle/10993/20223)
13. [FLOWDROID: PRECISE CONTEXT, FLOW FIELD, ...](https://people.cs.vt.edu/~ryder/6304/lectures/10-ArztEtAl-FlowDroid-PLDI2014-DanBarton.pdf)
14. [Mobile App Privacy in Software Engineering Research: A Systematic Mapping Study](https://arxiv.org/pdf/1910.03622)
15. [Jasmine: A Static Analysis Framework for Spring Core Technologies](https://dl.acm.org/doi/fullHtml/10.1145/3551349.3556910)
16. [Static Analyses of GUI Behavior in Android Applications Dissertation](https://core.ac.uk/download/pdf/47055446.pdf)
17. [\[PDF\] Static window transition graphs for Android](https://www.semanticscholar.org/paper/Static-window-transition-graphs-for-Android-Yang-Wu/2de93fc2044d0d7445a5ecc5c1414252b3526cdb)
18. [Static window transition graphs for Android](https://dl.acm.org/doi/abs/10.1109/ASE.2015.76)
19. <https://www.cs.umd.edu/~atif/pubs/MemonWCRE2003.pdf>
20. [\[PDF\] Modeling and Discovering Vulnerabilities with Code Property Graphs](https://www.semanticscholar.org/paper/Modeling-and-Discovering-Vulnerabilities-with-Code-Yamaguchi-Golde/07c4549be429a52274bc0ec083bf5598a3e5c365)
21. [TaintRadar: Semantic-Aware Taint-Style Vulnerability Detection via Augmented Code Property Graphs](https://arxiv.org/pdf/2607.16456)
22. [PolyCruise: A Cross-Language Dynamic Information Flow Analysis](https://www.usenix.org/conference/usenixsecurity22/presentation/li-wen)
23. [PolyCruise: A Cross-Language Dynamic Information Flow ...](https://www.usenix.org/system/files/sec22-li-wen.pdf)
24. [Reconstructing the Holistic Architecture of Microservice Systems using](https://www.scitepress.org/PublishedPapers/2022/110321/110321.pdf)
25. [Assessing Evolution of Microservices Using Static Analysis](https://www.mdpi.com/2076-3417/14/22/10725)
26. [Static Analysis of Dynamic Database Usage in Java Systems](https://link.springer.com/chapter/10.1007/978-3-319-39696-5_30)
27. [Statically Checking Web API Requests in JavaScript](https://arxiv.org/pdf/1702.03906)
28. [Uwaterloo](http://asset.uwaterloo.ca/ArchRecovery/)
29. [\[PDF\] A comparative analysis of software architecture recovery techniques](https://www.semanticscholar.org/paper/A-comparative-analysis-of-software-architecture-Garcia-Ivkovic/e535bd8fbe8b14dd55d0600a6dd54f7c0af7d3ce)
30. [Feature location in source code: a taxonomy and survey - Dit - 2013 - Journal of Software: Evolution and Process - Wiley Online Library](https://onlinelibrary.wiley.com/doi/abs/10.1002/smr.567)
31. [CODEXGRAPH: Bridging Large Language Models](https://arxiv.org/pdf/2408.03910)
32. [\[2408.03910v1\] CodexGraph: Bridging Large Language Models and Code Repositories via Code Graph Databases](https://arxiv.org/abs/2408.03910v1)
33. [LLMDFA: Analyzing Dataflow in Code with Large Language Models](https://arxiv.org/html/2402.10754)
34. [LLMDFA: Analyzing Dataflow in Code with Large Language Models](https://arxiv.org/pdf/2402.10754)
35. [LLM-Assisted Static Analysis for Detecting](https://arxiv.org/html/2405.17238v1)
36. [An Empirical Study on Concurrency Bugs in Interrupt-Driven Embedded Software](https://dl.acm.org/doi/pdf/10.1145/3597926.3598140)
37. [Automatic Detection, Validation and Repair of Race ...](https://arxiv.org/pdf/2305.17869)
38. [(PDF) Automatic Detection, Validation and Repair of Race Conditions in Interrupt-Driven Embedded Software](https://www.researchgate.net/publication/371137085_Automatic_Detection_Validation_and_Repair_of_Race_Conditions_in_Interrupt-Driven_Embedded_Software)
39. [Efficient data race detection for interrupt-driven programs via path feasibility analysis](https://link.springer.com/article/10.1007/s11227-024-06189-4)
40. [IEEE TRANSACTIONS ON COMPUTER-AIDED DESIGN OF INTEGRATED CIRCUITS AND SYSTEMS 1](https://sites.engineering.ucsb.edu/~sherwood/pubs/TCAD-11-gliftproof.pdf)
41. [Hardware Information Flow Tracking](https://dl.acm.org/doi/fullHtml/10.1145/3447867)
42. [Method and system providing mutli-level security to gate level information flow](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/10083305)
43. [LLM-IFT: LLM-Powered Information Flow Tracking for Secure Hardware](https://arxiv.org/pdf/2504.07015)
44. [FlowDroid: Precise Context, Flow, Field, Object-sensitive and Lifecycle-aware Taint Analysis for Android Apps](https://paperswelove.org/papers/flowdroid-precise-context-flow-field-object-sensit-407ad55e/)
45. [Static Analysis of Dynamic Database Usage in Java Systems](https://www.researchgate.net/publication/303394636_Static_Analysis_of_Dynamic_Database_Usage_in_Java_Systems)
46. [github.com](https://github.com/iris-sast/iris)
47. [Microvision: Static analysis-based approach to visualizing microservices in augmented reality](https://arxiv.org/html/2207.02974v2)
48. [Deriving Microservice Architectural Perspectives Using ...](https://par.nsf.gov/servlets/purl/10670944)
49. [FLOWDROID: Precise context, flow, field, object-sensitive and lifecycle-aware taint analysis for Android apps - Penn State](https://pure.psu.edu/en/publications/flowdroid-precise-context-flow-field-object-sensitive-and-lifecyc/)
50. [(PDF) Numerical Static Analysis of Interrupt-driven Programs via Sequentialization](https://www.researchgate.net/publication/283730752_Numerical_Static_Analysis_of_Interrupt-driven_Programs_via_Sequentialization)
51. [Static Deadlock Detection for Interrupt-driven Embedded Software](https://ieeexplore.ieee.org/document/10799242/)
52. [What do all these Buttons do? Statically Mining Android User Interfaces at Scale](https://arxiv.org/pdf/2105.03144)
53. [Hardware Information Flow Tracking - Kastner Research Group](https://kastner.ucsd.edu/wp-content/uploads/2020/12/admin/hw_ift_survey.pdf)
54. [\[PDF\] FlowDroid: precise context, flow, field, object-sensitive and lifecycle-aware taint analysis for Android apps](https://www.semanticscholar.org/paper/FlowDroid:-precise-context,-flow,-field,-and-taint-Arzt-Rasthofer/b585c2e102f20a71f1588440470186c49a532dfd)
