# Daodan come harness a ciclo chiuso: disegno e contesto completo

Data: 18 ottobre 2026. Record di disegno della ristrutturazione di Daodan in un
harness di sviluppo a ciclo chiuso. Questo documento è il contesto autorevole
per chi riprende il lavoro: contiene la diagnosi con le sue evidenze, le
decisioni con le loro motivazioni, i contratti, il piano di attuazione per
ondate e lo stato al giorno della stesura. Il piano complementare
[economy-model-vibe-cycle-harness](../plans/2026-10-18-economy-model-vibe-cycle-harness.md)
copre il lato `codebase-map` (pacchetti di impatto, card, nuovi linguaggi) e
resta distinto: qui si disegna il ciclo che consuma quel lavoro.

Le convenzioni del repository valgono per intero: kernel sotto `plugins/`,
adapter sotto `adapters/`, tutto il resto generato; Python standard library;
nessuna dipendenza locale opzionale; nessuna costruzione a inciso tra trattini.

## 1. Intento

Daodan deve diventare l'harness che accompagna un progetto lungo tutto il suo
ciclo di vita, con un modello economico al posto di guida. La tesi, da
verificare e non da assumere, è che un modello economico dentro Daodan
raggiunga o superi un modello di frontiera usato a mano, perché Daodan gli
toglie il lavoro in cui quel modello fallisce: trovare il punto giusto nel
codice, ricordare chi dipende da cosa, accorgersi che una modifica ha rotto un
contratto, giudicare il proprio lavoro senza eco.

Quattro proprietà definiscono il risultato:

1. **Un ciclo lineare**: inizializzazione del progetto, poi per ogni task un
   giro completo (preparazione, intervista, decisione, piano, esecuzione,
   revisione, integrazione, riallineamento), poi di nuovo dall'inizio.
2. **Ogni comando è eseguibile anche da solo**, fuori dal ciclo: una review di
   un diff, di un documento, di un piano o di una specifica; un ADR; un
   aggiornamento della mappa; un audit Python. Il ciclo compone, non sequestra.
3. **La review multi-prospettiva resta il centro**, con il roster completo degli
   specialisti che oggi solo `team-review` attiva, e con l'isolamento
   epistemico che la distingue da ogni altro strumento.
4. **La conoscenza resta allineata da sola**: Codebase Map, ADR, documentazione
   e istruzioni dell'agente si aggiornano alla chiusura di ogni giro, non per
   iniziativa dell'utente.

## 2. Diagnosi verificata

Ogni punto cita il file che lo dimostra. Le righe si riferiscono allo stato del
repository al commit `be43f661` più le modifiche non committate del 18 ottobre.

### 2.1 Superficie dei comandi

Il catalogo conta 19 plugin e 29 punti di ingresso. La confusione ha tre
cause, nessuna delle quali è un difetto di un singolo file:

- **Il bivio team/non team non è uno scopo dell'utente.** `codebase-map:analyze`
  e `team-analyze` costruiscono la stessa mappa; la differenza è monolite
  contro partizionato. `senior-review:code-review` e `team-review` usano
  entrambi un team di revisori; la differenza è diff contro sistema intero.
  L'utente deve scegliere un meccanismo interno invece di dichiarare cosa vuole.
- **`project-lifecycle` espone sette verbi piatti** (`assess`, `repair`,
  `change`, `verify`, `consolidate`, `handover`, `maintain`) senza un verbo di
  inizializzazione né uno di riallineamento dopo una merge.
- **Omonimie**: `project-lifecycle:maintain` (campagna di bonifica) e
  `project-knowledge:maintain` (drift documentale).

### 2.2 Il ciclo non attiva la review che Daodan possiede

`plugins/project-lifecycle/skills/lifecycle-method/references/change.md`
e `verify.md` chiamano `senior-review:review-method` con la variante
`code-review`. Quella variante seleziona dodici slot. La variante `team-review`
(`plugins/senior-review/skills/review-preparation/references/team-review.md`,
sezione Phase 0b) aggiunge `logic-integrity-auditor`, `distributed-flow-auditor`,
`chicken-egg-detector`, `api-contract-auditor`, `cleanup-auditor` completo,
`repo-hygiene:workspace-auditor`, la derivazione cieca delle premesse e la
mappa di interconnessione. Il lavoro quotidiano usa quindi la review ridotta.

### 2.3 La review scarta i documenti

`plugins/senior-review/skills/review-preparation/references/code-review.md`,
regola 6 e passo "Filter code files": i file `.md`, `.txt` e `.rst` sono
esclusi, e se non restano file di codice la review si ferma. Un piano di
implementazione, una specifica o un ADR non sono revisionabili con il motore
che è il punto di forza del progetto. La stessa variante non lega la mappa
(`.codebase-map/`) né verifica la sua freschezza prima del dispatch.

### 2.4 Python e dependency-audit fuori dal roster obbligatorio

`plugins/senior-review/plugin.toml` dichiara `react-development`,
`typescript-development` e `platform-engineering` come dipendenze obbligatorie,
e `stack-dimensions.md` ha una riga per ciascuno. `python-development` (due
ruoli, nove skill, la suite `ruff`, `mypy` o `pyright`, `vulture`,
`complexipy`, `pytest`) e `dependency-audit` non compaiono né nel manifest né
nelle dimensioni. Un diff Python non attiva lo specialista Python.

