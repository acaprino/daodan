# Benchmark: promemoria con orario fluttuante

Prova il ruolo `senior-review:calendar-time-auditor`: deve trovare dove un orario civile viene calcolato, mostrato o fatto suonare in modo incoerente tra fusi orari, ora legale, ricorrenze e cambi di fuso.

## Parametri

| Parametro | Valore |
|---|---|
| prova | `calendar-time-auditor` |
| confronto | `temporal-resilience-auditor` e `data-representation-auditor` insieme, al commit `4ac9475`: i due ruoli che prima del ruolo nuovo nominavano fusi e ora legale |
| richiesta | «Rivedi `app/`: ogni promemoria deve suonare alla sua ora nel fuso in cui si trova l'utente.» |
| esecuzione | un `senior-review:isolated-worker` per configurazione, con i file ruolo come istruzioni |
| modello | da registrare alla run, uguale per le due configurazioni |
| fixture | copia di `app/` in una directory vuota: il worker non vede README, test né risultati attesi |

## Fixture

`app/reminders.py`, circa 60 righe: promemoria lato server con orario fluttuante (le 9:00 restano le 9:00 nel fuso corrente dell'utente), creazione, cambio di fuso, tick ogni minuto e scheda del giorno. Contiene quattro difetti seminati e un'esca: gli istanti salvati in UTC sono corretti e non vanno segnalati.

## Risultati attesi

| Seme | Dove | Difetto | Esempio |
|---|---|---|---|
| S1 | `card` contro `ring_at` | La scheda e il suono risolvono in modo diverso l'orario che non esiste al cambio d'ora | Sydney, 4 ottobre 2026: la scheda mostra 02:30, suona alle 03:30 |
| S2 | `tick` | La ricorrenza aggiunge 24 ore all'istante: l'orario locale si sposta al cambio d'ora | Roma, dopo il 29 marzo 2026: suona alle 10:00 |
| S3 | `set_zone` | Il cambio di fuso non ricalcola il prossimo suono già pianificato | Da Roma a Tokyo: suona alle 17:00 invece delle 09:00 |
| S4 | `done_on` | «Fatto» confronta la data UTC del suono con il giorno locale | Tokyo, 08:00: dopo il suono la scheda resta «to do» |

Criterio, dichiarato prima della run: il ruolo resta se trova almeno un seme che il confronto non trova, senza segnalare l'esca.

## Prove senza modello

`python -B -m pytest -q benchmarks/calendar-time`

`test_fixture.py` dimostra ogni seme: i test passano finché il difetto è presente, e l'esca fa il giro completo da UTC all'orario locale.

## Run con il modello

Ogni run richiede prima il via dell'utente.

1. `d=$(mktemp -d) && cp -r benchmarks/calendar-time/app "$d"/`
2. In un processo nuovo con radice `$d`, affidare la richiesta a un `isolated-worker` che applica `roles/calendar-time-auditor.md`; in un altro processo nuovo, con radice in una seconda copia, ai due ruoli del confronto presi dal commit `4ac9475`.
3. Registrare per ciascuna run: finding con `file:line`, token, costo e tempo.
4. Confrontare i finding con i risultati attesi: semi trovati, altri difetti reali, segnalazioni errate.

## Misure

Nessuna run eseguita.
