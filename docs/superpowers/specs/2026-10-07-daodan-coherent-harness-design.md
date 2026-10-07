# Daodan: ristrutturazione come harness coerente

Data: 7 ottobre 2026. Disegno di attuazione della ristrutturazione completa delegata dall'utente. La distribuzione resta pubblica, neutrale e costruita da kernel e adapter per cinque host.

## 1. Intento e promessa del prodotto

Daodan accompagna lo sviluppo di un progetto con IA e si prende carico delle conseguenze del lavoro. Ogni intervento lascia il progetto coerente, verificabile e comprensibile, in proporzione al suo impatto: comportamento, codice, test, conoscenza e artefatti devono continuare ad accordarsi.

I problemi centrali sono frammentazione della conoscenza, decisioni contraddittorie, duplicazione, dead code, test inutili o errati e residui delle prove. Il prodotto offre un percorso per recuperare un progetto e uno per evitare di degradarlo durante lo sviluppo. Non misura il successo con il numero di test, documenti, agenti o file eliminati.

Tri-Tech Code è un consumatore esterno dei pacchetti OpenCode V2. Non è un sesto adapter. Un motore persistente del desktop può usare le identità e i risultati delle run; i permessi per una radice privata dell'app devono essere provati nell'integrazione del desktop. La prima distribuzione usa una radice di artefatti dentro il progetto.

## 2. Diagnosi verificata e materiale di partenza

L'inventario dei manifest prima della migrazione conta 40 plugin, 76 ruoli, 59 skill e 58 workflow. 55 sidecar dichiarano un solo esito; 57 hanno schemi vuoti. Questi conteggi descrivono il catalogo, senza dimostrarne la qualità.

Tre plugin possiedono oggi istruzioni, guide e README. La review generale trascina React, TypeScript e piattaforma anche nell'installazione della documentazione. Il writer Python e il suo metodo TDD duplicano il testing comune con quote di test e coverage arbitrarie. Il mapper produce un pacchetto documentale fisso anche quando sono già presenti documenti autorevoli. Le operazioni che modificano hanno criteri di rollback e gate diversi.

La prova manuale riferita dall'utente ha composto cinque auditor esistenti senza prompt nuovi. Ha mostrato il valore di un piano trasversale e il costo di una diagnosi non proporzionata. Il consumo riferito di circa 1,4 milioni di token in circa trenta minuti, senza X-ray, è un'esperienza di quella sessione, non un benchmark dei cinque host. Le lacune emerse riguardano runner o suite assenti, pulizia dei segreti, directory di piani non riconosciute e gate non collegati alla revisione candidata.

Difetti da correggere nella migrazione: Step 7c esegue il gate prima del commit ma ripristina HEAD~1; clean-code può perdere modifiche preesistenti usando git restore; X-ray propone modifiche rapide incompatibili con il proprio confinamento; marketplace-ops prescrive ancora il layout precedente e la registrazione manuale dei cataloghi generati.

La [ricerca su test, conoscenza e residui](../../../research/2026-10-07-coerenza-progetti-ai-test-e-residui.md) informa i criteri, senza dimostrare una prevalenza statistica del disordine attribuibile all'IA.

## 3. Architettura e composizione

Il nucleo distingue governo dell'incarico, proprietà dei metodi e specializzazioni. I plugin conservano autonomia; il lifecycle prepara gli input, dispaccia gli stessi ruoli e applica gli stessi metodi dei comandi specialistici. Non contiene una seconda raccolta di prompt di rilevazione.

Il riuso segue quattro gradini: riusare così com'è; spostare il metodo presso il proprietario; migliorarlo quando un caso concreto lo richiede; scrivere solo la capacità assente. Nessun componente è intoccabile per il solo fatto di esistere.

