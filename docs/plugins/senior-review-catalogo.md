# Senior Review: catalogo completo dei reviewer ed esempi

Guida esaustiva a tutte le **10 composizioni** e ai **59 ruoli atomici** definiti in `daodan/review/catalog.toml` e `daodan/review/roles/*.md`, con esempi concreti dei difetti che identificano e prevengono.

Questo documento descrive e integra i mandati operativi; la fonte normativa eseguita dall'LLM resta `daodan/review/catalog.toml`, `daodan/review/roles/<nome>.md` e `plugins/senior-review/skills/defect-taxonomy/references/*.md`.

---

## Come funziona il catalogo

- **Ruoli atomici (59)**: ciascuno è un file `daodan/review/roles/<nome>.md` con un mandato mirato (`TRIGGER WHEN` / `DO NOT TRIGGER WHEN`).
- **Composizioni (10)**: gruppi definiti in `[reviewers.compositions]` di `daodan/review/catalog.toml`. Non hanno un file proprio: `daodan composition` li espande nei loro membri atomici.
- **Esecuzione**: ogni ruolo gira su `senior-review:isolated-worker` (5 strumenti: Read, Write, Glob, Grep, Bash), partendo dal grafo e dagli indici già costruiti da **Codebase Map**.
- **Tassonomia trasversale**: i riferimenti in `plugins/senior-review/skills/defect-taxonomy/references/` (tra cui `logic-integrity.md` e `ui-state-intent.md`) forniscono pattern e criteri semantici caricati per dominio.

### Le 10 composizioni

| Composizione | Membri |
|---|---|
| `code-auditor` | `local-correctness`, `local-concurrency`, `input-validation`, `resource-lifecycle`, `algorithmic-cost`, `security-auditor`, `data-integrity-auditor`, `chicken-egg-detector`, `temporal-resilience`, `distributed-flow-auditor`, `api-contract`, `logic-integrity` |
| `security-auditor` | `authorization`, `session-delegation`, `secret-exposure`, `input-validation`, `untrusted-resource`, `browser-security`, `callback-authenticity`, `ai-boundary`, `audit-trail`, `capacity-quota` |
| `data-integrity-auditor` | `transaction-integrity`, `schema-coherence`, `cache-consistency`, `data-representation`, `data-retention` |
| `distributed-flow-auditor` | `message-delivery`, `remote-effect`, `service-resilience`, `session-delegation`, `environment-binding` |
| `performance-auditor` | `sql-efficiency`, `algorithmic-cost`, `asset-delivery`, `capacity-quota`, `runtime-cost`, `resource-lifecycle`, `responsiveness` |
| `operability-auditor` | `observability`, `service-health`, `release-compatibility`, `environment-binding`, `feature-flag`, `recovery`, `build-pruning` |
| `cleanup-auditor` | `application-reachability`, `dependency-usage`, `artifact-lifecycle`, `asset-delivery`, `secret-exposure`, `workspace-hygiene` |
| `tauri-auditor` | `tauri-ipc`, `tauri-hardening`, `tauri-sync`, `tauri-reliability`, `build-pruning` |
| `accessibility-auditor` | `accessible-navigation`, `accessible-perception` |
| `dependency-auditor` | `dependency-usage`, `dependency-provenance` |

---

## 1. Correttezza, logica e architettura (10 ruoli)

### `local-correctness-auditor`
- **Cosa cerca**: valori locali, flussi di controllo, rami, aritmetica, conversioni, gestione errori e stato d'istanza.
- **Esempio**: una funzione di paginazione calcola `offset = (page - 1) * limit` senza controllare `page <= 0`, producendo un offset negativo; oppure un `if/else` dimentica un ramo di ritorno e restituisce `None`/`undefined` silenziosamente.

