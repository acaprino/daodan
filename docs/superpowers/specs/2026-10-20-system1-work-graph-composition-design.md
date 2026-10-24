# Grafo di lavoro e decisioni locali: specifica del Filone B

Data: 20 ottobre 2026. Revisione dopo team review.
Stato: **proposta emendata, non implementata né promossa**.

Direzione iniziale aggiornata da
[ADR-0001](../../adr/ADR-0001-work-graph-step0-llm.md): lo Step 0 usa un prompt LLM
per proporre il grafo, seguito dalla validazione meccanica. L'esecuzione interamente
offline è la destinazione successiva. Il record precisa costo, routing per incarico
e limiti di questa scelta rispetto alla strategia iniziale di S1/S2; resta da
implementare e verificare.

La [specifica sui chiarimenti e le mappe decisionali](2026-10-24-conversational-decisions-and-work-graphs-design.md)
definisce il passaggio a domanda diretta, intervista o mappa decisionale quando manca una
decisione umana essenziale, con attesa dei consumatori dipendenti e ripresa o
revisione del piano. Anche questa integrazione resta proposta.

## 1. Obiettivo, autorità e compatibilità

Comporre ed eseguire lavoro di editing, planning, analysis e review tramite
un grafo esplicito, con avanzamento verificato e recupero limitato.
Gutsy è un candidato per alcune decisioni di routing, non il controllore.
I cicli di riparazione rimangono transizioni esplicite e limitate.

Riferimenti di disegno:
- `2026-10-19-graph-grounded-economy-routing-design.md`: §1.1 separazione
  Grafo del Codice / Workflow, §3.6 Choicer, §7.5 e §8 valutazione e adozione;
- `2026-10-20-system1-work-graph-composition-review.md`: review storica e
  registro di risoluzione degli emendamenti;
- `plugins/project-protocol/contracts/work.toml` e relativo `run_state.py`:
  contratti implementati da estendere, non già conformi a questo disegno;
- `evals/senior-review/choicer-eval/GUTSY_RESULTS.md`: osservazioni e limiti.

Questa revisione sostituisce le precedenti proposte di soglie operative e di
router AST primario del report Gutsy. Non modifica la specifica madre né
autorizza modifiche ai kernel. Le estensioni qui proposte richiedono approvazione
del disegno, migrazione dei contratti e verifiche prima dell'integrazione.
Non dipende dalla presenza nel working tree della specifica eliminata del
18 ottobre: il macro-flusso richiesto è enumerato in §6.

### 1.0 Coordinamento tra nodi fratelli (integrazione dal 20–21 ottobre 2026)

Questa sezione rende esplicita una regola che il resto del disegno assume ma
non enuncia: il coordinamento tra nodi fratelli (nodi indipendenti nella stessa
wave, eventualmente eseguiti in parallelo) NON avviene tra loro direttamente,
ma attraverso il controller e la barriera di sincronizzazione.

**Artefatti circolanti.** I fratelli scambiano esclusivamente artefatti
versionati e hashati: per ogni artefatto, il grafo registra il produttore, la
versione e il digest corrente. Al dispatch di un nodo, il controller lega
(digest-immutabile) la versione dell'artefatto consumato nei suoi `consumes`.
Se durante l'esecuzione viene pubblicata una nuova versione dello stesso
artefatto logico, il completamento del nodo non può più promuovere: il nodo
diventa `stale` e va re-verificato o re-eseguito su input corrente.

**Un unico registro.** Le decisioni di scheduling, prenotazione, budget e
stato vivono nella `work.json` del run, mai in file paralleli per nodo. Ogni
transizione di stato passa per una prenotazione (reservation con holder,
lease e fencing) con verifica della revisione (CAS) e a commit atomico del
registro, altrimenti due scrittori concorrenti possono prenotare lo stesso nodo.

**Barriera (join).** I fratelli si sincronizzano alla barriera di wave; essa
avanza solo quando (a) tutti i nodi richiesti sono `succeeded`, (b) gli
artefatti da loro prodotti sono pubblicati e (c) il **candidato combinato**
supera i gate. L'integrazione dei risultati in un candidato unico precede i
gate globali: i gate non girano sui singoli worktree dei fratelli.

**Budget condiviso.** Il budget è un ledger unico per run e ogni azione
(dispatch, verifica, riparazione) viene addebitata prima di partire. Non
esistono budget paralleli per nodo: un ramo che esaurisce la sua quota
dirompe sugli altri e il controller lo rende visibile, invece di lasciar
derapare silenziosamente il recovery.

**Isolamento di scrittura reale.** Disgiunzione dei write_set non basta: due
fratelli possono condividere DB, lock, servizi esterni o letture incrociate.
Il controller abilita la scrittura parallela solo se l'host fornisce
isolamento verificato (worktree/snapshot separati e risorse dedicate).
Altrimenti si esegue in sequenza, anche se il grafo le avrebbe abilitate:
la prontezza logica dei prerequisiti non implica mai prontezza di esecuzione.

**Esiti di coordinamento.**

| Evento | Effetto |
|---|---|
| Un fratello fallisce il gate | Il suo artefatto non viene pubblicato; i consumatori non partono o vengono revocati; gli indipendenti possono completare, ma la barriera non chiude |
| Nuova versione pubblicata mentre gira | Invalidazione selettiva: i pacchetti preparati sono revocati, i risultati già conseguiti non sono promuovibili e diventano stale |
| Una risorsa è condivisa | Il controller li serializza dalla coda delle prenotazioni: readiness logica ≠ readiness di esecuzione |
| Crash del coordinatore a dispatch avvenuto | Il tentativo resta `running` con lease scaduta: la ripresa riconcilia senza re-dispatch automatico; esito incerto = ENVIRONMENT_BLOCKED |
| Completamento ripetuto | Idempotenza per ID evento: stesso payload restituisce l'esito registrato; payload diverso con stesso ID è rifiutato |

**Esempio (Phazly).** Un nodo `react-app` (`SearchBar.tsx`) e un nodo
`functions-python` (endpoint `/search`) lavorano in parallelo perché nessuno
consuma l'output dell'altro mentre lavora: il primo produce `contract:/search@v1`
e il secondo lo consuma solo in integrazione. Al join, con entrambi verdi, il
candidato combinato riceve i gate globali e la review. Se durante l'esecuzione
l'endpoint passa alla versione `v2`, il nodo di integrazione già startato con
`v1` viene invalidato e non può promuovere.

### 1.1 Responsabilità

