# Benchmark: la stessa cosa in due posti

**Stato:** In uso. Il ruolo `prior-art-auditor` è nel prodotto (`daodan/review/roles/prior-art-auditor.md`) con la correzione misurata qui.

**Domanda.** I reviewer trovano, in una modifica, ciò che il codice sa o fa due volte: copie di una regola, due percorsi per lo stesso effetto, lo stesso controllo ripetuto e il codice che gestisce più casi perché non sa quale vale?

**Risultati validi oggi** (16-17 novembre 2026, Sonnet):

| Fixture | `prior-art-auditor` corretto | Confronto (`local-correctness-auditor` e `logic-integrity-auditor`) |
|---|---|---|
| `shop/` | 5 semi su 5 | 2 finding, 3 note |
| `booking/` | 5 su 5 | 1 finding, 1 nota |
| `parcel/` | 3 su 3 in tre run | non eseguito |

Nessuna esca segnalata in nessuna run. Tutte le misure usano un modello; senza modello ci sono solo i test che dimostrano semi ed esche. Le fixture sono lette per intero dal worker: la ricerca delle copie attraverso la mappa (indice lessicale, grafo, schede) in un codebase grande non è misurata, né con un modello né senza.

## Parametri

| Parametro | Valore |
|---|---|
| prova | `prior-art-auditor`, il ruolo che la review aggiunge al rigor `deep` |
| confronto | `local-correctness-auditor` e `logic-integrity-auditor` insieme: i due membri di `code-auditor`, presente a ogni rigor, i cui mandati nominano percorsi alternativi, ripieghi e proprietari di un fatto |
| richiesta | «Rivedi la modifica: aggiunge …» con il diff e l'albero candidato |
| esecuzione | un `senior-review:isolated-worker` per configurazione, con i file ruolo come istruzioni e `CLAUDE_PLUGIN_ROOT` sulla copia del plugin; sola lettura, nessuna esecuzione |
| modello | Sonnet, uguale per tutte le configurazioni |
| fixture | copia in una directory vuota: albero candidato e diff; il worker non vede README, test né risultati attesi |
| mappa | nessuna run: la fixture ha sette file e il worker li legge direttamente; la ricerca attraverso la mappa non è misurata |
| verifica | lenti 1 e 2 di `panel-and-critic-prompts.md` sui semi delle run indicate nelle tabelle, un worker per lente |

Esito di un seme: `sì` se è un finding che nomina i due posti (per un'incertezza: i casi gestiti e l'unico produttore), `nota` se il ruolo lo registra senza farne un finding, `no` altrimenti. Un'esca è segnalata se un finding la dichiara doppione, controllo ridondante o caso senza produttore; un finding nello stesso punto che dice altro conta tra gli altri finding.

Criterio, dichiarato prima delle run:

- Giro 1 misura i ruoli come sono. Si corregge il ruolo per ogni seme che la prova non trova o che le lenti scartano con due `FALSE_POSITIVE`.
- Giro 2 usa un'altra fixture, con semi scritti prima della correzione. La correzione resta se il ruolo corretto trova almeno un seme in più del ruolo al commit precedente, non segnala un'esca e nessun seme trovato è scartato dalle lenti.
- Giro 3, aggiunto dopo il giro 2 e prima di scrivere la correzione. Il giro 1 non ha chiesto correzioni: la correzione nasce dalle run del giro 2 con il ruolo attuale, quindi `booking/` non è più una prova mai vista. `parcel/` ha semi delle sole due classi mancate e due esche che una correzione troppo larga segnalerebbe. Vale il criterio del giro 2 su `parcel/`, con due run per configurazione; in più il ruolo corretto ritrova ogni seme di `shop/` e `booking/` senza segnalarne le esche.

## Prove senza modello

`python -B -m pytest -q benchmarks/prior-art`

`test_shop.py`, `test_booking.py` e `test_parcel.py` dimostrano ogni seme e ogni esca: i test passano sulla fixture così com'è.

Ultima esecuzione registrata: 17 novembre 2026 sul commit `f992db5609c72cd8bdc0d0d9c5da8696acade82a`, **21/21 test passati** con `python -B -m unittest discover -s benchmarks/prior-art -v`, Python 3.13.18 su Linux, nel container Daodan su Kiri 0.2.1, senza rete né mount dell'host.

## Run con il modello

1. Copiare in una directory vuota `<fixture>/`, `<fixture>.diff` e il plugin della configurazione in `plugin/`.
2. Un worker nuovo per configurazione, vincolato alla directory, con la richiesta e i file ruolo.
3. Registrare finding con `file:line`, token, strumenti usati e tempo.
4. Un worker per lente su ogni seme trovato, con il testo del finding, il diff e il file.