### `local-concurrency-auditor`
- **Cosa cerca**: interleaving e pubblicazione di stato condiviso locale (memoria condivisa, lock, rientranza, cancellazione, inizializzazione concorrente).
- **Esempio**: una cache in memoria verifica `if key not in cache` fuori dal lock e poi scrive dentro, oppure un handler `on_change` muta uno stato che rilancia ricorsivamente `on_change` corrompendo i campi intermedi.

### `logic-integrity-auditor`
- **Cosa cerca**: invarianti di dominio cross-componente, pre/post-condizioni, ordinamento obbligatorio, idempotenza e transizioni di state machine.
- **Esempio**: un ordine in stato terminale `paid` viene comunque modificato da un endpoint admin che chiama `OrderRepository.update` direttamente bypassando `OrderService`; oppure un ordine `archived` può tornare `draft` perché `status` è un campo libero senza guardie.

### `api-contract-auditor`
- **Cosa cerca**: drift e rotture di compatibilità tra API dichiarate (OpenAPI, JSON Schema, GraphQL, `.proto`, AsyncAPI), validatori runtime, client, payload di coda e output strutturati AI.
- **Esempio**: il backend rinomina il campo `user_id` in `account_id` o aggiunge un campo obbligatorio senza versione, mentre il client TypeScript o il consumer AMQP continua a leggere il vecchio schema fallendo a runtime.

### `chicken-egg-detector`
- **Cosa cerca**: cicli di avvio, prerequisiti di bootstrap mancanti, ordine di inizializzazione, readiness prima del traffico, seed e migrazioni al boot.
- **Esempio**: un servizio registra il proprio endpoint di readiness come `200 OK` prima di aver caricato la configurazione o completato la connessione al DB, ricevendo richieste che falliscono nei primi 5 secondi di avvio.

### `temporal-resilience-auditor`
- **Cosa cerca**: guasti nel tempo: job bloccati, retry storm, guardie mai ripulite, morte silenziosa di worker/scheduler, problemi di clock.
- **Esempio**: un worker imposta un flag `in_progress = true` prima di una chiamata di rete senza `finally` né timeout; al primo timeout di rete il flag resta `true` per sempre e il job non riparte più.

### `irreversible-action-auditor`
- **Cosa cerca**: cancellazioni, sovrascritture, `DROP`, `force-push`, `truncate` o purge che procedono su prove mancanti, stantie o ambigue.
- **Esempio**: uno script di pulizia cancella una directory calcolata da una variabile d'ambiente opzionale (`rm -rf "$CACHE_DIR/"*`): se la variabile è vuota o non risolta, cancella il percorso sbagliato senza alcuna verifica preliminare.

### `boundary-auditor`
- **Cosa cerca**: codice che attraversa confini architetturali dichiarati (ADR, regole di layer, manifest di modulo). Se nessun confine è dichiarato, segnala il prerequisito mancante anziché giudicare a gusto.
- **Esempio**: l'ADR dichiara che `core/` non dipende da `viewer/` o da HTTP/MCP; una PR importa un helper del server HTTP dentro `core/model.py`.

### `prior-art-auditor`
- **Cosa cerca**: codice nuovo che re-implementa ciò che esiste già nel repository, conoscenza duplicata, due proprietari concorrenti per lo stesso concetto, soglie o check ripetuti.
- **Esempio**: una nuova feature introduce una seconda funzione `parseIsoDate()` e una seconda tabella di estensioni supportate invece di riusare quelle già presenti nel modulo condiviso, creando drift futuro.

### `premise-auditor`
- **Cosa cerca**: deriva claim indipendenti dal codice (Mode 1), sfida le premesse portanti dei finding degli altri revisori (Mode 2 / Lens 0) e verifica le affermazioni di piani, spec e documenti (Mode 3).
- **Esempio**: un revisore segnala un bug sostenendo che `foo()` può ricevere `null`; `premise-auditor` (Lens 0) traccia tutti i chiamanti nel grafo e dimostra che il chiamante garantisce non-null, eliminando un falso positivo prima del report finale.

