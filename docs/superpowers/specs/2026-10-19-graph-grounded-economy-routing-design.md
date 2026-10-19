# Graph-Grounded Economy Execution e Router Cognitivo Dinamico: specifica di disegno

Data: 19 ottobre 2026. Specifica architetturale e di implementazione per portare
Daodan a operare con modelli economici (classe Flash/Haiku) mantenendo qualità
pari o superiore a un modello di frontiera non assistito e abbattendo i token di
esplorazione, ritrascrizione, orchestrazione e retry. Si innesta sul disegno del
ciclo chiuso (`docs/superpowers/specs/2026-10-18-closed-loop-harness-design.md`),
sulla superficie a 22 comandi di `daodan`
(`docs/superpowers/specs/2026-10-19-command-set-design.md`) e sulle evidenze
della prima prova dal vivo
(`docs/superpowers/reports/2026-10-19-closed-loop-probe-claude.md`) e della
deliberazione multi-modello (`.tritech/local/moe/20261019-economy-model-graph-loop/answer.md`).

Valgono tutte le convenzioni del repository: kernel sotto `plugins/`, adapter
sotto `adapters/`, tutto il resto generato; sola standard library Python;
nessuna dipendenza locale opzionale; nessuna costruzione a inciso tra trattini.

---

## 1. Obiettivo e principi

L'obiettivo è duplice:

1. **Qualità da modello di frontiera con modelli economici**: compensare i punti
   deboli dei modelli piccoli (orizzonte di pianificazione corto, omissione di
   casi limite sulle combinazioni di parametri, fragilità sintattica nel
   produrre JSON/shell, tendenza a scrivere test accomodanti) attraverso il
   grafo statico di `codebase-map`, pacchetti pre-compilati su disco e un router
   dinamico di modello e livello di `thinking` (`effort`).
2. **Taglio radicale dello spreco di token e dei ricicli**: eliminare le letture
   esplorative ripetute, i fraintendimenti iniziali, le riscritture a effetto
   domino, gli errori di quoting CLI e i loop di retry identici.

### La distinzione fondamentale sui grafi

Il disegno distingue due grafi che non vanno mai confusi:

- **Grafo dei Dati e dei Vincoli (`codebase-map` + `ADR` + `waves` DAG)**: deve
  essere **ricco e interrogato dagli script Python a costo zero di token**. Evita
  al modello di fare `grep` esplorativi, di dimenticare i chiamanti, di
  modificare i file nell'ordine sbagliato (`callers` prima di `callees`) e di
  ri-verificare chiamanti quando cambia solo il corpo interno (`body_hash`).
- **Grafo di Controllo dei Subagenti**: deve essere **corto e piatto**. Ogni
  nodo LLM aggiuntivo paga il cold-start del system prompt dell'host (5.000-10.000
  token) e la ritrascrizione del contesto. Gli script Python eseguono
  transazioni spesse; il modello interviene solo dove serve giudizio semantico.

---

## 2. Scoperta dei modelli e dei livelli di thinking nei 5 harness

Ogni harness espone il catalogo dei modelli e il controllo del `thinking` in
modo diverso. Nessun kernel sotto `plugins/` può cablare nomi di modelli
specifici di un host: i kernel parlano solo per **profili astratti** e gli
adapter dichiarano il meccanismo reale.

### 2.1 Binding per host in `adapters/<host>/templates/operational-binding.md.tmpl`

La selezione del modello e della variante di `thinking` non introduce una nuova
capability nel registro chiuso `CAPABILITY_REGISTRY` di
`scripts/daodan/validate.py` (che in `tests/test_daodan_adapters.py` impone la
parità stretta su tutti e cinque gli host e governa i requisiti strutturali dei
plugin): poiché il fallback `inherit` è sempre valido su ogni host, nessun
plugin diventa incompatibile quando l'override per-subagente non è disponibile.
Il meccanismo resta confinato nei template `operational-binding.md.tmpl` di
ciascun adapter e nella sezione `environment.models` del run:

