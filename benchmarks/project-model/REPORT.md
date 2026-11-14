# Pre-mappa del progetto: cosa danno gli strumenti esistenti

**Data:** 14 novembre 2026. **Corpus:** 122 fixture (js 20, py 21, jvm 16, sys 25, mix 30, real 10), tutte valide con `python score.py --check all`. **Numeri:** ogni numero viene da `results/*.json` ripunteggiato con `score.py` di questa cartella. "Trovate" vuol dire voce abbinata con ogni campo dato giusto; fra parentesi le voci abbinate, comprese quelle con un campo sbagliato; "+n" le voci in più. **In corso:** le celle segnate così arrivano in un secondo passaggio.

## 1. Verdetto

1. Nessuno strumento dà la pre-mappa da solo: il più largo copre quattro faccette su nove, e nessuno dice se serve un container (`needs`: 0 su 122 fixture).
2. **Linguaggi ed esclusi** sono risolti: go-enry o i dati di Linguist danno 305-308 linguaggi su 313 e 460-463 file su 486. Lavorano offline, senza eseguire nulla, in meno di 0,2 s per fixture.
3. **Dipendenze dirette con versione:** Renovate in estrazione locale ne trova 673 su 861 (741 abbinate); Trivy 357, con poche voci in più (+69). Syft e osv-scanner danno anche le transitive senza distinguerle (+1.827 e +1.789).
4. **Versioni di toolchain dichiarate:** Renovate 122 su 381; mise, proto e Railpack fra 22 e 25. Su 381 dichiarazioni, 225 non le riporta nessuno strumento.
5. **Unità del build system:** senza eseguire codice del progetto si arriva a 137 unità su 447. Con i comandi di modello eseguiti nel container (Gradle, .NET, CMake, Meson, Swift, Mix) si sale a 236. Il `modules.py` di Daodan da solo ne abbina 266 e ne trova esatte 197, più di qualunque strumento esterno.
6. **Cartelle sorgente, source set, task di compilazione, alias, tsconfig** vengono solo dai comandi nativi, un ecosistema alla volta: 132 cartelle sorgente su 489, 155 fatti di configurazione su 828.
7. **Framework e servizi** sono deboli ovunque: Specfy 29 framework su 330, il registro di Daodan 45 servizi su 123.
8. **Combinazione consigliata,** ognuno nel suo pezzo:
   - go-enry per linguaggi ed esclusi;
   - Renovate (AGPL-3.0, eseguito come processo separato) per toolchain e dipendenze dichiarate;
   - Trivy per le versioni bloccate dai lockfile;
   - sull'host i comandi di modello di Go, Cargo, npm/pnpm, uv e `tsc --showConfig`;
   - nel container Gradle, Maven, .NET, CMake e Swift.
9. **L'adattatore sottile di Daodan deve ancora:**
   - unire le fonti per unità;
   - leggere le versioni dove nessuno le legge (release Java nel pom, matrici di CI);
   - dichiarare buchi per framework e servizi;
   - decidere `needs`.
10. **Finding su Daodan:**
    - la lettura di base scarica in silenzio le grammatiche tree-sitter da GitHub;
    - si ferma sui link simbolici di python-semver;
    - impiega fino a 334 s su un repository vero.

### La ricerca alla prova

| Affermazione di [2026-11-14-project-model-detection.md](../../docs/research/2026-11-14-project-model-detection.md) | Esito misurato |
| --- | --- |
| Nessuno strumento dà da solo la pre-mappa | Confermata |
| Chi legge i file non dà sorgenti, source set, task | Confermata: `units.source_roots` e `units.config` vengono solo da comandi nativi |
| Syft dà nomi, versioni e relazioni per tutti gli ecosistemi | Vero per i pacchetti. Come fonte di dipendenze dirette però è sotto Renovate (360 contro 673), non separa le transitive (+1.827) e non dà unità |
| Un solo lettore delle versioni dichiarate: mise | Smentita: mise 25 su 381, Renovate 122 |
| La versione Java si legge solo dal modello nativo nel container | Confermata: sul jvm i migliori sono Gradle (9 su 30) e Maven (5), entrambi nel container |
| `go list` per ogni `go.mod` | Confermata: `go list` dalla radice salta i moduli annidati (caso chi) |
| Framework e servizi: Specfy stack-analyser | Debole: 29 framework su 330; il registro di Daodan dà più servizi (45) del CLI di Specfy (22) |

