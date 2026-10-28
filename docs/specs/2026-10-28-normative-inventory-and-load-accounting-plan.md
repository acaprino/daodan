# Piano: inventario normativo e contabilità statica del carico

Data: 2026-10-28. Stato: **piano proposto, esecuzione non autorizzata**.

## 1. Approvazione, ambito e consegna

Requisito approvato: [specifica](2026-10-28-normative-inventory-and-load-accounting-design.md), SHA-256 `a78883a98a1697ac8021c6a30e48f3196d0ebe9cf0fc41ec60fa5bdf7d81dcfd`.

La fonte dell'approvazione è questa conversazione: risposta del committente **«approvo»** alla presentazione della specifica e alle due scelte del §8. La risposta successiva **«autorizzo la pianificazione»** autorizza questo piano. Sono quindi acquisiti sia il perimetro esteso a istruzioni di repository, adapter e check richiamati, sia autore e revisore distinti con accettazione finale dell'inventario da parte del committente.

La specifica rimane byte-identica alla versione approvata: il suo stato storico non viene riscritto. Questo documento conserva il legame all'approvazione. Quando sarà autorizzata l'esecuzione, quel legame e le risposte originali entreranno nel registro del run, senza inventare approvazioni di artefatti ancora inesistenti.

**Consegna della pianificazione:** questo solo file. Nessun codice, indice normativo, manifest di carico, render dorato, fixture, registro operativo o baseline viene creato adesso. Nessun commit, push o bump. Anche `daodan_build.py --check` è rinviato: il comando produce render temporanei, pur non pubblicandoli.

Il piano realizza in futuro i due prodotti approvati: inventario shadow e contabilità statica report-only. Si ferma al primo rapporto reale e all'accettazione del relativo perimetro. Fixture frozen per eval, pilot lazy, parafrasi, ratchet, conversione a ondate e sostituzione della convenzione sulle 700 righe restano fuori da questo piano. I normali test unitari sintetici degli strumenti sono distinti dalle future fixture frozen del programma.

## 2. Stato verificato e punti di riuso

HEAD osservato per la pianificazione: `552daa15dafd9ec5673678d2ba3f783a862bc571`. La specifica approvata è presente, ancora non tracciata. Restano estranei al lavoro `docs/gutsay/julia-adapter-retest-2026-10-27.md` ed `evals/julia-adapter-retest/`. Lo stato va ricontrollato prima dell'esecuzione; questi dati non attestano una futura baseline verde.

La directory `.codebase-map/` non esiste nel checkout osservato. Applicato il percorso di consumo in lettura di `plugins/codebase-map/skills/map-method/references/standalone.md:27-34`: letture mirate dei sorgenti, senza creare o aggiornare una mappa. Nessun censimento globale è stato ripetuto. Il numero di direttive e il costo dell'audit restano ignoti.

### 2.1 Compilazione e input

| Evidenza letta | Decisione del piano |
|---|---|
| `scripts/daodan/load.py:61`, `179-216` | Il sidecar workflow accetta un insieme chiuso di campi. I manifest TOML di analisi saranno separati dai sidecar runtime: nessuna aggiunta di `[load]` al kernel in questa fase. |
| `scripts/daodan_build.py:225-253`, `415-428` | Riutilizzare il controllo completo esistente e catturare gli export già verificati, compresi cataloghi fuori da `exports/` e package files. Non duplicare l'orchestrazione del renderer. |
| `scripts/daodan/validate.py:75-133` | Riutilizzare `confined_source()` e `source_members()` per letture confinate ed enumerazione deterministica. Il controllo non garantisce protezione da mutazioni ostili concorrenti; la cattura aggiunge verifiche dei digest prima/dopo. |
| `scripts/daodan/model.py:51-57`; `scripts/lint_dependency_graph.py:184-192`, `210-218`, `267-321` | Le identità strutturate sono riutilizzabili. `[dispatch]` non è una sequenza eseguita; gli edge euristici restano candidati incompleti, separati da eventi e manifest auditati. |
| `scripts/daodan/provenance.py:22-42`; `scripts/daodan/report.py:18-28` | Provenienza e `BuildReport` mantengono i loro contratti. Il rapporto di carico usa tipi separati e non viene inserito fra i fallimenti della build. |

### 2.2 Test, audit e protocollo

