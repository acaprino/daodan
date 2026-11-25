# Ricerca dei flussi e pacchetto di una review

> Ciò che di questo documento resta da fare è condensato in [Il lavoro che resta, in ondate](2026-11-25-lavoro-residuo-a-ondate.md), ondata 9: lo stato di una voce si aggiorna là.

**Stato:** Parte della [spec dei flussi e della mappa del sistema](2026-11-18-flussi-e-mappa-del-sistema.md), divisa per aspetto il 20 novembre 2026 su richiesta del proprietario. Parole e Principi sono quelli della spec della mappa. I numeri di sezione, di motivo, di limite e di decisione sono rimasti gli stessi: «3.8», «11.6» e «motivo 12» si citano come prima. Una sezione che qui manca è nelle altre spec: la [mappa](2026-11-18-flussi-e-mappa-del-sistema.md) (1–10), [ingressi e scoperta dei flussi](2026-11-20-ingressi-e-scoperta-dei-flussi.md) (6.5–6.8, 7), la [pipeline di analisi](2026-11-15-pipeline-di-analisi.md) (preparazione e indicizzatori). Qui: l'anagrafica dei flussi e i loro legami, la ricerca che da una richiesta in parole trova il flusso, il modulo logico o il componente, il perimetro di una review e dove serve l'embedder. Se unità e flussi fanno trovare più difetti si misura nella [fase 3](2026-11-09-flows-in-review.md). **Piano:** [ricerca e pacchetto di review](../plans/2026-11-20-ricerca-e-pacchetto-di-review.md).

## Stato al 20 novembre 2026

| Parte | Stato |
| --- | --- |
| Unità di una review (11.3–11.5) | Applicato nel plugin: `flows.py`. Prova: `tests/test_codebase_map_flows.py` |
| Anagrafica e legami fra flussi (3.8) | Proposta; provata a costo zero sui riferimenti (README di `benchmarks/system-map`, «Legami fra flussi») |
| Ricerca per embedding (12.1, 12.2) | In corso: l'embedder c'è (`daodan/core/embedding_worker.py`, EmbeddingGemma 2, solo testo), facoltativo e spento nel plugin, e indicizza i simboli del codice; sulle voci dell'anagrafica è proposta. Misurato solo multilingual-e5-large, su voci scritte dai riferimenti |
| Dall'intento ai controlli e pacchetto dalla ricerca (11.1, 11.2, 11.6, 12.3) | Proposta |
| L'embedder nell'abbinamento dei flussi (12.4) | Proposta dalle parole del proprietario, non misurata |

## 3. Flussi: anagrafica e legami

I punti 3.1–3.7 sono nella [spec della mappa](2026-11-18-flussi-e-mappa-del-sistema.md).

8. **Proposta del 20 novembre, dalle parole del proprietario: l'anagrafica dei flussi e i legami fra flussi** (motivo 13). È la base per trovare, da una richiesta, il flusso o il modulo logico giusto da dare a un revisore, e per dire quali prove fare. L'anagrafica ha una voce per flusso: identità, nome, area, tipi, l'intento in una frase e la scheda del percorso (sezione 9), ingressi, effetti, nodi, file, e le prove del progetto che lo attraversano. I legami fra due flussi li calcola la macchina dalla mappa, senza modello: **avvia**, quando un effetto dell'uno è l'ingresso dell'altro, con il riscontro di 3.3 (spec della mappa); **condivide**, quando passano per gli stessi nodi, esclusi quelli che quasi tutti i flussi toccano; **stesso dato**, quando toccano la stessa entità. Il risultato è un grafo di flussi, dove ogni flusso è un nodo che si apre nel suo sottografo e i nodi in comune restano gli stessi. Provata a costo zero sui riferimenti: README di `benchmarks/system-map`, «Legami fra flussi».

## 11. Perimetro di una review

**Unità applicate nel plugin; dall'intento ai controlli: proposta, da misurare prima di adottarla ([fase 3](2026-11-09-flows-in-review.md)).** Prova delle unità: `tests/test_codebase_map_flows.py` (`test_a_stop_leaves_the_flow_incomplete`, `test_units_keep_writers_with_readers_and_assign_every_file`, `test_a_shared_file_is_a_member_of_few_units_and_context_in_the_others`).

