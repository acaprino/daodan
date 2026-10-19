# Analisi Ancorata al Grafo, Choicer Dinamico e Review a Due Modalità: specifica di disegno

Data: 19 ottobre 2026. Specifica architetturale e di implementazione per
massimizzare la qualità dell'analisi, della pianificazione e della verifica in
Daodan, azzerando fraintendimenti, dipendenze rotte, bug e riscritture, e
allocando in modo intelligente modelli e livello di `thinking` (`effort`) lungo
il ciclo. Si innesta sul disegno del ciclo chiuso
(`docs/superpowers/specs/2026-10-18-closed-loop-harness-design.md`), sulla
superficie a 22 comandi di `daodan`
(`docs/superpowers/specs/2026-10-19-command-set-design.md`) e sulle evidenze
della prima prova dal vivo
(`docs/superpowers/reports/2026-10-19-closed-loop-probe-claude.md`).

Valgono tutte le convenzioni del repository: kernel sotto `plugins/`, adapter
sotto `adapters/`, tutto il resto generato; sola standard library Python;
nessuna dipendenza locale opzionale; nessuna costruzione a inciso tra trattini.

---

## 1. Principio guida: qualità dell'analisi prima di tutto

L'obiettivo primario **non è risparmiare qualche centesimo tagliando i controlli**,
ma **costruire un flusso di analisi e lavoro così preciso da evitare alla radice
fraintendimenti, codice sbagliato, regressioni sui chiamanti e bug non visti**.
L'efficienza sui token è la conseguenza naturale del non dover rifare il lavoro
due volte, non una scorciatoia sulla qualità.

La catena che garantisce questo risultato poggia su cinque pilastri:

1. **Grafo e Sourcemap (`codebase-map`: `manifest.sqlite`, `cards.sqlite`, `edit-impact`)**:
   prima di decidere o toccare qualsiasi cosa, lo script estrae dal grafo
   statico la verità strutturale completa (simboli, firme, chiamanti e chiamati,
   tripli hash `body_hash` / `interface_hash` / `effects_hash`). Nessun worker
   lavora alla cieca o per tentativi.
2. **Grounding completo su Codice, ADR e tutta la Documentazione esistente (Stage A)**:
   l'analisi iniziale raccoglie non solo gli ADR attivi (`docs/adr/`), ma
   **tutti i documenti esistenti nel progetto** (`docs/`, specifiche, guide,
   `README.md`, contratti OpenAPI/Protobuf/GraphQL) che citano i file o i
   simboli coinvolti. L'intervista e la verifica di **Stage A** bloccano
   qualsiasi fraintendimento o contraddizione con la documentazione e i
   contratti esistenti **prima** che venga pianificata o scritta una sola riga
   di codice.
3. **Onde (`waves`) ordinate sulle dipendenze reali del grafo (Stage B)**:
   il piano ordina i micro-task lungo gli archi risolti della mappa (`callees`
   prima di `callers`), prepara a monte la griglia combinatoria dei casi limite
   dalla firma AST (`oracle_scaffold`) e verifica in **Stage B** che ogni task
   abbia il contesto completo, l'oracolo `RED` e le dipendenze corrette.
4. **Due sole modalità di review (`lite` e `full`) guidate da un Choicer semantico (Zero Regex cablate)**:
   spariscono i quattro tier statici (`light`, `small`, `medium`, `large`) e le
   regex cablate in Python (`SENSITIVE_PATH`, `SIGNAL_PATTERNS`,
   `LANGUAGE_BY_SUFFIX`), che rischiavano di lasciare spento il revisore giusto
   (come `security-auditor` su una nuova URL esposta in `api/invoices.py`). Il
   **Choicer** legge il diff, i fatti del grafo e i frontmatter `TRIGGER WHEN /
   DO NOT TRIGGER WHEN` di tutte le 20+ prospettive di Daodan e accende tutti e
   soli i revisori pertinenti al significato reale della modifica.
5. **Routing dinamico a 3 Tier (`tier1`, `tier2`, `tier3`) + `effort`**:
   invece di 4 fasce, bastano **al massimo 3 Tier**:
   - **`tier1`** (`#low`): Choicer, prompt improver / rewriter / `humanize-text` e operazioni meccaniche;
   - **`tier2`** (`#medium` / `#high`): il motore principale che esegue sia le task normali e i test, sia la **review `lite` e i revisori multi-lente della review `full`** (perché è proprio la struttura a grafo più la divisione in lenti specialistiche a fare il lavoro pesante senza bisogno di un modello gigante per ogni lente);
   - **`tier3`** (`#high` / `#xhigh`): riservato alla definizione delle specifiche e del piano quando l'architettura è complessa, alle singole task di codice davvero difficili (`complex`) o come escalation se un tentativo su `tier2` fallisce.

