# Fase 3: unità e flussi aiutano la review?

**Stato:** abbozzo, da rifinire dopo le fasi [1](2026-11-09-working-run-and-review-fixes.md) e [2](2026-11-09-flow-model.md). **Data:** 9 novembre 2026. Fase 3 di 3.

Una domanda sola: la review trova più difetti se riceve le unità e i flussi della fase 2? Si risponde con una misura. Unità e flussi restano comunque utili all'esploratore e alla mappa funzionale: qui si decide solo se entrano nella review. Le parole sono quelle definite nelle fasi 1 e 2.

## Cosa sappiamo

Dalle run di [`benchmarks/phazly-flow`](../../benchmarks/phazly-flow/README.md), fatte con i gruppi per percorso:

- Il difetto `G1` è descritto esattamente in una run su tre con il metodo completo.
- I revisori scelti e i gruppi di file cambiano da una run all'altra.
- Avere i file giusti nello stesso incarico non basta: in A3b lettore e helper erano insieme e il difetto non è uscito.
- E non è necessario: in B due scrittori erano in incarichi diversi e cinque revisori hanno trovato il difetto.
- Ogni incarico riceve la richiesta in una frase e un elenco di file. Nessuna domanda sul dato.
- La mappa di quelle run non aveva i collegamenti `chiama` per TypeScript.

Dalla [rassegna della letteratura](../research/2026-11-09-flow-reconstruction-literature.md): dividere il lavoro seguendo i collegamenti è misurato sulle modifiche da rivedere, non sul numero di difetti trovati; confrontare il significato fra chi scrive e chi legge un dato non ha strumenti valutati. La risposta può quindi essere «non aiuta».

## Le tre prove

Stessa richiesta, stessa mappa, stessi revisori. Cambia solo ciò che il revisore riceve.

| Prova | File affidati | In più nel contesto |
| --- | --- | --- |
| A | Gruppi per percorso, come oggi | Niente |
| B | Unità | Niente |
| C | Gruppi per percorso, come oggi | Il flusso del dato richiesto: chi lo scrive, chi lo legge, con quale granularità |

- **Richiesta:** la logica dei widget della home di phazly-app, al commit prima della correzione.
- **Difetti attesi:** `G1`, `G2` e lo scrittore che lascia lo stato «saltato».
- **Mappa:** completa dei collegamenti `chiama` per TypeScript.
- **Revisori:** scelti a mano una volta, uguali per le tre prove.
- **Ripetizioni:** due run per prova.
- **Regole della fase 1:** attive in tutte e tre.
- **Costo atteso:** 15-21 USD a run, circa 110 USD in tutto.

Si conta, per ogni run: difetti attesi presenti nel rapporto finale (non solo in un incarico), altri difetti reali, segnalazioni sbagliate, costo, tempo.

## La prova sulla ricerca

Dieci domande scritte con le parole del dominio («dove si decide che un piatto è stato mangiato») sugli stessi simboli. Si confronta la posizione del simbolo giusto in tre casi: indice lessicale da solo; con un campo di testo separato che contiene schede ed etichette; con gli embedding su quel campo.

## Come si decide

Le soglie si scrivono nel README del benchmark prima delle run. Proposta di partenza:

1. B o C vince se porta nel rapporto finale, in entrambe le run, almeno un difetto atteso che A non porta, spendendo al massimo il doppio.
2. Se B e C danno lo stesso esito, resta la meno costosa.
3. Il campo di testo resta se porta nei primi cinque risultati almeno tre simboli che l'indice lessicale da solo non porta, senza peggiorare le ricerche per nome.
4. Se né B né C superano A, la review resta com'è, e lo si scrive con i numeri.

**Da decidere alla rifinitura:** come passare un'unità a `composition.py bind`; come scrivere il flusso in `01-context.md`; se due run per prova bastano, vista la variabilità misurata.
