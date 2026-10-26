# Scambi tra agenti con risparmio misurato

Data: 26 ottobre 2026. Stato: proposta di implementazione da approvare.

## Intento e scelta dell'utente

L'utente vuole estendere a Daodan un formato di scambio che consumi meno token.
Tra TOON obbligatorio e adozione basata sui risultati ha scelto «risparmio
misurato». Questa scelta approva l'approccio, non dichiara già approvati questo
progetto, una dipendenza o un incremento di spesa per chiamate ai modelli.

Il risultato richiesto è una politica comune a tutti i plugin: ogni superficie
di dati destinata al modello viene censita e, quando supportata, confrontata
con rappresentazioni equivalenti. TOON entra soltanto dove supera i controlli
di integrità, comprensione e consumo. Una superficie esclusa, non misurabile o
non verificata resta visibile nel rapporto; non conta come conversione riuscita.

## Approcci

1. **Adozione misurata, scelta dall'utente.** Si confrontano formato attuale,
   JSON compatto quando rappresenta gli stessi dati, e TOON. Il vantaggio deve
   sopravvivere al costo del flusso completo e ai controlli del destinatario.
2. **TOON obbligatorio per gli scambi compatibili, scartato.** Uniforma il
   formato senza garantire un minor consumo; non è la scelta dell'utente.
3. **Sola minificazione, confronto di controllo.** Può spiegare parte del
   risparmio. Rimane un candidato reale, così il beneficio della minificazione
   non viene attribuito a TOON.

JSON compatto può diventare la rappresentazione di produzione quando supera
gli stessi gate di una conversione TOON e risulta il candidato meno costoso.
Il risultato cercato è il risparmio misurato, non il numero di file TOON.

## Fatti verificati e confini

- Work Controller ha proiezioni limitate in `work_controller/views.py` e
  pacchetti agente in `work_controller/engine.py`; `cli.emit` stampa JSON
  formattato e MCP espone sia testo JSON sia `structuredContent`.
- `codebase-map/context_packet.py` misura l'input completo tramite un
  `token_counter` associato a `tokenizer_id`. CLI e MCP non forniscono oggi un
  tokenizer esatto; i caratteri restano una misura distinta. Il renderer emette
  un header JSON seguito da sezioni di sorgente grezzo; `parse_input` lo legge.
- `cycle_packets.py` verifica ricevute e digest e distingue la verifica ancora
  richiesta al destinatario. La serializzazione scelta deve essere legata alla
  ricevuta prima del dispatch, non applicata dopo la verifica del pacchetto.
- `model-routing/usage_pricing.py` legge consumi locali e normalizza i bucket.
  ADR-0003 è ancora `Proposed`: non si presume già disponibile un ledger
  completo per job, fase e tentativo. Copilot non ha una fonte consumi verificata.
- Il gate del precedente esperimento di selezione del contesto non è passato
  (`2026-10-25-context-packet-redesign.md`). Questo lavoro è un esperimento di
  rappresentazione separato: non riapre quelle fasi, non usa il secondo holdout
  congelato e non cambia selezione delle prove o criteri di `ready`.

Ricognizione statica mirata ai file citati, senza una mappa locale del repository,
test eseguiti, prove sui modelli o censimento completo delle superfici. La prima
consegna dell'implementazione completa il censimento leggendo i produttori e i
consumatori; nessun conteggio di file vale come copertura comportamentale.

## Architettura proposta

Work Controller possiede un componente leggero `agent-data`, senza un nuovo
comando utente: skill breve, contratto TOML e helper sotto la skill. Gestisce
selezione della rappresentazione, ricevuta e verifiche, separatamente dal motore
dei processi. Non acquisisce dipendenze da consumatori o da model-routing.

Ogni produttore conserva la proprietà dei propri dati, schemi e parser. I
consumatori invocano il provider dichiarato attraverso il suo contratto, senza
importare file di un altro plugin con percorsi di checkout. I consumatori che
già dipendono da Work Controller riusano quel collegamento. Se il censimento
conferma l'integrazione standalone di codebase-map, questo dichiara la nuova
dipendenza obbligatoria da work-controller; il grafo viene verificato prima
dell'integrazione. Nessuna dipendenza viene aggiunta a plugin senza un uso reale.

Il renderer riceve dati validati, identità del destinatario, wrapper e una
capacità di conteggio esplicitamente fornita dal dispatcher. Non inventa API,
tool di conteggio o corrispondenze tra nomi di modelli e tokenizer. Non cambia
contenuto, ordine significativo, obblighi, autorizzazioni o esiti dei controlli.

Il formato resta quello corrente quando manca una capacità necessaria, una
misura esatta o una qualificazione valida. Un provider locale obbligatorio
mancante rimane invece un errore di dipendenza: non viene nascosto dal fallback.

### Codec