---

## 2. Scoperta dei modelli e dei livelli di thinking nei 5 harness

Ogni harness espone il catalogo dei modelli e il controllo del `thinking` in
modo diverso. Nessun kernel sotto `plugins/` contiene nomi di modelli specifici
di un host: i kernel usano **quattro profili astratti** e il binding dell'host
li traduce nei modelli reali.

### 2.1 Binding per host in `adapters/<host>/templates/operational-binding.md.tmpl`

Poiché il fallback `inherit` è sempre valido su ogni host, non serve aggiungere
una nuova capability bloccante in `CAPABILITY_REGISTRY` (`scripts/daodan/validate.py`).
Il meccanismo vive nei template `operational-binding.md.tmpl` e nella sezione
`environment.models` di `work.json`:

| Host | Strategia di binding | Meccanismo di scoperta | Meccanismo di dispatch al worker |
|---|---|---|---|
| **OpenCode V2 / Tri-Tech Code** | `catalog-and-variant` | Strumento runtime `tools.opencode.models()` (restituisce `id`, array `variants` e prezzi `cost` in USD/M token) + `~/.config/opencode/opencode.json` | Parametro `model: "providerID/modelID#variant"` sullo strumento `subagent` |
| **Claude Code** | `tier-alias` | Alias nativi dello schema `Agent` (`haiku`, `sonnet`, `opus`) + lettura di `~/.claude/settings.json` e `ANTHROPIC_DEFAULT_*_MODEL` | Parametro `model: "haiku" \| "sonnet" \| "opus"` sullo strumento `Agent` |
| **Pi** | `companion-model` | Lettura di `~/.pi/agent/settings.json` / `models.json` o `pi --list-models` | Parametro `model` di `pi-subagents` quando supportato, altrimenti `inherit` |
| **Codex** | `inherit-session` | Lettura di `~/.codex/config.toml` (`model`, `model_reasoning_effort`) | `inherit` (i subagenti inline ereditano il modello della sessione) |
| **Copilot** | `inherit-session` | Configurazione dell'host; nessuna API di catalogo esposta ai tool | `inherit` (il tool `agent` invoca il custom agent registrato) |

### 2.2 I tre Tier (`tier1`, `tier2`, `tier3`) e come funzionano anche senza controllo dell'`effort`

Non tutti gli harness e non tutti i modelli permettono di cambiare il livello di
`thinking` (`effort`), e alcuni harness (come Codex o Copilot, o un utente con
un solo modello) non permettono nemmeno di cambiare modello sui subagenti.

Per questo motivo ogni Tier non è legato solo a un flag dell'API, ma governa
**tre leve indipendenti**, applicando automaticamente quelle disponibili
sull'harness attivo:

| Tier | 1. Leva Modello (se l'host ha più modelli) | 2. Leva Effort API (solo se il modello espone `variants`) | 3. Leva Strutturale nel Pacchetto (funziona SEMPRE su ogni host) |
|---|---|---|---|
| **`tier1` (`micro` / `router`)** | Modello leggero (`haiku`, `flash-lite`) | `#low` (se supportato, altrimenti omesso) | **Output diretto senza preamboli**: prompt compatto, risposta immediata nello schema richiesto (zero ragionamento verboso in output) |
| **`tier2` (`work`, motore principale)** | Modello di lavoro (`sonnet`, `flash`) | `#medium` (se supportato, altrimenti omesso) | **Contesto chirurgico a 1 hop + griglia AST**: fetta sorgente verificata, chiamanti a 1 hop, ciclo `RED -> GREEN` o singola lente di review |
| **`tier3` (`heavy` / `deep`)** | Modello superiore (`opus`, `sonnet`, `sol`) | `#high` (se supportato, altrimenti omesso) | **Contesto espanso a 2 hop + verifica pre-modifica**: chiamanti/chiamati a 2 hop, ADR/documenti completi e obbligo di compilare la tabella di impatto sugli invarianti prima di scrivere la patch |

In questo modo:
- **Se l'harness ha modelli + `variants`** (es. OpenCode/Tri-Tech): usa tutte e
  3 le leve (`modello#effort` + pacchetto);
- **Se l'harness cambia solo il modello ma NON ha `effort`** (es. Claude Code
  con `haiku` / `sonnet` / `opus`, o modelli senza `variants`): omette `#effort`
  e usa **Modello + Leva Strutturale**;