| Proprietario | Responsabilità canonica |
|---|---|
| `codebase-map` | Evidenze statiche, freschezza, limiti e proiezioni del codice |
| `project-lifecycle` | Intento, piano semantico, archetipi, compositore e task-packet tramite `cycle_packets.py` |
| `senior-review` | Policy, roster, pacchetti di review, panel e verdetti |
| `project-protocol` | Schema del grafo, registro runtime, budget, transazioni e validazione delle consegne |
| `skill-catalog` | Binding e provenienza della conoscenza assegnata ai worker |
| Adapter dell'host | Dispatch, processi, modelli/effort, permessi e stop supportati |
| Umano | Requisiti e autorizzazioni non deducibili dalle evidenze |

Il pianificatore, anche generativo, propone task e dipendenze semantiche per
codice nuovo **o esistente**. Il compilatore verifica e materializza un piano
approvato: non ricava automaticamente requisiti e test corretti da un call graph.
Il decisore propone scelte su opzioni enumerabili. Il controller ammette solo
transizioni previste con evidenze sufficienti. Nessun numero di chiamate LLM
è garantito per la creazione di una feature.

Il protocollo resta una foglia: riceve input espliciti, non apre database della
mappa e non invoca lifecycle o senior-review. `graph-next` non genera prompt.
I template degli archetipi vivono in lifecycle, gli operatori nel contratto
del protocollo. Il compilatore valida tutti i template contro operatori,
tipi di artefatto, gate e provider; i cataloghi per host sono generati.

### 1.2 Limiti dell'enforcement

L'helper può rifiutare una transizione o una consegna non valida. Non può,
da solo, impedire a un coordinatore di chiamare altri tool, modificare file
o spendere token fuori protocollo. Questi divieti sono obblighi di prompt
finché un probe dell'host non dimostra un controllo runtime.
Una checklist o un hash non provano confinamento né correttezza semantica.

### 1.3 Componenti e interfacce di confine (21 ottobre 2026)

Daodan si articola in sei componenti macro. Questo filone costruisce il
graph plan writer e il graph plan executor; per loro gli altri quattro sono
interfacce. Le interfacce si specificano prima delle implementazioni, così
un mock, un prompt LLM, Gutsy o codebase-map si sostituiscono senza toccare
writer ed executor.

| Componente | Ruolo in questo filone | Implementazione attuale | Snodo |
|---|---|---|---|
| Router dei modelli | Interfaccia I4 | `TASK_TIER_CHOICER` (LLM `tier1`) e driver di `tier_router.py` della madre | S3; proposta di tier su escalation S5 |
| Selettore agenti/revisori | Interfaccia I3 | Pavimento di `review_roster.py` e `REVIEWER_CHOICER`; Gutsy solo candidato offline | S4 |
| Codebase mapper | Interfaccia I1 | API MCP di codebase-map | `MAP_SLICE`, `GROUNDING` |
| Specs writer | Interfaccia I2 | Intervista lifecycle e `adr-method` | `SPEC_ADR`, `GROUNDING` |
| Graph plan writer | Costruito qui | Compositore (lifecycle) e compilatore (protocol) | S1, S2, espansioni |
| Graph plan executor | Costruito qui | Controller su `work.json` (protocol) | Dispatch, budget, gate, recovery |

**Regole comuni.**

1. Schema versionato `daodan/<interfaccia>/v1`: un lettore rifiuta una
   versione che non conosce.
2. Busta comune: `schema`, `implementation` (nome e versione), `input_digest`
   della richiesta canonica, `status` (`ok`, `abstain`, `unavailable`) e
   `gaps`. Con stato diverso da `ok` la risposta non porta decisioni. I3 e I4
   aggiungono `decision_id` e i campi di audit di §2.2.
3. La risposta vale solo per la richiesta del suo digest. Un digest diverso,
   un'opzione fuori dall'insieme chiuso o un riferimento fuori dalla richiesta
   rendono non conforme l'intera risposta.
4. Nessun effetto collaterale: l'interfaccia non scrive nel registro, non
   avvia worker e non modifica il progetto. Produce solo il proprio output.
5. L'implementazione propone, la policy di writer o executor decide. Nessuna
   risposta rimuove una lente del pavimento, scende sotto un tier minimo,
   aumenta il budget o aggiunge un arco non dichiarato.
6. Astensione, indisponibilità e risposta non conforme ricevono un default
   dichiarato che non indebolisce mai la policy: pavimento del roster, tier
   di default, ritorno al proprietario. Mai un valore plausibile sostituito
   al posto della risposta (AC17).
7. Ogni interfaccia ha una suite di conformità. Il mock del prototipo e ogni
   implementazione reale la superano prima dello shadow. Superarla prova la
   forma del contratto, non la qualità delle decisioni.