### 2.5 Densità delle skill

Le skill del ciclo sono prosa normativa in cui ogni frase è una regola e dove la
regola, la sua motivazione storica e la negazione difensiva stanno nello stesso
paragrafo. Esempio: `review-quality-gates/SKILL.md` spiega perché esiste il
cost guard dentro la regola del cost guard. Un coordinatore carica
`lifecycle-method`, `project-protocol`, `review-method`, `review-preparation` e
i loro riferimenti prima di agire: migliaia di parole da tenere come vincoli
simultanei. Un modello economico non regge questo carico; `map-method` è
l'unica skill con un budget di carico misurato (`tests/test_xray_load_budget.py`).

### 2.6 Il trasporto multi-modello fallisce in modo opaco

Nelle sei deliberazioni tentate il 18 ottobre, cinque chiamate su sette sono
terminate con `MoE request failed or delivery was incomplete`. In
`plugins/moe/skills/multi-model-deliberation/scripts/server.py` quel messaggio
copriva quattro cause diverse: risposta oltre 8000 byte, `finish_reason` non
riconosciuto, risposta fatta di chiamate a strumenti, errore di rete. L'unica
chiamata riuscita era vincolata a 3500 byte. La causa più probabile è la prima:
4096 token di output valgono fino a 16000 byte, e il flusso chiedeva al modello
di restare "entro 8000 byte", un'unità che un modello non conta.

### 2.7 Verifica statica contro esecuzione

Il compilatore prova che ogni pacchetto si rigenera dal kernel. Non prova che
un host installato abbia eseguito un ciclo. `CLAUDE.md` lo dichiara. Il rischio
è leggere `--check` verde come prova di esecuzione.

## 3. Decisioni e motivazioni

### 3.1 Il ciclo vive in `project-lifecycle`, senza nuovi plugin

`project-lifecycle` è già il proprietario di obiettivo, ambito, piano e
chiusura. Aggiungere un plugin "loop" creerebbe un secondo coordinatore con lo
stesso compito. I verbi restano quelli esistenti, con significato chiarito:

| Verbo | Nel ciclo | Da solo |
|---|---|---|
| `assess` | Fase 0: inizializzazione o diagnosi (`--init` quando mappa, registro ADR o istruzioni mancano) | Diagnosi di salute in sola lettura |
| `change` | Fasi 1-7: preparazione, intervista, ADR, piano a ondate, esecuzione, review del candidato, integrazione e riallineamento | `--plan-only` si ferma dopo il piano approvato; `--run-id` sullo stesso run riprende un piano già approvato (il flag `--resume` previsto qui è stato unificato con `--run-id` il 19 ottobre, perché il protocollo riprende già un run per identità) |
| `repair` | Variante breve di `change` per un difetto con test di riproduzione | Correzione mirata senza intervista estesa |
| `verify` | Fase 6 su un candidato | Gate completo su codice scritto a mano o su un branch |
| `consolidate` | Fase 7: promozione ADR, aggiornamento mappa, docs, istruzioni, pulizia | Riallineamento dopo una merge fatta fuori da Daodan |
| `handover`, `maintain` | Invariati | Invariati |

Non si introducono `init` e `sync` come verbi nuovi: `assess --init` e
`consolidate` coprono gli stessi casi, e due verbi in più sulla stessa
superficie sono il problema che si vuole risolvere. Il test
`validate_record` in `run_state.py` accetta solo le cinque operazioni
esistenti, e resta così.

### 3.2 Il bivio team/non team sparisce dalla scelta dell'utente

`codebase-map:analyze` decide da solo tra analista singolo e partizioni, sulla
base dell'inventario di `snapshot.py scope`. `senior-review:code-review` decide
da solo quanto allargare il roster, sulla base dei segnali del diff. I comandi
`team-analyze` e `team-review` restano come override espliciti, perché
rimuoverli romperebbe invocazioni salvate e la documentazione che li cita.

### 3.3 Il ciclo usa il detector completo di Phase 0b con due budget

`review-preparation` accetta `budget=delta|full`, indipendente dalla variante:

- `delta` a fine ondata: il detector di Phase 0b sul solo diff dell'ondata,
  con `logic-integrity-auditor` per la conformità agli esempi dell'ADR,
  `test-suite-auditor` per l'oracolo, e gli specialisti dello stack toccato.
- `full` prima della merge: le sei fasi di `team-review` sul candidato intero,
  derivazione cieca, mappa di interconnessione, pannello a quattro lenti e
  critico di completezza.

Motivazione: un budget separato dalla variante evita di duplicare la
preparazione (il lifecycle ha già un candidato legato al run) e rende la
scalata automatica, non una scelta.

### 3.4 Review di qualsiasi artefatto, ancorata al codice reale

