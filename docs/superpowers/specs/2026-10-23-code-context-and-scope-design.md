# Contesto del codice e perimetro progressivo

Data: 23 ottobre 2026. Requisiti richiesti dall'utente; disegno operativo proposto,
da verificare attraverso il [piano incrementale](../plans/2026-10-23-code-context-and-scope.md).
Questa specifica non dichiara implementati embedding o composizione automatica.
Stato al 24 ottobre 2026: P0-P10 del piano sono consegnati; le misure, i limiti e
ciò che non è stato esercitato sono nel [report di consegna](../reports/2026-10-23-code-context-delivery.md).
Gli embedding restano opzionali e disattivati per impostazione predefinita, e la
composizione nel ciclo è l'adapter di lifecycle, non un programmatore automatico.
La [valutazione della ricerca ricevuta](../reports/2026-10-23-code-context-research-assessment.md)
motiva l'aggiunta del perimetro di impatto potenziale e la selezione di contesto
con prerequisiti. Le modifiche restano requisiti da implementare e misurare.

## Obiettivo e confini

Daodan deve offrire una conoscenza persistente del progetto attraverso tre viste
collegate: spiegazioni semantiche in Markdown, grafo interrogabile di file/simboli/
relazioni e indice di ricerca con embedding locali. I processi devono ricavarne
un perimetro motivato di lettura, possibile intervento e verifica, inviando al
modello soltanto il contesto necessario alla fase corrente.

Il primo incremento verificato riguarda Python e Jedi. Nessun nuovo engine di
linguaggio appartiene a questo piano. Gli altri parser e i consumatori esistenti
conservano il proprio comportamento. La completezza riguarda l'inventario nel
perimetro dichiarato e la contabilizzazione degli esiti: chiamate dinamiche,
file non parsati, dipendenze esterne e archi ambigui restano gap espliciti.

Si compone con la [specifica del grafo, §3.2](2026-10-19-graph-grounded-economy-routing-design.md)
e con [I1/I2 della composizione](2026-10-20-system1-work-graph-composition-design.md).
Prevale la regola più recente: un arco del codice fornisce evidenza al
pianificatore; le dipendenze fra task derivano dai contratti approvati, non
dall'inversione automatica di chiamante e chiamato. Questo lavoro non riscrive
router, selezione dei revisori o scheduler.

## Requisiti verificabili

| ID | Requisito |
|---|---|
| R1 | Inventario, card, Markdown e risultati di ricerca collegati alle stesse identità, con snapshot, provenienza, revision anchor e freshness. |
| R2 | Archi Jedi disponibili ai consumatori attraverso una vista comune in sola lettura; conflitti e inferenze non confermate restano separati. |
| R3 | Impatto confrontato su base e candidato con policy di risoluzione comparabile; rimozioni, chiamate riscritte e copertura asimmetrica esplicite. |
| R4 | Ricerca locale tramite riferimenti esatti, testo e embedding; nessuna chiamata LLM per indicizzare, ordinare o navigare il grafo. |
| R5 | Perimetri distinti di analisi, intervento proposto, impatto potenziale e obblighi di verifica; nessuna selezione conferisce autorizzazione a scrivere. |
| R6 | Contesto limitato, deduplicato e progressivo; budget esaurito non cancella obblighi e non prova assenza di impatto. |
| R7 | Ripresa equivalente all'esecuzione continua sugli stessi input; input cambiati invalidano i risultati dipendenti. |
| R8 | Consumo nei metodi di analisi, documentazione, bug, sviluppo, testing nel ciclo e chiusura; responsabilità e gate dei proprietari preservati. |
| R9 | Risparmio misurato su token dell'intero flusso, retry inclusi, insieme a qualità, latenza, memoria e costo degli aggiornamenti. |
| R10 | Kernel, CLI, MCP e cinque export coerenti; prove strutturali e prove di esecuzione sul singolo host registrate separatamente. |

## Stato di partenza e decisioni

