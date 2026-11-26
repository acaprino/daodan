# Benchmark: mappa del sistema

Prova la [spec della mappa del sistema](../../docs/specs/2026-11-18-flussi-e-mappa-del-sistema.md), misure da 1 a 6. Le soglie sono scritte qui prima di ogni misura; il proprietario può cambiarle. I casi sono quelli dei benchmark dei flussi: [`polar-flow`](../polar-flow/README.md) e [`tududi-flow`](../tududi-flow/README.md). Le regole di collegamento ci sono per tududi (`benchmarks/tududi-flow/rules.json`, scritte a mano il 12 novembre 2026 per la misura 2: store di Zustand, chiamate `fetch(getApiPath(...))`, rotte di Express, modelli di Sequelize). Il codice dei casi non entra qui: solo nomi di file e valori attesi. Le run girano su Modal, in un processo nuovo.

## Soglie

| Misura | Cosa si conta | Soglia |
| --- | --- | --- |
| 1 Riproduzione | su un'area di un riferimento: nodi del riferimento ritrovati, confrontati per file (indice di Jaccard almeno 0,5); flussi ritrovati (due terzi dei nodi); frecce rifiutate dopo la correzione. L'unico riferimento d'area era di un progetto privato, tolto: nessun caso la misura | i nodi e i flussi da fissare con il caso; frecce rifiutate al massimo il 20% |
| 2 Secondo progetto | lo stesso prompt su polar o tududi: frecce provate o dichiarate; nomi letti a mano | almeno l'80% delle frecce provate o dichiarate; 8 nomi giusti su 10 |
| 3 Livelli | per un flusso del riferimento, a ogni livello: tipi dei nodi mostrati, punti citati | nessun nodo fuori dal suo livello; ogni punto citato esiste |
| 4 Costo | token e costo per mappa e per modello; aperture del sorgente | un'area entro 0,30 USD e 5 aperture; l'intero sistema entro 2 USD |
| 5 Stabilità | due esecuzioni sullo stesso snapshot, nodi confrontati per file | almeno l'80% dei nodi uguali |
| 6 Registro | servizi e progetti esterni riconosciuti contro l'elenco letto a mano dai manifest, per registro, stack-analyser e i due insieme | richiamo almeno 80% per caso; al massimo un riconoscimento sbagliato per caso |

## Parametri da provare

Nel comando `score.py system`, `flows_by_nodes` misura la sovrapposizione dei nodi e `flows_depth_1` la somiglianza al primo livello. `flows` conta una corrispondenza uno a uno quando almeno due terzi dei nodi attesi appartengono a percorsi diretti da un ingresso atteso a un effetto atteso. I percorsi seguono frecce provate o dichiarate e scartano quelle scadute. `entries` e `effects` contano gli estremi collegati. `flows.by_type` richiede anche il tipo corretto e `flow_type_precision` indica la quota di etichette di tipo corrette su tutte quelle proposte. Le misure storiche dell'intero sistema basate sui soli nodi sono confrontabili con `flows_by_nodes`.

