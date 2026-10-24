> Stato: proposta storica. Fa fede [Reviewer specializzati e composti](2026-10-22-specialized-reviewers-design.md): prima specialisti canonici, poi reviewer ampi generati dalla loro unione, riusando il registro esistente. Le strutture aggiuntive qui proposte non sono requisiti impliciti.

# Riorganizzazione dei reviewer: identità, nuclei, moduli e migrazione

Data: 22 ottobre 2026. Stato: **Proposto per revisione**.
Questo documento specifica comportamento futuro; non attesta implementazione, qualifica o disponibilità dei nuovi componenti.
La richiesta autorizza la redazione delle specifiche. L'implementazione e la pubblicazione hanno un percorso successivo.

## 1. Scopo, fonti e decisioni vincolanti

Questa specifica governa la riorganizzazione dei 18 ruoli e dei due method binding di review oggi compilati da `scripts/daodan/reviewer_catalog.py`.
Governa inoltre il nuovo `senior-review:accessibility-auditor` e tre moduli di copertura resi espliciti dalla riorganizzazione.
La decisione confermata è mantenere ruoli permanenti e comporre per ogni review i controlli pertinenti al candidato.
La copertura dei requisiti e delle failure mode precede l'ottimizzazione economica.

Documenti coordinati:

- [Disegno del sistema di review](2026-10-22-review-system-redesign-design.md): processo complessivo e responsabilità del coordinatore.
- [Authoring e catalogo](2026-10-22-reviewer-authoring-catalog-design.md): vocabolario, scrittura, promozione e backlog dei moduli.
- [Composizione e verifica](2026-10-22-review-composition-verification-design.md): piano, identità, selezione, consegne, gate e ripresa.
- [Analisi di impatto](../reports/2026-10-22-review-composer-impact-analysis.md): osservazioni sul candidato e motivazioni del cambiamento.

La baseline locale osservata è `849797acbf8aaae74f23b55ce30710dc599c89bb`, con modifiche preesistenti nel workspace.
Gli allegati del composer dichiarano una baseline distinta, `e7583329e7ab59596a091fba27e4af705912d731`.
Il loro stato di implementazione non viene trasferito implicitamente al checkout locale.
I 50 temi dichiarati storici negli allegati costituiscono materiale di backlog; questa specifica non ne ripete la tassonomia né presume approvazioni non presenti nella richiesta.

Decisioni:

1. Si conservano tutte le identità registrate dei 18 ruoli e dei due method binding esistenti.
2. Si aggiunge un solo ruolo permanente: `senior-review:accessibility-auditor`.
3. `code-concurrency` e `code-general-performance` appartengono a `senior-review:code-auditor`.
4. `interaction-critical-paths` appartiene a `senior-review:accessibility-auditor`.
5. La prima iterazione integrata usa composition v2 e aggrega soltanto stesso owner, stessa lente e stessa modalità di input, rispettando i vincoli di indipendenza.
6. Un job non esegue moduli di un altro owner. Il packing cross-owner rimane fuori da questa versione.
7. Ogni profilo permanente espone nucleo, moduli ammessi e percorso standalone completo.
8. L'abilitazione del profilo compatto richiede migrazione degli obblighi e qualifica; aggiungere un link non riduce il metodo caricato.
9. Discovery, derivazione cieca, verifica di finding, claim check dei testi e completeness critic hanno percorsi distinti.
10. Una consegna senza finding è valida quando le assegnazioni sono state esaminate e i limiti sono dichiarati.

## 2. Modello degli oggetti e proprietà canoniche

| Oggetto | Definizione normativa | Proprietario |
|---|---|---|
| Owner | Responsabile del significato di una famiglia di controlli, delle esclusioni e del metodo | Plugin che possiede il ruolo o il metodo |
| Profilo permanente | Identità esecutiva registrata, nucleo, moduli consentiti, modalità e prerequisiti | Owner, proiettato dal compiler nel catalogo |
| Nucleo | Mandato, regole comuni di prova, input, limiti, consegna e controlli realmente universali | Owner |
| Modulo | Domanda selezionabile con attivazione, percorso di analisi, evidenza, controevidenza e limite delle conclusioni | Un solo owner canonico |
| Preset | Selezione dichiarata per un'invocazione diretta o per una forma di review | Metodo del consumer con riferimenti canonici |
| Job | Istanza isolata di un profilo su coppie scope/modulo, candidato, binding e report assegnati | Coordinatore del run |
| Obbligo | Comportamento osservabile richiesto dal metodo precedente o dal nuovo requisito approvato | Owner nella matrice di migrazione |
| Evidenza | Sorgente, configurazione, risultato di tool o prova runtime ammessa e identificata | Evidence pack del candidato |

Markdown resta la fonte del comportamento. I metadata dichiarano identità, compatibilità, selettori e riferimenti.
Il compiler costruisce la vista portabile dei profili; il runtime legge quella vista e verifica la disponibilità effettiva sull'host.
La presenza nel catalogo non equivale a installazione, dispatch riuscito o capacità esercitata.
Il coordinatore non cerca corpi di ruoli nei kernel di una checkout al momento della review installata.
I riferimenti fra provider passano da skill e contratti dichiarati, senza leggere file privati di altri plugin.

Il registro proposto `daodan/review-profiles/v1` deve rappresentare, per ogni identità:

- `id`, `kind`, provider, versione e binding nativo per host;
- lente, modalità ammesse e permessi effettivamente richiesti;
- riferimento e fingerprint del nucleo;
- moduli ammessi e relativi fingerprint, incluse reference obbligatorie;
- prerequisiti per modalità, input consentiti ed esclusioni;
- preset standalone e regole di preparazione quando la selezione non è fornita;
- stato `atomic`, `compact-qualified` o `deprecated-compatible` e provenienza della qualifica.

Il registro si integra con context/modules/composition v2 e con work/project-result v2 del processo principale.
I campi sono un'estensione da implementare nel contratto del catalogo e del loader.
Il catalogo v1 corrente non viene interpretato come se già esponesse questi dati.
La migrazione di schema deve mantenere leggibili le vecchie registrazioni e identificare esplicitamente il nuovo pacchetto.

## 3. Regole comuni del nucleo

Il nucleo DEVE essere sufficiente a usare correttamente i moduli selezionati senza ripetere tutte le tassonomie dell'owner.
DEVE includere la domanda dell'owner e il suo confine con gli owner vicini.
DEVE dichiarare le prove necessarie, la gestione dell'incertezza e le modalità di invocazione.
DEVE preservare il contratto di risultato, il report assegnato e la provenienza delle premesse.
Le liste specifiche per tecnologia o per rischio condizionale appartengono ai moduli o alle reference condizionali.
Un controllo universalmente obbligatorio rimane nel nucleo o in un modulo base che il selettore non può eliminare.
Un nucleo privo dei controlli del job non costituisce una review completa.

Ogni profilo supporta due ingressi espliciti:

| Ingresso | Procedura | Condizione di avvio |
|---|---|---|
| `composed` | Validare pacchetto del job, caricare nucleo e moduli indicati, eseguire soltanto le conclusioni assegnate | Piano congelato, profilo compatibile, prerequisiti soddisfatti |
| `standalone` | Risolvere scope e modalità, preparare la selezione completa applicabile dell'owner, poi usare lo stesso metodo modulare | Preset completo o preparazione riuscita; gap espliciti |

Una chiamata diretta conserva la capacità del vecchio metodo; il chiamante usa il preset registrato senza indovinare moduli.
Il preset standalone include i controlli applicabili dell'owner e gli obblighi storici trasferiti ad altri owner.
Il coordinatore chiamante prepara una sola composizione attraverso `senior-review:review-preparation`, poi esegue job distinti presso i destinatari dichiarati.
Questa preparazione è una fase del medesimo run, con un solo ledger e un solo report finale; non avvia un secondo workflow.
Il vecchio ruolo non carica copie dei metodi trasferiti e non assume una capacità autonoma di dispatch.
Se il consumer diretto non supporta ancora questa coordinazione, conserva l'adapter atomico di compatibilità; il profilo compatto non è abilitato su quel percorso.
Il preset light è distinto dal preset standalone completo: conserva un solo reviewer e segue la sezione 5.2 del documento principale.
La sua versione compatta richiede qualifica delle protezioni precedenti; il preset atomico light rimane ammesso con qualifica, costo e motivazione espliciti, senza fan-out automatico.
Una modalità non supportata produce un blocco identificato, non una sostituzione automatica del profilo.
Gli owner non ancora qualificati usano il corpo atomico e ne contabilizzano l'intero input.
Il dispatcher seleziona la modalità dal contratto; non chiede al worker di ignorare istruzioni già caricate.

