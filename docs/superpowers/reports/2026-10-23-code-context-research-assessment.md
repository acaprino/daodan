# Valutazione della ricerca sul perimetro del codice

Data: 23 ottobre 2026. Esito: utile per rendere operativi P6/P7 e rafforzare
P3/P5/P10 del piano (rimosso il 2026-10-26).
Sono aggiornamenti di disegno; nessun algoritmo di produzione è stato eseguito
o consegnato attraverso questa valutazione.

## Provenienza e livello di verifica

Il [materiale ricevuto](2026-10-23-code-context-research-input.md) è conservato
senza modifiche dall'allegato dell'utente. SHA-256:
`1c1cf2a7e14cfa356eaaa25f1d2cb5e0b1ee3277d4466a6c91aafec48c355dc2`.
È una sintesi di ricerca fornita dall'utente, non un insieme di esperimenti
riprodotti da Daodan. Questa valutazione non certifica ogni release, licenza,
formula, percentuale o repository citato nella sintesi.

Verifiche mirate su fonti primarie:

- [LocAgent, ACL 2025](https://aclanthology.org/2025.acl-long.426/): confermati
  pubblicazione, localizzazione guidata dal grafo e artefatto ufficiale.
  Non riprodotti gli esperimenti o tutte le ablation riportate nell'allegato.
- [RepoGraph v2, tabella 4](https://arxiv.org/html/2410.14684v2): verificato il
  confronto fra espansione piatta a uno e due hop. Nel suo esperimento il
  contesto aumenta e il resolve rate diminuisce. Questo sostiene il confronto
  con espansione selettiva, non una soglia universale di hop.
- [Skip the Compressor v1](https://arxiv.org/html/2610.21073v1): verificati
  selezione del sorgente verbatim, confronto a budget per issue e limiti dei
  risultati. Ne deriviamo un'alternativa file intero/corpo con prerequisiti,
  non la regola che ogni pacchetto debba contenere file interi.
- [CodeNib v2, sezione 9.5](https://arxiv.org/html/2607.25431v2): confermata la
  distinzione fra aggiornamento concluso e accordo col rebuild, incluso il
  risultato held-out di 13/24 per symbol repair. Motiva il controllo di
  inventario e replay oltre al successo del processo. Non adottiamo il
  prodotto o le sue dipendenze per questo solo riscontro.

## Decisioni recepite

| Decisione | Conseguenza nel disegno | Verifica prevista |
|---|---|---|
| Quattro perimetri separati | `analysis`, `edit_candidates`, `potential_impact`, `validation_obligations` | Chiamante potenzialmente coinvolto presente nell'impatto senza edit automatico. |
| Obblighi rigidi separati dai rank | Ogni rappresentazione dichiara quali prove può fornire | Similarità e card non sostituiscono sorgente corrente o test eseguiti. |
| Packing con prerequisiti | Corpo, firma, card e file sono alternative; costo ricalcolato dopo deduplicazione | Prerequisiti condivisi, upgrade che perde un supporto, entità identiche ma distinte. |
| Budget multipli e residui | Limiti su contesto, token cumulativi, lavoro locale e round | Hub, timeout e split conservano obblighi e cursore. |
| Invalidazione più completa | Hash dell'input realmente codificato e dipendenze negative/ambientali | Export prima assente, rename, registro popolato, confronto con rebuild. |
| Arresto con significato limitato | `ready_for_attempt` è preparazione della fase, non successo del task | Gap critico non cancellabile dal budget o da un punteggio basso. |

La versione iniziale del planner ordinava classi di evidenza. Quella baseline
rimane nel benchmark. Il nuovo packing è un candidato misurabile, con selezione
per utilità marginale rispetto al costo aggiuntivo e controlli rigidi separati.
La complementarità fra contratto e implementazione, le alternative di
rappresentazione e i costi condivisi impediscono di attribuirgli automaticamente
le garanzie dei problemi classici di knapsack o submodular maximization.

`needs_split` significa che il metodo non ha trovato il supporto richiesto
entro i propri limiti; non prova che nessuna soluzione possa entrare. Anche
il perimetro della patch richiede diagnosi e validazione del proprietario:
minimizzare il contesto non determina la modifica corretta più piccola.

## Adattamenti necessari a Daodan

La sintesi propone azioni adattive che possono includere test e riproduzioni.
In Daodan il mapper rimane statico: quelle azioni spettano a lifecycle/testing
e i relativi risultati entrano come prove distinte. Le decisioni del DAG restano
nei contratti approvati; un arco statico non autorizza da solo una task o un edit.

Nessuna promozione automatica di un embedder, di Qdrant, di un nuovo parser o
di un engine alternativo. Il gate P5 verifica supporto, licenza, compatibilità,
caricamento e qualità sul nostro holdout. CP-SAT può essere un confronto offline
su piccoli insiemi; SDG/IFDS completo, GNN e arresto statisticamente calibrato
restano fuori dal primo incremento. Non introdurre chiamate LLM per assegnare
un valore a ogni nodo o ogni espansione.

## Esito pratico

La ricerca fornisce una base per costruire e confrontare un algoritmo, non
una prova anticipata di risparmio o completezza. Il criterio di consegna resta:
meno uso cumulativo del modello a qualità e obblighi preservati, misurato
su task non usati per tarare la policy. Il
disegno aggiornato (rimosso il 2026-10-26)
contiene il pseudocodice e il piano contiene le regressioni corrispondenti.
