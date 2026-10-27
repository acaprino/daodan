# Campagna estesa: piano di esecuzione

**Stop richiesto dall'utente il 26 ottobre 2026:** «Nulla, interrompi la campagna»; «Pesa troppo». Le due app Modal risultano `stopped`, con zero task attivi. Il piano seguente è conservato come storico e non autorizza altri lanci.

Autorizzazione: richiesta della campagna completa e successivo «ok ho aggionrato, andiamo» del 26 ottobre 2026. Limiti del disegno accettato: CPU, un container, 22 ore globali, budget operativo 6 USD, massimo 50.000 domande. Il requisito finale resta l'uso leggero su CPU locale.

## Passaggi

1. Materializzare corpus, provenienza, oracle e split; verificare indipendentemente le etichette.
2. Congelare manifest, codice, input senza oracle e regole di scoring; verificare checkpoint e ripresa.
3. Avviare un'unica campagna Modal con controlli preliminari automatici, risultati persistenti e arresto sui limiti.
4. Scegliere le policy soltanto sulla calibrazione, valutare la verifica separata e produrre il rapporto per dominio.

I moduli seguono il [contratto del banco di prova](campaign-module-contract.md). Codice e fixture sono in `evals/gutsy-campaign/`; registro ed evidenza in `.daodan/runs/2026-10-26-gutsy-campaign/`. Il pilot precedente rimane immutato.

## Quantità materializzate prima della revisione finale

Sono disponibili 600 scenari principali per dominio: 120 sviluppo, 120 calibrazione e 360 verifica. Si aggiungono 480 perturbazioni per dominio, 24 episodi di compattazione con più coppie, 480 decisioni di profiling, replay dei percorsi tool e cataloghi da 8 a 256 strumenti. Il manifest ricalcola il numero effettivo di domande: tool già esclusi e routing inapplicabile non consumano le massime quantità teoriche del disegno.

La componente pubblica comprende richieste costruite su codice di dieci progetti, adattamenti del benchmark BFCL e cronologie simulate con estratti del codice fast-jev. Queste ultime sono simulazioni con contenuto pubblico, non sessioni reali osservate. Licenze, revisioni e hash accompagnano gli artefatti; nessuna API dei tool descritti viene eseguita.

## Limite statistico emerso dalla revisione

Nel routing i casi condividono sia progetti sia template di richiesta. Unendo tutte queste dipendenze, la verifica forma un solo componente connesso. Per questo corpus il confronto principale sarà **diagnostico**: differenze appaiate, risultati per progetto e per template, senza intervallo di confidenza inferenziale. Non si dichiarano 360 prove indipendenti. La stessa verifica dei componenti si applica agli altri domini; con meno di due componenti non si calcola un intervallo bootstrap.

Questa precisazione precede qualsiasi nuova risposta Gutsy. Conserva l'utilità dell'esperimento per confrontare procedure, ma limita la generalizzazione statistica. I gruppi e le dipendenze sono pubblicati nel report.

## Controlli automatici su Modal

Il worker verifica identità Q4, hash di input/esecutore/pesi, tokenizer reale e limiti del contesto. Confronta i percorsi di cache su tre input di sviluppo; una divergenza oltre 0,02 interrompe la campagna prima dei test di qualità. Tale controllo non prova equivalenza su ogni input.

I probe di sviluppo misurano il tempo prima dell'apertura della verifica. La previsione usa token effettivamente valutati, numero di domande e overhead per richiesta; include il costo osservato dei checkpoint, un margine del 25% e 20 minuti per i riavvii. Lo scaling dei thread è un'ipotesi di pianificazione. Se la previsione supera 22 ore, il worker conserva l'evidenza preliminare e si ferma per ripianificare. Le misure reali rimangono distinte dalla stima.

Ogni tentativo viene salvato su Volume prima dell'inferenza; ogni risposta viene salvata prima del passaggio successivo. Dopo un crash, una richiesta dall'esito sconosciuto non viene ripetuta automaticamente. Il tempo globale e il conteggio dei tentativi sopravvivono alla ripresa. Il tetto monetario è operativo, non una garanzia della fatturazione Modal.

## Stato delle verifiche

Le revisioni degli oracle e dell'esecutore consentono il lancio con controlli preliminari. Sono passati 61 controlli locali sui domini, sul registro persistente e sul controllo dell'esecuzione. I test dell'esecutore usano un server simulato; non attestano l'esecuzione reale su Modal.

