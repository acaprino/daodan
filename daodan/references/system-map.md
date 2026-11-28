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
            "entries": ["Cliente"], "effects": ["Checkout"],
            "arrows": [{"from": "Cliente", "to": "Checkout", "data": "click on Pay", "kind": "attiva",
                        "cite": "web/checkout.ts:22"}]}]}
```

- Without `scope` the proposal covers the whole system and declares every area present or absent. With `scope`, declare, change or remove flows only in the named areas. Reference a node shared with another area by its current name or id. Include every owning area when changing the shared node.
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
- `position`: `internal` (default) has `members`: `path`, `path::Symbol`, `store:<store>/<key>`, `module:<name>`; a route is cited by its handler. A `store:` member no rule reads yet does not refuse the node when another member resolves: the answer lists it in `unlinked`, the node does not hold it and no arrow is proved through it. `external` (an actor, a device, an external service or project) has no members and cites `evidence`. `unseen` (part of the system outside the snapshot) says `where`.
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
- Declare `entries` and `effects` together as nonempty lists of the flow's participating nodes. Every participant must be reachable from an entry and lead to an effect along the direction of standing arrows. Branches, multiple entries and cycles can satisfy this check. `reachability` is `verified` when those paths exist and `unproved` when they do not. Older flows without endpoints have `not_declared`; coverage for them records membership only. Revising an anchored flow retains its endpoints unless both lists are supplied.
- Any other arrow is refused. A separate component, an isolated node or a refused arrow makes a flow with standing arrows incomplete. If all proposed arrows are refused and the nodes are valid, the map keeps the latest refusal for review separately from any admitted version. Read it with `about` using the flow name or its area. A corrected proposal replaces the diagnostic. Invalid node or flow identities are reported at write time.
- An entity reached through one representation and left through another is not a path: write the arrow between the two with its own evidence.

## Areas

Go through each: accesso e identità; funzioni principali; pagamenti e abbonamenti; dati dell'utente (sync, export, deletion, consent); integrazioni esterne; comunicazioni; amministrazione; esercizio (scheduled work, cache, maintenance, release). Declare the flows found or that the area is absent; add the areas the project has and the list lacks.

## Flow types

funzionale (the product does it for its user), operativo (runs without a person), tecnico (an internal mechanism), dati (follows a piece of data), hardware (goes through devices or the network), devops (builds, packages, releases or trains at development time). One or more.

## Report

The answer lists each node and flow with `status` (`accepted`, `incomplete`, `refused`, `confirmed`), explains incomplete and refused records, names in `unlinked` the store members of an accepted node that the links lack, lists each arrow as `proved`, `declared` or `refused`, and reports the coverage of complete flows over entry points, store keys and routes. It gives the ids `created`, `updated`, `removed`, `kept`, and `not_removed` with the reason. Names the project confirmed in `codebase-system-map.json` do not change.

## Reading the map

The brief shows candidates from the syntax tree and the recorded pre-map. The AST readers find candidates in callback arguments, markup bindings and decorators. Each has its reader, shape, symbol and source site. Use `entry_offset=0` with an optional `limit` and continue at `next_offset` to inspect every candidate, even before link rules exist. These rows have status `candidate`; only verified flows contribute to map coverage.

`about="name"` answers for an area, a flow or a node by id or current name: its flows, nodes, member files, external and unseen nodes. A report or an answer names up to 40 files of a node; past that it counts them by directory (`files_by_directory`). With `levels=[...]`, the natures of the nodes (persone, logico, dati, codice, fisico), and a flow, it shows the flow at those levels: arrows contracted through hidden nodes keep their state and proof, and a path that changes representation or crosses a refused step is a gap.

## Sequence

1. Read `shape_offset=0` for forms still to classify. Answer the numbered rows with `shape_answers={"id": "...", "answers":{"1":"..."}}` using a value from `allowed`. Read the first page again after saving. The registry and previously classified forms are already applied. Record any route/store rules separately. An empty `rules=[]` records that no project rule is needed.
2. For a whole-system run, ask `next_question=true`. Read the returned `card_id` with `trace_id`; paginate numbered steps with `trace_offset=next_offset`. Submit `trace_decision` with that card_id, name, area, types, step numbers in order, and one data label per step. If the evidence stops or the entry is out of scope, record `disposition` (`unresolved` or `excluded`) and a short `reason`. Repeat until the queue is empty. For an area-only review use `trace_offset=0` to select relevant cards; leave other areas' decisions alone.
3. Map the system's parts and devices and declare present or absent areas. For additional contextual proposals use the existing map format with the appropriate scope. Keep an unresolved event's stopping point visible; a line mentioning a destination cannot certify a missing link.
4. Read `about` for saved names and `next_question` for remaining entries. Read `effect_offset=0` for write sites without a proved entry and continue with `next_offset`. Report accepted paths, reviewed exclusions, unresolved entries, entries still to examine and writes without an entry. Preserve the provenance of observed and sampled calls.