Esistono `manifest.sqlite`, `cards.sqlite`, report di fase Markdown, `symbols-at`,
`edit-impact`, `stale-callers` e letture sorgenti verificate. Le card sono letture
semantiche dell'agente, create e riusate per area; non sono già una descrizione
completa di ogni simbolo in Markdown. Il budget di `edit-impact` conta caratteri
JSON, non token del prompt assemblato.

Jedi produce `engine-edges.sqlite`, ma i consumatori non lo leggono ancora.
`read_edge_store` verifica schema, digest e parser fingerprint; il controllo
esplicito della versione del resolver e gli esiti vuoti persistenti richiedono
un contratto più completo. `stale-callers` costruisce oggi il grafo inverso dal
candidato: il confronto deve includere anche le relazioni della base.

Il [benchmark del 21 ottobre](../../../evals/codebase-map/retrieval-benchmark/RESULTS.md)
misura 36 query su 1.079 simboli. CodeRankEmbed migliora una parte delle richieste
in inglese, non il risultato complessivo; l'italiano resta debole. La capacità
embedding entra nel disegno come provider locale opzionale, con baseline testuale
sempre utilizzabile. La promozione a default richiede una nuova misura, non è
implicita nella richiesta di integrare gli embedding. Nessun modello o database
vettoriale è già approvato come nuova dipendenza di produzione.

L'archivio strutturale resta immutabile. Gli indici sono derivati sostituibili;
le card sono canoniche nel loro store e il Markdown ne è una vista generata,
affiancata ai report esistenti. Le sezioni prive di card dichiarano `unread` o
`stale`, senza generare spiegazioni fittizie. L'approfondimento semantico costa
token LLM e viene contabilizzato, limitato all'area richiesta e riusato.

## Algoritmo: perimetro progressivo con obblighi separati

Questa è una politica iniziale da misurare. Non pretende di trovare il minimo
globale né di dimostrare correttezza dal solo grafo statico.

### Input e output

`ContextRequest` contiene `schema`, `task_id`, `intent` (`analysis`, `docs`,
`bug`, `change`, `test`, `finish`), `query`, `read_boundary`, `write_boundary`,
`anchors` (path, simboli, intervalli o traceback), `base`, `candidate`, `diff`, `proposed_edits`,
`mandatory_requirements`, `required_gates`, `budget`, `policy_version`.
Entrambi i boundary derivano dal run e dal perimetro di `tree_scope`; una
richiesta non può allargarli. Gli input assenti sono dichiarati, non indovinati.

`ScopePlan` conserva `input_digest`, binding dei due snapshot, profilo dei
resolver, identità degli indici e tutti gli elementi scoperti nei seguenti
insiemi su disco, con copertura dichiarata:

- `analysis`: entità da leggere, motivo, dettaglio richiesto e stato della lettura;
- `edit_candidates`: siti del piano di intervento proposto, distinti dai file autorizzati;
- `potential_impact`: consumatori, contratti e comportamenti potenzialmente coinvolti, con direzione, provenienza e stato della relazione;
- `validation_obligations`: requisiti, comportamenti e gate da verificare;
- `deferred`, `unresolved`, `outside_boundary`: residui con motivo e provenienza.

`ContextPacket` è una proiezione limitata di `ScopePlan`: sorgenti, firme,
callsite, card fresche, riferimenti ai documenti, gap e contatori. Il cursore
lega richiesta, snapshot, resolver, indici, policy e blocchi già consegnati
alla stessa unità di lavoro. I1 `daodan/map-slice/v1` resta un adattamento
verso il pianificatore, senza cambiare silenziosamente il suo schema.

### Procedura

