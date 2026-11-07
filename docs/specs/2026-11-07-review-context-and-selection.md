# Review: contesto, domande e selezione

Attua «Come si compone una review» del [disegno comune](2026-11-03-semantic-review-foundation.md) nella shape `branch` di senior-review. La shape `light` resta `review-method/references/light.md`.

## Comportamento attuale

La Phase 1 di `review-preparation/references/team-review.md` esegue quattro dispatch prima del primo reviewer: 1a nuova analisi Codebase Map sul perimetro (`map-analyst`), 1c derivazione cieca delle premesse (`premise-auditor` Mode 1), 1d join di provenienza, 1b mappa delle interconnessioni (`semantic-interconnect-mapper`). Phase 2 legge `02-interconnect.md` e `01-knowledge-provenance.md`.

Prova del 2026-11-07 (`benchmarks/scope-resolution/results/review-light-943bdc44c/`): la shape `light`, con la mappa completa già prerequisito e i tool MCP, ha trovato il difetto seminato senza nessuna di queste fasi. Costo 217K token, due verifiche incluse.

## Proposta

La Phase 1 diventa tre passi del coordinatore, nel suo contesto, senza dispatch.

1. **Comprendere l'oggetto nel perimetro.** Dal perimetro di Phase 0, con i tool della mappa completa: sorgenti, contratti e test pertinenti allo scopo della review. Ogni riferimento ha percorso, righe e versione. Output `.team-review/01-context.md`.
2. **Scegliere i reviewer pertinenti.** Candidati: i ruoli del catalogo (`plugin.toml` via `composition.py catalog`); le micro skill quando esisteranno. Le descrizioni selezionano i candidati, il coordinatore ne legge i mandati prima di decidere. Linguaggi ed estensioni orientano la scelta, non la determinano. `composition.py bind` riceve la scelta in `BINDINGS.json` (`selection`) e la rende roster; una review `branch` senza selezione dichiarata si ferma. Code review, PR review e tipi documentali dichiarano `automatic`.
3. **Preparare l'avvio.** I reviewer scelti partono insieme in Phase 2, ciascuno sull'intero perimetro con il proprio mandato e il contesto del passo 1: il mandato dice cosa verificare, il perimetro dove. Una competenza necessaria ma non disponibile, inclusa la baseline di uno stack toccato, è una lacuna dichiarata. Output `.team-review/02-selection.md` (reviewer scelti e perché), letto da Phase 2 al posto di `02-interconnect.md` e `01-knowledge-provenance.md`.

Cade 1a perché la mappa completa è prerequisito e una nuova analisi parziale la duplica. Cade 1b perché il contesto del passo 1 ne prende il posto. Cadono 1c e 1d perché la verifica delle premesse resta per finding (Lens 0 in `light.md`), dove costa in proporzione ai finding e non a priori. Cade 0c (leads immutabili) perché alimentava solo la derivazione cieca 1c. `review_roster.py compute` resta per rigor e verifica; il suo roster è uno spunto per il passo 2.

Il rigor è `quick`, `standard` o `deep`. Lo decide il modello leggendo la richiesta intera, senza una tabella di parole; `standard` se la richiesta non dice nulla. Stabilisce la verifica (`verification` del roster): `critical` per `quick`, solo Critical con Lens 1; `critical-high` per `standard` e `light`, Critical e High con Lens 0 e Lens 1; `all-above-floor` per `deep`, ogni finding sopra la soglia con il pannello completo e il critico. Un segnale di rischio (interfaccia pubblica, percorso sensibile, manifest, 20 chiamanti) porta a `deep` anche una richiesta `quick`. File e moduli non alzano più il rigor. Prima il roster dichiarava il livello ma nessun testo lo leggeva: nella misura del `943bdc44c` otto lenti su due finding, e il pacchetto da 9 file di produzione era diventato medio solo per la soglia dei 6 file. Il nome `tier` è sostituito da `rigor` perché `medium` indicava anche una severità.

## Criterio

Su una modifica con un difetto verificabile e noto indipendentemente, la review `branch` lo trova con i reviewer scelti al passo 2, meno dei 26 della composizione generica, dichiara le baseline mancanti e costa meno della `light`. Misura in `benchmarks/scope-resolution` sul commit `943bdc44c` (oracolo nel commit successivo `f52f7352c`), confronto con la `light` con tool. È il caso di costruzione: prima di dichiarare il metodo valido servono casi non usati nella costruzione.

## Gap

- Micro skill e baseline per stack non esistono: la selezione lavora sui ruoli del catalogo, più larghi di un controllo, e ogni review `branch` dichiara la lacuna di baseline.
- `graph` fallisce sul run attuale (`ValueError: path is missing or inaccessible`, l'inventario precede la rinomina di `skills/map-method`) e `edit_impact` riporta `missing_store`: fuori perimetro.
- `brief` e `record` di review-preparation non concordano con `bind` (`input_mode`, `job_id`): fuori perimetro.

## Interventi

1. `review-preparation/references/team-review.md`: la sezione Phase 1 diventa i tre passi; via la Phase 0c. `references/composition.md`: la selezione finalizza il `roster` prima di `bind`. `roles/premise-auditor.md`: il Mode 1 non legge più `01a-review-knowledge-leads.md`. `composition.py`: `selection`. `review_roster.py`: `rigor` al posto di `tier`, `--rigor` passato dal modello, via le soglie su file, moduli e chiamanti medi; `check` accetta la review preparata. `candidate-grounding.md`, `verification-panel.md` e `review-consolidation/references/*`: la regola per rigor.
2. `review-method/references/team-review.md`: Phase 2 legge `02-selection.md`; il prompt del reviewer elenca i nuovi file di contesto; via il riferimento a 1c.
3. `review-method/SKILL.md`, `review-preparation/SKILL.md`, `README.md` del plugin: via le istruzioni su Phase 1a; la riga sul selettore descrive il passo 3.
4. `roles/premise-auditor.md`: Mode 1 resta disponibile su richiesta esplicita, fuori dal flusso.
5. `benchmarks/scope-resolution/README.md`: parametro «Phase 1» con valori attuale e ridisegnata e la misura.