- **Se l'harness ha un solo modello fisso (`inherit`) senza `effort`** (es.
  Codex, Copilot, o scelta dell'utente): usa la **Leva Strutturale del
  Pacchetto** (output secco su `tier1`, grafo a 1 hop su `tier2`, grafo a 2 hop
  + verifica esplicita degli invarianti su `tier3`).

### 2.3 Come Daodan scopre cosa supporta l'harness e costruisce i 3 Tier

La catena reale funziona in tre passi senza mai assumere che `effort` o più
modelli esistano:

#### Passo 1: Scoperta delle capacità reali durante `/daodan:init-project`
- **Su OpenCode V2 / Tri-Tech Code**: il Coordinatore chiama
  `tools.opencode.models()`. Per ogni modello legge `id`, `cost` e la lista
  `variants`: aggiunge `#low` / `#medium` / `#high` **solo se** quella variante
  compare effettivamente nell'array `variants` di quel modello; se `variants` è
  vuoto, usa il solo `id` del modello.
- **Su Claude Code**: usa i 3 alias nativi di `Agent` (`tier1 = "haiku"`,
  `tier2 = "sonnet"`, `tier3 = "opus"`), senza alcun suffisso `#effort`.
- **Su Pi**: legge i modelli da `~/.pi/agent/settings.json` se `pi-subagents` è
  attivo, altrimenti imposta `inherit`.
