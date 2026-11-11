# Fase 3: unità e flussi aiutano la review?

**Stato:** abbozzo, da rifinire dopo le fasi [1](2026-11-09-working-run-and-review-fixes.md) e [2](2026-11-09-flow-model.md). **Data:** 9 novembre 2026; aggiornata l'11 novembre 2026. Fase 3 di 3.

Una domanda sola: la review trova più difetti se riceve le unità e i flussi della fase 2? Si risponde con una misura. Unità e flussi restano comunque utili all'esploratore e alla mappa funzionale: qui si decide solo se entrano nella review. Le parole sono quelle definite nelle fasi 1 e 2.

## Cosa sappiamo

Dalle run di [`benchmarks/phazly-flow`](../../benchmarks/phazly-flow/README.md), un solo caso su un'app sola, fatte con i gruppi per percorso del file:

- Il difetto `G1` è descritto esattamente in una run su tre con il metodo completo.
- I revisori scelti e i gruppi di file cambiano da una run all'altra.
- Avere i file giusti nello stesso incarico non basta: in A3b lettore e helper erano insieme e il difetto non è uscito.
- E non è necessario: in B due scrittori erano in incarichi diversi e cinque revisori hanno trovato il difetto.
- Ogni incarico riceve la richiesta in una frase e un elenco di file. Nessuna domanda sul dato.
- La mappa di quelle run non aveva i collegamenti `chiama` per TypeScript.

Dalla [rassegna della letteratura](../research/2026-11-09-flow-reconstruction-literature.md): dividere il lavoro seguendo i collegamenti è misurato sulle modifiche da rivedere, non sul numero di difetti trovati; confrontare il significato fra chi scrive e chi legge un dato non ha strumenti valutati. La risposta può quindi essere «non aiuta».

## Le tre prove

Si prova su casi: progetti reali con difetti noti, al commit che precede la correzione. Ogni caso dichiara nel README del proprio benchmark richiesta, perimetro, contesto e difetti attesi: [`benchmarks/polar-flow`](../../benchmarks/polar-flow/README.md) è un servizio senza interfaccia, [`benchmarks/tududi-flow`](../../benchmarks/tududi-flow/README.md) un'app con frontend e backend, [`benchmarks/phazly-flow`](../../benchmarks/phazly-flow/README.md) un'app con interfaccia. Dentro un caso restano uguali richiesta, mappa, perimetro, contesto, revisori e limite di byte per incarico; perimetro e contesto sono fissati prima di generare gruppi e flussi. Cambia solo ciò che indica la tabella.

| Prova | File affidati | In più nell'incarico |
| --- | --- | --- |
| A | Gruppi per percorso del file, come oggi | Niente |
| B | Unità | Niente |
| C | Gruppi per percorso del file, come oggi | I flussi che attraversano il perimetro, non scelti a mano: chi scrive, chi legge, con quale granularità |

- **Richiesta:** nomina le aree del progetto, non i dati né i comportamenti.
- **Perimetro:** fissato a mano una volta per caso; comprende i file di tutti i difetti attesi.
- **Mappa:** completa dei collegamenti `chiama` per i linguaggi del perimetro.
- **Revisori:** scelti a mano una volta per caso, uguali per le tre prove.
- **Ripetizioni:** due run per prova.
- **Regole della fase 1:** attive in tutte e tre.
- **Stima iniziale:** 15-21 USD a run, circa 110 USD per le sei run di un caso; da ricalibrare sul perimetro di ogni caso.

I flussi di C si ricavano dallo stesso perimetro e dallo stesso contesto di A e B.

Si conta, per ogni run: difetti attesi presenti nel rapporto finale (non solo in un incarico), altri difetti reali, segnalazioni sbagliate, costo, tempo e file non esaminati. Il confronto è valido solo a parità di perimetro e con copertura completa: una run con file mancanti va completata prima di applicare le soglie.

## La prova sulla ricerca

Dieci domande per caso, scritte con le parole di chi usa l'applicativo e non con i nomi del codice, sugli stessi simboli. Si confronta la posizione del simbolo giusto in tre casi: indice lessicale da solo; con un campo di testo separato che contiene schede ed etichette; con gli embedding su quel campo.

## Come si decide

Le soglie si scrivono nel README del benchmark prima delle run e valgono per ogni caso. Proposta di partenza:

1. B o C vince se porta nel rapporto finale, in entrambe le run, almeno un difetto atteso che A non porta, spendendo al massimo il doppio.
2. Se B e C danno lo stesso esito, resta la meno costosa.
3. Il campo di testo resta se porta nei primi cinque risultati almeno tre simboli che l'indice lessicale da solo non porta, senza peggiorare le ricerche per nome.
4. Se né B né C superano A, la review resta com'è, e lo si scrive con i numeri.

**Da decidere alla rifinitura:** come passare un'unità a `composition.py bind`; come scrivere il flusso in `01-context.md`; se due run per prova bastano, vista la variabilità misurata; come si combinano gli esiti di casi diversi.