| Evidenza letta | Conseguenza |
|---|---|
| `tests/test_daodan_render.py:214-217`, `287-347`; `tests/test_daodan_host_rendering.py:61-91` | Le convenzioni dei test aiutano a verificare riproducibilità e percorsi dei cinque host. Non sono render dorati congelati né prove di consumo runtime. |
| `tests/host_binding_assertions.py:26-59` | L'helper di parità rimuove binding dalle reference concatenate. Non va usato come payload della contabilità; il nuovo test conserva entrambi i binding di wrapper e reference. |
| `scripts/lint_fact_anchors.py:277-320` | Non riutilizzare la sua selezione/normalizzazione come inventario normativo: filtra fonti e normalizza valori. Lo shadow index conserva byte originali, errori e lacune. |
| `plugins/work-controller/skills/work-record/scripts/run_state.py:324-357`, `421-475` | Le task hanno write set, oracle, verification e dipendenze; il limite normale è quattro file, sei con eccezione motivata. Un'onda non contiene task con file, lock o dipendenze incrociati. |
| `plugins/project-delivery/skills/delivery-method/references/waves.md:5-24` | Piano legato alla specifica, oracoli espliciti, review avversaria prima dell'esecuzione. La pianificazione non autorizza l'esecuzione. |

Le citazioni documentano comportamento letto nel codice. I comandi dei task successivi sono **interfacce e test proposti**, non strumenti già disponibili o risultati già verificati.

## 3. Organizzazione scelta

### 3.1 Codice e dati

Il codice nuovo risiede in `scripts/instruction_load/`, con un entry point `scripts/normative_load.py`. È tooling di repository, non un nuovo plugin, un motore di workflow o una dipendenza del compilatore. Usa la standard library e i lettori del compilatore già compatibili con i requisiti. Nessun cambiamento richiesto a kernel, adapter, linter, cataloghi, export, `CLAUDE.md`, `AGENTS.md` o CI.

I moduli sono definiti dai task, senza un'infrastruttura di plugin o registry aggiuntiva. I test usano `unittest` e convenzioni locali. La guida del tool è `docs/instruction-load-accounting.md`, distinta dalla normativa dei plugin.

Nel seguito **R** indica `.daodan/runs/<execution-id>/instruction-load/`, nella home del checkout principale. Non viene assegnato o creato un run durante questa pianificazione. I nomi `R/...` sono binding di output da risolvere prima dell'esecuzione, non path immediatamente eseguibili.

I dati dell'audit restano nel run proprietario. Per continuare da un altro run si importa esplicitamente lo snapshot precedente con hash, ID e attestazioni; non si rigenerano gli ID. Un handoff conserva quegli artefatti e la loro origine. Non si effettua purge o promozione automatica dell'indice a fonte autorevole. La successiva eventuale distribuzione di fixture versionate richiede il suo ambito futuro.

### 3.2 Render dorati

La cattura futura produce cinque archivi ZIP deterministici, uno per host, e un `index.json`. Comprende i byte dei pacchetti e i cataloghi indicati dall'adapter, anche fuori da `exports/`, come `package.json` di Pi; comprende anche i file di package come il loader OpenCode. Non ricostruisce a mano i payload.

Il sottocomando esplicito `capture-golden` richiama il controllo `build_repository(..., check=True)` già esistente, sui cinque host. Lega il risultato ai digest degli input e degli export prima e dopo controllo e cattura. Una mutazione, drift o validazione fallita impedisce di pubblicare un indice completo; non si correggono implicitamente gli export. Se serve una loro correzione, è un blocco da risolvere fuori dai task di questa cattura.

Gli archivi hanno ordine e metadata fissi, conservano i byte esatti e vengono letti direttamente con `zipfile`, senza estrazione. Il lettore verifica nomi univoci, percorsi relativi confinati, dimensioni, digest e limiti dichiarati; non accetta un archivio manipolato come input affidabile. I timestamp dei receipt operativi non entrano nei byte canonici del rapporto di carico.

Il sottocomando `report` non richiama il compilatore né la cattura. Legge snapshot disponibili e dichiara come ignote le proiezioni non dimostrate. La completezza dello snapshot renderizzato è separata dalla copertura normativa e dal consumo runtime.

### 3.3 Inventario e manifest

Lo scope dell'inventario fissa esplicitamente le fonti canoniche, istruzioni di repository, testi adapter, check richiamati e occorrenze generate. Un archivio separato conserva i byte delle fonti auditate. Sono dichiarati esclusioni, riferimenti esterni e input non disponibili. Nessuna scansione di cartelle personali, configurazioni con segreti o cache installate è implicita.