## 4. Contratto comune di esecuzione e risultato

Input comune di discovery:

- identità progetto/worktree/run e snapshot corrente ammesso;
- modalità full/changeset/dir/doc, scope delle conclusioni e policy applicabile; `review_basis` deriva dalla modalità e non richiede una scelta separata;
- diff e base reale soltanto quando richiesti dalla modalità;
- `composition`, `job_id`, assegnazioni scope/modulo e report path univoco;
- nucleo, corpi selezionati, reference minime e fingerprint risolti;
- evidence pack e contesto ammesso, con locator e freshness;
- knowledge assignment del job, disponibilità verificata e binding del modello già risolto;
- limiti di lettura, budget, autorizzazioni e capacità dell'host.

Il worker controlla l'identità prima di analizzare e restituisce un gap se non può risolvere una prova necessaria.
I percorsi delle conclusioni delimitano ciò su cui può emettere un risultato, non impediscono di leggere dipendenze pertinenti.
Le letture ulteriori vengono dichiarate nella copertura effettiva e nella misura del costo.
Nessun job di discovery riceve finding dei peer prima della propria consegna.
Il modello predefinito resta `inherit`; il nucleo non sceglie modelli da alias o prezzi presunti.

Output comune:

- file nativo dell'owner al solo report path assegnato, con identity header del job;
- esito per ogni assegnazione: `examined`, `partial` o `blocked`, con motivazione; il fallimento del tentativo resta uno stato amministrativo distinto;
- evidenze effettivamente lette, controlli eseguiti, controevidenze e lacune;
- finding con percorso concreto, citazioni, premessa falsificabile e provenienza;
- `knowledge_usage` per ogni input assegnato, anche quando il risultato è non applicabile motivato;
- collegamenti verso note di altro owner senza avviare worker aggiuntivi;
- stato delivered o failed nel risultato amministrativo, distinto dalla completezza semantica.

Un header corretto e un corpo non vuoto provano identità e presenza dell'artefatto, non sufficienza della review.
Un risultato parziale può essere consegnato; mantiene incompleta la copertura interessata.
La consegna non autorizza modifiche al prodotto, installazioni, migrazioni, cleanup o pubblicazione.
I tool runtime si usano soltanto nel perimetro autorizzato dal metodo chiamante; le classificazioni delle prove restano distinte.

## 5. Registro completo delle identità da migrare

Le righe seguenti sono esaustive rispetto a `REVIEWER_ROLES` e `METHOD_BINDINGS` della baseline locale.
`M` indica i consumer comuni elencati nella sezione 14; le eccezioni sono esplicitate nei profili.
I nomi dei moduli base esistenti restano disponibili come ponte di compatibilità.
La divisione interna in moduli più piccoli non può conservare un vecchio modulo base che ricarica incondizionatamente tutto il vecchio corpo.

| Identità esatta | Azione | Lente primaria | Preset e consumer |
|---|---|---|---|
| `senior-review:api-contract-auditor` | Estrarre nucleo e controlli contract | `api-contract` | Composed e audit diretto; M |
| `senior-review:chicken-egg-detector` | Estrarre nucleo startup | `startup` | Composed e audit diretto; M |
| `senior-review:cleanup-auditor` | Separare controlli semantici di sottrazione | `application-hygiene` | Composed, tidy e health; M |
| `senior-review:code-auditor` | Delimitare generalista; estrarre concorrenza e performance | `code-correctness` | Light, composed, standalone; M |
| `senior-review:data-integrity-auditor` | Estrarre controlli persistenti | `data-integrity` | Composed e audit diretto; M |
| `senior-review:distributed-flow-auditor` | Estrarre controlli end-to-end | `distributed-flow` | Composed e audit diretto; M |
| `senior-review:logic-integrity-auditor` | Estrarre invarianti e mantenere prerequisito semantico | `logic-integrity` | Composed, scoped e testi pertinenti; M |
| `senior-review:premise-auditor` | Separare tre modalità con gli stessi metodi canonici | Modalità epistemica esplicita | Derivazione, Lens 0, claim check; M |
| `senior-review:resource-lifecycle-auditor` | Estrarre acquire/release e lifetime | `resource-lifecycle` | Composed e audit diretto; M |
| `senior-review:security-auditor` | Estrarre famiglie di trust e abuso | `security` | Composed e audit diretto; M |
| `senior-review:temporal-resilience-auditor` | Estrarre controlli sull'asse temporale | `temporal-resilience` | Composed e audit diretto; M |
| `senior-review:ui-race-auditor` | Delimitare la causalità temporale UI | `ui-race` | Composed e audit diretto; M |
| `repo-hygiene:workspace-auditor` | Conservare owner filesystem/Git | `workspace-hygiene` | Composed, tidy e health; M |
| `testing:test-suite-auditor` | Estrarre D1-D9 conservando governance/no-run | `testing` | Composed, audit suite e metodi testing; M |
| `abstraction-architect:abstraction-architect-agent` | Estrarre D1-D7 conservando discovery globale | `structural-entropy` | Composed e audit global/diff/content; M |
| `react-development:react-performance-optimizer` | Separare correttezza React e costo del rendering | `react-performance` | Composed e audit diretto; M |
| `typescript-development:type-safety-auditor` | Estrarre controlli di soundness | `type-safety` | Composed e audit diretto; M |
| `platform-engineering:platform-reviewer` | Estendere esplicitamente operatività/backend | `platform` | Composed e audit piattaforma; M |
| `senior-review:python-method` | Conservare method binding audit-only | `python` | `project-protocol:isolated-worker`; M |
| `senior-review:dependencies-method` | Conservare method binding audit-only | `dependencies` | `project-protocol:isolated-worker`; M |
| `senior-review:accessibility-auditor` | Creare ruolo, nucleo e moduli con qualifica | `accessibility` | Composed e audit diretto preparato; M |

## 6. Matrice normativa per ruolo

Ogni profilo seguente eredita input/output della sezione 4.
Le qualifiche indicate sono casi minimi specifici; si aggiungono quelli comuni della sezione 13.
Le destinazioni citate richiedono aggiornamento bilaterale dei vecchi obblighi e delle esclusioni del ricevente.

### 6.1 `senior-review:api-contract-auditor`

- Fonte: `roles/api-contract-auditor.md`, fasi 1-5, righe 42, 48, 71, 99 e 107.
- Conserva inventario dei contratti, confronto request/response, breaking changes, consumer e coerenza fra contratti.
- Moduli canonici: base contract, request/response drift, compatibility e consumer coherence; AMQP schema usa `amqp-contracts`.
- Input specifici: contratto formale o runtime, implementazione e consumer risolti; baseline per il confronto delle versioni.
- Output specifico: entrambe le citazioni, lato dichiarato e lato applicato, con direzione della compatibilità.
- Trasferisce diagnosi di delivery e saga al distributed; semantica del dominio al logic; exploit al security.
- Un DTO senza schema runtime resta prova del contratto dichiarato, non dimostra validazione dell'input.
- In content conserva drift presente; senza base non inventa una classificazione di breaking change storico.
- Qualifica: schema dichiarato corretto, campo incompatibile, consumer permissivo, contratto assente, errore non documentato.
- Consumer da migrare: M e brief contract/AMQP; una rigenerazione di client richiede workspace e autorizzazione propri.

### 6.2 `senior-review:chicken-egg-detector`

