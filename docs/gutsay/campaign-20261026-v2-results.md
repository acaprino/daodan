# Campagna Gutsy CPU: risultati verificati

**Campagna con evidenza incompleta.** Il completamento della campagna non promuove automaticamente il modello.

Arresto registrato dal worker (dettagli completi nel JSON):

    {"type": "TimeoutError", "message": "Frozen campaign forecast 181353s exceeds 79200s; replan before verification"}

## Copertura e decisioni

Richieste pianificate: **10510**. Stati osservati: `{"delivered": 40, "missing": 10470}`.

| Dominio | Confronto principale grezzo | Differenza | Supporto e limiti | Prossimo passo |
|---|---|---:|---|---|
| routing | R3 vs R1 | n/d (copertura incompleta) | 360 casi; 3348 osservazioni etichettate; 1 componenti; IC soppresso | Completare o correggere il banco di prova; dati di verifica incompleti, nessuna promozione del modello. |
| tools | T2 vs T1 | n/d (copertura incompleta) | 111 casi; 111 osservazioni etichettate; 5 componenti; IC soppresso | Completare o correggere il banco di prova; dati di verifica incompleti, nessuna promozione del modello. |
| compaction | C1-Q1 vs C0-Q0 | n/d (copertura incompleta) | 360 casi; 360 osservazioni etichettate; 6 componenti; IC soppresso | Completare o correggere il banco di prova; dati di verifica incompleti, nessuna promozione del modello. |

Le differenze includono tutti i casi preregistrati eleggibili per la metrica. Le risposte mancanti non sono successi. Per i tool, il confronto principale usa gli oracle esatti; i witness BFCL pubblici misurano copertura sufficiente e non forniscono etichette negative per ogni alternativa.

## Policy scelte sulla calibrazione

Le selezioni sono salvate prima dello scoring della verifica e legate agli hash di corpus e risposte di calibrazione. I confronti grezzi sopra mantengono le soglie diagnostiche originarie; non usano soglie adattate alla verifica.

| Dominio | Policy congelata | Stato |
|---|---|---|
| compaction | `non disponibile` | unavailable |
| routing | `non disponibile` | unavailable |
| tools | `non disponibile` | unavailable |

| Dominio / oracle | Strategia selezionata: successi certificati | Fallimenti noti / sconosciuti | Fallback / errori critici |
|---|---:|---:|---:|

Le procedure protette, i recuperi e le baseline hanno righe distinte nell’analisi per caso. Il loro successo non è credito per una predizione grezza errata. I token risparmiati negli schemi non sono disponibili: manca un tokenizer esplicito del modello destinatario.

## Qualità grezza e procedure protette

| Dominio / strategia / oracle | Successi certificati | Sconosciuti | Fallback riusciti | Errori critici | Costo / unità |
|---|---:|---:|---:|---:|---|
| compaction / C-keep-all / labelled_requirement | 360/360 | 0 | 0 | 0 | 877028 retained_and_recovered_serialized_bytes |
| compaction / C0-Q0 / labelled_requirement | 0/360 | 0 | 0 | 0 | 877028 retained_and_recovered_serialized_bytes |
| compaction / C1-Q1 / labelled_requirement | 0/360 | 0 | 0 | 0 | 877028 retained_and_recovered_serialized_bytes |
| compaction / C1-Q1:protected / labelled_requirement | 0/360 | 0 | 0 | 0 | 877028 retained_and_recovered_serialized_bytes |
| routing / R0 / labelled_requirement | 0/360 | 0 | 0 | 0 | 756 incorrect_labelled_fields |
| routing / R1 / labelled_requirement | 0/360 | 0 | 0 | 0 | 3348 incorrect_labelled_fields |
| routing / R3 / labelled_requirement | 0/360 | 0 | 0 | 0 | 756 incorrect_labelled_fields |
| tools / T0 / exact | 111/111 | 0 | 0 | 0 | 331250 normalized_schema_utf8_bytes |
| tools / T1 / exact | 0/111 | 0 | 0 | 36 | 250 normalized_schema_utf8_bytes |
| tools / T1-protected / exact | 111/111 | 0 | 111 | 0 | 331250 normalized_schema_utf8_bytes |
| tools / T2 / exact | 0/111 | 0 | 0 | 36 | 250 normalized_schema_utf8_bytes |
| tools / T2-protected / exact | 111/111 | 0 | 111 | 0 | 331250 normalized_schema_utf8_bytes |
| tools / T0 / sufficient_witness | 235/235 | 0 | 0 | 0 | 725947 normalized_schema_utf8_bytes |
| tools / T1 / sufficient_witness | 0/235 | 235 | 0 | 0 | 470 normalized_schema_utf8_bytes |
| tools / T1-protected / sufficient_witness | 235/235 | 0 | 235 | 0 | 725947 normalized_schema_utf8_bytes |
| tools / T2 / sufficient_witness | 0/235 | 235 | 0 | 0 | 470 normalized_schema_utf8_bytes |
| tools / T2-protected / sufficient_witness | 235/235 | 0 | 235 | 0 | 725947 normalized_schema_utf8_bytes |