| Host | Strategia di binding | Meccanismo di scoperta | Meccanismo di dispatch al worker |
|---|---|---|---|
| **OpenCode V2 / Tri-Tech Code** | `catalog-and-variant` | Strumento runtime `tools.opencode.models()` (restituisce `id`, array `variants` e prezzi `cost` in USD/M token) + `~/.config/opencode/opencode.json` | Parametro `model: "providerID/modelID#variant"` sullo strumento `subagent` |
| **Claude Code** | `tier-alias` | Alias nativi dello schema `Agent` (`haiku`, `sonnet`, `opus`) + lettura di `~/.claude/settings.json` e `ANTHROPIC_DEFAULT_*_MODEL` | Parametro `model: "haiku" \| "sonnet" \| "opus"` sullo strumento `Agent` |
| **Pi** | `companion-model` | Lettura di `~/.pi/agent/settings.json` / `models.json` o `pi --list-models` | Parametro `model` di `pi-subagents` quando supportato, altrimenti `inherit` |
| **Codex** | `inherit-session` | Lettura di `~/.codex/config.toml` (`model`, `model_reasoning_effort`) | `inherit` (i subagenti inline ereditano il modello della sessione) |
| **Copilot** | `inherit-session` | Configurazione dell'host; nessuna API di catalogo esposta ai tool | `inherit` (il tool `agent` invoca il custom agent registrato) |

### 2.2 I quattro profili cognitivi astratti

Ogni task, micro-task di ondata o review riceve uno dei quattro profili:

| Profilo | Effort predefinito | Scopo nel ciclo |
|---|---|---|
| `fast` | `low` | Sonde, riallineamento documentale meccanico, scrittura di test `RED` quando gli esempi `EX-*` e la griglia AST sono già fissati, fixture e cablaggi banali |
| `standard` | `medium` | Implementazione `GREEN` locale (`write_set` fino a 4 file, nessun cambio di interfaccia pubblica, nessun path sensibile), aggiornamenti dei chiamanti a firma già chiusa |
| `deep` | `high` | Intervista ancorata, stesura ADR, compilazione del piano DAG (`waves`) su più moduli, micro-task marcati `complex`, primo retry dopo un fallimento |
| `frontier` | `xhigh` | `premise-auditor` (Lente 0), review finale di branch su tier `medium`/`large` o `SENSITIVE_PATH`, pianificazione di modifiche ad alto impatto (>5 chiamanti o contratti pubblici), escalation dopo un retry fallito su `deep` |

### 2.3 Sonda e registrazione in `/daodan:init-project` (`references/init.md`)

Al passo 3 di `init.md` (**Environment**), oltre a `interpreter` e `commands`,
l'inizializzazione rileva la mappa dei modelli per l'harness attivo e propone
all'utente una delle tre modalità operative, registrandola direttamente nella
sezione `environment.models` del run di inizializzazione (da cui `run_state.py
init` la eredita automaticamente nei run successivi del progetto, senza creare
un secondo file di configurazione fuori da `work.json`):