- Fonte: `roles/chicken-egg-detector.md`, fasi 1-6, righe 38, 69, 102, 135, 160 e 177.
- Conserva inventario init, grafo dei prerequisiti, cicli bootstrap, accoppiamento temporale e dipendenze infrastrutturali.
- Moduli canonici: startup base, bootstrap/config ordering e `migration-ordering`.
- Input specifici: entrypoint, configurazione effettiva, prerequisiti e ordine di init/migrazione.
- Output specifico: sequenza causale e condizione che impedisce l'avvio, con nodi e archi provati.
- Trasferisce retry continuativo al temporal; compatibilità fra versioni e rollout al platform; invarianti del dato al data.
- Un ciclo di import non implica da solo un ciclo di bootstrap: il percorso di inizializzazione deve essere dimostrato.
- Liveness a regime appartiene all'operatività; readiness prima dell'ingresso nel servizio rimane startup.
- Qualifica: ordine valido, dipendenza circolare effettiva, ordine pigro lecito, migrazione con prerequisito mancante.
- Consumer da migrare: M, brief di migrazione e riferimenti che usano circular-dependencies come sinonimo di ogni ciclo.

### 6.3 `senior-review:cleanup-auditor`

- Fonte: `roles/cleanup-auditor.md`, D1-D5, righe 29, 51, 84, 125 e 149.
- Conserva dead code semantico, asset dell'applicazione, dipendenze non usate, documentazione storica e residui di lifecycle.
- Moduli canonici: application-hygiene base e D1-D5 selezionabili con i loro allargamenti di ricerca.
- Input specifici: grafo degli usi, configurazione, risoluzioni dinamiche, convenzioni di pubblicazione e perimetro.
- Output specifico: classificazione del residuo, riferimenti cercati e incertezza sulla removibilità.
- Trasferisce garbage/VCS a workspace; CVE/licenze al dependencies method; oracoli e ritiro dei test al testing.
- I controlli di dead code di lingua sono prove riusate, non un secondo scan completo disaccoppiato dall'evidence pack.
- Il report rimane detection-only: un finding non costituisce autorizzazione a rimuovere l'artefatto.
- Qualifica: uso dinamico, export pubblico, asset configurato, dipendenza phantom e residuo realmente inutilizzato.
- Consumer da migrare: M, tidy, application-cleanup-method e i riferimenti lite/full dei tre variant.

### 6.4 `senior-review:code-auditor`

- Fonte: `roles/code-auditor.md`, righe 45-75, 78, 95, 104, 138 e 167.
- Conserva correttezza locale, casi limite, error handling, confini visibili nel file e triage dei rischi inattesi.
- Moduli espliciti aggiunti: `code-concurrency` e `code-general-performance`, descritti nella sezione 7.
- I controlli security, acquire/release, transazioni e qualità degli oracoli vengono assegnati ai relativi owner specialisti.
- Singleton e stato per istanza vengono distinti per causa: race a concurrency, ordine init a startup, copie autorevoli ad abstraction.
- Input specifici: file completi, caller/callee necessari, contratti locali e prova che il percorso sia raggiungibile.
- Output specifico: trigger, percorso locale e conseguenza; un triage rimanda la domanda specialistica alla preparazione.
- Il triage non genera job ulteriori dopo il congelamento; rende necessaria una ricomposizione tracciata.
- Qualifica: errore locale, caso limite corretto, concorrenza non DB/non UI, I/O evitabile e rischio senza segnale lessicale ovvio.
- Consumer da migrare: M, light, architecture/general-performance mapping, code-review agent templates e specialist addenda.

### 6.5 `senior-review:data-integrity-auditor`

- Fonte: `roles/data-integrity-auditor.md`, fasi 1-5, righe 37, 52, 62, 70 e 76.
- Conserva inventario di tutti i writer, enforcement persistente, anomalie concorrenti, divergenza fra store e rappresentazioni.
- Moduli: base data, `sql-transactions`, `sql-constraints`, `data-concurrency`, cache consistency e retention applicativa.
- Input specifici: schema, writer/reader, transazioni, lock/versioni, cache e contratti di conservazione pertinenti.
- Output specifico: stato impossibile persistibile e percorso che supera la difesa, oppure limite della prova.
- Trasferisce costo query e indici a platform; race di memoria a code-concurrency; regole del dominio non persistenti a logic.
- Conserva il controllo di dati e shape durante migrazione; ordering a startup e coesistenza rollout a platform.
- Retention riguarda il dato applicativo e le copie pertinenti, non la gestione dei run di project-lifecycle.
- Qualifica: lost update, vincolo equivalente, transazione corretta, cache stale ammessa e lettore di payload precedente.
- Consumer da migrare: M, data-migrations aliases, controlli SQL e addenda che attribuiscono ogni migrazione al solo data owner.

### 6.6 `senior-review:distributed-flow-auditor`

- Fonte: `roles/distributed-flow-auditor.md`, fasi 1-6, righe 38, 72, 103, 130, 158 e 191.
- Conserva topologia, entrambi gli endpoint, trasformazioni, deadline chain, retry distribuiti, saga e delivery/order.
- Moduli: distributed base, idempotenza dell'effetto esterno, queue/retry/DLQ e specializzazioni AMQP di ack/replay.
- Input specifici: producer/caller, consumer/callee, configurazione effettiva e modello di fallimento indipendente.
- Output specifico: timeline end-to-end e stato rimasto su ciascun lato dopo errore, retry o partizione.
- Trasferisce schema dichiarato contro implementazione al contracts; autorizzazione al security; lifetime del canale a resources.
- La presenza di una libreria broker non prova protocollo/versione; un endpoint assente resta un gap.
- Idempotenza del singolo writer locale resta data/logic; il confine remoto e l'effetto duplicato restano distributed.
- Qualifica: crash prima/dopo ack, deduplica corretta, timeout chain, compensazione fallita e producer/consumer incompleti.
- Consumer da migrare: M, brief messaging e API contracts; i moduli non effettuano chiamate di produzione.

### 6.7 `senior-review:logic-integrity-auditor`

- Fonte: `roles/logic-integrity-auditor.md`, righe 33-39, 46, 60, 101 e 111.
- Conserva pre/postcondizioni, invarianti, assunzioni, regole, reentrancy strutturale, transizioni e drift della rappresentazione.
- Moduli: base logic e categorie L1-L8, con idempotenza locale e percorsi alternativi esplicitamente delimitati.
- Input specifici: interconnect map oppure contesto semantico scoped, entrambi trattati come ipotesi da verificare.
- Output specifico: regola e violazione citate, scenario concreto, anchor o MAP-GAP e molteplicità accertata.
- Trasferisce thread/data race a code-concurrency, timing DOM a UI race, saga distribuita a distributed.
- La derivazione autonoma rimane obbligatoria quando la mappa tace; il silenzio della mappa non disattiva una categoria plausibile.
- Un'invariante dichiarata valida richiede esplorazione delle istanze e dei mutatori; evidenza incompleta produce unverifiable.
- Qualifica: bypass admin/batch, stato terminale mutato, istanza alternativa, mappa errata e contesto semantico scoped valido.
- Consumer da migrare: M, no-context handling, claim/spec review e note T17 che attribuiscono a logic tutte le race.

### 6.8 `senior-review:premise-auditor`

- Fonte: `roles/premise-auditor.md`, Mode 1 a riga 19, Mode 2 a riga 63 e Mode 3 a riga 93.
- Conserva tre ingressi tipizzati con la stessa identità registrata; la modalità è obbligatoria nel binding e nel report.
- Mode 1 deriva claim da sorgenti e scope prima della riconciliazione, senza mappe né finding dei peer.
- Mode 2 prova a falsificare la premessa di un finding già formulato; accetta contesto completo e conserva target della refutazione.
- Mode 3 verifica i claim di plan/spec/doc contro sorgenti e decisioni; non diventa una discovery generica del prodotto.
- I moduli e i report dei tre modi sono incompatibili per packing, riuso automatico e qualifica.
- Input/output specifici: claim e controesempi per Mode 1; HOLDS/REFUTED/UNCERTAIN per Mode 2; claim risolti/non risolti per Mode 3.
- Il prerequisito compilato deve includere anche Mode 3; l'attuale descrizione di due modi non è il contratto futuro completo.
- Qualifica: contaminazione rifiutata, derivazione indipendente, refutazione di PREMISE/SUPPORT e riferimento testuale inesistente.
- Consumer da migrare: M, Phase 1c/1d, Lens 0, light text e tutti i reader dell'output delle premesse.