`review-preparation` classifica il target (`--target-kind
auto|changeset|plan|spec|doc`) e per ogni tipo esegue un gate di ancoraggio
prima del dispatch: freschezza della mappa (`snapshot.py diff --verify` sui
path citati o toccati), lettura dei sorgenti reali su disco, binding del
concept index e degli ADR attivi. Un piano che cita un simbolo inesistente
viene bocciato dalla lente 0 con `file:line` reale.

Il roster per tipo:

| Tipo | Lenti |
|---|---|
| `changeset` | Phase 0b completo più specialisti di stack |
| `plan` | `premise-auditor` (ancoraggio), `test-suite-auditor` (ogni task ha un oracolo RED non tautologico), `chicken-egg-detector` più il validatore meccanico delle ondate, `abstraction-architect-agent` (secondo proprietario), specialisti dello stack toccato |
| `spec` (ADR, specifica, RFC) | `premise-auditor`, `logic-integrity-auditor`, `abstraction-architect-agent`, `test-suite-auditor` per la verificabilità dei criteri, `security`, `data-integrity`, `api-contract` quando lo scope li tocca |
| `doc` | `premise-auditor` per le affermazioni sul codice; il drift strutturale su venti dimensioni resta a `project-knowledge:maintain`, che dipende già da `senior-review` e lo compone |

Il tipo `doc` non porta i ruoli di `project-knowledge` dentro `senior-review`,
perché `project-knowledge` dipende da `senior-review` e il ciclo di dipendenze
è vietato. La direzione resta quella attuale: `project-knowledge` compone la
review, non il contrario.

### 3.5 Python e dependency-audit entrano nel roster obbligatorio

`senior-review` dichiara `python-development` e `dependency-audit`;
`project-lifecycle` dichiara `python-development`, perché ne dispaccia lo
scrittore, e raggiunge `dependency-audit` attraverso la review, perché il
linter delle dipendenze rifiuta un edge che il kernel non usa direttamente.
`stack-dimensions.md` ottiene due righe, `python` (attivazione su `.py`,
`pyproject.toml`, `uv.lock`, `requirements*.txt`) e `dependencies`
(attivazione su manifest e lockfile). Entrambe legano un metodo
attraverso `project-protocol:isolated-worker` in sola lettura, non un ruolo:
`python-refactor-agent` modifica il codice per mandato, e una lente di review
non scrive; `dependency-audit` non ha ruoli. Il worker Python legge i
risultati degli strumenti dal pacchetto di evidenze e riporta ciò che gli
strumenti non vedono. Il costo di installazione cresce di due plugin per chi
installa la review, in cambio di uno specialista che non manca mai.

### 3.6 Il metodo canonico degli ADR vive in `project-knowledge`

Nuova skill `adr-method` con helper `scripts/adr_tool.py` e workflow
autonomo `project-knowledge:adr`. Un ADR ha frontmatter leggibile dalla
macchina (`adr_id`, `status` tra `Proposed`, `Accepted`, `Superseded`,
`superseded_by`, `supersedes`, `scope` con path, moduli e domini,
`governs_symbols`, `proposed_at_sha`, `accepted_at_sha`, `last_verified_sha`)
e tre sezioni obbligatorie: esempi verificati dall'intervista (`EX-*`),
alternative rifiutate (`RA-*`), invarianti applicabili (`INV-*`). Il registro
`docs/adr/README.md` è generato dall'helper e risolve, dato uno scope, gli
uno-tre ADR attivi che lo governano.

Motivazioni:

- Un ADR nasce `Proposed` dall'intervista e viene promosso `Accepted` solo
  alla merge verificata, con `accepted_at_sha` pari al commit integrato. Prima
  di allora guida il task ma non vincola gli altri. Questo evita che una
  decisione non ancora implementata diventi legge.
- La supersessione è bidirezionale e scritta dall'helper, mai a mano: un
  modello economico che legge il vecchio ADR trova `superseded_by` e si ferma.
- Gli esempi `EX-*` sono l'oracolo dei test: ogni micro-task del piano ne
  indirizza almeno uno. Specifica ed esempio di test coincidono.
- `AGENTS.md` e `CLAUDE.md` restano corti: il perché va negli ADR, le regole
  operative restano nelle istruzioni, in un blocco delimitato
  `<!-- LOOP-HARNESS:BEGIN -->` ... `<!-- LOOP-HARNESS:END -->` che
  `instructions-method` aggiorna senza toccare il testo dell'utente.

### 3.7 Lo stato del ciclo vive in `work.json`, non in un secondo registro

`project-protocol` estende il contratto `daodan/work/v1` con sezioni opzionali
validate: `workspace` (modalità `WORKTREE`, `BRANCH` o `IN_PLACE`, branch,
`base_sha`, binding ambientali senza valori segreti), `preflight` (stato dei
test di partenza `GREEN`, `KNOWN_RED` o `UNKNOWN_RED` con impronta, stato
migrazioni), `adr` (attivi e proposto), `waves` (ondate e micro-task) e
`rulings` (decisioni locali dei worker, solo in aggiunta). I campi obbligatori
attuali e lo schema restano invariati, così i run esistenti restano validi.

Il validatore impone meccanicamente:

- **Budget del micro-task**: al più quattro file in `write_set` (sei con una
  `granularity_exception` motivata), un oracolo che fallisce prima
  dell'implementazione, un comando di verifica, un commit atomico.
- **Disgiunzione nell'ondata**: due task della stessa ondata non condividono
  file in `write_set` né `resource_locks`, e nessun contratto prodotto da uno
  è consumato dall'altro. In `IN_PLACE` un'ondata con più task è sequenziale.
- **Ruling solo in aggiunta**: `validate_transitions` rifiuta un aggiornamento
  che rimuove o altera un ruling registrato.

Motivazione: il contratto esiste già, ha un helper testato, un sentinel, un
lock di scrittura e la ripresa per identità esatta. Un secondo registro
(`.harness/`, `.planning/`) sarebbe la contraddizione tra file che questo
repository riconosce come proprio difetto caratteristico.

### 3.8 Preparazione e scelta dell'area di lavoro

Prima dell'intervista il coordinatore esegue sonde deterministiche: stato del
working tree (`git status --porcelain=v2 --branch`), distanza dall'upstream
(`git fetch --prune` e `git rev-list --left-right --count HEAD...@{upstream}`,
mai un `git pull` cieco), test di partenza sullo scope, stato delle
migrazioni, freschezza della mappa. Poi chiede all'utente la modalità:

- `WORKTREE`: consigliata per ondate parallele o working tree sporco. La
  creazione usa `superpowers:using-git-worktrees`, che è il proprietario
  dichiarato di questa capacità dopo il ritiro di `git-worktrees`.
- `BRANCH`: branch dedicato nel checkout corrente, ondate sequenziali.
- `IN_PLACE`: branch corrente, ondate sequenziali, file preesistenti
  registrati come protetti.

Casi particolari con regola fissa: merge o rebase interrotti bloccano;
upstream avanti chiede rebase o fissa `base_sha`; `UNKNOWN_RED` blocca una
feature e propone di convertire il task in riparazione o di registrare
l'impronta come `KNOWN_RED` autorizzata; migrazioni pendenti avvisano prima dei
test.

### 3.9 Rollback chirurgico, non `git checkout <sha> -- <paths>`

Il ripristino di un micro-task fallito usa gli snapshot pre-fase di
`run_state.py`, non un checkout dal `pre_step_sha`: quel comando fallisce sui
file nuovi e sovrascrive modifiche utente preesistenti in `IN_PLACE`. I file
creati dal task vengono rimossi, quelli modificati tornano ai byte registrati,
tutto il resto resta intatto.

### 3.10 La review multi-prospettiva presidia quattro momenti

| Momento | Lenti | Regola anti-eco |
|---|---|---|
| A. ADR `Proposed` | `premise-auditor`, `abstraction-architect-agent`, lente di dominio da `skill-catalog` | Le affermazioni dell'ADR sull'esistente sono ipotesi finché non derivate dal sorgente |
| B. Piano a ondate | ancoraggio, oracolo, isolamento più specialisti condizionali | Il testo del piano non fa prova; ogni lente vede la sua fetta |
| C. Fine ondata (`delta`) | specialisti le cui ancore toccano il diff, `test-suite-auditor`, lente 0 sui nuovi ruling | Un ruling nasce `unverified` |
| D. Candidato (`full`) e post-merge | `team-review` intero; poi `guide-reviewer` e `instructions-auditor` su ADR, docs e istruzioni | Un'affermazione copiata dall'ADR nei docs è un'eco |

Il rigore sale e non scende: un task locale parte con lenti mirate, e appena il
diff tocca sicurezza, persistenza, concorrenza, risorse o contratti pubblici
il coordinatore passa al rigore massimo.

### 3.11 Ritorno di `peer-review` e `moe`

I due plugin tornano da Shinatama, perché il ciclo li consuma: `peer-review`
revisiona artefatti di intento (piani, specifiche, ADR), che è la lacuna 2.3,
e la sua dottrina (R14, `GIVEN` contro `DERIVED`) è la stessa di
`review-quality-gates`; `moe` offre una seconda opinione multi-modello nei
momenti A e B, attivata da flag e mai per default. La politica delle
dipendenze impone che un plugin torni solo se un metodo lo dispaccia o ne
carica la skill: `project-lifecycle` li dichiara e li usa in `lifecycle-method`.
Gli altri 23 plugin estratti non hanno un consumatore nel ciclo e restano in
Shinatama. `ai-tooling` non torna: `project-lifecycle` delega già a
`superpowers` direttamente.

La rimozione dei due plugin da Shinatama è un lavoro separato su quell'altro
repository. Finché non avviene, un host che installa entrambi i marketplace
registra `moe` e `peer-review` due volte.

### 3.12 Il server MoE restituisce la causa

`moe_ask` restituisce `error`, `code` e `charged`. I codici distinguono
`invalid_request`, `identity_contract`, `model_collision`, `payload_invalid`,
`brief_bound`, `transport`, `response_shape`, `model_identity_missing`,
`model_changed`, `reply_tool_calls`, `reply_empty`, `reply_truncated`,
`finish_reason_unsupported` e `reply_bound`. `charged` è falso prima dell'invio
e vero dopo, così la spesa parziale è registrata e non indovinata. Il
vocabolario di un provider inoltrato da un gateway (`end_turn`,
`stop_sequence`) è accettato; `length` e `max_tokens` sono troncamento. Il
flusso chiede il tetto in parole, non in byte.

