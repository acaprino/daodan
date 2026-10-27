# Julia: criteri descrittivi nella compattazione

**I criteri descrittivi riducono le perdite critiche, ma trasformano Julia quasi in un selettore che conserva tutto. Questa variante non soddisfa il requisito di compattazione utile e leggera.** L'esperimento è completo; non segue una campagna automatica.

La richiesta «ok fallo» autorizza il confronto proposto dopo la ricerca sulla documentazione di Julia: formulazione originale con `false/true` contro descrizioni esplicite, su casi nuovi. La precedente campagna Gutsy resta interrotta e il pilot Julia precedente resta separato. Questa prova riguarda solo la compattazione: routing e tool selection non sono stati rieseguiti.

## Risultato principale

**32 scenari appaiati, 64 richieste, 128 domande misurate**, più quattro valutazioni di riscaldamento/parità. Tutti gli input sono stati accettati senza troncamenti. Una sola esecuzione CPU, nessun addestramento, installazione o servizio cloud.

| Misura | Risposte letterali | Criteri descrittivi |
|---|---:|---:|
| Decisioni corrette sulla necessità dell'output completo | 18/32 (56,25%) | 12/32 (37,50%) |
| Output necessari riconosciuti | 0/12 | 11/12 |
| Output superflui conservati integralmente | 2/20 | 19/20 |
| Accuratezza bilanciata sulle due classi | 45,00% | 48,33% |
| Scenari con perdita di fatti critici | 14/14 | 1/14 |
| Riduzione dei byte serializzati | 33,99% | 1,29% |
| Mediana della richiesta completa (due domande) | 1,64 s | 1,63 s |
| p95 descrittivo delle 32 richieste | 2,48 s | 3,37 s |

Le descrizioni correggono 11 decisioni e ne peggiorano 17; quattro restano invariate. L'accuratezza complessiva scende di 18,75 punti percentuali. Il forte miglioramento nel riconoscere gli output necessari è accompagnato dalla quasi scomparsa della capacità di eliminare quelli superflui. L'accuratezza bilanciata tiene conto del campione con 12 output necessari e 20 dispensabili: nessuna delle due formulazioni mostra una buona separazione delle classi.

Con i criteri descrittivi, fast-jev conserva integralmente 30 output, ne tronca uno ed elimina una coppia chiamata/risultato. I messaggi serializzati passano da 57.721 a 56.976 byte: **745 byte risparmiati**. Sono byte JSON, non token del modello destinatario. Nei 16 scenari italiani conserva tutto, con zero byte risparmiati. Questa osservazione riguarda soltanto questi casi sintetici con istruzioni inglesi.

Il confronto deterministico «conserva tutti gli output» avrebbe 12/32 decisioni esatte, ma nessuna perdita di fatti e nessuna riduzione. La variante descrittiva ottiene lo stesso numero di decisioni esatte, perde fatti critici in uno scenario e risparmia solo l'1,29%. La formulazione letterale, invece, elimina troppo. Anche la previsione costante «output completo non necessario» avrebbe 20/32 etichette esatte: l'accuratezza isolata non è un criterio sufficiente di utilità.

### La perdita ancora presente

N25 chiede di riportare l'esito registrato di una migrazione e vieta di ripeterla. Il risultato contiene `applied=false` e `FOREIGN_KEY_CYCLE`, oltre i primi 300 caratteri. La variante descrittiva assegna circa 0,341 alla necessità del risultato e 0,024 alla chiamata; con la soglia preregistrata di 0,5, fast-jev elimina la coppia e perde entrambi i fatti. Sono dati di una fixture: nessuna migrazione reale è stata eseguita.

## Che cosa abbiamo isolato

