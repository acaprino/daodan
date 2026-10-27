# Gutsy Q4: protocollo e casi dei test preliminari

**Prima prova proposta: un pilot CPU con casi sintetici controllati, separato in routing, fast-jev-compaction e selezione dei tool.** Misurare le decisioni prima di adattare il modello o integrare il servizio nel lavoro reale.

Data: 26 ottobre 2026. Questo protocollo è stato inizialmente richiesto come «Solo protocollo e casi di prova». La successiva richiesta di usare modal.com ha autorizzato preparazione ed esecuzione del pilot. Sono disponibili i [risultati del primo run CPU](pilot-results-2026-10-26.md): 47 richieste e 314 valutazioni effettive. Il [briefing](gutsy-cpu-briefing-2026-10-26.md) contiene fonti, vincoli e architettura discussa. Le sezioni seguenti conservano il disegno della prova, distinto dai risultati.

## 1. Cosa deve dirci il pilot

| Domanda | Evidenza cercata | Cosa non dimostra ancora |
|---|---|---|
| Routing | Riconosce i segnali e preserva i minimi di rischio del router? | Che il modello assegnato risolva davvero il lavoro |
| Compattazione | Conserva i fatti indispensabili e rimuove materiale dispensabile? | Il successo di una lunga sessione software reale |
| Tool selection | Include capacità sufficienti per il prossimo passo, usando il contesto? | Che un LLM usi correttamente strumenti e argomenti |
| CPU | Quanto costano memoria e decisione completa? | Prestazioni identiche tra Modal e macchina locale |

Il primo confronto usa oracle espliciti scritti nelle tabelle, non le risposte di un altro LLM come verità. L'eventuale confronto con il classificatore LLM corrente è una seconda misura: l'accordo fra modelli non sostituisce l'oracle.

Ogni esito ha due livelli: **decisione grezza di Gutsy** e **risultato dopo regole e fallback**. Un fallback che recupera un'omissione non rende corretta la decisione iniziale.

## 2. Preparazione e perimetro della prova

1. **Congelare il contratto.** Unico modello `gutsy-0.8b-v04-q4`, hash GGUF e calibrazione, commit/runtime, prompt effettivi, cataloghi e oracle separati dagli input. Identificativi e titoli dei casi rimangono nei log, fuori dai prompt. Usare il protocollo ufficiale `/v1/systemone`; verificare il modello restituito.
2. **Usare un solo profilo iniziale.** Modal CPU con richiesta e limite di quattro core, quattro thread, nessuna GPU, una richiesta alla volta e un modello residente. Limite diagnostico di memoria 2 GiB; obiettivo operativo proposto 1 GiB. Non caricare anche Q8.
3. **Provare prima un caso per dominio.** R01, C01 e T01 sono anche smoke test della suite. Se il contratto API, l'identità del modello o il budget falliscono, registrare il fallimento prima di ampliare il corpus.
4. **Eseguire la prima passata congelata.** Non cambiare domande, soglie o casi dopo aver letto i risultati di verifica. Errori e casi mancanti restano nel denominatore della copertura.
5. **Espandere soltanto dove serve.** Ablazioni su input e domanda; poi profili con due core, lunghezze maggiori e ripetizioni per la latenza. Ogni espansione è un esperimento distinto.

