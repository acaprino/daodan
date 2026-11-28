# Senior Review: catalogo completo dei reviewer ed esempi

Guida strutturata a tutte le **10 composizioni** e ai **59 ruoli atomici** di `daodan/review/catalog.toml` e `daodan/review/roles/*.md`, organizzata su tre livelli:
1. **Le 10 composizioni**: come i membri si spartiscono il lavoro su uno scenario concreto.
2. **I 59 ruoli atomici**: scheda compatta a 3 punti fissi (*Cosa cerca*, *Trappola tipica*, *Prova dal grafo*).
3. **Casi reali verificati**: solo incidenti davvero accaduti (con progetto, commit, sintomo, causa e rimedio), senza casi inventati.

La fonte normativa eseguita dall'LLM resta `daodan/review/catalog.toml`, `daodan/review/roles/<nome>.md` e `plugins/senior-review/skills/defect-taxonomy/references/*.md`.

---

## 1. Le 10 composizioni e come si spartiscono il lavoro

Le composizioni non hanno un file ruolo proprio: `daodan composition` le espande nei membri atomici elencati in `[reviewers.compositions]` di `daodan/review/catalog.toml`. Ogni ruolo gira su `senior-review:isolated-worker` partendo dal grafo di **Codebase Map**.

### `code-auditor`
- **Membri**: `local-correctness`, `local-concurrency`, `input-validation`, `resource-lifecycle`, `algorithmic-cost`, `security-auditor`, `data-integrity-auditor`, `chicken-egg-detector`, `temporal-resilience`, `distributed-flow-auditor`, `api-contract`, `logic-integrity`.
- **Scenario concreto**: su una PR che aggiunge un endpoint di importazione CSV, `input-validation` controlla dimensione/parsing sicuro, `algorithmic-cost` cerca loop $O(n^2)$, `resource-lifecycle` verifica chiusura di file/stream su errore, `data-integrity` controlla transazione e upsert, `logic-integrity` verifica gli invarianti di dominio.

### `security-auditor`
- **Membri**: `authorization`, `session-delegation`, `secret-exposure`, `input-validation`, `untrusted-resource`, `browser-security`, `callback-authenticity`, `ai-boundary`, `audit-trail`, `capacity-quota`.
- **Scenario concreto**: su un endpoint di export fatture con webhook e allegati, `authorization` verifica l'isolamento multi-tenant sull'ID, `untrusted-resource` controlla path traversal/SSRF sugli allegati, `callback-authenticity` verifica la firma HMAC del webhook, `secret-exposure` verifica che i log di errore non espongano token, `audit-trail` controlla la tracciabilità dell'export.

### `data-integrity-auditor`
- **Membri**: `transaction-integrity`, `schema-coherence`, `cache-consistency`, `data-representation`, `data-retention`.
- **Scenario concreto**: su una migrazione che introduce un campo saldo e una cache Redis, `schema-coherence` confronta DDL, ORM e SQL manuale, `data-representation` segnala l'uso di `FLOAT` per denaro, `transaction-integrity` verifica il lock contro double-spend, `cache-consistency` controlla invalidazione e chiave multi-tenant, `data-retention` verifica la cancellazione GDPR.

### `distributed-flow-auditor`
- **Membri**: `message-delivery`, `remote-effect`, `service-resilience`, `session-delegation`, `environment-binding`.
- **Scenario concreto**: su un servizio ordini che pubblica su RabbitMQ e chiama un gateway pagamenti, `message-delivery` controlla `ack` dopo l'elaborazione e DLQ, `remote-effect` verifica outbox e chiave di idempotenza, `service-resilience` verifica timeout/backoff/circuit breaker, `environment-binding` verifica che l'endpoint di produzione non cada in fallback su staging.

### `performance-auditor`
- **Membri**: `sql-efficiency`, `algorithmic-cost`, `asset-delivery`, `capacity-quota`, `runtime-cost`, `resource-lifecycle`, `responsiveness`.
- **Scenario concreto**: su una dashboard lenta con chiamate LLM e query ORM, `sql-efficiency` trova le query N+1, `algorithmic-cost` trova l'ordinamento ripetuto nel loop, `asset-delivery` segnala un bundle da 1,2 MB caricato eager, `runtime-cost` verifica il cap sui token LLM, `responsiveness` segnala il parsing sincrono sul main thread.

### `operability-auditor`
- **Membri**: `observability`, `service-health`, `release-compatibility`, `environment-binding`, `feature-flag`, `recovery`, `build-pruning`.
- **Scenario concreto**: prima di un rilascio in rolling deploy, `release-compatibility` blocca una migrazione che droppa una colonna ancora letta dalla versione N-1, `service-health` controlla che la liveness probe non dipenda da servizi esterni, `feature-flag` verifica le combinazioni di flag, `observability` segnala `except: pass`, `build-pruning` verifica che la build di release non elimini handler caricati per nome.