I digest del render e quelli dell'inventario hanno perimetri distinti: le fonti che alimentano il render devono coincidere con quelle della cattura; eventuali fonti di audit non distribuite hanno il proprio hash e non fingono un'occorrenza renderizzata. HEAD da solo non identifica i byte del candidato.

I manifest di carico saranno TOML versionati sotto `R/manifests/`, legati a workflow, host, fasi, contesti, snapshot e inventario. Le condizioni usano operatori chiusi su dati, mai `eval` o shell. Non contengono nuovi prompt né eseguono scheduling. La loro scrittura registra il comportamento letto: non autorizza a cambiare quando i metodi caricano una reference.

L'estrattore esistente può contribuire candidati solo quando il suo repository sorgente coincide con quello fissato e i digest dei file letti sono verificati. Non è un API generico per snapshot arbitrari: se tale binding manca, si usa la lettura strutturata dei sidecar disponibili e si registra la lacuna euristica. Nessuna sostituzione globale del suo root, fusione automatica degli ID o deduzione delle fasi da `[dispatch]`.

## 4. Regole di esecuzione futura

I task hanno cinque obblighi comuni, da applicare quando l'esecuzione sarà autorizzata:

1. **Binding:** ricontrollare specifica, piano, fonti e grants; assegnare run e file esatti. Usare il ramo singolo esistente e task sequenziali, preservando lavoro estraneo. Nessuna nuova branch o worktree è necessaria per questo piano.
2. **Test prima del comportamento:** il test writer prepara l'oracolo dal requisito; il Python specialist implementa. I test sono sintetici, con valori attesi indipendenti. `ImportError`, test non scoperti o setup fallito non sono il red semantico richiesto. Osservare il fallimento pertinente prima della soluzione; se l'oracolo non discrimina il requisito, correggerlo prima di proseguire.
3. **Una task per micro-onda:** ogni task fissa `write_set`, `oracle`, `verification`, `resource_locks`, `produces`, `consumes`, EX e INV. Le ricette dei dati vengono materializzate in task concrete, controllate con il protocollo e revisionate prima del dispatch. Nessuna wildcard resta in un write set.
4. **Verifica e review:** eseguire i controlli pertinenti sul candidato e review indipendente di task e onda. I test regolano la correttezza dello strumento; carico alto o ignoto resta diagnosi non bloccante. Le ondate lasciano la build verde senza allentare gate o baseline esistenti.
5. **Autorizzazioni separate:** niente commit, push, bump, pubblicazione, rimozione di fonti o modifica dei prompt impliciti. Senza grant di commit le task possono essere verificate ma le ondate non sono dichiarate `sealed`; non si dichiara completo un protocollo che richiede consegne mancanti. Un errore conserva byte pre-fase e lavoro estraneo; nessun reset generico.

La baseline futura usa i controlli del §8. Se è rossa, distinguere guasto preesistente, ambiente e regressione del candidato. Non modificare codice estraneo per rendere verde il preflight e non iniziare la task dipendente da una baseline sconosciuta.

## 5. Registro dei task

Questo registro è il formato canonico del piano. Ogni riga Txx diventa una singola onda Wxx, sequenziale, inizialmente `pending`. `resource_locks` contiene `instruction-load:serial`; `produces` contiene `task:Txx`; la colonna Dipendenze elenca i `consumes`, con prefisso `task:` per Txx. Le dipendenze esterne sono definite sotto. Le righe dati I/M diventano altre onde singole nel punto indicato.

La colonna Test nomina il file futuro di verifica. Per una riga di codice, `oracle.command` e `verification.command` sono entrambi `python -m unittest discover -s tests -p <Test> -v`; il fallimento atteso è nella riga. Il comando viene usato dopo l'autoria del test e prima/dopo il comportamento interessato. Nei task di dati sono indicati i comandi del futuro CLI. Tutti i nuovi path sono **da creare**, tranne i file introdotti da task precedenti, che vengono aggiornati.

Ogni EX-nn richiama anche INV-nn della specifica approvata. Le dipendenze impediscono di scambiare il completamento di un tool con il completamento dell'audit reale.

### 5.1 Blocco A: cattura dei render

