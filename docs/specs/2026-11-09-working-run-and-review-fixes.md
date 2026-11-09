# Fase 1: mappa aggiornata a ogni modifica e quattro correzioni al metodo di review

**Stato:** proposta rifinita, da approvare. **Data:** 9 novembre 2026. Fase 1 di 3: [fase 2](2026-11-09-flow-model.md), [fase 3](2026-11-09-flows-in-review.md).

Contiene solo ciò che usa meccanismi già esistenti e misurati: l'aggiornamento incrementale dello snapshot e quattro regole di testo nel metodo di review. Nessun modello nuovo dei dati.

## A. Run di lavoro aggiornato a ogni modifica

### Comportamento attuale

- Dopo una modifica al codice la mappa resta quella dell'ultimo run: `codebase_map_read` fallisce con «source changed; refresh the manifest» sul file toccato, ricerca e grafo rispondono sullo stato vecchio.
- Aggiornare richiede un run nuovo dall'ingresso della mappa. Un run è evidenza immutabile: gli artefatti di fase legano il digest del proprio manifest (`snapshot.py`, `manifest_sha256`), quindi il manifest di un run con fasi non si può riscrivere.
- Ogni strumento MCP riceve un `run_id` esplicito; `_bound_run` accetta un run senza dichiarazione di consegna (`delivery` assente).
- `snapshot.py write --reuse` riusa la struttura dei file invariati e rifà indice lessicale, moduli e archi del motore. Misura su questo repository (569 file, 3.205 simboli): 15,7 s da zero, 3,4 s senza modifiche, 3,6 s con un file modificato, 4,4 s con il motore. Il manifest pesa 127 MB qui e 20 MB sul run di `react-app` di phazly-app: un run nuovo per ogni modifica non è sostenibile.
- Un hook `PostToolUse` con `async: true` parte dopo `Write` in `claude` 2.1.319 e riceve `tool_name`, `tool_input.file_path`, `cwd` e `CLAUDE_PROJECT_DIR` (prova del 9 novembre). Un hook di plugin vale per ogni sessione e ogni agente (`policies/write-confinement.toml`), e non tutti gli host eseguono gli hook di plugin.

### Proposta

1. **Un solo run mutabile, dichiarato: `working`.** Vive in `.daodan/map/runs/working/` con `state.json` e `snapshot/`, senza dichiarazione di consegna e senza file di fase: non si prepara, non si registra come attivo e non si può pubblicare. `parent_run` è l'ultimo run pubblicato, di cui eredita target e formato. Senza un run pubblicato non nasce: la mappa si crea solo su richiesta.
2. **Un comando, `snapshot.py refresh`.** Scrive il manifest nuovo riusando quello di lavoro (o del genitore alla prima volta), lo sostituisce in modo atomico, poi assicura indice lessicale, grafo dei moduli e archi del motore accanto. Scrive `refresh.json` con ora, file e simboli cambiati e, da `snapshot.py diff` contro il genitore, le affermazioni delle fasi pubblicate che citano simboli cambiati. È l'unico scrittore del run di lavoro; lo specchio pubblicato e gli altri run non si toccano.
3. **Livello che richiede il modello: solo segnato.** Schede, documenti di fase e mappa di interconnessione non si rigenerano. La freschezza delle schede si calcola già a ogni lettura contro i digest correnti; le affermazioni di fase stantie stanno in `refresh.json`.
4. **L'hook è solo il grilletto.** `plugins/codebase-map/hooks/hooks.json`: `PostToolUse`, matcher `Edit|Write|NotebookEdit|Bash`, `async: true`. Lo script esce subito se il progetto non ha un run pubblicato o se il file toccato sta fuori dal perimetro dello snapshot, sotto `.daodan/` o sotto `.team-review/`. Gli host senza hook chiamano `snapshot.py refresh` dall'ingresso della mappa.
5. **Una passata alla volta.** Un lock accanto al run; una richiesta arrivata durante una passata lascia un segno, e la passata in corso ne esegue un'altra alla fine. Oltre il 40% di file cambiati rispetto al genitore il comando non aggiorna e scrive in `refresh.json` che serve un run completo, come la soglia dell'aggiornamento attuale.
6. **Chi legge cosa.** Ricerca, outline, grafo, lettura e impatto usano `working` quando esiste; documenti di fase e pubblicazione restano sul run pubblicato. Una review non si lega mai a `working`: lega un run immutabile, creato dall'ingresso con riuso.

