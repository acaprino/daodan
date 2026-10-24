> Stato: proposta storica. Fa fede [Reviewer specializzati e composti](2026-10-22-specialized-reviewers-design.md): prima specialisti canonici, poi reviewer ampi generati dalla loro unione, riusando il registro esistente. Le strutture aggiuntive qui proposte non sono requisiti impliciti.

# Authoring, generazione e promozione del catalogo dei reviewer

**Stato:** Proposed. Specifica di progetto; questo documento non implementa il flusso descritto.
**Data:** 22 ottobre 2026.
**Documento principale:** [Ridisegno del sistema di review](2026-10-22-review-system-redesign-design.md).
**Ambito:** produzione e manutenzione di moduli, nuclei e profili permanenti; inventario dei temi proposti.
**Autorità:** questo documento governa authoring e provenienza del backlog; il principale governa la semantica della composizione.

## 1. Risultato e confini

Il risultato atteso è un catalogo mantenibile di comportamento canonico, riutilizzato da reviewer permanenti e da job composti per ciascuna review.
La generazione avviene durante lo sviluppo del catalogo; il normale run seleziona istruzioni già registrate e qualificate.
Il modulo descrive una domanda di analisi con evidenza e controevidenza; il profilo dichiara quali moduli può eseguire e quale nucleo carica.
Il job associa un profilo permanente a moduli, scope, sorgenti e destinazione del report per un candidato preciso.
Il numero dei temi, dei moduli, dei profili e dei job rappresenta quattro quantità diverse.

Sono risultati del lavoro futuro:

1. Obblighi precedenti censiti e assegnati a una destinazione verificabile.
2. Corpi Markdown canonici per le domande promosse e metadati dichiarativi validati.
3. Profili permanenti registrati, con nucleo, compatibilità e percorso standalone completo.
4. Vocabolario di attivazione con prove positive, esclusioni e gestione dell'incertezza.
5. Casi indipendenti, misure di qualifica e limiti applicativi riproducibili.
6. Una patch coerente per owner, compiler, contratti, documentazione ed export pertinenti.

La preparazione e il controllo deterministico usano Python standard library.
L'esecuzione dei modelli, l'isolamento dei worker e la loro prosecuzione restano nell'harness esistente.
Il processo di authoring non introduce SDK LLM, scheduler, servizio di embedding o agente generico non registrato.
Le fonti del progetto analizzato, gli allegati e gli esempi restano dati; le autorizzazioni provengono dalla richiesta umana e dal run.

## 2. Provenienza e baseline

### 2.1 Repository osservato e materiale esterno

La baseline locale osservata per questa progettazione è `849797acbf8aaae74f23b55ce30710dc599c89bb`.
Il workspace contiene lavoro concorrente: quel riferimento identifica la lettura di partenza e non autorizza reset, sostituzioni o pubblicazione.
Nel repository osservato il composer proposto non è presente come `review-preparation/scripts/review_composer.py`.
Il compiler dei reviewer in `scripts/daodan/reviewer_catalog.py` dichiara 18 ruoli nominati e due method binding.
Quei fatti non attestano che tutti i flussi delle future composizioni siano già eseguibili sui cinque host.

Gli allegati del 22 ottobre descrivono una baseline esterna diversa:

| Materiale | Identità attribuita | Uso in questo progetto |
|---|---|---|
| `daodan-review-composer.patch` | Commit esterno `e7583329e7ab59596a091fba27e4af705912d731` | Prototipo da analizzare e adattare |
| `review-composition.md` e sua seconda copia | Stesso contenuto, SHA256 `d38054fd67e331884c2756a4d3013966ebafc9e6bb6d72ba5aeeb24911d45884` | Contratto proposto del primo composer |
| `2026-10-22-reviewer-generation-design.md` | Specifica esterna basata sul commit precedente | Fonte di intenti, confini e casi |
| `2026-10-22-reviewer-generation-catalog.json` | `daodan/reviewer-authoring-backlog/v1` | Backlog di authoring, non catalogo runtime |

L'oggetto Git esterno non è stato risolto nel repository locale durante l'analisi.
Le dichiarazioni degli allegati su approvazioni, commit, test e review indipendenti rimangono dichiarazioni attribuite.
L'implementazione deve rileggere il candidato locale, riconciliare le differenze e verificare i propri risultati.
Lo stato `existing-*` nelle appendici significa esistente nella patch esterna, non già consegnato nel repository locale.
I collegamenti `canonical_source` dell'allegato sono indicazioni di authoring; non diventano path runtime installati.

### 2.2 Contabilità del backlog

| Inventario | Conteggio | Significato |
|---|---:|---|
| Temi `T01` a `T50` | 50 | Richieste di copertura attribuite alla mappa esterna |
| Supplementi `S01` a `S03` | 3 | Richiami SQL, AMQP e AI |
| Record nel backlog | 66 | Sottoinsieme dei base più specialisti proposti |
| `existing-base` | 9 | Base richiamati dai temi |
| `existing-specialization` | 8 | Specialisti SQL e AMQP della patch esterna |
| `planned-base` | 1 | Base del nuovo owner accessibility |
| `planned-specialization` | 48 | Specialisti da scrivere e qualificare |
| Base esterni assenti dal backlog | 11 | Da preservare esplicitamente |
| Catalogo prospettico conservativo | 77 | 66 record più gli 11 base preservati |
| Moduli ulteriori della riorganizzazione | 3 | Concurrency, prestazioni generali e percorsi d'interazione critici |

Se nessun'altra estrazione divide o riunisce moduli, la proiezione è 80 definizioni.
77 e 80 sono contabilità di progetto, non obiettivi numerici né prove di completezza o qualità equivalente.
Ogni successivo splitting o accorpamento aggiorna inventario e matrice degli obblighi con una motivazione.
Le appendici conservano gli ID originali; le correzioni di selettori e mandato sono delta espliciti.
Un modulo base non referenziato direttamente da un tema rimane valido quando protegge un obbligo del profilo.

## 3. Oggetti canonici e responsabilità

| Oggetto | Proprietà necessarie | Responsabile |
|---|---|---|
| Tema | ID, origine, bisogno, stato di destinazione | Coordinatore del catalogo |
| Obbligo precedente | Fonte e locator, significato, condizioni, destinazione | Owner del comportamento |
| Nucleo | Metodo, regole probatorie, confini, output e gestione lacune | Owner permanente |
| Modulo | ID, corpo canonico, attivazione, prerequisiti, casi | Owner del comportamento |
| Profilo | Identità registrata, nucleo, moduli compatibili, preset standalone | Provider del ruolo |
| Job | Candidato, profilo, assegnazioni, input ammessi, report | Composer e harness nativo |
| Qualifica | Versioni, corpus, modello, ampiezza e risultati osservati | Valutazione indipendente |

L'owner del modulo rimane unico e riconoscibile anche quando diversi profili permanenti dello stesso owner lo supportano.
La compatibilità non viene dedotta dal nome del ruolo o dalla somiglianza dei prompt.
Il registro deve risolvere nucleo, corpi, reference obbligatorie, moduli compatibili e preset standalone di ogni profilo.
La composizione conserva packing per stesso owner, stessa lente e stesso input mode.
Un nuovo profilo non autorizza aggregazione fra owner o contaminazione di un passaggio blind.
La semantica dei floor come obblighi di copertura è definita nel documento principale e mappata nei profili dal registro.

