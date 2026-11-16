# Daodan: prototipo business

Aprire `index.html` direttamente nel browser. Asset, Inter e componenti SmoothUI sono locali; non servono server o rete.

Percorso: repository GitHub pubblica/privata e branch → pre-mappa con tecnologie e alberi → analisi senza obiettivo → sintesi e grafo. L'obiettivo facoltativo appartiene alla review e al suo perimetro di moduli, funzioni e file/cartelle.

**È una demo:** login GitHub, selezione, avanzamento e costruzione progressiva del grafo non eseguono OAuth, clone, modelli o analisi. L'inventario proviene dai file Git tracciati e dai manifesti locali; il grafo e il finding di review hanno provenienza storica distinta. Scegliere un'altra repository non cambia questi dataset dimostrativi.

## Riproduzione

- `python -B prototypes/daodan-app/scripts/export_premap_preview.py` aggiorna inventario dichiarativo e JSON incorporato nella pagina.
- Per ricompilare SmoothUI: eseguire `npm ci` e `npm run build` nella cartella `smoothui`.
- Il benchmark browser e i parametri misurati sono in [standalone-app](../../benchmarks/standalone-app/README.md).

`smoothui/src` adatta gli originali AI Task List e Animated Stepper; fonti e tema Candy sono in `smoothui/registry`. Licenza SmoothUI MIT e licenza Inter sono conservate accanto agli asset. `node_modules` e screenshot di verifica non sono versionati.