### `cleanup-auditor`
- **Membri**: `application-reachability`, `dependency-usage`, `artifact-lifecycle`, `asset-delivery`, `secret-exposure`, `workspace-hygiene`.
- **Scenario concreto**: dopo un refactoring, `application-reachability` trova moduli/export senza più consumatori, `dependency-usage` individua pacchetti rimasti in `package.json`, `artifact-lifecycle` segnala vecchi README/script obsoleti, `workspace-hygiene` blocca file di build committati per errore.

### `tauri-auditor`
- **Membri**: `tauri-ipc`, `tauri-hardening`, `tauri-sync`, `tauri-reliability`, `build-pruning`.
- **Scenario concreto**: su una nuova feature di un'app desktop Tauri, `tauri-ipc` verifica che i `#[tauri::command]` non accettino path arbitrari dalla webview, `tauri-hardening` controlla `capabilities/*.json` e CSP, `tauri-sync` cerca `Mutex` tenuti attraverso `.await` e divergenze tra finestre, `tauri-reliability` cerca I/O bloccante sul main thread e `.unwrap()` su input utente.

### `accessibility-auditor`
- **Membri**: `accessible-navigation`, `accessible-perception`.
- **Scenario concreto**: su una modale di configurazione con form, `accessible-navigation` verifica focus trap, ordine di tabulazione e chiusura con `Esc`; `accessible-perception` verifica etichette associate, errori annunciati via `aria-describedby` e contrasto nei temi chiaro/scuro.

### `dependency-auditor`
- **Membri**: `dependency-usage`, `dependency-provenance`.
- **Scenario concreto**: su una PR che tocca `package.json` / `uv.lock`, `dependency-usage` verifica che il pacchetto sia effettivamente usato e nella sezione giusta (`dependencies` vs `devDependencies`), `dependency-provenance` verifica origine, pin di versione e rischi noti.

---

## 2. I 59 ruoli atomici (per area)

### Area A — Correttezza, logica e architettura (10 ruoli)

#### `local-correctness-auditor`
- **Cosa cerca**: valori locali, rami di controllo, aritmetica, conversioni, gestione errori e stato d'istanza.
- **Trappola tipica**: `offset = (page - 1) * limit` con `page <= 0`, oppure un ramo `if/else` che ritorna `None`/`undefined` silenziosamente.
- **Prova dal grafo**: traccia tutti i percorsi di uscita della funzione rispetto al tipo/contratto atteso dai chiamanti diretti.

#### `local-concurrency-auditor`
- **Cosa cerca**: interleaving e pubblicazione di stato condiviso locale (lock, rientranza, cancellazione, init concorrente).
- **Trappola tipica**: check-then-act fuori dal lock su una cache in memoria, oppure handler `on_change` che muta stato e si auto-invoca ricorsivamente.
- **Prova dal grafo**: incrocia tutti i lettori/scrittori dello stato mutabile condiviso e cerca cicli nel call graph via callback/observer.

#### `logic-integrity-auditor`
- **Cosa cerca**: invarianti di dominio cross-componente, pre/post-condizioni, ordinamento obbligatorio, idempotenza e state machine.
- **Trappola tipica**: un ordine in stato terminale `paid` viene modificato da un endpoint admin che chiama il repository bypassando il service.
- **Prova dal grafo**: confronta tutti i mutatori dello stesso stato di dominio lungo i diversi entry point (API, job, webhook, admin).

#### `api-contract-auditor`
- **Cosa cerca**: drift e rotture di compatibilità tra API dichiarate (OpenAPI, JSON Schema, GraphQL, `.proto`, AsyncAPI), validatori runtime, client e output AI strutturati.
- **Trappola tipica**: il backend rinomina `user_id` in `account_id` o aggiunge un campo obbligatorio senza versionare, rompendo client o consumer di coda.
- **Prova dal grafo**: confronta schema/produttore lato server con validatori, DTO e consumatori lato client/broker.

#### `chicken-egg-detector`
- **Cosa cerca**: cicli di avvio, prerequisiti di bootstrap mancanti, ordine di inizializzazione, readiness prima del traffico, seed e migrazioni.
- **Trappola tipica**: la readiness probe risponde `200 OK` prima che il pool DB o la configurazione siano inizializzati.
- **Prova dal grafo**: confronta la sequenza di startup/registrazione route con l'inizializzazione delle dipendenze lette dagli handler.

#### `temporal-resilience-auditor`
- **Cosa cerca**: guasti nel tempo: job bloccati, retry amplification, guardie mai ripulite, morte silenziosa di worker, rischi di clock.
- **Trappola tipica**: flag `in_progress = true` impostato prima di una chiamata di rete senza `finally` né timeout; al primo errore il job resta fermo per sempre.
- **Prova dal grafo**: segue ogni ciclo di polling/scheduler/worker attraverso i percorsi di eccezione, timeout e riavvio.