La qualifica del modulo misura se la domanda, l'evidenza e le esclusioni sono corrette.
La qualifica di esecuzione misura se un profilo e un modello svolgono quel lavoro entro il perimetro provato.
Il router usa disponibilità e qualifiche; la scelta del modello non rende corretto un modulo difettoso.
Le qualifiche si riferiscono a versioni precise di nucleo, moduli, fonti, corpus e adattamento host.

## 4. Ammissione del lavoro di authoring

### 4.1 Classificazione della richiesta

| Condizione dimostrata | Operazione proposta | Uscita necessaria |
|---|---|---|
| Stessa causa, stessa domanda e stessa evidenza | `amend-existing` | Delta degli obblighi con ID mantenuto |
| Stesso owner, domanda selezionabile distinta | `add-module` | Nuovo modulo e casi di attivazione |
| Tecnologia diversa, mandato invariato | `specialize-module` | Variante e condizioni che la distinguono |
| Corpo atomico da rendere selettivo | `extract-owner` | Matrice completa degli obblighi e profilo |
| Mandato senza owner adeguato | `propose-owner` | Confine, ruolo, registro, corpus e integrazioni |
| Evidenza o autorizzazione insufficiente | `blocked` | Lacuna e requisito concreto per proseguire |

La decisione è motivata con i moduli vicini e un esempio nominale, uno di confine e uno di esclusione.
Un nuovo nome di tecnologia non basta a giustificare un owner.
Un nuovo owner richiede mandato distinto, risultati non duplicati, corpus proprio e necessità di un metodo autonomo.
L'intervento sui 50 temi richiede una destinazione esplicita per ciascuno; nessun tema produce automaticamente un ruolo.
L'inventario conserva anche temi rinviati, accorpati o già protetti, con stato e ragione visibili.

### 4.2 Pacchetto riproducibile

Prima della generazione preparare un pacchetto confinato al run e legato al candidato:

| Campo del pacchetto | Contenuto e controllo |
|---|---|
| `request` | Operazione, tema, esito desiderato e autorizzazione pertinente |
| `candidate` | Progetto/worktree, commit, snapshot e dirty state rilevanti |
| `source_obligations` | Ogni obbligo estratto con fonte, locator e significato |
| `owner_contract` | Mandato, esclusioni, nucleo, input e report canonici |
| `neighbors` | Moduli e profili con sovrapposizione plausibile |
| `evidence` | Fonti tecniche, sorgenti esemplificativi, versione e provenienza |
| `negative_cases` | Casi corretti, near miss, esclusioni e limiti |
| `activation` | Tag proposti, prove positive/negative e proprietà impattate |
| `qualification` | Corpus separato, oracoli, metriche e budget fissati prima |
| `write_scope` | File posseduti e path di output permessi |
| `fingerprints` | Hash di ogni input realmente usato, incluso nucleo e reference |

Le fonti tecniche devono essere verificate presso documentazione ufficiale o altra fonte primaria pertinente.
Registrare prodotto, versione, URL o locator, data della verifica e affermazione sostenuta.
Una fonte non verificata resta `unknown`; un requisito tecnico dipendente da essa impedisce la qualifica pertinente.
Questa specifica non incorpora nuove prescrizioni di protocolli, standard di accessibilità, sicurezza o compatibilità.
Gli esempi del backlog sono domande da sviluppare con quelle fonti, non autorità tecniche autosufficienti.
Il pacchetto include il materiale necessario al problema assegnato, senza caricare l'intero catalogo o repository nel generatore.

## 5. Generazione e riscrittura dei corpi

### 5.1 Comportamento in Markdown

Il corpo deve permettere un'analisi utile anche con zero finding.
Deve chiarire cosa seguire nel sorgente, cosa proverebbe il difetto e cosa lo smentirebbe.
L'esito richiesto distingue rischio derivato, difetto dimostrato, dato osservato e limite dell'evidenza.
Ogni domanda conserva il suo owner; problemi adiacenti diventano riferimenti incrociati verificabili.
La brevità si ottiene rimuovendo ripetizioni del nucleo, non eliminando prerequisiti o modalità di fallimento.
Applicare il mantra della sezione 1.3 della specifica principale: ogni istruzione aggiunta soddisfa un obbligo non già espresso nella fonte canonica e il corpo richiede output compatti con prove e limiti intatti.
150–300 token stimati per specialista è una guida editoriale iniziale da qualificare, non un criterio di promozione autonomo.

Template di corpo da adattare al modulo, con una sola intestazione risolvibile:

```markdown
## module-id

Obiettivo: preservare l'invariante dichiarato nel percorso assegnato.
Attivazione: usare il bisogno e l'evidenza che rendono applicabile il controllo.
Tracciare ingressi, trasformazioni, confini e uscite fino alla condizione decisiva.
Confrontare il comportamento effettivo con il contratto e i percorsi alternativi.
Per ogni ipotesi cercare la protezione equivalente e le condizioni che la rendono valida.
Sostenere un finding con trigger concreto, percorso raggiungibile, conseguenza e locator.
Per un'affermazione di assenza dichiarare quali istanze e percorsi sono stati esaminati.
Registrare sorgenti o prerequisiti mancanti come copertura parziale, indicando cosa manca.
Rispettare i confini dell'owner e il report nativo del profilo.
Produrre una sola volta gli esiti e le prove richiesti; usare riferimenti ai dettagli canonici nei riepiloghi.
```

Il template mostra la struttura; un corpo promosso sostituisce ogni elemento generico con controlli pertinenti.
Una lista di parole chiave o un invito generico a cercare bug non costituisce un metodo.
Un singolo modulo può avere più controlli quando condividono attivazione, evidenza e conclusione.
Domande con prerequisiti, protocolli o input mode incompatibili richiedono separazione esplicita.
Una riscrittura conserva locator della fonte precedente e confronto degli obblighi prima/dopo.

### 5.2 Metadati dichiarativi separati

Il backlog può contenere domanda, evidenza e controevidenza come materiale di authoring.
La promozione sposta il comportamento nel Markdown e proietta solo campi ammessi nel catalogo runtime.
Il runtime non deve trattare `question` o `activation_and_required_evidence` del backlog come prompt alternativo.
Schema e loader dei profili saranno versionati insieme al loro registro; il v1 esterno non seleziona da solo nuclei compatti.

| Contratto proposto | Versione | Uso nell'authoring |
|---|---|---|
| Contesto di review | `daodan/review-context/v2` | Evidenza, scope e classificazione validati contro vocabolario |
| Moduli runtime | `daodan/review-modules/v2` | Metadati dichiarativi proiettati dopo la promozione |
| Composizione runtime | `daodan/review-composition/v2` | Job derivati da moduli e profili compatibili |
| Profili permanenti | `daodan/review-profiles/v1` | Nucleo, compatibilità e preset standalone |
| Vocabolario | `daodan/review-vocabulary/v1` | Tag, proprietà, relazioni e condizioni di incertezza |
| Policy content | `daodan/review-content-policy/v1` | Preparazione senza diff e obblighi di verifica, definiti nel documento principale |
| Backlog di authoring | `daodan/reviewer-authoring-backlog/v1` | Proposte, stati e provenienza; separato dal runtime |

