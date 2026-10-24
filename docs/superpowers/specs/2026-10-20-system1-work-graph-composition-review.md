# Multi-agent review: `2026-10-20-system1-work-graph-composition-design.md`

Data: 20 ottobre 2026. Protocollo: Loop Engineering (gate, budget), Graph
Engineering (DAG), Multi-Agent Review (lenti isolate in cieco reciproco),
secondo il documento di riferimento "Loop Engineering, Graph Engineering e
Multi-Agent Review".

## Esito degli emendamenti alla specifica

La review riportata sotto è storica e riferisce la prima versione della spec.
Severità, conteggi e locator originali non sono una nuova certificazione della
versione emendata. La correzione è documentale: contratti e runtime proposti
devono ancora essere implementati e verificati.

| Finding originali | Risoluzione nella spec emendata |
|---|---|
| A1, C1 | §1-2 e §6: piano semantico distinto dalla compilazione; S2 deterministico |
| L1, C2, L11 | §5.3: unica autorità budget nel run, prenotazioni e carry-over attraverso replan, guardie anche su update |
| A2 | §1.1 e §7.1: packet ai produttori lifecycle/senior-review, protocollo solo frontiera e riferimenti |
| A3, P3 | §2.2 e §10: citazioni come binding di evidenza; incompletezza v2 e fallback primo hunk dichiarati |
| A4, P9 | §2: autorità e ricorso per ogni snodo; S1 non usa un prompt inesistente, S2/S6 deterministici |
| A5 | §2.1 e §12: offline/shadow/active distinti, promozione per snodo; proposta AST-primary del report ritirata |
| A6, A7 | §5.1: piano immutabile, tentativi e Decision Log nel solo work.json; puntatori decision_ids |
| A8, L7 | §5.2 e §7.2: recovery dal template, artefatti logici stabili/versionati, invalidazione e stalezza delle prove |
| A9, L8, L10 | §2.2 e §5.2: due sole forme di review, ABSTAIN separato dalle azioni, recovery schema con vincoli |
| A10, L9 | §1.1, §4 e §6: cataloghi con ownership e cross-validazione; WAVE_BARRIER, nove archetipi coperti da AC16 |
| L2, L12, T5 | §8: fingerprint/delta verificabili, primo retry definito, flakiness e diagnostica limitata |
| L3, L4 | §7.4: estensione esplicita work/v2, stopped distinto da successo, nuove delivery per tentativo |
| L5, L6, T4 | §7.1-7.3: reservation, lease, fencing, CAS, commit atomico, gate post-patch isolato e resume |
| T1, T6, P5 | §3.2-3.3: adapter proprietario, identity handshake, stop posseduto e probe host |
| T2, T3, T7, T8 | §3.4 e §5.3: deadline totale, cap ricorso/riavvii, budget tempo e unità normalizzate |
| P1, P2, P4, P6, P7, P8 | §10: provenienza corretta e limitazioni; GUTSY_RESULTS.md allineato |
| Premesse non misurate | §3.1, §10-12: nessuna calibrazione trasferita o promozione automatica da S4 agli altri snodi |

### Rettifiche alla review stessa

- L1 descrive una **lacuna della garanzia**: il testo precedente vietava il
  reset ma non definiva autorità/carry-over. Non era prova di un reset eseguito
  da un controller che ancora non esiste.
- L2 era un controesempio possibile perché evidence_delta non era definito,
  non una prova universale di irraggiungibilità dello stallo.
- Non adottata la proposta di re-run del verifier completamente gratuiti:
  §8 li addebita a work units e tempo, con cap diagnostico separato dai repair.
- Il gate deve usare il candidato **post-patch**, non lo snapshot pre-patch
  di dispatch. Nessun verdetto semantico diventa deterministico per registrazione.
- I processi Python osservati non sono attribuiti a Gutsy né provati orfani.
  La porta e il PID non costituiscono prova di identità/ownership.