### 6.9 `senior-review:resource-lifecycle-auditor`

- Fonte: `roles/resource-lifecycle-auditor.md`, righe 18-22 e fasi 1-4 a righe 37, 53, 63 e 70.
- Conserva inventario acquisizioni, ownership nominabile, release su successo/errore/cancellazione e mismatch di lifetime.
- Moduli: resource base, pool/registry, task lifetime e connection-pool-lifecycle; linguaggi/framework sono specializzazioni.
- Input specifici: acquire, tutti i percorsi di uscita, chi possiede il riferimento e chi termina il suo lifetime.
- Output specifico: matrice acquire/owner/tre uscite e prove di leak, double-release o use-after-release.
- Trasferisce linearizzabilità e lock ordering a code-concurrency; ripetizione del danno al temporal; exploit memory safety al security.
- Un timer è risorsa per registrazione/clear e meccanismo temporale per rearm/failure: le due domande restano distinguibili.
- La cancellazione del lavoro è letta anche quando il chiamante smette di attendere senza chiudere il processo.
- Qualifica: early-return leak, cancel corretto, task orfano, pool bounded e cleanup idempotente.
- Consumer da migrare: M, React cleanup e controlli duplicati State Auditor/Failure Flow del code owner.

### 6.10 `senior-review:security-auditor`

- Fonte: `roles/security-auditor.md`, famiglie a righe 35, 46, 57, 66, 75 e 86.
- Conserva trust boundary, auth/authz/ownership, injection, segreti, crypto e abuso dei confini esposti.
- Moduli: security base e specializzazioni del backlog per identità, input, webhook, AI boundary e audit trail.
- Input specifici: chiamante non fidato, dati controllabili, decisione di autorizzazione e sink effettivamente raggiunto.
- Output specifico: percorso di abuso concreto, controllo assente/aggirabile e controevidenza cercata.
- Trasferisce audit ecosystem/CVE/licenze al dependencies method; meccanismi nativi di piattaforma al platform specialista pertinente.
- La stessa mancanza di validazione non produce copie security, contracts e TypeScript prive di failure mode distinta.
- I consigli dipendenti da provider/versione richiedono conoscenza verificata; un nome di tecnologia non stabilisce la vulnerabilità.
- Qualifica: IDOR, RLS aggirata, input non controllabile, policy equivalente e prompt injection verso tool autorizzati.
- Consumer da migrare: M, critical scan del code owner e sovrapposizioni con platform security.

### 6.11 `senior-review:temporal-resilience-auditor`

- Fonte: `roles/temporal-resilience-auditor.md`, righe 18-22 e fasi 1-5 a righe 38, 54, 71, 83 e 94.
- Conserva primo/N-esimo/continuo fallimento, stato terminale, silent death, conseguenza per utente e clock/environment.
- Moduli: temporal base, background jobs, timeout locali, retry/backoff e restart dei meccanismi residenti.
- Input specifici: trigger/cadenza, contatori, guardie, reset, segnali all'utente e stato conservato dopo restart.
- Output specifico: tre orizzonti di fallimento e chi rileva la degradazione, con tempi misurati o derivati dichiarati.
- Trasferisce bootstrap a startup; deadline chain remota a distributed; acquire/release a resources.
- Alerting end-to-end del servizio è platform; escalation della specifica macchina temporale resta temporal.
- Il costo di ripetizione non viene dichiarato misurato da una semplice lettura del codice.
- Qualifica: rearm saltato, await senza uscita, backoff continuo intenzionale, guardia corretta e sleep/resume.
- Consumer da migrare: M, process-recovery addenda e mapping che attivano temporal soltanto quando compare un timer.

### 6.12 `senior-review:ui-race-auditor`

- Fonte: `roles/ui-race-auditor.md`, righe 17-20, 30, 53, 74 e 117.
- Conserva causalità temporale fra dati asincroni, render/layout, eventi, scroll, focus, misure e scheduler del framework.
- Moduli: UI-race base con timeline, stale closure e sincronizzazione render/evento.
- Input specifici: componenti e ciclo degli eventi, evento iniziale e ordine dei passaggi che produce il difetto.
- Output specifico: timeline T0..Tn, punto di invalidazione e sintomo osservabile.
- Trasferisce blocco CSS statico e raggiungibilità dei controlli a interaction-critical-paths; semantica/tastiera ad accessibility.
- Trasferisce copie autorevoli per istanza ad abstraction quando la causa è duplicazione dello stato, non interleaving.
- Il fatto che un difetto appaia nell'interfaccia non lo rende automaticamente una race.
- Qualifica: focus anticipato, measurement stale, ordine sincronizzato corretto e consent bloccato solo da CSS classificato fuori race.
- Consumer da migrare: M, React stale closures e i casi deterministici oggi inseriti sotto Cross-Component Timing.

### 6.13 `repo-hygiene:workspace-auditor`

- Fonte: `roles/workspace-auditor.md`, direttive a righe 23-31 e catalogo C1-C7 della skill repo-hygiene.
- Conserva filesystem/Git, output generati tracciati, ignore, scratch, asset documentali e stato ausiliario del repository.
- Moduli: workspace base e C1-C7 con la ricerca allargata che controlla intenzionalità e riferimenti indiretti.
- Input specifici: inventario confinato, configurazione di pubblicazione e risultati dei comandi sul candidato.
- Output specifico: comando/prova, classificazione KEEP o candidato e limite di conclusione.
- Trasferisce usi dei simboli e asset applicativi al cleanup; il confine non richiede deduplica sistematica fra i due owner.
- Un artefatto tracciato o una ignore rule senza match può essere intenzionale: l'assenza non dimostra inutilità.
- Il worker resta report-only, compresi stash, branch e worktree; nessun modulo eredita permessi di rimozione.
- Qualifica: dist pubblicato intenzionalmente, ignore preventiva, asset da config e directory di scratch realmente posseduta.
- Consumer da migrare: M, tidy/retention reader e istruzioni che confondono applicazione sottraibile con filesystem garbage.

### 6.14 `testing:test-suite-auditor`

- Fonte: `roles/test-suite-auditor.md`, D1-D9 a righe 49-105 e no-run a riga 31.
- Conserva inventario/layer, orfani, disabled, failure/flakiness, duplicazioni, contraddizioni, coupling e test che non falliscono.
- Moduli: testing base, D1-D9, contract/journey/capacity/AI protection quando pertinenti.
- Input specifici: requisiti protetti, sorgenti importate, test/oracoli, fixture e risultati ammessi con snapshot/versione.
- Output specifico: requisito/failure mode protetti o mancanti, condizioni indipendenti e statistiche con evidenza.
- D1/D9 restano suite-wide come contesto; D2-D8 seguono i moduli assegnati e le dipendenze necessarie.
- In review no-run riusa risultati ammessi, marca metriche stale/not measured e non esegue il full suite per completare una tabella.
- Product defect, oracle errato, ambiente e flakiness restano distinti; conteggi e refactor non giustificano ritiro.
- Qualifica: test triviale sempre verde, oracolo indipendente, duplicazione stessa failure mode e difese su livelli differenti.
- Consumer da migrare: M, metodi testing, code test-infra scan e addenda che fissano un report unico per tutto l'owner.

### 6.15 `abstraction-architect:abstraction-architect-agent`

