# Codebase Map: linguaggi e strumenti

Aggiornato al 16 novembre 2026.

Lo snapshot analizza ogni linguaggio con un parser e risolve le chiamate con il risolutore lessicale. La pipeline (`docs/plugins/codebase-map.md`, sezione Pipeline) risolve poi ciò che il lessicale non prova con l'analyzer del linguaggio, l'indice di un indicizzatore letto per intero oppure un motore interrogato posizione per posizione, e aggiunge le chiamate che i test del progetto eseguono sotto il registratore dell'osservatore. La copertura si legge per linguaggio: siti con una risposta, per classe, buchi per classe, archi incerti, e lo stato `complete` oppure `lower-bound` (`docs/plugins/codebase-map.md`, sezione Copertura). Spec: `docs/specs/2026-11-08-risoluzione-chiamate-motore.md`.

## Linguaggi supportati

| Linguaggio | Estensioni | Parser dello snapshot | Analyzer | Librerie del progetto | Osservatore |
|---|---|---|---|---|---|
| Python | `.py` `.pyi` | `ast` della libreria standard | indice di scip-python; su Windows in un container | installate da Daodan dai manifest (`pyproject.toml`, `requirements*.txt`, `uv.lock`), solo wheel | registro di Daodan su `sys.monitoring`, sotto pytest o unittest |
| TypeScript | `.ts` `.tsx` `.mts` `.cts` | tree-sitter | indice di scip-typescript, in un container | ripristinate nel container dal gestore del lockfile (npm, pnpm, Yarn), con i suoi script di installazione | registro di Daodan, un plugin di Babel, sotto lo script `test` e i runner che il progetto dichiara |
| JavaScript | `.js` `.jsx` `.mjs` `.cjs` | tree-sitter | indice di scip-typescript | come TypeScript | come TypeScript |
| Vue, Svelte | `.vue` `.svelte` | tree-sitter sui blocchi `<script>`, tokenizer sui blocchi `<style>` (CSS, SCSS, Sass, LESS; Stylus nominato nelle note, non letto) | typescript-language-server | come TypeScript | nessuno |
| Java | `.java` | tree-sitter | indice di scip-java, una build Maven o Gradle per cartella della pre-mappa, in un container, sul JDK che la build dichiara | risolte da Maven e Gradle nel container, dai registri JVM e dagli host che il progetto dichiara | agente di Daodan su ASM, sotto `mvn test` o i task `Test` di Gradle |
| Kotlin | `.kt` `.kts` | tree-sitter | indice di scip-java con il plugin Kotlin, come Java | come Java | come Java |
| Rust | `.rs` | tree-sitter | indice di rust-analyzer (`rust-analyzer scip`) | le dipendenze di Cargo, scaricate da Daodan | Callgrind, sugli eseguibili di `cargo test` |
| Go | `.go` | tree-sitter | indice di scip-go | i moduli di `go.mod`, scaricati da Daodan | registro di Daodan, una riscrittura dei sorgenti nella copia, sotto `go test` |
| C# | `.cs` | tree-sitter | indice di scip-dotnet, in un container, sull'SDK di `global.json` | ripristinate nel container da `dotnet restore` | nessuno |
| C, C++ | `.c` `.h` (C); `.cc` `.cpp` `.cxx` `.hpp` `.hh` `.hxx` (C++); un `.h` è C++ se il testo ha namespace, classi, template, etichette di accesso o `using namespace` | tree-sitter | indice di scip-clang, in un container, sul database di compilazione che dà la build dell'unità: CMake, Meson, Make, Bazel o cgo | ripristinate nella preparazione quando la radice dichiara vcpkg o Conan; mai scaricata una dipendenza che CMake prende da un sito fuori dai registri | Callgrind, sui test che la build CMake dichiara, lanciati da CTest |
| SQL, PL/SQL | `.sql` `.ddl` `.dml` `.pks` `.pkb` `.pls` e altri | regex DDL e sqlglot, installato da Daodan con il server MCP | non applicabile: dipendenze fra tabelle, non chiamate | — | non applicabile |
| CSS, SCSS, Sass, LESS, PostCSS | `.css` `.scss` `.sass` `.less` `.pcss` `.postcss` | tokenizer; il Sass indentato è letto come lo SCSS che l'indentazione implica, riga per riga | grafo dei fogli di stile (`indexers/css.py`): i nomi che regole e variabili dichiarano e ogni punto che li usa, con i motori fissati sotto | — | non applicabile |
| Markup | `.html` `.htm` `.xhtml` `.ejs` `.erb` `.astro` `.hbs` `.handlebars` `.mustache` `.liquid` `.twig` `.j2` `.jinja` `.njk` `.jsp` `.jspx` `.cshtml` `.razor` `.ftl` `.vm` | tokenizer sui soli blocchi `<style>`: le loro regole sono simboli | grafo dei fogli di stile per HTML, EJS e Astro; gli altri sono dichiarati senza lettore | — | non applicabile |
| Stylus, Pug | `.styl` `.stylus` `.pug` `.jade` | nessun lettore: voce a livello di file con il motivo nelle note | Stylus nel grafo dei fogli di stile; Pug nessuno | — | non applicabile |

