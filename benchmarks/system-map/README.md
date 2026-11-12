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

- `expected/phazly-payments.json`: gli 11 nodi con i loro file e i 3 flussi della mappa fatta a mano il 12 novembre 2026 (pagamento, gestione abbonamento, paywall e limiti d'uso). Si registra dopo la conferma del proprietario e con i percorsi letti dall'archivio di phazly.
- `expected/externals-<caso>.json`: per ogni caso l'elenco a mano dei servizi e dei progetti esterni dichiarati nei manifest.

## Esecuzione

| Misura | Comando |
| --- | --- |
| 1, 2, 4, 5 | `python score.py map MAP.json expected/phazly-payments.json` sulla mappa salvata dalla run |
| 6 | `python score.py externals BRIEF.json expected/externals-<caso>.json` sulla scheda del sistema del caso |

## Risultati

### Gruppi candidati, 12 novembre 2026, prima di fissare la regola

Con una soglia sulla quota dei punti d'ingresso (20%) la fixture `flow-model` non forma nessun gruppo, perché due su sei sono già il 33%, e phazly (235 punti d'ingresso, 68 risorse) forma un solo gruppo da 117 più 118 isolati: le risorse a media condivisione fanno catena. Con un gruppo per risorsa la fixture dà i due gruppi attesi (`store:db/payments` con quattro punti d'ingresso, `module:card payment provider` con tre) e phazly 44 gruppi, 143 punti d'ingresso in almeno un gruppo, 92 isolati (86 non toccano nessuna risorsa), in 9.300 caratteri.

### Costruzione del registro, 12 novembre 2026

2.172 voci da stack-analyser 1.27.6 (743 regole), CNCF Landscape (commit `75b47639`, senza le categorie dei membri e dei fornitori certificati) e Simple Icons 16.37.0 (marchi agganciati per nome). `derive`, senza modello, trova pacchetti su PyPI, crates.io o nel proxy di Go per 102 delle 455 voci con un pacchetto npm; tiene un pacchetto solo se il repository ha lo stesso proprietario del pacchetto npm principale, un modulo Go solo se il suo `go.mod` è vero, e scarta i pacchetti trovati per più voci. Una run di Haiku 5.5 (0,023 USD, 40.257 token in uscita) propone il resto: la macchina ne tiene 141, fra cui FastAPI, Flask e Pydantic, e ne rifiuta 22 oltre a quelle già coperte, compresi pacchetti veri con un altro proprietario (`boto3`, `prometheus-client`, il driver Go di MongoDB).

Misura 6 e dimensione della scheda sui tre casi: da eseguire su Modal.
