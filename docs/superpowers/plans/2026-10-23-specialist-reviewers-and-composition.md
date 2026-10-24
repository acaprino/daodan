# Specialist Reviewers and Composition Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Repository instructions and the user's context/output economy take precedence over generic execution defaults.

**Goal:** Scrivere tutti gli specialisti canonici e ottenere reviewer tematici predefiniti o ad hoc soltanto dalla loro composizione, preservando copertura e verifiche indipendenti.

**Architecture:** Prima specialisti singolarmente invocabili e qualificati; poi corpi ampi e incarichi contestuali dal registro esistente. Codebase Map fornisce fatti e limiti; preparation prepara, review_roster conserva rigore e obblighi, il compositore assembla, harness e protocollo eseguono e contabilizzano.

**Tech Stack:** Markdown, TOML, Python standard library, compiler e cinque adapter esistenti. Nessuna nuova dipendenza, servizio, modello obbligatorio o scheduler.

**Spec:** [Reviewer specializzati e composti](../specs/2026-10-22-specialized-reviewers-design.md).

## Stato della consegna focalizzata (2026-10-24)

L'ultima indicazione dell'utente richiede di chiudere rapidamente evitando prove
ridondanti. Sono implementati i 64 ruoli canonici e i due method binding distinti,
il resolver dei 13 preset generati, la composizione ad hoc e i relativi consumer
e gate. Il trasferimento finale conserva i corpi ritirati nel run e mantiene gli
ID pubblici. La qualifica sorgente individuale è 54/64; dieci ruoli e i due metodi
restano non qualificati. La campagna comparativa completa di T13 è rinviata.
Queste voci non vengono considerate eseguite dai checkbox originali.

La consegna usa build/parità dei cinque host, verifiche essenziali dei contratti
e quattro prove focalizzate preset/ad hoc. Risultati e limiti effettivi sono nel
[report di consegna](../reports/2026-10-23-reviewer-composition-delivery.md).
Una lacuna obbligatoria resta incompleta anche quando la prova ne conferma la
corretta segnalazione. Nessuna autorizzazione a commit o push è implicita.

## Global Constraints

- «Ogni controllo si scrive una volta, nel suo specialista.»
- «Nessun secondo catalogo runtime o framework di agenti è richiesto da questa decisione.»
- «Non unire incarichi incompatibili per input, autorizzazioni o indipendenza.»
- «Budget e limiti non trasformano omissioni in copertura riuscita.»
- «I passi 1-3 costituiscono la prima fase richiesta. Il passo 4 viene dopo.»
- Default model `inherit`; reviewer read-only sul prodotto, scrittura solo delle consegne autorizzate.
- Il riordino del 22 ottobre è intermedio; i suoi risultati non certificano questa implementazione.
- Preservare lavoro concorrente, compresi Codebase Map e routing. Nessun commit globale, reset o push implicito.
- Sorgenti in kernel/adapter/compiler; export e cataloghi root generati. Prima del commit posseduto: versioni dei plugin toccati, marketplace, build universale e parità.
- Non aumentare tetti di istruzioni. Parole, token, costo ed efficacia sono misure distinte.
- Le milestone si espandono nel ledger in micro-task da massimo quattro file, fino a sei con eccezione motivata. Pubblicazione degli export separata e posseduta dal coordinatore.

## Review Focus

1. Grafo incompleto o di un altro candidate: obblighi conservati e gap espliciti (T9).
2. Specialista condiviso fra preset o su scope diversi: deduplicare solo la stessa obbligazione (T8/T10).
3. Worker consegnato che omette un membro: il gate obbligatorio non passa (T11).
4. Tipi corretti ma mock o serializzazione divergenti: finding di contratto distinto dalla regola di dominio (T2).
5. Membro di un altro plugin/host: identità, root, riferimenti e permessi conservati nel composto (T8/T12).

---

## Consegne e dipendenze

| Consegna | Task | Risultato |
|---|---|---|
| A: specialisti | T0-T7 | Mandati censiti; specialisti registrati e valutati singolarmente. Vecchi ampi transitori. |
| B: composizione | T8-T13 | Ampi generati, preset e ad hoc dalle stesse foglie; nessuna checklist ampia parallela. |

