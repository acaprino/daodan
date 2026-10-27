# Science-based Approach: specifica funzionale e tecnica

| Campo | Valore |
|---|---|
| Identità | `SPEC-SCIENCE-001`, revisione 3 |
| Stato | Implementazione locale; prove e limiti in [validazione](../validation.md) |
| Creazione | 2026-10-27T09:19:58+01:00, Europe/Rome |
| Ultimo aggiornamento | 2026-10-27T10:30:25+01:00, Europe/Rome |
| Proprietario | Plugin `research` |
| Origine | Specifica richiesta e successivo «ok procediamo»; lavoro nella checkout principale e documentazione aggiornata |

## 1. Obiettivo e confini

Fornire una base scientifica consultabile e aggiornabile per risolvere problemi,
confrontare algoritmi e tecnologie e motivare specifiche, ADR e FRD. La skill
`science-based-approach` cerca letteratura pertinente, legge le fonti accessibili,
collega le conclusioni alle evidenze e propone o registra verifiche locali.

**Science Mode è ON per impostazione predefinita.** Il controllo automatico
sceglie se riutilizzare una ricerca, aggiornarla o crearne una. Non richiede una
nuova ricerca online per ogni compito. Le conclusioni conservano condizioni,
incertezze, controevidenze e storia del loro eventuale superamento.

Questa specifica comprende comportamento, documenti, integrazioni e criteri di
accettazione. Non installa la skill, non abilita hook, non modifica la modalità
del progetto e non approva nuovi ADR/FRD. I nomi dei comandi descrivono l'interfaccia
da realizzare; non attestano che siano già disponibili.

Fuori perimetro: monitoraggio periodico senza una richiesta separata, crawler
generalista, abbonamenti obbligatori, raccolta indiscriminata di PDF e modifica
automatica del prodotto in conseguenza di un nuovo paper.

## 2. Decisioni raccolte e responsabilità

| Requisito concordato | Contratto |
|---|---|
| Ricerca scientifica mirata | Ricerca su indici accademici e siti primari scelti per disciplina; lettura verificabile |
| Memoria documentale | Indice in `docs/research/`, template uniforme, fonti, spiegazione concisa e test |
| Aggiornamento | Nuove versioni, correzioni, ritiri, risultati contrari e cambi tecnologici con cronologia |
| Attivazione automatica | Brainstorming, specifiche, ADR, FRD e problemi o scelte sostanziali |
| Controllo dell'utente | ON di default; ON/OFF persistente per progetto; richieste esplicite disponibili anche su OFF |

`research` possiede metodo, fonti, sintesi e manutenzione della ricerca.
`project-delivery` possiede i punti di integrazione, ADR e FRD; `project-knowledge`
possiede organizzazione documentale e istruzioni persistenti; `testing` possiede
le verifiche del prodotto. `work-controller` conserva le esecuzioni e le loro
consegne senza diventare dipendente da `research`.

La progettazione rispetta [ADR-0004](../../../adr/ADR-0004-adr-versions-and-drift.md):
approvazione del testo, verifica dell'implementazione e superamento di una
decisione sono operazioni distinte. Il riferimento FRD indica il documento dei
requisiti funzionali, anche quando nella richiesta è scritto «FDR».

Questa proposta richiede una revisione intenzionale del confine attuale di
`research`, che `CLAUDE.md` descrive come web-only e privo di dipendenze. I nuovi
metodo e comandi scientifici gestiscono archivio e preferenza locali; il vecchio
`team-research` e i suoi ricercatori mantengono il contratto web-only. La dipendenza
nuova prevista è `research -> work-controller`, per home e record; non si aggiunge
una dipendenza verso i consumer o verso `testing`. La regola di repository andrà
aggiornata insieme all'implementazione, rendendo espliciti questi due ambiti.

## 3. Interfaccia utente

La notazione seguente è l'identità logica; ciascun host espone l'entry point
tramite il proprio adattatore. L'argomento è testo libero, senza nuovi flag.

| Comando | Effetto e risultato |
|---|---|
| `/research:science-research <problema>` | Risolve il contesto, cerca ricerche pertinenti, legge fonti e pubblica una nuova ricerca o revisione motivata |
| `/research:update-research <tema o identità>` | Riesamina solo le ricerche selezionate e restituisce cambiamenti, limiti e documenti coinvolti |
| `/research:update-research tutte` | Prende uno snapshot dell'indice e controlla una volta ogni ricerca canonica, con esito distinto per ciascuna |
| `/research:science-mode on` / `off` | Persiste la preferenza, restituendo stato effettivo, progetto e origine della configurazione |
| `/research:science-mode` | Mostra stato, origine predefinita/esplicita/errore e copertura disponibile delle integrazioni; non scrive e non cerca online |

