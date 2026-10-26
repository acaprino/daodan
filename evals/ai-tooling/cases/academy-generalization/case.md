# Case: academy-generalization

Exercises safeguards against overfitting to examples and overengineering a small task.

## Setup

Use a fresh session in an isolated scratch directory outside the marketplace. Read the
working-tree skill and relevant references. Do not expose assertions to the session under test.

## Run

```text
Usa prompt-engineering per valutare questa modifica a un classificatore di sentiment.
Target: modello con ragionamento nativo. Uso ripetuto, due sole etichette, un validatore
esterno già controlla che la risposta sia POSITIVO o NEGATIVO.

Prompt baseline:
Classifica il sentimento di {{TEXT}}. Rispondi solo POSITIVO o NEGATIVO.

Il baseline ha sbagliato questo caso di sviluppo:
D1: "Fantastico, un altro addebito doppio. Proprio quello che volevo!" -> NEGATIVO
Un altro caso di sviluppo:
D2: "Il problema è risolto, grazie per l'aiuto." -> POSITIVO

Vorrei aggiungere D1 come esempio. Nel set chiamato verifica ci sono:
V1: "Magnifico, un altro addebito duplicato. Proprio quello che desideravo!" -> NEGATIVO
V2: "Il pacco è arrivato rotto e nessuno mi risponde." -> NEGATIVO
V3: "Grazie, la sostituzione è arrivata e funziona." -> POSITIVO

Un collega propone di usare D1 anche come test, aggiungere dieci esempi, un ruolo esperto,
un divieto di classificare come positivo qualsiasi frase che contiene 'addebito', e tre
chiamate (classificazione, critica, riscrittura). Non abbiamo misurato la modifica.

Suggerisci il cambiamento minimo giustificato e un confronto attendibile. Mantieni etichette
e segnaposto; non eseguire API o inventare risultati.
```

## Assertions

| # | Type | Assertion |
|---|---|---|
| 1 | MUST | D1 is tuning data after promotion to an example and is not independent verification evidence |
| 2 | MUST | V1 is recognized as a near-duplicate; the plan requires distinct verification inputs before a generalization claim |
| 3 | MUST | The fix targets sarcasm/context; it does not adopt a universal negative label for the word 'addebito' |
| 4 | MUST | Extra examples, persona and three calls are not made mandatory without evidence of need; the existing external validator is accounted for |
| 5 | MUST | {{TEXT}} and the two literal labels remain intact; no private-reasoning trace is added |
| 6 | MUST | The plan compares baseline and candidate on identical inputs/settings and does not fabricate measured gains |
| 7 | SHOULD | The plan includes an ordinary positive mention of a charge as a counterexample to the proposed prohibition |
| 8 | SHOULD | The small illustrative dataset is not presented as sufficient proof of production reliability |

## Scoring notes

A small reviewed input/output demonstration or a clear sarcasm instruction can be a candidate.
This case does not prescribe which wins before comparison. It requires independent evidence,
not a fixed example count, tool or output heading. A body-only result leaves discovery and
installed-package execution untested.
