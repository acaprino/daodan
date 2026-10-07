# Daodan: proposta di ristrutturazione come harness coerente

Data: 7 ottobre 2026. Proposta di architettura da revisionare, senza modifiche ai plugin o ai pacchetti distribuiti.

## 1. Intento e promessa del prodotto

Daodan è un marketplace pubblico e neutrale rispetto al produttore dell'ambiente di sviluppo. Deve aiutare sviluppatori e team a recuperare e mantenere il controllo sui progetti sviluppati con l'IA. I problemi centrali sono frammentazione della conoscenza, decisioni contraddittorie, duplicazione di concetti e implementazioni, dead code, test inutili o errati e residui delle prove.

La promessa comune è: **ogni intervento lascia il progetto coerente, verificabile e comprensibile, in proporzione al suo impatto**. La chiusura del lavoro riguarda il comportamento richiesto e le conseguenze della modifica su codice, test, documentazione, istruzioni e artefatti.

L'identità si concretizza in due responsabilità: riparare un progetto già degradato e prevenire nuovo disordine durante lo sviluppo. Le competenze di linguaggio, framework e dominio restano strumenti di questo metodo. La profondità del lavoro segue rischio, ambito e autorizzazione della richiesta.

Tri-Tech Code è un consumatore esterno dei pacchetti e dei contratti Daodan per OpenCode V2, non un sesto adapter. Può ospitare un motore persistente per progetto, con una specifica propria. Questo documento definisce il metodo pubblico di Daodan; le scelte private del desktop passano attraverso parametri del contratto comune e non diventano eccezioni nel kernel.

## 2. Diagnosi della struttura esistente

L'inventario dei manifest conta 40 plugin, 76 ruoli, 59 skill e 58 workflow. Sono conteggi delle dichiarazioni in `plugin.toml`, non una misura della qualità o della copertura.

Il compilatore garantisce già una base comune per distribuire gli stessi kernel sui cinque host. La frammentazione osservata riguarda soprattutto i percorsi di lavoro e i criteri di risultato.

| Evidenza nel repository | Implicazione per il progetto |
|---|---|
| `codebase-mapper`, `project-setup` e `docs` hanno percorsi propri per guide, istruzioni e README | Manca una responsabilità comune per distinguere fatti implementati, intenzioni, decisioni e istruzioni correnti |
| Cleanup applicativo, test e residui del filesystem hanno tre proprietari | Il coordinamento deve offrire un percorso unitario rispettando queste differenze di evidenza |
| 55 sidecar su 58 dichiarano un solo esito; 57 su 58 hanno `schemas = []`. L'unico con schemi è `senior-review:team-review` | Un workflow terminato non dimostra quali garanzie siano state conservate |
| `senior-review:team-review` dichiara già risultati con evidenze, provenienza delle premesse e contabilizzazione dei worker | Esiste un modello concreto da estendere alla composizione fra workflow |
| Il testing collega la quarantena a una suite immediatamente affidabile e usa la copertura come gate principale di consolidamento | Serve distinguere esclusione, correzione del difetto e conservazione della protezione |
| La quarantena del workspace sposta i file e lascia all'utente la cancellazione | I report devono distinguere materiale spostato da spazio effettivamente recuperato |
| `PhaseSpec.invoke` viene caricato, ma non è usato dal rendering o dalla validazione semantica dei riferimenti | La composizione richiede un'implementazione verificata; aggiungere nomi di workflow a un TOML non crea da solo un executor |

Fonti locali: [modello neutrale](../../../scripts/daodan/model.py), [caricamento](../../../scripts/daodan/load.py), [review strutturata](../../../plugins/senior-review/workflows/team-review.toml), [consolidamento dei test](../../../plugins/testing/workflows/test-consolidate.md), [regole dei test](../../../plugins/testing/skills/test-hygiene/SKILL.md), [tidy](../../../plugins/repo-hygiene/workflows/tidy.md).

La [ricerca sui progetti sviluppati con agenti](../../../research/2026-10-07-coerenza-progetti-ai-test-e-residui.md) informa i criteri proposti. La combinazione completa qui descritta deve ancora essere valutata sul campo.

## 3. Alternative e scelta proposta

| Approccio | Beneficio | Costo |
|---|---|---|
| Accorpare tutti i plugin trasversali in un unico plugin | Un solo pacchetto visibile | Mescola responsabilità, aumenta il contesto e rende difficile verificare le singole competenze |
| Aggiungere comandi che concatenano i workflow attuali | Migrazione iniziale breve | Conserva criteri incompatibili, scansioni ripetute e rapporti scollegati |
| Ristrutturare le responsabilità e introdurre un nucleo di lifecycle | Offre pochi percorsi completi, specialisti riutilizzabili e risultati confrontabili | Richiede migrazione di contratti, riferimenti e verifiche comportamentali |

Si propone il terzo approccio. I prerequisiti sono due interventi separati: 0a per gli schemi condivisi e la loro distribuzione, 0b per rendere caricabile il cleanup applicativo. Solo dopo si costruisce il percorso diagnosi e riparazione; le altre parti hanno specifiche e piani separati.

### Scelta del meccanismo di composizione

La prima implementazione compone skill e ruoli, con la sola eccezione X-ray descritta sotto. Il coordinatore carica metodi canonici e dispone le fasi tramite i meccanismi di dispatch già presenti. Il workflow specialistico e il coordinatore usano lo stesso metodo, che conserva condizioni di ingresso, autorizzazioni, verifiche ed esiti.

Step 7c è già distribuito sotto `review-quality-gates/references/code-review-fix-loop.md`, insieme a 7a e 7b. L'intervento 0b lo promuove a skill caricabile per nome, `senior-review:application-cleanup-method`. `code-review` conserva l'ingresso pubblico e carica questa skill; `repair` carica la medesima skill quando il piano contiene rimozioni applicative. Il corpo del fix-loop mantiene il puntatore e perde il metodo duplicato; 7a e 7b restano al loro posto.