Un problema già chiaro non richiede un secondo questionario. Un selettore
ambiguo chiede una sola precisazione prima di aggiornare documenti; un selettore
inesistente non crea implicitamente una ricerca. `update-research` senza
argomento usa la ricerca esplicitamente collegata al compito corrente solo se
univoca; altrimenti chiede l'ambito. Un indice vuoto produce «nessuna ricerca da
aggiornare». Gli esiti parziali non sono riassunti come «tutto aggiornato».

`science-mode` accetta `on`, `off` o argomento vuoto. Un valore diverso restituisce
gli usi validi e non modifica lo stato. ON ripetuto su ON, o OFF su OFF, è idempotente.
Riattivare ON non avvia una revisione retroattiva dell'intero archivio.

## 4. Science Mode e persistenza

Il progetto condivide una sola preferenza fra sessioni, host e worktree.
La home è quella già risolta da Work Controller attraverso la directory Git
comune; fuori da Git è la root del progetto. Non cercare configurazioni in
directory antenate arbitrarie o nell'installazione globale del plugin.

La preferenza, i checkpoint e il lock usano tale home condivisa. I documenti
scientifici restano nella checkout del chiamante, entro il suo perimetro di
scrittura: il lavoro su un branch non pubblica documenti nella main.

Proposta di persistenza minima: `<project-home>/.daodan/science-mode.json`, con
`schema: daodan/science-mode/v1`, `enabled` booleano, `revision` intero,
`updated_at` ISO 8601 con offset e riferimento alla richiesta che ha cambiato
lo stato. L'helper di `research` usa il contratto della home esistente, senza
introdurre un secondo resolver incompatibile.

| Situazione | Comportamento richiesto |
|---|---|
| File assente | Stato ON implicito; la lettura non crea file |
| Configurazione valida | Usa il booleano persistito; OFF prevale sul valore predefinito |
| Configurazione corrotta o schema sconosciuto | Stato `configuration-error`; sospende l'automatismo, segnala il problema e conserva i byte |
| Scrittura non consentita o revisione concorrente | Nessun cambio dichiarato riuscito; rilettura e risultato esplicito, senza sovrascrivere modifiche altrui |
| OFF durante una ricerca automatica | Non avvia nuovi lavori automatici; ferma quelli posseduti al prossimo punto sicuro e conserva risultati parziali dichiarati |

Le scritture devono essere atomiche e controllare la revisione letta. Il passaggio
di stato è tracciato nel record dell'esecuzione. L'eventuale riparazione di una
configurazione corrotta non avviene silenziosamente tramite un valore di default.

OFF disabilita consultazione, nuova ricerca, aggiornamento e scritture avviati
automaticamente da questa funzionalità. Non cancella documenti né invalida le
citazioni già presenti; le ordinarie verifiche del workflow conservano i loro
obblighi. Un comando scientifico esplicito autorizza quella singola operazione
anche su OFF e non cambia la preferenza. Un problema nella configurazione non
impedisce tale invocazione esplicita, se progetto e autorizzazioni sono risolti.

## 5. Attivazione automatica e hook

Il punto di attivazione comune riceve contesto del compito, fase, intento,
documento/candidato interessato, versioni tecnologiche pertinenti e autorizzazioni.
Legge prima Science Mode. Non usa la sola presenza di parole come «paper» o «ADR»
come prova che sia iniziato un lavoro scientifico.

| Punto del flusso | Intervento prima della decisione |
|---|---|
| Brainstorming | Cerca conoscenza pertinente prima di confrontare le alternative |
| Specifica | Esamina le affermazioni tecniche e collega quelle verificabili ai criteri di accettazione |
| ADR proposto o revisione | Confronta evidenze, controevidenze e applicabilità delle alternative |
| FRD proposto o revisione | Separa bisogno dell'utente, ipotesi di prodotto, comportamento osservato ed evidenza scientifica |
| Problema, algoritmo, compito o revisione sostanziale | Valuta l'incertezza che può cambiare la soluzione; aggiorna il contesto se cambiano requisiti o tecnologia |