---

## 2. Sicurezza (10 ruoli — `security-auditor`)

### `authorization-auditor`
- **Cosa cerca**: bypass di autorizzazione su oggetti (IDOR), tenant, operazioni e privilegi (RLS, IAM, rotte admin/export/batch).
- **Esempio**: `GET /api/invoices/:id` controlla che l'utente sia autenticato, ma non verifica `invoice.tenant_id == current_user.tenant_id`, permettendo di leggere fatture di altri clienti cambiando l'ID.

### `session-delegation-auditor`
- **Cosa cerca**: difetti di identità, ciclo di vita sessione, token, password, refresh/logout/revoca, URL firmati e identità di servizio.
- **Esempio**: il logout cancella il cookie lato browser ma non revoca il refresh token sul server; un token rubato continua a generare nuovi access token validi.

### `secret-exposure-auditor`
- **Cosa cerca**: esposizione di segreti utilizzabili o stato interno, errori di confidenzialità crittografica, confronti timing-unsafe, segreti in log/bundle/risposte di errore.
- **Esempio**: un middleware di errore serializza `err.config.headers` nei log o nella risposta HTTP 500, esponendo `Authorization: Bearer <API_KEY>`.

### `input-validation-auditor`
- **Cosa cerca**: valori non fidati interpretati come sintassi eseguibile (SQLi, command injection, template injection, `eval`, deserializzazione) o input di dimensione avversariale.
- **Esempio**: un nome file fornito dall'utente viene passato in `subprocess.run(f"convert {filename} out.png", shell=True)`, permettendo esecuzione arbitraria di comandi.

### `untrusted-resource-auditor`
- **Cosa cerca**: bypass di confinamento su file, archivi (Zip Slip), upload/download, URL, redirect e SSRF.
- **Esempio**: un endpoint di preview accetta un `url` dall'utente e fa `fetch(url)` seguendo i redirect senza bloccare IP privati (`169.254.169.254`, `127.0.0.1`), esponendo i metadati cloud.

### `browser-security-auditor`
- **Cosa cerca**: violazioni del trust boundary nel browser: XSS/DOM sink, cookie (`HttpOnly`/`SameSite`), CSRF, CORS, CSP, framing, SRI.
- **Esempio**: un componente renderizza markdown utente con `dangerouslySetInnerHTML` senza sanitizzazione, oppure il server risponde `Access-Control-Allow-Origin: *` insieme a `Access-Control-Allow-Credentials: true`.

### `callback-authenticity-auditor`
- **Cosa cerca**: webhook e callback firmati accettati senza verifica autentica, senza finestra anti-replay o con selezione errata della chiave.
- **Esempio**: un handler webhook confronta la firma HMAC con `==` sul JSON ri-serializzato invece che sul body raw, oppure accetta timestamp vecchi di giorni permettendo replay attack.

### `ai-boundary-auditor`
- **Cosa cerca**: contesto AI non fidato (documenti recuperati, memoria, output di tool) o output del modello che acquisisce autorità non autorizzata (prompt injection → tool execution).
- **Esempio**: un agente legge un'email esterna e passa il testo direttamente in un prompt che ha accesso a un tool `send_email` o `delete_record` senza approvazione né vincoli di destinazione.

### `audit-trail-auditor`
- **Cosa cerca**: attribuzione mancante o manomissibilità nei record di audit richiesti (azioni privilegiate, tentativi falliti, log framing/injection).
- **Esempio**: un cambio di ruolo admin non registra chi l'ha eseguito né il valore precedente, oppure scrive l'input utente non escapato nel log di audit permettendo di falsificare righe di log.

### `capacity-quota-auditor`
- **Cosa cerca**: ammissione, limiti aggregati e backpressure sotto carico legittimo o avversariale (code, rate limit login, fan-out, concorrenza).
- **Esempio**: l'endpoint di login non ha rate limiting né lockout progressivo, oppure un job di notifica fa fan-out illimitato su 100.000 utenti in parallelo saturando il pool DB.

