# Astro: `parse` del compilatore che il progetto installa

**Stato:** In parte. In uso: la sorgente [`daodan/core/premap/astro.py`](../../daodan/core/premap/astro.py) con lo script `astro_templates.mjs` è in `premap.SOURCES` e `TEMPLATE_SOURCES` e ha la voce `astro` in `container_runner.TOOLS`; dà ogni evento `on*` con file, riga e colonna. Manca: la funzione che il gestore chiama (ogni riga ha una lacuna, 0 ingressi nei collegamenti) e le rotte, che uno strumento ufficiale elenca e nessuna sorgente legge («Aperto»).

## Domanda

Quante posizioni sono giuste nell'albero che `parse` del compilatore di Astro dà per un file `.astro` (il suo README avverte: «Position data is currently incomplete and in some cases incorrect»), quali ingressi ne ricava la sorgente, e se uno strumento ufficiale elenca le rotte di un progetto Astro senza avviarlo. Spec: [ingressi e scoperta dei flussi](../../docs/specs/2026-11-20-ingressi-e-scoperta-dei-flussi.md), sezione 6 (task 13e del piano).

## Strumento ufficiale provato

`parse` del compilatore che l'`astro` del progetto dichiara; Node 24.22.3, e Astro 5.18.2 anche su Node 20.20.2. Misurato su Modal il 23 novembre 2026, rete bloccata.

| Astro | Compilatore (`dependencies` di `astro`) | `parse` |
| --- | --- | --- |
| 5.18.2 | `@astrojs/compiler` 2.13.1 (Go e WebAssembly) | asincrona, albero proprio con `position`; offset in byte, colonna in unità UTF-16 |
| 6.4.8 | `@astrojs/compiler` 4.0.0 (Go e WebAssembly) | identica alla 2.13.1 in ogni misura sotto |
| 7.4.13 | `@astrojs/compiler-rs` 0.5.3 (Rust, NAPI) | sincrona, ESTree con nodi JSX, `start` e `end` in unità UTF-16, nessuna riga né colonna |

Quali attributi sono eventi lo dice Astro, non `parse`:

| Candidato | Misura | Uso |
| --- | --- | --- |
| `typescript/lib/lib.dom.d.ts`, `interface GlobalEventHandlers` | c'è nei pacchetti di Astro 5 (TypeScript 5.9.3 arriva con una sua dipendenza), **non c'è in quelli di Astro 6 e 7** | non usato: esiste solo se il progetto ha TypeScript |
| `astro/astro-jsx.d.ts`, `interface DOMAttributes` | in tutte e tre le versioni, 56.494 byte; 98 membri, 97 sono `on*` (tipo `string \| undefined \| null`) e `children` | **usato**: lo script lo stampa (`jsx`), la sorgente lo legge con tree-sitter (`QUERIES["astro_events"]`); senza il file, o senza l'interfaccia, nessun evento è letto e la lacuna lo dice |

Il prefisso `on` (`event_prefix`, dati) è solo un filtro di volume di ciò che lo script stampa.

## Parametri

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