La composizione ordinaria usa skill caricabili e ruoli dichiarati. La sola invocazione di un altro workflow è l'analisi X-ray nel contesto del coordinatore, già presente nella Phase 1a di team-review. Questo precedente resta un obbligo da provare nei pacchetti installati sui cinque host. Il compilatore rifiuta invoke finché non esiste un executor verificato.

Le fasi con ruolo di un altro kernel devono essere validate contro l'inventario globale e renderizzate con il binding dell'adapter. La sintassi neutrale dei sidecar è plugin/role; l'identità pubblica dei contenuti è plugin:component. Un riferimento non risolto fallisce la compilazione. I wrapper di un host non possono presumere che tutti i ruoli si trovino nel pacchetto del coordinatore.

## 4. Proprietà e catalogo

| Proprietario | Responsabilità canonica |
|---|---|
| project-lifecycle | Obiettivo, ambito, costo, piano, dispatch, esecuzione generale e chiusura |
| project-protocol | Identità e stato della run, snapshot, consegne, verifica e annullamento comuni |
| project-knowledge | Istruzioni durevoli, guide, README e integrazione delle conclusioni |
| senior-review | Correttezza, reviewer universali, validazione dei finding e sottrazione applicativa |
| review-plus | Orchestrazione della review estesa con React, TypeScript e piattaforma |
| testing | Oracoli, diagnosi, authoring, quarantena e conservazione della protezione |
| abstraction-architect | Diagnosi di duplicazione, concept index e criteri di design |
| codebase-xray | Evidenze statiche e interconnessioni; nessuna modifica applicativa |
| repo-hygiene | Stato filesystem/Git e operazioni reversibili, ancora foglia |
| clean-code | Leggibilità con comportamento conservato |
| text-humanizer | Voce dei testi e rimozione dei pattern artificiali |

project-protocol è un plugin foglia. I contratti canonici sono nel suo contracts/; il manifest dichiara gli export, il compilatore li valida e li distribuisce. La skill spiega l'uso, senza ospitare copie degli schemi. Il record work e l'envelope project-result sono operativi dalla prima run; non si rinviano ripresa, stati o revisioni a una generalizzazione futura.

I sette contratti di team-review restano schemi di dominio di senior-review. Non vengono ridenominati in uno schema universale dei finding. project-result contiene contabilizzazione e riferimenti ai payload specialistici, senza ridefinirne finding, severità o disposizioni. Il protocollo comune non sostituisce il payload del proprietario. Un'integrazione che richiede uno schema esportato lo dichiara attraverso shared_schemas, senza copiare i campi.

senior-review perde le tre dipendenze di dominio e conserva X-ray, abstraction, testing e repo-hygiene. review-plus dipende obbligatoriamente da senior-review, React, TypeScript e platform-engineering e aggiunge soltanto il dispatch specialistico ai metodi canonici. La copertura degli ingressi senior diventa esplicitamente universale; chi vuole la copertura precedente completa usa review-plus. Non si introducono dipendenze locali opzionali.

project-knowledge sostituisce codebase-mapper, project-setup e docs. Offre instructions, guide, maintain e readme. La guida aggiorna prima i documenti esistenti; i destinatari e il piano dei file precedono la scrittura. Il pacchetto completo si produce quando richiesto. config-writer confluisce in ops-writer; onboarding conserva la prospettiva del nuovo collaboratore. doc-humanizer possiede struttura e navigazione, text-humanizer la voce. Si ritirano quote di domande e sezioni vuote obbligatorie.

testing è il solo proprietario delle regole universali di test. Il metodo TDD effettivo resta quello upstream dichiarato. python-development ritira python-test-engineer e trasforma python-tdd in pytest-patterns: fixture, async, mock, configurazione e tecniche Python restano disponibili. Il writer canonico usa il contesto fornito dal richiedente. Non si introduce un ciclo di dipendenze testing verso Python.

Gli extra restano prodotti autonomi. Il lifecycle può acquisire un loro risultato come input; un dispatch automatico di un extra richiede un consumatore con la dipendenza obbligatoria dichiarata. Il nucleo non porta con sé trading, marketing, RAG o tutti i framework.