---

## 3. Integrità dei dati e persistenza (6 ruoli)

### `transaction-integrity-auditor`
- **Cosa cerca**: invarianti persistenti rotti da confini di transazione, scritture concorrenti, isolamento insufficiente, upsert o replay.
- **Esempio**: un prelievo legge il saldo in una query, verifica `balance >= amount` in memoria e poi esegue `UPDATE` in una seconda query senza `SELECT ... FOR UPDATE` né `WHERE balance >= amount`, permettendo double-spend concorrente.

### `schema-coherence-auditor`
- **Cosa cerca**: disaccordo tra rappresentazioni dello stesso oggetto persistente: DDL/migrazioni, modelli ORM, SQL scritto a mano, trigger, viste, stored procedure.
- **Esempio**: una migrazione rende `NOT NULL` la colonna `phone`, ma il modello ORM e una query SQL manuale continuano a inserire `NULL` in un percorso secondario.

### `cache-consistency-auditor`
- **Cosa cerca**: letture derivate stantie o con scope errato (cache, repliche, indici, proiezioni, invalidazione, read-your-writes, propagazione cancellazioni).
- **Esempio**: la chiave di cache è `user:{user_id}:permissions` ma il sistema è multi-tenant e i permessi dipendono anche da `tenant_id`, causando inquinamento cross-tenant; oppure un utente cancellato resta valido in cache per 1 ora.

### `data-representation-auditor`
- **Cosa cerca**: perdita di significato nei valori persistiti, paginazione e conversioni (soldi in float, timezone/date, NULL vs default, versioni enum/JSON, cursori).
- **Esempio**: gli importi monetari vengono salvati come `FLOAT` invece che in centesimi interi/`DECIMAL`, introducendo errori di arrotondamento; oppure un timestamp locale viene salvato senza timezone e spostato al cambio d'ora legale.

### `data-retention-auditor`
- **Cosa cerca**: percorsi di cancellazione e scadenza che violano policy di retention approvate (richieste GDPR, copie derivate, restore backup, legal hold).
- **Esempio**: la cancellazione account rimuove la riga da `users` ma lascia copie in tabelle di export, bucket S3 o indici di ricerca, violando l'obbligo di cancellazione.

### `storage-durability-auditor`
- **Cosa cerca**: scritture su file che perdono o corrompono dati in caso di crash, disco pieno, errore di scrittura o accesso concorrente (temp+rename, `fsync`, lock file, NFS).
- **Esempio**: l'app sovrascrive `state.json` aprendolo direttamente in modalità `w`; un crash a metà scrittura lascia il file troncato a 0 byte invece di scrivere su un file temporaneo nella stessa directory e fare `rename` atomico.

---

## 4. Sistemi distribuiti (3 ruoli — in `distributed-flow-auditor`)

### `message-delivery-auditor`
- **Cosa cerca**: lavoro su broker perso, duplicato o riordinato contro il contratto di consegna (publisher/consumer, AMQP, confirm, ack, prefetch, DLQ, offset).
- **Esempio**: il consumer invia `ack` appena riceve il messaggio e prima di elaborarlo: se il processo crasha durante l'elaborazione, il messaggio è perso definitivamente.

### `remote-effect-auditor`
- **Cosa cerca**: effetti remoti ripetuti, confermati falsamente o lasciati non riconciliati dopo guasti (pagamenti, outbox/inbox, saga, idempotenza, lease/fencing).
- **Esempio**: il servizio fa `db.commit()` e poi chiama un'API esterna di addebito senza outbox né chiave di idempotenza: se la chiamata va in timeout dopo aver addebitato, il retry addebita due volte.