Come gira la build di ogni analyzer, e il JDK di Java e Kotlin: `docs/plugins/codebase-map.md`, sezione Pipeline.

## Strumenti

| Strumento | Versione | Rilasciata | Licenza | Come gira | Spazio su disco |
|---|---|---|---|---|---|
| typescript-language-server | 4.3.3, con TypeScript 5.5.4 | 9 febbraio 2024 (TypeScript 22 luglio 2024) | Apache 2.0 | server LSP su Node.js, versione fissata da multilspy 0.1.1 | 24 MB |
| scip-java | 0.14.2 | 12 novembre 2026 | Apache 2.0 | nel container `eclipse-temurin:17-jdk-noble`, con il classpath di Maven Central verificato con lo sha256 | — |
| scip-clang | v0.4.1, LLVM 21 | 22 ottobre 2026 | Apache 2.0 | nel container `buildpack-deps:noble` (glibc 2.39), sul database di compilazione della build | — |
| scip-dotnet | 0.2.16 | 21 ottobre 2026 | Apache 2.0 | il pacchetto NuGet, fissato per sha256, nel container sull'SDK che il progetto dichiara | — |
| rust-analyzer | 2026-11-09 | 9 novembre 2026 | Apache 2.0 e MIT | `rust-analyzer scip` in uno specchio del progetto, senza build script né macro procedurali | 52 MB |
| Rust (cargo, rustc, rust-src), se il PATH non ha i sorgenti di `std` | 1.99.1 | 15 ottobre 2026 | Apache 2.0 e MIT | letto da rust-analyzer, mai usato per compilare | 550 MB |
| scip-go | v0.2.9 | 22 ottobre 2026 | Apache 2.0 | indicizzatore nativo, compilato al primo uso con il Go di Daodan (`go install`, 4 compilatori al massimo), in uno specchio del progetto | — |
| Go, per scip-go e per leggere i moduli | 1.27.3 | 2026 | BSD 3-clause | sull'host solo `go list` e `go mod download`, nessuna build; configurazione e telemetria, spenta, nella cartella condivisa | 264 MB |
| scip-typescript | 0.5.2 | 22 ottobre 2026 | Apache 2.0 | nel container, sul Node di Daodan, installato da npm senza i suoi script di installazione | — |
| scip-python | 0.6.8 | 22 ottobre 2026 | MIT | indicizzatore su Node, installato con `--ignore-scripts`, in uno specchio del progetto; su Windows non parte (`new RegExp(path.sep)`), quindi gira in un container `python:3.13-slim` senza rete | — |
| Node.js, sull'host | 22.23.4 | 20 ottobre 2026 | MIT | per scip-python e per i motori dei fogli di stile; scaricato da nodejs.org e verificato con lo `SHASUMS256` della release; npm e Node tengono le cache nella cartella condivisa | — |
| Motori dei fogli di stile | `sass-parser` 0.5.6, Less 4.9.1, Stylus 0.64.0, `@vue/compiler-sfc` 3.5.45, Svelte 5.57.3, `@astrojs/compiler` 4.0.0, TypeScript 5.9.3 | — | MIT; Less e TypeScript Apache 2.0 | sull'host, installati una volta dal lockfile di `indexers/css_engines/`; il Tailwind del progetto lo caricano, con la sua configurazione, dalla `node_modules` del progetto, se c'è | — |
| CMake | 3.28.3, quella di Ubuntu 24.04 | — | BSD 3-clause | configura le unità CMake nel container; un minimo dichiarato più alto lo installa mise | — |
| Meson e Ninja | 1.12.1 e 1.13.2 | — | Apache 2.0 | i wheel di PyPI, portati nel container: `meson setup --wrap-mode nodownload`, nella pre-mappa e nell'analisi | — |
| Bear | 3.1.3 | — | GPL-3.0-or-later | i pacchetti di Ubuntu 24.04, con le librerie che l'immagine non ha, fissati per sha256 e installati con dpkg nell'esecuzione, attorno a `make` e a `go build` | — |
| Bazel | 9.3.1 | — | Apache 2.0 | `bazel query` nella pre-mappa, `bazel aquery` nella preparazione con gli host di Bazel; il Bazel che il progetto dichiara lo installa mise | — |
| Registri di Daodan | — | — | MIT | Python su `sys.monitoring`; JavaScript e TypeScript, un plugin di Babel stampato con `@babel/core` 7.29.7 (MIT); Go, una riscrittura dei sorgenti nella copia; JVM, un agente costruito per Java 8 su ASM 9.11.1 (BSD 3-clause, il jar di Maven Central fissato per sha256) | — |
| Valgrind, Callgrind | 3.22.0 | — | GPL-2.0-or-later | il pacchetto di Ubuntu 24.04 dal pool dell'archivio, con Launchpad come seconda fonte, fissato per sha256, aperto nella preparazione e mai installato nel sistema; pyelftools 0.33 (dominio pubblico) dà le colonne dalle tabelle DWARF | — |
| mise | v2026.11.8 | — | MIT | installa nella preparazione le toolchain che il progetto dichiara, alla versione dichiarata | — |
| Android SDK command-line tools di Google | 15859902 | — | Android Software Development Kit License Agreement | da dl.google.com, fissati per sha256; sdkmanager installa nella preparazione i soli pacchetti che la build dichiara | — |
| Toolchain della preparazione (`preparation.NEEDS`) | Node 24.22.3, Go 1.27.3, .NET SDK 10.0.404, Rust 1.99.1, uv 0.11.28, Conan 2.34.0, Poetry 2.1.3, vcpkg-tool 2026-10-29, Arm GNU Toolchain 15.2.rel1 | — | MIT (Node, .NET, Conan, Poetry, vcpkg-tool); BSD 3-clause (Go); Apache 2.0 e MIT (Rust, uv); GPL-3.0-or-later (Arm GNU Toolchain) | portate nel container dove un comando le chiede (`needs`) | — |
| Kiri | 0.2.0 | 10 novembre 2026 | Apache 2.0 | il motore di container su Windows quando l'utente non ha Docker né Podman, in una distribuzione WSL 2 di Daodan | — |
| Immagini dei container | `eclipse-temurin:17-jdk-noble`, `buildpack-deps:noble`, `python:3.13-slim` (3.13.18), `python:3.13-alpine` | — | quelle dei pacchetti della distribuzione; il JDK Temurin GPL-2.0 con Classpath Exception | fissate per digest: Java e Kotlin; C e C++, C#, TypeScript e la pre-mappa; scip-python su Windows; il proxy dei registri | — |
| multilspy, trasporto LSP | 0.1.1 | 13 ottobre 2026 | MIT | libreria Python nell'ambiente dello stage | 12 MB |
| tree-sitter, parser dello snapshot | 0.26.0, grammatiche `tree-sitter-language-pack` 1.13.5 | 30 giugno 2026 (grammatiche 27 luglio 2026) | MIT | libreria Python, installata dal server MCP; il bundle delle grammatiche lo mette Daodan nella sua cache, verificato con lo sha256 fissato; senza grammatica il file è una lacuna dichiarata dello snapshot | — |
| sqlglot, parser SQL dello snapshot | 30.30.0 | 6 novembre 2026 | MIT | libreria Python, installata dal server MCP: riconosce le CTE ricorsive e quotate | — |