| ID | Write set | Test / verifica | Fallimento atteso e risultato richiesto | EX | Dipendenze |
|---|---|---|---|---|---|
| T01 | `scripts/instruction_load/__init__.py`; `scripts/instruction_load/render_snapshot.py`; `scripts/normative_load.py`; `tests/test_instruction_load_snapshot.py` | `test_instruction_load_snapshot.py` | Rifiutare drift, source mutato, archivio corrotto, duplicati e traversal; conservare byte, catalogo Pi e loader OpenCode. Due catture degli stessi input sono identiche. Sentinelle dimostrano che input/export non sono modificati. | EX-11, EX-12, EX-14 | execution-grant |
| T02 | `R/golden/claude.zip`; `R/golden/copilot.zip`; `R/golden/codex.zip`; `R/golden/pi.zip`; `R/golden/opencode.zip`; `R/golden/index.json` | `python scripts/normative_load.py verify-golden R/golden/index.json` | Prima manca uno snapshot completo verificato. Dopo `capture-golden --repo . --out R/golden`, il verificatore legge tutti i membri, prova hash e copertura dei cinque host e conferma il controllo del compilatore sul medesimo input. | EX-11, EX-12, EX-14 | T01, baseline-green |

T02 usa `granularity_exception.reason`: «Cinque archivi host e un unico indice costituiscono uno snapshot atomico; un indice parziale non può attestare la baseline dei cinque host». Sei output, entro il limite eccezionale esistente; nessuna modifica al protocollo. I temporanei della cattura appartengono al run e sono dichiarati come scratch operativo, non come sorgenti modificabili. Non si sovrascrive una cattura accettata: una ripetizione riceve una nuova identità.

### 5.2 Blocco B: strumenti dell'inventario

| ID | Write set | Test / verifica | Fallimento atteso e risultato richiesto | EX | Dipendenze |
|---|---|---|---|---|---|
| T03 | `scripts/instruction_load/records.py`; `tests/test_instruction_load_records.py` | `test_instruction_load_records.py` | Rifiutare ID duplicati, riferimenti inesistenti, campi sconosciuti e numeri non finiti; conservare direttive, check, eccezioni, stop condition e irrisolti. Serializzazione canonica senza ID casuali rigenerati. | EX-03, EX-05, EX-14 | T02 |
| T04 | `scripts/instruction_load/sources.py`; `tests/test_instruction_load_sources.py` | `test_instruction_load_sources.py` | Verificare byte UTF-8, offset, righe, CRLF/LF, span discontinui e hash contestuali. Rilocazione con ID invariato; condizione esterna cambiata invalida l'audit. Rifiutare boundary UTF-8 errati e fonti mutate. | EX-01, EX-02, EX-05 | T03 |
| T05 | `scripts/instruction_load/audit.py`; `tests/test_instruction_load_audit.py` | `test_instruction_load_audit.py` | Blocchi omessi, esclusioni immotivate, autore e revisore coincidenti, approvazioni obsolete o consegne irrisolte non producono audit completo. Invalidazione selettiva, storia conservata, stessa frase con contesto diverso non fusa. | EX-02, EX-03, EX-05, EX-08 | T04 |
| T06 | `scripts/instruction_load/inventory.py`; `scripts/normative_load.py`; `tests/test_instruction_load_inventory.py`; `docs/instruction-load-accounting.md` | `test_instruction_load_inventory.py` | Preparare scope e pacchetti di lettura senza auto-classificazione autorevole. Validare/importare gli shard; una fonte non classificata resta lacuna, non sparisce. Un documento senza MUST può contenere normativa. Nessuna scrittura nei sorgenti. | EX-01, EX-03, EX-08, EX-14 | T05 |

La documentazione di T06 descrive soltanto interfacce effettivamente implementate in quel punto. Lo strumento verifica struttura, byte e ricevute, non la correttezza semantica delle esclusioni. Le attestazioni conservano evidenza e identità del revisore; un agente non firma l'accettazione del committente.

### 5.3 Blocco C: inventario reale

| ID | Write set | Test / verifica | Fallimento atteso e risultato richiesto | EX | Dipendenze |
|---|---|---|---|---|---|
| T07 | `R/inventory/scope.json`; `R/inventory/sources.zip`; `R/inventory/partitions.json`; `R/inventory/index.json` | `python scripts/normative_load.py verify-scope R/inventory/scope.json` | Prima manca un perimetro fissato. Dopo `prepare-inventory --golden R/golden/index.json --repo . --out R/inventory`, ogni fonte inclusa ha byte/hash, owner, motivo e assegnazione; gli esterni non disponibili restano gap. | EX-03, EX-08, EX-12 | T06 |
| T08 | `R/inventory/aggregate.json`; `R/inventory/source-audit.json`; `R/inventory/coverage.json` | `python scripts/normative_load.py verify-inventory R/inventory/aggregate.json --require integrity` | Uno shard atteso assente senza diagnosi viola l'integrità dell'aggregato. Un riferimento indisponibile esplicitamente registrato, con attestazioni valide, produce exit 0 e audit incompleto. Aggregare tutti i lotti senza perdere esclusioni, conflitti e irrisolti; la completezza semantica e il mapping delle emissioni restano stati separati. | EX-01, EX-02, EX-03, EX-05, EX-08 | T07, inventory-lots-reviewed |