### `service-resilience-auditor`
- **Cosa cerca**: guasti cross-service che violano deadline, budget di retry o isolamento del recovery (timeout HTTP/gRPC, circuit breaker, bulkhead).
- **Esempio**: un client HTTP non imposta timeout e fa 5 retry immediati senza backoff né jitter: un rallentamento del servizio a valle blocca tutti i thread e amplifica il carico di 5×.

---

## 5. Prestazioni, risorse e costi (6 ruoli — in `performance-auditor`)

### `sql-efficiency-auditor`
- **Cosa cerca**: amplificazione di lavoro sul DB e percorsi di accesso inefficaci (query N+1, join senza indice, paginazione `OFFSET` profonda, caricamento di intere tabelle).
- **Esempio**: un loop su 500 ordini esegue `SELECT * FROM items WHERE order_id = ?` per ogni ordine (N+1) invece di una singola query `IN (...)` o `JOIN`.

### `algorithmic-cost-auditor`
- **Cosa cerca**: complessità dipendente dall'input, picchi di allocazione e lavoro bloccante su percorsi caldi (loop annidati, copie ripetute, ricorsione non limitata, ReDoS).
- **Esempio**: per ogni riga di un CSV da 50.000 righe si fa una ricerca lineare in una lista di 50.000 elementi ($O(n^2)$) invece di usare un `set`/`dict`.

### `asset-delivery-auditor`
- **Cosa cerca**: consegna ridondante di asset e bundle sui percorsi critici (import eager, glob loading, immagini non ottimizzate, font bloccanti).
- **Esempio**: la pagina di login importa l'intera libreria di grafici da 1,2 MB in modo sincrono nel bundle iniziale invece di caricarla lazy solo nella dashboard.

### `runtime-cost-auditor`
- **Cosa cerca**: attribuzione di lavoro a pagamento e rispetto dei limiti di spesa dichiarati (chiamate LLM/token, compute, egress, storage, log ad alto volume).
- **Esempio**: un loop di retry su un'API LLM non ha un cap sui token né un budget massimo per richiesta: un prompt malformato può bruciare decine di dollari in pochi minuti.

### `resource-lifecycle-auditor`
- **Cosa cerca**: acquisizione, ownership e rilascio di risorse su percorsi di successo, errore e cancellazione (file handle, socket, connessioni DB, subprocess, listener, timer, lock).
- **Esempio**: un `subprocess.Popen` viene avviato ma in caso di eccezione intermedia non viene terminato né atteso (`wait()`), lasciando processi zombie e file descriptor aperti.

### `responsiveness-auditor`
- **Cosa cerca**: lavoro user-facing che blocca il main/UI thread oltre il budget senza progresso né cancellazione (parsing sincrono, I/O file/rete, crittografia sul thread UI).
- **Esempio**: in un'app desktop o web, un click esegue `JSON.parse` e ordinamento sincrono di 20 MB sul main thread, congelando l'interfaccia per 3 secondi senza stato di caricamento.

---

## 6. Operabilità e rilascio (7 ruoli — `operability-auditor`)

### `observability-auditor`
- **Cosa cerca**: segnali operativi utilizzabili che raggiungono il destinatario (error handling che inghiotte errori, correlazione, metriche, exporter, alert).
- **Esempio**: un blocco `except Exception: pass` silenzia un fallimento di sincronizzazione senza log né metrica, rendendo il guasto invisibile finché non se ne accorgono gli utenti.

### `service-health-auditor`
- **Cosa cerca**: probe di readiness e liveness a regime rispetto alla reale capacità di servire traffico, watchdog e modalità degradata.
- **Esempio**: la liveness probe interroga un servizio esterno di terze parti: quando il fornitore esterno cade, Kubernetes riavvia in loop tutti i pod del nostro servizio.

### `release-compatibility-auditor`
- **Cosa cerca**: coesistenza, continuità e rollback tra versioni supportate (rolling deploy, migrazioni expand-contract, formati versionati).
- **Esempio**: una migrazione rimuove subito una colonna ancora letta dai pod della versione precedente durante un rolling deploy, causando errori 500 finché tutti i pod non sono aggiornati.