- La soglia 0.30 appartiene a `probe_gutsy_v2.py`; 0.15 con diversa regola
  appartiene a `run_gutsy_v2_eval.py`. Scrivono lo stesso summary, senza binding
  immutabile che permetta di attribuirlo con certezza a una delle due regole.
- La verifica corrente ha anche rilevato troncamenti/input modificati V1 e
  assenza di parity del backend custom. Corretti nella spec e nel report;
  non sanati modificando o rigenerando gli output storici.

Accettazione documentale: tutti gli ID delle quattro lenti hanno una
risoluzione sopra; §11 della spec elenca AC01-AC20 per l'implementazione futura.
Una nuova team review della revisione non è stata eseguita durante il fix
documentale iniziale. Il successivo riscontro del 21 ottobre è registrato sotto.

### Secondo passaggio mirato (21 ottobre 2026)

Due revisori indipendenti, sola lettura: controllo di budget/stati/recovery
e controllo di ownership/evidenze/rollout. Entrambi hanno dato PASS per un
prototipo isolato con fixture, non per integrazione o promozione System-1.
Sessioni: `ses_ea29bb1adffehQ8TiWTn15m8fZ` e
`ses_ea29bb1abffeJ0lXkLtEak79On`.

Raccordo ancora richiesto prima dell'integrazione: allineare nella specifica
madre la proprietà dei packet a lifecycle/senior-review, evitando un secondo
produttore nel protocollo. Il prototipo è sotto
`evals/project-lifecycle/work-graph/`; il suo README separa criteri esercitati
e mancanti. Non costituisce implementazione completa di work/v2.

Verifiche eseguite sul fix: controllo della presenza di tutti i 39 ID
originari nel registro di risoluzione, dei 20 scenari AC e dei blocchi Markdown;
ricalcolo indipendente delle cinque righe Suite 2 dalle probabilità salvate;
ricalcolo del summary V2 (18/23, 24 eccessi su 10 casi) e riscontro delle
citazioni vuote C08-C11. Nessuna nuova inferenza né prova del runtime del
controller: non è implementato. I punteggi restano osservazioni con i limiti
di provenienza descritti in §10 della specifica emendata.

## Metodo (review originale)

Quattro revisori isolati, nessuno vede i findings degli altri, consolidamento
del coordinatore con verifica incrociata su spec, contratti (`work.toml`,
`run_state.py`) e artefatti del benchmark (`evals/senior-review/choicer-eval/`).
Sola lettura per tutti i revisori; questo documento è l'unico artefatto
scritto della review.

| Lente | Focus | Esito |
|---|---|---|
| Concettuale | entropia strutturale, fonti di verità in competizione | 1 Critical, 1 High, 1 Low, 3 concetti mancanti |
| Premesse | derivazione blind + verifica numerica contro gli artefatti | 1 High, 8 premesse classificate, correzioni numeriche a §12 |
| Integrità logica | macchina a stati, terminazione, resume | 1 Critical, 5 High, 3 Medium, 3 Low, 5 domande di disegno |
| Resilienza temporale | sidecar, timeout, recovery over time | 5 High, 3 Medium, 1 difetto più pericoloso designato |

## Verdetto

L'ossatura del disegno è corretta come ideale (genera / decide / governa, gate
deterministici, budget monotono), ma due difetti Critical vanno chiusi prima
di qualsiasi implementazione: la ricomposizione (`needs_replan`) ricarica il
budget globale aprendo un loop non terminante, e lo snodo S2 è definito in tre
modi non coincidenti destabilizzando il confine componi/decidi. A valle, 12
findings High si raggruppano in sei temi; il più pericoloso per un run reale è
un verifier flaky che consuma il budget fino a un terminale falso
(`VERIFIER_UNSTABLE` esiste ma non può mai attivarsi). La sezione evidenze
(§12) contiene quattro imprecisioni numeriche trovate e verificate contro gli
artefatti.

## Findings Critical

### C1 [A1, concettuale] S2 è definita tre volte in modo non coincidente