L'esito minimo è uno fra `disabled`, `not-applicable`, `reused`, `updated`,
`created`, `partial`, `unavailable`, `configuration-error`. Ogni esito ha una
ragione e riferimenti; un riuso non dichiara una nuova verifica online. Le modifiche
editoriali senza impatto semantico normalmente producono `not-applicable`.

Il controllo è deduplicato per progetto, compito, fase, versione della modalità e
impronta del contesto rilevante. Uno stesso evento nativo e del workflow converge
sulla stessa esecuzione. Cambi di ipotesi o vincoli richiedono rivalutazione; un
semplice salvataggio no. Scrivere ricerca, template, changelog o configurazione non
deve riattivare ricorsivamente il controllo. La modalità viene riletta prima di
nuove attività automatiche, anche alla ripresa di un'esecuzione.

L'aggancio riusa le autorizzazioni del compito: ON non concede permessi di scrittura
aggiuntivi. In una richiesta di sola lettura conserva eventuali risultati nel run
già autorizzato oppure li restituisce in chat; non pubblica in `docs/`. Per supportare
la pubblicazione durante brainstorming occorre aggiornare esplicitamente il suo
contratto attuale, che limita le scritture ai materiali del run e alle idee concordate.
Un compito che già autorizza la ricerca documentata non ripete la stessa richiesta
di consenso. I consumer compongono il metodo, senza lanciare comandi dentro altri
comandi o ripetere l'intervista del flusso chiamante.

**Due livelli distinti di integrazione:** gli agganci espliciti nei metodi Daodan
costituiscono il percorso comune; gli hook nativi aggiungono intercettazione degli
eventi nei soli host verificati. Un hook nativo raccoglie il contesto e consegna
il controllo al coordinatore con un meccanismo supportato: non avvia un secondo
coordinatore né una ricerca lunga dentro un callback soggetto a timeout.

Alla stesura della revisione 1, il compilatore distribuiva implementazioni eseguibili delle policy:
per esempio copia il guard di Codebase Map nel pacchetto Copilot. Quel guard è
esplicitamente `wired = false`, quindi non è registrato automaticamente come hook.
Mancava il percorso generale di dichiarazione neutrale e registrazione degli eventi
per i nuovi hook scientifici, non la possibilità di esportarne gli script.
L'implementazione aggiunge `[[hooks]]` neutri e genera `hooks/hooks.json` per
Claude e Codex, mentre per OpenCode adatta l'intercettazione nel proprio loader
eseguendo gli script Python sugli eventi di sessione e prompt. Copilot e Pi
mantengono i checkpoint dei metodi con fallback esplicito. Il [contratto tecnico](../technical-spec.md)
descrive il formato e i limiti.
I plugin esterni possono distribuire manifest hook propri, fuori dalla compilazione
Daodan. Le righe `hooks.lifecycle` degli adattatori sono evidenza dichiarativa,
non collaudi. La verifica distingue,
per Claude, Codex, Copilot, Pi e OpenCode, aggancio del workflow,
manifest/evento generato o adattato nel loader, installazione e prova eseguita. Un host senza
registrazione di hook conserva il percorso del workflow e dichiara il limite per gli usi
diretti esterni ai workflow. Non promettere intercettazione universale.

Evidenze locali: [copia delle policy nel renderer](../../../../scripts/daodan/render.py),
[contratto di confinamento](../../../../plugins/codebase-map/policies/write-confinement.toml)
e [guard Copilot non collegato](../../../../adapters/copilot/policies/xray-guard/policy.toml).

## 6. Metodo di ricerca e qualità delle evidenze

1. Formulare domanda, decisione supportata, vincoli, tecnologia/versione e cosa
   renderebbe utile una risposta. Consultare l'indice e le revisioni pertinenti.
2. Cercare letteratura con termini, sinonimi e famiglie di fonti disciplinari;
   includere lavori fondamentali e risultati recenti, repliche e controevidenze.
3. Leggere le fonti accessibili e registrare copertura reale, versione e punti
   precisi che sostengono ciascuna affermazione.
4. Confrontare metodi, dati e condizioni; sintetizzare cosa si trasferisce al
   progetto e cosa resta incerto. Collegare eventuali esperimenti locali.
5. Verificare citazioni e collegamenti; pubblicare il documento e aggiornare
   l'indice solo con una consegna integra e uno stato di copertura veritiero.

