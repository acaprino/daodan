# Fase 3: unità e flussi aiutano l'analisi?

**Stato:** abbozzo, da rifinire dopo le fasi [1](2026-11-09-working-run-and-review-fixes.md) e [2](2026-11-09-flow-model.md). **Data:** 9 novembre 2026. Fase 3 di 3.

Decide con misure se la review deve usare le unità costruite sul grafo e le catene dei flussi. Le unità e i flussi restano comunque per l'esploratore e la mappa funzionale: qui si decide solo il loro posto nell'analisi.

## Cosa si sa già

Da [`benchmarks/phazly-flow`](../../benchmarks/phazly-flow/README.md), con gruppi per percorso:

- il difetto `G1` è descritto esattamente in una run su tre con il metodo completo; il roster e i gruppi cambiano da una run all'altra;
- file legati nello stesso job non bastano (A3b: lettore e helper insieme, nessun finding) e non sono necessari (B: due scrittori in job diversi, difetto trovato da cinque ruoli);
- il brief dà ai job l'intento in una frase e una lista di file: nessuna domanda sul dato.

## Ipotesi da provare

1. Un job che riceve un'unità costruita sul grafo trova più difetti di provenienza di un job che riceve un gruppo per percorso.
2. La sola catena nel contesto (chi scrive, chi legge, a quale livello), senza cambiare il taglio, ottiene lo stesso effetto a costo minore.
3. Le regole 2 e 3 della fase 1 (livello nel contesto, gravità) cambiano l'esito anche senza unità né catena.
4. Schede ed etichette indicizzate in un canale di testo separato dal sorgente portano ai simboli giusti le richieste in parole di dominio.

## Disegno

| Braccio | Taglio | Contesto |
| --- | --- | --- |
| A | Gruppi per percorso | Come oggi, con le regole della fase 1 |
| B | Unità sul grafo | Come A |
| C | Gruppi per percorso | Come A, più la catena del dato richiesto |

- Richiesta: i widget della home di phazly-app al commit prima della correzione; roster fissato a mano, uguale per i tre bracci; due run per braccio. La richiesta su inserimento e scansione solo se la prima mostra un effetto.
- Difetti attesi: `G1`, `G2` e lo scrittore divergente dello stato «saltato». Misure: difetti attesi nel rapporto finale e non solo in un job, altri difetti reali, segnalazioni errate, costo, tempo.
- Ricerca: dieci richieste in parole di dominio sugli stessi simboli; posizione con il solo indice lessicale, con il canale di schede ed etichette, con gli embedding sul canale.
- Costo atteso dalle run già fatte: 15-21 USD per run sui widget, circa 110 USD per i tre bracci.

## Decisione

Criteri da fissare nel README prima delle run. Proposta di partenza:

- un braccio resta se porta nel rapporto finale, in entrambe le run, almeno un difetto atteso che A non porta, a costo entro due volte;
- fra B e C a pari esito resta il meno costoso;
- il canale di testo resta se porta nei primi cinque almeno tre simboli che il solo lessicale non porta, senza far scendere le richieste per identificatore.

Se nessun braccio supera A, la review resta com'è e lo si scrive nel README con i numeri.

**Da decidere alla rifinitura:** come passare un'unità a `composition.py bind`; forma della catena in `01-context.md`; se due run per braccio bastano, vista la variabilità misurata.
