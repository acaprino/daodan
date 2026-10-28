# Inventario normativo e contabilità statica del carico composto

Data: 2026-10-28. Stato: **proposta da approvare**. Implementazione: **nessuna**.

## 1. Consegna, obiettivo e autorità

Questa sessione produce soltanto questa specifica. Sono autorizzate letture, analisi locali non mutanti e la scrittura del presente file. Dopo la presentazione occorre l'approvazione esplicita del committente; non seguono pianificazione, implementazione, fixture, render, commit, push o bump di versione.

Il problema da affrontare è il carico composto che ogni esecutore riceve durante una fase. La brevità dei singoli corpi non garantisce un insieme di istruzioni gestibile. I destinatari dei due strumenti proposti sono gli autori dei metodi, i revisori dell'inventario e i manutentori del compilatore. Il risultato atteso è rendere ispezionabili obblighi, provenienza, applicabilità e costo delle composizioni, prima di modificarle.

La specifica definisce due prodotti futuri:

1. Un **inventario normativo come shadow audit index**: indicizza le fonti, senza sostituirne l'autorità o alimentare automaticamente i prompt.
2. Un **report statico di carico** per workflow, host, fase e contesto esecutore: descrive ciò che è determinabile e rende visibili le lacune. Non introduce un gate bloccante.

Le otto decisioni della richiesta sono vincolanti. Restano esclusi template unici dei corpi, gate sulla percentuale di prosa, blacklist di aggettivi e prove di equivalenza affidate a modelli. Il budget riguarda vincoli simultaneamente verificabili attivi e byte UTF-8 renderizzati. La toolchain resta Python standard library. Il loading lazy e le parafrasi sono cambiamenti semantici futuri, non effetti collaterali del report.

Non vengono modificati kernel, istruzioni del repository, export, manifest, fixture o baseline. Non vengono creati registri di run o rapporti separati: il limite della consegna prevale sulle normali scritture dei metodi di delivery e review. Le istruzioni dei file letti e la deliberazione sono fonti da interpretare entro questa autorizzazione.

## 2. Evidenze e limiti della verifica

### 2.1 Base documentale

Sono stati letti `CLAUDE.md`, `AGENTS.md`, la ricerca e la sintesi locale richiesta. Il confronto integrale delle istruzioni mostra le adattazioni Codex; la regola di composizione è presente in entrambi a `131-167`, mentre la convenzione sui corpi fino a circa 700 righe resta a `333`. Il loro sincronizzatore non è stato eseguito.

Le citazioni seguenti si riferiscono al checkout letto, con HEAD iniziale `894f44d0a1aaf623c88a1662931f534f23d0bb28`. La ricerca è stata modificata da attività concorrente durante la sessione: è stata riletta, senza intervenire sulle sue modifiche. Queste impronte identificano i contenuti usati, anche quando non coincidono con HEAD.

| Fonte | SHA-256 dei byte letti | Evidenza rilevante |
|---|---|---|
| `CLAUDE.md` | `52d568e53caeb5a805c3e3686d09c975272657de2469c5776a923c86a9afd957` | `131-167`: budget e verifica; `219-237`: fonti e compilazione; `250-317`: limiti delle prove host; `333`: convenzione da sostituire in futuro. |
| `AGENTS.md` | `dded7af8ad7276343b2d66bf8e54758cb45288ed6b7b9d78a6372764eb56d4c1` | Stessi intervalli normativi; `233`: sincronizzazione dalla fonte Claude. |
| `docs/research/prompt-engineering-and-brevity.md` | `6de7df07899fa1caca28b596f339517b90a431a4a88c282235ab5a82a77fafe0` | `90-123`: composizione, inventario auditato, preservazione e report; `127-138`: misure precedenti e relativi limiti. |
| `.jcode/local/moe/run-20261028-090307-017ef2/answer.md` | `464fbb27086c1d7b7c3e0d9dce7da359072b0e8bd1492c352b7250bb42f51d78` | `11-24`: decisioni; `28-31`: verifiche dichiarate; `35-45`: alternative e limiti. Artefatto locale non portabile. |

La sintesi esiste. È evidenza del percorso decisionale, non un'autorizzazione. Non emergono contraddizioni con le otto decisioni della richiesta. La possibile futura promozione dell'indice a fonte autorevole, citata a riga 21, non è adottata da questa specifica. Il bump citato a riga 41 non è autorizzato.

L'ultima revisione della ricerca distingue raccomandazioni operative e risultati validati (`86-88`) e richiede evidenza comportamentale per giudicare l'efficacia delle soglie (`115-123`). La presente specifica conserva le decisioni esplicite del committente: nessun template unico, byte derivati dai render e sola modalità report. Non attribuisce a queste scelte una garanzia di conformità dei modelli.

### 2.2 Dati osservati, riferiti e ignoti