La selezione dei siti è guidata dalla disciplina, non da una lista esclusiva
immutabile. Esempi iniziali: Semantic Scholar per scoperta e reti di citazioni;
arXiv per preprint; ACL Anthology per linguaggio/NLP; PMLR per machine learning.
Per altre discipline selezionare archivi ed editori primari pertinenti. Seguire
DOI e pagina dell'editore per identità, versione e avvisi. Documentazione ufficiale
e standard affiancano i paper per fatti legati a API, implementazioni e versioni.

Il registro di ricerca conserva query, sito, filtri, istante, risultati
selezionati/esclusi con motivo e limiti di accesso. Non impone un numero minimo di
paper. Una fonte fondativa pertinente può bastare per una domanda circoscritta;
una scelta controversa richiede confronto. Versioni dello stesso studio, copie
su siti diversi e studi sullo stesso dataset non valgono come repliche indipendenti.

Per ogni paper registrare identità stabile, autori, titolo, anno, sede, DOI o
identificatore equivalente, URL primario, versione, sinossi breve, metodo,
risultati rilevanti, limiti e stato di lettura. La lettura distingue
`full-text`, `selected-sections`, `abstract-only`, `metadata-only`, `unavailable`.
Le sezioni lette vanno nominate; un PDF troncato non è `full-text`.

Ogni conclusione ha un identificatore stabile, fonti e sezioni/pagine, tipo di
supporto teorico/empirico/documentale, controevidenze, condizioni di validità e
confidenza motivata. Separare quanto afferma la fonte dall'inferenza dell'agente e
dal risultato locale. Peer review, recente pubblicazione o numero di citazioni
non bastano da soli a certificare correttezza o trasferibilità.

Registrare il budget di ricerca e i consumi osservabili. L'automatismo impiega il
minimo sforzo che può cambiare la decisione; si ferma quando le domande sono
risolte, ulteriori ricerche non aggiungono evidenza pertinente, termina il budget
o manca una capacità. I valori iniziali saranno calibrati con casi reali e non
presentati come soglie scientifiche. Usare backend già disponibili; nessuna API
a pagamento, nuova dipendenza o credenziale è un prerequisito implicito.

## 7. Aggiornamento, superamento e impatto

`update-research` rilegge domanda e contesto, confronta le versioni delle fonti,
cerca avvisi editoriali e nuove evidenze e controlla le tecnologie pertinenti
rispetto a quelle realmente usate. Usa quando disponibili Crossmark, Crossref e
Retraction Watch insieme alla fonte primaria. Assenza di un avviso significa
«nessun avviso trovato nelle fonti consultate», non validità accertata.

| Dimensione | Informazione mantenuta separatamente |
|---|---|
| Fonte | Preprint/pubblicazione; versione; avvisi di correzione, preoccupazione, ritiro o ripristino, con data e fonte |
| Conclusione | Supportata, contestata, contraddetta entro condizioni definite oppure evidenza insufficiente |
| Applicabilità locale | Applicabile, da rivalutare o non applicabile, con tecnologia/versione e motivo |
| Ricerca | Corrente, da riesaminare o superata da una revisione/ricerca identificata |
| Esperimento | Pianificato, eseguito o non eseguibile; esito e ambito della verifica indipendenti dai giudizi sulla letteratura |

Un ritiro fa riesaminare le conclusioni dipendenti e rimuove la fonte come sostegno
positivo affidabile finché non chiarita; non dimostra da solo l'opposto di ogni
conclusione. Un risultato contrario può dipendere da condizioni diverse. Un
paper anziano non scade per età; una nuova tecnologia può cambiare l'applicabilità
senza confutare il risultato originale. Ogni superamento indica ambito, motivo,
fonte sostitutiva, conclusioni coinvolte ed eventuale incertezza residua.

Distinguere `last_checked_at` (tentativo più recente), copertura/esito del controllo
e `last_updated_at` (modifica sostanziale). Un controllo completo senza novità
aggiunge una voce alla cronologia dei controlli, senza creare una revisione
scientifica fittizia. Un controllo fallito registra il tentativo ma non dichiara
freschezza verificata. Cambi sostanziali producono una nuova revisione immutabile.

Una modifica accertata, come un ritiro verificato, può essere pubblicata anche
quando il controllo complessivo è parziale. Revisione e ricevuta mantengono
questo limite senza avanzare la data dell'ultimo controllo completo.