1. Il modello legge l'intento e lo riporta sulla mappa: quali aree, flussi e nodi tocca, e a quali livelli. Lo dichiara in `00-scope.md`; chiede solo se due letture cambiano correttezza o costo. «Review dell'annullamento ordini» prende il flusso con tutte le varianti, anche quelle automatiche; «review dell'annullamento automatico» prende quel ramo e la logica condivisa che ne decide l'esito; un componente nominato porta al nodo e ai flussi che lo attraversano.
2. La mappa restituisce, per ogni ramo: i file e i simboli da revisionare con il motivo; i riferimenti da consultare come contesto; le frecce con i dati che passano; i servizi esterni; i dati tenuti in più posti, da confrontare; le lacune che limitano il giudizio. Un componente condiviso compare una volta, con i rami interessati. Il brief dei revisori elenca queste cose, non solo i file.
3. Senza mappa, l'unità si forma da ciò che la richiesta nomina:

   | La richiesta nomina | Punti di partenza | Come si forma l'unità |
   | --- | --- | --- |
   | Una cartella o un modulo | I suoi file | Per percorso del file |
   | Una funzione | La funzione | Con chi la chiama e chi chiama |
   | Un componente dell'interfaccia | Il componente | Dal fatto mostrato a chi lo scrive; dalle azioni a chi reagisce |
   | Una funzionalità | I suoi ingressi | Seguendo i collegamenti, anche fra strati |
   | Un flusso di dati | Lo store o il fatto mostrato | Chi scrive e chi legge, anche fra strati |
   | Un aspetto (sicurezza, prestazioni, concorrenza) | L'aspetto sceglie i revisori, non i file | Dagli ingressi se l'aspetto segue il dato, altrimenti per percorso del file |

4. La macchina segue `chiama`, `scrive`, `legge` e `attiva` dai punti di partenza, senza limite di salti e ciascuno una volta sola. Si ferma quando il collegamento esce dal confine di lettura, quando un limite del budget si esaurisce o quando il collegamento non si risolve. Ciò che non ha seguito resta elencato, e il flusso è dichiarato incompleto. *Stato corretto dopo la revisione esterna del 20 novembre: una lacuna senza simbolo (per esempio «argomenti non leggibili») non entra nel percorso che la tocca, e `through` senza attraversamenti risulta completo (task 7c).* Come contesto aggiunge solo ciò che dista un `chiama` dal flusso.
5. Divide il perimetro in unità entro un limite di byte. Raggruppa chi scrive e chi legge lo stesso dato. Quando finiscono in unità separate, `cuts` nomina lo store, il file che scrive e quelli che leggono. Un file condiviso da due flussi compare in entrambe le unità. Un file che molti flussi toccano è membro di poche unità, in numero fissato, e contesto nelle altre. I file che nessun flusso tocca vengono dopo, per percorso. Ogni file del perimetro è assegnato almeno una volta. Un file più grande del limite occupa da solo un'unità e compare in `oversized` con dimensione e limite. Nel pacchetto di ciascun revisore il file condiviso è assegnato una volta. Gli altri incarichi lo ricevono tra i percorsi di contesto.
6. **Proposta del 20 novembre: dai legami al contesto e alle prove** (motivo 13). Dalla richiesta al flusso, al modulo logico o al componente si arriva con la ricerca sull'anagrafica (3.8, motivo 12): per il proprietario è il passo che decide quando si compone il pacchetto di una review; i file li dà poi il grafo, non la vicinanza del testo. Il flusso che la richiesta nomina è il perimetro; i flussi che «condivide» o «avvia» sono il contesto, e dicono che cosa può rompersi altrove. Per le prove un flusso è uno scenario: il suo ingresso è ciò che si aziona, il suo effetto ciò che deve cambiare. Quando un nodo cambia, i flussi che lo attraversano sono quelli da riprovare; un flusso che nessuna prova del progetto raggiunge è scoperto, e la mappa lo dice.

## 12. L'embedder: dove serve e dove no