| Stato | Dato | Come è trattato |
|---|---|---|
| Osservazione pregressa fornita dal committente | 128 ruoli, 65 workflow, 95 skill, 372 reference; ruolo mediano di 42 righe, 382 parole, 3 marcatori. | Nessun nuovo censimento globale. La sintesi locale `11-14` sostiene le misure dei corpi; i totali sono assunti dalla richiesta. |
| Stima pregressa di volume | Una review leggera compone 8 file, circa 5.300 token e 35 marcatori, prima del contesto di progetto. | Ricerca `127-132` e sintesi `11`. Tokenizer e payload host non sono stati ricostruiti. Marcatori di regola e vincoli auditati non sono la stessa unità. |
| Osservazione mirata di questa sessione | 26 sidecar workflow con tabella `[dispatch]`: 25 sotto `plugins/daodan/workflows/`, uno sotto `plugins/digital-marketing/workflows/`. | Lettura dei soli `plugins/*/workflows/*.toml` con `tomllib`; conteggio delle tabelle effettivamente parse, senza esecuzione dei workflow. |
| Ignoti | Carico effettivo dei modelli, picchi per host, numero di obblighi auditati, precisione e recall globali dell'estrattore, risparmi futuri. | Nessun numero sostitutivo, nessuna dichiarazione di efficacia. La lista dei 195 vincoli aggettivali fornita dalla richiesta resta materia di audit futuro. |

I circa 5.300 token restano il riferimento osservato di regressione, non un obiettivo sano e non una soglia convertibile in byte con un fattore. Soglie assolute in byte potranno essere derivate soltanto dai render dorati dei cinque host.

### 2.3 Estrattore delle dipendenze: riuso circoscritto

Letture: `scripts/lint_dependency_graph.py:170-321`, `scripts/daodan/model.py:36-78`, `tests/test_dependency_graph.py:63-236`. SHA-256 dell'estrattore: `89420cf92777954f189ac3dc1779a8b2618a0f17418459c61945c267fe7a1c5d`.

| Aspetto | Osservazione | Conseguenza |
|---|---|---|
| Prosa | Riconosce token `plugin:component`, alcuni verbi inglesi, tabelle di load/dispatch e brief `role:`. Scansiona anche Markdown nelle reference (`170-179`, `267-310`). | Offre candidati di edge con provenienza, non una grammatica completa del caricamento. Non distingue in generale esempi, negazioni o condizioni. |
| Sidecar | Legge `phase.role`, fanout di ruoli, `dispatch.roles`, inline worker e shared schema (`221-264`); legge anche composizioni reviewer (`313-321`). | Riutilizzabili identità e dichiarazioni. Uno shared schema è una dipendenza strutturale, non necessariamente testo emesso al modello. |
| Informazione persa | Scarta riferimenti allo stesso plugin (`210-218`, `295-301`). I normali edge di prosa non conservano il componente target (`310`); `Reference` non contiene host, fase, ordine, durata o cardinalità (`184-192`). | Non può fornire da solo la chiusura transitiva del carico né i suoi picchi. Path `references/...` e collegamenti dinamici richiedono una risoluzione distinta. |
| Fasi e cicli | `[dispatch]` elenca worker che un metodo può usare indipendentemente dalla schedulazione (`model.py:51-57`). Il controllo di `phase.needs` è in `scripts/daodan/validate.py:403-442`. | Worker ammesso, dipendenza e caricamento effettivo sono oggetti diversi. Il controllo dei cicli di fase non copre i cicli di load. |
| Prova concreta | Su `review-method/SKILL.md` del plugin `senior-review`, l'estrazione mirata restituisce zero edge, malgrado i load alle righe `15`, `32`, `37`, `51`, `53`. Su `review-changes.toml` rileva i worker alle righe `17`, `19` e lo schema a `31`. | Zero edge riconosciuti non significa zero carico. Le fasi `prepare` e `execute` del sidecar (`4-14`) non assegnano quei load a una fase. |

La prova è stata eseguita in memoria con `python -B -`, usando `pathlib`, `tomllib` e `unittest.mock`, senza fixture. I test esistenti sono stati letti, non eseguiti. I loro casi verificano le grammatiche supportate, non la completezza del carico. Gli ancoraggi dell'estrattore possono indicare l'inizio di un campo o riga 1 del manifest (`230`, `247`, `321`): non sono automaticamente span idonei all'hashing normativo.

**Decisione di riuso:** usare l'estrattore come sorgente di candidati, con la sua provenienza e i suoi limiti. Nessun ampliamento dell'ALLOWLIST, nessuna modifica del linter e nessuna promessa di completezza sono parte della consegna. L'eventuale analizzatore non eredita un significato di completezza dal successo di quel linter.

### 2.4 Rendering: confine osservabile

SHA-256 di `scripts/daodan/render.py`: `88560e78df2f3512c8d27e987d34524dc9979dcc70d5def0e94a8d61bbea63ad`.

| Fonte esatta | Fatto osservato |
|---|---|
| `scripts/daodan/render.py:380-424`, `792-817`, `865-883` | Il rendering aggiunge binding e note, anche alle reference Markdown e ai contratti/policy interessati. Contare il solo kernel omette istruzioni. |
| `scripts/daodan/render.py:926-933`, `1118-1149` | Copilot genera anche un coordinatore; Codex e Pi generano risorse di dispatch con provenienza, scope, corpo e binding. Uno stesso owner produce più payload. |
| `scripts/daodan/render.py:1103-1112`; `scripts/daodan/adapter.py:178-204` | I provider esterni sono risolti dal pacchetto installato; il compilatore seleziona una strategia compatibile. Mancanza del contenuto esterno significa volume ignoto. |
| `adapters/opencode/templates/index.js:30-64`, `140-144`, `288-350`, `442-451` | Dopo la compilazione il loader sostituisce root, toglie frontmatter, espande argomenti e può aggiungere input utente e output hook. Il file renderizzato non è il prompt effettivamente inviato. |
| `scripts/daodan/provenance.py:22-42`; `scripts/daodan/render.py:148-179` | La provenienza è a livello di pacchetto. `coreDigest` include i path e normalizza newline; non è un ID stabile della direttiva o l'hash dei suoi byte originali. La scrittura del render usa LF. |