- Fonte: `roles/abstraction-architect-agent.md`, discovery a riga 92, diff a riga 101 e D1-D7 a righe 160-166.
- Conserva ownership dei fatti, rappresentazioni equivalenti, stato derivabile, prior art, ricorrenza e fitness dell'astrazione.
- Moduli: structural-entropy base e D1-D7 con discovery per nome/sinonimo, letterale, chiamata e forma della decisione.
- Input specifici: target, anchor diff quando presente, concept index identificato e stato di freshness della mappa.
- Output specifico: rappresentazioni confrontate, contratto semanticamente identico o diverso e gap della ricerca.
- La ricerca resta nell'intero progetto pertinente oltre i file cambiati; lo scope limita le conclusioni, non nasconde prior art.
- In review content scrive soltanto il report; l'aggiornamento del concept index resta nell'audit globale autorizzato.
- Trasferisce coupling locale al code; timing a UI/concurrency; dead code al cleanup.
- Qualifica: copia semantica con nomi diversi, omonimi legittimi, dato derivabile, index stale e concept nuovo non indicizzato.
- Consumer da migrare: M, check-health, method audit, report path e preset global/diff/content.

### 6.16 `react-development:react-performance-optimizer`

- Fonte: `roles/react-performance-optimizer.md`, confine a riga 18 e controlli a righe 30, 38, 44, 48 e 57.
- Conserva conoscenza React per subscription/selectors, effect loops, closure, teardown, virtualizzazione, caching e bundle.
- Moduli: React base e specializzazioni per store/effect, costo render e bundle/lista; ogni failure mode mantiene un solo owner primario.
- Input specifici: component tree, store/effect, scheduling pertinente e prove ammesse di costo/render.
- Output specifico: percorso React ed effetto, con impatto quantitativo solo quando la prova lo sostiene.
- Release della risorsa a resources; race layout/evento a UI; CSS statico a interaction-critical-paths; costo generico a code-general-performance.
- La conoscenza React può informare il modulo dell'owner primario tramite knowledge binding; non richiede una copia del finding.
- Nella modalità audit non applica le correzioni o installazioni che il vecchio ruolo poteva descrivere per optimization.
- Qualifica: selector stabile/instabile, effect loop, cleanup corretto, virtualizer key e closure non obsoleta.
- Consumer da migrare: M, audit React diretto e riferimenti che interpretano il ruolo sempre come autorizzazione a ottimizzare.

### 6.17 `typescript-development:type-safety-auditor`

- Fonte: `roles/type-safety-auditor.md`, scope guard a riga 16 e workflow a riga 29.
- Conserva soundness delle asserzioni, narrowing, generic/type contracts, runtime boundary schema e strict configuration.
- Moduli: type-safety base e famiglie del rulebook, selezionate sul package pertinente.
- Input specifici: TypeScript sorgente, tsconfig effettivo, tipi producer/consumer e risultati del compilatore ammessi.
- Output specifico: assunzione di tipo non provata e percorso runtime che rende osservabile la discrepanza.
- Trasferisce naming/style al metodo write, dead code a knip/cleanup, performance React al relativo owner.
- La validazione di confine viene distinta da drift del contratto e da sfruttabilità: una causa condivisa non genera copie.
- Uno snippet che compila non prova sicurezza runtime; l'assenza di `any` non esaurisce la soundness.
- Qualifica: assertion non sicura, narrowing reale, schema applicato, tsconfig del package e type alias pubblico compatibile.
- Consumer da migrare: M, audit type-safety e collegamenti alle regole selezionate.

### 6.18 `platform-engineering:platform-reviewer`

- Fonte: `roles/platform-reviewer.md`, fasi 1-4 a righe 26, 32, 76 e 86; reference infrastructure, righe 41, 70 e 88.
- Conserva meccanismi di piattaforma, confini client/backend, performance native, API/DB, bundle e contesto del deploy.
- Estende il mandato in modo esplicito a backend-only, telemetria, rollout, backup/restore e recovery: i vecchi trigger multi-platform vengono aggiornati.
- Moduli: platform base, SQL indexes/N+1, capacità, operatività, rilascio, browser compatibility e recovery del backlog.
- Input specifici: target/runtime/versioni, requisiti di capacità/disponibilità e configurazione effettiva con prove ammesse.
- Output specifico: requisito violato, meccanismo coinvolto e condizioni; restore/throughput non vengono dichiarati esercitati da config.
- Trasferisce costo algoritmico generico a code-general-performance, risorse acquisite a resources e invariant persistente a data.
- Meccanismi auth/storage/IPC specifici restano specializzazioni platform con confini concordati con security.
- Qualifica: backend-only, schema rollout misto, restore non provato, indice equivalente, browser supportato e target assente.
- Consumer da migrare: M, stack-dimensions, audit platform e i brief che richiedono due segnali integrazione per ogni nuovo modulo operativo.

### 6.19 `senior-review:python-method`

- Fonte: `METHOD_BINDINGS` del compiler e `review-preparation/references/stack-dimensions.md`, riga 13.
- Conserva identità di metodo, esecuzione tramite `project-protocol:isolated-worker` e modalità audit-only.
- Il binding carica `python-development:python-refactor-method` e `python-development:python-dead-code` nei loro percorsi di audit.
- Moduli: Python base e controlli semantici/idiomatici selezionabili dell'owner provider; tooling già ammesso resta nell'evidence pack.
- Input specifici: package Python, runtime/configurazione e risultati ruff/type checker/dead code/complexity pertinenti.
- Output specifico: problemi che i tool non hanno già risolto, con metodo/skill effettivamente caricati e report assegnato.
- Trasferisce test quality a testing e race generale a code-concurrency; la conoscenza Python specializza le domande pertinenti.
- Non viene inventato un ruolo python-reviewer; il ruolo esecutivo e l'identità logica restano entrambi registrati nella delivery.
- Qualifica: Python semantico non rilevato dal lint, segnalazione duplicata del tool evitata, binding conservato e load mancante.
- Consumer da migrare: M, router aliases `isolated-worker#python`, catalog loader e ledger method-binding.

### 6.20 `senior-review:dependencies-method`

- Fonte: `METHOD_BINDINGS` del compiler e `review-preparation/references/stack-dimensions.md`, riga 14.
- Conserva identità di metodo, esecuzione tramite `project-protocol:isolated-worker` e `dependency-audit:dependency-audit` read-only.
- Moduli: dependency base, audit ecosystem, compatibilità/supporto, licenze e fatti UNKNOWN secondo il metodo provider.
- Input specifici: manifest/lockfile del package, versione effettiva e risultati tooling/fonti primarie ammessi.
- Output specifico: fatti TOOL-REPORTED, INFERRED e UNKNOWN, con source/versione e limiti del controllo.
- Trasferisce dipendenze inutilizzate al cleanup; exploit applicativo al security; footprint non prova vulnerabilità.
- Un tool assente produce una lacuna; nessuna installazione o remediation viene autorizzata dal method binding.
- Le dipendenze di un package estraneo non attivano il job sul componente selezionato.
- Qualifica: lockfile corretto, advisory non applicabile alla versione, runtime unsupported, licenza sconosciuta e audit tool assente.
- Consumer da migrare: M, alias `isolated-worker#dependencies`, manifest evidence pack e router dei metodi.

### 6.21 `senior-review:accessibility-auditor`

- Azione: creare identità nel kernel, catalog compiler e dispatch dei consumer; default model inherit.
- Mandato: operabilità tecnica dei percorsi utente, semantica, input/tastiera/focus e percezione nelle condizioni supportate.
- Moduli: base `accessibility-auditor`, `a11y-navigation-semantics`, `a11y-perception-feedback` e `interaction-critical-paths`.
- Input specifici: journey/controlli, markup/component tree, cascata effettiva, condizioni supportate e target di accessibilità dichiarato.
- Output specifico: barriera concreta, percorso non completabile e prove distinte fra fonte statica, tool, browser e tecnologia assistiva.
- Trasferisce timing asincrono a UI race, rendering cost a React/platform, design estetico ai metodi di design pertinenti.
- Il target WCAG/versione/livello guida i moduli a11y; non è un prerequisito per rilevare un login o consent irraggiungibile.
- I limiti delle verifiche assistive restano visibili; il profilo non dichiara conformità completa a partire da una review statica.
- Qualifica: CSS globale che batte il modal, focus/keyboard corretto, native semantics, reflow, UI statica e scope non UI.
- Consumer da migrare: M, selector di UI statiche, report a11y e reader che confondono assenza di race con operabilità provata.

