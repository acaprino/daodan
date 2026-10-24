# Consegna del contesto del codice: P0-P10

Data: 24 ottobre 2026. Piano: [contesto del codice e perimetro](../plans/2026-10-23-code-context-and-scope.md).
Misure, harness e gold congelato: [`evals/codebase-map/context-scope/`](../../../evals/codebase-map/context-scope/RESULTS.md).

## Esito

L'infrastruttura è consegnata e funziona come meccanismo: indice di ricerca, archi Jedi,
pianificatore di perimetro, pacchetti di contesto, ricevute legate alla revisione del
registro, ripresa e invalidazione. Il **beneficio della composizione non è dimostrato**:
sul progetto di prova, al budget previsto dal piano (6 000 a 24 000 caratteri), il
pianificatore con il costruttore di pacchetti non ha consegnato nulla in 72 tentativi su
72, mentre la ricerca testuale ha consegnato dal 31% al 52% dei corpi cercati. Il sistema
rifiuta senza dare contesto sbagliato, ma oggi non aiuta a questi budget.

Il **recupero con embedding migliora in modo netto**: con il modello scaricato dopo la tua
autorizzazione, la ricerca fusa (embedding più parole) consegna il 74% dei corpi interi a
24 000 caratteri contro il 52% della sola ricerca per parole. Ma la composizione resta
rifiutata 24 volte su 24 anche con quelle piste: il limite non è la qualità della ricerca,
è la struttura del pacchetto.

## Cosa è consegnato

| Fase | Commit | Contenuto |
|---|---|---|
| P8 | `3d5be51b3` | adapter `cycle_packets.py` per preflight, task e post-task; proiezione pubblica I1 |
| P9 | `feaa1f9e7` | consumatori: documentazione, review, test, finish; matrice dei comandi |
| P10 | questo commit | harness e gold in `evals/`, braccio embedding, correzione del timeout, documentazione d'uso di plugin e MCP, questo report |

P8 e P9 sono pubblicati con CI verde su entrambi i workflow. La suite completa sul
candidato P10 passa: 1899 test, 12 saltati su questa macchina (collegamenti simbolici
senza privilegio, SDK MCP dal vivo non installato nell'interprete, test specifici di
piattaforma).
La revisione indipendente di P8 ha richiesto tre giri; l'ultimo non ha trovato difetti
Critical, High o Medium.

## Cosa è stato misurato

Progetto di prova: Starlette 1.9.0 (669 entità, 263 129 caratteri), 24 query congelate,
12 in inglese e 12 in italiano, gold scritto alla cieca e verificato da un secondo passaggio.

- **Ricerca e grafo.** A 24 000 caratteri il testo consegna il 52% dei corpi interi, il
  testo con grafo Jedi il 56%. Le query con nomi del codice o con una decisione arrivano
  all'88%; quelle di comportamento senza nomi al 25%. La ricerca lessicale non trova
  nei primi 60 risultati il 56% delle entità cercate.