| Parametro | Valori |
| --- | --- |
| tetto della scheda (`system_brief.LIMIT` (il limite dell'intera risposta, da cui si ricava il tetto della scheda)) | 12.000, 24.000, 48.000 caratteri |
| punti d'ingresso mostrati per gruppo (`HOLDERS`) | 5, 8, 12 |
| modello dell'agente | economico (Haiku 5.5), intermedio (Sonnet 5.5) |
| perimetro | un'area, l'intero sistema |
| generatori dei collegamenti possibili (`possible.py`) | nessuno, `ritorno`, `incerto`, tutti e due |

## Riferimenti attesi

- `expected/externals-<caso>.json`: per ogni caso l'elenco a mano letto dai manifest, dai Dockerfile, dai file compose e dai modelli di `.env` del perimetro dello snapshot (`read`). In `externals` stanno ogni servizio esterno che quei file nominano e i progetti con un ruolo nell'architettura (framework dell'applicazione, guscio dell'app, accesso ai dati, stato, code, container). In `also` stanno le cose usate che una persona non nomina (linguaggi, strumenti di build, stile, test e lint, librerie di utilità): non contano per il richiamo né come errore. Un identificatore che il registro non ha è scritto come nome semplice (`zustand`).

- `../project-model/fixtures/real-<caso>/system.json` e `graph.json`, per cinque progetti pubblici di complessità crescente: `auth0-go`, `sveltekit-realworld`, `microblog`, `next-subscriptions`, `bank-of-anthos`. Un caso reale misura Daodan nel complesso e sta in una cartella sola del corpus, con `source.json` (repository e commit), `expected.json` (la pre-mappa), `system.json` e `graph.json`: [`project-model/README.md`](../project-model/README.md), «Casi reali completi». Scritti a mano il 25 novembre 2026 leggendo il codice a quel commit, senza eseguirlo: sono ciò che Daodan dovrebbe dare a refactoring finito, non una sua uscita, e nessuna misura è ancora stata fatta contro di loro. La mappa di sistema segue `reference-brief.md` e passa `python reference.py check ../project-model/fixtures/real-<caso>/system.json CHECKOUT` senza problemi. Il grafo (`daodan/real-graph-expected/v1`) è ciò che gli otto step danno sotto la mappa: moduli e tecnologie, ingressi (rotte, pagine, azioni), rotte unite ai loro chiamanti per metodo e percorso, chiamate ai servizi esterni, store con chi scrive e chi legge, configurazione e lacune; lo controlla `python real_references.py <caso> CHECKOUT` (percorsi, simboli e righe citati), e `test_real_references.py` ne tiene la forma. Oltre ai campi comuni ogni grafo aggiunge quelli che il suo framework chiede (azioni di form, server action, hook, webhook, lavori): non sono ancora un contratto.

| Caso | Nodi | Flussi | Frecce | Rotte | Chiamanti uniti | Chiamate esterne | Store | Lacune del grafo |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `auth0-go` | 17 | 7 | 45 | 11 | 9 | 9 | 6 | 7 |
| `sveltekit-realworld` | 20 | 18 | 137 | 21 | 53 | 24 | 3 | 16 |
| `microblog` | 61 | 33 | 176 | 36 | 60 | 13 | 13 | 22 |
| `next-subscriptions` | 38 | 24 | 164 | 9 | 71 | 42 | 13 | 25 |
| `bank-of-anthos` | 44 | 27 | 158 | 40 | 74 | 34 | 12 | 25 |

### Riferimenti dell'intero sistema

`expected/<caso>-system.json` è la mappa che disegnerebbe una persona che conosce bene il prodotto: tutto il sistema, dal nodo unico fino alle schermate, ai gruppi di rotte, ai lavori a orario, ai dati e ai servizi esterni, con i flussi che li attraversano. È il bersaglio a cui Daodan deve arrivare, ed è la fixture con inventario indipendente che il «Confronto proposto per i flussi multilivello» chiede. La scrive un agente leggendo il progetto, senza eseguirlo e senza vedere artefatti di Daodan, con le istruzioni di [`reference-brief.md`](reference-brief.md). Vale come riferimento solo dopo la conferma del proprietario.

Ha i campi di `daodan/system-map/v1` (`system_map.py`) e in più:

| Campo | Dove | Significato |
| --- | --- | --- |
| `inside` | nodo | il nodo dentro cui questo si apre. Assente sul nodo dell'intero sistema e su ciò che sta fuori (attori, dispositivi, servizi esterni) |
| `what` | nodo | che cos'è, in una frase |
| `proof` | nodo | `[{"at": "percorso:riga", "has": "testo"}]`: una riga che lo prova e un testo che quella riga contiene |
| `routes` | nodo | le rotte che il nodo offre, `METODO /percorso` |
| `registry` | nodo esterno | l'id della sua voce in `daodan/data/service-registry.json`; un id che il registro non ha ancora è una nota del controllo, non un problema |
| `family` | nodo esterno che non è attore, dispositivo o filesystem | `provider` (fa funzionare il programma: il processore dei pagamenti) o `piattaforma di integrazione` (un sistema di altri a cui il programma si collega per scambiare dati: il portale da cui importa un annuncio) |
| `role` | come `family` | a che cosa serve al programma, in una frase breve: «processore dei pagamenti», «invio delle email», «fonte degli annunci» |
| `mode` | come `family` | in che modo il programma si collega, in una frase breve: «chiamate API e avvisi di ritorno», «importazione una tantum dalla pagina», «sincronizzazione nei due sensi», «protocollo di posta» |
| `has` | freccia | un testo che la riga di `cite` contiene |
| `entries`, `effects` | flusso | gli estremi, `{"node", "kind", "what"}`; `kind` di un ingresso è uno fra controllo dell'interfaccia, rotta, comando, messaggio, evento hardware, orario, cambio di un dato, avvio di un processo, evento del repository, evento del sistema operativo (gli ultimi quattro dal 20 novembre 2026) |
| `packages` | mappa | i moduli della toolchain, `{"path", "manifest", "kind"}` |
| `gaps` | mappa | ciò che l'agente non ha potuto stabilire, con la causa |

In testa: `case`, `root` (la cartella del progetto), `scope: "sistema"`, `made` (la data). Sono ammessi tre tipi di nodo in più (proposte del 19 novembre 2026, confermate dal proprietario per i riferimenti): `filesystem`, `applicazione` (un'app o un sito intero, che una persona apre e che contiene schermate e logica) e `lavoro a orario`. Fra i tipi di flusso è ammesso `devops` (proposta dello stesso giorno): un flusso che costruisce, impacchetta, rilascia o addestra a tempo di sviluppo. `tecnico` resta per la macchina del prodotto che gira: cache, sincronizzazione, registro degli errori. Dal 19 novembre anche la mappa v1 ha `inside`, e una mappa scritta prima resta valida: il confronto su quel campo conta dalle run successive.

`python reference.py check EXPECTED.json RADICE_DEL_PROGETTO` verifica campi, membri e citazioni aprendo i file del progetto, senza eseguire nulla (`test_reference.py`). Un riferimento con `problems` non vuoto non si usa.

I riferimenti dell'intero sistema dei progetti privati restano fuori da git (`.gitignore`); quelli dei progetti pubblici stanno in `../project-model/fixtures/real-<nome>/`.

## Confronto con i riferimenti dell'intero sistema

`python score.py system MAP.json EXPECTED-system.json FILES.txt` confronta una mappa con un riferimento: nodi ritrovati (in tutto, per profondità e per tipo), precisione, quota dei nodi proposti fatti di una sola cartella, tipo uguale, `inside` tenuto, flussi ritrovati (anche con i nodi alzati al loro avo di profondità 1), ingressi ed effetti, e in `reach` le parti di profondità 0 e 1 che la mappa tocca senza portarle: un nodo che nomina un file di una parte, un servizio di altri con il suo nome. Non contano i nomi.

### Soglie proposte, da confermare dal proprietario

Confermate dal proprietario il 26 novembre 2026.

Ogni misura almeno 0,85 volte l'accordo fra due mappatori che non si vedono: nodi ritrovati 66%, profondità 0 e 1 79%, precisione 64%, tipo uguale 81%, `inside` tenuto 78% con almeno 15 nodi per caso, flussi alla profondità 1 63%. Flussi, ingressi ed effetti alla loro grana (28%, 31%, 23%) si riportano senza soglia finché i flussi non sono confermati. Frecce rifiutate al massimo 20%; stabilità fra due ripetizioni almeno 80%; una run fermata dal budget conta come fallita. Finché il proprietario non conferma i flussi di un caso, la misura dei flussi che vale è quella alla profondità 1. Il tetto di costo per l'intero sistema, 2 USD, era scritto per Sonnet: con Opus 5.5, scelto dal proprietario, si riscrive dopo la prima run misurata.

Parametri da provare: modello (Opus 5.5 per partenza e gate; Sonnet 5.5 e Haiku 5.5 alla fine, per il costo; e sempre, come metro accanto a Claude, deciso dal proprietario il 20 novembre 2026, Qwen dal suo gateway LiteLLM: `--models qwen`, indirizzo e chiave nel secret Modal `daodan-gateway`, mai in un file), giri sui resti (0, 1, 3), `system_brief.LIMIT` (24.000, 48.000).

### Conferma del proprietario

Per ogni caso `results/system/<caso>-conferma.md` (fuori da git) elenca ciò che si conferma a mano: i nodi di profondità 0 e 1, i flussi e 20 foglie estratte con `random.Random(2026)`. Il resto regge su `reference.py check`. Un caso non confermato resta una bozza e i suoi numeri sono segnati così.

Gli archivi inviati a Modal portano solo codice e configurazione (`code_archive.py`): un nodo del riferimento fatto solo di dati, immagini o fogli non è nello snapshot e non si può ritrovare. Si conta a parte.

Un riferimento è legato a un commit del suo progetto (`commit`: un id, oppure cartella e id quando il caso sta su più repository): `reference.py check` legge i file di quel commit con git, non l'albero di lavoro, perché il progetto va avanti. `python reference.py pin EXPECTED.json RADICE [CARTELLA …]` lega un riferimento al commit di oggi, sposta le citazioni il cui testo ha cambiato riga e nomina quelle che non ritrova. L'archivio di una misura si fa sullo stesso commit: `python code_archive.py OUT.tar REPOSITORY@COMMIT`.

### Schede dei percorsi, prova a costo zero, 20 novembre 2026

Prova della proposta del piano (Task C4): la macchina mostra, il modello nomina. `python traces.py cards LINKS.json GLOB OUT.json` prende dai collegamenti già calcolati di un caso i simboli che chiamano e che nessuno chiama, nei file che corrispondono a `GLOB` (qui le pagine del meta-framework), e per ognuno scrive una scheda: ciò che raggiunge e che al più il 15% degli altri raggiunge, dal più vicino, con nome, file e riga della chiamata. `python traces.py ask CARDS.json OUT.json` dà una scheda per richiesta a un modello, con indirizzo e chiave dall'ambiente; `test_traces.py`.

**Il contratto in quattro punti, lo stesso giorno.** La prima prova chiedeva un nome a una lista piatta di funzioni: il modello indovinava dai nomi, e nulla lo provava. `traces.py` ora fa trovare, correggere e certificare (il suo docstring dice i quattro punti): archi tipizzati e numerati (`chiama`, l'evento, `HTTP metodo percorso`, `scrive`, `legge`), tenuti solo sui rami che arrivano a un effetto o a un punto dove i collegamenti si fermano; sotto quel punto il sorgente; un flusso è una catena contigua di numeri dall'ingresso a un effetto; `traces.py verify` rifiuta ciò che non regge sui collegamenti e sulle righe.

### Ingressi senza regole

Misura del piano (Task C4.1), prima di scrivere le reti: per tipo degli otto e per rete, quanti ingressi dei riferimenti la rete ritrova, quanti suoi candidati non sono ingressi e quali file nessun candidato raggiunge. `modal run benchmarks/system-map/modal_map.py::entries --tars CASO=ARCHIVIO[,CASO=ARCHIVIO]` scrive per caso, senza regole e dopo il passaggio del motore, `candidates.json` (i candidati di `daodan/core/entries.py` e le chiamate dei collegamenti) e `files.txt` in `results/system/entries/CASO/`; poi `python entries.py measure candidates.json expected/CASO-system.json files.txt` (`test_entries.py`). Un ingresso è ritrovato da una rete quando un suo candidato sta in un file del nodo dell'ingresso, con i membri espansi sui file dello snapshot come in `score.py system`; un ingresso il cui nodo non è interno o ha più di 12 file si conta a parte (`apart`); un candidato fuori dai file di ogni nodo d'ingresso non è un ingresso (`not_entries`); i file che nessun candidato contiene né raggiunge con le chiamate si contano per cartella (`unreached`). La prima rete è il residuo, «chiama e nessuno lo chiama».

### Lettore del framework (prova tolta)

Una prova del 20 novembre 2026: un programma a parte sul compilatore TypeScript, su un albero senza dipendenze. **Tolta lo stesso giorno per decisione del proprietario:** era un doppione scritto a mano di scip-typescript, lo strumento ufficiale che Daodan avvia già nel container dopo il ripristino delle dipendenze del progetto (`daodan/core/indexers/typescript.py`), e andava contro la regola di AGENTS.md sulle soluzioni pronte. Gli ingressi dell'interfaccia si leggono da ciò che quello strumento risolve.

## Esecuzione

| Misura | Comando |
| --- | --- |
| 1, 2, 4, 5 | `modal deploy benchmarks/system-map/modal_map.py`, poi `python benchmarks/system-map/modal_map.py spawn --tag TAG --cases CASO[,CASO] --tar CASO=ARCHIVIO … --rules session --scopes system --models opus --reps 2 [--budget USD]` (archivio da `python code_archive.py OUT.tar REPOSITORY[@COMMIT]`: codice e configurazione fra i file tracciati, mai dati né segreti, `test_code_archive.py`): per caso, perimetro e modello il passaggio del motore e una sessione `claude -p` con il compito `LINKS` dell'app scrivono le regole; la prima ripetizione le lascia sul volume con i collegamenti (`rules.json`, `links.json`) e avvia le altre su di esse; ogni ripetizione è una sessione nuova di `claude -p --agent codebase-map:system-mapper`. `--rules PERCORSO` con `--links CASO=PERCORSO` usa un file di regole e i collegamenti calcolati prima; `--rules none` lascia le regole all'agente. Sul volume `daodan-flow-results`, in `TAG/ETICHETTA`, restano `map.json`, `files.txt`, `stream.jsonl`, `rules-stream.jsonl` e `summary.json` (costo, token, arresto per budget); `modal volume get daodan-flow-results TAG/ETICHETTA benchmarks/system-map/results/system/TAG` li porta qui. Poi `python score.py system map.json expected/CASO-system.json files.txt` |
| 3 | `map.json` di ogni run riporta in `levels` i nodi fuori dal loro livello e i punti citati che non esistono, per ogni flusso registrato e ogni livello |
| 6, dimensione della scheda | `modal run benchmarks/system-map/modal_map.py::brief [--tar PATH --links-file PATH] [--cases polar,tududi]` scrive `results/brief-<caso>.json`; poi `python score.py externals results/brief-<caso>.json expected/externals-<caso>.json registry` (oppure `stack-analyser`, `both`) |
| Il container nella run (task 1 del piano dell'analisi unificata) | `modal run benchmarks/system-map/modal_map.py::engine_proof_run [--tag TAG] [--out PATH]`, prima dei cinque casi: sulla fixture `js-npm-single`, cinque controlli con la loro prova scritta in `results/engine-proof.json`. 1: `engine-report.json` dice scip-typescript `fresh` (la pass è un processo figlio, con il motore da `sitecustomize`). 2: un arco osservato del passo dinamico è nell'archivio `engine-edges.sqlite`, su `src/index.js`. 3: la preparazione raggiunge `pypi.org` e rifiuta un host fuori dai registri, un indirizzo HTTP semplice e un indirizzo IP. 4: una sandbox non vede `/results` né i risultati di un altro caso, e non scrive nella sua cartella. 5: dopo una preparazione fallita e una sandbox che non parte non resta nulla sul volume né in esecuzione. Richiede il client Modal 1.5.0 o successivo (`outbound_domain_allowlist`, `Volume.with_mount_options`). *Eseguita il 23 novembre 2026 su Modal (client 1.5.5), `results/engine-proof.json`. Primo giro: 3 controlli su 5; scip-typescript e l'arco osservato mancavano perché il processo figlio della pass non trovava `grpclib` (il client Modal sta in `/pkg`, le sue dipendenze altrove): `engine_environment` ora mette sul percorso le cartelle da cui il padre le importa. Secondo giro: 5 su 5. scip-typescript `fresh` su JavaScript; 6 archi osservati nell'archivio, uno in `src/index.js` (`lodash.head`); la preparazione raggiunge `pypi.org` e rifiuta un host fuori dai registri, HTTP semplice e un indirizzo IP; la sandbox non ha `/results` e non scrive nella sua cartella; dopo una preparazione fallita e un'immagine che non parte non resta nulla sul volume né in esecuzione. Non misurati: tempo e costo del giro.* |
| Intera analisi (task 2 del piano dell'analisi unificata) | `python benchmarks/system-map/code_archive.py OUT.tar REPOSITORY@COMMIT` (scrive anche `OUT.json`, i conteggi), `modal deploy benchmarks/system-map/modal_map.py`, poi `python benchmarks/system-map/modal_map.py whole --tag TAG --cases CASO --tar CASO=OUT.tar [--models qwen,haiku,opus] [--reps 2]`: un job per caso (`whole_case`: archivio, pass del motore con i container su Modal Sandbox, candidati) e, con `--models`, una `map_run` indipendente per caso, modello e ripetizione (ognuna prepara per sé e scrive le sue regole). Senza `--models` girano solo i casi, senza modello. Poi `modal volume get daodan-flow-results TAG benchmarks/system-map/results/system/TAG` e `python benchmarks/system-map/score.py whole benchmarks/system-map/results/system/TAG`: una tabella per caso, una riga per modello, una colonna che manca dice «non misurato» con la causa. *Scritto il 23 novembre 2026 e non eseguito; il formato dei file per caso è provvisorio fino al primo giro. Mancano le schede dei percorsi con il modello (`paths.json`) e la ricerca (`search.json`), che dipendono dai task 9 e 10.* |
| Tre corse sullo stesso progetto (task 2b) | `python benchmarks/system-map/score.py runs DA-ZERO SENZA-MODIFICHE UN-MODULO`, su tre cartelle con `pipeline-events.jsonl`, i `container-runs.jsonl` e `links.json` (`found`, `of`, di `possible.py`): tempo, ripristini, avvii degli indicizzatori e dell'app, collegamenti ritrovati; una corsa che costa meno e ritrova meno collegamenti è segnata, non contata come un guadagno. CPU, picco di RAM e spazio temporaneo non sono in nessun evento: «non misurato», finché la pipeline non li scrive. *Scritto il 23 novembre 2026 con uscite sintetiche; la misura su Modal aspetta il via del proprietario.* |
| Collegamenti possibili | sullo snapshot di un caso con il motore: `python daodan/core/flows.py links MANIFEST --rules RULES > LINKS.json`, poi `python benchmarks/system-map/possible.py MANIFEST LINKS.json EXPECTED-system.json --generators ritorno,incerto` (`--generators ""` per i soli collegamenti certi) |
| Ingressi senza regole | `modal run benchmarks/system-map/modal_map.py::entries --tars CASO=ARCHIVIO[,CASO=ARCHIVIO]`, poi `python entries.py measure results/system/entries/CASO/candidates.json expected/CASO-system.json results/system/entries/CASO/files.txt` |

## Risultati

### Gruppi candidati, 12 novembre 2026, prima di fissare la regola

Con una soglia sulla quota dei punti d'ingresso (20%) la fixture `flow-model` non forma nessun gruppo, perché due su sei sono già il 33%. Con un gruppo per risorsa dà i due gruppi attesi (`store:db/payments` con quattro punti d'ingresso, `module:card payment provider` con tre).

### Costruzione del registro, 12 novembre 2026

2.172 voci da stack-analyser 1.27.6 (743 regole), CNCF Landscape (commit `75b47639`, senza le categorie dei membri e dei fornitori certificati) e Simple Icons 16.37.0 (marchi agganciati per nome). `derive`, senza modello, trova pacchetti su PyPI, crates.io o nel proxy di Go per 102 delle 455 voci con un pacchetto npm; tiene un pacchetto solo se il repository ha lo stesso proprietario del pacchetto npm principale, un modulo Go solo se il suo `go.mod` è vero, e scarta i pacchetti trovati per più voci. Una run di Haiku 5.5 (0,023 USD, 40.257 token in uscita) propone il resto: la macchina ne tiene 141, fra cui FastAPI, Flask e Pydantic, e ne rifiuta 22 oltre a quelle già coperte, compresi pacchetti veri con un altro proprietario (`boto3`, `prometheus-client`, il driver Go di MongoDB).

### Misura 6 e dimensione della scheda, 12 novembre 2026

Su Modal, senza modello, uno snapshot per caso: polar (`server/`) e tududi ai commit dei loro benchmark, senza regole. Richiamo sull'elenco scritto prima; sbagliati sono i riconoscimenti fuori da `externals` e da `also`, ognuno letto al punto citato.

| Caso | Attesi | Registro | stack-analyser | Insieme | Falsi letti al punto citato |
| --- | --- | --- | --- | --- | --- |
| polar | 25 | 60,0% | 32,0% | 60,0% | 0 |
| tududi | 14 | 78,6% | 78,6% | 78,6% | 3: `zoom` da un tipo TypeScript, `caddy` e `kubernetes` dagli esempi in `docs/examples` |

Nessun caso raggiunge la soglia del richiamo; tududi supera anche quella dei falsi. stack-analyser non riconosce nulla che il registro non veda già. Cause:

- Mancano dal registro: Zustand, Motor, Dramatiq, Logfire, Numeral, Plain, IPinfo.
- Il registro ha la voce ma non il segno che il progetto mostra: AWS (`boto3` riconosce solo il progetto Boto3), GitHub (`githubkit`), Expo (`exponent-server-sdk`), MinIO e Tailscale (immagini `bitnamilegacy/minio`, `tailscale/tailscale`), Cloud Run (solo un commento del Dockerfile e `.gcloudignore`), Cloudflare in tududi (`TURNSTILE_*`), Google Calendar (`GOOGLE_CLIENT_ID`, un prefisso troppo generico).
- L'elenco letto dai soli manifest non vede i servizi chiamati via HTTP e configurati con variabili: in polar il registro trova Discord, Linear, Slack, Resend e OpenAI, in tududi Discord, tutti veri al punto citato.
- Gli esempi di documentazione contano come configurazione del progetto.

Corretto durante la misura: con un target dentro il repository (polar `server/`) stack-analyser legge i percorsi dal target e lo snapshot dalla radice, così ogni riconoscimento cadeva; il richiamo di stack-analyser su polar passa da 0 a 32%.

Dimensione del testo della scheda, in caratteri; fra parentesi i gruppi riassunti in una riga:

| `CAP` \ `HOLDERS` | 5 | 8 | 12 |
| --- | --- | --- | --- |
| polar, tududi, ogni valore | 5.465 e 5.442 | | |

polar e tududi senza regole non hanno gruppi.

### Misure da 1 a 5, prima tornata, 12 novembre 2026

8 run su Modal (tag `system-map-runs`), una sessione nuova ciascuna di `claude -p --agent codebase-map:system-mapper`: tududi, area «pagamenti e abbonamenti» e intero sistema, Haiku 5.5 e Sonnet 5.5, due ripetizioni. Tetto della scheda 48.000, `HOLDERS` 8. Costo 0,38 USD. Valori per run in `results/runs-20261112.json`.

| Misura | Risultato | Soglia |
| --- | --- | --- |
| 2 Secondo progetto, tududi | nessuna mappa registrata in otto run | non misurabile |
| 4 Costo | area: Haiku 0,007 e 0,011 USD, Sonnet 0,085 e 0,068; intero sistema: Haiku 0,002 e 0,010, Sonnet 0,15 e 0,047; aperture del sorgente da 0 a 2; nessuna mappa registrata | — |
| 5 Stabilità | nessuna mappa registrata | non misurabile |

Cause:

- **tududi:** la risposta di `brief` è di 51,9 KB e supera il limite dell'host per l'uscita di uno strumento: l'host la salva in un file e l'agente, che ha solo i quattro strumenti della mappa, non la legge. Il rapporto di `map` è di 86.648 caratteri, soprattutto per gli elenchi di ciò che la copertura lascia fuori (831 punti d'ingresso). In più `codebase_map_read` rifiuta con «parser fingerprint changed»: probabilmente il run è preparato con le versioni di tree-sitter dell'immagine e il server gira in un ambiente `uv` con altre versioni.
Dopo questa tornata il tetto della scheda torna a 24.000 caratteri, perché la risposta di `brief` resti sotto il limite dell'host. Il modello dell'agente non è fissato.

### Misure da 1 a 5, seconda tornata, 12 novembre 2026

Corretti i tre blocchi della prima tornata: il rapporto di `map` conta per cartella ciò che la copertura lascia fuori quando l'elenco supera 40 voci, il run si prepara con l'ambiente del server MCP, ogni run ha un container suo. Tetto della scheda 24.000, `HOLDERS` 8. Le stesse 8 run (tag `system-map-runs2`), tutte partite, 0,76 USD. Nessuna risposta degli strumenti supera il limite dell'host. Valori per run in `results/runs2-20261112.json`.

| Misura | Risultato | Soglia |
| --- | --- | --- |
| 2 Secondo progetto, tududi | frecce provate o dichiarate 57 su 60 (95%), solo 4 provate; nomi letti a mano 8 su 10 (vedi sotto) | raggiunta |
| 3 Livelli | fino a 50 viste per run: nessun nodo fuori dal suo livello, nessun punto citato che manca | raggiunta |
| 4 Costo | area: Haiku 0,010 e 0,009 USD, Sonnet 0,20 e 0,11; intero sistema: Haiku 0,013 e 0,014, Sonnet 0,26 e 0,13; aperture del sorgente da 0 a 2 | raggiunta |
| 5 Stabilità | nodi uguali fra le due ripetizioni: al più 55%, intero sistema, Haiku (6 su 11) | non raggiunta |

Nomi letti a mano (tududi, area, Sonnet, prima ripetizione, e due nodi dell'intero sistema): giusti API abbonamenti, Gestione abbonamenti, Pagina admin fatturazione, Provider di pagamento, Scheda Abbonamento, Utente, Assistente MCP, Piano del giorno; sbagliati Client abbonamenti (il nome del codice, non della cosa) e Gateway di pagamento (un nodo solo per Stripe, Paddle e Lemon Squeezy, che il registro riconosce uno per uno).

Cause di ciò che non raggiunge la soglia:

- **La correzione toglie ciò che era stato accettato.** Una proposta con `scope` toglie i flussi non confermati dell'area che non riporta; l'agente corregge mandando solo ciò che è stato rifiutato, e così perde i flussi accettati e i loro nodi. Il rapporto della correzione toglie da 3 a 5 nodi e flussi in 2 run su 4 dell'area. È la causa principale della misura 5, e la regola di `system-map.md` («Correct what was refused once») non la previene.
- **L'intero sistema in una proposta** dà da 11 a 18 nodi per tutto il prodotto, spesso un file per nodo.

Dopo questa tornata una proposta non toglie più ciò che non nomina, e una freccia verso un membro indicato come funzione si prova anche sul file, dichiarandosi meno precisa.

Il modello dell'agente non è fissato: Haiku e Sonnet stanno entrambi sotto la misura 5.

### Candidati prima delle regole e osservazioni registrate, 21 novembre 2026

Eseguire `python benchmarks/system-map/path_observations.py`. Prima delle regole, CLI, MCP e strumento dell’app trovano il candidato AST `@trigger("refresh")` con gestore `controls.py::dispatch`. Classificata la forma come comando, la scheda letta da CLI, MCP e HTTP espone l’osservazione esatta di `save` a riga 3, il campione di `also_save` a riga 4 e il conflitto tra la destinazione statica `refund` e quella osservata `cancel` a riga 5. Tre regole associano una scrittura al rispettivo chiamato. CLI, MCP e strumento dell’app accettano `store:db/payments` e rifiutano sia `store:db/orders` (campione) sia `store:db/refunds` (conflitto). Alla riapertura, l’area contiene il solo pagamento, ancora `verified`. Le righe dell’indice e le osservazioni sono sintetiche. La verifica usa il join e l’archivio SQLite di Daodan, con lo scanner simulato.

### Scheda «Paga», riapertura e seconda corsa, 21 novembre 2026

Dalla radice, eseguire `python benchmarks/system-map/path_reuse.py` con le dipendenze di Daodan. Il benchmark prepara uno snapshot SQLite della fixture `flow-model`, registra le sue undici regole e consulta prima l’elenco, poi la scheda del pulsante «Paga». La CLI verifica anche il rifiuto di una decisione discontinua (uscita 1) e la riapertura per nome. La lista e i conteggi delle scritture senza un ingresso provato coincidono su CLI, MCP e HTTP. La CLI, il client MCP con trasporto in memoria, la rotta HTTP dell’app e lo strumento dell’app restituiscono gli stessi passi. Il test usa uno scanner che restituisce zero segreti e tiene spento il container. Nessun sorgente della fixture viene eseguito.

Il percorso registrato segue `onPayClick → submitPayment → store:web state/payment`. La sola scrittura, presentata come passo iniziale dal controllo, viene rifiutata per discontinuità. Il cambio del tema, pur usando lo stesso store, resta fuori dalla scheda. Un nuovo servizio riapre la mappa e ritrova gli estremi verificati, il sito e la provenienza di ogni passo.

| Operazione sullo snapshot già scritto | Aperture sorgenti | Parse tree-sitter | Inventari AST / costruzioni link | Inventari schede / espansioni | Connessioni manifest / cache schede |
| --- | ---: | ---: | ---: | ---: | ---: |
| Registrare le regole | 23 | 23 | 1 / 1 | 0 / 0 | 8 / 0 |
| Aprire elenco e scheda | 0 | 0 | 0 / 0 | 1 / 1 | 8 / 3 |
| Ripetere elenco e scheda con un nuovo servizio | 0 | 0 | 0 / 0 | 0 / 0 | 10 / 5 |
| Riaprire il flusso per nome | 0 | 0 | 0 / 0 | 0 / 0 | 6 / 1 |

La prima consultazione prepara un unico indice del grafo. Il [test di costo](../../tests/test_flow_path_identity.py) conta 256 visite per indicizzare 256 percorsi indipendenti e 512 visite per 512 percorsi, ciascuno con un solo arco. Aprire i dettagli richiede poi i soli archi raggiunti. La seconda lettura di elenco e scheda apre due volte `flow-links.json` e una volta `system-map.json`. La lettura del flusso per nome li apre una volta ciascuno. Le quattro operazioni hanno richiesto zero elenchi di directory sorgenti, nuovi snapshot, avvii degli indicizzatori, comandi nel container, gestori di pacchetti o download di strumenti. I numeri valgono per questa fixture con grammatiche di Daodan già disponibili. La misura esclude la creazione iniziale dello snapshot e il costo di una vera analisi dinamica.

La scheda globale ha una prova separata in `tests/test_codebase_map_system_brief.py::DeclaredTests::test_global_brief_reopens_only_changed_unmodelled_yaml`. La fixture contiene Dockerfile, Compose, package.json e due manifesti YAML. Prima della modifica, prima e seconda consultazione aprivano quattro sorgenti ciascuna. Ora la scheda riprende le immagini Docker, i servizi Compose e le dipendenze dalla pre-mappa. Apre i soli manifesti Kubernetes e Backstage alla prima consultazione (2 aperture) e nessun sorgente alla seconda, anche riaprendo il servizio. Cambiando il catalogo alla terza lettura, la verifica riapre un solo file e scarta la dichiarazione che diverge dallo snapshot.

### Due analisi complete con il container acceso, 21 novembre 2026

Eseguire `python benchmarks/system-map/pipeline_reuse.py --container`: la stessa fixture `js-npm-single` e lo stesso manifest, due processi, con il motore di container della macchina (qui quello di Daodan su Windows). Ripristino, scip-typescript e `node --test` girano davvero.

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

Nella seconda analisi resta una lettura per ognuno dei quattro file, per confrontare lo snapshot con il disco, e un comando git. Le letture interne dei programmi nel container non sono contate. La misura non separa i ripristini: il registro dei container dell'indicizzatore sta in una cartella temporanea.

### Tre percorsi con gli indicizzatori veri, 21 novembre 2026

Eseguire `python benchmarks/system-map/real_paths.py [web] [tk] [tauri] [--work DIR]` con le dipendenze di Daodan e un motore di container (su Windows quello di Daodan). Parametri: il caso (`benchmarks/flow-model/app`, `real-paths/tk-desk`, `real-paths/tauri-desk`), le regole e le risposte sulle forme del caso, la disposizione (analisi accanto al checkout). Lo script crea il run dal servizio con il passaggio del motore, legge i candidati prima delle regole, registra regole e risposte, apre ogni scheda e controlla ciò che deve reggere; esce con 1 se un controllo cade.

| Caso | Indicizzatori nel container | Secondi | Controllo, gestore, ultimo punto provato |
| --- | --- | ---: | --- |
| web | scip-python 0.6.8, scip-typescript 0.6.2 | 129 | «Paga» `web/checkout.ts:22` → `onPayClick` → `submitPayment` → `store:web state/payment` (`web/checkout.ts:14`) |
| tk | scip-python 0.6.8 | 106 | «Salva» `ui.py:8` → `App.save` (gestore dato dall'indice) → `store:disk/orders` (`ui.py:11`) |
| tauri | scip-typescript 0.6.2, rust-analyzer 2026-11-09 | 322 | «Salva profilo» `src/view.tsx:18` → `save` → `src-tauri/src/main.rs::persist` (`tauri-invoke`, `src/view.tsx:4`); `only_in_tests` e `on_idle_builder` restano lacune |

Il caso Tauri prima falliva: con il ripristino Node condiviso `tsc` e scip-typescript non trovavano `node.tar.gz` (spec della pipeline, sezione 7.1). Con 6,4 GB liberi rust-analyzer non parte (ne chiede 8) ed è una lacuna con la causa. Le stesse tre fixture su Modal (`modal_pipeline.py --folder-out`): indici `fresh` in 132, 100 e 242 secondi; lì i test Rust non partono per le librerie di sistema che mancano. Le fixture non dichiarano test: nessun arco osservato.

### Le rotte di Next.js dallo strumento del framework, 21 novembre 2026

Eseguire `python benchmarks/system-map/real_paths.py next [--work DIR]` con un motore di container. Parametri: la fixture `real-paths/next-shop` (Next.js 16.4.6, App Router: tre pagine, un gestore `POST`, un layout, un pulsante «Paga» in un form la cui `action` è una funzione `"use server"`), nessuna regola, una risposta sulla forma `action` (il registro non la conosce). La sorgente della pre-mappa lancia `next typegen` del progetto nel container e legge `.next/types/validator.ts`; i collegamenti danno a ogni file la sua funzione dagli export dello snapshot.

| Controllo | Container locale | Modal (`modal_pipeline.py --folder-out`) |
| --- | --- | --- |
| secondi dell'analisi | 169 | 145 |
| `/checkout` è un ingresso sulla funzione della pagina (`app/checkout/page.tsx::Checkout`, riga 3) | sì | sì |
| `/api/pay` è una sola voce, su `app/api/pay/route.ts::POST` | sì | sì |
| nessun ingresso è la rotta `/pay` | sì | sì |
| la scheda «Paga» arriva a `app/checkout/actions.ts::pay` | sì | non misurato: il giro su Modal non apre le schede |

Prima della sorgente le tre pagine non erano ingressi, e Noir dava la funzione sul server come una rotta `/pay` che l'app non ha. `next typegen` da solo, nel container senza rete: 0,9 secondi, exit 0; `next build` 7,9 secondi. Non provati: il Pages Router, un `distDir` diverso, una versione senza `typegen` (la fixture `js-nextjs`, Next.js 14, dà la lacuna `model_failed`).

### Collegamenti possibili, senza modello

Domanda: delle frecce e degli ingressi che mancano ai flussi di un riferimento, quanti darebbe un collegamento possibile, che la macchina propone senza affermarlo e un modello conferma o scarta. `possible.py` verifica le frecce fra nodi con codice con `system_map.verify`, prima con i soli collegamenti certi e poi aggiungendo i possibili; le frecce e gli ingressi su un servizio di altri li controlla nella loro direzione e sui simboli di ogni nodo (il ritorno di un webhook va dal modulo esterno al gestore, non il contrario). Generatori: `ritorno` (una rotta di una regola `offre` che nessuna chiamata del progetto raggiunge, nemmeno come candidata, in un file che usa un modulo esterno, è chiamata da quel modulo; le rotte trovate da un lettore come Noir non hanno un'offerta a cui unire le chiamate e sono contate a parte) e `incerto` (una chiamata con più rotte candidate va a ognuna). I conteggi per freccia e per ingresso sono elencati nel docstring di `possible.py`. Il contesto React e la chiave in una variabile non hanno un generatore: cadono in `mancante con lacuna` o `mancante`. Un collegamento possibile che non sta su nessuna freccia o ingresso del riferimento è contato in `outside_reference`, non come sbagliato. Prova del metodo: `test_possible.py`, sulla fixture `flow-model` con un webhook. Va misurato sui casi con riferimento.

## Confronto proposto per i flussi multilivello

Protocollo per la [spec del 18 novembre](../../docs/specs/2026-11-18-flussi-e-mappa-del-sistema.md). **Confronto proposto, ancora da eseguire su Modal.**

**Scoperta cieca.** Ogni variante riceve la stessa richiesta, «analizza questo sistema», e lo stesso snapshot completo. Il mapper vede i normali artefatti dell'analisi, inclusi i nomi presenti nel prodotto. Prompt, regole e card accessibili al mapper devono essere privi di etichette provenienti dal valutatore o da mappe di flussi già compilate per la prova. I riferimenti manuali, le aree attese, i nomi e il numero di processi e rami rimangono fuori dall'ambiente dell'agente. Il valutatore li confronta con la mappa salvata **prima** di formulare richieste di review.

| Variante | Compito |
| --- | --- |
| A, attuale | Eseguire il mapper attuale sull'intero sistema. |
| B, grafo | Partire da ingressi ed effetti dell'intero inventario. Il modello identifica processi e varianti. La macchina verifica i percorsi. |
| C, grafo e card | Come B, aggiungendo l'accesso mirato alle card di simbolo aggiornate. B e C possono richiedere gli stessi estratti di sorgente. |

**Casi.** Un riferimento d'area si valuta dopo la scoperta sui soli flussi che copre; gli altri flussi scoperti vanno giudicati a parte prima di contarli come errati. Per misurare la scoperta di un intero sistema, predisporre in repository una fixture con inventario manuale indipendente ed esaustivo. Deve comprendere più funzionalità, una funzionalità con ramo utente e cron, un modulo condiviso con un altro processo e un effetto il cui ingresso resta irrisolto.

**Parametri e misure.** Fare due ripetizioni indipendenti per variante e caso, a parità di grafo, modello, tetto di contesto e budget. Registrare flussi e varianti mancanti, estranei, accorpati o duplicati, verificandoli per ingressi, effetti e membri anche quando il nome differisce. Contare gli estremi spiegati, esclusi con motivo, irrisolti e non esaminati. Misurare token osservati di input e output, aperture e costo dell'intero run, distinguendo riuso e prima generazione delle card. Valgono le soglie storiche applicabili per riproduzione sull'area di riferimento, stabilità e costo a sistema. Un riferimento parziale non misura il richiamo globale.

**Criteri sulla fixture completa.** Il mapper deve scoprire tutti i processi e tutte le varianti attesi, conservare il modulo condiviso una sola volta e rendere conto di ogni estremo, inclusa l'origine irrisolta. Nessun arco causale senza evidenza. Aprire il processo deve mostrare i due rami e richiuderlo deve ripristinare la selezione, con zero chiamate LLM. Solo a questo punto chiedere una review della funzionalità e poi del solo ramo automatico. Nel primo caso sono attesi entrambi i percorsi, nel secondo il gestore del cron e il codice condiviso pertinente. In entrambi i casi verificare la motivazione dei file, i file di solo contesto e le lacune rispetto al riferimento.

A qualità uguale si preferisce il minor consumo totale osservato. Se il grafo non espone un ingresso o un effetto, attribuire l'omissione alla raccolta delle evidenze. Se il riferimento è visibile al modello e viene interpretato male, attribuirla alla scoperta semantica. **Risultati del nuovo protocollo e fixture completa: da produrre.**

### Due analisi complete sullo stesso snapshot JavaScript, 21 novembre 2026

Eseguire `python benchmarks/system-map/pipeline_reuse.py`. Lo script crea una volta il manifest SQLite della fixture `js-npm-single`, poi avvia due processi distinti che chiamano `pipeline.run` senza saltare passi. La fixture dichiara pacchetti npm e il comando `node --test`. Ogni corsa imposta `DAODAN_CONTAINER=off`. Le grammatiche e l’ambiente uv di Daodan erano già disponibili.

| Passo o misura | Prima analisi | Seconda analisi |
| --- | ---: | ---: |
| Scan eseguito / pre-mappe derivate | 1 / 1 | 1 / 0 |
| Grafo dei moduli | ricostruito | riusato |
| Sorgenti di pre-mappa con lacuna del container | 4 | 4 |
| Stack eseguito / tecnologie restituite | 1 / 2 | 1 / 2 |
| Analyze / tentativi dell’adattatore SCIP | 1 / 1 | 1 / 1 |
| Dynamic / osservazioni runtime | 1 / 0 | 1 / 0 |
| Union eseguito | 1 | 1 |
| Aperture di file del progetto da Python | 14 | 4 |
| Elenchi di directory del progetto da Python | 9 | 0 |
| Processi Git / uv offline | 5 / 2 | 1 / 2 |
| Verifiche della disponibilità del container | 2 | 1 |
| Copie nel container / comandi npm / download di Daodan | 0 / 0 / 0 | 0 / 0 / 0 |
| Nuovi snapshot / parse tree-sitter | 0 / 0 | 0 / 0 |

La seconda analisi riapre una volta ciascuno `package.json`, `package-lock.json`, `src/index.js` e `test/index.test.js`. Nella prima le aperture sono rispettivamente 7, 3, 2 e 2. Gli hook di audit coprono i tre interpreti Python di ogni corsa. Contano anche gli avvii di Git e uv. Le letture interne ai binari nativi non sono misurate.

La prima corsa tenta go-enry, Renovate, npm e Noir. La seconda riapre le quattro lacune con la loro causa. Prima di questa modifica la seconda corsa rigenerava una pre-mappa, apriva sei file del progetto, elencava tre directory e verificava due volte la disponibilità del container. Il riuso vale quando lo snapshot e le sorgenti sono gli stessi, il runner è quello del container predefinito e Daodan ha già registrato lo stesso spegnimento esplicito per tutte le sorgenti rimaste da eseguire. Una richiesta di rigenerazione, un runner diverso, una causa diversa e la riattivazione del container consentono il nuovo tentativo.

SCIP si ferma prima della build con stato `unavailable`. Dynamic riporta `no-static-graph` e Union conserva lo stato `unavailable` per JavaScript. I due avvii di uv verificano e aprono l’ambiente offline dell’adattatore. Nessun processo ha installato i pacchetti del progetto o eseguito i suoi test. Resta da misurare una seconda analisi con container disponibile e un indice ufficiale prodotto realmente.
