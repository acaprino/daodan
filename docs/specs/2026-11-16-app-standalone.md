# Daodan standalone: confini applicativi

**Stato:** proposta tecnica sulla destinazione concordata. Questo documento definisce i confini; server applicativo, coordinatore e adattatori dei motori restano da implementare.

## Problema

Daodan possiede già analisi, dati persistenti e report, ma la sessione host esegue il ragionamento e coordina i worker. La web app deve poter avviare e seguire lo stesso lavoro con Claude Code locale, Codex locale o un endpoint compatibile OpenAI, mantenendo una sola logica applicativa.

Oggi `MapService` è indipendente dal runtime MCP. `make_server`, `live_routes` e `live_actions` espongono già run, eventi, richieste e finding. L'avvio HTTP vive nel tool MCP; le richieste passano da `pending` a `taken` e `done`, ma nessun consumer autonomo avvia gli agenti. Il mockup business SmoothUI è una dimostrazione, non una UI già collegata.

## Soluzione

Un'app locale con un unico nucleo applicativo, trasporti sottili e adattatori dei motori. Il launcher compone le dipendenze, avvia il server e ne possiede la chiusura. L'ingresso è una repository GitHub e il branch selezionato; il backend prepara il checkout da analizzare. All'inizio un processo gestisce un contesto repository/branch attivo.

| Confine | Responsabilità | Dipendenze consentite |
| --- | --- | --- |
| Avvio | Configurazione, composizione, avvio e arresto | Componenti concreti dell'app |
| UI, HTTP e MCP | Input, autenticazione locale, presentazione e consegna degli eventi | Operazioni dell'applicazione |
| Applicazione | Richieste, coordinamento di analisi/review, avanzamento, esiti e ripresa | Nucleo esistente e contratto dei motori |
| Analisi e review | Snapshot, pipeline, grafi, evidenze, verifica e report | Strumenti e store già proprietari dei dati |
| Motori | Avvio, comunicazione, eventi, sessione e arresto del motore scelto | CLI o protocollo API specifico |
| GitHub | Login, repository accessibili, branch e preparazione del checkout | API GitHub, Git e credenziali del backend |

Le dipendenze vanno verso il nucleo. Solo l'avvio sceglie gli adattatori concreti; analisi e regole di review non importano HTTP, MCP o SDK dei modelli. Nessun framework di plugin o contenitore di dependency injection finché non risolve un problema reale.

## Casi d'uso

1. Collego una repository GitHub pubblica o privata, scelgo branch e motore, avvio analisi o review e ne seguo avanzamento, messaggi e lacune.
2. Esploro grafi e report anche quando il motore non è in esecuzione.
3. Riprendo un lavoro identificato, oppure ne interrompo l'esecuzione conservando risultati e stato affidabili.
4. Una sessione esterna usa MCP sullo stesso progetto senza duplicare coordinamento o dati.

## Percorso UI

**Ingresso GitHub.** Inserire un solo URL e tentare l'accesso, senza scegliere pubblico o privato. Se accessibile, caricare i branch; se non accessibile, chiedere il login e riprovare lo stesso URL. Un accesso fallito non dimostra che la repository sia privata: può non esistere o mancare un permesso. Se anche dopo il login resta inaccessibile, indicare di controllare URL e permessi; un errore di rete offre invece la ripetizione della verifica. Scegliere `main` se esiste, altrimenti `master`, altrimenti il branch predefinito dichiarato dalla repository. L'utente può selezionarne un altro. Mostrare repository, visibilità solo se nota, branch e commit acquisito lungo il percorso. Una repository vuota o non accessibile non avvia l'analisi. Modificare l'URL invalida esito, richiesta di login e operazioni pendenti, anche tornando al valore precedente.

