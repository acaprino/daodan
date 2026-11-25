# Astro: `parse` del compilatore che il progetto installa

Domanda: quante posizioni sono giuste nell'albero che `parse` del compilatore di Astro dà per un file `.astro` (il suo README avverte:
«Position data is currently incomplete and in some cases incorrect»), quali ingressi ne ricava la sorgente della pre-mappa
[`daodan/core/premap/astro.py`](../../daodan/core/premap/astro.py), e se uno strumento ufficiale elenca le rotte di un progetto Astro senza
avviarlo. Piano: [ingressi e flussi](../../docs/plans/2026-11-20-ingressi-e-flussi.md), task 13e; spec:
[ingressi e scoperta dei flussi](../../docs/specs/2026-11-20-ingressi-e-scoperta-dei-flussi.md), sezione 6.

Tutto gira su Modal, in un container con la rete bloccata: il codice del progetto (qui `astro` e il suo compilatore, installati dal
`package-lock.json` mentre l'immagine si costruisce, l'unico momento con la rete aperta) non gira mai su questa macchina.

**Astro 5, 6 e 7 non hanno lo stesso compilatore**, e la sorgente usa quello che l'`astro` del progetto dichiara:

| Astro | Compilatore (`dependencies` di `astro`) | `parse` |
| --- | --- | --- |
| 5.18.2 | `@astrojs/compiler` 2.13.1 (Go e WebAssembly) | asincrona, albero proprio con `position`; offset in byte, colonna in unità UTF-16 |
| 6.4.8 | `@astrojs/compiler` 4.0.0 (Go e WebAssembly) | identica alla 2.13.1 in ogni misura sotto |
| 7.4.13 | `@astrojs/compiler-rs` 0.5.3 (Rust, NAPI) | sincrona, ESTree con nodi JSX, `start` e `end` in unità UTF-16, nessuna riga né colonna |