- **Su Codex e Copilot** (o quando non c'è supporto per-subagente): imposta
  automaticamente `mode = "inherit"` (nessun parametro `model` passato al
  subagente; agisce solo la Leva Strutturale del pacchetto).

#### Passo 2: Conferma dell'utente in `/daodan:init-project`
Quando l'harness offre più modelli o varianti, `/daodan:init-project` propone
la tabella a 3 righe (`tier1`, `tier2`, `tier3`) e la salva come semplice
stringa `model_ref` (già comprensiva di `#variant` solo dove supportato, oppure
`null` per `inherit`) dentro `environment.models`:

```json
{
  "host": "opencode",
  "tiers": {
    "tier1": {"model_ref": "tri-llm-gateway/gemini-3.5-flash-lite#low", "hop_depth": 1, "direct_output": true},
    "tier2": {"model_ref": "tri-llm-gateway/gemini-3.8-flash#medium", "hop_depth": 1, "direct_output": false},
    "tier3": {"model_ref": "tri-llm-gateway/claude-sonnet-5-5#high", "hop_depth": 2, "direct_output": false}
  }
}
```

Su Claude Code la stessa struttura contiene semplicemente `"model_ref": "haiku"`,
`"sonnet"`, `"opus"`; su Codex/Copilot contiene `"model_ref": null`.

#### Passo 3: Uso a runtime per ciascuna task
Durante il lavoro (`new-feature`, `fix-bug`, `refactor-code`, `review-changes`,
`review-branch`):
1. Il Choicer (`tier1`) assegna a ciascuna task o revisore l'etichetta `tier1`,
   `tier2` o `tier3`;
2. `cycle_packets.py` adatta il pacchetto della task (`hop_depth: 1` contro `2`,
   risposta JSON diretta contro verifica esplicita degli invarianti);
3. Se `model_ref` non è `null`, il Coordinatore lo passa al parametro `model`
   del subagente; se è `null` (o se il modello non è più disponibile), omette il
   parametro `model` usando il modello della sessione (`inherit`).

---

## 3. Il Choicer Dinamico e le Due Modalità di Review (`lite` e `full`)

### 3.1 Estrazione dinamica delle 20+ prospettive dai ruoli (`plugins/*/roles/*.md`)

Invece di mantenere liste di regex o di estensioni di file dentro Python,
`review_roster.py` costruisce il catalogo delle prospettive leggendo
direttamente i manifesti `plugin.toml` e i frontmatter YAML (`name`,
`description` con `TRIGGER WHEN` e `DO NOT TRIGGER WHEN`) di tutti i ruoli
registrati nei plugin obbligatori (`senior-review`, `abstraction-architect`,
`testing`, `repo-hygiene`, `react-development`, `typescript-development`,
`platform-engineering`, `python-development`, `dependency-audit`), più le lenti
di dominio selezionate da `skill-catalog`.

Per garantire che le superfici esposte e i controlli di accesso vengano sempre
intercettati anche in file con nomi ordinari (come `api/invoices.py` o
`views/users.py`), il frontmatter di
`plugins/senior-review/roles/security-auditor.md` viene precisato così:

```yaml
description: >
  Attacker-mindset pass over the target: assumes it is exploitable and proves it.
  TRIGGER WHEN: the target adds or modifies exposed URLs, routes, endpoints or public functions, reads external/user input, checks login, sessions, roles, permissions or object ownership (IDOR / data theft), or touches SQL/shell/file paths, secrets, tokens, CORS, crypto or security headers; or the user asks for a security or auth review.
  DO NOT TRIGGER WHEN: pure in-memory calculation or formatting with no external I/O, no permissions, no exposed endpoint and no sensitive data, or infrastructure-only config (use platform-reviewer).
```

L'intero catalogo delle 20+ prospettive occupa circa 550 token statici (che
restano identici tra le chiamate e sfruttano la prompt cache dell'host):
**nessun revisore viene pre-filtrato o nascosto da Python**, eliminando il
rischio che un filtro sulle estensioni nasconda `ui-race-auditor` su Python/Qt o
`.ts` oppure `security-auditor` su un controller dal nome generico.

### 3.2 Fatti strutturali preparati da Python (`review_roster.py prepare`)

Prima che il Choicer scelga, `review_roster.py prepare` raccoglie in modo
deterministico (senza regex di dominio) i fatti oggettivi dal diff e da
`snapshot.py edit-impact`:

- elenco dei file toccati con righe aggiunte/rimosse (`git diff --numstat`);
- simboli toccati e, per ciascuno, se è cambiato solo `body_hash` (`body_only`),
  oppure `interface_hash` (`interface_changed`) o `effects_hash`
  (`effects_changed`);
- identità e firme dei chiamanti e chiamati a 1 hop nel grafo di `codebase-map`;
- ADR attivi e documenti esistenti (`docs/`, `README.md`, contratti) che citano
  quei file o simboli.

### 3.3 Il Contratto del Choicer (Regola della `trigger_line`)

Il Choicer riceve il requisito, i fatti strutturali del grafo, il diff e il
catalogo completo `TRIGGER WHEN / DO NOT TRIGGER WHEN`.

Per garantire che vengano scelti **tutti e soli i revisori davvero pertinenti**
(senza né dimenticare un fronte di rischio né lanciare revisori scollegati dal
codice), ogni revisore selezionato deve indicare **`trigger_line`** (il
percorso, riga o simbolo esatto del diff o dell'artefatto che attiva il
`TRIGGER WHEN` di quel revisore):

```json
{
  "mode": "lite",
  "selected": [
    {
      "role": "senior-review:security-auditor",
      "tier": "tier2",
      "effort": "high",
      "trigger_line": "api/invoices.py:34 @router.get('/invoices/{invoice_id}')",
      "reason": "Nuova URL esposta che restituisce una fattura per ID senza verificare l'owner (rischio IDOR)"
    },
    {
      "role": "senior-review:premise-auditor",
      "tier": "tier2",
      "effort": "high",
      "trigger_line": "api/invoices.py:41 if discount >= 0",
      "reason": "Verifica dei casi limite su note di credito e sconti"
    },
    {
      "role": "testing:test-suite-auditor",
      "tier": "tier2",
      "effort": "medium",
      "trigger_line": "tests/test_invoices.py:18 def test_get_invoice",
      "reason": "Verifica che i test coprano l'accesso non autorizzato e gli importi limite"
    }
  ],
  "recommend_full_review": false,
  "recommend_full_reason": null
}
```

Differenza tra le due sole modalità:
- **Modalità `lite`** (`review-changes`, e i controlli di Stage A, Stage B e
  Stage C a fine ondata):
  1. Esegue prima tutti gli strumenti deterministici del progetto (`test`,
     `lint`, `types`, `dependency-audit` se cambia un manifesto);
  2. Il Choicer (`tier1`) seleziona i revisori mirati allo specifico target e li
     fa girare sul **`tier2`** (perché ogni revisore riceve già il pacchetto
     della mappa e deve controllare una sola lente focalizzata);
  3. Ogni finding `Critical` o `High` viene verificato da Lente 0 (premessa) e
     Lente 1 (raggiungibilità).
- **Modalità `full`** (`review-branch` e Stage D a chiusura del candidato):
  1. Costruisce o aggiorna la mappa di interconnessione e la derivazione cieca
     delle premesse;
  2. Il Choicer (`tier1`) attiva **tutte** le prospettive del catalogo che hanno
     un riscontro nel branch o nelle sue dipendenze a 1 hop: anche nella `full`
     i revisori girano di default sul **`tier2`** (con `effort = "high"` per le
     lenti più critiche), perché è proprio la struttura a grafo più la divisione
     multi-lente a rendere superfluo un modello gigante su ciascuna lente; il
     `tier3` interviene solo se il Choicer rileva un nodo architetturale o di
     sicurezza di complessità estrema;
  3. Esegue il pannello di verifica avversariale completo (Lenti 0, 1, 2, 3) e
     il Critico di Completezza.

### 3.4 Validazione deterministica (`review_roster.py check-choice`)

Lo script Python valida l'output del Choicer prima di scriverlo in `work.json`:

1. Ogni `role` in `selected` deve essere un ruolo realmente registrato nei
   `plugin.toml` del marketplace;
2. Ogni voce deve avere `trigger_line` e `reason` non vuoti, e il file o simbolo
   citato deve appartenere al candidato o al suo vicinato nella mappa;
3. Ogni revisore usa almeno `tier2` (mai `tier1`, che è riservato a Choicer e
   rewriter); se il grafo segnala che un simbolo toccato ha cambiato
   `interface_hash` o `effects_hash` con chiamanti esterni o che il revisore è
   `premise-auditor` / `security-auditor`, `effort` viene garantito almeno a
   `"high"`.

### 3.5 Selezione dinamica del Tier (`tier1`, `tier2`, `tier3`) e dell'`effort` per CIASCUNA Task

Nessuna task usa `tier1` per scrivere codice o specifiche, e non serve pagare
`tier3` dove il grafo e la scomposizione multi-lente fanno già il lavoro:

1. **Task di Choicer, Prompt Improver e Rewriter (`tier1`)**:
   - Tutte le scelte di routing interno (Choicer dei revisori, classificazione
     delle task), la riscrittura/miglioramento di prompt e `humanize-text`, più
     eventuali aggiornamenti puramente meccanici, girano su **`tier1`**
     (`effort = low`).
2. **Task di Lavoro normale, Test e Review `lite` / `full` (`tier2`)**:
   - Le task `mechanical` o `standard` nelle `waves` (scrittura test `RED` sulla
     griglia AST già pronta, implementazione `GREEN` con contesto `edit-impact`
     già estratto, adeguamento dei chiamanti) e **sia la review `lite` sia le
     lenti della review `full`** girano su **`tier2`** (`effort = medium` per i
     task facili, `effort = high` per i revisori principali o quando cambia
     un'interfaccia).
3. **Task Complesse, Specifiche Difficili ed Escalation (`tier3`)**:
   - Il **`tier3`** (`effort = high / xhigh`) viene selezionato dinamicamente
     solo per:
     - la **definizione delle specifiche e del piano** quando la richiesta tocca
       più moduli, contratti complessi o scelte architetturali non banali;
     - le singole micro-task nelle `waves` marcate `difficulty = "complex"`
       (algoritmi delicati, concorrenza, sicurezza critica, redesign);
     - l'**escalation automatica** quando una task eseguita su `tier2` fallisce
       il primo tentativo.
4. **Visibilità nella tabella del piano**:
   - Prima dell'avvio, la tabella del piano mostra per ciascuna task il Tier e
     l'`effort` assegnati (`tier1`, `tier2#medium`, `tier2#high`, `tier3#high`),
     così l'utente può confermarli o cambiarli.

---

## 4. Flusso di Lavoro Guidato dal Grafo: Zero Fraintendimenti e Zero Codice Errato

Per rispettare l'architettura delle dipendenze (`AGENTS.md`: `project-protocol`
è una foglia pura senza dipendenze locali, mentre `project-lifecycle` dipende
da `project-protocol`, `codebase-map`, `project-knowledge`, `senior-review` e
`testing`):
- **`project-protocol` (`run_state.py`, `review_roster.py`)** valida lo stato,
  legge i metadati dei ruoli, valida le scelte del Choicer e blocca i retry
  duplicati senza mai invocare `codebase-map` o `project-knowledge`;
- **`project-lifecycle` (`plugins/project-lifecycle/skills/lifecycle-method/scripts/cycle_packets.py`)**
  orchestra `snapshot.py`, `adr_tool.py` e `run_state.py` per il preflight, il
  grounding documentale e la generazione dei pacchetti completi per i worker.

### 4.1 Definizione delle Specifiche: Grounding su Codice, ADR e Documentazione esistente + Stage A

La definizione delle specifiche prima del codice è il passaggio più importante
dell'intero ciclo: se la specifica è incompleta o ambigua, qualsiasi worker a
valle scriverà codice o test sbagliati. Per azzerare i fraintendimenti:

1. **Grounding automatico (`cycle_packets.py preflight` e `interview.md`)**:
   prima di fare domande o scrivere proposte, lo script estrae da
   `snapshot.py edit-impact` le firme e i chiamanti/chiamati reali dei simboli
   coinvolti e cerca nell'inventario di `codebase-map` (`DOC_EXTENSIONS` e file
   di contratto) **tutte le pagine di documentazione e specifica esistenti**
   (`docs/`, specifiche funzionali, guide, `README.md`, schemi
   OpenAPI/Protobuf/GraphQL) che citano quei path o quei simboli, affiancandole
   agli ADR attivi (`adr_tool.py resolve`) e alle istruzioni del commit base
   (`AGENTS.md`, `CLAUDE.md`).