1. **`thinking-only` (un solo modello, varia solo l'effort)**: tutti e quattro
   i profili usano il modello della sessione corrente cambiando solo il suffisso
   di variante dove l'host lo supporta (`#low`, `#medium`, `#high`, `#xhigh`). È
   la scelta predefinita quando l'utente vuole restare su un unico modello senza
   cambiare provider.
2. **`hybrid` (Flash per l'esecuzione, modello superiore per premesse e gate)**:
   sfrutta i prezzi e le capacità restituite dal catalogo dell'host (su
   OpenCode tramite `tools.opencode.models()`, su Claude Code tramite
   `haiku`/`sonnet`/`opus`) per associare `fast` e `standard` al modello
   economico/Flash con effort `low`/`medium`, `deep` al modello intermedio o
   Flash con effort `high`, e `frontier` al modello di punta con effort `high`/`xhigh`.
3. **`inherit` (nessun routing)**: tutti i profili valgono `inherit`. È il
   fallback automatico sugli host che non supportano override per-subagente o
   quando un modello configurato non compare più nel catalogo attivo.

Schema di `environment.models` in `work.toml`:

```json
{
  "mode": "hybrid",
  "host": "opencode",
  "profiles": {
    "fast":     {"model": "tri-llm-gateway/gemini-3.8-flash", "effort": "low"},
    "standard": {"model": "tri-llm-gateway/gemini-3.8-flash", "effort": "medium"},
    "deep":     {"model": "tri-llm-gateway/claude-sonnet-5-5", "effort": "high"},
    "frontier": {"model": "tri-llm-gateway/claude-opus-5-5", "effort": "xhigh"}
  }
}
```

---

## 3. Il Router Cognitivo Ibrido: Pavimento Python + Intra-Router Semantico

Un subagente LLM dedicato solo a fare routing pagherebbe 5.000-10.000 token di
system prompt a ogni chiamata e sottovaluterebbe proprio i bug architetturali
nascosti dentro poche righe di codice. Il routing è quindi diviso in due stadi
senza alcun subagente aggiuntivo:

### 3.1 Stadio 1: Pavimento deterministico nello script (`Hard Floor`)

Durante `plan-check` (in `run_state.py`) e durante il calcolo della review (in
`review_roster.py`), lo script calcola per ogni micro-task e per ogni review il
profilo minimo obbligatorio `profile_floor` usando solo fatti oggettivi del
grafo e del diff:

- **`fast`**: task che modifica solo file di test (`TEST_PATH`) o documentazione
  (`DOC_PATH`) con `EX-*` già presenti e nessun simbolo di produzione in
  `write_set`.
- **`standard`**: task di produzione con `write_set` $\le 4$ file, nessun match
  su `SENSITIVE_PATH`, `MANIFEST_NAME` o `CONTRACT_NAME`, nessun contratto
  esportato in `produces` e $< 5$ chiamanti a 1 hop nel pacchetto `edit-impact`.
- **`deep`**: task che modifica un simbolo con $\ge 5$ chiamanti a 1 hop,
  dichiara `produces` (modifica una firma o un contratto consumato da altri
  task), richiede `granularity_exception` (5-6 file), oppure è al tentativo
  `attempt == 2`.
- **`frontier`**: task o review che tocca `SENSITIVE_PATH` (autenticazione,
  pagamenti, persistenza/migrazioni, concorrenza, crittografia), cambia un
  manifesto o un contratto esterno, ha $\ge 20$ chiamanti (`LARGE_CALLERS`), o è
  il ruolo `senior-review:premise-auditor` nello stadio finale del candidato.

### 3.2 Stadio 2: Valutazione semantica nella skill di Plan e nel Coordinatore (`Soft Escalation`)

Il modello della sessione principale (che può essere esso stesso un modello
economico) agisce da **intra-router semantico a costo zero di turni extra** in
due momenti precisi:

1. **Nella compilazione del piano (`references/waves.md`)**: per ogni micro-task
   il pianificatore dichiara `difficulty: "mechanical" | "standard" | "complex"`
   in base alla difficoltà logica dell'intervento (ad esempio: `mechanical` per
   aggiungere un campo o una fixture, `complex` per derivare il segno di un
   intervallo su unità intere e frazionarie).
2. **All'ingresso del task o dopo un test fallito**: il coordinatore valuta se
   la richiesta in linguaggio naturale è sottospecificata o se lo stack trace
   di un fallimento indica un errore concettuale anziché un refuso.

La regola di combinazione in `run_state.py` è monotona:

$$\text{profile\_final} = \max\bigl(\text{profile\_floor},\; \text{map}(\text{difficulty}),\; \text{escalation\_retry}\bigr)$$

dove `mechanical -> fast`, `standard -> standard`, `complex -> deep`. Il modello
**può solo alzare** la potenza rispetto al pavimento calcolato dal grafo, **mai
abbassarla**. Quando `plan-check` valida il piano, risolve `profile_final` per
ogni micro-task usando `environment.models` e lo mostra all'utente nella tabella
di approvazione del piano prima che inizi l'esecuzione.

---

## 4. Cinque Interventi nel Motore per Eliminare Token Persi e Ricicli