## Giro 1: `shop/`

Sette file, circa 150 righe: catalogo, prezzi, ordini e ingresso HTTP. La modifica (`shop.diff`) aggiunge i resi (`returns.py`), una statistica (`stats.py`) e la validazione dell'ingresso (`api.py`).

| Seme | Dove | Cosa | Esempio |
|---|---|---|---|
| S1 | `returns._clean_sku` contro `catalog.normalize_sku` | Copia che si comporta già in modo diverso: non toglie i trattini | Reso di `ab-12`: rimborso 0,00 invece di 39,80 |
| S2 | `returns._total` contro `pricing.lines_total` | Rifacimento con lo stesso risultato su ogni ingresso | — |
| S3 | `returns.void` contro `orders.cancel` | Secondo percorso per lo stesso effetto: stesso controllo di stato, stesso ritorno a scorta | — |
| S4 | `api.post_order` contro `orders.place` | Lo stesso controllo di quantità ripetuto sullo stesso percorso, con `20` scritto a mano al posto di `MAX_QTY` | — |
| S5 | `returns._customer_id` | Incertezza: gestisce dizionario con due chiavi, oggetto e valore nudo; l'unico produttore, `orders.place`, scrive `{"id": …}` | — |

Esche: `stats.round_avg` arrotonda diversamente da `pricing.round_cents` apposta, e lo dichiara (E1); il controllo di tipo in `api.post_order` ferma ciò che il controllo di intervallo del dominio non sa giudicare (E2).

Run del 2026-11-16, ruoli al commit `3be871d8d`.

| Configurazione | S1 | S2 | S3 | S4 | S5 | Altri finding | Esca segnalata | Token | Strumenti | Tempo |
|---|---|---|---|---|---|---|---|---|---|---|
| `prior-art-auditor` | sì | sì | sì | sì | sì | 0 | no | 42.776 | 5 | 145 s |
| confronto | sì | nota | nota | nota | sì | 7 | no | 57.129 | 17 | 194 s |

| Lente | S1 | S2 | S3 | S4 | S5 |
|---|---|---|---|---|---|
| 1, raggiungibilità | REAL 95 | REAL 85 | REAL 88 | REAL 88 | REAL 85 |
| 2, cause di falso positivo | REAL 90 | REAL 85 | REAL 88 | REAL 85 | REAL 80 |

- Le lenti hanno giudicato i finding di `prior-art-auditor`: dieci worker, 216.684 token in tutto. Nessun seme è scartato, nemmeno quelli senza differenza di comportamento (S2, S3, S4).
- Il confronto registra S2, S3 e S4 come note («rischio di deriva soltanto») e non ne fa finding: al rigor `standard` e nella review prima del commit, dove `prior-art-auditor` non c'è, restano fuori dal rapporto.
- S5: entrambe le configurazioni lo legano a un difetto raggiungibile, l'`or` che scarta un identificativo 0 o vuoto. Il confronto lo segnala con confidenza 45, sotto la soglia di verifica.
- Gli altri finding del confronto non sono dimostrati dai test: tra questi `body["lines"]` letto fuori dal `try` in `api.post_order`, una regressione non voluta della fixture, che `prior-art-auditor` annota a margine come fuori ruolo.
- `prior-art-auditor` segnala nel rapporto che il ruolo si contraddice: «un comportamento identico è un finding» e «una seconda occorrenza si registra senza finding». Ha scelto la prima regola.
- Lo strumento di scrittura dell'host ha rifiutato il file di rapporto: i worker hanno consegnato il rapporto come testo.
- Nessun seme da correggere secondo il criterio.

## Giro 2: `booking/`

Sette file, circa 140 righe: sale, fasce orarie, prenotazioni e calendario. La modifica (`booking.diff`) abbassa la durata massima da 4 a 3 ore e aggiunge conferme via email (`mail.py`), importazione (`imports.py`), prenotazioni ricorrenti (`recurring.py`) e la regola delle pulizie (`slots.needs_gap`).

| Seme | Dove | Cosa | Esempio |
|---|---|---|---|
| R1 | `view.can_extend` contro `rooms.MAX_HOURS` | La modifica aggiorna una copia della soglia e non l'altra, che sta fuori dal diff | Prenotazione di 3 ore: il pulsante «Estendi» compare, l'estensione è rifiutata |
| R2 | `mail._title` contro `view.label` | Rifacimento con lo stesso risultato, scritto in altro modo | — |
| R3 | `imports.load` contro `bookings.create` | Secondo percorso per lo stesso effetto: stessi controlli, stesso record | — |
| R4 | `recurring.book_weekly` contro `bookings._check` | Gli stessi due controlli ripetuti prima di chiamare chi li fa già | — |
| R5 | `mail._owner` | Incertezza: ripiega su `user` e `created_by`; ogni produttore scrive `owner` | — |

