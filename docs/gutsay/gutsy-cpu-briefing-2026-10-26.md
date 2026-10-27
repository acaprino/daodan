# Gutsy su CPU: usarlo bene prima di addestrarlo

**Proposta: provare Gutsy v0.4 Q4_K_M congelato come piccolo servizio decisionale locale, iniziando dai segnali del router.** Modal è il laboratorio dei test; il risultato deve funzionare su CPU locale senza un servizio cloud nel percorso ordinario.

Data: 26 ottobre 2026. Stato: briefing di ricerca e ideazione, non specifica approvata. Nessuna integrazione, installazione, nuova inferenza o attività Modal eseguita in questa ricerca. I risultati storici citati esistevano già nel repository. Lettura principale: circa 12 minuti.

## 1. La scelta iniziale

Condividere **un modello caricato e tre contratti di domanda**, mantenendo regole e responsabilità nei rispettivi proprietari:

| Uso | Giudizio chiesto a Gutsy | Decisione applicata dal software |
|---|---|---|
| Model routing | Quali caratteristiche semantiche ha questo lavoro? | Il router esistente sceglie modello ed effort da inventario, catalogo e regole |
| Tool selection | Quali strumenti disponibili servono al prossimo passo? | L'host include gli schemi esatti consentiti e conserva un percorso di recupero |
| Compattazione | Questa chiamata e questo risultato servono ancora? | Il compattatore conserva, tronca o rimuove coppie valide, rispettando le protezioni |

Il vantaggio da verificare è il risparmio complessivo di chiamate e contesto. Un classificatore locale che interroga cento candidati o rilegge tutta la storia a ogni turno può consumare troppo tempo anche con pesi piccoli.

Ordine raccomandato: **routing, selezione tool, compattazione**. Il routing ha un contratto già delimitato; la selezione tool richiede un inventario e un punto di intercettazione; la compattazione introduce il costo maggiore di un'omissione irreversibile nella vista corrente.

## 2. Che cosa offre davvero Gutsy

