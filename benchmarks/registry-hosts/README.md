# Host dei gestori di pacchetti

Prova gli host di `daodan/data/package-managers.json`, che `container.REGISTRIES` apre alla preparazione. I nomi dei gestori vengono dall'elenco di Wikipedia (revisione nel campo `source`); gli host sono scritti a memoria, quindi questa prova li raggiunge uno per uno.

## Parametri

| Prova | Cosa varia | Comando |
|---|---|---|
| `modal_probe.py` | ogni host di `REGISTRIES` attraverso il proxy della preparazione (`container.PROXY_SCRIPT`): HTTPS su `/`, o `dists/noble/Release` per un archivio `http://`; e gli host che devono restare fuori (GitHub, la sua API, Docker Hub, ghcr.io) | `python benchmarks/registry-hosts/modal_probe.py` |

Un host è raggiunto se risponde con un qualsiasi codice HTTP; non lo è se il proxy rifiuta il tunnel o non arriva risposta. Gli host fuori devono essere rifiutati.

## Risultati misurati

Non ancora eseguita: questa sessione non ha le credenziali di Modal. L'esito andrà in `results/<data>.json`.

Prova preliminare, non ripetibile (24 novembre 2026, `curl` diretto da una sessione cloud, senza il proxy di Daodan): tutti gli host HTTPS dell'elenco hanno risposto con un codice HTTP.
