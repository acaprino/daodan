# Benchmark: mappa del sistema

**Stato:** In parte. Misurati: il mappatore con un modello contro i riferimenti, il registro dei servizi, ciò che il grafo dà senza modello su phazly, il riuso di una seconda analisi, i percorsi con gli indicizzatori veri. Mancano: le varianti B e C del confronto fra grafo e modello, la fixture completa, le soglie confermate dal proprietario.

**Domanda.** La [spec della mappa del sistema](../../docs/specs/2026-11-18-flussi-e-mappa-del-sistema.md) regge? Cioè: quanta parte della mappa che una persona disegnerebbe (nodi, frecce, flussi) la macchina ricostruisce da sola, quanta ne aggiunge un modello, e a quale costo.

**Casi.** [`phazly-flow`](../phazly-flow/README.md), [`polar-flow`](../polar-flow/README.md), [`tududi-flow`](../tududi-flow/README.md), più i casi privati con un riferimento dell'intero sistema. Il codice dei casi non entra qui: solo nomi di file e valori attesi. Le run girano su Modal.

**Risultati validi oggi.**

| Domanda | Ultima misura | Dove |
| --- | --- | --- |
| Il mappatore con un modello riproduce l'area «pagamenti» di phazly? | no: da 1 a 3 nodi su 11, 0 flussi su 3 (Haiku 5.5 e Sonnet 5.5, 12 novembre) | [Area con un modello](#il-mappatore-con-un-modello-su-unarea) |
| Il mappatore con Haiku ricostruisce l'intero sistema alla cieca? | no: 0 flussi in ogni caso, nodi da 0 su 129 a 7 su 118 (cinque casi, 10 run, 23-24 novembre) | [Intero sistema alla cieca](#il-mappatore-con-un-modello-sullintero-sistema-alla-cieca) |
| Quante frecce e flussi del riferimento dà il grafo senza modello? | phazly: 129 frecce certe su 240, 18 flussi chiusi su 38 (23 novembre) | [`phazly-flow`](../phazly-flow/README.md#flussi-del-riferimento-chiusi-dal-grafo-senza-modello) |
| Il registro riconosce i servizi esterni? | richiamo 75%, 60% e 78,6% su tre casi, sotto la soglia dell'80% (12 novembre, prima dello stack dal fork) | [Registro](#il-registro-dei-servizi-esterni) |
| Una seconda analisi riusa la prima? | 131,5 s la prima, 1,2 s la seconda, 0 container (21 novembre) | [Riuso](#riuso-di-una-seconda-analisi) |
| Gli indicizzatori veri danno il percorso di un controllo? | sì su web, Tk, Tauri e Next.js (21 novembre) | [Percorsi veri](#percorsi-con-gli-indicizzatori-veri) |

**Passo successivo della pipeline.** Le misure senza modello si fermano al passo `analyze` (statico). Quante frecce mancanti chiude il passo dinamico (`observe`) su questi casi non è misurato; il passo dinamico sulle chiamate è misurato in [`call-provenance`](../call-provenance/README.md), l'esplorazione dell'app avviata in [`project-model`](../project-model/README.md). Dopo il modello la misura è quella delle due righe del mappatore qui sopra.

## Soglie

Scritte prima di ogni misura; il proprietario può cambiarle.

| Misura | Cosa si conta | Soglia |
| --- | --- | --- |
| 1 Riproduzione | su phazly, area «pagamenti e abbonamenti»: nodi del riferimento ritrovati, confrontati per file (indice di Jaccard almeno 0,5); flussi ritrovati (due terzi dei nodi); frecce rifiutate dopo la correzione | almeno 8 nodi su 11 e 3 flussi su 3; frecce rifiutate al massimo il 20% |
| 2 Secondo progetto | lo stesso prompt su polar o tududi: frecce provate o dichiarate; nomi letti a mano | almeno l'80% delle frecce provate o dichiarate; 8 nomi giusti su 10 |
| 3 Livelli | per un flusso del riferimento, a ogni livello: tipi dei nodi mostrati, punti citati | nessun nodo fuori dal suo livello; ogni punto citato esiste |
| 4 Costo | token e costo per mappa e per modello; aperture del sorgente | un'area entro 0,30 USD e 5 aperture; l'intero sistema entro 2 USD |
| 5 Stabilità | due esecuzioni sullo stesso snapshot, nodi confrontati per file | almeno l'80% dei nodi uguali |
| 6 Registro | servizi e progetti esterni riconosciuti contro l'elenco letto a mano dai manifest, per registro, stack-analyser e i due insieme | richiamo almeno 80% per caso; al massimo un riconoscimento sbagliato per caso |

## Parametri

| Parametro | Valori |
| --- | --- |
| limite della risposta di `brief` (`system_brief.LIMIT`) | oggi 31.800 caratteri di JSON; le misure del 12 novembre usavano un tetto del testo di 12.000, 24.000 e 48.000 caratteri, che nel codice non c'è più |
| punti d'ingresso mostrati per gruppo (`system_brief.HOLDERS`) | 5, 8, 12; oggi 8 |
| modello dell'agente | economico (Haiku 5.5), intermedio (Sonnet 5.5) |
| perimetro | un'area, l'intero sistema |
| generatori dei collegamenti possibili (`possible.py`) | nessuno, `ritorno`, `incerto`, tutti e due |

`score.py system` conta: `flows`, una corrispondenza uno a uno quando almeno due terzi dei nodi attesi stanno su percorsi diretti da un ingresso atteso a un effetto atteso (frecce provate o dichiarate, non scadute); `entries` ed `effects`, gli estremi collegati; `flows.by_type` chiede anche il tipo giusto e `flow_type_precision` è la quota di etichette di tipo corrette; `flows_by_nodes` è la sovrapposizione dei nodi (confrontabile con le misure sull'area) e `flows_depth_1` la somiglianza al primo livello.

## Riferimenti

- `expected/phazly-payments.json`: 11 nodi e 3 flussi (pagamento, gestione abbonamento, paywall e limiti d'uso) della mappa fatta a mano il 12 novembre 2026 e confermata dal proprietario; i 35 percorsi sono letti dall'archivio di phazly. Un nodo con codice si ritrova per file e chiavi di store, un nodo senza codice se un nodo nella stessa posizione cita uno dei suoi file, un nodo non visto per posizione e tipo.
- `expected/phazly-anchors.json`: i punti d'appoggio dei 3 flussi, dati a mano.
- `expected/externals-<caso>.json`: l'elenco a mano letto da manifest, Dockerfile, file compose e modelli di `.env`. In `externals` i servizi esterni e i progetti con un ruolo nell'architettura; in `also` ciò che una persona non nomina (linguaggi, build, stile, test, utilità), che non conta per il richiamo né come errore.

### Riferimenti dell'intero sistema

La mappa che una persona che conosce il prodotto disegnerebbe, per caso. Non sono nel repository: quattro casi su cinque sono privati, e gli script li leggono a runtime (`EXPECTED-system.json`, `--expected`).

- **Formato:** i campi di `daodan/system-map/v1` più `inside`, `what`, `proof`, `routes`, `registry`, `family`, `role` e `mode` su un nodo, `has`, `entries` ed `effects` su un flusso, `packages` e `gaps` sulla mappa (docstring di `reference.py`). Ogni nodo e ogni freccia cita una riga del progetto e un testo che quella riga contiene.
- **Controllo:** `python reference.py check EXPECTED.json PROJECT_ROOT` apre i file e non esegue nulla; `pin` lega il riferimento a un commit. Prova: `test_reference.py`.
- **Chi li scrive:** un agente per progetto con il brief [`reference-brief.md`](reference-brief.md), leggendo i file senza eseguirli.
- **Limite:** il proprietario ha confermato le regole (i tipi, `devops`, il database al primo livello), non i nodi né i flussi: ogni numero misurato contro di loro è una bozza (spec, «Limiti», punto 8).

## Script

| Domanda | Script | Prova |
| --- | --- | --- |
| Il mappatore con un modello | `modal_map.py spawn` (una sessione nuova di `claude -p --agent codebase-map:system-mapper` per caso, perimetro, modello e ripetizione), poi `score.py map` o `score.py system` | `tests/test_benchmark_system_map_score.py` |
| L'intera analisi, con o senza modello | `code_archive.py OUT.tar REPOSITORY@COMMIT`, `modal_map.py whole --tag TAG --cases CASO --tar CASO=OUT.tar [--models qwen,haiku,opus] [--reps 2]`, poi `score.py whole CARTELLA`: una tabella per caso, una riga per modello, «non misurato» con la causa dove manca una colonna | `test_code_archive.py`, `WholeTableTests` |
| Il container nella run su Modal | `modal run benchmarks/system-map/modal_map.py::engine_proof_run`, sulla fixture `js-npm-single`; chiede il client Modal 1.5.0 o successivo | `results/engine-proof.json` |
| Registro e scheda | `modal run benchmarks/system-map/modal_map.py::brief`, poi `score.py externals results/brief-<caso>.json expected/externals-<caso>.json registry` (oppure `stack-analyser`, `both`) | |
| Candidati e frecce senza modello | `candidates.py LINKS.json expected/phazly-payments.json FILES.txt`, `anchors.py LINKS.json expected/phazly-payments.json expected/phazly-anchors.json` | |
| Collegamenti possibili | `python daodan/core/flows.py links MANIFEST --rules RULES > LINKS.json`, poi `possible.py MANIFEST LINKS.json EXPECTED-system.json --generators ritorno,incerto`; su Modal `modal_map.py::possible` | `test_possible.py` |
| Tetto della scheda del percorso | `card_ceiling.py MANIFEST LINKS.json EXPECTED-system.json` | `test_card_ceiling.py` |
| Ingressi del riferimento contro i candidati dei lettori | `entries.py measure CANDIDATES.json EXPECTED.json FILES.txt` | `test_entries.py` |
| Schede di traccia: il modello trova, corregge e certifica flussi su archi che la macchina ha | `traces.py cards`, `ask`, `verify` | `test_traces.py` |
| Ricerca in parole di un flusso o di una parte | `embed_queries.py`, `embed_probe.py`, `modal_embed.py` | |
| Riuso | `path_reuse.py`, `pipeline_reuse.py [--container]`, `path_observations.py` | |
| Percorsi veri | `real_paths.py [web] [tk] [tauri] [next] [--work DIR]` | |
| Tre corse sullo stesso progetto | `score.py runs DA-ZERO SENZA-MODIFICHE UN-MODULO`; parametri e risultati in [`project-model`](../project-model/README.md) | |

**Risultati senza il loro file.** I risultati di `entries.py`, `traces.py` e degli script `embed_*`, e le misure sui cinque riferimenti dell'intero sistema, non sono in questo README e non lo sono mai stati in git. Le spec [mappa del sistema](../../docs/specs/2026-11-18-flussi-e-mappa-del-sistema.md), [ingressi e scoperta dei flussi](../../docs/specs/2026-11-20-ingressi-e-scoperta-dei-flussi.md) e [ricerca e pacchetto di review](../../docs/specs/2026-11-20-ricerca-e-pacchetto-di-review.md) citano sezioni di questo file che non esistono: «Misura di partenza», «Il tetto: l'accordo fra due mappatori», «Soglie proposte», «Ingressi senza regole», «Le tre reti», «Schede dei percorsi», «Schede dei percorsi, prova a costo zero», «Legami fra flussi», «Embedder piccoli», «Su 531 richieste in parole». I numeri che quelle spec riportano restano senza una prova rieseguibile in questa cartella finché le sezioni non sono riscritte dai risultati.

## Risultati

### Il mappatore con un modello, su un'area

12 novembre 2026, tag `system-map-runs2`: 16 run su Modal, phazly e tududi, area «pagamenti e abbonamenti» e intero sistema, Haiku 5.5 e Sonnet 5.5, due ripetizioni, `HOLDERS` 8, tetto del testo di allora 24.000 caratteri. 1,37 USD in tutto. Valori per run in `results/runs2-20261112.json`.

| Misura | Risultato | Soglia |
| --- | --- | --- |
| 1 Riproduzione, phazly area | nodi ritrovati: Haiku 1 e 2, Sonnet 3 e 1 su 11; flussi 0 su 3; frecce rifiutate 0% | non raggiunta |
| 1 Riproduzione, phazly intero sistema | 0 nodi su 11 in tutte e quattro le run | non raggiunta |
| 2 Secondo progetto, tududi | frecce provate o dichiarate 57 su 60 (95%), solo 4 provate; nomi letti a mano 8 su 10 | raggiunta |
| 3 Livelli | da 5 a 50 viste per run sui due casi: nessun nodo fuori dal suo livello, nessun punto citato che manca | raggiunta |
| 4 Costo | area: Haiku da 0,008 a 0,010 USD, Sonnet da 0,11 a 0,20; intero sistema: Haiku da 0,010 a 0,019, Sonnet da 0,13 a 0,26; aperture del sorgente da 0 a 2 | raggiunta |
| 5 Stabilità | nodi uguali fra le due ripetizioni: da 0% a 55%; il migliore è tududi, intero sistema, Haiku (6 su 11) | non raggiunta |

- Nomi letti a mano (tududi, area, Sonnet, prima ripetizione, e due nodi dell'intero sistema). Giusti: API abbonamenti, Gestione abbonamenti, Pagina admin fatturazione, Provider di pagamento, Scheda Abbonamento, Utente, Assistente MCP, Piano del giorno. Sbagliati: Client abbonamenti (il nome del codice, non della cosa) e Gateway di pagamento (un nodo solo per Stripe, Paddle e Lemon Squeezy).
- **La correzione toglieva ciò che era stato accettato:** in 5 run su 8 dell'area il rapporto della correzione toglie da 3 a 5 nodi e flussi. Dopo questa misura una proposta non toglie più ciò che non nomina, e una freccia verso un membro indicato come funzione si prova anche sul file. Non rimisurato sull'area dopo la modifica.
- **Pochi nodi per area:** da 2 a 8 dove il riferimento ne ha 11; il taglio segue i gestori più che le cose che una persona nomina. Mancano Google Play Billing, i limiti d'uso e i consumi.
- **L'intero sistema in una proposta** dà da 2 a 18 nodi, spesso un file per nodo.
- Il modello dell'agente non è fissato: la differenza fra Haiku e Sonnet è più piccola della variazione fra ripetizioni.
- `results/runs-20261112.json` è la tornata precedente dello stesso giorno, superata da questa: su tududi nessuna mappa veniva registrata perché la risposta di `brief` (51,9 KB) superava il limite dell'host. Da lì viene `system_brief.LIMIT`.

### Il mappatore con un modello, sull'intero sistema, alla cieca

Il riferimento resta fuori dall'ambiente dell'agente ed è confrontato dopo il salvataggio.

**Cinque casi, 23 e 24 novembre 2026** (`modal_map.py whole --models haiku --reps 2 --budget 1`, Haiku 5.5, 10 run indipendenti, ognuna con la sua pass del motore e le sue due sessioni; registrata nel [piano dell'analisi unificata](../../docs/plans/2026-11-20-analisi-unificata.md), task 2; i risultati per caso restano fuori da git):

- nodi ritrovati da 0 su 129 a 7 su 118; flussi 0 in ogni caso;
- due ripetizioni concordano su da 1 su 3 a 5 su 7 nodi;
- sessioni 2,02 USD in tutto, da 0,26 a 0,76 per caso; nessuna fermata per budget;
- la pass del caso più grande impiega da 51 a 68 minuti.

Senza modello (tag `whole-nomodel-1`, 23 novembre): indici `fresh` per tutti i linguaggi dei cinque casi tranne Kotlin in uno; i candidati degli ingressi si producono per tutti e cinque.

**Il caso più piccolo, 21 novembre 2026** (`modal_map.py spawn --tag collaudo-cieco-haiku --rules session --scopes system --models haiku --reps 2 --budget 1`; 49 nodi confrontabili, 19 flussi, 22 ingressi, 24 effetti; archivio di solo codice, 178 file). I `map.json` della run non sono nel repository: la cartella `results/system/collaudo-cieco-haiku/` citata dalla misura non c'è.

| Misura | Ripetizione 1 | Ripetizione 2 |
| --- | ---: | ---: |
| Flussi ritrovati / proposti | 0 su 19 / 2 | 0 su 19 / 3 |
| Ingressi / effetti ritrovati | 0 su 22 / 0 su 24 | 0 su 22 / 0 su 24 |
| Nodi ritrovati (profondità 0 e 1) | 3 su 49 (3 su 12) | 7 su 49 (7 su 12) |
| Precisione dei nodi | 4 su 7 | 9 su 10 |
| Flussi alla profondità 1 | 26% | 38% |
| Frecce rifiutate | 0 su 7 | 1 su 8 |
| Schede in coda / aperte / decisioni di percorso | 50 / 0 / 0 | 49 / 0 / 0 |
| Mapper: secondi, turni | 60, 9 | 67, 10 |
| Costo (USD) | 0,048, con le 88 regole | 0,019 |

Il mappatore elenca le schede dei percorsi e passa alla proposta libera senza aprirne una. Con `--models qwen` la sessione delle regole si è fermata dopo 1.574 secondi: il gateway rifiutava la connessione.

**Non misurato:** Qwen e Opus; le colonne delle schede dei percorsi con il modello e della ricerca.

**Perché il risultato è così basso:** la sessione del mappatore con Haiku dura da 5 a 12 turni e spende da 0,008 a 0,05 dollari, con il tetto di 1 dollaro intatto, e usa solo lo strumento `flows`: si ferma da sola con «con il budget rimasto non l'ho fatto» davanti a centinaia di schede dei percorsi da rivedere (798 in un caso); in quel caso il riepilogo dice anche 0 rotte collegate su 33 chiamate, quindi le frecce dal sito alle API e dalle API ai dati non si provano. Due cause diverse: l'agente si ferma presto (prompt o modello) e il legame delle rotte non c'è nel grafo. **Il legame delle rotte, riprovato il 24 novembre** (`modal_map.py::routes_case`, lo stesso caso e le stesse regole salvate, senza modello, al codice con `97b5851bc`): rotte offerte da 1 a 121, chiamate 33, collegate da 0 a 23; 120 righe di Noir legate a una funzione. La causa (due investigatori indipendenti, Opus e Fable, in sola lettura, concordi) era il nome che Noir dà ai metodi Spring, `Classe.metodo`, confrontato con il solo `metodo`: corretto da `97b5851bc`, e la prova che mancava è `test_a_spring_method_noir_names_with_its_class_is_an_offered_route_that_a_call_of_another_module_meets` (fallisce sul codice precedente con offerte 0 e collegate 0, passa sull'attuale). Restano 10 chiamate senza rotta: 5 di un controller il cui file non dà dichiarazioni a Noir (5 righe «no function starts at the line»), 1 con un buco incollato a un testo fisso (`/properties{}`) e 4 senza il prefisso della base (`/parts/{}`, `/complete`, `/retry`, `/logout`). Il secondo controllo, con i testi completi delle lacune, ha corretto una mia ipotesi: Noir cita la riga del `fun` e non quella dell'annotazione, e il file del controller ha 0 dichiarazioni nello snapshot; delle altre 50 righe di Noir senza gestore, quasi tutte non hanno una funzione da legare per natura (un server di prova, file OpenAPI, endpoint di Actuator dichiarati in `build.gradle.kts`, script). **Rotte dichiarate solo da una specifica (24 novembre):** le righe di Noir con l'etichetta `spec-only` (qui 5, tra cui `POST /logout`, una delle chiamate senza rotta) non sono più lacune: `flows._spec_routes` le offre al nodo del file della specifica quando nessun codice offre lo stesso metodo e percorso, e l'arco che le incontra porta `spec`; tre test in `tests/test_codebase_map_flows_noir_binding.py`, il principale rosso prima del codice, 192 test verdi nelle suite collegate. **Un difetto trovato dalla suite intera:** gli archivi apt `http://` dei registri passano per indirizzo alla lista di rete della sandbox di preparazione, e Modal rifiuta gli indirizzi IPv6 (`Network access allowlist does not support IPv6 CIDRs`): ora solo IPv4, con un test; un host solo IPv6 è una lacuna `network_archive_unresolved`. **Il file Kotlin con 0 dichiarazioni**, riprodotto su uno snapshot di quel solo file: il parser Kotlin segnala `has_error` sul corpo della classe senza nodo `ERROR` né token mancante (un `companion object { const val A=..; private val b=.. }` su una riga), `check_syntax_errors` scriveva «line 1» e `semantic_store` leggeva il file `lexical` (`source-not-successfully-parsed`), senza dichiarazioni. Ora il nodo che ha l'errore quando nessun figlio ce l'ha è il luogo dell'errore (`semantic._around`, `_treesitter.check_syntax_errors`): il file è `partial`, con le righe non lette, e le dichiarazioni restano; test `tests/test_codebase_map_syntax_error_without_place.py`, rosso prima del codice. **Errore mio, trovato dal caso vero:** nell'uscita di Noir le etichette sono oggetti con `name`, non stringhe; i test con stringhe passavano e la funzione non scattava (ora entrambe le forme, con il test nella forma vera). **Esito sul caso vero**, senza modello e con le regole salvate, rotte offerte e chiamate collegate su 33: 1 e 0 (23 novembre), 121 e 23 (con `97b5851bc`), 126 e 28 (con il parser Kotlin corretto), **131 e 29** (con le rotte della specifica). Restano 4 chiamate senza rotta: `/properties{}` (un buco incollato a un testo fisso) e `/parts/{}`, `/complete`, `/retry` (il prefisso della base perso sul lato che chiama, cioè i wrapper HTTP, non ancora esaminati). Nei 270 testi di strumenti consegnati ai modelli nelle 10 run, 206 letti come JSON, i segreti mascherati sono 0 (nell'archivio sono 16).

### Grafo contro modello: il confronto ancora da fare

**Stato:** Aperta: da approfondire. La domanda: partendo dal grafo che la macchina costruisce a strati, un modello che nomina processi e varianti dà una mappa migliore, e a quale costo, di un modello che propone da solo? Finora è misurata solo la variante A.

| Variante | Compito | Stato |
| --- | --- | --- |
| A, attuale | il mappatore attuale sull'intero sistema | misurata: le due sezioni qui sopra |
| B, grafo | parte da ingressi ed effetti dell'intero inventario; il modello identifica processi e varianti, la macchina verifica i percorsi | non eseguita |
| C, grafo e schede | come B, con l'accesso mirato alle schede di simbolo aggiornate | non eseguita |

Protocollo, per la spec del 18 novembre:

- **Scoperta cieca.** Stessa richiesta («analizza questo sistema») e stesso snapshot completo per ogni variante. Prompt, regole e schede senza etichette del valutatore; riferimenti, aree attese, nomi e numero di processi fuori dall'ambiente dell'agente. Il valutatore confronta la mappa salvata prima di ogni richiesta di review.
- **Casi.** Su phazly i tre flussi dell'area pagamenti; gli altri flussi scoperti si giudicano a parte prima di contarli come errati. Per il richiamo sull'intero sistema serve una fixture nel repository con inventario manuale esaustivo: più funzionalità, una con ramo utente e cron, un modulo condiviso con un altro processo, un effetto il cui ingresso resta irrisolto. **Da produrre.**
- **Misure.** Due ripetizioni indipendenti per variante e caso, a parità di grafo, modello, tetto di contesto e budget. Flussi e varianti mancanti, estranei, accorpati o duplicati, verificati per ingressi, effetti e membri anche quando il nome differisce. Estremi spiegati, esclusi con motivo, irrisolti e non esaminati. Token, aperture e costo dell'intero run, distinguendo riuso e prima generazione delle schede.
- **Criteri sulla fixture completa.** Tutti i processi e le varianti attesi, il modulo condiviso una sola volta, ogni estremo reso conto, nessun arco causale senza evidenza. Aprire il processo mostra i due rami e richiuderlo ripristina la selezione, con zero chiamate al modello. Poi una review della funzionalità e una del solo ramo automatico.
- **Attribuzione.** Se il grafo non espone un ingresso o un effetto, l'omissione è della raccolta delle evidenze; se il riferimento è visibile al modello e viene interpretato male, è della scoperta semantica. A qualità uguale vince il minor consumo totale.

Ciò che c'è già senza modello, da mettere a confronto: [flussi chiusi dal grafo](../phazly-flow/README.md#flussi-del-riferimento-chiusi-dal-grafo-senza-modello) e [tetto della scheda del percorso](../phazly-flow/README.md#il-tetto-della-scheda-del-percorso-senza-modello).

### Che cosa dà il grafo senza modello, sull'area dei pagamenti di phazly

13 novembre 2026, sui collegamenti di phazly calcolati con il motore; nessun modello.

**Candidati** (`candidates.py`: la partizione per dominatori del grafo dei file dai punti d'ingresso; ogni chiave di store è un candidato).

| Cosa | Risultato |
| --- | --- |
| Candidati | 408, di cui 123 chiavi di store; 360 hanno un solo file |
| File di codice | 386 in un candidato, 618 che nessun punto d'ingresso raggiunge |
| Candidati con file di due nodi del riferimento | nessuno |
| Nodi del riferimento come unione di candidati | Funzioni a consumo, API diritti, Abbonamento, Consumi interi; API acquisti 9 file su 11; Paywall 2 su 4; Scheda abbonamento 2 su 5 |
| File che i candidati aggiungono ai nodi del riferimento | 22 a Funzioni a consumo e 2 ad API diritti: le funzioni di supporto dei gestori |
| Frecce del riferimento fra nodi con codice ricavate dai soli collegamenti | 5 su 6 |

- La regola dei gruppi è un gruppo per risorsa: con una soglia sulla quota dei punti d'ingresso (20%) phazly formava un solo gruppo da 117 e la fixture `flow-model` nessuno.
- La freccia mancante, API diritti → Consumi, veniva da `db[USAGE_EVENTS_COLLECTION]`, una forma che le regole non leggevano. La chiave dello store come indice costante è letta dal 23 novembre: [`phazly-flow`](../phazly-flow/README.md#flussi-del-riferimento-chiusi-dal-grafo-senza-modello).
- I soli collegamenti trovano una freccia vera che il riferimento non ha: API acquisti → API diritti, 13 chiamate.
- I 618 file che nessun punto d'ingresso raggiunge sono soprattutto componenti dell'interfaccia: rendere un componente non è un collegamento.

**Flussi dai punti d'appoggio** (`anchors.py`: la macchina prende ciò che sta su un percorso da una partenza a un arrivo, senza limite di passi).

| Flusso | Nodi del riferimento con codice attraversati | File estranei | Dove il grafo si ferma |
| --- | --- | --- | --- |
| Pagamento | API acquisti, Abbonamento; manca Paywall | 0 | `PaywallModal.handleCheckout` non raggiunge niente fuori dal suo file |
| Gestione abbonamento | API acquisti, Abbonamento; manca Scheda abbonamento | 0 | `SubscriptionCard.handleOpenPortal` e `handleSetRenewal`, come sopra |
| Paywall e limiti d'uso | Funzioni a consumo, API diritti, Abbonamento; mancano Consumi e Paywall | 0 | nessuna partenza raggiunge `mongo/usageEvents` |

Nessun percorso si allarga: 0 file fuori dal riferimento, fra 4 e 6 file o chiavi per flusso. I nodi mancanti dell'interfaccia vengono dal contesto React (`startCheckout` da `useSubscription()`): non misurato dopo il passo dinamico.

### Collegamenti possibili

Un collegamento possibile è un collegamento che la macchina propone senza affermarlo e che un modello conferma o scarta. `possible.py` verifica le frecce fra nodi con codice con `system_map.verify`, prima con i soli collegamenti certi e poi con i possibili. Generatori:

- `ritorno`: una rotta di una regola `offre` che nessuna chiamata del progetto raggiunge, in un file che usa un modulo esterno, è chiamata da quel modulo;
- `incerto`: una chiamata con più rotte candidate va a ognuna.

Un possibile fuori dal riferimento è contato in `outside_reference`, non come sbagliato. Il contesto React non ha un generatore.

Su phazly (riferimento dell'intero sistema: 38 flussi, 240 frecce; pipeline intera su Modal fino ad `analyze`, 22 novembre 2026): con gli archi `usa` ricavati dalle chiamate nei pacchetti dei servizi, quattro servizi del riferimento hanno un modulo (Stripe, Firebase Authentication, MongoDB Atlas, Resend) e gli archi `usa` nei collegamenti passano da 2 a 150. `ritorno` propone 4 possibili: uno è il ritorno di Stripe sul gestore del webhook, e «Rinnovo e variazione dell'abbonamento» si chiude solo con quello; gli altri 3 sono fuori dal riferimento e non sono stati letti. `incerto` ne propone 0. Tredici servizi restano senza modulo: lo stack li riconosce da un host o da una variabile, non da un pacchetto.

I totali di frecce e flussi di oggi stanno in [`phazly-flow`](../phazly-flow/README.md#flussi-del-riferimento-chiusi-dal-grafo-senza-modello). Un indice del motore è letto solo dal codice che l'ha scritto: un conteggio fatto con un codice diverso ripiega sul parser semplice senza errori (qui dava 13.621 chiamate invece di 23.867). **Non misurato:** gli altri casi con riferimento; un modello che conferma o scarta i possibili.

### Il registro dei servizi esterni

12 novembre 2026, su Modal, senza modello. Lo step `stack` è cambiato dopo questa misura (stack dal fork): il confronto di oggi è in [`project-model`](../project-model/README.md); questi tre casi non sono stati rimisurati.

| Caso | Attesi | Registro | stack-analyser | Insieme | Falsi letti al punto citato |
| --- | --- | --- | --- | --- | --- |
| phazly | 16 | 75,0% | 37,5% | 75,0% | 1: `ghost` da un nome in un test |
| polar | 25 | 60,0% | 32,0% | 60,0% | 0 |
| tududi | 14 | 78,6% | 78,6% | 78,6% | 3: `zoom` da un tipo TypeScript, `caddy` e `kubernetes` dagli esempi in `docs/examples` |

Nessun caso raggiunge la soglia del richiamo. File: `results/brief-<caso>.json`.

- Mancano dal registro: Zustand, Motor, Dramatiq, Logfire, Numeral, Plain, IPinfo, Google Play Billing.
- Il registro ha la voce ma non il segno che il progetto mostra: AWS (`boto3`), GitHub (`githubkit`), Expo (`exponent-server-sdk`), MinIO e Tailscale (immagini), Cloud Run, Cloudflare in tududi (`TURNSTILE_*`), Google Calendar.
- L'elenco letto dai soli manifest non vede i servizi chiamati via HTTP e configurati con variabili: in polar il registro trova Discord, Linear, Slack, Resend e OpenAI, in tududi Discord, tutti veri al punto citato.
- Gli esempi di documentazione contano come configurazione del progetto.

**Costruzione del registro** (12 novembre): 2.172 voci da stack-analyser 1.27.6 (743 regole), CNCF Landscape (commit `75b47639`) e Simple Icons 16.37.0. `derive`, senza modello, trova pacchetti su PyPI, crates.io o nel proxy di Go per 102 delle 455 voci con un pacchetto npm. Una run di Haiku 5.5 (0,023 USD, 40.257 token in uscita) propone il resto: la macchina ne tiene 141, fra cui FastAPI, Flask e Pydantic, e ne rifiuta 22, compresi pacchetti veri con un altro proprietario (`boto3`, `prometheus-client`, il driver Go di MongoDB).

### Riuso di una seconda analisi

21 novembre 2026. Nessun sorgente delle fixture è eseguito sull'host.

**Due analisi complete con il container acceso** (`pipeline_reuse.py --container`, fixture `js-npm-single`, due processi; ripristino, scip-typescript e `node --test` girano davvero):

| Misura | Prima analisi | Seconda analisi |
| --- | ---: | ---: |
| Secondi | 131,5 | 1,2 |
| Indice / archi osservati dai test | `fresh` / 6 | `fresh` / 6, riusati |
| Richieste di container / copie del progetto | 6 / 6 | 0 / 0 |
| Avvii dell'indicizzatore / sonde del motore | 1 / 7 | 0 / 0 |
| Download di strumenti (già in cache) | 0 | 0 |
| Aperture di sorgenti / elenchi di cartelle da Python | 52 / 39 | 4 / 0 |
| Parse tree-sitter | 2 | 0 |
| Processi `wsl` / `git` / `uv --offline` | 118 / 12 / 2 | 0 / 1 / 0 |

Nella seconda analisi resta una lettura per ognuno dei quattro file, per confrontare lo snapshot con il disco, e un comando git. Le letture interne dei programmi nel container non sono contate.

**Con il container spento** (`pipeline_reuse.py`, `DAODAN_CONTAINER=off`): la seconda analisi apre 4 file del progetto contro 14, elenca 0 directory contro 9, lancia 1 processo git contro 5, non rigenera la pre-mappa e riusa il grafo dei moduli. Le quattro lacune del container (go-enry, Renovate, npm, Noir) si riaprono con la loro causa senza un nuovo tentativo. Il riuso vale quando snapshot e sorgenti sono gli stessi, il runner è quello predefinito e lo spegnimento è già registrato per tutte le sorgenti rimaste.

**Scheda «Paga», riapertura e seconda corsa** (`path_reuse.py`, snapshot SQLite della fixture `flow-model`, undici regole; CLI, MCP e HTTP danno gli stessi passi):

| Operazione sullo snapshot già scritto | Aperture sorgenti | Parse tree-sitter | Inventari AST / costruzioni link | Inventari schede / espansioni | Connessioni manifest / cache schede |
| --- | ---: | ---: | ---: | ---: | ---: |
| Registrare le regole | 23 | 23 | 1 / 1 | 0 / 0 | 8 / 0 |
| Aprire elenco e scheda | 0 | 0 | 0 / 0 | 1 / 1 | 8 / 3 |
| Ripetere elenco e scheda con un nuovo servizio | 0 | 0 | 0 / 0 | 0 / 0 | 10 / 5 |
| Riaprire il flusso per nome | 0 | 0 | 0 / 0 | 0 / 0 | 6 / 1 |

Il percorso registrato segue `onPayClick → submitPayment → store:web state/payment`; la sola scrittura presentata come passo iniziale è rifiutata per discontinuità. Il [test di costo](../../tests/test_flow_path_identity.py) conta 256 visite per indicizzare 256 percorsi indipendenti e 512 per 512. La misura esclude la creazione dello snapshot e il costo di una vera analisi dinamica.

**Scheda globale** (`tests/test_codebase_map_system_brief.py::DeclaredTests::test_global_brief_reopens_only_changed_unmodelled_yaml`): alla prima consultazione apre i soli manifest Kubernetes e Backstage (2 aperture), nessun sorgente alla seconda; cambiando il catalogo riapre un solo file.

**Candidati prima delle regole e osservazioni registrate** (`path_observations.py`, righe dell'indice e osservazioni sintetiche, scanner simulato): prima delle regole CLI, MCP e app trovano il candidato `@trigger("refresh")` con gestore `controls.py::dispatch`; la scheda espone l'osservazione esatta, il campione e il conflitto fra destinazione statica e osservata; i tre canali accettano `store:db/payments` e rifiutano `store:db/orders` (campione) e `store:db/refunds` (conflitto).

Tre corse sullo stesso progetto (da zero, senza modifiche, un modulo cambiato): [`project-model`](../project-model/README.md).

### Percorsi con gli indicizzatori veri

21 novembre 2026, `real_paths.py` con un motore di container: lo script crea il run dal servizio con il passaggio del motore, legge i candidati prima delle regole, registra regole e risposte, apre ogni scheda e controlla ciò che deve reggere; esce con 1 se un controllo cade.

| Caso | Indicizzatori nel container | Secondi | Controllo, gestore, ultimo punto provato |
| --- | --- | ---: | --- |
| web (`benchmarks/flow-model/app`) | scip-python 0.6.8, scip-typescript 0.6.2 | 129 | «Paga» `web/checkout.ts:22` → `onPayClick` → `submitPayment` → `store:web state/payment` (`web/checkout.ts:14`) |
| tk (`real-paths/tk-desk`) | scip-python 0.6.8 | 106 | «Salva» `ui.py:8` → `App.save` (gestore dato dall'indice) → `store:disk/orders` (`ui.py:11`) |
| tauri (`real-paths/tauri-desk`) | scip-typescript 0.6.2, rust-analyzer 2026-11-09 | 322 | «Salva profilo» `src/view.tsx:18` → `save` → `src-tauri/src/main.rs::persist` (`tauri-invoke`, `src/view.tsx:4`); `only_in_tests` e `on_idle_builder` restano lacune |

Con 6,4 GB liberi rust-analyzer non parte (ne chiede 8) ed è una lacuna con la causa. Le stesse tre fixture su Modal (`modal_pipeline.py --folder-out`): indici `fresh` in 132, 100 e 242 secondi. Le fixture non dichiarano test: nessun arco osservato.

#### Le rotte di Next.js dallo strumento del framework

`real_paths.py next`, fixture `real-paths/next-shop`, Next.js 16.4.6, App Router; la sorgente della pre-mappa lancia `next typegen` del progetto nel container e legge `.next/types/validator.ts`.

| Controllo | Container locale | Modal |
| --- | --- | --- |
| secondi dell'analisi | 169 | 145 |
| `/checkout` è un ingresso sulla funzione della pagina (`app/checkout/page.tsx::Checkout`, riga 3) | sì | sì |
| `/api/pay` è una sola voce, su `app/api/pay/route.ts::POST` | sì | sì |
| nessun ingresso è la rotta `/pay` | sì | sì |
| la scheda «Paga» arriva a `app/checkout/actions.ts::pay` | sì | non misurato: il giro su Modal non apre le schede |

`next typegen` da solo, nel container senza rete: 0,9 secondi; `next build` 7,9 secondi. Non provati: il Pages Router, un `distDir` diverso, una versione senza `typegen` (la fixture `js-nextjs`, Next.js 14, dà la lacuna `model_failed`).

### Il container nella run della mappa su Modal

23 novembre 2026, `engine_proof_run` sulla fixture `js-npm-single`: 5 controlli su 5 passano (`results/engine-proof.json`).

1. `engine-report.json` dice scip-typescript `fresh`.
2. Un arco osservato del passo dinamico è nell'archivio `engine-edges.sqlite`, su `src/index.js`.
3. La preparazione raggiunge `pypi.org` e rifiuta un host fuori dai registri, un indirizzo HTTP semplice e un indirizzo IP.
4. Una sandbox non vede `/results` né i risultati di un altro caso, e non scrive nella sua cartella.
5. Dopo una preparazione fallita e una sandbox che non parte non resta nulla sul volume né in esecuzione.

## Aperto

- **Grafo contro modello:** varianti B e C e fixture completa, sopra.
- **Soglie:** quelle dell'intero sistema sono proposte; il proprietario non ha confermato nodi e flussi dei riferimenti.
- **Passo dinamico sui flussi:** quante frecce mancanti chiude, non misurato su nessun caso con riferimento.
- **Registro:** i tre casi dopo lo stack dal fork.
- **Sezioni citate dalle spec e assenti:** vedi «Risultati senza il loro file», sotto la tabella degli script.