T1 precede T2-T6. Authoring parallelo su file distinti; coordinatore proprietario
di registrazioni e common. T7 chiude A. T8 e T9 possono procedere separatamente
dopo A; T10 li unisce, T11 protegge il completamento, T12 integra i consumer,
T13 chiude B. La stesura non chiude task di implementazione.

## File e interfacce

| File | Responsabilità |
|---|---|
| `plugins/<owner>/roles/<role>.md` | Unico mandato specialistico canonico. |
| `plugins/<owner>/plugin.toml` | Registrazioni; in B membri declarativi, mai prompt TOML. |
| `scripts/daodan/reviewer_catalog.py` | Unico catalogo compilato: identità, trigger, prerequisiti, digest, binding, membri. |
| `plugins/senior-review/skills/review-quality-gates/references/reviewer-common.md` | Scope, evidenza, provenienza, coverage e consegna. Provider ricevono common dal brief, senza dipendenze inverse. |
| `plugins/project-protocol/skills/project-protocol/scripts/review_roster.py` | Rigore e obblighi meccanici; riusare `compute` e `check`. |
| `plugins/senior-review/contracts/*.toml` | I sette contratti esistenti, estesi senza un ottavo record parallelo. |
| `plugins/project-protocol/skills/project-protocol/scripts/run_state.py` | Review, job, delivery e gate sul candidate. |
| `scripts/daodan/render.py` | Corpi registrati, catalogo e risorse inline con resolver comune. |

Firme nuove da implementare, non API esistenti:

- `scripts/daodan/role_bodies.py`: `resolve_role(registry: dict, owner: str, role: str) -> dict`, con `metadata`, `parts`, `members`, `source_hashes`. Ogni parte conserva owner, fonte e semantica del root.
- `scripts/daodan/composition.py`: `assemble_body(parts: list[dict], common: list[dict]) -> str`; `compose_jobs(roster: dict, catalog: dict, bindings: dict) -> list[dict]`; `validate_composition(roster: dict, jobs: list[dict], catalog: dict) -> list[str]`. Solo stdlib, senza import del compiler o discovery arbitrario. Il compiler copia questo stesso modulo in `skills/review-preparation/scripts/composition.py` del package senior-review: unica implementazione meccanica build/runtime.
- `review_roster.compute(...)`: conservare gli argomenti attuali; aggiungere il keyword opzionale `context: dict | None = None` e `--context` alla CLI tecnica. Riferimenti a brief, basis, snapshot e packet esistenti, senza nuovi parametri utente.

Il catalogo mantiene `kind=role|method-binding`; `members` identifica le foglie
del composto. Il roster aggiunge `required_specialists` e `jobs`. Obbligo:
`specialist_id`, `scope_id`, evidenza. Job: `id`, `role`, `specialist_ids`,
`scope_id`, `input_mode`, `body_sha256`, `output_path`. Binding/result/ledger
aggiungono `job_id` ed esiti per membro; finding canonici unici con riferimenti
agli obblighi. Record storici senza questi campi restano leggibili; campi
presenti sono validati strettamente.

## T0: Baseline e matrice di migrazione

**Files:** creare `docs/superpowers/reports/2026-10-23-reviewer-specialist-migration.md`; leggere spec, corpi e riferimenti caricati. **Consumes:** candidato/autorizzazioni. **Produces:** controllo → specialista → caso, con fonte e delta posseduto.

- [x] Acquisire branch, HEAD, stato completo e digest nel run project-protocol; separare lavoro precedente e concorrente.
- [x] Censire i 21 ruoli e due method binding attuali, inclusi skill/reference obbligatori. Mappare tutti i controlli oltre a T01-T50/S01-S03.
- [x] Assegnare difetto e `must_not_report`/alternativa corretta, riusando `evals/senior-review/cases/` e smoke set. Controllo senza destinazione o prova resta aperto.
- [x] Molteplicità e controprove restano obblighi trasversali, non specialisti separati. Motivare ulteriori scissioni prima dell'authoring.