1. **Pre-mappa.** L'analisi descrive il progetto selezionato e non ha un obiettivo testuale da compilare. Prima dell'analisi approfondita mostrare tecnologie, linguaggi, framework, toolchain e dipendenze con versione, fonte e stato. Due alberature distinguono directory fisiche e moduli tecnici dichiarati dai manifesti; la selezione apre i relativi dettagli. La vista compone la pre-mappa canonica con le dichiarazioni dei manifesti: le librerie non entrano nel suo schema. Una dipendenza dichiarata non è una versione installata o risolta; un compiler usato dagli analyzer non prova che il progetto usi quel framework.
2. **Analisi.** Esporre step, analyzer e unità in lavorazione, avanzamento, messaggi, errori e lacune. Il grafo si costruisce con i risultati disponibili: aggiungere nodi e archi quando un artefatto canonico è stato scritto, senza animare relazioni inventate. Riutilizzare eventi e lettura delle viste esistenti, mostrando stato parziale e provenienza. Pausa, annullamento e ripresa conservano il lavoro acquisito; non presentare la sola animazione come avanzamento reale.
3. **Sintesi e grafo.** Rendere consultabili sintesi, responsabilità, relazioni, flussi, evidenze e limiti man mano che sono disponibili; al termine presentare l'esito finale e il grafo esplorabile con filtri e inspector. Finché una sintesi non è prodotta, indicarla come in attesa. Tornare alla pre-mappa o ricaricare la pagina conserva stato e selezioni.

Il mockup mantiene il tema business originale SmoothUI. Accesso GitHub e selezione sono dimostrativi: non eseguono login o clone. Le viste distinguono contesto selezionato, inventario e manifesti locali, snapshot storico e avanzamento simulato. La crescita progressiva della demo non dichiara un'analisi del branch scelto.

Gli scenari offline sono deterministici: `acaprino/daodan` è l'esempio accessibile senza login; `organizzazione-demo/progetto-privato` richiede login e riprova sullo stesso URL; `organizzazione-demo/non-disponibile` resta inaccessibile anche dopo login; `organizzazione-demo/errore-rete` produce un errore di connessione simulato. Gli altri URL validi aprono una demo generica con esistenza e visibilità non verificate. Esiti e login simulato persistono; i salvataggi della precedente scelta pubblico/privato richiedono una nuova verifica dell'URL.

### Perimetro della review

La code review può avere un obiettivo facoltativo. Da quello e dalla mappa Daodan ricava un perimetro proposto di moduli, funzioni/simboli e file/cartelle, includendo chiamanti e dipendenze pertinenti. La UI mostra la corrispondenza fra questi livelli, le evidenze e le lacune, e permette di correggere il perimetro. Senza obiettivo usa il changeset o il progetto scelto. Nessun campo di questo tipo condiziona l'avvio dell'analisi della codebase.

Nel mockup il perimetro storico deriva dai record della review campione; per un nuovo testo libero senza motore collegato il perimetro resta da calcolare, senza fingere un'inferenza.

## Decisioni architetturali

