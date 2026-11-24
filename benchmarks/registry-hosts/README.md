# Host dei gestori di pacchetti

Prova gli host di `daodan/data/package-managers.json`, che `container.REGISTRIES` apre alla preparazione. I nomi dei gestori vengono dall'elenco di Wikipedia (revisione nel campo `source`); gli host sono scritti a memoria, quindi questa prova li raggiunge uno per uno.

## Parametri

| Prova | Cosa varia | Comando |
|---|---|---|
| `modal_probe.py` | ogni host di `REGISTRIES` attraverso il proxy della preparazione (`container.PROXY_SCRIPT`): HTTPS su `/`, o `dists/noble/Release` per un archivio `http://`; e gli host che devono restare fuori (GitHub, la sua API, Docker Hub, ghcr.io) | `python benchmarks/registry-hosts/modal_probe.py` |

Un host è raggiunto se risponde con un qualsiasi codice HTTP; non lo è se il proxy rifiuta il tunnel o non arriva risposta. Gli host fuori devono essere rifiutati.

## Risultati misurati

24 novembre 2026, su Modal (`results/2026-11-24.json`): 33 righe su 33 come atteso.

- Raggiunti 28 host: 25 HTTPS e i 3 archivi apt `http://` (`archive.ubuntu.com`, `security.ubuntu.com`, `ports.ubuntu.com`). Rispondono 200, 404 (`files.pythonhosted.org`, `static.crates.io`, `ports.ubuntu.com`), 400 (`api.nuget.org`), 403 (`cdn.cocoapods.org`, `jsr.io`: risposte del sito, non del proxy) e 302 (`conda.anaconda.org`).
- Rifiutati dal proxy 5 host che devono restare fuori: `github.com`, `api.github.com`, `raw.githubusercontent.com`, `ghcr.io`, `registry-1.docker.io`.
- Nessun host dell'elenco è stato corretto o tolto. Corretta la prova, non l'elenco: la prima esecuzione dava `conda.anaconda.org` non raggiunto perché `urllib` seguiva il suo 302 verso `anaconda.org`, che il proxy rifiuta; ora il reindirizzamento non si segue (è la risposta dell'host) e `anaconda.org` non entra nell'elenco. Il canale `conda-forge` risponde 200 su `conda.anaconda.org` (`curl`, fuori dal proxy). Corretto anche `REPO`, che nel container usciva dal percorso del file.

Prova preliminare, non ripetibile (24 novembre 2026, `curl` diretto da una sessione cloud, senza il proxy di Daodan): tutti gli host HTTPS dell'elenco hanno risposto con un codice HTTP.
