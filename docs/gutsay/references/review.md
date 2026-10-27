# Revisione indipendente del disegno della campagna Gutsy

Data: 26 ottobre 2026. Revisore: `/root/campaign_design_review`.

**Verdetto: disegno coerente come proposta di campagna, non ancora specifica pronta al lancio.** Non sono emersi errori aritmetici nei massimi dichiarati. Corpus, oracle, runner persistente e riserva di stress sono correttamente indicati come lavoro da materializzare. Nessuna inferenza o risorsa cloud è stata avviata da questa revisione.

## Controlli effettuati

Lettura integrale del [disegno della campagna](../gutsy-campaign-design-2026-10-26.md) e del relativo [campaign-outline.json](../campaign-outline.json).

- Core: routing 8.400, tool 10.800, compattazione 7.200; totale 26.400 domande.
- Robustezza 8.160, prestazioni 4.160 e dipendenze di compattazione 1.152: totale definito 39.872.
- Riserva 10.128: tetto complessivo 50.000, comprensivo dei tentativi.
- Prestazioni: sei workload per quattro profili, due modalità e dieci repliche producono 480 decisioni complete. Con 52 domande per giro, il totale di 4.160 e il massimo di 2.320 richieste HTTP sono coerenti.
- Le 1.800 unità sono target di scenari-base da acquisire, non corpus già disponibile né famiglie iid. Le varianti restano raggruppate per provenienza; il pilot già osservato resta fuori dalla verifica nuova.

Sono correttamente distinti: confronti di rappresentazione e domanda; strategie tool simulate e loro latenza realmente eseguita; errore del modello e protezione del controller; thread e quota fisica CPU; singolo lancio e possibile rischedulazione su altro host. La formulazione a due domande di routing è limitata ai casi con metadati sufficienti. I limiti downstream e la necessità di licenze per i dati esatti restano espliciti.

## Tre decisioni da chiudere prima dell'implementazione del lancio

1. **Rendere eseguibile la selezione della policy.** Il disegno richiede una griglia e una regola preregistrate, ma non specifica ancora soglie candidate, bande di astensione, vincoli di ammissibilità e tie-break. Anche termini come “qualità adeguata” e “contributo marginale” richiedono un criterio osservabile per ogni dominio. Inserire questi valori nel manifest prima del run, compreso l'esito `nessuna candidata`; non lasciarli alla lettura manuale della verifica finale.

2. **Fissare il denominatore del confronto routing e degli input fuori limite.** Il testo già prevede sottoinsieme comune, fallback e copertura. Rendere meccanica la regola: maschera di applicabilità determinata dai soli metadati prima delle risposte; confronto paired sul medesimo insieme; tabella sull'intero corpus con input incompatibili, astensioni, fallback e loro costo. Non consentire che una strategia risulti migliore solo perché ignora casi difficili o richiede una rappresentazione che non entra nel budget.

3. **Specificare la molteplicità dei confronti paired.** La correzione Bonferroni per i limiti binomiali dei tre domini è esplicita e corretta. Per gli intervalli bootstrap dei tre contrasti principali, scegliere ora intervalli simultanei/correzione preregistrata se si intende dichiarare superiorità inferenziale; in alternativa etichettarli come intervalli descrittivi separati. Il trattamento dei contrasti secondari deve rimanere coerente con questa scelta.

Questi punti non richiedono nuovi esempi o inferenze per essere decisi. Gli altri prerequisiti di lancio sono già dichiarati nel documento: dati e diritti verificati, oracle, split, conteggio espanso, checkpoint/resume, parità e tetto di durata/spesa.

## Limiti della revisione

Revisione del disegno e della contabilità, non audit del corpus o del futuro codice. Non sono state verificate una per una le licenze dei dataset candidati, la fatturazione del workspace, la disponibilità di 1.800 scenari o il funzionamento del runner persistente ancora da costruire. Non vi è un verdetto sulla qualità di Gutsy oltre alle evidenze del pilot già citate dal coordinatore.