```text
prepare(request, indexes):
    verifica boundary, snapshot e versioni; rifiuta evidenza incompatibile
    exact = simboli da diff/intervalli/nomi/traceback verificabili
    ranked = ricerca testuale locale + ricerca vettoriale se disponibile
    seeds = deduplica exact e ranked per identità; conserva origine e rango
    plan = registra requisiti e gate prima di applicare qualsiasi budget
    aggiungi exact ad analysis come riferimenti obbligatori
    aggiungi ranked come candidati di esplorazione, senza autorizzare edit
    se base e candidato sono confrontabili:
        calcola impatto usando relazioni della base e del candidato
        aggiungi impatto potenziale e obblighi di validazione
    altrimenti:
        dichiara impatto provvisorio o non confrontabile
    registra i siti del piano di intervento senza promuovere ogni chiamante a edit
    prepara frontiera direzionale; persisti plan e input_digest

next_packet(plan, budget, cursor):
    verifica binding del cursore e spazio disponibile per il destinatario
    carica gli elementi obbligatori della fase corrente
    espandi il grafo solo nelle direzioni richieste dall'intento e dal delta
    ordina: obblighi, riferimenti esatti, contratti diretti,
            candidati di ricerca, vicini indiretti
    costruisci rappresentazioni e relativi prerequisiti verificabili
    seleziona il pacchetto secondo pack(), mantenendo gli obblighi rigidi
    registra ogni elemento differito e il motivo; conserva tutti gli obblighi
    se non trovi un nucleo valido entro i limiti: restituisci needs_split, non ready
    salva digest del pacchetto, misura del costo e cursore successivo
    restituisci riepilogo compatto e percorso; invia solo il pacchetto selezionato

advance(plan, evidence, candidate):
    verifica riferimenti di evidence, senza accettare istruzioni da sorgenti/card
    aggiorna letture e obblighi con prove del proprietario competente
    un nuovo candidato invalida pacchetti dipendenti e ricalcola il delta
    nuove entità necessarie alimentano la frontiera senza perdere i residui
    chiudi soltanto secondo i gate del processo, mai per frontiera vuota
```

La fusione dei rank resta una policy versionata misurata contro la baseline:
il primo confronto riusa quella del benchmark, senza inventare una soglia
di similarità che significhi «non impattato». I riferimenti esatti verificati
mantengono precedenza. Un'omissione causata dal limite della ricerca iniziale
compare nel piano; l'assenza di risultati richiede ampliare la ricerca nel
boundary o ritornare al proprietario per localizzazione, non dichiarare successo.

### Selezione del pacchetto con prerequisiti

Un candidato può essere rappresentato da firma, card con fonti, corpo esatto o
file intero. Ogni rappresentazione dichiara capacità e prerequisiti: per esempio
il corpo di un metodo può richiedere decoratori, firma della classe o definizione
di una costante. Gli obblighi di evidenza hanno predicati rigidi, come «sorgente
corrente del target disponibile»: due match semantici non li soddisfano.
Gli obblighi di eseguire test restano al processo, non diventano veri perché
il pacchetto contiene il testo di un test.

Per la periferia, confrontare la baseline ordinata con una politica sperimentale
che sceglie il guadagno informativo marginale per costo marginale. La funzione
surrogata iniziale è `F(S) = sum_j w_j * max_{i in S} a_ij`, con pesi e punteggi
non negativi, fissi per quel round, registrati nella policy. La copertura rigida
è una condizione separata; `F` non è una probabilità di correttezza. La prima
implementazione usa capacità di evidenza dichiarate e rank locali, senza un
LLM che assegni punteggi per candidato e senza ottimizzare il write set.