Per rispettare la politica delle dipendenze (`AGENTS.md`: `project-protocol` è
una foglia pura senza dipendenze locali, mentre `project-lifecycle` dipende da
`project-protocol`, `codebase-map`, `project-knowledge`, `senior-review` e
`testing`), la responsabilità tra gli script resta divisa in modo netto:
- **`project-protocol` (`run_state.py`, `review_roster.py`)** valida lo stato,
  applica i flag CLI piatti, calcola `profile_floor` e i roster dai file di
  evidenza passati in ingresso (`--impact IMPACT.json`, `--diff DIFF.patch`) e
  blocca i retry con impronta duplicata, senza mai importare né invocare
  `codebase-map` o `project-knowledge`.
- **`project-lifecycle` (`plugins/project-lifecycle/skills/lifecycle-method/scripts/cycle_packets.py`)**
  orchestra le chiamate tra `snapshot.py`, `adr_tool.py` e `run_state.py` per il
  preflight unificato e per la generazione su disco dei pacchetti dei worker.

### 4.1 Transazione unica di Preflight e fine degli heredoc JSON

Nella prova 37.0.0 il coordinatore ha speso 9 chiamate shell per le sonde di
avvio e ha fallito 7 volte su 12 per errori di virgolette negli heredoc JSON
usati con `--payload`.

1. **Transazione `cycle_packets.py preflight` (in `project-lifecycle`)**:
   ```text
   python cycle_packets.py preflight --project ROOT [--run-id ID] [--scope-path PATH ...]
   ```
   Esegue in un unico processo Python:
   - verifica del repository root, `HEAD`, `git status --porcelain=v2 --branch`,
     presenza di `MERGE_HEAD` / `rebase-merge`, distanza dall'upstream;
   - scoperta automatica dell'interprete del progetto (`.venv`, `uv`, `node_modules`)
     e dei comandi dichiarati nel blocco `LOOP-HARNESS`;
   - verifica della presenza di `.codebase-map/` e `docs/adr/README.md` (se
     mancano, restituisce `status = "NEEDS_INIT"` al primo secondo invece di
     proseguire);
   - aggiornamento di `work.json` attraverso `run_state.py` con `workspace`
     (candidato), `preflight` ed `environment` (ereditando `environment.models`
     dall'ultimo run di `init` se presente), restituendo un singolo riepilogo
     compatto.
2. **Flag CLI piatti per gli aggiornamenti frequenti di `run_state.py` (in `project-protocol`)**:
   `update` guadagna flag diretti che non richiedono `--payload FILE.json`:
   ```text
   --set-phase FASE=STATO[:REASON]
   --set-delivery ID=STATO[:OUTPUT_PATH]
   --set-gate ID=STATO[:COMMAND]
   --set-task WAVE_ID:TASK_ID=STATO
   --seal-wave WAVE_ID
   ```
   `--payload FILE.json` resta supportato per le scritture strutturate (come il
   piano delle ondate), scritte sempre con lo strumento `write` dell'host e mai
   tramite heredoc bash.

### 4.2 Compilazione su disco dei Pacchetti per Worker e Revisori

Oggi il coordinatore legge l'output di `snapshot.py edit-impact`, le schede e
gli ADR nel proprio contesto e li riscrive nel prompt del worker (`worker-brief.md`),
pagando due volte i token e rischiando omissioni.

1. **`cycle_packets.py task-packet` (in `project-lifecycle`)**:
   ```text
   python cycle_packets.py task-packet --project ROOT --run-id ID --wave WAVE_ID --task TASK_ID
   ```
   Legge `work.json`, invoca `snapshot.py edit-impact` sui file in `write_set`,
   estrae gli `EX-*`, `INV-*` e `RA-*` pertinenti dall'ADR proposto e compila
   `.daodan/runs/<id>/packets/<task_id>.md` **usando esattamente le intestazioni
   e i codici di uscita chiusi (`OK`, `NEEDS_REPLAN`, `ORACLE_INVALID`) di
   `references/worker-brief.md`** (preservando il contratto verificato da
   `tests/test_skill_load_budget.py`):
   - obiettivo, `write_set:`, path protetti e profilo cognitivo risolto;
   - `examples to make pass:`, `invariants to keep:`, `rejected alternatives:` e
     la griglia dei casi limite;
   - fette di codice sorgente verificate dei simboli in `write_set` e firme/card
     dei chiamanti e chiamati a 1 hop, con i relativi tripli hash (`body_hash`,
     `interface_hash`, `effects_hash`);
   - `expected failure before the change:`, `verification after the change:` e
     `## Prior rulings in this run`.
   Il coordinatore dispaccia il worker passandogli il contenuto/percorso di
   `.daodan/runs/<id>/packets/<task_id>.md` e il percorso di uscita, senza
   ri-sintetizzare il codice.
2. **`review_roster.py --emit-packets DIR` (in `project-protocol`)**:
   Quando calcola il roster (ricevendo `--diff DIFF.patch`, `--impact IMPACT.json`
   e opzionalmente `--intent INTENT.md` e `--tools TOOLS.json`), `review_roster.py`
   scrive per ciascun revisore `.daodan/runs/<id>/packets/review-<review_id>-<role>.md`
   includendo il requisito originale (`EX-*`, `INV-*`), il diff, i risultati già
   eseguiti degli strumenti deterministici (`pytest`, `ruff`, `mypy`) e il
   pacchetto di impatto della mappa, **escludendo la prosa del worker che ha
   scritto la patch**, così l'indipendenza epistemica è garantita dallo script.

### 4.3 Griglia Meccanica dei Casi Limite (`oracle_scaffold`) e Regola di Split

Per evitare che un modello economico trascuri casi limite sui parametri (come
`minimum_unit="years"` su valori interi in `precisedelta`):

1. **Separazione condizionale tra `test-writer` e `implementer`**:
   - Se l'oracolo `RED` **esiste già** (un test che fallisce già sulla base o un
     riproduttore fornito nel ticket), `plan-check` permette un singolo task
     combinato (`oracle_origin = "existing"`): un solo worker verifica il `RED` e
     scrive il `GREEN`, risparmiando un cold-start.
   - Se l'oracolo **va scritto da zero** (`oracle_origin = "generated"`),
     l'autore del test `RED` (`testing:test-writer`) e l'autore della patch
     `GREEN` restano due task distinti, così il modello che implementa non può
     addomesticare il test.