Fuori da questa fase: avvisare l'agente con `asyncRewake`; un `write` che ricalcola l'hash dei soli percorsi indicati, da fare se una passata supera 10 s su un progetto reale.

### Prova, senza modello

Test in `tests/` su un progetto temporaneo con un run pubblicato:

- dopo la modifica di un file e `refresh`, il simbolo nuovo esce da `search` e `outline` su `working`, e `read` non fallisce;
- byte dello specchio pubblicato e del run genitore invariati;
- due `refresh` sovrapposti: una passata più una ripetizione, nessun manifest corrotto;
- oltre la soglia: nessun aggiornamento e avviso in `refresh.json`;
- filtro dell'hook: un file sotto `.team-review/` o fuori perimetro non avvia nulla; nessun run pubblicato, uscita immediata.

Misure da registrare: tempo di una passata su questo repository e sul run completo di phazly-app.

## B. Quattro correzioni al metodo di review

Ogni punto nasce da una run di [`benchmarks/phazly-flow`](../../benchmarks/phazly-flow/README.md).

| # | Dove | Oggi | Evidenza | Regola |
| --- | --- | --- | --- | --- |
| 1 | `review-method/SKILL.md`, in testa | La sequenza (preparazione, job isolati, consolidamento) è descritta, non imposta | Run A: il modello revisiona da solo e lo dichiara alla fine | La prima azione di una review è caricare la preparazione, o `references/light.md` per la forma leggera. Chi non può seguire il metodo lo dice nella prima riga e si ferma: nessun rapporto prodotto fuori dal metodo esce sotto questa skill |
| 2 | `review-preparation/references/team-review.md`, Phase 1 | `01-context.md` è «a short description and relevant source references» | Run B: «nessun tipo planned», vero per il record dello slot e falso per le sue aggiunte, ereditato da 49 job | Un'affermazione sul modello dei dati nomina il tipo e il livello per cui vale e cita `file:line`. Una negazione cita la ricerca che la sostiene su tutti i tipi del perimetro, oppure si scrive come non nota |
| 3 | `review-quality-gates/references/reviewer-common.md`, «Calibrate severity to impact» | Nessun criterio per ciò che l'utente vede | Run A3 e A3b: «piatto non mangiato mostrato Completato, e il bottone per registrarlo sparisce» valutato Low | Un'affermazione falsa mostrata all'utente o un'azione resa indisponibile su un percorso richiesto vale almeno Medium |
| 4 | `review-consolidation/references/team-review.md`, regole 1 e 2 | «same `file:line` + same issue» si fonde; «different issues» resta separato | Run A3: «pasto saltato» e «cibo estraneo» sulla stessa riga fusi in un cluster, il secondo sparito dal titolo | Stesso problema significa stesso meccanismo e stesso trigger. Trigger diversi sulla stessa ancora restano righe separate, co-locate; un trigger consegnato da un job non sparisce dal rapporto |

### Prova

- **Regola 1, con modello, economica.** La richiesta A in cinque sessioni nuove, fermate dopo i primi turni: la prima azione è il caricamento della preparazione in cinque su cinque. La run A2 fermata al prerequisito è costata 0,34 USD.
- **Regola 4, con modello, senza reviewer.** Il consolidamento rieseguito sui dodici risultati di job già salvati della run A3: il trigger «cibo estraneo» di `job-03-F4` compare nel rapporto come riga propria.
- **Regole 2 e 3.** Si misurano nella fase 3, con le run complete.

## Ordine

1. `snapshot.py refresh` e i suoi test.
2. Hook e filtro.
3. Regole 1 e 4 con le loro prove; regole 2 e 3 come testo.
4. Versioni dei due plugin e riga in `tools-guide.md` su `working`.