I documenti consumatori citano ricerca, revisione e conclusioni usate. La ricerca
registra i consumatori conosciuti, senza promettere di aver trovato citazioni
esterne non indicizzate. Un cambiamento genera un elenco di specifiche, ADR, FRD
e test da riesaminare, con motivo. Non riscrive decisioni accettate o requisiti
approvati. L'eventuale revisione segue il proprietario e la sua procedura di
approvazione; implementazione e test di prodotto richiedono il relativo compito.

## 8. Archivio, template e cronologia

`docs/research/README.md` è l'indice di accesso: titolo, temi, domanda, proprietario,
revisione corrente, ultimo controllo con esito, ultimo aggiornamento e stato.
Lettura progressiva: indice, TL;DR pertinente, sezioni e fonti necessarie.

Prima di creare un documento, cercare ricerche e Markdown affini anche non
indicizzati nelle cartelle research pertinenti. Un tema ripreso nella
conversazione riusa quella ricerca. Nuove fonti o aggiornamenti cambiano lo
stesso file corrente: timestamp di ricerca, passaggi superati visibilmente
barrati con sostituzione motivata e changelog descrittivo. Un documento nuovo
serve solo a una domanda distinta; più proprietari sovrapposti richiedono una
scelta prima di creare, unire o spostare. Il solo riuso non genera file.

Nei progetti senza un'altra convenzione, ogni ricerca usa questa struttura:

```text
docs/research/<tema>/
  README.md                 # stesso file corrente, ricerca completa e stato dei controlli
  revisions/r0001.md        # snapshot storico immutabile
  revisions/r0002.md        # creato solo per cambi sostanziali
  checks/<check-id>.md      # ricevuta append-only di ogni controllo effettivo
  experiments/<exp-id>/     # protocollo/risultati necessari, quando presenti
```

In Daodan, una ricerca specifica di un plugin risiede nel suo dossier
`docs/plugins/<plugin>/research/<tema>/`; l'indice globale la collega. Una ricerca
trasversale può avere sede in `docs/research/<tema>/`, con link dai dossier.
Una ricerca ha un solo proprietario canonico; non duplicare il testo. Non migrare
archivi esistenti implicitamente e non scrivere sotto `docs/superpowers/`.

L'identità della ricerca è stabile; titolo, slug e revisioni non devono spezzare
i riferimenti. Le revisioni precedenti restano leggibili e citabili esattamente.
Ogni nuova revisione porta il changelog cumulativo e il link alla precedente.
Il file corrente contiene l'intera ricerca; gli snapshot non sono pagine
correnti concorrenti. Un Markdown preesistente mantiene il proprio percorso,
senza un secondo README parallelo: l'aggiornamento conserva i byte originari
nello storico e verifica il digest prima della sostituzione. I metadati derivati
dei controlli restano separati dal corpo scientifico, così un controllo senza
novità aggiorna la data visibile senza inventare una nuova revisione scientifica.
Modifiche manuali concorrenti non vengono sovrascritte silenziosamente.

Il [template documentale](science-research-template.md) definisce metadati,
TL;DR, contesto, changelog, bibliografia ragionata, sintesi, conclusioni, verifiche,
impatto e cronologia. La prosa risponde alla domanda; dettagli riproducibili lunghi
sono collegati. Una spiegazione insufficiente non viene abbreviata per rispettare
un limite arbitrario di parole.

Prima di pubblicare, confrontare la revisione attesa. Una collisione fra sessioni
non sovrascrive file. Pubblicare revisione e ricevute complete prima di aggiornare
il puntatore e l'indice; un'interruzione mantiene disponibile l'ultima revisione
integra e rende riconoscibile il lavoro non pubblicato. Gli indici sono
ricostruibili dalle fonti canoniche. I percorsi devono restare nel progetto e
nelle destinazioni autorizzate, anche in presenza di traversal, symlink o junction.

## 9. Evidenza empirica e test

Un esperimento utile definisce prima dell'esecuzione ipotesi, confronto di base,
dataset o casi, metrica, criterio di successo e condizioni. Non cambiare la
soglia dopo aver visto il risultato senza registrare una nuova analisi esplorativa.
Il confronto deve proteggere un requisito o una modalità di fallimento indipendente.

