# Chiarimenti, mappe decisionali e grafi di lavoro

Data: 24 ottobre 2026; direzione di reintegrazione del 25 ottobre 2026. Stato: **specifica proposta; il motore appartiene a `work-controller@daodan`; capacità progettate, trasferimento del codice e verifiche di esecuzione restano fatti distinti (sezione 13)**.

Questa specifica estende [ADR-0001](../../adr/ADR-0001-work-graph-step0-llm.md)
e il [disegno dei grafi di lavoro](2026-10-20-system1-work-graph-composition-design.md).
Definisce quando Daodan deve coinvolgere l'utente, come scegliere la forma della
conversazione e come riprendere il lavoro. La sezione 13 definisce il perimetro
del futuro motore condiviso di processi.

[ADR-0002](../../adr/ADR-0002-work-controller.md), proposto, assegna a
`work-controller` il motore generalista: composizione o sola verifica dei grafi,
orchestrazione ed esecuzione, con binding dei modelli e contabilizzazione dei
costi. La direzione del 24 ottobre verso un repository proprio, Deadly Brain,
è sostituita dalla richiesta del 25 ottobre: tutto il motore appartiene solo a
`work-controller@daodan`. Shinatama, Mukade e altri progetti consumano quel
provider senza introdurre dipendenze inverse. `model-routing@daodan` conserva
selezione dei modelli e prezzi. Il contratto progettato riceve definizioni YAML
di job, grafi e loop; anche l'intervista produce quel formato. La presenza del
runtime per grafi non prova che ogni costrutto progettato sia implementato.

**Il bisogno di una decisione umana attiva un chiarimento proporzionato:** una
domanda diretta, un'intervista mirata oppure una mappa decisionale. I prototipi dei
grafi operativi continuano a descrivere metodi, dipendenze, consegne e verifiche.
La mappa decisionale, progettata in Daodan da idee di Wayfinder e destinata al
motore condiviso, aiuta a esplorare le decisioni che determinano quel lavoro.

L'utente ha richiesto la stesura della specifica. Questo documento non prova
l'esecuzione del flusso e non autorizza installazioni, scritture su tracker,
implementazione, pubblicazione o addestramento.

## 1. Un esempio completo

Un consulente deve definire una migrazione. La documentazione chiarisce i sistemi
coinvolti, ma manca la tolleranza del cliente al fermo del servizio. Daodan cerca
prima nei requisiti e nelle decisioni esistenti. Se il dato manca, lo chiede.
Nel frattempo può continuare l'inventario autorizzato; la progettazione del cutover
resta in attesa perché dipende dalla risposta.

Se emergono scelte collegate su continuità, costi e responsabilità, la conversazione
diventa un'intervista. Se quelle scelte richiedono indagini e incontri successivi,
una mappa decisionale conserva le domande e il percorso esplorativo. Un'indagine
circoscritta può partire anche prima che tutte le decisioni siano prese: produce
evidenza che torna nella conversazione. La risposta accettata aggiorna il requisito
o il record competente; Daodan valuta quindi quali parti del piano riprendere o
rivedere.

Questo scambio può ripetersi. Ogni piano eseguibile conserva dipendenze valide;
il ritorno di evidenza alla conversazione non crea prerequisiti circolari tra task.

## 2. Responsabilità e fonti canoniche

| Elemento | Responsabilità | Quando ha concluso |
|---|---|---|
| Conversazione | Chiarire bisogni, alternative, criteri, vincoli e scelte dell'utente. | La domanda ha una risposta utilizzabile, oppure resta esplicitamente aperta, rinviata o ritirata. |
| Mappa decisionale | Guidare l'intero effort: destinazione, decisioni, domande, indagini, ticket di esecuzione e aspetti ancora indefiniti. | Quando la destinazione è raggiunta: nessun ticket aperto e ogni ticket di esecuzione chiuso dai gate del suo run. La chiusura di un ticket non sostituisce quei gate. |
| Piano e grafo operativo | Comporre i metodi conosciuti in attività con input, dipendenze, consegne e gate. | Tutte le consegne e verifiche obbligatorie del perimetro autorizzato sono soddisfatte. |
| Requisiti, specifiche e ADR | Conservare gli esiti sostanziali nel documento del rispettivo proprietario. | Secondo il ciclo del documento; un ADR resta `Proposed` fino alla sua integrazione. |
| Registro del run | Registrare domande pendenti, autorizzazioni, revisioni, consegne e controlli. | Secondo i gate di `work-controller`; un riepilogo conversazionale non li sostituisce. |

Il modulo di composizione espone anche un ingresso esplicito per iniziare
l'intervista da un obiettivo, senza YAML iniziale (sezione 13). L'utente può
quindi avviarla direttamente; il coordinatore può richiamare lo stesso metodo
quando un processo autorizzato richiede una composizione nuova.

Il metodo proprietario dell'attività decide quali input servono. `project-lifecycle`
fornisce il contesto e i vincoli del task cycle all'intervista generica del motore;
gli altri metodi richiamano lo stesso contratto di chiarimento senza duplicare un
proprio framework di intervista. `work-controller` possiede composizione,
validazione, orchestrazione, esecuzione e legame con la contabilizzazione.
`model-routing@daodan` conserva selezione dei modelli e prezzi.
`senior-review`
possiede obblighi, roster e composizione della review. Il catalogo verifica le
identità dei metodi disponibili; l'adapter dell'host lega strumenti e capacità.

Una domanda nel registro collega la conversazione ai consumatori che attendono.
La mappa riassume e collega le decisioni; il requisito o ADR ne conserva la
formulazione canonica. Nessuna delle tre viste deve diventare una copia autonoma
e divergente delle altre.

Il ticket conserva l'esito dell'esplorazione e le sue evidenze. Quando tale esito
diventa un requisito o una decisione architetturale, il documento proprietario
ne diventa la fonte normativa; ticket e mappa ne citano identità e revisione,
senza ricopiarne il contenuto. Le evidenze storiche rimangono consultabili.

## 3. Quando si attiva un chiarimento

Il coordinatore controlla gli input prima del dispatch e quando una nuova evidenza
invalida un presupposto. Consulta requisiti, decisioni applicabili, autorizzazioni
e fonti accessibili prima di coinvolgere l'utente. Il trigger è una decisione
umana essenziale ancora mancante, non la semplice presenza di incertezza.

| Situazione | Comportamento |
|---|---|
| La risposta esiste ed è ancora applicabile. | Riutilizzarla con il suo riferimento. Nessuna nuova domanda. |
| Manca un fatto verificabile da codice, dati o documentazione accessibili. | Eseguire l'indagine autorizzata. Dichiarare un eventuale limite di accesso o di evidenza. |
| Manca una preferenza, un criterio di business, un requisito o una scelta di perimetro essenziale. | Aprire un chiarimento e identificare i consumatori dipendenti. |
| Manca il permesso per un'azione che lo richiede. | Chiedere l'autorizzazione prevista dal proprietario; una preferenza tecnica non la concede. |
| È una scelta ordinaria di implementazione già coperta da requisiti e autorizzazione. | Decidere nel perimetro assegnato e motivare le assunzioni materiali. |
| Un tool fallisce, manca un provider o un contratto è violato. | Attivare il recupero competente. Chiedere all'utente solo l'eventuale decisione che il recupero non può risolvere. |