- **Embedding** (modello CodeRankEmbed in versione ONNX INT8 della comunità, 138 MB, scaricato
  dopo l'autorizzazione e verificato per dimensione e SHA). Corpi interi consegnati a
  6 000, 12 000 e 24 000 caratteri: parole 0,31 / 0,47 / 0,52; solo embedding 0,44 / 0,58 /
  0,66; fusione del plugin 0,47 / 0,55 / **0,74**; fusione più grafo 0,51 / 0,55 / 0,68.
  Per query, a 24 000: 9 migliori, 2 peggiori, 13 pari (24 query di una sola libreria
  danno una direzione, non una prova statistica). Le query di comportamento passano da
  0,25 a 0,67 e quelle in italiano da 0,46 a 0,65; **le query di decisione scendono da 0,88
  a 0,75**. Le entità cercate fuori dai primi 60 risultati scendono dal 56% al 27%. Costo
  a freddo su CPU: 127 s per indicizzare 669 entità, 2,9 MB su disco, circa 410 MB di
  memoria del codificatore, 4 s a query per il solo embedding.
- **Composizione.** Pianificatore più pacchetto: 0% a tutti e tre i budget. Il piano
  resta `incomplete` e si localizza una volta su 24; con un'ancora si localizza sempre
  ma il perimetro resta di circa 386 entità su 669 e il pacchetto rifiuta ancora.
- **Composizione con piste dell'embedding.** 24 rifiuti su 24 a 24 000 caratteri; il
  perimetro cresce da 386 a 589 entità in media (da 512 a 669), perché il risultato
  dell'embedding classifica tutto il progetto e ogni pista diventa una riga che chiede il
  sorgente. Il difetto 2 è quindi confermato come causa: migliorare la ricerca non
  basta finché le piste sono obbligatorie.
- **Perché rifiuta.** Un pacchetto minimo da 44 319 caratteri contiene 22 014 caratteri di
  profilo del resolver, 12 778 di impatto, 4 745 di obblighi e 2 660 di sorgente
  utile. Il nucleo obbligatorio più piccolo vale 32 457 caratteri, quindi sotto quel
  limite anche una funzione piccola fa rifiutare il pacchetto. In più il pianificatore
  trasforma ogni candidato, anche un semplice suggerimento della ricerca, in una riga che
  richiede il sorgente, e il costruttore rende obbligatorio il sorgente di ogni riga.
- **Con la risposta in mano.** Prova esplorativa con il perimetro ristretto ai file giusti e
  un'ancora corretta: il pacchetto arriva a 79% dei corpi interi a 96 000 caratteri
  (23 pacchetti su 24, in media 64 000 caratteri). La ricerca testuale con la stessa
  informazione arriva all'84% a 24 000 caratteri. Il valore degli obblighi e dell'impatto
  non è misurato dalla copertura e non è misurato qui.
- **Impatto.** Su 10 scenari (firma, corpo, rimozione, funzione molto usata) e 28 siti di
  chiamata: con gli archi Jedi 25 su 28 (89%), senza 6 su 23 per i tre tipi diversi dalla
  rimozione; nessun sito riportato era falso.
- **Percorso reale.** Tutti i comandi hanno chiuso con 0, la ripresa ha restituito la stessa
  ricevuta e la ricevuta precedente è stata rifiutata dopo la modifica. Ma i tre pacchetti
  sono stati `needs_split`: nessun sorgente è arrivato a un lavoratore.
- **Export.** Su cinque host, 12 file del contesto per host sono identici al kernel (o lo
  contengono dopo il preambolo dell'host) e i quattro schemi esportati coincidono.

## Difetti trovati

1. **Busta del pacchetto troppo grande** (sopra). Correggerla è una riprogettazione del
   formato del pacchetto, non una patch: il profilo del resolver deve viaggiare come
   digest con percorso, non dentro l'input del destinatario.
2. **Suggerimenti trattati come obbligatori** (`scope_planner.py`, `_candidate`, e
   `context_packet.py`, `_project`). Un pianificatore che chiede il sorgente di metà
   progetto non può restringere nulla.
3. **Callable decorati senza chiamanti e senza avviso.** Con `@contextmanager` o
   `@asynccontextmanager` il resolver trova la funzione nello stub, non nel progetto, e
   riporta `no-project-targets`. Misurato: `FileResponse._open_file`, 0 chiamanti su 3. Il
   pacchetto non dichiara il vuoto, quindi una rimozione appare sicura.
4. **Nessun comando per l'indice di ricerca.** Si costruisce solo chiamando
   `retrieval.refresh_index` da Python; né la riga di comando né lo strumento MCP lo fanno.
5. **Timeout fisso dell'adapter a 120 secondi**, vicino al tempo reale di un pacchetto
   (circa 100 s). **Corretto** in questo commit: il provider può durare quanto
   `max_seconds` della richiesta, almeno 120; un test fallisce sul codice precedente.
6. **Documentazione obsoleta.** La pagina del plugin dichiarava 14 strumenti MCP, il server
   ne espone 19, e lo strumento di contesto non era nella tabella del contratto MCP.
   **Corretto** con la guida d'uso aggiornata (plugin, MCP e adapter del ciclo).

Non corretti (1 a 4): sono lavoro nuovo su P6 e P7, con test e revisione propri, e il
holdout è congelato per non essere tarato sul risultato.

## Non esercitato

Risultato dei task, uso di token e costo (nessun tokenizer né fatturazione), la memoria
oltre a quella del codificatore, l'embedding su un secondo corpus o con il modello
ufficiale (qui è una conversione della comunità), un secondo linguaggio, progetti oltre le 669 entità, qualsiasi host installato, un lavoratore
con modello che riceva un pacchetto. Nessuna compatibilità runtime universale è dichiarata.
Il gold è scritto da modelli e controllato da un secondo passaggio, senza adjudicazione umana.

## Decisioni per il proprietario

1. **Riprogettare busta e obbligatorietà** (difetti 1 e 2) prima di proporre il contesto del
   codice come risparmio di token. Raccomandato. Rimisurare poi con lo stesso gold, che va
   considerato consumato per la taratura: serve un secondo progetto per il nuovo holdout.
2. **Embedding.** Misurato: aiuta il recupero (74% contro 52%) ma non la composizione. Resta
   da decidere se tenerlo opzionale e spento (oggi) o proporlo per le query di comportamento
   e in italiano; le query con una decisione da ritrovare vanno meglio con le sole parole.
   Il modello usato è una conversione della comunità, non l'artefatto del fornitore.
   Disponibilità e abilitazione di default restano due esiti distinti: l'indice è
   disponibile come opzione, la modifica del default non è proposta (una sola libreria,
   query di decisione peggiori).
3. **Comando per l'indice** (difetto 4) e **gap dichiarato per i decorati** (difetto 3): piccoli,
   utili in ogni caso.