Fra T07 e T08 si istanziano le ricette **I-A-n** e **I-R-n**:

1. **I-A-n, autore:** legge tutte le fonti esatte del lotto e il contesto dichiarato; scrive soltanto `R/inventory/shards/<id>.json`. Classifica tutti i blocchi, propone ID/predicati/applicabilità/precedenza, conserva dubbi e collegamenti tra fonti. Oracle: `verify-shard <file> --scope R/inventory/scope.json`, inizialmente shard assente o copertura incompleta; verifica finale del medesimo comando più lettura indipendente.
2. **I-R-n, revisore distinto:** legge le fonti originali, anche parti escluse e non normative, poi lo shard; scrive soltanto `R/inventory/reviews/<id>.json`. Oracle: `verify-audit <file> --shard <shard>`, inizialmente attestazione mancante; verifica finale dei binding e degli esiti. Un controllo strutturale non sostituisce la seconda lettura.
3. **Riconciliazione:** un rilievo torna all'autore del lotto. Le revisioni mantengono la storia e invalidano solo le attestazioni coinvolte; il nuovo nome di output e il write set vengono fissati prima del lavoro. Nessuna correzione della fonte normativa è autorizzata da questo giro.

Le ricette producono rispettivamente `inventory-shard:<id>` e `inventory-review:<id>`; il consumo delle review richiede lo shard esatto. Mantengono il lock seriale, EX-01..EX-05 e EX-08. `inventory-lots-reviewed` si risolve solo dall'elenco completo di `partitions.json`, non dall'assenza di errori dei lotti già arrivati. La materializzazione dei lotti avviene dopo il congelamento delle fonti, senza un nuovo censimento preliminare adesso.

Il primo lotto misura separatamente tempo di estrazione, seconda lettura e correzioni. Non è il pilot di riscrittura del programma. Il committente può accettare l'audit di fonti e semantica su un perimetro nominato; **l'audit completo delle consegne resta pendente** fino al Blocco E. Un perimetro parziale non viene ribattezzato audit completo del repository.

### 5.4 Blocco D: calcolo del carico

| ID | Write set | Test / verifica | Fallimento atteso e risultato richiesto | EX | Dipendenze |
|---|---|---|---|---|---|
| T09 | `scripts/instruction_load/load_manifest.py`; `scripts/instruction_load/edges.py`; `tests/test_instruction_load_manifest.py`; `tests/test_instruction_load_edges.py` | `test_instruction_load_manifest.py` e `test_instruction_load_edges.py`, eseguiti separatamente | Manifest assente e campo ignoto non equivalgono a zero eventi. Conservare provenienza candidate/declared/audited, binding dei digest e operatori chiusi; distinguere dipendenza, worker ammesso ed emissione. Edge interno o path irrisolto produce gap. | EX-04, EX-08, EX-09, EX-12 | T08 |
| T10 | `scripts/instruction_load/payloads.py`; `tests/test_instruction_load_payloads.py` | `test_instruction_load_payloads.py` | Conteggio degli span UTF-8 attestati, senza stripping implicito dei binding. Wrapper più reference conserva entrambi i contributi. Trasformazioni runtime non fissate restano ignote; pacchetto disponibile non significa payload emesso. | EX-06, EX-11, EX-12, EX-14 | T09 |
| T11 | `scripts/instruction_load/scenarios.py`; `tests/test_instruction_load_scenarios.py` | `test_instruction_load_scenarios.py` | Base 100 e alternative esclusive 40/70 producono 140/170, mai 210. Preservare correlazioni; distinguere cicli limitati, ignoti e senza limite. Espansione terminante con `analysis_limit` esplicito. | EX-07, EX-08, EX-09, EX-13 | T10 |
| T12 | `scripts/instruction_load/accounting.py`; `tests/test_instruction_load_accounting.py` | `test_instruction_load_accounting.py` | Due emissioni da 100 producono 200 cumulativi/residenti e 100 unici; worker isolati restano separati. Fine fase non elimina byte; reset, eredità e return sono eventi attestati. Picchi distinti conservano i propri testimoni. | EX-06, EX-07, EX-08, EX-10 | T11 |
| T13 | `scripts/instruction_load/accounting.py`; `tests/test_instruction_load_constraints.py` | `test_instruction_load_constraints.py` | Un predicato ripetuto sul medesimo risultato conta una volta; domini indipendenti contano separatamente. Load tardivo non sottrae obblighi dovuti; eccezioni modificatrici e normativa senza oracolo restano rappresentate. | EX-03, EX-04, EX-06, EX-08 | T12 |