Un worker segnala il bisogno al coordinatore con le evidenze e i consumatori
interessati. Il coordinatore deduplica le richieste ed è responsabile del dialogo:
più worker non devono porre la stessa domanda in parallelo. Una classificazione
incerta lascia visibile il dubbio; non produce una risposta implicita.

## 4. Tre forme della conversazione

| Forma | Quando serve | Esito atteso |
|---|---|---|
| Domanda diretta | Un dato o una scelta locale, con conseguenze sufficientemente chiare. | Risposta collegata alla domanda e ai consumatori. |
| Intervista mirata | Scelte collegate che vanno chiarite progressivamente entro il problema corrente. | Requisiti, esempi verificabili, alternative e decisioni nel formato del metodo proprietario. |
| Mappa decisionale | Esplorazione dal percorso ancora incerto, troppo ampia per una sola sessione. | Mappa persistente con ticket decisionali e di esecuzione, collegati alle evidenze, ai documenti canonici e ai run. |

La selezione dipende dalla struttura del problema, non da una soglia arbitraria
di domande. Si parte dalla forma sufficiente e si rispetta la preferenza esplicita
dell'utente. Un ritardo nella risposta non giustifica l'apertura di una mappa.
Si riusa una mappa pertinente già esistente; problemi indipendenti non vengono
accorpati soltanto perché riguardano lo stesso progetto.

L'intervista del task cycle conserva il metodo già presente: contesto concreto,
una domanda per turno, raccomandazione motivata quando utile, esempi nominali,
di confine e di rifiuto. Non si aggiunge una seconda intervista prima di quella
esistente. La mappa decisionale usa la stessa intervista per i suoi ticket con
l'utente (sezione 7).

### Come si pone una domanda

Vale per ogni forma e ogni dominio: requisiti di un documento Word o di una
presentazione, indagine su un bug, nuova funzionalità o evolutiva. Chi risponde
ha poca attenzione disponibile: la domanda deve bastare da sola, senza perdere
fatti. Vale anche per ogni ticket della mappa decisionale.

- **Prima la domanda.** La prima riga è la domanda. Niente premesse, niente riepiloghi.
- **Contesto minimo e concreto.** Solo i fatti che servono a rispondere, ancorati
  a ciò che l'utente ha davanti: file e riga, sezione o slide, messaggio d'errore,
  comportamento osservato. Ciò che serve dai turni precedenti viene ripetuto, non
  dato per ricordato.
- **Una decisione per domanda.** Una domanda per turno, una sola scelta per domanda.
- **Opzioni brevi, raccomandazione prima.** Da due a quattro opzioni, ciascuna con
  la sua conseguenza in una riga. La raccomandazione è la prima e porta il motivo.
  L'utente può sempre rispondere fuori dalle opzioni.
- **Linguaggio semplice e letterale.** Frasi brevi, parole dell'utente e del suo
  dominio, nessuna figura retorica. Gergo tecnico solo se l'utente lo usa.
- **Si tagliano parole, mai fatti.** Vincoli, rischi, effetti irreversibili, costi
  e limiti dell'evidenza restano nella domanda quando incidono sulla risposta.
  Un dettaglio rilevante troppo lungo per una riga diventa un rimando esplicito,
  non un'omissione.
- **Lo stato si vede.** In un'intervista ogni domanda dice a che punto è il
  chiarimento e cosa sblocca la risposta.

### Avvio della mappa

La mappa è un metodo di `work-controller`: il coordinatore la apre o la riprende quando
la forma scelta è la mappa, e dice all'utente il motivo in una riga. L'utente può
chiedere una forma più leggera. Si riusa la mappa pertinente esistente invece di
aprirne una seconda.

