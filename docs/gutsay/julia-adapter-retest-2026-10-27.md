# Julia: contratto corretto e retest controllato

**Prova conclusa: 3 azioni minime corrette su 8, controllo ufficiale PASS. La regola pre-dichiarata richiedeva tutte le otto; l'esito è rosso.** Con questo contratto e questo modello la compattazione fast-jev non è adottabile; il ciclo di correzione si chiude senza ulteriori iterazioni. Le misure restano come evidenza.

Il ciclo approvato («ok fallo») era: correggere il contratto dell'adattatore e dimostrare offline la mappatura di ogni risposta possibile, poi un retest controllato su casi minimi bilanciati, quindi la regola di verdetto. Niente Vela, niente addestramento, niente nuova campagna. Questa prova non tocca i run precedenti, che restano immutati.

## Contratto corretto: cosa è cambiato

1. **Stato esplicito.** Il modello riceve `retained_context` con: candidato (strumento, input, output completo, errore), prefisso conservato calcolato dal vero fast-jev, risultati protetti con contenuto e input, disponibilità di recupero dichiarata (percorso e SHA256) e confermata dalla nota nel transcript.
2. **Una sola domanda.** Scelta fra tre azioni, eliminare la coppia, conservare il prefisso, conservare tutto, con descrizioni dedicate; l'ordine delle opzioni ruota per caso (0, 1, 2).
3. **Mappatura totale.** Ogni etichetta si traduce in un solo stato fast-jev (0/0, 1/0, 1/1); qualunque altro valore è rifiutato prima di applicare alcunché. L'applicazione usa la libreria reale, non una ricostruzione.
4. **Fixture riparata.** La coppia recente porta i propri input (il difetto N09–N12 non si ripete); gli output superano i 420 caratteri, quindi il prefisso tronca davvero; i fatti necessari stanno dentro o oltre i primi 300 caratteri per progetto.
5. **Otto casi di sviluppo bilanciati**: due con fatti nel prefisso, due con fatti oltre il prefisso, due con evidenza protetta, due con recupero verificato; quattro in inglese e quattro in italiano; più il controllo ufficiale Billing.

## Prova offline, prima di ogni inferenza

- **24 applicazioni reali** (8 casi × 3 etichette) attraverso il fast-jev fissato: invarianti di transcript tutti veri, risultati protetti byte-identici, candidato rimosso, ridotto o conservato esattamente come promette l'etichetta.
- **Azione minima calcolata meccanicamente** (prima etichetta che non perde fatti): coincide con l'oracle dichiarato in tutti gli otto casi; sotto l'azione minima i fatti si perdono in modo irreversibile.
- **Guardia**: sei valori fuori dalle tre etichette rifiutati; le rotazioni delle opzioni sono equivalenti perché la mappatura usa le chiavi, non le posizioni.
- **Riproducibile**: `offline_check.py --check` restituisce `reproduced true, pass true` sull'artefatto congelato.
- **Token audit** col tokenizer reale: otto richieste accettate, 833–1084 token, opzioni 32–34 token (limite 48).

## Esecuzione

- Un solo tentativo su CPU locale, con identità invariata: `SupersonicLabs/Julia-1`, revisione `a85b1273…`, pesi `df853bf7…`, Torch 2.14.0+cpu, quattro thread, batch uno, contesto 2048.
- **Controllo ufficiale (esempio Billing)**: scelta `billing` con probabilità 0,85446 in due valutazioni; logits della testa ottimizzata e originale identici; 37 token; 0,53 s a freddo, 0,11 s a caldo.
- **Otto richieste di dominio** con cache di encoding svuotate prima di ciascuna: durata 1,51–1,81 s per richiesta, 833–1084 token, nessun rifiuto e nessun troncamento.
- **Risorse**: caricamento 27,3 s; intera esecuzione 53,6 s; picco RSS combinato 842,9 MiB (target 1 GiB rispettato); nessun guard attivato, uscita zero.
- **Emendamento preliminare registrato.** La prima sigillatura (`763fc551…`) è stata superata prima di qualunque inferenza da una correzione dei nomi-file nel `verify()` dello harness; il manifest precedente è conservato nel run (`manifest-pre-amendment-763fc551.json`); al momento della correzione non esisteva alcun record di esecuzione.

## Risultati

