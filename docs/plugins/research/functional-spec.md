# Funzioni della ricerca scientifica

| Comando | Risultato osservabile |
|---|---|
| `/research:science-research <problema>` | Ricerca nuova o revisione motivata, con fonti lette e conclusioni tracciate |
| `/research:update-research <ID o tema>` | Controllo di una ricerca; una selezione ambigua viene chiarita |
| `/research:update-research tutte` | Ogni identità visitata una volta; esiti separati anche con fallimenti parziali |
| `/research:science-mode on` / `off` | Preferenza persistente condivisa dal progetto |
| `/research:science-mode` | Stato e origine, senza scritture né ricerche |

Prima di creare Markdown, la skill cerca documenti affini anche non indicizzati.
Un tema ripreso nella conversazione riusa la ricerca esistente; nuove evidenze
aggiornano lo stesso file, con timestamp, testo superato barrato e changelog.
Un nuovo documento richiede una domanda distinta. Più candidati sovrapposti
richiedono di chiarire quale mantenere, senza duplicazioni o fusioni silenziose.

La modalità predefinita è ON. OFF sospende consultazione dell'archivio,
ricerca online e pubblicazione automatiche. I comandi scientifici espliciti
restano disponibili e non cambiano la preferenza. Riattivare ON non aggiorna
retroattivamente tutto l'archivio. Una configurazione corrotta sospende
l'automatismo e resta intatta.

Brainstorming, specifiche, ADR/FRD e problemi sostanziali passano dal controllo
scientifico prima delle decisioni. Il metodo valuta pertinenza e incertezza,
sceglie riuso/aggiornamento/nuova ricerca e spiega quando non serve. Un salvataggio
o una parola chiave non bastano ad avviare una ricerca.

Ogni documento contiene titolo, temi, contesto, date con fuso, TL;DR,
paper con autore/titolo/sinossi/link e lettura effettiva, sintesi ragionata,
conclusioni e controevidenze, eventuali test locali e changelog.
Le fonti tecniche ufficiali sono distinte dai paper. Risultati pianificati
non sono misure eseguite.

Un controllo senza novità produce una ricevuta, senza nuova revisione
scientifica. Un cambiamento sostanziale preserva la precedente revisione,
identifica conclusioni cambiate e documenti da riesaminare. Anzianità,
ritiro e nuova tecnologia hanno significati diversi: il metodo motiva
superamento e applicabilità senza cancellare la storia.

La modalità non concede nuovi permessi. Un compito di sola lettura restituisce
risultati in chat o nel run autorizzato. La ricerca non modifica automaticamente
decisioni accettate, requisiti approvati o codice di prodotto.
