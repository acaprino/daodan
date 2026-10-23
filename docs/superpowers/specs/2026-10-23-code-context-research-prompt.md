# Deep Search: selezione del contesto e impatto delle modifiche

Data: 23 ottobre 2026. Prompt di ricerca, non risultato di una ricerca eseguita.
Alimenta il [disegno](2026-10-23-code-context-and-scope-design.md) e il relativo
[piano](../plans/2026-10-23-code-context-and-scope.md). La ricerca può procedere
mentre si chiudono i contratti e l'integrazione Jedi.

## Prompt pronto all'uso

Find primary research papers, reproducible algorithms and maintained open-source
implementations for **budget-constrained code retrieval and change-impact
analysis for coding agents**. The target system combines a static code graph,
persistent semantic documentation and local embeddings to select the smallest
sufficient analysis and intervention scope for bug fixing, feature development,
documentation and testing.

Investigate hybrid lexical/vector retrieval; query localization; call/dependency
graphs; program slicing and dependence analysis; directional graph expansion;
incremental analysis and cache invalidation; submodular selection, constrained
set cover, knapsack and other context-budget algorithms; uncertainty-aware
stopping and selective context expansion.

For each relevant approach, explain inputs, outputs, pseudocode, computational
complexity, assumptions, failure modes and suitability for Python's dynamic
dispatch. Distinguish retrieval relevance, potential change impact, required
validation and proven dependencies. Never treat embedding similarity or missing
static edges as proof of dependency or independence.

Compare against lexical search, embedding-only retrieval, fixed k-hop graph
expansion and full-context baselines. Report localization recall, dependency
recall, task success, billed LLM input/output tokens including retries and
indexing summaries, latency, memory and incremental update cost. Separate
measured results from conjectures and document benchmark leakage risks.

Prioritize local execution, reusable indexes, source provenance, explicit
coverage gaps and bounded tool outputs. Include foundational work and recent
research; verify dates, official repositories, licenses and maintenance status.
Finish with an evidence-backed minimal architecture, an implementable
scope-selection algorithm, and an evaluation protocol. Cite original papers
and official implementations directly; identify unsupported claims and
unresolved design choices.

## Risultato richiesto

1. Tabella fonte/anno/artefatto ufficiale/idea/limiti/riproducibilità/licenza.
2. Separazione fra risultati degli autori, repliche indipendenti e inferenze.
3. Massimo tre alternative implementabili, con pseudocodice e costo totale.
4. Decisioni applicabili al disegno Daodan, motivi di esclusione e prove mancanti.
5. Protocollo di confronto che includa query italiane, cambi di firma, chiamate
   dinamiche, hub, rimozioni, indici obsoleti e ripresa dopo interruzione.

Non assumere Qdrant, CodeRankEmbed, un runtime ONNX o un database dedicato come
scelta già effettuata. Non proporre un LLM per ogni nodo o ogni chiamata.
Valutare il benchmark locale esistente come baseline limitata: 36 query,
1.079 simboli, solo cinque query con dipendenze dichiarate. Non trasformare
questi conteggi in prove di generalizzazione o di copertura del progetto.
