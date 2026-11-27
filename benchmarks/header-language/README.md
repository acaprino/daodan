# Come riconoscere un `.h`: C, C++ o Objective-C

Prova della sezione «`.h`: prima la prova» di `docs/specs/2026-11-24-libreria-del-linguaggio.md`. Quattro vie contro la risposta giusta nota, su header di progetti di sola C, di sola C++ e di Objective-C. Gli strumenti veri (le grammatiche, la regola `.h` del prodotto) girano solo su Modal; il resto è libreria standard. Ogni numero delle tabelle viene da `results/*.json` (`header_tables.py --write`): un test fallisce se il README non è quello che i JSON producono.

**Stato al 25 novembre 2026.** Il proprietario ha scelto l'albero (T): il prodotto legge un `.h` con la via `R3dx` (`daodan/core/languages/header.py`, sezione «Il prodotto»). Il candidato `fixqc` era entrato nel prodotto con il commit `cd19c05e8` e ne è uscito allora. «R0», «prima» e, dove è rimasto, «oggi» sono in tutto il README e in `results/` la regola di prima: quella del commit `3960973d8`, congelata in `header_patterns.py` (`BEFORE_*`, un test la confronta con il commit via `git show`). `CPP_FIXQC` è congelato al commit `cd19c05e8`, `NOISE_FIXQ` è ancora il pattern del prodotto, e `test_header_patterns.py` li confronta. `Probe.r0` esegue la copia congelata (`fixqc`), non il prodotto: la risposta del prodotto è `languages.detect_language`, che `--step product` esegue.

## Le vie

| Via | Come decide |
| --- | --- |
| R0 | La regola `.h` di prima del 25 novembre (commit `3960973d8`): due regex di `daodan/core/languages/__init__.py` su un testo senza commenti e stringhe, congelate in `header_patterns.py` (`BEFORE_*`). Tutti i risultati registrati sono di questa regola |
| R1 | Un albero C++ (tree-sitter): C++ se contiene nodi che la grammatica C non ha. `d` = nodi di dichiarazione, `e` = anche espressioni; `g` = i nodi dentro un blocco `#if` che nomina `__cplusplus` non contano; `o` = prima la grammatica Objective-C. L'elenco dei nodi solo-C++ è la differenza tra le due grammatiche (`test_header_probe.py` la ricalcola) |
| R2 | Due o tre grammatiche (C, C++, anche Objective-C): vince quella con meno nodi `ERROR` e `MISSING`; a parità, C |
| R3 | R1 con i nodi (`R3d`: di dichiarazione; `R3`: anche le espressioni); se non ne trova, R2 a tre grammatiche |
| `x` | La regola Objective-C prima, nessuna grammatica Objective-C: dove R0 dice Objective-C la risposta è quella e l'header non si parsa; altrimenti l'albero sceglie tra C e C++. `R1dx` e `R1ex` sono R1 senza guardia (`d`, `e`), `R3dx` è `R3d` con C e C++ soltanto |

## In breve

<!-- table:verdict -->
| Via | C giusti (*) | C++ sbagliati | ObjC giusti | Simboli persi | Costo s: totale / marginale | Marginale ms: mediana / p95 / massimo | Crescita peggiore (esponente) | Righe rispetto a prima |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R0 regola di prima | 99.8% | 12.0 ± 5.9 | 91.3% | 55 | 2.9 / 2.9 | 0.13 / 2.0 / 112 | 2.0 (`escaped_dq`) | +0 |
| R0 con `fixqc` (ora nel prodotto) | 99.8% | 12.0 ± 5.9 | 91.3% | 55 | 3.8 / 3.8 | 0.19 / 2.6 / 133 | 1.0 (`escaped_dq`) | +0 |
| R1 nodi dichiarazione, guardia | 99.8% | 68.3 ± 12.4 | 0.0% | 393 | 18.5 / 14.9 | 0.28 / 2.9 / 6,982 | 2.0 (`open_comment_repeat`) | +89 |
| R1 nodi + espressioni, guardia | 97.6% | 4.0 ± 3.5 | 0.0% | 389 | 18.5 / 14.4 | 0.24 / 2.7 / 6,982 | 2.0 (`open_comment_repeat`) | +89 |
| R1 dichiarazioni, senza guardia, regola ObjC davanti | 97.8% | 64.2 ± 12.2 | 91.3% | 14 | 21.1 / 17.2 | 0.40 / 4.5 / 7,008 | 2.0 (`escaped_dq`) | +80 |
| R1 espressioni, senza guardia, regola ObjC davanti | 94.1% | 0.0 ± 0.0 | 91.3% | 29 | 21.1 / 16.8 | 0.39 / 4.4 / 7,008 | 2.0 (`escaped_dq`) | +80 |
| R2 meno ERROR, C e C++ | 98.2% | 52.2 ± 11.3 | 0.0% | 500 | 43.3 / 27.6 | 0.78 / 13.5 / 6,987 | 2.0 (`open_comment_repeat`) | +48 |
| R2 meno ERROR, C, C++, ObjC | 96.3% | 56.2 ± 11.6 | 91.3% | 1025 | 68.3 / 52.9 | 1.36 / 25.3 / 13,959 | 2.0 (`open_comment_repeat`) | +48 |
| R3 nodi, poi meno ERROR | 94.1% | 0.0 ± 0.0 | 34.8% | 514 | 42.8 / 27.2 | 0.33 / 4.0 / 13,959 | 2.0 (`open_comment_repeat`) | +98 |
| R3 (dichiarazioni, poi meno ERROR) | 96.3% | 0.0 ± 0.0 | 91.3% | 551 | 43.6 / 28.3 | 0.41 / 4.8 / 13,959 | 2.0 (`open_comment_repeat`) | +98 |
| R3 (dichiarazioni, poi meno ERROR) senza grammatica ObjC, regola ObjC davanti | 98.0% | 0.0 ± 0.0 | 91.3% | 29 | 33.2 / 17.8 | 0.43 / 4.9 / 7,013 | 2.0 (`escaped_dq`) | +106 |
<!-- /table -->

«Simboli persi» sono le definizioni (funzioni, classi, metodi) che l'adattatore di Daodan estrae con la lettura giusta e non con quella data, e quelle di un header che la via dichiara Objective-C (che il prodotto non legge); l'etichetta è quella del progetto, spostata dalle annotazioni, e dove un header è indifferente non perde nulla comunque. «C++ sbagliati» è la stima con le etichette (± errore standard); un «0.0 ± 0.0» è «nessuno visto nel campione», non «nessuno». La crescita è l'esponente del tempo sulla grandezza del testo cattivo peggiore, da 2 a 32 KB (1 è lineare, 2 quadratico). «Righe» sono quelle che la via aggiunge a prima, con il controllo prima del parse per le vie ad albero. Sbagliati, simboli e costo delle vie ad albero sono senza tetto (con il tetto vedi «Costo» e «Il tetto non è gratis»). Le due righe R0 hanno il costo della stessa corsa.