File: `fixture/` (13 file `.astro` e un endpoint `.ts`, uguali per le tre versioni), `versions/astro5`, `astro6`, `astro7` (`package.json` con un solo `astro` esatto e il suo lockfile), `probe/` (le sonde), `modal_probe.py` (`--mode lock`, `--mode probes`, `--mode source`, che registra `tests/fixtures/premap/astro/` con l'impronta dello script e la `VERSION`), `results/<versione>/`.

```
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal python -m modal run benchmarks/astro-compiler/modal_probe.py --mode lock
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal python -m modal run benchmarks/astro-compiler/modal_probe.py
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal python -m modal run benchmarks/astro-compiler/modal_probe.py --mode source
```

## Risultato

Verità delle posizioni: dove il testo scrive il simbolo del nodo (`<nome`, `{`, il nome dell'attributo, `---`) contro l'offset dichiarato. 13 file; `\n` e `\r\n` danno gli stessi numeri.

**Il compilatore Go (Astro 5 e 6, identici)**, `results/astro5/02_positions.txt` e `results/astro6/02_positions.txt`:

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

- `offset` è in byte UTF-8, `column` in unità UTF-16 e 1-based; lo snapshot scrive la colonna in byte e la sorgente converte (`frameworks.column_bytes`).
- Eventi: 86 su 86 trovati e con inizio esatto; nessuno inventato da una stringa di `<script>`, da `set:html` o da un commento.
- Le posizioni degli attributi bastano per `file:riga` e colonna di un evento; quelle delle espressioni e degli elementi senza chiusura no, e di nessun attributo c'è la fine.
- Markup rotto: zero diagnostiche; un apice non chiuso fa leggere il gestore seguente dentro il valore del primo. Un gestore perso lì è perso senza una lacuna.

**`@astrojs/compiler-rs` (Astro 7)**, `results/astro7/02_positions_rs.txt`:

| Nodo | n | Giusti come unità UTF-16 | Non giusti |
| --- | --- | --- | --- |
| `JSXAttribute`, `JSXSpreadAttribute` | 83, 2 | 83, 2 | 0 |
| `JSXOpeningElement`, `JSXElement` | 83, 83 | 82, 82 | 1 ciascuno: l'elemento `this` a 0..0 che il compilatore inventa in `broken.astro` per riprendersi dall'errore |
| `JSXClosingElement`, `JSXExpressionContainer`, `JSXText` | 73, 20, 133 | tutti | 0 |
| `AstroFrontmatter` | 13 | 11 (due sono file senza frontmatter, 0..0) | 0 |
| `Literal` di un attributo | 64 | 62 | 2 artefatti della sonda: con un valore senza apici (`title=plain`, `onclick=go()`) `raw` ha gli apici aggiunti e `start..end` copre il testo giusto |

- Gli offset sono unità UTF-16; riga e colonna non ci sono, la sorgente le calcola dal testo.
- Eventi: 80 su 80 trovati e con inizio esatto nei file che si leggono; i 3 gestori di `broken.astro` no (2 diagnostiche `error`, una lacuna).
- Un apice non chiuso lancia un'eccezione dentro `parse`: la sorgente la prende per file e la dice come lacuna (provato solo con una risposta modificata).
- Tutto è `JSXElement`: lo script distingue un componente dalla prima lettera del nome, come JSX.

**Che cosa dà `parse`, e che cosa no.**

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

**La sorgente.** Lo script gira sotto `timeout` con la rete bloccata; le risposte registrate sono in `tests/fixtures/premap/astro/`.

| Misura | Risultato |
| --- | --- |
| eventi che lo script stampa (Astro 5 e 6) | 42 candidati con il prefisso `on` in 13 file (con `one`, `onfoo` e `onend` di `<animate>`, che la sorgente scarta perché Astro non li dichiara; `<Card onclick>` è di un componente e non è stampato); lo stesso con `\r\n`. Astro 7: 39 (i 3 di `broken.astro` no) |
| righe che la sorgente ne ricava | 40 con Astro 5 e 6 (33 per un nome, 2 per una chiamata su un oggetto, 3 per un callee che non è un nome, 2 per un valore che non è una stringa), 37 con Astro 7 (i 3 gestori di `broken.astro` no); tutte con `symbol` uguale a `owner` (il modulo del file) e una lacuna; nessuna ha `handler_source` |
| forme di chiamata (`calls.astro`) | `cart.add(1)`: una riga «su un oggetto»; `window.open('/x'); save()`: due righe, `window.open` su un oggetto e `save`; `items[0]()` e `(0, run)()`: una riga ciascuna, «un callee che non è un nome» con il tipo del nodo; `factory()()`: due righe; `new Thing()`: nessuna riga (limite) |
| elementi SVG con la maiuscola (`svg.astro`) | `<foreignObject onclick>` e `<textPath onclick>`: una riga ciascuno, con le tre versioni. |
| uguaglianza fra versioni | stesse righe (sito, colonna, forma, evento, simbolo) per Astro 5 e 6; per Astro 7 le stesse fuori da `broken.astro` |
| Node 20 | Astro 5.18.2 su Node v20.20.2: exit 0, gli stessi 65.400 byte di uscita e le stesse 40 righe che su Node 24.22.3. |
| colonna | in byte: `unicode.astro:4`: il compilatore dà la colonna 28 (da 1, unità UTF-16), lo snapshot scrive 36 (da 0, byte) |
| senza i pacchetti | exit 3: `astro is not installed for ... Cannot find module 'astro/package.json'`, una lacuna con le parole dello strumento, nessuna riga |
| tempo scaduto | con 0,05 secondi `timeout` esce 124 senza uscita: la lacuna dice «non finisce in N secondi»; exit 137 (`--kill-after`) è provato solo con una risposta modificata |
| lacune della sorgente | Astro 5 e 6: 0; Astro 7: 1, `parse reported 2 errors in src/pages/broken.astro, so events may be missing: Unterminated regular expression (line 9)` |

**La pre-mappa intera** (`modal_pipeline.py --folder-stop scan`, `results/pipeline-scan-<versione>.json`):

| Misura | Astro 5.18.2 | Astro 7.4.13 |
| --- | --- | --- |
| `scan`, tutto | 109,3 secondi | 123,0 secondi |
| sorgente `astro@daodan/premap/v2` | `ran`, 18,9 secondi, compreso il ripristino | `ran`, 20,1 secondi (il binding nativo di `compiler-rs` si carica nel container) |
| `framework_entries` | 40 righe, 0 lacune | 37 righe, 1 lacuna (`broken.astro`) |
| nei collegamenti | 0 ingressi, 38 lacune: le 2 righe di `onsubmit` e `oninput` (`index.astro:22`) non vi entrano, perché le forme non sono nel registro (solo `onclick` lo è) | 0 ingressi, 35 lacune (lo stesso motivo) |

**Le rotte: uno strumento ufficiale le elenca**, `results/<versione>/04_routes.txt`:

| Misura | Astro 5.18.2 | Astro 6.4.8 | Astro 7.4.13 |
| --- | --- | --- | --- |
| comandi di `astro --help` che elencano le rotte | nessuno (add, build, check, create-key, db, dev, docs, info, preview, sync, preferences, telemetry) | nessuno (gli stessi) | nessuno (senza `db`) |
| `astro sync` (CLI): file scritti | `.astro/types.d.ts` e 3 file del contenuto; nessuno nomina una pagina o una rotta | 2 file, nessuno | 2 file, nessuno |
| `sync()` dell'API con un'integrazione data in linea: `astro:routes:resolved` | scatta, 12 rotte, 0,191 s | scatta, 14 rotte, 0,571 s | scatta, 14 rotte, 0,335 s |
| rotte del progetto (`origin: "project"`) | 11 con `entrypoint` (`src/pages/about.astro`, `src/pages/api/items.ts`, `src/pages/blog/[slug].astro`, ...), `type` (`page`, `endpoint`), `isPrerendered`, `params`; le altre sono di Astro (`/_image`; con 6 e 7 anche `/_server-islands/[name]` e `/404`) | le stesse 11 | le stesse 11; anche `broken.astro`, che `build()` rifiuta |
| `build()` con la stessa integrazione | riuscita in 1,02 s, `astro:routes:resolved` e `astro:build:done` (11 rotte) | riuscita in 2,32 s; `astro:build:done` dà 0 rotte e le pagine | fallita in 0,45 s su `broken.astro` (errore del compilatore) |

`sync` dell'API JavaScript con l'hook `astro:routes:resolved` è documentato, non avvia l'app, non fa il build e non carica le pagine: dà per ogni rotta il file e il tipo, non i metodi di un endpoint (le esportazioni `GET` e `POST` le ha lo snapshot, come per Next.js).

## Aperto

- **Le rotte di Astro.** Proposta, nulla nel codice: uno script di Daodan che chiami `sync` con un'integrazione in linea, dopo il ripristino dei pacchetti, in una sorgente come `nextjs.py`. `astro.config.*` è codice del progetto e gira nel container.
- **La funzione che il gestore chiama.** Nessuno strumento ufficiale dice quale funzione il globale della pagina tiene sotto un nome (`transform` di `@astrojs/compiler` dice quali `<script>` elabora, senza le posizioni delle dichiarazioni). Il passo successivo è il dinamico: l'esplorazione nel browser preme i controlli e isola il gestore (`daodan/core/dynamic/app.py`, `observed_entries.py`), misurata su un'app React in [project-model](../project-model/README.md), «Esplorazione dell'app avviata»; su un progetto Astro non è misurata.
- **Le forme fuori dal registro:** nei collegamenti solo `onclick` è una forma nota; `onsubmit` e `oninput` non vi entrano.
- **Un progetto Astro vero:** nessuno è stato misurato; non si sa quanti gestori `on*` in una stringa abbia un progetto reale.
- **Limiti dichiarati:** `new Thing()` e un template con tag non sono righe né lacune; un attributo `on*` che Astro non dichiara (`onend` di SMIL) non è letto; `<svg:rect>` e `<a.b>` non sono elementi per compiler-rs; solo le diagnostiche di gravità `error` contano; 600 secondi divisi fra le cartelle.
- **Non provati:** Astro 4 (`@astrojs/compiler` ^2.10) e Node 18; pnpm o Yarn con pacchetti non alla radice; una diagnostica che non sia un errore; `Astro.slots`, `define:vars`.
