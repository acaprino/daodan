# Routing automatico programmatico delle review: ricerca e specifica operativa proposta

Data: 2026-11-07. Stato: report di ricerca con indicazioni di sviluppo; router non implementato e benchmark non eseguito.

Prerequisito: [profilazione e tiering dei modelli dell'harness](harness-model-tiering.md). Quel documento produce candidati qualificati; questo definisce come usarli per un job senza affidare la selezione a un altro LLM.

## TL;DR

1. **Un router senza IA è realizzabile:** filtri di compatibilità e autorizzazione, lookup di qualificazioni empiriche, scelta del costo stimato minimo con tie-break stabile. La qualità della scelta dipende dalla tabella e dalle regole, non dalla loro deterministica esecuzione.
2. **Separare tre decisioni:** quali controlli servono, quali modelli sono qualificati, quale configurazione costa meno per il job. Il roster esistente governa la prima; non va sostituito da una classifica di modelli.
3. **Selezionare modello ed effort insieme**, usando etichette native dell'host. Numero di campioni, limite token, tool budget e reasoning effort sono controlli diversi: i paper non offrono una conversione universale.
4. **La cascata non è gratis:** una seconda review costa anche quando la prima non basta. La mancanza di contesto richiede contesto; zero finding non è un certificato di correttezza; errori di protocollo non sono automaticamente limiti di ragionamento.
5. **Partire da regole e misurare sul nostro task.** Le survey includono ML, LLM judge e bandit; RADAR usa ML e review LLM. Non sono dimostrazioni che una policy a regex o quattro tier universali mantengano la qualità.

## Perimetro e attendibilità

Sono stati consultati i testi primari delle versioni sotto, le sezioni metodologiche e i risultati pertinenti, con appendici mirate. Per R5 è stato letto il PDF di 21 pagine. Per le due survey si distinguono tassonomia e risultati riportati di altri lavori: questi ultimi non diventano repliche indipendenti. Le metriche sono attribuite agli autori; non sono risultati Daodan.

Il documento collega la letteratura al codice presente, ma non costituisce approvazione di una nuova architettura, autorizzazione a cambiare modello o autorizzazione ad automatizzare merge. Le proposte sono un punto di partenza per sviluppo e benchmark, non requisiti già validati dal cliente. Le versioni sono fissate: la scheda di R1 segnala anche una v3 e quella di R3 una v2, non analizzate qui.

## Paper citati

| ID | Paper e versione | Tipo di evidenza | Rilevanza pratica |
|---|---|---|---|
| R1 | Yasmin Moslem, John D. Kelleher. [Dynamic Model Routing and Cascading for Efficient LLM Inference: A Survey](https://arxiv.org/html/2603.04445v2), 2026, arXiv v2. | Survey su selezione fra LLM distinti, non MoE interno a un modello. | Distingue quando si decide, quali segnali si usano e come si calcola la scelta. |
| R2 | Zhiyuan Zhai, Bingcong Li, Bingnan Xiao, Ming Li, Xin Wang. [Adaptive Test-Time Compute Allocation for Reasoning LLMs via Constrained Policy Optimization](https://arxiv.org/html/2604.14853v1), 2026, arXiv v1. | Metodo Solve-then-Learn e benchmark matematici. | Utilità marginale del compute; limiti importanti per una trasposizione deterministica, descritti sotto. |
| R3 | Chris Adams et al. [Automating Low-Risk Code Review at Meta: RADAR, Risk Calibration, and Review Efficiency](https://arxiv.org/html/2605.30208v1), 2026, arXiv v1. | Studio industriale osservazionale di una pipeline di review e landing. | Separare ammissibilità, rischio, review semantica e validazione; non è un router di modelli senza ML. |
| R4 | Junyi Lu, Lili Jiang, Xiaojia Li, Jianbing Fang, Fengjun Zhang, Li Yang, Chun Zuo. [Towards Practical Defect-Focused Automated Code Review](https://arxiv.org/html/2505.17928v2), 2025; [scheda](https://arxiv.org/abs/2505.17928v2) con accettazione Spotlight ICML 2025. [Artifact](https://zenodo.org/records/14779175). | Review C++ su fault report reali, contesto, reviewer multipli e validatore. | Misurare finding e falsi allarmi; qualificare ruoli/configurazioni, non soltanto il modello base. |
| R5 | Ziyu Chen, Qiangpu Chen, Yuwei Li, Taiyan Wang, Shiwen Ou, Qingsong Xie, Lu Zhang, Zulie Pan. [Do LLM Vulnerability-Detection Agents Reason Better? An Empirical Decomposition of Robustness, Resistance, and Grounding](https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.ESEM.2026.28), ESEM 2026, pp. 28:1–28:21. [Replication package dichiarato](https://github.com/cielverse/llm-vuln-agent-reasoning-eval). | Confronti controllati fra contesto, agente, verifica e multi-ruolo su sei modelli. | Non attribuire all'orchestrazione i guadagni del retrieval; valutare robustezza, grounding e costo. |

H4, la survey di Behera et al., e H5, l'esperienza Ericsson, sono letti nel [report sul tiering](harness-model-tiering.md#paper-citati): completano rispettivamente la valutazione dei vincoli operativi e l'integrazione nel workflow. Per R1–R3 non si assume peer review dalla sola disponibilità arXiv. Gli artifact citati non sono stati eseguiti.

## Lettura critica dei paper

### R1 — Una soglia finale non rende l'intero router privo di ML

La tassonomia (§1.4) distingue tre assi: decisione prima/dopo la generazione o multistadio; segnali della query, metadati dei modelli, risposta e feedback; regole, classificatori, bandit o reinforcement learning. È la distinzione più utile per il nostro requisito.

Un router può essere deterministico in esecuzione e dipendere comunque da embedding o predittori appresi. Ad esempio, la survey descrive SCOPE come stima appresa di correttezza/costo seguita da selezione a regole (§5.1). UniRoute aggiunge nuovi modelli valutandoli su cluster esistenti, ma usa rappresentazioni e clustering (§4). Questi non sono equivalenti a una lookup table costruita su famiglie di review dichiarate.

La cascata (§7) decide dopo una prima risposta e deve stimarne l'affidabilità. La confidence verbalizzata non è automaticamente calibrata (§6); la survey riporta anche approcci supervisionati che la migliorano. Nessuna percentuale di risparmio dei metodi citati viene trasferita al nostro plugin.

**Applicazione:** classificazione del job da dati già disponibili, vincoli espliciti, tabella empirica e tie-break stabile. Valutare separatamente la cascata: non aggiungerla solo perché esiste in letteratura.

### R2 — Allocazione del compute: idea utile, controlli e garanzie da non sovrainterpretare

Il paper massimizza l'accuracy attesa sotto un vincolo di costo medio. La fase offline stima utilità per input/budget; una penalità lagrangiana produce azioni-oracolo; un classificatore apprende a predirle. Negli esperimenti (§5.1), il budget è il **numero di risposte campionate** in `{1, 2, 4, 8, 16}`, aggregate per self-consistency, non il parametro API `reasoning_effort`.

Il dataset usa 200 domande MATH e 200 GSM8K; tre backbone e quattro combinazioni modello/dataset. Gli autori raccolgono 48 risposte per domanda, riportando **38.400 chiamate** complessive (Appendice E.4). XGBoost usa 16 feature, inclusa l'entropia ottenuta con una chiamata LLM: quindi non soddisfa il nostro requisito di selezione senza inferenza aggiuntiva.

La Tabella 1 riporta, per DeepSeek-V3 su MATH a budget medio massimo 3, accuracy **0,575** e costo medio **2,73**, contro **0,517** e costo **2,00** di Fixed-b. È un confronto sotto lo stesso tetto, non a identico consumo effettivo. I guadagni non diventano un risparmio garantito in dollari; il costo della feature di entropia va contabilizzato nel nostro eventuale confronto. Le repliche del paper sono su tre seed; l'ablazione pooled di Tabella 2 usa un diverso setting e non va fusa con la tabella principale.

**Limite teorico individuato nella lettura.** L'Appendice C.4 afferma che la rilassazione sulle policy stocastiche ha soltanto vertici deterministici anche dopo l'intersezione con il vincolo di budget. Questo passaggio non vale in generale. Controesempio: un input, costi `1, 2`, utilità `0, 1`, budget `1,5`. La policy deterministica ammissibile ha utilità 0; una miscela al 50% ha costo medio 1,5 e utilità 0,5. L'intersezione introduce un vertice frazionario. Il calcolo è stato verificato localmente con aritmetica razionale, non mediante replica del paper. Inoltre l'Appendice E.3 dichiara esplicitamente mixing stocastico per raggiungere budget esatti.

Questo rilievo limita l'uso della garanzia per il nostro caso discreto deterministico; non dimostra che tutte le misure empiriche siano false. La bisezione su una funzione a gradini non garantisce da sola un'allocazione deterministica che saturi esattamente ogni budget.

**Applicazione:** misurare il beneficio marginale di ogni configurazione; non assumere che più compute aiuti sempre. **Non adottare senza nuova verifica:** la garanzia di ottimalità deterministica, la feature LLM o la conversione campioni→effort. Per pochi candidati è sufficiente enumerare le scelte ammissibili.

### R3 — RADAR: ammissibilità deterministica intorno a componenti appresi

RADAR combina classificazione della sorgente del diff, regole di ammissibilità, Diff Risk Score appreso, review semantica LLM e controlli di validazione (§2). Il DRS è un predittore di esiti negativi, principalmente incidenti in produzione; non è una semplice funzione del numero di righe. La soglia percentile regola quali diff entrano nel flusso, non quale modello LLM viene assegnato.

Il paper riporta oltre **535.000 diff revisionati** e **331.000 landed**, con approve rate del **60,31%** dopo l'ampliamento della soglia. Revert e incident rate sono riportati rispettivamente come 1/3 e 1/50 dei non-RADAR. Questi rapporti non sono effetti causali isolati della review automatica: i diff sono selezionati per rischio, l'assegnazione non è casuale e infrastruttura/policy possono cambiare (§6). La specifica completa del modello difference-in-differences e i dati diff-level non sono pubblicati nel testo.

Il lavoro usa l'espressione «riduzione di oltre 330%» del tempo mediano di chiusura: non è interpretabile come una normale riduzione percentuale di un tempo non negativo. Non viene quindi riutilizzata come misura di efficacia. Servirebbero definizione e denominatore riconciliati.

**Applicazione:** regole chiare di ammissibilità, motivazioni registrate, soglie calibrate per dominio e monitoraggio dei risultati. **Non trasferire:** percentili Meta, confidence LLM ≥8/10 come soglia universale o auto-landing nel nostro plugin. RADAR non prova un tiering automatico dei modelli e non autorizza a saltare controlli obbligatori.

### R4 — Una configurazione di review può cambiare il compromesso precision/recall

Valutazione su **45 fault report reali** di quattro repository C++, con 12 errori logici, 31 di sicurezza e due prestazionali (Appendice K). Si confrontano slicing del contesto, numero e ruoli dei reviewer, meta-reviewer, validatore e prompting. I modelli principali sono open-weight da 70B a 405B; le condizioni di precisione/quantizzazione non sono tutte identiche (Appendici L–N).

Il KBI misura il recupero dei bug chiave. Il FAR conta come rumore i commenti non riferiti al bug del fault report: non coincide con la normale probabilità di falso positivo su codice pulito. Gli stessi autori riconoscono che alcuni commenti così penalizzati potrebbero indicare problemi veri (Appendice V). Il CPI armonizza KBI e complemento del FAR: non sostituisce l'analisi separata di entrambi.

Un confronto pratico (Appendice O, Tabella 10, slicing Left Flow): reviewer Llama-3.1-70B e validatore 405B producono **KBI 17,78, FAR1 55,74, CPI1 25,37**; 405B in entrambi i ruoli produce **20,00, 75,37, 22,07**. Il mix migliora il CPI e riduce il FAR, ma perde recall. Non è un miglioramento su ogni asse e non dimostra un risparmio economico misurato. Il setup inverso non conserva gli stessi risultati.

**Applicazione:** scegliere per job/ruolo, poi verificare anche la combinazione end-to-end. Non assegnare automaticamente lo stesso modello a discovery e verifica per simmetria; non promuovere una combinazione perché massimizza soltanto una metrica aggregata. La numerazione di righe valida agevola la verifica, ma una riga esistente non prova il finding.

### R5 — Prima attribuire il beneficio al contesto, poi all'agente

Il disegno separa prompt singolo (C1), replay delle osservazioni scelte dall'agente (L1), ReAct (C2), self-review (C3), verificatore isolato dalla traccia (C4) e composizione multi-ruolo (C5). Il benchmark principale comprende **150 coppie vulnerabile/corretto**, 300 funzioni, con tre strati di difficoltà e sei modelli. SecVulEval e SV-TrustEval-C forniscono controlli complementari (§§3–4).

Per DeepSeek-V3.2 (Tabella 5), da C1 a C2 l'F1 sale da **0,351 a 0,630**, ma l'accuracy di coppia sale soltanto da **0,068 a 0,122**; L1 è già a **0,116**. Il tasso di predizioni «vulnerabile» sale da **0,270 a 0,805**. Il guadagno aggregato non dimostra quindi un corrispondente miglioramento nel distinguere bug e fix. Per altri modelli la direzione cambia: non è una regola «gli agenti peggiorano sempre».

Le perturbazioni senza cambiamento semantico aumentano il flip rate C1→C2 su cinque modelli su sei (§5.2). Le citazioni di evidenze restano deboli; metriche e denominatori del grounding dipendono dai sottoinsiemi eleggibili (§5.4). L'audit causale di 50 tracce, valutato da un autore, classifica il 30% come causale: supporto esplorativo, non ground truth universale.

La verifica cieca rispetto all'indizio fuorviante riduce il danno nel particolare stress test D2; non significa che qualunque secondo passaggio o modello diverso sia indipendente. Il replay L1 usa contesto selezionato da C2: l'attribuzione è condizionata a quella policy di retrieval. Il suo costo di sola replay **non include il costo necessario a produrre la traccia**. La Tabella 9 mostra per DeepSeek-V3.2 costi medi C1/C2/C4 di **0,003 / 0,026 / 0,044 USD** a campione; confronti trasferibili solo a quello specifico setup.

**Applicazione:** benchmark appaiato, casi corretti, perturbazioni realistiche, prove causali, input indipendenti quando il metodo li richiede e costo dell'intero workflow. Cambiare modello non compensa il passaggio al verificatore della medesima premessa contaminata.

## Confine nel codice del plugin

| Punto attuale | Comportamento verificato | Conseguenza per lo sviluppo |
|---|---|---|
| [review_roster.py](../../plugins/senior-review/skills/review-preparation/scripts/review_roster.py), `compute`, righe 529–677 | Calcola rigore, ruoli, obblighi, segnali, grounding e gap. Soglie per chiamanti/file/moduli e segnali sensibili, non qualità dei modelli. | Riutilizzare segnali e obblighi; non duplicare un secondo analizzatore del diff per assegnare il modello. |
| [composition.py](../../plugins/senior-review/skills/review-preparation/scripts/composition.py), `bind`, righe 75–156 | Produce job con membri, scope, input mode, permessi, candidato e digest. `light` richiede un solo discovery job. | La selezione avviene dopo che il job e il suo contenuto sono noti, prima del dispatch; non cambia numero o membri del roster. |
| [composition.md](../../plugins/senior-review/skills/review-preparation/references/composition.md), sezioni Execute and account | Dispatch attraverso binding isolato dell'host; report e provenienza legati al job; record preparati immutabili. | Collocare la scelta nell'adapter/record del dispatch senza mutare retroattivamente `PREPARED-REVIEW`. |
| [verification-panel.md](../../plugins/senior-review/skills/review-quality-gates/references/verification-panel.md), righe 13–20 | Modello di sessione ereditato; override soltanto esplicito e supportato dal binding. | Prima dell'automazione serve un'estensione opt-in del contratto host. Oggi una funzione di selezione potrebbe solo consigliare, non imporre l'override. |
| [review_roster.py](../../plugins/senior-review/skills/review-preparation/scripts/review_roster.py), `check`, righe 680–694 | Controlla ruolo/obblighi di dispatch e schema, non compatibilità modello/effort. | Aggiungere il controllo della selezione nel punto che governa il dispatch, senza presumere che il check corrente lo faccia già. |

Questi sono punti d'integrazione candidati, non un audit completo dei consumer. Prima di implementare vanno individuati nell'host scelto invocazione effettiva, validatori del record, accounting dei token/costi e comportamento di retry. Il codice host non è stato ispezionato in questo incarico.

## Procedura minima proposta

### Ingressi e uscita

Il router riceve il **job preparato** e i suoi obblighi, i segnali già calcolati, il profilo dei candidati dell'harness, la policy autorizzata e il budget residuo. Per classificare la richiesta usa identificatori di ruolo/membri e dati strutturati, non un LLM che interpreta nuovamente il prompt.

La configurazione è la coppia `(model_id, effort)` nel relativo provider/adapter. La qualifica è legata anche al contratto del job: un profilo di security review non viene applicato automaticamente al premise auditor. Per un job composto occorre coprire tutti i membri richiesti o una composizione specificamente valutata; non basta la specialità più semplice.

L'uscita logica minima è configurazione scelta, riferimento al profilo/policy e motivo, associati al `job_id` già esistente. Se nessuna scelta è possibile, restituisce una ragione distinguibile: incompatibilità, qualità non qualificata, dati insufficienti, vincolo economico o override non autorizzato. Questi sono esiti proposti, non nuovi campi già presenti nello schema.

### Regola di selezione

Per un job `j`, formare l'insieme `A(j)` delle configurazioni che:

1. sono ammesse dalla policy e selezionabili tramite il binding corrente;
2. supportano i requisiti tecnici del job, incluso il contesto necessario;
3. sono qualificate per gli obblighi e la classe di casi del job, con profilo non stale;
4. rispettano i vincoli operativi/economici definiti;
5. conservano isolamento, permessi e obblighi del metodo di review.

Fra queste scegliere il costo totale stimato minimo; a parità usare latenza stimata e infine ID stabili. In forma dichiarativa:

```text
se l'utente ha scelto esplicitamente una configurazione:
    verificare compatibilità e contratto; non sostituirla silenziosamente
altrimenti, se il routing automatico non è autorizzato:
    mantenere l'eredità di sessione prevista dal contratto corrente
altrimenti:
    calcolare A(job) con filtri puramente programmatici
    se A(job) è vuoto: restituire causa e gap, senza dispatch automatico
    scegliere min(A(job), chiave=(costo_stimato, latenza_stimata, provider, modello, variante))
    fissare la decisione nel record di dispatch prima dell'invocazione
```

È pseudocodice di proposta, non implementazione eseguita. L'ereditarietà attuale non va descritta come «modello qualificato» se non esistono misure. Un override esplicito resta una scelta dell'utente e deve mantenere visibili eventuali gap.

La deterministica riproducibilità vale a parità di job, snapshot dei profili, policy, budget e stato disponibile. Se prezzi o disponibilità cambiano, può cambiare la scelta: registrare lo snapshot evita una falsa promessa di output sempre identico.

### Segnali da riusare senza trasformarli in qualità

| Segnale | Uso proposto | Inferenza da evitare |
|---|---|---|
| Ruolo, membri, scope, kind | Identificare le qualificazioni richieste | Un tier globale è adatto a ogni revisore |
| Interfacce, effetti, dipendenze, path sensibili | Selezionare classi di benchmark e requisiti più pertinenti | Una regex dimostra presenza/assenza di un difetto |
| Numero file/moduli/chiamanti | Descrivere il contesto e attivare regole già calibrate | Un diff lungo è necessariamente difficile; un diff corto è sicuro |
| Gap del contesto | Richiedere evidenza o mantenere review incompleta | Aumentare effort crea le informazioni mancanti |
| Input stimato, prezzi, latenza | Filtrare compatibilità e ordinare gli idonei | Modello costoso o contesto grande implica migliore recall |

Non servono tutti i segnali in ogni job. Partire dai campi già disponibili e aggiungere una feature soltanto se un benchmark mostra un errore di routing che risolve.

### Costo, budget e concorrenza

Stimare input/output, cache solo se effettivamente applicabile, reasoning fatturato secondo il provider, tool e retry. Registrare poi il consumo osservato separatamente dalla stima. L'effort non è un moltiplicatore di costo universale.

Un costo medio atteso non garantisce un tetto rigido. Se il contratto richiede un limite di spesa, devono esistere limiti enforceable dell'host e una stima conservativa/reserva; se mancano, dichiarare il limite non garantibile anziché inventare un prezzo massimo. Prezzo sconosciuto non equivale a costo zero.

Nel dispatch parallelo, non lasciare che due job leggano lo stesso budget residuo e lo consumino entrambi. Riutilizzare il ledger/accounting dell'host per una prenotazione atomica e riconciliare il consumo alla fine, con `job_id` come identità per evitare doppi addebiti logici. È un requisito dell'eventuale integrazione, non un nuovo servizio da costruire se l'host lo offre già.

### Escalation: trigger distinti, nessuna scala automatica universale

| Evento | Azione proposta | Limite |
|---|---|---|
| Tool/schema fallito | Retry limitato o configurazione compatibile secondo policy | Tenere distinto il fallimento di protocollo dal mancato rilevamento del bug |
| Contesto mancante o troncato | Recuperare contesto pertinente o mantenere un gap | Più effort non ripara una premessa assente |
| Modello temporaneamente indisponibile | Fallback qualificato per gli stessi obblighi, se autorizzato | Non usare un modello inferiore solo perché risponde |
| Critico/verifica segnala copertura incompleta | Applicare il requisito esistente e rivalutare risorse/contesto | Non eliminare lens, membri o indipendenza per rientrare nel budget |
| Nessun finding o confidence alta | Nessuna chiusura speciale basata soltanto su questi segnali | Un output vuoto può essere un falso negativo; la confidence richiede calibrazione |

Un'eventuale cascata deve avere un massimo di tentativi e un budget totale, confrontati con la selezione diretta. In `light` non introdurre un secondo discovery job nascosto; se il lavoro richiede più job si applica il passaggio esplicito alla modalità prevista dal metodo. Un retry deve restare tracciato e non fingere che due esecuzioni siano una sola misura.

## Materiale pratico da portare nello sviluppo

### Cinque interventi circoscritti

1. **Adapter di discovery dell'host iniziale.** Tradurre il catalogo reale senza indovinare varianti o limiti; riusare identità e autenticazione del runner. Test: paginazione, nomi omonimi fra provider, prezzo assente, alias automatico, capacità unknown.
2. **Profili empirici condivisi.** Usare le fixture e il modello dati del [report tiering](harness-model-tiering.md#benchmark-da-preparare). Test: un profilo con prompt/tool/provider diverso non qualifica silenziosamente il job corrente.
3. **Funzione pura di selezione.** Input strutturato, nessuna rete e nessun LLM. Testare filtro degli obblighi, minimo di costo, tie-break, nessun candidato e selezione esplicita dell'utente. Non sostituire `review_roster.compute`.
4. **Binding e accounting.** In modalità opt-in autorizzata, applicare modello/effort effettivamente supportati; registrare decisione prima della chiamata e consumo dopo. Test: parametro rifiutato/ignorato, job concorrenti, retry e record preparato immutabile.
5. **Replay e confronto end-to-end.** Confrontare la policy con configurazioni fisse e attuale eredità di sessione; misurare qualità e costo inclusi tool, verifica e retry. Adottare solo una policy che soddisfa criteri scelti prima del test finale.

Questo ordine definisce dipendenze tecniche, non un piano approvato né una stima di consegna. Nessuna nuova dipendenza ML è necessaria per l'MVP proposto; eventuali predittori appresi devono giustificarsi rispetto alla baseline semplice.

### Benchmark del router

Usare lo stesso percorso proposto `benchmarks/model-routing/`, senza duplicare il corpus di qualificazione. Separare due livelli di prova:

| Livello | Confronto | Che cosa dimostra |
|---|---|---|
| Unit/replay senza modelli | Profili sintetici e poi esiti registrati; stessa policy/input produce la stessa scelta | Correttezza delle regole, compatibilità, gestione del budget e riproducibilità; non qualità dei finding |
| Review reali held-out | Stessi casi, configurazione fissa economica qualificata, fissa più capace qualificata, eredità attuale e router | Trade-off effettivo su difetti, rumore, costo e latenza nel nostro harness |

Un oracolo che sceglie a posteriori il risultato corretto più economico può essere riportato come **limite superiore sperimentale**, non come policy implementabile: conosce le risposte. Il replay del contesto R5 può isolare l'effetto di una configurazione, ma il benchmark economico deve addebitare anche la costruzione di quel contesto.

Misurare recall per famiglia/severità, precision dei finding confermati, falsi allarmi sui casi puliti, accuracy delle coppie bug/fix, failure rate di protocollo e completamento degli obblighi. Contare separatamente errori operativi, casi mancanti e finding non adjudicati; non escludere i fallimenti per far apparire migliore il router. Riportare costo totale e latenza end-to-end, con code/parallelismo esplicitati e percentili solo se la numerosità li rende sensati.

Usare split per repository o famiglie di difetto e mantenere insieme bug/fix e varianti della stessa fixture. Selezionare soglie su calibrazione, congelarle, poi valutare l'held-out. Una modifica delle soglie dopo aver visto il test richiede un nuovo test non contaminato. Le repliche misurano variabilità, non ampliano il numero dei difetti indipendenti.

### Criteri di accettazione osservabili proposti

| Requisito | Prova |
|---|---|
| Il router non usa IA per scegliere | Esecuzione con rete e invocazioni modello disabilitate, profili già disponibili |
| Nessuna perdita di obblighi | Membri, scope, permessi, isolamento e verifiche identici prima/dopo la scelta |
| Unknown non equivale a supportato | Caso con requisito tool/context senza evidenza non entra in selezione automatica |
| Nessun override silenzioso | Modalità default conserva il contratto di sessione; override solo con policy autorizzata |
| Qualità/costo dimostrati separatamente | Risultati held-out con soglie e margini prestabiliti, denominatori e intervalli; risparmio non ottenuto omettendo controlli |

Valori di recall minimo, margine di non inferiorità, massimo rumore e budget non sono fissati da questi paper: sono decisioni da prendere per la prima famiglia di review. Il documento non inventa un obiettivo numerico di prodotto.

## Conclusione e verifiche

La soluzione minima sostenibile è **roster esistente → job preparato → filtri su profili misurati → scelta modello/effort → dispatch autorizzato → verifica e accounting esistenti**. Il tier numerico è opzionale per la decisione; serve soltanto se comprime qualificazioni reali senza nascondere differenze fra domini.

Sono stati ispezionati roster, composizione e contratti locali citati, consultati i paper delle due selezioni e verificato il controesempio razionale alla rilassazione di R2. Non sono stati riprodotti i benchmark degli autori, auditati i loro repository o provati dispatch/billing/modelli dell'harness. Le incongruenze rilevate nelle fonti sono riportate, non risolte per supposizione.

Prima di implementare resta da scegliere l'host iniziale e autorizzare l'estensione del binding, definire la prima famiglia di review e i criteri di qualità. Il materiale pratico sopra permette di sviluppare e mettere alla prova l'ipotesi; non prova ancora che il router risparmi mantenendo il recall nel nostro plugin.

Prossima decisione: fissare un solo host e una sola famiglia di review per il primo benchmark, mantenendo l'attuale eredità di sessione come baseline.