## 7. Specifica dei tre moduli resi espliciti

### 7.1 `code-concurrency`

Owner: `senior-review:code-auditor`. Lente: `code-correctness`. Input: shared ammesso, peer findings esclusi.
Domanda: quali interleaving fra thread, task, processi o callback violano atomicità, visibilità, ordine o progresso?
L'attivazione richiede evidenza di accessi concorrenti o di coordinamento, anche senza parole `thread` o `lock` nel diff.
Il preparatore registra il nuovo segnale tramite il vocabolario; tag esatto e incertezza seguono il contratto authoring.
Il modulo inventaria accessi e identità dello stato, poi costruisce un ordine concreto che produce l'errore.
Controlla check/use, read-modify-write, lock identity/scope/order, attese reciproche, starvation e coordinamento dei task.
La semantica memory-ordering viene applicata soltanto con linguaggio/runtime/versione identificati e reference pertinenti.
Esamina cancellazione e failure dei sibling per l'ordine degli effetti; la liberazione dell'handle resta resources.
Controevidenze: serializzazione effettiva, transazione/CAS comune, immutabilità, single ownership e scheduling contrattuale provato.
Race esclusivamente nel database rimane data; race del layout rimane UI; reentrancy puramente strutturale rimane logic.
Un pool lockato correttamente non prova correttezza del dato che contiene; l'identità del lock deve essere comune agli attori.
Finding minimo: attori, stato condiviso, sequenza, istruzioni citate e stato finale osservabile.
Qualifica obbligatoria: lost update in memoria, lock inversion, check/use lecito, single-event-loop con await interleavabile e actor serializzato.
T17 della mappa allegata viene integrato con questo modulo per coprire la concorrenza non DB/non UI.

### 7.2 `code-general-performance`

Owner: `senior-review:code-auditor`. Lente: `code-correctness`. Input: shared ammesso, peer findings esclusi.
Domanda: il costo per operazione, per input o per frequenza cresce oltre il requisito/budget ammesso per un percorso raggiungibile?
L'attivazione deriva da algoritmo, ripetizione, volume I/O, allocazione, serializzazione o lavoro sincrono pertinente.
Si identificano dimensione dell'input, numero di esecuzioni, posizione sul percorso e limite effettivo del lavoro.
Si controllano complessità, scansioni ripetute, chiamate inutili, lavoro duplicato, I/O sincrono sull'event loop e materializzazioni evitabili.
Un'operazione costosa intenzionale, bounded o fuori dal percorso critico è controevidenza da verificare.
SQL indexing/query plan e N+1 restano platform; React subscription/rendering restano React; pool release resta resources.
Il modulo può annotare il moltiplicatore comune senza duplicare un finding specialistico con la stessa causa.
Una deduzione statica identifica un rischio e il suo trigger; non si inventano latenza, throughput o costo monetario misurati.
L'assenza di benchmark non prova che il percorso sia rapido, ma può limitare severità e conclusioni quantitative.
Finding minimo: lavoro eseguito, crescita o ripetizione, trigger, esito richiesto violato e difese cercate.
Qualifica obbligatoria: algoritmo quadratico raggiungibile, input bounded legittimo, I/O duplicato, blocking su loop e costo calcolato con cap reale.
La general-performance dimension legacy risolve a questo modulo senza avviare un secondo code-auditor completo.

### 7.3 `interaction-critical-paths`

Owner: `senior-review:accessibility-auditor`. Lente: `accessibility`. Input: shared ammesso, peer findings esclusi.
Domanda: il percorso necessario per entrare o completare l'azione critica rimane concretamente raggiungibile e azionabile?
L'attivazione riguarda login, onboarding, consent/policy acceptance, setup e altri percorsi critici dimostrati dal prodotto.
Il requisito di operabilità esiste anche quando non è dichiarato un obiettivo normativo di accessibilità.
Si segue la journey fino al controllo finale attraverso componenti, stato, overlay, viewport e cascata CSS effettiva.
Si controllano visibilità, containing block, positioning, stacking, overflow/scroll-lock, dimensionamento, hit target e disabled/loading state.
Tema, font scale, locale e viewport ammessi sono condizioni del percorso; non vengono dedotti da un unico screenshot.
I lead `cascade_scan.py` della mappa sono riferimenti da confermare contro selettori e component tree, non verdetti riutilizzati.
Un selector globale che prevale sul `position: fixed` del consent e rende irraggiungibile il pulsante appartiene a questo modulo.
Il caso resta di questo owner anche senza async, transizione, focus race, React o incompatibilità fra due browser.
Una dipendenza di ordine fra render/evento produce invece la domanda del modulo UI race; una causa comune viene consolidata una volta.
Controevidenze: alternative equivalenti realmente raggiungibili, scroll container funzionante, difesa della cascata e condizione non supportata.
Finding minimo: configurazione raggiungibile, selettore/regola e controllo coinvolti, percorso bloccato e motivo per cui manca un'alternativa.
Una prova statica del conflitto resta derived; browser exercise, screenshot e tecnologie assistive sono fatti separati.
Qualifica obbligatoria: login coperto da overlay, consent fuori viewport, layout corretto su tema alternativo, testo espanso e race focus esclusa.

## 8. Decisioni di deconflitto e gestione delle duplicazioni

L'identità del file o della tecnologia non determina l'owner. Lo determinano domanda, causa e contratto violato.
La preparazione assegna i moduli prima del dispatch; il worker usa cross-owner notes per problemi fuori dal proprio mandato.
Le note non avviano worker e non soddisfano la copertura del destinatario.
Una scoperta che richiede nuovo lavoro torna al coordinatore per ricomposizione. A snapshot uguale si invalidano le consegne con fingerprint cambiato; un nuovo snapshot invalida conservativamente tutti i job.

| Causa o domanda | Owner primario | Contributo ammesso del vicino |
|---|---|---|
| Interleaving di memoria/task | code-concurrency | Resources prova lifetime; logic esplicita l'invariante |
| Lost update nello store | Data | Concurrency può citare la sequenza, senza duplicare la transazione |
| Copie autorevoli dello stesso fatto | Abstraction | UI mostra il sintomo; logic mostra l'invariante infranta |
| Ordine bootstrap | Startup | Temporal tratta soltanto il comportamento residente successivo |
| Release mancante | Resources | React fornisce la semantica effect; temporal quantifica la ripetizione |
| Schema dichiarato diverso dal payload | Contracts | Type-safety fornisce l'asserzione; distributed il percorso remoto |
| Effetto remoto ripetuto | Distributed | Data prova l'enforcement locale della deduplica |
| Blocco CSS deterministico della journey | Interaction-critical-paths | UI race soltanto se esiste una causa temporale distinta |
| Tastiera, semantic name/state o percezione | Accessibility | Il costo rendering non è una barriera semantica equivalente |
| Indice/query cost | Platform | Data valuta soltanto unicità/integrità/isolamento |
| Segreto o autorizzazione aggirabile | Security | Platform documenta il meccanismo nativo pertinente |
| Codice senza uso semantico | Cleanup | Workspace fornisce inventario senza interpretare simboli |
| Test che non protegge l'esito | Testing | Il product reviewer esplicita il requisito/failure mode |

Il consolidatore unisce una stessa causa mantenendo tutti i report sorgente e le prove indipendenti.
Domande complementari sulla stessa riga restano finding distinti soltanto se proteggono esiti o failure mode differenti.
Accordo da premessa condivisa resta echo; il numero di moduli o di job non aumenta automaticamente la confidenza.
La migrazione rimuove le vecchie copie dei controlli soltanto dopo aver provato la destinazione equivalente.

## 9. Template normativo del nucleo

Il seguente template è una struttura di authoring, non un prompt da incollare integralmente in tutti i job.
Le parti tra parentesi angolari sono campi del template da risolvere prima della promozione.