Le versioni v2 sono incompatibili con i contratti runtime della prima patch esterna.
Un backlog valido non viene passato direttamente al composer; la proiezione produce il contratto runtime appropriato.
Il loader distingue contratto dichiarato, disponibilità locale e registrazione nell'host attivo.

| Campo dichiarativo | Regola di validazione |
|---|---|
| `id` | Unico, stabile, kebab-case; rinomina accompagnata da migrazione |
| `owner` / binding equivalente | Identità canonica registrata e provider disponibile |
| `lens` | Famiglia coerente con il mandato del proprietario |
| `body_ref` | Corpo Markdown unico e confinato nel package spedito; conversione esplicita del campo `brief` del backlog esterno |
| `when_any` | OR di tag registrati con evidenza nello scope |
| `when_all`, `unless` | Congiunzione richiesta ed esclusioni dimostrate, secondo il predicato completo della specifica principale |
| `impact_policy`, `impact_any` | `always` oppure `intersects` con proprietà non vuote e motivate; convertire esplicitamente l'uso della lista vuota nella patch |
| `base` / obblighi equivalenti | Relazione esplicita con il floor di copertura |
| `input_mode` e indipendenza | Compatibili con profilo, moduli e fase nativa |
| Prerequisiti e reference | Risolvibili, necessari e conteggiati nei costi |
| Compatibilità profili | Dichiarata e verificata nel registro compilato |

I nomi effettivi dei campi sono chiusi nel contratto versionato; gli esempi di progetto non autorizzano campi extra.
Hash, token stimati e riferimenti installati vengono prodotti da loader/compiler sulle fonti reali.
Un costo assente rimane sconosciuto; una stima non rappresenta consumo misurato o capacità del modello.

### 5.3 Prompt circoscritto per l'autore

```text
Produce one bounded authoring proposal from the prepared package.
Choose amend-existing, add-module, specialize-module, extract-owner, propose-owner or blocked.
Preserve every supplied source obligation or give its verified equivalent destination.
Use the registered owner, profile constraints, vocabulary and admitted technical sources.
Return declarative metadata, one operational Markdown body and an explicit coverage delta.
Minimize new code, instructions and requested output while preserving every required protection and verifiable evidence.
Include positive, corrected, near-miss, unknown-input and dependency-only case proposals.
Explain neighboring-owner boundaries and source claims that remain unverified.
The proposal does not run reviewers, select an unbound model or grant mutation authority.
```

Una chiamata produce un modulo o un piccolo gruppo con stesso owner ed evidenza comune.
Il batch iniziale di 1–3 moduli è un'ipotesi da misurare sul profilo usato per l'authoring.
Il generatore consegna una proposta; la sua autovalutazione e i suoi casi non sostituiscono l'oracolo indipendente.
Il budget e il massimo numero di riparazioni di formato vengono stabiliti prima del run.
Esaurito il budget, conservare output e stato incompleto; il ciclo non avvia una catena ricorsiva di riscrittori.

## 6. Segnali, impatto e assenze

### 6.1 Vocabolario chiuso

Ogni tag promosso ha ID, definizione, prove positive, condizioni di esclusione e regola di incertezza.
La classificazione usa tre esiti: applicabile, escluso con evidenza sufficiente, sconosciuto.
Il validatore rifiuta tag e proprietà fuori registro come errori strutturali di input.
Lo stato unknown riguarda soltanto un segnale o una proprietà registrati la cui applicabilità o presenza non è ancora risolta.
Un refuso non viene trattato come prova che una tecnologia o una responsabilità sia assente.
`when_any` indica OR fra tag esatti; congiunzioni e relazioni di implicazione sono dichiarate nel registro.
Il validatore controlla le relazioni necessarie; l'autore del contesto non deve ricordarle soltanto dalla prosa.
Esempio: SQL implica un ambito di codice e persistenza; un contratto AMQP richiede evidenza del protocollo e del contratto.

Il backlog contiene 61 tag distinti; 45 sono nuovi rispetto al catalogo della patch esterna.
Questa espansione richiede un registro e casi di classificazione, non 45 nuove euristiche basate sul nome del file.
`ui` e `user-interface` hanno perimetri differenti: la superficie UI statica può essere rilevante senza asincronia.
La preparazione deve rappresentare quel bisogno senza inventare un segnale di race.
La presenza di una dipendenza in un package estraneo non attiva il controllo nello scope esaminato.

### 6.2 Controlli richiesti dall'assenza

Un controllo si attiva per il bisogno di una protezione, non soltanto per l'esistenza della sua implementazione.
Un inventario di dati recuperabili può richiedere backup anche quando nessuna configurazione di backup è presente.
Un ingresso con attesa esterna può richiedere esaminare deadline anche quando manca un timeout esplicito.
Un'azione sensibile può richiedere audit anche quando non esiste un sink con un nome riconoscibile.
I test di selezione devono contenere protezione presente, equivalente, assente e requisito sconosciuto.
Quando il requisito manca, la classificazione registra l'incertezza; non inventa un obbligo legale o di prodotto.
Le assenze dichiarate richiedono perimetro di ricerca, rappresentazioni alternative considerate e fonti esaminate.

### 6.3 Correzione dei changeset di sole dipendenze

I 49 record `planned-*` dell'allegato condividono sette proprietà di impatto e omettono tutti `dependencies`.
Quel default non è adottabile come selettore canonico: un aggiornamento di libreria può modificare garanzie senza cambiare il corpo locale.
Il riesame copre anche tutti i base e gli otto specialisti importati dalla patch, SQL e AMQP inclusi; lo stato existing non esenta dalla qualifica.
Prima della promozione valutare `dependencies` per ogni famiglia con engine, framework, driver, runtime o configurazione indiretta pertinenti.
La scelta positiva deve descrivere il percorso concreto; la scelta negativa deve avere un caso di esclusione motivato.
In presenza di impatto ignoto, conservare il gap e la domanda da risolvere.
L'obbligo di valutare questa proprietà non significa attivare ogni modulo per ogni lockfile del monorepo.

| Famiglia | Caso di aggiornamento da includere nella qualifica |
|---|---|
| Security e AI | Libreria di sessione, validazione o SDK che modifica il confine di fiducia |
| Dati e asincrono | Driver, ORM o client che modifica transazioni, retry, pool o serializzazione |
| UI e accessibility | Componente, runtime o asset che modifica semantica, stile effettivo o interazione |
| Platform e recovery | Integrazione che modifica configurazione, deploy, esportazione o recupero |
| Testing e contratti | Runner, validator o harness che modifica la protezione o il significato dell'oracolo |

I casi indicano domande da verificare; non affermano comportamento di una libreria o versione concreta.
La qualifica comprende aggiornamento pertinente, aggiornamento estraneo e aggiornamento con effetti non risolvibili.
Le proprietà body, interface, effects, schema, configuration, structure e instructions vengono motivate con lo stesso rigore.

