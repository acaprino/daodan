# Next.js: un record di `next analyze` dice che `pay` è un'azione del server?

Domanda: l'esportazione di `next analyze` (Turbopack, `-o`, poi `next analyze export`) nomina, per il modulo `app/checkout/actions.ts`, qualcosa che distingua una funzione `"use server"`: un `ident` che porta il livello o la marca dell'azione, un record che la nomina, o un `server-reference-manifest.json` scritto dall'analisi. Piano: [ingressi e flussi](../../docs/plans/2026-11-20-ingressi-e-flussi.md), task 13a; spec: [ingressi e scoperta dei flussi](../../docs/specs/2026-11-20-ingressi-e-scoperta-dei-flussi.md), sezione 6, «Il legame dal pulsante alla funzione `"use server"` e dove gira». `next analyze` compila l'intera app: il proprietario lo ha ammesso il 23 novembre 2026, e gira solo su Modal.

**Esito: il punto 3 della decisione (sotto).** La direttiva lascia una traccia nell'esportazione, ma di modulo e di rotta, non di funzione: un record `module` il cui `ident` porta `{ ACTIONS_MODULE0 => "<modulo>" } … (server actions loader, ecmascript)` e le cui `dependencies` nominano il modulo, e che con la direttiva non c'è. Il nome `pay`, la riga e l'`id` dell'azione non sono in nessun record: stanno nel testo del modulo caricatore e nel manifest, che l'analisi non esporta e non scrive. Misurato su Modal il 23 novembre 2026 con Next.js 16.4.6 (dettagli sotto); `results/` tiene le uscite.

## Parametri

- Fixture: [`benchmarks/system-map/real-paths/next-shop`](../system-map/real-paths/next-shop) (Next.js 16.4.6, `typedRoutes: true`, `app/checkout/actions.ts` con `"use server"` e `pay` alla riga 3, `app/checkout/page.tsx` con `<form action={pay}>`), pacchetti dal suo `package-lock.json` (`npm ci` mentre l'immagine si costruisce, l'unico momento con la rete aperta).
- Immagine `node:24-bookworm` (node v24.22.3, npm 11.19.1), 2 CPU, 4096 MB, rete bloccata, 600 secondi per comando; `npm_config_offline=true`, `NEXT_TELEMETRY_DISABLED=1`. Noir si scarica nell'immagine con l'url e lo sha256 che `daodan/core/premap/noir.py` fissa (1.5.0).
- Varianti, ognuna in una copia della fixture con i suoi `node_modules` (salvo `noir`):

| Variante | Comandi |
| --- | --- |
| `typegen` | `next typegen`: la base di 13a, con l'elenco di `.next/` |
| `intact` | `next --version`, `next analyze --help`, `next analyze export --help`, `next analyze -o --snapshot probe`, `next analyze export --snapshot probe`, poi `--route <chiave>` per le chiavi di `route-summaries.json` che contengono `checkout` |
| `no-directive` | gli stessi, con `"use server";` tolto da `actions.ts` (se la riga manca la sonda si ferma) |
| `noir` | `noir --version`, `noir scan <copia senza pacchetti> -f json --no-log` (come `premap/noir.py`), con le righe numerate di `actions.ts` e `page.tsx` |