#### `irreversible-action-auditor`
- **Cosa cerca**: cancellazioni, sovrascritture, `DROP`, `force-push`, `truncate` o purge che procedono su prove mancanti, stantie o ambigue.
- **Trappola tipica**: `rm -rf "$CACHE_DIR/"*` quando `CACHE_DIR` può essere vuota o non validata, oppure sovrascrittura distruttiva senza controllo di esistenza/versione.
- **Prova dal grafo**: traccia la provenienza dei parametri dell'operazione distruttiva fino al punto di origine (env, input, config) verificando le guardie intermedie.

#### `boundary-auditor`
- **Cosa cerca**: codice che viola confini architetturali dichiarati (ADR, regole di layer, manifest di modulo). Se non sono dichiarati, riporta il gap.
- **Trappola tipica**: `core/` importa un modulo di `viewer/` o del trasporto HTTP violando l'isolamento dichiarato nell'ADR.
- **Prova dal grafo**: confronta gli archi di import del grafo dei moduli con le regole di dipendenza dichiarate nei documenti architetturali.

#### `prior-art-auditor`
- **Cosa cerca**: nuovo codice che re-implementa ciò che esiste già, conoscenza duplicata, proprietari concorrenti dello stesso concetto, check/soglie ripetuti.
- **Trappola tipica**: una PR aggiunge una seconda tabella di estensioni o una seconda funzione `parseDate` invece di riusare il modulo condiviso.
- **Prova dal grafo**: cerca simboli e costanti con responsabilità equivalente sull'intera mappa del repository, ancorandosi ai simboli nuovi nel diff.

#### `premise-auditor`
- **Cosa cerca**: deriva claim indipendenti (Mode 1), sfida le premesse dei finding (Mode 2 / Lens 0) e verifica piani, spec e documenti (Mode 3).
- **Trappola tipica**: un revisore segnala un possibile `NullPointerException` su un parametro che in realtà ogni chiamante garantisce non-null.
- **Prova dal grafo**: verifica ogni premessa portante del finding (o del documento) risalendo tutti i chiamanti e le definizioni reali nel codice.

---

### Area B — Sicurezza (10 ruoli)

#### `authorization-auditor`
- **Cosa cerca**: bypass di autorizzazione su oggetti (IDOR), tenant, operazioni e privilegi (RLS, IAM, rotte admin/export/batch).
- **Trappola tipica**: `GET /api/invoices/:id` controlla l'autenticazione ma non `invoice.tenant_id == user.tenant_id`.
- **Prova dal grafo**: confronta gli entry point HTTP/RPC che ricevono un ID con le query/policy di accesso a valle.

#### `session-delegation-auditor`
- **Cosa cerca**: difetti di identità, ciclo di vita sessione, token, password, refresh/logout/revoca, URL firmati e identità di servizio.
- **Trappola tipica**: il logout elimina il cookie nel browser ma lascia attivo il refresh token sul server.
- **Prova dal grafo**: incrocia emissione, verifica, refresh e revoca dei token tra middleware auth, store sessioni e endpoint di logout.

#### `secret-exposure-auditor`
- **Cosa cerca**: esposizione di segreti utilizzabili o stato interno, errori crittografici, confronti timing-unsafe, segreti in log/bundle/errori.
- **Trappola tipica**: un error handler logga o restituisce `err.config.headers` esponendo `Authorization: Bearer ...`.
- **Prova dal grafo**: traccia il flusso delle variabili contenenti credenziali/chiavi verso sink di log, risposte HTTP, bundle client e file serializzati.

#### `input-validation-auditor`
- **Cosa cerca**: input non fidati interpretati come sintassi eseguibile (SQLi, command/template injection, `eval`, deserializzazione) o dimensioni avversariali.
- **Trappola tipica**: `subprocess.run(f"convert {filename} out.png", shell=True)` con `filename` proveniente dalla richiesta.
- **Prova dal grafo**: traccia il taint dagli ingressi esterni fino a sink SQL, shell, template, parser e deserializzatori.

#### `untrusted-resource-auditor`
- **Cosa cerca**: bypass di confinamento su file, archivi (Zip Slip), upload/download, URL, redirect e SSRF.
- **Trappola tipica**: endpoint di preview che fa `fetch(userUrl)` seguendo redirect senza bloccare IP privati (`169.254.169.254`, `127.0.0.1`).
- **Prova dal grafo**: segue percorsi/URL controllati dal chiamante fino a operazioni filesystem, estrazione archivi e client HTTP in uscita.

#### `browser-security-auditor`
- **Cosa cerca**: violazioni del trust boundary nel browser (XSS/DOM sink, cookie `HttpOnly`/`SameSite`, CSRF, CORS, CSP, framing, SRI).
- **Trappola tipica**: `dangerouslySetInnerHTML` su input utente non sanitizzato, o `CORS *` combinato con `credentials: true`.
- **Prova dal grafo**: incrocia i dati che arrivano dal server/URL con i sink DOM nel frontend e gli header di sicurezza impostati dal server/edge.

