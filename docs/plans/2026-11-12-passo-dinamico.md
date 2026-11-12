# Piano: passo dinamico in un container

Eseguire i task nell'ordine e segnare solo i passi verificati. La Parte A misura senza toccare i plugin; la Parte B resta subordinata alla misura e al via dell'utente.

**Obiettivo:** sapere quante chiamate senza risposta ricevono una destinazione quando i test del progetto girano in un container, e a quale costo; poi, se la misura lo giustifica, portare l'operazione e gli archi osservati in Codebase Map.

**Funzionamento:** un motore di container che parla la Docker Engine API esegue i test su una copia del perimetro dello snapshot. Le chiamate osservate si riportano alle posizioni che il passaggio del motore lascia senza risposta e si contano con lo stesso criterio, risolte su risolvibili.

**Tecnologie:** Python 3 solo libreria standard, riga di comando compatibile con `docker`, Kiri 0.2.0, Markdown.

**Spec:** `docs/specs/2026-11-12-passo-dinamico.md`

## Vincoli

- Il codice di un progetto gira solo in un container, mai sull'host, anche durante la misura.
- Run pesanti: chiedere prima all'utente, un processo alla volta, memoria libera controllata. Dove gira la misura, in locale o su Modal, lo decide l'utente prima del lancio.
- Soglie e parametri si scrivono nel README del benchmark prima di misurare.
- Nessun bump di versione di plugin o marketplace.
- Documenti in italiano al presente; riferimenti e brief in inglese, come sono.
- I commit si eseguono solo su richiesta dell'utente.

## Parte A: misura

### Task 1: avvio di un container isolato

- [x] **Passo 1:** container senza rete su Kiri: la richiesta di rete fallisce.
- [x] **Passo 2:** cartella montata in sola lettura: la scrittura è rifiutata e sull'host non compare nessun file.
- [x] **Passo 3:** tempi a freddo e a caldo nel README di `benchmarks/call-provenance`.

### Task 2: copertura osservata su un caso JavaScript

**File:**
- Crea: uno script in `benchmarks/call-provenance/` che prepara il container, esegue i test e scrive le coppie chiamante-chiamato osservate.
- Modifica: `benchmarks/call-provenance/README.md` (risultati).

- [x] **Passo 1:** parametri e soglia nel README.
- [x] **Passo 2:** copia del perimetro, installazione dei pacchetti con la rete aperta ai soli registri, test con la rete chiusa e il profiler attivo. Eseguito con le deviazioni scritte nel README.
- [x] **Passo 3:** riporto delle coppie osservate alle posizioni senza risposta dello store del motore, classificate per provenienza.
- [x] **Passo 4:** conteggio con e senza gli archi osservati, archi che contraddicono un arco provato, durata, RAM di picco e spazio.
- [x] **Passo 5:** risultati nel README, con i test che non sono partiti e il motivo.

### Task 3: decisione

- [ ] **Passo 1:** l'utente decide dai numeri del Task 2 se la Parte B parte, per quali linguaggi e con quale registratore.
  - Registratore per JavaScript, deciso il 12 novembre 2026: il registro esatto (`benchmarks/call-provenance/dynamic_record.js`), da misurare sullo stesso caso prima di decidere il resto. Misurato lo stesso giorno: 72,2%, soglia raggiunta (README del benchmark).

## Parte B: nel plugin (dopo la misura)

I passi di ogni task si scrivono dopo il Task 3, perché dipendono dalle scelte ancora aperte nella spec.

### Task 4: operazione «esegui un comando in un container»

Le cinque garanzie della sezione 2 della spec, ciascuna con il suo test; ricerca del motore presente e scaricamento di Kiri a versione fissata con checksum; lacuna dichiarata dove il motore manca.

### Task 5: archi osservati nello store

Un risolutore nuovo in `resolve_edges.py` con la provenienza «osservato»; il rapporto li conta a parte; un arco osservato che contraddice un arco provato viene riportato.

### Task 6: riferimenti del plugin

`docs/plugins/codebase-map.md`, `docs/plugins/codebase-map-linguaggi.md` e i `references/` della skill descrivono il passo come comportamento attuale solo quando i Task 4 e 5 sono verificati.

### Task 7: review dinamiche

Spec propria in senior-review: la riproduzione di un finding e il test di riproduzione di un'indagine usano l'operazione del Task 4.

### Task 8: ambiente del passo 2 dal container

Le librerie calcolate dagli script Gradle e i file generati dai build script di Rust (sezione 4 della spec), misurati su un caso per linguaggio (misura 4) prima di adottarli.
