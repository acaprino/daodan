# System map: format and rules

A system map names the things a system is made of (nodes), the processes it runs (flows) and the areas a person names together. Propose it with `codebase_map_flows(run_id, map={...})`; the machine accepts or refuses each part and says why.

## Format

```json
{"scope": ["pagamenti e abbonamenti"],
 "areas": [{"name": "pagamenti e abbonamenti", "present": true}],
 "nodes": [{"name": "Checkout", "type": "schermata", "members": ["web/checkout.ts"]},
           {"name": "Cliente", "type": "attore", "position": "external", "evidence": ["web/checkout.ts"]}],
 "flows": [{"name": "Pagamento dell'ordine", "area": "pagamenti e abbonamenti", "types": ["funzionale"],
            "nodes": ["Cliente", "Checkout"],
            "arrows": [{"from": "Cliente", "to": "Checkout", "data": "click on Pay", "kind": "attiva",
                        "cite": "web/checkout.ts:22"}]}]}
```

- Without `scope` the proposal covers the whole system and declares every area of the list present or absent. With `scope` it covers those areas only; their flows must stay inside them.
- A proposal adds or changes what it names; what it does not name stays as it is. `remove` lists the flows to drop, by id or current name; a node leaves the map when no flow uses it, it is inside no node and no `on` or `inside` names it.
- References between nodes (`nodes`, `from`, `to`, `on`, `inside`) are by current name. A flow may name nodes already in the map.
- The brief numbers its items (`M1`, `E3`, `G1`) to read them; the machine accepts no number, so a proposal copies what the item names: its path, `path::Symbol`, `store:` or `module:` resource, `id` or `file:line`.
- To change a recorded node or flow, give its `id` or its current name. A new name without `id` creates a new record.

## Names

In the language of the product. The machine refuses a flow whose first word is empty and an external node with `registry` whose name does not begin with the name of that registry entry; it checks no other rule.

- A flow: the noun of the action and its object, not a verb (`Rimborso dell'ordine`, not `Rimborsare l'ordine`): the verbs are on the arrows. The product's words, not the code's nor a vendor's.
- No empty word first: gestione, elaborazione, processo, management, handling, processing.
- One flow, one outcome: two pieces that start from different entries are two flows.
- A part: as who works on it calls it, without the product's name, which only the node of the whole system carries (`App mobile`).
- A screen: the title the user sees. An entity: singular, a word of the domain (`Ordine`).
- A service of others: its proper name from the registry, never its role (`Stripe`, not `Pagamenti`); the role goes in `role`.
- The same name for the same thing in every map and every run.

## Nodes

- `type`: attore, schermata, funzionalità, servizio o API, gateway, database, coda, autenticazione, dispositivo, filesystem (a file or folder on disk the program reads or writes while it runs), altro, entità (a named piece of data, its members are the store keys that hold it), applicazione (a whole app or site a person opens, holding screens and logic), lavoro a orario (a job a schedule starts; a queue consumer stays a coda).
- `position`: `internal` (default) has `members`: `path`, `path::Symbol`, `store:<store>/<key>`, `module:<name>`; a route is cited by its handler. `external` (an actor, a device, an external service or project) has no members and cites `evidence`. `unseen` (part of the system outside the snapshot) says `where`.
- One node is the whole system: type `altro`, named as the product, members `.`, no `inside`. Inside it go the parts a person names, also without a manifest (an app, a site, a server, an admin panel), and the database, with its entities inside it. Inside a part go its screens, groups of routes, scheduled jobs and stores.
- Above every interface sits its device: an external `dispositivo` the interface names in `on`.
- A node's members are its whole part, the folder or the files it is made of, not an example file; `path::Symbol` only when the node is that function. Never a symbol you were not shown.
- `on` names the nodes it runs on or lives in. `inside` names the one node it is a part of; a circle is refused.
- An external node the brief lists with an `id` copies it as `registry`; an id the service registry does not have refuses the whole proposal. Every external service of others (not an attore, dispositivo or filesystem) says `family` (provider: it makes the program work; piattaforma di integrazione: a system of others the program exchanges data with), `role` (what it is for) and `mode` (how the program connects to it), as read in the code that calls it.
- Never one node per symbol; a dependency is a node only when a flow needs it. A member may belong to several nodes.
- A new node is refused when an existing node of the same type has the same members, all of them, or a part of them, unless one is inside the other, directly or through other nodes.

## Arrows

- `data` says what passes. The machine proves an arrow between two nodes with code from the links: a link from a member of the first to a member of the second, or a write and a read of the same store key. It asserts only what those links say (`asserts`) and names the store keys it goes through (`via`).
- When the links reach another function of the file of a function member, the arrow is proved with `precise: false`: it holds, less precisely. It does not hold when another node has the function reached as its member.
- An arrow is declared when an end has no code, or when it says `stessa informazione` (one piece of data kept in several places): then `kind` is one of chiama, attiva, scrive, legge, usa, trasferisce, stessa informazione, and `cite` is a `path:line` that exists, in a file of the end with code. The machine checks that the point exists, not that it says it.
- Any other arrow is refused. A flow stands when its nodes are accepted and one arrow stands.
- An entity reached through one representation and left through another is not a path: write the arrow between the two with its own evidence.

## Areas

Go through each: accesso e identità; funzioni principali; pagamenti e abbonamenti; dati dell'utente (sync, export, deletion, consent); integrazioni esterne; comunicazioni; amministrazione; esercizio (scheduled work, cache, maintenance, release). Declare the flows found or that the area is absent; add the areas the project has and the list lacks.

## Flow types

funzionale (the product does it for its user), operativo (runs without a person), tecnico (an internal mechanism), dati (follows a piece of data), hardware (goes through devices or the network), devops (builds, packages, releases or trains at development time). One or more.

## Report

The answer lists each node and flow with `status` (`accepted`, `refused`, `confirmed`), the `reason` of a refusal, each arrow as `proved`, `declared` or `refused`, the coverage of entry points, store keys and routes (what it leaves out by name, or by directory when the list is long), the ids `created`, `updated`, `removed`, `kept`, and `not_removed` with the reason. Names the project confirmed in `codebase-system-map.json` do not change.

## Reading the map

`about="name"` answers for an area, a flow or a node by id or current name: its flows, nodes, member files, external and unseen nodes. A report or an answer names up to 40 files of a node; past that it counts them by directory (`files_by_directory`). With `levels=[...]` (persone, funzioni, dati, codice, infrastruttura) and a flow, it shows the flow at those levels: arrows contracted through hidden nodes keep their state and proof, and a path that changes representation or crosses a refused step is a gap.

## Sequence

1. A skeleton, without `scope`: the node of the whole system, its parts and their devices, every area present or absent. External nodes come in step 2, with the flows that reach them.
2. One proposal per present area, with `scope` naming it: its flows, the nodes they pass through, the external nodes they reach.
3. After each answer, correct once what it refused, sending only the corrected parts; what stays refused stays out.
4. Then the remainder, at most 3 rounds: propose flows for what `coverage` leaves out; when an arrow is refused for want of a link the code makes, correct the link rules if you wrote them, record them all again (`rules` replaces them) and propose the arrow again.
5. Answer with counts: nodes and flows accepted and refused; arrows proved, declared and refused; what `coverage` still leaves out and the links the rules miss.