| Cartella | Contenuto |
| --- | --- |
| `fixture/` | i file del progetto, uguali per le tre versioni: 13 file `.astro` (una pagina con frontmatter e 13 eventi di forme diverse, un componente con `client:*`, un layout, un file con caratteri fuori dall'ASCII, uno con tabulazioni, uno senza frontmatter, uno che non si chiude, uno con i casi difficili, uno con elementi SVG scritti con la maiuscola, uno con le forme di chiamata e due attributi che cominciano con `on` e non sono eventi) e un endpoint `.ts` |
| `versions/astro5`, `astro6`, `astro7` | `package.json` con un solo `astro` esatto e il suo `package-lock.json` (fatto su Modal con `npm install --package-lock-only --ignore-scripts`; tutti i `resolved` puntano a `registry.npmjs.org`) |
| `probe/` | le sonde; ognuna stampa ciò che misura. `_lib.mjs` trova il compilatore dalla cartella di `astro` con `createRequire`, come lo script di Daodan |
| `results/<versione>/` | l'uscita di ogni sonda, eseguita su Modal il 23 novembre 2026; `pipeline-scan-astro5.json` e `pipeline-scan-astro7.json`, il passo `scan` della pipeline intera |
| `modal_probe.py` | `--mode lock` scrive i lockfile; `--mode probes` esegue le sonde; `--mode source` esegue la sorgente di Daodan, anche su Node 20, e registra le risposte in `tests/fixtures/premap/astro/` |

```
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal python -m modal run benchmarks/astro-compiler/modal_probe.py --mode lock
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal python -m modal run benchmarks/astro-compiler/modal_probe.py
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal python -m modal run benchmarks/astro-compiler/modal_probe.py --mode source
```

## Parametri provati

| Parametro | Valori |
| --- | --- |
| Versione | Astro 5.18.2, 6.4.8, 7.4.13 (Node 24.22.3); Astro 5.18.2 anche su Node 20.20.2 |
| Fine riga | `\n` e `\r\n` (ogni file due volte) |
| Dove sta l'evento | su un elemento; su più righe; dopo testo di `<script>` e `<style>` che contiene `</` e `{`; dopo una stringa con `}` e `>` dentro `{...}`; dopo un attributo con un template literal su più righe; dentro `{items.map(...)}` e `{a && <a>}`; su `<svg>`, su `<foreignObject>`, `<textPath>` e `<animate>`, su un elemento personalizzato (`my-widget`), su un componente (`<Card onclick>`); dopo testo con `é`, `日本語` e `😀` sulla stessa riga; con tabulazioni |
| Forma dell'attributo | `onclick="..."`, `onclick='...'`, `onclick=go()` (senza apici), ``onclick={`...`}``, `{onclick}`, `{...rest}`, `client:load`, `is:inline`, `one="two()"`, `onfoo="bar()"` |
| Che gestore | `save()`, `this.disabled = true; confirmOrder(event)`, `return validate(this)`, `update(this.value)`, `cancel("now")`, `cart.add(1)`, `window.open('/x'); save()`, `items[0]()`, `factory()()`, `(0, run)()`, `new Thing()`; una funzione dichiarata solo nel frontmatter, in un `<script>` elaborato, in `<script is:inline type="module">`, in uno `is:inline` del layout |
| Testo che contiene un gestore e non lo è | una stringa in `<script>`, una stringa di `set:html`, un commento HTML |
| Markup rotto | frontmatter non chiuso, tag non chiuso, apice non chiuso, graffa non chiusa, file vuoto, solo testo; e `broken.astro` nella fixture |
| Rotte | `astro --help`, `astro sync`, `sync()` e `build()` dell'API con un'integrazione data in linea |
| Nomi degli eventi | `typescript/lib/lib.dom.d.ts` (`GlobalEventHandlers`), `astro/astro-jsx.d.ts` (`DOMAttributes`) |
| Tempo | il comando sotto `timeout` con 0,05 secondi |

## Posizioni del compilatore Go (Astro 5 e 6, identici), misurate

Verità: dove il testo scrive il simbolo del nodo (`<nome`, `{`, il nome dell'attributo, `---`) contro l'offset dichiarato; riga e colonna
devono essere quelle di quell'offset. 13 file; `\n` e `\r\n` danno gli stessi numeri. Uscita: `results/astro5/02_positions.txt`,
`results/astro6/02_positions.txt` (uguali dopo la prima riga).

| Nodo | n | Inizio esatto | Non esatto | Fine |
| --- | --- | --- | --- | --- |
| attributo (67 tra apici o senza, 10 senza valore, 8 con espressione, 1 `{nome}`, 2 `{...x}`) | 88 | **88** (il nome, anche dentro le graffe) | 0 | assente per tutti gli 88 |
| testo | 165 | 165 | 0 | 163 uguale al valore, 2 altrove |
| elemento | 78 | 75 | 3: un elemento che non ha tag di chiusura (`<meta>` del layout, il `<div>` e il `<section>` non chiusi di `broken.astro`) comincia un carattere dopo l'offset | fino al tag di chiusura 70; 2 `/>` un carattere prima del `>`; 3 altrove; 3 assente |
| componente, elemento personalizzato, frammento | 7, 1, 1 | tutti | 0 | componente: 5 al tag di chiusura, 2 altrove (autochiusi); frammento altrove |
| espressione `{...}` | 12 | **0** | 12: il `{` comincia un carattere dopo l'offset | 12 altrove |
| frontmatter | 11 | 11 | 0 | 11 fino alla riga `---` |
| commento | 1 | 1 (all'inizio del valore, dopo `<!--`) | 0 | non fino al valore |
| `doctype`, radice | 1, 13 | nessuna posizione | | |

- **Unità:** `offset` è in **byte UTF-8** (lo dice il tipo `Point`: «0-based byte offset»), `column` in **unità UTF-16** e 1-based: in `unicode.astro` 5 attributi,
  5 elementi e 9 testi hanno l'offset giusto solo letto come byte. Riga e colonna concordano con l'offset in tutti i nodi con posizione (0 discordanze), con questa convenzione.
  Lo snapshot scrive la colonna in byte: la sorgente converte (`angular._bytes`).
- **Eventi:** per ogni fine riga i 43 eventi elencati nella fixture, 86 su 86 trovati e 86 su 86 con inizio esatto (offset, riga e colonna); gli attributi `on*` nell'albero
  sono quelli elencati in tutti i 26 file×fine riga (nessuno inventato da una stringa di `<script>`, da `set:html` o da un commento, nessuno perso).
- Quindi: le posizioni **degli attributi** bastano a dare `file:riga` e colonna di un evento; quelle delle espressioni e degli elementi senza chiusura no, e di nessun attributo c'è la fine.
- **Markup rotto:** zero diagnostiche in tutti i 6 casi di `03_errors.txt` e in `broken.astro`; un apice non chiuso fa leggere il gestore seguente dentro il valore del primo e inventa un attributo `b()"`
  (`03_errors.txt`). Un gestore perso lì è perso senza una lacuna: la sorgente non lo può dire.

## Posizioni di `@astrojs/compiler-rs` (Astro 7), misurate

Stessa verità, sull'ESTree (`start..end` di un `JSXOpeningElement` comincia con `<nome` e finisce con `>`, un `JSXText` è il suo `raw`, un `JSXAttribute` comincia dal nome o da `{nome`, ...).
Uscita: `results/astro7/02_positions_rs.txt`, `01_rs.txt` (la struttura), `03_errors.txt`.

| Nodo | n | Giusti come unità UTF-16 | Non giusti |
| --- | --- | --- | --- |
| `JSXAttribute`, `JSXSpreadAttribute` | 83, 2 | 83, 2 | 0 |
| `JSXOpeningElement`, `JSXElement` | 83, 83 | 82, 82 | 1 ciascuno: l'elemento `this` a 0..0 che il compilatore inventa in `broken.astro` per riprendersi dall'errore |
| `JSXClosingElement`, `JSXExpressionContainer`, `JSXText` | 73, 20, 133 | tutti | 0 |
| `AstroFrontmatter` | 13 | 11 (due sono file senza frontmatter, 0..0) | 0 |
| `Literal` di un attributo | 64 | 62 | 2 artefatti della sonda: con un valore senza apici (`title=plain`, `onclick=go()`) `raw` ha gli apici aggiunti e `start..end` copre il testo giusto |

- **Unità:** gli offset sono unità UTF-16 (in `unicode.astro` nessun nodo è giusto solo come byte); riga e colonna non ci sono, la sorgente le calcola dal testo.
- **Eventi:** 80 su 80 trovati e con inizio esatto nei file che si leggono (86 elencati con i due fine riga; i 6 mancanti sono i 3 gestori di `broken.astro`); gli `on*` nell'albero sono quelli elencati in tutti
  i file tranne `broken.astro` (0 nell'albero, 3 elencati).
- **Markup rotto:** `broken.astro` dà 2 diagnostiche con `severity: error` e un albero senza i suoi gestori; `tag non chiuso` e `graffa non chiusa` danno un errore (riga e colonna nell'etichetta); `frontmatter non chiuso` non dà
  errore; **`apice non chiuso` lancia un'eccezione** (`Expected ',' or '}' after property value in JSON`, dentro l'involucro di `parse`): la sorgente la prende per file e la dice come lacuna (provato solo con una risposta modificata, non registrata).
- Non distingue un componente da un elemento: tutto è `JSXElement` (`Card`, `Counter`, `my-widget`); lo script usa la prima lettera del nome, come JSX (una maiuscola è un componente). `client:load` è un `JSXAttribute` senza valore.

## Che cosa dà `parse`, e che cosa non dà

| Dato | Misura |
| --- | --- |
| l'evento: l'attributo `on*` di un elemento HTML con la sua riga e colonna | sì, 100% esatto sui file che si leggono, per entrambi i compilatori |
| quali attributi sono eventi | **non `parse`**: i membri di `interface DOMAttributes` in `astro/astro-jsx.d.ts`, che ogni `astro` porta (56.494 byte in Astro 5, 6 e 7; 98 membri: 97 `on*` e `children`; `results/<versione>/06_astro_jsx.txt`), letti dall'albero sintattico di TypeScript. `one="two()"`, `onfoo` e `onend` di un `<animate>` non vi sono (limite: `onend` è un attributo SMIL che un browser può conoscere) |
| il valore | una stringa di JavaScript (`save()`), per un attributo tra apici; per `onclick={...}`, un template literal e `{onclick}` il compilatore non dà la stringa: si calcola al rendering della pagina |
| la funzione che il gestore chiama | **no**: è testo in una stringa. Lo leggono l'albero sintattico di JavaScript (`QUERIES["handlers"]`: ogni callee) e nient'altro; quale funzione il globale della pagina tiene sotto quel nome non lo dice nessuno strumento ufficiale. Il frontmatter gira sul server, un `<script>` che Astro elabora è un modulo, solo `is:inline` dichiara un globale, e lo snapshot legge frontmatter e `<script>` come un solo modulo: in `edge.astro` dichiara `fromFrontmatter`, `fromProcessedScript` e `fromModuleScript`, e una ricerca per nome legherebbe i gestori a codice che la pagina non raggiunge (`test_nothing_is_bound_by_name_...`) |
| `<script>` con `addEventListener` | JavaScript: il lettore del linguaggio lo legge già (le righe `argomento` degli `addEventListener`, per esempio `index.astro:43`); non duplicato |
| `client:*` | un attributo di un componente: un'isola, i cui eventi stanno nel file del componente (React, Vue, ...) e li legge il lettore del suo framework; non è un evento |
| `onclick` su un componente (`<Card onclick>`) | una prop, non un evento della pagina: non letto |
| le rotte | non da `parse` (vedi sotto) |

### Dove si trovano i nomi degli eventi (valutato)

`results/<versione>/05_event_names.txt`, `06_astro_jsx.txt`.

| Candidato | Misura | Uso |
| --- | --- | --- |
| `typescript/lib/lib.dom.d.ts`, `interface GlobalEventHandlers` | c'è nei pacchetti di Astro 5 (TypeScript 5.9.3 arriva con una sua dipendenza), **non c'è in quelli di Astro 6 e 7** | non usato: esiste solo se il progetto ha TypeScript |
| `astro/astro-jsx.d.ts`, `interface DOMAttributes` | in tutte e tre le versioni, 56.494 byte; 98 membri, 97 sono `on*` (tipo `string \| undefined \| null`) e `children` | **usato**: lo script lo stampa (`jsx`), la sorgente lo legge con tree-sitter (`QUERIES["astro_events"]`); senza il file, o senza l'interfaccia, nessun evento è letto e la lacuna lo dice |

Il prefisso `on` (`event_prefix`, dati) resta come filtro di volume di ciò che lo script stampa; non decide che cosa è un evento.

## Le rotte: uno strumento ufficiale le elenca (misurato), la sorgente non le legge

`results/<versione>/04_routes.txt`. Il confine di questo lavoro è `parse`: le rotte sono valutate e **non lette**.

| Misura | Astro 5.18.2 | Astro 6.4.8 | Astro 7.4.13 |
| --- | --- | --- | --- |
| comandi di `astro --help` che elencano le rotte | nessuno (add, build, check, create-key, db, dev, docs, info, preview, sync, preferences, telemetry) | nessuno (gli stessi) | nessuno (senza `db`) |
| `astro sync` (CLI): file scritti | `.astro/types.d.ts` e 3 file del contenuto; nessuno nomina una pagina o una rotta | 2 file, nessuno | 2 file, nessuno |
| `sync()` dell'API con un'integrazione data in linea: `astro:routes:resolved` | scatta, 12 rotte, 0,191 s | scatta, 14 rotte, 0,571 s | scatta, 14 rotte, 0,335 s |
| rotte del progetto (`origin: "project"`) | 11 con `entrypoint` (`src/pages/about.astro`, `src/pages/api/items.ts`, `src/pages/blog/[slug].astro`, ...), `type` (`page`, `endpoint`), `isPrerendered`, `params`; le altre sono di Astro (`/_image`; con 6 e 7 anche `/_server-islands/[name]` e `/404`) | le stesse 11 | le stesse 11; anche `broken.astro`, che `build()` rifiuta |
| `build()` con la stessa integrazione | riuscita in 1,02 s, `astro:routes:resolved` e `astro:build:done` (11 rotte) | riuscita in 2,32 s; `astro:build:done` dà 0 rotte e le pagine | fallita in 0,45 s su `broken.astro` (errore del compilatore) |

Lo strumento c'è, è documentato (la funzione `sync` dell'API JavaScript e l'hook `astro:routes:resolved` delle integrazioni), non avvia l'app, non fa il build e non carica le pagine: dà per ogni rotta il file e il tipo, non i metodi di un endpoint
(le esportazioni `GET` e `POST` le ha lo snapshot, come per Next.js). Non è un comando della CLI: serve uno script di Daodan che chiami `sync` con l'integrazione, dopo il ripristino dei pacchetti. Il file `astro.config.*` del progetto è codice del progetto e gira nel container. **Non scritto**: è il passo successivo (una sorgente come `nextjs.py`).

## La sorgente su Modal

`--mode source`: la sorgente dà il comando per la fixture, poi lo script
([`astro_templates.mjs`](../../daodan/core/premap/astro_templates.mjs)) gira con la rete bloccata sotto `timeout`, in una copia del progetto con i pacchetti, in una con `\r\n`, in una senza i pacchetti e con 0,05 secondi,
per ognuna delle tre versioni, e Astro 5 anche su Node 20.20.2. Le risposte, come le restituisce il container, sono in `tests/fixtures/premap/astro/`, con l'impronta sha256 dello script e la `VERSION` della sorgente (`script.json`).

| Misura | Risultato |
| --- | --- |
| eventi che lo script stampa (Astro 5 e 6) | 42 candidati con il prefisso `on` in 13 file (con `one`, `onfoo` e `onend` di `<animate>`, che la sorgente scarta perché Astro non li dichiara; `<Card onclick>` è di un componente e non è stampato); lo stesso con `\r\n`. Astro 7: 39 (i 3 di `broken.astro` no) |
| righe che la sorgente ne ricava | 40 con Astro 5 e 6 (33 per un nome, 2 per una chiamata su un oggetto, 3 per un callee che non è un nome, 2 per un valore che non è una stringa), 37 con Astro 7 (i 3 gestori di `broken.astro` no); tutte con `symbol` uguale a `owner` (il modulo del file) e una lacuna; nessuna ha `handler_source` |
| forme di chiamata (`calls.astro`) | `cart.add(1)`: una riga «su un oggetto»; `window.open('/x'); save()`: due righe, `window.open` su un oggetto e `save`; `items[0]()` e `(0, run)()`: una riga ciascuna, «un callee che non è un nome» con il tipo del nodo; `factory()()`: due righe; `new Thing()`: nessuna riga (limite) |
| elementi SVG con la maiuscola (`svg.astro`) | `<foreignObject onclick>` e `<textPath onclick>`: una riga ciascuno, con le tre versioni. Con la prima versione dello script (`tag === tag.toLowerCase()`) Astro 7 le saltava in silenzio e Astro 5 e 6 le leggevano (misurato su Modal con la fixture di ora) |
| uguaglianza fra versioni | stesse righe (sito, colonna, forma, evento, simbolo) per Astro 5 e 6; per Astro 7 le stesse fuori da `broken.astro` |
| Node 20 | Astro 5.18.2 su Node v20.20.2: exit 0, gli stessi 65.400 byte di uscita e le stesse 40 righe che su Node 24.22.3. Con il primo script (`findPackageJSON` di `node:module`, che esiste da Node 22.14) lo stesso comando usciva con 1: `SyntaxError: The requested module 'node:module' does not provide an export named 'findPackageJSON'` |
| colonna | in byte: `unicode.astro:4`: il compilatore dà la colonna 28 (da 1, unità UTF-16), lo snapshot scrive 36 (da 0, byte) |
| senza i pacchetti | exit 3: `astro is not installed for ... Cannot find module 'astro/package.json'`, una lacuna con le parole dello strumento, nessuna riga |
| tempo scaduto | con 0,05 secondi `timeout` esce 124 senza uscita: la lacuna dice «non finisce in N secondi»; exit 137 (`--kill-after`) è provato solo con una risposta modificata |
| lacune della sorgente | Astro 5 e 6: 0; Astro 7: 1, `parse reported 2 errors in src/pages/broken.astro, so events may be missing: Unterminated regular expression (line 9)` |

### La pre-mappa intera, nel container di Daodan

`DAODAN_FOLDER=<copia della fixture con package.json e package-lock.json di una versione> python -m modal run benchmarks/project-model/modal_pipeline.py --folder-out DIR --folder-stop scan`:
il ripristino dei pacchetti dal `package-lock.json` con la rete aperta ai soli registri, poi i comandi con la rete bloccata, come li lancia `container_runner`. `results/pipeline-scan-<versione>.json` tiene gli stati, le righe e le lacune della sorgente.

| Misura | Astro 5.18.2 | Astro 7.4.13 |
| --- | --- | --- |
| `scan`, tutto | 109,3 secondi | 123,0 secondi |
| sorgente `astro@daodan/premap/v2` | `ran`, 18,9 secondi, compreso il ripristino | `ran`, 20,1 secondi (il binding nativo di `compiler-rs` si carica nel container) |
| `framework_entries` | 40 righe, 0 lacune | 37 righe, 1 lacuna (`broken.astro`) |
| nei collegamenti | 0 ingressi, 38 lacune: le 2 righe di `onsubmit` e `oninput` (`index.astro:22`) non vi entrano, perché le forme non sono nel registro (solo `onclick` lo è) | 0 ingressi, 35 lacune (lo stesso motivo) |

Le righe sono quelle della risposta registrata (`test_the_premap_the_whole_pipeline_wrote_on_modal_holds_the_rows_of_the_recorded_answer`).

## Limiti dichiarati

- **`new Thing()`** (un costruttore) e un template con tag non sono chiamate che la query legge: nessuna riga, nessuna lacuna (`# shortcut:` in `astro.py`).
- **Nomi degli eventi:** quelli che Astro dichiara in `DOMAttributes`. Un attributo `on*` che un browser conosce e Astro no (`onend` di SMIL) non è letto. Il file manca in una versione di Astro che non lo porta con quel nome (Astro 4 non è stato eseguito): nessun evento e una lacuna.
- **Un nome con namespace (`<svg:rect>`) o un membro (`<a.b>`)** non è un elemento per compiler-rs (`# shortcut:` nello script).
- **Diagnostiche:** solo quelle di gravità `error` (Go: 1, Rust: `'error'`) sono errori di un file; la fixture non ha prodotto altre gravità, quindi il filtro non ha una risposta registrata.
- **Tempo:** 600 secondi divisi fra le cartelle (minimo 10 ciascuna); un progetto di più di 60 cartelle chiede di più (`# shortcut:` in `astro.py`).
- **Una sola `VERSION` per sorgente:** cambiare lo script senza alzarla lascia righe vecchie in una pre-mappa fresca; il test dell'impronta registrata (`script.json` porta anche la `VERSION`) fallisce finché le risposte non sono registrate di nuovo, ma non obbliga ad alzarla: è un avviso, non un vincolo.

## Non provato

- Una versione di Astro diversa da 5.18.2, 6.4.8 e 7.4.13: Astro 4 usa `@astrojs/compiler` ^2.10 (non eseguito); Node 18 (Astro 5 lo supporta) non provato.
- Un progetto Astro vero: nessun repository pubblico è stato misurato, quindi non si sa quanti gestori `on*` in una stringa ci siano in un progetto reale, né quante righe darebbe la sorgente.
- Il gestore che il globale della pagina lega a una funzione: nessuno strumento ufficiale lo dà (`transform` di `@astrojs/compiler` dice quali `<script>` elabora, ma senza le posizioni delle dichiarazioni dello snapshot); aperto, non misurato.
- pnpm o Yarn con pacchetti non alla radice: la ricerca parte dalla cartella di `astro`, ma è provata solo con npm.
- L'eccezione di `compiler-rs` su un apice non chiuso come lacuna: lo script la prende per file, la risposta non è registrata dal container.
- Una diagnostica che non sia un errore (avviso, informazione): nessuna prodotta, il filtro per gravità non è coperto da una risposta registrata.
- Un `.astro` con `Astro.slots`, `define:vars` o altre forme non nella fixture.