2. **Griglia preliminare dei parametri e dei casi limite (`oracle_scaffold`)**:
   già durante la definizione delle specifiche, lo script analizza l'AST/firma
   dei simboli bersaglio ed elenca i parametri opzionali, i valori di default e
   le partizioni di input (segno, zero, valori interi sulla soglia, collezioni
   vuote), così l'intervista non dimentica mai di chiarire come il sistema deve
   comportarsi sui casi di confine (come `minimum_unit="years"` con valori
   interi negativi in `precisedelta`).
3. **Intervista Socratica ancorata e Specifica Eseguibile**:
   le domande all'utente mostrano sempre il comportamento attuale nel codice e
   nella documentazione esistente e fissano nella specifica/ADR quattro blocchi
   obbligatori prima di poter passare al piano:
   - **Perimetro (`scope`)**: file, moduli e simboli inclusi, cosa è
     esplicitamente fuori perimetro e quali documenti esistenti devono essere
     aggiornati;
   - **Esempi Eseguibili (`EX-*`)**: coppie concrete `input -> output atteso`
     per il caso nominale, per ciascun caso limite emerso dalla griglia dei
     parametri e per i casi di errore o rifiuto;
   - **Alternative Rifiutate (`RA-*`)**: le strade scartate con la motivazione,
     così nessun worker successivo le reintroduce;
   - **Invarianti (`INV-*`)**: i contratti verso i chiamanti e le proprietà che
     non devono mai rompersi.