Esche: `slots.needs_gap` usa estremi inclusi apposta, e lo dichiara (F1); `mail.SENDER` ha un predefinito documentato (F2).

Run del 2026-11-16, ruoli al commit `3be871d8d`: il ruolo com'è, due volte, e il confronto.

| Configurazione | R1 | R2 | R3 | R4 | R5 | Altri finding | Esca segnalata | Token | Strumenti | Tempo |
|---|---|---|---|---|---|---|---|---|---|---|
| `prior-art-auditor`, run 1 | sì | sì | sì | sì | no | 1 | no | 50.888 | 8 | 197 s |
| `prior-art-auditor`, run 2 | sì | sì | sì | nota | no | 0 | no | 36.671 | 6 | 113 s |
| confronto | sì | no | no | no | nota | 6 | no | 45.030 | 15 | 146 s |

- R5: entrambe le run lo vedono e lo instradano ad `application-reachability` come codice morto, per la riga del ruolo «dead code to application-reachability». Quel ruolo cerca simboli senza consumatore, non rami per forme che nessuno scrive. Nel giro 1 S5 era uscito perché nascondeva un difetto raggiungibile; qui l'incertezza è pura e non diventa un finding.
- R4: finding con confidenza 50 in una run, nota nell'altra («i valori non possono divergere»). Il ruolo non nomina il controllo ripetuto lungo un percorso.
- R1: trovato da tutti, anche se la copia rimasta indietro sta fuori dal diff.
- Il confronto trova solo R1, che è già un difetto, e non nomina R2, R3 e R4.
- Altro finding della run 1, reale: la regola delle pulizie vale solo in `book_weekly`, quindi una prenotazione successiva può togliere l'ora libera.
- Correzione motivata: R5 mai trovato, R4 instabile.

## Giro 3: `parcel/`

Otto file, circa 110 righe: spedizioni, stati, addebiti e importazione dal vecchio gestionale. La modifica (`parcel.diff`) aggiunge l'affidamento al corriere (`dispatch.py`), le notifiche del corriere (`webhook.py`) e le etichette (`labels.py`).

| Seme | Dove | Cosa | Esempio |
|---|---|---|---|
| T1 | `webhook.on_event` contro `tracking.add_event` | La stessa guardia di esistenza ripetuta prima di chiamare chi la fa già, senza nulla in mezzo | — |
| T2, ritirato | `webhook.on_event` contro `tracking.add_event` | Dichiarato come controllo dello stato contenuto in quello del chiamato. Non lo è: per una spedizione consegnata `add_event(id, None)` passa e scrive `None`, e solo il controllo del webhook lo ferma | — |
| T3 | `labels._history` | Incertezza: gestisce `None` e un valore che non è una lista; ogni produttore scrive una lista | — |
| T4 | `labels.STATUSES` contro `tracking.NEXT` | Incertezza: rifiuta uno stato fuori da un elenco copiato; nessun produttore ne scrive altri | Un nuovo stato in `NEXT`: l'etichetta di una spedizione valida è rifiutata |

Esche: `labels._recipient` gestisce il destinatario come testo perché `legacy.load` lo scrive davvero così (D1); `dispatch.ship` controlla lo stato prima dell'addebito, e senza quel controllo il conto verrebbe addebitato prima del rifiuto di `add_event` (D2).

Run del 2026-11-16: il ruolo al commit `3be871d8d` e il ruolo corretto, due volte ciascuno.

| Configurazione | T1 | T3 | T4 | Altri finding | Esca segnalata | Token | Strumenti | Tempo |
|---|---|---|---|---|---|---|---|---|
| ruolo al commit, run 1 | sì | no | sì | 2 | no | 43.564 | 13 | 145 s |
| ruolo al commit, run 2 | sì | no | sì | 3 | no | 48.578 | 11 | 166 s |
| ruolo corretto, run 1 | sì | sì | sì | 1 | no | 42.277 | 13 | 138 s |
| ruolo corretto, run 2 | sì | sì | sì | 2 | no | 43.807 | 6 | 148 s |

| Lente, sui finding del ruolo corretto run 1 | T1 | T3 | T4 |
|---|---|---|---|
| 1, raggiungibilità | REAL 75 | REAL 60 | REAL 72 |
| 2, cause di falso positivo | REAL 62 | REAL 75 | REAL 70 |