La skill verifica i prerequisiti ereditati: severità e finding accettati in 7a, correzioni propedeutiche di 7b completate e committate, albero pulito e baseline di build e test riferita allo stesso workspace. Ricevere questi dati come input non sostituisce la verifica dello stato effettivo. Restano il vincolo `--commit` e i gate per ogni fase; non viene ricreato un comando standalone di cleanup.

Le altre estrazioni entrano nell'intervento che per primo usa il metodo. Le skill già complete vengono riusate; una skill di sole nozioni non viene trattata come un executor. I metodi della conoscenza vengono organizzati direttamente nel nuovo `project-knowledge` durante l'accorpamento, evitando una precedente estrazione destinata a essere spostata di nuovo. I quattro percorsi non lanciano comandi specialistici tramite prosa, con una sola eccezione dichiarata: l'X-ray. Phase 1a di `team-review` prescrive già l'esecuzione di `codebase-xray:analyze` nel proprio contesto, come lo invocherebbe un utente, e ne risolve la run da `.codebase-xray/runs.json`. Si conserva questo ingresso e il suo contratto, senza spostare qui l'intera pipeline. È un precedente comportamentale, distinto da un executor generico verificato. Quel passo va provato sui cinque pacchetti installati nell'intervento 1. Un host su cui fallisce rivela un difetto anche di `team-review`, da correggere una volta per entrambi.

Un executor generico di `invoke` su cinque host resta un'alternativa più costosa, fuori dalla prima implementazione. L'intervento 0a aggiunge invece il rifiuto esplicito di un `invoke` valorizzato fino a quando esista un'implementazione verificata, chiudendo il caso di metadata accettato e ignorato.

### Riuso prima di scrittura

I quattro percorsi non contengono dimensioni di audit né prompt di rilevazione propri. Dispacciano i ruoli esistenti con i loro metodi e divieti. La logica nuova di diagnosi del coordinatore si limita a quattro cose: la tabella che associa ogni focus alle dimensioni, la preparazione degli input che ciascun ruolo già richiede, la riconciliazione fra intenzione dichiarata e implementazione, la costruzione del piano. Questo riuso non elimina il lavoro sui contratti di risultato di 0a, sui record di esecuzione o sui minimi parametri mancanti per una modalità di sola lettura.

Per ogni bisogno si sceglie la prima forma applicabile:

1. **Così com'è.** Un ruolo o una skill già caricabile per nome viene usato senza modifiche.
2. **Spostamento.** La logica che oggi vive nel corpo di un workflow passa nella skill dello stesso plugin, e il workflow conserva il puntatore. Il testo si sposta, non si parafrasa. È la stessa operazione di 0b e di `senior-review` 8.0.0, che ha reso sottile `code-review`.
3. **Miglioramento.** Un pezzo che quasi serve riceve nel suo proprietario la modalità o il parametro mancante, a beneficio del comando esistente e del coordinatore insieme.
4. **Scrittura.** Solo quando le prime tre non bastano. La specifica nomina il pezzo esistente considerato e il motivo per cui non serve.

Uno spostamento non cambia il comportamento del comando da cui parte. Lo verificano gli eval esistenti dove ci sono; altrove, un confronto dell'output del comando prima e dopo sullo stesso progetto campione.

| Bisogno | Pezzo esistente | Dove vive oggi | Forma di riuso |
|---|---|---|---|
| Contesto tecnico del progetto | `codebase-xray:analyze` e contratto `.codebase-xray/` | Workflow e artefatto. La procedura con cui un consumatore ottiene una run è formulata due volte: Phase 1a di `team-review`, passi 2 e 3 di `abstraction-architect:audit` | Spostamento della procedura del consumatore in `xray-method`. `assess` non ne aggiunge una terza |
| Contratti, invarianti, regole di dominio | `codebase-xray:semantic-interconnect-mapper` | Ruolo | Così com'è |
| Codice morto, asset orfani, dipendenze, documentazione stantia, archeologia | `senior-review:cleanup-auditor` | Ruolo | Così com'è |
| Residui decisi da filesystem e Git | `repo-hygiene:workspace-auditor` e catalogo dei controlli | Ruolo e skill | Così com'è |
| Entropia strutturale sull'albero intero | `abstraction-architect:abstraction-architect-agent`, modalità globale | Ruolo. Lo stato del concept index si risolve nel passo 4 del corpo di `audit` | Ruolo così com'è; spostamento del passo 4 nella skill |
| Salute della suite di test | `testing:test-suite-auditor` | Ruolo. Rilevazione del runner e misure meccaniche stanno negli Step 1 e 2 del corpo di `test-audit`, con i comandi già in `runner-playbook.md` | Ruolo così com'è; spostamento degli Step 1 e 2 in `test-hygiene` |
| Istruzioni contro codebase | `project-setup:claude-md-auditor`, Workflow A fino al report | Ruolo; il percorso continua poi verso conferma e applicazione | Miglioramento minimo nell'intervento 1: modalità audit-only che termina al report; rilevazione riusata |
| Documentazione contro codice | `codebase-mapper:documentation-engineer` e `docs-maintain --audit-only` | Ruolo e workflow. Il flag di sola lettura e la tabella dei controlli di deriva per dimensione appartengono al workflow | Spostamento della tabella nella skill e promozione del contratto audit-only nel ruolo, durante l'intervento 3 |
| README contro codebase | `docs:readme-craft` | Skill. Scansione e checklist di audit stanno nel corpo di `maintain-readme` | Spostamento nella skill, durante l'intervento 3 |
| Dispatch, isolamento dei worker, barriera di consegna | Harness generato dal compilatore per ogni host | Template degli adapter | Così com'è |
| Contesto condiviso, provenienza delle premesse, classi di evidenza, verifica avversariale, critico di completezza, gate di consegna | `senior-review:review-quality-gates` | Skill | Così com'è |
| Deduplica, co-locazione, conflitti di gravità, corroborazione distinta dall'eco | Phase 4 di `team-review` | Corpo del workflow | Spostamento in `review-quality-gates` |
| Formato di finding, risultato e registro delle consegne | I sette contratti di `team-review` | `contracts/` | Migrazione già decisa in 0a |
| Stato delle fasi e ripresa di una run | `state.json` di `team-review`, `runs.json` dell'X-ray | Convenzioni dei due pipeline | Miglioramento: riuso degli stati di fase e della risoluzione della run, con transizioni e identità persistenti formalizzate nel contratto comune |
| Rimozione applicativa | Step 7c | Riferimento di skill | Promozione in 0b |
| Quarantena dei test | Step 5 di `test-audit` e `remediation-workflow.md` | Corpo e riferimento di skill | Spostamento al primo uso, intervento 2 |
| Applicazione di `tidy` | Step 4 di `tidy` | Corpo | Spostamento dentro `repo-hygiene` al primo uso, intervento 2 |