Le [indicazioni ufficiali di Julia](https://huggingface.co/SupersonicLabs/Julia-1#reproduce-typed-decision-accuracy) documentano un beneficio delle descrizioni booleane nel loro benchmark. Qui viene verificato il trasferimento di quella pratica al nostro compito, senza presumere lo stesso beneficio.

Ogni coppia riceve lo stesso stato e le stesse due domande prodotte da fast-jev. La sola differenza è l'aggiunta di criteri descrittivi per la chiamata e per il risultato. Il testo esatto dei criteri è congelato nel [protocollo](../../evals/julia-criteria-ablation/PROTOCOL.md). Ordine dei casi mescolato con seme fisso; ciascuna variante viene eseguita per prima in 16 coppie. Nessun cambio di soglia, prompt o label dopo aver osservato le risposte.

Lo stato condiviso mostra il contenuto del risultato candidato, come la precedente rappresentazione B. Specifica che bisogna ridurre la cronologia preservando i fatti necessari, che il troncamento conserva i primi 300 caratteri e che un recupero è possibile soltanto quando una fonte sicura è esplicitamente disponibile. Questo adattamento comune corregge l'affermazione generale dello stato upstream secondo cui si possono sempre rieseguire gli strumenti. Il confronto misura l'effetto dei criteri con questo adattatore; non misura il comportamento upstream senza modifiche e non è un confronto diretto con i vecchi otto scenari.

I casi nuovi coprono otto famiglie, quattro scenari ciascuna: prove uniche non recuperabili, duplicati, risultati superati, informazioni irrilevanti, fonti immutabili recuperabili, azioni non ripetibili, evidenza negativa utile e istruzioni avversarie citate nei risultati. Sono 16 stati inglesi e 16 italiani; domande e criteri restano inglesi. I casi sono sintetici e condividono un formato di raccolta: non rappresentano una distribuzione di traffico reale né 32 osservazioni indipendenti di produzione.

L'oracle distingue la necessità dell'output completo dall'importanza dei fatti. In N02/N04 i fatti sono critici ma stanno nel prefisso conservabile: troncare è sufficiente, eliminare la chiamata perde comunque i fatti. Per la domanda sulla chiamata non è stata inventata un'etichetta umana: le sue risposte incidono sulla ricostruzione, ma non vengono presentate come accuratezza classificatoria verificata.

### Ricostruzione reale

Ogni risposta è applicata al vero fast-jev, revisione `e3f262a7f4d42bd8dd32ced30d26176f7cb545b0`. Gli invarianti dei messaggi passano in tutte le 64 ricostruzioni. Prima dell'inferenza sono state controllate anche 96 ricostruzioni deterministiche: conserva, tronca e rimuovi per ogni scenario.

La formulazione letterale perde fatti richiesti in 18 scenari. Quattro hanno una fonte immutabile recuperabile con percorso e hash: il recupero deterministico verificato lascia 14 perdite. La variante descrittiva ha una sola perdita sia prima sia dopo il recupero. Il recupero è un risultato dell'adattatore, non un merito del modello. I token testuali richiesti sono controlli sintetici di conservazione, non una misura di riuscita del successivo compito LLM.

## CPU e limiti operativi

Windows 11, stessa macchina Intel Core Ultra 7 155H del pilot precedente. Julia ufficiale `SupersonicLabs/Julia-1`, revisione `a85b127321d580d65176c89ced8273f305745d85`; pesi SHA-256 `df853bf7fe424420011f3d0c47a05d7341aa9eefa7fb9f203ea4aada4ad95b72`. Python 3.13.14, Torch 2.14.0 e Transformers 5.0.0. FP32, quattro thread, batch uno, contesto massimo 1.024 token, head 512, encoding rigoroso e head CPU ottimizzata.

Il modello resta residente; le cache di tokenizzazione/encoding vengono svuotate prima di ogni richiesta cronometrata. I tempi includono la tokenizzazione e il costo delle descrizioni aggiunte. Non misurano un servizio con cache calda, una singola domanda o una configurazione CPU ottimizzata con altri batch. Il p95 descrive questo piccolo campione, senza garanzia di servizio.

Il tentativo monitorato dura **165,1 secondi**, caricamento del modello/runtime incluso (42,8 secondi). Picco RSS combinato worker e monitor **869,9 MiB**; worker 844,2 MiB. Nessuna delle 64 richieste termina entro un secondo. Target memoria di 1 GiB rispettato; target di un secondo per richiesta non raggiunto. Il controllo campiona ogni 100 ms e interrompe oltre 2 GiB, 600 secondi totali o 45 secondi per richiesta: nessun arresto, uscita zero. È un controllo campionato, non un limite del sistema operativo, e la somma RSS può contare pagine condivise più volte.

La parità fra head ottimizzata e originale su due righe distinte dai casi restituisce le stesse scelte; massimo scarto nei logits circa 0,00000012. Il controllo è circoscritto alle due righe e non prova equivalenza universale.

## Decisione

Il segnale preregistrato richiedeva almeno 10 punti percentuali di miglioramento dell'accuratezza senza aumentare le perdite critiche: **non è raggiunto**. Rimane inoltre una perdita critica. Questa formulazione non supporta compattazione autonoma e non risolve il requisito di leggerezza nella latenza misurata.

Il prossimo intervento sensato, se autorizzato separatamente, è definire una compattazione deterministica per duplicati verificati e risultati sicuramente superati, con protezione esplicita dei fatti critici. Julia può essere rivalutata su decisioni residue soltanto con una nuova ipotesi verificabile. Questa prova non giustifica addestramento, una campagna più grande o una modifica automatica di soglia. Nessun nuovo test viene avviato a seguito di questo risultato.

## Evidenza riproducibile

1. [Manifest](../../.daodan/runs/2026-10-27-julia-criteria-ablation/manifest.json), [input effettivi](../../.daodan/runs/2026-10-27-julia-criteria-ablation/input.json) e [casi/oracle separati](../../.daodan/runs/2026-10-27-julia-criteria-ablation/cases.json). Manifest SHA-256: `3aca560305a8976110cfa0e41c3c4a9d3fd47a55968d8f68eec9db71b2853184`.
2. [Risposte originali](../../.daodan/runs/2026-10-27-julia-criteria-ablation/execution/records/), [misure delle risorse](../../.daodan/runs/2026-10-27-julia-criteria-ablation/execution/resources.json) e [risultati completi per caso, famiglia e lingua](../../.daodan/runs/2026-10-27-julia-criteria-ablation/results.json).
3. [Verifica preliminare indipendente](../../.daodan/runs/2026-10-27-julia-criteria-ablation/preflight-review.md), [verifica indipendente dei risultati](../../.daodan/runs/2026-10-27-julia-criteria-ablation/results-review.md) e [controllo delle 96 ricostruzioni](../../.daodan/runs/2026-10-27-julia-criteria-ablation/offline-reconstruction-check.json).
4. [Codice e protocollo congelati](../../evals/julia-criteria-ablation/), [pilot precedente separato](julia-pilot-results-2026-10-27.md).