Non si implementa un dialetto TOON o un parser generale nuovo. Il candidato è
l'implementazione Python ufficiale, isolata in un sidecar del solo runtime e
vincolata a una versione verificata. Compiler, lint e import della toolchain
restano standard library; non si richiede Node per questa funzionalità.

La sorgente ufficiale consultata dichiara Python >=3.10, MIT e nessuna dipendenza
runtime; il `pyproject.toml` consultato riporta 1.2.0. L'elenco delle
implementazioni e il README non concordano sulla versione di specifica Python.
Sono dati di ricognizione, non una verifica di sicurezza o della distribuzione.
Prima dell'adozione si verificano release realmente pubblicata, supporto,
licenza, dipendenze, codice eseguito e fixture di conformità della revisione
esatta, seguendo l'intake del repository. La revisione risolta viene fissata e
registrata. Nessuna installazione o dipendenza è approvata da questo documento.
Se l'intake fallisce si conserva il formato attuale, senza riscrivere il codec.

## Contratto di rappresentazione e selezione

La fonte canonica mantiene il suo schema. La vista per il modello è un artefatto
derivato con ricevuta JSON contenente almeno: produttore e revisione dello
schema; digest della fonte; codec e revisione; profilo del destinatario;
identità e revisione del contatore; istruzioni e wrapper; digest dell'input
finale; conteggi dei candidati; rappresentazione scelta; motivo e stato della
qualificazione. I limiti, l'autorità di scrittura e i controlli sui percorsi
restano quelli del produttore e del run esistente.

La scelta avviene a questi confini:

1. Il produttore prepara e valida lo stesso insieme di informazioni per tutti
   i candidati. Si applicano le verifiche di equivalenza; si escludono i valori
   che il codec non conserva secondo lo schema, senza coercizioni silenziose.
2. Si costruisce l'intero testo che il destinatario riceverà: payload, eventuali
   istruzioni TOON, identificatore di formato, delimitatori, prefissi e suffissi.
   Il codice sorgente e il testo già grezzo conservano i propri byte e confini.
3. Il contatore esatto del destinatario misura ogni candidato. TOON è eleggibile
   solo con una qualificazione comportamentale valida e un conteggio inferiore
   sia al formato corrente sia a JSON compatto, quando questo è applicabile.
   JSON compatto è eleggibile soltanto con i medesimi gate e un conteggio
   inferiore al formato corrente. Si sceglie il candidato qualificato meno
   costoso; a parità si mantiene quello corrente, poi JSON compatto.
4. La ricevuta viene legata all'input finale e ricontrollata prima del dispatch.
   I consumi delle chiamate precedenti necessarie a conteggio o preparazione
   entrano nel saldo della prova; caratteri e byte non diventano token.

Un profilo comportamentale lega almeno famiglia di payload, schema e revisione,
codec, istruzioni, modello/endpoint, tokenizer e percorso dell'host verificato.
Una variazione di questi elementi invalida il profilo. Il profilo non sostituisce
il conteggio della singola consegna e non garantisce esiti futuri.

## Adozione trasversale e compatibilità

Il censimento classifica tutte le superfici dei kernel in: dati per il modello,
contratti macchina, testo/sorgente, oppure nessuna superficie pertinente. Ogni
riga registra produttore, lettori, schema, wrapper effettivo, capacità e prove.
Il risultato è una matrice di adozione, non un'affermazione che ogni plugin
debba produrre TOON. Le famiglie prive di vantaggio mantengono la baseline.

L'ordine proposto è: proiezioni e pacchetti di Work Controller; dati di
coordinamento di project-delivery e senior-review; infine metadati dei pacchetti
di codebase-map e altri produttori individuati. I risultati di una famiglia non
qualificano automaticamente le altre. L'indipendenza dei revisori resta intatta.

CLI macchina, JSON-RPC, `structuredContent`, API web, YAML, SQLite, manifest,
ricevute e report canonici mantengono i formati attesi. La vista per gli agenti
si richiede esplicitamente; il default consumato da `json.loads` non cambia.
Le istruzioni restano Markdown; TOML resta metadato dichiarativo.

MCP richiede una prova specifica: se l'host inserisce nel contesto sia il testo
TOON sia il JSON strutturato, si conta la duplicazione e quel percorso non si
promuove senza un vantaggio netto dimostrato. Non si eliminano campi richiesti
dal protocollo per rendere migliore il confronto.

Per i pacchetti di codice, il formato dell'header va dichiarato, letto dal parser
del produttore e incluso nei binding. Fonti, span, marker, hash, controlli,
omissioni e ricevute conservano il loro significato. Questa integrazione non
riattiva la selezione del contesto fermata dal precedente esperimento.

## Misurazione e qualificazione

Si mantengono separate tre prove: equivalenza strutturale, comprensione/esito
del destinatario e consumo complessivo. Il round trip del codec non prova che
un modello svolga correttamente il compito.