Il Blocco D non afferma che T08 abbia già concluso l'audit delle consegne. Il conteggio usa stati e quote irrisolte anche su inventari validi ma parziali. L'analisi dei cicli appartiene agli eventi, non al solo grafo delle fasi. Gli output dei tool e degli agenti non vengono prodotti per riempire lacune della contabilità statica.

Oracolo trasversale assegnato ai test CLI di T06 e T14: una fonte esterna indisponibile è registrata come lacuna e revisionata senza inventarne il contenuto; `verify-inventory --require integrity` restituisce 0, l'audit rimane incompleto e `report` produce exit 0 con il contributo `unknown`. La richiesta separata `verify-inventory --require complete-audit` restituisce 1. T08 consuma soltanto il primo criterio: né T09 né T15 aspettano la completezza semantica o l'accettazione finale del committente.

### 5.5 Blocco E: rapporto reale e accettazione

| ID | Write set | Test / verifica | Fallimento atteso e risultato richiesto | EX | Dipendenze |
|---|---|---|---|---|---|
| T14 | `scripts/instruction_load/report.py`; `scripts/normative_load.py`; `tests/test_instruction_load_cli.py`; `docs/instruction-load-accounting.md` | `test_instruction_load_cli.py` | Tutti i workflow selezionati e cinque host sono presenti, anche senza manifest. Stessi input producono JSON identico; ignoti non diventano zero. Carico alto non causa un errore di build. Confronti non omogenei non dichiarano risparmio. Test di composizione end-to-end legano snapshot, inventario, manifest, proiezioni e quantità. | EX-01..EX-14 | T13 |
| T15 | `R/report.json`; `R/report.md`; `R/delivery-coverage.json`; `R/inventory/final-audit.json` | `python scripts/normative_load.py verify-report R/report.json --inventory R/inventory/aggregate.json --golden R/golden/index.json` | Prima manca una riconciliazione completa delle righe e delle consegne. Dopo `report --inventory R/inventory/aggregate.json --golden R/golden/index.json --manifests R/manifests --out R/report.json`, ogni risultato cita input, fase, contesto e stato. La vista Markdown deriva dal JSON. Audit finale espone consegne mancanti, approvazione pendente e limiti, senza un no-loss anticipato. | EX-01..EX-14 | T14, load-manifests-reviewed |
| T16 | `R/verification.json`; `R/acceptance.md`; `docs/instruction-load-accounting.md` | Controlli del §8, poi `python scripts/normative_load.py verify-deliverables R` | Prima mancano ricevute sul candidato finale e accettazione dell'inventario. Dopo review e controlli, il dossier distingue tool verificati, perimetri auditati, diagnosi residue e prove runtime assenti. L'accettazione del committente è legata agli artefatti esatti. | EX-01..EX-14 | T15, inventory-acceptance |

Fra T14 e T15 si istanziano **M-A-n** e **M-R-n**, sullo stesso principio dei lotti dell'inventario:

1. **M-A-n:** scrive un manifest esatto `R/manifests/<workflow-id>/<profile-id>.toml`, dopo lettura della catena e dei render. Dichiara fasi, condizioni, cardinalità, contesti, durata e mapping normativo con evidenze; ciò che non può stabilire resta ignoto. Oracle/verifica: `verify-manifest <file> --inventory R/inventory/aggregate.json --golden R/golden/index.json`, inizialmente manifest assente o non legato agli input.
2. **M-R-n:** un revisore distinto legge fonti e manifest; scrive soltanto `R/manifest-reviews/<id>.json`. Oracle/verifica: `verify-manifest-audit <file> --manifest <manifest>`, inizialmente attestazione assente. Verifica soprattutto applicabilità prima del load, residenza, ripetizioni e alternative correlate.
3. **Riconciliazione:** un elenco di profili attesi deriva dallo scope fissato, con tutte le cinque righe host per workflow. Il completamento dei lotti è confrontato con quell'elenco. Un manifest intenzionalmente irrisolto è una consegna con gap, non evidenza di zero carico. Le rettifiche mantengono storia e nuova review.