### 3.13 Densità: forma obbligatoria e budget misurato

Questa è la decisione che decide se un modello economico ce la fa.

**Forma delle skill a runtime.** Una skill che un coordinatore carica è un
router: una tabella di caricamento (risorsa, sezione, quando) e una procedura
per passo scritta come checklist con input, output, condizione di stop e codici
di esito chiusi. La regola sta nel kernel; la motivazione e la storia stanno
nella pagina `docs/plugins/<nome>.md`, che è il posto previsto per le
spiegazioni. Il modello di riferimento è `map-method/SKILL.md` con la sua
tabella "Load map".

**Brief dei worker generati, mai skill lette.** Un worker di ondata riceve un
brief da template con campi fissi: contratto del task, estratti `EX-*`, `RA-*`
e `INV-*` assegnati, card dei simboli in `write_set` e dei chiamanti diretti,
`pre_step_sha`, ruling delle ondate precedenti. Restituisce un codice chiuso:
`OK`, `NEEDS_REPLAN`, `ORACLE_INVALID`. Non legge `review-quality-gates` né
`lifecycle-method`.

**Budget misurato dal CI.** `tests/test_xray_load_budget.py` misura le parole
che ogni contesto di `codebase-map` carica, per unità e per ruolo, e fallisce
quando un tetto è superato. La stessa misura si estende a `lifecycle-method`,
`project-protocol`, `review-preparation`, `review-method`,
`review-quality-gates` e `adr-method`. Un tetto si abbassa quando una skill si
alleggerisce e non si alza per far passare una modifica.

Motivazione: la densità non è un'impressione ma un numero, e un numero che il
CI controlla non può tornare indietro di nascosto. La separazione tra regola e
motivazione preserva la motivazione (che resta leggibile nei docs) e toglie
dal contesto a runtime ciò che a runtime non decide nulla.

### 3.14 Un quinto principio di lavoro: ridisegnare invece di rattoppare

`project-protocol` è il proprietario canonico della disciplina di lavoro, e
le sue quattro regole (`Working assumptions`, `simplicity`, `scope`,
`verification`) sono copiate in `CLAUDE.md`, `AGENTS.md` e nei due riferimenti
che `instructions-method` usa per creare le istruzioni dei progetti. Si
aggiunge `Working redesign`: correggere la causa e mai il sintomo; quando un
difetto mostra che uno script, una skill, un contratto o un workflow ha la
forma sbagliata per il suo problema, ridisegnare quell'unità da zero; un
rattoppo che lascia la forma sbagliata è debito. Il test di parità
`tests/test_harness_domain_ownership.py` verifica le cinque regole in ogni
copia e su tutti e cinque gli host. Il principio entra quindi in ogni progetto
che Daodan inizializza, tramite `working-principles.md` e
`instruction-example.md`.

### 3.15 `project-lifecycle` non delega più a `superpowers`

Le quattro skill delegate (`brainstorming`, `writing-plans`, `executing-plans`,
`subagent-driven-development`) coprono le fasi 2, 4 e 5 del ciclo. Il ciclo
non le copia: l'intervista è ancorata alla mappa e agli ADR attivi, il piano è
un DAG validato in `work.json`, l'esecuzione passa dagli specialisti di stack
con brief generati e codici di esito chiusi. Tenere la delega significherebbe
eseguire due metodi per lo stesso passo. `using-git-worktrees` resta l'unico
pezzo utile, e la creazione di una worktree è una procedura di poche righe
dentro la fase 1, che il ciclo possiede comunque.

`project-lifecycle` perde quindi la dipendenza da
`superpowers@claude-plugins-official`. Il linter delle dipendenze impone che
nessun riferimento resti nei suoi kernel. Anche `peer-review`, tornato in
Daodan, perde la dipendenza: l'unico uso era la skill di ricezione delle
review caricata dal ruolo `respondent`, e le cinque regole che servivano a
quel ruolo (verificare prima di rispondere, accettare ciò che regge,
confutare con evidenza positiva, chiedere quando è ambiguo, non riformulare
il finding) ora stanno nel ruolo stesso. Nessun kernel di Daodan dichiara più
`superpowers`. `CLAUDE.md` registra
che la delega è terminata il 18 ottobre 2026 e che `superpowers` resta un
compagno installabile dall'utente per uso diretto. Non è una reimportazione
delle skill ritirate: è un metodo diverso, con un modello di stato e di
evidenza che quelle skill non hanno.

### 3.16 Review evidence-first: cosa prendiamo da una ricerca esterna

Il 18 ottobre l'utente ha portato un'analisi sulla replica del servizio di
code review gestito di Anthropic (quattro stadi: find, verify, rank, post).
Confrontata con `senior-review`, la ricerca conferma l'impianto e aggiunge
cinque cose che Daodan non ha ancora. Tre punti in cui Daodan è già oltre:
la regola di provenienza del contesto condiviso (N revisori che ereditano
una premessa valgono una osservazione), la derivazione cieca del
`premise-auditor` e il protocollo di assenza di finding. Tre cose che non si
applicano: una GitHub App come servizio, un orchestratore esterno, e i prezzi
per modello, che non entrano in questo documento perché non misurati qui.

