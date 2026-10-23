# Prova locale CodeRankEmbed: metadati e corpi Python

Data: 23 ottobre 2026. Stato: esperimento completato; gate di adozione P5 aperto.
Evidenza strutturata: [metriche, provenienza e ranghi dei target](runs/2026-10-23-coderank-local.json).

**Esito:** CodeRankEmbed funziona offline su CPU e migliora il recupero rispetto
alla baseline che vede soltanto metadati. Quando entrambe le pipeline ricevono
anche i corpi Python, la baseline lessicale supera la combinazione con embedding.
Questa configurazione non giustifica l'abilitazione predefinita di CodeRankEmbed.

## Configurazione e corpus

- Modello base: [nomic-ai/CodeRankEmbed](https://huggingface.co/nomic-ai/CodeRankEmbed),
  137M parametri, licenza MIT. Eseguita la conversione comunitaria
  [mrsladoje/CodeRankEmbed-onnx-int8](https://huggingface.co/mrsladoje/CodeRankEmbed-onnx-int8)
  alla revisione `e74f446dc6e67e29fcee77213472c142f73a6bbb` già prevista dal benchmark.
- ONNX: 138.619.279 byte; SHA-256 verificato prima dell'inferenza:
  `4eae31d09b1843103a1ebd5e2b2e24b5a5cad441a33906b35b12b1e2ed91d1db`.
  È la conversione corretta con `reduce_range`, descritta dal suo autore.
- Intel Core Ultra 7 155H, Windows build 26200, solo `CPUExecutionProvider`.
  Runtime isolato già presente: Python 3.11.15, ONNX Runtime 1.31.0,
  NumPy 2.4.6, tokenizers 0.23.3, huggingface_hub 2.2.0.
  Lo snapshot è stato generato separatamente con Python 3.13.
- Snapshot congelato alle 10:20:11 Europe/Rome: commit `849797acbf8a`, checkout
  con modifiche non committate. Corpus: 1.423 simboli di 65 file sotto `plugins/`.
  Include 79 regole di stile come distrattori; il gold riguarda codice Python.
- 36 query esistenti: 12 nomi esatti, 4 traceback, 8 descrizioni inglesi,
  6 italiane, 6 frammenti di codice. Nessuna query modificata o taratura dei pesi.
- Prima prova: nomi, firme, percorsi e vicini del grafo. Seconda: stessi ID,
  ordine, adjacency e gold; aggiunto il sorgente a 1.258 funzioni/metodi Python.
  Hash dei file verificati rispetto allo snapshot prima della lettura.
  Le altre 165 rappresentazioni rimangono identiche.
- A: anchor esatti + FTS5. C: gli stessi anchor, fusione dei ranghi con peso
  embedding 0,75 e FTS 0,25. Stessa espansione del grafo per la metrica dipendenze.
  FTS e vettori ricostruiti separatamente per ciascuna rappresentazione.

Il download iniziale ha richiesto 6,75 secondi con accesso di rete autorizzato.
Le inferenze successive hanno usato i file locali con `HF_HUB_OFFLINE=1`.
Il progetto non viene importato né inviato a un servizio di embedding; il modello
è caricato come ONNX senza eseguire codice remoto personalizzato.

## Risultati

Recall@20 misura la quota media dei target attesi presenti nei primi 20 risultati.
MRR@10 premia un target corretto vicino all'inizio; nDCG considera anche le
dipendenze dichiarate. I valori non misurano correttezza di una modifica.

| Documento | Ricerca | Recall@20 | MRR@10 | nDCG@10 | Latenza media / P95 |
|---|---|---:|---:|---:|---:|
| Metadati | A: lessicale | 0,7778 | 0,5797 | 0,5946 | 2,1 / 3,2 ms |
| Metadati | C: CodeRank + lessicale | 0,8333 | 0,6259 | 0,6512 | 51,7 / 72,5 ms |
| Metadati e corpo | A: lessicale | **0,9167** | **0,7148** | **0,7142** | 2,6 / 3,4 ms |
| Metadati e corpo | C: CodeRank + lessicale | 0,8611 | 0,6782 | 0,6946 | 33,9 / 46,1 ms |

La latenza C misura encoder della query, similarità e fusione; esclude la ricerca
FTS precalcolata. Non è una misura completa del servizio. Le configurazioni di
thread differiscono fra le due prove C, quindi il confronto dei loro tempi non
isola il costo dei corpi. A non carica un modello.

| Query senza nomi esatti | Metadati A | Metadati C | Corpo A | Corpo C |
|---|---:|---:|---:|---:|
| Inglese, 8 query: Recall@20 | 0,7500 | 0,8750 | **1,0000** | 0,8750 |
| Italiano, 6 query: Recall@20 | 0,3333 | 0,3333 | **0,5000** | 0,3333 |
| Inglese: MRR@10 | 0,2052 | 0,3583 | **0,7125** | 0,6146 |
| Italiano: MRR@10 | 0,0655 | **0,1944** | 0,0333 | 0,1667 |

Esempio della prima prova: la richiesta inglese sui chiamanti interessati da
cambi di firma porta `build_stale_callers` dal rango 43 con A al rango 5 con C.
Questo beneficio non basta a generalizzare a tutte le rappresentazioni o lingue.
Dependency Recall@15 è 1,0 in tutte le prove, ma soltanto cinque query dichiarano
dipendenze; non prova completezza dell'impatto o benefici degli archi Jedi.

## Costi e controlli

| Misura | Metadati C | Corpo C |
|---|---:|---:|
| Calcolo vettori documenti | 154,2 s | 262,2 s |
| Processo offline completo | 169,1 s | 265,3 s |
| Batch documenti | 16 | 2 |
| Thread | default ONNX Runtime | 4 intra-op, 1 inter-op |
| Picco working set del processo | non misurato | 377,5 MiB |
| Vettori, float32 × 768 dimensioni | 4,17 MiB | 4,17 MiB |
| Documenti oltre 512 token | 0 | 257 su 1.423 (18,1%) |

FTS indicizza il corpo completo; l'encoder vede al massimo 512 token, anche se
il modello base supporta contesti più lunghi. Il corpus arricchito contiene
520.150 token secondo il tokenizer, ridotti a 349.918 dal limite per documento.
Questo esperimento confronta le pipeline configurate, non la qualità massima
ottenibile da CodeRankEmbed. Non attribuiamo il risultato negativo a una causa
unica senza una prova separata.

Il primo tentativo sui corpi si è interrotto dopo 320 documenti, senza indice
completo. Un processo di audit avviato in parallelo ha restituito lo stato Windows
`0xc000012d`; il controllo successivo è riuscito. Il tentativo concluso usa batch
ridotti e checkpoint ogni 64 documenti, vincolati agli hash di corpus, modello,
tokenizer e configurazione. È partito con checkpoint vuoti e li ha completati
tutti. I tempi in tabella escludono il lavoro del tentativo interrotto.

Controlli superati:

- Tutti i vettori hanno forma 1.423 × 768, valori finiti e norma unitaria.
- Probe indipendente su codice: due lettori JSON hanno similarità 0,6975;
  lettore JSON contro somma numerica o invio email circa 0,089. La query sulla
  lettura JSON seleziona per primi i due lettori; ripeterla produce vettori identici.
- ID, ordine e adjacency identici fra prove; gold e sorgenti del benchmark
  invariati durante il confronto. Revisione indipendente degli intervalli inclusivi
  e del controllo di freschezza. `task_router.py` è cambiato dopo l'acquisizione:
  i risultati si riferiscono ai documenti congelati, non al checkout successivo.
- Quattro test del benchmark eseguiti prima delle prove, tutti superati.

## Limiti e decisione per P5

È un piccolo set di sviluppo già noto, con target ripetuti fra formulazioni;
non è un holdout indipendente. Nessun budget di contesto LLM, risultato di task o
risparmio di token è stato misurato. Indicizzazione, embedding e ranking locali
non hanno effettuato chiamate LLM a pagamento; questa affermazione non include
la conversazione che coordina l'esperimento.

Il sidecar esistente identifica la cache vettoriale dal solo numero di documenti.
Sono state usate cache nuove e separate, senza riusare vettori fra rappresentazioni.
I checkpoint dell'esperimento non sostituiscono la cache di produzione prevista
da P5, che deve includere anche versione del runtime/encoder e invalidazione.
Il limite di cinque anchor non interviene: queste query hanno da zero a due anchor.
FTS conserva la pesatura esistente, effettivamente 5/3/1/1 per le colonne
ricercabili a causa della colonna iniziale non indicizzata; vale identicamente
per A e per la componente lessicale C.

Procedere con una baseline che includa sorgente utile; mantenere CodeRank come
candidato opzionale. Il prossimo confronto deve verificare separatamente
segmentazione dei corpi, fusione dei ranghi e qualità italiana su un holdout
congelato. Non tarare e promuovere il modello sugli stessi 36 casi. Il
[piano P5](../../../docs/superpowers/plans/2026-10-23-code-context-and-scope.md)
resta aperto per cache, integrazione, aggiornamenti e gate di adozione.

Gli artefatti completi locali, incluse rappresentazioni, ranking, snapshot,
checkpoint e script della prova, sono in
`.daodan/evals/coderank-local-20261023-101933/`. Il riepilogo JSON collegato sopra
conserva metriche per query, ranghi dei target, configurazione e digest; i pesi
del modello e i vettori non entrano nel repository versionato.
