# Angular: `parseTemplate` del compilatore che il progetto installa

**Stato:** In uso. La sorgente [`daodan/core/premap/angular.py`](../../daodan/core/premap/angular.py) con lo script `angular_templates.mjs` è in `premap.SOURCES` e `TEMPLATE_SOURCES`, ha la voce `angular` in `container_runner.TOOLS`; le sue righe si fondono con quelle del lettore ad albero (`entries.compiled`). Aperto: gli eventi di `host` e `@HostListener`, la distinzione fra evento del DOM e uscita di un componente, i gestori proprietà-freccia, e le rotte di Angular, che nessuno strumento elenca («Aperto»).

## Domanda

Che dati e che posizioni dà `parseTemplate` di `@angular/compiler` per gli eventi legati in un template (`(click)="save()"`), e che cosa ne ricava la sorgente. Spec: [ingressi e scoperta dei flussi](../../docs/specs/2026-11-20-ingressi-e-scoperta-dei-flussi.md), sezione 6 (task 13f del piano).

## Strumento ufficiale provato

`@angular/compiler` 22.3.0 e `@angular/compiler-cli` (fixture), Angular 20.3.35 con TypeScript 5.9.3 (immagine a parte), Angular 22.1.6 (`jhipster-sample-app`); Node 24.22.3. Misurato su Modal il 23 novembre 2026, rete bloccata.

- **`parseTemplate`** dà gli eventi con le posizioni e l'albero del gestore. Ha un commento ma nessuna etichetta `@publicApi` (0 occorrenze in `compiler.d.ts`).
- **`R3TargetBinder`**, dello stesso pacchetto, dice se un nome è una variabile del template.
- **Il controllore dei template di `@angular/compiler-cli`** (`getSymbolOfNode`, `getTsSymbolOfSymbol`) dice la dichiarazione di una chiamata su un altro oggetto. Chiede l'opzione interna `_enableTemplateTypeChecker`.
- **Valutato e non usato:** il servizio del linguaggio (`@angular/language-service`, `getDefinitionAndBoundSpan`) dà la stessa dichiarazione ma è un plugin per gli editor; il progetto si carica in 2,8-4,3 secondi. `NgCompiler.getComponentsWithTemplateFile` non dà la classe di un template scritto nel `.ts`: la classe la dà il decoratore, letto dall'albero sintattico.

## Parametri

| Parametro | Valori |
| --- | --- |
| Dove sta il template | file `.html` (`templateUrl`); letterale con i backtick, stringa con apici singoli e `\'`, `\n`, stringa con apici doppi e `\"` (`template` nel decoratore); file con `\r\n` |
| Come si chiama `parseTemplate` | senza opzioni; con il solo testo della stringa; con il testo del `.ts` intero, `range` del contenuto e `escapedString` vero o falso |
| Dove sta l'evento | su un elemento; dentro `@if`, `@for`, `@switch`, `@defer`; su `ng-template`; su un elemento con `*ngFor`; su un componente figlio; `(window:resize)`; `(keyup.enter)`; `(ngSubmit)`; `[(ngModel)]` |
| Che gestore | `save()`, `this.save()`, `svc.cancel()`, `!busy && save()`, `busy ? close() : reopen()`, `save(); close()`, `open = !open`, `router.navigate([...])`, `$any(x).go()`, `a?.b()`, `items[0].run()`, `c('x')` in `ng-template let-c`, un `@let save`, la variabile `go` di un `@for`, `handlers[0]()`, `factory()()` |
| Template rotto | chiamata non chiusa, gestore vuoto, `@if` non chiuso, blocco sconosciuto, pipe in un gestore |
| Chi dice se un nome è del template | `R3TargetBinder` di `@angular/compiler` |
| Chi dice dove è il metodo | la sorgente, dalle dichiarazioni dello snapshot, per un metodo del componente; per un ricevente diverso, il servizio del linguaggio di Angular (`getDefinitionAndBoundSpan`) e il controllore dei template di `@angular/compiler-cli` (`getSymbolOfNode`, `getTsSymbolOfSymbol`), a confronto |