§2 dichiara S2 snodo di decisione con tipo `vincolato` (tipo inesistente nel
contratto madre §3.6, che ammette solo `choice`/`score`/`noul`); §6.3 la
riduce a "proposta di partizione"; §14.3 propone di renderla deterministica.
La partizione in nodi determina `write_set`, parallelismo e forma del DAG:
è topologia, quindi in conflitto con §1.2.3 ("LLM non inventa la forma del
workflow"). Emendamento: chiudere §14.3 sul default deterministico prima di
congelare la tabella; S2 o esce dagli snodi (passo di composizione) o diventa
consultazione advisory con tipo definito nel contratto esteso.

### C2 [L1, logica] La ricomposizione ricarica il budget globale

`needs_replan` "riapre la composizione con un nuovo hash": il compositore
compone un nuovo `work-graph.json` con `global_budget` appena scritto. Nessuna
regola impone il carry-over del budget residuo né dei contatori di stallo nel
grafo nuovo. Scenario: S5 → `needs_replan` → ricomposizione (budget 18 nuovo)
→ nuovo grafo fallisce uguale → loop non terminante, ogni giro "regolare".
Emendamento: il controller copia budget residuo e contatori di stallo nel
nuovo grafo come precondizione di freeze, verificata meccanicamente; rifiuto
del freeze se non combacia.

## Findings High, per tema

### Tema 1: Semantica di stallo e instabilità (L2, L12, T5)

- `evidence_delta` non è definito da nessuna parte (né nella spec né nel repo);
  la condizione di stallo ("stesso fingerprint e delta vuoto") non è
  implementabile.
- Fresh Escalation produce per costruzione pacchetti nuovi → delta mai vuoto →
  `STALLED_SAME_FAILURE` irraggiungibile nel loop principale; terminazione solo
  per `BUDGET_EXHAUSTED`, con diagnosi sbagliata presentata all'utente.
- `retry_same_tier` richiede "output del verifier cambiato": al primo
  fallimento non esiste baseline, l'opzione è morta proprio al primo snodo S5.
- `VERIFIER_UNSTABLE` compare come etichetta senza condizione di attivazione.
  Scenario: verifier flaky, alternanza pass/fail sul medesimo candidato → né
  stallo né instabilità rilevata → 18 transizioni consumate e terminale falso.
- Mitigation: `evidence_delta` = confronto canonizzato tra output verifier
  consecutivi (id test ordinati + classe eccezione + testo asserzione,
  whitespace-insensitive); stallo sul solo fingerprint ripetuto dopo N
  tentativi; stesso digest di candidato con esiti di gate diversi ≥ 2 →
  `VERIFIER_UNSTABLE`; re-run del verifier su candidato invariato non
  decrementano il budget.

### Tema 2: Mappatura sulla record (L3, L4, L11)

- Gli 8 terminali della spec non hanno rappresentazione in `work.toml`:
  `status` è solo `in_progress|complete`, `terminal_reason`/`terminal_outcome`
  non esistono; `complete` richiede deliveries `delivered`, gate `passed` e
  `interruption == null`, quindi `REFUTED`, `STALLED_SAME_FAILURE`,
  `BUDGET_EXHAUSTED`, `HUMAN_ESCALATION` non possono né completare né chiudere
  `in_progress`. Serve `terminal_outcome` nel contratto o mappatura esplicita
  su `result.json.limitations`, con tabella riga per riga nella spec.
- `delivered` è terminale: le recovery edges che riaprono nodi completati
  (N5 → N3) violano `validate_transitions` al primo ciclo di repair. Ogni
  invalidazione deve mintare una nuova identity di delivery
  (`artifact:patch:<id>_v2` come nuova delivery con riferimento alla
  precedente) oppure serve lo stato `invalidated`.
- `budget` non è in `IMMUTABLE` in `run_state.py`: un `update` generico può
  riscriverlo; inoltre `record.budget` e `graph.global_budget` coesistono
  senza regola di autorità (la record fa fede per §5.7 della spec).

### Tema 3: Concorrenza, atomicità, resume (L5, L6, T4)

- Nessuno stato "in flight": due `graph-next` prima di un `graph-complete`
  riemettono lo stesso nodo (doppio dispatch, doppio costo, collisione di
  delivery). Servono stati di nodo `pending/running/gate_failed/invalidated`
  con holder marker e rifiuto di riemissione.
- Il gate gira sul candidato intero condiviso: con wave parallele nel medesimo
  WORKTREE, il gate di A può fallire per scritture di B (falsi fallimenti
  strutturali). Gate su snapshot pinned alla dispatch o quiescenza della wave.
- Crash/resume: il resume esistente rifiuta il candidato mutato da un worker;
  `graph-complete` (gate + delivery + budget + invalidazione) non è dichiarato
  atomico sotto lock; lo stato di runtime non può stare nel grafo congelato e
  la spec non dice dove sta. Serve procedura di resume del grafo
  (riconciliazione delle deliveries `running`) e file di stato separato,
  hashato.
- Finestra corsa pacchetti/invalidazione: `graph-next` scrive i pacchetti su
  disco, un completamento intermedio muta il candidato, il coordinatore può
  dispatchare un pacchetto stantio. Ogni pacchetto incorpora i digest degli
  input al momento della preparazione; il controller rifiuta pacchetti con
  digest non correnti; obbligo di ri-interrogare `graph-next` dopo ogni
  `graph-complete`.

### Tema 4: Provenienza di soglie ed evidenze (P1, P2, P3)

- [P1, High] §3.4 attribuisce la soglia 0.40 alle misure v2: la v2 ha misurato
  con `th = 0.30` più regola OR-decode (`probe_gutsy_v2.py:324-326`, `is_hit =
  letter == "A" or norm_p_yes >= th`), con divergenza interna nell'eval stesso
  (prosa: "P(A) >= 0.15 relativa"). L'unica misura reale a 0.40 (V1,
  `gutsy_exact_catalog_th_0.40`) dà 3/5 critici (60%), non 4/5. Il registro
  delle soglie, meccanismo centrale del disegno, parte con provenienza
  sbagliata: ricostruire prima di scrivere `work-graph.toml`.
