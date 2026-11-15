# Codebase Map: linguaggi e motori di inferenza

Aggiornato al 14 novembre 2026.

Lo snapshot analizza ogni linguaggio con un parser e risolve le chiamate con il risolutore lessicale. Per alcuni linguaggi una fonte risolve in background ciò che il lessicale non prova: l'indice di un indicizzatore, letto per intero, oppure un motore di inferenza interrogato posizione per posizione. La copertura si legge per linguaggio: siti con una risposta, per classe, buchi per classe, archi incerti, e lo stato `complete` oppure `lower-bound` (`docs/plugins/codebase-map.md`, sezione Copertura). Spec: `docs/specs/2026-11-08-risoluzione-chiamate-motore.md`.

## Linguaggi supportati

| Linguaggio | Estensioni | Parser dello snapshot | Motore di inferenza | Librerie del progetto |
|---|---|---|---|---|
| Python | `.py` `.pyi` | `ast` della libreria standard | indice di scip-python; su Windows in un container | installate da Daodan dai manifest (`pyproject.toml`, `requirements*.txt`, `uv.lock`), solo wheel |
| TypeScript | `.ts` `.tsx` `.mts` `.cts` | tree-sitter | indice di scip-typescript | installate da Daodan con `npm ci --ignore-scripts` |
| JavaScript | `.js` `.jsx` `.mjs` `.cjs` | tree-sitter | indice di scip-typescript | come TypeScript |
| Vue, Svelte | `.vue` `.svelte` | tree-sitter sui blocchi `<script>`, tokenizer sui blocchi `<style>` (CSS, SCSS, Sass, LESS; Stylus nominato nelle note, non letto) | typescript-language-server | come TypeScript |
| Java | `.java` | tree-sitter | Eclipse JDT LS | lette da Maven e Gradle, scaricate da Daodan |
| Kotlin | `.kt` `.kts` | tree-sitter | Kotlin Analysis API | come Java |
| Rust | `.rs` | tree-sitter | indice di rust-analyzer (`rust-analyzer scip`) | le dipendenze di Cargo, scaricate da Daodan |
| Go | `.go` | tree-sitter | indice di scip-go | i moduli di `go.mod`, scaricati da Daodan |
| C# | `.cs` | tree-sitter | **da fare**: motore da scegliere (server LSP o SCIP) | — |
| SQL, PL/SQL | `.sql` `.ddl` `.dml` `.pks` `.pkb` `.pls` e altri | regex DDL e sqlglot, installato da Daodan con il server MCP | non applicabile: dipendenze fra tabelle, non chiamate | — |
| CSS, SCSS, Sass, LESS, PostCSS | `.css` `.scss` `.sass` `.less` `.pcss` `.postcss` | tokenizer; il Sass indentato è letto come lo SCSS che l'indentazione implica, riga per riga | non applicabile | — |
| Markup | `.html` `.htm` `.xhtml` `.ejs` `.astro` `.hbs` `.mustache` `.liquid` `.twig` `.jsp` `.jspx` `.cshtml` `.razor` `.ftl` `.vm` | tokenizer sui soli blocchi `<style>`: le loro regole sono simboli | non applicabile | — |
| Stylus, Pug | `.styl` `.stylus` `.pug` | nessun lettore nel prodotto: voce a livello di file con il motivo nelle note | non applicabile | — |
| C, C++ | `.c` `.h` (C); `.cc` `.cpp` `.cxx` `.hpp` `.hh` `.hxx` (C++); un `.h` è C++ se il testo ha namespace, classi, template, etichette di accesso o `using namespace` | tree-sitter | **da fare**: scip-clang, piano `docs/plans/2026-11-14-grafo-dall-indice.md`, task 10 | — |

## Motori