2. **Generazione della griglia combinatoria dalla fetta sorgente di `edit-impact`**:
   Per ogni funzione o metodo bersaglio in `write_set`, `cycle_packets.py`
   analizza la firma dichiarata in `sem_declarations` e la fetta di codice
   sorgente verificata restituita da `snapshot.py edit-impact` (usando `ast.parse`
   della standard library per Python e i pattern di firma/token per gli altri
   linguaggi) ed estrae parametri posizionali, keyword, valori di default e
   costanti/letterali confrontati con i parametri nel corpo della funzione.
   Inserisce quindi nel pacchetto del `test-writer` una tabella obbligatoria di
   partizioni:
   - **Segno / Stato numerico**: negativo, zero, positivo, intero esatto sulla
     soglia dell'unità, frazionario multi-unità;
   - **Collezioni / Stringhe**: vuoto, singolo elemento, multiplo;
   - **Parametri opzionali non-default**: almeno un caso per ciascun parametro
     con valore di default (es. `minimum_unit != "seconds"`, `suppress != ()`,
     `format != "%0.2f"`) incrociato con la condizione del bug.
   Il `test-writer` economico deve coprire ogni riga applicabile della griglia o
   motivare perché una riga è impossibile per contratto.

### 4.4 Controllo post-modifica sugli archi del grafo e Collasso Stage C/D

1. **Verifica automatica dei chiamanti tramite triplo hash**:
   Dopo che il worker restituisce `OK` su un micro-task, `cycle_packets.py
   post-task` aggiorna lo snapshot incrementale sui file toccati e passa i delta
   (`meta_changeset_deltas`) e i chiamanti a 1 hop a `run_state.py`:
   - Se cambia solo `body_hash` (`body_only`), nessun chiamante esterno viene
     marcato come impattato.
   - Se cambia `interface_hash` o `effects_hash` e un chiamante a 1 hop non
     compare nel `write_set` dell'ondata corrente o delle ondate successive del
     piano, `run_state.py` segnala immediatamente i chiamanti scoperti prima
     del commit, forzando `NEEDS_REPLAN` senza aspettare la review finale.
