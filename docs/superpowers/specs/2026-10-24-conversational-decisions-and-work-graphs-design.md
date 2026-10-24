# Chiarimenti, mappe decisionali e grafi di lavoro

Data: 24 ottobre 2026. Stato: **specifica proposta; integrazione da implementare e verificare**.

Questa specifica estende [ADR-0001](../../adr/ADR-0001-work-graph-step0-llm.md)
e il [disegno dei grafi di lavoro](2026-10-20-system1-work-graph-composition-design.md).
Definisce quando Daodan deve coinvolgere l'utente, come scegliere la forma della
conversazione e come riprendere il lavoro. Non introduce un nuovo motore di grafi.

[ADR-0002](../../adr/ADR-0002-work-controller.md), proposto, sposta nel plugin
`work-controller` le responsabilità che qui sono attribuite a `work-controller`,
insieme a chiarimenti, intervista generica, mappa e composizione dei grafi.

**Il bisogno di una decisione umana attiva un chiarimento proporzionato:** una
domanda diretta, un'intervista mirata oppure una mappa decisionale. I prototipi dei
grafi operativi continuano a descrivere metodi, dipendenze, consegne e verifiche.
La mappa decisionale, metodo proprio di Daodan ispirato a Wayfinder, aiuta a
esplorare le decisioni che determinano quel lavoro.

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

Il metodo proprietario dell'attività decide quali input servono. `project-lifecycle`
coordina il piano e l'intervista del task cycle; gli altri metodi richiamano lo
stesso contratto di chiarimento senza duplicare un proprio framework di intervista.
`work-controller` possiede persistenza, ripresa e contabilizzazione. `senior-review`
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

La mappa è un metodo di Daodan: il coordinatore la apre o la riprende da sé quando
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

## 7. Mappa decisionale: idee di Wayfinder, metodo di Daodan

Decisione del 24 ottobre 2026: Daodan scrive un proprio metodo di mappa decisionale
ispirato a Wayfinder (`mattpocock/skills`, licenza MIT), nella modalità
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

Oggi `work.toml` e `run_state.py` già conservano domande per gli host senza
strumento di interrogazione e le espongono alla ripresa. Questo non prova ancora
l'attesa selettiva dei nodi, i legami di validità o la mappa decisionale qui
descritti. L'assemblaggio canonico dei reviewer è invece presente; va distinto
dalla proposta semantica a prompt e dalle capacità del futuro runtime dei grafi.

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
