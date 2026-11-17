# Confini dell'app standalone

Prova di riuso per la [spec dell'app](../../docs/specs/2026-11-16-app-standalone.md). Esercita `MapService` e il server HTTP esistenti su un progetto temporaneo, senza modificare il repository analizzato e senza processi figli.

## Esecuzione nel container

Browser, probe e codice importato si eseguono esclusivamente nel container Daodan. Richiede Git e un motore compatibile con Docker; l'immagine ufficiale Chromium è fissata per digest e Playwright alla versione 1.64.1. Nessuna credenziale GitHub o API key. I comandi seguenti usano un checkout revisionato e versionato: `git archive HEAD` verifica il commit, non le modifiche locali. Non eseguire gli script direttamente sull'host.

1. Creare nomi temporanei dedicati dalla radice del checkout:

   ```powershell
   $qaDir = Join-Path ([IO.Path]::GetTempPath()) ('daodan-qa-' + [guid]::NewGuid().ToString('N'))
   $qaContainer = 'daodan-qa-' + [guid]::NewGuid().ToString('N')
   $qaPrepare = 'daodan-prepare-' + [guid]::NewGuid().ToString('N')
   $qaImage = 'daodan-standalone-qa:' + [guid]::NewGuid().ToString('N')
   if (Test-Path -LiteralPath 'DAODAN_EXECUTION_CANARY') { throw 'Canary già presente sull’host: verificare la causa prima di proseguire' }
   New-Item -ItemType Directory -Path $qaDir
   ```

2. Preparare l'archivio senza eseguire codice del progetto:

   ```powershell
   git archive --format=tar --output="$qaDir/source.tar" HEAD prototypes/daodan-app benchmarks/standalone-app plugins/codebase-map/skills/map/scripts benchmarks/scope-resolution/app/packages/orders/pricing.py
   ```

3. Preparare l'immagine senza codice del progetto; l'installazione avviene nel container:

   ```powershell
   $qaBase = 'mcr.microsoft.com/playwright/python:v1.64.1-noble@sha256:330d401ae23c905896a0c26c66c36fc971b621519e7b11b435a8328d7bf6e031'
   docker pull $qaBase
   docker create --name $qaPrepare $qaBase python -m pip install --no-cache-dir playwright==1.64.1
   docker start -a $qaPrepare
   if ((docker inspect --format '{{.State.ExitCode}}' $qaPrepare) -ne '0') { throw 'Preparazione fallita: nessun ripiego host' }
   docker commit $qaPrepare $qaImage
   docker rm $qaPrepare
   ```

4. Copiare il sorgente ed eseguire entrambe le prove senza rete o mount dell'host:

   ```powershell
   docker create --name $qaContainer --network none --memory 3g --memory-swap 3g --cpus 2 --pids-limit 512 --shm-size 512m --cap-drop ALL --security-opt no-new-privileges $qaImage sh -lc 'mkdir -p /work /out && tar -xf /tmp/source.tar -C /work && cd /work && python -B benchmarks/standalone-app/fixtures/execution_canary.py && python -B benchmarks/standalone-app/probe.py --repeat 3 --requests 4 --out /out/results.json && python -B benchmarks/standalone-app/ui_flow.py --out /out/ui-results.json --artifacts /out/screenshots'
   docker cp "$qaDir/source.tar" "${qaContainer}:/tmp/source.tar"
   docker start -a $qaContainer
   $qaExit = docker inspect --format '{{.State.ExitCode}}' $qaContainer
   ```

5. Recuperare soltanto le evidenze e rimuovere il container dedicato:

   ```powershell
   docker cp "${qaContainer}:/out/." $qaDir
   docker cp "${qaContainer}:/work/DAODAN_EXECUTION_CANARY" $qaDir
   docker rm $qaContainer
   docker rmi $qaImage
   if (Test-Path -LiteralPath 'DAODAN_EXECUTION_CANARY') { throw 'Canary apparso sull’host: verificare il confine di esecuzione' }
   if ($qaExit -ne '0') { throw "Benchmark fallito (exit $qaExit); evidenze in $qaDir" }
   ```

Il canary è un file del progetto che scrive un segno quando eseguito: deve comparire soltanto nelle evidenze copiate dal container. L'assenza del segno nel checkout host prima e dopo controlla che archivio e trasferimenti non abbiano eseguito il sorgente.

Questo percorso è stato eseguito con Kiri in WSL 2. Non richiede il builder: nella prova locale `docker build` ha completato l'installazione ma fallito l'esportazione con `Internal: input/output error`. La preparazione sopra ha invece prodotto l'immagine effettivamente usata dalle prove.

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

## Percorso UI

La stessa esecuzione nel container esercita il [prototipo versionato](../../prototypes/daodan-app/README.md) con Chromium standard di Playwright. `--out` sceglie il JSON dei risultati e `--artifacts` la directory degli screenshot; i default rimangono locali al checkout del container.

Parametri: viewport desktop 1440×1000 e mobile 390×844, timer originali della demo da 2.200 ms accelerati con `clock.run_for`, senza riscrivere lo stato per simulare l'avanzamento. `ui-results.json` registra i controlli e l'hash della pagina; gli screenshot locali sono esclusi da Git.

La prova segue repository/branch, pre-mappa, alberi, avvio senza obiettivo, crescita del grafo, pausa, ripristino e sintesi; controlla inoltre l'obiettivo facoltativo e il perimetro della review. Login GitHub, dati privati e branch alternativi sono dimostrazioni esplicite. I contatori visualizzati devono coincidere con il JSON incorporato e con `assets/premap-preview.json`, senza valori congelati nel test.

Le regressioni coprono `constructor/nested/probe.ts`, `__proto__/probe.ts` e `toString/probe.ts`; invalidazione del retry per cambio branch, ritorno al branch iniziale e logout; annullamento degli avvii e delle aperture pre-mappa pendenti. La calcolatrice confronta risultati e importi visualizzati con `pricing.py` eseguito in Python: include 1,25 €/10%, 100 €/10%, 200 €/10%, frazioni e sconto completo. L'helper monetario verifica anche pareggi, 1.005, valori negativi e grandi valori finiti. Nessuna riscrittura dello stato di avanzamento; soltanto l'inventario viene sostituito temporaneamente per la fixture dell'albero.

Misura del 16 novembre 2026 nel container Linux: **52/52 controlli superati**, Chromium 156.0.8078.4, nessun errore runtime o richiesta esterna, nessun overflow a 1440/390 px. Prima delle correzioni, gli stessi 52 controlli hanno prodotto 8 fallimenti attesi; dopo le correzioni, tutti passano. Per 1,25 €/10% la UI mostra 1,38 € e 1,23 €, come Python. Il canary ha scritto il marker soltanto nel container; assente sull'host prima e dopo la prova.

Le precedenti **44/44** su Windows riguardano un dataset e un hash HTML precedenti e rimangono misure storiche. Il processo termina con codice diverso da zero se un controllo fallisce; `ui-results.json` registra hash della pagina, ambiente, conteggi e prove puntuali.

Conferma del 17 novembre 2026 sullo stesso commit `f992db5609c72cd8bdc0d0d9c5da8696acade82a`: **52/52 controlli UI passati**, Chromium 156.0.8078.4, container Daodan su Kiri 0.2.1. Rete disabilitata, nessun mount host, limiti di 3 GiB, 2 CPU, 512 processi e 512 MiB di memoria condivisa; canary assente dal checkout host prima e dopo. Nessuna nuova misura LLM.

## Limiti

Le prove validano il confine già esistente e il prototipo, non implementano il launcher o un coordinatore. Nessuna esecuzione LLM, clone, OAuth reale, analisi completa, cancellazione di processi, ripresa di sessioni o chiamata a provider API. Il mobile è una viewport Chromium, non un dispositivo fisico. La corrispondenza del grafo e la correttezza dei reviewer hanno benchmark propri.