| Motore | Versione | Rilasciata | Licenza | Come gira | Spazio su disco |
|---|---|---|---|---|---|
| typescript-language-server | 4.3.3, con TypeScript 5.5.4 | 9 febbraio 2024 (TypeScript 22 luglio 2024) | Apache 2.0 | server LSP su Node.js, versione fissata da multilspy 0.1.1 | 24 MB |
| Eclipse JDT LS | 1.51.0, dentro vscode-java 1.46.0 con il runtime Java 21.0.8 | 2 ottobre 2025 | EPL 2.0 | server LSP su JVM, heap 1 GB | 167 MB |
| Kotlin Analysis API, modalità standalone | KSP `symbol-processing-aa` 2.3.13, risolutore compilato con Kotlin 2.4.21 | 30 ottobre 2026 (compilatore 8 ottobre 2026) | Apache 2.0 | processo JVM di Daodan, heap 1,5 GB | 140 MB |
| rust-analyzer | 2026-11-09 | 9 novembre 2026 | Apache 2.0 e MIT | `rust-analyzer scip` in uno specchio del progetto, senza build script né macro procedurali | 52 MB |
| Rust (cargo, rustc, rust-src), se il PATH non ha i sorgenti di `std` | 1.99.1 | 15 ottobre 2026 | Apache 2.0 e MIT | letto da rust-analyzer, mai usato per compilare | 550 MB |
| scip-go | v0.2.9 | 22 ottobre 2026 | Apache 2.0 | indicizzatore nativo, compilato al primo uso con il Go di Daodan (`go install`, 4 compilatori al massimo), in uno specchio del progetto | — |
| Go, per scip-go e per leggere i moduli | 1.27.3 | 2026 | BSD 3-clause | solo `go list` e `go mod download`, nessuna build; configurazione e telemetria, spenta, nella cartella condivisa | 264 MB |
| scip-typescript | 0.5.2 | 22 ottobre 2026 | Apache 2.0 | indicizzatore su Node, installato con `--ignore-scripts`, in uno specchio del progetto | — |
| scip-python | 0.6.8 | 22 ottobre 2026 | MIT | indicizzatore su Node, installato con `--ignore-scripts`, in uno specchio del progetto; su Windows non parte (`new RegExp(path.sep)`), quindi gira in un container `python:3.13-slim` senza rete, con Docker o Podman | — |
| Node.js, per gli indicizzatori su npm | 22.23.4 | 20 ottobre 2026 | MIT | scaricato da nodejs.org e verificato con lo `SHASUMS256` della release; npm e Node tengono le cache nella cartella condivisa | — |
| Coursier, per le librerie JVM | 2.1.24 | 9 gennaio 2025 | Apache 2.0 | risolve le coordinate Maven, non esegue build | 43 MB |
| multilspy, trasporto LSP | 0.1.1 | 13 ottobre 2026 | MIT | libreria Python nell'ambiente dello stage | 12 MB |
| tree-sitter, parser dello snapshot | 0.26.0, grammatiche `tree-sitter-language-pack` 1.13.5 | 30 giugno 2026 (grammatiche 27 luglio 2026) | MIT | libreria Python, installata dal server MCP; il bundle delle grammatiche lo mette Daodan nella sua cache, verificato con lo sha256 fissato; senza grammatica il file è una lacuna dichiarata dello snapshot | — |
| sqlglot, parser SQL dello snapshot | 30.30.0 | 6 novembre 2026 | MIT | libreria Python, installata dal server MCP: riconosce le CTE ricorsive e quotate | — |

Tutto si installa al primo uso in `%LOCALAPPDATA%\Daodan` (`$XDG_CACHE_HOME/daodan` fuori da Windows), una volta per la macchina, con il checksum verificato. Le librerie dei progetti finiscono nella stessa cartella: `coursier/` per Java e Kotlin, `npm/` per TypeScript e JavaScript. Nessun motore compila, esegue la build o scrive nel progetto. Dopo l'installazione il passaggio non apre connessioni di rete.

## Copertura misurata

Le misure per progetto, con la copertura per linguaggio, i buchi per classe e la verifica a mano, stanno in `benchmarks/inference-audit/README.md`.

Vue e Svelte sono verificati su una fixture, non su un progetto pubblico.

## Limiti noti

- **JavaScript dinamico.** Su express le chiamate senza risposta sono metodi di `req`, `res` e `app`, oggetti che Express costruisce a runtime: nessuna analisi statica li tipizza.
- **Librerie calcolate dagli script Gradle.** Daodan legge le dipendenze scritte nei file di build senza eseguirli; quelle che uno script calcola (`listOf("reflect").forEach { kotlin(it) }`) restano invisibili.
- **Python senza tipi.** Le chiamate su parametri non annotati (`store.get_file`) restano senza risposta.
- **Kotlin standalone.** La modalità standalone dell'Analysis API non è stabile: la versione è fissata e un aggiornamento può richiedere adattamenti.
- **Rust.** Le macro procedurali e i build script restano spenti: ciò che generano non ha tipi, quindi le chiamate a funzioni generate restano senza risposta. Le dipendenze di Cargo si scaricano nella cartella condivisa; senza la toolchain completa Daodan scarica 550 MB di Rust.
- **Go.** Una chiamata su un valore di funzione o su un'interfaccia anonima non ha una dichiarazione a cui arrivare.
- **C e C++.** Ogni file si legge con le macro dei file della sua unità di traduzione, cioè quelli che include e quelli che lo includono: una macro definita come decorazione (`#define local static`) o come involucro di prototipo (`OF((args))`) si cancella prima di leggere. Un file che tree-sitter non legge intero non ha fatti semantici, solo i simboli: restano 12 file C su 66 di zlib e 1 file su 4 di tinyxml2, per un'istruzione spezzata fra i rami di un `#if` o una parola del compilatore in un ramo spento. Un nome che il file non dichiara si risolve sull'unica definizione non `static` fra le dichiarazioni delle intestazioni di progetto incluse; con due definizioni, o in C++ con una funzione omonima in un namespace visibile, resta senza risposta. Un `#include <x.h>` non è mai un'intestazione di progetto.
- **Da fare.** C#: scegliere il motore misurando server LSP e SCIP. C e C++: l'indice di scip-clang.
- **Da fare: passo dinamico.** Ciò che il motore non prova perché si decide in esecuzione (JavaScript dinamico, Python senza tipi, valori di funzione in Go) si osserva eseguendo i test del progetto in un container. JavaScript è il primo linguaggio. Oggi nessun motore esegue codice del progetto. Spec: `docs/specs/2026-11-12-passo-dinamico.md`; piano: `docs/plans/2026-11-12-passo-dinamico.md`.