`guide-reviewer` non compare nella mappa: lavora sulle guide generate in `.codebase-map/` e modifica i documenti, quindi non è un rilevatore per `assess`.

Anche il piano parte da dati che i ruoli producono già. `cleanup-auditor` chiude ogni finding con la fase di Step 7c che lo rimuove, `test-suite-auditor` con il `Fix path`, `workspace-auditor` con la fase di `tidy` e una disposizione fra sette valori definiti. I primi due propongono anche un ordine di esecuzione. Il coordinatore unisce questi dati, risolve le dipendenze fra interventi di proprietari diversi e aggiunge autorizzazione richiesta ed eseguibilità. Conserva i proprietari indicati; assegna un percorso di sviluppo ai finding strutturali che oggi non ne nominano uno.

La duplicazione ha un percorso di riparazione già nell'intervento 2. `abstraction-architect` conserva la diagnosi report-only e la direzione suggerita. `project-lifecycle` possiede la riparazione e riusa planning ed esecuzione di `superpowers`, già inclusi nella chiusura proposta: non nasce un nuovo auditor o un ruolo generalista Daodan. L'esecuzione può avvenire nel contesto corrente tramite il metodo upstream; per incarichi TypeScript pertinenti esiste anche `typescript-development:typescript-engineer`, già nella chiusura. Step 7b salta i refactor significativi e Step 7c è sola sottrazione: nessuno dei due diventa un metodo di refactor architetturale.

Prima di eseguire, il piano identifica il concetto e la sua autorità, il comportamento da conservare, le rappresentazioni coinvolte, l'ambito autorizzato, una baseline e le verifiche pertinenti. Le scelte tecniche documentabili vengono risolte nel piano. Una contraddizione sull'intenzione di dominio resta da chiarire prima della modifica; non ogni finding di astrazione richiede una nuova domanda all'utente. Una riparazione conclusa richiede verifica del comportamento, nuovo audit strutturale sullo stato modificato e aggiornamento delle conseguenze su test e conoscenza.

## 4. Responsabilità dei plugin

| Area | Proprietario proposto | Migrazione |
|---|---|---|
| Schemi e validazione comuni | Nuovo `project-contracts` | Plugin foglia senza dipendenze locali; possiede schema di risultato, record di lavoro e validazione |
| Coordinamento del progetto | Nuovo `project-lifecycle` | Possiede i percorsi principali, l'incarico, il piano e la contabilizzazione degli esiti |
| Conoscenza del progetto | Nuovo `project-knowledge` | Accorpa `codebase-mapper`, `project-setup` e `docs`, preservando guide, istruzioni, README e voce dell'autore |
| Comprensione tecnica statica | `codebase-xray` | Conserva metodo, analisi incrementale e contratto `.codebase-xray/` |
| Duplicazione semantica e astrazioni | `abstraction-architect` per la diagnosi; `project-lifecycle` per la riparazione | Conserva l'auditor report-only e riusa il percorso upstream di sviluppo per la modifica |
| Protezione attraverso i test | `testing` | Rivede diagnosi, quarantena, aspettative e consolidamento alla luce della ricerca |
| Difetti e cleanup applicativo | `senior-review` | Conserva reviewer e proprietario delle rimozioni applicative; rende il percorso utilizzabile dal coordinatore |
| Residui decisi dal filesystem e Git | `repo-hygiene` | Resta leaf, senza dipendenze locali, senza rimozione di codice applicativo o test, con Git ausiliario detection-only |
| Leggibilità | `clean-code` | Resta una competenza delimitata, invocata quando serve |
| Linguaggi, framework e domini | Plugin specialistici esistenti | Mantengono le proprie competenze; ricevono incarichi delimitati |

L'accorpamento della conoscenza governa ciò che il progetto afferma di sé e ciò che guida chi vi lavora. Questa coesione è un beneficio, da confrontare con il costo di installazione dichiarato sotto. Ogni tipo di informazione conserva la propria fonte autorevole. Il codice descrive l'implementazione; i requisiti e le decisioni approvate descrivono l'intenzione. Una discrepanza va risolta con evidenze, senza trasformare automaticamente il codice corrente nel requisito corretto.

Il coordinatore dipende dai plugin che usa. Gli specialisti non dipendono dal coordinatore. A migrazione conclusa, `project-lifecycle`, `project-knowledge`, `codebase-xray`, `abstraction-architect`, `testing`, `senior-review` e `clean-code` dichiarano `project-contracts` come dipendenza obbligatoria e caricano il suo metodo di risultato anche quando eseguiti autonomamente. Ogni adozione entra nell'intervento che ne usa il risultato; 0a migra soltanto `team-review` come primo consumatore.

`repo-hygiene` resta una foglia senza dipendenze locali, come prescrive la policy esistente. Il suo comando autonomo conserva il contratto proprio. Quando partecipa a un percorso coordinato, `project-lifecycle` confeziona il risultato nel record comune e lo valida, conservando evidenze e limiti. Questo adattamento ha un solo proprietario nel coordinatore e due ingressi distinti. Nell'intervento 1 il wrapper diagnostico consuma i finding di `workspace-auditor` nel loro formato esistente, conserva il report originale e ha un test di contratto sui campi consumati. Nell'intervento 2 il convertitore degli esiti applicativi consuma il report di `tidy`.