4. **Stage A (Verifica della Specifica contro Codice, ADR e Documentazione)**:
   prima di compilare il piano delle ondate, Stage A controlla che la specifica
   prodotta:
   - non contenga premesse false sui simboli o sulle firme reali del codice;
   - non lasci casi limite scoperti rispetto alla griglia dei parametri;
   - sia coerente con gli ADR attivi e con tutta la documentazione esistente
     (o dichiari esplicitamente quali ADR soppianta e quali pagine di `docs/`
     aggiorna).
   Finché la specifica non supera Stage A ed è approvata dall'utente, nessuna
   task di pianificazione o codifica può partire.

### 4.2 Stage B: Piano `waves` ordinato sulle dipendenze (`callees -> callers`) e Griglia `oracle_scaffold`

Per evitare codice errato, riscritture a effetto domino e test deboli:
1. **Ordinamento topologico sulle dipendenze reali della sourcemap**: i
   micro-task in `waves` seguono gli archi risolti di `codebase-map` partendo
   dai simboli chiamati (`callees`) e salendo verso i chiamanti (`callers`).
   Ogni chiamante viene modificato solo quando la firma e il comportamento del
   chiamato sono già definitivi e verificati coi test verdi.
2. **Griglia combinatoria dei casi limite (`oracle_scaffold`)**: per ogni
   simbolo bersaglio, `cycle_packets.py` analizza la firma in `sem_declarations`
   e la fetta sorgente verificata di `edit-impact` (con `ast.parse` per Python e
   pattern di firma per gli altri linguaggi), estraendo parametri, valori di
   default e costanti confrontate nel corpo, e genera la matrice obbligatoria
   dei casi limite (`segno/zero/intero sulla soglia/frazionario x ciascun
   parametro opzionale non-default`, come `minimum_unit="years"` su valore
   intero negativo in `precisedelta`).
3. **Stage B (Verifica del piano)**: `plan-check` verifica l'isolamento dei
   `write_set` e la presenza degli oracoli `RED`; la review del piano controlla
   che ogni simbolo e chiamante citato esista nella mappa, che l'ordine
   rispetti le dipendenze e che la griglia dei casi limite sia coperta.

### 4.3 Esecuzione assistita da Pacchetti Completi e Controllo Post-Task sugli Archi

Per evitare che un worker scriva codice sbagliato per mancanza di contesto o
per errori di trascrizione del coordinatore:
1. **Pacchetti completi su disco (`cycle_packets.py task-packet`)**: lo script
   compila `.daodan/runs/<id>/packets/<task_id>.md` (usando le intestazioni e i
   codici chiusi `OK`, `NEEDS_REPLAN`, `ORACLE_INVALID` di `worker-brief.md`)
   con l'obiettivo, gli esempi `EX-*`, gli invarianti `INV-*`, gli estratti di
   ADR e documentazione esistente, la griglia dei casi limite, le fette di
   codice sorgente verificate dei simboli in `write_set`, le firme e le card
   dei chiamanti e chiamati a 1 hop dalla mappa e i comandi `RED`/`GREEN`.