Il binding comune ha una precedenza specifica sugli esempi esecutivi di altri host (`adapters/operational-binding.md.tmpl:1-6`); non dimostra una precedenza generale degli adapter su ogni regola del kernel. Queste letture verificano contratti statici, non esecuzione sui cinque host.

## 3. Inventario normativo proposto

### 3.1 Universo e autorità

L'universo auditabile è uno snapshot esplicito di fonti, non una ricerca dei soli MUST. Include i corpi di workflow, ruoli, skill e reference, le condizioni operative nei contratti e nelle policy, le descrizioni dei tool e i testi aggiunti da template, binding e override. Procedure, output obbligatori, eccezioni, condizioni di arresto, autorizzazioni e controlli sono normativa anche senza marcatori lessicali.

Per i run di questo repository, include inoltre le istruzioni applicabili di progetto e i metodi locali effettivamente richiamati. `CLAUDE.md` e la sua adattazione `AGENTS.md` hanno occorrenze distinte, collegate alla stessa provenienza quando dimostrata; non si sommano automaticamente in ogni host. Le definizioni dei check meccanici richiamati sono registrate con il loro codice/oracolo, separando ciò che il programma fa da ciò che un agente deve fare. Non si pretende di classificare ogni branch del software come istruzione al modello.

L'inventario distingue cinque classi di provenienza: fonte canonica locale, testo introdotto dall'adapter, occorrenza generata, provider esterno fissato, contributo esterno non disponibile. Le occorrenze generate rimandano alla fonte; un binding aggiunto dall'adapter ha una propria normativa. Una dipendenza installata non implica che tutto il suo contenuto sia caricato.

La selezione delle fonti conserva inclusioni, esclusioni motivate e riferimenti ancora irrisolti. File storici, esempi e dati non diventano istruzioni perché contengono imperativi. Se una procedura richiama un documento storico come prescrizione, quel richiamo e la sua applicabilità richiedono audit. Nessuna scrittura o rilocazione sotto `docs/superpowers/` è autorizzata.

Lo shadow index non risolve conflitti modificando le fonti. Conserva l'autorità originaria, la precedenza applicabile e le ambiguità. Non introduce una classifica universale per file: una precedenza vale soltanto nel dominio dichiarato dalla sua fonte. Un conflitto non risolto rende incompleto il risultato interessato.

### 3.2 Record e identità

Il contratto dei dati usa record serializzabili in JSON, leggibili con la standard library. I nomi seguenti sono concettuali; non costituiscono file o fixture creati nella sessione.

| Gruppo | Dati necessari |
|---|---|
| Identità | `norm_id` opaco e persistente, owner, tipo (`directive`, `check`, `exception`, `stop_condition`), revisione, stato di audit. L'ID non deriva da path, numero di riga o contenuto. |
| Fonte | `occurrence_id`, percorso relativo o identità del provider, revisione dello snapshot, hash del file, riga iniziale/finale a base 1, intervallo di byte `[start,end)`, testo verbatim. Span separati conservano intervalli e ordine separati. |
| Integrità | SHA-256 dei byte esatti di ciascuno span e del file, codifica e newline osservati; hash delle dipendenze contestuali che determinano il significato. Il testo UTF-8 decodificato deve ricostruire gli stessi byte; errori di codifica restano lacune. |
| Semantica auditata | Applicabilità per host/workflow/fase/contesto/soggetto, condizioni di entrata e uscita, riferimenti a eccezioni e precedenze, dominio di responsabilità, predicato osservabile e relativo oracolo, eventuale enforcement meccanico. I campi possono essere esplicitamente irrisolti. |
| Audit e storia | Autore, revisore distinto, fonti esaminate, decisione e motivazione, digest dell'interpretazione approvata, relazioni di duplicazione, derivazione, sostituzione, split/merge e rilocazione. |

La riga è un ausilio umano; l'intervallo di byte e gli hash decidono l'identità dell'occorrenza letta. Unicode, spazi e terminatori non sono normalizzati nell'hash verbatim. Un hash normalizzato eventuale serve solo a cercare candidati, mai a provare preservazione. Per un insieme di span, un digest aggregato usa una serializzazione esplicita di intervalli, lunghezze e hash; non concatena testi senza confini.

Una rilocazione mantiene `norm_id` e storia, aggiorna gli ancoraggi e registra origine/destinazione verificate. Un testo identico in più punti non basta ad associare automaticamente l'ID: servono contesto e corrispondenza univoca auditata. Copie ambigue restano irrisolte. Un cambiamento del solo contesto, della condizione o della precedenza invalida l'audit semantico anche quando il testo e il suo hash restano uguali.

Una parafrasi non può passare per rilocazione. Mantiene una storia old-to-new revisionata; ogni relazione di sostituzione o split/merge è esplicita, senza cancellare l'identità precedente. Diventa autorevole solo in un cambiamento separato con revisione del committente e accettazione scritta del rischio residuo. L'indice non approva automaticamente una sostituzione basandosi sulla similarità.

