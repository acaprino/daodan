# Daodan: prototipo business

Aprire `index.html` nel browser del container Daodan. Asset, Inter e componenti SmoothUI sono locali; non servono server o rete. Browser, benchmark, exporter e build si eseguono esclusivamente nel container; i comandi riproducibili sono in [standalone-app](../../benchmarks/standalone-app/README.md).

Percorso: URL GitHub → verifica accesso → login solo se richiesto, con riprova dello stesso URL → branch → pre-mappa con tecnologie e alberi → analisi senza obiettivo → sintesi e grafo. Nessuna scelta pubblico/privato. L'obiettivo facoltativo appartiene alla review e al suo perimetro di moduli, funzioni e file/cartelle.

**È una demo:** login GitHub, selezione, avanzamento e costruzione progressiva del grafo non eseguono OAuth, clone, modelli o analisi. L'inventario proviene dai file Git tracciati e dai manifesti locali; il grafo e il finding di review hanno provenienza storica distinta. Scegliere un'altra repository non cambia questi dataset dimostrativi.

Per provare l'accesso usare URL `https://github.com/` seguiti da:

- `acaprino/daodan`: accessibile senza login, branch dalla cache locale.
- `organizzazione-demo/progetto-privato`: prima richiede login, poi apre lo stesso URL.
- `organizzazione-demo/non-disponibile`: resta inaccessibile anche dopo login; controllare URL e permessi.
- `organizzazione-demo/errore-rete`: errore di connessione simulato, ripetibile senza login.

Gli altri URL validi aprono una demo generica: esistenza, accessibilità e visibilità non sono verificate in rete. URL, esito e login simulato persistono al reload; modificare l'URL annulla le operazioni pendenti. I vecchi salvataggi con scelta pubblico/privato richiedono una nuova verifica.

## Riproduzione

- Nel container, `uv run --no-project --with-requirements plugins/codebase-map/skills/map/scripts/requirements.txt python -B prototypes/daodan-app/scripts/export_premap_preview.py` aggiorna inventario e JSON incorporato nella pagina. Linguaggi, tecnologie e versioni dichiarate vengono da Daodan (snapshot di `plugins/`, step `stack`, toolchain della pre-mappa); file, unità e versioni delle dipendenze da Git e dai manifest.
- Per ricompilare SmoothUI nel container, eseguire `npm ci` e `npm run build` nella cartella `smoothui`.
- Il benchmark browser e i parametri misurati sono in [standalone-app](../../benchmarks/standalone-app/README.md).

`smoothui/src` adatta gli originali AI Task List e Animated Stepper; fonti e tema Candy sono in `smoothui/registry`. Licenza SmoothUI MIT e licenza Inter sono conservate accanto agli asset. `node_modules` e screenshot di verifica non sono versionati.
