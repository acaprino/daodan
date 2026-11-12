# System map: format and rules

A system map names the things a system is made of (nodes), the processes it runs (flows) and the areas a person names together. Propose it with `codebase_map_flows(run_id, map={...})`; the machine accepts or refuses each part and says why.

## Format

```json
{"scope": ["pagamenti e abbonamenti"],
 "areas": [{"name": "pagamenti e abbonamenti", "present": true}],
 "nodes": [{"name": "Checkout", "type": "schermata", "members": ["web/checkout.ts"]},
           {"name": "Cliente", "type": "attore", "position": "external", "evidence": ["web/checkout.ts"]}],
 "flows": [{"name": "Pagare un ordine", "area": "pagamenti e abbonamenti", "types": ["funzionale"],
            "nodes": ["Cliente", "Checkout"],
            "arrows": [{"from": "Cliente", "to": "Checkout", "data": "click on Pay", "kind": "attiva",
                        "cite": "web/checkout.ts:22"}]}]}
```

- Without `scope` the proposal covers the whole system and declares every area of the list present or absent. With `scope` it covers those areas only; their flows must stay inside them.
- References between nodes (`nodes`, `from`, `to`, `on`) are by current name. A flow may name nodes already in the map.
- To change a recorded node or flow, give its `id` or its current name. A new name without `id` creates a new record.

## Nodes

- `type`: attore, schermata, funzionalità, servizio o API, gateway, database, coda, autenticazione, dispositivo, altro, entità (a named piece of data, its members are the store keys that hold it).
- `position`: `internal` (default) has `members`: `path`, `path::Symbol`, `store:<store>/<key>`, `module:<name>`; a route is cited by its handler. `external` (an actor, a device, an external service or project) has no members and cites `evidence`. `unseen` (part of the system outside the snapshot) says `where`.
- `on` names the nodes it runs on or lives in.
- Never one node per symbol; a dependency is a node only when a flow needs it. A member may belong to several nodes.
- A new node is refused when an existing node of the same type has the same members, all of them, or a part of them.

## Arrows

- `data` says what passes. The machine proves an arrow between two nodes with code from the links: a link from a member of the first to a member of the second, or a write and a read of the same store key. It asserts only what those links say (`asserts`) and names the store keys it goes through (`via`).
- An arrow is declared when an end has no code, or when it says `stessa informazione` (one piece of data kept in several places): then `kind` is one of chiama, attiva, scrive, legge, usa, trasferisce, stessa informazione, and `cite` is a `path:line` that exists, in a file of the end with code. The machine checks that the point exists, not that it says it.
- Any other arrow is refused. A flow stands when its nodes are accepted and one arrow stands.
- An entity reached through one representation and left through another is not a path: write the arrow between the two with its own evidence.

## Areas

Go through each: accesso e identità; funzioni principali; pagamenti e abbonamenti; dati dell'utente (sync, export, deletion, consent); integrazioni esterne; comunicazioni; amministrazione; esercizio (scheduled work, cache, maintenance, release). Declare the flows found or that the area is absent; add the areas the project has and the list lacks.

## Flow types

funzionale (the product does it for its user), operativo (runs without a person), tecnico (an internal mechanism), dati (follows a piece of data), hardware (goes through devices or the network). One or more.

## Report and correction

The answer lists each node and flow with `status` (`accepted`, `refused`, `confirmed`), the `reason` of a refusal, each arrow as `proved`, `declared` or `refused`, the coverage of entry points, store keys and routes (what it leaves out by name, or by directory when the list is long), and the ids `created`, `updated`, `removed`, `kept`. Correct what was refused once; what stays refused does not enter the map. Names the project confirmed in `codebase-system-map.json` do not change.

## Reading the map

`about="name"` answers for an area, a flow or a node by id or current name: its flows, nodes, member files, external and unseen nodes. With `levels=[...]` (persone, funzioni, dati, codice, infrastruttura) and a flow, it shows the flow at those levels: arrows contracted through hidden nodes keep their state and proof, and a path that changes representation or crosses a refused step is a gap.