#### `callback-authenticity-auditor`
- **Cosa cerca**: webhook e callback firmati accettati senza verifica autentica, senza finestra anti-replay o con chiave errata.
- **Trappola tipica**: verifica HMAC sul JSON ri-serializzato anziché sul raw body, o assenza di controllo sul timestamp della firma.
- **Prova dal grafo**: segue la rotta webhook dal middleware di parsing del body fino alla verifica firma e all'handler di business.

#### `ai-boundary-auditor`
- **Cosa cerca**: contesto AI non fidato (documenti recuperati, memoria, output tool) o output LLM che acquisisce autorità non autorizzata.
- **Trappola tipica**: un agente ingerisce contenuto esterno (email, pagina web) nello stesso prompt che può invocare tool distruttivi o di invio esterno senza conferma.
- **Prova dal grafo**: traccia le sorgenti di contesto che entrano nel prompt fino ai tool eseguibili collegati al modello.

#### `audit-trail-auditor`
- **Cosa cerca**: attribuzione mancante o manomissibilità nei record di audit richiesti (azioni privilegiate, tentativi falliti, log injection).
- **Trappola tipica**: cambio di permessi admin senza registrare attore e stato precedente, o input utente non escapato nel record di audit.
- **Prova dal grafo**: confronta le operazioni privilegiate/sensibili con le chiamate al sink di audit e i relativi controlli di accesso.

#### `capacity-quota-auditor`
- **Cosa cerca**: ammissione, limiti aggregati e backpressure sotto carico legittimo o avversariale (rate limit, code, fan-out, concorrenza).
- **Trappola tipica**: login senza rate limit, oppure job che lancia 100.000 richieste in parallelo senza semaforo né coda limitata.
- **Prova dal grafo**: confronta gli ingressi pubblici e i loop di fan-out con i middleware di rate limiting, pool e quote configurati.

---

### Area C — Integrità dei dati e persistenza (6 ruoli)

#### `transaction-integrity-auditor`
- **Cosa cerca**: invarianti persistenti rotti da confini di transazione, scritture concorrenti, isolamento insufficiente, upsert o replay.
- **Trappola tipica**: lettura saldo + `if balance >= amount` + `UPDATE` in due query separate senza lock né clausola condizionale atomica.
- **Prova dal grafo**: esamina l'intera catena di letture e scritture sullo stesso record dentro e fuori i confini della transazione.

#### `schema-coherence-auditor`
- **Cosa cerca**: disaccordo tra rappresentazioni dello stesso oggetto persistente (DDL/migrazioni, ORM, SQL manuale, trigger, viste, stored procedure).
- **Trappola tipica**: migrazione che rende `NOT NULL` una colonna mentre un modello ORM o una query manuale continua a scriverci `NULL`.
- **Prova dal grafo**: confronta le migrazioni/DDL con tutti i modelli ORM e le query SQL che referenziano la stessa tabella/colonna.

#### `cache-consistency-auditor`
- **Cosa cerca**: letture derivate stantie o con scope errato (cache, repliche, indici, proiezioni, invalidazione, read-your-writes).
- **Trappola tipica**: chiave cache `user:{id}:perms` che dimentica `tenant_id`, o mutazione DB che non invalida la relativa chiave cache.
- **Prova dal grafo**: incrocia tutti i punti di scrittura/cancellazione della fonte primaria con le chiavi di lettura e invalidazione della cache.

#### `data-representation-auditor`
- **Cosa cerca**: perdita di significato nei valori persistiti, paginazione e conversioni (denaro in float, timezone/date, NULL vs default, enum/JSON, cursori).
- **Trappola tipica**: prezzi salvati come `FLOAT` anziché `DECIMAL`/centesimi interi, o timestamp locali salvati senza timezone.
- **Prova dal grafo**: segue i valori dal modello applicativo attraverso conversioni/serializzazioni fino ai tipi colonna e ritorno.

#### `data-retention-auditor`
- **Cosa cerca**: percorsi di cancellazione e scadenza che violano policy di retention approvate (GDPR, copie derivate, restore backup, legal hold).
- **Trappola tipica**: la cancellazione utente rimuove la riga da `users` ma lascia copie in export, bucket S3 o indici di ricerca.
- **Prova dal grafo**: confronta tutti gli store/copie dove il dato personale viene scritto con i percorsi di cancellazione ed expiry.

#### `storage-durability-auditor`
- **Cosa cerca**: scritture su file che perdono o corrompono dati su crash, disco pieno, errore o accesso concorrente (temp+rename, `fsync`, lock file).
- **Trappola tipica**: sovrascrittura diretta di `state.json` con `open(..., "w")` senza file temporaneo + `rename` atomico.
- **Prova dal grafo**: ispeziona tutti gli scrittori e lettori dello stesso file su disco e i relativi percorsi di errore/concorrenza.

---

### Area D — Sistemi distribuiti (3 ruoli)