## 7. Riscrittura degli owner e nuovi ruoli permanenti

### 7.1 Estrazione senza perdita amministrativa

La matrice degli obblighi è necessaria prima di sostituire un corpo atomico con nucleo e moduli.
Ogni riga contiene `old_obligation`, fonte/locator, `new_location`, attivazione, evidenza e caso di qualifica.
La destinazione è nucleo, modulo base, modulo condizionale o obbligo equivalente già posseduto, con prova dell'equivalenza proposta.
Un obbligo senza destinazione impedisce la promozione del profilo estratto.
Una corrispondenza testuale completa dimostra la migrazione amministrativa, non recall equivalente.
La qualifica del flusso e dei difetti indipendenti rimane necessaria dopo la migrazione.

Il nucleo conserva metodo, evidenza, confini, report, gestione dei prerequisiti e regole di prosecuzione.
I moduli conservano le domande specialistiche selezionabili; reference comuni hanno un solo proprietario.
Il preset standalone carica la preparazione e la selezione necessarie o un preset completo qualificato.
Un'invocazione senza composition non deve avviare un nucleo privo delle domande richieste.
Il preset light è distinto: conserva il singolo reviewer e la compatibilità qualificata specificata nella sezione 5.2 del documento principale, senza attivare il fan-out dello standalone completo.
I tre moduli ulteriori di riorganizzazione sono elencati nell'appendice D.
Le regole di compatibilità e la destinazione di tutti gli obblighi sono sviluppate nel [progetto di riorganizzazione](2026-10-22-reviewer-reorganization-design.md).

### 7.2 Nuovo owner accessibility

`senior-review:accessibility-auditor` è un'identità proposta e deve essere registrata esplicitamente.
Possiede accessibilità del percorso e usabilità tecnica dei punti d'ingresso critici, compreso un blocco statico da CSS o overlay.
Il modulo `interaction-critical-paths` è distinto dalle race temporali e dai problemi generali di control flow.
L'owner riceve un nucleo, il modulo base, i due specialisti a11y e il modulo dei percorsi critici.
Una singola causa ha un finding primario e riferimenti agli owner adiacenti; non si duplica il difetto per aumentare la copertura apparente.

La creazione del ruolo deve aggiornare in modo coordinato:

1. Corpo del ruolo nel kernel e componenti dichiarati in `plugin.toml`.
2. Registro dei reviewer, profilo permanente, nucleo, compatibilità e preset standalone.
3. Selezione, obblighi di copertura, input e reporting nei metodi pertinenti.
4. Dipendenze e capacità realmente necessarie, senza introdurre provider companion impliciti.
5. Compiler, risorse di dispatch e riferimenti installati di ciascun host.
6. Casi di estrazione/selezione, qualifica semantica, adattamento e prove operative disponibili.

Le fonti ufficiali, il target di accessibilità e i limiti delle prove devono essere acquisiti durante l'authoring.
Lettura statica, test automatici, browser e tecnologie assistive sono classi distinte di evidenza.
Un percorso utilizzabile o due specialisti a11y non attestano conformità complessiva a uno standard.
I moduli recovery, retention e AI rimangono sotto gli owner assegnati; il backlog non propone altri tre owner autonomi.

## 8. Stati e controlli di transizione

| Stato | Criterio d'ingresso | Azione ammessa e criterio d'uscita |
|---|---|---|
| `proposed` | Tema e operazione identificati | Preparare pacchetto e decisione di ownership |
| `prepared` | Input confinati e fingerprint completi | Generare o riscrivere la bozza assegnata |
| `draft` | Metadati e corpo prodotti | Eseguire controlli statici e correggere nel budget |
| `validated` | Schema, path, ID, obblighi e reference risolti | Richiedere review semantica e corpus indipendente |
| `qualification-pending` | Casi, oracoli e policy fissati | Eseguire la valutazione tramite harness esistente |
| `qualified` | Gate pertinenti passati con limiti dichiarati | Preparare patch e verificare integrazioni |
| `promoted` | Patch integrata e registri/export verificati | Rendere selezionabile soltanto il perimetro qualificato |
| `blocked` | Prerequisito, decisione o capacità essenziale assente | Conservare artefatti e requisito di ripresa |
| `rejected` | Proposta non conforme o mandato duplicato | Conservare ragione e destinazione degli obblighi |
| `superseded` | Una proposta successiva ne assume gli obblighi | Collegare identità e delta di copertura |
| `deprecated` | Uso nuovo disabilitato con percorso di migrazione | Verificare consumatori e obblighi sostitutivi |
| `retired` | Consumo concluso e protezioni migrate | Applicare la disposizione esplicitamente autorizzata |

Una modifica di input invalida la qualifica coinvolta e riporta l'oggetto allo stato più precoce necessario.
Cambiare nucleo o reference obbligatoria può invalidare più moduli e profili; il registro deve rendere visibile quell'impatto.
La selezione di un modello diverso richiede la qualifica di esecuzione pertinente; non riscrive lo stato semantico del modulo.
La promozione in un ramo non equivale a pubblicazione su un marketplace o prova di esecuzione installata.
Una mancata consegna, un turno concluso o un checker strutturale verde non producono `qualified`.
Ogni transizione registra autore del run, candidato, artefatti, esito, lacune e fonte dell'autorizzazione necessaria.

Gli stati persistono nell'artefatto di authoring posseduto dal run, non in `AGENTS.md` o nel corpo delle istruzioni permanenti.
Il catalogo promosso contiene la versione del comportamento; lo storico di tentativi e costi rimane nel run con provenienza.
Una bozza respinta può essere ripresa con un nuovo pacchetto, conservando il legame alla proposta precedente.
L'autore confronta prima gli input correnti e poi decide la fase da ripetere; non riusa un esito solo perché il nome del file è identico.

## 9. Helper deterministico di authoring

L'helper proposto è `scripts/reviewer_authoring.py`, superficie da implementare nel toolchain standard library.
Se una sua parte deve essere usata dai package installati, quella parte vive sotto una skill e viene spedita dal compiler.
L'helper prepara e verifica artefatti; il chiamante conserva esecuzione dei modelli, permessi e decisione di promozione.
Nessun comando dell'helper viene presentato come già disponibile nella baseline locale.

| Operazione proposta | Input | Output e criterio di completamento |
|---|---|---|
| `prepare` | Richiesta, backlog, registro, sorgenti e root posseduto | Pacchetto e manifest degli input, oppure blocco motivato |
| `check` | Pacchetto, bozza, vocabolario e candidato corrente | Problemi strutturati con locator, senza qualificare semanticamente |

Entrambe le operazioni validano identità di progetto e appartenenza dei path prima della lettura o scrittura di output.
Un path relativo viene risolto contro il root esplicito; symlink e destinazioni normalizzate devono restare nel perimetro consentito.
Gli input vengono letti come dati; codice negli allegati non viene importato o eseguito per validarli.
L'helper usa scrittura atomica degli output posseduti e preserva bozze e fasi riuscite prima di un errore.
Gli errori identificano ID, campo e locator; output troncati o mancanti conservano uno stato incompleto.