- [P2, Medium] Il 78.3% della v2 non è "gutsy da solo": include `code-auditor`
  sempre attivo, regole AST su path e attivazione per lettera decodificata a
  prescindere dalla probabilità. Contraddice il principio "nessun pre-filtro
  Python" previsto per S4 in §6.5 e non è dichiarato in §12.
- [P3, Medium] "La linea v2 produce hunk/file/linea per ogni selezione" è
  falso: C08-C11 hanno `citations: {}` (il passo di citazione in
  `probe_gutsy_v2.py:339` gira solo se `len(hunks) > 1`). Contraddice la
  regola §2.1 (citazione obbligatoria validata meccanicamente) su 4/11 casi.

### Tema 5: Ciclo di vita del sidecar (T1, T2, T3)

- Nessun proprietario di avvio/spento, nessun watchdog, nessun health check,
  nessuna registrazione PID/porta; porte fisse hard-coded (8089 nella v2, 8765
  in un altro script) con rischio di collisione tra sessioni e di
  interrogazione silenziosa del sidecar sbagliato. Caso osservato durante lo
  sviluppo: circa 29 processi python orfani nel working tree. Mitigation:
  PID + porta + hash pesi registrati all'avvio, `sidecar-stop` su ogni stato
  terminale, sweep dei PID stantii con autorizzazione registrata, porta
  dinamica o handshake d'identità (revisione + SHA-256 pesi) con fallimento
  forte su mismatch.
- Il fallback LLM non ha cap runtime: sidecar morto allo snodo 3 di 40 → 37
  snodi degradati in silenzio, con costo che a conversione 100% passa da 0 a
  ~184k token stimati per 11 casi. Mitigation: cap operativo (più del 20% in
  finestra mobile → `ENVIRONMENT_BLOCKED` o `HUMAN_ESCALATION`), probe di
  salute pre-run, segnalazione al secondo ricorso consecutivo.
