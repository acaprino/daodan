# Risoluzione delle chiamate: il passaggio degli indicizzatori e la sua copertura

**Stato:** In uso, come step `analyze` della [pipeline](2026-11-15-pipeline-di-analisi.md) (`resolve` nei nomi nuovi). La fonte di ogni linguaggio è l'indice SCIP di un indicizzatore (`daodan/core/indexers/`), costruito nel container di Daodan; i motori per posizione di prima (Jedi, i language server) non ci sono più. Restano in uso i requisiti qui sotto, con il loro numero. Come gira il passaggio, lo stato e la copertura per linguaggio sono descritti in [`docs/plugins/codebase-map.md`](../plugins/codebase-map.md), «Grafo, risoluzione e moduli», e gli strumenti per linguaggio in [`codebase-map-linguaggi.md`](../plugins/codebase-map-linguaggi.md).

**Questo step non chiude l'analisi.** Ciò che lascia senza risposta è un buco con la sua classe, e passa allo step dinamico, che lo chiude dove un test esegue la chiamata ([passo dinamico](2026-11-12-passo-dinamico.md), sezione 5). Un buco si dichiara e si misura dopo l'ultimo passo, mai su questo solo: su tududi, JavaScript, delle 16.527 chiamate che questo step lascia senza risposta il registro esatto ne risolve 13.677, l'82,8% ([`benchmarks/call-provenance`](../../benchmarks/call-provenance/README.md), «Registro esatto su tududi»).