## 2. Per faccetta

| Faccetta | Attese | Miglior strumento: trovate (abbinate) +in più | Seguono | Errori tipici |
| --- | --- | --- | --- | --- |
| Linguaggi presenti | 313 | dati di Linguist 308 +291 | Linguist 307, go-enry 305 +118 | le voci in più sono formati di dati che il corpus non elenca: JSON 46, TOML 36, YAML 23 (Linguist) |
| Linguaggio dei file difficili | 486 | dati di Linguist 463 (469) | go-enry 460, Linguist 450 | `.sql` per dialetto (T-SQL letto come SQL); Magika confonde TSX con TypeScript e Svelte con testo |
| Esclusi | 463 | go-enry 382 (402) +392 | Linguist 382 (402) +398; Magika 224 | `next-env.d.ts` detto vendored invece che generated; in più README, LICENSE, lockfile, `.github/` |
| Unità | 447 | `modules.py` di Daodan 197 (266) | ScanCode 100 (105), Specfy 94 (95), Alizer 90 (220) | nome della radice Gradle (`:` contro `rootProject.name`); tipi mancati: progetti Python senza pyproject, `source-tree`, Helm, buf |
| Dipendenze fra unità | 199 | `modules.py` 70 +31 | .NET SDK 10 47 (solo eShop), CMake 8 | nessuno strumento esterno su più ecosistemi |
| Cartelle sorgente | 489 | Gradle 31 | Maven 28, Cargo 28, Go 19, CMake 15 | solo comandi nativi; js, py e real: nessuno |
| Configurazione per indicizzatori | 828 | `tsc --showConfig` 35 (45) | Cargo 35 (44), CMake 26, Gradle 21 (42) | alias di Vite mancanti; target Cargo con altro nome |
| Workspace | 32 | `modules.py` 15 (19) | Netlify build-info 6 (7), .NET 6 | lo strumento del workspace (npm contro turbo) |
| Membri del workspace | 114 | `modules.py` 64 +486 | .NET SDK 10 34, Netlify 26, Vercel 25 | `modules.py` mette fra i membri cartelle sorgente e moduli fuori dal profilo |
| Toolchain | 381 | Renovate 122 (133) +35 | Railpack 25 (81), mise 25 (27), Go 23, proto 22 (37) | `go1.23.4` contro `1.23.4`; versione presa dal Dockerfile invece che dal workflow |
| Dipendenze | 861 | Renovate 673 (741) +368 | `modules.py` 508 (573), npm 365, Syft 360 (409), Specfy 359, Trivy 357 (395) +69, component-detection 288 (334) +154 | file di dichiarazione (catalogo pnpm, proprietà Maven); intervallo senza prefisso `jsr:`; versione dal BOM come se fosse bloccata |
| Framework | 330 | Specfy 29 (33) | Alizer 28 (42) +65, Vercel 15 | test e librerie (JUnit, xUnit, Jackson, gRPC) e build tool (Vite) mai riportati; nessun framework sul jvm |
| Servizi | 123 | registro di Daodan 45 +26 | stack-analyser di Daodan 27 +66, Specfy 22 | servizi presenti solo in compose o nel codice; il wrapper `stack_analyser.py` aggiunge un solo servizio vero (Redis in mix-php-laravel) e 47 in più |
| Bisogno di container | 122 | nessuno | — | nessuno strumento lo dice |

### Combinazioni, voce per voce

Per ogni fixture conta la voce trovata dal migliore dell'insieme.