**(\*) La colonna «C giusti» è gonfiata a favore di R0.** Gli header dei progetti C valgono «C» perché lo dice il progetto, non il testo (anche i 30 annotati: la regola di «indifferente» non è stata applicata ai C): una via che risponde C++ a un header C indifferente è contata sbagliata, R0, che tende al C, no. La classifica si decide sui simboli persi, che non passano da nessuna etichetta.

**Decisione del proprietario (25 novembre): `R3dx`, nel prodotto.** La raccomandazione di questo file era R0 con `fixqc` (il testo che segue è quello della raccomandazione; i pattern, scritti per intero, sono sotto). R0 vince per costo e righe ed è alla pari per simboli persi: le vie ad albero migliori sui simboli, con la regola Objective-C davanti (`R1dx`, `R1ex`, `R3dx`), ne perdono meno di R0 per poche decine su tutto il corpus, `R1ex` e `R3dx` sbagliano meno header C++ (nessuno visto, contro quelli di R0), ma costano molte volte di più (totale e marginale), hanno un massimo di secondi su tabelle di numeri che il prodotto parsa comunque, ereditano la crescita quadratica della regex di prima (la regola Objective-C davanti) e vogliono decine di righe in più e un controllo scritto a mano prima del parse. Dove sta il loro vantaggio sul C++: pochi header (sotto «confronto con R0»).