Il risultato registra comando/procedura riproducibile, revisione del codice,
versioni software, ambiente, dati o loro identità, tentativi, misure con unità,
variabilità pertinente ed esito. Conservare risultati negativi e inconcludenti.
Una misura singola o una replica degli stessi dati non dimostra generalità.

La skill produce il protocollo e recepisce gli esiti con la loro provenienza.
L'esecuzione locale resta al coordinatore del compito e al proprietario competente,
quando autorizzata e con dati e strumenti disponibili. La scrittura di test del
prodotto resta a `testing`; per esperimenti di altro dominio il consumer usa il
metodo pertinente. Una ricerca esplicita senza tale contesto consegna il protocollo
non eseguito. Mancanza di dati, costo, accesso o autorizzazione produce un protocollo
`not-run` con prerequisiti. Un risultato teorico può non richiedere un esperimento:
spiegare cosa è dimostrato e cosa resterebbe da misurare nel progetto.

## 10. Integrazione nel repository e negli host

| Proprietario | Modifica da progettare e verificare nell'implementazione |
|---|---|
| `research` | Nuova skill, template, helper minimi per stato/archivio e tre workflow con relativi sidecar TOML |
| `project-delivery` | Chiamata del metodo ai punti di brainstorming, specificazione, ADR/FRD e aggiornamento del contesto |
| `project-knowledge` e `skill-catalog` | Regola persistente, indice canonico e discovery della skill senza caricare tutto l'archivio |
| `work-controller` e `testing` | Riuso dei rispettivi contratti per home, esecuzioni, consegne e test; nessuna inversione delle dipendenze |
| Adattatori e compilatore | Capacità opzionale degli hook, dichiarazione/generazione e binding degli eventi realmente supportati; rigenerazione dei cinque host |

Il comando e la skill hanno nomi diversi: `science-research` e
`science-based-approach`, evitando collisioni fra componenti. I consumer dichiarano
il provider richiesto quando invocano il metodo; la sua assenza non viene mascherata
come OFF. Il controllo di stato non necessita della rete. Gli hook nativi non
diventano una capacità obbligatoria che esclude gli host serviti dai workflow.

Gli archi statici nuovi previsti sono `project-delivery -> research`,
`project-knowledge -> research` e `research -> work-controller`. Il primo serve
brainstorming e documenti decisionali; il secondo i percorsi documentali diretti;
il terzo la home e le esecuzioni scientifiche. `project-delivery -> testing` resta
l'arco per i test. Nessun arco `research -> project-delivery` o `research -> testing`.
La validazione del registro deve confermare assenza di cicli e completezza della
closure, inclusi i ruoli realmente dispatchati. L'entry plugin `daodan` raggiunge
il metodo tramite i proprietari dichiarati, senza duplicarne l'orchestrazione.

Gli attuali ricercatori di `research` sono web-only. Il coordinatore locale prepara
un brief minimo e privo di dati riservati; i ricercatori ricevono domanda e vincoli
necessari e restituiscono evidenze. Non assegnare loro implicitamente letture del
repository. Riutilizzare ricerca e lettura esistenti, ma specializzare la
valutazione scientifica: l'attuale graduatoria generale delle fonti non sostituisce
il giudizio su disegno dello studio, repliche e pertinenza della domanda.

Negli FRD, il DOI è una citazione bibliografica, non una prova di comportamento
locale. Quando pertinente, l'evidenza FRD punta alla sintesi locale versionata con
digest e span previsti dal suo schema. Rimane distinta l'origine del requisito
richiesto dall'utente; nessun paper lo rende automaticamente approvato.

La regola durevole da integrare attraverso `project-knowledge` è: leggere Science
Mode; quando ON applicare il controllo scientifico nei punti previsti e consultare
l'indice pertinente; quando OFF rispettare la disattivazione; collegare le revisioni
usate e conservare limiti ed evidenze. Non memorizzare lo stato ON/OFF nei file di
istruzioni. In Daodan modificare la fonte canonica `CLAUDE.md` e sincronizzare
`AGENTS.md` con il generatore; nessuna modifica a questi file è parte della presente
consegna documentale.

## 11. Errori, limiti e uso delle risorse