Il manifest congela input, oracle, scorer dei domini, griglie, dipendenze effettive ed esecutore. L'analizzatore aggregato del rapporto viene verificato separatamente e avrà una propria identità di versione; non può cambiare gli input, gli oracle o le regole di selezione dopo aver visto la verifica. I suoi controlli restano un gate della fase di rapporto.

Il rapporto finale richiede l'evidenza del run, copertura completa o lacune dichiarate, scoring verificato e decisione separata per routing, tool selection e compattazione. Il piano da solo non attesta il lancio né il completamento remoto.

## Lancio registrato

Il 26 ottobre 2026 è stata creata l'[app Modal](https://modal.com/apps/alfio-caprino/main/ap-nvojzM6xBMQ5RLunrQazsR) `ap-nvojzM6xBMQ5RLunrQazsR`, chiamata `fc-01M5WZ1DRKXC8VPMYJM2G0ZM89`. La [ricevuta locale](../../.daodan/runs/2026-10-26-gutsy-campaign/modal-invocation.json) lega il lancio all'input `10d662094411e776687c65bfa8f9964a5d9a56370c4d500158ee52152151f443`.

Il manifest finale pianifica **10.510 richieste e 33.580 domande**, con conteggi effettivi delle procedure gerarchiche da misurare. Il worker ha iniziato i controlli preliminari su CPU. Questo stato non attesta ancora il completamento o il superamento delle prove.

Il primo avvio si è poi fermato dopo 9 richieste e 75 domande, senza aprire core, calibrazione o verifica. La [modifica esplicita del protocollo](campaign-preflight-amendment-2026-10-26.md) registra il fallimento numerico e il contratto della seconda esecuzione, con budget globale ereditato.

## Secondo avvio con budget ereditato

Il secondo avvio del 26 ottobre 2026 usa l'[app Modal v2](https://modal.com/apps/alfio-caprino/main/ap-BVmF7rC21ZX4NNCGdco2gZ), chiamata `fc-01M5X0GMF4HXPKFK9XYV7SZGSS`. La [ricevuta v2](../../.daodan/runs/2026-10-26-gutsy-campaign/modal-invocation-v2.json) identifica gli artefatti effettivamente inviati in `artifacts-v2-final/`:

| Identità | SHA-256 |
|---|---|
| Input v2 | `4f14c292f8b0425736b7ea5b522d9cb7d82c9e6b8725fc400ef22eaec271fffe` |
| Esecutore remoto | `e3a0a00b6b3ad3805101d936f4e8f77e0127a9ffa206866879d1653ea36d39a7` |
| Analizzatore del rapporto | `2f75d0ff7331829487d316676c1a358367aaf8a19cb0ad1969ca24b2e467552d` |

Le 74 sorgenti vincolate dal manifest sono copiate e verificate in `frozen-sources-v2/`, per analizzare il run anche se il repository cambia in seguito. Input, oracle e ordine delle domande restano identici al primo avvio, salvo i metadati espliciti del nuovo controllo e del budget ereditato. La verifica dei byte ha preceduto l'inferenza del corpus.

Il registro remoto conserva la scadenza del primo avvio e 93 domande già impegnate (75 domande al modello e 18 riservate ai controlli di avvio). I limiti di 22 ore, 6 USD operativi e 50.000 domande si applicano all'intera campagna. Le nuove revisioni locali comprendono 24 controlli dell'esecutore e del registro, oltre a 35 controlli dell'analizzatore; le [revisioni dell'esecutore](../../.daodan/runs/2026-10-26-gutsy-campaign/runtime-v2-review.md) e [dell'analizzatore](../../.daodan/runs/2026-10-26-gutsy-campaign/analysis-review.md) restano distinte dalle prove del modello.

Il secondo avvio ha concluso 40 richieste preliminari (187 domande) e si è fermato prima del core: la previsione di 50,4 ore superava il limite di 22 ore. Il [rapporto v2](campaign-20261026-v2-results.md) conserva l'evidenza incompleta. **Qualità non misurata:** le tabelle di replay e delle baseline non rappresentano accuratezza osservata di Gutsy. La successiva richiesta di stop chiude ogni attività ulteriore della campagna.