### `environment-binding-auditor`
- **Cosa cerca**: risoluzione delle configurazioni d'ambiente e instradamento verso le risorse intese (variabili di deploy, layer di config, promozione artefatti, endpoint).
- **Esempio**: un URL di staging è hardcoded come fallback quando `API_URL` manca, facendo puntare silenziosamente un container di produzione verso staging.

### `feature-flag-auditor`
- **Cosa cerca**: transizioni di stato dei flag, fallback, coesistenza di flag interagenti e disattivazione sicura.
- **Esempio**: attivare `flag_A` senza `flag_B` causa un `NullPointerException` perché il percorso di fallback di `flag_A` presuppone dati scritti solo quando `flag_B` è attivo.

### `recovery-auditor`
- **Cosa cerca**: asset recuperabili e ripristino in servizio utilizzabile dopo un disastro dichiarato (backup, runbook di restore, failover, RPO/RTO).
- **Esempio**: i backup del database vengono creati ma non includono le chiavi di cifratura o i file caricati sullo storage locale necessari per rendere utilizzabile il restore.

### `build-pruning-auditor`
- **Cosa cerca**: elementi raggiunti dal codice solo per nome (reflection, ID risorse, comandi registrati dinamicamente) che l'ottimizzatore della build di release (tree-shaking, shrinking, ProGuard/R8, dead-code elimination) rimuove.
- **Esempio**: in debug funziona tutto, ma nella build di release il bundler/linker elimina un handler registrato solo tramite stringa perché non vede riferimenti statici.

---

## 7. Frontend, UI e accessibilità (4 ruoli)

### `ui-race-auditor`
- **Cosa cerca**: guasti temporali osservabili tra dati asincroni, rendering, layout e interazione utente (risposte fuori ordine, closure stantie, scroll/focus/resize, liste virtualizzate).
- **Esempio**: l'utente digita `"ab"` poi `"abc"` in una casella di ricerca; la richiesta `"ab"` arriva dopo `"abc"` e sovrascrive i risultati più recenti perché manca `AbortController` o un controllo di sequenza.

### `accessible-navigation-auditor`
- **Cosa cerca**: accesso semantico e da tastiera ai percorsi interattivi richiesti (controlli, form, menu, dialog, focus trap, ordine di tabulazione).
- **Esempio**: una modale si apre senza spostare il focus al suo interno e premendo `Esc` non si chiude; un utente da tastiera resta intrappolato dietro l'overlay.

### `accessible-perception-auditor`
- **Cosa cerca**: informazione percepibile, feedback e layout efficace (etichette associate ai campi, errori di validazione annunciati, stati asincroni, contrasto, temi, layout su viewport stretti).
- **Esempio**: un errore di validazione cambia solo il bordo del campo in rosso senza testo né `aria-describedby`, risultando invisibile agli screen reader e agli utenti daltonici.

### `react-auditor`
- **Cosa cerca**: difetti di render, effect e stato specifici di React (dipendenze mancanti in `useEffect`, state derivato duplicato, chiavi instabili in liste, leak di subscription, misuse di context/Suspense/RSC).
- **Esempio**: un custom hook usa `useState` locale per modellare uno stato globale dell'app (es. disponibilità aggiornamenti) e viene montato in due componenti diversi: l'azione in uno non aggiorna mai l'altro.

---

## 8. Linguaggi, stack e piattaforme (7 ruoli)

### `typescript-auditor`
- **Cosa cerca**: punti in cui i tipi TypeScript smettono di descrivere il valore a runtime (`as`, `!`, `any`, generic non vincolati, risposte JSON non validate, config compilatore).
- **Esempio**: `const data = (await res.json()) as User` dichiara `User` a compile-time senza validare il payload a runtime; se il server restituisce `{ error: "..." }`, il codice crasha più avanti leggendo `data.profile.name`.

