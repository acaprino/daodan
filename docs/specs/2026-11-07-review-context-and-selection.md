# Review: contesto, domande e selezione

Attua «Come si compone una review» del [disegno comune](2026-11-03-semantic-review-foundation.md) nella shape `branch` di senior-review. La shape `light` resta `review-method/references/light.md`.

## Comportamento attuale

La Phase 1 di `review-preparation/references/team-review.md` esegue quattro dispatch prima del primo reviewer: 1a nuova analisi Codebase Map sul perimetro (`map-analyst`), 1c derivazione cieca delle premesse (`premise-auditor` Mode 1), 1d join di provenienza, 1b mappa delle interconnessioni (`semantic-interconnect-mapper`). Phase 2 legge `02-interconnect.md` e `01-knowledge-provenance.md`.

Prova del 2026-11-07 (`benchmarks/scope-resolution/results/review-light-943bdc44c/`): la shape `light`, con la mappa completa già prerequisito e i tool MCP, ha trovato il difetto seminato senza nessuna di queste fasi. Costo 217K token, due verifiche incluse.

## Proposta

La Phase 1 diventa tre passi del coordinatore, nel suo contesto, senza dispatch.

1. **Comprendere l'oggetto nel perimetro.** Dal perimetro di Phase 0, con i tool della mappa completa: sorgenti, contratti e test pertinenti allo scopo della review. Ogni riferimento ha percorso, righe e versione. Output `.team-review/01-context.md`.
2. **Scegliere i reviewer pertinenti.** Candidati: i ruoli del catalogo (`plugin.toml` via `composition.py catalog`); le micro skill quando esisteranno. Le descrizioni selezionano i candidati, il coordinatore ne legge i mandati prima di decidere. Linguaggi ed estensioni orientano la scelta, non la determinano. La selezione finalizza il campo `roster` che `composition.py bind` lega.
3. **Preparare l'avvio.** I reviewer scelti partono insieme in Phase 2, ciascuno sull'intero perimetro con il proprio mandato e il contesto del passo 1: il mandato dice cosa verificare, il perimetro dove. Una competenza necessaria ma non disponibile, inclusa la baseline di uno stack toccato, è una lacuna dichiarata. Output `.team-review/02-selection.md` (reviewer scelti e perché), letto da Phase 2 al posto di `02-interconnect.md` e `01-knowledge-provenance.md`.

Cade 1a perché la mappa completa è prerequisito e una nuova analisi parziale la duplica. Cade 1b perché il contesto del passo 1 ne prende il posto. Cadono 1c e 1d perché la verifica delle premesse resta per finding (Lens 0 in `light.md`), dove costa in proporzione ai finding e non a priori. Cade 0c (leads immutabili) perché alimentava solo la derivazione cieca 1c. `review_roster.py compute` resta per tier e verifica; la scelta dei membri passa dal passo 2.

## Criterio

Su una modifica con un difetto verificabile e noto indipendentemente, la review `branch` lo trova con i reviewer scelti al passo 2, meno dei 26 della composizione generica, dichiara le baseline mancanti e costa meno della `light`. Misura in `benchmarks/scope-resolution` sul commit `943bdc44c` (oracolo nel commit successivo `f52f7352c`), confronto con la `light` con tool. È il caso di costruzione: prima di dichiarare il metodo valido servono casi non usati nella costruzione.

## Gap

- Micro skill e baseline per stack non esistono: la selezione lavora sui ruoli del catalogo, più larghi di un controllo, e ogni review `branch` dichiara la lacuna di baseline.
- `edit_impact` e `graph` falliscono nell'ambiente attuale (`ModuleNotFoundError: edge_view`, `store_graph`) pur importando dalla cartella degli script: guasto del server MCP, fuori perimetro.
- `brief` e `record` di review-preparation non concordano con `bind` (`input_mode`, `job_id`): fuori perimetro.

## Interventi

1. `review-preparation/references/team-review.md`: la sezione Phase 1 diventa i tre passi; via la Phase 0c. `references/composition.md`: la selezione finalizza il `roster` prima di `bind`. `roles/premise-auditor.md`: il Mode 1 non legge più `01a-review-knowledge-leads.md`.
2. `review-method/references/team-review.md`: Phase 2 legge `02-selection.md`; il prompt del reviewer elenca i nuovi file di contesto; via il riferimento a 1c.
3. `review-method/SKILL.md`, `review-preparation/SKILL.md`, `README.md` del plugin: via le istruzioni su Phase 1a; la riga sul selettore descrive il passo 3.
4. `roles/premise-auditor.md`: Mode 1 resta disponibile su richiesta esplicita, fuori dal flusso.
5. `benchmarks/scope-resolution/README.md`: parametro «Phase 1» con valori attuale e ridisegnata e la misura.
