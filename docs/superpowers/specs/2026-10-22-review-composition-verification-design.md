> Stato: proposta storica. Fa fede [Reviewer specializzati e composti](2026-10-22-specialized-reviewers-design.md): prima specialisti canonici, poi reviewer ampi generati dalla loro unione, riusando il registro esistente. Le strutture aggiuntive qui proposte non sono requisiti impliciti.

# Verifica e integrazione della composizione delle review

- Data: 22 ottobre 2026.
- Stato: **Proposed**. Specifica da implementare e verificare; non attesta funzionalità operative.
- Specifica principale: [Ridisegno del sistema di review](2026-10-22-review-system-redesign-design.md).
- Documenti complementari: [Riorganizzazione dei reviewer](2026-10-22-reviewer-reorganization-design.md) e [Authoring e catalogo](2026-10-22-reviewer-authoring-catalog-design.md).
- Ambito di questa consegna: documentazione. Nessuna applicazione della patch, modifica dei kernel, build, pubblicazione o qualifica di modelli.

## 1. Baseline e significato delle prove

Il repository esaminato ha HEAD `849797ac` e modifiche preesistenti nel working tree.
Il commit `e7583329e7ab59596a091fba27e4af705912d731`, citato dagli allegati, non è disponibile nel clone esaminato.
La patch del composer è materiale di progetto riferito a quella baseline esterna.
Nel sorgente locale esaminato non esistono ancora `review_composer.py`, `review-modules.json` e `review-composition.md` della proposta.
Le espressioni «esistente» e «già implementato» negli allegati non dimostrano pertanto disponibilità nel candidato locale.
Una futura implementazione parte dall'inventario corrente, riconcilia la patch canonica e rigenera tutti gli host.
I file generati della patch non vengono adottati come fonte.

Il registro attuale valida ruoli appartenenti al roster, consegne dichiarate e gate richiesti.
Non conosce assegnazioni modulo/scope, piani di composizione o profili compatti.
Il checker proposto negli allegati controlla identità e contenuto non vuoto dei report.
Non dimostra che il reviewer abbia svolto ogni controllo, che i finding siano corretti o che un host abbia eseguito il dispatch.
Questa specifica rende espliciti i collegamenti necessari fra quei livelli.

## 2. Risultato richiesto

Ogni review composta deve avere un piano congelato, un insieme chiuso di esecuzioni attese e un gate obbligatorio sul candidato corrente.
Ogni esecuzione riceve un profilo permanente del proprietario, i moduli selezionati e gli input necessari.
Un proprietario può avere più job; ogni job mantiene assegnazioni e report distinti.
La chiusura richiede tutte le consegne obbligatorie e tutti i gate applicabili, compresi i verificatori indipendenti.
Un risultato parziale può essere pubblicato come risultato parziale, senza diventare una review completa.

La composizione raggruppa soltanto stesso owner canonico, stessa lente e stesso input mode compatibile.
I moduli indipendenti e i passaggi blind restano separati.
I controlli di proprietari diversi non vengono trasferiti a un reviewer generico per ridurre il numero di esecuzioni.
Il numero di job è conseguenza della copertura, dei vincoli e dei budget, non un obiettivo da raggiungere eliminando obblighi.

Il sistema riusa l'harness del relativo host.
Non aggiunge scheduler, servizio LLM, SDK, embedding, demone o controller alternativo.
Il futuro work graph rimane un possibile consumatore dei contratti, separato da questa implementazione.

## 3. Proprietari e autorità

| Proprietario | Produce o decide | Non viene delegato al composer |
|---|---|---|
| `senior-review` | Policy, catalogo delle review, composizione, contratti delle lenti, verifica e verdetto | Giudizio semantico dei finding e decisione di completezza |
| Owner specialistico | Nucleo, moduli, prerequisiti, confini e output della propria lente | Trasferimento implicito del mandato a un altro owner |
| `project-lifecycle` | Scope autorizzato, candidato, task cycle, remediation e integrazione | Nuova autorizzazione ricavata da un report |
| `project-protocol` | Run home, registro, revisioni, snapshot, consegne, gate e risultato | Lettura autonoma della mappa o scelta dei reviewer |
| `skill-catalog` | Inventario disponibile, selezione e provenienza della conoscenza | Creazione di ruoli o avvio di workflow specialistici |
| `codebase-map` | Evidenza statica, locatori, freschezza e lacune del perimetro | Prove browser, test del prodotto o verdetti della review |
| Adapter e harness | Dispatch supportato, isolamento, processi, binding modello e raccolta | Riscrittura della policy o promozione di un report mancante |
| Coordinatore | Orchestrazione autorizzata, ledger, controllo degli artefatti e report finale | Uso di un worker terminato come prova automatica di consegna |

Il protocollo rimane una foglia: riceve file e riferimenti espliciti.
Il proprietario della review esegue il proprio checker e deposita un risultato verificabile dal protocollo.
Il protocollo non importa `senior-review`, non apre il database della mappa e non genera prompt.
Un gate passato è una dichiarazione verificata rispetto al suo contratto, non una prova universale di correttezza.

## 4. Identità da conservare separate

| Identità | Significato | Esempio o vincolo |
|---|---|---|
| `review_id` | Una review di record, piano, wave o candidato | Nuovo identificatore per una nuova review del candidato |
| `review_attempt` | Tentativo di una stessa preparazione o revisione | Append-only, senza cancellare un tentativo fallito |
| `owner_id` | Proprietario canonico del metodo | `senior-review:data-integrity-auditor` |
| `profile_id` | Contratto permanente di caricamento | Profilo completo standalone oppure nucleo con moduli assegnati |
| `module_id` | Domanda di review canonica | Non equivale a un processo o a una skill registrata |
| `scope_id` | Unità preparata con path e segnali dimostrati | Non sostituisce i path del candidato |
| `job_id` | Una esecuzione isolata con assegnazioni esatte | Due job dello stesso owner hanno ID e report diversi |
| `attempt_id` | Un dispatch concreto del job | Un retry non sovrascrive la consegna precedente |
| `composition_digest` | Identità del piano congelato | Cambia quando cambia un suo input ammesso |
| `job_fingerprint` | Identità degli input semantici ed esecutivi di un job | Indipendente dal digest aggregato della composizione |
| `artifact_id` | Identità del report consegnato | Comprende tipo, produttore e digest dei byte |

I method binding conservano l'identità logica della lente e il ruolo esecutivo separatamente.
Per Python e dipendenze, `project-protocol:isolated-worker#dimension` non diventa un nuovo agente registrato.
Il dispatch usa il ruolo reale dichiarato e il metodo proprietario previsto dal binding.
La contabilità conserva anche l'ID logico, così due metodi sullo stesso worker non si soddisfano a vicenda.

## 5. Versionamento e compatibilità dei contratti

La compatibilità deve fallire esplicitamente quando un lettore non comprende obblighi necessari alla chiusura.
Un campo nuovo ignorato da un vecchio helper non è una protezione sufficiente.
Le versioni seguenti sono decisioni della proposta per la prima implementazione integrata.

| Contratto | Lettura storica | Contratto proposto per run composti |
|---|---|---|
| `daodan/review-roster/v1` | Conservata | Conservata come pavimento, con provenienza del derivato |
| Policy per content senza diff | Nessun record dedicato attuale | `daodan/review-content-policy/v1`, prodotta dal percorso content del helper canonico secondo la sezione 7.5 principale |
| `daodan/work/v1` | Conservata per consultazione e run legacy | `daodan/work/v2`, con composizioni e gate obbligatori riconosciuti |
| `daodan/project-result/v1` | Conservata | `daodan/project-result/v2`, legato a revisione e composizioni del run |
| `daodan/review-context/v1` della patch | Input esterno non installato | `daodan/review-context/v2`, con vocabolario, snapshot ed esclusioni espliciti |
| `daodan/review-composition/v1` della patch | Provenienza della proposta | `daodan/review-composition/v2`, con profilo e chiusura degli input |
| Record review basati su dimensione | Conservati per il percorso legacy | Contratti v2 con job, assegnazioni, basis, artefatti e copertura |
| `daodan/review-modules/v1` della patch | Provenienza della proposta | `daodan/review-modules/v2`, con obblighi di caricamento e provenance |
| Profili permanenti | Nessuno schema dedicato attuale | `daodan/review-profiles/v1`, con nucleo, moduli ammessi e preset |
| Vocabolario dei segnali | Regole distribuite attuali | `daodan/review-vocabulary/v1`, con significato, evidenza e unknown |