### `python-auditor`
- **Cosa cerca**: semantica di valutazione e controllo specifica di Python (default mutabili, late binding nelle closure, short-circuit, `return` in `finally`, context manager, logging).
- **Esempio**: `def add(item, items=[]):` condivide la stessa lista tra tutte le chiamate; oppure `[lambda: i for i in range(5)]` cattura tutte le closure sull'ultimo valore `4`.

### `stripe-auditor`
- **Cosa cerca**: integrazioni Stripe che perdono, duplicano o si fidano ciecamente di un evento di pagamento (webhook `constructEvent`, copertura eventi, checkout, subscription, Connect).
- **Esempio**: l'app attiva l'abbonamento sulla pagina di redirect `success_url` invece che sul webhook `checkout.session.completed`, oppure non gestisce `invoice.payment_failed` lasciando attivo un utente che non ha pagato.

### `tauri-ipc-auditor`
- **Cosa cerca**: percorsi IPC Tauri su cui una webview compromessa raggiunge l'host (`#[tauri::command]` che si fidano degli argomenti, `invoke`/`emit`/`listen`, custom URI scheme, deep-link).
- **Esempio**: un comando `#[tauri::command] fn read_note(path: String)` apre qualsiasi percorso passato dal frontend senza confinarlo nella directory delle note, permettendo path traversal sull'intero disco.

### `tauri-hardening-auditor`
- **Cosa cerca**: configurazione Tauri (`tauri.conf.json`, `capabilities/*.json`, CSP, scope asset/shell, updater, sidecar) che allarga i permessi oltre il necessario.
- **Esempio**: una capability concede `fs:allow-read-file` su `**` o abilita `shell:allow-open` senza filtro di schema, permettendo alla webview di lanciare eseguibili arbitrari.

### `tauri-sync-auditor`
- **Cosa cerca**: stato Tauri che diverge tra backend Rust, finestre multiple e copie frontend (lock tenuti attraverso `.await`, scrittori concorrenti, eventi persi o riordinati).
- **Esempio**: un comando Rust tiene un `std::sync::Mutex` bloccato attraverso un `.await` (deadlock), oppure due finestre aggiornano lo stesso file di configurazione senza coordinamento sovrascrivendosi a vicenda.

### `tauri-reliability-auditor`
- **Cosa cerca**: percorsi Tauri che congelano, crashano, perdono risorse o falliscono su una piattaforma (comandi bloccanti sul main thread, `unwrap()` su input, leak di listener/finestre, percorsi Windows/macOS).
- **Esempio**: un comando sincrono esegue `std::fs::read` o una richiesta HTTP sul main thread congelando la finestra, oppure usa `.unwrap()` su un payload JSON proveniente dalla webview facendo andare in panic l'intera app.

---

## 9. Test, pulizia, dipendenze e igiene (6 ruoli)

### `testing-auditor`
- **Cosa cerca**: comportamenti lasciati senza protezione e test che non possono fallire, indeboliti, mockati male o flaky.
- **Esempio**: un test mocka la funzione stessa sotto test o asserisce solo `expect(result).toBeDefined()`, passando anche quando la logica è completamente rotta; oppure usa `sleep(100)` rendendo la suite instabile in CI.

### `application-reachability-auditor`
- **Cosa cerca**: simboli applicativi, export, barrel, asset o entry point ritirati che non hanno più alcun consumatore legittimo.
- **Esempio**: dopo un refactoring restano 4 file di vecchi handler e 300 righe di helper esportati ma mai più importati da nessun percorso vivo.

### `artifact-lifecycle-auditor`
- **Cosa cerca**: artefatti documentali e di migrazione non allineati all'intento attuale (riferimenti obsoleti, residui di rebrand, vecchi piani, backup, resti di migrazioni).
- **Esempio**: il README e gli script di avvio citano ancora vecchi nomi di comandi o flag rimossi mesi prima.