Le fonti della pre-mappa (Renovate, go-enry e i modelli dei build system), con versioni e licenze, sono in `plugins/codebase-map/skills/map/references/premap.md`.

Tutto ciò che Daodan scarica va al primo uso in `%LOCALAPPDATA%\Daodan` (`$XDG_CACHE_HOME/daodan` fuori da Windows), una volta per la macchina, con il checksum verificato. Nessuno strumento scrive nel progetto; dove gira il codice del progetto: `docs/plugins/codebase-map.md`, sezione Pipeline.

`sdkmanager --licenses` accetta l'Android Software Development Kit License Agreement per chi esegue Daodan, come fa ogni CI. Daodan non distribuisce né replica l'SDK: gli strumenti a riga di comando li scarica da Google nella cartella condivisa, i pacchetti dichiarati li scarica sdkmanager da Google nella preparazione (sezioni 2.1-2.2, 2.4, 3.1-3.4, 3.8 e 6.1 dell'accordo).

## Copertura misurata

Le misure per progetto, con la copertura per linguaggio, i buchi per classe e la verifica a mano, stanno in `benchmarks/inference-audit/README.md`; quelle del passo dinamico in `benchmarks/call-provenance/README.md`.

Vue e Svelte sono verificati su una fixture, non su un progetto pubblico.

## Limiti noti

- **JavaScript dinamico.** Su express le chiamate senza risposta sono metodi di `req`, `res` e `app`, oggetti che Express costruisce a runtime: nessuna analisi statica li tipizza.
- **Python senza tipi.** Le chiamate su parametri non annotati (`store.get_file`) restano senza risposta.
- **Rust.** Le macro procedurali e i build script restano spenti: ciò che generano non ha tipi, quindi le chiamate a funzioni generate restano senza risposta. Le dipendenze di Cargo si scaricano nella cartella condivisa; senza la toolchain completa Daodan scarica 550 MB di Rust.
- **Go.** Una chiamata su un valore di funzione o su un'interfaccia anonima non ha una dichiarazione a cui arrivare.
- **Java e Kotlin sotto il 17.** scip-java non indicizza su un JDK più vecchio: `jdk_unsupported` (`docs/plugins/codebase-map.md`, sezione Pipeline).
- **C e C++.** Ogni file si legge con le macro dei file della sua unità di traduzione, cioè quelli che include e quelli che lo includono: una macro definita come decorazione (`#define local static`) o come involucro di prototipo (`OF((args))`) si cancella prima di leggere. Un file che tree-sitter non legge intero non ha fatti semantici, solo i simboli: restano 12 file C su 66 di zlib e 1 file su 4 di tinyxml2, per un'istruzione spezzata fra i rami di un `#if` o una parola del compilatore in un ramo spento. Un nome che il file non dichiara si risolve sull'unica definizione non `static` fra le dichiarazioni delle intestazioni di progetto incluse; con due definizioni, o in C++ con una funzione omonima in un namespace visibile, resta senza risposta. Un `#include <x.h>` non è mai un'intestazione di progetto. Una build MSBuild non dà un database di compilazione: le sue unità restano senza indice.
- **Passo dinamico.** Chiude un buco solo dove un test esegue la chiamata: un progetto senza test dichiarati, o con test che non partono, non aggiunge nulla, e la lacuna lo dice. C#, Vue e Svelte non hanno osservatore. Valgrind non parte sotto gVisor (le Sandbox di Modal): Rust, C e C++ lì sono `recorder_failed`, con la causa.