Le cinque aggiunte, con il punto del piano che le assorbe:

1. **Strumenti prima, modello dopo.** `review-preparation` esegue sul
   candidato i controlli deterministici che il progetto dichiara (lint, tipi,
   test di impatto, audit delle dipendenze, segreti) e li consegna ai revisori
   come evidenza. Un revisore non riporta ciò che un linter ha già riportato,
   e non spende contesto per riscoprirlo. Ondata 2, task 2.2.
2. **Politica letta dal commit base, non dal candidato.** Le istruzioni che
   governano la review (`AGENTS.md`, `CLAUDE.md`, il blocco del ciclo) si
   leggono da `base_sha`, così un task o un diff non possono riscrivere le
   regole che li giudicano. Il contenuto del candidato resta dato, mai
   istruzione. Ondata 2, task 2.2.
3. **Il finding è un'ipotesi strutturata.** Il contratto `evidenced-finding`
   guadagna `trigger` (la condizione concreta che innesca il difetto),
   `counterevidence_checked` (cosa è stato cercato per confutarla) e
   `introduced_by_candidate` (vero solo se il diff lo causa; altrimenti il
   finding è preesistente e si riporta a parte, mai come regressione). Il
   pannello riceve questi campi, non la prosa persuasiva del revisore.
   Ondata 2, task 2.2.
4. **La riproduzione è l'evidenza più alta.** Nel momento D, quando il
   workspace è una worktree usa e getta e il runner è disponibile, la lente
   di raggiungibilità può chiedere a `testing:test-writer` un test minimo e
   osservare `pass` sul base e `fail` sul candidato. Quel risultato vale più
   di qualunque ragionamento ed entra come classe `reproduced`, sopra
   `measured` e `derived`. Il vocabolario di `dependency-audit`
   (`TOOL-REPORTED`, `INFERRED`, `UNKNOWN`) si allinea alle stesse classi.
   Ondata 2, task 2.2; ondata 3, task 3.3.
5. **Il rischio decide il budget, e lo decide una regola.** La scelta tra
   `delta` e `full`, e tra i livelli di rigore, nasce da segnali
   deterministici: il pacchetto di impatto della mappa (interfaccia o effetti
   cambiati, numero di chiamanti), i path sensibili (autenticazione,
   migrazioni, pagamenti, concorrenza), le dipendenze toccate. Un modello
   non sceglie il proprio rigore. Ondata 3, task 3.2.

Una sesta idea resta rinviata: registrare l'esito umano di ogni finding
(`fixed`, `accepted_no_change`, `disputed`, `false_positive`,
`pre_existing`) nel run, per alimentare gli eval di `senior-review` con dati
reali. Richiede una fase di raccolta che il ciclo ancora non ha.

## 4. Il ciclo, fase per fase

### Fase 0: inizializzazione (`assess --init`)

1. Mappa: `snapshot.py scope` e primo run di `codebase-map`.
2. Registro ADR: `adr_tool.py init-index`.
3. Istruzioni: `instructions-method` crea o verifica `AGENTS.md` e `CLAUDE.md`
   con il blocco `LOOP-HARNESS`.
4. Comandi di test, lint e build registrati; `last_synced_sha` pari a `HEAD`.

### Fase 1: preparazione e area di lavoro (`change`, passo 1)

Sonde di 3.8, scelta della modalità, registrazione in `work.json`.

### Fase 2: intervista ancorata (`change`, passo 2)

Il coordinatore estrae dalla mappa le card dei simboli coinvolti e con
`adr_tool.py resolve` gli ADR attivi. Fa una domanda per turno, ancorata a
`file:line`, con esempi concreti di input e output presi dal codice. Si ferma
quando scope, esempi nominale, di confine e di errore, alternative rifiutate e
invarianti sono fissati.

### Fase 3: ADR `Proposed` e momento A

`adr_tool.py propose` scrive l'ADR; la review di momento A lo verifica.

### Fase 4: piano a ondate e momento B

Il coordinatore compila il DAG in `work.json`; `run_state.py` lo valida; la
review di momento B lo giudica. Fino a tre cicli tra pianificatore e lenti
prima di chiedere all'utente. L'ondata 0 costruisce fixture e harness di test
quando mancano.

### Fase 5: esecuzione e momento C

Per ogni micro-task: snapshot pre-fase, test RED (altrimenti `ORACLE_INVALID`),
codice minimo dentro `write_set` (altrimenti `NEEDS_REPLAN`), test verdi,
commit atomico, ruling se serve. Lo scrittore è lo specialista dello stack:
`python-development:python-engineer`, `typescript-development:typescript-engineer`,
`testing:test-writer`, `clean-code:clean-code-agent` per la leggibilità, un
`isolated-worker` con le skill di `skill-catalog` per gli altri stack. A fine
ondata la review `delta`; l'ondata diventa `SEALED`.