Costo del nucleo ricalcolato sui manifest finali, contando la radice e project-protocol: project-lifecycle comprende dieci plugin locali e tre esterni; project-knowledge otto locali e due esterni; senior-review sei locali e due esterni; review-plus dieci locali e due esterni. Sono chiusure dichiarative, non stime di byte o token. La disponibilità degli upstream su un host va verificata prima del metodo che li usa.

## 5. Cinque percorsi completi

| Ingresso | Obiettivo e risultato |
|---|---|
| assess | Rilevare incoerenze con gli auditor esistenti e produrre un piano motivato, con proprietari, dipendenze, copertura e limiti |
| repair | Applicare un piano identificato alla revisione validata e verificare ogni rimedio, conservando fasi aperte e decisioni mancanti |
| change | Bootstrap, feature, bugfix, refactor o migrazione attraverso scoperta, intenzione, piano proporzionato, authoring e chiusura |
| verify | Verificare lo snapshot candidato e le conseguenze fuori dal diff; distinguere verifiche passate, fallite e non eseguite |
| consolidate | Ridurre prove e output a conclusioni verificate, integrare conoscenza durevole e applicare retention agli artefatti posseduti |

La ripresa usa l'identità esatta della run, non un secondo workflow. Ingressi specialistici e cinque percorsi usano gli stessi metodi.

assess prepara scope, intenzione, test runner, inventario workspace e contesto strutturale; dispaccia cleanup-auditor, test-suite-auditor, abstraction-architect-agent, instructions-auditor e workspace-auditor secondo il focus. Gli audit documentali aggiungono il metodo knowledge. Una selezione vuota è una dimensione non richiesta, non una consegna mancata. Gli stati assente, fallito, non eseguibile e non coperto sono distinti.

assess studia coerenza e produce un piano; team-review studia correttezza e produce finding validati. Condividono auditor, evidenze e indipendenza delle premesse. Un audit non diventa una prova runtime.

Il focus all non autorizza una scansione senza limite. La preparazione espone ruoli, profondità, ripetizioni e costo osservabile; usa una sola passata iniziale e riusa solo consegne ancora valide per gli stessi input. Consumo token ignoto rimane ignoto. Limiti dichiarati nel prompt non vengono presentati come enforcement meccanico dell'host.

repair associa ogni finding a un metodo. Le ambiguità di design restano decisioni concrete; i refactor con intenzione nota possono essere eseguiti attraverso change e verificati dall'auditor delle astrazioni. Cleanup non diventa refactor. Un'azione che richiede commit lo dichiara già nel piano assess.

change include l'avvio del progetto e riusa i metodi upstream di discovery, piano ed esecuzione quando pertinenti. Prima cerca implementazioni e test esistenti. Il base model può implementare una modifica senza installare ogni specialista. Gli extra sono percorsi autonomi o composizioni dichiarate.

verify lega ogni gate allo snapshot candidato, comprese modifiche non committate. Un job remoto verde su una revisione precedente non verifica la modifica. Se il gate richiede pubblicazione, autorizzazione e ordine commit/push/gate devono essere dichiarati; l'annullamento di un commit pubblicato usa revert.

consolidate richiede obiettivo, revisione, condizioni, tentativi, errori, esiti, decisioni, limiti e ripetibilità. Verifica il report contro le evidenze necessarie. Un risultato passato non sostituisce un test che protegge il comportamento futuro. Lo stato temporaneo rimane nella run; le conclusioni durevoli passano a knowledge.

## 6. Contratto comune di lavoro

Ogni incarico coordinato registra solo quanto serve per eseguirlo, verificarlo e riprenderlo:

- Obiettivo e comportamento richiesto, con fonte dell'intenzione o ambiguità dichiarata.
- Ambito, revisione e impronta dei file coinvolti, comprese le modifiche non committate.
- Vincoli e autorizzazioni già ricevuti dall'utente.
- Piano con dipendenze fra interventi e proprietario di ciascuno.
- Evidenze consultate e distinzione fra fatti verificati, inferenze e informazioni ereditate.
- Disposizioni motivate: mantenere, correggere, accorpare, ritirare o lasciare da chiarire.
- Verifiche eseguite, fallite o non eseguibili e relativo ambito.
- Problemi ancora aperti e materiale necessario per riprendere il lavoro.

Ogni specialista restituisce un esito strutturato con ambito, revisione, stato, evidenze, risultati e limiti. Il coordinatore verifica i campi e i riferimenti, contabilizza le consegne e risolve i duplicati per comportamento o problema. Una consegna mancante resta mancante. Due reviewer che ereditano la stessa premessa non costituiscono due conferme indipendenti.

Gli schemi possono verificare struttura e consistenza dei record. La correttezza semantica richiede letture, strumenti, esecuzioni e decisioni umane quando l'intenzione non è ricostruibile.

## 7. Regole condivise da rendere operative

1. Cercare materiale e implementazioni pertinenti prima di aggiungerne di nuovi.
2. Confrontare ciò che una modifica rende obsoleto anche nei file non modificati.
3. Distinguere test errato, difetto nel prodotto, problema di ambiente e flakiness prima di proporre una quarantena. Escludere un test non corregge un difetto.
4. Motivare la rimozione di una verifica con il requisito ritirato o la protezione equivalente conservata. Copertura, numero di test ed età restano segnali.
5. Conservare risultati delle prove, condizioni, errori e limiti prima di disporre degli output. Un riassunto deve essere verificato contro le evidenze necessarie.
6. Distinguere dati rigenerabili, cache riutilizzabili, evidenze di problemi irrisolti e residui conclusi.
7. Riesaminare gli esiti interessati quando cambiano i relativi input, evitando di trattare un vecchio report come conoscenza corrente.
8. Tenere lo stato delle esecuzioni separato dalle istruzioni durevoli. AGENTS.md e CLAUDE.md non diventano registri di sessione.

L'interfaccia comune proposta distingue `--dry-run`, `--fix` e `--commit`: anteprima, modifica con verifica senza commit, modifica con commit autorizzati. Questa uniformità richiede una migrazione esplicita dei metodi attuali. Il nuovo coordinatore deve rispettare i loro vincoli finché la migrazione non è completata: il cleanup applicativo di Step 7c richiede `--commit`, e i workflow dei test hanno gate propri. Le fasi incompatibili con l'autorizzazione ricevuta restano aperte, con il motivo.

Le autorizzazioni persistono nel loro ambito e non vengono richieste nuovamente a ogni passaggio. Le decisioni mancanti riguardano risultati concreti e revisionabili. Il piano non autorizza rimozioni prive di evidenza o operazioni fuori ambito. La quarantena di untracked e il Git-state detection-only di `repo-hygiene` restano vincoli del proprietario.

## 8. Protocollo, artefatti e sicurezza operativa

La destinazione predefinita è .daodan/runs/<id>/ nel progetto. La radice ha un sentinel .daodan-root. Una destinazione alternativa deve essere una directory dedicata dentro il progetto; le radici private esterne dell'app sono dichiarate non supportate dalla prima integrazione. I permessi OpenCode non vengono dedotti dalla possibilità di leggere il pacchetto installato.

Ogni run possiede work.json, result.json, rapporti dei worker e riferimenti a prove esterne. work.json identifica progetto, worktree, HEAD, snapshot dei file interessati, obiettivo, scope, autorizzazioni, budget, fasi, piano e consegne. La versione del record e la sua revisione sono esplicite. Gli aggiornamenti sono atomici e rifiutano una revisione superata. Riprendere richiede identità, input e autorizzazioni ancora validi.