Il checker statico deve coprire almeno:

- Schema e campi ammessi; unicità degli ID e distinzione fra kind di componenti.
- Risoluzione di owner, profili, moduli, obblighi e riferimenti tema/modulo in entrambe le direzioni.
- Corpo Markdown unico, reference spedite, path confinati e assenza di segnaposto.
- Tag/proprietà registrati, relazioni fra segnali e casi per l'incertezza.
- Matrice completa di migrazione dei base, isolamento, indipendenza e obblighi obbligatori.
- Costi noti o esplicitamente sconosciuti, con inventario di nucleo e reference.
- Provenienza delle fonti e separazione fra casi proposti e corpus indipendente.
- Fingerprint corrente degli input, senza assumere che un commit identico implichi file locali immutati.

Il checker non giudica verità dei finding, adeguatezza semantica dei tag, equivalenza o qualità del modello.
Quei limiti devono essere esposti nell'output, insieme a ciò che è stato effettivamente controllato.

`prepare` non seleziona un modello e non avvia generazioni; il chiamante può assegnare il pacchetto a un autore umano o a un worker autorizzato.
`check` conserva gli errori di ciascuna bozza senza sovrascrivere il pacchetto originale o dichiarare promozione automatica.
Il manifest di risultato distingue input letti, controlli eseguiti, controlli non disponibili e artefatti prodotti.
Il front-end può preparare contenuto della patch e elenco di destinazioni per la revisione finale.
L'applicazione della patch avviene soltanto nel workspace assegnato all'implementazione, dopo il controllo degli input correnti.
Una mancata corrispondenza di snapshot conserva la bozza come dato e richiede riconciliazione; non attiva un merge cieco.

## 10. Qualifica e promozione

### 10.1 Pacchetto minimo di casi

| Famiglia di caso | Scopo della prova |
|---|---|
| Difetto nominale | Il controllo trova una violazione concreta con evidenza corretta |
| Caso corretto | La protezione effettiva viene riconosciuta senza falso positivo |
| Near miss | Una somiglianza lessicale o strutturale non basta a dichiarare il difetto |
| Protezione assente | Il bisogno attiva il controllo anche senza file/configurazione dedicati |
| Prerequisito ignoto | La lacuna rimane visibile e impedisce conclusioni universali |
| Impatto cross-scope | Producer, consumer o rappresentazione alternativa restano esaminabili |
| Solo dipendenze | Il selettore conserva gli specialisti pertinenti o registra incertezza |
| Budget ridotto | Il piano divide o blocca senza perdere obblighi |
| Più moduli insieme | Le domande mantengono profondità, confini e indipendenza richieste |
| Modalità full/dir, changeset e doc/spec/plan | Il tipo di richiesta determina perimetro, metodo e trattamento dei preesistenti, senza una scelta separata della basis |

Il corpus contiene difetti con oracolo indipendente e casi tenuti fuori dalla scrittura del modulo.
Il confronto usa stesso candidato, policy e verificatori, separando errori di selezione, retrieval, discovery e verifica.
Registrare numeratori, denominatori, casi non valutabili, variabilità e risultati per famiglia.
Il risultato è limitato al corpus, al profilo, al modello e all'ampiezza del job esaminati.
Nessuna equivalenza di recall o economia viene dichiarata dalla sola somiglianza dei corpi o dal numero di moduli.
La policy di accettazione viene fissata prima delle prove e non viene abbassata per promuovere un risultato deludente.
Il contratto dettagliato di misure e prove appartiene a [verifica della composizione](2026-10-22-review-composition-verification-design.md).

Il confronto registra separatamente il costo dell'authoring una tantum e il costo della review ordinaria.
Per il secondo contabilizza preparazione, nucleo/reference, moduli, evidenza, letture aggiuntive, tool output, output, reasoning esposto e retry.
I valori non esposti dal provider rimangono sconosciuti; non vengono ricostruiti da un'etichetta commerciale del modello.
La qualifica conserva modello risolto, effort, limite di ampiezza, host/versione e confini di validità dei risultati.
Un modello qualificato su un singolo modulo non è automaticamente qualificato sul job che aggrega dodici assegnazioni.
I casi di regressione comprendono anche combinazioni di moduli con evidenza condivisa e un percorso che richiede una lettura esterna allo scope.
Una protezione corretta riconosciuta come controevidenza ha lo stesso rilievo di una violazione trovata ai fini della precisione.
Il verificatore riceve l'evidenza pertinente attraverso il proprio metodo indipendente; il generatore non gli impone il verdetto atteso.

### 10.2 Freschezza e riuso dei risultati

L'identità semantica del job è distinta dal fingerprint dell'intero piano, secondo il contratto principale.
Il digest del job comprende profilo, nucleo, moduli/reference, input ammessi, assegnazioni, policy e binding rilevanti.
Il riuso di una consegna è una decisione esplicita con il digest verificato e la provenienza originale preservata.
Una nuova disposizione del piano che lascia un job identico può consentire quel riuso secondo le regole della verifica.
Una modifica dell'evidenza, del corpo, della policy o del modello coinvolti richiede rivalutazione del job pertinente.
L'authoring non copia un header nuovo su un vecchio report e non equipara un test di identità alla correttezza del contenuto.
La qualifica del catalogo e il riuso delle consegne di un run restano due decisioni differenti.

### 10.3 Patch di promozione

La patch collega comportamento, registrazione, selettori, casi e qualifiche in un unico candidato rivedibile.
Si scrivono i kernel e il compiler; gli export vengono rigenerati per tutti i cinque host.
Si aggiornano versioni e documentazione quando richiesto dal tipo di modifica effettivamente realizzata.
L'autore preserva modifiche concorrenti e registra conflitti; un vecchio output generato non sostituisce quello del candidato corrente.
La promozione verifica i metodi annidati: un wrapper nuovo non neutralizza istruzioni diff-only o requisiti incompatibili rimasti nelle reference.
La pubblicazione richiede l'autorizzazione applicabile e i gate del repository sul candidato reale.
Il presente lavoro di sola specifica non applica questi passi di implementazione o pubblicazione.

Il riepilogo della promozione contiene destinazioni degli obblighi, input verificati, gate passati/non disponibili e perimetri qualificati.
Un modulo con prerequisito mancante o un profilo non verificato rimane indisponibile o limitato al perimetro dichiarato.
Rollback e deprecazione conservano la provenienza e identificano la versione sostitutiva; una cancellazione richiede scope autorizzato.

## 11. Piano di introduzione e gate documentali

| Lotto | Contenuto | Condizione per passare oltre |
|---|---|---|
| A | Inventario, vocabolario, stati, helper e base preservati | Nessun ID irrisolto e nessun obbligo senza destinazione |
| B | SQL, AMQP, dati, concorrenza e asincrono | Selettori, confini e casi pertinenti verificati |
| C | Sicurezza, AI e contratti | Fonti primarie e controesempi indipendenti disponibili |
| D | Operatività, deploy, costi e recupero | Backend-only, assenze e impatti indiretti rappresentati |
| E | Testing, browser, accessibility e percorsi critici | Nuovo ruolo registrato e limiti delle evidenze dichiarati |
| F | Estrazione progressiva dei nuclei | Matrice obblighi completa e qualifica prima dell'abilitazione |