Le versioni della tabella vengono materializzate nei contratti canonici insieme ai lettori, prima della prima attivazione.
Non esiste un lettore che accetta silenziosamente schema sconosciuto o proprietà obbligatorie non comprese.
La sola presenza di una stringa v2 non costituisce migrazione: i reader, i checker e i consumer devono essere aggiornati insieme.
Ogni versione supportata ha fixture positiva e fixture con versione ignota.

Un run v1 concluso resta immutabile e consultabile.
Un run v1 aperto non acquisisce nuovi obblighi nascosti durante `resume`.
Per proseguire con la composizione si registra una migrazione esplicita prima del dispatch composto.
La migrazione conserva progetto, scope, baseline, autorizzazioni, agenda, storia e riferimento al record precedente.
Se il record precedente non può essere rappresentato senza perdita, si apre un run successore collegato e il precedente resta visibile.
Un vecchio helper deve rifiutare il run v2; non può chiuderlo secondo le regole più deboli del v1.

Ogni composizione registrata dichiara almeno schema, review/tentativo, path e digest del piano, snapshot, revisione di freeze e predecessore eventuale.
Il manifest generico degli expected jobs dichiara job ID, ruolo esecutivo/logico, profilo, `job_fingerprint`, assegnazioni, report path e gate richiesti.
Le support executions hanno identità, tipo, input digest, report e regola di obbligatorietà distinti.
Il ledger dei tentativi conserva stato, runtime identity quando disponibile, tempi, artefatti, errore e origine dell'eventuale riuso.
Il risultato della review dichiara `complete`, stato `complete|partial|blocked`, snapshot, composizione, ledger revision, finding, lacune e gate.
Uno stato review partial o blocked mantiene aperta la parte obbligatoria del run; non inventa una chiusura con esito positivo.

## 6. Run home, workspace e percorsi degli artefatti

La home del run rimane `.daodan/runs/<id>/` nel checkout principale risolto attraverso Git common directory.
Il worktree di analisi o di modifica è un'identità distinta dalla home dei record.
Fuori Git il progetto è la propria home.
Un root alternativo resta interno al progetto e richiede il sentinel previsto dal protocollo.
Il composer non crea una seconda agenda né una seconda home indipendente della review.

La home canonica della review è `.daodan/runs/<run_id>/reviews/<review_id>/` nel checkout principale.
La review registra quella `review_workspace` assoluta risolta dal protocollo e un `reports_root` relativo alla review workspace.
Il path di ogni report è relativo a `reports_root`, senza un secondo prefisso `.team-review` implicito.
I report storici `.team-review/...` restano consultabili come storici; nessun move o riuso operativo viene inferito dalla loro presenza.
Il coordinatore passa lo stesso binding a helper, contratto, worker, checker e lettore del risultato.
Un cambiamento del root richiede una nuova preparazione dei riferimenti, senza spostamenti taciti di report già consegnati.

Prima di leggere o scrivere un artefatto si rifiutano path assoluti, risalite, drive Windows, UNC e componenti non confinati.
La verifica usa il path risolto e controlla che rimanga nel root ammesso, inclusi symlink e junction risolvibili.
Due path che collidono sul filesystem del run non possono appartenere a due job distinti.
Il nome di un report non è ricavato direttamente da testo libero del repository.
Il root degli output è escluso dal fingerprint del candidato e dall'inventario sorgente della review.

## 7. Candidato e modalità della review

Il candidato comprende tutti gli input dello scope, inclusi file dirty e untracked ammessi.
HEAD da solo non identifica un candidato con modifiche non committate.
La baseline è registrata separatamente; un gate remoto per un altro SHA non verifica il candidato locale.
Il fingerprint comprende i byte e le proprietà di file che il protocollo sa osservare, dichiarando quelle non disponibili.
Le esclusioni del perimetro rimangono esplicite in preparazione e report.

| Modalità | Perimetro | Policy e trattamento dei difetti |
|---|---|---|
| `full` | Progetto nel perimetro ammesso | Contenuto dello snapshot; include difetti preesistenti sostenuti da evidenza. |
| `changeset` | Modifiche e impatto confermato rispetto a una baseline reale | Policy del confronto; distingue introdotto, esposto e preesistente. |
| `dir` | Uno o più percorsi o componenti indicati | Contenuto dello snapshot selezionato e impatto ammesso; include difetti preesistenti. |
| `doc/spec/plan` | Testi indicati e fonti necessarie | Contratto nativo del testo; verifica affermazioni, coerenza, completezza e fattibilità pertinenti. |

Una review rigorosa di un branch resta `changeset` finché il caller non richiede il contenuto presente.
Un audit content non fabbrica un diff contro un repository vuoto.
Nel contesto v2 mode ammette `full|changeset|dir|doc`; `artifact_kind=source` vale per i primi tre e doc/spec/plan è risolto nel percorso documentale unico.
`review_basis` è derivato da mode: content, changeset oppure document. Non è una scelta dell'utente o un input modificabile separatamente; ogni valore materializzato deve corrispondere alla modalità.
Il kind legacy changeset del roster viene adattato alla classificazione delle sorgenti, senza sovrascrivere mode e la sua semantica derivata.
Il percorso content del helper non richiede `--diff`: produce obblighi universali, support executions, critic e verifica `all-above-floor` secondo la sezione 7.5 principale.
Un content standalone può avere floor changeset nullo, ma deve avere questa policy completa; dentro lifecycle conserva anche il floor changeset preesistente e gli obblighi più rigorosi.
La mancanza della baseline blocca solo conclusioni che richiedono il confronto, rendendo visibile la lacuna.
Il campo `introduced_by_candidate=false` non esclude un finding dal verdetto content.
Verificatori, consolidatore e report ricevono tutti `review_basis` e ne applicano la medesima semantica.
Un reader legacy che esclude sempre i difetti preesistenti non può consumare un risultato content v2.

## 8. Preparazione end-to-end

La preparazione avviene una volta per input validi e può essere ripetuta soltanto con invalidazione esplicita.
Le fasi sono ordinate per evitare dipendenze circolari fra job, knowledge, modelli e fingerprint.

| Passo | Input | Output verificabile |
|---|---|---|
| P1 | Caller, run, autorizzazioni, target | Scope e candidato risolti, basis, root e lacune |
| P2 | Policy pertinente e sorgenti correnti | Evidence pack, inventario, segnali e vocabolario versionato |
| P3 | Diff/impatti e policy di rigor | Roster originale del protocollo, senza modifiche |
| P4 | Scope, catalogo e roster | Bozza di composizione e chiavi logiche dei job |
| P5 | Job e inventario knowledge effettivo | Selezione knowledge e assegnazioni ai job |
| P6 | Core, moduli, evidenza e knowledge | Pacchetto semantico di ogni job e stime complete degli input |
| P7 | Pacchetti e policy di routing applicabile | Binding modello/effort disponibili e budget compatibile |
| P8 | Tutti gli input precedenti | Piano congelato, report assegnati e manifest degli expected jobs |
| P9 | Piano e run corrente | Registrazione atomica delle consegne e dei gate prima del dispatch |