| Insieme | Linguaggi | File | Esclusi | Unità | Dip. fra unità | Sorgenti | Config | Workspace | Membri | Toolchain | Dipendenze | Framework | Servizi |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Senza codice del progetto: go-enry, Renovate, Trivy, Specfy, registro di Daodan, Go, Cargo, npm, pnpm, yarn, bun, uv, `tsc`, Maven, Composer, pub, `.gitmodules` | 305/313 | 460/486 | 385/463 | 137/447 | 12/199 | 73/489 | 94/828 | 12/32 | 41/114 | 128/381 | 716/861 | 29/330 | 46/123 |
| Lo stesso più il container (Gradle, .NET, CMake, Meson, Swift, Mix, Bazel, pip) | 305 | 460 | 385 | 236 | 96 | 132 | 155 | 25 | 100 | 153 | 729 | 29 | 46 |
| Tutti gli strumenti, Daodan compreso | 312 | 477 | 389 | 277 | 106 | 132 | 155 | 26 | 107 | 156 | 740 | 35 | 46 |

### Strumento per faccetta su tutto il corpus

"—" = faccetta non data. I comandi nativi girano solo sulle fixture del loro ecosistema; il totale di colonna resta quello di tutto il corpus.

| Strumento | Ling. (313) | File (486) | Esclusi (463) | Unità (447) | Dip. unità (199) | Sorgenti (489) | Config (828) | WS (32) | Membri (114) | Toolchain (381) | Dipendenze (861) | Framework (330) | Servizi (123) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Linguist 9.7.0 | 307 +289 | 450 (456) | 382 (402) +398 | — | — | — | — | — | — | — | — | — | — |
| dati di Linguist 9.7.0 | 308 +291 | 463 (469) | 142 (161) +345 | — | — | — | — | — | — | — | — | — | — |
| go-enry 2.9.6 | 305 +118 | 460 (466) | 382 (402) +392 | — | — | — | — | — | — | — | — | — | — |
| scc 4.1.0 | 289 +276 | 442 (469) | 30 (33) +39 | — | — | — | — | — | — | — | — | — | — |
| tokei 15.0.0 | 292 +239 | 438 (462) | — | — | — | — | — | — | — | — | — | — | — |
| Magika 1.0.3 | 275 +404 | 405 (471) | 224 (239) +7 | — | — | — | — | — | — | — | — | — | — |
| tabella di Daodan | 190 +35 | 323 (366) | 19 +35 | — | — | — | — | — | — | — | — | — | — |
| Syft 1.57.1 | — | — | — | — | — | — | — | — | — | — | 360 (409) +1.827 | — | — |
| Trivy 0.76.2 | — | — | — | 41 | — | — | — | — | — | — | 357 (395) +69 | — | — |
| osv-scanner 2.7.1 | — | — | — | — | — | — | — | — | — | — | 309 (436) +1.789 | — | — |
| cdxgen 13.7.0 | — | — | — | 70 (79) +13 | — | — | — | — | — | — | 346 (458) +154 | — | — |
| ScanCode 32.5.0 | — | — | — | 100 (105) | — | — | — | — | — | — | 321 (377) +77 | — | — |
| component-detection 9.1.0 | — | — | — | — | — | — | — | — | — | — | 288 (334) +154 | — | — |
| Renovate 44.239.1 | — | — | — | — | — | — | — | — | — | 122 (133) +35 | 673 (741) +368 | — | — |
| mise 2026.11.8 | — | — | — | — | — | — | — | — | — | 25 (27) | — | — | — |
| proto 0.64.0 | — | — | — | — | — | — | — | — | — | 22 (37) | — | — | — |
| Railpack 0.43.0 | — | — | — | — | — | — | — | — | — | 25 (81) +50 | — | 7 | 0 |
| Specfy stack-analyser 1.27.6 | — | — | — | 94 (95) | — | — | — | — | — | — | 359 (372) +35 | 29 (33) +3 | 22 +2 |
| Alizer 1.10.0 | 165 +85 | — | — | 90 (220) +5 | — | — | — | — | — | — | — | 28 (42) +65 | 0 |
| Vercel fs-detectors 7.12.1 | — | — | — | — | — | — | — | 4 (6) +1 | 25 | — | — | 15 (16) | 0 |
| Netlify build-info 11.3.1 | — | — | — | 25 (26) | — | — | — | 6 (7) | 26 | — | — | 10 (11) +1 | 0 |
| registro di Daodan | — | — | — | — | — | — | — | — | — | — | — | — | 45 +26 |
| stack-analyser via Daodan | — | — | — | — | — | — | — | — | — | — | — | — | 27 +66 |
| `modules.py` di Daodan | — | — | — | 197 (266) +4 | 70 +31 | — | — | 15 (19) +7 | 64 +486 | — | 508 (573) +332 | — | — |
| npm (Node 22.23.4) | — | — | — | 52 (53) | 1 | — | 1 (2) | 2 (5) | 2 | 18 | 365 (374) +3 | — | — |
| Go 1.27.3 | — | — | — | 19 | 2 | 19 | 19 (22) | 1 | 3 | 23 | 51 (53) | — | — |
| Cargo 1.99.1 | — | — | — | 25 | 5 | 28 +1 | 35 (44) | 1 | 3 | 6 (7) +2 | 0 (31) | — | — |
| uv 0.11.28 | — | — | — | 5 +3 | 1 | — | — | 2 | 3 | 3 | 25 | — | — |
| `tsc --showConfig` 6.0.3 | — | — | — | 34 (35) | — | — | 35 (45) | — | — | — | — | — | — |
| Maven 3.10.0 | — | — | — | 19 | 1 | 28 | 19 (24) | 3 (4) +5 | 12 +2 | 8 | 25 (45) | — | — |
| Gradle 9.9.1 | — | — | — | 24 | 6 | 31 +4 | 21 (42) | 4 +11 | 9 +3 | 9 (10) +1 | 29 (45) +87 | — | — |
| CMake 3.28 | — | — | — | 15 | 8 | 15 +1 | 26 (32) | — | — | 5 (6) | — | — | — |
| .NET SDK 10.0.302 | — | — | — | 31 +3 | 47 | — | 0 | 5 | 34 | — | 0 (5) | — | — |