2. **Allineamento di `SMALL_ROSTER` e Collasso di Stage C e Stage D per i task a singola ondata (`small`)**:
   - In `review_roster.py`, `SMALL_ROSTER` (`["senior-review:code-auditor",
     "testing:test-suite-auditor"]`) viene aggiornato per includere
     `senior-review:premise-auditor` al posto o a fianco del controllo di
     aderenza alle premesse quando il task ha esempi `EX-*` / `oracle_scaffold`,
     perché nella prova 37.0.0 su `humanize #379` (classificata `small` da
     `review_roster.py`) l'unico revisore che ha intercettato il bug su
     `minimum_unit="years"` è stato `premise-auditor` (che oggi in `small`
     compariva solo in `SUPPORT`, attivato unicamente se un altro revisore aveva
     già alzato un finding `High`/`Critical`).
   - Quando il piano ha una sola ondata (`len(waves) == 1`) e `review_roster.py`
     assegna il tier `small`, non si eseguono due review separate sullo stesso
     diff (Stage C `light` seguita immediatamente da Stage D `branch`): si
     registra in `reviews` un'unica review `branch` di tier `small` (`stage =
     "candidate"`) che esegue prima gli strumenti deterministici del progetto
     (`test`, `lint`, `types`) e poi il roster `small` unificato. In
     `run_state.py`, `validate_waves` richiede che ogni task di un'ondata
     `sealed` sia `committed`, quindi un'unica voce in `reviews` per l'ondata
     unica soddisfa pienamente `validate_waves` e `validate_reviews`.

### 4.5 Guardia meccanica anti-riciclo (`Failure Fingerprinting`)

Ogni tentativo fallito di un micro-task registra in `work.json` (dentro la
storia dei tentativi del task in `waves`) l'impronta:

```json
{
  "attempt": 1,
  "profile": "standard",
  "effort": "medium",
  "fingerprint": "sha256(sorted_failing_test_ids + touched_symbols + exception_class)",
  "diagnostic": "AssertionError in test_precisedelta_negative_minimum_unit_years"
}
```

Regole imposte da `run_state.py`:
1. Al **1° fallimento**, per il tentativo 2 lo script rigenera il pacchetto
   allargando il contesto della mappa da 1 hop a 2 hop e promuove
   automaticamente `profile` di un gradino (`fast -> standard -> deep -> frontier`).
2. Se il **2° tentativo** produce la **stessa `fingerprint`** del 1° tentativo
   (o se fallisce anch'esso), `run_state.py` rifiuta un 3° tentativo cieco e
   ferma il task chiedendo o una ripianificazione (`NEEDS_REPLAN`) o l'intervento
   dell'utente con la diagnostica esatta.

---

## 5. Modifiche ai contratti e ai file del repository

Tutte le modifiche ai file Markdown delle skill devono rispettare o abbassare i
tetti di parole verificati da `tests/test_skill_load_budget.py` (`UNIT_CAPS` e
`STEP_CAPS`, che non possono mai essere alzati) e mantenere in `worker-brief.md`
le intestazioni e i codici di uscita richiesti da
`test_the_worker_receives_a_closed_template_not_the_methods`.

| File | Modifica |
|---|---|
| `plugins/project-protocol/contracts/work.toml` | Aggiunta di `difficulty`, `profile`, `effort`, `oracle_origin` e `attempts` (con `fingerprint`) nei task di `[loop.waves]`; aggiunta della sottosezione opzionale `models` in `[loop.environment]` |
| `plugins/project-protocol/skills/project-protocol/scripts/run_state.py` | Flag CLI piatti su `update`; eredità automatica di `environment` dall'ultimo run di `init`; calcolo di `profile_floor` e risoluzione di `profile_final` in `plan-check` (con `--impact IMPACT.json` opzionale); blocco sul retry con `fingerprint` duplicata; verifica dei chiamanti scoperti su `interface_hash` / `effects_hash`. Resta foglia pura senza dipendenze da altri plugin |
| `plugins/project-protocol/skills/project-protocol/scripts/review_roster.py` | Inclusione di `senior-review:premise-auditor` in `SMALL_ROSTER`; calcolo di `profile` ed `effort` per ciascun ruolo del roster; flag `--emit-packets DIR`; regola di review unica (`stage = "candidate"`) quando `waves == 1` e `tier == "small"` |
| `plugins/project-lifecycle/skills/lifecycle-method/scripts/cycle_packets.py` | Nuovo script di orchestrazione nel proprietario del ciclo (`project-lifecycle`): sottocomandi `preflight`, `task-packet` (con `oracle_scaffold` via `ast` sulla fetta sorgente di `edit-impact`) e `post-task` (refresh incrementale della mappa e passaggio dei delta a `run_state.py`) |
| `plugins/project-lifecycle/skills/lifecycle-method/references/init.md` | Passo 3 esteso con la scoperta del catalogo modelli dell'host e la registrazione di `environment.models` (`thinking-only`, `hybrid`, `inherit`), restando entro il tetto di 265 parole |
| `plugins/project-lifecycle/skills/lifecycle-method/references/preflight.md` | Sostituzione delle 9 sonde manuali con la chiamata unica a `cycle_packets.py preflight` e abbassamento del relativo tetto in `tests/test_skill_load_budget.py` |
| `plugins/project-lifecycle/skills/lifecycle-method/references/waves.md` | Assegnazione di `difficulty` per micro-task, approvazione del piano con colonna `profile#effort`, uso di `cycle_packets.py task-packet` e regola di review unica per `waves == 1` e `small`, restando entro il tetto di 515 parole |
| `plugins/project-lifecycle/skills/lifecycle-method/references/worker-brief.md` | Conserva tutte le intestazioni e i codici chiusi (`OK`, `NEEDS_REPLAN`, `ORACLE_INVALID`) come template riempito da `cycle_packets.py task-packet`, restando entro 300 parole |
| `adapters/*/templates/operational-binding.md.tmpl` | Istruzione per passare allo strumento di subagente il `model` risolto in `environment.models` (o `inherit` quando la strategia dell'host è `inherit-session`) |

---

## 6. Piano di verifica e soglie di accettazione

1. **Unit test deterministici (`tests/`)**:
   - `test_run_state_preflight_and_flags.py`: verifica che `preflight` catturi
     interprete `.venv`, stato git e provider mancanti in una chiamata e che i
     flag CLI piatti aggiornino `work.json` senza file JSON intermedi;
   - `test_cognitive_router.py`: verifica il calcolo monotono
     `max(profile_floor, difficulty, retry_escalation)` su task `mechanical`,
     `standard`, `complex`, path sensibili, cambi di interfaccia e retry;
   - `test_failure_fingerprint.py`: verifica che due tentativi con la stessa
     impronta vengano bloccati da `run_state.py` e che il primo fallimento
     promuova il profilo e allarghi il pacchetto a 2 hop;
   - `test_oracle_scaffold.py`: verifica che per `precisedelta(value, minimum_unit="seconds", suppress=(), format="%0.2f")`
     lo scaffold generi le partizioni `segno x magnitudine intera/frazionaria x minimum_unit/suppress/format`.
2. **Gate di compilazione sui 5 host**:
   - `python scripts/daodan_build.py --check --support`
   - tutti i linter di `consistency.yml` verdi.
3. **Prova dal vivo su `python-humanize #379` (criterio di successo)**:
   - Esecuzione da `/daodan:init-project` a `/daodan:finish-task` con routing
     attivo;
   - 287/287 casi dell'oracolo superati (incluso `minimum_unit="years"` su
     valori interi negativi);
   - $\le 25$ turni totali, $\le 70$ tool call totali, $0$ errori di quoting
     heredoc/JSON, costo $< 10$ USD (meno di un terzo dei 30,90 USD della
     prima prova) nel braccio ibrido e $< 3$ USD nel braccio Flash.