### Fase 6: candidato e momento D

Review `full` su `base_sha..HEAD`. I finding `BLOCKER` e `HIGH` confermati
generano un'ondata di rimedio, al più due volte; poi si torna all'utente.

### Fase 7: integrazione e riallineamento (`consolidate`)

Merge del branch o chiusura della worktree; `adr_tool.py promote`; mappa
incrementale (`snapshot.py write --reuse`, invalidazione per hash); concept
index; docs e README sulle sezioni toccate; blocco `LOOP-HARNESS`;
`last_synced_sha` pari a `HEAD`; chiusura del run con `result.json`.

## 5. Piano di attuazione per ondate

Ogni ondata rispetta il budget che il ciclo imporrà ai propri micro-task:
`write_set` disgiunti nella stessa ondata, oracolo RED prima del codice,
comando di verifica, nessun file generato toccato a mano.

### Ondata 0: ritorno dei plugin e principio di lavoro (eseguita)

| Task | `write_set` | Verifica |
|---|---|---|
| 0.1 copia di `plugins/moe` e `plugins/peer-review` da Shinatama, ripristino di `docs/plugins/`, `evals/peer-review/` e dei test | i file elencati | `daodan_build.py`, i quattro linter |
| 0.2 ridisegno del contratto di errore di `moe_ask` | `server.py`, `ultra-nerd.md`, `docs/plugins/moe.md`, `tests/test_moe_transport.py` | 11 test, uno saltato dove manca l'SDK |
| 0.3 quinto principio `Working redesign` | protocollo, `CLAUDE.md`, `AGENTS.md` via sync, i due riferimenti, il test di parità | 14 test di parità su cinque host |

### Ondata 1: fondamenta

| Task | `write_set` | Oracolo |
|---|---|---|
| 1.1 estensione del contratto di lavoro | `plugins/project-protocol/contracts/work.toml`, `scripts/run_state.py`, `SKILL.md` | test che rifiutano `write_set` sovrapposti, cinque file senza eccezione, ruling rimossi, ondata parallela in `IN_PLACE` |
| 1.2 skill `adr-method` e workflow `adr` | `plugins/project-knowledge/skills/adr-method/**`, `workflows/adr.md` e `.toml`, `plugin.toml`, `instructions-method/SKILL.md` | test su `validate`, `resolve`, `propose`, `promote` e sul blocco `LOOP-HARNESS` |

### Ondata 2: review

| Task | `write_set` | Oracolo |
|---|---|---|
| 2.1 roster obbligatorio | `senior-review/plugin.toml`, `stack-dimensions.md`, `knowledge-bindings.md`, i tre sidecar | `lint_dependency_graph.py`, parità `STACK_ROLES` |
| 2.2 target-kind, gate di ancoraggio, budget, evidenza deterministica, politica da `base_sha`, campi `trigger`, `counterevidence_checked`, `introduced_by_candidate`, classe `reproduced` | `review-preparation/SKILL.md` e `references/code-review.md`, `review-method/SKILL.md`, `review-quality-gates/SKILL.md`, `contracts/evidenced-finding.toml` | test di porta della pipeline, test del contratto |

### Ondata 3: ciclo

| Task | `write_set` | Oracolo |
|---|---|---|
| 3.1 dipendenze e sidecar | `project-lifecycle/plugin.toml` (entrano `python-development`, `dependency-audit`, `skill-catalog`, `peer-review`, `moe`; esce `superpowers`), `change.toml`, `repair.toml`, `verify.toml`, `maintain.toml` | unione dei ruoli composti in `maintain`, nessun riferimento residuo a `superpowers` |
| 3.2 `lifecycle-method` come router e fasi 1-5 | `SKILL.md`, `references/change.md`, nuovi riferimenti per passo, template del brief | budget di carico |
| 3.3 fasi 6-7 e inizializzazione | `verify.md`, `consolidate.md`, `assess.md`, `repair.md` | test di retention invariati |

### Ondata 4: test e densità

| Task | `write_set` | Oracolo |
|---|---|---|
| 4.1 test unitari | `tests/test_project_protocol.py`, `tests/test_adr_method.py` | i test stessi |
| 4.2 contratti multi-host | `tests/test_harness_domain_ownership.py`, `tests/test_lifecycle_campaign.py` | cinque host |
| 4.3 budget di carico | `tests/test_skill_load_budget.py` su sei skill | tetti registrati |
| 4.4 alleggerimento | `review-quality-gates`, `review-method`, `review-preparation`: regola nel kernel, motivazione in `docs/plugins/senior-review.md` | il budget scende, i test di porta restano verdi |

### Ondata 5: versioni, documentazione, build

Bump di `project-protocol`, `project-knowledge`, `senior-review`,
`project-lifecycle`, `moe`, `peer-review` e di `metadata.version`;
`sync_codex_instructions.py`; `daodan_build.py`; `sync_plugin_docs.py`; i nove
gate del CI; aggiornamento di `README.md` e `CLAUDE.md` (tabella delle
dipendenze, frase su Shinatama).

## 6. Vincoli che il lavoro deve rispettare

