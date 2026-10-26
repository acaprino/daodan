# Scorecard: academy-generalization

- **Date:** 2026-10-09
- **Component run:** `prompt-engineering`
- **Model / session:** Fresh independent Codex subagent; inherited session model, precise model identifier not recorded. Scorer was independent of the candidate author and runner.
- **Plugin version under test:** ai-tooling 5.5.0
- **Run stage:** working tree (bodies, not the loader); body-only stage
- **Setup materialized:** Isolated scratch under `C:/Users/alfio/.codex/visualizations/2026/10/09/01a12061-6c3c-7421-8d63-e4f4b5e12b98/prompt-academy-eval/generalization/`; output in `response.md`. No API calls. No deliberate setup edits recorded.

## Assertions

| # | Type | Outcome (pass / fail / n/a) | Evidence |
|---|------|-----------------------------|----------|
| 1 | MUST | pass | “D1 diventa sviluppo perché entra nel prompt; rieseguirlo serve come controllo della correzione, senza contarlo come verifica indipendente.” |
| 2 | MUST | pass | “V1 è una parafrasi molto vicina a D1: spostarlo nei controlli di sviluppo ed escluderlo dalla misura di generalizzazione.” The plan then says: “Costruire una verifica nuova e congelarla prima delle prove” and “Separare sviluppo e verifica anche per fonte, scenario o famiglia di parafrasi, evitando quasi duplicati.” |
| 3 | MUST | pass | “Il difetto osservato è una classificazione errata su una frase sarcastica” and “L'ipotesi è che l'esempio aiuti a riconoscere il sentimento espresso oltre alle parole apparentemente positive.” It rejects the keyword rule: “Il divieto sulla parola “addebito” introdurrebbe una regola diversa dal sentimento”. |
| 4 | MUST | pass | “Aggiungerei **solo D1 come esempio input/output**, mantenendo una chiamata e il validatore esistente.” Also: “Dieci esempi, un ruolo esperto e la sequenza classificazione/critica/riscrittura non hanno un beneficio dimostrato qui.” |
| 5 | MUST | pass | Candidate prompt: “Classifica il sentimento di {{TEXT}}. Rispondi solo POSITIVO o NEGATIVO.” Also: “Non aggiungerei una spiegazione del ragionamento all'output: il consumatore richiede soltanto l'etichetta.” |
| 6 | MUST | pass | “Eseguire baseline e candidato sugli stessi input, con la stessa versione di modello, impostazioni di ragionamento e generazione, contesto e validatore.” Also: “il beneficio del candidato è predetto e non misurato. Non ho eseguito API né verificato alcun miglioramento.” |
| 7 | SHOULD | pass | “L'addebito errato è stato annullato subito, ottima assistenza!” is offered as “un controesempio sintetico plausibilmente POSITIVO, da far confermare prima di usarlo come dato etichettato.” The verification plan also includes “frasi positive che contengono “addebito””. |
| 8 | SHOULD | pass | “V2 e V3 possono restare controlli ordinari congelati, ma due casi non bastano a sostenere affidabilità generale.” Also: “un successo su D1 o V1 da solo non soddisfa quel criterio.” |

## Cost

- Wall-clock: Not recorded.
- References loaded: Runner output reports the working-tree `prompt-engineering/SKILL.md` and four references: `prompting-foundations.md`, `extraction-prompting.md`, `reasoning-patterns.md`, and `structured-output.md`. These reported reads were not independently inspected by the scorer.
- Tokens / agents, if visible: One fresh independent runner subagent; token count not recorded. Independent scoring performed separately.

## Observations

The output proposes one reviewed sarcasm example as an unmeasured candidate, preserves the classification contract, and explains why the existing validator does not resolve semantic errors. It treats D1 and near-duplicate V1 as development controls, requires distinct frozen verification data, and accounts for regressions, stochastic variation, invalid outputs, and cost in the comparison plan.

The positive charge counterexample is explicitly synthetic and only plausibly labelled; the output requires review before treating that label as evaluation data. No assertion regression was observed in this case.

Untested scope: This body-only run does not establish workflow discovery, loader behavior, generated-package parity, or installed-package execution. No API comparison was run, so candidate quality, measured gains, latency, and actual cost remain untested. The precise runner model was not recorded, limiting exact reproduction.

## Verdict

- MUST assertions: 6 passed / 6 total
- SHOULD assertions: 2 passed / 2 total
- All assertions: 8 passed / 8 total; 0 failed; 0 n/a
- Case result: PASS (all MUST passed)