La suite congelata comprende dati reali rappresentativi e casi avversi: tabelle,
record irregolari, annidamento, pacchetti piccoli, Unicode, quote e separatori,
stringhe simili a numeri o booleani, valori nulli, numeri e limiti di precisione,
input troncati, testo ostile e collisioni con i delimitatori di sorgente.
Sviluppo e holdout sono distinti. Gli stessi oracoli e gli stessi obblighi
valgono per baseline e candidati; non si elimina un caso perso dal rapporto.

Le prove accoppiate usano stesso modello, endpoint, revisioni, permessi e
materiale; l'ordine viene alternato e le condizioni di cache dichiarate.
Numero di ripetizioni e suite si fissano prima della misura sul holdout; il
piano li dimensiona sui consumi del preflight e sul budget già autorizzato.
Il piano preregistra anche la regola di confronto del saldo e della sua
incertezza: un risultato compatibile con un saldo nullo o negativo non promuove
la famiglia. I risultati riportano variabilità e limiti, senza proclamare
equivalenza universale da un campione finito.

Per ogni coppia si riportano consumo totale e di input, esiti verificati,
errori di formato, retry, fallback e latenza. Il totale include preparazione,
coordinamento, istruzioni, letture, validazione e ripetizioni di tutti i worker.
I bucket normalizzati del helper di model-routing evitano di contare cache o
reasoning due volte. Costo, token e tempo rimangono metriche distinte.

Prima di dichiarare il saldo completo si verifica la copertura delle sessioni
e dei worker attesi. Una fonte mancante è `unavailable` o `partial`, mai zero;
lo stato `complete` dei prezzi non dimostra tale copertura. Se i log disponibili
non bastano, si registra il limite e non si dichiara una riduzione complessiva.

La promozione di una famiglia richiede: equivalenza senza perdita; nessuna
regressione osservata negli oracoli obbligatori; tutti i gate conservati;
conteggio esatto disponibile. JSON compatto richiede un saldo totale positivo
rispetto alla baseline; TOON richiede un saldo totale positivo sia rispetto
alla baseline sia rispetto al controllo compatto, quando applicabile.
Un fallimento tiene quella famiglia sul formato corrente.
Prove a pagamento rispettano le autorizzazioni e i budget del run; questo
progetto non autorizza nuove chiamate o aumenti di spesa.

## Consegne e accettazione

1. Matrice completa delle superfici, intake del codec e dataset congelato con
   provenienza; nessuna installazione implicita negli import della toolchain.
2. Provider condiviso, ricevute, conteggio e selezione conservativa; regressioni
   per dati corrotti, identità errate, misura assente, digest e default macchina.
3. Integrazioni dei produttori con equivalenza verificata; obblighi, autorizzazioni,
   fonti e indipendenza dei revisori conservati; nessuna dipendenza circolare.
4. Prove comportamentali e consumo per ogni profilo promosso. Tabella esplicita
   di percorsi attivi, esclusi, non misurati e con capability mancante.
5. Build e controlli di tutti i cinque export, dipendenze, riferimenti e dispatch;
   probe installati separati dai test del compiler. Versioni, documentazione,
   istruzioni canoniche e artefatti generati si aggiornano secondo il workflow
   del repository, soltanto nell'implementazione approvata.

Si può completare una consegna infrastrutturale con zero profili promossi, se
questo è l'esito della misura; il rapporto deve allora dire che nessuno scambio
è stato convertito e che non è stato dimostrato un risparmio. Non equivale alla
consegna dell'adozione su tutti i percorsi. I gate o le consegne mancanti restano
aperti. Non si presume che questa sessione possa certificare tutti gli host.

## Scelte del coordinatore e spazio al piano

Proposte del coordinatore: owner work-controller, componente leggero separato,
codec ufficiale isolato dopo intake, selezione prima del dispatch, baseline
conservata senza misura, e qualificazione separata per famiglia e destinatario.
L'utente ha scelto l'approccio misurato, non questi dettagli individualmente.
Il piano definisce gli argomenti CLI, la forma esatta del contratto, i fixture,
le prove e le micro-task senza indebolire i criteri sopra.

## Riferimenti

- [Pacchetto di contesto e punto di arresto](2026-10-25-context-packet-redesign.md).
- [ADR-0003, proposta sul ledger](../../adr/ADR-0003-usage-ledger.md).
- [TOON: confronto dei formati](https://toonformat.dev/guide/benchmarks).
- [TOON: uso nei prompt](https://toonformat.dev/guide/llm-prompts).
- [Implementazione Python ufficiale](https://github.com/toon-format/toon-python).
- [Metadati Python consultati](https://github.com/toon-format/toon-python/blob/main/pyproject.toml).
- [Specifica TOON](https://github.com/toon-format/spec/blob/main/SPEC.md).