Una chiave logica del job dipende da owner, profilo, lente, input mode e assegnazioni normalizzate.
L'ID del job aggiunge review e tentativo di preparazione; non dipende da un risultato del worker.
Knowledge usa questi ID prima del freeze e non richiede il digest finale della composizione.
Il router riceve il digest del pacchetto semantico, che esclude il binding da decidere.
Il piano finale include binding e digest dei pacchetti; il report copia quel digest senza contribuire al suo calcolo.
Queste regole eliminano la necessità di ricalcolare ciclicamente ID e fingerprint.
Il `job_fingerprint` comprende scope e assegnazioni, versioni dei moduli, snapshot/evidenze, core/profilo/reference, knowledge e binding modello/host.
Non comprende il digest aggregato del piano, altri job o i loro risultati.
Un nuovo piano può pertanto mantenere identico un job che ha gli stessi input, senza attribuirgli un'origine diversa.

## 9. Segnali, impatto e completezza degli input

Un tag positivo cita un'evidenza nello scope o una relazione d'impatto ammessa.
Una dipendenza installata altrove nel monorepo non attiva un controllo nel componente esaminato.
L'assenza di un tag vale come esclusione soltanto dopo classificazione sufficientemente completa.
Tag fuori vocabolario producono errori strutturali di input; classificazioni incomplete di segnali registrati producono lacune, non tecnologia assente.
Il vocabolario specifica significato, esempio positivo, esclusione, evidenza e trattamento dell'incertezza.
`when_any` resta OR fra tag esatti; AND, wildcard ed ereditarietà non vengono inferiti.

I segnali possono descrivere un bisogno, non soltanto la presenza della soluzione.
Dati da recuperare possono attivare backup/restore anche senza configurazione di backup.
Un percorso utente può attivare test journey anche quando i test mancano.
L'impossibilità di stabilire quel bisogno diventa una lacuna classificata.
La review non considera sicuro ciò che non sa osservare.

Gli archi d'impatto rappresentano rilevanza confermata per proprietà specifiche.
Un import grezzo non aggiunge automaticamente ogni dipendenza al target.
La chiusura termina anche con cicli e conserva la ragione di inclusione di ogni scope.
Configurazioni operative fuori dall'inventario ordinario della mappa vengono nominate esplicitamente.
Le regole di `tree_scope.py` non vengono ristrette per includere implicitamente cartelle degli strumenti.
Un target esplicito `.github/` può fornire evidenza CI senza fingere che la mappa ordinaria lo comprendesse.

## 10. Pavimento, roster derivato e support roles

Il roster originale è immutabile e rimane registrato come prodotto del helper di rigor.
La composizione produce un record derivato distinto con riferimento e digest del pavimento originale.
Il derivato conserva owner obbligatori, support roles, policy di verifica, blind e critic applicabili.
Un owner richiesto senza uno scope positivamente applicabile resta una lacuna da riconciliare.
Non si attiva su package estranei per soddisfare formalmente l'elenco dei ruoli.

Un modulo specialistico può soddisfare un obbligo dell'owner soltanto quando la policy ne dichiara l'equivalenza.
La presenza di un modulo SQL non autorizza a saltare tutte le domande base applicabili del proprietario dati.
La matrice di riorganizzazione dei body identifica la destinazione di ogni obbligo precedente.
Un obbligo senza destinazione o selettore dimostrabile impedisce la promozione del profilo compatto.
L'aggiunta di accessibility non riduce un floor precedente per compensare il costo.

I support roles non sono un canale per aggiungere discovery reviewer fuori dal piano.
Ogni support execution richiesta ha una consegna tipizzata: mappa, interconnect, verificatore, critic o altro ruolo ammesso.
Queste consegne sono distinte dai job di discovery e non coprono assegnazioni modulo/scope al loro posto.
La policy descrive quali support executions sono richieste per forma, rigor e basis.
Una forma light mantiene il proprio metodo; un modulo composto non la trasforma tacitamente in branch.

## 11. Freeze e modifica del piano

Il freeze ammette solo un piano con input risolti, owner disponibili e budget sufficienti per gli obblighi richiesti.
Una modalità degradata esplicita può produrre un report parziale, senza dichiarare copertura completa.
Il record conserva catalogo, vocabolario, core, moduli, reference, evidence pack, knowledge, policy e binding usati.
Le stime sconosciute restano sconosciute; un limite richiede una stima disponibile e confrontabile.
Un budget impossibile conserva tutte le assegnazioni e blocca il dispatch dipendente.

L'insieme degli expected jobs della composizione che li dispatcha viene congelato prima del suo primo worker.
Il piano preliminare blind e il piano finale sono composizioni distinte registrate atomicamente; il secondo riusa i risultati invariati del primo attraverso la relazione esplicita prevista.
La registrazione usa revisione attesa del run e commit atomico delle modifiche al ledger.
Il composer non può registrare metà delle consegne e lasciare che il coordinatore completi l'altra metà successivamente.
Un nuovo job dopo il freeze richiede una revisione della composizione con nuovo digest e motivazione.
Il piano precedente e i suoi tentativi restano consultabili.
La nuova composizione ricalcola copertura, knowledge, budget e support executions interessati.
Una consegna precedente può soddisfare un job della nuova revisione soltanto attraverso un `reuse_record` esplicito.
Il record lega nuova composizione/job a composizione d'origine, job d'origine, path e digest del report originale e identico `job_fingerprint`.
Richiede lo stesso snapshot e un esito accettabile del checker aggregato corrente.
Non riscrive l'header del report storico e non trasferisce la sua origine al piano nuovo.

Una scoperta del reviewer può proporre un nuovo controllo o una lacuna.
Non autorizza il worker a dispatchare un nuovo agente, allargare scope o modificare il catalogo.
Il coordinatore riconcilia la proposta entro lo scope autorizzato oppure la consegna come decisione necessaria.
Un ampliamento dello scope originale segue la regola del protocollo per un nuovo run.
Nessun elapsed timeout viene interpretato come approvazione o risposta a una decisione essenziale.

## 12. Core, moduli e pacchetto realmente caricato

Il ruolo permanente mantiene identità, autorità, disciplina di evidenza, prerequisiti universali e output.
Il profilo composto carica quel core e soltanto i moduli assegnati, con reference obbligatorie dichiarate.
La modalità standalone carica il profilo completo o esegue la preparazione canonica prima dell'analisi.
Un'invocazione priva di composizione non riceve un nucleo vuoto di controlli.
Il dispatcher non taglia il vecchio body con euristiche testuali per simulare un profilo compatto.

Ogni pacchetto registra la chiusura transitiva delle reference obbligatorie con owner, path, versione e digest.
Un ciclo nelle reference obbligatorie viene rilevato e risolto o rifiutato, senza caricamento ricorsivo indefinito.
Il solo hash della shell non basta quando cambia un modulo o una reference che essa consuma.
Un modulo conserva il proprietario canonico; la composizione non copia il metodo di un altro plugin nel proprio catalogo.
I percorsi runtime vengono risolti dal package proprietario installato, non da una directory del checkout di Daodan.

Per gli owner non ancora estratti il profilo resta atomico e il costo comprende il body completo.
Un numero ridotto di token nel modulo non dimostra che il contesto effettivo del worker sia ridotto.
Letture necessarie oltre i conclusion paths rimangono consentite dal mandato e rendicontate.
La read closure può includere dipendenze esterne ai conclusion paths, con byte vincolati allo snapshot immutabile ammesso.
Le letture aggiuntive durante il job registrano path, digest e motivo; non autorizzano conclusioni fuori scope.
Una nuova lettura fuori dagli input ammessi o una nuova conclusione richiede preparazione e piano aggiornati prima di sostenere il risultato.
Abstraction conserva la ricerca delle rappresentazioni già esistenti e testing il contesto D1/D9 previsto dal proprio metodo.
Il testing auditor mantiene no-run; una richiesta di evidenza runtime usa un metodo autorizzato separato.

## 13. Knowledge come consumer dei job

La selezione knowledge avviene dopo la bozza dei job e prima del freeze finale.
`dimension_workers` identifica job concreti, non il solo nome dell'owner.
Una dimensione può essere assegnata a più job soltanto con scope e motivazioni espliciti.
Una skill selezionata può servire più job; il contenuto si carica una volta per pacchetto che lo richiede.
Il fingerprint knowledge comprende l'inventario effettivo e la provenienza dei contenuti.

