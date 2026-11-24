# Guardia dell'host: l'avvio del server e dell'hook

**Stato:** In uso. Le due prove si rieseguono su Modal; il test che resta nelle suite è `tests/test_codebase_map_launch.py`.

**Domanda.** Le righe di comando con cui l'host avvia il plugin (`plugins/codebase-map/.mcp.json`, `plugins/codebase-map/hooks/hooks.json`) possono eseguire codice del progetto analizzato sull'host, contro la regola invalicabile di `AGENTS.md`? Si misura che cosa `uv` e Claude Code fanno davvero con quelle righe, per ogni insieme di opzioni.

**Risultato valido oggi** (16 novembre 2026, Modal, Linux): `uv` esegue l'interprete del `.venv` del progetto con ogni insieme di opzioni provato tranne `--python <percorso di un interprete>` e `--directory <plugin>`. Nessun modello è usato. Windows non è misurato.

## Parametri

| Prova | Cosa varia | Comando |
|---|---|---|
| `uv_options.py::test_options` | ciò che il progetto contiene (un `.venv` con un interprete, un `.python-version` con un percorso o con una versione assente, `uv.toml` e `pyproject.toml` illeggibili) per sei insiemi di opzioni, a cache vuota | `python tests/modal_pytest.py -q -s benchmarks/host-guard/uv_options.py` |
| `uv_options.py::test_starts` | avvii successivi con una sola cache | lo stesso |
| `modal_host_launch.py` | un plugin di prova il cui server registra riga di comando, cartella di lavoro e variabili; `claude mcp list` dalla cartella del progetto e da una sottocartella, senza chiamare un modello | `modal run benchmarks/host-guard/modal_host_launch.py` |

## Risultati misurati

uv 0.11.28, avviato nella cartella del progetto:

- con `--no-config --no-project` esegue `.venv/bin/python3` del progetto; lo esegue anche con `--project <plugin>`, `--managed-python` (che poi fallisce) e `--python 3.13`;
- non lo esegue con `--python <percorso di un interprete>` né con `--directory <plugin>`, che però porta fuori dal progetto anche la cartella di lavoro dello script;
- con `--no-config --no-project` non legge `.python-version`, `uv.toml` e `pyproject.toml` del progetto;
- cerca un interprete solo finché lo script non ha un ambiente nella sua cache: lo esegue al primo avvio e con lo script a un nuovo percorso (un aggiornamento del plugin), non al secondo avvio né dopo una modifica del testo dello script.

Claude Code 2.1.322:

- avvia il server stdio di un plugin nella cartella da cui è partito;
- sostituisce `${CLAUDE_PLUGIN_ROOT}` e `${CLAUDE_PROJECT_DIR}` negli argomenti e le esporta al processo; la seconda è la cartella da cui è partito, anche quando è una sottocartella del repository;
- lascia com'è scritta una variabile non impostata; non imposta `PWD`.

## Non misurato

- Windows: `.venv\Scripts\python.exe`, e come l'host risolve un `uv` scritto senza percorso.
- L'input dell'hook: la documentazione di Claude Code dice che porta `cwd`; provarlo chiede una sessione con un modello.
- Gli altri host che leggono `hooks/hooks.json`.
