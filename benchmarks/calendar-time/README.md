# Benchmark: promemoria con orario fluttuante

Ha provato il ruolo `senior-review:calendar-time-auditor`, rimosso dopo il giro 2 perché non ha trovato nulla che i ruoli esistenti non trovino. Il ruolo doveva trovare dove un orario civile viene calcolato, mostrato o fatto suonare in modo incoerente tra fusi orari, ora legale, ricorrenze e cambi di fuso.

## Parametri

| Parametro | Valore |
|---|---|
| prova | `calendar-time-auditor` |
| confronto | `temporal-resilience-auditor` e `data-representation-auditor` insieme, al commit `4ac9475`: i due ruoli che prima del ruolo nuovo nominavano fusi e ora legale |
| richiesta | «Rivedi `<fixture>/`: ogni promemoria deve suonare alla sua ora nel fuso in cui si trova l'utente.» |
| esecuzione | un sotto-agente `general-purpose` dell'host per configurazione, con i file ruolo come istruzioni e `CLAUDE_PLUGIN_ROOT` sulla copia del plugin; può eseguire Python nella copia |
| modello | Sonnet, uguale per le due configurazioni |
| fixture | copia in una directory vuota: il worker non vede README, test né risultati attesi |

Criterio, uguale per ogni giro e dichiarato prima della run: il ruolo resta se trova almeno un seme che il confronto non trova, senza segnalare un'esca.

## Prove senza modello

`python -B -m pytest -q benchmarks/calendar-time`

`test_app.py` e `test_app2.py` dimostrano ogni seme e ogni esca: i test passano sulla fixture così com'è.

## Run con il modello

1. `d=$(mktemp -d) && cp -r benchmarks/calendar-time/<fixture> "$d"/` e una copia del plugin della configurazione in `"$d"/plugin`.
2. Un sotto-agente nuovo per configurazione, vincolato a `$d`, con la richiesta e i file ruolo.
3. Registrare finding con `file:line`, token, strumenti usati e tempo.
4. Confrontare con i risultati attesi: semi trovati, altri difetti reali, segnalazioni errate.

## Giro 1: `app/`

`app/reminders.py`, circa 60 righe: promemoria lato server, creazione, cambio di fuso, tick ogni minuto e scheda del giorno. Esca: gli istanti salvati in UTC sono corretti.

| Seme | Dove | Difetto | Esempio |
|---|---|---|---|
| S1 | `card` contro `ring_at` | La scheda e il suono risolvono in modo diverso l'orario che non esiste al cambio d'ora | Sydney, 4 ottobre 2026: la scheda mostra 02:30, suona alle 03:30 |
| S2 | `tick` | La ricorrenza aggiunge 24 ore all'istante: l'orario locale si sposta al cambio d'ora | Roma, dopo il 29 marzo 2026: suona alle 10:00 |
| S3 | `set_zone` | Il cambio di fuso non ricalcola il prossimo suono già pianificato | Da Roma a Tokyo: suona alle 17:00 invece delle 09:00 |
| S4 | `done_on` | «Fatto» confronta la data UTC del suono con il giorno locale | Tokyo, 08:00: dopo il suono la scheda resta «to do» |

Run del 2026-11-09, ruolo al commit `cf78d8b`.

| Configurazione | S1 | S2 | S3 | S4 | Altri reali | Esca segnalata | Token | Strumenti | Tempo |
|---|---|---|---|---|---|---|---|---|---|
| `calendar-time-auditor` | no | sì | sì | sì | 0 | no | 75.365 | 8 | 53 s |
| confronto | in parte | sì | sì | sì | 1 | no | 78.000 | 6 | 58 s |

- S1: il ruolo nota che l'orario inesistente è risolto da un default implicito, ma confronta `ring_at` con `tick`, non con la scheda. Il confronto osserva a margine che la scheda mostra l'ora della regola e non quella in cui suona, senza legarlo al cambio d'ora.
- Altro reale del confronto: con `every_days` uguale a 0 il ciclo di `tick` non termina e ferma tutti i promemoria.
- Criterio non raggiunto. Cause visibili prima dei risultati: un solo file con difetti evidenti, e un confronto con due ruoli concentrati mentre nelle review reali sono diluiti in composizioni più grandi.
- Correzione generale del ruolo dopo il giro: confrontare per ogni occorrenza l'orario mostrato con quello che suona.

## Giro 2: `app2/`

Quattro file, circa 90 righe: regola settimanale (`model.py`), pianificazione (`planner.py`), notifiche dal server, cambio di fuso e lista «Oggi» (`server.py`), allarmi locali del telefono come riserva offline (`device.py`). Il contratto sta nella docstring di `Rule`: al più una volta per data, nel fuso corrente. Semi diversi dal giro 1, scelti prima della correzione del ruolo.

| Seme | Dove | Difetto | Esempio |
|---|---|---|---|
| R1 | `device.local_alarms` contro `planner.resolve` | Allarme locale e notifica del server risolvono l'ora ripetuta o inesistente con `fold` diversi; la deduplica per istante non li riconosce e suonano entrambi | New York, 1 novembre 2026, 01:30: notifica 05:30Z, allarme 06:30Z |
| R2 | `planner.next_occurrence` | Il giorno della settimana è preso dall'istante UTC, non dal giorno locale | Tokyo, lunedì 07:00: suona martedì |
| R3 | `server.on_zone_change` | La ripianificazione dopo il cambio di fuso ignora che la data ha già suonato | Da Tokyo a Roma il 10 novembre: suona due volte nella stessa data |
| R4 | `server.today` | La lista «Oggi» usa il fuso dell'iscrizione, non quello corrente | Iscritto a Roma, a Tokyo alle 05:00 del 10 novembre: mostra il 9 |

Esche: `next_occurrence` avanza per giorno locale e poi converte, quindi non sposta l'ora al cambio d'ora; gli istanti salvati in UTC sono corretti.

Decisione dichiarata prima della run: se il criterio non è raggiunto neanche qui, il ruolo e il segnale `calendar` si rimuovono e restano solo le pulizie dei confini e della tassonomia.

Run del 2026-11-09, ruolo al commit `187b25f`.

| Configurazione | R1 | R2 | R3 | R4 | Altri reali | Esca segnalata | Token | Strumenti | Tempo |
|---|---|---|---|---|---|---|---|---|---|
| `calendar-time-auditor` | sì | sì | sì | sì | 0 | no | 76.088 | 7 | 59 s |
| confronto | sì | sì | sì | sì | 2 | no | 83.656 | 6 | 82 s |

- Entrambe le configurazioni trovano i quattro semi; R3 è segnalato da entrambe con il dubbio su quale data conti, che il contratto lascia aperto.
- Altri reali del confronto: una regola senza giorni fa sollevare `next_occurrence` e blocca `tick` per le regole successive; un cambio di fuso sovrascrive un suono già dovuto e non ancora inviato.
- Il confronto ha scritto uno script fuori dalla copia, senza leggere nulla fuori: isolamento violato solo in scrittura.
- Criterio non raggiunto. Come dichiarato, ruolo e segnale `calendar` sono rimossi; restano la correzione della tassonomia 15.2 (UTC per gli istanti, identificatore di fuso o orario locale fluttuante per gli orari civili) e questa fixture per provare modifiche future.
