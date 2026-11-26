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

## Dopo la risoluzione

- Un agente ha scritto nel piano, sotto le voci interessate, i fatti accertati e le «Scelte aperte» di ogni rilievo ESCALATE (solo aggiunte, punti `[deciso]` invariati).
- M2 va letto con una correzione: Syft **è** già misurato in `benchmarks/project-model/REPORT.md`; resta aperto che cosa il confronto del piano debba decidere.
- La fase 1 non è stata rieseguita: l'utente ha chiesto di passare alla fase 2.

## Correzioni di fatto fuori dalle categorie

- T1.6: `benchmarks/stack-build-tools/` indicata come da creare (parte di M2, che resta aperto).
- T0.3: «37 marchi senza cornice» sostituito dalla causa (rilievo del coordinatore, non dei revisori).

---

# Fase 3: critica, giro 1

**Target:** `docs/specs/architettura.md` (intero). Rilievi in [`critic_report.md`](critic_report.md); questa sessione non ha scritto il documento, salvo la sezione «Nodi del grafo».
**Conteggio (54):** 18 ESCALATE, 20 PROPOSE FIX, 16 DECLINE, 0 CONTEST. Nessuna modifica applicata. Il giro non è pulito.

## ESCALATE: decisioni del proprietario

| Gruppo | Id | Che cosa va deciso |
| --- | --- | --- |
| G1 | S2, S3, D1 | Quale problema risolve il refactoring; obiettivi e non obiettivi |
| G2 | S1, D2 | Quali alternative sono state scartate e perché |
| G3 | D3, T2 | Django, FastAPI, Flask contro i tre verdetti «no» (domanda A, B, C) |
| G4 | D4, S4 | Modello di minaccia, rischi, indurimento del container |
| G6 | D6 | Che cosa succede quando uno step fallisce; chi prepara l'ambiente |
| G10 | D8, T8 | Tetti di tempo, memoria, disco; soglia del consenso |
| G11 | D9 | Stati, ripresa e scrittore del piano unico |
| G12 | D10 | Se i backend scartati restano nel contratto |
| G13 | D11 | Regole sulle credenziali e sulle azioni distruttive |
| G14 | D12 | Punto di uscita unico e registri privati |
| G15 | D14 | Ripiego e manutenzione di fork, Noir, Kiri |
| G16 | D15 | Regola per i legami HTTP ambigui |

## PROPOSE FIX

| Gruppo | Id | Dove | Modifica proposta |
| --- | --- | --- | --- |
| G4b | T6 | «Servizi comuni» | Aggiungere ciò che è nel codice (`--network none`, proxy ai soli registri, `no-new-privileges`; non passati `--cap-drop` e `--user`; la prova su container vero è T3.1). Per Secretlint: oggi `secret_mask` è importato da `app.py`, `mcp_server.py`, `pipeline_tree.py` |
| G5 | S5, S6, D7, T1, T3, T5 | intestazione, «Superfici», anagrafiche | «contratto stabile di riferimento» diventa «contratto di arrivo»; legenda dalla spec rimossa (`[deciso]` approvata dal proprietario, `[proposta]` mai approvata, `[misura]` da misurare, `[difetto]` errore noto); accanto a `surface`, `ui_execution_deferred`, `approval_required`: «non nel codice; nessun traguardo del piano lo porta» |
| G7 | D5 | «Convivenza tra sorgente dedicata e Noir» | Sostituire l'ultima frase con: «A introspezione fallita Noir fa da ripiego, con il motivo dichiarato. Senza container non girano né la sorgente dedicata né Noir: restano le query tree-sitter e una lacuna. Un'introspezione riuscita con 0 ingressi non è un errore.» |
| G8 | S8, T7, D17 | tabella dei nodi | «Voce con `category: service`», «con `category: framework` o `library`», «con `category: tool`»; colonna «Tipo di nodo (`type`)» |
| G9 | D13 | «Tipi di nodo» | Aggiungere: «La mappa di sistema aggiunge `entità`, `applicazione`, `lavoro a orario` (`daodan/core/system_map.py`)»; e che i tipi `by: model` non sono verificati a campione |
| G17 | T4, D16 | «Le anagrafiche» | «ha un controllo» diventa «deve avere un controllo» |
| G18 | S7 | titoli | «Nodi del grafo», «Il piano», «L'interfaccia segue la pipeline», «Le anagrafiche», «Servizi comuni» diventano H2 |
| G19 | T9, T10, S14, D18 | in coda e nel testo | Glossario breve (Kiri, Noir, fork `stack-analyser`, pre-mappa, SCIP, tessera, store, modulo e unità); un solo termine: «ripiego», «adattatore», «modello di evidenza» |
| G20 | T11 | «Superfici», «Come si sa che cosa lanciare» | Togliere il rimando al backlog dalla regola della lacuna e la riga «Modello piccolo locale», che è già nel backlog |

## DECLINE: minori registrati

