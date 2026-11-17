# Giro della pipeline sul corpus

File: `2026-11-17-vue-svelte.json`.

Codice di `2026-11-17-vue-svelte.json`: commit `f992db5609c7`, albero `338d872be487`, diverso dal commit in 971 percorsi (`benchmarks/project-model/fixtures/_done-js`, `benchmarks/project-model/fixtures/_done-jvm`, `benchmarks/project-model/fixtures/_done-mix`, …).

## Casi

- Eseguiti: 3; falliti: 3.
- Secondi: 1.839,0 in totale; mediana 157,8.

### Casi più lenti

| Caso | Secondi |
| --- | --- |
| real-app-hoppscotch | 1.532,4 |
| js-sveltekit | 157,8 |
| js-vue-pnpm | 148,8 |

### Casi falliti

| Caso | Errore |
| --- | --- |
| js-vue-pnpm | stack: FileNotFoundError: [Errno 2] No such file or directory: '/daodan/map/data/service-registry.json' |
| js-sveltekit | stack: FileNotFoundError: [Errno 2] No such file or directory: '/daodan/map/data/service-registry.json' |
| real-app-hoppscotch | stack: FileNotFoundError: [Errno 2] No such file or directory: '/daodan/map/data/service-registry.json' |

## Linguaggi

| Linguaggio | Casi | fresh | failed | unavailable | File indicizzati / nello snapshot | Siti | Risposti | Buchi | Quota risposta |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| go | 1 | 1 | 0 | 0 | 7 / 7 | 571 | 571 | 0 | 100,0 % |
| javascript | 2 | 1 | 1 | 0 | 1 / 1 | 2 | 2 | 0 | 100,0 % |
| rust | 1 | 1 | 0 | 0 | 99 / 105 | 5.715 | 5.026 | 689 | 87,9 % |
| stylesheet | 3 | 3 | 0 | 0 | 1.614 / 1.616 | 16.678 | 16.208 | 470 | 97,2 % |
| svelte | 2 | 1 | 1 | 0 | 2 / 2 | 5 | 4 | 1 | 80,0 % |
| typescript | 3 | 2 | 1 | 0 | 6 / 6 | 10 | 9 | 1 | 90,0 % |
| vue | 2 | 1 | 1 | 0 | 3 / 3 | 5 | 3 | 2 | 60,0 % |

### Risposte per tipo e buchi per classe

