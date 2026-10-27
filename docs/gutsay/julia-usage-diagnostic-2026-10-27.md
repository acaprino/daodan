# Julia: verifica dell'adattatore e del protocollo

**La contestazione dell'utente è fondata: abbiamo trovato difetti negli input e nella composizione delle decisioni. Il consiglio di passare subito a Vela era prematuro.** Questo controllo corregge l'interpretazione dei precedenti risultati; non dimostra ancora che Julia sia adatta alla compattazione richiesta.

Il controllo è concluso: quattro casi già osservati, tre rappresentazioni, una prova positiva tratta dall'esempio ufficiale. Nessun addestramento, nuova campagna Modal o integrazione in Daodan. Routing e selezione dei tool non sono stati rieseguiti. I precedenti esperimenti restano immutati e disponibili come evidenza del comportamento dei rispettivi adattatori.

## Errori e limiti confermati

1. **Metadati sbagliati nei casi di risultato superato.** In N09–N12, la fixture attribuisce alla chiamata recente gli stessi input della vecchia chiamata. N10 mostra `inventory-S23` anche per la lettura che ha realmente prodotto `inventory-S24`. Il contenuto recente è nascosto nello stato consegnato al modello. Valutavamo quindi la capacità di riconoscere la sostituzione usando un riferimento errato e senza vedere la nuova evidenza. Il difetto è in `evals/julia-criteria-ablation/cases.py`, nella costruzione di `recent-copy`. La diagnostica corregge la copia privata di N10; non riscrive i casi storici.
2. **Due domande non compongono correttamente le tre azioni.** Chiedere se servono l'operazione con i suoi input e se serve l'output completo non equivale a chiedere se sia eliminabile tutta la coppia. In N02/N04 il fatto necessario sta nei primi 300 caratteri: può non servire né conoscere l'operazione né conservare l'intero output, ma eliminare tutto perde il fatto. La mappatura dei due `false` a `drop_call` introduce questa possibilità. L'oracle precedente valutava la necessità dell'output completo; non certificava questa composizione.
3. **Informazioni conservate poco visibili.** La cronologia costruita da fast-jev sostituisce i risultati con una nota di omissione. La nostra variante precedente esponeva il risultato candidato, ma non un elenco esplicito dei risultati recenti protetti con il loro contenuto e la garanzia di conservazione. Alcuni obiettivi dichiarano già la duplicazione, quindi non tutti i casi erano impossibili da risolvere; rimaneva lavoro implicito richiesto al modello.
4. **Lavoro deterministico delegato al classificatore.** Julia doveva ricavare il prefisso dei primi 300 caratteri e collegarlo alle regole della ricostruzione, dentro stati con molto testo di raccolta artificiale. Calcolare il prefisso e dichiarare il contesto conservato è responsabilità dell'adattatore. Il danno del rumore alla qualità resta un'ipotesi: questa prova non lo isola.
5. **Controllo iniziale insufficiente.** La parità fra due implementazioni della head verificava la stessa risposta, senza verificare che fosse quella corretta dell'esempio. Ora controlliamo anche la risposta attesa. Non sono emersi errori nell'ordine `false/true`, nell'attivazione della modalità di inferenza o nell'uso dell'API ufficiale.

