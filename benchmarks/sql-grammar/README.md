# Grammatica tree-sitter su SQL e PL/SQL (T1.A.6)

Domanda: la grammatica `sql` di `tree-sitter-language-pack` 1.13.5 (la versione di Daodan, `_treesitter.PACK_VERSION`) legge
SQL e PL/SQL meglio dei lettori a espressioni regolari di oggi (`daodan/core/languages/sql.py`, `plsql.py`)? Confronto con
`sqlglot` (già dipendenza del prodotto, `_try_sqlglot_tables`) come comparatore. Nessun LLM, nessun cambio al prodotto: l'adozione
spetta al proprietario (e, se approvata, a `T2.B`). ANTLR `grammars-v4` (comparatore previsto dal piano) non è stato eseguito.

## Primo controllo: `plsql` nel pack?

**No.** `pack.get_parser("plsql")` risponde `DownloadError: Language 'plsql' not available`; nel pack c'è solo `sql` (anche
`oracle` e `pl_sql` non esistono). Il verdetto sotto misura quindi la grammatica `sql` sui file PL/SQL. La grammatica `sql` non ha
nodi per `package`, `package body`, `type body`: i nodi di creazione sono tabella, vista, vista materializzata, indice, sequenza,
tipo, schema, trigger, funzione, procedura (`sql_grammar.CREATES`).

## Parametri

- **Lettori** (`sql_readers.py`): regex = `get_adapter("sql"|"plsql").parse` col linguaggio scelto da `detect_language` (oggetti = classi e
  funzioni, riga di inizio, nessuna riga di fine); tree-sitter = visita dell'albero di `get_parser("sql")` per tipo di nodo
  (`sql_grammar.tree_objects`: nessun testo letto, nessuna regola per un caso); sqlglot = `sqlglot.parse` (espressioni `Create`),
  senza dialetto (come il prodotto) e col dialetto del progetto (`oracle` | `postgres`). Di sqlglot la riga è quella del nome
  (tiene la riga degli identificatori), e i file sopra 200 KB si saltano (4 su 346 nei `.sql`).
- **Fixture** (`fixtures/`, scritte a mano, annotate in `fixtures/gold.json`): package spec e body (costanti, cursore, eccezione,
  `q'[..]'`, `EXECUTE IMMEDIATE` con DDL in stringa, commento con DDL), trigger riga e composto, quoting (identificatori fra
  virgolette con spazio e punto, `$$` e `$tag$`, DDL in stringa e in commento), commento annidato PostgreSQL, DDL ANSI/Oracle (sequenza, indice,
  vista materializzata, funzione senza parentesi). Oggetto = (tipo, nome minuscolo senza virgolette, riga iniziale, riga finale, annidato).
- **Corpus** (`sql_corpus.py`, scaricato a tag dalla funzione con la rete e letto in memoria, nulla gira; i sorgenti non si tengono qui):
  utPLSQL v3.1.14, Logger (master), pljson v3.5.0, oos-utils (master), db-sample-schemas v23.3, PostgreSQL REL_17_0 (`src/test/regress/sql`, 250 al massimo
  a seme fisso), pagila (master). Commit risolti, licenze e sha256 dei file in `results/corpus.json`. I tag di Logger, oos-utils e pagila non esistevano:
  buchi registrati in `holes`, ripiego sul ramo `master` (il commit misurato è quello scritto). File fino a 2 MB (tetto del prodotto);
  si misurano solo quelli che `detect_language` legge come `sql` o `plsql` (346 + 140 su 688 scelti; `.tps`, `.tpb`, `.pck` non sono estensioni lette).
- **Crescita** (`growth_worker.py`): un processo per lettore, testo a N e 4N ripetizioni più una linea di base, timeout 180 s; memoria = picco del processo meno la base.

Corsa: `python -m modal run benchmarks/sql-grammar/modal_sql.py [--step warm|prepare|fixtures|measure|growth]`; test della logica pura: `modal run tests/modal_pytest.py --args "benchmarks/sql-grammar/test_sql_grammar.py -q"`.

## Risultati: fixture contro l'annotazione (22 oggetti: 17 di primo livello, 5 sottoprogrammi di package)

| Lettore | Trovati | Mancanti | In più | Riga iniziale diversa | Riga finale |
| --- | --- | --- | --- | --- | --- |
| regex (oggi) | 21 | 1 (`function customer_name`, senza parentesi) | 0 | 3 | nessuna |
| tree-sitter `sql` | 13 | 9 | 1 (`ghost_nested`) | 1 | giusta in 13 su 13 |
| sqlglot, senza dialetto | 1 | 21 | 0 | 0 | nessuna |
| sqlglot, col dialetto | 6 | 16 | 0 | 0 | nessuna |