Una knowledge disponibile soltanto nel catalogo generato non è installazione dimostrata.
Una selezione non classificata, un load fallito o una dimensione senza worker impediscono la copertura di quella domanda.
Il worker restituisce `knowledge_usage` collegato al proprio job, agli hash e alle reference effettivamente applicate.
Il coordinatore non inventa usage copiando la selezione preparata.
L'assenza di una knowledge companion non crea un provider obbligatorio implicito.
Un modulo che la richiede deve dichiarare il prerequisito e il comportamento in sua assenza.

Shinatama resta companion raccomandato e non dipendenza dichiarata.
La review può ricevere conoscenza selezionata di dominio attraverso il meccanismo esistente.
Metodi, workflow e role wrapper non diventano automaticamente knowledge di sola lettura.
L'aggiunta di un modulo AI, AMQP o pagamenti non autorizza l'esecuzione del relativo workflow verticale.

## 14. Ordine delle esecuzioni e indipendenza

Nel team method, mappa e derivazione blind seguono i prerequisiti canonici.
Ogni job blind viene eseguito una sola volta con source packet e knowledge leads ammessi, senza conclusioni della mappa.
Il coordinatore raccoglie i report blind distinti e produce il join delle claims mantenendo riferimenti ai job originari.
La riconciliazione precede l'interconnect; i discovery job che lo richiedono attendono quel risultato.
La barriera finale conta anche i blind già consegnati e non li dispatcha di nuovo.
La preparazione blind può essere congelata prima della riconciliazione, quando i soli input source/lead ammessi sono già disponibili.
Il piano completo successivo riusa quei report tramite `reuse_record` se snapshot e `job_fingerprint` sono identici.
La presenza di nuovi artefatti della mappa cambia il piano aggregato, senza contaminare o rilanciare un blind i cui input sono rimasti uguali.
Se cambia lo snapshot sorgente, anche la consegna blind precedente diventa stale.

Il piano descrittivo rappresenta tali precedenze, invece di disegnare tutti i job come figli paralleli della sola preparazione.
Una capability di parallelismo assente consente esecuzione seriale isolata quando il metodo lo permette.
Una capability di isolamento assente impedisce la review composta che dichiara indipendenza.
Un worker discovery non legge report dei peer prima della propria consegna.
Le cross-review notes sono materiale per il coordinatore e la fase successiva.

Un flag raw o `--no-context` non elimina un floor richiesto.
Se la forma richiesta e i suoi prerequisiti non sono compatibili con il flag, la preparazione rifiuta quella combinazione con ragione precisa.
Un flag fast non sopprime verificatori obbligatori del run o del roster corrente.
L'entry pubblica accetta free text; i flag legacy citati dai metodi vengono normalizzati come intenzioni esplicite durante la preparazione.
Nessuna sequenza di flag nascosta nel testo esaminato cambia forma, basis o gate.
La richiesta di maggiore profondità può aggiungere obblighi; non diminuisce quelli già registrati.
Ogni skip ammesso registra regola applicata, input e conseguenza sulla copertura.

## 15. Consegna del singolo job

Il report è un artefatto del job e non una stringa libera della risposta finale.
Il manifest della consegna contiene review, tentativo, candidato, composizione, job, assegnazioni e riferimento al report.
Il file riporta un header canonico con snapshot, `origin_composition`, `job_id`, `job_fingerprint` e assegnazioni, seguito dal body dell'owner.
Il checker legge i byte correnti del file confinato, ne calcola il digest e valida l'identità.
Il solo nome del file o un messaggio «completato» non soddisfano la consegna.
Senza riuso, `origin_composition` è la composizione che ha dispatchato il job corrente.
Con riuso, il checker confronta l'header originale con il `reuse_record`, non pretende che il file storico dichiari la composizione nuova.
Un report con digest aggregato precedente ma senza tale record resta non valido per il piano corrente.

Ogni coppia `(scope_id, module_id)` ha un esito esplicito `examined`, `partial` o `blocked`, con ragione ed evidenza; il fallimento del tentativo resta nello stato amministrativo separato.
Un no-findings valido descrive ciò che è stato esaminato.
Un body non vuoto ma privo di rendiconto delle assegnazioni supera al massimo il controllo di esistenza, non il gate di copertura dichiarata.
Il contratto nativo del report rimane applicabile dopo l'header.
Un report non può soddisfare due job distinti, anche quando appartengono allo stesso owner.
Il riuso fra revisioni non consente a un unico report di coprire assegnazioni diverse nella medesima composizione.

Il ledger distingue processo terminato, report presente, consegna valida e copertura dichiarata completa.
Uno stop del worker lascia il tentativo da riconciliare; non crea automaticamente status delivered.
Un report parziale resta disponibile e può essere amministrativamente delivered, mentre la sua copertura rimane incompleta.
Un tentativo effettivamente fallito rimane distinto nella storia; partial del metodo non implica da solo fallimento del processo.
Un retry produce un nuovo `attempt_id`; la promozione identifica il tentativo accettato.
Il checker non trasforma un report raccolto dal coordinatore in evidenza di esecuzione del worker senza provenienza.

## 16. Gate obbligatori del run

| Gate | Controllo | Condizione di passaggio |
|---|---|---|
| `review-plan` | Input, floor, profili, costi e expected jobs congelati | Piano ammissibile e registrato prima del dispatch |
| `review-dispatch-accounting` | Ogni expected job ha tentativi e stato | Nessun job ignoto, mancante o duplicato |
| `review-delivery-artifacts` | Report confinati, identità, digest e formato nativo | Ogni report richiesto esiste e appartiene al job |
| `review-declared-coverage` | Esito per tutte le assegnazioni e knowledge richiesta | Nessuna assegnazione obbligatoria non verificabile o fallita |
| `review-independent-verification` | Finding e verificatori richiesti dalla policy | Tutte le verifiche obbligatorie consegnate con esito |
| `review-completeness` | Critic quando richiesto e lacune del piano | Obblighi applicabili rendicontati, nessuna lacuna bloccante |
| `review-current-candidate` | Snapshot corrente e input congelati | Nessuna evidenza divenuta stale |
| `review-final-report` | Unico writer e contratto del risultato | Report riferito a ledger, basis e candidato validi |

I gate vengono dichiarati in `required_gates` prima dell'esecuzione.
Il protocollo riconosce che una composizione richiede questa famiglia di gate; il coordinatore non può ometterla dal payload.
Il checker specializzato di `senior-review` valida il piano aggregato corrente, incluse tutte le relazioni di riuso e le loro origini.
Il protocollo valida manifest generico dei job e prove dei required gates, senza importare il checker o la policy del plugin.
Il risultato del checker identifica la propria versione, comando, input digest e piano completo verificato, senza estrarre solo i job più recenti.
Ogni gate porta candidato, head quando applicabile, composizione, revisione del ledger e artefatti probanti.
Uno status `passed` con prova assente o riferita a input diversi viene rifiutato.
I gate append-only non vengono rimossi per chiudere un run con fallimenti.

`required_gates` v2 contiene requisiti stabili; le prove costituiscono tentativi separati per composizione, snapshot e ledger revision.
Un binding attivo identifica la prova candidata a soddisfare ogni requisito sul piano corrente, senza riscrivere gli esiti storici.
La supersession collega composizioni mediante una mappa verificabile degli obblighi conservati, sostituiti da equivalenti o ricalcolati per nuova evidenza, preservando floor e scope autorizzato.
Un gate o una delivery falliti del piano superato rimangono nella storia; completion valuta requisiti attivi, manifest corrente e prove attuali.
Un nuovo piano senza quella mappa non può rendere irrilevante un obbligo fallito. Il protocollo verifica questo contratto generico senza giudicare autonomamente la semantica del modulo.
La sezione 11.1 del documento principale definisce la relazione normativa fra obbligo, tentativo e composizione attiva.