#### `message-delivery-auditor`
- **Cosa cerca**: lavoro su broker perso, duplicato o riordinato contro il contratto di consegna (AMQP, confirm, ack, prefetch, DLQ, offset).
- **Trappola tipica**: `ack` inviato prima di completare l'elaborazione del messaggio, causando perdita silenziosa su crash.
- **Prova dal grafo**: traccia il ciclo di vita del messaggio dal consumer/prefetch attraverso elaborazione, gestione errori e `ack`/`nack`.

#### `remote-effect-auditor`
- **Cosa cerca**: effetti remoti ripetuti, confermati falsamente o lasciati non riconciliati dopo guasti (pagamenti, outbox/inbox, saga, idempotenza, fencing).
- **Trappola tipica**: `db.commit()` seguito da chiamata HTTP di addebito senza outbox né chiave di idempotenza dentro un handler con retry.
- **Prova dal grafo**: incrocia commit locali, chiamate esterne mutanti e policy di retry/redelivery dello stesso flusso.

#### `service-resilience-auditor`
- **Cosa cerca**: guasti cross-service che violano deadline, budget di retry o isolamento del recovery (timeout HTTP/gRPC, circuit breaker, bulkhead).
- **Trappola tipica**: client HTTP senza timeout con 5 retry immediati senza backoff né jitter, causando tempeste di retry.
- **Prova dal grafo**: segue le chiamate cross-service dalla configurazione del client fino ai chiamanti e ai loro budget di timeout.

---

### Area E — Prestazioni, risorse e costi (6 ruoli)

#### `sql-efficiency-auditor`
- **Cosa cerca**: amplificazione di lavoro sul DB e percorsi di accesso inefficaci (query N+1, join senza indice, `OFFSET` profondo, lazy loading).
- **Trappola tipica**: loop su 500 ordini che esegue una query separata per ogni ordine invece di un `JOIN` o `IN (...)`.
- **Prova dal grafo**: incrocia loop applicativi e chiamate repository con le query SQL/ORM e gli indici definiti nello schema.

#### `algorithmic-cost-auditor`
- **Cosa cerca**: complessità dipendente dall'input, picchi di allocazione e lavoro bloccante su percorsi caldi (loop annidati, copie, ricorsione, ReDoS, I/O sincrono in `async`).
- **Trappola tipica**: ricerca lineare $O(n)$ dentro un loop su $n$ elementi ($O(n^2)$), o chiamata HTTP sincrona dentro `async def`.
- **Prova dal grafo**: segue le funzioni chiamate dentro loop o coroutine `async` fino alle operazioni bloccanti o superlineari.

#### `asset-delivery-auditor`
- **Cosa cerca**: consegna ridondante di asset e bundle sui percorsi critici (import eager, glob loading, immagini non ottimizzate, font bloccanti).
- **Trappola tipica**: import sincrono di una libreria grafici da 1,2 MB nel bundle della pagina di login.
- **Prova dal grafo**: traccia gli import statici dagli entry point delle pagine critiche verso librerie pesanti o asset non lazy.

#### `runtime-cost-auditor`
- **Cosa cerca**: attribuzione di lavoro a pagamento e rispetto dei limiti di spesa dichiarati (chiamate LLM/token, compute, egress, log ad alto volume).
- **Trappola tipica**: loop di retry su un'API LLM senza cap sui token né budget massimo per richiesta/sessione.
- **Prova dal grafo**: collega i punti di chiamata a servizi fatturati (LLM, cloud API, storage) ai relativi limiti, retry e guardie di budget.

#### `resource-lifecycle-auditor`
- **Cosa cerca**: acquisizione, ownership e rilascio di risorse su successo, errore e cancellazione (file, socket, connessioni DB, subprocess, listener, timer, lock).
- **Trappola tipica**: `subprocess.Popen` o connessione aperta senza `try/finally` / context manager, lasciando zombie o leak su eccezione.
- **Prova dal grafo**: accoppia ogni sito di acquisizione con tutti i percorsi di uscita, errore e cancellazione del chiamante.

#### `responsiveness-auditor`
- **Cosa cerca**: lavoro user-facing che blocca il main/UI thread oltre il budget senza progresso né cancellazione (parsing sincrono, I/O, crypto).
- **Trappola tipica**: `JSON.parse` + ordinamento sincrono di 20 MB in un click handler sul main thread, congelando la UI.
- **Prova dal grafo**: traccia gli event handler UI e i percorsi di render/startup fino a operazioni CPU-bound o I/O sincrone.

---

### Area F — Operabilità e rilascio (7 ruoli)

#### `observability-auditor`
- **Cosa cerca**: segnali operativi utilizzabili che raggiungono il destinatario (errori inghiottiti, correlazione, metriche, exporter, alert).
- **Trappola tipica**: `except Exception: pass` che nasconde un fallimento di sincronizzazione senza log né metrica.
- **Prova dal grafo**: ispeziona i blocchi `catch`/`except` e i percorsi di errore verificando se emettono segnali verso il logger/telemetry configurato.

