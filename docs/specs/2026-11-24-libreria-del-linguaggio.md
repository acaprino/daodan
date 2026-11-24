# Libreria nostra per il linguaggio dei file

**Stato:** bozza. La chiede il proprietario il 24 novembre 2026, con parole sue: «creare una lib noi», «da Linguist solo il catalogo di partenza», «ben strutturato, con una logica e design pattern puliti, tipo strategy o adapter». Nel prodotto non c'è nulla: oggi decide `languages.detect_language`. Il fork `acaprino/linguist-daodan` (creato lo stesso giorno, senza modifiche) non serve più: si cancella solo se il proprietario lo dice.

## Perché

Meno codice nostro sparso, una sorgente aggiornata e regole che si provano una per una. Un primo lettore dei soli dati di Linguist 9.7.0 è stato bocciato dalla review (24 novembre), con il lettore di oggi come riferimento:

| Prova | Esito |
| --- | --- |
| 51.729 file di 180 progetti | 11 differenze, tutte a favore di Linguist. Il corpus ha solo 66 `.h` |
| 6.857 `.h` (per lo più Windows SDK, MSVC, CPython) | 130 differenze: 95 C++ letti C, 33 C letti C++, 2 senza linguaggio |
| 47.999 `.ts` | 8 TypeScript con `<TS` letti come XML |
| Estensioni nuove | `binding.gyp` diventa Python: aggiunge un analyzer e fonde le corse di due servizi |
| Costo | 8–48 s per un file da 50 KB costruito male, su sei estensioni. La regola `.h` di oggi ne impiega 28 |

## Che cosa contiene

| Pezzo | Origine |
| --- | --- |
| Catalogo: linguaggi, estensioni | Linguist, `languages.yml`, come punto di partenza; poi è nostro |
| Riconoscitore: estensione più lunga, scelta fra i candidati | Il lettore provato il 24 novembre (51 righe), rifatto con la struttura sotto |
| Regole `.h` (C++), `.ts`, `.sql` e Oracle | Quelle di oggi di Daodan, che nel confronto vincono |
| Regole `.ftl` (Fluent), `.h` (Objective-C) | Quelle di Linguist, che vincono |
| `.rs`, `.cs`, `.html`, `.tsx`, `.hh` | Come oggi, finché un campione non prova il contrario |
| Estensioni accettate | Le 63 di oggi; una nuova entra solo con una prova che non cambia il piano dell'analisi |

## Struttura

| Pezzo | Pattern | Responsabilità |
| --- | --- | --- |
| `catalog.py` | — | `Catalog`: estensione → nomi dei linguaggi, e le estensioni accettate |
| `sources/linguist.py` | Adapter | Trasforma `languages.yml` nel `Catalog`; serve solo a generare il catalogo, non a usarlo |
| `strategies/` | Strategy | `Strategy`: dato un file e i candidati, dà i candidati rimasti. `ByExtension`, `ByContent`, `ByFallback`, provate in fila |
| `matchers/` | Strategy | I tipi di confronto che una regola può chiedere, uno per file, ognuno con il suo limite di tempo: `starts-with`, `contains`, `regex`, `regex-on-code` (dopo aver tolto commenti e stringhe, come la regola `.h` di oggi) |
| `rules.toml` | Dati | Il catalogo delle regole (sotto): nessuna regola è codice |
| `detector.py` | — | Esegue le strategie in fila e dà `Detection(language, decided_by)` |

Nessuna fabbrica, nessun sistema di plugin, nessuna opzione non richiesta. Dipendenze: nessuna in esecuzione, a parte ciò che il limite di tempo chiede (`regex`, se la prova lo conferma).

Vincoli:

1. Pura: nessuna lettura di file, nessuna rete, nessun processo. Riceve nome e testo.
2. **Limite di tempo per regola**: un file costruito male non tiene fermo il chiamante più di un secondo.
3. Ogni risultato dice quale strategia o regola ha deciso.
4. Ogni regola ha campioni scritti a mano, dei due esiti; mai un header copiato.
5. Nessun concetto di Daodan nella libreria: la mappa verso i linguaggi di Daodan sta in Daodan.