## 3. Repository veri

| Repository | Unità attese (tipi) | Chi le elenca tutte | Migliore | Chi perde tipi interi |
| --- | --- | --- | --- | --- |
| real-svc-eshop | 29 (28 .NET, 1 npm) | `modules.py` | `modules.py` 29; .NET SDK 10 28 con 3 workspace su 3 | cdxgen e npm vedono 1 unità su 29 |
| real-svc-petclinic-microservices | 9 Maven | cdxgen, Maven, Trivy | Maven 9 con il workspace | Alizer: 8 abbinate, nomi diversi |
| real-svc-voting-app | 4 (npm, .NET, Python, source-tree) | Alizer | Alizer 4 | `modules.py` perde il Python senza pyproject e il source-tree |
| real-svc-otel-demo | 27 in 11 tipi | nessuno | `modules.py` 16 (20) | Alizer perde CMake, Bundler, Mix, Cargo; Specfy vede 6 |
| real-svc-robot-shop | 12 (npm, Maven, Composer, Python, 4 source-tree, Helm) | nessuno | Alizer 10 (11) | tutti perdono il chart Helm; `modules.py` 4 |
| real-app-hoppscotch | 24 (15 npm, 8 Cargo, 1 Go) | nessuno | Specfy 23; `modules.py` 22 (24) | pnpm e Netlify perdono i crate Cargo e il modulo Go |
| real-app-kotlinconf | 13 (10 Gradle, 1 Xcode, 2 Swift) | nessuno | Gradle con JDK 21: 10 | nessuno vede il target Xcode; Gradle con JDK 17 fallisce |
| real-app-full-stack-fastapi | 5 (3 npm, 2 Python) | nessuno | `modules.py` 4 | Specfy perde i due Python |
| real-app-jhipster-sample | 3 (npm, Angular, Maven) nella stessa radice | nessuno | Alizer 2 | Alizer perde Maven; Maven e cdxgen vedono solo Maven |
| real-app-memos | 3 (Go, npm, buf) | nessuno | `modules.py` 2 | il modulo buf non lo vede nessuno |