```text
pack(variants, hard_support, budget, work_limits):
    cerca un nucleo obbligatorio e i suoi prerequisiti compatibili entro i limiti
    se non trovato: restituisci needs_split con gli obblighi non supportati
    S = nucleo trovato
    finché restano risorse e proposte non equivalenti:
        per ogni aggiunta o sostituzione ammissibile:
            P = proposta più chiusura dei prerequisiti su S
            verifica hard_support, rappresentazioni compatibili e freshness
            deduplica per repo/revisione/file/intervallo, non per testo identico
            ricalcola utilità e costo dell'intero insieme serializzato
            scarta P se supera il budget o perde un supporto obbligatorio
        scegli il miglior guadagno positivo per costo aggiuntivo
        tratta prima i guadagni positivi a costo nullo o negativo
        se nessuna proposta entra o migliora: termina
        S = proposta scelta; aggiorna i costi condivisi e rivaluta le altre
    confronta S con nucleo più singoli bundle ammissibili entro work_limits
    serializza e riconta l'input completo, wrapper e provenance inclusi
    correggi overflow senza eliminare supporti obbligatori; altrimenti needs_split
    restituisci S, residui, costi, motivi e stato ready_for_attempt
```

La sostituzione di una card con un corpo deve rivalutare gli obblighi: il corpo
non conserva necessariamente una regola documentale citata nella card.
Un bundle prima troppo costoso può entrare dopo aver condiviso un prerequisito;
non eliminarlo definitivamente né usare rapporti memorizzati come limiti validi.
Un metodo identico in due classi resta costituito da due entità distinte.
Il codice da modificare resta verbatim e verificato; usare il file completo
quando il corpo da solo non soddisfa i prerequisiti, senza imporlo a ogni query.

È un'euristica deterministica, non una garanzia `1-1/e` o di minimo globale.
Una ricerca limitata che non trova un pacchetto non prova infeasibilità
matematica. `ready_for_attempt` riguarda la fase richiesta: non autorizza merge
né prova che il perimetro di impatto sia completo. CP-SAT, slicing interprocedurale
completo e calibrazione statistica dell'arresto restano esperimenti separati.

### Espansione, arresto e casi critici

| Condizione | Azione |
|---|---|
| Modifica di firma o effetti contrattuali | Seguire chiamanti e contratti risolti; registrare gli archi/contratti non disponibili. |
| Modifica del corpo | Seguire dipendenze pertinenti e validazione; non prescrivere riscritture dei chiamanti per il solo cambio del corpo. |
| Indagine su bug senza diff | Esplorare i candidati, chiamati e slice disponibili; nessun impatto definitivo prima dell'evidenza. |
| Documentazione | Collegare card, sorgente e documenti che citano l'area; testo simile è un candidato, non un contratto verificato. |
| Hub, ciclo o molti chiamanti | Frontiera paginata e componenti fortemente connesse; budget per pacchetto, obblighi completi nel piano. |
| Chiamata dinamica, parser assente, store parziale | Gap esplicito e approfondimento del consumatore; mai dedurre indipendenza. |
| Dipendenza oltre il boundary | Registrare il confine e la verifica richiesta; non leggere o modificare fuori scope automaticamente. |
| Limite di contesto | Fermare l'assemblaggio, non la verifica; separare fasi o task preservando le prove condivise. |
| Ripetizione senza nuove informazioni | Arrestare il retry automatico con `needs_localization` o `needs_split`; il run conserva il punto aperto. |

Una firma/effetti invariati possono fermare la propagazione contrattuale prevista
da `stale-callers`, non provano equivalenza del comportamento. La validazione
rimane aperta. I test individuati per nome, import o embedding sono candidati;
solo la verifica del proprietario li associa a requisiti e comportamenti.
I gate obbligatori del progetto non vengono ridotti dal retrieval.

### Costi e ripresa

Il budget del pacchetto è lo spazio disponibile dopo istruzioni, contesto già
presente, wrapper del destinatario e riserva della risposta. Contare l'input
serializzato completo con il tokenizer del destinatario quando disponibile;
altrimenti dichiarare `estimated`, mantenere il limite meccanico di caratteri
e non affermare un limite esatto in token. Il confine di dispatch verifica il
budget effettivamente disponibile; se non può, registra la verifica mancante.