I costi in byte non sono token. Le riduzioni rispetto alla baseline sono nell’analisi JSON, con lo stesso insieme di casi. Robustezza, episodi congiunti e provenienza sono conservati separatamente: le varianti non aumentano il numero di prove indipendenti.

## Prestazioni e risorse

Decisioni di profiling complete su un singolo host: **0/480** (disegno: 480). Ogni decisione somma tutte le proprie parti HTTP. Host diversi non vengono aggregati.

| Host / profilo | Modalità / workload | Decisioni | p50 | p95 | Entro 1 s |
|---|---|---:|---:|---:|---:|

I replay gerarchici e retrieval realmente eseguiti sono separati dalla simulazione offline di qualità:

| Host / profilo | Percorso | Decisioni | p50 | p95 |
|---|---|---:|---:|---:|

Stabilità catalogo completo/sottoinsieme: 0/48 coppie con domande confrontabili, 0 sottoinsiemi vuoti, 48 coppie incomplete. Differenze di probabilità e cambiamenti alla soglia diagnostica 0,5 sono nel JSON, insieme a profili e host di entrambe le chiamate.


Picco RSS combinato: **1.391 GiB**; obiettivo locale 1 GiB, limite diagnostico 4 GiB. La somma può contare pagine condivise più volte.

Avvii server misurati: 158.916 s. Scritture checkpoint misurate: 135.63014351400017 s. Tempo globale: 2208.2886440753937 s; limite 79.200 s. Domande tentate: 187; riserva startup: 18; limite 50.000.

Domande già consumate dalle versioni precedenti: 93; consumo totale vincolato: 298. Verifica del budget ereditato: verified.

Stima operativa del calcolo: 0.13532392835731505 USD, tetto 6 USD. Non è una fattura; build, download, startup e checkpoint non diventano latenza del modello.

Gate runtime: parità **recomputed_pass**; previsione del budget **incomplete**. La parità viene ricalcolata dalle risposte; la regressione temporale è un’attestazione del runtime vincolata ai suoi hash, non una nuova stima indipendente.

Contratto di parità: `cached-paths-v2`. Nel contratto v2 la ricodifica completa resta un fattore esplorativo non equivalente; non viene aggregata come misura di velocità a qualità invariata. Il contratto v1 mantiene il confronto originale fra tutti e tre i percorsi.

## Indipendenza e limiti

Il bootstrap usa 10.000 ricampionamenti di componenti connessi tramite famiglia, provenienza e template, seed 26102026. Gli intervalli dei tre confronti principali sono al 98,33% ciascuno (Bonferroni, famiglia 95%). Con meno di due componenti o verifica incompleta l’intervallo viene soppresso. Le sensibilità per progetto/provenienza, famiglia e template sono nell’analisi JSON.

Il routing misura segnali e assegnazione deterministica, non il modello minimo capace di completare il lavoro. I casi source-derived e i replay non sono automaticamente sessioni utente reali. Le verifiche di compattazione misurano evidenza per la continuazione, non una risposta di un LLM downstream. Nessuna prestazione osservata su Modal dimostra già il funzionamento sulla CPU locale.

Manifest analizzato: `e7f00f2c7cc42741d690fc7d0ac4fa9aa10fef2066e3ee1b36c82fe58729e82a`. Input: `4f14c292f8b0425736b7ea5b522d9cb7d82c9e6b8725fc400ef22eaec271fffe`. Modello atteso: `gutsy-0.8b-v04-q4`.

Artefatti locali: `analysis.json`, `case-scores.json`, `selection-status.json` e `selections/` nella directory di analisi scelta. Risposte originali e registri del worker restano separati e immutati.