Con più build system affiancati:

- ogni comando nativo vede solo il suo ecosistema;
- gli scanner su più ecosistemi (Alizer, Specfy, ScanCode, Trivy) perdono i tipi che non conoscono: Helm, buf, Xcode, Python senza pyproject, codice senza build;
- nessuno strumento ha elencato tutte le unità di un repository con più di due tipi;
- ScanCode ha uscita su 2 repository veri su 10: gli altri 8 sono stati saltati per il costo (**non misurato**). Il registro di Daodan ha uscita su 9 su 10: si ferma su mix-real-python-semver per il crash dei link simbolici. Sui quattro repository più grandi il registro ha una sola esecuzione cronometrata, a 1 cpu e 2 GB, senza traccia né prova offline.

## 4. I nove casi misurati in questo progetto

| Caso | Fixture | Chi lo riporta | Note |
| --- | --- | --- | --- |
| chi: moduli Go annidati in `_examples/*` | mix-real-chi, sys-go-nested | Trivy, ScanCode, `modules.py`; Alizer uno dei due | `go list` dalla radice li salta; cdxgen vede solo la radice; Syft non dà unità |
| tududi: un solo `package.json` radice | mix-real-tududi | Alizer, cdxgen, `modules.py`, npm, `tsc`, ScanCode, Specfy | |
| App React: alias `@/` in `tsconfig.app.json` | js-vite-react-ts | solo `tsc --showConfig`, ma a metà | dà `@/*` dal tsconfig, perde `@` di `vite.config.ts` |
| Rust: modulo di test condiviso fra crate di test | sys-rust-shared-test-module | Cargo dà le cartelle `src` e `tests` e l'edizione | il modulo condiviso non lo riporta nessuno |
| Kotlin: più task di compilazione | jvm-kotlin-source-sets | solo Gradle, nel container | esegue codice del progetto |
| Android Gradle | jvm-android-app-lib | solo Gradle, nel container: le tre unità | codice del progetto eseguito, 54 tentativi di rete, 11,1 s, 2.902 MB |
| Sottomoduli Git assenti dall'archivio | sys-git-submodule-absent, mix-edge-submodules | solo la lettura di `.gitmodules` | 2 su 2 esclusi e dipendenze dopo il nuovo punteggio |
| Versioni da `uv.lock` | py-uv-src-layout, py-uv-workspace, mix-real-python-semver | uv, osv-scanner, Renovate, Syft, Trivy: 4/4, 2/2, 14/14 | cdxgen 3/4 e 11/14; pip 0/14 |
| App Vue: fogli globali caricati da `main.ts` | — | non è un fatto della pre-mappa | resta al grafo |

## 5. Per difetto e con i comandi di sola lettura

Il corpus gira con le opzioni di sola lettura (`command` in ogni `results/<tool>.json`). Ogni strumento è stato provato anche per difetto, su sei fixture.

| Strumento | Per difetto (6 fixture) | Con le opzioni usate | Offline, seconda esecuzione |
| --- | --- | --- | --- |
| Syft | 7 tentativi di rete per fixture (controllo di aggiornamento) | 0 tentativi; codice del progetto mai eseguito | uguale su 122 |
| Trivy | 14-21 tentativi (database) | 0 | uguale su 121 |
| osv-scanner | 5-9 tentativi (osv.dev) | 0 | uguale su 119 |
| cdxgen | esegue i gestori di pacchetti su 1 fixture su 6 | `CDXGEN_SECURE_MODE`, nessun comando: 0 | uguale su 114, diverso su 1 |
| ScanCode | 0 | 0 | uguale su 114 |
| component-detection 9.1.0 | lancia `ant -version`, `mvn --version`, `pip --version`, `python --version`, `go version`, `cargo` per vedere quali strumenti ci sono; 0 tentativi di rete | `CD_MAVEN_DISABLE_CLI`, `DisableGoCliScan`, `DisableRustCliScan`, `PipReportOverrideBehavior=SourceCodeScan`: 0 tentativi su 122; codice del progetto `unknown` su 122 | uguale su 110, stessi pacchetti su 10, diverso su 2 |
| Renovate, mise, proto, uv, rustup, corepack | — | tracciati su 6 fixture: nessun codice del progetto; sulle altre 115 `unknown` | mise, Renovate, rustup uguali su 6; proto diverso su 6 su 6 |
| Magika | — | 5 fixture con tentativi di rete | uguale su 122; picco 7,0 GB |
| Comandi nativi | — | npm, pnpm, Cargo, Go, uv, `tsc`: nessun codice del progetto. Gradle, .NET, CMake, Meson, Swift, Mix, Bundler: sì | tabella sotto |