S9, S10, S11, S12, S13, D19, D20, D21, T12, T13, T14, T15, T16, T17, T18, T19.

**Scelta dell'utente:** «Andiamo avanti con la review», intesa come passare alla fase 4; poi, prima del rapporto della fase 4, «applica».

**Status: resolved** per le 20 PROPOSE FIX, applicate al solo `architettura.md`. Le 18 ESCALATE restano aperte. Il ciclo di critica si è fermato dopo il giro 1, senza convergenza.

Differenze dalle proposte scritte sopra:
- G4b: `pipeline_tree.py` legge solo la versione di `secret_mask`; scritti i soli chiamanti `app.py` e `mcp_server.py`.
- G18: «Nodi del grafo» è stata spostata dopo «Come si sa che cosa lanciare», perché da H2 non assorbisse le due sezioni seguenti.
- G19: i termini sono cambiati anche dentro il punto `[deciso]` sul modello di evidenza (solo i nomi); «modulo» e «unità» restano senza definizione, perché non ne ho trovata una citabile.
- La fase 4 già avviata è stata fermata prima del rapporto, perché leggeva il testo di prima: superata, non «zero rilievi».

# Fase 4: seconda visione d'insieme

Rapporto in [`intermediate_zoom_out_report.md`](intermediate_zoom_out_report.md). L'utente ha risposto «Ok» alle tre scelte offerte, inteso come: correggere la riga sugli strumenti (Z5, errore del coordinatore, corretta) e passare alla fase 5. Gli altri rilievi Z1-Z11 restano aperti.

# Fase 5: prontezza del piano, giro 1

**Target:** `docs/plans/refactoring.md`. Rilievi in [`implementation_readiness_report.md`](implementation_readiness_report.md). Il piano contiene lavoro non in un commit scritto fuori da questa sessione.
**Conteggio (50):** 17 ESCALATE, 19 PROPOSE FIX, 14 DECLINE, 0 CONTEST. Nessuna modifica applicata. Il giro non è pulito.

## ESCALATE: decisioni del proprietario

| Id | Che cosa va deciso |
| --- | --- |
| R-B1 | Per ogni difetto di T0.3: sintomo, correzione o quarantena, come proteggere le tessere |
| R-B3 | Campione di riferimento, domande, oracolo, protocollo cieco |
| R-M1, R-M2 | Se la sonda di rete è in T0, e che cosa prova |
| R-M3, R-M5, P-B2 | Che cosa vuol dire «run coerenti» e con quali soglie si chiudono i cancelli |
| R-M4 | Come la regola dello SHA convive con albero sporco e commit del bot di `modal.yml` |
| R-M6, R-M7, R-M8 | Forma del dossier, come si raccolgono le decisioni, che cosa aggiorna T0.C.1 |
| R-M9, P-M5 | Confini delle tranche di T1 e dove sta il punto 9; una sola descrizione per tranche |
| P-B1 | `[deciso]` su punti riaperti dalle «Scelte aperte» |
| C-M6 | La regola `.ts` è un difetto o una scelta da accettare |
| C-M8, P-M4 | Un solo percorso e un solo esito per ogni step |

## PROPOSE FIX

| Id | Modifica proposta |
| --- | --- |
| C-B1 | In `architettura.md` e nel piano: scrivere che oltre ai registri il proxy apre gli host fissi per strumento e quelli che il progetto dichiara (indicizzatori, esecuzione osservata, dipendenze Python da Git, secondo tentativo di Gradle). Decisione del proprietario, non di questa correzione: «come una CI» o «solo registri» |
| R-B2, C-M2 | Nominare il flake misurato (`test_codebase_map_playwright_controls.py`); l'instabilità di `test_codebase_map_app.py` non ha test né causa |
| C-M1 | T2.3: `JavaEngine` e `KotlinEngine` non esistono; resta `KotlinResolver.kt` |
| C-M3 | Dire che `modal.yml` con `corpus` o `baseline` fa commit e push, e che nessun workflow esegue `pytest` |
| C-M4 | T0.A.2: aggiungere gli altri punti che usano la rete e le sonde già presenti (`container.leaves`, `container.reached`) |
| C-M5 | Il parser dei lockfile, la tabella dei comandi e le neutralizzazioni non esistono: da creare in T3 |
| C-M7 | T1.1 e T1.4: `header.py` esiste e va collegato; perimetro reale di go-enry |
| P-M1, P-M2, P-M3, P-M6 | Titolo «accertate», legenda di `[misura]`, `[difetto]`, `[spike]`, un solo termine per concetto, un fatto per voce |
| R-N1, R-N2, R-N4, C-N1, C-N2, C-N3, C-N7 | 27 file di test, percorsi dalla radice, `read` di `flask_app.py`, nome del test di `support_table` |

## DECLINE: minori registrati

R-N3, R-N5, C-N4, C-N5, C-N6, P-N1, P-N2, P-N3, P-N4, P-N5, P-N6, P-N7, P-N8, P-N9.