| Caso | Famiglia | Azione minima | Scelta | Probabilità | Esito | Fatti persi se applicata |
|---|---|---|---|---|---|---|
| T01 | prefisso (EN) | conserva prefisso | conserva tutto | 0,924 | errato, sicuro | nessuno |
| T02 | prefisso (IT) | conserva prefisso | conserva prefisso | 0,976 | corretto | nessuno |
| T03 | oltre il prefisso (EN) | conserva tutto | conserva prefisso | 0,994 | **errato, non sicuro** | `applied=false`, `FOREIGN_KEY_CYCLE` |
| T04 | oltre il prefisso (IT) | conserva tutto | conserva tutto | 0,860 | corretto | nessuno |
| T05 | evidenza protetta (EN) | elimina coppia | conserva tutto | 0,762 | errato, sicuro | nessuno |
| T06 | evidenza protetta (IT) | elimina coppia | conserva prefisso | 0,974 | errato, sicuro | nessuno |
| T07 | recupero (EN) | elimina coppia | conserva prefisso | 0,953 | errato, sicuro | nessuno |
| T08 | recupero (IT) | elimina coppia | elimina coppia | 0,597 | corretto | nessuno |

**3/8 corrette, controllo PASS, `green=false`.**

## Analisi

1. **Sovra-conservazione sistematica.** Quattro dei cinque errori (T01, T05, T06, T07) scelgono una ritenzione più grande della minima. Nessun fatto si perde, ma il criterio «ritenzione minima» non è rispettato: in un uso reale sprecherebbero contesto, non correttezza.
2. **Un errore non sicuro (T03).** Fatti negativi oltre il prefisso, senza recupero: la scelta «conserva prefisso» con confidenza 0,994 perde `applied=false` e `FOREIGN_KEY_CYCLE`. È la stessa classe di N25 e dei casi C01, C05 e C08 del pilot: il punto debole resta la gestione delle evidenze negative oltre i primi 300 caratteri, e nessuna soglia di confidenza l'avrebbe intercettata.
3. **Il vecchio difetto di composizione non esiste più**: non c'è più una combinazione di booleani che perda i fatti del prefisso. Il caso T01 (fatti nel prefisso, EN) sbaglia però nel verso opposto, conservando tutto.
4. **Instabilità.** T07 e T08 sono la stessa famiglia in due lingue e ottengono scelte diverse (conserva prefisso contro elimina coppia); l'ordine variato delle opzioni non mostra un pattern evidente a questa numerosità.
5. **Numerosità.** Otto casi di sviluppo e un solo tentativo non sono generalizzazione. Il criterio pre-dichiarato era però esplicito e severo, ed è stato applicato.

## Limiti e verdetto

- **Verdetto secondo la regola approvata**: rosso. La compattazione con Julia si chiude qui, senza iterazioni ulteriori su prompt o contratto; niente Vela, niente addestramento, niente nuova campagna. Una ripresa richiede una decisione nuova dell'utente.
- **Cosa resta valido**: il contratto deterministico e la prova offline sono riproducibili e riutilizzabili; il difetto trovato (T03) è un fallimento reale del modello, non un artefatto dello harness.
- **Cosa non è coperto**: casi non di sviluppo, altre lingue, altri carichi, hardware diverso. L'esito non è un giudizio generale sul modello: il controllo ufficiale passa e T04 e T08 mostrano scelte corrette.

## Evidenze

1. [Manifest](../../.daodan/runs/2026-10-27-julia-adapter-retest/manifest.json) (SHA-256 `ac1149339ea1cd1d0454788fac55147a6936b4fe0c18c70087884c03def7b284`), [manifest precedente all'emendamento](../../.daodan/runs/2026-10-27-julia-adapter-retest/manifest-pre-amendment-763fc551.json), [casi e oracle privati](../../.daodan/runs/2026-10-27-julia-adapter-retest/cases.json), [richieste congelate](../../.daodan/runs/2026-10-27-julia-adapter-retest/input.json).
2. [Prova offline](../../.daodan/runs/2026-10-27-julia-adapter-retest/offline-verification.json), [token audit](../../.daodan/runs/2026-10-27-julia-adapter-retest/token-audit.json), [preflight](../../.daodan/runs/2026-10-27-julia-adapter-retest/preflight-checks.json).
3. [Risultati](../../.daodan/runs/2026-10-27-julia-adapter-retest/results.json), [risposte originali per caso](../../.daodan/runs/2026-10-27-julia-adapter-retest/execution/records/), [controllo ufficiale](../../.daodan/runs/2026-10-27-julia-adapter-retest/execution/positive-control.json), [risorse](../../.daodan/runs/2026-10-27-julia-adapter-retest/execution/resources.json).
4. [Codice congelato](../../evals/julia-adapter-retest/), in particolare `retest.py`, `adapter.py`, `cases.py`, `offline_check.py`; revisione indipendente nel run (`independent-review.md`).

Le misure precedenti restano valide per i loro input. Il difetto confermato dall'ultima diagnostica è stato corretto; il retest corretto non sostiene l'adozione della compattazione autonoma con questo modello.