Offline dopo una prima esecuzione con rete (HOME calda) e da zero (HOME vuota). Fonte: nota del runner nativo; campo `facts.offline_cold` in `results/native_<tool>.json`.

| Comando | HOME calda: uguale / diverso / non misurato | HOME vuota: uguale su misurate |
| --- | --- | --- |
| Go | 10 / 0 / 4 | 9/10 |
| Cargo | 8 / 2 / 3 | 1/10 |
| npm | 27 / 0 / 9 | 27/27 |
| pnpm | 2 / 0 / 2 | 0/2 |
| uv | 18 / 0 / 2 | 18/18 |
| pip | 1 / 21 / 5 | 1/22 |
| Maven | 5 / 0 / 4 | 0/5 |
| Gradle | 11 / 0 / 3 | 1/11 |
| CMake | 6 / 0 / 3 | 6/6 |
| .NET | 1 / 0 / 4 | 0/1 |
| `tsc` | non misurato | 11/11 |
| `.gitmodules` | non misurato | 2/2 |

Windows, dalle pagine delle release:

- scc ha un binario (7,2 MB);
- Magika ha la wheel `win_amd64` (13 MB);
- go-enry e tokei non hanno binari recenti: vanno compilati;
- Linguist è una gemma con estensioni native, senza binario;
- i dati di Linguist sono quattro file letti da Python.

Per gli altri: **non misurato**.

### Progetti che non dichiarano nulla

Cinque fixture senza build tool (js-node-scripts, js-static-html, py-notebooks, py-pep723-scripts, py-undeclared-scripts), con 16 moduli esca piantati. Dal campo `honesty` dei risultati.

| Strumento | Moduli importati e non dichiarati riportati | Errori | Nomi inventati | Esche scattate | Rete |
| --- | --- | --- | --- | --- | --- |
| deptry 0.25.1 | 6 su 6 Python (PIL, cv2, numpy, sklearn, yaml; seaborn) | due moduli locali presi per esterni (`helpers`, `nbproj`); le tre dipendenze dei blocchi PEP 723 dette non dichiarate (non legge PEP 723) | 0 | 0 | 0 |
| dependency-cruiser 18.7.2, senza configurazione | 2 su 2 JavaScript (`ms`, `vue`) | nessuno; non vede Python, come atteso | 0 | 0 | 0 |
| uv 0.13.8, `uv tree --script` | non è il suo compito | sui blocchi PEP 723 dà come `resolved` le versioni di oggi (requests 2.34.2, rich 15.0.0, pandas 2.2.3), che nessun file fissa | 0 | 0 | 60 tentativi su py-pep723-scripts |

### Due strade per la versione di toolchain

Dalla nota del runner nativo, misurata nel container.

| Caso (fixture) | Dal file dichiarato | Dal messaggio d'errore dello strumento |
| --- | --- | --- |
| .NET SDK (real-svc-eshop) | sì: `global.json` 10.0.302; con quella versione 31/31 unità | sì: "Requested SDK version: 10.0.302" |
| JVM del demone Gradle (real-app-kotlinconf) | no, senza codice proprio: `jvmToolchain(21)` è negli script | sì: "requires at least JVM runtime version 21"; con JDK 21 10/10 unità |
| Elixir (real-svc-otel-demo) | no, senza eseguire `mix.exs` | sì: "supports only Elixir ~> 1.20" |
| .NET `.slnx` (real-svc-otel-demo) | solo leggendo il Dockerfile (`sdk:10.0.403`) | no: l'errore non nomina una versione |
| Go, Rust, CMake, Python (modo "più nuovo") | sì | sì |
| Maven, release 99 | solo con `help:effective-pom` | no: nessun errore, la release è ignorata |