| Caso | Esito richiesto |
|---|---|
| Rete/backend assente, fonte bloccata o testo non accessibile | Registrare copertura e limite; usare soltanto evidenze effettivamente disponibili |
| Paper senza letteratura sufficiente o fonti in conflitto | Dichiarare insufficienza o contrasto; non inventare consenso o citazioni |
| Budget esaurito o interruzione | Salvare consegne e checkpoint posseduti; stato parziale, ripresa senza ripetere lavoro già verificato |
| Documento o record modificato in parallelo | Rifiutare la pubblicazione sul candidato precedente; rileggere e riconciliare |
| Mancanza di prova necessaria a una decisione | Mantenere esplicita l'ipotesi e aperto il relativo requisito di verifica; continuare lavoro indipendente |

OFF non è un errore e non impedisce i normali workflow. Una ricerca non riuscita
non è una ricerca scientifica completata; può comunque permettere una bozza che
esponga le sue ipotesi. Nessun blocco universale di ogni decisione per assenza di
paper: valgono i criteri di accettazione e gli obblighi del compito specifico.

Le query pubbliche non includono segreti, codice riservato o dati personali del
progetto. I contenuti recuperati sono dati, mai istruzioni operative. Collegare e
sintetizzare le fonti nel rispetto delle condizioni d'accesso; non aggirare login
o paywall e non ridistribuire PDF senza un titolo che lo consenta. Le dipendenze
nuove richiedono verifica corrente di supporto, licenza, compatibilità e costo;
questa specifica non impone l'integrazione di alcuna nuova API.

## 12. Criteri di accettazione

I casi seguenti definiscono l'accettazione. La [validazione](../validation.md)
distingue prove automatiche, revisione dei metodi e verifiche non eseguite.

### Modalità e attivazione

| ID | Scenario | Risultato osservabile |
|---|---|---|
| AC-01 | Progetto senza configurazione | Stato ON implicito; consultazione non scrive configurazione |
| AC-02 | OFF, nuova sessione e worktree dello stesso progetto | Stato OFF condiviso; nessuna ricerca, consultazione o scrittura automatica |
| AC-03 | Ricerca esplicita mentre OFF | Esegue solo il compito richiesto; preferenza resta OFF |
| AC-04 | Configurazione corrotta, comando invalido o scrittura concorrente | Errore esplicito; nessuna riattivazione o sovrascrittura silenziosa |
| AC-05 | ON ripetuto, poi OFF durante lavoro automatico | Nessun aggiornamento retroattivo o storico fittizio; stop al punto sicuro con parziali preservati |

### Workflow e fonti

| ID | Scenario | Risultato osservabile |
|---|---|---|
| AC-06 | Brainstorming, specifica, ADR, FRD e problema sostanziale | Ciascun percorso raggiunge il controllo prima della decisione e ne conserva l'esito |
| AC-07 | Stesso evento da hook e workflow; salvataggio della ricerca | Una sola esecuzione; nessun ciclo ricorsivo |
| AC-08 | Ricerca pertinente riutilizzabile; modifica editoriale | Nessuna nuova rete inutile; distinzione `reused` / `not-applicable` |
| AC-09 | Abstract disponibile e PDF troncato | Copertura dichiarata correttamente; nessuna lettura integrale inventata |
| AC-10 | Due copie dello stesso studio e una fonte contraria | Nessuna falsa replica indipendente; controevidenza e condizioni riportate |

### Aggiornamento e tracciabilità

| ID | Scenario | Risultato osservabile |
|---|---|---|
| AC-11 | Correzione, ritiro, ripristino o nuova versione | Avviso documentato, confronto sulle conclusioni coinvolte e nuovo stato motivato |
| AC-12 | Paper antico valido; tecnologia del progetto cambiata | Nessun superamento per sola età; applicabilità valutata sulla versione pertinente |
| AC-13 | Controllo senza novità oppure controllo fallito | Ricevuta aggiunta; nessuna revisione sostanziale fittizia o freschezza non verificata |
| AC-14 | Conclusione superata citata da ADR/FRD accettati | Nuova revisione e impatto segnalato; byte dei record accettati invariati |
| AC-15 | Aggiornamento di tutte le ricerche, una inaccessibile | Elenco completo degli esiti per identità canonica, senza duplicazioni né successo globale falso |

### Archivio e verifica

