# Casi del benchmark

Intent pronte al paste; attese e motivazioni in `ground_truth.json`.

| ID | Intent | Esito atteso |
|---|---|---|
| C1 | Rivedi packages/orders/pricing.py: modifica dello sconto cliente. | resolved: pricing.py, service.py |
| C2 | In produzione il dispatch dell'evento di pagamento ha sollevato KeyError: 'pay_online'. Rivedi la registrazione degli eventi e l'addebito online. | resolved: api.py, gateway.py |
| C3 | Rivedi il modulo shipping. | resolved: rates.py |
| C3b | Feature rimborsi: come è calcolato lo storno dell'IVA sui rimborsi emessi? | resolved: refunds.py |
| C4 | C'è un bug nello sconto: rivedi lo sconto. | clarify: pricing.py vs rates.py |
| C5 | Rivedi la catena del checkout: come arriva il totale ordine dalla callback registrata in api fino alla scrittura a ledger? | resolved: api, service, pricing, ledger; reporting fuori |
| C6 | Rivedi come viene notificato il cliente dopo il checkout: quale funzione invia davvero sul canale configurato? | partial: service.py, notifications.py |
| C7 | Elenca e rivedi i simboli di formattazione audit in packages/orders/big_module.py. | resolved: big_module.py |
| C8 | Rivedi ogni punto che tocca l'IVA/VAT: per ciascuno verifica che l'aliquota sia allineata a pricing.VAT_RATE. | resolved o partial: pricing.py, refunds.py |

## Resolver deterministico

Reference policy in `resolver.py` (`POLICY`): cap 6 interrogazioni e 10 letture, un file per lettura,
nodi deduplicati; una riformulazione per anchor vuoto dal lessico IT↔EN; top-5 hit per anchor; liste
di parole per riconoscere intent esaustivi, di flusso, di destinazione, di impatto. Sono approssimazioni
dei giudizi che la spec affida al modello: C1 fallisce per costruzione (xfail), perché il resolver non
usa `edit_impact`. Le sue letture usano il solo percorso, quindi non vedono i corpi delle funzioni: la
«lettura di conferma» del resolver è nominale.

Motivi d'arresto nelle tracce (convenzione di misura, non della spec): `delimited_by_evidence`,
`budget_exhausted`, `unresolved_required_link`, `ambiguous_domain_term`, `prerequisite_gap`,
`invalid_request`.

## Sessione con il modello

Brief in `results/model-runs/BRIEF.md`: testo operativo di `team-review.md` (copiato a mano: va
riallineato se il testo cambia), uso di `mapcli.py`, formato di `final.json`. Non contiene gli esempi della
spec né `tools-guide.md`, che usano questa stessa app e rivelerebbero le risposte. Un subagente per caso,
contesto isolato; la traccia la scrive il tool, non il modello. Valutazione con `model_eval.py SESSION CASO`.

Prima di lanciare le sessioni: `ensure_run(Path('.'), 'bench-model')` se `app/` è cambiata. I commenti di
`app/` non devono suggerire le risposte né nominare i casi.