- T3: il ruolo al commit lo instrada ad `application-reachability` in entrambe le run, come R5; il ruolo corretto lo segnala in entrambe con confidenza 80. Le lenti lo tengono anche senza un difetto raggiungibile oggi: sei worker, 134.286 token.
- T2: l'errore della fixture lo hanno trovato le run del ruolo al commit. Tutte e quattro le run descrivono il caso `None`; `test_parcel.py` lo dimostra. Non conta per nessuna configurazione.
- D1: nessuna run dice che il ramo è senza produttore. Il ruolo al commit apre comunque in entrambe le run un finding nello stesso punto, che chiede di convertire il formato in `legacy.load` (confidenza 55 e 50); il ruolo corretto in una run su due, con confidenza 40.
- D2: nessuna run chiama ridondante il controllo. La prima del ruolo al commit e la seconda del ruolo corretto segnalano i due stati scritti a mano al posto di `NEXT`, non il controllo.
- Difetto reale non seminato: `webhook.on_event` accetta `in_transit` e mette in viaggio una spedizione senza addebito. Il ruolo al commit lo trova in entrambe le run, il ruolo corretto in una su due. Due run non dicono se è un costo della correzione.

## Ruolo corretto

La correzione di `prior-art-auditor.md`, scritta dopo il giro 2 e dopo i semi di `parcel/`:

- un controllo per la stessa condizione valutata due volte su un percorso, senza effetti in mezzo;
- un controllo per ripieghi, predefiniti e guardie su casi che nessun produttore scrive;
- una sola regola al posto delle due che si contraddicevano su copia identica e seconda occorrenza;
- il ramo tenuto per un caso senza produttore resta al ruolo, invece di passare ad `application-reachability`.

Una run per fixture già vista, con il ruolo corretto.

| Fixture | Semi trovati | Altri finding | Esca segnalata | Token | Strumenti | Tempo |
|---|---|---|---|---|---|---|
| `shop/` | 5 su 5 | 0 | no | 47.263 | 6 | 141 s |
| `booking/` | 5 su 5 | 1 | no | 52.392 | 16 | 172 s |

- `booking/`: R5 con confidenza 80 e R4 con 65; il ruolo al commit ne trovava 4 e 3.
- Altro finding su `booking/`: la scansione stessa sala e stesso giorno è scritta in quattro punti.

Su `parcel/` il ruolo corretto trova T3 in entrambe le run e il ruolo al commit in nessuna, nessuna esca è segnalata, e su `shop/` e `booking/` ritrova ogni seme. Le lenti 1 e 2 non scartano i semi della prima run corretta di `parcel/`; la seconda run e le run corrette di `shop/` e `booking/` non sono state verificate dalle lenti. La correzione resta con questa copertura parziale della verifica prevista dal criterio.

Dopo queste run il testo del ruolo ha ricevuto tre ritocchi senza controlli nuovi: il mandato nomina il caso che nessuno produce, la regola del tre dice a quale seconda occorrenza si riferisce, l'output nomina la direzione «togliere» per il controllo ripetuto e per il caso senza produttore. Una run di conferma su `parcel/` il 2026-11-17 con il testo finale, non verificata dalle lenti:

| Configurazione | T1 | T3 | T4 | Altri finding | Esca segnalata | Token | Strumenti | Tempo |
|---|---|---|---|---|---|---|---|---|
| ruolo finale | sì | sì | sì | 1 | no | 42.926 | 14 | 135 s |

- Confidenza 90, 85 e 60; le tre direzioni dicono di togliere la copia o la gestione. D1 e D2 sono registrate come occorrenze necessarie.
- L'altro finding è il caso `None` di T2. Il difetto reale non seminato di `webhook.on_event` non compare: il ruolo corretto lo trova in una run su tre.

Limiti della misura: un solo modello; due run per configurazione su `parcel/` e una sulle altre; lenti 0 e 3 non eseguite. Il miglioramento sui controlli ripetuti riguarda R4 in una sola run corretta su `booking/`, fixture già vista; T1 e T4 su `parcel/` erano trovati anche prima. Non è separato se T3 lo fa trovare il nuovo controllo sui casi senza produttore o il solo cambio di instradamento: il ruolo al commit vedeva il ramo e lo passava ad `application-reachability`. Nessuna esca ha un `except` legittimo su I/O o timeout. Le fixture sono lette per intero: la ricerca attraverso la mappa in un codebase grande e il flusso completo al rigor `deep` restano non misurati.