I lotti descrivono dipendenze e ordine di lavoro, non autorizzano a saltare i temi meno economici.
Il lotto F è un percorso trasversale: l'estrazione degli owner più ampi deve accompagnare le prime famiglie pertinenti, con qualifica prima dell'abilitazione.
F raccoglie la chiusura della riorganizzazione e non consente di rimandare tutti i nuclei compatti a dopo gli altri lotti.
Una consegna completa di authoring ha tutti i temi destinati, tutti i record inventariati e ogni stato documentato.
Una consegna completa di implementazione richiede inoltre corpi, registri, test, qualifiche e gate dei documenti collegati.
Le appendici sono l'inventario iniziale proposto; le modifiche future si accompagnano a delta e provenienza.

## Appendice A. Mappa dei 50 temi e dei tre supplementi

La destinazione elenca gli ID dell'allegato senza trasformarli in una dichiarazione di qualità equivalente.
Gli owner esatti e gli stati sono risolti nell'appendice B; `R` indica riuso adattato della patch esterna e `S` scrittura proposta.
Un tema con più moduli richiede confini e casi di interazione; la lista non equivale a più job obbligatori.

| ID | Area | Tema | Moduli e destinazione |
|---|---|---|---|
| T01 | Identità e permessi | RLS | `security-rls` (S) |
| T02 | Identità e permessi | Authorization bypass | `security-authorization` (S) |
| T03 | Identità e permessi | IDOR | `security-authorization` (S) |
| T04 | Identità e permessi | Scadenza delle sessioni | `security-sessions` (S) |
| T05 | Identità e permessi | Least privilege | `security-least-privilege` (S) |
| T06 | Identità e permessi | Signed URLs | `security-signed-urls` (S) |
| T07 | Sicurezza applicativa | Validazione server | `security-input-validation` (S) |
| T08 | Sicurezza applicativa | Segreti | `security-secrets` (S) |
| T09 | Sicurezza applicativa | Webhook: autenticità e integrità | `security-webhook-auth` (S) |
| T10 | Sicurezza applicativa | Dipendenze | `dependencies-method` (R) |
| T11 | Sicurezza applicativa | Prompt injection | `security-ai-boundaries` (S) |
| T12 | Sicurezza applicativa | XSS | `security-xss` (S) |
| T13 | Sicurezza applicativa | CSRF | `security-csrf` (S) |
| T14 | Sicurezza applicativa | SSRF | `security-ssrf` (S) |
| T15 | Sicurezza applicativa | Upload | `security-upload` (S) |
| T16 | Sicurezza applicativa | Security headers | `security-headers` (S) |
| T17 | Correttezza dei dati | Race conditions | `data-concurrency` (S); `logic-integrity-auditor` (R); `ui-race-auditor` (R) |
| T18 | Correttezza dei dati | Idempotenza | `data-idempotency` (S); `amqp-idempotency` (R); `external-effect-idempotency` (S) |
| T19 | Correttezza dei dati | Transazioni | `sql-transactions` (R); `data-integrity-auditor` (R) |
| T20 | Prestazioni e capacità | Indici DB | `sql-indexes` (R) |
| T21 | Prestazioni e capacità | N+1 | `sql-query-n-plus-one` (R) |
| T22 | Prestazioni e capacità | Connection pooling | `connection-pool-lifecycle` (S) |
| T23 | Prestazioni e capacità | Cache | `cache-consistency` (S) |
| T24 | Prestazioni e capacità | Rate limiting | `capacity-rate-limits` (S); `security-auditor` (R) |
| T25 | Prestazioni e capacità | Load testing | `test-capacity` (S) |
| T26 | Fallimenti e lavoro asincrono | Background jobs | `temporal-background-jobs` (S) |
| T27 | Fallimenti e lavoro asincrono | Timeout | `temporal-timeouts` (S); `distributed-flow-auditor` (R) |
| T28 | Fallimenti e lavoro asincrono | Retry | `temporal-retry-backoff` (S) |
| T29 | Fallimenti e lavoro asincrono | Exponential backoff | `temporal-retry-backoff` (S) |
| T30 | Fallimenti e lavoro asincrono | Dead letter queues | `queue-retries-dlq` (S); `amqp-retries-dlq` (R) |
| T31 | Osservabilità e costi | Error monitoring | `observability-errors` (S) |
| T32 | Osservabilità e costi | Structured logging | `observability-logs` (S) |
| T33 | Osservabilità e costi | Audit logs | `security-audit-trail` (S) |
| T34 | Osservabilità e costi | Health checks | `operability-health` (S); `chicken-egg-detector` (R) |
| T35 | Osservabilità e costi | Alerting | `operability-alerts` (S); `temporal-resilience-auditor` (R) |
| T36 | Osservabilità e costi | Cost monitoring | `runtime-cost-budgets` (S) |
| T37 | Modifiche e rilasci | Database migrations | `migration-ordering` (S); `release-schema-compatibility` (S) |
| T38 | Modifiche e rilasci | Rollback | `release-rollback` (S) |
| T39 | Modifiche e rilasci | Feature flags | `release-feature-flags` (S); `logic-integrity-auditor` (R) |
| T40 | Modifiche e rilasci | Staging | `release-environments` (S) |
| T41 | Modifiche e rilasci | Zero-downtime deployment | `release-zero-downtime` (S) |
| T42 | Esperienza completa e test | E2E | `test-user-journeys` (S) |
| T43 | Esperienza completa e test | Contract testing | `test-contract-coverage` (S); `api-contract-auditor` (R); `amqp-contracts` (R) |
| T44 | Esperienza completa e test | Payment webhooks | `external-effect-idempotency` (S); `security-webhook-auth` (S); `logic-integrity-auditor` (R) |
| T45 | Esperienza completa e test | Accessibilità | `a11y-navigation-semantics` (S); `a11y-perception-feedback` (S) |
| T46 | Esperienza completa e test | Browser mobili | `browser-compatibility` (S) |
| T47 | Conservazione e recupero | Backup | `recovery-backups` (S) |
| T48 | Conservazione e recupero | Restore | `recovery-restore` (S) |
| T49 | Conservazione e recupero | Disaster recovery | `recovery-disaster` (S) |
| T50 | Conservazione e recupero | Data retention | `data-retention` (S) |

| ID | Supplemento | Moduli e destinazione |
|---|---|---|
| S01 | Vincoli SQL | `sql-constraints` (R) |
| S02 | AMQP: acknowledgement e redelivery | `amqp-ack-redelivery` (R) |
| S03 | AI: output, RAG e regressioni | `security-ai-boundaries` (S); `ai-output-contracts` (S); `test-ai-regressions` (S) |

## Appendice B. Destinazione dei 66 record del backlog