#### `service-health-auditor`
- **Cosa cerca**: probe di readiness e liveness a regime rispetto alla reale capacità di servire traffico, watchdog e modalità degradata.
- **Trappola tipica**: liveness probe che chiama un servizio esterno di terze parti, causando riavvii a cascata quando il fornitore è giù.
- **Prova dal grafo**: segue gli handler `/healthz` e `/readyz` fino a tutte le dipendenze interne ed esterne che interrogano.

#### `release-compatibility-auditor`
- **Cosa cerca**: coesistenza, continuità e rollback tra versioni supportate (rolling deploy, migrazioni expand-contract, formati versionati).
- **Trappola tipica**: migrazione che rimuove subito una colonna ancora letta dai pod della versione precedente durante il deploy.
- **Prova dal grafo**: confronta le modifiche a schema, formati persistiti e API con la compatibilità verso la versione N-1.

#### `environment-binding-auditor`
- **Cosa cerca**: risoluzione delle configurazioni d'ambiente e instradamento verso le risorse intese (variabili di deploy, layer di config, endpoint).
- **Trappola tipica**: URL di staging hardcoded come default quando `API_URL` manca in produzione.
- **Prova dal grafo**: incrocia i file di configurazione/deploy con tutti i siti che leggono `os.environ`/`process.env` e i loro fallback.

#### `feature-flag-auditor`
- **Cosa cerca**: transizioni di stato dei flag, fallback, coesistenza di flag interagenti e disattivazione sicura.
- **Trappola tipica**: abilitare `flag_A` senza `flag_B` manda in crash il percorso di fallback che presuppone dati scritti solo da `flag_B`.
- **Prova dal grafo**: mappa tutti i rami condizionati da ciascun flag e verifica le combinazioni di attivazione/disattivazione.

#### `recovery-auditor`
- **Cosa cerca**: asset recuperabili e ripristino in servizio utilizzabile dopo un disastro dichiarato (backup, runbook di restore, failover, RPO/RTO).
- **Trappola tipica**: backup del DB che esclude chiavi di cifratura o file locali necessari per rendere funzionante il restore.
- **Prova dal grafo**: confronta tutti gli store persistenti usati dall'app con ciò che gli script/configurazioni di backup e restore includono.

#### `build-pruning-auditor`
- **Cosa cerca**: elementi raggiunti solo per nome (reflection, ID risorse, comandi dinamici) che l'ottimizzatore della build di release elimina.
- **Trappola tipica**: in debug tutto funziona, in release il bundler/linker rimuove un handler registrato solo come stringa.
- **Prova dal grafo**: confronta i lookup dinamici per nome con le regole di keep/tree-shaking/bundling nella configurazione di build.

---

### Area G — Frontend, UI e accessibilità (4 ruoli)

#### `ui-race-auditor`
- **Cosa cerca**: guasti temporali osservabili tra dati asincroni, rendering, layout e interazione utente (risposte fuori ordine, closure stantie, scroll/focus/resize).
- **Trappola tipica**: ricerca asincrona senza `AbortController` dove la risposta di `"ab"` arriva dopo `"abc"` e sovrascrive i risultati.
- **Prova dal grafo**: segue le chiamate async nei componenti/hook fino agli aggiornamenti di stato e verifica cancellazione o guardia di sequenza.

#### `accessible-navigation-auditor`
- **Cosa cerca**: accesso semantico e da tastiera ai percorsi interattivi richiesti (controlli, form, menu, dialog, focus trap, tab order).
- **Trappola tipica**: modale che non sposta il focus all'apertura e non si chiude con `Esc`, intrappolando gli utenti da tastiera.
- **Prova dal grafo**: ispeziona componenti interattivi, dialoghi e gestori tastiera lungo i percorsi utente principali.

#### `accessible-perception-auditor`
- **Cosa cerca**: informazione percepibile, feedback e layout efficace (etichette associate, errori annunciati, stati async, contrasto, temi, viewport stretti).
- **Trappola tipica**: errore di validazione indicato solo col bordo rosso senza testo né `aria-describedby`.
- **Prova dal grafo**: verifica il collegamento tra stato di errore/caricamento nel modello, attributi ARIA e rendering visivo/stili.

#### `react-auditor`
- **Cosa cerca**: difetti di render, effect e stato specifici di React (dipendenze `useEffect`, stato derivato duplicato, chiavi instabili, leak di subscription, context/Suspense/RSC).
- **Trappola tipica**: custom hook con `useState` locale usato da due componenti per uno stato globale dell'app: un'azione in uno non aggiorna l'altro.
- **Prova dal grafo**: traccia tutti i siti di chiamata dei custom hook, i provider di context e le dipendenze degli effect nell'albero React.

---

### Area H — Linguaggi, stack e piattaforme (7 ruoli)