- **Riuso prima dell'estrazione.** I moduli canonici vivono nell'applicazione (`daodan/core/`, comando `daodan`); i plugin sono skill che la chiamano e non contengono codice (dal 18 novembre; script, catalogo e ruoli di senior-review in `daodan/core/` e `daodan/review/`). Separare bootstrap HTTP e MCP senza copiare `MapService` o la pipeline. Il nome attuale del modulo non impone una dipendenza dal trasporto.
- **GitHub prepara l'ingresso, non analizza.** Un adattatore concreto gestisce repository e branch e consegna al nucleo un checkout locale legato a repository e commit immutabile. Ogni `MapService` resta vincolato al proprio checkout. Memorizzare l'identità GitHub e il branch insieme al commit effettivo della run; risultati e cache appartengono a quel contesto. Cambiare repository/branch invalida la vista corrente, preservando lo storico; durante un lavoro attivo la selezione resta bloccata finché si termina o si interrompe.
- **Accesso privato.** Per l'app locale usare una GitHub App con device flow abilitato e permessi repository in lettura per metadata e contenuti; il backend conserva i token nel portachiavi del sistema e gestisce scadenza/revoca. Mostrare soltanto repository autorizzate sia all'utente sia all'app; il login da solo non concede accesso a tutte le repository private. Le pubbliche possono essere indicate senza login. Il token non entra nell'URL persistito del clone, negli argomenti registrati o nei log. La registrazione della GitHub App e il suo client ID sono prerequisiti dell'integrazione reale. [Autenticazione](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/generating-a-user-access-token-for-a-github-app), [permessi](https://docs.github.com/en/apps/creating-github-apps/registering-a-github-app/choosing-permissions-for-a-github-app).
- **Lavoro fuori dalle richieste HTTP.** La UI deposita una richiesta e legge eventi/esiti; un coordinatore la prende in carico. Anche preparazione e snapshot, oggi sincroni nella rotta di creazione, passano nel lavoro in background. Iniziare con un lavoro alla volta per progetto, preservando il parallelismo interno necessario ai reviewer.
- **Un solo esecutore per richiesta.** Riutilizzare coda persistente, identificatori e claim atomico esistenti. Lo stato della richiesta distingue presa in carico e chiusura; quello della run resta autorevole per l'analisi. Aggiungere solo i dati necessari a distinguere esito, motore e sessione. In modalità app il coordinatore possiede la coda: i tool legacy di presa/chiusura da host devono rifiutare una gestione concorrente. La modalità plugin attuale resta esplicita e separata.
- **MCP condivide le operazioni.** L'adattatore MCP della modalità app inoltra al servizio avviato, che possiede esecuzione e stato. Il suo processo stdio non avvia un secondo coordinatore; se l'app non è disponibile restituisce un errore esplicito. La connessione può terminare senza fermare l'app o il lavoro già accettato.
- **Un contratto piccolo per tre motori.** Eseguire un incarico con contesto, strumenti consentiti, eventi e segnale di annullamento; restituire esito, sessione e riferimenti agli artefatti. Errori di trasporto restano dell'adattatore, regole del workflow dell'applicazione. Non simulare capacità che un motore non offre.
- **Sessioni locali.** Claude Code e Codex usano le rispettive autenticazioni locali e identificatori di sessione. Nuova sessione e ripresa sono operazioni esplicite. I reviewer mantengono l'isolamento previsto dal metodo; non ereditano una conversazione personale per caso. Collegarsi a una sessione già attiva non è una ripresa ordinaria e resta fuori dal primo rilascio.
- **API compatibili OpenAI.** Configurare endpoint, modello e credenziale. Il primo protocollo è Chat Completions, con una prova di capacità per chiamate agli strumenti e streaming; Responses si aggiunge quando un endpoint concreto lo richiede. Il relativo adattatore ospita il ciclo richiesta al modello, esecuzione degli strumenti Daodan e ritorno dei risultati. Il coordinatore mantiene lo stesso metodo di analisi/review usato con i CLI. Credenziali nel backend, tramite ambiente o portachiavi del sistema; mai negli artefatti del progetto o nei log.
- **Workflow e report unici.** La pipeline deterministica resta proprietaria del grafo; i motori svolgono i compiti di ragionamento. Le istruzioni Markdown dei ruoli restano riusabili, con caricamento e strumenti adattati al motore. Il coordinatore deve preservare auditor, verifiche e isolamento di senior-review; il generatore HTML esistente rende gli stessi finding consolidati. Non sostituire il metodo con una generica richiesta di review al modello.
- **Errori e ciclo di vita espliciti.** Timeout e annullamento arrivano ai processi figli, con chiusura e raccolta dell'esito prima di dichiarare il lavoro fermo. Mai mantenere il lock del progetto durante attese LLM. Al riavvio una richiesta rimasta presa diventa interrotta, da riconciliare con processo/sessione prima della ripresa: non rilanciarla automaticamente. Conservare output parziali come tali e mantenere i controlli di pubblicazione canonici.
- **Avvio locale.** Il launcher avvia il server; il contesto del progetto si crea dalla selezione GitHub nella UI. Porta e cartella di lavoro sono configurazioni del launcher. Riutilizzare binding a loopback, token, controlli Host/Origin e allowlist degli asset. La UI deriva dal mockup business SmoothUI, con asset compilati locali. Non cambiare framework HTTP per ottenere soltanto un nuovo entry point.