```markdown
# <Identità canonica del profilo>

## Mandato e confine
Domanda: <esito o classe di difetto di cui l'owner risponde>.
Conclusioni ammesse: <scope e contratti>.
Owner vicini: <domanda da trasferire e identità canonica>.

## Ingresso
Composed: valida <identity, snapshot, profilo, moduli, report path>.
Standalone: richiedi al coordinatore <preset con destinazioni dei trasferimenti>.
Il coordinatore prepara una sola composizione e job separati per owner.
Modalità richiesta: <full|changeset|dir|doc>; risolvi tipo di testo e base di giudizio secondo il contratto, rispettando gli input epistemici ammessi.
Prerequisiti: <prove che devono risolvere o gap che blocca>.

## Metodo comune
Leggi le prove assegnate e i corpi dei moduli ammessi.
Deriva il trigger e segui il percorso che rende osservabile il difetto.
Controlla la controevidenza prima di promuovere il finding.
Tratta mappe e altri risultati di preparazione come ipotesi con provenienza.
Rendi esplicite letture ulteriori necessarie e loro limiti.

## Obblighi universali
<soltanto controlli realmente comuni, con ID di migrazione>.

## Consegna
Scrivi <report nativo> soltanto al report path del job.
Conserva identity header e stato per ogni assegnazione.
Restituisci finding, evidenze lette, gap e knowledge usage.
Usa il rendiconto canonico minimo completo; nei riepiloghi rinvia ai dettagli senza duplicarli.
Una review senza finding nomina comunque ciò che ha esaminato.
```

Il controllo del nucleo verifica che ciascuna reference obbligatoria sia necessaria per tutte le sue invocazioni.
Una reference condizionale include il trigger che la rende necessaria; il suo costo viene misurato quando viene caricata.
Il contratto non impone persona, biografia, punteggi universali o un numero minimo di raccomandazioni.
Il nucleo segue il mantra della sezione 1.3 della specifica principale: minimo carico di istruzioni e output, efficacia preservata o migliorata e ogni obbligo necessario ancora verificabile.

## 10. Template normativo del modulo

Il metadata runtime mantiene un solo owner e una lente coerente; il loader calcola hash e token estimate dal corpo canonico.

```markdown
## <module-id>

Owner: <catalog-id>. Lente: <lens>. Modalità input: <shared|blind>.
Esito preservato: <invariante o requisito osservabile>.

Attivazione: <segnali con evidenza positiva nello scope>.
Esclusione: <quali prove possono stabilire non applicabilità>.
Incertezza: <prove assenti che impediscono di escludere il modulo>.

Procedimento:
1. Identifica <attori, risorsa o contratto>.
2. Segui <percorso e condizioni rilevanti>.
3. Verifica <difesa che preserva l'esito>.
4. Cerca <controesempio o alternativa lecita>.

Finding: cita <prove minime>, trigger e conseguenza.
Controevidenza: controlla <difesa equivalente e near miss>.
Confine: trasferisci <domanda distinta> a <owner>.
Limiti: distingui <deduzione statica> da <tool/runtime richiesti>.
Qualifica: <caso difettoso, corretto, near miss, gap e impatto>.
```

Un modulo di protocollo/versione specifica il prodotto/versione o lascia esplicito il gap.
Un'assenza richiesta, come backup mancante, si attiva dal bisogno evidenziato e non dalla presenza del file di backup.
La descrizione di un tool non autorizza installazione né una prova di produzione.
La granularità viene scelta sulla domanda verificabile: un elenco di parole chiave non è un metodo di review.

## 11. Matrice obbligo, modulo, job ed evidenza

Ogni porzione normativa del vecchio metodo riceve un ID stabile di migrazione.
La matrice deve includere corpo del ruolo, skill obbligatorie, addenda dei consumer e reference effettivamente caricate.
Un obbligo conservato in una reference continua a esistere e va contabilizzato; spostarlo non basta a riorganizzarlo.
Il seguente record logico è completo per decidere la destinazione; il formato eseguibile appartiene al contratto di migrazione.

```json
{
  "obligation_id": "code.failure.cancel-siblings",
  "old_owner": "senior-review:code-auditor",
  "old_source": "roles/code-auditor.md#phase-3",
  "old_source_digest": "digest-calcolato-dal-pacchetto",
  "requirement": "stabilire ordine ed effetti dei task sibling al fallimento",
  "decision": "split-by-failure-mode",
  "destinations": [
    {"owner": "senior-review:code-auditor", "module": "code-concurrency", "question": "ordine degli effetti"},
    {"owner": "senior-review:resource-lifecycle-auditor", "module": "resource-lifecycle-auditor", "question": "fine del lifetime"}
  ],
  "activation": "coordinamento concorrente o acquisizione di risorsa provati",
  "exclusion_evidence": "serializzazione o assenza pertinente provata",
  "unknown_policy": "coverage-gap",
  "qualification_cases": ["sibling-effect-order", "cancel-releases-resource", "serial-near-miss"],
  "consumers": ["review-branch", "review-changes", "lifecycle-final-review"],
  "standalone_preset": "all-applicable-owner-obligations",
  "floor_mapping": "preserve-required-obligation"
}
```

Le decisioni ammesse sono conservare nel nucleo, estrarre, trasferire, dividere per failure mode o sostituire con equivalenza provata.
Il ritiro di un controllo richiede requisito cessato o equivalenza dimostrata; brevità, età e mancati finding non bastano.
La matrice registra chi possiede il comportamento dopo il trasferimento e chi conserva il riferimento storico.
La qualifica lega il caso all'obbligo, al modulo, al profilo e al tipo di input ammesso.
Il piano del run aggiunge job ed evidence IDs; la consegna aggiunge prove effettivamente lette ed esito dell'assegnazione.
La catena completa è `obbligo -> modulo canonico -> profilo compatibile -> job -> evidenza -> consegna -> verifica`.
Un anello assente blocca la dichiarazione di copertura equivalente per il profilo migrato.

## 12. Migrazione, floor e compatibilità

La migrazione avviene per owner con checkpoint pubblicabili; gli owner non migrati continuano atomicamente.
Per ciascun owner si catturano sorgenti/digest e tutti i consumer, poi si completa la matrice prima di sostituire l'entrypoint.
Si realizza il nucleo e si trasferiscono i controlli alle destinazioni canoniche, aggiornando esclusioni e preset.
Si confrontano metodo precedente, profilo con moduli e profilo compatto sullo stesso corpus e policy di verifica.
Si abilita compact soltanto dopo la qualifica e si rende osservabile il profilo usato nelle delivery.
La riduzione di token dichiarata confronta input effettivi completi e non soltanto il testo del nuovo nucleo.

Il floor v1 a ruoli viene conservato come identità e collegato agli obblighi richiesti dalla matrice.
Conservare il nome di un ruolo non prova che i controlli obbligatori siano ancora presenti nel suo preset.
Quando un obbligo passa a un owner diverso, il piano derivato deve includerne la destinazione e la relazione con il floor originale.
Una base obbligatoria senza scope positivamente applicabile lascia un gap da riconciliare; non si fabbrica il segnale necessario.
La conversione verso un floor esplicito di copertura è versionata e mantiene leggibili i record storici.
Il protocollo conserva roster originale e derivato; non riscrive retroattivamente delivery e snapshot conclusi.

Le identità e i preset legacy restano disponibili: il preset dichiara job di destinazione dei controlli trasferiti, tutti nello stesso run.
La deprecazione indica sostituto, campo/modalità cambiati, consumer migrati e prova di equivalenza.
I reader supportano i run storici nel loro schema; la disponibilità del nuovo profilo non rende stale una prova storica per definizione.
Un run aperto non cambia profilo in silenzio: riconcilia bindings, input e consegne prima di riprendere.
Questa versione non rimuove identità esistenti e non crea profili nuovi per ogni tecnologia.

## 13. Qualifica della riorganizzazione

La qualifica è distinta dalla validità sintattica e dal build dei cinque host.
Per ogni obbligo migrato servono difetto positivo, versione corretta, near miss, incertezza e attivazione/esclusione nello scope.
Servono casi content senza baseline e changeset con impatto su dipendenze oltre il diff.
Servono casi in cui il rischio esiste senza un segnale lessicale ovvio, per verificare la preparazione semantica.
Le reference e il nucleo sono inclusi nel profilo sottoposto alla prova; un benchmark del solo modulo non qualifica il job reale.
I casi scritti dal generatore non sono l'unica prova del generatore o del reviewer.