2. **Controllo immediato delle dipendenze post-task (`cycle_packets.py post-task`)**:
   appena il worker restituisce `OK`, lo snapshot incrementale confronta i
   tripli hash (`body_hash`, `interface_hash`, `effects_hash`):
   - se è cambiato `interface_hash` o `effects_hash` e un chiamante a 1 hop
     nella mappa non è stato aggiornato o previsto nelle ondate successive, lo
     script segnala immediatamente il chiamante rotto prima del commit;
   - lo stesso vale per i pacchetti dei revisori (`review_roster.py
     check-choice --emit-packets DIR`), che ricevono il requisito originale, gli
     estratti di ADR/documentazione, il diff, l'output dei tool e il pacchetto
     `edit-impact`, senza la prosa auto-assolutoria del worker.

### 4.4 Preflight in una chiamata, Flag CLI piatti e Guardia Anti-Riciclo

1. **Transazione unica `cycle_packets.py preflight`**: esegue in un colpo solo
   le 9 sonde (git, `.venv`, provider richiesti, freschezza della mappa, ADR e
   documentazione esistente sullo scope), bloccando all'istante ambienti non
   inizializzati o con plugin disabilitati.
2. **Flag CLI piatti su `run_state.py update`** (`--set-phase`,
   `--set-delivery`, `--set-gate`, `--set-task`, `--seal-wave`): eliminano la
   scrittura manuale di JSON tramite heredoc bash (causa di 7 errori su 12 nella
   prova).
3. **Stop meccanico ai retry ciechi (`Failure Fingerprinting`)**: se un worker
   fallisce un test, `run_state.py` calcola l'impronta
   `sha256(sorted_failing_test_ids + touched_symbols + exception_class)`. Al 1°
   errore, rigenera il pacchetto allargando il grafo da 1 hop a 2 hop e alza
   il tier/effort di un gradino (`tier2#medium -> tier2#high -> tier3#high`) così il secondo
   tentativo ha più contesto e più capacità di analisi. Se il 2° tentativo
   produce la stessa impronta, blocca il loop e riporta la diagnosi esatta.

---

## 5. Modifiche ai contratti e ai file del repository

Tutte le modifiche ai file Markdown delle skill devono rispettare o abbassare i
tetti di parole verificati da `tests/test_skill_load_budget.py` (`UNIT_CAPS` e
`STEP_CAPS`, che non possono mai essere alzati) e mantenere in `worker-brief.md`
le intestazioni e i codici di uscita richiesti da
`test_the_worker_receives_a_closed_template_not_the_methods`.

