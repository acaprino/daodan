# senior-review

**Responsabilità:** comprendere l'oggetto da rivedere, scegliere i reviewer pertinenti leggendo i loro mandati e comporre il minimo lavoro di review giustificato dalle evidenze.

L'unica dipendenza di prodotto è **Codebase Map**. Le micro skill e i controlli restano di proprietà di senior-review; un reviewer è un incarico temporaneo sull'intero perimetro, diviso in gruppi di file sotto un budget quando la base è `content`, composto da mandato, contesto, istruzioni selezionate e risultato atteso. Una skill non implica un agente separato.

Il risultato distingue difetti dimostrati, verifiche svolte e lacune. Nessuna selezione semantica garantisce di individuare tutti i difetti.

## Prerequisito

Prima di avviare una review, **Codebase Map deve aver già completato la mappatura dell'intero progetto**. La Phase 0 e la Phase 1 usano gli indici e i tool di quel run esistente; nessuna fase della review analizza il progetto al suo posto. Se la mappa completa manca, eseguire prima Codebase Map.

## Phase 0: cosa rivedere

La richiesta («rivedi X») diventa l'elenco dei file da rivedere, in quattro passi: trova i nomi con lo strumento più economico; conferma ogni file con la riga che dimostra la pertinenza, rispettando i limiti espliciti e trattando gli altri nomi come punti di partenza e includendo i chiamanti coinvolti se la richiesta riguarda una modifica; fermati quando le evidenze bastano o a circa 6 interrogazioni e 10 letture, dicendo perché; rispondi con uno di tre esiti, `resolved`, `partial` o `clarify`. Il perimetro è ciò che la review giudica; ciò che legge per giudicarlo è contesto di Phase 1. Tutto il resto è giudizio del reviewer, motivato.

Spec: [`docs/specs/2026-11-04-review-scope-resolution.md`](../../docs/specs/2026-11-04-review-scope-resolution.md). Strumenti di Codebase Map, una riga ciascuno: `plugins/codebase-map/skills/map/references/tools-guide.md`. Testo operativo: `skills/review-preparation/references/team-review.md`, sezione "Request to files". Prova: `benchmarks/scope-resolution/`, su 9 casi, una esecuzione per caso: i file indispensabili ci sono sempre, sia su Haiku sia su Opus; l'esito coincide con l'atteso in 7 casi su Haiku e 9 su Opus. Vale per la review di branch (`team-review.md`) e per quella leggera (`light.md`, `code-review.md` caso W). Una review completa con questa Phase 0 non è ancora stata eseguita.

## Esecuzione: aiutante leggero, chiamate a ondate

**Regola.** Job, lenti 1-3 e critico girano su `senior-review:isolated-worker` (`roles/isolated-worker.md`), che ha solo cinque strumenti: Read, Write, Glob, Grep, Bash. La Lens 0 resta su `premise-auditor`. Il coordinatore chiama gli aiutanti a ondate: ogni passo che non dipende da un altro parte in un solo turno. I passi sono: tutti i job, poi le Lens 0, poi le lenti 1 e 2 di tutti i finding, poi la Lens 3 dei finding sopravvissuti, infine il critico.

**Perché.** Il costo di una review dipende poco dal codice letto. Dipende soprattutto da quanto contesto il modello rilegge a ogni passo:

- **Contesto iniziale.** Un aiutante, prima di fare qualcosa, carica il proprio contesto iniziale e lo rilegge a ogni passo. L'aiutante generico dell'host porta le definizioni di tutti gli strumenti installati e l'elenco di tutte le skill. A un job di review servono cinque strumenti.
- **Turni del coordinatore.** Anche il coordinatore rilegge tutto il proprio contesto a ogni turno. Chiamando un aiutante per turno, più un turno di attesa, le riletture si moltiplicano.

Misure del 2026-11-08, modello Sonnet 5.5, run del benchmark [`whole-source-coverage`](../../benchmarks/whole-source-coverage/README.md):

| Misura | Valore |
|---|---|
| Contesto iniziale dell'aiutante generico | 128.300 token |
| Contesto iniziale di `isolated-worker` | 20.400 token |
| Codice letto da un job di gruppo | circa 3.000 token |
| Turni del coordinatore, metodo a gruppi | 103, di cui 26 chiamate una per turno e 26 di attesa |
| Contesto riletto dal coordinatore a ogni turno | circa 270.000 token |

I due valori iniziali vengono da una prova a parte, in cui ogni aiutante risponde «OK» senza usare strumenti.

**Schema.**

```
Prima: un aiutante per turno               Ora: un'ondata per passo

coordinatore                               coordinatore
 ├─ chiama job-01, attende                  ├─ chiama job-01…04, attende tutti
 ├─ chiama job-02, attende                  ├─ chiama Lens 0 di F1…F5, attende
 ├─ chiama job-03, attende                  ├─ chiama Lens 1 e 2 di F1…F5, attende
 ├─ …                                       ├─ chiama Lens 3 dei sopravvissuti, attende
 └─ 26 chiamate = 52 turni                  └─ chiama il critico, attende

ogni aiutante parte da ~111.000 token      ogni aiutante parte da ~20.000 token
```

**Esempio.** Review di sicurezza di un servizio di note di 12 file, in 4 gruppi, con 5 finding da verificare. Il lavoro resta lo stesso: 4 job, 20 lenti e 1 critico, cioè 25 aiutanti.

