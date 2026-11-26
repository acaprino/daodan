# Benchmark: mappa del sistema

Prova la [spec della mappa del sistema](../../docs/specs/2026-11-18-flussi-e-mappa-del-sistema.md), misure da 1 a 6. Le soglie sono scritte qui prima di ogni misura; il proprietario può cambiarle. I casi sono quelli dei benchmark dei flussi: [`phazly-flow`](../phazly-flow/README.md), [`polar-flow`](../polar-flow/README.md) e [`tududi-flow`](../tududi-flow/README.md). Le regole di collegamento ci sono per phazly e per tududi (`benchmarks/tududi-flow/rules.json`, scritte a mano il 12 novembre 2026 per la misura 2: store di Zustand, chiamate `fetch(getApiPath(...))`, rotte di Express, modelli di Sequelize). Il codice dei casi non entra qui: solo nomi di file e valori attesi. Le run girano su Modal, in un processo nuovo.

## Soglie

| Misura | Cosa si conta | Soglia |
| --- | --- | --- |
| 1 Riproduzione | su phazly, area «pagamenti e abbonamenti»: nodi del riferimento ritrovati, confrontati per file (indice di Jaccard almeno 0,5); flussi ritrovati (due terzi dei nodi); frecce rifiutate dopo la correzione | almeno 8 nodi su 11 e 3 flussi su 3; frecce rifiutate al massimo il 20% |
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