Oggi gli Step 3 e 5 di `tidy` prescrivono l'output in prosa. L'intervento 2 formalizza quel formato nel metodo canonico di `tidy`, sotto `repo-hygiene`, senza dipendenze dal protocollo comune. Un test di contratto confronta i campi consumati con quel formato e verifica, su fixture significative, la conservazione di quarantena, materiale mantenuto e Git-state non applicato. Una modifica incompatibile a uno dei due formati deve far fallire il relativo test; nessun default inventato dal coordinatore può mascherarla. La stessa promessa di schema uniforme non viene estesa a tutti i plugin del marketplace.

### Decisioni comuni e disposizioni operative

I cinque valori del §6 restano decisioni sul materiale. I sette valori di `workspace-auditor` restano disposizioni operative del suo dominio. Il payload conserva la disposizione originale, il controllo C1-C7, l'oggetto interessato, lo stato Git, l'azione proposta e i suoi limiti. Il mapping non conferisce autorizzazione e può produrre più decisioni, riferite a oggetti diversi.

| Disposizione nativa | Collegamento alle decisioni del §6 |
|---|---|
| `KEEP` | Mantenere l'artefatto |
| `KEEP+IGNORE` | Mantenere l'artefatto e correggere ignore o tracking dove richiesto |
| `REMOVE` | Ritirare l'oggetto indicato; conservare la distinzione fra rimozione tracciata e quarantena dell'untracked |
| `REMOVE+IGNORE` | Qualificare controllo e oggetto: ritirare scratch in C5 oppure mantenere un artefatto e correggerne il tracking, quando l'azione è solo untracking; correggere anche l'ignore |
| `UNIGNORE` | Correggere la regola ignore |
| `REVIEW` | Lasciare da chiarire |
| `REPORT-ONLY` | Non impone una decisione sul materiale; conserva il limite permanente all'esecuzione automatica, anche quando la valutazione è certa |

0a formalizza questa separazione nel risultato comune, mantenendo opache le disposizioni di dominio. Il wrapper diagnostico dell'intervento 1 conserva quei dati per costruire il piano; conversione degli esiti applicativi e mapping delle azioni di `tidy` entrano nell'intervento 2. Quest'ultimo risolve nel proprietario una divergenza già presente: C5 e `tidy` prescrivono `git rm -r` per scratch tracciato, mentre la tabella generica della skill associa `REMOVE+IGNORE` a `git rm --cached`. L'operazione viene qualificata per controllo e oggetto; il test di contratto verifica che il coordinatore conservi quella differenza. `REPORT-ONLY` non diventa una rimozione eseguibile tramite un flag.

### Una sola casa per gli schemi

Gli schemi canonici vivono in `plugins/project-contracts/contracts/`. La skill dello stesso plugin contiene il metodo, il validatore e i suoi helper, senza una seconda copia degli schemi. Gli schemi specifici di dominio restano in `contracts/` del rispettivo kernel. `contract.schemas` conserva il significato attuale di percorsi locali al kernel.

Il rendering attuale copia solo gli schemi dichiarati da un workflow; un plugin foglia senza workflow non può quindi distribuirli tramite quel meccanismo. L'intervento 0a introduce una dichiarazione esplicita degli schemi esportati in `plugin.toml`, con ID e percorso locale sotto `contracts/`, e ne implementa validazione e distribuzione nel solo pacchetto proprietario, su tutti i cinque host. Introduce inoltre nei sidecar `shared_schemas` qualificati, per esempio `project-contracts:project-result`, risolti soltanto contro gli export di dipendenze obbligatorie. Sono nuove capacità del compilatore, non comportamenti già disponibili.

Il risultato comune è un involucro `project-result`: possiede ambito, revisione, autore, stato della consegna, evidenze, limiti e riferimenti agli output. Il payload contiene i soli dati di dominio. L'involucro ne porta l'ID dello schema in un campo `payload_schema`; lo schema resta locale al consumatore, che lo dichiara in `contract.schemas`. Per il compilatore il payload è opaco. Stato della consegna e riuscita delle verifiche restano distinti. I risultati di worker e aggregati usano lo stesso involucro con identità e granularità esplicite; il risultato aggregato riferisce le consegne, senza ricopiarle. `work` possiede invece incarico, piano e dati di ripresa.

I sette contratti esistenti di `team-review` hanno questa destinazione:

| Contratto attuale | Proprietario e forma dopo 0a |
|---|---|
| `review-brief` | Resta in `senior-review`, come input specifico della review |
| `reviewer-binding` | Resta in `senior-review`, per selezione e assegnazione delle dimensioni |
| `reviewer-selection` | Resta in `senior-review` e riferisce il binding locale |
| `evidenced-finding` | Migra in `project-contracts`; ogni finding di review usa questo unico schema |
| `delivery-ledger` | Migra in `project-contracts`; conserva la contabilizzazione e il barrier |
| `reviewer-result` | Resta come payload di review dentro `project-result`, con la dimensione e gli altri soli dati di dominio; autore, stato, finding, gap e output usano i campi comuni |
| `final-report` | Resta come payload del risultato aggregato, con selezione dei finding, copertura e dimensioni degradate; riferisce i finding canonici e non ridefinisce l'involucro |

Il compilatore non acquisisce un sistema di tipi fra schemi. In 0a verifica due cose: ogni ID in `shared_schemas` corrisponde a un export di una dipendenza obbligatoria, e ogni `payload_schema` dichiarato da un workflow corrisponde a uno schema locale di quel kernel. La validazione di un record avviene a runtime in due passi. Il metodo di `project-contracts` valida l'involucro; il consumatore valida il payload contro il proprio schema locale. Un payload che nomina un finding lo riferisce per ID dentro l'involucro, senza ridefinirlo. Riferimenti tipizzati fra schemi, ereditarietà e controllo dei cicli restano fuori da 0a: entrano con una specifica propria solo se un secondo consumatore mostra che i due passi non bastano. Il provider comune non dipende da `senior-review`: è il consumatore a dichiarare il proprio payload. La migrazione di sidecar, corpi, template, eval e fixture di `team-review` è atomica, senza mantenere il vecchio `reviewer-result` completo come secondo formato dell'esito.

