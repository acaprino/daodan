# Primo controllo remoto e modifica del protocollo prima della verifica

Il run `campaign-20261026-v1` si è fermato dopo **9 richieste e 75 domande di sviluppo**. Nessun caso core, di calibrazione o di verifica è stato eseguito. Le risposte, il registro e i 73 file sorgenti congelati sono conservati nel run locale. Il criterio originario di equivalenza numerica fra tre percorsi **non è stato superato**.

| Dominio del probe | Cache LRU contro cache intra-richiesta | Massimo scarto contro ricalcolo completo |
|---|---:|---:|
| Routing | 0 | 0,028715 |
| Tool selection | 0 | 0,017656 |
| Compattazione | 0 | 0,020810 |

La soglia preregistrata era 0,02. Nei tre input non sono cambiate le scelte argmax o le decisioni noul a soglia 0,5. È un'osservazione circoscritta: non dimostra equivalenza o assenza di cambiamenti su altri input. Il confronto riproducibile è in [preflight-v1-comparison.json](../../.daodan/runs/2026-10-26-gutsy-campaign/preflight-v1-comparison.json).

## Decisione per la seconda esecuzione

I due percorsi con cache dell'implementazione ufficiale producono risposte identiche su questi input; il ricalcolo completo è un percorso sperimentale distinto. La campagna deve valutare l'utilità del percorso con cache destinato all'uso leggero, senza presupporne l'intercambiabilità numerica con il ricalcolo completo.

La revisione `cached-paths-v2`, registrata prima di eseguire qualsiasi caso core, applica quindi queste regole:

1. Mantiene il gate di consistenza fra LRU e cache intra-richiesta, con la stessa soglia **0,02**.
2. Conserva il ricalcolo completo come fattore sperimentale separato: pubblica differenze numeriche e decisioni, senza dichiarare equivalenza o accelerazione a qualità invariata.
3. Mantiene identici casi, domande, oracle, ordine delle richieste e griglie di calibrazione. Non usa dati di verifica per la modifica.
4. Conserva il fallimento del primo run e congela un nuovo manifest e una nuova identità remota. Il rapporto distingue i contratti v1 e v2.
5. Eredita dal registro remoto v1 l'istante iniziale del limite globale di 22 ore e **93 domande già consumate o riservate**: 75 domande esplicite e 18 self-check. Il budget di 6 USD e il limite totale di 50.000 domande non ripartono da zero.

Questa è una modifica del protocollo motivata dai probe di sviluppo, non il superamento retroattivo del criterio originario. La revisione metodologica indipendente la considera adatta a un confronto diagnostico, con questi limiti espliciti. I risultati principali e l'idoneità per una CPU locale restano da misurare.