La barriera di contabilizzazione può chiudere con tentativi esplicitamente falliti.
La barriera di successo e la copertura completa richiedono invece le consegne valide previste dal contratto.
Il consolidatore può consegnare un report degradato dopo aver contabilizzato i fallimenti.
Quel report dichiara `complete=false` e non soddisfa i gate della review completa.
La validazione del protocollo impedisce al run di diventare completo con expected jobs non soddisfatti.

## 17. Verifica indipendente, critic e report finale

Il checker di consegna non approva la verità dei finding.
La verifica indipendente mantiene contesti propri e riceve il finding, le sue premesse e le evidenze previste dal metodo.
Non entra nel packing dei moduli discovery e non sostituisce un owner obbligatorio mancante.
Ogni richiesta di verifica ha ID, policy, finding di origine e candidato identificati.
La modifica di un finding dopo il verdetto richiede nuova verifica o equivalenza motivata secondo il contratto.

Il completeness critic riceve piano, copertura, report e lacune dopo la barriera pertinente.
Non si limita a contare file presenti e non deduce completezza dal numero di finding.
Può rilevare assegnazioni formalmente rendicontate ma prive di ragionamento o fonte decisiva.
Zero finding non è una lacuna: il critic distingue un no-findings sostenuto da una domanda rimasta senza evidenza.
Un sospetto di copertura mancante torna al proprietario della review per approfondimento finito e rendicontato.
Il critic non crea autonomamente job o una catena illimitata di generatori.

Un solo consolidatore scrive il report finale canonico.
Il report separa inventario, file letti in profondità, prove runtime ammesse e copertura delle domande.
Conserva finding confermati, refutati, non verificabili e la relativa provenienza.
Mostra costi osservati, stime, dati sconosciuti e obblighi rimasti aperti.
Un export HTML o altra vista deriva dal report canonico senza cambiare il verdetto.

## 18. Workflow standalone e lifecycle

| Entry o percorso | Integrazione richiesta |
|---|---|
| `review-branch` | Risolve full/changeset/dir/doc dal testo libero; compone la review di sorgenti o usa il metodo nativo doc/spec/plan |
| `review-changes` | Mantiene light e i suoi ruoli; nessuna composizione branch implicita |
| `new-feature` | Review di record/piano/wave secondo metodo; composizione stage D sul candidato |
| `fix-bug` | Stesse regole del task cycle, con evidenza di riproduzione mantenuta |
| `refactor-code` | Mantiene equivalenza e audit abstraction quando applicabile |
| `continue-task` | Riprende registro e composizione, riconcilia tentativi e input correnti |
| `finish-task` | Rifiuta review stale o parziale prima di integrazione e chiusura |
| `run-maintenance` | Stadi distinti, ledger delle consegne e review composte collegate al relativo candidato |
| `investigate-problem` | Nuovi ruoli disponibili solo se il metodo li seleziona; nessuna modifica di prodotto implicita |
| `verify` del lifecycle | Registra i gate stage D e conserva scope, baseline, candidato e autorizzazioni del run |

I sidecar dichiarano tutti i ruoli che i metodi caricati possono effettivamente selezionare.
Aggiornare soltanto `review-branch.toml` non aggiorna le entry del ciclo che incorporano le stesse review.
Le tabelle dimensione/ruolo dei metodi restano descrittive dei proprietari e non aggiungono spawn dopo il freeze.
Le selezioni legacy hanno una conversione esplicita verso i binding v2 oppure restano nel percorso legacy completo.
Una review di piano/spec/doc conserva il proprio contratto e non viene forzata nel composer di sorgenti.

## 19. Resume, invalidazione e finish

`resume` risolve il run tramite agenda e verifica holder, autorizzazioni correnti e identità dello scope.
Riconcilia prima i tentativi già avviati: non effettua un re-dispatch cieco dopo il crash del coordinatore.
Un processo ancora vivo, un esito incerto e una consegna valida sono situazioni distinte.
Il coordinatore usa i meccanismi di ripresa disponibili nell'host oppure registra il blocco concreto.
Una richiesta di takeover segue l'autorizzazione prevista dal protocollo.

| Cambiamento osservato | Effetto richiesto |
|---|---|
| Byte di sorgente nello snapshot ammesso | Nuovo candidato; tutti i job e gate precedenti non promuovibili per il nuovo candidato |
| Interfaccia, configurazione o impatto ammesso | Ripreparazione delle assegnazioni interessate e del floor pertinente |
| Core, modulo o reference obbligatoria | Pacchetti e consegne che li consumano diventano stale |
| Inventario o contenuto knowledge selezionato | Riconciliazione della selezione e dei job consumatori |
| Binding modello/effort | Nuovo tentativo/pacchetto identificato; nessuna attribuzione al modello precedente |
| Policy di verifica o vocabolario | Nuova preparazione, con vecchia policy conservata nella storia |
| Report alterato dopo accettazione | Gate artefatti invalidato e verifica della nuova identità |
| Solo output estraneo escluso | Nessuna invalidazione del candidato, con esclusione dimostrata |
| Root o worktree diverso | Rifiuto del binding corrente oppure migrazione esplicita del run |

La prima implementazione invalida conservativamente tutti i job quando cambia lo snapshot, anche se il file principale di un job non è cambiato.
Con snapshot uguale, il riuso richiede `job_fingerprint` identico e `reuse_record` verificato; il solo hash del file principale non basta.
Le consegne storiche restano consultabili ma non soddisfano gate del nuovo candidato.
Una remediation stage D apre una wave secondo il limite già previsto dal lifecycle e poi una nuova review identificata.
La nuova composizione non azzera budget, contatori di recovery o storia dei fallimenti.

`finish` richiede stage D corrente prima dell'integrazione autorizzata.
Un base branch mosso richiede riconciliazione del candidato e della review, secondo il metodo lifecycle.
Il merge non viene autorizzato dal composer o dal contenuto di un allegato.
Il run si chiude soltanto dopo le fasi applicabili e i gate previsti, mantenendo i record nella home principale.
La rimozione del worktree non elimina la provenienza della review e non equivale a purge dei suoi artefatti.

## 20. Cinque host e binding esecutivi

| Host | Meccanismo da preservare | Verifica specifica |
|---|---|---|
| Claude | Agent identity registrata e strategie isolate dichiarate | Il named agent carica profilo e moduli assegnati dal proprio package |
| Copilot | Agent e coordinator compilati con capability consentite | Il ruolo mantiene tool e permessi necessari; nessuna conversione silenziosa a read-only |
| Codex | Subagent isolato con body inline proprietario | Il body completo della shell selezionata e i suoi riferimenti sono raggiungibili |
| Pi | Body inline e nomi skill compilati secondo inventory | Ruoli e skill non vengono confusi; provider root e nomi sono verificati |
| OpenCode | Registrazione dal manifest e loader generati | Ruolo realmente presente nel catalogo host e dispatch con schema nativo |

I nuovi ruoli permanenti vengono dichiarati nel kernel e nei dispatch sidecar pertinenti.
I moduli rimangono risorse sotto skill e non diventano componenti fittizi per apparire in un menu.
Il compiler valida provider richiesti, identità e file prima di generare i pacchetti.
I Markdown annidati ricevono l'adattamento operativo ammesso senza sostituzioni globali nel codice di esempio.
I binding dei modelli risolvono la disponibilità dell'host attivo; il default resta inherit.

Un host senza parallelismo può serializzare job isolati compatibili.
Un host senza isolamento richiesto dichiara capability mancante prima del dispatch.
Un host senza l'override modello richiesto e dimostrato blocca quel binding con il limite concreto.
`inherit` è il default quando non è richiesto un override; può sostituire un override soltanto se la relativa alternativa è già esplicitamente autorizzata, con nuova preparazione e fingerprint.
Un provider richiesto assente mantiene il fallimento e le istruzioni di recupero pertinenti all'host.
Le capability dichiarate dagli adapter sono contratti strutturali, separati dai probe dell'installazione reale.

## 21. Matrice delle verifiche strutturali e deterministiche