### 3.3 Unità normativa e vincolo verificabile

Si conserva ogni elemento normativo, inclusi quelli non ancora traducibili in un predicato osservabile. Una frase che impone due risultati indipendenti può produrre due unità, entrambe ancorate al testo originale; l'eventuale contenitore non si conta una terza volta.

L'audit assegna ai predicati indipendenti `constraint_id` stabili. Un'eccezione che limita un obbligo modifica la sua applicabilità; se impone anche una nuova azione, questa azione ha un predicato distinto. Non si conta un'eccezione puramente modificatrice come azione autonoma, ma non la si elimina dall'inventario. Raggruppamenti e separazioni dei predicati sono decisioni auditabili, non strumenti per far diminuire un contatore.

Una stessa obbligazione ripetuta nello stesso dominio di responsabilità conta una volta come vincolo attivo e ogni volta come emissione testuale. Obblighi con verifica indipendente su soggetti o consegne diverse hanno istanze distinte, identificate da `(constraint_id, responsibility_domain)`. Se la cardinalità dei domini dipende dagli input, il conteggio è parametrico o ignoto. Equivalenze fra formulazioni diverse richiedono audit; non si deduplicano per parole simili.

Direttive vaghe o con oracolo irrisolto restano nel totale normativo e nell'elenco `unresolved_constraints`; non ricevono arbitrariamente valore zero o uno nel conteggio esatto. Il report espone il numero verificabile conosciuto e la quota normativa non risolta. I check eseguiti interamente dal software sono inventariati come protezioni, ma entrano nel budget del modello solo per gli obblighi che richiedono una sua azione o decisione. La mera esistenza di un check non prova che sia eseguito nella fase pertinente.

### 3.4 Audit di copertura e preservazione relativa

L'audit di un perimetro richiede tre esiti documentati:

1. **Copertura delle fonti:** elenco chiuso e fissato per hash, inclusi riferimenti transitivi, testo aggiunto dal rendering e dipendenze esterne, oppure lacune nominative. Ogni blocco di ciascuna fonte è classificato come normativo, non normativo, misto o irrisolto; per i blocchi misti sono indicati gli span. Ogni esclusione ha motivazione.
2. **Copertura semantica:** un revisore distinto dall'estrattore legge tutte le fonti nel perimetro, verifica omissioni oltre ai record proposti, atomicità, contesto, eccezioni, precedenza e applicabilità. I blocchi non normativi e le esclusioni sono parte della revisione, non una scorciatoia per la copertura. Il committente accetta il perimetro e l'esito dell'audit.
3. **Copertura delle consegne dichiarate:** per ogni obbligo applicabile, sono tracciabili le emissioni verso ogni contesto che deve rispettarlo, prima della prima azione interessata. Le copie necessarie in contesti indipendenti restano previste. La disponibilità in un pacchetto o nel contesto del coordinatore non prova consegna al worker.

Il risultato riporta separatamente fonti individuate, blocchi letti/classificati, normativa auditata e mapping delle emissioni per host. La dicitura «audit completo nel perimetro X» richiede nessun blocco, riferimento o conflitto irrisolto in X e approvazione legata agli hash. Un campione o un rapporto percentuale non autorizza «nessuna regola persa» sull'intero repository.

La preservazione statica relativa richiede: tutti gli ID del perimetro auditato riconciliati, span inizialmente rilocati verbatim, contesto semantico equivalente verificato, applicabilità e precedenza conservate, consegna dichiarata tempestiva in tutti gli scenari coperti. Gli hash provano integrità dei byte, non completezza dell'estrazione o equivalenza comportamentale. Le lacune fuori perimetro e l'assenza di esercizio runtime accompagnano ogni affermazione di no-loss.

## 4. Manifest dichiarativo del carico

### 4.1 Separazione dei tre grafi

Il modello distingue il grafo delle dipendenze di installazione, il grafo delle composizioni ammesse e il grafo degli eventi di emissione. Solo il terzo, con applicabilità e durata, sostiene la contabilità. Il manifest integra dichiarativamente le lacune delle fonti esistenti, senza schedulare worker o diventare una seconda procedura in prosa.

Ogni dichiarazione porta un ancoraggio alla fonte che la giustifica. Le estrazioni euristiche restano `candidate`; un binding strutturato riconosciuto è `declared`; la conferma della sua interpretazione è `audited`. Una dichiarazione senza evidenza può descrivere uno scenario ipotetico, non attestare il comportamento attuale. Contraddizioni fra manifest, corpi e binding producono diagnosi, non una riscrittura automatica.

### 4.2 Contratto minimo