| ID | Scenario | Risultato osservabile |
|---|---|---|
| AC-16 | Nuova ricerca dal template | Metadati, sinossi, fonti, contesto, TL;DR, conclusioni, test e cronologia collegati |
| AC-17 | Interruzione durante pubblicazione o collisione | Ultima revisione integra leggibile; storico preservato; nessuna scrittura fuori destinazione |
| AC-18 | Esperimento positivo, negativo, inconcludente o non eseguito | Protocollo, ambiente ed esito corretti; nessuna esecuzione inventata |
| AC-19 | Fonte accademica collegata a FRD | Evidenza locale verificabile dove richiesta; paper distinto dall'approvazione del requisito |
| AC-20 | Cinque export e host con/senza hook nativi | Compatibilità dei workflow verificata separatamente da manifest e prove effettive degli hook |

### Autorizzazioni e composizione

| ID | Scenario | Risultato osservabile |
|---|---|---|
| AC-21 | Brainstorming di sola lettura con Science Mode ON | Nessuna scrittura nel progetto; risultati nel run autorizzato o in chat |
| AC-22 | Controllo chiamato da un consumer con autorizzazione sufficiente | Metodo composto senza un secondo comando/intervista; pubblicazione entro il perimetro autorizzato |
| AC-23 | Nuove dipendenze e vecchio `team-research` | Registro aciclico; ricercatori precedenti web-only; nessun dispatch di test non dichiarato |
| AC-24 | Conversazione riprende un tema presente in Markdown non indicizzato | Scoperta e riuso prima di creare file; nessuna ricerca parallela sovrapposta |
| AC-25 | Nuove evidenze cambiano una ricerca esistente | Stesso percorso corrente, timestamp aggiornati, passaggi superati barrati e changelog descrittivo; storico separato |
| AC-26 | File corrente modificato manualmente o proprietari sovrapposti | Nessuna sovrascrittura o duplicazione silenziosa; confronto del digest o scelta del proprietario |

Le verifiche automatiche devono proteggere comportamento e integrità: modalità,
deduplicazione, contenimento dei percorsi, aggiornamento atomico e storia. Le
valutazioni del metodo usano casi realistici e fonti controllate, con almeno un
caso negativo; un conteggio di citazioni o un confronto dei titoli non prova
qualità scientifica. Prove su host installati registrano versione, evento,
permessi e risultato. Un test del compilatore non sostituisce queste prove.

## 13. Riferimenti e scelte da non introdurre

Fonti ufficiali consultate il 27 ottobre 2026 per le capacità dei servizi, non
come prova empirica dell'efficacia di questa skill:

| Fonte | Uso nella proposta |
|---|---|
| [Semantic Scholar Academic Graph](https://api.semanticscholar.org/api-docs/snippets) | Scoperta, metadati, riferimenti e citazioni |
| [arXiv](https://arxiv.org/) | Archivio accademico; presenza in archivio distinta dalla peer review |
| [ACL Anthology](https://aclanthology.org/) e [PMLR](https://proceedings.mlr.press/) | Esempi di fonti primarie disciplinari |
| [Crossmark](https://www.crossref.org/services/crossmark/) | Verifica degli aggiornamenti editoriali registrati |
| [Crossref / Retraction Watch](https://www.crossref.org/documentation/retrieve-metadata/retraction-watch/) | Ritiri e altri avvisi, con copertura dichiarata e non esaustiva |

Alternative escluse dalla proposta: ricerca online obbligatoria a ogni modifica;
nuovo plugin che duplica `research`; età usata come prova di obsolescenza;
riscrittura dello storico; aggiornamento automatico di decisioni accettate;
hook dichiarati universali senza prova; copia dell'intero archivio nelle istruzioni.

L'implementazione dovrà confermare gli eventi e gli schemi reali degli host e
calibrare i budget del metodo. Queste verifiche sono parte del lavoro futuro,
non prerequisiti inventati per usare i comandi di stato.

## Changelog della specifica

| Revisione | Data e ora | Modifica | Origine |
|---|---|---|---|
| 1 | 2026-10-27T09:19:58+01:00 | Prima specifica: ricerca, aggiornamento, archivio, verifiche, integrazioni e Science Mode | Conversazione e contratti locali ispezionati |
| 2 | 2026-10-27T10:17:12+01:00 | Implementazione: registrazione hook, archivio nella checkout autorizzata, pubblicazione parziale e collegamenti alla documentazione | Autorizzazione dell'utente, test e revisione indipendente |
| 3 | 2026-10-27T10:30:25+01:00 | Riuso preventivo anche dei Markdown non indicizzati; stesso file corrente, obsolescenza visibile e changelog; niente pagine sovrapposte | Chiarimento esplicito dell'utente sul riuso e aggiornamento in posto |
