# Codebase Map: linguaggi e motori di inferenza

Aggiornato al 9 novembre 2026.

Lo snapshot analizza ogni linguaggio con un parser e risolve le chiamate con il risolutore lessicale. Per alcuni linguaggi un motore di inferenza risolve in background ciò che il lessicale non prova. La copertura è sempre **risolte su risolvibili**: le chiamate esterne, cioè builtin riconosciuti e destinazioni provate esterne dal motore, sono fuori dal denominatore. Spec e misure complete: `docs/specs/2026-11-08-risoluzione-chiamate-motore.md`.

## Linguaggi supportati

| Linguaggio | Estensioni | Parser dello snapshot | Motore di inferenza | Librerie del progetto |
|---|---|---|---|---|
| Python | `.py` `.pyi` | `ast` della libreria standard | Jedi | l'ambiente del progetto (`.venv`, `venv`, `VIRTUAL_ENV`) |
| TypeScript | `.ts` `.tsx` `.mts` `.cts` | tree-sitter | typescript-language-server | `node_modules` del progetto, altrimenti installate da Daodan |
| JavaScript | `.js` `.jsx` `.mjs` `.cjs` | tree-sitter | typescript-language-server | come TypeScript |
| Vue, Svelte | `.vue` `.svelte` | tree-sitter sui soli blocchi `<script>` | typescript-language-server | come TypeScript |
| Java | `.java` | tree-sitter | Eclipse JDT LS | lette da Maven e Gradle, scaricate da Daodan |
| Kotlin | `.kt` `.kts` | tree-sitter | Kotlin Analysis API | come Java |
| Rust | `.rs` | tree-sitter | rust-analyzer | le dipendenze di Cargo, scaricate da Daodan |
| Go | `.go` | tree-sitter | gopls | i moduli di `go.mod`, scaricati da Daodan |
| C# | `.cs` | tree-sitter | **da fare**: motore da scegliere (server LSP o SCIP) | — |
| SQL, PL/SQL | `.sql` `.ddl` `.dml` `.pks` `.pkb` `.pls` e altri | regex DDL e sqlglot, installato da Daodan con il server MCP | non applicabile: dipendenze fra tabelle, non chiamate | — |
| CSS, SCSS, LESS | `.css` `.scss` `.less` | tokenizer | non applicabile | — |
| C, C++ | `.c` `.h` `.cpp` `.hpp` e altri | **da fare**: adattatore tree-sitter (dichiarazioni, chiamate, `#include`) | **da fare**: clangd | — |

## Motori

| Motore | Versione | Rilasciata | Licenza | Come gira | Spazio su disco |
|---|---|---|---|---|---|
| Jedi | 0.20.1 | 12 ottobre 2026 | MIT | libreria Python, in un ambiente `uv` dello stage | 15 MB |
| typescript-language-server | 4.3.3, con TypeScript 5.5.4 | 9 febbraio 2024 (TypeScript 22 luglio 2024) | Apache 2.0 | server LSP su Node.js, versione fissata da multilspy 0.1.1 | 24 MB |
| Eclipse JDT LS | 1.51.0, dentro vscode-java 1.46.0 con il runtime Java 21.0.8 | 2 ottobre 2025 | EPL 2.0 | server LSP su JVM, heap 1 GB | 167 MB |
| Kotlin Analysis API, modalità standalone | KSP `symbol-processing-aa` 2.3.13, risolutore compilato con Kotlin 2.4.21 | 30 ottobre 2026 (compilatore 8 ottobre 2026) | Apache 2.0 | processo JVM di Daodan, heap 1,5 GB | 140 MB |
| rust-analyzer | 2026-11-09 | 9 novembre 2026 | Apache 2.0 e MIT | server LSP nativo, senza compilare né eseguire build script | 52 MB |
| Rust (cargo, rustc, rust-src), se il PATH non ha i sorgenti di `std` | 1.99.1 | 15 ottobre 2026 | Apache 2.0 e MIT | letto da rust-analyzer, mai usato per compilare | 550 MB |
| gopls | 0.24.0 | 2026 | BSD 3-clause | server LSP nativo, compilato al primo uso | 43 MB |
| Go, per gopls e per leggere i moduli | 1.27.3 | 2026 | BSD 3-clause | solo `go list` e `go mod download`, nessuna build | 264 MB |
| Coursier, per le librerie JVM | 2.1.24 | 9 gennaio 2025 | Apache 2.0 | risolve le coordinate Maven, non esegue build | 43 MB |
| multilspy, trasporto LSP | 0.1.1 | 13 ottobre 2026 | MIT | libreria Python nell'ambiente dello stage | 12 MB |
| tree-sitter, parser dello snapshot | 0.26.0, grammatiche `tree-sitter-language-pack` 1.13.5 | 30 giugno 2026 (grammatiche 27 luglio 2026) | MIT | libreria Python, installata dal server MCP | — |
| sqlglot, parser SQL dello snapshot | 30.30.0 | 6 novembre 2026 | MIT | libreria Python, installata dal server MCP: riconosce le CTE ricorsive e quotate | — |

