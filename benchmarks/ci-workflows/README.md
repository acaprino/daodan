# Il lettore dei workflow di GitHub

Confronta, sugli stessi workflow, il lettore di oggi (la libreria `yaml` che Renovate fissa, con le regole di `daodan/core/premap/renovate.py`) e il lettore di GitHub, `@actions/workflow-parser` (`actions/languageservices`, MIT). Passo `T3.B.4` di `docs/plans/refactoring.md`; ne dipende `T3.B.5`.

## Parametri

| Parametro | Valore |
|---|---|
| (a) | `node <renovate>/node_modules/yaml/bin.mjs --json --single --strict --merge` (il comando di `renovate.EACH`), `yaml` 2.9.1 di Renovate 44.239.1; passi letti con `renovate._directory`, `_shell`, `_env`, `_services` |
| (b) | `@actions/workflow-parser` 0.3.61 (4 agosto 2026): `parseWorkflow` (lo schema `workflow-v1.0.json` di GitHub) e `convertWorkflowTemplate`, da `workflows.mjs` |
| Node | 24.22.3, come il container di Renovate; ogni pacchetto con `--ignore-scripts` |
| Workflow | `fixtures/valid` (default di workflow e job, `working-directory`, `shell`, `env`, `if`, servizi, `container`, espressioni), `fixtures/invalid` (tre errori di schema: `run` e `uses` nello stesso passo, `runs-on` mancante, chiave sconosciuta), `mix-infra-gha` del corpus, e cinque repository reali al commit del loro `source.json`: `real-sveltekit-realworld`, `real-svc-otel-demo`, `real-bank-of-anthos`, `real-app-full-stack-fastapi`, `real-stack-plausible` |
| Campi per job | dei passi `run`, `uses`, `working-directory` (del passo, se no dei default del job o del workflow), `shell`, `env` (i nomi), `if`; servizi (nome e immagine); `container` |
| Comando | `modal run benchmarks/ci-workflows/modal_workflows.py`, risultato in `results/<data>.json` |

Nessun codice dei progetti gira: i due lettori leggono solo YAML. `workflows.mjs` aggiunge l'attributo `type: "json"` all'import dello schema che il pacchetto fa senza (Node 24 lo rifiuta, `ERR_IMPORT_ATTRIBUTE_MISSING`); nient'altro.

## Valutati e scartati prima della misura

- `act` (`nektos/act`, `pkg/model`, MIT) e `actionlint` (`rhysd/actionlint`, MIT): riscrivono il lettore in Go, non sono di GitHub.
- Lo schema di SchemaStore (`github-workflow.json`): controlla la forma, non dà il modello.
- GitLab: nessun lettore ufficiale fuori dal server (`POST /projects/:id/ci/lint` chiede un'istanza e il progetto); resta la libreria `yaml`.

## Regola di decisione (scritta prima della corsa)

**[deciso, su delega]** Vince `@actions/workflow-parser` se, insieme:

1. legge ogni workflow valido che la `yaml` legge (un modello con i job e nessun errore di schema);
2. dà, per ogni job letto da entrambi, gli stessi passi (stesso numero; `run`, `uses`, `working-directory`, `shell`, `env`, `if` uguali, con `if` uguale anche quando GitHub lo scrive `success() && (...)`) e gli stessi servizi e `container`;
3. dà gli errori di schema dei tre workflow non validi, che la `yaml` legge senza errore.

Altrimenti resta la `yaml` con le regole di `renovate.py`, e `T3.B.5` scrive il motivo accanto a `YAML` senza cambiare codice.

## Risultati misurati

28 novembre 2026, su Modal (`ap-UMH9C3wcfvSfb5VaY1a7Fw`, `results/2026-11-28.json`): Node 24.22.3, `yaml` 2.9.1, `@actions/workflow-parser` 0.3.61; 57 workflow (19 di `real-svc-otel-demo`, 15 di `real-app-full-stack-fastapi`, 15 di `real-stack-plausible`, 2 di `real-bank-of-anthos`, 2 di `mix-infra-gha`, 4 delle fixture di qui; `real-sveltekit-realworld` non ne ha), 400 passi letti da entrambi.

| Criterio | Esito |
|---|---|
| 1. ogni workflow valido letto | sì: 54 su 54, nessun job e nessun passo in meno |
| 2. stessi passi, servizi e `container` | no: `working-directory` diverso in 34 passi e `shell` in 4 (il modello convertito non li porta: né il campo del passo né `defaults`), `run` in 16 e `if` in 2 (un `${{ }}` diventa `format('…', …)`, il testo della riga non c'è più), un servizio con l'immagine da espressione (`real-stack-plausible`, `elixir.yml`: `{expr: matrix.postgres_image}` contro `${{ matrix.postgres_image }}`, stessa informazione); `uses`, `env` e `container` uguali |
| 3. errori di schema che la `yaml` non vede | sì: 3 su 3 (`Required property is missing: runs-on`, `Unexpected value 'run'`, `Unexpected value 'step'`), che la `yaml` legge senza errore; un workflow con un errore non dà nessun job, come su GitHub |

**Esito:** vince la `yaml` con le regole di `renovate.py`: il modello di GitHub perde la cartella e la shell di ogni passo e riscrive le righe con un'espressione, che sono ciò che Daodan legge di un passo (`_steps`, `_ci_steps`). Il controllo dello schema (criterio 3) resta una proposta a parte, non decisa qui: dire come lacuna un workflow che GitHub rifiuta.