Il JSON non è di per sé un uso scorretto: Julia accetta stati strutturati, domande e opzioni descritte. La [model card ufficiale](https://huggingface.co/SupersonicLabs/Julia-1) e il [dataset typed-decisions](https://huggingface.co/datasets/LocalLLaMA/typed-decisions) documentano questo contratto. Il problema accertato riguarda le informazioni e le decisioni che abbiamo costruito sopra quel contratto.

## Controllo positivo ufficiale

L'esempio di smistamento di un addebito duplicato, con le tre opzioni Billing, Shipping e Account access, restituisce correttamente **Billing**, probabilità 0,85446.

La scelta è corretta nelle quattro valutazioni previste: API typed, logits con head ottimizzata, logits con head originale, API typed ripetuta. I logits delle due head sono identici su questo esempio; la revisione indipendente conferma la corrispondenza con le probabilità dell'API.

L'input occupa **37 token**. La prima inferenza dopo il caricamento richiede 343 ms; la ripetizione a caldo **130 ms**. Il caricamento del modello/runtime richiede separatamente 50,94 secondi. Il tempo a caldo riguarda un solo esempio con possibili cache riutilizzate: non è una latenza garantita del servizio né una misura del nostro compito di compattazione. Un esempio positivo non sostituisce un benchmark bilanciato.

## Diagnostica sui quattro casi

Gli input e gli oracle sono stati congelati prima dell'inferenza. Sono casi di sviluppo già osservati, scelti per studiare i difetti; nessuna stima di generalizzazione.

| Caso | Azione minima corretta | Adattatore precedente | Evidenza conservata esplicita | Scelta diretta fra tre azioni |
|---|---|---|---|---|
| N02: fatti utili nel prefisso | Conserva prefisso | Conserva tutto | Conserva tutto | Conserva prefisso |
| N05: duplicato protetto | Elimina coppia | Conserva tutto | Conserva tutto | Conserva prefisso |
| N10: lettura superata | Elimina coppia | Conserva tutto | Conserva tutto | Conserva prefisso |
| N25: esito non ripetibile oltre il prefisso | Conserva tutto | Elimina coppia | Conserva tutto | Conserva prefisso |

| Misura descrittiva | Precedente | Evidenza esplicita | Scelta diretta |
|---|---:|---:|---:|
| Azioni minime corrette | 0/4 | 1/4 | 1/4 |
| Casi con fatti richiesti conservati | 3/4 | 4/4 | 3/4 |

N25 perde `applied=false` e `FOREIGN_KEY_CYCLE` sia con l'adattatore precedente sia con la scelta diretta. Rendere esplicita l'evidenza conservata evita questa perdita, ma conserva integralmente tutti e quattro gli output. La scelta diretta corregge N02 e sceglie il prefisso in tutti i casi, compreso N25 dove non basta. **Nessuna delle due varianti costituisce una soluzione validata.**

Il revisore ha ricostruito separatamente tutte le dodici risposte usando il vero fast-jev e ha enumerato offline le tre azioni per ciascuna fixture: gli oracle delle azioni minime e i fatti persi sono confermati. Tutti gli invarianti strutturali passano. Conservare token testuali di fixture non misura la riuscita del successivo compito affidato all'LLM.

### Differenze effettive fra le condizioni

La condizione precedente riusa esattamente gli input descrittivi del vecchio esperimento. La condizione con evidenza aggiunge il prefisso già calcolato, i risultati protetti completi e la garanzia della loro conservazione; corregge anche il riferimento recente di N10. La terza condizione riusa questo stato e sostituisce i due booleani con una scelta fra eliminare la coppia, conservare il prefisso e conservare tutto. Le descrizioni complete sono nell'input congelato.

Sono cambiamenti multipli: il confronto non separa l'effetto di ogni campo aggiunto dalla lunghezza o dalla correzione della fixture. L'ordine è fisso e la scelta diretta usa una domanda anziché due. Non è un confronto isolato delle prestazioni o una ricerca di prompt ottimali.

Il limite di contesto passa da 1.024 a 2.048 token per consentire la vista aggiunta. Nessun input supera 864 token o viene troncato. Per tutti e quattro i controlli, la revisione del runtime conferma input identici byte per byte, stessi token e probabilità esattamente identiche rispetto al precedente esperimento descrittivo. Anche N10 era già `keep`: una sospetta divergenza è stata risolta controllando i record originali, senza nuova inferenza.

## Risorse e riproducibilità

Una sola esecuzione locale su Intel Core Ultra 7 155H, Windows 11, CPU FP32, quattro thread, batch uno, head 512 e encoding rigoroso. Modello `SupersonicLabs/Julia-1`, revisione `a85b127321d580d65176c89ced8273f305745d85`; stesso checkpoint e ambiente dei precedenti esperimenti. Torch 2.14.0+cpu. La head ottimizzata è quella del runtime ufficiale.

Sono state eseguite **12 richieste di dominio, 20 domande misurate e quattro valutazioni di controllo**, 24 in totale. Durata monitorata **112,77 secondi**, caricamento incluso. Picco RSS combinato worker e monitor **871,5 MiB**, campionamento ogni 100 ms. Il limite dichiarato era 180 secondi, 45 secondi per richiesta e 2 GiB: nessun arresto, uscita zero. La misura RSS può contare pagine condivise più volte e non è una misura dei soli pesi.

Le richieste dei casi richiedono da 0,98 a 6,10 secondi, su 597–864 token per domanda. Le cache di encoding sono svuotate prima di ogni richiesta di dominio. Le durate descrivono questa sequenza e non dimostrano un vantaggio della nuova rappresentazione. Il test ufficiale breve mostra che una singola decisione semplice può essere molto più rapida; il requisito di compattazione leggera resta da verificare con input appropriati.

1. [Manifest](../../.daodan/runs/2026-10-27-julia-usage-diagnostic/manifest.json), [input](../../.daodan/runs/2026-10-27-julia-usage-diagnostic/input.json), [casi privati e oracle](../../.daodan/runs/2026-10-27-julia-usage-diagnostic/cases.json). Manifest SHA-256: `1c46c64c2d92bbfe44811d6ff58a04890c7f7a5da85607fa9b86f3e9e9c3ff1d`.
2. [Risultati](../../.daodan/runs/2026-10-27-julia-usage-diagnostic/results.json), [controllo positivo](../../.daodan/runs/2026-10-27-julia-usage-diagnostic/positive-control.json), [risposte originali](../../.daodan/runs/2026-10-27-julia-usage-diagnostic/records/), [risorse](../../.daodan/runs/2026-10-27-julia-usage-diagnostic/resources.json).
3. [Codice congelato](../../evals/julia-usage-diagnostic/diagnose.py), [controlli preliminari](../../.daodan/runs/2026-10-27-julia-usage-diagnostic/preflight-checks.json), [revisione indipendente](../../.daodan/runs/2026-10-27-julia-usage-diagnostic/diagnostic-review.md).
4. [Ablazione precedente](julia-criteria-ablation-2026-10-27.md) e [pilot precedente](julia-pilot-results-2026-10-27.md), conservati senza modifiche.

## Conseguenza per il prossimo protocollo

Il passo utile è correggere il contratto dell'adattatore prima di aumentare il numero di prove. Julia dovrebbe ricevere decisioni semantiche circoscritte con informazioni sufficienti; le regole di protezione, il calcolo dei prefissi e l'applicazione delle azioni rimangono codice deterministico. Questo è un indirizzo da verificare, non una proprietà dimostrata del modello.

1. Definire quali informazioni uniche sono ancora necessarie, rendendo espliciti obiettivo attivo, candidato, prefisso calcolato, fatti protetti e possibilità reale di recupero. Dimostrare prima offline che ogni risposta possibile si traduca nell'azione desiderata.
2. Verificare domande minime con controlli positivi e negativi bilanciati, descrizioni chiare, italiano/inglese e ordine delle opzioni variato. Separare la capacità di classificare dalla logica di compattazione.
3. Solo dopo, congelare l'adattatore e misurarlo su nuovi casi non usati per svilupparlo, includendo esempi realistici e successo del compito successivo, oltre a perdite, byte/token, latenza e memoria. Per routing e tool selection servono protocolli propri; questa diagnostica non ne cambia i risultati misurati.

Le misure precedenti restano valide per quegli input, ma non sostengono una bocciatura generale di Julia. I difetti confermati non spiegano automaticamente tutti gli errori. Non segue un passaggio automatico a Vela, un addestramento o una nuova campagna.