Censimento e lacune: [matrice T0](../reports/2026-10-23-reviewer-specialist-migration.md). La qualifica resta aperta nelle task successive; le prove proposte non sono esecuzioni.

## T1: Contratto comune e qualifica

**Files:** modificare `reviewer-common.md`, `tests/test_reviewer_catalog.py`, `evals/senior-review/README.md`; creare `evals/senior-review/specialist-cases.md`. **Produces:** protocollo di qualifica, nessun nuovo runner LLM.

- [x] Estendere test: foglia non registrata rende indisponibile il dispatch; input obbligatorio mancante produce coverage fallita. Non misurare qualità con parole chiave del prompt.
- [x] Template breve: mandato/attivazione, input, ricerca causale, controevidenza, confini, output. Envelope esistente, confidence numerica, common/knowledge una volta.
- [x] Eval in contesto fresco senza oracle/peer/scorecard; report, snapshot/hash, gap e costo persistiti. Scorer separato usa meccanismi e anti-finding del protocollo esistente.
- [x] Verificare no-findings, formato e statico/runtime separati; un errore di consegna non diventa difetto del prodotto.
- [x] Eseguire `python -m unittest discover -s tests -p test_reviewer_catalog.py -v` e `python tests/test_skill_load_budget.py`.

Contratto e protocollo definiti in [common](../../../plugins/senior-review/skills/review-quality-gates/references/reviewer-common.md),
[qualifica](../../../evals/senior-review/README.md#specialist-qualification) e
[template/casi](../../../evals/senior-review/specialist-cases.md). Le spunte di T1
attestano il protocollo e i controlli meccanici, non la qualifica comportamentale
delle foglie. Nessun nuovo runner o schema.

Verifica T1 conclusa: 8 test catalogo/consegne e 10 test pipeline passati;
parità dei cinque export e controlli di coerenza superati. Il protocollo resta
entro 1682 parole; il metodo di authoring conserva tutti gli obblighi in un
riferimento di 208 parole, caricato quando serve e conteggiato nel passo dedicato
(1890 parole). Intervista: 397 parole. Nessun limite preesistente aumentato.

Verifica locale completa: 92 moduli, 1600 casi passati, 64 esclusioni dichiarate
per dipendenze opzionali o piattaforma, nessun errore irrisolto. La review
indipendente ha verificato la conservazione degli obblighi. Prove e limiti nel
[rapporto finale T1](../../../.daodan/runs/reviewer-contract-t1-final-20261023/verification.md).
La qualifica comportamentale degli specialisti resta in T2-T7.

## T2-T6: Authoring, una micro-task per foglia

**Files per foglia:** `plugins/<provider>/roles/<role>.md`; nuovo caso solo se
manca sotto `evals/senior-review/cases/<provider>-<role>/case.md`.
Registrazioni e matrice T1 hanno micro-task separate del coordinatore.
**Consumes:** fonte/prove T0. **Produces:** reviewer singolarmente invocabile e qualificato.

Per ogni ruolo della tabella:

- [ ] Fissare difetto atteso, limite e controprova valida; oracle indipendente dalla nuova implementazione.
- [ ] Scrivere/restringere il corpo, mantenere controlli e riferimenti del provider; eliminare quote, score inventati e stop per letture.
- [ ] Registrare e verificare invocabilità nei cinque export, `inherit` e permessi necessari alla review. Nessuna dipendenza circolare verso senior-review.
- [ ] Eseguire T1: difetto trovato, controprova non segnalata, consegna/gap corretti. I soli test strutturali non chiudono il ruolo.
- [ ] Registrare casi, outcome e controlli conservati nella matrice. Broad transitori e process roles non diventano nuove foglie.

Ogni nome `r` del provider `p` indica esattamente `plugins/p/roles/r.md`.
Nuovi nomi sono target di implementazione; quelli conservati richiedono qualifica.

| Task/famiglia | Provider | Ruoli canonici |
|---|---|---|
| T2 Sicurezza | senior-review | `authorization-auditor`, `session-delegation-auditor`, `secret-exposure-auditor`, `input-validation-auditor`, `untrusted-resource-auditor`, `browser-security-auditor`, `callback-authenticity-auditor`, `ai-boundary-auditor`, `audit-trail-auditor` |
| T2 Contratti | senior-review | `api-contract-auditor` conservato: confine producer/consumer |
| T3 Dati | senior-review | `transaction-integrity-auditor`, `schema-coherence-auditor`, `cache-consistency-auditor`, `data-representation-auditor`, `data-retention-auditor` |
| T3 Distribuzione | senior-review | `message-delivery-auditor`, `remote-effect-auditor`, `service-resilience-auditor` |
| T3 Esecuzione | senior-review | `chicken-egg-detector`, `resource-lifecycle-auditor`, `temporal-resilience-auditor`, `logic-integrity-auditor` conservati |
| T4 Prestazioni | senior-review | `sql-efficiency-auditor`, `algorithmic-cost-auditor`, `asset-delivery-auditor`, `capacity-quota-auditor`, `runtime-cost-auditor` |
| T4 Operatività | senior-review | `observability-auditor`, `service-health-auditor`, `release-compatibility-auditor`, `environment-binding-auditor`, `feature-flag-auditor`, `recovery-auditor` |
| T5 Accessibilità/UI | senior-review | `accessible-navigation-auditor`, `accessible-perception-auditor`; `ui-race-auditor` conservato |
| T5 Correttezza/cleanup | senior-review | `local-correctness-auditor`, `local-concurrency-auditor`, `application-reachability-auditor`, `dependency-usage-auditor`, `artifact-lifecycle-auditor` |
| T6 Testing | testing | `test-suite-structure-auditor`, `test-oracle-auditor`, `test-reliability-auditor`, `journey-protection-auditor`, `contract-test-auditor`, `capacity-test-auditor`, `ai-evaluation-auditor` |
| T6 React | react-development | `react-effects-auditor`, `react-render-cost-auditor`, `react-bundle-auditor`, `react-dataflow-auditor` |
| T6 TypeScript | typescript-development | `type-soundness-auditor`, `typed-boundary-auditor` |
| T6 Piattaforme | platform-engineering | `browser-compatibility-auditor`, `offline-lifecycle-auditor`, `native-lifecycle-auditor`, `desktop-bridge-auditor`, `app-distribution-auditor` |
| T6 Astrazioni | abstraction-architect | `concept-ownership-auditor`, `abstraction-fit-auditor` |
| T6 Python | python-development | `python-semantics-auditor`; metodi audit/dead-code read-only |
| T6 Workspace/processo | repo-hygiene / senior-review | `workspace-auditor` focalizzato; `premise-auditor` indipendente; dependencies-method mantiene il metodo dependency-audit |

### Controlli e prove da preservare

| Famiglia | Prove obbligatorie |
|---|---|
| Sicurezza/contratti | Tenant/IDOR, controlli input→sink. Contratto autorevole e tipi/mock/serializzazione: ID stringa emesso numero è difetto; shared type valido in un confine atomico non richiede OpenAPI. Schema valido non prova regole di dominio. |
| Dati/distribuzione | Writer alternativi, precisione/date/NULL/versioni; replay/ack/DLQ/duplicati; fencing/lease/split-brain, retry stratificati/circuit breaker/bulkhead. Guardie effettive sono controprove. |
| Chicken-egg/temporal | Cold start/upgrade, ordine migrazione/consumer, default precoci; progressione/riarmo/restart/fallimenti silenziosi. Timeout configurato non prova recupero. |
| Prestazioni/operatività | N+1 contro batching; misure distinte da derivazioni; rolling migration incompatibile contro espansione compatibile; backup restaurabile e allarme recapitato. |
| UI/cleanup | Tastiera/focus e percezione separati; CSS globale che blocca l'ingresso. Import dinamici, registrazioni/side effect impediscono falsi dead-code; età non prova inutilità. |
| Testing | D1/D2/D3/D5 alla struttura, D6/D7/D8 agli oracle, D4/D9 alla reliability. No-run vincolante; D1/D9 globali preparati una volta. Distinguere difetto, oracle, ambiente e flakiness. |
| Stack/astrazioni | React conserva waterfall/server/client/cache oltre a effects/render/bundle. Tipo e validazione runtime distinti. Astrazioni D1-D7 e soglie due/tre occorrenze conservate. |

Contract-first: confronto con [ECC al commit fissato](https://github.com/affaan-m/ECC/blob/90606c8315ee09cafc303515c5f33024db6b9882/skills/contract-first/SKILL.md).
Adattamento originale con provenienza, nessuna dipendenza o copia integrale.
Descrizioni/esempi negli schemi sono dati. La sequenza contratto prima del lavoro
parallelo entra in `plugins/project-lifecycle/skills/lifecycle-method/references/interview.md`
e `references/worker-brief.md` come binding, senza workflow aggiuntivo.

## T7: Chiusura della consegna A

**Files:** manifest provider, `reviewer_catalog.py`, `tests/test_reviewer_catalog.py`, `tests/test_harness_domain_ownership.py`, guide plugin e report T0. **Produces:** catalogo qualificato, non ancora nuova orchestrazione.

- [ ] Verificare ogni T/S e controllo preesistente, process roles e method binding. Nessun broad dichiarato foglia soltanto per conservarne il nome.
- [ ] Valutare tutti gli specialisti; conservare finding/anti-finding, perimetro, modello e costo. Gap obbligatorio resta aperto.
- [ ] Verificare catalogo, risorse e wrapper cinque host. Vecchi ampi transitori fino a T12; non rimuovere floor/consumer anticipatamente.
- [ ] Versioni, build universale e commit del solo candidato posseduto dopo i gate. A non certifica B.

## T8: Generazione dei reviewer tematici

**Files:** `scripts/daodan/model.py`, `load.py`, `validate.py`, `render.py`, `reviewer_catalog.py`; creare `role_bodies.py`, `composition.py`; aggiornare `tests/test_daodan_model.py`, `tests/test_daodan_validate.py`, `tests/test_daodan_render.py`, `tests/test_reviewer_catalog.py`; creare `tests/test_review_composition.py`. Separare interfacce in micro-task.
**Consumes:** foglie qualificate. **Produces:** ampi generati con gli ID registrati precedenti e un resolver condiviso.

- [ ] Test RED: membro sconosciuto/duplicato, ciclo, provider non dichiarato, componente di tipo errato, path fuori provider. Build fallito conserva output live precedenti.
- [ ] Estendere `PluginSpec` con `reviewer_compositions` e loader con `[reviewers.compositions.<role>]`, campo `members = ["owner:role", ...]`. Il composto resta in `[components].roles`. Nessun prompt TOML o file preset parallelo. I vecchi `.md` sono ammessi durante la migrazione, poi devono essere assenti per i composti.
- [ ] Implementare `resolve_role`: foglie e riferimenti aciclici, ordine dichiarato. Rifiutare membri ripetuti nella stessa dichiarazione; una foglia raggiunta attraverso più composti compare una volta, al primo incontro. Conservare metadati della foglia; composto con `inherit`, descrizione derivata e permessi richiesti dai metodi entro il grant della review. Non assorbire premise/verificatori in discovery.
- [ ] Usare lo stesso resolver per rendering nativo, `_dispatch_bindings`, catalogo e provenance. Trust/secret validation e lint dipendenze vedono la medesima chiusura, non soltanto i `.md` rimasti. Esistenza di un componente generato non significa sorgente assente valido per ogni ruolo.
- [ ] Build e runtime usano `assemble_body`: common una volta, owner e metodo di ogni parte conservati. Non deduplicare frasi simili di controlli distinti. Catalogo con riferimenti ai corpi, non tutti i prompt incorporati.
- [ ] Copiare il modulo stdlib nella skill installata come da Interfacce; verificare byte/digest del medesimo algoritmo distribuito e bundled-path gate sul package generato.
- [ ] PASS: `test_generated_body_keeps_all_members`, `test_cross_provider_roots_survive_on_all_hosts`, `test_common_is_loaded_once`, `test_invalid_composition_preserves_outputs`.

Destinazioni: security→T2; data-integrity→T3 dati; distributed-flow→T3
distribuzione; performance→T4 prestazioni e stack pertinente; operability→T4
operatività; accessibility→due foglie T5; cleanup→reachability/dependency-usage/
artifact-lifecycle; code→local-correctness/local-concurrency e controlli
specialistici richiesti dal floor light; test-suite/React/TypeScript/platform/
abstraction→famiglie T6. Python-method unisce Python semantics, metodi read-only
e reachability pertinenti, senza dipendenze inverse. Ogni controllo sorgente ha
un membro nella matrice T0 prima di cancellare il vecchio corpo.

## T9: Packet reali del grafo e selezione

**Files:** `review_roster.py`; `plugins/senior-review/skills/review-preparation/references/candidate-grounding.md`, `stack-dimensions.md`; `tests/test_review_roster.py`.
**Produces:** obblighi specialistici con evidenza/gap sul candidate corretto.

- [ ] Test d'integrazione con packet realmente prodotti da `build_edit_impact` e `build_stale_callers`: delta effects rilevato; variazione storica estranea non alza il tier corrente. Non limitarsi a dizionari ad hoc.
- [ ] Correggere adapter: `edit-impact/v2` usa `symbol_id` e `recent_changes[].change_kind`; la cronologia è contesto. Il delta deriva da `stale-callers.changed` base/candidate con digest legati agli snapshot. Schema/binding estranei non diventano segnali autorevoli.
- [ ] Conservare caller totals, omitted neighbours, unknown/truncated targets, blind spot, parser/source errors e freshness. Un packet non vuoto non prova mappa completa. Legacy senza binding rimane gap, mai prova di copertura.
- [ ] Unire grafo, sorgenti, configurazioni e requisiti nel brief. Nessuna dipendenza da embedding o API solo pianificate in `2026-10-23-code-context-and-scope.md`; integrare quel lavoro successivamente per il suo contratto, senza modificarlo qui.
- [ ] Changeset conserva entrambi i lati, rimozioni/rinomine e untracked. Full/dir content usa inventario corrente e requisiti, senza diff artificiale per dedurre novità. Doc/spec/plan mantiene il proprio metodo. Nessun nuovo comando pubblico o parametro utente.
- [ ] CSS/markup/config e `.github/` esplicita restano in scope anche fuori mappa. `do_not_touch` non elimina caller da validare. Applicabilità sconosciuta è gap, non `false` implicito.
- [ ] PASS: `test_real_effect_delta_selects_required_specialist`, `test_old_history_is_not_candidate_delta`, `test_stale_or_truncated_graph_keeps_gaps`, `test_content_audit_keeps_unchanged_requirements`, `test_hidden_config_and_static_css_remain_reviewable`. Conservare probe humanize small e light a una discovery.

## T10: Composizione contestuale e preset

**Files:** `scripts/daodan/composition.py`, `reviewer_catalog.py`; `review-preparation/SKILL.md`, `references/team-review.md`; `tests/test_review_composition.py`.
**Consumes:** catalogo risolto e roster T9. **Produces:** job deterministici con corpo, scope e digest.

- [ ] Test RED: preset e ad hoc sugli stessi membri/scope danno la stessa coverage; obbligo identico unito, stesso specialista su scope differenti distinto.
- [ ] Implementare `compose_jobs`: obblighi del roster, preset espansi, membri applicabili al contesto; unire solo scope/input/permessi compatibili. Ordine stabile, ID dai binding, nessun LLM che riscriva metodi.
- [ ] Ad hoc usa `project-protocol:isolated-worker`, già supportato. Il job ID è identità di consegna, non agent type registrato. Preset e foglie singole restano invocabili; provider/root/versione/hash derivano da inventario verificato e catalogo, mismatch è fallimento esplicito.
- [ ] Budget insufficiente separa job mantenendo obblighi e residuo. Light resta una discovery: se il contratto non entra, incompleto/advice, nessun fan-out nascosto.
- [ ] Preparare knowledge_selection una volta e assegnare dimensioni a job/membri reali. Candidate, corpo, reference o knowledge cambiati invalidano il binding; presenza del file non prova freshness.
- [ ] PASS: `test_preset_and_adhoc_share_canonical_members`, `test_duplicate_is_scoped`, `test_changed_member_invalidates_body_digest`, `test_blind_or_verifier_input_cannot_merge`, `test_budget_omits_no_required_member`.

Oracle di copertura per `test_budget_omits_no_required_member`, nella suite
`unittest` esistente: preparare catalogo/binding validi e un roster con due
specialisti richiesti su due scope, poi ridurre il budget. La funzione può
separare i job o fallire esplicitamente; se restituisce un piano eseguibile,
devono valere queste asserzioni. `validate_composition` restituisce una lista
vuota soltanto quando il piano soddisfa il contratto.

```python
jobs = compose_jobs(roster, catalog, bindings)
required = {(r["specialist_id"], r["scope_id"])
            for r in roster["required_specialists"]}
covered = {(member, job["scope_id"])
           for job in jobs for member in job["specialist_ids"]}
self.assertLessEqual(required, covered)
self.assertEqual(validate_composition(roster, jobs, catalog), [])
self.assertTrue(validate_composition(roster, [], catalog))
```

In `test_duplicate_is_scoped`, verificare inoltre che ciascuna coppia richiesta
compaia esattamente una volta nei job discovery compatibili; i verificatori
indipendenti hanno incarichi distinti. Copertura completa non basta a provare
correttezza dei corpi: i casi T1 e T13 mantengono quell'oracolo separato.

## T11: Gate per ogni membro

**Files:** `plugins/senior-review/contracts/reviewer-binding.toml`, `reviewer-selection.toml`, `reviewer-result.toml`, `delivery-ledger.toml`; `plugins/project-protocol/contracts/work.toml`, `skills/project-protocol/scripts/run_state.py`; `tests/test_project_protocol.py`, `tests/test_review_composition.py`.
**Produces:** expected set fissato prima del dispatch e coverage verificata alla chiusura.

- [ ] Estendere i record come nelle Interfacce. Campi presenti validati strettamente; record storici conservano il proprio contratto. Nessun ottavo schema/file parallelo.
- [ ] Validare il piano completo con `validate_composition` prima del dispatch. `check` continua ad autorizzare singoli dispatch intermedi; un run aperto non deve avere già consegnato tutto.
- [ ] Al gate finale confrontare job attesi, ruolo, membri, scope, snapshot/hash ed esiti per membro. Omissione, duplicato che nasconde un obbligo, ruolo estraneo, risposta vuota o coverage assente impediscono il pass.
- [ ] Barriera e successo distinti: failed può essere contabilizzato ma non soddisfa un controllo obbligatorio. Lens/critic hanno delivery proprie; isolated-worker ausiliario non soddisfa discovery solo perché condivide il ruolo.
- [ ] Verificare blind_derivation/critic e check richiesti secondo tier/eleggibilità. `--fast`/`--no-context` non li cancellano; zero finding esaminati non equivale a membro mancante.
- [ ] PASS: `test_missing_member_blocks_completion`, `test_failed_member_is_accounted_not_passed`, `test_duplicate_job_cannot_hide_missing_scope`, `test_auxiliary_worker_cannot_satisfy_discovery`, `test_legacy_review_remains_readable`.

## T12: Consumer e ritiro dei corpi ampi

**Files:** sidecar di `review-branch`, `continue-task`, `finish-task`, `fix-bug`, `new-feature`, `refactor-code`, `run-maintenance` in `plugins/daodan/workflows/`; riferimenti preparation/method/consolidation senior-review; `plugins/project-lifecycle/skills/lifecycle-method/references/verify.md`; `tests/test_review_pipeline_ports.py`, `test_method_dispatch_contracts.py`, `test_harness_domain_ownership.py`, `test_daodan_operational_binding.py`.

- [ ] Unica preparation→roster→jobs→ledger→verifica→report. Collegare anche `review-method/references/light.md`, con la sua preparazione distinta; nessun secondo coordinatore/selettore nel lifecycle.
- [ ] Conservare allowlist/provider dei sette consumer, foglie singole e worker inline. Wrapper non neutralizza istruzioni annidate; leggere un ruolo non equivale a dispatcharlo come skill.
- [ ] Confrontare ogni vecchio ruolo con matrice T0 e casi; eliminare `.md` ampio manuale e copie nei riferimenti solo dopo copertura verificata. Conservare ID pubblici compatibili e documentare migrazioni necessarie.
- [ ] Verificare cinque host anche attraverso reference e singolo worker: capability negative, report permissions, model inheritance, provider richiesto mancante. Ad hoc non presume registrazione di agenti a runtime.
- [ ] PASS: suite consumer e `test_named_and_inline_compositions_have_same_members` per tutti i cinque host; light una discovery, branch floor/support/lenti e unico report owner.

## T13: Qualifica comparativa e consegna B

**Files:** `evals/senior-review/README.md`, `RESULTS.md`, scorecard selezionate; `docs/plugins/senior-review.md`, guide provider; creare `docs/superpowers/reports/2026-10-23-reviewer-composition-delivery.md`; istruzioni canoniche solo per verità durevoli, poi sync AGENTS.

- [ ] Contesti freschi: consumer AMQP→DB, rollout/schema, UI cascade/focus, mock/runtime divergenti e stato multiistanza. Confrontare broad precedente, foglie singole e composto sullo stesso snapshot/modello/effort, senza oracle nei worker.
- [ ] Nessun difetto noto richiesto perso, nessun anti-finding trattenuto, nessuna falsa dichiarazione runtime/coverage. Nuovi FP esaminati. Controllo perso richiede correzione e riesecuzione prima del ritiro definitivo.
- [ ] Misurare preparazione, contesto, tool, retry, letture, token disponibili, wall time e dispatch. Costo non osservabile resta non misurato; calo di parole non chiude l'efficacia.
- [ ] Versioni dei plugin effettivamente toccati/marketplace e tutti gli export. Eseguire i gate sotto sul candidato finale, ripetendo dopo modifiche soltanto le verifiche pertinenti.
- [ ] Provare preset e ad hoc sul percorso reale disponibile. Per host registrare versione, percorso e limiti; rendering e live execution restano distinti. Capability obbligatoria indisponibile mantiene aperta quella consegna.
- [ ] Aggiornare report/guide, stage del solo delta posseduto. Commit/push rispettano perimetro e autorizzazioni del run; preservare lavoro concorrente.

## Comandi di verifica

Modulo mirato: `python -m unittest discover -s tests -p test_review_roster.py -v`.
Sostituire con `test_reviewer_catalog.py`, `test_review_composition.py`,
`test_project_protocol.py` o il modulo della task. I moduli nuovi vengono creati
dalla task proprietaria, non sono dichiarati già esistenti.

```text
python -m unittest discover -s tests -v
python scripts/lint_dependency_graph.py
python scripts/lint_bundled_paths.py
python scripts/lint_plugin_registration.py
python scripts/lint_host_vocabulary.py
python scripts/lint_fact_anchors.py
python scripts/sync_plugin_docs.py --check
python scripts/sync_codex_instructions.py --check
python scripts/daodan_build.py --check --support
python adapters/copilot/policies/xray-guard/test_xray_guard.py
```

Atteso exit 0 dei gate richiesti; skip elencati, mai contati come esecuzioni
riuscite. Windows: directory temporanea posseduta ereditata tramite `TMP`, `TEMP`,
`TMPDIR` oltre a `tempfile.tempdir`. Test che escludono `.daodan` richiedono
fixture senza quel nome negli antenati. Link/junction richiedono capacità reale:
diagnosticare ambiente prima di cambiare prodotto; riesecuzioni e accessi
aggiuntivi conservano il proprio log.

## Ripresa ed esecuzione

Run project-protocol e agenda conservano baseline, scope, hash, esiti, gate,
ruling e prossimo micro-task. Le caselle indicizzano il ledger, non sono una
seconda verità. Recovery dai byte pre-fase, mai da HEAD precedente presunto o
pulizia globale.

Raccomandazione: esecuzione prevalentemente nativa per mantenere contesto e
contenere costi, delega di famiglie indipendenti e review fresca ai confini di
consegna. Qualunque metodo conserva ledger e gate. Le task restano aperte finché
implementazione ed evidenza non le chiudono.