**Conflitto con AGENTS** («il codice si legge dall'albero, mai con espressioni regolari»): tenere R0 chiedeva un'eccezione del proprietario, motivata con costo e righe, non con la giustezza; le soluzioni pronte valutate sono R1, R2 e R3 di questo file. Il proprietario ha scelto `R3dx` (la più giusta sul C++, simboli alla pari), con la regola Objective-C davanti e un tetto: il prezzo è nelle tabelle «Righe di codice» e «Il tetto non è gratis» e nella sezione «Il prodotto».

**Vie da non scegliere**: quelle in cui la grammatica Objective-C decide tra C e C++ (`R1…o` con espressioni, `R2o`, `R3`, `R3d`): header C e C++ letti come Objective-C, che il prodotto non legge, perdono tutti i loro simboli (colonna «C o C++ letto ObjC» della tabella delle perdite). Quelle che non hanno né la grammatica né la regola Objective-C (`R1dg`, `R1eg`, R2 da sola) non dicono mai «Objective-C»: gli header Objective-C, oggi lasciati (R0 risponde «nessun linguaggio»), verrebbero letti come C o C++ (la matrice lo mostra). R2 da sola non supera la migliore R1 né sul C né sul C++.

## I pattern candidati

Tre, in `header_patterns.py`, ciascuno scritto per intero e controllato dai test contro quello di prima (congelato) e, per `fixqc`, contro il prodotto (`test_header_patterns.py`, `test_header_probe.py`): se il prodotto cambia un pattern, i test falliscono, non diventano un no-op. In ordine: `fix` (solo la prima modifica), `fixq` (anche le virgolette), `fixqc` (anche `class`: il candidato finale).

`_C_NOISE_RE`, finale (`fixq`; flag `re.DOTALL`):

```
//[^\n]*|/\*.*?(?:\*/|\Z)|(?<!\\)"(?:\\.|[^"\\\n])*+"|(?<!\\)\'(?:\\.|[^\'\\\n])*+\'
```

`_CPP_HEADER_RE`, finale (`fixqc`; flag `re.MULTILINE`; l'unica modifica è `class`):

```
\bnamespace\s+\w+(?:\s*::\s*(?:inline\s+)?\w+)*\s*\{|^[ \t]*namespace\s*\{|^[ \t]*namespace\s+\w+\s*=(?!=)|\bclass\s+\w++(?:(?!\bclass\s+\w)[^;(){}])*+\{|\btemplate\s*<|^[ \t]*(?:public|private|protected)\s*:|\busing\s+namespace\b|\bstd::\w|^[ \t]*#\s*include\s*<(?:cstdint|string|vector|map|list|array|bitset|queue|stack|forward_list|unordered_map|unordered_set|(?:i|o|io)stream)>
```

`_OBJC_HEADER_RE` non cambia. I quantificatori possessivi (`*+`, `++`) vogliono Python 3.11 o più (il progetto chiede 3.12).

Che cosa fa ciascuna modifica, e dove cambia una risposta:
- **`|\Z`**: un `/*` mai chiuso è un solo commento fino alla fine del testo (non uno per ogni `/*`: la crescita quadratica). Cambia una risposta da C++ a C dove un `/*` non ha mai una `*/` dopo e nel resto del testo c'è C++: `#include <foo/*>`, `a/*p` (una divisione per un puntatore dereferenziato, senza spazio), una raw string che contiene un `"` e un `/*`. Oggi quel `/*` non è un commento; con la modifica copre il resto del file, come lo legge il compilatore. Sulle header reali: nessuna risposta cambiata.
- **Le virgolette**: una stringa si apre solo su una virgoletta che nessun backslash precede e non torna indietro (la crescita quadratica di `"\"\"\"…`). Cambia una risposta solo dove una virgoletta segue un backslash fuori da una stringa e il resto è un `/*`: codice che non compila.
- **`class`**: la ricerca si ferma al `class NOME` seguente, da cui parte lo stesso incontro che sarebbe partito dal primo: la risposta non cambia (un test lo confronta con quello di prima su 20000 testi casuali di quei pezzi), il costo diventa lineare. Il tetto `{0,400}` provato prima non va: perde un C++ vero con le basi lunghe (14 basi `public ns::VeryLongInterfaceName<int>` superano 400 caratteri tra il nome e la graffa).

## Il corpus e le etichette

<!-- table:corpus -->
| Etichetta del progetto | Progetti | Header | MB |
| --- | --- | --- | --- |
| C | 14 | 2,171 | 16.1 |
| C++ | 12 | 2,327 | 23.5 |
| Objective-C | 5 | 297 | 1.0 |

Grandezza di un header: mediana 2,860 byte, p95 32,534, massimo 908,527; 1,058 sopra 8 KB, 544 sopra 16 KB, 238 sopra 32 KB.
<!-- /table -->

Progetti e commit fissati in `header_corpus.py` (licenza di ogni commit, controllata con l'API di GitHub). In locale non si tengono sorgenti: solo percorso e sha256. I sorgenti selezionati stanno nel volume Modal `daodan-header-language`, anche quelli di `linux` (GPL-2.0 con eccezione, non ridistribuibile: il volume è la sola copia e non ne esce nulla). Un header per contenuto (il primo per percorso); dove un progetto ha più header del tetto, se ne prendono quelli del tetto nell'ordine del seme `header-language-1`.

**Etichetta di un header** = quella del suo progetto (C, C++, Objective-C), spostata da un prefisso di percorso dove il progetto mescola linguaggi (`include/leveldb/c.h` è l'API C di un progetto C++), e dall'**annotazione a mano** di `labels.json` (`progetto/percorso` → `label`, `why`, `declared`, `stratum`, `sha`). Una quarta categoria, **indifferente** (`either`): nessuna riga dell'header dice C da C++ (solo direttive, macro, dichiarazioni valide in entrambi); qualunque risposta è giusta.

Si annotano solo i **pool**: gli header che almeno una delle nove vie principali (`R0 R1dg R1eg R1dgo R1ego R2 R2o R3 R3d`) legge diversamente dall'etichetta del progetto, divisi in `all` (tutte le vie sbagliano) e `some`. Di ogni pool si annota un campione (`header_report.py --sample 90,30,25`, seme fisso, almeno due per stratum: le etichette di `labels.json` sono esattamente quelle, un test lo verifica), e il resto del pool si stima dal campione, stratum per stratum, con il suo errore standard (`estimate`). Gli header fuori dai pool (tutte e nove le vie d'accordo con il progetto) non sono stati annotati: valgono l'etichetta del progetto.

<!-- table:truth -->
| Header di progetti | Header | In un pool | Annotati | Indifferenti (stima ± e.s.) | Stessi simboli letti C o C++ | Letto C non perde nulla | Nessun nodo solo-C++ |
| --- | --- | --- | --- | --- | --- | --- | --- |
| C | 2,184 | 134 | 30 | 0.0 ± 0.0 | 2,128 | 2,157 | 1,840 |
| C++ | 2,314 | 363 | 90 | 106.0 ± 6.0 | 544 | 586 | 114 |
| Objective-C | 297 | 297 | 25 | 7.0 ± 0.0 | 264 | 275 | 74 |

I 119 header di progetti C++ che la regola di prima legge C: 29 annotati (25 indifferenti, 3 C++, 1 C); 3 perdono simboli (37 su 94 che hanno); 104 non hanno alcun nodo solo-C++ nell'albero.

Le etichette a mano contro i soli simboli: 28 dei 28 «indifferenti» danno gli stessi simboli letti C o C++; dei 63 «C++», 35 ne danno di più letti C++, 27 gli stessi, 1 di meno.
<!-- /table -->

Due strade indipendenti per «quanti sono davvero indifferenti»: le annotazioni (stima, con errore) e i simboli (un censimento, senza etichette: lo stesso numero di simboli letti C o C++). Più avanti, nelle perdite, i simboli sono la misura che non passa da nessuna etichetta.

## Giusti e sbagliati

Stime con le etichette, per categoria vera.

<!-- table:right -->
| Via | C sbagliati su 2188 | C++ sbagliati su 2204 | ObjC sbagliati su 290 | Accordo con le etichette a mano |
| --- | --- | --- | --- | --- |
| R0 regola di prima | 4.5 ± 3.9 (99.8%) | 12.0 ± 5.9 (99.5%) | 25.2 ± 16.7 (91.3%) | 139/145 |
| R1 nodi dichiarazione, guardia | 4.5 ± 3.9 (99.8%) | 68.3 ± 12.4 (96.9%) | 290.0 ± 0.0 (0.0%) | 104/145 |
| R1 nodi + espressioni, guardia | 53.6 ± 10.7 (97.6%) | 4.0 ± 3.5 (99.8%) | 290.0 ± 0.0 (0.0%) | 109/145 |
| R1 dichiarazione, guardia, ObjC prima | 4.5 ± 3.9 (99.8%) | 68.3 ± 12.4 (96.9%) | 63.0 ± 24.5 (78.3%) | 122/145 |
| R1 espressioni, guardia, ObjC prima | 58.1 ± 10.9 (97.3%) | 132.5 ± 14.1 (94.0%) | 0.0 ± 0.0 (100.0%) | 99/145 |
| R2 meno ERROR, C e C++ | 40.2 ± 10.0 (98.2%) | 52.2 ± 11.3 (97.6%) | 290.0 ± 0.0 (0.0%) | 100/145 |
| R2 meno ERROR, C, C++, ObjC | 80.4 ± 10.7 (96.3%) | 56.2 ± 11.6 (97.5%) | 25.2 ± 16.7 (91.3%) | 111/145 |
| R3 nodi, poi meno ERROR | 129.5 ± 3.9 (94.1%) | 0.0 ± 0.0 (100.0%) | 189.1 ± 28.3 (34.8%) | 101/145 |
| R3 (dichiarazioni, poi meno ERROR) | 80.4 ± 10.7 (96.3%) | 0.0 ± 0.0 (100.0%) | 25.2 ± 16.7 (91.3%) | 125/145 |
| R1 dichiarazioni, senza guardia, regola ObjC davanti | 47.5 ± 3.9 (97.8%) | 64.2 ± 12.2 (97.1%) | 25.2 ± 16.7 (91.3%) | 126/145 |
| R1 espressioni, senza guardia, regola ObjC davanti | 129.5 ± 10.9 (94.1%) | 0.0 ± 0.0 (100.0%) | 25.2 ± 16.7 (91.3%) | 129/145 |
| R3 (dichiarazioni, poi meno ERROR) senza grammatica ObjC, regola ObjC davanti | 44.7 ± 10.3 (98.0%) | 0.0 ± 0.0 (100.0%) | 25.2 ± 16.7 (91.3%) | 133/145 |

Veri per categoria (stima ± e.s.): C 2188.1 ± 3.5, C++ 2204.0 ± 4.9, Objective-C 290.0 ± 0.0, indifferenti 113.0 ± 6.0.
<!-- /table -->

Il confronto con R0 sugli stessi header (sbagliati della via meno quelli di R0, con il suo errore standard: negativo = meglio di R0). È il confronto da leggere: non porta il dubbio su quali header siano davvero C o C++, che le due vie condividono.

<!-- table:versus -->
| Via | C: sbagliati in più | C++: sbagliati in più | ObjC: sbagliati in più |
| --- | --- | --- | --- |
| R1 nodi dichiarazione, guardia | +0.0 ± 5.7 | +56.2 ± 11.6 | +264.8 ± 16.7 |
| R1 nodi + espressioni, guardia | +49.1 ± 12.0 | -8.0 ± 7.0 | +264.8 ± 16.7 |
| R1 dichiarazione, guardia, ObjC prima | +0.0 ± 5.7 | +56.2 ± 11.6 | +37.8 ± 20.0 |
| R1 espressioni, guardia, ObjC prima | +53.6 ± 12.1 | +120.5 ± 16.5 | -25.2 ± 16.7 |
| R2 meno ERROR, C e C++ | +35.7 ± 11.2 | +40.2 ± 13.3 | +264.8 ± 16.7 |
| R2 meno ERROR, C, C++, ObjC | +75.9 ± 12.2 | +44.2 ± 13.6 | +0.0 ± 17.5 |
| R3 nodi, poi meno ERROR | +125.1 ± 7.9 | -12.0 ± 5.9 | +163.9 ± 34.2 |
| R3 (dichiarazioni, poi meno ERROR) | +75.9 ± 12.2 | -12.0 ± 5.9 | +0.0 ± 17.5 |
| R1 dichiarazioni, senza guardia, regola ObjC davanti | +43.0 ± 5.7 | +52.2 ± 11.3 | +0.0 ± 0.0 |
| R1 espressioni, senza guardia, regola ObjC davanti | +125.1 ± 10.9 | -12.0 ± 5.9 | +0.0 ± 0.0 |
| R3 (dichiarazioni, poi meno ERROR) senza grammatica ObjC, regola ObjC davanti | +40.2 ± 11.5 | -12.0 ± 5.9 | +0.0 ± 0.0 |

Da dove viene il vantaggio sul C++: gli header annotati «C++» che R0 legge C sono 3 e perdono 0 simboli; i simboli che R0 perde sul C++ (37) stanno in 3 header, tutti non annotati.
<!-- /table -->

La matrice stimata (vero per riga, risposta per colonna) per una via di ogni famiglia:

<!-- table:matrix -->
| Via | Vero | letto C | letto C++ | letto ObjC |
| --- | --- | --- | --- | --- |
| R0 regola di prima | C | 2183.6 ± 5.3 | 4.5 ± 3.9 | 0.0 ± 0.0 |
|  | C++ | 12.0 ± 5.9 | 2191.9 ± 7.5 | 0.0 ± 0.0 |
|  | Objective-C | 25.2 ± 16.7 | 0.0 ± 0.0 | 264.8 ± 16.7 |
|  | indifferenti | 108.9 ± 5.0 | 4.0 ± 3.5 | 0.0 ± 0.0 |
| R1 nodi + espressioni, guardia | C | 2134.5 ± 11.3 | 53.6 ± 10.7 | 0.0 ± 0.0 |
|  | C++ | 4.0 ± 3.5 | 2200.0 ± 5.9 | 0.0 ± 0.0 |
|  | Objective-C | 113.5 ± 29.0 | 176.5 ± 29.0 | 0.0 ± 0.0 |
|  | indifferenti | 108.9 ± 5.0 | 4.0 ± 3.5 | 0.0 ± 0.0 |
| R1 dichiarazioni, senza guardia, regola ObjC davanti | C | 2140.6 ± 5.3 | 47.5 ± 3.9 | 0.0 ± 0.0 |
|  | C++ | 64.2 ± 12.2 | 2139.7 ± 12.7 | 0.0 ± 0.0 |
|  | Objective-C | 25.2 ± 16.7 | 0.0 ± 0.0 | 264.8 ± 16.7 |
|  | indifferenti | 113.0 ± 6.0 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| R3 (dichiarazioni, poi meno ERROR) | C | 2107.7 ± 11.3 | 40.2 ± 10.0 | 40.2 ± 10.0 |
|  | C++ | 0.0 ± 0.0 | 2204.0 ± 4.9 | 0.0 ± 0.0 |
|  | Objective-C | 12.6 ± 12.1 | 12.6 ± 12.1 | 264.8 ± 16.7 |
|  | indifferenti | 108.9 ± 6.9 | 0.0 ± 0.0 | 4.1 ± 3.5 |
<!-- /table -->

Esempi di errori (prima gli annotati a mano; la riga è il primo nodo che la via non ha visto, o che l'ha tratta in inganno):

<!-- table:examples -->
- R0 regola di prima, c letto cpp: 5 (es. `cpython/Include/internal/mimalloc/mimalloc/atomic.h`, `redis/src/lzfP.h`*)
- R0 regola di prima, cpp letto c: 93 (es. `bitcoin/src/policy/fees_args.h:10`, `bitcoin/src/pow.h:13`)
- R0 regola di prima, objc letto c: 36 (es. `iglistkit/Source/IGListDiffKit/IGListCompatibility.h:8`, `iglistkit/Source/IGListKit/Internal/IGListCollectionViewLayoutInternal.h:9`)
- R1 nodi + espressioni, guardia, c letto cpp: 60 (es. `musl/arch/microblaze/atomic_arch.h:49`, `sqlite/src/vdbeInt.h:580`)
- R1 nodi + espressioni, guardia, cpp letto c: 95 (es. `wil/include/wil/result_macros.h:1595`, `abseil/absl/base/attributes.h`*)
- R1 dichiarazioni, senza guardia, regola ObjC davanti, c letto cpp: 58 (es. `linux/include/linux/greybus/hd.h:44`, `redis/src/lzfP.h:142`*)
- R1 dichiarazioni, senza guardia, regola ObjC davanti, cpp letto c: 158 (es. `spdlog/include/spdlog/async_logger-inl.h:16`, `bitcoin/src/clientversion.h:36`)
- R1 dichiarazioni, senza guardia, regola ObjC davanti, objc letto c: 36 (es. `iglistkit/Source/IGListDiffKit/IGListCompatibility.h:8`, `iglistkit/Source/IGListKit/Internal/IGListCollectionViewLayoutInternal.h:9`)
- R3 (dichiarazioni, poi meno ERROR), c letto cpp: 52 (es. `libuv/include/uv/win.h`, `libuv/src/win/fs-fd-hash-inl.h`)
- R3 (dichiarazioni, poi meno ERROR), c letto objc: 37 (es. `curl/include/curl/curl.h:161`, `mbedtls/library/alignment.h:1`)
- R3 (dichiarazioni, poi meno ERROR), cpp letto c: 87 (es. `abseil/absl/base/attributes.h`*, `abseil/absl/base/config.h:162`*)
- R3 (dichiarazioni, poi meno ERROR), cpp letto objc: 3 (es. `abseil/absl/base/internal/inline_variable.h`*, `abseil/absl/debugging/internal/stacktrace_config.h`*)
- R3 (dichiarazioni, poi meno ERROR), objc letto c: 19 (es. `iglistkit/Source/IGListDiffKit/IGListCompatibility.h:8`, `afnetworking/AFNetworking/AFCompatibilityMacros.h`*)
- R3 (dichiarazioni, poi meno ERROR), objc letto cpp: 10 (es. `iglistkit/Source/IGListKit/IGListBindingSectionControllerSelectionDelegate.h:8`, `afnetworking/AFNetworking/AFHTTPSessionManager.h:22`*)

`*` = non annotato a mano: la sua etichetta è quella del progetto.
<!-- /table -->

## La perdita in simboli

Con l'etichetta (annotata a mano dove c'è, del progetto altrove). «Header» = letti con la lettura sbagliata, «con perdita» = ne perdono, «persi di N» = su N che la lettura giusta estrae da quegli header.

<!-- table:loss -->
| Via | C++ letto C: header / con perdita / simboli persi | C letto C++: header / con perdita / simboli persi | C o C++ letto ObjC (non letto affatto) | Simboli persi in tutto |
| --- | --- | --- | --- | --- |
| R0 regola di prima | 93 / 3 / 37 di 87 | 5 / 1 / 18 di 179 | 0 | 55 |
| R1 nodi dichiarazione, guardia | 163 / 8 / 393 di 711 | 11 / 0 / 0 di 140 | 0 | 393 |
| R1 nodi + espressioni, guardia | 95 / 3 / 379 di 473 | 60 / 3 / 10 di 1124 | 0 | 389 |
| R1 dichiarazione, guardia, ObjC prima | 163 / 8 / 393 di 711 | 11 / 0 / 0 di 140 | 0 | 393 |
| R1 espressioni, guardia, ObjC prima | 95 / 3 / 379 di 473 | 59 / 3 / 10 di 1124 | 110 header, 7289 simboli | 7678 |
| R2 meno ERROR, C e C++ | 150 / 16 / 471 di 693 | 44 / 2 / 29 di 829 | 0 | 500 |
| R2 meno ERROR, C, C++, ObjC | 147 / 16 / 471 di 693 | 43 / 2 / 29 di 745 | 43 header, 525 simboli | 1025 |
| R3 nodi, poi meno ERROR | 85 / 0 / 0 di 35 | 97 / 5 / 39 di 1723 | 37 header, 475 simboli | 514 |
| R3 (dichiarazioni, poi meno ERROR) | 87 / 0 / 0 di 218 | 52 / 2 / 29 di 834 | 40 header, 522 simboli | 551 |
| R1 dichiarazioni, senza guardia, regola ObjC davanti | 158 / 5 / 14 di 274 | 58 / 0 / 0 di 550 | 0 | 14 |
| R1 espressioni, senza guardia, regola ObjC davanti | 90 / 0 / 0 di 36 | 135 / 5 / 29 di 2164 | 0 | 29 |
| R3 (dichiarazioni, poi meno ERROR) senza grammatica ObjC, regola ObjC davanti | 90 / 0 / 0 di 218 | 53 / 2 / 29 di 918 | 0 | 29 |
<!-- /table -->

<!-- table:loss_declared -->
Con la sola etichetta del progetto, senza alcuna annotazione, gli header con perdita e i simboli persi (C++ letto C, C letto C++) sono gli stessi in tutte le vie: un header indifferente non perde nulla comunque lo si legga.
<!-- /table -->

## Costo

<!-- table:cost -->
| Via | Totale s | Marginale s | Totale ms: mediana / p95 / massimo | Marginale ms: mediana / p95 / massimo | Con tetto 8 KB, totale ms |
| --- | --- | --- | --- | --- | --- |
| R0 regola di prima | 2.9 | 2.9 | 0.14 / 1.9 / 80 | 0.14 / 1.9 / 80 | 0.13 / 1.2 / 3.9 |
| R0 regola di prima (corsa r0check) | 2.9 | 2.9 | 0.13 / 2.0 / 112 | 0.13 / 2.0 / 112 | — |
| R0 con `fixqc` (ora nel prodotto) (corsa r0check) | 3.8 | 3.8 | 0.19 / 2.6 / 133 | 0.19 / 2.6 / 133 | — |
| R1 nodi dichiarazione, guardia | 18.5 | 14.9 | 0.47 / 5.8 / 6,982 | 0.28 / 2.9 / 6,982 | — |
| R1 nodi + espressioni, guardia | 18.5 | 14.4 | 0.47 / 5.8 / 6,982 | 0.24 / 2.7 / 6,982 | 0.61 / 2.7 / 236.1 |
| R1 dichiarazioni, senza guardia, regola ObjC davanti | 21.1 | 17.2 | 0.66 / 7.3 / 7,008 | 0.40 / 4.5 / 7,008 | — |
| R1 espressioni, senza guardia, regola ObjC davanti | 21.1 | 16.8 | 0.66 / 7.3 / 7,008 | 0.39 / 4.4 / 7,008 | — |
| R1 espressioni, guardia, ObjC prima | 43.5 | 40.3 | 1.09 / 17.2 / 13,954 | 0.94 / 14.6 / 13,954 | 1.16 / 7.1 / 475.7 |
| R2 meno ERROR, C e C++ | 43.3 | 27.6 | 1.11 / 17.7 / 13,860 | 0.78 / 13.5 / 6,987 | 1.19 / 7.2 / 433.9 |
| R2 meno ERROR, C, C++, ObjC | 68.3 | 52.9 | 1.66 / 29.1 / 20,832 | 1.36 / 25.3 / 13,959 | 1.68 / 11.9 / 673.5 |
| R3 (dichiarazioni, poi meno ERROR) | 43.6 | 28.3 | 0.80 / 8.4 / 20,832 | 0.41 / 4.8 / 13,959 | 0.92 / 3.9 / 673.5 |
| R3 (dichiarazioni, poi meno ERROR) senza grammatica ObjC, regola ObjC davanti | 33.2 | 17.8 | 0.78 / 8.8 / 13,886 | 0.43 / 4.9 / 7,013 | — |

Su tutte le 4,795 header, senza tetto. Marginale = totale meno il parse che il prodotto farebbe comunque con la grammatica del linguaggio dato (l'albero si può tenere); la regola di prima non parsa nulla, quindi il suo costo è tutto marginale. Le due righe «corsa r0check» sono della stessa corsa e si confrontano tra loro; le altre sono di un'altra corsa, su un altro host. Il massimo è `musl/src/locale/gb18030.h` (144,966 byte, una tabella di numeri): 6,873 ms con la grammatica C, 6,976 con C++, 26 ms con la regola di prima; il prodotto la parsa comunque.
<!-- /table -->

Crescita sui testi cattivi (7 forme, da 2 a 32 KB; esponente e tempo alla grandezza maggiore misurata; un timeout è 60 s):

<!-- table:growth -->
| Testo cattivo | R0 di prima | R0 con `\Z` | R0 con `\Z` e le virgolette | R0 con `\Z`, virgolette e `class` | Grammatica C | Grammatica C++ | Controllo lineare |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `blank_lines` | 1.0 (9 ms a 50 KB) | 1.0 (12 ms a 50 KB) | 1.0 (14 ms a 50 KB) | 1.0 (14 ms a 50 KB) | 0.9 (2 ms a 50 KB) | 0.9 (2 ms a 50 KB) | 1.0 (3 ms a 50 KB) |
| `open_comment` | 1.0 (8 ms a 32 KB) | 0.9 (0 ms a 32 KB) | 1.0 (1 ms a 32 KB) | 0.9 (1 ms a 32 KB) | 1.0 (61 ms a 32 KB) | 1.0 (125 ms a 32 KB) | 1.2 (0 ms a 32 KB) |
| `open_comment_repeat` | 2.0 (1,912 ms a 32 KB) | 1.0 (1 ms a 32 KB) | 1.0 (1 ms a 32 KB) | 1.0 (1 ms a 32 KB) | 2.0 (>60,000 ms a 32 KB) | 2.0 (>60,000 ms a 32 KB) | 0.3 (0 ms a 32 KB) |
| `open_comment_lines` | 2.0 (1,223 ms a 32 KB) | 0.9 (1 ms a 32 KB) | 0.9 (1 ms a 32 KB) | 1.0 (1 ms a 32 KB) | 1.9 (1,280 ms a 32 KB) | 1.9 (1,308 ms a 32 KB) | 0.1 (0 ms a 32 KB) |
| `class_repeat` | 1.9 (164 ms a 32 KB) | 1.9 (435 ms a 32 KB) | 1.9 (434 ms a 32 KB) | 1.0 (7 ms a 32 KB) | 1.0 (52 ms a 32 KB) | 1.4 (125 ms a 32 KB) | 1.0 (2 ms a 32 KB) |
| `nested_brace` | 1.0 (5 ms a 32 KB) | 1.0 (7 ms a 32 KB) | 1.0 (8 ms a 32 KB) | 1.0 (8 ms a 32 KB) | 1.9 (722 ms a 32 KB) | 1.9 (720 ms a 32 KB) | 0.9 (2 ms a 32 KB) |
| `open_string` | 0.9 (4 ms a 32 KB) | 1.0 (5 ms a 32 KB) | 1.0 (6 ms a 32 KB) | 1.0 (6 ms a 32 KB) | 1.0 (5 ms a 32 KB) | 1.0 (99 ms a 32 KB) | 0.9 (2 ms a 32 KB) |
| `escaped_dq` | 2.0 (3,607 ms a 32 KB) | 2.0 (3,496 ms a 32 KB) | 1.0 (9 ms a 32 KB) | 1.0 (9 ms a 32 KB) | 1.0 (11 ms a 32 KB) | 1.0 (11 ms a 32 KB) | 1.0 (1 ms a 32 KB) |
| `escaped_sq` | 2.0 (3,408 ms a 32 KB) | 2.0 (3,478 ms a 32 KB) | 1.0 (9 ms a 32 KB) | 1.0 (9 ms a 32 KB) | 1.0 (11 ms a 32 KB) | 1.0 (11 ms a 32 KB) | 1.0 (1 ms a 32 KB) |

Sulle 4,795 header reali i tre candidati danno le stesse risposte della regola di prima (differiscono 0, 0, 0); costo mediano 0.13 / 0.12 / 0.19 / 0.19 ms, totale 2.9 / 2.9 / 3.8 / 3.8 s (prima / `\Z` / + virgolette / + class).
<!-- /table -->

I tempi in ms di corse diverse non si confrontano (la stessa regex, su host diversi, ha variato di più volte tra due corse): vale l'esponente. Un singolo `/*` aperto è lineare (riga `open_comment`); quadratici sono i `/*` ripetuti, uno per riga o di seguito.

Il rimedio minimo e il suo prezzo. **Per le vie ad albero** non basta un tetto ai byte: un testo di `/* ` ripetuti costa secondi anche a 8 KB (colonna «tetto solo»); serve il controllo lineare prima del parse (`safe_prefix`: taglia a fine riga e prima di un `/*` mai chiuso), che con il tetto riduce il peggiore a decine di ms:

<!-- table:caps_bad -->
| Testo cattivo | Regola di prima, 8 KB | Grammatica C++, 8 KB (tetto solo) | Grammatica C++, tetto e controllo (peggiore) | Il controllo da solo (fino a 32 KB) |
| --- | --- | --- | --- | --- |
| `open_comment` | 2.0 | 32.5 | 0.0 | 0.4 |
| `open_comment_repeat` | 120.8 | 4,130.1 | 0.0 | 0.1 |
| `open_comment_lines` | 75.1 | 88.7 | 0.0 | 0.1 |
| `class_repeat` | 11.2 | 15.2 | 15.4 | 1.6 |
| `nested_brace` | 1.2 | 48.1 | 48.8 | 1.6 |
| `open_string` | 0.9 | 24.2 | 24.8 | 1.6 |
| `escaped_dq` | 211.3 | 2.9 | 3.1 | 0.8 |
| `escaped_sq` | 203.5 | 2.7 | 2.8 | 0.8 |
<!-- /table -->

**Il tetto non è gratis**: un header oltre il tetto si legge solo nelle prime righe, e un C++ il cui primo costrutto sta più in là diventa C (conteggi grezzi: gli «sbagliati» includono gli header non annotati; conta la differenza con «nessun tetto»).

<!-- table:cap_accuracy -->
| Via | Tetto | C sbagliati (grezzi) | C++ sbagliati (grezzi) | ObjC sbagliati (grezzi) | Simboli persi |
| --- | --- | --- | --- | --- | --- |
| R0 regola di prima | nessun tetto | 5 | 93 | 36 | 55 |
|  | 8 KB | 3 | 106 | 37 | 1528 |
|  | 16 KB | 3 | 97 | 36 | 446 |
|  | 32 KB | 5 | 95 | 36 | 79 |
| R1 nodi + espressioni, guardia | nessun tetto | 60 | 95 | 295 | 389 |
|  | 8 KB | 80 | 121 | 295 | 2030 |
|  | 16 KB | 75 | 101 | 295 | 699 |
|  | 32 KB | 71 | 97 | 295 | 637 |
| R2 meno ERROR, C e C++ | nessun tetto | 44 | 150 | 295 | 500 |
|  | 8 KB | 31 | 182 | 295 | 2308 |
|  | 16 KB | 34 | 159 | 295 | 754 |
|  | 32 KB | 40 | 154 | 295 | 692 |
<!-- /table -->

**Per R0** il rimedio sono i pattern candidati (sezione «I pattern candidati», tabella della crescita, colonne «R0 con…»): niente tetto, nessuna risposta cambia sulle header reali, e un `/*` mai chiuso copre il resto del testo come fa il compilatore.

## Righe di codice

Contate dal codice del benchmark già provato (`header_probe.py`, `header_routes.py`) con `header_loc.py`: righe che hanno codice, non commenti, non docstring, funzioni intere (le righe del cronometro del benchmark ci sono: i numeri sono un tetto). Una via a grammatica ha bisogno anche di un alias Objective-C in `languages/_treesitter.py`, che Daodan non ha, e di un controllo prima del parse.

<!-- table:lines -->
| Via | Righe di codice della via | Più il controllo prima del parse | Totale | Rispetto a prima |
| --- | --- | --- | --- | --- |
| R0 regola di prima | 15 | — | 15 | 0 |
| R0 con `fixqc` (ora nel prodotto: pattern riscritti, non aggiunti) | 15 | — | 15 | 0 |
| R1 nodi C++ (dichiarazioni o espressioni, guardia) | 65 | 39 | 104 | +89 |
| R1 con la grammatica ObjC | 76 | 39 | 115 | +100 |
| R1 senza guardia, con la regola ObjC (R1dx, R1ex) | 56 | 39 | 95 | +80 |
| R2 meno ERROR (C e C++, o anche ObjC) | 24 | 39 | 63 | +48 |
| R3 nodi, poi meno ERROR | 74 | 39 | 113 | +98 |
| R3 senza grammatica ObjC, con la regola ObjC (R3dx) | 82 | 39 | 121 | +106 |

La regola `.h` del prodotto sono 15 righe di codice (le stesse prima e dopo `fixqc`), di cui 6 sono la parte Objective-C (che le vie con «regola ObjC» tengono e contano); tutta la parte di rilevamento di `languages/__init__.py` (righe 1-229) ne ha 158.
<!-- /table -->

## Il prodotto

`daodan/core/languages/detect/rules/header.py`, chiamato da `detect_language` per ogni `.h` con testo: la regola Objective-C di prima (la sola regex rimasta, con il suo motivo accanto), poi una visita dell'albero C++ che si ferma al primo nodo di `CPP_DECL` fuori da un blocco `#if` che nomina `__cplusplus`, poi la grammatica C e il confronto degli `ERROR`/`MISSING`, a parità C. Senza grammatica o senza testo la risposta è `c`. **+50 righe di codice nette** (`header.py` 62, `__init__.py` −12, `results/loc.json`, chiave `product`; con commenti e righe vuote `header.py` ha 103 righe e `__init__.py` +2 −24), contro le +106 stimate sopra: il controllo prima del parse è la regex di rumore già del prodotto, il cui ultimo match trova il `/*` mai chiuso. `test_header_probe.py` confronta il prodotto con `R3dx` di `header_routes` sui testi di `PARITY`.

**La visita, non la query.** Una query tree-sitter su un albero la cui radice ha migliaia di figli di errore è quadratica nel loro numero (`{` ×65.536: parse 36 ms, query 10.9 s; Python 3.13.14, Windows; con la visita il rilevamento intero costa 0.12 s): la visita è lineare e dà le stesse risposte (0 differenze da R3dx sulle 4.795 header, come con la query).

**Il tetto.** Un contatore di chiamate di `Parser.parse(read, progress_callback=...)` sarebbe un tetto senza orologio, ma non si usa: con tree-sitter 0.26.0 su Python 3.14.9 (Windows) la callback è chiamata lo stesso numero di volte in tre corse (652 per 5.000 righe `int a;`, 74.720 per 2.730 `/* `) e fermarla ferma il parse; con Python 3.13.14 (Windows) il processo muore con un'access violation alla prima chiamata, anche con la sola `tree-sitter-cpp` (non provato su Linux). Il tetto è sul testo: i primi `MAX_CHARS` caratteri, senza il commento mai chiuso con cui finiscono (la grammatica è quadratica sui `/*` ripetuti). Un C++ il cui primo costrutto sta oltre è letto C. `MAX_CHARS` è `MAX_PARSE_BYTES` (2.000.000): oltre il snapshot non parsa il file, e fino a lì il rilevamento non costa più del parse che l'adattatore farà comunque (tabella sotto). Rispondere C a ogni header oltre il tetto, senza leggerne la testa, perderebbe molto di più (`c_beyond` di `results/product.json`: 20.770 simboli a 16,384 caratteri, 2.944 a 131,072).

Sulle 4.795 header (Modal, `--step product`, `header_report.product`, `results/product.json`), il prodotto contro `R3dx` registrata:

| Tetto (caratteri) | Risposte diverse da R3dx | Simboli persi | C giusti / C++ giusti | Costo ms: mediana / p95 / massimo | Totale s |
| --- | --- | --- | --- | --- | --- |
| nessuno | 0 | 29 | 2132 / 2197 | 0.71 / 7.9 / 14,876 | 34.0 |
| 16,384 | 39 | 717 | 2124 / 2188 | 0.67 / 5.0 / 601 | 9.1 |
| 65,536 | 7 | 382 | 2130 / 2196 | 0.66 / 7.6 / 3,458 | 17.6 |
| 131,072 | 1 | 29 | 2131 / 2197 | 0.65 / 7.7 / 12,433 | 29.6 |
| 524,288 | 0 | 29 | 2132 / 2197 | 0.65 / 7.8 / 14,847 | 33.2 |
| **2,000,000 (prodotto)** | 0 | 29 | 2132 / 2197 | 0.65 / 7.7 / 15,179 | 33.6 |

La più grande delle header è di 909 KB: con il tetto di prodotto la risposta è quella senza tetto. Con 16,384 e 65,536 caratteri i simboli persi stanno in pochi header (`wil/.../result_macros.h`, 322 KB, 353; `gtest-port.h`, 93 KB, 245). Il massimo è `musl/src/locale/gb18030.h` (145 KB, una tabella di numeri): il rilevamento sono due parse da circa 7 s (C++ e C), quello dell'adattatore uno. Il costo di R0 (3.8 s in tutto, mediana 0.19 ms) è di un'altra corsa: si confronta con riserva.

Testi cattivi a 50 e 200 KB (Modal, `--step growth --targets product,parse`, `results/product-growth.json`, ms): il rilevamento con il tetto a 65,536 / 131,072 / 2,000,000, contro il parse dell'adattatore del linguaggio trovato, che il prodotto fa subito dopo.

| Testo | Dimensione | Rilevamento | Parse dell'adattatore |
| --- | --- | --- | --- |
| `class a ` ripetuto | 50 KB | 442 / 444 / 444 | 344 |
| `class a ` ripetuto | 200 KB | 676 / 2,197 / 5,095 | 4,708 |
| stringa mai chiusa | 50 KB | 198 / 195 / 197 | 90 |
| stringa mai chiusa | 200 KB | 261 / 511 / 804 | 376 |
| `"\"\"…` | 200 KB | 69 / 139 / 214 | 314 |
| `{` ripetuto | 50 KB | 74 / 74 / 78 | 2,596 |
| `{` ripetuto | 200 KB | 105 / 209 / 336 | 40,400 |
| `/* ` ripetuto | 200 KB | 6.3 / 7.8 / 9.2 | > 60,000 |
| un `/*` per riga | 200 KB | 6.7 / 7.4 / 8.9 | 47,932 |
| righe vuote | 200 KB | 17 / 26 / 35 | 43 |

Dove il rilevamento costa più del parse è la stringa mai chiusa (circa 2×: due grammatiche contro una); `class a ` ripetuto costa da 1.1× a 1.3× il parse, e `class a ` ×12.000 (96 KB) in locale, su Windows con Python 3.13.14, supera i 2 s di `test_codebase_map_language_cost.py` (da 2.1 a 4.2 s con il tetto da 131,072 in su; 1.2 s con 65,536).

## Limiti

- **Le etichette a mano le ha date un solo annotatore** (un agente, non una persona) leggendo un estratto del testo senza commenti; non c'è un secondo annotatore. L'estratto portava davanti i nodi C++ e Objective-C trovati dal parser e i conteggi di `ERROR` (le feature di R1, R2, R3, non l'esito di R0). Rischio: etichette «indifferente» date perché il parser non trovava nodi. Controlli: nessuna via ad albero concorda con le etichette quanto R0 (colonna «Accordo con le etichette a mano»), e l'estratto non contiene l'esito di R0; e le etichette «indifferente» danno tutte gli stessi simboli letti C o C++, un fatto che nessuna etichetta tocca (tabella «Header di progetti», ultima frase). R0 e l'annotatore leggono però gli stessi indizi di testo (`namespace`, `class`, `template`): il loro accordo non è indipendenza.
- **Gli header fuori dai pool non sono annotati**, e di ogni pool è annotato un campione casuale (per hash e seme): gli errori standard lo suppongono; un campione senza alcun caso dà errore standard 0 (i «0.0 ± 0.0» sono «nessuno visto», non «nessuno»), per questo il confronto tra vie è quello appaiato con R0. Le tabelle «giusti» e «indifferenti» sono stime; le matrici «grezze» di `summary.json` contano gli header non annotati con l'etichetta del progetto e quindi sovrastimano gli errori di ogni via.
- **Le etichette dei C**: gli header dei progetti C valgono C perché lo dice il progetto; i 30 annotati nel pool C sono tutti C e non c'è stata una regola di «indifferente» per loro. «C giusti» è gonfiata a favore di R0.
- **«Indifferente» è un giudizio**, non una misura; i simboli lo controllano ma l'adattatore C++ di Daodan non estrae nulla da molto codice con template, e «stessi simboli» non è «stesso linguaggio».
- **Il corpus** è software libero di Unix, di C e C++ moderni e di Objective-C di Apple/iOS. Le header del Windows SDK e di MSVC, da cui nacquero le differenze citate dalla spec, non sono ridistribuibili e non sono nel corpus né nei JSON (`cppwinrt` e `wil` sono C++ per Windows); la review del team lead le ha lette in locale: stessa risposta di R0 con e senza i ritocchi (riportato da lì, non rifatto qui). Le regole di R0 sono nate sui progetti della pre-mappa di Daodan: non è stato controllato quanto i progetti di questo corpus siano indipendenti da quelli; un insieme tenuto da parte non c'è (i campioni di Linguist hanno pochi `.h`, troppo pochi per distinguere un punto percentuale).
- **La scelta delle varianti di R1 e R2** (`d`/`e`, `g`, `o`, `b`) è fatta guardando questo stesso corpus: le righe dicono quanto vale ciascuna qui, non quanto varrebbe su un altro. Per questo non si è tolto un nodo (per esempio `qualified_identifier`, che confonde molti C con `::` degli `asm`) per salvare una via.
- **La spec e il costo**: un solo `/*` aperto cresce in linea con la grandezza (tabella della crescita); la spec dice che un commento mai chiuso cresce più che al quadrato (14,5 s a 8 KB): la cifra torna, per ordine di grandezza, con la forma dei `/*` ripetuti (qui secondi a 8 KB per le grammatiche; gli host variano di più volte), non con un solo commento aperto, che è lineare.
- **I tempi** sono su Modal con grammatiche scaldate (il primo parse di una grammatica paga la sua preparazione e non è contato); le corse diverse hanno host diversi. Il costo con il tetto (`capcost.json.gz`) è misurato sulle header reali; il costo senza tetto di R1/R2/R3 è dominato da pochi header (quella nominata sotto la tabella «Costo»). I pattern candidati costano di più di quelli di prima (possessivi e `(?<!\\)` non sono gratis): è nella tabella della crescita.
- **Due commit**: `headers.json.gz`, `corpus.json` e i `growth` principali sono del commit `c85c384`; `capcost`, `r0check` e i `growth` dei candidati e delle virgolette del commit `3960973`, con la regola di prima ancora nel prodotto. Il codice di rilevamento (`daodan/core/languages`) è identico tra i due (il test legge le stesse header e la stessa risposta di R0 nelle due corse). I candidati hanno il sostegno di nessuna risposta cambiata su queste header, di una crescita lineare sui 9 testi cattivi misurati e, per `class`, del confronto con il pattern di prima su testi casuali; non di un insieme di header tenuto da parte.
- **Il «circa 110» del brief**: la regola di prima per `.h` sono le righe di codice della tabella «Righe di codice», tutta la parte di rilevamento ne ha di più; nessuna delle due è 110.
- **Non misurato**: R3 senza la grammatica Objective-C a decidere (`R3d` ha le tre), il costo di un secondo parse riusato dall'analisi, Linguist (`heuristics.yml`) come quinta via.

## Comandi

```
# prove pure e del probe (nessuna compilazione; il probe usa le grammatiche della cache di Daodan)
uv run --no-project --with modal --with pytest --with "tree-sitter==0.26.0" --with "tree-sitter-language-pack==1.13.5" --with "sqlglot>=30" --with "PyYAML>=6" python -m pytest benchmarks/header-language -q

# misure, solo su Modal
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal python -m modal run benchmarks/header-language/modal_headers.py --step STEP
#   STEP: warm | prepare | measure | collect | growth | capcost | r0check | product | excerpt | all
#   --projects a,b   solo questi progetti     --kinds a,b / --targets x,y   solo questi testi cattivi / questi bersagli
#   --step product --caps 0,16384   il prodotto con questi tetti (0: nessuno) -> results/product.json.gz, poi header_report.py scrive product.json
#   --step growth --targets product --out benchmarks/header-language/results/product-growth.json   i testi cattivi contro il prodotto
#   --step excerpt --keys FILE   stampa gli estratti da annotare (progetto/percorso, uno per riga)

# punteggio, righe di codice, tabelle del README
python benchmarks/header-language/header_report.py       # results/summary.json (--sample 90,30,25 stampa gli header da annotare)
python benchmarks/header-language/header_loc.py          # results/loc.json
python benchmarks/header-language/header_tables.py --write
```

Parametri: seme `header-language-1` (`header_corpus.SEED`); tetti di byte 4, 8, 16, 32 KB, ognuno `cut` (a fine riga) e `safe` (anche prima di un `/*` aperto); testi cattivi da 2 a 32 KB (50 KB per le righe vuote), un processo per ogni misura, timeout 60 s, 7 forme (`header_routes.BAD_KINDS`).

## File

`header_corpus.py` (progetti, etichette), `header_probe.py` (le tre grammatiche, le feature, R0 e le sue varianti, i simboli), `header_routes.py` (le vie come decisioni sulle feature, statistiche, testi cattivi, `safe_prefix`), `header_report.py` (punteggio), `header_loc.py` (righe), `header_tables.py` (tabelle), `modal_headers.py` e `bad_worker.py` (Modal), `labels.json`, `results/` (`headers.json.gz`, `corpus.json`, `growth*.json`, `capcost.json.gz`, `r0check.json.gz`, `product.json.gz`, `product.json`, `product-growth.json`, `summary.json`, `loc.json`), `test_*.py`.