Tutto si installa al primo uso in `%LOCALAPPDATA%\Daodan` (`$XDG_CACHE_HOME/daodan` fuori da Windows), una volta per la macchina, con il checksum verificato. Le librerie dei progetti finiscono nella stessa cartella: `coursier/` per Java e Kotlin, `npm/` per TypeScript e JavaScript. Nessun motore compila, esegue la build o scrive nel progetto. Dopo l'installazione il passaggio non apre connessioni di rete.

## Copertura misurata

| Linguaggio | Progetto | Solo lessicale | Con il motore | Durata del passaggio | RAM di picco |
|---|---|---|---|---|---|
| Python | Daodan `42a63a9ac` | 33,8% | 81,5% (7.399 su 9.083) | 12 min 35 s | 0,3 GB su un campione di 400 posizioni |
| Python | requests `3c7baaa` | 25,9% | 92,0% (643 su 699) | 2 min 19 s | 0,4 GB |
| TypeScript | ky `3541888` | 12,9% | 90,9% (3.911 su 4.302) | 45 s, 170 s con l'installazione delle librerie | 1,3 GB |
| JavaScript | express `43fca52` | 7,2% | 13,4% (385 su 2.867) | 24 s | 0,7 GB |
| Java | javapoet `b9017a9` | 7,3% | 99,7% (2.864 su 2.874) | 107 s | 1,1 GB |
| Kotlin | klaxon `1173bdc` | 25,1% | 89,6% (812 su 906) | 45 s | 0,6 GB |
| Rust | semver `280ebcb` | 15,7% | 98,5% (447 su 454) | 22 s | 1,0 GB |
| Rust | serde_json `8c535a2` | 21,3% | 92,3% (1.641 su 1.778) | 27 s | 0,9 GB |
| Go | chi `c64ed7d` | 11,1% | 95,9% (1.014 su 1.057) | 18 s | 0,5 GB |
| Go | cobra `adbc881` | 24,8% | 98,7% (1.626 su 1.648) | 7 s | 0,4 GB |

Vue e Svelte sono verificati su una fixture, non su un progetto pubblico.

## Limiti noti

- **JavaScript dinamico.** Su express le chiamate senza risposta sono metodi di `req`, `res` e `app`, oggetti che Express costruisce a runtime: nessuna analisi statica li tipizza.
- **Librerie calcolate dagli script Gradle.** Daodan legge le dipendenze scritte nei file di build senza eseguirli; quelle che uno script calcola (`listOf("reflect").forEach { kotlin(it) }`) restano invisibili.
- **Python senza tipi.** Le chiamate su parametri non annotati (`store.get_file`) restano senza risposta.
- **Kotlin standalone.** La modalità standalone dell'Analysis API non è stabile: la versione è fissata e un aggiornamento può richiedere adattamenti.
- **Rust.** Le macro procedurali e i build script restano spenti: ciò che generano non ha tipi, quindi le chiamate a funzioni generate restano senza risposta. Le dipendenze di Cargo si scaricano nella cartella condivisa; senza la toolchain completa Daodan scarica 550 MB di Rust.
- **Go.** Una chiamata su un valore di funzione o su un'interfaccia anonima non ha una dichiarazione a cui arrivare.
- **Da fare.** C#: scegliere il motore misurando server LSP e SCIP. C e C++: prima l'adattatore tree-sitter, poi clangd.
- **Da fare, progetto a sé: copertura runtime per JavaScript.** Ciò che lo statico non risolve (i metodi di `req`, `res` e `app` su express; `create`, `findOne` e `send` su valori senza tipo in tududi) si vede solo osservando il programma in esecuzione. Oggi nessun motore esegue codice del progetto.