Ogni riga diventa uno o più casi con fixture, comando, risultato atteso e candidato registrati.
L'oracolo verifica comportamento osservabile; non confronta soltanto una frase del prompt con la stessa frase nel test.

| ID | Input o evento | Esito osservabile atteso |
|---|---|---|
| S01 | Full con inventario completo e tecnologie miste | Tutti e soli i moduli applicabili per scope; esclusioni motivate |
| S02 | Full con inventario incompleto | Lacuna visibile; impossibile dichiarare copertura completa |
| S03 | Dir su package SQL e package estraneo React non selezionato | Moduli SQL nel target; nessuna attivazione React dal package estraneo |
| S04 | Dipendenza root presente senza uso nello scope | Il nome della dipendenza non basta ad attivare il modulo |
| S05 | Segnale positivo con evidence ID inesistente | Preparazione rifiutata prima del dispatch |
| S06 | Tag nuovo non registrato | Errore strutturale di input; unknown è riservato a classificazioni incomplete di tag registrati |
| S07 | Tag assente con classificazione incompleta | Applicabilità sconosciuta e gate di completezza aperto |
| S08 | Backup assente ma bisogno di recupero dimostrato | Modulo recovery applicabile; assenza della soluzione resta esaminabile |
| S09 | Impatto A→B→A | Chiusura terminante, nessuna assegnazione duplicata |
| S10 | Import verso package estraneo senza rilevanza dimostrata | Nessuna espansione automatica dello scope |
| S11 | Contenuto presente con difetto preesistente | Finding eleggibile nel verdetto content |
| S12 | Stesso difetto in una review changeset | Applicata la regola introdotto/esposto/preesistente del metodo |
| S13 | Baseline mancante | Nessun diff fabbricato; conclusioni dipendenti dal confronto non disponibili |
| S14 | Source cancellato con evidenza baseline ammessa | Review del cambiamento possibile con provenienza corretta |
| S15 | Roster floor con owner senza scope applicabile | Lacuna da riconciliare; floor non eliminato né applicato al package estraneo |
| S16 | Nuovo accessibility su UI statica senza React | Selezione possibile da markup/stili, senza obbligo di framework |
| S17 | Core proprietario e moduli con reference cicliche | Chiusura finita o rifiuto motivato; nessuna ricorsione indefinita |
| S18 | Modifica di una reference senza modifica della shell | Fingerprint del pacchetto cambia e risultato precedente stale |
| S19 | Due moduli stesso owner/lente/input con evidenza sovrapposta | Packing compatibile e assegnazioni conservate |
| S20 | Due moduli di owner diversi | Job distinti anche con la stessa evidenza |
| S21 | Due scope con sola mappa condivisa | La mappa non basta a unire scope sorgente estranei |
| S22 | Modulo blind e modulo shared dello stesso owner | Contesti distinti; il blind non riceve conclusioni condivise |
| S23 | Singola assegnazione oltre budget | Job visibile e bloccato; assegnazione non scartata |
| S24 | Costo core/reference sconosciuto con input budget | Dispatch budgeted bloccato; unknown non convertito in zero |
| S25 | Limite di job inferiore al minimo compatibile | Piano preservato con blocker; nessuna fusione cross-owner |
| S26 | Budget totale insufficiente | Nessun avanzamento dipendente; costo necessario e gap espliciti |
| S27 | Knowledge selezionata senza job assegnato | Preparazione incompleta; gate di copertura aperto |
| S28 | Knowledge disponibile solo nel catalogo dichiarato | Nessuna affermazione di installazione effettiva |
| S29 | Method binding Python e dipendenze sullo stesso ruolo reale | Identità logiche, pacchetti e consegne non intercambiabili |
| S30 | Nuovo job aggiunto dopo freeze | Rifiuto del vecchio piano o revisione esplicita con nuovi expected jobs |
| S31 | Registrazione parziale degli expected jobs | Update atomico rifiutato; nessun dispatch su ledger incompleto |
| S32 | Due job dello stesso owner, un solo report | Gate consegne fallito e run non completo |
| S33 | Report dello stesso job registrato due volte | Duplicazione rifiutata; non aumenta la copertura |
| S34 | Report con header di un altro job | Consegna non valida |
| S35 | Report con candidato precedente o composizione precedente senza reuse record | Stale o non associato, senza promozione sul piano corrente |
| S36 | Report vuoto oppure solo header | Consegna non valida |
| S37 | Report non vuoto senza esito per un'assegnazione | Accounting possibile, copertura dichiarata incompleta |
| S38 | Body sostituito dopo accettazione | Digest diverso, gate artefatti invalidato |
| S39 | Path con `..`, drive, UNC o link esterno | Lettura/scrittura rifiutata nel checker confinato |
| S40 | Path diversi che collidono sul filesystem del run | Piano rifiutato prima del dispatch |
| S41 | Worker terminato senza file | Stato da riconciliare o failed; nessun delivered automatico |
| S42 | Retry dopo fallimento con report valido | Nuovo tentativo registrato, storia precedente conservata |
| S43 | Crash dopo dispatch prima dell'update finale | Resume riconcilia il tentativo; nessun doppio dispatch cieco |
| S44 | Scope ampliato nel payload di resume | Rifiuto o nuovo run collegato secondo protocollo |
| S45 | File untracked nello scope cambia | Snapshot e gate correnti cambiano anche senza nuovo commit |
| S46 | File di output escluso cambia | Nessuna falsa invalidazione della sorgente |
| S47 | CI verde per HEAD con candidato dirty | Gate remoto non utilizzabile per il candidato dirty |
| S48 | `--no-context` contro prerequisito obbligatorio | Combinazione rifiutata; nessun floor silenziosamente rimosso |
| S49 | Verificatore o critic obbligatorio mancante | Report eventuale parziale; gate finale aperto |
| S50 | Tutti i discovery report validi ma finding non verificati | Discovery consegnata distinta da review completa |
| S51 | Helper precedente legge schema composto v2 | Rifiuto esplicito; nessuna chiusura con regole legacy |
| S52 | Run v1 concluso consultato dal nuovo helper | Lettura storica senza riscrittura o nuovi obblighi retroattivi |
| S53 | Nuovo ruolo non dichiarato nel sidecar lifecycle | Build/validazione fallita prima di produrre export incoerenti |
| S54 | Ruolo nel catalogo ma provider assente al preflight | Dispatch bloccato con recupero pertinente all'host |
| S55 | Host privo di parallelismo, isolamento disponibile | Esecuzione seriale ammessa, stessi job e stessa barriera |
| S56 | Host privo di isolamento richiesto | Blocco capability, nessuna falsa review indipendente |
| S57 | Override modello non disponibile sull'host | Binding rifiutato; alternativa solo se esplicitamente autorizzata e preparata, mai alias inventato |
| S58 | Profilo standalone senza composizione | Metodo completo selezionato; nessun core privo dei controlli necessari |
| S59 | Tutti i moduli nuovi proposti senza brief | Restano backlog; impossibile includerli nel catalogo eseguibile |
| S60 | Stage D precedente seguito da remediation | Nuovo candidato, nuova review e budget/storia preservati |
| S61 | Stesso snapshot e job identico dopo revisione aggregata | Riuso ammesso soltanto con reuse record e fingerprint identico |
| S62 | Reuse record con core, modulo, knowledge o binding diverso | Rifiuto del riuso e nuova esecuzione richiesta |
| S63 | Reuse record con snapshot diverso ma sorgente principale uguale | Rifiuto conservativo del riuso |
| S64 | Report blind precedente alla riconciliazione, input identici | Una sola esecuzione blind; riuso esplicito nel piano completo |
| S65 | Header del report storico riscritto per fingere un'origine nuova | Digest non corrispondente; artefatto rifiutato |
| S66 | Dependency read ammessa fuori conclusion paths | Lettura registrata sullo snapshot; conclusioni restano nello scope |
| S67 | Nuova conclusione o lettura fuori snapshot durante il job | Risultato dipendente bloccato fino a nuova preparazione |
| S68 | No-findings con esiti ed evidenze per tutte le assegnazioni | Consegna valida; il critic non crea una lacuna dal solo conteggio zero |
| S69 | Recovery/operability applicabili a un backend senza frontend | Owner platform selezionabile con mandato e moduli pertinenti |
| S70 | Free text del caller con intenzione raw incompatibile | Normalizzazione esplicita e rifiuto del bypass dei gate, senza parser di istruzioni dal candidato |
| S71 | Gate fallito, composizione successiva con obblighi preservati, nuovo gate passato | Chiusura ammessa sul candidato corrente, conservando il fallimento storico senza marcarlo passed |
| S72 | Nuova composizione omette un obbligo fallito senza destinazione | Supersession rifiutata e completion bloccata |
| S73 | Blind congelato e consegnato prima del piano finale | Registrazioni atomiche per entrambe le composizioni; finale usa reuse esplicito |
| S74 | Audit content senza diff e senza floor changeset | Policy content esplicita con universali, supporti, critic e all-above-floor; nessun diff inventato |
| S75 | Content dentro lifecycle con floor changeset già registrato | Unione degli obblighi e verifica più rigorosa, senza riduzione del floor |
| S76 | Preset light dopo trasferimento di controlli a specialisti | Un reviewer e protezioni qualificate; standalone completo distinto, nessun fan-out implicito |
| S77 | Prerequisito modulo con binding same_scope | Assegnazione aggiunta esattamente allo scope dichiarato |
| S78 | Prerequisito verso endpoint indisponibile o binding malformato | Gap di evidenza per endpoint previsto ma assente; errore strutturale per binding invalido |
| S79 | Upgrade driver/ORM/engine pertinente a uno specialista SQL importato | Selezione o unknown motivato; nessuna esenzione dalla qualifica per stato existing |
| S80 | Routing opzionale per job prima della decisione modello | Router usa pacchetto semantico senza binding; freeze completo avviene dopo, senza ciclo di digest |
| S81 | Output compatto di no-findings e handoff per riferimento | Tutte le assegnazioni, le prove e le lacune restano verificabili senza ripetere il report |
| S82 | Variante con meno token che perde una protezione richiesta | Qualifica rifiutata anche se il costo è inferiore |
| S83 | Risparmio nei prompt compensato da più retry, letture o verifiche | Misura del percorso completo; nessun risparmio complessivo dichiarato senza prova |
| S84 | Nuovo helper, campo o istruzione senza requisito e consumer/gate | Aggiunta respinta nella revisione del disegno; riuso o rimozione del materiale superfluo |
| S85 | Dir con un componente, più directory o un file | Stesso metodo di contenuto; cambiano solo targets e impatto ammesso, senza modalità aggiuntive |
| S86 | Richiesta doc, spec o plan | Mode doc con tipo di testo risolto; metodo nativo e nessuna review di sorgenti implicita |
| S87 | Basis materializzata incompatibile con mode | Record rifiutato; nessuna seconda opzione con cui cambiare il significato della review |
| S88 | Nuovo contesto usa subset o module come modalità | Input rifiutato; le sole proposte o registrazioni storiche possono essere riconciliate esplicitamente in dir preservando targets |

