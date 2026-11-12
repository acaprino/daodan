# Benchmark: mappa del sistema

Prova la [spec della mappa del sistema](../../docs/specs/2026-11-12-mappa-del-sistema.md), misure da 1 a 6. Le soglie sono scritte qui prima di ogni misura; il proprietario può cambiarle. I casi sono quelli dei benchmark dei flussi, che hanno già le regole di collegamento: [`phazly-flow`](../phazly-flow/README.md), [`polar-flow`](../polar-flow/README.md) e [`tududi-flow`](../tududi-flow/README.md). Il codice dei casi non entra qui: solo nomi di file e valori attesi. Le run girano su Modal, in un processo nuovo.

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
| 1, 2, 4, 5 | `python score.py map MAP.json expected/phazly-payments.json` sulla mappa salvata dalla run |
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