Wayfinder upstream resta invocabile solo dall'utente (`disable-model-invocation:
true`), ed è la ragione principale per cui Daodan ne riscrive le idee invece di
delegarlo (sezione 7). Chi preferisce lo strumento upstream può sempre usarlo da
sé; un suo esito entra in Daodan come evidenza, non come mappa di Daodan.

## 5. Contratto del passaggio

La domanda deve essere persistente e identificabile anche dopo un'interruzione.
Questa tabella definisce informazioni logiche richieste, **non un nuovo schema
JSON di produzione**. L'implementazione estenderà il contratto di `work-controller`
e userà riferimenti agli artefatti esistenti dove bastano.

| Informazione | Scopo |
|---|---|
| Identità e origine | ID stabile della domanda, run e metodo richiedente. Evitare duplicati e riconoscere risposte ripetute. |
| Contenuto e motivo | Domanda formulata secondo la sezione 4, cosa manca e quale decisione consente. Distinguere requisito, preferenza, fatto dichiarato e autorizzazione. |
| Contesto pertinente | Perimetro, evidenze consultate, decisioni precedenti e limiti noti. Caricare solo ciò che serve alla risposta. |
| Consumatori e validità | Attività, input e revisioni interessati; condizioni sotto cui la risposta rimane applicabile. |
| Conversazione | Forma scelta e riferimenti alla sessione, mappa o ticket, se presenti. |
| Risposta e provenienza | Risposta umana originale o riferimento stabile, fonte, significato normalizzato e artefatti canonici aggiornati. |
| Risoluzione | Esito, parti ancora aperte, eventuale sostituzione e motivazione della ripresa o revisione. |

Opzioni e raccomandazione possono aiutare a rispondere. Una selezione preimpostata
non è una risposta. La normalizzazione non deve aggiungere obblighi, preferenze
o permessi che l'utente non ha espresso. Una risposta che autorizza un'azione
entra anche nel registro delle autorizzazioni attraverso il meccanismo competente.

I prototipi dichiarano gli input decisionali e i punti in cui possono servire.
L'istanza del grafo lega le domande ai consumatori effettivi. Non si inserisce
un'intervista obbligatoria in ogni nodo né una copia della mappa nel grafo.

## 6. Attesa, risposta e ripresa

1. **Registrare prima di attendere.** Salvare domanda, contesto e dipendenze prima
   di terminare il turno o cedere il controllo. Se manca lo strumento per domande,
   mostrare la domanda nel canale disponibile e conservarla per la ripresa.
2. **Fermare i consumatori dipendenti.** Non avviare attività che richiedono la
   risposta. Se sono già in esecuzione, richiedere l'arresto al primo punto sicuro
   supportato dall'host e riconciliare consegne ed effetti già prodotti. Il loro
   risultato non passa un gate basato sul presupposto invalidato.
3. **Proseguire il lavoro indipendente.** Farlo soltanto se perimetro, permessi,
   input, risorse, isolamento e budget lo consentono. Non trattenere inutilmente
   worker o lock durante l'attesa; conservare le protezioni necessarie sugli effetti
   in corso. Nessun polling continuo per sollecitare l'utente.
4. **Accettare una risposta pertinente.** Verificarne fonte, significato e validità
   rispetto alla domanda. Risposte parziali o contraddittorie risolvono solo ciò che
   è esplicito; il resto richiede un seguito mirato. Silenzio e tempo trascorso
   non risolvono la domanda.
5. **Valutare l'impatto.** Aggiornare il documento competente e le autorizzazioni
   effettivamente concesse. Se cambiano semantica, perimetro, contratti o topologia,
   produrre una nuova revisione del piano secondo il controllo esistente.
6. **Riprendere con verifiche valide.** Riutilizzare risultati e controlli solo se
   le loro dipendenze sono ancora valide. Invalidare selettivamente con evidenze
   sufficienti; altrimenti riesaminare conservativamente la regione dipendente.
   Conservare revisioni, risposte e artefatti precedenti per spiegare il cambiamento.

L'attesa non è una consegna riuscita né, da sola, un errore del worker. Finché
un input obbligatorio manca, il run non può dichiarare il relativo lavoro completo.
Rinviare o rifiutare una risposta conserva questo limite. L'utente può ritirare
un obiettivo o ridurre il perimetro; il cambiamento va registrato e verificato,
senza presentare il lavoro escluso come eseguito.

La ripresa usa lo stesso ID di domanda. Ricevere due volte la stessa risposta
non duplica autorizzazioni, ticket o dispatch. Una risposta sostitutiva resta
distinta dalla precedente. Un cambiamento estraneo al contesto della domanda non
obbliga a richiederla; un cambiamento sostanziale dei suoi presupposti richiede
nuova validazione e, quando necessario, conferma umana.

Questo è comportamento richiesto al futuro runtime. Un host senza interruzione
sicura o isolamento comprovato deve dichiarare il limite e trattenere l'ammissione
dei risultati coinvolti; la specifica non gli attribuisce capacità inesistenti.

## 7. Mappa decisionale: idee di Wayfinder, metodo condiviso

Decisione del 24 ottobre 2026: il metodo di mappa decisionale nasce in Daodan e
confluisce in `work-controller` (sezione 13). È ispirato a Wayfinder
(`mattpocock/skills`, licenza MIT), nella modalità
*ispirazione originale* della procedura di intake. Nessun testo upstream viene
copiato. I motivi:

- l'upstream è invocabile solo dall'utente, quindi Daodan non potrebbe aprirlo
  quando il trigger di chiarimento sceglie la mappa;
- il suo tracker locale di default (`.scratch/<effort>/`) vive nel checkout
  corrente: in un worktree sparisce con il worktree, e ogni worktree vede una
  mappa diversa;
- la sua fonte canonica è un issue tracker, mentre in Daodan l'autorità
  sull'esecuzione è il registro del run.

**La mappa guida l'intero effort**, per decisione dello stesso giorno. Nasce dalle
decisioni e prosegue con l'esecuzione. Qui Daodan si discosta dall'upstream, che
di default pianifica soltanto. I livelli:

1. la mappa tiene l'effort, su più sessioni;
2. un ticket di esecuzione è una parte della destinazione;
3. un run del task cycle esegue quel ticket, con il suo piano;
4. il grafo di lavoro ordina le attività dentro quel run.

**Idee adottate**, riscritte nei termini di Daodan:

| Idea | In Daodan |
|---|---|
| Destinazione | Si fissa per prima; ne deriva il perimetro. |
| Indice delle decisioni | Una riga per decisione chiusa, con collegamento. La decisione vive in un solo posto: ticket, requisito o ADR. |
| Non ancora specificato | Ciò che si intravede ma non si sa ancora formulare. Diventa ticket quando la domanda è precisa, non quando ha già risposta. |
| Fuori scope | Escluso consapevolmente; rientra solo se si ridisegna la destinazione. |
| Ticket con dipendenze | Un ticket decisionale è una domanda del registro (sezione 5); un ticket di esecuzione rimanda al suo run. I blocchi formano un grafo aciclico. La frontiera sono i ticket aperti, sbloccati e non presi. |
| Tipi di ticket | Ricerca (l'agente da solo, anche con worker in parallelo); prototipo e intervista (solo con l'utente); attività che serve a sbloccare una decisione; esecuzione, che consegna una parte della destinazione attraverso un task cycle. |
| Presa in carico | Una sessione prende il ticket prima di lavorarci, così sessioni parallele non lo duplicano. Per un ticket di esecuzione la presa in carico è la riga del suo task in `.daodan/agenda.json` (branch e holder): la mappa la collega, non la copia. |
| Dalle decisioni all'esecuzione | Un ticket di esecuzione si sblocca quando sono chiuse le decisioni da cui dipende. Apre un task cycle, la cui intervista riusa le decisioni già prese invece di richiederle. |

**Non adottato:** il tracker remoto come fonte canonica, i branch `research/<name>`
e il percorso `.scratch/`. Un tracker remoto potrà diventare una vista futura, con
riferimenti stabili e scritture soggette alle autorizzazioni del run.

**Regole della mappa:**

- Un ticket con l'utente si chiude solo con la sua risposta reale: l'agente non
  risponde al posto suo. Con l'utente si lavora un ticket alla volta; i ticket di
  ricerca possono procedere in parallelo.
- Le indagini producono evidenze. Possono chiudere una domanda fattuale, mai
  inventare una scelta dell'utente.
- Chiudere un ticket, prenderlo in carico o annotare la mappa non concede permessi
  e non soddisfa un gate operativo.
- Un ticket di esecuzione si chiude solo quando il suo run ha superato consegne e
  gate. Se il run produce evidenza che contraddice una decisione chiusa, si apre
  un nuovo ticket decisionale che blocca i ticket dipendenti: i blocchi restano
  aciclici e la decisione precedente resta consultabile.
- Blocchi della mappa e dipendenze del grafo di lavoro usano la stessa validazione
  aciclica; la libreria che la realizza è oggetto dell'ADR sul motore dei grafi.
- Mappa e ticket vivono nella home del progetto risolta da `work-controller`
  (il `.daodan/` del checkout principale), condivisa tra worktree; scrittura e
  lettura sono legate insieme. La mappa funziona offline.
- Le domande dei ticket seguono la forma della sezione 4.

**Provenienza e aggiornamenti upstream.** Il README nomina Wayfinder, con link e
licenza, tra i progetti di ispirazione. La tabella della skill `upstream-sync`
riceve una riga di sola ispirazione con il commit upstream letto: oggi `8295b8e`
del 7 ottobre 2026, plugin 1.3.1. A ogni refresh si legge cosa è cambiato in
`skills/engineering/wayfinder/` da quel commit, si decide quali idee adottare,
le si riscrive con parole proprie e si aggiorna il commit registrato. Nessun
merge, nessun testo copiato. README e riga si aggiungono con l'implementazione
del metodo.

## 8. Applicazione ai casi di Daodan

| Caso | Ruolo della conversazione | Ruolo del grafo operativo |
|---|---|---|
| Raccolta requisiti e consulenza funzionale | Chiarire obiettivo, attori, vincoli, esempi e criteri di accettazione; usare una mappa quando serve un percorso lungo. | Eseguire indagini e produrre specifiche secondo consegne verificabili. |
| Indagine tecnica o informativa | Chiedere finalità o priorità mancanti; distinguere ciò che l'utente decide da ciò che va verificato nelle fonti. | Acquisire e confrontare evidenze, conservando provenienza e limiti. |
| Analisi dati | Chiarire significato delle metriche, popolazione, interpretazione e scelte di business. | Profilare dati, controllare qualità e riprodurre trasformazioni e risultati. |
| Sviluppo e riparazione | Risolvere ambiguità che incidono sui requisiti o su una scelta essenziale; riusare l'intervista esistente. | Comporre modifica, test e review dai metodi canonici. |
| Codebase Map (`/daodan:map-code`) | Chiarire il perimetro se essenziale; leggere prima quanto già dichiarato. | Eseguire il metodo statico del proprietario. Nessuna intervista imposta per ogni fase, nessuna prova browser aggiunta alla mappa. |
| Composizione dei reviewer | Chiarire dominio o requisito se manca davvero un input di applicabilità. | Calcolare il roster previsto, preservare gli obblighi e assemblare i corpi canonici. L'utente non viene interrogato per ogni scelta meccanica di reviewer. |

Nel reviewer composer il contesto può cambiare l'applicabilità dei controlli.
Un'incertezza non consente di eliminare uno specialista obbligatorio: le regole
del proprietario conservano gli obblighi finché esiste evidenza valida per una
diversa applicabilità. Il dialogo non modifica indipendenza, coverage o criteri
di completamento della review.

In ogni riga della tabella le domande seguono la forma della sezione 4.

## 9. Implementazione iniziale e destinazione offline

Lo Step 0 segue ADR-0001: l'LLM può riconoscere la decisione mancante, proporre la
modalità e preparare domanda o piano nel contesto già disponibile. Ogni incarico
LLM distinto passa dal router competente. Non serve una chiamata aggiuntiva solo
per riconoscere un bisogno già emerso chiaramente nel lavoro corrente.

Il router conserva la conferma umana della proposta concreta di modello ed effort
prima del binding; può riusare una conferma dello stesso binding invariato secondo
le proprie regole. Il trigger di chiarimento non elimina questo gate e non
introduce un'approvazione automatica per tutto il run.

Validazione, identità, autorizzazioni e ammissione dei risultati restano ai
proprietari dei contratti. Input ed esiti strutturati non devono dipendere da un
provider di prompt o da un transcript remoto per essere interpretati.

In futuro il modello decisionale locale con inferenza CPU potrà aiutare a scegliere
la modalità e strutturare il passaggio, come per grafo, router e reviewer composer.
Non sostituisce la persona nel decidere requisiti, preferenze o autorizzazioni.
Questa specifica non seleziona una famiglia di modelli e non avvia addestramento.
L'adozione offline richiederà strumenti e dati locali, verifiche senza rete e
assenza di fallback remoto implicito.

## 10. Criteri di accettazione

I seguenti scenari definiscono cosa verificare durante l'implementazione.
**Non sono risultati di test già eseguiti.**

| ID | Scenario | Risultato osservabile |
|---|---|---|
| CD-01 | Esiste una risposta applicabile in un requisito o in un'autorizzazione precedente. | Il coordinatore la collega e prosegue senza ripetere la domanda. |
| CD-02 | Manca un dato reperibile nelle fonti accessibili. | Parte l'indagine autorizzata; una preferenza umana non viene inventata per colmare il dato. |
| CD-03 | Serve una scelta locale, eventualmente con una breve indagine risolvibile nella stessa sessione; poi emergono scelte collegate. | Domanda diretta e indagine circoscritta, quindi intervista solo quando necessaria. Né l'indagine breve né il ritardo della risposta causano l'apertura di una mappa. |
| CD-04 | L'esplorazione ha un percorso incerto, supera una sessione e ha già una mappa pertinente. | Il coordinatore riapre quella mappa, dice il motivo in una riga e riparte dalla frontiera; non ne apre una seconda. |
| CD-05 | Un task dipende dalla risposta, un altro è indipendente e autorizzato. | Il primo attende; il secondo può avanzare entro lock, budget e capacità reali. Il run non risulta completo. |
| CD-06 | Nuova evidenza invalida l'input di un worker già attivo. | Richiesta di arresto sicuro, riconciliazione degli effetti e verifica prima di ammettere il risultato. L'assenza della capacità è dichiarata. |
| CD-07 | Arrivano silenzio, risposta parziale, rinvio, rifiuto o risposta contraddittoria. | Restano espliciti i punti irrisolti; nessun default viene trattato come risposta. Un eventuale ritiro di scope non conta come lavoro eseguito. |
| CD-08 | Una risposta arriva due volte oppure dopo una revisione del piano. | Identità stabile e nessun doppio dispatch. Si verifica l'applicabilità; una revisione estranea non forza una nuova domanda. |
| CD-09 | La scelta modifica il perimetro o un contratto del piano. | Nuova revisione, invalidazione motivata delle parti dipendenti e conservazione delle evidenze precedenti. |
| CD-10 | L'utente preferisce una soluzione ma non autorizza l'azione richiesta. | La preferenza non diventa un grant. I gate e l'autorizzazione competente rimangono necessari. |
| CD-11 | Un ticket è chiuso, oppure un reviewer richiesto è indisponibile. | Nessun completamento dedotto dal tracker e nessuna riduzione silenziosa degli obblighi di review. |
| CD-12 | Manca lo strumento per domande e il processo viene riavviato. | La domanda persiste, viene presentata e ripresa con lo stesso ID; il processo non inventa la risposta. |
| CD-13 | Un tracker remoto o un'altra scrittura esterna non è autorizzata o non è supportata dall'host. | Il limite emerge prima dell'azione esterna; la mappa resta locale e nessuna scrittura esterna viene dichiarata eseguita. |
| CD-14 | Una decisione finale richiede un'indagine preliminare circoscritta. | L'indagine può completare il proprio perimetro; la sua evidenza torna alla domanda senza creare un ciclo nei prerequisiti del piano. |
| CD-15 | Si valuta il futuro percorso con inferenza CPU e rete disabilitata. | Le decisioni del modello rispettano gli stessi contratti; nessuna chiamata remota implicita e nessuna risposta umana sintetizzata. |
| CD-16 | Serve una domanda su un requisito di un documento, su un bug o su una funzionalità. | La prima riga è la domanda; il contesto è ancorato e basta a rispondere senza rileggere i turni precedenti; una sola decisione; opzioni con conseguenza e raccomandazione motivata; vincoli, rischi ed effetti irreversibili rilevanti sono presenti. |
| CD-17 | Wayfinder upstream cambia dopo il commit registrato. | Il refresh legge il diff da quel commit, adotta le idee utili riscrivendole e aggiorna il commit; nessun testo upstream entra nel repository. |
| CD-18 | Un ticket di esecuzione viene chiuso mentre il suo run non ha superato i gate. | La chiusura è rifiutata e la destinazione non risulta raggiunta. |
| CD-19 | Due sessioni prendono lo stesso ticket di esecuzione. | Solo una ottiene la riga in agenda; l'altra vede il ticket preso e sceglie un altro ticket della frontiera. |
| CD-20 | Il run di un ticket di esecuzione contraddice una decisione chiusa. | Nasce un nuovo ticket decisionale che blocca i dipendenti; nessun ciclo tra i blocchi, la decisione precedente resta consultabile. |

## 11. Percorso di adozione e stato verificabile

1. **Contratto e ripresa.** Estendere il registro canonico delle domande con
   dipendenze, provenienza e validità; definire migrazione e gate di completamento.
   La forma della domanda (sezione 4) entra nel contratto di chiarimento, così ogni
   metodo che chiede la eredita senza copiarla; l'intervista del task cycle la
   richiama dal contratto.
   Verificare prima domanda diretta, interruzione, duplicati e risposta obsoleta.
2. **Intervista e piano.** Collegare il metodo di intervista esistente e la
   revisione del grafo, mantenendo l'esecuzione delle sole parti indipendenti.
3. **Mappa decisionale.** Costruire mappa e ticket sul registro delle domande,
   nella home del progetto. Verificare apertura automatica, riuso della mappa,
   frontiera, presa in carico tra sessioni parallele e passaggio al task cycle.
   Collegare i ticket di esecuzione ai run e alle righe di `.daodan/agenda.json`
   senza copiarne lo stato, e chiuderli solo dopo i gate del run.
   Aggiungere il paragrafo nel README e la riga di sola ispirazione con il commit
   upstream letto.
4. **Host e costi.** Distinguere test del contratto, output dei cinque adapter e
   prove reali sugli host installati. Misurare domande evitabili, richieste ripetute,
   riprese errate e costo totale di contesto, esecuzione, verifica e retry.

Il passo 1 è implementato da
[questo piano](../plans/2026-10-24-work-controller-questions.md): `ask` registra
ogni domanda prima di porla, `answer` registra parole e fonte dell'utente, un task
che consuma `question:<id>` attende la risposta e un run non si chiude con domande
aperte. Restano da implementare i legami di validità, la revisione del lavoro già
fatto dopo una decisione cambiata e la mappa decisionale. L'assemblaggio canonico dei reviewer è invece presente; va distinto
dalla proposta semantica a prompt e dalle capacità del futuro runtime dei grafi.

Il lavoro sul motore appartiene a `work-controller@daodan`; la reintegrazione
non richiede uno split della toolchain né un repository aggiuntivo (sezione 13).

La prima adozione non richiede un planner offline completo. La specifica non
promette una riduzione dei token senza confronti misurati su lavoro equivalente.

## 12. Riferimenti e provenienza

Contratti e metodi del repository:

- [Registro canonico del lavoro](../../../plugins/work-controller/contracts/work.toml) e [helper di stato](../../../plugins/work-controller/skills/work-record/scripts/run_state.py).
- [Intervista del task cycle](../../../plugins/project-lifecycle/skills/lifecycle-method/references/interview.md).
- [Routing per incarico](../../../plugins/model-routing/skills/model-routing/references/task-routing.md).
- [Composizione della review](../../../plugins/senior-review/skills/review-preparation/references/composition.md) e [assemblaggio canonico](../../../scripts/daodan/composition.py).
- [Navigatore dei grafi](../../graphs/README.md).

Upstream esaminato il 24 ottobre 2026: plugin 1.3.1, ultimo commit di Wayfinder
`8295b8e` del 7 ottobre 2026. Su questo Claude Code è installata la 1.2.0. I link
puntano al ramo principale e servono come provenienza delle idee, non come
dipendenza:

- [Wayfinder: metodo upstream](https://github.com/mattpocock/skills/blob/main/skills/engineering/wayfinder/SKILL.md).
- [Regole di invocazione](https://github.com/mattpocock/skills/blob/main/.agents/invocation.md).
- [Tracker locale](https://github.com/mattpocock/skills/blob/main/skills/engineering/setup-matt-pocock-skills/issue-tracker-local.md).
- [Licenza MIT](https://github.com/mattpocock/skills/blob/main/LICENSE) e [changelog](https://github.com/mattpocock/skills/blob/main/CHANGELOG.md).

## 13. Deadly Brain: il motore condiviso

Il titolo conserva il nome storico per mantenere validi i riferimenti a questa
sezione. La decisione del 24 ottobre 2026 spostava il motore in un repository
proprio, **Deadly Brain**. La richiesta del 25 ottobre la sostituisce:
**il motore completo ha come unico proprietario `work-controller@daodan`**.
Shinatama, Mukade e altri progetti possono dipendere da quel provider; il motore
non dipende dai loro plugin. La collocazione in Daodan non crea un ciclo tra
marketplace. Nessun repository o pacchetto esterno fornisce una seconda copia
canonica del motore. La dismissione del repository separato richiede la verifica
del trasferimento e una propria autorizzazione circoscritta.

Identità, nelle parole dell'utente: ispirata a Wayfinder, con una forte componente
a grafo, anche deterministica. La precisazione successiva dello stesso giorno
fissa `work-controller` come creatore ed esecutore generalista di processi.
`model-routing@daodan` conserva il routing e i prezzi; la reintegrazione non
duplica quel proprietario. La presenza di helper, skill, codice trasferito o
prototipi non prova l'esecuzione di tutto il perimetro progettato.

| Contenuto | Proprietario canonico | Confine |
|---|---|---|
| Registro del run, agenda, gate, worker isolato, domande (`ask`, `answer`) | `work-controller@daodan` | identità ed evidenze `daodan/work/v1` conservate |
| Routing dei modelli e prezzi | `model-routing@daodan` | binding concreti del coordinatore, nessuna copia del router |
| Runtime dei grafi, artefatti, ticket, console e MCP | `work-controller@daodan` | moduli e risorse sotto la skill `work-record` |
| Discovery, modelli osservati, memoria semantica, loop e handover sugli host | requisiti dei rispettivi contratti | prove separate dall'inclusione del codice |

Il codice esistente trasferito gestisce ammissione immutabile di grafi YAML,
esecuzione sequenziale, tentativi e journal SQLite, artefatti per impronta,
ticket decisionali, ripresa conservativa e viste condivise per console locale e
MCP di sola lettura. I moduli Python sono in
`plugins/work-controller/skills/work-record/scripts/work_controller/`; il launcher
è `skills/work-record/scripts/controller.py`. Lo store predefinito è
`.daodan/processes` del checkout principale. Un legame esplicito tra processo e
registro mantiene autorevoli autorizzazioni, consegne, domande e gate del task;
il successo del grafo non li sostituisce. Gli schemi legacy e le impronte delle
definizioni ammesse non vengono riscritti. La lettura di archivi legacy richiede
una home esplicita invece di scegliere silenziosamente tra radici concorrenti.

Le capacità aggiuntive descritte qui sono requisiti, non risultati del
trasferimento: discovery di componenti registrati, dispatch e arresto su host
installati, osservazione dei modelli, memoria semantica, loop limitati,
esecuzione parallela e replan selettivo richiedono implementazione ed evidenza
proprie. La licenza e la provenienza del motore restano conservate.

Gli archetipi restano ai consumatori: il task cycle di Daodan, le operazioni Office
di Mukade, i flussi di Shinatama. Il nucleo gestisce dipendenze, decisioni,
tentativi, consegne, verifiche e budget. Regole su branch, worktree, ADR e commit
restano nel contratto Daodan; un processo documentale non deve ereditarle.

### Tre usi, un solo contratto YAML

Il runtime **deve ricevere una definizione YAML** per ogni job, grafo o loop.
Il formato è obbligatorio anche quando il processo nasce da conversazione,
contesto, intervista o archetipi: il compositore materializza il YAML prima
dell'ammissione. Il file scritto dall'utente segue lo stesso percorso.

| Uso | Comportamento |
|---|---|
| Composizione | Avviare l'intervista dall'ingresso esplicito o dal coordinatore, leggere contesto e capacità disponibili, chiedere ciò che manca, riusare un archetipo pertinente oppure proporre il processo con un LLM (ADR-0001), quindi produrre YAML. |
| Sola verifica di integrità | Ricevere YAML già scritto e restituire errori, lacune o validità strutturale. Non avviare job, assegnare modelli o concedere autorizzazioni. |
| Esecuzione o ripresa | Ammettere una versione YAML validata, assegnare i modelli ai job LLM, eseguire i nodi pronti e conservarne stato, consegne, verifiche e costi. |

Il passaggio logico è: **contesto o YAML fornito → definizione YAML → validazione
→ binding dei job LLM → esecuzione e contabilizzazione**. La modalità di sola
verifica termina alla validazione. Un YAML valido non dimostra da solo che il
processo raggiunga l'obiettivo e non autorizza la sua esecuzione.

Il contratto identifica versione e tipo della definizione: job singolo, grafo o
loop. Per ogni nodo dichiara identità, attività, componente o worker consentito,
input, output, dipendenze, condizioni, controlli di successo, perimetro e capacità
richieste. I nodi possono essere LLM, operazioni deterministiche o passaggi umani.
Un input proviene da un predecessore oppure è dichiarato come input esterno del
processo. Il tipo di grafo conserva i riferimenti ai componenti registrati e ai
loro contratti; non copia gli inventari di `plugin.toml`. Le capacità restano
neutre, per esempio `repository.read` e `shell.execute`; l'adapter lega gli
strumenti dell'host. Una skill fornisce un metodo, un ruolo identifica un worker,
un workflow un ingresso: caricare una skill non equivale ad avviare un agente.

Lo schema concreto e i nomi dei campi saranno definiti nel piano di
implementazione, riusando i contratti esistenti dove servono già. TOML può restare
il formato dei metadati e dei contratti dei componenti; JSON può restare una
rappresentazione interna e il formato dei record di esecuzione. Nessuno dei due
sostituisce il YAML obbligatorio in ingresso al runtime.

Il parser YAML è una **eccezione circoscritta** al vincolo della sola libreria
standard: lettura di dati senza costruttori eseguibili, errori espliciti per
definizioni ambigue o non supportate. Il nucleo mantiene la libreria standard.
Nessuna libreria viene selezionata o installata da questa specifica; prima
dell'adozione vanno verificati manutenzione, compatibilità, licenza e sicurezza.
Non realizzare un parser artigianale o chiamare YAML un sottoinsieme implicito.

### Modulo di composizione tramite intervista

Il compositore è un modulo interno di `work-controller`. Riceve obiettivo,
contesto ed evidenze accessibili, decisioni e vincoli, eventuale processo da
evolvere e inventario reale dell'harness. Produce la definizione YAML con i
riferimenti ai componenti scelti e agli artefatti ad hoc; le decisioni mancanti
rimangono domande registrate. Non introduce un secondo planner o catalogo
canonico accanto ai proprietari esistenti.

**Trigger pubblico di avvio.** Deve esistere un ingresso dedicato, con identità
funzionale proposta `compose-process`, esposto dall'adapter come comando oppure
skill/workflow invocabile dall'utente. L'utente lo richiama con l'obiettivo in
testo libero, per esempio «costruisci un processo che analizzi questi documenti
e produca un report verificato». Il YAML non è un prerequisito per iniziare
l'intervista: è l'output del compositore e il successivo ingresso del runtime.
Nome registrato, sintassi e meccanismo effettivi vanno legati a ciascun host;
questa specifica non dichiara il comando già disponibile.

Il trigger legge il contesto e le decisioni applicabili, chiarisce destinazione
e criteri di successo e pone soltanto le domande necessarie nella forma della
sezione 4. Se l'utente indica un processo, una mappa o un'intervista esistente,
ne verifica l'identità e riprende dal checkpoint e dalle domande aperte, senza
creare una seconda intervista. Il coordinatore dispone dello stesso ingresso
interno quando il lavoro autorizzato richiede composizione: l'avvio manuale e
quello contestuale condividono metodo, memoria e contratto. La sola richiesta
di comporre non concede nuove autorizzazioni di esecuzione.

L'analogia con [l'invocazione di Wayfinder](https://github.com/mattpocock/skills/blob/main/skills/engineering/wayfinder/SKILL.md#invocation)
è l'ingresso esplicito da un'idea oppure da una mappa da riprendere. Il suo
`disable-model-invocation: true` resta una proprietà dell'upstream; il modulo
condiviso qui descritto espone anche il richiamo da parte del coordinatore.

**Discovery dell'harness.** L'adapter fornisce l'intero inventario disponibile di
strumenti, agenti/ruoli, skill, workflow, script e capacità dei provider. Ogni
voce distingue tipo, identità reale, origine e revisione, interfaccia o schema
degli argomenti, input/output, disponibilità e permessi. Dichiarato, installato,
utilizzabile e verificato sono fatti distinti. Una capacità sconosciuta rimane
una lacuna. Il motore riceve questo inventario attraverso il contratto
dell'adapter e non dipende da un catalogo specifico di Daodan.

La ricerca copre l'inventario con metadati e paginazione; legge corpi, contratti
e dettagli soltanto per i candidati pertinenti. Le parole chiave aiutano a
trovare candidati, poi il compositore verifica la corrispondenza con l'incarico.
Registra identità e revisioni scelte e rivalida i riferimenti se l'inventario
cambia prima dell'esecuzione o durante la ripresa.

**Riuso e job ad hoc.** Si riusano prima archetipi, strumenti e specialisti
pertinenti. Quando manca un componente adatto e il contratto lo permette, il
compositore può definire un nuovo incarico e il suo prompt, produrre uno script
o preparare una chiamata. Un job inline usa un executor registrato e consentito,
per esempio il worker isolato del controller, con obiettivo, input/output,
perimetro, controlli, capacità e budget espliciti. Il prompt è un dato del job;
l'incarico nuovo non simula l'esistenza di un agente registrato. Un job ad hoc
non sostituisce uno specialista obbligatorio né aggira un provider richiesto ma
indisponibile: quel caso segue il recupero del proprietario.

Gli script prodotti sono artefatti del run identificati da percorso e impronta,
con interprete, argomenti, input/output e verifiche dichiarate. Il grafo rende
esplicita la loro produzione e verifica prima dell'uso; l'executor esegue la
versione verificata entro le autorizzazioni applicabili. Le chiamate citano
strumenti o API realmente disponibili e i loro schemi, senza inventare nomi o
permessi. Parsing, composizione e sola verifica non eseguono gli script né le
chiamate di lavoro proposte; le operazioni di lettura e discovery necessarie
alla composizione seguono il perimetro già autorizzato. La generazione non
installa provider o dipendenze e non modifica permanentemente l'harness.

### Integrità, revisioni e loop

La validazione controlla schema, identità, componenti e capacità disponibili,
collegamenti degli input, dipendenze e limiti. I prerequisiti formano un DAG
verificato con `graphlib`. Il risultato distingue errore strutturale, requisito
non verificato e capacità non disponibile; una lacuna non diventa un successo.

Un loop è un costrutto dichiarato: corpo da ripetere, condizione d'uscita,
massimo di iterazioni e budget applicabile. Il corpo di ogni iterazione conserva
dipendenze acicliche. Condizioni e controlli usano dati e verificatori consentiti
dal contratto, senza valutare codice arbitrario incorporato nel YAML. Iterazioni
e retry hanno identità distinte e restano consultabili; raggiungere un limite
interrompe l'avanzamento con una causa, senza fingere raggiunto l'obiettivo.

Ogni esecuzione si lega alla versione e all'impronta della definizione YAML
ammessa, ai contratti, agli input e alle autorizzazioni applicabili. Una modifica
produce una nuova revisione, con riesame dei dipendenti e conservazione dei
risultati ancora validi; non modifica retroattivamente la definizione eseguita.

### Orchestrazione, memoria e passaggio tra sessioni

Il motore possiede la frontiera dei nodi pronti, le prese in carico e i tentativi.
Prima di avviare un job verifica input, dipendenze, autorizzazioni, binding,
isolamento, risorse e budget. Registra il tentativo prima del dispatch e collega
l'handle restituito dall'host al job e al tentativo. Le consegne e i controlli
competenti decidono il completamento; un turno finito non è una consegna.

Il **checkpoint** conserva il punto dell'esecuzione: revisione, nodi e tentativi,
handle attivi, risultati, domande, controlli e contabilizzazione. La **memoria**
conserva contesto, decisioni ed evidenze con fonte, perimetro e validità; prepara
il contesto pertinente senza trasformare un riepilogo in una nuova fonte
normativa. Non richiede di introdurre un servizio o un archivio vettoriale.
Entrambi vivono nella home persistente del progetto, condivisa tra worktree.

Il **session handover** trasferisce identità del processo e della revisione,
titolarità, checkpoint, riferimenti alla memoria e lavoro aperto. Prima di
riprendere, il nuovo coordinatore riconcilia handle, effetti e risultati: un job
ancora attivo non viene duplicato; un esito ignoto rimane tale fino al recupero.
La presa in carico impedisce a due sessioni di avviare lo stesso tentativo.

La **comunicazione tra agenti** è legata a processo, nodo e tentativo: mittente,
destinatario, contenuto o riferimento e identità del messaggio sono registrati,
con deduplicazione e consegna osservabile secondo le capacità dell'host. I
messaggi non sostituiscono risposte umane, autorizzazioni o gate. Una domanda
umana sospende i dipendenti e lascia proseguire soltanto il lavoro indipendente
ammesso, secondo le sezioni 5 e 6.

### Esecuzione e binding del model-router

`work-controller` possiede l'esecuzione reale. Gli adapter collegano il runtime
ai meccanismi verificati degli host: avvio e osservazione dei worker, isolamento,
selezione del modello e dell'effort, arresto, comunicazione e lettura dei consumi.
Le capacità mancanti sono dichiarate prima del dispatch coinvolto. Il motore
mantiene stato e decisioni; l'adapter applica le operazioni dell'host.

**L'executor è la sessione coordinatrice che segue il registro**, per decisione
dell'utente dello stesso giorno: legge dal registro la frontiera dei nodi pronti,
avvia gli agenti con il meccanismo nativo dell'host, e ammette le consegne e i
file di controllo e di coordinamento che gli agenti scrivono. L'esecuzione è un
normale processo di lavoro agentico: non la governa un consumo di token e non
richiede un servizio autonomo o un processo in background dopo la chiusura della
chat. L'executor è parte fondamentale del motore e si costruisce insieme a
composizione e validazione, non dopo. Gli agenti comunicano attraverso quei file
e il registro, che conserva tentativi, handle e consegne; una sessione successiva
riprende dallo stesso registro (handover, sopra).

Il **model-router mantiene il proprietario `model-routing@daodan`**. Il
coordinatore ne riusa classificazione, cataloghi, prezzi e selezione per ottenere
binding concreti, senza copiare quei dati e quella politica nel motore.
L'assorbimento del router previsto nella direzione esterna del 24 ottobre non
fa parte della reintegrazione; identità e contratti del provider restano validi.

Ogni job LLM, inclusi compositore, classificatore e verifiche semantiche, riceve
il proprio binding di modello ed effort secondo le regole applicabili del router.
Conta l'incarico concreto, con obiettivo, input, capacità, complessità e rischio:
lo stesso agente può usare modelli diversi per job diversi. Un nodo deterministico
non richiede un modello. L'assegnazione è derivata e si lega a nodo, tentativo,
richiesta, inventario e catalogo; non è una scelta unica per tutto il grafo.

Prima di dispatch e ripresa si verifica che il binding sia ancora applicabile e
che l'host possa applicarlo. Modello assegnato e modello effettivamente osservato
restano fatti distinti; discrepanze o assenza di prova sono lacune visibili.
Il gate corrente richiede conferma della proposta concreta. Un'eventuale delega
iniziale a una politica di routing, con modelli consentiti, limiti ed escalation,
richiede una decisione esplicita e il relativo contratto: questo documento non
la deduce dall'approvazione del processo e non la considera già implementata.

### Consumi, costi e budget

[ADR-0003](../../adr/ADR-0003-usage-ledger.md) conserva la proprietà del ledger e
delle regole di normalizzazione e prezzo. Il controller collega i consumi
osservati al job, al tentativo e all'handle dell'host; deduplica per identità della
sorgente anche dopo ripresa o handover. Include composizione, routing,
coordinamento, esecuzione, verifiche, iterazioni fallite e retry. Il lavoro non
attribuibile a un nodo rimane costo esplicito di coordinamento del processo.

La vista presenta consumi misurati, costo calcolato ai prezzi dell'endpoint con
le revisioni applicate e stime del lavoro futuro separate. I valori servono al
confronto dei processi; non sono una fattura. Sorgenti mancanti e prezzi ignoti
restano mancanti o parziali, mai zero. Una modifica dei prezzi non riscrive le
misure e le basi storiche del run.

Il budget è verificato prima di nuove ammissioni, comprese iterazioni e retry,
riusando gli avvisi e le autorizzazioni di aumento di ADR-0003. Un superamento
ferma nuove partenze; le operazioni già attive seguono le capacità di arresto
effettivamente provate. Il controllo non promette un tetto monetario esatto sulle
chiamate già in corso. Misure incomplete lasciano il budget non verificato;
un limite obbligatorio non può essere dichiarato rispettato senza evidenza.

### Distribuzione e costi

- Il compilatore e gli adapter di Daodan distribuiscono il runtime insieme al
  plugin. L'estrazione di `daodan-common`, un marketplace aggiuntivo e un pacchetto
  Deadly Brain separato erano costi della direzione esterna del 24 ottobre,
  sostituita dalla reintegrazione; non sono prerequisiti del motore in Daodan.
- I consumatori dichiarano `work-controller@daodan`. I pacchetti dei cinque host
  devono includere moduli, asset, launcher e contratto; registrazione e prove su
  host installati restano evidenze separate ([host](../../hosts.md)).
- `model-routing@daodan` mantiene identità e politica. Non viene rimosso né
  ricopiato dentro il motore per questa reintegrazione.
- La home `.daodan` del checkout principale mantiene registri e agenda. Lo store
  del processo usa `.daodan/processes`; nessuna migrazione riscrive in modo
  implicito archivi, definizioni ammesse o autorizzazioni pregresse.
- Il registro del run accetta le operazioni di consumatori diversi: dalla
  versione 2.1.0 di `work-controller` il consumatore sceglie il nome
  dell'operazione (lettere minuscole, cifre e trattini) e il motore ne controlla
  solo la forma, per decisione dell'utente del 25 ottobre 2026.

### Criteri di accettazione del motore

Questi scenari definiscono il lavoro futuro; non sono risultati già ottenuti.

| ID | Scenario | Risultato osservabile |
|---|---|---|
| WC-01 | Un'intervista, un archetipo e un file fornito descrivono lo stesso processo. | Producono o forniscono YAML equivalente, ammesso dallo stesso validatore. |
| WC-02 | Si richiede soltanto il check di integrità. | Il risultato contiene diagnosi; nessun job viene eseguito o instradato a un modello. |
| WC-03 | YAML malformato, componente inesistente, ciclo o input senza produttore e senza dichiarazione esterna. | L'ammissione è rifiutata con la causa precisa; un processo valido lega la versione e l'impronta eseguite. |
| WC-04 | Si eseguono un job singolo, un grafo e un loop. | Tutti entrano da YAML; il loop verifica uscita, iterazioni massime e budget, conservando ogni tentativo. |
| WC-05 | Si usa lo stesso agente in due job LLM diversi, accanto a un nodo deterministico. | I job ricevono binding propri di modello ed effort; il nodo deterministico non riceve un modello. |
| WC-06 | L'host non applica il modello richiesto oppure non espone una capacità necessaria. | Il limite impedisce il dispatch interessato o l'ammissione del risultato; nessuna esecuzione conforme viene dedotta. |
| WC-07 | Una sessione si interrompe con un worker attivo; un'altra prende in carico il processo. | Checkpoint e memoria vengono recuperati; l'handle è riconciliato prima della ripresa, senza duplicare job o costi. |
| WC-08 | Due sessioni reclamano lo stesso tentativo oppure un messaggio viene consegnato due volte. | Una sola presa in carico e una sola applicazione del messaggio; origine e destinazione restano osservabili. |
| WC-09 | Una risposta o una nuova revisione YAML cambia un input. | I dipendenti sono riesaminati; le revisioni e le evidenze precedenti rimangono consultabili. |
| WC-10 | Un job fallisce e viene ritentato; i log sono raccolti due volte. | Ogni tentativo conserva consumi e risultato; le righe di origine sono contate una sola volta, inclusi costi di routing e coordinamento. |
| WC-11 | Manca un prezzo o una fonte di consumo; il budget è raggiunto. | Totale parziale o non misurato esplicito; nessuna nuova ammissione oltre il limite senza autorizzazione, nessuno zero inventato. |
| WC-12 | Un processo documentale viene eseguito senza il task cycle di Daodan. | Il nucleo non impone branch, worktree, ADR, commit o controlli specifici del codice; applica i contratti del processo. |
| WC-13 | L'utente invoca l'ingresso di composizione con un obiettivo e nessun YAML. | Si avvia l'intervista con contesto e domande persistenti; l'esito è YAML, senza avvio implicito del processo. |
| WC-14 | L'utente o il coordinatore richiama il compositore per un processo già aperto. | Si riprendono identità, decisioni, checkpoint e domande applicabili, senza duplicare l'intervista o inferire risposte. |
| WC-15 | Nell'inventario esiste uno specialista o uno strumento pertinente. | Il compositore lo trova e riusa con identità, metodo e interfaccia verificati; un cambiamento dell'inventario richiede rivalidazione prima dell'uso. |
| WC-16 | Nessun componente soddisfa un incarico e il contratto permette un job ad hoc. | Il YAML contiene un job inline con executor disponibile, prompt, input/output e controlli; non occorre inventare un ruolo o installare un nuovo plugin. |
| WC-17 | Una chiamata cita uno strumento inesistente o argomenti non validi; oppure lo script differisce dalla versione verificata. | L'operazione non è ammessa e la causa è esplicita; un job ad hoc non aggira l'assenza di un provider obbligatorio. |
| WC-18 | La composizione propone uno script o una chiamata ad hoc. | L'artefatto e i suoi controlli compaiono nel grafo; parsing, composizione e sola verifica non eseguono il lavoro proposto. |

### Questioni aperte

- **Una domanda per turno o tutta la frontiera in un round?** La sezione 4 e
  l'intervista del task cycle chiedono una domanda per turno. L'intake Office di
  Mukade e il grilling di Wayfinder pongono in un solo round tutte le domande già
  sbloccate. Nella sessione Mukade è stato raccomandato il round. Il contratto
  delle domande regge entrambe le forme: `ask` registra ogni domanda e `answer`
  ogni risposta. La scelta cambia solo la prosa dei metodi che chiedono.
- Schema YAML concreto per job, grafi e loop; parser da verificare prima
  dell'adozione. Il formato YAML obbligatorio non è più una questione aperta.
- Nome e binding dell'ingresso pubblico di composizione (`compose-process`
  proposto), da registrare e verificare sugli host insieme al richiamo interno.
- Prove delle capacità degli host per l'executor: dispatch, isolamento,
  selezione del modello, arresto e lettura dei consumi su ciascuno dei cinque.
- Conferma per singolo binding oppure futura delega esplicita a una politica
  di routing; fino a tale decisione resta il gate corrente.
- Repository e proprietario sono fissati dalla reintegrazione del 25 ottobre:
  `work-controller@daodan`, con licenza e provenienza conservate. La rimozione
  della cartella locale o del repository remoto separato è un'operazione
  distinta, subordinata a trasferimento verificato e autorizzazione specifica.