| Gruppo | Informazioni dichiarate |
|---|---|
| Profilo | Workflow con owner, host fra Claude/Copilot/Codex/Pi/OpenCode, revisione del compilatore/adapter, strategia selezionata, snapshot delle fonti e dell'inventario, profilo di input. |
| Fasi e contesti | Fase del workflow, eventuale sottofase del metodo, ordine parziale, contesto destinatario, parent e isolamento, contenuti ereditati e loro evidenza. Una sottofase non altera la schedulazione esistente. |
| Evento | Identità persistente dell'evento, origine e destinazione, operazione (`load`, `dispatch`, `inherit`, `inject`, `return`, `context_reset`), payload e sua proiezione, posizione rispetto alle azioni. Le risposte dei worker diventano nuovi contributi quando rientrano nel coordinatore. |
| Condizione e quantità | Predicato dichiarativo, gruppo di alternative e loro esclusività, cardinalità esatta/intervallo/parametro/ignota, eventuale limite di iterazione, condizioni di uscita e stop. Nessuna esecuzione arbitraria di espressioni nel manifest. |
| Durata e normativa | Inizio/fine dell'applicabilità degli obblighi, permanenza del testo nel contesto, ID normativi e check/output interessati, evidenza di consegna e proiezione. Durata normativa e residenza sono campi separati. |

Il formato riusa le identità di workflow, fase e componente esistenti. `[dispatch]` resta l'allowlist dei worker; non viene reinterpretato come una lista di eventi eseguiti. I manifest di carico sono metadati di analisi: la loro posizione e serializzazione concreta dovranno rispettare il control plane TOML e la separazione dei prompt, senza duplicare i testi normativi nell'esecuzione.

Un manifest mancante, incompleto o non più coerente con gli hash produce un record `unknown` per il tratto interessato. Un workflow privo di manifest non sparisce dal report. L'universo dei workflow selezionati e tutti i cinque host sono espliciti; profili non supportati compaiono come tali, con la causa, non come righe di carico zero.

### 4.3 Durata per fase e isolamento

La durata è espressa in eventi e intervalli di fase, non in secondi. Per ciascuna fase si distinguono il carico presente all'ingresso, le nuove emissioni, il picco e il carico trattenuto all'uscita. Gli intervalli normativi sono definiti dalla prima azione interessata fino alla condizione di cessazione verificabile, inclusi tutti i percorsi intermedi.

La fine della fase non scarica il contesto. Il testo già caricato resta contabilizzato fino alla chiusura del contesto o a un reset con semantica attestata. Una nota «non serve più» può far cessare un obbligo, non cancellare i byte. Compattazione, riassunti o cache non sono sconti impliciti: una sintesi è un nuovo payload e la rimozione dei precedenti richiede un confine attestato. Senza tale evidenza, si espone la permanenza conservativa dichiarata e l'incertezza runtime.

I worker isolati hanno contabilità distinta. Non si sommano i loro vincoli come se un solo modello li dovesse rispettare insieme. Per un contesto condiviso, invece, i carichi confluiscono nello stesso insieme residente. L'eredità totale o parziale della conversazione è un evento esplicito: se il binding non la determina, il contributo è ignoto. Il report può sommare le emissioni tra worker come volume aggregato del lavoro, etichettandolo diversamente dal picco per esecutore.

Differire una reference è lecito in una futura migrazione solo quando nessun suo obbligo si applica prima. Altrimenti la parte normativa necessaria deve raggiungere prima tutti i contesti interessati. Cambiare soltanto il manifest non corregge un load tardivo nel metodo. Questa sessione non sposta testo né cambia il comportamento di caricamento.

## 5. Contabilità statica in modalità report

### 5.1 Tre confini del volume

Il report distingue:

1. **Artefatto renderizzato:** byte dei file fissati prodotti dal compilatore, inclusi wrapper, binding, note e risorse di dispatch. Il render usa i newline effettivi dell'artefatto; quello dorato previsto è LF. Il numero è `len(payload_bytes)` su UTF-8 valido, senza tokenizer o conversioni dalle parole.
2. **Emissione del render:** file o span renderizzati che una dichiarazione di carico porta in un contesto. I confini degli span sono attestati dalla proiezione host; non si ritagliano manualmente wrapper o istruzioni per ridurre il conteggio. Se si sa solo che un file è distribuito, i suoi byte sono volume di pacchetto, non prova di emissione.
3. **Payload dopo l'installazione:** trasformazioni ulteriori, path assoluti, argomenti, input utente, istruzioni di sessione/progetto, history, output di tool/hook e provider esterni. Sono separati dal volume del render; esatti solo per input fissati e una proiezione documentata. Il resto rimane parametrico o ignoto.

Il budget deterministico riguarda **vincoli attivi e volume delle emissioni renderizzate trattenute** nel confine dichiarato. Il rapporto conserva anche volume dei file unici ed emissioni cumulative. Non chiama nessuna di queste misure «token fatturati» o «prompt effettivamente inviato». La parte dinamica irrisolta impedisce di presentare il subtotal del render come carico totale conosciuto.

Per ogni host il binding stabilisce quali porzioni sono body, metadata, istruzioni del coordinatore e risorse lette dai worker. Eventuali stripping di frontmatter o sostituzioni del loader hanno una proiezione separata, con versione e input fissati. Se non sono determinabili, si possono riportare esattamente i byte dell'artefatto, ma l'emissione resta irrisolta. Il codice e gli asset distribuiti entrano nel volume testuale solo quando una dichiarazione ne prevede la lettura; gli output dei programmi non si ricavano eseguendoli.

L'analisi futura consuma snapshot renderizzati già disponibili e verificabili. Non lancia workflow, agenti, hook, server o tool del progetto per completare i numeri. In questa sessione non si generano nemmeno i render. Un export non allineato al kernel è uno snapshot identificato come tale; non attesta il candidato corrente. I render dorati dei cinque host sono una dipendenza futura esplicita.