Il pacchetto consumatore registra il riferimento e il metodo che rende disponibile il contratto; non copia il file canonico. I corpi caricano il metodo per nome, senza raggiungere un altro plugin per percorso. Le prove installate verificano che quel metodo legga gli schemi dal pacchetto proprietario.

### Costo di installazione scelto nella proposta

La proposta mantiene le capacità attuali e accetta un nucleo completo con tutte le dipendenze obbligatorie. Un focus restringe il lavoro eseguito, non l'installazione. Questa scelta include il costo di installare lo stack di review anche per usare il futuro `project-knowledge` solo su README o istruzioni.

`project-knowledge` eredita `senior-review`, `codebase-xray`, `text-humanizer` e `agent-teams@claude-code-workflows`, oltre al nuovo `project-contracts`. Il nucleo dichiara direttamente le competenze usate e `superpowers@claude-plugins-official` per la riparazione strutturale dall'intervento 2 e per `change`; non richiede `ai-tooling` solo per ottenere quella dipendenza. Testing porta i propri due pacchetti upstream. Anticipare questo uso non aggiunge un pacchetto alla chiusura misurata sotto, ma richiede prove di esecuzione proprie su ciascun host.

| Baseline misurata sulle dipendenze attuali | Plugin locali | Pacchetti esterni | File e byte nei pacchetti Claude locali |
|---|---|---|---|
| Unione di mapper, project-setup e docs con chiusura transitiva | 12 | 3 | 301 file, 2.123.493 byte |
| Competenze previste per lifecycle, prima dei nuovi kernel | 13 | 4 | 306 file, 2.138.256 byte |

I quattro pacchetti esterni sono `agent-teams@claude-code-workflows`, `developer-essentials@claude-code-workflows`, `mattpocock-skills@mattpocock` e `superpowers@claude-plugins-official`. Le dichiarazioni nominano tre namespace di marketplace. Le misure escludono pacchetti esterni, runtime, cache e i nuovi contenuti; non sono il costo totale dell'installazione, né una stima dei token caricati. I corpi si caricano secondo necessità.

L'accorpamento sostituisce i tre kernel attuali con un unico proprietario; non promette un'installazione minima per la manutenzione di un solo file. Alleggerirla richiederebbe un altro confine di pacchetto o la rimozione esplicita delle capacità che portano quelle dipendenze, da decidere prima di cambiare questo design. Non si usano dipendenze opzionali o fallback per simulare quel risultato.

## 5. Quattro percorsi principali

I nomi seguenti sono gli ID neutrali proposti. Ogni host li espone attraverso la propria forma nativa; Tri-Tech Code può mostrarne etichette italiane.

| Workflow | Scopo e risultato | Confine |
|---|---|---|
| `/project-lifecycle:assess` | Inventario pertinente, contraddizioni accertate, rischi e piano ordinato di intervento | Scrive l'esito dell'analisi, senza modificare codice, test, documentazione o configurazione del progetto |
| `/project-lifecycle:repair` | Esegue un piano delimitato e verifica ogni riparazione | Ogni intervento ha un proprietario; le ambiguità sull'intenzione richiedono una decisione prima della modifica |
| `/project-lifecycle:change` | Realizza feature, bugfix, migrazioni o refactor con prevenzione e verifica delle conseguenze | La profondità segue il cambiamento; planning e authoring già delegati restano delegati agli upstream dichiarati |
| `/project-lifecycle:consolidate` | Chiude una prova o campagna, conserva risultati e motivazioni, classifica e gestisce gli artefatti | I test di regressione restano protezione eseguibile; la rimozione semantica di codice o test passa al proprietario della riparazione |

`assess` e `repair` accettano il focus `knowledge`, `structure`, `tests`, `artifacts` oppure `all`. Il focus seleziona l'intervento, lasciando visibili le dipendenze necessarie a valutarlo. Una riparazione dei test può richiedere la verifica del contratto documentato.

`assess` e `team-review` riusano le stesse regole di pipeline e i ruoli pertinenti; si distinguono per finalità, dimensioni attivate ed esito. `team-review` accetta diff, PR, file o directory e valuta correttezza e rischi, includendo già dimensioni di igiene e astrazione. Restituisce finding ordinati per gravità. `assess` parte dal progetto e da un focus, attiva le dimensioni di coerenza della mappa di riuso del §3 e restituisce un piano. Quando serve una review di correttezza, il piano la indica come azione il cui proprietario è `team-review`. `team-review` conserva il proprio esito di review. Un finding che entrambi possono sollevare proviene dallo stesso ruolo e ha quindi una sola definizione.

La copertura del focus `knowledge` è dichiarata per sottodimensione: fino all'intervento 3 riguarda istruzioni e documentazione stantia; audit completo della deriva delle guide e del README non sono ancora coperti. `all` conserva questi limiti e non viene presentato come copertura totale. Il piano distingue anche rilevazione disponibile e riparazione disponibile.

Il piano di `assess` dichiara già per ogni azione metodo proprietario, autorizzazione richiesta, prerequisiti, gate e stato di eseguibilità. Una rimozione applicativa in bulk richiede `--commit` e una baseline stabile: con solo `--fix` viene indicata come non eseguibile prima di avviare `repair`. Se il focus `structure` contiene solo quel tipo di interventi, il piano dice esplicitamente che `repair --fix` non applicherà alcuna riparazione strutturale. Una correzione puntuale ammessa dal metodo di Step 7b è distinta dalle rimozioni in bulk.

I comandi specialistici restano accessibili agli utenti avanzati. Quelli partecipanti al protocollo dichiarato nel §4 caricano i criteri e gli schemi del plugin foglia; `repo-hygiene` conserva l'eccezione esplicita descritta lì. I percorsi principali riusano metodi specialistici. Le regole operative hanno un solo proprietario e non vengono ricopiate nei quattro workflow.

## 6. Contratto comune di lavoro

Ogni incarico coordinato registra solo quanto serve per eseguirlo, verificarlo e riprenderlo:

- Obiettivo e comportamento richiesto, con fonte dell'intenzione o ambiguità dichiarata.
- Ambito, revisione e impronta dei file coinvolti, comprese le modifiche non committate.
- Vincoli e autorizzazioni già ricevuti dall'utente.
- Piano con dipendenze fra interventi e proprietario di ciascuno.
- Evidenze consultate e distinzione fra fatti verificati, inferenze e informazioni ereditate.
- Disposizioni motivate: mantenere, correggere, accorpare, ritirare o lasciare da chiarire.
- Verifiche eseguite, fallite o non eseguibili e relativo ambito.
- Problemi ancora aperti e materiale necessario per riprendere il lavoro.

Ogni specialista restituisce un esito strutturato con ambito, revisione, stato, evidenze, risultati e limiti. Il coordinatore verifica i campi e i riferimenti, contabilizza le consegne e risolve i duplicati per comportamento o problema. Una consegna mancante resta mancante. Due reviewer che ereditano la stessa premessa non costituiscono due conferme indipendenti.

Gli schemi possono verificare struttura e consistenza dei record. La correttezza semantica richiede letture, strumenti, esecuzioni e decisioni umane quando l'intenzione non è ricostruibile.

## 7. Regole condivise da rendere operative

1. Cercare materiale e implementazioni pertinenti prima di aggiungerne di nuovi.
2. Confrontare ciò che una modifica rende obsoleto anche nei file non modificati.
3. Distinguere test errato, difetto nel prodotto, problema di ambiente e flakiness prima di proporre una quarantena. Escludere un test non corregge un difetto.
4. Motivare la rimozione di una verifica con il requisito ritirato o la protezione equivalente conservata. Copertura, numero di test ed età restano segnali.
5. Conservare risultati delle prove, condizioni, errori e limiti prima di disporre degli output. Un riassunto deve essere verificato contro le evidenze necessarie.
6. Distinguere dati rigenerabili, cache riutilizzabili, evidenze di problemi irrisolti e residui conclusi.
7. Riesaminare gli esiti interessati quando cambiano i relativi input, evitando di trattare un vecchio report come conoscenza corrente.
8. Tenere lo stato delle esecuzioni separato dalle istruzioni durevoli. AGENTS.md e CLAUDE.md non diventano registri di sessione.

L'interfaccia comune proposta distingue `--dry-run`, `--fix` e `--commit`: anteprima, modifica con verifica senza commit, modifica con commit autorizzati. Questa uniformità richiede una migrazione esplicita dei metodi attuali. Il nuovo coordinatore deve rispettare i loro vincoli finché la migrazione non è completata: il cleanup applicativo di Step 7c richiede `--commit`, e i workflow dei test hanno gate propri. Le fasi incompatibili con l'autorizzazione ricevuta restano aperte, con il motivo.

Le autorizzazioni persistono nel loro ambito e non vengono richieste nuovamente a ogni passaggio. Le decisioni mancanti riguardano risultati concreti e revisionabili. Il piano non autorizza rimozioni prive di evidenza o operazioni fuori ambito. La quarantena di untracked e il Git-state detection-only di `repo-hygiene` restano vincoli del proprietario.

## 8. Artefatti e integrazione nel harness

Un incarico coordinato ha un solo record operativo e un esito consolidato. Gli output degli specialisti restano evidenze collegate a quel record. Le conclusioni durevoli vengono integrate nelle fonti del progetto; il record non ne mantiene copie concorrenti.

La directory di contratto predefinita è `<project-root>/.daodan/`. Ogni esecuzione usa `runs/<run-id>/`, con `work.json`, `result.json` e i riferimenti alle evidenze; un puntatore allo stato della run serve a riprenderla. L'ID distingue anche esecuzioni simultanee e viene creato prima del dispatch. In assenza di `--out` si usa questa destinazione, senza domanda aggiuntiva.

Il vocabolario di fase parte da `state.json` di `team-review`: `pending`, `in_progress`, `complete`, `skipped`. Lo stato della run (`in_progress`, `complete`), la consegna (`delivered`, `failed`) e l'esito delle verifiche sono dimensioni distinte. 0a formalizza nel contratto comune transizioni, prerequisiti di completamento e registrazione dell'interruzione, con verifica di coerenza rispetto al primo consumatore. Una fase terminata con consegna fallita non rende riuscito il lavoro. Le run interrotte e le consegne fallite restano rintracciabili nel proprio `work.json`, indipendentemente dall'indice delle run attive.

La risoluzione della run X-ray riusa la procedura del consumatore, ma conserva in `work.json` l'identità esatta della run chiamata, il target, la profondità e il percorso verificato. La ripresa usa quel binding, senza scegliere il solo `latest_completed` o il mirror. L'X-ray rimuove da `active` anche run abortite o fallite: quel registro non è il catalogo di ripresa lifecycle. L'intervento 1 prova la correlazione della run anche in concorrenza e in caso di fallimento; se la procedura attuale non basta, il minimo parametro di correlazione viene aggiunto nel proprietario X-ray e riusato dai suoi consumatori. Un'identità non risolvibile resta un errore di pipeline. Le directory di sessione degli specialisti restano le loro e vengono riferite senza ricopiarne il contenuto.

Nella prima implementazione `--out <root>` seleziona una directory dedicata agli artefatti, strettamente interna al progetto. La radice viene risolta e verificata prima del dispatch, registrata nell'incarico e propagata a ogni writer. Ogni radice risolta, compresa quella predefinita, riceve prima del dispatch un file sentinella vuoto con nome fisso, `.daodan-root`. Questa inizializzazione del coordinatore è una scrittura esplicita alla radice; le successive scritture dei record sono limitate alla run posseduta. Un percorso esterno al progetto viene rifiutato con un limite esplicito; non si cambia destinazione silenziosamente. Su OpenCode i ruoli hanno oggi un'allowance `external_directory` limitata al pacchetto installato: il parametro non concede accesso a una radice privata dell'app. Il probe di 0a documenta questo confine, senza presentare un'esecuzione privilegiata manualmente come capacità del pacchetto.