## 6. Daodan

| Fatto | Misura | Causa |
| --- | --- | --- |
| `modules.py` contro gli strumenti | Unità: 197 esatte (266 abbinate) su 447, contro 137 di tutti gli strumenti senza codice del progetto e 236 con il container. Dipendenze fra unità 70 su 199. Membri del workspace 64, ma +486 in più. Dipendenze 508 (573) | i 30 lettori di manifest coprono più tipi di ogni scanner; i suoi errori principali sono il nome della radice Gradle e i membri in più |
| Download nascosto delle grammatiche | `snapshot.py write --no-engine --no-index` tenta la rete su 90 fixture su 122 (6-7 tentativi), verso `github.com` e `release-assets.githubusercontent.com` | `tree-sitter-language-pack` 1.13.5 scarica il pacchetto di grammatiche al primo `get_parser()` (`languages/_treesitter.py:124-126`, chiamato da `snapshot.py:316-320`), in `~/.cache/tree-sitter-language-pack/`, fuori dalla cache di Daodan. La versione non è fissata (`requirements.txt:31-33`, `>=1.0`). Offline il download fallisce e il file passa al lettore a espressioni regolari, più debole (`_treesitter.py:127-132`). Le 32 fixture senza tentativi non hanno file di un linguaggio tree-sitter |
| Arresto sui link simbolici | mix-real-python-semver: `sqlite3.IntegrityError: UNIQUE constraint failed: files.path` | `snapshot_store.py:429`, `put_file` chiamato da `snapshot.py:873`: due percorsi per lo stesso file |
| Tempi sui repository grandi | 333,9 s su kotlinconf, 208,8 s su eShop, 104,4 s su tududi, 90,6 s su memos; mediana sul corpus 0,93 s | non misurata per passo |
| Tabella dei linguaggi | 190 linguaggi su 313 e 323 file su 486, contro 305-308 e 460-463 di go-enry e Linguist | la tabella dei suffissi non ha euristiche |
| Wrapper `stack_analyser.py` | Sui servizi, contro il registro: 48 servizi che il registro non ha, di cui 1 vero (Redis in mix-php-laravel) e 47 in più; il registro da solo ne trova 45 | il CLI di Specfy rilegge le stesse regole già nel registro: tenerlo aggiunge un servizio e 47 errori |

Servizi del registro, letti voce per voce dal punteggio (`score.py daodan_registry all --json`):

| Voci | Quante | Quali |
| --- | --- | --- |
| Trovate | 45 su 123 | |
| Perse | 78 | PostgreSQL 7, SMTP 6, Redis 3; SQLite, H2, Prometheus, Grafana, Cloud Firestore e Firebase Hosting 2 ciascuno: servizi dichiarati in compose, nei manifest di deploy o usati nel codice, non in un pacchetto |
| In più: errori | circa 6 | Zoom 2, Ghost e Discord dal nome di una variabile d'ambiente; Caddy da un esempio nella documentazione |
| In più: strumenti, non servizi | circa 9 | Playwright 3, Cypress 2, Travis CI, Renovate, Postman, GitHub Pages |
| In più: veri, con un nome più generico dell'atteso | circa 11 | OpenTelemetry 3, AWS 2, Firebase, GCP, Google Compute, Kubernetes, OpenAI, Hugging Face, Prometheus |

La divisione delle 26 voci in più nelle tre righe è una lettura a mano dei nomi, non un conteggio del punteggio.

### `BuildTarget` di BSP come modello delle unità

Campi letti dallo spec al tag `v2.2.0-M3` del repository. Il file `version` dice 2.2.0; su Maven Central l'ultimo `bsp4j` è `2.2.0-M4.TEST`.