Gli stati riusano il vocabolario operativo di team-review: pending, running, delivered e failed per le consegne; le transizioni della run e le interruzioni sono specificate nel protocollo. Una run completa non contiene consegne mancanti o gate richiesti non contabilizzati. Il risultato può dichiarare limiti, ma non rinomina il fallimento in successo.

Gli helper confinano meccanicamente le proprie scritture. Il confinamento degli altri tool dell'agente rimane un obbligo del prompt su tutti e cinque gli host: non esiste ancora un hook del lifecycle collegato. Anche xray-guard è un'implementazione Copilot presente nel repository senza prova di collegamento al runtime. Le due garanzie non vengono confuse.

repo-hygiene C5 riconosce .daodan/ e radici con sentinel soltanto per nome/presenza e non ne propone la rimozione. Non legge work.json né interpreta gli stati delle run. La classificazione della retention appartiene a consolidate. Il convertitore del report tidy mantiene i sette esiti nativi e li affianca alle cinque decisioni del piano; un test di contratto impedisce divergenze.

Gate e rollback condividono una procedura: worktree posseduto esclusivamente, baseline esplicita, SHA pre-fase, snapshot candidato, gate, commit quando autorizzato. Il fallimento prima del commit ripristina il proprio stato pre-fase, senza annullare la fase riuscita precedente. Modifiche preesistenti e file creati da altre sessioni non si eliminano. Le operazioni senza baseline affidabile rimangono aperte.

La retention distingue dati di ripresa, problemi irrisolti, prove necessarie, cache e output rigenerabili conclusi. L'anteprima elenca percorsi, motivi e byte. La quarantena conserva i file e libera zero byte sulla stessa unità. La cancellazione permanente è una capacità distinta, con flag --purge e autorizzazione esplicita di artefatti effimeri posseduti, report verificato, manifest dei percorsi e nessun riferimento irrisolto. Non deriva dalle autorizzazioni di tidy. Si rifiutano link, percorsi esterni e file cambiati dopo il piano.

## 9. Attuazione e verifica

L'ordine autorevole della migrazione è questo:

1. Rendere reale il dispatch cross-plugin, rifiutare invoke e distribuire gli export dei contratti. Creare il protocollo minimo operativo con helper stdlib, record versionati e gate comuni.
2. Separare review universale ed estesa, promuovere cleanup e consolidamento canonici; correggere rollback, gates e igiene dei test. Riutilizzare le diagnosi esistenti.
3. Migrare la conoscenza una sola volta nel proprietario finale. Rendere caricabili preparazione e audit, ritirare namespace e writer duplicati e aggiornare i consumatori.
4. Implementare i cinque ingressi lifecycle con focus, piano, ripresa, risultati e retention. Consolidate è una capacità nuova; la ricerca web non viene trasformata in un executor locale.
5. Allineare Python, readability, X-ray, marketplace-ops e documentazione. Ricostruire tutti i pacchetti, cataloghi e istruzioni Codex, con bump di release maggiore.
6. Eseguire controlli di compilazione, contratti, regressioni operative ed eval comportamentali. Effettuare una review dell'intero cambiamento, includendo consumer non toccati.
7. Distinguere la verifica dei pacchetti generati dalle prove in sessioni installate. Registrare le prove host non disponibili come non eseguite; non promettere cinque esecuzioni verificate dalla sola compilazione.

I piani di implementazione nominano file, interfacce, prove e ownership. La migrazione cambia i nomi in corpi, sidecar, dipendenze, linter, fact anchor, eval, docs/plugins, README e CLAUDE.md. Le copie Codex e gli export sono rigenerati. Gli ID ritirati compaiono soltanto nella guida di migrazione e nella storia, senza wrapper permanenti che mantengano due contratti.

## 10. Criteri di valutazione