- Nessun timeout socket lato client (`urllib` senza `timeout` vincolato a §3.3):
  un sidecar appeso blocca il controller per la vita del processo e la soglia
  non viene mai "superata" perché non misurata. Mitigation: `urlopen(...,
  timeout=30)`, `TimeoutError` → ricorso registrato, kill/riavvio dopo 3
  timeout consecutivi.

### Tema 6: Unicità dei produttori (A2)

`graph-next` (project-protocol) "prepara i pacchetti di dispatch su disco", ma
la specifica madre assegna il task-packet a `cycle_packets.py` in
project-lifecycle; project-protocol è foglia senza dipendenze e non può né
delegare né consumare proiezioni della mappa senza dichiararlo. Due renderer
dello stesso artefatto testato sono la classe di difetto caratteristica del
repository. Mitigation: un solo produttore (o `graph-next` restituisce solo
frontiera e riferimenti, o migrazione integrale con la madre emendata).

## Findings Medium

- [L7] Chiusura transitiva ambigua con consumatori parziali e naming `_v2`:
  definire invalidazione per arco di contratto (consumatori di ogni contratto
  il cui digest è cambiato, id stabile con digest nuovo, non id nuovo) unione
  discendenti `needs`; dichiarare `consumes` come arco di scheduling.
- [L8] S5 con `reject` alto: "needs_replan o escalation umana" senza decisore;
  regola deterministica nel registro soglie o quarta opzione esplicita.
- [L9] L'archetipo `bugfix_repro_first` usa `REVIEW_BARRIER`, operatore fuori
  dal catalogo §4 (solo `WAVE_BARRIER`); il validatore rifiuterebbe il proprio
  archetipo; §13.3 testa 3 archetipi ma §6.6 ne definisce 5; typo
  "canditato".
- [T6] Autodegradazione silenziosa della calibrazione: provenienza registrata
  ma non verificata alla connessione; handshake a ogni (ri)connessione con
  scarto forte su mismatch.
- [T7] Nessun budget a wall-clock: aggiungere `wall_clock_budget_s` verificato
  a ogni `graph-next`.
- [T8] Latenze registrate senza normalizzazione (device, backend,
  quantizzazione, batch); le soglie 30 s/120 s sono assolute; probe di classe
  latenza pre-run con `ENVIRONMENT_BLOCKED` se nota-incompatibile.
- [P5] Sidecar su 5 host: nessun probe dimostra che Codex/Copilot/Pi avvino
  server dichiarati da plugin; disponibilità di `uv`/`llama-server` assunta.
- [P6] `gutsy-inference` (Jev-style `/v1/systemone`) mai esercitato: il
  benchmark usa solo `llama-server` via `urllib.request`.

## Findings Low

- [A10] Operatori (§4, project-protocol) e archetipi (§6.2, project-lifecycle):
  due tassonomie con due proprietari e cross-validazione non dichiarata;
  mettere gli scheletri nello stesso `work-graph.toml` o un check meccanico a
  build.
- [P4] Eccesso router AST riportato come 2.11 ma sulla base della riga (11
  casi) il valore è 2.5 (2.11 è della base a 8 casi); errore ereditato da
  `GUTSY_RESULTS.md`.
- [P7] "4 casi scartati per errori di citazione" impreciso: 3 errori di
  citazione (C02/C03/C07) e 1 motivo di 16 parole contro il limite di 15
  (C08).
- [P8] Latenza "~3-4 s/query" sovrastimata: medie per caso 1.5-3.8 s.
- [P9] Nessun fallback dichiarato per S6.
- [L10] Schema `recovery_edges` incoerente tra i due esempi (`to`/`on`
  opzionali non vincolati); il gate della barriera non prevede l'esito
  `skip_con_lente_zero`.
- [L12] Vedi Tema 1 (retry_same_tier senza baseline al primo fallimento).

## Concetti mancanti (dal revisore concettuale)

