# Next.js: un record di `next analyze` dice che `pay` è un'azione del server?

**Stato:** In parte. `next analyze` è provato e non è nel prodotto: la sua esportazione dice che un modulo ha almeno un'azione e da quale pagina è raggiunto, non quale funzione né dove. Nel prodotto la funzione `"use server"` la dà Noir (`kind: server-action`, classificata «nessun ingresso» in `daodan/data/entry-queries.json`). Aperto: nessuno strumento di Next.js dice, per funzione, che gira sul server.

## Domanda

L'esportazione di `next analyze` (Turbopack, `-o`, poi `next analyze export`) nomina, per il modulo `app/checkout/actions.ts`, qualcosa che distingua una funzione `"use server"`: un `ident`, un record, o un `server-reference-manifest.json` scritto dall'analisi? Spec: [ingressi e scoperta dei flussi](../../docs/specs/2026-11-20-ingressi-e-scoperta-dei-flussi.md), sezione 6, «Il legame dal pulsante alla funzione `"use server"` e dove gira» (task 13a del piano). `next analyze` compila l'intera app: gira solo su Modal.

## Strumento e parametri

Next.js 16.4.6 (`@next/swc-linux-x64-gnu`), Noir 1.5.0 (url e sha256 di `daodan/core/premap/noir.py`). Misurato su Modal il 23 novembre 2026.

- Fixture: [`benchmarks/system-map/real-paths/next-shop`](../system-map/real-paths/next-shop) (`typedRoutes: true`, `app/checkout/actions.ts` con `"use server"` e `pay` alla riga 3, `app/checkout/page.tsx` con `<form action={pay}>`), pacchetti dal suo `package-lock.json`.
- Immagine `node:24-bookworm` (node v24.22.3, npm 11.19.1), 2 CPU, 4096 MB, rete bloccata, 600 secondi per comando; `npm_config_offline=true`, `NEXT_TELEMETRY_DISABLED=1`.
- Varianti, ognuna in una copia della fixture:

| Variante | Comandi |
| --- | --- |
| `typegen` | `next typegen`, con l'elenco di `.next/` |
| `intact` | `next analyze -o --snapshot probe`, `next analyze export --snapshot probe`, poi `--route <chiave>` per le chiavi di `route-summaries.json` che contengono `checkout` |
| `no-directive` | gli stessi, con `"use server";` tolto da `actions.ts` |
| `noir` | `noir scan <copia senza pacchetti> -f json --no-log`, come `premap/noir.py` |

```
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal modal run benchmarks/next-server-actions/modal_probe.py
```

`VARIANTS=intact,no-directive` ne sceglie alcune. `results/` tiene `00_env.json`, `typegen.json`, `noir.json` e `diff.json` (tutti i record che differiscono fra le due esportazioni); le due esportazioni intere (2,5 MB l'una) non sono in git: la sonda le riscrive.

## Risultato

Tutti i comandi escono con 0. Le esportazioni di tre giri sulla stessa fixture sono identiche byte per byte: i record che differiscono vengono dalla direttiva.

| Comando | Tempo | Picco di memoria (`ru_maxrss` del processo più grande) |
| --- | --- | --- |
| `next typegen` | 1,3 s | 223 MiB |
| `next analyze -o --snapshot probe` | 2,8 s con la direttiva, 2,7 s senza | 800 MiB, 839 MiB |
| `next analyze export --snapshot probe` (1,5 MB di JSON Lines) | 0,8 s | 158 MiB |
| `… --route /checkout` (0,65 MB) | 0,8 s | 157 MiB |
| `noir scan` | 0,7 s | 149 MiB |

- **Nessun manifest su disco.** `.next/` ha 77 file in entrambe le varianti, nessun `server/`, nessun `server-reference-manifest.json`. L'esportazione lo nomina come uscita con la sola dimensione (287 byte con la direttiva, 30 senza).
- **`typegen` non dice nulla dell'azione:** scrive 5 file in `.next/types`, nessuno nomina `checkout/actions` né `use server`.
- **La direttiva lascia una traccia di modulo e di rotta, non di funzione.** Dei record (4676 con la direttiva, 4671 senza) 20 stanno solo con la direttiva e 15 solo senza. Con la direttiva il modulo caricatore `.next-internal/server/app/checkout/page/actions.js … (server actions loader, ecmascript)` porta nell'`ident` `{ ACTIONS_MODULE0 => "[project]/app/checkout/actions.ts [app-rsc] (ecmascript)" }` e ha `actions.ts` fra le dipendenze; senza, le dipendenze sono vuote. Il caricatore c'è anche per le pagine senza azioni: distingue l'insieme delle sue dipendenze, non la sua presenza. Il record `output` della rotta `/checkout` lega la rotta al caricatore.
- **Il nome `pay`, la riga e l'`id` dell'azione non sono in nessun record.** Dal sorgente di Next.js (tag `v16.4.6`, commit `54b876b6`, `crates/next-api/src/server_actions.rs`): il nome esportato e l'`id` stanno nel testo del modulo caricatore (`build_server_actions_loader`, righe 121-171) e nel manifest (`ServerActionManifestAsset`, righe 175-383), che `analyze` nomina e non scrive. Chi decide che un modulo ha azioni legge il commento `__next_internal_action_entry_do_not_use__` (righe 777-815, 1010-1042), API interna. Lo stesso insieme comprende le azioni di `"use cache"`, distinte da un bit dell'`id` che l'esportazione non porta (letto, non misurato).
- **Noir dà la funzione.** Due endpoint (`results/noir.json`): `POST /api/pay` e `POST /pay` con `kind: "server-action"`, `handler` `{name: "pay", path: app/checkout/actions.ts, line: 3}`: file, nome e riga della dichiarazione. Non dà la pagina `/checkout` né `/orders/[id]`.

I nomi `server actions loader`, `next-flight-loader/server-reference.js` e `action-validate.js` sono interni di Turbopack, non lo schema `graph-v1`: nessun lettore è stato scritto su di loro.

## Aperto

- Aperta: da approfondire. Uno strumento ufficiale di Next.js che dica, per funzione, che gira sul server. Restano fuori `next build` (escluso dal proprietario) e il commento della trasformazione SWC (API interna, non valutata).
- Una funzione `"use server"` in linea in un componente, un file con più azioni, una funzione a freccia o `export default`, una direttiva in un `.tsx`, un'azione importata da un componente client: la sonda ha una sola forma. Non si sa se il caricatore le nomini allo stesso modo, né se Noir le dia con nome e riga.
- Che il `symbol` della riga di Noir sia quello che la scheda del pulsante raggiunge nella pipeline (da scip-typescript): confrontato solo con la dichiarazione.
- `next analyze` su un progetto vero (qui 908 moduli), con Webpack, con `distDir` diverso, con più pagine che raggiungono la stessa azione.
- Se il passo dinamico osserva la chiamata dal pulsante all'azione: non misurato.
