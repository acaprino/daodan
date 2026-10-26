# Riprogettazione del pacchetto di contesto

Data: 25 ottobre 2026. Stato: approvato dal proprietario dopo due revisioni indipendenti;
fasi 1 e 2 eseguite, più l'unico tentativo consentito sul formato dell'input; misure in
[RESULTS](../../../evals/codebase-map/context-scope/RESULTS.md). Il punto di decisione dopo la
fase 2 non è superato (a 24 000 caratteri 46% dei corpi contro 52% della ricerca testuale, e
nessuna affermazione in più): la riprogettazione si ferma qui, le fasi 3 e 4 non partono e il
secondo holdout resta intatto. Origine: report di consegna P0-P10 (rimosso il 2026-10-26),
difetti 1 e 2. Specifica di partenza: contesto del codice e perimetro (rimosso il 2026-10-26),
che alle righe 113-119 distingueva già i riferimenti esatti, obbligatori, dai risultati di
ricerca, destinati all'esplorazione: questa riprogettazione riallinea il codice a quella
distinzione e chiude i difetti che la misura ha mostrato.

## Problema misurato

Sul progetto di prova (Starlette 1.9.0, 24 query) pianificatore e costruttore del pacchetto
hanno rifiutato 72 tentativi su 72 a 6 000, 12 000 e 24 000 caratteri. Cause verificate:

1. `scope_planner._candidate` segna ogni candidato `required_detail="source"`, piste di
   ricerca comprese, e `context_packet._project` rende obbligatorio il sorgente di ogni riga.
2. Il profilo del resolver occupa 22 014 caratteri dentro l'input del destinatario.
3. Il taglio a 1 000 varianti avviene dopo aver accodato i pezzi di sorgente: può togliere
   un prerequisito e lasciare il corpo che ne dipende.
4. Sorgente e impatto vengono materializzati per ogni entità proiettata prima della selezione.
5. `needs_split` riporta l'intero insieme rigido anche per un semplice overflow; `map_slice`
   proietta tutto il perimetro senza distinguere il nucleo dalle piste.

Il rischio opposto è il falso `ready`: piste opzionali senza un nucleo minimo producono
pacchetti piccoli ma privi di prove.

## Matrice origine × intento

Ogni riga di analisi porta `required_detail`: `source` (il suo sorgente attuale è supporto
obbligatorio) oppure `lead` (pista: entra se c'è spazio, non blocca mai il pacchetto).

| Origine | analysis, docs | bug | change, test, finish |
|---|---|---|---|
| Obiettivo di un requisito obbligatorio (`current_source`) | source | source | source |
| Ancora: anchor esatto, diff fornito, intervento proposto, evidenza di localizzazione, match esatto o traceback della ricerca | source | source | source |
| Simbolo cambiato nel confronto tra snapshot | lead | lead | source |
| Impatto canonico, coda non classificata, deriva dei legami | lead | lead | lead |
| Pista: ricerca testuale o densa, ancora ambigua, pista esterna, vicino risolto | lead | lead | lead |

Regole:

- Il dettaglio si fonde in modo monotono: una riga diventata `source` non torna `lead`,
  qualunque sia l'ordine in cui le origini arrivano.
- Gli obblighi di validazione (requisiti, gate, impatto, confini) restano nel pacchetto e
  restano aperti a ogni budget, come prima.
- L'evidenza d'impatto (`graph:`) si costruisce solo per le entità del nucleo e solo per gli
  intenti `bug`, `change`, `test`, `finish`.
- Un riferimento (percorso più digest) non è mai prova consegnata: soddisfa un predicato solo
  il materiale che il destinatario riceve nell'input.

## Stati del pacchetto

Gli stati restano `ready`, `incomplete`, `needs_split`. Un nuovo campo `status_reason` dice perché:

| Stato | Motivo | Quando |
|---|---|---|
| `ready` | nessuno | piano localizzato, nucleo non vuoto, supporto rigido coperto, input dentro il budget |
| `incomplete` | `not_localized` | il piano non è localizzato; le piste consegnate restano piste |
| `incomplete` | `empty_core` | piano localizzato senza alcun predicato obbligatorio: mai `ready` |
| `needs_split` | `missing_support` | un predicato rigido non ha fornitori o i suoi prerequisiti mancano; `missing_support` elenca solo quelli |
| `needs_split` | `core_too_large` | il nucleo esiste ma non entra; `missing_support` è vuoto |
| `needs_split` | `projection_limit` | un fornitore del nucleo è stato escluso dai limiti di proiezione |
| `needs_split` | `work_limit` | la ricerca del nucleo ha esaurito le valutazioni |

## Limiti

- Proiezione: prima tutte le entità del nucleo, poi al massimo 60 piste nell'ordine del
  pianificatore; 200 entità in tutto.
- Varianti: si includono bundle interi (firma, corpo, card, impatto e i pezzi di sorgente
  nuovi), mai metà bundle; i bundle del nucleo vengono prima. Un bundle di pista escluso è
  dichiarato come gap per entità.
- Materializzazione: sorgente e impatto si calcolano per un'entità solo quando il suo bundle
  entra nella proiezione.
- Il confronto tra politiche `ordered` e `marginal` gira solo se il destinatario lo chiede
  (`compare: true`); altrimenti si calcola solo la politica del destinatario.

## Busta

L'input renderizzato porta del profilo del resolver solo digest, versione e stato di
copertura. Il profilo completo resta nella ricevuta del pacchetto su disco, che il lifecycle
già verifica per digest. La fase 3 estende questo schema a sidecar generali con percorso
confinato, schema, legame a piano e snapshot e capacità di lettura del destinatario.

### Trovato durante la fase 2

La prima misura dopo la correzione di obbligatorietà e profilo mostrava ancora rifiuti con
nucleo vuoto: la busta senza blocchi pesava circa 9 600 caratteri. Tre cause, corrette nella
stessa fase perché sono la stessa busta:

- il gap `projection_limit` elencava ogni entità esclusa (circa 7 100 caratteri su una query):
  nell'input una lista lunga diventa conteggio più primi elementi, la ricevuta la tiene intera;
- ogni pista portava la propria firma, cioè il record completo dell'entità (circa 1 400
  caratteri, con un percorso assoluto della macchina): una pista ora è il solo corpo, con
  posizione e hash, e le firme restano al nucleo;