La policy `run-write-confinement` del coordinatore limita la scrittura dei suoi record alla run posseduta. Gli helper rifiutano percorsi che escono dalla radice risolta, inclusi collegamenti che portano fuori. Questo controllo limita le scritture degli helper, senza confinare meccanicamente ogni altro tool del worker. I writer specialistici hanno i propri output e permessi dichiarati nel piano: per esempio, la fase X-ray conserva `.codebase-xray/`. La policy dei record non autorizza modifiche al sorgente e non viene resa un hook globale della sessione.

Il catalogo C5 di `repo-hygiene` riconosce `.daodan/` soltanto per nome e non ne propone mai la rimozione, indipendentemente dallo stato Git. Non legge `work.json`, non verifica riferimenti e non classifica le run. Lo stesso vale per ogni directory che contiene la sentinella `.daodan-root`: C5 la riconosce dal nome del file, senza aprirlo, e la riporta come stato di protocollo. La protezione include la rimozione di un antenato che porterebbe via la directory protetta. Così anche un `tidy` lanciato da solo, che non riceve alcun ambito dal coordinatore, non mette in quarantena una radice `--out` personalizzata e non interrompe la ripresa di una run. Una sentinella rimasta in una directory altrimenti vuota resta materia di `consolidate`. Interpretazione del protocollo, dati di ripresa, evidenze irrisolte e disposizioni delle run concluse appartengono a `consolidate`, che usa `project-contracts`. Le eventuali operazioni filesystem rispettano quarantena e limiti Git del loro proprietario. L'eventuale ignore entry è proposta o applicata in una fase autorizzata; `assess` non modifica `.gitignore` di nascosto.

I kernel possiedono comportamento e contratti. Gli adapter possiedono dispatch, registrazione, meccanismi ed eventuale enforcement. `run-write-confinement` parte come obbligo nel prompt su tutti e cinque gli host. Esiste un'implementazione di `xray-guard` per Copilot, ma la [policy X-ray](../../../plugins/codebase-xray/policies/write-confinement.toml) dichiara `mechanical_wired = false`: non è enforcement attivo, né copre le run lifecycle. La pubblicazione non promette hook per worker che nessun probe ha dimostrato.

Tri-Tech Code consuma il pacchetto OpenCode. La destinazione nei dati privati dell'app, separata per progetto e worktree, resta un requisito dell'intervento 5 e non è supportata dalla prima implementazione di `--out`. Prima di abilitarla serve una prova installata di un writer posseduto dall'app o di un permesso limitato alla run, comprendente il rifiuto di scritture su altri progetti e directory. Non viene concessa un'allowance generale sulle directory esterne. Il meccanismo scelto avrà una specifica nel consumatore; un'eventuale capacità portabile torna agli adapter, senza aggiungere un sesto host o un ramo Tri-Tech nei kernel. L'app possiede il proprio stato, gli eventi e la retention. Le decisioni condivise restano nei repository. Il comportamento pubblico resta verificabile sugli altri host con `.daodan/` come default.

La composizione scelta verifica disponibilità dei metodi, input/output, vincoli di autorizzazione e consegna di ogni passo. Non usa `invoke` per eseguire un altro workflow. Il riuso di `superpowers` richiede prove su versioni identificate nei cinque ambienti installati, inclusi helper, modalità di esecuzione e review finale. La presenza della dipendenza nei manifest non dimostra che l'installazione nativa OpenCode o Pi e i suoi helper funzionino. Il workspace e il ledger upstream, quando prodotti, vengono riferiti dalla run senza duplicarli o dichiararli confinati dalla policy dei record lifecycle. La generazione dei pacchetti non certifica da sola l'esecuzione dei metodi.

## 9. Migrazione in interventi separati

| Intervento | Ambito e gate |
|---|---|
| **0a. Contratti condivisi e primo consumatore** | Rifiutare `invoke` valorizzato. Creare `project-contracts` con schemi sotto `contracts/` e metodo di validazione sotto una skill. Implementare export degli schemi, `shared_schemas` e la dichiarazione di `payload_schema` nel modello, loader, validatori e rendering, con il payload opaco per il compilatore e validato a runtime dal consumatore. Formalizzare la separazione fra decisioni e disposizioni del §4, gli stati e le transizioni del §8. Migrare atomicamente i sette contratti di `team-review`; solo `senior-review` acquisisce qui la nuova dipendenza. Verificare distribuzione senza copie nei consumatori, caricamento e validazione sui cinque pacchetti installati. Caratterizzare il permesso OpenCode per una destinazione esterna al progetto e documentare il limite di `--out`. Nessun workflow lifecycle entra in questo intervento. |
| **0b. Metodo caricabile di cleanup** | Promuovere il solo Step 7c a `application-cleanup-method`, aggiornando il puntatore nel fix-loop. Portare i prerequisiti di 7a e 7b, albero pulito, baseline e `--commit`. Verificare caricamento da `code-review` e da un chiamante indipendente nella prova, più il rifiuto dell'esecuzione quando i prerequisiti mancano. Nessuna estrazione da altri plugin. |
| **1. Contratti e diagnosi** | Costruire `assess` su un progetto campione dopo 0a. Introdurre `.daodan/`, la sentinella `.daodan-root`, la policy dei record e l'esclusione C5 per nome, provata anche con `tidy` autonomo e radice personalizzata dentro una directory candidata alla rimozione. Nessuna dimensione e nessun prompt di rilevazione nuovi: `assess` dispaccia i ruoli della mappa del §3. Eseguire i quattro spostamenti, lasciando il puntatore nel comando di partenza: procedura del consumatore X-ray, consolidamento di `team-review`, passo 4 di `audit`, Step 1 e 2 di `test-audit`. Aggiungere al proprietario delle istruzioni il solo parametro audit-only. Verificare comportamento precedente dei quattro comandi e assenza di modifiche al sorgente da `assess`, anche quando gli auditor propongono correzioni. Adottare il risultato comune nei proprietari usati; introdurre il wrapper diagnostico di `workspace-auditor` con test del formato dei finding. Fino all'intervento 3 `knowledge` copre istruzioni e documentazione stantia; deriva per dimensione e README restano non coperti. Provare sui cinque pacchetti installati esecuzione in contesto dell'X-ray, identità della run in concorrenza e al fallimento, input, consegne, limiti dei writer e destinazioni interne. Dichiarare validità delle evidenze ed eseguibilità delle azioni. |
| **2. Riparazione delimitata** | Costruire `repair` con i proprietari esistenti, preservando i gate; il cleanup in bulk richiede 0b. Rendere caricabili i metodi dei test e di `tidy` al loro primo uso. Formalizzare il formato nativo di `tidy`, risolvere nel proprietario la divergenza C5/untracking e introdurre convertitore, mapping e test di contratto. Abilitare la riparazione strutturale del §3, anticipando l'uso di planning/esecuzione `superpowers`. Provare su tutti gli host installati handoff, esecuzione upstream, verifiche, ripresa e consegna, oltre a un caso reale di duplicazione con comportamento conservato. La riparazione coordinata della conoscenza resta non eseguibile fino all'intervento 3, come dichiara il piano di `assess`. |
| **3. Conoscenza unificata** | Migrare i tre plugin direttamente in `project-knowledge`, organizzando qui i metodi caricabili di conoscenza e adottando `project-contracts`. Spostare nella skill la tabella dei controlli di deriva e la checklist di audit del README; rendere caricabile il contratto audit-only della documentazione e provarne il rispetto. Completare la copertura del focus `knowledge`, mantenendo separate diagnosi e modifica. Accettare il costo di installazione dichiarato nel §4. Abilitare la relativa riparazione e provare le informazioni contraddittorie. Aggiornare tutti i consumatori e gli elementi elencati sotto, pubblicare la tabella degli ID ed evitare copie parallele dei corpi. |
| **4. Prevenzione e consolidamento** | Aggiungere `change` e `consolidate`, dopo il percorso di riparazione. Estrarre i metodi ancora necessari al loro primo uso. `consolidate` assume la classificazione delle run, la verifica della ripresa e la retention, senza affidarle a C5. Completare le adozioni del protocollo previste nel §4. |
| **5. Motore Tri-Tech Code** | Integrare il ciclo nei servizi per progetto, con invalidazione incrementale e contesto pertinente per l'agente. Abilitare la destinazione privata soltanto dopo il gate di permessi e scrittura limitata del §8. Questo intervento ha una specifica e un piano propri. |