#### `typescript-auditor`
- **Cosa cerca**: punti in cui i tipi TypeScript smettono di descrivere il valore a runtime (`as`, `!`, `any`, generic non vincolati, JSON non validato).
- **Trappola tipica**: `(await res.json()) as User` senza validazione runtime: un payload di errore passa il compilatore e crasha a valle.
- **Prova dal grafo**: segue i cast/asserzioni ai confini esterni (rete, storage, IPC) fino ai consumatori che assumono il tipo dichiarato.

#### `python-auditor`
- **Cosa cerca**: semantica specifica di Python (default mutabili, late binding nelle closure, short-circuit, `return` in `finally`, context manager, logging).
- **Trappola tipica**: `def add(item, items=[]):` che condivide la stessa lista fra chiamate, o `[lambda: i for i in range(5)]` che cattura solo `4`.
- **Prova dal grafo**: ispeziona firme, closure, blocchi `try/finally` e context manager nei moduli Python toccati.

#### `stripe-auditor`
- **Cosa cerca**: integrazioni Stripe che perdono, duplicano o si fidano ciecamente di un evento di pagamento (webhook `constructEvent`, copertura eventi, checkout, subscription, Connect).
- **Trappola tipica**: attivare l'abbonamento su `success_url` anziché sul webhook `checkout.session.completed`, o ignorare `invoice.payment_failed`.
- **Prova dal grafo**: incrocia la creazione di checkout/subscription con tutti gli handler webhook Stripe e le mutazioni dello stato billing nel DB.

#### `tauri-ipc-auditor`
- **Cosa cerca**: percorsi IPC Tauri su cui una webview compromessa raggiunge l'host (`#[tauri::command]`, `invoke`/`emit`/`listen`, custom URI scheme, deep-link).
- **Trappola tipica**: `#[tauri::command] fn read_note(path: String)` che legge qualsiasi file sul disco senza confinarlo nella directory attesa.
- **Prova dal grafo**: collega ogni `invoke()` del frontend al corrispondente `#[tauri::command]` Rust verificando la validazione degli argomenti.

#### `tauri-hardening-auditor`
- **Cosa cerca**: configurazione Tauri (`tauri.conf.json`, `capabilities/*.json`, CSP, scope asset/shell, updater, sidecar) che allarga i permessi oltre il necessario.
- **Trappola tipica**: capability `fs:allow-read-file` su `**` o `shell:allow-open` senza filtro di schema.
- **Prova dal grafo**: confronta le capability e gli scope concessi nei manifest Tauri con ciò che i comandi e la webview usano davvero.

#### `tauri-sync-auditor`
- **Cosa cerca**: stato Tauri che diverge tra backend Rust, finestre multiple e copie frontend (`Mutex` attraverso `.await`, scrittori concorrenti, eventi persi/riordinati).
- **Trappola tipica**: `std::sync::Mutex` tenuto bloccato attraverso un `.await` (deadlock), o due finestre che sovrascrivono lo stesso file di config.
- **Prova dal grafo**: mappa `tauri::State`, eventi `emit`/`listen` e store condivisi tra comandi Rust e finestre frontend.

#### `tauri-reliability-auditor`
- **Cosa cerca**: percorsi Tauri che congelano, crashano, perdono risorse o falliscono su una piattaforma (comandi bloccanti sul main thread, `.unwrap()` su input, leak di listener/finestre).
- **Trappola tipica**: comando sincrono che fa I/O file/rete sul main thread congelando la finestra, o `.unwrap()` su JSON dalla webview.
- **Prova dal grafo**: ispeziona i corpi di `#[tauri::command]`, l'hook `setup` e la gestione del ciclo di vita di finestre e listener.

---

### Area I — Test, pulizia, dipendenze e igiene (6 ruoli)

#### `testing-auditor`
- **Cosa cerca**: comportamenti lasciati senza protezione e test che non possono fallire, indeboliti, mockati male o flaky.
- **Trappola tipica**: test che mocka la funzione stessa sotto test o asserisce solo `toBeDefined()`, passando anche a logica rotta.
- **Prova dal grafo**: confronta i simboli/comportamenti cambiati nel codice di produzione con i test, le fixture e i target mockati.

#### `application-reachability-auditor`
- **Cosa cerca**: simboli applicativi, export, barrel, asset o entry point ritirati senza più alcun consumatore legittimo.
- **Trappola tipica**: 4 file di vecchi handler rimasti esportati dopo un refactoring ma mai più importati da alcun percorso vivo.
- **Prova dal grafo**: verifica l'assenza di archi entranti nel grafo di chiamate/import a partire dagli entry point reali dell'app.

#### `artifact-lifecycle-auditor`
- **Cosa cerca**: artefatti documentali e di migrazione non allineati all'intento attuale (riferimenti obsoleti, residui di rebrand, vecchi piani, backup).
- **Trappola tipica**: README e script di avvio che citano ancora comandi o flag rimossi mesi prima.
- **Prova dal grafo**: confronta nomi di comandi, percorsi e simboli citati nei documenti con l'inventario reale del codice.