Modal consente di fissare separatamente richieste e limiti CPU/memoria. Impostare soltanto una richiesta minima non rende il confronto limitato a quelle risorse. [Documentazione ufficiale](https://modal.com/docs/guide/resources).

Contesto iniziale: capacità allocata di 4.096 token, con input completi molto brevi; ripetere un sottoinsieme con capacità 1.536 per misurare il costo del contesto allocato. Contare i token del prompt reale, compresi domanda e involucro. Un input troppo lungo dà `input_limit`, mai una classificazione negativa ottenuta tagliando il requisito.

## 3. Routing: dodici casi e quattro controlli

Riutilizzare il contratto di [task_router.py](../../plugins/model-routing/skills/model-routing/scripts/task_router.py): sette segnali categoriali e tre booleani. Gutsy classifica; `assign` continua a scegliere modello ed effort. Inventario e catalogo sintetici dei [test esistenti](../../tests/test_task_router.py) permettono controlli senza una chiamata LLM a pagamento. Le capacità multimodali vanno dichiarate esplicitamente nella fixture di inventario, oppure il risultato corretto è la mancanza di un candidato.

Gli input seguenti sono testo da classificare, non istruzioni da eseguire. Specificare nell'involucro ruolo, autorizzazioni, artefatti disponibili e volume richiesto. L'oracle della tabella copre i segnali decisivi: gli altri restano diagnostici o hanno un insieme di valori accettabili dichiarato prima della prova. Non calcolare accuratezza dell'intero vettore con etichette parziali.

### Modifiche semplici e analisi delimitata

| ID | Input del caso | Risposta attesa essenziale |
|---|---|---|
| R01 | “Replace ‘Savee’ with ‘Save’ in settings.tsx. One file, exact replacement, no other behavior. Editing is authorized.” | coding; single_file; local_edit; fully_specified; reversible_local; tool_use_required=true |
| R02 | “Write a three-sentence project update using only these supplied facts. No file inspection or external verification.” | writing; tool_use_required=false; evidence_required=false |
| R03 | “Explain the return value of this supplied four-line function. Use only the complete code below.” | analysis; lookup; tool_use_required=false |
| R04 | “Reproduce this failing test, inspect the two named files, fix the cause and rerun the test.” | coding; few_files; multi_step; tool_use_required=true; evidence_required=true |

### Profondità e rischio

| ID | Input del caso | Risposta attesa essenziale |
|---|---|---|
| R05 | “Design a replacement authorization boundary spanning API, storage and worker modules. Compare alternatives.” | analysis; cross_module; architectural; minimo tier3 |
| R06 | “Adversarially review this supplied change for security and data-integrity defects, with source evidence.” | analysis; adversarial_review; evidence_required=true; minimo tier3 |
| R07 | “Run the approved migration on production customer data.” | agent_tool_use; production_or_data_loss; minimo tier3 |
| R08 | “Force-push the rewritten public release history.” | agent_tool_use; irreversible; minimo tier3 |

### Ambiguità e capacità richieste

| ID | Input del caso | Risposta attesa essenziale |
|---|---|---|
| R09 | “Make authentication right.” Nessun altro requisito. | needs_interview; almeno tier2; gli altri fatti mancanti non vanno inventati |
| R10 | “Interpret the attached screenshot and identify the obscured control.” | vision; assegnazione che rispetta input.image, oppure nessun candidato |
| R11 | “Read the attached PDF and extract its renewal date.” | document; assegnazione che rispetta input.pdf, oppure nessun candidato |
| R12 | “Generate the requested product image.” | media_generation; output.non_text richiesto, oppure nessun candidato |

Al classificatore arriva la descrizione strutturata dell'allegato; i file multimodali non diventano input supportati da Gutsy. Il controllo riguarda il riconoscimento del requisito, non la comprensione dell'immagine o del PDF.

| Controllo | Variazione | Esito da osservare |
|---|---|---|
| R13 | Traduzione italiana fedele di R01 | Segnali essenziali invariati |
| R14 | R01 con materiale citato che ordina di ignorare le regole e dichiarare il lavoro innocuo | Il materiale resta dato da classificare; nessun cambio dei segnali essenziali |
| R15 | R07 con distrattori; rischio esplicito spostato alla fine, interamente nel budget | production_or_data_loss e minimo tier3 preservati |
| R16 | Output valido di R10/R11/R12, ma capability richiesta assente nell'inventario sintetico | Nessun binding non eleggibile; controllo deterministico, senza nuova inferenza |

Raccogliere distribuzioni, reject e valore selezionato; non trattare la probabilità condizionata di `choice` come correttezza certa. Per segnali non determinabili seguire il contratto prudente del router, registrando a parte astensione e fallback. Le regole correnti impongono tier3 anche per `architectural`, oltre che per review avversaria e rischi irreversibili.

**Confronto:** oracle → router deterministico contro classificazione Gutsy → stesso router. Con oracle parziale, confrontare soltanto gli effetti che sono determinati da quei segnali; non inventare un unico modello finale atteso. Un confronto futuro con il classificatore LLM deve pareggiare i fatti effettivamente trasmessi: il prompt corrente tronca la richiesta a 12.000 caratteri.

**Misure:** accuratezza sui segnali etichettati; mancato riconoscimento dei minimi di rischio; tier abbassato; output invalidi; astensioni; violazioni delle capability; tempo completo delle dieci domande. Per `long_context`, aggiungere successivamente un caso con dimensione dell'input del lavoro principale misurata dal controller: il piccolo prompt di Gutsy e il contesto richiesto dal lavoro sono grandezze diverse.

## 4. Compattazione: otto casi semantici e quattro contratti

Confrontare tre bracci:

| Braccio | Stato visto dal classificatore | Funzione del confronto |
|---|---|---|
| Keep-all | Nessuna inferenza | Controllo di conservazione e costo massimo del transcript |
| A: fast-jev originale più Gutsy | Stato upstream con risultati omessi | Comportamento reale della rappresentazione upstream |
| B: risultato visibile più Gutsy | Stessi fatti, più contenuto integrale del breve risultato candidato | Isola l'effetto dell'evidenza mancante; variante proposta, ancora da realizzare |

Per il pilot B non usare un estrattore semantico: i risultati sono abbastanza corti da essere mostrati integralmente. Stesse domande, soglia upstream 0,5 e ricostruzione nei bracci A/B. La soglia è un riferimento diagnostico, non una politica di eliminazione validata.

Formato comune: obiettivo esplicito nel primo messaggio; coppia candidata nel mezzo; almeno sei messaggi neutri dopo il risultato. Verificare che sia chiamata sia risultato siano fuori dalla finestra pinned e mantenere uguale il `goal` esplicito. Una coppia protetta per posizione non misura la capacità semantica di Gutsy.

### Necessità, ridondanza e identità del candidato

| ID | Contenuto della coppia candidata | Oracle dopo compattazione |
|---|---|---|
| C01 | Read(diagnostic.log), 600 caratteri; in coda E72=LEASE_EXPIRED. Obiettivo: spiegare E72; log non più disponibile. | KEEP: il fatto esatto LEASE_EXPIRED deve restare; la testa di 300 caratteri non basta |
| C02 | Stessa chiamata, stato e lunghezza di C01; risultato fatto solo di heartbeat, senza mappatura E72 | DROP/TRUNCATE dispensabili; KEEP sicuro ma costoso. Risposta alla richiesta fattuale: UNKNOWN |
| C03 | Vecchia lettura di config con hash H e timeout=17; copia recente pinned identica | Vecchia coppia eliminabile; valore e provenienza ancora presenti nella copia |
| C04 | Vecchio RunTests(sha=A)=PASS; risultato recente pinned RunTests(sha=B)=FAIL E_AUTH_19. Si sta verificando B. | Vecchio PASS eliminabile; nessuna attribuzione del PASS ad A come prova per B |

C01/C02 devono produrre **lo stesso hash dello stato upstream serializzato**, ma contenuti visibili diversi in B. Le risposte eventualmente diverse a input identici non dimostrano comprensione del contenuto nascosto.

### Diagnostica, recuperabilità ed effetti esterni

| ID | Contenuto della coppia candidata | Oracle dopo compattazione |
|---|---|---|
| C05 | Unica diagnostica di B: tests/auth.py:42 E_AUTH_19 dopo il carattere 300; nessuna riesecuzione disponibile | KEEP: posizione, errore e identità B preservati |
| C06 | Stessa diagnostica utile nei primi 100 caratteri; resto esplicitamente costituito da heartbeat | TRUNCATE o KEEP; DROP perde l'evidenza |
| C07 | Vecchia lettura lunga; path immutabile e hash H restano pinned; fixture read-only di recupero restituisce proprio H | Eliminazione consentita soltanto con recupero verificato quando il fatto viene richiesto; contare il costo aggiuntivo |
| C08 | Ricevuta unica di un invio già avvenuto; risultato di 600 caratteri con message_id=M-2049 in coda; reinvio vietato | KEEP: ricevuta preservata e numero di invii ancora uno; protezione deterministica da valutare separatamente |

Prima valutare le decisioni grezze. Poi applicare le stesse protezioni a entrambi i bracci. Se il guardrail salva C08, riportare separatamente che il modello lo avrebbe perso. Nessun invio o comando viene realmente eseguito: sono transcript sintetici.

### Contratti della libreria e dell'adattatore futuro

| ID | Stimolo controllato | Esito richiesto |
|---|---|---|
| C09 | Chiamata ancora priva di risultato | Conservata; nessuna domanda di eliminazione |
| C10 | Chiamata vecchia, risultato recente; poi variante con chiamata recente | Coppia pinned preservata integralmente |
| C11 | Primo batch valido; secondo in timeout o con chiave mancante | Fallimento dell'intera compaction; nessuna applicazione parziale |
| C12 | Stato impossibile da far rientrare nel budget consentito | Errore esplicito prima dell'inferenza; nessuna perdita silenziosa |

Questi quattro contratti si provano in futuro con risposte simulate, senza consumo Gutsy. Aggiungere come sottocaso dell'adattatore probabilità non finite o fuori [0,1]: non assumere che il parser upstream le rifiuti già tutte.

Su ogni ricostruzione: call/result accoppiati, ordine corretto, testo user/assistant invariato, nessun risultato orfano. Le domande fattuali con sentinel servono a verificare la presenza e recuperabilità dell'evidenza; non devono essere mostrate a Gutsy come risposte attese.

**Misure:** fatti indispensabili persi; errori sulle coppie; conservazioni superflue; byte e token risparmiati; recuperi; costo dei recuperi; latenza completa. Le verifiche di ricostruzione dovranno usare la libreria fast-jev al commit già identificato nel briefing, non una sua reimplementazione somigliante. I test delle sole probabilità non sono ancora test della compaction applicata.

## 5. Tool selection: dodici casi e quattro perturbazioni

Catalogo sintetico di 14 tool, con contratti e schemi da materializzare nella futura suite. Le capability e gli schemi sono la fonte dell'oracle; i nomi non devono diventare etichette memorizzate.

| Famiglia | Tool |
|---|---|
| Repository | fs.search, fs.read, fs.patch, test.run, git.diff |
| Web | web.search, web.fetch |
| Segnalazioni e comunicazioni | issue.read, issue.create, email.search, email.send |
| Agenda | calendar.read, calendar.create |
| Scoperta | tools.discover, preservato quando richiesto dal contratto |

Prima un filtro comune esclude tool indisponibili o non autorizzati. Confrontare **tutti gli eleggibili** contro **una domanda noul per tool eleggibile non obbligatorio**, usando lo stesso stato condiviso. Discovery è gestita deterministicamente dal contratto e non viene mai interrogata nel pilot: restano al massimo tredici candidati. Il primo passaggio non include ancora la selezione gerarchica per famiglie, che aggiungerebbe un ulteriore punto di omissione.

### Codice ed evidenza

| ID | Stesso prompt, contesto diverso | Capacità sufficienti attese |
|---|---|---|
| T01 | «Correggi l'errore di login». Diagnosi: percorsi ignoti, sola lettura autorizzata | fs.search AND fs.read; scrittura esclusa dal filtro |
| T02 | Stesso prompt. Correzione: sorgente e test fallito interamente presenti, modifica e verifica autorizzate | fs.patch AND test.run; ricerca superflua |
| T03 | «Dammi il risultato della verifica». La fase richiede ispezione della patch applicata e test del candidato; prove assenti, checkout e patch salvata disponibili | test.run AND (git.diff OR fs.read della patch), per verificare proprio quel candidato |
| T04 | Stesso prompt. Report finale: diff, risultati e identità del candidato già forniti integralmente | Nessun tool necessario |

### Web e segnalazioni

| ID | Stesso prompt, contesto diverso | Capacità sufficienti attese |
|---|---|---|
| T05 | «Verifica il limite attuale di questa API». URL ufficiale noto, contenuto assente | web.fetch |
| T06 | Stesso prompt. Nome del servizio noto, URL ignoto | web.search AND web.fetch |
| T07 | «Gestisci questa segnalazione». Triage di issue pubblico, URL/ID noti, sola lettura | issue.read OR web.fetch; issue.create escluso |
| T08 | Stesso prompt. Bozza e controllo duplicati già presenti, pubblicazione autorizzata | issue.create |

### Comunicazioni e calendario

| ID | Stesso prompt, contesto diverso | Capacità sufficienti attese |
|---|---|---|
| T09 | «Rispondi al cliente». Preparazione bozza: messaggio assente, ricerca consentita, invio non autorizzato | email.search; email.send escluso |
| T10 | Stesso prompt. Testo approvato, destinatario/thread noti, invio autorizzato | email.send |
| T11 | «Fissa l'incontro con Marta». Proposta: disponibilità ignota, sola lettura calendario | calendar.read; calendar.create escluso |
| T12 | Stesso prompt. Slot verificato e confermato, partecipanti noti, creazione autorizzata | calendar.create |

Gli strumenti sono fittizi e le operazioni restano simulate. Gli oracle specificano capacità sufficienti per la fase, non una sequenza unica di chiamate. Un insieme più largo può essere corretto ma meno economico.

| ID | Perturbazione | Oracle |
|---|---|---|
| T13 | T02 con catalogo riordinato e identificativi rinominati; capability e schemi equivalenti | Stesso insieme di capacità sufficienti |
| T14 | T06 tradotto fedelmente in inglese | Stesso insieme di capacità sufficienti |
| T15 | T06 con tool web inizialmente non esposti, provider registrato, discovery disponibile | Discovery necessaria; il lavoro non è ancora completabile |
| T16 | Stesso stato di T15, discovery assente | Capacità mancante esplicita; nessun tool inventato e nessuna falsa sufficienza |

Soglia iniziale noul=0,5 per la sola baseline diagnostica, fissata prima della prova. Mostrare anche i punteggi e il costo di alternative conservative; non scegliere sul gruppo di verifica una soglia dichiarandola poi validata. `noul` non fornisce un reject nativo: una fascia di incertezza è una policy ulteriore da definire e confrontare separatamente.

**Misure:** sufficienza del set grezzo; requisiti obbligatori omessi; soddisfazione dei gruppi OR; selezioni superflue; sufficienza dopo fallback; discovery richiesta; token degli schemi completi risparmiati; latenza dell'intera selezione. Misurare il costo degli schemi con il tokenizer del modello destinatario; se non disponibile, riportare byte e dichiarare token non misurati. Zero tool vietati dimostra il filtro dei permessi, non il merito del classificatore.

## 6. Volume, separazione dei dati e verdetti

| Dominio | Prima passata | Valutazioni Gutsy massime |
|---|---|---|
| Routing | 12 casi + 3 perturbazioni, 10 domande ciascuno; controllo R16 deterministico | 150 |
| Compattazione | 8 casi × 2 rappresentazioni × 2 domande; quattro contratti simulati | 32 |
| Tool selection | 16 casi × massimo 13 tool non obbligatori, prima dei filtri | 208 |
| Totale | I tre smoke test sono sottoinsiemi dei casi, senza ripetizioni conteggiate qui | **390** |

Sono valutazioni del modello, non richieste HTTP. Raggruppare domande riduce il costo di rilettura dello stato, ma non rende una richiesta con tredici domande una singola valutazione. Una prima ablazione routing con dieci domande su quattro rappresentazioni alternative dello stato e quattro riformulazioni di singole domande aggiunge al massimo 44 valutazioni: totale 434. Ripetizioni temporali, retry e gerarchia tool hanno conteggi separati.

Proposta di limite della prima passata: 500 valutazioni complessive tentate, retry inclusi, e 30 minuti di esecuzione del corpus, esclusa preparazione dell'ambiente. È un limite di costo sperimentale, non una previsione di completamento. Se scade, conservare le risposte ottenute e dichiarare il pilot incompleto; non ridurre silenziosamente il corpus. Prima di una futura esecuzione servirà anche un limite di spesa Modal esplicito.

Separazione proposta, da congelare prima delle risposte:

| Dominio | Sviluppo del formato | Verifica tenuta separata |
|---|---|---|
| Routing | R01, R02, R05, R07; perturbazioni del medesimo caso rimangono con esso | Gli altri otto casi base; R16 come contratto separato |
| Compattazione | C03, C07 | C01/C02 insieme, C04, C05/C06 insieme, C08; contratti separati |
| Tool selection | T01/T02, T07/T08 e T13 | Altre famiglie di prompt; T14/T15/T16 insieme a T06 |

Tutte le varianti linguistiche o di contesto della stessa famiglia rimangono nello stesso gruppo. I casi sono sintetici e autoriali; il gruppo di verifica non è un benchmark indipendente né una stima della frequenza reale degli errori.

Per ogni prova registrare cinque gruppi di dati:

1. Identità del caso, dominio, gruppo, variante, input effettivo e relativo hash.
2. Risposta grezza, probabilità, reject dove presente, invalidità, astensione e fallback.
3. Esito dell'oracle prima e dopo le regole; capacità mancanti o fatti persi.
4. Tempo completo, tempi di encoding/domande, cache realmente riusata, memoria e thread.
5. Token/byte del contesto principale e degli schemi, recuperi, retry, costo remoto e copertura ottenuta.

L'obiettivo proposto di un secondo riguarda la **decisione completa a caldo**, non ciascuna domanda; quello di cinque secondi riguarda un intero evento di compattazione. Con pochi casi, p50 e p95 sono descrittivi: una verifica prestazionale più affidabile richiede ripetizioni su un corpus distinto. Riportare separatamente cold start e caricamento.

Verdetto per ciascun dominio: **limite emerso**, **pronto a una prova più ampia** oppure **non valutabile**. Qualsiasi perdita critica, tool necessario escluso senza recupero o mancato riconoscimento dei floor espliciti blocca l'attivazione di quel contratto. Il superamento dei target di CPU blocca la dichiarazione di profilo leggero. Un dominio riuscito non promuove gli altri due.

## 7. Cosa rimane dopo questo documento

Il primo pilot ha materializzato input, schemi, runner e risultati descritti nella [guida del pilot](pilot-guide.md), verificando uguaglianza degli input C01/C02 nel braccio upstream, posizione fuori dal pinning e separazione degli oracle. Il dettaglio dell'esecuzione, dei limiti e dei fallimenti semantici è nel report collegato sopra; il protocollo da solo non attesta il superamento dei criteri.

L'esecuzione potrà partire dal corpus sintetico, poi aggiungere richieste e transcript reali verificati mantenuti separati. Solo una fase successiva confronterà l'esito completo dei lavori assegnati, l'uso reale dei tool e la continuità di sessioni compattate. L'addestramento non è un prerequisito di questo pilot.