- `tests/test_harness_domain_ownership.py` impone che `dispatch.roles` di ogni
  sidecar di `senior-review` sia esattamente `CORE_ROLES | STACK_ROLES`: ogni
  ruolo aggiunto va dichiarato in entrambi i posti.
- `tests/test_lifecycle_campaign.py` impone che `maintain.toml` contenga
  l'unione dei ruoli di tutte le operazioni e di `team-review`.
- `validate_component_kinds` vieta che una skill e un workflow condividano il
  nome in un plugin: la skill è `adr-method`, il workflow è `adr`.
- `lint_bundled_paths.py`: i file letti a runtime stanno sotto `skills/<nome>/`.
- `lint_host_vocabulary.py`: nessun nome di strumento host nei kernel.
- `check_version_bumps.py`: ogni plugin toccato cambia versione.
- Nessun file sotto `exports/` o manifest di root è modificato a mano.
- Il lavoro non committato del 18 ottobre su `codebase-map` (card store,
  pacchetto di impatto, Go) appartiene a un'altra sessione e non va toccato;
  il build lo include perché è nel kernel.

## 7. Decisioni rinviate

- **Rimozione di `moe` e `peer-review` da Shinatama**: lavoro separato su
  quell'altro repository, con il suo build e il suo commit.
- **Sonde di esecuzione per host del ciclo**: un task minimo eseguito su
  ciascun host, registrato in `tests/host-probes/`, per chiudere la distanza
  di 2.7. Non è nel piano perché richiede gli host installati.
- **Misura della tesi**: il piano complementare definisce tre bracci
  (frontiera da sola, economico da solo, economico con Daodan) e le misure.
  Nessun numero di costo o di token compare in questo documento, perché nessuno
  è stato misurato.
- **Scrittura delle card via MCP**: rinviata dal piano complementare.

## 8. Stato al 19 ottobre 2026

Eseguite le ondate 0-5 nel working tree, non committate:

| Ondata | Esito |
|---|---|
| 0 | `moe` 1.2.0 e `peer-review` 2.5.0 riportati da Shinatama; contratto di errore di `moe_ask` ridisegnato; principio `Working redesign` in ogni copia |
| 1 | `work.toml` con sezione `[loop]`; `run_state.py` valida workspace, preflight, adr, waves e rulings, più il comando `plan-check`; skill `adr-method` con `adr_tool.py` e workflow `/project-knowledge:adr`; blocco del ciclo in `instructions-method` |
| 2 | `senior-review` 15.3.0: Python e dipendenze nel roster; `candidate-grounding.md` (tipo di target, politica da `base_sha`, gate di ancoraggio, pacchetto di evidenze, budget `delta` e `full`, roster per tipo); filtro dei `.md` rimosso; campi ipotesi nel contratto `evidenced-finding`; classe `reproduced` e grant di riproduzione per la lente 1 |
| 3 | `project-lifecycle` 1.5.0: `superpowers` rimosso; `lifecycle-method` come router con sei unità per fase (`preflight`, `interview`, `waves`, `worker-brief`, `verify`, `consolidate`) e `assess --init` |
| 4 | `tests/test_adr_method.py` (10), `LoopRecordTests` (8), test di trasporto MoE (+2), `tests/test_skill_load_budget.py` (4) |
| 5 | marketplace 37.0.0; build dei cinque host, documentazione e istruzioni rigenerate; suite completa e nove gate verdi |

Chiusi il 19 ottobre, dopo le ondate:

- `review-quality-gates` diviso in un nucleo di 892 parole e due unità per passo
  (`context-sharing.md` per la preparazione, `verification-panel.md` per la
  consolidazione); la preparazione di `team-review` scende da 3562 a 3128
  parole, con le motivazioni spostate in `docs/plugins/senior-review.md`. Il
  passo di preparazione di una team review caricava 9647 parole e ora ne
  carica 7988, con il tetto nel CI.
- `moe` e `peer-review` rimossi da Shinatama (marketplace 2.0.0), con i loro
  test di rendering reale portati in Daodan.
- I server MCP di `peer-review` e `moe` partivano con `uv run --script`, quindi
  il progetto in lavorazione poteva scegliere l'indice dei pacchetti di un
  server che tiene una chiave API. Ora partono con `--no-config --no-project`
  come quello di `codebase-map`, e una tabella in `tests/test_daodan_mcp.py`
  obbliga ogni server dichiarato a quel lancio.

Il 19 ottobre, dopo la prima prova reale
(`docs/superpowers/reports/2026-10-19-closed-loop-probe-claude.md`), la
proporzione della review è passata da prosa a script: `review_roster.py` nel
protocollo calcola il roster dal diff e dalla mappa e il validatore rifiuta una
consegna fuori roster. Con quello i budget `delta` e `full` di questo documento
si chiamano `light` e `branch`, gli stessi nomi dei comandi `review-changes` e
`review-branch` della proposta successiva
(`docs/superpowers/specs/2026-10-19-command-set-design.md`), che sostituisce i
comandi qui descritti.

Aperti: sonde di esecuzione per host e misura della tesi. Lo stato
successivo vive nei run, nei commit e nelle pagine `docs/plugins/`.
