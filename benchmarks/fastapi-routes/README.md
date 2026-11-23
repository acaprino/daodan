# FastAPI: `app.openapi()` e `app.routes`

Piano, task 14a. **Stato: solo fixture e note, il 23 novembre 2026; nessuna sorgente, nessuna misura.**

## Letto dal sorgente (fastapi 0.165.0, fastapi-cli 0.0.34; wheel scaricati, non eseguiti)

- L'OpenAPI dà percorso, metodo e `operationId`, che è `route.unique_id` (`generate_unique_id`: `route.name`, percorso e metodo; `route.name` è `endpoint.__name__`, o `operation_id` se la rotta lo dichiara). Non dà modulo, file né riga: il legame operazione e funzione passa da `app.routes` (`APIRoute.unique_id` e `.endpoint`), che la spec chiama «lower-level». Un `operationId` personalizzato duplicato è una lacuna.
- L'app la trova `fastapi_cli` (`discover.get_import_data`, `config.FastAPIConfig` con `[tool.fastapi] entrypoint`): priorità percorso e `--app`, poi `entrypoint`, poi `main.py`, `app.py`, `api.py`, `app/main.py`… e i nomi `app`, `api`. Non è un'API documentata e c'è solo con `fastapi[standard]`. Alternativa da valutare: la stringa `module:app` che il progetto dichiara (`entrypoint`, o l'argomento di `uvicorn` nei comandi di avvio); senza dichiarazione, una lacuna. Non riscrivere l'auto-discovery.
- Nessun comando di `fastapi` elenca le rotte (`dev` e `run` avviano un server).

## Da misurare

Se un comando ufficiale carica l'app senza aprire una porta; che cosa danno `app.routes` e `app.openapi()` sulla fixture (`/docs`, `/redoc`, `/openapi.json`, il router incluso con prefisso, `add_api_route`, una funzione con decoratore); se `unwrap` risale alla funzione; tempo e memoria.