**Proposta del 20 novembre 2026, dalle parole del proprietario** («fondamentale nell'identificazione o ricerca o matching dei flussi, soprattutto quando bisogna costruire un pacchetto di una funzionalità o di un flusso o di una componente per il code review»). Non misurata, tranne la ricerca (motivo 12).

1. **Il modello.** EmbeddingGemma 2, il grafo di solo testo che Daodan ha già (motivo 12). Immagini, audio e video non servono e non si scaricano.
2. **Che cosa si indicizza.** Una volta, dopo la mappa: le voci dell'anagrafica (3.8) e i nodi di profondità da 0 a 2. A ogni ricerca si calcola solo la frase cercata.
3. **Il pacchetto di una review.** Dalla richiesta in parole la ricerca dà le tre voci più vicine con il punteggio: un flusso, un modulo logico o un componente. La voce scelta è il punto di partenza; i file e le unità li dà il grafo (11.4, 11.5), il contesto i legami fra flussi (11.6). L'embedder sceglie da dove partire, non che cosa entra.
4. **L'abbinamento dei flussi.** L'embedder propone, non decide: due percorsi o due varianti che sono lo stesso flusso scritto con parole diverse (la domanda di 7.7, in [ingressi e scoperta dei flussi](2026-11-20-ingressi-e-scoperta-dei-flussi.md)), e il tipo di una forma che somiglia a una già classificata (6.5). Fra le proposte sceglie il modello; la macchina verifica sul grafo. Un abbinamento per sola vicinanza non si registra. Riprende gli usi 2 e 3 del task G2b del [piano del 19 novembre](../plans/2026-11-19-verso-i-riferimenti.md).
5. **Dove non serve.** Non prova un collegamento: due testi simili non sono collegati nel codice. La prova di un flusso resta il percorso (Parole).
6. **Senza modello preparato** la ricerca risponde con le parole in comune e lo dice. Né l'indice né una richiesta scaricano i pesi (decisione aperta 11).

## Limiti

Dalla spec della mappa, «Assunzioni e limiti noti», con il loro numero.

- **11.** **Richieste scritte da un modello.** Le 531 richieste della prova di ricerca le ha scritte un modello dai riferimenti, senza le parole del nome; nessuna viene da chi usa il prodotto (motivo 12).
- **19.** **Le 531 richieste sono di quattro casi** (I7): 262 su 131 flussi e 269 su parti, cercate fra 19–93 voci scritte dai riferimenti, non da Daodan.

## Prova

Le misure 7 («Dall'intento ai controlli») e 8 («Review») sono nella [spec della mappa](2026-11-18-flussi-e-mappa-del-sistema.md), «Prova»; i numeri della ricerca nel README di [`benchmarks/system-map`](../../benchmarks/system-map/README.md), «Embedder piccoli» e «Su 531 richieste in parole»; la prova sulla ricerca con le parole di chi usa il prodotto nella [fase 3](2026-11-09-flows-in-review.md).

## Motivi delle scelte

Con il numero che hanno nella spec della mappa; «README» è quello di [`benchmarks/system-map`](../../benchmarks/system-map/README.md).

- **12.** **La ricerca sull'anagrafica** (3.8). Deciso dal proprietario il 20 novembre: l'indice si calcola una volta, dopo la mappa e le schede, sulla voce intera; il modello è EmbeddingGemma 2, quello che Daodan ha (`embedding_worker.py`); la prova da zero lo misura sulle stesse 531 richieste accanto a multilingual-e5-large, e il numero dice quanto si lascia, non rimette in discussione la scelta. Perché: riusare ciò che c'è; su 531 richieste di quattro casi il migliore misurato, multilingual-e5-large, dà la risposta giusta fra le prime tre 91–93 volte su 100, il miglior modello statico 58–77, le parole in comune 36–64; sui soli nomi il migliore scende a 65. Scartato: multilingual-e5-large come modello del prodotto (la raccomandazione era di provarli tutti e due); un modello statico, approvato prima sulla prova di 35 flussi; un modello solo inglese, che sulle richieste di chi usa il prodotto scende a 66; un GGUF Q4_K_M convertito da un privato (182 MB) e il q8 della libreria di Ollama (304 MB, che non ha un q4), che chiederebbero llama.cpp accanto a ONNX Runtime senza dare un file più piccolo: il proprietario ha deciso il 20 novembre di non provarli. Il file: il grafo di testo `onnx/model_q4.onnx` di `onnx-community/embeddinggemma-2-ONNX` (174 MB, Apache 2.0, revisione e sha256 verificati da `embedding_worker.py`). È solo testo, come serve: gli encoder di immagini e audio sono file a parte, che Daodan non scarica, e i tre ingressi del grafo che li aspettano restano vuoti. Dimensioni lette il 20 novembre sulle pagine dei tre archivi. Prova: README, «Embedder piccoli» e «Su 531 richieste in parole». Non misurati: EmbeddingGemma 2, tempo e memoria, richieste di persone.
- **13.** **Anagrafica e legami fra flussi** (3.8, 11.6). Dalle parole del proprietario del 20 novembre. Perché: dai soli flussi di due riferimenti, 48 nodi su 106 e 43 su 100 stanno in più di un flusso, 60 e 34 coppie di flussi condividono almeno due nodi, 6 e 7 flussi non hanno legami. Scartato: leggere `avvia` dai riferimenti, dove esce una volta per caso; va letto dai collegamenti. Prova: README, «Legami fra flussi, prova a costo zero»; nessuno script del repository la rifà.

## Errori registrati

- La prova piccola degli embedder (35 flussi) diceva che i modelli stanno vicini e che il più grande non è il migliore, e su quella è stato approvato un modello statico; su 531 richieste i modelli a trasformatore multilingue stanno sopra ogni modello statico.

## Decisioni aperte

- **2.** Quanto EmbeddingGemma 2 lascia rispetto a multilingual-e5-large: lo dice la prova da zero.
- **10.** Se l'embedder entra nell'abbinamento dei flussi (12.4): lo decide la misura del task 10c del [piano](../plans/2026-11-20-ricerca-e-pacchetto-di-review.md); fino ad allora è proposta, e nessun abbinamento si registra per sola vicinanza.
- **11.** Chi prepara il modello della ricerca: oggi né l'indice né una richiesta scaricano i pesi (`embedding_worker.py`) e il plugin dà gli embedding per facoltativi e spenti (`plugins/codebase-map/skills/map/references/embeddings.md`); il task 10 del piano del 20 novembre li usa dopo ogni mappa, con il modello preparato.
