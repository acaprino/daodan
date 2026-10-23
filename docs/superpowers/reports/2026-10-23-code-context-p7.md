# P7: pacchetti di contesto limitati e riprendibili

Run: `.tritech/daodan/runs/code-context-p7-20261023/`.
Correzione di integrazione registrata separatamente:
`.tritech/daodan/runs/code-context-p7-authority-20261023/`.
Baseline pubblicata: `75f8af06958edc3a8dd7346417c5ba11bc151720`.

## Consegna

`context_packet.py` assembla evidenza statica verificata senza chiamate LLM,
download, refresh di indici o avvio implicito dell'encoder. Il nucleo obbligatorio
mantiene sorgenti e prerequisiti; firme, card fresche, callsite e dettagli L0–L4
riusano i produttori esistenti. Il selettore confronta ordine locale e guadagno
marginale con limiti di lavoro dichiarati. I cicli restano unità tutto-o-niente.
La deduplicazione usa snapshot, file e intervalli fisici, preservando identità
distinte anche per testo identico. Gli obblighi di validazione restano aperti.

L'input completo include istruzioni aggiuntive, metadati e provenienza. Un
contatore esplicito del destinatario verifica i token; CLI/MCP dichiarano il
limite in caratteri e richiedono la verifica del contesto al dispatch. Il costo
tokenizzato non viene presentato come consumo fatturato o risparmio misurato.

CLI `snapshot.py context` e tool MCP `codebase_map_context` condividono la stessa
operazione e restituiscono percorsi e contatori compatti. Il servizio lega il
candidato e l'eventuale base a run verificati. Un'autorità distinta per il
progetto degli artefatti e la radice delle sorgenti protegge i target non Git
senza permettere alla richiesta di ampliare il perimetro.

I checkpoint legano piano, richiesta, autorità, snapshot, resolver, indici,
card, input mancanti, destinatario e policy. Le pubblicazioni sono esclusive;
la ripresa rifiuta evidenza obsoleta. Nucleo non contenibile o ricerca limitata
senza nucleo valido producono `needs_split`, con residui e obblighi conservati.

## Verifica

Gli oracoli RED sono conservati nel run: modulo/CLI/tool assenti sulla baseline,
contratto non Git incompatibile prima della correzione e confronto base MCP.
La revisione indipendente ha rilevato due difetti MEDIUM, corretti in una sola
passata con regressioni RED/GREEN: ripartizione del lavoro fra policy e mancato
addebito dei token del nucleo rifiutato. I 24 test del pacchetto passano, insieme
alla suite del perimetro e del servizio, ai 10 test SDK MCP e alle quattro modalita
del probe CodeRank nativo. Gate comuni, budget di caricamento e build dei cinque
host passano. La suite completa della CI verifica il commit esatto pubblicato;
conteggi, digest e riferimenti dei job sono nelle consegne del run.
Le prime esecuzioni Windows hanno rilevato errori ambientali di memoria/paging;
non sono classificate come esiti del prodotto.

`reading.md` passa da 126 a 116 parole. Non aumentano i limiti di caricamento.
La compilazione deve rigenerare tutti e cinque gli host; una prova SDK stdio
resta distinta da una prova eseguita da un plugin installato in un host.

## Limiti

L'euristica non garantisce ottimo, infeasibilità matematica o correttezza del
codice. La mappa resta statica; le relazioni dinamiche e le coperture parziali
restano gap. Un pacchetto pronto non chiude test, task o autorizzazioni.
P8 collega il provider al ciclo di lavoro, P9 ai consumatori e P10 misura il
beneficio completo a budget equivalente. Nessun risparmio complessivo in token
viene dichiarato da questa consegna.
