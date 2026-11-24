# Confini dell'app standalone

Prova di riuso per la [spec dell'app](../../docs/specs/2026-11-16-app-standalone.md). Esercita `MapService` e il server HTTP esistenti su un progetto temporaneo, senza modificare il repository analizzato e senza processi figli.

## Esecuzione nel container

Dalla radice del checkout, preparare un archivio del commit da verificare e un container Python dedicato.

```powershell
$qaDir = Join-Path ([IO.Path]::GetTempPath()) ('daodan-qa-' + [guid]::NewGuid().ToString('N'))
$qaContainer = 'daodan-qa-' + [guid]::NewGuid().ToString('N')
$qaImage = 'python:3.13-slim'
if (Test-Path -LiteralPath 'DAODAN_EXECUTION_CANARY') { throw 'Canary già presente nel checkout' }
New-Item -ItemType Directory -Path $qaDir
git archive --format=tar --output="$qaDir/source.tar" HEAD daodan/core benchmarks/standalone-app/probe.py benchmarks/standalone-app/fixtures/execution_canary.py
if ($LASTEXITCODE -ne 0) { throw 'Archivio non creato' }
docker create --name $qaContainer --network none --memory 3g --memory-swap 3g --cpus 2 --pids-limit 512 --shm-size 512m --cap-drop ALL --security-opt no-new-privileges $qaImage sh -ec 'mkdir -p /work /out && tar -xf /tmp/source.tar -C /work && cd /work && python -B benchmarks/standalone-app/fixtures/execution_canary.py && python -B benchmarks/standalone-app/probe.py --repeat 3 --requests 4 --out /out/results.json'
if ($LASTEXITCODE -ne 0) { throw 'Container non creato' }
try {
    docker cp "$qaDir/source.tar" "${qaContainer}:/tmp/source.tar"
    if ($LASTEXITCODE -ne 0) { throw 'Archivio non copiato' }
    docker start -a $qaContainer
    if ((docker inspect --format '{{.State.ExitCode}}' $qaContainer) -ne '0') { throw 'Probe fallito' }
    docker cp "${qaContainer}:/out/results.json" $qaDir
    if ($LASTEXITCODE -ne 0) { throw 'Risultati mancanti' }
    docker cp "${qaContainer}:/work/DAODAN_EXECUTION_CANARY" $qaDir
    if ($LASTEXITCODE -ne 0) { throw 'Canary mancante nel container' }
} finally {
    docker rm $qaContainer
    if (Test-Path -LiteralPath 'DAODAN_EXECUTION_CANARY') { throw 'Canary apparso nel checkout' }
}
```

Il probe gira senza rete e senza mount dell'host. La directory temporanea raccoglie il risultato JSON e il canary prodotto dal codice eseguito nel container.

## Probe HTTP e parametri

- `--repeat`: cicli indipendenti di avvio/arresto, da 1 a 10; default 3.
- `--requests`: richieste map/review per ciclo, da 1 a 10; default 4.
- Due consumer concorrenti provano il claim della stessa coda.
- `--out`: file JSON dei risultati; senza, stampa soltanto.

Le asserzioni verificano import del nucleo senza UI/SDK MCP, HTTP autonomo, loopback e token, rifiuto di un'origine estranea, persistenza e lettura delle richieste, claim unico, rilascio, completamento e chiusura di thread/socket. Ogni tentativo di avviare un processo fa fallire la prova.

## Risultati misurati

16 novembre 2026, container Linux, Python 3.12.3; risultato completo in `results.json`, isolamento e passaggio RED/GREEN in `container-results.json`. Esecuzione senza rete e senza mount host, con limiti di 3 GiB, 2 CPU, 512 processi e 512 MiB di memoria condivisa.

| Parametri | Esito misurato |
| --- | --- |
| 3 cicli, 4 richieste per ciclo, 2 consumer concorrenti | 9 controlli superati complessivamente; 12 richieste chiuse, nessun claim duplicato |
| Chiusura dopo ogni ciclo | Thread terminato e socket chiuso in tutti e 3 i cicli |
| Durata complessiva della prova | 1,665 s; misura descrittiva, non un obiettivo prestazionale |

La precedente misura Windows, Python 3.13.14, registrava 9 controlli in 2,477 s: è storica e distinta dall'esecuzione container corrente.

Conferma del 17 novembre 2026 sul commit `f992db5609c72cd8bdc0d0d9c5da8696acade82a`, escludendo le modifiche locali: **9/9 controlli HTTP passati** con gli stessi parametri (3 cicli, 4 richieste, 2 consumer), in 1,678 s. Python 3.13.18 su Linux, container Daodan su Kiri 0.2.1, senza rete né mount host, con limiti di 1 GiB, 2 CPU e 256 processi.

## Test delle interfacce Imago

La [suite browser](../../viewer/test/browser.mjs) esercita gli asset distribuiti dell'app e dell'esploratore. Il comando è `npm run test:ui` dalla directory `viewer/`, in un ambiente con le dipendenze del viewer e Chromium di Playwright installati.

Le misure UI in `container-results.json` appartengono al prototipo ritirato.