- `expected/phazly-payments.json`: gli 11 nodi e i 3 flussi (pagamento, gestione abbonamento, paywall e limiti d'uso) del grafo d'insieme della mappa fatta a mano il 12 novembre 2026, confermati dal proprietario lo stesso giorno; i 35 percorsi sono letti dall'archivio di phazly. Il pagamento dal web e il suo ritorno (`SubscriptionContext.tsx`, `CheckoutVerificationOverlay.tsx`, `checkout-complete/index.html`) stanno nel Paywall, gli avvisi di prova e scadenza nella Scheda abbonamento; Abbonamento e Consumi sono le chiavi `mongo/subscriptions` e `mongo/usageEvents`; la Landing è un nodo non visto. Un nodo con codice si ritrova per file e chiavi di store, un nodo senza codice se un nodo nella stessa posizione cita uno dei suoi file, un nodo non visto per posizione e tipo.
- `expected/externals-<caso>.json`: per ogni caso l'elenco a mano letto dai manifest, dai Dockerfile, dai file compose e dai modelli di `.env` del perimetro dello snapshot (`read`). In `externals` stanno ogni servizio esterno che quei file nominano e i progetti con un ruolo nell'architettura (framework dell'applicazione, guscio dell'app, accesso ai dati, stato, code, container), come la mappa fatta a mano di phazly ne nomina 6 su 59 pacchetti. In `also` stanno le cose usate che una persona non nomina (linguaggi, strumenti di build, stile, test e lint, librerie di utilità): non contano per il richiamo né come errore. Un identificatore che il registro non ha è scritto come nome semplice (`zustand`, `google-play-billing`).

- `expected/real/<caso>-system.json` ed `expected/real/<caso>-graph.json` (nella cartella `real` perché pubblici: `.gitignore` tiene fuori da git i `expected/*-system.json` dei progetti privati), per cinque progetti pubblici di complessità crescente (`expected/real/sources.json`: repository, commit, licenza, perché): `auth0-go`, `sveltekit-realworld`, `microblog`, `next-subscriptions`, `bank-of-anthos`. Scritti a mano il 25 novembre 2026 leggendo il codice a quel commit, senza eseguirlo: sono ciò che Daodan dovrebbe dare a refactoring finito, non una sua uscita, e nessuna misura è ancora stata fatta contro di loro. La mappa di sistema segue `reference-brief.md` e passa `python reference.py check expected/real/<caso>-system.json CHECKOUT` senza problemi. Il grafo (`daodan/real-graph-expected/v1`) è ciò che gli otto step danno sotto la mappa: moduli e tecnologie, ingressi (rotte, pagine, azioni), rotte unite ai loro chiamanti per metodo e percorso, chiamate ai servizi esterni, store con chi scrive e chi legge, configurazione e lacune; lo controlla `python real_references.py <caso> CHECKOUT` (percorsi, simboli e righe citati), e `test_real_references.py` ne tiene la forma. Oltre ai campi comuni ogni grafo aggiunge quelli che il suo framework chiede (azioni di form, server action, hook, webhook, lavori): non sono ancora un contratto.

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
| `entries`, `effects` | flusso | gli estremi, `{"node", "kind", "what"}`; `kind` di un ingresso è uno fra controllo dell'interfaccia, rotta, comando, messaggio, evento hardware, orario, cambio di un dato, avvio di un processo, evento del repository, evento del sistema operativo (gli ultimi quattro dal 20 novembre 2026: nei riferimenti scritti prima, 18 avvii stanno sotto altri tipi e 8 avvisi di ritorno su 9 sotto «messaggio» invece che «rotta») |
| `packages` | mappa | i moduli della toolchain, `{"path", "manifest", "kind"}` |
| `gaps` | mappa | ciò che l'agente non ha potuto stabilire, con la causa |

In testa: `case`, `root` (la cartella del progetto), `scope: "sistema"`, `made` (la data). Sono ammessi tre tipi di nodo in più (proposte del 19 novembre 2026, confermate dal proprietario per i riferimenti): `filesystem`, `applicazione` (un'app o un sito intero, che una persona apre e che contiene schermate e logica) e `lavoro a orario`. Fra i tipi di flusso è ammesso `devops` (proposta dello stesso giorno): un flusso che costruisce, impacchetta, rilascia o addestra a tempo di sviluppo. `tecnico` resta per la macchina del prodotto che gira: cache, sincronizzazione, registro degli errori. Dal 19 novembre anche la mappa v1 ha `inside`, e una mappa scritta prima resta valida: il confronto su quel campo conta dalle run successive.

`python reference.py check EXPECTED.json RADICE_DEL_PROGETTO` verifica campi, membri e citazioni aprendo i file del progetto, senza eseguire nulla (`test_reference.py`). Un riferimento con `problems` non vuoto non si usa.

Bozze del 19 novembre 2026, scritte da un agente per progetto (Opus 5.5) e passate dal controllo senza problemi. Il proprietario ha confermato le regole (i tre tipi di nodo, `devops`, il database al primo livello con le sue entità, community ed enterprise affiancati in Qamille); i nodi e i flussi di ogni caso restano da confermare.

| Caso | Radice | Nodi | Flussi | Frecce | Lacune dichiarate |
| --- | --- | --- | --- | --- | --- |
| `phazly-system.json` | `phazly` | 130 | 38 | 240 | 20 |
| `hostay-system.json` | `hostay` | 109 | 35 | 187 | 18 |
| `qamille-enterprise-system.json` | la cartella che contiene `qamille-mail` (il nucleo community) e `qamille` (la parte enterprise) | 142 | 39 | 245 | 16 |
| `qamille-system.json` | `qamille-mail`, la versione community | 106 | 29 | 169 | 15 |
| `poc-data-extraction-system.json` | `poc-data-extraction` | 62 | 19 | 105 | 14 |

Il riferimento di phazly tiene i nomi, i tipi e i file degli 11 nodi e i 3 flussi di `phazly-payments.json`, con una differenza, confermata dal proprietario: «Landing · prezzi» è interno, perché `landing-app` sta nella radice. Qamille enterprise usa `qamille-mail` come nucleo e ha il resto in un secondo repository: i suoi percorsi cominciano con il nome del repository, e al primo livello i nodi del nucleo portano «(community)» nel nome.

## Confronto con i riferimenti dell'intero sistema

`python score.py system MAP.json EXPECTED-system.json FILES.txt` confronta una mappa con un riferimento: nodi ritrovati (in tutto, per profondità e per tipo), precisione, quota dei nodi proposti fatti di una sola cartella, tipo uguale, `inside` tenuto, flussi ritrovati (anche con i nodi alzati al loro avo di profondità 1), ingressi ed effetti, e in `reach` le parti di profondità 0 e 1 che la mappa tocca senza portarle: un nodo che nomina un file di una parte, un servizio di altri con il suo nome. Non contano i nomi. Una proposta che rispecchia l'albero delle cartelle ha precisione fra 7% e 23% sui cinque casi e non ritrova nessun flusso (`tests/test_benchmark_system_map_score.py`).

### Il tetto: l'accordo fra due mappatori (19 novembre 2026)

Due riferimenti dello stesso caso, il più piccolo (62 nodi ciascuno), scritti da due agenti che non si vedono, confrontati nei due versi:

| Misura | Primo verso | Secondo verso | Accordo |
| --- | --- | --- | --- |
| Nodi ritrovati | 40 su 49 | 41 su 56 | 77% |
| Nodi a profondità 0 e 1 | 12 su 12 | 12 su 14 | 93% |
| Precisione | 46 su 62 | 47 su 62 | 75% |
| Tipo uguale | 44 su 46 | 45 su 47 | 96% |
| `inside` tenuto | 31 su 34 | 33 su 36 | 91% |
| Flussi ritrovati | 7 su 19 | 6 su 20 | 33% |
| Flussi, nodi alzati alla profondità 1 | 73% | 75% | 74% |
| Ingressi | 9 su 22 | 7 su 22 | 36% |
| Effetti | 8 su 24 | 5 su 25 | 27% |

Due lettori attenti arrivano alla stessa mappa su nodi, tipi e gerarchia. Sui flussi no: li tagliano con una grana diversa, e tornano a concordare quando si guarda per quali parti del sistema passano. Finché il proprietario non conferma i flussi di un caso, la misura dei flussi che vale è quella alla profondità 1.

### Soglie proposte, da confermare dal proprietario

Confermate dal proprietario il 26 novembre 2026.

Ogni misura almeno 0,85 volte l'accordo: nodi ritrovati 66%, profondità 0 e 1 79%, precisione 64%, tipo uguale 81%, `inside` tenuto 78% con almeno 15 nodi per caso, flussi alla profondità 1 63%. Flussi, ingressi ed effetti alla loro grana (28%, 31%, 23%) si riportano senza soglia finché i flussi non sono confermati. Frecce rifiutate al massimo 20%; stabilità fra due ripetizioni almeno 80%; una run fermata dal budget conta come fallita. Il tetto di costo per l'intero sistema, 2 USD, era scritto per Sonnet: con Opus 5.5, scelto dal proprietario, si riscrive dopo la prima run misurata.

Parametri da provare: modello (Opus 5.5 per partenza e gate; Sonnet 5.5 e Haiku 5.5 alla fine, per il costo; e sempre, come metro accanto a Claude, deciso dal proprietario il 20 novembre 2026, Qwen dal suo gateway LiteLLM: `--models qwen`, indirizzo e chiave nel secret Modal `daodan-gateway`, mai in un file), giri sui resti (0, 1, 3), `system_brief.LIMIT` (24.000, 48.000).

### Conferma del proprietario

Per ogni caso `results/system/<caso>-conferma.md` (fuori da git) elenca ciò che si conferma a mano: i nodi di profondità 0 e 1, i flussi e 20 foglie estratte con `random.Random(2026)`. Il resto regge su `reference.py check`. Un caso non confermato resta una bozza e i suoi numeri sono segnati così.

Gli archivi inviati a Modal portano solo codice e configurazione (`code_archive.py`): un nodo del riferimento fatto solo di dati, immagini o fogli non è nello snapshot e non si può ritrovare. Si conta a parte.

Un riferimento è legato a un commit del suo progetto (`commit`: un id, oppure cartella e id quando il caso sta su più repository): `reference.py check` legge i file di quel commit con git, non l'albero di lavoro, perché il progetto va avanti. `python reference.py pin EXPECTED.json RADICE [CARTELLA …]` lega un riferimento al commit di oggi, sposta le citazioni il cui testo ha cambiato riga e nomina quelle che non ritrova. L'archivio di una misura si fa sullo stesso commit: `python code_archive.py OUT.tar REPOSITORY@COMMIT`. Il 19 novembre i sei riferimenti sono legati al commit del giorno: 20 citazioni spostate in due riferimenti, un membro tolto perché git lo ignora.

### Run di verifica, 19 novembre 2026

Una run intera sul caso più piccolo, con `--rules session` e Haiku 5.5, archivio di solo codice (175 file nello snapshot): prova che lo script gira dall'inizio alla fine, non è la misura di partenza. Preparazione 188 s; sessione delle regole 108 s, 19 turni, 0,128 USD, 10 regole; mapper 32 s, 4 turni, 0,011 USD. La mappa ha 9 nodi e 4 flussi contro i 62 nodi e 19 flussi del riferimento: nodi ritrovati 4 su 49, a profondità 0 e 1 2 su 12, precisione 6 su 9, `inside` tenuto 0 (la mappa di oggi non ha il campo), flussi 0 su 19 e 34% alla profondità 1; frecce 4 provate, 5 dichiarate, 1 rifiutata. Non verificato: una ripetizione avviata dall'interno della prima (`--reps 2`).

### Misura di partenza, 19 novembre 2026

Il Daodan di oggi sui cinque casi: `--rules session`, Haiku 5.5, due ripetizioni del mapper sulle stesse regole, archivi di solo codice. I numeri sono una bozza finché il proprietario non conferma i riferimenti. Dieci run riuscite, nessuna fermata dal budget, 0,97 USD in tutto; il dettaglio è in `results/system/sysmap-a7-haiku/`.

| Caso | Nodi del riferimento | Nodi della mappa | Nodi ritrovati | Parti di profondità 0 e 1 ritrovate | Parti toccate | Precisione | File coperti | Flussi della mappa | Flussi abbinati | Stabilità | Costo (USD) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| poc-data-extraction | 62 | 7 e 7 | 3 e 3 su 49 | 0 e 1 su 12 | 3 e 4 su 12 | 3 su 7 e 5 su 7 | 5% | 4 e 3 | 0 su 19 | 43% | 0,04 |
| phazly | 130 | 6 e 13 | 1 e 0 su 118 | 1 e 0 su 24 | 3 e 5 su 24 | 3 su 6 e 4 su 13 | 15% e 1% | 2 e 7 | 0 su 38 | 23% | 0,20 |
| hostay | 109 | 18 e 19 | 0 e 1 su 98 | 0 su 22 | 6 e 9 su 22 | 3 su 18 e 4 su 19 | 2% e 5% | 8 e 10 | 0 su 35 | 68% | 0,40 |
| qamille | 106 | 11 e 14 | 2 e 4 su 95 | 1 e 0 su 17 | 3 su 17 | 4 su 11 e 6 su 14 | 11% e 3% | 5 e 11 | 0 su 29 | 64% | 0,15 |
| qamille-enterprise | 142 | 5 e 5 | 2 e 3 su 129 | 1 su 26 | 3 su 26 | 3 su 5 e 4 su 5 | 28% e 30% | 2 e 1 | 0 su 39 | 40% | 0,17 |

«File coperti» è la quota dei file dello snapshot che stanno in un nodo interno della mappa. «Parti toccate» conta le parti di profondità 0 e 1 in cui un nodo della mappa punta senza portarle (`reach`; due riferimenti dello stesso caso ne toccano 12 su 12 e 13 su 14). Nessun nodo ha `inside`: il campo non esiste. Nodi ritrovati, parti di profondità 0 e 1 e stabilità restano sotto la soglia in ogni run. Precisione e tipo uguale passano la soglia in qualche run, su 3–6 nodi abbinati: lì non dicono nulla. Le frecce rifiutate superano il 20% in tre run su dieci.

**«Flussi abbinati 0» non vuol dire che la mappa non ha flussi.** Il confronto abbina un flusso attraverso i suoi nodi, e un nodo attraverso i suoi file: con nodi di 1–3 file nessun nodo si abbina, e nessun flusso con lui. La mappa ha da 1 a 11 flussi per run. Letti a mano per nome in quattro casi, sono quasi tutti flussi del riferimento (4 su 4, 6 su 7, 10 su 10, 9 su 11), più grossi: ne coprono fra un quinto e un terzo, ne fondono alcuni, e passano per blocchi interi («l'app», «l'API», «il database») invece che per la schermata e la funzione. È una lettura, non una misura. Un abbinamento più largo dei flussi, provato il 19 novembre, li accoppiava a caso attraverso quei blocchi ed è stato tolto: il confronto dei flussi torna a valere quando i nodi portano la loro parte (Parte B); fino ad allora per i flussi vale la misura alla profondità 1, da 12% a 51% (soglia 63%).

Cause, lette nei file delle run:

1. **La mappa è un elenco corto e piatto.** Da 5 a 19 nodi contro 62–142, nessuno con `inside` (il campo non esiste): il mapper chiude in 4–10 turni e 38–126 secondi, per 0,6–2,9 centesimi.
2. **Un nodo nomina pochi file, non la sua parte.** In quattro casi la mediana è fra 1 e 3 file per nodo interno, nel quinto la mappa ha due o tre nodi interni grandi quanto un repository; il riferimento dà a un nodo di primo livello la sua cartella. Per questo nemmeno le parti di primo livello che il mapper riconosce risultano ritrovate.
3. **I collegamenti dipendono da chi scrive le regole, e variano da caso a caso.** Regole scritte: 4, 10, 133, 10, 48. Due casi hanno archivi letti e scritti (38 e 6), tre nessuno. Un caso con due interfacce desktop non ha nessuna azione dell'utente (5 lacune «handler not a named function»). Due sessioni scrivono una regola per rotta (122 e 45 regole `offre`) invece di una regola per costrutto. Il caso su due repository non ha nessun punto d'ingresso e 187 lacune, 105 delle quali «call arguments not readable».
4. **I flussi sono pochi, grossi e non poggiano sui collegamenti.** Da 1 a 11 per run contro 19–39; in tre casi nessuna freccia della mappa è provata da un collegamento, sono tutte dichiarate.
5. **Due ripetizioni sulle stesse regole danno mappe diverse.** Stabilità fra 23% e 68%, soglia 80%.

La preparazione dello snapshot e del passaggio del motore chiede da 142 a 1.326 secondi alla prima ripetizione: in tre casi più delle due sessioni del modello insieme.

**Quanto conta il modello.** Lo stesso caso più piccolo con Sonnet 5.5 (`results/system/sysmap-a7-sonnet/`): 12 e 10 nodi, ritrovati 5 e 2 su 49, a profondità 0 e 1 1 su 12 (toccate 5 e 6 su 12, contro 3 e 4), precisione 7 su 12 e 4 su 10, 6 e 5 flussi, abbinati 0 su 19 (47% e 23% alla profondità 1), stabilità 50%, 0,46 USD contro 0,04. Le regole sono 5, nessuna azione dell'utente diventa un collegamento, nessun archivio. Il modello più grande costa undici volte tanto e non cambia l'ordine di grandezza: il limite è in ciò che Daodan dà al mapper e in ciò che la mappa sa dire.

### Ordine dopo la misura

Le cause 1 e 2 non dipendono dal caso e vengono prima: Parte B (tipi, `inside`, un nodo che resta fuori dai flussi, la regola che un nodo porta la sua parte). Poi la Parte C, perché le cause 3 e 5 chiedono un giro in cui il modello rivede regole e mappa su ciò che resta fuori. Poi la Parte D, che toglie al modello la scoperta di applicazioni, schermate e azioni dell'utente. E ed F restano in coda: registro e grafo dell'app non spostano queste misure.

### Dopo la Parte B, 19 novembre 2026

Gli stessi cinque casi, Haiku 5.5, due ripetizioni, archivi sul commit dei riferimenti, dopo i task B1–B4 (tipi nuovi, `inside`, campi dei servizi di altri, regole del mapper); 0,84 USD, nessuna run fermata dal budget; `results/system/sysmap-gate-b-haiku/`. Ogni cella dà prima e dopo, sulle due ripetizioni.

| Caso | Nodi della mappa | Nodi ritrovati | Parti di profondità 0 e 1 ritrovate | Precisione | `inside` tenuto | Flussi della mappa | Flussi alla profondità 1 | Stabilità |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| poc-data-extraction | 7, 7 → 11, 12 | 3, 3 → 8, 9 su 49 | 0, 1 → 6, 8 su 12 | 3/7, 5/7 → 10/11, 11/12 | 0 su 2, 0 su 1 | 4, 3 → 3, 4 | 28%, 30% → 44%, 48% | 43% → 83% |
| phazly | 6, 13 → 24, 17 | 1, 0 → 16, 9 su 118 | 1, 0 → 11, 7 su 24 | 3/6, 4/13 → 18/24, 12/17 | 8 su 8, 4 su 4 | 2, 7 → 12, 7 | 25%, 17% → 31%, 39% | 23% → 42% |
| hostay | 18, 19 → 15, 10 | 0, 1 → 4, 5 su 98 | 0, 0 → 2, 4 su 22 | 3/18, 4/19 → 7/15, 7/10 | 1 su 1, 3 su 3 | 8, 10 → 5, 2 | 12%, 14% → 34%, 21% | 68% → 33% |
| qamille | 11, 14 → 5, 5 | 2, 4 → 5, 3 su 95 | 1, 0 → 3, 2 su 17 | 4/11, 6/14 → 5/5, 5/5 | 2 su 4, 1 su 2 | 5, 11 → 0, 2 | 29%, 51% → 0%, 46% | 64% → 60% |
| qamille-enterprise | 5, 5 → 6, 6 | 2, 3 → 5, 5 su 129 | 1, 1 → 4, 4 su 26 | 3/5, 4/5 → 6/6, 6/6 | 3 su 4, 3 su 4 | 2, 1 → 0, 1 | 40%, 36% → 0%, 36% | 40% → 100% |

**Il gate non è passato.** Salgono le parti di profondità 0 e 1 ritrovate e la precisione in ogni caso; i nodi con un padre sono da 2 a 15 per mappa e, dove si può misurare, il padre è quello del riferimento; un servizio di altri con l'id del registro porta sempre la famiglia giusta (da 0 a 6 per mappa). Ma `inside` si misura su 1–8 coppie, mai su 15, perché le mappe restano di 5–24 nodi, e in tre casi i flussi calano. «File coperti» non si riporta più: il nodo dell'intero sistema copre tutto.

La causa, letta nelle sessioni: la risposta a una proposta registrata era di 93.000–286.000 caratteri, perché ogni nodo elencava ogni file della sua parte e il nodo del sistema ogni file del repository. In 7 delle 8 run lette (tutte tranne il caso più piccolo) la risposta superava il limite dello strumento: il mapper non ha mai letto che cosa era stato accettato o rifiutato, e si è fermato dopo una proposta, in 4–7 turni. In più, in quattro run la prima proposta è tornata indietro per `scope` scritto `null` o vuoto. Corretti il 19 novembre con i loro test: una risposta conta per cartella i file di un nodo oltre i 40 (`files_by_directory`), e uno `scope` vuoto vale come assente.

**Rimisurata con le due correzioni** (`results/system/sysmap-gate-b2-haiku/`, 0,87 USD). La risposta a una proposta scende a circa 7.000 caratteri e il mapper la legge; la proposta è accettata intera. Poi si ferma: 3–6 turni, una proposta sola, e lo dice («copre solo una parte del sistema»): nulla gli chiede di continuare.

| Caso | Nodi della mappa | Nodi ritrovati | Parti di profondità 0 e 1 ritrovate | Precisione | `inside` tenuto | Flussi alla profondità 1 | Stabilità |
| --- | --- | --- | --- | --- | --- | --- | --- |
| poc-data-extraction | 8, 7 | 6, 3 su 49 | 6, 3 su 12 | 7/8, 4/7 | 0 su 0 | 30%, 28% | 38% |
| phazly | 6, 12 | 6, 9 su 118 | 6, 7 su 24 | 6/6, 10/12 | 3 su 3, 4 su 4 | 31%, 61% | 33% |
| hostay | 6, 9 | 4, 5 su 98 | 4, 4 su 22 | 4/6, 6/9 | 1 su 1, 1 su 1 | 17%, 17% | 67% |
| qamille | 7, 15 | 5, 7 su 95 | 3, 3 su 17 | 6/7, 10/15 | 2 su 4, 2 su 4 | 19%, 46% | 40% |
| qamille-enterprise | 6, 8 | 4, 5 su 129 | 4, 4 su 26 | 5/6, 7/8 | 3 su 3, 3 su 4 | 9%, 37% | 75% |

**Esito del gate B.** Quello che la Parte B porta regge: precisione da 4 nodi su 7 a 6 su 6, `inside` tenuto in 19 coppie su 24 misurate, famiglia giusta su 11 servizi di altri ritrovati su 13. Il gate non passa perché le mappe restano di 6–15 nodi, e la causa non è la gerarchia ma la sessione che si ferma dopo una proposta: è il compito della Parte C (la sequenza, il giro sui resti), che parte.

### Con la sequenza (Task C1), 20 novembre 2026

Haiku 5.5, `--rules session`, due ripetizioni (`results/system/sysmap-c1-haiku/`, 0,75 USD). Il mapper comincia la sequenza (lo scheletro, poi una proposta per area) e si ferma dopo 1–4 aree, scrivendo da sé che la mappa è parziale: 4–19 turni, 5–15 nodi, 0–4 flussi. Nessun limite lo ferma.

**Quanto conta il modello.** Il solo mapper, sulle regole e i collegamenti scritti da Haiku nella prima ripetizione, una run per modello (`results/system/sysmap-c1-models/`):

| Caso | Modello | Nodi | Flussi | Nodi ritrovati | Profondità 0 e 1 | Profondità 2 | Precisione | `inside` tenuto | Flussi alla profondità 1 | Ingressi | Turni | Costo del mapper (USD) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| poc-data-extraction | Haiku (2 run) | 6, 10 | 3, 3 | 5, 9 su 49 | 5, 8 su 12 | 0, 1 su 32 | 5/6, 9/10 | 0 su 0, 0 su 1 | 48%, 29% | 0 su 22 | 5, 8 | 0,01 |
| poc-data-extraction | Sonnet | 12 | 4 | 9 su 49 | 8 su 12 | 1 su 32 | 11/12 | 0 su 1 | 45% | 0 su 22 | 6 | 0,23 |
| poc-data-extraction | Opus | 37 | 15 | 21 su 49 | 8 su 12 | 11 su 32 | 26/37 | 9 su 10 | 58% | 4 su 22 | 19 | 1,18 |
| hostay | Haiku (2 run) | 15, 11 | 4, 4 | 4, 3 su 98 | 2 su 22 | 2, 1 su 60 | 5/15, 4/11 | 1 su 1 | 3%, 26% | 0 su 48 | 19, 15 | 0,02 |
| hostay | Sonnet | 19 | 5 | 8 su 98 | 6 su 22 | 2 su 60 | 9/19 | 2 su 2 | 10% | 0 su 48 | 10 | 0,21 |
| hostay | Opus | 49 | 19 | 15 su 98 | 7 su 22 | 5 su 60 | 20/49 | 6 su 6 | 44% | 0 su 48 | 19 | 1,44 |

Con la sequenza il modello conta: Opus arriva in fondo (la prima mappa con il secondo livello e con flussi ritrovati alla loro grana, 3 su 19 nel caso più piccolo), Haiku e Sonnet si fermano presto. Sonnet si è fermato per chiedere una scelta a chi non c'è: il ruolo ora dice che nessuno risponde durante il lavoro. Su hostay nessun ingresso entra nei flussi e 8 frecce su 43 sono rifiutate: le regole di Haiku non legano il sito alla API, la causa che la Parte D e il giro sulle regole devono togliere.

**Uno strumento pronto per le rotte: OWASP Noir, 20 novembre 2026** (piano, Task C4.14; `modal run modal_map.py::noir`, `results/system/noir/`). Noir 1.5.0 (MIT, analisi statica, un eseguibile solo) nel container, sugli stessi cinque archivi, pochi minuti in tutto. Per ogni endpoint dà metodo, percorso, parametri, il gestore con file e riga, la tecnologia e il protocollo.

| Caso | Endpoint di Noir | Rotte offerte trovate da Daodan con le regole del modello | Rotte scritte nel riferimento | Ritrovate uguali | Con lo stesso percorso a meno di un prefisso |
| --- | --- | --- | --- | --- | --- |
| poc-data-extraction | 13 (tutti comandi) | 0 | 1 | 0 | 0 |
| phazly | 193 (115 HTTP, 75 comandi, 3 collegamenti aperti da fuori) | 112 | 126 | 3 | 99 |
| hostay | 176 (151 HTTP, 25 comandi) | 0 | 143 | 113 | 113 |
| qamille | 59 (56 HTTP, 3 comandi) | 0 | 40 | 38 | 40 |
| qamille-enterprise | 86 (83 HTTP, 3 comandi) | 0 | 63 | 61 | 63 |

Sulle rotte che i riferimenti scrivono (373) Noir ne ritrova 215 uguali per metodo e percorso e 315 a meno di un prefisso: in un caso le rotte sono montate sotto un prefisso che Noir non risolve. In tre casi dove le regole scritte dal modello non avevano trovato nessuna rotta offerta, Noir ne trova 56, 83 e 151. Con la misura degli ingressi (un candidato in un file del nodo d'ingresso): rotte 10 su 12, messaggi 4 su 14 (gli avvisi di ritorno), comandi 4 su 17. Trova anche comandi da riga di comando (119) e collegamenti aperti da fuori, cioè ingressi di altri due tipi. Passa il criterio della spec (5.8): pubblico, licenza adatta, e trova ciò che le altre fonti non vedono. Legge il codice del progetto: gira nel container, non sull'host.

### Schede dei percorsi, prova a costo zero, 20 novembre 2026

Prova della proposta del piano (Task C4): la macchina mostra, il modello nomina. `python traces.py cards LINKS.json GLOB OUT.json` prende dai collegamenti già calcolati di un caso i simboli che chiamano e che nessuno chiama, nei file che corrispondono a `GLOB` (qui le pagine del meta-framework), e per ognuno scrive una scheda: ciò che raggiunge e che al più il 15% degli altri raggiunge, dal più vicino, con nome, file e riga della chiamata. `python traces.py ask CARDS.json OUT.json` dà una scheda per richiesta a un modello, con indirizzo e chiave dall'ambiente; `test_traces.py`.

| Cosa | Risultato |
| --- | --- |
| Ingressi trovati, schede con almeno un passo, passi | 26, 23, 261 |
| Modello | Qwen dal gateway del proprietario, una richiesta per scheda, contesto nuovo ogni volta |
| Tempo, token | 112 secondi; 15.135 in ingresso, 3.543 in uscita |
| Risposte in JSON valido | 23 su 23 |
| Flussi nominati | 51, ognuno con area e numeri dei passi |

Letti a mano contro il riferimento del caso (35 flussi; una lettura, non una misura): 23 flussi del riferimento partono da una schermata, e 15 sono riconosciuti per nome, 3 in modo incerto, 5 mancano; gli altri 12 partono da un lavoro a orario, da un avviso di ritorno o dal rilascio, e chiedono altri ingressi. Circa 10 dei 51 nomi sono una funzione, non un flusso (un calcolo, un caricamento): la scheda non dice ancora quali passi sono un'azione della persona. Una volta su 51 il nome comincia con una parola vuota. Con la proposta intera, sullo stesso caso e le stesse regole, Haiku registra 4 flussi e Opus 19 per 1,44 USD, nessuno abbinato al riferimento. Limiti della prova: il `GLOB` l'ha dato una persona; i percorsi si fermano al confine fra il sito e la API, che i collegamenti di quel caso non hanno.

**Il contratto in quattro punti, lo stesso giorno.** La prima prova chiedeva un nome a una lista piatta di funzioni: il modello indovinava dai nomi, e nulla lo provava. `traces.py` ora fa trovare, correggere e certificare (il suo docstring dice i quattro punti): archi tipizzati e numerati (`chiama`, l'evento, `HTTP metodo percorso`, `scrive`, `legge`), tenuti solo sui rami che arrivano a un effetto o a un punto dove i collegamenti si fermano; sotto quel punto il sorgente; un flusso è una catena contigua di numeri dall'ingresso a un effetto; `traces.py verify` rifiuta ciò che non regge sui collegamenti e sulle righe.

| Caso | Schede | Con almeno una catena | Archi mostrati, tolti perché non portano a nulla | Flussi proposti | Certificati | Rifiutati | Lacune con causa | Tempo |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| collegamenti con una sola regola (nessuno store, nessuna rotta legata) | 26 | 0 | 0, 722 | - | - | - | - | - |
| collegamenti con store, rotte legate ed eventi | 194 | 23 | 1.082, 12.602 | 115 | 97 | 18 (16 non partono dall'ingresso, 2 non contigui) | 17 su 17 | 197 s |

Che cosa dicono: (1) dove i collegamenti non hanno effetti nulla si può certificare, e i 51 nomi della prima prova su quel caso erano ipotesi; (2) dove li hanno, il modello debole compone catene vere e la macchina scarta le altre con il motivo; (3) certificato non vuol dire giusto: i 97 flussi hanno 33 nomi, e i più frequenti (14, 10 e 9 volte) sono un controllo che ogni rotta fa per prima cosa, non lo scopo dell'ingresso. Restano da fare: unire le catene con la stessa coda di archi in un flusso con più ingressi; distinguere l'effetto proprio di un ingresso da quello che quasi tutti raggiungono; partire dagli eventi dell'interfaccia e non dai simboli che nessuno chiama (3 archi di evento su 1.082). Nessuna correzione è stata tentata sulle 17 lacune: la causa data ripete il motivo della macchina.

### Ingressi senza regole

Misura del piano (Task C4.1), prima di scrivere le reti: per tipo degli otto e per rete, quanti ingressi dei riferimenti la rete ritrova, quanti suoi candidati non sono ingressi e quali file nessun candidato raggiunge. `modal run benchmarks/system-map/modal_map.py::entries --tars CASO=ARCHIVIO[,CASO=ARCHIVIO]` scrive per caso, senza regole e dopo il passaggio del motore, `candidates.json` (i candidati di `daodan/core/entries.py` e le chiamate dei collegamenti) e `files.txt` in `results/system/entries/CASO/`; poi `python entries.py measure candidates.json expected/CASO-system.json files.txt` (`test_entries.py`). Un ingresso è ritrovato da una rete quando un suo candidato sta in un file del nodo dell'ingresso, con i membri espansi sui file dello snapshot come in `score.py system`; un ingresso il cui nodo non è interno o ha più di 12 file si conta a parte (`apart`); un candidato fuori dai file di ogni nodo d'ingresso non è un ingresso (`not_entries`); i file che nessun candidato contiene né raggiunge con le chiamate si contano per cartella (`unreached`). La prima rete è il residuo, «chiama e nessuno lo chiama».

**La rete del residuo, 20 novembre 2026.** Sui cinque casi, dai collegamenti della misura con la sequenza (con le regole che quella sessione aveva scritto; il job senza regole è scritto e non lanciato):

| Tipo di ingresso | Ritrovati | A parte |
| --- | --- | --- |
| controllo dell'interfaccia | 63 su 67 | 41 |
| rotta | 11 su 12 | 4 |
| comando | 13 su 17 | 8 |
| messaggio | 11 su 14 | 4 |
| orario | 12 su 26 | 4 |
| evento hardware | - | 2 |

I candidati sono 8.591, e 7.717 non stanno in nessun nodo d'ingresso: nove su dieci non sono ingressi (test, codice morto, pezzi a metà flusso di cui i collegamenti hanno perso chi li chiama). 2.874 file su 5.826 non sono raggiunti da nessun candidato. La rete serve a dire dove guardare, non a dire che cos'è un ingresso: è il compito delle reti che seguono (C4.3-C4.10). I tre denominatori più alti di uno rispetto alla prima stima a mano contano anche i nodi i cui file non sono nello snapshot.

**Le tre reti, senza regole, 20 novembre 2026** (`modal run modal_map.py::entries`, `results/system/entries-c43/`; nessun modello). Le reti di C4.3 e C4.4 leggono ancora il markup con espressioni regolari: è la misura di prima della riscrittura sull'albero (C4.12).

| Rete | Candidati | Non ingressi | Controlli dell'interfaccia | Rotte | Comandi | Messaggi | Orari |
| --- | --- | --- | --- | --- | --- | --- | --- |
| residuo (chiama e nessuno lo chiama) | 8.715 | 90% | 63 su 67 | 11 su 12 | 13 su 17 | 11 su 14 | 12 su 26 |
| argomento (una funzione data a una chiamata) | 8.908 | 82% | 64 su 67 | 9 su 12 | 11 su 17 | 5 su 14 | 6 su 26 |
| attributo (una funzione legata nel markup) | 1.223 | 37% | 53 su 60 | 2 su 12 | 0 su 6 | 0 su 13 | 0 su 25 |

- La rete dell'attributo è la sola precisa: due candidati su tre stanno in un nodo d'ingresso, e ritrova quasi tutti i controlli che la misura può contare. Ha un'etichetta per 378 candidati su 1.223: è il numero che la lettura dall'albero deve alzare.
- La rete dell'argomento ha 1.388 forme distinte, e le più numerose non sono ingressi: asserzioni e casi delle prove, funzioni date a `map` o a chi trasforma un errore, effetti di un componente. Vanno classificate una volta (C4.5), e le prime decine coprono la maggior parte dei candidati; fra le forme vere ci sono il comando di un pulsante di una interfaccia desktop (125) e chi ascolta un evento della finestra (82).
- Gli orari restano scoperti da ogni rete (al più 12 su 26, e solo dal residuo): servono le dichiarazioni fuori dal codice e le annotazioni (C4.6, C4.8).
- 2.822 file su 5.826 non sono raggiunti da nessun candidato.

**Dopo la riparazione della lettura dall'albero e con la rete delle annotazioni** (`results/system/entries-tree2/`, stessi cinque casi, senza regole e senza container: il motore nativo non ha girato, come in ogni misura di questa pagina finora).

| Rete | Candidati | Non ingressi | Controlli dell'interfaccia | Rotte | Comandi | Messaggi | Orari |
| --- | --- | --- | --- | --- | --- | --- | --- |
| attributo, dall'albero | 1.720 | 38% | 54 su 60 | 2 su 12 | 0 su 6 | 0 su 13 | 1 su 25 |
| argomento, dall'albero | 6.546 | 82% | 64 su 67 | 9 su 12 | 11 su 17 | 1 su 14 | 5 su 26 |
| decoratore | 7.539 | 97% | 4 su 67 | 9 su 12 | 4 su 17 | 8 su 14 | 23 su 26 |

La lettura dall'albero supera quella a righe che sostituisce (1.223 legami, 53 su 60, 378 etichette): 1.720 legami, 54 su 60, un'etichetta su 542. Le annotazioni ritrovano 23 orari su 26, che nessun'altra rete vedeva; quasi tutti i loro candidati non sono ingressi, e quali forme lo sono si decide una volta (C4.5). In un caso con interfacce Python: 26 legami di un controllo, 26 con il gestore risolto, 14 con l'etichetta (prima 25, 4 e 0).

### Lettore del framework (prova tolta)

Una prova del 20 novembre 2026: un programma a parte sul compilatore TypeScript, su un albero senza dipendenze. **Tolta lo stesso giorno per decisione del proprietario:** era un doppione scritto a mano di scip-typescript, lo strumento ufficiale che Daodan avvia già nel container dopo il ripristino delle dipendenze del progetto (`daodan/core/indexers/typescript.py`), e andava contro la regola di AGENTS.md sulle soluzioni pronte. Gli ingressi dell'interfaccia si leggono da ciò che quello strumento risolve. Resta il numero, come confronto.

**Prima misura, 20 novembre 2026** (`results/system/framework/`, albero nudo, senza le dipendenze dei progetti; meno di 1 USD). Sui quattro casi con un'interfaccia web: 3.792 legami con un valore di tipo funzione, 53 controlli dell'interfaccia dei riferimenti ritrovati su 60 (la lettura generica dall'albero 48, con 959 legami), il 46% dei legami fuori da ogni nodo d'ingresso, un'etichetta su 1.060. Il tipo resta ignoto per 4.500 attributi (2.276 in un caso): senza le librerie installate il compilatore non conosce i tipi dei loro componenti. Il caso con sole interfacce Python dà zero, come atteso. I risultati restano in `results/system/framework/`.

### Legami fra flussi, prova a costo zero, 20 novembre 2026

Dai soli flussi di due riferimenti (38 e 35 flussi), senza modello: 48 nodi su 106 e 43 su 100 sono usati da più di un flusso; 60 e 34 coppie di flussi condividono almeno due nodi, tolti gli attori, i dispositivi e i nodi che più del 30% dei flussi tocca; l'entità più condivisa sta in 53 e in 6 coppie; 6 e 7 flussi non hanno nessun legame. Il legame «avvia» (un effetto dell'uno è l'ingresso dell'altro) esce una volta sola per caso: i riferimenti non scrivono l'ingresso di un flusso sul nodo dove un altro ha l'effetto, e va letto dai collegamenti (chi scrive un dato e chi parte dal suo cambio). Proposta nella spec del 18 novembre, sezioni 3.8 e 11.6.

### Embedder piccoli, prova a costo zero, 20 novembre 2026

`embed_probe.py`, in locale, modelli statici di model2vec (MIT, senza scheda grafica). Due misure. **Catene:** sui 97 flussi certificati di un caso (33 nomi; 262 coppie su 4.656 hanno la stessa coda di tre archi), quanto bene la somiglianza dei nomi dice «stessa catena». **Ricerca:** su un altro caso, per ognuno dei 35 flussi del riferimento, il nome certificato che gli risponde fra 52, oppure nessuno (20 hanno una risposta; le etichette le ha scritte una persona e stanno fuori da git).

| Modello | Catene: F1 (precisione, richiamo) | Ricerca: il più vicino è giusto | Ricerca: giusti con «nessuno» ammesso |
| --- | --- | --- | --- |
| nessuno, parole in comune | 0,72 (0,73, 0,71) | 8 su 20 | 20 su 35 |
| potion-base-8M | 0,72 (0,73, 0,71) | 13 su 20 | 22 su 35 |
| potion-base-32M | 0,77 (0,68, 0,87) | 12 su 20 | 23 su 35 |
| potion-retrieval-32M | 0,75 (0,61, 0,97) | 12 su 20 | 25 su 35 |
| potion-multilingual-128M | 0,71 (0,70, 0,73) | 11 su 20 | 23 su 35 |
| potion-code-16M | 0,74 (0,64, 0,87) | 12 su 20 | 24 su 35 |
| potion-code-16M-v2 | 0,76 (0,68, 0,87) | 11 su 20 | 24 su 35 |

- Un embedder serve per la ricerca per parole: trova 11-13 risposte su 20 dove le parole in comune ne trovano 8. Non basta da solo: 7-9 risposte su 20 restano sbagliate, quindi propone e non decide.
- Sulle catene il guadagno è nel richiamo (87-97 coppie su 100 contro 71), a prezzo della precisione; per i doppioni esatti la coda di archi è già un fatto dei collegamenti, e l'embedder serve per le varianti scritte con parole diverse.
- I modelli stanno tutti vicini: la differenza fra loro è di una o due risposte su 35, sotto ciò che un caso solo può distinguere. Il più grande non è il migliore.
- Non provati: i modelli a trasformatore (il primo tentativo ha riempito il disco della macchina; vanno provati su Modal) ed EmbeddingGemma, che Daodan ha come facoltativo.

**Su 531 richieste in parole, lo stesso giorno** (`embed_queries.py`, poi `embed_probe.py rank` in locale e `modal_embed.py` per i modelli a trasformatore). Un modello dal gateway ha scritto, dai riferimenti di quattro casi, due richieste per ognuno dei 131 flussi (come chi usa il prodotto, come chi chiede una review) e una domanda per ognuna di 269 parti, senza le parole del nome. Si cerca fra i flussi o le parti dello stesso caso (da 19 a 93). Quante volte la risposta giusta è la prima, e fra le prime tre, cercando nella voce dell'anagrafica (nome, ingressi, effetti, nodi; per una parte nome e descrizione):

| Modello | Flusso, review: prima / prime tre | Flusso, utente | Parte |
| --- | --- | --- | --- |
| nessuno, parole in comune | 54% / 64% | 24% / 40% | 25% / 36% |
| potion-base-8M | 32% / 53% | 30% / 45% | 23% / 36% |
| potion-retrieval-32M | 47% / 66% | 32% / 48% | 30% / 43% |
| potion-code-16M-v2 | 39% / 53% | 31% / 47% | 27% / 40% |
| potion-multilingual-128M | 60% / 77% | 51% / 70% | 43% / 58% |
| e5-small-v2 (solo inglese) | 61% / 82% | 41% / 66% | 29% / 49% |
| paraphrase-multilingual-MiniLM-L12-v2 | 57% / 76% | 56% / 77% | 45% / 69% |
| multilingual-e5-small | 68% / 85% | 60% / 78% | 60% / 79% |
| multilingual-e5-base | 73% / 89% | 69% / 82% | 65% / 84% |
| bge-m3 | 79% / 92% | 81% / 92% | 67% / 85% |
| multilingual-e5-large | 82% / 93% | 82% / 92% | 71% / 91% |

- Cercando fra i soli nomi ogni modello perde da 20 a 40 punti (il migliore: 47% / 65% sui flussi): la voce dell'anagrafica con ingressi, effetti e nodi è ciò che rende la ricerca possibile.
- Il modello conta, e la prova piccola non lo mostrava: i modelli a trasformatore multilingue stanno sopra ogni modello statico, e fra gli statici solo il multilingue supera le parole in comune. Il modello solo inglese regge la richiesta di review, che usa parole vicine al codice, e cade su quella di chi usa il prodotto.
- Limiti: le richieste le ha scritte un modello, non persone; i quattro casi sono in italiano; tempi e memoria dei modelli sulla macchina di chi usa Daodan non sono misurati.

## Esecuzione

| Misura | Comando |
| --- | --- |
| 1, 2, 4, 5 | `modal deploy benchmarks/system-map/modal_map.py`, poi `python benchmarks/system-map/modal_map.py spawn --tag TAG --cases CASO[,CASO] --tar CASO=ARCHIVIO … --rules session --scopes system --models opus --reps 2 [--budget USD]` (archivio da `python code_archive.py OUT.tar REPOSITORY[@COMMIT]`: codice e configurazione fra i file tracciati, mai dati né segreti, `test_code_archive.py`): per caso, perimetro e modello il passaggio del motore e una sessione `claude -p` con il compito `LINKS` dell'app scrivono le regole; la prima ripetizione le lascia sul volume con i collegamenti (`rules.json`, `links.json`) e avvia le altre su di esse; ogni ripetizione è una sessione nuova di `claude -p --agent codebase-map:system-mapper`. `--rules PERCORSO` con `--links CASO=PERCORSO` usa un file di regole e i collegamenti calcolati prima; `--rules none` lascia le regole all'agente. Sul volume `daodan-flow-results`, in `TAG/ETICHETTA`, restano `map.json`, `files.txt`, `stream.jsonl`, `rules-stream.jsonl` e `summary.json` (costo, token, arresto per budget); `modal volume get daodan-flow-results TAG/ETICHETTA benchmarks/system-map/results/system/TAG` li porta qui. Poi `python score.py system map.json expected/CASO-system.json files.txt` |
| 3 | `map.json` di ogni run riporta in `levels` i nodi fuori dal loro livello e i punti citati che non esistono, per ogni flusso registrato e ogni livello |
| 6, dimensione della scheda | `modal run benchmarks/system-map/modal_map.py::brief --phazly-tar PATH --phazly-links PATH` scrive `results/brief-<caso>.json`; poi `python score.py externals results/brief-<caso>.json expected/externals-<caso>.json registry` (oppure `stack-analyser`, `both`) |
| Il container nella run (task 1 del piano dell'analisi unificata) | `modal run benchmarks/system-map/modal_map.py::engine_proof_run [--tag TAG] [--out PATH]`, prima dei cinque casi: sulla fixture `js-npm-single`, cinque controlli con la loro prova scritta in `results/engine-proof.json`. 1: `engine-report.json` dice scip-typescript `fresh` (la pass è un processo figlio, con il motore da `sitecustomize`). 2: un arco osservato del passo dinamico è nell'archivio `engine-edges.sqlite`, su `src/index.js`. 3: la preparazione raggiunge `pypi.org` e rifiuta un host fuori dai registri, un indirizzo HTTP semplice e un indirizzo IP. 4: una sandbox non vede `/results` né i risultati di un altro caso, e non scrive nella sua cartella. 5: dopo una preparazione fallita e una sandbox che non parte non resta nulla sul volume né in esecuzione. Richiede il client Modal 1.5.0 o successivo (`outbound_domain_allowlist`, `Volume.with_mount_options`). *Eseguita il 23 novembre 2026 su Modal (client 1.5.5), `results/engine-proof.json`. Primo giro: 3 controlli su 5; scip-typescript e l'arco osservato mancavano perché il processo figlio della pass non trovava `grpclib` (il client Modal sta in `/pkg`, le sue dipendenze altrove): `engine_environment` ora mette sul percorso le cartelle da cui il padre le importa. Secondo giro: 5 su 5. scip-typescript `fresh` su JavaScript; 6 archi osservati nell'archivio, uno in `src/index.js` (`lodash.head`); la preparazione raggiunge `pypi.org` e rifiuta un host fuori dai registri, HTTP semplice e un indirizzo IP; la sandbox non ha `/results` e non scrive nella sua cartella; dopo una preparazione fallita e un'immagine che non parte non resta nulla sul volume né in esecuzione. Non misurati: tempo e costo del giro.* |
| Intera analisi (task 2 del piano dell'analisi unificata) | `python benchmarks/system-map/code_archive.py OUT.tar REPOSITORY@COMMIT` (scrive anche `OUT.json`, i conteggi), `modal deploy benchmarks/system-map/modal_map.py`, poi `python benchmarks/system-map/modal_map.py whole --tag TAG --cases CASO --tar CASO=OUT.tar [--models qwen,haiku,opus] [--reps 2]`: un job per caso (`whole_case`: archivio, pass del motore con i container su Modal Sandbox, candidati) e, con `--models`, una `map_run` indipendente per caso, modello e ripetizione (ognuna prepara per sé e scrive le sue regole). Senza `--models` girano solo i casi, senza modello. Poi `modal volume get daodan-flow-results TAG benchmarks/system-map/results/system/TAG` e `python benchmarks/system-map/score.py whole benchmarks/system-map/results/system/TAG`: una tabella per caso, una riga per modello, una colonna che manca dice «non misurato» con la causa. *Scritto il 23 novembre 2026 e non eseguito; il formato dei file per caso è provvisorio fino al primo giro. Mancano le schede dei percorsi con il modello (`paths.json`) e la ricerca (`search.json`), che dipendono dai task 9 e 10.* |
| Tre corse sullo stesso progetto (task 2b) | `python benchmarks/system-map/score.py runs DA-ZERO SENZA-MODIFICHE UN-MODULO`, su tre cartelle con `pipeline-events.jsonl`, i `container-runs.jsonl` e `links.json` (`found`, `of`, di `possible.py`): tempo, ripristini, avvii degli indicizzatori e dell'app, collegamenti ritrovati; una corsa che costa meno e ritrova meno collegamenti è segnata, non contata come un guadagno. CPU, picco di RAM e spazio temporaneo non sono in nessun evento: «non misurato», finché la pipeline non li scrive. *Scritto il 23 novembre 2026 con uscite sintetiche; la misura su Modal aspetta il via del proprietario.* |
| Collegamenti possibili | sullo snapshot di un caso con il motore: `python daodan/core/flows.py links MANIFEST --rules RULES > LINKS.json`, poi `python benchmarks/system-map/possible.py MANIFEST LINKS.json EXPECTED-system.json --generators ritorno,incerto` (`--generators ""` per i soli collegamenti certi); un caso privato si misura su Modal o sullo snapshot del proprietario |
| Ingressi senza regole | `modal run benchmarks/system-map/modal_map.py::entries --tars CASO=ARCHIVIO[,CASO=ARCHIVIO]`, poi `python entries.py measure results/system/entries/CASO/candidates.json expected/CASO-system.json results/system/entries/CASO/files.txt` |

## Risultati

### Gruppi candidati, 12 novembre 2026, prima di fissare la regola

Con una soglia sulla quota dei punti d'ingresso (20%) la fixture `flow-model` non forma nessun gruppo, perché due su sei sono già il 33%, e phazly (235 punti d'ingresso, 68 risorse) forma un solo gruppo da 117 più 118 isolati: le risorse a media condivisione fanno catena. Con un gruppo per risorsa la fixture dà i due gruppi attesi (`store:db/payments` con quattro punti d'ingresso, `module:card payment provider` con tre) e phazly 44 gruppi, 143 punti d'ingresso in almeno un gruppo, 92 isolati (86 non toccano nessuna risorsa), in 9.300 caratteri.

### Costruzione del registro, 12 novembre 2026

2.172 voci da stack-analyser 1.27.6 (743 regole), CNCF Landscape (commit `75b47639`, senza le categorie dei membri e dei fornitori certificati) e Simple Icons 16.37.0 (marchi agganciati per nome). `derive`, senza modello, trova pacchetti su PyPI, crates.io o nel proxy di Go per 102 delle 455 voci con un pacchetto npm; tiene un pacchetto solo se il repository ha lo stesso proprietario del pacchetto npm principale, un modulo Go solo se il suo `go.mod` è vero, e scarta i pacchetti trovati per più voci. Una run di Haiku 5.5 (0,023 USD, 40.257 token in uscita) propone il resto: la macchina ne tiene 141, fra cui FastAPI, Flask e Pydantic, e ne rifiuta 22 oltre a quelle già coperte, compresi pacchetti veri con un altro proprietario (`boto3`, `prometheus-client`, il driver Go di MongoDB).

### Misura 6 e dimensione della scheda, 12 novembre 2026

Su Modal, senza modello, uno snapshot per caso: phazly dall'archivio con i collegamenti già calcolati con il motore, polar (`server/`) e tududi ai commit dei loro benchmark, senza regole. Richiamo sull'elenco scritto prima; sbagliati sono i riconoscimenti fuori da `externals` e da `also`, ognuno letto al punto citato.

| Caso | Attesi | Registro | stack-analyser | Insieme | Falsi letti al punto citato |
| --- | --- | --- | --- | --- | --- |
| phazly | 16 | 75,0% | 37,5% | 75,0% | 1: `ghost` da un nome in un test |
| polar | 25 | 60,0% | 32,0% | 60,0% | 0 |
| tududi | 14 | 78,6% | 78,6% | 78,6% | 3: `zoom` da un tipo TypeScript, `caddy` e `kubernetes` dagli esempi in `docs/examples` |

Nessun caso raggiunge la soglia del richiamo; tududi supera anche quella dei falsi. stack-analyser non riconosce nulla che il registro non veda già. Cause:

- Mancano dal registro: Zustand, Motor, Dramatiq, Logfire, Numeral, Plain, IPinfo, Google Play Billing (il segno è `@choochmeque/tauri-plugin-iap-api`).
- Il registro ha la voce ma non il segno che il progetto mostra: AWS (`boto3` riconosce solo il progetto Boto3), GitHub (`githubkit`), Expo (`exponent-server-sdk`), MinIO e Tailscale (immagini `bitnamilegacy/minio`, `tailscale/tailscale`), Cloud Run (solo un commento del Dockerfile e `.gcloudignore`), Cloudflare in tududi (`TURNSTILE_*`), Google Calendar (`GOOGLE_CLIENT_ID`, un prefisso troppo generico).
- L'elenco letto dai soli manifest non vede i servizi chiamati via HTTP e configurati con variabili: in polar il registro trova Discord, Linear, Slack, Resend e OpenAI, in tududi Discord, tutti veri al punto citato.
- Gli esempi di documentazione contano come configurazione del progetto.

Corretto durante la misura: con un target dentro il repository (polar `server/`) stack-analyser legge i percorsi dal target e lo snapshot dalla radice, così ogni riconoscimento cadeva; il richiamo di stack-analyser su polar passa da 0 a 32%.

Dimensione del testo della scheda, in caratteri; fra parentesi i gruppi riassunti in una riga:

| `CAP` \ `HOLDERS` | 5 | 8 | 12 |
| --- | --- | --- | --- |
| phazly 12.000 | 12.000 (48 su 48) | 12.000 (48) | 12.000 (48) |
| phazly 24.000 | 23.868 (7) | 23.891 (14) | 23.687 (30) |
| phazly 48.000 e senza tetto | 25.022 (0) | 26.773 (0) | 32.261 (0) |
| polar, tududi, ogni valore | 5.465 e 5.442 | | |

phazly ha 235 punti d'ingresso, 123 chiavi di store, 48 gruppi e 92 punti d'ingresso isolati; a 12.000 caratteri la sola parte fissa (moduli, esterni, isolati) riempie il tetto. polar e tududi senza regole non hanno gruppi.

### Misure da 1 a 5, prima tornata, 12 novembre 2026

16 run su Modal (tag `system-map-runs`), una sessione nuova ciascuna di `claude -p --agent codebase-map:system-mapper`: phazly e tududi, area «pagamenti e abbonamenti» e intero sistema, Haiku 5.5 e Sonnet 5.5, due ripetizioni. Tetto della scheda 48.000, `HOLDERS` 8. Costo totale 1,53 USD; una run (phazly, area, Haiku, prima ripetizione) non è partita perché Modal ha riusato il container di un'altra. Valori per run in `results/runs-20261112.json`.

| Misura | Risultato | Soglia |
| --- | --- | --- |
| 1 Riproduzione, phazly area | nodi ritrovati: Haiku 3, Sonnet 4 e 3 su 11; flussi 0 su 3; frecce rifiutate: Haiku 33%, Sonnet 0% | non raggiunta |
| 1 Riproduzione, phazly intero sistema | 0 nodi su 11 in tutte e quattro le run | non raggiunta |
| 2 Secondo progetto, tududi | nessuna mappa registrata in otto run | non misurabile |
| 3 Livelli | 10-20 viste per run su phazly: nessun nodo fuori dal suo livello, nessun punto citato che manca | raggiunta, sui flussi registrati |
| 4 Costo | area: Haiku 0,014 USD, Sonnet 0,41 e 0,18; intero sistema: Haiku 0,011 e 0,016, Sonnet 0,24 e 0,28; aperture del sorgente da 0 a 2 | area Sonnet oltre 0,30 in una run su due |
| 5 Stabilità | phazly area Sonnet 8 nodi su 9 uguali; intero sistema Haiku 1 su 6, Sonnet 1 su 7 | raggiunta solo sull'area con Sonnet |

Cause:

- **tududi:** la risposta di `brief` è di 51,9 KB e supera il limite dell'host per l'uscita di uno strumento (su phazly 31,8 KB passano): l'host la salva in un file e l'agente, che ha solo i quattro strumenti della mappa, non la legge. Il rapporto di `map` è di 86.648 caratteri, soprattutto per gli elenchi di ciò che la copertura lascia fuori (831 punti d'ingresso). In più `codebase_map_read` rifiuta con «parser fingerprint changed»: probabilmente il run è preparato con le versioni di tree-sitter dell'immagine e il server gira in un ambiente `uv` con altre versioni.
- **phazly, area:** la forma è vicina al riferimento (attore, paywall, scheda abbonamento, Stripe, entità), ma il taglio è più fine (un nodo per gestore: avvio del pagamento, portale clienti, ricezione degli eventi, dove il riferimento ha «API acquisti») e mancano Google Play Billing, i limiti d'uso e i consumi. Un flusso si ritrova con due terzi dei suoi nodi: con 3 o 4 nodi ritrovati su 11 nessun flusso arriva alla soglia.
- **phazly, intero sistema:** da 2 a 7 nodi per tutto il prodotto (accesso, editor dei pasti, modelli LLM, cancellazioni programmate); l'area dei pagamenti non compare.

Dopo questa tornata il tetto della scheda torna a 24.000 caratteri, perché la risposta di `brief` resti sotto il limite dell'host. Il modello dell'agente non è fissato: nessuno dei due supera la misura 1.

### Misure da 1 a 5, seconda tornata, 12 novembre 2026

Corretti i tre blocchi della prima tornata: il rapporto di `map` conta per cartella ciò che la copertura lascia fuori quando l'elenco supera 40 voci, il run si prepara con l'ambiente del server MCP, ogni run ha un container suo. Tetto della scheda 24.000, `HOLDERS` 8. Stesse 16 run (tag `system-map-runs2`), tutte partite, 1,37 USD. Nessuna risposta degli strumenti supera il limite dell'host salvo un rapporto su phazly, intero sistema, Haiku (16 flussi in una proposta). Valori per run in `results/runs2-20261112.json`.

| Misura | Risultato | Soglia |
| --- | --- | --- |
| 1 Riproduzione, phazly area | nodi ritrovati: Haiku 1 e 2, Sonnet 3 e 1 su 11; flussi 0 su 3; frecce rifiutate 0% | non raggiunta |
| 1 Riproduzione, phazly intero sistema | 0 nodi su 11 in tutte e quattro le run | non raggiunta |
| 2 Secondo progetto, tududi | frecce provate o dichiarate 57 su 60 (95%), solo 4 provate; nomi letti a mano 8 su 10 (vedi sotto) | raggiunta |
| 3 Livelli | da 5 a 50 viste per run sui due casi: nessun nodo fuori dal suo livello, nessun punto citato che manca | raggiunta |
| 4 Costo | area: Haiku da 0,008 a 0,010 USD, Sonnet da 0,11 a 0,20; intero sistema: Haiku da 0,010 a 0,019, Sonnet da 0,13 a 0,26; aperture del sorgente da 0 a 2 | raggiunta |
| 5 Stabilità | nodi uguali fra le due ripetizioni: da 0% a 55%; il migliore è tududi, intero sistema, Haiku (6 su 11) | non raggiunta |

Nomi letti a mano (tududi, area, Sonnet, prima ripetizione, e due nodi dell'intero sistema): giusti API abbonamenti, Gestione abbonamenti, Pagina admin fatturazione, Provider di pagamento, Scheda Abbonamento, Utente, Assistente MCP, Piano del giorno; sbagliati Client abbonamenti (il nome del codice, non della cosa) e Gateway di pagamento (un nodo solo per Stripe, Paddle e Lemon Squeezy, che il registro riconosce uno per uno).

Cause di ciò che non raggiunge la soglia:

- **La correzione toglie ciò che era stato accettato.** Una proposta con `scope` toglie i flussi non confermati dell'area che non riporta; l'agente corregge mandando solo ciò che è stato rifiutato, e così perde i flussi accettati e i loro nodi. Il rapporto della correzione toglie da 3 a 5 nodi e flussi in 5 run su 8 dell'area (3 su 4 su phazly, 2 su 4 su tududi): su phazly, area, Sonnet, sparisce «Abbonarsi a un piano» con il Paywall. È la causa principale della misura 1 e della misura 5, e la regola di `system-map.md` («Correct what was refused once») non la previene.
- **Pochi nodi per area.** Da 2 a 8 nodi dove il riferimento ne ha 11: mancano Google Play Billing, i limiti d'uso e i consumi; il taglio segue i gestori (ricezione degli eventi, stato nell'app) più che le cose che una persona nomina.
- **L'intero sistema in una proposta** dà da 2 a 18 nodi per tutto il prodotto, spesso un file per nodo, e l'area dei pagamenti si riduce a un nodo.

Dopo questa tornata una proposta non toglie più ciò che non nomina, e una freccia verso un membro indicato come funzione si prova anche sul file, dichiarandosi meno precisa: su phazly, area, Sonnet, prima ripetizione, le tre frecce rifiutate alla prima proposta reggevano al livello del file (il Paywall chiama `useSubscription`, e il membro indicato era `SubscriptionProvider` nello stesso file).

Il modello dell'agente non è fissato: Haiku e Sonnet stanno entrambi sotto le misure 1 e 5, e la differenza fra i due (1-2 contro 1-3 nodi su phazly) è più piccola della variazione fra ripetizioni.

### Candidati e frecce senza modello, phazly, 13 novembre 2026

Prova a costo zero della revisione del 13 novembre della spec, sui collegamenti di phazly già calcolati con il motore: `python candidates.py LINKS.json expected/phazly-payments.json FILES.txt`. I candidati sono la partizione per dominatori del grafo dei file dai punti d'ingresso; le chiavi di store sono un candidato ciascuna.

| Cosa | Risultato |
| --- | --- |
| Candidati | 408, di cui 123 chiavi di store; 360 hanno un solo file |
| File di codice | 386 in un candidato, 618 che nessun punto d'ingresso raggiunge |
| Candidati con file di due nodi del riferimento | nessuno |
| Nodi del riferimento come unione di candidati | Funzioni a consumo, API diritti, Abbonamento, Consumi interi; API acquisti 9 file su 11; Paywall 2 su 4; Scheda abbonamento 2 su 5. I file mancanti sono raggiunti da nessun punto d'ingresso |
| File che i candidati aggiungono ai nodi del riferimento | 22 a Funzioni a consumo e 2 ad API diritti: le funzioni di supporto dei gestori, che il riferimento non elenca |
| Frecce del riferimento fra nodi con codice ricavate dai soli collegamenti | 5 su 6: Paywall → API acquisti (4 chiamate), API acquisti → Abbonamento (7 scritture, 14 letture all'indietro), Funzioni a consumo → API diritti (11 chiamate), API diritti → Abbonamento (2 scritture, 3 letture) |

- La freccia mancante, API diritti → Consumi, è un buco del grafo non dichiarato: `services/usage.py` scrive e legge con `db[USAGE_EVENTS_COLLECTION]`, una forma che le regole di phazly non leggono.
- Scheda abbonamento → API acquisti arriva come Scheda abbonamento → Paywall (5 chiamate al contesto dell'abbonamento, che il riferimento mette nel Paywall) e Paywall → API acquisti: secondo la spec sono due frecce, e il contesto dell'abbonamento è un candidato a sé.
- In più c'è una freccia vera che il riferimento non ha: API acquisti → API diritti, 13 chiamate.
- I file che nessun punto d'ingresso raggiunge sono soprattutto componenti dell'interfaccia: rendere un componente non è un collegamento, e chi lo rende non si vede. È il secondo buco del grafo da chiudere.
- I candidati sono troppo fini per la scheda così come sono: il raggruppamento oltre il tetto è da misurare.

### Flussi dai punti d'appoggio, phazly, 13 novembre 2026

Prova a costo zero dei flussi costruiti dalla macchina: `python anchors.py LINKS.json expected/phazly-payments.json expected/phazly-anchors.json`. Per i 3 flussi del riferimento i punti d'appoggio sono dati a mano, come li darebbe il modello dalla scheda: punti d'ingresso e chiavi di store, nessun percorso. La macchina prende ciò che sta su un percorso da una partenza a un arrivo, senza limite di passi.

| Flusso | Nodi del riferimento con codice attraversati | File estranei | Dove il grafo si ferma |
| --- | --- | --- | --- |
| Pagamento | API acquisti, Abbonamento; manca Paywall | 0 | `PaywallModal.handleCheckout` non raggiunge niente fuori dal suo file |
| Gestione abbonamento | API acquisti, Abbonamento; manca Scheda abbonamento | 0 | `SubscriptionCard.handleOpenPortal` e `handleSetRenewal`, come sopra |
| Paywall e limiti d'uso | Funzioni a consumo, API diritti, Abbonamento; mancano Consumi e Paywall | 0 | nessuna partenza raggiunge `mongo/usageEvents` |

- Nessun percorso si allarga: 0 file fuori dal riferimento in tutti e 3 i flussi, fra 4 e 6 file o chiavi per flusso.
- Ogni nodo mancante corrisponde a un buco del grafo già visto, e la prova lo localizza: l'interfaccia chiama le funzioni dell'abbonamento attraverso un contesto React (`startCheckout` da `useSubscription()`), e le regole non leggono `db[USAGE_EVENTS_COLLECTION]`. Nessuno dei due è dichiarato oggi.
- Nei tre flussi non ci sono servizi esterni: senza il grafo dei moduli, i collegamenti `usa` verso Stripe e Google Play mancano da questi dati.

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

Domanda: delle frecce e degli ingressi che mancano ai flussi di un riferimento, quanti darebbe un collegamento possibile, che la macchina propone senza affermarlo e un modello conferma o scarta. `possible.py` verifica le frecce fra nodi con codice con `system_map.verify`, prima con i soli collegamenti certi e poi aggiungendo i possibili; le frecce e gli ingressi su un servizio di altri li controlla nella loro direzione e sui simboli di ogni nodo (il ritorno di un webhook va dal modulo esterno al gestore, non il contrario). Generatori: `ritorno` (una rotta di una regola `offre` che nessuna chiamata del progetto raggiunge, nemmeno come candidata, in un file che usa un modulo esterno, è chiamata da quel modulo; le rotte trovate da un lettore come Noir non hanno un'offerta a cui unire le chiamate e sono contate a parte) e `incerto` (una chiamata con più rotte candidate va a ognuna). I conteggi per freccia e per ingresso sono elencati nel docstring di `possible.py`. Il contesto React e la chiave in una variabile non hanno un generatore: cadono in `mancante con lacuna` o `mancante`. Un collegamento possibile che non sta su nessuna freccia o ingresso del riferimento è contato in `outside_reference`, non come sbagliato: il 13 novembre i soli collegamenti hanno trovato una freccia vera che il riferimento non aveva. Prova del metodo: `test_possible.py`, sulla fixture `flow-model` con un webhook. Va misurato su tutti i casi con riferimento: la prova piccola dei 35 flussi ha già portato a una scelta sbagliata.

**Risultati, phazly, 22 novembre 2026** (riferimento dell'intero sistema: 38 flussi, 240 frecce; snapshot al commit del riferimento, regole di `benchmarks/phazly-flow/rules.json`, nessun modello). L'analisi è l'intera pipeline su Modal fino al passo `analyze` (`benchmarks/project-model/modal_pipeline.py --folder-out DIR --folder-stop analyze`, 41 minuti: Python, TypeScript, JavaScript, Rust e fogli di stile `fresh`, Kotlin fallito); il conteggio è `modal run benchmarks/system-map/modal_map.py::possible` sui file di quel giro caricati sul volume, con la stessa copia del codice che ha fatto l'indice (`DAODAN_CODE`): un indice del motore è letto solo dal codice che l'ha scritto, e un conteggio fatto con un codice diverso ripiega sul parser semplice senza errori (qui dava 13.621 chiamate e 64 frecce certe invece di 23.867 e 91).

| Frecce del riferimento | Prima: servizi di altri fuori dai collegamenti | Dopo: archi `usa` dalle chiamate nei pacchetti dei servizi |
| --- | ---: | ---: |
| `certo` | 91 | 101 |
| `possibile:ritorno` | 0 | 2 |
| `dichiarata` | 43 | 43 |
| `senza modulo` | 41 | 21 |
| `mancante`, `mancante con lacuna` | 39 | 47 |
| `non misurabile` | 26 | 26 |
| flussi con ogni effetto raggiunto: solo certi, con i possibili | 13, 13 | 14, 15 |
| archi `usa` nei collegamenti | 2 | 150 |
| collegamenti possibili `ritorno`, di cui fuori dal riferimento | 0 | 4, 3 |
| collegamenti possibili `incerto` | 0 | 0 |

Con gli archi `usa` precisi quattro servizi del riferimento hanno un modulo (Stripe, Firebase Authentication, MongoDB Atlas, Resend) e `ritorno` propone il ritorno di Stripe sul gestore del webhook: «Rinnovo e variazione dell'abbonamento» si chiude solo con quel possibile. Tredici servizi restano `senza modulo`: lo stack li riconosce da un host o da una variabile, non da un pacchetto, e gli archi precisi nascono solo da un pacchetto. Le frecce `senza modulo` che ora hanno un modulo ma nessuna prova passano a `mancante`. I tre possibili fuori dal riferimento non sono stati letti uno per uno. Prima degli archi `usa` precisi i collegamenti non avevano alcun servizio di altri: il grafo dei moduli di phazly ha 13 moduli, tutti interni. Non misurato: gli altri casi con riferimento, e il conteggio dopo le correzioni ai lettori dei framework (i pulsanti su un componente e le rotte scritte nel codice oggi si perdono).

## Confronto proposto per i flussi multilivello

Protocollo per la [spec del 18 novembre](../../docs/specs/2026-11-18-flussi-e-mappa-del-sistema.md). **Confronto proposto, ancora da eseguire su Modal.**

**Scoperta cieca.** Ogni variante riceve la stessa richiesta, «analizza questo sistema», e lo stesso snapshot completo. Il mapper vede i normali artefatti dell'analisi, inclusi i nomi presenti nel prodotto. Prompt, regole e card accessibili al mapper devono essere privi di etichette provenienti dal valutatore o da mappe di flussi già compilate per la prova. I riferimenti manuali, le aree attese, i nomi e il numero di processi e rami rimangono fuori dall'ambiente dell'agente. Il valutatore li confronta con la mappa salvata **prima** di formulare richieste di review.

| Variante | Compito |
| --- | --- |
| A, attuale | Eseguire il mapper attuale sull'intero sistema. |
| B, grafo | Partire da ingressi ed effetti dell'intero inventario. Il modello identifica processi e varianti. La macchina verifica i percorsi. |
| C, grafo e card | Come B, aggiungendo l'accesso mirato alle card di simbolo aggiornate. B e C possono richiedere gli stessi estratti di sorgente. |

**Casi.** Su Phazly valutare dopo la scoperta i tre flussi noti dell'area pagamenti. Il riferimento storico copre quell'area soltanto. Gli altri flussi scoperti vanno giudicati a parte prima di contarli come errati. Per misurare la scoperta di un intero sistema, predisporre in repository una fixture con inventario manuale indipendente ed esaustivo. Deve comprendere più funzionalità, una funzionalità con ramo utente e cron, un modulo condiviso con un altro processo e un effetto il cui ingresso resta irrisolto. Gli estremi dati a mano nella prova del 13 novembre restano un controllo separato del tracciatore.

**Parametri e misure.** Fare due ripetizioni indipendenti per variante e caso, a parità di grafo, modello, tetto di contesto e budget. Registrare flussi e varianti mancanti, estranei, accorpati o duplicati, verificandoli per ingressi, effetti e membri anche quando il nome differisce. Contare gli estremi spiegati, esclusi con motivo, irrisolti e non esaminati. Misurare token osservati di input e output, aperture e costo dell'intero run, distinguendo riuso e prima generazione delle card. Valgono le soglie storiche applicabili per riproduzione sull'area di riferimento, stabilità e costo a sistema. Il riferimento parziale di Phazly non misura il richiamo globale.

**Criteri sulla fixture completa.** Il mapper deve scoprire tutti i processi e tutte le varianti attesi, conservare il modulo condiviso una sola volta e rendere conto di ogni estremo, inclusa l'origine irrisolta. Nessun arco causale senza evidenza. Aprire il processo deve mostrare i due rami e richiuderlo deve ripristinare la selezione, con zero chiamate LLM. Solo a questo punto chiedere una review della funzionalità e poi del solo ramo automatico. Nel primo caso sono attesi entrambi i percorsi, nel secondo il gestore del cron e il codice condiviso pertinente. In entrambi i casi verificare la motivazione dei file, i file di solo contesto e le lacune rispetto al riferimento.

A qualità uguale si preferisce il minor consumo totale osservato. Se il grafo non espone un ingresso o un effetto, attribuire l'omissione alla raccolta delle evidenze. Se il riferimento è visibile al modello e viene interpretato male, attribuirla alla scoperta semantica. **Risultati del nuovo protocollo e fixture completa: da produrre.**

### Scoperta cieca con il modello debole, variante A, 21 novembre 2026

`python modal_map.py spawn --tag collaudo-cieco-haiku --cases CASO --tar CASO=ARCHIVIO --rules session --scopes system --models haiku --reps 2 --budget 1`, poi `python score.py system` su ogni `map.json` (`results/system/collaudo-cieco-haiku/`). Caso: il più piccolo con riferimento dell'intero sistema (49 nodi confrontabili, 19 flussi, 22 ingressi, 24 effetti); archivio di solo codice sul commit del riferimento (178 file, nessun segreto trovato). Il riferimento resta fuori dall'ambiente dell'agente ed è confrontato dopo il salvataggio.

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

Preparazione 320 secondi; nessuna run fermata dal tetto. Il mapper elenca le schede dei percorsi e passa alla proposta libera senza aprirne una. Le otto run precedenti di Haiku sullo stesso caso (`sysmap-a7-haiku`, `sysmap-gate-b-haiku`, `sysmap-gate-b2-haiku`, `sysmap-c1-haiku`), rivalutate con lo `score.py` di oggi: 0 flussi su 19, 0 ingressi e 0 effetti in tutte; nodi da 3 a 9 su 49. Con `--models qwen` la sessione delle regole si è fermata dopo 1.574 secondi: il gateway rifiutava la connessione. Limiti: un solo caso; il passaggio del motore di queste run gira senza il container di Daodan; varianti B e C e fixture completa non eseguite.

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

### Intera analisi senza modello, cinque casi, 23 novembre 2026

`python benchmarks/system-map/modal_map.py whole --tag whole-nomodel-1 --cases phazly,hostay,qamille,qamille-enterprise,poc-data-extraction --tar CASO=ARCHIVIO ...` (archivi di `code_archive.py` sul commit dei riferimenti, nessun modello), poi `modal volume get daodan-flow-results whole-nomodel-1 results/system/` e `python score.py whole results/system/whole-nomodel-1`. Il job di ogni caso ha scritto archivio, stato della pass e candidati; il motore Modal ha dato indici `fresh` per tutti i linguaggi, con Kotlin `failed` solo in phazly. Colonna degli ingressi del riferimento (trovati su contati, il lettore che ne trova di più per tipo):

| Caso | Controlli | Rotte | Messaggi | Orari | Comandi | Candidati non ingressi (residuo) | File non raggiunti |
| --- | --- | --- | --- | --- | --- | --- | --- |
| hostay | 19/19 (residuo) | 2/2 (next) | 4/4 (residuo, decoratore, noir) | 7/7 (decoratore) | — | 2.057 su 2.286 | 348 su 1.163 |
| phazly | 1/1 (residuo, argomento) | 1/2 | 2/2 (residuo) | 2/2 | — | 2.721 su 2.825 | 1.285 su 2.393 |
| poc-data-extraction | 7/7 (residuo, argomento) | — | 1/1 | 1/1 | 10/11 (residuo) | 480 su 559 | 77 su 175 |
| qamille | 17/18 (argomento) | 3/3 | 2/3 | 7/7 | 1/1 | 3.868 su 4.185 | 380 su 1.005 |
| qamille-enterprise | 21/22 (argomento) | 5/5 | 2/4 | 8/9 (residuo) | 2/5 | 4.177 su 4.510 | 427 su 1.095 |

«Ingresso omesso» in tutti i casi (l'archivio lascia fuori da 10 a 2.507 file). Segreti mascherati nell'archivio: da 0 a 13. Non misurato, con la causa: schede dei percorsi con modello, ricerca, controllo e gestore giusti. In phazly un candidato del lettore `observed` (un controllo trovato dal browser nell'app di amministrazione, nella sandbox) non aveva `symbol` e `entries.py measure` si fermava: ora lo conta al file del suo gestore. Non misurati: tempo e costo del giro.

Con Haiku 5.5, 23 e 24 novembre 2026: `python modal_map.py whole --tag whole-nomodel-1 --no-cases --cases ... --models haiku --reps 2 --budget 1`, 10 run indipendenti (ognuna prepara per sé, scrive le sue regole e poi mappa); `score.py whole` sul tag.

| Caso | Costo sessioni | Nodi | Flussi | Ingressi | Effetti | Stabilità fra due ripetizioni |
| --- | --- | --- | --- | --- | --- | --- |
| hostay | 0,48 | 5 su 98 | 0 su 35 | 0 su 48 | 0 su 38 | 5 su 7 |
| phazly | 0,76 | 7 su 118 | 0 su 38 | 0 su 48 | 0 su 50 | 5 su 12 |
| poc-data-extraction | 0,26 | 4 su 49 | 0 su 19 | 0 su 22 | 0 su 24 | 3 su 14 |
| qamille | 0,26 | 3 su 95 | 0 su 29 | 0 su 34 | 0 su 34 | 3 su 6 |
| qamille-enterprise | 0,26 | 0 su 129 | 0 su 39 | 0 su 47 | 0 su 47 | 1 su 3 |

Totale 2,02 dollari, nessuna fermata per budget. La pass del motore: 51-68 minuti in phazly (una run è scaduta a 3600 secondi senza pagare sessioni; il limite è ora di 2 ore), 7-20 minuti negli altri. Non misurati: i token e il tempo delle sessioni, Qwen e Opus.