Gutsy deriva da Qwen3.5-0.8B. Il runtime legge i logits di lettere associate alle alternative, usando un formato specifico con thinking disattivato. Non produce il riassunto o la chiamata tool finale. Il servizio riutilizza lo stato fra domande, ma valuta ogni domanda separatamente. [Prompt](https://github.com/kouhxp/gutsy/blob/db5c2ec62fc81703938adbd714915b53a9fb0de1/gutsy-inference/gutsy_inference/prompt.py), [motore](https://github.com/kouhxp/gutsy/blob/db5c2ec62fc81703938adbd714915b53a9fb0de1/gutsy-inference/gutsy_inference/engine.py).

| Fatto verificato nel contratto | Implicazione pratica |
|---|---|
| Q4_K_M: circa 529 MB di file, cioè 505 MiB | Il file dei pesi non misura la RAM totale |
| Contesto: 8.192 token per stato, una domanda e involucro | Non passargli la storia lunga destinata al modello principale |
| Massimo 64 domande per richiesta | È un limite API, non un budget di latenza ragionevole |
| `noul`, `choice`, `score`; 16 alternative per valutazione diretta | Usare domande piccole; liste maggiori richiedono altri passaggi |
| Lingua dichiarata: inglese | Richieste italiane e miste devono entrare esplicitamente nella valutazione |

Fonti: [pesi](https://huggingface.co/kouhxp/gutsy/tree/main), [schema](https://github.com/kouhxp/gutsy/blob/db5c2ec62fc81703938adbd714915b53a9fb0de1/gutsy-inference/gutsy_inference/schema.py), [model card](https://github.com/kouhxp/gutsy/blob/db5c2ec62fc81703938adbd714915b53a9fb0de1/MODEL_CARD.md).

La configurazione di esempio registra Q8 e Q4 e usa Q8 come default. Sull'endpoint Jev-style, un nome ignoto può ricadere sul default. Il profilo proposto deve registrare **solo `gutsy-0.8b-v04-q4`**, passare questa identità e verificare il modello restituito. Cambiare soltanto URL lasciando `jev-latest` non dimostra l'uso di Q4. [Configurazione](https://github.com/kouhxp/gutsy/blob/db5c2ec62fc81703938adbd714915b53a9fb0de1/gutsy-inference/models.example.json), [server](https://github.com/kouhxp/gutsy/blob/db5c2ec62fc81703938adbd714915b53a9fb0de1/gutsy-inference/gutsy_inference/server.py).

## 3. Come formulare input e domande

La proposta è una scheda di stato breve: obiettivo attivo, prossimo passo, fatti verificati, vincoli pertinenti e osservazioni necessarie. Il catalogo dei candidati contiene identità e descrizioni correnti. Il transcript completo rimane presso l'host, con riferimenti recuperabili alle fonti.

1. **Una domanda, una proprietà.** Chiedere se serve evidenza esterna o se un tool è necessario; evitare domande che combinano più decisioni.
2. **Alternative distinguibili.** Dare criteri positivi e confini; includere casi senza risposta sufficiente. Non insegnare al modello prezzi o nomi del catalogo finale.
3. **Fatti prima delle inferenze.** Calcolare dimensioni, disponibilità, permessi e limiti in codice. Interrogare Gutsy soltanto sulla parte semantica non già accertata.
4. **Stato condiviso, domande raggruppate.** Ridurre il lavoro di encoding ripetuto e misurare il riuso effettivo; richieste concorrenti allo stesso modello sono serializzate dal runtime.
5. **Input incompleto esplicito.** Se manca evidenza, conservare o ampliare prudentemente la scelta. Il sistema non deve trasformare un contesto tagliato in una risposta negativa certa.

Esempio concettuale per il router: stato con obiettivo, ruolo, file coinvolti e requisiti; domanda «Which reasoning depth is required by the unresolved work?»; alternative esattamente corrispondenti agli enum esistenti. Le domande restano in inglese, mentre la lingua dell'obiettivo è una variabile da testare. Una traduzione LLM obbligatoria per ogni richiesta rischierebbe di reintrodurre proprio il costo evitato.

Per `choice` e `score`, le probabilità delle alternative sono condizionate a non-reject. Il valore `reject` va letto separatamente; una probabilità alta fra le alternative non basta a rendere accettabile la decisione. `noul` restituisce P(yes), senza un campo di astensione equivalente. Gli intervalli di incertezza sono quindi una politica applicativa da verificare, non una funzionalità da presumere. [Schema e conversione risposte](https://github.com/kouhxp/gutsy/blob/db5c2ec62fc81703938adbd714915b53a9fb0de1/gutsy-inference/gutsy_inference/schema.py).

## 4. Primo uso: sostituire la classificazione LLM nel router

**Oggi l'LLM non sceglie il modello in Daodan.** `task_router.py plan` prepara una classificazione su dieci segnali chiusi; il coordinatore esegue la chiamata. `assign` applica poi regole, minimi di rischio, capability e catalogo. Una risposta mancante o invalida porta al fallback dichiarato, normalmente tier3. [Implementazione](../../plugins/model-routing/skills/model-routing/scripts/task_router.py), [metodo operativo](../../plugins/model-routing/skills/model-routing/references/task-routing.md).

L'innesto proposto è:

```text
richiesta e fatti del lavoro
  → segnali già verificabili dai metadati
  → Gutsy per i segnali semantici ancora mancanti
  → validazione degli enum esistenti
  → assign: modello, effort e proposta di binding
```

La derivazione dai metadati è già discussa in un [draft locale](../superpowers/specs/2026-10-24-derived-routing-signals-draft.md), ma non è implementata né decisa. Qui rimane un'alternativa da confrontare. Come baseline di compatibilità, Gutsy può rispondere ai sette segnali categoriali con `choice` e ai tre booleani con `noul`; questa traduzione richiederebbe dieci valutazioni e potrebbe essere troppo lenta per l'uso frequente.

Tre varianti da misurare sullo stesso corpus:

| Variante | Utilità | Costo o limite |
|---|---|---|
| Classificatore LLM attuale | Baseline della procedura corrente | Chiamata remota o altro modello disponibile sull'host |
| Gutsy per tutti i segnali | Verifica l'innesto senza cambiare le regole di scelta | Dieci domande per nodo |
| Metadati più Gutsy residuo | Candidata preferita per CPU leggera | Serve provare che i segnali derivati siano corretti e completi |

Nel confronto dei classificatori, fissare gli stessi fatti disponibili e distinguere l'effetto del modello da quello della nuova scheda di contesto. Stesso corpus con informazioni diverse non isola la qualità del modello. La variante con segnali derivati confronta invece l'intera procedura.

Non addestrare o interrogare Gutsy per scegliere direttamente nomi come GPT/Claude: prezzi, ranking e disponibilità restano aggiornabili nel catalogo. Conservare anche i controlli e le conferme del binding già previsti dal metodo corrente. Nessuna integrazione automatica nei dispatcher è dimostrata da questo briefing.

## 5. Secondo uso: scegliere gli schemi dei tool

La selezione delle skill di conoscenza non equivale alla selezione dei tool eseguibili. `skill-catalog` svolge la prima; nel percorso esaminato non è emerso un filtro generale già operativo degli schemi per ogni chiamata. [Contratto skill-catalog](../../plugins/skill-catalog/skills/skill-catalog/SKILL.md).

Proposta: **tool realmente disponibili → filtro per host, permessi e prerequisiti → valutazione semantica → schemi esatti nella chiamata LLM**. Il modello principale continua a scegliere se usare il tool e con quali argomenti.

Gutsy valuta «serve questo strumento per il prossimo passo?». La domanda è multi-label: leggere un file e lanciare un test possono essere entrambi necessari. Una `choice` esclusiva su tutti i tool sarebbe una rappresentazione sbagliata.

Per cataloghi grandi, confrontare un primo passaggio per famiglie seguito da poche domande sui candidati. La selezione gerarchica è un'ipotesi di riduzione del costo: se il primo livello esclude una famiglia necessaria, il secondo non la recupera. Misurare quindi il recall dell'intera catena e mantenere disponibili gli strumenti obbligatori del metodo e la discovery prevista dall'host. Se la discovery manca, includere un insieme conservativo più ampio.

Le descrizioni possono essere compatte durante la selezione; gli schemi inviati all'LLM devono rimanere completi e validi. Una selezione non concede permessi e non modifica le autorizzazioni. La frequenza storica d'uso aiuta la cache, ma non prova che un tool raro sia inutile.

Il controllo va ripetuto quando cambiano obiettivo, fase, catalogo o prerequisiti, anziché aggiungere automaticamente una chiamata Gutsy a ogni turno.

## 6. Terzo uso: motore per fast-jev-compaction

L'interfaccia utile è `JevAsker.ask(state, questions)` della libreria, attraverso un adattatore locale. La compattazione usa due domande `noul` per coppia: conservare la chiamata e conservare il risultato. Gutsy offre la forma di risposta necessaria. Il hook Claude pubblicato non espone però `baseUrl` nel suo trasporto: la compatibilità della libreria non rende il plugin già configurabile verso Gutsy. [Tipi](https://github.com/tamaratran/fast-jev-compaction/blob/e3f262a7f4d42bd8dd32ced30d26176f7cb545b0/src/types.ts), [hook](https://github.com/tamaratran/fast-jev-compaction/blob/e3f262a7f4d42bd8dd32ced30d26176f7cb545b0/hooks/fast-jev.ts).

**Il limite decisivo è l'input:** fast-jev sostituisce il contenuto dei risultati con note di esito e lunghezza. Due risultati diversi, con metadati uguali, possono diventare indistinguibili anche quando uno contiene l'unica evidenza necessaria. Il solo miglioramento del modello non risolve questa perdita informativa. [Costruzione dello stato](https://github.com/tamaratran/fast-jev-compaction/blob/e3f262a7f4d42bd8dd32ced30d26176f7cb545b0/src/state.ts).

La variante da ideare conserva accoppiamento e ricostruzione del transcript, ma mostra per ogni candidato una scheda di evidenza: provenienza, rapporto con il compito aperto, ripetibilità, estratti pertinenti e riferimento recuperabile. L'estrazione deve includere il contenuto utile o proteggere conservativamente il risultato quando non sa rappresentarlo. Non spostare il medesimo problema in un estrattore che scarta già il fatto necessario.

Prima dei punteggi, proteggere autorizzazioni, vincoli attivi, operazioni aperte ed evidenze non riproducibili o relative a un preciso candidato. Il registro canonico delle autorizzazioni rimane autorevole. Non rieseguire un'azione con effetti esterni per ricostruire un risultato eliminato.

I budget upstream, 25k token stimati di stato e 30k per richiesta, non sono adatti al limite Gutsy. Il suo vincolo riguarda lo stato più la singola domanda completa; le 64 domande ammesse equivalgono al massimo a 32 coppie con due quesiti ciascuna. Anche quel massimo può essere troppo costoso su CPU. Tokenizzare con il runtime effettivo, non affidarsi alla stima upstream tarata su Jev. [Compattazione e batching](https://github.com/tamaratran/fast-jev-compaction/blob/e3f262a7f4d42bd8dd32ced30d26176f7cb545b0/src/compact.ts), [motore Gutsy](https://github.com/kouhxp/gutsy/blob/db5c2ec62fc81703938adbd714915b53a9fb0de1/gutsy-inference/gutsy_inference/engine.py).

Politica proposta: eliminare soltanto con evidenza sufficiente di dispensabilità; nell'incertezza conservare. La soglia predefinita upstream di keep=0,5 non è già validata per questo rischio. Un errore, un valore fuori intervallo o un budget superato non deve produrre un drop. Se il transcript pieno non entra nel modello principale, occorre un percorso esplicito di recupero o un compattatore alternativo valutato: «conservare tutto» da solo non risolve l'esaurimento del contesto.

## 7. Profilo operativo leggero su CPU

Punto di partenza sperimentale, da confrontare con il runtime ufficiale: **un processo, un Q4 residente, nessun offload GPU, concorrenza uno**, contesto operativo iniziale di 1.536 token e poche domande. Questo profilo riprende un precedente locale, senza attribuirgli equivalenza con il servizio ufficiale.

Il runtime Python richiede NumPy e llama-cpp-python; non richiede PyTorch per l'inferenza. La cache configurata può occupare ulteriori centinaia di MiB. Limitare inizialmente gli snapshot a uno, mantenendo verificabile il riuso dello stato. [Manifest](https://github.com/kouhxp/gutsy/blob/db5c2ec62fc81703938adbd714915b53a9fb0de1/gutsy-inference/pyproject.toml), [registro e cache](https://github.com/kouhxp/gutsy/blob/db5c2ec62fc81703938adbd714915b53a9fb0de1/gutsy-inference/gutsy_inference/registry.py).

Per evitare lavoro inutile: memorizzare decisioni solo su input, modello, calibrazione e catalogo identici; invalidarle quando cambiano. Riutilizzare il prefisso realmente comune fra domande. Avviare la compattazione soltanto quando il recupero atteso di contesto giustifica il costo.

La via con meno codice nuovo è valutare prima il runtime ufficiale. Il percorso nativo llama-server già sperimentato può essere un confronto per memoria e tempi, ma richiede dimostrare equivalenza di prompt, tokenizer, readout e calibrazione. Non ricostruire le probabilità soltanto da pochi token top-k.

**Obiettivi proposti per rendere misurabile “molto lightweight”, non prestazioni promesse:**

| Dimensione | Obiettivo iniziale da verificare |
|---|---|
| Dipendenze operative | Nessuna GPU, nessun servizio remoto necessario per la decisione accettata |
| Memoria | Picco dell'intero motore entro 1 GiB; riportare anche memoria privata e cache |
| Routing e selezione tool | p95 entro 1 secondo per decisione completa a caldo, inclusi encoding e assemblaggio |
| Compattazione | Budget distinto fino a 5 secondi per evento, senza avviarla a ogni chiamata |
| Convenienza | Qualità preservata e risparmio netto dopo fallback, recuperi e tempo di classificazione |

I limiti di latenza sono deliberatamente una prova di fattibilità: le misure storiche non dimostrano che siano raggiunti. Se un contratto li supera, ridurre domande o frequenza e verificare nuovamente la qualità; non chiamare leggero il sistema basandosi solo sui 505 MiB dei pesi.

Il risparmio non compensa omissioni critiche. Prima di aprire il test separato, fissare i limiti accettabili per perdita di evidenza, esclusione di tool necessari ed errori che abbassano il routing. Un errore critico osservato richiede analisi e mantiene quel contratto in osservazione. Riportare sempre astensioni e fallback con il loro costo; l'assenza di errori nel campione non garantisce assenza di errori futuri.

## 8. Le prove Daodan già disponibili

Un follow-up CPU su Q4_K_M ha completato 496 chiamate con contesto 1.536 e quattro thread. Il replay con ripristino dello stato ha impiegato **580 secondi contro 1.994,7**, con picco RSS combinato runner/server di circa **969 milioni di byte**. È evidenza utile del costo di encoding ripetuto. [Confronto registrato](../../evals/senior-review/choicer-eval/runs/20261021-gutsy-followup-slot/COMPARISON.md).

Queste prove usavano llama-server `/completion` e lettere A/B/Z, con probabilità non calibrate; non validano `/v1/systemone`. I circa 0,67 secondi medi per domanda escludevano encoding iniziale e restore: il totale ammortizzato era circa 1,17 secondi per domanda. Tre profili precedenti superarono il watchdog di memoria. [Identità e limiti](../../evals/senior-review/choicer-eval/GUTSY_RESULTS.md), [report del follow-up](../../evals/senior-review/choicer-eval/runs/20261020-gutsy-followup-ctx1536/REPORT.md).

Le domande candidate trovarono 7 delle 11 prospettive attese sulle nuove funzioni, contro 5/11 della formulazione precedente, ma sul gruppo di verifica entrambe rimasero a 4/5. Erano prove di selezione revisori su un solo progetto. Inoltre 495/496 lettere rimasero uguali con il ripristino, mentre nessuna distribuzione di probabilità fu identica. Riutilizzare questi dati come diagnostica; servono casi nuovi e calibrazione nel percorso realmente distribuito. [Risultati e correzioni](../../evals/senior-review/choicer-eval/RESULTS.md).

## 9. Come testarlo su Modal

Il [protocollo preliminare con casi e oracle](gutsy-preliminary-tests-2026-10-26.md) dettaglia il primo pilot dei tre domini. Rimane una definizione di prova, non una suite già implementata o eseguita.

Modal viene inteso come [modal.com](https://modal.com). Per questa prima fase servono **test CPU, senza addestramento**. CPU e memoria possono avere richieste e limiti espliciti; una semplice richiesta minima può consentire più risorse del previsto. [Documentazione risorse](https://modal.com/docs/guide/resources).

1. **Congelare identità e input.** Hash di GGUF e calibrazione, versione Gutsy, build llama.cpp, corpus e formato delle domande; distinguere i pesi storici da quelli attualmente pubblicati finché gli hash non coincidono.
2. **Provare il contratto ufficiale.** Verificare identità Q4 restituita, tokenizer, limiti, probabilità, astensione e cache. Separare avvio, caricamento e inferenza a caldo.
3. **Confrontare pochi profili CPU.** Due e quattro core con limite esplicito, thread coerenti; contesti 512, 1.536 e 4.096; una, quattro e dieci domande. Usare un disegno progressivo, fermando i profili che superano il budget. Un tetto diagnostico iniziale di 2 GiB permette di osservare se il target di 1 GiB fallisce.
4. **Valutare i tre compiti separatamente.** Per routing misurare errori che abbassano il tier e costo finale; per tool selection omissioni bloccanti, recuperi e token degli schemi; per compaction perdita di evidenza, successo del lavoro e token realmente risparmiati. Separare sviluppo, calibrazione e test per progetto/sessione; includere italiano.
5. **Confermare sulla CPU locale.** Ripetere il corpus minimo con il profilo scelto e il sistema operativo destinatario. La CPU Linux di Modal non dimostra la stessa latenza su Windows o su una diversa microarchitettura.

Prima osservare le decisioni senza applicarle, poi valutare l'attivazione per ciascun contratto. Un successo nel routing non autorizza automaticamente drop di risultati o esclusione di tool. Registrare anche costi Modal e chiamate della baseline: non esiste ancora una stima attendibile senza corpus e durata misurati.

I casi devono contenere una verità verificabile. Per il routing, concordare con il vecchio classificatore non basta: conta se il lavoro riesce con il modello assegnato. Per i tool, quello storicamente chiamato non è l'unico possibile. Per la compattazione, «mai citato dopo» non significa «eliminabile»: confrontare continuazioni con e senza l'evidenza, includendo errori e riesecuzioni.

## 10. Confini di integrazione e opzione successiva

`model-routing` conserva scelta e prezzi; il runtime del modello fornisce probabilità; il controller/host applica binding, strumenti e gestione della storia. Le capacità di intercettare richieste, cambiare gli schemi dei tool o riscrivere il transcript devono essere provate per ogni host. Una skill, una libreria npm o un endpoint locale non forniscono da soli questi poteri. [Contratto operativo degli host](../hosts.md#operational-compatibility-review).

Il codice fast-jev osservato è al commit `e3f262a7f4d42bd8dd32ced30d26176f7cb545b0`, libreria 0.2.0 e plugin 0.3.0, licenza MIT. Gutsy è stato osservato al commit `db5c2ec62fc81703938adbd714915b53a9fb0de1`, runtime 0.4.0, con codice e pesi dichiarati Apache-2.0. Sono candidati sperimentali: questa ricerca non è un audit delle vulnerabilità né una prova installata sui cinque host. [Manifest fast-jev](https://github.com/tamaratran/fast-jev-compaction/blob/e3f262a7f4d42bd8dd32ced30d26176f7cb545b0/package.json), [manifest plugin](https://github.com/tamaratran/fast-jev-compaction/blob/e3f262a7f4d42bd8dd32ced30d26176f7cb545b0/.claude-plugin/plugin.json), [licenza Gutsy](https://github.com/kouhxp/gutsy/blob/db5c2ec62fc81703938adbd714915b53a9fb0de1/LICENSE).

L'addestramento torna rilevante soltanto se input, domande, cache e politica di incertezza sono stati verificati e rimane un errore sistematico documentato. Prima si può calibrare separatamente il Q4 finale, senza modificare i pesi, su dati tenuti distinti dal test. Le temperature generiche pubblicate non sono una validazione per Daodan. [Calibrazione Q4](https://huggingface.co/kouhxp/gutsy/blob/main/gutsy-0.8b-v04-q4_k_m.calibration.json).

Nei percorsi ufficiali ispezionati non sono stati individuati checkpoint allenabili e trainer disponibili: sono pubblici GGUF, calibrazioni e runtime. Se in futuro servirà una specializzazione, occorrerà prima ottenere quel materiale o dichiarare una nuova derivazione dalla base. Il GGUF Q4_K_M rimane l'artefatto di distribuzione. Questa dipendenza futura non blocca la prima valutazione a pesi congelati. [Materiali pubblicati](https://huggingface.co/kouhxp/gutsy/tree/main), [ricetta dichiarata](https://github.com/kouhxp/gutsy/blob/db5c2ec62fc81703938adbd714915b53a9fb0de1/MODEL_CARD.md).

**Primo esperimento proposto: confrontare su Modal CPU il classificatore attuale, Gutsy sui dieci segnali e metadati più Gutsy residuo, usando la stessa selezione deterministica finale.** Prima della prova vanno fissati corpus, budget e integrazione host; nessuno di questi esperimenti è stato avviato con questo briefing.