| Linguaggio | Risposte | Buchi |
| --- | --- | --- |
| go | external 238, project-callable 35, project-value 298 | — |
| javascript | external 2 | — |
| rust | external 3.038, lexical 13, project-callable 714, project-value 1.261 | no-document 250, no-occurrence 1, undefined-project-symbol 17, under `#[cfg(all(desktop, not(feature = "portable")))]`, false in the configuration rust-analyzer reads (every feature on, Linux in Daodan's container, the build scripts run): nothing is written 7, under `#[cfg(mobile)]`, false in the co |
| stylesheet | external 15.627, namespace 15, project-value 566 | call 7, no-font-face 4, no-rule 361, parameter 1, property 23, template 16, undeclared 2, unresolved-import 26, variable 30 |
| svelte | external 2, project-callable 1, project-value 1 | undefined-project-symbol 1 |
| typescript | external 9 | no declaration of *.vue modules: the import is not typed 1 |
| vue | external 1, project-value 2 | dangling-local 1, undefined-project-symbol 1 |

### Stati diversi da fresh

| Linguaggio | Stato | Casi | Motivo |
| --- | --- | --- | --- |
| javascript | failed | 1 | scip-typescript wrote no index (exit code 0): ............... + /work (16s 426ms) done /daodan/out/index.scip DAODAN_PEAK - |
| svelte | failed | 1 | scip-typescript wrote no index (exit code 0): ............... + /work (16s 426ms) done /daodan/out/index.scip DAODAN_PEAK - |
| typescript | failed | 1 | scip-typescript wrote no index (exit code 0): ............... + /work (16s 426ms) done /daodan/out/index.scip DAODAN_PEAK - |
| vue | failed | 1 | scip-typescript wrote no index (exit code 0): ............... + /work (16s 426ms) done /daodan/out/index.scip DAODAN_PEAK - |

### Linguaggi fresh con file fuori dall'indice

| Caso | Linguaggio | Mancanti / nello snapshot | Motivi |
| --- | --- | --- | --- |
| real-app-hoppscotch | rust | 6 / 105 | the `mod` item that loads it is under `#[cfg(mobile)]`, false in the configuration rust-analyzer reads (every feature on, Linux in Daodan's container, the build scripts run) (2); the `mod` item that loads it is under `#[cfg(target_os = "macos")]`, false in the configuration rust-analyzer reads (ever |
| real-app-hoppscotch | stylesheet | 2 / 1.602 | template language: no reader (2) |

### Linguaggi senza analizzatore

| Linguaggio | Casi | File |
| --- | --- | --- |
| sql | 1 | 22 |

## Pre-mappa

| Faccetta | Casi che la danno | Casi che non la danno | Trovate | Attese | In più | Sbagliate |
| --- | --- | --- | --- | --- | --- | --- |
| languages | 3 | 0 | 24 | 24 | 21 | 0 |
| languages.files | 0 | 3 | 0 | 0 | 0 | 0 |
| excluded | 3 | 0 | 115 | 121 | 63 | 0 |
| units | 3 | 0 | 26 | 26 | 0 | 0 |
| units.depends_on | 3 | 0 | 15 | 15 | 0 | 0 |
| units.source_roots | 1 | 2 | 9 | 24 | 1 | 0 |
| units.config | 3 | 0 | 28 | 72 | 0 | 8 |
| workspace | 3 | 0 | 1 | 1 | 0 | 0 |
| workspace.members | 1 | 2 | 14 | 14 | 0 | 0 |
| toolchains | 3 | 0 | 13 | 35 | 23 | 0 |
| dependencies | 0 | 3 | 0 | 0 | 0 | 0 |
| frameworks | 0 | 3 | 0 | 0 | 0 | 0 |
| services | 0 | 3 | 0 | 0 | 0 | 0 |
| needs | 0 | 3 | 0 | 0 | 0 | 0 |

## Gap

| Passo | Tipo | Numero | Esempi |
| --- | --- | --- | --- |
| scan | file_withheld | 28 | real-app-hoppscotch: .npmrc: .npmrc is a file Daodan never reads (its name matches .npmrc) and only the .env files Git tracks reach the copy: the copy leaves it out, and what reads it there finds nothing<br>real-app-hoppscotch: packages/hoppscotch-common/src/helpers/aichat/__tests__/secret-references.spec.ts: packages/hoppscotch-common/src/helpers/aichat/__tests__/secret-references.spec.ts is a file Daodan never reads (its name speaks of secrets and it holds a generated value) and only the .env files G<br>real-app-hoppscotch: packages/hoppscotch-common/src/helpers/aichat/secret-references.ts: packages/hoppscotch-common/src/helpers/aichat/secret-references.ts is a file Daodan never reads (its name speaks of secrets and it holds a generated value) and only the .env files Git tracks reach the copy: the  |
| scan | not_executed | 14 | real-app-hoppscotch: package.json: install scripts are not run (scripts.preinstall, scripts.prepare): what they generate is unknown<br>real-app-hoppscotch: packages/codemirror-lang-graphql/package.json: install scripts are not run (scripts.prepare): what they generate is unknown<br>real-app-hoppscotch: packages/hoppscotch-backend/package.json: install scripts are not run (scripts.postinstall): what they generate is unknown |
| scan | model_failed | 12 | js-sveltekit: tsconfig.json: tsc --showConfig: error TS5083: Cannot read file '/work/.svelte-kit/tsconfig.json'.<br>real-app-hoppscotch: packages/codemirror-lang-graphql: npm query: npm error Cannot read properties of undefined (reading 'target') npm error A complete log of this run can be found in: /daodan/state/npm-cache/_logs/2026-11-17T08_45_57_386Z-debug-0.log; npm error Cannot read properties of undefined (<br>real-app-hoppscotch: packages/hoppscotch-agent: npm query: npm error Cannot read properties of undefined (reading 'target') npm error A complete log of this run can be found in: /daodan/state/npm-cache/_logs/2026-11-17T08_45_58_758Z-debug-0.log; npm error Cannot read properties of undefined (reading |
| scan | toolchain_unavailable | 10 | js-sveltekit: package.json: node >=18.13: a range, not a version to install<br>js-sveltekit: package.json: node >=18.13: a range, not a version to install<br>real-app-hoppscotch: packages/hoppscotch-selfhost-web/Dockerfile: node lts: a range, not a version to install |
| scan | mask_partial | 7 | real-app-hoppscotch: Daodan does not mask the values of .env.example:ENABLE_SUBPATH_BASED_ACCESS, .env.example:TRUST_PROXY, a boolean word or a number of five digits at most: what the run keeps may hold them<br>real-app-hoppscotch: Daodan does not mask the values of .env.example:ENABLE_SUBPATH_BASED_ACCESS, .env.example:TRUST_PROXY, a boolean word or a number of five digits at most: what the run keeps may hold them<br>real-app-hoppscotch: Daodan does not mask the values of .env.example:ENABLE_SUBPATH_BASED_ACCESS, .env.example:TRUST_PROXY, a boolean word or a number of five digits at most: what the run keeps may hold them |
| scan | no_analyzer | 4 | real-app-hoppscotch: 4 Dockerfile files and no analyzer lists the language: their code is in no graph<br>real-app-hoppscotch: 4 Nix files and no analyzer lists the language: their code is in no graph<br>real-app-hoppscotch: 2 PLpgSQL files and no analyzer lists the language: their code is in no graph |
| scan | model_partial | 2 | real-app-hoppscotch: packages/hoppscotch-desktop/plugin-workspace/tauri-plugin-appload/examples/tauri-app/src-tauri: registries unknown: cargo metadata --locked: : cannot create the lock file /work/packages/hoppscotch-desktop/plugin-workspace/tauri-plugin-appload/examples/tauri-app/src-tauri/Cargo.l<br>real-app-hoppscotch: .: npm query answered without the lockfile: no workspace member before an install |
| scan | ownership_ambiguous | 2 | real-app-hoppscotch: packages/hoppscotch-desktop/plugin-workspace/tauri-plugin-appload: Directory scope cannot distinguish build ownership: curiouscorrelation-plugin-appload, tauri-plugin-appload<br>real-app-hoppscotch: packages/hoppscotch-desktop/plugin-workspace/tauri-plugin-relay: Directory scope cannot distinguish build ownership: curiouscorrelation-plugin-relay, tauri-plugin-relay |
| scan | restore_failed | 1 | real-app-hoppscotch: packages/hoppscotch-desktop/plugin-workspace/tauri-plugin-appload/examples/tauri-app: its packages are not installed: no workspace above names this folder |
| analyze | build_script_failed | 28 | real-app-hoppscotch: packages/hoppscotch-agent/src-tauri: the build script of atk-sys 0.18.2 failed: The system library `atk` required by crate `atk-sys` was not found: rust-analyzer reads atk-sys as with build scripts off: without the cfgs they set and the files they write<br>real-app-hoppscotch: packages/hoppscotch-agent/src-tauri: the build script of gdk-sys 0.18.2 failed: The system library `gdk-3.0` required by crate `gdk-sys` was not found: rust-analyzer reads gdk-sys as with build scripts off: without the cfgs they set and the files they write<br>real-app-hoppscotch: packages/hoppscotch-agent/src-tauri: the build script of soup3-sys 0.5.0 failed: The system library `libsoup-3.0` required by crate `soup3-sys` was not found: rust-analyzer reads soup3-sys as with build scripts off: without the cfgs they set and the files they write |
| analyze | file_withheld | 12 | real-app-hoppscotch: .npmrc: .npmrc is a file Daodan never reads (its name matches .npmrc) and only the .env files Git tracks reach the copy: the copy leaves it out, and what reads it there finds nothing<br>real-app-hoppscotch: packages/hoppscotch-common/src/helpers/aichat/__tests__/secret-references.spec.ts: packages/hoppscotch-common/src/helpers/aichat/__tests__/secret-references.spec.ts is a file Daodan never reads (its name speaks of secrets and it holds a generated value) and only the .env files G<br>real-app-hoppscotch: packages/hoppscotch-common/src/helpers/aichat/secret-references.ts: packages/hoppscotch-common/src/helpers/aichat/secret-references.ts is a file Daodan never reads (its name speaks of secrets and it holds a generated value) and only the .env files Git tracks reach the copy: the  |
| analyze | alias_ambiguous | 7 | real-app-hoppscotch: `@components/*` has other targets in packages/hoppscotch-common, packages/hoppscotch-desktop, packages/hoppscotch-sh-admin: one program holds one mapping, so an import through it resolves to the first target that holds the file<br>real-app-hoppscotch: `@composables/*` has other targets in packages/hoppscotch-common, packages/hoppscotch-desktop, packages/hoppscotch-sh-admin: one program holds one mapping, so an import through it resolves to the first target that holds the file<br>real-app-hoppscotch: `@functional/*` has other targets in packages/hoppscotch-common, packages/hoppscotch-desktop, packages/hoppscotch-sh-admin: one program holds one mapping, so an import through it resolves to the first target that holds the file |
| analyze | mask_partial | 3 | real-app-hoppscotch: Daodan does not mask the values of .env.example:ENABLE_SUBPATH_BASED_ACCESS, .env.example:TRUST_PROXY, a boolean word or a number of five digits at most: what the run keeps may hold them<br>real-app-hoppscotch: Daodan does not mask the values of .env.example:ENABLE_SUBPATH_BASED_ACCESS, .env.example:TRUST_PROXY, a boolean word or a number of five digits at most: what the run keeps may hold them<br>real-app-hoppscotch: Daodan does not mask the values of .env.example:ENABLE_SUBPATH_BASED_ACCESS, .env.example:TRUST_PROXY, a boolean word or a number of five digits at most: what the run keeps may hold them |
| analyze | component_import_unresolved | 1 | real-app-hoppscotch: 356 imports of a .vue component TypeScript resolves to nothing (module resolution Bundler: an ECMAScript module's import adds no .ts to the name), in packages/hoppscotch-common/src/components.d.ts, packages/hoppscotch-common/src/components/aichat/__tests__/message-links.spec.ts, |
| analyze | output_withheld | 1 | real-app-hoppscotch: out/index.scip: out/index.scip holds the value of .env.example:PROXY_APP_URL, .env.example:VITE_BASE_URL, .env.example:VITE_SHORTCODE_BASE_URL, which Daodan keeps nowhere: the output is not kept |

## Container

- Corse: 30; secondi: 524,3.

| Fase | Corse | Secondi |
| --- | --- | --- |
| execute | 16 | 146,7 |
| prepare | 14 | 377,5 |

### Esiti diversi da exit 0

Nessuno.