- Registra, per ogni comando: argv, exit, standard error (la coda), tempo, picco di memoria residente (`wait4`: il processo più grande dell'albero del comando, `npx`, `node`, il binding nativo; non la loro somma né il picco del container); per l'esportazione: il testo (tagliato a 2.000.000 di caratteri), i byte e lo sha256. Per ogni variante: i record con `checkout` in una stringa, i moduli di un passo prima e dopo, le uscite e i gruppi che ne nominano gli `ident`, il conteggio per tipo di record, l'elenco di `.next/` con le dimensioni, il testo di ogni manifest sotto `.next/server` e di `route-summaries.json`, `history.json`, `metadata.json`, e l'intestazione JSON di ogni `.data` (i primi quattro byte, big endian, ne dicono la lunghezza: l'intestazione si legge come JSON, tagliata a 4000 caratteri); per `typegen` il testo di ogni file di `.next/types`. `diff.json` è la differenza d'insieme fra tutti i record delle due esportazioni, ed è ciò su cui si regge l'esito: `filtered.named` si ferma a 200 record in entrambe le varianti, e il confronto degli `ident` che la sonda stampa è tagliato. Nessun filtro interpreta un record: i filtri tengono, il grezzo resta.
- Il container non ha rete, e un risultato oltre il limite in linea di Modal si carica con la rete: la prima esecuzione è fallita così (`ClientConnectorDNSError`) dopo aver eseguito tutto. `probe` è ora un generatore che restituisce la risposta di ogni variante deflate, in pezzi da 1 MB.

```
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal modal run benchmarks/next-server-actions/modal_probe.py
```

`VARIANTS=intact,no-directive` ne sceglie alcune.

## Che cosa si decide, e come

Dal sorgente di `next@16.4.6` (letto, non eseguito): lo schema dei record (`analyze/graph-v1.schema.json`) ha per i moduli solo `ident`, `path` e dipendenze; le radici di rotta distinguono `entry_kind` (`server` o `client_bootstrap`) e portano i riferimenti client; nessun campo nomina un'azione né un'esportazione. `analyze` chiama solo `projectWriteAnalyzeData` (nativo); `server-reference-manifest.json` lo scrive `writeManifests`, che il codice JavaScript chiama solo nella compilazione di `next build` (`turbopack-build/impl.js`): che `analyze` lo scriva la parte nativa è un'ipotesi, che l'elenco di `.next/` decide.

1. L'esportazione o un'altra uscita non riesce (exit diverso da 0, nessun binding nativo, la rete): la voce chiude con la causa.
2. Gli `ident` dei moduli che nominano `checkout` sono gli stessi in `intact` e in `no-directive`, e nessun manifest è scritto: la direttiva non lascia traccia in ciò che `analyze` dà, e il punto si ferma qui, senza un lettore della direttiva.
3. Un `ident` o un record che compare solo con la direttiva: si apre il suo sorgente prima di ogni codice, e la lettura sarà del record, mai del testo del file.
4. Un `server-reference-manifest.json` scritto da `analyze`: è lo strumento, e si registra che cosa dice per `pay` (file, nome esportato, livello).

Resta fuori, per ogni esito: `typegen` (non dice nulla, letto dal sorgente), il commento `__next_internal_action_entry_do_not_use__` della trasformazione SWC (API interna, non valutata), `next build` (escluso dal compito), Next.js diverso dalla 16.4.6.

## Risultati (Modal, 23 novembre 2026)

Next.js 16.4.6 (`@next/swc-linux-x64-gnu`), Noir 1.5.0. Tutti i comandi escono con 0.

Il picco è il `ru_maxrss` del processo più grande dell'albero del comando, in MiB; il container ha 4096 MB, e `os.cpu_count()` dentro dice 18 contro i 2 CPU chiesti (`00_env.json`): i tempi non sono di due core. Le esportazioni dei tre ultimi giri (run di sviluppo della sonda, stessa fixture) sono identiche byte per byte (`stdout_sha256` di `intact` `f80e5655…` e di `no-directive` `a16d9d83…`): i 35 record che differiscono vengono dalla direttiva, non dal caso. Tempi e picchi qui sotto sono dell'ultimo giro, quello che `results/` tiene:

| Comando | Tempo | Picco di memoria |
| --- | --- | --- |
| `next typegen` | 1,3 s | 223 MiB |
| `next --version`, `analyze --help`, `analyze export --help` | 0,7 s | 157 MiB |
| `next analyze -o --snapshot probe` | 2,8 s con la direttiva, 2,7 s senza | 800 MiB, 839 MiB |
| `next analyze export --snapshot probe` (1,5 MB di JSON Lines) | 0,8 s | 158 MiB |
| `… --route /checkout` (0,65 MB) | 0,8 s | 157 MiB |
| `noir scan` | 0,7 s | 149 MiB |

`analyze` con `typedRoutes: true` non fallisce e non scrive `.next/types` (lo scrive `typegen`: 5 file, `results/typegen.json` ne tiene il testo; la rotta `/api/pay` e la pagina `/checkout` ci sono, nessun file nomina `checkout/actions` né `use server`).

**Nessun manifest su disco.** `.next/` ha 77 file in entrambe le varianti (cache di Turbopack e `diagnostics/analyze/`), nessun `server/`, nessun `server-reference-manifest.json`. L'esportazione nomina il file come uscita (`coverage: not_a_chunk`, nessun modulo) e come `part` con la sola dimensione: 287 byte con la direttiva, 30 senza. Il contenuto non c'è. Il punto 4 non si verifica.

**La differenza.** Dei record delle due esportazioni (4676 con la direttiva, 4671 senza) 20 stanno solo con la direttiva e 15 solo senza (`diff.json`; `exports_whole: true`). I moduli (908 contro 905):

| Solo con la direttiva | Solo senza |
| --- | --- |
| `.next-internal/server/app/checkout/page/actions.js { ACTIONS_MODULE0 => "[project]/app/checkout/actions.ts [app-rsc] (ecmascript)" } [app-rsc] (server actions loader, ecmascript)`, con `dependencies.sync` = il modulo `actions.ts [app-rsc]` e la sua variante `<locals>` | `.next-internal/server/app/checkout/page/actions.js [app-rsc] (server actions loader, ecmascript)`, `dependencies` vuote |
| `app/checkout/actions.ts [app-rsc] (ecmascript)` con `dependencies.sync` = `next/dist/build/webpack/loaders/next-flight-loader/server-reference.js` e `…/action-validate.js` (che compaiono come moduli solo qui) | lo stesso modulo, `dependencies` vuote |

Il modulo caricatore c'è anche per le pagine senza azioni (`.next-internal/server/app/page/actions.js … (server actions loader, ecmascript)`, `dependencies` vuote): chi distingue è l'insieme delle sue `dependencies`, non la sua presenza. Il record `output` della rotta `/checkout` lega la rotta al caricatore.

**Il sorgente aperto** (Next.js, tag `v16.4.6`, commit `54b876b6`, lo stesso che nomina `.next/cache/turbopack/v16.4.6-54b876b6`): `crates/next-api/src/server_actions.rs`.

- `build_server_actions_loader` (righe 121-171) scrive, per ogni pagina, un modulo virtuale `.next-internal/server/app{page_name}/actions.js` con il modificatore `server actions loader`: una riga `export {<nome> as '<id>'} from 'ACTIONS_MODULE<i>'` per ogni azione raggiungibile dalla pagina, e la mappa `ACTIONS_MODULE<i> => <modulo>` va nell'`ident`. Da qui il suffisso che si vede. Il nome esportato e l'`id` sono nel testo del modulo, non nell'`ident`; il record `part` del caricatore ha la sola dimensione.
- `ServerActionManifestAsset` (righe 175-383) è il manifest: per ogni azione un campo `exported_name` (il nome nel JSON scritto non è stato letto), `filename` (il sorgente `.ts`, se il commento lo ha) e i `workers` per pagina. È un `OutputAsset` che `analyze` nomina e non scrive.
- Chi decide che un modulo ha azioni è `map_server_actions` (righe 1010-1042: i moduli raggiungibili nei livelli `app-rsc`, `app-edge-rsc`, `app-route`, `app-edge-route`, `app-client`) con `parse_actions` e `parse_server_actions` (righe 777-815): legge il commento `__next_internal_action_entry_do_not_use__` che la trasformazione scrive, lo stesso che il piano esclude.
- Lo stesso insieme di azioni alimenta il caricatore e il manifest, e comprende anche quelle di `"use cache"`: le distingue un bit dell'`id` (`extract_type_from_server_reference_id`, righe 1050-1061), che l'esportazione non porta. Un caricatore non dice quindi `"use server"` in particolare (letto nel sorgente, non misurato: la fixture non ha `"use cache"`).

Quindi un record dell'esportazione dice, di un modulo, che ha almeno un'azione e da quale pagina è raggiunto; non dice quale funzione né dove. Il nome del caricatore (`server actions loader`, `.next-internal/server/app/…/actions.js`) e le dipendenze `next-flight-loader/server-reference.js` e `action-validate.js` sono nomi interni di Turbopack e della trasformazione, non lo schema `graph-v1`: il secondo segnale è osservato, non letto nel sorgente.

**Noir.** `noir scan` su una copia della fixture senza pacchetti dà due endpoint (`results/noir.json`): `POST /api/pay` (`technology: js_nextjs`, `kind` vuoto, `handler` `POST` alla riga 1 di `app/api/pay/route.ts`) e `POST /pay` con `kind: "server-action"`, `handler` `{name: "pay", path: app/checkout/actions.ts, line: 3}` e `code_paths` alla riga 3. La riga 3 di `actions.ts` è `export async function pay() {`: il file, il nome e la riga sono quelli della dichiarazione. I campi che `tests/test_codebase_map_premap_noir.py` (`test_a_noir_server_action_is_no_entry_and_no_route_of_the_flows`) scriveva a mano per le due righe (`protocol`, `url`, `method`, `kind`, `handler.path`, `handler.line`, `handler.name`) coincidono con quelli misurati su Noir 1.5.0. Da `noir.rows` (letto, non eseguito qui; il test, non eseguito qui, asserisce solo `path`, `shape` e `kind` di quella riga) ne escono `site` `app/checkout/actions.ts:3`, `symbol` `app/checkout/actions.ts::pay`, `kind` «nessun ingresso». Noir non dà la pagina `/checkout` (non è un endpoint) né `/orders/[id]`.

## Non verificato

- Una funzione `"use server"` in linea nel corpo di un componente, un file con più azioni, una funzione a freccia o `export default`, una direttiva in un `.tsx`, un'azione importata da un componente client: la sonda ha una sola forma (direttiva di file, `export async function`). Non si sa se il caricatore le nomini allo stesso modo, né se Noir le dia con il nome e la riga.
- Che il `symbol` della riga di Noir sia quello della scheda «Paga» nella pipeline (la scheda arriva da scip-typescript): qui è confrontato solo con la dichiarazione.
- `next analyze` sul progetto reale (tempo e memoria dipendono dai moduli: qui 908; `container_runner.TOOLS["next"]` dà 3 GB), con Webpack (`analyze` è di Turbopack), con `distDir` diverso, con un'app con più pagine che raggiungono la stessa azione (un caricatore per pagina: non provato).
- Un secondo segnale, `next-flight-loader/server-reference.js` fra le dipendenze del modulo, non è stato letto nel sorgente di Next.js.

**Non nel repository.** Le due esportazioni intere (`results/intact.json` e `results/no-directive.json`, 2,5 MB l'una) non sono in git: la sonda le riscrive, e `results/diff.json` tiene tutti i record che differiscono fra le due.