- **Prima.** Ognuno dei 25 aiutanti rilegge circa 111.000 token a ogni passo, per leggere circa 3.000 token di codice. Il coordinatore spende 52 turni solo per chiamare e attendere.
- **Ora.** Ogni aiutante rilegge circa 20.000 token a ogni passo. Il coordinatore chiama in 5 ondate, una per passo.

Stima ricavata dalle trascrizioni di quella run: circa un terzo in meno, da 8,9 a circa 5,7 milioni di token equivalenti. Non è ancora misurata da una run nuova.

**Nessun ripiego.** L'aiutante generico dell'host (in Claude Code `general-purpose`) non sostituisce `isolated-worker`. Se il plugin non è caricato, la review dichiara non disponibili job, lenti e critico e resta incompleta: costerebbe sei volte tanto per aiutante, e il costo deve restare una scelta, non un effetto nascosto. Succede per esempio in una copia `git worktree` senza `.claude/settings.local.json`: prima di una review lì, copiare quel file.

Le chiamate a ondate restano isolate: nessun aiutante vede i finding degli altri prima di consegnare.

## Stato

Versione **1.1.0**. Dipendenza richiesta: solo `codebase-map`. I ruoli compositi sono definiti in `[reviewers.compositions]` di `plugin.toml`, non come file ruolo.

Installazione: `claude plugin install senior-review@daodan` (marketplace `acaprino/daodan`; richiede `codebase-map`). Ingresso: la skill `/senior-review:review-method`. Le review eseguite sul benchmark `benchmarks/scope-resolution/` e i loro costi sono registrati nel suo README: il criterio di costo non è ancora raggiunto. Il catalogo dei reviewer è `plugin.toml`: `skills/review-preparation/scripts/composition.py catalog` lo legge e scrive `CATALOG.json`; `bind` lega il roster ai job.

Nei testi `${CLAUDE_PLUGIN_ROOT}` indica la radice del plugin installato; in Bash la variabile non è impostata e il percorso si ricava dalla directory della skill. I ruoli compositi (`code-auditor`, `security-auditor`, …) non hanno un file agente: `composition.py` li espande nei membri, mentre chi li nomina come agente da dispacciare (`investigation-method`) non li trova. React, TypeScript, Tauri, testing, prior art, workspace hygiene e i confini architetturali dichiarati hanno ruoli propri (`react-auditor`, `typescript-auditor`, `tauri-auditor`, `testing-auditor`, `prior-art-auditor`, `workspace-hygiene-auditor`, `boundary-auditor`). `tauri-auditor` è una composizione di quattro classi (`tauri-ipc`, `tauri-hardening`, `tauri-sync`, `tauri-reliability`) e si attiva su `src-tauri/`, `tauri.conf.json`, `capabilities/` e chiamate `@tauri-apps/*`; `testing-auditor` sui file di test toccati e al rigor `deep`; `prior-art-auditor` al rigor `deep`; `workspace-hygiene-auditor` su `.gitignore`, output di build e residui, ed è membro di `cleanup-auditor`. Browser/PWA/mobile oltre Tauri, Python e licenze non hanno un reviewer: restano lacune dichiarate.

La Phase 1 di `team-review` comprende l'oggetto nel perimetro già risolto, sceglie i reviewer adatti leggendo i loro mandati. `composition.py bind` riceve la scelta e senza di essa si ferma; i reviewer scelti partono insieme nella Phase 2, ciascuno sull'intero perimetro, diviso in gruppi di file sotto un budget quando la base è `content`; `composition.py account` conta i file controllati e quelli rimasti aperti, con il motivo. Il rigor (`quick`, `standard`, `deep`) lo decide il modello leggendo la richiesta, `standard` se non dice nulla: stabilisce la verifica, da solo Critical a tutti i finding con il critico. I segnali di rischio lo portano a `deep`. Testo operativo: `skills/review-preparation/references/team-review.md`.

## Non indirizzato

Temi che la review non giudica perché richiedono esecuzione, infrastruttura esterna al repository o processo organizzativo. Dove indicato, un auditor verifica i presupposti nel codice; il tema in sé resta fuori perimetro.

| Tema | Perché fuori perimetro | Presupposti statici |
|---|---|---|
| Latenza, throughput, P99/tail latency | misura runtime | `algorithmic-cost`, `responsiveness`, `sql-efficiency` |
| Comportamento del garbage collector | misura runtime | `resource-lifecycle` |
| Chaos engineering, esecuzione dei test | richiedono di eseguire il sistema; "testing" è lacuna dichiarata in § Stato | — |
| Cold start reali, limiti serverless | vincoli di piattaforma | `chicken-egg-detector`, `responsiveness` |
| WAF, protezione DDoS | controlli perimetrali esterni | `capacity-quota` (backpressure applicativo) |
| Autoscaling, scaling orizzontale/verticale, multi-region | policy di piattaforma | `capacity-quota`, `recovery` |
| Load balancer, reverse proxy, API gateway, DNS, CDN | infrastruttura esterna; se la configurazione è nel repository la giudicano `environment-binding` e `asset-delivery` | `environment-binding`, `asset-delivery` |
| Build caching | pipeline di build, fuori dal sorgente applicativo | — |
| SLO, SLI, error budget | definizione di processo | `observability` (i segnali esistono e raggiungono il destinatario) |
| On-call, production incident, postmortem | processo organizzativo; un documento di postmortem è rivedibile (`premise-auditor`, Mode 3) | — |
| Rotazione o revoca di chiavi trapelate | rimedio operativo | `secret-exposure` (rileva l'esposizione) |

[Disegno comune](../../docs/specs/2026-11-03-semantic-review-foundation.md)
