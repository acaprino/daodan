# Benchmark: mappa del sistema

Prova la [spec della mappa del sistema](../../docs/specs/2026-11-12-mappa-del-sistema.md), misure da 1 a 6. Le soglie sono scritte qui prima di ogni misura; il proprietario può cambiarle. I casi sono quelli dei benchmark dei flussi: [`phazly-flow`](../phazly-flow/README.md), [`polar-flow`](../polar-flow/README.md) e [`tududi-flow`](../tududi-flow/README.md). Le regole di collegamento ci sono per phazly e per tududi (`benchmarks/tududi-flow/rules.json`, scritte a mano il 12 novembre 2026 per la misura 2: store di Zustand, chiamate `fetch(getApiPath(...))`, rotte di Express, modelli di Sequelize). Il codice dei casi non entra qui: solo nomi di file e valori attesi. Le run girano su Modal, in un processo nuovo.

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