`existing-base` e `existing-specialization` sono stati attribuiti alla baseline esterna.
`planned-base` e `planned-specialization` richiedono corpo, registro, casi e qualifica prima della promozione.
Per tutti i record verificare i selettori contro il vocabolario chiuso e le proprietà di impatto pertinenti.
Gli esistenti possono essere riscritti solo con la matrice degli obblighi e la qualifica prevista.

| ID esatto | Owner canonico esatto | Stato della fonte | Destinazione proposta |
|---|---|---|---|
| `a11y-navigation-semantics` | `senior-review:accessibility-auditor` | `planned-specialization` | Scrittura: corpo, segnali, casi e qualifica |
| `a11y-perception-feedback` | `senior-review:accessibility-auditor` | `planned-specialization` | Scrittura: corpo, segnali, casi e qualifica |
| `accessibility-auditor` | `senior-review:accessibility-auditor` | `planned-base` | Scrittura: base accessibility e registrazione del nuovo owner |
| `ai-output-contracts` | `senior-review:api-contract-auditor` | `planned-specialization` | Scrittura: corpo, segnali, casi e qualifica |
| `amqp-ack-redelivery` | `senior-review:distributed-flow-auditor` | `existing-specialization` | Riuso adattato: corpo esterno, selettori e qualifica locali |
| `amqp-contracts` | `senior-review:api-contract-auditor` | `existing-specialization` | Riuso adattato: corpo esterno, selettori e qualifica locali |
| `amqp-idempotency` | `senior-review:distributed-flow-auditor` | `existing-specialization` | Riuso adattato: corpo esterno, selettori e qualifica locali |
| `amqp-retries-dlq` | `senior-review:distributed-flow-auditor` | `existing-specialization` | Riuso adattato: corpo esterno, selettori e qualifica locali |
| `api-contract-auditor` | `senior-review:api-contract-auditor` | `existing-base` | Adattamento: fonte esterna, nucleo/profilo e matrice obblighi |
| `browser-compatibility` | `platform-engineering:platform-reviewer` | `planned-specialization` | Scrittura: corpo, segnali, casi e qualifica |
| `cache-consistency` | `senior-review:data-integrity-auditor` | `planned-specialization` | Scrittura: corpo, segnali, casi e qualifica |
| `capacity-rate-limits` | `platform-engineering:platform-reviewer` | `planned-specialization` | Scrittura: corpo, segnali, casi e qualifica |
| `chicken-egg-detector` | `senior-review:chicken-egg-detector` | `existing-base` | Adattamento: fonte esterna, nucleo/profilo e matrice obblighi |
| `connection-pool-lifecycle` | `senior-review:resource-lifecycle-auditor` | `planned-specialization` | Scrittura: corpo, segnali, casi e qualifica |
| `data-concurrency` | `senior-review:data-integrity-auditor` | `planned-specialization` | Scrittura: corpo, segnali, casi e qualifica |
| `data-idempotency` | `senior-review:data-integrity-auditor` | `planned-specialization` | Scrittura: corpo, segnali, casi e qualifica |
| `data-integrity-auditor` | `senior-review:data-integrity-auditor` | `existing-base` | Adattamento: fonte esterna, nucleo/profilo e matrice obblighi |
| `data-retention` | `senior-review:data-integrity-auditor` | `planned-specialization` | Scrittura: corpo, segnali, casi e qualifica |
| `dependencies-method` | `senior-review:dependencies-method` | `existing-base` | Adattamento: fonte esterna, nucleo/profilo e matrice obblighi |
| `distributed-flow-auditor` | `senior-review:distributed-flow-auditor` | `existing-base` | Adattamento: fonte esterna, nucleo/profilo e matrice obblighi |
| `external-effect-idempotency` | `senior-review:distributed-flow-auditor` | `planned-specialization` | Scrittura: corpo, segnali, casi e qualifica |
| `logic-integrity-auditor` | `senior-review:logic-integrity-auditor` | `existing-base` | Adattamento: fonte esterna, nucleo/profilo e matrice obblighi |
| `migration-ordering` | `senior-review:chicken-egg-detector` | `planned-specialization` | Scrittura: corpo, segnali, casi e qualifica |
| `observability-errors` | `platform-engineering:platform-reviewer` | `planned-specialization` | Scrittura: corpo, segnali, casi e qualifica |
| `observability-logs` | `platform-engineering:platform-reviewer` | `planned-specialization` | Scrittura: corpo, segnali, casi e qualifica |
| `operability-alerts` | `platform-engineering:platform-reviewer` | `planned-specialization` | Scrittura: corpo, segnali, casi e qualifica |
| `operability-health` | `platform-engineering:platform-reviewer` | `planned-specialization` | Scrittura: corpo, segnali, casi e qualifica |
| `queue-retries-dlq` | `senior-review:distributed-flow-auditor` | `planned-specialization` | Scrittura: corpo, segnali, casi e qualifica |
| `recovery-backups` | `platform-engineering:platform-reviewer` | `planned-specialization` | Scrittura: corpo, segnali, casi e qualifica |
| `recovery-disaster` | `platform-engineering:platform-reviewer` | `planned-specialization` | Scrittura: corpo, segnali, casi e qualifica |
| `recovery-restore` | `platform-engineering:platform-reviewer` | `planned-specialization` | Scrittura: corpo, segnali, casi e qualifica |
| `release-environments` | `platform-engineering:platform-reviewer` | `planned-specialization` | Scrittura: corpo, segnali, casi e qualifica |
| `release-feature-flags` | `platform-engineering:platform-reviewer` | `planned-specialization` | Scrittura: corpo, segnali, casi e qualifica |
| `release-rollback` | `platform-engineering:platform-reviewer` | `planned-specialization` | Scrittura: corpo, segnali, casi e qualifica |
| `release-schema-compatibility` | `platform-engineering:platform-reviewer` | `planned-specialization` | Scrittura: corpo, segnali, casi e qualifica |
| `release-zero-downtime` | `platform-engineering:platform-reviewer` | `planned-specialization` | Scrittura: corpo, segnali, casi e qualifica |
| `runtime-cost-budgets` | `platform-engineering:platform-reviewer` | `planned-specialization` | Scrittura: corpo, segnali, casi e qualifica |
| `security-ai-boundaries` | `senior-review:security-auditor` | `planned-specialization` | Scrittura: corpo, segnali, casi e qualifica |
| `security-audit-trail` | `senior-review:security-auditor` | `planned-specialization` | Scrittura: corpo, segnali, casi e qualifica |
| `security-auditor` | `senior-review:security-auditor` | `existing-base` | Adattamento: fonte esterna, nucleo/profilo e matrice obblighi |
| `security-authorization` | `senior-review:security-auditor` | `planned-specialization` | Scrittura: corpo, segnali, casi e qualifica |
| `security-csrf` | `senior-review:security-auditor` | `planned-specialization` | Scrittura: corpo, segnali, casi e qualifica |
| `security-headers` | `senior-review:security-auditor` | `planned-specialization` | Scrittura: corpo, segnali, casi e qualifica |
| `security-input-validation` | `senior-review:security-auditor` | `planned-specialization` | Scrittura: corpo, segnali, casi e qualifica |
| `security-least-privilege` | `senior-review:security-auditor` | `planned-specialization` | Scrittura: corpo, segnali, casi e qualifica |
| `security-rls` | `senior-review:security-auditor` | `planned-specialization` | Scrittura: corpo, segnali, casi e qualifica |
| `security-secrets` | `senior-review:security-auditor` | `planned-specialization` | Scrittura: corpo, segnali, casi e qualifica |
| `security-sessions` | `senior-review:security-auditor` | `planned-specialization` | Scrittura: corpo, segnali, casi e qualifica |
| `security-signed-urls` | `senior-review:security-auditor` | `planned-specialization` | Scrittura: corpo, segnali, casi e qualifica |
| `security-ssrf` | `senior-review:security-auditor` | `planned-specialization` | Scrittura: corpo, segnali, casi e qualifica |
| `security-upload` | `senior-review:security-auditor` | `planned-specialization` | Scrittura: corpo, segnali, casi e qualifica |
| `security-webhook-auth` | `senior-review:security-auditor` | `planned-specialization` | Scrittura: corpo, segnali, casi e qualifica |
| `security-xss` | `senior-review:security-auditor` | `planned-specialization` | Scrittura: corpo, segnali, casi e qualifica |
| `sql-constraints` | `senior-review:data-integrity-auditor` | `existing-specialization` | Riuso adattato: corpo esterno, selettori e qualifica locali |
| `sql-indexes` | `platform-engineering:platform-reviewer` | `existing-specialization` | Riuso adattato: corpo esterno, selettori e qualifica locali |
| `sql-query-n-plus-one` | `platform-engineering:platform-reviewer` | `existing-specialization` | Riuso adattato: corpo esterno, selettori e qualifica locali |
| `sql-transactions` | `senior-review:data-integrity-auditor` | `existing-specialization` | Riuso adattato: corpo esterno, selettori e qualifica locali |
| `temporal-background-jobs` | `senior-review:temporal-resilience-auditor` | `planned-specialization` | Scrittura: corpo, segnali, casi e qualifica |
| `temporal-resilience-auditor` | `senior-review:temporal-resilience-auditor` | `existing-base` | Adattamento: fonte esterna, nucleo/profilo e matrice obblighi |
| `temporal-retry-backoff` | `senior-review:temporal-resilience-auditor` | `planned-specialization` | Scrittura: corpo, segnali, casi e qualifica |
| `temporal-timeouts` | `senior-review:temporal-resilience-auditor` | `planned-specialization` | Scrittura: corpo, segnali, casi e qualifica |
| `test-ai-regressions` | `testing:test-suite-auditor` | `planned-specialization` | Scrittura: corpo, segnali, casi e qualifica |
| `test-capacity` | `testing:test-suite-auditor` | `planned-specialization` | Scrittura: corpo, segnali, casi e qualifica |
| `test-contract-coverage` | `testing:test-suite-auditor` | `planned-specialization` | Scrittura: corpo, segnali, casi e qualifica |
| `test-user-journeys` | `testing:test-suite-auditor` | `planned-specialization` | Scrittura: corpo, segnali, casi e qualifica |
| `ui-race-auditor` | `senior-review:ui-race-auditor` | `existing-base` | Adattamento: fonte esterna, nucleo/profilo e matrice obblighi |

