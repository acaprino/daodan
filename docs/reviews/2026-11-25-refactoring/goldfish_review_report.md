# Goldfish Annotated Review Report

**Target:** `docs/specs/architettura.md` e `docs/plans/refactoring.md` (interi), commit `78e070129`
**Rilievi:** fase 1 di 5. Testo integrale in [`zoom_out_report.md`](zoom_out_report.md); i numeri di riga là sono di quel commit.
**Chi risolve:** una sessione che **non** ha scritto i documenti: le sue obiezioni pesano meno, e le voci `[deciso]` non sono state riscritte.
**Approvazione delle modifiche:** richiesta dell'utente «aggiorna i doc, sì», applicata alle sole correzioni di fatto.

**Conteggio (19):** 10 ESCALATE, 3 PROPOSE FIX (applicate), 6 DECLINE, 0 CONTEST.

## ESCALATE: servono decisioni del proprietario, nessuna modifica

| Id | Severità | Dove | Rilievo | Perché sale a te |
| --- | --- | --- | --- | --- |
| B1 | Blocker | `architettura.md`, strumenti e sorgenti; T1.12-13 | Django, FastAPI e Flask `[deciso]` come sorgenti primarie contro tre benchmark chiusi con «no» (verificati) | Il backlog registra la decisione; la ragione e la misura che la conferma non sono nei documenti |
| M1 | Major | T0.7, T3.1 | La prova di isolamento arriva due traguardi dopo il primo uso con rete | Ordine dei traguardi. Nel codice ci sono già `--network none`, proxy ai soli registri e `no-new-privileges`; non ho trovato `--cap-drop` né `--user` in `container.py` |
| I1 | Major | T0.7, T3.1, cancello T3 | Stesso punto: portare la sonda di rete nel cancello T0 | Come M1 |
| M2 | Major | T1.6-7 | Syft non riconosce strumenti di build | Confronto `[deciso]` |
| M3 | Major | T1.7-9 | Dieci famiglie nel fork senza un difetto che le chieda | Scelta `[deciso]`; gli adattatori esistono in `premap/` (verificato) |
| M4 | Major | «Il piano», T1.16 | Piano unico più grande del consumatore di oggi | Scelta `[deciso]`; `pipeline/plan.py` esiste (verificato) |
| M5 | Major | `link_calls`, T2.1 | «Evidence model» che ricopre `edge_grading` ed `edge_store` | Scelta `[deciso]`; le strutture citate esistono (verificato) |
| M6 | Major | `run_and_observe`, T3.3 | Confronto fra backend runtime senza un difetto misurato | Ambito di T3; Python usa già `sys.monitoring` (verificato) |
| M7 | Major | T1, T2 | Traguardi troppo larghi per un cancello solo | Taglio dei traguardi |
| I2 | Major | T0.6, T3.4 | La diagnosi dello `0/19` arriva per ultima | Ordine dei traguardi |

## PROPOSE FIX: applicate

### B2 [zoom out] Blocker: manca il problema, rimandi a documenti rimossi
- **Applicato:** nel piano, il comando che apre la spec rimossa; in `architettura.md`, una riga per Noir e una per Kiri.
- **Resta aperto, tuo:** quale difetto di oggi il refactoring risolve. La spec rimossa non lo dice nell'intestazione: non l'ho inventato.

### M8 [zoom out] Major: requisiti senza un punto nel piano, riferimenti che non esistono
- **Applicato:** T2.5 (ramo `feat/link-key-shape` assente), T0.5 (`docs/pipeline/` già tracciata), T1.4 (`go-enry` condizionato alla scelta aperta).
- **Resta aperto, tuo:** in quale traguardo entrano `surface`, `ui_execution_deferred` e `approval_required`.

### N4 [zoom out] Nit: lanciatore comune a due o a quattro step
- **Applicato:** la frase sotto la tabella degli step rimanda a «Servizi comuni» (quattro step).

## DECLINE: registrate, non corrette

| Id | Rilievo |
| --- | --- |
| N1 | Dettagli da verbale in T0.4, T1.17, T2.3 |
| N2 | Colonne «Stato» in un contratto a refactoring finito |
| N3 | Altre copie dello stato: `roadmap.md`, piano non tracciato, `pipeline_tree.py` |
| N5 | Spike SQL fuori dal cancello T1; lettori SQL a espressioni regolari (nessun uso di tree-sitter in `sql.py`, verificato) |
| I3 | Manca lo stato «in attesa di consenso» |
| I4 | «Zero regressioni» con un test instabile: serve un elenco dei fallimenti noti |

## Correzioni di fatto fuori dalle categorie

- T1.6: `benchmarks/stack-build-tools/` indicata come da creare (parte di M2, che resta aperto).
- T0.3: «37 marchi senza cornice» sostituito dalla causa (rilievo del coordinatore, non dei revisori).
