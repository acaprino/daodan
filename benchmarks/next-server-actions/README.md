# Next.js: un record di `next analyze` dice che `pay` è un'azione del server?

Domanda: l'esportazione di `next analyze` (Turbopack, `-o`, poi `next analyze export`) nomina, per il modulo `app/checkout/actions.ts`, qualcosa che distingua una funzione `"use server"`: un `ident` che porta il livello o la marca dell'azione, un record che la nomina, o un `server-reference-manifest.json` scritto dall'analisi. Piano: [ingressi e flussi](../../docs/plans/2026-11-20-ingressi-e-flussi.md), task 13a; spec: [ingressi e scoperta dei flussi](../../docs/specs/2026-11-20-ingressi-e-scoperta-dei-flussi.md), sezione 6, «Il legame dal pulsante alla funzione `"use server"` e dove gira». `next analyze` compila l'intera app: il proprietario lo ha ammesso il 23 novembre 2026, e gira solo su Modal.

**Risultati: non misurati. La sonda è scritta e non è stata eseguita** (il 23 novembre 2026 la sessione non aveva credenziali di Modal; il file è stato solo letto dal parser di Python, mai importato). Qui sotto ci sono i parametri e il criterio, decisi prima della misura; `results/` non esiste ancora.

## Parametri

- Fixture: [`benchmarks/system-map/real-paths/next-shop`](../system-map/real-paths/next-shop) (Next.js 16.4.6, `typedRoutes: true`, `app/checkout/actions.ts` con `"use server"` e `pay`, `app/checkout/page.tsx` con `<form action={pay}>`), pacchetti dal suo `package-lock.json` (`npm ci` mentre l'immagine si costruisce, l'unico momento con la rete aperta).
- Immagine `node:24-bookworm`, 2 CPU, 4096 MB, rete bloccata, 600 secondi per comando; `npm_config_offline=true`, `NEXT_TELEMETRY_DISABLED=1`.
- Varianti, ognuna in una copia della fixture con i suoi `node_modules`:

| Variante | Comandi |
| --- | --- |
| `typegen` | `next typegen`: la base di 13a, con l'elenco di `.next/` |
| `intact` | `next --version`, `next analyze --help`, `next analyze export --help`, `next analyze -o --snapshot probe`, `next analyze export --snapshot probe`, poi `--route <chiave>` per le chiavi di `route-summaries.json` che contengono `checkout` |
| `no-directive` | gli stessi, con `"use server";` tolto da `actions.ts` (se la riga manca la sonda si ferma) |

- Registra, per ogni comando: argv, exit, standard error (la coda), tempo; per l'esportazione: il testo (tagliato a 2.000.000 di caratteri), i byte e lo sha256. Per ogni variante: i record con `checkout` in una stringa, i moduli di un passo prima e dopo, le uscite e i gruppi che ne nominano gli `ident`, il conteggio per tipo di record, l'elenco di `.next/` con le dimensioni, il testo di ogni manifest sotto `.next/server` e di `route-summaries.json`, `history.json`, `metadata.json`, e l'intestazione JSON di ogni `.data` (l'ipotesi che i primi quattro byte, big endian, ne dicano la lunghezza è registrata con il suo errore se non regge). Nessun filtro interpreta un record: i filtri tengono, il grezzo resta.

```
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal python -m modal run benchmarks/next-server-actions/modal_probe.py
```

`VARIANTS=intact,no-directive` ne sceglie alcune.

## Che cosa si decide, e come

Dal sorgente di `next@16.4.6` (letto, non eseguito): lo schema dei record (`analyze/graph-v1.schema.json`) ha per i moduli solo `ident`, `path` e dipendenze; le radici di rotta distinguono `entry_kind` (`server` o `client_bootstrap`) e portano i riferimenti client; nessun campo nomina un'azione né un'esportazione. `analyze` chiama solo `projectWriteAnalyzeData` (nativo); `server-reference-manifest.json` lo scrive `writeManifests`, che il codice JavaScript chiama solo nella compilazione di `next build` (`turbopack-build/impl.js`): che `analyze` lo scriva la parte nativa è un'ipotesi, che l'elenco di `.next/` decide.

1. L'esportazione o un'altra uscita non riesce (exit diverso da 0, nessun binding nativo, la rete): la voce chiude con la causa.
2. Gli `ident` dei moduli che nominano `checkout` sono gli stessi in `intact` e in `no-directive`, e nessun manifest è scritto: la direttiva non lascia traccia in ciò che `analyze` dà, e il punto si ferma qui, senza un lettore della direttiva.
3. Un `ident` o un record che compare solo con la direttiva: si apre il suo sorgente prima di ogni codice, e la lettura sarà del record, mai del testo del file.
4. Un `server-reference-manifest.json` scritto da `analyze`: è lo strumento, e si registra che cosa dice per `pay` (file, nome esportato, livello).

Resta fuori, per ogni esito: `typegen` (non dice nulla, letto dal sorgente), il commento `__next_internal_action_entry_do_not_use__` della trasformazione SWC (API interna, non valutata), `next build` (escluso dal compito), `typedRoutes: true` sotto `analyze` (effetto ignoto), Next.js diverso dalla 16.4.6.