1. Provenienza della citazione per implementazioni non generative: la citazione
   deve essere assemblata da Python come binding opzione → ID al momento
   dell'enumerazione dei candidati; chi la compone e come si distingue
   "selezione senza citazione possibile" da "violazione della regola".
2. Rappresentazione di audit per le decisioni deterministiche: l'enum
   `implementation: system1|llm_tier1` non copre le scelte del compositore e
   del controller; senza `deterministic` il Decision audit rate è indefinito
   su parte degli snodi.
3. Il macro-grafo come contratto proprio della spec: enumerare i sei stadi
   macro (nomi, confini, mappatura sui terminali) come invariante, così la
   riscrittura del ciclo non altera silenziosamente ciò che è dichiarato
   "fisso e non negoziabile dal modello".

## Numeri verificati ed errori trovati in §12

Verificati corretti contro gli artefatti: recall v2 78.3% (18/23), critici 4/5
(security 1/1, data-integrity 3/4), eccessi 2.4; team 31/39 (79.5%) con 12
fuori perimetro contro 102 di Julia-1; LLM tier1 25.0% (4/16), 33.3% critici,
0.86 eccessi, 7/11 casi validati, ~184k token come stima dichiarata; Julia-1
esatto 0/11; adattato 14/18 (77.8%), 100% critici, 12.44; unione AST+gutsy
69.6% (16/23) con 3.4; AST 65.2% (15/23); 8/8 famiglie con 0 falsi positivi e
p_react 0.003484 sul caso C01-H1; premise-auditor 0 casi positivi; pilota
11+12+8; debolezze T02/T04.

Errori da correggere in §12 (e in `GUTSY_RESULTS.md` dove ereditati):
attribuzione della soglia 0.40 (P1), "citazioni per ogni selezione" (P3),
eccesso AST 2.11 vs 2.5 (P4), "4 casi scartati" (P7), range di latenza (P8),
componente deterministica della v2 non dichiarata (P2).

## Domande di disegno da chiudere prima dell'implementazione

1. Dove vive lo stato di runtime dei nodi (pending/running/gate_failed/
   invalidated) e il conteggio del budget: nel `work-graph.json` congelato, in
   un file di stato separato hashato, o nelle deliveries della record?
2. La riapertura della composizione eredita budget residuo e contatori di
   stallo? Quante riaperture sono ammesse prima di un terminale?
3. L'invalidazione è per arco di contratto o per discendenza `needs`?
   `consumes` è arco di ordinamento? Gli id di contratto restano stabili tra
   versioni?
4. Come si registra un terminale non riuscito nella record senza violare la
   completion esistente: nuovo campo in `work.toml`, `result.json`, o
   `interruption`?
5. Il gate di un nodo parallelo gira sul candidato intero del worktree
   condiviso o su uno snapshot pinned alla dispatch?
6. Chi avvia il sidecar su Codex/Copilot/Pi e con quali prerequisiti
   (`uv`, `llama-server`) verificati?
7. S2: si chiude sul default deterministico (partizione al compositore) prima
   di congelare la tabella degli snodi?

## Ordine consigliato di correzione

1. Provenienza delle soglie (P1) e correzioni numeriche a §12: il registro
   soglie è centrale e parte con numeri sbagliati.
2. Chiusura di S2 (C1): default deterministico, tipo esplicito nel contratto.
3. Estensioni di contratto: `terminal_outcome` (L3), identità delivery
   invalidata (L4), `budget` in `IMMUTABLE` (L11).
4. Semantica di stallo/instabilità: `evidence_delta` canonizzato, trigger
   `VERIFIER_UNSTABLE` (T5).
5. Controller: stati in-flight, atomicità `graph-complete`, procedura resume,
   carry-over budget alla ricomposizione (C2, L5, L6).
6. Sidecar: handshake identità, timeout socket, cap ricorso, sweep orfani
   (T1, T2, T3, T6).
7. Un produttore per il task-packet (A2) e cross-validazione archetipi vs
   catalogo (A10, L9).