| Fatto delle 346 unità di partenza del corpus | Campo di BSP | Ci sta |
| --- | --- | --- |
| nome, radice, dipendenze fra unità | `displayName`, `baseDirectory`, `dependencies` | sì |
| cartelle sorgente, file generati | `buildTarget/sources` (`roots`, `generated`) | sì |
| linguaggi | `languageIds` | sì |
| tipo dell'unità (`npm-package`, `gradle-project`, …) | `tags` dice solo library, application, test | no |
| manifest | — | no |
| `entry_files` (197 usi), `packages` (55), `tsconfig` (37), `paths` (21) | — (solo Rust ha `crateRootUrl`) | no |
| `source_sets` (51), `compile_tasks` (32) | un target per source set | sì, cambiando la granularità |
| `build_tags` (37), `include_dirs` (27), `edition` (20) | feature Cargo, `CppOptionsItem` (defines, copts), `CargoBuildTarget.edition` | sì per Rust e C/C++, no per i tag Go |
| workspace e membri | solo il workspace Rust | no |
| toolchain chiesta | `JvmBuildTarget.javaVersion`, `PythonBuildTarget.version`, `CppBuildTarget.version` | in parte: niente Node, Go, gestori di pacchetti, né file di dichiarazione |
| dipendenze esterne | `DependencyModule` con una versione; scope solo Maven | in parte: niente intervallo dichiarato né file |

Gli autori hanno usato 80 chiavi diverse di `config`, circa 50 una volta sola: il resto è specifico di ogni build system.

## 7. Costi Modal

Da `modal billing report --for today --resolution h`, cifre per app riportate dai runner.

| Gruppo | Speso letto (USD) | Tetto (USD) | Note |
| --- | --- | --- | --- |
| lang | 0,3216 | 0,25 + 0,15 per i repository veri | sopra il primo tetto: una scrittura del volume per fixture (circa 12 s l'una), un repository Git nuovo per fixture |
| sbom | 0,3755 | 0,30 + 0,40 per i repository veri + 0,06 per gli strumenti aggiunti | primo passaggio 0,3197, appena sopra il suo tetto, con i repository veri dentro (il tetto di 0,40 non è stato usato a parte); strumenti aggiunti (component-detection, deptry, dependency-cruiser, uv, correzione di cdxgen) 0,0558 |
| native | 0,5182, ultima ora aperta | 0,40 + 1,00 | 0,389 corpus, 0,129 repository veri, compresa una chiamata a build-server-for-gradle bloccata e annullata |
| versions | 0,406, ore recenti fatturate in ritardo | 0,30 + 0,10 + 0,25 | la riesecuzione del corpus ha superato il suo tetto (circa 0,17 contro 0,10): quattro container invece di uno |
| frameworks | 0,5905 (0,5872 dell'app più 0,0033 di sei app di sonda) | 0,25 + 0,25 per i repository veri | sopra il primo tetto: due giri completi con una scrittura del volume per fixture; il passaggio sui repository veri è costato 0,078 |
| **Totale** | **2,212** | 3,71 | quattro gruppi su cinque sopra il primo tetto: lang, sbom (di 0,02), versions (riesecuzione), frameworks |

## 8. Cosa non è stato misurato

- ScanCode sugli 8 repository veri saltati per il costo.
- Il registro di Daodan sui quattro repository più grandi: una sola esecuzione cronometrata, a 1 cpu e 2 GB, senza traccia né prova offline; i suoi tempi non si confrontano con le altre esecuzioni.
- Binario per Windows di component-detection.
- Codice eseguito dai lettori di versioni: tracciato su 6 fixture, `unknown` sulle altre 115.
- Binari per Windows di Syft, Trivy, Renovate, mise e dei comandi nativi.
- La lettura offline di base di Daodan: dedotta dal codice, non eseguita.
- Le voci in più di linguaggi ed esclusi: il corpus non dice se i formati di dati e i documenti contano. Le tabelle le riportano senza correggerle.