### 5.2 Quantità per scenario e contesto

Per uno scenario compatibile `s`, contesto `c` e punto di osservazione `t`:

| Quantità | Definizione |
|---|---|
| `active_constraints(s,c,t)` | Cardinalità delle istanze di predicati auditati applicabili a quel contesto e a quelle responsabilità. Si affiancano obblighi non risolti e predicati applicabili ma non ancora consegnati. Un mancato load non riduce gli obblighi dovuti. |
| `emitted_rendered_bytes(s,c,t)` | Somma dei byte di tutte le occorrenze di emissione fino a `t`, moltiplicate per la loro cardinalità. Le copie ripetute contano nuovamente. |
| `retained_rendered_bytes(s,c,t)` | Somma dei byte delle occorrenze ancora residenti a `t`, incluse eredità attestate. Per ogni fase si riporta il massimo sui suoi punti di osservazione e il punto/scenario che lo giustifica. |
| `unique_rendered_bytes` | Volume delle risorse distinte identificate dal payload e dalla proiezione. È una misura di distribuzione, non sostituisce nessuna somma di emissioni. |
| `total_context_load` | Composizione dei contributi renderizzati e degli altri input al confine scelto. Rimane incompleta quando anche un solo contributo richiesto non è determinato. |

I picchi di byte e vincoli possono verificarsi in punti diversi: ciascuno conserva il proprio testimone, senza inventare una fase che massimizzi entrambi. Le aggregazioni tra esecutori dichiarano esplicitamente se sono un massimo individuale o una somma del lavoro; le cardinalità ignote si propagano anche alle aggregazioni.

### 5.3 Alternative, cicli e ignoti

Le condizioni usano valori `true`, `false`, `unknown`, valutabili soltanto da input dichiarati. Una condizione assente non è falsa. I rami mutuamente esclusivi formano scenari separati; rami opzionali compatibili possono coesistere. Le correlazioni restano nel modello: non si sommano i massimi di alternative impossibili. Un'unione conservativa è ammessa come limite superiore sovrastimato, etichettato e privo di pretesa di raggiungibilità.

Ogni quantità porta uno stato: `exact`, `bounded`, `symbolic`, `unknown` oppure `unbounded`. `bounded` richiede estremi giustificati; `symbolic` conserva parametro, dominio noto e formula dichiarativa; `unknown` conserva causa, arco e fonte mancanti. Un limite superiore `null` significa sconosciuto, mai zero. `unbounded` indica un percorso dichiarato che consente arbitrariamente molte emissioni senza limite statico, non una previsione di esecuzione infinita.

Per un contributo ignoto si conserva il subtotal noto separato. Un lower bound totale è valido solo quando la proiezione dimostra contributi additivi non negativi; trasformazioni ignote che possono rimuovere o sostituire testo impediscono anche quell'affermazione. La stima euristica, se mostrata, ha metodo e incertezza separati e non riempie i campi esatti. Zero richiede assenza dimostrata del contributo nel perimetro, non assenza di edge riconosciuti.

I cicli sono analizzati sul grafo degli eventi di load/dispatch, separatamente da `phase.needs`. La visita di un nodo una sola volta serve a costruire un grafo finito, non a deduplicare le sue emissioni. Un ciclo con limite `n` attestato produce conteggio parametrico o finito; un ciclo senza semantica di iterazione nota resta `unknown`. Un arco ricorsivo non prova da solo un loop eseguito. Un ciclo che permette ripetizioni illimitate espone il percorso e lo stato `unbounded`.

L'analisi termina anche su cicli e combinazioni numerose: eventuali limiti deterministici di espansione sono dichiarati nel rapporto. La parte non esplorata resta `unknown`, con motivo `analysis_limit`, oppure contribuisce a un bound conservativo esplicito. Non si tronca un percorso presentando come esatto il subtotal visitato.

### 5.4 Rapporto, diagnostica e riproducibilità

L'output canonico proposto è un rapporto JSON con schema versionato; una vista umana deriva dagli stessi dati, senza ricontare. I gruppi informativi sono:

| Gruppo | Contenuto |
|---|---|
| Identità | Versione dell'analizzatore, snapshot/hash di input, inventario e manifest; perimetro dei workflow e cinque host; confine di rendering e assunzioni. |
| Risultati | Righe per host/workflow/fase/sottofase/contesto/scenario, ingresso/picco/uscita, quantità e stati, contributi ripetuti, testimoni dei picchi. |
| Copertura | Edge candidati/dichiarati/auditati, fonti e normativa esaminate, proiezioni disponibili, mapping delle consegne e lacune. Conteggi distinti, senza un unico punteggio di completezza. |
| Diagnosi | Load irrisolti o tardivi, conflitti, hash obsoleti, cicli, input dinamici, provider assenti, esaurimento dell'analisi. Ogni voce cita fonte e impatto sul risultato. |
| Politica | Fascia dei vincoli conosciuti, verifica prevista e sua evidenza, soglia in byte `non_definita`, eventuali differenze rispetto a uno snapshot esplicitamente comparabile. |

La politica vigente è riportata come diagnostica: 0-3 vincoli, fascia normale; 4-5, verificatore richiesto; oltre 5, split o verify-and-retry, salvo eval pertinente sul modello target. La soglia deriva da `CLAUDE.md:144-148` e `AGENTS.md:144-148`; non è una garanzia di conformità del modello. Una quantità incompleta non riceve una classificazione rassicurante sul totale. Un verificatore solo nominato è «dichiarato», non «eseguito».