## Servizio sul PC, codice del progetto in Kiri

**Decisione** del proprietario, 19 novembre 2026. Il servizio resta un processo sul PC, come oggi `daodan app`: server Python, store SQLite, checkout e motori (`engines`). In Kiri gira solo il codice del progetto analizzato, in container che Daodan avvia da solo (`find_engine`). Gli harness si usano in due modi: il servizio avvia Claude Code o Codex con il login dell'utente, oppure l'utente chiede analisi e review dalla sua sessione attraverso l'MCP. Scartato il servizio dentro Kiri: chiedeva MCP via HTTP, segreti fuori dal portachiavi, inoltro della porta e un ponte verso ogni strumento del PC, senza rendere l'utente più sicuro.

Proposte:

- **Una cartella applicativa.** Tutto in una cartella portabile, come Shinatama e Muro: l'app Tauri, un Python privato con il nucleo, `muroctl` e `mukade`. Anche Kiri e la base Alpine della distribuzione possono starci: oggi sono 51 MB scaricati al primo uso (47,4 il pacchetto di Kiri 0.2.0 per x64, 3,7 Alpine). Resterebbero da scaricare solo le immagini dei container.
- **Piattaforme.** Ora: app desktop su Windows, pagina web su Linux con `daodan app` e il Docker o Podman dell'utente. Poi: guscio desktop su Linux. Un'app Android non può ospitare server e container: sarebbe un client di un server remoto, che è fuori dal primo rilascio.
- **Daodan UI, app Tauri a sé stante, stile Shinatama.** L'app porta la sua pagina, avvia il server Python come processo in background, ne aspetta la risposta, lo ferma alla chiusura e gli parla solo attraverso l'API HTTP locale, con il token. Scartato l'IPC come trasporto: sarebbe un secondo canale accanto all'HTTP che il browser chiede comunque, e un servizio web futuro riusa il contratto HTTP senza toccare la UI. La sua origine non è quella del server, che la accetta per nome: oggi `visual.make_server` rifiuta ogni origine che non sia la sua e nessuna risposta ne ammette altre. Da Shinatama riusa il vetro (finestra trasparente con effetto `acrylic`, look Smooth) e il recupero della WebView (`webview_recovery.rs`): una finestra non resta mai vuota. Lo stesso sorgente della pagina resta servito dal server per il browser, con il fondo opaco. L'app desktop esce solo per Windows.
- **Motori configurati nell'app.** Gli harness collegati con Muro oppure un'API compatibile OpenAI, con endpoint, modello e chiave inseriti nella pagina.
- **Segreti con `keyring`, il resto in SQLite.** Chiave dell'API e token GitHub passano dalla libreria Python `keyring`, nel servizio: usa il deposito del sistema (Gestione credenziali su Windows, Secret Service o KWallet su Linux), che li cifra con l'account dell'utente. Motore scelto, endpoint e modello stanno nello store SQLite con run, risultati e log, non cifrati: non sono segreti, e il checkout accanto è leggibile comunque. Ogni parte viene dalla prima fonte che la nomina: le variabili d'ambiente di Daodan (`DAODAN_ENGINE`, `DAODAN_OPENAI_*`), poi ciò che l'utente ha salvato, poi `OPENAI_API_KEY`, che è generica e non scavalca una chiave salvata per un altro endpoint. La chiave si rimuove dalla pagina. Un deposito o un file che non si legge o non si scrive è una causa detta nella pagina, mai un avvio fallito: senza deposito la chiave resta in memoria per la sessione.
- **Un clic per collegare un harness.** Il servizio elenca gli harness del PC con la scoperta di Mukade (`muroctl request discover`) e installa su quelli scelti il plugin di Daodan con Muro (`save_plugin`, `resolve`, `plan`, `apply`). Riusa i loro adattatori: Daodan non scrive configurazioni di harness. `muroctl` è uno strumento in più lanciato sull'host, con il suo test come chiede la regola invalicabile.

