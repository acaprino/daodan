# P8: contesto nel ciclo di sviluppo

Run: `.tritech/daodan/runs/code-context-p8-20261024/`.
Baseline pubblicata: `f3e90cfcee73e2ed833693f2440fed27f5759540`.
P0–P7 conservano le proprie consegne.

## Comportamento

`cycle_packets.py` collega preflight, task e post-task tramite le CLI pubbliche
di protocollo e mappa. Non importa moduli privati di altri plugin, non aggiorna
il ledger, non fa dispatch e non esegue chiamate LLM o refresh impliciti.
Il coordinatore mantiene autorizzazioni, aggiornamenti, verifiche e consegne.

Il perimetro di lettura deriva dai file del binding del protocollo dopo le
esclusioni; il write set resta quello del task registrato. Le coordinate sono
tradotte esplicitamente anche nei sottoprogetti Git. Proposte della mappa non
allargano il write set. Requisiti e gate registrati vengono conservati.

La proiezione pubblica I1 accompagna ora il pacchetto CLI/MCP con percorso e
digest: componenti per file, chiamate confermate citate, freshness, limiti e gap.
Non trasforma il grafo del codice nelle precedenze del piano. L'envelope resta
compatibile con il contratto I1; il prototipo locale non è una dipendenza runtime.

I receipt legano candidato, task, scope, requisiti, gate, destinatario e artefatti.
Una modifica del codice, del task o degli indici blocca il dispatch dipendente.
La sola registrazione della consegna, che aumenta la revisione del ledger senza
cambiare gli input di esecuzione, non invalida il contesto. Una seconda barriera
controlla il candidato dopo la verifica del destinatario.

Al post-task il coordinatore aggiorna esplicitamente mappa e candidato. Il receipt
precedente mantiene la base; gli obblighi precedenti e nuovi restano aperti.
Intenti e pubblicazioni esclusive consentono la ripresa dopo un'interruzione.
Un artefatto parziale non conta come consegna.

## Verifiche e limiti

Gli oracoli RED e GREEN del run includono sette test I1 e quattordici scenari
lifecycle: bug senza diff, firma cambiata, documentazione e test, scope escluso,
sottoprogetto Git, candidato mutato, indici mutati e interruzione/ripresa.
Due regressioni aggiuntive hanno verificato il budget effettivo della richiesta
e una modifica concorrente durante il conteggio del destinatario.

I gate comuni, le suite richieste, il build dei cinque host, la revisione
indipendente e la CI del commit esatto vengono registrati nel run. La milestone
resta aperta finché tutti passano. I conteggi e gli eventuali skip appartengono
alle ricevute delle verifiche, senza sostituire la copertura delle applicazioni.

I quattro riferimenti lifecycle diminuiscono di parole; nessun tetto aumenta.
La contabilità CLI resta in caratteri: senza contatore esplicito del destinatario
il dispatch conserva il controllo aperto. Nessuna garanzia di risparmio totale in
token, compatibilità runtime universale o correttezza del progetto è dedotta da
questi test. P9 collega gli altri consumatori; P10 misura il percorso completo.

Il candidato pubblicabile parte dalla baseline verificata e contiene soltanto
gli interventi P8. Le modifiche concorrenti nei riferimenti, sidecar e versioni
del checkout principale sono preservate tramite sostituzioni circoscritte,
registrate con i byte precedenti. Il commit locale di documentazione del grafo
rimane estraneo alla pubblicazione.
