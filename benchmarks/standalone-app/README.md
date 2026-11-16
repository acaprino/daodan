# Confini dell'app standalone

Prova di riuso per la [spec dell'app](../../docs/specs/2026-11-16-app-standalone.md). Esercita `MapService` e il server HTTP esistenti su un progetto temporaneo, senza modificare il repository analizzato e senza processi figli.

## Esecuzione nel container

Browser, probe e codice importato si eseguono esclusivamente nel container Daodan. Richiede Git e un daemon Docker disponibile; Chromium e Playwright 1.64.1 sono installati nell'immagine del [Dockerfile](Dockerfile). Nessuna credenziale GitHub o API key. I comandi seguenti usano un checkout revisionato e versionato: `git archive HEAD` verifica il commit, non le modifiche locali. Non eseguire gli script direttamente sull'host.

1. Creare nomi temporanei dedicati dalla radice del checkout:

   ```powershell
   $qaDir = Join-Path ([IO.Path]::GetTempPath()) ('daodan-qa-' + [guid]::NewGuid().ToString('N'))
   $qaContainer = 'daodan-qa-' + [guid]::NewGuid().ToString('N')
   New-Item -ItemType Directory -Path $qaDir
   ```

2. Preparare l'archivio senza eseguire codice del progetto:

   ```powershell
   git archive --format=tar --output="$qaDir/source.tar" HEAD prototypes/daodan-app benchmarks/standalone-app plugins/codebase-map/skills/map/scripts benchmarks/scope-resolution/app/packages/orders/pricing.py
   ```

3. Costruire l'immagine; l'installazione avviene nel container:

   ```powershell
   docker build -f benchmarks/standalone-app/Dockerfile -t daodan-standalone-qa benchmarks/standalone-app
   ```

4. Copiare il sorgente ed eseguire entrambe le prove senza rete o mount dell'host:

   ```powershell
   docker create --name $qaContainer --network none --memory 3g --cpus 2 --pids-limit 512 --cap-drop ALL --security-opt no-new-privileges daodan-standalone-qa sh -lc 'mkdir /work /out && tar -xf /tmp/source.tar -C /work && cd /work && python -B benchmarks/standalone-app/probe.py --repeat 3 --requests 4 --out /out/results.json && python -B benchmarks/standalone-app/ui_flow.py --out /out/ui-results.json --artifacts /out/screenshots'
   docker cp "$qaDir/source.tar" "${qaContainer}:/tmp/source.tar"
   docker start -a $qaContainer
   $qaExit = docker inspect --format '{{.State.ExitCode}}' $qaContainer
   ```

5. Recuperare soltanto le evidenze e rimuovere il container dedicato:

   ```powershell
   docker cp "${qaContainer}:/out/." $qaDir
   docker rm $qaContainer
   if ($qaExit -ne '0') { throw "Benchmark fallito (exit $qaExit); evidenze in $qaDir" }
   ```

## Probe HTTP e parametri

- `--repeat`: cicli indipendenti di avvio/arresto, da 1 a 10; default 3.
- `--requests`: richieste map/review per ciclo, da 1 a 10; default 4.
- Due consumer concorrenti provano il claim della stessa coda.
- `--out`: file JSON dei risultati; senza, stampa soltanto.

Le asserzioni verificano import del nucleo senza UI/SDK MCP, HTTP autonomo, loopback e token, rifiuto di un'origine estranea, persistenza e lettura delle richieste, claim unico, rilascio, completamento e chiusura di thread/socket. Ogni tentativo di avviare un processo fa fallire la prova.

## Risultati misurati

La precedente misura del 16 novembre 2026 su Windows, Python 3.13.14, è storica e non valida il runtime container corrente.

| Parametri | Esito misurato |
| --- | --- |
| 3 cicli, 4 richieste per ciclo, 2 consumer concorrenti | 9 controlli superati complessivamente; 12 richieste chiuse, nessun claim duplicato |
| Chiusura dopo ogni ciclo | Thread terminato e socket chiuso in tutti e 3 i cicli |
| Durata complessiva della prova | 2,477 s; misura descrittiva, non un obiettivo prestazionale |

## Percorso UI

La stessa esecuzione nel container esercita il [prototipo versionato](../../prototypes/daodan-app/README.md) con Chromium standard di Playwright. `--out` sceglie il JSON dei risultati e `--artifacts` la directory degli screenshot; i default rimangono locali al checkout del container.

Parametri: viewport desktop 1440×1000 e mobile 390×844, timer originali della demo da 2.200 ms accelerati con `clock.run_for`, senza riscrivere lo stato per simulare l'avanzamento. `ui-results.json` registra i controlli e l'hash della pagina; gli screenshot locali sono esclusi da Git.

La prova segue repository/branch, pre-mappa, alberi, avvio senza obiettivo, crescita del grafo, pausa, ripristino e sintesi; controlla inoltre l'obiettivo facoltativo e il perimetro della review. Login GitHub, dati privati e branch alternativi sono dimostrazioni esplicite. I contatori visualizzati devono coincidere con il JSON incorporato e con `assets/premap-preview.json`, senza valori congelati nel test.

Le regressioni coprono `constructor/nested/probe.ts`, `__proto__/probe.ts` e `toString/probe.ts`; invalidazione del retry per cambio branch, ritorno al branch iniziale e logout; annullamento degli avvii e delle aperture pre-mappa pendenti. La calcolatrice confronta risultati e importi visualizzati con `pricing.py` eseguito in Python: include 1,25 €/10%, 100 €/10%, 200 €/10%, frazioni e sconto completo. Il helper monetario verifica anche pareggi, 1.005, valori negativi e grandi valori finiti. Nessuna riscrittura dello stato di avanzamento; soltanto l'inventario viene sostituito temporaneamente per la fixture dell'albero.

Le precedenti **44/44** su Windows riguardano un dataset e un hash HTML precedenti. Non sono una misura della versione corrente. Il processo termina con codice diverso da zero se un controllo fallisce; `ui-results.json` registra hash della pagina, ambiente, conteggi e prove puntuali. Le nuove misure saranno riportate soltanto dopo l'esecuzione nel container.

## Limiti

Le prove validano il confine già esistente e il prototipo, non implementano il launcher o un coordinatore. Nessuna esecuzione LLM, clone, OAuth reale, analisi completa, cancellazione di processi, ripresa di sessioni o chiamata a provider API. Il mobile è una viewport Chromium, non un dispositivo fisico. La corrispondenza del grafo e la correttezza dei reviewer hanno benchmark propri.