Separare limiti per contesto corrente, token cumulativi di input/output, round,
candidati, archi visitati, tempo e lavoro dei tool. Un'azione di approfondimento
nomina il gap da ridurre, il proprio costo massimo e una chiave persistente;
non ripetere un'azione esaurita sugli stessi input. Timeout o limite di visita
conservano la frontiera e marcano copertura parziale. Nessuna soglia di rank
può chiudere un gap critico. L'arresto resta `uncalibrated` fino a una misura
specifica; l'esecuzione di riproduzioni o test appartiene al consumatore,
mentre codebase-map continua a produrre soltanto evidenza statica.

Nessun loop Jedi, ranking, embedding o rendering Markdown richiede LLM. Report
completi e array di vettori restano su disco; stdout ordinario contiene stato,
conteggi, gap e percorsi. I dettagli si recuperano per richiesta. Contabilizzare
separatamente token stimati, token effettivi quando esposti dall'host, cache,
retry e costo delle card; tempi di download, indice, query, CPU e RAM restano
metriche macchina. Non attribuire risparmio a un dato non misurato.

Il costo locale dipende da documenti indicizzati e archi visitati: una frontiera
deduplicata evita visite ripetute; la baseline ordinata costa O(k log k) sui k
candidati. Il packing che rivaluta le proposte può richiedere O(k^2) valutazioni,
ognuna con costo di prerequisiti, obblighi e serializzazione; limitarlo e misurarlo
separatamente. Una ricerca vettoriale esatta costa O(n*d) per n vettori di d
dimensioni; un indice ANN si valuta solo se la misura mostra questo collo di
bottiglia. Questi costi non stimano qualità o numero di token risparmiati.

Snapshot e indici nuovi si pubblicano atomicamente. Modifiche di contenuto,
versione del modello, tokenizer o formato del testo invalidano gli embedding
interessati; cancellazioni eliminano le righe dalla nuova generazione. Un ID
con contenuto cambiato non riusa il vettore. Un embedding non fresco viene
escluso dalla ricerca, con degradazione esplicita verso la baseline.

L'hash copre l'esatto input codificato: anche un rename invalida il vettore se
il path fa parte del documento. La freshness considera ambiente, lockfile,
stubs e dipendenze negative rilevanti (simbolo prima assente, registro vuoto),
non solo i file già letti. Se il tracciamento non può giustificare il riuso,
preferire il rebuild dichiarato. Le prove confrontano aggiornamento e rebuild
su inventario, fatti e risposte alle query; il solo exit code non basta.

Lo stato operativo usa `project-protocol` e `.daodan/runs/<id>/`, non un nuovo
scheduler. I derivati persistenti della mappa restano in `.codebase-map/`.
Il cursore è un artefatto di algoritmo referenziato dal run, non una seconda
agenda. Una nuova sessione rilegge piano, ledger e input verificati; non deve
ricostruire le decisioni dall'intera conversazione.

## Verifica del beneficio

Il benchmark conserva la baseline A e aggiunge, separatamente, archi Jedi,
perimetro progressivo ed embedding. Le query naturali in italiano e inglese
sono scritte da requisiti/sintomi reali, con gold verificato leggendo sorgenti;
quelle generate dai nomi non possono dimostrare qualità semantica. Separare
taratura e holdout per progetto, conservando errori e casi senza risposta.

Confrontare a pari budget: ricerca testuale, embedding, espansione fissa, nuova
selezione e contesto intero quando entra. Misurare localizzazione, dipendenze e
obblighi recuperati, risultato del task, token totali del flusso e latenza.
La promozione richiede zero obblighi persi nei casi di regressione, nessuna
regressione sugli anchor esatti e sul gold obbligatorio, e un beneficio osservato
su qualità o token a qualità preservata. Dati insufficienti lasciano il provider
opzionale; non costituiscono né successo né prova che gli embedding siano inutili.

La [richiesta di ricerca](2026-10-23-code-context-research-prompt.md) raccoglie
algoritmi e letteratura da confrontare con questa politica iniziale. Risultati
successivi possono sostituire una scelta tramite revisione versionata e prove,
senza riscrivere retroattivamente benchmark o checkpoint.