**Collocazione:** `resolve_edges.py` (comando), `engine_pass.py` (stage, stato, rapporto), `edge_grading.py` e `edge_store.py` (archi e copertura), `edge_view.py` (vista), `source_positions.py` e `scip_engine.py` (posizioni e lettura dell'indice), `languages/semantic.py` (posizione dei nomi), tutti in `daodan/core/`.

## Requisiti in uso

I numeri sono quelli con cui gli altri documenti li citano. I numeri 3, 4, 10, 17–22 e 24 erano dei motori per posizione e non si riusano.

1. **Il passaggio è uno store derivato dello snapshot**, come l'indice lessicale e il grafo dei moduli: lo avviano `snapshot.py write` e `codebase_map_create_run`, lo riavvia `codebase_map_index` quando non è fresco. `--no-engine` e `engine=false` lo saltano; il run registra la scelta e nessuna riparazione la scavalca.
2. **Il passaggio non blocca.** Gira staccato e scrive accanto al manifest `engine-edges.sqlite`, `engine-report.json` e `engine-pass.log`. Lo stato (`running`, `fresh`, `stale`, `failed`, `unavailable`, `stopped`, `off`) compare nello stato del run e nella vista degli archi, complessivo e per linguaggio.
5. **La copertura si legge per linguaggio, sulle righe dello store:** `files`, `sites`, `answered`, `holes` per classe con fino a tre esempi, `uncertain`, `externals` e `state` (`complete` o `lower-bound`). Vale sempre `sites` = `answered` + `holes`: uno stage che scriverebbe uno store senza righe per un sito fallisce, e lo store non si scrive. «Risolte su risolvibili» non è un numero del prodotto: i benchmark lo calcolano con i loro script.
6. **Si verificano i sorgenti che lo stage legge,** con l'hash prima e dopo (`edge_grading.verify_sources`).
7. **Un run fermato ferma il suo passaggio** (`engine_pass.stop_pass`) e registra `stopped`; nessuna riparazione lo riavvia, solo un nuovo snapshot.
8. **Nessuna regola nuova in `resolution.py`.** Ciò che il risolutore lessicale non prova lo prova l'indice.
9. **Il membro di un valore calcolato conserva il suo nome:** `Path(__file__).resolve()` si registra come `(expr).resolve`, in ogni linguaggio (`res.status(500).render()` è `(expr).render`).
11. **Una fonte per ogni linguaggio, uno stage alla volta.** Le voci del passaggio (`ENGINES`) si costruiscono dalle dichiarazioni degli indicizzatori, dal più leggero in memoria al più pesante. Prima di ogni stage si controlla la memoria libera contro il `MIN_FREE` dell'indicizzatore; dopo uno stage finito per esaurimento della memoria non ne partono altri. Lo store tiene una voce per linguaggio con la fonte che l'ha scritta, e uno stage sostituisce solo le sue.
12. **Daodan scarica da sé ciò che serve allo stage,** nella sua cartella condivisa, a versione fissata e con il checksum verificato. Il codice del progetto (build, build script, macro, script di installazione) gira solo nel container: le regole sono nel [passo dinamico](2026-11-12-passo-dinamico.md), sezioni 2–4. Senza container un linguaggio che chiede una build è `unavailable` con la causa, mai `failed`.
13. **Le posizioni si convertono in modo esplicito.** Al confine la colonna è in byte UTF-8, l'unità dello snapshot; SCIP usa la codifica che il documento dichiara. Un byte dentro un carattere non è una posizione.
14. **L'arco arriva dove la fonte nomina la dichiarazione.** La dichiarazione dello snapshot che ha il nome in quella posizione (`name_span`, e `signature_spans` per gli overload) dà identità e tipo dell'arco. Una posizione che nomina due dichiarazioni è ambigua; una risposta fuori dai file del progetto è esterna; una risposta su una variabile o un parametro dice dove il callable è tenuto, non il bersaglio. Un costruttore nomina la sua classe.
15. **Il callee finisce sul suo nome:** lo span va dal ricevitore al nome, mai sugli argomenti.
16. **Un contratto è una dichiarazione.** I membri callable di un'interfaccia o di un tipo, un metodo di interfaccia Go, la firma senza corpo di un trait Rust e una variante di enum sono dichiarazioni marcate `contract`. Un arco su un contratto è vero e non dice quale implementazione gira.
23. **Una chiamata si classifica per la provenienza della funzione chiamata, mai per il nome,** in ogni linguaggio e senza eccezioni per librerie o nomi.

    | Evidenza | Esito |
    | --- | --- |
    | Una sola destinazione interna, identificata senza ambiguità | Risolta |
    | Tutte le destinazioni possibili sono provate esterne | Esterna |
    | Provenienza incompleta, ambigua o decisa a runtime | Non risolta in questo step: buco, che passa allo step dinamico |

    Il riferimento è quello preciso della chiamata, nel suo file e nel suo scope; la funzione si segue attraverso variabili, alias, proprietà, parametri e valori restituiti. Né la posizione della variabile né la libreria che la riempie dicono dove la funzione è implementata. «Nome assente dal progetto, quindi esterna» non vale: una funzione interna si può chiamare con un alias.

## Prove

- Requisito 23: [`benchmarks/call-provenance`](../../benchmarks/call-provenance/README.md).
- Copertura per progetto e per linguaggio, buchi per classe, verifica a mano: [`benchmarks/inference-audit`](../../benchmarks/inference-audit/README.md).
- Test: `tests/test_codebase_map_resolve_edges.py`, `tests/test_codebase_map_mcp.py`, `tests/test_codebase_map_mcp_wire.py`.

## Limiti e aperto

- Ciò che ogni indicizzatore lascia aperto, per linguaggio: [`codebase-map-linguaggi.md`](../plugins/codebase-map-linguaggi.md), «Limiti noti». Sono limiti di questo step: quanto ne resta dopo lo step dinamico è misurato solo per JavaScript su tududi (sopra) e per Python su python-semver (`benchmarks/call-provenance`); per gli altri linguaggi e su express non è misurato dopo il passo dinamico.
- **Aperta: da approfondire:** uno stage non ha un limite di tempo suo ([pipeline](2026-11-15-pipeline-di-analisi.md), 8.9).
- `position_stage.py` resta per un indice SCIP dato a mano (`resolve_edges.py --engine scip`), con la sua cache `engine-answers.sqlite`.

**Per modificare questa spec:** un requisito in più solo per un'esigenza obbligatoria o un esito sbagliato riproducibile.
