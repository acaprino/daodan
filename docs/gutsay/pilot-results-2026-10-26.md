# Gutsy Q4 su Modal CPU: primo pilot

**Il pilot è stato eseguito; la configurazione provata non è pronta per attivare automaticamente routing, filtro tool o compattazione.** Il routing riconosce i rischi espliciti del campione, ma restano errori sui segnali. La selezione tool omette capacità necessarie. La compattazione perde evidenza critica anche mostrando il risultato completo al classificatore.

Esecuzione: 26 ottobre 2026. [Run Modal](https://modal.com/apps/alfio-caprino/main/ap-RB7GIPeVDZMs8m98eosJoA), app `ap-RB7GIPeVDZMs8m98eosJoA`, chiamata `fc-01M5WQGXXJRNGFJ55ZFYBRX736`. Il client riporta app completata e il server è stato arrestato esplicitamente.

## Risultati principali

| Dominio | Risultato osservato | Conseguenza |
|---|---|---|
| Routing | **36/45 segnali essenziali corretti**, 9/15 casi con tutti i segnali etichettati corretti; nessun mancato riconoscimento dei floor espliciti del campione | Buon segnale sui rischi dichiarati, insufficiente per equivalenza al classificatore corrente |
| Tool selection | **5/14 casi semantici** con capacità sufficienti; nove omissioni. T15/T16 sono contratti di discovery/inventario e rimangono separati | Il filtro con soglia diagnostica 0,5 può impedire il lavoro |
| Compattazione A: stato upstream | Evidenza conservata in 5/8 casi; perdita critica in **C01, C05, C08** | Eliminazione/troncatura automatica non attivabile |
| Compattazione B: risultato visibile | Stesse tre perdite critiche; evidenza conservata in 5/8 casi | Aggiungere il contenuto, mantenendo le domande upstream, non risolve il problema nel campione |

Sono **47 richieste e 314 valutazioni del modello**, tutte restituite e validamente valutate. Copertura completa non significa successo semantico. I casi sono piccoli, sintetici e parzialmente etichettati; non sono 47 lavori reali risolti.

Nel routing, i 45 oracle riguardano soltanto i campi essenziali dichiarati prima della prova. Non è un'accuratezza sull'intero vettore dei dieci segnali. Non è stato eseguito un confronto a pagamento con l'LLM corrente, né misurato il successo del lavoro svolto dal modello finale. È stato usato il router canonico per il tier e per i controlli deterministici di floor/capability.

## Errori che cambiano la decisione d'uso

1. **Routing:** R01/R13 riconoscono la modifica del codice ma negano la necessità dei tool. R04 scambia l'intento coding per agent_tool_use, lo scope few_files per module e non riconosce evidence_required. Alcuni casi semplici ricevono tier3 per segnali non supportati dall'evidenza; il vantaggio economico non è dimostrato.
2. **Tool selection:** T02 esclude sia la modifica sia il test necessari; T05/T06 escludono la lettura della fonte web. Le omissioni coinvolgono T01, T02, T05, T06, T07, T09, T11, T13 e T14. Nessun fallback scatta, perché le risposte sono formalmente valide: la validità non rileva una scelta sbagliata.
3. **Compattazione:** C01 perde la causa esatta dell'errore; C05 perde posizione e diagnostica del candidato; C08 perde la ricevuta di un invio non ripetibile. Il guardrail esplicito conserva la ricevuta C08 in entrambi i bracci, ma non rende corretta la decisione grezza del modello.

C01/C02 hanno lo stesso stato serializzato nel braccio upstream, pur avendo risultati diversi. Il controllo conferma la perdita informativa della rappresentazione. Nel braccio B le domande rimangono quelle upstream, incluso il presupposto che un tool possa essere rieseguito: è in conflitto con gli output irriproducibili dichiarati da C01/C05/C08. Questa prova non dimostra che una futura domanda corretta e una diversa politica conservativa fallirebbero allo stesso modo.

T15 conserva discovery per regola e T16 riconosce un inventario insufficiente tramite il contratto; non sono successi semantici attribuibili a Gutsy. I divieti sono applicati dal filtro meccanico prima della selezione. I controlli della libreria compattatrice preservano pairing e testo; i fatti persi sono una conseguenza delle decisioni di troncatura applicate correttamente.

## Tempi e memoria

Profilo: CPU soltanto, quattro core richiesti e massimi, quattro thread, n_ctx=4096, Q4 unico, una richiesta alla volta, una cache entry e budget cache 128 MiB. Server ufficiale `gutsy-inference` 0.4.0, llama-cpp-python 0.3.36, NumPy 2.3.4. CPU virtualizzata AMD; nome commerciale non esposto.

| Decisione completa | Mediana | p95 descrittivo | Target proposto |
|---|---:|---:|---:|
| Routing, dieci domande | 8,52 s | 9,72 s | 1 s |
| Tool selection, numero variabile di domande | 8,49 s | 10,37 s | 1 s |
| Compattazione A, due domande | 3,85 s | 4,51 s | 5 s |
| Compattazione B, due domande | 4,92 s | 5,59 s | 5 s |

Il picco campionato di RSS combinato worker/server è **1.366.757.376 byte**, circa **1,27 GiB**. Supera il target di 1 GiB secondo questa metrica e rimane sotto il limite diagnostico di 2 GiB. Il valore somma RSS di processi e può contare pagine condivise più volte; non è la RAM privata di una futura applicazione locale. I contatori cgroup non erano disponibili: lo zero del campo campionato non significa consumo nullo.

Durata della Function: **352,52 s**, circa 5 minuti e 53 secondi. Somma dei tempi delle richieste: 338,65 s. Download pesi: 7,67 s; avvio e self-check: 5,65 s; preparazione dell'immagine separata. Il controllo cache riporta `caching OK`, differenza massima 0,017, e tutte le richieste attestano la strada cached per lo stato. Questo non annulla il costo delle singole domande. Con pochi casi, i percentili restano descrittivi.

Alle tariffe base pubblicate, il costo teorico dei 352,52 secondi usando quattro core e fino a 2 GiB è circa **0,02 USD**, esclusa preparazione. È una stima delle risorse, non un importo letto dalla fatturazione. [Tariffe Modal](https://modal.com/pricing).

## Evidenza e riproducibilità

Il file Q4 di 529.296.832 byte corrisponde allo SHA256 `ddf9c23b8a07c008172f1731f4dd93c464b651b9a70409f0feaf8c2d4e089152`, HF revision `f9995fe26a337f1a4ea3f1a5ed38c9799e5a8f63`. Il runtime Gutsy proviene dal commit `db5c2ec62fc81703938adbd714915b53a9fb0de1`. Il compattatore effettivamente applicato proviene dal commit `e3f262a7f4d42bd8dd32ced30d26176f7cb545b0` di fast-jev.

Il digest dell'input nell'invocazione remota coincide con quello congelato: `3646b7a515b8ac111026833e9d0da8f2e23919dbcf1c932836b35f7a8415f9fb`. Gli oracle sono rimasti locali. Raw response, hash delle librerie native, calibrazione, tempi e memoria sono conservati nella cartella del run:

- [Input e manifest](../../.daodan/runs/2026-10-26-gutsy-modal-pilot/artifacts/manifest.json).
- [Risposte originali Modal](../../.daodan/runs/2026-10-26-gutsy-modal-pilot/artifacts/modal-results.json).
- [Scoring per caso e ricostruzioni](../../.daodan/runs/2026-10-26-gutsy-modal-pilot/artifacts/scores.json).
- [Contratti deterministici](../../.daodan/runs/2026-10-26-gutsy-modal-pilot/artifacts/deterministic-checks.json).

I **32 controlli locali** del pilot passano, inclusi quelli sull'upstream reale. Durante la prova sono stati aggiunti controlli di provenienza e metriche per dominio ai soli file di post-processing `pilot.py` e `test_pilot.py`: differiscono dalla prima fotografia del preparatore, senza modificare input, domande, oracle o codice remoto. La [verifica indipendente](../../.daodan/runs/2026-10-26-gutsy-modal-pilot/review.md) documenta questa distinzione.

Due avvii preparatori si sono fermati prima dell'inferenza: codifica del terminale Windows e modifica concorrente del file durante la build. Il run riportato è quello successivo su sorgente fissato; domande e oracle non sono stati ritoccati dopo aver visto le risposte. Un [controllo successivo dello stato Modal](../../.daodan/runs/2026-10-26-gutsy-modal-pilot/modal-app-states.json) riporta entrambe le app temporanee `stopped`, con zero task attivi.

## Revisione degli scorer dopo il pilot

Una rilettura delle fixture (26 ottobre 2026, dopo il run) ha trovato tre modi in cui gli scorer gonfiavano i successi. Il codice in `evals/gutsy-decision-pilot/` è stato corretto; le cifre sopra restano quelle prodotte dagli scorer dell'epoca, e gli artefatti congelati del run non sono stati rigenerati. Una nuova esecuzione produce un `cases.json` con hash diverso e va in una cartella di run nuova.

1. **Compattazione: 3 degli 8 casi non dipendono dalla decisione.** C02 non richiede alcun token; C03 e C04 hanno il fatto richiesto anche nella coppia recente, che è pinned e sopravvive a qualsiasi risposta. Lo scorer ora calcola `evidence_decision_bearing` (il fatto vive solo nel risultato candidato) e il riepilogo conta `evidence_preserved_decision_bearing` a parte. Riletto così, il pilot ha conservato l'evidenza in **2 casi su 5 decision-bearing** (C06, C07) per entrambi i bracci, non 5 su 8. C07 resta decision-bearing per la conservazione grezza, ma il suo recupero è garantito dal locator pinned: `evidence_preserved_after_recovery` non misura il modello.
2. **Tool selection: le selezioni superflue non erano misurate.** Il protocollo le elenca fra le misure; lo scorer riportava solo i byte degli schemi, e T04 (nessun tool necessario) risultava sufficiente anche selezionando tutti i tredici. Ora ogni caso riporta `superfluous_canonical`, `selected_count`, `exact_sufficient` e `schema_bytes_minimal` (il set sufficiente più economico, scegliendo l'alternativa OR meno costosa); il riepilogo aggiunge i casi con selezioni superflue e quelli con selezione vuota. Nel pilot il modello ha restituito una selezione vuota in 9 casi su 14: T04 è stato "sufficiente" per lo stesso comportamento che ha fallito gli altri.
3. **Routing: quattro segnali su dieci senza oracle, tier attribuito a errori non etichettati.** `domain_knowledge`, `output_volume` e `long_context` non avevano etichette in nessun caso, `scope` in tre soli; il tier grezzo usa però l'intero vettore, quindi "casi semplici a tier3" non era attribuibile a un errore misurato. Le fixture ora etichettano 90 campi essenziali invece di 45, con insiemi accettabili dove più valori sono difendibili (per esempio R04 ammette `coding` e `agent_tool_use`, perché le descrizioni del router li sovrappongono per un fix eseguito con strumenti). Lo scorer ricalcola il tier correggendo ogni errore etichettato al valore accettabile più mite e riporta `tier_changed_by_labeled_errors`: un tier che non si muove non è causato da un errore misurato. L'istruzione "usa il valore più severo" resta solo sulle scale ordinate; `work_type` chiede il deliverable principale.

Le 36/45 del pilot non sono confrontabili con le 90 etichette nuove senza una nuova esecuzione.

## Prossimo esperimento motivato dai risultati

Il candidato più utile è **metadati deterministici più poche domande semantiche**, anziché dieci domande per ogni routing o una per ogni tool. Per la compattazione occorre prima una domanda coerente con la ripetibilità e una politica che protegga i risultati irriproducibili. Un successivo esperimento dovrà usare un nuovo gruppo di verifica, mantenendo questi casi come diagnostica; abbassare una soglia sui casi già osservati non costituisce validazione.

Nessuna indicazione di questo pilot richiede ancora un addestramento. Non sono stati misurati token del modello destinatario, risparmio netto rispetto all'LLM corrente, qualità del lavoro finale, compatibilità operativa sui cinque host o prestazioni sulla CPU locale.