Gate specifici:

- Tutti i 20 binding originari risolvono dopo la migrazione; accessibility risolve soltanto dopo registrazione e qualifica.
- Ogni obbligo del vecchio corpo e dei consumer ha destinazione, selettore pertinente e caso indipendente.
- Nessun difetto bloccante noto del corpus viene perso rispetto al riferimento senza classificazione e risoluzione.
- Precisione, richiamo e casi non valutabili sono riportati per famiglia, con numeratori, denominatori e variabilità.
- Standalone esercita gli obblighi originali applicabili, inclusi job distinti per trasferimenti, senza ricevere il solo nucleo.
- Light mantiene il suo singolo reviewer e la propria ampiezza; non eredita tutti i job di branch.
- Abstraction conserva discovery fuori diff, testing D1/D9 globali e no-run, premise l'isolamento dei tre modi.
- I due method binding conservano identità logica, isolated-worker effettivo, skill, modalità audit-only e report proprio.
- Concorrenza generale, performance generale e CSS che blocca l'ingresso hanno casi obbligatori specifici.
- I cinque export preservano corpo consumato, reference, capability, identità, reporting e strumenti nativi.

Se il nuovo profilo non supera la qualifica, resta atomic o non disponibile; la migrazione conserva la prova e il lavoro corretto già svolto.
Una qualifica su un modello non è un'equivalenza generale per tutti i modelli o per job più ampi.
Una modifica a nucleo, reference obbligatoria, indipendenza o domanda di un modulo invalida le qualifiche dipendenti pertinenti.
L'economia si valuta dopo i gate di copertura, includendo preparazione, letture aggiuntive, retry e verificatori.

## 14. Consumer e fase di adozione

M comprende le tre varianti senior-review, i loro riferimenti di preparazione/dispatch/consolidamento e i consumer lifecycle.
Vanno ispezionati i sidecar di `review-branch`, `review-changes`, `new-feature`, `fix-bug`, `refactor-code`, `continue-task`, `finish-task`, `run-maintenance`, `check-health`, `tidy-repo` e `investigate-problem` quando dichiarano il ruolo o il metodo.
La dichiarazione di una capability o una phase non prova che tutti i worker annidati abbiano ricevuto il nuovo contratto.
Le aggiunte si propagano a entry, skill, ruolo, reference, risorse dispatch e risultati, nel sorgente canonico del proprietario.
I template del compiler e gli adapter cambiano soltanto per esprimere meccanismi host; il comportamento resta nel kernel.
Gli export e i marketplace derivano dal build e non vengono corretti manualmente.

Light conserva il riferimento dedicato; branch/content usa preparazione comune e job del piano congelato.
Plan/spec/doc conservano i loro set e il claim-check; l'estrazione dei metodi non li converte in review del sorgente non richiesta.
Check-health e gli audit diretti adottano il percorso standalone del provider, senza avviare anche la stessa review composta.
Tidy e cleanup ricevono soltanto detection nelle review; autorizzazioni alla rimozione rimangono nei loro metodi.
Il lifecycle riceve copertura e gap insieme alle delivery; una chiusura del run non può nascondere un obbligo incompleto.
L'ordine preciso e i gate del piano sono normati dal documento di composizione e verifica.

## 15. Derivazione, verificatori e completeness critic

La generazione dei moduli avviene nell'authoring; il run ordinario carica controlli già promossi.
Map analyst e interconnect mapper producono prove e lead di preparazione e non entrano nell'elenco dei reviewer di discovery.
Premise Mode 1 corre blind prima della riconciliazione; il report per job viene riusato una sola volta al join e alla barriera.
Premise Mode 2 è Lens 0 e accetta il finding da falsificare; quel contesto rende il risultato inadatto a una derivazione indipendente.
Lenti 1/2 e severità conservano contesti freschi e contratti nativi; nessuna lente viene impacchettata con il suo discoverer.
Il claim-check Mode 3 usa il testo come artefatto e sorgenti come prova, con prerequisito e output propri.

Il completeness critic riceve piano, matrice obblighi, job attesi, consegne, copertura dichiarata, prove lette e gap.
Riceve anche finding verificati e contesto pertinente per contestare aree ad alto rischio realmente non esaminate.
Non deduce un gap soltanto dal fatto che un file o hotspot non abbia prodotto finding.
Controlla selezioni incoerenti, prerequisiti mancanti, claim universali senza molteplicità, assignment parziali e conclusioni oltre le prove.
Può contestare la sufficienza della copertura dichiarata; una spunta amministrativa non vincola il suo giudizio semantico.
Non certifica l'assenza di bug e non sostituisce una discovery omessa con un finding improvvisato.
Un follow-up ammesso torna al coordinatore con owner, modulo, scope e prova mancante; richiede piano/delivery/gate coerenti.
Nessun worker espande silenziosamente il fan-out o assegna a sé una nuova responsabilità.

## 16. Criterio di completamento della riorganizzazione

La riorganizzazione complessiva è completata quando tutti i 18 ruoli e i due method binding hanno la matrice esaustiva e il percorso di discovery composta con nucleo, moduli e preset qualificati.
La sola introduzione di moduli aggiuntivi sotto i vecchi corpi non completa questo risultato.
L'unica conservazione atomica prevista dalla specifica è il preset light della sezione 5.2 del documento principale, qualificato e contabilizzato separatamente.
Altre conservazioni atomiche restano transitorie e non soddisfano R14; un'eccezione definitiva richiede una modifica esplicita della specifica con obblighi, motivazione e qualifica.
Il nuovo accessibility e i tre moduli espliciti hanno corpi, trigger, confini, casi e reader realmente verificati.
Standalone, light, testi, branch e content preservano i contratti applicabili e le loro differenze.
Il registro dei profili, il loader e i gate rendono osservabile che cosa sia stato selezionato, eseguito e verificato.
La verifica finale distingue controlli statici del compiler, probe installati e review reali eseguite per ciascun host.
Il report di migrazione conserva lacune, deprecazioni, risultati non qualificati e costi sconosciuti.

## 17. Riferimenti al sorgente verificato

| Fonte canonica | Evidenza usata per la decisione |
|---|---|
| `scripts/daodan/reviewer_catalog.py`, righe 24-91 | 18 ruoli, due method binding, prerequisiti e identità host |
| `plugins/project-protocol/skills/project-protocol/scripts/review_roster.py`, righe 88-137 e 348-384 | Floor a ruoli, specialisti, support e policy di verifica |
| `plugins/project-protocol/skills/project-protocol/scripts/run_state.py`, righe 431-459 | Gate attuale di appartenenza al roster, distinto dalla copertura dei moduli |
| `plugins/senior-review/skills/review-preparation/references/knowledge-bindings.md`, righe 17-38 | Conoscenza assegnata alle delivery, lens aggiuntiva e nessun reviewer per skill |
| `plugins/senior-review/skills/review-method/references/team-review.md`, righe 96-130 e 174-179 | Report per dimensione, addenda abstraction/testing e delivery barrier |
| `plugins/senior-review/skills/review-quality-gates/references/panel-and-critic-prompts.md`, righe 182-215 | Critic attuale e segnali basati su assenza di finding da sostituire |
| `plugins/codebase-map/skills/map-method/references/phases-3-4.md`, riga 11 | Entry-gating path e cascata CSS da tracciare |
| `plugins/codebase-map/skills/map-method/references/phases-5-6.md`, righe 7 e 13 | Cascade leads e rischio Usability-blocking statico |
| `plugins/senior-review/contracts/evidenced-finding.toml` e `reviewer-result.toml` | Provenienza, evidenza e risultato nativo da preservare e adattare alla basis |

I percorsi della matrice sono riferimenti al sorgente di authoring del repository.
I pacchetti installati devono usare i corrispondenti riferimenti portabili compilati; questo documento non autorizza path cross-plugin a runtime.