Le ricette producono `load-manifest:<id>` e `load-manifest-review:<id>`, conservano il lock seriale e EX-04, EX-06..EX-14. `load-manifests-reviewed` non attesta che le incognite runtime siano risolte. La lista esatta dei profili e dei path viene materializzata nel run e verificata prima del dispatch. L'assenza di un profilo rilevata dopo l'audit riapre quella copertura.

## 6. Interfacce e politica degli esiti

I nomi CLI nel registro sono il contratto da implementare, non comandi da eseguire ora. I sottocomandi di verifica scrivono solo su stdout/stderr; quelli di preparazione/cattura/report richiedono un output esplicito nel run e non sovrascrivono input o snapshot accettati. I controlli dei path precedono le letture/scritture; timestamp e path macchina restano nei receipt operativi, fuori dalle quantità canoniche.

Gli stati del rapporto rimangono quelli della specifica: `exact`, `bounded`, `symbolic`, `unknown`, `unbounded`. La serializzazione dei numeri non ammette NaN o Infinity; un limite assente è `null` accompagnato dallo stato e dalla causa. Niente stima lessicale nei campi esatti. Il formato conserva separatamente quantità note e residui sconosciuti, inclusi i casi nei quali non è lecito dedurre neppure un lower bound del payload dopo l'installazione.

Il CLI distingue tre esiti:

| Esito | Comportamento previsto |
|---|---|
| Rapporto valido con diagnosi | Exit 0, anche per carico alto, ignoto, cicli senza limite o gap dichiarati. Il report non è un gate. |
| Criterio richiesto di integrità/copertura non soddisfatto | Exit 1 nei soli comandi `verify-*`: per esempio archivio incoerente o audit richiesto ma mancante. Non è un limite di carico e non viene aggiunto a CI come gate. |
| Invocazione/input non interpretabile o impossibilità di produrre l'artefatto | Exit 2 con diagnosi distinta; non produce un finto rapporto completo. Un manifest assente o stale ma identificabile resta invece un gap del rapporto. |

I comandi `verify-*` servono a verificare gli artefatti prodotti e i criteri della specifica, non a far fallire una build per densità o carico. Tutti i loro test futuri sono test di correttezza del nuovo strumento. Nessun nuovo job o soglia entra nella CI.

Per `verify-inventory`, `--require integrity` verifica schema, ID, digest disponibili, ancoraggi verificabili, binding delle attestazioni e contabilizzazione di tutte le partizioni, comprese le lacune dichiarate. Non richiede che le lacune siano risolte o che il committente abbia accettato l'audit finale. `--require complete-audit` aggiunge invece i criteri completi del §3.4 della specifica, incluse copertura semantica, consegne e accettazione legata agli hash. Questa seconda richiesta non è una dipendenza della produzione del report.

## 7. Dipendenze, stop e autorizzazioni

Le dipendenze esterne del registro hanno questo significato:

| Identità | Evidenza necessaria prima del consumo |
|---|---|
| `execution-grant` | Autorizzazione del committente all'implementazione del piano esatto; attualmente assente. |
| `baseline-green` | Controlli esistenti sul candidato iniziale e snapshot delle fonti; attualmente non eseguiti. Un eventuale known-red richiede la sua specifica accettazione e non viene chiamato verde. |
| `inventory-lots-reviewed` | Tutte le partizioni fissate di T07 hanno autore e revisore, con hash correnti e lacune conservate. |
| `load-manifests-reviewed` | Tutti i profili attesi hanno una review oppure una consegna esplicitamente irrisolta, senza profili omessi. |
| `inventory-acceptance` | Risposta esplicita del committente sugli hash di inventario e audit finale, con perimetro e lacune. L'approvazione della specifica non la sostituisce. |

Quando un perimetro non può avere copertura completa, T15 produce comunque un report parziale corretto. La decisione di accettarlo come consegna parziale appartiene al committente; non sana lacune né autorizza una migrazione lazy. T16 non registra «inventario completo/no-loss del repository» se i criteri della specifica non sono soddisfatti.

Se una fonte normativa è ambigua, si preserva come tale e si chiede una decisione soltanto per il lavoro che ne dipende. L'analisi indipendente può continuare. Non si trasforma un task di audit in una correzione della normativa; parafrasi e rilocazioni restano fuori scope. Se servono file oltre il write set, è necessario aggiornare e riesaminare la task interessata prima di scriverli.