File: `fixture/` (un progetto Angular 22.3.0: 14 template, 3 `.html` e 11 scritti nel `.ts`), `probe/` (le sonde, ognuna stampa ciò che misura), `modal_probe.py` (`--mode probes`; `--mode source`, che registra `tests/fixtures/premap/angular/` con l'impronta dello script; `--mode measure` con `REPO` e `COMMIT` di un repository pubblico), `results/` (`00_env.txt` dà le versioni).

```
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal python -m modal run benchmarks/angular-compiler/modal_probe.py
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal python -m modal run benchmarks/angular-compiler/modal_probe.py --mode source
REPO=https://github.com/jhipster/jhipster-sample-app COMMIT=6b000b5d23a36c45e01472471b84a44fa2464044 PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal python -m modal run benchmarks/angular-compiler/modal_probe.py --mode measure
```

## Risultato

**Che cosa dà `parseTemplate`.**

| Misura | Risultato | Uscita |
| --- | --- | --- |
| eventi legati in `app.component.html` (33 righe) | 21 scorrendo i nodi, 20 distinti: il `li` con `*ngFor` tiene lo stesso `BoundEvent` sul `Template` e sull'`Element`; il visitatore ufficiale (`tmplAstVisitAll`, `TmplAstRecursiveVisitor`) vede gli stessi 21 | `results/01_html.txt` |
| posizioni di `sourceSpan`, `keySpan`, `handlerSpan` per i 20 eventi | 60 su 60 esatte in riga, colonna e offset contro un controllo scritto a parte nella sonda, anche dentro `@if`, `@for`, `*ngFor` e `ng-template`; con `\r\n` 63 su 63 | `results/01_html.txt`, `03_extras.txt` |
| gestore | l'albero del gestore nomina il metodo e il ricevente: `save()` e `this.save()` (`ImplicitReceiver`, `ThisReceiver`), `svc.cancel()` (ricevente `svc`), il lato destro di `&&`, i due rami di un ternario, le due chiamate di una catena; `open = !open` e `[(ngModel)]` non chiamano nulla; `[(ngModel)]` è l'evento `ngModelChange`, tipo 2 | `01_html.txt`, `03_extras.txt` |
| template scritto nel `.ts`, `parseTemplate(testo del .ts, url, {range, escapedString: true})` | posizioni esatte, nel `.ts`, per il letterale, per la stringa con `\'` e `\n` e per quella con `\"`; riga e colonna sono quelle del file | `results/02_inline.txt`, `11_inline_more.txt` |
| lo stesso, con `escapedString: false` | la stringa con `\"` dà due errori e nessun nodo | `results/11_inline_more.txt` |
| lo stesso, con la sola stringa e nessuna opzione | gli offset sono dentro la stringa, non nel file | `results/02_inline.txt` |
| template rotto | `errors` e nodi parziali, mai un'eccezione; una chiamata non chiusa dà comunque l'evento con la `Call` parziale; un `@if` non chiuso non dà alcun evento (li dà con `alwaysAttemptHtmlToR3AstConversion`, non usata) | `results/03_extras.txt` |
| stato dell'API | `parseTemplate` ha un commento ma nessuna etichetta `@publicApi` (0 occorrenze in `compiler.d.ts`) | `results/03_extras.txt` |

**Che cosa non dà, e chi lo dà.**

| Dato | Misura | Uscita |
| --- | --- | --- |
| la classe del ricevente (`svc` in `svc.cancel()`) | `parseTemplate` dà il nome `svc` e il metodo `cancel`, non il tipo. Lo dà un controllore dei tipi, e ne sono stati misurati due: il servizio del linguaggio (`ts.server.ProjectService` con il plugin `@angular/language-service`, `getDefinitionAndBoundSpan` a una posizione: `svc.cancel` va a `order.service.ts`, il progetto si carica in 2,8-4,3 secondi nelle tre run: 2794, 4138 e 4270 ms) e il controllore dei template di `@angular/compiler-cli` (`getSymbolOfNode` su un nodo del template, poi `getTsSymbolOfSymbol`: stessa dichiarazione; `ngc` stesso esce 0 in 1,7 secondi, `loadNgStructureAsync` 67 ms). **La sorgente usa il secondo**: `ngc`, il compilatore di Angular, è un programma di `@angular/compiler-cli` (esce 0 sulla fixture), che un progetto che si compila con Angular ha, mentre il plugin del servizio del linguaggio serve agli editor; il prezzo è l'opzione interna `_enableTemplateTypeChecker`, senza la quale il controllore rifiuta (`{}` lancia, `{_enableTemplateTypeChecker: true}` funziona) | `results/04_compiler_cli.txt`, `10_symbols_options.txt`, `07_ls_join.txt` |
| se un nome senza oggetto davanti è un metodo della classe | `parseTemplate` non risolve gli ambiti: `c('x')` dentro `<ng-template let-c="close">`, un `@let save = …` e la variabile di un `@for` sono per lui `PropertyRead` di `ImplicitReceiver`, come un metodo. Lo dice `R3TargetBinder(null).bind({template}).getExpressionTarget(callee)` di `@angular/compiler`, lo stesso pacchetto: `Variable` per `let-c` e per la variabile del `@for`, `LetDeclaration` per `@let`, `null` per un metodo e per `this.save()`. Provato con e senza `SelectorMatcher` | `results/12_target_binder.txt` |
| la classe che possiede un template | non la dà `parseTemplate`: la dà il decoratore, letto dall'albero sintattico del `.ts` (tree-sitter), `templateUrl` per il file `.html`, `template` per la posizione nel `.ts`. Valutati e non usati: `NgCompiler.getComponentsWithTemplateFile` dà la classe di un `.html` e nessuna per un template scritto nel `.ts` (lista vuota per `inline.component.ts`); `getComponentLocationsForTemplate` del servizio del linguaggio chiede un programma TypeScript e il plugin. La prima passata deve funzionare con il solo `@angular/compiler`: per questo non si usa `ttc.getTemplate`, che chiede il programma del progetto | `results/11_inline_more.txt`, `04_compiler_cli.txt` |
| un chiamato che non è un nome (`handlers[0]()`, `factory()()`) | l'albero lo dà (`KeyedRead`, `Call`), il nome no: la sorgente dice la lacuna con il tipo del nodo, e legge comunque la chiamata dentro (`factory`) | `modal_probe.py --mode source` |
| gli eventi di `host: {...}` e di `@HostListener` | `parseHostBindings` dà le stringhe senza posizioni; `createHostElement`, con i legami costruiti a mano, risponde `null`. Il controllore dei template ha `getHostElement`, che dà i due ascoltatori dell'esempio: **non letto dalla sorgente** | `results/05_host.txt`, `10_symbols_options.txt` |
| le rotte | nessuno strumento di Angular le elenca; il valutatore del compilatore (`PartialEvaluator`, `@angular/compiler-cli/private/migrations`) dà `Reference(...)` per `component` e `DynamicValue` per `loadComponent` e `loadChildren`: **non lette** | `results/09_routes.txt` |
| il tipo dell'evento: DOM o uscita di un componente figlio | `(saved)` e `(click)` sono entrambi `type` 0 per `parseTemplate`; il controllore dei template e il servizio del linguaggio li distinguono (`saved` va a `editor.component.ts`, `click` a `addEventListener` di `lib.dom.d.ts`). **La sorgente non lo usa**: la forma `(saved)` aspetta la classificazione | `results/07_ls_join.txt`, `10_symbols_options.txt` |

**La sorgente.** Per ogni cartella due comandi di `angular_templates.mjs`, con la lista dei template in un file: il primo chiama `parseTemplate` e il binder; il secondo, `--types`, interroga il controllore dei template sotto `timeout`. Le risposte registrate sono in `tests/fixtures/premap/angular/`, con l'impronta sha256 dello script (`script.json`): se lo script cambia, un test fallisce finché le risposte non sono registrate di nuovo su Modal.

| Variante del progetto | Analisi (`parseTemplate`, binder) | Controllore dei tipi (`--types`) |
| --- | --- | --- |
| con i pacchetti | exit 0, 40 eventi in 14 template: 2 senza chiamata (`open = !open`, `[(ngModel)]`), 2 con una chiamata che non si legge | exit 0, 4 chiamate su un altro oggetto: `svc.cancel` → `src/app/order.service.ts` riga 5; `router.navigate` → `node_modules/@angular/router/…d.ts`; `saved.emit` → `node_modules/@angular/core/…d.ts`; `helper.run` → errore: `UnreachedComponent` non è nel programma del `tsconfig.json` (1 file radice) |
| senza i pacchetti | exit 3, `@angular/compiler is not installed … Cannot find module '@angular/compiler'` | non chiesto: senza eventi non c'è nulla da risolvere |
| senza `@angular/compiler-cli` | exit 0, stesse righe | exit 0, `error`: `@angular/compiler-cli is not installed for … Cannot find module '@angular/compiler-cli'` |
| senza `tsconfig.json` | exit 0, stesse righe | exit 0, `error`: `tsconfig.json is not in …` |
| `tsconfig.json` solution-style (`files: []`, `references` al vero, che diventa `tsconfig.app.json`) | exit 0, stesse righe | exit 0, stesse 4 risposte; l'errore di `helper.run` nomina `tsconfig.app.json` (1 file radice). Il programma del solo `tsconfig.json` avrebbe 0 file radice: non provato con lo script precedente |
| il controllore con 0,05 secondi | exit 0 | exit 124 (`timeout`), nessuna uscita: la lacuna dice «non finisce in N secondi» |
| Angular 20.3.35, TypeScript 5.9.3 (immagine a parte, pacchetti dal registro senza lockfile) | exit 0, gli stessi 40 eventi con le stesse chiamate | exit 0, le stesse 4 risposte (cambia solo il nome del file `.d.ts` di `node_modules`) |

| Misura | Risultato |
| --- | --- |
| lacune dette prima dell'esecuzione | 2: un `template` con `${...}` (`computed.component.ts`) e un `templateUrl` che nomina un file che lo snapshot non ha (`nowhere.component.html`) |
| righe che la sorgente ne ricava | 41: 32 sul metodo (compreso `OrderService.cancel`, in un altro file, e `ScopedComponent.real` e `.save` per `this.save()`), 9 lacune con la causa: `router.navigate` e `saved.emit('done')` (dichiarate fuori dallo snapshot), `helper.run()` (componente fuori dal programma), `gone()` (che `GoneComponent` non dichiara), `c('x')` e `go()` (variabili del template), `save()` (un `@let`), `handlers[0]()` e `factory()()` (chiamato che non è un nome); più 1 lacuna della sorgente per gli errori di un template rotto (`bad.component.html`) |
| nei collegamenti (`flows.cached_links`, in `tests/test_codebase_map_premap_angular.py`) | 28 ingressi sui metodi giusti e 9 lacune, solo `(click)`: le altre forme (`(ngSubmit)`, `(keyup.enter)`, `(window:resize)`, `(saved)`) non sono nel registro e aspettano la risposta sulla forma, come per il lettore ad albero; senza le righe del compilatore il lettore ad albero dà 0 ingressi e 11 lacune «handler … not resolved» |
| l'arco `attiva` di un evento | parte dalla classe del componente (`AppComponent`), anche quando il metodo è di un'altra classe (`OrderService.cancel`) |
| una riga di `svc.cancel()` ha l'etichetta | no: l'etichetta passa dalla riga del lettore ad albero, che per `svc.cancel()` e `this.save()` non ne ha |

**La pre-mappa intera** (`modal_pipeline.py --folder-stop scan` sulla fixture, `results/pipeline-scan.json`; rifatta il 24 novembre 2026 con la sorgente `daodan/premap/v2`):

| Misura | Risultato |
| --- | --- |
| `scan`, tutto | 134,0 secondi, rifatto il 24 novembre 2026 (con `renovate` 39,0 s, `tsc` 24,5 s, `go-enry` 23,6 s, `noir` 10,0 s, `npm` 6,8 s) |
| sorgente `angular@daodan/premap/v2` | `ran`, 28,7 secondi, compreso il ripristino dei pacchetti e i due comandi |
| `framework_entries` in `premap.json` | 41 righe non legate (dalla v2 il legame al metodo si fa nei collegamenti), le stesse della risposta registrata campo per campo; legate, 9 lacune, lo stesso sito, colonna, simbolo, lacuna, evento e proprietario; `test_the_premap_the_whole_pipeline_wrote_on_modal_holds_the_rows_of_the_recorded_answer` lo verifica su `results/pipeline-scan.json` |
| `c('x')` dentro `ng-template let-c` | una lacuna «c is a template variable …», non più «ScopedComponent does not declare c: it is inherited…» |
| lacune della sorgente | 3: `computed.component.ts`, `nowhere.component.html`, `bad.component.html` (errori del compilatore) |
| `next` | `not_needed`: la fixture non dichiara Next.js |

**Un progetto reale:** `jhipster/jhipster-sample-app` (Apache-2.0, commit `6b000b5d23a36c45e01472471b84a44fa2464044`, Angular 22.1.6).

| Misura | Risultato | Uscita |
| --- | --- | --- |
| che cosa trova la sorgente (`--mode measure`) | 59 componenti, 59 template, 1 cartella, nessuna lacuna prima dell'esecuzione | `results/measure-jhipster-sample-app.json` |
| `scan` della pipeline, tutto | 293,2 secondi (con `tsc` 82,1 s, `maven` 25,5 s, `npm` 9,1 s, `noir` 9,1 s) | `results/pipeline-scan-jhipster-sample-app.json` |
| sorgente `angular@daodan/premap/v1` | `ran`, 84,1 secondi, compreso il ripristino dei pacchetti (`npm`, senza lockfile) e i due comandi; il tempo del solo controllore dei tipi non è registrato | idem |
| `framework_entries` | 94 righe: 89 sul metodo della classe, 5 lacune. Per forma: `(click)` 65, `(ngSubmit)` 16, `(sortChange)` 7, `(ngModelChange)` 2, `(closed)` 2, `(pageChange)` 1, `(scrolled)` 1. Due righe sono di template scritti nel `.ts` | idem |
| le 5 lacune | 3 chiamate su un altro oggetto che il controllore dei tipi dichiara in `node_modules/@angular/core/…d.ts` (`beansFilter.set`, `filter.set`, `isNavbarCollapsed.update`: segnali); 2 in file `.spec.ts` (`TestSortByDirective` e `TestSortDirective` non dichiarano `transition`: ereditato o assegnato a run time) | idem |
| le chiamate che il controllore dei tipi ha legato a un metodo del progetto in un altro file | **0**: in questo repository nessun template chiama un servizio del progetto; il caso `svc.cancel()` è provato solo sulla fixture. Nessuna chiamata è di una variabile del template | idem |
| lacune che accompagnano la risposta | 3, della preparazione e non della lettura: un intervallo di Node (`>=24.21.0`) che non è una versione da installare e due file che Daodan non legge; nessuna lacuna di lettura dei template | idem |

## Aperto

- **Tre punti con una sonda scritta e mai eseguita** (`probe/13_open_points.mjs`, uscita attesa in `results/13_open_points.txt`):
  - `host: {…}` e `@HostListener`: `getHostElement` del controllore dà i listener; se dà un `file:riga` nel `.ts` non è misurato. Oggi non sono letti.
  - Uscita di un componente o evento del DOM: `(saved)` e `(click)` sono lo stesso tipo per `parseTemplate`; il controllore li distingue, la sorgente non lo usa.
  - Un gestore proprietà-freccia (`save = () => {}`): lo snapshot lo dichiara come funzione anonima e la sorgente dà la lacuna «non dichiara»; il controllore lo darebbe.
- **Le rotte di Angular:** nessuno strumento le elenca; `PartialEvaluator` dà `Reference(...)` per `component` e `DynamicValue` per `loadComponent` e `loadChildren`. Non lette.
- **I gestori che lo strumento non lega** (9 lacune sulla fixture, 5 su `jhipster-sample-app`: dichiarazioni fuori dallo snapshot, metodi ereditati o assegnati a run time, variabili del template): il passo dinamico preme i controlli nel browser e isola il gestore (`daodan/core/dynamic/app.py`, `observed_entries.py`), misurato su un'app React in [project-model](../project-model/README.md), «Esplorazione dell'app avviata»; su un'app Angular non è misurato.
- **Le forme fuori dal registro:** nei collegamenti entra solo `(click)`; `(ngSubmit)`, `(keyup.enter)`, `(window:resize)`, `(saved)` aspettano la decisione sulla forma.
- **Non provati:** Angular diverso da 20.3.35, 22.1.6 e 22.3.0 (prima della 20 `getTsSymbolOfSymbol` può mancare; fino alla 12 una chiamata è `MethodCall`); un riferimento del template (`#box`); un `tsconfig.json` solution-style di un progetto vero; un secondo progetto reale (su `jhipster-sample-app` nessuna delle 94 righe è stata confrontata a mano con il template); `import * as core from '@angular/core'` con `@core.Component(...)` (il file non è scelto, senza lacuna); memoria e tempo del controllore dei tipi su un progetto grande.
