# Review per aspetto: copertura esplicita dell'intero sorgente

Attua «Verificare e rendere visibili le lacune» del [disegno comune](2026-11-03-semantic-review-foundation.md) quando l'oggetto non è una modifica ma tutto il sorgente visto sotto una o più classi di difetto (sicurezza, Tauri, testing, …). Prior art: `cloudflare/security-audit-skill`, fasi ricognizione → ledger per unità → hunter → critici di copertura; qui si riusa ciò che senior-review ha già.

## Comportamento attuale

La base `content` (`full`, `dir` in `review-preparation/references/candidate-grounding.md`) rivede tutto il sorgente, ma il perimetro è una lista piatta di file e ogni reviewer riceve l'intero perimetro. La copertura è dichiarata in prosa (`reviewer-common.md`, «Report examined scope»); il completeness critic (`panel-and-critic-prompts.md`, §3) cerca buchi nei finding, non nel sorgente non letto. Nessuna review ricorda cosa ha coperto una run precedente: una seconda run ricomincia da zero.

## Proposta

La review per aspetto inverte l'indice della review per perimetro: non «quali ruoli servono a questi file» ma «quali file deve esaurire questo ruolo». Stessa macchina, cinque regole.

1. **Unità = modulo della mappa.** Le unità sono i moduli di `codebase_map_modules`, ognuno con il digest dei suoi file nello snapshot. Non si inventa una seconda partizione.
2. **Cella = unità × ruolo.** Il ledger `.team-review/coverage-ledger.json` ha una riga per cella: `unit`, `role`, `digest`, `status` (`covered`, `partial`, `unread`, `not-applicable`), `read` (`file:from-to` letti), `gaps`. Un ruolo che consegna senza aggiornare le sue celle ha consegna incompleta (`status: failed` del risultato).
3. **Applicabilità per unità.** `review_roster.py` applica `SIGNAL_PATTERNS`, `SIGNAL_PATHS` e `LANGUAGE_BY_SUFFIX` al contenuto di ogni modulo, non al diff: una cella è `not-applicable` solo con la ragione in codice (nessun file Tauri nel modulo); segnale assente ma non escluso resta `unknown` e la cella è da coprire. Senza questo filtro il prodotto unità × ruoli esplode.
4. **Job per gruppo di unità.** `composition.py bind` crea un job per (ruolo, gruppo di unità) sotto un budget di letture dichiarato nel brief, con `scope_id` = gruppo; la stessa composizione può avere più job. Una cella `unread` a budget esaurito resta `unread`: mai «pulita», mai letta da un altro ruolo al suo posto.
5. **Il critico legge il ledger.** Il completeness critic riceve il ledger e produce «Coverage Gaps» dalle celle `unread` e `partial`, con l'unità e il ruolo. Il rapporto finale (`final-report.toml`, `coverage`) riporta tre numeri per ruolo: celle coperte, parziali, non lette.

**Run successive.** Il ledger è legato al digest dello snapshot. Alla run seguente una cella `covered` con digest invariato si eredita; cambiano solo le celle il cui digest è cambiato o che erano `unread`/`partial`. I finding ereditati restano con la run che li ha prodotti; i finding sulle celle ricoperte si riverificano.

## Criterio

Su un progetto con difetti noti di una classe (seminati o da storia dei fix), la review per aspetto con i soli ruoli di quella classe li trova, il ledger non ha celle `unread` dichiarate `covered`, e la seconda run su un commit che tocca un modulo costa meno di un quinto della prima. Misura in un benchmark dedicato, con il costo per cella e il rapporto fra prima e seconda run nel README.

## Gap

- La review `branch` resta per perimetro: questa spec aggiunge una shape, non la sostituisce. La shape `light` non ha ledger.
- La «unità» funziona solo se la mappa completa è aggiornata: una mappa stantia produce digest falsi; il prerequisito del README del plugin vale anche qui.
- Un ruolo può coprire una cella leggendo poco: `covered` dichiara letture, non comprensione. Il critico confronta le righe lette con la dimensione dell'unità e segnala coperture sproporzionate come `partial`.

## Interventi

1. `review_roster.py`: `--basis content` con `--units` dal run della mappa; applicabilità per unità; emissione del ledger iniziale con ogni cella `unread` o `not-applicable`.
2. `composition.py bind`: job per (ruolo, gruppo di unità) e budget di letture nel brief; `scope_id` = gruppo.
3. `reviewer-common.md`, «Deliver once»: aggiornamento delle celle del ledger come parte della consegna; `reviewer-result.toml`: campo `coverage_cells`.
4. `panel-and-critic-prompts.md` §3 e `review-consolidation/references/team-review.md`: il critico legge il ledger; il rapporto riporta i tre numeri per ruolo.
5. `benchmarks/whole-source-coverage/`: README con parametri (ruoli, budget di letture, dimensione del gruppo), progetto target, difetti noti, costo per cella e costo della seconda run.