- ogni riga di sorgente portava il proprio numero: l'input dà la prima e l'ultima riga del
  blocco e il testo, la ricevuta tiene le righe numerate.

## Lettore di sorgente

`source_reader` ripiegava sul file intero quando due funzioni si sovrapponevano nelle righe.
Una funzione annidata si sovrappone sempre a quella che la contiene, quindi 10 dei 34 file
Python di Starlette (tra cui `routing.py`, 768 righe, e `responses.py`) venivano letti interi
per una funzione di poche righe. La regola voleva intercettare dichiarazioni sulla stessa riga
fisica: ora scatta solo per una sovrapposizione parziale o due funzioni che iniziano sulla
stessa riga, e una funzione annidata si legge con le funzioni che la contengono. Restano il
ripiego per span incerti, errori di parsing e righe condivise. `source_reader.py` entra
nell'impronta del parser: le mappe esistenti vanno rigenerate dopo l'aggiornamento.

## `map_slice`

Ogni componente elenca in `entities` le entità del nucleo e in `leads` le piste. Le entità
del nucleo superano il limite di proiezione per prime.

## Misure di accettazione

1. Oracolo comportamentale del cookie corretto: un nome non valido deve essere rifiutato con
   qualsiasi eccezione (`ValueError` o `http.cookies.CookieError`), un nome valido deve
   produrre l'header atteso.
2. Gold per affermazioni su 4-6 scenari critici, accanto alla gold per entità: affermazioni,
   intervalli necessari, alternative accettabili, gap attesi (anche il codice della libreria
   standard fuori dal perimetro, dichiarato come gap).
3. Sulle 24 query accoppiate, prima e dopo: copertura su tutte le 24 con rifiuti ed errori a
   zero; qualità dei soli pacchetti consegnabili (`ready`); falsi `ready`, obblighi
   conservati, affermazioni supportate; tempi separati di pianificazione e pacchetto.
4. Secondo progetto congelato nella fase 1 e usato solo nella fase 4.

## Punto di decisione dopo la fase 2

Si prosegue se il pacchetto, contato su tutte le 24 query, consegna almeno quanto la ricerca
testuale, oppure la eguaglia con garanzie misurate (zero falsi `ready`, obblighi conservati,
più affermazioni supportate) a un costo che il proprietario accetta. Ci si ferma se continua a
non consegnare, o se peggiora senza un beneficio verificabile.