| Caso rappresentativo | Comportamento da osservare |
|---|---|
| Una feature ha già implementazione e test | Il percorso trova il materiale e lo estende dove appropriato |
| Un test codifica un bug corrente | L'aspettativa viene confrontata con il requisito; il risultato non diventa affidabile attraverso la sola esclusione |
| Due test sembrano duplicati ma proteggono failure mode diversi | La differenza viene conservata e spiegata |
| Un refactor lascia invariato il comportamento | La protezione resta valida; il cambio di struttura non giustifica da solo il ritiro dei test |
| Una modifica contraddice un documento non toccato | Il percorso identifica la conseguenza oltre il diff |
| Una campagna produce output pesanti e risultati utili | Il consolidamento conserva risultati verificati e provenienza; il report distingue byte spostati ed eliminati |
| Un residuo ha funzione o provenienza incerta | Rimane da chiarire e non viene dichiarato inutile |
| La run è interrotta o un worker non consegna | Stato e limiti restano ricostruibili; il risultato non viene presentato completo |

Gli eval misurano comportamenti su progetti campione, con versioni identificate e sessioni nuove. Le prove sui corpi delle skill e quelle sul pacchetto installato sono evidenze distinte. Il giudice non riceve la soluzione dal worker; la condivisione delle premesse è dichiarata. I test del compilatore verificano distribuzione e contratti strutturali, mentre gli eval verificano il metodo.

La prima implementazione è riuscita quando il percorso `assess` e `repair` produce interventi motivati e verificati, mantiene la protezione significativa e rende leggibili problemi aperti e conseguenze. Il numero di plugin o di file rimossi non è il criterio di riuscita.

## 11. Destino dell'intero catalogo

| Plugin iniziale | Destino |
|---|---|
| abstraction-architect | Nucleo: diagnosi e design |
| ai-tooling | Extra: prompt e SDK |
| app-analyzer | Extra: analisi di applicazioni |
| browser-extensions | Extra: Firefox |
| business | Extra: business e documenti legali |
| clean-code | Nucleo: leggibilità |
| codebase-mapper | Migra in project-knowledge |
| codebase-xray | Nucleo: analisi statica |
| csp | Extra: solver |
| dependency-audit | Extra trasversale: dipendenze e vulnerabilità |
| digital-marketing | Extra: marketing e analytics |
| docker | Extra: immagini e packaging |
| docs | Migra in project-knowledge |
| frontend-review | Extra: UX e frontend |
| grabber-development | Extra: scraping |
| kotlin-development | Extra: Kotlin |
| learning | Extra: mappe per apprendimento |
| libgdx-development | Extra: LibGDX |
| marketplace-ops | Extra: manutenzione marketplace, riallineato ai kernel |
| messaging | Extra: RabbitMQ |
| obsidian-development | Extra: Obsidian |
| opentelemetry | Extra: osservabilità |
| peer-review | Extra: deliberazione fra modelli |
| platform-engineering | Extra: piattaforma, consumato da review-plus |
| project-setup | Migra in project-knowledge |
| pwa-expert | Extra: PWA |
| python-development | Extra: Python; test universali passano a testing |
| rag-development | Extra: RAG e Qdrant |
| react-development | Extra: React, consumato da review-plus |
| repo-hygiene | Nucleo foglia: filesystem e Git |
| research | Extra trasversale: ricerca verificata |
| senior-review | Nucleo: review universale |
| stripe | Extra: Stripe |
| system-utils | Extra: file personali; repository attivi al proprietario repo |
| tauri-development | Extra: Tauri e Rust |
| testing | Nucleo: protezione comportamentale |
| text-humanizer | Foglia: voce dei testi |
| trading-broker-integration | Extra: trading |
| typescript-development | Extra: TypeScript, consumato da review-plus |
| xterm | Extra: terminali |
| project-lifecycle (nuovo) | I cinque percorsi completi |
| project-protocol (nuovo) | Contratti e garanzie operative |
| project-knowledge (nuovo) | Conoscenza del progetto |
| review-plus (nuovo) | Review specialistica estesa |