## 8. Verifica futura e criterio di completamento

Per ogni task di codice: test mirati del registro, con conteggio dei test eseguiti e risultato effettivo; verifica delle dipendenze stdlib e delle sentinelle degli input quando pertinente. A ogni onda di codice verificata si mantengono i controlli richiesti dal repository sul candidato corrente. Il piano non utilizza CI di un vecchio SHA come prova di byte non committati.

I comandi di progetto, da eseguire **solo nella fase autorizzata di implementazione**, sono raggruppati per contratto:

1. **Build:** `python scripts/daodan_build.py --check --support`.
2. **Linter:** `python scripts/lint_dependency_graph.py`, `python scripts/lint_bundled_paths.py`, `python scripts/lint_host_vocabulary.py`, `python scripts/lint_plugin_registration.py`, `python scripts/lint_fact_anchors.py`.
3. **Parità:** `python scripts/sync_plugin_docs.py --check` e `python scripts/sync_codex_instructions.py --check`.
4. **Test:** `python -m unittest discover -s tests -v` e `python adapters/copilot/policies/xray-guard/test_xray_guard.py`.
5. **Consegna:** verifica degli artefatti del registro, review indipendente di piano/task/onde e review finale del candidato secondo il metodo del repository; ricevute legate ai byte verificati.

La configurazione corrente della suite è documentata in `.github/workflows/consistency.yml:19-82`: Python 3.12, Node 22 per i test del loader, parser PyYAML già richiesto dai test del Work Controller. Questo piano non aggiunge una dipendenza esterna; se l'ambiente non offre i requisiti della suite, il controllo è indisponibile e non viene dichiarato passato. Non installare pacchetti implicitamente durante la pianificazione.

La matrice dei casi è intenzionalmente distribuita: EX-01..05 su record, span e audit; EX-06..10 su scenari, residenza e vincoli; EX-11..14 su snapshot, payload e report. T14 verifica anche la composizione fra moduli con dati sintetici indipendenti. T15 esercita gli strumenti sul corpus reale fissato; non prova il runtime degli agenti né l'efficacia su modelli low-cost.

La consegna futura comprende strumenti verificati, cinque render dorati, inventario con perimetro e attestazioni, manifest dichiarati e primo report con ignoti espliciti. Il completamento richiede tutte le task previste e le istanze dei lotti, controlli pertinenti e decisione del committente sull'audit. Registro tecnico verde, audit semanticamente completo e conformità runtime sono tre affermazioni differenti.

## 9. Stima e stato della pianificazione

**Stima preliminare, non misurata:** 24-40 ore di lavoro per strumenti, test e integrazione; 2-4 ore per cattura e verifica iniziale, se l'ambiente e la baseline sono già funzionanti. L'audit dell'intero corpus e la redazione dei manifest non hanno una durata attendibile prima del primo lotto. Riservare inizialmente 60-90 minuti a estrazione e seconda lettura di un lotto limitato; misurare blocchi/ora, ambiguità e correzioni per stimare il residuo. Nessuna stima di token o costo monetario è presentata come misura.

La sequenza rimane sul ramo singolo: cattura, inventario, report. Le verifiche intermedie evitano di accumulare una serie di cambiamenti non controllati. Non sono previste conversioni cosmetiche o sostituzioni della normativa per far diminuire i numeri.

| Stato | Contenuto |
|---|---|
| **Proposto** | 16 task fisse in micro-ondate sequenziali, più lotti espliciti di autoria/review dell'inventario e dei manifest; interfacce, write set, dipendenze e oracoli. |
| **Implementato** | Nessuno. Scritto solo questo piano; specifica approvata preservata. |
| **Verificato in pianificazione** | Hash della specifica, sorgenti e punti di riuso citati, assenza della mappa locale, convenzioni dei test e limiti del protocollo. I controlli strutturali del piano e la review documentale vengono comunicati con lo SHA-256 finale alla presentazione. |
| **Non verificato** | Test futuri, baseline di esecuzione, render dorati, copertura auditata, contabilità reale, tempi del corpus, runtime ed efficacia sui modelli. Nessun PASS di esecuzione o no-loss dichiarato. |

L'approvazione richiesta è del presente piano. L'implementazione richiede un'autorizzazione esplicita; commit, push, bump, migrazioni normative e fasi successive rimangono esclusi salvo richiesta specifica.
