# Il linguaggio dei file: un modulo di Daodan con il catalogo di Linguist

**Stato:** approvata dal proprietario il 24 novembre 2026, con le correzioni del consulente («A»). Nel prodotto non c'è nulla ancora: oggi decide `languages.detect_language`. Sostituisce la bozza di una libreria separata: un modulo dentro Daodan, con la stessa struttura, si estrae il giorno in cui un secondo programma la usa.

## Perché

Meno codice nostro sparso, una sorgente aggiornata, regole che si provano una per una. Un primo lettore dei soli dati di Linguist 9.7.0 è stato bocciato dalla review (24 novembre):

| Prova | Esito |
| --- | --- |
| 51.729 file di 180 progetti | 11 differenze, tutte a favore di Linguist. Il corpus ha solo 66 `.h` |
| 6.857 `.h` (per lo più Windows SDK, MSVC, CPython) | 130 differenze: 95 C++ letti C, 33 C letti C++, 2 senza linguaggio |
| 47.999 `.ts` | 8 TypeScript con `<TS` letti come XML |
| Estensioni nuove | `binding.gyp` diventa Python: aggiunge un analyzer e fonde le corse di due servizi |
| Costo | 8–48 s per un file da 50 KB costruito male, su sei estensioni |

Già corretto (`e9bc57cac`): le righe vuote di un `.h` costavano 25,5 s, perché `^\s*` attraversa le righe. Aperto: 6,9 s su commenti mai chiusi.

## Struttura (`daodan/core/languages/detect/`)

| Pezzo | Pattern | Responsabilità |
| --- | --- | --- |
| `catalog.json` e lo script che lo genera | Adapter | Da `languages.yml` di Linguist al nostro catalogo: estensione → nomi. Solo le estensioni accettate (le 63 di oggi); una nuova entra con una prova che non cambia il piano dell'analisi |
| `rules.toml` | Dati | Le regole semplici (sotto) |
| `rules/` | Strategy | Le regole che non sono dati: una classe per file, con la stessa scheda e `decide(testo) -> linguaggio o niente` |
| `detect.py` | — | Estensione, poi le regole di quell'estensione nell'ordine, poi il ripiego dichiarato. Dà `Detection(language, decided_by)` |

Tre passi fissi, non una catena di oggetti. Il catalogo non nomina linguaggi di Daodan: la mappa verso quelli sta accanto, con il suo test.

## Le regole

Formato preciso, controllabile, replicabile e manutenibile. La scheda di ogni regola: `id` (unico, `estensione.motivo`), `extension`, `language`, `why`, `source` con la data, `samples` (almeno un campione che sì e uno che no, scritti a mano).

| | `rules.toml` | Classe Python |
| --- | --- | --- |
| Che cosa può chiedere | Un solo confronto, `starts-with` o `contains`, su testi letterali. Nessuna composizione, nessuna regex | Ciò che un confronto letterale non può dire |
| Esempi | `.ts` che inizia come XML, `.ftl` Fluent, i marcatori letterali di `.sql` | `.h` C contro C++, Objective-C |
| Prova | Lo stesso test per tutte | Lo stesso test per tutte |

Il formato non cresce: una regola che non ci sta è una classe.

Garanzie, ognuna un test:

1. Una regola fuori schema non si carica, con il nome del campo.
2. Ogni regola ha campioni dei due esiti; due regole della stessa estensione che si contraddicono sullo stesso campione sono un errore.
3. Stessi dati e stesso file, stessa risposta su ogni sistema: nessun orologio decide. Un'impronta di catalogo e regole entra nell'impronta del parser.
4. Il costo cresce in linea con la lunghezza (2, 4, 8 KB: il tempo raddoppia), per ogni regola e su una lista fissa di testi. Un tetto ai byte guardati.
5. Aggiungere un caso è una voce nel catalogo, o una classe, con i suoi campioni.

## `.h`: prima la prova

La regola di oggi è una regex su un testo senza commenti e stringhe, e AGENTS vuole l'albero sintattico. Si misura prima di scegliere, su header con la risposta giusta nota (progetti di sola C, di sola C++, Objective-C), a parità di tempi:

| Via | Come |
| --- | --- |
| Oggi | Le due regex di `languages/__init__.py` |
| Nodi C++ | tree-sitter C++ e i nodi che C non ha (`namespace_definition`, `class_specifier` con corpo, `template_declaration`, `access_specifier`, `using_declaration`) |
| Due grammatiche | tree-sitter C e C++, si tiene quella con meno nodi `ERROR`; a parità, C |

Limite noto: tree-sitter su un commento aperto mai chiuso cresce più che al quadrato (14,5 s a 8 KB). Se la via si sceglie, serve un tetto ai byte o un controllo lineare dei commenti prima. Il costo dell'errore non è simmetrico: un header C++ letto come C perde le classi, un header C letto come C++ perde poco.

## Aggiornamento

Una corsa settimanale confronta il catalogo con l'ultima versione di Linguist e propone le estensioni aggiunte, tolte o spostate: si accettano o no una per una. Le regole non cambiano mai da sole.

## Come si prova

1. I casi della review diventano campioni con l'esito giusto.
2. Il gate: i 180 progetti e gli insiemi della review contro il lettore di oggi preso con `git show`, senza cloni. E, per le regole, un insieme con la risposta giusta, non solo «diverso da oggi».
3. Il costo: la crescita, per ogni regola.
4. Il piano dell'analisi dei 122 progetti della pre-mappa è quello di prima. CRLF, BOM, `text=None`, file troncato, il tempo totale sui 51.729 file contro oggi, la mappa dei nomi.
5. Suite e phazly su Modal: niente scende.
