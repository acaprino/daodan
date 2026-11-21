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
| tetto della scheda (`system_brief.CAP`) | 12.000, 24.000, 48.000 caratteri |
| punti d'ingresso mostrati per gruppo (`HOLDERS`) | 5, 8, 12 |
| modello dell'agente | economico (Haiku 5.5), intermedio (Sonnet 5.5) |
| perimetro | un'area, l'intero sistema |

## Riferimenti attesi

- `expected/phazly-payments.json`: gli 11 nodi e i 3 flussi (pagamento, gestione abbonamento, paywall e limiti d'uso) del grafo d'insieme della mappa fatta a mano il 12 novembre 2026, confermati dal proprietario lo stesso giorno; i 35 percorsi sono letti dall'archivio di phazly. Il pagamento dal web e il suo ritorno (`SubscriptionContext.tsx`, `CheckoutVerificationOverlay.tsx`, `checkout-complete/index.html`) stanno nel Paywall, gli avvisi di prova e scadenza nella Scheda abbonamento; Abbonamento e Consumi sono le chiavi `mongo/subscriptions` e `mongo/usageEvents`; la Landing è un nodo non visto. Un nodo con codice si ritrova per file e chiavi di store, un nodo senza codice se un nodo nella stessa posizione cita uno dei suoi file, un nodo non visto per posizione e tipo.
- `expected/externals-<caso>.json`: per ogni caso l'elenco a mano letto dai manifest, dai Dockerfile, dai file compose e dai modelli di `.env` del perimetro dello snapshot (`read`). In `externals` stanno ogni servizio esterno che quei file nominano e i progetti con un ruolo nell'architettura (framework dell'applicazione, guscio dell'app, accesso ai dati, stato, code, container), come la mappa fatta a mano di phazly ne nomina 6 su 59 pacchetti. In `also` stanno le cose usate che una persona non nomina (linguaggi, strumenti di build, stile, test e lint, librerie di utilità): non contano per il richiamo né come errore. Un identificatore che il registro non ha è scritto come nome semplice (`zustand`, `google-play-billing`).

## Esecuzione

| Misura | Comando |
| --- | --- |
| 1, 2, 4, 5 | `modal deploy benchmarks/system-map/modal_map.py`, poi `python benchmarks/system-map/modal_map.py spawn --phazly-tar PATH --phazly-links PATH --tududi-links PATH --tag TAG`: una run per caso, perimetro, modello e ripetizione, ognuna una sessione nuova di `claude -p --agent codebase-map:system-mapper` su un run di Codebase Map preparato prima con le regole del caso e i collegamenti calcolati con il motore; sul volume `daodan-flow-results` restano `stream.jsonl`, `map.json` e `summary.json`. Poi `python score.py map map.json expected/phazly-payments.json` |
| 3 | `map.json` di ogni run riporta in `levels` i nodi fuori dal loro livello e i punti citati che non esistono, per ogni flusso registrato e ogni livello |
| 6, dimensione della scheda | `modal run benchmarks/system-map/modal_map.py::brief --phazly-tar PATH --phazly-links PATH` scrive `results/brief-<caso>.json`; poi `python score.py externals results/brief-<caso>.json expected/externals-<caso>.json registry` (oppure `stack-analyser`, `both`) |

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

### Tre percorsi con gli indicizzatori veri, 21 novembre 2026

Eseguire `python benchmarks/system-map/real_paths.py [web] [tk] [tauri] [--work DIR]` con le dipendenze di Daodan e un motore di container (su Windows quello di Daodan). Parametri: il caso (`benchmarks/flow-model/app`, `real-paths/tk-desk`, `real-paths/tauri-desk`), le regole e le risposte sulle forme del caso, la disposizione (analisi accanto al checkout). Lo script crea il run dal servizio con il passaggio del motore, legge i candidati prima delle regole, registra regole e risposte, apre ogni scheda e controlla ciò che deve reggere; esce con 1 se un controllo cade.

| Caso | Indicizzatori nel container | Secondi | Controllo, gestore, ultimo punto provato |
| --- | --- | ---: | --- |
| web | scip-python 0.6.8, scip-typescript 0.6.2 | 129 | «Paga» `web/checkout.ts:22` → `onPayClick` → `submitPayment` → `store:web state/payment` (`web/checkout.ts:14`) |
| tk | scip-python 0.6.8 | 106 | «Salva» `ui.py:8` → `App.save` (gestore dato dall'indice) → `store:disk/orders` (`ui.py:11`) |
| tauri | scip-typescript 0.6.2, rust-analyzer 2026-11-09 | 322 | «Salva profilo» `src/view.tsx:18` → `save` → `src-tauri/src/main.rs::persist` (`tauri-invoke`, `src/view.tsx:4`); `only_in_tests` e `on_idle_builder` restano lacune |

Il caso Tauri prima falliva: con il ripristino Node condiviso `tsc` e scip-typescript non trovavano `node.tar.gz` (spec della pipeline, sezione 7.1). Con 6,4 GB liberi rust-analyzer non parte (ne chiede 8) ed è una lacuna con la causa. Le stesse tre fixture su Modal (`modal_pipeline.py --folder-out`): indici `fresh` in 132, 100 e 242 secondi; lì i test Rust non partono per le librerie di sistema che mancano. Le fixture non dichiarano test: nessun arco osservato.

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
