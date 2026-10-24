# P8: contesto nel ciclo di sviluppo

Run: `.tritech/daodan/runs/code-context-p8-20261024/`.
Baseline: `f3e90cfcee73e2ed833693f2440fed27f5759540` (P7 pubblicato); il candidato finale
parte da `9d867bf219081194cad28befb756bb2628b3ae3a`, che ne contiene già una stesura intermedia.
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
controlla il candidato dopo la verifica del destinatario. Un'invocazione della
CLI incompleta o illeggibile esce con stato 2 e nessun traceback; un'operazione
rifiutata dal ciclo esce con stato 1.

Al post-task il coordinatore aggiorna esplicitamente la mappa in un nuovo manifest
e il candidato; un refresh sul posto è rifiutato, perché la base del passo
successivo è il candidato del receipt precedente, vincolato per percorso e byte e
timbrato prima che il provider lo legga. Gli obblighi precedenti e nuovi restano
aperti. Intenti e pubblicazioni esclusive consentono la ripresa dopo
un'interruzione; quando gli input di un receipt si spostano, lo stesso intento
riparte in un nuovo tentativo e i tentativi precedenti restano come evidenza. Il
primo risultato del provider vince: una preparazione concorrente lo adotta.
Un artefatto parziale non conta come consegna.

## Verifiche e limiti

Gli oracoli RED e GREEN del run includono sette test I1 e quattordici scenari
lifecycle: bug senza diff, firma cambiata, documentazione e test, scope escluso,
sottoprogetto Git, candidato mutato, indici mutati e interruzione/ripresa.
Le regressioni aggiuntive hanno verificato il contratto d'invocazione della CLI
(uscita 2 senza traceback su argomenti mancanti o file illeggibili), il budget
effettivo della richiesta e una modifica concorrente durante il conteggio del
destinatario.

I gate comuni, le suite richieste, il build dei cinque host, la revisione
indipendente e la CI del commit esatto vengono registrati nel run. La milestone
resta aperta finché tutti passano.

La revisione indipendente ha richiesto tre giri. Il primo (R1–R7) ha mostrato
documenti di forma errata che uscivano con traceback: la validazione puntuale è
stata sostituita da un contratto dichiarativo unico per config, richiesta,
destinatario, receipt e consegne di protocollo e provider (forma e tipo degli
elementi), con uscita 2 per ogni documento d'ingresso non valido e uscita 1
senza traceback per un'operazione rifiutata. Il secondo (N1–N8) ha trovato la base
della mappa non vincolata a un'evidenza, l'impossibilità di rigenerare un intento
dopo uno spostamento degli indici, la corsa tra preparazioni identiche, un cap
della proiezione I1 che poteva escludere il sito di modifica proposto o consumare
tutti gli archi su una sola coppia di file: tutti corretti alla radice e coperti da
test che falliscono sul codice precedente. L'help documenta ora ogni documento
d'ingresso e dice che la CLI non conta i token del destinatario (verifica con
`verify_cycle(..., token_counter=...)` dal dispatcher). Il terzo giro non ha
trovato difetti Critical, High o Medium e ha confermato chiusi R1, N1, N3, N4,
N5, N7 e N8. Restavano cinque residui Low: N2 e N6 ancora parziali, il receipt che
portava l'`origin_revision`, un `_claim` che catturava ogni `ValueError` e
`NaN` o `Infinity` in un documento d'ingresso che uscivano con 1 invece di 2.
Sono stati corretti dopo la revisione: la collisione ha una classe propria, il
tetto dei tentativi vale per chiamata e parte dalla generazione più recente, il
receipt non porta più la revisione del ledger, le costanti non JSON danno uscita 2
e l'help nomina i sei tetti di budget, il contratto `context.toml` e la `policy`
del destinatario. Quattro test nuovi li coprono; questa correzione non ha avuto un
quarto giro di revisione e il suo unico controllo indipendente sono quei test.
I conteggi e gli eventuali skip appartengono
alle ricevute delle verifiche, senza sostituire la copertura delle applicazioni.

I quattro riferimenti lifecycle diminuiscono di parole; nessun tetto aumenta.
La skill lifecycle resta sotto il tetto di 630 parole (597 sull'albero
principale, 599 sul candidato) e il brief `context-cycle.md` di 22 parole entra
nei passi del ciclo senza aumentare i tetti. Il gate comune delle dipendenze
conta il riferimento al protocollo di lavoro solo quando la frase nomina la parola
`skill`: la prima stesura accorciata l'aveva persa e il linter l'ha segnalata sul
candidato, la frase finale la contiene e il gate passa (549 riferimenti, 86 skill
load).
La contabilità CLI resta in caratteri: senza contatore esplicito del destinatario
il dispatch conserva il controllo aperto. Nessuna garanzia di risparmio totale in
token, compatibilità runtime universale o correttezza del progetto è dedotta da
questi test. P9 collega gli altri consumatori; P10 misura il percorso completo.

Il candidato pubblicabile parte da `HEAD` e contiene soltanto gli interventi P8
(merge a tre vie registrato in `v2/rebase-report.json`). Le modifiche concorrenti
non committate del checkout principale (rinomina del protocollo, ADR, specialisti
di review) restano fuori e intatte. Il ruolo `senior-review:code-auditor` della
roster non esiste più dopo la scomposizione dei revisori: la revisione è stata
eseguita da un agente generico che applica `reviewer-common.md` e i controlli di
correttezza locale; la roster registrata nel run resta quella calcolata allora.
