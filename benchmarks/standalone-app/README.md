# Confini dell'app standalone

Prova di riuso per la [spec dell'app](../../docs/specs/2026-11-16-app-standalone.md). Esercita `MapService` e il server HTTP esistenti su un progetto temporaneo, senza modificare il repository analizzato e senza processi figli.

## Esecuzione e parametri

```powershell
python -B benchmarks/standalone-app/probe.py --repeat 3 --requests 4 --out benchmarks/standalone-app/results.json
```

- `--repeat`: cicli indipendenti di avvio/arresto, da 1 a 10; default 3.
- `--requests`: richieste map/review per ciclo, da 1 a 10; default 4.
- Due consumer concorrenti provano il claim della stessa coda.
- `--out`: file JSON dei risultati; senza, stampa soltanto.

Le asserzioni verificano import del nucleo senza UI/SDK MCP, HTTP autonomo, loopback e token, rifiuto di un'origine estranea, persistenza e lettura delle richieste, claim unico, rilascio, completamento e chiusura di thread/socket. Ogni tentativo di avviare un processo fa fallire la prova.

## Risultati misurati

16 novembre 2026, Windows, Python 3.13.14; risultato completo in `results.json`.

| Parametri | Esito misurato |
| --- | --- |
| 3 cicli, 4 richieste per ciclo, 2 consumer concorrenti | 9 controlli superati complessivamente; 12 richieste chiuse, nessun claim duplicato |
| Chiusura dopo ogni ciclo | Thread terminato e socket chiuso in tutti e 3 i cicli |
| Durata complessiva della prova | 2,477 s; misura descrittiva, non un obiettivo prestazionale |

## Percorso UI

```powershell
python -B benchmarks/standalone-app/ui_flow.py
```

Richiede il [prototipo versionato](../../prototypes/daodan-app/README.md), Playwright per Python e Chrome installato nel percorso Windows usato dallo script. Nessuna credenziale GitHub o API key.

Parametri: viewport desktop 1440×1000 e mobile 390×844, timer originali della demo da 2.200 ms accelerati con `clock.run_for`, senza riscrivere lo stato per simulare l'avanzamento. `ui-results.json` registra i controlli e l'hash della pagina; gli screenshot locali sono esclusi da Git.

La prova segue repository/branch, pre-mappa, alberi, avvio senza obiettivo, crescita del grafo, pausa, ripristino e sintesi; controlla inoltre l'obiettivo facoltativo e il perimetro della review. Login GitHub, dati privati e branch alternativi sono dimostrazioni esplicite.

Misura del 16 novembre 2026: **44/44 controlli superati**, nessun errore runtime o richiesta esterna, nessun overflow a 1440/390 px. La crescita osservata è 0 nodi/0 archi → 3/3 → 10/23 → 18/43; pausa e ripristino conservano il grafo. Il processo termina con codice diverso da zero se un controllo fallisce. Dettagli e hash della pagina in `ui-results.json`.

## Limiti

Le prove validano il confine già esistente e il prototipo, non implementano il launcher o un coordinatore. Nessuna esecuzione LLM, clone, OAuth reale, analisi completa, cancellazione di processi, ripresa di sessioni o chiamata a provider API. Il mobile è una viewport Chrome, non un dispositivo fisico. La corrispondenza del grafo e la correttezza dei reviewer hanno benchmark propri.
