# Casi d'uso e tutorial

Gli esempi scientifici sono illustrativi; non dichiarano paper letti o benchmark
eseguiti. Richiedono il plugin research con i provider dichiarati, Python e
ricerca web disponibile per le operazioni online.

## Controllare la modalità

1. Esegui `/research:science-mode`; su un progetto senza preferenza restituisce ON implicito.
2. Esegui `/research:science-mode off`; i successivi controlli automatici sono disabilitati.
3. Esegui `/research:science-mode on`; i controlli riprendono sui compiti pertinenti.

Ripetere lo stesso stato non genera cambiamenti inutili. Un valore diverso
da on/off viene rifiutato. Uno stato corrotto viene segnalato e non sovrascritto.

## Fondare una decisione algoritmica

1. Richiedi `/research:science-research confronta LRU e LFU per la cache di questo progetto`.
2. Il coordinatore risolve carico, vincoli e decisione; legge ricerche esistenti e cerca paper pertinenti.
3. Apri il documento corrente dall'indice: distingui risultati delle fonti, inferenze e prove locali.
4. Usa identità, revisione e conclusioni nel documento decisionale.

Non sono garantiti una conclusione favorevole o un numero di paper.
Se mancano dati del carico reale, la consegna può includere un protocollo
di benchmark marcato non eseguito. La sua esecuzione appartiene al compito di sviluppo.

## Controllare una ricerca dopo un aggiornamento

1. Esegui `/research:update-research <ID della ricerca>` indicando la tecnologia cambiata.
2. Leggi la ricevuta: fonti/versioni consultate, copertura ed esito.
3. Riapri lo stesso file: confronta timestamp, passaggi superati barrati e changelog descrittivo.
4. Riesamina i documenti consumatori elencati attraverso il loro normale flusso.

Nessuna novità significa ricevuta senza revisione. Un errore di rete significa
controllo fallito/parziale, non evidenza aggiornata. `tutte` applica lo stesso
processo alle identità presenti all'inizio e mostra separatamente gli esiti.

## Riprendere un tema già discusso

Richiedi un approfondimento sullo stesso tema nella conversazione. Il metodo
cerca prima l'eventuale documento corrente, anche se non è indicizzato. Se la
domanda vi rientra, usa o aggiorna quel file senza una nuova pagina datata.
Se due ricerche si sovrappongono e non è chiaro quale sia proprietaria del tema,
chiarisce la scelta prima di creare, unire o spostare contenuti.

## Ricerca esplicita con modalità OFF

`/research:science-mode off` seguito da una richiesta `science-research`
esegue soltanto la ricerca richiesta. La modalità resta OFF.
Durante un brainstorming di sola lettura, risultati e limiti restano nel
run/chat; l'eventuale pubblicazione richiede che il compito la autorizzi già.
