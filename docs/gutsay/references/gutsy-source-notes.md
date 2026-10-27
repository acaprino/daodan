# Gutsy v0.4 Q4_K_M: note di ricerca

Data: 26 ottobre 2026. Perimetro: lettura delle fonti pubbliche e ideazione, senza download dei pesi, installazioni, benchmark o training. Le proposte non sono risultati sperimentali.

## Identità e maturità verificabili

Il repository GitHub pubblico è `kouhxp/gutsy`, con HEAD osservato `db5c2ec62fc81703938adbd714915b53a9fb0de1`, del 5 ottobre 2026. Il manifest Python dichiara `gutsy-inference` 0.4.0, Python >=3.10, NumPy e `llama-cpp-python>=0.3.35`. Il requisito llama.cpp è legato al supporto dell'architettura `qwen35`. Il repository è pubblico, non archiviato, creato il 1 ottobre 2026; la pagina mostra quattro commit. Questi sono segnali di un progetto giovane, non prove di manutenzione futura, compatibilità Windows esercitata, assenza di vulnerabilità o SLA. Codice e pesi dichiarano Apache-2.0; i dataset upstream hanno licenze diverse da rispettare se redistribuiti.

Fonti: [commit osservato](https://github.com/kouhxp/gutsy/commit/db5c2ec62fc81703938adbd714915b53a9fb0de1), [manifest](https://github.com/kouhxp/gutsy/blob/db5c2ec62fc81703938adbd714915b53a9fb0de1/gutsy-inference/pyproject.toml), [licenza](https://github.com/kouhxp/gutsy/blob/main/LICENSE), [model card](https://github.com/kouhxp/gutsy/blob/main/MODEL_CARD.md).

## Cosa fa realmente

Gutsy è un modello decisionale fine-tuned da `Qwen/Qwen3.5-0.8B`. Non genera riassunti, risposte di ragionamento o chiamate tool. Il runtime costruisce un prompt ChatML con thinking disattivato, stato, domanda e alternative A-P. Per choice e score aggiunge Z come opzione di rifiuto. Legge i logits del prossimo token delle sole lettere e applica softmax con temperatura. Il prompt va preservato durante l'adattamento.

L'API condivide uno stato fra più domande. Il costo di encoding dello stato è riutilizzato tramite snapshot del KV cache e dello stato ricorrente delle attention ibride. Ogni domanda resta una valutazione distinta; più domande nello stesso POST non sono un unico forward pass indipendente dal loro numero. Le richieste concorrenti vengono serializzate per modello.

Fonti: [prompt.py](https://github.com/kouhxp/gutsy/blob/main/gutsy-inference/gutsy_inference/prompt.py), [engine.py](https://github.com/kouhxp/gutsy/blob/main/gutsy-inference/gutsy_inference/engine.py), [backend](https://github.com/kouhxp/gutsy/blob/main/gutsy-inference/gutsy_inference/backend_llamacpp.py).

| Contratto | Evidenza |
|---|---|
| Endpoint Jev-style | `POST /v1/systemone`; altri endpoint `/api/alpha/decisions`, `/v1/decisions` |
| Modello Q4 esplicito | `gutsy-0.8b-v04-q4` |
| Stato | Testo o JSON |
| Domande | `noul`, `choice`, `score`; massimo 64 domande nel POST |
| Contesto | 8.192 token per stato più singola domanda e involucro del prompt |
| Alternative | 16 per chiamata del modello; choice fino a 255 tramite shortlisting ricorsivo |
| Output noul | `P(yes)`; nessuna proprietà confidence, margin o reject |
| Output choice | Distribuzione sulle opzioni, scelta, confidence, margin, reject |
| Output score | Livello e distribuzione ordinale; massimo 16 livelli |

Le probabilità choice e score sono condizionate sull'evento non-reject e sommano a uno separatamente da reject. Per la massa non condizionata di un'opzione si considera `(1-reject)*probability`. La confidence è una misura della concentrazione della distribuzione, non una misura indipendente di correttezza. Con shortlisting, reject significa nessuno dei finalisti, non necessariamente nessuno di tutti i candidati originali.

Su `/v1/systemone`, un nome modello sconosciuto come `jev-latest` viene sostituito con il default. La configurazione di esempio ha Q8 come default. Cambiare soltanto la base URL di un client Jev può pertanto usare Q8 senza rispettare la richiesta Q4. Occorre nominare Q4 e verificare il campo model della risposta.

Fonti: [schema.py](https://github.com/kouhxp/gutsy/blob/main/gutsy-inference/gutsy_inference/schema.py), [server.py](https://github.com/kouhxp/gutsy/blob/main/gutsy-inference/gutsy_inference/server.py), [runtime README](https://github.com/kouhxp/gutsy/blob/main/gutsy-inference/README.md), [configurazione](https://github.com/kouhxp/gutsy/blob/main/gutsy-inference/models.example.json).

## Q4, capacità e limiti

Il file Q4_K_M è circa 529 MB decimali, indicato dall'autore come 505 MB; sono circa 505 MiB. La dimensione del file non è la RAM dell'applicazione. A pesi e pagine mappate si aggiungono contesto, stato ricorrente, snapshot, buffer, Python e librerie. Il runtime configura per default una LRU fino a 512 MiB e quattro snapshot per modello. La configurazione demo registra Q8 e Q4 e il server li precarica entrambi. Un deployment CPU leggero dovrebbe configurare soltanto Q4 e limitare il numero di snapshot, misurando l'effetto sulla latenza.

La calibrazione Q4 pubblicata ha temperature choice circa 1.04484, yes/no circa 0.78567, score 1.0. Il campione di score è appena 26 elementi e la temperatura non è stimata. Il `cache_tol: 0.02` di Q4 serve al self-check cached contro full; non è una soglia di affidabilità applicativa. Il modello dichiara solo inglese: italiano, messaggi misti e codice con descrizioni italiane richiedono valutazione specifica o dati bilingui. Tradurre tutte le richieste con un altro LLM aggiungerebbe costo e latenza al percorso che si vuole semplificare.

Le misure di qualità sono pubblicate dall'autore, non verificate in questa ricerca: JevBench pubblico Q4 161/231, circa 69.7%, contro Q8 169/231, circa 73.2%. Non equivalgono all'accuratezza su compaction, routing o tool selection di Daodan. L'autore evidenzia difficoltà con aritmetica, nuove policy a più passaggi e ambiguità. Le latenze dichiarate Q8 su stati lunghi, mediana 4.3 secondi e p95 27 secondi sulla macchina dell'autore, non sono misure del deployment proposto. Non assumere che locale significhi latenza trascurabile.

Fonti: [file HF](https://huggingface.co/kouhxp/gutsy/tree/main), [calibrazione Q4](https://huggingface.co/kouhxp/gutsy/blob/main/gutsy-0.8b-v04-q4_k_m.calibration.json), [model card](https://github.com/kouhxp/gutsy/blob/main/MODEL_CARD.md), [registry.py](https://github.com/kouhxp/gutsy/blob/main/gutsy-inference/gutsy_inference/registry.py).

## Addestramento documentato e materiale mancante

La ricetta dichiarata è un full fine-tune con embedding token congelati e output head condivisa quindi congelata, master weights FP32 e compute BF16. La loss è cross-entropy più 0.5 volte Brier sulle lettere delle opzioni, con soft labels dove disponibili. Sono dichiarati 105.114 quesiti, una epoca, learning rate 1e-5, batch effettivo 256, scelta del checkpoint sul development set, GPU da 80 GB per circa un'ora. Q4 viene quantizzato dallo stesso checkpoint usato per Q8 e poi calibrato separatamente. Non è una stima del costo di una futura specializzazione Daodan.

Nel repository GitHub ispezionato sono pubblici runtime e documentazione, non trainer o checkpoint allenabile. Il tree HF osservato contiene GGUF Q4/Q8, calibrazioni, runtime e documentazione; non mostra pesi BF16/FP32, adapter LoRA o dataset. La README HF collega `gutsy-bench` e `gutsy-teacher` a sottodirectory del medesimo repository HF; entrambi i link rispondono 404. La riproducibilità dichiarata tramite `gutsy-bench/TRAINING_V04.md` non è stata verificata e quel percorso non è raggiungibile dai link pubblicati.

Le tre strade sono quindi:

1. Usare il checkpoint Q4 congelato, raccogliere esempi reali, calibrare per compito e valutare soglie. È la strada con meno prerequisiti mancanti.
2. Ottenere checkpoint allenabile, trainer e licenze dei dati dall'autore; provare LoRA o full fine-tune mantenendo prompt e readout delle lettere. Nessuna delle due tecniche va presentata come già validata per questo checkpoint.
3. Ripartire dai pesi ufficiali Qwen3.5-0.8B e ricostruire un decision model con loss e formato descritti. È una nuova specializzazione ispirata a Gutsy, non un continued fine-tune riproducibile di v0.4.

Il GGUF Q4_K_M è l'artefatto di inferenza previsto. QLoRA può allenare adapter sopra una base quantizzata in un ambiente di training, ma la quantizzazione NF4 comunemente usata da bitsandbytes non coincide con il GGUF Q4_K_M. Non proporre di aprire quel GGUF in PEFT come normale checkpoint allenabile. Il percorso di rilascio da ipotizzare è training su checkpoint supportato, eventuale merge, conversione, quantizzazione Q4_K_M, calibrazione dopo quantizzazione e nuova verifica della qualità.

Fonti: [ricetta dichiarata](https://github.com/kouhxp/gutsy/blob/main/MODEL_CARD.md), [listing HF](https://huggingface.co/kouhxp/gutsy/tree/main), [link trainer non disponibile](https://huggingface.co/kouhxp/gutsy/tree/main/gutsy-bench/), [link teacher non disponibile](https://huggingface.co/kouhxp/gutsy/tree/main/gutsy-teacher/), [PEFT quantization](https://huggingface.co/docs/peft/developer_guides/quantization), [Qwen originale allenabile](https://huggingface.co/Qwen/Qwen3.5-0.8B).

## Proposta di dati e criteri

Separare i tre contratti pur condividendo un eventuale unico modello: rilevanza di call/result; sufficienza di una classe modello; necessità di una capability tool. Usare domande semplici in inglese, stato strutturato e identificatori dinamici: evitare di insegnare nomi di modelli, prezzi correnti o tool che cambiano. Prezzi, permessi, limiti contesto e budget restano regole eseguibili.

Per compaction, l'etichetta rilevante è la necessità futura verificata, non la lunghezza o l'età del risultato. Per routing occorre osservare esiti di più modelli sullo stesso compito: la scelta storica del coordinatore da sola non prova che un modello più economico fosse sufficiente. Per tool selection, non usare il tool storicamente chiamato come unica verità: diversi strumenti possono essere equivalenti o complementari, e la metrica principale dovrebbe penalizzare l'esclusione di uno strumento necessario.

Dividere train, calibration e test per progetto/sessione e tempo; domande derivate dalla stessa trascrizione appartengono allo stesso split. Includere controesempi che differiscono in un solo requisito, opzioni riordinate, alias e descrizioni variate, assenza dell'opzione corretta e casi italiani. Una policy unica di soglia 0.5 sui tre compiti non è motivata. Validare separatamente la probabilità di perdita di evidenza, l'errore di sotto-dimensionamento del modello e il recall dei tool necessari. Le scelte non devono conferire autorizzazioni.

Queste sono proposte di disegno sperimentale, non capacità provate di Gutsy.

## Modal come laboratorio, CPU locale come destinazione

Proposta: usare Modal per raccolta e replay dei dataset, eventuale training GPU e quantizzazione; usare separatamente funzioni Modal CPU per verificare il medesimo artefatto GGUF e runtime destinato al locale. Le API ufficiali consentono di richiedere GPU, CPU e memoria e salvare checkpoint su Volumes. Non è necessario un servizio Modal nel percorso di inferenza locale.

Il confronto deve fissare hash di pesi/calibrazione, versione runtime e build llama.cpp, corpus, tokenizzazione, numero di thread e limite CPU. Modal interpreta cpu come core fisici e permette limite esplicito; una richiesta minima senza limite potrebbe usare più CPU di quelle previste. Separare warm inference, cold start e caricamento pesi; rilevare peak RSS e RAM di regime, n_ctx e cache. Variare lunghezza dello stato e numero domande, perché l'encoding condiviso non annulla il costo per domanda. I risultati su CPU Linux Modal non provano uguale latenza su CPU Windows: l'ultimo controllo va eseguito sulla macchina di destinazione.

Fonti: [Modal GPU](https://modal.com/docs/guide/gpu), [risorse CPU e memoria](https://modal.com/docs/guide/resources), [Volumes](https://modal.com/docs/guide/volumes).

## Copertura e questioni rimaste

Fonti lette: README GitHub e HF, model card, config, manifest, codice prompt/schema/engine/backend/server/registry, listing pubblico GitHub e HF, documentazione ufficiale PEFT e Modal. Nessuna esecuzione runtime, nessun benchmark, nessun audit di sicurezza completo, nessuna verifica del training originale.

Questioni da risolvere prima di un piano esecutivo: disponibilità del checkpoint allenabile Gutsy e trainer; RAM e latenza sulla CPU locale richiesta; qualità su italiano e dati Daodan; permessi e punti di intercettazione reali dell'host per restringere tool o modificare contesto/modello.