## 22. Benchmark semantico e qualifica dei profili

Le fixture strutturali precedenti non qualificano il giudizio di un modello.
Ogni modulo promosso richiede casi indipendenti: difetto, versione corretta, near miss, evidenza mancante e scope non applicabile.
Le famiglie temporali, distribuite e persistenti includono interleaving o timeline falsificabili.
I temi operativi includono backend-only e configurazioni assenti, esterne o escluse.
Accessibility distingue evidenza statica, browser e assistive technology effettivamente ammessa.

Il confronto usa stessi candidati e stessa policy di verifica fra body originale, body con moduli e profilo estratto.
Il corpus include le 20 identità/binding precedenti e il nuovo owner accessibility, senza confondere un method binding con un agente nominato.
Per gli owner non estratti si conserva il costo e il comportamento atomico finché l'equivalenza non è qualificata.
Un campione scritto interamente dal generatore non è un oracle indipendente di qualità del generatore.
I casi riservati alla qualifica rimangono separati dai casi usati per redigere il modulo.

| Misura | Dato da registrare |
|---|---|
| Selezione | Applicabili attesi, selezionati corretti, omessi, attivazioni errate e unknown |
| Retrieval/input | Evidenze richieste presenti, mancanti, stale e letture aggiuntive |
| Discovery | Difetti trovati, falsi positivi e motivazioni verificabili |
| Verifica | Finding confermati/refutati, errori del verificatore e non valutabili |
| Qualifica | Owner/profilo/modello/versione, famiglia, ampiezza e casi effettivamente valutati |
| Economia | Input/output, cache, reasoning esposto, tool output, retry, tempi e costi disponibili |
| Copertura | Inventario, lettura approfondita, prove runtime, moduli consegnati e lacune |

Le soglie si fissano prima del run e accompagnano numeratori, denominatori e variabilità osservata.
La perdita di un difetto bloccante noto resta un blocker finché classificata e risolta.
Un miglioramento su pochi casi non viene presentato come equivalenza generale.
Un modello può essere qualificato per una famiglia e ampiezza specifiche, senza promozione universale.
Nessuna percentuale di risparmio o parità di efficacia viene promessa da questa specifica.
Per R15 il confronto include anche dimensione delle istruzioni effettivamente caricate, output richiesto e duplicato, nuova logica introdotta e costo delle fasi successive.
La revisione verifica per ogni aggiunta il requisito, il consumer o gate e l'alternativa di riuso; i conteggi di codice e istruzioni sono descrittivi e non giustificano perdita di leggibilità o protezioni.
La variante economica viene ammessa soltanto dopo la qualifica pertinente a copertura e correttezza; si registrano separatamente gli eventuali miglioramenti di efficacia osservati.

## 23. Probe installati e limiti dell'enforcement

Per ogni host si registra versione, package, strategia, tool effettivo e percorso esercitato.
Il probe minimo avvia due job dello stesso ruolo con moduli distinti e un support execution pertinente.
Controlla input ricevuti, riferimenti del package, report univoci, barriera e risultato sul candidato identificato.
Un probe negativo omette o corrompe un report e dimostra che la chiusura è rifiutata.
Un altro esercita ripresa di un tentativo interrotto senza consegna completa.

CLI su record sintetici prova parsing, packaging e accounting.
Un subagent realmente eseguito prova il percorso esercitato su quella versione dell'host.
Una review con oracle indipendente aggiunge evidenza sulla qualità dei risultati, nel perimetro del corpus.
Nessuna di queste prove dimostra da sola confinamento generale dei tool o impossibilità di spendere fuori protocollo.
Questi obblighi restano di prompt finché un meccanismo runtime specifico è stato misurato.

Il report di verifica mantiene quattro sezioni di evidenza separate: strutturale, semantica, host installato e enforcement runtime.
Una sezione non esercitata riporta unavailable con requisito concreto per ottenerla.
L'assenza di accesso a un host non viene trasformata in un pass attraverso i soli export generati.
I gate obbligatori indisponibili mantengono aperta la consegna che li richiede.

## 24. Rollout finito e criteri di uscita

| Fase | Consegna finita | Criterio di uscita |
|---|---|---|
| R0 | Baseline locale e allegati riconciliati | Stato reale distinto dalla patch; nessuna modifica preesistente persa |
| R1 | Contratti, versioni, reader e fixture del protocollo | Un job mancante impedisce la chiusura e un reader vecchio rifiuta il run composto |
| R2 | Composer integrato e preparazione/knowledge/binding | Quattro mode, floor e budget passano i casi deterministici pertinenti |
| R3 | Profili e migrazione degli obblighi di tutte le 20 identità precedenti | Ogni obbligo ha destinazione e standalone completo; nessuna lente scompare |
| R4 | Nuovo owner accessibility, sua base e 48 specializzazioni nuove approvate | Ruolo e ogni modulo approvato promossi con trigger, limiti e casi qualificati; una voce ancora planned mantiene aperta la fase |
| R5 | Entry review e tutte le entry lifecycle aggiornate | Resume/verify/finish e support executions condividono gli stessi gate |
| R6 | Cinque export e controlli del repository | Build riproducibile, lint e contratti cross-host senza nuove baseline di debito |
| R7 | Benchmark semantico e profili economici candidati | Qualifica osservata nel perimetro dichiarato, costi completi e limiti visibili |
| R8 | Probe installati richiesti e consegna finale | Evidenze distinte, nessun gate obbligatorio mancante, documentazione coerente |