### `dependency-usage-auditor`
- **Cosa cerca**: consumatori reali delle dipendenze e proprietà delle dichiarazioni per pacchetto (pacchetti inutilizzati, dipendenze runtime dichiarate solo in dev o viceversa).
- **Esempio**: un pacchetto usa `lodash` a runtime ma lo dichiara solo in `devDependencies`, rompendo l'installazione di produzione.

### `dependency-provenance-auditor`
- **Cosa cerca**: pacchetti installati o dichiarati la cui origine o versione porta un rischio noto e raggiungibile (bump, pin/range modificati, cambio registry/URL).
- **Esempio**: un lockfile introduce un pacchetto da un URL git non pinnato a un commit SHA, oppure fa downgrade a una versione con CVE nota.

### `workspace-hygiene-auditor`
- **Cosa cerca**: file tracciati rigenerati dalla build, regole `.gitignore` che nascondono sorgenti necessari, file scratch/residui di merge e stato Git sporco.
- **Esempio**: una PR committa `dist/`, `.DS_Store` o file temporanei di test, oppure una regola `.gitignore` troppo larga (`*.json`) nasconde un file di configurazione necessario al build.

---

## Tassonomia trasversale e casi reali documentati

Oltre ai 59 ruoli, `plugins/senior-review/skills/defect-taxonomy/references/` raccoglie le categorie trasversali caricate per dominio (concorrenza, tipi, memoria, sicurezza, sistemi distribuiti, dati/ops, `logic-integrity.md`, `ui-state-intent.md`).

### Caso reale #1 — Muro: incoerenza UI–stato–intento («Needs a build»)

- **Classe**: `ui-state-intent.md` (`U1.1 Overloaded State Value`, `U1.2 Contradictory Entity Views`, `U2.1 Prescription Disguised as Status`, `U2.2 Ghost or Misnamed Command`, `U3.1 Dropped Diagnostic Cause`).
- **Origine**: progetto Muro (novembre 2026), corretto nel commit `b1b73a5`.
- **Sintomo**: la tabella Sync mostrava un badge arancione `Needs a build` (e l'intestazione `"N plugins need a build"`) per quattro situazioni diverse:
  1. plugin di terze parti che non pubblica per quell'harness;
  2. progetto `.mp` la cui release non contiene la variante;
  3. plugin mai controllato;
  4. plugin adattato con AI le cui istruzioni personalizzate sono cambiate dopo l'adattamento.
- **Causa nel codice**:
  - In `apps/desktop/src/model.ts`, `cellState` restituiva un solo valore `needs-build` per sia "non disponibile" sia "da riadattare".
  - `SyncTable.tsx` traduceva quel valore in una prescrizione (`Needs a build`), ma nell'app non esiste alcun comando "Build" (il comando reale è `Adapt with AI`, nascosto in `More`).
  - Il backend Rust (`missing()` in `crates/muro-registry/src/sources.rs`) conosceva già la causa precisa, ma la UI la schiacciava in una sola etichetta generica.
  - Contraddizione interna: `pluginState` diceva già `Adapt again` mentre la tabella diceva `Needs a build`.
- **Rimedio**: separazione in due stati distinti (`unavailable` → badge neutro `Not available`; `adapt-again` → badge arancione `Adapt again`), propagando il significato reale.
- **Regola generale**:
  1. Un'etichetta di stato dichiara il fatto attuale; il rimedio è un'azione separata che usa il nome reale del comando.
  2. Uno stato nel modello ha un solo significato: cause con rimedi diversi richiedono stati diversi.
  3. Quando il backend conosce già la causa, la UI non la riduce a una parola generica.
  4. Per rilevare questa classe serve il **grafo end-to-end della GUI** (backend → modello di stato → proiezione UI → comandi esposti) letto da un revisore LLM.