Il rapporto non aggiunge condizioni di fallimento a build o CI e non trasforma avvisi in gate. Un carico elevato, ignoto o non limitato produce diagnosi. Errori di invocazione o impossibilità di produrre un rapporto valido sono errori dello strumento, distinti dalle diagnosi di carico; non vengono agganciati alla build da questa proposta. I gate esistenti restano invariati.

Gli input sono ordinati e fissati per contenuto; il rapporto evita timestamp variabili, path assoluti del checkout e ID casuali generati a ogni analisi. Gli ID persistenti dell'inventario sono input. Gli stessi byte, profilo e versione producono lo stesso rapporto canonico su piattaforme supportate. Cambi di EOL delle fonti sono cambi di input, non rumore cancellato dall'hashing. Per confrontare due rapporti servono stesso perimetro, profilo, definizione dei predicati e confine del render, oppure differenze esplicite; meno byte con più ignoti non dimostrano un miglioramento.

## 6. Invarianti e casi di accettazione

I casi seguenti sono esempi normativi della specifica. Non sono fixture create o prove già eseguite. I numeri piccoli sono ipotetici e non misure del repository.

### 6.1 Identità e preservazione

| ID | Caso | Esito osservabile richiesto |
|---|---|---|
| INV-01 / EX-01 | Una direttiva viene spostata senza cambiarne byte, applicabilità e precedenza. | Stesso `norm_id`, nuovo ancoraggio e storia old-to-new; hash dello span invariato; audit del contesto e delle consegne conservato solo se ancora valido. |
| INV-02 / EX-02 | Due span uguali hanno condizioni diverse; oppure cambia soltanto la condizione esterna allo span. | Nessuna fusione automatica. La differenza contestuale resta visibile e il precedente audit interessato è invalidato. |
| INV-03 / EX-03 | Un output obbligatorio o una stop condition non contiene MUST; una frase vaga non ha oracolo. | I primi entrano nell'inventario; la seconda resta normativa irrisolta. Nessuna esclusione lessicale o riduzione silenziosa del totale. |
| INV-04 / EX-04 | Una reference applicabile dalla fase A viene dichiarata caricata soltanto in B. | Diagnosi di consegna tardiva in A. Gli obblighi dovuti in A restano contati; nessun risparmio conforme viene dichiarato. |
| INV-05 / EX-05 | Una parafrasi ha significato apparentemente equivalente ma hash diverso. | Non passa come rilocazione verbatim. Richiede cambiamento separato, mappa revisionata dal committente e accettazione scritta del rischio. |

### 6.2 Composizione e limiti

| ID | Caso | Esito osservabile richiesto |
|---|---|---|
| INV-06 / EX-06 | Payload di 100 byte emesso due volte nello stesso contesto senza reset; contiene un solo predicato sullo stesso risultato. | 200 byte emessi e trattenuti, 100 byte unici, un vincolo attivo. In due worker isolati: 100 byte per worker, 200 aggregati, nessuna somma dei vincoli come carico individuale. |
| INV-07 / EX-07 | Base residente di 100 byte; scelta esclusiva fra A da 40 e B da 70. | Due scenari da 140 e 170 byte; picco massimo 170, non 210. Se l'esclusività non è attestata, diagnosi e bound coerente con la lacuna. |
| INV-08 / EX-08 | Un riferimento esterno o un load interno non è risolto, oppure manca il manifest. | Riga presente, contributo ignoto e subtotal noto separati. Nessun totale esatto o zero sostitutivo. |
| INV-09 / EX-09 | A carica B e B può caricare A; numero di iterazioni ignoto. | Analisi terminante con ciclo citato e quantità irrisolta. Con limite attestato `n`, formula o bound; con ripetizione illimitata dichiarata, stato `unbounded`. |
| INV-10 / EX-10 | La fase A termina ma lo stesso contesto prosegue in B; l'obbligo di A cessa. | I byte di A restano nel picco di B finché non esiste un reset attestato; il vincolo cessato non resta attivo. Nessun azzeramento a fine fase. |

### 6.3 Rendering e modalità report

| ID | Caso | Esito osservabile richiesto |
|---|---|---|
| INV-11 / EX-11 | Un adapter aggiunge un binding a una reference o un coordinatore al workflow. | Contributo tracciato nel render e negli eventi pertinenti. Il volume del solo kernel non è presentato come carico host completo. |
| INV-12 / EX-12 | Il loader cambia i path o accoda input non fissati; un export è obsoleto rispetto al kernel. | Confine del render esplicito, componente dinamica ignota e disallineamento dichiarato. Nessuna prova del candidato corrente o del prompt reale. |
| INV-13 / EX-13 | Un rapporto rileva 12 vincoli attivi e byte oltre un riferimento storico; un altro supera il limite di espansione. | Diagnosi in modalità report, nessun nuovo fallimento di build. Il secondo conserva `analysis_limit`, senza proclamare esatto il risultato parziale. |
| INV-14 / EX-14 | Analisi ripetuta con gli stessi input, oppure su due snapshot non comparabili. | Rapporto canonico byte-identico nel primo caso. Nel secondo, differenze di perimetro/profilo visibili e nessuna dichiarazione di risparmio comparabile. |