#### `dependency-usage-auditor`
- **Cosa cerca**: consumatori reali delle dipendenze e proprietà delle dichiarazioni per pacchetto (pacchetti inutilizzati, runtime dichiarati solo in dev).
- **Trappola tipica**: `lodash` importato nel codice di produzione ma dichiarato solo in `devDependencies`.
- **Prova dal grafo**: incrocia gli import effettivi dei moduli (produzione vs test/build) con i manifest di ciascun pacchetto.

#### `dependency-provenance-auditor`
- **Cosa cerca**: pacchetti installati o dichiarati la cui origine o versione porta un rischio noto e raggiungibile (bump, pin/range modificati, cambio registry/URL).
- **Trappola tipica**: lockfile che punta a un URL git non pinnato a uno SHA, o downgrade a una versione con vulnerabilità nota.
- **Prova dal grafo**: confronta le voci aggiunte/cambiate in manifest e lockfile con i moduli che le importano.

#### `workspace-hygiene-auditor`
- **Cosa cerca**: file tracciati rigenerati dalla build, regole `.gitignore` che nascondono sorgenti necessari, residui di merge e stato Git sporco.
- **Trappola tipica**: `dist/` o artefatti temporanei committati, o `.gitignore` troppo largo (`*.json`) che nasconde una config necessaria.
- **Prova dal grafo**: incrocia l'elenco dei file tracciati, le regole di ignore effettive e le directory di output dichiarate nella build.

---

## 3. Casi reali verificati

Questa sezione registra solo difetti **davvero accaduti** (con progetto, commit e rimedio verificabili). Ogni nuovo caso reale si aggiunge qui, mai inventato.

### Caso reale #1 — Muro: incoerenza UI–stato–intento («Needs a build»)
- **Progetto / commit**: Muro, corretto nel commit `b1b73a5` (novembre 2026).
- **Tassonomia / ruoli**: `plugins/senior-review/skills/defect-taxonomy/references/ui-state-intent.md` (`U1.1`, `U1.2`, `U2.1`, `U2.2`, `U3.1`).
- **Sintomo**: la tabella Sync mostrava il badge arancione `Needs a build` (e `"N plugins need a build"`) sia quando un plugin non esisteva per quell'harness (terze parti, `.mp` senza variante, mai controllato) sia quando le istruzioni personalizzate erano cambiate dopo l'adattamento AI.
- **Causa nel codice**: `cellState` in `apps/desktop/src/model.ts` collassava due significati diversi in un solo valore `needs-build`; `SyncTable.tsx` lo mostrava come prescrizione per un comando "Build" inesistente (il comando reale è `Adapt with AI` in `More`); il backend Rust (`missing()` in `crates/muro-registry/src/sources.rs`) conosceva già la causa precisa ma la UI la perdeva; `pluginState` diceva già `Adapt again` contraddicendo la tabella.
- **Rimedio**: separato in `unavailable` (badge neutro `Not available`) e `adapt-again` (badge arancione `Adapt again`).
- **Lezione**: serve il grafo completo della GUI (*backend → stato → UI → comandi*) letto da un revisore LLM con criteri `ui-state-intent`.

### Caso reale #2 — polarsource/polar (F1): chiamata Stripe sincrona dentro `async def`
- **Progetto / commit**: `polarsource/polar`, introdotto in `071de575` (2024-10-02), corretto in `54da7207` (2024-10-09); fonte: `benchmarks/stack-reviewers/README.md`.
- **Ruoli**: `algorithmic-cost-auditor`, `responsiveness-auditor`, `stripe-auditor` (pilota `fastapi-auditor`).
- **Sintomo**: blocco dell'event loop FastAPI durante il checkout.
- **Causa nel codice**: `async def calculate_tax` (`server/polar/checkout/tax.py:295`) chiamava `stripe_service.create_tax_calculation`, implementato come metodo sincrono sopra `stripe_lib.tax.Calculation.create` (`server/polar/integrations/stripe/service.py:696`).
- **Rimedio**: conversione delle chiamate Stripe del checkout a versioni asincrone.

### Caso reale #3 — polarsource/polar (S1): relazione `lazy="raise"` letta su `AsyncSession`
- **Progetto / commit**: `polarsource/polar`, introdotto in `fda49793` (2025-07-29), corretto in `949877de` (2025-07-30); fonte: `benchmarks/stack-reviewers/README.md`.
- **Ruoli**: `sql-efficiency-auditor`, `data-integrity-auditor` (pilota `sqlalchemy-auditor`).
- **Sintomo**: il task `account.under_review` sollevava eccezione a runtime e non creava il thread di review.
- **Causa nel codice**: `get_all_by_account` (`server/polar/organization/repository.py:64`) caricava le organizzazioni senza eager-load della relazione `account` (`lazy="raise"` in `server/polar/models/organization.py:132`), poi letta da `create_account_review_thread` (`server/polar/integrations/plain/service.py:126`).
- **Rimedio**: caricamento esplicito della relazione nella query prima di passare gli oggetti al servizio.