## Il catalogo delle regole

Chiesto dal proprietario il 24 novembre: un formato preciso, controllabile, replicabile e mantenibile. Ogni regola è una voce di dati, non codice.

```toml
[[rule]]
id = "ts.xml-qt"
extension = ".ts"
language = "XML"
match = { kind = "starts-with", any = ["<?xml", "<!DOCTYPE"] }
why = "Un .ts che e' un documento XML e' una traduzione di Qt"
source = "daodan 2026-11-24"
samples = ["samples/ts.xml-qt/yes", "samples/ts.xml-qt/no"]
```

| Campo | Regola |
| --- | --- |
| `id` | Unico e stabile, `estensione.motivo`. Si legge nelle risposte (`decided_by`) |
| `extension`, `language` | L'estensione nel catalogo; il nome del linguaggio come nel catalogo |
| `match` | Un tipo di confronto dichiarato nello schema, con i suoi parametri. L'ordine delle regole di un'estensione è l'ordine nel file |
| `why`, `source` | Il motivo in una riga, la provenienza e la data. Una regola presa da Linguist dice la versione |
| `samples` | Almeno un campione che deve dare quel linguaggio e uno che non lo deve dare, scritti a mano |

Le garanzie, ognuna un test:

1. **Formato.** Uno schema dice campi e tipi ammessi; una regola fuori schema non si carica, con il nome del campo.
2. **Controllo.** Una regola senza campioni positivi e negativi non passa. Due regole della stessa estensione che si contraddicono sullo stesso campione sono un errore.
3. **Replicabilità.** Catalogo e regole hanno una versione e un'impronta; stessi dati, stesso file, stessa risposta, su ogni sistema. Nessun ordine dipende dal caso.
4. **Costo.** Per ogni regola, un input costruito per essere il peggiore sta sotto il limite.
5. **Manutenzione.** Aggiungere un caso è una voce nel catalogo e i suoi campioni: nessun file di codice cambia. Un tipo di confronto nuovo è un file in `matchers/`, con il suo test.

## In Daodan

1. La libreria è una dipendenza fissata alla versione. `languages.detect_language` diventa una chiamata più la mappa dei nomi.
2. `SUPPORTED_EXTENSIONS` si ricava dal catalogo e dalla mappa; la tabella e le regole di `languages/__init__.py` spariscono.
3. La versione della libreria entra nell'impronta del parser.
4. Le liste di suffissi sparse (`import_resolution`, `clang`, `typescript`, `edge_grading`, `usage_finder`, `store_consumers`) leggono la stessa tabella, o restano con il motivo scritto.

## Aggiornamento

Una corsa settimanale nella libreria confronta il catalogo con l'ultima versione di Linguist e apre una modifica con le estensioni aggiunte, tolte o spostate: si accettano o no una per una. Le nostre regole non cambiano mai da sole.

## Come si prova

1. I casi della review diventano campioni con l'esito giusto.
2. Il gate: i 180 progetti e gli insiemi della review (6.857 `.h`, 47.999 `.ts`, 26.896 `.rs`) contro il lettore di oggi, preso con `git show`, senza cloni. Ogni differenza è spiegata e nessun file perde il suo parser.
3. Il costo: file da 50 KB costruiti male, per ogni regola, sotto il limite.
4. Il piano dell'analisi dei 122 progetti della pre-mappa è quello di prima.
5. Suite e phazly su Modal: niente scende.

## Scelte aperte

| Scelta | Proposta |
| --- | --- |
| Nome e repository | `acaprino/daodan-languages`, pubblico, creato quando c'è qualcosa da pubblicare |
| `.h`: togliere commenti e stringhe prima di cercare | Restano come oggi; il costo quadratico si risolve con il limite di tempo |