Per file: `quoting.sql` (SQL standard e PostgreSQL) tree-sitter 5/5 con righe e fine giuste, regex 5/5, sqlglot 5/5 solo col dialetto `postgres`.
Package spec e body, trigger: tree-sitter 0 trovati su 2 package e 2 trigger (`ERROR` su tutto il file; del body vede solo una `add_item` sbagliata, righe 1-18);
regex trova tutto ma con 3 righe sbagliate nel body (`fee` 2 invece di 4, `add_item` 8 invece di 9, `total` 19 invece di 20: l'espressione dei sottoprogrammi parte da `^\s*` e
si prende le righe vuote che precedono). Commento annidato PostgreSQL: tree-sitter lo chiude al primo `*/` e legge `ghost_nested` come tabella, regex e sqlglot no.
`ddl.sql`: tree-sitter e regex perdono entrambi `customer_name` (funzione senza parentesi); sqlglot non legge il file (`ParseError` sulla procedura `IS`).

## Risultati: corpus, albero e oggetti (nessuna verità: il riferimento del confronto è il lettore regex)

| Linguaggio (file) | File con ERROR/MISSING | Nodi ERROR | Byte dentro ERROR | Oggetti regex | Oggetti tree-sitter | In comune | Solo regex | Solo tree-sitter |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| plsql (140) | 140 (100%) | 6,876 | 90.6% | 1,819 | 357 | 323 | 1,496 | 34 |
| sql (346) | 320 (92%) | 96,742 | 34.4% | 6,252 | 3,889 | 3,484 | 2,768 | 405 |

Nel plsql tutto ciò che manca al tree-sitter è: funzioni 899, procedure 388, package 54, package body 53, type body 8, trigger 50 (dei 56 che il regex legge, 6 in comune). Nel sql le differenze maggiori sono `table` (in comune 1,897, solo regex 1,908, solo tree-sitter 41: la grammatica perde le tabelle dei file di regressione PostgreSQL con costrutti che non regge, ma non è stato verificato file per file) e `index` (in comune 438, solo regex 181, solo tree-sitter 162);
sono differenze, non errori accertati: sul corpus non c'è annotazione (i dettagli per file sono in `results/measure.json.gz`, i totali in `results/summary.json`).
sqlglot sul corpus: oggetti 318 (senza dialetto) e 486 (con dialetto) contro i 6,252 del regex nei `.sql`, 0 nei file PL/SQL (139 su 140 `ParseError`).

Tempo totale di lettura (ms, parse e estrazione, tutti i file): plsql regex 4,018, tree-sitter 601, sqlglot 936; sql regex 21,673, tree-sitter 7,420, sqlglot 5,972.

## Risultati: costo (testi che crescono, N e 4N; rapporto = tempo su 4N diviso 4 volte il tempo su N, 1 = lineare)

| Testo | regex | tree-sitter | sqlglot |
| --- | --- | --- | --- |
| `CREATE TABLE` ripetuti (N = 5,000 e 20,000) | 1.71 lineare, memoria +5 e +98 MB | 0.98 lineare, +5 e +62 MB | 0.89 lineare, 0 e +74 MB |
| package body ripetuti (N = 500 e 2,000) | 1.24 lineare | 0.92 lineare | 1.73 lineare |
| `/* ` mai chiuso (N = 20,000 e 80,000) | 0.52 lineare | **3.93 superlineare** (4.8 s e 76 s) | 0.36 lineare |
| `$a$ ` mai chiuso (N = 20,000 e 80,000) | 0.66 lineare | rumore (35 e 165 ms) | 0.57 lineare |

Valori esatti in `results/growth.json`.

## Verdetto (la scelta è del proprietario)

- Il pack non ha `plsql`; la grammatica `sql` **non regge PL/SQL**: ERROR in 140 file su 140, il 91% dei byte dentro nodi ERROR, nessun nodo per package, package body e type body, trigger e funzioni di package persi. Sul PL/SQL il lettore regex trova molto di più (1,819 oggetti contro 357) ed è da tenere.
- Sul SQL standard e PostgreSQL la grammatica `sql` legge bene (`quoting.sql` 5/5, righe iniziale e finale giuste, dollar-quote e quoting compresi) ma lascia errori nel 92% dei file del corpus, non nidifica i commenti (legge `ghost_nested` come tabella) e ha un costo superlineare su un `/*` mai chiuso. Dà la riga finale che il regex non ha.
- sqlglot non è un lettore di oggetti adatto: non legge PL/SQL né il DDL Oracle, e senza dialetto perde anche il PostgreSQL con `$$`.
- Scelte aperte: (a) tenere i lettori regex e correggere la riga dei sottoprogrammi (`^\s*` prende le righe vuote) e la funzione senza parentesi; (b) usare la grammatica `sql` solo per il SQL standard con ripiego sul regex, accettando l'errore nel 92% dei file; (c) cercare una grammatica PL/SQL fuori dal pack (non valutata qui: `ANTLR grammars-v4` non è stato eseguito). Nessuna è decisa.