Lacune:

- **Kiri nella cartella.** La licenza di Kiri deve permettere di ridistribuirlo [da verificare]. `pasta` oggi si installa nella distribuzione dalla rete: per un primo avvio senza altri download va messo in una base già pronta. Il peso su disco dopo l'estrazione è [da misurare].
- **Muro.** `plan` copre tutta la lista di Muro: con quella dell'utente il clic applicherebbe anche modifiche estranee a Daodan; una lista propria con `--data` lo evita [da verificare].
- **Persistenza.** Fatto per il motore (`engines.kept`, `engines.recalled`): la scelta sta in `settings.sqlite` nella cartella di lavoro, la chiave nel deposito. Una sola voce nel deposito: cambiando endpoint senza ridare la chiave, la stessa chiave lo segue. Con il deposito bloccato una chiave nuova resta in memoria e al riavvio torna quella già depositata. Su Linux senza desktop un portachiavi chiuso può fermare l'avvio in attesa dello sblocco [da verificare]. Il token GitHub non ha ancora codice. Per un server Linux senza deposito, il file cifrato con password di `keyrings.cryptfile`, pacchetto di terzi, è [da valutare]. `keyrings.alt` non si installa: porta un deposito non cifrato che `keyring` può scegliere da solo.

## Verifica

La superficie principale è l'API locale osservata da un client, precedente già presente nei test del server visuale. Il benchmark `standalone-app` mette alla prova il riuso attuale: import senza SDK MCP, bootstrap HTTP indipendente, protezione delle rotte, invio e lettura di richieste, claim concorrente senza presa in carico duplicata, rilascio e chiusura. Usa un progetto temporaneo e non avvia modelli o analisi del repository.

La futura implementazione deve provare sullo stesso ingresso un intero lavoro con un motore controllato: eventi, completamento, errore, timeout, annullamento e riavvio. Ogni adattatore reale richiede poi uno smoke test esplicito nel proprio ambiente. Il benchmark attuale non dimostra esecuzione LLM, cancellazione di processi o compatibilità di un provider API.

Per la UI verificare ingresso con un solo URL senza scelta di visibilità, accesso pubblico senza login, login condizionale e riprova dello stesso URL, accesso ancora negato e rete, scelta branch e default `main`/`master`/default remoto, invalidazione al cambio e reload. Coprire cambi URL A→B→A durante verifica/login, logout privato e migrazione dello stato precedente. Seguire poi pre-mappa, avvio senza obiettivo o dialogo testuale, crescita del grafo, pausa/ripresa e sintesi finale, oltre ad alberi e ricerca. La review deve accettare l'obiettivo vuoto e distinguere il perimetro storico da quello non ancora calcolato per un nuovo testo. Il benchmark registra viewport, eventi simulati, risultati e limiti: non sostituisce login, checkout o analisi collegati al backend.

## Fuori ambito

In questo passo: backend completo, modifica della pipeline, collegamento produttivo del mockup, distribuzione installabile e migrazione massiva dei plugin. Nel primo rilascio: hosting remoto, multiutenza, scheduler distribuito, controllo di sessioni personali già attive e portabilità automatica della cronologia fra motori.

## Note

La spec della pipeline rimane autorevole per step, analyzer e listener; questa proposta aggiunge gestione applicativa senza ridisegnarli. Il benchmark pubblica nel proprio README parametri e risultati misurati. I successivi tagli verticali vanno concordati dopo questa definizione dei confini.
