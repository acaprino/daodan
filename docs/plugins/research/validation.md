# Validazione

Ultimo aggiornamento: 2026-10-27.

## Esito e perimetro

La skill `science-based-approach`, i workflow `science-research`,
`update-research` e `science-mode`, il runtime dell'archivio e l'adattamento
OpenCode sono stati verificati sul candidato corrente. Le prove automatiche usano
fixture sintetiche: non sono evidenza di qualità scientifica di paper reali.

Restano separate la riproduzione dei pacchetti, i test del loader, l'esecuzione
degli hook in un host installato e la validazione di una ricerca accademica.

## Prove automatiche

| Comando | Esito | Copertura |
|---|---|---|
| `python -m unittest discover -s tests -p test_science_research.py` | 23 test superati | Science Mode, checkpoint, archivio, revisioni, recupero, confinamento e selezione vuota |
| `node --test tests/opencode/loader.test.mjs` | 30 test superati | Loader, registrazione V2, fallback session-start, injection e assenza di contesto residuo |
| `python -m unittest discover -s tests -p test_opencode_loader.py` | 2 test superati | Suite Node dal gate Python e manifest OpenCode reale |
| `python -m unittest discover -s tests -p test_daodan_hooks.py` | 14 test superati | Contratto neutrale, host nativi/adattati/non supportati e comandi generati |
| `python -m unittest discover -s tests -p test_daodan_catalogs.py` | 17 test superati | Cataloghi, identità e loader OpenCode byte-identico al template |
| `python scripts/daodan_build.py` | Completato | Rigenerazione dei cinque host dai kernel e dagli adapter |
| `python scripts/daodan_build.py --check --support` | Da rieseguire a writer concorrente concluso | Il supporto è completo; il drift intermittente riguarda soltanto `office`, fuori dal perimetro scientifico |
| `python scripts/sync_plugin_docs.py --check` e `sync_codex_instructions.py --check` | Superati, 0 derive | Parità della documentazione e delle istruzioni |
| `python scripts/lint_dependency_graph.py`, `lint_bundled_paths.py`, `lint_plugin_registration.py`, `lint_fact_anchors.py`, `lint_host_vocabulary.py` | Tutti superati | Dipendenze, percorsi distribuiti, registrazione, fatti ancorati e vocabolario neutrale |
| `python adapters/copilot/policies/xray-guard/test_xray_guard.py` | 36/36 superati | Confinamento del guard Copilot esistente |
| `git diff --check` | Superato | Nessun errore di whitespace nel candidato |

Il test post-pointer usa deliberatamente una directory al posto della ricevuta
Markdown derivata. Verifica che il puntatore canonico resti pubblicato e che il
retry esatto ricostruisca le viste senza cambiarne i byte. Non indebolisce il
controllo del documento corrente durante `prepare_current()`.

## Probe OpenCode installato

Ambiente: OpenCode 2.1.4 su Windows, configurazione e stato isolati sotto la root
temporanea approvata. Nessuna configurazione di produzione è stata modificata.

1. Una prima probe API ha registrato `session.prompt` e ha mostrato che
   `session.created` può precedere l'attivazione del plugin. Il loader quindi non
   dipende soltanto dal bus per `session-start`: usa anche un fallback una sola
   volta al primo prompt.
2. Il pacchetto reale `exports/opencode/index.js` è stato caricato da un wrapper
   locale con `plugins = ["research"]`; `work-controller` è stato risolto come
   dipendenza obbligatoria.
3. Con `openrouter/openai/gpt-5-nano`, il comando `opencode run --standalone` ha
   completato una richiesta sintetica con risposta `OK`.
4. Il `session.context` catturato contiene una sola parte con
   `type = "text"` e contenuto che inizia `Science Mode is ON`. Questo prova
   l'esecuzione del callback e l'iniezione nel contesto primario, non soltanto
   la presenza del manifest.
5. Dopo `science_runtime.py mode off` nella stessa directory isolata, una seconda
   sessione ha completato con `OK` e il relativo `session.context` contiene zero
   parti scientifiche. ON e OFF sono quindi verificati sull'host installato.

Riferimenti del contratto V2 letto sulla tag `v2.1.4`:
[`promise/plugin.ts`](https://github.com/anomalyco/opencode/blob/v2.1.4/packages/plugin/src/promise/plugin.ts),
[`promise/session.ts`](https://github.com/anomalyco/opencode/blob/v2.1.4/packages/plugin/src/promise/session.ts),
[`core/session/prompt.ts`](https://github.com/anomalyco/opencode/blob/v2.1.4/packages/core/src/session/prompt.ts) e
[`core/session/model-request.ts`](https://github.com/anomalyco/opencode/blob/v2.1.4/packages/core/src/session/model-request.ts).

## Limiti e verifiche aperte

- La probe riguarda OpenCode CLI 2.1.4. Non copre OpenCode Desktop, Claude,
  Codex, Copilot o Pi in esecuzione installata.
- Non è stata osservata o approvata una finestra di fiducia dell'host.
- I test scientifici non eseguono ricerca online, lettura di paper, valutazione
  di retrazioni o esperimenti empirici reali. Tali esiti restano da produrre
  quando il comando viene usato su una domanda concreta.
- Le prove complete del repository, i linter e il drift gate finale sono
  riportati qui soltanto dopo la loro esecuzione sul candidato finale.
