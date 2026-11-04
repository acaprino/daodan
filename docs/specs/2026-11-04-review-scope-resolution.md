# Identificazione del perimetro di review

Data: 4 novembre 2026.

**Stato:** proposta iniziale.

## Step 1 — Che cosa devo rivedere?

Lo Step 1 interpreta il prompt e, tramite Codebase Map quando serve, individua **il perimetro esatto della review** come:

- una o più cartelle;
- una lista di file;
- un mix di cartelle e file.

Non prepara il contesto, non sceglie reviewer e non introduce altri output obbligatori.

```text
Prompt + Codebase Map → cartelle e/o file da rivedere → contesto → review
        Step 1                                  Step 2
```

Il prompt può indicare un changeset, un path, un modulo, una feature o un documento. Lo Step 1 lo traduce comunque nei path concreti da esaminare:

- per un **changeset**, usa i file realmente modificati;
- per un **path**, usa il file o la cartella indicati;
- per un **modulo o feature**, usa i path identificati da Codebase Map;
- per un **documento**, usa il documento stesso.

Un modulo non coincide necessariamente con una directory, un package o una componente macro. Codebase Map può definirlo come un insieme di funzioni, classi, file o componenti con una responsabilità o un ruolo architetturale comune. I membri devono essere verificabili; lo Step 1 converte la loro appartenenza nell'elenco di cartelle e file da rivedere.

Una cartella può essere usata soltanto se tutto il suo contenuto pertinente fa parte della review; altrimenti vengono elencati i singoli file.

## Come usa Codebase Map

1. **Evita la ricerca quando il target è già esplicito.** Per un path, documento, commit, range o PR, risolvi direttamente i file. Non avviare embedding o esplorazione del grafo.
2. **Usa prima gli anchor concreti.** Estrai dal prompt identificatori, nomi di componenti, path, errori e termini di dominio. Cerca prima simboli e componenti esatti; passa al lessicale solo per i riferimenti mancanti e agli embedding soltanto se la ricerca precedente non basta.
3. **Usa la struttura adatta alla domanda.** Per un modulo leggi i suoi membri e il loro ruolo nella mappa; per una feature segui soltanto gli archi del flusso; per un impatto usa `edit-impact` e `stale-callers`. Documentazione e `AGENTS.md` confermano responsabilità e confini senza caricare interi archivi.
4. **Espandi soltanto ciò che è necessario.** Il grafo fornisce candidate, non un perimetro automatico. Una relazione di primo livello è il default; si prosegue soltanto per attraversare wrapper o completare il flusso richiesto.
5. **Verifica poco e fermati.** Leggi soltanto le sezioni decisive per distinguere le candidate, poi restituisci il mix minimo di cartelle e file che copre la richiesta. Non leggere ogni hit, non espandere per aumentare genericamente la recall e non chiedere chiarimenti se il target è già inequivocabile.

Il risparmio di token viene quindi da quattro scelte: niente retrieval per target esatti, risultati di mappa prima del codice, letture soltanto decisive e nessuna espansione dopo che il perimetro è coperto. Se restano due target materialmente diversi, si chiede quale rivedere.

## Esempi

Gli elenchi di file sono illustrativi.

### Una cartella

> Rivedi il plugin Codebase Map.

```text
Perimetro:
- plugins/codebase-map/
```

### Una lista di file

> Rivedi le modifiche a snapshot e retrieval.

```text
Perimetro:
- plugins/codebase-map/skills/map-method/scripts/snapshot.py
- plugins/codebase-map/skills/map-method/scripts/retrieval.py
```

### Un mix

> Rivedi il modulo di context building e la sua documentazione.

```text
Perimetro:
- plugins/codebase-map/skills/map-method/scripts/
- docs/research/context-building-research.md
- docs/research/context-building-benchmarks.md
```

La cartella è inclusa soltanto se l'intero modulo di script è nel target; altrimenti lo Step 1 restituisce soltanto i file pertinenti.

## Confine con lo Step 2

Lo Step 2 riceve questo elenco e raccoglie il contesto utile: file completi, caller, test, contratti e documentazione. Queste letture non allargano automaticamente il perimetro della review.
