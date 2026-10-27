# Lab Gutsy su CPU

**Campagna interrotta su richiesta dell'utente il 26 ottobre 2026: «Pesa troppo».** Entrambe le app Modal sono ferme, con zero task attivi. Nessun rilancio è previsto. Documentazione e prove preliminari restano conservate; la campagna principale non è stata completata.

Parti dal [disegno della campagna estesa](gutsy-campaign-design-2026-10-26.md) per vedere strategie, casi, budget proposto e criteri per decidere come proseguire.

Il lab valuta Gutsy v0.4 Q4_K_M per routing, compattazione fast-jev e selezione dei tool. Gutsy è il modello e il server locale, con API compatibile con Jev; fast-jev è una libreria di compattazione senza modello proprio, che riceve le decisioni da Gutsy attraverso una callback. Il servizio Jev non viene mai usato. Il requisito finale è un'esecuzione leggera su CPU locale; Modal è l'ambiente delle prove. Il primo pilot è completato. Il primo avvio della campagna estesa si è fermato nel controllo numerico; la [modifica del protocollo prima della verifica](campaign-preflight-amendment-2026-10-26.md) conserva l'esito e definisce la seconda esecuzione. Il secondo avvio è registrato nel [piano di esecuzione](campaign-execution-plan-2026-10-26.md#secondo-avvio-con-budget-ereditato); il lancio non attesta il completamento delle prove.

## Documenti principali

| Documento | Contenuto |
|---|---|
| [Briefing](gutsy-cpu-briefing-2026-10-26.md) | Modello, integrazioni, limiti e ipotesi iniziali |
| [Protocollo preliminare](gutsy-preliminary-tests-2026-10-26.md) | Casi e criteri del primo pilot |
| [Risultati del pilot](pilot-results-2026-10-26.md) | 47 richieste, 314 valutazioni, errori e prestazioni osservate |
| [Guida del pilot](pilot-guide.md) e [piano di implementazione](2026-10-26-gutsy-modal-pilot.md) | Riproducibilità, comandi e lavoro completato |
| [Campagna estesa](gutsy-campaign-design-2026-10-26.md), [schema dei conteggi](campaign-outline.json) e [piano di esecuzione](campaign-execution-plan-2026-10-26.md) | Confronti fra strategie, corpus, profili CPU e regole decisionali |

## Esperimenti Julia (27 ottobre 2026)

| Documento | Contenuto |
|---|---|
| [Pilot Julia su CPU](julia-pilot-results-2026-10-27.md) | Prima prova del modello su routing, tool e compattazione; target di memoria e latenza |
| [Ablazione dei criteri](julia-criteria-ablation-2026-10-27.md) | Criteri descrittivi contro letterali su 32 casi nuovi; esito negativo |
| [Diagnostica d'uso](julia-usage-diagnostic-2026-10-27.md) | Difetti confermati di fixture e adattatore; controllo ufficiale e direzione per il contratto |
| [Retest con contratto corretto](julia-adapter-retest-2026-10-27.md) | Contratto deterministico, prova offline della mappatura, retest controllato: 3/8, esito rosso |

La serie valuta `SupersonicLabs/Julia-1` come motore di decisione leggero su CPU locale. Il pilot misura, l'ablazione e la diagnostica correggono, il retest applica la regola pre-dichiarata: la compattazione con questo modello si chiude; le misure restano come evidenza.

## Note e verifiche di progettazione

1. [Fonti e comportamento di Gutsy](references/gutsy-source-notes.md).
2. [Disegno statistico](references/statistics.md).
3. [Strategie e modalità di esecuzione](references/strategies.md).
4. [Casi reali e provenienza dei dati](references/real-cases.md).
5. [Revisione indipendente della campagna](references/review.md).

Le note documentano la preparazione. Il disegno della campagna estesa raccoglie le scelte consolidate; il briefing conserva le ipotesi precedenti al pilot.

## Codice ed evidenza delle esecuzioni

Il [codice del pilot](../../evals/gutsy-decision-pilot/) rimane nell'area di valutazione.
I dati originali e i registri dell'esecuzione completata rimangono nel [run del pilot](../../.daodan/runs/2026-10-26-gutsy-modal-pilot/):

- [Manifest degli input](../../.daodan/runs/2026-10-26-gutsy-modal-pilot/artifacts/manifest.json) e [risposte originali](../../.daodan/runs/2026-10-26-gutsy-modal-pilot/artifacts/modal-results.json).
- [Scoring e ricostruzioni](../../.daodan/runs/2026-10-26-gutsy-modal-pilot/artifacts/scores.json) e [report generato](../../.daodan/runs/2026-10-26-gutsy-modal-pilot/artifacts/REPORT.md).
- [Revisione del pilot](../../.daodan/runs/2026-10-26-gutsy-modal-pilot/review.md) e [report consegnato immutabile](../../.daodan/runs/2026-10-26-gutsy-modal-pilot/execution-report.md).

Questi registri conservano i percorsi e gli hash storici. La [mappa degli spostamenti](relocations.json) collega i vecchi percorsi alla documentazione raccolta qui e registra gli hash prima e dopo lo spostamento. Non modifica l'evidenza del run.