Le prove di distribuzione di 0a e caricamento di 0b non sostituiscono quelle dei percorsi completi. `assess` viene presentato funzionante soltanto dopo il gate dell'intervento 1; `repair` dopo quello dell'intervento 2, dichiarando le capacità ancora non disponibili. Il limite sui percorsi esterni resta esplicito finché non esiste un meccanismo verificato.

Ogni intervento ha una propria specifica, piano e verifica. I kernel e gli adapter rimangono le fonti; gli export e i cataloghi si rigenerano. Le modifiche a plugin richiedono i bump, il build per tutti gli host e i gate previsti dal repository. Le istruzioni native si aggiornano dalla copia canonica e si sincronizzano.

### Superficie della migrazione degli ID

- Manifest, dipendenze, sidecar, ruoli, skill e riferimenti runtime di tutti i kernel consumatori.
- `scripts/lint_host_vocabulary.py`: esenzione stretta di `project-setup/examples/` e le tre voci `GRANDFATHERED` di mapper. I tre corpi vengono neutralizzati e le voci rimosse, senza trasferire o aumentare la baseline per fare passare un nome nuovo. L'esenzione dei file che trattano il tooling resta motivata nel nuovo percorso.
- `scripts/lint_bundled_paths.py`: il riferimento `AUDIENCE` e ogni altro percorso legato ai kernel rinominati; inoltre linter delle dipendenze, registrazione e fact anchor per le invarianti interessate.
- `CLAUDE.md`, inclusa la tabella delle dipendenze e le regole di ownership; poi sincronizzazione di `AGENTS.md` e delle skill native, senza editing delle copie generate.
- `README.md`, `docs/plugins/`, guide di installazione e migrazione, eval, test di contratto e fixture interessate.
- Cataloghi, pacchetti dei cinque host, provenance e eventuali fingerprint degli override, tutti rigenerati.
- Consumatore esterno Tri-Tech Code: catalogo, pin di revisione, mapping degli ID e integrazione. L'aggiornamento appartiene al suo repository e alla sua pubblicazione, non al build Daodan.

La verifica finale cerca i vecchi ID nell'intero repository e classifica ogni occorrenza rimasta come storia o riferimento attivo. I riferimenti storici mantengono il contesto; nessun consumatore runtime resta sul contratto sostituito.

## 10. Criteri di valutazione

| Caso rappresentativo | Comportamento da osservare |
|---|---|
| Una feature ha già implementazione e test | Il percorso trova il materiale e lo estende dove appropriato |
| Un test codifica un bug corrente | L'aspettativa viene confrontata con il requisito; il risultato non diventa affidabile attraverso la sola esclusione |
| Due test sembrano duplicati ma proteggono failure mode diversi | La differenza viene conservata e spiegata |
| Un refactor lascia invariato il comportamento | La protezione resta valida; il cambio di struttura non giustifica da solo il ritiro dei test |
| Una modifica contraddice un documento non toccato | Il percorso identifica la conseguenza oltre il diff |
| Una campagna produce output pesanti e risultati utili | Il consolidamento conserva risultati verificati e provenienza; il report distingue byte spostati ed eliminati |
| Un residuo ha funzione o provenienza incerta | Rimane da chiarire e non viene dichiarato inutile |
| La run è interrotta o un worker non consegna | Stato e limiti restano ricostruibili; il risultato non viene presentato completo |

Gli eval misurano comportamenti su progetti campione, con versioni identificate e sessioni nuove. Le prove sui corpi delle skill e quelle sul pacchetto installato sono evidenze distinte. Il giudice non riceve la soluzione dal worker; la condivisione delle premesse è dichiarata. I test del compilatore verificano distribuzione e contratti strutturali, mentre gli eval verificano il metodo.

La prima implementazione è riuscita quando il percorso `assess` e `repair` produce interventi motivati e verificati, mantiene la protezione significativa e rende leggibili problemi aperti e conseguenze. Il numero di plugin o di file rimossi non è il criterio di riuscita.