**I1 `daodan/map-slice/v1`: codebase mapper verso writer.** Richiesta:
candidato o snapshot atteso, target (path o simboli), profondità. Risposta:
`snapshot` (`run_id`, `digest`, `freshness`: `fresh`, `stale`, `unknown`),
`components` (id e path disgiunti: unità di lavoro separabili), `edges`
(`from`, `to`, `kind`: `call`, `import`, `contract`; riferimento all'evidenza)
e `gaps` (riferimenti dinamici, file non parsati, perimetro escluso).
Il writer congela solo su una slice `fresh` rispetto al candidato, altrimenti
torna al mapper. Gli archi sono indizi per lock, conflitti di scrittura e
precedenze da proporre al pianificatore, mai archi del grafo invertiti in
automatico (§6). Un gap non è assenza di impatto. Il protocollo riceve la
slice come file con digest e non apre il database della mappa.

**I2 `daodan/approved-spec/v1`: specs writer verso writer.** Risposta:
`spec` (id, path, digest, `status`), `adr_refs`, `requirements` (id, testo,
`kind`: `behavior`, `refactor`, `artifact`, `analysis`; `oracle` tipizzato
rispettivamente `test`, `equivalence`, `artifact`, `review`), `scope` (`in`,
`out`), `contracts` (id, requisito produttore, requisiti consumatori,
artefatto logico), `open_questions`, `authorizations`. Il writer compila solo
con `status = approved` e nessuna domanda aperta; altrimenti il lavoro torna
allo specs writer o all'umano. Il tipo di oracolo segue §4: un RED solo per
`behavior`. Le dipendenze semantiche tra task nascono dai `contracts`
dichiarati, mai dalla mappa.

**I3 `daodan/selection/v1`: selettore agenti/revisori verso writer.**
Richiesta: `purpose` (`review` o `worker`), digest del candidato, hunk
enumerati `H1..Hn` con path e testo, catalogo dei ruoli con digest
(`TRIGGER WHEN` / `DO NOT TRIGGER WHEN`) e il roster `daodan/review-roster/v1`
come pavimento. Risposta: al più una decisione per ruolo del catalogo con
`role`, `selected`, `probability` (o null) e `citation`, un `H_k` della
richiesta (o null). Il writer applica: ruoli applicati uguale al pavimento
più i selezionati con citazione valida; una selezione senza citazione è
ignorata e registrata, mai riassegnata al primo hunk; un ruolo del pavimento
non si rimuove. Il gate leggero blocca solo una lente critica con trigger
reale mancante: una ripreparazione, poi `HUMAN_ESCALATION`. Il risultato
espande la zona review con il freeze versionato di §6. Con
`purpose = worker` (specialisti di stack) vale lo stesso contratto, ma oggi
esiste solo l'implementazione deterministica per segnali di stack: nessuna
evidenza Gutsy copre quella scelta.

**I4 `daodan/routing/v1`: router dei modelli verso executor.** Richiesta:
digest del piano congelato e, per ogni nodo LLM, operatore, testo della task,
ruolo della lente e fatti (`downstream`, `fanin`, chiamanti, visibilità
pubblica). Una chiamata per piano o espansione. Su escalation, una chiamata
per il solo nodo con tier corrente e ultimo tentativo. Risposta: per nodo
`tier` (`tier1`, `tier2`, `tier3`) ed `effort` (`low`, `medium`, `high`),
oppure astensione. L'executor applica in ordine:

1. nodi deterministici (`MAP_SLICE`, `CONTRACT_CHECK`, `WAVE_BARRIER`,
   `INTEGRATE`) senza tier;
2. pavimento per operatore: `tier2` per `SPEC_ADR`, `PLAN`, `VERIFY_FINDING`
   e per le lenti critiche; astensione uguale al default `tier2`, mai sotto
   il pavimento;
3. tetto autorizzato: un pavimento sopra il tetto dà `POLICY_BLOCKED` prima
   di spendere;
4. binding dell'host tramite il driver di `tier_router.py`, nella tripla
   `(model_param, effort_applied, packet_policy)`. Dove l'override non è
   provato, `model_param` è null (`inherit`) e il tier applica solo la
   `packet_policy`; il pavimento garantisce allora il pacchetto, non il modello;
5. adattamento al budget di un passaggio (dispatch, verifica, chiamata al
   router) scendendo verso il pavimento, mai sotto. Pavimenti non coperti
   danno `BUDGET_EXHAUSTED` prima di iniziare.

Il tier vive nel tentativo e non cambia il digest del grafo. I giudici
(`VERIFY_FINDING`) si instradano una volta e non si scalano mai: un verdetto
diverso non deve potersi spiegare con un giudice diverso. L'escalation passa
da S5, addebita la chiamata al router e non azzera il fingerprint (§8). Il
costo di un dispatch in work unit dipende dal tier applicato; con modello
ereditato dal tier della sessione, o dal massimo se ignoto. I pesi sono
policy versionata, non misure.

**Graph plan writer.** Riceve I2 e I1, più I3 alle espansioni. Applica
l'archetipo (S1) e le regole deterministiche (S2) e consegna il piano
congelato con digest. Non chiama l'executor né il router.

**Graph plan executor.** Riceve il piano compilato, la risposta I4 e la probe
dell'host. Possiede `work.json`, budget, prenotazioni, gate e recovery. Non
riscrive il piano: chiede al writer una revisione (replan) o un'espansione.

## 2. Decisioni, composizione e rollout

Gli identificatori S1-S6 restano per tracciabilità, ma non designano tutti
chiamate al modello. L'audit ammette `deterministic`, `llm_tier1`, `system1`
e `human`. La policy obbligatoria non è disattivabile dal classificatore.

| ID | Funzione | Autorità iniziale / ricorso | System-1 |
|---|---|---|---|
| S1 | Selezione archetipo | Regola lifecycle sull'operazione approvata; ambiguità al pianificatore o all'umano | Solo proposta `choice` in esperimento separato |
| S2 | Partizione e archi | Compilatore deterministico sul piano approvato; insufficienza riapre il piano | Nessuna decisione System-1 |
| S3 | Tier ed effort | `TASK_TIER_CHOICER`, vincoli di host e autorizzazione | `choice`/`score`, solo dopo promozione specifica |
| S4 | Attivazione revisori | `REVIEWER_CHOICER` e policy senior-review; nessuna lente obbligatoria rimossa | `noul` per coppia evidenza/ruolo, dopo promozione specifica |
| S5 | Recupero | `RETRY_TRIAGER` propone fra azioni ancora ammesse; controller applica budget e guardie | `choice`, dopo promozione specifica |
| S6 | Review della barriera | Policy senior-review: `lite` alle wave, `full` sul candidato; solo approfondimento ammesso | Nessun downgrade o skip via System-1 |

S3, S4, S5 preservano le opzioni della §3.6 madre. S1 è un'estensione
esplicita non coperta dai tre prompt. S2 e S6 non richiedono un prompt di
fallback. `skip_con_lente_zero` non è una modalità ammessa.
I nomi progettati `lite/full` richiedono un binding esplicito con le forme
implementate `light/branch`; non si rinominano le evidenze storiche.

### 2.1 Modalità

1. `offline`: harness sperimentale sotto `evals/`; nessun effetto sul ciclo.
2. `shadow`: solo dopo il gate previsto dalla madre; il decisore vigente
   resta autorevole, il candidato locale produce un audit separato senza
   cambiare roster, tier, grafo o recovery. Non si inserisce prima di questo
   gate un riferimento al classificatore nel ciclo operativo.
3. `active`: autorizzazione e promozione **per snodo, modello, runtime e policy**.
   Una promozione di S4 non abilita S1/S3/S5. S2/S6 restano deterministici.

L'esperimento sul controller deterministico è separato dalla promozione del
modello: può essere verificato con decisioni registrate o simulate.

### 2.2 Astensione, citazioni e audit

Ogni decisione ha `decision_id`, snodo, implementazione, versione di policy,
digest dello stato e dei candidati, opzioni complete, risposta grezza,
scelta proposta, scelta applicata, motivazione di eventuale rifiuto,
identità runtime, tempi, usage o `unknown` e riferimenti alle evidenze.
Un evento successivo collega l'esito a valle senza riscrivere la decisione.
Il grafo contiene solo `decision_ids`, non una seconda copia delle decisioni.

Python enumera gli ID di evidenza e lega ogni domanda/opzione a snapshot,
lato base/candidato, path, span e digest. La scelta locale conserva quel
binding; non inventa citazioni. Un locator valido prova l'identità della
fonte, non che la fonte supporti semanticamente la scelta. Tale supporto
richiede verifica separata. Un artefatto non-code usa un locator proprio.

`Z`, risposta malformata, opzioni mancanti, encoding incompleto e incertezza
sono `ABSTAIN`, non un voto negativo né un'azione di recovery.
In shadow si registra il gap; in active si usa il decisore di riferimento
solo se disponibile e autorizzato. Senza ricorso ammesso si sospende con
`ENVIRONMENT_BLOCKED`; una decisione di requisito mancante dà
`HUMAN_ESCALATION`. Un ricorso fallito non innesca un altro ricorso automatico.

## 3. Soglie e runtime locale

### 3.1 Policy versionata, non soglie promosse dal pilota

Non esistono soglie operative validate da questa specifica. Il profilo
sperimentale deve fissare prima del set di valutazione: soglia per ruolo,
semantica di `score`, normalizzazione, gestione reject, margine minimo,
aggregazione fra evidenze, controlli obbligatori e condizioni di ricorso.
Una curva sui casi già osservati è descrittiva, non selezione di una soglia
di produzione. Un profilo incompleto blocca `active`.

La calibrazione è una proprietà misurata sul dominio, non una conseguenza
del campo `probabilities`. Non si presume che 0.8 significhi 80% su questi
task. I limiti di contesto e opzioni si verificano per runtime e modello.
Stati non inglesi sono preservati e dichiarati fuori dal dominio valutato;
una traduzione è una trasformazione tracciata, con costo e verifica propri.

### 3.2 Binding del runtime

Il client di protocollo è standard-library Python. Nessun import di inferenza
nella toolchain; pesi e runtime sono una capability esterna provisionata
secondo le autorizzazioni e i vincoli dell'host. `gutsy-inference` e
`llama-server` hanno API diverse: l'adapter deve implementare e verificare
schema, tokenizzazione, prompt, logits di tutte le opzioni, calibrazione,
reject e gestione del contesto. Un `/completion` a token singolo con top-k
parziale non dimostra equivalenza con `/v1/systemone`.

Non si prescrive `uv` per un eseguibile nativo. Nessuna installazione
automatica nel workflow; un host che vieta provisioning richiede il suo
percorso di manutenzione. Le dipendenze locali di metodo restano obbligatorie;
l'assenza del sidecar sperimentale non giustifica saltare un provider richiesto.

### 3.3 Proprietà, avvio e arresto

L'adapter esecutore possiede il processo per run. Il registro conserva:
`instance_id`, host/versione, PID e ora di creazione, porta assegnata,
percorso/digest binario, revisione/hash/quantizzazione pesi, digest prompt e
calibrazione, device/thread/batch, limiti e profilo soglie.

- Prima dell'avvio: probe dei prerequisiti, porta assegnata dal sistema
  ove supportato, oppure prenotazione esclusiva e handshake verificato.
- Bind loopback, CORS disabilitato, configurazione e log posseduti dal run.
  Non riutilizzare un endpoint soltanto perché risponde a `/health`.
- Handshake a ogni connessione o riavvio: confronto con identità registrata.
  Se il server non espone tale identità serve un wrapper verificato o un
  binding processo/porta dimostrabile; altrimenti capability non disponibile.
- Hash dei file verificati all'avvio, nuova verifica dopo riavvio; self-check
  cache e controlli noti all'avvio. Questo non certifica la calibrazione.
- Poll di salute limitato durante il lavoro, backoff e massimo un riavvio
  per run come default proposto. Ogni riavvio consuma budget e rifà handshake.
- Su conclusione, cancellazione o perdita del proprietario: stop cooperativo
  con grace timeout, poi terminazione del solo processo posseduto se autorizzata.
  Serve una lease/supervisione dell'adapter, non solo un `finally` LLM.
- Resume: riconciliare instance ID, PID, creation time, comando e directory.
  Nessuno sweep generico dei processi Python; un PID da solo non prova ownership.
  Se cleanup non è verificabile, registrare il residuo e bloccare nuovo avvio
  sul medesimo binding.

### 3.4 Tempo, cap e ricorso

Default **proposti e configurabili prima del run**: deadline 30 s per domanda,
120 s per batch logico; cap 2 ricorsi LLM e 1 riavvio sidecar. Al primo
ricorso si notifica il degrado; al secondo fallimento consecutivo sidecar si
apre il circuito. Ulteriori decisioni dipendenti attendono recovery o umano.
In shadow nessun timeout del candidato blocca il decisore autorevole.

Una deadline comprende connessione, invio, lettura e coda. Un socket timeout
non basta contro risposte lente a frammenti: l'adapter deve imporre il limite
totale e un limite ai byte di risposta. Alla scadenza chiude la richiesta,
registra l'esito incerto e non lancia una duplicata mentre il lavoro remoto
potrebbe ancora essere attivo. La cancellazione non supportata è un gap.

Ogni azione esterna, inclusi test, worker e fallback, ha una deadline nel
run. Il tempo attivo usa un clock monotono; il limite elapsed persistito
include pause e riavvii. Se l'orologio rende il residuo non affidabile, si
blocca la ripresa per riconciliazione invece di aumentare il budget.
Latenze di load, coda, inferenza, domanda e batch si registrano separatamente
con hardware/runtime; nessun confronto diretto tra secondi/query e secondi/caso.

## 4. Catalogo degli operatori e gate

Il catalogo appartiene a project-protocol; i metodi specialistici conservano
ownership. I gate sono tipizzati: `command`, `artifact`, `review`, `authorization`.
Un verdetto LLM è evidenza semantica, non un test deterministico.

| Operatore | Esecutore/produttore | Consegna e condizione di accettazione |
|---|---|---|
| `MAP_SLICE` | codebase-map | Slice verificata con snapshot, freschezza e lacune |
| `SPEC_ADR` | lifecycle e adr-method | Record proposto, review e approvazioni richieste |
| `ANALYZE` | Ruolo dichiarato dal metodo | Analisi con fonti, copertura e questioni aperte |
| `PLAN` | Pianificatore lifecycle | Task, contratti, scope e dipendenze riesaminati |
| `ORACLE_RED` | testing:test-writer | Test discriminante fallito per causa prevista, non errore ambiente |
| `CODE_PATCH` | Specialista dello stack | Patch nel write_set e verifica del requisito |
| `EDIT_ARTIFACT` | Proprietario del documento/artefatto | Modifica autorizzata e controlli pertinenti di contenuto/parità |
| `CONTRACT_CHECK` | Tool o revisore di contratto | Evidenze di compatibilità con gap espliciti |
| `REVIEW_LENS` | Ruolo selezionato da senior-review | Finding o assenza di finding con copertura, non solo file presente |
| `VERIFY_FINDING` | Panel senior-review | Esito semantico e prove, compreso contested |
| `REPAIR_PATCH` | Specialista proprietario | Nuova versione dell'artefatto e regressioni verificate |
| `WAVE_BARRIER` | Coordinatore tramite controller | Consegne contabilizzate, snapshot stabile, review richiesta accettata |
| `INTEGRATE` | Metodo finish e adapter Git | Autorizzazioni pertinenti, gate finali e integrazione registrata |

Ogni operatore dichiara pre/postcondizioni, schema input/output, privilegi,
provider, deadline e politica di errore. Un oracle RED è richiesto per un
cambiamento comportamentale che lo prevede; non si forza un test fallente
su puro refactoring, analisi o modifica documentale. In quei casi il gate
protegge rispettivamente equivalenza, fondatezza o contratto dell'artefatto.
L'AST può suggerire casi limite, non fissare l'oracolo di business.

## 5. Piano immutabile e stato canonico

### 5.1 File e identità

Il run root è quello risolto dal protocollo del progetto (main checkout via
Git common directory); il binding Tri-Tech può assegnare `.tritech/daodan`.
Nessun helper deriva il root dal testo di un prompt.

- `graphs/<digest>.json`: piano immutabile, scritto dal compositore; versione
  schema, predecessore, nodi, archi, policy e riferimenti alle decisioni.
- `work.json`: **unica autorità runtime**, con estensione proposta versionata
  `execution` (grafo attivo, nodi, tentativi, lease, artefatti, ledger budget,
  decisioni/eventi append-only e outcome). Nessun runtime mutabile nel grafo.
- Payload, output e gate evidence: file immutabili referenziati con digest.
  Le viste del grafo e del Decision Log sono derivate, non altre autorità.

Identità: `node_id` logico stabile; `attempt_id` univoco per esecuzione;
`delivery_id` distinto per tentativo; `artifact_id` logico stabile con
`version` e `digest` immutabili per pubblicazione. Un repair non rinomina
il contratto in `_v2`: aggiorna la versione e conserva tutte le precedenti.

Il piano congela scope, topologia, read/write set, gate, template e policy.
Il tier iniziale è un default; l'escalation ammessa dalla policy vive nel
tentativo, non muta il piano. Cambiare un gate o write_set richiede una nuova
revisione approvata e non modifica retroattivamente le prove.

### 5.2 Schema normativo minimo

Un grafo contiene `schema`, `run_id`, `parent_graph_digest` (null alla prima
revisione), `nodes`, `recovery_edges`, `policy_digest`, `decision_ids`.
Il digest è SHA-256 della serializzazione canonica UTF-8, chiavi ordinate,
separatori fissi e senza NaN; è esterno al corpo hashato.

Ogni nodo contiene `id`, `op`, `executor_ref`, `needs`, `consumes`, `produces`,
`read_set`, `write_set`, `resource_locks`, `gate_refs`, `decision_ids`.
I consumi nominano artefatti logici e versione richiesta; il tentativo lega
la versione concreta. Gli executor_ref sono binding verificati di ruoli,
metodi o tool, mai identità inventate né confusione ruolo/skill.
I gate command hanno argv e cwd strutturati, ambiente risolto, timeout,
atteso e parser di esito; il modello non fornisce shell libera da eseguire.

Ogni recovery edge ha sempre `from`, `when`, `action`, `target` e `routes`.
`target` è null per `TRIAGE` e un node_id per `OPEN_REPAIR`.
`routes` è vuoto per `OPEN_REPAIR`; per `TRIAGE` contiene esattamente le tre
opzioni S5 con azione tipizzata e destinazione valida. `REOPEN_PLAN` punta
a PLAN; `RETRY_NODE` e `FRESH_ESCALATION` al nodo fallito. Le guardie del
controller possono rendere un'opzione non disponibile ma non aggiungerne altre.
Gli edge sono emessi dai template lifecycle e validati dal protocollo;
S5 sceglie fra azioni ancora ammesse, non scrive edge.

Il validatore rifiuta: ID duplicati/ignoti, consumi senza produttore o input
esterno dichiarato, cicli in `needs` uniti agli archi producer/consumer,
operatori/provider assenti, gate non risolvibili, policy/digest incoerenti,
copertura insufficiente dei requisiti e conflitti di accesso dichiarati.
La copertura semantica richiede review, non è provata dal solo validatore.

### 5.3 Budget unico e terminazione

`work.budget.execution` possiede limiti iniziali immutabili e ledger di
prenotazioni/consumi. Il grafo contiene soltanto il riferimento alla policy.
Limiti obbligatori: work units totali, tentativi per nodo, replan, verifiche
diagnostiche, chiamate di ricorso, riavvii, tempo attivo ed elapsed.
Si dimensionano dal piano approvato; nessun limite universale di 18 passi.

Prima di iniziare un'azione che può consumare risorse si prenota e addebita
atomicamente una work unit: dispatch, decisione modello, verifier, riparazione,
replan o riavvio. Completion duplicata non paga di nuovo; crash o timeout
non rimborsano una prenotazione di cui l'esecuzione è incerta. Le letture di
stato e la chiusura terminale non consumano unità, non avviano lavoro e non
possono riaprire il run. Ogni percorso di recovery attraversa un addebito.

Una nuova revisione del grafo mantiene lo stesso run e ledger. Il freeze
richiede parent digest e revisione attesa di work.json; respinge reset di
limiti, contatori di stallo e tentativi, anche dopo rinomina di task
(lineage obbligatoria). `update` generico deve applicare le stesse guardie;
nessun percorso di scrittura può aumentare il residuo. Questo richiede
modifiche future a validate_transitions, non è già garantito dal contratto v1.

Richiedere altro budget conclude/sospende la campagna; un nuovo run richiede
autorizzazione esplicita e riferimento al precedente, mai apertura automatica.
La terminazione del **lavoro ammesso dal controller** deriva dal numero finito
di unità, deadline e recovery limitati. Non garantisce la terminazione di tool
fuori protocollo né di processi che l'host non può interrompere.

## 6. Composizione del piano e macro-flusso

Macro-stadi obbligatori: `PREFLIGHT` (scope, ambiente e grants), `GROUNDING`
(requisiti, fonti, record ove richiesto), `PLAN` (grafo approvato), `EXECUTE`
(task e barriere), `CANDIDATE_REVIEW` (risultato complessivo), `CLOSE`
(integrazione autorizzata o consegna read-only). Analisi e planning-only
terminano con il loro artefatto verificato, senza merge e senza patch fittizie.

Archetipi lifecycle richiesti: `bugfix_repro_first`,
`contract_callee_to_caller`, `db_migration_two_phase`, `pure_refactor`,
`ui_async_flow`, `artifact_edit`, `planning_only`, `analysis_only`,
`review_only`. Ogni template espande solo operatori §4, inclusa
`WAVE_BARRIER`, e ha casi di accettazione propri.

`graph_compose.py` riceve piano semantico approvato, slice della mappa,
requisiti/ADR, cataloghi e policy risolti. Verifica freschezza rispetto al
candidato prima del freeze: file cambiati, riferimenti dinamici, parser
assenti e dipendenze ignote sono gap, non assenza di impatto.

Le chiamate del codice sono indizi per le precedenze dei task, non archi da
invertire ciecamente. Ricorsione e componenti cicliche richiedono un task
coeso o una strategia di migrazione del contratto; migrazioni DB e rollout
possono richiedere expand/contract, backfill e compatibilità temporanea.
Un callee non deve sempre essere modificato prima del caller.

S2 applica regole deterministiche al piano (dimensione task, ownership,
artefatti, lock e dipendenze). Se manca la decomposizione semantica ritorna
al pianificatore; non inventa un task per ogni simbolo. Con identici input,
policy e decisioni registrate, la compilazione deve produrre lo stesso digest.

S4 lavora quando esiste il candidato della barriera: può produrre una
revisione del sottografo review attraverso lo stesso freeze versionato.
Nessun roster dipende da un diff futuro immaginato. In shadow la revisione
proposta da System-1 non viene attivata.

## 7. Controller, concorrenza e ripresa

### 7.1 Stati e protocollo di dispatch

Stati runtime del nodo: `pending`, `ready`, `reserved`, `running`,
`verifying`, `succeeded`, `failed`, `stale`, `blocked`, `cancelled`.
`ready` è calcolato, non un flag dichiarato dal worker. Lo storico delle
deliveries resta terminale; riaprire un nodo crea un tentativo e delivery nuovi.

1. `graph-next`: sotto writer lock e CAS sulla revisione del registro,
   seleziona la frontiera compatibile con lock/budget e prenota tentativi.
   Ritorna reservation ID, scadenza, graph digest, input versionati e
   riferimenti per i produttori di pacchetti, non il testo dei pacchetti.
2. Lifecycle produce il task-packet, senior-review il review-packet. Il
   controller ne registra digest e input; questi sono gli unici produttori.
3. `graph-start`: immediatamente prima del dispatch verifica reservation,
   holder, lease, policy, snapshot e digest; registra fencing token e
   intent di dispatch. L'adapter collega il worker handle al tentativo.
4. Il worker consegna output e candidato immutabili. `graph-complete`
   riserva la verifica, esegue il gate fuori lock, poi riacquisisce lock e
   CAS, ricontrolla digest e persiste esito, budget, artefatti e invalidazioni
   in **un unico commit del registro**. Output e prove sono staged prima
   dell'atomic replace; un crash non crea un successo senza evidenza durevole.

Gli ID di evento/completion sono idempotenti. Una seconda richiesta identica
ritorna l'esito registrato; un payload diverso con stesso ID è rifiutato.
Lease scaduta non autorizza un nuovo dispatch finché il precedente potrebbe
essere attivo. Le reservation non dispatchate scadono e i pacchetti sono revocati.

### 7.2 Isolamento e invalidazione

Parallelismo di scrittura solo nel modo WORKTREE e con isolamento verificato
per worker (worktree/snapshot separati, risorse esterne e schema DB dedicati).
Disgiunzione dei write_set non isola i read_set o gli effetti esterni. Se
l'host non fornisce isolamento, esecuzione sequenziale. I gate girano sul
**candidato post-patch immutabile**, non sulla baseline di dispatch né su un
worktree modificato contemporaneamente. Integrazione seriale dei risultati,
poi gate di integrazione e review del candidato combinato.

Invalidazione: nuova versione di un artefatto marca stale i consumatori
che hanno legato la precedente e propaga la stalezza ai loro risultati;
gli edge `needs` che esigono ri-verifica propagano conservativamente.
P produce X e Y, C consuma solo X: Y cambiato da solo non invalida C, salvo
altre letture/dipendenze dichiarate. Dipendenze non risolte impongono
invalidazione conservativa dello scope della barriera, mai promessa di completezza.

Recovery riapre il lavoro; invalidazione revoca l'utilizzabilità delle prove,
non cancella né riscrive le consegne storiche. Contratti mantengono ID logico;
i nuovi tentativi consumano nuove versioni. Pacchetti pending sono revocati,
worker running ricevono stop ove supportato e i loro output stantii non sono
promuovibili. Si ricalcola la frontiera dopo ogni commit.
I gate globali di candidato richiedono sempre il digest corrente completo;
riuso di prove locali richiede un binding d'input dimostrato e policy esplicita.

### 7.3 Crash e resume

Il resume v1 rifiuta cambiamenti del candidato: non si aggira tale controllo.
La futura operazione `graph-resume` riconcilia graph digest, revisione,
lease, worker handle, journal degli intent e file prodotti nello scope
autorizzato. Modifiche estranee bloccano la ripresa e non vengono ripristinate.

Crash prima del dispatch: revoca reservation; dopo intent ma senza handle:
esito incerto, cercare il worker tramite ID dell'adapter. Se non risolvibile,
`ENVIRONMENT_BLOCKED`, mai dispatch duplicato automatico. Crash dopo il gate
ma prima del commit: riusare solo prove staged integre con identico candidato,
altrimenti una nuova verifica addebitata. Il registro torna sempre a una
revisione completa; i file orfani non diventano prove per semplice presenza.

### 7.4 Terminali e migrazione di work.toml

Proposta esplicita di nuovo schema `daodan/work/v2`: `status` ammette
`in_progress`, `complete`, `stopped`; `execution.outcome` è null durante il
lavoro, poi uno dei valori sotto. V1 resta leggibile con le sue regole;
migrazione esplicita produce un nuovo record con origine e hash del v1.
I consumer non compatibili rifiutano v2, non ignorano i nuovi stati.

| Outcome | status | Significato |
|---|---|---|
| `VERIFIED_SUCCESS` | complete | Tutte le obbligazioni correnti soddisfatte sul candidato corrente |
| `REFUTED` | stopped | Obiettivo/ipotesi smentita con prova; nessuna integrazione |
| `STALLED_SAME_FAILURE` | stopped | Ripetizione senza progresso verificabile |
| `BUDGET_EXHAUSTED` | stopped | Limite work units, tentativi o tempo raggiunto |
| `VERIFIER_UNSTABLE` | stopped | Esiti incompatibili sullo stesso input verificato |
| `ENVIRONMENT_BLOCKED` | stopped | Capability, processo o verifica non disponibile |
| `HUMAN_ESCALATION` | stopped | Decisione essenziale non risolta |
| `POLICY_BLOCKED` | stopped | Autorizzazione o vincolo non soddisfatto |

`stopped` non equivale a successo. Conserva consegne fallite, gate non passati,
motivi e obbligazioni non soddisfatte. `complete` continua a richiedere tutte
le consegne **correnti richieste**, gate correnti e grants pertinenti.
Eventi di supersessione legano obbligazioni a nuove delivery senza eliminare
i vecchi gate o farli risultare passati. Obbligazioni invariate restano richieste;
ritirarne una richiede una decisione di scope autorizzata, non un replan tecnico.
Una ripresa autorizzata da stopped conserva outcome storico e budget residuo;
non riapre un run esaurito né converte retroattivamente un fallimento in successo.

## 8. Stallo, verifier e Fresh Escalation

Il verifier emette un risultato strutturato: ID/versione, input digest
(candidato, test, ambiente, configurazione), exit classification,
test ID e asserzioni atteso/ottenuto. Il raw output è conservato.
La normalizzazione versionata rimuove solo rumore documentato (timestamp,
temp path), non numeri/valori semanticamente rilevanti.

`failure_fingerprint` hash di verifier version, test ID, classe di errore,
asserzione normalizzata e identità logica del task. Non include attempt ID,
tier, prompt o hash del candidato; questi stanno accanto al fingerprint.
`evidence_delta` confronta esiti strutturati omogenei e nuove prove pertinenti;
il cambio di prompt/tier non è progresso. Un delta diverso non prova da solo
un miglioramento: il progresso richiede un oracle prima fallito ora passato
senza regressioni, o la risoluzione documentata di una precondizione bloccante.

Default proposto: due fallimenti consecutivi equivalenti senza progresso
verificato fermano il task. Il primo fallimento può ricevere un solo
`retry_same_tier` se la policy classifica il difetto come meccanico e i budget
lo consentono; non si richiede una baseline precedente inesistente.
Fresh Escalation usa nuovo worker, requisiti, codice candidato, diagnostica
grezza ed evidenze pertinenti, senza ragionamento privato del worker precedente.
Conserva lineage, fingerprint e consumi. Escalation non disponibile o già al
massimo tier lascia soltanto le altre azioni ammesse o HUMAN_ESCALATION.

Esiti incompatibili del medesimo verifier sullo stesso input digest completo
attivano `VERIFIER_UNSTABLE`: bloccare promozione e diagnosticare separatamente
ambiente, oracolo e prodotto. Ripetizioni diagnostiche hanno cap e deadline,
consumano work units/tempo ma non il contatore delle riparazioni di codice.
Non sono gratuite o illimitate. Un singolo pass non dimostra assenza di flakiness.

## 9. Review e autorità semantica

Primi passaggi isolati e sigillati, visibilità dei peer solo dopo la consegna.
Il panel resta posseduto da senior-review; questa spec non sostituisce con
un voto locale o una probabilità le sue regole di conferma e contestazione.
Un finding refutato non termina l'intero lavoro: `REFUTED` di run si applica
solo all'obiettivo investigativo pertinente. Finding bloccanti contestati
restano bloccanti secondo la policy autorevole.

Un cambiamento della policy del panel rispetto all'implementazione esistente
richiede una modifica coordinata del proprietario; non si afferma che
l'implementazione attuale sia già un aggregatore esclusivamente per evidenza.
La review globale verifica interazioni tra rami e requisiti indipendenti dai test
scritti dall'implementatore. S6 non elimina mai tale passaggio.

## 10. Evidenza disponibile e correzioni al pilota

Questi numeri sono descrittivi dei file salvati, **non un A/B controllato**.
Le basi, gli input, i runtime e le policy sono diversi. Eccessi sui casi
C01-C11 sono selezioni non presenti nelle etichette positive parziali, non
falsi positivi tutti dimostrati. I team hanno invece required/allowed espliciti.

| Esperimento | Recall attesi | Critici osservati | Eccessi/caso | Base |
|---|---|---|---|---|
| LLM validato | 4/16 | 1/3 | 0.86 | 7 casi validi su 11 |
| Julia esatto | Non valutabile | Non valutabile | Non valutabile | 0/11 completi |
| Julia adattato | 14/18 | 5/5 | 12.44 | 9 casi |
| AST dominio | 15/23 | 3/5 | 2.5 | 10 etichettati su 11 |
| AST + Gutsy V1, curva a 0.40 | 16/23 | 3/5 | 3.4 | 10 etichettati su 11 |
| Summary v2, sistema ibrido | 18/23 | 4/5 | 2.4 | 10 etichettati su 11 |

Fonti: `RESULTS.md`, `static-router-comparison.json`, `gutsy-comparison.json`
e `gutsy-v2-summary.json` sotto `evals/senior-review/choicer-eval/` e relativo
`runs/20261020T100258Z/`. Team V1 a 0.50: 31/39 obbligatori, 12 fuori
perimetro, soltanto 2/12 team accettabili. Famiglie: 8/8 sui controlli piccoli.
Le sei demo model-router non hanno un oracle indipendente di modello minimo
sufficiente: non costituiscono una misura di accuratezza 6/6.

Limiti che impediscono promozione:
- V1 usa un backend PyTorch custom su Qwen3Next e tokenizer ricostruito;
  il self-check cache non prova equivalenza con Qwen3.5/llama.cpp ufficiale.
  `decide_fast` bypassa parti dell'Engine. Occorre parity indipendente.
- `run_gutsy_benchmark.py` taglia gli hunk e lo stato a 3800 caratteri e
  sostituisce negativi mancanti: la Suite 3 non è catalogo/input esatto
  lossless, contrariamente al precedente report.
- V2 usa contesti di modulo scritti manualmente per case ID, otto lenti
  mirate, generalista sempre attivo e regole per estensioni. Non è prova di
  estrazione automatica codebase-map né di selezione dal catalogo completo.
- `probe_gutsy_v2.py` usa 0.30/0.50 su probabilità normalizzata con OR-lettera;
  `run_gutsy_v2_eval.py` usa lettera A oppure, per critici, p_A >= 0.15 e
  p_A > p_B. Entrambi scrivono `gutsy-v2-summary.json`: senza binding
  immutabile input/script/runtime non si attribuisce il summary a una soglia.
- Citazioni v2 vuote in C08-C11, parziali altrove; il runner può sostituire
  un rifiuto con il primo hunk. Non è verifica semantica delle citazioni.
- Nessuna calibrazione dimostrata su S1/S3/S5/S6. Premise senza positivi
  nella base C01-C11; non generalizzare l'assenza alla suite dei 22 ruoli.
- Le latenze registrate v2 sono medie per caso delle query (circa 1.5-3.8 s),
  non percentili né durata end-to-end; nessuna misura AST <5 ms provata qui.
- La baseline LLM ha tre errori di citazione e uno di lunghezza motivo;
  184073 token è una stima characters/4, non usage. Inferenza locale evita
  chiamate LLM hosted nel routing, non costo computazionale o tokenizzazione.
- Processi Python osservati non sono stati attribuiti: non sono prova di
  orfani Gutsy. Nessuna proprietà su cinque host è dimostrata da questi numeri.

## 11. Verifiche richieste e criteri di accettazione

Ogni caso sotto è un requisito di verifica futura, non un test già eseguito.

| ID | Scenario | Esito richiesto |
|---|---|---|
| AC01 | Due next concorrenti sullo stesso ready | Un solo tentativo prenotato e addebitato |
| AC02 | Completion ripetuta o con payload alterato | Idempotenza oppure rifiuto, mai doppio consumo |
| AC03 | Replan ripetuto e rinomina dei task | Ledger/lineage conservati, arresto al limite |
| AC04 | Repair di nodo già delivered | Nuova delivery, vecchia prova conservata ma stale |
| AC05 | Produttore X/Y cambia solo Y | C che legge solo X riusabile se binding completo |
| AC06 | Invalidazione prima di start o durante worker | Packet revocato o output non promuovibile |
| AC07 | Crash prima/dopo intent, gate e commit | Resume riconcilia senza doppio dispatch o falso verde |
| AC08 | Due worker scrivono mentre parte un gate | Isolamento di snapshot o sequenzializzazione |
| AC09 | Verifier alterna esiti su identici input | Instabilità, diagnostica limitata, nessuna promozione |
| AC10 | Stesso errore con nuovo tier/prompt | Nessun progresso fittizio, stallo e budget preservati |
| AC11 | Sidecar occupato, sbagliato, morto, slow-drip | Identity gate, deadline totale, circuito e cleanup |
| AC12 | Modello/calibrazione cambiati al riavvio | Rifiuto, niente decisioni mescolate |
| AC13 | Missing provider, opzioni o evidenza troncata | Gap esplicito, nessuna lente obbligatoria saltata |
| AC14 | Tentativo di aumentare budget via update | Rifiuto anche fuori graph-complete |
| AC15 | Terminale non-successo e lettore v1 | stopped distinto da complete; lettore incompatibile rifiuta |
| AC16 | Tutti i nove archetipi, incluso read-only | Solo operatori registrati e gate pertinenti; nessun merge fittizio |
| AC17 | Citazione rifiutata / input inesistente | Astensione, nessuna sostituzione col primo hunk |
| AC18 | Policy shadow e active per snodo | Shadow senza effetti; promozione S4 non abilita S5 |
| AC19 | Recursion/ciclo del codice e piano incompleto | Replan semantico, non DAG inventato |
| AC20 | Input storici congelati | Nessuna riscrittura; nuove prove in run distinto |
| AC21 | Risposta I1-I4 con schema ignoto, digest di un'altra richiesta, opzione o riferimento fuori insieme | Risposta intera non conforme; default della policy, mai più debole |
| AC22 | Router sotto pavimento, sopra tetto, astenuto o indisponibile | Pavimento, tetto e default applicati; pavimento sopra tetto `POLICY_BLOCKED` senza spesa |
| AC23 | Host senza override del modello | `model_param` null, `packet_policy` del tier, costo dal tier di sessione o dal massimo |
| AC24 | Escalation di un giudice, o escalation seguita dallo stesso fallimento | Giudice rifiutato; `STALLED_SAME_FAILURE` con fingerprint invariato |
| AC25 | Selettore omette o deseleziona un ruolo del pavimento, o seleziona senza citazione | Pavimento sempre applicato; selezione senza citazione ignorata e registrata |

Per ogni test: input, oracle indipendente, failure attesa, artefatti, snapshot
e comando. Matrice host distinta per Claude, OpenCode/Tri-Tech, Codex, Copilot,
Pi: dispatch/isolation, modelli, lease, stop, sidecar e path binding.
Compilazione e capability dichiarate non sostituiscono probe reali.

## 12. Piano di consegna e promozione

1. Correggere documentazione/provenienza e mantenere i risultati storici;
   nessun nuovo benchmark a pagamento implicito.
2. Dopo approvazione: schema v2 e migrazione, budget/lease/terminali e
   compatibilità dei consumer; AC01-AC15 con executor simulati.
3. Compositore e unico produttore di ogni packet, validazione di tutti gli
   archetipi; AC16-AC20. Prove su host disponibili senza nuove garanzie inventate.
4. Eval offline per snodo con runtime ufficiale o parity dimostrata, payload
   completi immutabili, provenienza, tutti i ruoli pertinenti, gold fuori input.
   Separare training/calibrazione da held-out; fissare soglie prima del test.
5. Shadow autorizzato secondo la madre: output registrati senza effetto;
   misurare errori decisionali e qualità downstream, non solo accordo fra modelli.
6. Active per binding/snodo solo con falsi negativi critici non peggiori della
   baseline matched, supporto premise, copertura e incertezza dichiarati,
   risparmio netto osservato includendo preprocessing/ricorso/errori e costo CPU.

Metriche separate: recall con denominatore, fuori perimetro, calibrazione su
held-out, team accettabili, ritentativi/stallo, coverage, ricorsi/cap, latenza,
CPU e usage noto/unknown. Non si sommano secondi e token come stessa unità.
Decision audit rate conta i campi applicabili: probabilità non applicabili
per decisioni deterministic/human non sono falsi gap.

Decisioni risolte nel disegno: S2 deterministico, S6 policy-owned, runtime
canonico in work.json, delivery per tentativo, budget per run attraverso
replan, packet ai proprietari, isolamento prima del parallelismo.
Restano gate sperimentali: quantizzazione/runtime di riferimento, soglie
validate per snodo e prove host. La loro assenza mantiene System-1 offline;
non impedisce di verificare separatamente il controller con fixture.