## Appendice C. Undici base da preservare fuori dal backlog

Questi moduli appartengono al catalogo della prima patch esterna e non sono sostituiti dal file dei 66 record.
La loro destinazione è adattamento al registro dei profili, con conservazione degli obblighi, anche quando nessuno dei 50 temi li nomina.
Il percorso locale attuale dei ruoli e metodi fornisce la fonte effettiva da rileggere durante l'implementazione.

| ID esatto | Owner o binding canonico esatto | Stato della fonte | Destinazione proposta |
|---|---|---|---|
| `cleanup-auditor` | `senior-review:cleanup-auditor` | `existing-base` esterno | Adattamento e conservazione degli obblighi nel profilo |
| `code-auditor` | `senior-review:code-auditor` | `existing-base` esterno | Adattamento e conservazione degli obblighi nel profilo |
| `premise-auditor` | `senior-review:premise-auditor` | `existing-base` esterno | Adattamento e conservazione degli obblighi nel profilo |
| `resource-lifecycle-auditor` | `senior-review:resource-lifecycle-auditor` | `existing-base` esterno | Adattamento e conservazione degli obblighi nel profilo |
| `workspace-auditor` | `repo-hygiene:workspace-auditor` | `existing-base` esterno | Adattamento e conservazione degli obblighi nel profilo |
| `test-suite-auditor` | `testing:test-suite-auditor` | `existing-base` esterno | Adattamento e conservazione degli obblighi nel profilo |
| `abstraction-architect-agent` | `abstraction-architect:abstraction-architect-agent` | `existing-base` esterno | Adattamento e conservazione degli obblighi nel profilo |
| `react-performance-optimizer` | `react-development:react-performance-optimizer` | `existing-base` esterno | Adattamento e conservazione degli obblighi nel profilo |
| `type-safety-auditor` | `typescript-development:type-safety-auditor` | `existing-base` esterno | Adattamento e conservazione degli obblighi nel profilo |
| `platform-reviewer` | `platform-engineering:platform-reviewer` | `existing-base` esterno | Adattamento e conservazione degli obblighi nel profilo |
| `python-method` | `senior-review:python-method` | `existing-base` esterno | Adattamento e conservazione degli obblighi nel profilo |

## Appendice D. Moduli ulteriori della riorganizzazione

| ID nuovo | Owner canonico | Stato | Destinazione e confine |
|---|---|---|---|
| `code-concurrency` | `senior-review:code-auditor` | Proposed, aggiuntivo | Scrivere controllo di concorrenza locale generale; coordinare con dati, temporale, UI e flussi distribuiti |
| `code-general-performance` | `senior-review:code-auditor` | Proposed, aggiuntivo | Scrivere analisi generale di lavoro/costo/risorse; preservare specialisti SQL, React e platform |
| `interaction-critical-paths` | `senior-review:accessibility-auditor` | Proposed, aggiuntivo | Scrivere tracciamento di ingresso, login, consent e interazione bloccati anche da CSS/overlay statici; timeline asincrone a ui-race |

Questi ID non provengono dai 66 record e restano separati nella provenienza e nella contabilità.
T17 e T45 sono collegamenti tematici utili, ma le domande aggiuntive proteggono obblighi generali oltre quelle due righe storiche.
La dismissione di domande precedenti richiede una destinazione dimostrata, anche quando un nuovo nome sembra più ampio.

## Appendice E. Regole per aggiornare questo inventario

Ogni tema nuovo o rettificato ha origine attribuita, ID stabile e destinazione esplicita.
Ogni modulo mantiene owner e stato; fusioni e rinomine collegano gli ID precedenti.
I conteggi vengono ricalcolati dalle definizioni effettive e confrontati con tutte le tabelle.
La completezza dell'inventario, la profondità della review e l'esecuzione runtime rimangono fatti distinti.
Gli allegati originali restano fonti della proposta, non risorse richieste al funzionamento dei package installati.
Le decisioni definitive e la promozione richiedono il run di implementazione e i relativi gate.