R3 non è conclusa dopo avere estratto soltanto un owner pilota.
R4 comprende i moduli nuovi proposti nella specifica principale, con uno stato esplicito per ogni voce.
Prima della chiusura, l'insieme dei moduli promossi deve coincidere con l'insieme approvato, salvo modifica esplicita dello scope.
La mappa dei 50 temi, gli otto specialisti SQL/AMQP della patch e le estensioni AI vengono conservati.
Il catalogo atteso deriva dal merge delle definizioni approvate, senza sostituire tutte le basi con il sottoinsieme del backlog.
Una fase pilota può qualificare il processo, ma non chiude l'intero intervento.

Le fasi non avviano una manutenzione infinita del catalogo.
Ogni eccezione o prerequisito indisponibile ha owner, artefatto, effetto sul completamento e prossima prova concreta.
Un eventuale rinvio di una parte approvata cambia esplicitamente lo scope della consegna; non viene nascosto come fase successiva facoltativa.
Versionamento, rigenerazione e pubblicazione seguono le autorizzazioni del task di implementazione, separato da questa consegna documentale.

## 25. Mappa dei file canonici interessati

| Area | File o directory canonici | Conseguenza richiesta |
|---|---|---|
| Contratto del run | `plugins/project-protocol/contracts/work.toml` | Schema composto, composizioni, expected jobs e gate obbligatori |
| Risultato del run | `plugins/project-protocol/contracts/project-result.toml` | Revisione, candidato, composizioni e completezza coerenti |
| Runtime del protocollo | `plugins/project-protocol/skills/project-protocol/scripts/run_state.py` | Validazione, transizioni, resume, migrazione e rifiuto di chiusura incompleta |
| Metodo del protocollo | `plugins/project-protocol/skills/project-protocol/SKILL.md` | Contratti e limiti reali del nuovo percorso |
| Pavimento | `plugins/project-protocol/skills/project-protocol/scripts/review_roster.py` | Provenienza del floor e compatibilità dei suoi consumer |
| Preparazione | `plugins/senior-review/skills/review-preparation/SKILL.md` | Ordine P1-P9 e output composti |
| Grounding | `plugins/senior-review/skills/review-preparation/references/candidate-grounding.md` | Basis, snapshot, policy e floor |
| Knowledge | `plugins/senior-review/skills/review-preparation/references/knowledge-bindings.md` | Assegnazioni ai job e fingerprint condivisi |
| Stack | `plugins/senior-review/skills/review-preparation/references/stack-dimensions.md` | Attivazioni coerenti e nessun secondo spawn dalle tabelle |
| Composer | `plugins/senior-review/skills/review-preparation/scripts/review_composer.py` | Nuovo helper canonico riconciliato con contratti integrati |
| Catalogo | `plugins/senior-review/skills/review-preparation/references/` | Moduli, composizione, vocabolario e riferimenti promossi |
| Metodi review | `plugins/senior-review/skills/review-method/SKILL.md` e `references/` | Dispatch dei job e percorsi legacy completi |
| Verifica | `plugins/senior-review/skills/review-quality-gates/SKILL.md` e `references/` | Basis content, verificatori, critic e gate distinti |
| Consolidamento | `plugins/senior-review/skills/review-consolidation/SKILL.md` e `references/` | Unico writer e risultato parziale/completo verificabile |
| Contratti review | `plugins/senior-review/contracts/` | Job, assegnazioni, basis, artefatti, usage e copertura |
| Owner | `plugins/senior-review/roles/` e owner provider pertinenti | Shell, moduli, standalone e nuovo accessibility |
| Lifecycle | `plugins/project-lifecycle/skills/lifecycle-method/references/verify.md` | Stage D composto e gate sul candidato corrente |
| Ripresa/chiusura | `plugins/project-lifecycle/skills/lifecycle-method/references/continue.md`, `finish.md`, `waves.md` | Invalidation, remediation e chiusura coerenti |
| Entry | `plugins/daodan/workflows/*.md` e sidecar pertinenti | Input composti, ruoli consentiti e contratti condivisi |
| Catalog compiler | `scripts/daodan/reviewer_catalog.py` | Profili/ruoli realmente registrati, provenance e binding per host |
| Validazione compiler | `scripts/daodan/validate.py` | Chiusura fra catalogo, provider, moduli e dispatch dichiarato |
| Rendering | `scripts/daodan/render.py` e adapter quando necessario | Bundling dei body e riferimenti operativi senza nuove primitive |
| Regressioni | `tests/test_review_*.py`, test protocollo e adapter pertinenti | Casi positivi/negativi e compatibilità legacy |
| Qualifica | `evals/senior-review/` e `tests/host-probes/` | Corpus, misure e prove installate separate |
| Documentazione | `docs/plugins/senior-review.md`, `docs/hosts.md` e guide owner pertinenti | Capacità effettive, limiti e recovery aggiornati |

La lista dei sidecar comprende `review-branch`, `new-feature`, `fix-bug`, `refactor-code`, `continue-task`, `finish-task`, `run-maintenance` e `investigate-problem`.
`review-changes` viene verificato per preservare light, senza ampliare automaticamente il suo dispatch.
I manifest di plugin cambiano solo quando cambiano componenti, dipendenze o versione del kernel pertinente.
Tutto sotto `exports/` e i marketplace root viene rigenerato; nessuna correzione manuale entra nella fonte.
Le istruzioni native Codex vengono sincronizzate solo se cambiano le rispettive fonti canoniche.

## 26. Compatibilità futura con il work graph

Il piano composto espone job, prerequisiti e riferimenti agli artefatti in forma deterministica.
La sua struttura è descrittiva per l'harness attuale e non assume l'executor del work graph.
Un futuro adapter verso quel grafo deve preservare identità, input digest, expected jobs, barriere, policy e report owner.
Le interfacce I3/I4 del disegno work graph restano distinte da selezione deterministica dei moduli e binding esecutivi del presente sistema.
Il loro rollout e le relative promozioni non sono implicati dalla riuscita del composer.

Il registro del futuro executor, se adottato, dovrà continuare a usare una sola fonte delle transizioni del run.
Non si introducono qui lease, reservation o budget paralleli che competano con quella futura fonte.
Le consegne conservano abbastanza provenienza per essere importate come artefatti, non come stati succeeded presunti.
Un benchmark del modello di selezione non prova readiness del controller o dispatch di un host.
Questa compatibilità resta un requisito d'interfaccia; non è un deliverable di implementazione del futuro executor.

## 27. Condizione finale di completezza

La consegna implementativa è completa quando le 20 identità precedenti e accessibility hanno percorsi coerenti, i moduli approvati risolvono e full/changeset/dir/doc conservano scope, floor e unknown secondo il proprio metodo.
Tutti gli expected jobs, support executions e gate obbligatori devono essere registrati e verificati sul candidato effettivo.
Continue, verify e finish devono rifiutare risultato stale, mancante o parziale attraverso lo stesso contratto.
I cinque host devono riprodurre i package corretti e riportare separatamente le prove installate realmente ottenute.
Costo e qualità vengono descritti soltanto nel perimetro misurato, con limiti e dati non disponibili.

La presenza di tutti i file, una build verde o un turno terminato non sostituisce questi criteri.
Un'analisi di accounting completa non equivale a copertura semantica completa.
Un risultato dichiarato completo deve permettere a un lettore di risalire da verdetto a verifica, report, job, modulo, pacchetto e candidato senza deduzioni implicite.