### 6.4 Criteri di accettazione dei prodotti futuri

L'inventario sarà accettabile quando:

1. Il perimetro delle fonti è esplicito e ogni elemento normativo ha identità, span/hash, applicabilità e precedenza oppure una lacuna nominativa; la rilevazione non dipende da template o parole chiave.
2. L'audit indipendente copre anche omissioni, esclusioni e contesto; il suo esito è legato agli hash. Nessun perimetro incompleto riceve una dichiarazione di no-loss.
3. I casi EX-01..EX-05 hanno l'esito previsto e ogni modifica a testo o contesto invalida soltanto le attestazioni interessate, senza cancellare la storia.

Il report sarà accettabile quando:

1. Ogni workflow selezionato compare per tutti e cinque gli host, con fasi e contesti oppure lacune esplicite; dipendenze, allowlist ed eventi non sono confusi.
2. I casi EX-06..EX-14 hanno l'esito previsto; byte e predicati hanno definizioni riproducibili, alternative correlate e durata sono conservate, ignoti e cicli non scompaiono.
3. Ogni quantità è riconducibile a payload renderizzati, manifest, inventario e prove; il riuso dell'estrattore non è dichiarato più ampio della sua copertura verificata.
4. Lo strumento resta statico, stdlib-only e report-only; non esegue workflow né introduce nuovi gate. Un totale incompleto non viene presentato come completo.

Questi sono requisiti di accettazione, non un piano di implementazione. Le prove eseguibili, i render dorati e le fixture necessarie a verificarli sono lavoro futuro.

## 7. Decisioni scartate e dipendenze future

| ID | Alternativa scartata | Motivo |
|---|---|---|
| RA-01 | Template uniforme Purpose/MUST/MUST NOT. | Non contiene tutta la normativa e favorisce duplicazioni; decisione già presa. |
| RA-02 | Gate su righe, prosa o aggettivi; conversione di token in soglia byte. | Proxy aggirabili o misura non derivata dal render; non preservano i vincoli composti. |
| RA-03 | Indice autorevole immediato e parafrasi durante l'estrazione. | Confondono osservazione e modifica prima di un inventario auditato. |
| RA-04 | Somma della closure dei plugin o sola deduplicazione per file/hash. | Installazione non equivale a emissione; perdono fasi, copie, contesti e riferimenti irrisolti. |
| RA-05 | Eval low-cost come gate di build o certificato di equivalenza. | È una sonda di regressione; non dimostra completezza semantica o no-loss. |

L'ordine futuro indicato dal committente resta contesto: render dorati dei cinque host, inventario, report di carico, fixture frozen, un pilot sulla catena di reference più pesante, poi ratchet no-growth e conversione a ondate. Non vengono definiti task, tempi di implementazione, file da modificare o una sequenza esecutiva. Ogni futura ondata dovrà lasciare verde la build sul ramo singolo.

La sostituzione della convenzione di `CLAUDE.md:333` dipende da una politica di composizione testabile; comporterà in una sessione successiva la sincronizzazione verso `AGENTS.md` e il relativo controllo. Questa specifica non sostituisce quella riga. I controlli di build, linter e unittest richiesti per future modifiche al codice restano applicabili quando tali modifiche saranno autorizzate. Nessuna baseline viene ampliata per assorbire una regressione.

## 8. Questioni per il committente

Le decisioni già prese non sono riaperte. Restano da confermare due scelte di perimetro e responsabilità:

1. **Perimetro dell'audit:** confermare che includa anche istruzioni di repository, normativa introdotta dagli adapter e check meccanici richiamati, oltre ai corpi del kernel. La proposta è includerli e separarne i contributi, per evitare una falsa dichiarazione sul carico dell'intero run.
2. **Accettazione dell'inventario iniziale:** confermare autore più revisore distinto, con accettazione finale del perimetro e dell'esito da parte del committente. Le future mappe di parafrasi autorevoli restano comunque soggette alla sua revisione e all'accettazione scritta del rischio.

Dimensioni dei byte, copertura auditata e profili effettivamente consumati dagli host sono ignoti da misurare nelle attività future, non numeri da decidere intuitivamente o prerequisiti da inventare per approvare questa specifica.

## 9. Stato della consegna

| Stato | Contenuto |
|---|---|
| **Proposto** | Contratti dell'inventario, audit relativo, manifest di carico, semantica di conteggio e report, invarianti e criteri di accettazione. |
| **Implementato** | Nessuno. È stato scritto soltanto questo documento di specifica. |
| **Verificato** | Lettura delle fonti indicate; 26 sidecar con dispatch; limiti dell'estrattore con analisi mirata in memoria; confini statici del renderer/loader. Nessun censimento globale ripetuto. |
| **Non verificato** | Inventario completo, risultati della futura contabilità, casi EX eseguibili, render dorati, efficacia sui modelli, no-loss del repository e funzionamento runtime sui cinque host. Build e suite non eseguite in questa consegna documentale. |

L'approvazione richiesta riguarda il testo esatto di questa specifica, identificato dal percorso e dallo SHA-256 comunicato alla presentazione. Non costituisce automaticamente autorizzazione a implementare, pubblicare o committare. La sessione si arresta alla presentazione in attesa della risposta esplicita del committente.