| File | Modifica |
|---|---|
| `plugins/project-protocol/contracts/work.toml` | Semplificazione di `[loop.reviews]` a due sole modalità (`modes = ["lite", "full"]`, rimozione dei 4 `tiers`); aggiunta di `trigger_line`, `tier` (`tier1 \| tier2 \| tier3`), `effort` per revisore scelto; aggiunta di `difficulty`, `tier`, `effort`, `oracle_origin` e `attempts` (con `fingerprint`) nei task di `[loop.waves]`; aggiunta di `models` (con `tiers = {tier1, tier2, tier3}`) in `[loop.environment]` |
| `plugins/project-protocol/skills/project-protocol/scripts/review_roster.py` | Rimozione delle regex cablate (`SENSITIVE_PATH`, `SIGNAL_PATTERNS`, `LANGUAGE_BY_SUFFIX`) e dei 4 tier statici; lettura dinamica dei ruoli e dei `TRIGGER WHEN / DO NOT TRIGGER WHEN` dai `plugin.toml` e `roles/*.md`; sottocomandi `prepare` (fatti del diff/mappa + catalogo completo per il Choicer) e `check-choice` (validazione di `selected`, `trigger_line`, `tier >= tier2` ed emissione pacchetti `--emit-packets DIR`) |
| `plugins/project-protocol/skills/project-protocol/scripts/run_state.py` | Flag CLI piatti su `update`; eredità automatica di `environment` dall'ultimo run di `init`; calcolo di `tier` ed `effort` per micro-task in `plan-check`; blocco sul retry con `fingerprint` duplicata; verifica dei chiamanti scoperti su `interface_hash` / `effects_hash`. Resta foglia pura senza dipendenze da altri plugin |
| `plugins/senior-review/roles/security-auditor.md` | Esplicitazione nel frontmatter `TRIGGER WHEN` di URL/route/funzioni esposte, accesso a dati per ID (IDOR / furto dati), permessi/ruoli e login/sessioni |
| `plugins/project-lifecycle/skills/lifecycle-method/scripts/cycle_packets.py` | Nuovo script di orchestrazione in `project-lifecycle`: sottocomandi `preflight` (9 sonde + ricerca di ADR e di tutta la documentazione esistente che cita lo scope), `task-packet` (con `oracle_scaffold` via `ast` sulla fetta di `edit-impact`) e `post-task` (refresh incrementale mappa e controllo delta chiamanti) |
| `plugins/project-lifecycle/skills/lifecycle-method/references/init.md` | Passo 3 esteso con la scoperta del catalogo modelli dell'host e la registrazione dei 3 Tier (`tier1`, `tier2`, `tier3`) in `environment.models` (`thinking-only`, `hybrid`, `inherit`), entro il tetto di 265 parole |
| `plugins/project-lifecycle/skills/lifecycle-method/references/preflight.md` | Sostituzione delle 9 sonde manuali con `cycle_packets.py preflight` e abbassamento del tetto parole in `tests/test_skill_load_budget.py` |
| `plugins/project-lifecycle/skills/lifecycle-method/references/interview.md` | Grounding ed Stage A estesi a tutta la documentazione esistente (`docs/`, guide, `README.md`, contratti) che cita i simboli toccati, oltre agli ADR, entro il tetto di 445 parole |
| `plugins/project-lifecycle/skills/lifecycle-method/references/waves.md` | Ordinamento `callees -> callers` dal grafo, assegnazione di `difficulty` e `tier#effort` per micro-task, uso di `cycle_packets.py task-packet` e controllo post-task dei chiamanti, entro il tetto di 515 parole |
| `plugins/project-lifecycle/skills/lifecycle-method/references/worker-brief.md` | Conserva tutte le intestazioni e i codici chiusi (`OK`, `NEEDS_REPLAN`, `ORACLE_INVALID`) come template riempito da `cycle_packets.py task-packet`, entro 300 parole |
| `plugins/senior-review/skills/review-method/references/light.md` | Allineato alla modalità `lite` con Choicer (selezione dinamica dal catalogo completo con `trigger_line` su `tier2` + Lente 0/1 su `Critical`/`High`), entro 600 parole |
| `adapters/*/templates/operational-binding.md.tmpl` | Istruzione per passare allo strumento di subagente il `model` risolto in `environment.models` (o `inherit` quando la strategia dell'host è `inherit-session`) |

---

## 6. Piano di verifica e criteri di successo

1. **Unit test deterministici (`tests/`)**:
   - `test_review_roster.py`: verifica che il catalogo venga estratto
     dinamicamente dai frontmatter `roles/*.md` senza regex di dominio cablate,
     che `check-choice` validi `selected` e `trigger_line` sui file del
     candidato per entrambe le modalità (`lite` e `full`), e che usi `tier2`
     come default anche per i revisori multi-lente della `full`;
   - `test_run_state_preflight_and_flags.py`: verifica che `preflight` catturi
     interprete `.venv`, stato git, provider, ADR e tutti i documenti esistenti
     che citano lo scope in una chiamata, e che i flag CLI piatti aggiornino
     `work.json` senza heredoc JSON;
   - `test_cognitive_router.py`: verifica l'assegnazione ai 3 Tier (`tier1`,
     `tier2`, `tier3`) e l'escalation su retry;
   - `test_failure_fingerprint.py`: verifica che al 1° errore il pacchetto si
     allarghi a 2 hop con promozione di tier/effort e che al 2° errore con la
     stessa impronta il loop venga fermato;
   - `test_oracle_scaffold.py`: verifica che per `precisedelta(value, minimum_unit="seconds", suppress=(), format="%0.2f")`
     lo scaffold generi le partizioni `segno x magnitudine intera/frazionaria x minimum_unit/suppress/format`.
2. **Gate di compilazione sui 5 host**:
   - `python scripts/daodan_build.py --check --support`
   - tutti i linter di `consistency.yml` e `tests/test_skill_load_budget.py` verdi.
3. **Prova dal vivo su `python-humanize #379`**:
   - Esecuzione completa da `/daodan:init-project` a `/daodan:finish-task`;
   - Zero fraintendimenti (intervista e Stage A ancorati a codice, ADR e
     documentazione esistente), griglia dei casi limite generata prima dei test,
     287/287 casi dell'oracolo superati al primo giro (incluso
     `minimum_unit="years"` su valori interi negativi), zero errori di quoting
     CLI e selezione chirurgica dei revisori tramite Choicer.
